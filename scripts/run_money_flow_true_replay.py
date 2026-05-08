"""Run SV1.16 Money Flow rejected-signal true replay diagnostics."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from core.domain.enums import (
    Environment,
    StrategyFamily,
    StrategyValidationCapitalSizingMode,
    StrategyValidationFillTiming,
)
from core.domain.models import StrategyValidationAssumptions, StrategyValidationRequest
from services.strategy_validation.replay import (
    MoneyFlowVariantReplayService,
    lower_rsi_floor_trend_intact_variant,
    money_flow_replay_report_to_markdown,
    money_flow_true_replay_result_to_dict,
)

DEFAULT_PUBLIC_CAMPAIGN_CONFIG = Path(
    "configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_PUBLIC_CAMPAIGN_CONFIG))
    parser.add_argument("--symbol", action="append", default=None)
    parser.add_argument("--component", action="append", default=None)
    parser.add_argument(
        "--fill-timing",
        default=StrategyValidationFillTiming.NEXT_CANDLE_OPEN.value,
        choices=[item.value for item in StrategyValidationFillTiming],
    )
    parser.add_argument("--fee-bps", default="5")
    parser.add_argument("--slippage-bps", default="3")
    parser.add_argument("--initial-capital", default="10000")
    parser.add_argument("--position-notional-pct", default="1.0")
    parser.add_argument(
        "--output",
        default="docs/strategy_validation_sv1_16_rejected_signal_replay.md",
    )
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--format", choices=("markdown", "json", "both"), default="markdown")
    args = parser.parse_args()

    raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
    symbols = args.symbol or ["ETH"]
    components = args.component or ["sleeve_1h"]
    baseline_results = []
    variant_results = []
    service = MoneyFlowVariantReplayService()
    for symbol in symbols:
        symbol_row = _symbol_row(raw, symbol)
        for component in components:
            window = _window_row(raw, component)
            request = StrategyValidationRequest(
                strategy_family=StrategyFamily.MONEY_FLOW,
                environment=Environment(raw["environment"]),
                venue=str(raw["venue"]),
                symbol=str(symbol_row["symbol"]),
                instrument_key=str(symbol_row["instrument_key"]),
                component_keys=(component,),
                start_at=_parse_utc(str(window["start"])),
                end_at=_parse_utc(str(window["end"])),
                assumptions=StrategyValidationAssumptions(
                    initial_capital=Decimal(args.initial_capital),
                    fee_bps=Decimal(args.fee_bps),
                    slippage_bps=Decimal(args.slippage_bps),
                    position_notional_pct=Decimal(args.position_notional_pct),
                    capital_sizing_mode=StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT,
                    fill_timing=StrategyValidationFillTiming(args.fill_timing),
                ),
            )
            baseline_results.extend(
                asyncio.run(service.run_money_flow_true_replay(request))
            )
            variant_results.extend(
                asyncio.run(
                    service.run_money_flow_true_replay(
                        request,
                        variant=lower_rsi_floor_trend_intact_variant(),
                    )
                )
            )

    payload = {
        "campaign_config_path": str(args.config),
        "baseline_results": [
            money_flow_true_replay_result_to_dict(result) for result in baseline_results
        ],
        "variant_results": [
            money_flow_true_replay_result_to_dict(result) for result in variant_results
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.format in {"markdown", "both"}:
        output.write_text(
            money_flow_replay_report_to_markdown(baseline_results, variant_results),
            encoding="utf-8",
        )
    if args.format == "json":
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "both":
        json_output = Path(args.json_output) if args.json_output else output.with_suffix(".json")
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0


def _symbol_row(raw: dict[str, object], symbol: str) -> dict[str, object]:
    for row in raw.get("symbols", []):
        if isinstance(row, dict) and row.get("symbol") == symbol:
            return row
    raise SystemExit(f"symbol not found in campaign config: {symbol}")


def _window_row(raw: dict[str, object], component: str) -> dict[str, object]:
    for row in raw.get("timeframe_windows", []):
        if isinstance(row, dict) and row.get("component") == component:
            return row
    raise SystemExit(f"component window not found in campaign config: {component}")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise SystemExit(f"timestamp must be timezone-explicit: {value}")
    return parsed.astimezone(UTC)


if __name__ == "__main__":
    raise SystemExit(main())
