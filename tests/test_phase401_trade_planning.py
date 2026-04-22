from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    InstrumentResolutionMode,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderSide,
    PositionStatus,
    ProductType,
    StrategyDecisionStatus,
    StrategyFamily,
    Timeframe,
    TradeTargetScope,
    Venue,
    VenueSupportLevel,
    OrderType,
)
from core.domain.models import ExchangeStatus, TopOfBookSnapshot, VenueCapabilities
from db.models import (
    ClientModel,
    InstrumentModel,
    MandateAccountBindingModel,
    MandateMarketDataSourcePolicyModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    PositionModel,
    StrategyDecisionModel,
    StrategyMandateModel,
    SymbolModel,
    VenueAccountModel,
)
from services.planning.service import DefaultTradePlanningService
from services.runtime.context import DefaultRuntimeContextService
from tests.test_phase3_strategy import build_settings, build_test_session_factory, seed_symbol


class _StubVenueAdapter:
    def __init__(
        self,
        *,
        venue: str,
        supports_order_submission: bool,
        top_of_book: TopOfBookSnapshot | None,
    ) -> None:
        self._venue = venue
        self._supports_order_submission = supports_order_submission
        self._top_of_book = top_of_book

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue(self._venue),
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            supports_spot=self._venue != Venue.HYPERLIQUID.value,
            supports_perpetuals=True,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=False,
            supports_account_sync=True,
            supports_top_of_book=True,
            supports_depth_summary=False,
            supports_order_submission=self._supports_order_submission,
            supports_order_cancel=True,
            supports_order_amend=True,
            supports_recent_fills_query=False,
            adapter_supports_order_submission=False,
            adapter_supports_order_cancel=False,
            adapter_supports_order_amend=False,
            adapter_supports_user_streams=False,
            supports_order_preview=True,
            supports_account_snapshot=True,
            supports_open_orders_query=self._venue == Venue.HYPERLIQUID.value,
            supports_open_positions_query=self._venue == Venue.HYPERLIQUID.value,
            supports_reduce_only_orders=self._venue != Venue.COINBASE_ADVANCED_TRADE.value,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=self._venue == Venue.OKX.value,
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
            supported_time_in_force=["gtc", "ioc"],
            account_model="wallet_address" if self._venue == Venue.HYPERLIQUID.value else "account_with_subaccounts",
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
            wallet_address_configured=self._venue == Venue.HYPERLIQUID.value,
            account_identifier_configured=True,
            credentials_configured=self._venue != Venue.HYPERLIQUID.value,
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
        return self._top_of_book


class _StubVenueRegistry:
    def __init__(self) -> None:
        self._adapters = {
            Venue.HYPERLIQUID.value: _StubVenueAdapter(
                venue=Venue.HYPERLIQUID.value,
                supports_order_submission=True,
                top_of_book=TopOfBookSnapshot(
                    instrument_key="perpetual:linear:BTC:USDC:USDC",
                    instrument_ref_id="inst-1",
                    venue=Venue.HYPERLIQUID.value,
                    symbol="BTC",
                    bid_price=Decimal("100"),
                    bid_size=Decimal("2"),
                    ask_price=Decimal("101"),
                    ask_size=Decimal("3"),
                    observed_at=datetime.now(UTC),
                ),
            ),
            Venue.OKX.value: _StubVenueAdapter(
                venue=Venue.OKX.value,
                supports_order_submission=True,
                top_of_book=None,
            ),
        }

    async def list_supported_venues(self):
        raise NotImplementedError

    async def get_adapter(self, venue: str):
        return self._adapters[venue]


def _seed_additional_okx_binding(session_factory, *, mandate_key: str) -> None:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "default_client"))
        mandate = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        assert client is not None
        assert mandate is not None
        okx_account = VenueAccountModel(
            venue_account_key="okx_testnet_desk_a",
            client_ref_id=client.id,
            venue=Venue.OKX.value,
            environment=Environment.TESTNET,
            venue_native_account_id="okx-acct",
            account_address=None,
            account_label="desk-a",
            subaccount_label="desk-a",
            credentials_ref="secret://okx",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={},
        )
        session.add(okx_account)
        session.flush()
        session.add(
            MandateAccountBindingModel(
                binding_key=f"{mandate_key}::okx_testnet_desk_a",
                strategy_mandate_ref_id=mandate.id,
                venue_account_ref_id=okx_account.id,
                enabled=True,
                strategy_eligible=True,
                routing_eligible=True,
                trading_enabled=True,
                allow_builder_deployed_for_strategy=False,
                allow_builder_deployed_for_trading=False,
                notes=None,
                metadata_json={},
            )
        )
        session.commit()


