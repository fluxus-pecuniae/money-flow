"""Mandate-level desired trade and routing-candidate planning surfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    DecisionAction,
    MandateDesiredTradeStatus,
    OrderSide,
    PositionStatus,
    StrategyDecisionStatus,
    TradeTargetScope,
)
from core.domain.models import (
    ActiveMandateBindingContext,
    ActiveMandateContext,
    BindingQuoteSnapshot,
    BindingRoutingCandidate,
    DesiredTradeConvertibilityAssessment,
    MandateMarketDataSourcePolicy,
    MandateDesiredTrade,
    StrategyComponentConfig,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueQuoteSnapshot,
)
from core.interfaces.services import MandateTradePlanningService, RuntimeContextService, VenueRegistryService
from db.models import (
    ExchangeAccountSnapshotModel,
    InstrumentModel,
    MandateMarketDataSourcePolicyModel,
    MandateDesiredTradeModel,
    PositionModel,
    StrategyDecisionModel,
    StrategyMandateModel,
    SymbolModel,
)
from db.session import SessionLocal
from services.exchange.registry import DefaultVenueRegistryService
from services.runtime.context import DefaultRuntimeContextService


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _dedupe(values: Sequence[str]) -> list[str]:
    return sorted({value for value in values if value})


def _parse_planning_as_of(payload: dict[str, Any]) -> datetime | None:
    candidate = payload.get("indicator_as_of") or payload.get("latest_candle_close")
    if not candidate:
        return None
    return datetime.fromisoformat(str(candidate))


class DesiredTradeConversionError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class DefaultTradePlanningService(MandateTradePlanningService):
    """Provides mandate-level planning objects ahead of risk and routing."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        runtime_context_service: RuntimeContextService | None = None,
        venue_registry_service: VenueRegistryService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self.runtime_context_service = runtime_context_service or DefaultRuntimeContextService(
            self.settings,
            session_factory=session_factory,
        )
        self.venue_registry_service = venue_registry_service or DefaultVenueRegistryService(self.settings)

    async def get_market_data_source_policy(
        self,
        *,
        mandate_key: str | None = None,
    ) -> MandateMarketDataSourcePolicy:
        context = await self._resolve_context(mandate_key=mandate_key)
        return context.market_data_source_policy

    async def inspect_decision_convertibility(
        self,
        decision_id: str,
    ) -> DesiredTradeConvertibilityAssessment:
        with self._session_factory() as session:
            decision = self._load_decision_model(session, decision_id)
            instrument_key = self._lookup_instrument_key(session, decision.instrument_ref_id)
            source_policy = self._load_source_policy_for_decision(session, decision)
            position = self._load_bound_position(
                session,
                instrument_ref_id=decision.instrument_ref_id,
                venue_account_ref_id=decision.venue_account_ref_id,
            )
            return self._convertibility_assessment(
                decision,
                instrument_key=instrument_key,
                source_policy=source_policy,
                position=position,
            )

    async def preview_desired_trade_from_decision(
        self,
        decision_id: str,
        *,
        persist: bool = False,
    ) -> MandateDesiredTrade:
        with self._session_factory() as session:
            decision = self._load_decision_model(session, decision_id)
            instrument_key = self._lookup_instrument_key(session, decision.instrument_ref_id)
            source_policy = self._load_source_policy_for_decision(session, decision)
            position = self._load_bound_position(
                session,
                instrument_ref_id=decision.instrument_ref_id,
                venue_account_ref_id=decision.venue_account_ref_id,
            )
            assessment = self._convertibility_assessment(
                decision,
                instrument_key=instrument_key,
                source_policy=source_policy,
                position=position,
            )
            if not assessment.convertible:
                raise DesiredTradeConversionError(assessment.reason_code or "non_convertible", assessment.message)
            desired_trade = self._desired_trade_from_decision_model(
                decision,
                instrument_key=instrument_key,
                source_policy=source_policy,
                position=position,
            )
            existing_model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.desired_trade_key == desired_trade.desired_trade_key
                )
            )
            if existing_model is not None:
                desired_trade = self._merge_with_existing_model(
                    desired_trade,
                    existing_model,
                )
            if persist:
                model = self._persist_desired_trade(session, desired_trade, existing_model=existing_model)
                session.commit()
                desired_trade.desired_trade_ref_id = model.id
        return desired_trade

    async def list_desired_trades(
        self,
        *,
        mandate_key: str | None = None,
        component_key: str | None = None,
        status: MandateDesiredTradeStatus | None = None,
        limit: int = 100,
    ) -> Sequence[MandateDesiredTrade]:
        with self._session_factory() as session:
            query = select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.environment == self.settings.app.environment
            )
            if mandate_key is not None:
                query = query.where(MandateDesiredTradeModel.mandate_key == mandate_key)
            if component_key is not None:
                query = query.where(MandateDesiredTradeModel.component_key == component_key)
            if status is not None:
                query = query.where(MandateDesiredTradeModel.status == status)
            models = session.scalars(
                query.order_by(MandateDesiredTradeModel.created_at.desc()).limit(limit)
            ).all()
        return [self._desired_trade_from_model(model) for model in models]

    async def list_routing_candidates(
        self,
        *,
        symbol: str | None = None,
        instrument_key: str | None = None,
        component_key: str | None = None,
        mandate_key: str | None = None,
    ) -> Sequence[BindingRoutingCandidate]:
        context = await self._resolve_context(mandate_key=mandate_key)
        instrument = self._resolve_instrument(
            symbol=symbol,
            instrument_key=instrument_key,
            source_policy=context.market_data_source_policy,
        )
        candidates: list[BindingRoutingCandidate] = []
        for binding_context in context.bindings:
            if component_key is not None and not any(
                component.component_key == component_key for component in binding_context.component_configs
            ):
                continue
            candidates.append(
                await self._build_routing_candidate(
                    context=context,
                    binding_context=binding_context,
                    instrument=instrument,
                    component_key=component_key,
                )
            )
        return candidates

    async def list_binding_quotes(
        self,
        *,
        symbol: str | None = None,
        instrument_key: str | None = None,
        component_key: str | None = None,
        mandate_key: str | None = None,
    ) -> Sequence[BindingQuoteSnapshot]:
        candidates = await self.list_routing_candidates(
            symbol=symbol,
            instrument_key=instrument_key,
            component_key=component_key,
            mandate_key=mandate_key,
        )
        quotes: list[BindingQuoteSnapshot] = []
        for candidate in candidates:
            if candidate.quote_snapshot is not None:
                quotes.append(candidate.quote_snapshot)
        return quotes

    async def _resolve_context(self, *, mandate_key: str | None = None) -> ActiveMandateContext:
        active_context = await self.runtime_context_service.ensure_active_context()
        target_mandate_key = mandate_key or active_context.mandate.mandate_key
        if target_mandate_key == active_context.mandate.mandate_key:
            return active_context

        client = active_context.client
        mandates = await self.runtime_context_service.list_mandates(client_key=client.client_key)
        mandate = next((item for item in mandates if item.mandate_key == target_mandate_key), None)
        if mandate is None:
            raise ValueError(f"Mandate not found for active client: {target_mandate_key}")
        with self._session_factory() as session:
            mandate_model = session.scalar(
                select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == target_mandate_key)
            )
            if mandate_model is None:
                raise ValueError(f"Mandate model not found: {target_mandate_key}")
            source_policy_model = session.scalar(
                select(MandateMarketDataSourcePolicyModel).where(
                    MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == mandate_model.id
                )
            )
            if source_policy_model is None:
                raise ValueError(f"Market-data source policy not found for mandate: {target_mandate_key}")
            source_policy = self._source_policy_from_model(source_policy_model, mandate_key=mandate.mandate_key)
        accounts = {
            account.venue_account_key: account
            for account in await self.runtime_context_service.list_venue_accounts(client_key=client.client_key)
        }
        binding_contexts: list[ActiveMandateBindingContext] = []
        for binding in await self.runtime_context_service.list_bindings(mandate_key=target_mandate_key):
            venue_account = accounts.get(binding.venue_account_key)
            if venue_account is None:
                continue
            component_configs = list(
                await self.runtime_context_service.list_effective_component_configs(binding_key=binding.binding_key)
            )
            binding_contexts.append(
                ActiveMandateBindingContext(
                    binding=binding,
                    venue_account=venue_account,
                    component_configs=component_configs,
                )
            )
        return ActiveMandateContext(
            client=client,
            mandate=mandate,
            market_data_source_policy=source_policy,
            bindings=binding_contexts,
        )

    def _resolve_instrument(
        self,
        *,
        symbol: str | None,
        instrument_key: str | None,
        source_policy: MandateMarketDataSourcePolicy,
    ) -> InstrumentModel:
        with self._session_factory() as session:
            if instrument_key is not None:
                model = session.scalar(
                    select(InstrumentModel).where(InstrumentModel.instrument_key == instrument_key)
                )
                if model is None:
                    raise ValueError(f"Instrument not found: {instrument_key}")
                return model
            if symbol is None:
                raise ValueError("instrument_key is preferred; symbol is only allowed when resolution is safe.")
            if source_policy.instrument_resolution_mode.value == "require_instrument_key":
                raise ValueError(
                    "This mandate requires explicit instrument_key for planning resolution."
                )
            query = select(InstrumentModel).where(InstrumentModel.canonical_symbol == symbol.upper())
            if source_policy.market_type is not None:
                query = query.where(InstrumentModel.market_type == source_policy.market_type)
            if source_policy.product_type is not None:
                query = query.where(InstrumentModel.product_type == source_policy.product_type)
            models = session.scalars(
                query.order_by(InstrumentModel.market_type.asc(), InstrumentModel.product_type.asc())
            ).all()
            if not models:
                raise ValueError(f"Canonical instrument not found for symbol: {symbol}")
            if len(models) > 1:
                raise ValueError(
                    f"Ambiguous canonical symbol for planning: {symbol}. Provide instrument_key or tighten the mandate source policy."
                )
            return models[0]

    async def _build_routing_candidate(
        self,
        *,
        context: ActiveMandateContext,
        binding_context: ActiveMandateBindingContext,
        instrument: InstrumentModel,
        component_key: str | None,
    ) -> BindingRoutingCandidate:
        adapter = await self.venue_registry_service.get_adapter(binding_context.venue_account.venue)
        capabilities = await adapter.get_venue_capabilities()
        status = await adapter.get_exchange_status()
        symbol_model = self._lookup_symbol_for_binding(
            venue=binding_context.venue_account.venue,
            instrument_ref_id=instrument.id,
        )
        component_config = self._resolve_component(binding_context.component_configs, component_key)
        account_snapshot = self._latest_account_snapshot(binding_context.venue_account.venue_account_ref_id)
        account_connectivity = VenueAccountConnectivity(
            venue=binding_context.venue_account.venue,
            environment=binding_context.venue_account.environment,
            support_level=capabilities.support_level,
            account_model=capabilities.account_model,
            account_identifier=(
                binding_context.venue_account.account_address
                or binding_context.venue_account.venue_native_account_id
                or None
            ),
            account_label=binding_context.venue_account.account_label,
            subaccount_label=binding_context.venue_account.subaccount_label,
            credentials_ref=(
                binding_context.venue_account.credentials_ref or binding_context.venue_account.wallet_ref
            ),
            account_identifier_configured=bool(
                binding_context.venue_account.account_address
                or binding_context.venue_account.venue_native_account_id
            ),
            credentials_configured=bool(
                binding_context.venue_account.credentials_ref or binding_context.venue_account.wallet_ref
            ),
            read_only_mode=status.read_only_mode,
            dry_run_mode=status.dry_run_mode,
            submission_authorized=status.submission_authorized,
            private_account_sync_enabled=bool(
                capabilities.supports_account_sync
                and (binding_context.venue_account.credentials_ref or binding_context.venue_account.wallet_ref)
            ),
            account_snapshot_available=account_snapshot is not None,
            open_orders_query_available=capabilities.supports_open_orders_query,
            open_positions_query_available=capabilities.supports_open_positions_query,
            last_success_at=status.last_success_at,
            last_error=status.last_error,
        )
        quote_snapshot = await self._binding_quote_snapshot(
            binding_context=binding_context,
            instrument=instrument,
            symbol_model=symbol_model,
            adapter=adapter,
            account_connectivity=account_connectivity,
        )
        eligibility_reasons = self._candidate_reasons(
            binding_context=binding_context,
            component_config=component_config,
            symbol_model=symbol_model,
            capabilities=capabilities,
            status=status,
            account_connectivity=account_connectivity,
            quote_snapshot=quote_snapshot,
        )
        strategy_eligible = not any(
            reason
            in eligibility_reasons
            for reason in (
                "binding_disabled",
                "binding_strategy_ineligible",
                "component_not_bound",
                "component_disabled",
                "instrument_unavailable_on_venue",
                "symbol_not_strategy_eligible",
            )
        )
        trading_eligible = not any(
            reason
            in eligibility_reasons
            for reason in (
                "binding_disabled",
                "binding_strategy_ineligible",
                "component_not_bound",
                "component_disabled",
                "binding_trading_disabled",
                "instrument_unavailable_on_venue",
                "symbol_not_strategy_eligible",
                "symbol_not_trading_eligible",
                "venue_order_submission_unsupported",
                "venue_read_only_mode",
                "account_identifier_missing",
            )
        )
        routing_eligible = not any(
            reason
            in eligibility_reasons
            for reason in (
                "binding_disabled",
                "binding_routing_ineligible",
                "component_not_bound",
                "component_disabled",
                "instrument_unavailable_on_venue",
                "venue_order_submission_unsupported",
                "venue_read_only_mode",
                "account_identifier_missing",
            )
        )
        return BindingRoutingCandidate(
            client_ref_id=context.client.client_ref_id,
            strategy_mandate_ref_id=context.mandate.mandate_ref_id,
            mandate_key=context.mandate.mandate_key,
            market_data_source_policy_ref_id=context.market_data_source_policy.policy_ref_id,
            planning_source_venue=context.market_data_source_policy.source_venue,
            binding_ref_id=binding_context.binding.binding_ref_id,
            binding_key=binding_context.binding.binding_key,
            venue_account_ref_id=binding_context.venue_account.venue_account_ref_id,
            venue_account_key=binding_context.venue_account.venue_account_key,
            venue=binding_context.venue_account.venue,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol=instrument.canonical_symbol,
            exchange_symbol=symbol_model.exchange_symbol if symbol_model is not None else None,
            strategy_eligible=strategy_eligible,
            trading_eligible=trading_eligible,
            routing_eligible=routing_eligible,
            account_connected=account_connectivity.account_identifier_configured,
            quote_available=bool(
                quote_snapshot is not None
                and quote_snapshot.quote_snapshot is not None
                and quote_snapshot.quote_snapshot.available
            ),
            available_balance_hint=account_snapshot.available_balance if account_snapshot is not None else None,
            venue_capabilities=capabilities,
            account_connectivity=account_connectivity,
            quote_snapshot=quote_snapshot,
            eligibility_reasons=eligibility_reasons,
        )

    async def _binding_quote_snapshot(
        self,
        *,
        binding_context: ActiveMandateBindingContext,
        instrument: InstrumentModel,
        symbol_model: SymbolModel | None,
        adapter: Any,
        account_connectivity: VenueAccountConnectivity,
    ) -> BindingQuoteSnapshot:
        quote_snapshot: VenueQuoteSnapshot | None = None
        if symbol_model is None:
            quote_snapshot = VenueQuoteSnapshot(
                instrument_key=instrument.instrument_key,
                instrument_ref_id=instrument.id,
                venue=binding_context.venue_account.venue,
                symbol=instrument.canonical_symbol,
                exchange_symbol="",
                bid_price=None,
                ask_price=None,
                bid_size=None,
                ask_size=None,
                observed_at=None,
                available=False,
                reason_unavailable="instrument_unavailable_on_venue",
            )
        else:
            try:
                top = await adapter.get_top_of_book(symbol_model.exchange_symbol)
            except Exception as exc:  # noqa: BLE001
                top = None
                quote_snapshot = VenueQuoteSnapshot(
                    instrument_key=instrument.instrument_key,
                    instrument_ref_id=instrument.id,
                    venue=binding_context.venue_account.venue,
                    symbol=instrument.canonical_symbol,
                    exchange_symbol=symbol_model.exchange_symbol,
                    bid_price=None,
                    ask_price=None,
                    bid_size=None,
                    ask_size=None,
                    observed_at=None,
                    available=False,
                    reason_unavailable=str(exc),
                )
            if quote_snapshot is None:
                if top is None:
                    quote_snapshot = VenueQuoteSnapshot(
                        instrument_key=instrument.instrument_key,
                        instrument_ref_id=instrument.id,
                        venue=binding_context.venue_account.venue,
                        symbol=instrument.canonical_symbol,
                        exchange_symbol=symbol_model.exchange_symbol,
                        bid_price=None,
                        ask_price=None,
                        bid_size=None,
                        ask_size=None,
                        observed_at=None,
                        available=False,
                        reason_unavailable="top_of_book_unavailable",
                    )
                else:
                    quote_snapshot = VenueQuoteSnapshot(
                        instrument_key=instrument.instrument_key,
                        instrument_ref_id=instrument.id,
                        venue=top.venue,
                        symbol=instrument.canonical_symbol,
                        exchange_symbol=symbol_model.exchange_symbol,
                        bid_price=top.bid_price,
                        ask_price=top.ask_price,
                        bid_size=top.bid_size,
                        ask_size=top.ask_size,
                        observed_at=top.observed_at,
                        available=bool(top.bid_price is not None and top.ask_price is not None),
                        reason_unavailable=None,
                    )
        connectivity_status = "configured"
        if not account_connectivity.account_identifier_configured:
            connectivity_status = "missing_account_identifier"
        elif account_connectivity.last_error:
            connectivity_status = "adapter_error"
        return BindingQuoteSnapshot(
            client_ref_id=binding_context.venue_account.client_ref_id,
            strategy_mandate_ref_id=binding_context.binding.strategy_mandate_ref_id,
            mandate_key=binding_context.binding.mandate_key,
            binding_ref_id=binding_context.binding.binding_ref_id,
            binding_key=binding_context.binding.binding_key,
            venue_account_ref_id=binding_context.venue_account.venue_account_ref_id,
            venue_account_key=binding_context.venue_account.venue_account_key,
            venue=binding_context.venue_account.venue,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol=instrument.canonical_symbol,
            exchange_symbol=symbol_model.exchange_symbol if symbol_model is not None else None,
            quote_snapshot=quote_snapshot,
            account_connectivity_status=connectivity_status,
            trading_eligible=binding_context.binding.trading_enabled,
            routing_eligible=binding_context.binding.routing_eligible,
        )

    def _candidate_reasons(
        self,
        *,
        binding_context: ActiveMandateBindingContext,
        component_config: StrategyComponentConfig | None,
        symbol_model: SymbolModel | None,
        capabilities: VenueCapabilities,
        status: Any,
        account_connectivity: VenueAccountConnectivity,
        quote_snapshot: BindingQuoteSnapshot,
    ) -> list[str]:
        reasons: list[str] = []
        binding = binding_context.binding
        if not binding.enabled:
            reasons.append("binding_disabled")
        if not binding.strategy_eligible:
            reasons.append("binding_strategy_ineligible")
        if not binding.routing_eligible:
            reasons.append("binding_routing_ineligible")
        if not binding.trading_enabled:
            reasons.append("binding_trading_disabled")
        if component_config is None:
            reasons.append("component_not_bound")
        elif not component_config.enabled:
            reasons.append("component_disabled")
        if symbol_model is None:
            reasons.append("instrument_unavailable_on_venue")
        else:
            if not symbol_model.is_strategy_eligible and not binding.allow_builder_deployed_for_strategy:
                reasons.append("symbol_not_strategy_eligible")
            if not symbol_model.is_trading_eligible and not binding.allow_builder_deployed_for_trading:
                reasons.append("symbol_not_trading_eligible")
        if not capabilities.supports_order_submission:
            reasons.append("venue_order_submission_unsupported")
        if capabilities.support_level.value != "execution_preparable":
            reasons.append("venue_not_execution_preparable")
        if status.read_only_mode:
            reasons.append("venue_read_only_mode")
        if not account_connectivity.account_identifier_configured:
            reasons.append("account_identifier_missing")
        if quote_snapshot.quote_snapshot is None or not quote_snapshot.quote_snapshot.available:
            reasons.append("quote_unavailable")
        return reasons

    def _resolve_component(
        self,
        components: Sequence[StrategyComponentConfig],
        component_key: str | None,
    ) -> StrategyComponentConfig | None:
        if component_key is None:
            return components[0] if components else None
        return next((component for component in components if component.component_key == component_key), None)

    def _lookup_symbol_for_binding(
        self,
        *,
        venue: str,
        instrument_ref_id: str,
    ) -> SymbolModel | None:
        with self._session_factory() as session:
            return session.scalar(
                select(SymbolModel)
                .where(
                    SymbolModel.venue == venue,
                    SymbolModel.instrument_ref_id == instrument_ref_id,
                    SymbolModel.is_active.is_(True),
                )
                .order_by(SymbolModel.exchange_symbol.asc())
            )

    def _latest_account_snapshot(self, venue_account_ref_id: str | None) -> ExchangeAccountSnapshotModel | None:
        if venue_account_ref_id is None:
            return None
        with self._session_factory() as session:
            return session.scalar(
                select(ExchangeAccountSnapshotModel)
                .where(
                    ExchangeAccountSnapshotModel.environment == self.settings.app.environment,
                    ExchangeAccountSnapshotModel.venue_account_ref_id == venue_account_ref_id,
                )
                .order_by(ExchangeAccountSnapshotModel.observed_at.desc())
            )

    def _load_decision_model(self, session: Any, decision_id: str) -> StrategyDecisionModel:
        decision = session.scalar(
            select(StrategyDecisionModel).where(
                StrategyDecisionModel.environment == self.settings.app.environment,
                StrategyDecisionModel.decision_id == decision_id,
            )
        )
        if decision is None:
            raise ValueError(f"Strategy decision not found: {decision_id}")
        return decision

    def _load_source_policy_for_decision(
        self,
        session: Any,
        decision: StrategyDecisionModel,
    ) -> MandateMarketDataSourcePolicy:
        if decision.strategy_mandate_ref_id is None:
            raise ValueError("Strategy decision is missing mandate context.")
        model = session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == decision.strategy_mandate_ref_id
            )
        )
        if model is None:
            raise ValueError(f"Market-data source policy missing for mandate: {decision.mandate_key}")
        return self._source_policy_from_model(model, mandate_key=decision.mandate_key)

    def _source_policy_from_model(
        self,
        model: MandateMarketDataSourcePolicyModel,
        *,
        mandate_key: str | None,
    ) -> MandateMarketDataSourcePolicy:
        runtime_exchange_venue = self.settings.exchange.venue
        return MandateMarketDataSourcePolicy(
            policy_ref_id=model.id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=mandate_key or "",
            source_mode=model.source_mode,
            source_venue=model.source_venue,
            market_type=model.market_type,
            product_type=model.product_type,
            instrument_resolution_mode=model.instrument_resolution_mode,
            runtime_exchange_venue=runtime_exchange_venue,
            runtime_exchange_matches_source=(model.source_venue == runtime_exchange_venue),
            notes=model.notes,
            metadata=dict(model.metadata_json or {}),
        )

    def _convertibility_assessment(
        self,
        decision: StrategyDecisionModel,
        *,
        instrument_key: str | None,
        source_policy: MandateMarketDataSourcePolicy,
        position: PositionModel | None,
    ) -> DesiredTradeConvertibilityAssessment:
        target_scope: TradeTargetScope | None = None
        reason_code: str | None = None
        message = "Convertible strategy decision."
        convertible = False

        if decision.status == StrategyDecisionStatus.NO_TRADE:
            reason_code = "decision_no_trade_not_convertible"
            message = "No-trade strategy decisions do not become mandate desired trades."
        elif decision.status == StrategyDecisionStatus.INVALID:
            reason_code = "decision_invalid_not_convertible"
            message = "Invalid strategy decisions do not become mandate desired trades."
        elif decision.status != StrategyDecisionStatus.PROPOSED:
            reason_code = "decision_status_not_supported"
            message = f"Strategy decision status is not convertible: {decision.status.value}."
        elif instrument_key is None or decision.instrument_ref_id is None:
            reason_code = "instrument_identity_missing"
            message = "Convertible planning requires canonical instrument identity."
        elif decision.action == DecisionAction.OPEN:
            convertible = True
            target_scope = TradeTargetScope.MANDATE
            message = "Open proposals become mandate-scoped desired trade drafts."
        elif decision.action == DecisionAction.HOLD:
            reason_code = "hold_non_convertible"
            message = "Hold proposals remain inspection-only and do not become desired trades."
        elif decision.action == DecisionAction.REDUCE:
            if not decision.mandate_account_binding_ref_id or not decision.venue_account_ref_id:
                reason_code = "binding_context_required_for_reduce"
                message = "Reduce proposals require binding/account context."
            else:
                convertible = True
                target_scope = TradeTargetScope.BINDING
                message = "Reduce proposals become binding-scoped desired trade drafts."
        elif decision.action == DecisionAction.CLOSE:
            if not decision.mandate_account_binding_ref_id or not decision.venue_account_ref_id:
                reason_code = "binding_context_required_for_close"
                message = "Close proposals require binding/account context."
            elif position is None:
                reason_code = "open_position_required_for_close"
                message = "Close proposals require an open bound position for quantity derivation."
            else:
                convertible = True
                target_scope = TradeTargetScope.BINDING
                message = "Close proposals become binding-scoped desired trade drafts."
        else:
            reason_code = "action_not_convertible"
            message = f"Action is not convertible in Phase 4.0.2: {decision.action.value}."

        desired_trade_key_preview = None
        if convertible and target_scope is not None:
            desired_trade_key_preview = self._desired_trade_key_for_decision(
                decision,
                instrument_key=instrument_key,
                source_policy=source_policy,
                target_scope=target_scope,
            )
        return DesiredTradeConvertibilityAssessment(
            decision_id=decision.decision_id,
            convertible=convertible,
            decision_status=decision.status,
            action=decision.action,
            target_scope=target_scope,
            reason_code=reason_code,
            message=message,
            instrument_key=instrument_key,
            desired_trade_key_preview=desired_trade_key_preview,
        )

    def _desired_trade_from_decision_model(
        self,
        decision: StrategyDecisionModel,
        *,
        instrument_key: str | None,
        source_policy: MandateMarketDataSourcePolicy,
        position: PositionModel | None,
    ) -> MandateDesiredTrade:
        assessment = self._convertibility_assessment(
            decision,
            instrument_key=instrument_key,
            source_policy=source_policy,
            position=position,
        )
        if not assessment.convertible or assessment.target_scope is None:
            raise DesiredTradeConversionError(
                assessment.reason_code or "non_convertible",
                assessment.message,
            )
        target_scope = assessment.target_scope
        side = self._side_for_action(decision.action)
        planning_as_of = _parse_planning_as_of(dict(decision.provenance or {}))
        desired_trade_key = assessment.desired_trade_key_preview
        assert desired_trade_key is not None
        desired_quantity = None
        if decision.action == DecisionAction.CLOSE and position is not None:
            desired_quantity = position.quantity
        source_binding_keys = _dedupe([decision.binding_key or ""])
        source_evaluation_keys = _dedupe([decision.evaluation_key])
        provenance = {
            **dict(decision.provenance or {}),
            "phase_boundary": "phase_4_0_2",
            "convertibility_rule": assessment.message,
            "planning_source_policy": {
                "policy_ref_id": source_policy.policy_ref_id,
                "source_mode": source_policy.source_mode.value,
                "source_venue": source_policy.source_venue,
                "market_type": source_policy.market_type.value if source_policy.market_type is not None else None,
                "product_type": source_policy.product_type.value if source_policy.product_type is not None else None,
                "instrument_resolution_mode": source_policy.instrument_resolution_mode.value,
            },
            "source_decision_status": decision.status.value,
            "source_signal_id": decision.signal_id,
            "source_reason_code": decision.reason_code,
            "source_decision_count": 1,
            "source_binding_count": len(source_binding_keys),
            "order_intent_role": "downstream_binding_child_intent_only",
        }
        return MandateDesiredTrade(
            desired_trade_key=desired_trade_key,
            desired_trade_ref_id=None,
            evaluated_state_fingerprint=self._evaluated_state_fingerprint(
                desired_trade_key=desired_trade_key,
                planning_as_of=planning_as_of,
                source_decision_ids=[decision.decision_id],
                source_evaluation_keys=source_evaluation_keys,
                source_binding_keys=source_binding_keys,
            ),
            environment=decision.environment,
            client_ref_id=decision.client_ref_id,
            strategy_mandate_ref_id=decision.strategy_mandate_ref_id,
            mandate_key=decision.mandate_key,
            family=decision.family,
            component_key=decision.component_key or decision.sleeve_id,
            market_data_source_policy_ref_id=source_policy.policy_ref_id,
            planning_source_venue=source_policy.source_venue,
            planning_source_mode=source_policy.source_mode,
            planning_as_of=planning_as_of,
            target_scope=target_scope,
            mandate_account_binding_ref_id=(
                decision.mandate_account_binding_ref_id if target_scope == TradeTargetScope.BINDING else None
            ),
            binding_key=decision.binding_key if target_scope == TradeTargetScope.BINDING else None,
            venue_account_ref_id=decision.venue_account_ref_id if target_scope == TradeTargetScope.BINDING else None,
            instrument_key=instrument_key,
            instrument_ref_id=decision.instrument_ref_id,
            symbol=decision.symbol,
            action=decision.action,
            side=side,
            desired_quantity=desired_quantity,
            desired_notional=None,
            source_decision_ids=[decision.decision_id],
            source_evaluation_keys=source_evaluation_keys,
            source_binding_keys=source_binding_keys,
            status=MandateDesiredTradeStatus.DRAFT,
            status_reason_code=None,
            status_message=None,
            provenance=provenance,
            created_at=_utcnow(),
            approved_at=None,
            rejected_at=None,
        )

    def _desired_trade_key_for_decision(
        self,
        decision: StrategyDecisionModel,
        *,
        instrument_key: str,
        source_policy: MandateMarketDataSourcePolicy,
        target_scope: TradeTargetScope,
    ) -> str:
        planning_as_of = _parse_planning_as_of(dict(decision.provenance or {}))
        return _json_fingerprint(
            {
                "environment": decision.environment.value,
                "family": decision.family.value,
                "strategy_version": dict(decision.provenance or {}).get("strategy_version"),
                "mandate_key": decision.mandate_key,
                "strategy_mandate_ref_id": decision.strategy_mandate_ref_id,
                "component_key": decision.component_key or decision.sleeve_id,
                "instrument_key": instrument_key,
                "instrument_ref_id": decision.instrument_ref_id,
                "action": decision.action.value,
                "side": self._side_for_action(decision.action).value if self._side_for_action(decision.action) else None,
                "target_scope": target_scope.value,
                "binding_key": decision.binding_key if target_scope == TradeTargetScope.BINDING else None,
                "venue_account_ref_id": (
                    decision.venue_account_ref_id if target_scope == TradeTargetScope.BINDING else None
                ),
                "position_state_fingerprint": (
                    dict(decision.provenance or {}).get("position_state_fingerprint")
                    if target_scope == TradeTargetScope.BINDING
                    else None
                ),
                "source_policy_ref_id": source_policy.policy_ref_id,
                "source_mode": source_policy.source_mode.value,
                "source_venue": source_policy.source_venue,
                "market_type": source_policy.market_type.value if source_policy.market_type is not None else None,
                "product_type": source_policy.product_type.value if source_policy.product_type is not None else None,
                "planning_as_of": planning_as_of.isoformat() if planning_as_of is not None else None,
            }
        )

    @staticmethod
    def _evaluated_state_fingerprint(
        *,
        desired_trade_key: str,
        planning_as_of: datetime | None,
        source_decision_ids: Sequence[str],
        source_evaluation_keys: Sequence[str],
        source_binding_keys: Sequence[str],
    ) -> str:
        return _json_fingerprint(
            {
                "desired_trade_key": desired_trade_key,
                "planning_as_of": planning_as_of.isoformat() if planning_as_of is not None else None,
                "source_decision_ids": _dedupe(source_decision_ids),
                "source_evaluation_keys": _dedupe(source_evaluation_keys),
                "source_binding_keys": _dedupe(source_binding_keys),
            }
        )

    @staticmethod
    def _side_for_action(action: DecisionAction) -> OrderSide | None:
        if action in {DecisionAction.OPEN, DecisionAction.ADD}:
            return OrderSide.BUY
        if action in {DecisionAction.REDUCE, DecisionAction.CLOSE}:
            return OrderSide.SELL
        return None

    @staticmethod
    def _lookup_instrument_key(session: Any, instrument_ref_id: str | None) -> str | None:
        if instrument_ref_id is None:
            return None
        return session.scalar(
            select(InstrumentModel.instrument_key).where(InstrumentModel.id == instrument_ref_id)
        )

    @staticmethod
    def _lookup_symbol_id(
        session: Any,
        *,
        instrument_ref_id: str | None,
        venue: str | None,
        symbol: str,
    ) -> str | None:
        query = select(SymbolModel.id).where(
            SymbolModel.instrument_ref_id == instrument_ref_id,
            SymbolModel.symbol == symbol,
        )
        if venue is not None:
            query = query.where(SymbolModel.venue == venue)
        return session.scalar(query)

    def _load_bound_position(
        self,
        session: Any,
        *,
        instrument_ref_id: str | None,
        venue_account_ref_id: str | None,
    ) -> PositionModel | None:
        if instrument_ref_id is None or venue_account_ref_id is None:
            return None
        return session.scalar(
            select(PositionModel).where(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.instrument_ref_id == instrument_ref_id,
                PositionModel.venue_account_ref_id == venue_account_ref_id,
                PositionModel.status == PositionStatus.OPEN,
            )
        )

    def _merge_with_existing_model(
        self,
        desired_trade: MandateDesiredTrade,
        existing_model: MandateDesiredTradeModel,
    ) -> MandateDesiredTrade:
        existing_trade = self._desired_trade_from_model(existing_model)
        source_decision_ids = _dedupe(existing_trade.source_decision_ids + desired_trade.source_decision_ids)
        source_evaluation_keys = _dedupe(
            existing_trade.source_evaluation_keys + desired_trade.source_evaluation_keys
        )
        source_binding_keys = _dedupe(existing_trade.source_binding_keys + desired_trade.source_binding_keys)
        provenance = {
            **dict(existing_trade.provenance),
            **dict(desired_trade.provenance),
            "source_decision_count": len(source_decision_ids),
            "source_binding_count": len(source_binding_keys),
            "phase_boundary": "phase_4_0_2",
            "order_intent_role": "downstream_binding_child_intent_only",
        }
        return MandateDesiredTrade(
            desired_trade_key=existing_trade.desired_trade_key,
            desired_trade_ref_id=existing_trade.desired_trade_ref_id,
            evaluated_state_fingerprint=self._evaluated_state_fingerprint(
                desired_trade_key=existing_trade.desired_trade_key,
                planning_as_of=desired_trade.planning_as_of or existing_trade.planning_as_of,
                source_decision_ids=source_decision_ids,
                source_evaluation_keys=source_evaluation_keys,
                source_binding_keys=source_binding_keys,
            ),
            environment=existing_trade.environment,
            client_ref_id=existing_trade.client_ref_id,
            strategy_mandate_ref_id=existing_trade.strategy_mandate_ref_id,
            mandate_key=existing_trade.mandate_key,
            family=existing_trade.family,
            component_key=existing_trade.component_key,
            market_data_source_policy_ref_id=existing_trade.market_data_source_policy_ref_id,
            planning_source_venue=existing_trade.planning_source_venue,
            planning_source_mode=existing_trade.planning_source_mode,
            planning_as_of=desired_trade.planning_as_of or existing_trade.planning_as_of,
            target_scope=existing_trade.target_scope,
            mandate_account_binding_ref_id=existing_trade.mandate_account_binding_ref_id,
            binding_key=existing_trade.binding_key,
            venue_account_ref_id=existing_trade.venue_account_ref_id,
            instrument_key=existing_trade.instrument_key,
            instrument_ref_id=existing_trade.instrument_ref_id,
            symbol=existing_trade.symbol,
            action=existing_trade.action,
            side=existing_trade.side,
            desired_quantity=desired_trade.desired_quantity or existing_trade.desired_quantity,
            desired_notional=desired_trade.desired_notional or existing_trade.desired_notional,
            source_decision_ids=source_decision_ids,
            source_evaluation_keys=source_evaluation_keys,
            source_binding_keys=source_binding_keys,
            status=existing_trade.status,
            status_reason_code=existing_trade.status_reason_code,
            status_message=existing_trade.status_message,
            provenance=provenance,
            created_at=existing_trade.created_at,
            approved_at=existing_trade.approved_at,
            rejected_at=existing_trade.rejected_at,
        )

    def _persist_desired_trade(
        self,
        session: Any,
        desired_trade: MandateDesiredTrade,
        *,
        existing_model: MandateDesiredTradeModel | None,
    ) -> MandateDesiredTradeModel:
        model = existing_model
        if model is None:
            model = MandateDesiredTradeModel(
                environment=desired_trade.environment,
                desired_trade_key=desired_trade.desired_trade_key,
                evaluated_state_fingerprint=desired_trade.evaluated_state_fingerprint,
                client_ref_id=desired_trade.client_ref_id,
                strategy_mandate_ref_id=desired_trade.strategy_mandate_ref_id,
                market_data_source_policy_ref_id=desired_trade.market_data_source_policy_ref_id,
                mandate_account_binding_ref_id=desired_trade.mandate_account_binding_ref_id,
                mandate_key=desired_trade.mandate_key,
                binding_key=desired_trade.binding_key,
                venue_account_ref_id=desired_trade.venue_account_ref_id,
                family=desired_trade.family,
                component_key=desired_trade.component_key,
                planning_source_venue=desired_trade.planning_source_venue,
                planning_source_mode=desired_trade.planning_source_mode,
                planning_as_of=desired_trade.planning_as_of,
                target_scope=desired_trade.target_scope,
                instrument_key=desired_trade.instrument_key,
                instrument_ref_id=desired_trade.instrument_ref_id,
                symbol_id=self._lookup_symbol_id(
                    session,
                    instrument_ref_id=desired_trade.instrument_ref_id,
                    venue=desired_trade.planning_source_venue,
                    symbol=desired_trade.symbol,
                ),
                symbol=desired_trade.symbol,
                action=desired_trade.action,
                side=desired_trade.side,
                desired_quantity=desired_trade.desired_quantity,
                desired_notional=desired_trade.desired_notional,
                source_decision_ids_json=list(desired_trade.source_decision_ids),
                source_evaluation_keys_json=list(desired_trade.source_evaluation_keys),
                source_binding_keys_json=list(desired_trade.source_binding_keys),
                status=desired_trade.status,
                status_reason_code=desired_trade.status_reason_code,
                status_message=desired_trade.status_message,
                provenance=dict(desired_trade.provenance),
                created_at=desired_trade.created_at or _utcnow(),
                approved_at=desired_trade.approved_at,
                rejected_at=desired_trade.rejected_at,
            )
            session.add(model)
            session.flush()
            return model
        model.evaluated_state_fingerprint = desired_trade.evaluated_state_fingerprint
        model.client_ref_id = desired_trade.client_ref_id
        model.strategy_mandate_ref_id = desired_trade.strategy_mandate_ref_id
        model.market_data_source_policy_ref_id = desired_trade.market_data_source_policy_ref_id
        model.mandate_account_binding_ref_id = desired_trade.mandate_account_binding_ref_id
        model.mandate_key = desired_trade.mandate_key
        model.binding_key = desired_trade.binding_key
        model.venue_account_ref_id = desired_trade.venue_account_ref_id
        model.family = desired_trade.family
        model.component_key = desired_trade.component_key
        model.planning_source_venue = desired_trade.planning_source_venue
        model.planning_source_mode = desired_trade.planning_source_mode
        model.planning_as_of = desired_trade.planning_as_of
        model.target_scope = desired_trade.target_scope
        model.instrument_key = desired_trade.instrument_key
        model.instrument_ref_id = desired_trade.instrument_ref_id
        model.symbol_id = self._lookup_symbol_id(
            session,
            instrument_ref_id=desired_trade.instrument_ref_id,
            venue=desired_trade.planning_source_venue,
            symbol=desired_trade.symbol,
        )
        model.symbol = desired_trade.symbol
        model.action = desired_trade.action
        model.side = desired_trade.side
        model.desired_quantity = desired_trade.desired_quantity
        model.desired_notional = desired_trade.desired_notional
        model.source_decision_ids_json = list(desired_trade.source_decision_ids)
        model.source_evaluation_keys_json = list(desired_trade.source_evaluation_keys)
        model.source_binding_keys_json = list(desired_trade.source_binding_keys)
        model.status = desired_trade.status
        model.status_reason_code = desired_trade.status_reason_code
        model.status_message = desired_trade.status_message
        model.provenance = dict(desired_trade.provenance)
        model.approved_at = desired_trade.approved_at
        model.rejected_at = desired_trade.rejected_at
        return model

    @staticmethod
    def _desired_trade_from_model(model: MandateDesiredTradeModel) -> MandateDesiredTrade:
        return MandateDesiredTrade(
            desired_trade_key=model.desired_trade_key,
            desired_trade_ref_id=model.id,
            evaluated_state_fingerprint=model.evaluated_state_fingerprint,
            environment=model.environment,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            family=model.family,
            component_key=model.component_key,
            market_data_source_policy_ref_id=model.market_data_source_policy_ref_id,
            planning_source_venue=model.planning_source_venue,
            planning_source_mode=model.planning_source_mode,
            planning_as_of=model.planning_as_of,
            target_scope=model.target_scope,
            mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
            binding_key=model.binding_key,
            venue_account_ref_id=model.venue_account_ref_id,
            instrument_key=model.instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            action=model.action,
            side=model.side,
            desired_quantity=model.desired_quantity,
            desired_notional=model.desired_notional,
            source_decision_ids=list(model.source_decision_ids_json or []),
            source_evaluation_keys=list(model.source_evaluation_keys_json or []),
            source_binding_keys=list(model.source_binding_keys_json or []),
            status=model.status,
            status_reason_code=model.status_reason_code,
            status_message=model.status_message,
            provenance=dict(model.provenance or {}),
            created_at=model.created_at,
            approved_at=model.approved_at,
            rejected_at=model.rejected_at,
        )
