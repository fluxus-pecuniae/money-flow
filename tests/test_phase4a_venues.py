from __future__ import annotations

import asyncio
import base64
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config.settings import AppSettings
from core.domain.enums import Environment, MarketType, Venue, VenueSupportLevel
from core.domain.models import VenueCapabilities
from db.base import Base
from db.models import InstrumentModel, SymbolModel  # noqa: F401
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.base import VenueAdapterError
from services.exchange.binance.adapter import BinanceExchangeAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.kraken.adapter import KrakenExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _settings(**overrides: object) -> AppSettings:
    defaults = {
        "APP_ENV": Environment.TESTNET,
        "EXCHANGE_USE_TESTNET": True,
        "EXCHANGE_ACCOUNT_ADDRESS": "0xabc123",
        "EXCHANGE_ACCOUNT_LABEL": "primary",
    }
    defaults.update(overrides)
    return AppSettings(**defaults)


def _coinbase_test_private_key_pem() -> str:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _aster_transport(method: str, path: str, params: dict[str, object] | None):
    async def _impl():
        if path == "/fapi/v1/exchangeInfo":
            return {
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "contractType": "PERPETUAL",
                        "status": "TRADING",
                        "baseAsset": "BTC",
                        "quoteAsset": "USDT",
                        "filters": [
                            {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                            {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                        ],
                    }
                ]
            }
        if path == "/fapi/v1/klines":
            return [
                [1710000000000, "100", "101", "99", "100.5", "50"],
                [1710000900000, "100.5", "102", "100", "101.5", "55"],
            ]
        if path == "/fapi/v1/ticker/bookTicker":
            return {"bidPrice": "100", "bidQty": "2", "askPrice": "101", "askQty": "3"}
        if path == "/fapi/v2/balance":
            return [
                {
                    "balance": "1000",
                    "availableBalance": "700",
                    "crossWalletBalance": "300",
                    "crossUnPnl": "10",
                    "maxWithdrawAmount": "900",
                }
            ]
        if path == "/fapi/v1/ping":
            return {}
        raise AssertionError((method, path, params))

    return _impl()


def _okx_transport(method: str, path: str, params: dict[str, object] | None):
    async def _impl():
        if path == "/api/v5/public/instruments":
            inst_type = params["instType"] if params else None
            if inst_type == "SPOT":
                return {
                    "data": [
                        {
                            "instId": "BTC-USD",
                            "instType": "SPOT",
                            "baseCcy": "BTC",
                            "quoteCcy": "USD",
                            "tickSz": "0.1",
                            "lotSz": "0.0001",
                            "minSz": "0.0001",
                            "state": "live",
                        }
                    ]
                }
            if inst_type == "SWAP":
                return {
                    "data": [
                        {
                            "instId": "BTC-USDT-SWAP",
                            "instType": "SWAP",
                            "baseCcy": "BTC",
                            "quoteCcy": "USDT",
                            "settleCcy": "USDT",
                            "tickSz": "0.1",
                            "lotSz": "0.001",
                            "minSz": "0.001",
                            "state": "live",
                        }
                    ]
                }
        if path == "/api/v5/market/candles":
            return {"data": [["1710000900000", "100", "102", "99", "101", "40"]]}
        if path == "/api/v5/market/books":
            return {"data": [{"bids": [["100", "2"]], "asks": [["101", "3"]]}]}
        if path == "/api/v5/account/balance":
            return {
                "data": [
                    {
                        "totalEq": "1000",
                        "availEq": "650",
                        "imr": "100",
                        "upl": "20",
                        "notionalUsd": "400",
                        "details": [{"availEq": "650"}],
                    }
                ]
            }
        if path == "/api/v5/public/time":
            return {"data": [{"ts": "1710000000000"}]}
        raise AssertionError((method, path, params))

    return _impl()


