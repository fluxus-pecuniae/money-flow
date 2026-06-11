#!/usr/bin/env python3
"""FUND-EV2 — one-shot public read-only l2Book cost calibration.

EXEC-EV1 documented its liquidity tiers as MODELED assumptions and noted
that "a future, clearly optional one-shot read-only public l2Book
calibration could refine these". This is that calibration, scoped to the
FUND-EV2 carry universe: it snapshots the CURRENT Hyperliquid public
``l2Book`` for the four perps (BTC/ETH/SOL/HYPE) and their HL spot pairs
(UBTC/UETH/USOL/HYPE vs USDC) and records, per book:

  - top-of-book half-spread (bps of mid);
  - visible quote-notional depth within +-10 / +-25 / +-50 bps of mid
    (20 visible levels per side — a LOWER bound on true depth);
  - the raw top-5 levels for auditability.

PUBLIC READ-ONLY ONLY: single endpoint POST https://api.hyperliquid.xyz/info
with info type ``l2Book``. No private, signed, account, or order endpoint;
no API keys; nothing submitted. Research data preparation only.

Honesty boundaries (documented in the output):
  - This is a POINT-IN-TIME snapshot, not the historical spread/depth over
    the 2025-2026 evidence window. It grounds the ORDER OF MAGNITUDE of the
    FUND-EV2 cost model (is HL spot 0.5 bps-tight or 5 bps-wide?), it does
    not replay history. The evidence run's cost-sensitivity sweep covers
    the uncertainty band this introduces.
  - Depth is the visible 20 levels per side only.

Run locally:
    .venv/bin/python scripts/fetch_fund_ev2_l2book_calibration.py
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

INFO_URL = "https://api.hyperliquid.xyz/info"
PHASE = "FUND-EV2"

BOOKS: dict[str, dict[str, str]] = {
    "BTC": {"perp": "BTC", "spot": "@142", "spot_label": "UBTC/USDC"},
    "ETH": {"perp": "ETH", "spot": "@151", "spot_label": "UETH/USDC"},
    "SOL": {"perp": "SOL", "spot": "@156", "spot_label": "USOL/USDC"},
    "HYPE": {"perp": "HYPE", "spot": "@107", "spot_label": "HYPE/USDC"},
}
DEPTH_BANDS_BPS = (10, 25, 50)
DEFAULT_SUMMARY_OUTPUT = Path("docs/fund_ev2_l2book_calibration_summary.json")
REQUEST_PAUSE_SECONDS = 1.2


def info_request(payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        INFO_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read())


def measure_book(coin: str) -> dict[str, Any]:
    book = info_request({"type": "l2Book", "coin": coin})
    bids, asks = book["levels"][0], book["levels"][1]
    if not bids or not asks:
        raise ValueError(f"empty_l2book:{coin}")
    best_bid = Decimal(str(bids[0]["px"]))
    best_ask = Decimal(str(asks[0]["px"]))
    mid = (best_bid + best_ask) / 2
    half_spread_bps = (best_ask - best_bid) / 2 / mid * Decimal("10000")

    def depth_within(levels: list[dict[str, Any]], band_bps: int) -> Decimal:
        limit = mid * Decimal(band_bps) / Decimal("10000")
        return sum(
            (
                Decimal(str(level["px"])) * Decimal(str(level["sz"]))
                for level in levels
                if abs(Decimal(str(level["px"])) - mid) <= limit
            ),
            Decimal("0"),
        )

    return {
        "coin": coin,
        "best_bid": str(best_bid),
        "best_ask": str(best_ask),
        "mid": str(mid),
        "half_spread_bps": str(half_spread_bps.quantize(Decimal("0.0001"))),
        "visible_depth_quote_by_band_bps": {
            str(band): str((depth_within(bids, band) + depth_within(asks, band)).quantize(Decimal("1")))
            for band in DEPTH_BANDS_BPS
        },
        "visible_levels_per_side": [len(bids), len(asks)],
        "top5_bids": bids[:5],
        "top5_asks": asks[:5],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    args = parser.parse_args(argv)
    fetched_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    books: dict[str, Any] = {}
    for symbol, spec in BOOKS.items():
        perp = measure_book(spec["perp"])
        time.sleep(REQUEST_PAUSE_SECONDS)
        spot = measure_book(spec["spot"])
        spot["spot_label"] = spec["spot_label"]
        time.sleep(REQUEST_PAUSE_SECONDS)
        books[symbol] = {"perp": perp, "spot": spot}
        print(
            f"{symbol}: perp half-spread {perp['half_spread_bps']} bps "
            f"(depth±10bps ${perp['visible_depth_quote_by_band_bps']['10']}); "
            f"spot {spec['spot_label']} half-spread {spot['half_spread_bps']} bps "
            f"(depth±10bps ${spot['visible_depth_quote_by_band_bps']['10']})"
        )
    summary = {
        "phase": PHASE,
        "report": "fund_ev2_l2book_calibration",
        "fetched_at_utc": fetched_at,
        "provenance": {
            "endpoint": INFO_URL,
            "info_types": ["l2Book"],
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
            "exec_ev1_context": (
                "EXEC-EV1 documented its tier half-spreads as modeled assumptions and "
                "explicitly scoped this optional one-shot public l2Book calibration"
            ),
        },
        "honesty": {
            "point_in_time_snapshot_not_window_history": True,
            "depth_is_visible_20_levels_per_side_lower_bound": True,
            "uncertainty_covered_by_cost_sensitivity_sweep": True,
        },
        "books": books,
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
