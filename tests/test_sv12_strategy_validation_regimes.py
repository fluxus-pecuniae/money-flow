from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import func, select

from core.domain.enums import Environment, StrategyFamily, StrategyValidationFillTiming, Timeframe
from core.domain.models import (
    StrategyValidationAssumptions,
    StrategyValidationBatchRequest,
    StrategyValidationRequest,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingAssessmentModel,
    RoutingAutomationApprovalModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SignalEventModel,
    StrategyDecisionModel,
    SubmittedOrderModel,
)
from scripts.run_money_flow_validation_batch import build_batch_request, build_parser
from services.strategy_validation import (
    MoneyFlowBacktestService,
    strategy_validation_batch_report_to_markdown,
    strategy_validation_report_to_dict,
    strategy_validation_report_to_markdown,
)
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    bullish_then_break_closes,
    seed_candles,
    seed_symbol,
)


def _request(
    *,
    start,
    end,
    instrument_key: str,
    component: str = "sleeve_15m",
    fill_timing: StrategyValidationFillTiming = StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
) -> StrategyValidationRequest:
    return StrategyValidationRequest(
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        symbol="BTC",
        instrument_key=instrument_key,
        component_keys=(component,),
        start_at=start,
        end_at=end,
        assumptions=StrategyValidationAssumptions(
            initial_capital=Decimal("10000"),
            fee_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
            fill_timing=fill_timing,
            position_notional_pct=Decimal("1.0"),
        ),
    )


def _trend_labels(report) -> set[str]:
    return {
        summary.regime_label
        for summary in report.component_reports[0].regime_summaries
        if summary.regime_type == "trend"
    }


def test_data_coverage_reports_complete_and_thin_windows() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(12)]
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    complete = asyncio.run(
        service.run_money_flow_backtest(
            _request(
                start=start,
                end=start + (delta * len(closes)),
                instrument_key=instrument_key,
            )
        )
    )
    complete_coverage = complete.component_reports[0].data_coverage
    assert complete_coverage is not None
    assert complete_coverage.expected_candle_count == len(closes)
    assert complete_coverage.actual_candle_count == len(closes)
    assert complete_coverage.missing_candle_count == 0
    assert complete_coverage.coverage_percent == Decimal("1.00000000")
    assert complete_coverage.warning_reason_codes == []

    thin = asyncio.run(
        service.run_money_flow_backtest(
            _request(
                start=start,
                end=start + (delta * 20),
                instrument_key=instrument_key,
            )
        )
    )
    thin_coverage = thin.component_reports[0].data_coverage
    assert thin_coverage is not None
    assert thin_coverage.expected_candle_count == 20
    assert thin_coverage.actual_candle_count == len(closes)
    assert thin_coverage.missing_candle_count == 8
    assert "data_coverage_below_warning_threshold" in thin_coverage.warning_reason_codes
    assert "missing_candles_in_requested_window" in thin_coverage.warning_reason_codes
    payload = strategy_validation_report_to_dict(thin)
    assert "data_coverage_below_warning_threshold" in payload["data_coverage_summary"]["warning_reason_codes"]


def test_regime_labeling_is_deterministic_for_trend_and_insufficient_data() -> None:
    settings = build_settings()

    for closes, expected_label in (
        ([Decimal(str(100 + index)) for index in range(20)], "uptrend"),
        ([Decimal(str(120 - index)) for index in range(20)], "downtrend"),
        ([Decimal("100"), Decimal("100.1"), Decimal("99.9"), Decimal("100.0")] * 5, "sideways"),
        ([Decimal("100"), Decimal("101"), Decimal("102")], "unknown_or_insufficient_data"),
    ):
        session_factory = build_test_session_factory()
        instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
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
                _request(
                    start=start,
                    end=start + (delta * len(closes)),
                    instrument_key=instrument_key,
                )
            )
        )
        assert expected_label in _trend_labels(report)
        assert report.component_reports[0].regime_methodology["trade_assignment"] == (
            "entry_signal_candle_regime"
        )


def test_regime_grouped_metrics_mark_trade_entry_regime_without_live_artifacts() -> None:
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
            _request(
                start=start,
                end=start + (delta * len(closes)),
                instrument_key=instrument_key,
                fill_timing=StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY,
            )
        )
    )

    trades = report.component_reports[0].trades
    assert trades
    assert trades[0].entry_market_regime == "uptrend"
    trend_rows = [
        row
        for row in report.regime_comparison["rows"]
        if row["regime_type"] == "trend" and row["regime_label"] == "uptrend"
    ]
    assert trend_rows
    assert trend_rows[0]["trade_count"] >= 1
    assert trend_rows[0]["net_pnl"] == report.aggregate_metrics.net_pnl

    markdown = strategy_validation_report_to_markdown(report)
    assert "## Data Coverage" in markdown
    assert "## Market-Regime Methodology" in markdown
    assert "## Regime Performance" in markdown
    assert "Regimes are deterministic descriptive labels only" in markdown
    assert "SubmittedOrder" in markdown

    with session_factory() as session:
        for model in (
            MandateDesiredTradeModel,
            RoutingAssessmentModel,
            RouteReadinessAuditModel,
            RoutingTargetRecommendationModel,
            RoutingTargetChoiceModel,
            RoutingAutomationApprovalModel,
            OrderIntentModel,
            ExecutionReadinessEvaluationModel,
            SubmittedOrderModel,
            StrategyDecisionModel,
            SignalEventModel,
        ):
            assert session.scalar(select(func.count()).select_from(model)) == 0


def test_batch_cli_repeated_windows_produce_date_window_and_regime_comparison() -> None:
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
    parser = build_parser()
    first_end = start + (delta * 24)
    second_start = start + (delta * 24)
    second_end = start + (delta * len(closes))
    args = parser.parse_args(
        [
            "--batch-name",
            "sv1.2-window-check",
            "--venue",
            "hyperliquid",
            "--symbol",
            "BTC",
            "--instrument-key",
            instrument_key,
            "--component",
            "sleeve_15m",
            "--fill-timing",
            "next_candle_open",
            "--window",
            f"{start.isoformat()},{first_end.isoformat()}",
            "--window",
            f"{second_start.isoformat()},{second_end.isoformat()}",
            "--initial-capital",
            "10000",
            "--fee-bps",
            "0",
            "--slippage-bps",
            "0",
        ]
    )

    request = build_batch_request(args)
    assert len(request.runs) == 2
    assert request.runs[0].start_at == start
    assert request.runs[1].start_at == second_start

    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    report = asyncio.run(service.run_money_flow_batch_backtest(request))
    markdown = strategy_validation_batch_report_to_markdown(report)

    assert "## Date-Window Comparison" in markdown
    assert "## Data-Coverage Comparison" in markdown
    assert "## Market-Regime Comparison" in markdown
    assert report.comparison_summary["regime_comparison"]
    assert report.comparison_summary["data_coverage_comparison"]
    assert "recommended strategy" not in markdown.lower()
    assert "optimal" not in markdown.lower()
