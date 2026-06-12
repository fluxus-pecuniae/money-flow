"""DATA1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - catalog: the full venue x asset x series grid exists with the documented
    venue gaps (OKX/Coinbase/Kraken BNB, Coinbase perp/funding, HL spot)
    recorded as ``venue_lacks_market`` — never silently absent;
  - endpoint hygiene: only allowlisted public market-data URLs can be
    fetched; no key/signing material exists in the module;
  - per-venue normalizers map the venue-native payload shapes exactly
    (Coinbase's [time, low, high, open, close, vol] order; OKX base-volume
    column differing between spot and swap; Kraken spot vs futures shapes);
  - alignment correctness: daily candles are accepted on exact midnight-UTC
    boundaries only (a UTC+8-aligned OKX bar is REFUSED, not mis-aligned),
    and the OKX fetcher requests ``bar=1Dutc`` and drops unconfirmed rows;
  - funding-interval handling: 1h and 8h venues aggregate to daily sums
    under the same FUND-EV1 close-time convention with exact Decimal sums;
    partial days are reported via event counts, never scaled or filled;
  - no silent gap-filling: union-calendar alignment leaves explicit None
    holes (listing-date offsets AND internal holes) and never truncates;
  - pagination: forward (Binance) and backward (Bybit) cursors collect all
    pages, deduplicate boundaries, and drop in-progress rows at the clamp;
  - provenance: artifacts round-trip through the loader; a tampered
    artifact raises Data1IntegrityError; a missing artifact surfaces as
    ``artifact_missing_rerun_fetch_script`` (never fabricated); venue-lacks
    blocks pass through; the loader exposes coverage flags and as-of;
  - the committed snapshot summary reconciles with the module's constants
    and its own internal gap accounting.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from services.market_data import data1_multi_venue as mv

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "data1_multi_venue_snapshot_summary.json"

# Midnight-UTC epoch anchors (ms) used across fixtures.
D08 = 1781049600000  # 2026-06-08T00:00:00Z
D09 = 1781136000000  # 2026-06-09T00:00:00Z
D10 = 1781222400000  # 2026-06-10T00:00:00Z
D11 = 1781308800000  # 2026-06-11T00:00:00Z
H8 = 8 * 3600 * 1000


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_catalog_covers_the_full_grid_with_explicit_gaps():
    catalog = mv.build_catalog()
    assert len(catalog) == len(mv.VENUES) * len(mv.ASSETS) * len(mv.SERIES_KEYS) == 126

    lacks = {key for key, ref in catalog.items() if ref.status == mv.STATUS_VENUE_LACKS}
    # OKX/Kraken list no BNB at all; Coinbase has no BNB spot and no perp/funding anywhere.
    for series in mv.SERIES_KEYS:
        assert ("okx", "BNB", series) in lacks
        assert ("kraken", "BNB", series) in lacks
    for asset in mv.ASSETS:
        assert ("coinbase", asset, "funding") in lacks
        assert ("coinbase", asset, "perp_1d") in lacks
    assert ("coinbase", "BNB", "spot_1d") in lacks
    # Hyperliquid spot exists only for BTC/ETH/SOL in this universe.
    for asset in ("XRP", "DOGE", "BNB", "AVAX"):
        assert ("hyperliquid", asset, "spot_1d") in lacks
    for asset in ("BTC", "ETH", "SOL"):
        assert catalog[("hyperliquid", asset, "spot_1d")].status == mv.STATUS_EXPECTED
    # Every gap carries a human-readable reason; every expected market a symbol.
    for key, ref in catalog.items():
        if ref.status == mv.STATUS_VENUE_LACKS:
            assert ref.note, key
            assert ref.venue_symbol is None
        else:
            assert ref.venue_symbol, key
    assert len(lacks) == 25
    # Every expected (venue, series) pair is fetchable and documented.
    for (venue, _asset, series), ref in catalog.items():
        if ref.status == mv.STATUS_EXPECTED:
            assert (venue, series) in mv.FETCH_DISPATCH
            assert (venue, series) in mv.ENDPOINT_TEMPLATES


# ---------------------------------------------------------------------------
# Endpoint hygiene
# ---------------------------------------------------------------------------


def test_only_allowlisted_public_endpoints_are_fetchable():
    with pytest.raises(mv.Data1Error, match="endpoint_not_in_public_allowlist"):
        mv._checked_url("https://api.evil.example/anything")
    for prefix in mv.PUBLIC_ENDPOINT_ALLOWLIST:
        assert prefix.startswith("https://")
        assert mv._checked_url(prefix) == prefix


def test_module_contains_no_key_or_signing_material():
    source = (REPO_ROOT / "services" / "market_data" / "data1_multi_venue.py").read_text(encoding="utf-8")
    for needle in ("apikey", "api_key", "api-key", "x-mbx", "privatekey", "secret", "hmac", "sign("):
        assert needle not in source.lower(), needle


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------


def test_candle_normalizers_map_each_venue_shape_exactly():
    binance = mv.normalize_daily_candles(
        "binance", "perp_1d", [[D09, "61483.60", "63915.30", "61480.00", "63487.50", "186822.444", D10 - 1, "q", 1, "t", "u", "0"]]
    )
    assert binance == [
        {
            "open_time": _iso(D09),
            "close_time": _iso(D10),
            "open": "61483.60",
            "high": "63915.30",
            "low": "61480.00",
            "close": "63487.50",
            "volume_base": "186822.444",
        }
    ]
    bybit = mv.normalize_daily_candles("bybit", "spot_1d", [[str(D09), "1", "2", "0.5", "1.5", "100", "150"]])
    assert bybit[0]["close"] == "1.5" and bybit[0]["volume_base"] == "100"
    # Coinbase order is [time_s, LOW, HIGH, OPEN, close, volume].
    coinbase = mv.normalize_daily_candles("coinbase", "spot_1d", [[D09 // 1000, 60.0, 64.0, 61.0, 63.0, 8919.2]])
    assert coinbase[0]["open"] == "61.0" and coinbase[0]["high"] == "64.0"
    assert coinbase[0]["low"] == "60.0" and coinbase[0]["close"] == "63.0"
    # OKX base volume: column 5 for spot, column 6 (volCcy) for swap contracts.
    okx_row = [str(D09), "62", "64", "61", "63", "3125566", "31255", "1976839629", "1"]
    assert mv.normalize_daily_candles("okx", "spot_1d", [okx_row])[0]["volume_base"] == "3125566"
    assert mv.normalize_daily_candles("okx", "perp_1d", [okx_row])[0]["volume_base"] == "31255"
    # Kraken spot arrays [time_s, o, h, l, c, vwap, VOLUME, count] vs futures dicts.
    kraken_spot = mv.normalize_daily_candles(
        "kraken", "spot_1d", [[D09 // 1000, "64833", "64999", "63335", "64087", "64028", "1178.24", 22945]]
    )
    assert kraken_spot[0]["volume_base"] == "1178.24" and kraken_spot[0]["close"] == "64087"
    kraken_perp = mv.normalize_daily_candles(
        "kraken", "perp_1d", [{"time": D09, "open": "89254", "high": "91799", "low": "87736", "close": "90421", "volume": "3497.95"}]
    )
    assert kraken_perp[0]["close"] == "90421"
    hl = mv.normalize_daily_candles(
        "hyperliquid", "perp_1d", [{"t": D09, "o": "61", "h": "64", "l": "60", "c": "63", "v": "5", "n": 9}]
    )
    assert hl[0]["close_time"] == _iso(D10)


def test_non_midnight_utc_daily_candle_is_refused_not_misaligned():
    # The default OKX 1D bar opens at 16:00Z (UTC+8 day) — the probe-verified
    # trap. The normalizer must refuse it rather than shift or accept it.
    utc8_open = D09 + 16 * 3600 * 1000
    row = [str(utc8_open), "62", "64", "61", "63", "1", "1", "1", "1"]
    with pytest.raises(mv.Data1AlignmentError, match="non_midnight_daily_candle"):
        mv.normalize_daily_candles("okx", "spot_1d", [row])


def test_funding_normalizers_pick_the_comparable_rate_field():
    binance = mv.normalize_funding("binance", [{"fundingTime": D09 + 4, "fundingRate": "0.0001", "markPrice": "1"}])
    assert binance == [{"time_utc": _iso(D09), "rate": "0.0001"}]  # ms jitter floors to the second
    bybit = mv.normalize_funding("bybit", [{"fundingRateTimestamp": str(D09), "fundingRate": "-0.0002"}])
    assert bybit[0]["rate"] == "-0.0002"
    okx = mv.normalize_funding("okx", [{"fundingTime": str(D09), "fundingRate": "0.00003", "realizedRate": "0.00003"}])
    assert okx[0]["time_utc"] == _iso(D09)
    # Kraken Futures: the price-relative rate is the comparable fraction; the
    # absolute USD fundingRate must NOT be used.
    kraken = mv.normalize_funding(
        "kraken", [{"timestamp": "2026-06-09T01:00:00.123Z", "fundingRate": 1.375, "relativeFundingRate": 1.25e-05}]
    )
    assert kraken == [{"time_utc": "2026-06-09T01:00:00Z", "rate": "1.25e-05"}]
    hl = mv.normalize_funding("hyperliquid", [{"coin": "BTC", "time": D09, "fundingRate": "0.0000125"}])
    assert hl[0]["rate"] == "0.0000125"


# ---------------------------------------------------------------------------
# Funding intervals + daily aggregation
# ---------------------------------------------------------------------------


def _events(times_ms: list[int], rate: str = "0.0001") -> list[dict[str, str]]:
    return [{"time_utc": _iso(t), "rate": rate} for t in times_ms]


def test_observed_interval_distinguishes_1h_from_8h_venues():
    hourly = _events([D09 + i * 3600 * 1000 for i in range(24)])
    eight = _events([D09 + i * H8 for i in range(9)])
    assert mv.observed_funding_interval_hours(hourly) == 1.0
    assert mv.observed_funding_interval_hours(eight) == 8.0
    assert mv.observed_funding_interval_hours(eight[:2]) is None  # too few to claim


def test_daily_funding_sums_use_the_fund_ev1_close_convention_exactly():
    # Three 8h events inside [D09, D10) -> slot CLOSING at D10; exact Decimal sum.
    events = _events([D09, D09 + H8, D09 + 2 * H8], rate="0.0001")
    daily = mv.daily_funding_sums(events)
    assert daily == [{"close_time": _iso(D10), "funding_rate_sum": "0.0003", "events": 3}]
    # 24 hourly events sum exactly without float drift.
    hourly = mv.daily_funding_sums(_events([D09 + i * 3600 * 1000 for i in range(24)], rate="0.0000125"))
    assert hourly == [{"close_time": _iso(D10), "funding_rate_sum": "0.0003000", "events": 24}]


def test_partial_funding_days_are_reported_never_scaled_or_filled():
    # Venue outage: only 2 of 3 8h events on D09 — the sum is the sum of the
    # two REAL events and the event count exposes the partial day.
    events = _events([D09, D09 + H8], rate="0.0001") + _events([D10, D10 + H8, D10 + 2 * H8], rate="0.0001")
    daily = mv.daily_funding_sums(events)
    assert daily[0] == {"close_time": _iso(D10), "funding_rate_sum": "0.0002", "events": 2}
    assert daily[1]["events"] == 3


# ---------------------------------------------------------------------------
# Alignment + coverage: gaps stay gaps
# ---------------------------------------------------------------------------


def test_union_alignment_keeps_listing_offsets_and_holes_explicit():
    venue_a = [  # listed early, full coverage
        {"close_time": _iso(D08), "close": "1"},
        {"close_time": _iso(D09), "close": "2"},
        {"close_time": _iso(D10), "close": "3"},
        {"close_time": _iso(D11), "close": "4"},
    ]
    venue_b = [  # listed later AND has an internal hole at D10
        {"close_time": _iso(D09), "close": "20"},
        {"close_time": _iso(D11), "close": "40"},
    ]
    view = mv.aligned_daily_view({"a": venue_a, "b": venue_b}, "close")
    assert view["close_times"] == [_iso(D08), _iso(D09), _iso(D10), _iso(D11)]
    assert view["venues"]["a"] == ["1", "2", "3", "4"]  # never truncated to b's window
    assert view["venues"]["b"] == [None, "20", None, "40"]  # explicit None, no forward-fill


def test_zero_volume_backfill_is_counted_never_mistaken_for_trading():
    # Probe-verified HL behavior: daily perp candles pre-dating the venue's
    # own launch arrive with volume 0. They are kept (the venue serves them)
    # but counted, and the first REAL traded candle is identified.
    candles = [
        {"close_time": _iso(D08), "volume_base": "0.0"},
        {"close_time": _iso(D09), "volume_base": "0"},
        {"close_time": _iso(D10), "volume_base": "10.7"},
        {"close_time": _iso(D11), "volume_base": "12.1"},
    ]
    assert mv.volume_coverage(candles) == {"zero_volume_rows": 2, "first_nonzero_volume_close": _iso(D10)}
    assert mv.volume_coverage([]) == {"zero_volume_rows": 0, "first_nonzero_volume_close": None}


def test_series_coverage_counts_internal_missing_days():
    closes = [_iso(D08), _iso(D09), _iso(D11)]  # D10 missing inside the range
    cov = mv.series_coverage(closes)
    assert cov["rows"] == 3 and cov["expected_days"] == 4 and cov["missing_internal_days"] == 1
    assert mv.series_coverage([]) == {
        "first_close": None,
        "last_close": None,
        "rows": 0,
        "expected_days": 0,
        "missing_internal_days": 0,
    }


def test_clamp_drops_in_progress_rows_and_duplicates_only():
    rows = [{"t": D09}, {"t": D09}, {"t": D10}, {"t": D11}]  # D11 = in-progress at end=D11
    out = mv._dedupe_sorted(rows, key=lambda r: int(r["t"]), end_ms=D11)
    assert [r["t"] for r in out] == [D09, D10]


# ---------------------------------------------------------------------------
# Pagination (fake transports)
# ---------------------------------------------------------------------------


def test_binance_forward_pagination_collects_all_pages():
    pages = {
        0: [{"fundingTime": D08 + i * H8, "fundingRate": "0.0001"} for i in range(1000)],
        1: [{"fundingTime": D08 + 1000 * H8, "fundingRate": "0.0002"}],
    }
    calls: list[str] = []

    def transport(method, url, body):
        calls.append(url)
        return pages[len(calls) - 1]

    end_ms = D08 + 2000 * H8
    rows = mv.fetch_binance_funding(transport, "BTCUSDT", D08, end_ms)
    assert len(rows) == 1001
    assert "startTime=" + str(D08) in calls[0]
    assert "startTime=" + str(D08 + 999 * H8 + 1) in calls[1]  # cursor = last ts + 1
    assert rows == sorted(rows, key=lambda r: r["fundingTime"])


def test_bybit_backward_pagination_dedupes_and_stops_at_start():
    newest = [{"fundingRateTimestamp": str(D08 + i * H8), "fundingRate": "0.0001"} for i in range(250)]
    page1 = list(reversed(newest[50:250]))  # newest-first, 200 rows
    page2 = list(reversed(newest[0:50]))

    calls: list[str] = []

    def transport(method, url, body):
        calls.append(url)
        return {"result": {"list": page1 if len(calls) == 1 else page2}}

    rows = mv.fetch_bybit_funding(transport, "BTCUSDT", D08 - 1, D08 + 251 * H8)
    assert len(rows) == 250 and len(calls) == 2
    assert int(rows[0]["fundingRateTimestamp"]) == D08


def test_okx_fetcher_requires_utc_bar_and_drops_unconfirmed_candles():
    closed = [str(D09), "62", "64", "61", "63", "1", "1", "1", "1"]
    in_progress = [str(D10), "63", "65", "62", "64", "1", "1", "1", "0"]
    captured: list[str] = []

    def transport(method, url, body):
        captured.append(url)
        return {"data": [in_progress, closed]}

    rows = mv.fetch_okx_candles(transport, "BTC-USDT", D08, D11)
    assert "bar=1Dutc" in captured[0]
    assert rows == [closed]  # confirm=0 dropped, never half-included


# ---------------------------------------------------------------------------
# Artifacts + loader round trip
# ---------------------------------------------------------------------------


def _write_snapshot(tmp_path: Path) -> Path:
    snapshot_dir = tmp_path / "raw_series"
    snapshot_dir.mkdir()
    catalog = mv.build_catalog()
    blocks = []

    def add_ok(venue: str, asset: str, series: str, native_rows, extra=None):
        ref = catalog[(venue, asset, series)]
        path = mv.write_series_artifact(
            snapshot_dir, ref, native_rows, endpoint=mv.ENDPOINT_TEMPLATES[(venue, series)], fetched_at_utc="2026-06-11T12:00:00Z"
        )
        block = {
            "venue": venue,
            "asset": asset,
            "series": series,
            "venue_symbol": ref.venue_symbol,
            "status": mv.STATUS_OK,
            "note": "",
            "raw_sha256": mv.sha256_of(path),
            "coverage": {},
            **(extra or {}),
        }
        blocks.append(block)

    add_ok(
        "kraken",
        "BTC",
        "funding",
        [{"timestamp": _iso(D09 + i * 3600 * 1000), "fundingRate": 1.0, "relativeFundingRate": 1e-05} for i in range(24)],
        {"funding_interval_hours_observed": 1.0},
    )
    add_ok("binance", "BTC", "perp_1d", [[D09, "61", "64", "60", "63", "100", D10 - 1, "q", 1, "t", "u", "0"]])
    add_ok("coinbase", "BTC", "spot_1d", [[D09 // 1000, 60.0, 64.0, 61.0, 63.0, 10.0]])
    blocks.append(
        {
            "venue": "okx",
            "asset": "BNB",
            "series": "spot_1d",
            "venue_symbol": None,
            "status": mv.STATUS_VENUE_LACKS,
            "note": "OKX does not list BNB",
        }
    )
    blocks.append(
        {
            "venue": "bybit",
            "asset": "BTC",
            "series": "spot_1d",
            "venue_symbol": "BTCUSDT",
            "status": mv.STATUS_FETCH_FAILED,
            "note": "fetch failed; gap reported, never substituted: HTTP 503",
            "error": "HTTPError: 503",
        }
    )
    summary = {
        "phase": mv.PHASE,
        "fetched_at_utc": "2026-06-11T12:00:00Z",
        "snapshot_dir": str(snapshot_dir),
        "window": {"end_utc": _iso(D11)},
        "series": blocks,
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def test_loader_roundtrip_exposes_series_coverage_and_as_of(tmp_path):
    ds = mv.load_data1_dataset(_write_snapshot(tmp_path))
    assert ds.as_of_utc == _iso(D11)
    funding = ds.series("kraken", "BTC", "funding")
    assert funding.status == mv.STATUS_OK
    assert funding.daily_funding == ({"close_time": _iso(D10), "funding_rate_sum": "0.00024", "events": 24},)
    assert funding.funding_interval_hours_declared == 1.0
    perp = ds.series("binance", "BTC", "perp_1d")
    assert perp.rows[0]["close"] == "63" and perp.rows[0]["close_time"] == _iso(D10)
    view = ds.aligned_daily("BTC", series="spot_1d")
    assert view["venues"] == {"coinbase": ["63.0"]}  # bybit failed -> excluded from aligned, not faked
    lacks = ds.series("okx", "BNB", "spot_1d")
    assert lacks.status == mv.STATUS_VENUE_LACKS and lacks.rows == ()
    failed = ds.series("bybit", "BTC", "spot_1d")
    assert failed.status == mv.STATUS_FETCH_FAILED and "never substituted" in failed.note
    table = ds.coverage_table()
    assert {r["status"] for r in table} == {mv.STATUS_OK, mv.STATUS_VENUE_LACKS, mv.STATUS_FETCH_FAILED}


def test_loader_refuses_tampered_artifacts(tmp_path):
    summary_path = _write_snapshot(tmp_path)
    artifact = tmp_path / "raw_series" / mv.artifact_filename("kraken", "BTC", "funding")
    artifact.write_text(artifact.read_text(encoding="utf-8").replace("1e-05", "9e-05"), encoding="utf-8")
    with pytest.raises(mv.Data1IntegrityError, match="artifact_sha256_mismatch"):
        mv.load_data1_dataset(summary_path)


def test_loader_reports_missing_artifacts_never_fabricates(tmp_path):
    summary_path = _write_snapshot(tmp_path)
    (tmp_path / "raw_series" / mv.artifact_filename("binance", "BTC", "perp_1d")).unlink()
    ds = mv.load_data1_dataset(summary_path)
    missing = ds.series("binance", "BTC", "perp_1d")
    assert missing.status == mv.STATUS_ARTIFACT_MISSING
    assert missing.rows == ()


# ---------------------------------------------------------------------------
# Committed summary reconciliation
# ---------------------------------------------------------------------------


def test_committed_summary_reconciles_with_module_truth():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["phase"] == mv.PHASE
    assert summary["boundaries"] == mv.BOUNDARIES
    assert summary["boundaries"]["public_read_only"] is True
    assert summary["boundaries"]["calls_private_signed_or_order_endpoints"] is False
    assert summary["provenance"]["funding_interval_hours_declared"] == {
        k: v for k, v in mv.DECLARED_FUNDING_INTERVAL_HOURS.items()
    }
    assert set(summary["universe"]["assets"]) == set(mv.ASSETS)
    assert set(summary["universe"]["venues"]) == set(mv.VENUES)
    # Per-series accounting: ok rows carry sha256 + coverage + history depth;
    # the gap list is exactly the non-ok rows (honesty: gaps are first-class).
    statuses = {}
    for block in summary["series"]:
        statuses[(block["venue"], block["asset"], block["series"])] = block["status"]
        if block["status"] == mv.STATUS_OK:
            assert len(block["raw_sha256"]) == 64
            assert block["coverage"]["rows"] > 0
            assert block["coverage"]["first_close"] <= block["coverage"]["last_close"]
            if block["series"] == "funding":
                assert block["funding_interval_hours_observed"] is not None
        else:
            assert block["note"]
    gap_keys = {(b["venue"], b["asset"], b["series"]) for b in summary["coverage_gaps"]}
    assert gap_keys == {k for k, s in statuses.items() if s != mv.STATUS_OK}
    # Catalog-declared venue gaps must appear as venue_lacks in the summary.
    for key, ref in mv.build_catalog().items():
        assert key in statuses
        if ref.status == mv.STATUS_VENUE_LACKS:
            assert statuses[key] == mv.STATUS_VENUE_LACKS
    # Funding intervals observed must reconcile with the declared per-venue
    # interval where the venue declares one (drift would be a finding).
    for block in summary["series"]:
        if block["status"] == mv.STATUS_OK and block["series"] == "funding":
            declared = mv.DECLARED_FUNDING_INTERVAL_HOURS[block["venue"]]
            observed = block["funding_interval_hours_observed"]
            assert declared is not None
            assert abs(observed - declared) / declared < 0.25, (block["venue"], observed, declared)
