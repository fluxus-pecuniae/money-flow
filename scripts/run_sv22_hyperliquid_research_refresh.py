#!/usr/bin/env python3
"""Run SV2.2 Hyperliquid public-mainnet research refresh.

This is research/dashboard preparation only. It fetches public Hyperliquid
mainnet metadata and candleSnapshot rows, writes compact data-inventory and
selected Historical Replay chart payloads, and never calls private, signed,
testnet, or order endpoints.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
import urllib.request
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PHASE = "SV2.2"
REPORT_NAME = "sv2_2_hyperliquid_research_refresh"
SOURCE_LABEL = "hyperliquid_public_mainnet_candleSnapshot"
HYPERLIQUID_MAINNET_PUBLIC_INFO_URL = "https://api.hyperliquid.xyz/info"
DEFAULT_WORK_DIR = Path("/tmp/money-flow-sv22-research-refresh")
DEFAULT_SUMMARY_OUTPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/sv2_2_hyperliquid_research_refresh.md")
DEFAULT_CHART_ROOT = Path("reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data")
DEFAULT_PACK_ROOT = Path("reports/strategy_validation")
ACTIVE_TIMEFRAMES = ("1h", "4h", "1d")
DISABLED_TIMEFRAMES = ("15m",)
WEEK2_REPLAY_STRATEGY_IDS = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)
FILL_ASSUMPTIONS = ("next_candle_open", "next_candle_close")
INITIAL_EQUITY = Decimal("10000")
FEE_BPS = Decimal("5")
SLIPPAGE_BPS = Decimal("3")
HYPERLIQUID_INTERVAL_BY_TIMEFRAME = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}
TIMEFRAME_SECONDS = {
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
}
PUBLIC_CANDLE_LIMIT = 5000
FOUNDER_APPROVED_REQUESTED_SYMBOLS = (
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "DOGE",
    "HYPE",
    "BNB",
    "SUI",
    "AVAX",
    "TRON",
    "ADA",
    "ZEC",
    "LINK",
    "XMR",
    "TON",
    "LTC",
    "UNI",
    "DOT",
    "ASTER",
    "AAVE",
    "POL",
    "FIL",
    "TRUMP",
    "PEPE",
    "OKB",
)
FOUNDER_APPROVED_SYMBOL_ALIASES = {
    "TRON": "TRX",
    "PEPE": "kPEPE",
}
FOUNDER_APPROVED_EXCLUDED_SYMBOLS = {
    "PEPE": "pepe_kpepe_unit_semantics_deferred",
    "OKB": "okb_support_not_confirmed_or_public_mid_unavailable",
}
FOUNDER_APPROVED_RESOLVED_SYMBOLS = tuple(
    dict.fromkeys(
        FOUNDER_APPROVED_SYMBOL_ALIASES.get(symbol, symbol).upper()
        for symbol in FOUNDER_APPROVED_REQUESTED_SYMBOLS
        if symbol not in FOUNDER_APPROVED_EXCLUDED_SYMBOLS
    )
)
NO_ORDER_FLAGS = {
    "submits_orders": False,
    "calls_order_endpoints": False,
    "calls_private_or_signed_endpoints": False,
    "uses_api_keys": False,
    "uses_testnet_prices_as_strategy_truth": False,
    "uses_testnet_fills_as_pnl_truth": False,
    "enables_live_trading": False,
    "changes_production_money_flow_rules": False,
    "approves_production_strategy": False,
}


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-explicit: {value}")
    return parsed.astimezone(UTC)


FALLBACK_START_AT = parse_utc("2024-01-01T00:00:00Z")


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def unix_ms(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp() * 1000)


def hyperliquid_meta_payload() -> dict[str, Any]:
    return {"type": "meta"}


def hyperliquid_candle_snapshot_payload(
    *,
    coin: str,
    timeframe: str,
    start_at: datetime,
    end_at: datetime,
) -> dict[str, Any]:
    if timeframe not in HYPERLIQUID_INTERVAL_BY_TIMEFRAME:
        raise ValueError(f"unsupported_sv22_timeframe:{timeframe}")
    return {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": HYPERLIQUID_INTERVAL_BY_TIMEFRAME[timeframe],
            "startTime": unix_ms(start_at),
            "endTime": unix_ms(end_at),
        },
    }


def fetch_hyperliquid_public_info(
    payload: dict[str, Any],
    *,
    url: str = HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    timeout_seconds: float = 20.0,
) -> Any:
    if url != HYPERLIQUID_MAINNET_PUBLIC_INFO_URL:
        raise ValueError("sv22_requires_hyperliquid_mainnet_public_info_endpoint")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def decimal_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value}") from exc


def parse_millis(value: Any) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def normalize_hyperliquid_candle_snapshot(
    payload: Any,
    *,
    requested_symbol: str,
    resolved_venue_symbol: str,
    timeframe: str,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(payload, list):
        raise ValueError("hyperliquid_candleSnapshot_payload_not_list")
    seconds = TIMEFRAME_SECONDS[timeframe]
    rows: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError("hyperliquid_candleSnapshot_row_not_object")
        open_time = parse_millis(row.get("t"))
        raw_close_time = parse_millis(row["T"]) if row.get("T") is not None else open_time + timedelta(seconds=seconds)
        close_time = open_time + timedelta(seconds=seconds)
        open_price = decimal_value(row.get("o"))
        high = decimal_value(row.get("h"))
        low = decimal_value(row.get("l"))
        close = decimal_value(row.get("c"))
        volume = decimal_value(row.get("v") or "0")
        if min(open_price, high, low, close) <= 0:
            raise ValueError("historical_refresh_blocked_invalid_ohlc")
        if high < max(open_price, close) or low > min(open_price, close):
            raise ValueError("historical_refresh_blocked_high_low_inconsistent")
        rows.append(
            {
                "symbol": requested_symbol,
                "venue_symbol": resolved_venue_symbol,
                "timeframe": timeframe,
                "display_timeframe": "1D" if timeframe == "1d" else timeframe,
                "open_time": iso_utc(open_time),
                "close_time": iso_utc(close_time),
                "raw_venue_close_time": iso_utc(raw_close_time),
                "open": str(open_price),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": str(volume),
                "trade_count": int(row["n"]) if row.get("n") is not None else None,
                "source": SOURCE_LABEL,
            }
        )
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class SV22Identity:
    requested_symbol: str
    resolved_venue_symbol: str
    canonical_symbol: str
    asset_id: int
    sz_decimals: int
    max_leverage: int | None
    only_isolated: bool
    raw_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SV22Dataset:
    symbol: str
    venue_symbol: str
    timeframe: str
    rows: int
    earliest_close: str | None
    latest_close: str | None
    raw_path: str | None
    chart_data_path: str | None
    status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SV22ReplayResult:
    strategy_id: str
    strategy_label: str
    symbol: str
    timeframe: str
    fill_assumption: str
    period: str
    status: str
    starting_equity: str
    ending_equity: str
    net_pnl: str
    max_drawdown: str
    max_drawdown_pct: str
    trade_count: int
    win_rate: str | None
    profit_factor: str | None
    largest_win: str
    largest_loss: str
    evidence_pack_path: str
    chart_data_path: str
    reason_counts: dict[str, int]
    reason_codes: tuple[str, ...]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--chart-root", type=Path, default=DEFAULT_CHART_ROOT)
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--fetch-public-data", action="store_true")
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--timeframe", action="append", choices=ACTIVE_TIMEFRAMES, default=[])
    parser.add_argument("--end-at", default=None)
    parser.add_argument("--run-timestamp", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def latest_closed_timeframe(value: datetime, timeframe: str) -> datetime:
    value = value.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    if timeframe == "1h":
        return value
    if timeframe == "4h":
        return value.replace(hour=(value.hour // 4) * 4)
    if timeframe == "1d":
        return value.replace(hour=0)
    raise ValueError(f"unsupported_sv22_timeframe:{timeframe}")


def timeframe_delta(timeframe: str) -> timedelta:
    if timeframe == "1h":
        return timedelta(hours=1)
    if timeframe == "4h":
        return timedelta(hours=4)
    if timeframe == "1d":
        return timedelta(days=1)
    raise ValueError(f"unsupported_sv22_timeframe:{timeframe}")


def default_start_at(end_at: datetime, timeframe: str) -> datetime:
    if timeframe == "1d":
        return FALLBACK_START_AT
    return max(FALLBACK_START_AT, end_at - timeframe_delta(timeframe) * PUBLIC_CANDLE_LIMIT)


def safe_segment(value: Any) -> str:
    return (
        str(value or "unknown")
        .strip()
        .lower()
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_compact_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")


def active_hyperliquid_identities_from_meta(meta: Any) -> list[SV22Identity]:
    universe = meta.get("universe", []) if isinstance(meta, dict) else []
    identities: list[SV22Identity] = []
    for asset_id, row in enumerate(universe):
        if not isinstance(row, dict):
            continue
        venue_symbol = str(row.get("name") or "")
        sz_decimals = row.get("szDecimals")
        if not venue_symbol or sz_decimals is None or bool(row.get("isDelisted") or row.get("delisted")):
            continue
        canonical = venue_symbol.upper()
        identities.append(
            SV22Identity(
                requested_symbol=canonical,
                resolved_venue_symbol=venue_symbol,
                canonical_symbol=canonical,
                asset_id=asset_id,
                sz_decimals=int(sz_decimals),
                max_leverage=int(row["maxLeverage"]) if row.get("maxLeverage") is not None else None,
                only_isolated=bool(row.get("onlyIsolated", False)),
                raw_metadata=row,
            )
        )
    return identities


def filter_founder_approved_identities(identities: Sequence[SV22Identity]) -> list[SV22Identity]:
    allowed = set(FOUNDER_APPROVED_RESOLVED_SYMBOLS)
    return [identity for identity in identities if identity.canonical_symbol.upper() in allowed]


def dec_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sma(values: list[float | None], period: int) -> list[float | None]:
    rows: list[float | None] = []
    for index in range(len(values)):
        window = values[max(0, index - period + 1) : index + 1]
        if len(window) < period or any(value is None for value in window):
            rows.append(None)
        else:
            rows.append(sum(value for value in window if value is not None) / period)
    return rows


def rolling_range_pct(candles: list[dict[str, Any]], period: int) -> list[float | None]:
    rows: list[float | None] = []
    for index, candle in enumerate(candles):
        window = candles[max(0, index - period + 1): index + 1]
        if len(window) < period:
            rows.append(None)
            continue
        high = max(float(row["high"]) for row in window)
        low = min(float(row["low"]) for row in window)
        close = float(candle["close"])
        rows.append(None if close <= 0 else (high - low) / close)
    return rows


def ema(values: list[float | None], period: int) -> list[float | None]:
    rows: list[float | None] = []
    multiplier = 2 / (period + 1)
    previous: float | None = None
    for value in values:
        if value is None:
            rows.append(previous)
            continue
        previous = value if previous is None else (value - previous) * multiplier + previous
        rows.append(previous)
    return rows


def rsi(values: list[float | None], period: int = 14) -> list[float | None]:
    rows: list[float | None] = [None]
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(values)):
        if values[index] is None or values[index - 1] is None:
            rows.append(None)
            continue
        change = values[index] - values[index - 1]  # type: ignore[operator]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
        if len(gains) < period:
            rows.append(None)
            continue
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            rows.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rows.append(100 - (100 / (1 + rs)))
    return rows


def normalize_candles(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "timestamp_utc": row["close_time"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row.get("volume", "0"),
        }
        for row in candles
    ]


def indicators(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closes = [dec_or_none(row.get("close")) for row in candles]
    ema5 = ema(closes, 5)
    ema10 = ema(closes, 10)
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    rsi14 = rsi(closes, 14)
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd = [
        None if fast is None or slow is None else fast - slow
        for fast, slow in zip(ema12, ema26, strict=True)
    ]
    signal = ema(macd, 9)
    range20 = rolling_range_pct(candles, 20)
    return [
        {
            "timestamp_utc": candle["close_time"],
            "EMA5": ema5[index],
            "EMA10": ema10[index],
            "SMA20": sma20[index],
            "SMA50": sma50[index],
            "SMA200": sma200[index],
            "RSI": rsi14[index],
            "MACD": macd[index],
            "MACD_signal": signal[index],
            "MACD_histogram": None if macd[index] is None or signal[index] is None else macd[index] - signal[index],
            "rolling_range_20": range20[index],
        }
        for index, candle in enumerate(candles)
    ]


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


def fmt_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(money(value), "f")


def dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return Decimal("0") if denominator == 0 else money(numerator / denominator)


def timeframe_settings(timeframe: str) -> dict[str, float | int | bool]:
    if timeframe == "1h":
        return {
            "min_history_bars": 35,
            "rsi_floor": 50.0,
            "rsi_ceiling": 68.0,
            "overbought_rsi": 74.0,
            "trim_rsi": 80.0,
            "max_extension_pct_above_ema5": 0.02,
            "require_macd_confirmation": True,
            "allow_pullback_entries": True,
            "allow_continuation_entries": True,
            "close_on_ma_break": True,
            "close_on_macd_rollover": True,
        }
    if timeframe == "4h":
        return {
            "min_history_bars": 40,
            "rsi_floor": 48.0,
            "rsi_ceiling": 70.0,
            "overbought_rsi": 76.0,
            "trim_rsi": 82.0,
            "max_extension_pct_above_ema5": 0.025,
            "require_macd_confirmation": True,
            "allow_pullback_entries": True,
            "allow_continuation_entries": True,
            "close_on_ma_break": True,
            "close_on_macd_rollover": True,
        }
    return {
        "min_history_bars": 50,
        "rsi_floor": 46.0,
        "rsi_ceiling": 72.0,
        "overbought_rsi": 78.0,
        "trim_rsi": 84.0,
        "max_extension_pct_above_ema5": 0.03,
        "require_macd_confirmation": True,
        "allow_pullback_entries": True,
        "allow_continuation_entries": True,
        "close_on_ma_break": True,
        "close_on_macd_rollover": True,
    }


def fill_candle(candles: list[dict[str, Any]], signal_index: int, fill_assumption: str) -> dict[str, Any] | None:
    if signal_index + 1 >= len(candles):
        return None
    return candles[signal_index + 1]


def fill_price(candle: dict[str, Any], fill_assumption: str, side: str) -> Decimal:
    raw = dec(candle["open"] if fill_assumption == "next_candle_open" else candle["close"])
    adjustment = Decimal("1") + (SLIPPAGE_BPS / Decimal("10000") if side == "buy" else -SLIPPAGE_BPS / Decimal("10000"))
    return money(raw * adjustment)


def fill_time(candle: dict[str, Any], fill_assumption: str) -> str:
    return str(candle["open_time"] if fill_assumption == "next_candle_open" else candle["close_time"])


def missing_indicator_reasons(row: dict[str, Any]) -> list[str]:
    required = (
        ("EMA5", "missing_ema5"),
        ("EMA10", "missing_ema10"),
        ("SMA20", "missing_sma20"),
        ("RSI", "missing_rsi"),
        ("MACD", "missing_macd"),
        ("MACD_signal", "missing_macd_signal"),
        ("MACD_histogram", "missing_macd_histogram"),
    )
    return [reason for field, reason in required if row.get(field) is None]


def baseline_entry_reason(indicator: dict[str, Any], candle: dict[str, Any], timeframe: str) -> str | None:
    missing = missing_indicator_reasons(indicator)
    if missing:
        return "missing_indicator_field"
    settings = timeframe_settings(timeframe)
    close = float(candle["close"])
    ema5 = float(indicator["EMA5"])
    ema10 = float(indicator["EMA10"])
    sma20 = float(indicator["SMA20"])
    rsi_value = float(indicator["RSI"])
    macd = float(indicator["MACD"])
    macd_signal = float(indicator["MACD_signal"])
    macd_histogram = float(indicator["MACD_histogram"])
    if not (ema5 > ema10 > sma20):
        return "bearish_alignment"
    if rsi_value >= float(settings["overbought_rsi"]):
        return "overextended_rsi"
    if not (float(settings["rsi_floor"]) <= rsi_value <= float(settings["rsi_ceiling"])):
        return "rsi_not_constructive"
    if bool(settings["require_macd_confirmation"]) and not (macd > macd_signal and macd_histogram >= 0):
        return "macd_not_constructive"
    max_extension = float(settings["max_extension_pct_above_ema5"])
    pullback_ok = bool(settings["allow_pullback_entries"]) and close >= ema10 and close <= ema5 * (1 + max_extension)
    continuation_ok = bool(settings["allow_continuation_entries"]) and close > ema5 and close <= ema5 * (1 + max_extension)
    if not (pullback_ok or continuation_ok):
        return "entry_quality_not_constructive"
    if (close / ema5) - 1.0 > max_extension:
        return "price_too_extended"
    return None


def baseline_exit_reason(indicator: dict[str, Any], candle: dict[str, Any], timeframe: str) -> str | None:
    missing = missing_indicator_reasons(indicator)
    if missing:
        return None
    settings = timeframe_settings(timeframe)
    close = float(candle["close"])
    ema5 = float(indicator["EMA5"])
    ema10 = float(indicator["EMA10"])
    sma20 = float(indicator["SMA20"])
    macd = float(indicator["MACD"])
    macd_signal = float(indicator["MACD_signal"])
    macd_histogram = float(indicator["MACD_histogram"])
    if bool(settings["close_on_ma_break"]) and (ema5 <= ema10 or ema10 <= sma20 or close < ema10):
        return "ma_alignment_break"
    if close < sma20 or ema5 <= ema10:
        return "trend_invalidated"
    if bool(settings["close_on_macd_rollover"]) and (macd < macd_signal or macd_histogram < 0):
        return "macd_rollover"
    if float(indicator["RSI"]) >= float(settings["trim_rsi"]):
        return "trim_on_overbought_rsi"
    return None


def prior_high(candles: list[dict[str, Any]], index: int, lookback: int) -> Decimal | None:
    window = candles[max(0, index - lookback): index]
    if not window:
        return None
    return max(dec(row["high"]) for row in window)


def prior_low(candles: list[dict[str, Any]], index: int, lookback: int) -> Decimal | None:
    window = candles[max(0, index - lookback): index]
    if not window:
        return None
    return min(dec(row["low"]) for row in window)


def crossed_above(current: dict[str, Any], previous: dict[str, Any] | None, left: str, right: str) -> bool:
    if previous is None or current.get(left) is None or current.get(right) is None or previous.get(left) is None or previous.get(right) is None:
        return False
    return dec(previous[left]) <= dec(previous[right]) and dec(current[left]) > dec(current[right])


def crossed_below(current: dict[str, Any], previous: dict[str, Any] | None, left: str, right: str) -> bool:
    if previous is None or current.get(left) is None or current.get(right) is None or previous.get(left) is None or previous.get(right) is None:
        return False
    return dec(previous[left]) >= dec(previous[right]) and dec(current[left]) < dec(current[right])


def macd_bullish_or_improving(current: dict[str, Any], previous: dict[str, Any] | None) -> bool:
    if current.get("MACD") is None or current.get("MACD_signal") is None or current.get("MACD_histogram") is None:
        return False
    if dec(current["MACD"]) > dec(current["MACD_signal"]) and dec(current["MACD_histogram"]) >= 0:
        return True
    return previous is not None and previous.get("MACD_histogram") is not None and dec(current["MACD_histogram"]) > dec(previous["MACD_histogram"])


def classify_stage(candles: list[dict[str, Any]], indicator_rows: list[dict[str, Any]], index: int, prior_stage: str) -> str:
    row = indicator_rows[index]
    prev = indicator_rows[index - 1] if index > 0 else None
    if row.get("EMA5") is None or row.get("EMA10") is None or row.get("SMA20") is None or row.get("RSI") is None:
        return "stage_unknown_insufficient_history"
    close = dec(candles[index]["close"])
    if close < dec(row["SMA20"]) or crossed_below(row, prev, "EMA5", "SMA20"):
        return "stage_4_markdown"
    if (close > dec(row["SMA20"]) and crossed_above(row, prev, "EMA5", "SMA20")) or (
        prior_stage == "stage_2_markup" and dec(row["EMA5"]) > dec(row["SMA20"]) and close > dec(row["SMA20"])
    ):
        if dec(row["RSI"]) > Decimal("72") and not macd_bullish_or_improving(row, prev):
            return "stage_3_distribution"
        return "stage_2_markup"
    if prior_stage == "stage_2_markup" and (dec(row["RSI"]) > Decimal("70") or not macd_bullish_or_improving(row, prev)):
        return "stage_3_distribution"
    return "stage_1_accumulation_sideways"


def mf_orig_entry_reason(
    candles: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
    stages: list[str],
    index: int,
) -> tuple[bool, list[str]]:
    row = indicator_rows[index]
    prev = indicator_rows[index - 1] if index > 0 else None
    missing = missing_indicator_reasons(row)
    if missing or row.get("SMA50") is None:
        return False, [*(missing or ["missing_indicator_field"]), "missing_sma50"]
    if stages[index] != "stage_2_markup":
        return False, ["blocked_not_stage_2_markup"]
    if dec(row["RSI"]) >= Decimal("80"):
        return False, ["blocked_rsi_extreme_overbought"]
    resistance = prior_high(candles, index, 20)
    if (
        resistance is not None
        and dec(candles[index]["close"]) > resistance
        and dec(candles[index]["close"]) > dec(row["SMA20"])
        and dec(row["EMA5"]) >= dec(row["SMA20"])
        and macd_bullish_or_improving(row, prev)
    ):
        return True, ["stage2_resistance_breakout", "price_above_sma20", "ema5_above_sma20", "macd_confirmation_or_improving"]
    return False, ["no_stage2_resistance_breakout_entry"]


def mf_orig_exit_reason(
    candles: list[dict[str, Any]],
    indicator_rows: list[dict[str, Any]],
    index: int,
    stop_price: Decimal,
) -> str | None:
    row = indicator_rows[index]
    prev = indicator_rows[index - 1] if index > 0 else None
    if dec(candles[index]["low"]) <= stop_price:
        return "structure_stop_hit"
    if row.get("EMA5") is None or row.get("SMA20") is None:
        return None
    if crossed_below(row, prev, "EMA5", "SMA20"):
        return "ema5_cross_below_sma20_exit"
    if dec(candles[index]["close"]) < dec(row["SMA20"]):
        return "price_close_below_sma20_exit"
    return None


def strategy_label(strategy_id: str) -> str:
    return {
        "money_flow_v1_2_baseline": "Control / Baseline - Money Flow v1.2",
        "avoid_low_rolling_range_20": "Diagnostic Comparator - avoid low rolling range 20",
        "mf_orig_1d_stage2_breakout_resistance_full_equity": "MF-ORIG Source-Faithful Candidate - 1D Stage 2 breakout resistance",
    }.get(strategy_id, strategy_id)


def replay_selected_strategy(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    fill_assumption: str,
) -> dict[str, Any]:
    indicator_rows = indicators(candles)
    stages: list[str] = []
    prior_stage = "stage_unknown_insufficient_history"
    for index in range(len(candles)):
        prior_stage = classify_stage(candles, indicator_rows, index, prior_stage)
        stages.append(prior_stage)
    open_position: dict[str, Any] | None = None
    equity = INITIAL_EQUITY
    equity_curve: list[dict[str, str]] = [{"time": candles[0]["close_time"], "equity": fmt_decimal(equity) or "0"}] if candles else []
    mtm_equity_points: list[Decimal] = [equity]
    trades: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for index, candle in enumerate(candles):
        indicator = indicator_rows[index]
        if index + 1 < int(timeframe_settings(timeframe)["min_history_bars"]):
            reason_counts["insufficient_history"] += 1
            continue
        if open_position is not None:
            mtm = equity + (dec(candle["low"]) - dec(open_position["entry_price"])) * dec(open_position["quantity"])
            mtm_equity_points.append(mtm)
            if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
                exit_reason = mf_orig_exit_reason(candles, indicator_rows, index, dec(open_position["stop_price"]))
            else:
                exit_reason = baseline_exit_reason(indicator, candle, timeframe)
            if exit_reason is None:
                reason_counts["paper_hold"] += 1
                continue
            exit_candle = fill_candle(candles, index, fill_assumption)
            if exit_candle is None:
                reason_counts[f"exit_signal_skipped_no_fill_candle_for_{fill_assumption}"] += 1
                continue
            raw_exit_price = dec(open_position["stop_price"]) if exit_reason == "structure_stop_hit" else fill_price(exit_candle, fill_assumption, "sell")
            exit_price = money(raw_exit_price)
            quantity = dec(open_position["quantity"])
            gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
            exit_notional = money(exit_price * quantity)
            exit_fee = money(exit_notional * FEE_BPS / Decimal("10000"))
            net_pnl = money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
            equity_before = equity
            equity = money(equity + gross_pnl - exit_fee)
            trade = {
                "trade_id": f"sv22-{safe_segment(strategy_id)}-{safe_segment(symbol)}-{timeframe}-{safe_segment(fill_assumption)}-{len(trades) + 1}",
                "strategy_id": strategy_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "fill_timing": fill_assumption,
                "entry_signal_time": open_position["entry_signal_time"],
                "entry_fill_time": open_position["entry_time"],
                "entry_time": open_position["entry_time"],
                "exit_signal_time": candle["close_time"],
                "exit_fill_time": fill_time(exit_candle, fill_assumption) if exit_reason != "structure_stop_hit" else candle["close_time"],
                "exit_time": fill_time(exit_candle, fill_assumption) if exit_reason != "structure_stop_hit" else candle["close_time"],
                "entry_price": open_position["entry_price"],
                "exit_price": fmt_decimal(exit_price),
                "quantity": open_position["quantity"],
                "notional": open_position["notional"],
                "net_pnl": fmt_decimal(net_pnl),
                "gross_pnl": fmt_decimal(gross_pnl),
                "fees": fmt_decimal(exit_fee + dec(open_position["entry_fee"])),
                "equity_before_trade": fmt_decimal(equity_before),
                "equity_after_trade": fmt_decimal(equity),
                "entry_reason_codes": open_position["entry_reason_codes"],
                "exit_reason_codes": [exit_reason],
                "exit_reason": exit_reason,
                "forced_exit": False,
                "source": "sv2_2_latest_public_mainnet_replay",
                "historical_replay_not_live": True,
            }
            trades.append(trade)
            equity_curve.append({"time": trade["exit_fill_time"], "equity": fmt_decimal(equity) or "0"})
            mtm_equity_points.append(equity)
            reason_counts[exit_reason] += 1
            open_position = None
            continue

        if strategy_id == "mf_orig_1d_stage2_breakout_resistance_full_equity":
            entry_allowed, entry_reasons = mf_orig_entry_reason(candles, indicator_rows, stages, index)
            reason = entry_reasons[0] if not entry_allowed else None
        else:
            reason = baseline_entry_reason(indicator, candle, timeframe)
            entry_allowed = reason is None
            entry_reasons = ["baseline_entry_allowed"]
            if entry_allowed and strategy_id == "avoid_low_rolling_range_20":
                rolling_range = indicator.get("rolling_range_20")
                if rolling_range is not None and float(rolling_range) <= 0.025:
                    entry_allowed = False
                    reason = "avoid_low_rolling_range_20_blocked_baseline_entry"
                    entry_reasons = ["blocked_low_rolling_range"]
        if not entry_allowed:
            reason_counts[reason or "no_trade"] += 1
            continue
        entry_candle = fill_candle(candles, index, fill_assumption)
        if entry_candle is None:
            reason_counts[f"open_signal_skipped_no_fill_candle_for_{fill_assumption}"] += 1
            continue
        entry_price = fill_price(entry_candle, fill_assumption, "buy")
        notional = equity
        quantity = notional / entry_price if entry_price > 0 else Decimal("0")
        if quantity <= 0:
            reason_counts["invalid_entry_quantity"] += 1
            continue
        entry_fee = money(notional * FEE_BPS / Decimal("10000"))
        equity = money(equity - entry_fee)
        stop_price = prior_low(candles, index, 10) or dec(candle["low"])
        open_position = {
            "entry_signal_time": candle["close_time"],
            "entry_time": fill_time(entry_candle, fill_assumption),
            "entry_price": fmt_decimal(entry_price),
            "quantity": fmt_decimal(quantity),
            "notional": fmt_decimal(notional),
            "entry_fee": fmt_decimal(entry_fee),
            "entry_reason_codes": entry_reasons,
            "stop_price": fmt_decimal(stop_price),
        }
        reason_counts["paper_opened"] += 1
        mtm_equity_points.append(equity)

    if open_position is not None and candles:
        last = candles[-1]
        exit_price = dec(last["close"])
        quantity = dec(open_position["quantity"])
        gross_pnl = money((exit_price - dec(open_position["entry_price"])) * quantity)
        exit_notional = money(exit_price * quantity)
        exit_fee = money(exit_notional * FEE_BPS / Decimal("10000"))
        net_pnl = money(gross_pnl - exit_fee - dec(open_position["entry_fee"]))
        equity_before = equity
        equity = money(equity + gross_pnl - exit_fee)
        trades.append({
            "trade_id": f"sv22-{safe_segment(strategy_id)}-{safe_segment(symbol)}-{timeframe}-{safe_segment(fill_assumption)}-{len(trades) + 1}",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "fill_timing": fill_assumption,
            "entry_signal_time": open_position["entry_signal_time"],
            "entry_fill_time": open_position["entry_time"],
            "entry_time": open_position["entry_time"],
            "exit_signal_time": last["close_time"],
            "exit_fill_time": last["close_time"],
            "exit_time": last["close_time"],
            "entry_price": open_position["entry_price"],
            "exit_price": fmt_decimal(exit_price),
            "quantity": open_position["quantity"],
            "notional": open_position["notional"],
            "net_pnl": fmt_decimal(net_pnl),
            "gross_pnl": fmt_decimal(gross_pnl),
            "fees": fmt_decimal(exit_fee + dec(open_position["entry_fee"])),
            "equity_before_trade": fmt_decimal(equity_before),
            "equity_after_trade": fmt_decimal(equity),
            "entry_reason_codes": open_position["entry_reason_codes"],
            "exit_reason_codes": ["end_of_window_forced_close"],
            "exit_reason": "end_of_window_forced_close",
            "forced_exit": True,
            "source": "sv2_2_latest_public_mainnet_replay",
            "historical_replay_not_live": True,
        })
        equity_curve.append({"time": last["close_time"], "equity": fmt_decimal(equity) or "0"})
        mtm_equity_points.append(equity)
        reason_counts["end_of_window_forced_close"] += 1

    peak = INITIAL_EQUITY
    max_drawdown = Decimal("0")
    for point in mtm_equity_points:
        peak = max(peak, point)
        max_drawdown = max(max_drawdown, peak - point)
    wins = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) > 0]
    losses = [dec(trade["net_pnl"]) for trade in trades if dec(trade["net_pnl"]) < 0]
    gross_wins = sum(wins, Decimal("0"))
    gross_losses = abs(sum(losses, Decimal("0")))
    return {
        "strategy_id": strategy_id,
        "strategy_label": strategy_label(strategy_id),
        "strategy_description": "SV2.2 latest public-mainnet historical replay for the founder-selected Week 2 Paper Trading slate.",
        "strategy_truth_lane": "hyperliquid_public_mainnet_sv2_2_latest_replay",
        "research_only": True,
        "changes_production_rules": False,
        "production_approved": False,
        "testnet_prices_used_as_strategy_truth": False,
        "symbol": symbol,
        "timeframe": timeframe,
        "component": f"sleeve_{timeframe}",
        "period": "SV2.2",
        "fill_assumption": fill_assumption,
        "data_source": "SV2.2 latest Hyperliquid public-mainnet candles",
        "candles": normalize_candles(candles),
        "indicators": indicator_rows,
        "trades": trades,
        "markers": markers_for_replay_trades(trades),
        "equity_curve": equity_curve,
        "summary": {
            "starting_equity": fmt_decimal(INITIAL_EQUITY),
            "ending_equity": fmt_decimal(equity),
            "net_pnl": fmt_decimal(equity - INITIAL_EQUITY),
            "max_drawdown": fmt_decimal(max_drawdown),
            "max_drawdown_pct": fmt_decimal(ratio(max_drawdown, INITIAL_EQUITY)),
            "trade_count": len(trades),
            "win_rate": fmt_decimal(ratio(Decimal(len(wins)), Decimal(len(trades)))) if trades else None,
            "profit_factor": fmt_decimal(gross_wins / gross_losses) if gross_losses > 0 else None,
            "largest_win": fmt_decimal(max(wins, default=Decimal("0"))),
            "largest_loss": fmt_decimal(min(losses, default=Decimal("0"))),
        },
        "reason_counts": dict(sorted(reason_counts.items())),
        "variant_metadata": {
            "phase": PHASE,
            "methodology": "latest_public_mainnet_true_forward_replay",
            "selected_week2_paper_lane": True,
            "fill_assumption": fill_assumption,
            "fee_bps": str(FEE_BPS),
            "slippage_bps": str(SLIPPAGE_BPS),
        },
        "boundary_flags": {
            "evidence_only": True,
            "no_orders": True,
            "no_private_signed_or_order_endpoints": True,
            "testnet_prices_used_as_strategy_truth": False,
            "testnet_fills_update_pnl": False,
            "production_rule_change": False,
            "production_approved": False,
            "live_trading_approved": False,
        },
    }


def markers_for_replay_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for trade in trades:
        markers.append({
            "time": trade["entry_fill_time"],
            "trade_id": trade["trade_id"],
            "marker_type": "entry_fill",
            "color_role": "green",
            "reason_codes": trade.get("entry_reason_codes", []),
            "net_pnl": trade.get("net_pnl"),
        })
        markers.append({
            "time": trade["exit_fill_time"],
            "trade_id": trade["trade_id"],
            "marker_type": "exit_fill",
            "color_role": "yellow" if trade.get("forced_exit") else "red",
            "reason_codes": trade.get("exit_reason_codes", []),
            "net_pnl": trade.get("net_pnl"),
        })
    return markers


def replay_chart_path(chart_root: Path, run_timestamp: str, symbol: str, timeframe: str, strategy_id: str, fill_assumption: str) -> Path:
    return chart_root / run_timestamp / "selected" / (
        f"hyperliquid_public_{safe_segment(symbol)}_{timeframe}_"
        f"{safe_segment(strategy_id)}_{safe_segment(fill_assumption)}_sv22_replay.json"
    )


def replay_pack_path(pack_root: Path, run_timestamp: str, symbol: str, timeframe: str, strategy_id: str) -> Path:
    return pack_root / (
        "sv2_2_latest_public_mainnet_week2_"
        f"{safe_segment(strategy_id)}_{safe_segment(symbol)}_{timeframe}_evidence_only"
    ) / run_timestamp


def write_replay_artifacts(
    *,
    dataset: SV22Dataset,
    chart_root: Path,
    pack_root: Path,
    run_timestamp: str,
) -> list[SV22ReplayResult]:
    if dataset.status != "refreshed" or not dataset.raw_path:
        return []
    raw = json.loads(Path(dataset.raw_path).read_text(encoding="utf-8"))
    candles = raw.get("candles") or []
    if not candles:
        return []
    results: list[SV22ReplayResult] = []
    for strategy_id in WEEK2_REPLAY_STRATEGY_IDS:
        run_reports: list[dict[str, Any]] = []
        selected_paths: list[str] = []
        for fill_assumption in FILL_ASSUMPTIONS:
            replay = replay_selected_strategy(
                strategy_id=strategy_id,
                symbol=dataset.symbol,
                timeframe=dataset.timeframe,
                candles=candles,
                fill_assumption=fill_assumption,
            )
            pack_path = replay_pack_path(pack_root, run_timestamp, dataset.symbol, dataset.timeframe, strategy_id)
            chart_path = replay_chart_path(chart_root, run_timestamp, dataset.symbol, dataset.timeframe, strategy_id, fill_assumption)
            replay["evidence_pack_path"] = pack_path.as_posix()
            selected_payload = {
                "report": "sv2_2_week2_replay_dashboard_chart_data",
                "phase": PHASE,
                "generated_from": {
                    "summary": DEFAULT_SUMMARY_OUTPUT.as_posix(),
                    "raw_candles": dataset.raw_path,
                    "evidence_pack": pack_path.as_posix(),
                },
                "symbol": dataset.symbol,
                "timeframe": dataset.timeframe,
                "period": "SV2.2",
                "dataset": {
                    "symbol": dataset.symbol,
                    "venue_symbol": dataset.venue_symbol,
                    "timeframe": dataset.timeframe,
                    "rows": dataset.rows,
                    "earliest_close": dataset.earliest_close,
                    "latest_close": dataset.latest_close,
                    "source": SOURCE_LABEL,
                    "db_imported": False,
                    "canonical_evidence_ready": False,
                    "replay_ready": True,
                    "reason_codes": list(dataset.reason_codes),
                },
                "selected_replay": {
                    "strategy_id": strategy_id,
                    "fill_assumption": fill_assumption,
                    "period": "SV2.2",
                },
                "replays": [replay],
            }
            write_compact_json(chart_path, selected_payload)
            selected_paths.append(chart_path.as_posix())
            run_report = {
                "status": "completed",
                "phase": PHASE,
                "strategy_id": strategy_id,
                "symbol": dataset.symbol,
                "timeframe": dataset.timeframe,
                "period": "SV2.2",
                "fill_timing": fill_assumption,
                "run_id": f"sv22-{safe_segment(strategy_id)}-{safe_segment(dataset.symbol)}-{dataset.timeframe}-{safe_segment(fill_assumption)}",
                "request": {
                    "symbol": dataset.symbol,
                    "component_keys": [f"sleeve_{dataset.timeframe}"],
                    "assumptions": {
                        "initial_capital": str(INITIAL_EQUITY),
                        "fee_bps": str(FEE_BPS),
                        "slippage_bps": str(SLIPPAGE_BPS),
                        "position_notional_pct": "1.0",
                        "fill_timing": fill_assumption,
                    },
                },
                "report": {
                    "strategy_id": strategy_id,
                    "symbol": dataset.symbol,
                    "timeframe": dataset.timeframe,
                    "aggregate_metrics": replay["summary"],
                    "component_reports": [
                        {
                            "component_key": f"sleeve_{dataset.timeframe}",
                            "timeframe": dataset.timeframe,
                            "metrics": replay["summary"],
                            "trades": replay["trades"],
                        }
                    ],
                    "trades": replay["trades"],
                    "reason_counts": replay["reason_counts"],
                    "boundary_flags": replay["boundary_flags"],
                },
            }
            run_reports.append(run_report)
            results.append(
                SV22ReplayResult(
                    strategy_id=strategy_id,
                    strategy_label=strategy_label(strategy_id),
                    symbol=dataset.symbol,
                    timeframe=dataset.timeframe,
                    fill_assumption=fill_assumption,
                    period="SV2.2",
                    status="completed",
                    starting_equity=replay["summary"]["starting_equity"],
                    ending_equity=replay["summary"]["ending_equity"],
                    net_pnl=replay["summary"]["net_pnl"],
                    max_drawdown=replay["summary"]["max_drawdown"],
                    max_drawdown_pct=replay["summary"]["max_drawdown_pct"],
                    trade_count=int(replay["summary"]["trade_count"]),
                    win_rate=replay["summary"]["win_rate"],
                    profit_factor=replay["summary"]["profit_factor"],
                    largest_win=replay["summary"]["largest_win"],
                    largest_loss=replay["summary"]["largest_loss"],
                    evidence_pack_path=pack_path.as_posix(),
                    chart_data_path=chart_path.as_posix(),
                    reason_counts=replay["reason_counts"],
                    reason_codes=("sv2_2_latest_public_mainnet_replay_completed",),
                )
            )
        pack_path.mkdir(parents=True, exist_ok=True)
        manifest = {
            "phase": PHASE,
            "artifact": "sv2_2_latest_public_mainnet_week2_evidence_only_replay_pack",
            "run_timestamp": run_timestamp,
            "strategy_id": strategy_id,
            "symbol": dataset.symbol,
            "timeframe": dataset.timeframe,
            "period": "SV2.2",
            "fill_assumptions": list(FILL_ASSUMPTIONS),
            "source": SOURCE_LABEL,
            "evidence_only": True,
            "production_approved": False,
            "orders_submitted": False,
            "private_signed_or_order_endpoints_called": False,
            "testnet_prices_used_as_strategy_truth": False,
            "selected_chart_data_paths": selected_paths,
        }
        batch_payload = {
            "phase": PHASE,
            "manifest": manifest,
            "assumptions_matrix": {
                "symbols": [dataset.symbol],
                "components": [f"sleeve_{dataset.timeframe}"],
                "fill_timings": list(FILL_ASSUMPTIONS),
                "strategy_ids": [strategy_id],
                "periods": ["SV2.2"],
                "initial_capital_values": [str(INITIAL_EQUITY)],
                "capital_sizing_modes": ["dynamic_equity_pct"],
            },
            "run_reports": run_reports,
            "boundary_flags": {
                "evidence_only": True,
                "production_approved": False,
                "orders_submitted": False,
                "private_signed_or_order_endpoints_called": False,
                "testnet_prices_used_as_strategy_truth": False,
                "testnet_fills_update_pnl": False,
            },
        }
        write_json(pack_path / "manifest.json", manifest)
        write_json(pack_path / "batch_report.json", batch_payload)
        (pack_path / "README.md").write_text(
            "# SV2.2 Latest Public-Mainnet Week 2 Replay Pack\n\n"
            "Evidence-only latest-data historical replay for founder review. No orders were submitted, "
            "no private/signed/order endpoints were called, no strategy is production-approved, and live trading is not approved.\n",
            encoding="utf-8",
        )
    return results


def fetch_dataset(
    *,
    identity: Any,
    timeframe: str,
    effective_end: datetime,
    work_dir: Path,
    timeout_seconds: float,
) -> SV22Dataset:
    start_at = default_start_at(effective_end, timeframe)
    raw = fetch_hyperliquid_public_info(
        hyperliquid_candle_snapshot_payload(
            coin=identity.resolved_venue_symbol,
            timeframe=timeframe,
            start_at=start_at,
            end_at=effective_end + timeframe_delta(timeframe),
        ),
        url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
        timeout_seconds=timeout_seconds,
    )
    candles = [
        row
        for row in normalize_hyperliquid_candle_snapshot(
            raw,
            requested_symbol=identity.canonical_symbol,
            resolved_venue_symbol=identity.resolved_venue_symbol,
            timeframe=timeframe,
        )
        if start_at < parse_utc(str(row["close_time"])) <= effective_end
    ]
    reason_codes = ["hyperliquid_public_mainnet_fetch_succeeded"]
    if not candles:
        reason_codes.append("no_public_candles_returned")
    raw_path = work_dir / "raw_candles" / (
        f"hyperliquid_public_{safe_segment(identity.resolved_venue_symbol)}_{timeframe}_sv2_2.json"
    )
    raw_payload = {
        "source": SOURCE_LABEL,
        "phase": PHASE,
        "symbol": identity.canonical_symbol,
        "venue_symbol": identity.resolved_venue_symbol,
        "timeframe": timeframe,
        "start_at": iso_utc(start_at),
        "end_at": iso_utc(effective_end),
        "candles": candles,
        "boundaries": NO_ORDER_FLAGS,
    }
    write_compact_json(raw_path, raw_payload)
    return SV22Dataset(
        symbol=identity.canonical_symbol,
        venue_symbol=identity.resolved_venue_symbol,
        timeframe=timeframe,
        rows=len(candles),
        earliest_close=str(candles[0]["close_time"]) if candles else None,
        latest_close=str(candles[-1]["close_time"]) if candles else None,
        raw_path=raw_path.as_posix(),
        chart_data_path=None,
        status="refreshed" if candles else "no_candles",
        reason_codes=tuple(reason_codes),
    )


def missing_identity_datasets(identities: Sequence[Any], timeframes: Sequence[str]) -> list[SV22Dataset]:
    seen = {identity.canonical_symbol.upper() for identity in identities}
    rows: list[SV22Dataset] = []
    for symbol in FOUNDER_APPROVED_RESOLVED_SYMBOLS:
        if symbol in seen:
            continue
        for timeframe in timeframes:
            rows.append(
                SV22Dataset(
                    symbol=symbol,
                    venue_symbol=symbol,
                    timeframe=timeframe,
                    rows=0,
                    earliest_close=None,
                    latest_close=None,
                    raw_path=None,
                    chart_data_path=None,
                    status="missing_identity",
                    reason_codes=("founder_symbol_not_in_active_public_meta",),
                )
            )
    return rows


def build_summary(
    *,
    generated_at: datetime,
    run_timestamp: str,
    datasets: Sequence[SV22Dataset],
    fetch_public_data: bool,
    chart_root: Path,
    selected_symbols: Sequence[str],
    timeframes: Sequence[str],
    replay_results: Sequence[SV22ReplayResult] = (),
    fetch_error: str | None = None,
) -> dict[str, Any]:
    dataset_rows = [asdict(row) for row in datasets]
    replay_rows = [asdict(row) for row in replay_results]
    refreshed = [row for row in datasets if row.status == "refreshed"]
    completed_replays = [row for row in replay_results if row.status == "completed"]
    status_counts = Counter(row.status for row in datasets)
    latest_by_timeframe: dict[str, str | None] = {}
    for timeframe in timeframes:
        closes = [row.latest_close for row in refreshed if row.timeframe == timeframe and row.latest_close]
        latest_by_timeframe[timeframe] = max(closes) if closes else None
    return {
        "phase": PHASE,
        "report": REPORT_NAME,
        "generated_at_utc": iso_utc(generated_at),
        "run_timestamp": run_timestamp,
        "status": "latest_replay_complete" if completed_replays and not fetch_error else "refresh_blocked" if fetch_error else "inventory_only",
        "fetch_public_data": fetch_public_data,
        "source": {
            "venue": "hyperliquid",
            "environment": "mainnet",
            "endpoint": HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
            "public_payloads": ["meta", "candleSnapshot"],
            "strategy_truth": "public_hyperliquid_mainnet_candles",
            "testnet_strategy_truth": False,
        },
        "universe_policy": {
            "name": "founder_23_symbols",
            "requested_or_resolved_symbols": list(FOUNDER_APPROVED_RESOLVED_SYMBOLS),
            "selected_symbols": list(selected_symbols),
            "excluded_symbols": FOUNDER_APPROVED_EXCLUDED_SYMBOLS,
        },
        "timeframes": list(timeframes),
        "disabled_timeframes": list(DISABLED_TIMEFRAMES),
        "week2_replay_strategy_ids": list(WEEK2_REPLAY_STRATEGY_IDS),
        "fill_assumptions": list(FILL_ASSUMPTIONS),
        "latest_close_by_timeframe": latest_by_timeframe,
        "dataset_count": len(dataset_rows),
        "refreshed_dataset_count": len(refreshed),
        "status_counts": dict(status_counts),
        "datasets": dataset_rows,
        "replay_result_count": len(replay_rows),
        "completed_replay_count": len(completed_replays),
        "replay_results": replay_rows,
        "evidence_pack_paths": sorted({row.evidence_pack_path for row in replay_results if row.evidence_pack_path}),
        "dashboard_status": {
            "default_surface_recommendation": "Historical Replay",
            "chart_data_root": (chart_root / run_timestamp).as_posix(),
            "selected_chart_files": [row.chart_data_path for row in replay_results if row.chart_data_path],
            "chart_payload_report": "sv2_2_week2_replay_dashboard_chart_data",
            "artifact_mode": "latest_public_mainnet_week2_strategy_replay",
            "not_a_replay_strategy": True,
        },
        "boundaries": NO_ORDER_FLAGS,
        "fetch_error": fetch_error,
    }


def render_report(summary: dict[str, Any]) -> str:
    status_counts = summary.get("status_counts", {})
    latest = summary.get("latest_close_by_timeframe", {})
    replay_rows = summary.get("replay_results", [])
    top_rows = sorted(
        replay_rows,
        key=lambda row: dec(row.get("net_pnl")),
        reverse=True,
    )[:10]
    lines = [
        "# SV2.2 Hyperliquid Latest Public-Mainnet Replay Refresh",
        "",
        "## Verdict",
        "",
        f"- Status: `{summary.get('status')}`",
        "- Purpose: refresh public-mainnet historical data and run the founder-selected Week 2 Paper Trading strategies through Historical Replay.",
        "- Artifact mode: latest-data replay/evidence-style review artifacts; SV2.2 is not itself a replay strategy.",
        "- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.",
        "- Trading boundary: no orders, private/signed/order endpoints, API keys, testnet strategy truth, live approval, or production approval.",
        "",
        "## Scope",
        "",
        f"- Generated at UTC: `{summary.get('generated_at_utc')}`",
        f"- Symbols: `{len(summary.get('universe_policy', {}).get('selected_symbols', []))}` founder-approved/resolved symbols",
        f"- Timeframes: `{', '.join(summary.get('timeframes', []))}`",
        f"- Disabled timeframes: `{', '.join(summary.get('disabled_timeframes', []))}`",
        f"- Data source: `{summary.get('source', {}).get('strategy_truth')}`",
        "",
        "## Refresh Result",
        "",
        f"- Datasets: `{summary.get('dataset_count')}`",
        f"- Refreshed datasets: `{summary.get('refreshed_dataset_count')}`",
        f"- Completed strategy replays: `{summary.get('completed_replay_count')}`",
        f"- Status counts: `{dict(status_counts)}`",
        f"- Latest 1h close: `{latest.get('1h')}`",
        f"- Latest 4h close: `{latest.get('4h')}`",
        f"- Latest 1d close: `{latest.get('1d')}`",
        f"- Chart data root: `{summary.get('dashboard_status', {}).get('chart_data_root')}`",
        f"- Evidence-style pack count: `{len(summary.get('evidence_pack_paths', []))}`",
        "",
        "## Selected Strategy Replay Scope",
        "",
        f"- Strategies: `{', '.join(summary.get('week2_replay_strategy_ids', []))}`",
        f"- Fill assumptions: `{', '.join(summary.get('fill_assumptions', []))}`",
        "- Timeframe scope: `1h, 4h, 1d`; `15m` remains disabled.",
        "- Replay source: refreshed Hyperliquid public-mainnet candles fetched by SV2.2, not stale dashboard rows.",
        "",
        "## Top Replay Rows By Net PnL",
        "",
        "| Strategy | Symbol | Timeframe | Fill | Net PnL | Trades | Max DD |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
        *[
            "| `{strategy_id}` | `{symbol}` | `{timeframe}` | `{fill_assumption}` | `{net_pnl}` | `{trade_count}` | `{max_drawdown}` |".format(**row)
            for row in top_rows
        ],
        "" if top_rows else "- No completed replay rows were generated.",
        "",
        "## Dashboard Use",
        "",
        "- Historical Replay should show SV2.2 as a latest data/replay source, not as a standalone candle-refresh pseudo-strategy.",
        "- Evidence and The Lab should show SV2.2 latest replay freshness separately from canonical SV2.0.2/SV2.1 evidence status.",
        "- The replay strategy dropdown should contain the three Week 2 strategies, not a candle-refresh pseudo-strategy.",
        "",
        "## Boundaries",
        "",
        "- Public Hyperliquid mainnet candles remain strategy truth.",
        "- Testnet data is not strategy truth.",
        "- Testnet fills do not update synthetic PnL.",
        "- No live trading is approved.",
        "- No strategy is production-approved.",
    ]
    if summary.get("fetch_error"):
        lines.extend(["", "## Fetch Blocker", "", f"- `{summary['fetch_error']}`"])
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    run_timestamp = args.run_timestamp or generated_at.strftime("%Y%m%dT%H%M%SZ")
    timeframes = tuple(args.timeframe or ACTIVE_TIMEFRAMES)
    requested_end = parse_utc(args.end_at) if args.end_at else generated_at
    selected_symbols = [symbol.upper() for symbol in args.symbol] if args.symbol else list(FOUNDER_APPROVED_RESOLVED_SYMBOLS)
    datasets: list[SV22Dataset] = []
    replay_results: list[SV22ReplayResult] = []
    fetch_error: str | None = None

    if args.fetch_public_data:
        try:
            meta = fetch_hyperliquid_public_info(
                hyperliquid_meta_payload(),
                url=HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
                timeout_seconds=args.timeout_seconds,
            )
            identities = filter_founder_approved_identities(active_hyperliquid_identities_from_meta(meta))
            wanted = set(selected_symbols)
            identities = [identity for identity in identities if identity.canonical_symbol.upper() in wanted]
            for identity in identities:
                for timeframe in timeframes:
                    datasets.append(
                        fetch_dataset(
                            identity=identity,
                            timeframe=timeframe,
                            effective_end=latest_closed_timeframe(requested_end, timeframe),
                            work_dir=args.work_dir,
                            timeout_seconds=args.timeout_seconds,
                        )
                    )
            datasets.extend(missing_identity_datasets(identities, timeframes))
            for dataset in datasets:
                replay_results.extend(
                    write_replay_artifacts(
                        dataset=dataset,
                        chart_root=args.chart_root,
                        pack_root=args.pack_root,
                        run_timestamp=run_timestamp,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - report exact blocker in summary.
            fetch_error = f"{type(exc).__name__}:{exc}"
    summary = build_summary(
        generated_at=generated_at,
        run_timestamp=run_timestamp,
        datasets=datasets,
        fetch_public_data=args.fetch_public_data,
        chart_root=args.chart_root,
        selected_symbols=selected_symbols,
        timeframes=timeframes,
        replay_results=replay_results,
        fetch_error=fetch_error,
    )
    write_json(args.summary_output, summary)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_report(summary), encoding="utf-8")
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"Status: {summary['status']}")
    print(f"Refreshed datasets: {summary['refreshed_dataset_count']}")
    print(f"Completed replays: {summary['completed_replay_count']}")
    if fetch_error:
        print(f"Fetch error: {fetch_error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
