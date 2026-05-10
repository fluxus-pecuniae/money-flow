from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT,
    SandboxAccountDrawdownFeed,
    SandboxAccountStateSnapshot,
    SandboxApprovalCandidate,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxCredentialBoundary,
    SandboxDrawdownFeedStatus,
    SandboxDryRunRejectReason,
    SandboxPrivateEndpointCategory,
    SandboxPrivateReadOnlyAccessRequest,
    SandboxPrivateReadOnlyAccountPolicy,
    SandboxPrivateReadOnlyApproval,
    SandboxPrivateReadOnlyRejectReason,
    SandboxRiskLimits,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    UAT3SandboxExecutableGateDryRunInput,
    build_sandbox_account_drawdown_feed,
    evaluate_sandbox_private_read_only_access,
    evaluate_uat3_sandbox_executable_gate_dry_run,
    redact_sandbox_credential_payload,
    validate_sandbox_account_drawdown_feed,
    validate_sandbox_credential_boundary,
    validate_sandbox_private_read_only_approval,
)


def _approval() -> SandboxPrivateReadOnlyApproval:
    return SandboxPrivateReadOnlyApproval(
        approval_text=(
            f"{REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT}\n"
            "This approval does not authorize order submission, cancel/amend/retry, "
            "paper trading, live trading, live endpoint access, production auto-submit, "
            "or broad top-20 order submission."
        ),
        approved_by="founder",
        approved_at_utc=datetime(2026, 5, 10, 13, 45, tzinfo=UTC),
    )


def _credential_boundary(**overrides: object) -> SandboxCredentialBoundary:
    values = {
        "environment": "testnet",
        "credential_source": "environment",
        "credentials_available": True,
        "sandbox_or_testnet_only": True,
        "approved_secret_source": True,
        "live_credentials": False,
        "committed_to_repo": False,
        "logged": False,
        "written_to_obsidian": False,
        "included_in_review_bundle": False,
        "raw_authorization_header_exposed": False,
        "sample_config_payload": {
            "Authorization": "Bearer sandbox-token",
            "api_key": "sandbox-api-key",
            "secret": "sandbox-secret",
            "database_url": "postgresql+psycopg://user:password@host:5432/db",
        },
    }
    values.update(overrides)
    return SandboxCredentialBoundary(**values)


def _private_read_only_policy(**overrides: object) -> SandboxRuntimePolicy:
    values = {
        "runtime_mode": "uat_sandbox",
        "live_trading_enabled": False,
        "paper_trading_enabled": False,
        "exchange_order_submission_enabled": False,
        "sandbox_order_submission_enabled": False,
        "private_exchange_endpoints_enabled": True,
        "live_endpoint_access": False,
        "api_keys_required": True,
        "sandbox_only": True,
    }
    values.update(overrides)
    return SandboxRuntimePolicy(**values)


def _sandbox_drawdown_feed(
    *,
    status: SandboxDrawdownFeedStatus = SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED,
) -> SandboxAccountDrawdownFeed:
    return build_sandbox_account_drawdown_feed(
        snapshot=SandboxAccountStateSnapshot(
            venue="hyperliquid",
            sandbox_account_id="sandbox-account-1",
            timestamp_utc=datetime(2026, 5, 10, 13, 50, tzinfo=UTC),
            sandbox_account_equity=Decimal("9900"),
            sandbox_realized_pnl=None,
            sandbox_unrealized_pnl=Decimal("-100"),
            open_positions_summary=("ETH-PERP qty=0.01",),
            max_sandbox_equity=Decimal("10000"),
            min_sandbox_equity=Decimal("9900"),
        ),
        drawdown_threshold=Decimal("0.05"),
        status=status,
    )


def test_private_read_only_sandbox_credential_approval_is_required() -> None:
    missing = validate_sandbox_private_read_only_approval(None)
    assert missing.blocked is True
    assert SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_REQUIRED in missing.reason_codes

    bad_text = validate_sandbox_private_read_only_approval(
        SandboxPrivateReadOnlyApproval(
            approval_text="I approve something else.",
            approved_by="founder",
            approved_at_utc=datetime(2026, 5, 10, 13, 45, tzinfo=UTC),
        )
    )
    assert SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_TEXT_MISMATCH in bad_text.reason_codes

    good = validate_sandbox_private_read_only_approval(_approval())
    assert good.allowed is True


def test_missing_approval_blocks_private_read_only_call_path() -> None:
    result = evaluate_sandbox_private_read_only_access(
        policy=SandboxPrivateReadOnlyAccountPolicy(),
        request=SandboxPrivateReadOnlyAccessRequest(
            category=SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_ACCOUNT,
            runtime_policy=_private_read_only_policy(),
            approval=None,
            credential_boundary=_credential_boundary(),
        ),
    )

    assert result.blocked is True
    assert SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_REQUIRED in result.reason_codes


