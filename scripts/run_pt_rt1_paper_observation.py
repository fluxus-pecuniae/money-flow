"""Run PT-RT1 public-mainnet paper-observation readiness cycles.

The runner writes ignored runtime artifacts under ``reports/paper_runtime/``.
It uses only Hyperliquid public mainnet ``/info`` payloads for strategy truth
and keeps testnet probes as plumbing-only audit/order-shape rows unless a
later separately approved transport phase submits them.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence

from services.paper_runtime.hyperliquid_public_market_data import (
    HyperliquidPublicMarketDataConnector,
    candle_request_window,
    resolve_watchlist_from_public_data,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_1B_RUNTIME_OUTPUT_PREFIX,
    PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_REQUESTED_SCANNER_SYMBOLS,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC,
    PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    TIMEFRAME_DURATIONS,
    DataHealth,
    PaperDecisionEvent,
    TestnetProbeCandidate,
    TestnetProbePolicy,
    build_pt_rt1_summary,
    canonical_candle_close,
    evaluate_paper_decision,
)


DEFAULT_OUTPUT_DIR = Path("reports/paper_runtime/pt_rt1_1b_smoke")
DECISION_LOG_MODES = ("compact", "full_audit", "signals_only")
ACTIONABLE_DECISION_ACTIONS = frozenset({"paper_opened", "paper_closed"})
COMPACT_ALWAYS_WRITE_ACTIONS = frozenset({"paper_opened", "paper_closed", "data_unavailable"})
DECISION_LOG_SIZE_WARNING_BYTES = 500 * 1024 * 1024
TESTNET_PROBE_AUDIT_LIMIT = 200
PT_RT1_2_EXACT_TRANSPORT_APPROVAL = (
    "I APPROVE PT-RT1.2 HYPERLIQUID TESTNET TRANSPORT PROBES ONLY. "
    "20 USDC MAX NOTIONAL. POST-ONLY ALO. SUBMIT CANCEL RECONCILE. "
    "TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL. LIVE TRADING IS NOT APPROVED."
)


class TestnetProbeTransport(Protocol):
    def __call__(self, order_shape: dict[str, Any], audit_row: dict[str, Any]) -> dict[str, Any]:
        """Submit/cancel/reconcile one testnet plumbing probe.

        Production runtime supplies no default signed transport here. Tests may
        inject a fake transport to verify lifecycle accounting without touching
        private/signed/order endpoints.
        """


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _ensure_ignored_output_dir(path: Path) -> None:
    normalized = Path(path)
    try:
        normalized.relative_to(PT_RT1_1B_RUNTIME_OUTPUT_PREFIX)
    except ValueError as exc:
        raise SystemExit("output_directory_not_under_ignored_reports_paper_runtime") from exc
    normalized.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_json_safe(row), sort_keys=True) + "\n")


def _read_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {"state_status": "invalid_json"}
    return payload if isinstance(payload, dict) else {"state_status": "invalid_shape"}


def _lane_key(lane_id: str, symbol: str, timeframe: str) -> str:
    return f"{lane_id}|{symbol.upper()}|{timeframe}"


def _paper_signal_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("lane_id") or ""),
            str(row.get("strategy_id") or ""),
            str(row.get("symbol") or "").upper(),
            str(row.get("timeframe") or ""),
            str(row.get("signal_candle_close_time") or ""),
            "entry",
        ]
    )


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _load_paper_runtime_state(prior_state: dict[str, Any]) -> dict[str, Any]:
    runtime = prior_state.get("paper_runtime") if isinstance(prior_state, dict) else None
    if not isinstance(runtime, dict):
        runtime = {}
    processed = runtime.get("processed_signal_keys")
    if not isinstance(processed, list):
        processed = []
    open_positions = runtime.get("open_positions_by_key")
    if not isinstance(open_positions, dict):
        open_positions = {}
    realized = runtime.get("realized_equity_by_lane")
    if not isinstance(realized, dict):
        realized = {}
    return {
        "processed_signal_keys": set(str(item) for item in processed),
        "open_positions_by_key": {
            str(key): value for key, value in open_positions.items() if isinstance(value, dict)
        },
        "realized_equity_by_lane": {
            str(key): str(value) for key, value in realized.items()
        },
        "paper_opens_total": int(runtime.get("paper_opens_total") or 0),
        "paper_closes_total": int(runtime.get("paper_closes_total") or 0),
        "duplicate_signal_blocks_total": int(runtime.get("duplicate_signal_blocks_total") or 0),
        "last_processed_close_by_key": dict(runtime.get("last_processed_close_by_key") or {}),
    }


def _paper_runtime_state_payload(
    *,
    processed_signal_keys: set[str],
    open_positions_by_key: dict[str, dict[str, Any]],
    realized_equity_by_lane: dict[str, str],
    last_processed_close_by_key: dict[str, str],
    paper_opens_total: int,
    paper_closes_total: int,
    duplicate_signal_blocks_total: int,
) -> dict[str, Any]:
    return {
        "processed_signal_keys": sorted(processed_signal_keys),
        "open_positions_by_key": open_positions_by_key,
        "realized_equity_by_lane": realized_equity_by_lane,
        "last_processed_close_by_key": last_processed_close_by_key,
        "paper_opens_total": paper_opens_total,
        "paper_closes_total": paper_closes_total,
        "duplicate_signal_blocks_total": duplicate_signal_blocks_total,
        "open_positions_count": len(open_positions_by_key),
    }


def _blocked_duplicate_row(row: dict[str, Any]) -> dict[str, Any]:
    reasons = list(row.get("reason_codes") or [])
    reasons.extend(["duplicate_signal_ignored", "existing_same_candle_signal_blocked"])
    return {
        **row,
        "action": "paper_hold",
        "position_after": row.get("position_before") or "flat",
        "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons)),
        "paper_state_transition": "duplicate_open_blocked",
    }


def _open_position_from_decision(
    *,
    row: dict[str, Any],
    candle: Any,
    equity_before: Decimal,
) -> dict[str, Any]:
    fill_price = candle.close
    fee = equity_before * Decimal("5") / Decimal("10000")
    quantity = (equity_before - fee) / fill_price if fill_price > 0 else Decimal("0")
    return {
        "lane_id": row.get("lane_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": str(row.get("symbol") or "").upper(),
        "timeframe": row.get("timeframe"),
        "side": "long",
        "entry_signal_time": row.get("signal_candle_close_time"),
        "entry_fill_time": row.get("signal_candle_close_time"),
        "entry_price": str(fill_price),
        "quantity": str(quantity),
        "notional": str(equity_before),
        "fees": str(fee),
        "slippage": "0",
        "equity_before": str(equity_before),
        "open_reason_codes": list(row.get("reason_codes") or []),
        "status": "open",
        "current_unrealized_pnl": "0",
    }


def _close_position_from_decision(
    *,
    row: dict[str, Any],
    position: dict[str, Any],
    candle: Any,
) -> tuple[dict[str, Any], Decimal]:
    entry_price = _dec(position.get("entry_price"))
    quantity = _dec(position.get("quantity"))
    equity_before = _dec(position.get("equity_before"), Decimal("10000"))
    entry_fees = _dec(position.get("fees"))
    exit_price = candle.close
    gross = (exit_price - entry_price) * quantity
    exit_fee = (exit_price * quantity) * Decimal("5") / Decimal("10000")
    net_pnl = gross - entry_fees - exit_fee
    equity_after = equity_before + net_pnl
    trade = {
        "paper_trade_id": f"pt_rt1_trade_{row.get('lane_id')}_{row.get('symbol')}_{row.get('timeframe')}_{row.get('signal_candle_close_time')}",
        "lane_id": row.get("lane_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": str(row.get("symbol") or "").upper(),
        "timeframe": row.get("timeframe"),
        "entry_time": position.get("entry_fill_time"),
        "exit_time": row.get("signal_candle_close_time"),
        "entry_price": str(entry_price),
        "exit_price": str(exit_price),
        "quantity": str(quantity),
        "gross_pnl": str(gross),
        "fees": str(entry_fees + exit_fee),
        "slippage": "0",
        "net_pnl": str(net_pnl),
        "equity_before": str(equity_before),
        "equity_after": str(equity_after),
        "entry_reason_codes": list(position.get("open_reason_codes") or []),
        "exit_reason_codes": list(row.get("reason_codes") or []),
        "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
        "testnet_fills_update_strategy_pnl": False,
    }
    return trade, equity_after


def _summarize_data_unavailable(
    *,
    market_health: Sequence[dict[str, Any]],
    decision_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    market_rows = [row for row in market_health if row.get("status") != DataHealth.HEALTHY.value]
    decision_unavailable = [row for row in decision_rows if row.get("action") == "data_unavailable"]

    def rollup(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: dict[tuple[str, str, str], int] = {}
        for row in rows:
            symbol = str(row.get("symbol") or row.get("requested_symbol") or "").upper()
            timeframe = str(row.get("timeframe") or "")
            reasons = row.get("reason_codes") or ["unknown"]
            primary_reason = str(reasons[0] if isinstance(reasons, list) and reasons else "unknown")
            buckets[(symbol, timeframe, primary_reason)] = buckets.get((symbol, timeframe, primary_reason), 0) + 1
        return [
            {"symbol": symbol, "timeframe": timeframe, "reason": reason, "count": count}
            for (symbol, timeframe, reason), count in sorted(buckets.items())
        ]

    return {
        "market_rows_checked": len(market_health),
        "market_rows_unavailable": len(market_rows),
        "lane_expanded_data_unavailable_decisions": len(decision_unavailable),
        "lane_expansion_note": (
            "One unavailable public market-data row can expand into one data_unavailable decision per strategy lane."
        ),
        "market_unavailable_rollup": rollup(market_rows),
        "lane_decision_unavailable_rollup": rollup(decision_unavailable),
    }


def _decision_log_key(row: dict[str, Any]) -> str:
    reasons = ",".join(str(item) for item in row.get("reason_codes") or ())
    return "|".join(
        str(row.get(field) or "")
        for field in (
            "lane_id",
            "symbol",
            "timeframe",
            "signal_candle_close_time",
            "action",
        )
    ) + f"|{reasons}"


def _select_decision_log_rows(
    decision_rows: Sequence[dict[str, Any]],
    *,
    mode: str,
    seen_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    if mode not in DECISION_LOG_MODES:
        raise ValueError(f"unsupported_decision_log_mode:{mode}")
    seen = set(seen_keys or set())
    selected: list[dict[str, Any]] = []

    for row in decision_rows:
        action = str(row.get("action") or "")
        if mode == "full_audit":
            selected.append(row)
            continue
        if mode == "signals_only":
            if action in ACTIONABLE_DECISION_ACTIONS:
                selected.append(row)
            continue
        if action in COMPACT_ALWAYS_WRITE_ACTIONS:
            selected.append(row)
            continue
        key = _decision_log_key(row)
        if key not in seen:
            selected.append(row)
            seen.add(key)

    suppressed = max(len(decision_rows) - len(selected), 0)
    stats = {
        "mode": mode,
        "evaluated_decisions_this_cycle": len(decision_rows),
        "written_decisions_this_cycle": len(selected),
        "suppressed_decisions_this_cycle": suppressed,
        "suppression_reason": (
            "none_full_audit"
            if mode == "full_audit"
            else "only_actionable_signals_written"
            if mode == "signals_only"
            else "repeated_non_actionable_decisions_suppressed"
        ),
    }
    return selected, seen, stats


def _filter_scanner_rows(rows: Sequence[Any], symbols: Sequence[str] | None, max_candle_symbols: int | None) -> list[Any]:
    selected = []
    requested = {item.upper() for item in symbols or ()}
    for row in rows:
        candidates = {row.requested_symbol.upper(), str(row.resolved_venue_symbol or "").upper(), str(row.canonical_symbol or "").upper()}
        if requested and not (requested & candidates):
            continue
        if row.scanner_eligible and not row.blocked:
            selected.append(row)
    if max_candle_symbols is not None:
        return selected[:max_candle_symbols]
    return selected


def _closed_prefix(candles: Sequence[Any], now: datetime) -> list[Any]:
    closed = [candle for candle in candles if canonical_candle_close(candle) <= now]
    return closed


def _testnet_probe_price(candle: Any) -> Decimal:
    # Buy-side post-only plumbing probes are kept below the latest public close so
    # they validate shape/precision without trying to become marketable.
    return (candle.close * Decimal("0.95")).quantize(Decimal("0.00000001"))


def _build_testnet_probe_audit_rows(
    *,
    decision_rows: Sequence[dict[str, Any]],
    scanner_rows: Sequence[Any],
    latest_closed_by_key: dict[tuple[str, str], Any],
    enabled: bool,
    approval_text: str,
    notional_usdc: Decimal,
    daily_cap: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_by_symbol = {
        str(row.canonical_symbol or row.requested_symbol).upper(): row
        for row in scanner_rows
        if row.scanner_eligible and not row.blocked
    }
    policy = TestnetProbePolicy()
    audit_rows: list[dict[str, Any]] = []
    actionable = [row for row in decision_rows if row.get("action") == "paper_opened"]
    for index, decision in enumerate(actionable[:TESTNET_PROBE_AUDIT_LIMIT]):
        symbol = str(decision.get("symbol") or "").upper()
        timeframe = str(decision.get("timeframe") or "")
        scanner_row = row_by_symbol.get(symbol)
        candle = latest_closed_by_key.get((symbol, timeframe))
        if scanner_row is None or candle is None:
            audit_rows.append(
                {
                    "lane": "testnet_plumbing_probe",
                    "environment": "hyperliquid_testnet_only",
                    "eligible": False,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "strategy_id": decision.get("strategy_id"),
                    "signal_candle_close_time": decision.get("signal_candle_close_time"),
                    "notional_usdc": str(notional_usdc),
                    "reason_codes": ["testnet_probe_context_unavailable"],
                    "testnet_fills_update_strategy_pnl": False,
                    "strategy_pnl_updated": False,
                    "signed_order_endpoint_called": False,
                    "order_endpoint_called": False,
                    "order_shape": None,
                }
            )
            continue
        price = _testnet_probe_price(candle)
        quantity = notional_usdc / price
        result = policy.evaluate(
            TestnetProbeCandidate(
                approval_text=approval_text,
                probes_enabled=enabled,
                kill_switch=not enabled,
                symbol=str(scanner_row.resolved_venue_symbol or symbol),
                asset_id=scanner_row.asset_id,
                sz_decimals=scanner_row.szDecimals,
                price=price,
                quantity=quantity,
                notional=notional_usdc,
                scanner_signal_eligible=True,
                daily_probe_count=index,
                daily_cap=daily_cap,
                notional_cap=PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC,
                precision_ready=bool(scanner_row.precision_ready),
                scanner_symbol_blocked=bool(scanner_row.blocked),
                unit_semantics_deferred=any("unit_semantics" in reason for reason in scanner_row.reason_codes),
            )
        )
        audit_rows.append(
            {
                **result.audit_row,
                "symbol": symbol,
                "venue_symbol": scanner_row.resolved_venue_symbol,
                "timeframe": timeframe,
                "strategy_id": decision.get("strategy_id"),
                "lane_id": decision.get("lane_id"),
                "signal_candle_close_time": decision.get("signal_candle_close_time"),
                "probe_price": str(price),
                "probe_quantity": str(quantity),
                "order_shape": result.order_shape,
            }
        )
    stats = {
        "enabled": enabled,
        "notional_usdc": str(notional_usdc),
        "notional_cap_usdc": str(PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC),
        "daily_cap": daily_cap,
        "signals_seen_this_cycle": len(actionable),
        "audit_rows_this_cycle": len(audit_rows),
        "eligible_probe_shapes_this_cycle": sum(1 for row in audit_rows if row.get("eligible") is True),
        "signed_order_endpoint_called": False,
        "order_endpoint_called": False,
        "testnet_fills_update_strategy_pnl": False,
        "transport_status": "not_submitted_by_pt_rt1_runtime",
    }
    return audit_rows, stats


def _apply_testnet_probe_transport(
    *,
    audit_rows: Sequence[dict[str, Any]],
    submit_enabled: bool,
    transport_approval_text: str,
    notional_usdc: Decimal,
    transport: TestnetProbeTransport | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lifecycle_rows: list[dict[str, Any]] = []
    eligible_rows = [row for row in audit_rows if row.get("eligible") is True and row.get("order_shape")]
    if not submit_enabled:
        return lifecycle_rows, {
            "transport_mode": "audit_only",
            "transport_status": "audit_only_not_submitted",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["testnet_probe_transport_not_requested"],
        }
    if transport_approval_text != PT_RT1_2_EXACT_TRANSPORT_APPROVAL:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_transport_approval_missing",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["pt_rt1_2_exact_transport_approval_required"],
        }
    if notional_usdc != PT_RT1_TESTNET_PROBE_NOTIONAL_USDC:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_notional_not_20usdc",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["testnet_probe_notional_must_be_20usdc"],
        }
    if transport is None:
        return lifecycle_rows, {
            "transport_mode": "submit_requested",
            "transport_status": "blocked_transport_not_configured",
            "submitted_this_cycle": 0,
            "cancel_attempted_this_cycle": 0,
            "reconciled_this_cycle": 0,
            "order_endpoint_called": False,
            "signed_order_endpoint_called": False,
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
            "reason_codes": ["signed_testnet_transport_client_not_configured"],
        }

    submitted = 0
    cancel_attempted = 0
    reconciled = 0
    for row in eligible_rows:
        order_shape = row.get("order_shape")
        if not isinstance(order_shape, dict):
            continue
        result = transport(order_shape, row)
        lifecycle = {
            "lane": "testnet_plumbing_probe",
            "environment": "hyperliquid_testnet_only",
            "symbol": row.get("symbol"),
            "timeframe": row.get("timeframe"),
            "strategy_id": row.get("strategy_id"),
            "lane_id": row.get("lane_id"),
            "notional_usdc": row.get("notional_usdc"),
            "submit_attempted": True,
            "cancel_attempted": bool(result.get("cancel_attempted")),
            "reconcile_attempted": bool(result.get("reconcile_attempted")),
            "transport_status": result.get("transport_status", "submitted_cancel_reconciled"),
            "venue_order_id": result.get("venue_order_id"),
            "sanitized_response": result.get("sanitized_response"),
            "order_endpoint_called": bool(result.get("order_endpoint_called", True)),
            "signed_order_endpoint_called": bool(result.get("signed_order_endpoint_called", True)),
            "testnet_fills_update_strategy_pnl": False,
            "strategy_pnl_updated": False,
        }
        lifecycle_rows.append(lifecycle)
        submitted += 1
        cancel_attempted += 1 if lifecycle["cancel_attempted"] else 0
        reconciled += 1 if lifecycle["reconcile_attempted"] else 0

    return lifecycle_rows, {
        "transport_mode": "submit_requested",
        "transport_status": "submitted_cancel_reconciled" if lifecycle_rows else "no_eligible_probe_shapes",
        "submitted_this_cycle": submitted,
        "cancel_attempted_this_cycle": cancel_attempted,
        "reconciled_this_cycle": reconciled,
        "order_endpoint_called": bool(lifecycle_rows),
        "signed_order_endpoint_called": bool(lifecycle_rows),
        "testnet_fills_update_strategy_pnl": False,
        "strategy_pnl_updated": False,
        "reason_codes": ["pt_rt1_2_transport_lifecycle_recorded"],
    }


def run_cycle(
    *,
    connector: HyperliquidPublicMarketDataConnector,
    output_dir: Path,
    symbols: Sequence[str] | None,
    timeframes: Sequence[str],
    max_candle_symbols: int | None,
    run_label: str = "PT-RT1.1B",
    decision_log_mode: str = "compact",
    testnet_probes_enabled: bool = False,
    testnet_probe_approval_text: str = "",
    testnet_probe_notional_usdc: Decimal = PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    testnet_probe_daily_cap: int = TESTNET_PROBE_AUDIT_LIMIT,
    submit_testnet_probes: bool = False,
    testnet_probe_transport_approval_text: str = "",
    testnet_probe_transport: TestnetProbeTransport | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    meta_result = connector.fetch_meta()
    mids_result = connector.fetch_all_mids()
    if meta_result.ok and mids_result.ok:
        scanner_rows = resolve_watchlist_from_public_data(meta_payload=meta_result.payload, mids_payload=mids_result.payload)
    else:
        scanner_rows = ()

    selected_rows = _filter_scanner_rows(scanner_rows, symbols, max_candle_symbols)
    market_health: list[dict[str, Any]] = []
    decisions: list[PaperDecisionEvent] = []
    latest_chart: dict[str, Any] | None = None
    latest_closed_by_key: dict[tuple[str, str], Any] = {}
    prior_state = _read_state(output_dir / "state.json")
    paper_state = _load_paper_runtime_state(prior_state)
    processed_signal_keys: set[str] = paper_state["processed_signal_keys"]
    open_positions_by_key: dict[str, dict[str, Any]] = paper_state["open_positions_by_key"]
    realized_equity_by_lane: dict[str, str] = paper_state["realized_equity_by_lane"]
    last_processed_close_by_key: dict[str, str] = paper_state["last_processed_close_by_key"]

    for row in selected_rows:
        for timeframe in timeframes:
            start_time, end_time = candle_request_window(timeframe=timeframe, now=now, bars=260)
            candle_result = connector.fetch_candle_snapshot(
                symbol=str(row.resolved_venue_symbol or row.requested_symbol),
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
            )
            closed_candles = _closed_prefix(candle_result.candles, now)
            if closed_candles:
                latest_closed_by_key[(str(row.canonical_symbol or row.requested_symbol).upper(), timeframe)] = closed_candles[-1]
            closed_status = "closed_candle_ready" if closed_candles else "candle_not_closed_or_unavailable"
            market_health.append(
                {
                    "symbol": row.canonical_symbol,
                    "requested_symbol": row.requested_symbol,
                    "resolved_venue_symbol": row.resolved_venue_symbol,
                    "timeframe": timeframe,
                    "source": "Hyperliquid public mainnet",
                    "endpoint_category": connector.endpoint_category,
                    "status": candle_result.data_health.value,
                    "fully_closed_candle_status": closed_status,
                    "latest_candle_update": candle_result.latest_candle_update,
                    "last_update_utc": _iso(now),
                    "reason_codes": list(candle_result.reason_codes),
                }
            )
            if closed_candles and latest_chart is None:
                latest_chart = {
                    "symbol": row.canonical_symbol,
                    "timeframe": timeframe,
                    "candles": [
                        {
                            "time": _iso(candle.open_time),
                            "open": str(candle.open),
                            "high": str(candle.high),
                            "low": str(candle.low),
                            "close": str(candle.close),
                            "volume": str(candle.volume),
                        }
                        for candle in closed_candles[-120:]
                    ],
                    "paper_markers": [],
                    "reason_code_toggle": True,
                }
            for lane in PT_RT1_STRATEGY_LANES:
                symbol = str(row.canonical_symbol or row.requested_symbol).upper()
                lane_position_key = _lane_key(lane.lane_id, symbol, timeframe)
                equity_before = _dec(realized_equity_by_lane.get(lane.lane_id), lane.initial_equity)
                decisions.append(
                    evaluate_paper_decision(
                        lane=lane,
                        symbol=symbol,
                        timeframe=timeframe,
                        candles=closed_candles,
                        now=now,
                        data_health=candle_result.data_health if closed_candles else DataHealth.UNAVAILABLE,
                        position_open=lane_position_key in open_positions_by_key,
                        equity_before=equity_before,
                    )
                )

    base_summary = build_pt_rt1_summary()
    scanner_payload = [asdict(row) for row in scanner_rows] if scanner_rows else base_summary["scanner_universe"]
    lane_payload = base_summary["strategy_lanes"]
    raw_decision_rows = [event.as_json_dict() for event in decisions]
    decision_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    duplicate_signal_blocks_this_cycle = 0
    paper_opens_this_cycle = 0
    paper_closes_this_cycle = 0
    for row in raw_decision_rows:
        symbol = str(row.get("symbol") or "").upper()
        timeframe = str(row.get("timeframe") or "")
        lane_id = str(row.get("lane_id") or "")
        lane_position_key = _lane_key(lane_id, symbol, timeframe)
        candle = latest_closed_by_key.get((symbol, timeframe))
        if row.get("signal_candle_close_time"):
            last_processed_close_by_key[lane_position_key] = str(row["signal_candle_close_time"])
        if row.get("action") == "paper_opened":
            signal_key = _paper_signal_key(row)
            if signal_key in processed_signal_keys or lane_position_key in open_positions_by_key:
                duplicate_signal_blocks_this_cycle += 1
                decision_rows.append(_blocked_duplicate_row(row))
                continue
            processed_signal_keys.add(signal_key)
            equity_before = _dec(realized_equity_by_lane.get(lane_id), Decimal("10000"))
            if candle is not None:
                position = _open_position_from_decision(row=row, candle=candle, equity_before=equity_before)
                open_positions_by_key[lane_position_key] = position
                realized_equity_by_lane[lane_id] = str(equity_before - _dec(position.get("fees")))
                paper_opens_this_cycle += 1
                row = {
                    **row,
                    "paper_state_transition": "opened_synthetic_position",
                    "paper_position_key": lane_position_key,
                    "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
                    "testnet_fills_update_strategy_pnl": False,
                }
            else:
                row = {
                    **row,
                    "action": "data_unavailable",
                    "reason_codes": list(row.get("reason_codes") or []) + ["paper_open_context_candle_missing"],
                    "paper_state_transition": "open_blocked_context_missing",
                }
        elif row.get("action") == "paper_closed":
            position = open_positions_by_key.get(lane_position_key)
            if position is None or candle is None:
                row = {
                    **row,
                    "action": "paper_hold",
                    "reason_codes": list(row.get("reason_codes") or []) + ["paper_position_missing"],
                    "paper_state_transition": "close_blocked_position_missing",
                }
            else:
                trade, equity_after = _close_position_from_decision(row=row, position=position, candle=candle)
                trade_rows.append(trade)
                realized_equity_by_lane[lane_id] = str(equity_after)
                open_positions_by_key.pop(lane_position_key, None)
                paper_closes_this_cycle += 1
                row = {
                    **row,
                    "paper_state_transition": "closed_synthetic_position",
                    "paper_position_key": lane_position_key,
                    "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
                    "testnet_fills_update_strategy_pnl": False,
                    "trade_net_pnl": trade["net_pnl"],
                    "equity_after": trade["equity_after"],
                }
        elif row.get("action") == "data_unavailable":
            pass
        decision_rows.append(row)

    prior_seen_keys = set(prior_state.get("decision_log_seen_keys") or [])
    decision_log_rows, decision_log_seen_keys, decision_log_stats = _select_decision_log_rows(
        decision_rows,
        mode=decision_log_mode,
        seen_keys=prior_seen_keys,
    )
    intended_entry_signals = [row for row in decision_rows if row.get("action") == "paper_opened"]
    testnet_probe_rows, testnet_probe_stats = _build_testnet_probe_audit_rows(
        decision_rows=decision_rows,
        scanner_rows=selected_rows,
        latest_closed_by_key=latest_closed_by_key,
        enabled=testnet_probes_enabled,
        approval_text=testnet_probe_approval_text,
        notional_usdc=testnet_probe_notional_usdc,
        daily_cap=testnet_probe_daily_cap,
    )
    testnet_transport_rows, testnet_transport_stats = _apply_testnet_probe_transport(
        audit_rows=testnet_probe_rows,
        submit_enabled=submit_testnet_probes,
        transport_approval_text=testnet_probe_transport_approval_text,
        notional_usdc=testnet_probe_notional_usdc,
        transport=testnet_probe_transport,
    )
    data_unavailable_summary = _summarize_data_unavailable(
        market_health=market_health,
        decision_rows=decision_rows,
    )
    runtime_status = "verified" if meta_result.ok and mids_result.ok and market_health else "blocked"
    if not meta_result.ok or not mids_result.ok:
        runtime_status = "blocked_public_mainnet_network_unavailable"
    is_pt_rt1_1c = run_label == "PT-RT1.1C"
    is_pt_rt1_2 = run_label == "PT-RT1.2"
    summary = {
        **base_summary,
        "phase": run_label,
        "revision": run_label,
        "status": (
            "runtime_correctness_cycle_verified"
            if is_pt_rt1_2 and runtime_status == "verified"
            else "runtime_correctness_cycle_blocked"
            if is_pt_rt1_2
            else
            "runtime_collection_cycle_verified"
            if is_pt_rt1_1c and runtime_status == "verified"
            else "runtime_readiness_smoke"
            if runtime_status == "verified"
            else runtime_status
        ),
        "market_data_endpoint_policy": {
            "strategy_truth_endpoint": PT_RT1_MAINNET_INFO_URL,
            "endpoint_category": "public_read_only",
            "allowed_public_info_types": base_summary["strategy_truth_lane"]["allowed_info_types"],
            "forbidden_payloads_rejected": True,
            "testnet_url_is_strategy_truth": False,
            "api_keys_required": False,
        },
        "connection_status": {
            "hyperliquid_public_mainnet": "connected" if meta_result.ok and mids_result.ok else "disconnected",
            "endpoint_category": "public_read_only",
            "last_update_utc": _iso(now),
            "meta_reason_codes": list(meta_result.reason_codes),
            "mids_reason_codes": list(mids_result.reason_codes),
            "no_private_signed_order_endpoints": True,
            "no_api_keys": True,
        },
        "scanner_universe": scanner_payload,
        "watchlist_status": {
            "requested_symbols": list(PT_RT1_REQUESTED_SCANNER_SYMBOLS),
            "resolved_rows": len(scanner_payload),
            "eligible_rows": sum(1 for row in scanner_payload if row.get("scanner_eligible") is True),
            "blocked_rows": sum(1 for row in scanner_payload if row.get("blocked") is True),
        },
        "market_data_health": market_health or base_summary["market_data_health"],
        "data_unavailable_summary": data_unavailable_summary,
        "strategy_lanes": lane_payload,
        "intended_entry_signals": intended_entry_signals[:200],
        "closed_trades": trade_rows[:200],
        "latest_decisions": decision_rows[:200],
        "live_chart": latest_chart or {
            "status": "data_not_available_in_pt_rt1_runtime",
            "reason_codes": ["public_mainnet_network_unavailable" if not meta_result.ok else "no_closed_candles_loaded"],
            "paper_markers": [],
        },
        "testnet_plumbing_status": {
            "status": "enabled_audit_only" if testnet_probes_enabled else "ready_but_disabled",
            "disabled_by_default": False if testnet_probes_enabled else True,
            "kill_switch_active": False if testnet_probes_enabled else True,
            "approval_required": True,
            "approval_captured": testnet_probe_approval_text == PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
            "daily_cap_configured": True,
            "daily_cap": testnet_probe_daily_cap,
            "notional_cap_configured": True,
            "probe_notional_usdc": str(testnet_probe_notional_usdc),
            "probe_notional_cap_usdc": str(PT_RT1_TESTNET_PROBE_NOTIONAL_CAP_USDC),
            "probe_audit_rows_this_cycle": testnet_probe_stats["audit_rows_this_cycle"],
            "eligible_probe_shapes_this_cycle": testnet_probe_stats["eligible_probe_shapes_this_cycle"],
            "transport_mode": testnet_transport_stats["transport_mode"],
            "transport_rows_this_cycle": len(testnet_transport_rows),
            "transport_submitted_this_cycle": testnet_transport_stats["submitted_this_cycle"],
            "transport_cancel_attempted_this_cycle": testnet_transport_stats["cancel_attempted_this_cycle"],
            "transport_reconciled_this_cycle": testnet_transport_stats["reconciled_this_cycle"],
            "post_only_required": True,
            "cancel_reconcile_required": True,
            "testnet_fills_do_not_update_strategy_pnl": True,
            "signed_order_endpoint_called": testnet_transport_stats["signed_order_endpoint_called"],
            "order_endpoint_called": testnet_transport_stats["order_endpoint_called"],
            "transport_status": testnet_transport_stats["transport_status"],
            "reason_codes": [
                *(
                    ["testnet_probe_order_shapes_created_audit_only", "testnet_probe_20usdc_per_signal"]
                    if testnet_probes_enabled
                    else [
                        "testnet_probe_not_enabled",
                        "testnet_probe_kill_switch_active",
                        "testnet_probe_approval_missing",
                        "testnet_probe_ready_but_disabled",
                    ]
                ),
                *testnet_transport_stats.get("reason_codes", []),
            ],
        },
        "runtime_command": {
            "duration_hours_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run --enable-testnet-probes --founder-approved-testnet-probes-20usdc --testnet-probe-notional-usdc 20 --public-mainnet-only",
            "smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 1 --output-dir reports/paper_runtime/pt_rt1_1b_smoke --disable-testnet-probes --public-mainnet-only",
            "output_dir": str(output_dir),
        },
        "smoke_run_status": {
            "status": runtime_status,
            "public_mainnet_fetch_attempted": True,
            "watchlist_resolved": bool(scanner_rows),
            "decisions_recorded": len(decision_rows),
            "decisions_written": len(decision_log_rows),
            "decision_log_mode": decision_log_mode,
            "orders_submitted": testnet_transport_stats["submitted_this_cycle"] > 0,
            "testnet_probes_enabled": testnet_probes_enabled,
            "testnet_probe_notional_usdc": str(testnet_probe_notional_usdc),
            "private_signed_order_endpoints_called": testnet_transport_stats["signed_order_endpoint_called"],
            "testnet_order_endpoints_called": testnet_transport_stats["order_endpoint_called"],
        },
        "paper_runtime_state": {
            "open_positions_count": len(open_positions_by_key),
            "processed_signal_keys_total": len(processed_signal_keys),
            "paper_opens_this_cycle": paper_opens_this_cycle,
            "paper_closes_this_cycle": paper_closes_this_cycle,
            "duplicate_signal_blocks_this_cycle": duplicate_signal_blocks_this_cycle,
            "paper_opens_total": paper_state["paper_opens_total"] + paper_opens_this_cycle,
            "paper_closes_total": paper_state["paper_closes_total"] + paper_closes_this_cycle,
            "duplicate_signal_blocks_total": paper_state["duplicate_signal_blocks_total"] + duplicate_signal_blocks_this_cycle,
            "open_positions_by_key": open_positions_by_key,
            "realized_equity_by_lane": realized_equity_by_lane,
            "paper_pnl_source": "synthetic_public_mainnet_paper_ledger",
            "testnet_fills_update_strategy_pnl": False,
        },
        "next_phase_decision": (
            "PT-RT1.2 may continue paper observation; signed testnet transport remains blocked unless exact transport approval and a configured client are present"
            if is_pt_rt1_2 and runtime_status == "verified"
            else "PT-RT1.2 blocked"
            if is_pt_rt1_2
            else
            "PT-RT1.1D may evaluate 24-hour runtime artifacts after completion"
            if is_pt_rt1_1c and runtime_status == "verified"
            else "PT-RT1.1D blocked"
            if is_pt_rt1_1c
            else
            "PT-RT1.1C may start 24-hour probes-disabled runtime collection"
            if runtime_status == "verified"
            else "PT-RT1.1C blocked"
        ),
    }
    _append_jsonl(output_dir / "decisions.jsonl", decision_log_rows)
    decisions_size = (output_dir / "decisions.jsonl").stat().st_size if (output_dir / "decisions.jsonl").exists() else 0
    summary["decision_log_stats"] = {
        **decision_log_stats,
        "decisions_jsonl_size_bytes": decisions_size,
        "decisions_jsonl_warning_threshold_bytes": DECISION_LOG_SIZE_WARNING_BYTES,
        "decisions_jsonl_warning": decisions_size >= DECISION_LOG_SIZE_WARNING_BYTES,
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(
        output_dir / "state.json",
        {
            "generated_at_utc": _iso(now),
            "strategy_lanes": lane_payload,
            "decision_log_mode": decision_log_mode,
            "decision_log_seen_keys": sorted(decision_log_seen_keys),
            "paper_runtime": _paper_runtime_state_payload(
                processed_signal_keys=processed_signal_keys,
                open_positions_by_key=open_positions_by_key,
                realized_equity_by_lane=realized_equity_by_lane,
                last_processed_close_by_key=last_processed_close_by_key,
                paper_opens_total=paper_state["paper_opens_total"] + paper_opens_this_cycle,
                paper_closes_total=paper_state["paper_closes_total"] + paper_closes_this_cycle,
                duplicate_signal_blocks_total=paper_state["duplicate_signal_blocks_total"]
                + duplicate_signal_blocks_this_cycle,
            ),
        },
    )
    _write_json(output_dir / "data_health.json", {"generated_at_utc": _iso(now), "rows": market_health})
    _write_json(output_dir / "equity_curves.json", {"generated_at_utc": _iso(now), "lanes": lane_payload})
    _append_jsonl(output_dir / "runtime_audit.jsonl", [summary["connection_status"], summary["testnet_plumbing_status"]])
    _append_jsonl(output_dir / "testnet_probe_audit.jsonl", testnet_probe_rows)
    _append_jsonl(output_dir / "testnet_probe_transport.jsonl", testnet_transport_rows)
    _append_jsonl(output_dir / "trades.jsonl", trade_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    duration = parser.add_mutually_exclusive_group(required=True)
    duration.add_argument("--duration-hours", type=Decimal)
    duration.add_argument("--duration-minutes", type=Decimal)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    probe_mode = parser.add_mutually_exclusive_group(required=True)
    probe_mode.add_argument("--disable-testnet-probes", action="store_true")
    probe_mode.add_argument("--enable-testnet-probes", action="store_true")
    parser.add_argument("--founder-approved-testnet-probes-20usdc", action="store_true")
    parser.add_argument("--submit-testnet-probes", action="store_true")
    parser.add_argument("--founder-approved-pt-rt1-2-testnet-transport-20usdc", action="store_true")
    parser.add_argument("--testnet-probe-notional-usdc", type=Decimal, default=PT_RT1_TESTNET_PROBE_NOTIONAL_USDC)
    parser.add_argument("--testnet-probe-daily-cap", type=int, default=TESTNET_PROBE_AUDIT_LIMIT)
    parser.add_argument("--public-mainnet-only", action="store_true")
    parser.add_argument("--poll-seconds", type=Decimal, default=Decimal("60"))
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--timeframe", action="append", choices=tuple(TIMEFRAME_DURATIONS), dest="timeframes")
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--max-candle-symbols", type=int)
    parser.add_argument("--decision-log-mode", choices=DECISION_LOG_MODES, default="compact")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.public_mainnet_only:
        raise SystemExit("public_mainnet_only_required_for_strategy_truth")
    if args.enable_testnet_probes and not args.founder_approved_testnet_probes_20usdc:
        raise SystemExit("founder_approved_testnet_probes_20usdc_required")
    if args.submit_testnet_probes and not args.enable_testnet_probes:
        raise SystemExit("submit_testnet_probes_requires_enable_testnet_probes")
    if args.submit_testnet_probes and not args.founder_approved_pt_rt1_2_testnet_transport_20usdc:
        raise SystemExit("founder_approved_pt_rt1_2_testnet_transport_20usdc_required")
    if args.testnet_probe_notional_usdc != PT_RT1_TESTNET_PROBE_NOTIONAL_USDC:
        raise SystemExit("testnet_probe_notional_must_be_20usdc")
    if args.testnet_probe_daily_cap <= 0:
        raise SystemExit("positive_testnet_probe_daily_cap_required")
    _ensure_ignored_output_dir(args.output_dir)
    duration = timedelta(
        hours=float(args.duration_hours or Decimal("0")),
        minutes=float(args.duration_minutes or Decimal("0")),
    )
    if duration <= timedelta(0):
        raise SystemExit("positive_duration_required")
    connector = HyperliquidPublicMarketDataConnector()
    end_time = _utc_now() + duration
    run_label = "PT-RT1.2" if args.enable_testnet_probes else "PT-RT1.1C" if "pt_rt1_1c" in str(args.output_dir) else "PT-RT1.1B"
    cycle = 0
    last_summary: dict[str, Any] = {}
    while True:
        cycle += 1
        last_summary = run_cycle(
            connector=connector,
            output_dir=args.output_dir,
            symbols=args.symbols,
            timeframes=args.timeframes or tuple(TIMEFRAME_DURATIONS),
            max_candle_symbols=args.max_candle_symbols,
            run_label=run_label,
            decision_log_mode=args.decision_log_mode,
            testnet_probes_enabled=args.enable_testnet_probes,
            testnet_probe_approval_text=(
                PT_RT1_EXACT_TESTNET_PROBE_APPROVAL if args.founder_approved_testnet_probes_20usdc else ""
            ),
            testnet_probe_notional_usdc=args.testnet_probe_notional_usdc,
            testnet_probe_daily_cap=args.testnet_probe_daily_cap,
            submit_testnet_probes=args.submit_testnet_probes,
            testnet_probe_transport_approval_text=(
                PT_RT1_2_EXACT_TRANSPORT_APPROVAL
                if args.founder_approved_pt_rt1_2_testnet_transport_20usdc
                else ""
            ),
        )
        if args.max_cycles is not None and cycle >= args.max_cycles:
            break
        now = _utc_now()
        if now >= end_time:
            break
        sleep_seconds = min(float(args.poll_seconds), max(0.0, (end_time - now).total_seconds()))
        if sleep_seconds:
            time.sleep(sleep_seconds)
    print(json.dumps(_json_safe({"summary_path": str(args.output_dir / "summary.json"), "status": last_summary.get("status")}), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
