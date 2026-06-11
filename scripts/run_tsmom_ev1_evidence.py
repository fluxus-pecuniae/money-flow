#!/usr/bin/env python3
"""Build TSMOM-EV1 vol-targeted time-series momentum evidence from SV2.2 candles.

TSMOM-EV1 is research/evidence only. It tests trend "done right" after the
earlier trend failures: per-asset time-series momentum (sign of the trailing
30/60/90-day return) with VOLATILITY TARGETING and RISK PARITY on the eight
liquid majors (BTC/ETH/SOL/XRP/DOGE/BNB/SUI/AVAX; HYPE excluded — mid-alt
tier + short history), judged against EQUAL-WEIGHT BUY-AND-HOLD on a
risk-adjusted basis (Sharpe + max drawdown) OUT-OF-SAMPLE after EXEC-EV1
depth-aware friction at 10,000 USDC sizing. Parameters are chosen on the
train split only. The gate never forces a positive verdict.

Reads SV2.2 raw candle artifacts from disk; no network I/O, no runtime
mutation, no orders, no private/signed/testnet/live endpoints, no production
or live approval. Deterministic (fixed seeds, Decimal arithmetic). Perp
funding is NOT modeled (documented assumption).

Run locally:
    .venv/bin/python scripts/run_tsmom_ev1_evidence.py
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


def _load_module(relative: str, alias: str):
    module_path = Path(__file__).resolve().parents[1] / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tsmom = _load_module("services/strategy_validation/tsmom_ev1.py", "tsmom_ev1_runner_module")
sel_ev1 = sys.modules["tsmom_ev1_sel_ev1"]

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "TSMOM-EV1"
REPORT_NAME = "tsmom_ev1_vol_targeted_momentum_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_SUMMARY_OUTPUT = Path("docs/tsmom_ev1_vol_targeted_momentum_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/tsmom_ev1_vol_targeted_momentum_evidence.md")
GATE_SCENARIO_ID = "exec_ev1_conservative"
REFERENCE_SCENARIO_IDS = ("exec_ev1_base", "exec_ev1_conservative", "exec_ev1_stress")
DEFAULT_RANDOM_SEED_COUNT = 20
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--random-seed-count", type=int, default=DEFAULT_RANDOM_SEED_COUNT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def load_universe(sv22_summary_path: Path) -> tuple[dict[str, Any], Any]:
    summary = json.loads(sv22_summary_path.read_text(encoding="utf-8"))
    if summary.get("phase") != "SV2.2":
        raise ValueError("tsmom_ev1_requires_sv2_2_summary_input")
    datasets = []
    for row in summary.get("datasets", []):
        if row.get("status") != "refreshed" or row.get("timeframe") != tsmom.TSMOM_TIMEFRAME:
            continue
        if row.get("symbol") not in tsmom.LIQUID_UNIVERSE:
            continue
        raw_path = row.get("raw_path")
        if not raw_path or not Path(raw_path).exists():
            raise FileNotFoundError(f"sv2_2_raw_candles_missing:{row.get('symbol')}:{raw_path}")
        payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        datasets.append(tsmom.dataset_from_sv22_payload(payload, source_path=str(raw_path)))
    if len(datasets) != len(tsmom.LIQUID_UNIVERSE):
        raise ValueError(
            f"liquid_universe_incomplete:{sorted(d.symbol for d in datasets)}"
        )
    return summary, tsmom.SelectionUniverse(datasets)


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in stats.items()}


def oos_trade_count(result: dict[str, Any], split: datetime) -> int:
    return sum(1 for t, *_ in result["trade_events"] if t > split)


def config_row(config: Any, result: dict[str, Any], split: datetime) -> dict[str, Any]:
    full = tsmom.curve_stats(result["equity_curve"])
    train = tsmom.curve_stats(result["equity_curve"], up_to=split)
    oos = tsmom.curve_stats(result["equity_curve"], after=split)
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "lookback_days": config.lookback_days,
        "portfolio_vol_target": str(config.portfolio_vol_target),
        "mode": config.mode,
        "vol_targeting": config.vol_targeting,
        "net_pnl": str(result["net_pnl"]),
        "ending_equity": str(result["ending_equity"]),
        "trade_count": result["trade_count"],
        "rebalance_count": result["rebalance_count"],
        "turnover_annual": str(result["turnover_annual"]),
        "avg_gross_exposure": str(result["avg_gross_exposure"]),
        "avg_net_exposure": str(result["avg_net_exposure"]),
        "avg_friction_bps": str(result["avg_friction_bps"]),
        "friction_paid_quote": str(result["friction_paid_quote"]),
        "full_stats": _stats_str(full),
        "train_stats": _stats_str(train),
        "oos_stats": _stats_str(oos),
        "oos_trade_count": oos_trade_count(result, split),
        "per_symbol_net_pnl": {k: str(v) for k, v in result["per_symbol_net_pnl"].items()},
        "entry_timing_cost_bps_by_lateness": {
            str(k): (str(v) if v is not None else None)
            for k, v in result["entry_timing_cost_bps_by_lateness"].items()
        },
    }


def verify_no_lookahead(universe: Any) -> dict[str, Any]:
    """Probe the causal signal + vol on real candles (truncation + tampering)."""
    symbol = universe.symbols[0]
    candles = universe.datasets[symbol].candles
    sample = [120, 200, 400, len(candles) - 2]

    def signal_fn(cs, idx):
        return tsmom.tsmom_signal([c.close for c in cs], idx, 60)

    def vol_fn(cs, idx):
        return tsmom.realized_vol_annual([c.close for c in cs], idx, tsmom.VOL_WINDOW_DAYS)

    return {
        "signal_point_in_time_ok": tsmom.verify_point_in_time_scores(signal_fn, candles, sample),
        "vol_point_in_time_ok": tsmom.verify_point_in_time_scores(vol_fn, candles, sample),
        "sampled_indices": sample,
        "probe_symbol": symbol,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sv22_summary, universe = load_universe(args.sv22_summary)
    gate_scenario = scenario_by_id(GATE_SCENARIO_ID)
    configs = tsmom.generate_tsmom_configs()
    split = tsmom.timeline_split_time(universe, CHRONOLOGICAL_TRAIN_RATIO)
    timeline = universe.timeline
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    # --- full grid under every scenario (gate uses conservative) -----------
    per_scenario_rows: dict[str, list[dict[str, Any]]] = {}
    results_by_config: dict[str, dict[str, Any]] = {}
    for scenario_id in REFERENCE_SCENARIO_IDS:
        scenario = scenario_by_id(scenario_id)
        rows = []
        for config in configs:
            result = tsmom.simulate_tsmom_portfolio(universe, config, scenario)
            rows.append(config_row(config, result, split))
            if scenario_id == GATE_SCENARIO_ID:
                results_by_config[config.config_id] = result
        per_scenario_rows[scenario_id] = rows

    config_by_id = {c.config_id: c for c in configs}

    # --- benchmarks (gate scenario; same machinery/friction/window) --------
    reference = configs[0]
    bench_buy_hold = tsmom.buy_hold_benchmark(universe, gate_scenario, reference=reference)
    bench_always_long = tsmom.always_long_no_vol_target_benchmark(
        universe, gate_scenario, reference=reference
    )
    bench_vt_beta = tsmom.always_long_vol_target_benchmark(
        universe, gate_scenario, reference=reference
    )
    seeds = list(range(1, args.random_seed_count + 1))
    bench_random = tsmom.random_long_flat_benchmark(
        universe, gate_scenario, reference=reference, seeds=seeds
    )

    # --- train-only choice + OOS comparison (the headline) -----------------
    chosen_id = tsmom.select_best_config_id(results_by_config, train_up_to=split)
    chosen_config = config_by_id[chosen_id]
    chosen_result = results_by_config[chosen_id]
    oos_strategy_stats = tsmom.curve_stats(chosen_result["equity_curve"], after=split)
    oos_buy_hold_stats = tsmom.curve_stats(bench_buy_hold["equity_curve"], after=split)
    train_strategy_stats = tsmom.curve_stats(chosen_result["equity_curve"], up_to=split)
    train_buy_hold_stats = tsmom.curve_stats(bench_buy_hold["equity_curve"], up_to=split)

    # --- anchored walk-forward thirds (train-only choice per fold) ---------
    def sharpe_edge(strategy_curve, after, up_to) -> Decimal | None:
        s = tsmom.curve_stats(strategy_curve, after=after, up_to=up_to)["sharpe_annual"]
        b = tsmom.curve_stats(bench_buy_hold["equity_curve"], after=after, up_to=up_to)[
            "sharpe_annual"
        ]
        if s is None or b is None:
            return None
        return tsmom._money(s - b)

    fold_b_choice = tsmom.select_best_config_id(results_by_config, train_up_to=t1)
    fold_b_edge = sharpe_edge(results_by_config[fold_b_choice]["equity_curve"], t1, t2)
    fold_c_choice = tsmom.select_best_config_id(results_by_config, train_up_to=t2)
    fold_c_edge = sharpe_edge(results_by_config[fold_c_choice]["equity_curve"], t2, None)
    walk_forward = {
        "fold_b": {"chosen_config": fold_b_choice, "window": [str(t1), str(t2)],
                   "sharpe_edge_vs_buy_hold": str(fold_b_edge) if fold_b_edge is not None else None},
        "fold_c": {"chosen_config": fold_c_choice, "window": [str(t2), "end"],
                   "sharpe_edge_vs_buy_hold": str(fold_c_edge) if fold_c_edge is not None else None},
    }

    # --- leave-one-out (drop each asset from BOTH book and benchmark) ------
    leave_one_out: dict[str, Any] = {}
    loo_edges: dict[str, Decimal | None] = {}
    for drop in universe.symbols:
        sub_datasets = [universe.datasets[s] for s in universe.symbols if s != drop]
        sub_universe = tsmom.SelectionUniverse(sub_datasets)
        sub_result = tsmom.simulate_tsmom_portfolio(sub_universe, chosen_config, gate_scenario)
        sub_bh = tsmom.buy_hold_benchmark(sub_universe, gate_scenario, reference=reference)
        s_stats = tsmom.curve_stats(sub_result["equity_curve"], after=split)
        b_stats = tsmom.curve_stats(sub_bh["equity_curve"], after=split)
        edge = (
            tsmom._money(s_stats["sharpe_annual"] - b_stats["sharpe_annual"])
            if s_stats["sharpe_annual"] is not None and b_stats["sharpe_annual"] is not None
            else None
        )
        loo_edges[drop] = edge
        leave_one_out[drop] = {
            "oos_strategy_sharpe": str(s_stats["sharpe_annual"]) if s_stats["sharpe_annual"] is not None else None,
            "oos_buy_hold_sharpe": str(b_stats["sharpe_annual"]) if b_stats["sharpe_annual"] is not None else None,
            "oos_sharpe_edge_vs_buy_hold": str(edge) if edge is not None else None,
            "oos_strategy_max_drawdown_pct": str(s_stats["max_drawdown_pct"]) if s_stats["max_drawdown_pct"] is not None else None,
        }

    # --- late-entry sensitivity (chosen config, +1 / +2 candle delays) -----
    late_entry: dict[str, Any] = {
        "avg_entry_timing_cost_bps_by_lateness": {
            str(k): (str(v) if v is not None else None)
            for k, v in chosen_result["entry_timing_cost_bps_by_lateness"].items()
        }
    }
    from dataclasses import replace as _replace

    for delay in (1, 2):
        delayed = tsmom.simulate_tsmom_portfolio(
            universe,
            _replace(chosen_config, config_id=f"{chosen_id}_delay{delay}", entry_delay_candles=delay),
            gate_scenario,
        )
        d_stats = tsmom.curve_stats(delayed["equity_curve"], after=split)
        late_entry[f"delay_{delay}_oos_sharpe"] = (
            str(d_stats["sharpe_annual"]) if d_stats["sharpe_annual"] is not None else None
        )
        late_entry[f"delay_{delay}_oos_net_pnl_delta"] = str(
            tsmom._money(delayed["net_pnl"] - chosen_result["net_pnl"])
        )

    # --- the gate -----------------------------------------------------------
    gate = tsmom.evaluate_tsmom_gate(
        strategy_type=chosen_config.strategy_type,
        oos_strategy_stats=oos_strategy_stats,
        oos_buy_hold_stats=oos_buy_hold_stats,
        walk_forward_sharpe_edges=[fold_b_edge, fold_c_edge],
        leave_one_out_edges=loo_edges,
        oos_trade_count=oos_trade_count(chosen_result, split),
    )

    random_oos_sharpes = []
    for row in bench_random:
        s = tsmom.curve_stats(row["equity_curve"], after=split)["sharpe_annual"]
        if s is not None:
            random_oos_sharpes.append(s)

    def bench_block(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "config_id": result["config_id"],
            "net_pnl": str(result["net_pnl"]),
            "trade_count": result["trade_count"],
            "avg_friction_bps": str(result["avg_friction_bps"]),
            "full_stats": _stats_str(tsmom.curve_stats(result["equity_curve"])),
            "train_stats": _stats_str(tsmom.curve_stats(result["equity_curve"], up_to=split)),
            "oos_stats": _stats_str(tsmom.curve_stats(result["equity_curve"], after=split)),
            "per_symbol_net_pnl": {k: str(v) for k, v in result["per_symbol_net_pnl"].items()},
        }

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "tsmom_evidence_complete",
        "verdict": gate["status"],
        "account_size_usdc": str(tsmom.STARTING_EQUITY),
        "universe": {
            "liquid_subset": list(tsmom.LIQUID_UNIVERSE),
            "excluded_thin_symbols": list(tsmom.EXCLUDED_THIN_SYMBOLS),
            "rationale": (
                "All eight have full 889-candle 1d history (2024-01-02 -> 2026-06-08) "
                "and sit in the EXEC-EV1 major/large liquidity tiers, so modeled "
                "friction is benign at 10k sizing. HYPE excluded: mid-alt tier and "
                "~550 candles only."
            ),
            "timeframe": tsmom.TSMOM_TIMEFRAME,
            "aligned_days": len(universe.timeline),
            "window": [str(universe.timeline[0]), str(universe.timeline[-1])],
        },
        "design": {
            "signal": "sign of trailing lookback return (30/60/90d); exact zero = flat",
            "vol_targeting": "equal risk budget per asset = portfolio_vol_target / N; weight = sign * min(budget / realized_vol_30d, 0.40)",
            "portfolio_vol_targets_annualized": [str(v) for v in tsmom.PORTFOLIO_VOL_TARGETS],
            "max_gross_leverage": str(tsmom.MAX_GROSS_LEVERAGE),
            "max_single_asset_weight": str(tsmom.MAX_SINGLE_ASSET_WEIGHT),
            "rebalance_interval_days": tsmom.REBALANCE_INTERVAL_DAYS,
            "rebalance_band_fraction_of_equity": str(tsmom.MIN_TRADE_NOTIONAL_FRACTION),
            "fills": "closed-candle decisions, next-candle-open fills, EXEC-EV1 depth-aware friction at traded notional",
            "config_grid_size": len(configs),
            "perp_funding_modeled": False,
        },
        "no_lookahead_verification": verify_no_lookahead(universe),
        "chronological_split": {
            "train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO),
            "split_time": str(split),
        },
        "train_only_choice": {
            "criterion": "best train-window Sharpe under conservative friction",
            "chosen_config": chosen_id,
        },
        "headline_comparison": {
            "gate_scenario": GATE_SCENARIO_ID,
            "strategy_oos": _stats_str(oos_strategy_stats),
            "buy_hold_oos": _stats_str(oos_buy_hold_stats),
            "strategy_train": _stats_str(train_strategy_stats),
            "buy_hold_train": _stats_str(train_buy_hold_stats),
            "oos_sharpe_edge_vs_buy_hold": (
                str(gate["oos_sharpe_edge_vs_buy_hold"])
                if gate["oos_sharpe_edge_vs_buy_hold"] is not None
                else None
            ),
            "oos_drawdown_delta_vs_buy_hold_pct": (
                str(gate["oos_drawdown_delta_vs_buy_hold_pct"])
                if gate["oos_drawdown_delta_vs_buy_hold_pct"] is not None
                else None
            ),
        },
        "benchmarks": {
            "buy_hold_equal_weight": bench_block(bench_buy_hold),
            "always_long_no_vol_target": bench_block(bench_always_long),
            "always_long_vol_target_beta": bench_block(bench_vt_beta),
            "random_long_flat": {
                "seed_count": len(seeds),
                "oos_sharpe_distribution": {
                    k: (str(v) if isinstance(v, Decimal) else v)
                    for k, v in tsmom.distribution_stats(random_oos_sharpes).items()
                },
            },
        },
        "per_config_results": {sid: rows for sid, rows in per_scenario_rows.items()},
        "walk_forward": walk_forward,
        "leave_one_out": leave_one_out,
        "late_entry_sensitivity": late_entry,
        "selection_gate": {
            k: (
                str(v)
                if isinstance(v, Decimal)
                else (
                    {ks: (str(vs) if isinstance(vs, Decimal) else vs) for ks, vs in v.items()}
                    if isinstance(v, dict)
                    else ([str(x) if isinstance(x, Decimal) else x for x in v] if isinstance(v, list) else v)
                )
            )
            for k, v in gate.items()
        },
        "routing": {
            "strategy_type": tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
            "gate_id": tsmom.TSMOM_GATE_ID,
            "never_judged_by": ["per_symbol_breadth_friction_gate", "selection_random_benchmark_gate"],
        },
        "data_provenance": {
            "sv22_summary": str(args.sv22_summary),
            "sv22_run_timestamp": sv22_summary.get("run_timestamp_utc"),
            "source": "hyperliquid_public_mainnet_candles_sv2_2_refresh",
        },
        "boundaries": {k: v for k, v in tsmom.boundary_flags().items()},
    }

    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"verdict: {gate['status']}")
    print(f"reasons: {gate['reason_codes']}")
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    h = summary["headline_comparison"]
    gate = summary["selection_gate"]
    bh = summary["benchmarks"]["buy_hold_equal_weight"]
    al = summary["benchmarks"]["always_long_no_vol_target"]
    vb = summary["benchmarks"]["always_long_vol_target_beta"]
    rnd = summary["benchmarks"]["random_long_flat"]
    lines = [
        "# TSMOM-EV1 — Volatility-Targeted Time-Series Momentum Evidence",
        "",
        "Research/evidence only. No runtime, strategy-rule, order, testnet, live,",
        "or production-approval change follows from this report. Modeled friction",
        "(EXEC-EV1) is an assumption layer, not real depth; perp funding is NOT",
        "modeled. Account basis: 10,000 USDC.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        f"Gate reasons: `{gate['reason_codes']}`",
        "",
        "## The honest question",
        "",
        "Does per-asset trend with volatility targeting + risk parity add",
        "risk-adjusted value (Sharpe / max drawdown) over simply holding the same",
        "liquid universe — out-of-sample, after conservative friction? The",
        "vol-targeted always-long benchmark separates 'trend timing' from 'vol",
        "targeting applied to beta'.",
        "",
        "## Headline (chronological 70/30 OOS, conservative friction)",
        "",
        "| | Sharpe (ann.) | Max DD % | Total return % | Days |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| TSMOM chosen (`{summary['train_only_choice']['chosen_config']}`) "
            f"| {h['strategy_oos'].get('sharpe_annual')} | {h['strategy_oos'].get('max_drawdown_pct')} "
            f"| {h['strategy_oos'].get('total_return_pct')} | {h['strategy_oos'].get('days')} |"
        ),
        (
            f"| Buy-and-hold equal-weight | {h['buy_hold_oos'].get('sharpe_annual')} "
            f"| {h['buy_hold_oos'].get('max_drawdown_pct')} | {h['buy_hold_oos'].get('total_return_pct')} "
            f"| {h['buy_hold_oos'].get('days')} |"
        ),
        "",
        f"- OOS Sharpe edge vs buy-hold: **{h['oos_sharpe_edge_vs_buy_hold']}**",
        f"- OOS max-drawdown delta vs buy-hold (negative = improved): **{h['oos_drawdown_delta_vs_buy_hold_pct']}**",
        "",
        "## Benchmarks (same machinery, same friction, full window)",
        "",
        "| Benchmark | Full Sharpe | Full Max DD % | OOS Sharpe | Net PnL |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| Buy-hold equal-weight | {bh['full_stats'].get('sharpe_annual')} | {bh['full_stats'].get('max_drawdown_pct')} "
            f"| {bh['oos_stats'].get('sharpe_annual')} | {bh['net_pnl']} |"
        ),
        (
            f"| Always-long, no vol target | {al['full_stats'].get('sharpe_annual')} | {al['full_stats'].get('max_drawdown_pct')} "
            f"| {al['oos_stats'].get('sharpe_annual')} | {al['net_pnl']} |"
        ),
        (
            f"| Always-long, vol-targeted (beta probe) | {vb['full_stats'].get('sharpe_annual')} | {vb['full_stats'].get('max_drawdown_pct')} "
            f"| {vb['oos_stats'].get('sharpe_annual')} | {vb['net_pnl']} |"
        ),
        (
            f"| Random long/flat ({rnd['seed_count']} seeds) | — | — "
            f"| median {rnd['oos_sharpe_distribution'].get('median')} | — |"
        ),
        "",
        "## Walk-forward (anchored thirds, train-only choice per fold)",
        "",
        f"- Fold B (`{summary['walk_forward']['fold_b']['chosen_config']}`): Sharpe edge {summary['walk_forward']['fold_b']['sharpe_edge_vs_buy_hold']}",
        f"- Fold C (`{summary['walk_forward']['fold_c']['chosen_config']}`): Sharpe edge {summary['walk_forward']['fold_c']['sharpe_edge_vs_buy_hold']}",
        "",
        "## Leave-one-out (drop each asset from book AND benchmark)",
        "",
        "| Dropped | OOS strategy Sharpe | OOS buy-hold Sharpe | Edge |",
        "| --- | --- | --- | --- |",
    ]
    for symbol, row in summary["leave_one_out"].items():
        lines.append(
            f"| {symbol} | {row['oos_strategy_sharpe']} | {row['oos_buy_hold_sharpe']} | {row['oos_sharpe_edge_vs_buy_hold']} |"
        )
    lines += [
        "",
        "## Late-entry sensitivity",
        "",
        f"- Avg adverse move by lateness (bps): {summary['late_entry_sensitivity']['avg_entry_timing_cost_bps_by_lateness']}",
        f"- +1 candle delay OOS Sharpe: {summary['late_entry_sensitivity'].get('delay_1_oos_sharpe')}",
        f"- +2 candle delay OOS Sharpe: {summary['late_entry_sensitivity'].get('delay_2_oos_sharpe')}",
        "",
        "## Universe + design",
        "",
        f"- Liquid subset: {', '.join(summary['universe']['liquid_subset'])} (excluded: {', '.join(summary['universe']['excluded_thin_symbols'])})",
        f"- Window: {summary['universe']['window'][0]} -> {summary['universe']['window'][1]} ({summary['universe']['aligned_days']} aligned days)",
        f"- {summary['design']['signal']}",
        f"- Vol targeting: {summary['design']['vol_targeting']}",
        f"- Gross leverage cap {summary['design']['max_gross_leverage']}; weekly rebalance; band {summary['design']['rebalance_band_fraction_of_equity']} of equity",
        "",
        "## Boundaries",
        "",
        "Research/evidence only; no order, testnet, live, production, or approval",
        "surface. Modeled depth, not real. Perp funding not modeled. The verdict",
        "above is the gate's output and was not forced positive.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