def _coinbase_transport(method: str, path: str, params: dict[str, object] | None):
    async def _impl():
        if path == "/api/v3/brokerage/products":
            return {
                "products": [
                    {
                        "product_id": "BTC-USD",
                        "product_type": "SPOT",
                        "base_currency_id": "BTC",
                        "quote_currency_id": "USD",
                        "quote_increment": "0.01",
                        "base_increment": "0.00000001",
                        "base_min_size": "0.0001",
                        "trading_disabled": False,
                    }
                ]
            }
        if path.endswith("/candles"):
            return {
                "candles": [
                    {
                        "start": "1710000000",
                        "open": "100",
                        "high": "103",
                        "low": "99",
                        "close": "102",
                        "volume": "25",
                    }
                ]
            }
        if path == "/api/v3/brokerage/best_bid_ask":
            return {
                "pricebooks": [
                    {
                        "bids": [{"price": "100", "size": "1.5"}],
                        "asks": [{"price": "101", "size": "1.0"}],
                    }
                ]
            }
        if path == "/api/v3/brokerage/accounts":
            return {"accounts": [{"available_balance": {"value": "500"}}]}
        if path == "/api/v3/brokerage/time":
            return {"iso": "2026-04-05T00:00:00Z"}
        raise AssertionError((method, path, params))

    return _impl()


def _binance_transport(method: str, path: str, params: dict[str, object] | None):
    async def _impl():
        if path == "/api/v3/exchangeInfo":
            return {
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "status": "TRADING",
                        "baseAsset": "BTC",
                        "quoteAsset": "USDT",
                        "filters": [
                            {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                            {"filterType": "LOT_SIZE", "stepSize": "0.0001", "minQty": "0.0001"},
                        ],
                    }
                ]
            }
        if path == "/api/v3/klines":
            return [[1710000000000, "100", "101", "99", "100.5", "50"]]
        if path == "/api/v3/ticker/bookTicker":
            return {"bidPrice": "100", "bidQty": "2", "askPrice": "101", "askQty": "3"}
        if path == "/api/v3/account":
            return {"balances": [{"asset": "USDT", "free": "800", "locked": "50"}]}
        if path == "/api/v3/ping":
            return {}
        raise AssertionError((method, path, params))

    return _impl()


def _kraken_transport(method: str, path: str, params: dict[str, object] | None):
    async def _impl():
        if path == "/0/public/AssetPairs":
            return {
                "result": {
                    "XXBTZUSD": {
                        "base": "XXBT",
                        "quote": "ZUSD",
                        "ordermin": "0.0001",
                        "tick_size": "0.1",
                    }
                }
            }
        if path == "/0/public/OHLC":
            return {"result": {"XXBTZUSD": [[1710000000, "100", "102", "99", "101", "100.5", "25", 12]]}}
        if path == "/0/public/Depth":
            return {"result": {"XXBTZUSD": {"bids": [["100", "2"]], "asks": [["101", "3"]]}}}
        if path == "/0/private/Balance":
            return {"result": {"ZUSD": "900"}}
        if path == "/0/public/Time":
            return {"result": {"unixtime": 1710000000}}
        raise AssertionError((method, path, params))

    return _impl()


