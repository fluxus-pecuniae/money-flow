"""Strategy evaluation orchestration and persistence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
import hashlib
import json
from typing import Any

from sqlalchemy import func, select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import StrategyFamily, Timeframe
from core.domain.models import (
    Candle,
    IndicatorSnapshot,
    Position,
    SignalEvent,
    StrategyDecision,
    StrategyEvaluationInput,
    StrategyEvaluationResult,
    StrategyFamilyStatus,
)
from core.interfaces.services import IndicatorService, MarketDataService, PortfolioService, StrategyEngine
from core.logging.setup import get_logger
from db.models import (
    CandleModel,
    IndicatorSnapshotModel,
    InstrumentModel,
    MarketDataHealthModel,
    PositionModel,
    SignalEventModel,
    StrategyDecisionModel,
    SymbolModel,
)
from db.session import SessionLocal
from services.indicators.service import DefaultIndicatorService
from services.market_data.service import DefaultMarketDataService
from services.portfolio.service import DefaultPortfolioService
from services.runtime.context import DefaultRuntimeContextService, money_flow_sleeve_config_from_component
from services.strategy.base import StrategyFamilyModule
from services.strategy.money_flow import MoneyFlowStrategyFamily


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class MandateStrategyEngine(StrategyEngine):
    """Coordinates mandate-scoped persisted inputs into strategy-family evaluation results."""

    def __init__(
        self,
        indicator_service: IndicatorService | None = None,
        market_data_service: MarketDataService | None = None,
        portfolio_service: PortfolioService | None = None,
        family_module: StrategyFamilyModule | None = None,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        runtime_context_service: DefaultRuntimeContextService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self._logger = get_logger(__name__)
        self.runtime_context_service = runtime_context_service or DefaultRuntimeContextService(
            self.settings,
            session_factory=session_factory,
        )
        self.indicator_service = indicator_service or DefaultIndicatorService(
            self.settings,
            session_factory=session_factory,
        )
        self.market_data_service = market_data_service or DefaultMarketDataService(
            settings=self.settings,
            session_factory=session_factory,
        )
        self.portfolio_service = portfolio_service or DefaultPortfolioService(
            settings=self.settings,
            session_factory=session_factory,
        )
        self.family_module = family_module or MoneyFlowStrategyFamily(self.settings)

    async def evaluate(self, evaluation_input: StrategyEvaluationInput) -> StrategyEvaluationResult:
        result = await self.family_module.evaluate(evaluation_input)
        self._persist_result(result)
        return result

    async def emit_signal(self, decision: StrategyDecision) -> SignalEvent | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(SignalEventModel).where(SignalEventModel.signal_id == decision.signal_id)
            )
            if model is None:
                return None
            instrument_key = self._lookup_instrument_key(session, model.instrument_ref_id)
        return _signal_from_model(model, instrument_key=instrument_key)

    async def get_family_status(self) -> StrategyFamilyStatus:
        with self._session_factory() as session:
            latest = session.scalar(
                select(func.max(StrategyDecisionModel.decided_at)).where(
                    StrategyDecisionModel.environment == self.settings.app.environment,
                    StrategyDecisionModel.family == StrategyFamily.MONEY_FLOW,
                )
            )
        context = await self.runtime_context_service.ensure_active_context()
        status = await self.family_module.get_family_status()
        status.latest_decision_at = latest
        status.mandate_key = context.mandate.mandate_key
        return status

    async def evaluate_symbol(
        self,
        sleeve_id: str,
        symbol: str,
        indicator_snapshot: IndicatorSnapshot,
    ) -> StrategyDecision:
        evaluation_input = await self._build_input_from_snapshot(
            sleeve_id=sleeve_id,
            symbol=symbol,
            indicator_snapshot=indicator_snapshot,
        )
        result = await self.evaluate(evaluation_input)
        return result.decision

    async def evaluate_sleeve(
        self,
        sleeve_id: str,
        *,
        symbols: Sequence[str] | None = None,
    ) -> list[StrategyEvaluationResult]:
        context = await self.runtime_context_service.ensure_active_context()
        binding_components = [
            (binding_context, component)
            for binding_context in context.bindings
            for component in binding_context.component_configs
            if component.component_key == sleeve_id
        ]
        if not binding_components:
            return []
        with self._session_factory() as session:
            query = select(SymbolModel).where(
                SymbolModel.venue == context.market_data_source_policy.source_venue,
                SymbolModel.is_active.is_(True),
            )
            if symbols:
                query = query.where(SymbolModel.symbol.in_(list(symbols)))
            models = session.scalars(query.order_by(SymbolModel.symbol.asc())).all()
        results: list[StrategyEvaluationResult] = []
        for binding_context, component in binding_components:
            assert component.timeframe is not None
            for model in models:
                if not model.instrument_ref_id:
                    continue
                indicator_snapshot = await self.indicator_service.load_latest_snapshot(
                    model.instrument_ref_id,
                    model.venue,
                    component.timeframe.value,
                )
                evaluation_input = await self._build_input(
                    context=context,
                    binding_context=binding_context,
                    component_config=component,
                    sleeve_id=sleeve_id,
                    timeframe=component.timeframe,
                    symbol_model=model,
                    indicator_snapshot=indicator_snapshot,
                )
                results.append(await self.evaluate(evaluation_input))
        return results

    async def evaluate_all(self) -> list[StrategyEvaluationResult]:
        context = await self.runtime_context_service.ensure_active_context()
        results: list[StrategyEvaluationResult] = []
        seen_components: set[str] = set()
        for binding_context in context.bindings:
            for component in binding_context.component_configs:
                if component.component_key in seen_components:
                    continue
                seen_components.add(component.component_key)
                results.extend(await self.evaluate_sleeve(component.component_key))
        return results

    async def recent_decisions(
        self,
        *,
        sleeve_id: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[StrategyDecision]:
        context = await self.runtime_context_service.ensure_active_context()
        with self._session_factory() as session:
            query = select(StrategyDecisionModel).where(
                StrategyDecisionModel.environment == self.settings.app.environment,
                StrategyDecisionModel.family == StrategyFamily.MONEY_FLOW,
                StrategyDecisionModel.strategy_mandate_ref_id == context.mandate.mandate_ref_id,
            )
            if sleeve_id is not None:
                query = query.where(StrategyDecisionModel.sleeve_id == sleeve_id)
            if symbol is not None:
                query = query.where(StrategyDecisionModel.symbol == symbol)
            models = session.scalars(query.order_by(StrategyDecisionModel.decided_at.desc()).limit(limit)).all()
            decisions = [
                _decision_from_model(
                    model,
                    instrument_key=self._lookup_instrument_key(session, model.instrument_ref_id),
                )
                for model in models
            ]
        return decisions

    async def recent_signals(self, *, sleeve_id: str | None = None, limit: int = 100) -> list[SignalEvent]:
        context = await self.runtime_context_service.ensure_active_context()
        with self._session_factory() as session:
            query = select(SignalEventModel).where(
                SignalEventModel.environment == self.settings.app.environment,
                SignalEventModel.family == StrategyFamily.MONEY_FLOW,
                SignalEventModel.strategy_mandate_ref_id == context.mandate.mandate_ref_id,
            )
            if sleeve_id is not None:
                query = query.where(SignalEventModel.sleeve_id == sleeve_id)
            models = session.scalars(query.order_by(SignalEventModel.generated_at.desc()).limit(limit)).all()
            signals = [
                _signal_from_model(
                    model,
                    instrument_key=self._lookup_instrument_key(session, model.instrument_ref_id),
                )
                for model in models
            ]
        return signals

    async def latest_indicator_snapshots(
        self,
        *,
        timeframe: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[IndicatorSnapshot]:
        context = await self.runtime_context_service.ensure_active_context()
        with self._session_factory() as session:
            query = select(IndicatorSnapshotModel).where(
                IndicatorSnapshotModel.environment == self.settings.app.environment,
                IndicatorSnapshotModel.venue == context.market_data_source_policy.source_venue,
            )
            if timeframe is not None:
                query = query.where(IndicatorSnapshotModel.timeframe == Timeframe(timeframe))
            if symbol is not None:
                query = query.where(IndicatorSnapshotModel.symbol == symbol)
            models = session.scalars(query.order_by(IndicatorSnapshotModel.as_of.desc()).limit(limit)).all()
            snapshots = [
                _indicator_from_model(
                    model,
                    instrument_key=self._lookup_instrument_key(session, model.instrument_ref_id),
                )
                for model in models
            ]
        return snapshots

    async def _build_input(
        self,
        *,
        context: Any,
        binding_context: Any,
        component_config: Any,
        sleeve_id: str,
        timeframe: Timeframe,
        symbol_model: SymbolModel,
        indicator_snapshot: IndicatorSnapshot | None,
    ) -> StrategyEvaluationInput:
        instrument_key = self._lookup_instrument_key_by_ref(symbol_model.instrument_ref_id)
        latest_candle = await self._load_latest_candle(symbol_model.symbol, timeframe)
        current_position = await self._load_current_position(
            symbol_model.instrument_ref_id,
            binding_context.venue_account.venue_account_ref_id,
        )
        with self._session_factory() as session:
            health = session.scalar(
                select(MarketDataHealthModel).where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == symbol_model.venue,
                    MarketDataHealthModel.symbol == symbol_model.symbol,
                    MarketDataHealthModel.timeframe == timeframe,
                )
            )
            history_bars = session.scalar(
                select(func.count()).select_from(CandleModel).where(
                    CandleModel.environment == self.settings.app.environment,
                    CandleModel.venue == symbol_model.venue,
                    CandleModel.instrument_ref_id == symbol_model.instrument_ref_id,
                    CandleModel.symbol == symbol_model.symbol,
                    CandleModel.timeframe == timeframe,
                )
            ) or 0
        sleeve_config = money_flow_sleeve_config_from_component(component_config)
        config_fingerprint = _json_fingerprint(sleeve_config.model_dump(mode="json"))
        position_state_fingerprint = self._position_state_fingerprint(current_position)
        latest_candle_close = latest_candle.close_time if latest_candle is not None else None
        strategy_version = getattr(self.family_module, "STRATEGY_VERSION", self.family_module.__class__.__name__)
        indicator_boundary_aligned = (
            indicator_snapshot is not None
            and latest_candle_close is not None
            and indicator_snapshot.as_of == latest_candle_close
        )
        evaluation_key = _json_fingerprint(
            {
                "family": StrategyFamily.MONEY_FLOW.value,
                "sleeve_id": sleeve_id,
                "component_key": component_config.component_key,
                "instrument_key": instrument_key,
                "instrument_ref_id": symbol_model.instrument_ref_id,
                "client_key": context.client.client_key,
                "client_ref_id": context.client.client_ref_id,
                "mandate_key": context.mandate.mandate_key,
                "mandate_ref_id": context.mandate.mandate_ref_id,
                "binding_key": binding_context.binding.binding_key,
                "binding_ref_id": binding_context.binding.binding_ref_id,
                "venue_account_key": binding_context.venue_account.venue_account_key,
                "venue_account_ref_id": binding_context.venue_account.venue_account_ref_id,
                "venue": symbol_model.venue,
                "symbol": symbol_model.symbol,
                "timeframe": timeframe.value,
                "latest_candle_close": latest_candle_close.isoformat() if latest_candle_close else None,
                "indicator_as_of": (
                    indicator_snapshot.as_of.isoformat() if indicator_snapshot is not None else None
                ),
                "strategy_version": strategy_version,
                "config_fingerprint": config_fingerprint,
                "position_state_fingerprint": position_state_fingerprint,
            }
        )
        return StrategyEvaluationInput(
            family=StrategyFamily.MONEY_FLOW,
            sleeve_id=sleeve_id,
            component_key=component_config.component_key,
            timeframe=timeframe,
            evaluation_key=evaluation_key,
            client_ref_id=context.client.client_ref_id,
            client_key=context.client.client_key,
            strategy_mandate_ref_id=context.mandate.mandate_ref_id,
            mandate_key=context.mandate.mandate_key,
            market_data_source_policy_ref_id=context.market_data_source_policy.policy_ref_id,
            market_data_source_venue=context.market_data_source_policy.source_venue,
            market_data_source_mode=context.market_data_source_policy.source_mode,
            mandate_account_binding_ref_id=binding_context.binding.binding_ref_id,
            binding_key=binding_context.binding.binding_key,
            venue_account_ref_id=binding_context.venue_account.venue_account_ref_id,
            venue_account_key=binding_context.venue_account.venue_account_key,
            account_address=binding_context.venue_account.account_address,
            instrument_key=instrument_key or "",
            instrument_ref_id=symbol_model.instrument_ref_id or "",
            venue=symbol_model.venue,
            symbol=symbol_model.symbol,
            indicator_snapshot=indicator_snapshot,
            latest_candle=latest_candle,
            current_position=current_position,
            market_data_fresh=bool(health is not None and not health.is_stale),
            instrument_active=symbol_model.is_active,
            instrument_strategy_eligible=(
                symbol_model.is_strategy_eligible
                or (
                    symbol_model.is_builder_deployed
                    and binding_context.binding.allow_builder_deployed_for_strategy
                )
            ),
            sleeve_enabled=sleeve_config.enabled,
            history_bars=int(history_bars),
            latest_candle_close=latest_candle_close,
            indicator_boundary_aligned=indicator_boundary_aligned,
            config_fingerprint=config_fingerprint,
            position_state_fingerprint=position_state_fingerprint,
            family_config=sleeve_config.model_dump(mode="json"),
        )

    async def _build_input_from_snapshot(
        self,
        *,
        sleeve_id: str,
        symbol: str,
        indicator_snapshot: IndicatorSnapshot,
    ) -> StrategyEvaluationInput:
        context = await self.runtime_context_service.ensure_active_context()
        binding_context = next(
            binding
            for binding in context.bindings
            if any(component.component_key == sleeve_id for component in binding.component_configs)
        )
        component_config = next(
            component for component in binding_context.component_configs if component.component_key == sleeve_id
        )
        with self._session_factory() as session:
            symbol_model = session.scalar(
                select(SymbolModel).where(
                    SymbolModel.symbol == symbol,
                    SymbolModel.instrument_ref_id == indicator_snapshot.instrument_ref_id,
                    SymbolModel.venue == indicator_snapshot.venue,
                )
            )
        if symbol_model is None:
            raise ValueError(f"Unable to resolve symbol model for strategy evaluation: {symbol}")
        return await self._build_input(
            context=context,
            binding_context=binding_context,
            component_config=component_config,
            sleeve_id=sleeve_id,
            timeframe=indicator_snapshot.timeframe,
            symbol_model=symbol_model,
            indicator_snapshot=indicator_snapshot,
        )

    async def _load_latest_candle(
        self,
        symbol: str,
        timeframe: Timeframe,
    ) -> Candle | None:
        candles = await self.market_data_service.get_recent_candles(symbol, timeframe.value, 1)
        return candles[-1] if candles else None

    async def _load_current_position(
        self,
        instrument_ref_id: str | None,
        venue_account_ref_id: str | None,
    ) -> Position | None:
        if instrument_ref_id is None:
            return None
        positions = await self.portfolio_service.get_open_positions(
            venue_account_ref_id=venue_account_ref_id,
        )
        for position in positions:
            if position.instrument_ref_id == instrument_ref_id:
                return position
        return None

    def _persist_result(self, result: StrategyEvaluationResult) -> None:
        with self._session_factory() as session:
            signal = result.signal_event
            if signal is not None:
                model = session.scalar(
                    select(SignalEventModel).where(SignalEventModel.evaluation_key == signal.evaluation_key)
                )
                if model is None:
                    model = SignalEventModel(
                        environment=self.settings.app.environment,
                        signal_id=signal.signal_id,
                        evaluation_key=signal.evaluation_key,
                        family=signal.family,
                        sleeve_id=signal.sleeve_id,
                        component_key=signal.component_key,
                        client_ref_id=signal.client_ref_id,
                        strategy_mandate_ref_id=signal.strategy_mandate_ref_id,
                        mandate_account_binding_ref_id=signal.mandate_account_binding_ref_id,
                        mandate_key=signal.mandate_key,
                        binding_key=signal.binding_key,
                        venue_account_ref_id=signal.venue_account_ref_id,
                        instrument_ref_id=signal.instrument_ref_id,
                        symbol_id=self._lookup_symbol_id(
                        session,
                        signal.instrument_ref_id,
                        signal.symbol,
                        signal.provenance.get("market_data_source_venue", self.settings.exchange.venue),
                    ),
                        symbol=signal.symbol,
                        timeframe=signal.timeframe,
                        signal_type=signal.signal_type,
                        reason_code=signal.reason_code,
                        provenance=signal.provenance,
                        features=signal.features,
                        generated_at=signal.generated_at,
                    )
                    session.add(model)
                else:
                    model.signal_id = signal.signal_id
                    model.component_key = signal.component_key
                    model.client_ref_id = signal.client_ref_id
                    model.strategy_mandate_ref_id = signal.strategy_mandate_ref_id
                    model.mandate_account_binding_ref_id = signal.mandate_account_binding_ref_id
                    model.mandate_key = signal.mandate_key
                    model.binding_key = signal.binding_key
                    model.venue_account_ref_id = signal.venue_account_ref_id
                    model.signal_type = signal.signal_type
                    model.reason_code = signal.reason_code
                    model.provenance = signal.provenance
                    model.features = signal.features
                    model.generated_at = signal.generated_at
            decision = result.decision
            model = session.scalar(
                select(StrategyDecisionModel).where(
                    StrategyDecisionModel.evaluation_key == decision.evaluation_key
                )
            )
            if model is None:
                model = StrategyDecisionModel(
                    environment=self.settings.app.environment,
                    decision_id=decision.decision_id,
                    evaluation_key=decision.evaluation_key,
                    family=decision.family,
                    signal_id=decision.signal_id,
                    sleeve_id=decision.sleeve_id,
                    component_key=decision.component_key,
                    client_ref_id=decision.client_ref_id,
                    strategy_mandate_ref_id=decision.strategy_mandate_ref_id,
                    mandate_account_binding_ref_id=decision.mandate_account_binding_ref_id,
                    mandate_key=decision.mandate_key,
                    binding_key=decision.binding_key,
                    venue_account_ref_id=decision.venue_account_ref_id,
                    instrument_ref_id=decision.instrument_ref_id,
                    symbol_id=self._lookup_symbol_id(
                        session,
                        decision.instrument_ref_id,
                        decision.symbol,
                        decision.provenance.get("market_data_source_venue", self.settings.exchange.venue),
                    ),
                    symbol=decision.symbol,
                    action=decision.action,
                    status=decision.status,
                    reason_code=decision.reason_code,
                    confidence=decision.confidence,
                    rationale=decision.rationale,
                    provenance=decision.provenance,
                    features=decision.features,
                    decided_at=decision.decided_at,
                )
                session.add(model)
            else:
                model.decision_id = decision.decision_id
                model.signal_id = decision.signal_id
                model.component_key = decision.component_key
                model.client_ref_id = decision.client_ref_id
                model.strategy_mandate_ref_id = decision.strategy_mandate_ref_id
                model.mandate_account_binding_ref_id = decision.mandate_account_binding_ref_id
                model.mandate_key = decision.mandate_key
                model.binding_key = decision.binding_key
                model.venue_account_ref_id = decision.venue_account_ref_id
                model.action = decision.action
                model.status = decision.status
                model.reason_code = decision.reason_code
                model.confidence = decision.confidence
                model.rationale = decision.rationale
                model.provenance = decision.provenance
                model.features = decision.features
                model.decided_at = decision.decided_at
            session.commit()
        self._logger.info(
            "strategy_evaluation_persisted",
            family=decision.family.value,
            sleeve_id=decision.sleeve_id,
            symbol=decision.symbol,
            evaluation_key=decision.evaluation_key,
            status=decision.status.value,
            action=decision.action.value,
            reason_code=decision.reason_code,
        )

    @staticmethod
    def _lookup_symbol_id(
        session: Any,
        instrument_ref_id: str | None,
        symbol: str,
        venue: str,
    ) -> str | None:
        model = session.scalar(
            select(SymbolModel.id).where(
                SymbolModel.instrument_ref_id == instrument_ref_id,
                SymbolModel.symbol == symbol,
                SymbolModel.venue == venue,
            )
        )
        return str(model) if model is not None else None

    @staticmethod
    def _lookup_instrument_key(session: Any, instrument_ref_id: str | None) -> str | None:
        if instrument_ref_id is None:
            return None
        model = session.scalar(
            select(InstrumentModel.instrument_key).where(InstrumentModel.id == instrument_ref_id)
        )
        return str(model) if model is not None else None

    def _lookup_instrument_key_by_ref(self, instrument_ref_id: str | None) -> str | None:
        with self._session_factory() as session:
            return self._lookup_instrument_key(session, instrument_ref_id)

    @staticmethod
    def _position_state_fingerprint(position: Position | None) -> str | None:
        if position is None:
            return None
        return _json_fingerprint(
            {
                "position_id": position.position_id,
                "venue_account_ref_id": position.venue_account_ref_id,
                "status": position.status.value,
                "side": position.side.value,
                "quantity": str(position.quantity),
                "avg_entry_price": str(position.avg_entry_price),
                "mark_price": str(position.mark_price) if position.mark_price is not None else None,
                "account_address": position.account_address,
            }
        )


def _indicator_from_model(model: IndicatorSnapshotModel, *, instrument_key: str | None) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        instrument_key=instrument_key,
        instrument_ref_id=model.instrument_ref_id,
        venue=model.venue,
        symbol=model.symbol,
        timeframe=model.timeframe,
        as_of=model.as_of,
        ema_5=model.ema_5,
        ema_10=model.ema_10,
        sma_20=model.sma_20,
        rsi_14=model.rsi_14,
        macd=model.macd,
        macd_signal=model.macd_signal,
        macd_histogram=model.macd_histogram,
    )


def _signal_from_model(model: SignalEventModel, *, instrument_key: str | None) -> SignalEvent:
    return SignalEvent(
        signal_id=model.signal_id,
        evaluation_key=model.evaluation_key,
        family=model.family,
        sleeve_id=model.sleeve_id,
        component_key=model.component_key,
        client_ref_id=model.client_ref_id,
        strategy_mandate_ref_id=model.strategy_mandate_ref_id,
        mandate_key=model.mandate_key,
        mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
        binding_key=model.binding_key,
        venue_account_ref_id=model.venue_account_ref_id,
        instrument_key=instrument_key,
        instrument_ref_id=model.instrument_ref_id,
        symbol=model.symbol,
        timeframe=model.timeframe,
        signal_type=model.signal_type,
        generated_at=model.generated_at,
        reason_code=model.reason_code,
        provenance=dict(model.provenance),
        features=dict(model.features),
    )


def _decision_from_model(model: StrategyDecisionModel, *, instrument_key: str | None) -> StrategyDecision:
    return StrategyDecision(
        decision_id=model.decision_id,
        evaluation_key=model.evaluation_key,
        family=model.family,
        sleeve_id=model.sleeve_id,
        component_key=model.component_key,
        client_ref_id=model.client_ref_id,
        strategy_mandate_ref_id=model.strategy_mandate_ref_id,
        mandate_key=model.mandate_key,
        mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
        binding_key=model.binding_key,
        venue_account_ref_id=model.venue_account_ref_id,
        instrument_key=instrument_key,
        instrument_ref_id=model.instrument_ref_id,
        signal_id=model.signal_id,
        symbol=model.symbol,
        action=model.action,
        status=model.status,
        reason_code=model.reason_code,
        confidence=model.confidence,
        rationale=model.rationale,
        decided_at=model.decided_at,
        provenance=dict(model.provenance),
        features=dict(model.features),
    )


# Deprecated compatibility alias for older imports. The active runtime is
# mandate/binding/component-oriented even when Money Flow still uses sleeve IDs
# as family-specific component keys.
SleeveStrategyEngine = MandateStrategyEngine
