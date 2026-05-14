"""Run PT-RT1 public-mainnet paper-observation readiness cycles.

The runner writes ignored runtime artifacts under ``reports/paper_runtime/``.
It uses only Hyperliquid public mainnet ``/info`` payloads for strategy truth
and fails closed if testnet probes are not explicitly disabled.
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
from typing import Any, Iterable, Sequence

from services.paper_runtime.hyperliquid_public_market_data import (
    HyperliquidPublicMarketDataConnector,
    candle_request_window,
    resolve_watchlist_from_public_data,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_1B_RUNTIME_OUTPUT_PREFIX,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_REQUESTED_SCANNER_SYMBOLS,
    PT_RT1_STRATEGY_LANES,
    TIMEFRAME_DURATIONS,
    DataHealth,
    PaperDecisionEvent,
    build_pt_rt1_summary,
    canonical_candle_close,
    evaluate_paper_decision,
)


DEFAULT_OUTPUT_DIR = Path("reports/paper_runtime/pt_rt1_1b_smoke")


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


def run_cycle(
    *,
    connector: HyperliquidPublicMarketDataConnector,
    output_dir: Path,
    symbols: Sequence[str] | None,
    timeframes: Sequence[str],
    max_candle_symbols: int | None,
    run_label: str = "PT-RT1.1B",
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
                decisions.append(
                    evaluate_paper_decision(
                        lane=lane,
                        symbol=str(row.canonical_symbol or row.requested_symbol),
                        timeframe=timeframe,
                        candles=closed_candles,
                        now=now,
                        data_health=candle_result.data_health if closed_candles else DataHealth.UNAVAILABLE,
                    )
                )

    base_summary = build_pt_rt1_summary()
    scanner_payload = [asdict(row) for row in scanner_rows] if scanner_rows else base_summary["scanner_universe"]
    lane_payload = base_summary["strategy_lanes"]
    decision_rows = [event.as_json_dict() for event in decisions]
    runtime_status = "verified" if meta_result.ok and mids_result.ok and market_health else "blocked"
    if not meta_result.ok or not mids_result.ok:
        runtime_status = "blocked_public_mainnet_network_unavailable"
    is_pt_rt1_1c = run_label == "PT-RT1.1C"
    summary = {
        **base_summary,
        "phase": run_label,
        "revision": run_label,
        "status": (
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
        "strategy_lanes": lane_payload,
        "latest_decisions": decision_rows[:200],
        "live_chart": latest_chart or {
            "status": "data_not_available_in_pt_rt1_runtime",
            "reason_codes": ["public_mainnet_network_unavailable" if not meta_result.ok else "no_closed_candles_loaded"],
            "paper_markers": [],
        },
        "testnet_plumbing_status": {
            "status": "ready_but_disabled",
            "disabled_by_default": True,
            "kill_switch_active": True,
            "approval_required": True,
            "daily_cap_configured": True,
            "notional_cap_configured": True,
            "post_only_required": True,
            "cancel_reconcile_required": True,
            "testnet_fills_do_not_update_strategy_pnl": True,
            "reason_codes": [
                "testnet_probe_not_enabled",
                "testnet_probe_kill_switch_active",
                "testnet_probe_approval_missing",
                "testnet_probe_ready_but_disabled",
            ],
        },
        "runtime_command": {
            "duration_hours_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run --disable-testnet-probes --public-mainnet-only",
            "smoke_example": ".venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 1 --output-dir reports/paper_runtime/pt_rt1_1b_smoke --disable-testnet-probes --public-mainnet-only",
            "output_dir": str(output_dir),
        },
        "smoke_run_status": {
            "status": runtime_status,
            "public_mainnet_fetch_attempted": True,
            "watchlist_resolved": bool(scanner_rows),
            "decisions_recorded": len(decision_rows),
            "orders_submitted": False,
            "testnet_probes_enabled": False,
            "private_signed_order_endpoints_called": False,
        },
        "next_phase_decision": (
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
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "state.json", {"generated_at_utc": _iso(now), "strategy_lanes": lane_payload})
    _write_json(output_dir / "data_health.json", {"generated_at_utc": _iso(now), "rows": market_health})
    _write_json(output_dir / "equity_curves.json", {"generated_at_utc": _iso(now), "lanes": lane_payload})
    _append_jsonl(output_dir / "runtime_audit.jsonl", [summary["connection_status"], summary["testnet_plumbing_status"]])
    _append_jsonl(output_dir / "decisions.jsonl", decision_rows)
    _append_jsonl(output_dir / "trades.jsonl", [])
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    duration = parser.add_mutually_exclusive_group(required=True)
    duration.add_argument("--duration-hours", type=Decimal)
    duration.add_argument("--duration-minutes", type=Decimal)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--disable-testnet-probes", action="store_true")
    parser.add_argument("--public-mainnet-only", action="store_true")
    parser.add_argument("--poll-seconds", type=Decimal, default=Decimal("60"))
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--timeframe", action="append", choices=tuple(TIMEFRAME_DURATIONS), dest="timeframes")
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--max-candle-symbols", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.disable_testnet_probes:
        raise SystemExit("testnet_probes_must_be_disabled_for_pt_rt1_1b")
    if not args.public_mainnet_only:
        raise SystemExit("public_mainnet_only_required_for_strategy_truth")
    _ensure_ignored_output_dir(args.output_dir)
    duration = timedelta(
        hours=float(args.duration_hours or Decimal("0")),
        minutes=float(args.duration_minutes or Decimal("0")),
    )
    if duration <= timedelta(0):
        raise SystemExit("positive_duration_required")
    connector = HyperliquidPublicMarketDataConnector()
    end_time = _utc_now() + duration
    run_label = "PT-RT1.1C" if "pt_rt1_1c" in str(args.output_dir) else "PT-RT1.1B"
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
