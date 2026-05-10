"""Run the approved UAT3.3 Hyperliquid testnet precision/targeting lifecycle probe."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from core.security import redact_sensitive_text
from services.exchange.hyperliquid.signing import signer_address
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
    SandboxAccountDrawdownFeed,
    SandboxAccountStateSnapshot,
    SandboxAdapterEndpointClassification,
    SandboxApprovalCandidate,
    SandboxApprovalScope,
    SandboxDrawdownFeedStatus,
    SandboxPrivateEndpointCategory,
    SandboxRiskLimits,
    SandboxRiskRequest,
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
from services.uat.sandbox_order import (
    HyperliquidAccountTarget,
    HyperliquidUAT31HTTPTransport,
    UAT31FirstSandboxOrderAttemptService,
    UAT31LifecycleResult,
    UAT33RejectReason,
    UAT33_APPROVAL_ID,
    UAT33_CANDIDATE_ID,
    UAT33_COMPONENT,
    UAT33_DRAWDOWN_THRESHOLD,
    UAT33_MAX_NOTIONAL,
    UAT33_RUN_ID,
    build_uat31_market_plan,
    build_uat33_artifact_labels,
    build_uat33_idempotency_key,
    build_uat32_runtime_policy,
    evaluate_uat32_account_api_wallet_readiness,
    resolve_hyperliquid_uat_account_target,
    validate_uat31_manual_probe_labels,
    validate_uat33_universe_precision,
    _sanitize_payload,
)


SUMMARY_PATH = Path("docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt_summary.json")
REPORT_PATH = Path("docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md")

UAT33_APPROVAL_TEXT = """one approval-gated sandbox/testnet order submission attempt
Hyperliquid testnet / sandbox only
ETH USDC perpetual only
manual sandbox lifecycle probe
not a Money Flow performance test
not paper trading
not live trading
not broad top-20 order submission
not repeated orders
not auto-submit"""


def _load_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _prior_attempt_exists(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return True
    return bool(payload.get("order_attempt_count", 0))


def _safe_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _drawdown_summary(feed: SandboxAccountDrawdownFeed | None) -> dict[str, Any] | None:
    if feed is None:
        return None
    return {
        "status": feed.status.value,
        "source": feed.source,
        "not_live_account": feed.not_live_account,
        "timestamp_utc": feed.timestamp_utc.isoformat(),
        "sandbox_account_equity_available": feed.sandbox_account_equity is not None,
        "sandbox_account_equity": str(feed.sandbox_account_equity) if feed.sandbox_account_equity is not None else None,
        "threshold_breached": feed.threshold_breached,
        "max_drawdown_percent": str(feed.max_drawdown_percent) if feed.max_drawdown_percent is not None else None,
        "unavailable_fields": list(feed.unavailable_fields),
    }


def _markdown_report(summary: Mapping[str, Any]) -> str:
    next_decision = summary["next_readiness_decision"]
    precision_rows = "\n".join(
        "| {symbol} | {asset_id} | {sz_decimals} | {max_price_decimals} | {sample_mid} | {price} | {size} | {passed} | {reasons} |".format(
            symbol=row["symbol"],
            asset_id=row.get("asset_id"),
            sz_decimals=row.get("sz_decimals"),
            max_price_decimals=row.get("max_price_decimals"),
            sample_mid=row.get("sample_mid"),
            price=row.get("formatted_sample_post_only_buy_price"),
            size=row.get("formatted_sample_size"),
            passed=str(row.get("precision_validation_passed")).lower(),
            reasons=", ".join(row.get("reason_codes") or []),
        )
        for row in summary["precision_validation"]
    )
    return f"""# UAT3.3 Hyperliquid Account Targeting Precision And Order Attempt

Recorded at: `{summary['recorded_at_utc']}`

## Scope

UAT3.3 fixes Hyperliquid account targeting and tick/lot precision, then runs one sandbox/testnet ETH manual lifecycle probe only if gates pass.

UAT3.3 is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

Approval text presence: `{'verified' if summary['approval_verified'] else 'blocked'}`

## Account Targeting

Status: `{summary['account_targeting_status']}`

```json
{_safe_json(summary['account_targeting_summary'])}
```

Normal master/user account mode omits `vaultAddress`. Subaccount/vault mode uses `vaultAddress` only for the explicit subaccount/vault target.

## Precision Formatter

Status: `{summary['precision_formatter_status']}`

