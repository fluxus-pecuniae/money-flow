from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config.settings import AppSettings
from core.domain.enums import Environment, MarketType, ProductType, StrategyFamily, Timeframe
from core.domain.models import StrategyValidationAssumptions, StrategyValidationRequest
from db.base import Base
from db.models import (
    CandleModel,
    ExecutionReadinessEvaluationModel,
    IndicatorSnapshotModel,
    InstrumentModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    SignalEventModel,
    StrategyDecisionModel,
    SubmittedOrderModel,
    SymbolModel,
)
from scripts.run_money_flow_backtest import build_parser, build_request
from services.strategy_validation import MoneyFlowBacktestService, strategy_validation_report_to_dict


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
        "MONEY_FLOW_15M_RSI_CEILING": 90.0,
        "MONEY_FLOW_15M_OVERBOUGHT_RSI": 95.0,
        "MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION": False,
    }
    base.update(overrides)
    return AppSettings(_env_file=None, **base)


def seed_symbol(session_factory, symbol: str = "BTC") -> tuple[str, str, str]:
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
            is_strategy_eligible=True,
            is_trading_eligible=True,
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
            open_price = closes[index - 1] if index else close
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
                    high=max(open_price, close) + Decimal("0.5"),
                    low=min(open_price, close) - Decimal("0.5"),
                    close=close,
                    volume=Decimal("100"),
                    trade_count=10,
                )
            )
        session.commit()
    return start, delta


def bullish_then_break_closes() -> list[Decimal]:
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
        Decimal("115.7"),
        Decimal("114.2"),
        Decimal("112.5"),
        Decimal("110.0"),
        Decimal("108.0"),
        Decimal("106.0"),
        Decimal("104.0"),
    ]


def bearish_closes() -> list[Decimal]:
    return [Decimal(str(120 - index)) for index in range(48)]


def build_request_for_window(
    *,
    start: datetime,
    delta: timedelta,
    closes: list[Decimal],
    instrument_key: str,
    fee_bps: Decimal = Decimal("0"),
    slippage_bps: Decimal = Decimal("0"),
) -> StrategyValidationRequest:
    return StrategyValidationRequest(
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        symbol="BTC",
        instrument_key=instrument_key,
        component_keys=("sleeve_15m",),
        start_at=start,
        end_at=start + (delta * len(closes)),
        assumptions=StrategyValidationAssumptions(
            initial_capital=Decimal("10000"),
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            position_notional_pct=Decimal("1.0"),
        ),
    )


def test_money_flow_validation_produces_simulated_trade_without_live_artifacts() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bullish_then_break_closes()
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    report = asyncio.run(
        service.run_money_flow_backtest(
            build_request_for_window(
                start=start,
                delta=delta,
                closes=closes,
                instrument_key=instrument_key,
            )
        )
    )

    component = report.component_reports[0]
    assert component.component_key == "sleeve_15m"
    assert component.timeframe == Timeframe.M15
    assert report.aggregate_metrics.number_of_trades == 4
    assert component.trades[0].entry_time < component.trades[0].exit_time
    assert component.trades[0].component_key == "sleeve_15m"
    assert component.trades[0].timeframe == Timeframe.M15
    assert report.no_live_execution_artifacts_created is True
    assert report.exchange_adapters_called is False
    payload = strategy_validation_report_to_dict(report)
    assert payload["assumptions"]["initial_capital"] == "10000"
    assert payload["assumptions"]["fee_bps"] == "0"
    assert payload["aggregate_metrics"]["number_of_trades"] == 4

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0
        assert session.scalar(select(func.count()).select_from(StrategyDecisionModel)) == 0
        assert session.scalar(select(func.count()).select_from(SignalEventModel)) == 0
        assert session.scalar(select(func.count()).select_from(IndicatorSnapshotModel)) == 0


def test_fees_and_slippage_reduce_net_pnl() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bullish_then_break_closes()
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    zero_cost_report = asyncio.run(
        service.run_money_flow_backtest(
            build_request_for_window(
                start=start,
                delta=delta,
                closes=closes,
                instrument_key=instrument_key,
            )
        )
    )
    costed_report = asyncio.run(
        service.run_money_flow_backtest(
            build_request_for_window(
                start=start,
                delta=delta,
                closes=closes,
                instrument_key=instrument_key,
                fee_bps=Decimal("10"),
                slippage_bps=Decimal("10"),
            )
        )
    )

    assert costed_report.aggregate_metrics.total_fees > 0
    assert costed_report.aggregate_metrics.total_slippage_cost > 0
    assert costed_report.aggregate_metrics.net_pnl < zero_cost_report.aggregate_metrics.net_pnl


def test_no_trade_reasons_and_report_are_deterministic() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bearish_closes()
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    request = build_request_for_window(
        start=start,
        delta=delta,
        closes=closes,
        instrument_key=instrument_key,
    )

    first = asyncio.run(service.run_money_flow_backtest(request))
    second = asyncio.run(service.run_money_flow_backtest(request))

    assert first.aggregate_metrics.number_of_trades == 0
    assert first.aggregate_metrics.no_trade_reason_counts["bearish_alignment"] > 0
    assert strategy_validation_report_to_dict(first) == strategy_validation_report_to_dict(second)


def test_cli_request_and_report_dict_expose_assumptions_and_metrics() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--venue",
            "hyperliquid",
            "--symbol",
            "BTC",
            "--component",
            "sleeve_15m",
            "--start",
            "2026-01-01T00:00:00Z",
            "--end",
            "2026-01-02T00:00:00Z",
            "--initial-capital",
            "10000",
            "--fee-bps",
            "5",
            "--slippage-bps",
            "2",
        ]
    )

    request = build_request(args)

    assert request.component_keys == ("sleeve_15m",)
    assert request.assumptions.initial_capital == Decimal("10000")
    assert request.assumptions.fee_bps == Decimal("5")
    assert request.assumptions.slippage_bps == Decimal("2")
