"""SOR-EV1 evidence-only loss anatomy and variant diagnostics.

This module reads canonical SV2.0.2 Strategy Validation evidence packs and builds
founder-facing diagnostics. It intentionally does not import candles, call
exchange adapters, create live artifacts, or change production Money Flow rules.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Sequence

CANONICAL_SV202_TIMESTAMP = "20260512T064916Z"
CANONICAL_SV202_PATH_TOKEN = "money_flow_sv2_0_2_hyperliquid_public_"
CANONICAL_SYMBOLS: tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX")
CANONICAL_TIMEFRAMES: tuple[str, ...] = ("15m", "1h", "4h", "1d")
METHODOLOGIES: tuple[str, ...] = (
    "true_forward_replay",
    "completed_trade_overlay_estimate",
    "lookahead_diagnostic_proxy",
    "reporting_only_attribution",
    "deferred_requires_rejected_signal_replay",
)
FORBIDDEN_PRODUCTION_WORDS: tuple[str, ...] = (
    "proven",
    "optimal",
    "approved for live",
    "guaranteed",
    "ready for real trading",
)


@dataclass(frozen=True, slots=True)
class Scenario:
    key: str
    batch_path: str
    run_id: str
    symbol: str
    timeframe: str
    component_key: str
    fill_timing: str
    metrics: dict[str, Any]
    request: dict[str, Any]
    trades: list[dict[str, Any]]


def canonical_sv202_batch_report_paths(root: str | Path = ".") -> list[Path]:
    base = Path(root) / "reports" / "strategy_validation"
    return sorted(base.glob(f"{CANONICAL_SV202_PATH_TOKEN}*canonical_db_imported/{CANONICAL_SV202_TIMESTAMP}/batch_report.json"))


def build_sor_ev1_report(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in (batch_report_paths or canonical_sv202_batch_report_paths())]
    _assert_canonical_paths(paths)
    batches = [_load_json(path) for path in paths]
    scenarios = _flatten_scenarios(paths, batches)
    trades = [trade for scenario in scenarios for trade in scenario.trades]
    losing_trades = [trade for trade in trades if _dec(trade.get("net_pnl")) < 0]
    loss_rows = _loss_anatomy(losing_trades)
    variant_results = _variant_results(scenarios)
    baseline_rows = [_baseline_scenario_row(scenario) for scenario in scenarios]
    positives = _positive_control_pockets(baseline_rows)
    control = _control_pocket_impact(variant_results, positives)
    generated_at = generated_at or datetime.now(UTC)
    report = {
        "phase": "SOR-EV1",
        "generated_at": generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "evidence_only_loss_anatomy_ready_for_founder_review",
        "baseline_evidence_references": [str(path) for path in paths],
        "canonical_baseline": {
            "source": "SV2.0.2 canonical DB-imported evidence packs",
            "timestamp": CANONICAL_SV202_TIMESTAMP,
            "path_count": len(paths),
            "paths": [str(path) for path in paths],
            "symbols": list(CANONICAL_SYMBOLS),
            "timeframes": list(CANONICAL_TIMEFRAMES),
            "money_flow_version": "money_flow_v1_2",
            "capital_mode": "dynamic_equity_pct",
            "initial_equity_per_independent_scenario": "10000",
            "forbidden_sources_excluded": [
                "sv1_13_dynamic_equity_packs",
                "compact_sv2_rows",
                "pt0_0_3_aggregated_historical_replay",
                "dashboard_chart_data_json",
                "dashboard_date_filter_fresh_10k",
                "hyperliquid_testnet_prices",
            ],
        },
        "baseline_summary": _baseline_summary(baseline_rows),
        "worst_trades": loss_rows[:20],
        "loss_anatomy_summary": _loss_anatomy_summary(loss_rows),
        "big_red_candle_summary": _big_red_candle_summary(loss_rows),
        "late_entry_classifications": _late_entry_summary(loss_rows),
        "rsi_macd_rejection_summary": _rsi_macd_rejection_summary(scenarios),
        "variant_results": variant_results,
        "variant_summary": _variant_summary(variant_results),
        "candidate_variants": _candidate_variants(variant_results),
        "rejected_variants": _rejected_variants(variant_results),
        "methodology_labels": {label: _methodology_description(label) for label in METHODOLOGIES},
        "control_pocket_impact": control,
        "symbol_comparison": _comparison_by(baseline_rows, "symbol"),
        "timeframe_comparison": _comparison_by(baseline_rows, "timeframe"),
        "limitations": [
            "canonical_sv2_0_2_packs_do_not_include_full_per_candle_indicator_trace",
            "stop_variants_are_completed_trade_overlay_estimates_not_true_forward_replay",
            "rsi_macd_rejection_analysis_uses_pack_no_trade_counts_and_is_deferred_for_true_replay",
            "large_red_candle_attribution_requires_candle_payload_or_replay_context_for_exact_classification",
            "independent_scenarios_are_not_one_combined_account",
            "no_variant_is_approved_for_production_paper_or_live_trading",
        ],
        "boundary_flags": {
            "uses_only_canonical_sv2_0_2_pack_paths": True,
            "uses_dashboard_chart_data_as_canonical_evidence": False,
            "uses_dashboard_date_filter_recalculation": False,
            "uses_hyperliquid_testnet_prices": False,
            "changes_production_money_flow_rules": False,
            "optimizes_parameters_blindly": False,
            "approves_paper_trading": False,
            "approves_live_trading": False,
            "creates_orders": False,
            "calls_private_signed_or_order_endpoints": False,
            "adds_sor_fanout_cbbo_or_target_reselection": False,
        },
    }
    return report


def sor_ev1_report_to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# SOR-EV1 Money Flow Trade Loss Anatomy And Evidence-Only Variants",
        "",
        f"Recorded at: `{report['generated_at']}`",
        "",
        f"Status: `{report['status']}`",
        "",
        "SOR-EV1 is evidence-only research. It uses only the canonical SV2.0.2 DB-imported evidence packs as baseline truth. Production Money Flow rules are unchanged, no order endpoints are called, and no stop-loss or entry variant is approved.",
        "",
        "## Executive Summary",
        "",
        f"- Baseline source: `{report['canonical_baseline']['source']}` at `{report['canonical_baseline']['timestamp']}`.",
        f"- Canonical pack paths inspected: `{report['canonical_baseline']['path_count']}`.",
        f"- Baseline scenarios: `{report['baseline_summary']['scenario_count']}` independent runs, not one combined account.",
        f"- Baseline trades: `{report['baseline_summary']['trade_count']}`; losing trades: `{report['loss_anatomy_summary']['losing_trade_count']}`.",
        f"- Worst observed trade: `{report['loss_anatomy_summary']['worst_trade_label']}`.",
        "- Fixed-stop diagnostics reduced some completed-trade losses in overlay estimates, but these are not true-forward replay results and are not production candidates.",
        "- RSI/MACD rejected-entry admission remains deferred for true replay because the canonical packs do not contain full rejected-candle indicator traces.",
        "",
        "## Canonical SV2.0.2 Baseline Reference",
        "",
        "Allowed baseline: canonical SV2.0.2 evidence packs only.",
        "",
        "Forbidden inputs excluded: " + ", ".join(f"`{item}`" for item in report["canonical_baseline"]["forbidden_sources_excluded"]),
        "",
        "## Dataset / Evidence-Pack Source",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Timestamp | `{report['canonical_baseline']['timestamp']}` |",
        f"| Symbols | `{', '.join(report['canonical_baseline']['symbols'])}` |",
        f"| Timeframes | `{', '.join(report['canonical_baseline']['timeframes'])}` |",
        f"| Capital mode | `{report['canonical_baseline']['capital_mode']}` |",
        f"| Initial equity | `{report['canonical_baseline']['initial_equity_per_independent_scenario']}` per independent scenario |",
        "",
        "## Biggest Loss Anatomy",
        "",
        "| Rank | Symbol | TF | Fill | Entry | Exit | Bars | Entry | Exit Price | Net PnL | MAE | MFE | Entry Class | Exit Reason |",
        "|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in report["worst_trades"][:20]:
        lines.append(
            "| {loss_rank} | {symbol} | {timeframe} | `{fill_timing}` | {entry_time} | {exit_time} | {bars_held} | {entry_price} | {exit_price} | {net_pnl} | {max_adverse_excursion} | {max_favorable_excursion} | `{entry_timing_classification}` | `{exit_reason}` |".format(**row)
        )
    lines.extend([
        "",
        "## Large Red Candle / Adverse Move Analysis",
        "",
        "Exact red-candle attribution is limited because canonical SV2.0.2 batch reports do not embed full candle payloads. SOR-EV1 therefore uses completed-trade MAE as reporting-only adverse-move attribution and labels exact candle attribution as deferred unless a replay/candle trace is added.",
        "",
        "| Class | Count |",
        "|---|---:|",
    ])
    for key, value in sorted(report["big_red_candle_summary"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend([
        "",
        "## Late-Entry Analysis",
        "",
        "| Classification | Losing Trades |",
        "|---|---:|",
    ])
    for key, value in sorted(report["late_entry_classifications"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend([
        "",
        "## RSI / MACD Rejection Analysis",
        "",
        f"Status: `{report['rsi_macd_rejection_summary']['status']}`.",
        "",
        "| Rejection Reason | Count |",
        "|---|---:|",
    ])
    for key, value in sorted(report["rsi_macd_rejection_summary"].get("first_failed_reason_counts", {}).items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend([
        "",
        "## Variant Comparison Tables",
        "",
        "| Variant | Methodology | Outcome | Scenarios | Net PnL Delta Sum | Max DD Delta | Stop Exits | Avoided Losers | Missed Winners |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in report["variant_summary"]:
        lines.append(
            "| `{variant_id}` | `{methodology}` | `{outcome}` | {scenario_count} | {net_pnl_delta_sum} | {max_drawdown_delta} | {stop_exit_count} | {avoided_loser_count} | {missed_winner_count} |".format(**row)
        )
    lines.extend([
        "",
        "## Stop-Loss Evidence",
        "",
        "Fixed stops are completed-trade overlay estimates based on reported MAE. They can identify whether a stop might have capped an already observed loss, but they do not model changed position occupancy, later trades, intrabar fill quality, or exact stop execution.",
        "",
        "## Extension-Filter Evidence",
        "",
        "Extension-filter variants are marked `insufficient_data` because the canonical packs do not carry complete EMA10/SMA20 extension traces for every entry. They should be replayed with per-candle contexts before candidate review.",
        "",
        "## Control-Pocket Section",
        "",
        "Control pockets are positive baseline scenarios, including ETH 1h where present. A variant that helps weak sleeves but damages these controls is not a clean improvement.",
        "",
        "| Variant | Control Pockets | Improved | Preserved | Damaged |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in report["control_pocket_impact"]:
        lines.append(f"| `{row['variant_id']}` | {row['control_pocket_count']} | {row['improved']} | {row['preserved']} | {row['damaged']} |")
    lines.extend([
        "",
        "## Symbol Comparison",
        "",
        "| Symbol | Scenarios | Trades | Net PnL Sum | Positive Scenarios | Worst Drawdown |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["symbol_comparison"]:
        lines.append(f"| `{row['symbol']}` | {row['scenario_count']} | {row['trade_count']} | {row['net_pnl_sum']} | {row['positive_scenario_count']} | {row['worst_drawdown']} |")
    lines.extend([
        "",
        "## Timeframe Comparison",
        "",
        "| Timeframe | Scenarios | Trades | Net PnL Sum | Positive Scenarios | Worst Drawdown |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["timeframe_comparison"]:
        lines.append(f"| `{row['timeframe']}` | {row['scenario_count']} | {row['trade_count']} | {row['net_pnl_sum']} | {row['positive_scenario_count']} | {row['worst_drawdown']} |")
    lines.extend([
        "",
        "## Candidate Variants",
        "",
    ])
    if report["candidate_variants"]:
        lines.extend(f"- `{item}`" for item in report["candidate_variants"])
    else:
        lines.append("- None promoted from SOR-EV1. No overlay-only result is treated as candidate evidence.")
    lines.extend([
        "",
        "## Rejected / Deferred Variants",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["rejected_variants"])
    lines.extend([
        "",
        "## Methodology Labels",
        "",
    ])
    lines.extend(f"- `{key}`: {value}" for key, value in report["methodology_labels"].items())
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["limitations"])
    lines.extend([
        "",
        "## Recommended Next Evidence Phase",
        "",
        "Run a true-forward SOR-EV2 replay for the most promising stop logic using per-candle DB candles and position occupancy, then separately replay rejected-signal entry variants with explicit RSI/MACD contexts. Do not change production rules until a true-forward replay preserves control pockets and improves loss behavior under both `next_candle_open` and `next_candle_close` assumptions.",
        "",
        "## Boundary Confirmation",
        "",
    ])
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(report["boundary_flags"].items()))
    return "\n".join(lines).rstrip() + "\n"


def write_sor_ev1_outputs(report: dict[str, Any], markdown_path: str | Path, json_path: str | Path) -> None:
    markdown = sor_ev1_report_to_markdown(report)
    for forbidden in FORBIDDEN_PRODUCTION_WORDS:
        if forbidden in markdown.lower():
            raise ValueError(f"forbidden proof/live approval language present: {forbidden}")
    Path(markdown_path).write_text(markdown, encoding="utf-8")
    Path(json_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _assert_canonical_paths(paths: Sequence[Path]) -> None:
    if not paths:
        raise FileNotFoundError("No canonical SV2.0.2 batch_report.json paths found.")
    for path in paths:
        text = str(path)
        if CANONICAL_SV202_PATH_TOKEN not in text or CANONICAL_SV202_TIMESTAMP not in text:
            raise ValueError(f"noncanonical SOR-EV1 evidence path: {path}")
        forbidden_tokens = ("dashboard", "pt0_0_3", "sv1_13", "compact")
        if any(token in text.lower() for token in forbidden_tokens):
            raise ValueError(f"forbidden SOR-EV1 evidence source path: {path}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten_scenarios(paths: Sequence[Path], batches: Sequence[dict[str, Any]]) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for path, batch in zip(paths, batches, strict=True):
        for run in batch.get("run_reports", []):
            if run.get("status") != "completed" or not run.get("report"):
                continue
            report = run["report"]
            component = (report.get("component_reports") or [{}])[0]
            request = run.get("request") or {}
            assumptions = request.get("assumptions") or report.get("assumptions") or {}
            metrics = component.get("metrics") or report.get("aggregate_metrics") or {}
            symbol = str(report.get("symbol") or request.get("symbol"))
            timeframe = _canonical_timeframe(str(component.get("timeframe") or _component_to_timeframe(component.get("component_key"))))
            fill_timing = str(assumptions.get("fill_timing"))
            component_key = str(component.get("component_key") or (request.get("component_keys") or [""])[0])
            key = f"{symbol}:{timeframe}:{fill_timing}:{run.get('run_id')}"
            scenario = Scenario(
                key=key,
                batch_path=str(path),
                run_id=str(run.get("run_id")),
                symbol=symbol,
                timeframe=timeframe,
                component_key=component_key,
                fill_timing=fill_timing,
                metrics=metrics,
                request=request,
                trades=[_trade_with_context(trade, scenario_key=key, path=str(path), run=run, report=report, component=component) for trade in component.get("trades", [])],
            )
            scenarios.append(scenario)
    return scenarios


def _trade_with_context(trade: dict[str, Any], *, scenario_key: str, path: str, run: dict[str, Any], report: dict[str, Any], component: dict[str, Any]) -> dict[str, Any]:
    row = dict(trade)
    row["scenario_key"] = scenario_key
    row["batch_report_path"] = path
    row["run_id"] = run.get("run_id")
    row["symbol"] = row.get("symbol") or report.get("symbol")
    row["timeframe"] = _canonical_timeframe(str(row.get("timeframe") or component.get("timeframe")))
    row["component_key"] = row.get("component_key") or component.get("component_key")
    return row


def _loss_anatomy(losing_trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(losing_trades, key=lambda row: _dec(row.get("net_pnl")))
    rows: list[dict[str, Any]] = []
    for idx, trade in enumerate(ordered, start=1):
        timeframe = _canonical_timeframe(str(trade.get("timeframe")))
        bars = _bars_held(trade, timeframe)
        mae = _dec(trade.get("max_adverse_excursion"))
        notional = max(_dec(trade.get("entry_notional")), Decimal("0"))
        mae_pct = abs(mae) / notional if notional else Decimal("0")
        entry_class = _entry_timing_classification(trade, mae_pct)
        rows.append({
            "loss_rank": idx,
            "trade_id": str(trade.get("trade_id")),
            "scenario_key": str(trade.get("scenario_key")),
            "symbol": str(trade.get("symbol")),
            "timeframe": timeframe,
            "sleeve": str(trade.get("component_key")),
            "fill_timing": str(trade.get("fill_timing")),
            "entry_time": str(trade.get("entry_time")),
            "exit_time": str(trade.get("exit_time")),
            "bars_held": bars,
            "entry_price": _fmt(_dec(trade.get("entry_price"))),
            "exit_price": _fmt(_dec(trade.get("exit_price"))),
            "gross_pnl": _fmt(_dec(trade.get("gross_pnl"))),
            "net_pnl": _fmt(_dec(trade.get("net_pnl"))),
            "fees": _fmt(_dec(trade.get("fees"))),
            "slippage": _fmt(_dec(trade.get("slippage_cost"))),
            "equity_before_trade": _fmt(_dec(trade.get("equity_before_entry"))),
            "equity_after_trade": _fmt(_dec(trade.get("equity_after_exit"))),
            "drawdown_contribution": _fmt(abs(_dec(trade.get("net_pnl")))),
            "entry_reason_codes": [str(trade.get("entry_reason") or "money_flow_entry_passed_all_current_entry_rules")],
            "exit_reason_codes": [str(trade.get("exit_reason") or "unknown_exit_reason")],
            "exit_reason": str(trade.get("exit_reason") or "unknown_exit_reason"),
            "rsi_at_entry": None,
            "rsi_at_exit": None,
            "ema5_at_entry": None,
            "ema10_at_entry": None,
            "sma20_at_entry": None,
            "macd_at_entry": None,
            "macd_signal_at_entry": None,
            "macd_histogram_at_entry": None,
            "price_extension_from_ema5": None,
            "price_extension_from_ema10": None,
            "price_extension_from_sma20": None,
            "entry_candle_body_percent": None,
            "largest_adverse_candle_during_trade": None,
            "largest_adverse_candle_reason": "canonical_pack_candle_payload_unavailable",
            "max_adverse_excursion": _fmt(mae),
            "max_adverse_excursion_pct_of_entry_notional": _fmt(mae_pct),
            "max_favorable_excursion": _fmt(_dec(trade.get("max_favorable_excursion"))),
            "market_regime": str(trade.get("entry_market_regime") or "unknown"),
            "volatility_regime": str(trade.get("entry_volatility_regime") or "unknown"),
            "large_down_candle_classification": _large_adverse_classification(mae_pct),
            "entry_timing_classification": entry_class,
            "methodology": "reporting_only_attribution",
        })
    return rows


def _variant_results(scenarios: Sequence[Scenario]) -> list[dict[str, Any]]:
    variants = [
        ("fixed_stop_loss_pct_1", "completed_trade_overlay_estimate", Decimal("0.01")),
        ("fixed_stop_loss_pct_1_5", "completed_trade_overlay_estimate", Decimal("0.015")),
        ("fixed_stop_loss_pct_2", "completed_trade_overlay_estimate", Decimal("0.02")),
    ]
    rows: list[dict[str, Any]] = []
    for variant_id, methodology, pct in variants:
        for scenario in scenarios:
            rows.append(_fixed_stop_overlay(scenario, variant_id=variant_id, methodology=methodology, stop_pct=pct))
    for variant_id in (
        "atr_stop_1_5x",
        "atr_stop_2x",
        "recent_low_stop_lookback_5",
        "recent_low_stop_lookback_10",
        "large_bear_candle_exit",
        "macd_histogram_improving_entry",
        "macd_histogram_above_negative_threshold",
        "lower_rsi_trend_intact_entry",
        "reject_entry_if_price_too_far_above_ema10",
        "reject_entry_if_price_too_far_above_sma20",
        "avoid_sideways_low_volatility",
        "avoid_macd_flat_chop",
    ):
        for scenario in scenarios:
            rows.append(_deferred_variant_row(scenario, variant_id))
    return rows


def _fixed_stop_overlay(scenario: Scenario, *, variant_id: str, methodology: str, stop_pct: Decimal) -> dict[str, Any]:
    baseline_equity = _metric(scenario.metrics, "ending_equity")
    equity = Decimal("10000")
    curve = [equity]
    stop_exits = 0
    avoided_losers = 0
    missed_winners = 0
    adjusted_trades = []
    for trade in scenario.trades:
        baseline_net = _dec(trade.get("net_pnl"))
        entry_notional = _dec(trade.get("entry_notional"))
        mae = abs(_dec(trade.get("max_adverse_excursion")))
        trigger_loss = entry_notional * stop_pct
        adjusted_net = baseline_net
        stop_triggered = entry_notional > 0 and mae >= trigger_loss
        if stop_triggered:
            # Estimate stop loss net of the original reported fees/slippage. This is diagnostic only.
            adjusted_net = -trigger_loss - _dec(trade.get("fees")) - _dec(trade.get("slippage_cost"))
            stop_exits += 1
            if baseline_net < adjusted_net:
                avoided_losers += 1
            if baseline_net > 0 and adjusted_net < baseline_net:
                missed_winners += 1
        equity += adjusted_net
        curve.append(equity)
        adjusted_trades.append({"trade_id": trade.get("trade_id"), "baseline_net_pnl": _fmt(baseline_net), "variant_net_pnl": _fmt(adjusted_net), "stop_triggered": stop_triggered})
    max_dd = _max_drawdown(curve)
    net = equity - Decimal("10000")
    baseline_net = _metric(scenario.metrics, "net_account_pnl") or (baseline_equity - Decimal("10000"))
    baseline_dd = _metric(scenario.metrics, "mark_to_market_max_drawdown") or _metric(scenario.metrics, "max_drawdown")
    outcome = _outcome_taxonomy(equity, baseline_equity, max_dd, baseline_dd)
    return {
        "variant_id": variant_id,
        "methodology": methodology,
        "scenario_key": scenario.key,
        "symbol": scenario.symbol,
        "timeframe": scenario.timeframe,
        "component_key": scenario.component_key,
        "fill_timing": scenario.fill_timing,
        "baseline_ending_equity": _fmt(baseline_equity),
        "variant_ending_equity": _fmt(equity),
        "baseline_net_pnl": _fmt(baseline_net),
        "variant_net_pnl": _fmt(net),
        "net_pnl_delta": _fmt(net - baseline_net),
        "baseline_max_drawdown": _fmt(baseline_dd),
        "variant_max_drawdown": _fmt(max_dd),
        "max_drawdown_delta": _fmt(max_dd - baseline_dd),
        "trade_count": len(scenario.trades),
        "stop_exit_count": stop_exits,
        "early_exit_count": stop_exits,
        "avoided_loser_count": avoided_losers,
        "missed_winner_count": missed_winners,
        "outcome": outcome,
        "candidate_evidence": False,
        "production_approved": False,
        "limitations": ["completed_trade_overlay_estimate_not_true_forward_replay"],
        "adjusted_trades_sample": adjusted_trades[:20],
    }


def _deferred_variant_row(scenario: Scenario, variant_id: str) -> dict[str, Any]:
    methodology = "deferred_requires_rejected_signal_replay" if "macd" in variant_id or "rsi" in variant_id else "completed_trade_overlay_estimate"
    if variant_id.startswith("atr") or variant_id.startswith("recent_low") or variant_id == "large_bear_candle_exit":
        methodology = "deferred_requires_rejected_signal_replay"
    return {
        "variant_id": variant_id,
        "methodology": methodology,
        "scenario_key": scenario.key,
        "symbol": scenario.symbol,
        "timeframe": scenario.timeframe,
        "component_key": scenario.component_key,
        "fill_timing": scenario.fill_timing,
        "baseline_ending_equity": _fmt(_metric(scenario.metrics, "ending_equity")),
        "variant_ending_equity": _fmt(_metric(scenario.metrics, "ending_equity")),
        "baseline_net_pnl": _fmt(_metric(scenario.metrics, "net_account_pnl")),
        "variant_net_pnl": _fmt(_metric(scenario.metrics, "net_account_pnl")),
        "net_pnl_delta": "0",
        "baseline_max_drawdown": _fmt(_metric(scenario.metrics, "mark_to_market_max_drawdown")),
        "variant_max_drawdown": _fmt(_metric(scenario.metrics, "mark_to_market_max_drawdown")),
        "max_drawdown_delta": "0",
        "trade_count": len(scenario.trades),
        "stop_exit_count": 0,
        "early_exit_count": 0,
        "avoided_loser_count": 0,
        "missed_winner_count": 0,
        "outcome": "insufficient_data",
        "candidate_evidence": False,
        "production_approved": False,
        "limitations": ["requires_per_candle_indicator_or_candle_replay_context"],
        "adjusted_trades_sample": [],
    }


def _baseline_scenario_row(scenario: Scenario) -> dict[str, Any]:
    return {
        "scenario_key": scenario.key,
        "symbol": scenario.symbol,
        "timeframe": scenario.timeframe,
        "component_key": scenario.component_key,
        "fill_timing": scenario.fill_timing,
        "ending_equity": _fmt(_metric(scenario.metrics, "ending_equity")),
        "net_pnl": _fmt(_metric(scenario.metrics, "net_account_pnl")),
        "max_drawdown": _fmt(_metric(scenario.metrics, "mark_to_market_max_drawdown") or _metric(scenario.metrics, "max_drawdown")),
        "trade_count": int(_metric(scenario.metrics, "number_of_trades")),
        "win_rate": _fmt(_metric(scenario.metrics, "win_rate")),
        "profit_factor": _fmt(_metric(scenario.metrics, "profit_factor")),
        "average_win": _fmt(_metric(scenario.metrics, "average_win")),
        "average_loss": _fmt(_metric(scenario.metrics, "average_loss")),
        "largest_loss": _fmt(_metric(scenario.metrics, "worst_trade_net_pnl")),
        "largest_win": _fmt(_metric(scenario.metrics, "best_trade_net_pnl")),
        "total_fees": _fmt(_metric(scenario.metrics, "total_fees")),
        "total_slippage": _fmt(_metric(scenario.metrics, "total_slippage_cost")),
    }


def _baseline_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario_count": len(rows),
        "trade_count": sum(int(row["trade_count"]) for row in rows),
        "net_pnl_sum_across_independent_scenarios": _fmt(sum((_dec(row["net_pnl"]) for row in rows), Decimal("0"))),
        "positive_scenario_count": sum(1 for row in rows if _dec(row["ending_equity"]) > Decimal("10000")),
        "negative_scenario_count": sum(1 for row in rows if _dec(row["ending_equity"]) < Decimal("10000")),
        "methodology": "sum across independent research scenarios",
    }


def _variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant_id"]].append(row)
    output = []
    for variant_id, selected in sorted(grouped.items()):
        output.append({
            "variant_id": variant_id,
            "methodology": selected[0]["methodology"],
            "scenario_count": len(selected),
            "outcome": _rollup_outcome(selected),
            "net_pnl_delta_sum": _fmt(sum((_dec(row["net_pnl_delta"]) for row in selected), Decimal("0"))),
            "max_drawdown_delta": _fmt(max((_dec(row["max_drawdown_delta"]) for row in selected), default=Decimal("0"))),
            "stop_exit_count": sum(int(row["stop_exit_count"]) for row in selected),
            "early_exit_count": sum(int(row["early_exit_count"]) for row in selected),
            "avoided_loser_count": sum(int(row["avoided_loser_count"]) for row in selected),
            "missed_winner_count": sum(int(row["missed_winner_count"]) for row in selected),
            "candidate_evidence": any(row["candidate_evidence"] for row in selected),
        })
    return output


def _candidate_variants(rows: Sequence[dict[str, Any]]) -> list[str]:
    return sorted({row["variant_id"] for row in rows if row.get("candidate_evidence") is True})


def _rejected_variants(rows: Sequence[dict[str, Any]]) -> list[str]:
    grouped = _variant_summary(rows)
    return sorted(row["variant_id"] for row in grouped if row["outcome"] in {"insufficient_data", "rejected", "deteriorated_vs_baseline", "loss_reduced_but_still_below_starting_equity", "overfit_risk", "lower_drawdown_but_lower_return", "higher_return_but_higher_drawdown"})


def _control_pocket_impact(rows: Sequence[dict[str, Any]], controls: Sequence[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    control_set = set(controls)
    for row in rows:
        if row["scenario_key"] in control_set:
            grouped[row["variant_id"]].append(row)
    output = []
    for variant_id, selected in sorted(grouped.items()):
        improved = sum(1 for row in selected if _dec(row["variant_ending_equity"]) > _dec(row["baseline_ending_equity"]))
        damaged = sum(1 for row in selected if _dec(row["variant_ending_equity"]) < _dec(row["baseline_ending_equity"]))
        output.append({
            "variant_id": variant_id,
            "control_pocket_count": len(selected),
            "improved": improved,
            "preserved": len(selected) - improved - damaged,
            "damaged": damaged,
        })
    return output


def _positive_control_pockets(rows: Sequence[dict[str, Any]]) -> list[str]:
    return [row["scenario_key"] for row in rows if _dec(row["ending_equity"]) > Decimal("10000") or (row["symbol"] == "ETH" and row["timeframe"] == "1h")]


def _comparison_by(rows: Sequence[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    output = []
    for key, selected in sorted(grouped.items()):
        output.append({
            field: key,
            "scenario_count": len(selected),
            "trade_count": sum(int(row["trade_count"]) for row in selected),
            "net_pnl_sum": _fmt(sum((_dec(row["net_pnl"]) for row in selected), Decimal("0"))),
            "positive_scenario_count": sum(1 for row in selected if _dec(row["ending_equity"]) > Decimal("10000")),
            "worst_drawdown": _fmt(max((_dec(row["max_drawdown"]) for row in selected), default=Decimal("0"))),
        })
    return output


def _loss_anatomy_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    worst = rows[0] if rows else {}
    return {
        "losing_trade_count": len(rows),
        "worst_trade_id": worst.get("trade_id"),
        "worst_trade_label": f"{worst.get('symbol')} {worst.get('timeframe')} {worst.get('fill_timing')} {worst.get('net_pnl')}" if worst else "none",
        "total_losing_trade_pnl": _fmt(sum((_dec(row["net_pnl"]) for row in rows), Decimal("0"))),
        "top_20_loss_sum": _fmt(sum((_dec(row["net_pnl"]) for row in rows[:20]), Decimal("0"))),
    }


def _big_red_candle_summary(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    c = Counter(row["large_down_candle_classification"] for row in rows)
    c["exact_red_candle_classification_deferred"] += len(rows)
    return dict(c)


def _late_entry_summary(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(row["entry_timing_classification"] for row in rows))


def _rsi_macd_rejection_summary(scenarios: Sequence[Scenario]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for scenario in scenarios:
        metrics = scenario.metrics
        for key, value in (metrics.get("no_trade_reason_counts") or {}).items():
            counts[str(key)] += int(value)
    first_failed = Counter()
    for key, value in counts.items():
        if "rsi" in key:
            first_failed["rsi_not_constructive"] += value
        elif "macd" in key:
            first_failed["macd_not_constructive"] += value
        elif "extension" in key or "quality" in key:
            first_failed["entry_quality_not_constructive"] += value
        elif "history" in key:
            first_failed["insufficient_history"] += value
        else:
            first_failed["other"] += value
    return {
        "status": "deferred_requires_rejected_signal_replay",
        "methodology": "reporting_only_attribution",
        "reason": "canonical SV2.0.2 packs expose aggregate no-trade reason counts but not full rejected-candle indicator traces",
        "first_failed_reason_counts": dict(sorted(first_failed.items())),
        "raw_no_trade_reason_counts": dict(sorted(counts.items())),
    }


def _entry_timing_classification(trade: dict[str, Any], mae_pct: Decimal) -> str:
    regime = str(trade.get("entry_market_regime") or "").lower()
    if "sideways" in regime:
        return "chop_entry"
    if mae_pct >= Decimal("0.02"):
        return "late_extension_entry"
    if "uptrend" in regime:
        return "continuation_entry"
    return "unknown"


def _large_adverse_classification(mae_pct: Decimal) -> str:
    if mae_pct >= Decimal("0.03"):
        return "losses_from_large_down_candles"
    if mae_pct >= Decimal("0.015"):
        return "stop_would_have_helped"
    return "adverse_move_not_stop_solvable"


def _outcome_taxonomy(equity: Decimal, baseline_equity: Decimal, max_dd: Decimal, baseline_dd: Decimal) -> str:
    if equity > baseline_equity and equity > Decimal("10000"):
        return "improved_positive_vs_baseline"
    if equity > baseline_equity and equity <= Decimal("10000"):
        return "loss_reduced_but_still_below_starting_equity"
    if max_dd < baseline_dd and equity < baseline_equity:
        return "lower_drawdown_but_lower_return"
    if equity > baseline_equity and max_dd > baseline_dd:
        return "higher_return_but_higher_drawdown"
    if equity < baseline_equity:
        return "deteriorated_vs_baseline"
    return "no_op"


def _rollup_outcome(rows: Sequence[dict[str, Any]]) -> str:
    outcomes = Counter(str(row["outcome"]) for row in rows)
    if outcomes.get("insufficient_data") == len(rows):
        return "insufficient_data"
    if outcomes.get("deteriorated_vs_baseline", 0) > outcomes.get("improved_positive_vs_baseline", 0):
        return "deteriorated_vs_baseline"
    if outcomes.get("improved_positive_vs_baseline", 0):
        return "candidate_for_more_evidence" if any(row["methodology"] == "true_forward_replay" for row in rows) else "overfit_risk"
    if outcomes.get("loss_reduced_but_still_below_starting_equity", 0):
        return "loss_reduced_but_still_below_starting_equity"
    return outcomes.most_common(1)[0][0] if outcomes else "no_op"


def _methodology_description(label: str) -> str:
    return {
        "true_forward_replay": "Chronological replay that can be considered candidate evidence if baseline parity and controls hold.",
        "completed_trade_overlay_estimate": "Diagnostic adjustment to completed baseline trades; useful for hypothesis triage, not rule approval.",
        "lookahead_diagnostic_proxy": "Uses information unavailable at decision time; never candidate evidence.",
        "reporting_only_attribution": "Explains observed baseline trades without changing decisions.",
        "deferred_requires_rejected_signal_replay": "Needs per-candle rejected-signal replay before truthful testing.",
    }[label]


def _metric(metrics: dict[str, Any], key: str) -> Decimal:
    return _dec(metrics.get(key))


def _dec(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _fmt(value: Decimal) -> str:
    normalized = value.quantize(Decimal("0.00000001")) if value == value else Decimal("0")
    return format(normalized.normalize(), "f")


def _bars_held(trade: dict[str, Any], timeframe: str) -> int:
    seconds = int(_dec(trade.get("duration_seconds")))
    tf = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}.get(_canonical_timeframe(timeframe), 1)
    return max(1, round(seconds / tf)) if seconds else 0


def _max_drawdown(curve: Sequence[Decimal]) -> Decimal:
    peak = curve[0] if curve else Decimal("0")
    max_dd = Decimal("0")
    for point in curve:
        if point > peak:
            peak = point
        dd = peak - point
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _canonical_timeframe(value: str) -> str:
    return "1d" if value in {"1D", "Timeframe.D1", "d1"} else value.replace("Timeframe.", "").lower().replace("m15", "15m").replace("h1", "1h").replace("h4", "4h")


def _component_to_timeframe(component: Any) -> str:
    text = str(component or "")
    return text.replace("sleeve_", "")
