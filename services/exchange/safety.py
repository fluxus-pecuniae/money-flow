"""Exchange endpoint safety classification and runtime policy guards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from core.config.settings import RuntimeSafetyPolicy, VenueIntegrationConfig


class ExchangeEndpointCategory(StrEnum):
    PUBLIC_READ_ONLY = "public_read_only"
    PRIVATE_READ_ONLY = "private_read_only"
    PRIVATE_SIGNED = "private_signed"
    ORDER_SUBMISSION = "order_submission"
    ORDER_CANCEL = "order_cancel"
    ORDER_AMEND = "order_amend"
    ORDER_RETRY_OR_RECOVERY = "order_retry_or_recovery"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EndpointRuntimePolicyDecision:
    allowed: bool
    reason_codes: tuple[str, ...]
    category: ExchangeEndpointCategory


@dataclass(frozen=True)
class UATReadOnlyEndpointPolicy:
    venue: str
    allowed_categories: tuple[ExchangeEndpointCategory, ...]
    forbidden_categories: tuple[ExchangeEndpointCategory, ...]
    runtime_mode_requirement: str
    required_api_scope: str
    private_endpoint_status: str
    order_endpoint_status: str
    notes: str
    allowed_public_info_types: tuple[str, ...] = ()
    endpoint_url_status: str = "needs_verification"
    sandbox_or_testnet_status: str = "needs_verification"


HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST = UATReadOnlyEndpointPolicy(
    venue="hyperliquid",
    allowed_categories=(ExchangeEndpointCategory.PUBLIC_READ_ONLY,),
    forbidden_categories=(
        ExchangeEndpointCategory.PRIVATE_READ_ONLY,
        ExchangeEndpointCategory.PRIVATE_SIGNED,
        ExchangeEndpointCategory.ORDER_SUBMISSION,
        ExchangeEndpointCategory.ORDER_CANCEL,
        ExchangeEndpointCategory.ORDER_AMEND,
        ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
        ExchangeEndpointCategory.UNKNOWN,
    ),
    runtime_mode_requirement="future_uat1_read_only_explicitly_enabled",
    required_api_scope="read_only_operator_or_operator_for_catalog_sync",
    private_endpoint_status="forbidden_in_uat1",
    order_endpoint_status="forbidden_in_uat1",
    notes=(
        "Future UAT1 may use unsigned public Hyperliquid metadata, candles, tickers, "
        "order-book snapshots, and public funding metadata only after a separate UAT1 phase. "
        "Private account state, signed requests, API keys, and order endpoints remain forbidden."
    ),
    allowed_public_info_types=(
        "allMids",
        "candleSnapshot",
        "fundingHistory",
        "l2Book",
        "meta",
        "metaAndAssetCtxs",
    ),
)


_ORDER_SUBMISSION_MARKERS = (
    "/order",
    "/orders",
    "addorder",
    "placeorder",
)
_ORDER_CANCEL_MARKERS = ("cancel", "cancelorder")
_ORDER_AMEND_MARKERS = ("amend", "replace", "modify")
_PRIVATE_MARKERS = (
    "/private/",
    "/account",
    "/balance",
    "/positions",
    "/fills",
    "/trades",
    "openorders",
    "queryorders",
    "mytrades",
    "usertrades",
)
_AUTH_HEADER_MARKERS = (
    "authorization",
    "x-mbx-apikey",
    "ok-access-key",
    "cb-access-key",
    "api-key",
    "api_sign",
    "api-key",
)


def classify_rest_endpoint(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | str | None = None,
    headers: dict[str, str] | None = None,
) -> ExchangeEndpointCategory:
    """Classify a REST adapter call before transport is invoked."""

    method_upper = method.upper()
    normalized_path = path.lower()
    normalized_headers = {str(key).lower(): str(value) for key, value in (headers or {}).items()}
    has_auth_header = any(marker in normalized_headers for marker in _AUTH_HEADER_MARKERS)
    payload_text = f"{params or {}} {body or {}}".lower()
    has_signature = "signature" in payload_text or "api-sign" in payload_text

    if any(marker in normalized_path for marker in _ORDER_CANCEL_MARKERS):
        return ExchangeEndpointCategory.ORDER_CANCEL
    if any(marker in normalized_path for marker in _ORDER_AMEND_MARKERS):
        return ExchangeEndpointCategory.ORDER_AMEND
    if method_upper == "DELETE" and any(marker in normalized_path for marker in _ORDER_SUBMISSION_MARKERS):
        return ExchangeEndpointCategory.ORDER_CANCEL
    if method_upper in {"POST", "PUT", "DELETE"} and any(
        marker in normalized_path for marker in _ORDER_SUBMISSION_MARKERS
    ):
        return ExchangeEndpointCategory.ORDER_SUBMISSION
    if has_auth_header and any(marker in normalized_path for marker in _ORDER_SUBMISSION_MARKERS):
        return ExchangeEndpointCategory.PRIVATE_SIGNED
    if has_auth_header or has_signature or any(marker in normalized_path for marker in _PRIVATE_MARKERS):
        return ExchangeEndpointCategory.PRIVATE_READ_ONLY
    if method_upper == "GET":
        return ExchangeEndpointCategory.PUBLIC_READ_ONLY
    return ExchangeEndpointCategory.UNKNOWN


_HYPERLIQUID_PUBLIC_INFO_TYPES = {
    "allMids",
    "candleSnapshot",
    "fundingHistory",
    "l2Book",
    "meta",
    "metaAndAssetCtxs",
    "spotMeta",
    "spotMetaAndAssetCtxs",
}
_HYPERLIQUID_PRIVATE_INFO_TYPES = {
    "clearinghouseState",
    "frontendOpenOrders",
    "historicalOrders",
    "openOrders",
    "orderStatus",
    "portfolio",
    "userFills",
    "userFillsByTime",
    "userRateLimit",
}


def classify_hyperliquid_info_payload(payload: dict[str, Any]) -> ExchangeEndpointCategory:
    request_type = str(payload.get("type") or "")
    if request_type in _HYPERLIQUID_PUBLIC_INFO_TYPES:
        return ExchangeEndpointCategory.PUBLIC_READ_ONLY
    if request_type in _HYPERLIQUID_PRIVATE_INFO_TYPES:
        return ExchangeEndpointCategory.PRIVATE_READ_ONLY
    return ExchangeEndpointCategory.UNKNOWN


def classify_hyperliquid_exchange_payload(payload: dict[str, Any]) -> ExchangeEndpointCategory:
    action = payload.get("action")
    action_type = ""
    if isinstance(action, dict):
        action_type = str(action.get("type") or "").lower()
    if "cancel" in action_type:
        return ExchangeEndpointCategory.ORDER_CANCEL
    if "modify" in action_type or "amend" in action_type:
        return ExchangeEndpointCategory.ORDER_AMEND
    return ExchangeEndpointCategory.ORDER_SUBMISSION


def evaluate_runtime_policy_for_endpoint(
    *,
    category: ExchangeEndpointCategory,
    runtime_policy: RuntimeSafetyPolicy,
    integration: VenueIntegrationConfig,
) -> EndpointRuntimePolicyDecision:
    reason_codes: list[str] = []

    if category == ExchangeEndpointCategory.UNKNOWN:
        reason_codes.append("exchange_endpoint_category_unknown")

    if category in {
        ExchangeEndpointCategory.PRIVATE_READ_ONLY,
        ExchangeEndpointCategory.PRIVATE_SIGNED,
        ExchangeEndpointCategory.ORDER_SUBMISSION,
        ExchangeEndpointCategory.ORDER_CANCEL,
        ExchangeEndpointCategory.ORDER_AMEND,
        ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
        ExchangeEndpointCategory.UNKNOWN,
    } and not runtime_policy.private_exchange_endpoints_enabled:
        reason_codes.append("private_exchange_endpoints_disabled_by_runtime_policy")

    if category in {
        ExchangeEndpointCategory.ORDER_SUBMISSION,
        ExchangeEndpointCategory.ORDER_CANCEL,
        ExchangeEndpointCategory.ORDER_AMEND,
        ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
    } and not runtime_policy.exchange_order_submission_enabled:
        reason_codes.append("exchange_order_submission_disabled_by_runtime_policy")

    if runtime_policy.runtime_mode == "live" and not runtime_policy.live_trading_enabled:
        reason_codes.append("live_trading_disabled_by_runtime_policy")

    if (
        category
        in {
            ExchangeEndpointCategory.PRIVATE_READ_ONLY,
            ExchangeEndpointCategory.PRIVATE_SIGNED,
            ExchangeEndpointCategory.ORDER_SUBMISSION,
            ExchangeEndpointCategory.ORDER_CANCEL,
            ExchangeEndpointCategory.ORDER_AMEND,
            ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
        }
        and runtime_policy.runtime_mode in {"uat", "sandbox", "paper"}
        and runtime_policy.sandbox_mode_required
        and not integration.use_testnet
        and not integration.use_demo_mode
    ):
        reason_codes.append("sandbox_or_testnet_required_by_runtime_policy")

    return EndpointRuntimePolicyDecision(
        allowed=not reason_codes,
        reason_codes=tuple(reason_codes),
        category=category,
    )
