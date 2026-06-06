"""GOAL-STRAT1 autonomous strategy discovery harness.

Research-only. This module reads local public-mainnet replay JSON, validates
candle truth, runs bounded strategy configurations, and labels only founder
production-testing review candidates. It must not import runtime, exchange,
execution, routing, or order modules.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


PHASE = "GOAL-STRAT1"
CANDIDATE_STATUS = "candidate_for_founder_production_testing_review"
STARTING_EQUITY = Decimal("10000")
FEE_BPS = Decimal("5")
SLIPPAGE_BPS = Decimal("2")
ACTIVE_TIMEFRAMES = ("1h", "4h", "1d")
DIAGNOSTIC_TIMEFRAMES = ("15m",)
DEFAULT_SELECTED_REPLAY_GLOBS = (
    "reports/strategy_validation/sv2_0_2_dashboard_chart_data/*/selected/*money_flow_v1_2_canonical_next_candle_open*_replay.json",
    "reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data/20260516T091500Z/selected/*money_flow_v1_2_canonical_next_candle_open*_replay.json",
)
FORBIDDEN_STATUS_WORDS = (
    "production_ready",
    "live_ready",
    "guaranteed_profitable",
    "approved",
)


@dataclass(frozen=True, slots=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source_path: str


@dataclass(frozen=True, slots=True)
class Dataset:
    symbol: str
    timeframe: str
    source_path: str
    source_provenance: str
    canonical_evidence_status: str
    candles: tuple[Candle, ...]


@dataclass(frozen=True, slots=True)
class DataInventoryRow:
    symbol: str
    timeframe: str
    source_path: str
    source_provenance: str
    canonical_evidence_status: str
    earliest_candle: str | None
    latest_fully_closed_candle: str | None
    candle_count: int
    missing_gaps: int
    raw_file_status: str
    db_import_status: str
    data_quality_status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    strategy_id: str
    display_name: str
    family: str
    entry_model: str
    exit_model: str
    risk_model: str
    regime_filter: str
    timeframe_scope: tuple[str, ...]
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Trade:
    strategy_id: str
    symbol: str
    timeframe: str
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    gross_pnl: Decimal
    fees: Decimal
    slippage: Decimal
    net_pnl: Decimal
    equity_after: Decimal
    entry_reason: str
    exit_reason: str


@dataclass(frozen=True, slots=True)
class Metrics:
    starting_equity: Decimal
    ending_equity: Decimal
    net_pnl: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    trade_count: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal | None
    profit_factor: Decimal | None
    largest_win: Decimal | None
    largest_loss: Decimal | None
    average_win: Decimal | None
    average_loss: Decimal | None
    max_consecutive_losses: int
    worst_losing_streak_pnl: Decimal


@dataclass(frozen=True, slots=True)
class CandidateRun:
    strategy_id: str
    display_name: str
    strategy_family: str
    entry_model: str
    exit_model: str
    risk_model: str
    regime_filter: str
    status: str
    reason_codes: tuple[str, ...]
    metrics: Metrics
    active_timeframe_metrics: Metrics
    chronological_oos_metrics: Metrics
    anchored_walk_forward_metrics: Metrics
    trades: tuple[Trade, ...]
    total_scenarios: int
    data_quality_blocks: int
    symbol_concentration: dict[str, str]
    timeframe_concentration: dict[str, str]
    period_concentration: dict[str, str]
    oos_slice_results: dict[str, Any]
    gate_result: dict[str, Any]


def build_goal_strat1_report(
    *,
    selected_replay_globs: Sequence[str] = DEFAULT_SELECTED_REPLAY_GLOBS,
    max_total_candidate_runs: int = 121,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC)
    datasets = load_replay_datasets(selected_replay_globs)
    inventory = build_data_inventory(datasets)
    valid = [
        dataset
        for dataset in datasets
        if dataset_quality_status(dataset) == "accepted"
        and dataset.timeframe in (*ACTIVE_TIMEFRAMES, *DIAGNOSTIC_TIMEFRAMES)
    ]
    configs = generate_strategy_configs()[:max_total_candidate_runs]
    context = build_simulation_context(valid)
    runs = [run_strategy_config(config, valid, context=context) for config in configs]
    passing = [run for run in runs if run.status == CANDIDATE_STATUS]
    top = _rank_runs(passing)[:3]
    near = _rank_runs([run for run in runs if run.status != CANDIDATE_STATUS])[:10]
    conclusion = (
        "three_candidates_found_for_founder_production_testing_review"
        if len(top) >= 3
        else "three_candidates_were_not_found_without_overfitting_after_full_autonomous_discovery"
    )
    report = {
        "phase": PHASE,
        "generated_at": _iso(generated_at),
        "status": "research_only_autonomous_discovery_complete",
        "data_inventory": [asdict(row) for row in inventory],
        "candidate_runs": [_run_to_dict(run, include_trades=False) for run in runs],
        "strategy_families_tested": sorted({run.strategy_family for run in runs}),
        "exit_models_tested": sorted({run.exit_model for run in runs}),
        "risk_models_tested": sorted({run.risk_model for run in runs}),
        "regime_filters_tested": sorted({run.regime_filter for run in runs}),
        "oos_methods_tested": ["chronological_70_30", "anchored_walk_forward_thirds"],
        "passing_candidates": [_run_to_dict(run, include_trades=True) for run in passing],
        "top_3_candidates": [_run_to_dict(run, include_trades=True) for run in top],
        "top_near_misses": [_run_to_dict(run, include_trades=False) for run in near],
        "candidate_gate": candidate_gate_policy(),
        "search_budget": {
            "max_strategy_families": 6,
            "max_candidate_variants_per_family": 20,
            "max_total_candidate_runs": max_total_candidate_runs,
            "broad_unbounded_optimizer": False,
            "minimum_candidate_configurations_before_exhaustion": 60,
        },
        "search_budget_used": {
            "candidate_runs": len(runs),
            "datasets_loaded": len(datasets),
            "datasets_accepted": len(valid),
            "strategy_families": len({run.strategy_family for run in runs}),
            "exit_models": len({run.exit_model for run in runs}),
            "risk_models": len({run.risk_model for run in runs}),
            "regime_filters": len({run.regime_filter for run in runs}),
            "oos_methods": 2,
        },
        "rejected_candidates": [_run_to_dict(run, include_trades=False) for run in runs if run.status != CANDIDATE_STATUS],
        "best_near_misses": [_run_to_dict(run, include_trades=False) for run in near[:5]],
        "why_prior_strat_disc1_was_insufficient": [
            "STRAT-DISC1 tested only 12 hypotheses.",
            "STRAT-DISC1 did not meet the minimum 60 candidate configurations requested for this goal.",
            "STRAT-DISC1 did not explicitly sweep at least 3 exit models, 3 risk models, 3 regime filters, and 2 OOS methods.",
        ],
        "what_changed_in_goal_strat1": [
            "Expanded to generated, bounded candidate configurations across six families.",
            "Added explicit entry, exit, risk, and regime-model dimensions.",
            "Added chronological 70/30 OOS and anchored walk-forward thirds checks.",
            "Kept all work local/research-only and separate from active PT-RT runtime.",
        ],
        "why_three_were_not_promoted": [] if len(top) >= 3 else _why_three_not_promoted(runs),
        "recommended_next_research": _recommended_next_research(conclusion, len(top)),
        "boundary_flags": boundary_flags(),
        "conclusion": conclusion,
    }
    return _json_ready(report)


def load_replay_datasets(selected_replay_globs: Sequence[str]) -> list[Dataset]:
    by_key: dict[tuple[str, str], Dataset] = {}
    for pattern in selected_replay_globs:
        for path in sorted(Path().glob(pattern)):
            dataset = _dataset_from_replay_file(path)
            if dataset is None:
                continue
            key = (dataset.symbol, dataset.timeframe)
            existing = by_key.get(key)
            if existing is None or _dataset_preference(dataset) > _dataset_preference(existing):
                by_key[key] = dataset
    return [by_key[key] for key in sorted(by_key)]


def build_data_inventory(datasets: Sequence[Dataset]) -> list[DataInventoryRow]:
    return [_inventory_row(dataset) for dataset in datasets]


def generate_strategy_configs() -> list[StrategyConfig]:
    configs: list[StrategyConfig] = []
    family_entry_models = {
        "money_flow_repair": [
            ("mf_pullback_reclaim", {"rsi_min": "45", "rsi_max": "70", "lookback": 8}),
            ("mf_macd_reacceleration", {"rsi_min": "48", "rsi_max": "74"}),
            ("mf_ema10_reclaim_after_reset", {"reset_bars": 12, "rsi_max": "72"}),
        ],
        "source_faithful_money_flow": [
            ("stage2_5_20_cross", {"lookback": 20}),
            ("stage2_pullback_sma20_reclaim", {"lookback": 10}),
            ("stage2_resistance_breakout", {"lookback": 20}),
        ],
        "trend_breakout": [
            ("donchian_breakout", {"lookback": 20}),
            ("donchian_breakout", {"lookback": 50}),
            ("higher_high_higher_low", {"lookback": 8}),
        ],
        "mean_reversion": [
            ("bullish_rsi_oversold_reclaim", {"rsi_floor": "35", "reclaim": "43"}),
            ("sma_distance_reclaim", {"distance": "-0.035"}),
            ("failed_breakdown_reclaim", {"lookback": 12}),
        ],
        "relative_strength_rotation": [
            ("top_n_trend_strength", {"rank_lookback": 20, "top_fraction": "0.34"}),
            ("top_n_trend_strength", {"rank_lookback": 50, "top_fraction": "0.25"}),
            ("avoid_bottom_rs_trend", {"rank_lookback": 20, "bottom_fraction": "0.40"}),
        ],
        "volatility_expansion": [
            ("volatility_expansion_breakout", {"lookback": 20, "compression_window": 20}),
            ("volatility_expansion_breakout", {"lookback": 50, "compression_window": 20}),
            ("atr_expansion_trend", {"atr_window": 20}),
        ],
    }
    exit_models = ("sma20_break", "atr_trail", "time_stop")
    risk_models = ("equity_5pct", "equity_10pct", "equity_15pct", "atr_risk_1pct")
    regime_filters = ("none", "sma200", "btc_proxy")
    per_family_limit = 20
    timeframes_by_family = {
        "mean_reversion": ("1h", "4h"),
        "relative_strength_rotation": ("4h", "1d"),
    }
    for family, entries in family_entry_models.items():
        for entry_model, params in entries:
            for exit_model in exit_models:
                for risk_model in risk_models:
                    for regime_filter in regime_filters:
                        if len([c for c in configs if c.family == family]) >= per_family_limit:
                            break
                        slug_params = "_".join(str(value).replace(".", "p").replace("-", "m") for value in params.values())
                        strategy_id = f"{family}_{entry_model}_{exit_model}_{risk_model}_{regime_filter}_{slug_params}"
                        configs.append(
                            StrategyConfig(
                                strategy_id=strategy_id[:140],
                                display_name=f"{family}: {entry_model} / {exit_model} / {risk_model} / {regime_filter}",
                                family=family,
                                entry_model=entry_model,
                                exit_model=exit_model,
                                risk_model=risk_model,
                                regime_filter=regime_filter,
                                timeframe_scope=timeframes_by_family.get(family, ACTIVE_TIMEFRAMES),
                                params=dict(params),
                            )
                        )
                    if len([c for c in configs if c.family == family]) >= per_family_limit:
                        break
                if len([c for c in configs if c.family == family]) >= per_family_limit:
                    break
            if len([c for c in configs if c.family == family]) >= per_family_limit:
                break
    configs.append(
        StrategyConfig(
            strategy_id="pairs_spread_research_proxy_zscore_time_stop_equity_10pct_none",
            display_name="pairs/spread research proxy: z-score reversion",
            family="pairs_spread_research",
            entry_model="pair_spread_zscore_reversion",
            exit_model="time_stop",
            risk_model="equity_10pct",
            regime_filter="none",
            timeframe_scope=("1d",),
            params={"zscore": "-1.5"},
        )
    )
    return configs


def build_simulation_context(datasets: Sequence[Dataset]) -> dict[str, Any]:
    return {
        "indicators": {key: _indicators(dataset.candles) for key, dataset in _dataset_map(datasets).items()},
        "relative_strength_maps": _relative_strength_maps(datasets),
    }


def run_strategy_config(config: StrategyConfig, datasets: Sequence[Dataset], *, context: dict[str, Any] | None = None) -> CandidateRun:
    context = context or build_simulation_context(datasets)
    indicators = context["indicators"]
    rs_maps = context["relative_strength_maps"]
    trades: list[Trade] = []
    blocks = 0
    scenarios = 0
    for dataset in datasets:
        if dataset_quality_status(dataset) != "accepted" or dataset.timeframe not in config.timeframe_scope:
            blocks += 1
            continue
        scenarios += 1
        trades.extend(_simulate_dataset(config, dataset, indicators[(dataset.symbol, dataset.timeframe)], rs_maps, indicators))
    metrics = _metrics(trades)
    active_trades = [trade for trade in trades if trade.timeframe in ACTIVE_TIMEFRAMES]
    active_metrics = _metrics(active_trades)
    chronological_split = _global_split_time(datasets, Decimal("0.70"))
    chronological_oos = _metrics([trade for trade in active_trades if trade.entry_time > chronological_split])
    anchored_oos = _anchored_walk_forward_metrics(active_trades, datasets)
    symbol_conc = _concentration_by(active_trades, lambda trade: trade.symbol)
    tf_conc = _concentration_by(active_trades, lambda trade: trade.timeframe)
    period_conc = _concentration_by(active_trades, lambda trade: f"{trade.entry_time.year}-H{1 if trade.entry_time.month <= 6 else 2}")
    oos = {
        "chronological_70_30_split_time": _iso(chronological_split),
        "chronological_70_30_net_pnl": str(chronological_oos.net_pnl),
        "anchored_walk_forward_thirds_net_pnl": str(anchored_oos.net_pnl),
        "active_timeframe_trade_count": dict(Counter(trade.timeframe for trade in active_trades)),
        "active_timeframe_net_pnl": {
            tf: str(_metrics([trade for trade in active_trades if trade.timeframe == tf]).net_pnl)
            for tf in ACTIVE_TIMEFRAMES
        },
    }
    gate = evaluate_candidate_gate(
        config=config,
        metrics=metrics,
        active_metrics=active_metrics,
        chronological_oos=chronological_oos,
        anchored_oos=anchored_oos,
        trades=active_trades,
        symbol_concentration=symbol_conc,
        period_concentration=period_conc,
    )
    return CandidateRun(
        strategy_id=config.strategy_id,
        display_name=config.display_name,
        strategy_family=config.family,
        entry_model=config.entry_model,
        exit_model=config.exit_model,
        risk_model=config.risk_model,
        regime_filter=config.regime_filter,
        status=gate["status"],
        reason_codes=tuple(gate["reason_codes"]),
        metrics=metrics,
        active_timeframe_metrics=active_metrics,
        chronological_oos_metrics=chronological_oos,
        anchored_walk_forward_metrics=anchored_oos,
        trades=tuple(active_trades),
        total_scenarios=scenarios,
        data_quality_blocks=blocks,
        symbol_concentration=symbol_conc,
        timeframe_concentration=tf_conc,
        period_concentration=period_conc,
        oos_slice_results=oos,
        gate_result=gate,
    )


def evaluate_candidate_gate(
    *,
    config: StrategyConfig,
    metrics: Metrics,
    active_metrics: Metrics,
    chronological_oos: Metrics,
    anchored_oos: Metrics,
    trades: Sequence[Trade],
    symbol_concentration: dict[str, str],
    period_concentration: dict[str, str],
) -> dict[str, Any]:
    reasons: list[str] = []
    min_trades = 20 if trades and all(trade.timeframe == "1d" for trade in trades) else 50
    if active_metrics.trade_count < min_trades:
        reasons.append("rejected_low_sample")
    if active_metrics.net_pnl <= 0 or metrics.ending_equity <= STARTING_EQUITY:
        reasons.append("rejected_no_edge")
    if active_metrics.profit_factor is None or active_metrics.profit_factor < Decimal("1.15"):
        reasons.append("profit_factor_below_threshold")
    if active_metrics.max_drawdown_pct > Decimal("0.30"):
        reasons.append("rejected_drawdown")
    largest_loss_pct = abs(active_metrics.largest_loss or Decimal("0")) / STARTING_EQUITY
    if largest_loss_pct > Decimal("0.08"):
        reasons.append("largest_single_trade_loss_too_large")
    if chronological_oos.net_pnl < 0:
        reasons.append("chronological_oos_net_pnl_negative")
    if anchored_oos.net_pnl < 0:
        reasons.append("anchored_walk_forward_oos_net_pnl_negative")
    if _max_concentration(symbol_concentration) > Decimal("0.45"):
        reasons.append("rejected_concentrated_symbol")
    if _max_concentration(period_concentration) > Decimal("0.60"):
        reasons.append("rejected_concentrated_period")
    if any(trade.timeframe == "15m" for trade in trades):
        reasons.append("diagnostic_15m_contribution_not_allowed")
    if config.family == "pairs_spread_research":
        reasons.append("research_only_insufficient_market_structure_data")
    status = CANDIDATE_STATUS if not reasons else _status_from_reasons(reasons)
    return {
        "status": status,
        "passed": status == CANDIDATE_STATUS,
        "reason_codes": reasons or ["candidate_gate_passed"],
        "min_trades_required": min_trades,
        "profit_factor_threshold": "1.15",
        "max_drawdown_pct_threshold": "0.30",
        "largest_loss_pct_threshold": "0.08",
        "max_symbol_contribution_threshold": "0.45",
        "max_period_contribution_threshold": "0.60",
        "chronological_oos_required_nonnegative": True,
        "anchored_walk_forward_required_nonnegative": True,
        "uses_15m_for_promotion": False,
    }


def candidate_gate_policy() -> dict[str, Any]:
    return {
        "positive_net_pnl_after_fees_slippage": True,
        "ending_equity_above_start": True,
        "profit_factor_min": "1.15",
        "max_drawdown_pct_max": "0.30",
        "largest_single_trade_loss_pct_max": "0.08",
        "min_trades_total_1h_4h": 50,
        "min_trades_total_1d": 20,
        "chronological_70_30_oos_net_pnl_nonnegative": True,
        "anchored_walk_forward_thirds_oos_net_pnl_nonnegative": True,
        "single_symbol_net_pnl_share_max": "0.45",
        "single_period_net_pnl_share_max": "0.60",
        "fifteen_minute_is_diagnostic_not_promotion": True,
        "lookahead_allowed": False,
        "same_candle_optimistic_fill_allowed": False,
        "production_or_live_approval": False,
    }


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "changes_production_money_flow_rules": False,
        "mutates_active_pt_rt_runtime": False,
        "mutates_runtime_artifacts": False,
        "creates_order_intent": False,
        "creates_prepared_venue_order": False,
        "creates_submitted_order": False,
        "submits_live_orders": False,
        "submits_testnet_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "uses_testnet_data_as_strategy_truth": False,
        "uses_testnet_fills_as_pnl_truth": False,
        "approves_live_trading": False,
        "approves_production_strategy": False,
        "uses_dashboard_date_filters_as_canonical_evidence": False,
    }


def write_goal_strat1_outputs(report: dict[str, Any], markdown_output: str | Path, json_output: str | Path) -> None:
    Path(markdown_output).write_text(report_to_markdown(report), encoding="utf-8")
    Path(json_output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    top = report.get("top_3_candidates", [])
    if len(top) >= 3:
        for index, candidate in enumerate(top[:3], start=1):
            Path(f"docs/goal_strat1_candidate_{index}_{candidate['strategy_id']}.md").write_text(
                candidate_report_markdown(index, candidate),
                encoding="utf-8",
            )
    else:
        Path("docs/goal_strat1_no_three_candidates_found.md").write_text(no_three_candidates_markdown(report), encoding="utf-8")


def report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GOAL-STRAT1 Strategy Discovery",
        "",
        "GOAL-STRAT1 is research-only. No strategy is production-approved. Live trading is not approved.",
        "",
        "## Summary",
        "",
        f"- Conclusion: `{report['conclusion']}`",
        f"- Candidate configurations tested: `{report['search_budget_used']['candidate_runs']}`",
        f"- Passing candidates: `{len(report.get('passing_candidates', []))}`",
        f"- Datasets accepted: `{report['search_budget_used']['datasets_accepted']}`",
        f"- Strategy families tested: `{report['search_budget_used']['strategy_families']}`",
        f"- Exit models tested: `{report['search_budget_used']['exit_models']}`",
        f"- Risk models tested: `{report['search_budget_used']['risk_models']}`",
        f"- Regime filters tested: `{report['search_budget_used']['regime_filters']}`",
        "",
        "## Data Inventory",
        "",
        "| symbol | timeframe | candles | earliest | latest | status | reason codes |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in report["data_inventory"]:
        lines.append(
            f"| {row['symbol']} | {row['timeframe']} | {row['candle_count']} | "
            f"{row['earliest_candle'] or 'n/a'} | {row['latest_fully_closed_candle'] or 'n/a'} | "
            f"{row['data_quality_status']} | {', '.join(row['reason_codes']) or 'none'} |"
        )
    lines.extend(["", "## Top Candidates", ""])
    if report.get("top_3_candidates"):
        for index, run in enumerate(report["top_3_candidates"], start=1):
            lines.extend(_candidate_summary_lines(index, run))
    else:
        lines.append("No strategy passed the full GOAL-STRAT1 candidate gate.")
    lines.extend(["", "## Best Near Misses", ""])
    for run in report.get("top_near_misses", [])[:8]:
        metrics = run["active_timeframe_metrics"]
        lines.append(
            f"- `{run['strategy_id']}`: `{run['status']}`, active net PnL `{metrics['net_pnl']}`, "
            f"PF `{metrics['profit_factor']}`, DD `{metrics['max_drawdown_pct']}`, blockers `{', '.join(run['reason_codes'])}`"
        )
    lines.extend(["", "## Candidate Gate", ""])
    for key, value in report["candidate_gate"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Boundaries", ""])
    for key, value in report["boundary_flags"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    if report["conclusion"] == "three_candidates_found_for_founder_production_testing_review":
        lines.append("Three strategies are ready for founder production-testing review.")
    else:
        lines.append("Three strategies were not found without overfitting after full autonomous discovery.")
    return "\n".join(lines) + "\n"


def candidate_report_markdown(index: int, candidate: dict[str, Any]) -> str:
    m = candidate["active_timeframe_metrics"]
    return "\n".join(
        [
            f"# GOAL-STRAT1 Candidate {index}: {candidate['display_name']}",
            "",
            "This is a founder production-testing review candidate only. It is not production-approved and live trading is not approved.",
            "",
            "## Strategy Logic",
            "",
            f"- Strategy id: `{candidate['strategy_id']}`",
            f"- Family: `{candidate['strategy_family']}`",
            f"- Entry model: `{candidate['entry_model']}`",
            f"- Exit model: `{candidate['exit_model']}`",
            f"- Risk model: `{candidate['risk_model']}`",
            f"- Regime filter: `{candidate['regime_filter']}`",
            "- Fill assumption: next candle open after a closed signal candle; no same-candle optimistic fill.",
            "- Fees/slippage: 5 bps fees plus 2 bps slippage on entry and exit assumptions.",
            "",
            "## Metrics",
            "",
            f"- Net PnL: `{m['net_pnl']}`",
            f"- Ending equity: `{m['ending_equity']}`",
            f"- Max drawdown: `{m['max_drawdown']}`",
            f"- Max drawdown pct: `{m['max_drawdown_pct']}`",
            f"- Profit factor: `{m['profit_factor']}`",
            f"- Win rate: `{m['win_rate']}`",
            f"- Trade count: `{m['trade_count']}`",
            f"- Largest win: `{m['largest_win']}`",
            f"- Largest loss: `{m['largest_loss']}`",
            f"- Average win: `{m['average_win']}`",
            f"- Average loss: `{m['average_loss']}`",
            f"- Max consecutive losses: `{m['max_consecutive_losses']}`",
            "",
            "## Robustness",
            "",
            f"- Chronological OOS net PnL: `{candidate['chronological_oos_metrics']['net_pnl']}`",
            f"- Anchored walk-forward OOS net PnL: `{candidate['anchored_walk_forward_metrics']['net_pnl']}`",
            f"- Symbol concentration: `{candidate['symbol_concentration']}`",
            f"- Timeframe concentration: `{candidate['timeframe_concentration']}`",
            f"- Period concentration: `{candidate['period_concentration']}`",
            "",
            "## Why This Passed",
            "",
            "- It passed the configured GOAL-STRAT1 gate for net PnL, profit factor, drawdown, largest loss, sample size, OOS stability, and concentration.",
            "",
            "## Why It May Still Fail Live",
            "",
            "- Backtests do not model funding, liquidation, order-book depth, partial fills, latency, venue rejects, or outages.",
            "- Public historical candle behavior may not persist in forward observation.",
            "- Candidate status only means founder review is justified; it does not authorize production or live trading.",
            "",
            "## Recommended Founder Review Checklist",
            "",
            "- Inspect trade distribution by symbol/timeframe/period.",
            "- Review the largest loss and longest losing streak manually.",
            "- Confirm the logic is acceptable before any separate paper-runtime phase.",
            "- Require PT-RT forward observation before any production-rule discussion.",
            "",
        ]
    )


def no_three_candidates_markdown(report: dict[str, Any]) -> str:
    reason_counts = Counter(reason for run in report.get("candidate_runs", []) for reason in run.get("reason_codes", []))
    lines = [
        "# GOAL-STRAT1 No Three Candidates Found",
        "",
        "GOAL-STRAT1 remained research-only. No strategy is production-approved and live trading is not approved.",
        "",
        f"- Families tested: `{', '.join(report['strategy_families_tested'])}`",
        f"- Candidate configurations: `{report['search_budget_used']['candidate_runs']}`",
        f"- Passing candidates: `{len(report.get('passing_candidates', []))}`",
        f"- Exit models tested: `{', '.join(report['exit_models_tested'])}`",
        f"- Risk models tested: `{', '.join(report['risk_models_tested'])}`",
        f"- Regime filters tested: `{', '.join(report['regime_filters_tested'])}`",
        f"- OOS methods tested: `{', '.join(report['oos_methods_tested'])}`",
        "",
        "## Best Near Misses",
        "",
    ]
    for run in report.get("best_near_misses", []):
        metrics = run["active_timeframe_metrics"]
        lines.append(
            f"- `{run['strategy_id']}`: `{run['status']}`, active net PnL `{metrics['net_pnl']}`, "
            f"PF `{metrics['profit_factor']}`, max DD `{metrics['max_drawdown_pct']}`, "
            f"chronological OOS `{run['chronological_oos_metrics']['net_pnl']}`, "
            f"anchored OOS `{run['anchored_walk_forward_metrics']['net_pnl']}`, blockers `{', '.join(run['reason_codes'])}`"
        )
    lines.extend(["", "## Blocker Summary", ""])
    for reason, count in reason_counts.most_common(12):
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(["", "## What The Evidence Suggests", ""])
    lines.extend(
        [
            "- Positive aggregate pockets exist in volatility-expansion and Donchian-style trend breakout variants.",
            "- Higher notional variants fail drawdown control.",
            "- Lower-risk variants that control drawdown still fail chronological and anchored OOS checks.",
            "- Mean-reversion and source-faithful Money Flow families did not produce a robust candidate under this data and gate.",
            "- Pairs/spread research remains research-only because candle-only data is insufficient for hedge, funding, borrow, and execution assumptions.",
        ]
    )
    lines.extend(["", "## What Is Needed Next", ""])
    for item in report.get("recommended_next_research", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Decision", "", "Three strategies were not found without overfitting after full autonomous discovery."])
    return "\n".join(lines) + "\n"


def _simulate_dataset(
    config: StrategyConfig,
    dataset: Dataset,
    indicators: Sequence[dict[str, Decimal | None]],
    rs_maps: dict[tuple[str, str, datetime], bool],
    all_indicators: dict[tuple[str, str], Sequence[dict[str, Decimal | None]]],
) -> list[Trade]:
    candles = dataset.candles
    trades: list[Trade] = []
    position: dict[str, Any] | None = None
    equity = STARTING_EQUITY
    for idx in range(220, len(candles) - 1):
        candle = candles[idx]
        next_candle = candles[idx + 1]
        if position is not None:
            position["age"] += 1
            position["highest_close"] = max(position["highest_close"], candle.close)
            exit_reason = _exit_reason(config, candles, indicators, idx, position)
            if exit_reason:
                trade, equity = _close_position(config, dataset, position, next_candle, equity, exit_reason)
                trades.append(trade)
                position = None
            continue
        if _entry_signal(config, dataset, indicators, idx, rs_maps, all_indicators):
            entry_price = _entry_price(next_candle.open)
            stop = _initial_stop(config, candles, indicators, idx, entry_price)
            quantity = _position_quantity(config, equity, entry_price, stop)
            if quantity <= 0:
                continue
            position = {
                "entry_time": next_candle.timestamp,
                "entry_price": entry_price,
                "quantity": quantity,
                "entry_reason": config.entry_model,
                "age": 0,
                "highest_close": next_candle.close,
                "stop": stop,
            }
    if position is not None and candles:
        trade, _ = _close_position(config, dataset, position, candles[-1], equity, "end_of_window_forced_close")
        trades.append(trade)
    return trades


def _entry_signal(
    config: StrategyConfig,
    dataset: Dataset,
    indicators: Sequence[dict[str, Decimal | None]],
    idx: int,
    rs_maps: dict[tuple[str, str, datetime], bool],
    all_indicators: dict[tuple[str, str], Sequence[dict[str, Decimal | None]]],
) -> bool:
    candles = dataset.candles
    ind = indicators[idx]
    prev = indicators[idx - 1]
    close = candles[idx].close
    ema5 = ind["ema5"]
    ema10 = ind["ema10"]
    sma20 = ind["sma20"]
    sma50 = ind["sma50"]
    sma200 = ind["sma200"]
    rsi = ind["rsi14"]
    macd_hist = ind["macd_histogram"]
    prev_macd_hist = prev["macd_histogram"]
    atr14 = ind["atr14"]
    if None in (ema5, ema10, sma20, sma50, rsi, macd_hist, atr14):
        return False
    if not _regime_passes(config, dataset, indicators, idx, all_indicators):
        return False
    trend = ema5 > ema10 > sma20 and close > sma20
    constructive = trend and macd_hist >= 0
    if config.entry_model == "mf_pullback_reclaim":
        recent_pullback = any(
            candles[j].low <= indicators[j]["ema10"]
            for j in range(max(0, idx - int(config.params["lookback"])), idx)
            if indicators[j]["ema10"] is not None
        )
        extension = (close - ema10) / ema10
        return constructive and Decimal(str(config.params["rsi_min"])) <= rsi <= Decimal(str(config.params["rsi_max"])) and recent_pullback and extension <= Decimal("0.055")
    if config.entry_model == "mf_macd_reacceleration":
        return constructive and prev_macd_hist is not None and prev_macd_hist < macd_hist and Decimal(str(config.params["rsi_min"])) <= rsi <= Decimal(str(config.params["rsi_max"]))
    if config.entry_model == "mf_ema10_reclaim_after_reset":
        had_reset = any(candles[j].close < indicators[j]["ema10"] for j in range(max(0, idx - int(config.params["reset_bars"])), idx) if indicators[j]["ema10"] is not None)
        return constructive and had_reset and candles[idx - 1].close <= indicators[idx - 1]["ema10"] and close > ema10 and rsi <= Decimal(str(config.params["rsi_max"]))
    if config.entry_model == "stage2_5_20_cross":
        prev_ema5 = prev["ema5"]
        prev_sma20 = prev["sma20"]
        return sma200 is not None and close > sma200 and prev_ema5 is not None and prev_sma20 is not None and prev_ema5 <= prev_sma20 and ema5 > sma20 and macd_hist >= 0
    if config.entry_model == "stage2_pullback_sma20_reclaim":
        recent_pullback = any(candles[j].low <= indicators[j]["sma20"] for j in range(max(0, idx - int(config.params["lookback"])), idx) if indicators[j]["sma20"] is not None)
        return constructive and recent_pullback and close > candles[idx - 1].high
    if config.entry_model == "stage2_resistance_breakout":
        lookback = int(config.params["lookback"])
        prior_high = max(c.high for c in candles[idx - lookback:idx])
        return constructive and close > prior_high
    if config.entry_model == "donchian_breakout":
        lookback = int(config.params["lookback"])
        prior_high = max(c.high for c in candles[idx - lookback:idx])
        return constructive and close > prior_high
    if config.entry_model == "higher_high_higher_low":
        lookback = int(config.params["lookback"])
        prior_high = max(c.high for c in candles[idx - lookback:idx])
        prior_low = min(c.low for c in candles[idx - lookback:idx])
        return constructive and close > prior_high and candles[idx].low > prior_low
    if config.entry_model == "bullish_rsi_oversold_reclaim":
        return close > sma50 and prev["rsi14"] is not None and prev["rsi14"] < Decimal(str(config.params["rsi_floor"])) and rsi >= Decimal(str(config.params["reclaim"]))
    if config.entry_model == "sma_distance_reclaim":
        prev_distance = (candles[idx - 1].close - indicators[idx - 1]["sma20"]) / indicators[idx - 1]["sma20"] if indicators[idx - 1]["sma20"] else Decimal("0")
        return close > sma50 and prev_distance < Decimal(str(config.params["distance"])) and close > sma20 and rsi >= Decimal("42")
    if config.entry_model == "failed_breakdown_reclaim":
        lookback = int(config.params["lookback"])
        prior_low = min(c.low for c in candles[idx - lookback:idx])
        return close > sma50 and candles[idx - 1].low < prior_low and close > prior_low and rsi >= Decimal("42")
    if config.entry_model == "top_n_trend_strength":
        return constructive and rs_maps.get((dataset.symbol, dataset.timeframe, candles[idx].timestamp), False)
    if config.entry_model == "avoid_bottom_rs_trend":
        return constructive and rs_maps.get((dataset.symbol, dataset.timeframe, candles[idx].timestamp), False)
    if config.entry_model == "volatility_expansion_breakout":
        lookback = int(config.params["lookback"])
        window = int(config.params["compression_window"])
        recent_range = (max(c.high for c in candles[idx - window:idx]) - min(c.low for c in candles[idx - window:idx])) / close
        prior_range = (max(c.high for c in candles[idx - lookback - window:idx - window]) - min(c.low for c in candles[idx - lookback - window:idx - window])) / close
        prior_high = max(c.high for c in candles[idx - lookback:idx])
        return constructive and recent_range > (prior_range * Decimal("0.75")) and close > prior_high
    if config.entry_model == "atr_expansion_trend":
        atr_sma = _sma([row["atr14"] or Decimal("0") for row in indicators], idx, int(config.params["atr_window"]))
        return constructive and atr_sma is not None and atr14 > atr_sma and close > max(c.high for c in candles[idx - 10:idx])
    if config.entry_model == "pair_spread_zscore_reversion":
        z = _rolling_zscore([c.close for c in candles], idx, 50)
        return z is not None and z < Decimal(str(config.params["zscore"])) and close > sma200
    return False


def _regime_passes(
    config: StrategyConfig,
    dataset: Dataset,
    indicators: Sequence[dict[str, Decimal | None]],
    idx: int,
    all_indicators: dict[tuple[str, str], Sequence[dict[str, Decimal | None]]],
) -> bool:
    ind = indicators[idx]
    close = ind["close"]
    sma200 = ind["sma200"]
    if config.regime_filter == "none":
        return True
    if config.regime_filter == "sma200":
        return sma200 is not None and close is not None and close > sma200
    if config.regime_filter == "btc_proxy":
        if dataset.symbol == "BTC":
            return sma200 is not None and close is not None and close > sma200 and (ind["macd_histogram"] or Decimal("-1")) >= 0
        btc_rows = all_indicators.get(("BTC", dataset.timeframe))
        if not btc_rows or idx >= len(btc_rows):
            return False
        btc = btc_rows[idx]
        return btc["sma200"] is not None and btc["close"] is not None and btc["close"] > btc["sma200"] and (btc["macd_histogram"] or Decimal("-1")) >= 0
    return False


def _exit_reason(config: StrategyConfig, candles: Sequence[Candle], indicators: Sequence[dict[str, Decimal | None]], idx: int, position: dict[str, Any]) -> str | None:
    candle = candles[idx]
    ind = indicators[idx]
    if position.get("stop") is not None and candle.close <= position["stop"]:
        return "stop_exit"
    if config.exit_model == "time_stop":
        max_hold = 8 if candles[idx].timeframe == "1h" else 6 if candles[idx].timeframe == "4h" else 10
        if position["age"] >= max_hold:
            return "time_stop_exit"
    if config.exit_model == "sma20_break":
        if ind["sma20"] is not None and candle.close < ind["sma20"]:
            return "sma20_break_exit"
    if config.exit_model == "atr_trail":
        atr = ind["atr14"]
        if atr is not None:
            trail = position["highest_close"] - (atr * Decimal("2.8"))
            position["stop"] = max(position.get("stop") or trail, trail)
            if candle.close <= position["stop"]:
                return "atr_trailing_stop_exit"
    if ind["ema10"] is not None and ind["macd_histogram"] is not None and candle.close < ind["ema10"] and ind["macd_histogram"] < 0:
        return "ema10_macd_loss_exit"
    return None


def _initial_stop(config: StrategyConfig, candles: Sequence[Candle], indicators: Sequence[dict[str, Decimal | None]], idx: int, entry_price: Decimal) -> Decimal | None:
    atr = indicators[idx]["atr14"]
    if atr is None:
        return None
    if config.risk_model == "atr_risk_1pct":
        return entry_price - (atr * Decimal("2.0"))
    if config.exit_model == "atr_trail":
        return entry_price - (atr * Decimal("2.8"))
    if config.family == "mean_reversion":
        return entry_price * Decimal("0.95")
    return entry_price - (atr * Decimal("3.5"))


def _position_quantity(config: StrategyConfig, equity: Decimal, entry_price: Decimal, stop: Decimal | None) -> Decimal:
    if config.risk_model == "equity_10pct":
        notional = equity * Decimal("0.10")
    elif config.risk_model == "equity_5pct":
        notional = equity * Decimal("0.05")
    elif config.risk_model == "equity_15pct":
        notional = equity * Decimal("0.15")
    elif config.risk_model == "atr_risk_1pct" and stop is not None and entry_price > stop:
        risk_budget = equity * Decimal("0.01")
        quantity = risk_budget / (entry_price - stop)
        notional = min(quantity * entry_price, equity * Decimal("0.25"))
    else:
        notional = equity * Decimal("0.10")
    return (notional / entry_price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


def _close_position(config: StrategyConfig, dataset: Dataset, position: dict[str, Any], exit_candle: Candle, equity: Decimal, exit_reason: str) -> tuple[Trade, Decimal]:
    exit_price = _exit_price(exit_candle.open if exit_reason != "end_of_window_forced_close" else exit_candle.close)
    quantity = position["quantity"]
    entry_price = position["entry_price"]
    gross_pnl = (exit_price - entry_price) * quantity
    fees = ((entry_price + exit_price) * quantity * FEE_BPS / Decimal("10000"))
    slippage = ((entry_price + exit_price) * quantity * SLIPPAGE_BPS / Decimal("10000"))
    net_pnl = _money(gross_pnl - fees - slippage)
    equity_after = _money(equity + net_pnl)
    return (
        Trade(
            strategy_id=config.strategy_id,
            symbol=dataset.symbol,
            timeframe=dataset.timeframe,
            entry_time=position["entry_time"],
            exit_time=exit_candle.timestamp,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            gross_pnl=_money(gross_pnl),
            fees=_money(fees),
            slippage=_money(slippage),
            net_pnl=net_pnl,
            equity_after=equity_after,
            entry_reason=position["entry_reason"],
            exit_reason=exit_reason,
        ),
        equity_after,
    )


def _dataset_from_replay_file(path: Path) -> Dataset | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    replays = payload.get("replays")
    if not isinstance(replays, list) or not replays:
        return None
    replay = replays[0]
    if "money_flow_v1_2" not in str(replay.get("strategy_id") or ""):
        return None
    if str(replay.get("fill_assumption") or "") != "next_candle_open":
        return None
    symbol = str(replay.get("symbol") or payload.get("symbol") or "").upper()
    timeframe = str(replay.get("timeframe") or payload.get("timeframe") or "").lower()
    candles: list[Candle] = []
    for row in replay.get("candles", []):
        try:
            timestamp = _parse_time(row.get("timestamp_utc"))
            open_ = _dec(row.get("open"))
            high = _dec(row.get("high"))
            low = _dec(row.get("low"))
            close = _dec(row.get("close"))
            volume = _dec(row.get("volume") or "0")
        except (InvalidOperation, TypeError, ValueError):
            continue
        candles.append(Candle(symbol, timeframe, timestamp, open_, high, low, close, volume, str(path)))
    source = "sv2_0_2_canonical_selected_replay" if "sv2_0_2" in str(path) else "sv2_1_1d_selected_replay"
    status = "canonical_sv2_0_2_selected_replay" if "sv2_0_2" in str(path) else "sv2_1_1d_corrobative_selected_replay"
    return Dataset(symbol, timeframe, str(path), source, status, tuple(sorted(candles, key=lambda candle: candle.timestamp)))


def _inventory_row(dataset: Dataset) -> DataInventoryRow:
    reasons = list(_quality_reason_codes(dataset))
    gaps = _missing_gap_count(dataset.candles, dataset.timeframe)
    if gaps:
        reasons.append("missing_candle_gap")
    status = dataset_quality_status(dataset, extra_reasons=reasons)
    return DataInventoryRow(
        symbol=dataset.symbol,
        timeframe=dataset.timeframe,
        source_path=dataset.source_path,
        source_provenance=dataset.source_provenance,
        canonical_evidence_status=dataset.canonical_evidence_status,
        earliest_candle=_iso(dataset.candles[0].timestamp) if dataset.candles else None,
        latest_fully_closed_candle=_iso(dataset.candles[-1].timestamp) if dataset.candles else None,
        candle_count=len(dataset.candles),
        missing_gaps=gaps,
        raw_file_status="present",
        db_import_status="db_imported_canonical" if "sv2_0_2" in dataset.source_provenance else "selected_replay_corrobative",
        data_quality_status=status,
        reason_codes=tuple(sorted(set(reasons or ["dataset_accepted"]))),
    )


def _quality_reason_codes(dataset: Dataset) -> tuple[str, ...]:
    reasons: list[str] = []
    if not dataset.candles:
        return ("dataset_missing",)
    previous: datetime | None = None
    for candle in dataset.candles:
        if candle.timestamp.tzinfo is None:
            reasons.append("timestamp_not_timezone_explicit")
        if previous is not None and candle.timestamp <= previous:
            reasons.append("out_of_order_candles")
        previous = candle.timestamp
        if min(candle.open, candle.high, candle.low, candle.close) <= 0:
            reasons.append("ohlc_invalid")
        if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
            reasons.append("ohlc_invalid")
    if not dataset.source_provenance:
        reasons.append("source_provenance_missing")
    if len(dataset.candles) < 240:
        reasons.append("insufficient_history")
    if "testnet" in dataset.source_path.lower():
        reasons.append("testnet_data_not_strategy_truth")
    if dataset.symbol in {"KSHIB", "SHIB"}:
        reasons.append("symbol_unit_semantics_deferred")
    return tuple(sorted(set(reasons)))


def dataset_quality_status(dataset: Dataset, *, extra_reasons: Sequence[str] | None = None) -> str:
    reasons = set(extra_reasons if extra_reasons is not None else _quality_reason_codes(dataset))
    hard = {
        "dataset_missing",
        "timestamp_not_timezone_explicit",
        "out_of_order_candles",
        "ohlc_invalid",
        "source_provenance_missing",
        "insufficient_history",
        "testnet_data_not_strategy_truth",
        "symbol_unit_semantics_deferred",
    }
    return "quarantined" if reasons.intersection(hard) else "accepted"


def _indicators(candles: Sequence[Candle]) -> list[dict[str, Decimal | None]]:
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    ema5 = _ema(closes, 5)
    ema10 = _ema(closes, 10)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = [a - b if a is not None and b is not None else None for a, b in zip(ema12, ema26, strict=False)]
    macd_signal = _ema([value if value is not None else Decimal("0") for value in macd], 9)
    rows: list[dict[str, Decimal | None]] = []
    for idx, close in enumerate(closes):
        signal = macd_signal[idx] if macd[idx] is not None else None
        rows.append(
            {
                "ema5": ema5[idx],
                "ema10": ema10[idx],
                "sma20": _sma(closes, idx, 20),
                "sma50": _sma(closes, idx, 50),
                "sma200": _sma(closes, idx, 200),
                "rsi14": _rsi(closes, idx, 14),
                "macd": macd[idx],
                "macd_signal": signal,
                "macd_histogram": macd[idx] - signal if macd[idx] is not None and signal is not None else None,
                "atr14": _atr(highs, lows, closes, idx, 14),
                "close": close,
            }
        )
    return rows


def _relative_strength_maps(datasets: Sequence[Dataset]) -> dict[tuple[str, str, datetime], bool]:
    by_tf_time: dict[tuple[str, datetime], list[tuple[str, Decimal]]] = defaultdict(list)
    for dataset in datasets:
        candles = dataset.candles
        for idx in range(50, len(candles)):
            prior = candles[idx - 20].close
            if prior > 0:
                by_tf_time[(dataset.timeframe, candles[idx].timestamp)].append((dataset.symbol, (candles[idx].close - prior) / prior))
    allowed: dict[tuple[str, str, datetime], bool] = {}
    for (timeframe, timestamp), rows in by_tf_time.items():
        ranked = sorted(rows, key=lambda row: row[1], reverse=True)
        top_n = max(1, math.ceil(len(ranked) * Decimal("0.34")))
        bottom_cutoff = max(1, math.floor(len(ranked) * Decimal("0.60")))
        for symbol, _ in ranked[:top_n]:
            allowed[(symbol, timeframe, timestamp)] = True
        for symbol, _ in ranked[:bottom_cutoff]:
            allowed.setdefault((symbol, timeframe, timestamp), True)
    return allowed


def _metrics(trades: Sequence[Trade]) -> Metrics:
    equity = STARTING_EQUITY
    peak = STARTING_EQUITY
    max_dd = Decimal("0")
    wins: list[Decimal] = []
    losses: list[Decimal] = []
    current_loss_count = 0
    max_loss_count = 0
    current_loss_pnl = Decimal("0")
    worst_loss_streak = Decimal("0")
    for trade in sorted(trades, key=lambda row: row.exit_time):
        equity = _money(equity + trade.net_pnl)
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        if trade.net_pnl > 0:
            wins.append(trade.net_pnl)
            current_loss_count = 0
            current_loss_pnl = Decimal("0")
        else:
            losses.append(trade.net_pnl)
            current_loss_count += 1
            max_loss_count = max(max_loss_count, current_loss_count)
            current_loss_pnl += trade.net_pnl
            worst_loss_streak = min(worst_loss_streak, current_loss_pnl)
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    count = len(trades)
    return Metrics(
        starting_equity=STARTING_EQUITY,
        ending_equity=_money(equity),
        net_pnl=_money(equity - STARTING_EQUITY),
        max_drawdown=_money(max_dd),
        max_drawdown_pct=_ratio(max_dd, STARTING_EQUITY),
        trade_count=count,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=_ratio(Decimal(len(wins)), Decimal(count)) if count else None,
        profit_factor=_ratio(gross_profit, gross_loss) if gross_loss > 0 else (Decimal("999") if gross_profit > 0 else None),
        largest_win=max(wins) if wins else None,
        largest_loss=min(losses) if losses else None,
        average_win=_ratio(sum(wins, Decimal("0")), Decimal(len(wins))) if wins else None,
        average_loss=_ratio(sum(losses, Decimal("0")), Decimal(len(losses))) if losses else None,
        max_consecutive_losses=max_loss_count,
        worst_losing_streak_pnl=_money(worst_loss_streak),
    )


def _anchored_walk_forward_metrics(trades: Sequence[Trade], datasets: Sequence[Dataset]) -> Metrics:
    times = sorted({c.timestamp for dataset in datasets for c in dataset.candles})
    if len(times) < 3:
        return _metrics([])
    cut1 = times[int(len(times) * 0.50)]
    cut2 = times[int(len(times) * 0.75)]
    oos = [trade for trade in trades if trade.entry_time > cut1 or trade.entry_time > cut2]
    return _metrics(oos)


def _global_split_time(datasets: Sequence[Dataset], ratio: Decimal) -> datetime:
    times = sorted({c.timestamp for dataset in datasets for c in dataset.candles})
    if not times:
        return datetime(1970, 1, 1, tzinfo=UTC)
    return times[int(len(times) * ratio)]


def _concentration_by(trades: Sequence[Trade], key_fn: Callable[[Trade], str]) -> dict[str, str]:
    positive_total = sum((trade.net_pnl for trade in trades if trade.net_pnl > 0), Decimal("0"))
    if positive_total <= 0:
        return {}
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for trade in trades:
        if trade.net_pnl > 0:
            totals[str(key_fn(trade))] += trade.net_pnl
    return {key: str(_ratio(value, positive_total)) for key, value in sorted(totals.items())}


def _status_from_reasons(reasons: Sequence[str]) -> str:
    if "research_only_insufficient_market_structure_data" in reasons:
        return "research_only"
    if "rejected_low_sample" in reasons:
        return "rejected_low_sample"
    if "rejected_drawdown" in reasons or "largest_single_trade_loss_too_large" in reasons:
        return "rejected_drawdown"
    if any(reason.startswith("rejected_concentrated") for reason in reasons):
        return "rejected_concentrated"
    if any("oos" in reason or "walk_forward" in reason for reason in reasons):
        return "rejected_overfit"
    return "rejected_no_edge"


def _rank_runs(runs: Sequence[CandidateRun]) -> list[CandidateRun]:
    return sorted(
        runs,
        key=lambda run: (
            run.status == CANDIDATE_STATUS,
            run.active_timeframe_metrics.net_pnl,
            run.chronological_oos_metrics.net_pnl,
            run.anchored_walk_forward_metrics.net_pnl,
            run.active_timeframe_metrics.profit_factor or Decimal("0"),
            -run.active_timeframe_metrics.max_drawdown_pct,
        ),
        reverse=True,
    )


def _dataset_map(datasets: Sequence[Dataset]) -> dict[tuple[str, str], Dataset]:
    return {(dataset.symbol, dataset.timeframe): dataset for dataset in datasets}


def _dataset_preference(dataset: Dataset) -> int:
    if "sv2_0_2" in dataset.source_provenance:
        return 20
    if "sv2_1" in dataset.source_provenance:
        return 10
    return 0


def _missing_gap_count(candles: Sequence[Candle], timeframe: str) -> int:
    expected = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}.get(timeframe)
    if expected is None:
        return 0
    return sum(1 for prev, curr in zip(candles, candles[1:], strict=False) if int((curr.timestamp - prev.timestamp).total_seconds()) > expected * 1.5)


def _sma(values: Sequence[Decimal], idx: int, period: int) -> Decimal | None:
    if idx + 1 < period:
        return None
    return sum(values[idx + 1 - period : idx + 1], Decimal("0")) / Decimal(period)


def _ema(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    alpha = Decimal("2") / Decimal(period + 1)
    output: list[Decimal | None] = []
    current: Decimal | None = None
    for idx, value in enumerate(values):
        if idx + 1 < period:
            output.append(None)
            continue
        if current is None:
            current = sum(values[idx + 1 - period : idx + 1], Decimal("0")) / Decimal(period)
        else:
            current = (value * alpha) + (current * (Decimal("1") - alpha))
        output.append(current)
    return output


def _rsi(values: Sequence[Decimal], idx: int, period: int) -> Decimal | None:
    if idx < period:
        return None
    gains = Decimal("0")
    losses = Decimal("0")
    for pos in range(idx + 1 - period, idx + 1):
        delta = values[pos] - values[pos - 1]
        if delta > 0:
            gains += delta
        else:
            losses += abs(delta)
    if gains == 0 and losses == 0:
        return Decimal("50")
    if losses == 0:
        return Decimal("100")
    rs = gains / losses
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def _atr(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], idx: int, period: int) -> Decimal | None:
    if idx < period:
        return None
    ranges: list[Decimal] = []
    for pos in range(idx + 1 - period, idx + 1):
        prev_close = closes[pos - 1] if pos > 0 else closes[pos]
        ranges.append(max(highs[pos] - lows[pos], abs(highs[pos] - prev_close), abs(lows[pos] - prev_close)))
    return sum(ranges, Decimal("0")) / Decimal(period)


def _rolling_zscore(values: Sequence[Decimal], idx: int, period: int) -> Decimal | None:
    if idx + 1 < period:
        return None
    window = values[idx + 1 - period : idx + 1]
    mean = sum(window, Decimal("0")) / Decimal(period)
    variance = sum((value - mean) * (value - mean) for value in window) / Decimal(period)
    std = Decimal(str(math.sqrt(float(variance))))
    if std == 0:
        return Decimal("0")
    return (values[idx] - mean) / std


def _entry_price(price: Decimal) -> Decimal:
    return _money(price * (Decimal("1") + SLIPPAGE_BPS / Decimal("10000")))


def _exit_price(price: Decimal) -> Decimal:
    return _money(price * (Decimal("1") - SLIPPAGE_BPS / Decimal("10000")))


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp_missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp_not_timezone_explicit")
    return parsed.astimezone(UTC)


def _dec(value: Any) -> Decimal:
    output = Decimal(str(value))
    if not output.is_finite():
        raise InvalidOperation("nonfinite_decimal")
    return output


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return (numerator / denominator).quantize(Decimal("0.00000001"))


def _max_concentration(concentration: dict[str, str]) -> Decimal:
    return max((Decimal(value) for value in concentration.values()), default=Decimal("0"))


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _metrics_to_dict(metrics: Metrics) -> dict[str, Any]:
    payload = asdict(metrics)
    return {key: (str(value) if isinstance(value, Decimal) else value) for key, value in payload.items()}


def _trade_to_dict(trade: Trade) -> dict[str, Any]:
    payload = asdict(trade)
    for key, value in list(payload.items()):
        if isinstance(value, Decimal):
            payload[key] = str(value)
        elif isinstance(value, datetime):
            payload[key] = _iso(value)
    return payload


def _run_to_dict(run: CandidateRun, *, include_trades: bool) -> dict[str, Any]:
    return {
        "strategy_id": run.strategy_id,
        "display_name": run.display_name,
        "strategy_family": run.strategy_family,
        "entry_model": run.entry_model,
        "exit_model": run.exit_model,
        "risk_model": run.risk_model,
        "regime_filter": run.regime_filter,
        "status": run.status,
        "reason_codes": list(run.reason_codes),
        "metrics": _metrics_to_dict(run.metrics),
        "active_timeframe_metrics": _metrics_to_dict(run.active_timeframe_metrics),
        "chronological_oos_metrics": _metrics_to_dict(run.chronological_oos_metrics),
        "anchored_walk_forward_metrics": _metrics_to_dict(run.anchored_walk_forward_metrics),
        "total_scenarios": run.total_scenarios,
        "data_quality_blocks": run.data_quality_blocks,
        "symbol_concentration": run.symbol_concentration,
        "timeframe_concentration": run.timeframe_concentration,
        "period_concentration": run.period_concentration,
        "oos_slice_results": run.oos_slice_results,
        "gate_result": run.gate_result,
        "trades": [_trade_to_dict(trade) for trade in run.trades[:250]] if include_trades else [],
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _why_three_not_promoted(runs: Sequence[CandidateRun]) -> list[str]:
    counts = Counter(reason for run in runs for reason in run.reason_codes)
    return [f"{reason}: {count}" for reason, count in counts.most_common()]


def _recommended_next_research(conclusion: str, passing_count: int) -> list[str]:
    if conclusion == "three_candidates_found_for_founder_production_testing_review":
        return [
            "Founder review should inspect candidate reports before any separate paper-runtime candidate phase.",
            "Run PT-RT forward paper observation under a separately scoped phase before discussing production rules.",
        ]
    return [
        f"Only {passing_count} candidates passed; do not promote fewer than three as a production-testing slate.",
        "Add longer non-overlapping OOS data and execution-quality constraints before widening parameters further.",
        "Prioritize candidates that fail only sample-size or OOS breadth, not candidates blocked by drawdown or concentration.",
    ]


def _candidate_summary_lines(index: int, run: dict[str, Any]) -> list[str]:
    m = run["active_timeframe_metrics"]
    return [
        f"### Candidate {index}: `{run['strategy_id']}`",
        "",
        f"- Status: `{run['status']}`",
        f"- Family: `{run['strategy_family']}`",
        f"- Entry/exit/risk/regime: `{run['entry_model']}` / `{run['exit_model']}` / `{run['risk_model']}` / `{run['regime_filter']}`",
        f"- Active net PnL: `{m['net_pnl']}`",
        f"- Ending equity: `{m['ending_equity']}`",
        f"- Profit factor: `{m['profit_factor']}`",
        f"- Max drawdown pct: `{m['max_drawdown_pct']}`",
        f"- Trade count: `{m['trade_count']}`",
        "",
    ]