def test_credentials_are_redacted_from_config_and_error_payloads() -> None:
    payload = {
        "Authorization": "Bearer abc123",
        "api_key": "abc123",
        "secret": "abc123",
        "password": "abc123",
        "db_url": "postgresql+psycopg://user:password@host:5432/db",
        "nested": {"private_key": "abc123"},
    }

    redacted = redact_sandbox_credential_payload(payload)
    rendered = str(redacted)

    assert "abc123" not in rendered
    assert "user:password@host" not in rendered
    assert "<redacted>" in rendered


def test_credential_boundary_rejects_secret_exposure_and_live_credentials() -> None:
    result = validate_sandbox_credential_boundary(
        _credential_boundary(
            live_credentials=True,
            committed_to_repo=True,
            logged=True,
            written_to_obsidian=True,
            included_in_review_bundle=True,
            raw_authorization_header_exposed=True,
        )
    )

    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_NOT_SANDBOX_ONLY in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_COMMITTED in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_LOGGED in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_WRITTEN_TO_OBSIDIAN in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_INCLUDED_IN_REVIEW_BUNDLE in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.RAW_AUTHORIZATION_HEADER_EXPOSED in result.reason_codes


def test_sandbox_private_read_only_category_is_distinct_from_order_category() -> None:
    allowed = evaluate_sandbox_private_read_only_access(
        policy=SandboxPrivateReadOnlyAccountPolicy(),
        request=SandboxPrivateReadOnlyAccessRequest(
            category=SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_BALANCE,
            runtime_policy=_private_read_only_policy(),
            approval=_approval(),
            credential_boundary=_credential_boundary(),
        ),
    )
    assert allowed.allowed is True

    blocked = evaluate_sandbox_private_read_only_access(
        policy=SandboxPrivateReadOnlyAccountPolicy(),
        request=SandboxPrivateReadOnlyAccessRequest(
            category=SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
            runtime_policy=_private_read_only_policy(),
            approval=_approval(),
            credential_boundary=_credential_boundary(),
        ),
    )
    assert blocked.blocked is True
    assert SandboxPrivateReadOnlyRejectReason.ORDER_ENDPOINT_FORBIDDEN in blocked.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CATEGORY_NOT_ALLOWED_FOR_UAT304 in blocked.reason_codes


def test_order_cancel_amend_retry_remain_blocked_with_private_read_only_enabled() -> None:
    expected = {
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL: SandboxPrivateReadOnlyRejectReason.CANCEL_ENDPOINT_FORBIDDEN,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND: SandboxPrivateReadOnlyRejectReason.AMEND_ENDPOINT_FORBIDDEN,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY: SandboxPrivateReadOnlyRejectReason.RETRY_ENDPOINT_FORBIDDEN,
    }
    for category, reason in expected.items():
        result = evaluate_sandbox_private_read_only_access(
            policy=SandboxPrivateReadOnlyAccountPolicy(),
            request=SandboxPrivateReadOnlyAccessRequest(
                category=category,
                runtime_policy=_private_read_only_policy(),
                approval=_approval(),
                credential_boundary=_credential_boundary(),
            ),
        )

        assert result.blocked is True
        assert SandboxPrivateReadOnlyRejectReason.ORDER_ENDPOINT_FORBIDDEN in result.reason_codes
        assert reason in result.reason_codes


def test_live_endpoint_access_remains_false_and_blocks_private_read_only() -> None:
    result = evaluate_sandbox_private_read_only_access(
        policy=SandboxPrivateReadOnlyAccountPolicy(),
        request=SandboxPrivateReadOnlyAccessRequest(
            category=SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_EQUITY,
            runtime_policy=_private_read_only_policy(live_endpoint_access=True),
            approval=_approval(),
            credential_boundary=_credential_boundary(),
        ),
    )

    assert result.blocked is True
    assert SandboxPrivateReadOnlyRejectReason.LIVE_ENDPOINT_FORBIDDEN in result.reason_codes


def test_sandbox_account_drawdown_feed_labels_and_unavailable_fields_are_explicit() -> None:
    feed = _sandbox_drawdown_feed()

    assert feed.source == "sandbox_account"
    assert feed.not_live_account is True
    assert feed.status == SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED
    assert feed.sandbox_account_equity == Decimal("9900")
    assert feed.max_drawdown_amount == Decimal("100")
    assert feed.max_drawdown_percent == Decimal("0.01")
    assert feed.threshold_breached is False
    assert "sandbox_realized_pnl" in feed.unavailable_fields
    assert SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED in feed.reason_codes


