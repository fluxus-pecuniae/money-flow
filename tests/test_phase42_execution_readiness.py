from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    DecisionAction,
    Environment,
    ExecutionReadinessOutcome,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    ProductType,
    StrategyFamily,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.models import (
    ExecutionReadinessAssessment,
    OrderIntent,
    PreparedVenueOrder,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueOrderConstraints,
)
from db.models import (
    ClientModel,
    ExecutionReadinessEvaluationModel,
    InstrumentModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    StrategyMandateModel,
    SymbolModel,
    VenueAccountModel,
)
from services.execution.service import DefaultExecutionService
from tests.test_phase3_strategy import build_settings, build_test_session_factory


def _seed_intent(
    session_factory,
    *,
    venue: str,
    symbol: str = "BTC",
) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-1"))
        if client is None:
            client = ClientModel(client_key="client-1", display_name="Client 1", is_active=True)
            session.add(client)
            session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::{venue}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()
        account = VenueAccountModel(
            venue_account_key=f"{venue}-acct",
            client_ref_id=client.id,
            venue=venue,
            environment=Environment.TESTNET,
            venue_native_account_id=f"{venue}-native",
            account_address=f"{venue}-acct",
            account_label="primary",
            subaccount_label=None,
            credentials_ref="secret://acct",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={},
        )
        session.add(account)
        session.flush()
        binding = MandateAccountBindingModel(
            strategy_mandate_ref_id=mandate.id,
            binding_key=f"{mandate.mandate_key}::{account.venue_account_key}",
            venue_account_ref_id=account.id,
            enabled=True,
            strategy_eligible=True,
            routing_eligible=True,
            trading_enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(binding)
        session.flush()
        instrument_key = f"perpetual:linear:{symbol}:USDT:USDT"
        instrument = session.scalar(
            select(InstrumentModel).where(InstrumentModel.instrument_key == instrument_key)
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key=instrument_key,
                canonical_symbol=symbol,
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset=symbol,
                quote_asset="USDT",
                settlement_asset="USDT",
                is_active=True,
            )
            session.add(instrument)
            session.flush()
        symbol_model = SymbolModel(
            instrument_ref_id=instrument.id,
            venue=venue,
            symbol=symbol,
            exchange_symbol=symbol if venue == Venue.HYPERLIQUID.value else f"{symbol}-USDT",
            venue_asset_id=f"{symbol}-asset",
            asset_id=None,
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset=symbol,
            quote_asset="USDT",
            settlement_asset="USDT",
            price_tick_size=Decimal("0.1"),
            quantity_step_size=Decimal("0.001"),
            min_order_size=Decimal("0.001"),
            size_decimals=3,
            max_leverage=20,
            only_isolated=False,
            is_perpetual=True,
            is_builder_deployed=False,
            is_strategy_eligible=True,
            is_trading_eligible=True,
            is_active=True,
            raw_metadata={},
        )
        session.add(symbol_model)
        session.flush()
        session.add(
            OrderIntentModel(
                environment=Environment.TESTNET,
                intent_id=f"intent-{venue}",
                decision_id=f"decision-{venue}",
                action=DecisionAction.REDUCE,
                mandate_desired_trade_ref_id=None,
                desired_trade_key=f"trade-{venue}",
                sleeve_id="sleeve_1h",
                component_key="sleeve_1h",
                client_ref_id=client.id,
                strategy_mandate_ref_id=mandate.id,
                mandate_account_binding_ref_id=binding.id,
                binding_key=binding.binding_key,
                venue_account_ref_id=account.id,
                instrument_key=instrument.instrument_key,
                instrument_ref_id=instrument.id,
                symbol_id=symbol_model.id,
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=Decimal("0.01"),
                limit_price=None,
                reduce_only=True,
                ttl_seconds=30,
                status=OrderIntentStatus.PREPARED,
                idempotency_key=f"idem-{venue}",
                provenance={"phase_boundary": "phase_4_1_1"},
                created_at=datetime.now(UTC),
            )
        )
        session.commit()
        return f"intent-{venue}"


def _set_binding_account_state(
    session_factory,
    intent_id: str,
    *,
    binding_enabled: bool | None = None,
    binding_routing_eligible: bool | None = None,
    venue_account_active: bool | None = None,
) -> None:
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert intent is not None
        binding = session.get(MandateAccountBindingModel, intent.mandate_account_binding_ref_id)
        account = session.get(VenueAccountModel, intent.venue_account_ref_id)
        assert binding is not None
        assert account is not None
        if binding_enabled is not None:
            binding.enabled = binding_enabled
        if binding_routing_eligible is not None:
            binding.routing_eligible = binding_routing_eligible
        if venue_account_active is not None:
            account.is_active = venue_account_active
        session.add(binding)
        session.add(account)
        session.commit()


class _StubVenueAdapter:
    def __init__(
        self,
        *,
        venue: str,
        support_level: VenueSupportLevel = VenueSupportLevel.EXECUTION_PREPARABLE,
        venue_supports_submission: bool = True,
        adapter_supports_submission: bool = False,
        adapter_supports_order_cancel: bool = False,
        adapter_supports_order_amend: bool = False,
        read_only_mode: bool = False,
        dry_run_mode: bool = False,
        submission_authorized: bool = True,
        private_state_available: bool = True,
        private_account_sync_enabled: bool = True,
        preview_status: VenueOrderPreviewStatus = VenueOrderPreviewStatus.PREPARABLE,
        preview_reason_codes: list[str] | None = None,
    ) -> None:
        self.venue = venue
        self.support_level = support_level
        self.venue_supports_submission = venue_supports_submission
        self.adapter_supports_submission = adapter_supports_submission
        self.adapter_supports_order_cancel = adapter_supports_order_cancel
        self.adapter_supports_order_amend = adapter_supports_order_amend
        self.read_only_mode = read_only_mode
        self.dry_run_mode = dry_run_mode
        self.submission_authorized = submission_authorized
        self.private_state_available = private_state_available
        self.private_account_sync_enabled = private_account_sync_enabled
        self.preview_status = preview_status
        self.preview_reason_codes = list(preview_reason_codes or [])

    async def prepare_order_preview(self, intent: OrderIntent) -> PreparedVenueOrder:
        capabilities = VenueCapabilities(
            venue=Venue(self.venue),
            support_level=self.support_level,
            supports_spot=False,
            supports_perpetuals=True,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=False,
            supports_account_sync=self.private_account_sync_enabled,
            supports_top_of_book=True,
            supports_depth_summary=False,
            supports_order_submission=self.venue_supports_submission,
            supports_order_cancel=True,
            supports_order_amend=self.adapter_supports_order_amend,
            supports_recent_fills_query=False,
            adapter_supports_order_submission=self.adapter_supports_submission,
            adapter_supports_order_cancel=self.adapter_supports_order_cancel,
            adapter_supports_order_amend=self.adapter_supports_order_amend,
            adapter_supports_user_streams=False,
            supports_order_preview=True,
            supports_account_snapshot=self.private_state_available,
            supports_open_orders_query=True,
            supports_open_positions_query=True,
            supports_reduce_only_orders=True,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=self.venue == Venue.OKX.value,
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
            supported_time_in_force=["gtc", "ioc"],
            account_model="wallet_address",
            notes=None,
            private_lifecycle_update_mode="polling",
        )
        connectivity = VenueAccountConnectivity(
            venue=self.venue,
            environment=Environment.TESTNET,
            support_level=self.support_level,
            account_model="wallet_address",
            account_identifier=f"{self.venue}-acct",
            account_label="primary",
            subaccount_label=None,
            credentials_ref="secret://acct",
            account_identifier_configured=True,
            credentials_configured=True,
            read_only_mode=self.read_only_mode,
            dry_run_mode=self.dry_run_mode,
            submission_authorized=self.submission_authorized,
            private_account_sync_enabled=self.private_account_sync_enabled,
            account_snapshot_available=self.private_state_available,
            open_orders_query_available=True,
            open_positions_query_available=True,
            last_success_at=datetime.now(UTC),
            last_error=None,
        )
        constraints = VenueOrderConstraints(
            venue=self.venue,
            support_level=self.support_level,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            exchange_symbol=intent.symbol if self.venue == Venue.HYPERLIQUID.value else f"{intent.symbol}-USDT",
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
        )
        payload = None
        if self.preview_status == VenueOrderPreviewStatus.PREPARABLE:
            payload = {"symbol": constraints.exchange_symbol, "type": intent.order_type.value}
        return PreparedVenueOrder(
            intent_id=intent.intent_id,
            desired_trade_key=intent.desired_trade_key,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=self.venue,
            support_level=self.support_level,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            exchange_symbol=constraints.exchange_symbol,
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            reduce_only=intent.reduce_only,
            time_in_force="ioc",
            client_order_id="mf-preview",
            preview_status=self.preview_status,
            reason_codes=list(self.preview_reason_codes),
            payload=payload,
            constraints=constraints,
            venue_capabilities=capabilities,
            account_connectivity=connectivity,
            prepared_at=datetime.now(UTC),
        )


class _StubVenueRegistry:
    def __init__(self, adapters: dict[str, _StubVenueAdapter]) -> None:
        self.adapters = adapters

    async def get_adapter(self, venue: str):
        return self.adapters[venue]

    async def list_supported_venues(self):
        raise NotImplementedError


def test_current_integrated_venues_are_assessed_in_execution_preparable_branch() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        ASTER_SUBMISSION_AUTHORIZED=True,
        OKX_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
    )
    intents = {}
    adapters = {}
    for venue in (
        Venue.HYPERLIQUID.value,
        Venue.ASTER.value,
        Venue.OKX.value,
        Venue.COINBASE_ADVANCED_TRADE.value,
    ):
        intents[venue] = _seed_intent(session_factory, venue=venue)
        adapters[venue] = _StubVenueAdapter(
            venue=venue,
            adapter_supports_submission=False,
            submission_authorized=True,
            read_only_mode=False,
            dry_run_mode=False,
        )
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(adapters),
    )

    for venue, intent_id in intents.items():
        assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))
        assert assessment.support_level == VenueSupportLevel.EXECUTION_PREPARABLE
        assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ADAPTER
        assert "adapter_submission_unimplemented" in assessment.reason_codes
        assert assessment.eligible_for_submission_in_principle is False
        assert assessment.venue == venue


