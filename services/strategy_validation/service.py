"""Money Flow strategy validation and backtest reporting.

This service is intentionally separate from routing, automation, and live
execution. It reads persisted historical candles, reuses the current Money Flow
strategy rules, and produces simulated research artifacts only.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
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
    StrategyFamily,
    Timeframe,
)
from core.domain.models import (
    Candle,
    IndicatorSnapshot,
    Position,
    StrategyEvaluationInput,
    StrategyValidationAssumptions,
    StrategyValidationComponentReport,
    StrategyValidationMetrics,
    StrategyValidationReport,
    StrategyValidationRequest,
    StrategyValidationTrade,
)
from db.models import CandleModel, InstrumentModel
from db.session import SessionLocal
from services.indicators.service import DefaultIndicatorService
from services.strategy.money_flow import MoneyFlowStrategyFamily

_DECIMAL_PLACES = Decimal("0.00000001")


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
        )
        limitations = sorted(
            {
                limitation
                for component_report in component_reports
                for limitation in component_report.limitations
            }
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
            limitations=limitations,
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
        trades: list[StrategyValidationTrade] = []
        no_trade_reasons: Counter[str] = Counter()
        invalid_reasons: Counter[str] = Counter()
        limitations: list[str] = []
        open_position: _SimulatedOpenPosition | None = None
        evaluated_candles = 0
        if not candles:
            limitations.append("no_persisted_candles_for_component")

        for history_index, (candle, snapshot) in enumerate(zip(candles, snapshots, strict=False), start=1):
            candle_close_time = _coerce_utc(candle.close_time)
            if candle_close_time < start_at or candle_close_time > end_at:
                continue
            evaluated_candles += 1
            current_position = (
                _position_from_open_position(open_position, request=request, candle=candle)
                if open_position is not None
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
                    open_position.position_state_fingerprint if open_position is not None else None
                ),
            )
            evaluation = await self._strategy_family.evaluate(evaluation_input)
            decision = evaluation.decision

            if open_position is not None:
                open_position.record_excursion(candle)
                if decision.action in {DecisionAction.CLOSE, DecisionAction.REDUCE}:
                    if decision.action == DecisionAction.REDUCE:
                        limitations.append("reduce_actions_are_simulated_as_full_exits_for_sv1_0")
                    trades.append(
                        _close_trade(
                            request=request,
                            open_position=open_position,
                            candle=candle,
                            exit_reason=decision.reason_code or decision.action.value,
                            exit_evaluation_key=decision.evaluation_key,
                            forced_exit=False,
                        )
                    )
                    open_position = None
                continue

            if decision.status == StrategyDecisionStatus.INVALID:
                invalid_reasons[decision.reason_code or "invalid_without_reason"] += 1
                continue
            if decision.status == StrategyDecisionStatus.NO_TRADE:
                no_trade_reasons[decision.reason_code or "no_trade_without_reason"] += 1
                continue
            if decision.action == DecisionAction.OPEN:
                open_position = _open_trade(
                    request=request,
                    sleeve=sleeve,
                    candle=candle,
                    entry_reason=decision.reason_code,
                    entry_evaluation_key=decision.evaluation_key,
                )

        if open_position is not None and request.assumptions.force_close_open_trade_at_end:
            last_candle = _last_candle_in_window(candles, start_at=start_at, end_at=end_at)
            if last_candle is not None:
                open_position.record_excursion(last_candle)
                trades.append(
                    _close_trade(
                        request=request,
                        open_position=open_position,
                        candle=last_candle,
                        exit_reason="end_of_window_forced_close",
                        exit_evaluation_key=f"{open_position.entry_evaluation_key}:forced_exit",
                        forced_exit=True,
                    )
                )
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
        )
        return StrategyValidationComponentReport(
            component_key=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            candle_count=len(candles),
            evaluated_candles=evaluated_candles,
            trades=trades,
            metrics=metrics,
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


class _SimulatedOpenPosition:
    def __init__(
        self,
        *,
        component_key: str,
        timeframe: Timeframe,
        entry_time: datetime,
        raw_entry_price: Decimal,
        entry_price: Decimal,
        size: Decimal,
        entry_notional: Decimal,
        entry_fee: Decimal,
        entry_slippage_cost: Decimal,
        entry_reason: str | None,
        entry_evaluation_key: str,
    ) -> None:
        self.component_key = component_key
        self.timeframe = timeframe
        self.entry_time = entry_time
        self.raw_entry_price = raw_entry_price
        self.entry_price = entry_price
        self.size = size
        self.entry_notional = entry_notional
        self.entry_fee = entry_fee
        self.entry_slippage_cost = entry_slippage_cost
        self.entry_reason = entry_reason
        self.entry_evaluation_key = entry_evaluation_key
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


def _open_trade(
    *,
    request: StrategyValidationRequest,
    sleeve: MoneyFlowSleeveConfig,
    candle: Candle,
    entry_reason: str | None,
    entry_evaluation_key: str,
) -> _SimulatedOpenPosition:
    slippage_rate = _bps_to_rate(request.assumptions.slippage_bps)
    fee_rate = _bps_to_rate(request.assumptions.fee_bps)
    raw_entry_price = candle.close
    entry_price = _money(raw_entry_price * (Decimal("1") + slippage_rate))
    entry_notional = _money(request.assumptions.initial_capital * request.assumptions.position_notional_pct)
    size = _quantity(entry_notional / entry_price)
    entry_fee = _money(entry_notional * fee_rate)
    entry_slippage_cost = _money((entry_price - raw_entry_price) * size)
    open_position = _SimulatedOpenPosition(
        component_key=sleeve.sleeve_id,
        timeframe=sleeve.timeframe,
        entry_time=_coerce_utc(candle.close_time),
        raw_entry_price=raw_entry_price,
        entry_price=entry_price,
        size=size,
        entry_notional=entry_notional,
        entry_fee=entry_fee,
        entry_slippage_cost=entry_slippage_cost,
        entry_reason=entry_reason,
        entry_evaluation_key=entry_evaluation_key,
    )
    open_position.record_excursion(candle)
    return open_position


def _close_trade(
    *,
    request: StrategyValidationRequest,
    open_position: _SimulatedOpenPosition,
    candle: Candle,
    exit_reason: str,
    exit_evaluation_key: str,
    forced_exit: bool,
) -> StrategyValidationTrade:
    slippage_rate = _bps_to_rate(request.assumptions.slippage_bps)
    fee_rate = _bps_to_rate(request.assumptions.fee_bps)
    raw_exit_price = candle.close
    exit_price = _money(raw_exit_price * (Decimal("1") - slippage_rate))
    exit_notional = _money(exit_price * open_position.size)
    exit_fee = _money(exit_notional * fee_rate)
    exit_slippage_cost = _money((raw_exit_price - exit_price) * open_position.size)
    gross_pnl = _money((raw_exit_price - open_position.raw_entry_price) * open_position.size)
    fees = _money(open_position.entry_fee + exit_fee)
    slippage_cost = _money(open_position.entry_slippage_cost + exit_slippage_cost)
    net_pnl = _money(gross_pnl - fees - slippage_cost)
    return_pct = _ratio(net_pnl, open_position.entry_notional) or Decimal("0")
    duration_seconds = int((_coerce_utc(candle.close_time) - open_position.entry_time).total_seconds())
    trade_payload = {
        "component_key": open_position.component_key,
        "entry_time": open_position.entry_time.isoformat(),
        "exit_time": _coerce_utc(candle.close_time).isoformat(),
        "entry_evaluation_key": open_position.entry_evaluation_key,
        "exit_evaluation_key": exit_evaluation_key,
    }
    return StrategyValidationTrade(
        trade_id=f"svt-{_stable_hash(trade_payload)[:24]}",
        strategy_family=StrategyFamily.MONEY_FLOW,
        component_key=open_position.component_key,
        timeframe=open_position.timeframe,
        symbol=request.symbol,
        side=OrderSide.BUY,
        entry_time=open_position.entry_time,
        exit_time=_coerce_utc(candle.close_time),
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
        duration_seconds=duration_seconds,
        forced_exit=forced_exit,
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
) -> StrategyValidationMetrics:
    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    gross_pnl = _money(sum((trade.gross_pnl for trade in trades), Decimal("0")))
    net_pnl = _money(sum((trade.net_pnl for trade in trades), Decimal("0")))
    total_fees = _money(sum((trade.fees for trade in trades), Decimal("0")))
    total_slippage_cost = _money(sum((trade.slippage_cost for trade in trades), Decimal("0")))
    winning_total = sum((trade.net_pnl for trade in wins), Decimal("0"))
    losing_total = sum((trade.net_pnl for trade in losses), Decimal("0"))
    equity = initial_capital
    peak = initial_capital
    max_drawdown = Decimal("0")
    for trade in trades:
        equity += trade.net_pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
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
        max_drawdown=_money(max_drawdown),
        max_drawdown_pct=_ratio(max_drawdown, initial_capital),
        average_trade_duration_seconds=_ratio(duration_total, Decimal(len(trades))),
        best_trade_id=best_trade.trade_id if best_trade is not None else None,
        best_trade_net_pnl=best_trade.net_pnl if best_trade is not None else None,
        worst_trade_id=worst_trade.trade_id if worst_trade is not None else None,
        worst_trade_net_pnl=worst_trade.net_pnl if worst_trade is not None else None,
        return_on_initial_capital=_ratio(net_pnl, initial_capital) or Decimal("0"),
        trades_by_component_timeframe=dict(sorted(trades_by_component_timeframe.items())),
        no_trade_reason_counts=dict(sorted(no_trade_reason_counts.items())),
        invalid_reason_counts=dict(sorted(invalid_reason_counts.items())),
    )


def strategy_validation_report_to_dict(report: StrategyValidationReport) -> dict[str, Any]:
    return _json_ready(asdict(report))


def strategy_validation_report_to_markdown(report: StrategyValidationReport) -> str:
    data = strategy_validation_report_to_dict(report)
    metrics = data["aggregate_metrics"]
    lines = [
        f"# Money Flow Strategy Validation Report `{data['report_id']}`",
        "",
        f"- Strategy family: `{data['strategy_family']}`",
        f"- Environment: `{data['environment']}`",
        f"- Venue/source: `{data['venue']}`",
        f"- Symbol: `{data['symbol']}`",
        f"- Range: `{data['start_at']}` to `{data['end_at']}`",
        f"- Initial capital: `{data['assumptions']['initial_capital']}`",
        f"- Fee bps: `{data['assumptions']['fee_bps']}`",
        f"- Slippage bps: `{data['assumptions']['slippage_bps']}`",
        f"- Position notional pct: `{data['assumptions']['position_notional_pct']}`",
        "",
        "## Aggregate Metrics",
        "",
        f"- Trades: `{metrics['number_of_trades']}`",
        f"- Win rate: `{metrics['win_rate']}`",
        f"- Net PnL: `{metrics['net_pnl']}`",
        f"- Gross PnL: `{metrics['gross_pnl']}`",
        f"- Fees: `{metrics['total_fees']}`",
        f"- Slippage cost: `{metrics['total_slippage_cost']}`",
        f"- Max drawdown: `{metrics['max_drawdown']}`",
        f"- Return on initial capital: `{metrics['return_on_initial_capital']}`",
        "",
        "## Limitations",
        "",
    ]
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
        if start_at <= _coerce_utc(candle.close_time) <= end_at
    ]
    return matching[-1] if matching else None


def _validate_assumptions(assumptions: StrategyValidationAssumptions) -> None:
    if assumptions.initial_capital <= 0:
        raise StrategyValidationError("initial_capital must be positive.")
    if assumptions.fee_bps < 0:
        raise StrategyValidationError("fee_bps must be non-negative.")
    if assumptions.slippage_bps < 0:
        raise StrategyValidationError("slippage_bps must be non-negative.")
    if assumptions.position_notional_pct <= 0 or assumptions.position_notional_pct > 1:
        raise StrategyValidationError("position_notional_pct must be within (0, 1].")


def _assumption_limitations(assumptions: StrategyValidationAssumptions) -> list[str]:
    limitations = [
        "sv1_0_uses_close_price_fill_assumptions_not_order_book_replay",
        "sv1_0_reports_research_simulated_trades_not_live_submitted_orders",
        "sv1_0_does_not_model_funding_liquidations_or_partial_fills",
    ]
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
