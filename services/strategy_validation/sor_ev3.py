"""SOR-EV3 avoid-sideways/low-volatility true-forward drilldown.

This module is evidence-only research. It replays the founder-selected
``avoid_sideways_low_volatility`` family against canonical SV2.0.2 pack
references and persisted candle truth. It does not change production Money Flow
rules, create trading artifacts, or call exchange adapters.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence

from core.domain.enums import (
    DecisionAction,
    StrategyDecisionStatus,
    StrategyValidationFillTiming,
)
from core.domain.models import Candle, StrategyValidationTrade
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
)
from services.strategy_validation.sor_ev1 import (
    CANONICAL_SV202_TIMESTAMP,
    CANONICAL_SYMBOLS,
    CANONICAL_TIMEFRAMES,
    canonical_sv202_batch_report_paths,
)
from services.strategy_validation.sor_ev2 import (
    _assert_canonical_paths,
    _atr_by_index,
    _baseline_row,
    _dec,
    _fmt,
    _load_canonical_scenarios,
    _parity_row,
    _parity_summary,
    _ratio,
    _request_from_payload,
    _snapshot_features,
)

SOR_EV3_VARIANTS: tuple[str, ...] = (
    "avoid_low_atr_percentile_20",
    "avoid_low_atr_percentile_30",
    "avoid_flat_sma20_slope",
    "avoid_flat_ema10_slope",
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
    "avoid_macd_flat_chop",
    "avoid_sideways_low_volatility_conservative",
)

FEATURE_DEFINITIONS: list[dict[str, str]] = [
    {"feature": "atr_pct", "definition": "ATR14 divided by candle close."},
    {"feature": "atr_percentile_lookback_50", "definition": "Current ATR percentage percentile over the prior/current 50 closed candles."},
    {"feature": "atr_percentile_lookback_100", "definition": "Current ATR percentage percentile over the prior/current 100 closed candles."},
    {"feature": "candle_range_pct", "definition": "Current high-low range divided by close."},
    {"feature": "rolling_range_pct_20", "definition": "20-candle high-low range divided by close."},
    {"feature": "rolling_range_pct_50", "definition": "50-candle high-low range divided by close."},
    {"feature": "sma20_slope_pct", "definition": "SMA20 percentage change versus 10 closed candles earlier."},
    {"feature": "ema10_slope_pct", "definition": "EMA10 percentage change versus 10 closed candles earlier."},
    {"feature": "ema5_ema10_spread_pct", "definition": "EMA5 minus EMA10 divided by close."},
    {"feature": "ema10_sma20_spread_pct", "definition": "EMA10 minus SMA20 divided by close."},
    {"feature": "price_distance_from_sma20_pct", "definition": "Close minus SMA20 divided by SMA20."},
    {"feature": "high_low_range_20_pct", "definition": "Alias of the 20-candle high-low compression range."},
    {"feature": "close_range_position_20", "definition": "Close location inside the 20-candle high-low range, 0=low and 1=high."},
    {"feature": "macd_histogram_abs_pct", "definition": "Absolute MACD histogram divided by close."},
    {"feature": "macd_histogram_slope_pct", "definition": "MACD histogram change from prior candle divided by close."},
    {"feature": "macd_signal_spread_abs_pct", "definition": "Absolute MACD-signal spread divided by close."},
    {"feature": "many_crosses_ema10_sma20_lookback_20", "definition": "EMA10/SMA20 spread sign changes over the last 20 candles."},
    {"feature": "price_whipsaw_count_lookback_20", "definition": "Close crossing EMA10 count over the last 20 candles."},
    {"feature": "low_directional_progress_lookback_20", "definition": "20-candle net close progress divided by 20-candle range is below 0.2."},
]

FORBIDDEN_REPORT_PHRASES = (
    "proven",
    "optimal",
    "approved for live",
    "guaranteed",
    "ready for real trading",
    "production-approved",
)


def build_sor_ev3_report_sync(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        build_sor_ev3_report(
            batch_report_paths,
            generated_at=generated_at,
            max_scenarios=max_scenarios,
            backtest_service=backtest_service,
        )
    )


async def build_sor_ev3_report(
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
    blocked_entries: list[dict[str, Any]] = []
    concentration_rows: list[dict[str, Any]] = []
    limitations: set[str] = set()

    for scenario in scenarios:
        request = _request_from_payload(scenario["request"])
        try:
            baseline_report = await service.run_money_flow_backtest(request)
        except Exception as exc:  # pragma: no cover - integration guard.
            baseline_parity.append(_blocked_parity_row(scenario, exc))
            limitations.add("one_or_more_baseline_replays_blocked")
            continue
        component_report = baseline_report.component_reports[0]
        parity = _parity_row(scenario, component_report.metrics)
        baseline_parity.append(parity)
        baseline_rows.append(_baseline_row(scenario, component_report.metrics, component_report.trades, parity))
        candles = service._load_candles(request=request, timeframe=component_report.timeframe, end_at=request.end_at)
        snapshots = service._indicator_service._compute_snapshots(candles)
        feature_rows = _feature_rows(candles, snapshots)
        if parity["status"] == "baseline_parity_failed":
            limitations.add("variant_conclusions_blocked_for_failed_baseline_parity")
            continue
        for variant_id in SOR_EV3_VARIANTS:
            replay = await _run_variant_replay(
                service=service,
                request=request,
                scenario=scenario,
                variant_id=variant_id,
                preloaded_candles=candles,
                preloaded_snapshots=snapshots,
                precomputed_features=feature_rows,
            )
            variant_rows.append(replay["row"])
            blocked_entries.extend(replay["blocked_entries"])
            concentration_rows.append(replay["loss_concentration"])
            limitations.update(replay["limitations"])

    variant_summary = _variant_summary(variant_rows)
    control = _control_pocket_impact(variant_rows, baseline_rows)
    candidates = _candidate_variants(variant_summary, control, baseline_parity)
    _apply_founder_review_labels(variant_summary, control, baseline_parity)
    not_promoted = sorted(row["variant_id"] for row in variant_summary if row["variant_id"] not in set(candidates))
    promising = sorted(row["variant_id"] for row in variant_summary if str(row.get("founder_review_label", "")).startswith("promising_"))
    rejected = sorted(row["variant_id"] for row in variant_summary if str(row.get("founder_review_label", "")).startswith("rejected_"))
    report = {
        "phase": "SOR-EV3",
        "generated_at": generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "avoid_sideways_low_volatility_true_forward_replay_ready_for_founder_review",
        "founder_selected_candidate_family": "avoid_sideways_low_volatility",
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
            "open_position_handling": "force_close_at_dataset_end",
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
        "regime_feature_definitions": FEATURE_DEFINITIONS,
        "variant_definitions": _variant_definitions(),
        "variant_results": variant_rows,
        "variant_summary": variant_summary,
        "blocked_entry_attribution": blocked_entries[:250],
        "blocked_entry_summary": _blocked_entry_summary(blocked_entries),
        "loss_concentration_summary": _loss_concentration_summary(concentration_rows),
        "control_pocket_impact": control,
        "candidate_variants": candidates,
        "promising_variants": promising,
        "not_promoted_variants": not_promoted,
        "rejected_variants": rejected,
        "variant_label_counts": dict(Counter(str(row.get("founder_review_label", "unlabeled")) for row in variant_summary)),
        "candidate_gate_policy": {
            "candidate_requires_true_forward_replay": True,
            "candidate_requires_positive_aggregate_net_pnl_delta": True,
            "candidate_requires_no_worst_drawdown_worsening": True,
            "candidate_requires_avoided_losers_at_least_missed_winners": True,
            "candidate_requires_trade_count_reduction_pct_at_most": "55",
            "candidate_requires_no_damaged_control_pockets": True,
            "promising_label_is_not_production_approval": True,
        },
        "limitations": sorted(limitations | {
            "independent_scenarios_are_not_one_combined_account",
            "dashboard_date_filters_are_display_only_not_canonical_evidence",
            "no_variant_is_production_approved",
            "sor_ev3_tests_only_founder_selected_sideways_low_volatility_family",
        }),
        "boundary_flags": {
            "uses_only_canonical_sv2_0_2_pack_paths": True,
            "uses_dashboard_date_filter_recalculation": False,
            "uses_dashboard_chart_data_as_canonical_evidence": False,
            "uses_hyperliquid_testnet_prices": False,
            "changes_production_money_flow_rules": False,
            "optimizes_parameters_blindly": False,
            "broad_parameter_grid_search": False,
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
    request: Any,
    scenario: dict[str, Any],
    variant_id: str,
    preloaded_candles: list[Candle],
    preloaded_snapshots: Sequence[Any],
    precomputed_features: Sequence[dict[str, Any]],
    include_replay_payload: bool = False,
) -> dict[str, Any]:
    sleeve = service._requested_sleeves(request.component_keys)[0]
    start_at = _coerce_utc(request.start_at)
    end_at = _coerce_utc(request.end_at)
    candles = preloaded_candles
    snapshots = preloaded_snapshots
    feature_rows = precomputed_features
    data_coverage = _data_coverage(candles, timeframe=sleeve.timeframe, start_at=start_at, end_at=end_at)
    regime_by_close_time = _label_candle_regimes(candles)
    feature_by_close_time = {_coerce_utc(row["close_time"]): row for row in feature_rows if row.get("close_time")}
    trades: list[StrategyValidationTrade] = []
    no_trade: Counter[str] = Counter()
    invalid: Counter[str] = Counter()
    limitations: set[str] = set(data_coverage.warning_reason_codes)
    open_position: Any | None = None
    realized_equity = request.assumptions.initial_capital
    closed_points = [request.assumptions.initial_capital]
    mtm_points = [request.assumptions.initial_capital]
    blocked_entries: list[dict[str, Any]] = []
    trades_skipped_due_to_insufficient_equity = 0

    for signal_index, (candle, snapshot) in enumerate(zip(candles, snapshots, strict=False)):
        close_time = _coerce_utc(candle.close_time)
        if close_time <= start_at or close_time > end_at:
            continue
        regime = regime_by_close_time.get(close_time, _CandleRegime.unknown(close_time))
        features = feature_rows[signal_index] if signal_index < len(feature_rows) else {"reason_codes": ["feature_unavailable_insufficient_history"]}
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

        if open_position is not None:
            if close_time > open_position.entry_time:
                open_position.record_excursion(candle)
                mtm_points.append(open_position.mark_to_market_equity(realized_equity, candle.low))
            if close_time <= open_position.entry_time:
                continue
            should_close = decision.action in {DecisionAction.CLOSE, DecisionAction.REDUCE}
            if should_close:
                if decision.action == DecisionAction.REDUCE:
                    limitations.add("reduce_actions_are_simulated_as_full_exits_for_sor_ev3")
                fill = _resolve_fill(candles=candles, signal_index=signal_index, fill_timing=request.assumptions.fill_timing)
                if fill is None:
                    limitations.add(f"exit_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}")
                    continue
                if request.assumptions.fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_CLOSE:
                    open_position.record_excursion(fill.candle)
                    mtm_points.append(open_position.mark_to_market_equity(realized_equity, fill.candle.low))
                trade = _close_trade(
                    request=request,
                    open_position=open_position,
                    fill=fill,
                    exit_signal_time=close_time,
                    exit_reason=decision.reason_code or decision.action.value,
                    exit_evaluation_key=(decision.evaluation_key or "sor_ev3") + f":{variant_id}:production_exit",
                    exit_market_regime=regime.trend_label,
                    exit_volatility_regime=regime.volatility_label,
                    forced_exit=False,
                )
                trades.append(trade)
                realized_equity = _money(realized_equity + trade.net_pnl)
                closed_points.append(realized_equity)
                mtm_points.append(realized_equity)
                open_position = None
            continue

        if decision.status == StrategyDecisionStatus.INVALID:
            invalid[decision.reason_code or "invalid_without_reason"] += 1
            continue
        if decision.status == StrategyDecisionStatus.NO_TRADE:
            no_trade[decision.reason_code or "no_trade_without_reason"] += 1
            continue

        block_reasons = _variant_block_reasons(variant_id, features)
        if decision.action == DecisionAction.OPEN and block_reasons:
            no_trade[f"{variant_id}_blocked_baseline_entry"] += 1
            blocked_entries.append(_blocked_entry_row(
                scenario=scenario,
                variant_id=variant_id,
                close_time=close_time,
                decision_reason=decision.reason_code or "open_without_reason",
                block_reasons=block_reasons,
                features=features,
                canonical_trade=_find_canonical_trade_for_signal(scenario, close_time),
            ))
            continue

        if decision.action == DecisionAction.OPEN:
            if _dynamic_equity_is_depleted(request.assumptions, realized_equity):
                invalid["dynamic_equity_depleted"] += 1
                trades_skipped_due_to_insufficient_equity += 1
                limitations.add("dynamic_equity_depleted_no_new_trades_opened")
                continue
            fill = _resolve_fill(candles=candles, signal_index=signal_index, fill_timing=request.assumptions.fill_timing)
            if fill is None:
                limitations.add(f"open_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}")
                continue
            open_position = _open_trade(
                request=request,
                sleeve=sleeve,
                fill=fill,
                entry_signal_time=close_time,
                entry_reason=decision.reason_code,
                entry_evaluation_key=(decision.evaluation_key or "sor_ev3") + f":{variant_id}",
                entry_market_regime=regime.trend_label,
                entry_volatility_regime=regime.volatility_label,
                current_realized_equity=realized_equity,
            )
            if _coerce_utc(fill.candle.close_time) > open_position.entry_time:
                open_position.record_excursion(fill.candle)
                mtm_points.append(open_position.mark_to_market_equity(realized_equity, fill.candle.low))

    if open_position is not None and request.assumptions.force_close_open_trade_at_end:
        last_candle = _last_candle_in_window(candles, start_at=start_at, end_at=end_at)
        if last_candle is not None:
            open_position.record_excursion(last_candle)
            mtm_points.append(open_position.mark_to_market_equity(realized_equity, last_candle.low))
            fill = _ResolvedFill(candle=last_candle, raw_price=last_candle.close, time=_coerce_utc(last_candle.close_time), source="end_of_window_close")
            close_time = _coerce_utc(last_candle.close_time)
            trade = _close_trade(
                request=request,
                open_position=open_position,
                fill=fill,
                exit_signal_time=close_time,
                exit_reason="end_of_window_forced_close",
                exit_evaluation_key=f"{open_position.entry_evaluation_key}:forced_exit",
                exit_market_regime=regime_by_close_time.get(close_time, _CandleRegime.unknown(close_time)).trend_label,
                exit_volatility_regime=regime_by_close_time.get(close_time, _CandleRegime.unknown(close_time)).volatility_label,
                forced_exit=True,
            )
            trades.append(trade)
            realized_equity = _money(realized_equity + trade.net_pnl)
            closed_points.append(realized_equity)
            mtm_points.append(realized_equity)
            limitations.add("open_positions_are_force_closed_at_window_end_for_sor_ev3")

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
    baseline_dd = _dec(canonical_metrics.get("mark_to_market_max_drawdown") or canonical_metrics.get("max_drawdown"))
    baseline_largest_loss = _dec(canonical_metrics.get("worst_trade_net_pnl"))
    row = {
        "variant_id": variant_id,
        "variant_family": "avoid_sideways_low_volatility",
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
        "baseline_max_drawdown": _fmt(baseline_dd),
        "variant_max_drawdown": _fmt(metrics.mark_to_market_max_drawdown or metrics.max_drawdown),
        "max_drawdown_delta": _fmt((metrics.mark_to_market_max_drawdown or metrics.max_drawdown) - baseline_dd),
        "baseline_largest_loss": _fmt(baseline_largest_loss),
        "variant_largest_loss": _fmt(metrics.worst_trade_net_pnl or Decimal("0")),
        "largest_loss_delta": _fmt((metrics.worst_trade_net_pnl or Decimal("0")) - baseline_largest_loss),
        "baseline_trade_count": int(_dec(canonical_metrics.get("number_of_trades"))),
        "trade_count": metrics.number_of_trades,
        "trade_count_delta": metrics.number_of_trades - int(_dec(canonical_metrics.get("number_of_trades"))),
        "win_rate": _fmt(metrics.win_rate or Decimal("0")),
        "profit_factor": _fmt(metrics.profit_factor or Decimal("0")),
        "average_win": _fmt(metrics.average_win or Decimal("0")),
        "average_loss": _fmt(metrics.average_loss or Decimal("0")),
        "largest_loss": _fmt(metrics.worst_trade_net_pnl or Decimal("0")),
        "largest_win": _fmt(metrics.best_trade_net_pnl or Decimal("0")),
        "total_fees": _fmt(metrics.total_fees),
        "total_slippage": _fmt(metrics.total_slippage_cost),
        "max_adverse_excursion": _fmt(max((abs(trade.max_adverse_excursion or Decimal("0")) for trade in trades), default=Decimal("0"))),
        "blocked_open_signals": len(blocked_entries),
        "blocked_entries": sum(1 for row in blocked_entries if row.get("baseline_trade_id")),
        "avoided_losers": sum(1 for row in blocked_entries if row["baseline_trade_would_have_been"] == "loser"),
        "missed_winners": sum(1 for row in blocked_entries if row["baseline_trade_would_have_been"] == "winner"),
        "new_bad_trades": 0,
        "outcome": _outcome(metrics.ending_equity, metrics.mark_to_market_max_drawdown or metrics.max_drawdown, baseline_ending, baseline_dd),
        "candidate_evidence": False,
        "production_approved": False,
        "limitations": sorted(limitations),
    }
    result: dict[str, Any] = {
        "row": row,
        "blocked_entries": blocked_entries,
        "loss_concentration": _loss_concentration_row(
            scenario=scenario,
            variant_id=variant_id,
            feature_by_close_time=feature_by_close_time,
            variant_trades=trades,
        ),
        "limitations": sorted(limitations),
    }
    if include_replay_payload:
        result.update(
            {
                "trades": trades,
                "metrics": metrics,
                "no_trade_reason_counts": dict(sorted(no_trade.items())),
                "invalid_reason_counts": dict(sorted(invalid.items())),
                "closed_trade_equity_points": closed_points,
                "mark_to_market_equity_points": mtm_points,
            }
        )
    return result


def _feature_rows(candles: Sequence[Candle], snapshots: Sequence[Any]) -> list[dict[str, Any]]:
    atr = _atr_by_index(candles)
    atr_pct_by_index = {
        idx: _ratio(value, candles[idx].close)
        for idx, value in atr.items()
        if idx < len(candles) and candles[idx].close
    }
    output: list[dict[str, Any]] = []
    for idx, candle in enumerate(candles):
        snapshot = snapshots[idx] if idx < len(snapshots) else None
        sleeve = type("Sleeve", (), {"max_extension_pct_above_ema5": Decimal("1")})()
        base = _snapshot_features(snapshot, candle, sleeve)
        reasons: list[str] = []
        if not base.get("indicators_valid"):
            reasons.append("invalid_indicator_snapshot")
        close = candle.close
        row: dict[str, Any] = {
            "close_time": _coerce_utc(candle.close_time),
            "reason_codes": reasons,
            "atr_pct": atr_pct_by_index.get(idx),
            "atr_percentile_lookback_50": _percentile_at(idx, atr_pct_by_index, 50),
            "atr_percentile_lookback_100": _percentile_at(idx, atr_pct_by_index, 100),
            "candle_range_pct": _ratio(candle.high - candle.low, close),
            "rolling_range_pct_20": _rolling_range_pct(candles, idx, 20),
            "rolling_range_pct_50": _rolling_range_pct(candles, idx, 50),
            "high_low_range_20_pct": _rolling_range_pct(candles, idx, 20),
            "close_range_position_20": _close_range_position(candles, idx, 20),
        }
        if not row["atr_percentile_lookback_50"]:
            reasons.append("feature_unavailable_insufficient_history:atr_percentile_lookback_50")
        if not row["atr_percentile_lookback_100"]:
            reasons.append("feature_unavailable_insufficient_history:atr_percentile_lookback_100")
        for lookback_key in ("rolling_range_pct_20", "rolling_range_pct_50", "close_range_position_20"):
            if row[lookback_key] is None:
                reasons.append(f"feature_unavailable_insufficient_history:{lookback_key}")
        if base.get("indicators_valid"):
            row.update({
                "sma20_slope_pct": _indicator_slope_pct(snapshots, idx, "sma_20", 10),
                "ema10_slope_pct": _indicator_slope_pct(snapshots, idx, "ema_10", 10),
                "ema5_ema10_spread_pct": _ratio(base["ema5"] - base["ema10"], close),
                "ema10_sma20_spread_pct": _ratio(base["ema10"] - base["sma20"], close),
                "price_distance_from_sma20_pct": _ratio(close - base["sma20"], base["sma20"]),
                "macd_histogram_abs_pct": _ratio(abs(base["macd_histogram"]), close),
                "macd_histogram_slope_pct": _macd_histogram_slope_pct(snapshots, idx, close),
                "macd_signal_spread_abs_pct": _ratio(abs(base["macd"] - base["macd_signal"]), close),
                "many_crosses_ema10_sma20_lookback_20": _ema_spread_crosses(snapshots, idx, 20),
                "price_whipsaw_count_lookback_20": _price_whipsaws(candles, snapshots, idx, 20),
                "low_directional_progress_lookback_20": _low_directional_progress(candles, idx, 20),
            })
        else:
            row.update({
                "sma20_slope_pct": None,
                "ema10_slope_pct": None,
                "ema5_ema10_spread_pct": None,
                "ema10_sma20_spread_pct": None,
                "price_distance_from_sma20_pct": None,
                "macd_histogram_abs_pct": None,
                "macd_histogram_slope_pct": None,
                "macd_signal_spread_abs_pct": None,
                "many_crosses_ema10_sma20_lookback_20": None,
                "price_whipsaw_count_lookback_20": None,
                "low_directional_progress_lookback_20": None,
            })
        for key in ("sma20_slope_pct", "ema10_slope_pct", "macd_histogram_slope_pct"):
            if row[key] is None:
                reasons.append(f"feature_unavailable_insufficient_history:{key}")
        output.append(row)
    return output


def _variant_block_reasons(variant_id: str, features: dict[str, Any]) -> list[str]:
    if variant_id == "avoid_low_atr_percentile_20":
        value = features.get("atr_percentile_lookback_100")
        return ["blocked_low_atr_percentile"] if isinstance(value, Decimal) and value <= Decimal("20") else []
    if variant_id == "avoid_low_atr_percentile_30":
        value = features.get("atr_percentile_lookback_100")
        return ["blocked_low_atr_percentile"] if isinstance(value, Decimal) and value <= Decimal("30") else []
    if variant_id == "avoid_flat_sma20_slope":
        value = features.get("sma20_slope_pct")
        return ["blocked_flat_sma20_slope"] if isinstance(value, Decimal) and abs(value) <= Decimal("0.0025") else []
    if variant_id == "avoid_flat_ema10_slope":
        value = features.get("ema10_slope_pct")
        return ["blocked_flat_ema10_slope"] if isinstance(value, Decimal) and abs(value) <= Decimal("0.002") else []
    if variant_id == "avoid_low_rolling_range_20":
        value = features.get("rolling_range_pct_20")
        return ["blocked_low_rolling_range"] if isinstance(value, Decimal) and value <= Decimal("0.025") else []
    if variant_id == "avoid_low_rolling_range_50":
        value = features.get("rolling_range_pct_50")
        return ["blocked_low_rolling_range"] if isinstance(value, Decimal) and value <= Decimal("0.05") else []
    if variant_id == "avoid_macd_flat_chop":
        hist = features.get("macd_histogram_abs_pct")
        slope = features.get("macd_histogram_slope_pct")
        spread = features.get("macd_signal_spread_abs_pct")
        if all(isinstance(value, Decimal) for value in (hist, slope, spread)):
            if hist <= Decimal("0.00005") and abs(slope) <= Decimal("0.00003") and spread <= Decimal("0.00008"):
                return ["blocked_macd_flat_chop"]
        return []
    if variant_id == "avoid_sideways_low_volatility_conservative":
        reasons: list[str] = []
        atr = features.get("atr_percentile_lookback_100")
        sma = features.get("sma20_slope_pct")
        ema = features.get("ema10_slope_pct")
        range20 = features.get("rolling_range_pct_20")
        hist = features.get("macd_histogram_abs_pct")
        slope = features.get("macd_histogram_slope_pct")
        if isinstance(atr, Decimal) and atr <= Decimal("30"):
            reasons.append("blocked_low_atr_percentile")
        if (isinstance(sma, Decimal) and abs(sma) <= Decimal("0.0025")) or (isinstance(ema, Decimal) and abs(ema) <= Decimal("0.002")):
            reasons.append("blocked_flat_sma20_slope" if isinstance(sma, Decimal) and abs(sma) <= Decimal("0.0025") else "blocked_flat_ema10_slope")
        if isinstance(range20, Decimal) and range20 <= Decimal("0.035"):
            reasons.append("blocked_low_rolling_range")
        if isinstance(hist, Decimal) and isinstance(slope, Decimal) and hist <= Decimal("0.00006") and abs(slope) <= Decimal("0.00004"):
            reasons.append("blocked_macd_flat_chop")
        return ["blocked_combined_sideways_low_volatility", *reasons] if len(set(reasons)) >= 2 else []
    return []


def _blocked_entry_row(
    *,
    scenario: dict[str, Any],
    variant_id: str,
    close_time: datetime,
    decision_reason: str,
    block_reasons: Sequence[str],
    features: dict[str, Any],
    canonical_trade: dict[str, Any] | None,
) -> dict[str, Any]:
    pnl = _dec(canonical_trade.get("net_pnl")) if canonical_trade else Decimal("0")
    winner_loser = "winner" if pnl > 0 else "loser" if pnl < 0 else "unknown"
    return {
        "variant_id": variant_id,
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "fill_assumption": scenario["fill_timing"],
        "candle_time": close_time.isoformat(),
        "baseline_would_enter_reason": decision_reason,
        "variant_block_reason": list(block_reasons),
        "regime_feature_values": _compact_features(features),
        "baseline_trade_id": canonical_trade.get("trade_id") if canonical_trade else None,
        "baseline_trade_would_have_been": winner_loser,
        "net_pnl_of_blocked_baseline_trade": _fmt(pnl),
        "block_avoided_loser": winner_loser == "loser",
        "block_missed_winner": winner_loser == "winner",
        "block_reduced_large_loss": pnl <= Decimal("-500"),
        "block_damaged_control_pocket": bool(canonical_trade and winner_loser == "winner" and _is_control_scenario(scenario)),
        "methodology": "true_forward_replay",
    }


def _find_canonical_trade_for_signal(scenario: dict[str, Any], close_time: datetime) -> dict[str, Any] | None:
    for trade in scenario.get("canonical_trades", []):
        if _parse_time(trade.get("entry_signal_time")) == close_time:
            return trade
    return None


def _loss_concentration_row(
    *,
    scenario: dict[str, Any],
    variant_id: str,
    feature_by_close_time: dict[datetime, dict[str, Any]],
    variant_trades: Sequence[StrategyValidationTrade],
) -> dict[str, Any]:
    baseline = _concentration_counts(
        trades=scenario.get("canonical_trades", []),
        variant_id=variant_id,
        feature_by_close_time=feature_by_close_time,
        accessor=lambda trade, field: trade.get(field),
        pnl_getter=lambda trade: _dec(trade.get("net_pnl")),
    )
    after = _concentration_counts(
        trades=variant_trades,
        variant_id=variant_id,
        feature_by_close_time=feature_by_close_time,
        accessor=lambda trade, field: getattr(trade, field),
        pnl_getter=lambda trade: trade.net_pnl,
    )
    return {
        "variant_id": variant_id,
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "fill_timing": scenario["fill_timing"],
        "baseline": baseline,
        "after_variant": after,
    }


def _concentration_counts(
    *,
    trades: Sequence[Any],
    variant_id: str,
    feature_by_close_time: dict[datetime, dict[str, Any]],
    accessor: Any,
    pnl_getter: Any,
) -> dict[str, Any]:
    losing = winning = flagged_losing = flagged_winning = 0
    flagged_loss_sum = Decimal("0")
    flagged_win_sum = Decimal("0")
    largest_flagged_loss = Decimal("0")
    for trade in trades:
        pnl = pnl_getter(trade)
        signal_time = _parse_time(accessor(trade, "entry_signal_time"))
        features = feature_by_close_time.get(signal_time)
        flagged = bool(features and _variant_block_reasons(variant_id, features))
        if pnl < 0:
            losing += 1
            if flagged:
                flagged_losing += 1
                flagged_loss_sum += pnl
                largest_flagged_loss = min(largest_flagged_loss, pnl)
        elif pnl > 0:
            winning += 1
            if flagged:
                flagged_winning += 1
                flagged_win_sum += pnl
    return {
        "losing_trades": losing,
        "winning_trades": winning,
        "flagged_losing_trades": flagged_losing,
        "flagged_winning_trades": flagged_winning,
        "percent_losing_trades_flagged": _pct(flagged_losing, losing),
        "percent_winning_trades_flagged": _pct(flagged_winning, winning),
        "average_loss_in_flagged_regime": _fmt(flagged_loss_sum / Decimal(flagged_losing)) if flagged_losing else "0",
        "average_win_in_flagged_regime": _fmt(flagged_win_sum / Decimal(flagged_winning)) if flagged_winning else "0",
        "largest_loss_in_flagged_regime": _fmt(largest_flagged_loss),
    }


def _variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant_id"]].append(row)
    output: list[dict[str, Any]] = []
    for variant_id, selected in sorted(grouped.items()):
        baseline_trade_count = sum(int(row["baseline_trade_count"]) for row in selected)
        blocked = sum(int(row["blocked_entries"]) for row in selected)
        blocked_open_signals = sum(int(row["blocked_open_signals"]) for row in selected)
        trade_count_delta = sum(int(row["trade_count_delta"]) for row in selected)
        output.append({
            "variant_id": variant_id,
            "variant_family": "avoid_sideways_low_volatility",
            "methodology": "true_forward_replay",
            "scenario_count": len(selected),
            "outcome_taxonomy": _rollup_outcome(selected, baseline_trade_count, blocked),
            "candidate": False,
            "rejected": True,
            "production_approved": False,
            "ending_equity_delta_sum_across_independent_scenarios": _fmt(sum((_dec(row["variant_ending_equity"]) - _dec(row["baseline_ending_equity"]) for row in selected), Decimal("0"))),
            "net_pnl_delta_sum_across_independent_scenarios": _fmt(sum((_dec(row["net_pnl_delta"]) for row in selected), Decimal("0"))),
            "max_drawdown_delta_worst": _fmt(max((_dec(row["max_drawdown_delta"]) for row in selected), default=Decimal("0"))),
            "largest_loss_delta_best": _fmt(max((_dec(row["largest_loss_delta"]) for row in selected), default=Decimal("0"))),
            "trade_count_delta_sum": trade_count_delta,
            "baseline_trade_count": baseline_trade_count,
            "blocked_open_signals": blocked_open_signals,
            "blocked_entries": blocked,
            "trade_count_reduction_pct": _pct(abs(min(trade_count_delta, 0)), baseline_trade_count),
            "avoided_losers": sum(int(row["avoided_losers"]) for row in selected),
            "missed_winners": sum(int(row["missed_winners"]) for row in selected),
            "new_bad_trades": sum(int(row["new_bad_trades"]) for row in selected),
            "per_symbol_impact": _impact_by(selected, "symbol"),
            "per_timeframe_impact": _impact_by(selected, "timeframe"),
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
            "return_reduced": damaged,
            "drawdown_reduced": dd_reduced,
            "trade_count_reduced_too_much": sum(1 for row in selected if int(row["baseline_trade_count"]) and abs(int(row["trade_count_delta"])) / int(row["baseline_trade_count"]) > 0.5),
            "notes": "control pockets include ETH 1h and positive baseline scenarios",
        })
    return output


def _candidate_variants(summary: Sequence[dict[str, Any]], control: Sequence[dict[str, Any]], parity: Sequence[dict[str, Any]]) -> list[str]:
    if any(row["status"] == "baseline_parity_failed" for row in parity):
        return []
    control_by_variant = {row["variant_id"]: row for row in control}
    candidates: list[str] = []
    for row in summary:
        controls = control_by_variant.get(row["variant_id"], {})
        if row["methodology"] != "true_forward_replay":
            continue
        if _dec(row["net_pnl_delta_sum_across_independent_scenarios"]) <= 0:
            continue
        if _dec(row["max_drawdown_delta_worst"]) > 0:
            continue
        if int(row["missed_winners"]) > int(row["avoided_losers"]):
            continue
        if Decimal(str(row["trade_count_reduction_pct"])) > Decimal("55"):
            continue
        if int(controls.get("damaged", 0)) > 0:
            continue
        candidates.append(row["variant_id"])
    for row in summary:
        if row["variant_id"] in candidates:
            row["candidate"] = True
            row["rejected"] = False
            row["outcome_taxonomy"] = "candidate_for_more_evidence"
    return sorted(candidates)


def _apply_founder_review_labels(summary: Sequence[dict[str, Any]], control: Sequence[dict[str, Any]], parity: Sequence[dict[str, Any]]) -> None:
    baseline_failed = any(row["status"] == "baseline_parity_failed" for row in parity)
    control_by_variant = {row["variant_id"]: row for row in control}
    for row in summary:
        controls = control_by_variant.get(row["variant_id"], {})
        blockers = _promotion_blockers(row, controls, baseline_failed)
        label = _founder_review_label(row, controls, blockers)
        row["promotion_blockers"] = blockers
        row["founder_review_label"] = label
        row["promotion_status"] = (
            "candidate_for_more_evidence"
            if row.get("candidate")
            else "promising_not_promoted"
            if label.startswith("promising_")
            else "not_promoted"
        )
        row["rejected"] = label.startswith("rejected_")
        row["review_explanation"] = _founder_review_explanation(label, row, controls)


def _promotion_blockers(row: dict[str, Any], controls: dict[str, Any], baseline_failed: bool) -> list[str]:
    blockers: list[str] = []
    if baseline_failed:
        blockers.append("baseline_parity_failed")
    if row.get("methodology") != "true_forward_replay":
        blockers.append("methodology_not_true_forward_replay")
    if _dec(row["net_pnl_delta_sum_across_independent_scenarios"]) <= 0:
        blockers.append("aggregate_net_pnl_delta_not_positive")
    if _dec(row["max_drawdown_delta_worst"]) > 0:
        blockers.append("worst_drawdown_worsened")
    if int(row["missed_winners"]) > int(row["avoided_losers"]):
        blockers.append("missed_winners_exceed_avoided_losers")
    if Decimal(str(row["trade_count_reduction_pct"])) > Decimal("55"):
        blockers.append("trade_count_reduction_above_55_pct")
    if int(controls.get("damaged", 0)) > 0:
        blockers.append("control_pockets_damaged")
    return blockers


def _founder_review_label(row: dict[str, Any], controls: dict[str, Any], blockers: Sequence[str]) -> str:
    if row.get("candidate"):
        return "candidate_for_more_evidence"
    net_delta = _dec(row["net_pnl_delta_sum_across_independent_scenarios"])
    dd_delta = _dec(row["max_drawdown_delta_worst"])
    avoided = int(row["avoided_losers"])
    missed = int(row["missed_winners"])
    damaged = int(controls.get("damaged", 0))
    if net_delta <= 0:
        return "rejected_negative_aggregate"
    if Decimal(str(row["trade_count_reduction_pct"])) > Decimal("55"):
        return "rejected_overblocked_trade_count"
    if avoided < missed:
        return "rejected_missed_more_winners_than_losers"
    if damaged <= 2 and net_delta >= Decimal("50000"):
        return "promising_high_pnl_control_risk"
    if damaged <= 2 and net_delta >= Decimal("25000"):
        return "promising_control_pocket_risk"
    if damaged > 2 and net_delta >= Decimal("10000"):
        return "mixed_positive_pnl_control_damage"
    if dd_delta > 0 and net_delta < Decimal("1000"):
        return "not_promoted_low_impact"
    return "not_promoted_mixed_result"


def _founder_review_explanation(label: str, row: dict[str, Any], controls: dict[str, Any]) -> str:
    if label == "candidate_for_more_evidence":
        return "Passes the strict SOR-EV3 candidate gate; still evidence-only and not production approved."
    if label == "promising_high_pnl_control_risk":
        return "Large aggregate PnL improvement and avoided-loser skew, but promotion is blocked because worst-scenario drawdown worsened and control pockets were damaged."
    if label == "promising_control_pocket_risk":
        return "Aggregate PnL and avoided-loser counts are directionally promising, but the result is not clean because drawdown worsened in at least one scenario and control pockets were damaged."
    if label == "mixed_positive_pnl_control_damage":
        return "Aggregate PnL improved, but too many strong baseline control pockets lost return, so this should not be promoted without a narrower follow-up."
    if label == "not_promoted_low_impact":
        return "The aggregate change was too small to justify more evidence despite avoiding more losers than winners."
    if label == "rejected_negative_aggregate":
        return "Aggregate PnL fell versus baseline, so this is a hard rejection for this evidence pass."
    if label == "rejected_overblocked_trade_count":
        return "The rule removed too many baseline trades to trust the result as a practical candidate."
    if label == "rejected_missed_more_winners_than_losers":
        return "The rule missed more winners than losers avoided."
    damaged = controls.get("damaged", 0)
    return f"Not promoted after strict evidence review; control pockets damaged: {damaged}."


def _blocked_entry_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_variant[row["variant_id"]].append(row)
    return {
        "total_blocked_open_signals": len(rows),
        "canonical_blocked_entries": sum(1 for row in rows if row.get("baseline_trade_id")),
        "by_variant": [
            {
                "variant_id": variant_id,
                "blocked_open_signals": len(selected),
                "blocked_entries": sum(1 for row in selected if row.get("baseline_trade_id")),
                "avoided_losers": sum(1 for row in selected if row["block_avoided_loser"]),
                "missed_winners": sum(1 for row in selected if row["block_missed_winner"]),
                "large_losses_reduced": sum(1 for row in selected if row["block_reduced_large_loss"]),
                "reason_counts": dict(Counter(reason for row in selected for reason in row["variant_block_reason"])),
            }
            for variant_id in SOR_EV3_VARIANTS
            for selected in [by_variant.get(variant_id, [])]
        ],
    }


def _loss_concentration_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant_id"]].append(row)
    output = []
    for variant_id, selected in sorted(grouped.items()):
        baseline_losing = sum(int(row["baseline"]["losing_trades"]) for row in selected)
        baseline_winning = sum(int(row["baseline"]["winning_trades"]) for row in selected)
        baseline_flagged_losing = sum(int(row["baseline"]["flagged_losing_trades"]) for row in selected)
        baseline_flagged_winning = sum(int(row["baseline"]["flagged_winning_trades"]) for row in selected)
        after_losing = sum(int(row["after_variant"]["losing_trades"]) for row in selected)
        after_winning = sum(int(row["after_variant"]["winning_trades"]) for row in selected)
        after_flagged_losing = sum(int(row["after_variant"]["flagged_losing_trades"]) for row in selected)
        after_flagged_winning = sum(int(row["after_variant"]["flagged_winning_trades"]) for row in selected)
        output.append({
            "variant_id": variant_id,
            "baseline_percent_losing_trades_flagged": _pct(baseline_flagged_losing, baseline_losing),
            "baseline_percent_winning_trades_flagged": _pct(baseline_flagged_winning, baseline_winning),
            "after_variant_percent_losing_trades_flagged": _pct(after_flagged_losing, after_losing),
            "after_variant_percent_winning_trades_flagged": _pct(after_flagged_winning, after_winning),
            "baseline_flagged_losing_trades": baseline_flagged_losing,
            "baseline_flagged_winning_trades": baseline_flagged_winning,
        })
    return output


def _baseline_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario_count": len(rows),
        "trade_count": sum(int(row["trade_count"]) for row in rows),
        "positive_control_pocket_count": sum(1 for row in rows if row["positive_control_pocket"]),
        "net_pnl_sum_across_independent_scenarios": _fmt(sum((_dec(row["net_pnl"]) for row in rows), Decimal("0"))),
        "methodology": "sum across independent research scenarios",
    }


def _variant_definitions() -> list[dict[str, Any]]:
    return [
        {"variant_id": "avoid_low_atr_percentile_20", "logic": "Block new long entries when ATR14 percent-of-price percentile over 100 candles is <= 20.", "reason_codes": ["blocked_low_atr_percentile"]},
        {"variant_id": "avoid_low_atr_percentile_30", "logic": "Block new long entries when ATR14 percent-of-price percentile over 100 candles is <= 30.", "reason_codes": ["blocked_low_atr_percentile"]},
        {"variant_id": "avoid_flat_sma20_slope", "logic": "Block new long entries when absolute SMA20 10-bar slope is <= 0.25%.", "reason_codes": ["blocked_flat_sma20_slope"]},
        {"variant_id": "avoid_flat_ema10_slope", "logic": "Block new long entries when absolute EMA10 10-bar slope is <= 0.20%.", "reason_codes": ["blocked_flat_ema10_slope"]},
        {"variant_id": "avoid_low_rolling_range_20", "logic": "Block new long entries when 20-candle high-low range is <= 2.5% of close.", "reason_codes": ["blocked_low_rolling_range"]},
        {"variant_id": "avoid_low_rolling_range_50", "logic": "Block new long entries when 50-candle high-low range is <= 5.0% of close.", "reason_codes": ["blocked_low_rolling_range"]},
        {"variant_id": "avoid_macd_flat_chop", "logic": "Block new long entries when MACD histogram and MACD-signal spread are both small relative to price.", "reason_codes": ["blocked_macd_flat_chop"]},
        {"variant_id": "avoid_sideways_low_volatility_conservative", "logic": "Block new long entries only when at least two independent low-vol/flat/compression/MACD-flat conditions agree.", "reason_codes": ["blocked_combined_sideways_low_volatility"]},
    ]


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


def _impact_by(rows: Sequence[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return [
        {
            field: key,
            "scenario_count": len(selected),
            "net_pnl_delta_sum": _fmt(sum((_dec(row["net_pnl_delta"]) for row in selected), Decimal("0"))),
            "trade_count_delta_sum": sum(int(row["trade_count_delta"]) for row in selected),
            "blocked_open_signals": sum(int(row["blocked_open_signals"]) for row in selected),
            "blocked_entries": sum(int(row["blocked_entries"]) for row in selected),
        }
        for key, selected in sorted(grouped.items())
    ]


def _outcome(variant_equity: Decimal, variant_dd: Decimal, baseline_equity: Decimal, baseline_dd: Decimal) -> str:
    if variant_equity > baseline_equity and variant_equity > Decimal("10000") and variant_dd <= baseline_dd:
        return "improved_positive_vs_baseline"
    if variant_equity > baseline_equity and variant_equity <= Decimal("10000"):
        return "loss_reduced_but_still_below_starting_equity"
    if variant_dd < baseline_dd and variant_equity < baseline_equity:
        return "lower_drawdown_but_lower_return"
    if variant_equity > baseline_equity and variant_dd > baseline_dd:
        return "higher_return_but_higher_drawdown"
    if variant_equity < baseline_equity:
        return "deteriorated_vs_baseline"
    return "no_op"


def _rollup_outcome(rows: Sequence[dict[str, Any]], baseline_trade_count: int, blocked_entries: int) -> str:
    if baseline_trade_count and Decimal(blocked_entries) / Decimal(baseline_trade_count) > Decimal("0.6"):
        return "trade_count_reduced_too_much"
    outcomes = Counter(row["outcome"] for row in rows)
    if outcomes.get("deteriorated_vs_baseline", 0) > outcomes.get("improved_positive_vs_baseline", 0):
        return "deteriorated_vs_baseline"
    if outcomes.get("higher_return_but_higher_drawdown", 0):
        return "higher_return_but_higher_drawdown"
    if outcomes.get("improved_positive_vs_baseline", 0) and outcomes.get("deteriorated_vs_baseline", 0):
        return "overfit_risk"
    if outcomes.get("improved_positive_vs_baseline", 0):
        return "candidate_for_more_evidence"
    if outcomes.get("loss_reduced_but_still_below_starting_equity", 0):
        return "loss_reduced_but_still_below_starting_equity"
    if outcomes.get("lower_drawdown_but_lower_return", 0):
        return "lower_drawdown_but_lower_return"
    return outcomes.most_common(1)[0][0] if outcomes else "insufficient_data"


def _is_control_scenario(scenario: dict[str, Any]) -> bool:
    metrics = scenario.get("metrics", {})
    return _dec(metrics.get("ending_equity")) > Decimal("10000") or (scenario["symbol"] == "ETH" and scenario["timeframe"] == "1h")


def _compact_features(features: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "atr_pct",
        "atr_percentile_lookback_50",
        "atr_percentile_lookback_100",
        "sma20_slope_pct",
        "ema10_slope_pct",
        "rolling_range_pct_20",
        "rolling_range_pct_50",
        "macd_histogram_abs_pct",
        "macd_histogram_slope_pct",
        "macd_signal_spread_abs_pct",
        "many_crosses_ema10_sma20_lookback_20",
        "price_whipsaw_count_lookback_20",
        "low_directional_progress_lookback_20",
        "reason_codes",
    ]
    return {key: features.get(key) for key in keys}


def _percentile_at(idx: int, values_by_index: dict[int, Decimal | None], lookback: int) -> Decimal | None:
    window = [values_by_index.get(i) for i in range(idx - lookback + 1, idx + 1)]
    values = [value for value in window if isinstance(value, Decimal)]
    current = values_by_index.get(idx)
    if not isinstance(current, Decimal) or len(values) < lookback:
        return None
    rank = sum(1 for value in values if value <= current)
    return (Decimal(rank) / Decimal(len(values)) * Decimal("100")).quantize(Decimal("0.00000001"))


def _rolling_range_pct(candles: Sequence[Candle], idx: int, lookback: int) -> Decimal | None:
    if idx + 1 < lookback:
        return None
    window = candles[idx - lookback + 1:idx + 1]
    return _ratio(max(candle.high for candle in window) - min(candle.low for candle in window), candles[idx].close)


def _close_range_position(candles: Sequence[Candle], idx: int, lookback: int) -> Decimal | None:
    if idx + 1 < lookback:
        return None
    window = candles[idx - lookback + 1:idx + 1]
    low = min(candle.low for candle in window)
    high = max(candle.high for candle in window)
    if high == low:
        return None
    return ((candles[idx].close - low) / (high - low)).quantize(Decimal("0.00000001"))


def _indicator_slope_pct(snapshots: Sequence[Any], idx: int, field: str, lookback: int) -> Decimal | None:
    if idx < lookback:
        return None
    current = _maybe_decimal(getattr(snapshots[idx], field, None))
    previous = _maybe_decimal(getattr(snapshots[idx - lookback], field, None))
    if current is None or previous is None or previous == 0:
        return None
    return _ratio(current - previous, previous)


def _macd_histogram_slope_pct(snapshots: Sequence[Any], idx: int, close: Decimal) -> Decimal | None:
    if idx < 1:
        return None
    current = _maybe_decimal(getattr(snapshots[idx], "macd_histogram", None))
    previous = _maybe_decimal(getattr(snapshots[idx - 1], "macd_histogram", None))
    if current is None or previous is None:
        return None
    return _ratio(current - previous, close)


def _ema_spread_crosses(snapshots: Sequence[Any], idx: int, lookback: int) -> int | None:
    if idx + 1 < lookback:
        return None
    signs: list[int] = []
    for snapshot in snapshots[idx - lookback + 1:idx + 1]:
        ema10 = _maybe_decimal(getattr(snapshot, "ema_10", None))
        sma20 = _maybe_decimal(getattr(snapshot, "sma_20", None))
        if ema10 is None or sma20 is None:
            return None
        signs.append(1 if ema10 >= sma20 else -1)
    return sum(1 for left, right in zip(signs, signs[1:], strict=False) if left != right)


def _price_whipsaws(candles: Sequence[Candle], snapshots: Sequence[Any], idx: int, lookback: int) -> int | None:
    if idx + 1 < lookback:
        return None
    signs: list[int] = []
    for candle, snapshot in zip(candles[idx - lookback + 1:idx + 1], snapshots[idx - lookback + 1:idx + 1], strict=False):
        ema10 = _maybe_decimal(getattr(snapshot, "ema_10", None))
        if ema10 is None:
            return None
        signs.append(1 if candle.close >= ema10 else -1)
    return sum(1 for left, right in zip(signs, signs[1:], strict=False) if left != right)


def _low_directional_progress(candles: Sequence[Candle], idx: int, lookback: int) -> bool | None:
    if idx + 1 < lookback:
        return None
    window = candles[idx - lookback + 1:idx + 1]
    total_range = max(candle.high for candle in window) - min(candle.low for candle in window)
    if total_range <= 0:
        return None
    progress = abs(window[-1].close - window[0].close) / total_range
    return progress < Decimal("0.2")


def _maybe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return decimal if decimal.is_finite() else None


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return _coerce_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except (TypeError, ValueError):
        return None


def _pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0"
    return _fmt((Decimal(numerator) / Decimal(denominator)) * Decimal("100"))


def sor_ev3_report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SOR-EV3 Avoid Sideways / Low-Volatility Drilldown",
        "",
        f"Recorded at: `{report['generated_at']}`",
        "",
        f"Status: `{report['status']}`",
        "",
        "SOR-EV3 is evidence-only research for the founder-selected `avoid_sideways_low_volatility` candidate family. It uses canonical SV2.0.2 DB-imported evidence packs and true-forward replay. Production Money Flow rules are unchanged, no order endpoints are called, no private/signed endpoints are called, and no variant is approved for production.",
        "",
        "## Executive Summary",
        "",
        f"- Baseline: `{report['canonical_baseline']['source']}` at `{report['canonical_baseline']['timestamp']}`.",
        f"- Baseline parity: `{report['baseline_parity_summary']['status_counts']}`.",
        f"- Variants tested: `{', '.join(row['variant_id'] for row in report['variant_summary'])}`.",
        f"- Candidate variants: `{', '.join(report['candidate_variants']) if report['candidate_variants'] else 'none'}`.",
        f"- Promising but not promoted: `{', '.join(report.get('promising_variants', [])) if report.get('promising_variants') else 'none'}`.",
        f"- Hard rejected variants: `{', '.join(report.get('rejected_variants', [])) if report.get('rejected_variants') else 'none'}`.",
        "- `promising_*` means directionally interesting for founder review, not approved and not promoted.",
        "- Dashboard date filters remain display-only and are not canonical evidence.",
        "",
        "## Founder-Selected Candidate",
        "",
        "`avoid_sideways_low_volatility` targets entries during compressed, flat, or low-directional-progress conditions. This phase tests objective definitions only; it does not approve a rule.",
        "",
        "## Baseline Reference",
        "",
        f"- Canonical pack paths inspected: `{len(report['baseline_evidence_references'])}`.",
        f"- Money Flow version: `{report['canonical_baseline']['money_flow_version']}`.",
        f"- Symbols: `{', '.join(report['canonical_baseline']['symbols'])}`.",
        f"- Timeframes: `{', '.join(report['canonical_baseline']['timeframes'])}`.",
        f"- Capital mode: `{report['canonical_baseline']['capital_mode']}` with `{report['canonical_baseline']['initial_equity_per_independent_scenario']}` USDC per independent scenario.",
        "",
        "## Feature Definitions",
        "",
        "| Feature | Definition |",
        "|---|---|",
    ]
    for row in report["regime_feature_definitions"]:
        lines.append(f"| `{row['feature']}` | {row['definition']} |")
    lines.extend([
        "",
        "## Variant Comparison",
        "",
        "| Variant | Founder Label | Promotion Status | Outcome | Scenarios | Net PnL Delta | DD Delta Worst | Blocked Signals | Matched Trades | Avoided Losers | Missed Winners | Trade Reduction % | Promotion Blockers |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["variant_summary"]:
        blockers = ", ".join(row.get("promotion_blockers", [])) or "none"
        lines.append(f"| `{row['variant_id']}` | `{row.get('founder_review_label', 'unlabeled')}` | `{row.get('promotion_status', 'not_promoted')}` | `{row['outcome_taxonomy']}` | {row['scenario_count']} | {row['net_pnl_delta_sum_across_independent_scenarios']} | {row['max_drawdown_delta_worst']} | {row['blocked_open_signals']} | {row['blocked_entries']} | {row['avoided_losers']} | {row['missed_winners']} | {row['trade_count_reduction_pct']} | `{blockers}` |")
    lines.extend([
        "",
        "## Founder Label Meaning",
        "",
        "| Label | Meaning |",
        "|---|---|",
        "| `candidate_for_more_evidence` | Passed the strict SOR-EV3 gate; still evidence-only and not production approved. |",
        "| `promising_high_pnl_control_risk` | Large aggregate PnL improvement, but drawdown/control-pocket preservation failed. |",
        "| `promising_control_pocket_risk` | Directionally interesting aggregate improvement, but control pockets and/or drawdown failed. |",
        "| `mixed_positive_pnl_control_damage` | Positive aggregate but too much damage to strong baseline pockets. |",
        "| `not_promoted_low_impact` | Too little aggregate impact for more evidence. |",
        "| `rejected_negative_aggregate` | Aggregate PnL was worse than baseline. |",
        "",
        "Promotion still requires true-forward methodology, positive aggregate PnL delta, no worst-scenario drawdown worsening, avoided losers at least equal to missed winners, trade reduction at or below 55%, and zero damaged control pockets.",
    ])
    lines.extend([
        "",
        "## Baseline Loss Concentration In Sideways / Low-Vol Regimes",
        "",
        "| Variant Definition | Losing Trades Flagged % | Winning Trades Flagged % | Flagged Losing Trades | Flagged Winning Trades |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in report["loss_concentration_summary"]:
        lines.append(f"| `{row['variant_id']}` | {row['baseline_percent_losing_trades_flagged']} | {row['baseline_percent_winning_trades_flagged']} | {row['baseline_flagged_losing_trades']} | {row['baseline_flagged_winning_trades']} |")
    lines.extend([
        "",
        "## Blocked-Entry Attribution",
        "",
        f"- Total blocked open signals measured: `{report['blocked_entry_summary']['total_blocked_open_signals']}`.",
        f"- Canonical blocked baseline trades with matched PnL attribution: `{report['blocked_entry_summary']['canonical_blocked_entries']}`.",
        "",
        "| Variant | Blocked Signals | Matched Baseline Trades | Avoided Losers | Missed Winners | Large Losses Reduced | Reason Counts |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["blocked_entry_summary"]["by_variant"]:
        lines.append(f"| `{row['variant_id']}` | {row['blocked_open_signals']} | {row['blocked_entries']} | {row['avoided_losers']} | {row['missed_winners']} | {row['large_losses_reduced']} | `{row['reason_counts']}` |")
    lines.extend([
        "",
        "## Control-Pocket Impact",
        "",
        "| Variant | Controls | Improved | Preserved | Damaged | Return Reduced | Drawdown Reduced | Trade Count Reduced Too Much |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in report["control_pocket_impact"]:
        lines.append(f"| `{row['variant_id']}` | {row['control_pocket_count']} | {row['improved']} | {row['preserved']} | {row['damaged']} | {row['return_reduced']} | {row['drawdown_reduced']} | {row['trade_count_reduced_too_much']} |")
    lines.extend([
        "",
        "## Candidate / Promising / Not Promoted Variants",
        "",
        f"- Candidate for more evidence: `{', '.join(report['candidate_variants']) if report['candidate_variants'] else 'none'}`.",
        f"- Promising but not promoted: `{', '.join(report.get('promising_variants', [])) if report.get('promising_variants') else 'none'}`.",
        f"- Not promoted: `{', '.join(report.get('not_promoted_variants', [])) if report.get('not_promoted_variants') else 'none'}`.",
        f"- Hard rejected: `{', '.join(report.get('rejected_variants', [])) if report.get('rejected_variants') else 'none'}`.",
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["limitations"])
    lines.extend([
        "",
        "## Recommended Next Phase",
        "",
        "If the founder wants to continue, SOR-EV4 should take only a narrow promising label from this report, rerun it with out-of-sample-style date slices, and require control-pocket preservation before any rule-change proposal. If no candidate is clean, keep the broader sideways/low-volatility idea unpromoted rather than treating it as production-ready.",
        "",
        "## Boundary Confirmation",
        "",
    ])
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(report["boundary_flags"].items()))
    return "\n".join(lines).rstrip() + "\n"


def write_sor_ev3_outputs(report: dict[str, Any], markdown_path: str | Path, json_path: str | Path) -> None:
    markdown = sor_ev3_report_to_markdown(report)
    lower = markdown.lower()
    for phrase in FORBIDDEN_REPORT_PHRASES:
        if phrase in lower:
            raise ValueError(f"forbidden proof/live approval language present: {phrase}")
    Path(markdown_path).write_text(markdown, encoding="utf-8")
    Path(json_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "FEATURE_DEFINITIONS",
    "SOR_EV3_VARIANTS",
    "build_sor_ev3_report",
    "build_sor_ev3_report_sync",
    "sor_ev3_report_to_markdown",
    "write_sor_ev3_outputs",
]
