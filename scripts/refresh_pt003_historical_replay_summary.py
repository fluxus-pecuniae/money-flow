#!/usr/bin/env python3
"""Build the PT0.0.3 historical replay horizon and 1D summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.strategy_validation.historical_replay import (
    PT003_TIMEFRAMES,
    audit_persisted_historical_candles,
    build_pt003_historical_replay_summary_from_pt002_summary,
)


DEFAULT_INPUT_PATH = Path("docs/pt0_0_2_historical_strategy_replay_summary.json")
DEFAULT_OUTPUT_PATH = Path("docs/pt0_0_3_historical_strategy_replay_summary.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build PT0.0.3 historical replay summary JSON with 1D UTC aggregation "
            "and Jan 2025 data-horizon truth."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="PT0.0.2 historical replay summary JSON path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="PT0.0.3 dashboard summary output path.",
    )
    parser.add_argument(
        "--skip-db-audit",
        action="store_true",
        help="Skip persisted strategy-validation candle DB audit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Missing PT0.0.2 summary JSON: {args.input}")
    pt002_summary = json.loads(args.input.read_text())
    db_audit_rows = (
        []
        if args.skip_db_audit
        else audit_persisted_historical_candles(timeframes=PT003_TIMEFRAMES)
    )
    summary = build_pt003_historical_replay_summary_from_pt002_summary(
        pt002_summary,
        source_path=args.input,
        db_audit_rows=db_audit_rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
