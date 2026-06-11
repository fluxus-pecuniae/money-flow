#!/usr/bin/env python3
"""Build FUND-SCALE1 scale & fee-tier viability evidence.

FUND-SCALE1 is research/evidence only. It maps the one axis FUND-EV2
sanctioned as new evidence: account size x cited fee tier. For each venue
construction it train-chooses a config per published fee tier (FUND-EV2's
bounded grid, train split only), then sweeps account sizes
10k/50k/250k/1M/5M, modeling BOTH effects of size honestly: published-tier
fees + amortizing fixed costs (helps) and EXEC-EV1 square-root impact driven
by the actual traded notional (hurts). Tier achievement is derived from the
strategy's OWN traded volume (HL 14d weighted, spot double; Kraken 30d) —
cells priced at tiers the strategy's flow cannot reach are marked assumed,
answer "what would it take", and can never form the viable band. Cells
whose fills exceed 10% of a candle's dollar volume are impact-implausible
and cannot pass. The 10k @ base-tier cell reproduces FUND-EV2's retail
verdict; it is not re-litigated.

No network I/O, no runtime mutation, no orders, no private/signed/testnet/
live endpoints. Deterministic.

Run locally:
    .venv/bin/python scripts/run_fund_scale1_evidence.py
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


scale1 = _load_module("services/strategy_validation/fund_scale1.py", "fund_scale1_runner_module")
ev2 = scale1.fund_ev2
fund = scale1.fund_ev1

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "FUND-SCALE1"
REPORT_NAME = "fund_scale1_size_fee_tier_viability"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_FUNDING_SNAPSHOT_INPUT = Path("docs/fund_ev1_funding_data_snapshot_summary.json")
DEFAULT_SPOT_RAW_DIR = Path("/tmp/money-flow-fund-ev1/raw_spot_candles")
DEFAULT_SUMMARY_OUTPUT = Path("docs/fund_scale1_size_fee_tier_viability_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/fund_scale1_size_fee_tier_viability.md")
SCENARIO = scenario_by_id("exec_ev1_conservative")  # unused on cited-cost path
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")
STRESS_COST_SCALE = Decimal("2.0")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--funding-snapshot", type=Path, default=DEFAULT_FUNDING_SNAPSHOT_INPUT)
    parser.add_argument("--spot-raw-dir", type=Path, default=DEFAULT_SPOT_RAW_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def _s(value: Any) -> Any:
    return str(value) if isinstance(value, Decimal) else value


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: _s(v) for k, v in stats.items()}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    runner_v1 = _load_module("scripts/run_fund_ev1_evidence.py", "fund_ev1_runner_for_scale1")
    _, snapshot, universe = runner_v1.load_universe(
        args.sv22_summary, args.funding_snapshot, args.spot_raw_dir
    )
    split = fund.timeline_split_time(universe, CHRONOLOGICAL_TRAIN_RATIO)
    timeline = universe.timeline
    window_days = len(timeline)
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]
    configs = ev2.generate_fund_ev2_configs()
    config_by_id = {c.config_id: c for c in configs}

    sim_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    def simulate(config, cost_model, size: Decimal, label: str):
        key = (label, config.config_id, str(size))
        if key not in sim_cache:
            sim_cache[key] = fund.simulate_funding_carry_portfolio(
                universe, config, SCENARIO, leg_cost_model=cost_model,
                starting_equity=size,
            )
        return sim_cache[key]

    # Tier ladders per construction: (label, tier object, cost model).
    ladders: dict[str, list[tuple[str, Any, Any]]] = {
        ev2.CONSTRUCTION_HL_SINGLE: [
            (tier.tier_id, tier, scale1.hl_tier_cost_model(tier))
            for tier in scale1.HL_SWEEP_TIERS
        ],
        ev2.CONSTRUCTION_CROSS_VENUE: [
            (tier.tier_id, tier, scale1.cross_venue_tier_cost_model(tier))
            for tier in scale1.KRAKEN_SWEEP_TIERS
        ],
    }

    base_size = scale1.ACCOUNT_SIZES_USDC[0]
    chosen_by_rung: dict[tuple[str, str], str] = {}
    grid_by_rung: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    # --- train-only choice per (construction, tier rung) at the base size ---
    for construction, ladder in ladders.items():
        grid_configs = [c for c in configs if c.venue_construction == construction]
        for tier_id, _tier, model in ladder:
            grid: dict[str, dict[str, Any]] = {}
            for config in grid_configs:
                grid[config.config_id] = simulate(config, model, base_size, tier_id)
            grid_by_rung[(construction, tier_id)] = grid
            chosen_by_rung[(construction, tier_id)] = fund.select_best_config_id(
                grid, train_up_to=split
            )

    # --- the size x tier map -------------------------------------------------
    def tier_qualifying_volume(construction: str, tier: Any) -> Decimal:
        if construction == ev2.CONSTRUCTION_HL_SINGLE:
            return tier.qualifying_weighted_14d_volume_usd
        return tier.qualifying_30d_volume_usd

    def own_volume_for(construction: str, result: dict[str, Any]) -> Decimal:
        if construction == ev2.CONSTRUCTION_HL_SINGLE:
            return scale1.hl_weighted_14d_volume(result, window_days)
        return scale1.kraken_30d_volume(result, window_days)

    cells: list[dict[str, Any]] = []
    for construction, ladder in ladders.items():
        for tier_id, tier, model in ladder:
            chosen_id = chosen_by_rung[(construction, tier_id)]
            chosen_config = config_by_id[chosen_id]
            for size in scale1.ACCOUNT_SIZES_USDC:
                result = simulate(chosen_config, model, size, tier_id)
                oos_net = fund.window_net_pnl(result["equity_curve"], after=split)
                own_volume = own_volume_for(construction, result)
                qualifying = tier_qualifying_volume(construction, tier)
                cells.append(
                    {
                        "construction": construction,
                        "tier_id": tier_id,
                        "account_size": str(size),
                        "chosen_config": chosen_id,
                        "oos_net_pnl": _s(oos_net),
                        "oos_net_pct_of_equity": _s(
                            fund._money(oos_net / size * Decimal("100"))
                            if oos_net is not None
                            else None
                        ),
                        "full_net_pnl": _s(result["net_pnl"]),
                        "funding_collected_total": _s(result["funding_collected_total"]),
                        "trade_count": result["trade_count"],
                        "max_fill_notional": _s(result["max_fill_notional"]),
                        "max_fill_participation": _s(result["max_fill_participation"]),
                        "impact_plausible": result["max_fill_participation"]
                        <= scale1.PARTICIPATION_PLAUSIBILITY_MAX,
                        "own_volume_for_tier": _s(own_volume),
                        "tier_qualifying_volume": _s(qualifying),
                        "tier_achieved_by_own_volume": own_volume >= qualifying,
                        "gate_passed": None,  # filled for gated cells below
                        "gate": None,
                    }
                )

    # --- gate battery: achieved-tier cells + every OOS-positive plausible
    # cell (candidates for the band / the "what would it take" surface) -----
    def cell_key(cell):
        return (cell["construction"], cell["tier_id"], cell["account_size"])

    def needs_gate(cell) -> bool:
        if cell["tier_achieved_by_own_volume"]:
            return True
        oos = cell["oos_net_pnl"]
        return (
            oos is not None
            and Decimal(str(oos)) > 0
            and cell["impact_plausible"]
        )

    model_by_rung = {
        (construction, tier_id): model
        for construction, ladder in ladders.items()
        for tier_id, _t, model in ladder
    }

    regimes = fund.classify_regimes(universe)
    for cell in cells:
        if not needs_gate(cell):
            continue
        construction, tier_id = cell["construction"], cell["tier_id"]
        size = Decimal(cell["account_size"])
        model = model_by_rung[(construction, tier_id)]
        chosen_config = config_by_id[cell["chosen_config"]]
        result = simulate(chosen_config, model, size, tier_id)
        oos_stats = fund.curve_stats(result["equity_curve"], after=split)
        oos_net = fund.window_net_pnl(result["equity_curve"], after=split)
        # Walk-forward: per-fold train-only choice on this rung's base-size
        # grid (fee bps are size-invariant; impact is second-order for the
        # choice), folds evaluated at THIS cell's size.
        grid = grid_by_rung[(construction, tier_id)]
        fold_nets = []
        for fold_train_up_to, fold_after, fold_up_to in (
            (t1, t1, t2),
            (t2, t2, None),
        ):
            fold_choice = fund.select_best_config_id(grid, train_up_to=fold_train_up_to)
            fold_result = simulate(config_by_id[fold_choice], model, size, tier_id)
            fold_nets.append(
                fund.window_net_pnl(
                    fold_result["equity_curve"], after=fold_after, up_to=fold_up_to
                )
            )
        # Leave-one-out at this cell's size/tier.
        loo: dict[str, Decimal | None] = {}
        for drop in universe.symbols:
            sub_universe = fund.CarryUniverse(
                [universe.assets[s] for s in universe.symbols if s != drop]
            )
            sub_split = fund.timeline_split_time(sub_universe, CHRONOLOGICAL_TRAIN_RATIO)
            sub_result = fund.simulate_funding_carry_portfolio(
                sub_universe, chosen_config, SCENARIO,
                leg_cost_model=model, starting_equity=size,
            )
            loo[drop] = fund.window_net_pnl(sub_result["equity_curve"], after=sub_split)
        # Legged-execution tail stress at this size (cost x2 + spot lag 1).
        stressed_result = fund.simulate_funding_carry_portfolio(
            universe,
            replace(chosen_config, config_id=f"{chosen_config.config_id}_s1stress",
                    spot_leg_lag_days=1),
            SCENARIO,
            leg_cost_model=model.with_scale(STRESS_COST_SCALE),
            starting_equity=size,
        )
        stressed_stats = fund.curve_stats(stressed_result["equity_curve"])
        regime_pnls = fund.pnl_by_regime(result["equity_curve"], regimes)
        gate = fund.evaluate_funding_carry_gate(
            strategy_type=chosen_config.strategy_type,
            oos_strategy_stats=oos_stats,
            oos_net_pnl=oos_net,
            walk_forward_net_pnls=fold_nets,
            regime_pnls=regime_pnls,
            leave_one_out_oos_net=loo,
            stressed_max_drawdown_pct=stressed_stats["max_drawdown_pct"],
        )
        stress_plausible = (
            stressed_result["max_fill_participation"]
            <= scale1.PARTICIPATION_PLAUSIBILITY_MAX
        )
        cell["impact_plausible"] = bool(cell["impact_plausible"] and stress_plausible)
        cell["gate_passed"] = bool(gate["passed"])
        cell["gate"] = {
            "status": gate["status"],
            "reason_codes": gate["reason_codes"],
            "oos_sharpe": _s(oos_stats["sharpe_annual"]),
            "oos_max_drawdown_pct": _s(oos_stats["max_drawdown_pct"]),
            "walk_forward_net_pnls": [_s(n) for n in fold_nets],
            "leave_one_out_oos_net": {k: _s(v) for k, v in sorted(loo.items())},
            "regime_pnls": {
                label: {"days": row["days"], "net_pnl": _s(row["net_pnl"])}
                for label, row in regime_pnls.items()
            },
            "stressed_max_drawdown_pct": _s(stressed_stats["max_drawdown_pct"]),
            "stressed_max_fill_participation": _s(
                stressed_result["max_fill_participation"]
            ),
        }

    for cell in cells:
        if cell["gate_passed"] is None:
            cell["gate_passed"] = False
            cell["gate"] = {
                "status": "not_gated_negative_oos_or_implausible",
                "reason_codes": ["cell_not_a_band_candidate"],
            }

    verdict, band_cells = scale1.viability_band(cells)

    # --- maker-bound optimistic line (non-gateable) --------------------------
    maker_model = scale1.maker_bound_cost_model()
    maker_grid = {
        c.config_id: simulate(c, maker_model, base_size, "maker_bound")
        for c in configs
        if c.venue_construction == ev2.CONSTRUCTION_HL_SINGLE
    }
    maker_chosen = fund.select_best_config_id(maker_grid, train_up_to=split)
    maker_line = []
    for size in scale1.ACCOUNT_SIZES_USDC:
        r = simulate(config_by_id[maker_chosen], maker_model, size, "maker_bound")
        maker_oos = fund.window_net_pnl(r["equity_curve"], after=split)
        maker_line.append(
            {
                "account_size": str(size),
                "oos_net_pnl": _s(maker_oos),
                "oos_net_pct_of_equity": _s(
                    fund._money(maker_oos / size * Decimal("100"))
                    if maker_oos is not None
                    else None
                ),
                "max_fill_participation": _s(r["max_fill_participation"]),
            }
        )

    # --- fee/size breakpoints along the two axes ------------------------------
    def first_positive_tier(construction: str, size: Decimal) -> str | None:
        for tier_id, _t, _m in ladders[construction]:
            cell = next(
                c for c in cells
                if cell_key(c) == (construction, tier_id, str(size))
            )
            if cell["oos_net_pnl"] is not None and Decimal(str(cell["oos_net_pnl"])) > 0:
                return tier_id
        return None

    breakpoints = {
        construction: {
            str(size): first_positive_tier(construction, size)
            for size in scale1.ACCOUNT_SIZES_USDC
        }
        for construction in ladders
    }

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "funding_carry_scale_viability_complete",
        "verdict": verdict,
        "discipline_guard": {
            "fee_tiers_published_and_cited": True,
            "sources": [
                "Hyperliquid docs fee tiers (fetched 2026-06-11): perp T0-T6 taker 4.5/4.0/3.5/3.0/2.8/2.6/2.4 bps, spot T0-T6 taker 7.0/6.0/5.0/4.0/3.5/3.0/2.5 bps; 14d weighted volume, spot counted double; maker-volume-share rebates (-0.1/-0.2/-0.3 bps) require market-maker flow, not modeled",
                "Kraken Pro fee schedule (fetched 2026-06-11): spot taker 40/35/24/22/20/18/16/14/12/10/8/5 bps at 30d volume 0/10k/50k/100k/250k/500k/1M/2.5M/5M/10M/100M/500M",
                "Spreads/impact/slippage/settlement: the FUND-EV2 cited model (l2Book calibration + flat 2 USDC cross-venue settlement, amortizing with size)",
            ],
            "tier_achievement_from_own_volume": (
                "a tier counts as achieved only if the strategy's own traded volume "
                "at that size reaches the published qualifying volume (HL 14d "
                "weighted, spot double; Kraken 30d)"
            ),
            "impact_plausibility_threshold_participation": str(
                scale1.PARTICIPATION_PLAUSIBILITY_MAX
            ),
            "retail_verdict_not_relitigated": (
                "the 10k @ base-tier cell reproduces FUND-EV2's fail; FUND-SCALE1 "
                "adds the size/fee axis only"
            ),
        },
        "account_sizes_usdc": [str(s) for s in scale1.ACCOUNT_SIZES_USDC],
        "tier_ladders": {
            ev2.CONSTRUCTION_HL_SINGLE: [
                {
                    "tier_id": t.tier_id,
                    "qualifying_weighted_14d_volume_usd": str(t.qualifying_weighted_14d_volume_usd),
                    "perp_taker_bps": str(t.perp_taker_bps),
                    "spot_taker_bps": str(t.spot_taker_bps),
                    "basis": t.basis,
                }
                for t in scale1.HL_SWEEP_TIERS
            ],
            ev2.CONSTRUCTION_CROSS_VENUE: [
                {
                    "tier_id": t.tier_id,
                    "qualifying_30d_volume_usd": str(t.qualifying_30d_volume_usd),
                    "spot_taker_bps": str(t.taker_bps),
                    "basis": t.basis,
                }
                for t in scale1.KRAKEN_SWEEP_TIERS
            ],
        },
        "chosen_config_by_rung": {
            f"{construction}:{tier_id}": chosen_by_rung[(construction, tier_id)]
            for construction, ladder in ladders.items()
            for tier_id, _t, _m in ladder
        },
        "chronological_split": {
            "train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO),
            "split_time": str(split),
        },
        "viability_map": cells,
        "fee_axis_breakpoints_first_positive_tier_by_size": breakpoints,
        "band_cells": band_cells,
        "maker_bound_line_optimistic_non_gateable": {
            "chosen_config": maker_chosen,
            "line": maker_line,
            "note": (
                "all fills passive at HL base maker fees with zero half-spread "
                "paid; non-fill/chase risk NOT modeled - informs, never passes"
            ),
        },
        "universe": {
            "carry_universe": list(fund.CARRY_UNIVERSE),
            "aligned_days": window_days,
            "window": [str(timeline[0]), str(timeline[-1])],
        },
        "data_provenance": {
            "inputs": "FUND-EV1 funding snapshot + SV2.2 perp candles + FUND-EV1 spot candles + FUND-EV2 l2Book calibration",
            "funding_snapshot_fetched_at": snapshot.get("fetched_at_utc"),
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        },
        "boundaries": {k: v for k, v in scale1.boundary_flags().items()},
    }

    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"verdict: {verdict}")
    print(f"sim count: {len(sim_cache)}")
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# FUND-SCALE1 — Funding Carry: Scale & Fee-Tier Viability",
        "",
        "Research/evidence only. No runtime, strategy-rule, order, testnet, live,",
        "or production-approval change. Fee tiers are the published schedules",
        "(cited); tier achievement is derived from the strategy's OWN volume;",
        "impact scales with the actual traded notional; implausible-participation",
        "cells cannot pass. The 10k retail verdict (FUND-EV2) is not re-litigated.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        "## Cited fee schedules",
        "",
    ]
    for source in summary["discipline_guard"]["sources"]:
        lines.append(f"- {source}")
    lines += [
        "",
        f"- Tier achievement rule: {summary['discipline_guard']['tier_achievement_from_own_volume']}",
        f"- Impact plausibility: max single-fill participation <= {summary['discipline_guard']['impact_plausibility_threshold_participation']} of candle $ volume",
        "",
        "## Viability map (OOS net carry, USDC; * = tier NOT achieved by own volume; ! = impact implausible)",
        "",
    ]
    sizes = summary["account_sizes_usdc"]
    for construction in ("hl_single", "cross_venue"):
        ladder = [t["tier_id"] for t in summary["tier_ladders"][construction]]
        lines.append(f"### {construction}")
        lines.append("")
        lines.append("| Tier \\ Size | " + " | ".join(f"{Decimal(s):,.0f}" for s in sizes) + " |")
        lines.append("| --- |" + " --- |" * len(sizes))
        for tier_id in ladder:
            row = [tier_id]
            for size in sizes:
                cell = next(
                    c for c in summary["viability_map"]
                    if c["construction"] == construction
                    and c["tier_id"] == tier_id
                    and c["account_size"] == size
                )
                marker = "" if cell["tier_achieved_by_own_volume"] else "*"
                marker += "" if cell["impact_plausible"] else "!"
                gate_mark = " PASS" if cell["gate_passed"] else ""
                row.append(f"{Decimal(cell['oos_net_pnl']):,.0f}{marker}{gate_mark}")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    lines += [
        "## Fee-axis breakpoint (first tier with positive OOS net, per size)",
        "",
    ]
    for construction, by_size in summary["fee_axis_breakpoints_first_positive_tier_by_size"].items():
        lines.append(f"- {construction}: " + ", ".join(
            f"{Decimal(size):,.0f}: {tier or 'none'}" for size, tier in by_size.items()
        ))
    mb = summary["maker_bound_line_optimistic_non_gateable"]
    lines += [
        "",
        "## Maker-bound line (OPTIMISTIC, non-gateable)",
        "",
        f"- {mb['note']}",
        "| Size | OOS net | OOS % of equity |",
        "| --- | --- | --- |",
    ]
    for row in mb["line"]:
        lines.append(
            f"| {Decimal(row['account_size']):,.0f} | {Decimal(row['oos_net_pnl']):,.1f} | {row['oos_net_pct_of_equity']}% |"
        )
    lines += [
        "",
        "## Boundaries",
        "",
        "Research/evidence only; public read-only data; published fee schedules",
        "cited; tier achievement derived from own volume; maker-bound line is an",
        "optimistic non-gateable bound; spot borrow/liquidation unmodeled. The",
        "verdict is computed from the gated cells and was not forced positive.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
