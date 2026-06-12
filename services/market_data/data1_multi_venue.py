"""DATA1 — multi-venue public read-only market & funding data foundation.

Every strategy phase so far consumed Hyperliquid-only data. DATA1 builds the
multi-venue base (perp funding history, perp daily candles, spot daily
candles) for the liquid majors across the deepest public venues so the next
funding test is venue-fair and future trend tests have broader history:

  - hyperliquid  (perp funding + perp candles; spot candles for BTC/ETH/SOL)
  - binance      (perp funding + perp candles + spot candles)
  - bybit        (perp funding + perp candles + spot candles)
  - okx          (perp funding + perp candles + spot candles; no BNB listing)
  - coinbase     (spot candles only — the public Exchange API has no perp or
                  funding market data; recorded as a venue gap, not filled)
  - kraken       (spot candles via api.kraken.com; perp funding + perp candles
                  via the public Kraken Futures API; no BNB listing)

PUBLIC READ-ONLY ONLY: every endpoint in PUBLIC_ENDPOINT_ALLOWLIST is an
unauthenticated public market-data endpoint. No API keys are read, no
private, signed, account, or order endpoint exists in this module, nothing
is submitted anywhere. Data ingestion for research only — no strategy logic,
no runtime change.

Honesty rules (the point of the dataset):
  - Differing funding intervals (1h Hyperliquid / Kraken Futures vs 8h
    Binance / Bybit / OKX) are recorded per venue, observed from the data,
    and aggregated to daily sums the same way for every venue — never
    rescaled to pretend the venues are identical.
  - Daily candles are accepted only on exact midnight-UTC boundaries (OKX
    must be fetched with ``bar=1Dutc``; the default OKX daily bar is UTC+8
    and is refused by the normalizer rather than silently mis-aligned).
  - Where a venue lacks an asset, a market, or a history period, the gap is
    reported as coverage (``venue_lacks_market`` / ``fetch_failed`` /
    ``artifact_missing``) — never substituted, forward-filled, or truncated
    away. Alignment unions calendars and leaves explicit ``None`` holes.
  - Raw per-venue payload artifacts are ignored local files; the committed
    summary records endpoint, params, row counts, history depth, funding
    interval, and the sha256 of every artifact so the dataset is auditable
    and any tampering is detectable at load time.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

PHASE = "DATA1"
DAY_MS = 86_400_000

ASSETS: tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "AVAX")
VENUES: tuple[str, ...] = ("hyperliquid", "binance", "bybit", "okx", "coinbase", "kraken")
SERIES_KEYS: tuple[str, ...] = ("funding", "perp_1d", "spot_1d")

# Transport seam: the fetch script injects a real HTTP transport; tests inject
# fakes. Signature: transport(method, url, json_body_or_None) -> parsed JSON.
Transport = Callable[[str, str, dict[str, Any] | None], Any]

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

PUBLIC_ENDPOINT_ALLOWLIST: tuple[str, ...] = (
    HYPERLIQUID_INFO_URL,
    "https://fapi.binance.com/fapi/v1/fundingRate",
    "https://fapi.binance.com/fapi/v1/klines",
    "https://api.binance.com/api/v3/klines",
    "https://api.bybit.com/v5/market/funding/history",
    "https://api.bybit.com/v5/market/kline",
    "https://www.okx.com/api/v5/public/funding-rate-history",
    "https://www.okx.com/api/v5/market/history-candles",
    "https://api.exchange.coinbase.com/products/",
    "https://api.kraken.com/0/public/OHLC",
    "https://futures.kraken.com/derivatives/api/v4/historicalfundingrates",
    "https://futures.kraken.com/api/charts/v1/trade/",
)

# Declared funding intervals (hours) from each venue's public docs; the
# snapshot also records the interval OBSERVED in the fetched events and the
# two must reconcile (a drift is reported, never papered over). Bybit/OKX can
# shorten intervals on extreme markets — another reason observed is recorded.
DECLARED_FUNDING_INTERVAL_HOURS: dict[str, float | None] = {
    "hyperliquid": 1.0,
    "binance": 8.0,
    "bybit": 8.0,
    "okx": 8.0,
    "kraken": 1.0,  # Kraken Futures publishes hourly relative funding rates
    "coinbase": None,  # no perp market on the public Exchange API
}

# Cited public rate limits (request budget the fetcher stays far under).
CITED_RATE_LIMITS: dict[str, str] = {
    "hyperliquid": "info endpoint weight budget 1200/min (fundingHistory weight 20) — fetcher paces ~1 req/s",
    "binance": "2400 request weight/min (fundingRate weight 1, klines weight <=10) — fetcher paces ~4 req/s",
    "bybit": "public market endpoints ~600 req/5s per IP — fetcher paces ~4 req/s",
    "okx": "funding-rate-history 10 req/2s, history-candles 10 req/2s per IP — fetcher paces ~3 req/s",
    "coinbase": "public market data ~10 req/s per IP — fetcher paces ~4 req/s",
    "kraken": "spot public ~1 req/s counterised; futures public charts/funding uncounted light use — fetcher paces ~1 req/s",
}

# Hyperliquid spot pairs (spotMeta index ids) — only BTC/ETH/SOL of the DATA1
# universe have an HL spot market (via Unit); the rest are recorded gaps.
HYPERLIQUID_SPOT_PAIRS: dict[str, tuple[str, str]] = {
    "BTC": ("@142", "UBTC/USDC"),
    "ETH": ("@151", "UETH/USDC"),
    "SOL": ("@156", "USOL/USDC"),
}

# Kraken venue symbols. Spot uses api.kraken.com pair names (DOGE is XDG);
# perp funding/candles use Kraken Futures PF_* multi-collateral perps.
KRAKEN_SPOT_PAIRS: dict[str, str] = {
    "BTC": "XBTUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
    "DOGE": "XDGUSD",
    "AVAX": "AVAXUSD",
}
KRAKEN_FUTURES_SYMBOLS: dict[str, str] = {
    "BTC": "PF_XBTUSD",
    "ETH": "PF_ETHUSD",
    "SOL": "PF_SOLUSD",
    "XRP": "PF_XRPUSD",
    "DOGE": "PF_DOGEUSD",
    "AVAX": "PF_AVAXUSD",
}

# Human-auditable endpoint documentation, recorded into every artifact and
# the committed summary (exact request URLs are built in the fetchers below).
ENDPOINT_TEMPLATES: dict[tuple[str, str], str] = {
    ("hyperliquid", "funding"): "POST https://api.hyperliquid.xyz/info type=fundingHistory (paginated 500/page)",
    ("hyperliquid", "perp_1d"): "POST https://api.hyperliquid.xyz/info type=candleSnapshot interval=1d (<=5000 candles)",
    ("hyperliquid", "spot_1d"): "POST https://api.hyperliquid.xyz/info type=candleSnapshot interval=1d spot pair id (<=5000 candles)",
    ("binance", "funding"): "GET https://fapi.binance.com/fapi/v1/fundingRate (paginated 1000/page, forward)",
    ("binance", "perp_1d"): "GET https://fapi.binance.com/fapi/v1/klines interval=1d (paginated 1500/page, forward)",
    ("binance", "spot_1d"): "GET https://api.binance.com/api/v3/klines interval=1d (paginated 1000/page, forward)",
    ("bybit", "funding"): "GET https://api.bybit.com/v5/market/funding/history category=linear (paginated 200/page, backward)",
    ("bybit", "perp_1d"): "GET https://api.bybit.com/v5/market/kline category=linear interval=D (paginated 1000/page, backward)",
    ("bybit", "spot_1d"): "GET https://api.bybit.com/v5/market/kline category=spot interval=D (paginated 1000/page, backward)",
    ("okx", "funding"): "GET https://www.okx.com/api/v5/public/funding-rate-history (paginated 100/page, backward)",
    ("okx", "perp_1d"): "GET https://www.okx.com/api/v5/market/history-candles bar=1Dutc (paginated 100/page, backward; UTC-aligned bar required)",
    ("okx", "spot_1d"): "GET https://www.okx.com/api/v5/market/history-candles bar=1Dutc (paginated 100/page, backward; UTC-aligned bar required)",
    ("coinbase", "spot_1d"): "GET https://api.exchange.coinbase.com/products/{product}/candles granularity=86400 (<=300/window, backward windows)",
    ("kraken", "funding"): "GET https://futures.kraken.com/derivatives/api/v4/historicalfundingrates (single call; trailing window)",
    ("kraken", "perp_1d"): "GET https://futures.kraken.com/api/charts/v1/trade/{symbol}/1d (single call, <=5000)",
    ("kraken", "spot_1d"): "GET https://api.kraken.com/0/public/OHLC interval=1440 (single call; venue caps history at last 720 candles)",
}

STATUS_EXPECTED = "expected"
STATUS_VENUE_LACKS = "venue_lacks_market"
STATUS_OK = "ok"
STATUS_FETCH_FAILED = "fetch_failed"
STATUS_ARTIFACT_MISSING = "artifact_missing_rerun_fetch_script"

BOUNDARIES: dict[str, bool] = {
    "research_only": True,
    "public_read_only": True,
    "calls_private_signed_or_order_endpoints": False,
    "creates_orders": False,
    "mutates_runtime_artifacts": False,
}


class Data1Error(RuntimeError):
    """Base error for DATA1 ingestion/loading."""


class Data1AlignmentError(Data1Error):
    """A candle is not on an exact midnight-UTC daily boundary."""


class Data1IntegrityError(Data1Error):
    """A snapshot artifact does not match its committed sha256."""


# ---------------------------------------------------------------------------
# Catalog: which (venue, asset, series) markets exist, and under what symbol.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketRef:
    venue: str
    asset: str
    series: str  # funding | perp_1d | spot_1d
    status: str  # expected | venue_lacks_market
    venue_symbol: str | None
    note: str


def _ref(venue: str, asset: str, series: str, symbol: str | None, note: str = "") -> MarketRef:
    status = STATUS_EXPECTED if symbol is not None else STATUS_VENUE_LACKS
    return MarketRef(venue=venue, asset=asset, series=series, status=status, venue_symbol=symbol, note=note)


def build_catalog() -> dict[tuple[str, str, str], MarketRef]:
    """The full venue x asset x series map, gaps included explicitly."""
    catalog: dict[tuple[str, str, str], MarketRef] = {}

    def put(ref: MarketRef) -> None:
        catalog[(ref.venue, ref.asset, ref.series)] = ref

    for asset in ASSETS:
        usdt = f"{asset}USDT"
        # hyperliquid: perps for all seven; spot only where an HL pair exists.
        put(_ref("hyperliquid", asset, "funding", asset))
        put(_ref("hyperliquid", asset, "perp_1d", asset))
        hl_spot = HYPERLIQUID_SPOT_PAIRS.get(asset)
        put(
            _ref(
                "hyperliquid",
                asset,
                "spot_1d",
                hl_spot[0] if hl_spot else None,
                hl_spot[1] if hl_spot else "no Hyperliquid spot pair for this asset",
            )
        )
        # binance / bybit: all seven on both perp and spot.
        for venue in ("binance", "bybit"):
            put(_ref(venue, asset, "funding", usdt))
            put(_ref(venue, asset, "perp_1d", usdt))
            put(_ref(venue, asset, "spot_1d", usdt))
        # okx: no BNB listing at all.
        if asset == "BNB":
            for series in SERIES_KEYS:
                put(_ref("okx", asset, series, None, "OKX does not list BNB"))
        else:
            put(_ref("okx", asset, "funding", f"{asset}-USDT-SWAP"))
            put(_ref("okx", asset, "perp_1d", f"{asset}-USDT-SWAP"))
            put(_ref("okx", asset, "spot_1d", f"{asset}-USDT"))
        # coinbase: spot only; no perp/funding on the public Exchange API.
        cb_note = "Coinbase Exchange public API has no perp/funding market data"
        put(_ref("coinbase", asset, "funding", None, cb_note))
        put(_ref("coinbase", asset, "perp_1d", None, cb_note))
        if asset == "BNB":
            put(_ref("coinbase", asset, "spot_1d", None, "Coinbase does not list BNB"))
        else:
            put(_ref("coinbase", asset, "spot_1d", f"{asset}-USD"))
        # kraken: spot pairs + Kraken Futures perps; no BNB listing.
        if asset == "BNB":
            for series in SERIES_KEYS:
                put(_ref("kraken", asset, series, None, "Kraken does not list BNB"))
        else:
            put(_ref("kraken", asset, "funding", KRAKEN_FUTURES_SYMBOLS[asset]))
            put(_ref("kraken", asset, "perp_1d", KRAKEN_FUTURES_SYMBOLS[asset]))
            put(_ref("kraken", asset, "spot_1d", KRAKEN_SPOT_PAIRS[asset]))
    return catalog


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def last_closed_day_end_ms(now: datetime) -> int:
    """Close timestamp (ms) of the most recent fully closed UTC day."""
    floor = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(floor.timestamp() * 1000)


def _checked_url(url: str) -> str:
    if not any(url.startswith(prefix) for prefix in PUBLIC_ENDPOINT_ALLOWLIST):
        raise Data1Error(f"endpoint_not_in_public_allowlist:{url}")
    return url


def _get(transport: Transport, url: str) -> Any:
    return transport("GET", _checked_url(url), None)


def _post(transport: Transport, url: str, body: dict[str, Any]) -> Any:
    return transport("POST", _checked_url(url), body)


# ---------------------------------------------------------------------------
# Per-venue fetchers (pure pagination logic over an injected transport).
# Each returns the venue-NATIVE rows, deduplicated and oldest-first — raw
# enough to audit, untransformed; normalization is a separate tested step.
# ---------------------------------------------------------------------------


def fetch_binance_funding(transport: Transport, symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        url = (
            "https://fapi.binance.com/fapi/v1/fundingRate"
            f"?symbol={symbol}&startTime={cursor}&endTime={end_ms}&limit=1000"
        )
        page = _get(transport, url)
        if not page:
            break
        rows.extend(page)
        last = int(page[-1]["fundingTime"])
        if len(page) < 1000:
            break
        cursor = last + 1
    return _dedupe_sorted(rows, key=lambda r: int(r["fundingTime"]), end_ms=end_ms)


def fetch_binance_klines(
    transport: Transport, symbol: str, start_ms: int, end_ms: int, *, market: str
) -> list[list[Any]]:
    base = "https://fapi.binance.com/fapi/v1/klines" if market == "perp" else "https://api.binance.com/api/v3/klines"
    limit = 1500 if market == "perp" else 1000
    rows: list[list[Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        url = f"{base}?symbol={symbol}&interval=1d&startTime={cursor}&endTime={end_ms - 1}&limit={limit}"
        page = _get(transport, url)
        if not page:
            break
        rows.extend(page)
        last_open = int(page[-1][0])
        if len(page) < limit:
            break
        cursor = last_open + DAY_MS
    return _dedupe_sorted(rows, key=lambda r: int(r[0]), end_ms=end_ms)


def fetch_bybit_funding(transport: Transport, symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor_end = end_ms
    while cursor_end > start_ms:
        url = (
            "https://api.bybit.com/v5/market/funding/history"
            f"?category=linear&symbol={symbol}&startTime={start_ms}&endTime={cursor_end}&limit=200"
        )
        payload = _get(transport, url)
        page = (payload.get("result") or {}).get("list") or []
        if not page:
            break
        rows.extend(page)
        earliest = min(int(r["fundingRateTimestamp"]) for r in page)
        if len(page) < 200 or earliest <= start_ms:
            break
        cursor_end = earliest - 1
    return _dedupe_sorted(rows, key=lambda r: int(r["fundingRateTimestamp"]), end_ms=end_ms)


def fetch_bybit_klines(
    transport: Transport, symbol: str, start_ms: int, end_ms: int, *, market: str
) -> list[list[Any]]:
    category = "linear" if market == "perp" else "spot"
    rows: list[list[Any]] = []
    cursor_end = end_ms - 1
    while cursor_end > start_ms:
        url = (
            "https://api.bybit.com/v5/market/kline"
            f"?category={category}&symbol={symbol}&interval=D&start={start_ms}&end={cursor_end}&limit=1000"
        )
        payload = _get(transport, url)
        page = (payload.get("result") or {}).get("list") or []
        if not page:
            break
        rows.extend(page)
        earliest = min(int(r[0]) for r in page)
        if len(page) < 1000 or earliest <= start_ms:
            break
        cursor_end = earliest - 1
    return _dedupe_sorted(rows, key=lambda r: int(r[0]), end_ms=end_ms)


def fetch_okx_funding(transport: Transport, inst_id: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor_after = end_ms  # OKX `after`: records EARLIER than this ts
    while cursor_after > start_ms:
        url = (
            "https://www.okx.com/api/v5/public/funding-rate-history"
            f"?instId={inst_id}&after={cursor_after}&limit=100"
        )
        payload = _get(transport, url)
        page = payload.get("data") or []
        if not page:
            break
        rows.extend(page)
        earliest = min(int(r["fundingTime"]) for r in page)
        if len(page) < 100 or earliest <= start_ms:
            break
        cursor_after = earliest
    return _dedupe_sorted(rows, key=lambda r: int(r["fundingTime"]), end_ms=end_ms)


def fetch_okx_candles(transport: Transport, inst_id: str, start_ms: int, end_ms: int) -> list[list[Any]]:
    # bar=1Dutc is REQUIRED: the default OKX 1D bar is UTC+8-aligned (probe
    # verified 16:00Z opens) and would silently mis-align the whole venue.
    rows: list[list[Any]] = []
    cursor_after = end_ms + DAY_MS
    while cursor_after > start_ms:
        url = (
            "https://www.okx.com/api/v5/market/history-candles"
            f"?instId={inst_id}&bar=1Dutc&after={cursor_after}&limit=100"
        )
        payload = _get(transport, url)
        page = payload.get("data") or []
        if not page:
            break
        rows.extend(page)
        earliest = min(int(r[0]) for r in page)
        if len(page) < 100 or earliest <= start_ms:
            break
        cursor_after = earliest
    confirmed = [r for r in rows if str(r[-1]) == "1"]  # drop in-progress candles
    return _dedupe_sorted(confirmed, key=lambda r: int(r[0]), end_ms=end_ms)


def fetch_coinbase_candles(transport: Transport, product: str, start_ms: int, end_ms: int) -> list[list[Any]]:
    rows: list[list[Any]] = []
    window = 300 * DAY_MS  # Coinbase Exchange returns at most 300 candles
    cursor_end = end_ms
    while cursor_end > start_ms:
        cursor_start = max(start_ms, cursor_end - window)
        url = (
            f"https://api.exchange.coinbase.com/products/{product}/candles"
            f"?granularity=86400&start={_iso(cursor_start)}&end={_iso(cursor_end - DAY_MS)}"
        )
        page = _get(transport, url)
        rows.extend(page or [])
        cursor_end = cursor_start
    return _dedupe_sorted(rows, key=lambda r: int(r[0]) * 1000, end_ms=end_ms)


def fetch_kraken_spot_ohlc(transport: Transport, pair: str, start_ms: int, end_ms: int) -> list[list[Any]]:
    # Kraken's public OHLC endpoint returns at most the last 720 candles
    # regardless of `since` — a hard venue history limit recorded as such.
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440"
    payload = _get(transport, url)
    if payload.get("error"):
        raise Data1Error(f"kraken_spot_ohlc_error:{payload['error']}")
    result = payload.get("result") or {}
    series_keys = [k for k in result if k != "last"]
    if len(series_keys) != 1:
        raise Data1Error(f"kraken_spot_ohlc_unexpected_result_keys:{sorted(result)}")
    rows = result[series_keys[0]]
    return _dedupe_sorted(rows, key=lambda r: int(r[0]) * 1000, end_ms=end_ms)


def fetch_kraken_futures_funding(transport: Transport, symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    # Single unpaginated endpoint; observed to return a trailing ~1y window.
    url = f"https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol={symbol}"
    payload = _get(transport, url)
    if payload.get("result") != "success":
        raise Data1Error(f"kraken_futures_funding_error:{payload.get('result')}")
    rows = payload.get("rates") or []
    return _dedupe_sorted(
        rows, key=lambda r: int(_parse_iso(_clean_kf_ts(r["timestamp"])).timestamp() * 1000), end_ms=end_ms
    )


def fetch_kraken_futures_candles(transport: Transport, symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    url = (
        f"https://futures.kraken.com/api/charts/v1/trade/{symbol}/1d"
        f"?from={start_ms // 1000}&to={end_ms // 1000}"
    )
    payload = _get(transport, url)
    rows = payload.get("candles") or []
    return _dedupe_sorted(rows, key=lambda r: int(r["time"]), end_ms=end_ms)


def fetch_hyperliquid_funding(transport: Transport, coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        page = _post(
            transport,
            HYPERLIQUID_INFO_URL,
            {"type": "fundingHistory", "coin": coin, "startTime": cursor, "endTime": end_ms},
        )
        if not page:
            break
        rows.extend(page)
        last = int(page[-1]["time"])
        if len(page) < 500:
            break
        cursor = last + 1
    return _dedupe_sorted(rows, key=lambda r: int(r["time"]), end_ms=end_ms)


def fetch_hyperliquid_candles(transport: Transport, coin_or_pair: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    payload = _post(
        transport,
        HYPERLIQUID_INFO_URL,
        {
            "type": "candleSnapshot",
            "req": {"coin": coin_or_pair, "interval": "1d", "startTime": start_ms, "endTime": end_ms + DAY_MS},
        },
    )
    return _dedupe_sorted(payload or [], key=lambda r: int(r["t"]), end_ms=end_ms)


def _clean_kf_ts(text: str) -> str:
    # Kraken Futures timestamps may carry fractional seconds; normalize.
    if "." in text:
        head, _, _ = text.partition(".")
        return head + "Z"
    return text


def _dedupe_sorted(rows: Iterable[Any], *, key: Callable[[Any], int], end_ms: int) -> list[Any]:
    """Deduplicate on the native timestamp, sort oldest-first, clamp to end.

    The clamp drops events/candles at-or-after the window end (the window end
    is the close of the last fully closed UTC day) — in-progress data never
    enters the dataset. Nothing is filled in; this only ever DROPS rows.
    """
    seen: set[int] = set()
    out: list[Any] = []
    for row in rows:
        ts = key(row)
        if ts in seen or ts >= end_ms:
            continue
        seen.add(ts)
        out.append(row)
    out.sort(key=key)
    return out


FETCH_DISPATCH: dict[tuple[str, str], Callable[[Transport, str, int, int], list[Any]]] = {
    ("hyperliquid", "funding"): fetch_hyperliquid_funding,
    ("hyperliquid", "perp_1d"): fetch_hyperliquid_candles,
    ("hyperliquid", "spot_1d"): fetch_hyperliquid_candles,
    ("binance", "funding"): fetch_binance_funding,
    ("binance", "perp_1d"): lambda t, s, a, b: fetch_binance_klines(t, s, a, b, market="perp"),
    ("binance", "spot_1d"): lambda t, s, a, b: fetch_binance_klines(t, s, a, b, market="spot"),
    ("bybit", "funding"): fetch_bybit_funding,
    ("bybit", "perp_1d"): lambda t, s, a, b: fetch_bybit_klines(t, s, a, b, market="perp"),
    ("bybit", "spot_1d"): lambda t, s, a, b: fetch_bybit_klines(t, s, a, b, market="spot"),
    ("okx", "funding"): fetch_okx_funding,
    ("okx", "perp_1d"): fetch_okx_candles,
    ("okx", "spot_1d"): fetch_okx_candles,
    ("coinbase", "spot_1d"): fetch_coinbase_candles,
    ("kraken", "funding"): fetch_kraken_futures_funding,
    ("kraken", "perp_1d"): fetch_kraken_futures_candles,
    ("kraken", "spot_1d"): fetch_kraken_spot_ohlc,
}


# ---------------------------------------------------------------------------
# Normalizers: venue-native rows -> canonical rows. Strict, no repair.
# ---------------------------------------------------------------------------


def _require_midnight(ms: int, venue: str, context: str) -> datetime:
    moment = datetime.fromtimestamp(ms / 1000, UTC)
    if (moment.hour, moment.minute, moment.second, moment.microsecond) != (0, 0, 0, 0):
        raise Data1AlignmentError(f"non_midnight_daily_candle:{venue}:{context}:{moment.isoformat()}")
    return moment


def _candle(venue: str, open_ms: int, o: Any, h: Any, l: Any, c: Any, v: Any) -> dict[str, Any]:  # noqa: E741
    open_time = _require_midnight(open_ms, venue, "open_time")
    close_time = open_time + timedelta(days=1)
    return {
        "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "close_time": close_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open": str(o),
        "high": str(h),
        "low": str(l),
        "close": str(c),
        "volume_base": str(v),
    }


def normalize_funding(venue: str, rows: Sequence[Any]) -> list[dict[str, str]]:
    """Canonical funding events: {time_utc, rate} oldest-first.

    Rates stay venue-native per-interval fractions (positive = longs pay
    shorts on all five funding venues); they are summed, never rescaled.
    For Kraken Futures the price-relative ``relativeFundingRate`` is the
    comparable per-interval fraction (``fundingRate`` there is absolute USD).
    """
    out: list[dict[str, str]] = []
    for row in rows:
        if venue == "hyperliquid":
            out.append({"time_utc": _iso(int(row["time"])), "rate": str(row["fundingRate"])})
        elif venue == "binance":
            out.append({"time_utc": _iso(int(row["fundingTime"])), "rate": str(row["fundingRate"])})
        elif venue == "bybit":
            out.append({"time_utc": _iso(int(row["fundingRateTimestamp"])), "rate": str(row["fundingRate"])})
        elif venue == "okx":
            out.append({"time_utc": _iso(int(row["fundingTime"])), "rate": str(row["fundingRate"])})
        elif venue == "kraken":
            out.append({"time_utc": _clean_kf_ts(str(row["timestamp"])), "rate": str(row["relativeFundingRate"])})
        else:
            raise Data1Error(f"no_funding_normalizer_for_venue:{venue}")
    out.sort(key=lambda r: r["time_utc"])
    return out


def normalize_daily_candles(venue: str, series: str, rows: Sequence[Any]) -> list[dict[str, Any]]:
    """Canonical daily candles, midnight-UTC enforced, oldest-first."""
    out: list[dict[str, Any]] = []
    for row in rows:
        if venue == "hyperliquid":
            out.append(_candle(venue, int(row["t"]), row["o"], row["h"], row["l"], row["c"], row["v"]))
        elif venue in ("binance", "bybit"):
            out.append(_candle(venue, int(row[0]), row[1], row[2], row[3], row[4], row[5]))
        elif venue == "okx":
            # [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]; base volume
            # is volCcy for SWAP contracts and vol for spot instruments.
            base_vol = row[6] if series == "perp_1d" else row[5]
            out.append(_candle(venue, int(row[0]), row[1], row[2], row[3], row[4], base_vol))
        elif venue == "coinbase":
            # [time_s, low, high, open, close, volume] — note the order.
            out.append(_candle(venue, int(row[0]) * 1000, row[3], row[2], row[1], row[4], row[5]))
        elif venue == "kraken" and series == "spot_1d":
            # [time_s, open, high, low, close, vwap, volume, count]
            out.append(_candle(venue, int(row[0]) * 1000, row[1], row[2], row[3], row[4], row[6]))
        elif venue == "kraken" and series == "perp_1d":
            out.append(
                _candle(venue, int(row["time"]), row["open"], row["high"], row["low"], row["close"], row["volume"])
            )
        else:
            raise Data1Error(f"no_candle_normalizer_for_venue:{venue}:{series}")
    out.sort(key=lambda r: r["open_time"])
    return out


# ---------------------------------------------------------------------------
# Funding interval observation + daily aggregation (FUND-EV1 convention).
# ---------------------------------------------------------------------------


def observed_funding_interval_hours(events: Sequence[Mapping[str, str]]) -> float | None:
    """Median spacing between consecutive funding events, in hours."""
    if len(events) < 3:
        return None
    times = [_parse_iso(e["time_utc"]) for e in events]
    deltas = [(b - a).total_seconds() / 3600.0 for a, b in itertools.pairwise(times)]
    return round(statistics.median(deltas), 4)


def daily_funding_sums(events: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    """Sum per-interval funding rates into daily slots keyed by close time.

    The slot closing at day D 00:00Z sums events with time in
    [D-1 00:00Z, D 00:00Z) — the funding paid during that daily candle —
    matching the committed FUND-EV1 convention exactly. Exact Decimal sums;
    ``events`` carries the per-day event count so partially covered days are
    visible (they are reported, never scaled up or filled).
    """
    buckets: dict[str, tuple[Decimal, int]] = {}
    for event in events:
        moment = _parse_iso(event["time_utc"])
        slot_close = moment.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        key = slot_close.strftime("%Y-%m-%dT%H:%M:%SZ")
        total, count = buckets.get(key, (Decimal("0"), 0))
        buckets[key] = (total + Decimal(str(event["rate"])), count + 1)
    return [
        {"close_time": key, "funding_rate_sum": str(total), "events": count}
        for key, (total, count) in sorted(buckets.items())
    ]


# ---------------------------------------------------------------------------
# Coverage (per series) and cross-venue alignment. Gaps stay gaps.
# ---------------------------------------------------------------------------


def _close_times(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [str(r["close_time"]) for r in rows]


def series_coverage(close_times: Sequence[str]) -> dict[str, Any]:
    """First/last close, row count, and INTERNAL missing days (reported)."""
    if not close_times:
        return {"first_close": None, "last_close": None, "rows": 0, "expected_days": 0, "missing_internal_days": 0}
    first, last = close_times[0], close_times[-1]
    expected = int((_parse_iso(last) - _parse_iso(first)).total_seconds() // 86400) + 1
    missing = expected - len(set(close_times))
    return {
        "first_close": first,
        "last_close": last,
        "rows": len(close_times),
        "expected_days": expected,
        "missing_internal_days": missing,
    }


def volume_coverage(candles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Zero-volume accounting for candle series.

    Some venues backfill price history from before their own market existed
    (probe-verified: Hyperliquid serves daily perp candles back to 2020-08
    with volume 0 — real HL trading starts 2023-02-26). Zero-volume rows are
    venue-published price marks, not traded candles; they are KEPT (the venue
    really serves them) but counted here so no consumer mistakes backfill for
    market history.
    """
    zero_rows = sum(1 for c in candles if float(c["volume_base"]) == 0.0)
    first_traded = next((str(c["close_time"]) for c in candles if float(c["volume_base"]) > 0.0), None)
    return {"zero_volume_rows": zero_rows, "first_nonzero_volume_close": first_traded}


