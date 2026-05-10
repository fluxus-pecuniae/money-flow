from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    PriorSandboxSubmitAttempt,
    SandboxAdapterEndpointClassification,
    SandboxApprovalCandidate,
    SandboxApprovalRejectReason,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxDrawdownFeedStatus,
    SandboxDryRunRejectReason,
    SandboxPrivateEndpointCategory,
    SandboxPrivateReadOnlyRejectReason,
    SandboxRiskLimits,
    SandboxRiskRejectReason,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    SandboxSubmitRejectReason,
    UAT3SandboxSubmitDryRunService,
    UAT3SandboxSubmitPathDryRunInput,
    evaluate_uat3_sandbox_submit_path_dry_run,
    build_sandbox_account_drawdown_feed,
    SandboxAccountStateSnapshot,
)


NOW = datetime(2026, 5, 10, 15, 40, tzinfo=UTC)


def _runtime_policy(**overrides: object) -> SandboxRuntimePolicy:
    values = {
        "runtime_mode": "uat_sandbox",
        "live_trading_enabled": False,
        "paper_trading_enabled": False,
        "exchange_order_submission_enabled": False,
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
        "uat_run_id": "uat3-0-6-run",
        "sandbox_order": True,
        "live_endpoint_access": False,
        "real_capital": False,
    }
    values.update(overrides)
    return SandboxArtifactLabels(**values)


def _approval_scope(**overrides: object) -> SandboxApprovalScope:
    values = {
        "approval_id": "uat306-approval-1",
        "uat_run_id": "uat3-0-6-run",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "max_notional_or_quantity": Decimal("25"),
        "expires_at_utc": NOW + timedelta(minutes=30),
        "environment": "testnet",
    }
    values.update(overrides)
    return SandboxApprovalScope(**values)


def _approval_candidate(**overrides: object) -> SandboxApprovalCandidate:
    values = {
        "uat_run_id": "uat3-0-6-run",
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
        "approval_id": "uat306-approval-1",
        "uat_run_id": "uat3-0-6-run",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "environment": "testnet",
    }
    values.update(overrides)
    return SandboxSubmitAttemptKey(**values)


def _drawdown_feed(**overrides: object):
    values = {
        "venue": "hyperliquid",
        "sandbox_account_id": "sandbox-account-1",
        "timestamp_utc": NOW,
        "sandbox_account_equity": Decimal("9900"),
        "sandbox_realized_pnl": None,
        "sandbox_unrealized_pnl": None,
        "open_positions_summary": (),
        "max_sandbox_equity": Decimal("10000"),
        "min_sandbox_equity": Decimal("9900"),
        "source": "sandbox_account",
        "not_live_account": True,
    }
    values.update(overrides)
    return build_sandbox_account_drawdown_feed(
        snapshot=SandboxAccountStateSnapshot(**values),
        drawdown_threshold=Decimal("0.05"),
        status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
    )


def _dry_run_input(**overrides: object) -> UAT3SandboxSubmitPathDryRunInput:
    values = {
        "runtime_policy": _runtime_policy(),
        "artifact_labels": _labels(),
        "approval_scope": _approval_scope(),
        "approval_candidate": _approval_candidate(),
        "risk_limits": _risk_limits(),
        "risk_request": _risk_request(),
        "submit_request": SandboxSubmitPreflightRequest(
            key=_submit_key(),
            submit_lease_acquired=True,
            idempotency_key="uat306-idem-1",
        ),
        "submit_state": SandboxSubmitPreflightState(),
        "now_utc": NOW,
        "sandbox_drawdown_feed": _drawdown_feed(),
        "endpoint_classification": SandboxAdapterEndpointClassification(
            endpoint_category=SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
            transport_invoked=False,
            calls_exchange=False,
        ),
    }
    values.update(overrides)
    return UAT3SandboxSubmitPathDryRunInput(**values)


def test_dry_run_submission_plan_creates_no_artifacts_or_exchange_calls() -> None:
    result = UAT3SandboxSubmitDryRunService().evaluate(
        _dry_run_input(founder_operator_actual_submission_approved=True)
    )

    assert result.allowed_for_future_submit is True
    assert result.blocked is False
    assert result.would_call_exchange is False
    assert result.would_create_order_intent is False
    assert result.would_create_prepared_order is False
    assert result.would_create_submitted_order is False
    assert result.would_create_executable_approval is False
    assert result.would_submit_if_enabled is False
    assert result.submission_plan.would_submit_if_enabled is False
    assert result.submission_plan.creates_order_intent is False
    assert result.submission_plan.creates_prepared_order is False
    assert result.submission_plan.creates_submitted_order is False
    assert result.submission_plan.creates_executable_approval is False
    assert result.submission_plan.calls_exchange is False
    assert result.submission_plan.endpoint_category == SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION
    assert result.submission_plan.endpoint_transport_invoked is False


def test_missing_actual_submission_approval_blocks_submit_path_dry_run() -> None:
    result = evaluate_uat3_sandbox_submit_path_dry_run(_dry_run_input())

    assert result.blocked is True
    assert (
        SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED
        in result.reason_codes
    )
    assert result.approval_requirement_result.blocked is True


def test_live_fed_sandbox_drawdown_missing_or_stale_blocks() -> None:
    missing = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            sandbox_drawdown_feed=None,
            drawdown_feed_status=SandboxDrawdownFeedStatus.MISSING.value,
        )
    )
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING in missing.reason_codes

    stale = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            sandbox_drawdown_feed=_drawdown_feed(timestamp_utc=NOW - timedelta(hours=1)),
        )
    )
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_STALE in stale.reason_codes


