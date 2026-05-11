"""Refresh the PT0 paper/sandbox runtime summary JSON.

Default mode is deterministic local summary generation. It does not call
network, private, signed, order, cancel, amend, retry, or live endpoints and
does not read credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.uat.pt0_runtime import write_pt0_runtime_summary


DEFAULT_OUTPUT = "docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json"
DEFAULT_UAT42_SUMMARY = "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json"
DEFAULT_UAT33_SUMMARY = "docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt_summary.json"
DEFAULT_UAT34_SUMMARY = "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="PT0 summary JSON output path.")
    parser.add_argument("--uat42-summary", default=DEFAULT_UAT42_SUMMARY)
    parser.add_argument("--uat33-summary", default=DEFAULT_UAT33_SUMMARY)
    parser.add_argument("--uat34-summary", default=DEFAULT_UAT34_SUMMARY)
    return parser.parse_args()


def _load_json(path: str) -> dict | None:
    source = Path(path)
    if not source.exists():
        return None
    return json.loads(source.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = write_pt0_runtime_summary(
        str(output),
        uat42_summary=_load_json(args.uat42_summary),
        uat33_summary=_load_json(args.uat33_summary),
        uat34_summary=_load_json(args.uat34_summary),
    )
    print(
        "wrote",
        output,
        "report=",
        summary["report"],
        "sandbox_orders_submitted_by_pt0=",
        summary["side_effect_flags"]["sandbox_orders_submitted_by_pt0"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
