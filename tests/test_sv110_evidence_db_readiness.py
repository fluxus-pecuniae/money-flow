from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

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
from services.strategy_validation import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    MoneyFlowBacktestService,
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_database_status_to_dict,
    money_flow_evidence_review_to_dict,
    money_flow_evidence_review_to_markdown,
    review_money_flow_evidence,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory
from test_sv19_evidence_status import _seed_current_alembic_version


def _assert_no_live_artifacts(session_factory) -> None:
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
    with session_factory() as session:
        for model in live_models:
            assert session.scalar(select(func.count()).select_from(model)) == 0


def test_intended_strategy_validation_db_target_is_reported_explicitly() -> None:
    settings = build_settings(
        DB_HOST="127.0.0.1",
        DB_PORT=5432,
        DB_NAME="money_flow",
        DB_USER="money_flow",
        DB_PASSWORD="money_flow",
    )
    session_factory = build_test_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    payload = money_flow_evidence_review_database_status_to_dict(
        inspect_strategy_validation_database_status(service)
    )

    assert payload["configured_database_url"] == (
        "postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow"
    )
    assert payload["database_host"] == "127.0.0.1"
    assert payload["database_port"] == 5432
    assert payload["database_name"] == "money_flow"
    assert payload["database_username"] == "money_flow"
    assert payload["database_target_role"] == "configured_money_flow_database"
    assert payload["intended_strategy_validation_database"] is True


def test_canonical_import_requirements_are_unique_and_timezone_explicit() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 4, 5, 20, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["database_status"]["schema_status"] == "migrated_schema_ready"
    assert payload["database_status"]["persisted_candle_count"] == 0
    assert payload["generated_campaign_count"] == 0
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert len(payload["canonical_candle_import_requirements"]) == 18
    assert "Campaigns impacted" in markdown
    assert "timezone-explicit" in markdown
    assert "timezone-naive rows are rejected by default" in markdown

    btc_15m_window_1 = next(
        requirement
        for requirement in payload["canonical_candle_import_requirements"]
        if requirement["symbol"] == "BTC"
        and requirement["timeframe"] == "15m"
        and requirement["requested_start_at"] == "2026-01-01T00:00:00+00:00"
    )
    assert btc_15m_window_1["expected_candle_count"] == 1344
    assert btc_15m_window_1["actual_candle_count"] == 0
    assert btc_15m_window_1["missing_candle_count"] == 1344
    assert btc_15m_window_1["campaigns_impacted"] == [
        "money_flow_core_btc",
        "money_flow_core_multi_symbol",
    ]
    assert btc_15m_window_1["components"] == ["sleeve_15m"]
    assert btc_15m_window_1["timezone_requirement"].startswith(
        "open_time and close_time must be timezone-explicit"
    )
    assert btc_15m_window_1["naive_timestamp_default_policy"] == "reject"
    assert "scripts/import_strategy_validation_candles.py" in btc_15m_window_1[
        "example_import_command"
    ]

    expected_counts = sorted(
        {
            (
                requirement["timeframe"],
                requirement["requested_start_at"],
                requirement["expected_candle_count"],
            )
            for requirement in payload["canonical_candle_import_requirements"]
        }
    )
    assert expected_counts == [
        ("15m", "2026-01-01T00:00:00+00:00", 1344),
        ("15m", "2026-01-15T00:00:00+00:00", 1632),
        ("1h", "2026-01-01T00:00:00+00:00", 336),
        ("1h", "2026-01-15T00:00:00+00:00", 408),
        ("4h", "2026-01-01T00:00:00+00:00", 84),
        ("4h", "2026-01-15T00:00:00+00:00", 102),
    ]

    _assert_no_live_artifacts(session_factory)


def test_canonical_empty_db_audit_does_not_write_evidence_packs(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 4, 5, 25, tzinfo=UTC),
        generated_at=datetime(2026, 5, 4, 5, 25, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["generated_campaign_count"] == 0
    assert payload["blocked_campaign_count"] == 2
    assert payload["generated_evidence_pack_paths"] == []
    assert not (tmp_path / "money_flow_core_btc").exists()
    assert not (tmp_path / "money_flow_core_multi_symbol").exists()
    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert "best strategy" not in money_flow_evidence_review_to_markdown(review).lower()
    assert "recommended strategy" not in money_flow_evidence_review_to_markdown(review).lower()
    assert "optimal" not in money_flow_evidence_review_to_markdown(review).lower()

    _assert_no_live_artifacts(session_factory)
