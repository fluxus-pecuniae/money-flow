#!/usr/bin/env python3
"""Build the MF-REPLAY1 dashboard replay pack (ignored local artifact).

Precomputes the common founder ranges — ALL-TIME and every calendar year —
for both PT-RT2 lanes through the committed range-replay engine, plus the
daily candle series for the chart, and writes
``reports/mf_replay1/replay_pack.json`` (gitignored). Custom date ranges are
served on demand by the dashboard control server's ``/api/mf-replay1/range``
endpoint — same engine, one code path.

HYPOTHETICAL REPLAY CONTEXT, NOT EVIDENCE — the disclaimer and the committed
characterization labels are embedded in the pack and rendered on the surface.

Run locally (read-only over the DATA1 snapshot; no network):
    .venv/bin/python scripts/build_mf_replay1_dashboard_data.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Read-only replay computation: keep the local runtime .env out of settings
# (same isolation tests/conftest.py applies); nothing here reads the DB.
from core.config.settings import AppSettings, get_settings  # noqa: E402

AppSettings.model_config["env_file"] = None
get_settings.cache_clear()

from services.paper_runtime import mf_replay1 as mr  # noqa: E402
from services.paper_runtime.pt_rt1 import PT_RT2_ACTIVE_REVIEW_START_UTC  # noqa: E402

DEFAULT_OUTPUT = REPO_ROOT / "reports" / "mf_replay1" / "replay_pack.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    print("building replay context (full DATA1 history, both lanes)...")
    candles = mr.replay_candles_from_data1()
    context = mr.build_replay_context(candles)
    years = mr.calendar_year_ranges(context)

    results: dict[str, dict] = {}
    for lane_id in ("mf_source_faithful_baseline", "mf_source_faithful_regime_gated"):
        results[f"{lane_id}|all_time"] = mr.replay_range(
            context, lane_id, context.aligned_start, context.last_close
        )
        for year in years:
            results[f"{lane_id}|year_{year['year']}"] = mr.replay_range(
                context, lane_id, year["start"], year["end"]
            )
        print(f"  {lane_id}: all-time + {len(years)} year books")

    pack = {
        "phase": mr.PHASE,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disclaimer": mr.REPLAY_DISCLAIMER,
        "semantics": mr.PRE_REGISTERED_SEMANTICS,
        "committed_characterization": mr.COMMITTED_CHARACTERIZATION,
        "runtime_observation_start_utc": PT_RT2_ACTIVE_REVIEW_START_UTC,
        "coverage": {
            "aligned_start": results["mf_source_faithful_baseline|all_time"]["first_in_range_close"],
            "last_close": results["mf_source_faithful_baseline|all_time"]["last_in_range_close"],
            "per_symbol_first_close": {
                symbol: series[0].close_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                for symbol, series in context.candles_by_symbol.items()
            },
        },
        "years": years,
        "lanes": list(("mf_source_faithful_baseline", "mf_source_faithful_regime_gated")),
        "results": results,
        "candles_by_symbol": {
            symbol: [
                {
                    "time": candle.close_time.strftime("%Y-%m-%d"),
                    "open": str(candle.open),
                    "high": str(candle.high),
                    "low": str(candle.low),
                    "close": str(candle.close),
                }
                for candle in series
            ]
            for symbol, series in context.candles_by_symbol.items()
        },
        "custom_range_endpoint": "/api/mf-replay1/range (dashboard control server; same engine)",
        "feeds_live_ledgers": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pack) + "\n", encoding="utf-8")
    size_mb = args.output.stat().st_size / 1e6
    print(f"wrote {args.output} ({size_mb:.1f} MB, ignored artifact)")
    print(f"> {mr.REPLAY_DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
