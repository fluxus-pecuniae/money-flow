from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
import urllib.parse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    ProductType,
    StrategyFamily,
    SubmittedOrderRecoveryCategory,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Venue,
)
from core.domain.models import (
    Fill,
    SubmittedOrder,
    SubmittedOrderLifecycleUpdate,
    VenueAccountConnectivity,
    VenuePrivateOpenOrder,
)
from db.models import (
    ClientModel,
    InstrumentModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    StrategyMandateModel,
    SubmittedOrderLifecycleEventModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from services.execution.service import DefaultExecutionService, SubmittedOrderActionError
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.base import VenueAdapterError
from services.exchange.binance.adapter import BinanceExchangeAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.hyperliquid.signing import signer_address
from services.exchange.kraken.adapter import KrakenExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService
from tests.test_phase3_strategy import build_settings, build_test_session_factory
from tests.test_phase431_submission_truth import _generate_ec_private_key_pem
from tests.test_phase42_execution_readiness import _seed_intent
from tests.test_phase44_submission_lifecycle import (
    _aster_ambiguous_transport,
    _aster_rejected_transport,
    _build_execution_service as _build_aster_execution_service,
    _seed_hyperliquid_submitted_order,
)

HYPERLIQUID_TEST_PRIVATE_KEY = "0x1111111111111111111111111111111111111111111111111111111111111111"


def _seed_symbol(
    session_factory,
    *,
    venue: str,
    symbol: str,
    exchange_symbol: str,
    market_type: MarketType,
    product_type: ProductType,
    quote_asset: str,
    settlement_asset: str | None,
) -> str:
    with session_factory() as session:
        instrument = session.scalar(
            select(InstrumentModel).where(
                InstrumentModel.market_type == market_type,
                InstrumentModel.product_type == product_type,
                InstrumentModel.base_asset == symbol,
                InstrumentModel.quote_asset == quote_asset,
                InstrumentModel.settlement_asset == settlement_asset,
            )
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key=f"{market_type.value}:{product_type.value}:{symbol}:{quote_asset}:{settlement_asset or ''}",
                canonical_symbol=symbol,
                market_type=market_type,
                product_type=product_type,
                base_asset=symbol,
                quote_asset=quote_asset,
                settlement_asset=settlement_asset,
                is_active=True,
            )
            session.add(instrument)
            session.flush()

        venue_symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == instrument.id,
                SymbolModel.venue == venue,
                SymbolModel.exchange_symbol == exchange_symbol,
            )
        )
        if venue_symbol is None:
            session.add(
                SymbolModel(
                    instrument_ref_id=instrument.id,
                    venue=venue,
                    symbol=symbol,
                    exchange_symbol=exchange_symbol,
                    venue_asset_id=exchange_symbol,
                    asset_id=None,
                    market_type=market_type,
                    product_type=product_type,
                    base_asset=symbol,
                    quote_asset=quote_asset,
                    settlement_asset=settlement_asset,
                    price_tick_size=Decimal("0.1"),
                    quantity_step_size=Decimal("0.001"),
                    min_order_size=Decimal("0.001"),
                    size_decimals=3,
                    max_leverage=10,
                    only_isolated=False,
                    is_perpetual=market_type == MarketType.PERPETUAL,
                    is_builder_deployed=False,
                    is_strategy_eligible=True,
                    is_trading_eligible=True,
                    is_active=True,
                    raw_metadata={},
                )
            )
        session.commit()
        return instrument.id


def _submitted_order(
    *,
    venue: str,
    instrument_ref_id: str,
    symbol: str,
    exchange_order_id: str,
    quantity: str = "0.01",
) -> SubmittedOrder:
    now = datetime.now(UTC)
    return SubmittedOrder(
        submitted_order_id=f"subm-{venue}",
        instrument_key=f"test::{venue}::{symbol}",
        instrument_ref_id=instrument_ref_id,
        venue_account_ref_id=None,
        venue=venue,
        account_address=f"{venue}-acct",
        intent_id=f"intent-{venue}",
        client_order_id=f"client-{venue}",
        exchange_order_id=exchange_order_id,
        status=SubmittedOrderStatus.ACKNOWLEDGED,
        submitted_at=now,
        acknowledged_at=now,
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100000"),
        original_quantity=Decimal(quantity),
        remaining_quantity=Decimal(quantity),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        last_fill_at=None,
        status_reason_code=None,
        status_message=None,
        reason_codes=[],
        cancelable_in_principle=True,
        amendable_in_principle=True,
        reduce_only=False,
        raw_payload={},
    )


def _submitted_fill(
    *,
    submitted_order_id: str,
    exchange_order_id: str,
    venue: str,
    instrument_ref_id: str,
    symbol: str,
    quantity: str,
    price: str = "100000",
) -> Fill:
    return Fill(
        fill_id=f"fill-{venue}-{quantity}",
        instrument_key=f"test::{venue}::{symbol}",
        instrument_ref_id=instrument_ref_id,
        venue_account_ref_id=None,
        venue=venue,
        account_address=f"{venue}-acct",
        submitted_order_id=submitted_order_id,
        exchange_order_id=exchange_order_id,
        symbol=symbol,
        price=Decimal(price),
        quantity=Decimal(quantity),
        fee=Decimal("0"),
        filled_at=datetime.now(UTC),
    )


def _build_private_state_test_adapter(
    adapter_cls,
    *,
    venue: str,
    session_factory,
    transport=None,
    **settings_overrides,
):
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=venue,
        **settings_overrides,
    )
    kwargs = {"session_factory": session_factory}
    if transport is not None:
        kwargs["transport"] = transport
    if adapter_cls is HyperliquidExchangeAdapter:
        class _RuntimeContextStub:
            async def ensure_active_context(self):
                return SimpleNamespace(bindings=[])

        kwargs["runtime_context_service"] = _RuntimeContextStub()
    return adapter_cls(settings, **kwargs)


def _install_private_state_summary_stubs(adapter) -> None:
    async def _connectivity_stub() -> VenueAccountConnectivity:
        environment = getattr(adapter, "_integration_environment", adapter.settings.app.environment)
        account_model = getattr(adapter, "account_model", "wallet_address")
        return VenueAccountConnectivity(
            venue=adapter.integration.venue.value,
            environment=environment,
            support_level=adapter.support_level,
            account_model=account_model,
            account_identifier="stub-account",
            account_label=None,
            subaccount_label=None,
            credentials_ref=None,
            account_identifier_configured=True,
            credentials_configured=True,
            read_only_mode=adapter.integration.read_only_mode,
            dry_run_mode=adapter.integration.dry_run_mode,
            submission_enabled=adapter.integration.submission_enabled,
            submission_authorized=adapter.integration.submission_authorized,
            private_account_sync_enabled=True,
            account_snapshot_available=False,
            open_orders_query_available=adapter.supports_open_orders_query,
            open_positions_query_available=adapter.supports_open_positions_query,
            last_success_at=None,
            last_error=None,
        )

    async def _snapshot_stub():
        return None

    adapter.get_account_connectivity = _connectivity_stub
    adapter.read_account_snapshot = _snapshot_stub


def _submitted_order_account_ref(session_factory, submitted_order_id: str) -> str:
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        assert model.venue_account_ref_id is not None
        return model.venue_account_ref_id


def _submitted_order_submitted_at_ms(
    session_factory,
    submitted_order_id: str,
    *,
    offset_ms: int = 0,
) -> int:
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted_at = model.submitted_at
        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=UTC)
        else:
            submitted_at = submitted_at.astimezone(UTC)
        return int(submitted_at.timestamp() * 1000) + offset_ms


async def _aster_lifecycle_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/fapi/v1/order":
        return {
            "symbol": "BTCUSDT",
            "status": "PARTIALLY_FILLED",
            "origQty": "0.01",
            "executedQty": "0.004",
            "avgPrice": "100100",
            "updateTime": 1710000000000,
        }
    if method == "DELETE" and path == "/fapi/v1/order":
        return {"orderId": "aster-1", "status": "CANCELED"}
    raise AssertionError((method, path, params, body, headers))


async def _okx_lifecycle_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v5/trade/order":
        return {
            "code": "0",
            "data": [
                {
                    "state": "partially_filled",
                    "sz": "0.01",
                    "accFillSz": "0.004",
                    "avgPx": "100100",
                    "fillTime": "1710000000000",
                }
            ],
        }
    if method == "POST" and path == "/api/v5/trade/cancel-order":
        return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
    raise AssertionError((method, path, params, body, headers))


async def _coinbase_lifecycle_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v3/brokerage/orders/historical/cb-1":
        return {
            "order": {
                "order_id": "cb-1",
                "status": "OPEN",
                "filled_size": "0.004",
                "average_filled_price": "100100",
                "order_configuration": {
                    "limit_limit_gtc": {
                        "base_size": "0.01",
                        "limit_price": "100000",
                    }
                },
            }
        }
    if method == "POST" and path == "/api/v3/brokerage/orders/batch_cancel":
        return {"results": [{"success": True}]}
    raise AssertionError((method, path, params, body, headers))


async def _binance_lifecycle_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v3/order":
        return {
            "status": "PARTIALLY_FILLED",
            "origQty": "0.01",
            "executedQty": "0.004",
            "cummulativeQuoteQty": "400.4",
            "updateTime": 1710000000000,
        }
    if method == "DELETE" and path == "/api/v3/order":
        return {"orderId": "binance-1", "status": "CANCELED"}
    raise AssertionError((method, path, params, body, headers))


async def _kraken_lifecycle_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "POST" and path == "/0/private/QueryOrders":
        return {
            "error": [],
            "result": {
                "krk-1": {
                    "status": "open",
                    "vol": "0.01",
                    "vol_exec": "0.004",
                    "price": "100100",
                }
            },
        }
    if method == "POST" and path == "/0/private/CancelOrder":
        return {"error": [], "result": {"count": 1}}
    raise AssertionError((method, path, params, body, headers))


def test_fill_merge_preserves_canceled_status_with_partial_fills() -> None:
    session_factory = build_test_session_factory()
    execution = DefaultExecutionService(build_settings(), session_factory=session_factory)
    current = _submitted_order(
        venue=Venue.ASTER.value,
        instrument_ref_id="inst-1",
        symbol="BTC",
        exchange_order_id="aster-merge-canceled",
    )
    update = SubmittedOrderLifecycleUpdate(
        submitted_order_id=current.submitted_order_id,
        venue=current.venue,
        venue_account_ref_id=current.venue_account_ref_id,
        exchange_order_id=current.exchange_order_id,
        status=SubmittedOrderStatus.CANCELED,
        reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
        event_type="reconciliation_canceled",
        status_reason_code="reconciliation_canceled",
        status_message="Venue reports the order as canceled.",
        reason_codes=["reconciliation_canceled"],
        cancelable_in_principle=False,
        amendable_in_principle=False,
        observed_at=datetime.now(UTC),
    )

    merged = execution._merge_lifecycle_update_with_fills(
        current=current,
        update=update,
        fills=[
            _submitted_fill(
                submitted_order_id=current.submitted_order_id,
                exchange_order_id=current.exchange_order_id or "aster-merge-canceled",
                venue=current.venue,
                instrument_ref_id="inst-1",
                symbol="BTC",
                quantity="0.004",
            )
        ],
    )

    assert merged.status == SubmittedOrderStatus.CANCELED
    assert merged.status_reason_code == "reconciliation_canceled"
    assert merged.filled_quantity == Decimal("0.004")
    assert merged.remaining_quantity == Decimal("0.006")
    assert merged.cancelable_in_principle is False
    assert merged.amendable_in_principle is False


def test_fill_merge_preserves_expired_status_with_partial_fills() -> None:
    session_factory = build_test_session_factory()
    execution = DefaultExecutionService(build_settings(), session_factory=session_factory)
    current = _submitted_order(
        venue=Venue.BINANCE.value,
        instrument_ref_id="inst-1",
        symbol="BTC",
        exchange_order_id="binance-merge-expired",
    )
    update = SubmittedOrderLifecycleUpdate(
        submitted_order_id=current.submitted_order_id,
        venue=current.venue,
        venue_account_ref_id=current.venue_account_ref_id,
        exchange_order_id=current.exchange_order_id,
        status=SubmittedOrderStatus.EXPIRED,
        reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
        event_type="reconciliation_expired",
        status_reason_code="reconciliation_expired",
        status_message="Venue reports the order as expired.",
        reason_codes=["reconciliation_expired"],
        cancelable_in_principle=False,
        amendable_in_principle=False,
        observed_at=datetime.now(UTC),
    )

    merged = execution._merge_lifecycle_update_with_fills(
        current=current,
        update=update,
        fills=[
            _submitted_fill(
                submitted_order_id=current.submitted_order_id,
                exchange_order_id=current.exchange_order_id or "binance-merge-expired",
                venue=current.venue,
                instrument_ref_id="inst-1",
                symbol="BTC",
                quantity="0.004",
            )
        ],
    )

    assert merged.status == SubmittedOrderStatus.EXPIRED
    assert merged.status_reason_code == "reconciliation_expired"
    assert merged.filled_quantity == Decimal("0.004")
    assert merged.remaining_quantity == Decimal("0.006")
    assert merged.cancelable_in_principle is False
    assert merged.amendable_in_principle is False


