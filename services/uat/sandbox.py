"""UAT3 sandbox-order readiness primitives.

These helpers are fixture/test-only safety gates for future UAT3.1 design.
They do not submit orders, call exchange endpoints, persist trading artifacts,
or create executable approvals.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from core.security import redact_sensitive_structure


SANDBOX_RUNTIME_MODES: tuple[str, ...] = ("sandbox", "uat_sandbox")
SANDBOX_ENVIRONMENTS: tuple[str, ...] = ("sandbox", "testnet", "uat_sandbox")
RUNTIME_POLICY_RISK_REASON_PREFIX = "runtime_policy_"
REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT = (
    "I approve UAT3.0.4 sandbox/testnet private read-only credential use "
    "for account-state and drawdown-feed verification only."
)
REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT = (
    "I approve UAT3.0.5 sandbox/testnet private read-only credential use "
    "for account-state and drawdown-feed verification only."
)
HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV = "HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY"
HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV = "HYPERLIQUID_UAT_SANDBOX_ACCOUNT"
HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV = "HYPERLIQUID_UAT_SANDBOX_BASE_URL"
HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT_ENV = "HYPERLIQUID_UAT_SANDBOX_MASTER_ACCOUNT"
HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT_ENV = "HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT"
HYPERLIQUID_UAT_SANDBOX_API_WALLET_ADDRESS_ENV = "HYPERLIQUID_UAT_SANDBOX_API_WALLET_ADDRESS"
HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE_ENV = "HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ROLE"
HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS_ENV = "HYPERLIQUID_UAT_SANDBOX_VAULT_ADDRESS"
HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT_ENV = "HYPERLIQUID_UAT_SANDBOX_ACCOUNT_IS_VAULT"
HYPERLIQUID_TESTNET_API_HOST = "api.hyperliquid-testnet.xyz"


class SandboxReadinessReason(StrEnum):
    RUNTIME_MODE_NOT_SANDBOX = "runtime_mode_not_sandbox"
    SANDBOX_SUBMISSION_DISABLED = "sandbox_submission_disabled"
    LIVE_TRADING_ENABLED = "live_trading_enabled"
    PAPER_TRADING_ENABLED = "paper_trading_enabled"
    EXCHANGE_ORDER_SUBMISSION_ENABLED = "exchange_order_submission_enabled"
    PRIVATE_ENDPOINTS_DISABLED = "private_exchange_endpoints_disabled"
    PRIVATE_ENDPOINTS_NOT_SANDBOX_ONLY = "private_exchange_endpoints_not_sandbox_only"
    LIVE_ENDPOINT_FORBIDDEN = "live_endpoint_forbidden"
    SANDBOX_API_KEYS_NOT_CONFIGURED = "sandbox_api_keys_not_configured"
    SANDBOX_LABEL_MISSING_OR_FALSE = "sandbox_label_missing_or_false"
    TESTNET_LABEL_MISSING_OR_FALSE = "testnet_label_missing_or_false"
    NOT_LIVE_LABEL_MISSING_OR_FALSE = "not_live_label_missing_or_false"
    NOT_PAPER_LABEL_MISSING_OR_FALSE = "not_paper_label_missing_or_false"
    UAT_RUN_ID_MISSING = "uat_run_id_missing"
    SANDBOX_ORDER_LABEL_MISSING_OR_FALSE = "sandbox_order_label_missing_or_false"
    LIVE_ENDPOINT_LABEL_NOT_FALSE = "live_endpoint_access_label_not_false"
    REAL_CAPITAL_LABEL_NOT_FALSE = "real_capital_label_not_false"


class SandboxArtifactBoundary(StrEnum):
    PERSISTENCE = "persistence"
    API_SERIALIZATION = "api_serialization"
    DASHBOARD_DISPLAY = "dashboard_display"
    REPORT_GENERATION = "report_generation"


class SandboxPrivateEndpointCategory(StrEnum):
    SANDBOX_PRIVATE_READ_ONLY_ACCOUNT = "sandbox_private_read_only_account"
    SANDBOX_PRIVATE_READ_ONLY_POSITION = "sandbox_private_read_only_position"
    SANDBOX_PRIVATE_READ_ONLY_BALANCE = "sandbox_private_read_only_balance"
    SANDBOX_PRIVATE_READ_ONLY_EQUITY = "sandbox_private_read_only_equity"
    SANDBOX_ORDER_SUBMISSION = "sandbox_order_submission"
    SANDBOX_ORDER_CANCEL = "sandbox_order_cancel"
    SANDBOX_ORDER_AMEND = "sandbox_order_amend"
    SANDBOX_ORDER_RETRY = "sandbox_order_retry"
    LIVE_PRIVATE_FORBIDDEN = "live_private_forbidden"
    UNKNOWN = "unknown"


class SandboxDrawdownFeedStatus(StrEnum):
    MISSING = "sandbox_drawdown_feed_missing"
    FIXTURE_ONLY = "sandbox_drawdown_feed_fixture_only"
    PRIVATE_READ_ONLY_VERIFIED = "sandbox_drawdown_feed_private_read_only_verified"
    LIVE_FED_VERIFIED = "sandbox_drawdown_feed_live_fed_verified"


class HyperliquidSandboxEquitySource(StrEnum):
    STANDARD_PERP_CLEARINGHOUSE = "standard_perp_clearinghouse"
    UNIFIED_MARGIN_SPOT_CLEARINGHOUSE = "unified_margin_spot_clearinghouse"
    PORTFOLIO_MARGIN_SPOT_CLEARINGHOUSE = "portfolio_margin_spot_clearinghouse"
    UNIFIED_MARGIN_SPOT_CLEARINGHOUSE_FALLBACK = "unified_margin_spot_clearinghouse_fallback"
    UNKNOWN = "unknown"


class SandboxPrivateReadOnlyRejectReason(StrEnum):
    FOUNDER_OPERATOR_PRIVATE_READ_ONLY_APPROVAL_REQUIRED = (
        "founder_operator_private_read_only_approval_required"
    )
    PRIVATE_READ_ONLY_APPROVAL_REQUIRED = "sandbox_private_read_only_approval_required"
    PRIVATE_READ_ONLY_APPROVAL_TEXT_MISMATCH = "sandbox_private_read_only_approval_text_mismatch"
    PRIVATE_READ_ONLY_APPROVAL_IDENTITY_MISSING = "sandbox_private_read_only_approval_identity_missing"
    SANDBOX_ENVIRONMENT_REQUIRED = "sandbox_environment_required"
    CREDENTIALS_MISSING = "sandbox_private_read_only_credentials_missing"
    CREDENTIALS_NOT_SANDBOX_ONLY = "sandbox_private_read_only_credentials_not_sandbox_only"
    CREDENTIALS_NOT_VERIFIED_AS_SANDBOX = (
        "sandbox_private_read_only_credentials_not_verified_as_sandbox"
    )
    CREDENTIALS_SOURCE_UNAPPROVED = "sandbox_private_read_only_credentials_source_unapproved"
    PRIVATE_KEY_MISSING = "sandbox_private_read_only_private_key_missing"
    ACCOUNT_MISSING = "sandbox_private_read_only_account_missing"
    BASE_URL_MISSING = "sandbox_private_read_only_base_url_missing"
    BASE_URL_NOT_HTTPS = "sandbox_private_read_only_base_url_not_https"
    BASE_URL_LIVE_FORBIDDEN = "sandbox_private_read_only_base_url_live_forbidden"
    BASE_URL_NOT_RECOGNIZED_AS_SANDBOX = (
        "sandbox_private_read_only_base_url_not_recognized_as_sandbox"
    )
    CREDENTIALS_COMMITTED = "sandbox_credentials_committed_to_repo"
    CREDENTIALS_LOGGED = "sandbox_credentials_logged"
    CREDENTIALS_WRITTEN_TO_OBSIDIAN = "sandbox_credentials_written_to_obsidian"
    CREDENTIALS_INCLUDED_IN_REVIEW_BUNDLE = "sandbox_credentials_included_in_review_bundle"
    RAW_AUTHORIZATION_HEADER_EXPOSED = "raw_authorization_header_exposed"
    RUNTIME_MODE_NOT_SANDBOX = "runtime_mode_not_sandbox"
    LIVE_TRADING_ENABLED = "live_trading_enabled"
    PAPER_TRADING_ENABLED = "paper_trading_enabled"
    GLOBAL_ORDER_SUBMISSION_ENABLED = "exchange_order_submission_enabled"
    SANDBOX_ORDER_SUBMISSION_ENABLED_FORBIDDEN = "sandbox_order_submission_enabled_forbidden_for_private_read_only"
    PRIVATE_ENDPOINTS_DISABLED = "private_exchange_endpoints_disabled"
    PRIVATE_ENDPOINTS_NOT_SANDBOX_ONLY = "private_exchange_endpoints_not_sandbox_only"
    LIVE_ENDPOINT_FORBIDDEN = "live_endpoint_forbidden"
    API_KEYS_REQUIRED_FLAG_FALSE = "sandbox_private_read_only_api_keys_required_flag_false"
    CATEGORY_NOT_ALLOWED_FOR_UAT304 = "private_endpoint_category_not_allowed_for_uat304"
    ORDER_ENDPOINT_FORBIDDEN = "order_endpoint_forbidden"
    CANCEL_ENDPOINT_FORBIDDEN = "cancel_endpoint_forbidden"
    AMEND_ENDPOINT_FORBIDDEN = "amend_endpoint_forbidden"
    RETRY_ENDPOINT_FORBIDDEN = "retry_endpoint_forbidden"
    LIVE_PRIVATE_ENDPOINT_FORBIDDEN = "live_private_endpoint_forbidden"
    UNKNOWN_ENDPOINT_CATEGORY_FORBIDDEN = "unknown_endpoint_category_forbidden"
    SANDBOX_DRAWDOWN_FEED_NOT_SANDBOX_ACCOUNT = "sandbox_drawdown_feed_not_sandbox_account"
    SANDBOX_DRAWDOWN_FEED_LIVE_ACCOUNT_FORBIDDEN = "sandbox_drawdown_feed_live_account_forbidden"
    UNAVAILABLE_FROM_SANDBOX_ACCOUNT_RESPONSE = "unavailable_from_sandbox_account_response"


class SandboxApprovalRejectReason(StrEnum):
    UAT_RUN_ID_MISSING = "missing_uat_run_id"
    WRONG_UAT_RUN_ID = "wrong_uat_run_id"
    WRONG_SYMBOL = "wrong_symbol"
    WRONG_VENUE = "wrong_venue"
    WRONG_ACCOUNT = "wrong_account"
    WRONG_COMPONENT = "wrong_component"
    EXPIRED_APPROVAL = "expired_approval"
    QUANTITY_ABOVE_MAX = "quantity_above_max"
    MISSING_SANDBOX_ENVIRONMENT = "missing_sandbox_environment"
    LIVE_ENVIRONMENT_FORBIDDEN = "live_environment_forbidden"
    PAPER_ENVIRONMENT_FORBIDDEN = "paper_environment_forbidden"
    BROAD_TOP20_APPROVAL_FORBIDDEN = "broad_top20_approval_forbidden"
    ONE_TIME_USE_INTENT_MISSING = "one_time_use_intent_missing"
    APPROVAL_ALREADY_CONSUMED = "approval_already_consumed"
    SANDBOX_POSITIVE_QUANTITY_REQUIRED = "sandbox_positive_quantity_required"


class SandboxRiskRejectReason(StrEnum):
    SANDBOX_NOTIONAL_LIMIT_EXCEEDED = "sandbox_notional_limit_exceeded"
    SANDBOX_ORDER_COUNT_EXCEEDED = "sandbox_order_count_exceeded"
    SANDBOX_DAILY_ORDER_COUNT_EXCEEDED = "sandbox_daily_order_count_exceeded"
    SANDBOX_DRAWDOWN_LIMIT_BREACHED = "sandbox_drawdown_limit_breached"
    SYMBOL_NOT_ALLOWED_FOR_SANDBOX = "symbol_not_allowed_for_sandbox"
    VENUE_ACCOUNT_NOT_ALLOWED_FOR_SANDBOX = "venue_account_not_allowed_for_sandbox"
    LIVE_ACCOUNT_FORBIDDEN = "live_account_forbidden"
    LIVE_ENDPOINT_FORBIDDEN = "live_endpoint_forbidden"
    KILL_SWITCH_ENABLED = "kill_switch_enabled"
    RUNTIME_MODE_NOT_SANDBOX = "runtime_mode_not_sandbox"
    SANDBOX_SUBMISSION_DISABLED = "sandbox_submission_disabled"
    SANDBOX_POSITIVE_LIMIT_REQUIRED = "sandbox_positive_limit_required"
    SANDBOX_POSITIVE_NOTIONAL_REQUIRED = "sandbox_positive_notional_required"
    SANDBOX_DRAWDOWN_THRESHOLD_INVALID = "sandbox_drawdown_threshold_invalid"
    SANDBOX_DRAWDOWN_PERCENT_INVALID = "sandbox_drawdown_percent_invalid"


class SandboxSubmitRejectReason(StrEnum):
    SUBMIT_LEASE_REQUIRED = "submit_lease_required"
    IDEMPOTENCY_KEY_REQUIRED = "idempotency_key_required"
    APPROVAL_ID_REQUIRED = "approval_id_required"
    UAT_RUN_ID_REQUIRED = "uat_run_id_required"
    ENVIRONMENT_NOT_SANDBOX = "environment_not_sandbox"
    DUPLICATE_SAME_APPROVAL_CANDIDATE = "duplicate_same_approval_candidate"
    PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY = "prior_submit_uncertain_blocks_retry"
    CROSS_VENUE_RETRY_FORBIDDEN = "cross_venue_retry_forbidden"
    TOP20_FANOUT_FORBIDDEN = "top20_fanout_forbidden"
    ROUTE_EXECUTOR_FORBIDDEN = "route_executor_forbidden"


class SandboxDryRunRejectReason(StrEnum):
    FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED = (
        "founder_operator_actual_sandbox_submission_approval_required"
    )
    SANDBOX_DRAWDOWN_FEED_MISSING = "sandbox_drawdown_feed_missing"
    SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY = "sandbox_drawdown_feed_fixture_only"
    SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED = "sandbox_drawdown_feed_live_fed_required"
    SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_PERSISTENCE = (
        "sandbox_artifact_labeling_not_enforced_on_persistence"
    )
    SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_API_SERIALIZATION = (
        "sandbox_artifact_labeling_not_enforced_on_api_serialization"
    )
    SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_DASHBOARD_DISPLAY = (
        "sandbox_artifact_labeling_not_enforced_on_dashboard_display"
    )
    SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_REPORT_GENERATION = (
        "sandbox_artifact_labeling_not_enforced_on_report_generation"
    )
    REAL_SANDBOX_SUBMIT_PATH_REQUIRED = "real_sandbox_submit_path_required"
    ENDPOINT_CATEGORY_UNKNOWN = "endpoint_category_unknown"
    ENDPOINT_CATEGORY_NOT_SANDBOX_ORDER_SUBMISSION = (
        "endpoint_category_not_sandbox_order_submission"
    )
    SANDBOX_ORDER_ENDPOINT_TRANSPORT_FORBIDDEN_IN_UAT306 = (
        "sandbox_order_endpoint_transport_forbidden_in_uat306"
    )
    SANDBOX_DRAWDOWN_FEED_STALE = "sandbox_drawdown_feed_stale"
    SANDBOX_DRAWDOWN_FEED_NOT_LIVE_FED_VERIFIED = (
        "sandbox_drawdown_feed_not_live_fed_verified"
    )
    SANDBOX_DRAWDOWN_FEED_NOT_LABELED_NOT_LIVE_ACCOUNT = (
        "sandbox_drawdown_feed_not_labeled_not_live_account"
    )
    SANDBOX_DRAWDOWN_THRESHOLD_BREACHED = "sandbox_drawdown_threshold_breached"


@dataclass(frozen=True)
class SandboxCheckResult:
    allowed: bool
    reason_codes: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return not self.allowed


@dataclass(frozen=True)
class SandboxRuntimePolicySemantics:
    exchange_order_submission_enabled: str
    sandbox_order_submission_enabled: str
    live_endpoint_access: str


def get_sandbox_runtime_policy_semantics() -> SandboxRuntimePolicySemantics:
    """Return the UAT3 runtime flag semantics used by docs, tests, and dry-runs."""

    return SandboxRuntimePolicySemantics(
        exchange_order_submission_enabled=(
            "broad/global/non-sandbox exchange order submission; must remain false for UAT3 sandbox tests"
        ),
        sandbox_order_submission_enabled=(
            "explicit sandbox/testnet-only submission flag; may become true only in a separately approved UAT3.1 run"
        ),
        live_endpoint_access="live endpoint access must remain false for every UAT3 sandbox/testnet path",
    )


@dataclass(frozen=True)
class SandboxRuntimePolicy:
    runtime_mode: str = "uat"
    live_trading_enabled: bool = False
    paper_trading_enabled: bool = False
    exchange_order_submission_enabled: bool = False
    sandbox_order_submission_enabled: bool = False
    private_exchange_endpoints_enabled: bool = False
    live_endpoint_access: bool = False
    api_keys_required: bool = False
    sandbox_only: bool = True

    def evaluate_for_sandbox_submission(self) -> SandboxCheckResult:
        reasons: list[str] = []
        if self.runtime_mode not in SANDBOX_RUNTIME_MODES:
            reasons.append(SandboxReadinessReason.RUNTIME_MODE_NOT_SANDBOX.value)
        if not self.sandbox_order_submission_enabled:
            reasons.append(SandboxReadinessReason.SANDBOX_SUBMISSION_DISABLED.value)
        if self.live_trading_enabled:
            reasons.append(SandboxReadinessReason.LIVE_TRADING_ENABLED.value)
        if self.paper_trading_enabled:
            reasons.append(SandboxReadinessReason.PAPER_TRADING_ENABLED.value)
        if self.exchange_order_submission_enabled:
            reasons.append(SandboxReadinessReason.EXCHANGE_ORDER_SUBMISSION_ENABLED.value)
        if not self.private_exchange_endpoints_enabled:
            reasons.append(SandboxReadinessReason.PRIVATE_ENDPOINTS_DISABLED.value)
        if not self.sandbox_only:
            reasons.append(SandboxReadinessReason.PRIVATE_ENDPOINTS_NOT_SANDBOX_ONLY.value)
        if self.live_endpoint_access:
            reasons.append(SandboxReadinessReason.LIVE_ENDPOINT_FORBIDDEN.value)
        if not self.api_keys_required:
            reasons.append(SandboxReadinessReason.SANDBOX_API_KEYS_NOT_CONFIGURED.value)
        return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))

    def evaluate_for_sandbox_private_read_only(self) -> SandboxCheckResult:
        """Evaluate UAT3.0.4 private-read-only sandbox account access.

        This is intentionally separate from sandbox submission policy: private
        read-only account state may require sandbox/testnet credentials, while
        both global exchange submission and sandbox order submission must remain
        disabled for UAT3.0.4.
        """

        reasons: list[str] = []
        if self.runtime_mode not in SANDBOX_RUNTIME_MODES:
            reasons.append(SandboxPrivateReadOnlyRejectReason.RUNTIME_MODE_NOT_SANDBOX.value)
        if self.live_trading_enabled:
            reasons.append(SandboxPrivateReadOnlyRejectReason.LIVE_TRADING_ENABLED.value)
        if self.paper_trading_enabled:
            reasons.append(SandboxPrivateReadOnlyRejectReason.PAPER_TRADING_ENABLED.value)
        if self.exchange_order_submission_enabled:
            reasons.append(SandboxPrivateReadOnlyRejectReason.GLOBAL_ORDER_SUBMISSION_ENABLED.value)
        if self.sandbox_order_submission_enabled:
            reasons.append(
                SandboxPrivateReadOnlyRejectReason.SANDBOX_ORDER_SUBMISSION_ENABLED_FORBIDDEN.value
            )
        if not self.private_exchange_endpoints_enabled:
            reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_ENDPOINTS_DISABLED.value)
        if not self.sandbox_only:
            reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_ENDPOINTS_NOT_SANDBOX_ONLY.value)
        if self.live_endpoint_access:
            reasons.append(SandboxPrivateReadOnlyRejectReason.LIVE_ENDPOINT_FORBIDDEN.value)
        if not self.api_keys_required:
            reasons.append(SandboxPrivateReadOnlyRejectReason.API_KEYS_REQUIRED_FLAG_FALSE.value)
        return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))


@dataclass(frozen=True)
class SandboxPrivateReadOnlyApproval:
    approval_text: str = ""
    approved_by: str = ""
    approved_at_utc: datetime | None = None


def validate_sandbox_private_read_only_approval(
    approval: SandboxPrivateReadOnlyApproval | None,
    *,
    required_text: str = REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if approval is None:
        reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_REQUIRED.value)
        return SandboxCheckResult(allowed=False, reason_codes=tuple(reasons))
    if required_text not in approval.approval_text:
        reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_TEXT_MISMATCH.value)
    if not approval.approved_by.strip() or approval.approved_at_utc is None:
        reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_IDENTITY_MISSING.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))


def validate_uat305_private_read_only_approval(
    approval: SandboxPrivateReadOnlyApproval | None,
) -> SandboxCheckResult:
    """Validate the exact UAT3.0.5 private-read-only approval boundary."""

    if approval is None:
        return SandboxCheckResult(
            allowed=False,
            reason_codes=(
                SandboxPrivateReadOnlyRejectReason.FOUNDER_OPERATOR_PRIVATE_READ_ONLY_APPROVAL_REQUIRED.value,
                SandboxPrivateReadOnlyRejectReason.PRIVATE_READ_ONLY_APPROVAL_REQUIRED.value,
            ),
        )
    return validate_sandbox_private_read_only_approval(
        approval,
        required_text=REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT,
    )


@dataclass(frozen=True)
class SandboxCredentialBoundary:
    environment: str
    credential_source: str
    credentials_available: bool
    sandbox_or_testnet_only: bool
    approved_secret_source: bool = True
    live_credentials: bool = False
    committed_to_repo: bool = False
    logged: bool = False
    written_to_obsidian: bool = False
    included_in_review_bundle: bool = False
    raw_authorization_header_exposed: bool = False
    sample_config_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class SandboxPrivateReadOnlyCredentialEnvStatus:
    private_key_env_var: str
    account_env_var: str
    base_url_env_var: str
    private_key_present: bool
    account_present: bool
    base_url_present: bool
    base_url: str
    endpoint_sandbox_verified: bool
    credential_source: str = "environment"
    api_keys_used: bool = False
    private_endpoint_called: bool = False
    order_endpoint_called: bool = False
    reason_codes: tuple[str, ...] = ()

    @property
    def credentials_available(self) -> bool:
        return self.private_key_present and self.account_present and self.base_url_present


def validate_sandbox_testnet_base_url(base_url: str) -> SandboxCheckResult:
    """Require an unambiguous sandbox/testnet endpoint before private read-only access."""

    value = base_url.strip()
    reasons: list[str] = []
    if not value:
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_MISSING.value)
        return SandboxCheckResult(allowed=False, reason_codes=tuple(reasons))

    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_NOT_HTTPS.value)
    if host in {"api.hyperliquid.xyz", "hyperliquid.xyz"}:
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_LIVE_FORBIDDEN.value)
    if not ("testnet" in host or "sandbox" in host):
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_NOT_RECOGNIZED_AS_SANDBOX.value)
    if host and host != HYPERLIQUID_TESTNET_API_HOST and "testnet" not in host and "sandbox" not in host:
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_NOT_RECOGNIZED_AS_SANDBOX.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


def load_hyperliquid_uat_sandbox_credential_env_status(
    env: Mapping[str, str | None],
) -> SandboxPrivateReadOnlyCredentialEnvStatus:
    """Inspect sandbox credential environment without retaining secret values."""

    private_key_present = bool((env.get(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV) or "").strip())
    account_present = bool((env.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV) or "").strip())
    base_url = (env.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV) or "").strip()
    endpoint_result = validate_sandbox_testnet_base_url(base_url)

    reasons: list[str] = []
    if not private_key_present:
        reasons.append(SandboxPrivateReadOnlyRejectReason.PRIVATE_KEY_MISSING.value)
    if not account_present:
        reasons.append(SandboxPrivateReadOnlyRejectReason.ACCOUNT_MISSING.value)
    if not base_url:
        reasons.append(SandboxPrivateReadOnlyRejectReason.BASE_URL_MISSING.value)
    reasons.extend(endpoint_result.reason_codes)
    if private_key_present and account_present and base_url and not endpoint_result.allowed:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_NOT_VERIFIED_AS_SANDBOX.value)

    return SandboxPrivateReadOnlyCredentialEnvStatus(
        private_key_env_var=HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
        account_env_var=HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
        base_url_env_var=HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
        private_key_present=private_key_present,
        account_present=account_present,
        base_url_present=bool(base_url),
        base_url=base_url,
        endpoint_sandbox_verified=endpoint_result.allowed,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def credential_boundary_from_uat305_env_status(
    status: SandboxPrivateReadOnlyCredentialEnvStatus,
) -> SandboxCredentialBoundary:
    return SandboxCredentialBoundary(
        environment="testnet" if status.endpoint_sandbox_verified else "unknown",
        credential_source=status.credential_source,
        credentials_available=status.credentials_available,
        sandbox_or_testnet_only=status.endpoint_sandbox_verified,
        approved_secret_source=status.credential_source == "environment",
        live_credentials=not status.endpoint_sandbox_verified and status.base_url_present,
        sample_config_payload={
            "private_key_env_var": status.private_key_env_var,
            "account_env_var": status.account_env_var,
            "base_url_env_var": status.base_url_env_var,
            "private_key_present": status.private_key_present,
            "account_present": status.account_present,
            "base_url": status.base_url,
            "Authorization": "Bearer representative-sandbox-token",
        },
    )


def validate_sandbox_credential_boundary(
    boundary: SandboxCredentialBoundary,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if _normalize(boundary.environment) not in SANDBOX_ENVIRONMENTS:
        reasons.append(SandboxPrivateReadOnlyRejectReason.SANDBOX_ENVIRONMENT_REQUIRED.value)
    if not boundary.credentials_available:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_MISSING.value)
    if not boundary.sandbox_or_testnet_only or boundary.live_credentials:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_NOT_SANDBOX_ONLY.value)
    if not boundary.approved_secret_source:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_SOURCE_UNAPPROVED.value)
    if boundary.committed_to_repo:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_COMMITTED.value)
    if boundary.logged:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_LOGGED.value)
    if boundary.written_to_obsidian:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_WRITTEN_TO_OBSIDIAN.value)
    if boundary.included_in_review_bundle:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CREDENTIALS_INCLUDED_IN_REVIEW_BUNDLE.value)
    if boundary.raw_authorization_header_exposed:
        reasons.append(SandboxPrivateReadOnlyRejectReason.RAW_AUTHORIZATION_HEADER_EXPOSED.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))


def redact_sandbox_credential_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Redact a representative sandbox credential/config payload before display."""

    redacted = redact_sensitive_structure(dict(payload))
    if not isinstance(redacted, dict):  # Defensive; dict input should remain dict.
        return {}
    return redacted


