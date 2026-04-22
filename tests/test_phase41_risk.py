from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderIntentStatus,
    VenueOrderPreviewStatus,
    OrderSide,
    PositionStatus,
    ProductType,
    RiskEvaluationOutcome,
    StrategyDecisionStatus,
    StrategyFamily,
    Venue,
    VenueSupportLevel,
    OrderType,
)
from core.domain.models import (
    ExchangeStatus,
    PreparedVenueOrder,
    TopOfBookSnapshot,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueOrderConstraints,
)
from db.models import (
    InstrumentModel,
    MandateDesiredTradeModel,
    MandateMarketDataSourcePolicyModel,
    OrderIntentModel,
    PositionModel,
    RiskEvaluationModel,
    StrategyDecisionModel,
    StrategyMandateModel,
)
from services.execution.service import DefaultExecutionService
from services.planning.service import DefaultTradePlanningService
from services.risk.engine import DefaultRiskEngine
from services.runtime.context import DefaultRuntimeContextService
from tests.test_phase3_strategy import build_settings, build_test_session_factory, seed_symbol


class _StubVenueAdapter:
    def __init__(self, *, venue: str) -> None:
        self._venue = venue

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue(self._venue),
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            supports_spot=False,
            supports_perpetuals=True,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=False,
            supports_account_sync=True,
            supports_top_of_book=True,
            supports_depth_summary=False,
            supports_order_submission=True,
            supports_order_cancel=True,
            supports_order_amend=True,
            supports_recent_fills_query=False,
            adapter_supports_order_submission=False,
            adapter_supports_order_cancel=False,
            adapter_supports_order_amend=False,
            adapter_supports_user_streams=False,
            supports_order_preview=True,
            supports_account_snapshot=True,
            supports_open_orders_query=True,
            supports_open_positions_query=True,
            supports_reduce_only_orders=True,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=False,
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
            supported_time_in_force=["gtc", "ioc"],
            account_model="wallet_address",
            private_lifecycle_update_mode="polling",
        )

    async def get_exchange_status(self) -> ExchangeStatus:
        return ExchangeStatus(
            venue=self._venue,
            environment=Environment.TESTNET,
            connected=True,
            api_base_url=f"https://{self._venue}.example",
            websocket_base_url=f"wss://{self._venue}.example/ws",
            can_sign_orders=False,
            wallet_address_configured=True,
            account_identifier_configured=True,
            credentials_configured=False,
            read_only_mode=True,
            dry_run_mode=True,
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            adapter_supports_order_submission=False,
            adapter_supports_order_cancel=False,
            adapter_supports_order_amend=False,
            adapter_supports_user_streams=False,
            submission_authorized=False,
            live_submission_phase_enabled=False,
            last_success_at=datetime.now(UTC),
            last_error=None,
            private_lifecycle_update_mode="polling",
        )

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        return TopOfBookSnapshot(
            instrument_key="perpetual:linear:BTC:USDC:USDC",
            instrument_ref_id="inst-1",
            venue=self._venue,
            symbol=symbol,
            bid_price=Decimal("100"),
            bid_size=Decimal("2"),
            ask_price=Decimal("101"),
            ask_size=Decimal("3"),
            observed_at=datetime.now(UTC),
        )

    async def prepare_order_preview(self, intent):
        return PreparedVenueOrder(
            intent_id=intent.intent_id,
            desired_trade_key=intent.desired_trade_key,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=self._venue,
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            exchange_symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            reduce_only=intent.reduce_only,
            time_in_force="ioc",
            client_order_id="mf-preview",
            preview_status=VenueOrderPreviewStatus.PREPARABLE,
            reason_codes=[],
            payload={"endpoint": "/exchange"},
            constraints=VenueOrderConstraints(
                venue=self._venue,
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                instrument_key=intent.instrument_key,
                instrument_ref_id=intent.instrument_ref_id,
                symbol=intent.symbol,
                exchange_symbol=intent.symbol,
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                price_tick_size=Decimal("0.1"),
                quantity_step_size=Decimal("0.001"),
                min_order_size=Decimal("0.001"),
                supports_order_preview=True,
                supports_reduce_only_orders=True,
                supports_client_order_ids=True,
                supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
                supported_time_in_force=["gtc", "ioc"],
                constraint_metadata_complete=True,
                notes=None,
            ),
            venue_capabilities=await self.get_venue_capabilities(),
            account_connectivity=VenueAccountConnectivity(
                venue=self._venue,
                environment=Environment.TESTNET,
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                account_model="wallet_address",
                account_identifier="acct",
                account_label="primary",
                subaccount_label=None,
                credentials_ref=None,
                account_identifier_configured=True,
                credentials_configured=False,
                read_only_mode=True,
                dry_run_mode=True,
                submission_authorized=False,
                private_account_sync_enabled=False,
                account_snapshot_available=False,
                open_orders_query_available=True,
                open_positions_query_available=True,
                last_success_at=datetime.now(UTC),
                last_error=None,
            ),
            prepared_at=datetime.now(UTC),
        )