def test_fill_merge_promotes_terminal_update_to_filled_only_when_full_completion_is_proven() -> None:
    session_factory = build_test_session_factory()
    execution = DefaultExecutionService(build_settings(), session_factory=session_factory)
    current = _submitted_order(
        venue=Venue.OKX.value,
        instrument_ref_id="inst-1",
        symbol="BTC",
        exchange_order_id="okx-merge-complete",
    )
    update = SubmittedOrderLifecycleUpdate(
        submitted_order_id=current.submitted_order_id,
        venue=current.venue,
        venue_account_ref_id=current.venue_account_ref_id,
        exchange_order_id=current.exchange_order_id,
        status=SubmittedOrderStatus.CANCELED,
        reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
        event_type="reconciliation_canceled",
        status_reason_code="reconciliation_canceled",
        status_message="Venue reports the order as canceled.",
        reason_codes=["reconciliation_canceled"],
        cancelable_in_principle=False,
        amendable_in_principle=False,
        observed_at=datetime.now(UTC),
    )

    merged = execution._merge_lifecycle_update_with_fills(
        current=current,
        update=update,
        fills=[
            _submitted_fill(
                submitted_order_id=current.submitted_order_id,
                exchange_order_id=current.exchange_order_id or "okx-merge-complete",
                venue=current.venue,
                instrument_ref_id="inst-1",
                symbol="BTC",
                quantity="0.01",
            )
        ],
    )

    assert merged.status == SubmittedOrderStatus.FILLED
    assert merged.status_reason_code == "reconciliation_completed_fill"
    assert merged.filled_quantity == Decimal("0.01")
    assert merged.remaining_quantity == Decimal("0")
    assert merged.cancelable_in_principle is False
    assert merged.amendable_in_principle is False


@pytest.mark.parametrize(
    ("venue", "adapter_cls", "overrides", "expected_cancel", "expected_amend"),
    [
        (
            Venue.ASTER.value,
            AsterExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXCHANGE_VENUE": Venue.ASTER.value,
                "ASTER_ENABLED": True,
                "ASTER_ACCOUNT_IDENTIFIER": "aster-main",
                "ASTER_API_KEY": "aster-key",
                "ASTER_API_SECRET": "aster-secret",
            },
            True,
            False,
        ),
        (
            Venue.BINANCE.value,
            BinanceExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXCHANGE_VENUE": Venue.BINANCE.value,
                "BINANCE_ENABLED": True,
                "BINANCE_ACCOUNT_IDENTIFIER": "binance-main",
                "BINANCE_API_KEY": "binance-key",
                "BINANCE_API_SECRET": "binance-secret",
            },
            True,
            False,
        ),
        (
            Venue.KRAKEN.value,
            KrakenExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXCHANGE_VENUE": Venue.KRAKEN.value,
                "KRAKEN_ENABLED": True,
                "KRAKEN_ACCOUNT_IDENTIFIER": "kraken-main",
                "KRAKEN_API_KEY": "kraken-key",
                "KRAKEN_API_SECRET": "a3Jha2VuLXNlY3JldA==",
            },
            True,
            True,
        ),
        (
            Venue.OKX.value,
            OkxExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXCHANGE_VENUE": Venue.OKX.value,
                "OKX_ENABLED": True,
                "OKX_ACCOUNT_IDENTIFIER": "okx-main",
                "OKX_API_KEY": "okx-key",
                "OKX_API_SECRET": "okx-secret",
                "OKX_API_PASSPHRASE": "okx-pass",
            },
            True,
            True,
        ),
        (
            Venue.COINBASE_ADVANCED_TRADE.value,
            CoinbaseAdvancedTradeExchangeAdapter,
            {
                "APP_ENV": Environment.TESTNET,
                "EXCHANGE_VENUE": Venue.COINBASE_ADVANCED_TRADE.value,
                "COINBASE_ADVANCED_ENABLED": True,
                "COINBASE_ADVANCED_ACCOUNT_IDENTIFIER": "cb-main",
                "COINBASE_ADVANCED_JWT_KEY_NAME": "organizations/test/apiKeys/key",
                "COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM": _generate_ec_private_key_pem(),
            },
            True,
            True,
        ),
    ],
)
def test_capability_surfaces_split_cancel_from_amend_truth(
    venue: str,
    adapter_cls,
    overrides: dict[str, object],
    expected_cancel: bool,
    expected_amend: bool,
) -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(**overrides)
    adapter = adapter_cls(settings, session_factory=session_factory)

    capabilities = asyncio.run(adapter.get_venue_capabilities())

    assert capabilities.venue.value == venue
    assert capabilities.supports_order_cancel is expected_cancel
    assert capabilities.adapter_supports_order_cancel is expected_cancel
    assert capabilities.supports_order_amend is expected_amend
    assert capabilities.adapter_supports_order_amend is expected_amend


def test_hyperliquid_status_and_capabilities_reflect_current_cancel_and_amend_truth() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.HYPERLIQUID.value,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0x1234",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    class _RuntimeContextStub:
        async def ensure_active_context(self):
            return SimpleNamespace(bindings=[])

    adapter = HyperliquidExchangeAdapter(
        settings,
        session_factory=session_factory,
        runtime_context_service=_RuntimeContextStub(),
    )

    capabilities = asyncio.run(adapter.get_venue_capabilities())
    status = asyncio.run(adapter.get_exchange_status())

    assert capabilities.supports_order_cancel is True
    assert capabilities.supports_order_amend is True
    assert capabilities.adapter_supports_order_cancel is True
    assert capabilities.adapter_supports_order_amend is True
    assert status.adapter_supports_order_cancel is True
    assert status.adapter_supports_order_amend is True


async def _aster_open_orders_empty_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/fapi/v1/openOrders":
        return []
    raise AssertionError((method, path, params, body, headers))


async def _binance_open_orders_empty_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v3/openOrders":
        return []
    raise AssertionError((method, path, params, body, headers))


async def _okx_private_state_empty_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v5/trade/orders-pending":
        return {"code": "0", "data": []}
    if method == "GET" and path == "/api/v5/trade/fills":
        return {"code": "0", "data": []}
    raise AssertionError((method, path, params, body, headers))


async def _coinbase_private_state_empty_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/api/v3/brokerage/orders/historical/batch":
        return {"orders": []}
    if method == "GET" and path == "/api/v3/brokerage/orders/historical/fills":
        return {"fills": []}
    raise AssertionError((method, path, params, body, headers))


async def _kraken_private_state_empty_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "POST" and path == "/0/private/OpenOrders":
        return {"error": [], "result": {"open": {}}}
    if method == "POST" and path == "/0/private/TradesHistory":
        return {"error": [], "result": {"trades": {}}}
    raise AssertionError((method, path, params, body, headers))


async def _hyperliquid_empty_user_fills_transport(payload):
    assert payload["type"] in {"userFills", "frontendOpenOrders", "clearinghouseState"}
    if payload["type"] == "clearinghouseState":
        return {"time": 1710000000000, "assetPositions": []}
    return []


@pytest.mark.parametrize(
    (
        "venue",
        "adapter_cls",
        "overrides",
        "expected_semantic_streams",
    ),
    [
        (
            Venue.HYPERLIQUID.value,
            HyperliquidExchangeAdapter,
            {
                "HYPERLIQUID_ENABLED": True,
                "EXCHANGE_ACCOUNT_ADDRESS": "",
            },
            False,
        ),
        (Venue.ASTER.value, AsterExchangeAdapter, {"ASTER_ENABLED": True}, True),
        (Venue.OKX.value, OkxExchangeAdapter, {"OKX_ENABLED": True}, True),
        (
            Venue.COINBASE_ADVANCED_TRADE.value,
            CoinbaseAdvancedTradeExchangeAdapter,
            {"COINBASE_ADVANCED_ENABLED": True},
            True,
        ),
        (Venue.BINANCE.value, BinanceExchangeAdapter, {"BINANCE_ENABLED": True}, True),
        (Venue.KRAKEN.value, KrakenExchangeAdapter, {"KRAKEN_ENABLED": True}, True),
    ],
)
def test_private_state_summary_reports_runtime_persistence_when_direct_query_is_not_used(
    venue: str,
    adapter_cls,
    overrides: dict[str, object],
    expected_semantic_streams: bool,
) -> None:
    session_factory = build_test_session_factory()
    adapter = _build_private_state_test_adapter(
        adapter_cls,
        venue=venue,
        session_factory=session_factory,
        **overrides,
    )

    capabilities = asyncio.run(adapter.get_venue_capabilities())
    status = asyncio.run(adapter.get_exchange_status())
    summary = asyncio.run(adapter.get_private_state_summary())

    assert capabilities.supports_user_streams is expected_semantic_streams
    assert capabilities.adapter_supports_user_streams is False
    assert capabilities.private_lifecycle_update_mode == "polling"
    assert status.adapter_supports_user_streams is False
    assert status.private_lifecycle_update_mode == "polling"
    assert summary.adapter_supports_user_streams is False
    assert summary.private_lifecycle_update_mode == "polling"
    assert summary.open_orders_source == "persistence"
    assert summary.recent_fills_source == "persistence"
    assert summary.open_positions_source == "persistence"
    assert summary.open_orders_query_available is True
    assert summary.recent_fills_query_available is True


@pytest.mark.parametrize(
    ("venue", "adapter_cls", "overrides", "transport"),
    [
        (
            Venue.ASTER.value,
            AsterExchangeAdapter,
            {
                "ASTER_ENABLED": True,
                "ASTER_ACCOUNT_IDENTIFIER": "aster-main",
                "ASTER_API_KEY": "aster-key",
                "ASTER_API_SECRET": "aster-secret",
            },
            _aster_open_orders_empty_transport,
        ),
        (
            Venue.BINANCE.value,
            BinanceExchangeAdapter,
            {
                "BINANCE_ENABLED": True,
                "BINANCE_ACCOUNT_IDENTIFIER": "binance-main",
                "BINANCE_API_KEY": "binance-key",
                "BINANCE_API_SECRET": "binance-secret",
            },
            _binance_open_orders_empty_transport,
        ),
        (
            Venue.OKX.value,
            OkxExchangeAdapter,
            {
                "OKX_ENABLED": True,
                "OKX_ACCOUNT_IDENTIFIER": "okx-main",
                "OKX_API_KEY": "okx-key",
                "OKX_API_SECRET": "okx-secret",
                "OKX_API_PASSPHRASE": "okx-pass",
            },
            _okx_private_state_empty_transport,
        ),
        (
            Venue.COINBASE_ADVANCED_TRADE.value,
            CoinbaseAdvancedTradeExchangeAdapter,
            {
                "COINBASE_ADVANCED_ENABLED": True,
                "COINBASE_ADVANCED_ACCOUNT_IDENTIFIER": "coinbase-main",
                "COINBASE_ADVANCED_JWT_KEY_NAME": "organizations/test/apiKeys/test",
                "COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM": _generate_ec_private_key_pem(),
            },
            _coinbase_private_state_empty_transport,
        ),
        (
            Venue.KRAKEN.value,
            KrakenExchangeAdapter,
            {
                "KRAKEN_ENABLED": True,
                "KRAKEN_ACCOUNT_IDENTIFIER": "kraken-main",
                "KRAKEN_API_KEY": "kraken-key",
                "KRAKEN_API_SECRET": "a3Jha2VuLXNlY3JldA==",
            },
            _kraken_private_state_empty_transport,
        ),
        (
            Venue.HYPERLIQUID.value,
            HyperliquidExchangeAdapter,
            {
                "HYPERLIQUID_ENABLED": True,
                "EXCHANGE_ACCOUNT_ADDRESS": "0x1111111111111111111111111111111111111111",
            },
            _hyperliquid_empty_user_fills_transport,
        ),
    ],
)
def test_private_state_summary_reports_venue_query_for_open_orders_when_auth_and_query_path_exist(
    venue: str,
    adapter_cls,
    overrides: dict[str, object],
    transport,
) -> None:
    session_factory = build_test_session_factory()
    adapter = _build_private_state_test_adapter(
        adapter_cls,
        venue=venue,
        session_factory=session_factory,
        transport=transport,
        **overrides,
    )
    _install_private_state_summary_stubs(adapter)

    summary = asyncio.run(adapter.get_private_state_summary())

    assert summary.open_orders_source == "venue_query"
    assert summary.open_orders_query_available is True


