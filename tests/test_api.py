from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.dependencies import (
    get_execution_service,
    get_exchange_adapter,
    get_hyperliquid_adapter,
    get_risk_engine,
    get_routing_assessment_service,
    get_runtime_context_service,
    get_strategy_engine,
    get_trade_planning_service,
    get_venue_registry_service,
)
from apps.api.app.main import app
from core.domain.enums import (
    DecisionAction,
    Environment,
    InstrumentResolutionMode,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    ProductType,
    RiskEvaluationOutcome,
    RoutingAssessmentDecisionStatus,
    RoutingCandidateEligibilityStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    StrategyDecisionStatus,
    StrategyFamily,
    SubmittedOrderStatus,
    Timeframe,
    TradeTargetScope,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.models import (
    ActiveMandateBindingContext,
    ActiveMandateContext,
    BindingQuoteSnapshot,
    BindingRoutingCandidate,
    Client,
    DesiredTradeConvertibilityAssessment,
    ExchangeSessionState,
    ExchangeStatus,
    Fill,
    Instrument,
    MandateMarketDataSourcePolicy,
    MandateDesiredTrade,
    MandateAccountBinding,
    OrderIntent,
    PreparedVenueOrder,
    RiskEvaluation,
    RoutingAssessment,
    RoutingCandidateAssessment,
    RoutingRequest,
    RoutingTargetChoice,
    RoutingTargetChoiceConversionResult,
    StrategyComponentConfig,
    StrategyFamilyStatus,
    StrategyMandate,
    TopOfBookSnapshot,
    VenueQuoteSnapshot,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueIntegrationSummary,
    VenueOrderConstraints,
    VenuePrivateOpenOrder,
    VenuePrivateStateSummary,
    VenueAccount,
)
from db.models import OrderIntentModel
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase52_target_choice_conversion import (
    _desired_trade_status,
    _execution_counts,
    _recorded_choice,
)


client = TestClient(app)


def _runtime_context() -> ActiveMandateContext:
    client_model = Client(
        client_key="default_client",
        client_ref_id="client-1",
        display_name="Default Client",
        is_active=True,
    )
    mandate = StrategyMandate(
        mandate_key="money_flow::hyperliquid_group",
        mandate_ref_id="mandate-1",
        client_key="default_client",
        client_ref_id="client-1",
        family=StrategyFamily.MONEY_FLOW,
        enabled=True,
        allow_builder_deployed_for_strategy=False,
        allow_builder_deployed_for_trading=False,
        notes=None,
        metadata={},
    )
    source_policy = MandateMarketDataSourcePolicy(
        policy_ref_id="policy-1",
        strategy_mandate_ref_id="mandate-1",
        mandate_key=mandate.mandate_key,
        source_mode=MarketDataSourceMode.SINGLE_VENUE,
        source_venue="hyperliquid",
        market_type=MarketType.PERPETUAL,
        product_type=ProductType.LINEAR,
        instrument_resolution_mode=InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS,
        runtime_exchange_venue="hyperliquid",
        runtime_exchange_matches_source=True,
        notes=None,
        metadata={},
    )
    account = VenueAccount(
        venue_account_key="hyperliquid_testnet_primary",
        venue_account_ref_id="acct-1",
        client_key="default_client",
        client_ref_id="client-1",
        venue="hyperliquid",
        environment=Environment.TESTNET,
        venue_native_account_id="acct",
        account_address="acct",
        account_label="primary",
        subaccount_label=None,
        credentials_ref=None,
        wallet_ref=None,
        is_active=True,
        trading_enabled=True,
    )
    binding = MandateAccountBinding(
        binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
        binding_ref_id="binding-1",
        strategy_mandate_ref_id="mandate-1",
        mandate_key=mandate.mandate_key,
        venue_account_key=account.venue_account_key,
        venue_account_ref_id=account.venue_account_ref_id,
        enabled=True,
        strategy_eligible=True,
        routing_eligible=True,
        trading_enabled=True,
        allow_builder_deployed_for_strategy=False,
        allow_builder_deployed_for_trading=False,
        notes=None,
        metadata={},
    )
    return ActiveMandateContext(
        client=client_model,
        mandate=mandate,
        market_data_source_policy=source_policy,
        bindings=[
            ActiveMandateBindingContext(
                binding=binding,
                venue_account=account,
                component_configs=[
                    StrategyComponentConfig(
                        component_config_ref_id="component-15m",
                        strategy_mandate_ref_id="mandate-1",
                        mandate_account_binding_ref_id="binding-1",
                        component_key="sleeve_15m",
                        component_type="money_flow_sleeve",
                        timeframe=Timeframe.M15,
                        enabled=True,
                        capital_allocation_pct=Decimal("0.34"),
                        max_open_risk_pct=Decimal("0.02"),
                        parameters={},
                        metadata={},
                        is_override=False,
                    ),
                    StrategyComponentConfig(
                        component_config_ref_id="component-1h",
                        strategy_mandate_ref_id="mandate-1",
                        mandate_account_binding_ref_id="binding-1",
                        component_key="sleeve_1h",
                        component_type="money_flow_sleeve",
                        timeframe=Timeframe.H1,
                        enabled=True,
                        capital_allocation_pct=Decimal("0.33"),
                        max_open_risk_pct=Decimal("0.02"),
                        parameters={},
                        metadata={},
                        is_override=False,
                    ),
                    StrategyComponentConfig(
                        component_config_ref_id="component-4h",
                        strategy_mandate_ref_id="mandate-1",
                        mandate_account_binding_ref_id="binding-1",
                        component_key="sleeve_4h",
                        component_type="money_flow_sleeve",
                        timeframe=Timeframe.H4,
                        enabled=True,
                        capital_allocation_pct=Decimal("0.33"),
                        max_open_risk_pct=Decimal("0.02"),
                        parameters={},
                        metadata={},
                        is_override=False,
                    ),
                ],
            )
        ],
    )


class _StubRuntimeContextService:
    async def ensure_active_context(self) -> ActiveMandateContext:
        return _runtime_context()

    async def get_active_context(self) -> ActiveMandateContext:
        return _runtime_context()

    async def list_clients(self) -> list[Client]:
        return [_runtime_context().client]

    async def list_venue_accounts(self, client_key: str | None = None) -> list[VenueAccount]:
        return [_runtime_context().bindings[0].venue_account]

    async def list_mandates(self, client_key: str | None = None) -> list[StrategyMandate]:
        return [_runtime_context().mandate]

    async def list_bindings(self, mandate_key: str | None = None) -> list[MandateAccountBinding]:
        return [_runtime_context().bindings[0].binding]

    async def list_effective_component_configs(
        self,
        binding_key: str | None = None,
    ) -> list[StrategyComponentConfig]:
        return list(_runtime_context().bindings[0].component_configs)

    async def create_mandate(
        self,
        *,
        mandate_key: str,
        family: StrategyFamily,
        enabled: bool = True,
        notes: str | None = None,
    ) -> StrategyMandate:
        mandate = _runtime_context().mandate
        mandate.mandate_key = mandate_key
        mandate.family = family
        mandate.enabled = enabled
        mandate.notes = notes
        return mandate

    async def bind_account(
        self,
        *,
        mandate_key: str,
        venue_account_key: str,
        binding_key: str | None = None,
        enabled: bool = True,
        strategy_eligible: bool = True,
        routing_eligible: bool = True,
        trading_enabled: bool = True,
        target_recommendation_priority: int | None = None,
        clear_target_recommendation_priority: bool = False,
    ) -> MandateAccountBinding:
        binding = _runtime_context().bindings[0].binding
        binding.mandate_key = mandate_key
        binding.venue_account_key = venue_account_key
        binding.binding_key = binding_key or binding.binding_key
        binding.enabled = enabled
        binding.strategy_eligible = strategy_eligible
        binding.routing_eligible = routing_eligible
        binding.trading_enabled = trading_enabled
        if clear_target_recommendation_priority:
            binding.target_recommendation_priority = None
        elif target_recommendation_priority is not None:
            binding.target_recommendation_priority = target_recommendation_priority
        return binding


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_components_backed_sleeves_endpoint() -> None:
    app.dependency_overrides[get_runtime_context_service] = lambda: _StubRuntimeContextService()
    try:
        response = client.get("/api/v1/sleeves")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_component_status_endpoint() -> None:
    app.dependency_overrides[get_runtime_context_service] = lambda: _StubRuntimeContextService()
    try:
        response = client.get("/api/v1/components")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["component_key"] == "sleeve_15m"


def test_exchange_status_endpoint() -> None:
    class _StubExchangeAdapter:
        async def get_exchange_status(self):
            return ExchangeStatus(
                venue="hyperliquid",
                environment=Environment.TESTNET,
                connected=True,
                api_base_url="https://api.hyperliquid-testnet.xyz",
                websocket_base_url="wss://api.hyperliquid-testnet.xyz/ws",
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
                last_success_at=None,
                last_error=None,
                private_lifecycle_update_mode="polling",
            )

    app.dependency_overrides[get_exchange_adapter] = lambda: _StubExchangeAdapter()
    try:
        response = client.get("/api/v1/exchange/status")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["venue"] == "hyperliquid"
    assert response.json()["adapter_supports_order_cancel"] is False
    assert response.json()["adapter_supports_order_amend"] is False


def test_exchange_capabilities_endpoint() -> None:
    class _StubExchangeAdapter:
        async def get_venue_capabilities(self):
            return VenueCapabilities(
                venue=Venue.HYPERLIQUID,
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                supports_spot=False,
                supports_perpetuals=True,
                supports_futures=False,
                supports_options=False,
                supports_hedge_mode=False,
                supports_websocket_market_data=True,
                supports_user_streams=False,
                supports_account_sync=True,
                supports_top_of_book=False,
                supports_depth_summary=False,
                supports_order_submission=True,
                supports_order_cancel=True,
                supports_order_amend=True,
                supports_recent_fills_query=True,
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
                supported_time_in_force=["gtc", "ioc", "alo"],
                account_model="wallet_address",
                private_lifecycle_update_mode="polling",
            )

    app.dependency_overrides[get_exchange_adapter] = lambda: _StubExchangeAdapter()
    try:
        response = client.get("/api/v1/exchange/capabilities")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["supports_perpetuals"] is True
    assert response.json()["supports_websocket_market_data"] is True
    assert response.json()["supports_order_cancel"] is True
    assert response.json()["supports_order_amend"] is True


def test_strategy_status_endpoint() -> None:
    class _StubStrategyEngine:
        async def get_family_status(self) -> StrategyFamilyStatus:
            return StrategyFamilyStatus(
                family=StrategyFamily.MONEY_FLOW,
                components=["sleeve_15m", "sleeve_1h", "sleeve_4h"],
                enabled_components=3,
                latest_decision_at=None,
                mandate_key="money_flow::hyperliquid_group",
            )

    app.dependency_overrides[get_strategy_engine] = lambda: _StubStrategyEngine()
    try:
        response = client.get("/api/v1/strategy/status")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["family"] == "money_flow"


def test_runtime_inspection_endpoints() -> None:
    app.dependency_overrides[get_runtime_context_service] = lambda: _StubRuntimeContextService()
    try:
        clients_response = client.get("/api/v1/clients")
        accounts_response = client.get("/api/v1/accounts")
        mandates_response = client.get("/api/v1/mandates")
        bindings_response = client.get("/api/v1/mandates/money_flow::hyperliquid_group/bindings")
        components_response = client.get(
            "/api/v1/bindings/money_flow::hyperliquid_group::hyperliquid_testnet_primary/components"
        )
        context_response = client.get("/api/v1/runtime/context")
    finally:
        app.dependency_overrides.clear()

    assert clients_response.status_code == 200
    assert clients_response.json()[0]["client_key"] == "default_client"
    assert accounts_response.status_code == 200
    assert accounts_response.json()[0]["venue_account_key"] == "hyperliquid_testnet_primary"
    assert mandates_response.status_code == 200
    assert mandates_response.json()[0]["mandate_key"] == "money_flow::hyperliquid_group"
    assert bindings_response.status_code == 200
    assert bindings_response.json()[0]["binding_key"].endswith("hyperliquid_testnet_primary")
    assert components_response.status_code == 200
    assert len(components_response.json()) == 3
    assert context_response.status_code == 200
    assert context_response.json()["active_mandate_key"] == "money_flow::hyperliquid_group"
    assert context_response.json()["market_data_source_venue"] == "hyperliquid"


def test_multi_venue_qa_endpoints() -> None:
    class _StubVenueAdapter:
        async def get_session_state(self):
            return ExchangeSessionState(
                venue="okx",
                environment=Environment.TESTNET,
                connected=True,
                last_heartbeat_at=datetime.now(UTC),
                session_sequence=7,
            )

        async def get_exchange_status(self) -> ExchangeStatus:
            return ExchangeStatus(
                venue="okx",
                environment=Environment.TESTNET,
                connected=True,
                api_base_url="https://www.okx.com",
                websocket_base_url="wss://ws.okx.com:8443/ws/v5/public",
                can_sign_orders=False,
                wallet_address_configured=False,
                account_identifier_configured=True,
                credentials_configured=True,
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

        async def get_venue_capabilities(self) -> VenueCapabilities:
            return VenueCapabilities(
                venue=Venue.OKX,
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                supports_spot=True,
                supports_perpetuals=True,
                supports_futures=True,
                supports_options=True,
                supports_hedge_mode=True,
                supports_websocket_market_data=True,
                supports_user_streams=True,
                supports_account_sync=True,
                supports_top_of_book=True,
                supports_depth_summary=True,
                supports_order_submission=True,
                supports_order_cancel=True,
                supports_order_amend=True,
                supports_recent_fills_query=True,
                adapter_supports_order_submission=False,
                adapter_supports_order_cancel=False,
                adapter_supports_order_amend=False,
                adapter_supports_user_streams=False,
                supports_order_preview=True,
                supports_account_snapshot=True,
                supports_open_orders_query=False,
                supports_open_positions_query=False,
                supports_reduce_only_orders=True,
                supports_client_order_ids=True,
                supports_demo_mode=True,
                supports_subaccounts=True,
                supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP],
                supported_time_in_force=["gtc", "ioc", "fok", "post_only"],
                account_model="account_with_subaccounts",
                notes="qa",
                private_lifecycle_update_mode="polling",
            )

        async def list_instruments(self):
            return [
                Instrument(
                    instrument_key="spot:spot:BTC:USD:",
                    instrument_ref_id="inst-1",
                    canonical_symbol="BTC",
                    market_type=MarketType.SPOT,
                    product_type=ProductType.SPOT,
                    base_asset="BTC",
                    quote_asset="USD",
                    settlement_asset=None,
                    is_active=True,
                )
            ]

        async def sync_symbols(self):
            return []

        async def get_account_connectivity(self) -> VenueAccountConnectivity:
            return VenueAccountConnectivity(
                venue="okx",
                environment=Environment.TESTNET,
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                account_model="account_with_subaccounts",
                account_identifier="acct-1",
                account_label="primary",
                subaccount_label="desk-a",
                credentials_ref="secret://okx",
                account_identifier_configured=True,
                credentials_configured=True,
                read_only_mode=True,
                dry_run_mode=True,
                submission_authorized=False,
                private_account_sync_enabled=True,
                account_snapshot_available=True,
                open_orders_query_available=False,
                open_positions_query_available=False,
                last_success_at=None,
                last_error=None,
            )

        async def read_account_snapshot(self):
            return None

        async def get_private_state_summary(self) -> VenuePrivateStateSummary:
            return VenuePrivateStateSummary(
                venue="okx",
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                account_model="account_with_subaccounts",
                account_identifier="acct-1",
                read_only_mode=True,
                dry_run_mode=True,
                private_account_sync_enabled=True,
                account_snapshot_available=True,
                balances_visible=True,
                open_orders_query_available=False,
                open_orders_count=0,
                open_orders_source="persistence",
                open_positions_query_available=False,
                open_positions_count=0,
                open_positions_source="persistence",
                recent_fills_query_available=False,
                recent_fills_count=0,
                recent_fills_source="persistence",
                equity=Decimal("1000"),
                available_balance=Decimal("650"),
                last_success_at=None,
                last_error=None,
                adapter_supports_user_streams=False,
                private_lifecycle_update_mode="polling",
            )

        async def fetch_open_orders(self, venue_account_ref_id: str | None = None):
            return [
                VenuePrivateOpenOrder(
                    venue="okx",
                    venue_account_ref_id=venue_account_ref_id,
                    account_address="acct-1",
                    exchange_order_id="ord-1",
                    client_order_id="cl-1",
                    instrument_key="perpetual:linear:BTC:USDT:USDT",
                    instrument_ref_id="inst-1",
                    symbol="BTC",
                    exchange_symbol="BTC-USDT-SWAP",
                    status=SubmittedOrderStatus.ACKNOWLEDGED,
                    observed_at=datetime.now(UTC),
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    limit_price=Decimal("100"),
                    original_quantity=Decimal("1"),
                    remaining_quantity=Decimal("1"),
                    filled_quantity=Decimal("0"),
                    average_fill_price=None,
                    last_fill_at=None,
                    status_reason_code="reconciliation_open_order",
                    status_message="ok",
                    reason_codes=["reconciliation_open_order"],
                    cancelable_in_principle=True,
                    amendable_in_principle=True,
                    reduce_only=False,
                    linked_submitted_order_id="subm-okx-1",
                    linked_order_intent_id="intent-okx-1",
                    raw_payload={},
                )
            ]

        async def fetch_open_orders_with_source(self, venue_account_ref_id: str | None = None):
            return ("persistence", await self.fetch_open_orders(venue_account_ref_id=venue_account_ref_id))

        async def fetch_recent_fills(self, limit: int = 100, venue_account_ref_id: str | None = None):
            return [
                Fill(
                    fill_id="fill-1",
                    instrument_key="perpetual:linear:BTC:USDT:USDT",
                    instrument_ref_id="inst-1",
                    venue_account_ref_id=venue_account_ref_id,
                    venue="okx",
                    account_address="acct-1",
                    submitted_order_id="ord-1",
                    exchange_order_id="ord-1",
                    symbol="BTC",
                    price=Decimal("100"),
                    quantity=Decimal("0.1"),
                    fee=Decimal("0.01"),
                    filled_at=datetime.now(UTC),
                )
            ]

        async def fetch_recent_fills_with_source(self, limit: int = 100, venue_account_ref_id: str | None = None):
            return (
                "persistence",
                await self.fetch_recent_fills(limit=limit, venue_account_ref_id=venue_account_ref_id),
            )

        async def fetch_open_positions(self, venue_account_ref_id: str | None = None):
            return []

        async def fetch_open_positions_with_source(self, venue_account_ref_id: str | None = None):
            return ("persistence", await self.fetch_open_positions(venue_account_ref_id=venue_account_ref_id))

        async def get_order_constraints(self, *, instrument_key=None, instrument_ref_id=None, symbol=None):
            return VenueOrderConstraints(
                venue="okx",
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                instrument_key="perpetual:linear:BTC:USDT:USDT",
                instrument_ref_id="inst-1",
                symbol="BTC",
                exchange_symbol="BTC-USDT-SWAP",
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                price_tick_size=Decimal("0.1"),
                quantity_step_size=Decimal("0.001"),
                min_order_size=Decimal("0.001"),
                supports_order_preview=True,
                supports_reduce_only_orders=True,
                supports_client_order_ids=True,
                supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP],
                supported_time_in_force=["gtc", "ioc", "fok", "post_only"],
                constraint_metadata_complete=True,
                notes=None,
            )

        async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
            return TopOfBookSnapshot(
                instrument_key="perpetual:linear:BTC:USDT:USDT",
                instrument_ref_id=None,
                venue="okx",
                symbol=symbol,
                bid_price=Decimal("100"),
                bid_size=Decimal("2"),
                ask_price=Decimal("101"),
                ask_size=Decimal("3"),
                observed_at=datetime.now(UTC),
            )

    @dataclass
    class _StubRegistry:
        async def list_supported_venues(self):
            return [
                VenueIntegrationSummary(
                    venue="hyperliquid",
                    display_name="Hyperliquid",
                    enabled=True,
                    read_only_mode=True,
                    dry_run_mode=True,
                    execution_authorized=True,
                    adapter_submission_implemented=False,
                    live_submission_phase_enabled=False,
                    support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                ),
                VenueIntegrationSummary(
                    venue="okx",
                    display_name="OKX",
                    enabled=True,
                    read_only_mode=True,
                    dry_run_mode=True,
                    execution_authorized=False,
                    adapter_submission_implemented=False,
                    live_submission_phase_enabled=False,
                    support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                ),
            ]

        async def get_adapter(self, venue: str):
            assert venue == "okx"
            return _StubVenueAdapter()

    app.dependency_overrides[get_venue_registry_service] = lambda: _StubRegistry()
    try:
        venues_response = client.get("/api/v1/venues")
        status_response = client.get("/api/v1/venues/okx/status")
        capabilities_response = client.get("/api/v1/venues/okx/capabilities")
        instruments_response = client.get("/api/v1/venues/okx/instruments")
        connectivity_response = client.get("/api/v1/venues/okx/account-connectivity")
        private_state_response = client.get("/api/v1/venues/okx/private-state-summary")
        session_state_response = client.get("/api/v1/venues/okx/session-state")
        open_orders_response = client.get("/api/v1/venues/okx/private-state/open-orders")
        recent_fills_response = client.get("/api/v1/venues/okx/private-state/recent-fills")
        constraints_response = client.get("/api/v1/venues/okx/order-constraints", params={"symbol": "BTC"})
        top_of_book_response = client.get("/api/v1/venues/okx/market-data/top-of-book", params={"symbol": "BTC"})
    finally:
        app.dependency_overrides.clear()

    assert venues_response.status_code == 200
    assert len(venues_response.json()) == 2
    assert status_response.status_code == 200
    assert status_response.json()["support_level"] == "execution_preparable"
    assert capabilities_response.status_code == 200
    assert capabilities_response.json()["supports_subaccounts"] is True
    assert capabilities_response.json()["supports_order_preview"] is True
    assert instruments_response.status_code == 200
    assert instruments_response.json()[0]["canonical_symbol"] == "BTC"
    assert connectivity_response.status_code == 200
    assert connectivity_response.json()["account_model"] == "account_with_subaccounts"
    assert private_state_response.status_code == 200
    assert private_state_response.json()["support_level"] == "execution_preparable"
    assert private_state_response.json()["private_lifecycle_update_mode"] == "polling"
    assert private_state_response.json()["open_positions_source"] == "persistence"
    assert session_state_response.status_code == 200
    assert session_state_response.json()["session_sequence"] == 7
    assert session_state_response.json()["state_scope"] == "adapter_runtime"
    assert open_orders_response.status_code == 200
    assert open_orders_response.json()["source"] == "persistence"
    assert open_orders_response.json()["items"][0]["exchange_order_id"] == "ord-1"
    assert "submitted_order_id" not in open_orders_response.json()["items"][0]
    assert open_orders_response.json()["items"][0]["linked_submitted_order_id"] == "subm-okx-1"
    assert recent_fills_response.status_code == 200
    assert recent_fills_response.json()["source"] == "persistence"
    assert recent_fills_response.json()["items"][0]["fill_id"] == "fill-1"
    assert constraints_response.status_code == 200
    assert constraints_response.json()["supports_client_order_ids"] is True
    assert top_of_book_response.status_code == 200
    assert top_of_book_response.json()["bid_price"] == 100.0

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    session_schema = openapi_response.json()["components"]["schemas"]["ExchangeSessionStateResponse"]
    assert "adapter/runtime connection bookkeeping" in session_schema["properties"]["state_scope"]["description"]


