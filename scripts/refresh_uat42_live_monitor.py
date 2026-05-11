"""Refresh the UAT4.2 dashboard monitor summary JSON.

Default mode is deterministic local summary generation. It does not call
network, private, signed, or order endpoints and does not read credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.uat.live_monitor import write_uat42_monitor_summary


DEFAULT_OUTPUT = "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json"
DEFAULT_UAT34_SUMMARY = "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Summary JSON output path.")
    parser.add_argument(
        "--uat34-summary",
        default=DEFAULT_UAT34_SUMMARY,
        help="Existing UAT3.4 routed-order ledger summary used for route/equity confirmation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    uat34_path = Path(args.uat34_summary)
    uat34_summary = None
    if uat34_path.exists():
        uat34_summary = json.loads(uat34_path.read_text(encoding="utf-8"))

    output.parent.mkdir(parents=True, exist_ok=True)
    summary = write_uat42_monitor_summary(str(output), uat34_summary=uat34_summary)
    print(
        "wrote",
        output,
        "report=",
        summary["report"],
        "order_endpoints_called=",
        summary["side_effect_flags"]["order_endpoints_called"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
