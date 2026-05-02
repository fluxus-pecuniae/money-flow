"""Run a Money Flow research campaign evidence pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from core.config.settings import get_settings
from services.strategy_validation import (
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    audit_money_flow_research_campaign_data_readiness,
    load_money_flow_research_campaign_config,
    money_flow_research_campaign_data_readiness_to_dict,
    run_money_flow_research_campaign_sync,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a read-only Money Flow research campaign config and write an evidence pack. "
            "Campaign windows use candle closes in (start, end]: closes exactly at start "
            "are excluded and closes on or before end are included. This is research-only; "
            "it does not optimize, recommend, route, trade, or call exchange adapters."
        ),
    )
    parser.add_argument("--config", required=True, help="Path to a JSON campaign config.")
    parser.add_argument(
        "--output-dir",
        help="Optional evidence-pack root directory override. Defaults to config output_dir.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="both",
        help="Evidence report format to write. Default writes both JSON and Markdown.",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help=(
            "Inspect persisted candle coverage/readiness for the campaign and print JSON. "
            "Does not run strategy validation and writes no evidence pack."
        ),
    )
    parser.add_argument(
        "--collision-policy",
        choices=("unique_suffix", "fail_if_exists"),
        default=MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
        help=(
            "Evidence-pack directory collision policy. Default `unique_suffix` writes "
            "a new suffixed run directory instead of overwriting an existing pack."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_money_flow_research_campaign_config(Path(args.config))
    service = MoneyFlowBacktestService(get_settings())
    if args.audit_only:
        audit = audit_money_flow_research_campaign_data_readiness(config, service=service)
        print(
            json.dumps(
                money_flow_research_campaign_data_readiness_to_dict(audit),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = run_money_flow_research_campaign_sync(
        config,
        service=service,
        output_dir=args.output_dir,
        report_formats=("json", "markdown") if args.format == "both" else (args.format,),
        evidence_pack_collision_policy=args.collision_policy,
    )
    print(
        json.dumps(
            {
                "campaign_name": result.campaign_name,
                "evidence_pack_dir": str(result.evidence_pack_dir),
                "manifest": result.manifest,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
