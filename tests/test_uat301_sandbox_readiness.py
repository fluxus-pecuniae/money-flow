from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    PriorSandboxSubmitAttempt,
    SandboxApprovalCandidate,
    SandboxApprovalRejectReason,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxReadinessReason,
    SandboxRiskLimits,
    SandboxRiskRejectReason,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    SandboxSubmitRejectReason,
    build_sandbox_drawdown_feed_fixture,
    evaluate_sandbox_risk_gates,
    evaluate_sandbox_submit_preflight,
    validate_sandbox_approval_scope,
    validate_sandbox_artifact_labels,
)


def _future_sandbox_runtime_policy() -> SandboxRuntimePolicy:
    return SandboxRuntimePolicy(
        runtime_mode="uat_sandbox",
        sandbox_order_submission_enabled=True,
        private_exchange_endpoints_enabled=True,
        live_endpoint_access=False,
        api_keys_required=True,
        sandbox_only=True,
    )


def _approval_scope(**overrides: object) -> SandboxApprovalScope:
    values = {
        "approval_id": "approval-1",
        "uat_run_id": "uat3-run-1",
        "venue": "hyperliquid",
        "account_id": "sandbox-account-1",
        "symbol": "ETH",
        "component": "sleeve_1h",
        "max_notional_or_quantity": Decimal("25"),
        "expires_at_utc": datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
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


def test_sandbox_runtime_policy_defaults_fail_closed() -> None:
    policy = SandboxRuntimePolicy()
    result = policy.evaluate_for_sandbox_submission()

    assert result.blocked is True
    assert policy.live_trading_enabled is False
    assert policy.paper_trading_enabled is False
    assert policy.exchange_order_submission_enabled is False
    assert policy.sandbox_order_submission_enabled is False
    assert policy.private_exchange_endpoints_enabled is False
    assert policy.live_endpoint_access is False
    assert policy.sandbox_only is True
    assert SandboxReadinessReason.RUNTIME_MODE_NOT_SANDBOX in result.reason_codes
    assert SandboxReadinessReason.SANDBOX_SUBMISSION_DISABLED in result.reason_codes
    assert SandboxReadinessReason.PRIVATE_ENDPOINTS_DISABLED in result.reason_codes
    assert SandboxReadinessReason.SANDBOX_API_KEYS_NOT_CONFIGURED in result.reason_codes


def test_future_sandbox_runtime_policy_requires_explicit_sandbox_enablement() -> None:
    result = _future_sandbox_runtime_policy().evaluate_for_sandbox_submission()

    assert result.allowed is True
    assert result.reason_codes == ()


def test_sandbox_artifact_labels_are_required_and_missing_labels_fail() -> None:
    valid = validate_sandbox_artifact_labels(
        SandboxArtifactLabels(
            sandbox=True,
            testnet=True,
            not_live=True,
            not_paper=True,
            uat_run_id="uat3-run-1",
            sandbox_order=True,
            live_endpoint_access=False,
            real_capital=False,
        )
    )
    invalid = validate_sandbox_artifact_labels(
        SandboxArtifactLabels(
            sandbox=False,
            testnet=True,
            not_live=False,
            not_paper=True,
            uat_run_id="",
            sandbox_order=False,
            live_endpoint_access=True,
            real_capital=True,
        )
    )

    assert valid.allowed is True
    assert invalid.blocked is True
    assert SandboxReadinessReason.SANDBOX_LABEL_MISSING_OR_FALSE in invalid.reason_codes
    assert SandboxReadinessReason.NOT_LIVE_LABEL_MISSING_OR_FALSE in invalid.reason_codes
    assert SandboxReadinessReason.UAT_RUN_ID_MISSING in invalid.reason_codes
    assert SandboxReadinessReason.SANDBOX_ORDER_LABEL_MISSING_OR_FALSE in invalid.reason_codes
    assert SandboxReadinessReason.LIVE_ENDPOINT_LABEL_NOT_FALSE in invalid.reason_codes
    assert SandboxReadinessReason.REAL_CAPITAL_LABEL_NOT_FALSE in invalid.reason_codes


def test_approval_scope_validator_accepts_only_exact_sandbox_scope() -> None:
    result = validate_sandbox_approval_scope(
        scope=_approval_scope(),
        candidate=_approval_candidate(),
        now_utc=datetime(2026, 5, 10, 11, 0, tzinfo=UTC),
    )

    assert result.allowed is True
    assert result.reason_codes == ()


def test_approval_scope_validator_rejects_wrong_symbol_expired_live_broad_and_missing_run() -> None:
    now = datetime(2026, 5, 10, 11, 0, tzinfo=UTC)

    wrong_symbol = validate_sandbox_approval_scope(
        scope=_approval_scope(),
        candidate=_approval_candidate(symbol="BTC"),
        now_utc=now,
    )
    expired = validate_sandbox_approval_scope(
        scope=_approval_scope(expires_at_utc=now - timedelta(seconds=1)),
        candidate=_approval_candidate(),
        now_utc=now,
    )
    live_environment = validate_sandbox_approval_scope(
        scope=_approval_scope(environment="live", not_live=False),
        candidate=_approval_candidate(environment="live"),
        now_utc=now,
    )
    broad_top20 = validate_sandbox_approval_scope(
        scope=_approval_scope(broad_top20_submission=True),
        candidate=_approval_candidate(broad_top20_submission=True),
        now_utc=now,
    )
    missing_run = validate_sandbox_approval_scope(
        scope=_approval_scope(uat_run_id=""),
        candidate=_approval_candidate(uat_run_id=""),
        now_utc=now,
    )

    assert SandboxApprovalRejectReason.WRONG_SYMBOL in wrong_symbol.reason_codes
    assert SandboxApprovalRejectReason.EXPIRED_APPROVAL in expired.reason_codes
    assert SandboxApprovalRejectReason.MISSING_SANDBOX_ENVIRONMENT in live_environment.reason_codes
    assert SandboxApprovalRejectReason.LIVE_ENVIRONMENT_FORBIDDEN in live_environment.reason_codes
    assert SandboxApprovalRejectReason.BROAD_TOP20_APPROVAL_FORBIDDEN in broad_top20.reason_codes
    assert SandboxApprovalRejectReason.UAT_RUN_ID_MISSING in missing_run.reason_codes


def test_approval_scope_validator_rejects_wrong_venue_account_quantity_and_consumed_scope() -> None:
    now = datetime(2026, 5, 10, 11, 0, tzinfo=UTC)
    result = validate_sandbox_approval_scope(
        scope=_approval_scope(consumed=True),
        candidate=_approval_candidate(
            venue="aster",
            account_id="other-account",
            requested_notional_or_quantity=Decimal("100"),
        ),
        now_utc=now,
    )

    assert SandboxApprovalRejectReason.WRONG_VENUE in result.reason_codes
    assert SandboxApprovalRejectReason.WRONG_ACCOUNT in result.reason_codes
    assert SandboxApprovalRejectReason.QUANTITY_ABOVE_MAX in result.reason_codes
    assert SandboxApprovalRejectReason.APPROVAL_ALREADY_CONSUMED in result.reason_codes


def test_sandbox_risk_gate_blocks_notional_drawdown_live_account_and_live_endpoint() -> None:
    limits = SandboxRiskLimits(
        max_sandbox_notional=Decimal("25"),
        max_sandbox_order_count=1,
        max_daily_sandbox_order_count=2,
        max_sandbox_drawdown_pct=Decimal("0.05"),
        allowed_symbols=("ETH",),
        allowed_venue_accounts=("sandbox-account-1",),
        allowed_venues=("hyperliquid",),
    )
    result = evaluate_sandbox_risk_gates(
        limits=limits,
        request=SandboxRiskRequest(
            venue="hyperliquid",
            account_id="sandbox-account-1",
            symbol="ETH",
            notional=Decimal("30"),
            current_order_count=0,
            current_daily_order_count=0,
            sandbox_drawdown_pct=Decimal("0.07"),
            live_account=True,
            live_endpoint_access=True,
            kill_switch_enabled=False,
            runtime_policy=_future_sandbox_runtime_policy(),
        ),
    )

    assert result.blocked is True
    assert SandboxRiskRejectReason.SANDBOX_NOTIONAL_LIMIT_EXCEEDED in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_DRAWDOWN_LIMIT_BREACHED in result.reason_codes
    assert SandboxRiskRejectReason.LIVE_ACCOUNT_FORBIDDEN in result.reason_codes
    assert SandboxRiskRejectReason.LIVE_ENDPOINT_FORBIDDEN in result.reason_codes


def test_sandbox_risk_gate_blocks_counts_symbol_account_kill_switch_and_disabled_runtime() -> None:
    limits = SandboxRiskLimits(
        max_sandbox_notional=Decimal("25"),
        max_sandbox_order_count=1,
        max_daily_sandbox_order_count=1,
        max_sandbox_drawdown_pct=Decimal("0.05"),
        allowed_symbols=("ETH",),
        allowed_venue_accounts=("sandbox-account-1",),
        allowed_venues=("hyperliquid",),
    )
    result = evaluate_sandbox_risk_gates(
        limits=limits,
        request=SandboxRiskRequest(
            venue="hyperliquid",
            account_id="other-account",
            symbol="BTC",
            notional=Decimal("10"),
            current_order_count=1,
            current_daily_order_count=1,
            sandbox_drawdown_pct=Decimal("0.01"),
            live_account=False,
            live_endpoint_access=False,
            kill_switch_enabled=True,
            runtime_policy=SandboxRuntimePolicy(),
        ),
    )

    assert SandboxRiskRejectReason.SANDBOX_ORDER_COUNT_EXCEEDED in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_DAILY_ORDER_COUNT_EXCEEDED in result.reason_codes
    assert SandboxRiskRejectReason.SYMBOL_NOT_ALLOWED_FOR_SANDBOX in result.reason_codes
    assert SandboxRiskRejectReason.VENUE_ACCOUNT_NOT_ALLOWED_FOR_SANDBOX in result.reason_codes
    assert SandboxRiskRejectReason.KILL_SWITCH_ENABLED in result.reason_codes
    assert SandboxRiskRejectReason.RUNTIME_MODE_NOT_SANDBOX in result.reason_codes
    assert SandboxRiskRejectReason.SANDBOX_SUBMISSION_DISABLED in result.reason_codes


def test_sandbox_drawdown_feed_fixture_is_not_live_account_and_computes_threshold() -> None:
    fixture = build_sandbox_drawdown_feed_fixture(
        sandbox_account_equity=Decimal("9400"),
        max_sandbox_equity=Decimal("10000"),
        drawdown_threshold=Decimal("0.05"),
        timestamp_utc=datetime(2026, 5, 10, 11, 30, tzinfo=UTC),
        venue_account_id="sandbox-account-1",
        sandbox_realized_pnl=Decimal("-100"),
        sandbox_unrealized_pnl=Decimal("-500"),
    )

    assert fixture.source == "sandbox_account"
    assert fixture.not_live_account is True
    assert fixture.max_drawdown_amount == Decimal("600")
    assert fixture.max_drawdown_percent == Decimal("0.06")
    assert fixture.threshold_breached is True
    assert "sandbox_account_drawdown_fixture_not_live_account" in fixture.reason_codes
    assert "sandbox_drawdown_threshold_breached" in fixture.reason_codes


def test_submit_duplicate_prevention_fixture_blocks_duplicate_uncertain_cross_venue_fanout_and_route_executor() -> None:
    prior_key = _submit_key()
    result = evaluate_sandbox_submit_preflight(
        request=SandboxSubmitPreflightRequest(
            key=_submit_key(venue="aster"),
            submit_lease_acquired=True,
            idempotency_key="idem-1",
            top20_fanout=True,
            route_executor_behavior=True,
        ),
        state=SandboxSubmitPreflightState(
            prior_attempts=(
                PriorSandboxSubmitAttempt(key=prior_key, status="adapter_submit_may_have_started"),
            )
        ),
    )

    assert result.blocked is True
    assert SandboxSubmitRejectReason.PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY in result.reason_codes
    assert SandboxSubmitRejectReason.CROSS_VENUE_RETRY_FORBIDDEN in result.reason_codes
    assert SandboxSubmitRejectReason.TOP20_FANOUT_FORBIDDEN in result.reason_codes
    assert SandboxSubmitRejectReason.ROUTE_EXECUTOR_FORBIDDEN in result.reason_codes

    duplicate = evaluate_sandbox_submit_preflight(
        request=SandboxSubmitPreflightRequest(
            key=prior_key,
            submit_lease_acquired=True,
            idempotency_key="idem-1",
        ),
        state=SandboxSubmitPreflightState(
            prior_attempts=(PriorSandboxSubmitAttempt(key=prior_key, status="accepted"),)
        ),
    )
    assert SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE in duplicate.reason_codes


def test_submit_preflight_requires_lease_idempotency_approval_run_and_sandbox_environment() -> None:
    result = evaluate_sandbox_submit_preflight(
        request=SandboxSubmitPreflightRequest(
            key=_submit_key(approval_id="", uat_run_id="", environment="live"),
            submit_lease_acquired=False,
            idempotency_key="",
        ),
        state=SandboxSubmitPreflightState(),
    )

    assert SandboxSubmitRejectReason.SUBMIT_LEASE_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.IDEMPOTENCY_KEY_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.APPROVAL_ID_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.UAT_RUN_ID_REQUIRED in result.reason_codes
    assert SandboxSubmitRejectReason.ENVIRONMENT_NOT_SANDBOX in result.reason_codes


def test_uat301_report_records_readiness_decision_and_no_live_artifact_boundary() -> None:
    report = Path("docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md").read_text()

    assert "UAT3.0.1 Sandbox Runtime / Approval / Risk Readiness" in report
    assert "fixture/readiness hardening only" in report
    assert "Sandbox Runtime Policy Status" in report
    assert "Sandbox Artifact Label Validation" in report
    assert "Actual Sandbox Order Approval Template" in report
    assert "Approval Scope Fixture Validation" in report
    assert "Sandbox Risk Gate Fixture Validation" in report
    assert "Sandbox Drawdown Feed Fixture Status" in report
    assert "Submit Lease / Duplicate Prevention Fixture Status" in report
    assert "`UAT3.1 is blocked`" in report
    assert "Actual sandbox order submission is not approved" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report
    for phrase in (
        "OrderIntent rows created | `false`",
        "SubmittedOrder rows created | `false`",
        "Executable approvals created | `false`",
        "Private/signed/order endpoint calls made | `false`",
    ):
        assert phrase in report