def aligned_daily_view(
    per_venue_rows: Mapping[str, Sequence[Mapping[str, Any]]], value_key: str
) -> dict[str, Any]:
    """Union-calendar alignment across venues for one asset/series.

    The calendar is the UNION of every venue's daily close timestamps —
    differing listing dates and venue gaps appear as explicit ``None`` holes.
    No forward-fill, no interpolation, no truncation to the intersection.
    """
    calendar = sorted({str(r["close_time"]) for rows in per_venue_rows.values() for r in rows})
    venues_out: dict[str, list[str | None]] = {}
    for venue, rows in per_venue_rows.items():
        by_close = {str(r["close_time"]): str(r[value_key]) for r in rows}
        venues_out[venue] = [by_close.get(ts) for ts in calendar]
    return {"close_times": calendar, "venues": venues_out}


# ---------------------------------------------------------------------------
# Snapshot artifacts + provenance
# ---------------------------------------------------------------------------


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_filename(venue: str, asset: str, series: str) -> str:
    return f"{venue}_{asset.lower()}_{series}_data1.json"


def write_series_artifact(
    snapshot_dir: Path,
    ref: MarketRef,
    native_rows: Sequence[Any],
    *,
    endpoint: str,
    fetched_at_utc: str,
) -> Path:
    """Write the deduped venue-native rows as the ignored local artifact."""
    path = snapshot_dir / artifact_filename(ref.venue, ref.asset, ref.series)
    payload = {
        "phase": PHASE,
        "venue": ref.venue,
        "asset": ref.asset,
        "series": ref.series,
        "venue_symbol": ref.venue_symbol,
        "endpoint": endpoint,
        "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        "fetched_at_utc": fetched_at_utc,
        "rows": list(native_rows),
    }
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Loader — what the strategy phases consume.
# ---------------------------------------------------------------------------

