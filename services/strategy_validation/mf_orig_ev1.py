"""MF-ORIG-EV1 original Money Flow reconstruction evidence.

This module is Strategy Validation-only research. It reconstructs a fixed,
source-faithful approximation of the original Money Flow Trading System from
the source summary supplied for MF-ORIG-EV1 and compares it against canonical
SV2.0.2 Money Flow v1.2 evidence rows. It does not mutate production
``services.strategy.money_flow`` rules, create orders, or call exchange
endpoints.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from core.domain.enums import StrategyValidationFillTiming, Timeframe
from core.domain.models import Candle
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    _coerce_utc,
    _json_ready,
    _money,
)
from services.strategy_validation.sor_ev1 import (
    CANONICAL_SV202_TIMESTAMP,
    CANONICAL_SYMBOLS,
    canonical_sv202_batch_report_paths,
)
from services.strategy_validation.sor_ev2 import (
    _assert_canonical_paths,
    _dec,
    _fmt,
    _load_canonical_scenarios,
    _parity_summary,
    _request_from_payload,
)

SOURCE_DOCUMENT_METADATA: dict[str, Any] = {
    "title": "The Money Flow Trading System",
    "author": "Gerald Peters",
    "edition": "September 5, 2019 Edition #2",
    "direct_pdf_available_to_agent": False,
    "source_basis": "prompt_provided_source_truth_summary",
    "limitation": (
        "The PDF file was not present in the repository or common local "
        "Downloads/Documents search paths during MF-ORIG-EV1, so source "
        "extraction is limited to the prompt-supplied source summary."
    ),
}

MF_ORIG_HYPOTHESES: tuple[str, ...] = (
    "mf_orig_1d_stage2_5_20_crossover",
    "mf_orig_1d_stage2_breakout_resistance",
    "mf_orig_stage2_pullback_reclaim",
    "mf_orig_stage_filter_only",
)

PRIMARY_TIMEFRAME_POLICY: dict[str, str] = {
    "1d": "primary_original_money_flow_timeframe",
    "4h": "secondary_context_comparative_run",
    "1h": "exploratory_timing_context_only",
    "15m": "not_source_primary_timeframe",
}

MF_ORIG_EV2_TIMEFRAME_POLICY: dict[str, str] = {
    "1d": "source_primary_original_money_flow_timeframe",
    "4h": "swing_fractal_adaptation",
    "1h": "intraday_fractal_adaptation",
    "15m": "stress_test_short_term_fractal_adaptation_not_source_primary",
}

MF_ORIG_EV2_DISPLAY_LABELS: dict[str, str] = {
    "mf_orig_1d_stage2_5_20_crossover": "mf_orig_stage2_5_20_crossover",
    "mf_orig_1d_stage2_breakout_resistance": "mf_orig_stage2_breakout_resistance",
    "mf_orig_stage2_pullback_reclaim": "mf_orig_stage2_pullback_reclaim",
    "mf_orig_stage_filter_only": "mf_orig_stage_filter_only",
}

SOURCE_RULE_EXTRACTION: list[dict[str, str]] = [
    {
        "section": "Four Stages",
        "source_rule": "Stage 1 accumulation/sideways is whipsaw risk; Stage 2 markup is the primary long regime; Stage 3 distribution warns of topping; Stage 4 markdown is decline.",
        "evidence_translation": "Classify stages deterministically from prior/current candles using close versus SMA20, EMA5/SMA20 crosses, whipsaw/range behavior, RSI/MACD warnings, and prior stage state.",
        "assumption_status": "implemented_with_objective_no_lookahead_proxy",
    },
    {
        "section": "Moving Averages",
        "source_rule": "5 EMA / 20 SMA crossover is the basic buy/sell signal; 10 EMA is trend/alignment context; 20 SMA is the foundation/stage line; 50/200 SMA are respected context.",
        "evidence_translation": "Primary entries require close above SMA20 plus EMA5 crossing above SMA20 or a pullback/reclaim within Stage 2. Full exits use EMA5 cross below SMA20 or price close below SMA20.",
        "assumption_status": "implemented",
    },
    {
        "section": "TSI / MACD",
        "source_rule": "TSI or MACD confirms trend and warns when profitable positions weaken.",
        "evidence_translation": "TSI is deferred; MACD 12/26/9 is used as the accepted substitute. Bullish crossover or improving histogram confirms entries; bearish crossover while profitable trims 25%.",
        "assumption_status": "tsi_deferred_macd_substitute_implemented",
    },
    {
        "section": "RSI / Profit Taking",
        "source_rule": "RSI > 70 is profit-taking/warning context, not necessarily a full exit.",
        "evidence_translation": "RSI above 70 records profit warnings; when paired with bearish MACD while profitable, one 25% trim is applied. RSI high alone does not close the trade.",
        "assumption_status": "implemented",
    },
    {
        "section": "Support / Resistance / Pivots / Stops",
        "source_rule": "Stops belong near logical support/resistance or pivots, not arbitrary fixed percent.",
        "evidence_translation": "Use prior completed-candle support/pivot proxy: recent support low from the prior 10 candles, with optional confirmed pivot low when available before entry.",
        "assumption_status": "implemented_simple_no_lookahead_proxy",
    },
    {
        "section": "Position Sizing",
        "source_rule": "Position sizing is based on defined risk, ideally 1% or less of current account equity per trade.",
        "evidence_translation": "Risk budget is 1% of current realized equity. Size is risk budget divided by entry-stop distance with 100% equity notional cap.",
        "assumption_status": "implemented",
    },
    {
        "section": "Timeframe Adaptation",
        "source_rule": "The book uses daily charts while describing the system as fractal.",
        "evidence_translation": "Treat 1d as primary, 4h as secondary context, 1h as exploratory timing, and exclude 15m from original-source conclusions.",
        "assumption_status": "implemented",
    },
]

GAP_MATRIX: list[dict[str, str]] = [
    {
        "original_pdf_rule": "Stage/20SMA/5EMA trigger hierarchy comes first.",
        "current_v1_2_behavior": "EMA5 > EMA10 > SMA20 stack, RSI sleeve, MACD constructive gate, and pullback/continuation quality are primary.",
        "gap_or_drift": "Current v1.2 is Money Flow-inspired but not source-faithful; it treats RSI/MACD as entry gates rather than secondary warning/confirmation context.",
        "evidence_implication": "MF-ORIG-EV1 must compare a 1d-first stage/crossover system against v1.2, not overwrite v1.2.",
        "source_faithful_reconstruction": "mf_orig_1d_stage2_5_20_crossover plus source-style exits/trims/stops/sizing.",
    },
    {
        "original_pdf_rule": "RSI > 70 is profit-warning/profit-taking context.",
        "current_v1_2_behavior": "RSI sleeve floors/ceilings act as entry eligibility gates and trim thresholds.",
        "gap_or_drift": "RSI has moved from warning context to entry filter.",
        "evidence_implication": "Original hypotheses should not reject entries solely because RSI is below a v1.2 sleeve floor.",
        "source_faithful_reconstruction": "Only block extreme-overbought entries and use RSI > 70 as warning/trim context.",
    },
    {
        "original_pdf_rule": "Full exit is 5 EMA crossing/closing below 20 SMA or price close below 20 SMA.",
        "current_v1_2_behavior": "MA break plus MACD rollover can close/reduce under sleeve-specific logic.",
        "gap_or_drift": "Current exits can be more MACD-sensitive than the source hierarchy.",
        "evidence_implication": "Original replay must separate full exits from profit-warning trims.",
        "source_faithful_reconstruction": "Full exits on EMA5/SMA20 bear cross or price below SMA20; MACD bearish while profitable trims.",
    },
    {
        "original_pdf_rule": "Stops are placed around support/resistance or pivots and risk is sized from stop distance.",
        "current_v1_2_behavior": "Canonical evidence primarily uses position_notional_pct dynamic equity and no source-structure stop model.",
        "gap_or_drift": "Current evidence does not model source-style structure stops or 1% risk sizing.",
        "evidence_implication": "MF-ORIG-EV1 should test risk-budget sizing and prior support/pivot stops explicitly.",
        "source_faithful_reconstruction": "Risk 1% of realized equity, cap notional at current equity, and use prior support low/pivot proxy.",
    },
]

FORBIDDEN_REPORT_PHRASES = (
    "proven",
    "optimal",
    "approved for live",
    "approved for paper",
    "ready for real trading",
    "production-approved",
)


@dataclass(slots=True)
class _OpenOriginalPosition:
    trade_id: str
    hypothesis_id: str
    symbol: str
    timeframe: str
    fill_timing: str
    entry_signal_time: datetime
    entry_time: datetime
    entry_price: Decimal
    stop_price: Decimal
    quantity: Decimal
    remaining_quantity: Decimal
    equity_before: Decimal
    entry_fee: Decimal
    risk_budget: Decimal
    notional: Decimal
    entry_reason_codes: tuple[str, ...]
    stage_at_entry: str
    min_equity_seen: Decimal
    accounting_events: list[dict[str, Any]]
    trimmed: bool = False
    profit_warning_count: int = 0
    trim_count: int = 0
    trim_realized_gross_pnl: Decimal = Decimal("0")
    trim_fees: Decimal = Decimal("0")
    trim_net_pnl: Decimal = Decimal("0")


def build_mf_orig_ev1_report_sync(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        build_mf_orig_ev1_report(
            batch_report_paths,
            generated_at=generated_at,
            max_scenarios=max_scenarios,
            backtest_service=backtest_service,
        )
    )


def build_mf_orig_ev2_report_sync(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        build_mf_orig_ev2_report(
            batch_report_paths,
            generated_at=generated_at,
            max_scenarios=max_scenarios,
            backtest_service=backtest_service,
        )
    )


async def build_mf_orig_ev2_report(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
) -> dict[str, Any]:
    report = await build_mf_orig_ev1_report(
        batch_report_paths,
        generated_at=generated_at,
        max_scenarios=max_scenarios,
        backtest_service=backtest_service,
        included_timeframes=("15m", "1h", "4h", "1d"),
        report_phase="MF-ORIG-EV2",
        report_status="mf_orig_multitimeframe_evidence_ready_for_founder_review",
        supersedes_phase="MF-ORIG-EV1.1",
        include_full_trade_results=True,
        source_timeframe_policy=MF_ORIG_EV2_TIMEFRAME_POLICY,
    )
    replay_rows = report.get("replay_results", [])
    report["ev2_scope"] = {
        "hypotheses": list(MF_ORIG_HYPOTHESES),
        "display_labels": MF_ORIG_EV2_DISPLAY_LABELS,
        "symbols": list(CANONICAL_SYMBOLS),
        "timeframes": ["15m", "1h", "4h", "1d"],
        "fill_assumptions": [
            StrategyValidationFillTiming.NEXT_CANDLE_OPEN.value,
            StrategyValidationFillTiming.NEXT_CANDLE_CLOSE.value,
        ],
        "scenario_count_expected": 4 * len(CANONICAL_SYMBOLS) * 4 * 2,
        "source_primary_timeframe": "1d",
        "fractal_adaptation_timeframes": ["4h", "1h"],
        "stress_test_timeframe": "15m",
    }
    report["timeframe_interpretation"] = MF_ORIG_EV2_TIMEFRAME_POLICY
    report["per_symbol_summary"] = _mf_orig_group_summary(replay_rows, ("symbol",))
    report["per_timeframe_summary"] = _mf_orig_group_summary(replay_rows, ("timeframe",))
    report["per_hypothesis_timeframe_summary"] = _mf_orig_group_summary(
        replay_rows,
        ("hypothesis_id", "timeframe"),
    )
    report["per_hypothesis_symbol_summary"] = _mf_orig_group_summary(
        replay_rows,
        ("hypothesis_id", "symbol"),
    )
    report["baseline_delta_summary"] = {
        "comparison_baseline": "Money Flow v1.2 canonical SV2.0.2 evidence",
        "net_pnl_delta_sum_across_independent_research_scenarios": _fmt(
            sum((_dec(row.get("net_pnl_delta_vs_v1_2")) for row in replay_rows), Decimal("0"))
        ),
        "worst_drawdown_delta_vs_v1_2": _fmt(
            max((_dec(row.get("drawdown_delta_vs_v1_2")) for row in replay_rows), default=Decimal("0"))
        ),
        "aggregate_label": "sum across independent research scenarios",
        "not_one_account_pnl": True,
    }
    report["dashboard_integration_status"] = {
        "historical_replay": "implemented_pending_generated_chart_data",
        "evidence_ui": "implemented_pending_generated_chart_data",
        "date_filter_warning": "display_filtered_not_canonical_pack_regeneration",
        "chart_data_report": "mf_orig_ev2_dashboard_chart_data",
    }
    report["evidence_pack_status"] = {
        "status": "pending_pack_writer",
        "evidence_pack_paths": [],
        "generated_packs_are_review_artifacts": True,
        "large_pack_directories_committed": False,
    }
    report["limitations"] = sorted(
        set(report.get("limitations", []))
        | {
            "mf_orig_ev2_extends_source_reconstruction_across_fractal_timeframes",
            "15m_is_stress_test_not_source_primary",
            "independent_scenarios_are_not_one_combined_account",
        }
    )
    return _json_ready(report)


async def build_mf_orig_ev1_report(
    batch_report_paths: Sequence[str | Path] | None = None,
    *,
    generated_at: datetime | None = None,
    max_scenarios: int | None = None,
    backtest_service: MoneyFlowBacktestService | None = None,
    included_timeframes: Sequence[str] | None = None,
    report_phase: str = "MF-ORIG-EV1.1",
    report_status: str = "original_money_flow_reconstruction_ready_for_founder_review",
    supersedes_phase: str = "MF-ORIG-EV1",
    include_full_trade_results: bool = False,
    source_timeframe_policy: dict[str, str] | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in (batch_report_paths or canonical_sv202_batch_report_paths())]
    _assert_canonical_paths(paths)
    scenarios = _load_canonical_scenarios(paths)
    if max_scenarios is not None:
        scenarios = scenarios[:max_scenarios]
    service = backtest_service or MoneyFlowBacktestService()
    generated_at = generated_at or datetime.now(UTC)
    allowed_timeframes = set(included_timeframes or ("1d", "4h", "1h"))
    timeframe_policy = source_timeframe_policy or PRIMARY_TIMEFRAME_POLICY

    baseline_parity: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    limitations: set[str] = {
        "source_pdf_not_available_to_agent_prompt_summary_used",
        "tsi_deferred_macd_used_as_substitute",
        "support_resistance_modeled_with_simple_prior_support_low_proxy",
        "independent_scenarios_are_not_one_combined_account",
        "dashboard_date_filters_are_display_only_not_canonical_evidence",
    }

    for scenario in scenarios:
        timeframe = str(scenario["timeframe"])
        if timeframe not in allowed_timeframes:
            reason = "not_source_primary_timeframe" if timeframe == "15m" else "timeframe_not_in_mf_orig_policy"
            skipped_rows.append(
                {
                    "scenario_key": scenario["scenario_key"],
                    "symbol": scenario["symbol"],
                    "timeframe": timeframe,
                    "fill_timing": scenario["fill_timing"],
                    "status": "excluded",
                    "reason_codes": [reason],
                }
            )
            continue
        request = _request_from_payload(scenario["request"])
        try:
            baseline_report = await service.run_money_flow_backtest(request)
        except Exception as exc:  # pragma: no cover - integration guard.
            baseline_parity.append(
                {
                    "scenario_key": scenario["scenario_key"],
                    "symbol": scenario["symbol"],
                    "timeframe": timeframe,
                    "fill_timing": scenario["fill_timing"],
                    "status": "baseline_parity_failed",
                    "reason_codes": ["baseline_parity_failed", "baseline_replay_blocked"],
                    "error": str(exc),
                }
            )
            limitations.add("one_or_more_baseline_replays_blocked")
            continue
        component_report = baseline_report.component_reports[0]
        parity = _mf_orig_parity_row(scenario, component_report.metrics)
        baseline_parity.append(parity)
        if parity["status"] == "baseline_parity_failed":
            limitations.add("variant_conclusions_blocked_for_failed_baseline_parity")
            continue
        candles = service._load_candles(request=request, timeframe=component_report.timeframe, end_at=request.end_at)
        snapshots = service._indicator_service._compute_snapshots(candles)
        context = _build_original_context(candles, snapshots)
        baseline_metrics = scenario["metrics"]
        for hypothesis_id in MF_ORIG_HYPOTHESES:
            result = _run_original_hypothesis(
                scenario=scenario,
                hypothesis_id=hypothesis_id,
                candles=candles,
                context=context,
                start_at=_coerce_utc(request.start_at),
                end_at=_coerce_utc(request.end_at),
                fill_timing=request.assumptions.fill_timing,
                fee_bps=request.assumptions.fee_bps,
                slippage_bps=request.assumptions.slippage_bps,
                initial_equity=request.assumptions.initial_capital,
                baseline_metrics=baseline_metrics,
                timeframe_policy=timeframe_policy,
            )
            replay_rows.append(result["row"])
            trade_rows.extend(result["trades"])
            limitations.update(result["limitations"])

    hypothesis_summary = _hypothesis_summary(replay_rows)
    control_pockets = _control_pocket_impact(replay_rows)
    candidate_status = _candidate_status(hypothesis_summary, control_pockets)
    candidate_by_hypothesis = {row["hypothesis_id"]: row for row in candidate_status}
    for row in hypothesis_summary:
        gate = candidate_by_hypothesis.get(row["hypothesis_id"], {})
        row["candidate_gate_status"] = gate.get("status", "insufficient_data")
        row["gate_blockers"] = gate.get("gate_blockers", [])
        row["outcome_label"] = row["candidate_gate_status"]

    report = {
        "phase": report_phase,
        "supersedes_phase": supersedes_phase,
        "generated_at": generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": report_status,
        "hotpatch": {
            "accounting_and_drawdown_hotpatch": "MF-ORIG-EV1.1",
            "pre_hotpatch_pnl_drawdown_conclusions_quarantined": True,
            "regenerated_reports_are_current_for_founder_review": True,
            "fixed_issues": [
                "entry_fee_counted_once",
                "trim_pnl_counted_once",
                "trade_net_pnl_equals_equity_delta",
                "drawdown_method_peak_to_trough",
                "positive_1d_pockets_filter_matches_label",
            ],
        },
        "accounting_convention": {
            "model": "event_ledger_accounting",
            "starting_equity": "10000",
            "entry_fee_counted": "exactly_once_as_entry_fee_event",
            "trim_pnl_counted": "exactly_once_as_trim_close_event",
            "final_close_scope": "remaining_quantity_only",
            "trade_net_pnl": "sum_accounting_event_net_amounts",
            "equity_after_trade": "equity_before_trade_plus_trade_net_pnl",
            "drawdown_method": "peak_to_trough",
            "candidate_gate_drawdown_metric": "mark_to_market_max_drawdown",
        },
        "source_document": SOURCE_DOCUMENT_METADATA,
        "source_rule_extraction": SOURCE_RULE_EXTRACTION,
        "gap_matrix": GAP_MATRIX,
        "primary_timeframe_policy": timeframe_policy,
        "hypothesis_definitions": _hypothesis_definitions(),
        "data_sources": {
            "canonical_baseline": "SV2.0.2 DB-imported Money Flow v1.2 evidence packs",
            "canonical_timestamp": CANONICAL_SV202_TIMESTAMP,
            "supported_symbols": list(CANONICAL_SYMBOLS),
            "batch_report_paths": [str(path) for path in paths],
            "uses_dashboard_date_filters_as_canonical_evidence": False,
            "uses_hyperliquid_testnet_prices": False,
        },
        "baseline_parity_results": baseline_parity,
        "baseline_parity_summary": _parity_summary(baseline_parity),
        "excluded_scenarios": skipped_rows,
        "replay_results": replay_rows,
        "hypothesis_summary": hypothesis_summary,
        "accounting_invariant_summary": _accounting_invariant_summary(trade_rows),
        "trade_samples": trade_rows[:250],
        "control_pocket_results": control_pockets,
        "candidate_status": candidate_status,
        "limitations": sorted(limitations),
        "boundary_flags": {
            "evidence_only": True,
            "changes_production_money_flow_rules": False,
            "production_money_flow_v1_2_unchanged": True,
            "uses_canonical_sv2_0_2_data": True,
            "uses_dashboard_date_filter_recalculation": False,
            "uses_hyperliquid_testnet_prices": False,
            "submits_orders": False,
            "calls_private_signed_or_order_endpoints": False,
            "approves_original_strategy_for_production": False,
            "approves_live_trading": False,
            "adds_paper_runtime": False,
            "adds_sor_fanout_cbbo_or_cross_venue_routing": False,
        },
    }
    if include_full_trade_results:
        report["trade_results"] = trade_rows
    return _json_ready(report)


def write_mf_orig_ev1_outputs(
    report: dict[str, Any],
    markdown_output: str | Path,
    json_output: str | Path,
    spec_output: str | Path,
) -> None:
    markdown_path = Path(markdown_output)
    json_path = Path(json_output)
    spec_path = Path(spec_output)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = mf_orig_ev1_report_to_markdown(report)
    spec = mf_orig_ev1_spec_to_markdown(report)
    _assert_safe_report_language(markdown)
    _assert_safe_report_language(spec)
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    spec_path.write_text(spec, encoding="utf-8")


def write_mf_orig_ev2_outputs(
    report: dict[str, Any],
    markdown_output: str | Path,
    json_output: str | Path,
) -> None:
    markdown_path = Path(markdown_output)
    json_path = Path(json_output)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    compact = _compact_mf_orig_ev2_report(report)
    markdown = mf_orig_ev2_report_to_markdown(compact)
    _assert_safe_report_language(markdown)
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_original_hypothesis(
    *,
    scenario: dict[str, Any],
    hypothesis_id: str,
    candles: Sequence[Candle],
    context: Sequence[dict[str, Any]],
    start_at: datetime,
    end_at: datetime,
    fill_timing: StrategyValidationFillTiming,
    fee_bps: Decimal,
    slippage_bps: Decimal,
    initial_equity: Decimal,
    baseline_metrics: dict[str, Any],
    timeframe_policy: dict[str, str] | None = None,
) -> dict[str, Any]:
    trades: list[dict[str, Any]] = []
    limitations: set[str] = set()
    no_trade_reasons: Counter[str] = Counter()
    invalid_reasons: Counter[str] = Counter()
    equity = initial_equity
    realized_equity_curve: list[Decimal] = [initial_equity]
    mark_to_market_equity_curve: list[Decimal] = [initial_equity]
    open_position: _OpenOriginalPosition | None = None
    trim_events = 0
    stop_exits = 0
    forced_closes = 0
    profit_warnings = 0

    for idx, candle in enumerate(candles):
        close_time = _coerce_utc(candle.close_time)
        if close_time <= start_at or close_time > end_at:
            continue
        row = context[idx]
        if open_position is not None and close_time > open_position.entry_time:
            mtm_equity = _mark_to_market_equity(equity, open_position, candle.low)
            open_position.min_equity_seen = min(open_position.min_equity_seen, mtm_equity)
            mark_to_market_equity_curve.append(mtm_equity)
            exit_reason = _original_exit_reason(row, context[idx - 1] if idx > 0 else None, candle, open_position)
            if exit_reason == "structure_stop_hit":
                exit_price = open_position.stop_price
                trade = _close_original_position(
                    open_position=open_position,
                    current_realized_equity=equity,
                    exit_signal_time=close_time,
                    exit_time=close_time,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    fee_bps=fee_bps,
                    forced_exit=False,
                    stop_fill_model="intrabar_stop_fill_at_stop_price",
                )
                trades.append(trade)
                equity = _dec(trade["equity_after_trade"])
                realized_equity_curve.append(equity)
                mark_to_market_equity_curve.append(equity)
                open_position = None
                stop_exits += 1
                continue
            if exit_reason in {"ema5_cross_below_sma20_exit", "price_close_below_sma20_exit"}:
                fill = _resolve_original_fill(candles, idx, fill_timing)
                if fill is None:
                    limitations.add(f"exit_signal_skipped_no_fill_candle_for_{fill_timing.value}")
                    continue
                exit_price = _apply_slippage(fill["price"], side="sell", slippage_bps=slippage_bps)
                trade = _close_original_position(
                    open_position=open_position,
                    current_realized_equity=equity,
                    exit_signal_time=close_time,
                    exit_time=fill["time"],
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    fee_bps=fee_bps,
                    forced_exit=False,
                    stop_fill_model="not_stop_exit",
                )
                trades.append(trade)
                equity = _dec(trade["equity_after_trade"])
                realized_equity_curve.append(equity)
                mark_to_market_equity_curve.append(equity)
                open_position = None
                continue
            trim_reason = _original_trim_reason(row, context[idx - 1] if idx > 0 else None, candle, open_position)
            if trim_reason and not open_position.trimmed:
                trim = _trim_original_position(
                    open_position=open_position,
                    current_realized_equity=equity,
                    trim_signal_time=close_time,
                    trim_price=_apply_slippage(candle.close, side="sell", slippage_bps=slippage_bps),
                    fee_bps=fee_bps,
                    reason=trim_reason,
                )
                equity = _dec(trim["realized_equity_after_event"])
                realized_equity_curve.append(equity)
                mark_to_market_equity_curve.append(
                    _mark_to_market_equity(equity, open_position, _dec(trim["price"]))
                )
                trim_events += 1
            if _profitable(open_position, candle.close) and row.get("rsi14") is not None and row["rsi14"] > Decimal("70"):
                open_position.profit_warning_count += 1
                profit_warnings += 1
            continue

        if open_position is not None:
            continue
        signal = _entry_signal(hypothesis_id, idx, candle, candles, context)
        if not signal["entry_allowed"]:
            for reason in signal["reason_codes"]:
                if reason.startswith("missing_") or reason == "insufficient_history":
                    invalid_reasons[reason] += 1
                else:
                    no_trade_reasons[reason] += 1
            continue
        fill = _resolve_original_fill(candles, idx, fill_timing)
        if fill is None:
            limitations.add(f"open_signal_skipped_no_fill_candle_for_{fill_timing.value}")
            continue
        stop_price = _structure_stop_price(candles, idx)
        if stop_price is None:
            no_trade_reasons["no_trade_structure_stop_unavailable"] += 1
            continue
        entry_price = _apply_slippage(fill["price"], side="buy", slippage_bps=slippage_bps)
        open_position = _open_original_position(
            scenario=scenario,
            hypothesis_id=hypothesis_id,
            fill_timing=fill_timing,
            signal_time=close_time,
            fill_time=fill["time"],
            entry_price=entry_price,
            stop_price=stop_price,
            equity=equity,
            fee_bps=fee_bps,
            reason_codes=tuple(signal["reason_codes"]),
            stage=str(signal.get("stage") or row.get("stage") or "unknown"),
        )
        if open_position is None:
            no_trade_reasons["no_trade_invalid_stop_distance"] += 1
            continue
        equity = _dec(open_position.accounting_events[-1]["realized_equity_after_event"])
        realized_equity_curve.append(equity)
        mark_to_market_equity_curve.append(equity)

    if open_position is not None:
        last_index = _last_candle_index_in_window(candles, start_at=start_at, end_at=end_at)
        if last_index is not None:
            last_candle = candles[last_index]
            open_position.min_equity_seen = min(
                open_position.min_equity_seen,
                _mark_to_market_equity(equity, open_position, last_candle.low),
            )
            mark_to_market_equity_curve.append(_mark_to_market_equity(equity, open_position, last_candle.low))
            trade = _close_original_position(
                open_position=open_position,
                current_realized_equity=equity,
                exit_signal_time=_coerce_utc(last_candle.close_time),
                exit_time=_coerce_utc(last_candle.close_time),
                exit_price=last_candle.close,
                exit_reason="end_of_window_forced_close",
                fee_bps=fee_bps,
                forced_exit=True,
                stop_fill_model="not_stop_exit",
            )
            trades.append(trade)
            equity = _dec(trade["equity_after_trade"])
            realized_equity_curve.append(equity)
            mark_to_market_equity_curve.append(equity)
            forced_closes += 1
            limitations.add("open_positions_are_force_closed_at_dataset_end")

    metrics = _original_metrics(
        trades,
        initial_equity=initial_equity,
        ending_equity=equity,
        realized_equity_curve=realized_equity_curve,
        mark_to_market_equity_curve=mark_to_market_equity_curve,
    )
    baseline_net_pnl = _dec(baseline_metrics.get("net_account_pnl"))
    baseline_drawdown = _dec(
        baseline_metrics.get("mark_to_market_max_drawdown") or baseline_metrics.get("max_drawdown")
    )
    row = {
        "scenario_key": scenario["scenario_key"],
        "hypothesis_id": hypothesis_id,
        "display_hypothesis_id": MF_ORIG_EV2_DISPLAY_LABELS.get(hypothesis_id, hypothesis_id),
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "timeframe_role": (timeframe_policy or PRIMARY_TIMEFRAME_POLICY).get(str(scenario["timeframe"]), "unknown"),
        "fill_timing": fill_timing.value,
        "methodology": "true_forward_replay",
        "source_strategy": "original_money_flow_reconstruction",
        "current_baseline": "money_flow_v1_2",
        "initial_equity": _fmt(initial_equity),
        "ending_equity": _fmt(metrics["ending_equity"]),
        "net_pnl": _fmt(metrics["net_pnl"]),
        "max_drawdown": _fmt(metrics["max_drawdown"]),
        "drawdown_method": metrics["drawdown_method"],
        "realized_max_drawdown": _fmt(metrics["realized_max_drawdown"]),
        "realized_max_drawdown_pct": _fmt(metrics["realized_max_drawdown_pct"]),
        "mark_to_market_max_drawdown": _fmt(metrics["mark_to_market_max_drawdown"]),
        "mark_to_market_max_drawdown_pct": _fmt(metrics["mark_to_market_max_drawdown_pct"]),
        "max_equity": _fmt(metrics["max_equity"]),
        "min_equity": _fmt(metrics["min_equity"]),
        "largest_loss": _fmt(metrics["largest_loss"]),
        "largest_win": _fmt(metrics["largest_win"]),
        "win_rate": _fmt(metrics["win_rate"]),
        "profit_factor": _fmt(metrics["profit_factor"]),
        "trade_count": metrics["trade_count"],
        "stop_exits": stop_exits,
        "trim_events": trim_events,
        "profit_warnings": profit_warnings,
        "forced_close_count": forced_closes,
        "baseline_net_pnl": _fmt(baseline_net_pnl),
        "baseline_max_drawdown": _fmt(baseline_drawdown),
        "net_pnl_delta_vs_v1_2": _fmt(Decimal(str(metrics["net_pnl"])) - baseline_net_pnl),
        "drawdown_delta_vs_v1_2": _fmt(Decimal(str(metrics["max_drawdown"])) - baseline_drawdown),
        "no_trade_reason_counts": dict(sorted(no_trade_reasons.items())),
        "invalid_reason_counts": dict(sorted(invalid_reasons.items())),
        "production_approved": False,
    }
    return {"row": row, "trades": trades, "limitations": limitations}


def _build_original_context(candles: Sequence[Candle], snapshots: Sequence[Any]) -> list[dict[str, Any]]:
    closes = [candle.close for candle in candles]
    sma50 = _sma_decimal(closes, 50)
    sma200 = _sma_decimal(closes, 200)
    atr14 = _atr_decimal(candles, 14)
    rows: list[dict[str, Any]] = []
    prior_stage = "stage_unknown_insufficient_history"
    for idx, candle in enumerate(candles):
        snapshot = snapshots[idx] if idx < len(snapshots) else None
        prev = rows[idx - 1] if idx > 0 else None
        missing = _missing_original_indicator_reasons(snapshot)
        row = {
            "ema5": getattr(snapshot, "ema_5", None) if snapshot is not None else None,
            "ema10": getattr(snapshot, "ema_10", None) if snapshot is not None else None,
            "sma20": getattr(snapshot, "sma_20", None) if snapshot is not None else None,
            "sma50": sma50[idx],
            "sma200": sma200[idx],
            "rsi14": getattr(snapshot, "rsi_14", None) if snapshot is not None else None,
            "macd": getattr(snapshot, "macd", None) if snapshot is not None else None,
            "macd_signal": getattr(snapshot, "macd_signal", None) if snapshot is not None else None,
            "macd_histogram": getattr(snapshot, "macd_histogram", None) if snapshot is not None else None,
            "atr14": atr14.get(idx),
            "missing_reasons": missing,
        }
        row["stage"] = _classify_stage(candles, rows, idx, row, prev, prior_stage)
        prior_stage = str(row["stage"])
        rows.append(row)
    return rows


def _entry_signal(
    hypothesis_id: str,
    idx: int,
    candle: Candle,
    candles: Sequence[Candle],
    context: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    row = context[idx]
    prev = context[idx - 1] if idx > 0 else None
    missing = tuple(row.get("missing_reasons") or ())
    if missing:
        return {"entry_allowed": False, "reason_codes": list(missing)}
    if row.get("sma50") is None:
        return {"entry_allowed": False, "reason_codes": ["insufficient_history", "missing_sma50"]}
    if hypothesis_id in {
        "mf_orig_1d_stage2_5_20_crossover",
        "mf_orig_1d_stage2_breakout_resistance",
        "mf_orig_stage2_pullback_reclaim",
    } and str(row.get("stage")) != "stage_2_markup":
        return {"entry_allowed": False, "reason_codes": ["blocked_not_stage_2_markup"], "stage": row.get("stage")}
    if Decimal(str(row["rsi14"])) >= Decimal("80"):
        return {"entry_allowed": False, "reason_codes": ["blocked_rsi_extreme_overbought"], "stage": row.get("stage")}
    macd_ok = _macd_bullish_or_improving(row, prev)
    if hypothesis_id == "mf_orig_1d_stage2_5_20_crossover":
        if candle.close > row["sma20"] and _crossed_above(row, prev, "ema5", "sma20") and macd_ok:
            return {
                "entry_allowed": True,
                "reason_codes": ["stage2_price_above_sma20", "ema5_cross_above_sma20", "macd_confirmation_or_improving"],
                "stage": row.get("stage"),
            }
        return {"entry_allowed": False, "reason_codes": ["no_stage2_5_20_crossover_entry"], "stage": row.get("stage")}
    if hypothesis_id == "mf_orig_1d_stage2_breakout_resistance":
        resistance = _prior_high(candles, idx, 20)
        if resistance is not None and candle.close > resistance and candle.close > row["sma20"] and row["ema5"] >= row["sma20"] and macd_ok:
            return {
                "entry_allowed": True,
                "reason_codes": ["stage2_resistance_breakout", "price_above_sma20", "ema5_above_sma20", "macd_confirmation_or_improving"],
                "stage": row.get("stage"),
            }
        return {"entry_allowed": False, "reason_codes": ["no_stage2_resistance_breakout_entry"], "stage": row.get("stage")}
    if hypothesis_id == "mf_orig_stage2_pullback_reclaim":
        near_support = candle.low <= min(row["ema10"], row["sma20"]) * Decimal("1.015")
        reclaim = candle.close >= row["ema5"] or candle.close >= row["ema10"]
        macd_not_strong_bear = row["macd_histogram"] >= Decimal("-0.025") or _macd_hist_improving(row, prev)
        if near_support and reclaim and macd_not_strong_bear:
            return {
                "entry_allowed": True,
                "reason_codes": ["stage2_pullback_near_ema10_or_sma20", "price_reclaimed_ema5_or_ema10", "macd_not_strong_bearish"],
                "stage": row.get("stage"),
            }
        return {"entry_allowed": False, "reason_codes": ["no_stage2_pullback_reclaim_entry"], "stage": row.get("stage")}
    if hypothesis_id == "mf_orig_stage_filter_only":
        current_like = row["ema5"] > row["ema10"] > row["sma20"] and row["macd"] > row["macd_signal"] and Decimal("46") <= row["rsi14"] <= Decimal("72")
        if current_like and str(row.get("stage")) == "stage_2_markup":
            return {
                "entry_allowed": True,
                "reason_codes": ["current_v1_2_like_entry_with_original_stage2_filter"],
                "stage": row.get("stage"),
            }
        return {"entry_allowed": False, "reason_codes": ["current_v1_2_like_entry_blocked_by_stage_filter"], "stage": row.get("stage")}
    return {"entry_allowed": False, "reason_codes": ["unknown_hypothesis"]}


def _classify_stage(
    candles: Sequence[Candle],
    prior_rows: Sequence[dict[str, Any]],
    idx: int,
    row: dict[str, Any],
    prev: dict[str, Any] | None,
    prior_stage: str,
) -> str:
    if row.get("ema5") is None or row.get("ema10") is None or row.get("sma20") is None or row.get("rsi14") is None:
        return "stage_unknown_insufficient_history"
    candle = candles[idx]
    if candle.close < row["sma20"] or _crossed_below(row, prev, "ema5", "sma20"):
        return "stage_4_markdown"
    whipsaws = _spread_cross_count(prior_rows, "ema5", "sma20", 20)
    low_progress = _low_directional_progress(candles, idx, 20)
    if (candle.close > row["sma20"] and _crossed_above(row, prev, "ema5", "sma20")) or (
        prior_stage == "stage_2_markup" and row["ema5"] > row["sma20"] and candle.close > row["sma20"]
    ):
        if row["rsi14"] > Decimal("72") and not _macd_bullish_or_improving(row, prev):
            return "stage_3_distribution"
        return "stage_2_markup"
    if prior_stage == "stage_2_markup" and (row["rsi14"] > Decimal("70") or not _macd_bullish_or_improving(row, prev)):
        return "stage_3_distribution"
    if whipsaws >= 3 or low_progress:
        return "stage_1_accumulation_sideways"
    return "stage_1_accumulation_sideways"


def _original_exit_reason(
    row: dict[str, Any],
    prev: dict[str, Any] | None,
    candle: Candle,
    open_position: _OpenOriginalPosition,
) -> str | None:
    if candle.low <= open_position.stop_price:
        return "structure_stop_hit"
    if row.get("ema5") is None or row.get("sma20") is None:
        return None
    if _crossed_below(row, prev, "ema5", "sma20"):
        return "ema5_cross_below_sma20_exit"
    if candle.close < row["sma20"]:
        return "price_close_below_sma20_exit"
    return None


def _original_trim_reason(
    row: dict[str, Any],
    prev: dict[str, Any] | None,
    candle: Candle,
    open_position: _OpenOriginalPosition,
) -> str | None:
    if not _profitable(open_position, candle.close):
        return None
    if row.get("rsi14") is None or row.get("ema5") is None or row.get("sma20") is None:
        return None
    if row["rsi14"] > Decimal("70") and row["ema5"] > row["sma20"] and _macd_bearish_cross(row, prev):
        return "rsi_profit_warning_macd_bearish_trim_25pct"
    return None


def _open_original_position(
    *,
    scenario: dict[str, Any],
    hypothesis_id: str,
    fill_timing: StrategyValidationFillTiming,
    signal_time: datetime,
    fill_time: datetime,
    entry_price: Decimal,
    stop_price: Decimal,
    equity: Decimal,
    fee_bps: Decimal,
    reason_codes: tuple[str, ...],
    stage: str,
) -> _OpenOriginalPosition | None:
    stop_distance = entry_price - stop_price
    if stop_distance <= 0 or not stop_distance.is_finite():
        return None
    risk_budget = equity * Decimal("0.01")
    quantity = risk_budget / stop_distance
    notional = quantity * entry_price
    max_notional = equity
    if notional > max_notional:
        quantity = max_notional / entry_price
        notional = max_notional
    if quantity <= 0 or notional <= 0:
        return None
    entry_fee = _money(notional * fee_bps / Decimal("10000"))
    entry_equity_after = _money(equity - entry_fee)
    trade_id = f"mf-orig-{hypothesis_id}-{scenario['symbol']}-{scenario['timeframe']}-{fill_timing.value}-{len(reason_codes)}-{int(fill_time.timestamp())}"
    accounting_events = [
        _accounting_event(
            event_type="entry_fee",
            timestamp=fill_time,
            quantity=quantity,
            price=entry_price,
            gross_pnl=Decimal("0"),
            fee=entry_fee,
            net_amount=-entry_fee,
            remaining_quantity_after_event=quantity,
            realized_equity_after_event=entry_equity_after,
            mark_to_market_equity_after_event=entry_equity_after,
        )
    ]
    return _OpenOriginalPosition(
        trade_id=trade_id,
        hypothesis_id=hypothesis_id,
        symbol=scenario["symbol"],
        timeframe=scenario["timeframe"],
        fill_timing=fill_timing.value,
        entry_signal_time=signal_time,
        entry_time=fill_time,
        entry_price=_money(entry_price),
        stop_price=_money(stop_price),
        quantity=quantity,
        remaining_quantity=quantity,
        equity_before=equity,
        entry_fee=entry_fee,
        risk_budget=_money(risk_budget),
        notional=_money(notional),
        entry_reason_codes=reason_codes,
        stage_at_entry=stage,
        min_equity_seen=entry_equity_after,
        accounting_events=accounting_events,
    )


def _close_original_position(
    *,
    open_position: _OpenOriginalPosition,
    current_realized_equity: Decimal,
    exit_signal_time: datetime,
    exit_time: datetime,
    exit_price: Decimal,
    exit_reason: str,
    fee_bps: Decimal,
    forced_exit: bool,
    stop_fill_model: str,
) -> dict[str, Any]:
    qty = open_position.remaining_quantity
    gross_pnl = (exit_price - open_position.entry_price) * qty
    exit_notional = exit_price * qty
    exit_fee = _money(exit_notional * fee_bps / Decimal("10000"))
    final_close_net_pnl = gross_pnl - exit_fee
    equity_after = _money(current_realized_equity + final_close_net_pnl)
    event_type = "forced_close" if forced_exit else "stop_close" if exit_reason == "structure_stop_hit" else "final_close"
    final_event = _accounting_event(
        event_type=event_type,
        timestamp=exit_time,
        quantity=qty,
        price=exit_price,
        gross_pnl=gross_pnl,
        fee=exit_fee,
        net_amount=final_close_net_pnl,
        remaining_quantity_after_event=Decimal("0"),
        realized_equity_after_event=equity_after,
        mark_to_market_equity_after_event=equity_after,
    )
    accounting_events = [*open_position.accounting_events, final_event]
    total_fees = sum((_dec(event["fee"]) for event in accounting_events), Decimal("0"))
    net_pnl = sum((_dec(event["net_amount"]) for event in accounting_events), Decimal("0"))
    total_gross_pnl = sum((_dec(event["gross_pnl"]) for event in accounting_events), Decimal("0"))
    min_equity_seen = min(
        [open_position.min_equity_seen, equity_after]
        + [_dec(event["mark_to_market_equity_after_event"]) for event in accounting_events]
    )
    return {
        "trade_id": open_position.trade_id,
        "hypothesis_id": open_position.hypothesis_id,
        "symbol": open_position.symbol,
        "timeframe": open_position.timeframe,
        "fill_timing": open_position.fill_timing,
        "entry_signal_time": open_position.entry_signal_time.isoformat(),
        "entry_time": open_position.entry_time.isoformat(),
        "exit_signal_time": exit_signal_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "entry_price": _fmt(open_position.entry_price),
        "exit_price": _fmt(exit_price),
        "stop_price": _fmt(open_position.stop_price),
        "quantity": _fmt(open_position.quantity),
        "notional": _fmt(open_position.notional),
        "risk_budget": _fmt(open_position.risk_budget),
        "entry_reason_codes": list(open_position.entry_reason_codes),
        "exit_reason": exit_reason,
        "entry_stage": open_position.stage_at_entry,
        "gross_pnl": _fmt(total_gross_pnl),
        "fees": _fmt(total_fees),
        "net_pnl": _fmt(net_pnl),
        "equity_before_trade": _fmt(open_position.equity_before),
        "equity_after_trade": _fmt(equity_after),
        "equity_before": _fmt(open_position.equity_before),
        "equity_after": _fmt(equity_after),
        "entry_fee": _fmt(open_position.entry_fee),
        "trim_count": open_position.trim_count,
        "trim_realized_gross_pnl": _fmt(open_position.trim_realized_gross_pnl),
        "trim_fees": _fmt(open_position.trim_fees),
        "trim_net_pnl": _fmt(open_position.trim_net_pnl),
        "final_close_gross_pnl": _fmt(gross_pnl),
        "final_close_fee": _fmt(exit_fee),
        "final_close_net_pnl": _fmt(final_close_net_pnl),
        "total_fees": _fmt(total_fees),
        "remaining_quantity_final": _fmt(Decimal("0")),
        "accounting_events": accounting_events,
        "min_equity_seen": _fmt(min_equity_seen),
        "profit_warning_count": open_position.profit_warning_count,
        "forced_exit": forced_exit,
        "entry_fill_model": open_position.fill_timing,
        "exit_fill_model": "dataset_end_close" if forced_exit else open_position.fill_timing,
        "stop_fill_model": stop_fill_model,
        "historical_replay_not_live": True,
    }


def _trim_original_position(
    *,
    open_position: _OpenOriginalPosition,
    current_realized_equity: Decimal,
    trim_signal_time: datetime,
    trim_price: Decimal,
    fee_bps: Decimal,
    reason: str,
) -> dict[str, Any]:
    trim_qty = open_position.remaining_quantity * Decimal("0.25")
    gross_pnl = (trim_price - open_position.entry_price) * trim_qty
    fee = _money(trim_price * trim_qty * fee_bps / Decimal("10000"))
    net_pnl = gross_pnl - fee
    open_position.remaining_quantity -= trim_qty
    realized_equity_after_event = _money(current_realized_equity + net_pnl)
    mark_to_market_after_event = _money(
        realized_equity_after_event
        + ((trim_price - open_position.entry_price) * open_position.remaining_quantity)
    )
    event = _accounting_event(
        event_type="trim_close",
        timestamp=trim_signal_time,
        quantity=trim_qty,
        price=trim_price,
        gross_pnl=gross_pnl,
        fee=fee,
        net_amount=net_pnl,
        remaining_quantity_after_event=open_position.remaining_quantity,
        realized_equity_after_event=realized_equity_after_event,
        mark_to_market_equity_after_event=mark_to_market_after_event,
    )
    open_position.accounting_events.append(event)
    open_position.trimmed = True
    open_position.trim_count += 1
    open_position.trim_realized_gross_pnl += gross_pnl
    open_position.trim_fees += fee
    open_position.trim_net_pnl += net_pnl
    open_position.min_equity_seen = min(open_position.min_equity_seen, realized_equity_after_event, mark_to_market_after_event)
    return {
        "event_type": "trim_close",
        "trim_time": trim_signal_time.isoformat(),
        "timestamp": trim_signal_time.isoformat(),
        "price": _fmt(trim_price),
        "trim_price": _fmt(trim_price),
        "quantity": _fmt(trim_qty),
        "trim_quantity": _fmt(trim_qty),
        "reason": reason,
        "gross_pnl": _fmt(gross_pnl),
        "fee": _fmt(fee),
        "net_amount": _fmt(net_pnl),
        "net_pnl": _fmt(net_pnl),
        "remaining_quantity_after_event": _fmt(open_position.remaining_quantity),
        "realized_equity_after_event": _fmt(realized_equity_after_event),
        "mark_to_market_equity_after_event": _fmt(mark_to_market_after_event),
    }


def _accounting_event(
    *,
    event_type: str,
    timestamp: datetime,
    quantity: Decimal,
    price: Decimal,
    gross_pnl: Decimal,
    fee: Decimal,
    net_amount: Decimal,
    remaining_quantity_after_event: Decimal,
    realized_equity_after_event: Decimal,
    mark_to_market_equity_after_event: Decimal,
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
        "quantity": _fmt(quantity),
        "price": _fmt(price),
        "gross_pnl": _fmt(gross_pnl),
        "fee": _fmt(fee),
        "net_amount": _fmt(net_amount),
        "remaining_quantity_after_event": _fmt(remaining_quantity_after_event),
        "realized_equity_after_event": _fmt(realized_equity_after_event),
        "mark_to_market_equity_after_event": _fmt(mark_to_market_equity_after_event),
    }


def _original_metrics(
    trades: Sequence[dict[str, Any]],
    *,
    initial_equity: Decimal,
    ending_equity: Decimal,
    realized_equity_curve: Sequence[Decimal],
    mark_to_market_equity_curve: Sequence[Decimal],
) -> dict[str, Any]:
    net_pnls = [Decimal(str(trade["net_pnl"])) for trade in trades]
    wins = [pnl for pnl in net_pnls if pnl > 0]
    losses = [pnl for pnl in net_pnls if pnl < 0]
    profit_factor = (sum(wins, Decimal("0")) / abs(sum(losses, Decimal("0")))) if losses else Decimal("0")
    win_rate = Decimal(len(wins)) / Decimal(len(net_pnls)) if net_pnls else Decimal("0")
    realized_dd = _drawdown_stats(realized_equity_curve)
    mtm_dd = _drawdown_stats(mark_to_market_equity_curve)
    return {
        "ending_equity": _money(ending_equity),
        "net_pnl": _money(ending_equity - initial_equity),
        "max_drawdown": mtm_dd["max_drawdown"],
        "realized_max_drawdown": realized_dd["max_drawdown"],
        "realized_max_drawdown_pct": realized_dd["max_drawdown_pct"],
        "mark_to_market_max_drawdown": mtm_dd["max_drawdown"],
        "mark_to_market_max_drawdown_pct": mtm_dd["max_drawdown_pct"],
        "max_equity": mtm_dd["max_equity"],
        "min_equity": mtm_dd["min_equity"],
        "drawdown_method": "peak_to_trough",
        "largest_loss": _money(min(net_pnls, default=Decimal("0"))),
        "largest_win": _money(max(net_pnls, default=Decimal("0"))),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "trade_count": len(trades),
    }


def _drawdown_stats(curve: Sequence[Decimal]) -> dict[str, Decimal]:
    if not curve:
        return {
            "max_drawdown": Decimal("0"),
            "max_drawdown_pct": Decimal("0"),
            "max_equity": Decimal("0"),
            "min_equity": Decimal("0"),
        }
    running_peak = curve[0]
    max_drawdown = Decimal("0")
    max_drawdown_pct = Decimal("0")
    max_equity = curve[0]
    min_equity = curve[0]
    for value in curve:
        max_equity = max(max_equity, value)
        min_equity = min(min_equity, value)
        if value > running_peak:
            running_peak = value
        drawdown = running_peak - value
        drawdown_pct = Decimal("0") if running_peak == 0 else drawdown / running_peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_pct = drawdown_pct
    return {
        "max_drawdown": _money(max_drawdown),
        "max_drawdown_pct": max_drawdown_pct,
        "max_equity": _money(max_equity),
        "min_equity": _money(min_equity),
    }


def _hypothesis_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["hypothesis_id"]].append(row)
    output: list[dict[str, Any]] = []
    for hypothesis_id, selected in sorted(grouped.items()):
        pnl_delta = sum((_dec(row["net_pnl_delta_vs_v1_2"]) for row in selected), Decimal("0"))
        worst_dd_delta = max((_dec(row["drawdown_delta_vs_v1_2"]) for row in selected), default=Decimal("0"))
        one_day = [row for row in selected if row["timeframe"] == "1d"]
        output.append(
            {
                "hypothesis_id": hypothesis_id,
                "methodology": "true_forward_replay",
                "scenario_count": len(selected),
                "one_day_scenario_count": len(one_day),
                "net_pnl_delta_sum_across_independent_scenarios": _fmt(pnl_delta),
                "worst_drawdown_delta_vs_v1_2": _fmt(worst_dd_delta),
                "trade_count_sum": sum(int(row["trade_count"]) for row in selected),
                "stop_exit_count_sum": sum(int(row["stop_exits"]) for row in selected),
                "trim_event_count_sum": sum(int(row["trim_events"]) for row in selected),
                "forced_close_count_sum": sum(int(row["forced_close_count"]) for row in selected),
                "one_day_net_pnl_sum": _fmt(sum((_dec(row["net_pnl"]) for row in one_day), Decimal("0"))),
                "performance_label": _outcome_label(selected),
                "outcome_label": _outcome_label(selected),
                "production_approved": False,
            }
        )
    return output


def _accounting_invariant_summary(trades: Sequence[dict[str, Any]]) -> dict[str, Any]:
    tolerance = Decimal("0.0000001")
    equity_delta_violations = 0
    fee_sum_violations = 0
    remaining_quantity_violations = 0
    entry_fee_event_violations = 0
    for trade in trades:
        equity_delta = _dec(trade["equity_after_trade"]) - _dec(trade["equity_before_trade"])
        if abs(equity_delta - _dec(trade["net_pnl"])) > tolerance:
            equity_delta_violations += 1
        event_fee_sum = sum((_dec(event["fee"]) for event in trade["accounting_events"]), Decimal("0"))
        if event_fee_sum != _dec(trade["total_fees"]):
            fee_sum_violations += 1
        if _dec(trade["remaining_quantity_final"]) != Decimal("0"):
            remaining_quantity_violations += 1
        if sum(1 for event in trade["accounting_events"] if event["event_type"] == "entry_fee") != 1:
            entry_fee_event_violations += 1
    return {
        "trade_count_checked": len(trades),
        "decimal_tolerance": _fmt(tolerance),
        "equity_delta_violations": equity_delta_violations,
        "fee_sum_violations": fee_sum_violations,
        "remaining_quantity_violations": remaining_quantity_violations,
        "entry_fee_event_violations": entry_fee_event_violations,
        "status": "passed"
        if not (
            equity_delta_violations
            or fee_sum_violations
            or remaining_quantity_violations
            or entry_fee_event_violations
        )
        else "failed",
    }


def _control_pocket_impact(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    pockets = [
        ("ETH", "1h", "ETH 1h current baseline", "all", True),
        ("*", "1d", "positive 1d pockets", "baseline_positive", True),
        ("*", "1d", "all_1d_pockets", "all", False),
    ]
    output: list[dict[str, Any]] = []
    for hypothesis_id in MF_ORIG_HYPOTHESES:
        selected = [row for row in rows if row["hypothesis_id"] == hypothesis_id]
        for symbol, timeframe, label, filter_mode, gating_control in pockets:
            pocket_rows = [
                row
                for row in selected
                if (symbol == "*" or row["symbol"] == symbol) and row["timeframe"] == timeframe
            ]
            if filter_mode == "baseline_positive":
                pocket_rows = [row for row in pocket_rows if _dec(row.get("baseline_net_pnl")) > 0]
            if not pocket_rows:
                output.append(
                    {
                        "hypothesis_id": hypothesis_id,
                        "control_pocket": label,
                        "status": "insufficient_data",
                        "filter": filter_mode,
                        "gating_control": gating_control,
                        "notes": "No matching source-policy scenario was replayed.",
                    }
                )
                continue
            pnl_delta = sum((_dec(row["net_pnl_delta_vs_v1_2"]) for row in pocket_rows), Decimal("0"))
            dd_delta = max((_dec(row["drawdown_delta_vs_v1_2"]) for row in pocket_rows), default=Decimal("0"))
            status = "preserved"
            if pnl_delta > 0 and dd_delta <= 0:
                status = "improved"
            elif pnl_delta < 0 or dd_delta > Decimal("0"):
                status = "damaged" if pnl_delta < Decimal("-100") or dd_delta > Decimal("100") else "return_reduced"
            output.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "control_pocket": label,
                    "status": status,
                    "filter": filter_mode,
                    "gating_control": gating_control,
                    "net_pnl_delta_sum": _fmt(pnl_delta),
                    "worst_drawdown_delta": _fmt(dd_delta),
                    "trade_count": sum(int(row["trade_count"]) for row in pocket_rows),
                }
            )
    return output


def _candidate_status(summary_rows: Sequence[dict[str, Any]], control_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    damaged = {
        row["hypothesis_id"]
        for row in control_rows
        if row.get("gating_control") is not False and row.get("status") in {"damaged", "return_reduced"}
    }
    output: list[dict[str, Any]] = []
    for row in summary_rows:
        blockers: list[str] = []
        if row["hypothesis_id"] in damaged:
            blockers.append("control_pocket_not_preserved")
        if int(row["trade_count_sum"]) < 3:
            blockers.append("insufficient_sample")
        if _dec(row["net_pnl_delta_sum_across_independent_scenarios"]) <= 0:
            blockers.append("did_not_improve_net_pnl_vs_v1_2")
        if _dec(row["worst_drawdown_delta_vs_v1_2"]) > 0:
            blockers.append("drawdown_worse_than_v1_2")
        status = "candidate_for_more_evidence" if not blockers else _fallback_outcome_from_blockers(blockers)
        output.append(
            {
                "hypothesis_id": row["hypothesis_id"],
                "status": status,
                "methodology": "true_forward_replay",
                "production_approved": False,
                "gate_blockers": blockers,
            }
        )
    return output


def _mf_orig_parity_row(scenario: dict[str, Any], metrics: Any) -> dict[str, Any]:
    canonical = scenario["metrics"]
    trade_delta = metrics.number_of_trades - int(_dec(canonical.get("number_of_trades")))
    equity_delta = metrics.ending_equity - _dec(canonical.get("ending_equity"))
    pnl_delta = metrics.net_account_pnl - _dec(canonical.get("net_account_pnl"))
    dd_delta = (metrics.mark_to_market_max_drawdown or metrics.max_drawdown) - _dec(
        canonical.get("mark_to_market_max_drawdown") or canonical.get("max_drawdown")
    )
    status = "baseline_parity_passed"
    if abs(equity_delta) > Decimal("0.05") or trade_delta != 0:
        status = "baseline_parity_failed"
    elif abs(pnl_delta) > Decimal("0.01") or abs(dd_delta) > Decimal("0.01"):
        status = "baseline_parity_warning"
    return {
        "scenario_key": scenario["scenario_key"],
        "symbol": scenario["symbol"],
        "timeframe": scenario["timeframe"],
        "fill_timing": scenario["fill_timing"],
        "status": status,
        "reason_codes": [status],
        "trade_count_delta": trade_delta,
        "ending_equity_delta": _fmt(equity_delta),
        "net_pnl_delta": _fmt(pnl_delta),
        "max_drawdown_delta": _fmt(dd_delta),
    }


def _resolve_original_fill(
    candles: Sequence[Candle],
    signal_index: int,
    fill_timing: StrategyValidationFillTiming,
) -> dict[str, Any] | None:
    if fill_timing == StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY:
        return None
    fill_index = signal_index + 1
    if fill_index >= len(candles):
        return None
    candle = candles[fill_index]
    if fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_OPEN:
        return {"price": candle.open, "time": _coerce_utc(candle.open_time)}
    if fill_timing == StrategyValidationFillTiming.NEXT_CANDLE_CLOSE:
        return {"price": candle.close, "time": _coerce_utc(candle.close_time)}
    return None


def _structure_stop_price(candles: Sequence[Candle], signal_index: int, lookback: int = 10) -> Decimal | None:
    prior = candles[max(0, signal_index - lookback):signal_index]
    if len(prior) < lookback:
        return None
    recent_support = min(candle.low for candle in prior)
    pivot = _confirmed_prior_pivot_low(candles, signal_index, left=2, right=2)
    if pivot is None:
        return recent_support
    return min(recent_support, pivot)


def _confirmed_prior_pivot_low(candles: Sequence[Candle], signal_index: int, *, left: int, right: int) -> Decimal | None:
    latest_confirmable = signal_index - right
    if latest_confirmable <= left:
        return None
    pivots: list[Decimal] = []
    for idx in range(left, latest_confirmable + 1):
        low = candles[idx].low
        prior = [candles[j].low for j in range(idx - left, idx)]
        after = [candles[j].low for j in range(idx + 1, idx + right + 1)]
        if all(low < value for value in prior + after):
            pivots.append(low)
    return pivots[-1] if pivots else None


def _last_candle_index_in_window(candles: Sequence[Candle], *, start_at: datetime, end_at: datetime) -> int | None:
    selected = [
        idx
        for idx, candle in enumerate(candles)
        if start_at < _coerce_utc(candle.close_time) <= end_at
    ]
    return selected[-1] if selected else None


def _missing_original_indicator_reasons(snapshot: Any) -> tuple[str, ...]:
    if snapshot is None:
        return ("missing_indicator_field", "invalid_indicator_snapshot")
    fields = (
        ("ema_5", "missing_ema5"),
        ("ema_10", "missing_ema10"),
        ("sma_20", "missing_sma20"),
        ("rsi_14", "missing_rsi"),
        ("macd", "missing_macd"),
        ("macd_signal", "missing_macd_signal"),
        ("macd_histogram", "missing_macd_histogram"),
    )
    reasons = [reason for field, reason in fields if getattr(snapshot, field, None) is None]
    if reasons:
        return ("missing_indicator_field", *reasons, "invalid_indicator_snapshot")
    return ()


def _sma_decimal(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    out: list[Decimal | None] = []
    for idx in range(len(values)):
        if idx + 1 < period:
            out.append(None)
        else:
            out.append(sum(values[idx + 1 - period: idx + 1], Decimal("0")) / Decimal(period))
    return out


def _atr_decimal(candles: Sequence[Candle], period: int) -> dict[int, Decimal]:
    trs: list[Decimal] = []
    out: dict[int, Decimal] = {}
    previous_close: Decimal | None = None
    for idx, candle in enumerate(candles):
        tr = candle.high - candle.low if previous_close is None else max(
            candle.high - candle.low,
            abs(candle.high - previous_close),
            abs(candle.low - previous_close),
        )
        trs.append(tr)
        if len(trs) >= period:
            out[idx] = sum(trs[-period:], Decimal("0")) / Decimal(period)
        previous_close = candle.close
    return out


def _crossed_above(row: dict[str, Any], prev: dict[str, Any] | None, left: str, right: str) -> bool:
    return prev is not None and prev.get(left) is not None and prev.get(right) is not None and row[left] > row[right] and prev[left] <= prev[right]


def _crossed_below(row: dict[str, Any], prev: dict[str, Any] | None, left: str, right: str) -> bool:
    return prev is not None and prev.get(left) is not None and prev.get(right) is not None and row[left] < row[right] and prev[left] >= prev[right]


def _macd_bullish_or_improving(row: dict[str, Any], prev: dict[str, Any] | None) -> bool:
    return bool(row["macd"] > row["macd_signal"] or _macd_hist_improving(row, prev))


def _macd_hist_improving(row: dict[str, Any], prev: dict[str, Any] | None) -> bool:
    return prev is not None and prev.get("macd_histogram") is not None and row["macd_histogram"] > prev["macd_histogram"]


def _macd_bearish_cross(row: dict[str, Any], prev: dict[str, Any] | None) -> bool:
    return bool(prev is not None and prev.get("macd") is not None and prev.get("macd_signal") is not None and prev["macd"] >= prev["macd_signal"] and row["macd"] < row["macd_signal"])


def _prior_high(candles: Sequence[Candle], signal_index: int, lookback: int) -> Decimal | None:
    prior = candles[max(0, signal_index - lookback):signal_index]
    if len(prior) < lookback:
        return None
    return max(candle.high for candle in prior)


def _spread_cross_count(rows: Sequence[dict[str, Any]], left: str, right: str, lookback: int) -> int:
    selected = rows[-lookback:]
    signs: list[int] = []
    for row in selected:
        if row.get(left) is None or row.get(right) is None:
            continue
        signs.append(1 if row[left] > row[right] else -1)
    return sum(1 for idx in range(1, len(signs)) if signs[idx] != signs[idx - 1])


def _low_directional_progress(candles: Sequence[Candle], idx: int, lookback: int) -> bool:
    if idx + 1 < lookback:
        return False
    selected = candles[idx + 1 - lookback:idx + 1]
    high = max(candle.high for candle in selected)
    low = min(candle.low for candle in selected)
    if high <= low:
        return True
    progress = abs(selected[-1].close - selected[0].close) / (high - low)
    return progress < Decimal("0.2")


def _profitable(open_position: _OpenOriginalPosition, price: Decimal) -> bool:
    return price > open_position.entry_price


def _apply_slippage(price: Decimal, *, side: str, slippage_bps: Decimal) -> Decimal:
    factor = Decimal("1") + (slippage_bps / Decimal("10000")) if side == "buy" else Decimal("1") - (slippage_bps / Decimal("10000"))
    return _money(price * factor)


def _mark_to_market_equity(current_realized_equity: Decimal, open_position: _OpenOriginalPosition, price: Decimal) -> Decimal:
    unrealized = (price - open_position.entry_price) * open_position.remaining_quantity
    return _money(current_realized_equity + unrealized)


def _outcome_label(rows: Sequence[dict[str, Any]]) -> str:
    pnl_delta = sum((_dec(row["net_pnl_delta_vs_v1_2"]) for row in rows), Decimal("0"))
    dd_delta = max((_dec(row["drawdown_delta_vs_v1_2"]) for row in rows), default=Decimal("0"))
    trade_count = sum(int(row["trade_count"]) for row in rows)
    if trade_count < 3:
        return "insufficient_sample"
    if pnl_delta > 0 and dd_delta <= 0:
        return "improved_pnl_drawdown_pre_gate"
    if pnl_delta > 0 and dd_delta > 0:
        return "higher_return_but_higher_drawdown"
    if pnl_delta <= 0 and dd_delta <= 0:
        return "lower_drawdown_but_lower_return"
    return "source_faithful_but_underperformed"


def _fallback_outcome_from_blockers(blockers: Sequence[str]) -> str:
    if "insufficient_sample" in blockers:
        return "insufficient_sample"
    if "did_not_improve_net_pnl_vs_v1_2" in blockers and "drawdown_worse_than_v1_2" not in blockers:
        return "lower_drawdown_but_lower_return"
    if "drawdown_worse_than_v1_2" in blockers and "did_not_improve_net_pnl_vs_v1_2" not in blockers:
        return "higher_return_but_higher_drawdown"
    return "source_faithful_but_underperformed"


def _mf_orig_group_summary(
    rows: Sequence[dict[str, Any]],
    keys: Sequence[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "unknown")) for key in keys)].append(row)
    output: list[dict[str, Any]] = []
    for values, selected in sorted(grouped.items()):
        wins = [row for row in selected if _dec(row.get("net_pnl")) > 0]
        losses = [row for row in selected if _dec(row.get("net_pnl")) < 0]
        net_pnl = sum((_dec(row.get("net_pnl")) for row in selected), Decimal("0"))
        delta = sum((_dec(row.get("net_pnl_delta_vs_v1_2")) for row in selected), Decimal("0"))
        drawdown = max((_dec(row.get("max_drawdown")) for row in selected), default=Decimal("0"))
        drawdown_delta = max((_dec(row.get("drawdown_delta_vs_v1_2")) for row in selected), default=Decimal("0"))
        row_out = {key: value for key, value in zip(keys, values, strict=True)}
        row_out.update(
            {
                "row_count": len(selected),
                "hypothesis_count": len({row.get("hypothesis_id") for row in selected}),
                "net_pnl_sum_across_independent_scenarios": _fmt(net_pnl),
                "net_pnl_delta_vs_v1_2_sum": _fmt(delta),
                "worst_max_drawdown": _fmt(drawdown),
                "worst_drawdown_delta_vs_v1_2": _fmt(drawdown_delta),
                "trade_count_sum": sum(int(row.get("trade_count") or 0) for row in selected),
                "win_scenario_count": len(wins),
                "loss_scenario_count": len(losses),
                "aggregate_label": "sum across independent research scenarios",
                "not_one_account_pnl": True,
            }
        )
        output.append(row_out)
    return output


def _compact_mf_orig_ev2_report(report: dict[str, Any]) -> dict[str, Any]:
    compact = dict(report)
    trade_results = compact.pop("trade_results", [])
    compact["trade_result_count"] = len(trade_results)
    compact["trade_samples"] = compact.get("trade_samples", [])[:250]
    return compact


def _hypothesis_definitions() -> list[dict[str, Any]]:
    return [
        {
            "hypothesis_id": "mf_orig_1d_stage2_5_20_crossover",
            "timeframe_policy": "1d primary; 4h/1h comparative only",
            "entry": ["price closes above SMA20", "EMA5 crosses above SMA20", "MACD bullish crossover or histogram improving", "RSI not extreme-overbought"],
            "exit": ["EMA5 crosses below SMA20", "price closes below SMA20", "structure stop hit"],
            "profit_management": ["RSI > 70 is warning", "MACD bearish crossover while profitable trims 25%"],
            "sizing": "risk_budget=current_realized_equity*1%; size=risk_budget/(entry-stop); notional capped at current equity",
        },
        {
            "hypothesis_id": "mf_orig_1d_stage2_breakout_resistance",
            "entry": ["price breaks above prior 20-candle resistance", "price above SMA20", "EMA5 above/crossing SMA20", "MACD confirmation or improving"],
        },
        {
            "hypothesis_id": "mf_orig_stage2_pullback_reclaim",
            "entry": ["Stage 2 already active", "pullback near EMA10/SMA20", "price reclaims EMA5/EMA10", "MACD not strongly bearish or improving"],
        },
        {
            "hypothesis_id": "mf_orig_stage_filter_only",
            "entry": ["diagnostic current-v1.2-like EMA/RSI/MACD entry", "blocked unless original Stage 2 is active"],
        },
    ]


def mf_orig_ev1_spec_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MF-ORIG-EV1.1 Original Money Flow Spec And Gap Matrix",
        "",
        "MF-ORIG-EV1.1 preserves the MF-ORIG-EV1 source interpretation but hotpatches accounting/drawdown truth in the regenerated reconstruction report. Pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions should not be used.",
        "",
        "## Source Document",
        "",
        f"- `title`: `{report['source_document']['title']}`",
        f"- `author`: `{report['source_document']['author']}`",
        f"- `edition`: `{report['source_document']['edition']}`",
        f"- `source_basis`: `{report['source_document']['source_basis']}`",
        f"- `direct_pdf_available_to_agent`: `{str(report['source_document']['direct_pdf_available_to_agent']).lower()}`",
        "",
        "The PDF was not present in the repository or common local paths during this implementation. MF-ORIG-EV1 therefore records the prompt-provided source-truth summary as the source basis and marks subjective translations explicitly.",
        "",
        "## Source Rule Extraction",
        "",
        "| Section | Source Rule | Evidence Translation | Assumption Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["source_rule_extraction"]:
        lines.append(f"| {row['section']} | {row['source_rule']} | {row['evidence_translation']} | `{row['assumption_status']}` |")
    lines.extend(["", "## Gap Matrix", "", "| Original PDF Rule | Current Money Flow v1.2 Behavior | Gap / Drift | Evidence Implication | Reconstruction |", "| --- | --- | --- | --- | --- |"])
    for row in report["gap_matrix"]:
        lines.append(
            f"| {row['original_pdf_rule']} | {row['current_v1_2_behavior']} | {row['gap_or_drift']} | {row['evidence_implication']} | {row['source_faithful_reconstruction']} |"
        )
    lines.extend([
        "",
        "## Required Boundaries",
        "",
        "- MF-ORIG-EV1.1 is evidence-only.",
        "- Current Money Flow v1.2 production rules remain unchanged.",
        "- Original Money Flow is not production approved.",
        "- No paper/live approval follows from MF-ORIG-EV1.",
        "- Testnet execution is separate from strategy evidence.",
        "- Dashboard date filters are display-only and not canonical evidence.",
    ])
    return "\n".join(lines) + "\n"


def mf_orig_ev2_report_to_markdown(report: dict[str, Any]) -> str:
    pack_paths = report.get("evidence_pack_status", {}).get("evidence_pack_paths", [])
    dashboard = report.get("dashboard_integration_status", {})
    lines = [
        "# MF-ORIG-EV2 Multi-Timeframe Original Money Flow Evidence Packs",
        "",
        "## Executive Summary",
        "",
        "MF-ORIG-EV2 extends the corrected MF-ORIG-EV1.1 Original Money Flow reconstruction across all canonical SV2.0.2 supported symbols and all four timeframes for founder review. It is evidence-only. Production Money Flow v1.2 is unchanged. No orders are submitted. No private/signed/order endpoints are called.",
        "",
        "## Scope",
        "",
        "- Hypotheses: `mf_orig_stage2_5_20_crossover`, `mf_orig_stage2_breakout_resistance`, `mf_orig_stage2_pullback_reclaim`, `mf_orig_stage_filter_only`.",
        "- Symbols: `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `HYPE`, `BNB`, `SUI`, `AVAX`.",
        "- Timeframes: `15m`, `1h`, `4h`, `1d`.",
        "- Fill assumptions: `next_candle_open`, `next_candle_close`.",
        "- Accounting: `event_ledger_accounting` with `peak_to_trough` drawdown.",
        "- Baseline: canonical SV2.0.2 Money Flow v1.2 DB-imported evidence timestamp `20260512T064916Z`.",
        "",
        "## Timeframe Interpretation",
        "",
        "| Timeframe | Role |",
        "| --- | --- |",
    ]
    for timeframe in ["1d", "4h", "1h", "15m"]:
        lines.append(f"| `{timeframe}` | `{report.get('timeframe_interpretation', {}).get(timeframe, 'unknown')}` |")
    lines.extend([
        "",
        "## Evidence Pack Status",
        "",
        f"- Status: `{report.get('evidence_pack_status', {}).get('status', 'unknown')}`",
        f"- Pack count: `{len(pack_paths)}`",
        "- Generated evidence-pack directories are review artifacts and are not committed as large generated packs.",
        "",
        "## Hypothesis Summary",
        "",
        "| Hypothesis | Scenarios | 1D Scenarios | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades | Candidate Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in report.get("hypothesis_summary", []):
        lines.append(
            f"| `{row['hypothesis_id']}` | {row['scenario_count']} | {row['one_day_scenario_count']} | {row['net_pnl_delta_sum_across_independent_scenarios']} | {row['worst_drawdown_delta_vs_v1_2']} | {row['trade_count_sum']} | `{row.get('outcome_label')}` |"
        )
    lines.extend([
        "",
        "## Per-Timeframe Results",
        "",
        "| Timeframe | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in report.get("per_timeframe_summary", []):
        lines.append(
            f"| `{row.get('timeframe')}` | {row['row_count']} | {row['net_pnl_delta_vs_v1_2_sum']} | {row['worst_drawdown_delta_vs_v1_2']} | {row['trade_count_sum']} |"
        )
    lines.extend([
        "",
        "## Per-Symbol Results",
        "",
        "| Symbol | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in report.get("per_symbol_summary", []):
        lines.append(
            f"| `{row.get('symbol')}` | {row['row_count']} | {row['net_pnl_delta_vs_v1_2_sum']} | {row['worst_drawdown_delta_vs_v1_2']} | {row['trade_count_sum']} |"
        )
    lines.extend([
        "",
        "## Candidate Gate",
        "",
        "| Hypothesis | Status | Gate Blockers |",
        "| --- | --- | --- |",
    ])
    for row in report.get("candidate_status", []):
        lines.append(f"| `{row['hypothesis_id']}` | `{row['status']}` | `{', '.join(row.get('gate_blockers', [])) or 'none'}` |")
    lines.extend([
        "",
        "## Dashboard Status",
        "",
        f"- Historical Replay: `{dashboard.get('historical_replay', 'unknown')}`",
        f"- Evidence UI: `{dashboard.get('evidence_ui', 'unknown')}`",
        f"- Date-filter warning: `{dashboard.get('date_filter_warning', 'display_filtered_not_canonical_pack_regeneration')}`",
        "",
        "The dashboard date filters are display-only recalculations from loaded evidence trades. Exact arbitrary-date canonical evidence requires backend Strategy Validation regeneration.",
        "",
        "## Control Pockets",
        "",
        "| Hypothesis | Pocket | Status | PnL Delta | Drawdown Delta |",
        "| --- | --- | --- | ---: | ---: |",
    ])
    for row in report.get("control_pocket_results", []):
        lines.append(
            f"| `{row['hypothesis_id']}` | `{row['control_pocket']}` | `{row['status']}` | {row.get('net_pnl_delta_sum', 'n/a')} | {row.get('worst_drawdown_delta', 'n/a')} |"
        )
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    for item in report.get("limitations", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Boundary Confirmation",
        "",
        "- MF-ORIG-EV2 is evidence-only.",
        "- Production Money Flow v1.2 remains unchanged.",
        "- No MF-ORIG hypothesis is approved for production.",
        "- No paper-runtime approval follows from this phase.",
        "- Live trading is not approved.",
        "- No orders were submitted.",
        "- Hyperliquid testnet prices are not strategy truth.",
        "- Independent scenario sums are not one account PnL.",
        "",
        "## Recommended Next Phase",
        "",
        "`MF-ORIG-EV3` should only proceed after founder review of the multi-timeframe replay charts and comparison tables.",
    ])
    return "\n".join(lines) + "\n"


def mf_orig_ev1_report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MF-ORIG-EV1.1 Original Money Flow Reconstruction Accounting Hotpatch",
        "",
        "## Executive Summary",
        "",
        "MF-ORIG-EV1.1 hotpatches MF-ORIG-EV1 accounting and drawdown truth, regenerates the original Money Flow reconstruction reports, and compares the corrected evidence with canonical Money Flow v1.2 SV2.0.2 evidence. Pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions were quarantined until this regeneration. Production Money Flow rules are unchanged. No orders are submitted. No private/signed/order endpoints are called.",
        "",
        "## Hotpatch Accounting Convention",
        "",
        "- Accounting model: `event_ledger_accounting`.",
        "- Entry fees are counted exactly once as `entry_fee` accounting events.",
        "- Trim realized PnL is counted exactly once as `trim_close` accounting events.",
        "- Final close events close only remaining quantity and do not re-add prior trim PnL.",
        "- Trade `net_pnl` is the sum of accounting-event `net_amount` values.",
        "- `equity_after_trade - equity_before_trade == net_pnl` for generated trades.",
        "- Drawdown method: `peak_to_trough`.",
        "- Candidate gate drawdown metric: `mark_to_market_max_drawdown`.",
        "",
        "## Source Limitation",
        "",
        report["source_document"]["limitation"],
        "",
        "## Hypotheses",
        "",
    ]
    for row in report["hypothesis_definitions"]:
        lines.append(f"- `{row['hypothesis_id']}`")
    lines.extend([
        "",
        "## Data Source",
        "",
        f"- Canonical baseline: `{report['data_sources']['canonical_baseline']}`",
        f"- Canonical timestamp: `{report['data_sources']['canonical_timestamp']}`",
        "- Strategy truth: DB-imported Hyperliquid public mainnet candles from SV2.0.2 pack requests.",
        "- Hyperliquid testnet prices are not used as strategy truth.",
        "",
        "## Baseline Parity",
        "",
        f"- Status counts: `{report['baseline_parity_summary'].get('status_counts', {})}`",
        "",
        "## Hypothesis Summary",
        "",
        "| Hypothesis | Scenarios | 1D Scenarios | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades | Performance Label | Candidate Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ])
    for row in report["hypothesis_summary"]:
        lines.append(
            f"| `{row['hypothesis_id']}` | {row['scenario_count']} | {row['one_day_scenario_count']} | {row['net_pnl_delta_sum_across_independent_scenarios']} | {row['worst_drawdown_delta_vs_v1_2']} | {row['trade_count_sum']} | `{row['performance_label']}` | `{row['outcome_label']}` |"
        )
    lines.extend([
        "",
        "## Source Gap Summary",
        "",
        "| Source Rule | Current v1.2 Drift | Evidence Implication |",
        "| --- | --- | --- |",
    ])
    for row in report["gap_matrix"]:
        lines.append(f"| {row['original_pdf_rule']} | {row['gap_or_drift']} | {row['evidence_implication']} |")
    lines.extend([
        "",
        "## 1D Primary Evidence",
        "",
    ])
    lines.extend(_timeframe_summary_markdown(report, "1d"))
    lines.extend([
        "",
        "## 4h / 1h Exploratory Evidence",
        "",
    ])
    lines.extend(_timeframe_summary_markdown(report, "4h"))
    lines.extend(_timeframe_summary_markdown(report, "1h"))
    lines.extend([
        "",
        "## Source-Rule Modeling Findings",
        "",
        "- Stage-filtering is modeled deterministically from current/prior candles only; subjective accumulation/distribution language is proxied with whipsaw/range and MA/RSI/MACD context.",
        "- RSI is used as profit-warning / trim context, not the same narrow v1.2 entry sleeve.",
        "- TSI is deferred; MACD is used as the substitute because the source summary allows MACD as confirmation/warning.",
        "- Stops use prior support / confirmed-pivot proxies available before entry; this is a simple structure model and not hand-drawn supply/demand analysis.",
        "- Sizing uses 1% risk budget from current realized equity, entry-to-stop distance, and a current-equity notional cap.",
        "",
        "## Accounting Invariant Audit",
        "",
        f"- Status: `{report['accounting_invariant_summary']['status']}`",
        f"- Trades checked: `{report['accounting_invariant_summary']['trade_count_checked']}`",
        f"- Equity-delta violations: `{report['accounting_invariant_summary']['equity_delta_violations']}`",
        f"- Fee-sum violations: `{report['accounting_invariant_summary']['fee_sum_violations']}`",
        f"- Remaining-quantity violations: `{report['accounting_invariant_summary']['remaining_quantity_violations']}`",
        f"- Entry-fee event violations: `{report['accounting_invariant_summary']['entry_fee_event_violations']}`",
        "",
        "## Comparison Versus Current Money Flow v1.2",
        "",
        "- PnL and drawdown deltas are compared against matching canonical SV2.0.2 Money Flow v1.2 independent scenarios.",
        "- Independent scenario deltas are descriptive sums, not one combined account.",
        "- Pre-gate aggregate improvement is not enough for candidate status when control pockets are damaged.",
        "- The candidate gate was re-run after MF-ORIG-EV1.1 accounting and drawdown corrections.",
        "- Candidate conclusions did not change after the correction: all original hypotheses remain `source_faithful_but_underperformed` because baseline-positive 1d control pockets were not preserved.",
    ])
    lines.extend([
        "",
        "## Candidate Gate",
        "",
        "| Hypothesis | Status | Gate Blockers |",
        "| --- | --- | --- |",
    ])
    for row in report["candidate_status"]:
        lines.append(f"| `{row['hypothesis_id']}` | `{row['status']}` | `{', '.join(row['gate_blockers']) or 'none'}` |")
    lines.extend([
        "",
        "## Stop / Risk Sizing",
        "",
        "- Risk per trade: 1% or less of current realized equity.",
        "- Position size: risk budget divided by entry-to-stop distance.",
        "- Notional cap: current realized equity.",
        "- Stop model: prior support/pivot proxy available before entry; no arbitrary fixed-percent primary stop.",
        "",
        "## Control Pocket Label Fix",
        "",
        "- `positive 1d pockets` now filters to baseline-positive 1d scenarios only.",
        "- `all_1d_pockets` is reported separately as context and does not imply positivity.",
        "",
        "## Limitations",
        "",
    ])
    for item in report["limitations"]:
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Boundary Confirmation",
        "",
        "- MF-ORIG-EV1.1 is evidence-only.",
        "- Current Money Flow v1.2 remains unchanged.",
        "- Original Money Flow is not approved for production.",
        "- Live trading is not approved.",
        "- No orders were submitted.",
        "- No private/signed/order endpoints were called.",
        "- Dashboard date-filter recalculations are not canonical evidence.",
        "",
        "## Recommended Next Phase",
        "",
        "`MF-ORIG-EV2` should only proceed if the founder wants dashboard overlays and deeper source-rule refinement after reviewing this first reconstruction.",
    ])
    return "\n".join(lines) + "\n"


def _timeframe_summary_markdown(report: dict[str, Any], timeframe: str) -> list[str]:
    selected = [row for row in report["replay_results"] if row["timeframe"] == timeframe]
    if not selected:
        return [f"- `{timeframe}`: no replay rows."]
    by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        by_hypothesis[row["hypothesis_id"]].append(row)
    lines = [
        f"- `{timeframe}` rows: `{len(selected)}` across `{len(by_hypothesis)}` hypotheses.",
        "| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for hypothesis_id, rows in sorted(by_hypothesis.items()):
        net_pnl = sum((_dec(row["net_pnl"]) for row in rows), Decimal("0"))
        delta = sum((_dec(row["net_pnl_delta_vs_v1_2"]) for row in rows), Decimal("0"))
        trades = sum(int(row["trade_count"]) for row in rows)
        lines.append(f"| `{hypothesis_id}` | {len(rows)} | {_fmt(net_pnl)} | {_fmt(delta)} | {trades} |")
    return lines


def _assert_safe_report_language(markdown: str) -> None:
    lowered = markdown.lower()
    for phrase in FORBIDDEN_REPORT_PHRASES:
        if phrase in lowered:
            raise ValueError(f"forbidden report phrase present: {phrase}")