def _seed_additional_hyperliquid_binding(session_factory, *, mandate_key: str, suffix: str) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "default_client"))
        mandate = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        assert client is not None
        assert mandate is not None
        venue_account_key = f"hyperliquid_testnet_{suffix}"
        account = VenueAccountModel(
            venue_account_key=venue_account_key,
            client_ref_id=client.id,
            venue=Venue.HYPERLIQUID.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"acct-{suffix}",
            account_address=f"acct-{suffix}",
            account_label=suffix,
            subaccount_label=None,
            credentials_ref=None,
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={},
        )
        session.add(account)
        session.flush()
        binding_key = f"{mandate_key}::{venue_account_key}"
        session.add(
            MandateAccountBindingModel(
                binding_key=binding_key,
                strategy_mandate_ref_id=mandate.id,
                venue_account_ref_id=account.id,
                enabled=True,
                strategy_eligible=True,
                routing_eligible=True,
                trading_enabled=True,
                allow_builder_deployed_for_strategy=False,
                allow_builder_deployed_for_trading=False,
                notes=None,
                metadata_json={},
            )
        )
        session.commit()
        return binding_key


def _seed_okx_symbol(session_factory, *, instrument_ref_id: str) -> None:
    with session_factory() as session:
        session.add(
            SymbolModel(
                instrument_ref_id=instrument_ref_id,
                venue=Venue.OKX.value,
                symbol="BTC",
                exchange_symbol="BTC-USDT-SWAP",
                venue_asset_id="BTC-USDT-SWAP",
                asset_id=None,
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset="BTC",
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
                is_trading_eligible=False,
                is_active=True,
                raw_metadata={},
            )
        )
        session.commit()


def _update_source_policy(
    session_factory,
    *,
    mandate_key: str,
    market_type: MarketType | None,
    product_type: ProductType | None,
    instrument_resolution_mode: InstrumentResolutionMode,
) -> None:
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
        policy.source_venue = Venue.HYPERLIQUID.value
        policy.market_type = market_type
        policy.product_type = product_type
        policy.instrument_resolution_mode = instrument_resolution_mode
        session.commit()


def test_open_decision_previews_as_mandate_desired_trade_and_does_not_create_child_intents() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)

    with session_factory() as session:
        session.add(
            StrategyDecisionModel(
                environment=Environment.TESTNET,
                decision_id="decision-open",
                evaluation_key="eval-open",
                family=StrategyFamily.MONEY_FLOW,
                signal_id="signal-open",
                sleeve_id="sleeve_1h",
                component_key="sleeve_1h",
                client_ref_id=context.client.client_ref_id,
                strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                mandate_key=context.mandate.mandate_key,
                binding_key=context.bindings[0].binding.binding_key,
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol="BTC",
                action=DecisionAction.OPEN,
                status=StrategyDecisionStatus.PROPOSED,
                reason_code=None,
                confidence=Decimal("0.8"),
                rationale="bullish",
                provenance={"strategy_version": "money_flow_v1_1"},
                features={},
                decided_at=datetime.now(UTC),
            )
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )
    desired_trade = asyncio.run(
        planning.preview_desired_trade_from_decision("decision-open", persist=True)
    )

    assert desired_trade.target_scope == TradeTargetScope.MANDATE
    assert desired_trade.mandate_account_binding_ref_id is None
    assert desired_trade.binding_key is None
    assert desired_trade.status == MandateDesiredTradeStatus.DRAFT
    assert desired_trade.planning_source_venue == Venue.HYPERLIQUID.value
    assert desired_trade.source_evaluation_keys == ["eval-open"]

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 1
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0