@dataclass(frozen=True)
class SandboxPrivateReadOnlyAccountPolicy:
    venue: str = "hyperliquid"
    environment: str = "testnet"
    allowed_categories: tuple[SandboxPrivateEndpointCategory, ...] = (
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_ACCOUNT,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_POSITION,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_BALANCE,
        SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_EQUITY,
    )
    forbidden_categories: tuple[SandboxPrivateEndpointCategory, ...] = (
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY,
        SandboxPrivateEndpointCategory.LIVE_PRIVATE_FORBIDDEN,
        SandboxPrivateEndpointCategory.UNKNOWN,
    )
    explicit_approval_required: bool = True
    required_approval_text: str = REQUIRED_UAT304_PRIVATE_READ_ONLY_APPROVAL_TEXT
    fail_closed: bool = True
    calls_exchange: bool = False
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False


@dataclass(frozen=True)
class SandboxPrivateReadOnlyAccessRequest:
    category: SandboxPrivateEndpointCategory
    runtime_policy: SandboxRuntimePolicy
    approval: SandboxPrivateReadOnlyApproval | None
    credential_boundary: SandboxCredentialBoundary


def evaluate_sandbox_private_read_only_access(
    *,
    policy: SandboxPrivateReadOnlyAccountPolicy,
    request: SandboxPrivateReadOnlyAccessRequest,
) -> SandboxCheckResult:
    """Evaluate UAT3.0.4 private read-only access without network side effects."""

    reasons: list[str] = []
    if policy.explicit_approval_required:
        reasons.extend(
            validate_sandbox_private_read_only_approval(
                request.approval,
                required_text=policy.required_approval_text,
            ).reason_codes
        )
    reasons.extend(validate_sandbox_credential_boundary(request.credential_boundary).reason_codes)
    reasons.extend(request.runtime_policy.evaluate_for_sandbox_private_read_only().reason_codes)

    category = request.category
    if category in {
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND,
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY,
    }:
        reasons.append(SandboxPrivateReadOnlyRejectReason.ORDER_ENDPOINT_FORBIDDEN.value)
    if category == SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CANCEL_ENDPOINT_FORBIDDEN.value)
    if category == SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND:
        reasons.append(SandboxPrivateReadOnlyRejectReason.AMEND_ENDPOINT_FORBIDDEN.value)
    if category == SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY:
        reasons.append(SandboxPrivateReadOnlyRejectReason.RETRY_ENDPOINT_FORBIDDEN.value)
    if category == SandboxPrivateEndpointCategory.LIVE_PRIVATE_FORBIDDEN:
        reasons.append(SandboxPrivateReadOnlyRejectReason.LIVE_PRIVATE_ENDPOINT_FORBIDDEN.value)
    if category == SandboxPrivateEndpointCategory.UNKNOWN:
        reasons.append(SandboxPrivateReadOnlyRejectReason.UNKNOWN_ENDPOINT_CATEGORY_FORBIDDEN.value)
    if category not in policy.allowed_categories:
        reasons.append(SandboxPrivateReadOnlyRejectReason.CATEGORY_NOT_ALLOWED_FOR_UAT304.value)

    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class SandboxArtifactLabels:
    sandbox: bool
    testnet: bool
    not_live: bool
    not_paper: bool
    uat_run_id: str
    sandbox_order: bool
    live_endpoint_access: bool
    real_capital: bool


