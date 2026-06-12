#!/usr/bin/env python3
"""Build REGIME2 objective-aligned regime-filter evidence.

RISK TOOL, NOT ALPHA — research/evidence only. The confirmatory re-test of
REGIME1 with exactly ONE change: config selection on the pre-registered
objective-aligned criterion (lowest gated TRAIN max drawdown, whipsaw
tie-break) instead of train Sharpe. The search space, universe, window,
friction, books, warm-up, folds, OOS methods, and EVERY REGIME1 bar are
unchanged (30% material OOS drawdown reduction; drawdown reduced in every
fold — strictly stronger than 'the chop fold must not worsen'; OOS Sharpe
not worse; plus the pre-stated return-retention tolerance). The criterion
and gates were committed to git BEFORE this selection ran (see
regime2.PRE_REGISTRATION and the Decision Log). A miss on any bar is an
honest fail.

Run locally:
    .venv/bin/python scripts/run_regime2_evidence.py
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


rg2 = _load_module("services/strategy_validation/regime2.py", "regime2_runner_module")
rg = rg2.regime1
fv = _load_module("services/strategy_validation/fund_venues1.py", "regime2_fund_venues1")
tsmom = rg.tsmom_ev1
sel_ev1 = rg._load_sel_ev1()

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402
from services.market_data.data1_multi_venue import load_data1_dataset  # noqa: E402

PHASE = "REGIME2"
REPORT_NAME = "regime2_objective_aligned_regime_filter_evidence"
DEFAULT_SUMMARY_OUTPUT = Path("docs/regime2_objective_aligned_regime_filter_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/regime2_objective_aligned_regime_filter_evidence.md")
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
    return tsmom.TsmomConfig(
        config_id=f"regime2_book_{label}",
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
    timeline = [
        t
        for t in universe.timeline
        if all(universe.index_by_time[s].get(t) is not None for s in universe.symbols)
    ]
    warmup_cutoff = timeline[WARMUP_CANDLES]
    scenario = scenario_by_id(GATE_SCENARIO_ID)
    print(f"universe: {len(timeline)} aligned days {timeline[0]} .. {timeline[-1]}")

    def warmed(provider):
        def wrapped(symbol: str, idx: int):
            t = universe.datasets[symbol].candles[idx].timestamp if idx < len(
                universe.datasets[symbol].candles
            ) else None
            if t is None or t < warmup_cutoff:
                return 0
            return provider(symbol, idx)

        return wrapped

    always_result = tsmom.simulate_tsmom_portfolio(
        universe,
        book_config("always_long"),
        scenario,
        signal_provider=warmed(rg.always_long_provider),
    )
    always_curve = always_result["equity_curve"]

    configs = rg.generate_regime_configs()  # REGIME1's exact grid, unwidened
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

    split = timeline[max(0, min(len(timeline) - 1, int(len(timeline) * float(CHRONOLOGICAL_TRAIN_RATIO)) - 1))]
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    # --- the pre-registered selection (train only; OOS never seen) ----------
    def selection_rows(train_up_to) -> list[dict[str, Any]]:
        rows = []
        for config in configs:
            train = rg.curve_stats(gated_results[config.config_id]["equity_curve"], up_to=train_up_to)
            rows.append(
                {
                    "config_id": config.config_id,
                    "train_max_drawdown_pct": train["max_drawdown_pct"],
                    "train_flips": rg2.train_flips(series_by_config[config.config_id], up_to=train_up_to),
                }
            )
        return rows

    selection = rg2.select_by_train_drawdown(selection_rows(split))
    chosen_id = selection["chosen"]["config_id"]
    chosen_config = next(c for c in configs if c.config_id == chosen_id)
    chosen = gated_results[chosen_id]
    print(f"pre-registered selection chose: {chosen_id} (ties: {selection['ties_considered']})")

    always_oos = rg.curve_stats(always_curve, after=split)
    gated_oos = rg.curve_stats(chosen["equity_curve"], after=split)
    always_train = rg.curve_stats(always_curve, up_to=split)
    gated_train = rg.curve_stats(chosen["equity_curve"], up_to=split)

    # Walk-forward folds with the SAME pre-registered criterion per fold.
    folds = []
    for label, train_up_to, lo, hi in (
        ("fold_b_chop", t1, t1, t2),
        ("fold_c", t2, t2, None),
    ):
        fold_selection = rg2.select_by_train_drawdown(selection_rows(train_up_to))
        fold_choice = fold_selection["chosen"]["config_id"]
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

    # Fixed-config fold texture (HONESTY SURFACE, NOT A VERDICT): the
    # pre-registered fold gate evaluates the SELECTION PROCESS (per-fold
    # train-only choice — REGIME1's method, unchanged) and that is what the
    # verdict judges. The final chosen config's own drawdown per fold window
    # is surfaced for consumers (MONEYFLOW-SIGNAL1) but cannot rescue the
    # verdict — re-reading the fold gate after the result would be the
    # self-deception the honesty guard forbids.
    fixed_fold_texture = []
    for label, lo, hi in (("fold_b_chop", t1, t2), ("fold_c", t2, None)):
        gated_fixed = rg.curve_stats(chosen["equity_curve"], after=lo, up_to=hi)
        always_fixed = rg.curve_stats(always_curve, after=lo, up_to=hi)
        fixed_fold_texture.append(
            {
                "fold": label,
                "config_id": chosen_id,
                "gated_max_drawdown_pct": _s(gated_fixed["max_drawdown_pct"]),
                "always_max_drawdown_pct": _s(always_fixed["max_drawdown_pct"]),
                "gated_return_pct": _s(gated_fixed["total_return_pct"]),
                "always_return_pct": _s(always_fixed["total_return_pct"]),
            }
        )

    sample_times = [timeline[i] for i in (WARMUP_CANDLES + 5, len(timeline) // 2, len(timeline) - 30)]
    no_lookahead = rg.verify_regime_point_in_time(universe, chosen_config, sample_times)

    chosen_series = series_by_config[chosen_id]
    whipsaw_full = rg.whipsaw_stats(chosen_series, always_curve)
    whipsaw_oos = rg.whipsaw_stats(chosen_series, always_curve, after=split)

    gate = rg2.evaluate_regime_filter_gate_v2(
        always_oos_stats=always_oos,
        gated_oos_stats=gated_oos,
        fold_dd_reductions=folds,
        no_lookahead_verified=no_lookahead,
    )
    print(f"verdict {gate['status']} reasons {gate['reason_codes']}")

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
                "train_stats": _stats_str(train),
                "train_flips": rg2.train_flips(series_by_config[config.config_id], up_to=split),
                "oos_stats": _stats_str(oos),
            }
        )

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
        "status": "regime2_objective_aligned_evidence_complete",
        "verdict": gate["status"],
        "disclaimer": rg.DISCLAIMER,
        "account_size_usdc": str(tsmom.STARTING_EQUITY),
        "pre_registration": rg2.PRE_REGISTRATION,
        "pre_registration_confirmation": (
            "the selection criterion and all gates above were fixed in regime2.py and the "
            "Decision Log and committed to git BEFORE this selection ran; the search space "
            "is REGIME1's grid unwidened; both REGIME1 bars are held unchanged"
        ),
        "universe": {
            "assets": list(BOOK_ASSETS),
            "venue_series": f"{BOOK_VENUE} perp_1d (DATA1)",
            "aligned_days": len(timeline),
            "window": [str(timeline[0]), str(timeline[-1])],
            "common_warmup_cutoff": str(warmup_cutoff),
            "book": f"equal-weight long book, {REBALANCE_DAYS}d rebalance, EXEC-EV1 {GATE_SCENARIO_ID} friction",
        },
        "chronological_split": {"train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO), "split_time": str(split)},
        "selection": conv(selection),
        "train_only_choice": {"chosen_config": chosen_id, "criterion": rg2.PRE_REGISTRATION["selection_criterion"]},
        "headline": {
            "always_long_oos": _stats_str(always_oos),
            "gated_oos": _stats_str(gated_oos),
            "always_long_train": _stats_str(always_train),
            "gated_train": _stats_str(gated_train),
            "oos_max_drawdown_reduction_pct": _s(dd_reduction_pct),
            "always_long_full_net": _s(always_result["net_pnl"]),
            "gated_full_net": _s(chosen["net_pnl"]),
        },
        "walk_forward": [{k: _s(v) for k, v in f.items()} for f in folds],
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
        "fixed_config_fold_texture_not_a_verdict": {
            "note": (
                "NOT A VERDICT: the pre-registered fold gate judges the SELECTION PROCESS "
                "(per-fold train-only choice, REGIME1's method unchanged) and failed; this "
                "block shows the final chosen config's own fold windows for consumers and "
                "cannot rescue the verdict"
            ),
            "folds": fixed_fold_texture,
        },
        "regime1_comparison": {
            "regime1_chosen": "regime1_lb30_br5_btc_vote_1d (train Sharpe criterion)",
            "regime1_verdict": "regime_filter_does_not_reduce_drawdown_oos",
            "regime1_oos_dd_reduction_pct": "29.76",
            "what_changed": "ONLY the selection criterion (objective-aligned, pre-registered); same grid, bars, books, methods",
        },
        "current_state_latest_closed_candle": latest_state,
        "regime_filter_gate": conv(gate),
        "reusable_gate": {
            "seam": "strategy_types.REGIME_FILTER_REF -> regime1.build_regime_gate(datasets) -> RegimeGate.is_risk_on(as_of)",
            "default_config_pinned": chosen_id,
            "intended_use": "suppress LONG entries while risk_off (drawdown control for long books; MONEYFLOW-SIGNAL1 next)",
        },
        "data_provenance": {
            "dataset": "DATA1 multi-venue snapshot (sha256-verified loader)",
            "as_of_utc": ds.as_of_utc,
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        },
        "boundaries": rg2.boundary_flags(),
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
    sel = summary["selection"]
    lines = [
        "# REGIME2 — Objective-Aligned Regime Filter (fix the criterion, hold the bars)",
        "",
        f"> {summary['disclaimer']}",
        "",
        "Research/tool only. No runtime, strategy-rule, order, testnet, live, or",
        "production-approval change follows from this report.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        f"- Reasons: `{gate['reason_codes']}`; qualifiers: `{gate['qualifiers']}`",
        "",
        "## Pre-registration (fixed before selection ran)",
        "",
        f"- {summary['pre_registration_confirmation']}",
        f"- Criterion: {summary['pre_registration']['selection_criterion']}",
    ]
    for g in summary["pre_registration"]["gates_all_required_pre_registered"]:
        lines.append(f"- Gate: {g}")
    lines += [
        "",
        "## Selection (train only)",
        "",
        f"- Chosen: `{summary['train_only_choice']['chosen_config']}` (ties considered: {sel['ties_considered']})",
        "",
        "| Rank | Config | Train maxDD | Train flips |",
        "| --- | --- | --- | --- |",
    ]
    for i, row in enumerate(sel["ranking"][:10], 1):
        lines.append(f"| {i} | {row['config_id']} | {row['train_max_drawdown_pct']}% | {row['train_flips']} |")
    lines += [
        "",
        "## Always-long vs regime-gated (chronological 70/30 OOS, post-friction)",
        "",
        "| Book | OOS return | OOS Sharpe | OOS maxDD | OOS days |",
        "| --- | --- | --- | --- | --- |",
        f"| always-long | {h['always_long_oos'].get('total_return_pct')}% | {h['always_long_oos'].get('sharpe_annual')} | {h['always_long_oos'].get('max_drawdown_pct')}% | {h['always_long_oos'].get('days')} |",
        f"| regime-gated | {h['gated_oos'].get('total_return_pct')}% | {h['gated_oos'].get('sharpe_annual')} | {h['gated_oos'].get('max_drawdown_pct')}% | {h['gated_oos'].get('days')} |",
        "",
        f"- **OOS max drawdown reduction: {h['oos_max_drawdown_reduction_pct']}%** (bar: >= 30%, held from REGIME1)",
        f"- Train: always {h['always_long_train'].get('total_return_pct')}% (maxDD {h['always_long_train'].get('max_drawdown_pct')}%) vs gated {h['gated_train'].get('total_return_pct')}% (maxDD {h['gated_train'].get('max_drawdown_pct')}%)",
        "",
        "## Walk-forward folds (incl. the REGIME1-failing chop fold, now a hard gate)",
        "",
    ]
    for fold in summary["walk_forward"]:
        lines.append(
            f"- {fold['fold']} (`{fold['chosen_config']}`): gated maxDD {fold['gated_max_drawdown_pct']}% vs always {fold['always_max_drawdown_pct']}%; "
            f"return {fold['gated_return_pct']}% vs {fold['always_return_pct']}%"
        )
    lines += [
        "",
        "## Fixed-config fold texture (NOT a verdict)",
        "",
        f"- {summary['fixed_config_fold_texture_not_a_verdict']['note']}",
    ]
    for fold in summary["fixed_config_fold_texture_not_a_verdict"]["folds"]:
        lines.append(
            f"- {fold['fold']} (`{fold['config_id']}` fixed): gated maxDD {fold['gated_max_drawdown_pct']}% vs always {fold['always_max_drawdown_pct']}%; "
            f"return {fold['gated_return_pct']}% vs {fold['always_return_pct']}%"
        )
    lines += [
        "",
        "## Whipsaw cost (the honest fine print)",
        "",
        f"- OOS: {wo['state_flips']} flips ({wo['flips_per_year']}/yr), {wo['risk_off_days']} risk-off days ({wo['risk_off_fraction']}), "
        f"{wo['risk_off_spells']} spells, {wo['false_risk_off_spells']} FALSE risk-offs giving up {wo['return_given_up_in_false_risk_off']} USDC; "
        f"drawdown avoided {wo['drawdown_avoided_in_true_risk_off']} USDC",
        f"- {summary['whipsaw_cost']['semantics']}",
        "",
        "## vs REGIME1",
        "",
        f"`{json.dumps(summary['regime1_comparison'])}`",
        "",
        "## Current state (latest closed candles in the evidence window)",
        "",
        f"`{json.dumps(summary['current_state_latest_closed_candle'])}`",
        "",
        "## Boundaries",
        "",
        "Signal only — no orders, no private/signed endpoints, no testnet/live, no",
        "approval surface, no runtime change. Drawdown control, not alpha: the",
        "filter reduces downside exposure; it does not predict returns and must",
        "never be read as a profit claim.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
