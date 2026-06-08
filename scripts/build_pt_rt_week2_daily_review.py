#!/usr/bin/env python3
"""Build a read-only PT-RT Week 2 daily review pack."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = "pt_rt1_6_week2_active"
RUNTIME_ROOT = Path("reports/paper_runtime")
REVIEW_ROOT = Path("reports/paper_reviews")
BASELINE_TESTNET_LANE = "money_flow_v1_2_baseline"
ACTIVE_TIMEFRAMES = ["1h", "4h", "1d"]
DISABLED_TIMEFRAMES = ["15m"]
ACTIVE_LANES = [
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
]
RUNTIME_FILES = {
    "summary": "summary.json",
    "state": "state.json",
    "decisions": "decisions.jsonl",
    "trades": "trades.jsonl",
    "testnet": "testnet_order_lifecycle.jsonl",
    "audit": "runtime_audit.jsonl",
    "health": "data_health.json",
}


def utc_now() -> datetime:
    return datetime.now(tz=UTC).replace(microsecond=0)


def parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def money(value: Any) -> str:
    return f"{dec(value):,.2f}"


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    try:
        handle = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def row_time(row: dict[str, Any]) -> datetime | None:
    for key in (
        "decision_time",
        "time",
        "timestamp",
        "updated_at_utc",
        "exit_time",
        "entry_time",
        "current_price_time",
        "signal_candle_close_time",
    ):
        parsed = parse_utc(row.get(key))
        if parsed is not None:
            return parsed
    return None


def row_reason_codes(row: dict[str, Any]) -> list[str]:
    reasons = row.get("reason_codes")
    if reasons is None:
        reasons = row.get("trigger_reason_codes")
    if isinstance(reasons, list):
        return [str(reason) for reason in reasons]
    if isinstance(reasons, str):
        return [part.strip() for part in reasons.split(",") if part.strip()]
    return []


def in_window(row: dict[str, Any], start: datetime, end: datetime) -> bool:
    timestamp = row_time(row)
    return timestamp is not None and start <= timestamp <= end


def file_status(path: Path, now: datetime) -> dict[str, Any]:
    exists = path.exists()
    if not exists:
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": 0,
            "modified_utc": None,
            "age_seconds": None,
        }
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_utc": iso(modified),
        "age_seconds": int((now - modified).total_seconds()),
    }


def runtime_process_lines() -> list[str]:
    result = subprocess.run(
        ["pgrep", "-fl", "run_pt_rt1_paper_observation"],
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def pick_latest_time(rows: Iterable[dict[str, Any]]) -> str | None:
    latest: datetime | None = None
    for row in rows:
        timestamp = row_time(row)
        if timestamp is not None and (latest is None or timestamp > latest):
            latest = timestamp
    return iso(latest)


def summarize_lanes(summary: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    lanes = summary.get("active_strategy_lanes")
    if not isinstance(lanes, list):
        lanes = []
    realized_by_lane = {}
    runtime_state = state.get("paper_runtime") if isinstance(state.get("paper_runtime"), dict) else state
    if isinstance(runtime_state, dict):
        realized_by_lane = runtime_state.get("realized_equity_by_lane") or {}
    result: list[dict[str, Any]] = []
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        lane_id = str(lane.get("lane_id") or lane.get("strategy_id") or "")
        realized = lane.get("realized_equity", realized_by_lane.get(lane_id, lane.get("starting_equity", "10000")))
        unrealized = lane.get("unrealized_pnl", "0")
        total = dec(realized, Decimal("10000")) + dec(unrealized)
        result.append(
            {
                "lane_id": lane_id,
                "role": lane.get("role"),
                "realized_equity": str(realized),
                "unrealized_pnl": str(unrealized),
                "total_equity": str(total),
                "net_pnl": str(total - Decimal("10000")),
                "open_positions": int(dec(lane.get("open_positions"), Decimal("0"))),
                "closed_trades": int(dec(lane.get("closed_trades"), Decimal("0"))),
                "testnet_eligible": bool(lane.get("testnet_eligible")),
                "production_approved": bool(lane.get("production_approved")),
                "live_approved": bool(lane.get("live_approved") or lane.get("live_trading_approved")),
            }
        )
    if not result:
        for lane_id in ACTIVE_LANES:
            result.append(
                {
                    "lane_id": lane_id,
                    "role": "configured_week2_active",
                    "realized_equity": "10000",
                    "unrealized_pnl": "0",
                    "total_equity": "10000",
                    "net_pnl": "0",
                    "open_positions": 0,
                    "closed_trades": 0,
                    "testnet_eligible": lane_id == BASELINE_TESTNET_LANE,
                    "production_approved": False,
                    "live_approved": False,
                }
            )
    return result


def summarize_open_positions(state: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_state = state.get("paper_runtime") if isinstance(state.get("paper_runtime"), dict) else state
    positions = {}
    if isinstance(runtime_state, dict):
        positions = runtime_state.get("open_positions_by_key") or runtime_state.get("open_synthetic_positions") or {}
    if isinstance(positions, dict):
        rows = list(positions.values())
    elif isinstance(positions, list):
        rows = positions
    else:
        rows = []
    if not rows and isinstance(summary.get("open_synthetic_positions"), list):
        rows = summary["open_synthetic_positions"]
    normalized = [row for row in rows if isinstance(row, dict)]
    return sorted(normalized, key=lambda row: str(row.get("entry_time") or ""), reverse=True)


def summarize_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    actions = Counter(str(row.get("action") or "unknown") for row in rows)
    reasons: Counter[str] = Counter()
    symbols = Counter(str(row.get("symbol") or "unknown") for row in rows)
    lanes = Counter(str(row.get("lane_id") or row.get("strategy_id") or "unknown") for row in rows)
    timeframes = Counter(str(row.get("timeframe") or "unknown") for row in rows)
    for row in rows:
        reasons.update(row_reason_codes(row))
    return {
        "count": len(rows),
        "actions": dict(actions.most_common()),
        "top_reason_codes": reasons.most_common(12),
        "top_symbols": symbols.most_common(12),
        "lanes": dict(lanes.most_common()),
        "timeframes": dict(timeframes.most_common()),
        "latest_decision_time": pick_latest_time(rows),
    }


def summarize_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    winners = [row for row in rows if dec(row.get("net_pnl")) > 0]
    losers = [row for row in rows if dec(row.get("net_pnl")) < 0]
    total = sum((dec(row.get("net_pnl")) for row in rows), Decimal("0"))
    largest_win = max((dec(row.get("net_pnl")) for row in winners), default=Decimal("0"))
    largest_loss = min((dec(row.get("net_pnl")) for row in losers), default=Decimal("0"))
    return {
        "count": len(rows),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "total_net_pnl": str(total),
        "largest_win": str(largest_win),
        "largest_loss": str(largest_loss),
        "latest_trade_time": pick_latest_time(rows),
    }


def summarize_testnet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(row.get("status") or "unknown") for row in rows)
    endpoint_called = sum(1 for row in rows if row.get("order_endpoint_called") is True)
    signed_called = sum(1 for row in rows if row.get("signed_order_endpoint_called") is True)
    filled = sum(1 for row in rows if row.get("status") in {"filled", "partially_filled"})
    strategy_pnl_updates = sum(1 for row in rows if row.get("strategy_pnl_update_from_testnet") is True)
    return {
        "count": len(rows),
        "statuses": dict(statuses.most_common()),
        "order_endpoint_called_count": endpoint_called,
        "signed_order_endpoint_called_count": signed_called,
        "filled_or_partial_count": filled,
        "strategy_pnl_update_from_testnet_count": strategy_pnl_updates,
        "latest_lifecycle_time": pick_latest_time(rows),
    }


def anomaly_flags(
    *,
    file_statuses: dict[str, dict[str, Any]],
    process_lines: list[str],
    decisions: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    testnet: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    lanes: list[dict[str, Any]],
    now: datetime,
    stale_minutes: int,
) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for key, status in file_statuses.items():
        if not status["exists"]:
            flags.append({"code": "missing_runtime_file", "severity": "warning", "detail": key})
    if not process_lines:
        flags.append({"code": "runtime_not_detected", "severity": "warning", "detail": "No local run_pt_rt1_paper_observation process detected."})
    summary_mtime = file_statuses.get("summary", {}).get("modified_utc")
    summary_dt = parse_utc(summary_mtime)
    if summary_dt and now - summary_dt > timedelta(minutes=stale_minutes):
        flags.append({"code": "runtime_stale", "severity": "warning", "detail": f"summary.json older than {stale_minutes} minutes"})
    if not decisions:
        flags.append({"code": "no_recent_decisions", "severity": "warning", "detail": "No decision rows in the review window."})
    if not trades:
        flags.append({"code": "no_closed_trades_yet", "severity": "info", "detail": "trades.jsonl can stay empty until a synthetic position closes."})
    if any(str(row.get("timeframe")) == "15m" for row in [*decisions, *trades, *testnet]):
        flags.append({"code": "new_15m_active_row_detected", "severity": "critical", "detail": "15m appeared in review-window runtime rows."})
    for row in testnet:
        lane = str(row.get("trigger_lane") or row.get("lane_id") or "")
        if lane and lane not in {BASELINE_TESTNET_LANE, "none"}:
            flags.append({"code": "candidate_lane_testnet_lifecycle_detected", "severity": "critical", "detail": lane})
            break
    if any(str(row.get("status")) == "unknown_state" or row.get("unknown_state") is True for row in testnet):
        flags.append({"code": "testnet_unknown_state", "severity": "critical", "detail": "A testnet lifecycle row entered unknown_state."})
    for row in testnet:
        status = str(row.get("status") or "")
        cancel_status = str(row.get("cancel_status") or "")
        reconcile_status = str(row.get("reconcile_status") or "")
        if status in {"accepted_open", "submitted"} and "canceled" not in cancel_status and "reconciled" not in reconcile_status:
            flags.append({"code": "testnet_cancel_reconcile_missing", "severity": "critical", "detail": status})
            break
    if any(row.get("strategy_pnl_update_from_testnet") is True for row in testnet):
        flags.append({"code": "synthetic_pnl_from_testnet_suspected", "severity": "critical", "detail": "Testnet lifecycle row claims strategy PnL update."})
    duplicate_count = sum(1 for row in decisions if "duplicate_candle_signal_ignored" in row_reason_codes(row))
    if duplicate_count > 20:
        flags.append({"code": "duplicate_signal_spike", "severity": "warning", "detail": str(duplicate_count)})
    warm_start_count = sum(1 for row in decisions if "warm_start_blocked_late_entry" in row_reason_codes(row))
    if warm_start_count > 50:
        flags.append({"code": "warm_start_block_spike", "severity": "info", "detail": str(warm_start_count)})
    for row in open_positions:
        pnl = dec(row.get("current_unrealized_pnl") or row.get("unrealized_pnl"))
        if pnl <= Decimal("-500"):
            flags.append({"code": "large_unrealized_loss", "severity": "warning", "detail": f"{row.get('lane_id') or row.get('strategy_id')} {row.get('symbol')} {pnl}"})
            break
    for lane in lanes:
        if dec(lane.get("net_pnl")) <= Decimal("-500"):
            flags.append({"code": "lane_drawdown_review_needed", "severity": "warning", "detail": str(lane.get("lane_id"))})
            break
    return flags


def build_review(
    *,
    repo_root: Path = REPO_ROOT,
    scope: str = DEFAULT_SCOPE,
    now: datetime | None = None,
    window_hours: int = 24,
    stale_minutes: int = 15,
    process_lines: list[str] | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    window_start = now - timedelta(hours=window_hours)
    runtime_dir = repo_root / RUNTIME_ROOT / scope
    paths = {key: runtime_dir / filename for key, filename in RUNTIME_FILES.items()}
    file_statuses = {key: file_status(path, now) for key, path in paths.items()}
    summary = read_json(paths["summary"])
    state = read_json(paths["state"])
    health = read_json(paths["health"])
    decision_rows = [row for row in iter_jsonl(paths["decisions"]) if in_window(row, window_start, now)]
    trade_rows = [row for row in iter_jsonl(paths["trades"]) if in_window(row, window_start, now)]
    testnet_rows = [row for row in iter_jsonl(paths["testnet"]) if in_window(row, window_start, now)]
    audit_rows = [row for row in iter_jsonl(paths["audit"]) if in_window(row, window_start, now)]
    lanes = summarize_lanes(summary, state)
    open_positions = summarize_open_positions(state, summary)
    processes = runtime_process_lines() if process_lines is None else process_lines
    flags = anomaly_flags(
        file_statuses=file_statuses,
        process_lines=processes,
        decisions=decision_rows,
        trades=trade_rows,
        testnet=testnet_rows,
        open_positions=open_positions,
        lanes=lanes,
        now=now,
        stale_minutes=stale_minutes,
    )
    critical = [flag for flag in flags if flag["severity"] == "critical"]
    warnings = [flag for flag in flags if flag["severity"] == "warning"]
    return {
        "report": "obs_os1_week2_paper_observation_daily_review",
        "generated_at_utc": iso(now),
        "review_window": {
            "scope": scope,
            "window_start_utc": iso(window_start),
            "window_end_utc": iso(now),
            "window_hours": window_hours,
        },
        "runtime": {
            "runtime_dir": str(runtime_dir),
            "process_count": len(processes),
            "process_lines": processes,
            "file_status": file_statuses,
            "summary_status": summary.get("status") or "summary_not_loaded",
            "active_review_scope": summary.get("active_review_scope") or scope,
            "last_update_utc": summary.get("connection_status", {}).get("last_update_utc"),
        },
        "week2_truth": {
            "active_lanes": ACTIVE_LANES,
            "active_timeframes": ACTIVE_TIMEFRAMES,
            "disabled_timeframes": DISABLED_TIMEFRAMES,
            "baseline_testnet_eligible_lane": BASELINE_TESTNET_LANE,
            "candidate_lanes_synthetic_only": [lane for lane in ACTIVE_LANES if lane != BASELINE_TESTNET_LANE],
            "synthetic_pnl_truth": "internal synthetic paper ledgers",
            "strategy_truth": "public Hyperliquid mainnet candles",
            "testnet_fills_update_synthetic_pnl": False,
            "live_trading_approved": False,
            "production_strategy_approved": False,
        },
        "lane_summary": lanes,
        "decision_summary": summarize_decisions(decision_rows),
        "closed_trade_summary": summarize_trades(trade_rows),
        "testnet_lifecycle_summary": summarize_testnet(testnet_rows),
        "open_position_summary": {
            "count": len(open_positions),
            "largest_unrealized_winner": max((dec(row.get("current_unrealized_pnl") or row.get("unrealized_pnl")) for row in open_positions), default=Decimal("0")).to_eng_string(),
            "largest_unrealized_loser": min((dec(row.get("current_unrealized_pnl") or row.get("unrealized_pnl")) for row in open_positions), default=Decimal("0")).to_eng_string(),
            "sample": open_positions[:20],
        },
        "data_health": health,
        "runtime_audit_summary": {
            "rows_in_window": len(audit_rows),
            "latest_audit_time": pick_latest_time(audit_rows),
        },
        "anomaly_flags": flags,
        "recommended_human_review": [
            flag["code"] for flag in flags if flag["severity"] in {"critical", "warning"}
        ][:12],
        "go_no_go": "review_required" if critical else "observation_may_continue_with_review" if warnings else "observation_may_continue",
        "boundaries": {
            "read_only_review": True,
            "runtime_behavior_changed": False,
            "orders_submitted_by_review": False,
            "live_trading_approved": False,
            "strategy_production_approved": False,
        },
    }


def markdown_table(rows: Iterable[Iterable[Any]]) -> str:
    rows = [list(row) for row in rows]
    if not rows:
        return ""
    header = rows[0]
    separator = ["---"] * len(header)
    lines = ["| " + " | ".join(str(cell) for cell in header) + " |", "| " + " | ".join(separator) + " |"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(review: dict[str, Any]) -> str:
    flags = review["anomaly_flags"]
    lane_rows = [["lane", "total equity", "net pnl", "open", "closed", "testnet"]]
    for lane in review["lane_summary"]:
        lane_rows.append([
            lane["lane_id"],
            money(lane["total_equity"]),
            money(lane["net_pnl"]),
            lane["open_positions"],
            lane["closed_trades"],
            "eligible" if lane["testnet_eligible"] else "synthetic-only",
        ])
    reason_rows = [["reason", "count"], *review["decision_summary"]["top_reason_codes"][:10]]
    symbol_rows = [["symbol", "count"], *review["decision_summary"]["top_symbols"][:10]]
    flag_rows = [["severity", "code", "detail"], *[[flag["severity"], flag["code"], flag.get("detail", "")] for flag in flags]]
    return "\n\n".join(
        [
            "# OBS-OS1 Week 2 Paper Observation Daily Review",
            "This is a read-only daily observation pack. It is synthetic paper only, not evidence of edge, not production approval, and not live trading approval.",
            "## Executive Summary",
            f"- Generated at UTC: `{review['generated_at_utc']}`",
            f"- Scope: `{review['review_window']['scope']}`",
            f"- Window: `{review['review_window']['window_start_utc']}` to `{review['review_window']['window_end_utc']}`",
            f"- Runtime processes detected: `{review['runtime']['process_count']}`",
            f"- Go/no-go: `{review['go_no_go']}`",
            f"- Anomaly flags: `{len(flags)}`",
            "## Week 2 Truth",
            f"- Active lanes: `{', '.join(review['week2_truth']['active_lanes'])}`",
            f"- Active timeframes: `{', '.join(review['week2_truth']['active_timeframes'])}`",
            f"- Disabled timeframes: `{', '.join(review['week2_truth']['disabled_timeframes'])}`",
            f"- Baseline testnet-eligible lane: `{review['week2_truth']['baseline_testnet_eligible_lane']}`",
            "- Candidate/MF-ORIG lanes are synthetic-only.",
            "- Testnet fills do not update synthetic PnL.",
            "## Lane Summary",
            markdown_table(lane_rows),
            "## Decisions",
            f"- Decision rows in window: `{review['decision_summary']['count']}`",
            f"- Latest decision time: `{review['decision_summary']['latest_decision_time'] or 'n/a'}`",
            markdown_table(reason_rows),
            markdown_table(symbol_rows),
            "## Synthetic Trades And Open MTM",
            f"- Open positions: `{review['open_position_summary']['count']}`",
            f"- Closed trades: `{review['closed_trade_summary']['count']}`",
            f"- Total closed net PnL: `{money(review['closed_trade_summary']['total_net_pnl'])}`",
            "## Testnet Lifecycle",
            f"- Lifecycle rows in window: `{review['testnet_lifecycle_summary']['count']}`",
            f"- Order endpoint called rows: `{review['testnet_lifecycle_summary']['order_endpoint_called_count']}`",
            f"- Signed order endpoint called rows: `{review['testnet_lifecycle_summary']['signed_order_endpoint_called_count']}`",
            f"- Strategy PnL updates from testnet: `{review['testnet_lifecycle_summary']['strategy_pnl_update_from_testnet_count']}`",
            "## Anomaly Flags",
            markdown_table(flag_rows) if flags else "No anomaly flags were raised.",
            "## Boundaries",
            "- Read-only review only.",
            "- No runtime behavior changed.",
            "- No orders were submitted by this review.",
            "- No live trading was approved.",
            "- No strategy was production-approved.",
        ]
    ) + "\n"


def write_review(review: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    date = str(review["generated_at_utc"]).split("T", 1)[0]
    json_path = output_dir / f"{date}_daily_review.json"
    md_path = output_dir / f"{date}_daily_review.md"
    json_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(review), encoding="utf-8")
    (output_dir / "latest_review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "latest_review.md").write_text(render_markdown(review), encoding="utf-8")
    return json_path, md_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only PT-RT Week 2 daily review pack.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--stale-minutes", type=int, default=15)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--generate", action="store_true", help="Write Markdown/JSON review artifacts under reports/paper_reviews/.")
    parser.add_argument("--status", action="store_true", help="Print review status without writing artifacts.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.window_hours <= 0:
        raise SystemExit("--window-hours must be positive")
    if args.stale_minutes <= 0:
        raise SystemExit("--stale-minutes must be positive")
    review = build_review(scope=args.scope, window_hours=args.window_hours, stale_minutes=args.stale_minutes)
    if args.generate:
        output_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / REVIEW_ROOT / args.scope
        json_path, md_path = write_review(review, output_dir)
        print(f"json: {json_path}")
        print(f"markdown: {md_path}")
    else:
        print(f"scope: {review['review_window']['scope']}")
        print(f"go_no_go: {review['go_no_go']}")
        print(f"anomaly_flags: {len(review['anomaly_flags'])}")
        for flag in review["anomaly_flags"]:
            print(f"- {flag['severity']} {flag['code']}: {flag.get('detail', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
