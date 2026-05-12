from __future__ import annotations

import argparse
from datetime import UTC, datetime

from services.strategy_validation.sor_ev3 import build_sor_ev3_report_sync, write_sor_ev3_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build SOR-EV3 avoid-sideways/low-volatility true-forward replay report.")
    parser.add_argument("--markdown-output", default="docs/sor_ev3_avoid_sideways_low_volatility.md")
    parser.add_argument("--json-output", default="docs/sor_ev3_avoid_sideways_low_volatility_summary.json")
    parser.add_argument("--max-scenarios", type=int, default=None, help="Test/debug limiter only; omit for full SOR-EV3.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = build_sor_ev3_report_sync(generated_at=datetime.now(UTC), max_scenarios=args.max_scenarios)
    write_sor_ev3_outputs(report, args.markdown_output, args.json_output)
    print(f"wrote {args.markdown_output}")
    print(f"wrote {args.json_output}")


if __name__ == "__main__":
    main()
