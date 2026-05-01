from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import StrategyValidationFillTiming, Timeframe
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
from scripts.run_money_flow_backtest import build_parser as build_single_run_parser
from scripts.run_money_flow_research_campaign import build_parser as build_campaign_parser
from services.strategy_validation import (
    MoneyFlowBacktestService,
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    build_money_flow_research_campaign_batch_request,
    load_money_flow_research_campaign_config,
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
    components: list[str] | None = None,
    fill_timings: list[str] | None = None,
    windows: list[dict[str, str | None]] | None = None,
) -> dict[str, object]:
    return {
        "campaign_name": "sv1_3_campaign_truth_test",
        "description": "Focused SV1.3 campaign test config.",
        "environment": "testnet",
        "venue": "hyperliquid",
        "symbols": [
            {
                "symbol": "BTC",
                "instrument_key": instrument_key,
            }
        ],
        "components": components or ["sleeve_15m"],
        "fill_timings": fill_timings or ["next_candle_open"],
        "windows": windows
        or [
            {
                "label": "test_window",
                "start": _iso(start),
                "end": _iso(end),
                "description": "Primary test window.",
                "expected_regime_label": "uptrend",
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


def test_single_run_cli_help_uses_start_exclusive_window_convention() -> None:
    help_text = build_single_run_parser().format_help()

    assert "Inclusive ISO-8601 start" not in help_text
    assert "Closes exactly at start are excluded" in help_text
    assert "Closes on or before end are included" in help_text
    assert "(start, end]" in help_text


def test_campaign_config_parsing_and_named_windows_build_batch_request(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    midpoint = datetime(2026, 1, 15, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    raw = _campaign_raw(
        output_dir=tmp_path,
        instrument_key="perpetual:linear:BTC:USDC:USDC",
        start=start,
        end=end,
        components=["sleeve_15m", "sleeve_1h"],
        fill_timings=[
            "same_candle_close_research_only",
            "next_candle_open",
            "next_candle_close",
        ],
        windows=[
            {
                "label": "jan_first_half",
                "start": _iso(start),
                "end": _iso(midpoint),
                "description": "First adjacent window.",
                "expected_regime_label": "uptrend",
            },
            {
                "label": "jan_second_half",
                "start": _iso(midpoint),
                "end": _iso(end),
                "description": "Second adjacent window.",
                "expected_regime_label": "sideways",
            },
        ],
    )

    config_path = tmp_path / "campaign.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    config = load_money_flow_research_campaign_config(config_path)
    batch_request = build_money_flow_research_campaign_batch_request(config)

    assert config.campaign_name == "sv1_3_campaign_truth_test"
    assert [window.label for window in config.windows] == ["jan_first_half", "jan_second_half"]
    assert len(batch_request.runs) == 12
    assert {run.component_keys for run in batch_request.runs} == {("sleeve_15m",), ("sleeve_1h",)}
    assert {run.assumptions.fill_timing for run in batch_request.runs} == {
        StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY,
        StrategyValidationFillTiming.NEXT_CANDLE_OPEN,
        StrategyValidationFillTiming.NEXT_CANDLE_CLOSE,
    }


def test_campaign_evidence_pack_writes_manifest_reports_and_preserves_boundaries(tmp_path: Path) -> None:
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
            run_timestamp=datetime(2026, 5, 1, 21, 30, tzinfo=UTC),
        )
    )

    assert result.evidence_pack_dir.exists()
    expected_files = {
        "campaign_config.json",
        "batch_report.json",
        "batch_report.md",
        "manifest.json",
        "README.md",
    }
    assert expected_files.issubset({path.name for path in result.evidence_pack_dir.iterdir()})

    manifest = json.loads((result.evidence_pack_dir / "manifest.json").read_text())
    markdown = (result.evidence_pack_dir / "batch_report.md").read_text()

    assert manifest["campaign_name"] == "sv1_3_campaign_truth_test"
    assert manifest["window_convention"] == STRATEGY_VALIDATION_WINDOW_CONVENTION
    assert manifest["window_convention_display"] == "(start_at, end_at]"
    assert manifest["blocked_run_count"] == 0
    assert manifest["report_paths"]["batch_report_json"] == "batch_report.json"
    assert manifest["report_paths"]["batch_report_markdown"] == "batch_report.md"
    assert len(manifest["assumptions_hash"]) == 64
    assert manifest["run_contexts"][0]["window_label"] == "test_window"
    assert manifest["no_live_execution_artifacts_created"] is True
    assert manifest["exchange_adapters_called"] is False

    assert "Money Flow Research Campaign Evidence Pack" in markdown
    assert "sv1_3_campaign_truth_test" in markdown
    assert "test_window" in markdown
    assert "(start_at, end_at]" in markdown
    assert "Blocked Runs" in markdown
    assert "recommended strategy" not in markdown.lower()
    assert "recommended component" not in markdown.lower()
    assert "optimal" not in markdown.lower()
    assert "best strategy" not in markdown.lower()

    _assert_no_live_artifacts(session_factory)


def test_campaign_adjacent_named_windows_do_not_double_count_boundary_candle(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(10)]
    start, delta = seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=closes,
    )
    boundary = start + (delta * 5)
    config = money_flow_research_campaign_config_from_dict(
        _campaign_raw(
            output_dir=tmp_path,
            instrument_key=instrument_key,
            start=start,
            end=start + (delta * len(closes)),
            windows=[
                {
                    "label": "first_window",
                    "start": _iso(start),
                    "end": _iso(boundary),
                    "description": "First adjacent window.",
                    "expected_regime_label": "uptrend",
                },
                {
                    "label": "second_window",
                    "start": _iso(boundary),
                    "end": _iso(start + (delta * len(closes))),
                    "description": "Second adjacent window.",
                    "expected_regime_label": "sideways",
                },
            ],
        )
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    result = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=datetime(2026, 5, 1, 21, 35, tzinfo=UTC),
        )
    )

    assert all(run.report is not None for run in result.batch_report.run_reports)
    first_component = result.batch_report.run_reports[0].report.component_reports[0]  # type: ignore[union-attr]
    second_component = result.batch_report.run_reports[1].report.component_reports[0]  # type: ignore[union-attr]
    assert first_component.evaluated_candles == 5
    assert second_component.evaluated_candles == 5
    assert first_component.data_coverage is not None
    assert second_component.data_coverage is not None
    assert first_component.data_coverage.last_candle_available_at == boundary
    assert second_component.data_coverage.first_candle_available_at == boundary + delta
    assert first_component.evaluated_candles + second_component.evaluated_candles == len(closes)
    assert result.manifest["run_contexts"][0]["window_label"] == "first_window"
    assert result.manifest["run_contexts"][1]["window_label"] == "second_window"


def test_campaign_keeps_blocked_runs_visible_in_manifest_and_markdown(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    closes = [Decimal(str(100 + index)) for index in range(12)]
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
            components=["sleeve_15m", "missing_sleeve"],
        )
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    result = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=datetime(2026, 5, 1, 21, 40, tzinfo=UTC),
        )
    )
    manifest = json.loads((result.evidence_pack_dir / "manifest.json").read_text())
    batch_payload = json.loads((result.evidence_pack_dir / "batch_report.json").read_text())
    markdown = (result.evidence_pack_dir / "batch_report.md").read_text()

    assert manifest["blocked_run_count"] == 1
    assert manifest["blocked_reason_counts"]["strategy_validation_run_blocked"] == 1
    assert any(context["status"] == "blocked" for context in manifest["run_contexts"])
    component_rows = batch_payload["comparison_summary"]["component_comparison"]
    missing_row = next(row for row in component_rows if row["component_keys"] == "missing_sleeve")
    assert missing_row["blocked_run_count"] == 1
    assert missing_row["completed_run_count"] == 0
    assert "strategy_validation_run_blocked" in markdown
    assert "Blocked run count: `1`" in markdown


def test_campaign_cli_help_is_research_only_and_window_truthful() -> None:
    help_text = build_campaign_parser().format_help()
    normalized_help = " ".join(help_text.split())

    assert "--config" in help_text
    assert "--output-dir" in help_text
    assert "--format" in help_text
    assert "(start, end]" in help_text
    assert "does not optimize" in normalized_help
    assert "call exchange adapters" in normalized_help
