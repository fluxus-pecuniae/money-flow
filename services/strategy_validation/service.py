"""Money Flow strategy validation and backtest reporting.

This service is intentionally separate from routing, automation, and live
execution. It reads persisted historical candles, reuses the current Money Flow
strategy rules, and produces simulated research artifacts only.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from core.config.settings import AppSettings, MoneyFlowSleeveConfig, get_settings
from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    MarketDataSourceMode,
    OrderSide,
    PositionStatus,
    StrategyDecisionStatus,
    StrategyValidationCapitalSizingMode,
    StrategyFamily,
    StrategyValidationFillTiming,
    Timeframe,
)
from core.domain.models import (
    Candle,
    IndicatorSnapshot,
    Position,
    StrategyEvaluationInput,
    StrategyValidationAssumptions,
    StrategyValidationBatchReport,
    StrategyValidationBatchRequest,
    StrategyValidationBatchRunReport,
    StrategyValidationComponentReport,
    StrategyValidationDataCoverage,
    StrategyValidationMetrics,
    StrategyValidationRegimeSummary,
    StrategyValidationReport,
    StrategyValidationRequest,
    StrategyValidationTrade,
)
from db.models import CandleModel, InstrumentModel
from db.session import SessionLocal
from services.indicators.service import DefaultIndicatorService
from services.strategy.money_flow import MoneyFlowStrategyFamily

_DECIMAL_PLACES = Decimal("0.00000001")
_REGIME_LOOKBACK_CANDLES = 8
_TREND_RETURN_THRESHOLD = Decimal("0.01")
_HIGH_VOLATILITY_AVG_ABS_RETURN = Decimal("0.0125")
_LOW_VOLATILITY_AVG_ABS_RETURN = Decimal("0.0025")
_DATA_COVERAGE_WARNING_THRESHOLD = Decimal("0.80")
STRATEGY_VALIDATION_WINDOW_CONVENTION = "candle_close_time_start_exclusive_end_inclusive"
_WINDOW_CONVENTION = STRATEGY_VALIDATION_WINDOW_CONVENTION


class StrategyValidationError(ValueError):
    """Raised when a validation request cannot be evaluated truthfully."""


class MoneyFlowBacktestService:
    """Runs deterministic Money Flow backtests from persisted candles."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        indicator_service: DefaultIndicatorService | None = None,
        strategy_family: MoneyFlowStrategyFamily | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self._indicator_service = indicator_service or DefaultIndicatorService(
            self.settings,
            session_factory=session_factory,
        )
        self._strategy_family = strategy_family or MoneyFlowStrategyFamily(self.settings)

    async def run_money_flow_backtest(
        self,
        request: StrategyValidationRequest,
    ) -> StrategyValidationReport:
        if request.strategy_family != StrategyFamily.MONEY_FLOW:
            raise StrategyValidationError("SV1.0 only supports the Money Flow strategy family.")
        start_at = _coerce_utc(request.start_at)
        end_at = _coerce_utc(request.end_at)
        if end_at <= start_at:
            raise StrategyValidationError("end_at must be after start_at.")
        _validate_assumptions(request.assumptions)

        component_reports: list[StrategyValidationComponentReport] = []
        for sleeve in self._requested_sleeves(request.component_keys):
            component_reports.append(
                await self._run_component(
                    request=request,
                    sleeve=sleeve,
                    start_at=start_at,
                    end_at=end_at,
                )
            )

        aggregate_metrics = _build_metrics(
            trades=[
                trade
                for component_report in component_reports
                for trade in component_report.trades
            ],
            initial_capital=request.assumptions.initial_capital,
            no_trade_reason_counts=_merge_counts(
                component_report.no_trade_reason_counts for component_report in component_reports
            ),
            invalid_reason_counts=_merge_counts(
                component_report.invalid_reason_counts for component_report in component_reports
            ),
            mark_to_market_drawdown_override=_max_optional(
                component_report.metrics.mark_to_market_max_drawdown
                for component_report in component_reports
            ),
            mark_to_market_drawdown_pct_override=_max_optional(
                component_report.metrics.mark_to_market_max_drawdown_pct
                for component_report in component_reports
            ),
            capital_sizing_mode=request.assumptions.capital_sizing_mode,
            position_notional_pct=request.assumptions.position_notional_pct,
            trades_skipped_due_to_insufficient_equity=sum(
                component_report.metrics.trades_skipped_due_to_insufficient_equity
                for component_report in component_reports
            ),
        )
        limitations = sorted(
            {
                limitation
                for component_report in component_reports
                for limitation in component_report.limitations
            }
        )
        if len(component_reports) > 1:
            limitations.append(
                "aggregate_mark_to_market_drawdown_uses_max_component_path_not_concurrent_portfolio_replay"
            )
        limitations.extend(_assumption_limitations(request.assumptions))
        report_payload = {
            "strategy_family": request.strategy_family.value,
            "environment": request.environment.value,
            "venue": request.venue,
            "symbol": request.symbol,
            "instrument_key": request.instrument_key,
            "instrument_ref_id": request.instrument_ref_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "assumptions": _json_ready(asdict(request.assumptions)),
            "components": [report.component_key for report in component_reports],
            "trade_ids": [
                trade.trade_id
                for component_report in component_reports
                for trade in component_report.trades
            ],
        }
        return StrategyValidationReport(
            report_id=f"svr-{_stable_hash(report_payload)[:24]}",
            strategy_family=StrategyFamily.MONEY_FLOW,
            environment=request.environment,
            venue=request.venue,
            symbol=request.symbol,
            instrument_key=request.instrument_key,
            instrument_ref_id=request.instrument_ref_id,
            start_at=start_at,
            end_at=end_at,
            assumptions=request.assumptions,
            component_reports=component_reports,
            aggregate_metrics=aggregate_metrics,
            component_comparison=_component_comparison(component_reports),
            data_coverage_summary=_data_coverage_summary(component_reports),
            regime_comparison=_regime_comparison(component_reports),
            limitations=limitations,
        )

    async def run_money_flow_batch_backtest(
        self,
        request: StrategyValidationBatchRequest,
    ) -> StrategyValidationBatchReport:
        if not request.runs:
            raise StrategyValidationError("batch request must include at least one validation run.")

        run_reports: list[StrategyValidationBatchRunReport] = []
        for run_index, run_request in enumerate(request.runs):
            run_payload = _request_payload(run_request)
            run_id = f"svbr-{_stable_hash({'run_index': run_index, 'request': run_payload})[:24]}"
            try:
                report = await self.run_money_flow_backtest(run_request)
            except StrategyValidationError as exc:
                run_reports.append(
                    StrategyValidationBatchRunReport(
                        run_id=run_id,
                        run_index=run_index,
                        request=run_request,
                        status="blocked",
                        reason_codes=["strategy_validation_run_blocked"],
                        error_message=str(exc),
                    )
                )
                continue
            run_reports.append(
                StrategyValidationBatchRunReport(
                    run_id=run_id,
                    run_index=run_index,
                    request=run_request,
                    status="completed",
                    report=report,
                    report_id=report.report_id,
                    reason_codes=[],
                )
            )

        batch_payload = {
            "batch_name": request.batch_name,
            "runs": [_request_payload(run.request) for run in run_reports],
            "statuses": [run.status for run in run_reports],
            "report_ids": [run.report_id for run in run_reports],
        }
        completed_reports = [
            run.report for run in run_reports if run.report is not None
        ]
        limitations = sorted(
            {
                limitation
                for report in completed_reports
                for limitation in report.limitations
            }
        )
        if any(run.status != "completed" for run in run_reports):
            limitations.append("one_or_more_batch_runs_blocked_and_reported_individually")
        warnings = _batch_warnings(run_reports)
        return StrategyValidationBatchReport(
            batch_id=f"svb-{_stable_hash(batch_payload)[:24]}",
            batch_name=request.batch_name,
            strategy_family=StrategyFamily.MONEY_FLOW,
            run_reports=run_reports,
            assumptions_matrix=_assumptions_matrix(run_reports),
            comparison_summary=_comparison_summary(run_reports),
            limitations=limitations,
            warnings=warnings,
        )

    async def _run_component(
        self,
        *,
        request: StrategyValidationRequest,
        sleeve: MoneyFlowSleeveConfig,
        start_at: datetime,
        end_at: datetime,
    ) -> StrategyValidationComponentReport:
        candles = self._load_candles(request=request, timeframe=sleeve.timeframe, end_at=end_at)
        snapshots = self._indicator_service._compute_snapshots(candles)
        data_coverage = _data_coverage(candles, timeframe=sleeve.timeframe, start_at=start_at, end_at=end_at)
        regime_by_close_time = _label_candle_regimes(candles)
        trades: list[StrategyValidationTrade] = []
        no_trade_reasons: Counter[str] = Counter()
        invalid_reasons: Counter[str] = Counter()
        no_trade_reasons_by_regime: dict[str, Counter[str]] = {}
        invalid_reasons_by_regime: dict[str, Counter[str]] = {}
        limitations: list[str] = []
        open_position: _SimulatedOpenPosition | None = None
        realized_equity = request.assumptions.initial_capital
        closed_trade_equity_points: list[Decimal] = [request.assumptions.initial_capital]
        mark_to_market_equity_points: list[Decimal] = [request.assumptions.initial_capital]
        trades_skipped_due_to_insufficient_equity = 0
        evaluated_candles = 0
        if not candles:
            limitations.append("no_persisted_candles_for_component")
        limitations.extend(data_coverage.warning_reason_codes)

        for signal_index, (candle, snapshot) in enumerate(zip(candles, snapshots, strict=False)):
            history_index = signal_index + 1
            candle_close_time = _coerce_utc(candle.close_time)
            if candle_close_time <= start_at or candle_close_time > end_at:
                continue
            regime = regime_by_close_time.get(
                candle_close_time,
                _CandleRegime.unknown(candle_close_time),
            )
            evaluated_candles += 1
            position_active_for_evaluation = (
                open_position is not None and candle_close_time > open_position.entry_time
            )
            current_position = (
                _position_from_open_position(open_position, request=request, candle=candle)
                if position_active_for_evaluation
                else None
            )
            evaluation_input = self._evaluation_input(
                request=request,
                sleeve=sleeve,
                candle=candle,
                snapshot=snapshot,
                history_bars=history_index,
                current_position=current_position,
                position_state_fingerprint=(
                    open_position.position_state_fingerprint if position_active_for_evaluation else None
                ),
            )
            evaluation = await self._strategy_family.evaluate(evaluation_input)
            decision = evaluation.decision

            if open_position is not None:
                if candle_close_time > open_position.entry_time:
                    open_position.record_excursion(candle)
                    mark_to_market_equity_points.append(
                        open_position.mark_to_market_equity(realized_equity, candle.low)
                    )
                if candle_close_time <= open_position.entry_time:
                    continue
                if decision.action in {DecisionAction.CLOSE, DecisionAction.REDUCE}:
                    if decision.action == DecisionAction.REDUCE:
                        limitations.append("reduce_actions_are_simulated_as_full_exits_for_sv1_0")
                    fill = _resolve_fill(
                        candles=candles,
                        signal_index=signal_index,
                        fill_timing=request.assumptions.fill_timing,
                    )
                    if fill is None:
                        limitations.append(
                            f"{decision.action.value}_signal_skipped_no_fill_candle_for_"
                            f"{request.assumptions.fill_timing.value}"
                        )
                        continue
                    if request.assumptions.fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_CLOSE:
                        open_position.record_excursion(fill.candle)
                        mark_to_market_equity_points.append(
                            open_position.mark_to_market_equity(realized_equity, fill.candle.low)
                        )
                    trade = _close_trade(
                        request=request,
                        open_position=open_position,
                        fill=fill,
                        exit_signal_time=candle_close_time,
                        exit_reason=decision.reason_code or decision.action.value,
                        exit_evaluation_key=decision.evaluation_key,
                        exit_market_regime=regime.trend_label,
                        exit_volatility_regime=regime.volatility_label,
                        forced_exit=False,
                    )
                    trades.append(trade)
                    realized_equity = _money(realized_equity + trade.net_pnl)
                    closed_trade_equity_points.append(realized_equity)
                    mark_to_market_equity_points.append(realized_equity)
                    open_position = None
                continue

            if decision.status == StrategyDecisionStatus.INVALID:
                reason = decision.reason_code or "invalid_without_reason"
                invalid_reasons[reason] += 1
                invalid_reasons_by_regime.setdefault(regime.trend_label, Counter())[reason] += 1
                continue
            if decision.status == StrategyDecisionStatus.NO_TRADE:
                reason = decision.reason_code or "no_trade_without_reason"
                no_trade_reasons[reason] += 1
                no_trade_reasons_by_regime.setdefault(regime.trend_label, Counter())[reason] += 1
                continue
            if decision.action == DecisionAction.OPEN:
                if _dynamic_equity_is_depleted(request.assumptions, realized_equity):
                    reason = "dynamic_equity_depleted"
                    invalid_reasons[reason] += 1
                    invalid_reasons_by_regime.setdefault(regime.trend_label, Counter())[reason] += 1
                    trades_skipped_due_to_insufficient_equity += 1
                    limitations.append("dynamic_equity_depleted_no_new_trades_opened")
                    continue
                fill = _resolve_fill(
                    candles=candles,
                    signal_index=signal_index,
                    fill_timing=request.assumptions.fill_timing,
                )
                if fill is None:
                    limitations.append(
                        f"open_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}"
                    )
                    continue
                open_position = _open_trade(
                    request=request,
                    sleeve=sleeve,
                    fill=fill,
                    entry_signal_time=candle_close_time,
                    entry_reason=decision.reason_code,
                    entry_evaluation_key=decision.evaluation_key,
                    entry_market_regime=regime.trend_label,
                    entry_volatility_regime=regime.volatility_label,
                    current_realized_equity=realized_equity,
                )
                if _coerce_utc(fill.candle.close_time) > open_position.entry_time:
                    open_position.record_excursion(fill.candle)
                    mark_to_market_equity_points.append(
                        open_position.mark_to_market_equity(realized_equity, fill.candle.low)
                    )

        if open_position is not None and request.assumptions.force_close_open_trade_at_end:
            last_candle = _last_candle_in_window(candles, start_at=start_at, end_at=end_at)
            if last_candle is not None:
                open_position.record_excursion(last_candle)
                mark_to_market_equity_points.append(
                    open_position.mark_to_market_equity(realized_equity, last_candle.low)
                )
                force_fill = _ResolvedFill(
                    candle=last_candle,
                    raw_price=last_candle.close,
                    time=_coerce_utc(last_candle.close_time),
                    source="end_of_window_close",
                )
                trade = _close_trade(
                    request=request,
                    open_position=open_position,
                    fill=force_fill,
                    exit_signal_time=_coerce_utc(last_candle.close_time),
                    exit_reason="end_of_window_forced_close",
                    exit_evaluation_key=f"{open_position.entry_evaluation_key}:forced_exit",
                    exit_market_regime=regime_by_close_time.get(
                        _coerce_utc(last_candle.close_time),
                        _CandleRegime.unknown(_coerce_utc(last_candle.close_time)),
                    ).trend_label,
                    exit_volatility_regime=regime_by_close_time.get(
                        _coerce_utc(last_candle.close_time),
                        _CandleRegime.unknown(_coerce_utc(last_candle.close_time)),
                    ).volatility_label,
                    forced_exit=True,
                )
                trades.append(trade)
                realized_equity = _money(realized_equity + trade.net_pnl)
                closed_trade_equity_points.append(realized_equity)
                mark_to_market_equity_points.append(realized_equity)
                limitations.append("open_positions_are_force_closed_at_window_end_for_sv1_0")
        if evaluated_candles == 0:
            limitations.append("no_candles_in_requested_window")

        no_trade_counts = dict(sorted(no_trade_reasons.items()))
        invalid_counts = dict(sorted(invalid_reasons.items()))
        metrics = _build_metrics(
            trades=trades,
            initial_capital=request.assumptions.initial_capital,
            no_trade_reason_counts=no_trade_counts,
            invalid_reason_counts=invalid_counts,
            closed_trade_equity_points=closed_trade_equity_points,
            mark_to_market_equity_points=mark_to_market_equity_points,
            capital_sizing_mode=request.assumptions.capital_sizing_mode,
            position_notional_pct=request.assumptions.position_notional_pct,
            trades_skipped_due_to_insufficient_equity=trades_skipped_due_to_insufficient_equity,
        )
        return StrategyValidationComponentReport(
            component_key=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            candle_count=len(candles),
            evaluated_candles=evaluated_candles,
            trades=trades,
            metrics=metrics,
            data_coverage=data_coverage,
            regime_methodology=_regime_methodology(),
            regime_summaries=_build_regime_summaries(
                trades=trades,
                candles=candles,
                regime_by_close_time=regime_by_close_time,
                start_at=start_at,
                end_at=end_at,
                no_trade_reason_counts_by_regime=no_trade_reasons_by_regime,
                invalid_reason_counts_by_regime=invalid_reasons_by_regime,
            ),
            no_trade_reason_counts=no_trade_counts,
            invalid_reason_counts=invalid_counts,
            limitations=sorted(set(limitations)),
        )

    def _requested_sleeves(self, component_keys: tuple[str, ...]) -> list[MoneyFlowSleeveConfig]:
        sleeves = list(self.settings.money_flow.sleeves)
        requested = set(component_keys)
        if not requested or "all" in requested:
            return sleeves
        by_key = {sleeve.sleeve_id: sleeve for sleeve in sleeves}
        unknown = sorted(requested.difference(by_key))
        if unknown:
            raise StrategyValidationError(f"Unknown Money Flow component(s): {', '.join(unknown)}")
        return [by_key[key] for key in component_keys]

    def _load_candles(
        self,
        *,
        request: StrategyValidationRequest,
        timeframe: Timeframe,
        end_at: datetime,
    ) -> list[Candle]:
        instrument_ref_id = request.instrument_ref_id
        with self._session_factory() as session:
            if request.instrument_key is not None and instrument_ref_id is None:
                instrument_ref_id = session.scalar(
                    select(InstrumentModel.id).where(InstrumentModel.instrument_key == request.instrument_key)
                )
                if instrument_ref_id is None:
                    raise StrategyValidationError(f"Unknown instrument_key: {request.instrument_key}")
            query = (
                select(CandleModel)
                .where(
                    CandleModel.environment == request.environment,
                    CandleModel.venue == request.venue,
                    CandleModel.symbol == request.symbol,
                    CandleModel.timeframe == timeframe,
                    CandleModel.close_time <= end_at,
                )
                .order_by(CandleModel.open_time.asc())
            )
            if instrument_ref_id is not None:
                query = query.where(CandleModel.instrument_ref_id == instrument_ref_id)
            models = session.scalars(query).all()
            instrument_keys = {
                model.instrument_ref_id: session.scalar(
                    select(InstrumentModel.instrument_key).where(InstrumentModel.id == model.instrument_ref_id)
                )
                for model in models
                if model.instrument_ref_id is not None
            }
        return [
            Candle(
                instrument_key=(
                    str(instrument_keys.get(model.instrument_ref_id))
                    if instrument_keys.get(model.instrument_ref_id) is not None
                    else None
                ),
                instrument_ref_id=model.instrument_ref_id,
                venue=model.venue,
                symbol=model.symbol,
                timeframe=model.timeframe,
                open_time=_coerce_utc(model.open_time),
                close_time=_coerce_utc(model.close_time),
                open=model.open,
                high=model.high,
                low=model.low,
                close=model.close,
                volume=model.volume,
                trade_count=model.trade_count,
            )
            for model in models
        ]

    def _evaluation_input(
        self,
        *,
        request: StrategyValidationRequest,
        sleeve: MoneyFlowSleeveConfig,
        candle: Candle,
        snapshot: IndicatorSnapshot,
        history_bars: int,
        current_position: Position | None,
        position_state_fingerprint: str | None,
    ) -> StrategyEvaluationInput:
        evaluation_key = _evaluation_key(
            request=request,
            sleeve=sleeve,
            candle=candle,
            history_bars=history_bars,
            position_state_fingerprint=position_state_fingerprint,
        )
        instrument_key = request.instrument_key or candle.instrument_key or ""
        instrument_ref_id = request.instrument_ref_id or candle.instrument_ref_id or ""
        return StrategyEvaluationInput(
            family=StrategyFamily.MONEY_FLOW,
            sleeve_id=sleeve.sleeve_id,
            component_key=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            evaluation_key=evaluation_key,
            client_ref_id=None,
            client_key=None,
            strategy_mandate_ref_id=None,
            mandate_key=None,
            market_data_source_policy_ref_id=None,
            market_data_source_venue=request.venue,
            market_data_source_mode=MarketDataSourceMode.SINGLE_VENUE,
            mandate_account_binding_ref_id=None,
            binding_key=None,
            venue_account_ref_id=None,
            venue_account_key=None,
            account_address=None,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            venue=request.venue,
            symbol=request.symbol,
            indicator_snapshot=snapshot,
            latest_candle=candle,
            current_position=current_position,
            market_data_fresh=True,
            instrument_active=True,
            instrument_strategy_eligible=True,
            sleeve_enabled=sleeve.enabled,
            history_bars=history_bars,
            latest_candle_close=candle.close_time,
            indicator_boundary_aligned=_coerce_utc(snapshot.as_of) == _coerce_utc(candle.close_time),
            config_fingerprint=_stable_hash(sleeve.model_dump(mode="json")),
            position_state_fingerprint=position_state_fingerprint,
            family_config=sleeve.model_dump(mode="json"),
        )


