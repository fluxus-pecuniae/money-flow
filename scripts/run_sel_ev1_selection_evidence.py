#!/usr/bin/env python3
"""Build SEL-EV1 cross-sectional selection evidence from SV2.2 candles.

SEL-EV1 is research/evidence only. It tests the founder's selection hypothesis
(approach b): rank the 23-symbol universe each closed candle on breakout /
volatility-adjusted relative strength, hold the top-1 / top-3 names, rotate as
leadership changes. The honesty bar is NOT raw PnL: the strategy must beat a
matched-cadence RANDOM-selection benchmark out-of-sample after conservative
depth-aware (EXEC-EV1) friction, beat naive baselines, actually rotate (not be
a secret single-name bet), and survive train-only parameter choice under both
chronological 70/30 and anchored walk-forward thirds splits.

Reads SV2.2 raw candle artifacts from disk; no network I/O, no runtime
mutation, no orders, no private/signed/testnet/live endpoints, no production
or live approval. Deterministic (fixed seeds, Decimal arithmetic).

Run locally:
    .venv/bin/python scripts/run_sel_ev1_selection_evidence.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence


def _load_sel_ev1():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "services"
        / "strategy_validation"
        / "sel_ev1.py"
    )
    spec = importlib.util.spec_from_file_location("sel_ev1_runner_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load SEL-EV1 module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sel_ev1 = _load_sel_ev1()

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "SEL-EV1"
REPORT_NAME = "sel_ev1_selection_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_SUMMARY_OUTPUT = Path("docs/sel_ev1_selection_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/sel_ev1_selection_evidence.md")
GATE_SCENARIO_ID = "exec_ev1_conservative"
REFERENCE_SCENARIO_IDS = ("exec_ev1_base", "exec_ev1_conservative", "exec_ev1_stress")
DEFAULT_RANDOM_SEED_COUNT = 50
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--random-seed-count", type=int, default=DEFAULT_RANDOM_SEED_COUNT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def load_universes(sv22_summary_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = json.loads(sv22_summary_path.read_text(encoding="utf-8"))
    if summary.get("phase") != "SV2.2":
        raise ValueError("sel_ev1_requires_sv2_2_summary_input")
    by_timeframe: dict[str, list[Any]] = {tf: [] for tf in sel_ev1.SELECTION_TIMEFRAMES}
    for row in summary.get("datasets", []):
        timeframe = row.get("timeframe")
        if row.get("status") != "refreshed" or timeframe not in by_timeframe:
            continue
        raw_path = row.get("raw_path")
        if not raw_path or not Path(raw_path).exists():
            continue
        payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        by_timeframe[timeframe].append(
            sel_ev1.dataset_from_sv22_payload(payload, source_path=str(raw_path))
        )
    universes = {
        timeframe: sel_ev1.SelectionUniverse(datasets)
        for timeframe, datasets in by_timeframe.items()
        if datasets
    }
    return summary, universes


def union_timeline(universes: dict[str, Any]) -> tuple[datetime, ...]:
    return tuple(sorted({t for u in universes.values() for t in u.timeline}))


def per_config_row(
    config: Any, result: dict[str, Any], split_time: datetime
) -> dict[str, Any]:
    trades = result["trades"]
    train = sel_ev1.window_metrics(trades, up_to=split_time)
    test = sel_ev1.window_metrics(trades, after=split_time)
    diversity = sel_ev1.rotation_diversity_metrics(result)
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "signal": config.signal,
        "lookback": config.lookback,
        "top_n": config.top_n,
        "timeframe": config.timeframe,
        "slot_fraction": config.slot_fraction,
        "full_metrics": sel_ev1._metrics_to_dict(result["metrics"]),
        "train_net_pnl": train.net_pnl,
        "train_trade_count": train.trade_count,
        "oos_net_pnl": test.net_pnl,
        "oos_trade_count": test.trade_count,
        "oos_max_drawdown_pct": test.max_drawdown_pct,
        "avg_friction_bps": result["avg_friction_bps"],
        "friction_paid_quote": result["friction_paid_quote"],
        "diversity": diversity,
    }


def walk_forward_thirds(
    results_by_config: dict[str, dict[str, Any]],
    timeline: Sequence[datetime],
) -> dict[str, Any]:
    """Anchored walk-forward thirds with train-only parameter choice per fold."""
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]
    fold_a_choice = sel_ev1.select_best_config_id(results_by_config, train_up_to=t1)
    fold_a_net = sel_ev1.trades_net_pnl(
        results_by_config[fold_a_choice]["trades"], after=t1, up_to=t2
    )
    fold_b_choice = sel_ev1.select_best_config_id(results_by_config, train_up_to=t2)
    fold_b_net = sel_ev1.trades_net_pnl(results_by_config[fold_b_choice]["trades"], after=t2)
    return {
        "method": "anchored_walk_forward_thirds",
        "cut_1": sel_ev1._iso(t1),
        "cut_2": sel_ev1._iso(t2),
        "fold_a_chosen_config": fold_a_choice,
        "fold_a_test_net_pnl": fold_a_net,
        "fold_b_chosen_config": fold_b_choice,
        "fold_b_test_net_pnl": fold_b_net,
        "combined_test_net_pnl": sel_ev1._money(fold_a_net + fold_b_net),
    }


def render_report(summary: dict[str, Any]) -> str:
    headline = summary["headline_comparison"]
    gate = summary["selection_gate"]
    random_dist = gate["random_oos_distribution"]
    grid_rows = [
        (
            "| `{config_id}` | `{train_net_pnl}` | `{oos_net_pnl}` | `{oos_trades}` | "
            "`{distinct}` | `{single}` |"
        ).format(
            config_id=row["config_id"],
            train_net_pnl=row["train_net_pnl"],
            oos_net_pnl=row["oos_net_pnl"],
            oos_trades=row["oos_trade_count"],
            distinct=row["diversity"]["distinct_symbols_held"],
            single=row["diversity"]["single_name_bet"],
        )
        for row in summary["per_config_results"]
    ]
    late = summary["late_entry_sensitivity"]
    late_rows = [
        "| `+{lateness}` | `{full_net_pnl}` | `{oos_net_pnl}` | `{avg_entry_timing_cost_bps}` |".format(
            **row
        )
        for row in late["by_lateness"]
    ]
    scenario_rows = [
        "| `{scenario_id}` | `{full_net_pnl}` | `{oos_net_pnl}` | `{avg_friction_bps}` | `{friction_paid_quote}` |".format(
            **row
        )
        for row in summary["friction_scenario_comparison"]
    ]
    lines = [
        "# SEL-EV1 Cross-Sectional Breakout Selection Evidence",
        "",
        "## Verdict",
        "",
        f"- **Verdict: `{summary['verdict']}`**",
        f"- Gate reason codes: {', '.join(f'`{r}`' for r in gate['reason_codes'])}",
        "- The bar is beating a matched-cadence random-selection benchmark "
        "out-of-sample after conservative depth-aware friction — not raw PnL.",
        "- Research/evidence only: no runtime mutation, no strategy-rule change, no "
        "orders, no private/signed/testnet/live endpoints, no production or live approval.",
        "",
        "## Strategy-Type Routing Seam (Must 0)",
        "",
        "- `per_symbol` (approach a — Money Flow / MF-ORIG / avoid_low lanes) and "
        "`cross_sectional_selection` (approach b — this phase) are parallel research "
        "tracks with separate simulators, gates, and evaluations.",
        "- The per-symbol breadth/anti-concentration gate never judges a selection "
        "strategy (point-in-time concentration is the design here), and the selection "
        "random-benchmark gate never judges a per-symbol strategy. Cross-application "
        "raises `StrategyTypeRoutingError`.",
        "- Per-symbol lane behavior and results are unchanged (byte-identical "
        "regression check in `tests/test_sel_ev1_selection_evidence.py`).",
        "",
        "## Hypothesis + Mechanics (Must 1-2)",
        "",
        f"- Universe: founder 23-symbol Hyperliquid set over SV2.2 public-mainnet candles; timeframes {summary['timeframes']}.",
        "- At each closed candle: score every symbol point-in-time, rank, hold the "
        "top-1 / top-3 (score must be > 0), enter at the NEXT candle open, hold while "
        "still top-ranked, rotate/exit otherwise; ATR(14) x 2.8 trailing stop.",
        "- Signals (bounded; train-only choice): `donchian_breakout_strength` = (close - "
        "prior N-high) / ATR; `vol_adjusted_relative_momentum` = N-return / (ATR/close); "
        f"lookbacks {list(sel_ev1.SELECTION_LOOKBACKS)}.",
        "- Sizing (explicit): fixed fraction of current equity per held name — top-1 -> "
        "50%, top-3 -> 30% each. Never full-equity-on-one-name (the ZEC inflater).",
        "- Friction: EXEC-EV1 depth-aware model on EVERY entry/exit/rotation fill "
        "(tier half-spread + sqrt participation impact + fill-probability chase on top "
        "of SV2.3 fee/slippage/adverse-gap). Depth is MODELED from candle volume, not real.",
        f"- OOS: chronological 70/30 split at `{summary['chronological_split_time']}`; "
        "anchored walk-forward thirds; parameters chosen on train only.",
        "",
        "## Headline — Strategy vs Random Selection (OOS, post-conservative-friction)",
        "",
        f"- Train-chosen config: `{headline['chosen_config_id']}` (best train net PnL).",
        f"- Strategy OOS net PnL: `{headline['strategy_oos_net_pnl']}` over `{headline['strategy_oos_trade_count']}` trades.",
        f"- Random-selection OOS distribution ({random_dist.get('count', 0)} seeds, matched cadence): "
        f"median `{random_dist.get('median')}`, mean `{random_dist.get('mean')}`, "
        f"p95 `{random_dist.get('p95')}` (bar), max `{random_dist.get('max')}`.",
        f"- Random seeds beaten: `{gate['random_seeds_beaten']}` of `{random_dist.get('count', 0)}`; "
        f"empirical p-value vs random: `{gate['empirical_p_value_vs_random']}`.",
        f"- Equal-weight buy-and-hold (OOS window): `{headline['equal_weight_buy_hold_oos_net_pnl']}`.",
        f"- Naive highest-past-return top-1 (OOS): `{headline['naive_past_return_oos_net_pnl']}`.",
        f"- Anchored walk-forward thirds combined test net: `{summary['walk_forward']['combined_test_net_pnl']}`.",
        "",
        "## Rotation / Diversity (reframed ZEC check)",
        "",
        f"- Distinct symbols held: `{gate['diversity']['distinct_symbols_held']}`; rotations: `{gate['diversity']['rotation_count']}`.",
        f"- Max single-symbol time-in-position share: `{gate['diversity']['max_single_symbol_time_share']}` "
        f"(threshold `{gate['diversity']['max_time_share_threshold']}`).",
        f"- Max single-symbol positive-PnL share: `{gate['diversity']['max_single_symbol_positive_pnl_share']}` "
        f"(threshold `{gate['diversity']['max_positive_pnl_share_threshold']}`).",
        f"- Single-name bet flag: `{gate['diversity']['single_name_bet']}`.",
        "",
        "## Bounded Grid (conservative friction; train / OOS by entry time)",
        "",
        "| Config | Train net | OOS net | OOS trades | Distinct symbols | Single-name? |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        *grid_rows,
        "",
        "## Friction Impact (chosen config across EXEC-EV1 scenarios)",
        "",
        "| Scenario | Full net | OOS net | Avg friction bps | Friction paid (quote) |",
        "| --- | ---: | ---: | ---: | ---: |",
        *scenario_rows,
        "",
        "## Late-Entry Sensitivity (Must 5; chosen config, conservative friction)",
        "",
        "Selection chases breakouts, so entry timing is acute. `+k` = filled k candles",
        "after the normal next-open fill. Connects to the RT-HISTSEED1 question.",
        "",
        "| Lateness | Full net | OOS net | Avg entry-timing cost bps |",
        "| --- | ---: | ---: | ---: |",
        *late_rows,
        "",
        "## Boundaries",
        "",
        *[f"- `{key}`: `{value}`" for key, value in summary["boundaries"].items()],
        "",
        "## Honest Caveats",
        "",
        "- Depth/liquidity is modeled from historical candle volume, never real "
        "order-book depth; every cost is an assumption.",
        "- A single historical period; OOS here is still one market regime.",
        "- The random benchmark shares the strategy's trade cadence; it does not "
        "answer whether the *cadence itself* (vs buy-and-hold) is wise.",
        "- If the verdict is `no_selection_skill_demonstrated`, that is a real result "
        "on a genuinely new hypothesis, not a failure of the harness.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    run_timestamp = args.run_timestamp or generated_at.strftime("%Y%m%dT%H%M%SZ")
    sv22_summary, universes = load_universes(args.sv22_summary)
    if not universes:
        print("No SV2.2 datasets available for SEL-EV1 timeframes")
        return 2
    timeline = union_timeline(universes)
    split_time = timeline[int(len(timeline) * float(CHRONOLOGICAL_TRAIN_RATIO))]
    gate_scenario = scenario_by_id(GATE_SCENARIO_ID)
    seeds = tuple(range(1, args.random_seed_count + 1))

    configs = [
        config
        for config in sel_ev1.generate_selection_configs()
        if config.timeframe in universes
    ]
    results_by_config: dict[str, dict[str, Any]] = {}
    config_by_id: dict[str, Any] = {}
    for config in configs:
        results_by_config[config.config_id] = sel_ev1.simulate_selection_portfolio(
            universes[config.timeframe], config, gate_scenario
        )
        config_by_id[config.config_id] = config
        print(f"simulated {config.config_id}")

    per_config = [
        per_config_row(config_by_id[config_id], result, split_time)
        for config_id, result in sorted(results_by_config.items())
    ]

    chosen_id = sel_ev1.select_best_config_id(results_by_config, train_up_to=split_time)
    chosen_config = config_by_id[chosen_id]
    chosen_result = results_by_config[chosen_id]
    chosen_universe = universes[chosen_config.timeframe]
    oos_metrics = sel_ev1.window_metrics(chosen_result["trades"], after=split_time)
    diversity = sel_ev1.rotation_diversity_metrics(chosen_result)

    # Truth serum 1: matched-cadence random benchmark (many seeds).
    cadence = frozenset(chosen_result["decision_timestamps"])
    random_results = sel_ev1.random_selection_benchmark(
        chosen_universe, chosen_config, gate_scenario, seeds=seeds, rebalance_timestamps=cadence
    )
    random_oos_nets = [
        sel_ev1.trades_net_pnl(result["trades"], after=split_time) for result in random_results
    ]
    random_full_nets = [result["metrics"].net_pnl for result in random_results]
    print(f"random benchmark complete: {len(random_results)} seeds")

    # Truth serum 2: naive baselines.
    buy_hold_full = sel_ev1.equal_weight_buy_hold(chosen_universe, gate_scenario)
    buy_hold_oos = sel_ev1.equal_weight_buy_hold(
        chosen_universe, gate_scenario, start_time=split_time
    )
    naive_config = sel_ev1.naive_past_return_config(chosen_config.timeframe)
    naive_result = sel_ev1.simulate_selection_portfolio(
        chosen_universe, naive_config, gate_scenario
    )
    naive_oos_net = sel_ev1.trades_net_pnl(naive_result["trades"], after=split_time)

    # OOS method 2: anchored walk-forward thirds (train-only choice per fold).
    walk_forward = walk_forward_thirds(results_by_config, timeline)

    gate = sel_ev1.evaluate_selection_gate(
        strategy_type=chosen_config.strategy_type,
        oos_net_pnl=oos_metrics.net_pnl,
        oos_trade_count=oos_metrics.trade_count,
        walk_forward_oos_net_pnl=walk_forward["combined_test_net_pnl"],
        random_oos_net_pnls=random_oos_nets,
        diversity=diversity,
    )

    # Must 5: late-entry sensitivity (+1 / +2 candles late).
    late_rows = []
    for lateness in sel_ev1.LATE_ENTRY_LATENESS_STEPS:
        if lateness == 0:
            late_result = chosen_result
        else:
            from dataclasses import replace as dc_replace

            late_config = dc_replace(
                chosen_config,
                config_id=f"{chosen_id}_late{lateness}",
                entry_delay_candles=lateness,
            )
            late_result = sel_ev1.simulate_selection_portfolio(
                chosen_universe, late_config, gate_scenario
            )
        late_rows.append(
            {
                "lateness": lateness,
                "full_net_pnl": late_result["metrics"].net_pnl,
                "oos_net_pnl": sel_ev1.trades_net_pnl(late_result["trades"], after=split_time),
                "avg_entry_timing_cost_bps": chosen_result[
                    "entry_timing_cost_bps_by_lateness"
                ][lateness],
            }
        )
    print("late-entry sensitivity complete")

    # Friction impact: chosen config across the three EXEC-EV1 scenarios.
    scenario_rows = []
    for scenario_id in REFERENCE_SCENARIO_IDS:
        if scenario_id == GATE_SCENARIO_ID:
            reference = chosen_result
        else:
            reference = sel_ev1.simulate_selection_portfolio(
                chosen_universe, chosen_config, scenario_by_id(scenario_id)
            )
        scenario_rows.append(
            {
                "scenario_id": scenario_id,
                "full_net_pnl": reference["metrics"].net_pnl,
                "oos_net_pnl": sel_ev1.trades_net_pnl(reference["trades"], after=split_time),
                "avg_friction_bps": reference["avg_friction_bps"],
                "friction_paid_quote": reference["friction_paid_quote"],
            }
        )

    summary: dict[str, Any] = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "generated_at_utc": sel_ev1._iso(generated_at),
        "run_timestamp": run_timestamp,
        "status": "selection_evidence_complete",
        "verdict": gate["status"],
        "supersedes": {
            "goal_strat3_breadth_gate": (
                "GOAL-STRAT3 (planned per-symbol breadth gate) is superseded by "
                "SEL-EV1: the breadth lens is wrong for a strategy designed to "
                "concentrate. The ZEC lesson is reframed as the rotation/diversity "
                "check. The breadth-gate idea is deferred, not deleted."
            )
        },
        "strategy_type_routing": sel_ev1.routing_policy(),
        "source": {
            "input_summary": str(args.sv22_summary),
            "input_phase": sv22_summary.get("phase"),
            "strategy_truth": "public_hyperliquid_mainnet_candles_from_sv2_2_refresh",
            "network_fetch_performed": False,
            "real_order_book_depth_used": False,
        },
        "timeframes": sorted(universes),
        "symbols_by_timeframe": {tf: list(u.symbols) for tf, u in sorted(universes.items())},
        "timeline_start": sel_ev1._iso(timeline[0]),
        "timeline_end": sel_ev1._iso(timeline[-1]),
        "chronological_split_time": sel_ev1._iso(split_time),
        "gate_scenario_id": GATE_SCENARIO_ID,
        "random_seed_count": len(seeds),
        "sizing_policy": {
            "description": "fixed fraction of current equity per held name",
            "slot_fraction_top_1": sel_ev1.SLOT_FRACTION_BY_TOP_N[1],
            "slot_fraction_top_3": sel_ev1.SLOT_FRACTION_BY_TOP_N[3],
            "full_equity_on_one_name": False,
        },
        "per_config_results": per_config,
        "headline_comparison": {
            "chosen_config_id": chosen_id,
            "chosen_on": "train_net_pnl_only",
            "strategy_oos_net_pnl": oos_metrics.net_pnl,
            "strategy_oos_trade_count": oos_metrics.trade_count,
            "random_oos_net_pnl_distribution": sel_ev1.distribution_stats(random_oos_nets),
            "random_full_net_pnl_distribution": sel_ev1.distribution_stats(random_full_nets),
            "equal_weight_buy_hold_full_net_pnl": buy_hold_full["net_pnl"],
            "equal_weight_buy_hold_oos_net_pnl": buy_hold_oos["net_pnl"],
            "naive_past_return_config_id": naive_config.config_id,
            "naive_past_return_full_net_pnl": naive_result["metrics"].net_pnl,
            "naive_past_return_oos_net_pnl": naive_oos_net,
        },
        "selection_gate": gate,
        "walk_forward": walk_forward,
        "late_entry_sensitivity": {
            "chosen_config_id": chosen_id,
            "by_lateness": late_rows,
        },
        "friction_scenario_comparison": scenario_rows,
        "chosen_config_trades_sample": [
            sel_ev1._trade_to_dict(trade) for trade in chosen_result["trades"][:200]
        ],
        "boundaries": sel_ev1.boundary_flags(),
    }
    summary = sel_ev1._json_ready(summary)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_report(summary), encoding="utf-8")
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"Verdict: {summary['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
