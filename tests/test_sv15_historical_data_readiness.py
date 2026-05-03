from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.domain.enums import Environment, Timeframe
from db.models import (
    CandleModel,
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
from scripts.import_strategy_validation_candles import build_parser as build_import_parser
from scripts.run_money_flow_research_campaign import build_parser as build_campaign_parser
from services.strategy_validation import (
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    audit_money_flow_research_campaign_data_readiness,
    import_strategy_validation_candles_from_path,
    load_money_flow_research_campaign_config,
    money_flow_research_campaign_config_from_dict,
    money_flow_research_campaign_data_readiness_to_dict,
    money_flow_research_campaign_data_readiness_to_markdown,
    run_money_flow_research_campaign,
    strategy_validation_candle_import_result_to_dict,
)
from test_sv10_strategy_validation import (
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_symbol,
)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


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


def _campaign_raw(
    *,
    output_dir: Path,
    instrument_key: str,
    start: datetime,
    end: datetime,
) -> dict[str, object]:
    return {
        "campaign_name": "money_flow_core_btc",
        "description": "SV1.5 first canonical evidence generation smoke config.",
        "window_convention": "(start_at, end_at] candle closes; platform convention is authoritative.",
        "environment": "testnet",
        "venue": "hyperliquid",
        "symbols": [{"symbol": "BTC", "instrument_key": instrument_key}],
        "components": ["sleeve_15m"],
        "fill_timings": ["next_candle_open"],
        "windows": [
            {
                "label": "seeded_window",
                "start": _iso(start),
                "end": _iso(end),
                "description": "Seeded SV1.5 evidence-generation smoke window.",
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


def test_campaign_window_convention_mismatch_fails_clearly(tmp_path: Path) -> None:
    raw = _campaign_raw(
        output_dir=tmp_path,
        instrument_key="perpetual:linear:BTC:USDC:USDC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    raw["window_convention"] = "[start_at, end_at] inclusive start"

    with pytest.raises(ValueError, match="window_convention.*platform convention"):
        money_flow_research_campaign_config_from_dict(raw)


def test_canonical_campaign_audit_path_surfaces_missing_and_thin_data(tmp_path: Path) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _instrument_key = seed_symbol(session_factory)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.M15,
        closes=[Decimal(str(100 + index)) for index in range(12)],
    )
    config = load_money_flow_research_campaign_config(
        Path("configs/strategy_validation/campaigns/money_flow_core_btc.json")
    )
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    audit = audit_money_flow_research_campaign_data_readiness(
        config,
        service=service,
        generated_at=datetime(2026, 5, 2, 7, 45, tzinfo=UTC),
    )
    payload = money_flow_research_campaign_data_readiness_to_dict(audit)
    markdown = money_flow_research_campaign_data_readiness_to_markdown(audit)

    assert payload["campaign_name"] == "money_flow_core_btc"
    assert payload["summary"]["row_count"] == 6
    assert payload["summary"]["thin_row_count"] >= 1
    assert payload["summary"]["missing_row_count"] >= 1
    assert "BTC" in payload["summary"]["symbols_with_data"]
    assert "sleeve_15m" in payload["summary"]["components_with_data"]
    assert "sleeve_1h" in payload["summary"]["components_missing_data"]
    assert payload["summary"]["paper_trading_auto_approved"] is False
    assert payload["summary"]["creates_live_artifacts"] is False
    assert payload["summary"]["calls_exchange_adapters"] is False
    assert "(start_at, end_at]" in markdown
    assert "Founder Review Summary" in markdown
    assert "Missing-Data Remediation Notes" in markdown
    assert "Backfill or import public historical candles" in markdown
    assert "not an optimization" in markdown

    _assert_no_live_artifacts(session_factory)


def test_historical_candle_csv_import_is_duplicate_safe_and_research_only(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "\n".join(
            [
                "symbol,instrument_key,open_time,close_time,open,high,low,close,volume,trade_count",
                "BTC,"
                f"{instrument_key},"
                "2026-01-01T00:00:00Z,2026-01-01T00:15:00Z,"
                "100,101,99,100.5,10,2",
                "BTC,"
                f"{instrument_key},"
                "2026-01-01T00:15:00Z,2026-01-01T00:30:00Z,"
                "100.5,102,100,101.5,12,3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    first = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        source_label="public_fixture",
        session_factory=session_factory,
    )
    second = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        source_label="public_fixture",
        session_factory=session_factory,
    )
    first_payload = strategy_validation_candle_import_result_to_dict(first)
    second_payload = strategy_validation_candle_import_result_to_dict(second)

    assert first_payload["inserted_count"] == 2
    assert first_payload["updated_count"] == 0
    assert first_payload["unchanged_count"] == 0
    assert "source_label_recorded_in_import_summary_only" in first_payload["warning_reason_codes"]
    assert second_payload["inserted_count"] == 0
    assert second_payload["updated_count"] == 0
    assert second_payload["unchanged_count"] == 2
    assert second_payload["creates_live_artifacts"] is False
    assert second_payload["calls_exchange_adapters"] is False
    assert second_payload["calls_private_exchange_endpoints"] is False
    assert second_payload["calls_exchange_order_endpoints"] is False

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 2
        assert session.scalar(
            select(func.count()).select_from(CandleModel).where(
                CandleModel.instrument_ref_id == instrument_ref_id,
                CandleModel.symbol_id == symbol_id,
            )
        ) == 2
    _assert_no_live_artifacts(session_factory)


def test_first_canonical_evidence_generation_path_preserves_collision_safety(
    tmp_path: Path,
) -> None:
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
    run_timestamp = datetime(2026, 5, 2, 7, 55, tzinfo=UTC)

    first = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=run_timestamp,
        )
    )
    first_manifest_before = (first.evidence_pack_dir / "manifest.json").read_text()
    second = asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            run_timestamp=run_timestamp,
        )
    )
    second_manifest = json.loads((second.evidence_pack_dir / "manifest.json").read_text())

    assert MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY == "unique_suffix"
    assert first.evidence_pack_dir.name == "20260502T075500Z"
    assert second.evidence_pack_dir.name == "20260502T075500Z-001"
    assert (first.evidence_pack_dir / "manifest.json").read_text() == first_manifest_before
    assert second_manifest["evidence_pack_collision_policy"] == "unique_suffix"
    assert second_manifest["evidence_pack_collision_occurred"] is True
    assert second_manifest["evidence_pack_collision_suffix"] == "001"
    assert second_manifest["final_evidence_pack_path"] == str(second.evidence_pack_dir)
    assert second_manifest["window_convention_display"] == "(start_at, end_at]"
    assert second_manifest["blocked_run_count"] == 0
    assert second_manifest["no_live_execution_artifacts_created"] is True
    assert second_manifest["exchange_adapters_called"] is False

    _assert_no_live_artifacts(session_factory)


def test_import_and_campaign_cli_help_are_research_only_and_truthful() -> None:
    import_help = build_import_parser().format_help()
    campaign_help = build_campaign_parser().format_help()
    normalized_import = " ".join(import_help.split())
    normalized_campaign = " ".join(campaign_help.split())

    assert "--source-label" in import_help
    assert "--assume-naive-utc" in import_help
    assert "naive timestamps are rejected" in normalized_import
    assert "timestamp_assumption=assume_naive_utc" in normalized_import
    assert "does not call exchanges" in normalized_import
    assert "does not create live trading artifacts" in normalized_import
    assert "--audit-format" in campaign_help
    assert "Markdown is founder-readable" in campaign_help
    assert "writes no evidence pack" in normalized_campaign
    assert "does not optimize" in normalized_campaign
