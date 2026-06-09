"""Trading safety invariants — must never be relaxed.

A red test here means a real safety default changed.
Pure/in-memory: no DB, network, env, runtime, or orders.
"""

from __future__ import annotations

import pytest

from core.config.settings import RuntimeSafetyPolicy, VenueIntegrationConfig
from services.exchange.safety import (
    EndpointRuntimePolicyDecision,
    ExchangeEndpointCategory,
    classify_hyperliquid_exchange_payload,
    classify_hyperliquid_info_payload,
    evaluate_runtime_policy_for_endpoint,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_4_DISABLED_TIMEFRAMES,
    PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT1_6_ACTIVE_TIMEFRAMES,
    PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS,
    pt_rt1_6_lane_testnet_eligible,
)

# ---------------------------------------------------------------------------
# RuntimeSafetyPolicy defaults
# ---------------------------------------------------------------------------


def test_runtime_safety_policy_live_trading_disabled_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.live_trading_enabled is False


def test_runtime_safety_policy_order_submission_disabled_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.exchange_order_submission_enabled is False


def test_runtime_safety_policy_private_endpoints_disabled_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.private_exchange_endpoints_enabled is False


def test_runtime_safety_policy_sandbox_required_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.sandbox_mode_required is True


def test_runtime_safety_policy_paper_trading_disabled_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.paper_trading_enabled is False


def test_runtime_safety_policy_lockout_properties_all_true_by_default() -> None:
    policy = RuntimeSafetyPolicy()
    assert policy.live_endpoint_lockout_enabled is True
    assert policy.order_endpoint_lockout_enabled is True
    assert policy.private_endpoint_lockout_enabled is True


# ---------------------------------------------------------------------------
# VenueIntegrationConfig defaults
# ---------------------------------------------------------------------------


def _make_integration(**overrides: object) -> VenueIntegrationConfig:
    from core.config.settings import Venue

    defaults = dict(venue=Venue.HYPERLIQUID, name="hyperliquid")
    return VenueIntegrationConfig(**{**defaults, **overrides})  # type: ignore[arg-type]


def test_venue_integration_read_only_by_default() -> None:
    config = _make_integration()
    assert config.read_only_mode is True


def test_venue_integration_dry_run_by_default() -> None:
    config = _make_integration()
    assert config.dry_run_mode is True


def test_venue_integration_submission_disabled_by_default() -> None:
    config = _make_integration()
    assert config.submission_enabled is False


def test_venue_integration_submission_unauthorized_by_default() -> None:
    config = _make_integration()
    assert config.submission_authorized is False


# ---------------------------------------------------------------------------
# evaluate_runtime_policy_for_endpoint — blocked categories under defaults
# ---------------------------------------------------------------------------

_DEFAULT_POLICY = RuntimeSafetyPolicy()
_DEFAULT_INTEGRATION = _make_integration()


def _eval(category: ExchangeEndpointCategory) -> EndpointRuntimePolicyDecision:
    return evaluate_runtime_policy_for_endpoint(
        category=category,
        runtime_policy=_DEFAULT_POLICY,
        integration=_DEFAULT_INTEGRATION,
    )


@pytest.mark.parametrize(
    "category",
    [
        ExchangeEndpointCategory.ORDER_SUBMISSION,
        ExchangeEndpointCategory.ORDER_CANCEL,
        ExchangeEndpointCategory.ORDER_AMEND,
        ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
    ],
)
def test_order_categories_blocked_by_default(category: ExchangeEndpointCategory) -> None:
    decision = _eval(category)
    assert decision.allowed is False
    assert "exchange_order_submission_disabled_by_runtime_policy" in decision.reason_codes
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in decision.reason_codes


@pytest.mark.parametrize(
    "category",
    [
        ExchangeEndpointCategory.PRIVATE_READ_ONLY,
        ExchangeEndpointCategory.PRIVATE_SIGNED,
    ],
)
def test_private_categories_blocked_by_default(category: ExchangeEndpointCategory) -> None:
    decision = _eval(category)
    assert decision.allowed is False
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in decision.reason_codes


def test_public_read_only_allowed_by_default() -> None:
    decision = _eval(ExchangeEndpointCategory.PUBLIC_READ_ONLY)
    assert decision.allowed is True
    assert not decision.reason_codes


def test_unknown_category_blocked_by_default() -> None:
    decision = _eval(ExchangeEndpointCategory.UNKNOWN)
    assert decision.allowed is False
    assert "exchange_endpoint_category_unknown" in decision.reason_codes


