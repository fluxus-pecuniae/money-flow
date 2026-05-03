from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.domain.enums import Timeframe
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
    money_flow_evidence_review_to_dict,
    review_money_flow_evidence,
)
from services.strategy_validation.evidence_review import (
    _calls_exchange_adapters_from_campaign_results,
    _creates_live_artifacts_from_campaign_results,
    _migration_head_revisions,
)
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)
from test_sv15_historical_data_readiness import _campaign_raw


def _seed_current_alembic_version(session_factory) -> None:
    revisions = _migration_head_revisions()
    assert revisions
    with session_factory() as session:
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        for revision in revisions:
            session.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
                {"version_num": revision},
            )
        session.commit()


def _seeded_campaign_config_path(tmp_path: Path, session_factory) -> Path:
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(36)]
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    raw = _campaign_raw(
        output_dir=tmp_path,
        instrument_key=instrument_key,
        start=start,
        end=start + (delta * len(closes)),
    )
    raw["campaign_name"] = "sv1_8_1_schema_truth_seeded_campaign"
    raw["description"] = "Seeded SV1.8.1 schema gate campaign."
    raw["windows"][0]["label"] = "sv1_8_1_schema_truth_window"
    config_path = tmp_path / "sv1_8_1_seeded_campaign.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    return config_path


def _partial_candles_only_session_factory():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        session.execute(text("CREATE TABLE candles (id VARCHAR(36) PRIMARY KEY)"))
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        for revision in _migration_head_revisions():
            session.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
                {"version_num": revision},
            )
        session.commit()
    return session_factory


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


def test_candles_without_alembic_truth_cannot_generate_evidence_pack(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(tmp_path, session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 15, 0, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 15, 0, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["database_status"]["candles_table_exists"] is True
    assert payload["database_status"]["alembic_version_table_exists"] is False
    assert payload["database_status"]["schema_status"] == "schema_present_migration_version_unknown"
    assert payload["database_status"]["schema_ready_for_evidence_generation"] is False
    assert "alembic_version_missing" in payload["campaign_results"][0]["blocked_or_gap_reason_codes"]
    assert (
        "schema_not_ready_for_evidence_generation"
        in payload["campaign_results"][0]["blocked_or_gap_reason_codes"]
    )
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["generated_campaign_count"] == 0
    assert payload["campaign_results"][0]["evidence_pack_generated"] is False
    assert not (tmp_path / "sv1_8_1_schema_truth_seeded_campaign").exists()

    _assert_no_live_artifacts(session_factory)


def test_current_alembic_truth_allows_seeded_sufficient_evidence_pack_generation(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(tmp_path, session_factory)
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 15, 5, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 15, 5, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["database_status"]["schema_status"] == "migrated_schema_ready"
    assert payload["database_status"]["schema_ready_for_evidence_generation"] is True
    assert payload["generated_campaign_count"] == 1
    assert payload["campaign_results"][0]["evidence_pack_generated"] is True

    _assert_no_live_artifacts(session_factory)


def test_partial_required_schema_reports_gap_without_uncaught_exception() -> None:
    settings = build_settings()
    session_factory = _partial_candles_only_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    status = inspect_strategy_validation_database_status(service)
    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 15, 10, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert status.reachable is True
    assert status.candles_table_exists is True
    assert status.alembic_version_table_exists is True
    assert status.schema_status == "required_schema_missing"
    assert status.schema_ready_for_evidence_generation is False
    assert status.required_schema_tables_missing == ("instruments", "symbols")
    assert payload["generated_campaign_count"] == 0
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert all(
        "required_schema_missing" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert all(
        "required_schema_table_missing_instruments" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )


def test_top_level_live_and_exchange_flags_are_aggregated_from_campaign_results() -> None:
    false_result = SimpleNamespace(
        no_live_artifacts_created=True,
        exchange_adapters_called=False,
    )
    true_result = SimpleNamespace(
        no_live_artifacts_created=False,
        exchange_adapters_called=True,
    )

    assert _creates_live_artifacts_from_campaign_results((false_result,)) is False
    assert _calls_exchange_adapters_from_campaign_results((false_result,)) is False
    assert _creates_live_artifacts_from_campaign_results((false_result, true_result)) is True
    assert _calls_exchange_adapters_from_campaign_results((false_result, true_result)) is True
