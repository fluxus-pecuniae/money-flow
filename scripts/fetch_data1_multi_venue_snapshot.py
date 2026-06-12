#!/usr/bin/env python3
"""DATA1 — one-shot public read-only multi-venue market & funding snapshot.

Fetches, for the DATA1 multi-venue data foundation, per venue x asset x
series (perp funding history / perp daily candles / spot daily candles) for
BTC ETH SOL XRP DOGE BNB AVAX across hyperliquid, binance, bybit, okx,
coinbase, kraken — at the longest history each venue's PUBLIC API allows.

PUBLIC READ-ONLY ONLY: every request goes to an unauthenticated public
market-data endpoint in ``data1_multi_venue.PUBLIC_ENDPOINT_ALLOWLIST``. No
private, signed, account, or order endpoint exists in this script; no API
keys are read; nothing is submitted. Data ingestion for research only — no
strategy logic, no runtime change.

Outputs (FUND-EV1 snapshot conventions):
  - Raw per-venue native payload rows -> ignored local artifacts under
    /tmp/money-flow-data1/raw_series/ (documented, NOT committed).
  - A committed provenance summary -> docs/data1_multi_venue_snapshot_summary.json
    with the window, per-series endpoint, row counts, history depth, funding
    intervals (declared + observed), coverage gaps (venue lacks / fetch
    failed — reported, never substituted), sha256 of every artifact, an
    alignment overview, and small audit samples.

Consume via ``services.market_data.data1_multi_venue.load_data1_dataset``.

Run locally:
    .venv/bin/python scripts/fetch_data1_multi_venue_snapshot.py
Resume after an interruption without refetching finished series:
    .venv/bin/python scripts/fetch_data1_multi_venue_snapshot.py --reuse-artifacts
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _load_module(relative: str, alias: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


mv = _load_module("services/market_data/data1_multi_venue.py", "data1_multi_venue_fetch_module")

DEFAULT_SNAPSHOT_DIR = Path("/tmp/money-flow-data1/raw_series")
DEFAULT_SUMMARY_OUTPUT = Path("docs/data1_multi_venue_snapshot_summary.json")

CANDLES_START_FLOOR = datetime(2015, 1, 1, tzinfo=UTC)
FUNDING_START_FLOOR = datetime(2019, 1, 1, tzinfo=UTC)

MAX_RETRIES = 6
RETRYABLE_HTTP = {418, 429, 500, 502, 503, 504}


def make_transport() -> Any:
    """Real HTTP transport: paced, retrying, public-allowlist-checked URLs only."""

    def transport(method: str, url: str, body: dict[str, Any] | None) -> Any:
        pause = 1.0 if "hyperliquid" in url else 0.35
        for attempt in range(MAX_RETRIES):
            time.sleep(pause if attempt == 0 else min(60.0, 2.0 * (2**attempt)))
            try:
                if method == "POST":
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(body).encode("utf-8"),
                        headers={"Content-Type": "application/json", "User-Agent": "money-flow-data1/0.1"},
                    )
                else:
                    req = urllib.request.Request(url, headers={"User-Agent": "money-flow-data1/0.1"})
                with urllib.request.urlopen(req, timeout=60) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as exc:
                if exc.code in RETRYABLE_HTTP and attempt < MAX_RETRIES - 1:
                    print(f"    HTTP {exc.code}; retrying ({attempt + 1}/{MAX_RETRIES})")
                    continue
                raise
            except urllib.error.URLError as exc:
                if attempt < MAX_RETRIES - 1:
                    print(f"    transport error {exc.reason}; retrying ({attempt + 1}/{MAX_RETRIES})")
                    continue
                raise
        raise RuntimeError("unreachable")

    return transport


def fetch_one(
    transport: Any,
    ref: Any,
    *,
    end_ms: int,
    snapshot_dir: Path,
    fetched_at: str,
    reuse_artifacts: bool,
) -> tuple[list[Any], Path]:
    path = snapshot_dir / mv.artifact_filename(ref.venue, ref.asset, ref.series)
    if reuse_artifacts and path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(f"  reusing artifact ({len(payload['rows'])} rows)")
        return payload["rows"], path
    start_floor = FUNDING_START_FLOOR if ref.series == "funding" else CANDLES_START_FLOOR
    start_ms = int(start_floor.timestamp() * 1000)
    fetcher = mv.FETCH_DISPATCH[(ref.venue, ref.series)]
    rows = fetcher(transport, ref.venue_symbol, start_ms, end_ms)
    path = mv.write_series_artifact(
        snapshot_dir,
        ref,
        rows,
        endpoint=mv.ENDPOINT_TEMPLATES[(ref.venue, ref.series)],
        fetched_at_utc=fetched_at,
    )
    return rows, path


def build_series_block(ref: Any, *, status: str, note: str = "", error: str | None = None) -> dict[str, Any]:
    return {
        "venue": ref.venue,
        "asset": ref.asset,
        "series": ref.series,
        "venue_symbol": ref.venue_symbol,
        "status": status,
        "note": note or ref.note,
        "error": error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--venues", nargs="*", default=list(mv.VENUES))
    parser.add_argument("--assets", nargs="*", default=list(mv.ASSETS))
    parser.add_argument(
        "--reuse-artifacts",
        action="store_true",
        help="reuse existing raw artifacts instead of refetching (resume support)",
    )
    args = parser.parse_args(argv)

    args.snapshot_dir.mkdir(parents=True, exist_ok=True)
    transport = make_transport()
    now = datetime.now(UTC)
    fetched_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_ms = mv.last_closed_day_end_ms(now)
    catalog = mv.build_catalog()

    series_blocks: list[dict[str, Any]] = []
    normalized_store: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for (venue, asset, series_key), ref in sorted(catalog.items()):
        if venue not in args.venues or asset not in args.assets:
            continue
        if ref.status == mv.STATUS_VENUE_LACKS:
            series_blocks.append(build_series_block(ref, status=mv.STATUS_VENUE_LACKS))
            print(f"{venue} {asset} {series_key}: venue lacks market ({ref.note})")
            continue
        print(f"{venue} {asset} {series_key} [{ref.venue_symbol}] ...")
        try:
            rows, path = fetch_one(
                transport,
                ref,
                end_ms=end_ms,
                snapshot_dir=args.snapshot_dir,
                fetched_at=fetched_at,
                reuse_artifacts=args.reuse_artifacts,
            )
            block = build_series_block(ref, status=mv.STATUS_OK)
            block["endpoint"] = mv.ENDPOINT_TEMPLATES[(venue, series_key)]
            block["raw_path"] = str(path)
            block["raw_sha256"] = mv.sha256_of(path)
            block["native_rows"] = len(rows)
            if series_key == "funding":
                events = mv.normalize_funding(venue, rows)
                daily = mv.daily_funding_sums(events)
                block["coverage"] = mv.series_coverage([d["close_time"] for d in daily])
                block["funding_interval_hours_declared"] = mv.DECLARED_FUNDING_INTERVAL_HOURS[venue]
                block["funding_interval_hours_observed"] = mv.observed_funding_interval_hours(events)
                block["samples"] = {"first": daily[:2], "last": daily[-2:]}
                normalized_store[(venue, asset, series_key)] = daily
                print(f"  {len(events)} events -> {len(daily)} daily sums; interval observed {block['funding_interval_hours_observed']}h")
            else:
                candles = mv.normalize_daily_candles(venue, series_key, rows)
                block["coverage"] = mv.series_coverage([c["close_time"] for c in candles])
                block["coverage"].update(mv.volume_coverage(candles))
                block["samples"] = {
                    "first": [{k: c[k] for k in ("close_time", "close")} for c in candles[:2]],
                    "last": [{k: c[k] for k in ("close_time", "close")} for c in candles[-2:]],
                }
                normalized_store[(venue, asset, series_key)] = candles
                cov = block["coverage"]
                print(f"  {len(candles)} daily candles {cov['first_close']} .. {cov['last_close']} (missing internal: {cov['missing_internal_days']})")
            series_blocks.append(block)
        except Exception as exc:  # a venue failure is a recorded gap, not a run abort
            series_blocks.append(
                build_series_block(
                    ref,
                    status=mv.STATUS_FETCH_FAILED,
                    note=f"fetch failed; gap reported, never substituted: {exc}",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            print(f"  FETCH FAILED ({type(exc).__name__}: {exc}) — recorded as coverage gap")

    # Alignment overview: union calendar per asset/series, per-venue presence.
    alignment_overview: dict[str, Any] = {}
    for asset in args.assets:
        per_series: dict[str, Any] = {}
        for series_key, value_key in (("funding", "funding_rate_sum"), ("perp_1d", "close"), ("spot_1d", "close")):
            per_venue = {
                venue: normalized_store[(venue, asset, series_key)]
                for venue in args.venues
                if (venue, asset, series_key) in normalized_store
            }
            if not per_venue:
                continue
            view = mv.aligned_daily_view(per_venue, value_key)
            per_series[series_key] = {
                "union_calendar_days": len(view["close_times"]),
                "first_close": view["close_times"][0],
                "last_close": view["close_times"][-1],
                "venue_days_present": {
                    venue: sum(1 for v in values if v is not None) for venue, values in view["venues"].items()
                },
            }
        alignment_overview[asset] = per_series

    # Funding quick stats (small, doc-facing): simple mean daily rate per venue.
    funding_quickstats: dict[str, Any] = {}
    for asset in args.assets:
        per_venue_stats: dict[str, Any] = {}
        for venue in args.venues:
            daily = normalized_store.get((venue, asset, "funding"))
            if not daily:
                continue
            values = [float(d["funding_rate_sum"]) for d in daily]
            mean_daily = sum(values) / len(values)
            per_venue_stats[venue] = {
                "days": len(values),
                "mean_daily_rate": f"{mean_daily:.8f}",
                "annualized_simple": f"{mean_daily * 365:.6f}",
            }
        if per_venue_stats:
            funding_quickstats[asset] = per_venue_stats

    gaps = [b for b in series_blocks if b["status"] != mv.STATUS_OK]
    summary = {
        "phase": mv.PHASE,
        "report": "data1_multi_venue_snapshot",
        "fetched_at_utc": fetched_at,
        "snapshot_dir": str(args.snapshot_dir),
        "window": {
            "candles_start_floor_utc": CANDLES_START_FLOOR.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "funding_start_floor_utc": FUNDING_START_FLOOR.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_utc": mv._iso(end_ms),
            "end_rule": "last fully closed UTC day at fetch time; in-progress rows always dropped",
        },
        "universe": {"assets": list(args.assets), "venues": list(args.venues)},
        "provenance": {
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
            "endpoints": {f"{v}/{s}": tpl for (v, s), tpl in sorted(mv.ENDPOINT_TEMPLATES.items())},
            "rate_limits_cited": mv.CITED_RATE_LIMITS,
            "funding_interval_hours_declared": mv.DECLARED_FUNDING_INTERVAL_HOURS,
            "funding_sign_convention": "positive funding rate: longs pay shorts (all five funding venues; kraken uses the price-relative relativeFundingRate)",
            "daily_aggregation": "daily slot closing at D 00:00Z sums funding events with time in [D-1 00:00Z, D 00:00Z) — the FUND-EV1 convention; per-day event counts recorded; partial days reported, never scaled or filled",
            "alignment_rule": "union calendar across venues; missing venue/day stays an explicit null; no forward-fill, no interpolation, no truncation to the intersection",
            "okx_daily_bar_note": "OKX fetched with bar=1Dutc — the default OKX 1D bar is UTC+8-aligned and is refused by the midnight-UTC normalizer guard",
            "kraken_history_limits": "spot OHLC capped by the venue at the last 720 daily candles; futures funding endpoint returns a trailing ~1y window — recorded as venue history limits, not filled",
            "okx_funding_history_limit": "the public funding-rate-history endpoint serves only a trailing ~3-month window — recorded as a venue history limit, not filled",
            "zero_volume_backfill_note": "some venues publish price candles from before their own market traded (Hyperliquid perps: zero-volume daily candles back to 2020-08; real HL trading starts at the first nonzero-volume candle). Zero-volume rows are kept exactly as the venue serves them and counted per series in coverage.zero_volume_rows / first_nonzero_volume_close so backfill is never mistaken for market history",
        },
        "series": series_blocks,
        "coverage_gaps": gaps,
        "alignment_overview": alignment_overview,
        "funding_quickstats": funding_quickstats,
        "boundaries": mv.BOUNDARIES,
    }
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ok_count = sum(1 for b in series_blocks if b["status"] == mv.STATUS_OK)
    print(f"\nWrote {args.summary_output} — {ok_count} series ok, {len(gaps)} gaps recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