def test_live_trading_disabled_in_live_mode() -> None:
    live_policy = RuntimeSafetyPolicy(runtime_mode="live", live_trading_enabled=False)
    decision = evaluate_runtime_policy_for_endpoint(
        category=ExchangeEndpointCategory.PUBLIC_READ_ONLY,
        runtime_policy=live_policy,
        integration=_DEFAULT_INTEGRATION,
    )
    assert "live_trading_disabled_by_runtime_policy" in decision.reason_codes


def test_live_mode_with_live_trading_enabled_clears_live_reason_code() -> None:
    live_policy = RuntimeSafetyPolicy(
        runtime_mode="live",
        live_trading_enabled=True,
        exchange_order_submission_enabled=True,
        private_exchange_endpoints_enabled=True,
    )
    decision = evaluate_runtime_policy_for_endpoint(
        category=ExchangeEndpointCategory.PUBLIC_READ_ONLY,
        runtime_policy=live_policy,
        integration=_DEFAULT_INTEGRATION,
    )
    assert "live_trading_disabled_by_runtime_policy" not in decision.reason_codes


# ---------------------------------------------------------------------------
# Exact reason-code string assertions
# ---------------------------------------------------------------------------


def test_exact_reason_codes_for_order_submission_default() -> None:
    decision = _eval(ExchangeEndpointCategory.ORDER_SUBMISSION)
    assert "private_exchange_endpoints_disabled_by_runtime_policy" in decision.reason_codes
    assert "exchange_order_submission_disabled_by_runtime_policy" in decision.reason_codes


def test_exact_reason_code_for_unknown_category() -> None:
    decision = _eval(ExchangeEndpointCategory.UNKNOWN)
    assert "exchange_endpoint_category_unknown" in decision.reason_codes


# ---------------------------------------------------------------------------
# Hyperliquid classifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "info_type",
    ["allMids", "candleSnapshot", "meta", "l2Book", "fundingHistory", "metaAndAssetCtxs"],
)
def test_hyperliquid_public_info_types_classified_public(info_type: str) -> None:
    result = classify_hyperliquid_info_payload({"type": info_type})
    assert result == ExchangeEndpointCategory.PUBLIC_READ_ONLY


@pytest.mark.parametrize(
    "info_type",
    ["clearinghouseState", "openOrders", "userFills", "orderStatus"],
)
def test_hyperliquid_private_info_types_classified_private(info_type: str) -> None:
    result = classify_hyperliquid_info_payload({"type": info_type})
    assert result == ExchangeEndpointCategory.PRIVATE_READ_ONLY


def test_hyperliquid_exchange_order_classified_submission() -> None:
    payload = {"action": {"type": "order", "orders": []}}
    result = classify_hyperliquid_exchange_payload(payload)
    assert result == ExchangeEndpointCategory.ORDER_SUBMISSION


def test_hyperliquid_exchange_cancel_classified_cancel() -> None:
    payload = {"action": {"type": "cancel", "cancels": []}}
    assert classify_hyperliquid_exchange_payload(payload) == ExchangeEndpointCategory.ORDER_CANCEL


def test_hyperliquid_exchange_modify_classified_amend() -> None:
    payload = {"action": {"type": "modify", "modifies": []}}
    assert classify_hyperliquid_exchange_payload(payload) == ExchangeEndpointCategory.ORDER_AMEND


# ---------------------------------------------------------------------------
# Slate boundaries (import anchors from pt_rt1 — do NOT duplicate as lists)
# ---------------------------------------------------------------------------


def test_active_lanes_are_exactly_three() -> None:
    assert len(PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS) == 3


def test_archived_lanes_are_exactly_seven() -> None:
    assert len(PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS) == 7


def test_active_timeframes_are_1h_4h_1d() -> None:
    assert PT_RT1_6_ACTIVE_TIMEFRAMES == ("1h", "4h", "1d")


def test_15m_is_paused() -> None:
    assert "15m" not in PT_RT1_6_ACTIVE_TIMEFRAMES
    assert "15m" in PT_RT1_4_DISABLED_TIMEFRAMES


def test_only_baseline_testnet_eligible_among_active() -> None:
    eligible = [
        lid for lid in PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS if pt_rt1_6_lane_testnet_eligible(lid)
    ]
    assert eligible == ["money_flow_v1_2_baseline"]


def test_non_baseline_active_lanes_not_testnet_eligible() -> None:
    non_baseline = [
        lid for lid in PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS if lid != "money_flow_v1_2_baseline"
    ]
    for lane_id in non_baseline:
        assert pt_rt1_6_lane_testnet_eligible(lane_id) is False


def test_no_archived_lane_testnet_eligible() -> None:
    for lane_id in PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS:
        assert pt_rt1_6_lane_testnet_eligible(lane_id) is False
