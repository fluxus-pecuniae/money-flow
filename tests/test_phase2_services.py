from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config.settings import AppSettings
from core.domain.enums import AttributionStatus, Environment, MarketType, ProductType, SubmittedOrderStatus, Timeframe
from db.base import Base
from db.models import (
    CandleModel,
    InstrumentModel,
    MarketDataCheckpointModel,
    PositionAttributionOverlayModel,
    PositionModel,
    SubmittedOrderModel,
    SymbolModel,
)
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.market_data.service import DefaultMarketDataService
from services.portfolio.service import DefaultPortfolioService


def build_test_session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def build_settings() -> AppSettings:
    return AppSettings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_USE_TESTNET=True,
        EXCHANGE_ACCOUNT_ADDRESS="acct",
        EXCHANGE_API_KEY="test-key",
        EXCHANGE_API_SECRET="test-secret",
        MARKET_DATA_CHECKPOINT_OVERLAP_BARS=1,
        PRIVATE_EXCHANGE_ENDPOINTS_ENABLED=True,
        EXCHANGE_ORDER_SUBMISSION_ENABLED=True,
    )


def build_transport() -> Callable[[dict[str, object]], Awaitable[object]]:
    async def transport(payload: dict[str, object]) -> object:
        request_type = payload["type"]
        if request_type == "allMids":
            return {"BTC": "50000.0"}
        if request_type == "meta":
            return {
                "universe": [
                    {
                        "name": "BTC",
                        "szDecimals": 3,
                        "maxLeverage": 50,
                        "onlyIsolated": False,
                    },
                    {
                        "name": "XYZ100",
                        "szDecimals": 2,
                        "maxLeverage": 20,
                        "onlyIsolated": True,
                        "isHip3": True,
                    },
                ]
            }
        if request_type == "candleSnapshot":
            return [
                {
                    "t": 1700000000000,
                    "T": 1700000900000,
                    "o": "50000",
                    "h": "50100",
                    "l": "49900",
                    "c": "50050",
                    "v": "123.45",
                },
                {
                    "t": 1700000900000,
                    "T": 1700001800000,
                    "o": "50050",
                    "h": "50200",
                    "l": "50010",
                    "c": "50150",
                    "v": "200.00",
                },
            ]
        if request_type == "clearinghouseState":
            return {
                "marginSummary": {
                    "accountValue": "10000",
                    "totalMarginUsed": "500",
                    "totalNtlPos": "2500",
                    "totalRawUsd": "9500",
                },
                "crossMarginSummary": {
                    "accountValue": "10000",
                    "totalMarginUsed": "500",
                    "totalNtlPos": "2500",
                    "totalRawUsd": "9500",
                },
                "assetPositions": [
                    {
                        "position": {
                            "coin": "BTC",
                            "entryPx": "50000",
                            "marginUsed": "500",
                            "positionValue": "2500",
                            "liquidationPx": "45000",
                            "szi": "0.05",
                            "unrealizedPnl": "25",
                            "leverage": {"type": "cross", "value": 5},
                        },
                        "type": "oneWay",
                    }
                ],
                "withdrawable": "9500",
                "time": 1700002000000,
            }
        if request_type == "frontendOpenOrders":
            return [
                {
                    "coin": "BTC",
                    "side": "B",
                    "orderType": "Limit",
                    "limitPx": "49900",
                    "origSz": "0.05",
                    "sz": "0.05",
                    "reduceOnly": False,
                    "oid": 12345,
                    "timestamp": 1700002100000,
                }
            ]
        if request_type == "userFills":
            return [
                {
                    "coin": "BTC",
                    "side": "B",
                    "px": "50010",
                    "sz": "0.02",
                    "fee": "1.25",
                    "closedPnl": "0",
                    "oid": 12345,
                    "hash": "0xabc",
                    "time": 1700002200000,
                }
            ]
        raise AssertionError(f"Unexpected payload: {payload}")

    return transport


def test_universe_sync_catalogs_builder_assets_but_marks_them_ineligible_by_default() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    adapter = HyperliquidExchangeAdapter(
        settings,
        transport=build_transport(),
        session_factory=session_factory,
    )

    symbols = asyncio.run(adapter.sync_symbols())
    instruments = asyncio.run(adapter.list_instruments())

    assert {symbol.symbol for symbol in symbols} == {"BTC", "XYZ100"}
    assert len(instruments) == 2
    assert instruments[0].market_type == MarketType.PERPETUAL
    assert instruments[0].product_type == ProductType.LINEAR

    with session_factory() as session:
        venue_symbols = {model.symbol: model for model in session.scalars(select(SymbolModel)).all()}
        canonical = session.scalars(select(InstrumentModel)).all()
    assert len(canonical) == 2
    assert venue_symbols["BTC"].instrument_ref_id is not None
    assert venue_symbols["XYZ100"].is_builder_deployed is True
    assert venue_symbols["XYZ100"].is_strategy_eligible is False
    assert venue_symbols["XYZ100"].is_trading_eligible is False


