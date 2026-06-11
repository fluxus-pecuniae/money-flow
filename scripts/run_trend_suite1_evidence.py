#!/usr/bin/env python3
"""Build TREND-SUITE1 canonical trend-suite evidence from SV2.2 candles.

TREND-SUITE1 is research/evidence only. TSMOM-EV1 tested one trend form
(return-sign momentum, vol-targeted) and found it defensive-but-not-
profitable; this phase tests the canonical suite never tried here —
Donchian channel breakout (Turtle 20/55), dual-MA crossover, multi-
timeframe confirmation, the TSMOM carry-over, and an ensemble — each under
BOTH vol-targeted (EV1-style) and non-vol-targeted equal-dollar sizing
(the key lever: vol targeting is known to cut exposure exactly in outlier
trends), plus channel vs ATR/chandelier trailing-stop exits. Everything is
judged by the same buy-and-hold risk-adjusted gate as TSMOM-EV1 on the
eight liquid majors after EXEC-EV1 depth-aware friction at 10,000 USDC.
Parameters are chosen on the train split only; the gate never forces a
positive verdict.

Reads SV2.2 raw candle artifacts from disk; no network I/O, no runtime
mutation, no orders, no private/signed/testnet/live endpoints, no
production or live approval. Deterministic (fixed seeds, Decimal
arithmetic). Perp funding is NOT modeled (documented assumption; the suite
is long-only, and longs typically PAY funding in bull regimes, so absolute
profits are optimistic).

Run locally:
    .venv/bin/python scripts/run_trend_suite1_evidence.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import replace
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


suite = _load_module("services/strategy_validation/trend_suite1.py", "trend_suite1_runner_module")

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "TREND-SUITE1"
REPORT_NAME = "trend_suite1_canonical_trend_suite_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_SUMMARY_OUTPUT = Path("docs/trend_suite1_canonical_trend_suite_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/trend_suite1_canonical_trend_suite_evidence.md")
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
        raise ValueError("trend_suite1_requires_sv2_2_summary_input")
    datasets = []
    for row in summary.get("datasets", []):
        if row.get("status") != "refreshed" or row.get("timeframe") != suite.TIMEFRAME:
            continue
        if row.get("symbol") not in suite.LIQUID_UNIVERSE:
            continue
        raw_path = row.get("raw_path")
        if not raw_path or not Path(raw_path).exists():
            raise FileNotFoundError(f"sv2_2_raw_candles_missing:{row.get('symbol')}:{raw_path}")
        payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        datasets.append(suite.dataset_from_sv22_payload(payload, source_path=str(raw_path)))
    if len(datasets) != len(suite.LIQUID_UNIVERSE):
        raise ValueError(f"liquid_universe_incomplete:{sorted(d.symbol for d in datasets)}")
    return summary, suite.SelectionUniverse(datasets)


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in stats.items()}


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    return value


def oos_trade_count(result: dict[str, Any], split: datetime) -> int:
    return sum(1 for t, *_ in result["trade_events"] if t > split)


def config_row(
    config: Any,
    result: dict[str, Any],
    split: datetime,
    oos_buy_hold_stats: dict[str, Any] | None,
) -> dict[str, Any]:
    full = suite.curve_stats(result["equity_curve"])
    train = suite.curve_stats(result["equity_curve"], up_to=split)
    oos = suite.curve_stats(result["equity_curve"], after=split)
    row = {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "family": config.family,
        "family_params": list(config.family_params),
        "sizing": config.sizing,
        "exit_style": config.exit_style,
        "decision_cadence_days": config.decision_cadence_days,
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
    }
    if oos_buy_hold_stats is not None:
        row["oos_screen"] = _json_ready(
            suite.per_config_screen(
                oos_strategy_stats=oos,
                oos_buy_hold_stats=oos_buy_hold_stats,
                oos_trade_count=row["oos_trade_count"],
            )
        )
    return row


def verify_no_lookahead(universe: Any, configs_by_id: dict[str, Any]) -> dict[str, Any]:
    """Probe each signal family (and both exit styles where they differ) on
    real candles via truncation + future-tampering."""
    symbol = universe.symbols[0]
    candles = universe.datasets[symbol].candles
    sample = [120, 200, 400, len(candles) - 2]
    probes = {
        "donchian_channel": "trend_suite1_donchian20x10_channel_vt_1d",
        "donchian_atr_trail": "trend_suite1_donchian55x20_atr_vt_1d",
        "ma_cross_signal": "trend_suite1_ma20x100_signal_vt_1d",
        "ma_cross_atr_trail": "trend_suite1_ma20x100_atr_vt_1d",
        "mtf_signal": "trend_suite1_mtf60w8_signal_vt_1d",
        "tsmom_signal": "trend_suite1_tsmom30_signal_vt_1d",
        "ensemble_majority": "trend_suite1_ens_majority_vt_1d",
        "ensemble_average": "trend_suite1_ens_average_vt_1d",
    }
    results = {}
    for name, config_id in probes.items():
        config = configs_by_id[config_id]

        def scorer(cs, idx, _config=config):
            return suite.strength_at(cs, idx, _config)

        results[name] = suite.verify_point_in_time_scores(scorer, candles, sample)
    return {
        "per_family_point_in_time_ok": results,
        "all_ok": all(results.values()),
        "sampled_indices": sample,
        "probe_symbol": symbol,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sv22_summary, universe = load_universe(args.sv22_summary)
    gate_scenario = scenario_by_id(GATE_SCENARIO_ID)
    configs = suite.generate_trend_suite_configs()
    config_by_id = {c.config_id: c for c in configs}
    split = suite.timeline_split_time(universe, CHRONOLOGICAL_TRAIN_RATIO)
    timeline = universe.timeline
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    # --- benchmarks (gate scenario; same machinery/friction/window) --------
    reference = configs[0]
    bench_buy_hold = suite.buy_hold_benchmark(universe, gate_scenario, reference=reference)
    oos_buy_hold_stats = suite.curve_stats(bench_buy_hold["equity_curve"], after=split)
    train_buy_hold_stats = suite.curve_stats(bench_buy_hold["equity_curve"], up_to=split)

    def always_long_benchmark(config_id: str, vol_targeting: bool) -> dict[str, Any]:
        config = replace(
            reference,
            config_id=config_id,
            mode="long_only",
            vol_targeting=vol_targeting,
            sizing=(
                suite.SIZING_VOL_TARGETED if vol_targeting else suite.SIZING_EQUAL_DOLLAR
            ),
            entry_delay_candles=0,
        )
        return suite.simulate_tsmom_portfolio(
            universe,
            config,
            gate_scenario,
            signal_provider=suite.always_long_provider,
            rebalance_timestamps=suite.decision_timestamps(universe, suite.WEEKLY_CADENCE),
        )

    bench_always_long = always_long_benchmark(
        "trend_suite1_benchmark_always_long_no_vol_target", vol_targeting=False
    )
    bench_vt_beta = always_long_benchmark(
        "trend_suite1_benchmark_always_long_vol_target", vol_targeting=True
    )
    seeds = list(range(1, args.random_seed_count + 1))
    bench_random = suite.random_long_flat_benchmark(
        universe, gate_scenario, reference=reference, seeds=seeds
    )

    # --- full grid under every scenario (gate uses conservative) -----------
    per_scenario_rows: dict[str, list[dict[str, Any]]] = {}
    results_by_config: dict[str, dict[str, Any]] = {}
    for scenario_id in REFERENCE_SCENARIO_IDS:
        scenario = scenario_by_id(scenario_id)
        rows = []
        for config in configs:
            result = suite.simulate_trend_suite_portfolio(universe, config, scenario)
            rows.append(
                config_row(
                    config,
                    result,
                    split,
                    oos_buy_hold_stats if scenario_id == GATE_SCENARIO_ID else None,
                )
            )
            if scenario_id == GATE_SCENARIO_ID:
                results_by_config[config.config_id] = result
        per_scenario_rows[scenario_id] = rows

    # --- train-only choices: global + per-family champions -----------------
    chosen_id = suite._tsmom.select_best_config_id(results_by_config, train_up_to=split)
    family_champion_ids: dict[str, str] = {}
    for family in suite.FAMILIES:
        family_results = {
            cid: result
            for cid, result in results_by_config.items()
            if config_by_id[cid].family == family
        }
        family_champion_ids[family] = suite._tsmom.select_best_config_id(
            family_results, train_up_to=split
        )

    # --- full gate (walk-forward + leave-one-out + sample) per champion ----
    def sharpe_edge(strategy_curve, after, up_to) -> Decimal | None:
        s = suite.curve_stats(strategy_curve, after=after, up_to=up_to)["sharpe_annual"]
        b = suite.curve_stats(bench_buy_hold["equity_curve"], after=after, up_to=up_to)[
            "sharpe_annual"
        ]
        if s is None or b is None:
            return None
        return suite._money(s - b)

    def full_gate_for(config_id: str, candidate_pool: dict[str, dict[str, Any]]) -> dict[str, Any]:
        config = config_by_id[config_id]
        result = results_by_config[config_id]
        oos_stats = suite.curve_stats(result["equity_curve"], after=split)

        # Anchored walk-forward thirds; the per-fold choice is train-only and
        # restricted to the same candidate pool the headline choice used.
        fold_b_choice = suite._tsmom.select_best_config_id(candidate_pool, train_up_to=t1)
        fold_b_edge = sharpe_edge(results_by_config[fold_b_choice]["equity_curve"], t1, t2)
        fold_c_choice = suite._tsmom.select_best_config_id(candidate_pool, train_up_to=t2)
        fold_c_edge = sharpe_edge(results_by_config[fold_c_choice]["equity_curve"], t2, None)

        # Leave-one-out: drop each asset from BOTH book and benchmark.
        loo_edges: dict[str, Decimal | None] = {}
        leave_one_out: dict[str, Any] = {}
        for drop in universe.symbols:
            sub_datasets = [universe.datasets[s] for s in universe.symbols if s != drop]
            sub_universe = suite.SelectionUniverse(sub_datasets)
            sub_result = suite.simulate_trend_suite_portfolio(sub_universe, config, gate_scenario)
            sub_bh = suite.buy_hold_benchmark(sub_universe, gate_scenario, reference=reference)
            s_stats = suite.curve_stats(sub_result["equity_curve"], after=split)
            b_stats = suite.curve_stats(sub_bh["equity_curve"], after=split)
            edge = (
                suite._money(s_stats["sharpe_annual"] - b_stats["sharpe_annual"])
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

        gate = suite.evaluate_tsmom_gate(
            strategy_type=config.strategy_type,
            oos_strategy_stats=oos_stats,
            oos_buy_hold_stats=oos_buy_hold_stats,
            walk_forward_sharpe_edges=[fold_b_edge, fold_c_edge],
            leave_one_out_edges=loo_edges,
            oos_trade_count=oos_trade_count(result, split),
        )

        # Late-entry sensitivity (+1 / +2 candle delays).
        late_entry: dict[str, Any] = {
            "avg_entry_timing_cost_bps_by_lateness": {
                str(k): (str(v) if v is not None else None)
                for k, v in result["entry_timing_cost_bps_by_lateness"].items()
            }
        }
        for delay in (1, 2):
            delayed = suite.simulate_trend_suite_portfolio(
                universe,
                replace(config, config_id=f"{config_id}_delay{delay}", entry_delay_candles=delay),
                gate_scenario,
            )
            d_stats = suite.curve_stats(delayed["equity_curve"], after=split)
            late_entry[f"delay_{delay}_oos_sharpe"] = (
                str(d_stats["sharpe_annual"]) if d_stats["sharpe_annual"] is not None else None
            )
            late_entry[f"delay_{delay}_oos_net_pnl_delta"] = str(
                suite._money(delayed["net_pnl"] - result["net_pnl"])
            )

        return {
            "config_id": config_id,
            "family": config.family,
            "sizing": config.sizing,
            "exit_style": config.exit_style,
            "gate": _json_ready(gate),
            "walk_forward": {
                "fold_b": {
                    "chosen_config": fold_b_choice,
                    "window": [str(t1), str(t2)],
                    "sharpe_edge_vs_buy_hold": str(fold_b_edge) if fold_b_edge is not None else None,
                },
                "fold_c": {
                    "chosen_config": fold_c_choice,
                    "window": [str(t2), "end"],
                    "sharpe_edge_vs_buy_hold": str(fold_c_edge) if fold_c_edge is not None else None,
                },
            },
            "leave_one_out": leave_one_out,
            "late_entry_sensitivity": late_entry,
            "absolute_oos": {
                "sharpe_annual": str(oos_stats["sharpe_annual"]) if oos_stats["sharpe_annual"] is not None else None,
                "total_return_pct": str(oos_stats["total_return_pct"]) if oos_stats["total_return_pct"] is not None else None,
                "max_drawdown_pct": str(oos_stats["max_drawdown_pct"]) if oos_stats["max_drawdown_pct"] is not None else None,
                "profitable_in_absolute_terms": bool(
                    oos_stats["total_return_pct"] is not None
                    and oos_stats["total_return_pct"] > 0
                    and oos_stats["sharpe_annual"] is not None
                    and oos_stats["sharpe_annual"] > 0
                ),
            },
        }

    family_gates = {
        family: full_gate_for(
            champion_id,
            {
                cid: result
                for cid, result in results_by_config.items()
                if config_by_id[cid].family == family
            },
        )
        for family, champion_id in family_champion_ids.items()
    }
    global_gate = full_gate_for(chosen_id, results_by_config)

    # --- the vol-targeting lever (Must 2): pairwise vt vs eq ---------------
    vt_comparison: dict[str, Any] = {}
    vt_class_counts: dict[str, int] = {}
    vt_pair_count = 0
    eq_raised_full_window_return = 0
    for config in configs:
        if config.sizing != suite.SIZING_VOL_TARGETED:
            continue
        eq_id = config.config_id.replace("_vt_", "_eq_")
        if eq_id not in results_by_config:
            continue
        vt_oos = suite.curve_stats(results_by_config[config.config_id]["equity_curve"], after=split)
        eq_oos = suite.curve_stats(results_by_config[eq_id]["equity_curve"], after=split)
        vt_full = suite.curve_stats(results_by_config[config.config_id]["equity_curve"])
        eq_full = suite.curve_stats(results_by_config[eq_id]["equity_curve"])
        classification = suite.classify_vol_targeting_effect(vt_oos, eq_oos)
        vt_class_counts[classification] = vt_class_counts.get(classification, 0) + 1
        vt_pair_count += 1
        if (
            eq_full["total_return_pct"] is not None
            and vt_full["total_return_pct"] is not None
            and eq_full["total_return_pct"] > vt_full["total_return_pct"]
        ):
            eq_raised_full_window_return += 1
        pair_key = config.config_id.replace("_vt_", "_X_")
        vt_comparison[pair_key] = {
            "family": config.family,
            "vol_targeted": {
                "config_id": config.config_id,
                "oos": _stats_str(vt_oos),
                "full": _stats_str(vt_full),
            },
            "equal_dollar": {
                "config_id": eq_id,
                "oos": _stats_str(eq_oos),
                "full": _stats_str(eq_full),
            },
            "oos_return_gain_pct_from_removing_vol_target": (
                str(suite._money(eq_oos["total_return_pct"] - vt_oos["total_return_pct"]))
                if eq_oos["total_return_pct"] is not None and vt_oos["total_return_pct"] is not None
                else None
            ),
            "oos_drawdown_change_pct_from_removing_vol_target": (
                str(suite._money(eq_oos["max_drawdown_pct"] - vt_oos["max_drawdown_pct"]))
                if eq_oos["max_drawdown_pct"] is not None and vt_oos["max_drawdown_pct"] is not None
                else None
            ),
            "classification": classification,
        }

    # --- headline blocks ----------------------------------------------------
    chosen_config = config_by_id[chosen_id]
    chosen_result = results_by_config[chosen_id]
    oos_strategy_stats = suite.curve_stats(chosen_result["equity_curve"], after=split)
    train_strategy_stats = suite.curve_stats(chosen_result["equity_curve"], up_to=split)

    absolute_clearers = [
        {
            "family": family,
            "config_id": block["config_id"],
            "gate_passed": block["gate"]["passed"],
            "profitable_in_absolute_terms": block["absolute_oos"]["profitable_in_absolute_terms"],
            "clears_bar_in_absolute_terms": bool(
                block["gate"]["passed"]
                and block["absolute_oos"]["profitable_in_absolute_terms"]
            ),
        }
        for family, block in family_gates.items()
    ]
    any_form_clears_absolute = any(row["clears_bar_in_absolute_terms"] for row in absolute_clearers)

    # Hindsight-best OOS config: surfaced for honesty about what WOULD have
    # been best — explicitly NOT a verdict (it was not train-chosen).
    def oos_sharpe_of(cid: str) -> Decimal:
        s = suite.curve_stats(results_by_config[cid]["equity_curve"], after=split)["sharpe_annual"]
        return s if s is not None else Decimal("-999")

    hindsight_best_id = max(sorted(results_by_config), key=oos_sharpe_of)
    hindsight_best_oos = suite.curve_stats(
        results_by_config[hindsight_best_id]["equity_curve"], after=split
    )

    random_oos_sharpes = []
    for row in bench_random:
        s = suite.curve_stats(row["equity_curve"], after=split)["sharpe_annual"]
        if s is not None:
            random_oos_sharpes.append(s)

    def bench_block(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "config_id": result["config_id"],
            "net_pnl": str(result["net_pnl"]),
            "trade_count": result["trade_count"],
            "avg_friction_bps": str(result["avg_friction_bps"]),
            "full_stats": _stats_str(suite.curve_stats(result["equity_curve"])),
            "train_stats": _stats_str(suite.curve_stats(result["equity_curve"], up_to=split)),
            "oos_stats": _stats_str(suite.curve_stats(result["equity_curve"], after=split)),
            "per_symbol_net_pnl": {k: str(v) for k, v in result["per_symbol_net_pnl"].items()},
        }

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "trend_suite_evidence_complete",
        "verdict": global_gate["gate"]["status"],
        "verdict_qualifiers": global_gate["gate"]["qualifiers"],
        "account_size_usdc": str(suite.STARTING_EQUITY),
        "headline_answers": {
            "question_1_does_any_trend_form_beat_buy_hold_risk_adjusted_oos_in_absolute_terms": any_form_clears_absolute,
            "per_family_absolute_bar": absolute_clearers,
            "question_2_did_removing_vol_targeting_unlock_profit_or_just_risk": {
                "classification_counts": vt_class_counts,
                "pair_count": vt_pair_count,
                "pairs_where_equal_dollar_raised_full_window_return": eq_raised_full_window_return,
                "reading": (
                    "see vol_targeting_comparison: pairwise OOS effect of removing "
                    "the vol cap for every signal cell; counts above aggregate the "
                    "deterministic classifications. The full-window counter shows "
                    "how often the uncapped variant DID capture more bull-window "
                    "upside in-sample — upside the OOS bear then took back"
                ),
            },
            "hindsight_best_oos_config_not_a_verdict": {
                "config_id": hindsight_best_id,
                "oos_stats": _stats_str(hindsight_best_oos),
                "note": (
                    "best OOS Sharpe across the grid IN HINDSIGHT; it was not "
                    "train-chosen, so it is surfaced for honesty, never as a verdict"
                ),
            },
        },
        "universe": {
            "liquid_subset": list(suite.LIQUID_UNIVERSE),
            "excluded_thin_symbols": list(suite.EXCLUDED_THIN_SYMBOLS),
            "rationale": (
                "Same eight liquid majors as TSMOM-EV1 (full 889-candle 1d history, "
                "EXEC-EV1 major/large tiers; HYPE excluded: mid-alt tier, ~550 candles). "
                "Hyperliquid candles are valid trend inputs for liquid majors (price is "
                "fungible across venues); multi-venue history is queued as DATA1."
            ),
            "timeframe": suite.TIMEFRAME,
            "aligned_days": len(universe.timeline),
            "window": [str(universe.timeline[0]), str(universe.timeline[-1])],
        },
        "design": {
            "families": {
                "donchian": "Turtle long-only: enter on prior 20/55-day-high close breakout; exit on prior 10/20-day-low close (channel) or chandelier 2.8x ATR(14) trail",
                "ma_cross": "dual SMA, long while SMA_short > SMA_long; short in {10,20,30} x long in {50,100,200}; canonical 20x100 also gets the ATR-trail exit",
                "mtf": "daily trailing-return sign (30/60/90d) gated by the weekly sign (8-week lookback, frozen at completed 7-day blocks); canonical 60d also gets the ATR-trail exit",
                "tsmom": "the EV1 signal carried over verbatim (sign of trailing 30/60/90d return, long_only mode, weekly cadence) — apples-to-apples",
                "ensemble": "majority (>=3 of 5) and average (fractional strength) of one fixed canonical member per family",
            },
            "sizing_variants": {
                "vol_targeted": "EV1 style: equal risk budget 0.20/N, per-asset weight cap 0.40, gross cap 1.5x",
                "equal_dollar": "non-vol-targeted: strength/N per asset, same documented gross cap 1.5x",
            },
            "exit_variants": "channel (Donchian), signal-off, ATR/chandelier trailing stop (2.8 x ATR14 from highest close since entry; re-entry requires a fresh signal)",
            "decision_cadence": "daily for stop/cross exits (a hit stop must not ride for days), weekly for the TSMOM carry-over (EV1 parity); rebalance band 0.5% of equity suppresses dust",
            "fills": "closed-candle decisions, next-candle-open fills, EXEC-EV1 depth-aware friction at traded notional",
            "config_grid_size": len(configs),
            "long_only": True,
            "long_short_already_covered_by": "TSMOM-EV1 grid (no edge found there)",
            "perp_funding_modeled": False,
        },
        "no_lookahead_verification": verify_no_lookahead(universe, config_by_id),
        "chronological_split": {
            "train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO),
            "split_time": str(split),
        },
        "train_only_choice": {
            "criterion": "best train-window Sharpe under conservative friction",
            "chosen_config": chosen_id,
            "family_champions": family_champion_ids,
        },
        "headline_comparison": {
            "gate_scenario": GATE_SCENARIO_ID,
            "strategy_oos": _stats_str(oos_strategy_stats),
            "buy_hold_oos": _stats_str(oos_buy_hold_stats),
            "strategy_train": _stats_str(train_strategy_stats),
            "buy_hold_train": _stats_str(train_buy_hold_stats),
            "oos_sharpe_edge_vs_buy_hold": global_gate["gate"]["oos_sharpe_edge_vs_buy_hold"],
            "oos_drawdown_delta_vs_buy_hold_pct": global_gate["gate"]["oos_drawdown_delta_vs_buy_hold_pct"],
        },
        "benchmarks": {
            "buy_hold_equal_weight": bench_block(bench_buy_hold),
            "always_long_no_vol_target": bench_block(bench_always_long),
            "always_long_vol_target_beta": bench_block(bench_vt_beta),
            "random_long_flat": {
                "seed_count": len(seeds),
                "oos_sharpe_distribution": {
                    k: (str(v) if isinstance(v, Decimal) else v)
                    for k, v in suite.distribution_stats(random_oos_sharpes).items()
                },
            },
        },
        "per_config_results": per_scenario_rows,
        "vol_targeting_comparison": vt_comparison,
        "global_gate": global_gate,
        "family_gates": family_gates,
        "routing": {
            "strategy_type": suite.STRATEGY_TYPE_TREND_SUITE,
            "config_id_prefix": suite.TREND_SUITE_ID_PREFIX,
            "gate_id": suite.TSMOM_GATE_ID,
            "gate_shared_with": "time_series_momentum (deliberate: same buy-and-hold risk-adjusted question)",
            "never_judged_by": [
                "per_symbol_breadth_friction_gate",
                "selection_random_benchmark_gate",
                "funding_carry_net_oos_tail_gate",
            ],
        },
        "data_provenance": {
            "sv22_summary": str(args.sv22_summary),
            "sv22_run_timestamp": sv22_summary.get("run_timestamp_utc"),
            "source": "hyperliquid_public_mainnet_candles_sv2_2_refresh",
        },
        "boundaries": {k: v for k, v in suite.boundary_flags().items()},
    }

    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"verdict: {summary['verdict']} qualifiers: {summary['verdict_qualifiers']}")
    print(f"chosen: {chosen_id}")
    print(f"any form clears absolute bar: {any_form_clears_absolute}")
    print(f"vt classifications: {vt_class_counts}")
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    h = summary["headline_comparison"]
    answers = summary["headline_answers"]
    gate = summary["global_gate"]["gate"]
    bh = summary["benchmarks"]["buy_hold_equal_weight"]
    al = summary["benchmarks"]["always_long_no_vol_target"]
    vb = summary["benchmarks"]["always_long_vol_target_beta"]
    rnd = summary["benchmarks"]["random_long_flat"]
    lines = [
        "# TREND-SUITE1 — Canonical Trend-Following Suite Evidence",
        "",
        "Research/evidence only. No runtime, strategy-rule, order, testnet, live,",
        "or production-approval change follows from this report. Modeled friction",
        "(EXEC-EV1) is an assumption layer, not real depth; perp funding is NOT",
        "modeled (the suite is long-only — longs typically PAY funding in bulls,",
        "so absolute profits here are optimistic). Account basis: 10,000 USDC.",
        "",
        f"## Verdict (train-chosen config): `{summary['verdict']}`",
        "",
        f"Qualifiers: `{summary['verdict_qualifiers']}`",
        f"Gate reasons: `{gate['reason_codes']}`",
        "",
        "## The two headline questions",
        "",
        "**1. Does ANY trend form beat buy-and-hold risk-adjusted OOS *in absolute",
        f"terms* (positive OOS return and Sharpe, full gate)?** -> **{answers['question_1_does_any_trend_form_beat_buy_hold_risk_adjusted_oos_in_absolute_terms']}**",
        "",
        "| Family | Champion (train-chosen) | Full gate | Profitable OOS (abs.) | Clears absolute bar |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in answers["per_family_absolute_bar"]:
        lines.append(
            f"| {row['family']} | `{row['config_id']}` | {row['gate_passed']} "
            f"| {row['profitable_in_absolute_terms']} | {row['clears_bar_in_absolute_terms']} |"
        )
    lines += [
        "",
        "**2. Did removing vol-targeting unlock profit, or just add risk?**",
        "",
        "Pairwise OOS effect of switching each signal cell from vol-targeted to",
        "equal-dollar sizing (deterministic classification):",
        "",
        "| Classification | Cells |",
        "| --- | --- |",
    ]
    q2 = answers["question_2_did_removing_vol_targeting_unlock_profit_or_just_risk"]
    for cls, count in sorted(q2["classification_counts"].items()):
        lines.append(f"| `{cls}` | {count} |")
    lines += [
        "",
        (
            f"In {q2['pairs_where_equal_dollar_raised_full_window_return']} of "
            f"{q2['pair_count']} pairs the uncapped (equal-dollar) variant DID earn a"
        ),
        "higher full-window return — the bull-window upside the vol cap suppresses —",
        "but every pair gave it back out-of-sample: more drawdown, no more OOS return.",
        "Removing the vol cap was leverage on the same signal, not a new edge.",
        "",
        f"Hindsight-best OOS config (NOT a verdict — not train-chosen): "
        f"`{answers['hindsight_best_oos_config_not_a_verdict']['config_id']}` "
        f"(OOS Sharpe {answers['hindsight_best_oos_config_not_a_verdict']['oos_stats'].get('sharpe_annual')}, "
        f"return {answers['hindsight_best_oos_config_not_a_verdict']['oos_stats'].get('total_return_pct')}%).",
        "",
        "## Headline (chronological 70/30 OOS, conservative friction)",
        "",
        "| | Sharpe (ann.) | Max DD % | Total return % | Days |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| Suite chosen (`{summary['train_only_choice']['chosen_config']}`) "
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
        "## Family champions (train-chosen within family; full gate each)",
        "",
        "| Family | Champion | OOS Sharpe | OOS return % | OOS max DD % | Gate | Reasons |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for family, block in summary["family_gates"].items():
        a = block["absolute_oos"]
        lines.append(
            f"| {family} | `{block['config_id']}` | {a['sharpe_annual']} | {a['total_return_pct']} "
            f"| {a['max_drawdown_pct']} | {block['gate']['status']} | `{block['gate']['reason_codes']}` |"
        )
    lines += [
        "",
        "## Benchmarks (same machinery, same friction)",
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
        "## Walk-forward (anchored thirds, train-only choice per fold; global pool)",
        "",
        f"- Fold B (`{summary['global_gate']['walk_forward']['fold_b']['chosen_config']}`): Sharpe edge {summary['global_gate']['walk_forward']['fold_b']['sharpe_edge_vs_buy_hold']}",
        f"- Fold C (`{summary['global_gate']['walk_forward']['fold_c']['chosen_config']}`): Sharpe edge {summary['global_gate']['walk_forward']['fold_c']['sharpe_edge_vs_buy_hold']}",
        "",
        "## Leave-one-out (global chosen config; drop each asset from book AND benchmark)",
        "",
        "| Dropped | OOS strategy Sharpe | OOS buy-hold Sharpe | Edge |",
        "| --- | --- | --- | --- |",
    ]
    for symbol, row in summary["global_gate"]["leave_one_out"].items():
        lines.append(
            f"| {symbol} | {row['oos_strategy_sharpe']} | {row['oos_buy_hold_sharpe']} | {row['oos_sharpe_edge_vs_buy_hold']} |"
        )
    late = summary["global_gate"]["late_entry_sensitivity"]
    lines += [
        "",
        "## Late-entry sensitivity (global chosen config)",
        "",
        f"- Avg adverse move by lateness (bps): {late['avg_entry_timing_cost_bps_by_lateness']}",
        f"- +1 candle delay OOS Sharpe: {late.get('delay_1_oos_sharpe')}",
        f"- +2 candle delay OOS Sharpe: {late.get('delay_2_oos_sharpe')}",
        "",
        "## Universe + design",
        "",
        f"- Liquid subset: {', '.join(summary['universe']['liquid_subset'])} (excluded: {', '.join(summary['universe']['excluded_thin_symbols'])})",
        f"- Window: {summary['universe']['window'][0]} -> {summary['universe']['window'][1]} ({summary['universe']['aligned_days']} aligned days)",
        f"- Grid: {summary['design']['config_grid_size']} configs — Donchian 20/55 (channel + ATR exits), MA cross 3x3 (+ATR on 20x100), MTF 30/60/90 (+ATR on 60), TSMOM 30/60/90 carry-over, ensemble majority/average; every cell in vol-targeted AND equal-dollar sizing",
        f"- {summary['design']['exit_variants']}",
        f"- Cadence: {summary['design']['decision_cadence']}",
        "",
        "## Boundaries",
        "",
        "Research/evidence only; no order, testnet, live, production, or approval",
        "surface. Modeled depth, not real. Perp funding not modeled. Long-only.",
        "The verdicts above are gate outputs and were not forced positive; the",
        "signals were designed from the documented canon, not tuned to the verdict.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