DEFAULT_SUMMARY_PATH = Path("docs/data1_multi_venue_snapshot_summary.json")
DEFAULT_SNAPSHOT_DIR = Path("/tmp/money-flow-data1/raw_series")


@dataclass(frozen=True)
class SeriesData:
    venue: str
    asset: str
    series: str
    status: str  # ok | venue_lacks_market | fetch_failed | artifact_missing_rerun_fetch_script
    venue_symbol: str | None
    note: str
    rows: tuple[dict[str, Any], ...] = ()
    daily_funding: tuple[dict[str, Any], ...] = ()  # funding series only
    coverage: dict[str, Any] = field(default_factory=dict)
    funding_interval_hours_declared: float | None = None
    funding_interval_hours_observed: float | None = None


@dataclass(frozen=True)
class VenueAssetData:
    venue: str
    asset: str
    funding: SeriesData
    perp_1d: SeriesData
    spot_1d: SeriesData


class MultiVenueDataset:
    """Read-only access to the DATA1 snapshot, coverage flags included.

    Loads the committed provenance summary, then materializes each series
    from its ignored local artifact, verifying sha256 (tampered or stale
    artifacts raise ``Data1IntegrityError``; absent artifacts surface as
    ``artifact_missing_rerun_fetch_script`` — they are never fabricated).
    """

    def __init__(self, summary: Mapping[str, Any], series: Mapping[tuple[str, str, str], SeriesData]):
        self._summary = dict(summary)
        self._series = dict(series)

    @property
    def as_of_utc(self) -> str:
        return str(self._summary["window"]["end_utc"])

    @property
    def fetched_at_utc(self) -> str:
        return str(self._summary["fetched_at_utc"])

    @property
    def summary(self) -> dict[str, Any]:
        return dict(self._summary)

    def series(self, venue: str, asset: str, series: str) -> SeriesData:
        try:
            return self._series[(venue, asset, series)]
        except KeyError as exc:
            raise Data1Error(f"unknown_series:{venue}:{asset}:{series}") from exc

    def get(self, venue: str, asset: str) -> VenueAssetData:
        return VenueAssetData(
            venue=venue,
            asset=asset,
            funding=self.series(venue, asset, "funding"),
            perp_1d=self.series(venue, asset, "perp_1d"),
            spot_1d=self.series(venue, asset, "spot_1d"),
        )

    def coverage_table(self) -> list[dict[str, Any]]:
        rows = []
        for (venue, asset, series_key), data in sorted(self._series.items()):
            rows.append(
                {
                    "venue": venue,
                    "asset": asset,
                    "series": series_key,
                    "status": data.status,
                    "venue_symbol": data.venue_symbol,
                    **data.coverage,
                    "funding_interval_hours_observed": data.funding_interval_hours_observed,
                    "note": data.note,
                }
            )
        return rows

    def aligned_daily(self, asset: str, *, series: str, value_key: str | None = None) -> dict[str, Any]:
        """Union-calendar aligned view of one asset across loaded venues."""
        loaded = [
            data
            for (venue, a, s), data in sorted(self._series.items())
            if a == asset and s == series and data.status == STATUS_OK
        ]
        if series == "funding":
            per_venue = {data.venue: list(data.daily_funding) for data in loaded}
            return aligned_daily_view(per_venue, value_key or "funding_rate_sum")
        per_venue = {data.venue: list(data.rows) for data in loaded}
        return aligned_daily_view(per_venue, value_key or "close")