class _StubVenueRegistry:
    def __init__(self) -> None:
        self._adapter = _StubVenueAdapter(venue=Venue.HYPERLIQUID.value)

    async def list_supported_venues(self):
        raise NotImplementedError

    async def get_adapter(self, venue: str):
        assert venue == Venue.HYPERLIQUID.value
        return self._adapter


def _build_services(session_factory, **settings_overrides: object):
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::phase41", **settings_overrides)
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    venue_registry = _StubVenueRegistry()
    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=venue_registry,
    )
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=venue_registry,
    )
    risk = DefaultRiskEngine(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        planning_service=planning,
        execution_service=execution,
    )
    return settings, runtime, planning, execution, risk


def _seed_decision(
    session_factory,
    *,
    context,
    decision_id: str,
    evaluation_key: str,
    instrument_ref_id: str,
    action: DecisionAction,
    status: StrategyDecisionStatus = StrategyDecisionStatus.PROPOSED,
    component_key: str = "sleeve_1h",
) -> None:
    with session_factory() as session:
        session.add(
            StrategyDecisionModel(
                environment=Environment.TESTNET,
                decision_id=decision_id,
                evaluation_key=evaluation_key,
                family=StrategyFamily.MONEY_FLOW,
                signal_id=f"signal-{decision_id}",
                sleeve_id=component_key,
                component_key=component_key,
                client_ref_id=context.client.client_ref_id,
                strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                mandate_key=context.mandate.mandate_key,
                binding_key=context.bindings[0].binding.binding_key,
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol="BTC",
                action=action,
                status=status,
                reason_code=None,
                confidence=Decimal("0.8"),
                rationale="phase_4_1_test",
                provenance={
                    "strategy_version": "money_flow_v1_1",
                    "indicator_as_of": datetime.now(UTC).replace(microsecond=0).isoformat(),
                    "latest_candle_close": datetime.now(UTC).replace(microsecond=0).isoformat(),
                },
                features={},
                decided_at=datetime.now(UTC),
            )
        )
        session.commit()


def _seed_open_position(session_factory, *, context, instrument_ref_id: str, quantity: Decimal = Decimal("0.25")) -> None:
    with session_factory() as session:
        session.add(
            PositionModel(
                environment=Environment.TESTNET,
                position_id=f"pos-{quantity}",
                exchange_position_key="btc-one-way",
                account_position_key="acct:btc:one_way",
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                sleeve_id=None,
                venue=Venue.HYPERLIQUID.value,
                account_address="acct",
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol="BTC",
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                attribution_status=AttributionStatus.UNASSIGNED,
                quantity=quantity,
                avg_entry_price=Decimal("100"),
                mark_price=Decimal("101"),
                unrealized_pnl=Decimal("0.25"),
                position_value=Decimal("25.25"),
                margin_used=Decimal("5"),
                liquidation_price=Decimal("80"),
                leverage_type="cross",
                leverage_value=5,
                raw_payload={},
                opened_at=datetime.now(UTC),
            )
        )
        session.commit()


def _set_source_policy_venue(session_factory, *, mandate_key: str, source_venue: str) -> None:
    with session_factory() as session:
        mandate = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        assert mandate is not None
        policy = session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == mandate.id
            )
        )
        assert policy is not None
        policy.source_mode = MarketDataSourceMode.SINGLE_VENUE
        policy.source_venue = source_venue
        policy.market_type = MarketType.PERPETUAL
        policy.product_type = ProductType.LINEAR
        session.commit()


def test_open_decision_becomes_routing_required_without_child_intent() -> None:
    session_factory = build_test_session_factory()
    _settings, runtime, _planning, _execution, risk = _build_services(session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-open",
        evaluation_key="eval-open",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.OPEN,
    )

    evaluation = asyncio.run(risk.evaluate_strategy_decision("decision-open"))

    assert evaluation.outcome == RiskEvaluationOutcome.ROUTING_REQUIRED
    assert evaluation.desired_trade_status == MandateDesiredTradeStatus.ROUTING_REQUIRED
    assert evaluation.child_intent_id is None
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 1
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        model = session.scalar(select(MandateDesiredTradeModel))
        assert model is not None
        assert model.status == MandateDesiredTradeStatus.ROUTING_REQUIRED
        assert model.status_reason_code == "routing_required_target_not_selected"
        assert model.approved_at is not None