@pytest.mark.parametrize(
    ("venue", "adapter_cls", "overrides", "transport"),
    [
        (
            Venue.HYPERLIQUID.value,
            HyperliquidExchangeAdapter,
            {
                "HYPERLIQUID_ENABLED": True,
                "EXCHANGE_ACCOUNT_ADDRESS": "0x1111111111111111111111111111111111111111",
            },
            _hyperliquid_empty_user_fills_transport,
        ),
        (
            Venue.OKX.value,
            OkxExchangeAdapter,
            {
                "OKX_ENABLED": True,
                "OKX_ACCOUNT_IDENTIFIER": "okx-main",
                "OKX_API_KEY": "okx-key",
                "OKX_API_SECRET": "okx-secret",
                "OKX_API_PASSPHRASE": "okx-pass",
            },
            _okx_private_state_empty_transport,
        ),
        (
            Venue.COINBASE_ADVANCED_TRADE.value,
            CoinbaseAdvancedTradeExchangeAdapter,
            {
                "COINBASE_ADVANCED_ENABLED": True,
                "COINBASE_ADVANCED_ACCOUNT_IDENTIFIER": "coinbase-main",
                "COINBASE_ADVANCED_JWT_KEY_NAME": "organizations/test/apiKeys/test",
                "COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM": _generate_ec_private_key_pem(),
            },
            _coinbase_private_state_empty_transport,
        ),
        (
            Venue.KRAKEN.value,
            KrakenExchangeAdapter,
            {
                "KRAKEN_ENABLED": True,
                "KRAKEN_ACCOUNT_IDENTIFIER": "kraken-main",
                "KRAKEN_API_KEY": "kraken-key",
                "KRAKEN_API_SECRET": "a3Jha2VuLXNlY3JldA==",
            },
            _kraken_private_state_empty_transport,
        ),
    ],
)
def test_private_state_summary_reports_venue_query_for_recent_fills_when_auth_and_query_path_exist(
    venue: str,
    adapter_cls,
    overrides: dict[str, object],
    transport,
) -> None:
    session_factory = build_test_session_factory()
    adapter = _build_private_state_test_adapter(
        adapter_cls,
        venue=venue,
        session_factory=session_factory,
        transport=transport,
        **overrides,
    )
    if venue != Venue.HYPERLIQUID.value:
        _install_private_state_summary_stubs(adapter)

    summary = asyncio.run(adapter.get_private_state_summary())

    assert summary.recent_fills_source == "venue_query"
    assert summary.recent_fills_query_available is True


def test_private_open_orders_use_distinct_model_and_optional_submitted_order_linkage() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(session_factory, suffix="private-link")
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)
    with session_factory() as session:
        account = session.scalar(
            select(VenueAccountModel).where(VenueAccountModel.id == venue_account_ref_id)
        )
        assert account is not None
        account.raw_metadata = {}
        session.commit()
    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        BINANCE_ENABLED=True,
    )

    orders = asyncio.run(adapter.fetch_open_orders(venue_account_ref_id=venue_account_ref_id))

    assert len(orders) == 1
    order = orders[0]
    assert isinstance(order, VenuePrivateOpenOrder)
    assert not hasattr(order, "submitted_order_id")
    assert order.linked_submitted_order_id == submitted_order_id
    assert order.exchange_order_id == "binance-order-private-link"


@pytest.mark.parametrize(
    ("venue", "adapter_cls", "settings_overrides", "transport", "exchange_symbol", "market_type", "product_type", "quote_asset", "settlement_asset", "exchange_order_id"),
    [
        (
            Venue.ASTER.value,
            AsterExchangeAdapter,
            {
                "ASTER_ENABLED": True,
                "ASTER_READ_ONLY_MODE": False,
                "ASTER_DRY_RUN_MODE": False,
                "ASTER_SUBMISSION_ENABLED": True,
                "ASTER_SUBMISSION_AUTHORIZED": True,
                "ASTER_ACCOUNT_IDENTIFIER": "aster-main",
                "ASTER_API_KEY": "aster-key",
                "ASTER_API_SECRET": "aster-secret",
            },
            _aster_lifecycle_transport,
            "BTCUSDT",
            MarketType.PERPETUAL,
            ProductType.LINEAR,
            "USDT",
            "USDT",
            "aster-1",
        ),
        (
            Venue.OKX.value,
            OkxExchangeAdapter,
            {
                "OKX_ENABLED": True,
                "OKX_READ_ONLY_MODE": False,
                "OKX_DRY_RUN_MODE": False,
                "OKX_SUBMISSION_ENABLED": True,
                "OKX_SUBMISSION_AUTHORIZED": True,
                "OKX_ACCOUNT_IDENTIFIER": "okx-main",
                "OKX_API_KEY": "okx-key",
                "OKX_API_SECRET": "okx-secret",
                "OKX_API_PASSPHRASE": "okx-pass",
            },
            _okx_lifecycle_transport,
            "BTC-USDT-SWAP",
            MarketType.PERPETUAL,
            ProductType.LINEAR,
            "USDT",
            "USDT",
            "okx-1",
        ),
        (
            Venue.COINBASE_ADVANCED_TRADE.value,
            CoinbaseAdvancedTradeExchangeAdapter,
            {
                "COINBASE_ADVANCED_ENABLED": True,
                "COINBASE_ADVANCED_READ_ONLY_MODE": False,
                "COINBASE_ADVANCED_DRY_RUN_MODE": False,
                "COINBASE_ADVANCED_SUBMISSION_ENABLED": True,
                "COINBASE_ADVANCED_SUBMISSION_AUTHORIZED": True,
                "COINBASE_ADVANCED_ACCOUNT_IDENTIFIER": "cb-main",
                "COINBASE_ADVANCED_JWT_KEY_NAME": "organizations/test/apiKeys/key",
                "COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM": _generate_ec_private_key_pem(),
            },
            _coinbase_lifecycle_transport,
            "BTC-USD",
            MarketType.SPOT,
            ProductType.SPOT,
            "USD",
            None,
            "cb-1",
        ),
        (
            Venue.BINANCE.value,
            BinanceExchangeAdapter,
            {
                "BINANCE_ENABLED": True,
                "BINANCE_READ_ONLY_MODE": False,
                "BINANCE_DRY_RUN_MODE": False,
                "BINANCE_SUBMISSION_ENABLED": True,
                "BINANCE_SUBMISSION_AUTHORIZED": True,
                "BINANCE_ACCOUNT_IDENTIFIER": "binance-main",
                "BINANCE_API_KEY": "binance-key",
                "BINANCE_API_SECRET": "binance-secret",
            },
            _binance_lifecycle_transport,
            "BTCUSDT",
            MarketType.SPOT,
            ProductType.SPOT,
            "USDT",
            None,
            "binance-1",
        ),
        (
            Venue.KRAKEN.value,
            KrakenExchangeAdapter,
            {
                "KRAKEN_ENABLED": True,
                "KRAKEN_READ_ONLY_MODE": False,
                "KRAKEN_DRY_RUN_MODE": False,
                "KRAKEN_SUBMISSION_ENABLED": True,
                "KRAKEN_SUBMISSION_AUTHORIZED": True,
                "KRAKEN_ACCOUNT_IDENTIFIER": "kraken-main",
                "KRAKEN_API_KEY": "kraken-key",
                "KRAKEN_API_SECRET": "a3Jha2VuLXNlY3JldA==",
            },
            _kraken_lifecycle_transport,
            "XBT/USD",
            MarketType.SPOT,
            ProductType.SPOT,
            "USD",
            None,
            "krk-1",
        ),
    ],
)
def test_venue_reconciliation_depth_is_available_beyond_hyperliquid(
    venue,
    adapter_cls,
    settings_overrides,
    transport,
    exchange_symbol,
    market_type,
    product_type,
    quote_asset,
    settlement_asset,
    exchange_order_id,
) -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id = _seed_symbol(
        session_factory,
        venue=venue,
        symbol="BTC",
        exchange_symbol=exchange_symbol,
        market_type=market_type,
        product_type=product_type,
        quote_asset=quote_asset,
        settlement_asset=settlement_asset,
    )
    settings = build_settings(APP_ENV=Environment.TESTNET, EXCHANGE_VENUE=venue, **settings_overrides)
    adapter = adapter_cls(settings, transport=transport, session_factory=session_factory)

    update = asyncio.run(
        adapter.reconcile_submitted_order(
            _submitted_order(
                venue=venue,
                instrument_ref_id=instrument_ref_id,
                symbol="BTC",
                exchange_order_id=exchange_order_id,
            )
        )
    )

    assert update.status == SubmittedOrderStatus.PARTIALLY_FILLED
    assert update.reconciliation_status.value == "reconciled"
    assert update.status_reason_code == "reconciliation_partial_fill"
    assert update.remaining_quantity == Decimal("0.006")


def _seed_okx_submitted_order(
    session_factory,
    *,
    suffix: str,
    api_key: str,
) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-okx"))
        if client is None:
            client = ClientModel(client_key="client-okx", display_name="Client OKX", is_active=True)
            session.add(client)
            session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::okx::{suffix}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()
        account = VenueAccountModel(
            venue_account_key=f"okx-acct-{suffix}",
            client_ref_id=client.id,
            venue=Venue.OKX.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"okx-native-{suffix}",
            account_address=f"okx-acct-{suffix}",
            account_label=f"label-{suffix}",
            subaccount_label=f"sub-{suffix}",
            credentials_ref=f"secret://{suffix}",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={
                "auth": {
                    "api_key": api_key,
                    "api_secret": f"secret-{suffix}",
                    "api_passphrase": f"pass-{suffix}",
                }
            },
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
        instrument = session.scalar(
            select(InstrumentModel).where(
                InstrumentModel.market_type == MarketType.PERPETUAL,
                InstrumentModel.product_type == ProductType.LINEAR,
                InstrumentModel.base_asset == "BTC",
                InstrumentModel.quote_asset == "USDT",
                InstrumentModel.settlement_asset == "USDT",
            )
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key="perpetual:linear:BTC:USDT:USDT",
                canonical_symbol="BTC",
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset="BTC",
                quote_asset="USDT",
                settlement_asset="USDT",
                is_active=True,
            )
            session.add(instrument)
            session.flush()

        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == instrument.id,
                SymbolModel.venue == Venue.OKX.value,
                SymbolModel.exchange_symbol == "BTC-USDT-SWAP",
            )
        )
        if symbol is None:
            symbol = SymbolModel(
                instrument_ref_id=instrument.id,
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
                max_leverage=10,
                only_isolated=False,
                is_perpetual=True,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
            session.add(symbol)
            session.flush()
        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id=f"intent-okx-{suffix}",
            decision_id=f"decision-okx-{suffix}",
            action=None,
            mandate_desired_trade_ref_id=None,
            desired_trade_key=f"trade-okx-{suffix}",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=binding.id,
            binding_key=binding.binding_key,
            venue_account_ref_id=account.id,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol.id,
            symbol="BTC",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.01"),
            limit_price=Decimal("100000"),
            reduce_only=False,
            ttl_seconds=30,
            status=OrderIntentStatus.SUBMITTED,
            idempotency_key=f"idem-okx-{suffix}",
            provenance={},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.flush()
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id=f"subm-okx-{suffix}",
                intent_id=intent.intent_id,
                client_order_id=f"cl-okx-{suffix}",
                venue_account_ref_id=account.id,
                venue=Venue.OKX.value,
                account_address=account.account_address,
                instrument_ref_id=instrument.id,
                symbol_id=symbol.id,
                symbol="BTC",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                limit_price=Decimal("100000"),
                original_quantity=Decimal("0.01"),
                remaining_quantity=Decimal("0.01"),
                reduce_only=False,
                exchange_order_id=f"okx-order-{suffix}",
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
                submitted_at=datetime.now(UTC),
                acknowledged_at=datetime.now(UTC),
                filled_quantity=Decimal("0"),
                average_fill_price=None,
                last_fill_at=None,
                last_reconciled_at=None,
                status_reason_code=None,
                status_message=None,
                reason_codes=[],
                cancelable_in_principle=True,
                amendable_in_principle=True,
                raw_payload={"seeded": True},
            )
        )
        session.commit()
    return f"subm-okx-{suffix}"


