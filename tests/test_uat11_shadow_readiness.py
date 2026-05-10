from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from core.security import REDACTED_VALUE
from core.logging.setup import redact_structlog_event
from services.uat.drawdown import UATDrawdownObservation, UATDrawdownPolicy
from services.uat.shadow import (
    LIVE_ARTIFACT_TYPE_NAMES,
    UATShadowDrawdownReason,
    UATShadowSignalStatus,
    UATShadowTimingAssumption,
    build_shadow_drawdown_state_from_equity_path,
    create_shadow_signal_audit_record,
    evaluate_uat11_readiness,
    load_uat1_universe_snapshot,
    render_uat11_report,
    verify_shadow_redaction_payloads,
)


def test_shadow_signal_audit_surface_exists_and_supports_uat2_timing() -> None:
    record = create_shadow_signal_audit_record(
        run_id="uat2-shadow-fixture",
        timestamp_utc=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        venue="hyperliquid",
        symbol="ETH",
        market_type="perpetual",
        product_type="perp",
        quote_asset="USDC",
        settlement_asset="USDC",
        component="sleeve_1h",
        timeframe="1h",
        candle_close_time_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
        signal_status=UATShadowSignalStatus.NO_TRADE,
        reason_codes=("uat1_1_fixture_no_strategy_run",),
        operator_visible_explanation="Fixture audit record only; no live strategy loop ran.",
        indicator_summary={"rsi14": "not_evaluated_in_uat1_1"},
        candidate_id="money_flow_hyperliquid_eth_1h_baseline_uat_candidate",
    )

    assert record.signal_status == UATShadowSignalStatus.NO_TRADE
    assert UATShadowTimingAssumption.NEXT_CANDLE_OPEN in record.timing_assumptions_evaluated
    assert UATShadowTimingAssumption.NEXT_CANDLE_CLOSE in record.timing_assumptions_evaluated
    assert UATShadowTimingAssumption.SAME_CANDLE_CLOSE_RESEARCH_ONLY not in record.timing_assumptions_evaluated
    assert record.same_candle_close_research_only is True
    assert record.no_live_artifacts_created is True
    assert record.creates_strategy_decision is False
    assert record.creates_order_intent is False
    assert record.creates_submitted_order is False
    assert "StrategyDecision" in LIVE_ARTIFACT_TYPE_NAMES
    assert "OrderIntent" in LIVE_ARTIFACT_TYPE_NAMES
    assert "SubmittedOrder" in LIVE_ARTIFACT_TYPE_NAMES


def test_shadow_drawdown_state_is_operator_visible_and_not_live_account_truth() -> None:
    state = build_shadow_drawdown_state_from_equity_path(
        run_id="uat2-shadow-fixture",
        candidate_id="money_flow_hyperliquid_eth_1h_baseline_uat_candidate",
        universe_scope="top20_hyperliquid_observation_universe",
        policy=UATDrawdownPolicy(threshold_pct=Decimal("0.10")),
        observations=(
            UATDrawdownObservation(
                timestamp_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
                observed_equity=Decimal("10000"),
            ),
            UATDrawdownObservation(
                timestamp_utc=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
                observed_equity=Decimal("11200"),
            ),
            UATDrawdownObservation(
                timestamp_utc=datetime(2026, 5, 10, 9, 0, tzinfo=UTC),
                observed_equity=Decimal("9800"),
            ),
        ),
    )

    assert state.initial_shadow_equity == Decimal("10000")
    assert state.current_shadow_equity == Decimal("9800")
    assert state.max_shadow_equity == Decimal("11200")
    assert state.min_shadow_equity == Decimal("9800")
    assert state.max_drawdown_amount == Decimal("1400")
    assert state.threshold_breached is True
    assert UATShadowDrawdownReason.THRESHOLD_BREACHED in state.reason_codes
    assert UATShadowDrawdownReason.SOURCE_NOT_LIVE_ACCOUNT in state.reason_codes
    assert UATShadowDrawdownReason.MONITOR_NOT_LIVE_FED in state.reason_codes
    assert state.not_live_account_drawdown is True
    assert state.shadow_simulated_drawdown is True


