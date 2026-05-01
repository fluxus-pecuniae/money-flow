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
    IndicatorSnapshotModel,
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
    strategy_validation_batch_report_to_dict,
    strategy_validation_batch_report_to_markdown,
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
    delta,
    closes,
    instrument_key: str,
    component: str,
    fill_timing: StrategyValidationFillTiming,
    symbol: str = "BTC",
) -> StrategyValidationRequest:
    return StrategyValidationRequest(
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        symbol=symbol,
        instrument_key=instrument_key,
        component_keys=(component,),
        start_at=start,
        end_at=start + (delta * len(closes)),
        assumptions=StrategyValidationAssumptions(
            initial_capital=Decimal("10000"),
            fee_bps=Decimal("2"),
            slippage_bps=Decimal("1"),
            fill_timing=fill_timing,
            position_notional_pct=Decimal("1.0"),
        ),
    )


def test_batch_runner_compares_fill_timing_and_components_without_live_artifacts() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = bullish_then_break_closes()
    opens = [close + Decimal("4") for close in closes]
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
        opens=opens,
    )
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.H1,
        closes=closes,
        opens=opens,
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    request = StrategyValidationBatchRequest(
        batch_name="sv1.1-fill-component-comparison",
        runs=tuple(
            _request(
                start=start,
                delta=delta,
                closes=closes,
                instrument_key=instrument_key,
                component=component,
                fill_timing=fill_timing,
            )
            for component in ("sleeve_15m", "sleeve_1h")
            for fill_timing in (
                StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY,
                StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
                StrategyValidationFillTiming.NEXT_CANDLE_CLOSE,
            )
        ),
    )

    first = asyncio.run(service.run_money_flow_batch_backtest(request))
    second = asyncio.run(service.run_money_flow_batch_backtest(request))

    payload = strategy_validation_batch_report_to_dict(first)
    assert payload == strategy_validation_batch_report_to_dict(second)
    assert len(first.run_reports) == 6
    assert {run.status for run in first.run_reports} == {"completed"}
    assert len(payload["comparison_summary"]["fill_timing_comparison"]) == 3
    assert len(payload["comparison_summary"]["component_comparison"]) == 2
    assert payload["comparison_summary"]["methodology"].startswith("descriptive_research")
    assert "same_candle_close_research_only" in payload["assumptions_matrix"]["fill_timings"]
    assert "next_candle_open" in payload["assumptions_matrix"]["fill_timings"]
    assert "next_candle_close" in payload["assumptions_matrix"]["fill_timings"]

    same_run = next(
        run
        for run in first.run_reports
        if run.request.component_keys == ("sleeve_15m",)
        and run.request.assumptions.fill_timing
        == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY
    )
    next_open_run = next(
        run
        for run in first.run_reports
        if run.request.component_keys == ("sleeve_15m",)
        and run.request.assumptions.fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_OPEN
    )
    assert same_run.report is not None
    assert next_open_run.report is not None
    assert same_run.report.component_reports[0].trades
    assert next_open_run.report.component_reports[0].trades
    assert (
        same_run.report.component_reports[0].trades[0].entry_price
        != next_open_run.report.component_reports[0].trades[0].entry_price
    )

    with session_factory() as session:
        live_models = [
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
            IndicatorSnapshotModel,
        ]
        for model in live_models:
            assert session.scalar(select(func.count()).select_from(model)) == 0


def test_batch_markdown_has_comparison_tables_and_no_recommendation_language() -> None:
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
        service.run_money_flow_batch_backtest(
            StrategyValidationBatchRequest(
                runs=(
                    _request(
                        start=start,
                        delta=delta,
                        closes=closes,
                        instrument_key=instrument_key,
                        component="sleeve_15m",
                        fill_timing=StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY,
                    ),
                    _request(
                        start=start,
                        delta=delta,
                        closes=closes,
                        instrument_key=instrument_key,
                        component="sleeve_15m",
                        fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
                    ),
                ),
            )
        )
    )

    markdown = strategy_validation_batch_report_to_markdown(report)

    assert "## Assumptions Matrix" in markdown
    assert "## Run Summary" in markdown
    assert "## Fill-Timing Comparison" in markdown
    assert "## Component Comparison" in markdown
    assert "## Top/Bottom Observed Runs" in markdown
    assert "does not recommend a strategy variant" in markdown
    assert "not optimization" in markdown
    assert "recommended strategy" not in markdown.lower()
    assert "optimal" not in markdown.lower()


def test_batch_surfaces_missing_candles_per_run_without_hiding_it() -> None:
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
        service.run_money_flow_batch_backtest(
            StrategyValidationBatchRequest(
                runs=(
                    _request(
                        start=start,
                        delta=delta,
                        closes=closes,
                        instrument_key=instrument_key,
                        component="sleeve_15m",
                        fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
                    ),
                    _request(
                        start=start,
                        delta=delta,
                        closes=closes,
                        instrument_key=instrument_key,
                        component="sleeve_4h",
                        fill_timing=StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
                    ),
                ),
            )
        )
    )

    missing_run = next(run for run in report.run_reports if run.request.component_keys == ("sleeve_4h",))
    assert missing_run.status == "completed"
    assert missing_run.report is not None
    assert missing_run.report.component_reports[0].metrics.number_of_trades == 0
    assert "no_persisted_candles_for_component" in missing_run.report.component_reports[0].limitations
    assert "no_candles_in_requested_window" in missing_run.report.component_reports[0].limitations
    payload = strategy_validation_batch_report_to_dict(report)
    missing_summary = next(
        run
        for run in payload["comparison_summary"]["run_summaries"]
        if run["component_keys"] == ["sleeve_4h"]
    )
    assert "no_persisted_candles_for_component" in missing_summary["limitations"]


def test_batch_cli_builds_explicit_matrix_request() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--batch-name",
            "research-check",
            "--venue",
            "hyperliquid",
            "--symbol",
            "BTC",
            "--component",
            "sleeve_15m",
            "--component",
            "sleeve_1h",
            "--fill-timing",
            "same_candle_close_research_only",
            "--fill-timing",
            "next_candle_open",
            "--start",
            "2026-01-01T00:00:00Z",
            "--end",
            "2026-02-01T00:00:00Z",
            "--initial-capital",
            "10000",
            "--fee-bps",
            "2",
            "--slippage-bps",
            "1",
        ]
    )

    request = build_batch_request(args)

    assert request.batch_name == "research-check"
    assert len(request.runs) == 4
    assert {run.component_keys for run in request.runs} == {("sleeve_15m",), ("sleeve_1h",)}
    assert {run.assumptions.fill_timing for run in request.runs} == {
        StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY,
        StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
    }