def test_trade_planning_endpoints() -> None:
    class _StubPlanningService:
        async def get_market_data_source_policy(
            self,
            *,
            mandate_key: str | None = None,
        ):
            return MandateMarketDataSourcePolicy(
                policy_ref_id="policy-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_key=mandate_key or "money_flow::hyperliquid_group",
                source_mode=MarketDataSourceMode.SINGLE_VENUE,
                source_venue="hyperliquid",
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                instrument_resolution_mode=InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS,
                runtime_exchange_venue="hyperliquid",
                runtime_exchange_matches_source=True,
                notes=None,
                metadata={},
            )

        async def inspect_decision_convertibility(
            self,
            decision_id: str,
        ):
            return DesiredTradeConvertibilityAssessment(
                decision_id=decision_id,
                convertible=True,
                decision_status=StrategyDecisionStatus.PROPOSED,
                action=DecisionAction.OPEN,
                target_scope=TradeTargetScope.MANDATE,
                reason_code=None,
                message="Open proposals become mandate-scoped desired trade drafts.",
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                desired_trade_key_preview="trade-1",
            )

        async def list_desired_trades(
            self,
            *,
            mandate_key: str | None = None,
            component_key: str | None = None,
            status: MandateDesiredTradeStatus | None = None,
            limit: int = 100,
        ):
            return [
                MandateDesiredTrade(
                    desired_trade_key="trade-1",
                    desired_trade_ref_id="trade-ref-1",
                    evaluated_state_fingerprint="eval-1",
                    environment=Environment.TESTNET,
                    client_ref_id="client-1",
                    strategy_mandate_ref_id="mandate-1",
                    mandate_key="money_flow::hyperliquid_group",
                    family=StrategyFamily.MONEY_FLOW,
                    component_key="sleeve_1h",
                    market_data_source_policy_ref_id="policy-1",
                    planning_source_venue="hyperliquid",
                    planning_source_mode=MarketDataSourceMode.SINGLE_VENUE,
                    planning_as_of=datetime.now(UTC),
                    target_scope=TradeTargetScope.MANDATE,
                    mandate_account_binding_ref_id=None,
                    binding_key=None,
                    venue_account_ref_id=None,
                    instrument_key="perpetual:linear:BTC:USDC:USDC",
                    instrument_ref_id="inst-1",
                    symbol="BTC",
                    action=DecisionAction.OPEN,
                    side=OrderSide.BUY,
                    desired_quantity=None,
                    desired_notional=None,
                    source_decision_ids=["decision-1"],
                    source_evaluation_keys=["eval-1"],
                    source_binding_keys=["binding-1"],
                    status=MandateDesiredTradeStatus.DRAFT,
                    status_reason_code=None,
                    status_message=None,
                    provenance={"source_decision_id": "decision-1"},
                    created_at=datetime.now(UTC),
                    approved_at=None,
                    rejected_at=None,
                )
            ]

        async def preview_desired_trade_from_decision(
            self,
            decision_id: str,
            *,
            persist: bool = False,
        ):
            return (
                await self.list_desired_trades()
            )[0]

        async def list_routing_candidates(
            self,
            *,
            symbol: str | None = None,
            instrument_key: str | None = None,
            component_key: str | None = None,
            mandate_key: str | None = None,
        ):
            capabilities = VenueCapabilities(
                venue=Venue.HYPERLIQUID,
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
                supported_time_in_force=["gtc", "ioc", "alo"],
                account_model="wallet_address",
                private_lifecycle_update_mode="polling",
            )
            connectivity = VenueAccountConnectivity(
                venue="hyperliquid",
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
                last_success_at=None,
                last_error=None,
            )
            quote = VenueQuoteSnapshot(
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                venue="hyperliquid",
                symbol="BTC",
                exchange_symbol="BTC",
                bid_price=Decimal("100"),
                ask_price=Decimal("101"),
                bid_size=Decimal("2"),
                ask_size=Decimal("3"),
                observed_at=datetime.now(UTC),
                available=True,
                reason_unavailable=None,
            )
            binding_quote = BindingQuoteSnapshot(
                client_ref_id="client-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_key="money_flow::hyperliquid_group",
                binding_ref_id="binding-1",
                binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                venue_account_ref_id="acct-1",
                venue_account_key="hyperliquid_testnet_primary",
                venue="hyperliquid",
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                exchange_symbol="BTC",
                quote_snapshot=quote,
                account_connectivity_status="configured",
                trading_eligible=False,
                routing_eligible=False,
            )
            return [
                BindingRoutingCandidate(
                    client_ref_id="client-1",
                    strategy_mandate_ref_id="mandate-1",
                    mandate_key="money_flow::hyperliquid_group",
                    market_data_source_policy_ref_id="policy-1",
                    planning_source_venue="hyperliquid",
                    binding_ref_id="binding-1",
                    binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                    venue_account_ref_id="acct-1",
                    venue_account_key="hyperliquid_testnet_primary",
                    venue="hyperliquid",
                    instrument_key="perpetual:linear:BTC:USDC:USDC",
                    instrument_ref_id="inst-1",
                    symbol="BTC",
                    exchange_symbol="BTC",
                    strategy_eligible=True,
                    trading_eligible=False,
                    routing_eligible=False,
                    account_connected=True,
                    quote_available=True,
                    available_balance_hint=Decimal("1000"),
                    venue_capabilities=capabilities,
                    account_connectivity=connectivity,
                    quote_snapshot=binding_quote,
                    eligibility_reasons=["venue_read_only_mode"],
                )
            ]

        async def list_binding_quotes(
            self,
            *,
            symbol: str | None = None,
            instrument_key: str | None = None,
            component_key: str | None = None,
            mandate_key: str | None = None,
        ):
            return [(await self.list_routing_candidates())[0].quote_snapshot]

    app.dependency_overrides[get_trade_planning_service] = lambda: _StubPlanningService()
    try:
        policy_response = client.get("/api/v1/planning/source-policy")
        convertibility_response = client.get("/api/v1/planning/decision-convertibility/decision-1")
        trades_response = client.get("/api/v1/planning/desired-trades")
        preview_response = client.post("/api/v1/planning/desired-trades/from-decision/decision-1")
        candidates_response = client.get("/api/v1/planning/routing-candidates", params={"symbol": "BTC"})
        quotes_response = client.get("/api/v1/planning/quotes", params={"symbol": "BTC"})
    finally:
        app.dependency_overrides.clear()

    assert policy_response.status_code == 200
    assert policy_response.json()["source_venue"] == "hyperliquid"
    assert convertibility_response.status_code == 200
    assert convertibility_response.json()["convertible"] is True
    assert trades_response.status_code == 200
    assert trades_response.json()[0]["target_scope"] == "mandate"
    assert preview_response.status_code == 200
    assert preview_response.json()["desired_trade_key"] == "trade-1"
    assert candidates_response.status_code == 200
    assert candidates_response.json()[0]["eligibility_reasons"] == ["venue_read_only_mode"]
    assert quotes_response.status_code == 200
    assert quotes_response.json()[0]["quote_snapshot"]["bid_price"] == 100.0