def _seed_coinbase_submitted_order(
    session_factory,
    *,
    suffix: str = "a",
) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-coinbase"))
        if client is None:
            client = ClientModel(client_key="client-coinbase", display_name="Client Coinbase", is_active=True)
            session.add(client)
            session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::coinbase::{suffix}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()
        account = VenueAccountModel(
            venue_account_key=f"coinbase-acct-{suffix}",
            client_ref_id=client.id,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"cb-native-{suffix}",
            account_address=f"cb-account-{suffix}",
            account_label=f"coinbase-{suffix}",
            subaccount_label=None,
            credentials_ref=f"secret://cb-{suffix}",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={
                "auth": {
                    "jwt_key_name": f"organizations/test/apiKeys/cb-{suffix}",
                    "jwt_private_key_pem": _generate_ec_private_key_pem(),
                }
            },
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
        instrument = session.scalar(
            select(InstrumentModel).where(
                InstrumentModel.market_type == MarketType.SPOT,
                InstrumentModel.product_type == ProductType.SPOT,
                InstrumentModel.base_asset == "BTC",
                InstrumentModel.quote_asset == "USD",
                InstrumentModel.settlement_asset.is_(None),
            )
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key="spot:spot:BTC:USD:",
                canonical_symbol="BTC",
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset="BTC",
                quote_asset="USD",
                settlement_asset=None,
                is_active=True,
            )
            session.add(instrument)
            session.flush()

        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == instrument.id,
                SymbolModel.venue == Venue.COINBASE_ADVANCED_TRADE.value,
                SymbolModel.exchange_symbol == "BTC-USD",
            )
        )
        if symbol is None:
            symbol = SymbolModel(
                instrument_ref_id=instrument.id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
                symbol="BTC",
                exchange_symbol="BTC-USD",
                venue_asset_id="BTC-USD",
                asset_id=None,
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset="BTC",
                quote_asset="USD",
                settlement_asset=None,
                price_tick_size=Decimal("0.01"),
                quantity_step_size=Decimal("0.00000001"),
                min_order_size=Decimal("0.0001"),
                size_decimals=8,
                max_leverage=None,
                only_isolated=False,
                is_perpetual=False,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
            session.add(symbol)
            session.flush()
        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id=f"intent-cb-{suffix}",
            decision_id=f"decision-cb-{suffix}",
            action=None,
            mandate_desired_trade_ref_id=None,
            desired_trade_key=f"trade-cb-{suffix}",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=binding.id,
            binding_key=binding.binding_key,
            venue_account_ref_id=account.id,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol.id,
            symbol="BTC",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.01"),
            limit_price=Decimal("100000"),
            reduce_only=False,
            ttl_seconds=30,
            status=OrderIntentStatus.SUBMITTED,
            idempotency_key=f"idem-cb-{suffix}",
            provenance={},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.flush()
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id=f"subm-cb-{suffix}",
                intent_id=intent.intent_id,
                client_order_id=f"cl-cb-{suffix}",
                venue_account_ref_id=account.id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
                account_address=account.account_address,
                instrument_ref_id=instrument.id,
                symbol_id=symbol.id,
                symbol="BTC",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                limit_price=Decimal("100000"),
                original_quantity=Decimal("0.01"),
                remaining_quantity=Decimal("0.01"),
                reduce_only=False,
                exchange_order_id=f"cb-order-{suffix}",
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
                submitted_at=datetime.now(UTC),
                acknowledged_at=datetime.now(UTC),
                filled_quantity=Decimal("0"),
                average_fill_price=None,
                last_fill_at=None,
                last_reconciled_at=None,
                status_reason_code=None,
                status_message=None,
                reason_codes=[],
                cancelable_in_principle=True,
                amendable_in_principle=True,
                raw_payload={"seeded": True},
            )
        )
        session.commit()
    return f"subm-cb-{suffix}"


def _seed_aster_submitted_order(
    session_factory,
    *,
    suffix: str = "a",
    api_key: str = "aster-key",
) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-aster"))
        if client is None:
            client = ClientModel(client_key="client-aster", display_name="Client Aster", is_active=True)
            session.add(client)
            session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::aster::{suffix}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()
        account = VenueAccountModel(
            venue_account_key=f"aster-acct-{suffix}",
            client_ref_id=client.id,
            venue=Venue.ASTER.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"aster-native-{suffix}",
            account_address=f"aster-account-{suffix}",
            account_label=f"aster-{suffix}",
            subaccount_label=None,
            credentials_ref=f"secret://aster-{suffix}",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={"auth": {"api_key": api_key, "api_secret": f"{api_key}-secret"}},
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
        instrument = session.scalar(
            select(InstrumentModel).where(
                InstrumentModel.market_type == MarketType.PERPETUAL,
                InstrumentModel.product_type == ProductType.LINEAR,
                InstrumentModel.base_asset == "BTC",
                InstrumentModel.quote_asset == "USDT",
                InstrumentModel.settlement_asset == "USDT",
            )
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key="perpetual:linear:BTC:USDT:USDT",
                canonical_symbol="BTC",
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset="BTC",
                quote_asset="USDT",
                settlement_asset="USDT",
                is_active=True,
            )
            session.add(instrument)
            session.flush()
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == instrument.id,
                SymbolModel.venue == Venue.ASTER.value,
                SymbolModel.exchange_symbol == "BTCUSDT",
            )
        )
        if symbol is None:
            symbol = SymbolModel(
                instrument_ref_id=instrument.id,
                venue=Venue.ASTER.value,
                symbol="BTC",
                exchange_symbol="BTCUSDT",
                venue_asset_id="BTCUSDT",
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
                max_leverage=10,
                only_isolated=False,
                is_perpetual=True,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
            session.add(symbol)
            session.flush()
        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id=f"intent-aster-{suffix}",
            decision_id=f"decision-aster-{suffix}",
            action=None,
            mandate_desired_trade_ref_id=None,
            desired_trade_key=f"trade-aster-{suffix}",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=binding.id,
            binding_key=binding.binding_key,
            venue_account_ref_id=account.id,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol.id,
            symbol="BTC",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.01"),
            limit_price=Decimal("100000"),
            reduce_only=False,
            ttl_seconds=30,
            status=OrderIntentStatus.SUBMITTED,
            idempotency_key=f"idem-aster-{suffix}",
            provenance={},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.flush()
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id=f"subm-aster-{suffix}",
                intent_id=intent.intent_id,
                client_order_id=f"cl-aster-{suffix}",
                venue_account_ref_id=account.id,
                venue=Venue.ASTER.value,
                account_address=account.account_address,
                instrument_ref_id=instrument.id,
                symbol_id=symbol.id,
                symbol="BTC",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                limit_price=Decimal("100000"),
                original_quantity=Decimal("0.01"),
                remaining_quantity=Decimal("0.01"),
                reduce_only=False,
                exchange_order_id=f"aster-order-{suffix}",
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
                submitted_at=datetime.now(UTC),
                acknowledged_at=datetime.now(UTC),
                filled_quantity=Decimal("0"),
                average_fill_price=None,
                last_fill_at=None,
                last_reconciled_at=None,
                status_reason_code=None,
                status_message=None,
                reason_codes=[],
                cancelable_in_principle=True,
                amendable_in_principle=True,
                raw_payload={"seeded": True},
            )
        )
        session.commit()
    return f"subm-aster-{suffix}"


def _seed_binance_submitted_order(
    session_factory,
    *,
    suffix: str = "a",
    api_key: str = "binance-key",
) -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "client-binance"))
        if client is None:
            client = ClientModel(client_key="client-binance", display_name="Client Binance", is_active=True)
            session.add(client)
            session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key=f"money_flow::binance::{suffix}",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata={},
        )
        session.add(mandate)
        session.flush()
        account = VenueAccountModel(
            venue_account_key=f"binance-acct-{suffix}",
            client_ref_id=client.id,
            venue=Venue.BINANCE.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"binance-native-{suffix}",
            account_address=f"binance-account-{suffix}",
            account_label=f"binance-{suffix}",
            subaccount_label=None,
            credentials_ref=f"secret://binance-{suffix}",
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={"auth": {"api_key": api_key, "api_secret": f"{api_key}-secret"}},
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
        instrument = session.scalar(
            select(InstrumentModel).where(
                InstrumentModel.market_type == MarketType.SPOT,
                InstrumentModel.product_type == ProductType.SPOT,
                InstrumentModel.base_asset == "BTC",
                InstrumentModel.quote_asset == "USDT",
                InstrumentModel.settlement_asset.is_(None),
            )
        )
        if instrument is None:
            instrument = InstrumentModel(
                instrument_key="spot:spot:BTC:USDT:",
                canonical_symbol="BTC",
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset="BTC",
                quote_asset="USDT",
                settlement_asset=None,
                is_active=True,
            )
            session.add(instrument)
            session.flush()
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == instrument.id,
                SymbolModel.venue == Venue.BINANCE.value,
                SymbolModel.exchange_symbol == "BTCUSDT",
            )
        )
        if symbol is None:
            symbol = SymbolModel(
                instrument_ref_id=instrument.id,
                venue=Venue.BINANCE.value,
                symbol="BTC",
                exchange_symbol="BTCUSDT",
                venue_asset_id="BTCUSDT",
                asset_id=None,
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset="BTC",
                quote_asset="USDT",
                settlement_asset=None,
                price_tick_size=Decimal("0.01"),
                quantity_step_size=Decimal("0.000001"),
                min_order_size=Decimal("0.000001"),
                size_decimals=6,
                max_leverage=None,
                only_isolated=False,
                is_perpetual=False,
                is_builder_deployed=False,
                is_strategy_eligible=True,
                is_trading_eligible=True,
                is_active=True,
                raw_metadata={},
            )
            session.add(symbol)
            session.flush()
        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id=f"intent-binance-{suffix}",
            decision_id=f"decision-binance-{suffix}",
            action=None,
            mandate_desired_trade_ref_id=None,
            desired_trade_key=f"trade-binance-{suffix}",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=binding.id,
            binding_key=binding.binding_key,
            venue_account_ref_id=account.id,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol.id,
            symbol="BTC",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.01"),
            limit_price=Decimal("100000"),
            reduce_only=False,
            ttl_seconds=30,
            status=OrderIntentStatus.SUBMITTED,
            idempotency_key=f"idem-binance-{suffix}",
            provenance={},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.flush()
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id=f"subm-binance-{suffix}",
                intent_id=intent.intent_id,
                client_order_id=f"cl-binance-{suffix}",
                venue_account_ref_id=account.id,
                venue=Venue.BINANCE.value,
                account_address=account.account_address,
                instrument_ref_id=instrument.id,
                symbol_id=symbol.id,
                symbol="BTC",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                limit_price=Decimal("100000"),
                original_quantity=Decimal("0.01"),
                remaining_quantity=Decimal("0.01"),
                reduce_only=False,
                exchange_order_id=f"binance-order-{suffix}",
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
                submitted_at=datetime.now(UTC),
                acknowledged_at=datetime.now(UTC),
                filled_quantity=Decimal("0"),
                average_fill_price=None,
                last_fill_at=None,
                last_reconciled_at=None,
                status_reason_code=None,
                status_message=None,
                reason_codes=[],
                cancelable_in_principle=True,
                amendable_in_principle=True,
                raw_payload={"seeded": True},
            )
        )
        session.commit()
    return f"subm-binance-{suffix}"


def _build_okx_execution_service(
    session_factory,
    *,
    transport,
    **settings_overrides,
) -> DefaultExecutionService:
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.OKX.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        EXECUTION_REQUIRE_PRIVATE_STATE_FOR_SUBMISSION_READINESS=False,
        OKX_ENABLED=True,
        OKX_READ_ONLY_MODE=False,
        OKX_DRY_RUN_MODE=False,
        OKX_SUBMISSION_ENABLED=True,
        OKX_SUBMISSION_AUTHORIZED=True,
        OKX_ACCOUNT_IDENTIFIER="okx-fallback",
        **settings_overrides,
    )
    adapter = OkxExchangeAdapter(settings, transport=transport, session_factory=session_factory)
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.OKX.value: adapter},
    )
    return DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


def _build_binance_execution_service(
    session_factory,
    *,
    transport,
    **settings_overrides,
) -> DefaultExecutionService:
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.BINANCE.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        EXECUTION_REQUIRE_PRIVATE_STATE_FOR_SUBMISSION_READINESS=False,
        BINANCE_ENABLED=True,
        BINANCE_READ_ONLY_MODE=False,
        BINANCE_DRY_RUN_MODE=False,
        BINANCE_SUBMISSION_ENABLED=True,
        BINANCE_SUBMISSION_AUTHORIZED=True,
        BINANCE_ACCOUNT_IDENTIFIER="binance-fallback",
        **settings_overrides,
    )
    adapter = BinanceExchangeAdapter(settings, transport=transport, session_factory=session_factory)
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.BINANCE.value: adapter},
    )
    return DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


def _build_coinbase_execution_service(
    session_factory,
    *,
    transport,
    **settings_overrides,
) -> DefaultExecutionService:
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.COINBASE_ADVANCED_TRADE.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        COINBASE_ADVANCED_ENABLED=True,
        COINBASE_ADVANCED_READ_ONLY_MODE=False,
        COINBASE_ADVANCED_DRY_RUN_MODE=False,
        COINBASE_ADVANCED_SUBMISSION_ENABLED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_ACCOUNT_IDENTIFIER="cb-fallback",
        COINBASE_ADVANCED_JWT_KEY_NAME="organizations/test/apiKeys/fallback",
        COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=_generate_ec_private_key_pem(),
        **settings_overrides,
    )
    adapter = CoinbaseAdvancedTradeExchangeAdapter(
        settings,
        transport=transport,
        session_factory=session_factory,
    )
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.COINBASE_ADVANCED_TRADE.value: adapter},
    )
    return DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


def _build_hyperliquid_execution_service(
    session_factory,
    *,
    transport,
    account_address: str,
    signing_private_key: str = HYPERLIQUID_TEST_PRIVATE_KEY,
    **settings_overrides,
) -> DefaultExecutionService:
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.HYPERLIQUID.value,
        EXCHANGE_USE_TESTNET=True,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
        HYPERLIQUID_SUBMISSION_ENABLED=True,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        EXCHANGE_ACCOUNT_ADDRESS=account_address,
        EXCHANGE_CREDENTIALS_REF="secret://acct",
        EXCHANGE_SIGNING_PRIVATE_KEY=signing_private_key,
        **settings_overrides,
    )
    adapter = HyperliquidExchangeAdapter(
        settings,
        transport=transport,
        session_factory=session_factory,
    )
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.HYPERLIQUID.value: adapter},
    )
    return DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


