#!/usr/bin/env python3
"""FUND-EV1 — one-shot public read-only funding + HL spot candle snapshot.

Fetches, for the FUND-EV1 delta-neutral funding-carry evidence phase:

  1. Hyperliquid PUBLIC perp funding history (``info`` type ``fundingHistory``,
     hourly entries, paginated) for the carry universe BTC / ETH / SOL / HYPE.
  2. Hyperliquid PUBLIC spot daily candles (``info`` type ``candleSnapshot``)
     for the matching HL spot pairs: UBTC/USDC (@142), UETH/USDC (@151),
     USOL/USDC (@156), HYPE/USDC (@107).

PUBLIC READ-ONLY ONLY: the single endpoint used is POST
https://api.hyperliquid.xyz/info with the two info types above. No private,
signed, account, or order endpoint exists in this script; no API keys are
read; nothing is submitted. Research data preparation only.

Outputs (SV2.2 conventions):
  - Raw hourly funding + raw spot candle payloads -> ignored local artifacts
    under /tmp/money-flow-fund-ev1/ (documented, NOT committed).
  - A committed provenance summary -> docs/fund_ev1_funding_data_snapshot_summary.json
    with the fetch window, endpoint/info types, row counts, sha256 of every
    raw artifact, and the per-day funding-rate sums per coin (the compact
    series the evidence run consumes), so the carry inputs are auditable from
    the repo even though raw hourly payloads stay ignored.

Window: funding from 2024-01-01 and spot candles from listing, both clamped
to fully closed daily slots ending 2026-06-08T00:00:00Z (the SV2.2-era candle
window end, matching the committed perp candle artifacts).

Run locally:
    .venv/bin/python scripts/fetch_fund_ev1_funding_snapshot.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

INFO_URL = "https://api.hyperliquid.xyz/info"  # public read-only info endpoint
PHASE = "FUND-EV1"

# Carry universe: the three liquid majors with HL spot via Unit, plus HYPE
# (HL-native spot, the most liquid HL spot pair). Next HL-spot-supported
# names (UFART/UPUMP/...) are excluded: thin, meme-tier liquidity.
FUNDING_COINS = ("BTC", "ETH", "SOL", "HYPE")
SPOT_PAIRS: dict[str, str] = {  # perp coin -> HL spot pair id (spotMeta index)
    "BTC": "@142",   # UBTC/USDC
    "ETH": "@151",   # UETH/USDC
    "SOL": "@156",   # USOL/USDC
    "HYPE": "@107",  # HYPE/USDC
}
SPOT_PAIR_LABELS: dict[str, str] = {
    "BTC": "UBTC/USDC",
    "ETH": "UETH/USDC",
    "SOL": "USOL/USDC",
    "HYPE": "HYPE/USDC",
}

FUNDING_START = datetime(2024, 1, 1, tzinfo=UTC)
# Last fully closed daily slot matching the SV2.2 perp candle artifacts:
WINDOW_END = datetime(2026, 6, 8, tzinfo=UTC)

DEFAULT_RAW_DIR = Path("/tmp/money-flow-fund-ev1")
DEFAULT_SUMMARY_OUTPUT = Path("docs/fund_ev1_funding_data_snapshot_summary.json")
REQUEST_PAUSE_SECONDS = 1.2  # public info endpoint rate-limit friendly
FUNDING_PAGE_LIMIT = 500
MAX_RETRIES = 6


def info_request(payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        INFO_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRIES - 1:
                wait = 2.0 * (2**attempt)
                print(f"  429 rate-limited; retrying in {wait:.0f}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def fetch_funding_history(coin: str) -> list[dict[str, Any]]:
    """Paginate hourly funding entries from FUNDING_START to WINDOW_END."""
    entries: list[dict[str, Any]] = []
    cursor_ms = int(FUNDING_START.timestamp() * 1000)
    end_ms = int(WINDOW_END.timestamp() * 1000)
    while cursor_ms < end_ms:
        page = info_request(
            {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": cursor_ms,
                "endTime": end_ms,
            }
        )
        if not page:
            break
        entries.extend(page)
        last_time = int(page[-1]["time"])
        if len(page) < FUNDING_PAGE_LIMIT:
            break
        cursor_ms = last_time + 1
        print(f"  {coin}: {len(entries)} hourly entries so far")
        time.sleep(REQUEST_PAUSE_SECONDS)
    # De-duplicate on time (pagination boundary) and keep <= window end.
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for row in entries:
        t = int(row["time"])
        if t in seen or t >= end_ms:
            continue
        seen.add(t)
        unique.append(row)
    unique.sort(key=lambda row: int(row["time"]))
    return unique


def fetch_spot_daily_candles(pair_id: str) -> list[dict[str, Any]]:
    start_ms = int(datetime(2023, 1, 1, tzinfo=UTC).timestamp() * 1000)
    end_ms = int((WINDOW_END + timedelta(days=2)).timestamp() * 1000)
    raw = info_request(
        {
            "type": "candleSnapshot",
            "req": {
                "coin": pair_id,
                "interval": "1d",
                "startTime": start_ms,
                "endTime": end_ms,
            },
        }
    )
    candles: list[dict[str, Any]] = []
    for row in raw:
        open_time = datetime.fromtimestamp(int(row["t"]) / 1000, UTC)
        close_time = open_time + timedelta(days=1)
        if close_time > WINDOW_END:  # keep fully closed SV2.2-era slots only
            continue
        candles.append(
            {
                "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "close_time": close_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": str(row["o"]),
                "high": str(row["h"]),
                "low": str(row["l"]),
                "close": str(row["c"]),
                "volume": str(row["v"]),
                "trade_count": int(row.get("n") or 0),
                "source": "hyperliquid_public_mainnet_candleSnapshot_spot",
            }
        )
    candles.sort(key=lambda c: c["open_time"])
    return candles


def daily_funding_sums(entries: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """Sum hourly funding rates into daily slots keyed by candle CLOSE time.

    The slot closing at day D 00:00 UTC contains the hourly entries with
    time in [D-1 00:00, D 00:00) — i.e. the funding paid DURING that daily
    candle. Exact Decimal string sums; count carries the hour coverage.
    """
    buckets: dict[str, tuple[Decimal, int]] = {}
    for row in entries:
        t = datetime.fromtimestamp(int(row["time"]) / 1000, UTC)
        slot_close = (t.replace(hour=0, minute=0, second=0, microsecond=0)) + timedelta(days=1)
        key = slot_close.strftime("%Y-%m-%dT%H:%M:%SZ")
        total, count = buckets.get(key, (Decimal("0"), 0))
        buckets[key] = (total + Decimal(str(row["fundingRate"])), count + 1)
    return [
        {"close_time": key, "funding_rate_sum": str(total), "hours": count}
        for key, (total, count) in sorted(buckets.items())
    ]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    args = parser.parse_args(argv)

    funding_dir = args.raw_dir / "raw_funding"
    spot_dir = args.raw_dir / "raw_spot_candles"
    funding_dir.mkdir(parents=True, exist_ok=True)
    spot_dir.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    funding_blocks: dict[str, Any] = {}
    spot_blocks: dict[str, Any] = {}

    for coin in FUNDING_COINS:
        entries = fetch_funding_history(coin)
        raw_path = funding_dir / f"hyperliquid_public_{coin.lower()}_funding_hourly_fund_ev1.json"
        raw_path.write_text(
            json.dumps(
                {
                    "phase": PHASE,
                    "source": "hyperliquid_public_mainnet_fundingHistory",
                    "coin": coin,
                    "fetched_at_utc": fetched_at,
                    "entries": entries,
                },
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        sums = daily_funding_sums(entries)
        funding_blocks[coin] = {
            "raw_path": str(raw_path),
            "raw_sha256": sha256_of(raw_path),
            "hourly_entries": len(entries),
            "first_entry_utc": datetime.fromtimestamp(int(entries[0]["time"]) / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if entries else None,
            "last_entry_utc": datetime.fromtimestamp(int(entries[-1]["time"]) / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if entries else None,
            "daily_funding_rate_sums": sums,
        }
        print(f"funding {coin}: {len(entries)} hourly entries -> {raw_path}")
        time.sleep(REQUEST_PAUSE_SECONDS)

    for coin in FUNDING_COINS:
        pair_id = SPOT_PAIRS[coin]
        candles = fetch_spot_daily_candles(pair_id)
        raw_path = spot_dir / f"hyperliquid_public_spot_{coin.lower()}_1d_fund_ev1.json"
        raw_path.write_text(
            json.dumps(
                {
                    "phase": PHASE,
                    "source": "hyperliquid_public_mainnet_candleSnapshot_spot",
                    "symbol": coin,
                    "spot_pair": SPOT_PAIR_LABELS[coin],
                    "spot_pair_id": pair_id,
                    "timeframe": "1d",
                    "fetched_at_utc": fetched_at,
                    "candles": candles,
                },
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        spot_blocks[coin] = {
            "spot_pair": SPOT_PAIR_LABELS[coin],
            "spot_pair_id": pair_id,
            "raw_path": str(raw_path),
            "raw_sha256": sha256_of(raw_path),
            "candle_count": len(candles),
            "first_close_time": candles[0]["close_time"] if candles else None,
            "last_close_time": candles[-1]["close_time"] if candles else None,
        }
        print(f"spot {coin} ({SPOT_PAIR_LABELS[coin]}): {len(candles)} daily candles -> {raw_path}")
        time.sleep(REQUEST_PAUSE_SECONDS)

    summary = {
        "phase": PHASE,
        "report": "fund_ev1_funding_data_snapshot",
        "fetched_at_utc": fetched_at,
        "provenance": {
            "endpoint": INFO_URL,
            "info_types": ["fundingHistory", "candleSnapshot"],
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
            "funding_window": [
                FUNDING_START.strftime("%Y-%m-%dT%H:%M:%SZ"),
                WINDOW_END.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ],
            "spot_candle_clamp_end": WINDOW_END.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "perp_candles": "reused from the SV2.2 public-mainnet refresh artifacts (docs/sv2_2_hyperliquid_research_refresh_summary.json)",
            "funding_sign_convention": "positive fundingRate: longs pay shorts (Hyperliquid hourly funding)",
            "daily_aggregation": "daily_funding_rate_sums[close_time] = sum of hourly fundingRate entries inside that daily candle slot",
        },
        "universe": {
            "coins": list(FUNDING_COINS),
            "spot_pairs": {c: SPOT_PAIR_LABELS[c] for c in FUNDING_COINS},
            "excluded_next_names": "UFART/UPUMP and other HL spot listings: thin meme-tier liquidity",
        },
        "funding": funding_blocks,
        "spot_candles": spot_blocks,
        "boundaries": {
            "research_only": True,
            "public_read_only": True,
            "calls_private_signed_or_order_endpoints": False,
            "creates_orders": False,
            "mutates_runtime_artifacts": False,
        },
    }
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {args.summary_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
