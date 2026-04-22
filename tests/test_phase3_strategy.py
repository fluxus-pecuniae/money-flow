from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.dependencies import get_indicator_service, get_market_data_service, get_strategy_engine
from apps.api.app.main import app
from core.config.settings import AppSettings
from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    MarketType,
    OrderSide,
    PositionStatus,
    ProductType,
    StrategyDecisionStatus,
    Timeframe,
)
from db.base import Base
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
from services.indicators.service import DefaultIndicatorService
from services.market_data.service import DefaultMarketDataService
from services.strategy.engine import MandateStrategyEngine


def build_test_session_factory():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def build_settings(**overrides: object) -> AppSettings:
    base = {
        "APP_ENV": Environment.TESTNET,
        "EXCHANGE_USE_TESTNET": True,
        "EXCHANGE_VENUE": "hyperliquid",
        "EXCHANGE_ACCOUNT_ADDRESS": "acct",
        "EXCHANGE_ACCOUNT_LABEL": "primary",
        "MARKET_DATA_STALE_AFTER_SECONDS": 10_000,
    }
    base.update(overrides)
    return AppSettings(_env_file=None, **base)


def seed_symbol(
    session_factory,
    symbol: str = "BTC",
    *,
    is_strategy_eligible: bool = True,
) -> tuple[str, str, str]:
    instrument_key = f"perpetual:linear:{symbol}:USDC:USDC"
    with session_factory() as session:
        instrument = InstrumentModel(
            instrument_key=instrument_key,
            canonical_symbol=symbol,
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset=symbol,
            quote_asset="USDC",
            settlement_asset="USDC",
            is_active=True,
        )
        session.add(instrument)
        session.flush()
        symbol_model = SymbolModel(
            instrument_ref_id=instrument.id,
            venue="hyperliquid",
            symbol=symbol,
            exchange_symbol=symbol,
            venue_asset_id="0",
            asset_id=0,
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset=symbol,
            quote_asset="USDC",
            settlement_asset="USDC",
            price_tick_size=Decimal("0.1"),
            quantity_step_size=Decimal("0.001"),
            min_order_size=Decimal("0.001"),
            size_decimals=3,
            max_leverage=20,
            only_isolated=False,
            is_perpetual=True,
            is_builder_deployed=False,
            is_strategy_eligible=is_strategy_eligible,
            is_trading_eligible=is_strategy_eligible,
            is_active=True,
            raw_metadata={},
        )
        session.add(symbol_model)
        session.commit()
        return instrument.id, symbol_model.id, instrument_key


def seed_candles(
    session_factory,
    *,
    instrument_ref_id: str,
    symbol_id: str,
    symbol: str,
    timeframe: Timeframe,
    closes: list[Decimal],
) -> tuple[datetime, timedelta]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    delta = {
        Timeframe.M15: timedelta(minutes=15),
        Timeframe.H1: timedelta(hours=1),
        Timeframe.H4: timedelta(hours=4),
    }[timeframe]
    with session_factory() as session:
        for index, close in enumerate(closes):
            open_time = start + (delta * index)
            close_time = open_time + delta
            open_price = closes[index - 1] if index > 0 else close
            high = max(open_price, close) + Decimal("0.2")
            low = min(open_price, close) - Decimal("0.2")
            session.add(
                CandleModel(
                    environment=Environment.TESTNET,
                    venue="hyperliquid",
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=symbol_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=open_time,
                    close_time=close_time,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=Decimal("100"),
                    trade_count=10,
                )
            )
        session.add(
            MarketDataHealthModel(
                environment=Environment.TESTNET,
                venue="hyperliquid",
                symbol=symbol,
                timeframe=timeframe,
                last_candle_open_time=start + (delta * (len(closes) - 1)),
                last_candle_close_time=start + (delta * len(closes)),
                last_synced_at=datetime.now(UTC),
                last_success_at=datetime.now(UTC),
                stale_after_seconds=10_000,
                is_stale=False,
                last_error=None,
            )
        )
        session.commit()
    return start, delta


