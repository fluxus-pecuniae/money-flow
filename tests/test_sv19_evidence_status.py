from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text

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
    money_flow_evidence_review_database_status_to_dict,
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


def _seed_outdated_alembic_version(session_factory) -> None:
    with session_factory() as session:
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        session.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
            {"version_num": "20260402_0001"},
        )
        session.commit()


def _seeded_campaign_config_path(tmp_path: Path, session_factory, *, name: str) -> Path:
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
    raw["campaign_name"] = name
    raw["description"] = f"Seeded {name} campaign."
    raw["windows"][0]["label"] = f"{name}_window"
    config_path = tmp_path / f"{name}.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    return config_path


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


def test_db_target_status_reports_host_port_name_and_target_role() -> None:
    settings = build_settings(
        DB_HOST="127.0.0.1",
        DB_PORT=54322,
        DB_NAME="postgres",
        DB_USER="postgres",
        DB_PASSWORD="postgres",
    )
    session_factory = build_test_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    status = inspect_strategy_validation_database_status(service)
    payload = money_flow_evidence_review_database_status_to_dict(status)

    assert payload["configured_database_url"] == (
        "postgresql+psycopg://postgres:***@127.0.0.1:54322/postgres"
    )
    assert payload["database_driver"] == "postgresql+psycopg"
    assert payload["database_host"] == "127.0.0.1"
    assert payload["database_port"] == 54322
    assert payload["database_name"] == "postgres"
    assert payload["database_username"] == "postgres"
    assert payload["database_target_role"] == (
        "maintenance_database_name_requires_operator_confirmation"
    )
    assert payload["intended_strategy_validation_database"] is False
    assert "strategy_validation_db_target_ambiguous" in payload[
        "database_target_warning_reason_codes"
    ]


def test_outdated_migration_revision_blocks_evidence_pack_generation(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(
        tmp_path,
        session_factory,
        name="sv1_9_outdated_migration_campaign",
    )
    _seed_outdated_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 20, 10, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 20, 10, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["database_status"]["candles_table_exists"] is True
    assert payload["database_status"]["alembic_version_table_exists"] is True
    assert payload["database_status"]["migrations_current"] is False
    assert payload["database_status"]["schema_status"] == "migrations_out_of_date"
    assert "database_schema_outdated" in payload["database_status"][
        "schema_status_reason_codes"
    ]
    assert "migrations_out_of_date" in payload["campaign_results"][0][
        "blocked_or_gap_reason_codes"
    ]
    assert payload["generated_campaign_count"] == 0
    assert payload["campaign_results"][0]["evidence_pack_generated"] is False
    assert not (tmp_path / "sv1_9_outdated_migration_campaign").exists()

    _assert_no_live_artifacts(session_factory)


def test_missing_canonical_candles_are_reported_as_import_requirements() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 20, 15, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["database_status"]["schema_status"] == "migrated_schema_ready"
    assert payload["generated_campaign_count"] == 0
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["canonical_candle_import_requirements"]
    first_requirement = payload["canonical_candle_import_requirements"][0]
    assert first_requirement["symbol"] in {"BTC", "ETH", "SOL"}
    assert first_requirement["required_file_format"].startswith("CSV or JSON")
    assert "scripts/import_strategy_validation_candles.py" in first_requirement[
        "example_import_command"
    ]
    assert "Canonical Candle Import Requirements" in markdown
    assert "Use these rows only after the intended database is reachable" in markdown
    assert "scripts/import_strategy_validation_candles.py" in markdown
    assert "best strategy" not in markdown.lower()
    assert "recommended strategy" not in markdown.lower()
    assert "optimal" not in markdown.lower()

    _assert_no_live_artifacts(session_factory)


def test_seeded_sufficient_data_still_generates_pack_with_current_schema_truth(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(
        tmp_path,
        session_factory,
        name="sv1_9_seeded_pack_campaign",
    )
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 20, 20, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 20, 20, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["database_status"]["schema_status"] == "migrated_schema_ready"
    assert payload["generated_campaign_count"] == 1
    assert payload["blocked_campaign_count"] == 0
    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert payload["canonical_candle_import_requirements"] == []
    pack_path = Path(payload["generated_evidence_pack_paths"][0])
    assert (pack_path / "manifest.json").exists()
    assert (pack_path / "batch_report.json").exists()

    _assert_no_live_artifacts(session_factory)