def _prepare_hyperliquid_signed_order_context(
    session_factory,
    submitted_order_id: str,
    *,
    signing_private_key: str = HYPERLIQUID_TEST_PRIVATE_KEY,
) -> str:
    account_address = signer_address(signing_private_key)
    with session_factory() as session:
        submitted = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert submitted is not None
        account = session.get(VenueAccountModel, submitted.venue_account_ref_id)
        symbol = session.get(SymbolModel, submitted.symbol_id)
        assert account is not None
        assert symbol is not None
        account.account_address = account_address
        account.venue_native_account_id = account_address
        submitted.account_address = account_address
        symbol.asset_id = 0
        symbol.venue_asset_id = symbol.venue_asset_id or "0"
        session.add(account)
        session.add(submitted)
        session.add(symbol)
        session.commit()
    return account_address


def _mark_submitted_order_retryable_rejected(
    session_factory,
    submitted_order_id: str,
) -> None:
    with session_factory() as session:
        order = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == order.intent_id)
        )
        assert order is not None
        assert intent is not None
        order.exchange_order_id = None
        order.client_order_id = f"{order.client_order_id}-retryable"
        order.status = SubmittedOrderStatus.REJECTED
        order.reconciliation_status = SubmittedOrderReconciliationStatus.RECONCILED
        order.status_reason_code = "temporarily_unavailable"
        order.status_message = "Venue temporarily unavailable."
        order.reason_codes = ["temporarily_unavailable"]
        order.cancelable_in_principle = False
        order.amendable_in_principle = False
        intent.status = OrderIntentStatus.REJECTED
        session.add(order)
        session.add(intent)
        session.commit()


def test_same_venue_multi_account_targeting_survives_cancel() -> None:
    session_factory = build_test_session_factory()
    first_order_id = _seed_okx_submitted_order(session_factory, suffix="a", api_key="okx-key-a")
    second_order_id = _seed_okx_submitted_order(session_factory, suffix="b", api_key="okx-key-b")
    seen_keys: list[str] = []

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/cancel-order":
            seen_keys.append(headers["OK-ACCESS-KEY"])
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.OKX.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        OKX_ENABLED=True,
        OKX_READ_ONLY_MODE=False,
        OKX_DRY_RUN_MODE=False,
        OKX_SUBMISSION_ENABLED=True,
        OKX_SUBMISSION_AUTHORIZED=True,
        OKX_ACCOUNT_IDENTIFIER="okx-fallback",
    )
    adapter = OkxExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.OKX.value: adapter},
    )
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )

    first = asyncio.run(execution.cancel_submitted_order(first_order_id))
    second = asyncio.run(execution.cancel_submitted_order(second_order_id))

    assert first.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert second.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert first.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert second.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert seen_keys == ["okx-key-a", "okx-key-b"]
    assert first.venue_account_ref_id != second.venue_account_ref_id

    with session_factory() as session:
        first_events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == first_order_id
            )
        ).all()
        second_events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == second_order_id
            )
        ).all()
        assert {event.event_type for event in first_events} >= {"cancel_requested", "cancel_acknowledged"}
        assert {event.event_type for event in second_events} >= {"cancel_requested", "cancel_acknowledged"}


def test_okx_cancel_requires_reconciliation_before_final_canceled() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(session_factory, suffix="c", api_key="okx-key-c")

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/cancel-order":
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        if method == "GET" and path == "/api/v5/trade/order":
            return {"code": "0", "data": [{"state": "canceled", "sz": "0.01", "accFillSz": "0"}]}
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.OKX.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        OKX_ENABLED=True,
        OKX_READ_ONLY_MODE=False,
        OKX_DRY_RUN_MODE=False,
        OKX_SUBMISSION_ENABLED=True,
        OKX_SUBMISSION_AUTHORIZED=True,
        OKX_ACCOUNT_IDENTIFIER="okx-fallback",
    )
    adapter = OkxExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.OKX.value: adapter},
    )
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )

    canceled = asyncio.run(execution.cancel_submitted_order(submitted_order_id))
    assert canceled.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert canceled.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING

    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted_order_id))
    assert reconciled.status == SubmittedOrderStatus.CANCELED
    assert reconciled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert {event.event_type for event in events} >= {
            "cancel_requested",
            "cancel_acknowledged",
            "reconciliation_canceled",
        }


def test_coinbase_cancel_requires_reconciliation_before_final_canceled() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_coinbase_submitted_order(session_factory, suffix="c")

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v3/brokerage/orders/batch_cancel":
            return {"results": [{"success": True}]}
        if method == "GET" and path == "/api/v3/brokerage/orders/historical/cb-order-c":
            return {
                "order": {
                    "order_id": "cb-order-c",
                    "status": "CANCELLED",
                    "filled_size": "0",
                    "order_configuration": {
                        "limit_limit_gtc": {
                            "base_size": "0.01",
                            "limit_price": "100000",
                        }
                    },
                }
            }
        raise AssertionError((method, path, params, body, headers))

    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.COINBASE_ADVANCED_TRADE.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        COINBASE_ADVANCED_ENABLED=True,
        COINBASE_ADVANCED_READ_ONLY_MODE=False,
        COINBASE_ADVANCED_DRY_RUN_MODE=False,
        COINBASE_ADVANCED_SUBMISSION_ENABLED=True,
        COINBASE_ADVANCED_SUBMISSION_AUTHORIZED=True,
        COINBASE_ADVANCED_ACCOUNT_IDENTIFIER="cb-fallback",
        COINBASE_ADVANCED_JWT_KEY_NAME="organizations/test/apiKeys/fallback",
        COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=_generate_ec_private_key_pem(),
    )
    adapter = CoinbaseAdvancedTradeExchangeAdapter(
        settings,
        transport=_transport,
        session_factory=session_factory,
    )
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.COINBASE_ADVANCED_TRADE.value: adapter},
    )
    execution = DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )

    canceled = asyncio.run(execution.cancel_submitted_order(submitted_order_id))
    assert canceled.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert canceled.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING

    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted_order_id))
    assert reconciled.status == SubmittedOrderStatus.CANCELED
    assert reconciled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert {event.event_type for event in events} >= {
            "cancel_requested",
            "cancel_acknowledged",
            "reconciliation_canceled",
        }


def test_okx_amend_updates_working_order_without_claiming_final_state() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(session_factory, suffix="amend", api_key="okx-key-amend")

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/amend-order":
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)

    actionability = asyncio.run(execution.get_submitted_order_actionability(submitted_order_id))
    assert actionability.amend_supported is True
    assert actionability.amend_allowed_now is True

    amended = asyncio.run(
        execution.amend_submitted_order(
            submitted_order_id,
            new_quantity=Decimal("0.02"),
            new_limit_price=Decimal("100500"),
        )
    )

    assert amended.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert amended.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert amended.original_quantity == Decimal("0.02")
    assert amended.remaining_quantity == Decimal("0.02")
    assert amended.limit_price == Decimal("100500")

    actionability = asyncio.run(execution.get_submitted_order_actionability(submitted_order_id))
    assert actionability.amend_allowed_now is False
    assert "amend_reconciliation_pending" in actionability.amend_reason_codes

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(event.event_type == "amend_requested" for event in events)
        assert any(event.event_type == "amend_acknowledged" for event in events)


def test_coinbase_amend_updates_working_order_without_claiming_final_state() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_coinbase_submitted_order(session_factory, suffix="amend")

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v3/brokerage/orders/edit":
            return {"success": True}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_coinbase_execution_service(session_factory, transport=_transport)

    actionability = asyncio.run(execution.get_submitted_order_actionability(submitted_order_id))
    assert actionability.amend_supported is True
    assert actionability.amend_allowed_now is True

    amended = asyncio.run(
        execution.amend_submitted_order(
            submitted_order_id,
            new_quantity=Decimal("0.02"),
            new_limit_price=Decimal("100500"),
        )
    )

    assert amended.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert amended.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert amended.original_quantity == Decimal("0.02")
    assert amended.remaining_quantity == Decimal("0.02")
    assert amended.limit_price == Decimal("100500")

    recommendation = asyncio.run(
        execution.get_submitted_order_recovery_recommendation(submitted_order_id)
    )
    assert recommendation.category == SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN
    assert recommendation.venue_state_uncertain is True

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(event.event_type == "amend_requested" for event in events)
        assert any(event.event_type == "amend_acknowledged" for event in events)


def test_same_venue_multi_account_targeting_survives_okx_amend() -> None:
    session_factory = build_test_session_factory()
    first_order_id = _seed_okx_submitted_order(session_factory, suffix="amenda", api_key="okx-key-amend-a")
    second_order_id = _seed_okx_submitted_order(session_factory, suffix="amendb", api_key="okx-key-amend-b")
    seen_keys: list[str] = []

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/amend-order":
            seen_keys.append(headers["OK-ACCESS-KEY"])
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)

    first = asyncio.run(
        execution.amend_submitted_order(first_order_id, new_limit_price=Decimal("100250"))
    )
    second = asyncio.run(
        execution.amend_submitted_order(second_order_id, new_limit_price=Decimal("100350"))
    )

    assert first.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert second.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert first.venue_account_ref_id != second.venue_account_ref_id
    assert seen_keys == ["okx-key-amend-a", "okx-key-amend-b"]


def test_retryable_rejection_can_execute_same_target_retry_safely() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(session_factory, suffix="retry", api_key="okx-key-retry")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v5/account/balance":
            return {
                "code": "0",
                "data": [{"totalEq": "1000", "availEq": "800", "upl": "0", "notionalUsd": "0"}],
            }
        if method == "GET" and path == "/api/v5/trade/orders-pending":
            return {"code": "0", "data": []}
        if method == "GET" and path == "/api/v5/trade/fills":
            return {"code": "0", "data": []}
        if method == "POST" and path == "/api/v5/trade/order":
            return {
                "code": "0",
                "data": [
                    {
                        "ordId": "okx-order-retry-new",
                        "clOrdId": "mf-retry",
                    }
                ],
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.action == "retry_same_target"
    assert result.executed is True
    assert result.blocked is False
    assert result.resulting_order is not None
    assert result.resulting_order.submitted_order_id != submitted_order_id
    assert result.resulting_order.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert result.resulting_order.venue_account_ref_id is not None

    with session_factory() as session:
        original_events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        persisted_orders = session.scalars(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.intent_id == "intent-okx-retry"
            )
        ).all()
        assert any(event.event_type == "recovery_retry_submitted" for event in original_events)
        assert len(persisted_orders) == 2


