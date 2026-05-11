#!/usr/bin/env python3
"""Build the PT0.0.2 historical strategy replay dashboard summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.strategy_validation.historical_replay import (
    audit_persisted_historical_candles,
    build_pt002_historical_replay_summary_from_sv117_payload,
)


DEFAULT_OFFLINE_REPLAY_PATH = Path("/tmp/money-flow-sv117-full-suite.json")
DEFAULT_OUTPUT_PATH = Path("docs/pt0_0_2_historical_strategy_replay_summary.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build PT0.0.2 historical strategy replay summary JSON from SV1.17 baseline replay output.",
    )
    parser.add_argument(
        "--offline-replay-json",
        type=Path,
        default=DEFAULT_OFFLINE_REPLAY_PATH,
        help="Trusted offline SV1.17 full-suite replay JSON path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Dashboard summary output path.",
    )
    parser.add_argument(
        "--skip-db-audit",
        action="store_true",
        help="Skip persisted strategy-validation candle DB audit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.offline_replay_json.exists():
        raise SystemExit(f"Missing offline replay JSON: {args.offline_replay_json}")
    payload = json.loads(args.offline_replay_json.read_text())
    db_audit_rows = [] if args.skip_db_audit else audit_persisted_historical_candles()
    summary = build_pt002_historical_replay_summary_from_sv117_payload(
        payload,
        source_path=args.offline_replay_json,
        db_audit_rows=db_audit_rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