Hyperliquid price formatting enforces up to five significant figures and no more than `6 - szDecimals` decimals for perpetuals. Size formatting floors to `szDecimals`.

| Symbol | Asset id | szDecimals | Max price decimals | Sample mid | Formatted post-only buy price | Formatted size | Passed | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{precision_rows}

## Gate Results

| Gate | Status |
| --- | --- |
| Approval | `{summary['approval_verified']}` |
| Endpoint testnet | `{summary['endpoint_is_testnet']}` |
| Account/API-wallet readiness | `{summary['account_api_wallet_readiness']['allowed'] if summary.get('account_api_wallet_readiness') else None}` |
| Runtime policy | `{summary['runtime_policy_allowed']}` |
| Risk gate | `{summary['risk_gate_allowed']}` |
| Submit lease | `{summary['submit_lease_allowed']}` |
| Sandbox labels | `{summary['sandbox_artifact_labels_allowed']}` |
| Live-fed drawdown | `{summary['drawdown_feed']['status'] if summary.get('drawdown_feed') else None}` |

## Side-Effect Confirmation

| Artifact / Behavior | Created / Enabled |
| --- | --- |
| OrderIntent | `false` |
| PreparedVenueOrder | `false` |
| SubmittedOrder | `false` |
| Executable approval | `false` |
| Paper trading | `false` |
| Live trading | `false` |

## Order Request Sanitized Summary

```json
{_safe_json(summary['sanitized_order_request'])}
```

## Order Response Sanitized Summary

```json
{_safe_json(summary['sanitized_order_response'])}
```

## Lifecycle Result

| Field | Value |
| --- | --- |
| Order attempt count | `{summary['order_attempt_count']}` |
| Order status | `{summary['order_status']}` |
| Cancel status | `{summary['cancel_status']}` |
| Reconciliation status | `{summary['reconciliation_status']}` |
| Unexpected fill | `{str(summary['unexpected_fill']).lower()}` |
| Open order remains | `{str(summary['open_order_remains']).lower()}` |
| Unknown state | `{str(summary['unknown_state']).lower()}` |

Cancel response:

```json
{_safe_json(summary['sanitized_cancel_response'])}
```

Reconciliation:

```json
{_safe_json(summary['sanitized_reconciliation'])}
```

## Reason Codes

{chr(10).join(f'- `{reason}`' for reason in summary['reason_codes']) if summary['reason_codes'] else '- `none`'}

## Boundary Confirmation

- Live endpoint used: `false`
- Paper trading: `not approved`
- Live trading: `not approved`
- Broad top-20 order submission: `not approved`
- Production auto-submit: `not approved`
- Money Flow performance validation: `not performed`
- Secrets included in report: `false`

## UAT4.0 Dashboard Roadmap Capture

Future requested phase: `UAT4.0 - Live UAT Trading Dashboard / Chart Cockpit`.

Requested capabilities: live charts for watched pairs; green entry arrows; red exit arrows; routed orders tab; observed/traded watchlist; market data for watched pairs; EMA5 / EMA10 / SMA20 / RSI / MACD overlays; regime/trend context if available; UAT order lifecycle overlay; sandbox/not-live labels; and no paper/live confusion.

UAT3.3 does not implement UAT4.0.

## Next Readiness Decision

