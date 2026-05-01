from __future__ import annotations

import asyncio
from datetime import timedelta
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
    strategy_validation_batch_report_to_dict,
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
    assert payload["data_coverage_summary"]["window_convention"] == (
        "candle_close_time_start_exclusive_end_inclusive"
    )
    assert "data_coverage_below_warning_threshold" in payload["data_coverage_summary"]["warning_reason_codes"]


def test_adjacent_windows_do_not_double_count_boundary_candle() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(10)]
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    boundary = start + (delta * 5)
    request = StrategyValidationBatchRequest(
        runs=(
            _request(start=start, end=boundary, instrument_key=instrument_key),
            _request(
                start=boundary,
                end=start + (delta * len(closes)),
                instrument_key=instrument_key,
            ),
        ),
        batch_name="sv1.2.1-adjacent-window-boundary",
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    report = asyncio.run(service.run_money_flow_batch_backtest(request))
    assert all(run.report is not None for run in report.run_reports)

    first_component = report.run_reports[0].report.component_reports[0]  # type: ignore[union-attr]
    second_component = report.run_reports[1].report.component_reports[0]  # type: ignore[union-attr]
    assert first_component.evaluated_candles == 5
    assert second_component.evaluated_candles == 5
    assert first_component.data_coverage is not None
    assert second_component.data_coverage is not None
    assert first_component.data_coverage.actual_candle_count == first_component.evaluated_candles
    assert second_component.data_coverage.actual_candle_count == second_component.evaluated_candles
    assert first_component.data_coverage.last_candle_available_at == boundary
    assert second_component.data_coverage.first_candle_available_at == boundary + delta
    assert (
        first_component.evaluated_candles + second_component.evaluated_candles
        == len(closes)
    )


def test_unaligned_window_coverage_uses_close_slots_and_warns_without_exceeding_one() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(4)]
    start, _delta = seed_candles(
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
                start=start + timedelta(minutes=1),
                end=start + timedelta(minutes=31),
                instrument_key=instrument_key,
            )
        )
    )

    coverage = report.component_reports[0].data_coverage
    assert coverage is not None
    assert coverage.expected_candle_count == 2
    assert coverage.actual_candle_count == 2
    assert coverage.missing_candle_count == 0
    assert coverage.coverage_percent == Decimal("1.00000000")
    assert "unaligned_window_boundary" in coverage.warning_reason_codes
    payload = strategy_validation_report_to_dict(report)
    assert "unaligned_window_boundary" in payload["data_coverage_summary"]["warning_reason_codes"]


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
    assert report.assumptions_matrix["window_convention"] == (
        "candle_close_time_start_exclusive_end_inclusive"
    )
    assert "recommended strategy" not in markdown.lower()
    assert "optimal" not in markdown.lower()


def test_blocked_runs_remain_visible_in_grouped_batch_comparisons() -> None:
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
    completed_request = _request(
        start=start,
        end=start + (delta * len(closes)),
        instrument_key=instrument_key,
        component="sleeve_15m",
    )
    blocked_request = _request(
        start=start,
        end=start + (delta * len(closes)),
        instrument_key=instrument_key,
        component="missing_sleeve",
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    report = asyncio.run(
        service.run_money_flow_batch_backtest(
            StrategyValidationBatchRequest(
                runs=(completed_request, blocked_request),
                batch_name="sv1.2.1-blocked-group-coverage",
            )
        )
    )
    payload = strategy_validation_batch_report_to_dict(report)
    summary = payload["comparison_summary"]

    assert [run["status"] for run in summary["run_summaries"]] == ["completed", "blocked"]
    fill_rows = {
        row["fill_timing"]: row for row in summary["fill_timing_comparison"]
    }
    fill_row = fill_rows[StrategyValidationFillTiming.NEXT_CANDLE_OPEN.value]
    assert fill_row["run_count"] == 2
    assert fill_row["completed_run_count"] == 1
    assert fill_row["blocked_run_count"] == 1
    assert fill_row["blocked_reason_counts"] == {"strategy_validation_run_blocked": 1}
    assert fill_row["total_trades"] == (
        report.run_reports[0].report.aggregate_metrics.number_of_trades  # type: ignore[union-attr]
    )

    component_rows = {
        row["component_keys"]: row for row in summary["component_comparison"]
    }
    assert component_rows["missing_sleeve"]["run_count"] == 1
    assert component_rows["missing_sleeve"]["completed_run_count"] == 0
    assert component_rows["missing_sleeve"]["blocked_run_count"] == 1
    assert component_rows["missing_sleeve"]["blocked_reason_counts"] == {
        "strategy_validation_run_blocked": 1
    }

    markdown = strategy_validation_batch_report_to_markdown(report)
    assert "blocked reasons" in markdown
    assert "strategy_validation_run_blocked" in markdown
