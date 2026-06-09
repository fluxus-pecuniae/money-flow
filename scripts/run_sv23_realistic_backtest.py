#!/usr/bin/env python3
"""Build SV2.3 realistic backtest evidence from local SV2.2 public candles.

SV2.3 is research/evidence only. It reads the latest SV2.2 Hyperliquid
public-mainnet candle artifacts, applies next-candle-open realistic execution
scenarios, and never calls private, signed, testnet, live, or order endpoints.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from scripts.run_sv22_hyperliquid_research_refresh import (
    ACTIVE_TIMEFRAMES,
    DISABLED_TIMEFRAMES,
    FOUNDER_APPROVED_RESOLVED_SYMBOLS,
    INITIAL_EQUITY,
    NO_ORDER_FLAGS,
    WEEK2_REPLAY_STRATEGY_IDS,
    baseline_entry_reason,
    baseline_exit_reason,
    classify_stage,
    dec,
    fmt_decimal,
    indicators,
    iso_utc,
    markers_for_replay_trades,
    mf_orig_entry_reason,
    mf_orig_exit_reason,
    money,
    normalize_candles,
    prior_low,
    ratio,
    safe_segment,
    strategy_label,
    timeframe_settings,
    write_compact_json,
    write_json,
)

PHASE = "SV2.3"
REPORT_NAME = "sv2_3_realistic_backtest"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_SUMMARY_OUTPUT = Path("docs/sv2_3_realistic_backtest_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/sv2_3_realistic_backtest.md")
DEFAULT_CHART_ROOT = Path("reports/strategy_validation/sv2_3_realistic_backtest_dashboard_chart_data")
PRIMARY_FILL_ASSUMPTION = "next_candle_open"
PROMOTION_DISABLED_FILL_ASSUMPTIONS = ("same_candle_close_research_only", "next_candle_close")
SCENARIO_TRADE_COUNT_GATE = 50
SCENARIO_PROFIT_FACTOR_GATE = Decimal("1.05")
SCENARIO_MAX_DRAWDOWN_PCT_GATE = Decimal("0.45")
CONCENTRATION_GATE = Decimal("0.45")


@dataclass(frozen=True, slots=True)
class ExecutionScenario:
    scenario_id: str
    label: str
    fee_bps: Decimal
    slippage_bps: Decimal
    adverse_gap_penalty_bps: Decimal
    adverse_gap_warn_bps: Decimal
    description: str


@dataclass(frozen=True, slots=True)
class SV23Result:
    strategy_id: str
    strategy_label: str
    symbol: str
    timeframe: str
    execution_scenario: str
    fill_assumption: str
    status: str
    starting_equity: str
    ending_equity: str
    net_pnl: str
    max_drawdown: str
    max_drawdown_pct: str
    trade_count: int
    win_rate: str | None
    profit_factor: str | None
    largest_win: str
    largest_loss: str
    fee_bps: str
    slippage_bps: str
    adverse_gap_penalty_bps: str
    adverse_gap_warn_bps: str
    chart_data_path: str
    gate_status: str
    reason_codes: tuple[str, ...]
    reason_counts: dict[str, int]
    research_only: bool
    production_approved: bool
    testnet_prices_used_as_strategy_truth: bool
    testnet_fills_update_pnl: bool
    live_trading_approved: bool


EXECUTION_SCENARIOS = (
    ExecutionScenario(
        scenario_id="base_next_open",
        label="Base next-open realistic",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("3"),
        adverse_gap_penalty_bps=Decimal("0"),
        adverse_gap_warn_bps=Decimal("250"),
        description="Next-candle-open fills with current baseline fee and slippage assumptions.",
    ),
    ExecutionScenario(
        scenario_id="conservative_next_open",
        label="Conservative next-open",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("8"),
        adverse_gap_penalty_bps=Decimal("2"),
        adverse_gap_warn_bps=Decimal("150"),
        description="Next-candle-open fills with higher slippage and small adverse-gap penalty.",
    ),
    ExecutionScenario(
        scenario_id="stress_next_open",
        label="Stress next-open",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("15"),
        adverse_gap_penalty_bps=Decimal("5"),
        adverse_gap_warn_bps=Decimal("75"),
        description="Next-candle-open fills with high slippage and explicit adverse-gap stress.",
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--chart-root", type=Path, default=DEFAULT_CHART_ROOT)
    parser.add_argument("--write-chart-data", action="store_true")
    parser.add_argument("--run-timestamp", default=None)
    return parser


def bps_rate(value: Decimal) -> Decimal:
    return value / Decimal("10000")


def adverse_gap_bps(signal_candle: dict[str, Any], fill_candle: dict[str, Any], side: str) -> Decimal:
    signal_close = dec(signal_candle["close"])
    fill_open = dec(fill_candle["open"])
    if signal_close <= 0:
        return Decimal("0")
    if side == "buy":
        return max(Decimal("0"), (fill_open - signal_close) / signal_close * Decimal("10000"))
    return max(Decimal("0"), (signal_close - fill_open) / signal_close * Decimal("10000"))


def execution_price(
    *,
    raw_price: Decimal,
    scenario: ExecutionScenario,
    side: str,
    adverse_gap: Decimal,
) -> Decimal:
    total_bps = scenario.slippage_bps + (scenario.adverse_gap_penalty_bps if adverse_gap > 0 else Decimal("0"))
    if side == "buy":
        return money(raw_price * (Decimal("1") + bps_rate(total_bps)))
    return money(raw_price * (Decimal("1") - bps_rate(total_bps)))


def next_open_fill_candle(candles: list[dict[str, Any]], signal_index: int) -> dict[str, Any] | None:
    if signal_index + 1 >= len(candles):
        return None
    return candles[signal_index + 1]


def stage_rows_for(candles: list[dict[str, Any]], indicator_rows: list[dict[str, Any]]) -> list[str]:
    stages: list[str] = []
    prior_stage = "stage_unknown_insufficient_history"
    for index in range(len(candles)):
        prior_stage = classify_stage(candles, indicator_rows, index, prior_stage)
        stages.append(prior_stage)
    return stages


def gap_reason_codes(prefix: str, gap_bps: Decimal, scenario: ExecutionScenario) -> list[str]:
    if gap_bps <= scenario.adverse_gap_warn_bps:
        return []
    return [
        f"{prefix}_adverse_gap_warning",
        f"{prefix}_adverse_gap_over_{fmt_decimal(scenario.adverse_gap_warn_bps) or scenario.adverse_gap_warn_bps}_bps",
    ]


def scenario_gate(summary: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    net_pnl = dec(summary.get("net_pnl"))
    trade_count = int(summary.get("trade_count") or 0)
    max_drawdown_pct = dec(summary.get("max_drawdown_pct"))
    profit_factor = summary.get("profit_factor")
    profit_factor_value = dec(profit_factor) if profit_factor is not None else Decimal("0")
    if net_pnl <= 0:
        reasons.append("net_pnl_not_positive_after_costs")
    if trade_count < SCENARIO_TRADE_COUNT_GATE:
        reasons.append("trade_count_below_realistic_gate")
    if profit_factor_value < SCENARIO_PROFIT_FACTOR_GATE:
        reasons.append("profit_factor_below_realistic_gate")
    if max_drawdown_pct > SCENARIO_MAX_DRAWDOWN_PCT_GATE:
        reasons.append("drawdown_above_realistic_gate")
    if not reasons:
        return "passes_realistic_scenario_gate", ("passes_realistic_scenario_gate",)
    return "fails_realistic_scenario_gate", tuple(reasons)


def replay_realistic_strategy(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    scenario: ExecutionScenario,
    indicator_rows: list[dict[str, Any]] | None = None,
    stages: list[str] | None = None,
    include_chart_payload: bool = False,
) -> dict[str, Any]:
    indicator_rows = indicator_rows or indicators(candles)
    stages = stages or stage_rows_for(candles, indicator_rows)

    open_position: dict[str, Any] | None = None
    equity = INITIAL_EQUITY
    equity_curve: list[dict[str, str]] = [{"time": candles[0]["close_time"], "equity": fmt_decimal(equity) or "0"}] if candles else []
    mtm_equity_points: list[Decimal] = [equity]
    trades: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for index, candle in enumerate(candles):
        indicator = indicator_rows[index]
        if index + 1 < int(timeframe_settings(timeframe)["min_history_bars"]):
            reason_counts["insufficient_history"] += 1
            continue

        if open_position is not None:
            mtm = equity + (dec(candle["low"]) - dec(open_position["entry_price"])) * dec(open_position["quantity"])
            mtm_equity_points.append(mtm)
            if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
                exit_reason = mf_orig_exit_reason(candles, indicator_rows, index, dec(open_position["stop_price"]))
            else:
                exit_reason = baseline_exit_reason(indicator, candle, timeframe)
            if exit_reason is None:
                reason_counts["paper_hold"] += 1
                continue
            fill = next_open_fill_candle(candles, index)
            if fill is None:
                reason_counts["exit_signal_skipped_no_next_open_fill_candle"] += 1
                continue
            gap_bps = adverse_gap_bps(candle, fill, "sell")
            raw_exit = dec(fill["open"])
            if exit_reason == "structure_stop_hit":
                raw_exit = min(dec(open_position["stop_price"]), raw_exit)
            exit_price = execution_price(raw_price=raw_exit, scenario=scenario, side="sell", adverse_gap=gap_bps)
            quantity = dec(open_position["quantity"])
            gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
            exit_notional = money(exit_price * quantity)
            exit_fee = money(exit_notional * bps_rate(scenario.fee_bps))
            net_pnl = money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
            equity_before = equity
            equity = money(equity + gross_pnl - exit_fee)
            exit_reason_codes = [exit_reason, *gap_reason_codes("exit", gap_bps, scenario)]
            trade = {
                "trade_id": f"sv23-{safe_segment(scenario.scenario_id)}-{safe_segment(strategy_id)}-{safe_segment(symbol)}-{timeframe}-{len(trades) + 1}",
                "strategy_id": strategy_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "execution_scenario": scenario.scenario_id,
                "fill_timing": PRIMARY_FILL_ASSUMPTION,
                "promotion_fill_eligible": True,
                "entry_signal_time": open_position["entry_signal_time"],
                "entry_fill_time": open_position["entry_time"],
                "entry_time": open_position["entry_time"],
                "exit_signal_time": candle["close_time"],
                "exit_fill_time": fill["open_time"],
                "exit_time": fill["open_time"],
                "entry_price": open_position["entry_price"],
                "exit_price": fmt_decimal(exit_price),
                "quantity": open_position["quantity"],
                "notional": open_position["notional"],
                "net_pnl": fmt_decimal(net_pnl),
                "gross_pnl": fmt_decimal(gross_pnl),
                "fees": fmt_decimal(exit_fee + dec(open_position["entry_fee"])),
                "slippage_bps": fmt_decimal(scenario.slippage_bps),
                "adverse_gap_penalty_bps": fmt_decimal(scenario.adverse_gap_penalty_bps),
                "entry_adverse_gap_bps": open_position["entry_adverse_gap_bps"],
                "exit_adverse_gap_bps": fmt_decimal(gap_bps),
                "equity_before_trade": fmt_decimal(equity_before),
                "equity_after_trade": fmt_decimal(equity),
                "entry_reason_codes": open_position["entry_reason_codes"],
                "exit_reason_codes": exit_reason_codes,
                "exit_reason": exit_reason,
                "forced_exit": False,
                "source": "sv2_3_realistic_backtest",
                "historical_replay_not_live": True,
            }
            trades.append(trade)
            equity_curve.append({"time": trade["exit_fill_time"], "equity": fmt_decimal(equity) or "0"})
            mtm_equity_points.append(equity)
            reason_counts.update(exit_reason_codes)
            open_position = None
            continue

        if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
            entry_allowed, entry_reasons = mf_orig_entry_reason(candles, indicator_rows, stages, index)
            reason = entry_reasons[0] if not entry_allowed else None
        else:
            reason = baseline_entry_reason(indicator, candle, timeframe)
            entry_allowed = reason is None
            entry_reasons = ["baseline_entry_allowed"]
            if entry_allowed and strategy_id == "avoid_low_rolling_range_20":
                rolling_range = indicator.get("rolling_range_20")
                if rolling_range is not None and float(rolling_range) <= 0.025:
                    entry_allowed = False
                    reason = "avoid_low_rolling_range_20_blocked_baseline_entry"
                    entry_reasons = ["blocked_low_rolling_range"]
        if not entry_allowed:
            reason_counts[reason or "no_trade"] += 1
            continue

        fill = next_open_fill_candle(candles, index)
        if fill is None:
            reason_counts["open_signal_skipped_no_next_open_fill_candle"] += 1
            continue
        gap_bps = adverse_gap_bps(candle, fill, "buy")
        entry_price = execution_price(raw_price=dec(fill["open"]), scenario=scenario, side="buy", adverse_gap=gap_bps)
        notional = equity
        quantity = notional / entry_price if entry_price > 0 else Decimal("0")
        if quantity <= 0:
            reason_counts["invalid_entry_quantity"] += 1
            continue
        entry_fee = money(notional * bps_rate(scenario.fee_bps))
        equity = money(equity - entry_fee)
        entry_reason_codes = [*entry_reasons, *gap_reason_codes("entry", gap_bps, scenario)]
        stop_price = prior_low(candles, index, 10) or dec(candle["low"])
        open_position = {
            "entry_signal_time": candle["close_time"],
            "entry_time": fill["open_time"],
            "entry_price": fmt_decimal(entry_price),
            "quantity": fmt_decimal(quantity),
            "notional": fmt_decimal(notional),
            "entry_fee": fmt_decimal(entry_fee),
            "entry_reason_codes": entry_reason_codes,
            "entry_adverse_gap_bps": fmt_decimal(gap_bps),
            "stop_price": fmt_decimal(stop_price),
        }
        reason_counts["paper_opened"] += 1
        reason_counts.update(gap_reason_codes("entry", gap_bps, scenario))
        mtm_equity_points.append(equity)

    if open_position is not None and candles:
        last = candles[-1]
        exit_price = execution_price(raw_price=dec(last["close"]), scenario=scenario, side="sell", adverse_gap=Decimal("0"))
        quantity = dec(open_position["quantity"])
        gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
        exit_notional = money(exit_price * quantity)
        exit_fee = money(exit_notional * bps_rate(scenario.fee_bps))
        net_pnl = money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
        equity_before = equity
        equity = money(equity + gross_pnl - exit_fee)
        trades.append({
            "trade_id": f"sv23-{safe_segment(scenario.scenario_id)}-{safe_segment(strategy_id)}-{safe_segment(symbol)}-{timeframe}-{len(trades) + 1}",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "execution_scenario": scenario.scenario_id,
            "fill_timing": PRIMARY_FILL_ASSUMPTION,
            "promotion_fill_eligible": True,
            "entry_signal_time": open_position["entry_signal_time"],
            "entry_fill_time": open_position["entry_time"],
            "entry_time": open_position["entry_time"],
            "exit_signal_time": last["close_time"],
            "exit_fill_time": last["close_time"],
            "exit_time": last["close_time"],
            "entry_price": open_position["entry_price"],
            "exit_price": fmt_decimal(exit_price),
            "quantity": open_position["quantity"],
            "notional": open_position["notional"],
            "net_pnl": fmt_decimal(net_pnl),
            "gross_pnl": fmt_decimal(gross_pnl),
            "fees": fmt_decimal(exit_fee + dec(open_position["entry_fee"])),
            "slippage_bps": fmt_decimal(scenario.slippage_bps),
            "adverse_gap_penalty_bps": fmt_decimal(scenario.adverse_gap_penalty_bps),
            "entry_adverse_gap_bps": open_position["entry_adverse_gap_bps"],
            "exit_adverse_gap_bps": "0",
            "equity_before_trade": fmt_decimal(equity_before),
            "equity_after_trade": fmt_decimal(equity),
            "entry_reason_codes": open_position["entry_reason_codes"],
            "exit_reason_codes": ["end_of_window_forced_close"],
            "exit_reason": "end_of_window_forced_close",
            "forced_exit": True,
            "source": "sv2_3_realistic_backtest",
            "historical_replay_not_live": True,
        })
        equity_curve.append({"time": last["close_time"], "equity": fmt_decimal(equity) or "0"})
        mtm_equity_points.append(equity)
        reason_counts["end_of_window_forced_close"] += 1

    peak = INITIAL_EQUITY
    max_drawdown = Decimal("0")
    for point in mtm_equity_points:
        peak = max(peak, point)
        max_drawdown = max(max_drawdown, peak - point)
    wins = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) > 0]
    losses = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) < 0]
    gross_wins = sum(wins, Decimal("0"))
    gross_losses = abs(sum(losses, Decimal("0")))
    summary = {
        "starting_equity": fmt_decimal(INITIAL_EQUITY),
        "ending_equity": fmt_decimal(equity),
        "net_pnl": fmt_decimal(equity - INITIAL_EQUITY),
        "max_drawdown": fmt_decimal(max_drawdown),
        "max_drawdown_pct": fmt_decimal(ratio(max_drawdown, INITIAL_EQUITY)),
        "trade_count": len(trades),
        "win_rate": fmt_decimal(ratio(Decimal(len(wins)), Decimal(len(trades)))) if trades else None,
        "profit_factor": fmt_decimal(gross_wins / gross_losses) if gross_losses > 0 else None,
        "largest_win": fmt_decimal(max(wins, default=Decimal("0"))),
        "largest_loss": fmt_decimal(min(losses, default=Decimal("0"))),
    }
    gate_status, gate_reasons = scenario_gate(summary)
    return {
        "strategy_id": strategy_id,
        "strategy_label": strategy_label(strategy_id),
        "strategy_description": "SV2.3 realistic next-candle-open backtest for the founder-selected Week 2 Paper Trading slate.",
        "strategy_truth_lane": "hyperliquid_public_mainnet_sv2_3_realistic_backtest",
        "research_only": True,
        "changes_production_rules": False,
        "production_approved": False,
        "testnet_prices_used_as_strategy_truth": False,
        "symbol": symbol,
        "timeframe": timeframe,
        "component": f"sleeve_{timeframe}",
        "period": "SV2.3",
        "fill_assumption": PRIMARY_FILL_ASSUMPTION,
        "execution_scenario": scenario.scenario_id,
        "execution_scenario_label": scenario.label,
        "data_source": "SV2.2 latest Hyperliquid public-mainnet candles replayed with SV2.3 realistic execution assumptions",
        "candles": normalize_candles(candles) if include_chart_payload else [],
        "indicators": indicator_rows if include_chart_payload else [],
        "trades": trades,
        "markers": markers_for_replay_trades(trades),
        "equity_curve": equity_curve,
        "summary": summary,
        "gate_status": gate_status,
        "gate_reason_codes": list(gate_reasons),
        "reason_counts": dict(sorted(reason_counts.items())),
        "variant_metadata": {
            "phase": PHASE,
            "methodology": "realistic_next_candle_open_backtest",
            "selected_week2_paper_lane": True,
            "fill_assumption": PRIMARY_FILL_ASSUMPTION,
            "fee_bps": fmt_decimal(scenario.fee_bps),
            "slippage_bps": fmt_decimal(scenario.slippage_bps),
            "adverse_gap_penalty_bps": fmt_decimal(scenario.adverse_gap_penalty_bps),
            "adverse_gap_warn_bps": fmt_decimal(scenario.adverse_gap_warn_bps),
        },
        "boundary_flags": {
            "evidence_only": True,
            "no_orders": True,
            "no_private_signed_or_order_endpoints": True,
            "testnet_prices_used_as_strategy_truth": False,
            "testnet_fills_update_pnl": False,
            "production_rule_change": False,
            "production_approved": False,
            "live_trading_approved": False,
        },
    }


def selected_chart_path(chart_root: Path, run_timestamp: str, replay: dict[str, Any]) -> Path:
    return chart_root / run_timestamp / "selected" / (
        f"hyperliquid_public_{safe_segment(replay['symbol'])}_{replay['timeframe']}_"
        f"{safe_segment(replay['strategy_id'])}_{safe_segment(replay['execution_scenario'])}_sv23_replay.json"
    )


def result_from_replay(replay: dict[str, Any], chart_path: Path) -> SV23Result:
    summary = replay["summary"]
    metadata = replay.get("variant_metadata", {})
    return SV23Result(
        strategy_id=replay["strategy_id"],
        strategy_label=replay["strategy_label"],
        symbol=replay["symbol"],
        timeframe=replay["timeframe"],
        execution_scenario=replay["execution_scenario"],
        fill_assumption=replay["fill_assumption"],
        status="completed",
        starting_equity=summary["starting_equity"],
        ending_equity=summary["ending_equity"],
        net_pnl=summary["net_pnl"],
        max_drawdown=summary["max_drawdown"],
        max_drawdown_pct=summary["max_drawdown_pct"],
        trade_count=int(summary["trade_count"]),
        win_rate=summary["win_rate"],
        profit_factor=summary["profit_factor"],
        largest_win=summary["largest_win"],
        largest_loss=summary["largest_loss"],
        fee_bps=metadata.get("fee_bps", "n/a"),
        slippage_bps=metadata.get("slippage_bps", "n/a"),
        adverse_gap_penalty_bps=metadata.get("adverse_gap_penalty_bps", "n/a"),
        adverse_gap_warn_bps=metadata.get("adverse_gap_warn_bps", "n/a"),
        chart_data_path=chart_path.as_posix(),
        gate_status=replay["gate_status"],
        reason_codes=tuple(replay["gate_reason_codes"]),
        reason_counts=replay["reason_counts"],
        research_only=True,
        production_approved=False,
        testnet_prices_used_as_strategy_truth=False,
        testnet_fills_update_pnl=False,
        live_trading_approved=False,
    )


def load_sv22_datasets(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("phase") != "SV2.2":
        raise ValueError("sv23_requires_sv2_2_summary_input")
    return summary, [
        row for row in summary.get("datasets", [])
        if row.get("status") == "refreshed" and row.get("raw_path") and Path(row["raw_path"]).exists()
    ]


def aggregate_results(results: Sequence[SV23Result]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[SV23Result]] = defaultdict(list)
    for row in results:
        buckets[(row.strategy_id, row.execution_scenario)].append(row)
    aggregates: list[dict[str, Any]] = []
    for (strategy_id, scenario_id), rows in sorted(buckets.items()):
        net_pnl = sum((dec(row.net_pnl) for row in rows), Decimal("0"))
        total_trades = sum(row.trade_count for row in rows)
        max_drawdown = max((dec(row.max_drawdown) for row in rows), default=Decimal("0"))
        wins = [dec(row.net_pnl) for row in rows if dec(row.net_pnl) > 0]
        losses = [dec(row.net_pnl) for row in rows if dec(row.net_pnl) < 0]
        gross_losses = abs(sum(losses, Decimal("0")))
        profit_factor = (sum(wins, Decimal("0")) / gross_losses) if gross_losses > 0 else None
        symbol_pnl: dict[str, Decimal] = defaultdict(Decimal)
        timeframe_pnl: dict[str, Decimal] = defaultdict(Decimal)
        for row in rows:
            symbol_pnl[row.symbol] += dec(row.net_pnl)
            timeframe_pnl[row.timeframe] += dec(row.net_pnl)
        positive_denominator = abs(net_pnl) if net_pnl != 0 else Decimal("1")
        symbol_concentration = max((abs(value) / positive_denominator for value in symbol_pnl.values()), default=Decimal("0"))
        timeframe_concentration = max((abs(value) / positive_denominator for value in timeframe_pnl.values()), default=Decimal("0"))
        reason_codes: list[str] = []
        if net_pnl <= 0:
            reason_codes.append("aggregate_net_pnl_not_positive_after_costs")
        if total_trades < SCENARIO_TRADE_COUNT_GATE:
            reason_codes.append("aggregate_trade_count_below_gate")
        if profit_factor is None or profit_factor < SCENARIO_PROFIT_FACTOR_GATE:
            reason_codes.append("aggregate_profit_factor_below_gate")
        if symbol_concentration > CONCENTRATION_GATE:
            reason_codes.append("symbol_concentration_above_gate")
        if timeframe_concentration > Decimal("0.70"):
            reason_codes.append("timeframe_concentration_above_gate")
        aggregates.append({
            "strategy_id": strategy_id,
            "strategy_label": strategy_label(strategy_id),
            "execution_scenario": scenario_id,
            "row_count": len(rows),
            "total_net_pnl": fmt_decimal(net_pnl),
            "total_trades": total_trades,
            "max_drawdown_worst": fmt_decimal(max_drawdown),
            "profit_factor": fmt_decimal(profit_factor) if profit_factor is not None else None,
            "symbol_concentration": fmt_decimal(symbol_concentration),
            "timeframe_concentration": fmt_decimal(timeframe_concentration),
            "gate_status": "passes_aggregate_realistic_gate" if not reason_codes else "fails_aggregate_realistic_gate",
            "reason_codes": reason_codes or ["passes_aggregate_realistic_gate"],
        })
    return aggregates


def strategy_gate_summary(aggregates: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_strategy: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in aggregates:
        by_strategy[row["strategy_id"]][row["execution_scenario"]] = row
    summaries: list[dict[str, Any]] = []
    for strategy_id, scenarios in sorted(by_strategy.items()):
        reasons: list[str] = []
        for scenario_id in ("base_next_open", "conservative_next_open"):
            if scenarios.get(scenario_id, {}).get("gate_status") != "passes_aggregate_realistic_gate":
                reasons.append(f"{scenario_id}_failed")
        stress = scenarios.get("stress_next_open")
        if stress is None or dec(stress.get("total_net_pnl")) < 0:
            reasons.append("stress_next_open_net_pnl_negative")
        summaries.append({
            "strategy_id": strategy_id,
            "strategy_label": strategy_label(strategy_id),
            "status": "candidate_for_forward_review" if not reasons else "not_promoted_realistic_gate_failed",
            "reason_codes": reasons or ["passes_base_conservative_and_stress_net_pnl_gate"],
            "scenario_status": {
                scenario_id: scenarios.get(scenario_id, {}).get("gate_status", "missing")
                for scenario_id in ("base_next_open", "conservative_next_open", "stress_next_open")
            },
        })
    return summaries


def build_summary(
    *,
    generated_at: datetime,
    run_timestamp: str,
    sv22_summary: dict[str, Any],
    results: Sequence[SV23Result],
) -> dict[str, Any]:
    result_rows = [asdict(row) for row in results]
    aggregates = aggregate_results(results)
    scenario_rows = [
        {
            "scenario_id": row.scenario_id,
            "label": row.label,
            "fee_bps": fmt_decimal(row.fee_bps),
            "slippage_bps": fmt_decimal(row.slippage_bps),
            "adverse_gap_penalty_bps": fmt_decimal(row.adverse_gap_penalty_bps),
            "adverse_gap_warn_bps": fmt_decimal(row.adverse_gap_warn_bps),
            "description": row.description,
        }
        for row in EXECUTION_SCENARIOS
    ]
    return {
        "phase": PHASE,
        "report": REPORT_NAME,
        "generated_at_utc": iso_utc(generated_at),
        "run_timestamp": run_timestamp,
        "status": "realistic_backtest_complete" if results else "realistic_backtest_blocked",
        "source": {
            "input_summary": DEFAULT_SV22_SUMMARY_INPUT.as_posix(),
            "input_phase": sv22_summary.get("phase"),
            "strategy_truth": "public_hyperliquid_mainnet_candles_from_sv2_2_refresh",
            "testnet_strategy_truth": False,
            "network_fetch_performed": False,
        },
        "universe_policy": {
            "name": "founder_23_symbols",
            "symbols": list(FOUNDER_APPROVED_RESOLVED_SYMBOLS),
        },
        "timeframes": list(ACTIVE_TIMEFRAMES),
        "disabled_timeframes": list(DISABLED_TIMEFRAMES),
        "strategy_ids": list(WEEK2_REPLAY_STRATEGY_IDS),
        "primary_fill_assumption": PRIMARY_FILL_ASSUMPTION,
        "disabled_promotion_fill_assumptions": list(PROMOTION_DISABLED_FILL_ASSUMPTIONS),
        "execution_scenarios": scenario_rows,
        "result_count": len(result_rows),
        "results": result_rows,
        "aggregate_results": aggregates,
        "strategy_gate_summary": strategy_gate_summary(aggregates),
        "candidate_gate": {
            "requires_positive_base_and_conservative_after_costs": True,
            "requires_stress_net_pnl_non_negative": True,
            "min_trade_count": SCENARIO_TRADE_COUNT_GATE,
            "profit_factor_gate": str(SCENARIO_PROFIT_FACTOR_GATE),
            "symbol_concentration_gate": str(CONCENTRATION_GATE),
            "same_candle_promotion_results_allowed": False,
        },
        "dashboard_status": {
            "default_surface_recommendation": "Evidence",
            "evidence_mode": "SV2.3 Latest Realistic Backtest",
            "chart_data_root": (DEFAULT_CHART_ROOT / run_timestamp).as_posix(),
        },
        "boundaries": NO_ORDER_FLAGS,
    }


def render_report(summary: dict[str, Any]) -> str:
    aggregate_rows = summary.get("aggregate_results", [])
    strategy_rows = summary.get("strategy_gate_summary", [])
    lines = [
        "# SV2.3 Realistic Backtest",
        "",
        "## Verdict",
        "",
        f"- Status: `{summary.get('status')}`",
        "- Purpose: realistic next-candle-open evidence layer for the founder-selected Week 2 strategies.",
        "- Default decision surface: Evidence, not Historical Replay.",
        "- Historical Replay remains visual inspection only.",
        "- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.",
        "- Trading boundary: no orders, private/signed/order endpoints, API keys, testnet strategy truth, live approval, or production approval.",
        "",
        "## Realistic Execution Model",
        "",
        f"- Primary fill assumption: `{summary.get('primary_fill_assumption')}`",
        f"- Disabled promotion fills: `{', '.join(summary.get('disabled_promotion_fill_assumptions', []))}`",
        "- Signals are evaluated after candle close; fills occur at the next candle open with fees, slippage, and scenario stress.",
        "- SV2.3 does not use same-candle fills for promotion-facing results.",
        "",
        "## Scope",
        "",
        f"- Generated at UTC: `{summary.get('generated_at_utc')}`",
        f"- Strategies: `{', '.join(summary.get('strategy_ids', []))}`",
        f"- Timeframes: `{', '.join(summary.get('timeframes', []))}`",
        f"- Disabled timeframes: `{', '.join(summary.get('disabled_timeframes', []))}`",
        f"- Result rows: `{summary.get('result_count')}`",
        "",
        "## Strategy Gate Summary",
        "",
        "| Strategy | Status | Reasons |",
        "| --- | --- | --- |",
        *[
            f"| `{row['strategy_id']}` | `{row['status']}` | `{', '.join(row.get('reason_codes', []))}` |"
            for row in strategy_rows
        ],
        "",
        "## Aggregate Results",
        "",
        "| Strategy | Scenario | Net PnL | Trades | Profit Factor | Worst DD | Gate |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        *[
            "| `{strategy_id}` | `{execution_scenario}` | `{total_net_pnl}` | `{total_trades}` | `{profit_factor}` | `{max_drawdown_worst}` | `{gate_status}` |".format(**row)
            for row in aggregate_rows
        ],
        "",
        "## Boundaries",
        "",
        "- Public Hyperliquid mainnet candles from SV2.2 remain strategy truth.",
        "- Testnet data is not strategy truth.",
        "- Testnet fills do not update PnL.",
        "- No live trading is approved.",
        "- No strategy is production-approved.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    run_timestamp = args.run_timestamp or generated_at.strftime("%Y%m%dT%H%M%SZ")
    sv22_summary, datasets = load_sv22_datasets(args.sv22_summary)
    results: list[SV23Result] = []
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
            for scenario in EXECUTION_SCENARIOS:
                replay = replay_realistic_strategy(
                    strategy_id=strategy_id,
                    symbol=dataset["symbol"],
                    timeframe=dataset["timeframe"],
                    candles=candles,
                    scenario=scenario,
                    indicator_rows=indicator_rows,
                    stages=stages,
                    include_chart_payload=args.write_chart_data,
                )
                chart_path = selected_chart_path(args.chart_root, run_timestamp, replay)
                if args.write_chart_data:
                    payload = {
                        "report": "sv2_3_realistic_backtest_dashboard_chart_data",
                        "phase": PHASE,
                        "generated_from": {
                            "summary": args.summary_output.as_posix(),
                            "sv22_summary": args.sv22_summary.as_posix(),
                            "raw_candles": dataset["raw_path"],
                        },
                        "symbol": dataset["symbol"],
                        "timeframe": dataset["timeframe"],
                        "period": "SV2.3",
                        "selected_replay": {
                            "strategy_id": strategy_id,
                            "fill_assumption": PRIMARY_FILL_ASSUMPTION,
                            "execution_scenario": scenario.scenario_id,
                        },
                        "replays": [replay],
                    }
                    write_compact_json(chart_path, payload)
                results.append(result_from_replay(replay, chart_path))
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