def test_market_data_checkpoint_progression_is_explicit_and_overlap_safe() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    adapter = HyperliquidExchangeAdapter(
        settings,
        transport=build_transport(),
        session_factory=session_factory,
    )
    asyncio.run(adapter.sync_symbols())
    market_data = DefaultMarketDataService(adapter=adapter, settings=settings, session_factory=session_factory)

    asyncio.run(market_data.ingest_latest_candles("BTC", Timeframe.M15.value, limit=10))
    checkpoint = asyncio.run(market_data.get_checkpoint("BTC", Timeframe.M15.value))

    assert checkpoint is not None
    assert checkpoint.last_requested_start_time is not None
    assert checkpoint.last_requested_end_time is not None
    assert checkpoint.last_persisted_open_time == datetime.fromtimestamp(1700000900, tz=UTC)
    assert checkpoint.last_persisted_close_time == datetime.fromtimestamp(1700001800, tz=UTC)
    assert checkpoint.next_sync_start_time == checkpoint.last_persisted_open_time - timedelta(minutes=15)
    assert checkpoint.overlap_bars == 1

    asyncio.run(market_data.ingest_latest_candles("BTC", Timeframe.M15.value, limit=10))

    with session_factory() as session:
        candles = session.scalars(select(CandleModel)).all()
        checkpoint_model = session.scalar(select(MarketDataCheckpointModel))
    assert len(candles) == 2
    assert checkpoint_model is not None
    assert checkpoint_model.next_sync_start_time == checkpoint.next_sync_start_time.replace(tzinfo=None)


def test_portfolio_bootstrap_summary_uses_open_orders_and_latest_overlay_semantics() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    adapter = HyperliquidExchangeAdapter(
        settings,
        transport=build_transport(),
        session_factory=session_factory,
    )
    asyncio.run(adapter.sync_symbols())
    asyncio.run(adapter.sync_account_state())
    asyncio.run(adapter.reconcile_positions())
    asyncio.run(adapter.reconcile_open_orders())
    asyncio.run(adapter.reconcile_fills())

    with session_factory() as session:
        position = session.scalar(select(PositionModel))
        assert position is not None
        session.add(
            SubmittedOrderModel(
                environment=Environment.TESTNET,
                submitted_order_id="historic-filled-order",
                intent_id=None,
                client_order_id="historic-filled-order",
                venue="hyperliquid",
                account_address="acct",
                instrument_ref_id=position.instrument_ref_id,
                symbol_id=position.symbol_id,
                symbol="BTC",
                side=position.side,
                order_type=None,
                limit_price=None,
                original_quantity=position.quantity,
                remaining_quantity=0,
                reduce_only=False,
                exchange_order_id="99999",
                status=SubmittedOrderStatus.FILLED,
                submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
                acknowledged_at=datetime(2026, 1, 1, tzinfo=UTC),
                raw_payload={},
            )
        )
        session.add(
            PositionAttributionOverlayModel(
                overlay_id="old-overlay",
                environment=Environment.TESTNET,
                venue="hyperliquid",
                position_id=position.position_id,
                sleeve_id="sleeve_15m",
                attributed_quantity=position.quantity,
                attributed_notional=Decimal("2500"),
                as_of=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        session.add(
            PositionAttributionOverlayModel(
                overlay_id="latest-overlay",
                environment=Environment.TESTNET,
                venue="hyperliquid",
                position_id=position.position_id,
                sleeve_id="sleeve_15m",
                attributed_quantity=Decimal("0"),
                attributed_notional=Decimal("0"),
                as_of=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        session.commit()

    portfolio = DefaultPortfolioService(settings, session_factory=session_factory)
    summary = asyncio.run(portfolio.get_bootstrap_summary())

    assert summary.open_positions == 1
    assert summary.open_orders == 1
    assert summary.recent_submitted_orders == 2
    assert summary.recent_fills == 1
    assert summary.unattributed_positions == 1

    with session_factory() as session:
        position = session.scalar(select(PositionModel))
        order = session.scalar(select(SubmittedOrderModel).where(SubmittedOrderModel.exchange_order_id == "12345"))
    assert position is not None
    assert position.sleeve_id is None
    assert position.attribution_status == AttributionStatus.UNASSIGNED
    assert position.account_position_key
    assert order is not None
    assert order.instrument_ref_id is not None
