"""Controlled Money Flow hypothesis experiments for Strategy Validation.

This module is intentionally research-only. It compares SV1.14 hypotheses
against existing dynamic-equity evidence packs without changing production
Money Flow rules, routing, execution, or eligibility behavior.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from services.strategy_validation.trade_anatomy import (
    DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
    LoadedCandle,
    _build_indicator_features,
    _flatten_run_rows,
    _flatten_trade_rows,
    _load_batch_reports,
    _market_structure_context,
    _parse_datetime,
    load_candles_for_batch_reports,
)

INITIAL_CAPITAL_DEFAULT = 10_000.0
POSITION_NOTIONAL_PCT_DEFAULT = 1.0

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
class MoneyFlowResearchVariant:
    variant_id: str
    variant_name: str
    description: str
    hypothesis: str
    applicable_components: tuple[str, ...]
    applicable_symbols: tuple[str, ...]
    parameters: dict[str, Any]
    variant_type: str
    expected_benefit: str
    risk: str
    methodology: str
    status: str = "experimental"
    research_only: bool = True
    changes_production_rules: bool = False


def build_money_flow_hypothesis_experiments(
    batch_report_paths: Sequence[str | Path] = DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
    *,
    candles_by_symbol_timeframe: dict[tuple[str, str], Sequence[LoadedCandle]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic SV1.15 experiment payload."""

    batch_reports = _load_batch_reports(batch_report_paths)
    run_rows = _flatten_run_rows(batch_reports)
    trade_rows = _flatten_trade_rows(run_rows)
    candles_by_symbol_timeframe = candles_by_symbol_timeframe or {}
    indicator_features = _build_indicator_features(candles_by_symbol_timeframe)

    for trade in trade_rows:
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
        trade["rsi_entry_zone"] = _rsi_entry_zone(str(trade.get("component_key")), trade)
        trade["entry_style"] = _entry_style(trade)

    runs_by_id = {str(row["run_id"]): row for row in run_rows}
    trades_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trade_rows:
        trades_by_run[str(trade.get("run_id"))].append(trade)

    baseline_rows = [_baseline_result(run) for run in run_rows]
    variants = _research_variants()
    variant_rows: list[dict[str, Any]] = []
    for variant in variants:
        if variant.variant_type == "reporting_only_attribution":
            continue
        for run_id, run in runs_by_id.items():
            trades = sorted(trades_by_run.get(run_id, []), key=lambda row: str(row.get("exit_time") or row.get("entry_time")))
            if not _variant_applies_to_run(variant, run):
                continue
            variant_rows.append(_simulate_variant_result(variant, run, trades))

    report = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Hyperliquid USDC perpetual public-candle research only",
        "status": "controlled_hypothesis_experiments_ready_for_founder_review",
        "batch_report_paths": [str(Path(path)) for path in batch_report_paths],
        "capital_sizing_mode": "dynamic_equity_pct",
        "baseline": {
            "description": "current Money Flow rules with dynamic_equity_pct",
            "changes_production_rules": False,
            "scenario_results": baseline_rows,
            "summary": _summarize_rows(baseline_rows),
            "by_component": _summarize_by(baseline_rows, "component_key"),
            "eth_1h": _summarize_rows(
                [row for row in baseline_rows if row["symbol"] == "ETH" and row["component_key"] == "sleeve_1h"]
            ),
        },
        "variant_definitions": [asdict(variant) for variant in variants],
        "variant_results": variant_rows,
        "variant_summary": _summarize_variants(variant_rows, baseline_rows),
        "eth_1h_preservation": _eth_1h_preservation(variant_rows, baseline_rows),
        "lower_half_rsi_attribution": _rsi_attribution(trade_rows),
        "pullback_vs_continuation_attribution": _entry_style_attribution(trade_rows),
        "lower_rsi_entry_admission_note": {
            "status": "partially_deferred_to_replay_instrumentation",
            "reason": (
                "Existing evidence packs contain completed trades and aggregate no-trade reason counts, "
                "but not every rejected candle's full indicator/market-structure snapshot. SV1.15 tests "
                "RSI-zone attribution from completed trades and records lower-floor entry variants as "
                "experimental designs; full admission of new lower-RSI trades needs a later replay runner "
                "that persists per-candle rejected-signal features."
            ),
            "falling_knife_risk": (
                "Lower RSI can improve pullback pricing only if trend stack and support context remain intact; "
                "otherwise it can add falling-knife entries."
            ),
        },
        "hypothesis_status": _hypothesis_status(variant_rows, baseline_rows),
        "methodology_truth": {
            "completed_trade_overlay_estimate": (
                "Filters or adjusts already-completed baseline trades. It does not admit new alternative "
                "trades, fully model changed position occupancy, fully model changed future capital path after "
                "skipped entries, or fully model exact earlier exit fills."
            ),
            "lookahead_diagnostic_proxy": (
                "Uses information from completed baseline trades to estimate an upper-bound diagnostic. It is "
                "not a forward-tradable result and requires true candle-by-candle replay before candidate review."
            ),
            "reporting_only_attribution": "Labels completed baseline trades for explanation only.",
            "deferred_requires_rejected_signal_replay": (
                "Needs rejected-candle indicator and market-structure snapshots before new entry admission can be tested."
            ),
            "true_forward_replay": "No SV1.15.1 variant currently has this methodology.",
        },
        "next_step_mapping": _next_step_mapping(),
        "boundary_flags": {
            "changes_production_money_flow_rules": False,
            "optimizes_parameters_globally": False,
            "approves_paper_trading": False,
            "creates_paper_trading_artifacts": False,
            "creates_live_artifacts": False,
            "creates_routing_artifacts": False,
            "calls_exchange_adapters": False,
            "calls_private_or_signed_exchange_endpoints": False,
            "calls_exchange_order_endpoints": False,
            "uses_api_keys": False,
            "uses_dynamic_equity_in_main_report": True,
        },
        "limitations": [
            "overlay_filters_compare_against_completed_baseline_research_trades",
            "completed_trade_overlays_are_not_true_forward_replays",
            "lookahead_proxy_results_are_not_candidate_rule_results",
            "lower_rsi_entry_admission_requires_later_per_candle_replay_instrumentation",
            "separate_scenarios_are_not_one_combined_account",
            "no_variant_is_authorized_or_production_ready",
            "paper_trading_design_remains_deferred",
        ],
        "live_artifact_names_absent": list(FORBIDDEN_LIVE_ARTIFACT_NAMES),
    }
    return report


