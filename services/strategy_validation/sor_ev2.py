"""SOR-EV2 true-forward stop/exit and rejected-signal replay.

This module consumes canonical SV2.0.2 evidence-pack requests as the baseline
inventory, reloads persisted candle truth through the existing Strategy Validation
backtest service, and runs research-only true-forward variants. It does not
change production Money Flow rules, create trading artifacts, or call exchange
adapters.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence

from core.domain.enums import (
    DecisionAction,
    Environment,
    StrategyDecisionStatus,
    StrategyFamily,
    StrategyValidationCapitalSizingMode,
    StrategyValidationFillTiming,
    Timeframe,
)
from core.domain.models import Candle, StrategyValidationAssumptions, StrategyValidationRequest, StrategyValidationTrade
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    _CandleRegime,
    _ResolvedFill,
    _build_metrics,
    _coerce_utc,
    _close_trade,
    _data_coverage,
    _dynamic_equity_is_depleted,
    _json_ready,
    _label_candle_regimes,
    _last_candle_in_window,
    _money,
    _open_trade,
    _position_from_open_position,
    _resolve_fill,
    _stable_hash,
)
from services.strategy_validation.sor_ev1 import (
    CANONICAL_SV202_TIMESTAMP,
    CANONICAL_SV202_PATH_TOKEN,
    CANONICAL_SYMBOLS,
    CANONICAL_TIMEFRAMES,
    METHODOLOGIES,
    canonical_sv202_batch_report_paths,
)

FIXED_STOP_VARIANTS: dict[str, Decimal] = {
    "fixed_stop_loss_pct_1": Decimal("0.01"),
    "fixed_stop_loss_pct_1_5": Decimal("0.015"),
    "fixed_stop_loss_pct_2": Decimal("0.02"),
}
ATR_STOP_VARIANTS: dict[str, Decimal] = {
    "atr_stop_1_5x": Decimal("1.5"),
    "atr_stop_2x": Decimal("2"),
}
RECENT_LOW_VARIANTS: dict[str, int] = {
    "recent_low_stop_lookback_5": 5,
    "recent_low_stop_lookback_10": 10,
}
ENTRY_VARIANTS = {
    "macd_histogram_improving_entry",
    "macd_histogram_above_negative_threshold",
    "lower_rsi_trend_intact_entry",
    "reject_entry_if_price_too_far_above_ema10",
    "reject_entry_if_price_too_far_above_sma20",
    "avoid_sideways_low_volatility",
    "avoid_macd_flat_chop",
}
ALL_VARIANTS: tuple[str, ...] = (
    *FIXED_STOP_VARIANTS.keys(),
    *ATR_STOP_VARIANTS.keys(),
    *RECENT_LOW_VARIANTS.keys(),
    "large_bear_candle_exit",
    *sorted(ENTRY_VARIANTS),
)
FORBIDDEN_REPORT_PHRASES = (
    "proven",
    "optimal",
    "approved for live",
    "guaranteed",
    "ready for real trading",
    "production-approved",
)


def build_sor_ev2_report_sync(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    """Synchronous wrapper for CLI/tests."""

    return asyncio.run(
        build_sor_ev2_report(
            batch_report_paths,
            generated_at=generated_at,
            max_scenarios=max_scenarios,
            backtest_service=backtest_service,
        )
    )


async def build_sor_ev2_report(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in (batch_report_paths or canonical_sv202_batch_report_paths())]
    _assert_canonical_paths(paths)
    scenarios = _load_canonical_scenarios(paths)
    if max_scenarios is not None:
        scenarios = scenarios[:max_scenarios]
    service = backtest_service or MoneyFlowBacktestService()
    generated_at = generated_at or datetime.now(UTC)

    baseline_parity: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    variant_rows: list[dict[str, Any]] = []
    rejected_counter: Counter[str] = Counter()
    admitted_counter: Counter[str] = Counter()
    large_loss_rows: list[dict[str, Any]] = []
    limitations: set[str] = set()

    for scenario in scenarios:
        request = _request_from_payload(scenario["request"])
        try:
            baseline_report = await service.run_money_flow_backtest(request)
        except Exception as exc:  # pragma: no cover - exercised by integration/report runs.
            row = _blocked_parity_row(scenario, exc)
            baseline_parity.append(row)
            limitations.add("one_or_more_baseline_replays_blocked")
            continue
        component_report = baseline_report.component_reports[0]
        parity = _parity_row(scenario, component_report.metrics)
        baseline_parity.append(parity)
        baseline_rows.append(_baseline_row(scenario, component_report.metrics, component_report.trades, parity))
        candles = service._load_candles(request=request, timeframe=component_report.timeframe, end_at=request.end_at)
        snapshots = service._indicator_service._compute_snapshots(candles)
        large_loss_rows.extend(_large_loss_context_rows(component_report.trades, candles, snapshots, limit=5))
        if parity["status"] == "baseline_parity_failed":
            limitations.add("variant_conclusions_blocked_for_failed_baseline_parity")
            continue
        for variant_id in ALL_VARIANTS:
            replay = await _run_variant_replay(
                service=service,
                request=request,
                scenario=scenario,
                variant_id=variant_id,
                preloaded_candles=candles,
                preloaded_snapshots=snapshots,
            )
            variant_rows.append(replay["row"])
            rejected_counter.update(replay["rejected_signal_counts"])
            admitted_counter.update(replay["variant_admitted_from_rejection_counts"])
            limitations.update(replay.get("limitations", []))

    variant_summary = _variant_summary(variant_rows)
    control = _control_pocket_impact(variant_rows, baseline_rows)
    candidates = _candidate_variants(variant_summary, control)
    rejected = _rejected_variants(variant_summary, candidates)
    report = {
        "phase": "SOR-EV2",
        "generated_at": generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "true_forward_replay_ready_for_founder_review",
        "baseline_evidence_references": [str(path) for path in paths],
        "canonical_baseline": {
            "source": "SV2.0.2 canonical DB-imported evidence packs",
            "timestamp": CANONICAL_SV202_TIMESTAMP,
            "path_count": len(paths),
            "symbols": list(CANONICAL_SYMBOLS),
            "timeframes": list(CANONICAL_TIMEFRAMES),
            "money_flow_version": "money_flow_v1_2",
            "capital_mode": "dynamic_equity_pct",
            "initial_equity_per_independent_scenario": "10000",
            "forbidden_sources_excluded": [
                "dashboard_date_filter_recalculation",
                "dashboard_chart_data_json_as_canonical_evidence",
                "hyperliquid_testnet_prices",
                "sv1_13_dynamic_equity_packs",
                "compact_sv2_rows",
            ],
        },
        "baseline_parity_results": baseline_parity,
        "baseline_parity_summary": _parity_summary(baseline_parity),
        "baseline_summary": _baseline_summary(baseline_rows),
        "stop_variant_results": [row for row in variant_summary if _variant_family(row["variant_id"]) == "stop_exit"],
        "entry_variant_results": [row for row in variant_summary if _variant_family(row["variant_id"]) == "entry_timing"],
        "variant_results": variant_rows,
        "variant_summary": variant_summary,
        "rejected_signal_replay_summary": {
            "methodology": "true_forward_replay",
            "baseline_rejection_counts": dict(sorted(rejected_counter.items())),
            "variant_admitted_from_rejection_counts": dict(sorted(admitted_counter.items())),
            "required_categories": [
                "rsi_not_constructive",
                "macd_not_constructive",
                "overextended_rsi",
                "entry_quality_not_constructive",
                "insufficient_history",
                "missing_indicator_field",
                "other",
            ],
        },
        "large_loss_candle_context_summary": _large_loss_summary(large_loss_rows),
        "large_loss_candle_context_samples": sorted(large_loss_rows, key=lambda row: _dec(row["net_pnl"]))[:20],
        "control_pocket_impact": control,
        "candidate_variants": candidates,
        "rejected_variants": rejected,
        "methodology_labels": {label: _methodology_description(label) for label in METHODOLOGIES},
        "limitations": sorted(limitations | {
            "independent_scenarios_are_not_one_combined_account",
            "stop_signals_exit_on_configured_fill_timing_after_observed_candle_not_intrabar_stop_fill",
            "no_variant_is_production_approved",
        }),
        "boundary_flags": {
            "uses_only_canonical_sv2_0_2_pack_paths": True,
            "loads_db_candles_or_service_candle_truth": True,
            "uses_dashboard_date_filter_recalculation": False,
            "uses_dashboard_chart_data_as_canonical_evidence": False,
            "uses_hyperliquid_testnet_prices": False,
            "changes_production_money_flow_rules": False,
            "optimizes_parameters_blindly": False,
            "approves_paper_trading": False,
            "approves_live_trading": False,
            "creates_orders": False,
            "calls_private_signed_or_order_endpoints": False,
            "adds_sor_fanout_cbbo_or_target_reselection": False,
        },
    }
    return _json_ready(report)


async def _run_variant_replay(
    *,
    service: MoneyFlowBacktestService,
    request: StrategyValidationRequest,
    scenario: dict[str, Any],
    variant_id: str,
    preloaded_candles: list[Candle] | None = None,
    preloaded_snapshots: Sequence[Any] | None = None,
) -> dict[str, Any]:
    sleeve = service._requested_sleeves(request.component_keys)[0]
    start_at = _coerce_utc(request.start_at)
    end_at = _coerce_utc(request.end_at)
    candles = preloaded_candles if preloaded_candles is not None else service._load_candles(request=request, timeframe=sleeve.timeframe, end_at=end_at)
    snapshots = preloaded_snapshots if preloaded_snapshots is not None else service._indicator_service._compute_snapshots(candles)
    data_coverage = _data_coverage(candles, timeframe=sleeve.timeframe, start_at=start_at, end_at=end_at)
    regime_by_close_time = _label_candle_regimes(candles)
    atr = _atr_by_index(candles)
    trades: list[StrategyValidationTrade] = []
    no_trade: Counter[str] = Counter()
    invalid: Counter[str] = Counter()
    rejected: Counter[str] = Counter()
    admitted: Counter[str] = Counter()
    limitations: set[str] = set(data_coverage.warning_reason_codes)
    open_position: Any | None = None
    open_context: dict[str, Any] | None = None
    realized_equity = request.assumptions.initial_capital
    closed_points = [request.assumptions.initial_capital]
    mtm_points = [request.assumptions.initial_capital]
    stop_exits = 0
    early_exits = 0
    variant_entries = 0
    new_bad_trades = 0
    trades_skipped_due_to_insufficient_equity = 0

    for signal_index, (candle, snapshot) in enumerate(zip(candles, snapshots, strict=False)):
        close_time = _coerce_utc(candle.close_time)
        if close_time <= start_at or close_time > end_at:
            continue
        regime = regime_by_close_time.get(close_time, _CandleRegime.unknown(close_time))
        position_active = open_position is not None and close_time > open_position.entry_time
        current_position = _position_from_open_position(open_position, request=request, candle=candle) if position_active else None
        evaluation_input = service._evaluation_input(
            request=request,
            sleeve=sleeve,
            candle=candle,
            snapshot=snapshot,
            history_bars=signal_index + 1,
            current_position=current_position,
            position_state_fingerprint=open_position.position_state_fingerprint if position_active else None,
        )
        evaluation = await service._strategy_family.evaluate(evaluation_input)
        decision = evaluation.decision
        features = _snapshot_features(snapshot, candle, sleeve)

        if open_position is not None:
            if close_time > open_position.entry_time:
                open_position.record_excursion(candle)
                mtm_points.append(open_position.mark_to_market_equity(realized_equity, candle.low))
            if close_time <= open_position.entry_time:
                continue
            variant_exit = _variant_exit_reason(
                variant_id=variant_id,
                open_position=open_position,
                open_context=open_context or {},
                candles=candles,
                snapshots=snapshots,
                signal_index=signal_index,
                features=features,
                atr_by_index=atr,
            )
            should_close = variant_exit is not None or decision.action in {DecisionAction.CLOSE, DecisionAction.REDUCE}
            if should_close:
                if decision.action == DecisionAction.REDUCE and variant_exit is None:
                    limitations.add("reduce_actions_are_simulated_as_full_exits_for_sor_ev2")
                fill = _resolve_fill(candles=candles, signal_index=signal_index, fill_timing=request.assumptions.fill_timing)
                if fill is None:
                    limitations.add(f"exit_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}")
                    continue
                if request.assumptions.fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_CLOSE:
                    open_position.record_excursion(fill.candle)
                    mtm_points.append(open_position.mark_to_market_equity(realized_equity, fill.candle.low))
                exit_reason = variant_exit or decision.reason_code or decision.action.value
                trade = _close_trade(
                    request=request,
                    open_position=open_position,
                    fill=fill,
                    exit_signal_time=close_time,
                    exit_reason=exit_reason,
                    exit_evaluation_key=(decision.evaluation_key or "sor_ev2") + f":{variant_id}:{exit_reason}",
                    exit_market_regime=regime.trend_label,
                    exit_volatility_regime=regime.volatility_label,
                    forced_exit=False,
                )
                trades.append(trade)
                if variant_exit is not None:
                    stop_exits += 1
                    early_exits += 1
                if open_context and open_context.get("variant_entry") and trade.net_pnl < 0:
                    new_bad_trades += 1
                realized_equity = _money(realized_equity + trade.net_pnl)
                closed_points.append(realized_equity)
                mtm_points.append(realized_equity)
                open_position = None
                open_context = None
            continue

        if decision.status == StrategyDecisionStatus.INVALID:
            reason = decision.reason_code or "invalid_without_reason"
            invalid[_rejection_category(reason)] += 1
            continue

        variant_entry_allowed = False
        if decision.status == StrategyDecisionStatus.NO_TRADE:
            reason = decision.reason_code or "no_trade_without_reason"
            category = _rejection_category(reason)
            rejected[category] += 1
            no_trade[reason] += 1
            variant_entry_allowed = _variant_entry_allowed(variant_id, reason, features, regime)
            if variant_entry_allowed:
                admitted[category] += 1
        baseline_open_blocked_by_variant = (
            decision.action == DecisionAction.OPEN
            and _variant_blocks_baseline_entry(variant_id, features, regime)
        )
        if baseline_open_blocked_by_variant:
            no_trade[f"{variant_id}_blocked_baseline_entry"] += 1
        should_open = (decision.action == DecisionAction.OPEN and not baseline_open_blocked_by_variant) or variant_entry_allowed
        if should_open:
            if _dynamic_equity_is_depleted(request.assumptions, realized_equity):
                invalid["dynamic_equity_depleted"] += 1
                trades_skipped_due_to_insufficient_equity += 1
                limitations.add("dynamic_equity_depleted_no_new_trades_opened")
                continue
            fill = _resolve_fill(candles=candles, signal_index=signal_index, fill_timing=request.assumptions.fill_timing)
            if fill is None:
                limitations.add(f"open_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}")
                continue
            entry_reason = f"{variant_id}_admitted_from_{decision.reason_code}" if variant_entry_allowed else decision.reason_code
            open_position = _open_trade(
                request=request,
                sleeve=sleeve,
                fill=fill,
                entry_signal_time=close_time,
                entry_reason=entry_reason,
                entry_evaluation_key=(decision.evaluation_key or "sor_ev2") + (f":{variant_id}" if variant_entry_allowed else ""),
                entry_market_regime=regime.trend_label,
                entry_volatility_regime=regime.volatility_label,
                current_realized_equity=realized_equity,
            )
            if _coerce_utc(fill.candle.close_time) > open_position.entry_time:
                open_position.record_excursion(fill.candle)
                mtm_points.append(open_position.mark_to_market_equity(realized_equity, fill.candle.low))
            open_context = {
                "variant_id": variant_id,
                "variant_entry": variant_entry_allowed,
                "entry_signal_index": signal_index,
                "entry_atr": atr.get(signal_index),
                "entry_recent_low_5": _prior_low(candles, signal_index, 5),
                "entry_recent_low_10": _prior_low(candles, signal_index, 10),
            }
            if variant_entry_allowed:
                variant_entries += 1

    if open_position is not None and request.assumptions.force_close_open_trade_at_end:
        last_candle = _last_candle_in_window(candles, start_at=start_at, end_at=end_at)
        if last_candle is not None:
            open_position.record_excursion(last_candle)
            mtm_points.append(open_position.mark_to_market_equity(realized_equity, last_candle.low))
            fill = _ResolvedFill(candle=last_candle, raw_price=last_candle.close, time=_coerce_utc(last_candle.close_time), source="end_of_window_close")
            trade = _close_trade(
                request=request,
                open_position=open_position,
                fill=fill,
                exit_signal_time=_coerce_utc(last_candle.close_time),
                exit_reason="end_of_window_forced_close",
                exit_evaluation_key=f"{open_position.entry_evaluation_key}:forced_exit",
                exit_market_regime=regime_by_close_time.get(_coerce_utc(last_candle.close_time), _CandleRegime.unknown(_coerce_utc(last_candle.close_time))).trend_label,
                exit_volatility_regime=regime_by_close_time.get(_coerce_utc(last_candle.close_time), _CandleRegime.unknown(_coerce_utc(last_candle.close_time))).volatility_label,
                forced_exit=True,
            )
            trades.append(trade)
            realized_equity = _money(realized_equity + trade.net_pnl)
            closed_points.append(realized_equity)
            mtm_points.append(realized_equity)
            limitations.add("open_positions_are_force_closed_at_window_end_for_sor_ev2")

    metrics = _build_metrics(
        trades=trades,
        initial_capital=request.assumptions.initial_capital,
        no_trade_reason_counts=dict(sorted(no_trade.items())),
        invalid_reason_counts=dict(sorted(invalid.items())),
        closed_trade_equity_points=closed_points,
        mark_to_market_equity_points=mtm_points,
        capital_sizing_mode=request.assumptions.capital_sizing_mode,
        position_notional_pct=request.assumptions.position_notional_pct,
        trades_skipped_due_to_insufficient_equity=trades_skipped_due_to_insufficient_equity,
    )
    canonical_metrics = scenario["metrics"]
    baseline_net = _dec(canonical_metrics.get("net_account_pnl"))
    baseline_ending = _dec(canonical_metrics.get("ending_equity"))
    row = {
        "variant_id": variant_id,
        "variant_family": _variant_family(variant_id),
        "methodology": "true_forward_replay",
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "component_key": scenario["component_key"],
        "fill_timing": scenario["fill_timing"],
        "baseline_ending_equity": _fmt(baseline_ending),
        "variant_ending_equity": _fmt(metrics.ending_equity),
        "baseline_net_pnl": _fmt(baseline_net),
        "variant_net_pnl": _fmt(metrics.net_account_pnl),
        "net_pnl_delta": _fmt(metrics.net_account_pnl - baseline_net),
        "baseline_max_drawdown": _fmt(_dec(canonical_metrics.get("mark_to_market_max_drawdown") or canonical_metrics.get("max_drawdown"))),
        "variant_max_drawdown": _fmt(metrics.mark_to_market_max_drawdown or metrics.max_drawdown),
        "trade_count": metrics.number_of_trades,
        "baseline_trade_count": int(_dec(canonical_metrics.get("number_of_trades"))),
        "win_rate": _fmt(metrics.win_rate or Decimal("0")),
        "profit_factor": _fmt(metrics.profit_factor or Decimal("0")),
        "average_win": _fmt(metrics.average_win or Decimal("0")),
        "average_loss": _fmt(metrics.average_loss or Decimal("0")),
        "largest_loss": _fmt(metrics.worst_trade_net_pnl or Decimal("0")),
        "largest_win": _fmt(metrics.best_trade_net_pnl or Decimal("0")),
        "total_fees": _fmt(metrics.total_fees),
        "total_slippage": _fmt(metrics.total_slippage_cost),
        "max_adverse_excursion": _fmt(max((abs(trade.max_adverse_excursion or Decimal("0")) for trade in trades), default=Decimal("0"))),
        "stop_exits": stop_exits,
        "early_exits": early_exits,
        "avoided_losers": _avoided_loser_estimate(scenario, trades),
        "missed_winners": _missed_winner_estimate(scenario, trades),
        "new_bad_trades": new_bad_trades,
        "variant_entries_from_rejections": variant_entries,
        "outcome": _outcome(metrics, canonical_metrics),
        "candidate_evidence": False,
        "production_approved": False,
        "limitations": sorted(limitations),
    }
    return {
        "row": row,
        "rejected_signal_counts": rejected,
        "variant_admitted_from_rejection_counts": admitted,
        "limitations": sorted(limitations),
    }


def _variant_exit_reason(
    *,
    variant_id: str,
    open_position: Any,
    open_context: dict[str, Any],
    candles: list[Candle],
    snapshots: Sequence[Any],
    signal_index: int,
    features: dict[str, Decimal | bool | None],
    atr_by_index: dict[int, Decimal],
) -> str | None:
    candle = candles[signal_index]
    if variant_id in FIXED_STOP_VARIANTS:
        stop_price = open_position.raw_entry_price * (Decimal("1") - FIXED_STOP_VARIANTS[variant_id])
        if candle.low <= stop_price:
            return f"{variant_id}_observed_low_breach_exit_signal"
    if variant_id in ATR_STOP_VARIANTS:
        entry_atr = open_context.get("entry_atr")
        if isinstance(entry_atr, Decimal) and entry_atr > 0:
            stop_price = open_position.raw_entry_price - (entry_atr * ATR_STOP_VARIANTS[variant_id])
            if candle.low <= stop_price:
                return f"{variant_id}_observed_atr_stop_breach_exit_signal"
        else:
            return None
    if variant_id in RECENT_LOW_VARIANTS:
        lookback = RECENT_LOW_VARIANTS[variant_id]
        prior_low = _prior_low(candles, signal_index, lookback)
        if prior_low is not None and candle.close < prior_low:
            return f"{variant_id}_prior_structure_low_break_exit_signal"
    if variant_id == "large_bear_candle_exit":
        body_pct = _ratio(candle.open - candle.close, candle.open)
        range_pct = _ratio(candle.high - candle.low, candle.open)
        if candle.close < candle.open and body_pct is not None and range_pct is not None:
            if body_pct >= Decimal("0.025") or range_pct >= Decimal("0.05"):
                return "large_bear_candle_exit_observed_current_candle_exit_signal"
    return None


def _variant_blocks_baseline_entry(variant_id: str, features: dict[str, Any], regime: _CandleRegime) -> bool:
    if variant_id == "reject_entry_if_price_too_far_above_ema10":
        extension = features.get("extension_ema10")
        return bool(features.get("indicators_valid")) and isinstance(extension, Decimal) and extension > Decimal("0.03")
    if variant_id == "reject_entry_if_price_too_far_above_sma20":
        extension = features.get("extension_sma20")
        return bool(features.get("indicators_valid")) and isinstance(extension, Decimal) and extension > Decimal("0.05")
    if variant_id == "avoid_sideways_low_volatility":
        return regime.trend_label == "sideways" and regime.volatility_label == "low_volatility"
    if variant_id == "avoid_macd_flat_chop":
        hist = features.get("macd_histogram")
        return regime.trend_label == "sideways" and isinstance(hist, Decimal) and abs(hist) < Decimal("0.005")
    return False


def _variant_entry_allowed(variant_id: str, baseline_reason: str, features: dict[str, Any], regime: _CandleRegime) -> bool:
    if variant_id not in ENTRY_VARIANTS:
        return False
    if not features.get("indicators_valid"):
        return False
    trend_ok = bool(features.get("bullish_alignment"))
    not_extended = bool(features.get("not_overextended_ema5"))
    macd_hist = features.get("macd_histogram")
    macd = features.get("macd")
    macd_signal = features.get("macd_signal")
    rsi = features.get("rsi")
    if variant_id == "macd_histogram_improving_entry":
        return baseline_reason == "macd_not_constructive" and trend_ok and not_extended and isinstance(macd_hist, Decimal) and macd_hist > Decimal("-0.01")
    if variant_id == "macd_histogram_above_negative_threshold":
        return baseline_reason == "macd_not_constructive" and trend_ok and not_extended and isinstance(macd, Decimal) and isinstance(macd_signal, Decimal) and (macd - macd_signal) > Decimal("-0.025")
    if variant_id == "lower_rsi_trend_intact_entry":
        return baseline_reason == "rsi_not_constructive" and trend_ok and not_extended and bool(features.get("macd_constructive")) and isinstance(rsi, Decimal) and rsi >= Decimal("43")
    if variant_id == "reject_entry_if_price_too_far_above_ema10":
        # Filter variant never admits rejected candles; it only blocks baseline opens in _snapshot_features via exit row no-op truth.
        return False
    if variant_id == "reject_entry_if_price_too_far_above_sma20":
        return False
    if variant_id == "avoid_sideways_low_volatility":
        return False
    if variant_id == "avoid_macd_flat_chop":
        return False
    return False


def _snapshot_features(snapshot: Any, candle: Candle, sleeve: Any) -> dict[str, Any]:
    values = {
        "ema5": getattr(snapshot, "ema_5", None),
        "ema10": getattr(snapshot, "ema_10", None),
        "sma20": getattr(snapshot, "sma_20", None),
        "rsi": getattr(snapshot, "rsi_14", None),
        "macd": getattr(snapshot, "macd", None),
        "macd_signal": getattr(snapshot, "macd_signal", None),
        "macd_histogram": getattr(snapshot, "macd_histogram", None),
    }
    valid = all(value is not None and Decimal(str(value)).is_finite() for value in values.values())
    if not valid:
        return {**values, "indicators_valid": False}
    ema5 = Decimal(str(values["ema5"]))
    ema10 = Decimal(str(values["ema10"]))
    sma20 = Decimal(str(values["sma20"]))
    rsi = Decimal(str(values["rsi"]))
    macd = Decimal(str(values["macd"]))
    macd_signal = Decimal(str(values["macd_signal"]))
    macd_hist = Decimal(str(values["macd_histogram"]))
    close = candle.close
    extension_ema5 = _ratio(close - ema5, ema5) or Decimal("0")
    extension_ema10 = _ratio(close - ema10, ema10) or Decimal("0")
    extension_sma20 = _ratio(close - sma20, sma20) or Decimal("0")
    return {
        **values,
        "ema5": ema5,
        "ema10": ema10,
        "sma20": sma20,
        "rsi": rsi,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_histogram": macd_hist,
        "indicators_valid": True,
        "bullish_alignment": ema5 > ema10 > sma20,
        "macd_constructive": macd > macd_signal and macd_hist >= 0,
        "not_overextended_ema5": extension_ema5 <= Decimal(str(sleeve.max_extension_pct_above_ema5)),
        "extension_ema5": extension_ema5,
        "extension_ema10": extension_ema10,
        "extension_sma20": extension_sma20,
    }


def _large_loss_context_rows(
    trades: Sequence[StrategyValidationTrade],
    candles: list[Candle],
    snapshots: Sequence[Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    atr = _atr_by_index(candles)
    by_close = {_coerce_utc(c.close_time): idx for idx, c in enumerate(candles)}
    rows: list[dict[str, Any]] = []
    for trade in sorted([t for t in trades if t.net_pnl < 0], key=lambda t: t.net_pnl)[:limit]:
        in_trade = [
            (idx, candle)
            for idx, candle in enumerate(candles)
            if _coerce_utc(trade.entry_time) <= _coerce_utc(candle.close_time) <= _coerce_utc(trade.exit_time)
        ]
        if not in_trade:
            continue
        red = [
            (idx, candle, _ratio(candle.open - candle.close, candle.open) or Decimal("0"), _ratio(candle.high - candle.low, candle.open) or Decimal("0"))
            for idx, candle in in_trade
            if candle.close < candle.open
        ]
        largest = max(red, key=lambda item: item[2], default=None)
        if largest is None:
            classification = "adverse_move_not_stop_solvable"
            largest_time = None
            body_pct = Decimal("0")
            range_pct = Decimal("0")
            atr_multiple = Decimal("0")
        else:
            idx, candle, body_pct, range_pct = largest
            largest_time = _coerce_utc(candle.close_time).isoformat()
            atr_value = atr.get(idx)
            atr_multiple = ((candle.high - candle.low) / atr_value) if atr_value and atr_value > 0 else Decimal("0")
            classification = "losses_from_large_down_candles" if body_pct >= Decimal("0.025") or range_pct >= Decimal("0.05") else "adverse_move_not_stop_solvable"
        fixed_2_triggered = any(candle.low <= trade.raw_entry_price * Decimal("0.98") for _, candle in in_trade)
        recent_break = any(_prior_low(candles, idx, 5) is not None and candle.close < (_prior_low(candles, idx, 5) or candle.low) for idx, candle in in_trade)
        ema_break = False
        for idx, candle in in_trade:
            if idx < len(snapshots):
                f = _snapshot_features(snapshots[idx], candle, type("Sleeve", (), {"max_extension_pct_above_ema5": Decimal("1")})())
                if f.get("indicators_valid") and (candle.close < f["ema10"] or candle.close < f["sma20"]):
                    ema_break = True
                    break
        if fixed_2_triggered and classification == "losses_from_large_down_candles":
            classification = "stop_would_have_helped"
        rows.append({
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "timeframe": trade.timeframe.value,
            "fill_timing": trade.fill_timing.value,
            "entry_time": _coerce_utc(trade.entry_time).isoformat(),
            "exit_time": _coerce_utc(trade.exit_time).isoformat(),
            "net_pnl": _fmt(trade.net_pnl),
            "exit_reason": trade.exit_reason,
            "largest_red_candle_close_time": largest_time,
            "red_candle_body_percent": _fmt(body_pct),
            "red_candle_range_percent": _fmt(range_pct),
            "atr_multiple": _fmt(atr_multiple),
            "stop_would_have_triggered_before_current_exit": fixed_2_triggered,
            "recent_low_break_before_current_exit": recent_break,
            "ema10_or_sma20_break_before_current_exit": ema_break,
            "exit_late_relative_to_adverse_move": largest_time is not None and largest_time < _coerce_utc(trade.exit_time).isoformat(),
            "classification": classification,
            "methodology": "true_forward_replay",
        })
    return rows


def _atr_by_index(candles: Sequence[Candle], period: int = 14) -> dict[int, Decimal]:
    true_ranges: list[Decimal] = []
    output: dict[int, Decimal] = {}
    previous_close: Decimal | None = None
    for idx, candle in enumerate(candles):
        if previous_close is None:
            tr = candle.high - candle.low
        else:
            tr = max(candle.high - candle.low, abs(candle.high - previous_close), abs(candle.low - previous_close))
        true_ranges.append(tr)
        if len(true_ranges) >= period:
            output[idx] = sum(true_ranges[-period:], Decimal("0")) / Decimal(period)
        previous_close = candle.close
    return output


def _prior_low(candles: Sequence[Candle], signal_index: int, lookback: int) -> Decimal | None:
    prior = candles[max(0, signal_index - lookback):signal_index]
    if len(prior) < lookback:
        return None
    return min(candle.low for candle in prior)


def _request_from_payload(payload: dict[str, Any]) -> StrategyValidationRequest:
    assumptions = payload["assumptions"]
    return StrategyValidationRequest(
        strategy_family=StrategyFamily(payload["strategy_family"]),
        environment=Environment(payload["environment"]),
        venue=payload["venue"],
        symbol=payload["symbol"],
        instrument_key=payload.get("instrument_key"),
        instrument_ref_id=payload.get("instrument_ref_id"),
        start_at=datetime.fromisoformat(payload["start_at"]),
        end_at=datetime.fromisoformat(payload["end_at"]),
        component_keys=tuple(payload.get("component_keys") or ()),
        assumptions=StrategyValidationAssumptions(
            initial_capital=Decimal(str(assumptions["initial_capital"])),
            fee_bps=Decimal(str(assumptions["fee_bps"])),
            slippage_bps=Decimal(str(assumptions["slippage_bps"])),
            position_notional_pct=Decimal(str(assumptions["position_notional_pct"])),
            capital_sizing_mode=StrategyValidationCapitalSizingMode(assumptions["capital_sizing_mode"]),
            fill_timing=StrategyValidationFillTiming(assumptions["fill_timing"]),
            reduce_action_model=assumptions.get("reduce_action_model", "full_exit"),
            force_close_open_trade_at_end=bool(assumptions.get("force_close_open_trade_at_end", True)),
            drawdown_methodology=assumptions.get("drawdown_methodology", "closed_trade_and_mark_to_market"),
        ),
    )


def _load_canonical_scenarios(paths: Sequence[Path]) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for path in paths:
        batch = json.loads(path.read_text(encoding="utf-8"))
        for run in batch.get("run_reports", []):
            if run.get("status") != "completed" or not run.get("report"):
                continue
            report = run["report"]
            component = (report.get("component_reports") or [{}])[0]
            metrics = component.get("metrics") or {}
            request = run.get("request") or {}
            symbol = str(report.get("symbol") or request.get("symbol"))
            timeframe = _canonical_timeframe(str(component.get("timeframe") or (request.get("component_keys") or [""])[0].replace("sleeve_", "")))
            fill_timing = str((request.get("assumptions") or {}).get("fill_timing"))
            scenario_key = f"{symbol}:{timeframe}:{fill_timing}:{run.get('run_id')}"
            scenarios.append({
                "scenario_key": scenario_key,
                "batch_report_path": str(path),
                "run_id": str(run.get("run_id")),
                "symbol": symbol,
                "timeframe": timeframe,
                "component_key": str(component.get("component_key") or (request.get("component_keys") or [""])[0]),
                "fill_timing": fill_timing,
                "request": request,
                "metrics": metrics,
                "canonical_trade_count": len(component.get("trades", [])),
                "canonical_trades": component.get("trades", []),
            })
    return scenarios


def _assert_canonical_paths(paths: Sequence[Path]) -> None:
    if not paths:
        raise FileNotFoundError("No canonical SV2.0.2 batch_report.json paths found.")
    for path in paths:
        text = str(path)
        if CANONICAL_SV202_PATH_TOKEN not in text or CANONICAL_SV202_TIMESTAMP not in text:
            raise ValueError(f"noncanonical SOR-EV2 evidence path: {path}")
        if any(token in text.lower() for token in ("dashboard", "pt0_0_3", "sv1_13", "compact")):
            raise ValueError(f"forbidden SOR-EV2 evidence source path: {path}")


def _parity_row(scenario: dict[str, Any], metrics: Any) -> dict[str, Any]:
    canonical = scenario["metrics"]
    trade_delta = metrics.number_of_trades - int(_dec(canonical.get("number_of_trades")))
    equity_delta = metrics.ending_equity - _dec(canonical.get("ending_equity"))
    pnl_delta = metrics.net_account_pnl - _dec(canonical.get("net_account_pnl"))
    dd_delta = (metrics.mark_to_market_max_drawdown or metrics.max_drawdown) - _dec(canonical.get("mark_to_market_max_drawdown") or canonical.get("max_drawdown"))
    largest_loss_delta = (metrics.worst_trade_net_pnl or Decimal("0")) - _dec(canonical.get("worst_trade_net_pnl"))
    status = "baseline_parity_passed"
    if abs(equity_delta) > Decimal("0.05") or trade_delta != 0:
        status = "baseline_parity_failed"
    elif abs(pnl_delta) > Decimal("0.01") or abs(dd_delta) > Decimal("0.01") or abs(largest_loss_delta) > Decimal("0.01"):
        status = "baseline_parity_warning"
    return {
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "fill_timing": scenario["fill_timing"],
        "status": status,
        "reason_codes": [status],
        "trade_count_delta": trade_delta,
        "ending_equity_delta": _fmt(equity_delta),
        "net_pnl_delta": _fmt(pnl_delta),
        "max_drawdown_delta": _fmt(dd_delta),
        "largest_loss_delta": _fmt(largest_loss_delta),
        "forced_close_count_delta": 0,
    }


def _blocked_parity_row(scenario: dict[str, Any], exc: Exception) -> dict[str, Any]:
    return {
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "fill_timing": scenario["fill_timing"],
        "status": "baseline_parity_failed",
        "reason_codes": ["baseline_parity_failed", "baseline_replay_blocked"],
        "error": str(exc),
    }


def _baseline_row(scenario: dict[str, Any], metrics: Any, trades: Sequence[StrategyValidationTrade], parity: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "component_key": scenario["component_key"],
        "fill_timing": scenario["fill_timing"],
        "parity_status": parity["status"],
        "ending_equity": _fmt(metrics.ending_equity),
        "net_pnl": _fmt(metrics.net_account_pnl),
        "max_drawdown": _fmt(metrics.mark_to_market_max_drawdown or metrics.max_drawdown),
        "trade_count": metrics.number_of_trades,
        "largest_loss": _fmt(metrics.worst_trade_net_pnl or Decimal("0")),
        "positive_control_pocket": metrics.ending_equity > Decimal("10000") or (scenario["symbol"] == "ETH" and scenario["timeframe"] == "1h"),
    }


def _variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant_id"]].append(row)
    output: list[dict[str, Any]] = []
    for variant_id, selected in sorted(grouped.items()):
        output.append({
            "variant_id": variant_id,
            "variant_family": _variant_family(variant_id),
            "methodology": "true_forward_replay",
            "scenario_count": len(selected),
            "outcome": _rollup_outcome(selected),
            "net_pnl_delta_sum_across_independent_scenarios": _fmt(sum((_dec(row["net_pnl_delta"]) for row in selected), Decimal("0"))),
            "ending_equity_delta_sum_across_independent_scenarios": _fmt(sum((_dec(row["variant_ending_equity"]) - _dec(row["baseline_ending_equity"]) for row in selected), Decimal("0"))),
            "max_drawdown_delta_worst": _fmt(max((_dec(row["variant_max_drawdown"]) - _dec(row["baseline_max_drawdown"]) for row in selected), default=Decimal("0"))),
            "stop_exits": sum(int(row["stop_exits"]) for row in selected),
            "early_exits": sum(int(row["early_exits"]) for row in selected),
            "avoided_losers": sum(int(row["avoided_losers"]) for row in selected),
            "missed_winners": sum(int(row["missed_winners"]) for row in selected),
            "new_bad_trades": sum(int(row["new_bad_trades"]) for row in selected),
            "trade_count_delta_sum": sum(int(row["trade_count"]) - int(row["baseline_trade_count"]) for row in selected),
            "per_symbol_impact": _impact_by(selected, "symbol"),
            "per_timeframe_impact": _impact_by(selected, "timeframe"),
            "candidate_evidence": False,
            "production_approved": False,
        })
    return output


def _control_pocket_impact(variant_rows: Sequence[dict[str, Any]], baseline_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    controls = {row["scenario_key"]: row for row in baseline_rows if row["positive_control_pocket"]}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in variant_rows:
        if row["scenario_key"] in controls:
            grouped[row["variant_id"]].append(row)
    output: list[dict[str, Any]] = []
    for variant_id, selected in sorted(grouped.items()):
        improved = sum(1 for row in selected if _dec(row["variant_ending_equity"]) > _dec(row["baseline_ending_equity"]))
        damaged = sum(1 for row in selected if _dec(row["variant_ending_equity"]) < _dec(row["baseline_ending_equity"]))
        dd_reduced = sum(1 for row in selected if _dec(row["variant_max_drawdown"]) < _dec(row["baseline_max_drawdown"]))
        output.append({
            "variant_id": variant_id,
            "control_pocket_count": len(selected),
            "improved": improved,
            "preserved": len(selected) - improved - damaged,
            "damaged": damaged,
            "drawdown_reduced": dd_reduced,
            "return_reduced": damaged,
            "trade_count_increased": sum(1 for row in selected if int(row["trade_count"]) > int(row["baseline_trade_count"])),
            "trade_count_decreased": sum(1 for row in selected if int(row["trade_count"]) < int(row["baseline_trade_count"])),
        })
    return output


def _candidate_variants(summary: Sequence[dict[str, Any]], control: Sequence[dict[str, Any]]) -> list[str]:
    control_by_variant = {row["variant_id"]: row for row in control}
    candidates = []
    for row in summary:
        control_row = control_by_variant.get(row["variant_id"], {})
        if row["methodology"] != "true_forward_replay":
            continue
        if row["outcome"] not in {"improved_positive_vs_baseline", "candidate_for_more_evidence", "lower_drawdown_but_lower_return"}:
            continue
        if control_row.get("damaged", 0) > control_row.get("improved", 0) + control_row.get("preserved", 0):
            continue
        if row["new_bad_trades"] > row["avoided_losers"]:
            continue
        candidates.append(row["variant_id"])
    return sorted(candidates)


def _rejected_variants(summary: Sequence[dict[str, Any]], candidates: Sequence[str]) -> list[str]:
    candidate_set = set(candidates)
    return sorted(row["variant_id"] for row in summary if row["variant_id"] not in candidate_set)


def _baseline_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario_count": len(rows),
        "trade_count": sum(int(row["trade_count"]) for row in rows),
        "positive_control_pocket_count": sum(1 for row in rows if row["positive_control_pocket"]),
        "net_pnl_sum_across_independent_scenarios": _fmt(sum((_dec(row["net_pnl"]) for row in rows), Decimal("0"))),
        "methodology": "sum across independent research scenarios",
    }


def _parity_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["status"] for row in rows)
    return {
        "scenario_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "all_variants_conclusion_eligible": counts.get("baseline_parity_failed", 0) == 0,
    }


def _large_loss_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_count": len(rows),
        "classification_counts": dict(sorted(Counter(row["classification"] for row in rows).items())),
        "late_exit_after_adverse_candle_count": sum(1 for row in rows if row["exit_late_relative_to_adverse_move"]),
        "stop_would_have_triggered_before_current_exit_count": sum(1 for row in rows if row["stop_would_have_triggered_before_current_exit"]),
        "recent_low_break_before_current_exit_count": sum(1 for row in rows if row["recent_low_break_before_current_exit"]),
        "ema10_or_sma20_break_before_current_exit_count": sum(1 for row in rows if row["ema10_or_sma20_break_before_current_exit"]),
    }


def _impact_by(rows: Sequence[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return [
        {
            field: key,
            "scenario_count": len(selected),
            "net_pnl_delta_sum": _fmt(sum((_dec(row["net_pnl_delta"]) for row in selected), Decimal("0"))),
            "trade_count_delta_sum": sum(int(row["trade_count"]) - int(row["baseline_trade_count"]) for row in selected),
        }
        for key, selected in sorted(grouped.items())
    ]


def _outcome(metrics: Any, canonical_metrics: dict[str, Any]) -> str:
    baseline_equity = _dec(canonical_metrics.get("ending_equity"))
    baseline_dd = _dec(canonical_metrics.get("mark_to_market_max_drawdown") or canonical_metrics.get("max_drawdown"))
    variant_dd = metrics.mark_to_market_max_drawdown or metrics.max_drawdown
    if metrics.ending_equity > baseline_equity and metrics.ending_equity > Decimal("10000"):
        return "improved_positive_vs_baseline"
    if metrics.ending_equity > baseline_equity and metrics.ending_equity <= Decimal("10000"):
        return "loss_reduced_but_still_below_starting_equity"
    if variant_dd < baseline_dd and metrics.ending_equity < baseline_equity:
        return "lower_drawdown_but_lower_return"
    if metrics.ending_equity > baseline_equity and variant_dd > baseline_dd:
        return "higher_return_but_higher_drawdown"
    if metrics.ending_equity < baseline_equity:
        return "deteriorated_vs_baseline"
    return "no_op"


def _rollup_outcome(rows: Sequence[dict[str, Any]]) -> str:
    outcomes = Counter(row["outcome"] for row in rows)
    if outcomes.get("deteriorated_vs_baseline", 0) > outcomes.get("improved_positive_vs_baseline", 0):
        return "deteriorated_vs_baseline"
    if outcomes.get("improved_positive_vs_baseline", 0):
        if outcomes.get("deteriorated_vs_baseline", 0) or outcomes.get("higher_return_but_higher_drawdown", 0):
            return "overfit_risk"
        return "candidate_for_more_evidence"
    if outcomes.get("loss_reduced_but_still_below_starting_equity", 0):
        return "loss_reduced_but_still_below_starting_equity"
    if outcomes.get("lower_drawdown_but_lower_return", 0):
        return "lower_drawdown_but_lower_return"
    return outcomes.most_common(1)[0][0] if outcomes else "insufficient_data"


def _variant_family(variant_id: str) -> str:
    return "entry_timing" if variant_id in ENTRY_VARIANTS else "stop_exit"


def _rejection_category(reason: str) -> str:
    if reason in {"rsi_not_constructive", "macd_not_constructive", "overextended_rsi", "entry_quality_not_constructive", "insufficient_history", "missing_indicator_field"}:
        return reason
    if "rsi" in reason:
        return "rsi_not_constructive"
    if "macd" in reason:
        return "macd_not_constructive"
    if "history" in reason:
        return "insufficient_history"
    if "missing" in reason or "indicator" in reason:
        return "missing_indicator_field"
    return "other"


def _avoided_loser_estimate(scenario: dict[str, Any], trades: Sequence[StrategyValidationTrade]) -> int:
    canonical_losses = sum(1 for trade in scenario.get("canonical_trades", []) if _dec(trade.get("net_pnl")) < 0)
    variant_losses = sum(1 for trade in trades if trade.net_pnl < 0)
    return max(canonical_losses - variant_losses, 0)


def _missed_winner_estimate(scenario: dict[str, Any], trades: Sequence[StrategyValidationTrade]) -> int:
    canonical_wins = sum(1 for trade in scenario.get("canonical_trades", []) if _dec(trade.get("net_pnl")) > 0)
    variant_wins = sum(1 for trade in trades if trade.net_pnl > 0)
    return max(canonical_wins - variant_wins, 0)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(Decimal("0.00000001"))


def _dec(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _fmt(value: Decimal | None) -> str:
    value = value or Decimal("0")
    return format(value.quantize(Decimal("0.00000001")).normalize(), "f")


def _canonical_timeframe(value: str) -> str:
    return "1d" if value in {"1D", "Timeframe.D1", "d1", "sleeve_1d"} else value.replace("Timeframe.", "").lower().replace("m15", "15m").replace("h1", "1h").replace("h4", "4h").replace("sleeve_", "")


def _methodology_description(label: str) -> str:
    return {
        "true_forward_replay": "Chronological replay over candles with position occupancy, fills, dynamic equity, fees, and slippage.",
        "completed_trade_overlay_estimate": "Diagnostic adjustment to completed baseline trades; not candidate evidence.",
        "lookahead_diagnostic_proxy": "Uses information unavailable at decision time; never candidate evidence.",
        "reporting_only_attribution": "Explains observed baseline trades without changing decisions.",
        "deferred_requires_rejected_signal_replay": "Needs rejected-signal replay before truthful testing.",
    }[label]


def sor_ev2_report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SOR-EV2 True-Forward Stop And Rejected-Signal Replay",
        "",
        f"Recorded at: `{report['generated_at']}`",
        "",
        f"Status: `{report['status']}`",
        "",
        "SOR-EV2 is evidence-only research. It uses canonical SV2.0.2 DB-imported pack paths as baseline references and persisted candle truth through the Strategy Validation replay path. Production Money Flow rules are unchanged, no order endpoints are called, no private/signed endpoints are called, and no variant is approved for production.",
        "",
        "## Executive Summary",
        "",
        f"- Canonical pack references inspected: `{len(report['baseline_evidence_references'])}`.",
        f"- Baseline parity status counts: `{report['baseline_parity_summary']['status_counts']}`.",
        f"- Candidate variants: `{', '.join(report['candidate_variants']) if report['candidate_variants'] else 'none'}`.",
        f"- Rejected/deferred variants: `{', '.join(report['rejected_variants'])}`.",
        "- Stop exits are generated by true-forward observed-candle signals and configured fill timing, not completed-trade overlays.",
        "- Dashboard date filters remain display-only and are not canonical evidence.",
        "",
        "## What SOR-EV1 Found",
        "",
        "SOR-EV1 found that large losses clustered around `late_extension_entry`, large adverse moves, 1d/4h losses, and `ma_alignment_break` exits. It promoted no variant because fixed-stop work was only a completed-trade overlay estimate.",
        "",
        "## Baseline Parity Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in report["baseline_parity_summary"]["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend([
        "",
        "## True-Forward Stop Results",
        "",
        "| Variant | Outcome | Scenarios | Net PnL Delta Sum | Stop Exits | Avoided Losers | Missed Winners | New Bad Trades |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in report["stop_variant_results"]:
        lines.append(f"| `{row['variant_id']}` | `{row['outcome']}` | {row['scenario_count']} | {row['net_pnl_delta_sum_across_independent_scenarios']} | {row['stop_exits']} | {row['avoided_losers']} | {row['missed_winners']} | {row['new_bad_trades']} |")
    lines.extend([
        "",
        "## True-Forward Entry Results",
        "",
        "| Variant | Outcome | Scenarios | Net PnL Delta Sum | Admitted From Rejections | New Bad Trades | Trade Count Delta |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["entry_variant_results"]:
        admitted = sum(item.get("variant_admitted_from_rejections", 0) for item in [])
        lines.append(f"| `{row['variant_id']}` | `{row['outcome']}` | {row['scenario_count']} | {row['net_pnl_delta_sum_across_independent_scenarios']} | n/a | {row['new_bad_trades']} | {row['trade_count_delta_sum']} |")
    lines.extend([
        "",
        "## Rejected-Signal Replay Findings",
        "",
        "| Category | Baseline Rejections | Variant Admissions |",
        "|---|---:|---:|",
    ])
    cats = sorted(set(report["rejected_signal_replay_summary"].get("baseline_rejection_counts", {})) | set(report["rejected_signal_replay_summary"].get("variant_admitted_from_rejection_counts", {})))
    for cat in cats:
        lines.append(f"| `{cat}` | {report['rejected_signal_replay_summary']['baseline_rejection_counts'].get(cat, 0)} | {report['rejected_signal_replay_summary']['variant_admitted_from_rejection_counts'].get(cat, 0)} |")
    lines.extend([
        "",
        "## Large Red Candle / Adverse Move Findings",
        "",
        f"- Large-loss samples with candle context: `{report['large_loss_candle_context_summary']['sample_count']}`.",
        f"- Classification counts: `{report['large_loss_candle_context_summary']['classification_counts']}`.",
        f"- Late exit after adverse candle count: `{report['large_loss_candle_context_summary']['late_exit_after_adverse_candle_count']}`.",
        f"- Stop would have triggered before current exit count: `{report['large_loss_candle_context_summary']['stop_would_have_triggered_before_current_exit_count']}`.",
        "",
        "## Control-Pocket Impact",
        "",
        "| Variant | Controls | Improved | Preserved | Damaged | Drawdown Reduced |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["control_pocket_impact"]:
        lines.append(f"| `{row['variant_id']}` | {row['control_pocket_count']} | {row['improved']} | {row['preserved']} | {row['damaged']} | {row['drawdown_reduced']} |")
    lines.extend([
        "",
        "## Candidate Variants",
        "",
    ])
    if report["candidate_variants"]:
        lines.extend(f"- `{item}`" for item in report["candidate_variants"])
    else:
        lines.append("- None promoted from SOR-EV2.")
    lines.extend([
        "",
        "## Rejected Variants",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["rejected_variants"])
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["limitations"])
    lines.extend([
        "",
        "## Recommended Next Evidence Phase",
        "",
        "If the founder wants to continue, run a narrower SOR-EV3 on only the best true-forward candidates and require out-of-sample style date slices plus control-pocket preservation before any production-rule-change proposal. No production change should be made from SOR-EV2 alone.",
        "",
        "## Boundary Confirmation",
        "",
    ])
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(report["boundary_flags"].items()))
    return "\n".join(lines).rstrip() + "\n"


def write_sor_ev2_outputs(report: dict[str, Any], markdown_path: str | Path, json_path: str | Path) -> None:
    markdown = sor_ev2_report_to_markdown(report)
    lower = markdown.lower()
    for phrase in FORBIDDEN_REPORT_PHRASES:
        if phrase in lower:
            raise ValueError(f"forbidden proof/live approval language present: {phrase}")
    Path(markdown_path).write_text(markdown, encoding="utf-8")
    Path(json_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "ALL_VARIANTS",
    "build_sor_ev2_report",
    "build_sor_ev2_report_sync",
    "sor_ev2_report_to_markdown",
    "write_sor_ev2_outputs",
]
