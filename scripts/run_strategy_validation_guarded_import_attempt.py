#!/usr/bin/env python3
"""SV1.12.3 guarded canonical candle import attempt CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.domain.enums import Environment
from services.strategy_validation import (
    DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    run_strategy_validation_guarded_import_attempt,
    strategy_validation_guarded_import_attempt_result_to_json,
    strategy_validation_guarded_import_attempt_result_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Attempt the SV1.12.3 research-only guarded canonical candle import. "
            "Identity seeding requires explicit operator verification and offline "
            "market-value confirmation. Candle import runs only if all 18 canonical "
            "timezone-explicit files map one-to-one and pass requirement-aware preflight. "
            "This generates no evidence packs and calls no exchanges."
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
        help="Attempt research-only identity seed if verification gates are supplied.",
    )
    parser.add_argument(
        "--operator-verified",
        action="store_true",
        help="Assert the operator/founder verified market identity values offline.",
    )
    parser.add_argument(
        "--verified-by",
        help="Operator/reviewer identity required for non-dry-run identity seed.",
    )
    parser.add_argument(
        "--market-identity-values-checked-offline",
        action="store_true",
        help=(
            "Explicitly confirm instrument keys, symbols, market/product/assets, "
            "tick/step/min-size, decimals/leverage/constraints, and venue ids were "
            "checked offline before seed."
        ),
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Canonical candle file path. May be repeated.",
    )
    parser.add_argument(
        "--input-dir",
        help="Directory containing files named exactly as the SV1.12.2 suggested filenames.",
    )
    parser.add_argument(
        "--input-requirement-map",
        help="Optional JSON mapping input file paths to requirement identifiers or objects.",
    )
    parser.add_argument(
        "--environment",
        default=Environment.TESTNET.value,
        choices=tuple(item.value for item in Environment),
    )
    parser.add_argument("--venue", default="hyperliquid")
    parser.add_argument("--input-format", default="auto", choices=("auto", "csv", "json"))
    parser.add_argument(
        "--source-label-prefix",
        default="canonical_strategy_validation_candle_bundle",
    )
    parser.add_argument("--format", default="markdown", choices=("json", "markdown", "both"))
    parser.add_argument("--output-dir", help="Optional directory for result files.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_strategy_validation_guarded_import_attempt(
        manifest_path=args.manifest,
        seed_identity=args.seed_identity,
        operator_verified=args.operator_verified,
        verified_by=args.verified_by,
        market_identity_values_checked_offline=args.market_identity_values_checked_offline,
        input_paths=tuple(Path(path) for path in args.input),
        input_dir=Path(args.input_dir) if args.input_dir else None,
        input_requirement_map_path=(
            Path(args.input_requirement_map) if args.input_requirement_map else None
        ),
        environment=Environment(args.environment),
        venue=args.venue,
        file_format=args.input_format,
        source_label_prefix=args.source_label_prefix,
    )
    outputs: dict[str, str] = {}
    if args.format in {"json", "both"}:
        outputs["json"] = strategy_validation_guarded_import_attempt_result_to_json(result)
    if args.format in {"markdown", "both"}:
        outputs["md"] = strategy_validation_guarded_import_attempt_result_to_markdown(result)

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for suffix, content in outputs.items():
            (output_dir / f"strategy_validation_sv1_12_3_guarded_import_result.{suffix}").write_text(
                content,
                encoding="utf-8",
            )
    else:
        for content in outputs.values():
            print(content, end="")
    return 0 if result.final_status == "canonical_import_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
