"""Review canonical Money Flow campaign data readiness and evidence packs."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from core.config.settings import get_settings
from services.strategy_validation import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowBacktestService,
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_database_status_to_json,
    money_flow_evidence_review_database_status_to_markdown,
    money_flow_evidence_review_to_json,
    money_flow_evidence_review_to_markdown,
    review_money_flow_evidence,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only Money Flow evidence review. The review audits "
            "database target host/port/name, reachability, migration/schema status, candle-table truth, "
            "and canonical campaign configs; optionally writes evidence packs only "
            "when the DB target is clearly intended/non-maintenance and persisted candle data is sufficient; and never routes, trades, "
            "optimizes, or calls exchange adapters. Override DB_HOST, DB_PORT, "
            "DB_NAME, DB_USER, and DB_PASSWORD to point at the intended migrated "
            "Money Flow database."
        ),
    )
    parser.add_argument(
        "--db-status-only",
        action="store_true",
        help=(
            "Inspect the configured strategy-validation DB target, migration/schema "
            "status, required tables, candle-table existence, and persisted candle count only. This "
            "does not audit campaigns or generate evidence packs."
        ),
    )
    parser.add_argument(
        "--config",
        action="append",
        dest="configs",
        help=(
            "Campaign config path. May be repeated. Defaults to the canonical BTC "
            "and multi-symbol Money Flow campaign configs."
        ),
    )
    parser.add_argument(
        "--generate-evidence-packs",
        action="store_true",
        help=(
            "Generate collision-safe evidence packs for campaigns whose data-readiness "
            "audit has no missing, thin, or blocked rows. Default audits only."
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Optional evidence-pack root directory override for generated packs.",
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
    parser.add_argument(
        "--run-timestamp",
        help=(
            "Optional ISO-8601 timestamp used for generated evidence-pack run ids. "
            "Useful for reproducible review tests."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="markdown",
        help="Review summary output format. Default prints Markdown.",
    )
    parser.add_argument(
        "--review-output-dir",
        help=(
            "Optional directory for `money_flow_evidence_review.json` and/or `.md`. "
            "If omitted, the selected summary is printed to stdout."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = MoneyFlowBacktestService(get_settings())
    formats = ("json", "markdown") if args.format == "both" else (args.format,)
    if args.db_status_only:
        status = inspect_strategy_validation_database_status(service)
        if args.review_output_dir:
            output_dir = Path(args.review_output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            written: list[str] = []
            if "json" in formats:
                path = output_dir / "money_flow_strategy_validation_db_status.json"
                path.write_text(
                    money_flow_evidence_review_database_status_to_json(status),
                    encoding="utf-8",
                )
                written.append(str(path))
            if "markdown" in formats:
                path = output_dir / "money_flow_strategy_validation_db_status.md"
                path.write_text(
                    money_flow_evidence_review_database_status_to_markdown(status),
                    encoding="utf-8",
                )
                written.append(str(path))
            print("\n".join(written))
            return 0
        if args.format == "json":
            print(money_flow_evidence_review_database_status_to_json(status), end="")
            return 0
        if args.format == "both":
            print(money_flow_evidence_review_database_status_to_json(status), end="")
            print(money_flow_evidence_review_database_status_to_markdown(status), end="")
            return 0
        print(money_flow_evidence_review_database_status_to_markdown(status), end="")
        return 0

    config_paths = tuple(args.configs or CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS)
    review = review_money_flow_evidence(
        config_paths,
        service=service,
        output_dir=args.output_dir,
        generate_evidence_packs=args.generate_evidence_packs,
        run_timestamp=_parse_datetime(args.run_timestamp) if args.run_timestamp else None,
        evidence_pack_collision_policy=args.collision_policy,
    )
    if args.review_output_dir:
        output_dir = Path(args.review_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        if "json" in formats:
            path = output_dir / "money_flow_evidence_review.json"
            path.write_text(money_flow_evidence_review_to_json(review), encoding="utf-8")
            written.append(str(path))
        if "markdown" in formats:
            path = output_dir / "money_flow_evidence_review.md"
            path.write_text(money_flow_evidence_review_to_markdown(review), encoding="utf-8")
            written.append(str(path))
        print("\n".join(written))
        return 0
    if args.format == "json":
        print(money_flow_evidence_review_to_json(review), end="")
        return 0
    if args.format == "both":
        print(money_flow_evidence_review_to_json(review), end="")
        print(money_flow_evidence_review_to_markdown(review), end="")
        return 0
    print(money_flow_evidence_review_to_markdown(review), end="")
    return 0


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


if __name__ == "__main__":
    raise SystemExit(main())
