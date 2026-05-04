#!/usr/bin/env python3
"""SV1.12.2 identity and canonical candle-file readiness report CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.domain.enums import Environment, Timeframe
from services.strategy_validation import (
    DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    evaluate_strategy_validation_import_readiness,
    strategy_validation_import_readiness_to_json,
    strategy_validation_import_readiness_to_markdown,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Strategy Validation market identity and canonical candle-file readiness "
            "without importing candles or generating evidence packs."
        )
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MARKET_IDENTITY_MANIFEST_PATH),
        help="Market identity manifest path.",
    )
    parser.add_argument(
        "--seed-identity",
        action="store_true",
        help="Run the verified research-only market identity seed path.",
    )
    parser.add_argument(
        "--operator-verified",
        action="store_true",
        help="Assert the operator/founder verified manifest values before seed.",
    )
    parser.add_argument(
        "--verified-by",
        help="Operator/reviewer identity required when --seed-identity writes rows.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Timezone-explicit candle input file to preflight. May be repeated.",
    )
    parser.add_argument(
        "--requirements-from-review-json",
        help="Evidence-review JSON containing canonical candle import requirements.",
    )
    parser.add_argument(
        "--requirement-json",
        action="append",
        default=[],
        help="Requirement JSON path for requirement-aware preflight. May be repeated.",
    )
    parser.add_argument(
        "--input-requirement-map",
        help="JSON object mapping input paths to requirement indexes, identifiers, or objects.",
    )
    parser.add_argument("--environment", default=Environment.TESTNET.value)
    parser.add_argument("--venue", default="hyperliquid")
    parser.add_argument(
        "--timeframe",
        choices=[item.value for item in Timeframe],
        help="Optional row-level timeframe hint for supplied files.",
    )
    parser.add_argument("--file-format", default="auto", choices=("auto", "csv", "json"))
    parser.add_argument(
        "--format",
        default="markdown",
        choices=("json", "markdown", "both"),
        help="Output format.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional directory for readiness report files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = evaluate_strategy_validation_import_readiness(
        manifest_path=args.manifest,
        seed_identity=args.seed_identity,
        operator_verified=args.operator_verified,
        verified_by=args.verified_by,
        input_paths=tuple(args.input),
        requirements_from_review_json=args.requirements_from_review_json,
        requirement_json_paths=tuple(args.requirement_json),
        input_requirement_map_path=args.input_requirement_map,
        environment=args.environment,
        venue=args.venue,
        timeframe=Timeframe(args.timeframe) if args.timeframe else None,
        file_format=args.file_format,
    )
    outputs: dict[str, str] = {}
    if args.format in {"json", "both"}:
        outputs["json"] = strategy_validation_import_readiness_to_json(result)
    if args.format in {"markdown", "both"}:
        outputs["md"] = strategy_validation_import_readiness_to_markdown(result)

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for suffix, content in outputs.items():
            (output_dir / f"strategy_validation_sv1_12_2_import_readiness.{suffix}").write_text(
                content,
                encoding="utf-8",
            )
    else:
        for content in outputs.values():
            print(content, end="")
    return 0 if result.ready_for_sv1123_guarded_import else 1


if __name__ == "__main__":
    raise SystemExit(main())