def test_routing_assessment_endpoints_are_non_executing() -> None:
    conversion_policy_inputs = []

    class _StubRoutingAssessmentService:
        def __init__(self) -> None:
            requested_at = datetime.now(UTC)
            routing_request = RoutingRequest(
                routing_request_id="rtreq-1",
                environment=Environment.TESTNET,
                desired_trade_ref_id="trade-ref-1",
                desired_trade_key="trade-1",
                client_ref_id="client-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_key="money_flow::hyperliquid_group",
                market_data_source_policy_ref_id="policy-1",
                planning_source_venue="hyperliquid",
                planning_source_mode=MarketDataSourceMode.SINGLE_VENUE,
                target_scope=TradeTargetScope.MANDATE,
                action=DecisionAction.OPEN,
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                component_key="sleeve_1h",
                requested_at=requested_at,
            )
            self.assessment = RoutingAssessment(
                assessment_id="rtassess-1",
                environment=Environment.TESTNET,
                desired_trade_ref_id="trade-ref-1",
                desired_trade_key="trade-1",
                client_ref_id="client-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_key="money_flow::hyperliquid_group",
                market_data_source_policy_ref_id="policy-1",
                planning_source_venue="hyperliquid",
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                action=DecisionAction.OPEN,
                target_scope=TradeTargetScope.MANDATE,
                decision_status=RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY,
                eligible_binding_count=1,
                ineligible_binding_count=0,
                request=routing_request,
                candidates=[
                    RoutingCandidateAssessment(
                        assessment_id="rtassess-1",
                        binding_ref_id="binding-1",
                        binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                        venue_account_ref_id="acct-1",
                        venue_account_key="hyperliquid_testnet_primary",
                        venue="hyperliquid",
                        instrument_key="perpetual:linear:BTC:USDC:USDC",
                        instrument_ref_id="inst-1",
                        symbol="BTC",
                        exchange_symbol="BTC",
                        eligibility_status=(
                            RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
                        ),
                        reason_codes=["binding_candidate_assessed_eligible"],
                        missing_data=[],
                        fact_snapshot={"non_executing": True},
                        evaluated_at=requested_at,
                    )
                ],
                reason_codes=["routing_assessment_only"],
                missing_data=[],
                evaluated_at=requested_at,
                provenance={
                    "phase": "phase_5_0",
                    "non_executing": True,
                    "child_intents_created": False,
                },
            )
            self.choice = RoutingTargetChoice(
                target_choice_id="rtchoice-1",
                environment=Environment.TESTNET,
                routing_assessment_ref_id="assessment-ref-1",
                routing_assessment_id="rtassess-1",
                desired_trade_ref_id="trade-ref-1",
                desired_trade_key="trade-1",
                selected_binding_ref_id="binding-1",
                selected_binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                selected_venue_account_ref_id="acct-1",
                selected_venue_account_key="hyperliquid_testnet_primary",
                selected_venue="hyperliquid",
                status=RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED,
                reason_codes=[
                    "target_choice_recorded",
                    "target_choice_non_executing",
                    "child_intent_conversion_deferred",
                ],
                missing_data=[],
                approval_note="operator approval note",
                requested_by="operator@example.test",
                non_executing=True,
                created_at=requested_at,
                selected_at=requested_at,
                provenance={
                    "phase": "phase_5_1",
                    "non_executing": True,
                    "order_intents_created": False,
                    "submitted_orders_created": False,
                },
            )
            self.conversion = RoutingTargetChoiceConversionResult(
                target_choice_id="rtchoice-1",
                environment=Environment.TESTNET,
                status=RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED,
                routing_assessment_id="rtassess-1",
                desired_trade_key="trade-1",
                intent_id="intent-choice-1",
                child_intent=None,
                reason_codes=[
                    "child_intent_created",
                    "conversion_non_submitting",
                    "submission_deferred",
                ],
                missing_data=[],
                non_submitting=True,
                prepared_order_created=False,
                readiness_assessment_created=False,
                submitted_order_created=False,
                converted_at=requested_at,
                provenance={
                    "phase": "phase_5_2",
                    "non_submitting": True,
                    "submitted_order_created": False,
                },
            )

        async def create_assessment_from_desired_trade(self, desired_trade_key: str):
            assert desired_trade_key == "trade-1"
            return self.assessment

        async def get_routing_assessment(self, assessment_id: str):
            assert assessment_id == "rtassess-1"
            return self.assessment

        async def record_target_choice_from_assessment(
            self,
            *,
            routing_assessment_id: str,
            binding_ref_id: str | None = None,
            binding_key: str | None = None,
            approval_note: str | None = None,
            requested_by: str | None = None,
        ):
            assert routing_assessment_id == "rtassess-1"
            assert binding_key == "money_flow::hyperliquid_group::hyperliquid_testnet_primary"
            assert binding_ref_id is None
            assert approval_note == "operator approval note"
            assert requested_by == "operator@example.test"
            return self.choice

        async def get_routing_target_choice(self, target_choice_id: str):
            assert target_choice_id == "rtchoice-1"
            return self.choice

        async def list_routing_target_choices_for_assessment(self, routing_assessment_id: str):
            assert routing_assessment_id == "rtassess-1"
            return [self.choice]

        async def convert_target_choice_to_child_intent(
            self,
            target_choice_id: str,
            order_shape_policy=None,
        ):
            assert target_choice_id == "rtchoice-1"
            conversion_policy_inputs.append(order_shape_policy)
            return self.conversion

    service = _StubRoutingAssessmentService()
    app.dependency_overrides[get_routing_assessment_service] = lambda: service
    try:
        create_response = client.post(
            "/api/v1/routing-assessments/from-desired-trade",
            json={"desired_trade_key": "trade-1"},
        )
        get_response = client.get("/api/v1/routing-assessments/rtassess-1")
        choice_response = client.post(
            "/api/v1/routing-target-choices/from-assessment",
            json={
                "routing_assessment_id": "rtassess-1",
                "binding_key": "money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                "approval_note": "operator approval note",
                "requested_by": "operator@example.test",
            },
        )
        get_choice_response = client.get("/api/v1/routing-target-choices/rtchoice-1")
        conversion_response = client.post(
            "/api/v1/routing-target-choices/rtchoice-1/convert-to-child-intent"
        )
        explicit_limit_conversion_response = client.post(
            "/api/v1/routing-target-choices/rtchoice-1/convert-to-child-intent",
            json={
                "routed_order_shape_policy": {
                    "order_type": "limit",
                    "limit_price": 101.25,
                    "policy_source": "operator_requested",
                    "requested_by": "operator@example.test",
                }
            },
        )
        list_choices_response = client.get("/api/v1/routing-assessments/rtassess-1/target-choices")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert get_response.status_code == 200
    assert choice_response.status_code == 200
    assert get_choice_response.status_code == 200
    assert conversion_response.status_code == 200
    assert explicit_limit_conversion_response.status_code == 200
    assert list_choices_response.status_code == 200
    assert conversion_policy_inputs[0] is None
    assert conversion_policy_inputs[1].order_type == OrderType.LIMIT
    assert conversion_policy_inputs[1].limit_price == Decimal("101.25")
    assert conversion_policy_inputs[1].policy_source == "operator_requested"
    assert conversion_policy_inputs[1].requested_by == "operator@example.test"
    payload = create_response.json()
    assert payload["decision_status"] == "assessment_only"
    assert payload["eligible_binding_count"] == 1
    assert payload["candidates"][0]["eligibility_status"] == "eligible_for_future_selection"
    assert payload["provenance"]["non_executing"] is True
    forbidden_keys = {
        "selected_binding_id",
        "selected_venue",
        "best_binding",
        "recommended_binding",
        "route_decision",
        "execution_plan",
        "child_intent_plan",
    }
    assert not (set(payload) & forbidden_keys)
    choice_payload = choice_response.json()
    assert choice_payload["status"] == "target_choice_recorded"
    assert choice_payload["selected_binding_key"] == "money_flow::hyperliquid_group::hyperliquid_testnet_primary"
    assert choice_payload["selected_venue"] == "hyperliquid"
    assert choice_payload["non_executing"] is True
    assert get_choice_response.json()["target_choice_id"] == "rtchoice-1"
    assert list_choices_response.json()[0]["target_choice_id"] == "rtchoice-1"
    conversion_payload = conversion_response.json()
    assert conversion_payload["status"] == "child_intent_created"
    assert conversion_payload["intent_id"] == "intent-choice-1"
    assert conversion_payload["non_submitting"] is True
    assert conversion_payload["prepared_order_created"] is False
    assert conversion_payload["readiness_assessment_created"] is False
    assert conversion_payload["submitted_order_created"] is False
    target_choice_forbidden_keys = {
        "order_intent_id",
        "prepared_venue_order_id",
        "execution_readiness_assessment_id",
        "submitted_order_id",
        "allocation_weights",
        "venue_ranking",
        "price_score",
        "confidence_score",
        "submit_payload",
    }
    assert not (set(choice_payload) & target_choice_forbidden_keys)
    assert not (set(conversion_payload) & target_choice_forbidden_keys)


