#!/usr/bin/env python3
"""Build EXEC-EV1 depth-aware execution-quality evidence from SV2.2 candles.

EXEC-EV1 is research/evidence only. It re-scores the three founder-selected
Week 2 lanes under a depth-aware modeled friction layer (spread + size-aware
square-root market impact + fill-probability), on top of SV2.3's fee/slippage/
adverse-gap terms, and reports the delta vs the matching SV2.3 row.

MODELED, NOT REAL, DEPTH: the liquidity inputs are derived from historical
candle volume, not real historical order-book depth (which does not exist —
Hyperliquid public l2Book is a current snapshot only). Every output is an
assumption layer, never observed execution. No runtime mutation, no orders, no
private/signed/testnet/live endpoints, no production or live approval.

Like SV2.3 this reads SV2.2 raw candle artifacts from disk and performs no
network I/O. Run locally:
    .venv/bin/python scripts/run_exec_ev1_execution_quality.py
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.run_sv22_hyperliquid_research_refresh import (
    ACTIVE_TIMEFRAMES,
    DISABLED_TIMEFRAMES,
    FOUNDER_APPROVED_RESOLVED_SYMBOLS,
    INITIAL_EQUITY,
    NO_ORDER_FLAGS,
    WEEK2_REPLAY_STRATEGY_IDS,
    baseline_entry_reason,
    baseline_exit_reason,
    dec,
    fmt_decimal,
    indicators,
    iso_utc,
    mf_orig_entry_reason,
    mf_orig_exit_reason,
    money,
    prior_low,
    ratio,
    safe_segment,
    strategy_label,
    timeframe_settings,
    write_json,
)
from scripts.run_sv23_realistic_backtest import (
    EXECUTION_SCENARIOS as SV23_SCENARIOS,
)
from scripts.run_sv23_realistic_backtest import (
    SCENARIO_TRADE_COUNT_GATE,
    adverse_gap_bps,
    load_sv22_datasets,
    next_open_fill_candle,
    replay_realistic_strategy,
    scenario_gate,
    stage_rows_for,
)
from services.execution_quality.exec_ev1 import (
    DEPTH_AWARE_SCENARIOS,
    DepthAwareScenario,
    candle_dollar_volume,
    depth_aware_execution_price,
    entry_timing_cost_bps,
    fill_friction_bps,
    symbol_tier,
)

PHASE = "EXEC-EV1"
REPORT_NAME = "exec_ev1_execution_quality_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_SUMMARY_OUTPUT = Path("docs/exec_ev1_execution_quality_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/exec_ev1_execution_quality_evidence.md")
PRIMARY_FILL_ASSUMPTION = "next_candle_open"
LATE_ENTRY_LATENESS_STEPS = (0, 1, 2)

_SV23_BY_ID = {scenario.scenario_id: scenario for scenario in SV23_SCENARIOS}


@dataclass(frozen=True, slots=True)
class ExecEv1Result:
    strategy_id: str
    strategy_label: str
    symbol: str
    symbol_tier: str
    timeframe: str
    execution_scenario: str
    sv23_parent_scenario: str
    net_pnl: str
    sv23_net_pnl: str
    net_pnl_delta_vs_sv23: str
    max_drawdown: str
    max_drawdown_pct: str
    trade_count: int
    win_rate: str | None
    profit_factor: str | None
    avg_friction_bps: str
    avg_impact_bps: str
    avg_spread_bps: str
    avg_chase_bps: str
    entry_timing_cost_bps_by_lateness: dict[str, str | None]
    gate_status: str
    reason_codes: tuple[str, ...]
    survives_size_aware_friction: bool
    research_only: bool
    production_approved: bool
    live_trading_approved: bool
    modeled_depth_not_real: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def _avg(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def replay_exec_ev1_strategy(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    scenario: DepthAwareScenario,
    indicator_rows: list[dict[str, Any]],
    stages: list[str],
) -> dict[str, Any]:
    """Replay one lane with the EXEC-EV1 depth-aware friction layer.

    Mirrors SV2.3's signal/exit logic exactly; the only difference is the fill
    price, which is adjusted by the depth-aware friction (spread + size-aware
    impact + fill-prob) instead of SV2.3's flat slippage. Captures per-fill
    friction breakdowns and late-entry costs.
    """
    open_position: dict[str, Any] | None = None
    equity = INITIAL_EQUITY
    mtm_equity_points: list[Decimal] = [equity]
    trades: list[dict[str, Any]] = []
    friction_total: list[Decimal] = []
    impact_total: list[Decimal] = []
    spread_total: list[Decimal] = []
    chase_total: list[Decimal] = []
    late_entry_costs: dict[int, list[Decimal]] = {step: [] for step in LATE_ENTRY_LATENESS_STEPS}

    for index, candle in enumerate(candles):
        indicator = indicator_rows[index]
        if index + 1 < int(timeframe_settings(timeframe)["min_history_bars"]):
            continue

        if open_position is not None:
            mtm = equity + (dec(candle["low"]) - dec(open_position["entry_price"])) * dec(
                open_position["quantity"]
            )
            mtm_equity_points.append(mtm)
            if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
                exit_reason = mf_orig_exit_reason(
                    candles, indicator_rows, index, dec(open_position["stop_price"])
                )
            else:
                exit_reason = baseline_exit_reason(indicator, candle, timeframe)
            if exit_reason is None:
                continue
            fill = next_open_fill_candle(candles, index)
            if fill is None:
                continue
            gap_bps = adverse_gap_bps(candle, fill, "sell")
            raw_exit = dec(fill["open"])
            if exit_reason == "structure_stop_hit":
                raw_exit = min(dec(open_position["stop_price"]), raw_exit)
            quantity = dec(open_position["quantity"])
            exit_notional_raw = money(raw_exit * quantity)
            friction = fill_friction_bps(
                scenario=scenario,
                symbol=symbol,
                notional=exit_notional_raw,
                liquidity_proxy=candle_dollar_volume(fill),
                adverse_gap=gap_bps,
            )
            friction_total.append(friction.total_bps)
            impact_total.append(friction.impact_bps)
            spread_total.append(friction.spread_bps)
            chase_total.append(friction.chase_bps)
            exit_price = depth_aware_execution_price(
                raw_price=raw_exit, side="sell", friction_total_bps=friction.total_bps
            )
            gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
            exit_notional = money(exit_price * quantity)
            exit_fee = money(exit_notional * (scenario.fee_bps / Decimal("10000")))
            net_pnl = money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
            equity_before = equity
            equity = money(equity + gross_pnl - exit_fee)
            trades.append(
                {
                    "trade_id": (
                        f"execev1-{safe_segment(scenario.scenario_id)}-{safe_segment(strategy_id)}-"
                        f"{safe_segment(symbol)}-{timeframe}-{len(trades) + 1}"
                    ),
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "execution_scenario": scenario.scenario_id,
                    "entry_price": open_position["entry_price"],
                    "exit_price": fmt_decimal(exit_price),
                    "quantity": open_position["quantity"],
                    "net_pnl": fmt_decimal(net_pnl),
                    "gross_pnl": fmt_decimal(gross_pnl),
                    "exit_friction_bps": fmt_decimal(friction.total_bps),
                    "exit_impact_bps": fmt_decimal(friction.impact_bps),
                    "exit_spread_bps": fmt_decimal(friction.spread_bps),
                    "exit_chase_bps": fmt_decimal(friction.chase_bps),
                    "equity_before_trade": fmt_decimal(equity_before),
                    "equity_after_trade": fmt_decimal(equity),
                    "exit_reason": exit_reason,
                    "source": "exec_ev1_execution_quality",
                    "historical_replay_not_live": True,
                    "modeled_depth_not_real": True,
                }
            )
            mtm_equity_points.append(equity)
            open_position = None
            continue

        if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
            entry_allowed, _entry_reasons = mf_orig_entry_reason(
                candles, indicator_rows, stages, index
            )
        else:
            reason = baseline_entry_reason(indicator, candle, timeframe)
            entry_allowed = reason is None
            if entry_allowed and strategy_id == "avoid_low_rolling_range_20":
                rolling_range = indicator.get("rolling_range_20")
                if rolling_range is not None and float(rolling_range) <= 0.025:
                    entry_allowed = False
        if not entry_allowed:
            continue

        fill = next_open_fill_candle(candles, index)
        if fill is None:
            continue

        # Late-entry / entry-timing cost measurement (Must 3): record the adverse
        # move from the signal candle to progressively later fills.
        for step in LATE_ENTRY_LATENESS_STEPS:
            cost = entry_timing_cost_bps(candles, index, step, "buy")
            if cost is not None:
                late_entry_costs[step].append(cost)

        gap_bps = adverse_gap_bps(candle, fill, "buy")
        notional = equity
        raw_entry = dec(fill["open"])
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=notional,
            liquidity_proxy=candle_dollar_volume(fill),
            adverse_gap=gap_bps,
        )
        friction_total.append(friction.total_bps)
        impact_total.append(friction.impact_bps)
        spread_total.append(friction.spread_bps)
        chase_total.append(friction.chase_bps)
        entry_price = depth_aware_execution_price(
            raw_price=raw_entry, side="buy", friction_total_bps=friction.total_bps
        )
        quantity = notional / entry_price if entry_price > 0 else Decimal("0")
        if quantity <= 0:
            continue
        entry_fee = money(notional * (scenario.fee_bps / Decimal("10000")))
        equity = money(equity - entry_fee)
        stop_price = prior_low(candles, index, 10) or dec(candle["low"])
        open_position = {
            "entry_time": fill["open_time"],
            "entry_price": fmt_decimal(entry_price),
            "quantity": fmt_decimal(quantity),
            "entry_fee": fmt_decimal(entry_fee),
            "stop_price": fmt_decimal(stop_price),
        }
        mtm_equity_points.append(equity)

    if open_position is not None and candles:
        last = candles[-1]
        quantity = dec(open_position["quantity"])
        raw_exit = dec(last["close"])
        friction = fill_friction_bps(
            scenario=scenario,
            symbol=symbol,
            notional=money(raw_exit * quantity),
            liquidity_proxy=candle_dollar_volume(last),
            adverse_gap=Decimal("0"),
        )
        friction_total.append(friction.total_bps)
        impact_total.append(friction.impact_bps)
        spread_total.append(friction.spread_bps)
        chase_total.append(friction.chase_bps)
        exit_price = depth_aware_execution_price(
            raw_price=raw_exit, side="sell", friction_total_bps=friction.total_bps
        )
        gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
        exit_fee = money(money(exit_price * quantity) * (scenario.fee_bps / Decimal("10000")))
        equity_before = equity
        equity = money(equity + gross_pnl - exit_fee)
        trades.append(
            {
                "trade_id": (
                    f"execev1-{safe_segment(scenario.scenario_id)}-{safe_segment(strategy_id)}-"
                    f"{safe_segment(symbol)}-{timeframe}-{len(trades) + 1}"
                ),
                "strategy_id": strategy_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "execution_scenario": scenario.scenario_id,
                "entry_price": open_position["entry_price"],
                "exit_price": fmt_decimal(exit_price),
                "quantity": open_position["quantity"],
                "net_pnl": fmt_decimal(
                    money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
                ),
                "gross_pnl": fmt_decimal(gross_pnl),
                "exit_friction_bps": fmt_decimal(friction.total_bps),
                "exit_impact_bps": fmt_decimal(friction.impact_bps),
                "exit_spread_bps": fmt_decimal(friction.spread_bps),
                "exit_chase_bps": fmt_decimal(friction.chase_bps),
                "equity_before_trade": fmt_decimal(equity_before),
                "equity_after_trade": fmt_decimal(equity),
                "exit_reason": "end_of_window_forced_close",
                "forced_exit": True,
                "source": "exec_ev1_execution_quality",
                "historical_replay_not_live": True,
                "modeled_depth_not_real": True,
            }
        )
        mtm_equity_points.append(equity)

    peak = INITIAL_EQUITY
    max_drawdown = Decimal("0")
    for point in mtm_equity_points:
        peak = max(peak, point)
        max_drawdown = max(max_drawdown, peak - point)
    wins = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) > 0]
    losses = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) < 0]
    gross_losses = abs(sum(losses, Decimal("0")))
    summary = {
        "net_pnl": fmt_decimal(equity - INITIAL_EQUITY),
        "max_drawdown": fmt_decimal(max_drawdown),
        "max_drawdown_pct": fmt_decimal(ratio(max_drawdown, INITIAL_EQUITY)),
        "trade_count": len(trades),
        "win_rate": fmt_decimal(ratio(Decimal(len(wins)), Decimal(len(trades))))
        if trades
        else None,
        "profit_factor": fmt_decimal(sum(wins, Decimal("0")) / gross_losses)
        if gross_losses > 0
        else None,
    }
    late_entry_avg = {
        str(step): (fmt_decimal(_avg(values)) if values else None)
        for step, values in late_entry_costs.items()
    }
    return {
        "summary": summary,
        "avg_friction_bps": fmt_decimal(_avg(friction_total)),
        "avg_impact_bps": fmt_decimal(_avg(impact_total)),
        "avg_spread_bps": fmt_decimal(_avg(spread_total)),
        "avg_chase_bps": fmt_decimal(_avg(chase_total)),
        "entry_timing_cost_bps_by_lateness": late_entry_avg,
        "trade_count": len(trades),
    }


def _result_row(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    scenario: DepthAwareScenario,
    exec_ev1: dict[str, Any],
    sv23_net_pnl: Decimal,
) -> ExecEv1Result:
    summary = exec_ev1["summary"]
    net_pnl = dec(summary["net_pnl"])
    gate_status, gate_reasons = scenario_gate(summary)
    survives = gate_status == "passes_realistic_scenario_gate"
    return ExecEv1Result(
        strategy_id=strategy_id,
        strategy_label=strategy_label(strategy_id),
        symbol=symbol,
        symbol_tier=symbol_tier(symbol),
        timeframe=timeframe,
        execution_scenario=scenario.scenario_id,
        sv23_parent_scenario=scenario.sv23_parent_scenario,
        net_pnl=fmt_decimal(net_pnl) or "0",
        sv23_net_pnl=fmt_decimal(sv23_net_pnl) or "0",
        net_pnl_delta_vs_sv23=fmt_decimal(net_pnl - sv23_net_pnl) or "0",
        max_drawdown=summary["max_drawdown"],
        max_drawdown_pct=summary["max_drawdown_pct"],
        trade_count=int(summary["trade_count"]),
        win_rate=summary["win_rate"],
        profit_factor=summary["profit_factor"],
        avg_friction_bps=exec_ev1["avg_friction_bps"] or "0",
        avg_impact_bps=exec_ev1["avg_impact_bps"] or "0",
        avg_spread_bps=exec_ev1["avg_spread_bps"] or "0",
        avg_chase_bps=exec_ev1["avg_chase_bps"] or "0",
        entry_timing_cost_bps_by_lateness=exec_ev1["entry_timing_cost_bps_by_lateness"],
        gate_status=gate_status,
        reason_codes=tuple(gate_reasons),
        survives_size_aware_friction=survives,
        research_only=True,
        production_approved=False,
        live_trading_approved=False,
        modeled_depth_not_real=True,
    )


def aggregate(results: Sequence[ExecEv1Result]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[ExecEv1Result]] = defaultdict(list)
    for row in results:
        buckets[(row.strategy_id, row.execution_scenario)].append(row)
    rows: list[dict[str, Any]] = []
    for (strategy_id, scenario_id), grouped in sorted(buckets.items()):
        net = sum((dec(r.net_pnl) for r in grouped), Decimal("0"))
        sv23_net = sum((dec(r.sv23_net_pnl) for r in grouped), Decimal("0"))
        trades = sum(r.trade_count for r in grouped)
        worst_dd = max((dec(r.max_drawdown) for r in grouped), default=Decimal("0"))
        avg_friction = _avg([dec(r.avg_friction_bps) for r in grouped])
        avg_impact = _avg([dec(r.avg_impact_bps) for r in grouped])
        late_by_step: dict[str, list[Decimal]] = defaultdict(list)
        for r in grouped:
            for step, value in r.entry_timing_cost_bps_by_lateness.items():
                if value is not None:
                    late_by_step[step].append(dec(value))
        survives = net > 0 and trades >= SCENARIO_TRADE_COUNT_GATE
        rows.append(
            {
                "strategy_id": strategy_id,
                "strategy_label": strategy_label(strategy_id),
                "execution_scenario": scenario_id,
                "sv23_parent_scenario": _depth_scenario(scenario_id).sv23_parent_scenario,
                "total_net_pnl": fmt_decimal(net),
                "sv23_total_net_pnl": fmt_decimal(sv23_net),
                "net_pnl_delta_vs_sv23": fmt_decimal(net - sv23_net),
                "total_trades": trades,
                "max_drawdown_worst": fmt_decimal(worst_dd),
                "avg_friction_bps": fmt_decimal(avg_friction),
                "avg_impact_bps": fmt_decimal(avg_impact),
                "entry_timing_cost_bps_by_lateness": {
                    step: fmt_decimal(_avg(values)) for step, values in sorted(late_by_step.items())
                },
                "verdict": "survives_size_aware_friction"
                if survives
                else "not_promoted_realistic_gate_failed",
            }
        )
    return rows


def _depth_scenario(scenario_id: str) -> DepthAwareScenario:
    for scenario in DEPTH_AWARE_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(scenario_id)


def build_summary(
    *,
    generated_at: datetime,
    run_timestamp: str,
    sv22_summary: dict[str, Any],
    results: Sequence[ExecEv1Result],
) -> dict[str, Any]:
    aggregates = aggregate(results)
    return {
        "phase": PHASE,
        "report": REPORT_NAME,
        "generated_at_utc": iso_utc(generated_at),
        "run_timestamp": run_timestamp,
        "status": "execution_quality_evidence_complete" if results else "execution_quality_blocked",
        "modeled_depth_disclaimer": (
            "Depth/liquidity is MODELED from historical candle volume, not real "
            "historical order-book depth (which does not exist; Hyperliquid public "
            "l2Book is a current snapshot only). Every cost is an assumption."
        ),
        "addresses_known_issue": (
            "K-001 partially (modeled, not real, depth-aware execution quality)"
        ),
        "source": {
            "input_summary": DEFAULT_SV22_SUMMARY_INPUT.as_posix(),
            "input_phase": sv22_summary.get("phase"),
            "strategy_truth": "public_hyperliquid_mainnet_candles_from_sv2_2_refresh",
            "network_fetch_performed": False,
            "real_order_book_depth_used": False,
        },
        "universe_policy": {
            "name": "founder_23_symbols",
            "symbols": list(FOUNDER_APPROVED_RESOLVED_SYMBOLS),
        },
        "timeframes": list(ACTIVE_TIMEFRAMES),
        "disabled_timeframes": list(DISABLED_TIMEFRAMES),
        "strategy_ids": list(WEEK2_REPLAY_STRATEGY_IDS),
        "primary_fill_assumption": PRIMARY_FILL_ASSUMPTION,
        "friction_model": {
            "components": [
                "fee_bps (kept from SV2.3)",
                "slippage_bps (kept from SV2.3)",
                "adverse_gap_penalty_bps (kept from SV2.3)",
                "spread_bps (NEW — per-symbol liquidity-tier half-spread)",
                "impact_bps (NEW — square-root participation-rate market impact)",
                "chase_bps (NEW — fill-probability unfilled-chase penalty)",
            ],
            "impact_law": "square_root_participation_rate",
            "liquidity_proxy": "candle base-asset volume * typical price ((H+L+C)/3)",
            "guarantee": (
                "EXEC-EV1 cost >= SV2.3 parent cost; EXEC-EV1 net PnL <= SV2.3 "
                "net PnL per lane/scenario"
            ),
        },
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "label": s.label,
                "sv23_parent_scenario": s.sv23_parent_scenario,
                "fee_bps": fmt_decimal(s.fee_bps),
                "slippage_bps": fmt_decimal(s.slippage_bps),
                "adverse_gap_penalty_bps": fmt_decimal(s.adverse_gap_penalty_bps),
                "spread_tier_multiplier": fmt_decimal(s.spread_tier_multiplier),
                "impact_coefficient_bps": fmt_decimal(s.impact_coefficient_bps),
                "fill_probability": fmt_decimal(s.fill_probability),
                "chase_penalty_bps": fmt_decimal(s.chase_penalty_bps),
                "description": s.description,
            }
            for s in DEPTH_AWARE_SCENARIOS
        ],
        "liquidity_tiers": {
            "major_perp_half_spread_bps": "1.0",
            "large_perp_half_spread_bps": "2.5",
            "mid_alt_perp_half_spread_bps": "5.0",
            "note": "Modeled typical perp half-spreads; assumption, not measured quotes.",
        },
        "late_entry_lateness_steps": list(LATE_ENTRY_LATENESS_STEPS),
        "result_count": len(results),
        "results": [asdict(row) for row in results],
        "aggregate_results": aggregates,
        "boundaries": NO_ORDER_FLAGS,
        "future_phase": {
            "name": "RT-HISTSEED1",
            "status": "position_live_in_historical",
            "summary": (
                "Startup historical-position reconstruction. Iron rules: separate "
                "bucket, never blended into forward synthetic PnL, never eligible "
                "for testnet/live transport."
            ),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    aggregates = summary.get("aggregate_results", [])
    late_rows = []
    for row in aggregates:
        late = row.get("entry_timing_cost_bps_by_lateness", {})
        late_rows.append(
            "| `{strategy_id}` | `{execution_scenario}` | `{l0}` | `{l1}` | `{l2}` |".format(
                strategy_id=row["strategy_id"],
                execution_scenario=row["execution_scenario"],
                l0=late.get("0", "n/a"),
                l1=late.get("1", "n/a"),
                l2=late.get("2", "n/a"),
            )
        )
    lines = [
        "# EXEC-EV1 Execution-Quality Evidence",
        "",
        "## Verdict",
        "",
        f"- Status: `{summary.get('status')}`",
        "- Purpose: re-score the three Week 2 lanes under a depth-aware modeled friction layer.",
        "- **Modeled depth, not real depth.** " + summary.get("modeled_depth_disclaimer", ""),
        f"- Known issue: {summary.get('addresses_known_issue')}",
        "- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.",
        "- Trading boundary: no orders, private/signed/order/testnet/live endpoints, or approvals.",
        "",
        "## Friction Model",
        "",
        f"- Impact law: `{summary['friction_model']['impact_law']}`",
        f"- Liquidity proxy: `{summary['friction_model']['liquidity_proxy']}`",
        f"- Guarantee: {summary['friction_model']['guarantee']}",
        "- Components: " + ", ".join(f"`{c}`" for c in summary["friction_model"]["components"]),
        "",
        "## Aggregate Results (EXEC-EV1 vs SV2.3)",
        "",
        "| Strategy | Scenario | EXEC-EV1 Net | SV2.3 Net | Delta | Trades | "
        "Avg Friction bps | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        *[
            (
                "| `{strategy_id}` | `{execution_scenario}` | `{total_net_pnl}` | "
                "`{sv23_total_net_pnl}` | `{net_pnl_delta_vs_sv23}` | `{total_trades}` | "
                "`{avg_friction_bps}` | `{verdict}` |"
            ).format(**row)
            for row in aggregates
        ],
        "",
        "## Late-Entry / Entry-Timing Cost (bps by lateness)",
        "",
        "Adverse move from the signal candle to fills 0/1/2 candles late. Informs the",
        "future RT-HISTSEED1 historical-position-seeding decision: small cost => seeding",
        "not worth the runtime risk; large cost => edge decays fast at the signal (a red flag).",
        "",
        "| Strategy | Scenario | +0 (next open) | +1 late | +2 late |",
        "| --- | --- | ---: | ---: | ---: |",
        *late_rows,
        "",
        "## Future Phase — RT-HISTSEED1",
        "",
        f"- Name: `{summary['future_phase']['name']}`",
        f"- Status: `{summary['future_phase']['status']}`",
        f"- {summary['future_phase']['summary']}",
        "",
        "## Boundaries",
        "",
        "- Public Hyperliquid mainnet candles from SV2.2 remain strategy truth.",
        "- Depth is modeled from candle volume, never real order-book depth.",
        "- No testnet/live strategy truth, no orders, no production or live approval.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    run_timestamp = args.run_timestamp or generated_at.strftime("%Y%m%dT%H%M%SZ")
    sv22_summary, datasets = load_sv22_datasets(args.sv22_summary)
    results: list[ExecEv1Result] = []
    for dataset in datasets:
        if dataset.get("timeframe") not in ACTIVE_TIMEFRAMES:
            continue
        raw = json.loads(Path(dataset["raw_path"]).read_text(encoding="utf-8"))
        candles = raw.get("candles") or []
        if not candles:
            continue
        indicator_rows = indicators(candles)
        stages = stage_rows_for(candles, indicator_rows)
        for strategy_id in WEEK2_REPLAY_STRATEGY_IDS:
            for scenario in DEPTH_AWARE_SCENARIOS:
                parent = _SV23_BY_ID[scenario.sv23_parent_scenario]
                sv23_replay = replay_realistic_strategy(
                    strategy_id=strategy_id,
                    symbol=dataset["symbol"],
                    timeframe=dataset["timeframe"],
                    candles=candles,
                    scenario=parent,
                    indicator_rows=indicator_rows,
                    stages=stages,
                )
                exec_ev1 = replay_exec_ev1_strategy(
                    strategy_id=strategy_id,
                    symbol=dataset["symbol"],
                    timeframe=dataset["timeframe"],
                    candles=candles,
                    scenario=scenario,
                    indicator_rows=indicator_rows,
                    stages=stages,
                )
                results.append(
                    _result_row(
                        strategy_id=strategy_id,
                        symbol=dataset["symbol"],
                        timeframe=dataset["timeframe"],
                        scenario=scenario,
                        exec_ev1=exec_ev1,
                        sv23_net_pnl=dec(sv23_replay["summary"]["net_pnl"]),
                    )
                )
    summary = build_summary(
        generated_at=generated_at,
        run_timestamp=run_timestamp,
        sv22_summary=sv22_summary,
        results=results,
    )
    write_json(args.summary_output, summary)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_report(summary), encoding="utf-8")
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"Status: {summary['status']}")
    print(f"Result rows: {summary['result_count']}")
    return 0 if results else 2


if __name__ == "__main__":
    raise SystemExit(main())
