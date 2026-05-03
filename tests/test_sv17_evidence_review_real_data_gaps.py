from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, func, select
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
    money_flow_evidence_review_to_markdown,
    review_money_flow_evidence,
)
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)
from test_sv15_historical_data_readiness import _campaign_raw


class _FailingSessionFactory:
    def __call__(self):
        raise RuntimeError("failed to resolve host 'postgres'")


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
    raw["campaign_name"] = "sv1_7_seeded_real_evidence_campaign"
    raw["description"] = "Seeded SV1.7 evidence generation campaign."
    raw["windows"][0]["label"] = "sv1_7_seeded_window"
    config_path = tmp_path / "sv1_7_seeded_campaign.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    return config_path


def _blocked_campaign_config_path(tmp_path: Path) -> Path:
    raw = _campaign_raw(
        output_dir=tmp_path,
        instrument_key="perpetual:linear:MISSING:USDC:USDC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    raw["campaign_name"] = "sv1_7_missing_data_campaign"
    raw["description"] = "Seeded SV1.7 missing-data campaign."
    raw["symbols"] = [
        {
            "symbol": "MISSING",
            "instrument_key": "perpetual:linear:MISSING:USDC:USDC",
        }
    ]
    raw["windows"][0]["label"] = "sv1_7_missing_window"
    config_path = tmp_path / "sv1_7_missing_campaign.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    return config_path


def test_evidence_review_reports_unreachable_database_as_data_gap() -> None:
    settings = build_settings(DB_HOST="postgres")
    service = MoneyFlowBacktestService(settings, session_factory=_FailingSessionFactory())

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 6, 40, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["database_status"]["reachable"] is False
    assert payload["database_status"]["candles_table_exists"] is False
    assert payload["database_status"]["blocking_error_type"] == "RuntimeError"
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["generated_campaign_count"] == 0
    assert payload["blocked_campaign_count"] == 2
    assert all(
        "database_host_unresolved" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert "Database Access" in markdown
    assert "failed to resolve host" in markdown
    assert "No evidence packs were generated" in markdown


def test_evidence_review_reports_reachable_database_missing_candles_table() -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    settings = build_settings()
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    database_status = inspect_strategy_validation_database_status(service)
    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 3, 6, 45, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert database_status.reachable is True
    assert database_status.candles_table_exists is False
    assert database_status.persisted_candle_count is None
    assert payload["database_status"]["reachable"] is True
    assert payload["database_status"]["candles_table_exists"] is False
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert all(
        "candles_table_missing" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    assert all(
        "blocked_campaign_rows" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )


def test_partial_evidence_status_is_visible_for_mixed_generated_and_blocked_campaigns(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    seeded_config = _seeded_campaign_config_path(tmp_path, session_factory)
    blocked_config = _blocked_campaign_config_path(tmp_path)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (seeded_config, blocked_config),
        service=service,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 6, 50, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 6, 50, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["database_status"]["reachable"] is True
    assert payload["database_status"]["candles_table_exists"] is True
    assert payload["database_status"]["persisted_candle_count"] == 36
    assert payload["paper_readiness_review_status"] == "partial_evidence_ready_with_data_gaps"
    assert payload["generated_campaign_count"] == 1
    assert payload["blocked_campaign_count"] == 1
    assert payload["campaign_results"][0]["evidence_pack_generated"] is True
    assert payload["campaign_results"][1]["readiness_status"] == "insufficient_data"
    assert "unknown_instrument_key" in payload["campaign_results"][1]["blocked_or_gap_reason_codes"]
    assert "partial_evidence_ready_with_data_gaps" in markdown
    assert "at least one campaign generated a pack while another canonical campaign remains blocked" in markdown
    assert "best strategy" not in markdown.lower()
    assert "recommended strategy" not in markdown.lower()
    assert "optimal" not in markdown.lower()

    _assert_no_live_artifacts(session_factory)