def test_structured_api_error_and_log_redaction_payloads_are_redacted() -> None:
    redacted = verify_shadow_redaction_payloads()
    rendered = repr(redacted)

    for secret in (
        "api-token-123",
        "db-pass-123",
        "key-123",
        "secret-123",
        "log-token-123",
        "log-secret-123",
        "log-pass-123",
        "runtime-token-123",
    ):
        assert secret not in rendered
    assert REDACTED_VALUE in rendered


def test_structlog_redaction_processor_redacts_event_dict() -> None:
    redacted = redact_structlog_event(
        None,
        None,
        {
            "event": "uat_shadow_fixture",
            "authorization": "Bearer processor-token-123",
            "nested": {"password": "processor-pass-123"},
            "message": "api_key=processor-key-123",
        },
    )
    rendered = repr(redacted)

    for secret in ("processor-token-123", "processor-pass-123", "processor-key-123"):
        assert secret not in rendered
    assert REDACTED_VALUE in rendered


def test_uat1_universe_snapshot_is_available_for_uat2_and_observation_only() -> None:
    snapshot = load_uat1_universe_snapshot()

    assert snapshot.source_provider == "coingecko_public_markets"
    assert snapshot.observation_only is True
    assert "ETH" in snapshot.included_assets
    assert "BTC" in snapshot.included_assets
    assert "USDT" in snapshot.excluded_assets
    assert snapshot.exclusion_reasons_by_symbol["USDT"] == ("unsupported_by_venue",)

    readiness = evaluate_uat11_readiness(universe_snapshot=snapshot)
    assert readiness.shadow_signal_audit_surface_status == "implemented"
    assert readiness.shadow_drawdown_state_status == "implemented"
    assert readiness.redaction_verification_status.startswith("implemented")
    assert readiness.uat2_readiness_decision == "UAT2 shadow strategy run may proceed"
    assert readiness.remaining_blockers == ()


def test_uat11_report_records_boundaries_and_readiness_decision() -> None:
    snapshot = load_uat1_universe_snapshot()
    readiness = evaluate_uat11_readiness(universe_snapshot=snapshot)
    record = create_shadow_signal_audit_record(
        run_id="uat2-shadow-fixture",
        timestamp_utc=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        venue="hyperliquid",
        symbol="ETH",
        market_type="perpetual",
        product_type="perp",
        quote_asset="USDC",
        settlement_asset="USDC",
        component="sleeve_1h",
        timeframe="1h",
        candle_close_time_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
        signal_status=UATShadowSignalStatus.NO_TRADE,
        reason_codes=("uat1_1_fixture_no_strategy_run",),
        operator_visible_explanation="Fixture audit record only; no live strategy loop ran.",
    )
    drawdown = build_shadow_drawdown_state_from_equity_path(
        run_id="uat2-shadow-fixture",
        candidate_id="money_flow_hyperliquid_eth_1h_baseline_uat_candidate",
        universe_scope="top20_hyperliquid_observation_universe",
        observations=(
            UATDrawdownObservation(
                timestamp_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
                observed_equity=Decimal("10000"),
            ),
        ),
    )

    report = render_uat11_report(
        audit_record=record,
        drawdown_state=drawdown,
        universe_snapshot=snapshot,
        readiness=readiness,
    )

    assert "UAT1.1 Shadow Signal Audit And Drawdown Readiness" in report
    assert "next_candle_open" in report
    assert "next_candle_close" in report
    assert "same_candle_close_research_only" in report
    assert "Shadow audit no-live-artifact check: `true`" in report
    assert "not_live_account_drawdown" in report
    assert "UAT2 shadow strategy run may proceed" in report
    assert "does not run the UAT2 shadow strategy loop" in report
    assert "StrategyDecision" in report
    assert "OrderIntent" in report
    assert "SubmittedOrder" in report
    for phrase in ("proven profitable", "approved for paper trading", "ready for live trading"):
        assert phrase not in report.lower()


def test_committed_uat11_report_exists_after_generation_if_present() -> None:
    report_path = Path("docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md")
    if report_path.exists():
        report = report_path.read_text()
        assert "UAT1.1 prepares shadow audit and drawdown visibility" in report
        assert "Paper trading is not approved" in report
        assert "Live trading is not approved" in report
        assert "Exchange order submission is not approved" in report
        assert "UAT2 shadow strategy run may proceed" in report or "UAT2 is blocked" in report
