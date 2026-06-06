"""STRAT-DISC1 autonomous strategy discovery research harness.

This module is research-only. It reads local historical replay/evidence JSON,
validates candle quality, runs a bounded set of curated hypotheses, and labels
only founder-review candidates. It creates no production strategy changes,
runtime mutations, order intents, submitted orders, or exchange calls.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path
from typing import Any, Iterable, Sequence


STRAT_DISC1_PHASE = "STRAT-DISC1"
STRAT_DISC1_STATUS_CANDIDATE = "candidate_for_founder_production_testing_review"
STARTING_EQUITY = Decimal("10000")
DEFAULT_FEE_BPS = Decimal("5")
DEFAULT_SLIPPAGE_BPS = Decimal("2")
DEFAULT_POSITION_NOTIONAL_PCT = Decimal("1")
ACTIVE_PROMOTION_TIMEFRAMES = ("1h", "4h", "1d")
DIAGNOSTIC_TIMEFRAMES = ("15m",)
CANONICAL_SYMBOLS = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "HYPE", "SOL", "SUI", "XRP")
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
class StratDiscCandle:
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
class StratDiscDataset:
    symbol: str
    timeframe: str
    source_path: str
    source_provenance: str
    canonical_evidence_status: str
    candles: tuple[StratDiscCandle, ...]
    reason_codes: tuple[str, ...] = ()


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
class StrategyHypothesis:
    strategy_id: str
    display_name: str
    family: str
    description: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimulatedTrade:
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
    status: str
    reason_codes: tuple[str, ...]
    metrics: Metrics
    in_sample_metrics: Metrics
    out_of_sample_metrics: Metrics
    active_timeframe_metrics: Metrics
    trades: tuple[SimulatedTrade, ...]
    total_scenarios: int
    data_quality_blocks: int
    symbol_concentration: dict[str, str]
    timeframe_concentration: dict[str, str]
    period_concentration: dict[str, str]
    oos_slice_results: dict[str, Any]
    gate_result: dict[str, Any]


def build_strat_disc1_report(
    *,
    selected_replay_globs: Sequence[str] = DEFAULT_SELECTED_REPLAY_GLOBS,
    max_total_candidate_runs: int = 120,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC)
    datasets = load_replay_datasets(selected_replay_globs)
    inventory = build_data_inventory(datasets)
    valid_datasets = [
        dataset
        for dataset in datasets
        if _dataset_quality_status(dataset) == "accepted"
        and dataset.timeframe in (*ACTIVE_PROMOTION_TIMEFRAMES, *DIAGNOSTIC_TIMEFRAMES)
    ]
    hypotheses = curated_strategy_hypotheses()[:max_total_candidate_runs]
    candidate_runs = [run_hypothesis(hypothesis, valid_datasets) for hypothesis in hypotheses]
    passing = [run for run in candidate_runs if run.status == STRAT_DISC1_STATUS_CANDIDATE]
    top_candidates = sorted(
        passing,
        key=lambda run: (
            run.out_of_sample_metrics.net_pnl,
            run.active_timeframe_metrics.net_pnl,
            run.metrics.profit_factor or Decimal("0"),
        ),
        reverse=True,
    )[:3]
    rejected = [run for run in candidate_runs if run.status != STRAT_DISC1_STATUS_CANDIDATE]
    near_misses = sorted(
        rejected,
        key=lambda run: (
            run.out_of_sample_metrics.net_pnl,
            run.metrics.net_pnl,
            run.metrics.profit_factor or Decimal("0"),
        ),
        reverse=True,
    )[:8]
    conclusion = (
        "three_candidates_found_for_founder_production_testing_review"
        if len(top_candidates) >= 3
        else "no_three_candidates_found_without_overfitting"
    )
    report = {
        "phase": STRAT_DISC1_PHASE,
        "generated_at": _iso(generated_at),
        "status": "research_only_strategy_discovery_complete",
        "data_inventory": [asdict(row) for row in inventory],
        "candidate_runs": [_candidate_run_to_dict(run, include_trades=False) for run in candidate_runs],
        "strategy_families_tested": sorted({run.strategy_family for run in candidate_runs}),
        "rejected_candidates": [_candidate_run_to_dict(run, include_trades=False) for run in rejected],
        "passing_candidates": [_candidate_run_to_dict(run, include_trades=False) for run in passing],
        "top_3_candidates": [_candidate_run_to_dict(run, include_trades=True) for run in top_candidates],
        "top_near_misses": [_candidate_run_to_dict(run, include_trades=False) for run in near_misses],
        "candidate_gate": candidate_gate_policy(),
        "search_budget": {
            "max_strategy_families": len({hypothesis.family for hypothesis in hypotheses}),
            "max_candidate_variants_per_family": 20,
            "max_total_candidate_runs": max_total_candidate_runs,
            "broad_unbounded_optimizer": False,
        },
        "search_budget_used": {
            "candidate_runs": len(candidate_runs),
            "datasets_loaded": len(datasets),
            "datasets_accepted": len(valid_datasets),
        },
        "conclusion": conclusion,
        "why_three_were_not_promoted": [] if len(top_candidates) >= 3 else _why_three_not_promoted(candidate_runs),
        "recommended_next_research": _recommended_next_research(conclusion),
        "boundary_flags": boundary_flags(),
    }
    return _json_ready(report)


def load_replay_datasets(selected_replay_globs: Sequence[str]) -> list[StratDiscDataset]:
    by_key: dict[tuple[str, str], StratDiscDataset] = {}
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


def build_data_inventory(datasets: Sequence[StratDiscDataset]) -> list[DataInventoryRow]:
    return [_inventory_row(dataset) for dataset in datasets]


def curated_strategy_hypotheses() -> list[StrategyHypothesis]:
    return [
        StrategyHypothesis(
            "mf_repair_rsi_cooldown_pullback",
            "Money Flow repair: RSI cooldown pullback",
            "money_flow_repair",
            "Trend alignment plus RSI cooldown and pullback/reclaim entry discipline.",
            {"min_rsi": "45", "max_rsi": "68", "max_extension_pct": "0.045"},
        ),
        StrategyHypothesis(
            "mf_repair_macd_histogram_reaccelerating",
            "Money Flow repair: MACD histogram reaccelerating",
            "money_flow_repair",
            "Trend alignment with MACD histogram crossing back above zero or improving after reset.",
            {"min_rsi": "48", "max_rsi": "72"},
        ),
        StrategyHypothesis(
            "regime_gated_stage2_trend",
            "Regime-gated Stage 2 trend continuation",
            "trend_following",
            "EMA/SMA Stage 2 trend with SMA200 regime guard and MACD constructive context.",
            {"require_sma200": True, "max_extension_pct": "0.06"},
        ),
        StrategyHypothesis(
            "donchian_20_breakout_atr_trail",
            "Donchian 20 breakout with ATR trail",
            "trend_breakout",
            "20-candle breakout, EMA/SMA trend alignment, ATR-based trailing exit.",
            {"lookback": 20, "atr_trail": "2.5"},
        ),
        StrategyHypothesis(
            "donchian_50_breakout_btc_regime",
            "Donchian 50 breakout with BTC-style regime proxy",
            "trend_breakout",
            "50-candle breakout with stronger 200 SMA and MACD regime filter.",
            {"lookback": 50, "atr_trail": "3.0"},
        ),
        StrategyHypothesis(
            "volatility_expansion_breakout_rr20",
            "Volatility expansion breakout RR20",
            "volatility_expansion",
            "Low rolling-range avoidance with breakout above recent 20-candle high.",
            {"lookback": 20, "compression_threshold": "0.08"},
        ),
        StrategyHypothesis(
            "volatility_expansion_breakout_rr50",
            "Volatility expansion breakout RR50",
            "volatility_expansion",
            "Low rolling-range avoidance with breakout above recent 50-candle high.",
            {"lookback": 50, "compression_threshold": "0.14"},
        ),
        StrategyHypothesis(
            "mf_orig_stage2_pullback_reclaim",
            "MF-ORIG inspired Stage 2 pullback reclaim",
            "original_money_flow_stage",
            "Stage 2 5/10/20 alignment with pullback toward SMA20 and reclaim.",
            {"pullback_bars": 8},
        ),
        StrategyHypothesis(
            "mf_orig_stage2_resistance_breakout",
            "MF-ORIG inspired Stage 2 resistance breakout",
            "original_money_flow_stage",
            "Stage 2 alignment with break above recent resistance and MACD confirmation.",
            {"lookback": 20},
        ),
        StrategyHypothesis(
            "bullish_regime_rsi_mean_reversion",
            "Bullish-regime RSI oversold reclaim",
            "mean_reversion",
            "RSI oversold reclaim only when higher trend structure is bullish, with max hold.",
            {"rsi_floor": "38", "reclaim_rsi": "45", "max_hold_bars": 12},
        ),
        StrategyHypothesis(
            "relative_strength_top3_trend_proxy",
            "Relative strength top-3 trend proxy",
            "relative_strength_rotation",
            "Trade only symbols in the top third of 20-candle relative momentum for the timeframe.",
            {"rank_lookback": 20, "rank_fraction": "0.34"},
        ),
        StrategyHypothesis(
            "pairs_spread_research_proxy",
            "Pairs/spread research proxy",
            "pairs_spread_research",
            "Research-only contrarian spread proxy using symbol-normalized SMA distance.",
            {"max_hold_bars": 8},
        ),
    ]


def run_hypothesis(hypothesis: StrategyHypothesis, datasets: Sequence[StratDiscDataset]) -> CandidateRun:
    trades: list[SimulatedTrade] = []
    data_quality_blocks = 0
    scenario_count = 0
    relative_strength_maps = _relative_strength_maps(datasets) if hypothesis.strategy_id == "relative_strength_top3_trend_proxy" else {}
    for dataset in datasets:
        if _dataset_quality_status(dataset) != "accepted":
            data_quality_blocks += 1
            continue
        scenario_count += 1
        trades.extend(_simulate_dataset(hypothesis, dataset, relative_strength_maps))
    metrics = _metrics(trades)
    active_trades = [trade for trade in trades if trade.timeframe in ACTIVE_PROMOTION_TIMEFRAMES]
    active_metrics = _metrics(active_trades)
    split_time = _global_split_time(datasets)
    in_sample_trades = [trade for trade in trades if trade.entry_time <= split_time]
    out_sample_trades = [trade for trade in trades if trade.entry_time > split_time]
    in_sample_metrics = _metrics(in_sample_trades)
    out_sample_metrics = _metrics(out_sample_trades)
    symbol_conc = _concentration_by(trades, lambda trade: trade.symbol)
    timeframe_conc = _concentration_by(trades, lambda trade: trade.timeframe)
    period_conc = _concentration_by(trades, lambda trade: f"{trade.entry_time.year}-H{1 if trade.entry_time.month <= 6 else 2}")
    oos = _oos_slice_results(trades, split_time)
    gate = evaluate_candidate_gate(
        hypothesis=hypothesis,
        metrics=metrics,
        active_metrics=active_metrics,
        out_sample_metrics=out_sample_metrics,
        trades=trades,
        symbol_concentration=symbol_conc,
        timeframe_concentration=timeframe_conc,
        period_concentration=period_conc,
    )
    return CandidateRun(
        strategy_id=hypothesis.strategy_id,
        display_name=hypothesis.display_name,
        strategy_family=hypothesis.family,
        status=gate["status"],
        reason_codes=tuple(gate["reason_codes"]),
        metrics=metrics,
        in_sample_metrics=in_sample_metrics,
        out_of_sample_metrics=out_sample_metrics,
        active_timeframe_metrics=active_metrics,
        trades=tuple(trades),
        total_scenarios=scenario_count,
        data_quality_blocks=data_quality_blocks,
        symbol_concentration=symbol_conc,
        timeframe_concentration=timeframe_conc,
        period_concentration=period_conc,
        oos_slice_results=oos,
        gate_result=gate,
    )


def evaluate_candidate_gate(
    *,
    hypothesis: StrategyHypothesis,
    metrics: Metrics,
    active_metrics: Metrics,
    out_sample_metrics: Metrics,
    trades: Sequence[SimulatedTrade],
    symbol_concentration: dict[str, str],
    timeframe_concentration: dict[str, str],
    period_concentration: dict[str, str],
) -> dict[str, Any]:
    reasons: list[str] = []
    min_trades = 20 if all(trade.timeframe == "1d" for trade in trades) else 50
    if active_metrics.trade_count < min_trades:
        reasons.append("rejected_low_sample")
    if active_metrics.net_pnl <= 0 or metrics.ending_equity <= STARTING_EQUITY:
        reasons.append("rejected_no_edge")
    if out_sample_metrics.net_pnl < 0:
        reasons.append("out_of_sample_net_pnl_negative")
    if metrics.profit_factor is None or metrics.profit_factor < Decimal("1.15"):
        reasons.append("profit_factor_below_threshold")
    if metrics.max_drawdown_pct > Decimal("0.30"):
        reasons.append("rejected_drawdown")
    largest_loss_pct = (abs(metrics.largest_loss or Decimal("0")) / STARTING_EQUITY) if metrics.largest_loss else Decimal("0")
    if largest_loss_pct > Decimal("0.08"):
        reasons.append("largest_single_trade_loss_too_large")
    if _max_concentration(symbol_concentration) > Decimal("0.45"):
        reasons.append("rejected_concentrated_symbol")
    if _max_concentration(period_concentration) > Decimal("0.60"):
        reasons.append("rejected_concentrated_period")
    if "15m" in timeframe_concentration and Decimal(timeframe_concentration["15m"]) > Decimal("0.20"):
        reasons.append("diagnostic_15m_contribution_too_high_for_promotion")
    if hypothesis.family == "pairs_spread_research":
        reasons.append("research_only_insufficient_market_structure_data")
    status = STRAT_DISC1_STATUS_CANDIDATE if not reasons else _status_from_reasons(reasons)
    return {
        "status": status,
        "passed": status == STRAT_DISC1_STATUS_CANDIDATE,
        "reason_codes": reasons or ["candidate_gate_passed"],
        "min_trades_required": min_trades,
        "profit_factor_threshold": "1.15",
        "max_drawdown_pct_threshold": "0.30",
        "largest_loss_pct_threshold": "0.08",
        "max_symbol_contribution_threshold": "0.45",
        "max_period_contribution_threshold": "0.60",
        "uses_15m_for_promotion": False,
    }


def candidate_gate_policy() -> dict[str, Any]:
    return {
        "positive_net_pnl_after_fees_slippage": True,
        "out_of_sample_net_pnl_nonnegative": True,
        "profit_factor_min": "1.15",
        "max_drawdown_pct_max": "0.30",
        "largest_single_trade_loss_pct_max": "0.08",
        "min_trades_total_1h_4h": 50,
        "min_trades_total_1d": 20,
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
        "creates_order_intent": False,
        "creates_prepared_venue_order": False,
        "creates_submitted_order": False,
        "submits_live_orders": False,
        "submits_testnet_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "uses_testnet_data_as_strategy_truth": False,
        "approves_live_trading": False,
        "approves_production_strategy": False,
        "uses_dashboard_date_filters_as_canonical_evidence": False,
    }


def strat_disc1_report_to_markdown(report: dict[str, Any]) -> str:
    top = report.get("top_3_candidates", [])
    lines = [
        "# STRAT-DISC1 Autonomous Strategy Discovery",
        "",
        "## Summary",
        "",
        "STRAT-DISC1 is research-only. No strategy is production-approved. Live trading is not approved.",
        "",
        f"- Conclusion: `{report['conclusion']}`",
        f"- Candidate runs: `{report['search_budget_used']['candidate_runs']}`",
        f"- Passing candidates: `{len(report.get('passing_candidates', []))}`",
        f"- Datasets accepted: `{report['search_budget_used']['datasets_accepted']}`",
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
    lines.extend(["", "## Strategy Families Tested", ""])
    for family in report["strategy_families_tested"]:
        lines.append(f"- `{family}`")
    lines.extend(["", "## Candidate Gate", ""])
    for key, value in report["candidate_gate"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Top Candidates", ""])
    if top:
        for index, run in enumerate(top, start=1):
            lines.extend(_candidate_markdown(index, run))
    else:
        lines.append("No strategy passed the full candidate gate.")
    lines.extend(["", "## Near Misses", ""])
    for run in report.get("top_near_misses", [])[:5]:
        lines.append(
            f"- `{run['strategy_id']}`: `{run['status']}`, net PnL `{run['metrics']['net_pnl']}`, "
            f"PF `{run['metrics']['profit_factor']}`, blockers `{', '.join(run['reason_codes'])}`"
        )
    lines.extend(["", "## Boundaries", ""])
    for key, value in report["boundary_flags"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    if report["conclusion"] == "three_candidates_found_for_founder_production_testing_review":
        lines.append("Three strategies are ready for founder production-testing review.")
    else:
        lines.append("Three strategies were not found without overfitting. No strategy should be promoted yet.")
    return "\n".join(lines) + "\n"


def write_strat_disc1_outputs(report: dict[str, Any], markdown_output: str | Path, json_output: str | Path) -> None:
    Path(markdown_output).write_text(strat_disc1_report_to_markdown(report), encoding="utf-8")
    Path(json_output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for index, candidate in enumerate(report.get("top_3_candidates", [])[:3], start=1):
        slug = candidate["strategy_id"]
        Path(f"docs/strat_disc1_candidate_{index}_{slug}.md").write_text(
            _candidate_report_markdown(index, candidate),
            encoding="utf-8",
        )


def _dataset_from_replay_file(path: Path) -> StratDiscDataset | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    replays = payload.get("replays")
    if not isinstance(replays, list) or not replays:
        return None
    replay = replays[0]
    strategy_id = str(replay.get("strategy_id") or "")
    fill_assumption = str(replay.get("fill_assumption") or "")
    if "money_flow_v1_2" not in strategy_id or fill_assumption != "next_candle_open":
        return None
    symbol = str(replay.get("symbol") or payload.get("symbol") or "").upper()
    timeframe = _canonical_timeframe(str(replay.get("timeframe") or payload.get("timeframe") or ""))
    candles: list[StratDiscCandle] = []
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
        candles.append(
            StratDiscCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                source_path=str(path),
            )
        )
    source = "sv2_0_2_canonical_selected_replay" if "sv2_0_2" in str(path) else "sv2_1_1d_selected_replay"
    status = "canonical_sv2_0_2_selected_replay" if "sv2_0_2" in str(path) else "sv2_1_1d_corrobative_selected_replay"
    return StratDiscDataset(
        symbol=symbol,
        timeframe=timeframe,
        source_path=str(path),
        source_provenance=source,
        canonical_evidence_status=status,
        candles=tuple(sorted(candles, key=lambda candle: candle.timestamp)),
    )


def _inventory_row(dataset: StratDiscDataset) -> DataInventoryRow:
    quality_reasons = list(_quality_reason_codes(dataset))
    gaps = _missing_gap_count(dataset.candles, dataset.timeframe)
    if gaps:
        quality_reasons.append("missing_candle_gap")
    status = _dataset_quality_status(dataset, extra_reasons=quality_reasons)
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
        reason_codes=tuple(quality_reasons or ["dataset_accepted"]),
    )


def _quality_reason_codes(dataset: StratDiscDataset) -> tuple[str, ...]:
    reasons: list[str] = []
    if not dataset.candles:
        return ("dataset_missing",)
    prev: datetime | None = None
    for candle in dataset.candles:
        if candle.timestamp.tzinfo is None:
            reasons.append("timestamp_not_timezone_explicit")
        if prev is not None and candle.timestamp <= prev:
            reasons.append("out_of_order_candles")
        prev = candle.timestamp
        if min(candle.open, candle.high, candle.low, candle.close) <= 0:
            reasons.append("ohlc_invalid")
        if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
            reasons.append("ohlc_invalid")
    if not dataset.source_provenance:
        reasons.append("source_provenance_missing")
    if len(dataset.candles) < 80:
        reasons.append("insufficient_history")
    return tuple(sorted(set(reasons)))


def _dataset_quality_status(dataset: StratDiscDataset, *, extra_reasons: Sequence[str] | None = None) -> str:
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


def _simulate_dataset(
    hypothesis: StrategyHypothesis,
    dataset: StratDiscDataset,
    relative_strength_maps: dict[tuple[str, str, datetime], bool],
) -> list[SimulatedTrade]:
    candles = dataset.candles
    indicators = _indicators(candles)
    trades: list[SimulatedTrade] = []
    open_position: dict[str, Any] | None = None
    realized_equity = STARTING_EQUITY
    max_hold = int(hypothesis.params.get("max_hold_bars", 10_000))
    for idx in range(55, len(candles) - 1):
        candle = candles[idx]
        next_candle = candles[idx + 1]
        ind = indicators[idx]
        if open_position is not None:
            open_position["age"] += 1
            exit_reason = _exit_reason(hypothesis, candles, indicators, idx, open_position, max_hold)
            if exit_reason:
                trade, realized_equity = _close_position(hypothesis, dataset, open_position, next_candle, realized_equity, exit_reason)
                trades.append(trade)
                open_position = None
            continue
        if _entry_signal(hypothesis, candles, indicators, idx, relative_strength_maps):
            entry_price = _entry_price(next_candle.open)
            if entry_price <= 0:
                continue
            notional = realized_equity * DEFAULT_POSITION_NOTIONAL_PCT
            quantity = (notional / entry_price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
            if quantity <= 0:
                continue
            open_position = {
                "entry_time": next_candle.timestamp,
                "entry_signal_time": candle.timestamp,
                "entry_price": entry_price,
                "quantity": quantity,
                "entry_reason": hypothesis.strategy_id,
                "age": 0,
                "highest_close": next_candle.close,
                "stop": _initial_stop(hypothesis, candles, indicators, idx, entry_price),
            }
    if open_position is not None and candles:
        trade, _ = _close_position(hypothesis, dataset, open_position, candles[-1], realized_equity, "end_of_window_forced_close")
        trades.append(trade)
    return trades


def _entry_signal(
    hypothesis: StrategyHypothesis,
    candles: Sequence[StratDiscCandle],
    indicators: Sequence[dict[str, Decimal | None]],
    idx: int,
    relative_strength_maps: dict[tuple[str, str, datetime], bool],
) -> bool:
    ind = indicators[idx]
    prev = indicators[idx - 1]
    candle = candles[idx]
    close = candle.close
    ema5 = ind.get("ema5")
    ema10 = ind.get("ema10")
    sma20 = ind.get("sma20")
    sma50 = ind.get("sma50")
    sma200 = ind.get("sma200")
    rsi = ind.get("rsi14")
    macd_hist = ind.get("macd_histogram")
    prev_macd_hist = prev.get("macd_histogram")
    atr = ind.get("atr14")
    if None in (ema5, ema10, sma20, rsi, macd_hist):
        return False
    trend = ema5 > ema10 > sma20 and close > sma20
    macd_ok = macd_hist >= 0
    if hypothesis.strategy_id == "mf_repair_rsi_cooldown_pullback":
        max_extension = Decimal(str(hypothesis.params["max_extension_pct"]))
        extension = (close - ema10) / ema10
        recent_pullback = any(candles[j].low <= indicators[j]["ema10"] for j in range(max(0, idx - 6), idx + 1) if indicators[j]["ema10"] is not None)
        return trend and macd_ok and Decimal("45") <= rsi <= Decimal("68") and extension <= max_extension and recent_pullback
    if hypothesis.strategy_id == "mf_repair_macd_histogram_reaccelerating":
        return trend and Decimal("48") <= rsi <= Decimal("72") and macd_hist >= 0 and prev_macd_hist is not None and prev_macd_hist < macd_hist
    if hypothesis.strategy_id == "regime_gated_stage2_trend":
        if sma200 is None or close <= sma200:
            return False
        extension = (close - ema10) / ema10
        return trend and macd_ok and extension <= Decimal("0.06")
    if hypothesis.strategy_id in {"donchian_20_breakout_atr_trail", "donchian_50_breakout_btc_regime"}:
        lookback = int(hypothesis.params["lookback"])
        if idx < lookback:
            return False
        prior_high = max(c.high for c in candles[idx - lookback:idx])
        regime_ok = True if hypothesis.strategy_id == "donchian_20_breakout_atr_trail" else sma200 is not None and close > sma200
        return trend and regime_ok and close > prior_high and macd_ok
    if hypothesis.strategy_id in {"volatility_expansion_breakout_rr20", "volatility_expansion_breakout_rr50"}:
        lookback = int(hypothesis.params["lookback"])
        threshold = Decimal(str(hypothesis.params["compression_threshold"]))
        if idx < lookback + 5:
            return False
        prior_range = (max(c.high for c in candles[idx - lookback:idx]) - min(c.low for c in candles[idx - lookback:idx])) / close
        recent_high = max(c.high for c in candles[idx - 20:idx])
        return trend and macd_ok and prior_range >= threshold and close > recent_high
    if hypothesis.strategy_id == "mf_orig_stage2_pullback_reclaim":
        recent_pullback = any(candles[j].low <= indicators[j]["sma20"] for j in range(max(0, idx - 8), idx) if indicators[j]["sma20"] is not None)
        return trend and macd_ok and recent_pullback and close > candles[idx - 1].high
    if hypothesis.strategy_id == "mf_orig_stage2_resistance_breakout":
        prior_high = max(c.high for c in candles[idx - 20:idx])
        return trend and macd_ok and close > prior_high
    if hypothesis.strategy_id == "bullish_regime_rsi_mean_reversion":
        if sma50 is None or close <= sma50 or not trend:
            return False
        prev_rsi = prev.get("rsi14")
        return prev_rsi is not None and prev_rsi < Decimal("38") and rsi >= Decimal("45")
    if hypothesis.strategy_id == "relative_strength_top3_trend_proxy":
        return trend and macd_ok and relative_strength_maps.get((candle.symbol, candle.timeframe, candle.timestamp), False)
    if hypothesis.strategy_id == "pairs_spread_research_proxy":
        if sma20 is None or sma50 is None:
            return False
        distance = (close - sma20) / sma20
        return close > sma50 and distance < Decimal("-0.04")
    return False


def _exit_reason(
    hypothesis: StrategyHypothesis,
    candles: Sequence[StratDiscCandle],
    indicators: Sequence[dict[str, Decimal | None]],
    idx: int,
    open_position: dict[str, Any],
    max_hold: int,
) -> str | None:
    candle = candles[idx]
    ind = indicators[idx]
    sma20 = ind.get("sma20")
    ema10 = ind.get("ema10")
    macd_hist = ind.get("macd_histogram")
    atr = ind.get("atr14")
    if candle.close > open_position["highest_close"]:
        open_position["highest_close"] = candle.close
    if open_position["age"] >= max_hold:
        return "max_hold_exit"
    stop = open_position.get("stop")
    if stop is not None and candle.close <= stop:
        return "stop_exit"
    if hypothesis.strategy_id.startswith("donchian") and atr is not None:
        multiple = Decimal(str(hypothesis.params.get("atr_trail", "2.5")))
        trail = open_position["highest_close"] - (atr * multiple)
        open_position["stop"] = max(open_position.get("stop") or trail, trail)
        if candle.close <= open_position["stop"]:
            return "atr_trailing_stop_exit"
    if sma20 is not None and candle.close < sma20:
        return "close_below_sma20_exit"
    if ema10 is not None and candle.close < ema10 and macd_hist is not None and macd_hist < 0:
        return "ema10_macd_loss_exit"
    return None


def _close_position(
    hypothesis: StrategyHypothesis,
    dataset: StratDiscDataset,
    open_position: dict[str, Any],
    exit_candle: StratDiscCandle,
    realized_equity: Decimal,
    exit_reason: str,
) -> tuple[SimulatedTrade, Decimal]:
    exit_price = _exit_price(exit_candle.open if exit_reason != "end_of_window_forced_close" else exit_candle.close)
    quantity = open_position["quantity"]
    entry_price = open_position["entry_price"]
    gross_pnl = (exit_price - entry_price) * quantity
    entry_fee = entry_price * quantity * DEFAULT_FEE_BPS / Decimal("10000")
    exit_fee = exit_price * quantity * DEFAULT_FEE_BPS / Decimal("10000")
    slippage = ((entry_price + exit_price) * quantity * DEFAULT_SLIPPAGE_BPS / Decimal("10000"))
    fees = entry_fee + exit_fee
    net_pnl = _money(gross_pnl - fees - slippage)
    equity_after = _money(realized_equity + net_pnl)
    trade = SimulatedTrade(
        strategy_id=hypothesis.strategy_id,
        symbol=dataset.symbol,
        timeframe=dataset.timeframe,
        entry_time=open_position["entry_time"],
        exit_time=exit_candle.timestamp,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        gross_pnl=_money(gross_pnl),
        fees=_money(fees),
        slippage=_money(slippage),
        net_pnl=net_pnl,
        equity_after=equity_after,
        entry_reason=open_position["entry_reason"],
        exit_reason=exit_reason,
    )
    return trade, equity_after


def _indicators(candles: Sequence[StratDiscCandle]) -> list[dict[str, Decimal | None]]:
    closes = [candle.close for candle in candles]
    highs = [candle.high for candle in candles]
    lows = [candle.low for candle in candles]
    ema5 = _ema(closes, 5)
    ema10 = _ema(closes, 10)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = [a - b if a is not None and b is not None else None for a, b in zip(ema12, ema26, strict=False)]
    macd_signal = _ema([value if value is not None else Decimal("0") for value in macd], 9)
    rows: list[dict[str, Decimal | None]] = []
    for idx, close in enumerate(closes):
        atr14 = _atr(highs, lows, closes, idx, 14)
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
                "atr14": atr14,
                "close": close,
            }
        )
    return rows


def _metrics(trades: Sequence[SimulatedTrade]) -> Metrics:
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
        profit_factor=_ratio(gross_profit, gross_loss) if gross_loss > 0 else (None if gross_profit <= 0 else Decimal("999")),
        largest_win=max(wins) if wins else None,
        largest_loss=min(losses) if losses else None,
        average_win=_ratio(sum(wins, Decimal("0")), Decimal(len(wins))) if wins else None,
        average_loss=_ratio(sum(losses, Decimal("0")), Decimal(len(losses))) if losses else None,
        max_consecutive_losses=max_loss_count,
        worst_losing_streak_pnl=_money(worst_loss_streak),
    )


def _relative_strength_maps(datasets: Sequence[StratDiscDataset]) -> dict[tuple[str, str, datetime], bool]:
    by_tf_time: dict[tuple[str, datetime], list[tuple[str, Decimal]]] = defaultdict(list)
    closes_by_key = {(dataset.symbol, dataset.timeframe): dataset.candles for dataset in datasets}
    for (symbol, timeframe), candles in closes_by_key.items():
        for idx in range(20, len(candles)):
            prior = candles[idx - 20].close
            if prior > 0:
                momentum = (candles[idx].close - prior) / prior
                by_tf_time[(timeframe, candles[idx].timestamp)].append((symbol, momentum))
    allowed: dict[tuple[str, str, datetime], bool] = {}
    for (timeframe, timestamp), rows in by_tf_time.items():
        ranked = sorted(rows, key=lambda row: row[1], reverse=True)
        top_n = max(1, math.ceil(len(ranked) * 0.34))
        for symbol, _ in ranked[:top_n]:
            allowed[(symbol, timeframe, timestamp)] = True
    return allowed


def _global_split_time(datasets: Sequence[StratDiscDataset]) -> datetime:
    times = sorted({candle.timestamp for dataset in datasets for candle in dataset.candles})
    if not times:
        return datetime(1970, 1, 1, tzinfo=UTC)
    return times[int(len(times) * 0.65)]


def _oos_slice_results(trades: Sequence[SimulatedTrade], split_time: datetime) -> dict[str, Any]:
    before = _metrics([trade for trade in trades if trade.entry_time <= split_time])
    after = _metrics([trade for trade in trades if trade.entry_time > split_time])
    by_timeframe = {key: _metrics([trade for trade in trades if trade.timeframe == key]) for key in ACTIVE_PROMOTION_TIMEFRAMES}
    return {
        "split_time": _iso(split_time),
        "in_sample_net_pnl": str(before.net_pnl),
        "out_of_sample_net_pnl": str(after.net_pnl),
        "active_timeframe_net_pnl": {key: str(value.net_pnl) for key, value in by_timeframe.items()},
        "active_timeframe_trade_count": {key: value.trade_count for key, value in by_timeframe.items()},
    }


def _concentration_by(trades: Sequence[SimulatedTrade], key_fn: Any) -> dict[str, str]:
    positive_total = sum((trade.net_pnl for trade in trades if trade.net_pnl > 0), Decimal("0"))
    if positive_total <= 0:
        return {}
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for trade in trades:
        if trade.net_pnl > 0:
            totals[str(key_fn(trade))] += trade.net_pnl
    return {key: str(_ratio(value, positive_total)) for key, value in sorted(totals.items())}


def _max_concentration(concentration: dict[str, str]) -> Decimal:
    return max((Decimal(value) for value in concentration.values()), default=Decimal("0"))


def _status_from_reasons(reasons: Sequence[str]) -> str:
    if "research_only_insufficient_market_structure_data" in reasons:
        return "research_only"
    if "rejected_low_sample" in reasons:
        return "rejected_low_sample"
    if "rejected_drawdown" in reasons or "largest_single_trade_loss_too_large" in reasons:
        return "rejected_drawdown"
    if any(reason.startswith("rejected_concentrated") for reason in reasons):
        return "rejected_concentrated"
    if "out_of_sample_net_pnl_negative" in reasons:
        return "rejected_overfit"
    return "rejected_no_edge"


def _missing_gap_count(candles: Sequence[StratDiscCandle], timeframe: str) -> int:
    expected = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}.get(timeframe)
    if expected is None:
        return 0
    gaps = 0
    for prev, curr in zip(candles, candles[1:], strict=False):
        delta = int((curr.timestamp - prev.timestamp).total_seconds())
        if delta > expected * 1.5:
            gaps += 1
    return gaps


def _dataset_preference(dataset: StratDiscDataset) -> int:
    if "sv2_0_2" in dataset.source_provenance:
        return 20
    if "sv2_1" in dataset.source_provenance:
        return 10
    return 0


def _initial_stop(
    hypothesis: StrategyHypothesis,
    candles: Sequence[StratDiscCandle],
    indicators: Sequence[dict[str, Decimal | None]],
    idx: int,
    entry_price: Decimal,
) -> Decimal | None:
    atr = indicators[idx].get("atr14")
    if hypothesis.strategy_id.startswith("donchian") and atr is not None:
        return entry_price - (atr * Decimal(str(hypothesis.params.get("atr_trail", "2.5"))))
    if hypothesis.family == "mean_reversion":
        return entry_price * Decimal("0.94")
    return None


def _entry_price(price: Decimal) -> Decimal:
    return _money(price * (Decimal("1") + DEFAULT_SLIPPAGE_BPS / Decimal("10000")))


def _exit_price(price: Decimal) -> Decimal:
    return _money(price * (Decimal("1") - DEFAULT_SLIPPAGE_BPS / Decimal("10000")))


def _sma(values: Sequence[Decimal], idx: int, period: int) -> Decimal | None:
    if idx + 1 < period:
        return None
    return sum(values[idx + 1 - period:idx + 1], Decimal("0")) / Decimal(period)


def _ema(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    if not values:
        return []
    alpha = Decimal("2") / Decimal(period + 1)
    out: list[Decimal | None] = []
    current: Decimal | None = None
    for idx, value in enumerate(values):
        if idx + 1 < period:
            out.append(None)
            continue
        if current is None:
            current = sum(values[idx + 1 - period:idx + 1], Decimal("0")) / Decimal(period)
        else:
            current = (value * alpha) + (current * (Decimal("1") - alpha))
        out.append(current)
    return out


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


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp_missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp_not_timezone_explicit")
    return parsed.astimezone(UTC)


def _dec(value: Any) -> Decimal:
    value_dec = Decimal(str(value))
    if not value_dec.is_finite():
        raise InvalidOperation("nonfinite_decimal")
    return value_dec


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return (numerator / denominator).quantize(Decimal("0.00000001"))


def _canonical_timeframe(value: str) -> str:
    return value.lower().replace("1d", "1d")


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _metrics_to_dict(metrics: Metrics) -> dict[str, Any]:
    payload = asdict(metrics)
    return {key: (str(value) if isinstance(value, Decimal) else value) for key, value in payload.items()}


def _trade_to_dict(trade: SimulatedTrade) -> dict[str, Any]:
    payload = asdict(trade)
    for key, value in list(payload.items()):
        if isinstance(value, Decimal):
            payload[key] = str(value)
        elif isinstance(value, datetime):
            payload[key] = _iso(value)
    return payload


def _candidate_run_to_dict(run: CandidateRun, *, include_trades: bool) -> dict[str, Any]:
    return {
        "strategy_id": run.strategy_id,
        "display_name": run.display_name,
        "strategy_family": run.strategy_family,
        "status": run.status,
        "reason_codes": list(run.reason_codes),
        "metrics": _metrics_to_dict(run.metrics),
        "in_sample_metrics": _metrics_to_dict(run.in_sample_metrics),
        "out_of_sample_metrics": _metrics_to_dict(run.out_of_sample_metrics),
        "active_timeframe_metrics": _metrics_to_dict(run.active_timeframe_metrics),
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
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _why_three_not_promoted(candidate_runs: Sequence[CandidateRun]) -> list[str]:
    counts = Counter(reason for run in candidate_runs for reason in run.reason_codes)
    return [f"{reason}: {count}" for reason, count in counts.most_common()]


def _recommended_next_research(conclusion: str) -> list[str]:
    if conclusion == "three_candidates_found_for_founder_production_testing_review":
        return [
            "Run founder review against candidate reports before any paper-runtime inclusion.",
            "Paper-test candidates in a separate PT scope with public mainnet strategy truth only.",
        ]
    return [
        "Add longer non-overlapping OOS candle windows before widening parameter ranges.",
        "Focus on regime-gated trend continuation and volatility-expansion filters without 15m promotion.",
        "Do not promote any strategy until concentration and OOS blockers clear.",
    ]


def _candidate_markdown(index: int, run: dict[str, Any]) -> list[str]:
    m = run["metrics"]
    return [
        f"### Candidate {index}: `{run['strategy_id']}`",
        "",
        f"- Status: `{run['status']}`",
        f"- Family: `{run['strategy_family']}`",
        f"- Net PnL: `{m['net_pnl']}`",
        f"- Ending equity: `{m['ending_equity']}`",
        f"- Max drawdown pct: `{m['max_drawdown_pct']}`",
        f"- Profit factor: `{m['profit_factor']}`",
        f"- Trade count: `{m['trade_count']}`",
        f"- Reason codes: `{', '.join(run['reason_codes'])}`",
        "",
    ]


def _candidate_report_markdown(index: int, candidate: dict[str, Any]) -> str:
    m = candidate["metrics"]
    lines = [
        f"# STRAT-DISC1 Candidate {index}: {candidate['display_name']}",
        "",
        "This is a founder production-testing review candidate only. It is not production-approved and live trading is not approved.",
        "",
        "## Strategy Logic",
        "",
        f"- Strategy id: `{candidate['strategy_id']}`",
        f"- Family: `{candidate['strategy_family']}`",
        "- Entry/exit rules: see STRAT-DISC1 curated hypothesis definition in the summary JSON.",
        "- Risk rules: dynamic simulated equity, fees/slippage, no same-candle optimistic fill, forced end-of-window close.",
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
        f"- Out-of-sample net PnL: `{candidate['out_of_sample_metrics']['net_pnl']}`",
        f"- Symbol concentration: `{candidate['symbol_concentration']}`",
        f"- Timeframe concentration: `{candidate['timeframe_concentration']}`",
        f"- Period concentration: `{candidate['period_concentration']}`",
        "",
        "## Why It May Still Fail Live",
        "",
        "- Backtest fills do not model order-book depth, partial fills, funding, latency, rejects, outages, or liquidation.",
        "- The result is not proof of edge and must be reviewed before any paper-runtime inclusion.",
        "- Testnet fills are not strategy truth and were not used as PnL evidence.",
        "",
    ]
    return "\n".join(lines)