def test_close_decision_previews_as_binding_scoped_desired_trade() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, symbol_id, _instrument_key = seed_symbol(session_factory)

    with session_factory() as session:
        session.add(
            PositionModel(
                environment=Environment.TESTNET,
                position_id="pos-btc",
                exchange_position_key="btc-one-way",
                account_position_key="acct:btc:one_way",
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                sleeve_id=None,
                venue="hyperliquid",
                account_address="acct",
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol="BTC",
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                attribution_status=AttributionStatus.UNASSIGNED,
                quantity=Decimal("0.25"),
                avg_entry_price=Decimal("100"),
                mark_price=Decimal("99"),
                unrealized_pnl=Decimal("-0.25"),
                position_value=Decimal("24.75"),
                margin_used=Decimal("5"),
                liquidation_price=Decimal("80"),
                leverage_type="cross",
                leverage_value=5,
                raw_payload={},
                opened_at=datetime.now(UTC),
            )
        )
        session.add(
            StrategyDecisionModel(
                environment=Environment.TESTNET,
                decision_id="decision-close",
                evaluation_key="eval-close",
                family=StrategyFamily.MONEY_FLOW,
                signal_id="signal-close",
                sleeve_id="sleeve_4h",
                component_key="sleeve_4h",
                client_ref_id=context.client.client_ref_id,
                strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                mandate_key=context.mandate.mandate_key,
                binding_key=context.bindings[0].binding.binding_key,
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol="BTC",
                action=DecisionAction.CLOSE,
                status=StrategyDecisionStatus.PROPOSED,
                reason_code="trend_invalidated",
                confidence=Decimal("0.9"),
                rationale="bearish",
                provenance={"strategy_version": "money_flow_v1_1"},
                features={},
                decided_at=datetime.now(UTC),
            )
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )
    desired_trade = asyncio.run(planning.preview_desired_trade_from_decision("decision-close"))

    assert desired_trade.target_scope == TradeTargetScope.BINDING
    assert desired_trade.binding_key == context.bindings[0].binding.binding_key
    assert desired_trade.side == OrderSide.SELL
    assert desired_trade.desired_quantity == Decimal("0.25")


def test_routing_candidates_normalize_quotes_and_binding_eligibility() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _seed_additional_okx_binding(session_factory, mandate_key=context.mandate.mandate_key)
    _seed_okx_symbol(session_factory, instrument_ref_id=instrument_ref_id)

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )
    candidates = asyncio.run(
        planning.list_routing_candidates(
            symbol="BTC",
            component_key="sleeve_15m",
        )
    )
    by_venue = {candidate.venue: candidate for candidate in candidates}

    assert set(by_venue) == {Venue.HYPERLIQUID.value, Venue.OKX.value}
    assert by_venue[Venue.HYPERLIQUID.value].instrument_key == instrument_key
    assert by_venue[Venue.HYPERLIQUID.value].quote_available is True
    assert by_venue[Venue.OKX.value].exchange_symbol == "BTC-USDT-SWAP"
    assert "venue_read_only_mode" in by_venue[Venue.OKX.value].eligibility_reasons
    assert "quote_unavailable" in by_venue[Venue.OKX.value].eligibility_reasons

    quotes = asyncio.run(
        planning.list_binding_quotes(
            symbol="BTC",
            component_key="sleeve_15m",
        )
    )
    assert len(quotes) == 2
    okx_quote = next(item for item in quotes if item.venue == Venue.OKX.value)
    assert okx_quote.quote_snapshot is not None
    assert okx_quote.quote_snapshot.available is False
    assert okx_quote.quote_snapshot.reason_unavailable == "top_of_book_unavailable"


