"""Preflight offline/public candles before Strategy Validation import."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from core.domain.enums import Timeframe
from services.strategy_validation import (
    preflight_strategy_validation_candle_import,
    strategy_validation_candle_import_preflight_result_to_json,
    strategy_validation_candle_import_preflight_result_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate offline/public candle files and market identity mappings before "
            "Strategy Validation import. This preflight writes no candles, generates no "
            "evidence packs, calls no exchanges, and creates no live artifacts."
        ),
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="CSV or JSON candle file to validate without writing. May be repeated.",
    )
    parser.add_argument(
        "--requirements-from-review-json",
        help="Optional evidence-review JSON containing canonical import/identity requirements.",
    )
    parser.add_argument(
        "--requirement-json",
        action="append",
        default=[],
        help=(
            "Requirement JSON object/list to reconcile against input files. May be repeated. "
            "If count matches --input count, files are paired by order unless an input map is supplied."
        ),
    )
    parser.add_argument(
        "--input-requirement-map",
        help=(
            "Optional JSON object mapping input file paths to requirement objects, requirement "
            "indexes, or requirement identifiers."
        ),
    )
    parser.add_argument(
        "--environment",
        required=True,
        help="Environment intended for the future candle import.",
    )
    parser.add_argument("--venue", required=True, help="Venue intended for the future import.")
    parser.add_argument(
        "--timeframe",
        choices=tuple(item.value for item in Timeframe),
        help="Optional timeframe for all supplied input rows. If omitted, input rows must include `timeframe`.",
    )
    parser.add_argument(
        "--input-format",
        choices=("auto", "csv", "json"),
        default="auto",
        help="Input file format. Default infers from extension.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional directory for preflight summary files; stdout is always written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = preflight_strategy_validation_candle_import(
        input_paths=tuple(Path(path) for path in args.input),
        requirements_from_review_json=(
            Path(args.requirements_from_review_json)
            if args.requirements_from_review_json
            else None
        ),
        requirement_json_paths=tuple(Path(path) for path in args.requirement_json),
        input_requirement_map_path=(
            Path(args.input_requirement_map) if args.input_requirement_map else None
        ),
        environment=args.environment,
        venue=args.venue,
        timeframe=Timeframe(args.timeframe) if args.timeframe else None,
        file_format=args.input_format,
    )
    json_output = strategy_validation_candle_import_preflight_result_to_json(result)
    markdown_output = strategy_validation_candle_import_preflight_result_to_markdown(result)
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.format in {"json", "both"}:
            (output_dir / "candle_import_preflight.json").write_text(
                json_output,
                encoding="utf-8",
            )
        if args.format in {"markdown", "both"}:
            (output_dir / "candle_import_preflight.md").write_text(
                markdown_output,
                encoding="utf-8",
            )
    if args.format == "json":
        print(json_output, end="")
    elif args.format == "both":
        print(markdown_output)
        print(json_output, end="")
    else:
        print(markdown_output, end="")
    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
