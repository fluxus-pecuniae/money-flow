"""Run an SV1.1/SV1.2/SV1.2.1 comparative Money Flow validation batch."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from core.config.settings import get_settings
from core.domain.enums import Environment, StrategyFamily, StrategyValidationFillTiming
from core.domain.models import (
    StrategyValidationAssumptions,
    StrategyValidationBatchRequest,
    StrategyValidationRequest,
)
from services.strategy_validation import (
    MoneyFlowBacktestService,
    strategy_validation_batch_report_to_dict,
    strategy_validation_batch_report_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a read-only comparative Money Flow validation batch. The batch is "
            "descriptive research only and does not optimize, recommend, route, or execute."
        ),
    )
    parser.add_argument("--batch-name")
    parser.add_argument("--environment", default="testnet", choices=[item.value for item in Environment])
    parser.add_argument("--venue", required=True)
    parser.add_argument(
        "--symbol",
        action="append",
        required=True,
        help="Symbol to evaluate. Repeat for multiple symbols.",
    )
    parser.add_argument("--instrument-key", action="append", default=[])
    parser.add_argument("--instrument-ref-id", action="append", default=[])
    parser.add_argument(
        "--component",
        action="append",
        required=True,
        help="Money Flow component to evaluate. Repeat for multiple components.",
    )
    parser.add_argument(
        "--fill-timing",
        action="append",
        required=True,
        choices=[item.value for item in StrategyValidationFillTiming],
        help="Fill timing assumption to compare. Repeat for multiple fill timings.",
    )
    parser.add_argument(
        "--start",
        help=(
            "ISO-8601 start timestamp for a single candle-close window. "
            "Closes exactly at start are excluded."
        ),
    )
    parser.add_argument(
        "--end",
        help=(
            "ISO-8601 end timestamp for a single candle-close window. "
            "Closes on or before end are included."
        ),
    )
    parser.add_argument(
        "--window",
        action="append",
        default=[],
        help=(
            "Date window as start,end using candle closes in (start, end]. "
            "Repeat for multi-window regime/coverage comparison. "
            "If omitted, --start and --end are required."
        ),
    )
    parser.add_argument("--initial-capital", required=True, type=Decimal)
    parser.add_argument(
        "--fee-bps",
        action="append",
        required=True,
        type=Decimal,
        help="Fee bps assumption. Repeat to compare fee assumptions.",
    )
    parser.add_argument(
        "--slippage-bps",
        action="append",
        required=True,
        type=Decimal,
        help="Slippage bps assumption. Repeat to compare slippage assumptions.",
    )
    parser.add_argument("--position-notional-pct", default=Decimal("1.0"), type=Decimal)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="Optional output file path. Defaults to stdout.")
    return parser


def build_batch_request(args: argparse.Namespace) -> StrategyValidationBatchRequest:
    symbols = list(args.symbol)
    instrument_keys = _optional_values(args.instrument_key, len(symbols))
    instrument_ref_ids = _optional_values(args.instrument_ref_id, len(symbols))
    windows = _windows(args)
    runs: list[StrategyValidationRequest] = []
    for symbol_index, symbol in enumerate(symbols):
        for start_at, end_at in windows:
            for component in args.component:
                for fill_timing in args.fill_timing:
                    for fee_bps in args.fee_bps:
                        for slippage_bps in args.slippage_bps:
                            runs.append(
                                StrategyValidationRequest(
                                    strategy_family=StrategyFamily.MONEY_FLOW,
                                    environment=Environment(args.environment),
                                    venue=args.venue,
                                    symbol=symbol,
                                    instrument_key=instrument_keys[symbol_index],
                                    instrument_ref_id=instrument_ref_ids[symbol_index],
                                    component_keys=(component,),
                                    start_at=start_at,
                                    end_at=end_at,
                                    assumptions=StrategyValidationAssumptions(
                                        initial_capital=args.initial_capital,
                                        fee_bps=fee_bps,
                                        slippage_bps=slippage_bps,
                                        fill_timing=StrategyValidationFillTiming(fill_timing),
                                        position_notional_pct=args.position_notional_pct,
                                    ),
                                )
                            )
    return StrategyValidationBatchRequest(
        runs=tuple(runs),
        batch_name=args.batch_name,
    )


async def run(args: argparse.Namespace) -> str:
    service = MoneyFlowBacktestService(get_settings())
    report = await service.run_money_flow_batch_backtest(build_batch_request(args))
    if args.format == "markdown":
        return strategy_validation_batch_report_to_markdown(report)
    return json.dumps(strategy_validation_batch_report_to_dict(report), indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = asyncio.run(run(args))
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def _optional_values(values: list[str], expected_count: int) -> list[str | None]:
    if not values:
        return [None] * expected_count
    if len(values) != expected_count:
        raise SystemExit(
            "instrument-key / instrument-ref-id values must be omitted or repeated once per symbol."
        )
    return values


def _windows(args: argparse.Namespace) -> list[tuple[datetime, datetime]]:
    if args.window:
        windows: list[tuple[datetime, datetime]] = []
        for raw_window in args.window:
            parts = [part.strip() for part in raw_window.split(",", maxsplit=1)]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise SystemExit("--window must be formatted as start,end.")
            windows.append((_parse_datetime(parts[0]), _parse_datetime(parts[1])))
        return windows
    if not args.start or not args.end:
        raise SystemExit("--start and --end are required when --window is not supplied.")
    return [(_parse_datetime(args.start), _parse_datetime(args.end))]


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


if __name__ == "__main__":
    raise SystemExit(main())