def test_venue_registry_lists_all_supported_venues_and_keeps_submission_authorization_conservative() -> None:
    registry = DefaultVenueRegistryService(_settings())
    summaries = asyncio.run(registry.list_supported_venues())
    by_venue = {item.venue: item for item in summaries}

    assert set(by_venue) >= {
        Venue.HYPERLIQUID.value,
        Venue.ASTER.value,
        Venue.BINANCE.value,
        Venue.OKX.value,
        Venue.COINBASE_ADVANCED_TRADE.value,
        Venue.KRAKEN.value,
    }
    assert by_venue[Venue.HYPERLIQUID.value].execution_authorized is False
    assert by_venue[Venue.OKX.value].execution_authorized is False
    assert by_venue[Venue.HYPERLIQUID.value].adapter_submission_implemented is True
    assert by_venue[Venue.HYPERLIQUID.value].submission_enabled is False
    assert by_venue[Venue.HYPERLIQUID.value].live_submission_phase_enabled is False
    assert by_venue[Venue.ASTER.value].support_level == VenueSupportLevel.EXECUTION_PREPARABLE

    assert isinstance(asyncio.run(registry.get_adapter(Venue.HYPERLIQUID.value)), HyperliquidExchangeAdapter)
    assert isinstance(asyncio.run(registry.get_adapter(Venue.ASTER.value)), AsterExchangeAdapter)
    assert isinstance(asyncio.run(registry.get_adapter(Venue.BINANCE.value)), BinanceExchangeAdapter)
    assert isinstance(asyncio.run(registry.get_adapter(Venue.OKX.value)), OkxExchangeAdapter)
    assert isinstance(
        asyncio.run(registry.get_adapter(Venue.COINBASE_ADVANCED_TRADE.value)),
        CoinbaseAdvancedTradeExchangeAdapter,
    )
    assert isinstance(asyncio.run(registry.get_adapter(Venue.KRAKEN.value)), KrakenExchangeAdapter)


def test_aster_okx_and_coinbase_adapters_are_execution_preparable_and_parse_distinct_account_shapes() -> None:
    session_factory = _session_factory()

    aster = AsterExchangeAdapter(
        _settings(
            ASTER_CREDENTIALS_REF="secret://aster",
            ASTER_ACCOUNT_IDENTIFIER="aster-main",
            ASTER_API_KEY="aster-key",
            ASTER_API_SECRET="aster-secret",
        ),
        transport=_aster_transport,
        session_factory=session_factory,
    )
    okx = OkxExchangeAdapter(
        _settings(
            OKX_CREDENTIALS_REF="secret://okx",
            OKX_ACCOUNT_IDENTIFIER="okx-main",
            OKX_SUBACCOUNT_LABEL="desk-a",
            OKX_API_KEY="okx-key",
            OKX_API_SECRET="okx-secret",
            OKX_API_PASSPHRASE="okx-pass",
        ),
        transport=_okx_transport,
        session_factory=session_factory,
    )
    coinbase = CoinbaseAdvancedTradeExchangeAdapter(
        _settings(
            COINBASE_ADVANCED_CREDENTIALS_REF="secret://coinbase",
            COINBASE_ADVANCED_ACCOUNT_IDENTIFIER="cb-brokerage",
            COINBASE_ADVANCED_JWT_KEY_NAME="organizations/test/apiKeys/read-only",
            COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=_coinbase_test_private_key_pem(),
        ),
        transport=_coinbase_transport,
        session_factory=session_factory,
    )

    aster_symbols = asyncio.run(aster.sync_symbols())
    okx_symbols = asyncio.run(okx.sync_symbols())
    coinbase_symbols = asyncio.run(coinbase.sync_symbols())

    assert aster_symbols[0].symbol == "BTC"
    assert any(symbol.market_type.value == "spot" for symbol in okx_symbols)
    assert coinbase_symbols[0].exchange_symbol == "BTC-USD"

    aster_connectivity = asyncio.run(aster.get_account_connectivity())
    okx_connectivity = asyncio.run(okx.get_account_connectivity())
    coinbase_connectivity = asyncio.run(coinbase.get_account_connectivity())
    assert aster_connectivity.account_model == "api_account"
    assert okx_connectivity.account_model == "account_with_subaccounts"
    assert okx_connectivity.subaccount_label == "desk-a"
    assert coinbase_connectivity.account_model == "brokerage_account"

    okx_capabilities = asyncio.run(okx.get_venue_capabilities())
    coinbase_capabilities = asyncio.run(coinbase.get_venue_capabilities())
    assert isinstance(okx_capabilities, VenueCapabilities)
    assert okx_capabilities.support_level == VenueSupportLevel.EXECUTION_PREPARABLE
    assert okx_capabilities.supports_options is True
    assert okx_capabilities.supports_order_preview is True
    assert coinbase_capabilities.supports_spot is True
    assert coinbase_capabilities.supports_perpetuals is False

    assert asyncio.run(aster.get_top_of_book("BTC")) is not None
    assert asyncio.run(okx.get_top_of_book("BTC")) is not None
    assert asyncio.run(coinbase.get_top_of_book("BTC")) is not None

    assert asyncio.run(aster.read_account_snapshot()) is not None
    assert asyncio.run(okx.read_account_snapshot()) is not None
    assert asyncio.run(coinbase.read_account_snapshot()) is not None

    for adapter in (aster, okx, coinbase):
        try:
            asyncio.run(adapter.submit_order(None))  # type: ignore[arg-type]
        except VenueAdapterError:
            pass
        else:
            raise AssertionError("read-only adapter unexpectedly accepted submit_order")