def load_default_hypothesis_experiment_candles(
    batch_report_paths: Sequence[str | Path] = DEFAULT_DYNAMIC_EQUITY_BATCH_REPORT_PATHS,
) -> dict[tuple[str, str], list[LoadedCandle]]:
    return load_candles_for_batch_reports(batch_report_paths)


def money_flow_hypothesis_experiments_to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# SV1.15 Controlled Money Flow Hypothesis Experiments",
        "",
        f"Recorded at: `{report['generated_at']}`",
        "",
        f"Status: `{report['status']}`",
        "",
        "This report is research-only. It tests SV1.14 hypotheses as isolated Strategy Validation variants. "
        "No production Money Flow rules changed, no parameters were optimized globally, no routing/execution "
        "artifacts were created, and paper/live trading remains deferred.",
        "",
        "Scope: Hyperliquid USDC perpetual public-candle research only. Main comparisons use `dynamic_equity_pct`; "
        "each scenario remains independent and is not one combined account.",
        "",
        "## Methodology Truth",
        "",
        "SV1.15.1 is a methodology-truth hotfix. Most SV1.15 variants are completed-trade overlay diagnostics, "
        "not true candle-by-candle strategy replays.",
        "",
        "Completed-trade overlays filter or adjust already-completed baseline trades. They do not admit new alternative "
        "trades, do not fully model changed position occupancy, do not fully model changed future capital after skipped "
        "entries, and do not fully model exact earlier exit fills. They are useful for ranking hypotheses for later "
        "replay work, not for authorizing rules.",
        "",
        "The `recent_low_invalidation_proxy_20c` result is a `lookahead_diagnostic_proxy`: it estimates an upper-bound "
        "diagnostic from completed baseline losers and is not a forward-tradable result. Exact earlier exit timing and "
        "fill modeling must be replayed before it can be considered for later candidate review.",
        "",
        "## Baseline",
        "",
        "Baseline is current Money Flow rules with `dynamic_equity_pct` sizing.",
        "",
        "| Component | Scenario Count | Start Equity Sum | Ending Equity Sum | Net Account PnL Sum | Min Ending Equity | Max Drawdown | Trade Count |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for component, summary in report["baseline"]["by_component"].items():
        lines.append(
            f"| {component} | {summary['scenario_count']} | {_money(summary['sum_starting_equity'])} | "
            f"{_money(summary['sum_ending_equity'])} | {_money(summary['sum_net_account_pnl'])} | "
            f"{_money(summary['minimum_ending_equity'])} | {_money(summary['max_drawdown'])} | {summary['trade_count']} |"
        )

    lines.extend(
        [
            "",
            "## Experiment List",
            "",
            "| Variant | Type | Methodology | Applies To | Status | Research Boundary |",
            "|---|---|---|---|---|---|",
        ]
    )
    for variant in report["variant_definitions"]:
        applies_to = ",".join(variant["applicable_components"]) or "all"
        lines.append(
            f"| `{variant['variant_id']}` | {variant['variant_type']} | `{variant['methodology']}` | {applies_to} | "
            f"{variant['status']} | research_only={str(variant['research_only']).lower()}, "
            f"changes_rules={str(variant['changes_production_rules']).lower()} |"
        )

    lines.extend(
        [
            "",
            "## One-Change-At-A-Time Comparison",
            "",
            "Grouped rows below are sums across independent research scenarios, not one account result.",
            "",
            "| Variant | Methodology | Scenarios | Baseline Net Sum | Variant Net Sum | Delta | Baseline Drawdown | Variant Drawdown | Baseline Trades | Variant Trades | Filtered Trades | Losing Trades Avoided | Winning Trades Missed |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["variant_summary"]:
        lines.append(
            f"| `{row['variant_id']}` | `{row['methodology']}` | {row['scenario_count']} | {_money(row['baseline_net_account_pnl_sum'])} | "
            f"{_money(row['variant_net_account_pnl_sum'])} | {_money(row['net_account_pnl_delta_sum'])} | "
            f"{_money(row['baseline_max_drawdown'])} | {_money(row['variant_max_drawdown'])} | "
            f"{row['baseline_trade_count']} | {row['variant_trade_count']} | {row['filtered_trade_count']} | "
            f"{row['losing_trades_avoided']} | {row['winning_trades_missed']} |"
        )

    lines.extend(
        [
            "",
            "## ETH 1h Preservation",
            "",
            "ETH `sleeve_1h` is the baseline pocket that variants must avoid damaging before later validation.",
            "",
            "| Variant | ETH 1h Scenarios | Baseline Net Sum | Variant Net Sum | Delta | Baseline Trades | Variant Trades | Status |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["eth_1h_preservation"]:
        lines.append(
            f"| `{row['variant_id']}` | {row['scenario_count']} | {_money(row['baseline_net_account_pnl_sum'])} | "
            f"{_money(row['variant_net_account_pnl_sum'])} | {_money(row['net_account_pnl_delta_sum'])} | "
            f"{row['baseline_trade_count']} | {row['variant_trade_count']} | {row['status']} |"
        )

    lines.extend(
        [
            "",
            "## Lower-RSI Experiment Section",
            "",
            "Current production Money Flow does not enter below the RSI sleeve floor. SV1.15 keeps that unchanged.",
            "",
            "### Lower-Half RSI Attribution Inside Current Band",
            "",
            "| Component | Symbol | RSI Zone | Trades | Net PnL | Win Rate | Avg MAE | Avg MFE |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["lower_half_rsi_attribution"]:
        lines.append(
            f"| {row['component_key']} | {row['symbol']} | `{row['rsi_entry_zone']}` | {row['trade_count']} | "
            f"{_money(row['net_pnl'])} | {_pct(row['win_rate'])} | {_money(row['average_adverse_excursion'])} | "
            f"{_money(row['average_favorable_excursion'])} |"
        )
    note = report["lower_rsi_entry_admission_note"]
    lines.extend(
        [
            "",
            "### Lower RSI Floor Expansion / Pullback Variants",
            "",
            f"- Status: `{note['status']}`",
            f"- Reason: {note['reason']}",
            f"- Risk: {note['falling_knife_risk']}",
            "- Lower RSI variants remain research-only. They are not production rules and are not paper/live authorization.",
            "",
            "## Pullback vs Continuation Attribution",
            "",
            "| Component | Symbol | Entry Style | Trades | Net PnL | Win Rate |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in report["pullback_vs_continuation_attribution"]:
        lines.append(
            f"| {row['component_key']} | {row['symbol']} | `{row['entry_style']}` | {row['trade_count']} | "
            f"{_money(row['net_pnl'])} | {_pct(row['win_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Hypothesis Status",
            "",
            "| Bucket | Hypotheses |",
            "|---|---|",
        ]
    )
    for bucket, values in report["hypothesis_status"].items():
        lines.append(f"| `{bucket}` | {', '.join(f'`{value}`' for value in values) or 'none'} |")

    lines.extend(
        [
            "",
            "## What Each Hypothesis Needs Before Rule Testing",
            "",
            "| Hypothesis | Needed Before Rule Testing |",
            "|---|---|",
        ]
    )
    for key, value in report["next_step_mapping"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Interpretation Boundaries",
            "",
            "- Completed-trade overlay deltas are methodology-limited research observations only.",
            "- The recent-low invalidation proxy is a lookahead diagnostic upper bound, not a candidate rule result.",
            "- No hypothesis receives authorization for production, paper trading, or live trading.",
            "- Lower RSI can represent constructive pullback pricing only when trend and support context remain intact; otherwise it can add falling-knife risk.",
            "- Full lower-RSI entry admission is intentionally deferred until the replay runner can persist rejected-candle feature rows.",
            "",
            "## Boundary Flags",
            "",
        ]
    )
    for key, value in report["boundary_flags"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Deferred Work",
            "",
            "- Build a per-candle rejected-signal replay runner before adding new lower-RSI entry-admission tests.",
            "- Build true forward replay for entry filters so skipped entries, position occupancy, and capital path are modeled.",
            "- Build real exit replay for recent-low invalidation with actual stop time and fill assumptions.",
            "- Validate any candidate on additional windows before considering a separate founder-scoped paper-design phase.",
            "- Keep Aster/Binance/OKX/Coinbase/Kraken outside this Hyperliquid-only experiment result.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_money_flow_hypothesis_experiment_report(
    report: dict[str, Any],
    output_path: str | Path,
    *,
    json_output_path: str | Path | None = None,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(money_flow_hypothesis_experiments_to_markdown(report), encoding="utf-8")
    if json_output_path is not None:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _research_variants() -> list[MoneyFlowResearchVariant]:
    return [
        MoneyFlowResearchVariant(
            variant_id="resistance_proximity_0_25pct",
            variant_name="Avoid entries within 0.25% of recent resistance",
            description="Skip baseline entries too close to the prior 20-candle swing high.",
            hypothesis="avoid entries too close to recent resistance",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"lookback_candles": 20, "max_distance_to_swing_high_pct": 0.0025},
            variant_type="entry_filter",
            expected_benefit="reduce entries with limited room before resistance",
            risk="can miss continuation winners in strong trends",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="resistance_proximity_0_50pct",
            variant_name="Avoid entries within 0.50% of recent resistance",
            description="Skip baseline entries near the prior 20-candle swing high.",
            hypothesis="avoid entries too close to recent resistance",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"lookback_candles": 20, "max_distance_to_swing_high_pct": 0.005},
            variant_type="entry_filter",
            expected_benefit="reduce nearby-resistance chop",
            risk="can remove valid breakout continuation trades",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="higher_low_confirmation_20c",
            variant_name="Require support context near prior swing low",
            description="Keep entries only when recent swing-low context is available and the entry is within 5% above it.",
            hypothesis="require higher-low context before pullback entries",
            applicable_components=("sleeve_15m", "sleeve_1h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"lookback_candles": 20, "max_distance_to_swing_low_pct": 0.05},
            variant_type="entry_filter",
            expected_benefit="favor pullbacks with visible nearby support context",
            risk="can over-filter ETH-like momentum pockets",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="recent_low_invalidation_proxy_20c",
            variant_name="Recent-low invalidation proxy",
            description="Remove baseline losing trades whose adverse excursion breached the prior swing-low distance.",
            hypothesis="test ATR or recent-low risk invalidation",
            applicable_components=("sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"lookback_candles": 20},
            variant_type="exit_filter",
            expected_benefit="estimate large-loss containment from structure invalidation",
            risk="proxy can overstate benefit because exact earlier exit fills are not replayed",
            methodology="lookahead_diagnostic_proxy",
            status="diagnostic_upper_bound_requires_forward_replay",
        ),
        MoneyFlowResearchVariant(
            variant_id="sideways_regime_avoidance_15m",
            variant_name="Avoid 15m non-uptrend regimes",
            description="Skip 15m baseline entries when entry market regime is not uptrend.",
            hypothesis="avoid 15m trades in sideways/choppy regimes",
            applicable_components=("sleeve_15m",),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"allowed_entry_market_regimes": ["uptrend"]},
            variant_type="entry_filter",
            expected_benefit="reduce high-frequency chop and repeated cost drag",
            risk="can miss early trend transitions",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="extension_limit_4h_2_0pct",
            variant_name="Limit 4h EMA5 extension to 2.0%",
            description="Skip 4h entries when entry close is more than 2.0% above EMA5.",
            hypothesis="limit 4h entries when price is extended from EMA10/SMA20",
            applicable_components=("sleeve_4h",),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"max_ema_extension_pct": 0.02},
            variant_type="entry_filter",
            expected_benefit="reduce late 4h entries",
            risk="can under-participate in persistent trends",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="extension_limit_4h_1_5pct",
            variant_name="Limit 4h EMA5 extension to 1.5%",
            description="Skip 4h entries when entry close is more than 1.5% above EMA5.",
            hypothesis="limit 4h entries when price is extended from EMA10/SMA20",
            applicable_components=("sleeve_4h",),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"max_ema_extension_pct": 0.015},
            variant_type="entry_filter",
            expected_benefit="test stricter 4h late-entry control",
            risk="can remove too many valid 4h trend entries",
            methodology="completed_trade_overlay_estimate",
        ),
        MoneyFlowResearchVariant(
            variant_id="lower_half_rsi_attribution",
            variant_name="Lower-half RSI attribution",
            description="Classify completed baseline trades by RSI entry zone inside the current sleeve band.",
            hypothesis="lower-half RSI attribution inside current RSI band",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"reporting_only": True},
            variant_type="reporting_only_attribution",
            expected_benefit="show whether winners already come from the lower side of the allowed RSI band",
            risk="does not admit new below-floor entries",
            methodology="reporting_only_attribution",
            status="candidate_for_later_validation",
        ),
        MoneyFlowResearchVariant(
            variant_id="pullback_vs_continuation_attribution",
            variant_name="Pullback vs continuation attribution",
            description="Classify completed baseline entries by simple extension context.",
            hypothesis="separate pullback entries from continuation entries in reporting",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"reporting_only": True},
            variant_type="reporting_only_attribution",
            expected_benefit="separate entry-style contribution before rule changes",
            risk="classification is simple and descriptive",
            methodology="reporting_only_attribution",
            status="candidate_for_later_validation",
        ),
        MoneyFlowResearchVariant(
            variant_id="lower_rsi_floor_expansion_replay_required",
            variant_name="Lower RSI floor expansion replay required",
            description="Design placeholder for lower RSI floor expansion that requires rejected-candle replay features.",
            hypothesis="allow lower RSI floors with current ceiling unchanged",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"candidate_floors": {"15m": [48, 50], "1h": [45, 48], "4h": [44, 46]}},
            variant_type="experimental_entry_variant",
            expected_benefit="test whether lower pullback pricing improves long entries",
            risk="can add falling-knife trades if trend/support context is weak",
            methodology="deferred_requires_rejected_signal_replay",
            status="needs_more_evidence",
        ),
        MoneyFlowResearchVariant(
            variant_id="lower_rsi_pullback_trend_intact_replay_required",
            variant_name="Lower RSI pullback with intact trend replay required",
            description="Design placeholder requiring EMA stack, price above SMA20, MACD improvement, and support context.",
            hypothesis="lower RSI pullback only when trend remains intact",
            applicable_components=("sleeve_15m", "sleeve_1h", "sleeve_4h"),
            applicable_symbols=("BTC", "ETH", "SOL"),
            parameters={"requires_ema_stack": True, "requires_price_above_sma20": True, "requires_support_context": True},
            variant_type="experimental_entry_variant",
            expected_benefit="distinguish constructive pullback from falling-knife weakness",
            risk="needs per-candle rejected-signal features to avoid lookahead or incomplete replay",
            methodology="deferred_requires_rejected_signal_replay",
            status="needs_more_evidence",
        ),
    ]


def _variant_applies_to_run(variant: MoneyFlowResearchVariant, run: dict[str, Any]) -> bool:
    return (
        str(run.get("component_key")) in variant.applicable_components
        and str(run.get("symbol")) in variant.applicable_symbols
        and variant.variant_type in {"entry_filter", "exit_filter"}
    )


def _simulate_variant_result(
    variant: MoneyFlowResearchVariant,
    run: dict[str, Any],
    trades: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    starting_equity = _starting_equity(run)
    equity = starting_equity
    peak = starting_equity
    max_drawdown = 0.0
    retained: list[float] = []
    filtered: list[dict[str, Any]] = []
    for trade in trades:
        if not _variant_keeps_trade(variant, trade):
            filtered.append(trade)
            continue
        if equity <= 0:
            filtered.append(trade)
            continue
        entry_notional = equity * _position_pct(run)
        trade_return = _trade_return_pct(trade)
        net = entry_notional * trade_return
        retained.append(net)
        equity += net
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    baseline = _baseline_result(run)
    return {
        "variant_id": variant.variant_id,
        "methodology": variant.methodology,
        "run_id": run.get("run_id"),
        "component_key": run.get("component_key"),
        "symbol": run.get("symbol"),
        "fill_timing": run.get("fill_timing"),
        "fee_bps": _float(run.get("fee_bps")),
        "slippage_bps": _float(run.get("slippage_bps")),
        "capital_sizing_mode": "dynamic_equity_pct",
        "starting_equity": starting_equity,
        "ending_equity": equity,
        "net_account_pnl": equity - starting_equity,
        "return_on_starting_equity": ((equity - starting_equity) / starting_equity) if starting_equity else 0.0,
        "max_closed_trade_drawdown": max_drawdown,
        "trade_count": len(retained),
        "filtered_trade_count": len(filtered),
        "winning_trades_missed": sum(1 for trade in filtered if _float(trade.get("net_pnl")) > 0),
        "losing_trades_avoided": sum(1 for trade in filtered if _float(trade.get("net_pnl")) <= 0),
        "profit_factor": _profit_factor(retained),
        "win_rate": (sum(1 for value in retained if value > 0) / len(retained)) if retained else 0.0,
        "baseline_net_account_pnl": baseline["net_account_pnl"],
        "baseline_ending_equity": baseline["ending_equity"],
        "baseline_max_closed_trade_drawdown": baseline["max_closed_trade_drawdown"],
        "baseline_trade_count": baseline["trade_count"],
        "net_account_pnl_delta": (equity - starting_equity) - baseline["net_account_pnl"],
        "ending_equity_delta": equity - baseline["ending_equity"],
        "drawdown_delta": max_drawdown - baseline["max_closed_trade_drawdown"],
    }


def _variant_keeps_trade(variant: MoneyFlowResearchVariant, trade: dict[str, Any]) -> bool:
    if variant.variant_id.startswith("resistance_proximity"):
        ctx = trade.get("market_structure") or {}
        if not ctx.get("context_available"):
            return True
        distance = _float(ctx.get("distance_to_recent_swing_high_pct"))
        threshold = _float(variant.parameters["max_distance_to_swing_high_pct"])
        return not (0 <= distance <= threshold)
    if variant.variant_id == "higher_low_confirmation_20c":
        ctx = trade.get("market_structure") or {}
        if not ctx.get("context_available"):
            return False
        return _float(ctx.get("distance_to_recent_swing_low_pct")) <= _float(variant.parameters["max_distance_to_swing_low_pct"])
    if variant.variant_id == "recent_low_invalidation_proxy_20c":
        ctx = trade.get("market_structure") or {}
        if _float(trade.get("net_pnl")) >= 0:
            return True
        return not bool(ctx.get("stop_like_invalidation_below_recent_low_descriptive_only"))
    if variant.variant_id == "sideways_regime_avoidance_15m":
        return str(trade.get("entry_market_regime")) in set(variant.parameters["allowed_entry_market_regimes"])
    if variant.variant_id.startswith("extension_limit_4h"):
        extension = (trade.get("entry_indicators") or {}).get("ema_extension_pct")
        if extension is None:
            return True
        return _float(extension) <= _float(variant.parameters["max_ema_extension_pct"])
    return True


def _baseline_result(run: dict[str, Any]) -> dict[str, Any]:
    metrics = run.get("metrics") or {}
    starting_equity = _float(metrics.get("starting_equity")) or _starting_equity(run)
    ending_equity = _float(metrics.get("ending_equity")) or (starting_equity + _float(metrics.get("net_account_pnl")))
    return {
        "run_id": run.get("run_id"),
        "component_key": run.get("component_key"),
        "symbol": run.get("symbol"),
        "fill_timing": run.get("fill_timing"),
        "fee_bps": _float(run.get("fee_bps")),
        "slippage_bps": _float(run.get("slippage_bps")),
        "capital_sizing_mode": metrics.get("capital_sizing_mode") or "dynamic_equity_pct",
        "starting_equity": starting_equity,
        "ending_equity": ending_equity,
        "net_account_pnl": _float(metrics.get("net_account_pnl") or metrics.get("net_pnl")),
        "max_closed_trade_drawdown": _float(
            metrics.get("max_closed_trade_equity_drawdown")
            or metrics.get("closed_trade_max_drawdown")
            or metrics.get("max_drawdown")
        ),
        "mark_to_market_drawdown": _float(
            metrics.get("max_mark_to_market_equity_drawdown")
            or metrics.get("mark_to_market_max_drawdown")
        ),
        "trade_count": int(_float(metrics.get("number_of_trades"))),
        "win_rate": _float(metrics.get("win_rate")),
        "profit_factor": _float(metrics.get("profit_factor")),
    }


def _summarize_variants(variant_rows: Sequence[dict[str, Any]], baseline_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_by_run = {str(row["run_id"]): row for row in baseline_rows}
    rows: list[dict[str, Any]] = []
    for variant_id in sorted({str(row["variant_id"]) for row in variant_rows}):
        selected = [row for row in variant_rows if row["variant_id"] == variant_id]
        baselines = [baseline_by_run[str(row["run_id"])] for row in selected if str(row["run_id"]) in baseline_by_run]
        rows.append(
            {
                "variant_id": variant_id,
                "methodology": str(selected[0].get("methodology") or "unknown"),
                "scenario_count": len(selected),
                "baseline_net_account_pnl_sum": _sum(row["net_account_pnl"] for row in baselines),
                "variant_net_account_pnl_sum": _sum(row["net_account_pnl"] for row in selected),
                "net_account_pnl_delta_sum": _sum(row["net_account_pnl_delta"] for row in selected),
                "baseline_max_drawdown": max((row["max_closed_trade_drawdown"] for row in baselines), default=0.0),
                "variant_max_drawdown": max((row["max_closed_trade_drawdown"] for row in selected), default=0.0),
                "baseline_trade_count": sum(int(row["trade_count"]) for row in baselines),
                "variant_trade_count": sum(int(row["trade_count"]) for row in selected),
                "filtered_trade_count": sum(int(row["filtered_trade_count"]) for row in selected),
                "losing_trades_avoided": sum(int(row["losing_trades_avoided"]) for row in selected),
                "winning_trades_missed": sum(int(row["winning_trades_missed"]) for row in selected),
            }
        )
    return rows


def _eth_1h_preservation(variant_rows: Sequence[dict[str, Any]], baseline_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_by_run = {str(row["run_id"]): row for row in baseline_rows}
    rows: list[dict[str, Any]] = []
    for variant_id in sorted({str(row["variant_id"]) for row in variant_rows}):
        selected = [
            row
            for row in variant_rows
            if row["variant_id"] == variant_id and row["symbol"] == "ETH" and row["component_key"] == "sleeve_1h"
        ]
        if not selected:
            continue
        baselines = [baseline_by_run[str(row["run_id"])] for row in selected if str(row["run_id"]) in baseline_by_run]
        delta = _sum(row["net_account_pnl_delta"] for row in selected)
        rows.append(
            {
                "variant_id": variant_id,
                "scenario_count": len(selected),
                "baseline_net_account_pnl_sum": _sum(row["net_account_pnl"] for row in baselines),
                "variant_net_account_pnl_sum": _sum(row["net_account_pnl"] for row in selected),
                "net_account_pnl_delta_sum": delta,
                "baseline_trade_count": sum(int(row["trade_count"]) for row in baselines),
                "variant_trade_count": sum(int(row["trade_count"]) for row in selected),
                "status": "eth_1h_preserved_or_improved" if delta >= 0 else "eth_1h_deteriorated",
            }
        )
    return rows


def _rsi_attribution(trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return _attribute_trades(trades, "rsi_entry_zone")


def _entry_style_attribution(trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return _attribute_trades(trades, "entry_style")


def _attribute_trades(trades: Sequence[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        groups[(str(trade.get("component_key")), str(trade.get("symbol")), str(trade.get(key) or "unknown"))].append(trade)
    rows: list[dict[str, Any]] = []
    for (component, symbol, value), selected in sorted(groups.items()):
        wins = sum(1 for trade in selected if _float(trade.get("net_pnl")) > 0)
        rows.append(
            {
                "component_key": component,
                "symbol": symbol,
                key: value,
                "trade_count": len(selected),
                "net_pnl": _sum(_float(trade.get("net_pnl")) for trade in selected),
                "win_rate": wins / len(selected) if selected else 0.0,
                "average_adverse_excursion": _average(_float(trade.get("max_adverse_excursion")) for trade in selected),
                "average_favorable_excursion": _average(_float(trade.get("max_favorable_excursion")) for trade in selected),
            }
        )
    return rows


def _hypothesis_status(variant_rows: Sequence[dict[str, Any]], baseline_rows: Sequence[dict[str, Any]]) -> dict[str, list[str]]:
    del baseline_rows
    summary = _summarize_variants(variant_rows, [])
    overlay_rows = [row for row in summary if row["methodology"] == "completed_trade_overlay_estimate"]
    improved = [
        row["variant_id"]
        for row in overlay_rows
        if row["net_account_pnl_delta_sum"] > 0 and row["variant_trade_count"] > 0
    ]
    deteriorated = [row["variant_id"] for row in overlay_rows if row["net_account_pnl_delta_sum"] < 0]
    no_trade = [row["variant_id"] for row in overlay_rows if row["variant_trade_count"] == 0]
    lookahead_proxy = [
        row["variant_id"] for row in summary if row["methodology"] == "lookahead_diagnostic_proxy"
    ]
    reporting_only = [
        "lower_half_rsi_attribution",
        "pullback_vs_continuation_attribution",
    ]
    deferred = [
        "lower_rsi_floor_expansion_replay_required",
        "lower_rsi_pullback_trend_intact_replay_required",
    ]
    return {
        "diagnostic_overlay_improved_needs_true_replay": sorted(improved),
        "diagnostic_overlay_deteriorated_or_overfiltered": sorted(set(deteriorated + no_trade)),
        "lookahead_proxy_upper_bound_not_candidate": sorted(lookahead_proxy),
        "reporting_attribution_only": sorted(reporting_only),
        "deferred_requires_rejected_signal_replay": sorted(deferred),
        "not_authorized": sorted({*(row["variant_id"] for row in summary), *reporting_only, *deferred}),
    }


def _next_step_mapping() -> dict[str, str]:
    return {
        "resistance_proximity": (
            "Build a true replay entry filter and test whether skipped entries alter later signal availability, "
            "position occupancy, and capital path."
        ),
        "sideways_regime_avoidance_15m": (
            "Build a true replay regime gate and confirm it does not simply remove nearly all 15m activity or "
            "miss early trend transitions."
        ),
        "extension_limit_4h": (
            "Build a true replay entry filter, test longer windows, and verify late-entry control without "
            "over-removing durable trend participation."
        ),
        "higher_low_confirmation": (
            "Redesign before replay; the completed-trade overlay deteriorated ETH 1h and may over-filter "
            "constructive momentum pockets."
        ),
        "recent_low_invalidation": (
            "Build real exit replay with actual stop time, fill timing, slippage, capital path, and missed-recovery "
            "accounting. Current result is an upper-bound diagnostic only."
        ),
        "lower_rsi": (
            "Add rejected-signal replay instrumentation with per-candle indicator and market-structure snapshots "
            "before below-floor entry admission can be tested."
        ),
    }


def _summarize_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario_count": len(rows),
        "sum_starting_equity": _sum(_float(row.get("starting_equity")) for row in rows),
        "sum_ending_equity": _sum(_float(row.get("ending_equity")) for row in rows),
        "sum_net_account_pnl": _sum(_float(row.get("net_account_pnl")) for row in rows),
        "minimum_ending_equity": min((_float(row.get("ending_equity")) for row in rows), default=0.0),
        "maximum_ending_equity": max((_float(row.get("ending_equity")) for row in rows), default=0.0),
        "max_drawdown": max((_float(row.get("max_closed_trade_drawdown")) for row in rows), default=0.0),
        "trade_count": sum(int(_float(row.get("trade_count"))) for row in rows),
    }


def _summarize_by(rows: Sequence[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for value in sorted({str(row.get(key)) for row in rows}):
        output[value] = _summarize_rows([row for row in rows if str(row.get(key)) == value])
    return output


def _rsi_entry_zone(component: str, trade: dict[str, Any]) -> str:
    rsi = (trade.get("entry_indicators") or {}).get("rsi_14")
    if rsi is None:
        return "unknown"
    floor, ceiling = _rsi_band(component)
    midpoint = floor + ((ceiling - floor) / 2)
    if rsi < floor:
        return "below_baseline_floor"
    if rsi < midpoint:
        return "lower_band_half"
    if rsi < ceiling - ((ceiling - floor) * 0.15):
        return "upper_band_half"
    if rsi <= ceiling:
        return "near_upper_band"
    return "above_baseline_ceiling"


def _rsi_band(component: str) -> tuple[float, float]:
    if component == "sleeve_15m":
        return 52.0, 66.0
    if component == "sleeve_1h":
        return 50.0, 68.0
    return 48.0, 70.0


def _entry_style(trade: dict[str, Any]) -> str:
    extension = (trade.get("entry_indicators") or {}).get("ema_extension_pct")
    if extension is None:
        return "unknown"
    if _float(extension) <= 0.005:
        return "pullback"
    return "continuation"


def _starting_equity(run: dict[str, Any]) -> float:
    assumptions = (run.get("request") or {}).get("assumptions") or {}
    return _float(assumptions.get("initial_capital")) or INITIAL_CAPITAL_DEFAULT


def _position_pct(run: dict[str, Any]) -> float:
    assumptions = (run.get("request") or {}).get("assumptions") or {}
    return _float(assumptions.get("position_notional_pct")) or POSITION_NOTIONAL_PCT_DEFAULT


def _trade_return_pct(trade: dict[str, Any]) -> float:
    explicit = _float(trade.get("return_pct"))
    if explicit:
        return explicit
    notional = _float(trade.get("entry_notional"))
    if notional:
        return _float(trade.get("net_pnl")) / notional
    return 0.0


def _profit_factor(values: Sequence[float]) -> float:
    gains = sum(value for value in values if value > 0)
    losses = abs(sum(value for value in values if value < 0))
    if losses == 0:
        return gains if gains else 0.0
    return gains / losses


def _average(values: Iterable[float]) -> float:
    clean = list(values)
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def _sum(values: Iterable[float]) -> float:
    return sum(values)


def _float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _money(value: Any) -> str:
    return f"${_float(value):,.2f}"


def _pct(value: Any) -> str:
    return f"{_float(value) * 100:.2f}%"
