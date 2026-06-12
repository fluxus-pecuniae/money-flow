"""DATA1 — OPTIONAL live-fetch smoke (public read-only; gated off in CI).

Skipped unless DATA1_LIVE_SMOKE=1 is set, so CI stays deterministic. When
enabled it makes ONE tiny unauthenticated public market-data request per
venue and asserts the venue-native shape still normalizes — an early-warning
canary for venue API changes, not part of any evidence run.

Run locally:
    DATA1_LIVE_SMOKE=1 .venv/bin/python -m pytest -q tests/test_data1_live_smoke.py
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

from services.market_data import data1_multi_venue as mv

pytestmark = pytest.mark.skipif(
    os.environ.get("DATA1_LIVE_SMOKE") != "1",
    reason="live public-endpoint smoke; set DATA1_LIVE_SMOKE=1 to run",
)


@pytest.fixture(scope="module")
def transport():
    from scripts.fetch_data1_multi_venue_snapshot import make_transport

    return make_transport()


@pytest.fixture(scope="module")
def window():
    now = datetime.now(UTC)
    end_ms = mv.last_closed_day_end_ms(now)
    start_ms = int((now - timedelta(days=5)).timestamp() * 1000)
    return start_ms, end_ms


def test_binance_funding_still_parses(transport, window):
    rows = mv.fetch_binance_funding(transport, "BTCUSDT", *window)
    events = mv.normalize_funding("binance", rows)
    assert events and float(events[-1]["rate"]) is not None


def test_bybit_perp_kline_still_parses(transport, window):
    rows = mv.fetch_bybit_klines(transport, "BTCUSDT", *window, market="perp")
    candles = mv.normalize_daily_candles("bybit", "perp_1d", rows)
    assert candles and candles[-1]["close_time"].endswith("T00:00:00Z")


def test_okx_utc_daily_bar_still_parses(transport, window):
    rows = mv.fetch_okx_candles(transport, "BTC-USDT", *window)
    candles = mv.normalize_daily_candles("okx", "spot_1d", rows)
    assert candles  # would raise Data1AlignmentError if OKX dropped 1Dutc


def test_coinbase_spot_candles_still_parse(transport, window):
    rows = mv.fetch_coinbase_candles(transport, "BTC-USD", *window)
    candles = mv.normalize_daily_candles("coinbase", "spot_1d", rows)
    assert candles and float(candles[-1]["close"]) > 0


def test_kraken_futures_funding_still_parses(transport, window):
    rows = mv.fetch_kraken_futures_funding(transport, "PF_XBTUSD", *window)
    events = mv.normalize_funding("kraken", rows)
    assert events and mv.observed_funding_interval_hours(events) is not None


def test_hyperliquid_perp_candles_still_parse(transport, window):
    rows = mv.fetch_hyperliquid_candles(transport, "BTC", *window)
    candles = mv.normalize_daily_candles("hyperliquid", "perp_1d", rows)
    assert candles and candles[-1]["close_time"].endswith("T00:00:00Z")
