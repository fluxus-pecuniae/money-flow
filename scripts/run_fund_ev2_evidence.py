#!/usr/bin/env python3
"""Build FUND-EV2 funding-carry-under-realistic-costs evidence.

FUND-EV2 is research/evidence only. It re-tests the FUND-EV1 question with
CITED per-venue costs instead of the deliberately conservative widest-tier
guess: does net funding survive realistic costs OOS — or was FUND-EV1's
fail a real absence of capturable edge? Both venue constructions are
modeled with their honest costs AND risks (hl_single: tight coupling,
HL spot fees; cross_venue: deep Kraken spot but 40 bps retail taker fee +
transfer friction + legged execution), entries are selective (expected
funding over the planned hold must clear 2x round-trip cost), holds are
longer (14/28d cadence, 2% band), and a cost-sensitivity sweep reports the
exact cost level where the OOS edge dies. Parameters chosen on train only;
the gate never forces a positive; costs are never lowered to flip it.

Inputs: SV2.2 perp candles + FUND-EV1 funding snapshot + FUND-EV1 HL spot
candles + the FUND-EV2 l2Book calibration (citations only). No network I/O,
no runtime mutation, no orders, no private/signed/testnet/live endpoints.

Run locally:
    .venv/bin/python scripts/run_fund_ev2_evidence.py
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


ev2 = _load_module("services/strategy_validation/fund_ev2.py", "fund_ev2_runner_module")
fund = ev2.fund_ev1

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "FUND-EV2"
REPORT_NAME = "fund_ev2_realistic_cost_carry_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_FUNDING_SNAPSHOT_INPUT = Path("docs/fund_ev1_funding_data_snapshot_summary.json")
DEFAULT_L2_CALIBRATION_INPUT = Path("docs/fund_ev2_l2book_calibration_summary.json")
DEFAULT_SPOT_RAW_DIR = Path("/tmp/money-flow-fund-ev1/raw_spot_candles")
DEFAULT_SUMMARY_OUTPUT = Path("docs/fund_ev2_realistic_cost_carry_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/fund_ev2_realistic_cost_carry_evidence.md")
# The scenario object is unused on the cited-cost path (the cost model owns
# every term); it is passed for the FUND-EV1-reference rows only.
GATE_SCENARIO_ID = "exec_ev1_conservative"
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")
STRESS_COST_SCALE = Decimal("2.0")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--funding-snapshot", type=Path, default=DEFAULT_FUNDING_SNAPSHOT_INPUT)
    parser.add_argument("--l2-calibration", type=Path, default=DEFAULT_L2_CALIBRATION_INPUT)
    parser.add_argument("--spot-raw-dir", type=Path, default=DEFAULT_SPOT_RAW_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def load_universe(sv22_path: Path, snapshot_path: Path, spot_dir: Path):
    runner_v1 = _load_module("scripts/run_fund_ev1_evidence.py", "fund_ev1_runner_for_v2")
    return runner_v1.load_universe(sv22_path, snapshot_path, spot_dir)


def _s(value: Any) -> Any:
    return str(value) if isinstance(value, Decimal) else value


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: _s(v) for k, v in stats.items()}


def simulate(universe, config, scale: Decimal = Decimal("1.0"), **kwargs):
    model = ev2.cost_model_for(config.venue_construction, scale)
    return fund.simulate_funding_carry_portfolio(
        universe, config, scenario_by_id(GATE_SCENARIO_ID), leg_cost_model=model, **kwargs
    )


def config_row(config, result, split) -> dict[str, Any]:
    full = fund.curve_stats(result["equity_curve"])
    train = fund.curve_stats(result["equity_curve"], up_to=split)
    oos = fund.curve_stats(result["equity_curve"], after=split)
    return {
        "config_id": config.config_id,
        "construction": config.venue_construction,
        "rebalance_interval_days": config.rebalance_interval_days,
        "top_k": config.top_k,
        "entry_margin_multiple": str(config.entry_margin_multiple),
        "min_trade_notional_fraction": str(config.min_trade_notional_fraction),
        "net_pnl": _s(result["net_pnl"]),
        "funding_collected_total": _s(result["funding_collected_total"]),
        "fees_total": _s(result["fees_total"]),
        "avg_friction_bps": _s(result["avg_friction_bps"]),
        "trade_count": result["trade_count"],
        "rebalance_count": result["rebalance_count"],
        "max_residual_delta_fraction": _s(result["max_residual_delta_fraction"]),
        "full_stats": _stats_str(full),
        "train_stats": _stats_str(train),
        "oos_stats": _stats_str(oos),
        "oos_net_pnl": _s(fund.window_net_pnl(result["equity_curve"], after=split)),
        "per_symbol_net_pnl": {k: _s(v) for k, v in result["per_symbol_net_pnl"].items()},
        "funding_by_symbol": {k: _s(v) for k, v in result["funding_by_symbol"].items()},
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sv22, snapshot, universe = load_universe(
        args.sv22_summary, args.funding_snapshot, args.spot_raw_dir
    )
    l2_calibration = json.loads(args.l2_calibration.read_text(encoding="utf-8"))
    configs = ev2.generate_fund_ev2_configs()
    config_by_id = {c.config_id: c for c in configs}
    split = fund.timeline_split_time(universe, CHRONOLOGICAL_TRAIN_RATIO)
    timeline = universe.timeline
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    # --- full grid at the cited realistic cost level (scale 1.0) -----------
    results_by_config: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for config in configs:
        result = simulate(universe, config)
        results_by_config[config.config_id] = result
        rows.append(config_row(config, result, split))

    # --- train-only choice (construction is part of the config) ------------
    chosen_id = fund.select_best_config_id(results_by_config, train_up_to=split)
    chosen_config = config_by_id[chosen_id]
    chosen_result = results_by_config[chosen_id]
    chosen_model = ev2.cost_model_for(chosen_config.venue_construction)
    oos_strategy_stats = fund.curve_stats(chosen_result["equity_curve"], after=split)
    train_strategy_stats = fund.curve_stats(chosen_result["equity_curve"], up_to=split)
    oos_net = fund.window_net_pnl(chosen_result["equity_curve"], after=split)

    # Best config per construction (both reported, Must 2).
    best_by_construction: dict[str, str] = {}
    for construction in ev2.CONSTRUCTIONS:
        sub = {
            cid: res
            for cid, res in results_by_config.items()
            if config_by_id[cid].venue_construction == construction
        }
        best_by_construction[construction] = fund.select_best_config_id(
            sub, train_up_to=split
        )

    # --- benchmarks ----------------------------------------------------------
    gross_result = simulate(universe, chosen_config, scale=Decimal("0"))
    costs_total = fund._money(gross_result["net_pnl"] - chosen_result["net_pnl"])
    always_on_config = replace(
        chosen_config,
        config_id=f"fund_ev2_benchmark_always_on_{chosen_config.venue_construction}",
        top_k=len(universe.symbols),
    )
    always_on_result = simulate(
        universe, always_on_config, signal_provider=fund.always_on_provider
    )
    # FUND-EV1-conservative reference: the SAME chosen config priced through
    # the old widest-tier model — the direct "was it our cost model?" probe.
    v1_reference = fund.simulate_funding_carry_portfolio(
        universe,
        replace(chosen_config, config_id=f"{chosen_id}_fund_ev1_cost_reference"),
        scenario_by_id(GATE_SCENARIO_ID),
    )

    # --- walk-forward (anchored thirds, train-only choice per fold) ---------
    fold_b_choice = fund.select_best_config_id(results_by_config, train_up_to=t1)
    fold_b_net = fund.window_net_pnl(
        results_by_config[fold_b_choice]["equity_curve"], after=t1, up_to=t2
    )
    fold_c_choice = fund.select_best_config_id(results_by_config, train_up_to=t2)
    fold_c_net = fund.window_net_pnl(
        results_by_config[fold_c_choice]["equity_curve"], after=t2
    )
    walk_forward = {
        "fold_b": {"chosen_config": fold_b_choice, "window": [str(t1), str(t2)], "net_carry": _s(fold_b_net)},
        "fold_c": {"chosen_config": fold_c_choice, "window": [str(t2), "end"], "net_carry": _s(fold_c_net)},
    }

    # --- leave-one-out -------------------------------------------------------
    leave_one_out: dict[str, Any] = {}
    loo_oos_net: dict[str, Decimal | None] = {}
    for drop in universe.symbols:
        sub_universe = fund.CarryUniverse(
            [universe.assets[s] for s in universe.symbols if s != drop]
        )
        sub_split = fund.timeline_split_time(sub_universe, CHRONOLOGICAL_TRAIN_RATIO)
        sub_result = simulate(sub_universe, chosen_config)
        sub_oos = fund.window_net_pnl(sub_result["equity_curve"], after=sub_split)
        sub_stats = fund.curve_stats(sub_result["equity_curve"], after=sub_split)
        loo_oos_net[drop] = sub_oos
        leave_one_out[drop] = {
            "oos_net_carry": _s(sub_oos),
            "oos_sharpe": _s(sub_stats["sharpe_annual"]),
            "oos_max_drawdown_pct": _s(sub_stats["max_drawdown_pct"]),
        }

    # --- regimes -------------------------------------------------------------
    regimes = fund.classify_regimes(universe)
    regime_pnls = fund.pnl_by_regime(chosen_result["equity_curve"], regimes)

    # --- tail / legged-execution stress per construction ---------------------
    def stressed_run(config):
        stressed = replace(
            config,
            config_id=f"{config.config_id}_stressed_scale2_leglag1",
            spot_leg_lag_days=1,
        )
        result = simulate(universe, stressed, scale=STRESS_COST_SCALE)
        stats = fund.curve_stats(result["equity_curve"])
        return result, stats

    stressed_result, stressed_stats = stressed_run(chosen_config)
    other_construction = (
        ev2.CONSTRUCTION_CROSS_VENUE
        if chosen_config.venue_construction == ev2.CONSTRUCTION_HL_SINGLE
        else ev2.CONSTRUCTION_HL_SINGLE
    )
    other_best = config_by_id[best_by_construction[other_construction]]
    other_stressed_result, other_stressed_stats = stressed_run(other_best)
    worst_day_move = max(
        abs(
            universe.assets[s].perp.candles[universe.perp_index[s][t]].close
            / universe.assets[s].perp.candles[universe.perp_index[s][t]].open
            - Decimal("1")
        )
        for s in universe.symbols
        for t in universe.timeline
    )
    tail_stress = {
        "worst_days_chosen_config": [
            [str(t), _s(v)] for t, v in chosen_result["worst_days"]
        ],
        "max_residual_delta_fraction": _s(chosen_result["max_residual_delta_fraction"]),
        "worst_single_candle_move_pct_in_window": _s(
            fund._money(worst_day_move * Decimal("100"))
        ),
        "stressed_run_chosen": {
            "config": stressed_result["config_id"],
            "construction": chosen_config.venue_construction,
            "cost_scale": str(STRESS_COST_SCALE),
            "spot_leg_lag_days": 1,
            "net_pnl": _s(stressed_result["net_pnl"]),
            "max_drawdown_pct": _s(stressed_stats["max_drawdown_pct"]),
            "max_residual_delta_fraction": _s(
                stressed_result["max_residual_delta_fraction"]
            ),
            "modeled_gap_loss_at_max_residual_pct_of_equity": _s(
                fund._money(
                    stressed_result["max_residual_delta_fraction"]
                    * worst_day_move
                    * Decimal("100")
                )
            ),
        },
        "stressed_run_other_construction": {
            "config": other_stressed_result["config_id"],
            "construction": other_best.venue_construction,
            "net_pnl": _s(other_stressed_result["net_pnl"]),
            "max_drawdown_pct": _s(other_stressed_stats["max_drawdown_pct"]),
            "max_residual_delta_fraction": _s(
                other_stressed_result["max_residual_delta_fraction"]
            ),
        },
        "legging_resolution_note": (
            "daily-candle resolution makes the legged stress hold one-leg exposure "
            "for a full day; real cross-venue legging is typically minutes-hours, so "
            "the stress OVERSTATES duration while honestly bounding the gap exposure"
        ),
    }

    # --- cost-sensitivity sweep (adaptive: the strategy re-decides at each
    # cost level — selectivity may go flat as costs rise, which reads as the
    # edge dying; trade_count makes the adaptation visible) -------------------
    sweep_rows: list[dict[str, Any]] = []
    for scale in ev2.SWEEP_SCALES:
        r = simulate(universe, chosen_config, scale=scale)
        sweep_rows.append(
            {
                "scale": str(scale),
                "oos_net_pnl": _s(fund.window_net_pnl(r["equity_curve"], after=split)),
                "full_net_pnl": _s(r["net_pnl"]),
                "trade_count": r["trade_count"],
                "funding_collected_total": _s(r["funding_collected_total"]),
            }
        )

    # --- the gate (same bar, realistic costs, plus sensitivity) -------------
    gate = ev2.evaluate_funding_carry_gate_v2(
        cost_sensitivity_sweep=sweep_rows,
        strategy_type=chosen_config.strategy_type,
        oos_strategy_stats=oos_strategy_stats,
        oos_net_pnl=oos_net,
        walk_forward_net_pnls=[fold_b_net, fold_c_net],
        regime_pnls=regime_pnls,
        leave_one_out_oos_net=loo_oos_net,
        stressed_max_drawdown_pct=stressed_stats["max_drawdown_pct"],
    )

    def bench_block(result) -> dict[str, Any]:
        return {
            "config_id": result["config_id"],
            "net_pnl": _s(result["net_pnl"]),
            "funding_collected_total": _s(result["funding_collected_total"]),
            "fees_total": _s(result["fees_total"]),
            "trade_count": result["trade_count"],
            "full_stats": _stats_str(fund.curve_stats(result["equity_curve"])),
            "oos_net_pnl": _s(fund.window_net_pnl(result["equity_curve"], after=split)),
            "oos_stats": _stats_str(fund.curve_stats(result["equity_curve"], after=split)),
        }

    def gate_json(g: dict[str, Any]) -> dict[str, Any]:
        def conv(v):
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, dict):
                return {k: conv(x) for k, x in v.items()}
            if isinstance(v, list):
                return [conv(x) for x in v]
            return v

        return {k: conv(v) for k, v in g.items()}

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "funding_carry_realistic_cost_evidence_complete",
        "verdict": gate["status"],
        "account_size_usdc": str(fund.STARTING_EQUITY),
        "discipline_guard": {
            "costs_cited_not_tuned": True,
            "sources": [
                "Hyperliquid fee schedule (docs, fetched 2026-06-11): perp taker 4.5 bps, spot taker 7 bps (base tier)",
                "Hyperliquid public l2Book one-shot calibration 2026-06-11: docs/fund_ev2_l2book_calibration_summary.json",
                "Kraken Pro fee schedule (fetched 2026-06-11): spot taker 40 bps base tier (Coinbase Advanced base tier worse at 60 bps)",
                "Cross-venue settlement: flat 2 USDC per spot fill (documented assumption)",
            ],
            "one_honest_retest_no_fund_ev3_cost_tweak": True,
        },
        "universe": {
            "carry_universe": list(fund.CARRY_UNIVERSE),
            "spot_pairs": dict(fund.SPOT_PAIR_BY_SYMBOL),
            "timeframe": fund.CARRY_TIMEFRAME,
            "aligned_days": len(universe.timeline),
            "window": [str(universe.timeline[0]), str(universe.timeline[-1])],
        },
        "design": {
            "constructions": {
                ev2.CONSTRUCTION_HL_SINGLE: ev2.hl_single_cost_model().describe(),
                ev2.CONSTRUCTION_CROSS_VENUE: ev2.cross_venue_cost_model().describe(),
            },
            "round_trip_cost_bps_at_2500_notional": {
                construction: {
                    s: _s(ev2.cost_model_for(construction).round_trip_cost_bps(s, Decimal("2500")))
                    for s in fund.CARRY_UNIVERSE
                }
                for construction in ev2.CONSTRUCTIONS
            },
            "selectivity": (
                f"enter only when trailing-{fund.FUNDING_LOOKBACK_DAYS}d mean funding x planned hold "
                f">= {ev2.ENTRY_MARGIN_MULTIPLE}x round-trip cost; hold while trailing stays favorable"
            ),
            "holds": f"cadence {list(ev2.V2_CADENCES_DAYS)} days; rebalance band {ev2.WIDE_BAND_FRACTION} of equity",
            "config_grid_size": len(configs),
            "mode": "collect_only (flip side needs unmodeled spot borrow; not leaned on)",
        },
        "chronological_split": {
            "train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO),
            "split_time": str(split),
        },
        "train_only_choice": {
            "criterion": "best train-window Sharpe at cited realistic costs (scale 1.0)",
            "chosen_config": chosen_id,
            "chosen_construction": chosen_config.venue_construction,
            "best_by_construction": best_by_construction,
        },
        "headline": {
            "strategy_oos": _stats_str(oos_strategy_stats),
            "strategy_train": _stats_str(train_strategy_stats),
            "oos_net_carry": _s(oos_net),
            "full_net_pnl": _s(chosen_result["net_pnl"]),
            "full_funding_collected": _s(chosen_result["funding_collected_total"]),
            "gross_carry_zero_cost_net": _s(gross_result["net_pnl"]),
            "costs_total_vs_zero_cost": _s(costs_total),
            "cost_share_of_gross_pct": _s(
                fund._money(costs_total / gross_result["net_pnl"] * Decimal("100"))
                if gross_result["net_pnl"] > 0
                else None
            ),
            "fund_ev1_cost_reference_same_config": {
                "net_pnl": _s(v1_reference["net_pnl"]),
                "oos_net_pnl": _s(fund.window_net_pnl(v1_reference["equity_curve"], after=split)),
                "note": "the SAME chosen config priced through FUND-EV1's widest-tier model",
            },
        },
        "cost_sensitivity_sweep": {
            "rows": sweep_rows,
            "breakpoint_scale_where_oos_edge_dies": gate["cost_sensitivity"][
                "breakpoint_scale_where_oos_edge_dies"
            ],
            "semantics": (
                "adaptive sweep: the strategy re-decides entries at each cost scale; "
                "selectivity going flat at high cost reads as net 0 = edge dead"
            ),
        },
        "benchmarks": {
            "gross_funding_zero_cost_same_config": bench_block(gross_result),
            "always_on_carry_all_names": bench_block(always_on_result),
            "cash": {"config_id": "hold_10000_usdc", "net_pnl": "0", "max_drawdown_pct": "0"},
        },
        "per_config_results": rows,
        "walk_forward": walk_forward,
        "leave_one_out": leave_one_out,
        "regimes": {
            "classification": (
                f"BTC perp trailing {fund.REGIME_TRAILING_DAYS}d return, point-in-time; "
                f"bear < -{fund.REGIME_BAND}, bull > +{fund.REGIME_BAND}"
            ),
            "chosen_config_pnl_by_regime": {
                label: {"days": row["days"], "net_pnl": _s(row["net_pnl"])}
                for label, row in regime_pnls.items()
            },
        },
        "tail_stress": tail_stress,
        "funding_carry_gate": gate_json(gate),
        "routing": {
            "strategy_type": fund.STRATEGY_TYPE_FUNDING_CARRY,
            "gate_id": fund.FUNDING_CARRY_GATE_ID,
            "config_id_prefix": "fund_ev2_",
        },
        "data_provenance": {
            "perp_candles": "hyperliquid_public_mainnet_candles_sv2_2_refresh",
            "funding": {
                "snapshot_summary": str(args.funding_snapshot),
                "fetched_at_utc": snapshot.get("fetched_at_utc"),
            },
            "spot_candles_raw_dir": str(args.spot_raw_dir),
            "l2book_calibration": {
                "summary": str(args.l2_calibration),
                "fetched_at_utc": l2_calibration.get("fetched_at_utc"),
            },
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        },
        "boundaries": {k: v for k, v in ev2.boundary_flags().items()},
    }

    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"verdict: {gate['status']}")
    print(f"reasons: {gate['reason_codes']}")
    print(
        "breakpoint scale:",
        gate["cost_sensitivity"]["breakpoint_scale_where_oos_edge_dies"],
    )
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    h = summary["headline"]
    gate = summary["funding_carry_gate"]
    sweep = summary["cost_sensitivity_sweep"]
    tail = summary["tail_stress"]
    rt = summary["design"]["round_trip_cost_bps_at_2500_notional"]
    lines = [
        "# FUND-EV2 — Funding Carry Under Realistic, Cited Costs",
        "",
        "Research/evidence only. No runtime, strategy-rule, order, testnet, live,",
        "or production-approval change follows from this report. Costs are cited",
        "(fee schedules + one-shot public l2Book calibration), never tuned to the",
        "verdict; the sensitivity sweep makes the cost dependence auditable.",
        "Account basis: 10,000 USDC.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        f"Gate reasons: `{gate['reason_codes']}`",
        f"Qualifiers: `{gate['qualifiers']}`",
        f"**Cost breakpoint: OOS edge dies at scale {sweep['breakpoint_scale_where_oos_edge_dies']}** (1.0 = cited realistic level)",
        "",
        "## The honest question",
        "",
        "FUND-EV1 killed the carry with a deliberately conservative cost model",
        "(HL spot at the widest tier). Was that our conservatism, or is there no",
        "capturable edge? Same bar, cited costs, selective entries, longer holds.",
        "",
        "## Cited cost basis",
        "",
    ]
    for source in summary["discipline_guard"]["sources"]:
        lines.append(f"- {source}")
    lines += [
        "",
        "## Round-trip cost (both legs, entry+exit, bps at 2.5k notional)",
        "",
        "| Asset | hl_single | cross_venue |",
        "| --- | --- | --- |",
    ]
    for s in summary["universe"]["carry_universe"]:
        lines.append(f"| {s} | {rt['hl_single'][s]} | {rt['cross_venue'][s]} |")
    lines += [
        "",
        "(cross_venue: Kraken retail taker fee 40 bps/side + transfers dominates —",
        "the deeper book does not help at a 10k account; Coinbase base tier is worse)",
        "",
        "## Headline (chronological 70/30 OOS, cited realistic costs)",
        "",
        f"- Train-only choice: `{summary['train_only_choice']['chosen_config']}` (construction {summary['train_only_choice']['chosen_construction']})",
        f"- OOS net carry: **{h['oos_net_carry']}** USDC; OOS Sharpe {h['strategy_oos'].get('sharpe_annual')}, max DD {h['strategy_oos'].get('max_drawdown_pct')}%, days {h['strategy_oos'].get('days')}",
        f"- Train: {h['strategy_train'].get('total_return_pct')}% (Sharpe {h['strategy_train'].get('sharpe_annual')})",
        f"- Full net {h['full_net_pnl']} vs zero-cost {h['gross_carry_zero_cost_net']} — costs ate {h['costs_total_vs_zero_cost']} ({h['cost_share_of_gross_pct']}% of gross)",
        f"- Same config under FUND-EV1's conservative model: net {h['fund_ev1_cost_reference_same_config']['net_pnl']}, OOS {h['fund_ev1_cost_reference_same_config']['oos_net_pnl']}",
        "",
        "## Cost-sensitivity sweep (the discipline guard)",
        "",
        "| Cost scale | OOS net | Full net | Trades |",
        "| --- | --- | --- | --- |",
    ]
    for row in sweep["rows"]:
        lines.append(
            f"| {row['scale']} | {row['oos_net_pnl']} | {row['full_net_pnl']} | {row['trade_count']} |"
        )
    lines += [
        "",
        f"- {sweep['semantics']}",
        "",
        "## Walk-forward + regimes + leave-one-out",
        "",
        f"- Fold B (`{summary['walk_forward']['fold_b']['chosen_config']}`): net {summary['walk_forward']['fold_b']['net_carry']}",
        f"- Fold C (`{summary['walk_forward']['fold_c']['chosen_config']}`): net {summary['walk_forward']['fold_c']['net_carry']}",
    ]
    for label, row in summary["regimes"]["chosen_config_pnl_by_regime"].items():
        lines.append(f"- regime {label}: {row['days']} days, net {row['net_pnl']}")
    lines += [
        f"- Gate non-bull net: {gate['non_bull_net_pnl']}",
        "",
        "| Dropped | OOS net carry | OOS Sharpe |",
        "| --- | --- | --- |",
    ]
    for symbol, row in summary["leave_one_out"].items():
        lines.append(f"| {symbol} | {row['oos_net_carry']} | {row['oos_sharpe']} |")
    sc = tail["stressed_run_chosen"]
    so = tail["stressed_run_other_construction"]
    lines += [
        "",
        "## Tail / legged execution (per construction)",
        "",
        (
            f"- Chosen ({sc['construction']}): stressed (cost x{sc['cost_scale']}, spot leg lag 1) net {sc['net_pnl']}, "
            f"max DD {sc['max_drawdown_pct']}% (limit {gate['max_stressed_drawdown_pct_limit']}%), "
            f"max one-leg exposure {sc['max_residual_delta_fraction']} of equity -> modeled gap loss "
            f"{sc['modeled_gap_loss_at_max_residual_pct_of_equity']}% at the window's worst candle ({tail['worst_single_candle_move_pct_in_window']}%)"
        ),
        (
            f"- Other ({so['construction']}): stressed net {so['net_pnl']}, max DD {so['max_drawdown_pct']}%, "
            f"max one-leg exposure {so['max_residual_delta_fraction']}"
        ),
        f"- {tail['legging_resolution_note']}",
        "",
        "## Boundaries",
        "",
        "Research/evidence only; public read-only data; no order, testnet, live,",
        "production, or approval surface. Costs cited, never tuned to the verdict;",
        "l2Book calibration is point-in-time (sweep covers the uncertainty); spot",
        "borrow + liquidation mechanics unmodeled. The verdict is the gate's",
        "output and was not forced positive.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