def test_open_desired_trade_aggregates_across_bindings_idempotently() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    second_binding_key = _seed_additional_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="secondary",
    )
    planning_as_of = datetime.now(UTC).replace(microsecond=0)

    with session_factory() as session:
        second_binding = session.scalar(
            select(MandateAccountBindingModel).where(MandateAccountBindingModel.binding_key == second_binding_key)
        )
        second_account = session.scalar(
            select(VenueAccountModel).where(VenueAccountModel.venue_account_key == "hyperliquid_testnet_secondary")
        )
        assert second_binding is not None
        assert second_account is not None
        session.add_all(
            [
                StrategyDecisionModel(
                    environment=Environment.TESTNET,
                    decision_id="decision-open-a",
                    evaluation_key="eval-open-a",
                    family=StrategyFamily.MONEY_FLOW,
                    signal_id="signal-open-a",
                    sleeve_id="sleeve_1h",
                    component_key="sleeve_1h",
                    client_ref_id=context.client.client_ref_id,
                    strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                    mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                    mandate_key=context.mandate.mandate_key,
                    binding_key=context.bindings[0].binding.binding_key,
                    venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=None,
                    symbol="BTC",
                    action=DecisionAction.OPEN,
                    status=StrategyDecisionStatus.PROPOSED,
                    reason_code=None,
                    confidence=Decimal("0.7"),
                    rationale="bullish_a",
                    provenance={
                        "strategy_version": "money_flow_v1_1",
                        "indicator_as_of": planning_as_of.isoformat(),
                        "latest_candle_close": planning_as_of.isoformat(),
                    },
                    features={},
                    decided_at=planning_as_of,
                ),
                StrategyDecisionModel(
                    environment=Environment.TESTNET,
                    decision_id="decision-open-b",
                    evaluation_key="eval-open-b",
                    family=StrategyFamily.MONEY_FLOW,
                    signal_id="signal-open-b",
                    sleeve_id="sleeve_1h",
                    component_key="sleeve_1h",
                    client_ref_id=context.client.client_ref_id,
                    strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                    mandate_account_binding_ref_id=second_binding.id,
                    mandate_key=context.mandate.mandate_key,
                    binding_key=second_binding_key,
                    venue_account_ref_id=second_account.id,
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=None,
                    symbol="BTC",
                    action=DecisionAction.OPEN,
                    status=StrategyDecisionStatus.PROPOSED,
                    reason_code=None,
                    confidence=Decimal("0.75"),
                    rationale="bullish_b",
                    provenance={
                        "strategy_version": "money_flow_v1_1",
                        "indicator_as_of": planning_as_of.isoformat(),
                        "latest_candle_close": planning_as_of.isoformat(),
                    },
                    features={},
                    decided_at=planning_as_of,
                ),
            ]
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )
    first_trade = asyncio.run(
        planning.preview_desired_trade_from_decision("decision-open-a", persist=True)
    )
    second_trade = asyncio.run(
        planning.preview_desired_trade_from_decision("decision-open-b", persist=True)
    )

    assert first_trade.desired_trade_key == second_trade.desired_trade_key
    assert second_trade.target_scope == TradeTargetScope.MANDATE
    assert second_trade.instrument_key == instrument_key
    assert sorted(second_trade.source_decision_ids) == ["decision-open-a", "decision-open-b"]
    assert sorted(second_trade.source_evaluation_keys) == ["eval-open-a", "eval-open-b"]
    assert sorted(second_trade.source_binding_keys) == sorted(
        [context.bindings[0].binding.binding_key, second_binding_key]
    )

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 1
        model = session.scalar(select(MandateDesiredTradeModel))
        assert model is not None
        assert sorted(model.source_decision_ids_json) == ["decision-open-a", "decision-open-b"]
        assert sorted(model.source_evaluation_keys_json) == ["eval-open-a", "eval-open-b"]


def test_convertibility_rules_reject_hold_no_trade_and_invalid() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)

    with session_factory() as session:
        session.add_all(
            [
                StrategyDecisionModel(
                    environment=Environment.TESTNET,
                    decision_id="decision-hold",
                    evaluation_key="eval-hold",
                    family=StrategyFamily.MONEY_FLOW,
                    signal_id="signal-hold",
                    sleeve_id="sleeve_1h",
                    component_key="sleeve_1h",
                    client_ref_id=context.client.client_ref_id,
                    strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                    mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                    mandate_key=context.mandate.mandate_key,
                    binding_key=context.bindings[0].binding.binding_key,
                    venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=None,
                    symbol="BTC",
                    action=DecisionAction.HOLD,
                    status=StrategyDecisionStatus.PROPOSED,
                    reason_code=None,
                    confidence=None,
                    rationale="hold",
                    provenance={"strategy_version": "money_flow_v1_1"},
                    features={},
                    decided_at=datetime.now(UTC),
                ),
                StrategyDecisionModel(
                    environment=Environment.TESTNET,
                    decision_id="decision-no-trade",
                    evaluation_key="eval-no-trade",
                    family=StrategyFamily.MONEY_FLOW,
                    signal_id="signal-no-trade",
                    sleeve_id="sleeve_1h",
                    component_key="sleeve_1h",
                    client_ref_id=context.client.client_ref_id,
                    strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                    mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                    mandate_key=context.mandate.mandate_key,
                    binding_key=context.bindings[0].binding.binding_key,
                    venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=None,
                    symbol="BTC",
                    action=DecisionAction.NOOP,
                    status=StrategyDecisionStatus.NO_TRADE,
                    reason_code="no_trade",
                    confidence=None,
                    rationale="no_trade",
                    provenance={"strategy_version": "money_flow_v1_1"},
                    features={},
                    decided_at=datetime.now(UTC),
                ),
                StrategyDecisionModel(
                    environment=Environment.TESTNET,
                    decision_id="decision-invalid",
                    evaluation_key="eval-invalid",
                    family=StrategyFamily.MONEY_FLOW,
                    signal_id="signal-invalid",
                    sleeve_id="sleeve_1h",
                    component_key="sleeve_1h",
                    client_ref_id=context.client.client_ref_id,
                    strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                    mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                    mandate_key=context.mandate.mandate_key,
                    binding_key=context.bindings[0].binding.binding_key,
                    venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=None,
                    symbol="BTC",
                    action=DecisionAction.OPEN,
                    status=StrategyDecisionStatus.INVALID,
                    reason_code="invalid",
                    confidence=None,
                    rationale="invalid",
                    provenance={"strategy_version": "money_flow_v1_1"},
                    features={},
                    decided_at=datetime.now(UTC),
                ),
            ]
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )

    hold = asyncio.run(planning.inspect_decision_convertibility("decision-hold"))
    no_trade = asyncio.run(planning.inspect_decision_convertibility("decision-no-trade"))
    invalid = asyncio.run(planning.inspect_decision_convertibility("decision-invalid"))

    assert hold.convertible is False
    assert hold.reason_code == "hold_non_convertible"
    assert no_trade.convertible is False
    assert no_trade.reason_code == "decision_no_trade_not_convertible"
    assert invalid.convertible is False
    assert invalid.reason_code == "decision_invalid_not_convertible"


