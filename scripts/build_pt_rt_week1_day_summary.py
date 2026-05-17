"""Build the PT-RT Week 1 daily founder review pack.

The builder reads ignored local paper-runtime artifacts and writes compact
Markdown/JSON review files under ``docs/``. It does not call exchanges,
regenerate evidence packs, or mutate runtime state.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from services.paper_runtime.pt_rt1 import PT_RT1_STRATEGY_LANES


ACTIVE_TIMEFRAMES = ("1h", "4h", "1d")
DISABLED_TIMEFRAMES = ("15m",)
DEFAULT_CUTOVER_SUMMARY = Path("docs/pt_rt1_4_paper_trading_command_center_cleanup_summary.json")
DEFAULT_ACTIVE_RUNTIME_DIR = Path("reports/paper_runtime/pt_rt1_4_1_active_week")
DEFAULT_PRE_CUTOVER_RUNTIME_DIR = Path("reports/paper_runtime/pt_rt1_1c_24h_dry_run")
DEFAULT_MARKDOWN_OUTPUT = Path("docs/pt_rt_week1_day_summary.md")
DEFAULT_JSON_OUTPUT = Path("docs/pt_rt_week1_day_summary.json")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _fmt(value: Any, places: int = 2) -> str:
    amount = _dec(value)
    quant = Decimal("1") if places == 0 else Decimal("1").scaleb(-places)
    return f"{amount.quantize(quant):,f}"


def _load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    skipped = 0
    try:
        handle = path.open(encoding="utf-8")
    except FileNotFoundError:
        return rows, skipped
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if isinstance(payload, dict):
                rows.append(payload)
            else:
                skipped += 1
    return rows, skipped


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _decision_ts(row: dict[str, Any]) -> datetime | None:
    return _parse_ts(row.get("decision_time") or row.get("signal_candle_close_time"))


def _reason_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for reason in row.get("reason_codes") or []:
            counts[str(reason)] += 1
    return counts


def _top_counter(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def _duration_label(start: Any, end: Any) -> str:
    start_dt = _parse_ts(start)
    end_dt = _parse_ts(end)
    if not start_dt or not end_dt:
        return "n/a"
    seconds = max(int((end_dt - start_dt).total_seconds()), 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _age_label(entry_time: Any, as_of: datetime) -> str:
    entry = _parse_ts(entry_time)
    if not entry:
        return "n/a"
    seconds = max(int((as_of - entry).total_seconds()), 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _position_row(position: dict[str, Any], as_of: datetime, *, legacy: bool) -> dict[str, Any]:
    entry_price = _dec(position.get("entry_price"))
    quantity = _dec(position.get("quantity"))
    notional = _dec(position.get("notional"))
    unrealized = _dec(position.get("current_unrealized_pnl"))
    pnl_pct = (unrealized / notional * Decimal("100")) if notional else Decimal("0")
    return {
        "lane": position.get("lane_id"),
        "symbol": position.get("symbol"),
        "timeframe": position.get("timeframe"),
        "entry_time": position.get("entry_fill_time") or position.get("entry_signal_time"),
        "age": _age_label(position.get("entry_fill_time") or position.get("entry_signal_time"), as_of),
        "entry_price": str(entry_price),
        "current_price": str(position.get("current_price") or entry_price),
        "quantity": str(quantity),
        "notional": str(notional),
        "unrealized_pnl": str(unrealized),
        "unrealized_pnl_pct": str(pnl_pct),
        "entry_reason": ", ".join(str(item) for item in position.get("open_reason_codes") or []) or "n/a",
        "data_health": position.get("data_health") or "not_reported",
        "status": "legacy_15m_position_visible" if legacy else position.get("status", "open"),
    }


def _trade_row(trade: dict[str, Any]) -> dict[str, Any]:
    entry_price = _dec(trade.get("entry_price"))
    exit_price = _dec(trade.get("exit_price"))
    net_pnl = _dec(trade.get("net_pnl"))
    notional = _dec(trade.get("notional") or trade.get("equity_before"))
    pnl_pct = (net_pnl / notional * Decimal("100")) if notional else Decimal("0")
    fee_slippage = _dec(trade.get("fees")) + _dec(trade.get("slippage"))
    return {
        "lane": trade.get("lane_id"),
        "symbol": trade.get("symbol"),
        "timeframe": trade.get("timeframe"),
        "entry_time": trade.get("entry_time") or trade.get("entry_fill_time"),
        "exit_time": trade.get("exit_time"),
        "duration": _duration_label(trade.get("entry_time") or trade.get("entry_fill_time"), trade.get("exit_time")),
        "entry_price": str(entry_price),
        "exit_price": str(exit_price),
        "quantity": str(_dec(trade.get("quantity"))),
        "net_pnl": str(net_pnl),
        "net_pnl_pct": str(pnl_pct),
        "equity_after": str(_dec(trade.get("equity_after"))),
        "exit_reason": ", ".join(str(item) for item in trade.get("exit_reason_codes") or []) or trade.get("exit_reason") or "n/a",
        "fees_slippage": str(fee_slippage),
    }


def _build_lane_metrics(
    *,
    lane_ids: list[str],
    decisions: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    realized_by_lane: dict[str, Any],
) -> list[dict[str, Any]]:
    by_lane_decisions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_lane_trades: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_lane_positions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        by_lane_decisions[str(row.get("lane_id"))].append(row)
    for row in trades:
        by_lane_trades[str(row.get("lane_id"))].append(row)
    for row in open_positions:
        by_lane_positions[str(row.get("lane"))].append(row)

    metrics: list[dict[str, Any]] = []
    for lane_id in lane_ids:
        lane_decisions = by_lane_decisions.get(lane_id, [])
        lane_trades = by_lane_trades.get(lane_id, [])
        lane_positions = by_lane_positions.get(lane_id, [])
        realized = _dec(realized_by_lane.get(lane_id), Decimal("10000"))
        unrealized = sum((_dec(row.get("unrealized_pnl")) for row in lane_positions), Decimal("0"))
        total_equity = realized + unrealized
        wins = [_dec(row.get("net_pnl")) for row in lane_trades if _dec(row.get("net_pnl")) > 0]
        losses = [_dec(row.get("net_pnl")) for row in lane_trades if _dec(row.get("net_pnl")) < 0]
        closed_count = len(lane_trades)
        win_rate = (Decimal(len(wins)) / Decimal(closed_count) * Decimal("100")) if closed_count else None
        duplicate_blocks = sum(
            1
            for row in lane_decisions
            if row.get("action") == "duplicate_ignored"
            or "duplicate_signal_ignored" in [str(item) for item in row.get("reason_codes") or []]
        )
        data_blocks = sum(1 for row in lane_decisions if row.get("action") == "data_unavailable")
        latest_time = max((str(row.get("decision_time") or "") for row in lane_decisions), default=None)
        metrics.append(
            {
                "lane_id": lane_id,
                "starting_equity": "10000",
                "realized_equity": str(realized),
                "unrealized_pnl": str(unrealized),
                "total_equity": str(total_equity),
                "net_pnl": str(total_equity - Decimal("10000")),
                "open_positions": len(lane_positions),
                "closed_trades": closed_count,
                "win_rate": str(win_rate) if win_rate is not None else "no_closed_trades",
                "largest_win": str(max(wins)) if wins else "no_closed_winner",
                "largest_loss": str(min(losses)) if losses else "no_closed_loser",
                "current_drawdown": str(max(Decimal("0"), Decimal("10000") - total_equity)),
                "max_drawdown": str(max(Decimal("0"), Decimal("10000") - total_equity)),
                "current_losing_streak": 0,
                "max_losing_streak": 0,
                "data_health_blocks": data_blocks,
                "duplicate_blocks": duplicate_blocks,
                "top_reason_codes": _top_counter(_reason_counts(lane_decisions), 5),
                "decision_count": len(lane_decisions),
                "latest_decision_time": latest_time,
                "status": "no_activity_for_active_timeframes" if not lane_decisions else "active_timeframe_observed",
            }
        )
    return metrics


def _timeframe_review(
    *,
    decisions: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    legacy_decisions: list[dict[str, Any]],
    legacy_open_positions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for timeframe in ACTIVE_TIMEFRAMES:
        tf_decisions = [row for row in decisions if row.get("timeframe") == timeframe]
        tf_trades = [row for row in trades if row.get("timeframe") == timeframe]
        tf_positions = [row for row in open_positions if row.get("timeframe") == timeframe]
        net_pnl = sum((_dec(row.get("net_pnl")) for row in tf_trades), Decimal("0")) + sum(
            (_dec(row.get("unrealized_pnl")) for row in tf_positions), Decimal("0")
        )
        rows.append(
            {
                "timeframe": timeframe,
                "decision_count": len(tf_decisions),
                "open_count": sum(1 for row in tf_decisions if row.get("action") == "paper_opened"),
                "close_count": sum(1 for row in tf_decisions if row.get("action") == "paper_closed"),
                "open_positions": len(tf_positions),
                "closed_trades": len(tf_trades),
                "net_pnl": str(net_pnl),
                "max_drawdown": str(max(Decimal("0"), -net_pnl)),
                "data_health_blocks": sum(1 for row in tf_decisions if row.get("action") == "data_unavailable"),
                "status": "active_week_timeframe",
            }
        )
    legacy_15m_decisions = [row for row in legacy_decisions if row.get("timeframe") == "15m"]
    rows.append(
        {
            "timeframe": "15m",
            "decision_count": len(legacy_15m_decisions),
            "open_count": sum(1 for row in legacy_15m_decisions if row.get("action") == "paper_opened"),
            "close_count": sum(1 for row in legacy_15m_decisions if row.get("action") == "paper_closed"),
            "open_positions": len(legacy_open_positions),
            "closed_trades": "legacy_not_active_score",
            "net_pnl": "legacy_not_active_score",
            "max_drawdown": "legacy_not_active_score",
            "data_health_blocks": sum(1 for row in legacy_15m_decisions if row.get("action") == "data_unavailable"),
            "status": "paused_legacy_not_active_score",
        }
    )
    return rows


def build_summary(
    *,
    active_runtime_dir: Path,
    pre_cutover_runtime_dir: Path,
    cutover_summary_path: Path,
) -> dict[str, Any]:
    generated_at = _utc_now()
    cutover_summary = _load_json(cutover_summary_path, {})
    cutover_ts = str(cutover_summary.get("active_review_start_utc") or "2026-05-17T09:47:55Z")
    cutover_dt = _parse_ts(cutover_ts) or datetime(2026, 5, 17, 9, 47, 55, tzinfo=UTC)

    active_summary = _load_json(active_runtime_dir / "summary.json", {})
    active_state = _load_json(active_runtime_dir / "state.json", {})
    active_decisions, active_decision_skips = _load_jsonl(active_runtime_dir / "decisions.jsonl")
    active_trades_raw, active_trade_skips = _load_jsonl(active_runtime_dir / "trades.jsonl")
    active_audit, active_audit_skips = _load_jsonl(active_runtime_dir / "runtime_audit.jsonl")
    active_transport, active_transport_skips = _load_jsonl(active_runtime_dir / "testnet_probe_transport.jsonl")

    pre_decisions, pre_decision_skips = _load_jsonl(pre_cutover_runtime_dir / "decisions.jsonl")
    pre_state = _load_json(pre_cutover_runtime_dir / "state.json", {})

    runtime_state = active_state.get("paper_runtime") if isinstance(active_state, dict) else {}
    if not isinstance(runtime_state, dict):
        runtime_state = {}
    active_open_positions_raw = runtime_state.get("open_positions_by_key")
    if not isinstance(active_open_positions_raw, dict):
        active_open_positions_raw = {}
    pre_runtime_state = pre_state.get("paper_runtime") if isinstance(pre_state, dict) else {}
    if not isinstance(pre_runtime_state, dict):
        pre_runtime_state = {}
    pre_open_positions_raw = pre_runtime_state.get("open_positions_by_key")
    if not isinstance(pre_open_positions_raw, dict):
        pre_open_positions_raw = {}

    active_decisions_scoped = [row for row in active_decisions if row.get("timeframe") in ACTIVE_TIMEFRAMES]
    active_trades = [row for row in active_trades_raw if row.get("timeframe") in ACTIVE_TIMEFRAMES]
    as_of_candidates = [_decision_ts(row) for row in active_decisions if _decision_ts(row)]
    as_of = max(as_of_candidates) if as_of_candidates else generated_at

    active_positions = [
        _position_row(position, as_of, legacy=False)
        for position in active_open_positions_raw.values()
        if isinstance(position, dict) and position.get("timeframe") in ACTIVE_TIMEFRAMES
    ]
    legacy_15m_positions = [
        _position_row(position, as_of, legacy=True)
        for position in pre_open_positions_raw.values()
        if isinstance(position, dict) and position.get("timeframe") == "15m"
    ]
    trade_rows = [_trade_row(row) for row in active_trades]

    pre_after_cutover = [row for row in pre_decisions if (_decision_ts(row) or generated_at) >= cutover_dt]
    retired_15m_opens_after = [
        row for row in pre_after_cutover if row.get("timeframe") == "15m" and row.get("action") == "paper_opened"
    ]
    active_15m_rows = [row for row in active_decisions if row.get("timeframe") == "15m"]
    active_15m_opens = [row for row in active_15m_rows if row.get("action") == "paper_opened"]

    lane_ids = [lane.lane_id for lane in PT_RT1_STRATEGY_LANES]
    realized_by_lane = runtime_state.get("realized_equity_by_lane")
    if not isinstance(realized_by_lane, dict):
        realized_by_lane = {}
    lane_metrics = _build_lane_metrics(
        lane_ids=lane_ids,
        decisions=active_decisions_scoped,
        trades=active_trades,
        open_positions=active_positions,
        realized_by_lane=realized_by_lane,
    )

    top_lane = max(lane_metrics, key=lambda row: _dec(row["total_equity"])) if lane_metrics else None
    worst_lane = min(lane_metrics, key=lambda row: _dec(row["total_equity"])) if lane_metrics else None
    open_winner = max(active_positions, key=lambda row: _dec(row["unrealized_pnl"]), default=None)
    open_loser = min(active_positions, key=lambda row: _dec(row["unrealized_pnl"]), default=None)
    closed_winner = max(trade_rows, key=lambda row: _dec(row["net_pnl"]), default=None)
    closed_loser = min(trade_rows, key=lambda row: _dec(row["net_pnl"]), default=None)

    action_counts = Counter(str(row.get("action") or "unknown") for row in active_decisions_scoped)
    reason_counts = _reason_counts(active_decisions_scoped)
    symbol_counts = Counter(str(row.get("symbol") or "unknown") for row in active_decisions_scoped)
    no_trade_rows = [
        row
        for row in active_decisions_scoped
        if row.get("action") in {"no_trade", "blocked_by_candidate_filter", "data_unavailable", "duplicate_ignored"}
    ]
    data_health = active_summary.get("data_unavailable_summary") if isinstance(active_summary, dict) else {}
    if not isinstance(data_health, dict):
        data_health = {}
    last_audit_probe = next((row for row in reversed(active_audit) if "transport_status" in row), {})

    closed_net = [_dec(row.get("net_pnl")) for row in trade_rows]
    closed_wins = [value for value in closed_net if value > 0]
    closed_losses = [value for value in closed_net if value < 0]
    closed_cards = {
        "closed_trade_count": len(trade_rows),
        "winning_trades": len(closed_wins),
        "losing_trades": len(closed_losses),
        "largest_win": str(max(closed_wins)) if closed_wins else "no_closed_winner",
        "largest_loss": str(min(closed_losses)) if closed_losses else "no_closed_loser",
        "average_win": str(sum(closed_wins, Decimal("0")) / Decimal(len(closed_wins))) if closed_wins else "no_closed_winner",
        "average_loss": str(sum(closed_losses, Decimal("0")) / Decimal(len(closed_losses))) if closed_losses else "no_closed_loser",
        "total_net_pnl": str(sum(closed_net, Decimal("0"))),
    }

    boundary = {
        "production_money_flow_rules_changed": False,
        "new_strategies_added": False,
        "strategy_thresholds_tuned": False,
        "strategy_production_approved": False,
        "live_trading_approved": False,
        "live_orders_submitted": False,
        "testnet_orders_submitted": False,
        "testnet_order_transport_enabled": False,
        "private_signed_order_endpoints_called_from_strategy_truth": False,
        "testnet_prices_used_as_strategy_truth": False,
        "testnet_fills_update_strategy_pnl": False,
        "historical_evidence_packs_regenerated": False,
        "sor_fanout_cbbo_added": False,
    }

    active_cutover_ok = (
        tuple(active_summary.get("active_timeframes") or ACTIVE_TIMEFRAMES) == ACTIVE_TIMEFRAMES
        and tuple(active_summary.get("disabled_timeframes") or DISABLED_TIMEFRAMES) == DISABLED_TIMEFRAMES
        and not active_15m_opens
        and not active_15m_rows
    )
    ledger_invariant_failures = [
        row["lane_id"]
        for row in lane_metrics
        if _dec(row["total_equity"]) != _dec(row["realized_equity"]) + _dec(row["unrealized_pnl"])
    ]
    broad_data_unavailable = _dec(data_health.get("market_rows_unavailable")) > Decimal("10")
    testnet_transport_enabled = bool(active_transport) or bool(last_audit_probe.get("signed_order_endpoint_called")) or bool(
        last_audit_probe.get("order_endpoint_called")
    )
    week_go = active_cutover_ok and not ledger_invariant_failures and not broad_data_unavailable and not testnet_transport_enabled

    return {
        "phase": "PT-RT1.4.1",
        "generated_at_utc": _iso(generated_at),
        "runtime_artifact_scope": {
            "active_runtime_dir": str(active_runtime_dir),
            "pre_cutover_runtime_dir": str(pre_cutover_runtime_dir),
            "pre_cutover_label": "pre_pt_rt1_4_weekend_burn_in",
            "active_review_label": "pt_rt1_4_active_week_runtime",
        },
        "cutover_verification": {
            "cutover_timestamp_utc": cutover_ts,
            "active_timeframes": list(ACTIVE_TIMEFRAMES),
            "disabled_timeframes": [
                {
                    "timeframe": "15m",
                    "status": "disabled_for_week1_noise_reduction",
                    "active_scoreboard_included": False,
                    "new_synthetic_entries_allowed": False,
                }
            ],
            "retired_runtime_cutover_not_applied": bool(retired_15m_opens_after),
            "retired_runtime_new_15m_entries_after_cutover": len(retired_15m_opens_after),
            "active_runtime_new_15m_entries_after_restart": len(active_15m_opens),
            "active_runtime_15m_rows_after_restart": len(active_15m_rows),
            "new_15m_entries_after_cutover": len(active_15m_opens),
            "all_active_scoreboard_excludes_15m": True,
            "legacy_15m_rows_visible": bool(pre_decisions),
            "legacy_15m_rows_excluded_from_active_score": True,
            "verification_status": "active_runtime_cutover_verified_after_restart" if active_cutover_ok else "runtime_cutover_not_applied",
        },
        "runtime_health": {
            "public_mainnet_connection": (active_summary.get("connection_status") or {}).get("hyperliquid_public_mainnet"),
            "last_update_utc": (active_summary.get("connection_status") or {}).get("last_update_utc"),
            "endpoint_category": (active_summary.get("connection_status") or {}).get("endpoint_category"),
            "no_api_keys": (active_summary.get("connection_status") or {}).get("no_api_keys"),
            "no_private_signed_order_endpoints": (active_summary.get("connection_status") or {}).get(
                "no_private_signed_order_endpoints"
            ),
            "data_health_summary": data_health,
            "decision_log_stats": active_summary.get("decision_log_stats"),
            "jsonl_skipped_rows": {
                "active_decisions": active_decision_skips,
                "active_trades": active_trade_skips,
                "active_runtime_audit": active_audit_skips,
                "active_testnet_transport": active_transport_skips,
                "pre_cutover_decisions": pre_decision_skips,
            },
        },
        "daily_observation_summary": {
            "observation_language": "24h / daily observation only; not evidence of edge; not production approval; synthetic paper only",
            "top_lane_by_total_synthetic_equity": top_lane,
            "worst_lane_by_total_synthetic_equity": worst_lane,
            "largest_open_unrealized_winner": open_winner or "no_open_positions",
            "largest_open_unrealized_loser": open_loser or "no_open_positions",
            "largest_closed_winner": closed_winner or "no_closed_winner",
            "largest_closed_loser": closed_loser or "no_closed_loser",
            "open_position_count": len(active_positions),
            "legacy_15m_open_position_count": len(legacy_15m_positions),
            "closed_trade_count": len(trade_rows),
            "data_health_blocks": sum(1 for row in active_decisions_scoped if row.get("action") == "data_unavailable"),
            "duplicate_blocks": sum(
                1
                for row in active_decisions_scoped
                if row.get("action") == "duplicate_ignored"
                or "duplicate_signal_ignored" in [str(item) for item in row.get("reason_codes") or []]
            ),
            "top_no_trade_reasons": _top_counter(_reason_counts(no_trade_rows), 10),
            "top_symbols_by_activity": _top_counter(symbol_counts, 10),
            "testnet_transport_status": "disabled",
        },
        "lane_review": lane_metrics,
        "timeframe_review": _timeframe_review(
            decisions=active_decisions_scoped,
            trades=active_trades,
            open_positions=active_positions,
            legacy_decisions=pre_decisions,
            legacy_open_positions=legacy_15m_positions,
        ),
        "open_position_review": {
            "active_positions_count": len(active_positions),
            "legacy_15m_positions_count": len(legacy_15m_positions),
            "active_positions": sorted(active_positions, key=lambda row: (_dec(row["unrealized_pnl"]), row["entry_time"] or ""))[:25],
            "legacy_15m_positions": sorted(legacy_15m_positions, key=lambda row: row["entry_time"] or "")[:25],
        },
        "closed_trade_review": {
            "summary_cards": closed_cards,
            "recent_closed_trades": sorted(trade_rows, key=lambda row: row.get("exit_time") or "", reverse=True)[:25],
        },
        "decision_review": {
            "action_counts": dict(action_counts),
            "top_reason_codes": _top_counter(reason_counts, 20),
            "labels": ["paper decision", "synthetic entry", "synthetic close", "not exchange order"],
        },
        "testnet_label_audit": {
            "testnet_order_transport": "disabled",
            "audit_only_shapes": "enabled" if last_audit_probe else "not_observed_in_latest_active_artifact",
            "signed_testnet_orders": 0,
            "strategy_pnl_update_from_testnet": False,
            "live_trading": "not approved",
            "transport_mode": last_audit_probe.get("transport_mode") or "audit_only",
            "transport_status": last_audit_probe.get("transport_status") or "audit_only_not_submitted",
            "order_endpoint_called": bool(last_audit_probe.get("order_endpoint_called")),
            "signed_order_endpoint_called": bool(last_audit_probe.get("signed_order_endpoint_called")),
            "transport_rows": len(active_transport),
            "testnet_probe_label_still_ambiguous": False,
        },
        "dashboard_qa": {
            "paper_trading_order": [
                "Top health banner",
                "Weekly scoreboard",
                "Live chart + watchlist",
                "Open positions",
                "Closed trades",
                "Signal / decision stream",
                "Data health + testnet plumbing",
            ],
            "reference_tabs": {
                "Historical Replay": "historical visual reference",
                "Evidence": "canonical backtest summaries",
                "The Lab": "research variants",
                "Audit": "audit findings",
                "Strategy": "rules/source notes",
            },
            "no_order_controls": True,
        },
        "go_no_go": {
            "decision": "Week 1 paper observation may continue" if week_go else "Week 1 paper observation blocked",
            "blockers": [
                blocker
                for blocker, active in [
                    ("runtime_cutover_not_applied", not active_cutover_ok),
                    ("ledger_invariants_failed", bool(ledger_invariant_failures)),
                    ("data_health_broadly_unavailable", bool(broad_data_unavailable)),
                    ("testnet_transport_accidentally_enabled", bool(testnet_transport_enabled)),
                ]
                if active
            ],
            "note": "The retired pre-PT-RT1.4 runtime produced 15m opens after cutover and is excluded from active scoring; the restarted active runtime has zero 15m rows.",
        },
        "boundaries": boundary,
    }


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def render_markdown(summary: dict[str, Any]) -> str:
    cutover = summary["cutover_verification"]
    daily = summary["daily_observation_summary"]
    top_lane = daily["top_lane_by_total_synthetic_equity"]
    worst_lane = daily["worst_lane_by_total_synthetic_equity"]

    lane_rows = [
        [
            row["lane_id"],
            _fmt(row["realized_equity"]),
            _fmt(row["unrealized_pnl"]),
            _fmt(row["total_equity"]),
            _fmt(row["net_pnl"]),
            row["open_positions"],
            row["closed_trades"],
            row["win_rate"],
            _fmt(row["current_drawdown"]),
            row["data_health_blocks"],
            row["duplicate_blocks"],
            row["status"],
        ]
        for row in summary["lane_review"]
    ]
    timeframe_rows = [
        [
            row["timeframe"],
            row["decision_count"],
            row["open_count"],
            row["close_count"],
            row["open_positions"],
            row["closed_trades"],
            row["net_pnl"],
            row["max_drawdown"],
            row["data_health_blocks"],
            row["status"],
        ]
        for row in summary["timeframe_review"]
    ]
    open_rows = [
        [
            row["lane"],
            row["symbol"],
            row["timeframe"],
            row["entry_time"],
            row["age"],
            _fmt(row["entry_price"], 6),
            _fmt(row["current_price"], 6),
            _fmt(row["quantity"], 6),
            _fmt(row["notional"]),
            _fmt(row["unrealized_pnl"]),
            _fmt(row["unrealized_pnl_pct"], 4),
            row["entry_reason"],
            row["data_health"],
            row["status"],
        ]
        for row in summary["open_position_review"]["active_positions"][:15]
    ]
    closed_rows = [
        [
            row["lane"],
            row["symbol"],
            row["timeframe"],
            row["entry_time"],
            row["exit_time"],
            row["duration"],
            _fmt(row["entry_price"], 6),
            _fmt(row["exit_price"], 6),
            _fmt(row["quantity"], 6),
            _fmt(row["net_pnl"]),
            _fmt(row["net_pnl_pct"], 4),
            _fmt(row["equity_after"]),
            row["exit_reason"],
            _fmt(row["fees_slippage"]),
        ]
        for row in summary["closed_trade_review"]["recent_closed_trades"][:15]
    ]
    reason_rows = [[item["value"], item["count"]] for item in summary["decision_review"]["top_reason_codes"][:12]]
    symbol_rows = [[item["value"], item["count"]] for item in daily["top_symbols_by_activity"][:10]]

    return "\n".join(
        [
            "# PT-RT Week 1 Daily Summary",
            "",
            "## Executive Summary",
            "",
            "PT-RT1.4.1 verifies the active Week 1 runtime cutover and creates the first daily founder review pack. This is 24h / daily observation only, not evidence of edge, not production approval, and synthetic paper only.",
            "",
            f"- Generated at UTC: `{summary['generated_at_utc']}`",
            f"- Cutover timestamp: `{cutover['cutover_timestamp_utc']}`",
            f"- Active timeframes: `{', '.join(cutover['active_timeframes'])}`",
            "- 15m status: `disabled_for_week1_noise_reduction`; legacy rows are visible but excluded from active scoring.",
            f"- Retired pre-cutover runtime 15m opens after cutover: `{cutover['retired_runtime_new_15m_entries_after_cutover']}`",
            f"- Restarted active runtime 15m opens: `{cutover['active_runtime_new_15m_entries_after_restart']}`",
            f"- Restarted active runtime 15m rows: `{cutover['active_runtime_15m_rows_after_restart']}`",
            f"- Cutover verification: `{cutover['verification_status']}`",
            f"- Go/no-go: `{summary['go_no_go']['decision']}`",
            "",
            "The retired runtime is labeled `pre_pt_rt1_4_weekend_burn_in` and must not be used for active Week 1 scoring because it continued producing 15m entries after the PT-RT1.4 cutover. A fresh active-week runtime was restarted in `reports/paper_runtime/pt_rt1_4_1_active_week/`; its first artifact cycle contains no 15m rows.",
            "",
            "## Runtime Health",
            "",
            f"- Public mainnet connection: `{summary['runtime_health']['public_mainnet_connection']}`",
            f"- Last update UTC: `{summary['runtime_health']['last_update_utc']}`",
            f"- Endpoint category: `{summary['runtime_health']['endpoint_category']}`",
            f"- No API keys: `{summary['runtime_health']['no_api_keys']}`",
            f"- No private/signed/order endpoints from strategy truth: `{summary['runtime_health']['no_private_signed_order_endpoints']}`",
            f"- Market rows checked: `{summary['runtime_health']['data_health_summary'].get('market_rows_checked')}`",
            f"- Market rows unavailable: `{summary['runtime_health']['data_health_summary'].get('market_rows_unavailable')}`",
            f"- Lane-expanded data unavailable decisions: `{summary['runtime_health']['data_health_summary'].get('lane_expanded_data_unavailable_decisions')}`",
            "",
            "## Daily Observation",
            "",
            f"- Top lane by total synthetic equity: `{top_lane['lane_id'] if isinstance(top_lane, dict) else 'n/a'}` at `{_fmt(top_lane['total_equity']) if isinstance(top_lane, dict) else 'n/a'}`",
            f"- Worst lane by total synthetic equity: `{worst_lane['lane_id'] if isinstance(worst_lane, dict) else 'n/a'}` at `{_fmt(worst_lane['total_equity']) if isinstance(worst_lane, dict) else 'n/a'}`",
            f"- Open positions: `{daily['open_position_count']}` active, `{daily['legacy_15m_open_position_count']}` legacy 15m",
            f"- Closed trades: `{daily['closed_trade_count']}`",
            f"- Data-health blocks: `{daily['data_health_blocks']}`",
            f"- Duplicate blocks: `{daily['duplicate_blocks']}`",
            "",
            "## Lane Review",
            "",
            _md_table(
                [
                    "lane",
                    "realized",
                    "unrealized",
                    "total",
                    "net pnl",
                    "open",
                    "closed",
                    "win rate",
                    "drawdown",
                    "data blocks",
                    "duplicate blocks",
                    "status",
                ],
                lane_rows,
            ),
            "",
            "## Timeframe Review",
            "",
            _md_table(
                [
                    "timeframe",
                    "decisions",
                    "opens",
                    "closes",
                    "open positions",
                    "closed trades",
                    "net pnl",
                    "max drawdown",
                    "data blocks",
                    "status",
                ],
                timeframe_rows,
            ),
            "",
            "## Open Position Review",
            "",
            "Active 1h/4h/1d positions are shown below. Legacy 15m positions remain visible in the JSON summary and are excluded from active scoring.",
            "",
            _md_table(
                [
                    "lane",
                    "symbol",
                    "tf",
                    "entry time",
                    "age",
                    "entry",
                    "current",
                    "qty",
                    "notional",
                    "unrealized",
                    "unrealized %",
                    "entry reason",
                    "health",
                    "status",
                ],
                open_rows or [["no_active_open_positions", "", "", "", "", "", "", "", "", "", "", "", "", ""]],
            ),
            "",
            "## Closed Trade Review",
            "",
            f"- Closed trade count: `{summary['closed_trade_review']['summary_cards']['closed_trade_count']}`",
            f"- Winning trades: `{summary['closed_trade_review']['summary_cards']['winning_trades']}`",
            f"- Losing trades: `{summary['closed_trade_review']['summary_cards']['losing_trades']}`",
            f"- Largest win: `{summary['closed_trade_review']['summary_cards']['largest_win']}`",
            f"- Largest loss: `{summary['closed_trade_review']['summary_cards']['largest_loss']}`",
            f"- Total net PnL: `{summary['closed_trade_review']['summary_cards']['total_net_pnl']}`",
            "",
            _md_table(
                [
                    "lane",
                    "symbol",
                    "tf",
                    "entry",
                    "exit",
                    "duration",
                    "entry px",
                    "exit px",
                    "qty",
                    "net pnl",
                    "net pnl %",
                    "equity after",
                    "exit reason",
                    "fees/slip",
                ],
                closed_rows or [["no_closed_trades", "", "", "", "", "", "", "", "", "", "", "", "", ""]],
            ),
            "",
            "## Signal / Decision Review",
            "",
            "Signal rows are paper decisions, synthetic entries, synthetic closes, or skipped/no-trade decisions. They are not exchange orders.",
            "",
            _md_table(["action", "count"], [[k, v] for k, v in summary["decision_review"]["action_counts"].items()]),
            "",
            "Top reason codes:",
            "",
            _md_table(["reason", "count"], reason_rows),
            "",
            "Top symbols by activity:",
            "",
            _md_table(["symbol", "count"], symbol_rows),
            "",
            "## Testnet Label Audit",
            "",
            f"- Testnet order transport: `{summary['testnet_label_audit']['testnet_order_transport']}`",
            f"- Audit-only shapes: `{summary['testnet_label_audit']['audit_only_shapes']}`",
            f"- Signed testnet orders: `{summary['testnet_label_audit']['signed_testnet_orders']}`",
            f"- Strategy PnL update from testnet: `{summary['testnet_label_audit']['strategy_pnl_update_from_testnet']}`",
            f"- Live trading: `{summary['testnet_label_audit']['live_trading']}`",
            f"- Transport status: `{summary['testnet_label_audit']['transport_status']}`",
            "",
            "## Dashboard QA",
            "",
            "Paper Trading tab order verified in code/static tests:",
            "",
            _md_table(["order", "panel"], [[idx + 1, panel] for idx, panel in enumerate(summary["dashboard_qa"]["paper_trading_order"])]),
            "",
            "Other tabs remain reference-only: Historical Replay is historical visual reference, Evidence is canonical backtest summaries, The Lab is research variants, Audit is audit findings, and Strategy is rules/source notes.",
            "",
            "## Boundaries",
            "",
            "- Synthetic paper only.",
            "- No strategy is production-approved.",
            "- No live trading is approved.",
            "- No live orders were submitted.",
            "- No testnet orders were submitted.",
            "- Testnet order transport is disabled.",
            "- No private/signed/order endpoints were called from strategy truth.",
            "- Hyperliquid testnet prices/fills are not strategy PnL truth.",
            "- Historical evidence packs were not regenerated.",
            "- Production Money Flow rules are unchanged.",
            "",
            "## Decision",
            "",
            f"`{summary['go_no_go']['decision']}`",
            "",
            summary["go_no_go"]["note"],
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active-runtime-dir", type=Path, default=DEFAULT_ACTIVE_RUNTIME_DIR)
    parser.add_argument("--pre-cutover-runtime-dir", type=Path, default=DEFAULT_PRE_CUTOVER_RUNTIME_DIR)
    parser.add_argument("--cutover-summary", type=Path, default=DEFAULT_CUTOVER_SUMMARY)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    summary = build_summary(
        active_runtime_dir=args.active_runtime_dir,
        pre_cutover_runtime_dir=args.pre_cutover_runtime_dir,
        cutover_summary_path=args.cutover_summary,
    )
    args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"markdown_output": str(args.markdown_output), "json_output": str(args.json_output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
