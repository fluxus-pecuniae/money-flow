from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    PriorSandboxSubmitAttempt,
    SandboxApprovalCandidate,
    SandboxApprovalRejectReason,
    SandboxApprovalScope,
    SandboxArtifactBoundary,
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
    UAT3SandboxDryRunGateService,
    UAT3SandboxExecutableGateDryRunInput,
    build_sandbox_drawdown_feed_fixture,
    evaluate_uat3_sandbox_executable_gate_dry_run,
    get_sandbox_runtime_policy_semantics,
    validate_sandbox_artifact_boundary,
)


def _runtime_policy(**overrides: object) -> SandboxRuntimePolicy:
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


def _labels(**overrides: object) -> SandboxArtifactLabels:
    values = {
        "sandbox": True,
        "testnet": True,
        "not_live": True,
        "not_paper": True,
        "uat_run_id": "uat3-run-1",
        "sandbox_order": True,
        "live_endpoint_access": False,
        "real_capital": False,
    }
    values.update(overrides)
    return SandboxArtifactLabels(**values)


def _scope(**overrides: object) -> SandboxApprovalScope:
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


def _candidate(**overrides: object) -> SandboxApprovalCandidate:
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
        "runtime_policy": _runtime_policy(),
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


def _drawdown_fixture():
    return build_sandbox_drawdown_feed_fixture(
        sandbox_account_equity=Decimal("9900"),
        max_sandbox_equity=Decimal("10000"),
        drawdown_threshold=Decimal("0.05"),
        timestamp_utc=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        venue_account_id="sandbox-account-1",
    )


def _dry_run_input(**overrides: object) -> UAT3SandboxExecutableGateDryRunInput:
    values = {
        "runtime_policy": _runtime_policy(),
        "artifact_labels": _labels(),
        "approval_scope": _scope(),
        "approval_candidate": _candidate(),
        "risk_limits": _risk_limits(),
        "risk_request": _risk_request(),
        "submit_request": SandboxSubmitPreflightRequest(
            key=_submit_key(),
            submit_lease_acquired=True,
            idempotency_key="idem-1",
        ),
        "submit_state": SandboxSubmitPreflightState(),
        "now_utc": datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        "sandbox_drawdown_feed": _drawdown_fixture(),
    }
    values.update(overrides)
    return UAT3SandboxExecutableGateDryRunInput(**values)


def test_sandbox_artifact_boundary_validator_rejects_missing_labels() -> None:
    invalid_labels = _labels(sandbox=False, testnet=False, uat_run_id="", live_endpoint_access=True)

    result = validate_sandbox_artifact_boundary(
        labels=invalid_labels,
        boundary=SandboxArtifactBoundary.PERSISTENCE,
    )

    assert result.boundary == SandboxArtifactBoundary.PERSISTENCE
    assert result.result.blocked is True
    assert SandboxReadinessReason.SANDBOX_LABEL_MISSING_OR_FALSE in result.result.reason_codes
    assert SandboxReadinessReason.TESTNET_LABEL_MISSING_OR_FALSE in result.result.reason_codes
    assert SandboxReadinessReason.UAT_RUN_ID_MISSING in result.result.reason_codes
    assert SandboxReadinessReason.LIVE_ENDPOINT_LABEL_NOT_FALSE in result.result.reason_codes
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False


def test_api_dashboard_and_report_boundaries_reject_missing_sandbox_labels() -> None:
    for boundary in (
        SandboxArtifactBoundary.API_SERIALIZATION,
        SandboxArtifactBoundary.DASHBOARD_DISPLAY,
        SandboxArtifactBoundary.REPORT_GENERATION,
    ):
        result = validate_sandbox_artifact_boundary(
            labels=_labels(not_live=False, sandbox_order=False, real_capital=True),
            boundary=boundary,
        )
        assert result.result.blocked is True
        assert SandboxReadinessReason.NOT_LIVE_LABEL_MISSING_OR_FALSE in result.result.reason_codes
        assert SandboxReadinessReason.SANDBOX_ORDER_LABEL_MISSING_OR_FALSE in result.result.reason_codes
        assert SandboxReadinessReason.REAL_CAPITAL_LABEL_NOT_FALSE in result.result.reason_codes


def test_dry_run_gate_service_reports_no_artifact_or_exchange_side_effects() -> None:
    result = UAT3SandboxDryRunGateService().evaluate(_dry_run_input())

    assert result.blocked is True
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False
    assert result.would_require_founder_approval is True
    assert result.would_require_live_fed_sandbox_drawdown is True
    assert result.would_require_real_sandbox_submit_path is True
    assert SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED in result.reason_codes
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY in result.reason_codes
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED in result.reason_codes
    assert SandboxDryRunRejectReason.REAL_SANDBOX_SUBMIT_PATH_REQUIRED in result.reason_codes


def test_dry_run_gate_service_blocks_approval_scope_mismatch() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(approval_candidate=_candidate(symbol="BTC"))
    )

    assert result.blocked is True
    assert SandboxApprovalRejectReason.WRONG_SYMBOL in result.reason_codes


