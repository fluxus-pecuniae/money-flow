"""Historical Money Flow replay export helpers for PT0 historical cockpit phases."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import func

from db.models import CandleModel
from db.session import SessionLocal


PT002_REPORT_NAME = "pt0_0_2_historical_strategy_replay_cockpit"
PT003_REPORT_NAME = "pt0_0_3_historical_data_horizon_and_1d_replay"
PT003_TARGET_START_AT = "2025-01-01T00:00:00Z"
PT002_SYMBOLS = ("BTC", "ETH", "SOL")
PT002_TIMEFRAMES = ("15m", "1h", "4h")
PT003_TIMEFRAMES = ("15m", "1h", "4h", "1D")
PT002_INITIAL_EQUITY = "10000"
PT002_FILL_ASSUMPTIONS = (
    "next_candle_open",
    "next_candle_close",
    "same_candle_close_research_only",
)
PT002_DEFAULT_FILL_ASSUMPTION = "next_candle_open"
PT002_SOURCE_KIND = "trusted_offline_historical_candles"
PT002_WINDOW_CONVENTION = "(start_at, end_at]"
PT003_DAILY_TIMEFRAME = "1D"
PT003_DAILY_SOURCE_TIMEFRAME = "4h"
PT002_BASELINE_STRATEGY_ID = "baseline_current_money_flow_rules"
PT002_NO_MACD_STRATEGY_ID = "macd_removed_research_only"
PT002_STRATEGIES = (
    {
        "id": PT002_BASELINE_STRATEGY_ID,
        "label": "OG replay / strategy",
        "description": "Current Money Flow rules with MACD entry confirmation and MACD-rollover exits.",
        "research_only": False,
        "changes_production_rules": False,
    },
    {
        "id": PT002_NO_MACD_STRATEGY_ID,
        "label": "MACD removed",
        "description": (
            "Research-only historical replay with MACD entry confirmation and MACD-rollover "
            "exit checks removed. Other Money Flow checks remain unchanged."
        ),
        "research_only": True,
        "changes_production_rules": False,
    },
)
_SLEEVE_PARAMS = {
    "sleeve_15m": {"overbought_rsi": Decimal("72"), "trim_rsi": Decimal("78"), "max_extension": Decimal("0.018")},
    "sleeve_1h": {"overbought_rsi": Decimal("74"), "trim_rsi": Decimal("80"), "max_extension": Decimal("0.02")},
    "sleeve_4h": {"overbought_rsi": Decimal("76"), "trim_rsi": Decimal("82"), "max_extension": Decimal("0.025")},
}
_TIMEFRAME_SECONDS = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1D": 24 * 60 * 60,
}


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


def _decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _quantity(value: Any) -> str:
    decimal = _decimal(value, Decimal("0")) or Decimal("0")
    return str(decimal.quantize(Decimal("0.000000000001")))


def _ratio(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator == 0:
        return None
    return _money(numerator / denominator)


def _source_hash(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _target_start() -> datetime:
    parsed = _parse_utc_timestamp(PT003_TARGET_START_AT)
    assert parsed is not None
    return parsed


def _expected_candle_count_from_target(end_time: str | None, timeframe: str) -> int | None:
    end = _parse_utc_timestamp(end_time)
    seconds = _TIMEFRAME_SECONDS.get(timeframe)
    if end is None or seconds is None:
        return None
    delta_seconds = int((end - _target_start()).total_seconds())
    if delta_seconds <= 0:
        return 0
    return delta_seconds // seconds


def _coverage_from_target(candle_count: int, end_time: str | None, timeframe: str) -> str | None:
    expected = _expected_candle_count_from_target(end_time, timeframe)
    if expected is None or expected <= 0:
        return None
    return _money(Decimal(candle_count) / Decimal(expected))


def _daily_bucket_close_time(value: str | None) -> datetime | None:
    timestamp = _parse_utc_timestamp(value)
    if timestamp is None:
        return None
    day_start = datetime(timestamp.year, timestamp.month, timestamp.day, tzinfo=UTC)
    if timestamp == day_start:
        return day_start
    return day_start + timedelta(days=1)


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


def _strategy_metadata(strategy_id: str) -> dict[str, Any]:
    return next(
        (dict(row) for row in PT002_STRATEGIES if row["id"] == strategy_id),
        dict(PT002_STRATEGIES[0]),
    )


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
        "strategy_id": PT002_BASELINE_STRATEGY_ID,
        "strategy_label": _strategy_metadata(PT002_BASELINE_STRATEGY_ID)["label"],
        "strategy_description": _strategy_metadata(PT002_BASELINE_STRATEGY_ID)["description"],
        "research_only": False,
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


def _context_decimal(context: dict[str, Any], key: str) -> Decimal | None:
    return _decimal(context.get(key))


def _no_macd_entry_rejection(context: dict[str, Any]) -> str | None:
    if context.get("baseline_status") == "invalid":
        return str((context.get("baseline_reason_codes") or ["invalid"])[0])
    component = str(context.get("component_key") or "")
    params = _SLEEVE_PARAMS.get(component, _SLEEVE_PARAMS["sleeve_1h"])
    close = _context_decimal(context, "close")
    ema5 = _context_decimal(context, "ema5")
    ema10 = _context_decimal(context, "ema10")
    sma20 = _context_decimal(context, "sma20")
    rsi = _context_decimal(context, "rsi14")
    floor = _context_decimal(context, "rsi_sleeve_floor")
    ceiling = _context_decimal(context, "rsi_sleeve_ceiling")
    if None in (close, ema5, ema10, sma20, rsi, floor, ceiling):
        return "insufficient_history"
    assert close is not None and ema5 is not None and ema10 is not None and sma20 is not None
    assert rsi is not None and floor is not None and ceiling is not None
    if not (ema5 > ema10 > sma20):
        return "bearish_alignment"
    if rsi >= params["overbought_rsi"]:
        return "overextended_rsi"
    if not (floor <= rsi <= ceiling):
        return "rsi_not_constructive"
    max_extension = params["max_extension"]
    pullback_ok = close >= ema10 and close <= ema5 * (Decimal("1") + max_extension)
    continuation_ok = close > ema5 and close <= ema5 * (Decimal("1") + max_extension)
    if not (pullback_ok or continuation_ok):
        return "entry_quality_not_constructive"
    extension = ((close / ema5) - Decimal("1")) if ema5 else Decimal("0")
    if extension > max_extension:
        return "price_too_extended"
    return None


def _no_macd_exit_reason(context: dict[str, Any]) -> str | None:
    component = str(context.get("component_key") or "")
    params = _SLEEVE_PARAMS.get(component, _SLEEVE_PARAMS["sleeve_1h"])
    close = _context_decimal(context, "close")
    ema5 = _context_decimal(context, "ema5")
    ema10 = _context_decimal(context, "ema10")
    sma20 = _context_decimal(context, "sma20")
    rsi = _context_decimal(context, "rsi14")
    if None in (close, ema5, ema10, sma20, rsi):
        return None
    assert close is not None and ema5 is not None and ema10 is not None and sma20 is not None and rsi is not None
    if ema5 <= ema10 or ema10 <= sma20 or close < ema10:
        return "ma_alignment_break"
    if close < sma20 or ema5 <= ema10:
        return "trend_invalidated"
    if rsi >= params["trim_rsi"]:
        return "trim_on_overbought_rsi"
    return None


def _fill_context(contexts: list[dict[str, Any]], signal_index: int, fill_assumption: str) -> tuple[dict[str, Any], str, str] | None:
    if fill_assumption == "same_candle_close_research_only":
        context = contexts[signal_index]
        return context, str(context.get("close")), str(_context_time(context))
    next_index = signal_index + 1
    if next_index >= len(contexts):
        return None
    context = contexts[next_index]
    if fill_assumption == "next_candle_close":
        return context, str(context.get("close")), str(_context_time(context))
    return context, str(context.get("open")), str(context.get("candle_open_time") or _context_time(context))


def _simulated_no_macd_trade(
    *,
    result: dict[str, Any],
    entry_context: dict[str, Any],
    entry_fill: tuple[dict[str, Any], str, str],
    exit_context: dict[str, Any],
    exit_fill: tuple[dict[str, Any], str, str],
    entry_reason: str,
    exit_reason: str,
    equity_before: Decimal,
    forced_exit: bool,
) -> dict[str, Any]:
    symbol = (result.get("request") or {}).get("symbol")
    timeframe = result.get("timeframe")
    component = ((result.get("request") or {}).get("component_keys") or ["unknown"])[0]
    fee_rate = Decimal("5") / Decimal("10000")
    slippage_rate = Decimal("3") / Decimal("10000")
    raw_entry = _decimal(entry_fill[1], Decimal("0")) or Decimal("0")
    raw_exit = _decimal(exit_fill[1], Decimal("0")) or Decimal("0")
    entry_price = raw_entry * (Decimal("1") + slippage_rate)
    exit_price = raw_exit * (Decimal("1") - slippage_rate)
    notional = equity_before
    size = (notional / entry_price) if entry_price else Decimal("0")
    entry_fee = notional * fee_rate
    exit_notional = exit_price * size
    exit_fee = exit_notional * fee_rate
    entry_slippage = (entry_price - raw_entry) * size
    exit_slippage = (raw_exit - exit_price) * size
    gross_pnl = (raw_exit - raw_entry) * size
    fees = entry_fee + exit_fee
    slippage = entry_slippage + exit_slippage
    net_pnl = gross_pnl - fees - slippage
    equity_after = equity_before + net_pnl
    payload = "|".join(
        [
            PT002_NO_MACD_STRATEGY_ID,
            str(symbol),
            str(timeframe),
            str(entry_fill[2]),
            str(exit_fill[2]),
            entry_reason,
            exit_reason,
        ]
    )
    trade = {
        "trade_id": f"svt-{sha256(payload.encode('utf-8')).hexdigest()[:24]}",
        "symbol": symbol,
        "timeframe": timeframe,
        "component": component,
        "side": "buy",
        "entry_signal_time": _context_time(entry_context),
        "entry_fill_time": entry_fill[2],
        "entry_time": entry_fill[2],
        "entry_price": _money(entry_price),
        "entry_reason_codes": [entry_reason],
        "entry_indicators": _trade_indicator_snapshot(
            {"entry_signal_time": _context_time(entry_context)},
            _context_by_time([entry_context]),
            "entry",
        ),
        "exit_signal_time": _context_time(exit_context),
        "exit_fill_time": exit_fill[2],
        "exit_time": exit_fill[2],
        "exit_price": _money(exit_price),
        "exit_reason_codes": [exit_reason],
        "exit_indicators": _trade_indicator_snapshot(
            {"exit_signal_time": _context_time(exit_context)},
            _context_by_time([exit_context]),
            "exit",
        ),
        "fill_assumption": PT002_DEFAULT_FILL_ASSUMPTION,
        "fee_bps": "5",
        "slippage_bps": "3",
        "fees": _money(fees),
        "slippage_cost": _money(slippage),
        "gross_pnl": _money(gross_pnl),
        "net_pnl": _money(net_pnl),
        "equity_before_trade": _money(equity_before),
        "equity_after_trade": _money(equity_after),
        "drawdown_after_trade": "0.00000000",
        "notional_used": _money(notional),
        "position_size": _quantity(size),
        "forced_exit": forced_exit,
        "market_regime": entry_context.get("market_regime_label"),
        "source": "historical_replay",
        "strategy_id": PT002_NO_MACD_STRATEGY_ID,
        "labels": {
            "historical_paper_replay": True,
            "not_live": True,
            "not_testnet_order": True,
            "not_real_capital": True,
            "research_variant": PT002_NO_MACD_STRATEGY_ID,
        },
    }
    return trade


def _summary_from_trades(trades: list[dict[str, Any]], no_trade: Counter[str], invalid: Counter[str]) -> dict[str, Any]:
    equities = [Decimal(PT002_INITIAL_EQUITY)]
    pnl_values: list[Decimal] = []
    fees = Decimal("0")
    slippage = Decimal("0")
    for trade in trades:
        equities.append(_decimal(trade.get("equity_after_trade"), Decimal(PT002_INITIAL_EQUITY)) or Decimal(PT002_INITIAL_EQUITY))
        pnl_values.append(_decimal(trade.get("net_pnl"), Decimal("0")) or Decimal("0"))
        fees += _decimal(trade.get("fees"), Decimal("0")) or Decimal("0")
        slippage += _decimal(trade.get("slippage_cost"), Decimal("0")) or Decimal("0")
    ending = equities[-1]
    wins = [value for value in pnl_values if value > 0]
    losses = [value for value in pnl_values if value < 0]
    peak = equities[0]
    max_drawdown = Decimal("0")
    for equity in equities:
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    gross_wins = sum(wins, Decimal("0"))
    gross_losses = abs(sum(losses, Decimal("0")))
    return {
        "starting_equity": PT002_INITIAL_EQUITY,
        "ending_equity": _money(ending),
        "net_pnl": _money(ending - Decimal(PT002_INITIAL_EQUITY)),
        "realized_pnl": _money(ending - Decimal(PT002_INITIAL_EQUITY)),
        "unrealized_pnl": "0.00000000",
        "max_equity": _money(max(equities)),
        "min_equity": _money(min(equities)),
        "max_drawdown": _money(max_drawdown),
        "max_drawdown_pct": _ratio(max_drawdown, max(equities)) or "0.00000000",
        "trade_count": len(trades),
        "win_rate": _ratio(Decimal(len(wins)), Decimal(len(trades))) if trades else "0.00000000",
        "profit_factor": _ratio(gross_wins, gross_losses) if gross_losses else None,
        "best_trade": _money(max(pnl_values, default=Decimal("0"))),
        "worst_trade": _money(min(pnl_values, default=Decimal("0"))),
        "total_fees": _money(fees),
        "total_slippage_cost": _money(slippage),
        "no_trade_reason_counts": dict(sorted(no_trade.items())),
        "invalid_reason_counts": dict(sorted(invalid.items())),
    }


def _no_macd_replay_from_result(result: dict[str, Any]) -> dict[str, Any]:
    contexts = list(result.get("contexts") or [])
    trades: list[dict[str, Any]] = []
    no_trade: Counter[str] = Counter()
    invalid: Counter[str] = Counter()
    equity = Decimal(PT002_INITIAL_EQUITY)
    open_entry: tuple[dict[str, Any], tuple[dict[str, Any], str, str], str, Decimal] | None = None
    for index, context in enumerate(contexts):
        if open_entry is not None:
            exit_reason = _no_macd_exit_reason(context)
            if exit_reason is None:
                continue
            exit_fill = _fill_context(contexts, index, PT002_DEFAULT_FILL_ASSUMPTION)
            if exit_fill is None:
                continue
            trade = _simulated_no_macd_trade(
                result=result,
                entry_context=open_entry[0],
                entry_fill=open_entry[1],
                exit_context=context,
                exit_fill=exit_fill,
                entry_reason=open_entry[2],
                exit_reason=exit_reason,
                equity_before=open_entry[3],
                forced_exit=False,
            )
            trades.append(trade)
            equity = _decimal(trade.get("equity_after_trade"), equity) or equity
            open_entry = None
            continue

        reason = _no_macd_entry_rejection(context)
        if reason in {"insufficient_history", "invalid"}:
            invalid[reason] += 1
            continue
        if reason is not None:
            no_trade[reason] += 1
            continue
        fill = _fill_context(contexts, index, PT002_DEFAULT_FILL_ASSUMPTION)
        if fill is None:
            no_trade["open_signal_skipped_no_fill_candle_for_next_candle_open"] += 1
            continue
        entry_reason = (
            "macd_removed_entry_allowed"
            if "macd_not_constructive" in (context.get("baseline_reason_codes") or [])
            or context.get("entry_rejection_reason") == "macd_not_constructive"
            else "baseline_entry_allowed"
        )
        open_entry = (context, fill, entry_reason, equity)

    if open_entry is not None and contexts:
        last_context = contexts[-1]
        force_fill = (last_context, str(last_context.get("close")), str(_context_time(last_context)))
        trade = _simulated_no_macd_trade(
            result=result,
            entry_context=open_entry[0],
            entry_fill=open_entry[1],
            exit_context=last_context,
            exit_fill=force_fill,
            entry_reason=open_entry[2],
            exit_reason="end_of_window_forced_close",
            equity_before=open_entry[3],
            forced_exit=True,
        )
        trades.append(trade)

    max_equity = Decimal(PT002_INITIAL_EQUITY)
    for trade in trades:
        trade["drawdown_after_trade"] = _drawdown_after(trade.get("equity_after_trade"), max_equity)
        max_equity = max(max_equity, _decimal(trade.get("equity_after_trade"), max_equity) or max_equity)

    candles = [_candle_from_context(context) for context in contexts]
    summary = _summary_from_trades(trades, no_trade, invalid)
    return {
        "strategy_id": PT002_NO_MACD_STRATEGY_ID,
        "strategy_label": _strategy_metadata(PT002_NO_MACD_STRATEGY_ID)["label"],
        "strategy_description": _strategy_metadata(PT002_NO_MACD_STRATEGY_ID)["description"],
        "research_only": True,
        "symbol": (result.get("request") or {}).get("symbol"),
        "timeframe": result.get("timeframe"),
        "component": ((result.get("request") or {}).get("component_keys") or ["unknown"])[0],
        "candles": candles,
        "indicators": [_indicator_from_context(context) for context in contexts],
        "markers": _trade_markers(trades),
        "trades": trades,
        "equity_curve": _equity_curve(trades, candles[0]["time"] if candles else None),
        "summary": summary,
        "reason_counts": {
            "entry_reason_counts": dict(
                Counter(reason for trade in trades for reason in trade.get("entry_reason_codes", []))
            ),
            "exit_reason_counts": dict(
                Counter(reason for trade in trades for reason in trade.get("exit_reason_codes", []))
            ),
            "no_trade_reason_counts": summary["no_trade_reason_counts"],
            "invalid_reason_counts": summary["invalid_reason_counts"],
        },
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
        "strategy_id": replay.get("strategy_id") or PT002_BASELINE_STRATEGY_ID,
        "strategy_label": replay.get("strategy_label") or "OG replay / strategy",
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


def _format_indicator(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:.12f}".rstrip("0").rstrip(".")


def _ema_values(values: list[float], period: int) -> list[float | None]:
    alpha = 2 / (period + 1)
    ema: float | None = None
    rows: list[float | None] = []
    for index, value in enumerate(values):
        ema = value if ema is None else (value * alpha) + (ema * (1 - alpha))
        rows.append(ema if index >= period - 1 else None)
    return rows


def _sma_values(values: list[float], period: int) -> list[float | None]:
    rows: list[float | None] = []
    for index, _value in enumerate(values):
        if index < period - 1:
            rows.append(None)
            continue
        window = values[index - period + 1 : index + 1]
        rows.append(sum(window) / period)
    return rows


def _rsi_values(values: list[float], period: int = 14) -> list[float | None]:
    rows: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return rows
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, period + 1):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rows[period] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
    for index in range(period + 1, len(values)):
        change = values[index] - values[index - 1]
        gain = max(change, 0)
        loss = abs(min(change, 0))
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        rows[index] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
    return rows


def _daily_indicator_rows(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closes = [float(_decimal(candle.get("close"), Decimal("0")) or Decimal("0")) for candle in candles]
    ema5 = _ema_values(closes, 5)
    ema10 = _ema_values(closes, 10)
    sma20 = _sma_values(closes, 20)
    rsi = _rsi_values(closes)
    ema12 = _ema_values(closes, 12)
    ema26 = _ema_values(closes, 26)
    macd: list[float | None] = [
        (fast - slow) if fast is not None and slow is not None else None
        for fast, slow in zip(ema12, ema26, strict=False)
    ]
    signal_rows: list[float | None] = []
    signal: float | None = None
    macd_seen = 0
    alpha = 2 / (9 + 1)
    for value in macd:
        if value is None:
            signal_rows.append(None)
            continue
        signal = value if signal is None else (value * alpha) + (signal * (1 - alpha))
        macd_seen += 1
        signal_rows.append(signal if macd_seen >= 9 else None)
    histogram: list[float | None] = [
        (value - signal_value) if value is not None and signal_value is not None else None
        for value, signal_value in zip(macd, signal_rows, strict=False)
    ]
    rows: list[dict[str, Any]] = []
    for index, candle in enumerate(candles):
        rows.append(
            {
                "time": candle.get("time"),
                "timestamp_utc": candle.get("timestamp_utc"),
                "EMA5": _format_indicator(ema5[index]),
                "EMA10": _format_indicator(ema10[index]),
                "SMA20": _format_indicator(sma20[index]),
                "RSI": _format_indicator(rsi[index]),
                "MACD": _format_indicator(macd[index]),
                "MACD_signal": _format_indicator(signal_rows[index]),
                "MACD_histogram": _format_indicator(histogram[index]),
                "regime": "daily_aggregated_replay",
                "volatility": "daily_aggregated_replay",
            }
        )
    return rows


def _aggregate_daily_candles(source_candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    sorted_candles = sorted(
        source_candles,
        key=lambda candle: _parse_utc_timestamp(candle.get("timestamp_utc") or candle.get("time")) or datetime.min.replace(tzinfo=UTC),
    )
    for candle in sorted_candles:
        close_time = _daily_bucket_close_time(candle.get("timestamp_utc") or candle.get("time"))
        if close_time is None:
            continue
        key = _iso_utc(close_time)
        if key is None:
            continue
        high = _decimal(candle.get("high"), Decimal("0")) or Decimal("0")
        low = _decimal(candle.get("low"), Decimal("0")) or Decimal("0")
        close = _decimal(candle.get("close"), Decimal("0")) or Decimal("0")
        volume = _decimal(candle.get("volume"), Decimal("0")) or Decimal("0")
        if key not in grouped:
            grouped[key] = {
                "time": key,
                "timestamp_utc": key,
                "open_time": _iso_utc(close_time - timedelta(days=1)),
                "open": str(candle.get("open")),
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "volume_status": candle.get("volume_status") or "available",
                "aggregation_used": True,
                "aggregation_source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
                "aggregation_source_candle_count": 1,
            }
            continue
        row = grouped[key]
        row["high"] = max(row["high"], high)
        row["low"] = min(row["low"], low)
        row["close"] = close
        row["volume"] = row["volume"] + volume
        row["aggregation_source_candle_count"] += 1
    daily = []
    for row in grouped.values():
        daily.append(
            {
                **row,
                "high": _money(row["high"]),
                "low": _money(row["low"]),
                "close": _money(row["close"]),
                "volume": _money(row["volume"]),
            }
        )
    return sorted(daily, key=lambda candle: candle["timestamp_utc"])


def _map_time_to_daily_close(value: str | None) -> str | None:
    return _iso_utc(_daily_bucket_close_time(value))


def _daily_trade_from_source(trade: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(trade)
    source_trade_id = str(row.get("trade_id") or "unknown")
    row["trade_id"] = f"{source_trade_id}-1d"
    row["timeframe"] = PT003_DAILY_TIMEFRAME
    row["source_timeframe"] = PT003_DAILY_SOURCE_TIMEFRAME
    row["aggregation_used"] = True
    row["aggregation_source_timeframe"] = PT003_DAILY_SOURCE_TIMEFRAME
    row["aggregation_note"] = "1D replay chart is aggregated from existing 4h historical replay candles/trades; no 1D Money Flow sleeve was created."
    labels = dict(row.get("labels") or {})
    labels.update(
        {
            "historical_aggregation_used": True,
            "aggregation_source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
            "not_new_strategy_rule": True,
        }
    )
    row["labels"] = labels
    return row


def _daily_markers_from_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers = _trade_markers(trades)
    for marker in markers:
        original_time = marker.get("time")
        marker["original_time"] = original_time
        marker["time"] = _map_time_to_daily_close(original_time)
        marker["aggregation_used"] = True
        marker["aggregation_source_timeframe"] = PT003_DAILY_SOURCE_TIMEFRAME
    return [marker for marker in markers if marker.get("time")]


def _daily_equity_curve_from_source(curve: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for point in curve:
        row = deepcopy(point)
        row["original_time"] = row.get("time")
        row["time"] = _map_time_to_daily_close(row.get("time"))
        row["aggregation_used"] = True
        row["aggregation_source_timeframe"] = PT003_DAILY_SOURCE_TIMEFRAME
        if row.get("time"):
            rows.append(row)
    return rows


def _daily_replay_from_source(source_replay: dict[str, Any]) -> dict[str, Any]:
    candles = _aggregate_daily_candles(list(source_replay.get("candles") or []))
    trades = [_daily_trade_from_source(trade) for trade in source_replay.get("trades") or []]
    replay = deepcopy(source_replay)
    replay.update(
        {
            "timeframe": PT003_DAILY_TIMEFRAME,
            "source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
            "component": source_replay.get("component"),
            "candles": candles,
            "indicators": _daily_indicator_rows(candles),
            "markers": _daily_markers_from_trades(trades),
            "trades": trades,
            "equity_curve": _daily_equity_curve_from_source(source_replay.get("equity_curve") or []),
            "data_source": "deterministic_aggregation_from_historical_replay_candles",
            "aggregation_used": True,
            "aggregation_source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
            "aggregation_note": "1D candles are aggregated from existing 4h historical replay candles using UTC day boundaries; existing 4h replay trades are overlaid for horizon review without creating a 1D Money Flow sleeve.",
            "daily_aggregation": {
                "status": "implemented",
                "source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
                "utc_day_boundaries": True,
                "creates_new_money_flow_sleeve": False,
                "reason_codes": [
                    "historical_aggregation_used",
                    "not_a_new_1d_money_flow_sleeve",
                ],
            },
            "dynamic_equity_summary": {
                "initial_equity": str(source_replay.get("summary", {}).get("initial_equity") or "10000"),
                "ending_equity": str(source_replay.get("summary", {}).get("ending_equity") or ""),
                "uses_dynamic_equity": True,
                "does_not_reset_each_trade_to_static_10000": True,
            },
            "data_warnings": [
                "historical_aggregation_used",
                "not_a_new_1d_money_flow_sleeve",
                "historical_target_start_not_available",
                "historical_earliest_available_after_target",
            ],
        }
    )
    return replay


def _enrich_dataset_for_pt003(row: dict[str, Any]) -> dict[str, Any]:
    enriched = deepcopy(row)
    timeframe = str(enriched.get("timeframe") or "")
    start_time = enriched.get("start_time")
    end_time = enriched.get("end_time")
    start = _parse_utc_timestamp(start_time)
    target_met = bool(start and start <= _target_start())
    reason_codes = list(enriched.get("reason_codes") or [])
    if target_met:
        reason_codes.append("historical_target_start_available")
    else:
        reason_codes.extend(["historical_target_start_not_available", "historical_earliest_available_after_target"])
    enriched.update(
        {
            "target_start_at": PT003_TARGET_START_AT,
            "actual_earliest_available": start_time,
            "actual_latest_available": end_time,
            "target_start_met": target_met,
            "expected_candle_count_from_target": _expected_candle_count_from_target(end_time, timeframe),
            "target_coverage_percent": _coverage_from_target(int(enriched.get("candle_count") or 0), end_time, timeframe),
            "aggregation_used": bool(enriched.get("aggregation_used", False)),
            "source_kind": enriched.get("selected_data_source") or enriched.get("source_kind") or PT002_SOURCE_KIND,
            "reason_codes": sorted(set(reason_codes)),
        }
    )
    return enriched


def _daily_dataset_from_replay(replay: dict[str, Any]) -> dict[str, Any]:
    candles = list(replay.get("candles") or [])
    source_count = sum(int(candle.get("aggregation_source_candle_count") or 0) for candle in candles)
    start_time = candles[0].get("timestamp_utc") if candles else None
    end_time = candles[-1].get("timestamp_utc") if candles else None
    reason_codes = [
        "historical_candles_available" if candles else "historical_candles_missing",
        "historical_aggregation_used",
        "historical_target_start_not_available",
        "historical_earliest_available_after_target",
        "not_a_new_1d_money_flow_sleeve",
    ]
    if not candles:
        reason_codes.append("historical_aggregation_not_possible")
    return {
        "symbol": replay.get("symbol"),
        "timeframe": PT003_DAILY_TIMEFRAME,
        "available": bool(candles),
        "start_time": start_time,
        "end_time": end_time,
        "actual_earliest_available": start_time,
        "actual_latest_available": end_time,
        "target_start_at": PT003_TARGET_START_AT,
        "target_start_met": False,
        "candle_count": len(candles),
        "expected_candle_count": len(candles),
        "expected_candle_count_from_target": _expected_candle_count_from_target(end_time, PT003_DAILY_TIMEFRAME),
        "coverage_percent": "1.00000000" if candles else "0",
        "target_coverage_percent": _coverage_from_target(len(candles), end_time, PT003_DAILY_TIMEFRAME),
        "missing_windows": [],
        "selected_data_source": "deterministic_aggregation_from_historical_replay_candles",
        "source_kind": "deterministic_aggregation_from_historical_replay_candles",
        "source_label": "1D UTC candles aggregated from trusted 4h historical replay candles",
        "source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
        "aggregation_used": True,
        "aggregation_source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
        "aggregation_source_candle_count": source_count,
        "aggregation_convention": "UTC day OHLCV from complete/in-range source candles",
        "creates_new_money_flow_sleeve": False,
        "replay_ready": bool(candles),
        "reason_codes": sorted(set(reason_codes)),
    }


def _actual_data_horizon_rows(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": row.get("symbol"),
            "timeframe": row.get("timeframe"),
            "target_start_at": row.get("target_start_at"),
            "actual_earliest_available": row.get("actual_earliest_available") or row.get("start_time"),
            "actual_latest_available": row.get("actual_latest_available") or row.get("end_time"),
            "target_start_met": bool(row.get("target_start_met")),
            "replay_ready": bool(row.get("replay_ready")),
            "aggregation_used": bool(row.get("aggregation_used")),
            "source_kind": row.get("source_kind") or row.get("selected_data_source"),
            "target_coverage_percent": row.get("target_coverage_percent"),
            "reason_codes": list(row.get("reason_codes") or []),
        }
        for row in datasets
    ]


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
            replays.append(_no_macd_replay_from_result(result))

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
        "strategies": list(PT002_STRATEGIES),
        "selected_strategy_id": PT002_BASELINE_STRATEGY_ID,
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
            "strategy_id": selected.get("strategy_id") if selected else None,
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


def build_pt003_historical_replay_summary_from_pt002_summary(
    pt002_summary: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    source_path: Path | None = None,
    db_audit_rows: list[HistoricalReplayDatasetAudit] | None = None,
) -> dict[str, Any]:
    """Build PT0.0.3 horizon/readiness JSON without changing Money Flow rules.

    The project does not currently define a production `sleeve_1d` Money Flow
    component. PT0.0.3 therefore adds 1D chart/replay support by aggregating the
    trusted 4h historical replay candles to UTC daily bars and overlaying the
    existing 4h replay trades. The export labels that truth explicitly so the
    daily view is not mistaken for a new strategy rule.
    """

    generated = generated_at_utc or _utc_now()
    source_replays = [deepcopy(row) for row in pt002_summary.get("replays") or []]
    source_lookup = {
        (
            row.get("strategy_id") or PT002_BASELINE_STRATEGY_ID,
            row.get("symbol"),
            row.get("timeframe"),
        ): row
        for row in source_replays
    }
    base_datasets = [
        _enrich_dataset_for_pt003(row)
        for row in (pt002_summary.get("datasets") or [])
        if row.get("symbol") in PT002_SYMBOLS and row.get("timeframe") in PT002_TIMEFRAMES
    ]
    dataset_lookup = {
        (row.get("symbol"), row.get("timeframe")): row
        for row in base_datasets
    }
    datasets: list[dict[str, Any]] = []
    replays: list[dict[str, Any]] = []
    for symbol in PT002_SYMBOLS:
        for timeframe in PT002_TIMEFRAMES:
            datasets.append(
                dataset_lookup.get(
                    (symbol, timeframe),
                    _enrich_dataset_for_pt003(
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
                            "reason_codes": [
                                "historical_candles_missing",
                                "historical_data_source_missing",
                            ],
                        }
                    ),
                )
            )
            for strategy_id in (PT002_BASELINE_STRATEGY_ID, PT002_NO_MACD_STRATEGY_ID):
                replay = source_lookup.get((strategy_id, symbol, timeframe))
                if replay:
                    replay = deepcopy(replay)
                    replay.setdefault("data_warnings", [])
                    replays.append(replay)

        first_daily_replay: dict[str, Any] | None = None
        for strategy_id in (PT002_BASELINE_STRATEGY_ID, PT002_NO_MACD_STRATEGY_ID):
            source_replay = source_lookup.get((strategy_id, symbol, PT003_DAILY_SOURCE_TIMEFRAME))
            if not source_replay:
                continue
            daily_replay = _daily_replay_from_source(source_replay)
            if first_daily_replay is None:
                first_daily_replay = daily_replay
            replays.append(daily_replay)
        datasets.append(
            _daily_dataset_from_replay(first_daily_replay or {"symbol": symbol, "candles": []})
        )

    comparison = [_comparison_from_replay(replay) for replay in replays]
    selected = next(
        (
            replay
            for replay in replays
            if replay.get("strategy_id") == PT002_BASELINE_STRATEGY_ID
            and replay.get("symbol") == "ETH"
            and replay.get("timeframe") == "1h"
        ),
        replays[0] if replays else None,
    )
    source = deepcopy(pt002_summary.get("source") or {})
    source.update(
        {
            "strategy_truth_lane": "historical_strategy_truth",
            "source_kind": source.get("source_kind") or PT002_SOURCE_KIND,
            "source_label": source.get("source_label")
            or "PT0.0.2 trusted historical replay summary plus deterministic 1D aggregation",
            "base_replay_summary_path": str(source_path) if source_path else None,
            "base_replay_summary_sha256": _source_hash(source_path),
            "testnet_prices_used_as_strategy_truth": False,
            "private_or_signed_endpoints_used": False,
            "order_endpoints_used": False,
            "daily_aggregation_source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
            "daily_aggregation_uses_utc_boundaries": True,
        }
    )
    return {
        "report": PT003_REPORT_NAME,
        "run_id": f"{PT003_REPORT_NAME}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "target_start_at": PT003_TARGET_START_AT,
        "source": source,
        "lanes": pt002_summary.get("lanes")
        or {
            "lane_a_historical_strategy_truth": "historical/mainnet/public candle replay",
            "lane_b_paper_runtime_truth": "internal 10000 USDC dynamic paper-equity simulation",
            "lane_c_sandbox_execution_plumbing": "Hyperliquid testnet/sandbox submit/cancel/reconcile plumbing only",
        },
        "symbols": list(PT002_SYMBOLS),
        "timeframes": list(PT003_TIMEFRAMES),
        "window_convention": PT002_WINDOW_CONVENTION,
        "daily_aggregation": {
            "status": "implemented",
            "timeframe": PT003_DAILY_TIMEFRAME,
            "source_timeframe": PT003_DAILY_SOURCE_TIMEFRAME,
            "convention": "UTC day boundaries with (start_at, end_at] daily close semantics",
            "creates_new_money_flow_sleeve": False,
            "reason_codes": ["historical_aggregation_used", "not_a_new_1d_money_flow_sleeve"],
        },
        "initial_equity": PT002_INITIAL_EQUITY,
        "capital_sizing_mode": "dynamic_equity_pct",
        "strategies": list(PT002_STRATEGIES),
        "selected_strategy_id": PT002_BASELINE_STRATEGY_ID,
        "sizing_policy": pt002_summary.get("sizing_policy")
        or {
            "sizing_basis": "realized_equity",
            "risk_display_basis": "realized_plus_unrealized",
            "does_not_reset_each_trade_to_static_10000": True,
        },
        "fill_assumptions": pt002_summary.get("fill_assumptions")
        or [
            {"id": "next_candle_open", "default": True, "research_only": False},
            {"id": "next_candle_close", "default": False, "research_only": False},
            {"id": "same_candle_close_research_only", "default": False, "research_only": True},
        ],
        "selected_fill_assumption": pt002_summary.get("selected_fill_assumption") or PT002_DEFAULT_FILL_ASSUMPTION,
        "cost_assumptions": pt002_summary.get("cost_assumptions") or {"fee_bps": "5", "slippage_bps": "3"},
        "datasets": datasets,
        "data_readiness": datasets,
        "actual_data_horizon": _actual_data_horizon_rows(datasets),
        "db_audit": [
            historical_replay_dataset_audit_to_dict(row)
            for row in (db_audit_rows or [])
        ],
        "replays": replays,
        "selected_replay": {
            "strategy_id": selected.get("strategy_id") if selected else None,
            "symbol": selected.get("symbol") if selected else None,
            "timeframe": selected.get("timeframe") if selected else None,
        },
        "comparison": comparison,
        "sandbox_execution_ledger_separate": True,
        "dashboard": {
            "historical_replay_tab": "implemented",
            "timeframe_1d_selector": "implemented",
            "data_horizon_panel": "implemented",
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
            "creates_1d_money_flow_sleeve": False,
            "live_trading_approved": False,
        },
        "roadmap": {
            "pt0_0_4": "Historical Replay Playback Controls + Market Structure Inspector",
            "pt0_1": "Supervised Paper Runtime Using Trusted Market Data",
        },
    }