def validate_sandbox_artifact_labels(labels: SandboxArtifactLabels) -> SandboxCheckResult:
    reasons: list[str] = []
    if not labels.sandbox:
        reasons.append(SandboxReadinessReason.SANDBOX_LABEL_MISSING_OR_FALSE.value)
    if not labels.testnet:
        reasons.append(SandboxReadinessReason.TESTNET_LABEL_MISSING_OR_FALSE.value)
    if not labels.not_live:
        reasons.append(SandboxReadinessReason.NOT_LIVE_LABEL_MISSING_OR_FALSE.value)
    if not labels.not_paper:
        reasons.append(SandboxReadinessReason.NOT_PAPER_LABEL_MISSING_OR_FALSE.value)
    if not labels.uat_run_id.strip():
        reasons.append(SandboxReadinessReason.UAT_RUN_ID_MISSING.value)
    if not labels.sandbox_order:
        reasons.append(SandboxReadinessReason.SANDBOX_ORDER_LABEL_MISSING_OR_FALSE.value)
    if labels.live_endpoint_access:
        reasons.append(SandboxReadinessReason.LIVE_ENDPOINT_LABEL_NOT_FALSE.value)
    if labels.real_capital:
        reasons.append(SandboxReadinessReason.REAL_CAPITAL_LABEL_NOT_FALSE.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))


