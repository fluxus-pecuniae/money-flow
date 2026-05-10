from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.uat.sandbox import (
    RUNTIME_POLICY_RISK_REASON_PREFIX,
    PriorSandboxSubmitAttempt,
    SandboxApprovalCandidate,
    SandboxApprovalRejectReason,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxDryRunRejectReason,
    SandboxReadinessReason,
    SandboxRiskLimits,
    SandboxRiskRejectReason,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    SandboxSubmitRejectReason,
    UAT3SandboxGateDryRunInput,
    build_sandbox_drawdown_feed_fixture,
    evaluate_sandbox_risk_gates,
    evaluate_sandbox_submit_preflight,
    evaluate_uat3_sandbox_submission_preflight,
    validate_sandbox_approval_scope,
)


def _future_sandbox_runtime_policy(**overrides: object) -> SandboxRuntimePolicy:
    values = {
        "runtime_mode": "uat_sandbox",
        "sandbox_order_submission_enabled": True,
        "private_exchange_endpoints_enabled": True,
        "live_endpoint_access": False,
        "api_keys_required": True,
        "sandbox_only": True,
    }
    values.update(overrides)
    return SandboxRuntimePolicy(**values)


def _approval_scope(**overrides: object) -> SandboxApprovalScope:
    values = {
        "approval_id": "approval-1",
        "uat_run_id": "uat3-run-1",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "max_notional_or_quantity": Decimal("25"),
        "expires_at_utc": datetime(2026, 5, 10, 13, 0, tzinfo=UTC),
        "environment": "testnet",
    }
    values.update(overrides)
    return SandboxApprovalScope(**values)


def _approval_candidate(**overrides: object) -> SandboxApprovalCandidate:
    values = {
        "uat_run_id": "uat3-run-1",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "requested_notional_or_quantity": Decimal("10"),
        "environment": "testnet",
    }
    values.update(overrides)
    return SandboxApprovalCandidate(**values)


def _risk_limits(**overrides: object) -> SandboxRiskLimits:
    values = {
        "max_sandbox_notional": Decimal("25"),
        "max_sandbox_order_count": 1,
        "max_daily_sandbox_order_count": 1,
        "max_sandbox_drawdown_pct": Decimal("0.05"),
        "allowed_symbols": ("ETH",),
        "allowed_venue_accounts": ("sandbox-account-1",),
        "allowed_venues": ("hyperliquid",),
    }
    values.update(overrides)
    return SandboxRiskLimits(**values)


def _risk_request(**overrides: object) -> SandboxRiskRequest:
    values = {
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "notional": Decimal("10"),
        "current_order_count": 0,
        "current_daily_order_count": 0,
        "sandbox_drawdown_pct": Decimal("0.01"),
        "live_account": False,
        "live_endpoint_access": False,
        "kill_switch_enabled": False,
        "runtime_policy": _future_sandbox_runtime_policy(),
    }
    values.update(overrides)
    return SandboxRiskRequest(**values)


def _submit_key(**overrides: object) -> SandboxSubmitAttemptKey:
    values = {
        "approval_id": "approval-1",
        "uat_run_id": "uat3-run-1",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "environment": "testnet",
    }
    values.update(overrides)
    return SandboxSubmitAttemptKey(**values)


def _artifact_labels() -> SandboxArtifactLabels:
    return SandboxArtifactLabels(
        sandbox=True,
        testnet=True,
        not_live=True,
        not_paper=True,
        uat_run_id="uat3-run-1",
        sandbox_order=True,
        live_endpoint_access=False,
        real_capital=False,
    )


def _drawdown_fixture():
    return build_sandbox_drawdown_feed_fixture(
        sandbox_account_equity=Decimal("9900"),
        max_sandbox_equity=Decimal("10000"),
        drawdown_threshold=Decimal("0.05"),
        timestamp_utc=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        venue_account_id="sandbox-account-1",
    )


def _dry_run_input(**overrides: object) -> UAT3SandboxGateDryRunInput:
    submit_request = SandboxSubmitPreflightRequest(
        key=_submit_key(),
        submit_lease_acquired=True,
        idempotency_key="idem-1",
    )
    values = {
        "runtime_policy": _future_sandbox_runtime_policy(),
        "artifact_labels": _artifact_labels(),
        "approval_scope": _approval_scope(),
        "approval_candidate": _approval_candidate(),
        "risk_limits": _risk_limits(),
        "risk_request": _risk_request(),
        "submit_request": submit_request,
        "submit_state": SandboxSubmitPreflightState(),
        "now_utc": datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        "sandbox_drawdown_feed": _drawdown_fixture(),
    }
    values.update(overrides)
    return UAT3SandboxGateDryRunInput(**values)


