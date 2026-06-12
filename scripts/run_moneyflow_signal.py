#!/usr/bin/env python3
"""MONEYFLOW-SIGNAL1 — the current Money Flow signal state (read-only CLI).

SOURCE-FAITHFUL SIGNAL, NOT ALPHA. Computes the documented Gerald Peters
Money Flow signal state (stage, 5/20 crossover buy/sell, confirmed Stage-2
entry, documented exits, RSI/MACD warnings — every intermediate term
inspectable) from the LATEST FULLY CLOSED public daily candles of the liquid
majors (Binance USDS-M perp klines — the same public read-only endpoint
DATA1 ingests; no keys, no private/signed endpoints, nothing submitted).

The directional Money Flow rules showed NO standalone edge out-of-sample
(MF-ORIG-EV1.1/EV2; re-confirmed by the MONEYFLOW-SIGNAL1 characterization);
this surface exists for fidelity and trust, not profit. The REGIME overlay
attached to every run is INFORMATIONAL RISK CONTEXT, not a validated control
— its committed evidence verdict is an honest FAIL
(``regime_filter_does_not_reduce_drawdown_oos``: endpoint-strong,
process-unstable). Signal only, never an order.

Run locally (public read-only fetch):
    .venv/bin/python scripts/run_moneyflow_signal.py
Offline replay (tests / no network):
    .venv/bin/python scripts/run_moneyflow_signal.py --input-json <candles.json>

Writes the ignored artifact reports/moneyflow_signal1/current_moneyflow_signal.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# This CLI is read-only signal computation: the reused MF-ORIG engine module
# imports DB plumbing at module level, so local runtime .env values must not
# gate (or leak into) signal computation — same isolation tests/conftest.py
# applies. Nothing here reads settings, keys, or the DB.
from core.config.settings import AppSettings, get_settings  # noqa: E402

AppSettings.model_config["env_file"] = None
get_settings.cache_clear()

from services.market_data import data1_multi_venue as mv  # noqa: E402
from services.strategy_validation import moneyflow_signal1 as ms  # noqa: E402


def _load_module(relative: str, alias: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rg = _load_module("services/strategy_validation/regime1.py", "moneyflow_signal_cli_regime1")
fv = _load_module("services/strategy_validation/fund_venues1.py", "moneyflow_signal_cli_fund_venues1")

ASSETS = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
VENUE = "binance"
HISTORY_DAYS = 200  # comfortably above the 90-candle regime warm-up and the 50-candle signal warm-up
DEFAULT_OUTPUT = Path("reports/moneyflow_signal1/current_moneyflow_signal.json")


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

    print("MONEYFLOW-SIGNAL1 current signal state (public read-only; signal only)")
    print(f"> {ms.DISCLAIMER}\n")

    if args.input_json is not None:
        candles_by_asset = json.loads(args.input_json.read_text(encoding="utf-8"))
        # Normalize offline-replay close times to the Z form the regime
        # dataset builder's strict parser expects (fund_venues1._parse_close);
        # otherwise the regime overlay silently degrades to unavailable on
        # isoformat(+00:00) fixtures.
        candles_by_asset = {
            asset: [{**row, "close_time": str(row["close_time"]).replace("+00:00", "Z")} for row in rows]
            for asset, rows in candles_by_asset.items()
        }
        source = "offline_input_json_replay"
    else:
        candles_by_asset = fetch_latest_candles()
        source = "binance_public_fapi_klines_read_only"

    core_candles = {
        asset: ms.core_candles_from_data1_rows(asset, rows)
        for asset, rows in sorted(candles_by_asset.items())
    }

    # The regime overlay (informational risk context; honest-FAIL verdict
    # travels with the state). A gate build failure never blocks the signal.
    regime_gate = None
    regime_error: str | None = None
    try:
        datasets = [
            fv.dataset_from_data1_rows(asset, VENUE, "perp_1d", rows)
            for asset, rows in sorted(candles_by_asset.items())
        ]
        regime_gate = rg.build_regime_gate(datasets)  # pinned committed default
    except Exception as exc:
        regime_error = f"regime_gate_unavailable:{exc}"

    payload = ms.latest_signal_report(
        core_candles, regime_gate=regime_gate, regime_error=regime_error
    )
    payload["source"] = source
    payload["pdf_provenance"] = ms.pdf_provenance_check(REPO_ROOT)

    for asset, block in payload["assets"].items():
        state = block["latest_state"]
        if state is None:
            print(f"{asset}: no candles")
            continue
        if not state["warmed_up"]:
            print(f"{asset}: warming up ({', '.join(state['missing_reasons'])})")
            continue
        flags = []
        if state["basic_signal"] != "none":
            flags.append(f"5/20 {state['basic_signal'].upper()} cross")
        if state["source_entry_signal"]:
            flags.append("stage-2 confirmed entry signal")
        if state["exit_signal"]:
            flags.append(state["exit_signal"])
        if state["rsi_profit_warning"]:
            flags.append("RSI>70 warning" + (" (ignore: MA stack aligned)" if state["rsi_ignore_active"] else ""))
        if state["trim_context_25pct"]:
            flags.append("MACD sell cross while 5>20 (quarter-trim context)")
        print(
            f"{asset}: stage={state['stage']} position={state['position_state']} "
            f"basic={state['basic_position_state']} close_vs_sma20={state['indicators']['close_vs_sma20_pct']}% "
            f"rsi14={state['indicators']['rsi14']}"
            + (f"  [{'; '.join(flags)}]" if flags else "")
        )

    overlay = payload["regime_overlay"]
    if overlay["available"]:
        print(
            f"\nregime overlay: {overlay['state']['state'].upper()} as of {overlay['as_of_close']} "
            f"({overlay['label']})"
        )
    else:
        print(f"\nregime overlay unavailable: {overlay['reason']} ({overlay['label']})")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nWrote {args.output} (ignored artifact)")
    print(f"> {ms.DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
