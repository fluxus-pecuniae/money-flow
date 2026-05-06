#!/usr/bin/env python3
"""Prepare public BTC/ETH/SOL candles for supported venue adapters.

Research-only helper:
- public endpoints only
- no keys
- no private/signed/order endpoints
- writes timezone-explicit CSVs under /tmp
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RUN_ROOT = Path("/tmp/money-flow-sv1125-supported-venues-public")
CSV_ROOT = RUN_ROOT / "csv"
RAW_ROOT = RUN_ROOT / "raw"
PREFLIGHT_ROOT = RUN_ROOT / "preflight"
SUMMARY_PATH = RUN_ROOT / "summary_supported_venues_public.json"
REQUIREMENTS_PATH = RUN_ROOT / "requirements_supported_venues_public.json"

SYMBOLS = ("BTC", "ETH", "SOL")
TIMEFRAMES = {
    "15m": {"delta": timedelta(minutes=15), "start": "2026-03-15T00:00:00Z", "end": "2026-05-05T00:00:00Z"},
    "1h": {"delta": timedelta(hours=1), "start": "2026-01-01T00:00:00Z", "end": "2026-05-05T00:00:00Z"},
    "4h": {"delta": timedelta(hours=4), "start": "2026-01-01T00:00:00Z", "end": "2026-05-05T00:00:00Z"},
}


@dataclass(frozen=True)
class VenueSpec:
    venue: str
    source: str
    market_type: str
    product_type: str
    quote_asset: str
    settlement_asset: str | None
    trade_count_mode: str


VENUES = {
    "aster": VenueSpec("aster", "aster_public_fapi_klines", "perpetual", "linear", "USDT", "USDT", "native"),
    "binance": VenueSpec("binance", "binance_public_spot_klines", "spot", "spot", "USDT", None, "native"),
    "okx": VenueSpec("okx", "okx_public_history_candles", "perpetual", "linear", "USDT", "USDT", "unavailable"),
    "coinbase_advanced_trade": VenueSpec(
        "coinbase_advanced_trade",
        "coinbase_public_product_candles",
        "spot",
        "spot",
        "USD",
        None,
        "unavailable",
    ),
    "kraken": VenueSpec("kraken", "kraken_public_ohlc", "spot", "spot", "USD", None, "native_recent_limited"),
}


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def sec(value: datetime) -> int:
    return int(value.timestamp())


def instrument_key(spec: VenueSpec, symbol: str) -> str:
    if spec.settlement_asset is None:
        return f"{spec.market_type}:{spec.product_type}:{symbol}:{spec.quote_asset}"
    return f"{spec.market_type}:{spec.product_type}:{symbol}:{spec.quote_asset}:{spec.settlement_asset}"


def expected_slots(start: datetime, end: datetime, delta: timedelta) -> list[datetime]:
    slots: list[datetime] = []
    cursor = start + delta
    while cursor <= end:
        slots.append(cursor)
        cursor += delta
    return slots


def request_json(url: str, params: dict[str, Any] | None = None, *, body: dict[str, Any] | None = None) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = None
    headers = {"User-Agent": "money-flow-public-research/1.0"}
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed public API URLs below.
        return json.loads(response.read().decode())


def decimal_ok(value: Any) -> bool:
    try:
        return Decimal(str(value)).is_finite()
    except (InvalidOperation, ValueError):
        return False


def valid_row(row: dict[str, Any], delta: timedelta) -> bool:
    if parse_utc(row["close_time"]) - parse_utc(row["open_time"]) != delta:
        return False
    o = Decimal(row["open"])
    h = Decimal(row["high"])
    low = Decimal(row["low"])
    c = Decimal(row["close"])
    volume = Decimal(row["volume"])
    trade_count = int(row["trade_count"])
    return (
        all(decimal_ok(row[key]) and Decimal(row[key]) > 0 for key in ("open", "high", "low", "close"))
        and low <= min(o, c) <= max(o, c) <= h
        and volume >= 0
        and trade_count >= 0
    )


def filter_rows(rows: list[dict[str, Any]], *, start: datetime, end: datetime, delta: timedelta) -> list[dict[str, Any]]:
    by_close: dict[datetime, dict[str, Any]] = {}
    for row in rows:
        close_time = parse_utc(row["close_time"])
        if start < close_time <= end and valid_row(row, delta):
            by_close[close_time] = row
    return [by_close[key] for key in sorted(by_close)]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["symbol", "instrument_key", "open_time", "close_time", "open", "high", "low", "close", "volume", "trade_count"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def filename(venue: str, symbol: str, timeframe: str, start: datetime, end: datetime) -> str:
    start_slug = start.strftime("%Y%m%d_%H%M%Sz").lower()
    end_slug = end.strftime("%Y%m%d_%H%M%Sz").lower()
    return f"{venue}_{symbol.lower()}_{timeframe}_{start_slug}_{end_slug}.csv"


def binance_interval(timeframe: str) -> str:
    return timeframe


def okx_bar(timeframe: str) -> str:
    return {"15m": "15m", "1h": "1H", "4h": "4H"}[timeframe]


def coinbase_granularity(timeframe: str) -> str:
    return {"15m": "FIFTEEN_MINUTE", "1h": "ONE_HOUR", "4h": "FOUR_HOUR"}[timeframe]


def kraken_interval(timeframe: str) -> int:
    return {"15m": 15, "1h": 60, "4h": 240}[timeframe]


def rows_from_kline_payload(
    payload: list[Any],
    *,
    spec: VenueSpec,
    symbol: str,
    delta: timedelta,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload:
        open_time = datetime.fromtimestamp(int(item[0]) / 1000, tz=UTC)
        close_time = open_time + delta
        rows.append(
            {
                "symbol": symbol,
                "instrument_key": instrument_key(spec, symbol),
                "open_time": iso_z(open_time),
                "close_time": iso_z(close_time),
                "open": str(item[1]),
                "high": str(item[2]),
                "low": str(item[3]),
                "close": str(item[4]),
                "volume": str(item[5]),
                "trade_count": str(int(item[8])) if len(item) > 8 else "0",
            }
        )
    return rows


def fetch_binance_like(
    *,
    base_url: str,
    path: str,
    spec: VenueSpec,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    limit: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    delta = TIMEFRAMES[timeframe]["delta"]
    cursor_ms = ms(start)
    end_ms = ms(end)
    all_rows: list[dict[str, Any]] = []
    raw_paths: list[str] = []
    page = 0
    while cursor_ms < end_ms:
        page += 1
        payload = request_json(
            base_url + path,
            {
                "symbol": f"{symbol}USDT",
                "interval": binance_interval(timeframe),
                "startTime": cursor_ms,
                "endTime": end_ms,
                "limit": limit,
            },
        )
        raw_path = RAW_ROOT / spec.venue / f"{symbol}_{timeframe}_{page:04d}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        raw_paths.append(str(raw_path))
        if not isinstance(payload, list) or not payload:
            break
        all_rows.extend(rows_from_kline_payload(payload, spec=spec, symbol=symbol, delta=delta))
        last_open = int(payload[-1][0])
        next_cursor = last_open + int(delta.total_seconds() * 1000)
        if next_cursor <= cursor_ms:
            break
        cursor_ms = next_cursor
        time.sleep(0.04)
    return filter_rows(all_rows, start=start, end=end, delta=delta), raw_paths


def fetch_okx(
    *, spec: VenueSpec, symbol: str, timeframe: str, start: datetime, end: datetime
) -> tuple[list[dict[str, Any]], list[str]]:
    delta = TIMEFRAMES[timeframe]["delta"]
    cursor_ms = ms(end) + int(delta.total_seconds() * 1000)
    start_ms = ms(start)
    all_rows: list[dict[str, Any]] = []
    raw_paths: list[str] = []
    page = 0
    while cursor_ms > start_ms:
        page += 1
        payload = request_json(
            "https://www.okx.com/api/v5/market/history-candles",
            {
                "instId": f"{symbol}-USDT-SWAP",
                "bar": okx_bar(timeframe),
                "after": cursor_ms,
                "limit": 100,
            },
        )
        raw_path = RAW_ROOT / spec.venue / f"{symbol}_{timeframe}_{page:04d}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        raw_paths.append(str(raw_path))
        data = payload.get("data", []) if isinstance(payload, dict) else []
        if not data:
            break
        for item in data:
            open_time = datetime.fromtimestamp(int(item[0]) / 1000, tz=UTC)
            all_rows.append(
                {
                    "symbol": symbol,
                    "instrument_key": instrument_key(spec, symbol),
                    "open_time": iso_z(open_time),
                    "close_time": iso_z(open_time + delta),
                    "open": str(item[1]),
                    "high": str(item[2]),
                    "low": str(item[3]),
                    "close": str(item[4]),
                    "volume": str(item[6] if len(item) > 6 else item[5]),
                    "trade_count": "0",
                }
            )
        oldest = min(int(item[0]) for item in data)
        next_cursor = oldest
        if next_cursor >= cursor_ms:
            break
        cursor_ms = next_cursor
        time.sleep(0.06)
    return filter_rows(all_rows, start=start, end=end, delta=delta), raw_paths


def fetch_coinbase(
    *, spec: VenueSpec, symbol: str, timeframe: str, start: datetime, end: datetime
) -> tuple[list[dict[str, Any]], list[str]]:
    delta = TIMEFRAMES[timeframe]["delta"]
    chunk = delta * 300
    cursor = start
    all_rows: list[dict[str, Any]] = []
    raw_paths: list[str] = []
    page = 0
    while cursor < end:
        page += 1
        chunk_end = min(cursor + chunk, end)
        payload = request_json(
            f"https://api.coinbase.com/api/v3/brokerage/market/products/{symbol}-USD/candles",
            {
                "start": sec(cursor),
                "end": sec(chunk_end),
                "granularity": coinbase_granularity(timeframe),
                "limit": 350,
            },
        )
        raw_path = RAW_ROOT / spec.venue / f"{symbol}_{timeframe}_{page:04d}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        raw_paths.append(str(raw_path))
        data = payload.get("candles", []) if isinstance(payload, dict) else []
        for item in data:
            open_time = datetime.fromtimestamp(int(item["start"]), tz=UTC)
            all_rows.append(
                {
                    "symbol": symbol,
                    "instrument_key": instrument_key(spec, symbol),
                    "open_time": iso_z(open_time),
                    "close_time": iso_z(open_time + delta),
                    "open": str(item["open"]),
                    "high": str(item["high"]),
                    "low": str(item["low"]),
                    "close": str(item["close"]),
                    "volume": str(item["volume"]),
                    "trade_count": "0",
                }
            )
        cursor = chunk_end
        time.sleep(0.05)
    return filter_rows(all_rows, start=start, end=end, delta=delta), raw_paths


def fetch_kraken(
    *, spec: VenueSpec, symbol: str, timeframe: str, start: datetime, end: datetime
) -> tuple[list[dict[str, Any]], list[str]]:
    delta = TIMEFRAMES[timeframe]["delta"]
    pair = {"BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD"}[symbol]
    payload = request_json(
        "https://api.kraken.com/0/public/OHLC",
        {"pair": pair, "interval": kraken_interval(timeframe), "since": sec(start)},
    )
    raw_path = RAW_ROOT / spec.venue / f"{symbol}_{timeframe}_0001.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    data = next((value for key, value in result.items() if key != "last"), [])
    rows: list[dict[str, Any]] = []
    for item in data:
        open_time = datetime.fromtimestamp(int(item[0]), tz=UTC)
        rows.append(
            {
                "symbol": symbol,
                "instrument_key": instrument_key(spec, symbol),
                "open_time": iso_z(open_time),
                "close_time": iso_z(open_time + delta),
                "open": str(item[1]),
                "high": str(item[2]),
                "low": str(item[3]),
                "close": str(item[4]),
                "volume": str(item[6]),
                "trade_count": str(int(item[7])) if len(item) > 7 else "0",
            }
        )
    return filter_rows(rows, start=start, end=end, delta=delta), [str(raw_path)]


def fetch_rows(venue: str, symbol: str, timeframe: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], list[str], str | None]:
    spec = VENUES[venue]
    try:
        if venue == "aster":
            rows, raw_paths = fetch_binance_like(
                base_url="https://fapi.asterdex.com",
                path="/fapi/v1/klines",
                spec=spec,
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=1500,
            )
        elif venue == "binance":
            rows, raw_paths = fetch_binance_like(
                base_url="https://api.binance.com",
                path="/api/v3/klines",
                spec=spec,
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=1000,
            )
        elif venue == "okx":
            rows, raw_paths = fetch_okx(spec=spec, symbol=symbol, timeframe=timeframe, start=start, end=end)
        elif venue == "coinbase_advanced_trade":
            rows, raw_paths = fetch_coinbase(spec=spec, symbol=symbol, timeframe=timeframe, start=start, end=end)
        elif venue == "kraken":
            rows, raw_paths = fetch_kraken(spec=spec, symbol=symbol, timeframe=timeframe, start=start, end=end)
        else:
            raise ValueError(f"unsupported venue: {venue}")
        return rows, raw_paths, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
        return [], [], f"{type(exc).__name__}: {exc}"


def main() -> int:
    CSV_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    PREFLIGHT_ROOT.mkdir(parents=True, exist_ok=True)
    generated_at = iso_z(datetime.now(UTC))
    summary: dict[str, Any] = {
        "generated_at_utc": generated_at,
        "run_root": str(RUN_ROOT),
        "csv_root": str(CSV_ROOT),
        "supported_adapter_venues_considered": ["hyperliquid", *VENUES.keys()],
        "notes": [
            "Hyperliquid files from SV1.12.4 remain at /tmp/money-flow-sv1124-public-ytd-recent/csv and are not regenerated here.",
            "OKX and Coinbase public candle endpoints do not provide trade_count; generated files use 0 only as schema placeholder and are not canonical import-ready.",
            "Kraken REST OHLC returns up to 720 recent entries and cannot cover the selected YTD/recent windows.",
        ],
        "files": [],
    }
    requirements: list[dict[str, Any]] = []
    for venue, spec in VENUES.items():
        for symbol in SYMBOLS:
            for timeframe, tf_info in TIMEFRAMES.items():
                start = parse_utc(str(tf_info["start"]))
                end = parse_utc(str(tf_info["end"]))
                delta = tf_info["delta"]
                expected = expected_slots(start, end, delta)
                rows, raw_paths, error = fetch_rows(venue, symbol, timeframe, start, end)
                found_slots = {parse_utc(row["close_time"]) for row in rows}
                missing = [iso_z(slot) for slot in expected if slot not in found_slots]
                extra = [iso_z(slot) for slot in sorted(found_slots) if slot not in set(expected)]
                complete = not error and len(rows) == len(expected) and not missing and not extra
                path: Path | None = None
                file_hash: str | None = None
                if rows:
                    path = CSV_ROOT / venue / filename(venue, symbol, timeframe, start, end)
                    file_hash = write_csv(path, rows)
                    requirements.append(
                        {
                            "venue": venue,
                            "symbol": symbol,
                            "instrument_key": instrument_key(spec, symbol),
                            "timeframe": timeframe,
                            "component": f"sleeve_{timeframe}",
                            "requested_start_at": iso_z(start),
                            "requested_end_at": iso_z(end),
                            "expected_candle_count": len(expected),
                            "window_label": f"{venue}_sleeve_{timeframe}",
                            "suggested_filename": path.name,
                            "input_path": str(path),
                        }
                    )
                summary["files"].append(
                    {
                        "venue": venue,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "market_type": spec.market_type,
                        "product_type": spec.product_type,
                        "quote_asset": spec.quote_asset,
                        "settlement_asset": spec.settlement_asset,
                        "source": spec.source,
                        "trade_count_mode": spec.trade_count_mode,
                        "start_at": iso_z(start),
                        "end_at": iso_z(end),
                        "expected_rows": len(expected),
                        "rows_found": len(rows),
                        "csv_path": str(path) if path else None,
                        "sha256": file_hash,
                        "complete_close_slot_coverage": complete,
                        "missing_count": len(missing),
                        "extra_count": len(extra),
                        "first_missing_close_times": missing[:10],
                        "raw_paths_count": len(raw_paths),
                        "error": error,
                        "canonical_import_readiness": (
                            "blocked_trade_count_unavailable"
                            if spec.trade_count_mode == "unavailable" and rows
                            else ("blocked_incomplete_public_coverage" if not complete else "candidate_file_ready_for_identity_preflight")
                        ),
                    }
                )
                print(f"{venue} {symbol} {timeframe}: rows={len(rows)} expected={len(expected)} error={error}", flush=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    REQUIREMENTS_PATH.write_text(json.dumps({"requirements": requirements}, indent=2, sort_keys=True), encoding="utf-8")
    print(str(SUMMARY_PATH))
    print(str(REQUIREMENTS_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
