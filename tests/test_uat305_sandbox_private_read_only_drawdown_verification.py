from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT,
    SandboxAccountDrawdownFeed,
    SandboxApprovalCandidate,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxDrawdownFeedStatus,
    SandboxDryRunRejectReason,
    SandboxPrivateEndpointCategory,
    SandboxPrivateReadOnlyApproval,
    SandboxPrivateReadOnlyRejectReason,
    SandboxRiskLimits,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    UAT3SandboxExecutableGateDryRunInput,
    evaluate_uat305_private_read_only_drawdown_verification,
    evaluate_uat3_sandbox_executable_gate_dry_run,
    load_hyperliquid_uat_sandbox_credential_env_status,
    redact_sandbox_credential_payload,
    validate_sandbox_account_drawdown_feed,
    validate_sandbox_testnet_base_url,
    validate_uat305_private_read_only_approval,
)


def _approval() -> SandboxPrivateReadOnlyApproval:
    return SandboxPrivateReadOnlyApproval(
        approval_text=(
            f"{REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT}\n\n"
            "This approval does not authorize:\n"
            "- order submission\n"
            "- cancel/amend/retry\n"
            "- private order endpoints\n"
            "- paper trading\n"
            "- live trading\n"
            "- live endpoint access\n"
            "- production auto-submit\n"
            "- broad top-20 order submission"
        ),
        approved_by="founder",
        approved_at_utc=datetime(2026, 5, 10, 14, 20, tzinfo=UTC),
    )


def _sandbox_env() -> dict[str, str]:
    return {
        HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV: "sandbox-private-key-value",
        HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV: "0x1234567890abcdef",
        HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV: "https://api.hyperliquid-testnet.xyz",
    }


def _hyperliquid_account_payload() -> dict[str, object]:
    return {
        "time": 1770000000000,
        "marginSummary": {"accountValue": "9900", "totalMarginUsed": "100"},
        "withdrawable": "9800",
        "assetPositions": [
            {
                "position": {
                    "coin": "ETH",
                    "szi": "0.01",
                    "positionValue": "35.50",
                    "unrealizedPnl": "-100",
                }
            }
        ],
    }


def test_uat305_private_read_only_approval_text_is_required() -> None:
    missing = validate_uat305_private_read_only_approval(None)
    assert missing.blocked is True
    assert (
        SandboxPrivateReadOnlyRejectReason.FOUNDER_OPERATOR_PRIVATE_READ_ONLY_APPROVAL_REQUIRED
        in missing.reason_codes
    )

    wrong_phase = validate_uat305_private_read_only_approval(
        SandboxPrivateReadOnlyApproval(
            approval_text=(
                "I approve UAT3.0.4 sandbox/testnet private read-only credential use "
                "for account-state and drawdown-feed verification only."
            ),
            approved_by="founder",
            approved_at_utc=datetime(2026, 5, 10, 14, 20, tzinfo=UTC),
        )
    )
    assert SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_TEXT_MISMATCH in wrong_phase.reason_codes

    assert validate_uat305_private_read_only_approval(_approval()).allowed is True


def test_sandbox_testnet_endpoint_validation_blocks_live_endpoint() -> None:
    live = validate_sandbox_testnet_base_url("https://api.hyperliquid.xyz")
    assert live.blocked is True
    assert SandboxPrivateReadOnlyRejectReason.BASE_URL_LIVE_FORBIDDEN in live.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.BASE_URL_NOT_RECOGNIZED_AS_SANDBOX in live.reason_codes

    testnet = validate_sandbox_testnet_base_url("https://api.hyperliquid-testnet.xyz")
    assert testnet.allowed is True


def test_missing_credentials_block_loading_and_private_read_only_calls() -> None:
    result = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env={},
        account_state_payload=_hyperliquid_account_payload(),
        observed_at_utc=datetime(2026, 5, 10, 14, 30, tzinfo=UTC),
    )

    assert result.approval_result.allowed is True
    assert result.credential_env_status.credentials_available is False
    assert SandboxPrivateReadOnlyRejectReason.PRIVATE_KEY_MISSING in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.ACCOUNT_MISSING in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.BASE_URL_MISSING in result.reason_codes
    assert result.sandbox_drawdown_feed is None
    assert result.drawdown_feed_status == SandboxDrawdownFeedStatus.MISSING
    assert result.private_endpoint_called is False
    assert result.order_endpoint_called is False
    assert result.api_keys_used is False


def test_env_status_never_retains_private_key_value() -> None:
    status = load_hyperliquid_uat_sandbox_credential_env_status(_sandbox_env())

    assert status.private_key_present is True
    assert status.account_present is True
    assert status.endpoint_sandbox_verified is True
    assert "sandbox-private-key-value" not in str(status)


def test_live_base_url_blocks_even_when_credentials_are_present() -> None:
    env = _sandbox_env()
    env[HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV] = "https://api.hyperliquid.xyz"

    result = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env=env,
        account_state_payload=_hyperliquid_account_payload(),
    )

    assert result.sandbox_drawdown_feed is None
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_NOT_VERIFIED_AS_SANDBOX in result.reason_codes
    assert SandboxPrivateReadOnlyRejectReason.CREDENTIALS_NOT_SANDBOX_ONLY in result.reason_codes
    assert result.private_endpoint_called is False


