"""UAT3.1 one-shot sandbox/testnet order lifecycle probe.

This module is intentionally separate from production execution models. It
supports one founder-approved Hyperliquid testnet lifecycle probe and does not
create OrderIntent, PreparedVenueOrder, SubmittedOrder, executable approvals,
paper-trading, or live-trading artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import time
from typing import Any, Protocol

import httpx

from core.security import redact_sensitive_structure, redact_sensitive_text
from services.exchange.hyperliquid.signing import float_to_wire, sign_l1_action, signer_address
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    SandboxAccountDrawdownFeed,
    SandboxAccountStateSnapshot,
    SandboxAdapterEndpointClassification,
    SandboxApprovalCandidate,
    SandboxApprovalScope,
    SandboxArtifactLabels,
    SandboxCheckResult,
    SandboxDrawdownFeedStatus,
    SandboxPrivateEndpointCategory,
    SandboxRiskLimits,
    SandboxRiskRequest,
    SandboxRuntimePolicy,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    UAT3SandboxSubmitPathDryRunInput,
    build_hyperliquid_sandbox_account_snapshot_from_payload,
    build_sandbox_account_drawdown_feed,
    evaluate_uat3_sandbox_submit_path_dry_run,
    load_hyperliquid_uat_sandbox_credential_env_status,
    validate_sandbox_testnet_base_url,
)


REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT = """FOUNDER / OPERATOR APPROVAL — UAT3.1 FIRST SANDBOX ORDER ATTEMPT

I approve one approval-gated sandbox/testnet order submission attempt under the exact scope below.

Approved scope:
- Venue: Hyperliquid testnet / sandbox only
- Symbol: ETH USDC perpetual
- Purpose: sandbox lifecycle plumbing validation only
- Strategy status: not a Money Flow performance test
- Order source: manual sandbox lifecycle probe, not an approved strategy signal
- Maximum order count: 1 order attempt
- Order type: non-marketable limit order or post-only limit order if supported
- Side: buy/open only if it can be placed safely as non-marketable; otherwise block
- Maximum notional: use the minimum practical testnet notional, capped at 10 USDC equivalent
- Expected lifecycle: submit -> accepted/open or rejected -> cancel if open -> reconcile
- If unexpectedly filled: stop, report immediately, and do not place any additional order without a separate approval
- Environment: sandbox/testnet only
- Live endpoint access: not approved
- Paper trading: not approved
- Live trading: not approved
- Broad top-20 order submission: not approved
- Repeated orders: not approved
- Auto-submit: not approved

Required gates:
- sandbox runtime policy must pass
- live-fed sandbox drawdown must be available
- approval scope must match this approval exactly
- sandbox risk gates must pass
- submit lease / duplicate prevention must pass
- sandbox artifact labels must be enforced
- no live endpoint may be reachable
- all secrets must remain redacted

