"""Generate SV1.14 Money Flow trade-anatomy diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.strategy_validation.trade_anatomy import (
    DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
    build_money_flow_trade_anatomy_diagnostics,
    load_candles_for_batch_reports,
    money_flow_trade_anatomy_to_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-report",
        action="append",
        dest="batch_reports",
        help="Path to a Strategy Validation batch_report.json. May be repeated.",
    )
    parser.add_argument(
        "--output",
        default="docs/strategy_validation_sv1_14_trade_anatomy_and_market_structure.md",
        help="Founder-readable Markdown output path.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON diagnostics output path. Generated outputs under reports/ should remain untracked.",
    )
    parser.add_argument(
        "--no-db-candles",
        action="store_true",
        help="Skip DB candle loading; market-structure diagnostics will report missing candle context.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "both"),
        default="markdown",
        help="Output format. JSON requires --json-output unless --format=json is used with --output.",
    )
    args = parser.parse_args()

    batch_paths = [Path(path) for path in args.batch_reports] if args.batch_reports else list(DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS)
    candles = {} if args.no_db_candles else load_candles_for_batch_reports(batch_paths)
    report = build_money_flow_trade_anatomy_diagnostics(batch_paths, candles_by_symbol_timeframe=candles)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.format in {"markdown", "both"}:
        output.write_text(money_flow_trade_anatomy_to_markdown(report), encoding="utf-8")
    if args.format == "json":
        output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "both":
        json_output = Path(args.json_output) if args.json_output else output.with_suffix(".json")
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