def test_verified_sandbox_payload_builds_live_fed_not_live_account_drawdown() -> None:
    result = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env=_sandbox_env(),
        account_state_payload=_hyperliquid_account_payload(),
        drawdown_threshold=Decimal("0.05"),
        observed_at_utc=datetime(2026, 5, 10, 14, 30, tzinfo=UTC),
    )

    feed = result.sandbox_drawdown_feed
    assert isinstance(feed, SandboxAccountDrawdownFeed)
    assert result.drawdown_feed_status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED
    assert feed.status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED
    assert feed.source == "sandbox_account"
    assert feed.not_live_account is True
    assert feed.sandbox_account_equity == Decimal("9900")
    assert feed.sandbox_unrealized_pnl == Decimal("-100")
    assert feed.max_drawdown_amount == Decimal("0")
    assert feed.max_drawdown_percent == Decimal("0")
    assert feed.threshold_breached is False
    assert validate_sandbox_account_drawdown_feed(feed, require_live_fed=True).allowed is True


def test_unavailable_fields_are_explicit_from_sandbox_account_response() -> None:
    result = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env=_sandbox_env(),
        account_state_payload={"marginSummary": {}, "assetPositions": []},
    )

    feed = result.sandbox_drawdown_feed
    assert feed is not None
    assert "sandbox_account_equity" in feed.unavailable_fields
    assert "sandbox_realized_pnl" in feed.unavailable_fields
    assert "sandbox_unrealized_pnl" in feed.unavailable_fields
    assert "open_positions_summary" in feed.unavailable_fields
    assert "sandbox_account_equity_unavailable" in feed.reason_codes


def test_order_cancel_amend_retry_remain_blocked_when_private_read_only_is_verified() -> None:
    result = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env=_sandbox_env(),
        account_state_payload=_hyperliquid_account_payload(),
    )

    for category in (
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY,
    ):
        lockout = result.order_lockout_results[category]
        assert lockout.blocked is True
        assert SandboxPrivateReadOnlyRejectReason.ORDER_ENDPOINT_FORBIDDEN in lockout.reason_codes

    assert result.order_endpoint_called is False
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False


def test_credentials_are_redacted_from_config_log_error_report_helpers() -> None:
    payload = {
        "Authorization": "Bearer sandbox-secret-token",
        "private_key": "sandbox-private-key-value",
        "api_key": "sandbox-api-key",
        "secret": "sandbox-secret",
        "password": "sandbox-password",
        "database_url": "postgresql+psycopg://user:password@host:5432/db",
    }

    rendered = str(redact_sandbox_credential_payload(payload))

    assert "sandbox-secret-token" not in rendered
    assert "sandbox-private-key-value" not in rendered
    assert "sandbox-api-key" not in rendered
    assert "sandbox-secret" not in rendered
    assert "sandbox-password" not in rendered
    assert "user:password@host" not in rendered
    assert "<redacted>" in rendered


def test_uat3_dry_run_preflight_consumes_verified_drawdown_but_still_blocks_submission_path() -> None:
    verification = evaluate_uat305_private_read_only_drawdown_verification(
        approval=_approval(),
        env=_sandbox_env(),
        account_state_payload=_hyperliquid_account_payload(),
    )
    runtime_policy = SandboxRuntimePolicy(
        runtime_mode="uat_sandbox",
        sandbox_order_submission_enabled=True,
        private_exchange_endpoints_enabled=True,
        live_endpoint_access=False,
        api_keys_required=True,
        sandbox_only=True,
    )
    now = datetime(2026, 5, 10, 14, 45, tzinfo=UTC)

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
            approval_scope=SandboxApprovalScope(
                approval_id="approval-1",
                uat_run_id="uat3-run-1",
                venue="hyperliquid",
                account_id="sandbox-account-1",
                symbol="ETH",
                component="sleeve_1h",
                max_notional_or_quantity=Decimal("25"),
                expires_at_utc=now + timedelta(hours=1),
                environment="testnet",
            ),
            approval_candidate=SandboxApprovalCandidate(
                uat_run_id="uat3-run-1",
                venue="hyperliquid",
                account_id="sandbox-account-1",
                symbol="ETH",
                component="sleeve_1h",
                requested_notional_or_quantity=Decimal("10"),
                environment="testnet",
            ),
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
                sandbox_drawdown_pct=Decimal("0"),
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
            now_utc=now,
            sandbox_drawdown_feed=verification.sandbox_drawdown_feed,
            founder_operator_actual_submission_approved=False,
            drawdown_feed_status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value,
            real_sandbox_submit_path_wired=False,
        )
    )

    assert result.drawdown_feed_status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value
    assert SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED not in result.reason_codes
    assert (
        SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED
        in result.reason_codes
    )
    assert SandboxDryRunRejectReason.REAL_SANDBOX_SUBMIT_PATH_REQUIRED in result.reason_codes
    assert result.creates_order_intent is False
    assert result.creates_prepared_order is False
    assert result.creates_submitted_order is False
    assert result.creates_executable_approval is False
    assert result.calls_exchange is False


def test_uat305_report_exists_and_records_blocked_local_credential_status() -> None:
    report = Path("docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md")
    assert report.exists()
    text = report.read_text()

    assert "UAT3.0.5 Sandbox Private Read-Only Drawdown Verification" in text
    assert REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT in text
    assert "approval status | `verified`" in text
    assert "credential source status | `blocked_missing_local_environment`" in text
    assert "sandbox_drawdown_feed_missing" in text
    assert "order endpoints called | `false`" in text
    assert "UAT3.1 is blocked" in text
    assert "Actual sandbox order submission is not approved" in text