def test_binance_and_kraken_adapters_join_the_current_maturity_branch_honestly() -> None:
    session_factory = _session_factory()

    binance = BinanceExchangeAdapter(
        _settings(
            BINANCE_CREDENTIALS_REF="secret://binance",
            BINANCE_ACCOUNT_IDENTIFIER="binance-main",
            BINANCE_API_KEY="binance-key",
            BINANCE_API_SECRET="binance-secret",
        ),
        transport=_binance_transport,
        session_factory=session_factory,
    )
    kraken = KrakenExchangeAdapter(
        _settings(
            KRAKEN_CREDENTIALS_REF="secret://kraken",
            KRAKEN_ACCOUNT_IDENTIFIER="kraken-main",
            KRAKEN_API_KEY="kraken-key",
            KRAKEN_API_SECRET=base64.b64encode(b"kraken-secret").decode("ascii"),
        ),
        transport=_kraken_transport,
        session_factory=session_factory,
    )

    binance_symbols = asyncio.run(binance.sync_symbols())
    kraken_symbols = asyncio.run(kraken.sync_symbols())
    assert binance_symbols[0].exchange_symbol == "BTCUSDT"
    assert kraken_symbols[0].exchange_symbol == "XXBTZUSD"

    binance_capabilities = asyncio.run(binance.get_venue_capabilities())
    kraken_capabilities = asyncio.run(kraken.get_venue_capabilities())
    assert binance_capabilities.support_level == VenueSupportLevel.EXECUTION_PREPARABLE
    assert kraken_capabilities.support_level == VenueSupportLevel.EXECUTION_PREPARABLE
    assert binance_capabilities.adapter_supports_order_submission is True
    assert kraken_capabilities.adapter_supports_order_submission is True

    assert asyncio.run(binance.get_top_of_book("BTC")) is not None
    assert asyncio.run(kraken.get_top_of_book("BTC")) is not None
    assert asyncio.run(binance.read_account_snapshot()) is not None
    assert asyncio.run(kraken.read_account_snapshot()) is not None


def test_cross_venue_catalog_sync_reuses_canonical_instrument_identity_for_same_perpetual() -> None:
    session_factory = _session_factory()
    aster = AsterExchangeAdapter(_settings(), transport=_aster_transport, session_factory=session_factory)
    okx = OkxExchangeAdapter(_settings(), transport=_okx_transport, session_factory=session_factory)

    asyncio.run(aster.sync_symbols())
    asyncio.run(okx.sync_symbols())

    with session_factory() as session:
        instruments = session.scalars(
            select(InstrumentModel).where(InstrumentModel.base_asset == "BTC")
        ).all()
        perp_instruments = [
            instrument
            for instrument in instruments
            if instrument.market_type.value == "perpetual" and instrument.quote_asset == "USDT"
        ]
        venue_symbols = session.scalars(
            select(SymbolModel).where(
                SymbolModel.base_asset == "BTC",
                SymbolModel.venue.in_([Venue.ASTER.value, Venue.OKX.value]),
                SymbolModel.market_type == MarketType.PERPETUAL,
            )
        ).all()

    assert len(perp_instruments) == 1
    assert len(venue_symbols) == 2
    assert venue_symbols[0].instrument_ref_id == venue_symbols[1].instrument_ref_id
