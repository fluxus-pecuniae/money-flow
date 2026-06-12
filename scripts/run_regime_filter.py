#!/usr/bin/env python3
"""REGIME1 — current market-regime risk-off state (read-only signal CLI).

RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA. Computes the breadth-based
risk_on / risk_off state from the LATEST FULLY CLOSED public daily candles
of the liquid majors (Binance USDS-M perp klines — the same public
read-only endpoint DATA1 ingests; no keys, no private/signed endpoints,
nothing submitted). The committed evidence verdict for this filter is
``regime_filter_does_not_reduce_drawdown_oos`` — the state printed here is
INFORMATIONAL RISK CONTEXT, not a validated control and never an order.

Defaults are pinned by test to the committed evidence summary's train-only
choice; re-tuning without new evidence fails CI.

Run locally (public read-only fetch):
    .venv/bin/python scripts/run_regime_filter.py
Offline replay (tests / no network):
    .venv/bin/python scripts/run_regime_filter.py --input-json <candles.json>

Writes the ignored artifact reports/regime1/current_regime_state.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _load_module(relative: str, alias: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rg = _load_module("services/strategy_validation/regime1.py", "regime1_cli_module")
fv = _load_module("services/strategy_validation/fund_venues1.py", "regime1_cli_fund_venues1")

from services.market_data import data1_multi_venue as mv  # noqa: E402

ASSETS = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
VENUE = "binance"
HISTORY_DAYS = 200  # comfortably above the 90-candle longest warm-up
DEFAULT_OUTPUT = Path("reports/regime1/current_regime_state.json")


def fetch_latest_candles() -> dict[str, list[dict[str, Any]]]:
    """Public read-only fetch of the last ~HISTORY_DAYS closed daily perp
    candles per asset (the DATA1 Binance fetcher + paced transport)."""
    from scripts.fetch_data1_multi_venue_snapshot import make_transport

    transport = make_transport()
    now = datetime.now(UTC)
    end_ms = mv.last_closed_day_end_ms(now)
    start_ms = end_ms - HISTORY_DAYS * 86_400_000
    out: dict[str, list[dict[str, Any]]] = {}
    for asset in ASSETS:
        rows = mv.fetch_binance_klines(transport, f"{asset}USDT", start_ms, end_ms, market="perp")
        out[asset] = mv.normalize_daily_candles(VENUE, "perp_1d", rows)
        print(f"  {asset}: {len(out[asset])} closed daily candles")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", type=Path, default=None, help="offline candle replay (tests)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    print("REGIME1 current regime state (public read-only; signal only)")
    print(f"> {rg.DISCLAIMER}")
    print(f"> {rg.COMMITTED_VERDICT_NOTE}\n")

    if args.input_json is not None:
        candles_by_asset = json.loads(args.input_json.read_text(encoding="utf-8"))
    else:
        candles_by_asset = fetch_latest_candles()

    datasets = [
        fv.dataset_from_data1_rows(asset, VENUE, "perp_1d", rows)
        for asset, rows in sorted(candles_by_asset.items())
    ]
    gate = rg.build_regime_gate(datasets)  # pinned DEFAULT_CONFIG
    as_of = gate.last_state_time
    state = gate.state_at(as_of)

    print(f"as-of close:    {as_of}")
    print(f"state:          {state['state'].upper()}")
    print(f"breadth:        {state['breadth_up_count']}/{state['universe_size']} majors trend-up (risk_score {state['risk_score']})")
    print(f"BTC bellwether: {'UP' if state['btc_trend_up'] else 'DOWN'}")
    print(f"config:         {state['config_id']} (pinned to the committed train-only choice)")

    payload = {
        "phase": rg.PHASE,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of_close": str(as_of),
        "state": {k: (str(v) if isinstance(v, Decimal) else v) for k, v in state.items()},
        "committed_verdict_note": rg.COMMITTED_VERDICT_NOTE,
        "source": (
            "offline_input_json_replay"
            if args.input_json is not None
            else "binance_public_fapi_klines_read_only"
        ),
        "boundaries": rg.boundary_flags(),
        "disclaimer": rg.DISCLAIMER,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nWrote {args.output} (ignored artifact)")
    print(f"> {rg.DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