def test_dry_run_gate_service_blocks_consumed_or_expired_approval() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(
            approval_scope=_scope(
                consumed=True,
                expires_at_utc=datetime(2026, 5, 10, 11, 59, tzinfo=UTC),
            )
        )
    )

    assert SandboxApprovalRejectReason.APPROVAL_ALREADY_CONSUMED in result.reason_codes
    assert SandboxApprovalRejectReason.EXPIRED_APPROVAL in result.reason_codes


def test_dry_run_gate_service_blocks_risk_gate_failure() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(risk_request=_risk_request(notional=Decimal("30"), kill_switch_enabled=True))
    )

    assert SandboxRiskRejectReason.SANDBOX_NOTIONAL_LIMIT_EXCEEDED in result.reason_codes
    assert SandboxRiskRejectReason.KILL_SWITCH_ENABLED in result.reason_codes


def test_dry_run_gate_service_blocks_submit_lease_duplicate_and_uncertainty() -> None:
    key = _submit_key()
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(
            submit_request=SandboxSubmitPreflightRequest(
                key=key,
                submit_lease_acquired=True,
                idempotency_key="idem-1",
            ),
            submit_state=SandboxSubmitPreflightState(
                prior_attempts=(
                    PriorSandboxSubmitAttempt(key=key, status="adapter_submit_may_have_started"),
                )
            ),
        )
    )

    assert SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE in result.reason_codes
    assert SandboxSubmitRejectReason.PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY in result.reason_codes


def test_dry_run_gate_service_blocks_missing_submit_lease_and_route_executor_behavior() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(
            submit_request=SandboxSubmitPreflightRequest(
                key=_submit_key(environment="live"),
                submit_lease_acquired=False,
                idempotency_key="",
                top20_fanout=True,
                route_executor_behavior=True,
            )
        )
    )

    assert SandboxSubmitRejectReason.SUBMIT_LEASE_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.IDEMPOTENCY_KEY_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.ENVIRONMENT_NOT_SANDBOX in result.reason_codes
    assert SandboxSubmitRejectReason.TOP20_FANOUT_FORBIDDEN in result.reason_codes
    assert SandboxSubmitRejectReason.ROUTE_EXECUTOR_FORBIDDEN in result.reason_codes


def test_runtime_policy_semantics_keep_sandbox_submission_separate_from_global_order_submission() -> None:
    semantics = get_sandbox_runtime_policy_semantics()

    assert "broad/global/non-sandbox" in semantics.exchange_order_submission_enabled
    assert "sandbox/testnet-only" in semantics.sandbox_order_submission_enabled
    assert "live endpoint access must remain false" in semantics.live_endpoint_access

    allowed_sandbox_only = _runtime_policy().evaluate_for_sandbox_submission()
    global_order_submission = _runtime_policy(exchange_order_submission_enabled=True).evaluate_for_sandbox_submission()

    assert allowed_sandbox_only.allowed is True
    assert SandboxReadinessReason.EXCHANGE_ORDER_SUBMISSION_ENABLED in global_order_submission.reason_codes


def test_dry_run_gate_service_can_pass_only_when_all_future_gates_are_explicitly_ready() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            drawdown_feed_status="sandbox_drawdown_feed_live_fed_verified",
            real_sandbox_submit_path_wired=True,
        )
    )

    assert result.allowed is True
    assert result.reason_codes == ()
    assert len(result.artifact_boundary_results) == 4
    assert all(boundary.result.allowed for boundary in result.artifact_boundary_results)
    assert result.would_require_founder_approval is False
    assert result.would_require_live_fed_sandbox_drawdown is False
    assert result.would_require_real_sandbox_submit_path is False


def test_dry_run_gate_service_marks_missing_boundary_enforcement_not_ready() -> None:
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            drawdown_feed_status="sandbox_drawdown_feed_live_fed_verified",
            artifact_boundary_enforcement=(SandboxArtifactBoundary.PERSISTENCE,),
            real_sandbox_submit_path_wired=True,
        )
    )

    assert result.blocked is True
    assert SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_API_SERIALIZATION in (
        result.reason_codes
    )
    assert SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_DASHBOARD_DISPLAY in (
        result.reason_codes
    )
    assert SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_REPORT_GENERATION in (
        result.reason_codes
    )


def test_uat303_report_records_label_enforcement_and_blocked_decision() -> None:
    report = Path("docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md")

    assert report.exists()
    text = report.read_text()
    assert "UAT3.0.3 Sandbox Gate Wiring And Label Enforcement" in text
    assert "Sandbox Artifact Label Boundary Enforcement" in text
    assert "Dry-Run Executable Gate Service" in text
    assert "Runtime Policy Semantics" in text
    assert "Approval-Scope Dry-Run Wiring" in text
    assert "Risk-Gate Dry-Run Wiring" in text
    assert "Submit-Lease Dry-Run Wiring" in text
    assert "`UAT3.1 is blocked`" in text
    assert "Actual sandbox order submission is not approved" in text
    assert "OrderIntent rows created | `false`" in text
    assert "PreparedVenueOrder rows created | `false`" in text
    assert "SubmittedOrder rows created | `false`" in text
    assert "Executable approvals created | `false`" in text