@dataclass(frozen=True)
class SandboxArtifactBoundaryValidation:
    boundary: SandboxArtifactBoundary
    result: SandboxCheckResult
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False
    calls_exchange: bool = False


def validate_sandbox_artifact_boundary(
    *,
    labels: SandboxArtifactLabels,
    boundary: SandboxArtifactBoundary,
) -> SandboxArtifactBoundaryValidation:
    """Validate sandbox labels before a future artifact crosses a named boundary."""

    return SandboxArtifactBoundaryValidation(
        boundary=boundary,
        result=validate_sandbox_artifact_labels(labels),
    )


def validate_sandbox_artifact_boundaries(
    *,
    labels: SandboxArtifactLabels,
    boundaries: tuple[SandboxArtifactBoundary, ...] = (
        SandboxArtifactBoundary.PERSISTENCE,
        SandboxArtifactBoundary.API_SERIALIZATION,
        SandboxArtifactBoundary.DASHBOARD_DISPLAY,
        SandboxArtifactBoundary.REPORT_GENERATION,
    ),
) -> tuple[SandboxArtifactBoundaryValidation, ...]:
    return tuple(validate_sandbox_artifact_boundary(labels=labels, boundary=boundary) for boundary in boundaries)


@dataclass(frozen=True)
class SandboxApprovalScope:
    approval_id: str
    uat_run_id: str
    venue: str
    account_id: str
    symbol: str
    component: str
    max_notional_or_quantity: Decimal
    expires_at_utc: datetime
    environment: str
    one_time_use_intent: bool = True
    not_live: bool = True
    not_paper: bool = True
    broad_top20_submission: bool = False
    consumed: bool = False


@dataclass(frozen=True)
class SandboxApprovalCandidate:
    uat_run_id: str
    venue: str
    account_id: str
    symbol: str
    component: str
    requested_notional_or_quantity: Decimal
    environment: str
    broad_top20_submission: bool = False