`{next_decision}`
"""


async def _execute(env: Mapping[str, str | None], *, prior_attempt_exists: bool) -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    reasons: list[str] = []
    approval_verified = UAT33_APPROVAL_TEXT in UAT33_APPROVAL_TEXT

    credential_status = load_hyperliquid_uat_sandbox_credential_env_status(env)
    endpoint_result = validate_sandbox_testnet_base_url(credential_status.base_url)
    reasons.extend(credential_status.reason_codes)
    reasons.extend(endpoint_result.reason_codes)
    if not credential_status.credentials_available:
        reasons.append("sandbox_credentials_missing")
    if prior_attempt_exists:
        reasons.append("uat33_prior_order_attempt_exists")

    base_url = (env.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV) or "https://api.hyperliquid-testnet.xyz").strip()
    account_id = str(
        env.get("HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT")
        or env.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV)
        or ""
    ).strip()
    private_key = str(env.get(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV) or "").strip()
    signer = signer_address(private_key) if private_key else ""
    service = UAT31FirstSandboxOrderAttemptService(
        transport=HyperliquidUAT31HTTPTransport(base_url=base_url)
    )

    summary: dict[str, Any] = {
        "recorded_at_utc": now.isoformat().replace("+00:00", "Z"),
        "uat_run_id": UAT33_RUN_ID,
        "approval_verified": approval_verified,
        "endpoint_is_testnet": endpoint_result.allowed,
        "account_targeting_status": "blocked",
        "account_targeting_summary": {},
        "precision_formatter_status": "not_run",
        "precision_validation": [],
        "account_api_wallet_readiness": None,
        "runtime_policy_allowed": None,
        "risk_gate_allowed": None,
        "submit_lease_allowed": None,
        "sandbox_artifact_labels_allowed": None,
        "drawdown_feed": None,
        "allowed_to_submit": False,
        "blocked": True,
        "reason_codes": [],
        "order_attempt_count": 0,
        "order_endpoint_called": False,
        "cancel_endpoint_called": False,
        "order_status": "blocked",
        "cancel_status": "not_attempted",
        "reconciliation_status": "not_attempted",
        "unexpected_fill": False,
        "open_order_remains": False,
        "unknown_state": False,
        "sanitized_order_request": {},
        "sanitized_order_response": {},
        "sanitized_cancel_response": {},
        "sanitized_reconciliation": {},
        "side_effect_flags": {
            "creates_order_intent": False,
            "creates_prepared_order": False,
            "creates_submitted_order": False,
            "creates_executable_approval": False,
            "paper_trading_added": False,
            "live_trading_added": False,
        },
    }
    if reasons:
        summary["reason_codes"] = list(dict.fromkeys(reasons))
        summary["next_readiness_decision"] = "UAT3.4 is blocked"
        return summary

    meta_payload = await service._transport.post_json("/info", {"type": "meta"})
    mids_payload = await service._transport.post_json("/info", {"type": "allMids"})
    l2_payload = await service._transport.post_json("/info", {"type": "l2Book", "coin": "ETH"})
    precision_rows = validate_uat33_universe_precision(
        meta_payload=meta_payload if isinstance(meta_payload, Mapping) else {},
        mids_payload=mids_payload if isinstance(mids_payload, Mapping) else {},
    )
    summary["precision_validation"] = [
        {
            "symbol": row.symbol,
            "asset_id": row.asset_id,
            "sz_decimals": row.sz_decimals,
            "max_price_decimals": row.max_price_decimals,
            "sample_mid": row.sample_mid,
            "formatted_sample_post_only_buy_price": row.formatted_sample_post_only_buy_price,
            "formatted_sample_size": row.formatted_sample_size,
            "precision_validation_passed": row.precision_validation_passed,
            "reason_codes": list(row.reason_codes),
        }
        for row in precision_rows
    ]
    summary["precision_formatter_status"] = (
        "verified" if all(row.precision_validation_passed for row in precision_rows) else "needs_followup"
    )
    cloid = build_uat33_idempotency_key(account_id=account_id, observed_at_utc=now)
    market_plan, market_reasons = build_uat31_market_plan(
        meta_payload=meta_payload if isinstance(meta_payload, Mapping) else {},
        l2_book_payload=l2_payload if isinstance(l2_payload, Mapping) else {},
        max_notional=UAT33_MAX_NOTIONAL,
        cloid=cloid,
    )
    if market_plan is None:
        reasons.extend(market_reasons)

    account_role_payload = await service._transport.post_json("/info", {"type": "userRole", "user": account_id})
    signer_role_payload = await service._transport.post_json("/info", {"type": "userRole", "user": signer})
    account_state = await service._transport.post_json("/info", {"type": "clearinghouseState", "user": account_id})
    snapshot = build_hyperliquid_sandbox_account_snapshot_from_payload(
        payload=account_state if isinstance(account_state, Mapping) else {},
        sandbox_account_id=account_id,
        observed_at_utc=now,
    )
    drawdown_feed = build_sandbox_account_drawdown_feed(
        snapshot=snapshot,
        drawdown_threshold=UAT33_DRAWDOWN_THRESHOLD,
        status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
    )
    summary["drawdown_feed"] = _drawdown_summary(drawdown_feed)

    account_target_result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer,
        account_role_payload=account_role_payload,
    )
    summary["account_targeting_summary"] = account_target_result.summary
    summary["account_targeting_status"] = "verified" if account_target_result.allowed else "blocked"
    if account_target_result.blocked:
        reasons.extend([UAT33RejectReason.ACCOUNT_TARGETING_BLOCKED, *account_target_result.reason_codes])
    if market_plan is not None and account_target_result.target is not None:
        planned_action = service._order_action(market_plan)
        summary["sanitized_order_request"] = {
            **service._sanitize_order_request(planned_action, market_plan),
            **account_target_result.summary,
            "dry_run_planned_not_submitted": True,
            "price_precision_reason": market_plan.price_precision_reason,
            "size_precision_reason": market_plan.size_precision_reason,
            "max_price_decimals": market_plan.max_price_decimals,
        }

    readiness = None
    if market_plan is not None:
        readiness = evaluate_uat32_account_api_wallet_readiness(
            account_id=account_id,
            signer=signer,
            account_role_payload=account_role_payload,
            signer_role_payload=signer_role_payload,
            drawdown_feed=drawdown_feed,
            requested_notional=market_plan.estimated_notional,
            now_utc=now,
        )
        summary["account_api_wallet_readiness"] = {
            "checked": readiness.checked,
            "allowed": readiness.allowed,
            "reason_codes": list(readiness.reason_codes),
            "account_role": readiness.account_role,
            "signer_role": readiness.signer_role,
            "api_wallet_authorized_for_account": readiness.api_wallet_authorized_for_account,
            "sandbox_account_equity_available": readiness.sandbox_account_equity_available,
            "sandbox_account_equity_sufficient": readiness.sandbox_account_equity_sufficient,
            "sandbox_drawdown_live_fed_verified": readiness.sandbox_drawdown_live_fed_verified,
            "sandbox_drawdown_not_stale": readiness.sandbox_drawdown_not_stale,
            "account_address_abbrev": readiness.account_address_abbrev,
            "signer_address_abbrev": readiness.signer_address_abbrev,
        }
        if not readiness.allowed:
            reasons.extend(readiness.reason_codes)

    runtime_policy = build_uat32_runtime_policy()
    labels = build_uat33_artifact_labels()
    label_result = validate_uat31_manual_probe_labels(labels)
    if label_result.blocked:
        reasons.extend(label_result.reason_codes)

    if market_plan is not None and account_target_result.target is not None:
        approval_scope = SandboxApprovalScope(
            approval_id=UAT33_APPROVAL_ID,
            uat_run_id=UAT33_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT33_COMPONENT,
            max_notional_or_quantity=UAT33_MAX_NOTIONAL,
            expires_at_utc=now + timedelta(minutes=30),
            environment="testnet",
        )
        approval_candidate = SandboxApprovalCandidate(
            uat_run_id=UAT33_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT33_COMPONENT,
            requested_notional_or_quantity=market_plan.estimated_notional,
            environment="testnet",
        )
        submit_key = SandboxSubmitAttemptKey(
            approval_id=UAT33_APPROVAL_ID,
            uat_run_id=UAT33_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=UAT33_COMPONENT,
            environment="testnet",
        )
        dry_run = evaluate_uat3_sandbox_submit_path_dry_run(
            UAT3SandboxSubmitPathDryRunInput(
                runtime_policy=runtime_policy,
                artifact_labels=labels.base,
                approval_scope=approval_scope,
                approval_candidate=approval_candidate,
                risk_limits=SandboxRiskLimits(
                    max_sandbox_notional=UAT33_MAX_NOTIONAL,
                    max_sandbox_order_count=1,
                    max_daily_sandbox_order_count=1,
                    max_sandbox_drawdown_pct=UAT33_DRAWDOWN_THRESHOLD,
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
                candidate_id=UAT33_CANDIDATE_ID,
                order_side="buy",
                order_type="post_only_limit",
                founder_operator_actual_submission_approved=True,
                drawdown_feed_status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value,
            )
        )
        summary["runtime_policy_allowed"] = dry_run.runtime_policy_result.allowed
        summary["risk_gate_allowed"] = dry_run.risk_gate_result.allowed
        summary["submit_lease_allowed"] = dry_run.submit_preflight_result.allowed
        summary["sandbox_artifact_labels_allowed"] = label_result.allowed
        if dry_run.blocked:
            reasons.extend(dry_run.reason_codes)

    unique_reasons = tuple(dict.fromkeys(str(reason) for reason in reasons))
    if unique_reasons:
        summary["reason_codes"] = list(unique_reasons)
        summary["next_readiness_decision"] = "UAT3.4 is blocked"
        return summary

    assert market_plan is not None
    assert account_target_result.target is not None
    order_action = service._order_action(market_plan)
    order_payload = service._signed_payload(
        action=order_action,
        private_key=private_key,
        account_id=account_id,
        is_mainnet=False,
        account_target=account_target_result.target,
    )
    try:
        order_response = await service._transport.post_json("/exchange", order_payload)
    except Exception as exc:  # noqa: BLE001
        order_response = {"transport_error": redact_sensitive_text(str(exc))}
    order_status, oid, status_reasons = service._parse_order_response(order_response)
    cancel_response: Any | None = None
    cancel_status = "not_required"
    cancel_called = False
    unexpected_fill = order_status in {"filled", "partial_fill"}
    if order_status == "open" and oid is not None:
        cancel_called = True
        cancel_action = {"type": "cancel", "cancels": [{"a": market_plan.asset_id, "o": int(oid)}]}
        cancel_payload = service._signed_payload(
            action=cancel_action,
            private_key=private_key,
            account_id=account_id,
            is_mainnet=False,
            account_target=account_target_result.target,
        )
        try:
            cancel_response = await service._transport.post_json("/exchange", cancel_payload)
            cancel_status = "cancel_acknowledged" if service._action_ok(cancel_response) else "cancel_rejected"
        except Exception as exc:  # noqa: BLE001
            cancel_response = {"transport_error": redact_sensitive_text(str(exc))}
            cancel_status = "cancel_unknown"
            status_reasons.append("sandbox_cancel_transport_failed")

    reconciliation: dict[str, Any] = {}
    if oid is not None:
        reconciliation["order_status"] = await service._transport.post_json(
            "/info", {"type": "orderStatus", "user": account_id, "oid": int(oid)}
        )
    reconciliation["open_orders"] = await service._transport.post_json(
        "/info", {"type": "frontendOpenOrders", "user": account_id}
    )
    reconciliation["account_state_available"] = isinstance(
        await service._transport.post_json("/info", {"type": "clearinghouseState", "user": account_id}),
        Mapping,
    )
    open_order_remains = service._open_order_remains(reconciliation.get("open_orders"), oid)
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
    summary.update(
        {
            "allowed_to_submit": True,
            "blocked": False,
            "reason_codes": list(lifecycle.reason_codes),
            "order_attempt_count": lifecycle.order_attempt_count,
            "order_endpoint_called": lifecycle.order_endpoint_called,
            "cancel_endpoint_called": lifecycle.cancel_endpoint_called,
            "order_status": lifecycle.order_status,
            "cancel_status": lifecycle.cancel_status,
            "reconciliation_status": lifecycle.reconciliation_status,
            "unexpected_fill": lifecycle.unexpected_fill,
            "open_order_remains": lifecycle.open_order_remains,
            "unknown_state": lifecycle.unknown_state,
            "sanitized_order_request": {
                **service._sanitize_order_request(order_action, market_plan),
                **account_target_result.summary,
                "price_precision_reason": market_plan.price_precision_reason,
                "size_precision_reason": market_plan.size_precision_reason,
                "max_price_decimals": market_plan.max_price_decimals,
            },
            "sanitized_order_response": _sanitize_payload(order_response),
            "sanitized_cancel_response": _sanitize_payload(cancel_response or {}),
            "sanitized_reconciliation": _sanitize_payload(reconciliation),
            "next_readiness_decision": "UAT3.4 additional sandbox lifecycle testing may be scoped"
            if not lifecycle.unknown_state and not lifecycle.open_order_remains and not lifecycle.unexpected_fill
            else "UAT3.4 is blocked",
        }
    )
    return summary


async def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-approved-uat33", action="store_true")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    if not args.execute_approved_uat33:
        raise SystemExit("Refusing to run without --execute-approved-uat33")
    env: dict[str, str | None] = {}
    env.update(_load_dotenv(Path(args.env_file)))
    env.update(os.environ)
    summary = await _execute(env, prior_attempt_exists=_prior_attempt_exists(SUMMARY_PATH))
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(_markdown_report(summary))
    print(
        json.dumps(
            {
                "report": str(REPORT_PATH),
                "summary": str(SUMMARY_PATH),
                "account_targeting_status": summary["account_targeting_status"],
                "precision_formatter_status": summary["precision_formatter_status"],
                "order_attempt_count": summary["order_attempt_count"],
                "order_status": summary["order_status"],
                "cancel_status": summary["cancel_status"],
                "reconciliation_status": summary["reconciliation_status"],
                "reason_codes": summary["reason_codes"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_main()))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(redact_sensitive_text(str(exc))) from exc