def test_aster_retry_uses_fresh_client_order_id_for_strict_reuse_venue() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(session_factory, suffix="retry", api_key="aster-key-retry")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    seen: dict[str, str] = {}

    with session_factory() as session:
        original = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert original is not None
        original_client_order_id = str(original.client_order_id)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v2/balance":
            return [
                {
                    "balance": "1000",
                    "availableBalance": "800",
                    "crossWalletBalance": "200",
                    "crossUnPnl": "10",
                    "maxWithdrawAmount": "800",
                }
            ]
        if method == "GET" and path == "/fapi/v1/openOrders":
            return []
        if method == "GET" and path == "/fapi/v1/userTrades":
            return []
        if method == "POST" and path == "/fapi/v1/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            seen["api_key"] = headers["X-MBX-APIKEY"]
            seen["client_order_id"] = parsed["newClientOrderId"]
            return {
                "orderId": "aster-order-retry-new",
                "clientOrderId": parsed["newClientOrderId"],
                "status": "accepted",
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_aster_execution_service(session_factory, transport=_transport)

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.action == "retry_same_target"
    assert result.executed is True
    assert result.resulting_order is not None
    assert seen["api_key"] == "aster-key-retry"
    assert seen["client_order_id"].startswith("mf-r-")
    assert seen["client_order_id"] != original_client_order_id
    assert result.resulting_order.client_order_id == seen["client_order_id"]


def test_binance_retry_uses_fresh_client_order_id_for_strict_reuse_venue() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry",
        api_key="binance-key-retry",
    )
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    seen: dict[str, str] = {}

    with session_factory() as session:
        original = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert original is not None
        original_client_order_id = str(original.client_order_id)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/account":
            return {"balances": [{"asset": "USDT", "free": "1000", "locked": "0"}]}
        if method == "GET" and path == "/api/v3/openOrders":
            return []
        if method == "GET" and path == "/api/v3/myTrades":
            return []
        if method == "POST" and path == "/api/v3/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            seen["api_key"] = headers["X-MBX-APIKEY"]
            seen["client_order_id"] = parsed["newClientOrderId"]
            return {
                "orderId": "binance-order-retry-new",
                "clientOrderId": parsed["newClientOrderId"],
                "status": "NEW",
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_binance_execution_service(session_factory, transport=_transport)

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.action == "retry_same_target"
    assert result.executed is True
    assert result.resulting_order is not None
    assert seen["api_key"] == "binance-key-retry"
    assert seen["client_order_id"].startswith("mf-r-")
    assert seen["client_order_id"] != original_client_order_id
    assert result.resulting_order.client_order_id == seen["client_order_id"]


def test_same_venue_multi_account_targeting_survives_binance_retry() -> None:
    session_factory = build_test_session_factory()
    first_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retrya",
        api_key="binance-key-retry-a",
    )
    second_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retryb",
        api_key="binance-key-retry-b",
    )
    _mark_submitted_order_retryable_rejected(session_factory, first_order_id)
    _mark_submitted_order_retryable_rejected(session_factory, second_order_id)

    with session_factory() as session:
        original_orders = session.scalars(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id.in_([first_order_id, second_order_id])
            )
        ).all()
        original_client_order_ids = {
            order.submitted_order_id: str(order.client_order_id)
            for order in original_orders
        }

    seen_keys: list[str] = []
    seen_client_order_ids: list[str] = []

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/account":
            return {"balances": [{"asset": "USDT", "free": "1000", "locked": "0"}]}
        if method == "GET" and path == "/api/v3/openOrders":
            return []
        if method == "GET" and path == "/api/v3/myTrades":
            return []
        if method == "POST" and path == "/api/v3/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            seen_keys.append(headers["X-MBX-APIKEY"])
            seen_client_order_ids.append(parsed["newClientOrderId"])
            return {
                "orderId": f"binance-order-{len(seen_client_order_ids)}",
                "clientOrderId": parsed["newClientOrderId"],
                "status": "NEW",
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_binance_execution_service(session_factory, transport=_transport)

    first = asyncio.run(execution.execute_submitted_order_recovery(first_order_id))
    second = asyncio.run(execution.execute_submitted_order_recovery(second_order_id))

    assert first.resulting_order is not None
    assert second.resulting_order is not None
    assert first.resulting_order.venue_account_ref_id != second.resulting_order.venue_account_ref_id
    assert seen_keys == ["binance-key-retry-a", "binance-key-retry-b"]
    assert len(set(seen_client_order_ids)) == 2
    assert all(client_order_id.startswith("mf-r-") for client_order_id in seen_client_order_ids)
    assert seen_client_order_ids[0] != original_client_order_ids[first_order_id]
    assert seen_client_order_ids[1] != original_client_order_ids[second_order_id]


def test_aster_retry_ignores_pre_submit_same_symbol_trade_when_time_bounded() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(session_factory, suffix="retry-stale-fill", api_key="aster-key-stale")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    seen: dict[str, object] = {}

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v2/balance":
            return [
                {
                    "balance": "1000",
                    "availableBalance": "800",
                    "crossWalletBalance": "200",
                    "crossUnPnl": "10",
                    "maxWithdrawAmount": "800",
                }
            ]
        if method == "GET" and path == "/fapi/v1/openOrders":
            return []
        if method == "GET" and path == "/fapi/v1/userTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "aster-order-stale-fill",
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms - 1,
                }
            ]
        if method == "POST" and path == "/fapi/v1/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            seen["client_order_id"] = parsed["newClientOrderId"]
            return {
                "orderId": "aster-order-retry-after-stale-fill",
                "clientOrderId": parsed["newClientOrderId"],
                "status": "accepted",
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_aster_execution_service(session_factory, transport=_transport)

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.executed is True
    assert result.resulting_order is not None
    assert seen["start_time"] == start_time_ms
    assert str(seen["client_order_id"]).startswith("mf-r-")


def test_binance_retry_ignores_pre_submit_same_symbol_trade_when_time_bounded() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry-stale-fill",
        api_key="binance-key-stale",
    )
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    seen: dict[str, object] = {}

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/account":
            return {"balances": [{"asset": "USDT", "free": "1000", "locked": "0"}]}
        if method == "GET" and path == "/api/v3/openOrders":
            return []
        if method == "GET" and path == "/api/v3/myTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "binance-order-stale-fill",
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms - 1,
                }
            ]
        if method == "POST" and path == "/api/v3/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            seen["client_order_id"] = parsed["newClientOrderId"]
            return {
                "orderId": "binance-order-retry-after-stale-fill",
                "clientOrderId": parsed["newClientOrderId"],
                "status": "NEW",
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_binance_execution_service(session_factory, transport=_transport)

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.executed is True
    assert result.resulting_order is not None
    assert seen["start_time"] == start_time_ms
    assert str(seen["client_order_id"]).startswith("mf-r-")


def test_aster_retry_is_blocked_when_same_account_symbol_fill_evidence_is_ambiguous_without_exchange_order_id() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(session_factory, suffix="retry-live-fill", api_key="aster-key-live")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    seen: dict[str, object] = {}
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v1/openOrders":
            return []
        if method == "GET" and path == "/fapi/v1/userTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "aster-order-retry-live-fill",
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                }
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        AsterExchangeAdapter,
        venue=Venue.ASTER.value,
        session_factory=session_factory,
        transport=_transport,
        ASTER_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "same_account_same_symbol_ambiguous"
    assert evidence.fills
    assert not hasattr(adapter, "fetch_submitted_order_private_fills_with_source")

    execution = _build_aster_execution_service(session_factory, transport=_transport)

    with pytest.raises(SubmittedOrderActionError):
        asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert seen["start_time"] == start_time_ms
    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(
            event.event_type == "recovery_retry_blocked"
            and "retry_same_account_symbol_fill_ambiguous" in (event.reason_codes or [])
            and event.raw_payload.get("fill_evidence_scope") == "same_account_same_symbol_ambiguous"
            for event in events
        )


def test_binance_retry_is_blocked_when_same_account_symbol_fill_evidence_is_ambiguous_without_exchange_order_id() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry-live-fill",
        api_key="binance-key-live",
    )
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    seen: dict[str, object] = {}
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/openOrders":
            return []
        if method == "GET" and path == "/api/v3/myTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "binance-order-retry-live-fill",
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                }
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        transport=_transport,
        BINANCE_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "same_account_same_symbol_ambiguous"
    assert evidence.fills
    assert not hasattr(adapter, "fetch_submitted_order_private_fills_with_source")

    execution = _build_binance_execution_service(session_factory, transport=_transport)

    with pytest.raises(SubmittedOrderActionError):
        asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert seen["start_time"] == start_time_ms
    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(
            event.event_type == "recovery_retry_blocked"
            and "retry_same_account_symbol_fill_ambiguous" in (event.reason_codes or [])
            and event.raw_payload.get("fill_evidence_scope") == "same_account_same_symbol_ambiguous"
            for event in events
        )


def test_aster_retry_private_fill_evidence_remains_order_scoped_when_exchange_order_id_matches() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(
        session_factory,
        suffix="retry-order-scoped",
        api_key="aster-key-order-scoped",
    )
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)
        exchange_order_id = model.exchange_order_id

    seen: dict[str, object] = {}

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v1/userTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "unrelated-aster-order",
                    "price": "100000",
                    "qty": "0.001",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                },
                {
                    "id": 2,
                    "orderId": exchange_order_id,
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms + 2,
                },
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        AsterExchangeAdapter,
        venue=Venue.ASTER.value,
        session_factory=session_factory,
        transport=_transport,
        ASTER_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert seen["start_time"] == start_time_ms
    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "order_scoped"
    assert len(evidence.fills) == 1
    assert evidence.fills[0].exchange_order_id == exchange_order_id
    assert evidence.message == "Aster private trade evidence was matched by exchange order id."
    assert not hasattr(adapter, "fetch_submitted_order_private_fills_with_source")


def test_binance_retry_private_fill_evidence_remains_order_scoped_when_exchange_order_id_matches() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry-order-scoped",
        api_key="binance-key-order-scoped",
    )
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)
        exchange_order_id = model.exchange_order_id

    seen: dict[str, object] = {}

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/myTrades":
            seen["start_time"] = params["startTime"]
            return [
                {
                    "id": 1,
                    "orderId": "unrelated-binance-order",
                    "price": "100000",
                    "qty": "0.001",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                },
                {
                    "id": 2,
                    "orderId": exchange_order_id,
                    "price": "100100",
                    "qty": "0.002",
                    "commission": "0.01",
                    "time": start_time_ms + 2,
                },
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        transport=_transport,
        BINANCE_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert seen["start_time"] == start_time_ms
    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "order_scoped"
    assert len(evidence.fills) == 1
    assert evidence.fills[0].exchange_order_id == exchange_order_id
    assert evidence.message == "Binance private trade evidence was matched by exchange order id."
    assert not hasattr(adapter, "fetch_submitted_order_private_fills_with_source")


def test_aster_order_scoped_fill_evidence_zero_match_message_is_not_misleading() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(
        session_factory,
        suffix="retry-order-scoped-empty",
        api_key="aster-key-order-scoped-empty",
    )
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v1/userTrades":
            return [
                {
                    "id": 1,
                    "orderId": "unrelated-aster-order",
                    "price": "100000",
                    "qty": "0.001",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                }
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        AsterExchangeAdapter,
        venue=Venue.ASTER.value,
        session_factory=session_factory,
        transport=_transport,
        ASTER_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "order_scoped"
    assert not evidence.fills
    assert evidence.message == (
        "Aster private trade query was filtered by exchange order id; no matching fills were returned."
    )
    assert "matched by exchange order id" not in str(evidence.message)


def test_binance_order_scoped_fill_evidence_zero_match_message_is_not_misleading() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry-order-scoped-empty",
        api_key="binance-key-order-scoped-empty",
    )
    start_time_ms = _submitted_order_submitted_at_ms(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/myTrades":
            return [
                {
                    "id": 1,
                    "orderId": "unrelated-binance-order",
                    "price": "100000",
                    "qty": "0.001",
                    "commission": "0.01",
                    "time": start_time_ms + 1,
                }
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        transport=_transport,
        BINANCE_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "venue_query"
    assert evidence.evidence_scope == "order_scoped"
    assert not evidence.fills
    assert evidence.message == (
        "Binance private trade query was filtered by exchange order id; no matching fills were returned."
    )
    assert "matched by exchange order id" not in str(evidence.message)


def test_aster_retry_fill_evidence_query_failure_is_not_reported_as_venue_query() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_aster_submitted_order(session_factory, suffix="retry-fill-fail", api_key="aster-key-fail")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v1/openOrders":
            return []
        if method == "GET" and path == "/fapi/v1/userTrades":
            raise VenueAdapterError("simulated Aster private trade query failure")
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        AsterExchangeAdapter,
        venue=Venue.ASTER.value,
        session_factory=session_factory,
        transport=_transport,
        ASTER_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "unavailable"
    assert evidence.evidence_scope == "query_failed"
    assert not evidence.fills

    execution = _build_aster_execution_service(session_factory, transport=_transport)

    with pytest.raises(SubmittedOrderActionError):
        asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(
            event.event_type == "recovery_retry_blocked"
            and "retry_private_fill_evidence_unavailable" in (event.reason_codes or [])
            and event.raw_payload.get("fill_evidence_scope") == "query_failed"
            for event in events
        )


def test_binance_retry_fill_evidence_query_failure_blocks_retry_without_new_submission() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="retry-fill-fail",
        api_key="binance-key-fail",
    )
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    with session_factory() as session:
        model = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert model is not None
        submitted = DefaultExecutionService._submitted_order_from_model(model)
        intent_id = model.intent_id
        before_order_ids = {
            row.submitted_order_id
            for row in session.scalars(
                select(SubmittedOrderModel).where(SubmittedOrderModel.intent_id == intent_id)
            ).all()
        }

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/openOrders":
            return []
        if method == "GET" and path == "/api/v3/myTrades":
            raise VenueAdapterError("simulated Binance private trade query failure")
        if method == "POST" and path == "/api/v3/order":
            raise AssertionError("retry submit must not run when private fill evidence query fails")
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        transport=_transport,
        BINANCE_ENABLED=True,
    )

    evidence = asyncio.run(adapter.fetch_retry_private_fill_evidence(submitted))

    assert evidence.source == "unavailable"
    assert evidence.evidence_scope == "query_failed"
    assert not evidence.fills

    execution = _build_binance_execution_service(session_factory, transport=_transport)

    with pytest.raises(SubmittedOrderActionError):
        asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    with session_factory() as session:
        after_order_ids = {
            row.submitted_order_id
            for row in session.scalars(
                select(SubmittedOrderModel).where(SubmittedOrderModel.intent_id == intent_id)
            ).all()
        }
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert after_order_ids == before_order_ids
        assert any(
            event.event_type == "recovery_retry_blocked"
            and "retry_private_fill_evidence_unavailable" in (event.reason_codes or [])
            and event.raw_payload.get("fill_evidence_scope") == "query_failed"
            for event in events
        )


def test_same_venue_multi_account_targeting_survives_binance_private_open_orders_query() -> None:
    session_factory = build_test_session_factory()
    first_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="privatea",
        api_key="binance-key-private-a",
    )
    second_order_id = _seed_binance_submitted_order(
        session_factory,
        suffix="privateb",
        api_key="binance-key-private-b",
    )
    first_account_ref = _submitted_order_account_ref(session_factory, first_order_id)
    second_account_ref = _submitted_order_account_ref(session_factory, second_order_id)
    seen_keys: list[str] = []

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v3/openOrders":
            seen_keys.append(headers["X-MBX-APIKEY"])
            order_id = "11" if headers["X-MBX-APIKEY"] == "binance-key-private-a" else "22"
            return [
                {
                    "symbol": "BTCUSDT",
                    "orderId": order_id,
                    "clientOrderId": f"venue-open-{order_id}",
                    "side": "SELL",
                    "type": "LIMIT",
                    "price": "100000",
                    "origQty": "0.01",
                    "executedQty": "0",
                    "cummulativeQuoteQty": "0",
                    "updateTime": 1710000000000,
                }
            ]
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        BinanceExchangeAdapter,
        venue=Venue.BINANCE.value,
        session_factory=session_factory,
        transport=_transport,
        BINANCE_ENABLED=True,
        BINANCE_ACCOUNT_IDENTIFIER="binance-fallback",
    )

    first_orders = asyncio.run(adapter.fetch_open_orders(venue_account_ref_id=first_account_ref))
    second_orders = asyncio.run(adapter.fetch_open_orders(venue_account_ref_id=second_account_ref))

    assert seen_keys == ["binance-key-private-a", "binance-key-private-b"]
    assert first_orders[0].venue_account_ref_id == first_account_ref
    assert second_orders[0].venue_account_ref_id == second_account_ref
    assert not hasattr(first_orders[0], "submitted_order_id")
    assert first_orders[0].exchange_order_id == "11"
    assert second_orders[0].exchange_order_id == "22"


