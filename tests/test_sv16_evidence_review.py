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
from scripts.review_money_flow_evidence_packs import build_parser as build_review_parser
from services.strategy_validation import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    money_flow_evidence_review_to_dict,
    money_flow_evidence_review_to_markdown,
    money_flow_research_campaign_config_from_dict,
    review_money_flow_evidence,
)
from services.strategy_validation.evidence_review import _migration_head_revisions
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)
from test_sv15_historical_data_readiness import _campaign_raw, _iso


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
    raw["campaign_name"] = "sv1_6_seeded_review_campaign"
    raw["description"] = "Seeded SV1.6 evidence review campaign."
    raw["windows"][0]["label"] = "sv1_6_seeded_window"
    config_path = tmp_path / "sv1_6_campaign.json"
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


def test_canonical_campaign_review_reports_insufficient_data_without_packs() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 5, 40, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["generated_campaign_count"] == 0
    assert payload["blocked_campaign_count"] == 2
    assert [result["campaign_name"] for result in payload["campaign_results"]] == [
        "money_flow_core_btc",
        "money_flow_core_multi_symbol",
    ]
    assert all(not result["evidence_pack_generated"] for result in payload["campaign_results"])
    assert all(
        "alembic_version_missing" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert all(
        "schema_not_ready_for_evidence_generation"
        in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert "insufficient data" in markdown.lower()
    assert "Missing or thin data is a data-readiness gap" in markdown
    assert "not proof of future profitability" in markdown

    _assert_no_live_artifacts(session_factory)


def test_sufficient_seeded_campaign_generates_evidence_pack_path_in_review_summary(
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
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 6, 0, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 6, 0, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["paper_readiness_review_status"] == "ready_for_founder_review"
    assert payload["generated_campaign_count"] == 1
    result = payload["campaign_results"][0]
    assert result["readiness_status"] == "ready_for_founder_review"
    assert result["evidence_pack_generated"] is True
    evidence_pack_path = Path(result["evidence_pack_path"])
    assert evidence_pack_path.exists()
    assert (evidence_pack_path / "manifest.json").exists()
    assert (evidence_pack_path / "batch_report.json").exists()
    assert result["evidence_pack_manifest"]["evidence_pack_collision_policy"] == "unique_suffix"
    assert result["evidence_pack_manifest"]["evidence_pack_collision_occurred"] is False
    assert result["evidence_pack_manifest"]["no_live_execution_artifacts_created"] is True
    assert result["evidence_pack_manifest"]["exchange_adapters_called"] is False
    assert str(evidence_pack_path) in markdown
    assert "ready_for_founder_review" in markdown

    _assert_no_live_artifacts(session_factory)


def test_same_timestamp_review_preserves_evidence_pack_collision_safety(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(tmp_path, session_factory)
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    run_timestamp = datetime(2026, 5, 3, 6, 15, tzinfo=UTC)

    first = review_money_flow_evidence(
        (config_path,),
        service=service,
        generate_evidence_packs=True,
        run_timestamp=run_timestamp,
        generated_at=run_timestamp,
    )
    first_payload = money_flow_evidence_review_to_dict(first)
    first_path = Path(first_payload["generated_evidence_pack_paths"][0])
    first_manifest_before = (first_path / "manifest.json").read_text()
    first_report_before = (first_path / "batch_report.json").read_text()

    second = review_money_flow_evidence(
        (config_path,),
        service=service,
        generate_evidence_packs=True,
        run_timestamp=run_timestamp,
        generated_at=run_timestamp,
    )
    second_payload = money_flow_evidence_review_to_dict(second)
    second_path = Path(second_payload["generated_evidence_pack_paths"][0])
    second_manifest = json.loads((second_path / "manifest.json").read_text())

    assert MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY == "unique_suffix"
    assert first_path != second_path
    assert first_path.name == "20260503T061500Z"
    assert second_path.name == "20260503T061500Z-001"
    assert (first_path / "manifest.json").read_text() == first_manifest_before
    assert (first_path / "batch_report.json").read_text() == first_report_before
    assert second_manifest["evidence_pack_collision_occurred"] is True
    assert second_manifest["evidence_pack_collision_suffix"] == "001"
    assert second_manifest["final_evidence_pack_path"] == str(second_path)

    _assert_no_live_artifacts(session_factory)


def test_evidence_review_summary_uses_descriptive_manual_status_language(
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
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 6, 30, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 6, 30, tzinfo=UTC),
    )
    markdown = money_flow_evidence_review_to_markdown(review)
    lower = markdown.lower()

    assert "manual paper-readiness review status" in lower
    assert "not an automatic approval" in lower
    assert "does not start paper trading" in lower
    assert "fill timing observations" in lower
    assert "component observations" in lower
    assert "regime observations" in lower
    assert "worst drawdown observations" in lower
    assert "fee/slippage sensitivity observations" in lower
    for prohibited in (
        "best strategy",
        "recommended strategy",
        "recommended component",
        "optimal",
        "proven profitable",
        "paper trading approved",
    ):
        assert prohibited not in lower

    _assert_no_live_artifacts(session_factory)


def test_review_cli_help_is_research_only_and_defaults_to_canonical_configs() -> None:
    help_text = build_review_parser().format_help()
    normalized = " ".join(help_text.split())

    assert "--generate-evidence-packs" in help_text
    assert "--collision-policy" in help_text
    assert "Defaults to the canonical BTC and multi-symbol Money Flow campaign configs" in normalized
    assert "never routes, trades, optimizes, or calls exchange adapters" in normalized


def test_review_can_audit_without_generating_pack_for_sufficient_data(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(tmp_path, session_factory)
    _seed_current_alembic_version(session_factory)
    config = money_flow_research_campaign_config_from_dict(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        generate_evidence_packs=False,
        generated_at=datetime(2026, 5, 3, 7, 0, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert config.campaign_name == "sv1_6_seeded_review_campaign"
    assert payload["paper_readiness_review_status"] == "not_reviewed"
    assert payload["generated_campaign_count"] == 0
    assert payload["campaign_results"][0]["readiness_status"] == "not_reviewed"
    assert payload["campaign_results"][0]["evidence_pack_generated"] is False
    assert not (tmp_path / "sv1_6_seeded_review_campaign").exists()

    _assert_no_live_artifacts(session_factory)
