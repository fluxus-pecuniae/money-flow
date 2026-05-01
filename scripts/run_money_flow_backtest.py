"""Run an SV1.0 Money Flow strategy validation report from persisted candles."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from core.config.settings import get_settings
from core.domain.enums import Environment, StrategyFamily
from core.domain.models import StrategyValidationAssumptions, StrategyValidationRequest
from services.strategy_validation import (
    MoneyFlowBacktestService,
    strategy_validation_report_to_dict,
    strategy_validation_report_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a read-only Money Flow backtest over persisted candles.",
    )
    parser.add_argument("--environment", default="testnet", choices=[item.value for item in Environment])
    parser.add_argument("--venue", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--instrument-key")
    parser.add_argument("--instrument-ref-id")
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        help="Money Flow component to evaluate. Repeat for multiple components or use 'all'.",
    )
    parser.add_argument("--start", required=True, help="Inclusive ISO-8601 start timestamp.")
    parser.add_argument("--end", required=True, help="Inclusive ISO-8601 end timestamp.")
    parser.add_argument("--initial-capital", required=True, type=Decimal)
    parser.add_argument("--fee-bps", required=True, type=Decimal)
    parser.add_argument("--slippage-bps", required=True, type=Decimal)
    parser.add_argument("--position-notional-pct", default=Decimal("1.0"), type=Decimal)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="Optional output file path. Defaults to stdout.")
    return parser


def build_request(args: argparse.Namespace) -> StrategyValidationRequest:
    return StrategyValidationRequest(
        strategy_family=StrategyFamily.MONEY_FLOW,
        environment=Environment(args.environment),
        venue=args.venue,
        symbol=args.symbol,
        instrument_key=args.instrument_key,
        instrument_ref_id=args.instrument_ref_id,
        component_keys=tuple(args.component or ("all",)),
        start_at=_parse_datetime(args.start),
        end_at=_parse_datetime(args.end),
        assumptions=StrategyValidationAssumptions(
            initial_capital=args.initial_capital,
            fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps,
            position_notional_pct=args.position_notional_pct,
        ),
    )


async def run(args: argparse.Namespace) -> str:
    service = MoneyFlowBacktestService(get_settings())
    report = await service.run_money_flow_backtest(build_request(args))
    if args.format == "markdown":
        return strategy_validation_report_to_markdown(report)
    return json.dumps(strategy_validation_report_to_dict(report), indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = asyncio.run(run(args))
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


if __name__ == "__main__":
    raise SystemExit(main())