def test_same_venue_multi_account_targeting_survives_okx_recent_fills_query() -> None:
    session_factory = build_test_session_factory()
    first_order_id = _seed_okx_submitted_order(
        session_factory,
        suffix="fillsa",
        api_key="okx-key-fills-a",
    )
    second_order_id = _seed_okx_submitted_order(
        session_factory,
        suffix="fillsb",
        api_key="okx-key-fills-b",
    )
    first_account_ref = _submitted_order_account_ref(session_factory, first_order_id)
    second_account_ref = _submitted_order_account_ref(session_factory, second_order_id)
    seen_keys: list[str] = []

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v5/trade/fills":
            seen_keys.append(headers["OK-ACCESS-KEY"])
            ord_id = "ord-a" if headers["OK-ACCESS-KEY"] == "okx-key-fills-a" else "ord-b"
            return {
                "code": "0",
                "data": [
                    {
                        "tradeId": f"trade-{ord_id}",
                        "ordId": ord_id,
                        "instId": "BTC-USDT-SWAP",
                        "fillPx": "100050",
                        "fillSz": "0.002",
                        "fee": "0.1",
                        "ts": "1710000000000",
                    }
                ],
            }
        raise AssertionError((method, path, params, body, headers))

    adapter = _build_private_state_test_adapter(
        OkxExchangeAdapter,
        venue=Venue.OKX.value,
        session_factory=session_factory,
        transport=_transport,
        OKX_ENABLED=True,
        OKX_ACCOUNT_IDENTIFIER="okx-fallback",
    )

    first_fills = asyncio.run(adapter.fetch_recent_fills(venue_account_ref_id=first_account_ref))
    second_fills = asyncio.run(adapter.fetch_recent_fills(venue_account_ref_id=second_account_ref))

    assert seen_keys == ["okx-key-fills-a", "okx-key-fills-b"]
    assert first_fills[0].venue_account_ref_id == first_account_ref
    assert second_fills[0].venue_account_ref_id == second_account_ref
    assert first_fills[0].exchange_order_id == "ord-a"
    assert second_fills[0].exchange_order_id == "ord-b"


def test_hyperliquid_recent_fills_query_uses_targeted_account_truth() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)
    seen_users: list[str] = []

    async def _transport(payload):
        assert payload["type"] == "userFills"
        seen_users.append(payload["user"])
        return [
            {
                "coin": "BTC",
                "oid": 123,
                "tid": 456,
                "px": "100250",
                "sz": "0.003",
                "fee": "0.02",
                "time": 1710000000000,
            }
        ]

    adapter = _build_private_state_test_adapter(
        HyperliquidExchangeAdapter,
        venue=Venue.HYPERLIQUID.value,
        session_factory=session_factory,
        transport=_transport,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0xdeadbeef",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    fills = asyncio.run(adapter.fetch_recent_fills(venue_account_ref_id=venue_account_ref_id))

    assert seen_users == [account_address]
    assert fills[0].venue_account_ref_id == venue_account_ref_id
    assert fills[0].account_address == account_address
    assert fills[0].exchange_order_id == "123"


def test_hyperliquid_open_orders_query_uses_targeted_account_truth() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)
    seen_users: list[str] = []

    async def _transport(payload):
        assert payload["type"] == "frontendOpenOrders"
        seen_users.append(payload["user"])
        return [
            {
                "coin": "BTC",
                "oid": 12345,
                "cloid": "hl-open-1",
                "limitPx": "100250",
                "origSz": "0.01",
                "sz": "0.01",
                "side": "B",
                "orderType": "limit",
                "timestamp": 1710000000000,
            }
        ]

    adapter = _build_private_state_test_adapter(
        HyperliquidExchangeAdapter,
        venue=Venue.HYPERLIQUID.value,
        session_factory=session_factory,
        transport=_transport,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0xdeadbeef",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    source, orders = asyncio.run(
        adapter.fetch_open_orders_with_source(venue_account_ref_id=venue_account_ref_id)
    )

    assert source == "venue_query"
    assert seen_users == [account_address]
    assert orders[0].venue_account_ref_id == venue_account_ref_id
    assert orders[0].account_address == account_address
    assert orders[0].exchange_order_id == "12345"
    assert orders[0].linked_submitted_order_id == submitted_order_id


def test_hyperliquid_open_positions_query_uses_targeted_account_truth() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)
    seen_users: list[str] = []

    async def _transport(payload):
        assert payload["type"] == "clearinghouseState"
        seen_users.append(payload["user"])
        return {
            "time": 1710000000000,
            "assetPositions": [
                {
                    "type": "oneWay",
                    "position": {
                        "coin": "BTC",
                        "szi": "0.02",
                        "entryPx": "100000",
                        "markPx": "101000",
                        "unrealizedPnl": "20",
                        "positionValue": "2020",
                    },
                }
            ],
        }

    adapter = _build_private_state_test_adapter(
        HyperliquidExchangeAdapter,
        venue=Venue.HYPERLIQUID.value,
        session_factory=session_factory,
        transport=_transport,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0xdeadbeef",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    source, positions = asyncio.run(
        adapter.fetch_open_positions_with_source(venue_account_ref_id=venue_account_ref_id)
    )

    assert source == "venue_query"
    assert seen_users == [account_address]
    assert len(positions) == 1
    assert positions[0].venue_account_ref_id == venue_account_ref_id
    assert positions[0].account_address == account_address
    assert positions[0].symbol == "BTC"
    assert positions[0].quantity == Decimal("0.02")
    assert positions[0].mark_price == Decimal("101000")


def test_hyperliquid_open_positions_derives_mark_price_from_position_value_when_mark_px_missing() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)

    async def _transport(payload):
        assert payload["type"] == "clearinghouseState"
        assert payload["user"] == account_address
        return {
            "time": 1710000000000,
            "assetPositions": [
                {
                    "type": "oneWay",
                    "position": {
                        "coin": "BTC",
                        "szi": "0.02",
                        "entryPx": "100000",
                        "unrealizedPnl": "20",
                        "positionValue": "2020",
                    },
                }
            ],
        }

    adapter = _build_private_state_test_adapter(
        HyperliquidExchangeAdapter,
        venue=Venue.HYPERLIQUID.value,
        session_factory=session_factory,
        transport=_transport,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0xdeadbeef",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    source, positions = asyncio.run(
        adapter.fetch_open_positions_with_source(venue_account_ref_id=venue_account_ref_id)
    )

    assert source == "venue_query"
    assert len(positions) == 1
    assert positions[0].mark_price == Decimal("101000")


def test_hyperliquid_open_positions_leave_mark_price_unknown_when_no_truthful_value_exists() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    venue_account_ref_id = _submitted_order_account_ref(session_factory, submitted_order_id)

    async def _transport(payload):
        assert payload["type"] == "clearinghouseState"
        assert payload["user"] == account_address
        return {
            "time": 1710000000000,
            "assetPositions": [
                {
                    "type": "oneWay",
                    "position": {
                        "coin": "BTC",
                        "szi": "0.02",
                        "entryPx": "100000",
                        "unrealizedPnl": "20",
                    },
                }
            ],
        }

    adapter = _build_private_state_test_adapter(
        HyperliquidExchangeAdapter,
        venue=Venue.HYPERLIQUID.value,
        session_factory=session_factory,
        transport=_transport,
        HYPERLIQUID_ENABLED=True,
        EXCHANGE_ACCOUNT_ADDRESS="0xdeadbeef",
        EXCHANGE_SIGNING_PRIVATE_KEY=HYPERLIQUID_TEST_PRIVATE_KEY,
    )

    source, positions = asyncio.run(
        adapter.fetch_open_positions_with_source(venue_account_ref_id=venue_account_ref_id)
    )

    assert source == "venue_query"
    assert len(positions) == 1
    assert positions[0].mark_price is None


def test_retry_is_blocked_when_other_attempt_exists_for_same_intent() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(session_factory, suffix="retry-block", api_key="okx-key-rb")
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)
    with session_factory() as session:
        original = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert original is not None
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id="subm-okx-retry-block-sibling",
                intent_id=original.intent_id,
                client_order_id="cl-okx-retry-block-sibling",
                venue_account_ref_id=original.venue_account_ref_id,
                venue=original.venue,
                account_address=original.account_address,
                instrument_ref_id=original.instrument_ref_id,
                symbol_id=original.symbol_id,
                symbol=original.symbol,
                side=original.side,
                order_type=original.order_type,
                limit_price=original.limit_price,
                original_quantity=original.original_quantity,
                remaining_quantity=original.remaining_quantity,
                reduce_only=original.reduce_only,
                exchange_order_id="okx-sibling",
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
                submitted_at=datetime.now(UTC),
                acknowledged_at=datetime.now(UTC),
                filled_quantity=Decimal("0"),
                average_fill_price=None,
                last_fill_at=None,
                last_reconciled_at=None,
                status_reason_code=None,
                status_message=None,
                reason_codes=[],
                cancelable_in_principle=True,
                amendable_in_principle=True,
                raw_payload={"seeded": True},
            )
        )
        session.commit()

    async def _should_not_submit(method: str, path: str, params=None, body=None, headers=None):
        raise AssertionError("submit should not happen")

    execution = _build_okx_execution_service(
        session_factory,
        transport=_should_not_submit,
    )

    with pytest.raises(SubmittedOrderActionError):
        asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(event.event_type == "recovery_retry_blocked" for event in events)


def test_recovery_execute_reconciles_cancel_acknowledged_order() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(session_factory, suffix="recover-cancel", api_key="okx-key-rc")

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/cancel-order":
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        if method == "GET" and path == "/api/v5/trade/order":
            return {"code": "0", "data": [{"state": "canceled", "sz": "0.01", "accFillSz": "0"}]}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)
    canceled = asyncio.run(execution.cancel_submitted_order(submitted_order_id))
    assert canceled.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.action == "reconcile_now"
    assert result.resulting_order is not None
    assert result.resulting_order.status == SubmittedOrderStatus.CANCELED


def test_recovery_execute_reconciles_amend_acknowledged_order() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(
        session_factory,
        suffix="recover-amend",
        api_key="okx-key-ra",
    )

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/api/v5/trade/amend-order":
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        if method == "GET" and path == "/api/v5/trade/order":
            return {"code": "0", "data": [{"state": "live", "sz": "0.02", "accFillSz": "0"}]}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)
    amended = asyncio.run(
        execution.amend_submitted_order(
            submitted_order_id,
            new_quantity=Decimal("0.02"),
            new_limit_price=Decimal("100250"),
        )
    )
    assert amended.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING

    result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert result.action == "reconcile_now"
    assert result.executed is True
    assert result.resulting_order is not None
    assert result.resulting_order.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert result.resulting_order.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED


def test_rejected_submitted_order_gets_non_retryable_recovery_guidance() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_aster_execution_service(session_factory, transport=_aster_rejected_transport)
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    recommendation = asyncio.run(
        execution.get_submitted_order_recovery_recommendation(submitted.submitted_order_id)
    )

    assert recommendation.category == SubmittedOrderRecoveryCategory.NON_RETRYABLE
    assert recommendation.retryable is False
    assert "venue_rejected" in recommendation.reason_codes


def test_unknown_reconciliation_gets_uncertain_recovery_guidance() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)

    def _unknown_update(submitted_order: SubmittedOrder) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=submitted_order.venue,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message="Order was absent from venue state and no fills were found.",
            reason_codes=["reconciliation_missing_order"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload={"matched_order": False},
            observed_at=datetime.now(UTC),
        )

    execution = _build_aster_execution_service(
        session_factory,
        transport=_aster_ambiguous_transport,
        lifecycle_update=_unknown_update,
    )
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted.submitted_order_id))
    recommendation = asyncio.run(
        execution.get_submitted_order_recovery_recommendation(reconciled.submitted_order_id)
    )

    assert recommendation.category == SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN
    assert recommendation.venue_state_uncertain is True