def test_routing_conversion_api_rejects_non_finite_limit_price_without_500() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        response = client.post(
            f"/api/v1/routing-target-choices/{choice.target_choice_id}/convert-to-child-intent",
            json={
                "routed_order_shape_policy": {
                    "order_type": "limit",
                    "limit_price": "Infinity",
                    "policy_source": "operator_requested",
                }
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.status_code != 500
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_routing_conversion_api_accepts_finite_decimal_limit_price() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        response = client.post(
            f"/api/v1/routing-target-choices/{choice.target_choice_id}/convert-to-child-intent",
            json={
                "routed_order_shape_policy": {
                    "order_type": "limit",
                    "limit_price": "101.25",
                    "policy_source": "operator_requested",
                    "requested_by": "operator@example.test",
                }
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED.value
    assert _execution_counts(session_factory) == (1, 0, 0)
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == payload["intent_id"])
        )
        assert intent is not None
        assert intent.order_type == OrderType.LIMIT
        assert intent.limit_price == Decimal("101.250000000000")
        assert intent.provenance["routed_order_shape_policy"]["limit_price"] == "101.25"


def test_risk_and_child_intent_endpoints() -> None:
    class _StubRiskEngine:
        async def evaluate_strategy_decision(self, decision_id: str):
            return RiskEvaluation(
                risk_evaluation_id="risk-eval-1",
                risk_evaluation_key="risk-key-1",
                environment=Environment.TESTNET,
                client_ref_id="client-1",
                strategy_mandate_ref_id="mandate-1",
                mandate_key="money_flow::hyperliquid_group",
                market_data_source_policy_ref_id="policy-1",
                planning_source_venue="hyperliquid",
                decision_id=decision_id,
                decision_evaluation_key="eval-close",
                component_key="sleeve_4h",
                target_scope=TradeTargetScope.BINDING,
                mandate_account_binding_ref_id="binding-1",
                binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                venue_account_ref_id="acct-1",
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                action=DecisionAction.CLOSE,
                decision_status=StrategyDecisionStatus.PROPOSED,
                outcome=RiskEvaluationOutcome.APPROVED_DESIRED_TRADE,
                reason_code="child_intent_prepared",
                message="Risk approved the binding-scoped desired trade and prepared a child intent.",
                desired_trade_ref_id="trade-ref-1",
                desired_trade_key="trade-1",
                desired_trade_status=MandateDesiredTradeStatus.APPROVED,
                child_intent_ref_id="intent-ref-1",
                child_intent_id="intent-1",
                child_intent_status=OrderIntentStatus.PREPARED,
                policy_checks={"candidate_binding_key": "money_flow::hyperliquid_group::hyperliquid_testnet_primary"},
                provenance={"phase_boundary": "phase_4_1"},
                evaluated_at=datetime.now(UTC),
            )

        async def evaluate_desired_trade(self, desired_trade):
            return await self.evaluate_strategy_decision("decision-close")

        async def recent_evaluations(
            self,
            *,
            outcome: str | None = None,
            desired_trade_status: MandateDesiredTradeStatus | None = None,
            limit: int = 100,
        ):
            return [await self.evaluate_strategy_decision("decision-close")]

        async def get_kill_switch_state(self) -> bool:
            return False

    class _StubExecutionService:
        async def create_child_intent(self, desired_trade, candidate):
            raise NotImplementedError

        async def list_child_intents(
            self,
            *,
            desired_trade_key: str | None = None,
            binding_key: str | None = None,
            limit: int = 100,
        ):
            return [
                OrderIntent(
                    intent_id="intent-1",
                    sleeve_id="sleeve_4h",
                    component_key="sleeve_4h",
                    decision_id="decision-close",
                    action=DecisionAction.CLOSE,
                    mandate_desired_trade_ref_id="trade-ref-1",
                    desired_trade_key="trade-1",
                    client_ref_id="client-1",
                    strategy_mandate_ref_id="mandate-1",
                    mandate_account_binding_ref_id="binding-1",
                    binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                    venue_account_ref_id="acct-1",
                    instrument_key="perpetual:linear:BTC:USDC:USDC",
                    instrument_ref_id="inst-1",
                    symbol="BTC",
                    environment=Environment.TESTNET,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=Decimal("0.25"),
                    limit_price=None,
                    reduce_only=True,
                    ttl_seconds=30,
                    status=OrderIntentStatus.PREPARED,
                    idempotency_key="intent-key-1",
                    created_at=datetime.now(UTC),
                    provenance={"phase_boundary": "phase_4_1"},
                )
            ]

        async def preview_child_intent(self, intent_id: str):
            return PreparedVenueOrder(
                intent_id=intent_id,
                desired_trade_key="trade-1",
                binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                venue_account_ref_id="acct-1",
                venue="hyperliquid",
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                exchange_symbol="BTC",
                side=OrderSide.SELL,
                quantity=Decimal("0.25"),
                order_type=OrderType.MARKET,
                limit_price=None,
                reduce_only=True,
                time_in_force="ioc",
                client_order_id="mf-preview",
                preview_status=VenueOrderPreviewStatus.PREPARABLE,
                reason_codes=[],
                payload={"endpoint": "/exchange", "action": "order"},
                constraints=VenueOrderConstraints(
                    venue="hyperliquid",
                    support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                    instrument_key="perpetual:linear:BTC:USDC:USDC",
                    instrument_ref_id="inst-1",
                    symbol="BTC",
                    exchange_symbol="BTC",
                    market_type=MarketType.PERPETUAL,
                    product_type=ProductType.LINEAR,
                    price_tick_size=Decimal("0.1"),
                    quantity_step_size=Decimal("0.001"),
                    min_order_size=Decimal("0.001"),
                    supports_order_preview=True,
                    supports_reduce_only_orders=True,
                    supports_client_order_ids=True,
                    supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
                    supported_time_in_force=["gtc", "ioc", "alo"],
                    constraint_metadata_complete=True,
                    notes=None,
                ),
                venue_capabilities=VenueCapabilities(
                    venue=Venue.HYPERLIQUID,
                    support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                    supports_spot=False,
                    supports_perpetuals=True,
                    supports_futures=False,
                    supports_options=False,
                    supports_hedge_mode=False,
                    supports_websocket_market_data=True,
                    supports_user_streams=False,
                    supports_account_sync=True,
                    supports_top_of_book=False,
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
                    supported_time_in_force=["gtc", "ioc", "alo"],
                    account_model="wallet_address",
                    notes=None,
                    private_lifecycle_update_mode="polling",
                ),
                account_connectivity=VenueAccountConnectivity(
                    venue="hyperliquid",
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
                    account_snapshot_available=True,
                    open_orders_query_available=True,
                    open_positions_query_available=True,
                    last_success_at=None,
                    last_error=None,
                ),
                prepared_at=datetime.now(UTC),
            )

        async def submit_prepared_intent(self, intent):
            raise NotImplementedError

        async def assess_child_intent_readiness(self, intent_id: str):
            preview = await self.preview_child_intent(intent_id)
            from core.domain.enums import ExecutionReadinessOutcome
            from core.domain.models import ExecutionReadinessAssessment

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
                binding_key="money_flow::hyperliquid_group::hyperliquid_testnet_primary",
                venue_account_ref_id="acct-1",
                instrument_key="perpetual:linear:BTC:USDC:USDC",
                instrument_ref_id="inst-1",
                symbol="BTC",
                venue="hyperliquid",
                support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
                preview_status=VenueOrderPreviewStatus.PREPARABLE,
                outcome=ExecutionReadinessOutcome.BLOCKED_BY_ADAPTER,
                eligible_for_submission_in_principle=False,
                live_submission_phase_enabled=False,
                venue_supports_order_submission=True,
                adapter_supports_order_submission=False,
                adapter_supports_order_cancel=False,
                adapter_supports_order_amend=False,
                submission_authorized=False,
                account_connected=True,
                private_state_required=True,
                private_state_ready=False,
                reason_codes=["adapter_submission_unimplemented"],
                message="Prepared child intent is not submission-ready: adapter_submission_unimplemented.",
                prepared_order=preview,
                evaluated_at=datetime.now(UTC),
                provenance={"phase_boundary": "phase_4_2"},
            )

        async def list_readiness_assessments(self, *, intent_id=None, outcome=None, limit: int = 100):
            return [await self.assess_child_intent_readiness(intent_id or "intent-1")]

        async def reconcile_fills(self, submitted_order_id: str):
            return []

    app.dependency_overrides[get_risk_engine] = lambda: _StubRiskEngine()
    app.dependency_overrides[get_execution_service] = lambda: _StubExecutionService()
    try:
        evaluation_response = client.post("/api/v1/risk/evaluations/from-decision/decision-close")
        list_response = client.get("/api/v1/risk/evaluations")
        intents_response = client.get("/api/v1/child-intents")
        preview_response = client.get("/api/v1/child-intents/intent-1/prepared-order-preview")
    finally:
        app.dependency_overrides.clear()

    assert evaluation_response.status_code == 200
    assert evaluation_response.json()["outcome"] == "approved_desired_trade"
    assert evaluation_response.json()["child_intent_id"] == "intent-1"
    assert list_response.status_code == 200
    assert list_response.json()[0]["desired_trade_status"] == "approved"
    assert intents_response.status_code == 200
    assert intents_response.json()[0]["status"] == "prepared"
    assert intents_response.json()[0]["reduce_only"] is True
    assert preview_response.status_code == 200
    assert preview_response.json()["preview_status"] == "preparable"
    assert preview_response.json()["exchange_symbol"] == "BTC"
