#!/usr/bin/env python3
"""Run UAT2 no-order Money Flow shadow observation.

The script requires explicit UAT2 shadow/public-read-only flags before any
public network call. It never uses API keys, private endpoints, signed
endpoints, order endpoints, or production trading artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from services.uat.shadow_run import (
    UAT2ShadowMode,
    render_uat2_report,
    run_uat2_shadow_strategy,
    save_uat2_result_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uat2-shadow-run", action="store_true")
    parser.add_argument("--shadow-only", action="store_true")
    parser.add_argument("--public-read-only", action="store_true")
    parser.add_argument("--allow-public-read-only-network", action="store_true")
    parser.add_argument("--runtime-mode", default="uat")
    parser.add_argument(
        "--component",
        action="append",
        choices=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
        help="Component to evaluate. Repeatable. Defaults to all Money Flow sleeves.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        help="Observation-universe symbol to evaluate. Repeatable. Defaults to all UAT1 included assets.",
    )
    parser.add_argument("--lookback-candles", type=int, default=80)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output", default="docs/uat2_shadow_strategy_top20_observation.md")
    parser.add_argument("--json-output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = UAT2ShadowMode(
        runtime_mode=args.runtime_mode,
        uat2_shadow_run=args.uat2_shadow_run,
        shadow_only=args.shadow_only,
        public_read_only=args.public_read_only,
        allow_public_read_only_network=args.allow_public_read_only_network,
        private_endpoints_allowed=False,
        signed_endpoints_allowed=False,
        order_endpoints_allowed=False,
        api_keys_used=False,
        order_submission_enabled=False,
        paper_trading_enabled=False,
        live_trading_enabled=False,
    )
    if not mode.explicit_and_safe:
        raise SystemExit(
            "UAT2 requires --uat2-shadow-run --shadow-only --public-read-only "
            "--allow-public-read-only-network with private/signed/order/API-key/paper/live paths disabled."
        )
    result = run_uat2_shadow_strategy(
        mode=mode,
        run_id=args.run_id,
        components=tuple(args.component) if args.component else None,
        symbols=tuple(args.symbol) if args.symbol else None,
        lookback_candles=args.lookback_candles,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_uat2_report(result), encoding="utf-8")
    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        save_uat2_result_json(result, str(json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