def test_phase_blocked_when_submission_is_eligible_in_principle() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
    )
    intent_id = _seed_intent(session_factory, venue=Venue.HYPERLIQUID.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.HYPERLIQUID.value: _StubVenueAdapter(
                    venue=Venue.HYPERLIQUID.value,
                    adapter_supports_submission=True,
                    adapter_supports_order_cancel=True,
                    adapter_supports_order_amend=True,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert assessment.eligible_for_submission_in_principle is True
    assert "phase_live_submit_deferred" in assessment.reason_codes


def test_live_enabled_support_level_can_reach_eligible_for_submission() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
    )
    intent_id = _seed_intent(session_factory, venue=Venue.HYPERLIQUID.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.HYPERLIQUID.value: _StubVenueAdapter(
                    venue=Venue.HYPERLIQUID.value,
                    support_level=VenueSupportLevel.LIVE_ENABLED,
                    adapter_supports_submission=True,
                    adapter_supports_order_cancel=True,
                    adapter_supports_order_amend=True,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.support_level == VenueSupportLevel.LIVE_ENABLED
    assert assessment.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    assert assessment.eligible_for_submission_in_principle is True
    assert assessment.reason_codes == []


def test_submission_semantic_support_without_adapter_support_blocks_by_adapter() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        OKX_SUBMISSION_AUTHORIZED=True,
        OKX_READ_ONLY_MODE=False,
        OKX_DRY_RUN_MODE=False,
    )
    intent_id = _seed_intent(session_factory, venue=Venue.OKX.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.OKX.value: _StubVenueAdapter(
                    venue=Venue.OKX.value,
                    support_level=VenueSupportLevel.LIVE_ENABLED,
                    venue_supports_submission=True,
                    adapter_supports_submission=False,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ADAPTER
    assert assessment.reason_codes == ["adapter_submission_unimplemented"]


def test_preview_rejected_intent_is_ineligible() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXECUTION_DRY_RUN=False)
    intent_id = _seed_intent(session_factory, venue=Venue.OKX.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.OKX.value: _StubVenueAdapter(
                    venue=Venue.OKX.value,
                    preview_status=VenueOrderPreviewStatus.REJECTED,
                    preview_reason_codes=["unsupported_order_type"],
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.INELIGIBLE
    assert assessment.reason_codes[0] == "preview_rejected"
    assert "unsupported_order_type" in assessment.reason_codes


def test_environment_and_private_state_blocking_are_explicit() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        EXECUTION_REQUIRE_PRIVATE_STATE_FOR_SUBMISSION_READINESS=True,
        ASTER_SUBMISSION_AUTHORIZED=True,
    )
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.ASTER.value: _StubVenueAdapter(
                    venue=Venue.ASTER.value,
                    adapter_supports_submission=True,
                    read_only_mode=True,
                    dry_run_mode=False,
                    submission_authorized=True,
                    private_state_available=False,
                    private_account_sync_enabled=False,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
    assert assessment.reason_codes == ["read_only_mode_enabled"]

    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.ASTER.value: _StubVenueAdapter(
                    venue=Venue.ASTER.value,
                    adapter_supports_submission=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    submission_authorized=True,
                    private_state_available=False,
                    private_account_sync_enabled=False,
                )
            }
        ),
    )
    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))
    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
    assert "private_state_unavailable" in assessment.reason_codes


