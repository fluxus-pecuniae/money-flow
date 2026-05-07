"""Money Flow trade-anatomy diagnostics for Strategy Validation.

This module is intentionally descriptive. It reads generated Strategy
Validation research reports and optional historical candles, then summarizes
trade anatomy and market-structure context without changing strategy rules.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlalchemy import select

from core.domain.enums import Environment, Timeframe
from core.domain.models import Candle
from db.models import CandleModel, InstrumentModel
from db.session import SessionLocal
from services.indicators.service import DefaultIndicatorService

DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS: tuple[Path, ...] = (
    Path(
        "reports/strategy_validation/"
        "money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_15m/"
        "20260507T104500Z/batch_report.json"
    ),
    Path(
        "reports/strategy_validation/"
        "money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_1h/"
        "20260507T104500Z/batch_report.json"
    ),
    Path(
        "reports/strategy_validation/"
        "money_flow_hyperliquid_public_ytd_recent_dynamic_equity_sleeve_4h/"
        "20260507T104500Z/batch_report.json"
    ),
)

MARKET_STRUCTURE_LOOKBACK_CANDLES = 20
NEAR_SWING_THRESHOLD_PCT = 0.005
NEAR_RESISTANCE_THRESHOLD_PCT = 0.01

FORBIDDEN_LIVE_ARTIFACT_NAMES: tuple[str, ...] = (
    "MandateDesiredTrade",
    "StrategyDecision",
    "SignalEvent",
    "OrderIntent",
    "PreparedVenueOrder",
    "ExecutionReadinessAssessment",
    "SubmittedOrder",
)


@dataclass(frozen=True, slots=True)
class LoadedCandle:
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def build_money_flow_trade_anatomy_diagnostics(
    batch_report_paths: Sequence[str | Path] = DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
    *,
    candles_by_symbol_timeframe: dict[tuple[str, str], Sequence[LoadedCandle]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic founder-review diagnostics payload."""

    batch_reports = _load_batch_reports(batch_report_paths)
    run_rows = _flatten_run_rows(batch_reports)
    trade_rows = _flatten_trade_rows(run_rows)
    candles_by_symbol_timeframe = candles_by_symbol_timeframe or {}
    indicator_features = _build_indicator_features(candles_by_symbol_timeframe)

    for trade in trade_rows:
        trade["entry_reason_normalized"] = (
            trade.get("entry_reason") or "money_flow_entry_passed_all_current_entry_rules"
        )
        trade["market_structure"] = _market_structure_context(
            trade,
            candles_by_symbol_timeframe.get((str(trade.get("symbol")), str(trade.get("timeframe"))), ()),
        )
        trade["entry_indicators"] = indicator_features.get(
            (
                str(trade.get("symbol")),
                str(trade.get("timeframe")),
                _parse_datetime(str(trade.get("entry_signal_time") or trade.get("entry_time"))),
            ),
            {},
        )

    component_summaries = [
        _component_summary(component, [trade for trade in trade_rows if trade.get("component_key") == component], run_rows)
        for component in sorted({str(row["component_key"]) for row in run_rows})
    ]
    eth_1h = _eth_1h_anatomy(trade_rows, run_rows)
    weakness = _weak_component_anatomy(component_summaries, trade_rows, run_rows)
    market_structure = _market_structure_summary(trade_rows)
    hypotheses = _rule_change_hypotheses(component_summaries, eth_1h, weakness, market_structure)

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Hyperliquid USDC perpetual public-candle research diagnostics only",
        "batch_report_paths": [str(Path(path)) for path in batch_report_paths],
        "current_strategy_logic": current_money_flow_strategy_logic(),
        "component_summaries": component_summaries,
        "eth_1h_anatomy": eth_1h,
        "weak_component_anatomy": weakness,
        "market_structure_diagnostics": market_structure,
        "rule_change_hypotheses_for_later_testing": hypotheses,
        "boundary_flags": {
            "changes_money_flow_rules": False,
            "optimizes_parameters": False,
            "creates_live_artifacts": False,
            "creates_paper_trading_artifacts": False,
            "creates_routing_artifacts": False,
            "calls_exchange_adapters": False,
            "calls_private_exchange_endpoints": False,
            "calls_signed_exchange_endpoints": False,
            "calls_exchange_order_endpoints": False,
            "market_structure_used_as_entry_filter": False,
            "regime_used_as_entry_filter": False,
        },
        "limitations": [
            "diagnostics_read_existing_research_reports_and_candles_only",
            "market_structure_metrics_are_descriptive_not_entry_or_exit_filters",
            "separate_research_scenarios_are_not_one_combined_account",
            "paper_trading_design_remains_deferred",
            "hyperliquid_usdc_perpetual_scope_only",
        ],
    }


