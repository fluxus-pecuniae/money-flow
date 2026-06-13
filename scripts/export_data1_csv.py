#!/usr/bin/env python3
"""Export DATA1 daily candles as per-symbol OHLCV CSVs (founder portable copy).

Reads the committed provenance summary + the durable ignored snapshot
(var/data1/raw_series/) through the standard sha256-verified loader and
writes one CSV per (venue, asset, series): close_time, open, high, low,
close, volume_base. Read-only over local artifacts; no network.

Run locally (the 7 Binance perp majors, the replay/observation universe):
    .venv/bin/python scripts/export_data1_csv.py
Everything in the snapshot:
    .venv/bin/python scripts/export_data1_csv.py --all-series
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from services.market_data.data1_multi_venue import load_data1_dataset  # noqa: E402

DEFAULT_OUTPUT_DIR = REPO_ROOT / "var" / "data1" / "csv"
MAJORS = ("BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "AVAX")
FIELDS = ("close_time", "open", "high", "low", "close", "volume_base")


def export_series(ds, venue: str, asset: str, series_key: str, output_dir: Path) -> Path | None:
    series = ds.series(venue, asset, series_key)
    if series.status != "ok":
        print(f"  skip {venue}/{asset}/{series_key}: {series.status}")
        return None
    path = output_dir / f"{venue}_{asset.lower()}_{series_key}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in series.rows:
            writer.writerow({field: row.get(field) for field in FIELDS})
    print(f"  wrote {path.relative_to(REPO_ROOT)} ({len(list(series.rows))} rows)")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--all-series", action="store_true", help="export every ok series, not just the Binance perp majors")
    args = parser.parse_args(argv)

    ds = load_data1_dataset()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    if args.all_series:
        for block in ds.summary["series"]:
            if block.get("status") != "ok" or block.get("series") == "funding":
                continue
            if export_series(ds, block["venue"], block["asset"], block["series"], args.output_dir):
                count += 1
    else:
        for asset in MAJORS:
            if export_series(ds, "binance", asset, "perp_1d", args.output_dir):
                count += 1
    print(f"exported {count} CSV file(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