def seed_open_position(
    session_factory,
    *,
    instrument_ref_id: str,
    symbol_id: str,
    symbol: str,
    quantity: Decimal = Decimal("0.05"),
    avg_entry_price: Decimal = Decimal("100"),
    mark_price: Decimal = Decimal("101"),
) -> None:
    with session_factory() as session:
        session.add(
            PositionModel(
                environment=Environment.TESTNET,
                position_id=f"pos-{symbol}",
                exchange_position_key=f"{symbol}-one-way",
                account_position_key=f"testnet:hyperliquid:acct:{instrument_ref_id}:one_way",
                sleeve_id=None,
                venue="hyperliquid",
                account_address="acct",
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol=symbol,
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                attribution_status=AttributionStatus.UNASSIGNED,
                quantity=quantity,
                avg_entry_price=avg_entry_price,
                mark_price=mark_price,
                unrealized_pnl=Decimal("1"),
                position_value=quantity * mark_price,
                margin_used=Decimal("10"),
                liquidation_price=Decimal("80"),
                leverage_type="cross",
                leverage_value=5,
                raw_payload={"position": {"coin": symbol}},
                opened_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        session.commit()


def bullish_closes() -> list[Decimal]:
    return [
        Decimal("100"),
        Decimal("100.8"),
        Decimal("101.4"),
        Decimal("101.1"),
        Decimal("102.0"),
        Decimal("102.8"),
        Decimal("103.4"),
        Decimal("103.1"),
        Decimal("104.0"),
        Decimal("104.7"),
        Decimal("105.2"),
        Decimal("104.9"),
        Decimal("105.8"),
        Decimal("106.4"),
        Decimal("107.0"),
        Decimal("106.7"),
        Decimal("107.5"),
        Decimal("108.2"),
        Decimal("108.9"),
        Decimal("108.6"),
        Decimal("109.4"),
        Decimal("110.0"),
        Decimal("110.7"),
        Decimal("110.4"),
        Decimal("111.2"),
        Decimal("111.8"),
        Decimal("112.3"),
        Decimal("112.0"),
        Decimal("112.9"),
        Decimal("113.5"),
        Decimal("114.0"),
        Decimal("113.7"),
        Decimal("114.4"),
        Decimal("114.9"),
        Decimal("114.6"),
        Decimal("115.1"),
        Decimal("115.6"),
        Decimal("116.0"),
        Decimal("115.8"),
        Decimal("116.2"),
    ]


def overextended_closes() -> list[Decimal]:
    return [Decimal(str(100 + i * 1.8)) for i in range(40)]


def bearish_break_closes() -> list[Decimal]:
    return [
        Decimal("120"),
        Decimal("121"),
        Decimal("122"),
        Decimal("123"),
        Decimal("124"),
        Decimal("125"),
        Decimal("124"),
        Decimal("123"),
        Decimal("122"),
        Decimal("121"),
        Decimal("120"),
        Decimal("119"),
        Decimal("118"),
        Decimal("117"),
        Decimal("116"),
        Decimal("115"),
        Decimal("114"),
        Decimal("113"),
        Decimal("112"),
        Decimal("111"),
        Decimal("110"),
        Decimal("109"),
        Decimal("108"),
        Decimal("107"),
        Decimal("106"),
        Decimal("105"),
        Decimal("104"),
        Decimal("103"),
        Decimal("102"),
        Decimal("101"),
        Decimal("100"),
        Decimal("99"),
        Decimal("98"),
        Decimal("97"),
        Decimal("96"),
        Decimal("95"),
        Decimal("94"),
        Decimal("93"),
        Decimal("92"),
        Decimal("91"),
    ]


def build_engine(settings: AppSettings, session_factory) -> MandateStrategyEngine:
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    market_data_service = DefaultMarketDataService(settings=settings, session_factory=session_factory)
    return MandateStrategyEngine(
        indicator_service=indicator_service,
        market_data_service=market_data_service,
        settings=settings,
        session_factory=session_factory,
    )


def test_indicator_computation_and_idempotent_persistence() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=bullish_closes(),
    )
    service = DefaultIndicatorService(settings, session_factory=session_factory)

    persisted_first = asyncio.run(
        service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.M15.value)
    )
    persisted_second = asyncio.run(
        service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.M15.value)
    )
    latest = asyncio.run(service.load_latest_snapshot(instrument_ref_id, "hyperliquid", Timeframe.M15.value))

    assert persisted_first > 0
    assert persisted_second == 0
    assert latest is not None
    assert latest.instrument_key == instrument_key
    assert latest.sma_20 == Decimal("113.225000000000")

    with session_factory() as session:
        count = session.scalar(select(func.count()).select_from(IndicatorSnapshotModel))
    assert count == persisted_first


