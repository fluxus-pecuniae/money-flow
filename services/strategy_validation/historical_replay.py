"""Historical Money Flow replay export helpers for PT0.0.2."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import func

from db.models import CandleModel
from db.session import SessionLocal


PT002_REPORT_NAME = "pt0_0_2_historical_strategy_replay_cockpit"
PT002_SYMBOLS = ("BTC", "ETH", "SOL")
PT002_TIMEFRAMES = ("15m", "1h", "4h")
PT002_INITIAL_EQUITY = "10000"
PT002_FILL_ASSUMPTIONS = (
    "next_candle_open",
    "next_candle_close",
    "same_candle_close_research_only",
)
PT002_DEFAULT_FILL_ASSUMPTION = "next_candle_open"
PT002_SOURCE_KIND = "trusted_offline_historical_candles"
PT002_WINDOW_CONVENTION = "(start_at, end_at]"


@dataclass(frozen=True)
class HistoricalReplayDatasetAudit:
    symbol: str
    timeframe: str
    available: bool
    start_time: str | None
    end_time: str | None
    candle_count: int
    expected_candle_count: int | None
    coverage_percent: str | None
    missing_windows: list[str]
    selected_data_source: str
    replay_ready: bool
    reason_codes: tuple[str, ...]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _money(value: Any, places: int = 8) -> str:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        decimal = Decimal("0")
    quant = Decimal("1").scaleb(-places)
    return str(decimal.quantize(quant))


def _source_hash(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_replay_dataset_audit_to_dict(audit: HistoricalReplayDatasetAudit) -> dict[str, Any]:
    return {
        "symbol": audit.symbol,
        "timeframe": audit.timeframe,
        "available": audit.available,
        "start_time": audit.start_time,
        "end_time": audit.end_time,
        "candle_count": audit.candle_count,
        "expected_candle_count": audit.expected_candle_count,
        "coverage_percent": audit.coverage_percent,
        "missing_windows": audit.missing_windows,
        "selected_data_source": audit.selected_data_source,
        "replay_ready": audit.replay_ready,
        "reason_codes": list(audit.reason_codes),
    }


def audit_persisted_historical_candles(
    *,
    session_factory: Any = SessionLocal,
    symbols: tuple[str, ...] = PT002_SYMBOLS,
    timeframes: tuple[str, ...] = PT002_TIMEFRAMES,
    venue: str = "hyperliquid",
) -> list[HistoricalReplayDatasetAudit]:
    """Audit persisted strategy-validation candles without using live/testnet market truth."""

    rows: list[HistoricalReplayDatasetAudit] = []
    try:
        with session_factory() as session:
            for symbol in symbols:
                for timeframe in timeframes:
                    count, first_close, last_close = (
                        session.query(
                            func.count(CandleModel.id),
                            func.min(CandleModel.close_time),
                            func.max(CandleModel.close_time),
                        )
                        .filter(
                            CandleModel.venue == venue,
                            CandleModel.symbol == symbol,
                            CandleModel.timeframe == timeframe,
                        )
                        .one()
                    )
                    available = bool(count)
                    rows.append(
                        HistoricalReplayDatasetAudit(
                            symbol=symbol,
                            timeframe=timeframe,
                            available=available,
                            start_time=first_close.isoformat() if first_close else None,
                            end_time=last_close.isoformat() if last_close else None,
                            candle_count=int(count or 0),
                            expected_candle_count=None,
                            coverage_percent=None,
                            missing_windows=[],
                            selected_data_source="persisted_strategy_validation_candles",
                            replay_ready=available,
                            reason_codes=("historical_candles_available",)
                            if available
                            else ("historical_candles_missing",),
                        )
                    )
    except Exception as exc:  # pragma: no cover - exercised by integration environment.
        reason = f"historical_db_unreachable:{exc.__class__.__name__}"
        rows = [
            HistoricalReplayDatasetAudit(
                symbol=symbol,
                timeframe=timeframe,
                available=False,
                start_time=None,
                end_time=None,
                candle_count=0,
                expected_candle_count=None,
                coverage_percent=None,
                missing_windows=[],
                selected_data_source="persisted_strategy_validation_candles",
                replay_ready=False,
                reason_codes=("historical_db_unreachable", reason),
            )
            for symbol in symbols
            for timeframe in timeframes
        ]
    return rows


def _dataset_from_result(result: dict[str, Any]) -> dict[str, Any]:
    request = result.get("request") or {}
    coverage = result.get("data_coverage") or {}
    symbol = request.get("symbol") or result.get("symbol") or "unknown"
    timeframe = result.get("timeframe") or request.get("component_keys", ["unknown"])[0].replace("sleeve_", "")
    warning_codes = list(coverage.get("warning_reason_codes") or [])
    actual = int(coverage.get("actual_candle_count") or len(result.get("contexts") or []))
    expected = int(coverage.get("expected_candle_count") or actual)
    coverage_percent = str(coverage.get("coverage_percent") or ("1.00000000" if actual else "0"))
    ready = actual > 0 and (not expected or actual >= expected) and not warning_codes
    reason_codes = ["historical_candles_available" if actual else "historical_candles_missing"]
    if expected and actual < expected:
        reason_codes.append("historical_candle_coverage_insufficient")
    reason_codes.extend(warning_codes)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "available": actual > 0,
        "start_time": coverage.get("first_candle_available_at"),
        "end_time": coverage.get("last_candle_available_at"),
        "requested_start_time": coverage.get("requested_start_at") or request.get("start_at"),
        "requested_end_time": coverage.get("requested_end_at") or request.get("end_at"),
        "candle_count": actual,
        "expected_candle_count": expected,
        "coverage_percent": coverage_percent,
        "missing_windows": [] if not warning_codes else warning_codes,
        "selected_data_source": PT002_SOURCE_KIND,
        "source_label": "SV1.17 historical true replay export from Hyperliquid public historical candles",
        "replay_ready": ready,
        "reason_codes": reason_codes,
    }


def _context_time(context: dict[str, Any]) -> str | None:
    return context.get("candle_close_time") or context.get("timestamp_utc")


def _candle_from_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "time": _context_time(context),
        "timestamp_utc": _context_time(context),
        "open_time": context.get("candle_open_time"),
        "open": str(context.get("open")),
        "high": str(context.get("high")),
        "low": str(context.get("low")),
        "close": str(context.get("close")),
        "volume": str(context.get("volume") or "0"),
        "volume_status": "unavailable_from_replay_context"
        if context.get("volume") is None
        else "available",
    }


def _indicator_from_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "time": _context_time(context),
        "timestamp_utc": _context_time(context),
        "EMA5": context.get("ema5"),
        "EMA10": context.get("ema10"),
        "SMA20": context.get("sma20"),
        "RSI": context.get("rsi14"),
        "MACD": context.get("macd"),
        "MACD_signal": context.get("macd_signal"),
        "MACD_histogram": context.get("macd_histogram"),
        "regime": context.get("market_regime_label"),
        "volatility": context.get("volatility_regime_label"),
    }


def _context_by_time(contexts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(_context_time(context)): context for context in contexts if _context_time(context)}


def _trade_indicator_snapshot(trade: dict[str, Any], contexts_by_time: dict[str, dict[str, Any]], prefix: str) -> dict[str, Any]:
    timestamp = trade.get(f"{prefix}_signal_time") or trade.get(f"{prefix}_time")
    context = contexts_by_time.get(str(timestamp)) or {}
    return {
        "time": timestamp,
        "RSI": context.get("rsi14"),
        "EMA5": context.get("ema5"),
        "EMA10": context.get("ema10"),
        "SMA20": context.get("sma20"),
        "MACD": context.get("macd"),
        "MACD_signal": context.get("macd_signal"),
        "MACD_histogram": context.get("macd_histogram"),
        "market_regime": context.get("market_regime_label") or trade.get(f"{prefix}_market_regime"),
        "volatility_regime": context.get("volatility_regime_label") or trade.get(f"{prefix}_volatility_regime"),
    }


def _drawdown_after(equity_after: Any, max_equity_before: Decimal) -> str:
    try:
        equity = Decimal(str(equity_after))
    except (InvalidOperation, TypeError, ValueError):
        equity = Decimal(PT002_INITIAL_EQUITY)
    peak = max(max_equity_before, equity)
    return _money(peak - equity)


def _normalized_trade(
    trade: dict[str, Any],
    contexts_by_time: dict[str, dict[str, Any]],
    max_equity_before: Decimal,
) -> dict[str, Any]:
    equity_before = _money(trade.get("equity_before_entry"))
    equity_after = _money(trade.get("equity_after_exit"))
    return {
        "trade_id": trade.get("trade_id"),
        "symbol": trade.get("symbol"),
        "timeframe": trade.get("timeframe"),
        "component": trade.get("component_key"),
        "side": trade.get("side"),
        "entry_signal_time": trade.get("entry_signal_time"),
        "entry_fill_time": trade.get("entry_time"),
        "entry_time": trade.get("entry_time"),
        "entry_price": trade.get("entry_price"),
        "entry_reason_codes": [trade.get("entry_reason") or "baseline_entry_allowed"],
        "entry_indicators": _trade_indicator_snapshot(trade, contexts_by_time, "entry"),
        "exit_signal_time": trade.get("exit_signal_time"),
        "exit_fill_time": trade.get("exit_time"),
        "exit_time": trade.get("exit_time"),
        "exit_price": trade.get("exit_price"),
        "exit_reason_codes": [trade.get("exit_reason") or "forced_end_of_window_exit"],
        "exit_indicators": _trade_indicator_snapshot(trade, contexts_by_time, "exit"),
        "fill_assumption": trade.get("fill_timing") or PT002_DEFAULT_FILL_ASSUMPTION,
        "fee_bps": "5",
        "slippage_bps": "3",
        "fees": trade.get("fees"),
        "slippage_cost": trade.get("slippage_cost"),
        "gross_pnl": trade.get("gross_pnl"),
        "net_pnl": trade.get("net_pnl"),
        "equity_before_trade": equity_before,
        "equity_after_trade": equity_after,
        "drawdown_after_trade": _drawdown_after(equity_after, max_equity_before),
        "notional_used": trade.get("entry_notional"),
        "position_size": trade.get("size"),
        "forced_exit": bool(trade.get("forced_exit")),
        "market_regime": trade.get("entry_market_regime"),
        "source": "historical_replay",
        "labels": {
            "historical_paper_replay": True,
            "not_live": True,
            "not_testnet_order": True,
            "not_real_capital": True,
        },
    }


def _trade_markers(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for trade in trades:
        trade_id = trade.get("trade_id")
        markers.append(
            {
                "time": trade.get("entry_fill_time"),
                "price": trade.get("entry_price"),
                "marker_type": "entry_fill",
                "color_role": "green",
                "trade_id": trade_id,
                "reason_codes": trade.get("entry_reason_codes") or [],
                "source": "historical_replay",
                "label": "historical replay entry fill",
                "fill_assumption": trade.get("fill_assumption"),
                "equity_before": trade.get("equity_before_trade"),
                "equity_after": trade.get("equity_after_trade"),
                "pnl": trade.get("net_pnl"),
            }
        )
        exit_reasons = trade.get("exit_reason_codes") or []
        is_trim = any("trim" in str(reason) or "reduce" in str(reason) for reason in exit_reasons)
        markers.append(
            {
                "time": trade.get("exit_fill_time"),
                "price": trade.get("exit_price"),
                "marker_type": "trim" if is_trim else "exit_fill",
                "color_role": "yellow" if is_trim else "red",
                "trade_id": trade_id,
                "reason_codes": exit_reasons,
                "source": "historical_replay",
                "label": "historical replay trim/reduce" if is_trim else "historical replay exit fill",
                "fill_assumption": trade.get("fill_assumption"),
                "equity_before": trade.get("equity_before_trade"),
                "equity_after": trade.get("equity_after_trade"),
                "pnl": trade.get("net_pnl"),
            }
        )
    return [marker for marker in markers if marker.get("time") and marker.get("price")]


def _equity_curve(trades: list[dict[str, Any]], first_candle_time: str | None) -> list[dict[str, Any]]:
    curve = [
        {
            "time": first_candle_time,
            "equity": PT002_INITIAL_EQUITY,
            "realized_pnl": "0.00000000",
            "unrealized_pnl": "0.00000000",
            "source": "historical_replay_initial_equity",
        }
    ]
    for trade in trades:
        curve.append(
            {
                "time": trade.get("exit_fill_time"),
                "equity": trade.get("equity_after_trade"),
                "realized_pnl": _money(Decimal(str(trade.get("equity_after_trade"))) - Decimal(PT002_INITIAL_EQUITY)),
                "unrealized_pnl": "0.00000000",
                "trade_id": trade.get("trade_id"),
                "source": "historical_replay_closed_trade_equity",
            }
        )
    return curve


def _reason_counts(result: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = result.get("metrics") or {}
    entry = Counter(reason for trade in trades for reason in trade.get("entry_reason_codes", []))
    exit_ = Counter(reason for trade in trades for reason in trade.get("exit_reason_codes", []))
    return {
        "entry_reason_counts": dict(entry),
        "exit_reason_counts": dict(exit_),
        "no_trade_reason_counts": metrics.get("no_trade_reason_counts") or {},
        "invalid_reason_counts": metrics.get("invalid_reason_counts") or {},
    }


def _summary_from_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "starting_equity": metrics.get("starting_equity") or PT002_INITIAL_EQUITY,
        "ending_equity": metrics.get("ending_equity"),
        "net_pnl": metrics.get("net_pnl") or metrics.get("net_account_pnl"),
        "realized_pnl": metrics.get("net_pnl") or metrics.get("net_account_pnl"),
        "unrealized_pnl": "0.00000000",
        "max_equity": metrics.get("maximum_realized_equity"),
        "min_equity": metrics.get("minimum_realized_equity"),
        "max_drawdown": metrics.get("max_drawdown") or metrics.get("closed_trade_max_drawdown"),
        "max_drawdown_pct": metrics.get("max_drawdown_pct") or metrics.get("closed_trade_max_drawdown_pct"),
        "trade_count": metrics.get("number_of_trades"),
        "win_rate": metrics.get("win_rate"),
        "profit_factor": metrics.get("profit_factor"),
        "best_trade": metrics.get("best_trade_net_pnl"),
        "worst_trade": metrics.get("worst_trade_net_pnl"),
        "total_fees": metrics.get("total_fees"),
        "total_slippage_cost": metrics.get("total_slippage_cost"),
    }


def _replay_from_result(result: dict[str, Any]) -> dict[str, Any]:
    contexts = list(result.get("contexts") or [])
    contexts_by_time = _context_by_time(contexts)
    raw_trades = list(result.get("trades") or [])
    max_equity = Decimal(PT002_INITIAL_EQUITY)
    trades: list[dict[str, Any]] = []
    for trade in raw_trades:
        normalized = _normalized_trade(trade, contexts_by_time, max_equity)
        try:
            max_equity = max(max_equity, Decimal(str(normalized["equity_after_trade"])))
        except (InvalidOperation, TypeError, ValueError):
            pass
        trades.append(normalized)
    candles = [_candle_from_context(context) for context in contexts]
    return {
        "symbol": (result.get("request") or {}).get("symbol"),
        "timeframe": result.get("timeframe"),
        "component": ((result.get("request") or {}).get("component_keys") or ["unknown"])[0],
        "candles": candles,
        "indicators": [_indicator_from_context(context) for context in contexts],
        "markers": _trade_markers(trades),
        "trades": trades,
        "equity_curve": _equity_curve(trades, candles[0]["time"] if candles else None),
        "summary": _summary_from_metrics(result.get("metrics") or {}),
        "reason_counts": _reason_counts(result, trades),
        "data_source": PT002_SOURCE_KIND,
        "strategy_truth_lane": "historical_strategy_truth",
        "testnet_prices_used_as_strategy_truth": False,
    }


def _comparison_from_replay(replay: dict[str, Any]) -> dict[str, Any]:
    trades = replay.get("trades") or []
    summary = replay.get("summary") or {}
    exit_reasons = Counter(
        reason for trade in trades for reason in (trade.get("exit_reason_codes") or [])
    ).most_common(3)
    entry_reasons = Counter(
        reason for trade in trades for reason in (trade.get("entry_reason_codes") or [])
    ).most_common(3)
    return {
        "symbol": replay.get("symbol"),
        "timeframe": replay.get("timeframe"),
        "status": "replay_ready" if replay.get("candles") else "data_missing",
        "ending_equity": summary.get("ending_equity"),
        "net_pnl": summary.get("net_pnl"),
        "trade_count": summary.get("trade_count"),
        "win_rate": summary.get("win_rate"),
        "max_drawdown": summary.get("max_drawdown"),
        "best_trade": summary.get("best_trade"),
        "worst_trade": summary.get("worst_trade"),
        "primary_entry_reasons": [reason for reason, _count in entry_reasons],
        "primary_exit_reasons": [reason for reason, _count in exit_reasons],
    }


def build_pt002_historical_replay_summary_from_sv117_payload(
    payload: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    source_path: Path | None = None,
    db_audit_rows: list[HistoricalReplayDatasetAudit] | None = None,
) -> dict[str, Any]:
    """Build PT0.0.2 cockpit JSON from the existing SV1.17 baseline replay export."""

    baseline_results = [
        result
        for result in payload.get("baseline_results", [])
        if (result.get("request") or {}).get("symbol") in PT002_SYMBOLS
        and result.get("timeframe") in PT002_TIMEFRAMES
    ]
    result_lookup = {
        ((result.get("request") or {}).get("symbol"), result.get("timeframe")): result
        for result in baseline_results
    }
    datasets = []
    replays = []
    for symbol in PT002_SYMBOLS:
        for timeframe in PT002_TIMEFRAMES:
            result = result_lookup.get((symbol, timeframe))
            if not result:
                datasets.append(
                    {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "available": False,
                        "start_time": None,
                        "end_time": None,
                        "candle_count": 0,
                        "expected_candle_count": None,
                        "coverage_percent": "0",
                        "missing_windows": [],
                        "selected_data_source": PT002_SOURCE_KIND,
                        "replay_ready": False,
                        "reason_codes": ["historical_candles_missing"],
                    }
                )
                continue
            datasets.append(_dataset_from_result(result))
            replays.append(_replay_from_result(result))

    comparison = [_comparison_from_replay(replay) for replay in replays]
    selected = next(
        (replay for replay in replays if replay.get("symbol") == "ETH" and replay.get("timeframe") == "1h"),
        replays[0] if replays else None,
    )
    return {
        "report": PT002_REPORT_NAME,
        "run_id": f"{PT002_REPORT_NAME}_{(generated_at_utc or _utc_now()).replace(':', '').replace('-', '')}",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "source": {
            "strategy_truth_lane": "historical_strategy_truth",
            "source_kind": PT002_SOURCE_KIND,
            "source_label": "SV1.17 full-suite baseline replay export built from Hyperliquid public historical candles",
            "source_path": str(source_path) if source_path else None,
            "source_sha256": _source_hash(source_path),
            "testnet_prices_used_as_strategy_truth": False,
            "private_or_signed_endpoints_used": False,
            "order_endpoints_used": False,
            "hyperliquid_testnet_role": "sandbox_execution_plumbing_only",
        },
        "lanes": {
            "lane_a_historical_strategy_truth": "historical/mainnet/public candle replay",
            "lane_b_paper_runtime_truth": "internal 10000 USDC dynamic paper-equity simulation",
            "lane_c_sandbox_execution_plumbing": "Hyperliquid testnet/sandbox submit/cancel/reconcile plumbing only",
        },
        "symbols": list(PT002_SYMBOLS),
        "timeframes": list(PT002_TIMEFRAMES),
        "window_convention": PT002_WINDOW_CONVENTION,
        "initial_equity": PT002_INITIAL_EQUITY,
        "capital_sizing_mode": "dynamic_equity_pct",
        "sizing_policy": {
            "sizing_basis": "realized_equity",
            "risk_display_basis": "realized_plus_unrealized",
            "does_not_reset_each_trade_to_static_10000": True,
        },
        "fill_assumptions": [
            {"id": "next_candle_open", "default": True, "research_only": False},
            {"id": "next_candle_close", "default": False, "research_only": False},
            {"id": "same_candle_close_research_only", "default": False, "research_only": True},
        ],
        "selected_fill_assumption": PT002_DEFAULT_FILL_ASSUMPTION,
        "cost_assumptions": {"fee_bps": "5", "slippage_bps": "3"},
        "datasets": datasets,
        "db_audit": [
            historical_replay_dataset_audit_to_dict(row)
            for row in (db_audit_rows or [])
        ],
        "replays": replays,
        "selected_replay": {
            "symbol": selected.get("symbol") if selected else None,
            "timeframe": selected.get("timeframe") if selected else None,
        },
        "comparison": comparison,
        "sandbox_execution_ledger_separate": True,
        "dashboard": {
            "historical_replay_tab": "implemented",
            "trade_inspector": "implemented",
            "equity_curve_panel": "implemented",
            "comparison_panel": "implemented",
        },
        "boundary_flags": {
            "uses_historical_candles_only_for_replay": True,
            "testnet_prices_used_as_strategy_truth": False,
            "submits_orders": False,
            "calls_order_endpoints": False,
            "calls_private_or_signed_endpoints": False,
            "uses_api_keys": False,
            "changes_money_flow_rules": False,
            "live_trading_approved": False,
        },
        "roadmap": {
            "pt0_0_3": "Historical Replay Playback Controls + Market Structure Inspector",
            "pt0_1": "Supervised Paper Runtime Using Trusted Market Data",
        },
    }
