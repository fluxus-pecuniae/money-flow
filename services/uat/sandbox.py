"""UAT3 sandbox-order readiness primitives.

These helpers are fixture/test-only safety gates for future UAT3.1 design.
They do not submit orders, call exchange endpoints, persist trading artifacts,
or create executable approvals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


SANDBOX_RUNTIME_MODES: tuple[str, ...] = ("sandbox", "uat_sandbox")
SANDBOX_ENVIRONMENTS: tuple[str, ...] = ("sandbox", "testnet", "uat_sandbox")
RUNTIME_POLICY_RISK_REASON_PREFIX = "runtime_policy_"


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


@dataclass(frozen=True)
class SandboxCheckResult:
    allowed: bool
    reason_codes: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return not self.allowed


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
    sandbox_drawdown_feed: SandboxDrawdownFeedFixture | None
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
    if preflight.drawdown_feed_status == SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY.value:
        reasons.append(SandboxDryRunRejectReason.SANDBOX_DRAWDOWN_FEED_FIXTURE_ONLY.value)
    if preflight.require_live_fed_drawdown and preflight.drawdown_feed_status != "sandbox_drawdown_feed_live_fed_verified":
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