def test_stale_indicator_snapshot_is_rejected() -> None:
    settings = build_settings(MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION=False)
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=bullish_closes(),
    )
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    asyncio.run(indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.M15.value))
    with session_factory() as session:
        session.add(
            CandleModel(
                environment=Environment.TESTNET,
                venue="hyperliquid",
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol="BTC",
                timeframe=Timeframe.M15,
                open_time=start + (delta * 40),
                close_time=start + (delta * 41),
                open=Decimal("116.2"),
                high=Decimal("116.5"),
                low=Decimal("116.0"),
                close=Decimal("116.4"),
                volume=Decimal("100"),
                trade_count=10,
            )
        )
        health = session.scalar(select(MarketDataHealthModel))
        assert health is not None
        health.last_candle_open_time = start + (delta * 40)
        health.last_candle_close_time = start + (delta * 41)
        session.commit()

    engine = build_engine(settings, session_factory)
    result = asyncio.run(engine.evaluate_sleeve("sleeve_15m", symbols=["BTC"]))

    assert result[0].decision.status == StrategyDecisionStatus.INVALID
    assert result[0].decision.reason_code == "stale_indicator_snapshot"


def test_strategy_evaluation_is_idempotent_on_unchanged_state() -> None:
    settings = build_settings(
        MONEY_FLOW_15M_RSI_CEILING=90.0,
        MONEY_FLOW_15M_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION=False,
    )
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=bullish_closes(),
    )
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    asyncio.run(indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.M15.value))
    engine = build_engine(settings, session_factory)

    first = asyncio.run(engine.evaluate_sleeve("sleeve_15m", symbols=["BTC"]))
    second = asyncio.run(engine.evaluate_sleeve("sleeve_15m", symbols=["BTC"]))

    assert first[0].decision.evaluation_key == second[0].decision.evaluation_key
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SignalEventModel)) == 1
        assert session.scalar(select(func.count()).select_from(StrategyDecisionModel)) == 1


def test_money_flow_1h_entry_path() -> None:
    settings = build_settings(
        MONEY_FLOW_1H_RSI_CEILING=90.0,
        MONEY_FLOW_1H_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_1H_REQUIRE_MACD_CONFIRMATION=False,
    )
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.H1,
        closes=bullish_closes(),
    )
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    asyncio.run(indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.H1.value))
    engine = build_engine(settings, session_factory)

    result = asyncio.run(engine.evaluate_sleeve("sleeve_1h", symbols=["BTC"]))

    assert result[0].decision.status == StrategyDecisionStatus.PROPOSED
    assert result[0].decision.action == DecisionAction.OPEN


def test_money_flow_4h_close_path_with_existing_position() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.H4,
        closes=bearish_break_closes(),
    )
    seed_open_position(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
    )
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    asyncio.run(indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.H4.value))
    engine = build_engine(settings, session_factory)

    result = asyncio.run(engine.evaluate_sleeve("sleeve_4h", symbols=["BTC"]))

    assert result[0].decision.status == StrategyDecisionStatus.PROPOSED
    assert result[0].decision.action == DecisionAction.CLOSE
    assert result[0].decision.reason_code in {"ma_alignment_break", "trend_invalidated", "macd_rollover"}