def test_hold_no_trade_and_invalid_do_not_create_desired_trades() -> None:
    session_factory = build_test_session_factory()
    _settings, runtime, _planning, _execution, risk = _build_services(session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-hold",
        evaluation_key="eval-hold",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.HOLD,
    )
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-no-trade",
        evaluation_key="eval-no-trade",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.OPEN,
        status=StrategyDecisionStatus.NO_TRADE,
    )
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-invalid",
        evaluation_key="eval-invalid",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.OPEN,
        status=StrategyDecisionStatus.INVALID,
    )

    hold_eval = asyncio.run(risk.evaluate_strategy_decision("decision-hold"))
    no_trade_eval = asyncio.run(risk.evaluate_strategy_decision("decision-no-trade"))
    invalid_eval = asyncio.run(risk.evaluate_strategy_decision("decision-invalid"))

    assert hold_eval.outcome == RiskEvaluationOutcome.NO_DESIRED_TRADE
    assert no_trade_eval.outcome == RiskEvaluationOutcome.NO_DESIRED_TRADE
    assert invalid_eval.outcome == RiskEvaluationOutcome.NO_DESIRED_TRADE
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(RiskEvaluationModel)) == 3


def test_reduce_decision_approves_and_prepares_idempotent_child_intent() -> None:
    session_factory = build_test_session_factory()
    _settings, runtime, _planning, _execution, risk = _build_services(session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)
    _seed_open_position(session_factory, context=context, instrument_ref_id=instrument_ref_id)
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-reduce",
        evaluation_key="eval-reduce",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.REDUCE,
        component_key="sleeve_4h",
    )

    first = asyncio.run(risk.evaluate_strategy_decision("decision-reduce"))
    second = asyncio.run(risk.evaluate_strategy_decision("decision-reduce"))

    assert first.outcome == RiskEvaluationOutcome.APPROVED_DESIRED_TRADE
    assert first.desired_trade_status == MandateDesiredTradeStatus.APPROVED
    assert first.child_intent_id is not None
    assert second.child_intent_id == first.child_intent_id
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 1
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 1
        assert session.scalar(select(func.count()).select_from(RiskEvaluationModel)) == 1
        intent = session.scalar(select(OrderIntentModel))
        assert intent is not None
        assert intent.status == OrderIntentStatus.PREPARED
        assert intent.reduce_only is True
        assert intent.quantity == Decimal("0.125000000000")


def test_close_decision_requires_open_position_and_prepares_full_close_intent() -> None:
    session_factory = build_test_session_factory()
    _settings, runtime, _planning, _execution, risk = _build_services(session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-close-missing",
        evaluation_key="eval-close-missing",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.CLOSE,
    )

    rejected = asyncio.run(risk.evaluate_strategy_decision("decision-close-missing"))
    assert rejected.outcome == RiskEvaluationOutcome.NO_DESIRED_TRADE
    assert rejected.reason_code == "open_position_required_for_close"

    _seed_open_position(session_factory, context=context, instrument_ref_id=instrument_ref_id, quantity=Decimal("0.40"))
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-close",
        evaluation_key="eval-close",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.CLOSE,
    )

    approved = asyncio.run(risk.evaluate_strategy_decision("decision-close"))
    assert approved.outcome == RiskEvaluationOutcome.APPROVED_DESIRED_TRADE
    assert approved.child_intent_id is not None
    with session_factory() as session:
        close_trade = session.scalar(
            select(MandateDesiredTradeModel).where(MandateDesiredTradeModel.desired_trade_key == approved.desired_trade_key)
        )
        assert close_trade is not None
        assert close_trade.status == MandateDesiredTradeStatus.APPROVED
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == approved.child_intent_id))
        assert intent is not None
        assert intent.quantity == Decimal("0.400000000000")


def test_source_policy_runtime_mismatch_rejects_desired_trade() -> None:
    session_factory = build_test_session_factory()
    _settings, runtime, _planning, _execution, risk = _build_services(session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)
    _seed_decision(
        session_factory,
        context=context,
        decision_id="decision-open-mismatch",
        evaluation_key="eval-open-mismatch",
        instrument_ref_id=instrument_ref_id,
        action=DecisionAction.OPEN,
    )
    _set_source_policy_venue(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        source_venue=Venue.OKX.value,
    )

    evaluation = asyncio.run(risk.evaluate_strategy_decision("decision-open-mismatch"))

    assert evaluation.outcome == RiskEvaluationOutcome.INVALID_INPUT
    assert evaluation.reason_code == "planning_source_runtime_mismatch"
    with session_factory() as session:
        trade = session.scalar(select(MandateDesiredTradeModel))
        assert trade is not None
        assert trade.status == MandateDesiredTradeStatus.REJECTED
        assert trade.status_reason_code == "planning_source_runtime_mismatch"
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
