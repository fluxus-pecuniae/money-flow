from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import func, select

from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    SubmittedOrderModel,
)
from services.strategy_validation import (
    LOWER_RSI_EMA10_HOLD_NO_RESISTANCE_VARIANT_ID,
    LOWER_RSI_NARROW_TREND_INTACT_VARIANT_ID,
    LOWER_RSI_SUPPORT_CONFIRMED_VARIANT_ID,
    LOWER_RSI_TREND_INTACT_VARIANT_ID,
    MoneyFlowVariantReplayService,
    money_flow_true_replay_experiment_report_to_markdown,
    sv117_round_one_variants,
)
from tests.test_sv116_replay_instrumentation import _seed_request


def test_sv117_round_one_variants_are_research_only_and_distinct() -> None:
    variants = sv117_round_one_variants()

    assert [variant.variant_id for variant in variants] == [
        LOWER_RSI_TREND_INTACT_VARIANT_ID,
        LOWER_RSI_NARROW_TREND_INTACT_VARIANT_ID,
        LOWER_RSI_SUPPORT_CONFIRMED_VARIANT_ID,
        LOWER_RSI_EMA10_HOLD_NO_RESISTANCE_VARIANT_ID,
    ]
    assert all(variant.methodology == "true_forward_replay" for variant in variants)
    assert all(variant.changes_production_rules is False for variant in variants)
    assert any(variant.requires_near_support for variant in variants)
    assert any(variant.requires_ema10_hold for variant in variants)
    assert any(variant.avoids_near_resistance for variant in variants)


def test_sv117_true_replay_variants_expose_counter_truth_without_live_artifacts() -> None:
    settings, session_factory, request = _seed_request(rsi_floor=80.0)
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    baseline = asyncio.run(service.run_money_flow_true_replay(request))
    results = []
    for variant in sv117_round_one_variants():
        results.extend(asyncio.run(service.run_money_flow_true_replay(request, variant=variant)))

    assert baseline[0].metrics.number_of_trades > 0
    assert {result.variant.variant_id for result in results} == {
        LOWER_RSI_TREND_INTACT_VARIANT_ID,
        LOWER_RSI_NARROW_TREND_INTACT_VARIANT_ID,
        LOWER_RSI_SUPPORT_CONFIRMED_VARIANT_ID,
        LOWER_RSI_EMA10_HOLD_NO_RESISTANCE_VARIANT_ID,
    }
    for result in results:
        assert "variant_admitted_from_rejection_reason_counts" in result.variant_summary
        assert "variant_no_trade_reason_counts" in result.variant_summary
        assert "variant_candidate_falling_knife_risk_proxy_count" in result.variant_summary
        assert result.variant_summary["changes_production_rules"] is False
        assert result.boundary_flags["creates_live_artifacts"] is False
        assert result.boundary_flags["creates_routing_artifacts"] is False
        assert result.boundary_flags["calls_exchange_adapters"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(MandateDesiredTradeModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def test_sv117_report_compares_variants_to_baseline_and_avoids_approval_language() -> None:
    settings, session_factory, request = _seed_request(rsi_floor=80.0)
    service = MoneyFlowVariantReplayService(settings, session_factory=session_factory)

    baseline = asyncio.run(service.run_money_flow_true_replay(request))
    results = []
    for variant in sv117_round_one_variants():
        results.extend(asyncio.run(service.run_money_flow_true_replay(request, variant=variant)))

    markdown = money_flow_true_replay_experiment_report_to_markdown(baseline, results)

    assert "# SV1.17 True Replay Experiment Round 1" in markdown
    assert "Delta Vs Baseline" in markdown
    assert "Variant Counter Truth" in markdown
    assert "falling-knife candidate proxy" in markdown.lower()
    assert LOWER_RSI_SUPPORT_CONFIRMED_VARIANT_ID in markdown
    assert "not production rules" in markdown
    assert "paper/live authorization" in markdown
    for forbidden in ("proven profitable", "paper trading approved", "ready for live trading"):
        assert forbidden not in markdown.lower()


def test_sv117_report_uses_symbol_component_scenario_baselines() -> None:
    markdown = Path("docs/strategy_validation_sv1_17_true_replay_experiments.md").read_text()

    assert "| Symbol | Component | Variant |" in markdown
    assert "full BTC/ETH/SOL x 15m/1h/4h public campaign suite" in markdown
    for symbol in ("BTC", "ETH", "SOL"):
        for component in ("sleeve_15m", "sleeve_1h", "sleeve_4h"):
            assert f"| {symbol} | {component} |" in markdown


def test_sv117_replay_substrate_is_not_wired_into_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text()

    assert LOWER_RSI_NARROW_TREND_INTACT_VARIANT_ID not in source
    assert LOWER_RSI_SUPPORT_CONFIRMED_VARIANT_ID not in source
    assert LOWER_RSI_EMA10_HOLD_NO_RESISTANCE_VARIANT_ID not in source
