"""Seed or verify research-only market identity for Strategy Validation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from services.strategy_validation import (
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_market_identity_seed_result_to_json,
    strategy_validation_market_identity_seed_result_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Seed or verify offline/manual Hyperliquid perpetual USDC market identity "
            "for Money Flow Strategy Validation. This is research-only: it creates or "
            "verifies Instrument/Symbol rows, creates no candles, calls no exchanges, "
            "and creates no live trading artifacts."
        ),
    )
    parser.add_argument("--manifest", required=True, help="Market identity manifest path.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report intended inserts/updates without writing rows.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Require all manifest identity rows to already exist and match.",
    )
    parser.add_argument(
        "--operator-verified",
        action="store_true",
        help=(
            "Explicitly confirm the operator verified the offline manifest values. "
            "Required with --verified-by for non-dry-run writes."
        ),
    )
    parser.add_argument(
        "--verified-by",
        help="Operator/person/system label that verified the manifest values before writing.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional directory for summary files; stdout is always written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = seed_strategy_validation_market_identity_from_manifest(
        Path(args.manifest),
        dry_run=args.dry_run,
        verify_only=args.verify_only,
        operator_verified=args.operator_verified,
        verified_by=args.verified_by,
    )
    json_output = strategy_validation_market_identity_seed_result_to_json(result)
    markdown_output = strategy_validation_market_identity_seed_result_to_markdown(result)
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.format in {"json", "both"}:
            (output_dir / "market_identity_seed_summary.json").write_text(
                json_output,
                encoding="utf-8",
            )
        if args.format in {"markdown", "both"}:
            (output_dir / "market_identity_seed_summary.md").write_text(
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
    return 1 if result.conflicts or result.missing_required_symbols else 0


if __name__ == "__main__":
    raise SystemExit(main())
