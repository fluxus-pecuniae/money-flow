from __future__ import annotations

import asyncio
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import StrategyValidationCapitalSizingMode, Timeframe
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    SubmittedOrderModel,
)
from services.strategy_validation import (
    MoneyFlowBacktestService,
    MoneyFlowVariantReplayService,
    lower_rsi_floor_trend_intact_variant,
    money_flow_replay_report_to_markdown,
    money_flow_true_replay_result_to_dict,
)
from tests.test_sv10_strategy_validation import (
    build_request_for_window,
    build_settings,
    build_test_session_factory,
    bullish_then_break_closes,
    seed_candles,
    seed_symbol,
)


def _seed_request(*, rsi_floor: float = 52.0):
    settings = build_settings(
        MONEY_FLOW_15M_RSI_FLOOR=rsi_floor,
        MONEY_FLOW_15M_RSI_CEILING=90.0,
        MONEY_FLOW_15M_OVERBOUGHT_RSI=95.0,
        MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION=False,
    )
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
    request = build_request_for_window(
        start=start,
        delta=delta,
        closes=closes,
        instrument_key=instrument_key,
    )
    request.assumptions.capital_sizing_mode = StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    return settings, session_factory, request


def test_replay_captures_per_candle_context_and_rejected_signals() -> None:
    settings, session_factory, request = _seed_request()
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    result = asyncio.run(service.run_money_flow_true_replay(request))[0]
    payload = money_flow_true_replay_result_to_dict(result)

    assert result.variant.methodology == "true_forward_replay"
    assert result.contexts
    assert result.rejected_signal_summary["captured_rejected_signal_context"] is True
    assert result.rejected_signal_summary["baseline_entry_rejected_count"] > 0
    assert "below_floor" in result.rejected_signal_summary["rsi_zone_counts"]
    first_context = result.contexts[0]
    assert first_context.component_key == "sleeve_15m"
    assert first_context.rsi_sleeve_floor == Decimal("52.0")
    assert first_context.market_structure.lookback_candles == 20
    assert "contexts" in payload
    assert payload["boundary_flags"]["creates_live_artifacts"] is False


def test_baseline_replay_preserves_dynamic_equity_path_without_live_artifacts() -> None:
    settings, session_factory, request = _seed_request()
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    result = asyncio.run(service.run_money_flow_true_replay(request))[0]

    assert result.metrics.capital_sizing_mode == StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
    assert result.metrics.ending_equity == Decimal("9982.08295638")
    assert result.metrics.net_account_pnl == Decimal("-17.91704362")
    assert result.metrics.number_of_trades == 4
    assert result.boundary_flags["changes_production_money_flow_rules"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def test_baseline_replay_matches_existing_validation_fixture() -> None:
    settings, session_factory, request = _seed_request()
    existing_service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    replay_service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    existing_report = asyncio.run(existing_service.run_money_flow_backtest(request))
    replay_result = asyncio.run(replay_service.run_money_flow_true_replay(request))[0]
    existing_component = existing_report.component_reports[0]

    assert replay_result.metrics.number_of_trades == existing_component.metrics.number_of_trades
    assert replay_result.metrics.net_account_pnl == existing_component.metrics.net_account_pnl
    assert replay_result.metrics.ending_equity == existing_component.metrics.ending_equity
    assert [trade.entry_time for trade in replay_result.trades] == [
        trade.entry_time for trade in existing_component.trades
    ]
    assert [trade.exit_time for trade in replay_result.trades] == [
        trade.exit_time for trade in existing_component.trades
    ]


def test_lower_rsi_true_replay_can_admit_rejected_candle_without_changing_rules() -> None:
    settings, session_factory, request = _seed_request(rsi_floor=80.0)
    variant = replace(
        lower_rsi_floor_trend_intact_variant(),
        requires_macd_constructive=False,
        requires_pullback_or_support=False,
    )
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    result = asyncio.run(service.run_money_flow_true_replay(request, variant=variant))[0]
    admitted_contexts = [context for context in result.contexts if context.variant_entry_allowed]

    assert result.variant.variant_id == "lower_rsi_floor_trend_intact_v1"
    assert result.variant.methodology == "true_forward_replay"
    assert result.variant_summary["variant_candidate_contexts"] > 0
    assert result.variant_summary["variant_entries_allowed"] == 1
    assert admitted_contexts[0].entry_rejection_reason == "rsi_not_constructive"
    assert admitted_contexts[0].rsi_zone == "below_floor"
    assert admitted_contexts[0].ema_trend_stack_state == "ema5_gt_ema10_gt_sma20"
    assert result.variant.changes_production_rules is False


def test_replay_markdown_explains_boundaries_and_avoids_approval_language() -> None:
    settings, session_factory, request = _seed_request(rsi_floor=80.0)
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)
    variant = replace(
        lower_rsi_floor_trend_intact_variant(),
        requires_macd_constructive=False,
        requires_pullback_or_support=False,
    )
    baseline = asyncio.run(service.run_money_flow_true_replay(request))
    variant_results = asyncio.run(service.run_money_flow_true_replay(request, variant=variant))

    markdown = money_flow_replay_report_to_markdown(baseline, variant_results)

    assert "per_candle_true_replay_context_research_only" in markdown
    assert "Rejected-Signal Summary" in markdown
    assert "Baseline Replay Parity" in markdown
    assert "not a production rule" in markdown
    assert "paper/live authorization" in markdown
    for forbidden in ("proven profitable", "paper trading approved", "ready for live trading"):
        assert forbidden not in markdown.lower()


def test_replay_substrate_is_not_wired_into_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text()

    assert "lower_rsi_floor_trend_intact_v1" not in source
    assert "MoneyFlowVariantReplayService" not in source
    assert "MoneyFlowReplayCandleContext" not in source