@dataclass(slots=True)
class _ResolvedFill:
    candle: Candle
    raw_price: Decimal
    time: datetime
    source: str


class _SimulatedOpenPosition:
    def __init__(
        self,
        *,
        component_key: str,
        timeframe: Timeframe,
        entry_time: datetime,
        entry_signal_time: datetime,
        raw_entry_price: Decimal,
        entry_price: Decimal,
        size: Decimal,
        entry_notional: Decimal,
        entry_fee: Decimal,
        entry_slippage_cost: Decimal,
        equity_before_entry: Decimal,
        entry_reason: str | None,
        entry_evaluation_key: str,
        capital_sizing_mode: StrategyValidationCapitalSizingMode,
        position_notional_pct: Decimal,
        fill_timing: StrategyValidationFillTiming,
        entry_fill_source: str,
        entry_market_regime: str,
        entry_volatility_regime: str,
    ) -> None:
        self.component_key = component_key
        self.timeframe = timeframe
        self.entry_time = entry_time
        self.entry_signal_time = entry_signal_time
        self.raw_entry_price = raw_entry_price
        self.entry_price = entry_price
        self.size = size
        self.entry_notional = entry_notional
        self.entry_fee = entry_fee
        self.entry_slippage_cost = entry_slippage_cost
        self.equity_before_entry = equity_before_entry
        self.entry_reason = entry_reason
        self.entry_evaluation_key = entry_evaluation_key
        self.capital_sizing_mode = capital_sizing_mode
        self.position_notional_pct = position_notional_pct
        self.fill_timing = fill_timing
        self.entry_fill_source = entry_fill_source
        self.entry_market_regime = entry_market_regime
        self.entry_volatility_regime = entry_volatility_regime
        self.max_adverse_excursion = Decimal("0")
        self.max_favorable_excursion = Decimal("0")
        self.position_state_fingerprint = _stable_hash(
            {
                "component_key": component_key,
                "entry_time": entry_time.isoformat(),
                "entry_price": str(entry_price),
                "size": str(size),
            }
        )

    def record_excursion(self, candle: Candle) -> None:
        adverse = ((candle.low - self.raw_entry_price) * self.size).quantize(_DECIMAL_PLACES)
        favorable = ((candle.high - self.raw_entry_price) * self.size).quantize(_DECIMAL_PLACES)
        self.max_adverse_excursion = min(self.max_adverse_excursion, adverse)
        self.max_favorable_excursion = max(self.max_favorable_excursion, favorable)

    def mark_to_market_equity(self, realized_equity: Decimal, mark_price: Decimal) -> Decimal:
        unrealized = (mark_price - self.raw_entry_price) * self.size
        return _money(realized_equity + unrealized - self.entry_fee - self.entry_slippage_cost)


