#!/usr/bin/env python
"""Run SV1.12.5 Hyperliquid public campaign seed/preflight/import workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.domain.enums import Environment
from services.strategy_validation.public_campaign_import import (
    PUBLIC_CAMPAIGN_CONFIG_PATH,
    run_strategy_validation_public_campaign_import,
    strategy_validation_public_campaign_import_result_to_json,
    strategy_validation_public_campaign_import_result_to_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Seed operator-approved research-only Hyperliquid identity and run the "
            "SV1.12.5 guarded public campaign import when all gates pass."
        )
    )
    parser.add_argument(
        "--campaign-config",
        default=str(PUBLIC_CAMPAIGN_CONFIG_PATH),
        help="Public campaign config path. Defaults to the SV1.12.4 Hyperliquid public YTD/recent campaign.",
    )
    parser.add_argument(
        "--manifest",
        default="configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json",
        help="Research-only Hyperliquid market identity manifest.",
    )
    parser.add_argument("--input", action="append", default=[], help="CSV input path; may be repeated.")
    parser.add_argument(
        "--input-dir",
        help="Directory containing the 9 public campaign CSV files. Defaults to campaign local_candle_output_dir.",
    )
    parser.add_argument(
        "--seed-identity",
        action="store_true",
        help="Seed market identity if operator verification flags are also supplied.",
    )
    parser.add_argument(
        "--operator-verified",
        action="store_true",
        help="Required for non-dry-run research identity seed writes.",
    )
    parser.add_argument(
        "--verified-by",
        help="Required operator/founder name for approved research identity seed writes.",
    )
    parser.add_argument(
        "--market-identity-values-checked-offline",
        action="store_true",
        help="Confirms the manifest values were checked offline before seed writes.",
    )
    parser.add_argument(
        "--regenerate-missing-public-candles",
        action="store_true",
        help="Fetch missing Hyperliquid public candleSnapshot CSV files. Public endpoint only; no API keys.",
    )
    parser.add_argument(
        "--environment",
        default=Environment.TESTNET.value,
        choices=[item.value for item in Environment],
        help="Candle import environment label.",
    )
    parser.add_argument("--venue", default="hyperliquid")
    parser.add_argument("--format", choices=("json", "markdown", "both"), default="markdown")
    parser.add_argument("--output-dir", help="Optional directory for deterministic report files.")
    args = parser.parse_args()

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=args.campaign_config,
        manifest_path=args.manifest,
        seed_identity=args.seed_identity,
        operator_verified=args.operator_verified,
        verified_by=args.verified_by,
        market_identity_values_checked_offline=args.market_identity_values_checked_offline,
        input_paths=tuple(args.input),
        input_dir=args.input_dir,
        regenerate_missing_public_candles=args.regenerate_missing_public_candles,
        environment=Environment(args.environment),
        venue=args.venue,
    )

    markdown = strategy_validation_public_campaign_import_result_to_markdown(result)
    json_text = strategy_validation_public_campaign_import_result_to_json(result)
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.format in {"markdown", "both"}:
            (output_dir / "strategy_validation_sv1_12_5_public_campaign_import_result.md").write_text(
                markdown,
                encoding="utf-8",
            )
        if args.format in {"json", "both"}:
            (output_dir / "strategy_validation_sv1_12_5_public_campaign_import_result.json").write_text(
                json_text,
                encoding="utf-8",
            )
    if args.format == "json":
        print(json_text, end="")
    elif args.format == "both":
        print(markdown)
        print(json_text, end="")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