def load_candles_for_batch_reports(
    batch_report_paths: Sequence[str | Path] = DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
    *,
    session_factory: Any = SessionLocal,
) -> dict[tuple[str, str], list[LoadedCandle]]:
    """Load persisted candles needed by the supplied batch reports."""

    reports = _load_batch_reports(batch_report_paths)
    requirements: set[tuple[str, str, str, str, str]] = set()
    for run in _flatten_run_rows(reports):
        request = run["request"]
        requirements.add(
            (
                str(request.get("environment", "testnet")),
                str(request.get("venue", "hyperliquid")),
                str(request.get("symbol")),
                str(run.get("timeframe")),
                str(request.get("instrument_key")),
            )
        )

    output: dict[tuple[str, str], list[LoadedCandle]] = {}
    with session_factory() as session:
        for environment, venue, symbol, timeframe, instrument_key in sorted(requirements):
            instrument_ref_id = session.scalar(
                select(InstrumentModel.id).where(InstrumentModel.instrument_key == instrument_key)
            )
            query = (
                select(CandleModel)
                .where(
                    CandleModel.environment == Environment(environment),
                    CandleModel.venue == venue,
                    CandleModel.symbol == symbol,
                    CandleModel.timeframe == Timeframe(timeframe),
                )
                .order_by(CandleModel.close_time.asc())
            )
            if instrument_ref_id is not None:
                query = query.where(CandleModel.instrument_ref_id == instrument_ref_id)
            rows = session.scalars(query).all()
            output[(symbol, timeframe)] = [
                LoadedCandle(
                    symbol=row.symbol,
                    timeframe=str(row.timeframe.value),
                    open_time=_coerce_utc(row.open_time),
                    close_time=_coerce_utc(row.close_time),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.volume),
                )
                for row in rows
            ]
    return output