def test_risk_gate_propagates_all_runtime_policy_blockers() -> None:
    unsafe_policy = SandboxRuntimePolicy(
        runtime_mode="uat",
        sandbox_order_submission_enabled=False,
        live_trading_enabled=True,
        paper_trading_enabled=True,
        exchange_order_submission_enabled=True,
        private_exchange_endpoints_enabled=False,
        live_endpoint_access=True,
        api_keys_required=False,
        sandbox_only=False,
    )

    result = evaluate_sandbox_risk_gates(
        limits=_risk_limits(),
        request=_risk_request(runtime_policy=unsafe_policy),
    )

    expected_runtime_reasons = (
        SandboxReadinessReason.RUNTIME_MODE_NOT_SANDBOX,
        SandboxReadinessReason.SANDBOX_SUBMISSION_DISABLED,
        SandboxReadinessReason.LIVE_TRADING_ENABLED,
        SandboxReadinessReason.PAPER_TRADING_ENABLED,
        SandboxReadinessReason.EXCHANGE_ORDER_SUBMISSION_ENABLED,
        SandboxReadinessReason.PRIVATE_ENDPOINTS_DISABLED,
        SandboxReadinessReason.PRIVATE_ENDPOINTS_NOT_SANDBOX_ONLY,
        SandboxReadinessReason.LIVE_ENDPOINT_FORBIDDEN,
        SandboxReadinessReason.SANDBOX_API_KEYS_NOT_CONFIGURED,
    )
    for reason in expected_runtime_reasons:
        assert f"{RUNTIME_POLICY_RISK_REASON_PREFIX}{reason.value}" in result.reason_codes

    assert SandboxRiskRejectReason.RUNTIME_MODE_NOT_SANDBOX in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_SUBMISSION_DISABLED in result.reason_codes


def test_approval_scope_rejects_non_positive_max_and_requested_quantity() -> None:
    result = validate_sandbox_approval_scope(
        scope=_approval_scope(max_notional_or_quantity=Decimal("0")),
        candidate=_approval_candidate(requested_notional_or_quantity=Decimal("-1")),
        now_utc=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
    )

    assert result.blocked is True
    assert SandboxApprovalRejectReason.SANDBOX_POSITIVE_QUANTITY_REQUIRED in result.reason_codes


def test_risk_gate_rejects_non_positive_limits_and_request_values() -> None:
    result = evaluate_sandbox_risk_gates(
        limits=_risk_limits(
            max_sandbox_notional=Decimal("0"),
            max_sandbox_order_count=0,
            max_daily_sandbox_order_count=0,
            max_sandbox_drawdown_pct=Decimal("-0.01"),
        ),
        request=_risk_request(notional=Decimal("0"), sandbox_drawdown_pct=Decimal("-0.01")),
    )

    assert SandboxRiskRejectReason.SANDBOX_POSITIVE_LIMIT_REQUIRED in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_POSITIVE_NOTIONAL_REQUIRED in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_INVALID in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_DRAWDOWN_PERCENT_INVALID in result.reason_codes


def test_drawdown_fixture_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError, match=SandboxRiskRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_INVALID.value):
        build_sandbox_drawdown_feed_fixture(
            sandbox_account_equity=Decimal("9900"),
            max_sandbox_equity=Decimal("10000"),
            drawdown_threshold=Decimal("-0.01"),
            timestamp_utc=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
            venue_account_id="sandbox-account-1",
        )


def test_unified_dry_run_preflight_blocks_without_actual_approval_and_live_fed_drawdown() -> None:
    result = evaluate_uat3_sandbox_submission_preflight(_dry_run_input())

    assert result.blocked is True
    assert SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED in (
        result.overall_reason_codes
    )
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY in result.overall_reason_codes
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED in result.overall_reason_codes
    assert SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_PERSISTENCE in (
        result.overall_reason_codes
    )
    assert result.runtime_policy_result.allowed is True
    assert result.artifact_label_result.allowed is True
    assert result.approval_scope_result.allowed is True
    assert result.risk_gate_result.allowed is True
    assert result.submit_preflight_result.allowed is True
    assert result.would_submit_if_enabled is False
    assert result.creates_order_intent is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False


def test_unified_dry_run_preflight_can_pass_only_when_all_fixture_gates_are_explicitly_clear() -> None:
    result = evaluate_uat3_sandbox_submission_preflight(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            drawdown_feed_status="sandbox_drawdown_feed_live_fed_verified",
            artifact_labels_persistence_enforced=True,
        )
    )

    assert result.allowed is True
    assert result.overall_reason_codes == ()
    assert result.would_submit_if_enabled is True
    assert result.creates_order_intent is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False


def test_duplicate_and_uncertainty_submit_fixtures_still_block_retry() -> None:
    key = _submit_key()
    result = evaluate_sandbox_submit_preflight(
        request=SandboxSubmitPreflightRequest(
            key=key,
            submit_lease_acquired=True,
            idempotency_key="idem-1",
        ),
        state=SandboxSubmitPreflightState(
            prior_attempts=(
                PriorSandboxSubmitAttempt(key=key, status="adapter_submit_persistence_unknown"),
            )
        ),
    )

    assert SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE in result.reason_codes
    assert SandboxSubmitRejectReason.PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY in result.reason_codes


def test_uat302_report_records_dry_run_boundaries() -> None:
    report = Path("docs/uat3_0_2_sandbox_gate_integration_dry_run.md")

    assert report.exists()
    text = report.read_text()
    assert "UAT3.0.2 Sandbox Gate Integration Dry-Run" in text
    assert "runtime policy blocker propagation" in text
    assert "unified dry-run sandbox gate preflight" in text
    assert "`UAT3.1 is blocked`" in text
    assert "Actual sandbox order submission is not approved" in text
    assert "OrderIntent rows created | `false`" in text
    assert "SubmittedOrder rows created | `false`" in text
    assert "Executable approvals created | `false`" in text
    assert "Private/signed/order endpoint calls made | `false`" in text
