"""Guardedly import canonical Strategy Validation candle bundles."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from core.domain.enums import Environment, Timeframe
from services.strategy_validation import (
    guarded_import_strategy_validation_candle_bundle,
    strategy_validation_canonical_candle_bundle_import_result_to_json,
    strategy_validation_canonical_candle_bundle_import_result_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded canonical candle bundle import for Money Flow Strategy Validation. "
            "This imports only offline/public historical candles after intended DB, "
            "schema, operator-verified non-trading identity, complete one-to-one "
            "requirement-aware preflight, and exact coverage checks pass. It generates "
            "no evidence packs, calls no exchanges, routes nothing, and creates no "
            "paper/live artifacts."
        )
    )
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="CSV or JSON candle file to import after guardrails pass. May be repeated.",
    )
    parser.add_argument(
        "--requirements-from-review-json",
        help=(
            "Evidence-review JSON containing canonical_candle_import_requirements. "
            "For guarded import this is also used as the requirement source for "
            "one-to-one input mapping."
        ),
    )
    parser.add_argument(
        "--requirement-json",
        action="append",
        default=[],
        help="Requirement JSON object/list to reconcile against input files. May be repeated.",
    )
    parser.add_argument(
        "--input-requirement-map",
        help=(
            "JSON object mapping input file paths to requirement indexes, identifiers, "
            "or requirement objects."
        ),
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=tuple(item.value for item in Environment),
        help="Environment for imported candle rows.",
    )
    parser.add_argument("--venue", required=True, help="Venue/source for imported candles.")
    parser.add_argument(
        "--timeframe",
        choices=tuple(item.value for item in Timeframe),
        help="Optional common timeframe. Requirement-aware imports usually infer per file.",
    )
    parser.add_argument(
        "--input-format",
        choices=("auto", "csv", "json"),
        default="auto",
        help="Input file format. Default infers from file extension.",
    )
    parser.add_argument(
        "--source-label-prefix",
        default="canonical_strategy_validation_candle_bundle",
        help="Prefix for import summary source labels.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional directory for guarded import summary files; stdout is always written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = guarded_import_strategy_validation_candle_bundle(
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
        environment=Environment(args.environment),
        venue=args.venue,
        timeframe=Timeframe(args.timeframe) if args.timeframe else None,
        file_format=args.input_format,
        source_label_prefix=args.source_label_prefix,
    )
    json_output = strategy_validation_canonical_candle_bundle_import_result_to_json(result)
    markdown_output = strategy_validation_canonical_candle_bundle_import_result_to_markdown(
        result
    )
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.format in {"json", "both"}:
            (output_dir / "canonical_candle_import_status.json").write_text(
                json_output,
                encoding="utf-8",
            )
        if args.format in {"markdown", "both"}:
            (output_dir / "canonical_candle_import_status.md").write_text(
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
    return 0 if result.import_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