def test_money_flow_reduce_and_hold_paths_with_existing_position() -> None:
    reduce_settings = build_settings(
        MONEY_FLOW_1H_CLOSE_ON_MA_BREAK=False,
        MONEY_FLOW_1H_CLOSE_ON_MACD_ROLLOVER=False,
        MONEY_FLOW_1H_TRIM_RSI=65.0,
    )
    reduce_session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(reduce_session_factory)
    seed_candles(
        reduce_session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.H1,
        closes=overextended_closes(),
    )
    seed_open_position(
        reduce_session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
    )
    indicator_service = DefaultIndicatorService(reduce_settings, session_factory=reduce_session_factory)
    asyncio.run(
        indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.H1.value)
    )
    reduce_engine = build_engine(reduce_settings, reduce_session_factory)
    reduce_result = asyncio.run(reduce_engine.evaluate_sleeve("sleeve_1h", symbols=["BTC"]))
    assert reduce_result[0].decision.action == DecisionAction.REDUCE
    assert reduce_result[0].decision.reason_code == "trim_on_overbought_rsi"

    hold_settings = build_settings(
        MONEY_FLOW_1H_RSI_CEILING=90.0,
        MONEY_FLOW_1H_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_1H_REQUIRE_MACD_CONFIRMATION=False,
        MONEY_FLOW_1H_TRIM_RSI=98.0,
        MONEY_FLOW_1H_CLOSE_ON_MA_BREAK=False,
        MONEY_FLOW_1H_CLOSE_ON_MACD_ROLLOVER=False,
    )
    hold_session_factory = build_test_session_factory()
    instrument_ref_id_hold, symbol_id_hold, _ = seed_symbol(hold_session_factory)
    seed_candles(
        hold_session_factory,
        instrument_ref_id=instrument_ref_id_hold,
        symbol_id=symbol_id_hold,
        symbol="BTC",
        timeframe=Timeframe.H1,
        closes=bullish_closes(),
    )
    seed_open_position(
        hold_session_factory,
        instrument_ref_id=instrument_ref_id_hold,
        symbol_id=symbol_id_hold,
        symbol="BTC",
    )
    hold_indicator_service = DefaultIndicatorService(hold_settings, session_factory=hold_session_factory)
    asyncio.run(
        hold_indicator_service.refresh_snapshots(instrument_ref_id_hold, "BTC", "hyperliquid", Timeframe.H1.value)
    )
    hold_engine = build_engine(hold_settings, hold_session_factory)
    hold_result = asyncio.run(hold_engine.evaluate_sleeve("sleeve_1h", symbols=["BTC"]))
    assert hold_result[0].decision.action == DecisionAction.HOLD
    assert hold_result[0].signal_event is None


def test_strategy_persistence_and_api_inspection() -> None:
    settings = build_settings(
        MONEY_FLOW_15M_RSI_CEILING=90.0,
        MONEY_FLOW_15M_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION=False,
    )
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=bullish_closes(),
    )
    indicator_service = DefaultIndicatorService(settings, session_factory=session_factory)
    market_data_service = DefaultMarketDataService(settings=settings, session_factory=session_factory)
    engine = MandateStrategyEngine(
        indicator_service=indicator_service,
        market_data_service=market_data_service,
        settings=settings,
        session_factory=session_factory,
    )

    asyncio.run(indicator_service.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.M15.value))
    asyncio.run(engine.evaluate_sleeve("sleeve_15m", symbols=["BTC"]))

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SignalEventModel)) == 1
        assert session.scalar(select(func.count()).select_from(StrategyDecisionModel)) == 1

    app.dependency_overrides[get_indicator_service] = lambda: DefaultIndicatorService(
        settings,
        session_factory=session_factory,
    )
    app.dependency_overrides[get_market_data_service] = lambda: DefaultMarketDataService(
        settings=settings,
        session_factory=session_factory,
    )
    app.dependency_overrides[get_strategy_engine] = lambda: MandateStrategyEngine(
        indicator_service=DefaultIndicatorService(settings, session_factory=session_factory),
        market_data_service=DefaultMarketDataService(settings=settings, session_factory=session_factory),
        settings=settings,
        session_factory=session_factory,
    )
    client = TestClient(app)
    try:
        indicators_response = client.get("/api/v1/indicators/latest", params={"timeframe": "15m", "symbol": "BTC"})
        signals_response = client.get("/api/v1/strategy/signals", params={"sleeve_id": "sleeve_15m"})
        decisions_response = client.get("/api/v1/strategy/decisions", params={"sleeve_id": "sleeve_15m"})
        status_response = client.get("/api/v1/strategy/status")
    finally:
        app.dependency_overrides.clear()

    assert indicators_response.status_code == 200
    assert indicators_response.json()[0]["instrument_key"] == instrument_key
    assert signals_response.status_code == 200
    assert signals_response.json()[0]["evaluation_key"]
    assert decisions_response.status_code == 200
    assert decisions_response.json()[0]["evaluation_key"]
    assert decisions_response.json()[0]["provenance"]["config_fingerprint"]
    assert status_response.status_code == 200
    assert status_response.json()["family"] == "money_flow"