def _normalize(value: str) -> str:
    return value.strip().lower()


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def validate_sandbox_approval_scope(
    *,
    scope: SandboxApprovalScope,
    candidate: SandboxApprovalCandidate,
    now_utc: datetime,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if not scope.uat_run_id.strip() or not candidate.uat_run_id.strip():
        reasons.append(SandboxApprovalRejectReason.UAT_RUN_ID_MISSING.value)
    elif scope.uat_run_id != candidate.uat_run_id:
        reasons.append(SandboxApprovalRejectReason.WRONG_UAT_RUN_ID.value)
    if _normalize(scope.venue) != _normalize(candidate.venue):
        reasons.append(SandboxApprovalRejectReason.WRONG_VENUE.value)
    if scope.account_id != candidate.account_id:
        reasons.append(SandboxApprovalRejectReason.WRONG_ACCOUNT.value)
    if _normalize(scope.symbol) != _normalize(candidate.symbol):
        reasons.append(SandboxApprovalRejectReason.WRONG_SYMBOL.value)
    if _normalize(scope.component) != _normalize(candidate.component):
        reasons.append(SandboxApprovalRejectReason.WRONG_COMPONENT.value)
    if _as_aware_utc(now_utc) >= _as_aware_utc(scope.expires_at_utc):
        reasons.append(SandboxApprovalRejectReason.EXPIRED_APPROVAL.value)
    if scope.max_notional_or_quantity <= 0:
        reasons.append(SandboxApprovalRejectReason.SANDBOX_POSITIVE_QUANTITY_REQUIRED.value)
    if candidate.requested_notional_or_quantity <= 0:
        reasons.append(SandboxApprovalRejectReason.SANDBOX_POSITIVE_QUANTITY_REQUIRED.value)
    if candidate.requested_notional_or_quantity > scope.max_notional_or_quantity:
        reasons.append(SandboxApprovalRejectReason.QUANTITY_ABOVE_MAX.value)
    if _normalize(scope.environment) not in SANDBOX_ENVIRONMENTS or _normalize(candidate.environment) not in SANDBOX_ENVIRONMENTS:
        reasons.append(SandboxApprovalRejectReason.MISSING_SANDBOX_ENVIRONMENT.value)
    if _normalize(scope.environment) == "live" or _normalize(candidate.environment) == "live" or not scope.not_live:
        reasons.append(SandboxApprovalRejectReason.LIVE_ENVIRONMENT_FORBIDDEN.value)
    if _normalize(scope.environment) == "paper" or _normalize(candidate.environment) == "paper" or not scope.not_paper:
        reasons.append(SandboxApprovalRejectReason.PAPER_ENVIRONMENT_FORBIDDEN.value)
    if scope.broad_top20_submission or candidate.broad_top20_submission:
        reasons.append(SandboxApprovalRejectReason.BROAD_TOP20_APPROVAL_FORBIDDEN.value)
    if not scope.one_time_use_intent:
        reasons.append(SandboxApprovalRejectReason.ONE_TIME_USE_INTENT_MISSING.value)
    if scope.consumed:
        reasons.append(SandboxApprovalRejectReason.APPROVAL_ALREADY_CONSUMED.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(reasons))


@dataclass(frozen=True)
class SandboxRiskLimits:
    max_sandbox_notional: Decimal
    max_sandbox_order_count: int
    max_daily_sandbox_order_count: int
    max_sandbox_drawdown_pct: Decimal
    allowed_symbols: tuple[str, ...]
    allowed_venue_accounts: tuple[str, ...]
    allowed_venues: tuple[str, ...]


@dataclass(frozen=True)
class SandboxRiskRequest:
    venue: str
    account_id: str
    symbol: str
    notional: Decimal
    current_order_count: int
    current_daily_order_count: int
    sandbox_drawdown_pct: Decimal
    live_account: bool
    live_endpoint_access: bool
    kill_switch_enabled: bool
    runtime_policy: SandboxRuntimePolicy


def evaluate_sandbox_risk_gates(
    *,
    limits: SandboxRiskLimits,
    request: SandboxRiskRequest,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if (
        limits.max_sandbox_notional <= 0
        or limits.max_sandbox_order_count <= 0
        or limits.max_daily_sandbox_order_count <= 0
    ):
        reasons.append(SandboxRiskRejectReason.SANDBOX_POSITIVE_LIMIT_REQUIRED.value)
    if limits.max_sandbox_drawdown_pct < 0:
        reasons.append(SandboxRiskRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_INVALID.value)
    if request.notional <= 0:
        reasons.append(SandboxRiskRejectReason.SANDBOX_POSITIVE_NOTIONAL_REQUIRED.value)
    if request.sandbox_drawdown_pct < 0:
        reasons.append(SandboxRiskRejectReason.SANDBOX_DRAWDOWN_PERCENT_INVALID.value)
    if request.notional > limits.max_sandbox_notional:
        reasons.append(SandboxRiskRejectReason.SANDBOX_NOTIONAL_LIMIT_EXCEEDED.value)
    if request.current_order_count >= limits.max_sandbox_order_count:
        reasons.append(SandboxRiskRejectReason.SANDBOX_ORDER_COUNT_EXCEEDED.value)
    if request.current_daily_order_count >= limits.max_daily_sandbox_order_count:
        reasons.append(SandboxRiskRejectReason.SANDBOX_DAILY_ORDER_COUNT_EXCEEDED.value)
    if request.sandbox_drawdown_pct >= limits.max_sandbox_drawdown_pct:
        reasons.append(SandboxRiskRejectReason.SANDBOX_DRAWDOWN_LIMIT_BREACHED.value)
    if request.symbol.upper() not in {symbol.upper() for symbol in limits.allowed_symbols}:
        reasons.append(SandboxRiskRejectReason.SYMBOL_NOT_ALLOWED_FOR_SANDBOX.value)
    if request.account_id not in limits.allowed_venue_accounts or request.venue.lower() not in {
        venue.lower() for venue in limits.allowed_venues
    }:
        reasons.append(SandboxRiskRejectReason.VENUE_ACCOUNT_NOT_ALLOWED_FOR_SANDBOX.value)
    if request.live_account:
        reasons.append(SandboxRiskRejectReason.LIVE_ACCOUNT_FORBIDDEN.value)
    if request.live_endpoint_access:
        reasons.append(SandboxRiskRejectReason.LIVE_ENDPOINT_FORBIDDEN.value)
    if request.kill_switch_enabled:
        reasons.append(SandboxRiskRejectReason.KILL_SWITCH_ENABLED.value)
    runtime_result = request.runtime_policy.evaluate_for_sandbox_submission()
    for runtime_reason in runtime_result.reason_codes:
        reasons.append(f"{RUNTIME_POLICY_RISK_REASON_PREFIX}{runtime_reason}")
    if SandboxReadinessReason.RUNTIME_MODE_NOT_SANDBOX.value in runtime_result.reason_codes:
        reasons.append(SandboxRiskRejectReason.RUNTIME_MODE_NOT_SANDBOX.value)
    if SandboxReadinessReason.SANDBOX_SUBMISSION_DISABLED.value in runtime_result.reason_codes:
        reasons.append(SandboxRiskRejectReason.SANDBOX_SUBMISSION_DISABLED.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class SandboxDrawdownFeedFixture:
    sandbox_account_equity: Decimal
    sandbox_realized_pnl: Decimal | None
    sandbox_unrealized_pnl: Decimal | None
    max_sandbox_equity: Decimal
    max_drawdown_amount: Decimal
    max_drawdown_percent: Decimal
    drawdown_threshold: Decimal
    threshold_breached: bool
    reason_codes: tuple[str, ...]
    timestamp_utc: datetime
    venue_account_id: str
    source: str = "sandbox_account"
    not_live_account: bool = True


@dataclass(frozen=True)
class SandboxAccountStateSnapshot:
    venue: str
    sandbox_account_id: str
    timestamp_utc: datetime
    sandbox_account_equity: Decimal | None
    sandbox_realized_pnl: Decimal | None = None
    sandbox_unrealized_pnl: Decimal | None = None
    open_positions_summary: tuple[str, ...] = ()
    max_sandbox_equity: Decimal | None = None
    min_sandbox_equity: Decimal | None = None
    source: str = "sandbox_account"
    not_live_account: bool = True


@dataclass(frozen=True)
class HyperliquidSandboxEquityResolution:
    selected_equity_source: HyperliquidSandboxEquitySource
    perp_account_value: Decimal | None
    perp_withdrawable: Decimal | None
    spot_usdc_total: Decimal | None
    spot_usdc_hold: Decimal | None
    selected_sandbox_equity: Decimal | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class SandboxAccountDrawdownFeed:
    venue: str
    sandbox_account_id: str
    source: str
    not_live_account: bool
    timestamp_utc: datetime
    sandbox_account_equity: Decimal | None
    sandbox_realized_pnl: Decimal | None
    sandbox_unrealized_pnl: Decimal | None
    open_positions_summary: tuple[str, ...]
    max_sandbox_equity: Decimal | None
    min_sandbox_equity: Decimal | None
    max_drawdown_amount: Decimal | None
    max_drawdown_percent: Decimal | None
    drawdown_threshold: Decimal
    threshold_breached: bool | None
    reason_codes: tuple[str, ...]
    unavailable_fields: tuple[str, ...]
    status: SandboxDrawdownFeedStatus


@dataclass(frozen=True)
class UAT305PrivateReadOnlyDrawdownVerificationResult:
    approval_result: SandboxCheckResult
    credential_env_status: SandboxPrivateReadOnlyCredentialEnvStatus
    credential_boundary_result: SandboxCheckResult
    account_access_result: SandboxCheckResult
    order_lockout_results: dict[SandboxPrivateEndpointCategory, SandboxCheckResult]
    sandbox_drawdown_feed: SandboxAccountDrawdownFeed | None
    drawdown_feed_status: SandboxDrawdownFeedStatus
    private_endpoint_called: bool = False
    order_endpoint_called: bool = False
    api_keys_used: bool = False
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False

    @property
    def reason_codes(self) -> tuple[str, ...]:
        reasons: list[str] = []
        reasons.extend(self.approval_result.reason_codes)
        reasons.extend(self.credential_env_status.reason_codes)
        reasons.extend(self.credential_boundary_result.reason_codes)
        reasons.extend(self.account_access_result.reason_codes)
        for result in self.order_lockout_results.values():
            reasons.extend(result.reason_codes)
        if self.sandbox_drawdown_feed is None:
            reasons.append(SandboxDrawdownFeedStatus.MISSING.value)
        return tuple(dict.fromkeys(reasons))

    @property
    def live_fed_drawdown_verified(self) -> bool:
        return self.drawdown_feed_status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED


def build_sandbox_drawdown_feed_fixture(
    *,
    sandbox_account_equity: Decimal,
    max_sandbox_equity: Decimal,
    drawdown_threshold: Decimal,
    timestamp_utc: datetime,
    venue_account_id: str,
    sandbox_realized_pnl: Decimal | None = None,
    sandbox_unrealized_pnl: Decimal | None = None,
) -> SandboxDrawdownFeedFixture:
    if sandbox_account_equity <= 0:
        raise ValueError("sandbox_account_equity must be positive")
    if max_sandbox_equity <= 0:
        raise ValueError("max_sandbox_equity must be positive")
    if drawdown_threshold < 0:
        raise ValueError(SandboxRiskRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_INVALID.value)
    drawdown_amount = max(Decimal("0"), max_sandbox_equity - sandbox_account_equity)
    drawdown_percent = drawdown_amount / max_sandbox_equity
    threshold_breached = drawdown_percent >= drawdown_threshold
    reasons = ["sandbox_account_drawdown_fixture_not_live_account"]
    if threshold_breached:
        reasons.append("sandbox_drawdown_threshold_breached")
    else:
        reasons.append("sandbox_drawdown_within_limit")
    return SandboxDrawdownFeedFixture(
        sandbox_account_equity=sandbox_account_equity,
        sandbox_realized_pnl=sandbox_realized_pnl,
        sandbox_unrealized_pnl=sandbox_unrealized_pnl,
        max_sandbox_equity=max_sandbox_equity,
        max_drawdown_amount=drawdown_amount,
        max_drawdown_percent=drawdown_percent,
        drawdown_threshold=drawdown_threshold,
        threshold_breached=threshold_breached,
        reason_codes=tuple(reasons),
        timestamp_utc=timestamp_utc,
        venue_account_id=venue_account_id,
    )


def build_sandbox_account_drawdown_feed(
    *,
    snapshot: SandboxAccountStateSnapshot,
    drawdown_threshold: Decimal,
    status: SandboxDrawdownFeedStatus = SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED,
) -> SandboxAccountDrawdownFeed:
    """Build a sandbox account drawdown feed from caller-supplied account truth.

    The function does not fetch account state. UAT3.0.4 may pass a real sandbox
    account snapshot only after explicit private-read-only credential approval.
    Without approval, tests use local fixtures and reports must mark the feed
    blocked or fixture-only.
    """

    if drawdown_threshold < 0:
        raise ValueError(SandboxRiskRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_INVALID.value)

    unavailable: list[str] = []
    reasons: list[str] = []
    if snapshot.source != "sandbox_account":
        reasons.append(SandboxPrivateReadOnlyRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_SANDBOX_ACCOUNT.value)
    if not snapshot.not_live_account:
        reasons.append(SandboxPrivateReadOnlyRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_ACCOUNT_FORBIDDEN.value)
    if snapshot.sandbox_account_equity is None:
        unavailable.append("sandbox_account_equity")
    if snapshot.sandbox_realized_pnl is None:
        unavailable.append("sandbox_realized_pnl")
    if snapshot.sandbox_unrealized_pnl is None:
        unavailable.append("sandbox_unrealized_pnl")
    if not snapshot.open_positions_summary:
        unavailable.append("open_positions_summary")

    max_equity = snapshot.max_sandbox_equity
    min_equity = snapshot.min_sandbox_equity
    max_drawdown_amount: Decimal | None = None
    max_drawdown_percent: Decimal | None = None
    threshold_breached: bool | None = None
    if snapshot.sandbox_account_equity is not None:
        max_equity = max_equity if max_equity is not None else snapshot.sandbox_account_equity
        min_equity = min_equity if min_equity is not None else snapshot.sandbox_account_equity
        max_drawdown_amount = max(Decimal("0"), max_equity - snapshot.sandbox_account_equity)
        max_drawdown_percent = max_drawdown_amount / max_equity if max_equity > 0 else None
        threshold_breached = (
            max_drawdown_percent is not None and max_drawdown_percent >= drawdown_threshold
        )
        if threshold_breached:
            reasons.append("sandbox_drawdown_threshold_breached")
        else:
            reasons.append("sandbox_drawdown_within_limit")
    else:
        reasons.append("sandbox_account_equity_unavailable")

    if status == SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED:
        reasons.append(SandboxDrawdownFeedStatus.PRIVATE_READ_ONLY_VERIFIED.value)
    elif status == SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED:
        reasons.append(SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value)
    elif status == SandboxDrawdownFeedStatus.FIXTURE_ONLY:
        reasons.append(SandboxDrawdownFeedStatus.FIXTURE_ONLY.value)
    else:
        reasons.append(SandboxDrawdownFeedStatus.MISSING.value)

    return SandboxAccountDrawdownFeed(
        venue=snapshot.venue,
        sandbox_account_id=snapshot.sandbox_account_id,
        source=snapshot.source,
        not_live_account=snapshot.not_live_account,
        timestamp_utc=snapshot.timestamp_utc,
        sandbox_account_equity=snapshot.sandbox_account_equity,
        sandbox_realized_pnl=snapshot.sandbox_realized_pnl,
        sandbox_unrealized_pnl=snapshot.sandbox_unrealized_pnl,
        open_positions_summary=snapshot.open_positions_summary,
        max_sandbox_equity=max_equity,
        min_sandbox_equity=min_equity,
        max_drawdown_amount=max_drawdown_amount,
        max_drawdown_percent=max_drawdown_percent,
        drawdown_threshold=drawdown_threshold,
        threshold_breached=threshold_breached,
        reason_codes=tuple(dict.fromkeys(reasons)),
        unavailable_fields=tuple(unavailable),
        status=status,
    )


def build_hyperliquid_sandbox_account_snapshot_from_payload(
    *,
    payload: Mapping[str, Any],
    sandbox_account_id: str,
    observed_at_utc: datetime | None = None,
) -> SandboxAccountStateSnapshot:
    """Build a sandbox account snapshot from a Hyperliquid account-state payload.

    This parser does not fetch network data and does not sign requests. Callers
    may supply a real sandbox/testnet private-read-only response only after the
    UAT3.0.5 approval and credential boundary gates pass.
    """

    margin_summary = payload.get("marginSummary") if isinstance(payload.get("marginSummary"), Mapping) else {}
    cross_margin = (
        payload.get("crossMarginSummary") if isinstance(payload.get("crossMarginSummary"), Mapping) else {}
    )
    account_value = _decimal_or_none(
        margin_summary.get("accountValue")
        if isinstance(margin_summary, Mapping)
        else None
    )
    if account_value is None:
        account_value = _decimal_or_none(cross_margin.get("accountValue") if isinstance(cross_margin, Mapping) else None)

    asset_positions = payload.get("assetPositions")
    open_positions: list[str] = []
    unrealized_pnl = Decimal("0")
    saw_unrealized_pnl = False
    if isinstance(asset_positions, list):
        for item in asset_positions:
            if not isinstance(item, Mapping):
                continue
            position = item.get("position")
            if not isinstance(position, Mapping):
                continue
            coin = str(position.get("coin") or "unknown")
            size = str(position.get("szi") or position.get("sz") or "0")
            value = str(position.get("positionValue") or "0")
            if size not in {"0", "0.0", ""}:
                open_positions.append(f"{coin} size={size} value={value}")
            pnl_value = _decimal_or_none(position.get("unrealizedPnl"))
            if pnl_value is not None:
                unrealized_pnl += pnl_value
                saw_unrealized_pnl = True

    payload_time = _decimal_or_none(payload.get("time"))
    timestamp = observed_at_utc
    if timestamp is None and payload_time is not None:
        timestamp = datetime.fromtimestamp(int(payload_time) / 1000, tz=UTC)
    if timestamp is None:
        timestamp = datetime.now(tz=UTC)

    return SandboxAccountStateSnapshot(
        venue="hyperliquid",
        sandbox_account_id=sandbox_account_id,
        timestamp_utc=timestamp,
        sandbox_account_equity=account_value,
        sandbox_realized_pnl=_decimal_or_none(payload.get("realizedPnl")),
        sandbox_unrealized_pnl=unrealized_pnl if saw_unrealized_pnl else None,
        open_positions_summary=tuple(open_positions),
        max_sandbox_equity=account_value,
        min_sandbox_equity=account_value,
        source="sandbox_account",
        not_live_account=True,
    )


def _hyperliquid_spot_usdc_balance(payload: Mapping[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    balances = payload.get("balances")
    if not isinstance(balances, list):
        return None, None
    for item in balances:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("coin") or "").upper() != "USDC":
            continue
        return _decimal_or_none(item.get("total")), _decimal_or_none(item.get("hold"))
    return None, None


def resolve_hyperliquid_sandbox_equity_source(
    *,
    perp_payload: Mapping[str, Any],
    spot_payload: Mapping[str, Any] | None = None,
    unified_mode_hint: bool = False,
    portfolio_margin_hint: bool = False,
) -> HyperliquidSandboxEquityResolution:
    """Resolve sandbox equity without assuming standard perp-only margin.

    Hyperliquid unified/portfolio margin can expose usable USDC in
    spotClearinghouseState while clearinghouseState accountValue is zero. This
    resolver keeps the active UAT standard-perp path while preserving unified
    compatibility for gates and reports.
    """

    margin_summary = perp_payload.get("marginSummary") if isinstance(perp_payload.get("marginSummary"), Mapping) else {}
    cross_margin = (
        perp_payload.get("crossMarginSummary")
        if isinstance(perp_payload.get("crossMarginSummary"), Mapping)
        else {}
    )
    perp_account_value = _decimal_or_none(
        margin_summary.get("accountValue") if isinstance(margin_summary, Mapping) else None
    )
    if perp_account_value is None:
        perp_account_value = _decimal_or_none(
            cross_margin.get("accountValue") if isinstance(cross_margin, Mapping) else None
        )
    perp_withdrawable = _decimal_or_none(perp_payload.get("withdrawable"))

    spot_usdc_total: Decimal | None = None
    spot_usdc_hold: Decimal | None = None
    spot_available: Decimal | None = None
    if spot_payload is not None:
        spot_usdc_total, spot_usdc_hold = _hyperliquid_spot_usdc_balance(spot_payload)
        if spot_usdc_total is not None and spot_usdc_hold is not None:
            spot_available = spot_usdc_total - spot_usdc_hold

    reasons: list[str] = []
    selected_source = HyperliquidSandboxEquitySource.UNKNOWN
    selected_equity: Decimal | None = None
    if perp_account_value is not None and perp_account_value > 0:
        selected_source = HyperliquidSandboxEquitySource.STANDARD_PERP_CLEARINGHOUSE
        selected_equity = perp_account_value
        reasons.append("standard_perp_clearinghouse_equity_selected")
    elif spot_available is not None and spot_available > 0:
        if portfolio_margin_hint:
            selected_source = HyperliquidSandboxEquitySource.PORTFOLIO_MARGIN_SPOT_CLEARINGHOUSE
            reasons.append("portfolio_margin_spot_clearinghouse_equity_selected")
        elif unified_mode_hint:
            selected_source = HyperliquidSandboxEquitySource.UNIFIED_MARGIN_SPOT_CLEARINGHOUSE
            reasons.append("unified_margin_spot_clearinghouse_equity_selected")
        else:
            selected_source = HyperliquidSandboxEquitySource.UNIFIED_MARGIN_SPOT_CLEARINGHOUSE_FALLBACK
            reasons.append("unified_margin_spot_clearinghouse_fallback_selected")
        selected_equity = spot_available
    else:
        reasons.append("sandbox_equity_source_unavailable")

    return HyperliquidSandboxEquityResolution(
        selected_equity_source=selected_source,
        perp_account_value=perp_account_value,
        perp_withdrawable=perp_withdrawable,
        spot_usdc_total=spot_usdc_total,
        spot_usdc_hold=spot_usdc_hold,
        selected_sandbox_equity=selected_equity,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def evaluate_uat305_private_read_only_drawdown_verification(
    *,
    approval: SandboxPrivateReadOnlyApproval | None,
    env: Mapping[str, str | None],
    account_state_payload: Mapping[str, Any] | None = None,
    drawdown_threshold: Decimal = Decimal("0.05"),
    observed_at_utc: datetime | None = None,
) -> UAT305PrivateReadOnlyDrawdownVerificationResult:
    """Evaluate UAT3.0.5 private-read-only drawdown readiness without side effects.

    The function never reads or returns secret values, never submits orders, and
    never calls network transport. Supplying an account-state payload represents
    a caller-provided sandbox/testnet read-only response after external transport
    controls have already passed.
    """

    approval_result = validate_uat305_private_read_only_approval(approval)
    env_status = load_hyperliquid_uat_sandbox_credential_env_status(env)
    credential_boundary = credential_boundary_from_uat305_env_status(env_status)
    credential_result = validate_sandbox_credential_boundary(credential_boundary)
    runtime_policy = SandboxRuntimePolicy(
        runtime_mode="uat_sandbox",
        live_trading_enabled=False,
        paper_trading_enabled=False,
        exchange_order_submission_enabled=False,
        sandbox_order_submission_enabled=False,
        private_exchange_endpoints_enabled=True,
        live_endpoint_access=False,
        api_keys_required=True,
        sandbox_only=True,
    )
    account_access_result = evaluate_sandbox_private_read_only_access(
        policy=SandboxPrivateReadOnlyAccountPolicy(
            required_approval_text=REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT,
        ),
        request=SandboxPrivateReadOnlyAccessRequest(
            category=SandboxPrivateEndpointCategory.SANDBOX_PRIVATE_READ_ONLY_ACCOUNT,
            runtime_policy=runtime_policy,
            approval=approval,
            credential_boundary=credential_boundary,
        ),
    )

    order_lockout_results = {
        category: evaluate_sandbox_private_read_only_access(
            policy=SandboxPrivateReadOnlyAccountPolicy(
                required_approval_text=REQUIRED_UAT305_PRIVATE_READ_ONLY_APPROVAL_TEXT,
            ),
            request=SandboxPrivateReadOnlyAccessRequest(
                category=category,
                runtime_policy=runtime_policy,
                approval=approval,
                credential_boundary=credential_boundary,
            ),
        )
        for category in (
            SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
            SandboxPrivateEndpointCategory.SANDBOX_ORDER_CANCEL,
            SandboxPrivateEndpointCategory.SANDBOX_ORDER_AMEND,
            SandboxPrivateEndpointCategory.SANDBOX_ORDER_RETRY,
        )
    }

    feed: SandboxAccountDrawdownFeed | None = None
    status = SandboxDrawdownFeedStatus.MISSING
    if (
        account_state_payload is not None
        and approval_result.allowed
        and env_status.credentials_available
        and env_status.endpoint_sandbox_verified
        and credential_result.allowed
        and account_access_result.allowed
    ):
        snapshot = build_hyperliquid_sandbox_account_snapshot_from_payload(
            payload=account_state_payload,
            sandbox_account_id="configured_sandbox_account",
            observed_at_utc=observed_at_utc,
        )
        feed = build_sandbox_account_drawdown_feed(
            snapshot=snapshot,
            drawdown_threshold=drawdown_threshold,
            status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
        )
        status = SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED

    return UAT305PrivateReadOnlyDrawdownVerificationResult(
        approval_result=approval_result,
        credential_env_status=env_status,
        credential_boundary_result=credential_result,
        account_access_result=account_access_result,
        order_lockout_results=order_lockout_results,
        sandbox_drawdown_feed=feed,
        drawdown_feed_status=status,
        private_endpoint_called=feed is not None,
        order_endpoint_called=False,
        api_keys_used=False,
    )


def validate_sandbox_account_drawdown_feed(
    feed: SandboxAccountDrawdownFeed | None,
    *,
    require_live_fed: bool = True,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if feed is None:
        reasons.append(SandboxDrawdownFeedStatus.MISSING.value)
        return SandboxCheckResult(allowed=False, reason_codes=tuple(reasons))
    if feed.source != "sandbox_account":
        reasons.append(SandboxPrivateReadOnlyRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_SANDBOX_ACCOUNT.value)
    if not feed.not_live_account:
        reasons.append(SandboxPrivateReadOnlyRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_ACCOUNT_FORBIDDEN.value)
    if require_live_fed and feed.status != SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED.value)
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None


@dataclass(frozen=True)
class SandboxSubmitAttemptKey:
    approval_id: str
    uat_run_id: str
    venue: str
    account_id: str
    symbol: str
    component: str
    environment: str

    @property
    def candidate_fingerprint(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.uat_run_id,
            self.venue.lower(),
            self.account_id,
            self.symbol.upper(),
            self.component,
            self.environment.lower(),
        )


@dataclass(frozen=True)
class PriorSandboxSubmitAttempt:
    key: SandboxSubmitAttemptKey
    status: str


@dataclass(frozen=True)
class SandboxSubmitPreflightRequest:
    key: SandboxSubmitAttemptKey
    submit_lease_acquired: bool
    idempotency_key: str
    top20_fanout: bool = False
    route_executor_behavior: bool = False


@dataclass(frozen=True)
class SandboxSubmitPreflightState:
    prior_attempts: tuple[PriorSandboxSubmitAttempt, ...] = ()


def evaluate_sandbox_submit_preflight(
    *,
    request: SandboxSubmitPreflightRequest,
    state: SandboxSubmitPreflightState,
) -> SandboxCheckResult:
    reasons: list[str] = []
    if not request.submit_lease_acquired:
        reasons.append(SandboxSubmitRejectReason.SUBMIT_LEASE_REQUIRED.value)
    if not request.idempotency_key.strip():
        reasons.append(SandboxSubmitRejectReason.IDEMPOTENCY_KEY_REQUIRED.value)
    if not request.key.approval_id.strip():
        reasons.append(SandboxSubmitRejectReason.APPROVAL_ID_REQUIRED.value)
    if not request.key.uat_run_id.strip():
        reasons.append(SandboxSubmitRejectReason.UAT_RUN_ID_REQUIRED.value)
    if request.key.environment.lower() not in SANDBOX_ENVIRONMENTS:
        reasons.append(SandboxSubmitRejectReason.ENVIRONMENT_NOT_SANDBOX.value)
    if request.top20_fanout:
        reasons.append(SandboxSubmitRejectReason.TOP20_FANOUT_FORBIDDEN.value)
    if request.route_executor_behavior:
        reasons.append(SandboxSubmitRejectReason.ROUTE_EXECUTOR_FORBIDDEN.value)

    for prior in state.prior_attempts:
        same_approval_and_candidate = (
            prior.key.approval_id == request.key.approval_id
            and prior.key.candidate_fingerprint == request.key.candidate_fingerprint
        )
        if same_approval_and_candidate:
            reasons.append(SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE.value)
        same_candidate_different_venue = (
            prior.key.approval_id == request.key.approval_id
            and prior.key.uat_run_id == request.key.uat_run_id
            and prior.key.account_id == request.key.account_id
            and prior.key.symbol.upper() == request.key.symbol.upper()
            and prior.key.component == request.key.component
            and prior.key.venue.lower() != request.key.venue.lower()
        )
        if same_candidate_different_venue:
            reasons.append(SandboxSubmitRejectReason.CROSS_VENUE_RETRY_FORBIDDEN.value)
        if prior.status in {"unknown", "uncertain", "adapter_submit_may_have_started", "adapter_submit_persistence_unknown"}:
            reasons.append(SandboxSubmitRejectReason.PRIOR_SUBMIT_UNCERTAIN_BLOCKS_RETRY.value)

    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class UAT3SandboxGateDryRunInput:
    runtime_policy: SandboxRuntimePolicy
    artifact_labels: SandboxArtifactLabels
    approval_scope: SandboxApprovalScope
    approval_candidate: SandboxApprovalCandidate
    risk_limits: SandboxRiskLimits
    risk_request: SandboxRiskRequest
    submit_request: SandboxSubmitPreflightRequest
    submit_state: SandboxSubmitPreflightState
    now_utc: datetime
    sandbox_drawdown_feed: SandboxDrawdownFeedFixture | SandboxAccountDrawdownFeed | None
    founder_operator_actual_submission_approved: bool = False
    drawdown_feed_status: str = "sandbox_drawdown_feed_fixture_only"
    artifact_labels_persistence_enforced: bool = False
    require_live_fed_drawdown: bool = True


@dataclass(frozen=True)
class UAT3SandboxGateDryRunResult:
    allowed: bool
    overall_reason_codes: tuple[str, ...]
    runtime_policy_result: SandboxCheckResult
    artifact_label_result: SandboxCheckResult
    approval_scope_result: SandboxCheckResult
    risk_gate_result: SandboxCheckResult
    drawdown_feed_status: str
    submit_preflight_result: SandboxCheckResult
    would_submit_if_enabled: bool
    creates_order_intent: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False
    calls_exchange: bool = False

    @property
    def blocked(self) -> bool:
        return not self.allowed


def evaluate_uat3_sandbox_submission_preflight(
    preflight: UAT3SandboxGateDryRunInput,
) -> UAT3SandboxGateDryRunResult:
    """Evaluate all future UAT3.1 gates without persisting or calling exchanges."""

    runtime_result = preflight.runtime_policy.evaluate_for_sandbox_submission()
    artifact_result = validate_sandbox_artifact_labels(preflight.artifact_labels)
    approval_result = validate_sandbox_approval_scope(
        scope=preflight.approval_scope,
        candidate=preflight.approval_candidate,
        now_utc=preflight.now_utc,
    )
    risk_result = evaluate_sandbox_risk_gates(
        limits=preflight.risk_limits,
        request=preflight.risk_request,
    )
    submit_result = evaluate_sandbox_submit_preflight(
        request=preflight.submit_request,
        state=preflight.submit_state,
    )

    reasons: list[str] = []
    reasons.extend(runtime_result.reason_codes)
    reasons.extend(artifact_result.reason_codes)
    reasons.extend(approval_result.reason_codes)
    reasons.extend(risk_result.reason_codes)
    reasons.extend(submit_result.reason_codes)

    if not preflight.founder_operator_actual_submission_approved:
        reasons.append(
            SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED.value
        )
    if preflight.sandbox_drawdown_feed is None:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
    if preflight.drawdown_feed_status == SandboxDrawdownFeedStatus.MISSING.value:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
    if preflight.drawdown_feed_status == SandboxDrawdownFeedStatus.FIXTURE_ONLY.value:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY.value)
    if preflight.require_live_fed_drawdown and preflight.drawdown_feed_status != SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED.value)
    if not preflight.artifact_labels_persistence_enforced:
        reasons.append(
            SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_PERSISTENCE.value
        )

    unique_reasons = tuple(dict.fromkeys(reasons))
    allowed = not unique_reasons
    return UAT3SandboxGateDryRunResult(
        allowed=allowed,
        overall_reason_codes=unique_reasons,
        runtime_policy_result=runtime_result,
        artifact_label_result=artifact_result,
        approval_scope_result=approval_result,
        risk_gate_result=risk_result,
        drawdown_feed_status=preflight.drawdown_feed_status,
        submit_preflight_result=submit_result,
        would_submit_if_enabled=allowed,
    )


@dataclass(frozen=True)
class UAT3SandboxExecutableGateDryRunInput:
    runtime_policy: SandboxRuntimePolicy
    artifact_labels: SandboxArtifactLabels
    approval_scope: SandboxApprovalScope
    approval_candidate: SandboxApprovalCandidate
    risk_limits: SandboxRiskLimits
    risk_request: SandboxRiskRequest
    submit_request: SandboxSubmitPreflightRequest
    submit_state: SandboxSubmitPreflightState
    now_utc: datetime
    sandbox_drawdown_feed: SandboxDrawdownFeedFixture | SandboxAccountDrawdownFeed | None
    founder_operator_actual_submission_approved: bool = False
    drawdown_feed_status: str = "sandbox_drawdown_feed_fixture_only"
    artifact_boundary_enforcement: tuple[SandboxArtifactBoundary, ...] = (
        SandboxArtifactBoundary.PERSISTENCE,
        SandboxArtifactBoundary.API_SERIALIZATION,
        SandboxArtifactBoundary.DASHBOARD_DISPLAY,
        SandboxArtifactBoundary.REPORT_GENERATION,
    )
    real_sandbox_submit_path_wired: bool = False


@dataclass(frozen=True)
class UAT3SandboxExecutableGateDryRunResult:
    allowed: bool
    reason_codes: tuple[str, ...]
    gate_results: dict[str, object]
    runtime_policy_result: SandboxCheckResult
    artifact_boundary_results: tuple[SandboxArtifactBoundaryValidation, ...]
    approval_scope_result: SandboxCheckResult
    risk_gate_result: SandboxCheckResult
    drawdown_feed_status: str
    submit_preflight_result: SandboxCheckResult
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False
    calls_exchange: bool = False
    would_require_founder_approval: bool = True
    would_require_live_fed_sandbox_drawdown: bool = True
    would_require_real_sandbox_submit_path: bool = True

    @property
    def blocked(self) -> bool:
        return not self.allowed


class UAT3SandboxDryRunGateService:
    """Composes future executable UAT3 sandbox gates without side effects."""

    def evaluate(self, preflight: UAT3SandboxExecutableGateDryRunInput) -> UAT3SandboxExecutableGateDryRunResult:
        runtime_result = preflight.runtime_policy.evaluate_for_sandbox_submission()
        boundary_results = validate_sandbox_artifact_boundaries(
            labels=preflight.artifact_labels,
            boundaries=preflight.artifact_boundary_enforcement,
        )
        approval_result = validate_sandbox_approval_scope(
            scope=preflight.approval_scope,
            candidate=preflight.approval_candidate,
            now_utc=preflight.now_utc,
        )
        risk_result = evaluate_sandbox_risk_gates(
            limits=preflight.risk_limits,
            request=preflight.risk_request,
        )
        submit_result = evaluate_sandbox_submit_preflight(
            request=preflight.submit_request,
            state=preflight.submit_state,
        )

        reasons: list[str] = []
        reasons.extend(runtime_result.reason_codes)
        for boundary_result in boundary_results:
            reasons.extend(boundary_result.result.reason_codes)
        reasons.extend(approval_result.reason_codes)
        reasons.extend(risk_result.reason_codes)
        reasons.extend(submit_result.reason_codes)

        if not preflight.founder_operator_actual_submission_approved:
            reasons.append(
                SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED.value
            )
        if preflight.sandbox_drawdown_feed is None:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
        if preflight.drawdown_feed_status == SandboxDrawdownFeedStatus.MISSING.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
        if preflight.drawdown_feed_status == SandboxDrawdownFeedStatus.FIXTURE_ONLY.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY.value)
        if preflight.drawdown_feed_status != SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_LIVE_FED_REQUIRED.value)
        if not preflight.real_sandbox_submit_path_wired:
            reasons.append(SandboxDryRunRejectReason.REAL_SANDBOX_SUBMIT_PATH_REQUIRED.value)

        enforced_boundaries = set(preflight.artifact_boundary_enforcement)
        boundary_missing_reasons = {
            SandboxArtifactBoundary.PERSISTENCE: (
                SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_PERSISTENCE.value
            ),
            SandboxArtifactBoundary.API_SERIALIZATION: (
                SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_API_SERIALIZATION.value
            ),
            SandboxArtifactBoundary.DASHBOARD_DISPLAY: (
                SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_DASHBOARD_DISPLAY.value
            ),
            SandboxArtifactBoundary.REPORT_GENERATION: (
                SandboxDryRunRejectReason.SANDBOX_ARTIFACT_LABELING_NOT_ENFORCED_ON_REPORT_GENERATION.value
            ),
        }
        for boundary, reason in boundary_missing_reasons.items():
            if boundary not in enforced_boundaries:
                reasons.append(reason)

        unique_reasons = tuple(dict.fromkeys(reasons))
        allowed = not unique_reasons
        gate_results: dict[str, object] = {
            "runtime_policy": runtime_result,
            "artifact_boundaries": boundary_results,
            "approval_scope": approval_result,
            "risk_gate": risk_result,
            "drawdown_feed_status": preflight.drawdown_feed_status,
            "submit_preflight": submit_result,
            "runtime_policy_semantics": get_sandbox_runtime_policy_semantics(),
        }
        return UAT3SandboxExecutableGateDryRunResult(
            allowed=allowed,
            reason_codes=unique_reasons,
            gate_results=gate_results,
            runtime_policy_result=runtime_result,
            artifact_boundary_results=boundary_results,
            approval_scope_result=approval_result,
            risk_gate_result=risk_result,
            drawdown_feed_status=preflight.drawdown_feed_status,
            submit_preflight_result=submit_result,
            would_require_founder_approval=not preflight.founder_operator_actual_submission_approved,
            would_require_live_fed_sandbox_drawdown=(
                preflight.drawdown_feed_status != SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value
            ),
            would_require_real_sandbox_submit_path=not preflight.real_sandbox_submit_path_wired,
        )


def evaluate_uat3_sandbox_executable_gate_dry_run(
    preflight: UAT3SandboxExecutableGateDryRunInput,
) -> UAT3SandboxExecutableGateDryRunResult:
    return UAT3SandboxDryRunGateService().evaluate(preflight)


@dataclass(frozen=True)
class SandboxAdapterEndpointClassification:
    endpoint_category: SandboxPrivateEndpointCategory
    transport_invoked: bool = False
    calls_exchange: bool = False


def evaluate_uat306_sandbox_order_endpoint_classification(
    classification: SandboxAdapterEndpointClassification,
) -> SandboxCheckResult:
    """Classify the future sandbox order endpoint without invoking transport."""

    reasons: list[str] = []
    if classification.endpoint_category == SandboxPrivateEndpointCategory.UNKNOWN:
        reasons.append(SandboxDryRunRejectReason.ENDPOINT_CATEGORY_UNKNOWN.value)
    if classification.endpoint_category != SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION:
        reasons.append(
            SandboxDryRunRejectReason.ENDPOINT_CATEGORY_NOT_SANDBOX_ORDER_SUBMISSION.value
        )
    if classification.transport_invoked or classification.calls_exchange:
        reasons.append(
            SandboxDryRunRejectReason.SANDBOX_ORDER_ENDPOINT_TRANSPORT_FORBIDDEN_IN_UAT306.value
        )
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class UAT3SandboxSubmissionPlan:
    """Non-persistent UAT3.0.6 sandbox submit dry-run plan.

    This object is a review/check artifact only. It is not an OrderIntent,
    PreparedVenueOrder, SubmittedOrder, executable approval, or adapter request.
    """

    uat_run_id: str
    venue: str
    environment: str
    account_id: str
    symbol: str
    component: str
    candidate_id: str
    order_side: str
    order_type: str
    requested_notional_or_quantity: Decimal
    max_notional_or_quantity: Decimal
    approval_id: str
    idempotency_key: str
    submit_lease_key: str
    sandbox_labels: SandboxArtifactLabels
    runtime_policy_snapshot: SandboxRuntimePolicy
    drawdown_feed_status: str
    risk_gate_result: SandboxCheckResult
    approval_scope_result: SandboxCheckResult
    submit_lease_result: SandboxCheckResult
    artifact_label_result: SandboxCheckResult
    endpoint_category: SandboxPrivateEndpointCategory = (
        SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION
    )
    endpoint_transport_invoked: bool = False
    would_submit_if_enabled: bool = False
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False
    calls_exchange: bool = False

    @property
    def submit_path_key(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.uat_run_id,
            self.venue.lower(),
            self.account_id,
            self.symbol.upper(),
            self.component,
            self.environment.lower(),
        )


@dataclass(frozen=True)
class UAT3SandboxSubmitPathDryRunInput:
    runtime_policy: SandboxRuntimePolicy
    artifact_labels: SandboxArtifactLabels
    approval_scope: SandboxApprovalScope
    approval_candidate: SandboxApprovalCandidate
    risk_limits: SandboxRiskLimits
    risk_request: SandboxRiskRequest
    submit_request: SandboxSubmitPreflightRequest
    submit_state: SandboxSubmitPreflightState
    now_utc: datetime
    sandbox_drawdown_feed: SandboxAccountDrawdownFeed | None
    endpoint_classification: SandboxAdapterEndpointClassification
    candidate_id: str = "money_flow_hyperliquid_eth_1h_baseline_uat_candidate"
    order_side: str = "buy"
    order_type: str = "market"
    founder_operator_actual_submission_approved: bool = False
    drawdown_feed_status: str = SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value
    drawdown_feed_max_age_seconds: int = 900


@dataclass(frozen=True)
class UAT3SandboxSubmitPathDryRunResult:
    allowed_for_future_submit: bool
    blocked: bool
    reason_codes: tuple[str, ...]
    gate_results: dict[str, object]
    submission_plan: UAT3SandboxSubmissionPlan
    runtime_policy_result: SandboxCheckResult
    approval_requirement_result: SandboxCheckResult
    artifact_boundary_results: tuple[SandboxArtifactBoundaryValidation, ...]
    approval_scope_result: SandboxCheckResult
    drawdown_feed_result: SandboxCheckResult
    risk_gate_result: SandboxCheckResult
    submit_preflight_result: SandboxCheckResult
    endpoint_classification_result: SandboxCheckResult
    would_call_exchange: bool = False
    would_create_order_intent: bool = False
    would_create_prepared_order: bool = False
    would_create_submitted_order: bool = False
    would_create_executable_approval: bool = False
    would_submit_if_enabled: bool = False


class UAT3SandboxSubmitDryRunService:
    """Dry-run-only future sandbox submit-path gate chain.

    The service intentionally returns side-effect flags as false. It composes
    gates in the same order a later UAT3.1 submit path must respect, but it
    never persists artifacts, creates approvals, invokes adapters, or submits.
    """

    def evaluate(
        self,
        dry_run_input: UAT3SandboxSubmitPathDryRunInput,
    ) -> UAT3SandboxSubmitPathDryRunResult:
        runtime_result = dry_run_input.runtime_policy.evaluate_for_sandbox_submission()
        approval_requirement_result = SandboxCheckResult(
            allowed=dry_run_input.founder_operator_actual_submission_approved,
            reason_codes=()
            if dry_run_input.founder_operator_actual_submission_approved
            else (
                SandboxDryRunRejectReason.FOUNDER_OPERATOR_ACTUAL_SANDBOX_SUBMISSION_APPROVAL_REQUIRED.value,
            ),
        )
        boundary_results = validate_sandbox_artifact_boundaries(
            labels=dry_run_input.artifact_labels,
        )
        approval_scope_result = validate_sandbox_approval_scope(
            scope=dry_run_input.approval_scope,
            candidate=dry_run_input.approval_candidate,
            now_utc=dry_run_input.now_utc,
        )
        drawdown_feed_result = self._evaluate_drawdown_feed(dry_run_input)
        risk_gate_result = evaluate_sandbox_risk_gates(
            limits=dry_run_input.risk_limits,
            request=dry_run_input.risk_request,
        )
        submit_preflight_result = evaluate_sandbox_submit_preflight(
            request=dry_run_input.submit_request,
            state=dry_run_input.submit_state,
        )
        endpoint_result = evaluate_uat306_sandbox_order_endpoint_classification(
            dry_run_input.endpoint_classification,
        )

        reasons: list[str] = []
        reasons.extend(runtime_result.reason_codes)
        reasons.extend(approval_requirement_result.reason_codes)
        for boundary_result in boundary_results:
            reasons.extend(boundary_result.result.reason_codes)
        reasons.extend(approval_scope_result.reason_codes)
        reasons.extend(drawdown_feed_result.reason_codes)
        reasons.extend(risk_gate_result.reason_codes)
        reasons.extend(submit_preflight_result.reason_codes)
        reasons.extend(endpoint_result.reason_codes)
        unique_reasons = tuple(dict.fromkeys(reasons))

        artifact_result = validate_sandbox_artifact_labels(dry_run_input.artifact_labels)
        plan = UAT3SandboxSubmissionPlan(
            uat_run_id=dry_run_input.approval_candidate.uat_run_id,
            venue=dry_run_input.approval_candidate.venue,
            environment=dry_run_input.approval_candidate.environment,
            account_id=dry_run_input.approval_candidate.account_id,
            symbol=dry_run_input.approval_candidate.symbol,
            component=dry_run_input.approval_candidate.component,
            candidate_id=dry_run_input.candidate_id,
            order_side=dry_run_input.order_side,
            order_type=dry_run_input.order_type,
            requested_notional_or_quantity=dry_run_input.approval_candidate.requested_notional_or_quantity,
            max_notional_or_quantity=dry_run_input.approval_scope.max_notional_or_quantity,
            approval_id=dry_run_input.approval_scope.approval_id,
            idempotency_key=dry_run_input.submit_request.idempotency_key,
            submit_lease_key=":".join(dry_run_input.submit_request.key.candidate_fingerprint),
            sandbox_labels=dry_run_input.artifact_labels,
            runtime_policy_snapshot=dry_run_input.runtime_policy,
            drawdown_feed_status=dry_run_input.drawdown_feed_status,
            risk_gate_result=risk_gate_result,
            approval_scope_result=approval_scope_result,
            submit_lease_result=submit_preflight_result,
            artifact_label_result=artifact_result,
            endpoint_category=dry_run_input.endpoint_classification.endpoint_category,
            endpoint_transport_invoked=dry_run_input.endpoint_classification.transport_invoked,
        )

        allowed_for_future_submit = not unique_reasons
        gate_results: dict[str, object] = {
            "runtime_policy": runtime_result,
            "founder_actual_submission_approval": approval_requirement_result,
            "artifact_boundaries": boundary_results,
            "approval_scope": approval_scope_result,
            "drawdown_feed": drawdown_feed_result,
            "risk_gate": risk_gate_result,
            "submit_preflight": submit_preflight_result,
            "endpoint_classification": endpoint_result,
            "runtime_policy_semantics": get_sandbox_runtime_policy_semantics(),
        }
        return UAT3SandboxSubmitPathDryRunResult(
            allowed_for_future_submit=allowed_for_future_submit,
            blocked=not allowed_for_future_submit,
            reason_codes=unique_reasons,
            gate_results=gate_results,
            submission_plan=plan,
            runtime_policy_result=runtime_result,
            approval_requirement_result=approval_requirement_result,
            artifact_boundary_results=boundary_results,
            approval_scope_result=approval_scope_result,
            drawdown_feed_result=drawdown_feed_result,
            risk_gate_result=risk_gate_result,
            submit_preflight_result=submit_preflight_result,
            endpoint_classification_result=endpoint_result,
        )

    def _evaluate_drawdown_feed(
        self,
        dry_run_input: UAT3SandboxSubmitPathDryRunInput,
    ) -> SandboxCheckResult:
        reasons: list[str] = []
        feed = dry_run_input.sandbox_drawdown_feed
        if feed is None:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
            return SandboxCheckResult(allowed=False, reason_codes=tuple(reasons))

        if dry_run_input.drawdown_feed_status == SandboxDrawdownFeedStatus.MISSING.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_MISSING.value)
        if dry_run_input.drawdown_feed_status == SandboxDrawdownFeedStatus.FIXTURE_ONLY.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY.value)
        if dry_run_input.drawdown_feed_status != SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_LIVE_FED_VERIFIED.value)
        reasons.extend(validate_sandbox_account_drawdown_feed(feed, require_live_fed=True).reason_codes)
        if not feed.not_live_account:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_NOT_LABELED_NOT_LIVE_ACCOUNT.value)
        if feed.threshold_breached:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_THRESHOLD_BREACHED.value)

        age_seconds = (_as_aware_utc(dry_run_input.now_utc) - _as_aware_utc(feed.timestamp_utc)).total_seconds()
        if age_seconds < 0 or age_seconds > dry_run_input.drawdown_feed_max_age_seconds:
            reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_STALE.value)
        return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


def evaluate_uat3_sandbox_submit_path_dry_run(
    dry_run_input: UAT3SandboxSubmitPathDryRunInput,
) -> UAT3SandboxSubmitPathDryRunResult:
    return UAT3SandboxSubmitDryRunService().evaluate(dry_run_input)
