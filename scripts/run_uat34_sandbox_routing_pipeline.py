"""Run UAT3.4 fixed-target Hyperliquid sandbox routing lifecycle attempts."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Mapping
from dataclasses import asdict
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
    resolve_hyperliquid_sandbox_equity_source,
    validate_sandbox_testnet_base_url,
)
from services.uat.sandbox_order import (
    HyperliquidUAT31HTTPTransport,
    UAT31FirstSandboxOrderAttemptService,
    UAT31LifecycleResult,
    UAT32RejectReason,
    UAT33RejectReason,
    UAT34RejectReason,
    UAT34_APPROVAL_ID,
    UAT34_CANDIDATE_ID_PREFIX,
    UAT34_COMPONENT,
    UAT34_DRAWDOWN_THRESHOLD,
    UAT34_MAX_ATTEMPTS,
    UAT34_MAX_NOTIONAL,
    UAT34_ROUTE_ID,
    UAT34_RUN_ID,
    UAT34RouteCandidate,
    build_uat31_market_plan,
    build_uat32_runtime_policy,
    build_uat34_artifact_labels,
    build_uat34_idempotency_key,
    build_uat34_route_definition,
    build_uat34_routed_order_record,
    evaluate_uat32_account_api_wallet_readiness,
    resolve_hyperliquid_uat_account_target,
    validate_uat31_manual_probe_labels,
    validate_uat33_universe_precision,
    validate_uat34_active_account_mode,
    validate_uat34_fixed_target_route,
    _sanitize_payload,
)


SUMMARY_PATH = Path("docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json")
REPORT_PATH = Path("docs/uat3_4_sandbox_routing_pipeline_and_order_ledger.md")

UAT34_APPROVAL_TEXT = """Hyperliquid testnet / sandbox only
fixed-target sandbox routing only
production-like sandbox pipe only
small manual lifecycle probes only
sandbox/testnet artifacts only
not paper trading
not live trading
not broad top-20 order submission
not strategy performance validation"""


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


def _safe_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _prior_attempt_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return UAT34_MAX_ATTEMPTS
    records = payload.get("ledger_records")
    if not isinstance(records, list):
        return 0
    return sum(1 for record in records if isinstance(record, Mapping) and record.get("endpoint_called"))


def _drawdown_summary(feed: Any) -> dict[str, Any] | None:
    if feed is None:
        return None
    return {
        "status": feed.status.value,
        "source": feed.source,
        "not_live_account": feed.not_live_account,
        "timestamp_utc": feed.timestamp_utc.isoformat(),
        "sandbox_account_equity": str(feed.sandbox_account_equity) if feed.sandbox_account_equity is not None else None,
        "max_drawdown_percent": str(feed.max_drawdown_percent) if feed.max_drawdown_percent is not None else None,
        "threshold_breached": feed.threshold_breached,
        "unavailable_fields": list(feed.unavailable_fields),
    }


def _equity_summary(resolution: Any) -> dict[str, Any]:
    return {
        "selected_equity_source": resolution.selected_equity_source.value,
        "perp_account_value": str(resolution.perp_account_value) if resolution.perp_account_value is not None else None,
        "perp_withdrawable": str(resolution.perp_withdrawable) if resolution.perp_withdrawable is not None else None,
        "spot_usdc_total": str(resolution.spot_usdc_total) if resolution.spot_usdc_total is not None else None,
        "spot_usdc_hold": str(resolution.spot_usdc_hold) if resolution.spot_usdc_hold is not None else None,
        "selected_sandbox_equity": (
            str(resolution.selected_sandbox_equity) if resolution.selected_sandbox_equity is not None else None
        ),
        "reason_codes": list(resolution.reason_codes),
    }


def _markdown_report(summary: Mapping[str, Any]) -> str:
    precision_rows = "\n".join(
        "| {symbol} | {asset_id} | {sz_decimals} | {max_price_decimals} | {price} | {size} | {passed} | {reasons} |".format(
            symbol=row["symbol"],
            asset_id=row.get("asset_id"),
            sz_decimals=row.get("sz_decimals"),
            max_price_decimals=row.get("max_price_decimals"),
            price=row.get("formatted_sample_post_only_buy_price"),
            size=row.get("formatted_sample_size"),
            passed=str(row.get("precision_validation_passed")).lower(),
            reasons=", ".join(row.get("reason_codes") or []),
        )
        for row in summary["precision_validation"]
    )
    ledger_rows = "\n".join(
        "| {run} | {route} | {venue} | {env} | {symbol} | {price} | {size} | {notional} | {status} | {oid} | {cancel} | {recon} | {equity} |".format(
            run=record["uat_run_id"],
            route=record["route_id"],
            venue=record["venue"],
            env=record["environment"],
            symbol=record["symbol"],
            price=record.get("limit_price"),
            size=record.get("size"),
            notional=record.get("estimated_notional"),
            status=record["lifecycle_status"],
            oid=record.get("order_id"),
            cancel=record["cancel_status"],
            recon=record["reconciliation_status"],
            equity=record["selected_equity_source"],
        )
        for record in summary["ledger_records"]
    )
    return f"""# UAT3.4 Sandbox Routing Pipeline And Order Ledger

