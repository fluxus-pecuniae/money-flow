from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

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
from scripts.run_money_flow_research_campaign import build_parser as build_campaign_parser
from services.strategy_validation import (
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    MoneyFlowBacktestService,
    audit_money_flow_research_campaign_data_readiness,
    build_money_flow_research_campaign_batch_request,
    load_money_flow_research_campaign_config,
    money_flow_research_campaign_config_from_dict,
    money_flow_research_campaign_data_readiness_to_dict,
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
    windows: list[dict[str, str | None]] | None = None,
    components: list[str] | None = None,
) -> dict[str, object]:
    return {
        "campaign_name": "sv1_4_evidence_readiness_test",
        "description": "Focused SV1.4 data-readiness and evidence-review test config.",
        "window_convention": "(start_at, end_at]",
        "environment": "testnet",
        "venue": "hyperliquid",
        "symbols": [
            {
                "symbol": "BTC",
                "instrument_key": instrument_key,
            }
        ],
        "components": components or ["sleeve_15m"],
        "fill_timings": ["next_candle_open"],
        "windows": windows
        or [
            {
                "label": "review_window",
                "start": _iso(start),
                "end": _iso(end),
                "description": "Review test window.",
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


def test_canonical_research_campaign_configs_parse_successfully() -> None:
    config_paths = sorted(Path("configs/strategy_validation/campaigns").glob("*.json"))

    assert {path.name for path in config_paths} == {
        "money_flow_core_btc.json",
        "money_flow_core_multi_symbol.json",
    }
    for config_path in config_paths:
        raw = json.loads(config_path.read_text())
        config = load_money_flow_research_campaign_config(config_path)
        batch_request = build_money_flow_research_campaign_batch_request(config)

        assert raw["window_convention"].startswith("(start_at, end_at]")
        assert config.components == ("sleeve_15m", "sleeve_1h", "sleeve_4h")
        assert len(config.fill_timings) == 3
        assert len(config.windows) >= 2
        assert batch_request.runs


def test_campaign_data_readiness_audit_reports_covered_thin_and_missing_windows(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(7)]
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
            end=start + (delta * 12),
            windows=[
                {
                    "label": "covered_window",
                    "start": _iso(start),
                    "end": _iso(start + (delta * 5)),
                    "description": "Complete coverage window.",
                    "expected_regime_label": "founder_review_required",
                },
                {
                    "label": "thin_window",
                    "start": _iso(start + (delta * 5)),
                    "end": _iso(start + (delta * 10)),
                    "description": "Thin coverage window.",
                    "expected_regime_label": "founder_review_required",
                },
                {
                    "label": "missing_window",
                    "start": _iso(start + (delta * 10)),
                    "end": _iso(start + (delta * 12)),
                    "description": "Missing coverage window.",
                    "expected_regime_label": "founder_review_required",
                },
            ],
        )
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    audit = audit_money_flow_research_campaign_data_readiness(
        config,
        service=service,
        generated_at=datetime(2026, 5, 2, 5, 30, tzinfo=UTC),
    )
    payload = money_flow_research_campaign_data_readiness_to_dict(audit)
    rows = {row["window_label"]: row for row in payload["rows"]}

    assert payload["window_convention"] == STRATEGY_VALIDATION_WINDOW_CONVENTION
    assert payload["window_convention_display"] == "(start_at, end_at]"
    assert rows["covered_window"]["readiness_status"] == "covered"
    assert rows["covered_window"]["expected_candle_count"] == 5
    assert rows["covered_window"]["actual_candle_count"] == 5
    assert rows["covered_window"]["coverage_percent"] == "1.00000000"
    assert rows["thin_window"]["readiness_status"] == "thin"
    assert rows["thin_window"]["expected_candle_count"] == 5
    assert rows["thin_window"]["actual_candle_count"] == 2
    assert "data_coverage_below_review_threshold" in rows["thin_window"]["warning_reason_codes"]
    assert rows["missing_window"]["readiness_status"] == "missing"
    assert rows["missing_window"]["expected_candle_count"] == 2
    assert rows["missing_window"]["actual_candle_count"] == 0
    assert rows["missing_window"]["likely_blocked"] is True
    assert "no_candles_in_requested_window" in rows["missing_window"]["likely_blocked_reason_codes"]
    assert payload["summary"]["covered_row_count"] == 1
    assert payload["summary"]["thin_row_count"] == 1
    assert payload["summary"]["missing_row_count"] == 1
    assert payload["summary"]["paper_trading_auto_approved"] is False
    assert payload["summary"]["creates_live_artifacts"] is False
    assert payload["summary"]["calls_exchange_adapters"] is False

    _assert_no_live_artifacts(session_factory)


def test_evidence_pack_includes_review_checklist_and_manual_readiness_criteria(tmp_path: Path) -> None:
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

    result = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=datetime(2026, 5, 2, 5, 35, tzinfo=UTC),
        )
    )

    manifest = json.loads((result.evidence_pack_dir / "manifest.json").read_text())
    markdown = (result.evidence_pack_dir / "batch_report.md").read_text()

    assert "review_checklist" in manifest
    assert "data_quality" in manifest["review_checklist"]
    assert "manual_paper_trading_readiness_criteria" in manifest
    assert any(
        "not an automated go/no-go decision" in item
        for item in manifest["manual_paper_trading_readiness_criteria"]
    )
    assert "Evidence-Pack Review Checklist" in markdown
    assert "Manual Paper-Trading Readiness Criteria" in markdown
    assert "do not auto-approve paper trading" in markdown
    assert "optimal" not in markdown.lower()
    assert "recommended component" not in markdown.lower()
    assert "best strategy" not in markdown.lower()

    _assert_no_live_artifacts(session_factory)


def test_campaign_cli_exposes_audit_only_mode_without_live_action_language() -> None:
    help_text = build_campaign_parser().format_help()
    normalized_help = " ".join(help_text.split())

    assert "--audit-only" in help_text
    assert "writes no evidence pack" in normalized_help
    assert "Does not run strategy validation" in normalized_help
    assert "call exchange adapters" in normalized_help
    assert "(start, end]" in help_text
