#!/usr/bin/env python3
"""Refresh the DATA1 snapshot in place: append ONLY newly closed candles.

Public read-only (the same DATA1 fetchers/transport; no keys, no private or
signed endpoints, nothing submitted). For every `ok` daily-candle series in
the committed provenance summary, fetch candles after the artifact's last
recorded candle, append the venue-native rows (deduped on the native open
time), rewrite the durable ignored artifact under var/data1/raw_series/, and
update the committed summary's sha256 + coverage for that series. Funding
series are left untouched (candle refresh only). Already-current series are
reported as up_to_date and their artifacts are not rewritten.

Run locally:
    .venv/bin/python scripts/refresh_data1_snapshot.py
Limit to one venue/series for a quick check:
    .venv/bin/python scripts/refresh_data1_snapshot.py --venue binance --series perp_1d
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from services.market_data import data1_multi_venue as mv  # noqa: E402

DEFAULT_SUMMARY = REPO_ROOT / "docs" / "data1_multi_venue_snapshot_summary.json"
CANDLE_SERIES = ("perp_1d", "spot_1d")


def _native_open_ms(venue: str, series: str, row: Any) -> int:
    """The venue-native open timestamp (ms) — the dedupe/append key."""
    normalized = mv.normalize_daily_candles(venue, series, [row])
    open_time = normalized[0]["open_time"]
    parsed = datetime.fromisoformat(str(open_time).replace("Z", "+00:00"))
    return int(parsed.timestamp() * 1000)


def refresh_series(
    transport: Any,
    summary: dict[str, Any],
    block: dict[str, Any],
    *,
    snapshot_dir: Path,
    now: datetime,
) -> dict[str, Any]:
    venue, asset, series = block["venue"], block["asset"], block["series"]
    ref = mv.build_catalog()[(venue, asset, series)]
    path = snapshot_dir / mv.artifact_filename(venue, asset, series)
    if not path.exists():
        return {"venue": venue, "asset": asset, "series": series, "status": "artifact_missing_run_full_fetch"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = list(payload["rows"])
    if not rows:
        return {"venue": venue, "asset": asset, "series": series, "status": "empty_artifact_run_full_fetch"}

    last_open_ms = max(_native_open_ms(venue, series, row) for row in rows)
    start_ms = last_open_ms + 86_400_000  # the first UNRECORDED daily open
    end_ms = mv.last_closed_day_end_ms(now)
    if start_ms >= end_ms:
        return {"venue": venue, "asset": asset, "series": series, "status": "up_to_date", "appended": 0}

    fetcher = mv.FETCH_DISPATCH[(venue, series)]
    fetched = fetcher(transport, ref.venue_symbol, start_ms, end_ms)
    fresh = [row for row in fetched if _native_open_ms(venue, series, row) > last_open_ms]
    if not fresh:
        return {"venue": venue, "asset": asset, "series": series, "status": "up_to_date", "appended": 0}

    merged = rows + sorted(fresh, key=lambda row: _native_open_ms(venue, series, row))
    fetched_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    path = mv.write_series_artifact(
        snapshot_dir,
        ref,
        merged,
        endpoint=mv.ENDPOINT_TEMPLATES[(venue, series)],
        fetched_at_utc=fetched_at,
    )
    normalized = mv.normalize_daily_candles(venue, series, merged)
    block["raw_sha256"] = mv.sha256_of(path)
    block["row_count"] = len(merged)
    coverage = dict(block.get("coverage") or {})
    coverage.update(mv.series_coverage([row["close_time"] for row in normalized]))
    block["coverage"] = coverage
    block["refreshed_at_utc"] = fetched_at
    return {
        "venue": venue,
        "asset": asset,
        "series": series,
        "status": "appended_newly_closed_candles",
        "appended": len(fresh),
        "last_close": normalized[-1]["close_time"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--venue", default=None)
    parser.add_argument("--series", default=None, choices=(None, *CANDLE_SERIES))
    args = parser.parse_args(argv)

    from scripts.fetch_data1_multi_venue_snapshot import make_transport

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    snapshot_dir = args.snapshot_dir or (REPO_ROOT / summary["snapshot_dir"])
    transport = make_transport()
    now = datetime.now(UTC)
    results = []
    for block in summary["series"]:
        if block.get("status") != "ok" or block.get("series") not in CANDLE_SERIES:
            continue
        if args.venue and block["venue"] != args.venue:
            continue
        if args.series and block["series"] != args.series:
            continue
        result = refresh_series(transport, summary, block, snapshot_dir=snapshot_dir, now=now)
        results.append(result)
        print(f"  {result['venue']}/{result['asset']}/{result['series']}: {result['status']} (+{result.get('appended', 0)})")

    appended_any = any(r.get("appended") for r in results)
    if appended_any:
        summary["refreshed_at_utc"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"updated {args.summary} (sha256 + coverage for refreshed series)")
    else:
        print("all selected series up to date; summary unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