def money_flow_trade_anatomy_to_markdown(report: dict[str, Any]) -> str:
    """Render founder-readable Strategy Validation trade-anatomy diagnostics."""

    logic = report["current_strategy_logic"]
    lines: list[str] = [
        "# SV1.14 Money Flow Trade Anatomy And Market-Structure Diagnostics",
        "",
        f"Recorded at: `{report['generated_at']}`",
        "",
        "Status: `diagnostic_founder_review_ready`",
        "",
        "This report is diagnostic only. No Money Flow rules changed, no parameters were optimized, "
        "no market-structure filters were added, no routing/execution artifacts were created, and paper/live "
        "trading remains deferred.",
        "",
        "Scope: Hyperliquid USDC perpetual public-candle research only. Separate research scenarios are not one combined account.",
        "",
        "## Current Money Flow Rule Logic",
        "",
        "### Readiness Gates",
        "",
    ]
    lines.extend(f"- `{gate}`" for gate in logic["readiness_gates"])
    lines.extend(
        [
            "",
            "### Entry Rules",
            "",
            "- Entry requires `EMA5 > EMA10 > SMA20`.",
            "- RSI must sit inside the configured sleeve band and below the overbought threshold.",
            "- MACD must be constructive when the sleeve requires confirmation.",
            "- Entry quality must be either controlled pullback or continuation quality.",
            "- Price cannot be too extended above EMA5.",
            "- The strategy currently does not enter long when RSI is below the sleeve floor.",
            "- It is not a buy-deep-oversold-weakness system; it is a constructive momentum / controlled pullback system.",
            "",
            "### Exit / Reduce / Hold Rules",
            "",
        ]
    )
    lines.extend(f"- `{rule}`" for rule in logic["exit_reduce_hold_rules"])
    lines.extend(
        [
            "",
            "### Market Structure Boundary",
            "",
            "Market-structure diagnostics in this report are descriptive only. Recent swing highs/lows, support/resistance proximity, "
            "and breakout context are not currently used as Money Flow entry or exit filters.",
            "",
            "## Component Trade Anatomy",
            "",
            "| Component | Runs | Trades | Avg Duration | Avg MAE | Avg MFE | Net Account PnL Sum Across Runs | Ending Equity Range | Most Common Exit | Main No-Trade Reason |",
            "|---|---:|---:|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in report["component_summaries"]:
        lines.append(
            "| {component} | {runs} | {trades} | {duration} | {mae} | {mfe} | {pnl} | {equity_range} | {exit_reason} | {no_trade} |".format(
                component=row["component_key"],
                runs=row["completed_run_count"],
                trades=row["trade_count"],
                duration=_format_duration(row["average_trade_duration_seconds"]),
                mae=_money(row["average_adverse_excursion"]),
                mfe=_money(row["average_favorable_excursion"]),
                pnl=_money(row["sum_net_account_pnl_across_runs"]),
                equity_range=f"{_money(row['minimum_ending_equity'])} to {_money(row['maximum_ending_equity'])}",
                exit_reason=row["most_common_exit_reason"],
                no_trade=row["most_common_no_trade_reason"],
            )
        )
    lines.extend(
        [
            "",
            "### Entry / Exit Reason Diagnostics",
            "",
        ]
    )
    for row in report["component_summaries"]:
        lines.extend(
            [
                f"#### {row['component_key']}",
                "",
                f"- Entry reason distribution: `{_inline_counts(row['entry_reason_distribution'])}`",
                f"- Exit reason distribution: `{_inline_counts(row['exit_reason_distribution'])}`",
                f"- No-trade reason distribution: `{_inline_counts(row['no_trade_reason_distribution'])}`",
                f"- Invalid reason distribution: `{_inline_counts(row['invalid_reason_distribution'])}`",
                f"- Net PnL by entry reason: `{_inline_money(row['net_pnl_by_entry_reason'])}`",
                f"- Net PnL by exit reason: `{_inline_money(row['net_pnl_by_exit_reason'])}`",
                f"- Best trade: `{_trade_label(row['best_trade'])}`",
                f"- Worst trade: `{_trade_label(row['worst_trade'])}`",
                "",
            ]
        )

    eth = report["eth_1h_anatomy"]
    lines.extend(
        [
            "## ETH 1h Winning Anatomy",
            "",
            "ETH `sleeve_1h` is the clearest positive pocket in the dynamic-equity evidence, but it remains a research observation for founder review.",
            "",
            "| Fill | Fee bps | Slip bps | Ending Equity | Net Account PnL | Trades | Win Rate | Profit Factor | MTM Drawdown |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in eth["scenario_rows"]:
        lines.append(
            f"| `{row['fill_timing']}` | {row['fee_bps']} | {row['slippage_bps']} | {_money(row['ending_equity'])} | "
            f"{_money(row['net_account_pnl'])} | {row['trade_count']} | {_pct(row['win_rate'])} | "
            f"{_number(row['profit_factor'])} | {_money(row['mark_to_market_drawdown'])} |"
        )
    lines.extend(
        [
            "",
            f"- Top winning trades: `{'; '.join(_trade_label(trade) for trade in eth['top_winning_trades'])}`",
            f"- Worst losing trades: `{'; '.join(_trade_label(trade) for trade in eth['worst_losing_trades'])}`",
            f"- Entry features on ETH 1h winners: `{_inline_stats(eth['winner_entry_feature_summary'])}`",
            f"- Entry features on ETH 1h losers: `{_inline_stats(eth['loser_entry_feature_summary'])}`",
            f"- Exit reasons on ETH 1h winners: `{_inline_counts(eth['winner_exit_reason_distribution'])}`",
            f"- Exit reasons on ETH 1h losers: `{_inline_counts(eth['loser_exit_reason_distribution'])}`",
            f"- Trade duration distribution: `{_inline_counts(eth['trade_duration_distribution'])}`",
            f"- Regime contribution: `{_inline_money(eth['regime_net_pnl'])}`",
            "- Founder question preserved: is the 1h pocket broad Money Flow behavior, or mostly one ETH window/sleeve pocket?",
            "",
            "## 15m Losing Anatomy",
            "",
        ]
    )
    sleeve15 = report["weak_component_anatomy"].get("sleeve_15m", {})
    lines.extend(_weak_component_markdown(sleeve15, "15m"))
    lines.extend(["", "## 4h Losing Anatomy", ""])
    sleeve4h = report["weak_component_anatomy"].get("sleeve_4h", {})
    lines.extend(_weak_component_markdown(sleeve4h, "4h"))

    structure = report["market_structure_diagnostics"]
    lines.extend(
        [
            "",
            "## Market-Structure Diagnostics",
            "",
            f"Definition: recent swing high/low use the prior `{structure['lookback_candles']}` candles before entry. "
            "Support/resistance proximity is descriptive and not used by the strategy.",
            "",
            "| Component | Trades With Context | Near Recent High | Near Recent Low | Breakout Context | Nearby Resistance | Median Distance To Swing High | Median Distance To Swing Low |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in structure["by_component"]:
        lines.append(
            f"| {row['component_key']} | {row['trades_with_context']} | {row['near_recent_high_count']} | "
            f"{row['near_recent_low_count']} | {row['breakout_context_count']} | {row['nearby_resistance_count']} | "
            f"{_pct(row['median_distance_to_recent_swing_high_pct'])} | {_pct(row['median_distance_to_recent_swing_low_pct'])} |"
        )
    lines.extend(
        [
            "",
            "## Rule-Change Hypotheses For Later Testing",
            "",
            "| Hypothesis | Applies To | Reason | Expected Benefit | Risk | Prove / Disprove Metric |",
            "|---|---|---|---|---|---|",
        ]
    )
    for hypothesis in report["rule_change_hypotheses_for_later_testing"]:
        lines.append(
            f"| {hypothesis['hypothesis']} | {hypothesis['applies_to']} | {hypothesis['reason']} | "
            f"{hypothesis['expected_benefit']} | {hypothesis['risk']} | {hypothesis['metric_to_test']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary Confirmation",
            "",
        ]
    )
    for key, value in report["boundary_flags"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Next Diagnostic Work",
            "",
            "- Controlled tests can later evaluate the hypotheses above, one change at a time.",
            "- Paper-trading design remains deferred until the founder manually accepts a later scoped design phase.",
            "- Live execution remains outside Strategy Validation.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def current_money_flow_strategy_logic() -> dict[str, Any]:
    return {
        "readiness_gates": [
            "strategy_family_enabled",
            "sleeve_enabled",
            "instrument_active",
            "instrument_strategy_eligible",
            "market_data_fresh",
            "indicators_available",
            "latest_candle_available",
            "enough_history",
            "valid_instrument_mapping",
        ],
        "entry_rules": [
            "EMA5 > EMA10 > SMA20",
            "RSI inside the sleeve band",
            "RSI below overbought",
            "MACD constructive when required",
            "pullback or continuation quality",
            "price not too extended above EMA5",
        ],
        "rsi_lower_floor_truth": "strategy_does_not_enter_long_when_rsi_is_below_sleeve_floor",
        "strategy_style": "constructive_momentum_controlled_pullback_not_deep_oversold_weakness",
        "exit_reduce_hold_rules": [
            "ma_alignment_break_close",
            "trend_invalidated_close",
            "macd_rollover_close",
            "trim_on_overbought_rsi_reduce",
            "hold_when_no_exit_condition_is_active",
        ],
        "market_structure_filter_status": "not_currently_used_as_entry_or_exit_filter",
        "confidence_score_status": "context_only_not_authorization",
    }


def write_money_flow_trade_anatomy_report(
    report: dict[str, Any],
    output_path: str | Path,
    *,
    json_output_path: str | Path | None = None,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(money_flow_trade_anatomy_to_markdown(report), encoding="utf-8")
    if json_output_path is not None:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _load_batch_reports(paths: Sequence[str | Path]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in paths:
        report_path = Path(path)
        if not report_path.exists():
            continue
        reports.append(json.loads(report_path.read_text(encoding="utf-8")))
    if not reports:
        raise FileNotFoundError("No Strategy Validation batch reports were found for trade anatomy diagnostics.")
    return reports


def _flatten_run_rows(batch_reports: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in batch_reports:
        for run in batch.get("run_reports", []):
            if run.get("status") != "completed" or not run.get("report"):
                continue
            report = run["report"]
            request = run.get("request", {})
            component_report = (report.get("component_reports") or [{}])[0]
            metrics = component_report.get("metrics", {})
            assumptions = request.get("assumptions") or report.get("assumptions", {})
            rows.append(
                {
                    "batch_name": batch.get("batch_name"),
                    "run_id": run.get("run_id"),
                    "request": request,
                    "report": report,
                    "component_report": component_report,
                    "component_key": component_report.get("component_key") or (request.get("component_keys") or ["unknown"])[0],
                    "timeframe": component_report.get("timeframe"),
                    "symbol": report.get("symbol") or request.get("symbol"),
                    "fill_timing": assumptions.get("fill_timing"),
                    "fee_bps": assumptions.get("fee_bps"),
                    "slippage_bps": assumptions.get("slippage_bps"),
                    "metrics": metrics,
                    "no_trade_reason_counts": component_report.get("no_trade_reason_counts") or metrics.get("no_trade_reason_counts") or {},
                    "invalid_reason_counts": component_report.get("invalid_reason_counts") or metrics.get("invalid_reason_counts") or {},
                }
            )
    return rows


def _flatten_trade_rows(run_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    for run in run_rows:
        for trade in run["component_report"].get("trades", []):
            row = dict(trade)
            row.setdefault("component_key", run["component_key"])
            row.setdefault("timeframe", run["timeframe"])
            row.setdefault("symbol", run["symbol"])
            row["run_id"] = run["run_id"]
            row["fill_timing"] = run["fill_timing"]
            row["fee_bps"] = run["fee_bps"]
            row["slippage_bps"] = run["slippage_bps"]
            trades.append(row)
    return trades


def _component_summary(component: str, trades: Sequence[dict[str, Any]], run_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    component_runs = [run for run in run_rows if run["component_key"] == component]
    exit_reasons = Counter(_reason(trade.get("exit_reason"), "open_or_forced_hold") for trade in trades)
    entry_reasons = Counter(str(trade.get("entry_reason_normalized")) for trade in trades)
    no_trade_counts: Counter[str] = Counter()
    invalid_counts: Counter[str] = Counter()
    for run in component_runs:
        no_trade_counts.update({str(k): int(v) for k, v in run["no_trade_reason_counts"].items()})
        invalid_counts.update({str(k): int(v) for k, v in run["invalid_reason_counts"].items()})
    ending_equities = [_float(run["metrics"].get("ending_equity")) for run in component_runs if run["metrics"].get("ending_equity") is not None]
    return {
        "component_key": component,
        "completed_run_count": len(component_runs),
        "trade_count": len(trades),
        "average_trade_duration_seconds": _average(_float(trade.get("duration_seconds")) for trade in trades),
        "entry_reason_distribution": dict(sorted(entry_reasons.items())),
        "exit_reason_distribution": dict(sorted(exit_reasons.items())),
        "no_trade_reason_distribution": dict(sorted(no_trade_counts.items())),
        "invalid_reason_distribution": dict(sorted(invalid_counts.items())),
        "win_loss_by_entry_reason": _win_loss_by_reason(trades, "entry_reason_normalized"),
        "win_loss_by_exit_reason": _win_loss_by_reason(trades, "exit_reason"),
        "net_pnl_by_entry_reason": _net_pnl_by_reason(trades, "entry_reason_normalized"),
        "net_pnl_by_exit_reason": _net_pnl_by_reason(trades, "exit_reason"),
        "average_adverse_excursion": _average(_float(trade.get("max_adverse_excursion")) for trade in trades),
        "average_favorable_excursion": _average(_float(trade.get("max_favorable_excursion")) for trade in trades),
        "best_trade": _selected_trade(trades, highest=True),
        "worst_trade": _selected_trade(trades, highest=False),
        "sum_net_account_pnl_across_runs": _sum(_float(run["metrics"].get("net_account_pnl") or run["metrics"].get("net_pnl")) for run in component_runs),
        "minimum_ending_equity": min(ending_equities) if ending_equities else 0.0,
        "maximum_ending_equity": max(ending_equities) if ending_equities else 0.0,
        "most_common_exit_reason": _most_common(exit_reasons),
        "most_common_no_trade_reason": _most_common(no_trade_counts),
        "cost_drag": _sum(_float(run["metrics"].get("total_fees")) + _float(run["metrics"].get("total_slippage_cost")) for run in component_runs),
    }


def _eth_1h_anatomy(trades: Sequence[dict[str, Any]], run_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    eth_trades = [
        trade
        for trade in trades
        if trade.get("symbol") == "ETH" and trade.get("component_key") == "sleeve_1h"
    ]
    eth_runs = [
        run
        for run in run_rows
        if run["symbol"] == "ETH" and run["component_key"] == "sleeve_1h"
    ]
    winners = [trade for trade in eth_trades if _float(trade.get("net_pnl")) > 0]
    losers = [trade for trade in eth_trades if _float(trade.get("net_pnl")) <= 0]
    return {
        "scenario_rows": [
            {
                "fill_timing": run["fill_timing"],
                "fee_bps": run["fee_bps"],
                "slippage_bps": run["slippage_bps"],
                "ending_equity": _float(run["metrics"].get("ending_equity")),
                "net_account_pnl": _float(run["metrics"].get("net_account_pnl") or run["metrics"].get("net_pnl")),
                "trade_count": int(_float(run["metrics"].get("number_of_trades"))),
                "win_rate": _float(run["metrics"].get("win_rate")),
                "profit_factor": _float(run["metrics"].get("profit_factor")),
                "mark_to_market_drawdown": _float(run["metrics"].get("mark_to_market_max_drawdown")),
            }
            for run in sorted(eth_runs, key=lambda row: (str(row["fill_timing"]), _float(row["fee_bps"]), _float(row["slippage_bps"])))
        ],
        "top_winning_trades": [_compact_trade(trade) for trade in sorted(winners, key=lambda item: _float(item.get("net_pnl")), reverse=True)[:5]],
        "worst_losing_trades": [_compact_trade(trade) for trade in sorted(losers, key=lambda item: _float(item.get("net_pnl")))[:5]],
        "winner_entry_feature_summary": _entry_feature_summary(winners),
        "loser_entry_feature_summary": _entry_feature_summary(losers),
        "winner_exit_reason_distribution": dict(Counter(_reason(trade.get("exit_reason"), "unknown") for trade in winners)),
        "loser_exit_reason_distribution": dict(Counter(_reason(trade.get("exit_reason"), "unknown") for trade in losers)),
        "trade_duration_distribution": dict(Counter(_duration_bucket(_float(trade.get("duration_seconds"))) for trade in eth_trades)),
        "regime_net_pnl": _net_pnl_by_reason(eth_trades, "entry_market_regime"),
    }


def _weak_component_anatomy(
    component_summaries: Sequence[dict[str, Any]],
    trades: Sequence[dict[str, Any]],
    run_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for component in ("sleeve_15m", "sleeve_4h"):
        summary = next((row for row in component_summaries if row["component_key"] == component), None)
        component_trades = [trade for trade in trades if trade.get("component_key") == component]
        component_runs = [run for run in run_rows if run["component_key"] == component]
        if summary is None:
            continue
        output[component] = {
            "component_key": component,
            "trade_count": summary["trade_count"],
            "cost_drag": summary["cost_drag"],
            "ma_break_exit_count": summary["exit_reason_distribution"].get("ma_alignment_break", 0),
            "macd_rollover_exit_count": summary["exit_reason_distribution"].get("macd_rollover", 0),
            "average_trade_duration_seconds": summary["average_trade_duration_seconds"],
            "average_win_rate_across_runs": _average(_float(run["metrics"].get("win_rate")) for run in component_runs),
            "worst_trade_group": [_compact_trade(trade) for trade in sorted(component_trades, key=lambda item: _float(item.get("net_pnl")))[:5]],
            "likely_chop_or_whipsaw": summary["exit_reason_distribution"].get("ma_alignment_break", 0) + summary["exit_reason_distribution"].get("macd_rollover", 0),
            "most_common_no_trade_reason": summary["most_common_no_trade_reason"],
            "interpretation": _weak_component_interpretation(component, summary),
        }
    return output


def _market_structure_summary(trades: Sequence[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for component in sorted({str(trade.get("component_key")) for trade in trades}):
        contexts = [trade["market_structure"] for trade in trades if trade.get("component_key") == component and trade.get("market_structure", {}).get("context_available")]
        rows.append(
            {
                "component_key": component,
                "trades_with_context": len(contexts),
                "near_recent_high_count": sum(1 for ctx in contexts if ctx["near_recent_high"]),
                "near_recent_low_count": sum(1 for ctx in contexts if ctx["near_recent_low"]),
                "breakout_context_count": sum(1 for ctx in contexts if ctx["breakout_context"]),
                "nearby_resistance_count": sum(1 for ctx in contexts if ctx["nearby_resistance"]),
                "median_distance_to_recent_swing_high_pct": _median(ctx["distance_to_recent_swing_high_pct"] for ctx in contexts),
                "median_distance_to_recent_swing_low_pct": _median(ctx["distance_to_recent_swing_low_pct"] for ctx in contexts),
            }
        )
    return {
        "lookback_candles": MARKET_STRUCTURE_LOOKBACK_CANDLES,
        "near_swing_threshold_pct": NEAR_SWING_THRESHOLD_PCT,
        "near_resistance_threshold_pct": NEAR_RESISTANCE_THRESHOLD_PCT,
        "used_as_entry_filter": False,
        "by_component": rows,
    }


def _rule_change_hypotheses(
    component_summaries: Sequence[dict[str, Any]],
    eth_1h: dict[str, Any],
    weakness: dict[str, Any],
    market_structure: dict[str, Any],
) -> list[dict[str, str]]:
    del component_summaries, eth_1h, weakness, market_structure
    return [
        {
            "hypothesis": "avoid entries too close to recent resistance",
            "applies_to": "15m and 4h continuation entries",
            "reason": "diagnostics can show entries clustered near recent swing highs or nearby resistance",
            "expected_benefit": "reduce whipsaw entries that have little room before resistance",
            "risk": "may remove valid continuation trades in strong trends",
            "metric_to_test": "net account PnL, trade count, win rate, MAE/MFE, and missed-run opportunity versus baseline",
        },
        {
            "hypothesis": "require higher-low context before pullback entries",
            "applies_to": "BTC/SOL 1h and 15m pullback-style entries",
            "reason": "current rules validate EMA/RSI/MACD but do not inspect local swing structure",
            "expected_benefit": "favor constructive pullbacks over weak rebounds",
            "risk": "adds lag and may over-filter ETH-like pockets",
            "metric_to_test": "scenario-level dynamic ending equity, drawdown, and no-trade reason expansion",
        },
        {
            "hypothesis": "test ATR or recent-low risk invalidation",
            "applies_to": "4h and large-drawdown 1h trades",
            "reason": "current exits wait for MA/trend/MACD deterioration and may react slowly",
            "expected_benefit": "limit large adverse excursions",
            "risk": "can stop out trades before recovery and increase churn",
            "metric_to_test": "closed-trade drawdown, mark-to-market drawdown, worst trade, and net account PnL versus baseline",
        },
        {
            "hypothesis": "avoid 15m trades in sideways/choppy regimes",
            "applies_to": "sleeve_15m",
            "reason": "15m evidence is negative across tested dynamic scenarios and likely pays repeated cost/chop drag",
            "expected_benefit": "reduce high-frequency weak trades and cost exposure",
            "risk": "regime labeling may be unstable and can remove valid early trend entries",
            "metric_to_test": "fee/slippage cost drag, trade count, whipsaw exits, and dynamic ending equity",
        },
        {
            "hypothesis": "limit 4h entries when price is extended from EMA10/SMA20",
            "applies_to": "sleeve_4h",
            "reason": "4h signals may arrive late relative to the tested public window",
            "expected_benefit": "reduce late trend entries and large drawdown trades",
            "risk": "can under-participate in durable trends",
            "metric_to_test": "entry extension distribution, trade duration, drawdown, and net account PnL",
        },
        {
            "hypothesis": "separate pullback entries from continuation entries in reporting and later tests",
            "applies_to": "all components",
            "reason": "current evidence stores successful entries under one passed-rule condition",
            "expected_benefit": "identify whether one entry style carries most favorable excursion",
            "risk": "requires added attribution before rule changes are justified",
            "metric_to_test": "MFE/MAE, exit reasons, and scenario-level ending equity by entry style",
        },
    ]


def _build_indicator_features(
    candles_by_symbol_timeframe: dict[tuple[str, str], Sequence[LoadedCandle]],
) -> dict[tuple[str, str, datetime], dict[str, float | None]]:
    output: dict[tuple[str, str, datetime], dict[str, float | None]] = {}
    service = DefaultIndicatorService()
    for (symbol, timeframe), rows in candles_by_symbol_timeframe.items():
        domain_candles = [
            Candle(
                instrument_key=None,
                instrument_ref_id=None,
                venue="hyperliquid",
                symbol=row.symbol,
                timeframe=Timeframe(row.timeframe),
                open_time=row.open_time,
                close_time=row.close_time,
                open=Decimal(str(row.open)),
                high=Decimal(str(row.high)),
                low=Decimal(str(row.low)),
                close=Decimal(str(row.close)),
                volume=Decimal(str(row.volume)),
            )
            for row in rows
        ]
        for candle, snapshot in zip(domain_candles, service._compute_snapshots(domain_candles), strict=False):
            output[(symbol, timeframe, _coerce_utc(snapshot.as_of))] = {
                "rsi_14": _optional_float(snapshot.rsi_14),
                "ema_5": _optional_float(snapshot.ema_5),
                "ema_10": _optional_float(snapshot.ema_10),
                "sma_20": _optional_float(snapshot.sma_20),
                "macd_histogram": _optional_float(snapshot.macd_histogram),
                "ema_extension_pct": (
                    ((float(candle.close) / float(snapshot.ema_5)) - 1.0)
                    if snapshot.ema_5
                    else None
                ),
            }
    return output


def _market_structure_context(
    trade: dict[str, Any],
    candles: Sequence[LoadedCandle],
) -> dict[str, Any]:
    entry_time = _parse_datetime(str(trade.get("entry_signal_time") or trade.get("entry_time")))
    prior = [candle for candle in candles if candle.close_time < entry_time]
    if len(prior) < MARKET_STRUCTURE_LOOKBACK_CANDLES:
        return {"context_available": False, "reason": "insufficient_prior_candles"}
    window = prior[-MARKET_STRUCTURE_LOOKBACK_CANDLES:]
    entry_price = _float(trade.get("entry_price"))
    swing_high = max(candle.high for candle in window)
    swing_low = min(candle.low for candle in window)
    distance_high = (swing_high - entry_price) / entry_price if entry_price else 0.0
    distance_low = (entry_price - swing_low) / entry_price if entry_price else 0.0
    return {
        "context_available": True,
        "recent_swing_high": swing_high,
        "recent_swing_low": swing_low,
        "distance_to_recent_swing_high_pct": distance_high,
        "distance_to_recent_swing_low_pct": distance_low,
        "near_recent_high": abs(distance_high) <= NEAR_SWING_THRESHOLD_PCT,
        "near_recent_low": abs(distance_low) <= NEAR_SWING_THRESHOLD_PCT,
        "breakout_context": entry_price > swing_high,
        "nearby_resistance": 0 <= distance_high <= NEAR_RESISTANCE_THRESHOLD_PCT,
        "stop_like_invalidation_below_recent_low_descriptive_only": (
            abs(_float(trade.get("max_adverse_excursion"))) >= max(entry_price - swing_low, 0)
        ),
    }


def _entry_feature_summary(trades: Sequence[dict[str, Any]]) -> dict[str, float]:
    return {
        "avg_rsi_14": _average(_optional_float(trade.get("entry_indicators", {}).get("rsi_14")) for trade in trades),
        "avg_ema_extension_pct": _average(_optional_float(trade.get("entry_indicators", {}).get("ema_extension_pct")) for trade in trades),
        "avg_macd_histogram": _average(_optional_float(trade.get("entry_indicators", {}).get("macd_histogram")) for trade in trades),
    }


def _weak_component_interpretation(component: str, summary: dict[str, Any]) -> str:
    if component == "sleeve_15m":
        return (
            "15m weakness appears consistent with many trades, repeated cost drag, and frequent fast invalidation/chop exits. "
            "This is a diagnostic observation, not a rule change."
        )
    return (
        "4h weakness appears consistent with sparse slower signals, larger adverse excursion, and late invalidation risk in the tested window. "
        "This is a diagnostic observation, not a rule change."
    )


def _weak_component_markdown(row: dict[str, Any], label: str) -> list[str]:
    if not row:
        return [f"No {label} rows were available."]
    return [
        f"- Trade count across scenarios: `{row['trade_count']}`",
        f"- Cost drag from fees/slippage: `{_money(row['cost_drag'])}`",
        f"- MA break exits: `{row['ma_break_exit_count']}`",
        f"- MACD rollover exits: `{row['macd_rollover_exit_count']}`",
        f"- Average trade duration: `{_format_duration(row['average_trade_duration_seconds'])}`",
        f"- Average win rate across runs: `{_pct(row['average_win_rate_across_runs'])}`",
        f"- Worst trade group: `{'; '.join(_trade_label(trade) for trade in row['worst_trade_group'])}`",
        f"- Whipsaw/chop proxy count: `{row['likely_chop_or_whipsaw']}`",
        f"- Main no-trade reason: `{row['most_common_no_trade_reason']}`",
        f"- Interpretation: {row['interpretation']}",
    ]


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _coerce_utc(parsed)


def _float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: Iterable[float | None]) -> float:
    clean = [value for value in values if value is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def _sum(values: Iterable[float]) -> float:
    return sum(values)


def _median(values: Iterable[float]) -> float:
    clean = sorted(values)
    if not clean:
        return 0.0
    midpoint = len(clean) // 2
    if len(clean) % 2:
        return clean[midpoint]
    return (clean[midpoint - 1] + clean[midpoint]) / 2


def _reason(value: Any, fallback: str) -> str:
    return str(value or fallback)


def _most_common(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return counter.most_common(1)[0][0]


def _win_loss_by_reason(trades: Sequence[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0})
    for trade in trades:
        reason = _reason(trade.get(key), "unknown")
        bucket = "wins" if _float(trade.get("net_pnl")) > 0 else "losses"
        output[reason][bucket] += 1
    return dict(sorted(output.items()))


def _net_pnl_by_reason(trades: Sequence[dict[str, Any]], key: str) -> dict[str, float]:
    output: defaultdict[str, float] = defaultdict(float)
    for trade in trades:
        output[_reason(trade.get(key), "unknown")] += _float(trade.get("net_pnl"))
    return dict(sorted(output.items()))


def _selected_trade(trades: Sequence[dict[str, Any]], *, highest: bool) -> dict[str, Any]:
    if not trades:
        return {}
    return _compact_trade(sorted(trades, key=lambda trade: _float(trade.get("net_pnl")), reverse=highest)[0])


def _compact_trade(trade: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_id": trade.get("trade_id"),
        "symbol": trade.get("symbol"),
        "component_key": trade.get("component_key"),
        "fill_timing": trade.get("fill_timing"),
        "fee_bps": trade.get("fee_bps"),
        "slippage_bps": trade.get("slippage_bps"),
        "entry_time": trade.get("entry_time"),
        "exit_time": trade.get("exit_time"),
        "entry_price": _float(trade.get("entry_price")),
        "exit_price": _float(trade.get("exit_price")),
        "net_pnl": _float(trade.get("net_pnl")),
        "max_adverse_excursion": _float(trade.get("max_adverse_excursion")),
        "max_favorable_excursion": _float(trade.get("max_favorable_excursion")),
        "exit_reason": trade.get("exit_reason"),
    }


def _duration_bucket(seconds: float) -> str:
    hours = seconds / 3600
    if hours <= 4:
        return "0-4h"
    if hours <= 24:
        return "4-24h"
    if hours <= 72:
        return "1-3d"
    return "3d+"


def _money(value: Any) -> str:
    return f"${_float(value):,.2f}"


def _pct(value: Any) -> str:
    return f"{_float(value) * 100:.2f}%"


def _number(value: Any) -> str:
    return f"{_float(value):.4f}"


def _format_duration(seconds: Any) -> str:
    hours = _float(seconds) / 3600
    if hours < 24:
        return f"{hours:.2f}h"
    return f"{hours / 24:.2f}d"


def _inline_counts(values: dict[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items(), key=lambda item: str(item[0])))


def _inline_money(values: dict[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={_money(value)}" for key, value in sorted(values.items(), key=lambda item: str(item[0])))


def _inline_stats(values: dict[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={_number(value)}" for key, value in sorted(values.items(), key=lambda item: str(item[0])))


def _trade_label(trade: dict[str, Any]) -> str:
    if not trade:
        return "none"
    return (
        f"{trade.get('symbol')} {trade.get('component_key')} {trade.get('fill_timing')} "
        f"net={_money(trade.get('net_pnl'))} exit={trade.get('exit_reason')}"
    )