@dataclass(slots=True)
class _CandleRegime:
    close_time: datetime
    trend_label: str
    volatility_label: str

    @classmethod
    def unknown(cls, close_time: datetime) -> "_CandleRegime":
        return cls(
            close_time=close_time,
            trend_label="unknown_or_insufficient_data",
            volatility_label="unknown_or_insufficient_data",
        )


def _data_coverage(
    candles: list[Candle],
    *,
    timeframe: Timeframe,
    start_at: datetime,
    end_at: datetime,
) -> StrategyValidationDataCoverage:
    timeframe_delta = _timeframe_delta(timeframe)
    window_candles = [
        candle
        for candle in candles
        if start_at < _coerce_utc(candle.close_time) <= end_at
    ]
    close_times = sorted(_coerce_utc(candle.close_time) for candle in window_candles)
    expected_count: int | None = None
    missing_count: int | None = None
    coverage_percent: Decimal | None = None
    gap_count: int | None = None
    largest_gap_seconds: int | None = None
    warning_reason_codes: list[str] = []
    if timeframe_delta is not None:
        expected_count = _expected_close_slot_count(
            start_at=start_at,
            end_at=end_at,
            timeframe_delta=timeframe_delta,
        )
        missing_count = max(expected_count - len(close_times), 0)
        coverage_percent = (
            _ratio(Decimal(len(close_times)), Decimal(expected_count))
            if expected_count > 0
            else None
        )
        if coverage_percent is not None:
            coverage_percent = min(coverage_percent, Decimal("1.00000000"))
        expected_gap_seconds = int(timeframe_delta.total_seconds())
        gaps = [
            int((later - earlier).total_seconds())
            for earlier, later in zip(close_times, close_times[1:], strict=False)
            if int((later - earlier).total_seconds()) > expected_gap_seconds
        ]
        gap_count = len(gaps)
        largest_gap_seconds = max(gaps) if gaps else 0
        if _has_unaligned_window_boundary(
            start_at=start_at,
            end_at=end_at,
            timeframe_delta=timeframe_delta,
        ):
            warning_reason_codes.append("unaligned_window_boundary")
        if expected_count is not None and len(close_times) > expected_count:
            warning_reason_codes.append("actual_candles_exceed_expected_close_slots")
        if coverage_percent is not None and coverage_percent < _DATA_COVERAGE_WARNING_THRESHOLD:
            warning_reason_codes.append("data_coverage_below_warning_threshold")
        if missing_count > 0:
            warning_reason_codes.append("missing_candles_in_requested_window")
        if gap_count > 0:
            warning_reason_codes.append("candle_gaps_detected")
    else:
        warning_reason_codes.append("expected_candle_count_not_derivable_for_timeframe")
    if not close_times:
        warning_reason_codes.append("no_candles_in_requested_window")

    return StrategyValidationDataCoverage(
        requested_start_at=start_at,
        requested_end_at=end_at,
        window_convention=_WINDOW_CONVENTION,
        first_candle_available_at=close_times[0] if close_times else None,
        last_candle_available_at=close_times[-1] if close_times else None,
        expected_candle_count=expected_count,
        actual_candle_count=len(close_times),
        missing_candle_count=missing_count,
        coverage_percent=coverage_percent,
        gap_count=gap_count,
        largest_gap_seconds=largest_gap_seconds,
        warning_reason_codes=sorted(set(warning_reason_codes)),
    )