def test_sandbox_account_drawdown_validation_requires_live_fed_status_for_uat31() -> None:
    result = validate_sandbox_account_drawdown_feed(_sandbox_drawdown_feed(), require_live_fed=True)

    assert result.blocked is True
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED in result.reason_codes

    live_fed_result = validate_sandbox_account_drawdown_feed(
        _sandbox_drawdown_feed(status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED),
        require_live_fed=True,
    )
    assert live_fed_result.allowed is True


def _approval_scope() -> SandboxApprovalScope:
    return SandboxApprovalScope(
        approval_id="approval-1",
        uat_run_id="uat3-run-1",
        venue="hyperliquid",
        account_id="sandbox-account-1",
        symbol="ETH",
        component="sleeve_1h",
        max_notional_or_quantity=Decimal("25"),
        expires_at_utc=datetime(2026, 5, 10, 15, 0, tzinfo=UTC),
        environment="testnet",
    )


def _approval_candidate() -> SandboxApprovalCandidate:
    return SandboxApprovalCandidate(
        uat_run_id="uat3-run-1",
        venue="hyperliquid",
        account_id="sandbox-account-1",
        symbol="ETH",
        component="sleeve_1h",
        requested_notional_or_quantity=Decimal("10"),
        environment="testnet",
    )


def test_uat3_dry_run_preflight_can_consume_live_fed_drawdown_status() -> None:
    live_fed_feed = _sandbox_drawdown_feed(status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED)
    runtime_policy = SandboxRuntimePolicy(
        runtime_mode="uat_sandbox",
        sandbox_order_submission_enabled=True,
        private_exchange_endpoints_enabled=True,
        live_endpoint_access=False,
        api_keys_required=True,
        sandbox_only=True,
    )
    result = evaluate_uat3_sandbox_executable_gate_dry_run(
        UAT3SandboxExecutableGateDryRunInput(
            runtime_policy=runtime_policy,
            artifact_labels=SandboxArtifactLabels(
                sandbox=True,
                testnet=True,
                not_live=True,
                not_paper=True,
                uat_run_id="uat3-run-1",
                sandbox_order=True,
                live_endpoint_access=False,
                real_capital=False,
            ),
            approval_scope=_approval_scope(),
            approval_candidate=_approval_candidate(),
            risk_limits=SandboxRiskLimits(
                max_sandbox_notional=Decimal("25"),
                max_sandbox_order_count=1,
                max_daily_sandbox_order_count=1,
                max_sandbox_drawdown_pct=Decimal("0.05"),
                allowed_symbols=("ETH",),
                allowed_venue_accounts=("sandbox-account-1",),
                allowed_venues=("hyperliquid",),
            ),
            risk_request=SandboxRiskRequest(
                venue="hyperliquid",
                account_id="sandbox-account-1",
                symbol="ETH",
                notional=Decimal("10"),
                current_order_count=0,
                current_daily_order_count=0,
                sandbox_drawdown_pct=Decimal("0.01"),
                live_account=False,
                live_endpoint_access=False,
                kill_switch_enabled=False,
                runtime_policy=runtime_policy,
            ),
            submit_request=SandboxSubmitPreflightRequest(
                key=SandboxSubmitAttemptKey(
                    approval_id="approval-1",
                    uat_run_id="uat3-run-1",
                    venue="hyperliquid",
                    account_id="sandbox-account-1",
                    symbol="ETH",
                    component="sleeve_1h",
                    environment="testnet",
                ),
                submit_lease_acquired=True,
                idempotency_key="idem-1",
            ),
            submit_state=SandboxSubmitPreflightState(),
            now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
            sandbox_drawdown_feed=live_fed_feed,
            founder_operator_actual_submission_approved=True,
            drawdown_feed_status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value,
            real_sandbox_submit_path_wired=False,
        )
    )

    assert result.drawdown_feed_status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED not in result.reason_codes
    assert SandboxDryRunRejectReason.REAL_SANDBOX_SUBMIT_PATH_REQUIRED in result.reason_codes
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False


def test_uat304_report_records_blocked_private_endpoint_and_uat31_decision() -> None:
    report = Path("docs/uat3_0_4_sandbox_private_read_only_drawdown.md")
    assert report.exists()
    text = report.read_text()

    assert "UAT3.0.4 Sandbox Private Read-Only Drawdown" in text
    assert REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT in text
    assert "approval status for private read-only credentials" in text
    assert "explicit approval not present" in text
    assert "sandbox_private_read_only_account" in text
    assert "sandbox_order_submission" in text
    assert "order endpoints called | `false`" in text
    assert "UAT3.1 is blocked" in text
    assert "Actual sandbox order submission is not approved" in text
