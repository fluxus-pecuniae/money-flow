from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

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
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    money_flow_research_campaign_config_from_dict,
    run_money_flow_research_campaign,
)
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _campaign_raw(
    *,
    output_dir: Path,
    instrument_key: str,
    start: datetime,
    end: datetime,
) -> dict[str, object]:
    return {
        "campaign_name": "sv1_4_1_evidence_integrity_test",
        "description": "Focused SV1.4.1 evidence-pack collision test config.",
        "environment": "testnet",
        "venue": "hyperliquid",
        "symbols": [
            {
                "symbol": "BTC",
                "instrument_key": instrument_key,
            }
        ],
        "components": ["sleeve_15m"],
        "fill_timings": ["next_candle_open"],
        "windows": [
            {
                "label": "collision_window",
                "start": _iso(start),
                "end": _iso(end),
                "description": "Collision safety test window.",
                "expected_regime_label": "founder_review_required",
            }
        ],
        "fee_bps_values": ["0"],
        "slippage_bps_values": ["0"],
        "initial_capital": "10000",
        "position_notional_pct": "1.0",
        "output_dir": str(output_dir),
        "report_formats": ["json", "markdown"],
    }


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


def test_same_timestamp_campaign_runs_use_unique_suffix_without_overwrite(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
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
    config = money_flow_research_campaign_config_from_dict(
        _campaign_raw(
            output_dir=tmp_path,
            instrument_key=instrument_key,
            start=start,
            end=start + (delta * len(closes)),
        )
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    run_timestamp = datetime(2026, 5, 2, 7, 0, tzinfo=UTC)

    first = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=run_timestamp,
        )
    )
    first_manifest_path = first.evidence_pack_dir / "manifest.json"
    first_report_path = first.evidence_pack_dir / "batch_report.json"
    first_manifest_before = first_manifest_path.read_text()
    first_report_before = first_report_path.read_text()

    second = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=run_timestamp,
        )
    )

    assert first.evidence_pack_dir != second.evidence_pack_dir
    assert first.evidence_pack_dir.name == "20260502T070000Z"
    assert second.evidence_pack_dir.name == "20260502T070000Z-001"
    assert first_manifest_path.read_text() == first_manifest_before
    assert first_report_path.read_text() == first_report_before

    first_manifest = json.loads(first_manifest_before)
    second_manifest = json.loads((second.evidence_pack_dir / "manifest.json").read_text())
    assert first_manifest["evidence_pack_collision_policy"] == "unique_suffix"
    assert first_manifest["evidence_pack_collision_occurred"] is False
    assert first_manifest["evidence_pack_collision_suffix"] is None
    assert first_manifest["requested_run_id"] == "20260502T070000Z"
    assert first_manifest["final_run_id"] == "20260502T070000Z"
    assert first_manifest["final_evidence_pack_path"] == str(first.evidence_pack_dir)
    assert second_manifest["evidence_pack_collision_policy"] == "unique_suffix"
    assert second_manifest["evidence_pack_collision_occurred"] is True
    assert second_manifest["evidence_pack_collision_suffix"] == "001"
    assert second_manifest["requested_run_id"] == "20260502T070000Z"
    assert second_manifest["final_run_id"] == "20260502T070000Z-001"
    assert second_manifest["final_evidence_pack_path"] == str(second.evidence_pack_dir)
    assert second_manifest["report_paths"]["manifest"] == "manifest.json"

    _assert_no_live_artifacts(session_factory)


def test_fail_if_exists_collision_policy_fails_without_mutating_original_pack(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
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
    config = money_flow_research_campaign_config_from_dict(
        _campaign_raw(
            output_dir=tmp_path,
            instrument_key=instrument_key,
            start=start,
            end=start + (delta * len(closes)),
        )
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)
    run_timestamp = datetime(2026, 5, 2, 7, 1, tzinfo=UTC)

    first = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=run_timestamp,
            evidence_pack_collision_policy="fail_if_exists",
        )
    )
    first_manifest_path = first.evidence_pack_dir / "manifest.json"
    first_manifest_before = first_manifest_path.read_text()

    with pytest.raises(FileExistsError, match="fail_if_exists"):
        asyncio.run(
            run_money_flow_research_campaign(
                config,
                service=service,
                run_timestamp=run_timestamp,
                evidence_pack_collision_policy="fail_if_exists",
            )
        )

    assert first_manifest_path.read_text() == first_manifest_before
    assert sorted(path.name for path in first.evidence_pack_dir.parent.iterdir()) == [
        "20260502T070100Z"
    ]

    _assert_no_live_artifacts(session_factory)


def test_generated_evidence_packs_remain_excluded_from_review_bundles() -> None:
    archiveignore = Path(".archiveignore").read_text()
    gitignore = Path(".gitignore").read_text()

    assert MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY == "unique_suffix"
    assert "reports/strategy_validation" in archiveignore
    assert "reports/strategy_validation/" in gitignore