def test_reduce_is_binding_scoped_when_binding_context_exists() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, _instrument_key = seed_symbol(session_factory)

    with session_factory() as session:
        session.add(
            StrategyDecisionModel(
                environment=Environment.TESTNET,
                decision_id="decision-reduce",
                evaluation_key="eval-reduce",
                family=StrategyFamily.MONEY_FLOW,
                signal_id="signal-reduce",
                sleeve_id="sleeve_15m",
                component_key="sleeve_15m",
                client_ref_id=context.client.client_ref_id,
                strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                mandate_account_binding_ref_id=context.bindings[0].binding.binding_ref_id,
                mandate_key=context.mandate.mandate_key,
                binding_key=context.bindings[0].binding.binding_key,
                venue_account_ref_id=context.bindings[0].venue_account.venue_account_ref_id,
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol="BTC",
                action=DecisionAction.REDUCE,
                status=StrategyDecisionStatus.PROPOSED,
                reason_code="take_partial",
                confidence=Decimal("0.8"),
                rationale="reduce",
                provenance={"strategy_version": "money_flow_v1_1"},
                features={},
                decided_at=datetime.now(UTC),
            )
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )
    desired_trade = asyncio.run(planning.preview_desired_trade_from_decision("decision-reduce"))

    assert desired_trade.target_scope == TradeTargetScope.BINDING
    assert desired_trade.binding_key == context.bindings[0].binding.binding_key
    assert desired_trade.side == OrderSide.SELL


def test_source_policy_and_symbol_ambiguity_are_explicit() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::planning")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime.ensure_active_context())
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _update_source_policy(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        market_type=None,
        product_type=None,
        instrument_resolution_mode=InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS,
    )
    with session_factory() as session:
        spot_instrument = InstrumentModel(
            instrument_key="spot:spot:BTC:USDC:",
            canonical_symbol="BTC",
            market_type=MarketType.SPOT,
            product_type=ProductType.SPOT,
            base_asset="BTC",
            quote_asset="USDC",
            settlement_asset=None,
            is_active=True,
        )
        session.add(spot_instrument)
        session.flush()
        session.add(
            SymbolModel(
                instrument_ref_id=spot_instrument.id,
                venue=Venue.HYPERLIQUID.value,
                symbol="BTC",
                exchange_symbol="BTC-SPOT",
                venue_asset_id="btc-spot",
                asset_id=10,
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset="BTC",
                quote_asset="USDC",
                settlement_asset=None,
                price_tick_size=Decimal("0.1"),
                quantity_step_size=Decimal("0.0001"),
                min_order_size=Decimal("0.0001"),
                size_decimals=4,
                max_leverage=None,
                only_isolated=False,
                is_perpetual=False,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
        )
        session.commit()

    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=_StubVenueRegistry(),
    )

    policy = asyncio.run(planning.get_market_data_source_policy())
    assert policy.source_venue == Venue.HYPERLIQUID.value
    assert policy.runtime_exchange_matches_source is True

    try:
        asyncio.run(planning.list_routing_candidates(symbol="BTC", component_key="sleeve_15m"))
        assert False, "Expected ambiguous canonical symbol resolution to raise."
    except ValueError as exc:
        assert "Ambiguous canonical symbol" in str(exc)

    candidates = asyncio.run(
        planning.list_routing_candidates(
            instrument_key=instrument_key,
            component_key="sleeve_15m",
        )
    )
    assert candidates
