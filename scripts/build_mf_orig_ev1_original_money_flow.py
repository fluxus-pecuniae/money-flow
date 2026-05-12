from __future__ import annotations

import argparse
from datetime import UTC, datetime

from services.strategy_validation.mf_orig_ev1 import (
    build_mf_orig_ev1_report_sync,
    write_mf_orig_ev1_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build MF-ORIG-EV1 original Money Flow reconstruction evidence."
    )
    parser.add_argument(
        "--markdown-output",
        default="docs/mf_orig_ev1_original_money_flow_reconstruction.md",
    )
    parser.add_argument(
        "--json-output",
        default="docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
    )
    parser.add_argument(
        "--spec-output",
        default="docs/mf_orig_ev1_original_money_flow_spec_and_gap_matrix.md",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Test/debug limiter only; omit for the full MF-ORIG-EV1 run.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = build_mf_orig_ev1_report_sync(
        generated_at=datetime.now(UTC),
        max_scenarios=args.max_scenarios,
    )
    write_mf_orig_ev1_outputs(
        report,
        args.markdown_output,
        args.json_output,
        args.spec_output,
    )
    print(f"wrote {args.markdown_output}")
    print(f"wrote {args.json_output}")
    print(f"wrote {args.spec_output}")


if __name__ == "__main__":
    main()
