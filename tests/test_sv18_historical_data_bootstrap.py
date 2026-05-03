from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

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
from scripts.review_money_flow_evidence_packs import build_parser as build_review_parser
from services.strategy_validation import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    MoneyFlowBacktestService,
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_database_status_to_dict,
    money_flow_evidence_review_database_status_to_markdown,
    money_flow_evidence_review_to_dict,
    money_flow_evidence_review_to_markdown,
    review_money_flow_evidence,
)
from services.strategy_validation.evidence_review import _migration_head_revisions
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)
from test_sv15_historical_data_readiness import _campaign_raw


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


def _blank_session_factory():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return sessionmaker(bind=engine, expire_on_commit=False)


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
    raw["campaign_name"] = "sv1_8_seeded_real_evidence_campaign"
    raw["description"] = "Seeded SV1.8 evidence-generation campaign."
    raw["windows"][0]["label"] = "sv1_8_seeded_window"
    config_path = tmp_path / "sv1_8_seeded_campaign.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    return config_path


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


def test_db_status_reports_missing_schema_and_migration_requirements() -> None:
    settings = build_settings()
    session_factory = _blank_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    status = inspect_strategy_validation_database_status(service)
    payload = money_flow_evidence_review_database_status_to_dict(status)
    markdown = money_flow_evidence_review_database_status_to_markdown(status)

    assert payload["reachable"] is True
    assert payload["candles_table_exists"] is False
    assert payload["schema_ready_for_evidence_generation"] is False
    assert payload["required_schema_tables_missing"] == [
        "candles",
        "instruments",
        "symbols",
    ]
    assert payload["alembic_version_table_exists"] is False
    assert payload["schema_status"] == "schema_missing"
    assert "schema_missing" in payload["schema_status_reason_codes"]
    assert "schema_not_ready_for_evidence_generation" in payload["schema_status_reason_codes"]
    assert "alembic_version_table_missing" in payload["schema_status_reason_codes"]
    assert "candles_table_missing" in payload["schema_status_reason_codes"]
    assert payload["migration_head_revisions"]
    assert ".venv/bin/python -m alembic upgrade head" in payload["migration_command_hint"]
    assert "DB_HOST" in payload["db_environment_override_hint"]
    assert "Schema And Migrations" in markdown
    assert "schema_missing" in markdown


def test_db_status_reports_candle_table_with_unknown_migration_version() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _instrument_key = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=[Decimal(str(100 + index)) for index in range(3)],
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    status = inspect_strategy_validation_database_status(service)
    payload = money_flow_evidence_review_database_status_to_dict(status)

    assert payload["reachable"] is True
    assert payload["candles_table_exists"] is True
    assert payload["persisted_candle_count"] == 3
    assert payload["alembic_version_table_exists"] is False
    assert payload["migrations_current"] is None
    assert payload["schema_ready_for_evidence_generation"] is False
    assert payload["schema_status"] == "schema_present_migration_version_unknown"
    assert "schema_present_migration_version_unknown" in payload["schema_status_reason_codes"]
    assert "schema_not_ready_for_evidence_generation" in payload["schema_status_reason_codes"]


def test_canonical_audit_blocks_missing_schema_with_migration_reasons() -> None:
    settings = build_settings()
    session_factory = _blank_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 13, 55, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["database_status"]["schema_status"] == "schema_missing"
    assert payload["database_status"]["schema_ready_for_evidence_generation"] is False
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["generated_campaign_count"] == 0
    assert payload["blocked_campaign_count"] == 2
    assert all(
        "schema_missing" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert all(
        "candles_table_missing" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert "Migration command hint" in markdown
    assert "No evidence packs were generated" in markdown


def test_seeded_sufficient_data_generates_evidence_pack_and_keeps_collision_truth(
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
        run_timestamp=datetime(2026, 5, 3, 14, 5, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 14, 5, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["database_status"]["candles_table_exists"] is True
    assert payload["database_status"]["schema_status"] == "migrated_schema_ready"
    assert payload["database_status"]["schema_ready_for_evidence_generation"] is True
    assert payload["database_status"]["persisted_candle_count"] == 36
    assert payload["generated_campaign_count"] == 1
    assert payload["blocked_campaign_count"] == 0
    assert payload["campaign_results"][0]["evidence_pack_generated"] is True
    pack_path = Path(payload["campaign_results"][0]["evidence_pack_path"])
    manifest = json.loads((pack_path / "manifest.json").read_text())
    assert manifest["evidence_pack_collision_policy"] == "unique_suffix"
    assert manifest["final_evidence_pack_path"] == str(pack_path)
    assert manifest["window_convention_display"] == "(start_at, end_at]"
    assert manifest["no_live_execution_artifacts_created"] is True
    assert manifest["exchange_adapters_called"] is False

    _assert_no_live_artifacts(session_factory)


def test_evidence_review_cli_exposes_db_status_only_help() -> None:
    help_text = build_review_parser().format_help()
    normalized = " ".join(help_text.split())

    assert "--db-status-only" in help_text
    assert "migration/schema status" in normalized
    assert "DB_HOST" in normalized
    assert "never routes, trades, optimizes, or calls exchange adapters" in normalized
