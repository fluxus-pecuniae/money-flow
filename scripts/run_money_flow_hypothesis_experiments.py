"""Generate SV1.15 controlled Money Flow hypothesis experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.strategy_validation.hypothesis_experiments import (
    build_money_flow_hypothesis_experiments,
    load_default_hypothesis_experiment_candles,
    money_flow_hypothesis_experiments_to_markdown,
)
from services.strategy_validation.trade_anatomy import DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-report",
        action="append",
        dest="batch_reports",
        help="Path to a dynamic-equity Strategy Validation batch_report.json. May be repeated.",
    )
    parser.add_argument(
        "--output",
        default="docs/strategy_validation_sv1_15_hypothesis_experiments.md",
        help="Founder-readable Markdown output path.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON output path. Generated JSON under reports/ should remain untracked unless intentional.",
    )
    parser.add_argument(
        "--no-db-candles",
        action="store_true",
        help="Skip DB candle loading; structure/indicator-dependent experiments will have less context.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "both"),
        default="markdown",
        help="Output format. JSON requires --json-output unless --format=json is used with --output.",
    )
    args = parser.parse_args()

    batch_paths = [Path(path) for path in args.batch_reports] if args.batch_reports else list(DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS)
    candles = {} if args.no_db_candles else load_default_hypothesis_experiment_candles(batch_paths)
    report = build_money_flow_hypothesis_experiments(batch_paths, candles_by_symbol_timeframe=candles)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.format in {"markdown", "both"}:
        output.write_text(money_flow_hypothesis_experiments_to_markdown(report), encoding="utf-8")
    if args.format == "json":
        output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "both":
        json_output = Path(args.json_output) if args.json_output else output.with_suffix(".json")
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
