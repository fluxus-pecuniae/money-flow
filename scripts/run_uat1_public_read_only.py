#!/usr/bin/env python3
"""Run UAT1 public-read-only connectivity and universe resolution.

This script requires explicit public-read-only flags before any network call.
It never uses API keys, private endpoints, signed endpoints, or order endpoints.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.uat.public_read_only import (
    UAT1PublicReadOnlyMode,
    render_uat1_report,
    result_to_jsonable,
    run_uat1_public_read_only_check,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uat1-public-read-only", action="store_true")
    parser.add_argument("--allow-public-read-only-network", action="store_true")
    parser.add_argument("--runtime-mode", default="uat")
    parser.add_argument(
        "--output",
        default="docs/uat1_public_read_only_connectivity_and_top20_universe.md",
    )
    parser.add_argument(
        "--json-output",
        default="docs/uat1_public_read_only_connectivity_and_top20_universe_summary.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = UAT1PublicReadOnlyMode(
        runtime_mode=args.runtime_mode,
        uat1_public_read_only=args.uat1_public_read_only,
        allow_public_read_only_network=args.allow_public_read_only_network,
        private_endpoints_allowed=False,
        signed_endpoints_allowed=False,
        order_endpoints_allowed=False,
        api_keys_used=False,
    )
    if not mode.uat1_public_read_only or not mode.allow_public_read_only_network:
        raise SystemExit(
            "UAT1 public network calls require both --uat1-public-read-only "
            "and --allow-public-read-only-network."
        )

    result = run_uat1_public_read_only_check(mode=mode)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_uat1_report(result), encoding="utf-8")

    json_output_path = Path(args.json_output)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(
        json.dumps(result_to_jsonable(result), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