def test_hyperliquid_cancel_requires_reconciliation_before_final_canceled() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    seen_actions: list[dict[str, object]] = []

    async def _transport(payload):
        if payload.get("action", {}).get("type") == "cancel":
            seen_actions.append(payload)
            return {"status": "ok", "response": {"data": {"statuses": [{}]}}}
        if payload.get("type") == "orderStatus":
            return {
                "order": {
                    "order": {
                        "oid": 12345,
                        "origSz": "0.01",
                        "sz": "0",
                        "timestamp": 1700002100000,
                    },
                    "status": "canceled",
                    "statusTimestamp": 1700002200000,
                }
            }
        if payload.get("type") == "userFills":
            return []
        raise AssertionError(payload)

    execution = _build_hyperliquid_execution_service(
        session_factory,
        transport=_transport,
        account_address=account_address,
    )

    canceled = asyncio.run(execution.cancel_submitted_order(submitted_order_id))
    assert canceled.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert canceled.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING

    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted_order_id))
    assert reconciled.status == SubmittedOrderStatus.CANCELED
    assert reconciled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert seen_actions
    assert seen_actions[0]["action"]["type"] == "cancel"

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert {event.event_type for event in events} >= {
            "cancel_requested",
            "cancel_acknowledged",
            "reconciliation_canceled",
        }


def test_hyperliquid_amend_updates_working_order_without_claiming_final_state() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    account_address = _prepare_hyperliquid_signed_order_context(session_factory, submitted_order_id)
    seen_actions: list[dict[str, object]] = []

    async def _transport(payload):
        if payload.get("action", {}).get("type") == "modify":
            seen_actions.append(payload)
            return {"status": "ok", "response": {"data": {"statuses": [{}]}}}
        raise AssertionError(payload)

    execution = _build_hyperliquid_execution_service(
        session_factory,
        transport=_transport,
        account_address=account_address,
    )

    actionability = asyncio.run(execution.get_submitted_order_actionability(submitted_order_id))
    assert actionability.amend_supported is True
    assert actionability.amend_allowed_now is True

    amended = asyncio.run(
        execution.amend_submitted_order(
            submitted_order_id,
            new_quantity=Decimal("0.02"),
            new_limit_price=Decimal("100500"),
        )
    )

    assert amended.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert amended.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert amended.original_quantity == Decimal("0.02")
    assert amended.remaining_quantity == Decimal("0.02")
    assert amended.limit_price == Decimal("100500")
    assert seen_actions
    assert seen_actions[0]["action"]["type"] == "modify"

    recommendation = asyncio.run(
        execution.get_submitted_order_recovery_recommendation(submitted_order_id)
    )
    assert recommendation.category == SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN

    with session_factory() as session:
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(event.event_type == "amend_requested" for event in events)
        assert any(event.event_type == "amend_acknowledged" for event in events)


def test_kraken_cancel_requires_reconciliation_before_final_canceled() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id = _seed_symbol(
        session_factory,
        venue=Venue.KRAKEN.value,
        symbol="BTC",
        exchange_symbol="XBT/USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        quote_asset="USD",
        settlement_asset=None,
    )
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.KRAKEN.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        KRAKEN_ENABLED=True,
        KRAKEN_READ_ONLY_MODE=False,
        KRAKEN_DRY_RUN_MODE=False,
        KRAKEN_SUBMISSION_ENABLED=True,
        KRAKEN_SUBMISSION_AUTHORIZED=True,
        KRAKEN_ACCOUNT_IDENTIFIER="kraken-main",
        KRAKEN_API_KEY="kraken-key",
        KRAKEN_API_SECRET="a3Jha2VuLXNlY3JldA==",
    )
    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/0/private/CancelOrder":
            return {"error": [], "result": {"count": 1}}
        if method == "POST" and path == "/0/private/QueryOrders":
            return {
                "error": [],
                "result": {
                    "krk-1": {
                        "status": "canceled",
                        "vol": "0.01",
                        "vol_exec": "0",
                    }
                },
            }
        raise AssertionError((method, path, params, body, headers))

    adapter = KrakenExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    submitted = _submitted_order(
        venue=Venue.KRAKEN.value,
        instrument_ref_id=instrument_ref_id,
        symbol="BTC",
        exchange_order_id="krk-1",
    )

    canceled = asyncio.run(adapter.cancel_order(submitted))
    assert canceled.status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
    assert canceled.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING

    reconciled = asyncio.run(
        adapter.reconcile_submitted_order(
            replace(
                submitted,
                status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
                cancelable_in_principle=False,
                amendable_in_principle=False,
            )
        )
    )
    assert reconciled.status == SubmittedOrderStatus.CANCELED
    assert reconciled.status_reason_code == "reconciliation_canceled"


def test_kraken_amend_updates_working_limit_order_without_claiming_final_state() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id = _seed_symbol(
        session_factory,
        venue=Venue.KRAKEN.value,
        symbol="BTC",
        exchange_symbol="XBT/USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        quote_asset="USD",
        settlement_asset=None,
    )
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.KRAKEN.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        KRAKEN_ENABLED=True,
        KRAKEN_READ_ONLY_MODE=False,
        KRAKEN_DRY_RUN_MODE=False,
        KRAKEN_SUBMISSION_ENABLED=True,
        KRAKEN_SUBMISSION_AUTHORIZED=True,
        KRAKEN_ACCOUNT_IDENTIFIER="kraken-main",
        KRAKEN_API_KEY="kraken-key",
        KRAKEN_API_SECRET="a3Jha2VuLXNlY3JldA==",
    )

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "POST" and path == "/0/private/AmendOrder":
            return {"error": [], "result": {"status": "ok"}}
        raise AssertionError((method, path, params, body, headers))

    adapter = KrakenExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    submitted = _submitted_order(
        venue=Venue.KRAKEN.value,
        instrument_ref_id=instrument_ref_id,
        symbol="BTC",
        exchange_order_id="krk-amend-1",
        quantity="0.01",
    )

    amended = asyncio.run(
        adapter.amend_order(
            submitted,
            new_quantity=Decimal("0.02"),
            new_limit_price=Decimal("100500"),
        )
    )

    assert amended.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert amended.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
    assert amended.original_quantity == Decimal("0.02")
    assert amended.remaining_quantity == Decimal("0.02")
    assert amended.limit_price == Decimal("100500")
    assert amended.status_reason_code == "amend_acknowledged"


def test_kraken_amend_rejects_quantity_below_filled_scope() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id = _seed_symbol(
        session_factory,
        venue=Venue.KRAKEN.value,
        symbol="BTC",
        exchange_symbol="XBT/USD",
        market_type=MarketType.SPOT,
        product_type=ProductType.SPOT,
        quote_asset="USD",
        settlement_asset=None,
    )
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.KRAKEN.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        KRAKEN_ENABLED=True,
        KRAKEN_READ_ONLY_MODE=False,
        KRAKEN_DRY_RUN_MODE=False,
        KRAKEN_SUBMISSION_ENABLED=True,
        KRAKEN_SUBMISSION_AUTHORIZED=True,
        KRAKEN_ACCOUNT_IDENTIFIER="kraken-main",
        KRAKEN_API_KEY="kraken-key",
        KRAKEN_API_SECRET="a3Jha2VuLXNlY3JldA==",
    )

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        raise AssertionError((method, path, params, body, headers))

    adapter = KrakenExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    submitted = replace(
        _submitted_order(
            venue=Venue.KRAKEN.value,
            instrument_ref_id=instrument_ref_id,
            symbol="BTC",
            exchange_order_id="krk-amend-2",
            quantity="0.01",
        ),
        filled_quantity=Decimal("0.005"),
        remaining_quantity=Decimal("0.005"),
    )

    rejected = asyncio.run(
        adapter.amend_order(
            submitted,
            new_quantity=Decimal("0.004"),
        )
    )

    assert rejected.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert rejected.event_type == "amend_rejected"
    assert rejected.status_reason_code == "amend_quantity_below_filled"
    assert "amend_quantity_below_filled" in rejected.reason_codes


def test_aster_canceled_after_partial_execution_is_not_masked_as_partial_fill() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id = _seed_symbol(
        session_factory,
        venue=Venue.ASTER.value,
        symbol="BTC",
        exchange_symbol="BTCUSDT",
        market_type=MarketType.PERPETUAL,
        product_type=ProductType.LINEAR,
        quote_asset="USDT",
        settlement_asset="USDT",
    )
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.ASTER.value,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        ASTER_ENABLED=True,
        ASTER_READ_ONLY_MODE=False,
        ASTER_DRY_RUN_MODE=False,
        ASTER_SUBMISSION_ENABLED=True,
        ASTER_SUBMISSION_AUTHORIZED=True,
        ASTER_ACCOUNT_IDENTIFIER="aster-main",
        ASTER_API_KEY="aster-key",
        ASTER_API_SECRET="aster-secret",
    )

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v1/order":
            return {
                "symbol": "BTCUSDT",
                "status": "CANCELED",
                "origQty": "0.01",
                "executedQty": "0.004",
                "avgPrice": "100100",
                "updateTime": 1710000000000,
            }
        raise AssertionError((method, path, params, body, headers))

    adapter = AsterExchangeAdapter(settings, transport=_transport, session_factory=session_factory)
    reconciled = asyncio.run(
        adapter.reconcile_submitted_order(
            _submitted_order(
                venue=Venue.ASTER.value,
                instrument_ref_id=instrument_ref_id,
                symbol="BTC",
                exchange_order_id="aster-1",
            )
        )
    )

    assert reconciled.status == SubmittedOrderStatus.CANCELED
    assert reconciled.status_reason_code == "reconciliation_canceled"
    assert reconciled.filled_quantity == Decimal("0.004")
    assert reconciled.remaining_quantity == Decimal("0.006")
    assert reconciled.average_fill_price == Decimal("100100")


def test_api_exposes_recovery_actionability_and_cancel() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/fapi/v2/balance":
            return [
                {
                    "balance": "1000",
                    "availableBalance": "800",
                    "crossWalletBalance": "200",
                    "crossUnPnl": "10",
                    "maxWithdrawAmount": "800",
                }
            ]
        if method == "POST" and path == "/fapi/v1/order":
            parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
            return {
                "orderId": "aster-order-45",
                "clientOrderId": parsed.get("newClientOrderId"),
                "status": "accepted",
            }
        if method == "DELETE" and path == "/fapi/v1/order":
            return {"orderId": "aster-order-45", "status": "CANCELED"}
        raise AssertionError((method, path, params, body, headers))

    execution = _build_aster_execution_service(session_factory, transport=_transport)
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    client = TestClient(app)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        actionability = client.get(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/actionability")
        cancel = client.post(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/cancel")
        recovery = client.get(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/recovery")
    finally:
        app.dependency_overrides.clear()

    assert actionability.status_code == 200
    assert actionability.json()["cancel_supported"] is True
    assert actionability.json()["cancel_allowed_now"] is True
    assert actionability.json()["amend_supported"] is False
    assert cancel.status_code == 200
    assert cancel.json()["status"] == SubmittedOrderStatus.CANCELED.value
    assert recovery.status_code == 200
    assert recovery.json()["category"] == SubmittedOrderRecoveryCategory.NO_ACTION_REQUIRED.value


def test_api_exposes_okx_amend_and_recovery_execute() -> None:
    session_factory = build_test_session_factory()
    amend_order_id = _seed_okx_submitted_order(session_factory, suffix="api-amend", api_key="okx-key-api-amend")
    retry_order_id = _seed_okx_submitted_order(session_factory, suffix="api-retry", api_key="okx-key-api-retry")
    _mark_submitted_order_retryable_rejected(session_factory, retry_order_id)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v5/account/balance":
            return {
                "code": "0",
                "data": [{"totalEq": "1000", "availEq": "800", "upl": "0", "notionalUsd": "0"}],
            }
        if method == "GET" and path == "/api/v5/trade/orders-pending":
            return {"code": "0", "data": []}
        if method == "GET" and path == "/api/v5/trade/fills":
            return {"code": "0", "data": []}
        if method == "POST" and path == "/api/v5/trade/amend-order":
            return {"code": "0", "data": [{"sCode": "0", "sMsg": ""}]}
        if method == "POST" and path == "/api/v5/trade/order":
            return {
                "code": "0",
                "data": [{"ordId": "okx-order-api-retry-new", "clOrdId": "mf-api-retry"}],
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)

    client = TestClient(app)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        amend = client.post(
            f"/api/v1/submitted-orders/{amend_order_id}/amend",
            json={"limit_price": 100750.0},
        )
        recover = client.post(
            f"/api/v1/submitted-orders/{retry_order_id}/recovery/execute",
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert amend.status_code == 200
    assert amend.json()["limit_price"] == 100750.0
    assert amend.json()["status"] == SubmittedOrderStatus.ACKNOWLEDGED.value
    assert recover.status_code == 200
    assert recover.json()["action"] == "retry_same_target"
    assert recover.json()["executed"] is True
    assert recover.json()["resulting_order"]["status"] == SubmittedOrderStatus.ACKNOWLEDGED.value
