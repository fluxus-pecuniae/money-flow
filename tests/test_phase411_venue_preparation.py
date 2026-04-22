from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.domain.enums import (
    DecisionAction,
    Environment,
    MandateDesiredTradeStatus,
    MarketType,
    OrderSide,
    OrderType,
    OrderIntentStatus,
    ProductType,
    StrategyFamily,
    TradeTargetScope,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.models import BindingRoutingCandidate, MandateDesiredTrade, OrderIntent, VenueCapabilities
from db.base import Base
from db.models import ClientModel, InstrumentModel, SymbolModel, VenueAccountModel
from services.execution.service import DefaultExecutionService
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.base import ReadOnlyVenueAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService
from services.runtime.context import DefaultRuntimeContextService
from tests.test_phase3_strategy import build_settings


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_account(session_factory, *, venue: str, venue_account_key: str, account_identifier: str) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-1"))
        if client is None:
            client = ClientModel(client_key="client-1", display_name="Client 1", is_active=True)
            session.add(client)
            session.flush()
        account = VenueAccountModel(
            venue_account_key=venue_account_key,
            client_ref_id=client.id,
            venue=venue,
            environment=Environment.TESTNET,
            venue_native_account_id=account_identifier,
            account_address=account_identifier,
            account_label="primary",
            subaccount_label=None,
            credentials_ref=None,
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={},
        )
        session.add(account)
        session.commit()
        return account.id


def _seed_symbol(
    session_factory,
    *,
    venue: str,
    exchange_symbol: str,
    canonical_symbol: str = "BTC",
    market_type: MarketType = MarketType.PERPETUAL,
    product_type: ProductType = ProductType.LINEAR,
    quote_asset: str = "USDT",
    settlement_asset: str | None = "USDT",
    price_tick_size: Decimal = Decimal("0.1"),
    quantity_step_size: Decimal = Decimal("0.001"),
    min_order_size: Decimal = Decimal("0.001"),
    asset_id: int | None = None,
) -> tuple[str, str]:
    instrument_key = (
        f"{market_type.value}:{product_type.value}:{canonical_symbol}:{quote_asset}:{(settlement_asset or '').upper()}"
    )
    with session_factory() as session:
        instrument = session.scalar(
            select(InstrumentModel).where(InstrumentModel.instrument_key == instrument_key)
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key=instrument_key,
                canonical_symbol=canonical_symbol,
                market_type=market_type,
                product_type=product_type,
                base_asset=canonical_symbol,
                quote_asset=quote_asset,
                settlement_asset=settlement_asset,
                is_active=True,
            )
            session.add(instrument)
            session.flush()
        symbol = SymbolModel(
            instrument_ref_id=instrument.id,
            venue=venue,
            symbol=canonical_symbol,
            exchange_symbol=exchange_symbol,
            venue_asset_id=exchange_symbol,
            asset_id=asset_id,
            market_type=market_type,
            product_type=product_type,
            base_asset=canonical_symbol,
            quote_asset=quote_asset,
            settlement_asset=settlement_asset,
            price_tick_size=price_tick_size,
            quantity_step_size=quantity_step_size,
            min_order_size=min_order_size,
            size_decimals=3,
            max_leverage=20,
            only_isolated=False,
            is_perpetual=market_type == MarketType.PERPETUAL,
            is_builder_deployed=False,
            is_strategy_eligible=True,
            is_trading_eligible=True,
            is_active=True,
            raw_metadata={},
        )
        session.add(symbol)
        session.commit()
        return instrument.id, instrument_key


def _intent(
    *,
    venue_account_ref_id: str,
    instrument_ref_id: str,
    instrument_key: str,
    symbol: str = "BTC",
    quantity: Decimal = Decimal("0.01"),
    order_type: OrderType = OrderType.MARKET,
    reduce_only: bool = False,
    limit_price: Decimal | None = None,
) -> OrderIntent:
    return OrderIntent(
        intent_id="intent-test",
        sleeve_id="sleeve_1h",
        component_key="sleeve_1h",
        decision_id="decision-1",
        action=DecisionAction.REDUCE if reduce_only else DecisionAction.OPEN,
        mandate_desired_trade_ref_id=None,
        desired_trade_key="trade-1",
        client_ref_id=None,
        strategy_mandate_ref_id=None,
        mandate_account_binding_ref_id=None,
        binding_key="binding-1",
        venue_account_ref_id=venue_account_ref_id,
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        symbol=symbol,
        environment=Environment.TESTNET,
        side=OrderSide.SELL if reduce_only else OrderSide.BUY,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit_price,
        reduce_only=reduce_only,
        ttl_seconds=30,
        status=OrderIntentStatus.PREPARED,
        idempotency_key="idempotency-1",
        created_at=datetime.now(UTC),
        provenance={},
    )


def test_current_integrated_venues_are_execution_preparable() -> None:
    settings = build_settings(
        ASTER_ACCOUNT_IDENTIFIER="aster-main",
        OKX_ACCOUNT_IDENTIFIER="okx-main",
        COINBASE_ADVANCED_ACCOUNT_IDENTIFIER="cb-main",
    )
    hyperliquid_session_factory = _session_factory()

    adapters = [
        HyperliquidExchangeAdapter(
            settings,
            session_factory=hyperliquid_session_factory,
            runtime_context_service=DefaultRuntimeContextService(
                settings,
                session_factory=hyperliquid_session_factory,
            ),
        ),
        AsterExchangeAdapter(settings, session_factory=_session_factory()),
        OkxExchangeAdapter(settings, session_factory=_session_factory()),
        CoinbaseAdvancedTradeExchangeAdapter(settings, session_factory=_session_factory()),
    ]

    for adapter in adapters:
        capabilities = asyncio.run(adapter.get_venue_capabilities())
        connectivity = asyncio.run(adapter.get_account_connectivity())
        assert isinstance(capabilities, VenueCapabilities)
        assert capabilities.support_level == VenueSupportLevel.EXECUTION_PREPARABLE
        assert capabilities.supports_order_preview is True
        assert connectivity.support_level == VenueSupportLevel.EXECUTION_PREPARABLE


def test_current_venues_prepare_native_order_previews() -> None:
    session_factory = _session_factory()
    settings = build_settings(
        ASTER_ACCOUNT_IDENTIFIER="aster-main",
        OKX_ACCOUNT_IDENTIFIER="okx-main",
        COINBASE_ADVANCED_ACCOUNT_IDENTIFIER="cb-main",
    )

    specs = [
        (
            HyperliquidExchangeAdapter(
                settings,
                session_factory=session_factory,
                runtime_context_service=DefaultRuntimeContextService(settings, session_factory=session_factory),
            ),
            Venue.HYPERLIQUID.value,
            "BTC",
            MarketType.PERPETUAL,
            ProductType.LINEAR,
            "USDC",
            "USDC",
            "/exchange",
            0,
        ),
        (
            AsterExchangeAdapter(settings, session_factory=session_factory),
            Venue.ASTER.value,
            "BTCUSDT",
            MarketType.PERPETUAL,
            ProductType.LINEAR,
            "USDT",
            "USDT",
            "/fapi/v1/order",
            None,
        ),
        (
            OkxExchangeAdapter(settings, session_factory=session_factory),
            Venue.OKX.value,
            "BTC-USDT-SWAP",
            MarketType.PERPETUAL,
            ProductType.LINEAR,
            "USDT",
            "USDT",
            "/api/v5/trade/order",
            None,
        ),
        (
            CoinbaseAdvancedTradeExchangeAdapter(settings, session_factory=session_factory),
            Venue.COINBASE_ADVANCED_TRADE.value,
            "BTC-USD",
            MarketType.SPOT,
            ProductType.SPOT,
            "USD",
            None,
            "/api/v3/brokerage/orders",
            None,
        ),
    ]

    for adapter, venue, exchange_symbol, market_type, product_type, quote_asset, settlement_asset, endpoint, asset_id in specs:
        account_ref_id = _seed_account(
            session_factory,
            venue=venue,
            venue_account_key=f"{venue}_acct",
            account_identifier=f"{venue}-acct",
        )
        instrument_ref_id, instrument_key = _seed_symbol(
            session_factory,
            venue=venue,
            exchange_symbol=exchange_symbol,
            market_type=market_type,
            product_type=product_type,
            quote_asset=quote_asset,
            settlement_asset=settlement_asset,
            asset_id=asset_id,
        )
        preview = asyncio.run(
            adapter.prepare_order_preview(
                _intent(
                    venue_account_ref_id=account_ref_id,
                    instrument_ref_id=instrument_ref_id,
                    instrument_key=instrument_key,
                    symbol="BTC",
                    quantity=Decimal("0.01"),
                    order_type=OrderType.LIMIT if venue == Venue.HYPERLIQUID.value else OrderType.MARKET,
                    limit_price=Decimal("50000") if venue == Venue.HYPERLIQUID.value else None,
                )
            )
        )
        assert preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
        assert preview.exchange_symbol == exchange_symbol
        assert preview.payload is not None
        assert preview.payload["endpoint"] == endpoint


def test_order_preview_rejects_invalid_quantity_step() -> None:
    session_factory = _session_factory()
    settings = build_settings(OKX_ACCOUNT_IDENTIFIER="okx-main")
    adapter = OkxExchangeAdapter(settings, session_factory=session_factory)
    account_ref_id = _seed_account(
        session_factory,
        venue=Venue.OKX.value,
        venue_account_key="okx_acct",
        account_identifier="okx-acct",
    )
    instrument_ref_id, instrument_key = _seed_symbol(
        session_factory,
        venue=Venue.OKX.value,
        exchange_symbol="BTC-USDT-SWAP",
        quantity_step_size=Decimal("0.001"),
    )

    preview = asyncio.run(
        adapter.prepare_order_preview(
            _intent(
                venue_account_ref_id=account_ref_id,
                instrument_ref_id=instrument_ref_id,
                instrument_key=instrument_key,
                quantity=Decimal("0.0005"),
            )
        )
    )

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "below_min_order_size" in preview.reason_codes
    assert "invalid_quantity_step" in preview.reason_codes


def test_future_qa_read_only_venues_can_still_be_modeled() -> None:
    class _QaVenueAdapter(ReadOnlyVenueAdapter):
        account_model = "account_id"
        support_level = VenueSupportLevel.QA_READ_ONLY

        async def _ping(self) -> None:
            return None

        async def _fetch_symbol_metadata(self):
            return []

        async def get_venue_capabilities(self) -> VenueCapabilities:
            return VenueCapabilities(
                venue=Venue.ASTER,
                support_level=VenueSupportLevel.QA_READ_ONLY,
                supports_spot=False,
                supports_perpetuals=True,
                supports_futures=False,
                supports_options=False,
                supports_hedge_mode=False,
                supports_websocket_market_data=True,
                supports_user_streams=False,
                supports_account_sync=False,
                supports_top_of_book=False,
                supports_depth_summary=False,
                supports_order_submission=False,
                supports_order_cancel=False,
                supports_order_amend=False,
                supports_recent_fills_query=False,
                adapter_supports_order_submission=False,
                adapter_supports_order_cancel=False,
                adapter_supports_order_amend=False,
                adapter_supports_user_streams=False,
                supports_order_preview=False,
                supports_account_snapshot=False,
                supports_open_orders_query=False,
                supports_open_positions_query=False,
                supports_reduce_only_orders=False,
                supports_client_order_ids=False,
                supports_demo_mode=False,
                supports_subaccounts=False,
                supported_order_types=[],
                supported_time_in_force=[],
                account_model="account_id",
                notes="qa only",
                private_lifecycle_update_mode="polling",
            )

    session_factory = _session_factory()
    settings = build_settings(ASTER_ENABLED=True)
    adapter = _QaVenueAdapter(settings.aster_integration, settings, session_factory=session_factory)
    account_ref_id = _seed_account(
        session_factory,
        venue=Venue.ASTER.value,
        venue_account_key="qa_aster",
        account_identifier="qa-aster",
    )
    instrument_ref_id, instrument_key = _seed_symbol(
        session_factory,
        venue=Venue.ASTER.value,
        exchange_symbol="BTCUSDT",
    )

    preview = asyncio.run(
        adapter.prepare_order_preview(
            _intent(
                venue_account_ref_id=account_ref_id,
                instrument_ref_id=instrument_ref_id,
                instrument_key=instrument_key,
            )
        )
    )

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "venue_not_execution_preparable" in preview.reason_codes
    assert "venue_order_preview_unsupported" in preview.reason_codes


def test_execution_service_persists_prepared_order_preview_provenance() -> None:
    session_factory = _session_factory()
    settings = build_settings(OKX_ACCOUNT_IDENTIFIER="okx-main")
    registry = DefaultVenueRegistryService(settings, session_factory=session_factory)
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )
    account_ref_id = _seed_account(
        session_factory,
        venue=Venue.OKX.value,
        venue_account_key="okx_child_intent",
        account_identifier="okx-child",
    )
    instrument_ref_id, instrument_key = _seed_symbol(
        session_factory,
        venue=Venue.OKX.value,
        exchange_symbol="BTC-USDT-SWAP",
    )
    adapter = asyncio.run(registry.get_adapter(Venue.OKX.value))

    desired_trade = MandateDesiredTrade(
        desired_trade_key="trade-1",
        desired_trade_ref_id=None,
        evaluated_state_fingerprint="eval-state-1",
        environment=Environment.TESTNET,
        client_ref_id=None,
        strategy_mandate_ref_id=None,
        mandate_key="mandate-1",
        family=StrategyFamily.MONEY_FLOW,
        component_key="sleeve_1h",
        market_data_source_policy_ref_id=None,
        planning_source_venue=Venue.HYPERLIQUID.value,
        planning_source_mode=settings.mandate_market_data_source_policy.source_mode,
        planning_as_of=datetime.now(UTC),
        target_scope=TradeTargetScope.BINDING,
        mandate_account_binding_ref_id=None,
        binding_key="binding-1",
        venue_account_ref_id=account_ref_id,
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        symbol="BTC",
        action=DecisionAction.REDUCE,
        side=OrderSide.SELL,
        desired_quantity=Decimal("0.01"),
        desired_notional=None,
        source_decision_ids=["decision-1"],
        source_evaluation_keys=["eval-1"],
        source_binding_keys=["binding-1"],
        status=MandateDesiredTradeStatus.APPROVED,
        provenance={},
        created_at=datetime.now(UTC),
        approved_at=datetime.now(UTC),
        rejected_at=None,
    )
    candidate = BindingRoutingCandidate(
        client_ref_id=None,
        strategy_mandate_ref_id=None,
        mandate_key="mandate-1",
        market_data_source_policy_ref_id=None,
        planning_source_venue=Venue.HYPERLIQUID.value,
        binding_ref_id=None,
        binding_key="binding-1",
        venue_account_ref_id=account_ref_id,
        venue_account_key="okx_child_intent",
        venue=Venue.OKX.value,
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        symbol="BTC",
        exchange_symbol="BTC-USDT-SWAP",
        strategy_eligible=True,
        trading_eligible=False,
        routing_eligible=False,
        account_connected=True,
        quote_available=False,
        available_balance_hint=None,
        venue_capabilities=asyncio.run(adapter.get_venue_capabilities()),
        account_connectivity=asyncio.run(adapter.get_account_connectivity()),
        quote_snapshot=None,
        eligibility_reasons=["venue_read_only_mode"],
    )

    intent = asyncio.run(execution.create_child_intent(desired_trade, candidate))
    preview = asyncio.run(execution.preview_child_intent(intent.intent_id))
    intents = asyncio.run(execution.list_child_intents(desired_trade_key="trade-1"))

    assert preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert preview.payload is not None
    assert intents[0].provenance["prepared_order_preview"]["preview_status"] == "preparable"