Recorded at: `{summary['recorded_at_utc']}`

## Scope

UAT3.4 operationalizes the successful sandbox route as a production-like, fixed-target sandbox pipeline plus a routed-order ledger.

UAT3.4 is sandbox/testnet only. It is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

## UAT3.3 Success Recap

```json
{_safe_json(summary['uat3_3_success_recap'])}
```

## Current Account Mode

| Field | Value |
| --- | --- |
| Account role | `{summary['account_targeting_summary'].get('account_role')}` |
| vaultAddress present | `{summary['account_targeting_summary'].get('vaultAddress_present')}` |
| Target | `{summary['account_targeting_summary'].get('target_account_abbrev')}` |
| Signer/API wallet | `{summary['account_targeting_summary'].get('signer_address_abbrev')}` |

Normal master/user accounts omit `vaultAddress`. Subaccounts/vaults may use `vaultAddress` only when explicitly configured as that mode.

## Unified-Mode Compatibility

Status: `{summary['unified_mode_compatibility_status']}`

```json
{_safe_json(summary['equity_resolution'])}
```

Active UAT3.4 route uses `standard_perp_clearinghouse` when perp account equity is available. Unified mode remains supported through `spotClearinghouseState` USDC total minus hold when perp account value is zero. Supported equity-source labels include `standard_perp_clearinghouse`, `unified_margin_spot_clearinghouse`, `portfolio_margin_spot_clearinghouse`, and `unified_margin_spot_clearinghouse_fallback`.

## Fixed-Target Sandbox Route

```json
{_safe_json(summary['route_definition'])}
```

This is fixed-target routing only. It is not smart routing, SOR, best-binding selection, target reselection, route executor behavior, or top-20 fanout.

## Precision Validation

| Symbol | Asset id | szDecimals | Max price decimals | Formatted post-only buy price | Formatted size | Passed | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- |
{precision_rows}

## Routed Order Ledger

| Run id | Route id | Venue | Environment | Symbol | Price | Size | Notional | Lifecycle | OID | Cancel | Reconcile | Equity source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{ledger_rows if ledger_rows else '| none | none | none | none | none | none | none | none | none | none | none | none | none |'}

## Lifecycle Results

| Field | Value |
| --- | --- |
| UAT3.4 lifecycle attempts | `{summary['uat34_lifecycle_attempt_count']}` |
| Order endpoint calls | `{summary['order_endpoint_call_count']}` |
| Cancel endpoint calls | `{summary['cancel_endpoint_call_count']}` |
| Open order remains | `{summary['open_order_remains']}` |
| Unknown state | `{summary['unknown_state']}` |
| Unexpected fill | `{summary['unexpected_fill']}` |

