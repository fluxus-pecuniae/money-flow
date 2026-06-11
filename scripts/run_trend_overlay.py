#!/usr/bin/env python3
"""TREND-OVERLAY1 — compute the current trend drawdown-control signal.

READ-ONLY SIGNAL TOOL, not an executor: it prints the vol-targeted target
exposure the TSMOM-EV1 defensive overlay would hold RIGHT NOW for the eight
liquid majors, and writes ``current_trend_overlay.json``. It submits
nothing, signs nothing, and approves nothing — the output is an advisory
number an operator may read to manage drawdown on a held long book.

DRAWDOWN CONTROL, NOT ALPHA (the disclaimer travels in every output):
TSMOM-EV1 validated this overlay as risk reduction (bear drawdown 66% ->
17%) while it LOST 12.2% absolute in the same OOS window - authored mixed,
"defensive, not profitable". Nothing here changes that.

Data: Hyperliquid PUBLIC mainnet ``candleSnapshot`` (the same read-only,
no-keys endpoint the dashboard already polls), latest FULLY CLOSED daily
candles only (the in-progress candle is dropped before computation).
Offline mode: ``--input-json`` replays a saved candle payload instead of
fetching (used by tests; no network).

Run locally:
    .venv/bin/python scripts/run_trend_overlay.py
    .venv/bin/python scripts/run_trend_overlay.py --account-size 25000
    .venv/bin/python scripts/run_trend_overlay.py --input-json saved.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any


def _load_module(relative: str, alias: str):
    module_path = Path(__file__).resolve().parents[1] / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


overlay_mod = _load_module(
    "services/strategy_validation/trend_overlay1.py", "trend_overlay1_cli_module"
)

INFO_URL = "https://api.hyperliquid.xyz/info"  # public read-only info endpoint
FETCH_DAYS = 150  # lookback 30 + vol window 30 + generous closed-history buffer
REQUEST_PAUSE_SECONDS = 1.2
MAX_RETRIES = 5
DEFAULT_OUTPUT = Path("reports/trend_overlay/current_trend_overlay.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--account-size", type=Decimal, default=overlay_mod.DEFAULT_ACCOUNT_SIZE_USDC
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="offline candle payload (skips the network fetch entirely)",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="UTC ISO time for the closed-candle cutoff (default: now)",
    )
    parser.add_argument(
        "--save-candles",
        type=Path,
        default=None,
        help="also save the fetched candle payload (for offline replay)",
    )
    return parser


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
                time.sleep(2.0 * (2**attempt))
                continue
            raise
    raise RuntimeError("unreachable")


def fetch_latest_candles(as_of: datetime) -> dict[str, list[dict[str, Any]]]:
    """Public read-only candleSnapshot fetch, normalized to the repo's
    candle dict shape; the CLOSED filter happens later in the calculator."""
    start_ms = int((as_of - timedelta(days=FETCH_DAYS)).timestamp() * 1000)
    end_ms = int((as_of + timedelta(days=1)).timestamp() * 1000)
    candles_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for symbol in overlay_mod.LIQUID_UNIVERSE:
        raw = info_request(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": symbol,
                    "interval": "1d",
                    "startTime": start_ms,
                    "endTime": end_ms,
                },
            }
        )
        rows = []
        for row in raw:
            open_time = datetime.fromtimestamp(int(row["t"]) / 1000, UTC)
            close_time = open_time + timedelta(days=1)
            rows.append(
                {
                    "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "close_time": close_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "open": str(row["o"]),
                    "high": str(row["h"]),
                    "low": str(row["l"]),
                    "close": str(row["c"]),
                    "volume": str(row["v"]),
                    "source": "hyperliquid_public_mainnet_candleSnapshot",
                }
            )
        candles_by_symbol[symbol] = rows
        time.sleep(REQUEST_PAUSE_SECONDS)
    return candles_by_symbol


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    as_of = (
        datetime.strptime(args.as_of, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        if args.as_of
        else datetime.now(UTC)
    )
    if args.input_json is not None:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
        candles_by_symbol = payload["candles_by_symbol"]
        source = f"offline_replay:{args.input_json}"
    else:
        candles_by_symbol = fetch_latest_candles(as_of)
        source = "hyperliquid_public_mainnet_candleSnapshot_read_only"
        if args.save_candles is not None:
            args.save_candles.parent.mkdir(parents=True, exist_ok=True)
            args.save_candles.write_text(
                json.dumps(
                    {
                        "phase": overlay_mod.PHASE,
                        "fetched_at_utc": datetime.now(UTC).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "candles_by_symbol": candles_by_symbol,
                    },
                    indent=1,
                )
                + "\n",
                encoding="utf-8",
            )
    overlay = overlay_mod.compute_overlay(
        candles_by_symbol, as_of=as_of, account_size_usdc=args.account_size
    )
    overlay["data_source"] = source
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(overlay, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(overlay_mod.render_table(overlay))
    print()
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