This approval does not authorize paper trading, live trading, production auto-submit, real-capital trading, or additional sandbox orders."""

UAT31_RUN_ID = "uat3_1_first_sandbox_order_attempt"
UAT31_APPROVAL_ID = "uat3_1_founder_actual_sandbox_submission_approval"
UAT31_COMPONENT = "manual_sandbox_lifecycle_probe"
UAT31_CANDIDATE_ID = "manual_sandbox_lifecycle_probe_eth_testnet"
UAT31_MAX_NOTIONAL = Decimal("10")
UAT31_DRAWDOWN_THRESHOLD = Decimal("0.05")


class UAT31RejectReason:
    APPROVAL_REQUIRED = "founder_operator_actual_sandbox_submission_approval_required"
    SANDBOX_ENDPOINT_REQUIRED = "sandbox_testnet_endpoint_required"
    LIVE_ENDPOINT_FORBIDDEN = "live_endpoint_forbidden"
    CREDENTIALS_MISSING = "sandbox_credentials_missing"
    PRIOR_ATTEMPT_EXISTS = "uat31_prior_order_attempt_exists"
    NON_MARKETABLE_LIMIT_REQUIRED = "non_marketable_limit_required"
    POST_ONLY_REQUIRED = "post_only_limit_required"
    ETH_MARKET_METADATA_MISSING = "eth_market_metadata_missing"
    PUBLIC_ORDER_BOOK_MISSING = "public_order_book_missing"
    QUANTITY_NOT_POSITIVE = "sandbox_positive_quantity_required"
    GATES_BLOCKED = "uat31_gate_chain_blocked"
    ORDER_TRANSPORT_FAILED = "sandbox_order_transport_failed"
    CANCEL_TRANSPORT_FAILED = "sandbox_cancel_transport_failed"
    UNEXPECTED_FILL = "unexpected_fill_stop_no_additional_order"
    OPEN_ORDER_REMAINS = "open_order_remains_manual_cleanup_required"


@dataclass(frozen=True)
class UAT31ManualProbeLabels:
    base: SandboxArtifactLabels
    manual_sandbox_lifecycle_probe: bool = True
    not_strategy_signal: bool = True
    not_performance_validation: bool = True


@dataclass(frozen=True)
class UAT31MarketPlan:
    asset_id: int
    symbol: str
    sz_decimals: int
    best_bid: Decimal
    best_ask: Decimal
    limit_price: Decimal
    quantity: Decimal
    estimated_notional: Decimal
    tif: str
    cloid: str


@dataclass(frozen=True)
class UAT31TransportResponse:
    path: str
    payload_type: str
    status: str
    body: Any


@dataclass(frozen=True)
class UAT31LifecycleResult:
    order_attempt_count: int
    order_endpoint_called: bool
    cancel_endpoint_called: bool
    order_status: str
    exchange_order_id: str | None
    client_order_id: str | None
    cancel_status: str
    reconciliation_status: str
    unexpected_fill: bool
    open_order_remains: bool
    unknown_state: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class UAT31FirstSandboxOrderAttemptResult:
    allowed_to_submit: bool
    blocked: bool
    reason_codes: tuple[str, ...]
    approval_result: SandboxCheckResult
    credential_status: Any | None
    runtime_policy_result: SandboxCheckResult | None
    gate_result: Any | None
    drawdown_feed: SandboxAccountDrawdownFeed | None
    market_plan: UAT31MarketPlan | None
    lifecycle: UAT31LifecycleResult
    sanitized_order_request: Mapping[str, Any]
    sanitized_order_response: Mapping[str, Any]
    sanitized_cancel_response: Mapping[str, Any]
    sanitized_reconciliation: Mapping[str, Any]
    creates_order_intent: bool = False
    creates_prepared_order: bool = False
    creates_submitted_order: bool = False
    creates_executable_approval: bool = False
    paper_trading_added: bool = False
    live_trading_added: bool = False


class UAT31Transport(Protocol):
    async def post_json(self, path: str, payload: Mapping[str, Any]) -> Any: ...


class HyperliquidUAT31HTTPTransport:
    """Minimal path-scoped Hyperliquid testnet transport for UAT3.1 only."""

    def __init__(self, *, base_url: str, timeout_seconds: float = 20.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def post_json(self, path: str, payload: Mapping[str, Any]) -> Any:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout_seconds) as client:
            response = await client.post(path, json=dict(payload))
            response.raise_for_status()
            return response.json()


def validate_uat31_actual_submission_approval_text(approval_text: str) -> SandboxCheckResult:
    normalized = approval_text.replace("\r\n", "\n").strip()
    required = REQUIRED_UAT31_ACTUAL_SUBMISSION_APPROVAL_TEXT.strip()
    allowed = required in normalized
    return SandboxCheckResult(
        allowed=allowed,
        reason_codes=() if allowed else (UAT31RejectReason.APPROVAL_REQUIRED,),
    )


def validate_uat31_manual_probe_labels(labels: UAT31ManualProbeLabels) -> SandboxCheckResult:
    reasons = list(_label_result(labels.base).reason_codes)
    if not labels.manual_sandbox_lifecycle_probe:
        reasons.append("manual_sandbox_lifecycle_probe_label_missing_or_false")
    if not labels.not_strategy_signal:
        reasons.append("not_strategy_signal_label_missing_or_false")
    if not labels.not_performance_validation:
        reasons.append("not_performance_validation_label_missing_or_false")
    return SandboxCheckResult(allowed=not reasons, reason_codes=tuple(dict.fromkeys(reasons)))


def _label_result(labels: SandboxArtifactLabels) -> SandboxCheckResult:
    from services.uat.sandbox import validate_sandbox_artifact_labels

    return validate_sandbox_artifact_labels(labels)


def build_uat31_runtime_policy() -> SandboxRuntimePolicy:
    return SandboxRuntimePolicy(
        runtime_mode="uat_sandbox",
        live_trading_enabled=False,
        paper_trading_enabled=False,
        exchange_order_submission_enabled=False,
        sandbox_order_submission_enabled=True,
        private_exchange_endpoints_enabled=True,
        live_endpoint_access=False,
        api_keys_required=True,
        sandbox_only=True,
    )


def build_uat31_artifact_labels() -> UAT31ManualProbeLabels:
    return UAT31ManualProbeLabels(
        base=SandboxArtifactLabels(
            sandbox=True,
            testnet=True,
            not_live=True,
            not_paper=True,
            uat_run_id=UAT31_RUN_ID,
            sandbox_order=True,
            live_endpoint_access=False,
            real_capital=False,
        )
    )


def build_uat31_idempotency_key(*, account_id: str, observed_at_utc: datetime) -> str:
    seed = f"{UAT31_RUN_ID}:{UAT31_APPROVAL_ID}:hyperliquid:{account_id}:ETH:{observed_at_utc.isoformat()}"
    return "0x" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def build_uat31_market_plan(
    *,
    meta_payload: Mapping[str, Any],
    l2_book_payload: Mapping[str, Any],
    max_notional: Decimal,
    cloid: str,
) -> tuple[UAT31MarketPlan | None, tuple[str, ...]]:
    universe = meta_payload.get("universe")
    if not isinstance(universe, list):
        return None, (UAT31RejectReason.ETH_MARKET_METADATA_MISSING,)
    asset_id: int | None = None
    sz_decimals: int | None = None
    for index, asset in enumerate(universe):
        if isinstance(asset, Mapping) and str(asset.get("name", "")).upper() == "ETH":
            asset_id = index
            sz_decimals = int(asset.get("szDecimals", 4))
            break
    if asset_id is None or sz_decimals is None:
        return None, (UAT31RejectReason.ETH_MARKET_METADATA_MISSING,)

    levels = l2_book_payload.get("levels")
    if not isinstance(levels, list) or len(levels) < 2:
        return None, (UAT31RejectReason.PUBLIC_ORDER_BOOK_MISSING,)
    bids = levels[0] if isinstance(levels[0], list) else []
    asks = levels[1] if isinstance(levels[1], list) else []
    if not bids or not asks or not isinstance(bids[0], Mapping) or not isinstance(asks[0], Mapping):
        return None, (UAT31RejectReason.PUBLIC_ORDER_BOOK_MISSING,)

    best_bid = Decimal(str(bids[0].get("px")))
    best_ask = Decimal(str(asks[0].get("px")))
    price_tick = Decimal("1").scaleb(-(6 - sz_decimals))
    limit_price = best_bid - price_tick
    if limit_price <= 0 or limit_price >= best_ask:
        return None, (UAT31RejectReason.NON_MARKETABLE_LIMIT_REQUIRED,)

    quantity_step = Decimal("1").scaleb(-sz_decimals)
    quantity = ((max_notional / limit_price) // quantity_step) * quantity_step
    if quantity <= 0:
        return None, (UAT31RejectReason.QUANTITY_NOT_POSITIVE,)
    estimated_notional = quantity * limit_price
    if estimated_notional > max_notional:
        quantity = (((max_notional / limit_price) - quantity_step) // quantity_step) * quantity_step
        estimated_notional = quantity * limit_price
    if quantity <= 0 or estimated_notional <= 0:
        return None, (UAT31RejectReason.QUANTITY_NOT_POSITIVE,)

    return (
        UAT31MarketPlan(
            asset_id=asset_id,
            symbol="ETH",
            sz_decimals=sz_decimals,
            best_bid=best_bid,
            best_ask=best_ask,
            limit_price=limit_price,
            quantity=quantity,
            estimated_notional=estimated_notional,
            tif="Alo",
            cloid=cloid,
        ),
        (),
    )


class UAT31FirstSandboxOrderAttemptService:
    def __init__(self, *, transport: UAT31Transport) -> None:
        self._transport = transport

    async def execute(
        self,
        *,
        approval_text: str,
        env: Mapping[str, str | None],
        prior_attempt_exists: bool,
        now_utc: datetime | None = None,
    ) -> UAT31FirstSandboxOrderAttemptResult:
        now = now_utc or datetime.now(tz=UTC)
        approval_result = validate_uat31_actual_submission_approval_text(approval_text)
        empty_lifecycle = UAT31LifecycleResult(
            order_attempt_count=0,
            order_endpoint_called=False,
            cancel_endpoint_called=False,
            order_status="blocked",
            exchange_order_id=None,
            client_order_id=None,
            cancel_status="not_attempted",
            reconciliation_status="not_attempted",
            unexpected_fill=False,
            open_order_remains=False,
            unknown_state=False,
            reason_codes=approval_result.reason_codes,
        )
        if not approval_result.allowed:
            return self._blocked_result(approval_result, empty_lifecycle, approval_result.reason_codes)

        credential_status = load_hyperliquid_uat_sandbox_credential_env_status(env)
        endpoint_result = validate_sandbox_testnet_base_url(credential_status.base_url)
        reasons: list[str] = list(credential_status.reason_codes) + list(endpoint_result.reason_codes)
        if not credential_status.credentials_available:
            reasons.append(UAT31RejectReason.CREDENTIALS_MISSING)
        if not credential_status.endpoint_sandbox_verified or not endpoint_result.allowed:
            reasons.append(UAT31RejectReason.SANDBOX_ENDPOINT_REQUIRED)
        if prior_attempt_exists:
            reasons.append(UAT31RejectReason.PRIOR_ATTEMPT_EXISTS)
        if reasons:
            return self._blocked_result(
                approval_result,
                empty_lifecycle,
                tuple(dict.fromkeys(reasons)),
                credential_status=credential_status,
            )

        account_id = str(env[HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV] or "").strip()
        private_key = str(env[HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV] or "").strip()
        cloid = build_uat31_idempotency_key(account_id=account_id, observed_at_utc=now)

        meta_payload = await self._transport.post_json("/info", {"type": "meta"})
        l2_payload = await self._transport.post_json("/info", {"type": "l2Book", "coin": "ETH"})
        market_plan, market_reasons = build_uat31_market_plan(
            meta_payload=meta_payload,
            l2_book_payload=l2_payload,
            max_notional=UAT31_MAX_NOTIONAL,
            cloid=cloid,
        )
        if market_plan is None:
            return self._blocked_result(
                approval_result,
                empty_lifecycle,
                market_reasons,
                credential_status=credential_status,
            )

        account_state = await self._transport.post_json(
            "/info",
            {"type": "clearinghouseState", "user": account_id},
        )
        snapshot = build_hyperliquid_sandbox_account_snapshot_from_payload(
            payload=account_state if isinstance(account_state, Mapping) else {},
            sandbox_account_id=account_id,
            observed_at_utc=now,
        )
        drawdown_feed = build_sandbox_account_drawdown_feed(
            snapshot=snapshot,
            drawdown_threshold=UAT31_DRAWDOWN_THRESHOLD,
            status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
        )

        runtime_policy = build_uat31_runtime_policy()
        labels = build_uat31_artifact_labels()
        label_result = validate_uat31_manual_probe_labels(labels)
        approval_scope = SandboxApprovalScope(
            approval_id=UAT31_APPROVAL_ID,
            uat_run_id=UAT31_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT31_COMPONENT,
            max_notional_or_quantity=UAT31_MAX_NOTIONAL,
            expires_at_utc=now + timedelta(minutes=30),
            environment="testnet",
        )
        approval_candidate = SandboxApprovalCandidate(
            uat_run_id=UAT31_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT31_COMPONENT,
            requested_notional_or_quantity=market_plan.estimated_notional,
            environment="testnet",
        )
        submit_key = SandboxSubmitAttemptKey(
            approval_id=UAT31_APPROVAL_ID,
            uat_run_id=UAT31_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT31_COMPONENT,
            environment="testnet",
        )
        dry_run = evaluate_uat3_sandbox_submit_path_dry_run(
            UAT3SandboxSubmitPathDryRunInput(
                runtime_policy=runtime_policy,
                artifact_labels=labels.base,
                approval_scope=approval_scope,
                approval_candidate=approval_candidate,
                risk_limits=SandboxRiskLimits(
                    max_sandbox_notional=UAT31_MAX_NOTIONAL,
                    max_sandbox_order_count=1,
                    max_daily_sandbox_order_count=1,
                    max_sandbox_drawdown_pct=UAT31_DRAWDOWN_THRESHOLD,
                    allowed_symbols=("ETH",),
                    allowed_venue_accounts=(account_id,),
                    allowed_venues=("hyperliquid",),
                ),
                risk_request=SandboxRiskRequest(
                    venue="hyperliquid",
                    account_id=account_id,
                    symbol="ETH",
                    notional=market_plan.estimated_notional,
                    current_order_count=0,
                    current_daily_order_count=0,
                    sandbox_drawdown_pct=drawdown_feed.max_drawdown_percent or Decimal("0"),
                    live_account=False,
                    live_endpoint_access=False,
                    kill_switch_enabled=False,
                    runtime_policy=runtime_policy,
                ),
                submit_request=SandboxSubmitPreflightRequest(
                    key=submit_key,
                    submit_lease_acquired=True,
                    idempotency_key=cloid,
                    top20_fanout=False,
                    route_executor_behavior=False,
                ),
                submit_state=SandboxSubmitPreflightState(),
                now_utc=now,
                sandbox_drawdown_feed=drawdown_feed,
                endpoint_classification=SandboxAdapterEndpointClassification(
                    endpoint_category=SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
                    transport_invoked=False,
                    calls_exchange=False,
                ),
                candidate_id=UAT31_CANDIDATE_ID,
                order_side="buy",
                order_type="post_only_limit",
                founder_operator_actual_submission_approved=True,
                drawdown_feed_status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value,
            )
        )
        gate_reasons = list(dry_run.reason_codes) + list(label_result.reason_codes)
        if gate_reasons:
            lifecycle = UAT31LifecycleResult(
                **{**asdict(empty_lifecycle), "reason_codes": tuple(dict.fromkeys(gate_reasons))}
            )
            return self._blocked_result(
                approval_result,
                lifecycle,
                tuple(dict.fromkeys([UAT31RejectReason.GATES_BLOCKED, *gate_reasons])),
                credential_status=credential_status,
                runtime_policy_result=dry_run.runtime_policy_result,
                gate_result=dry_run,
                drawdown_feed=drawdown_feed,
                market_plan=market_plan,
            )

        order_action = self._order_action(market_plan)
        order_payload = self._signed_payload(
            action=order_action,
            private_key=private_key,
            account_id=account_id,
            is_mainnet=False,
        )
        order_response: Any
        try:
            order_response = await self._transport.post_json("/exchange", order_payload)
        except Exception as exc:  # noqa: BLE001
            lifecycle = UAT31LifecycleResult(
                order_attempt_count=1,
                order_endpoint_called=True,
                cancel_endpoint_called=False,
                order_status="unknown",
                exchange_order_id=None,
                client_order_id=market_plan.cloid,
                cancel_status="not_attempted",
                reconciliation_status="not_attempted",
                unexpected_fill=False,
                open_order_remains=False,
                unknown_state=True,
                reason_codes=(UAT31RejectReason.ORDER_TRANSPORT_FAILED, redact_sensitive_text(str(exc))),
            )
            return self._result(
                allowed_to_submit=True,
                approval_result=approval_result,
                credential_status=credential_status,
                runtime_policy_result=dry_run.runtime_policy_result,
                gate_result=dry_run,
                drawdown_feed=drawdown_feed,
                market_plan=market_plan,
                lifecycle=lifecycle,
                sanitized_order_request=self._sanitize_order_request(order_action, market_plan),
                sanitized_order_response={"error": redact_sensitive_text(str(exc))},
            )

        order_status, oid, status_reasons = self._parse_order_response(order_response)
        cancel_response: Any | None = None
        cancel_status = "not_required"
        cancel_called = False
        unexpected_fill = order_status in {"filled", "partial_fill"}
        if order_status == "open" and oid is not None:
            cancel_called = True
            cancel_action = {"type": "cancel", "cancels": [{"a": market_plan.asset_id, "o": int(oid)}]}
            cancel_payload = self._signed_payload(
                action=cancel_action,
                private_key=private_key,
                account_id=account_id,
                is_mainnet=False,
            )
            try:
                cancel_response = await self._transport.post_json("/exchange", cancel_payload)
                cancel_status = "cancel_acknowledged" if self._action_ok(cancel_response) else "cancel_rejected"
            except Exception as exc:  # noqa: BLE001
                cancel_response = {"error": redact_sensitive_text(str(exc))}
                cancel_status = "cancel_unknown"
                status_reasons.append(UAT31RejectReason.CANCEL_TRANSPORT_FAILED)

        reconciliation_payloads: dict[str, Any] = {}
        if oid is not None:
            reconciliation_payloads["order_status"] = await self._transport.post_json(
                "/info",
                {"type": "orderStatus", "user": account_id, "oid": int(oid)},
            )
        reconciliation_payloads["open_orders"] = await self._transport.post_json(
            "/info",
            {"type": "frontendOpenOrders", "user": account_id},
        )
        post_account_state = await self._transport.post_json(
            "/info",
            {"type": "clearinghouseState", "user": account_id},
        )
        reconciliation_payloads["account_state"] = post_account_state

        open_order_remains = self._open_order_remains(reconciliation_payloads.get("open_orders"), oid)
        if open_order_remains:
            status_reasons.append(UAT31RejectReason.OPEN_ORDER_REMAINS)
        lifecycle = UAT31LifecycleResult(
            order_attempt_count=1,
            order_endpoint_called=True,
            cancel_endpoint_called=cancel_called,
            order_status=order_status,
            exchange_order_id=str(oid) if oid is not None else None,
            client_order_id=market_plan.cloid,
            cancel_status=cancel_status,
            reconciliation_status="completed" if not open_order_remains else "open_order_remaining",
            unexpected_fill=unexpected_fill,
            open_order_remains=open_order_remains,
            unknown_state=order_status == "unknown" or cancel_status == "cancel_unknown",
            reason_codes=tuple(dict.fromkeys(status_reasons)),
        )
        return self._result(
            allowed_to_submit=True,
            approval_result=approval_result,
            credential_status=credential_status,
            runtime_policy_result=dry_run.runtime_policy_result,
            gate_result=dry_run,
            drawdown_feed=drawdown_feed,
            market_plan=market_plan,
            lifecycle=lifecycle,
            sanitized_order_request=self._sanitize_order_request(order_action, market_plan),
            sanitized_order_response=_sanitize_payload(order_response),
            sanitized_cancel_response=_sanitize_payload(cancel_response or {}),
            sanitized_reconciliation=_sanitize_payload(reconciliation_payloads),
        )

    def _blocked_result(
        self,
        approval_result: SandboxCheckResult,
        lifecycle: UAT31LifecycleResult,
        reason_codes: tuple[str, ...],
        *,
        credential_status: Any | None = None,
        runtime_policy_result: SandboxCheckResult | None = None,
        gate_result: Any | None = None,
        drawdown_feed: SandboxAccountDrawdownFeed | None = None,
        market_plan: UAT31MarketPlan | None = None,
    ) -> UAT31FirstSandboxOrderAttemptResult:
        return self._result(
            allowed_to_submit=False,
            approval_result=approval_result,
            credential_status=credential_status,
            runtime_policy_result=runtime_policy_result,
            gate_result=gate_result,
            drawdown_feed=drawdown_feed,
            market_plan=market_plan,
            lifecycle=lifecycle,
            reason_codes=reason_codes,
        )

    def _result(
        self,
        *,
        allowed_to_submit: bool,
        approval_result: SandboxCheckResult,
        credential_status: Any | None,
        runtime_policy_result: SandboxCheckResult | None,
        gate_result: Any | None,
        drawdown_feed: SandboxAccountDrawdownFeed | None,
        market_plan: UAT31MarketPlan | None,
        lifecycle: UAT31LifecycleResult,
        reason_codes: tuple[str, ...] | None = None,
        sanitized_order_request: Mapping[str, Any] | None = None,
        sanitized_order_response: Mapping[str, Any] | None = None,
        sanitized_cancel_response: Mapping[str, Any] | None = None,
        sanitized_reconciliation: Mapping[str, Any] | None = None,
    ) -> UAT31FirstSandboxOrderAttemptResult:
        combined = tuple(dict.fromkeys(reason_codes or lifecycle.reason_codes))
        return UAT31FirstSandboxOrderAttemptResult(
            allowed_to_submit=allowed_to_submit,
            blocked=bool(combined) and not allowed_to_submit,
            reason_codes=combined,
            approval_result=approval_result,
            credential_status=credential_status,
            runtime_policy_result=runtime_policy_result,
            gate_result=gate_result,
            drawdown_feed=drawdown_feed,
            market_plan=market_plan,
            lifecycle=lifecycle,
            sanitized_order_request=sanitized_order_request or {},
            sanitized_order_response=sanitized_order_response or {},
            sanitized_cancel_response=sanitized_cancel_response or {},
            sanitized_reconciliation=sanitized_reconciliation or {},
        )

    @staticmethod
    def _order_action(plan: UAT31MarketPlan) -> dict[str, Any]:
        return {
            "type": "order",
            "orders": [
                {
                    "a": plan.asset_id,
                    "b": True,
                    "p": float_to_wire(plan.limit_price),
                    "s": float_to_wire(plan.quantity),
                    "r": False,
                    "t": {"limit": {"tif": plan.tif}},
                    "c": plan.cloid,
                }
            ],
            "grouping": "na",
        }

    @staticmethod
    def _signed_payload(
        *,
        action: dict[str, Any],
        private_key: str,
        account_id: str,
        is_mainnet: bool,
    ) -> dict[str, Any]:
        nonce = int(time.time() * 1000)
        signer = signer_address(private_key)
        vault_address = account_id.lower() if signer != account_id.lower() else None
        return {
            "action": action,
            "nonce": nonce,
            "signature": sign_l1_action(
                private_key=private_key,
                action=action,
                vault_address=vault_address,
                nonce=nonce,
                expires_after=None,
                is_mainnet=is_mainnet,
            ),
            "vaultAddress": vault_address,
            "expiresAfter": None,
        }

    @staticmethod
    def _parse_order_response(response: Any) -> tuple[str, str | None, list[str]]:
        reasons: list[str] = []
        if not isinstance(response, Mapping):
            return "unknown", None, ["order_response_shape_unknown"]
        if response.get("status") != "ok":
            reasons = ["order_rejected"]
            if "does not exist" in str(response.get("response", "")).lower():
                reasons.append("hyperliquid_testnet_user_or_api_wallet_not_found")
            return "rejected", None, reasons
        statuses = (((response.get("response") or {}).get("data") or {}).get("statuses") or [])
        first = statuses[0] if statuses else {}
        if isinstance(first, Mapping) and first.get("error") is not None:
            return "rejected", None, ["order_rejected", str(first.get("error"))]
        if isinstance(first, Mapping) and isinstance(first.get("resting"), Mapping):
            return "open", str(first["resting"].get("oid")), ["order_accepted_open"]
        if isinstance(first, Mapping) and isinstance(first.get("filled"), Mapping):
            return "filled", str(first["filled"].get("oid")), [UAT31RejectReason.UNEXPECTED_FILL]
        return "submitted", None, ["order_submitted_status_unclassified"]

    @staticmethod
    def _action_ok(response: Any) -> bool:
        if not isinstance(response, Mapping) or response.get("status") != "ok":
            return False
        statuses = (((response.get("response") or {}).get("data") or {}).get("statuses") or [])
        return not any(isinstance(item, Mapping) and item.get("error") for item in statuses)

    @staticmethod
    def _open_order_remains(open_orders_payload: Any, oid: str | None) -> bool:
        if oid is None or not isinstance(open_orders_payload, list):
            return False
        return any(isinstance(item, Mapping) and str(item.get("oid")) == str(oid) for item in open_orders_payload)

    @staticmethod
    def _sanitize_order_request(action: Mapping[str, Any], plan: UAT31MarketPlan) -> Mapping[str, Any]:
        return {
            "endpoint": "/exchange",
            "endpoint_category": SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION.value,
            "symbol": plan.symbol,
            "asset_id": plan.asset_id,
            "side": "buy",
            "order_type": "post_only_limit",
            "tif": plan.tif,
            "limit_price": str(plan.limit_price),
            "quantity": str(plan.quantity),
            "estimated_notional": str(plan.estimated_notional),
            "client_order_id_present": bool(plan.cloid),
            "signature_included_in_report": False,
            "raw_signed_payload_included_in_report": False,
            "action_summary": _sanitize_payload(action),
        }


def _sanitize_payload(payload: Any) -> Any:
    return redact_sensitive_structure(payload)


def result_to_summary_dict(result: UAT31FirstSandboxOrderAttemptResult) -> dict[str, Any]:
    drawdown = result.drawdown_feed
    market = result.market_plan
    return {
        "uat_run_id": UAT31_RUN_ID,
        "approval_verified": result.approval_result.allowed,
        "allowed_to_submit": result.allowed_to_submit,
        "blocked": result.blocked,
        "reason_codes": list(result.reason_codes),
        "order_attempt_count": result.lifecycle.order_attempt_count,
        "order_endpoint_called": result.lifecycle.order_endpoint_called,
        "cancel_endpoint_called": result.lifecycle.cancel_endpoint_called,
        "order_status": result.lifecycle.order_status,
        "cancel_status": result.lifecycle.cancel_status,
        "reconciliation_status": result.lifecycle.reconciliation_status,
        "unexpected_fill": result.lifecycle.unexpected_fill,
        "open_order_remains": result.lifecycle.open_order_remains,
        "unknown_state": result.lifecycle.unknown_state,
        "sandbox_labels": {
            "sandbox": True,
            "testnet": True,
            "not_live": True,
            "not_paper": True,
            "manual_sandbox_lifecycle_probe": True,
            "not_strategy_signal": True,
            "not_performance_validation": True,
            "live_endpoint_access": False,
            "real_capital": False,
        },
        "market_plan": None
        if market is None
        else {
            "symbol": market.symbol,
            "limit_price": str(market.limit_price),
            "quantity": str(market.quantity),
            "estimated_notional": str(market.estimated_notional),
            "tif": market.tif,
        },
        "drawdown_feed": None
        if drawdown is None
        else {
            "status": drawdown.status.value,
            "source": drawdown.source,
            "not_live_account": drawdown.not_live_account,
            "timestamp_utc": drawdown.timestamp_utc.isoformat(),
            "sandbox_account_equity_available": drawdown.sandbox_account_equity is not None,
            "max_drawdown_percent": (
                str(drawdown.max_drawdown_percent) if drawdown.max_drawdown_percent is not None else None
            ),
            "threshold_breached": drawdown.threshold_breached,
            "unavailable_fields": list(drawdown.unavailable_fields),
        },
        "side_effect_flags": {
            "creates_order_intent": result.creates_order_intent,
            "creates_prepared_order": result.creates_prepared_order,
            "creates_submitted_order": result.creates_submitted_order,
            "creates_executable_approval": result.creates_executable_approval,
            "paper_trading_added": result.paper_trading_added,
            "live_trading_added": result.live_trading_added,
        },
        "sanitized_order_request": result.sanitized_order_request,
        "sanitized_order_response": result.sanitized_order_response,
        "sanitized_cancel_response": result.sanitized_cancel_response,
        "sanitized_reconciliation": result.sanitized_reconciliation,
    }