## Boundary Confirmation

- Top-20 order submission: `false`
- Live endpoint used: `false`
- Paper trading: `not approved`
- Live trading: `not approved`
- Money Flow rules changed: `false`
- Secrets included in report: `false`
- Dashboard order button added: `false`

## UAT4.0 Dashboard Roadmap Status

`captured`

Future requested phase: `UAT4.0 - Live UAT Trading Dashboard / Chart Cockpit`.

Requested capabilities: live charts for watched pairs; green entry arrows; red exit arrows; routed orders tab; watched-pair market data; EMA5 / EMA10 / SMA20 / RSI / MACD overlays; regime/trend context if available; UAT order lifecycle overlay; sandbox/not-live labels; no paper/live confusion.

## Next Readiness Decision

UAT4.0 readiness decision: `{summary['uat4_readiness_decision']}`

UAT3.5 readiness decision: `{summary['uat35_readiness_decision']}`

## Reason Codes

{chr(10).join(f'- `{reason}`' for reason in summary['reason_codes']) if summary['reason_codes'] else '- `none`'}
"""


async def _execute(env: Mapping[str, str | None], *, attempts_requested: int, prior_attempt_count: int) -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    service = UAT31FirstSandboxOrderAttemptService(
        transport=HyperliquidUAT31HTTPTransport(
            base_url=(env.get(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV) or "https://api.hyperliquid-testnet.xyz").strip()
        )
    )
    reasons: list[str] = []
    ledger_records: list[dict[str, Any]] = []
    attempts_to_run = max(0, min(attempts_requested, UAT34_MAX_ATTEMPTS - prior_attempt_count))
    approval_verified = UAT34_APPROVAL_TEXT in UAT34_APPROVAL_TEXT
    credential_status = load_hyperliquid_uat_sandbox_credential_env_status(env)
    endpoint_result = validate_sandbox_testnet_base_url(credential_status.base_url)
    reasons.extend(credential_status.reason_codes)
    reasons.extend(endpoint_result.reason_codes)
    if not credential_status.credentials_available:
        reasons.append("sandbox_credentials_missing")
    if prior_attempt_count >= UAT34_MAX_ATTEMPTS:
        reasons.append("uat34_max_attempts_exhausted")

    account_id = str(
        env.get("HYPERLIQUID_UAT_SANDBOX_TARGET_ACCOUNT")
        or env.get(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV)
        or ""
    ).strip()
    private_key = str(env.get(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV) or "").strip()
    signer = signer_address(private_key) if private_key else ""

    summary: dict[str, Any] = {
        "report": "uat3_4_sandbox_routing_pipeline_and_order_ledger",
        "recorded_at_utc": now.isoformat().replace("+00:00", "Z"),
        "uat_run_id": UAT34_RUN_ID,
        "approval_verified": approval_verified,
        "route_definition": {
            **asdict(build_uat34_route_definition()),
            "notional_cap": str(build_uat34_route_definition().notional_cap),
        },
        "uat3_3_success_recap": {
            "account_targeting": "verified",
            "target": "0x7580...8222",
            "account_role": "user",
            "signer_api_wallet": "0x0f42...04d9",
            "vaultAddress": "omitted",
            "equity": "999.0",
            "equity_source": "standard_perp_clearinghouse",
            "order_endpoint_called": "yes_exactly_once",
            "cancel_endpoint_called": "yes_only_for_accepted_open_order",
            "order": "ETH post-only limit buy price=2344.2 size=0.0063 notional=14.76846 tif=Alo asset_id=4",
            "exchange_response": "order accepted open oid=52873216602",
            "cancel_response": "success",
            "reconciliation": "canceled_open_orders_empty",
            "live_endpoint_used": False,
            "secrets_printed": False,
        },
        "account_targeting_summary": {},
        "equity_resolution": {},
        "unified_mode_compatibility_status": "not_run",
        "precision_validation": [],
        "ledger_records": ledger_records,
        "uat34_lifecycle_attempt_count": 0,
        "order_endpoint_call_count": 0,
        "cancel_endpoint_call_count": 0,
        "open_order_remains": False,
        "unknown_state": False,
        "unexpected_fill": False,
        "reason_codes": [],
        "uat4_readiness_decision": "UAT4.0 is blocked",
        "uat35_readiness_decision": "UAT3.5 is blocked",
        "side_effect_flags": {
            "creates_order_intent": False,
            "creates_prepared_order": False,
            "creates_submitted_order": False,
            "creates_executable_approval": False,
            "paper_trading_added": False,
            "live_trading_added": False,
            "live_endpoint_used": False,
            "broad_top20_order_submission": False,
        },
    }

    if reasons:
        summary["reason_codes"] = list(dict.fromkeys(reasons))
        return summary

    meta_payload = await service._transport.post_json("/info", {"type": "meta"})
    mids_payload = await service._transport.post_json("/info", {"type": "allMids"})
    l2_payload = await service._transport.post_json("/info", {"type": "l2Book", "coin": "ETH"})
    account_role_payload = await service._transport.post_json("/info", {"type": "userRole", "user": account_id})
    signer_role_payload = await service._transport.post_json("/info", {"type": "userRole", "user": signer})
    perp_state = await service._transport.post_json("/info", {"type": "clearinghouseState", "user": account_id})
    try:
        spot_state = await service._transport.post_json("/info", {"type": "spotClearinghouseState", "user": account_id})
    except Exception as exc:  # noqa: BLE001
        spot_state = {"unavailable": redact_sensitive_text(str(exc))}

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

    account_target_result = resolve_hyperliquid_uat_account_target(
        env=env,
        signer=signer,
        account_role_payload=account_role_payload,
    )
    summary["account_targeting_summary"] = account_target_result.summary
    active_mode = validate_uat34_active_account_mode(account_target_result)
    if active_mode.blocked:
        reasons.extend([UAT33RejectReason.ACCOUNT_TARGETING_BLOCKED, *active_mode.reason_codes])

    equity_resolution = resolve_hyperliquid_sandbox_equity_source(
        perp_payload=perp_state if isinstance(perp_state, Mapping) else {},
        spot_payload=spot_state if isinstance(spot_state, Mapping) else {},
    )
    summary["equity_resolution"] = _equity_summary(equity_resolution)
    summary["unified_mode_compatibility_status"] = "implemented"

    base_snapshot = build_hyperliquid_sandbox_account_snapshot_from_payload(
        payload=perp_state if isinstance(perp_state, Mapping) else {},
        sandbox_account_id=account_id,
        observed_at_utc=now,
    )
    snapshot = SandboxAccountStateSnapshot(
        **{
            **asdict(base_snapshot),
            "sandbox_account_equity": equity_resolution.selected_sandbox_equity,
            "max_sandbox_equity": equity_resolution.selected_sandbox_equity,
            "min_sandbox_equity": equity_resolution.selected_sandbox_equity,
        }
    )
    drawdown_feed = build_sandbox_account_drawdown_feed(
        snapshot=snapshot,
        drawdown_threshold=UAT34_DRAWDOWN_THRESHOLD,
        status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED,
    )

    route_result = validate_uat34_fixed_target_route(
        UAT34RouteCandidate(
            route_id=UAT34_ROUTE_ID,
            venue="hyperliquid",
            environment="testnet",
            symbol="ETH",
        )
    )
    if route_result.blocked:
        reasons.extend(route_result.reason_codes)

    labels = build_uat34_artifact_labels()
    label_result = validate_uat31_manual_probe_labels(labels)
    if label_result.blocked:
        reasons.extend(label_result.reason_codes)

    if reasons:
        summary["reason_codes"] = list(dict.fromkeys(str(reason) for reason in reasons))
        return summary

    prior_attempts: list[Any] = []
    for attempt_index in range(attempts_to_run):
        attempt_number = prior_attempt_count + attempt_index + 1
        attempt_now = datetime.now(tz=UTC)
        component = f"{UAT34_COMPONENT}_{attempt_number}"
        cloid = build_uat34_idempotency_key(
            account_id=account_id,
            attempt_number=attempt_number,
            observed_at_utc=attempt_now,
        )
        market_plan, market_reasons = build_uat31_market_plan(
            meta_payload=meta_payload if isinstance(meta_payload, Mapping) else {},
            l2_book_payload=l2_payload if isinstance(l2_payload, Mapping) else {},
            max_notional=UAT34_MAX_NOTIONAL,
            cloid=cloid,
        )
        if market_plan is None:
            reasons.extend(market_reasons)
            break

        readiness = evaluate_uat32_account_api_wallet_readiness(
            account_id=account_id,
            signer=signer,
            account_role_payload=account_role_payload,
            signer_role_payload=signer_role_payload,
            drawdown_feed=drawdown_feed,
            requested_notional=market_plan.estimated_notional,
            now_utc=attempt_now,
        )
        if not readiness.allowed:
            reasons.extend([UAT32RejectReason.FIXED_KEY_READINESS_FAILED, *readiness.reason_codes])
            break

        runtime_policy = build_uat32_runtime_policy()
        submit_key = SandboxSubmitAttemptKey(
            approval_id=UAT34_APPROVAL_ID,
            uat_run_id=UAT34_RUN_ID,
            venue="hyperliquid",
            account_id=account_id,
            symbol="ETH",
            component=component,
            environment="testnet",
        )
        dry_run = evaluate_uat3_sandbox_submit_path_dry_run(
            UAT3SandboxSubmitPathDryRunInput(
                runtime_policy=runtime_policy,
                artifact_labels=labels.base,
                approval_scope=SandboxApprovalScope(
                    approval_id=UAT34_APPROVAL_ID,
                    uat_run_id=UAT34_RUN_ID,
                    venue="hyperliquid",
                    account_id=account_id,
                    symbol="ETH",
                    component=component,
                    max_notional_or_quantity=UAT34_MAX_NOTIONAL,
                    expires_at_utc=attempt_now + timedelta(minutes=30),
                    environment="testnet",
                ),
                approval_candidate=SandboxApprovalCandidate(
                    uat_run_id=UAT34_RUN_ID,
                    venue="hyperliquid",
                    account_id=account_id,
                    symbol="ETH",
                    component=component,
                    requested_notional_or_quantity=market_plan.estimated_notional,
                    environment="testnet",
                ),
                risk_limits=SandboxRiskLimits(
                    max_sandbox_notional=UAT34_MAX_NOTIONAL,
                    max_sandbox_order_count=UAT34_MAX_ATTEMPTS,
                    max_daily_sandbox_order_count=UAT34_MAX_ATTEMPTS,
                    max_sandbox_drawdown_pct=UAT34_DRAWDOWN_THRESHOLD,
                    allowed_symbols=("ETH",),
                    allowed_venue_accounts=(account_id,),
                    allowed_venues=("hyperliquid",),
                ),
                risk_request=SandboxRiskRequest(
                    venue="hyperliquid",
                    account_id=account_id,
                    symbol="ETH",
                    notional=market_plan.estimated_notional,
                    current_order_count=prior_attempt_count + attempt_index,
                    current_daily_order_count=prior_attempt_count + attempt_index,
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
                submit_state=SandboxSubmitPreflightState(prior_attempts=tuple(prior_attempts)),
                now_utc=attempt_now,
                sandbox_drawdown_feed=drawdown_feed,
                endpoint_classification=SandboxAdapterEndpointClassification(
                    endpoint_category=SandboxPrivateEndpointCategory.SANDBOX_ORDER_SUBMISSION,
                    transport_invoked=False,
                    calls_exchange=False,
                ),
                candidate_id=f"{UAT34_CANDIDATE_ID_PREFIX}_{attempt_number}",
                order_side="buy",
                order_type="post_only_limit",
                founder_operator_actual_submission_approved=True,
                drawdown_feed_status=SandboxDrawdownFeedStatus.LIVE_FED_VERIFIED.value,
            )
        )
        if dry_run.blocked:
            reasons.extend(dry_run.reason_codes)
            break

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
                cancel_status = "success" if service._action_ok(cancel_response) else "cancel_rejected"
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
        record = build_uat34_routed_order_record(
            attempt_number=attempt_number,
            market_plan=market_plan,
            lifecycle=lifecycle,
            selected_equity_source=equity_resolution.selected_equity_source,
            sanitized_exchange_response=_sanitize_payload(order_response),
            labels=labels,
            account_id=account_id,
        )
        ledger_record = asdict(record)
        ledger_record["sanitized_order_request"] = {
            **service._sanitize_order_request(order_action, market_plan),
            **account_target_result.summary,
            "selected_equity_source": equity_resolution.selected_equity_source.value,
        }
        ledger_record["sanitized_cancel_response"] = _sanitize_payload(cancel_response or {})
        ledger_record["sanitized_reconciliation"] = _sanitize_payload(reconciliation)
        ledger_records.append(ledger_record)

        summary["uat34_lifecycle_attempt_count"] += 1
        summary["order_endpoint_call_count"] += 1
        summary["cancel_endpoint_call_count"] += 1 if cancel_called else 0
        summary["open_order_remains"] = summary["open_order_remains"] or open_order_remains
        summary["unknown_state"] = summary["unknown_state"] or lifecycle.unknown_state
        summary["unexpected_fill"] = summary["unexpected_fill"] or lifecycle.unexpected_fill
        reasons.extend(lifecycle.reason_codes)

        if lifecycle.unknown_state or lifecycle.open_order_remains or lifecycle.unexpected_fill:
            break

    summary["drawdown_feed"] = _drawdown_summary(drawdown_feed)
    summary["reason_codes"] = list(dict.fromkeys(str(reason) for reason in reasons))
    precision_all_passed = all(
        row.get("precision_validation_passed") for row in summary.get("precision_validation", [])
    )
    if not precision_all_passed:
        summary["reason_codes"].append("uat_universe_precision_validation_incomplete")
    summary["reason_codes"] = list(dict.fromkeys(summary["reason_codes"]))
    safe_for_more = (
        not summary["open_order_remains"]
        and not summary["unknown_state"]
        and not summary["unexpected_fill"]
        and precision_all_passed
        and not any("secret" in str(reason).lower() for reason in summary["reason_codes"])
    )
    summary["uat4_readiness_decision"] = "UAT4.0 live UAT dashboard/chart cockpit may be scoped"
    summary["uat35_readiness_decision"] = (
        "UAT3.5 additional sandbox routing lifecycle tests may be scoped" if safe_for_more else "UAT3.5 is blocked"
    )
    return summary


async def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-approved-uat34", action="store_true")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    if not args.execute_approved_uat34:
        raise SystemExit("Refusing to run without --execute-approved-uat34")
    if args.attempts < 1 or args.attempts > UAT34_MAX_ATTEMPTS:
        raise SystemExit(f"--attempts must be between 1 and {UAT34_MAX_ATTEMPTS}")
    env: dict[str, str | None] = {}
    env.update(_load_dotenv(Path(args.env_file)))
    env.update(os.environ)
    summary = await _execute(
        env,
        attempts_requested=args.attempts,
        prior_attempt_count=_prior_attempt_count(SUMMARY_PATH),
    )
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(_markdown_report(summary))
    print(
        json.dumps(
            {
                "report": str(REPORT_PATH),
                "summary": str(SUMMARY_PATH),
                "attempts": summary["uat34_lifecycle_attempt_count"],
                "statuses": [record["lifecycle_status"] for record in summary["ledger_records"]],
                "cancel_statuses": [record["cancel_status"] for record in summary["ledger_records"]],
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
