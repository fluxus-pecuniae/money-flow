from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from services.uat.sandbox import (
    HyperliquidSandboxEquitySource,
    PriorSandboxSubmitAttempt,
    SandboxSubmitAttemptKey,
    SandboxSubmitPreflightRequest,
    SandboxSubmitPreflightState,
    SandboxSubmitRejectReason,
    evaluate_sandbox_submit_preflight,
    resolve_hyperliquid_sandbox_equity_source,
)
from services.uat.sandbox_order import (
    UAT31LifecycleResult,
    UAT34RejectReason,
    UAT34_APPROVAL_ID,
    UAT34_COMPONENT,
    UAT34_ROUTE_ID,
    UAT34_RUN_ID,
    UAT34RouteCandidate,
    build_uat34_artifact_labels,
    build_uat34_routed_order_record,
    validate_uat34_fixed_target_route,
)


NOW = datetime(2026, 5, 11, 6, 0, tzinfo=UTC)


def test_standard_perp_equity_source_selected_for_current_working_route() -> None:
    result = resolve_hyperliquid_sandbox_equity_source(
        perp_payload={
            "marginSummary": {"accountValue": "999.0"},
            "withdrawable": "998.5",
        },
        spot_payload={"balances": [{"coin": "USDC", "total": "1000", "hold": "1"}]},
    )

    assert result.selected_equity_source == HyperliquidSandboxEquitySource.STANDARD_PERP_CLEARINGHOUSE
    assert result.selected_sandbox_equity == Decimal("999.0")
    assert result.perp_withdrawable == Decimal("998.5")


def test_unified_spot_clearinghouse_fallback_selects_usdc_total_minus_hold() -> None:
    result = resolve_hyperliquid_sandbox_equity_source(
        perp_payload={"marginSummary": {"accountValue": "0.0"}, "withdrawable": "0"},
        spot_payload={"balances": [{"coin": "USDC", "total": "1000", "hold": "17.25"}]},
    )

    assert result.selected_equity_source == HyperliquidSandboxEquitySource.UNIFIED_MARGIN_SPOT_CLEARINGHOUSE_FALLBACK
    assert result.spot_usdc_total == Decimal("1000")
    assert result.spot_usdc_hold == Decimal("17.25")
    assert result.selected_sandbox_equity == Decimal("982.75")


def test_fixed_target_route_rejects_non_eth_top20_and_routing_behaviors() -> None:
    non_eth = validate_uat34_fixed_target_route(
        UAT34RouteCandidate(route_id=UAT34_ROUTE_ID, venue="hyperliquid", environment="testnet", symbol="BTC")
    )
    unsafe = validate_uat34_fixed_target_route(
        UAT34RouteCandidate(
            route_id=UAT34_ROUTE_ID,
            venue="hyperliquid",
            environment="testnet",
            symbol="ETH",
            top20_broad_submission=True,
            sor=True,
            fanout=True,
            target_reselection=True,
            route_executor_behavior=True,
        )
    )

    assert UAT34RejectReason.NON_ETH_SYMBOL_FORBIDDEN in non_eth.reason_codes
    assert UAT34RejectReason.TOP20_BROAD_ORDER_FORBIDDEN in unsafe.reason_codes
    assert UAT34RejectReason.SOR_FORBIDDEN in unsafe.reason_codes
    assert UAT34RejectReason.FANOUT_FORBIDDEN in unsafe.reason_codes
    assert UAT34RejectReason.TARGET_RESELECTION_FORBIDDEN in unsafe.reason_codes
    assert UAT34RejectReason.ROUTE_EXECUTOR_FORBIDDEN in unsafe.reason_codes


def test_fixed_target_route_accepts_hyperliquid_testnet_eth_only() -> None:
    result = validate_uat34_fixed_target_route(
        UAT34RouteCandidate(route_id=UAT34_ROUTE_ID, venue="hyperliquid", environment="testnet", symbol="ETH")
    )

    assert result.allowed is True


def test_routed_ledger_record_includes_lifecycle_cancel_reconcile_equity_and_labels() -> None:
    labels = build_uat34_artifact_labels()
    lifecycle = UAT31LifecycleResult(
        order_attempt_count=1,
        order_endpoint_called=True,
        cancel_endpoint_called=True,
        order_status="open",
        exchange_order_id="52873216602",
        client_order_id="0xabc",
        cancel_status="success",
        reconciliation_status="completed",
        unexpected_fill=False,
        open_order_remains=False,
        unknown_state=False,
        reason_codes=("order_accepted_open",),
    )

    record = build_uat34_routed_order_record(
        attempt_number=1,
        market_plan=None,
        lifecycle=lifecycle,
        selected_equity_source=HyperliquidSandboxEquitySource.STANDARD_PERP_CLEARINGHOUSE,
        sanitized_exchange_response={"status": "ok"},
        labels=labels,
        account_id="sandbox-account-1",
    )

    assert record.lifecycle_status == "canceled"
    assert record.cancel_status == "success"
    assert record.reconciliation_status == "completed"
    assert record.selected_equity_source == "standard_perp_clearinghouse"
    assert record.sandbox_labels["sandbox"] is True
    assert record.sandbox_labels["not_live"] is True
    assert record.sandbox_labels["not_paper"] is True
    assert record.no_live_no_paper_confirmation is True


def test_duplicate_submission_blocks_by_submit_lease_and_idempotency_key() -> None:
    key = SandboxSubmitAttemptKey(
        approval_id=UAT34_APPROVAL_ID,
        uat_run_id=UAT34_RUN_ID,
        venue="hyperliquid",
        account_id="sandbox-account-1",
        symbol="ETH",
        component=f"{UAT34_COMPONENT}_1",
        environment="testnet",
    )
    result = evaluate_sandbox_submit_preflight(
        request=SandboxSubmitPreflightRequest(
            key=key,
            submit_lease_acquired=True,
            idempotency_key="idem-1",
        ),
        state=SandboxSubmitPreflightState(
            prior_attempts=(PriorSandboxSubmitAttempt(key=key, status="canceled"),)
        ),
    )

    assert result.blocked is True
    assert SandboxSubmitRejectReason.DUPLICATE_SAME_APPROVAL_CANDIDATE in result.reason_codes


def test_uat4_dashboard_roadmap_request_is_captured_in_docs_or_runner() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("money-flow/00 Maps/UAT Roadmap.md"),
            Path("docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md"),
        )
        if path.exists()
    )
    runner = Path("scripts/run_uat34_sandbox_routing_pipeline.py").read_text(encoding="utf-8")
    text = f"{docs}\n{runner}"

    assert "UAT4.0" in text
    assert "Live UAT Trading Dashboard" in text
    assert "routed orders tab" in text