def _expected_close_slot_count(
    *,
    start_at: datetime,
    end_at: datetime,
    timeframe_delta: timedelta,
) -> int:
    if end_at <= start_at:
        return 0
    delta_seconds = int(timeframe_delta.total_seconds())
    if delta_seconds <= 0:
        return 0
    start_seconds = int(start_at.timestamp())
    end_seconds = int(end_at.timestamp())
    first_close_slot = ((start_seconds // delta_seconds) + 1) * delta_seconds
    if first_close_slot > end_seconds:
        return 0
    return ((end_seconds - first_close_slot) // delta_seconds) + 1


def _has_unaligned_window_boundary(
    *,
    start_at: datetime,
    end_at: datetime,
    timeframe_delta: timedelta,
) -> bool:
    delta_seconds = int(timeframe_delta.total_seconds())
    if delta_seconds <= 0:
        return False
    return (
        int(start_at.timestamp()) % delta_seconds != 0
        or int(end_at.timestamp()) % delta_seconds != 0
    )


def _label_candle_regimes(candles: list[Candle]) -> dict[datetime, _CandleRegime]:
    ordered = sorted(candles, key=lambda candle: _coerce_utc(candle.close_time))
    regimes: dict[datetime, _CandleRegime] = {}
    for index, candle in enumerate(ordered):
        close_time = _coerce_utc(candle.close_time)
        if index < _REGIME_LOOKBACK_CANDLES:
            regimes[close_time] = _CandleRegime.unknown(close_time)
            continue
        window = ordered[index - _REGIME_LOOKBACK_CANDLES : index + 1]
        first_close = window[0].close
        last_close = window[-1].close
        trend_return = _ratio(last_close - first_close, first_close) if first_close != 0 else None
        if trend_return is None:
            trend_label = "unknown_or_insufficient_data"
        elif trend_return > _TREND_RETURN_THRESHOLD:
            trend_label = "uptrend"
        elif trend_return < -_TREND_RETURN_THRESHOLD:
            trend_label = "downtrend"
        else:
            trend_label = "sideways"

        abs_returns: list[Decimal] = []
        for previous, current in zip(window, window[1:], strict=False):
            if previous.close == 0:
                continue
            abs_return = _ratio(abs(current.close - previous.close), previous.close)
            if abs_return is not None:
                abs_returns.append(abs_return)
        avg_abs_return = (
            sum(abs_returns, Decimal("0")) / Decimal(len(abs_returns))
            if abs_returns
            else None
        )
        if avg_abs_return is None:
            volatility_label = "unknown_or_insufficient_data"
        elif avg_abs_return >= _HIGH_VOLATILITY_AVG_ABS_RETURN:
            volatility_label = "high_volatility"
        elif avg_abs_return <= _LOW_VOLATILITY_AVG_ABS_RETURN:
            volatility_label = "low_volatility"
        else:
            volatility_label = "normal_volatility"
        regimes[close_time] = _CandleRegime(
            close_time=close_time,
            trend_label=trend_label,
            volatility_label=volatility_label,
        )
    return regimes


def _regime_methodology() -> dict[str, Any]:
    return {
        "methodology": "deterministic_descriptive_labels_only_not_strategy_filters",
        "trade_assignment": "entry_signal_candle_regime",
        "trend_lookback_candles": _REGIME_LOOKBACK_CANDLES,
        "trend_return_threshold": _TREND_RETURN_THRESHOLD,
        "uptrend_rule": "lookback_return_above_positive_threshold",
        "downtrend_rule": "lookback_return_below_negative_threshold",
        "sideways_rule": "absolute_lookback_return_within_threshold",
        "volatility_rule": "average_absolute_close_to_close_return_over_lookback",
        "high_volatility_threshold": _HIGH_VOLATILITY_AVG_ABS_RETURN,
        "low_volatility_threshold": _LOW_VOLATILITY_AVG_ABS_RETURN,
        "insufficient_data_rule": "fewer_than_lookback_candles_available",
    }


def _build_regime_summaries(
    *,
    trades: list[StrategyValidationTrade],
    candles: list[Candle],
    regime_by_close_time: dict[datetime, _CandleRegime],
    start_at: datetime,
    end_at: datetime,
    no_trade_reason_counts_by_regime: dict[str, Counter[str]],
    invalid_reason_counts_by_regime: dict[str, Counter[str]],
) -> list[StrategyValidationRegimeSummary]:
    window_regimes = [
        regime_by_close_time.get(_coerce_utc(candle.close_time), _CandleRegime.unknown(_coerce_utc(candle.close_time)))
        for candle in candles
        if start_at < _coerce_utc(candle.close_time) <= end_at
    ]
    summaries: list[StrategyValidationRegimeSummary] = []
    summaries.extend(
        _summaries_for_regime_type(
            regime_type="trend",
            labels=[regime.trend_label for regime in window_regimes],
            trades=trades,
            trade_label_fn=lambda trade: trade.entry_market_regime,
            no_trade_reason_counts_by_regime=no_trade_reason_counts_by_regime,
            invalid_reason_counts_by_regime=invalid_reason_counts_by_regime,
        )
    )
    summaries.extend(
        _summaries_for_regime_type(
            regime_type="volatility",
            labels=[regime.volatility_label for regime in window_regimes],
            trades=trades,
            trade_label_fn=lambda trade: trade.entry_volatility_regime,
            no_trade_reason_counts_by_regime={},
            invalid_reason_counts_by_regime={},
        )
    )
    return sorted(summaries, key=lambda item: (item.regime_type, item.regime_label))


def _summaries_for_regime_type(
    *,
    regime_type: str,
    labels: list[str],
    trades: list[StrategyValidationTrade],
    trade_label_fn: Any,
    no_trade_reason_counts_by_regime: dict[str, Counter[str]],
    invalid_reason_counts_by_regime: dict[str, Counter[str]],
) -> list[StrategyValidationRegimeSummary]:
    candle_counts = Counter(labels)
    trade_labels = {label for label in candle_counts}
    trade_labels.update(trade_label_fn(trade) for trade in trades)
    summaries: list[StrategyValidationRegimeSummary] = []
    for label in sorted(trade_labels):
        regime_trades = [trade for trade in trades if trade_label_fn(trade) == label]
        wins = [trade for trade in regime_trades if trade.net_pnl > 0]
        net_pnl = _money(sum((trade.net_pnl for trade in regime_trades), Decimal("0")))
        adverse_values = [
            abs(trade.max_adverse_excursion)
            for trade in regime_trades
            if trade.max_adverse_excursion is not None and trade.max_adverse_excursion < 0
        ]
        summaries.append(
            StrategyValidationRegimeSummary(
                regime_type=regime_type,
                regime_label=label,
                candle_count=candle_counts.get(label, 0),
                evaluated_candle_count=candle_counts.get(label, 0),
                trade_count=len(regime_trades),
                net_pnl=net_pnl,
                win_rate=_ratio(Decimal(len(wins)), Decimal(len(regime_trades))),
                mark_to_market_max_drawdown=(
                    _money(max(adverse_values)) if adverse_values else Decimal("0")
                ),
                no_trade_reason_counts=dict(
                    sorted(no_trade_reason_counts_by_regime.get(label, Counter()).items())
                ),
                invalid_reason_counts=dict(
                    sorted(invalid_reason_counts_by_regime.get(label, Counter()).items())
                ),
            )
        )
    return summaries


def _resolve_fill(
    *,
    candles: list[Candle],
    signal_index: int,
    fill_timing: StrategyValidationFillTiming,
) -> _ResolvedFill | None:
    if fill_timing == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY:
        candle = candles[signal_index]
        return _ResolvedFill(
            candle=candle,
            raw_price=candle.close,
            time=_coerce_utc(candle.close_time),
            source="signal_candle_close",
        )
    next_index = signal_index + 1
    if next_index >= len(candles):
        return None
    candle = candles[next_index]
    if fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_OPEN:
        return _ResolvedFill(
            candle=candle,
            raw_price=candle.open,
            time=_coerce_utc(candle.open_time),
            source="next_candle_open",
        )
    if fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_CLOSE:
        return _ResolvedFill(
            candle=candle,
            raw_price=candle.close,
            time=_coerce_utc(candle.close_time),
            source="next_candle_close",
        )
    raise StrategyValidationError(f"Unsupported fill_timing: {fill_timing}")


def _entry_notional_for_assumptions(
    *,
    assumptions: StrategyValidationAssumptions,
    current_realized_equity: Decimal,
) -> Decimal:
    if (
        assumptions.capital_sizing_mode
        == StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE
    ):
        return _money(assumptions.initial_capital * assumptions.position_notional_pct)
    if assumptions.capital_sizing_mode == StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT:
        return _money(current_realized_equity * assumptions.position_notional_pct)
    raise StrategyValidationError(
        f"Unsupported capital_sizing_mode: {assumptions.capital_sizing_mode}"
    )


def _dynamic_equity_is_depleted(
    assumptions: StrategyValidationAssumptions,
    current_realized_equity: Decimal,
) -> bool:
    return (
        assumptions.capital_sizing_mode == StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
        and current_realized_equity <= 0
    )


def _open_trade(
    *,
    request: StrategyValidationRequest,
    sleeve: MoneyFlowSleeveConfig,
    fill: _ResolvedFill,
    entry_signal_time: datetime,
    entry_reason: str | None,
    entry_evaluation_key: str,
    entry_market_regime: str,
    entry_volatility_regime: str,
    current_realized_equity: Decimal,
) -> _SimulatedOpenPosition:
    slippage_rate = _bps_to_rate(request.assumptions.slippage_bps)
    fee_rate = _bps_to_rate(request.assumptions.fee_bps)
    raw_entry_price = fill.raw_price
    entry_price = _money(raw_entry_price * (Decimal("1") + slippage_rate))
    equity_before_entry = _money(current_realized_equity)
    entry_notional = _entry_notional_for_assumptions(
        assumptions=request.assumptions,
        current_realized_equity=equity_before_entry,
    )
    size = _quantity(entry_notional / entry_price)
    entry_fee = _money(entry_notional * fee_rate)
    entry_slippage_cost = _money((entry_price - raw_entry_price) * size)
    open_position = _SimulatedOpenPosition(
        component_key=sleeve.sleeve_id,
        timeframe=sleeve.timeframe,
        entry_time=fill.time,
        entry_signal_time=entry_signal_time,
        raw_entry_price=raw_entry_price,
        entry_price=entry_price,
        size=size,
        entry_notional=entry_notional,
        entry_fee=entry_fee,
        entry_slippage_cost=entry_slippage_cost,
        equity_before_entry=equity_before_entry,
        entry_reason=entry_reason,
        entry_evaluation_key=entry_evaluation_key,
        capital_sizing_mode=request.assumptions.capital_sizing_mode,
        position_notional_pct=request.assumptions.position_notional_pct,
        fill_timing=request.assumptions.fill_timing,
        entry_fill_source=fill.source,
        entry_market_regime=entry_market_regime,
        entry_volatility_regime=entry_volatility_regime,
    )
    return open_position


def _close_trade(
    *,
    request: StrategyValidationRequest,
    open_position: _SimulatedOpenPosition,
    fill: _ResolvedFill,
    exit_signal_time: datetime,
    exit_reason: str,
    exit_evaluation_key: str,
    exit_market_regime: str,
    exit_volatility_regime: str,
    forced_exit: bool,
) -> StrategyValidationTrade:
    slippage_rate = _bps_to_rate(request.assumptions.slippage_bps)
    fee_rate = _bps_to_rate(request.assumptions.fee_bps)
    raw_exit_price = fill.raw_price
    exit_price = _money(raw_exit_price * (Decimal("1") - slippage_rate))
    exit_notional = _money(exit_price * open_position.size)
    exit_fee = _money(exit_notional * fee_rate)
    exit_slippage_cost = _money((raw_exit_price - exit_price) * open_position.size)
    gross_pnl = _money((raw_exit_price - open_position.raw_entry_price) * open_position.size)
    fees = _money(open_position.entry_fee + exit_fee)
    slippage_cost = _money(open_position.entry_slippage_cost + exit_slippage_cost)
    net_pnl = _money(gross_pnl - fees - slippage_cost)
    return_pct = _ratio(net_pnl, open_position.entry_notional) or Decimal("0")
    equity_after_exit = _money(open_position.equity_before_entry + net_pnl)
    duration_seconds = int((fill.time - open_position.entry_time).total_seconds())
    trade_payload = {
        "component_key": open_position.component_key,
        "entry_time": open_position.entry_time.isoformat(),
        "exit_time": fill.time.isoformat(),
        "entry_evaluation_key": open_position.entry_evaluation_key,
        "exit_evaluation_key": exit_evaluation_key,
        "fill_timing": request.assumptions.fill_timing.value,
    }
    return StrategyValidationTrade(
        trade_id=f"svt-{_stable_hash(trade_payload)[:24]}",
        strategy_family=StrategyFamily.MONEY_FLOW,
        component_key=open_position.component_key,
        timeframe=open_position.timeframe,
        symbol=request.symbol,
        side=OrderSide.BUY,
        entry_time=open_position.entry_time,
        exit_time=fill.time,
        raw_entry_price=open_position.raw_entry_price,
        raw_exit_price=raw_exit_price,
        entry_price=open_position.entry_price,
        exit_price=exit_price,
        size=open_position.size,
        entry_notional=open_position.entry_notional,
        exit_notional=exit_notional,
        fees=fees,
        slippage_cost=slippage_cost,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        return_pct=return_pct,
        max_adverse_excursion=open_position.max_adverse_excursion,
        max_favorable_excursion=open_position.max_favorable_excursion,
        entry_reason=open_position.entry_reason,
        exit_reason=exit_reason,
        entry_evaluation_key=open_position.entry_evaluation_key,
        exit_evaluation_key=exit_evaluation_key,
        entry_signal_time=open_position.entry_signal_time,
        exit_signal_time=exit_signal_time,
        fill_timing=request.assumptions.fill_timing,
        entry_fill_source=open_position.entry_fill_source,
        exit_fill_source=fill.source,
        duration_seconds=duration_seconds,
        forced_exit=forced_exit,
        entry_market_regime=open_position.entry_market_regime,
        entry_volatility_regime=open_position.entry_volatility_regime,
        exit_market_regime=exit_market_regime,
        exit_volatility_regime=exit_volatility_regime,
        equity_before_entry=open_position.equity_before_entry,
        equity_after_exit=equity_after_exit,
        capital_sizing_mode=open_position.capital_sizing_mode,
        position_notional_pct=open_position.position_notional_pct,
    )


def _position_from_open_position(
    open_position: _SimulatedOpenPosition,
    *,
    request: StrategyValidationRequest,
    candle: Candle,
) -> Position:
    return Position(
        position_id=f"sv-pos-{open_position.position_state_fingerprint[:24]}",
        instrument_key=request.instrument_key or candle.instrument_key,
        instrument_ref_id=request.instrument_ref_id or candle.instrument_ref_id,
        venue_account_ref_id=None,
        sleeve_id=open_position.component_key,
        venue=request.venue,
        account_address=None,
        symbol=request.symbol,
        environment=request.environment,
        side=OrderSide.BUY,
        status=PositionStatus.OPEN,
        attribution_status=AttributionStatus.FULLY_ATTRIBUTED,
        venue_position_id=None,
        quantity=open_position.size,
        avg_entry_price=open_position.entry_price,
        mark_price=candle.close,
        unrealized_pnl=_money((candle.close - open_position.raw_entry_price) * open_position.size),
        opened_at=open_position.entry_time,
    )


def _build_metrics(
    *,
    trades: list[StrategyValidationTrade],
    initial_capital: Decimal,
    no_trade_reason_counts: dict[str, int],
    invalid_reason_counts: dict[str, int],
    closed_trade_equity_points: list[Decimal] | None = None,
    mark_to_market_equity_points: list[Decimal] | None = None,
    mark_to_market_drawdown_override: Decimal | None = None,
    mark_to_market_drawdown_pct_override: Decimal | None = None,
    capital_sizing_mode: StrategyValidationCapitalSizingMode | None = None,
    position_notional_pct: Decimal | None = None,
    trades_skipped_due_to_insufficient_equity: int = 0,
) -> StrategyValidationMetrics:
    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    gross_pnl = _money(sum((trade.gross_pnl for trade in trades), Decimal("0")))
    net_pnl = _money(sum((trade.net_pnl for trade in trades), Decimal("0")))
    total_fees = _money(sum((trade.fees for trade in trades), Decimal("0")))
    total_slippage_cost = _money(sum((trade.slippage_cost for trade in trades), Decimal("0")))
    winning_total = sum((trade.net_pnl for trade in wins), Decimal("0"))
    losing_total = sum((trade.net_pnl for trade in losses), Decimal("0"))
    if closed_trade_equity_points is None:
        closed_trade_equity_points = [initial_capital]
        equity = initial_capital
        for trade in trades:
            equity = _money(equity + trade.net_pnl)
            closed_trade_equity_points.append(equity)
    else:
        closed_trade_equity_points = [_money(point) for point in closed_trade_equity_points]
        if not closed_trade_equity_points:
            closed_trade_equity_points = [initial_capital]
    closed_trade_max_drawdown = _drawdown_from_equity_points(closed_trade_equity_points)
    ending_equity = closed_trade_equity_points[-1]
    minimum_realized_equity = min(closed_trade_equity_points)
    maximum_realized_equity = max(closed_trade_equity_points)
    mark_to_market_max_drawdown = mark_to_market_drawdown_override
    mark_to_market_max_drawdown_pct = mark_to_market_drawdown_pct_override
    if mark_to_market_equity_points is not None:
        mark_to_market_equity_points = [_money(point) for point in mark_to_market_equity_points]
    if mark_to_market_max_drawdown is None and mark_to_market_equity_points is not None:
        mark_to_market_max_drawdown = _drawdown_from_equity_points(mark_to_market_equity_points)
        mark_to_market_max_drawdown_pct = _ratio(mark_to_market_max_drawdown, initial_capital)
    if mark_to_market_max_drawdown is None:
        mark_to_market_max_drawdown = closed_trade_max_drawdown
        mark_to_market_max_drawdown_pct = _ratio(mark_to_market_max_drawdown, initial_capital)
    best_trade = max(trades, key=lambda trade: trade.net_pnl, default=None)
    worst_trade = min(trades, key=lambda trade: trade.net_pnl, default=None)
    duration_total = sum((Decimal(trade.duration_seconds) for trade in trades), Decimal("0"))
    trades_by_component_timeframe = Counter(
        f"{trade.component_key}:{trade.timeframe.value}" for trade in trades
    )
    return StrategyValidationMetrics(
        number_of_trades=len(trades),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=_ratio(Decimal(len(wins)), Decimal(len(trades))),
        loss_rate=_ratio(Decimal(len(losses)), Decimal(len(trades))),
        average_win=_ratio(winning_total, Decimal(len(wins))),
        average_loss=_ratio(losing_total, Decimal(len(losses))),
        profit_factor=_ratio(winning_total, abs(losing_total)),
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        total_fees=total_fees,
        total_slippage_cost=total_slippage_cost,
        max_drawdown=_money(closed_trade_max_drawdown),
        max_drawdown_pct=_ratio(closed_trade_max_drawdown, initial_capital),
        closed_trade_max_drawdown=_money(closed_trade_max_drawdown),
        closed_trade_max_drawdown_pct=_ratio(closed_trade_max_drawdown, initial_capital),
        mark_to_market_max_drawdown=_money(mark_to_market_max_drawdown),
        mark_to_market_max_drawdown_pct=mark_to_market_max_drawdown_pct,
        drawdown_methodology="closed_trade_and_mark_to_market",
        average_trade_duration_seconds=_ratio(duration_total, Decimal(len(trades))),
        best_trade_id=best_trade.trade_id if best_trade is not None else None,
        best_trade_net_pnl=best_trade.net_pnl if best_trade is not None else None,
        worst_trade_id=worst_trade.trade_id if worst_trade is not None else None,
        worst_trade_net_pnl=worst_trade.net_pnl if worst_trade is not None else None,
        return_on_initial_capital=_ratio(net_pnl, initial_capital) or Decimal("0"),
        trades_by_component_timeframe=dict(sorted(trades_by_component_timeframe.items())),
        no_trade_reason_counts=dict(sorted(no_trade_reason_counts.items())),
        invalid_reason_counts=dict(sorted(invalid_reason_counts.items())),
        starting_equity=_money(initial_capital),
        ending_equity=_money(ending_equity),
        net_account_pnl=_money(ending_equity - initial_capital),
        return_on_starting_equity=_ratio(ending_equity - initial_capital, initial_capital)
        or Decimal("0"),
        minimum_realized_equity=_money(minimum_realized_equity),
        maximum_realized_equity=_money(maximum_realized_equity),
        closed_trade_equity_curve=closed_trade_equity_points,
        mark_to_market_equity_curve=mark_to_market_equity_points or [],
        max_closed_trade_equity_drawdown=_money(closed_trade_max_drawdown),
        max_closed_trade_equity_drawdown_pct=_ratio(closed_trade_max_drawdown, initial_capital),
        max_mark_to_market_equity_drawdown=_money(mark_to_market_max_drawdown),
        max_mark_to_market_equity_drawdown_pct=mark_to_market_max_drawdown_pct,
        capital_sizing_mode=capital_sizing_mode,
        position_notional_pct=position_notional_pct,
        trades_skipped_due_to_insufficient_equity=trades_skipped_due_to_insufficient_equity,
    )


def _drawdown_from_equity_points(equity_points: list[Decimal]) -> Decimal:
    if not equity_points:
        return Decimal("0")
    peak = equity_points[0]
    max_drawdown = Decimal("0")
    for equity in equity_points:
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return _money(max_drawdown)


def _max_optional(values: Any) -> Decimal | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return max(present)


def _component_comparison(component_reports: list[StrategyValidationComponentReport]) -> dict[str, Any]:
    if not component_reports:
        return {
            "components_sorted": [],
            "highest_net_pnl_component": None,
            "most_trades_component": None,
            "best_win_rate_component": None,
            "worst_mark_to_market_drawdown_component": None,
            "methodology": "reporting_only_no_optimization_or_ranking_decision",
        }
    sorted_reports = sorted(component_reports, key=lambda report: (report.component_key, report.timeframe.value))

    def component_ref(report: StrategyValidationComponentReport) -> dict[str, Any]:
        return {
            "component_key": report.component_key,
            "timeframe": report.timeframe,
            "trade_count": report.metrics.number_of_trades,
            "net_pnl": report.metrics.net_pnl,
            "win_rate": report.metrics.win_rate,
            "mark_to_market_max_drawdown": report.metrics.mark_to_market_max_drawdown,
        }

    return {
        "components_sorted": [
            f"{report.component_key}:{report.timeframe.value}" for report in sorted_reports
        ],
        "highest_net_pnl_component": component_ref(
            max(sorted_reports, key=lambda report: report.metrics.net_pnl)
        ),
        "most_trades_component": component_ref(
            max(sorted_reports, key=lambda report: report.metrics.number_of_trades)
        ),
        "best_win_rate_component": component_ref(
            max(sorted_reports, key=lambda report: report.metrics.win_rate or Decimal("-1"))
        ),
        "worst_mark_to_market_drawdown_component": component_ref(
            max(
                sorted_reports,
                key=lambda report: report.metrics.mark_to_market_max_drawdown or Decimal("0"),
            )
        ),
        "methodology": "reporting_only_no_optimization_or_ranking_decision",
    }


def _data_coverage_summary(component_reports: list[StrategyValidationComponentReport]) -> dict[str, Any]:
    coverages = [
        report.data_coverage
        for report in component_reports
        if report.data_coverage is not None
    ]
    warning_codes = sorted(
        {
            warning
            for coverage in coverages
            for warning in coverage.warning_reason_codes
        }
    )
    coverage_percents = [
        coverage.coverage_percent
        for coverage in coverages
        if coverage.coverage_percent is not None
    ]
    return {
        "methodology": (
            "coverage_counts_candle_closes_after_requested_start_and_on_or_before_requested_end"
        ),
        "window_convention": _WINDOW_CONVENTION,
        "component_count": len(component_reports),
        "total_actual_candle_count": sum(coverage.actual_candle_count for coverage in coverages),
        "total_expected_candle_count": (
            sum(coverage.expected_candle_count for coverage in coverages)
            if all(coverage.expected_candle_count is not None for coverage in coverages)
            else None
        ),
        "minimum_coverage_percent": min(coverage_percents) if coverage_percents else None,
        "warning_reason_codes": warning_codes,
        "components": [
            {
                "component_key": report.component_key,
                "timeframe": report.timeframe,
                "coverage": report.data_coverage,
            }
            for report in component_reports
        ],
    }


def _regime_comparison(component_reports: list[StrategyValidationComponentReport]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[StrategyValidationRegimeSummary]] = {}
    for report in component_reports:
        for summary in report.regime_summaries:
            grouped.setdefault((summary.regime_type, summary.regime_label), []).append(summary)
    rows: list[dict[str, Any]] = []
    for (regime_type, regime_label), summaries in sorted(grouped.items()):
        trade_count = sum(summary.trade_count for summary in summaries)
        winning_estimate = Decimal("0")
        for summary in summaries:
            if summary.win_rate is not None:
                winning_estimate += Decimal(summary.trade_count) * summary.win_rate
        rows.append(
            {
                "regime_type": regime_type,
                "regime_label": regime_label,
                "component_count": len(summaries),
                "candle_count": sum(summary.candle_count for summary in summaries),
                "evaluated_candle_count": sum(summary.evaluated_candle_count for summary in summaries),
                "trade_count": trade_count,
                "net_pnl": _money(sum((summary.net_pnl for summary in summaries), Decimal("0"))),
                "win_rate": (
                    _ratio(winning_estimate, Decimal(trade_count)) if trade_count else None
                ),
                "largest_mark_to_market_drawdown": max(
                    (
                        summary.mark_to_market_max_drawdown
                        for summary in summaries
                        if summary.mark_to_market_max_drawdown is not None
                    ),
                    default=None,
                ),
            }
        )
    return {
        "methodology": "descriptive_regime_grouping_only_not_strategy_filtering",
        "trade_assignment": "entry_signal_candle_regime",
        "rows": rows,
    }


def _capital_sizing_metadata(assumptions: StrategyValidationAssumptions) -> dict[str, str]:
    starting_entry_notional = _entry_notional_for_assumptions(
        assumptions=assumptions,
        current_realized_equity=assumptions.initial_capital,
    )
    if (
        assumptions.capital_sizing_mode
        == StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE
    ):
        return {
            "capital_sizing_mode": assumptions.capital_sizing_mode.value,
            "entry_notional_formula": "initial_capital * position_notional_pct",
            "starting_entry_notional": str(starting_entry_notional),
            "entry_notional": str(starting_entry_notional),
            "equity_effect_on_next_trade_size": "none",
            "realized_equity_usage": "pnl_and_drawdown_accounting_only",
        }
    return {
        "capital_sizing_mode": assumptions.capital_sizing_mode.value,
        "entry_notional_formula": "current_realized_equity * position_notional_pct",
        "starting_entry_notional": str(starting_entry_notional),
        "entry_notional": "varies_by_trade_with_current_realized_equity",
        "equity_effect_on_next_trade_size": "wins_increase_next_notional_losses_reduce_next_notional",
        "realized_equity_usage": "pnl_drawdown_and_next_trade_sizing",
    }


def _request_payload(request: StrategyValidationRequest) -> dict[str, Any]:
    assumptions = _json_ready(asdict(request.assumptions))
    assumptions.update(_capital_sizing_metadata(request.assumptions))
    return {
        "strategy_family": request.strategy_family.value,
        "environment": request.environment.value,
        "venue": request.venue,
        "symbol": request.symbol,
        "instrument_key": request.instrument_key,
        "instrument_ref_id": request.instrument_ref_id,
        "component_keys": list(request.component_keys),
        "start_at": _coerce_utc(request.start_at).isoformat(),
        "end_at": _coerce_utc(request.end_at).isoformat(),
        "assumptions": assumptions,
    }


def _run_summary(run: StrategyValidationBatchRunReport) -> dict[str, Any]:
    request = run.request
    summary: dict[str, Any] = {
        "run_id": run.run_id,
        "run_index": run.run_index,
        "status": run.status,
        "report_id": run.report_id,
        "component_keys": list(request.component_keys),
        "fill_timing": request.assumptions.fill_timing,
        "venue": request.venue,
        "symbol": request.symbol,
        "instrument_key": request.instrument_key,
        "instrument_ref_id": request.instrument_ref_id,
        "start_at": _coerce_utc(request.start_at),
        "end_at": _coerce_utc(request.end_at),
        "fee_bps": request.assumptions.fee_bps,
        "slippage_bps": request.assumptions.slippage_bps,
        "initial_capital": request.assumptions.initial_capital,
        "position_notional_pct": request.assumptions.position_notional_pct,
        "capital_sizing_mode": request.assumptions.capital_sizing_mode,
        "starting_entry_notional": _entry_notional_for_assumptions(
            assumptions=request.assumptions,
            current_realized_equity=request.assumptions.initial_capital,
        ),
        "reason_codes": list(run.reason_codes),
        "error_message": run.error_message,
    }
    if run.report is None:
        summary["metrics"] = None
        summary["data_coverage_summary"] = {}
        summary["regime_comparison"] = {}
        summary["limitations"] = []
        return summary
    metrics = run.report.aggregate_metrics
    summary["metrics"] = {
        "number_of_trades": metrics.number_of_trades,
        "win_rate": metrics.win_rate,
        "loss_rate": metrics.loss_rate,
        "net_pnl": metrics.net_pnl,
        "profit_factor": metrics.profit_factor,
        "closed_trade_max_drawdown": metrics.closed_trade_max_drawdown,
        "mark_to_market_max_drawdown": metrics.mark_to_market_max_drawdown,
        "total_fees": metrics.total_fees,
        "total_slippage_cost": metrics.total_slippage_cost,
        "return_on_initial_capital": metrics.return_on_initial_capital,
        "starting_equity": metrics.starting_equity,
        "ending_equity": metrics.ending_equity,
        "net_account_pnl": metrics.net_account_pnl,
        "return_on_starting_equity": metrics.return_on_starting_equity,
        "minimum_realized_equity": metrics.minimum_realized_equity,
        "maximum_realized_equity": metrics.maximum_realized_equity,
        "max_closed_trade_equity_drawdown": metrics.max_closed_trade_equity_drawdown,
        "max_mark_to_market_equity_drawdown": metrics.max_mark_to_market_equity_drawdown,
        "trades_skipped_due_to_insufficient_equity": (
            metrics.trades_skipped_due_to_insufficient_equity
        ),
        "best_trade_id": metrics.best_trade_id,
        "worst_trade_id": metrics.worst_trade_id,
        "no_trade_reason_counts": metrics.no_trade_reason_counts,
        "invalid_reason_counts": metrics.invalid_reason_counts,
    }
    summary["limitations"] = list(run.report.limitations)
    summary["data_coverage_summary"] = run.report.data_coverage_summary
    summary["regime_comparison"] = run.report.regime_comparison
    return summary


def _assumptions_matrix(run_reports: list[StrategyValidationBatchRunReport]) -> dict[str, Any]:
    requests = [run.request for run in run_reports]
    return {
        "window_convention": _WINDOW_CONVENTION,
        "components": sorted(
            {
                component
                for request in requests
                for component in (request.component_keys or ("all",))
            }
        ),
        "fill_timings": sorted({request.assumptions.fill_timing.value for request in requests}),
        "venues": sorted({request.venue for request in requests}),
        "symbols": sorted({request.symbol for request in requests}),
        "instrument_keys": sorted(
            {request.instrument_key for request in requests if request.instrument_key is not None}
        ),
        "date_windows": sorted(
            {
                f"{_coerce_utc(request.start_at).isoformat()}->{_coerce_utc(request.end_at).isoformat()}"
                for request in requests
            }
        ),
        "fee_bps_values": sorted({str(request.assumptions.fee_bps) for request in requests}),
        "slippage_bps_values": sorted(
            {str(request.assumptions.slippage_bps) for request in requests}
        ),
        "initial_capital_values": sorted(
            {str(request.assumptions.initial_capital) for request in requests}
        ),
        "position_notional_pct_values": sorted(
            {str(request.assumptions.position_notional_pct) for request in requests}
        ),
        "capital_sizing_modes": sorted(
            {request.assumptions.capital_sizing_mode.value for request in requests}
        ),
        "entry_notional_formulas": sorted(
            {
                _capital_sizing_metadata(request.assumptions)["entry_notional_formula"]
                for request in requests
            }
        ),
    }


def _comparison_summary(run_reports: list[StrategyValidationBatchRunReport]) -> dict[str, Any]:
    summaries = [_run_summary(run) for run in run_reports]
    completed = [run for run in run_reports if run.report is not None]
    return {
        "methodology": "descriptive_research_reporting_only_no_parameter_optimization_or_recommendation",
        "run_summaries": summaries,
        "highest_observed_net_pnl_run": _select_run(completed, "net_pnl", highest=True),
        "lowest_observed_net_pnl_run": _select_run(completed, "net_pnl", highest=False),
        "highest_observed_win_rate_run": _select_run(completed, "win_rate", highest=True),
        "largest_observed_mark_to_market_drawdown_run": _select_run(
            completed,
            "mark_to_market_max_drawdown",
            highest=True,
        ),
        "most_trades_run": _select_run(completed, "number_of_trades", highest=True),
        "least_trades_run": _select_run(completed, "number_of_trades", highest=False),
        "fill_timing_comparison": _group_comparison(
            run_reports,
            lambda run: run.request.assumptions.fill_timing.value,
            "fill_timing",
        ),
        "component_comparison": _group_comparison(
            run_reports,
            lambda run: ",".join(run.request.component_keys or ("all",)),
            "component_keys",
        ),
        "symbol_comparison": _group_comparison(run_reports, lambda run: run.request.symbol, "symbol"),
        "date_window_comparison": _group_comparison(
            run_reports,
            lambda run: (
                f"{_coerce_utc(run.request.start_at).isoformat()}->"
                f"{_coerce_utc(run.request.end_at).isoformat()}"
            ),
            "date_window",
        ),
        "regime_comparison": _batch_regime_comparison(completed),
        "data_coverage_comparison": _batch_data_coverage_comparison(completed),
    }


def _select_run(
    run_reports: list[StrategyValidationBatchRunReport],
    metric_name: str,
    *,
    highest: bool,
) -> dict[str, Any] | None:
    metric_runs = [
        run
        for run in run_reports
        if run.report is not None and _metric_value(run.report.aggregate_metrics, metric_name) is not None
    ]
    if not metric_runs:
        return None
    selected = max(
        metric_runs,
        key=lambda run: _metric_value(run.report.aggregate_metrics, metric_name),  # type: ignore[union-attr]
    )
    if not highest:
        selected = min(
            metric_runs,
            key=lambda run: _metric_value(run.report.aggregate_metrics, metric_name),  # type: ignore[union-attr]
        )
    return _selected_run_ref(selected, metric_name)


def _selected_run_ref(run: StrategyValidationBatchRunReport, metric_name: str) -> dict[str, Any]:
    assert run.report is not None
    return {
        "run_id": run.run_id,
        "report_id": run.report.report_id,
        "component_keys": list(run.request.component_keys),
        "fill_timing": run.request.assumptions.fill_timing,
        "venue": run.request.venue,
        "symbol": run.request.symbol,
        "start_at": _coerce_utc(run.request.start_at),
        "end_at": _coerce_utc(run.request.end_at),
        "metric_name": metric_name,
        "metric_value": _metric_value(run.report.aggregate_metrics, metric_name),
    }


def _group_comparison(
    run_reports: list[StrategyValidationBatchRunReport],
    key_fn: Any,
    label: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[StrategyValidationBatchRunReport]] = {}
    for run in run_reports:
        grouped.setdefault(str(key_fn(run)), []).append(run)
    rows: list[dict[str, Any]] = []
    for value, runs in sorted(grouped.items()):
        metrics = [run.report.aggregate_metrics for run in runs if run.report is not None]
        blocked_reason_counts: Counter[str] = Counter()
        for run in runs:
            if run.report is None:
                blocked_reason_counts.update(run.reason_codes or ["strategy_validation_run_blocked"])
        run_count = len(runs)
        total_net_pnl = _money(sum((metric.net_pnl for metric in metrics), Decimal("0")))
        total_trades = sum(metric.number_of_trades for metric in metrics)
        total_fees = _money(sum((metric.total_fees for metric in metrics), Decimal("0")))
        total_slippage = _money(
            sum((metric.total_slippage_cost for metric in metrics), Decimal("0"))
        )
        average_net_pnl = _ratio(total_net_pnl, Decimal(len(metrics))) if metrics else None
        max_mtm_drawdown_values = [
            metric.mark_to_market_max_drawdown
            for metric in metrics
            if metric.mark_to_market_max_drawdown is not None
        ]
        rows.append(
            {
                label: value,
                "run_count": run_count,
                "scenario_count": run_count,
                "completed_run_count": len(metrics),
                "blocked_run_count": run_count - len(metrics),
                "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
                "total_trades": total_trades,
                "sum_trades_across_research_runs": total_trades,
                "total_net_pnl": total_net_pnl,
                "sum_net_pnl_across_research_runs": total_net_pnl,
                "average_net_pnl": average_net_pnl,
                "average_net_pnl_per_completed_run": average_net_pnl,
                "total_fees": total_fees,
                "sum_fees_across_research_runs": total_fees,
                "total_slippage_cost": total_slippage,
                "sum_slippage_cost_across_research_runs": total_slippage,
                "largest_mark_to_market_drawdown": (
                    max(max_mtm_drawdown_values) if max_mtm_drawdown_values else None
                ),
                "run_ids": [run.run_id for run in runs],
            }
        )
    return rows


def _batch_regime_comparison(
    run_reports: list[StrategyValidationBatchRunReport],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in run_reports:
        if run.report is None:
            continue
        rows = run.report.regime_comparison.get("rows", [])
        for row in rows:
            grouped.setdefault((row["regime_type"], row["regime_label"]), []).append(row)
    output: list[dict[str, Any]] = []
    for (regime_type, regime_label), rows in sorted(grouped.items()):
        trade_count = sum(row["trade_count"] for row in rows)
        winning_estimate = Decimal("0")
        for row in rows:
            if row["win_rate"] is not None:
                winning_estimate += Decimal(row["trade_count"]) * row["win_rate"]
        drawdowns = [
            row["largest_mark_to_market_drawdown"]
            for row in rows
            if row["largest_mark_to_market_drawdown"] is not None
        ]
        output.append(
            {
                "regime_type": regime_type,
                "regime_label": regime_label,
                "run_count": len(rows),
                "total_trades": trade_count,
                "scenario_count": len(rows),
                "total_net_pnl": _money(sum((row["net_pnl"] for row in rows), Decimal("0"))),
                "sum_trades_across_research_runs": trade_count,
                "sum_net_pnl_across_research_runs": _money(
                    sum((row["net_pnl"] for row in rows), Decimal("0"))
                ),
                "win_rate": _ratio(winning_estimate, Decimal(trade_count)) if trade_count else None,
                "largest_mark_to_market_drawdown": max(drawdowns) if drawdowns else None,
            }
        )
    return output


def _batch_data_coverage_comparison(
    run_reports: list[StrategyValidationBatchRunReport],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in run_reports:
        if run.report is None:
            continue
        coverage = run.report.data_coverage_summary
        rows.append(
            {
                "run_id": run.run_id,
                "report_id": run.report.report_id,
                "component_keys": list(run.request.component_keys),
                "symbol": run.request.symbol,
                "date_window": (
                    f"{_coerce_utc(run.request.start_at).isoformat()}->"
                    f"{_coerce_utc(run.request.end_at).isoformat()}"
                ),
                "minimum_coverage_percent": coverage.get("minimum_coverage_percent"),
                "total_actual_candle_count": coverage.get("total_actual_candle_count"),
                "total_expected_candle_count": coverage.get("total_expected_candle_count"),
                "warning_reason_codes": coverage.get("warning_reason_codes", []),
            }
        )
    return rows


def _metric_value(metrics: StrategyValidationMetrics, metric_name: str) -> Any:
    return getattr(metrics, metric_name)


def _batch_warnings(run_reports: list[StrategyValidationBatchRunReport]) -> list[str]:
    warnings = [
        "comparisons_are_descriptive_research_outputs_not_strategy_recommendations",
        "results_do_not_prove_future_profitability",
        "simulated_trades_are_not_submitted_orders",
        "batch_runner_creates_no_live_trading_artifacts",
    ]
    if any(
        run.request.assumptions.fill_timing
        == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY
        for run in run_reports
    ):
        warnings.append("same_candle_close_runs_are_research_only_and_can_overstate_edge")
    if any(run.status != "completed" for run in run_reports):
        warnings.append("blocked_runs_are_reported_per_run_and_not_hidden")
    if any(
        run.report is not None
        and run.report.data_coverage_summary.get("warning_reason_codes")
        for run in run_reports
    ):
        warnings.append("one_or_more_runs_have_data_coverage_warnings")
    return sorted(set(warnings))


def strategy_validation_report_to_dict(report: StrategyValidationReport) -> dict[str, Any]:
    data = _json_ready(asdict(report))
    data["assumptions"].update(_capital_sizing_metadata(report.assumptions))
    return data


def strategy_validation_batch_report_to_dict(report: StrategyValidationBatchReport) -> dict[str, Any]:
    return _json_ready(asdict(report))


def strategy_validation_batch_report_to_markdown(report: StrategyValidationBatchReport) -> str:
    data = strategy_validation_batch_report_to_dict(report)
    summary = data["comparison_summary"]
    lines = [
        f"# Money Flow Strategy Validation Batch Report `{data['batch_id']}`",
        "",
        "This is a comparative research report. It is not optimization, does not recommend a "
        "strategy variant, does not create live trading artifacts, and does not prove future profitability.",
        "",
        "## Batch Context",
        "",
        f"- Batch id: `{data['batch_id']}`",
        f"- Batch name: `{data['batch_name']}`",
        f"- Strategy family: `{data['strategy_family']}`",
        f"- Run count: `{len(data['run_reports'])}`",
        f"- Live execution artifacts created: `{not data['no_live_execution_artifacts_created']}`",
        f"- Exchange adapters called: `{data['exchange_adapters_called']}`",
        "",
        "## Assumptions Matrix",
        "",
    ]
    for key, value in data["assumptions_matrix"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "Capital sizing note: `constant_initial_capital_notional_per_trade` sizes every "
            "opened trade from `initial_capital * position_notional_pct`. "
            "In that mode, realized equity changes PnL and drawdown metrics but does not "
            "compound, shrink, or stop subsequent trade notional. "
            "`dynamic_equity_pct` sizes each new trade from current realized equity after prior "
            "closed-trade net PnL. Dynamic equity is per scenario and is still not full "
            "exchange margin, liquidation, funding, or portfolio simulation.",
            "",
            "## Grouped Aggregate Semantics",
            "",
            "Grouped comparison rows are descriptive aggregates across completed research runs in the group. "
            "`sum_net_pnl_across_research_runs`, `sum_trades_across_research_runs`, fees, and slippage "
            "costs are summed across separate symbol, fill-timing, fee, slippage, and window scenarios. "
            "They are not one tradable account result and should not be read as single-scenario strategy PnL.",
            "",
            "`average_net_pnl_per_completed_run` is the mean across completed runs in that group. "
            "Use scenario-level rows for assumption-specific interpretation and manual review.",
        ]
    )
    lines.extend(
        [
            "",
            "## Run Summary",
            "",
            "| run id | status | components | sizing | fill timing | venue | symbol | window | trades | net PnL | ending equity | win rate | profit factor | MTM drawdown | fees | slippage | limitations |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in summary["run_summaries"]:
        metrics = run["metrics"] or {}
        lines.append(
            "| "
            f"`{run['run_id']}` | "
            f"`{run['status']}` | "
            f"`{', '.join(run['component_keys'])}` | "
            f"`{run.get('capital_sizing_mode', 'constant_initial_capital_notional_per_trade')}` | "
            f"`{run['fill_timing']}` | "
            f"`{run['venue']}` | "
            f"`{run['symbol']}` | "
            f"`{run['start_at']} -> {run['end_at']}` | "
            f"{metrics.get('number_of_trades', '-')} | "
            f"{metrics.get('net_pnl', '-')} | "
            f"{metrics.get('ending_equity', '-')} | "
            f"{metrics.get('win_rate', '-')} | "
            f"{metrics.get('profit_factor', '-')} | "
            f"{metrics.get('mark_to_market_max_drawdown', '-')} | "
            f"{metrics.get('total_fees', '-')} | "
            f"{metrics.get('total_slippage_cost', '-')} | "
            f"{', '.join(run['limitations']) or run['error_message'] or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Data-Coverage Comparison",
            "",
            "| run id | components | symbol | date window | actual candles | expected candles | minimum coverage % | warnings |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary["data_coverage_comparison"]:
        lines.append(
            "| "
            f"`{row['run_id']}` | "
            f"`{', '.join(row['component_keys'])}` | "
            f"`{row['symbol']}` | "
            f"`{row['date_window']}` | "
            f"{row['total_actual_candle_count']} | "
            f"{row['total_expected_candle_count']} | "
            f"{row['minimum_coverage_percent']} | "
            f"`{row['warning_reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Market-Regime Comparison",
            "",
            "Regimes are deterministic descriptive labels only. They are not strategy filters, optimization inputs, or recommendations.",
            "",
            "| regime type | label | scenario count | sum trades across research runs | sum net PnL across research runs | win rate | largest MTM drawdown |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["regime_comparison"]:
        lines.append(
            "| "
            f"`{row['regime_type']}` | "
            f"`{row['regime_label']}` | "
            f"{row.get('scenario_count', row['run_count'])} | "
            f"{row.get('sum_trades_across_research_runs', row['total_trades'])} | "
            f"{row.get('sum_net_pnl_across_research_runs', row['total_net_pnl'])} | "
            f"{row['win_rate']} | "
            f"{row['largest_mark_to_market_drawdown']} |"
        )
    lines.extend(
        [
            "",
            "## Fill-Timing Comparison",
            "",
            "| fill timing | scenario count | completed | blocked | blocked reasons | sum trades across research runs | sum net PnL across research runs | average net PnL per completed run | largest MTM drawdown |",
            "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["fill_timing_comparison"]:
        lines.append(
            "| "
            f"`{row['fill_timing']}` | "
            f"{row.get('scenario_count', row['run_count'])} | "
            f"{row['completed_run_count']} | "
            f"{row['blocked_run_count']} | "
            f"`{row['blocked_reason_counts']}` | "
            f"{row.get('sum_trades_across_research_runs', row['total_trades'])} | "
            f"{row.get('sum_net_pnl_across_research_runs', row['total_net_pnl'])} | "
            f"{row.get('average_net_pnl_per_completed_run', row['average_net_pnl'])} | "
            f"{row['largest_mark_to_market_drawdown']} |"
        )
    lines.extend(
        [
            "",
            "## Component Comparison",
            "",
            "| component(s) | scenario count | completed | blocked | blocked reasons | sum trades across research runs | sum net PnL across research runs | average net PnL per completed run | largest MTM drawdown |",
            "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["component_comparison"]:
        lines.append(
            "| "
            f"`{row['component_keys']}` | "
            f"{row.get('scenario_count', row['run_count'])} | "
            f"{row['completed_run_count']} | "
            f"{row['blocked_run_count']} | "
            f"`{row['blocked_reason_counts']}` | "
            f"{row.get('sum_trades_across_research_runs', row['total_trades'])} | "
            f"{row.get('sum_net_pnl_across_research_runs', row['total_net_pnl'])} | "
            f"{row.get('average_net_pnl_per_completed_run', row['average_net_pnl'])} | "
            f"{row['largest_mark_to_market_drawdown']} |"
        )
    if len(data["assumptions_matrix"]["symbols"]) > 1:
        lines.extend(
            [
                "",
                "## Symbol Comparison",
                "",
                "| symbol | scenario count | completed | blocked | blocked reasons | sum trades across research runs | sum net PnL across research runs | average net PnL per completed run | largest MTM drawdown |",
                "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summary["symbol_comparison"]:
            lines.append(
                "| "
                f"`{row['symbol']}` | "
                f"{row.get('scenario_count', row['run_count'])} | "
                f"{row['completed_run_count']} | "
                f"{row['blocked_run_count']} | "
                f"`{row['blocked_reason_counts']}` | "
                f"{row.get('sum_trades_across_research_runs', row['total_trades'])} | "
                f"{row.get('sum_net_pnl_across_research_runs', row['total_net_pnl'])} | "
                f"{row.get('average_net_pnl_per_completed_run', row['average_net_pnl'])} | "
                f"{row['largest_mark_to_market_drawdown']} |"
            )
    if len(data["assumptions_matrix"]["date_windows"]) > 1:
        lines.extend(
            [
                "",
                "## Date-Window Comparison",
                "",
                "| date window | scenario count | completed | blocked | blocked reasons | sum trades across research runs | sum net PnL across research runs | average net PnL per completed run | largest MTM drawdown |",
                "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summary["date_window_comparison"]:
            lines.append(
                "| "
                f"`{row['date_window']}` | "
                f"{row.get('scenario_count', row['run_count'])} | "
                f"{row['completed_run_count']} | "
                f"{row['blocked_run_count']} | "
                f"`{row['blocked_reason_counts']}` | "
                f"{row.get('sum_trades_across_research_runs', row['total_trades'])} | "
                f"{row.get('sum_net_pnl_across_research_runs', row['total_net_pnl'])} | "
                f"{row.get('average_net_pnl_per_completed_run', row['average_net_pnl'])} | "
                f"{row['largest_mark_to_market_drawdown']} |"
            )
    lines.extend(
        [
            "",
            "## Top/Bottom Observed Runs",
            "",
            f"- Highest observed net PnL: `{summary['highest_observed_net_pnl_run']}`",
            f"- Lowest observed net PnL: `{summary['lowest_observed_net_pnl_run']}`",
            f"- Highest observed win rate: `{summary['highest_observed_win_rate_run']}`",
            "- Largest observed mark-to-market drawdown: "
            f"`{summary['largest_observed_mark_to_market_drawdown_run']}`",
            f"- Most active run by trade count: `{summary['most_trades_run']}`",
            f"- Least active run by trade count: `{summary['least_trades_run']}`",
            "",
            "## Warnings And Limitations",
            "",
        ]
    )
    lines.extend(f"- `{warning}`" for warning in data["warnings"])
    lines.extend(f"- `{limitation}`" for limitation in data["limitations"])
    if not data["limitations"]:
        lines.append("- `none_recorded_beyond_standard_research_limitations`")
    return "\n".join(lines) + "\n"


def strategy_validation_report_to_markdown(report: StrategyValidationReport) -> str:
    data = strategy_validation_report_to_dict(report)
    metrics = data["aggregate_metrics"]
    assumptions = data["assumptions"]
    lines = [
        f"# Money Flow Strategy Validation Report `{data['report_id']}`",
        "",
        "This is a research-only validation report. It is not live execution, "
        "does not create `SubmittedOrder` records, and does not prove future profitability.",
        "",
        "## Report Context",
        "",
        f"- Report id: `{data['report_id']}`",
        f"- Strategy family: `{data['strategy_family']}`",
        f"- Environment: `{data['environment']}`",
        f"- Venue/source: `{data['venue']}`",
        f"- Symbol: `{data['symbol']}`",
        f"- Instrument key: `{data['instrument_key']}`",
        f"- Instrument ref id: `{data['instrument_ref_id']}`",
        f"- Date range: `{data['start_at']}` to `{data['end_at']}`",
        f"- Components: `{', '.join(component['component_key'] for component in data['component_reports'])}`",
        "",
        "## Assumptions",
        "",
        f"- Initial capital: `{assumptions['initial_capital']}`",
        f"- Fee bps: `{assumptions['fee_bps']}`",
        f"- Slippage bps: `{assumptions['slippage_bps']}`",
        f"- Fill timing: `{assumptions['fill_timing']}`",
        f"- Position notional pct: `{assumptions['position_notional_pct']}`",
        f"- Capital sizing mode: `{assumptions['capital_sizing_mode']}`",
        f"- Entry notional formula: `{assumptions['entry_notional_formula']}`",
        f"- Starting entry notional: `{assumptions['starting_entry_notional']}`",
        f"- Entry notional per opened trade: `{assumptions['entry_notional']}`",
        f"- Equity effect on next trade size: `{assumptions['equity_effect_on_next_trade_size']}`",
        f"- Realized equity usage: `{assumptions['realized_equity_usage']}`",
        f"- Reduce action model: `{assumptions['reduce_action_model']}`",
        f"- Force-close open trade at end: `{assumptions['force_close_open_trade_at_end']}`",
        f"- Drawdown methodology: `{assumptions['drawdown_methodology']}`",
        "",
        "## Data Coverage",
        "",
        f"- Methodology: `{data['data_coverage_summary'].get('methodology')}`",
        f"- Window convention: `{data['data_coverage_summary'].get('window_convention')}`",
        f"- Total actual candles: `{data['data_coverage_summary'].get('total_actual_candle_count')}`",
        f"- Total expected candles: `{data['data_coverage_summary'].get('total_expected_candle_count')}`",
        f"- Minimum coverage percent: `{data['data_coverage_summary'].get('minimum_coverage_percent')}`",
        f"- Warning reason codes: `{data['data_coverage_summary'].get('warning_reason_codes')}`",
        "",
        "| component | timeframe | requested start | requested end | first candle | last candle | expected | actual | missing | coverage % | gaps | largest gap seconds | warnings |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for component in data["component_reports"]:
        coverage = component["data_coverage"] or {}
        lines.append(
            "| "
            f"`{component['component_key']}` | "
            f"`{component['timeframe']}` | "
            f"`{coverage.get('requested_start_at')}` | "
            f"`{coverage.get('requested_end_at')}` | "
            f"`{coverage.get('first_candle_available_at')}` | "
            f"`{coverage.get('last_candle_available_at')}` | "
            f"{coverage.get('expected_candle_count')} | "
            f"{coverage.get('actual_candle_count')} | "
            f"{coverage.get('missing_candle_count')} | "
            f"{coverage.get('coverage_percent')} | "
            f"{coverage.get('gap_count')} | "
            f"{coverage.get('largest_gap_seconds')} | "
            f"`{coverage.get('warning_reason_codes')}` |"
        )
    lines.extend(
        [
            "",
            "## Market-Regime Methodology",
            "",
            "- Regimes are deterministic descriptive labels only; they are not strategy filters.",
            "- Trade-level performance is assigned by the entry signal candle regime.",
            f"- Methodology: `{data['regime_comparison'].get('methodology')}`",
            f"- Trade assignment: `{data['regime_comparison'].get('trade_assignment')}`",
            "",
            "## Regime Performance",
            "",
            "| regime type | label | candles | evaluated | trades | net PnL | win rate | MTM drawdown |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in data["regime_comparison"].get("rows", []):
        lines.append(
            "| "
            f"`{row['regime_type']}` | "
            f"`{row['regime_label']}` | "
            f"{row['candle_count']} | "
            f"{row['evaluated_candle_count']} | "
            f"{row['trade_count']} | "
            f"{row['net_pnl']} | "
            f"{row['win_rate']} | "
            f"{row['largest_mark_to_market_drawdown']} |"
        )
    lines.extend(
        [
            "",
        "## Aggregate Metrics",
        "",
        f"- Trades: `{metrics['number_of_trades']}`",
        f"- Win rate: `{metrics['win_rate']}`",
        f"- Loss rate: `{metrics['loss_rate']}`",
        f"- Average win: `{metrics['average_win']}`",
        f"- Average loss: `{metrics['average_loss']}`",
        f"- Profit factor: `{metrics['profit_factor']}`",
        f"- Net PnL: `{metrics['net_pnl']}`",
        f"- Gross PnL: `{metrics['gross_pnl']}`",
        f"- Fees: `{metrics['total_fees']}`",
        f"- Slippage cost: `{metrics['total_slippage_cost']}`",
        f"- Closed-trade max drawdown: `{metrics['closed_trade_max_drawdown']}`",
        f"- Closed-trade max drawdown pct: `{metrics['closed_trade_max_drawdown_pct']}`",
        f"- Mark-to-market max drawdown: `{metrics['mark_to_market_max_drawdown']}`",
        f"- Mark-to-market max drawdown pct: `{metrics['mark_to_market_max_drawdown_pct']}`",
        f"- Average trade duration seconds: `{metrics['average_trade_duration_seconds']}`",
        f"- Best trade: `{metrics['best_trade_id']}` / `{metrics['best_trade_net_pnl']}`",
        f"- Worst trade: `{metrics['worst_trade_id']}` / `{metrics['worst_trade_net_pnl']}`",
        f"- Return on initial capital: `{metrics['return_on_initial_capital']}`",
        f"- Starting equity: `{metrics['starting_equity']}`",
        f"- Ending equity: `{metrics['ending_equity']}`",
        f"- Net account PnL: `{metrics['net_account_pnl']}`",
        f"- Return on starting equity: `{metrics['return_on_starting_equity']}`",
        f"- Minimum realized equity: `{metrics['minimum_realized_equity']}`",
        f"- Maximum realized equity: `{metrics['maximum_realized_equity']}`",
        f"- Trades skipped due to insufficient equity: `{metrics['trades_skipped_due_to_insufficient_equity']}`",
        "",
        "## Component Comparison",
        "",
        f"- Highest net PnL component: `{data['component_comparison']['highest_net_pnl_component']}`",
        f"- Most trades component: `{data['component_comparison']['most_trades_component']}`",
        f"- Best win rate component: `{data['component_comparison']['best_win_rate_component']}`",
        f"- Worst mark-to-market drawdown component: "
        f"`{data['component_comparison']['worst_mark_to_market_drawdown_component']}`",
        f"- Methodology: `{data['component_comparison']['methodology']}`",
        "",
        "## Component Metrics",
        "",
            "| component | timeframe | candles | evaluated | trades | net PnL | win rate | loss rate | profit factor | closed DD | MTM DD | return | limitations |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for component in data["component_reports"]:
        component_metrics = component["metrics"]
        lines.append(
            "| "
            f"`{component['component_key']}` | "
            f"`{component['timeframe']}` | "
            f"{component['candle_count']} | "
            f"{component['evaluated_candles']} | "
            f"{component_metrics['number_of_trades']} | "
            f"{component_metrics['net_pnl']} | "
            f"{component_metrics['win_rate']} | "
            f"{component_metrics['loss_rate']} | "
            f"{component_metrics['profit_factor']} | "
            f"{component_metrics['closed_trade_max_drawdown']} | "
            f"{component_metrics['mark_to_market_max_drawdown']} | "
            f"{component_metrics['return_on_initial_capital']} | "
            f"{', '.join(component['limitations']) or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Trade Summary",
            "",
            "| trade id | component | timeframe | entry time | exit time | sizing | equity before | equity after | entry notional | entry regime | entry volatility | side | entry price | exit price | net PnL | return % | entry reason | exit reason | forced exit |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    trades = [
        trade
        for component in data["component_reports"]
        for trade in component["trades"]
    ]
    if trades:
        for trade in trades:
            lines.append(
                "| "
                f"`{trade['trade_id']}` | "
                f"`{trade['component_key']}` | "
                f"`{trade['timeframe']}` | "
                f"`{trade['entry_time']}` | "
                f"`{trade['exit_time']}` | "
                f"`{trade['capital_sizing_mode']}` | "
                f"{trade['equity_before_entry']} | "
                f"{trade['equity_after_exit']} | "
                f"{trade['entry_notional']} | "
                f"`{trade['entry_market_regime']}` | "
                f"`{trade['entry_volatility_regime']}` | "
                f"`{trade['side']}` | "
                f"{trade['entry_price']} | "
                f"{trade['exit_price']} | "
                f"{trade['net_pnl']} | "
                f"{trade['return_pct']} | "
                f"`{trade['entry_reason']}` | "
                f"`{trade['exit_reason']}` | "
                f"`{trade['forced_exit']}` |"
            )
    else:
        lines.append("| none | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Reason Counts",
            "",
            "### No-Trade Reasons",
            "",
        ]
    )
    if metrics["no_trade_reason_counts"]:
        lines.extend(
            f"- `{reason}`: `{count}`"
            for reason, count in metrics["no_trade_reason_counts"].items()
        )
    else:
        lines.append("- None recorded.")
    lines.extend(["", "### Invalid Reasons", ""])
    if metrics["invalid_reason_counts"]:
        lines.extend(
            f"- `{reason}`: `{count}`"
            for reason, count in metrics["invalid_reason_counts"].items()
        )
    else:
        lines.append("- None recorded.")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Results are research-only and do not prove future profitability.",
            "- Simulated trades are not live execution artifacts and are not `SubmittedOrder` rows.",
            "- No order book replay, funding, liquidation, partial-fill, or venue-latency model is included.",
            "- Dynamic equity mode, when selected, is sequential per validation run; it is not a portfolio allocator or full exchange margin model.",
            "- Reduce actions are currently modeled as full exits.",
            "- Forced end-of-window closes may distort results.",
            "- Data coverage warnings mean the requested research window may not be trustworthy.",
            "- Market-regime labels are descriptive only and are not used to alter entries or exits.",
        ]
    )
    if assumptions["fill_timing"] == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY.value:
        lines.append("- Same-candle close fills can overstate edge because the signal uses that candle.")
    lines.append("- Closed-trade drawdown and mark-to-market drawdown are reported separately.")
    lines.extend(f"- {limitation}" for limitation in data["limitations"])
    if not data["limitations"]:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def _evaluation_key(
    *,
    request: StrategyValidationRequest,
    sleeve: MoneyFlowSleeveConfig,
    candle: Candle,
    history_bars: int,
    position_state_fingerprint: str | None,
) -> str:
    payload = {
        "strategy_family": StrategyFamily.MONEY_FLOW.value,
        "strategy_version": MoneyFlowStrategyFamily.STRATEGY_VERSION,
        "component_key": sleeve.sleeve_id,
        "timeframe": sleeve.timeframe.value,
        "environment": request.environment.value,
        "venue": request.venue,
        "symbol": request.symbol,
        "candle_close_time": _coerce_utc(candle.close_time).isoformat(),
        "candle_close": str(candle.close),
        "history_bars": history_bars,
        "position_state_fingerprint": position_state_fingerprint,
    }
    return f"sv-{_stable_hash(payload)[:32]}"


def _last_candle_in_window(
    candles: list[Candle],
    *,
    start_at: datetime,
    end_at: datetime,
) -> Candle | None:
    matching = [
        candle
        for candle in candles
        if start_at < _coerce_utc(candle.close_time) <= end_at
    ]
    return matching[-1] if matching else None


def _timeframe_delta(timeframe: Timeframe) -> timedelta | None:
    return {
        Timeframe.M1: timedelta(minutes=1),
        Timeframe.M5: timedelta(minutes=5),
        Timeframe.M15: timedelta(minutes=15),
        Timeframe.H1: timedelta(hours=1),
        Timeframe.H4: timedelta(hours=4),
        Timeframe.D1: timedelta(days=1),
    }.get(timeframe)


def _validate_assumptions(assumptions: StrategyValidationAssumptions) -> None:
    if assumptions.initial_capital <= 0:
        raise StrategyValidationError("initial_capital must be positive.")
    if assumptions.fee_bps < 0:
        raise StrategyValidationError("fee_bps must be non-negative.")
    if assumptions.slippage_bps < 0:
        raise StrategyValidationError("slippage_bps must be non-negative.")
    if assumptions.position_notional_pct <= 0 or assumptions.position_notional_pct > 1:
        raise StrategyValidationError("position_notional_pct must be within (0, 1].")
    if not isinstance(assumptions.capital_sizing_mode, StrategyValidationCapitalSizingMode):
        raise StrategyValidationError(
            "capital_sizing_mode must be a supported StrategyValidationCapitalSizingMode value."
        )
    if not isinstance(assumptions.fill_timing, StrategyValidationFillTiming):
        raise StrategyValidationError("fill_timing must be a supported StrategyValidationFillTiming value.")


def _assumption_limitations(assumptions: StrategyValidationAssumptions) -> list[str]:
    limitations = [
        "research_only_not_live_execution",
        "simulated_trades_are_not_submitted_orders",
        "no_order_book_replay",
        "no_funding_model",
        "no_liquidation_model",
        "no_partial_fill_model",
        "no_venue_latency_model",
        "market_regime_labels_are_descriptive_only_not_strategy_filters",
        "data_coverage_counts_are_research_diagnostics_not_data_quality_certification",
        "results_do_not_prove_future_profitability",
    ]
    if (
        assumptions.capital_sizing_mode
        == StrategyValidationCapitalSizingMode.CONSTANT_INITIAL_CAPITAL_NOTIONAL_PER_TRADE
    ):
        limitations.extend(
            [
                "constant_initial_capital_notional_per_trade_no_dynamic_equity_sizing",
                "realized_equity_does_not_change_next_trade_notional",
            ]
        )
    elif assumptions.capital_sizing_mode == StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT:
        limitations.extend(
            [
                "dynamic_equity_pct_sizes_each_new_trade_from_current_realized_equity",
                "dynamic_equity_pct_is_not_full_margin_liquidation_or_portfolio_simulation",
            ]
        )
    if assumptions.fill_timing == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY:
        limitations.append("same_candle_close_fills_are_research_only_and_can_overstate_edge")
    if assumptions.drawdown_methodology == "closed_trade_and_mark_to_market":
        limitations.append("mark_to_market_drawdown_uses_intrabar_lows_for_open_long_positions")
    if assumptions.reduce_action_model == "full_exit":
        limitations.append("reduce_actions_are_modelled_as_full_exits")
    if assumptions.force_close_open_trade_at_end:
        limitations.append("open_positions_may_be_force_closed_at_window_end")
    return limitations


def _merge_counts(counts: Any) -> dict[str, int]:
    merged: Counter[str] = Counter()
    for item in counts:
        merged.update(item)
    return dict(sorted(merged.items()))


def _bps_to_rate(value: Decimal) -> Decimal:
    return value / Decimal("10000")


def _money(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_PLACES)


def _quantity(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000000000001"))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(_DECIMAL_PLACES)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _coerce_utc(value).isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value