def test_binding_disabled_blocks_readiness_by_policy() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXECUTION_DRY_RUN=False)
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    _set_binding_account_state(session_factory, intent_id, binding_enabled=False)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.ASTER.value: _StubVenueAdapter(
                    venue=Venue.ASTER.value,
                    support_level=VenueSupportLevel.LIVE_ENABLED,
                    adapter_supports_submission=True,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert assessment.reason_codes == ["binding_disabled"]
    assert assessment.eligible_for_submission_in_principle is False


def test_non_routing_eligible_binding_blocks_readiness_by_policy() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXECUTION_DRY_RUN=False)
    intent_id = _seed_intent(session_factory, venue=Venue.OKX.value)
    _set_binding_account_state(session_factory, intent_id, binding_routing_eligible=False)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.OKX.value: _StubVenueAdapter(
                    venue=Venue.OKX.value,
                    support_level=VenueSupportLevel.LIVE_ENABLED,
                    adapter_supports_submission=True,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert assessment.reason_codes == ["binding_not_routing_eligible"]
    assert assessment.eligible_for_submission_in_principle is False


def test_inactive_venue_account_blocks_readiness_by_policy() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXECUTION_DRY_RUN=False)
    intent_id = _seed_intent(session_factory, venue=Venue.COINBASE_ADVANCED_TRADE.value)
    _set_binding_account_state(session_factory, intent_id, venue_account_active=False)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.COINBASE_ADVANCED_TRADE.value: _StubVenueAdapter(
                    venue=Venue.COINBASE_ADVANCED_TRADE.value,
                    support_level=VenueSupportLevel.LIVE_ENABLED,
                    adapter_supports_submission=True,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                    private_state_available=True,
                    private_account_sync_enabled=True,
                )
            }
        ),
    )

    assessment = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert assessment.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert assessment.reason_codes == ["venue_account_inactive"]
    assert assessment.eligible_for_submission_in_principle is False


