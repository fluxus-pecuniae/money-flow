#!/usr/bin/env python3
"""Build REGIME1 market-regime risk-off filter evidence.

RISK TOOL, NOT ALPHA — research/evidence only. Tests whether the
breadth-based regime filter EARNS its use on a long book: equal-weight
liquid majors (DATA1 Binance perp daily, 2020-09 -> 2026-06), always-long
vs regime-gated (long when risk_on, cash otherwise), EXEC-EV1 conservative
friction, chronological 70/30 + anchored walk-forward OOS. The verdict is
a risk-tool pass (material OOS drawdown reduction at not-worse
risk-adjusted performance) or an honest fail — never an alpha claim. The
whipsaw cost (flips, false risk-off spells, return given up) is reported
in full. Parameters chosen on the train split only.

Both books idle through a common 90-candle warm-up (the longest regime
lookback) so the comparison starts the first day every config can decide.

Inputs: the DATA1 multi-venue snapshot (sha256-verified loader). No
network I/O, no runtime mutation, no orders, no private/signed endpoints.

Run locally:
    .venv/bin/python scripts/run_regime1_evidence.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _load_module(relative: str, alias: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rg = _load_module("services/strategy_validation/regime1.py", "regime1_runner_module")
fv = _load_module("services/strategy_validation/fund_venues1.py", "regime1_fund_venues1")
tsmom = rg.tsmom_ev1
sel_ev1 = rg._load_sel_ev1()

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402
from services.market_data.data1_multi_venue import load_data1_dataset  # noqa: E402

PHASE = "REGIME1"
REPORT_NAME = "regime1_market_regime_risk_off_filter_evidence"
DEFAULT_SUMMARY_OUTPUT = Path("docs/regime1_market_regime_risk_off_filter_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/regime1_market_regime_risk_off_filter_evidence.md")
DEFAULT_DATA1_SUMMARY = Path("docs/data1_multi_venue_snapshot_summary.json")
GATE_SCENARIO_ID = "exec_ev1_conservative"
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")
BOOK_ASSETS = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
BOOK_VENUE = "binance"
WARMUP_CANDLES = max(rg.REGIME_LOOKBACKS)
REBALANCE_DAYS = 7


def _s(value: Any) -> Any:
    return str(value) if isinstance(value, Decimal) else value


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: _s(v) for k, v in stats.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data1-summary", type=Path, default=DEFAULT_DATA1_SUMMARY)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def build_universe(ds):
    datasets = []
    for symbol in BOOK_ASSETS:
        series = ds.series(BOOK_VENUE, symbol, "perp_1d")
        if series.status != "ok":
            raise RuntimeError(f"data1_series_not_ok:{BOOK_VENUE}:{symbol}:{series.status}")
        datasets.append(
            fv.dataset_from_data1_rows(symbol, BOOK_VENUE, "perp_1d", list(series.rows))
        )
    return sel_ev1.SelectionUniverse(datasets)


def book_config(label: str) -> Any:
    # Benchmark plumbing through the unchanged tsmom_ev1 simulator: the
    # equal-weight long book (vol_targeting=False => weight = signal/N).
    return tsmom.TsmomConfig(
        config_id=f"regime1_book_{label}",
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=60,  # unused: signal_provider overrides
        portfolio_vol_target=Decimal("0.20"),  # unused with vol_targeting=False
        mode="long_only",
        vol_targeting=False,
        rebalance_interval_days=REBALANCE_DAYS,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    ds = load_data1_dataset(args.data1_summary)
    universe = build_universe(ds)
    # SelectionUniverse.timeline is the UNION of symbol timestamps; the
    # books and the regime state live on the ALIGNED (every-symbol) closes.
    timeline = [
        t
        for t in universe.timeline
        if all(universe.index_by_time[s].get(t) is not None for s in universe.symbols)
    ]
    warmup_cutoff = timeline[WARMUP_CANDLES]
    scenario = scenario_by_id(GATE_SCENARIO_ID)
    print(f"universe: {len(timeline)} aligned days {timeline[0]} .. {timeline[-1]}")
    print(f"common warm-up cutoff (both books idle before): {warmup_cutoff}")

    def warmed(provider):
        def wrapped(symbol: str, idx: int):
            t = universe.datasets[symbol].candles[idx].timestamp if idx < len(
                universe.datasets[symbol].candles
            ) else None
            if t is None or t < warmup_cutoff:
                return 0
            return provider(symbol, idx)

        return wrapped

    # --- the two books -------------------------------------------------------
    always_result = tsmom.simulate_tsmom_portfolio(
        universe,
        book_config("always_long"),
        scenario,
        signal_provider=warmed(rg.always_long_provider),
    )
    always_curve = always_result["equity_curve"]

    configs = rg.generate_regime_configs()
    gated_results: dict[str, Any] = {}
    series_by_config: dict[str, Any] = {}
    for config in configs:
        provider = rg.gated_long_provider(universe, config)
        result = tsmom.simulate_tsmom_portfolio(
            universe,
            book_config(config.config_id),
            scenario,
            signal_provider=warmed(provider),
        )
        gated_results[config.config_id] = result
        series_by_config[config.config_id] = rg.compute_regime_series(universe, config)
        print(f"{config.config_id}: net {result['net_pnl']}")

    # --- chronological split + anchored folds --------------------------------
    split = timeline[max(0, min(len(timeline) - 1, int(len(timeline) * float(CHRONOLOGICAL_TRAIN_RATIO)) - 1))]
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    def train_sharpe(result) -> Decimal:
        stats = rg.curve_stats(result["equity_curve"], up_to=split)
        return stats["sharpe_annual"] if stats["sharpe_annual"] is not None else Decimal("-999")

    chosen_id = sorted(gated_results, key=lambda cid: (-train_sharpe(gated_results[cid]), cid))[0]
    chosen_config = next(c for c in configs if c.config_id == chosen_id)
    chosen = gated_results[chosen_id]

    always_oos = rg.curve_stats(always_curve, after=split)
    gated_oos = rg.curve_stats(chosen["equity_curve"], after=split)
    always_train = rg.curve_stats(always_curve, up_to=split)
    gated_train = rg.curve_stats(chosen["equity_curve"], up_to=split)

    # Walk-forward folds: per-fold train-only choice, fold drawdown gated vs
    # always-long over the same window.
    folds = []
    for label, train_up_to, lo, hi in (
        ("fold_b", t1, t1, t2),
        ("fold_c", t2, t2, None),
    ):
        def fold_train_sharpe(result):
            stats = rg.curve_stats(result["equity_curve"], up_to=train_up_to)
            return stats["sharpe_annual"] if stats["sharpe_annual"] is not None else Decimal("-999")

        fold_choice = sorted(gated_results, key=lambda cid: (-fold_train_sharpe(gated_results[cid]), cid))[0]
        gated_fold = rg.curve_stats(gated_results[fold_choice]["equity_curve"], after=lo, up_to=hi)
        always_fold = rg.curve_stats(always_curve, after=lo, up_to=hi)
        folds.append(
            {
                "fold": label,
                "chosen_config": fold_choice,
                "window": [str(lo), str(hi) if hi else "end"],
                "gated_max_drawdown_pct": gated_fold["max_drawdown_pct"],
                "always_max_drawdown_pct": always_fold["max_drawdown_pct"],
                "gated_sharpe": _s(gated_fold["sharpe_annual"]),
                "always_sharpe": _s(always_fold["sharpe_annual"]),
                "gated_return_pct": _s(gated_fold["total_return_pct"]),
                "always_return_pct": _s(always_fold["total_return_pct"]),
            }
        )

    # --- no-lookahead probe ---------------------------------------------------
    sample_times = [timeline[i] for i in (WARMUP_CANDLES + 5, len(timeline) // 2, len(timeline) - 30)]
    no_lookahead = rg.verify_regime_point_in_time(universe, chosen_config, sample_times)

    # --- whipsaw cost (full window + OOS) -------------------------------------
    chosen_series = series_by_config[chosen_id]
    whipsaw_full = rg.whipsaw_stats(chosen_series, always_curve)
    whipsaw_oos = rg.whipsaw_stats(chosen_series, always_curve, after=split)

    # --- the risk-tool gate ----------------------------------------------------
    gate = rg.evaluate_regime_filter_gate(
        always_oos_stats=always_oos,
        gated_oos_stats=gated_oos,
        fold_dd_reductions=folds,
        no_lookahead_verified=no_lookahead,
    )
    print(f"chosen {chosen_id}: verdict {gate['status']} reasons {gate['reason_codes']}")

    # --- current state on the latest closed candles ---------------------------
    latest_state = dict(chosen_series[-1][1]) if chosen_series else None
    if latest_state is not None:
        latest_state["as_of_close"] = str(chosen_series[-1][0])
        latest_state = {k: _s(v) for k, v in latest_state.items()}

    def conv(v):
        if isinstance(v, Decimal):
            return str(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [conv(x) for x in v]
        return v

    per_config_rows = []
    for config in configs:
        result = gated_results[config.config_id]
        oos = rg.curve_stats(result["equity_curve"], after=split)
        train = rg.curve_stats(result["equity_curve"], up_to=split)
        per_config_rows.append(
            {
                "config_id": config.config_id,
                "lookback_days": config.lookback_days,
                "breadth_threshold": str(config.breadth_threshold),
                "btc_rule": config.btc_rule,
                "net_pnl": _s(result["net_pnl"]),
                "train_sharpe": _s(train_sharpe(result)),
                "train_stats": _stats_str(train),
                "oos_stats": _stats_str(oos),
            }
        )

    # Hindsight texture (HONESTY SURFACE, NOT A VERDICT — TREND-SUITE1
    # precedent): the config with the best OOS drawdown reduction, and what
    # an alternative train criterion (min train drawdown) would have chosen.
    # The train-only Sharpe choice above is the committed criterion; nothing
    # here re-decides it.
    def oos_dd(row):
        dd = row["oos_stats"]["max_drawdown_pct"]
        return Decimal(str(dd)) if dd is not None else Decimal("999")

    hindsight_best = min(per_config_rows, key=oos_dd)
    def train_dd(row):
        dd = row["train_stats"]["max_drawdown_pct"]
        return Decimal(str(dd)) if dd is not None else Decimal("999")

    alt_train_choice = min(per_config_rows, key=train_dd)
    hindsight = {
        "note": "NOT A VERDICT: surfaced for honesty only; the committed choice criterion is train Sharpe and was not re-decided",
        "best_oos_drawdown_config_in_hindsight": {
            "config_id": hindsight_best["config_id"],
            "oos_stats": hindsight_best["oos_stats"],
        },
        "alternative_train_criterion_min_train_drawdown_would_have_chosen": {
            "config_id": alt_train_choice["config_id"],
            "train_stats": alt_train_choice["train_stats"],
            "oos_stats": alt_train_choice["oos_stats"],
        },
    }

    dd_reduction_pct = None
    if always_oos["max_drawdown_pct"] and gated_oos["max_drawdown_pct"] is not None:
        dd_reduction_pct = rg._money(
            (Decimal(str(always_oos["max_drawdown_pct"])) - Decimal(str(gated_oos["max_drawdown_pct"])))
            / Decimal(str(always_oos["max_drawdown_pct"]))
            * Decimal("100")
        )

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "regime_filter_evidence_complete",
        "verdict": gate["status"],
        "disclaimer": rg.DISCLAIMER,
        "account_size_usdc": str(tsmom.STARTING_EQUITY),
        "universe": {
            "assets": list(BOOK_ASSETS),
            "venue_series": f"{BOOK_VENUE} perp_1d (DATA1)",
            "aligned_days": len(timeline),
            "window": [str(timeline[0]), str(timeline[-1])],
            "common_warmup_cutoff": str(warmup_cutoff),
            "book": f"equal-weight long book, {REBALANCE_DAYS}d rebalance, EXEC-EV1 {GATE_SCENARIO_ID} friction",
        },
        "design": {
            "signal": (
                "per-asset tsmom_ev1.tsmom_signal trailing-return sign (reused, not re-derived); "
                "breadth = fraction of assets trend-up; risk_on iff breadth >= threshold AND "
                "(btc_rule == vote OR BTC trend up); graded risk_score = breadth (display only)"
            ),
            "grid": f"lookbacks {list(rg.REGIME_LOOKBACKS)} x thresholds {[str(b) for b in rg.BREADTH_THRESHOLDS]} x btc rules {list(rg.BTC_RULES)} = {len(configs)} configs",
            "choice_criterion": "best train-window Sharpe of the gated book (chronological 70/30)",
            "gate_semantics": gate["verdict_semantics"],
        },
        "chronological_split": {"train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO), "split_time": str(split)},
        "train_only_choice": {"chosen_config": chosen_id},
        "headline": {
            "always_long_oos": _stats_str(always_oos),
            "gated_oos": _stats_str(gated_oos),
            "always_long_train": _stats_str(always_train),
            "gated_train": _stats_str(gated_train),
            "oos_max_drawdown_reduction_pct": _s(dd_reduction_pct),
            "always_long_full_net": _s(always_result["net_pnl"]),
            "gated_full_net": _s(chosen["net_pnl"]),
        },
        "walk_forward": folds and [{k: _s(v) for k, v in f.items()} for f in folds],
        "whipsaw_cost": {
            "full_window": conv(whipsaw_full),
            "oos_window": conv(whipsaw_oos),
            "semantics": (
                "false risk-off spell = always-long gained during the spell (return given up); "
                "true risk-off = always-long lost (drawdown avoided). Reported, never hidden."
            ),
        },
        "no_lookahead": {
            "verified": no_lookahead,
            "method": "truncation + future-tampering probes at sampled decision closes",
        },
        "per_config_results": per_config_rows,
        "hindsight_texture_not_a_verdict": hindsight,
        "committed_verdict_note": rg.COMMITTED_VERDICT_NOTE,
        "current_state_latest_closed_candle": latest_state,
        "regime_filter_gate": conv(gate),
        "reusable_gate": {
            "seam": "strategy_types.REGIME_FILTER_REF -> regime1.build_regime_gate(datasets) -> RegimeGate.is_risk_on(as_of)",
            "default_config_pinned": rg.DEFAULT_CONFIG.config_id,
            "intended_use": "suppress LONG entries while risk_off (drawdown control for long books; MONEYFLOW-SIGNAL1 and future per-asset strategies)",
        },
        "data_provenance": {
            "dataset": "DATA1 multi-venue snapshot (sha256-verified loader)",
            "as_of_utc": ds.as_of_utc,
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        },
        "boundaries": rg.boundary_flags(),
    }
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    h = summary["headline"]
    gate = summary["regime_filter_gate"]
    wo = summary["whipsaw_cost"]["oos_window"]
    wf = summary["whipsaw_cost"]["full_window"]
    lines = [
        "# REGIME1 — Market-Regime Risk-Off Filter (when NOT to be long)",
        "",
        f"> {summary['disclaimer']}",
        "",
        "Research/tool only. No runtime, strategy-rule, order, testnet, live, or",
        "production-approval change follows from this report.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        f"- Semantics: {summary['design']['gate_semantics']}",
        f"- Reasons: `{gate['reason_codes']}`; qualifiers: `{gate['qualifiers']}`",
        "",
        "## The rule",
        "",
        f"- {summary['design']['signal']}",
        f"- Grid: {summary['design']['grid']}; train-only choice: `{summary['train_only_choice']['chosen_config']}`",
        f"- Book: {summary['universe']['book']}; window {summary['universe']['window'][0]} .. {summary['universe']['window'][1]} ({summary['universe']['aligned_days']} days)",
        "",
        "## Always-long vs regime-gated (chronological 70/30 OOS, post-friction)",
        "",
        "| Book | OOS return | OOS Sharpe | OOS maxDD | OOS days |",
        "| --- | --- | --- | --- | --- |",
        f"| always-long | {h['always_long_oos'].get('total_return_pct')}% | {h['always_long_oos'].get('sharpe_annual')} | {h['always_long_oos'].get('max_drawdown_pct')}% | {h['always_long_oos'].get('days')} |",
        f"| regime-gated | {h['gated_oos'].get('total_return_pct')}% | {h['gated_oos'].get('sharpe_annual')} | {h['gated_oos'].get('max_drawdown_pct')}% | {h['gated_oos'].get('days')} |",
        "",
        f"- **OOS max drawdown reduction: {h['oos_max_drawdown_reduction_pct']}%** (material bar: >= {Decimal(gate['min_relative_dd_reduction']) * 100}% relative)",
        f"- Train: always {h['always_long_train'].get('total_return_pct')}% (maxDD {h['always_long_train'].get('max_drawdown_pct')}%) vs gated {h['gated_train'].get('total_return_pct')}% (maxDD {h['gated_train'].get('max_drawdown_pct')}%)",
        "",
        "## Walk-forward folds (drawdown gated vs always-long)",
        "",
    ]
    for fold in summary["walk_forward"]:
        lines.append(
            f"- {fold['fold']} (`{fold['chosen_config']}`): gated maxDD {fold['gated_max_drawdown_pct']}% vs always {fold['always_max_drawdown_pct']}%; "
            f"Sharpe {fold['gated_sharpe']} vs {fold['always_sharpe']}; return {fold['gated_return_pct']}% vs {fold['always_return_pct']}%"
        )
    lines += [
        "",
        "## Whipsaw cost (the honest fine print)",
        "",
        f"- OOS: {wo['state_flips']} flips ({wo['flips_per_year']}/yr), {wo['risk_off_days']} risk-off days ({wo['risk_off_fraction']}), "
        f"{wo['risk_off_spells']} spells (mean {wo['mean_spell_days']}d), {wo['false_risk_off_spells']} FALSE risk-offs giving up {wo['return_given_up_in_false_risk_off']} USDC; "
        f"drawdown avoided in true risk-offs {wo['drawdown_avoided_in_true_risk_off']} USDC",
        f"- Full window: {wf['state_flips']} flips, {wf['false_risk_off_spells']}/{wf['risk_off_spells']} false spells, "
        f"given up {wf['return_given_up_in_false_risk_off']} vs avoided {wf['drawdown_avoided_in_true_risk_off']} USDC",
        f"- {summary['whipsaw_cost']['semantics']}",
        "",
        "## Hindsight texture (NOT a verdict)",
        "",
        f"- {summary['hindsight_texture_not_a_verdict']['note']}",
        f"- Best OOS-drawdown config in hindsight: `{summary['hindsight_texture_not_a_verdict']['best_oos_drawdown_config_in_hindsight']['config_id']}` "
        f"(OOS maxDD {summary['hindsight_texture_not_a_verdict']['best_oos_drawdown_config_in_hindsight']['oos_stats'].get('max_drawdown_pct')}%)",
        f"- An alternative pre-committed criterion (min train drawdown) would have chosen "
        f"`{summary['hindsight_texture_not_a_verdict']['alternative_train_criterion_min_train_drawdown_would_have_chosen']['config_id']}` — surfaced because the gap between criteria is itself a finding about regime-filter fragility",
        "",
        "## Current state (latest closed candles in the evidence window)",
        "",
        f"`{json.dumps(summary['current_state_latest_closed_candle'])}`",
        "",
        "## Reusable gate",
        "",
        f"- {summary['reusable_gate']['seam']}",
        f"- Default pinned to the train-only choice: `{summary['reusable_gate']['default_config_pinned']}` (re-tuning without new evidence fails CI)",
        f"- Intended use: {summary['reusable_gate']['intended_use']}",
        "",
        "## Boundaries",
        "",
        "Signal only — no orders, no private/signed endpoints, no testnet/live, no",
        "approval surface, no runtime change. The filter reduces downside exposure;",
        "it does not predict returns and must never be read as a profit claim.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