def _series_from_artifact(
    block: Mapping[str, Any], ref_meta: Mapping[str, Any], snapshot_dir: Path, *, verify_sha256: bool
) -> SeriesData:
    venue = str(ref_meta["venue"])
    asset = str(ref_meta["asset"])
    series_key = str(ref_meta["series"])
    base = {
        "venue": venue,
        "asset": asset,
        "series": series_key,
        "venue_symbol": ref_meta.get("venue_symbol"),
        "note": str(block.get("note") or ""),
        "coverage": dict(block.get("coverage") or {}),
        "funding_interval_hours_declared": DECLARED_FUNDING_INTERVAL_HOURS.get(venue),
        "funding_interval_hours_observed": block.get("funding_interval_hours_observed"),
    }
    status = str(block.get("status"))
    if status != STATUS_OK:
        return SeriesData(status=status, **base)
    path = snapshot_dir / artifact_filename(venue, asset, series_key)
    if not path.exists():
        return SeriesData(status=STATUS_ARTIFACT_MISSING, **base)
    if verify_sha256 and sha256_of(path) != block.get("raw_sha256"):
        raise Data1IntegrityError(f"artifact_sha256_mismatch:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    native_rows = payload.get("rows") or []
    if series_key == "funding":
        events = normalize_funding(venue, native_rows)
        return SeriesData(
            status=STATUS_OK,
            rows=tuple(events),
            daily_funding=tuple(daily_funding_sums(events)),
            **base,
        )
    candles = normalize_daily_candles(venue, series_key, native_rows)
    return SeriesData(status=STATUS_OK, rows=tuple(candles), **base)


def load_data1_dataset(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    snapshot_dir: Path | None = None,
    *,
    verify_sha256: bool = True,
) -> MultiVenueDataset:
    """Load the DATA1 multi-venue dataset for strategy-phase consumption."""
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    resolved_dir = Path(snapshot_dir) if snapshot_dir is not None else Path(summary["snapshot_dir"])
    series: dict[tuple[str, str, str], SeriesData] = {}
    for block in summary["series"]:
        ref_meta = {
            "venue": block["venue"],
            "asset": block["asset"],
            "series": block["series"],
            "venue_symbol": block.get("venue_symbol"),
        }
        series[(block["venue"], block["asset"], block["series"])] = _series_from_artifact(
            block, ref_meta, resolved_dir, verify_sha256=verify_sha256
        )
    return MultiVenueDataset(summary, series)