def test_readiness_assessment_is_idempotent_for_unchanged_state() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXECUTION_DRY_RUN=False)
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=_StubVenueRegistry(
            {
                Venue.ASTER.value: _StubVenueAdapter(
                    venue=Venue.ASTER.value,
                    adapter_supports_submission=False,
                    submission_authorized=True,
                    read_only_mode=False,
                    dry_run_mode=False,
                )
            }
        ),
    )

    first = asyncio.run(execution.assess_child_intent_readiness(intent_id))
    second = asyncio.run(execution.assess_child_intent_readiness(intent_id))

    assert first.readiness_evaluation_id == second.readiness_evaluation_id
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 1


def test_execution_readiness_api_endpoints() -> None:
    class _StubExecutionService:
        async def assess_child_intent_readiness(self, intent_id: str):
            return ExecutionReadinessAssessment(
                readiness_evaluation_id="ready-1",
                readiness_evaluation_key="ready-key-1",
                environment=Environment.TESTNET,
                intent_ref_id="intent-ref-1",
                intent_id=intent_id,
                mandate_desired_trade_ref_id="trade-ref-1",
                desired_trade_key="trade-1",
                client_ref_id="client-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_account_binding_ref_id="binding-1",
                binding_key="binding-1",
                venue_account_ref_id="acct-1",
                instrument_key="perpetual:linear:BTC:USDT:USDT",
                instrument_ref_id="inst-1",
                symbol="BTC",
                venue="hyperliquid",
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                preview_status=VenueOrderPreviewStatus.PREPARABLE,
                outcome=ExecutionReadinessOutcome.PHASE_BLOCKED,
                eligible_for_submission_in_principle=True,
                live_submission_phase_enabled=False,
                venue_supports_order_submission=True,
                adapter_supports_order_submission=True,
                adapter_supports_order_cancel=True,
                adapter_supports_order_amend=True,
                submission_authorized=True,
                account_connected=True,
                private_state_required=True,
                private_state_ready=True,
                reason_codes=["phase_live_submit_deferred"],
                message="Prepared child intent is eligible in principle, but live submission remains intentionally deferred in the current phase.",
                prepared_order=None,
                evaluated_at=datetime.now(UTC),
                provenance={"phase_boundary": "phase_4_2"},
            )

        async def list_readiness_assessments(self, *, intent_id=None, outcome=None, limit: int = 100):
            return [await self.assess_child_intent_readiness(intent_id or "intent-1")]

    test_client = TestClient(app)
    app.dependency_overrides[get_execution_service] = lambda: _StubExecutionService()
    try:
        single = test_client.get("/api/v1/child-intents/intent-1/submission-readiness")
        listing = test_client.get("/api/v1/execution-readiness")
    finally:
        app.dependency_overrides.clear()

    assert single.status_code == 200
    assert single.json()["outcome"] == "phase_blocked"
    assert single.json()["eligible_for_submission_in_principle"] is True
    assert single.json()["adapter_supports_order_cancel"] is True
    assert single.json()["adapter_supports_order_amend"] is True
    assert listing.status_code == 200
    assert listing.json()[0]["reason_codes"] == ["phase_live_submit_deferred"]