def test_drawdown_must_be_live_fed_and_not_live_account_labeled() -> None:
    fixture_only = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            drawdown_feed_status=SandboxDrawdownFeedStatus.FIXTURE_ONLY.value,
        )
    )
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY in fixture_only.reason_codes
    assert (
        SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_LIVE_FED_VERIFIED
        in fixture_only.reason_codes
    )

    live_labeled = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            sandbox_drawdown_feed=_drawdown_feed(not_live_account=False),
        )
    )
    assert (
        SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_LABELED_NOT_LIVE_ACCOUNT
        in live_labeled.reason_codes
    )
    assert (
        SandboxPrivateReadOnlyRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_ACCOUNT_FORBIDDEN
        in live_labeled.reason_codes
    )


def test_approval_scope_mismatch_blocks_submit_path_dry_run() -> None:
    result = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            approval_candidate=_approval_candidate(symbol="BTC"),
        )
    )

    assert SandboxApprovalRejectReason.WRONG_SYMBOL in result.reason_codes


def test_risk_gate_failure_blocks_submit_path_dry_run() -> None:
    result = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            risk_request=_risk_request(notional=Decimal("30"), kill_switch_enabled=True),
        )
    )

    assert SandboxRiskRejectReason.SANDBOX_NOTIONAL_LIMIT_EXCEEDED in result.reason_codes
    assert SandboxRiskRejectReason.KILL_SWITCH_ENABLED in result.reason_codes


def test_submit_lease_duplicate_cross_venue_fanout_and_route_executor_block() -> None:
    key = _submit_key()
    duplicate = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            submit_state=SandboxSubmitPreflightState(
                prior_attempts=(
                    PriorSandboxSubmitAttempt(key=key, status="adapter_submit_may_have_started"),
                )
            ),
        )
    )
    assert SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE in duplicate.reason_codes
    assert SandboxSubmitRejectReason.PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY in duplicate.reason_codes

    cross_venue_prior = _submit_key(venue="okx")
    cross_venue = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            submit_state=SandboxSubmitPreflightState(
                prior_attempts=(PriorSandboxSubmitAttempt(key=cross_venue_prior, status="blocked"),)
            ),
            submit_request=SandboxSubmitPreflightRequest(
                key=key,
                submit_lease_acquired=True,
                idempotency_key="uat306-idem-1",
                top20_fanout=True,
                route_executor_behavior=True,
            ),
        )
    )
    assert SandboxSubmitRejectReason.CROSS_VENUE_RETRY_FORBIDDEN in cross_venue.reason_codes
    assert SandboxSubmitRejectReason.TOP20_FANOUT_FORBIDDEN in cross_venue.reason_codes
    assert SandboxSubmitRejectReason.ROUTE_EXECUTOR_FORBIDDEN in cross_venue.reason_codes


def test_endpoint_classification_unknown_blocks_and_order_transport_not_invoked() -> None:
    unknown = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            endpoint_classification=SandboxAdapterEndpointClassification(
                endpoint_category=SandboxPrivateEndpointCategory.UNKNOWN,
            ),
        )
    )
    assert SandboxDryRunRejectReason.ENDPOINT_CATEGORY_UNKNOWN in unknown.reason_codes
    assert (
        SandboxDryRunRejectReason.ENDPOINT_CATEGORY_NOT_SANDBOX_ORDER_SUBMISSION
        in unknown.reason_codes
    )

    invoked = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            endpoint_classification=SandboxAdapterEndpointClassification(
                endpoint_category=SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
                transport_invoked=True,
                calls_exchange=True,
            ),
        )
    )
    assert (
        SandboxDryRunRejectReason.SANDBOX_ORDER_ENDPOINT_TRANSPORT_FORBIDDEN_IN_UAT306
        in invoked.reason_codes
    )
    assert invoked.would_call_exchange is False


def test_missing_artifact_labels_block_before_future_boundaries() -> None:
    result = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            artifact_labels=_labels(sandbox=False, uat_run_id="", real_capital=True),
        )
    )

    assert "sandbox_label_missing_or_false" in result.reason_codes
    assert "uat_run_id_missing" in result.reason_codes
    assert "real_capital_label_not_false" in result.reason_codes


def test_runtime_policy_keeps_global_order_submission_separate_from_sandbox_submission() -> None:
    result = evaluate_uat3_sandbox_submit_path_dry_run(
        _dry_run_input(
            founder_operator_actual_submission_approved=True,
            runtime_policy=_runtime_policy(exchange_order_submission_enabled=True),
            risk_request=_risk_request(
                runtime_policy=_runtime_policy(exchange_order_submission_enabled=True)
            ),
        )
    )

    assert "exchange_order_submission_enabled" in result.reason_codes
    assert "runtime_policy_exchange_order_submission_enabled" in result.reason_codes
    assert result.submission_plan.runtime_policy_snapshot.sandbox_order_submission_enabled is True
    assert result.submission_plan.runtime_policy_snapshot.exchange_order_submission_enabled is True


def test_uat306_report_records_dry_run_wiring_and_blocked_decision() -> None:
    report = Path("docs/uat3_0_6_sandbox_submit_path_dry_run_wiring.md")

    assert report.exists()
    text = report.read_text()
    assert "UAT3.0.6 Sandbox Submit Path Dry-Run Wiring" in text
    assert "Dry-Run Submission Plan" in text
    assert "Executable Gate Chain" in text
    assert "Founder Actual-Submission Approval Requirement" in text
    assert "Live-Fed Sandbox Drawdown Status" in text
    assert "Endpoint Classification" in text
    assert "`UAT3.1 is blocked`" in text
    assert "Actual sandbox order submission is not approved" in text
    assert "OrderIntent rows created | `false`" in text
    assert "PreparedVenueOrder rows created | `false`" in text
    assert "SubmittedOrder rows created | `false`" in text
    assert "Executable approvals created | `false`" in text
