"""Run SV1.17 Money Flow true replay experiment round one."""

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
    baseline_replay_variant,
    money_flow_true_replay_experiment_report_to_markdown,
    money_flow_true_replay_result_to_dict,
    sv117_round_one_variants,
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
        "--full-suite",
        action="store_true",
        help="Run BTC/ETH/SOL across sleeve_15m, sleeve_1h, and sleeve_4h.",
    )
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
        default="docs/strategy_validation_sv1_17_true_replay_experiments.md",
    )
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--summary-output", default=None)
    parser.add_argument("--format", choices=("markdown", "json", "both"), default="markdown")
    args = parser.parse_args()

    raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.full_suite:
        symbols = ["BTC", "ETH", "SOL"]
        components = ["sleeve_15m", "sleeve_1h", "sleeve_4h"]
    else:
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
                asyncio.run(
                    service.run_money_flow_true_replay(
                        request,
                        variant=baseline_replay_variant(),
                    )
                )
            )
            for variant in sv117_round_one_variants():
                variant_results.extend(
                    asyncio.run(
                        service.run_money_flow_true_replay(
                            request,
                            variant=variant,
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
        "boundary_flags": {
            "research_only": True,
            "changes_production_money_flow_rules": False,
            "optimizes_parameters": False,
            "approves_paper_trading": False,
            "creates_live_artifacts": False,
            "creates_routing_artifacts": False,
            "calls_exchange_adapters": False,
        },
    }
    payload["summary_rows"] = _summary_rows(payload)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.format in {"markdown", "both"}:
        output.write_text(
            money_flow_true_replay_experiment_report_to_markdown(
                baseline_results,
                variant_results,
            ),
            encoding="utf-8",
        )
    if args.format == "json":
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "both":
        json_output = Path(args.json_output) if args.json_output else output.with_suffix(".json")
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.summary_output:
        summary_output = Path(args.summary_output)
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_text(
            json.dumps(
                {
                    "report": "sv1_17_true_replay_experiment_summary",
                    "campaign_config_path": str(args.config),
                    "generated_at": datetime.now(UTC)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "summary_rows": payload["summary_rows"],
                    "boundary_flags": payload["boundary_flags"],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    return 0


def _summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    baseline_by_scenario: dict[tuple[str, str], Decimal] = {}
    rows: list[dict[str, object]] = []
    label_by_variant = {
        "baseline_current_money_flow_rules": "Baseline current Money Flow",
        "lower_rsi_floor_trend_intact_v1": "Lower RSI trend-intact v1",
        "lower_rsi_floor_trend_intact_v2_narrow": "Lower RSI narrow trend-intact",
        "lower_rsi_support_confirmed_v1": "Lower RSI support-confirmed",
        "lower_rsi_ema10_hold_no_resistance_v1": "Lower RSI EMA10 hold / no resistance",
    }
    baseline_results = payload["baseline_results"]
    variant_results = payload["variant_results"]
    assert isinstance(baseline_results, list)
    assert isinstance(variant_results, list)
    for result in baseline_results:
        request = result["request"]
        metrics = result["metrics"]
        key = (str(request["symbol"]), str(result["component_key"]))
        baseline_by_scenario[key] = Decimal(str(metrics["ending_equity"]))

    for result in [*baseline_results, *variant_results]:
        request = result["request"]
        metrics = result["metrics"]
        variant = result["variant"]
        summary = result.get("variant_summary", {})
        key = (str(request["symbol"]), str(result["component_key"]))
        ending_equity = Decimal(str(metrics["ending_equity"]))
        delta = ending_equity - baseline_by_scenario[key]
        variant_id = str(variant["variant_id"])
        if variant_id == "baseline_current_money_flow_rules":
            status = "baseline replay anchor"
        elif delta > 0:
            status = "improved vs baseline"
        elif delta == 0:
            status = "unchanged vs baseline"
        else:
            status = "deteriorated vs baseline"
        rows.append(
            {
                "id": variant_id,
                "label": label_by_variant.get(variant_id, variant_id),
                "symbol": key[0],
                "component": key[1],
                "methodology": str(variant["methodology"])
                + ("" if variant_id == "baseline_current_money_flow_rules" else "_research_only"),
                "contexts": len(result.get("contexts", [])),
                "trades": metrics["number_of_trades"],
                "endingEquity": metrics["ending_equity"],
                "netPnl": metrics["net_account_pnl"],
                "deltaVsBaseline": str(delta),
                "rejectedEntries": result["rejected_signal_summary"][
                    "baseline_entry_rejected_count"
                ],
                "variantCandidates": summary.get("variant_candidate_contexts", 0),
                "variantEntries": summary.get("variant_admitted_entry_count", 0),
                "nearSupportEntries": summary.get("variant_admitted_near_support_count", 0),
                "nearResistanceEntries": summary.get(
                    "variant_admitted_near_resistance_count", 0
                ),
                "fallingKnifeCandidates": summary.get(
                    "variant_candidate_falling_knife_risk_proxy_count", 0
                ),
                "winRate": metrics["win_rate"],
                "profitFactor": metrics["profit_factor"],
                "closedDrawdown": metrics["closed_trade_max_drawdown"],
                "markToMarketDrawdown": metrics["mark_to_market_max_drawdown"],
                "worstTrade": metrics.get("worst_trade_net_pnl") or "0",
                "status": status,
            }
        )
    return rows


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
