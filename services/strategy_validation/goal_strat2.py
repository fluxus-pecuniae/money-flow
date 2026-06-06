"""GOAL-STRAT2 research-only selector for two non-existing strategies.

This module consumes the committed GOAL-STRAT1 discovery summary and selects
strategies worth founder paper-testing review. It does not run runtime code,
call exchange endpoints, create order artifacts, or approve production/live use.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


PHASE = "GOAL-STRAT2"
SOURCE_SUMMARY_PATH = Path("docs/goal_strat1_strategy_discovery_summary.json")
REPORT_PATH = Path("docs/goal_strat2_two_non_existing_strategies.md")
SUMMARY_PATH = Path("docs/goal_strat2_two_non_existing_strategies_summary.json")

CANDIDATE_LABEL = "candidate_for_founder_paper_testing_review"
RESEARCH_ONLY_LABEL = "research_only_not_production_approved_not_live_approved"

EXISTING_RUNTIME_LANES = {
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
}

EXCLUDED_EXISTING_OR_ADJACENT_FAMILIES = {
    "money_flow_repair",
    "source_faithful_money_flow",
    "volatility_expansion",
}

EXISTING_OR_ADJACENT_ENTRY_MODELS = {
    "mf_pullback_reclaim",
    "mf_macd_reacceleration",
    "mf_ema10_reclaim_after_reset",
    "stage2_5_20_cross",
    "stage2_pullback_sma20_reclaim",
    "stage2_resistance_breakout",
    "volatility_expansion_breakout",
    "atr_expansion_trend",
}


@dataclass(frozen=True, slots=True)
class TestingGate:
    min_net_pnl: Decimal = Decimal("0")
    min_profit_factor: Decimal = Decimal("1.30")
    max_drawdown_pct: Decimal = Decimal("0.32")
    min_trade_count: int = 200
    min_chronological_oos_pnl: Decimal = Decimal("-500")
    min_anchored_oos_pnl: Decimal = Decimal("-500")
    max_single_symbol_positive_concentration: Decimal = Decimal("0.65")
    require_family_diversity: bool = True


def build_goal_strat2_report(source_summary_path: Path = SOURCE_SUMMARY_PATH) -> dict[str, Any]:
    source = json.loads(source_summary_path.read_text(encoding="utf-8"))
    gate = TestingGate()
    eligible = [_classify_run(run, gate) for run in source["candidate_runs"]]
    passing = [row for row in eligible if row["testing_status"] == CANDIDATE_LABEL]
    selected = _select_diverse_top_two(passing)
    near_misses = [row for row in eligible if row["testing_status"] != CANDIDATE_LABEL]
    near_misses.sort(key=_sort_key, reverse=True)
    return {
        "phase": PHASE,
        "status": "research_only_two_strategy_selection_complete",
        "source_summary": str(source_summary_path),
        "source_conclusion": source.get("conclusion"),
        "candidate_label": CANDIDATE_LABEL,
        "gate": {
            "min_net_pnl": str(gate.min_net_pnl),
            "min_profit_factor": str(gate.min_profit_factor),
            "max_drawdown_pct": str(gate.max_drawdown_pct),
            "min_trade_count": gate.min_trade_count,
            "min_chronological_oos_pnl": str(gate.min_chronological_oos_pnl),
            "min_anchored_oos_pnl": str(gate.min_anchored_oos_pnl),
            "max_single_symbol_positive_concentration": str(gate.max_single_symbol_positive_concentration),
            "require_family_diversity": gate.require_family_diversity,
            "not_existing_strategy_policy": {
                "excluded_runtime_lanes": sorted(EXISTING_RUNTIME_LANES),
                "excluded_existing_or_adjacent_families": sorted(EXCLUDED_EXISTING_OR_ADJACENT_FAMILIES),
                "excluded_existing_or_adjacent_entry_models": sorted(EXISTING_OR_ADJACENT_ENTRY_MODELS),
            },
        },
        "candidate_runs_screened": len(source["candidate_runs"]),
        "eligible_non_existing_candidates": len(passing),
        "selected_candidates": selected,
        "top_near_misses": near_misses[:10],
        "rejection_reason_counts": dict(Counter(reason for row in eligible for reason in row["testing_gate_reasons"] if row["testing_status"] != CANDIDATE_LABEL)),
        "boundary_flags": boundary_flags(),
        "decision": "two_non_existing_strategies_worth_testing" if len(selected) == 2 else "two_non_existing_strategies_not_found",
        "next_phase": "founder_review_then_optional_research_only_paper_testing_lane_scope",
    }


def write_goal_strat2_outputs(
    report: dict[str, Any],
    report_path: Path = REPORT_PATH,
    summary_path: Path = SUMMARY_PATH,
    candidate_dir: Path = Path("docs"),
) -> None:
    report_path.write_text(markdown_report(report), encoding="utf-8")
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_dir.mkdir(parents=True, exist_ok=True)
    for index, candidate in enumerate(report["selected_candidates"], start=1):
        slug = candidate["strategy_id"][:90]
        (candidate_dir / f"goal_strat2_candidate_{index}_{slug}.md").write_text(candidate_markdown(index, candidate, report), encoding="utf-8")


def boundary_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "mutates_active_pt_rt_runtime": False,
        "creates_runtime_artifacts": False,
        "submits_live_orders": False,
        "submits_testnet_orders": False,
        "calls_private_signed_order_endpoints": False,
        "uses_testnet_data_as_strategy_truth": False,
        "uses_testnet_fills_as_pnl_truth": False,
        "changes_production_money_flow_rules": False,
        "approves_production_strategy": False,
        "approves_live_trading": False,
        "creates_order_intent": False,
        "creates_prepared_venue_order": False,
        "creates_submitted_order": False,
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# GOAL-STRAT2 Two Non-Existing Strategies Worth Testing",
        "",
        "GOAL-STRAT2 is research-only. No strategy is production-approved. Live trading is not approved.",
        "",
        "## Decision",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Candidate runs screened: `{report['candidate_runs_screened']}`",
        f"- Eligible non-existing candidates: `{report['eligible_non_existing_candidates']}`",
        f"- Selected candidates: `{len(report['selected_candidates'])}`",
        "",
        "## Selected Candidates",
        "",
    ]
    for index, candidate in enumerate(report["selected_candidates"], start=1):
        m = candidate["active_timeframe_metrics"]
        o = candidate["chronological_oos_metrics"]
        a = candidate["anchored_walk_forward_metrics"]
        lines.extend(
            [
                f"### {index}. `{candidate['strategy_id']}`",
                "",
                f"- Family: `{candidate['strategy_family']}`",
                f"- Entry / exit / risk / regime: `{candidate['entry_model']}` / `{candidate['exit_model']}` / `{candidate['risk_model']}` / `{candidate['regime_filter']}`",
                f"- Active net PnL: `{m['net_pnl']}`",
                f"- Profit factor: `{m['profit_factor']}`",
                f"- Max drawdown pct: `{m['max_drawdown_pct']}`",
                f"- Trade count: `{m['trade_count']}`",
                f"- Chronological OOS net PnL: `{o['net_pnl']}`",
                f"- Anchored OOS net PnL: `{a['net_pnl']}`",
                f"- Why worth testing: `{'; '.join(candidate['why_worth_testing'])}`",
                f"- Why it may fail: `{'; '.join(candidate['why_may_fail'])}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Gate",
            "",
            f"- Minimum profit factor: `{report['gate']['min_profit_factor']}`",
            f"- Maximum drawdown pct: `{report['gate']['max_drawdown_pct']}`",
            f"- Minimum trade count: `{report['gate']['min_trade_count']}`",
            f"- Minimum chronological OOS net PnL: `{report['gate']['min_chronological_oos_pnl']}`",
            f"- Minimum anchored OOS net PnL: `{report['gate']['min_anchored_oos_pnl']}`",
            "- Existing Money Flow/SOR/MF-ORIG/wildcard-adjacent families and entry models are excluded.",
            "",
            "## Boundaries",
            "",
        ]
    )
    for key, value in report["boundary_flags"].items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def candidate_markdown(index: int, candidate: dict[str, Any], report: dict[str, Any]) -> str:
    m = candidate["active_timeframe_metrics"]
    o = candidate["chronological_oos_metrics"]
    a = candidate["anchored_walk_forward_metrics"]
    return "\n".join(
        [
            f"# GOAL-STRAT2 Candidate {index}: {candidate['display_name']}",
            "",
            "This is a founder paper-testing review candidate only. It is not production-approved and live trading is not approved.",
            "",
            "## Strategy Logic",
            "",
            f"- Strategy id: `{candidate['strategy_id']}`",
            f"- Family: `{candidate['strategy_family']}`",
            f"- Entry model: `{candidate['entry_model']}`",
            f"- Exit model: `{candidate['exit_model']}`",
            f"- Risk model: `{candidate['risk_model']}`",
            f"- Regime filter: `{candidate['regime_filter']}`",
            "- Current PT runtime lanes excluded: yes.",
            "- Existing Money Flow/SOR/MF-ORIG/wildcard-adjacent families excluded: yes.",
            "",
            "## Evidence",
            "",
            f"- Active net PnL: `{m['net_pnl']}`",
            f"- Ending equity: `{m['ending_equity']}`",
            f"- Max drawdown pct: `{m['max_drawdown_pct']}`",
            f"- Profit factor: `{m['profit_factor']}`",
            f"- Win rate: `{m['win_rate']}`",
            f"- Trade count: `{m['trade_count']}`",
            f"- Largest win: `{m['largest_win']}`",
            f"- Largest loss: `{m['largest_loss']}`",
            f"- Average win: `{m['average_win']}`",
            f"- Average loss: `{m['average_loss']}`",
            f"- Max consecutive losses: `{m['max_consecutive_losses']}`",
            f"- Chronological OOS net PnL: `{o['net_pnl']}`",
            f"- Anchored OOS net PnL: `{a['net_pnl']}`",
            f"- Symbol concentration: `{candidate['symbol_concentration']}`",
            f"- Timeframe concentration: `{candidate['timeframe_concentration']}`",
            f"- Period concentration: `{candidate['period_concentration']}`",
            "",
            "## Why It Is Worth Testing",
            "",
            *[f"- {item}" for item in candidate["why_worth_testing"]],
            "",
            "## Why It May Still Fail",
            "",
            *[f"- {item}" for item in candidate["why_may_fail"]],
            "",
            "## Boundary",
            "",
            "Research-only. Do not route to testnet or live trading. Do not treat this as production approval.",
        ]
    ) + "\n"


def _classify_run(run: dict[str, Any], gate: TestingGate) -> dict[str, Any]:
    candidate = dict(run)
    reasons = []
    if run["strategy_id"] in EXISTING_RUNTIME_LANES:
        reasons.append("existing_runtime_lane_excluded")
    if run["strategy_family"] in EXCLUDED_EXISTING_OR_ADJACENT_FAMILIES:
        reasons.append("existing_or_adjacent_family_excluded")
    if run["entry_model"] in EXISTING_OR_ADJACENT_ENTRY_MODELS:
        reasons.append("existing_or_adjacent_entry_model_excluded")
    metrics = run["active_timeframe_metrics"]
    chrono = run["chronological_oos_metrics"]
    anchored = run["anchored_walk_forward_metrics"]
    net = Decimal(metrics["net_pnl"])
    pf = Decimal(metrics["profit_factor"] or "0")
    drawdown = Decimal(metrics["max_drawdown_pct"])
    trades = int(metrics["trade_count"])
    chrono_oos = Decimal(chrono["net_pnl"])
    anchored_oos = Decimal(anchored["net_pnl"])
    symbol_concentration = max((Decimal(value) for value in run.get("symbol_concentration", {}).values()), default=Decimal("0"))
    if net <= gate.min_net_pnl:
        reasons.append("net_pnl_not_positive")
    if pf < gate.min_profit_factor:
        reasons.append("profit_factor_below_testing_gate")
    if drawdown > gate.max_drawdown_pct:
        reasons.append("drawdown_above_testing_gate")
    if trades < gate.min_trade_count:
        reasons.append("trade_count_below_testing_gate")
    if chrono_oos < gate.min_chronological_oos_pnl:
        reasons.append("chronological_oos_too_negative_for_testing")
    if anchored_oos < gate.min_anchored_oos_pnl:
        reasons.append("anchored_oos_too_negative_for_testing")
    if symbol_concentration > gate.max_single_symbol_positive_concentration:
        reasons.append("symbol_concentration_above_testing_gate")
    candidate["testing_gate_reasons"] = reasons
    candidate["testing_status"] = CANDIDATE_LABEL if not reasons else "not_worth_testing_yet"
    candidate["why_worth_testing"] = _why_worth_testing(candidate) if not reasons else []
    candidate["why_may_fail"] = _why_may_fail(candidate)
    candidate["research_status"] = RESEARCH_ONLY_LABEL
    candidate["not_existing_strategy"] = not any(
        reason in reasons
        for reason in (
            "existing_runtime_lane_excluded",
            "existing_or_adjacent_family_excluded",
            "existing_or_adjacent_entry_model_excluded",
        )
    )
    return candidate


def _select_diverse_top_two(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(rows, key=_sort_key, reverse=True)
    selected: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    for row in rows:
        if row["strategy_family"] in seen_families:
            continue
        selected.append(row)
        seen_families.add(row["strategy_family"])
        if len(selected) == 2:
            return selected
    for row in rows:
        if row not in selected:
            selected.append(row)
            if len(selected) == 2:
                break
    return selected


def _sort_key(row: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    metrics = row["active_timeframe_metrics"]
    chrono = row["chronological_oos_metrics"]
    anchored = row["anchored_walk_forward_metrics"]
    oos_floor = min(Decimal(chrono["net_pnl"]), Decimal(anchored["net_pnl"]))
    return (
        oos_floor,
        Decimal(metrics["profit_factor"] or "0"),
        Decimal(metrics["net_pnl"]),
        -Decimal(metrics["max_drawdown_pct"]),
    )


def _why_worth_testing(row: dict[str, Any]) -> list[str]:
    metrics = row["active_timeframe_metrics"]
    chrono = row["chronological_oos_metrics"]
    anchored = row["anchored_walk_forward_metrics"]
    reasons = [
        "non-existing strategy family relative to current PT runtime lanes",
        f"positive active net PnL {metrics['net_pnl']} after fees/slippage",
        f"profit factor {metrics['profit_factor']} exceeds paper-testing gate",
        f"{metrics['trade_count']} trades is enough for forward paper-testing triage",
        f"drawdown {metrics['max_drawdown_pct']} stays inside paper-testing gate",
    ]
    if Decimal(chrono["net_pnl"]) >= 0 and Decimal(anchored["net_pnl"]) >= 0:
        reasons.append("both OOS checks are positive")
    elif Decimal(chrono["net_pnl"]) >= 0 or Decimal(anchored["net_pnl"]) >= 0:
        reasons.append("one OOS check is positive and the other is near-flat enough for paper testing")
    else:
        reasons.append("OOS losses are small enough to justify forward testing but not promotion")
    return reasons


def _why_may_fail(row: dict[str, Any]) -> list[str]:
    reasons = []
    metrics = row["active_timeframe_metrics"]
    chrono = row["chronological_oos_metrics"]
    anchored = row["anchored_walk_forward_metrics"]
    if Decimal(chrono["net_pnl"]) < 0:
        reasons.append("chronological OOS is negative")
    if Decimal(anchored["net_pnl"]) < 0:
        reasons.append("anchored OOS is negative")
    if Decimal(metrics["max_drawdown_pct"]) > Decimal("0.30"):
        reasons.append("drawdown is near the upper testing bound")
    symbol_concentration = max((Decimal(value) for value in row.get("symbol_concentration", {}).values()), default=Decimal("0"))
    timeframe_concentration = max((Decimal(value) for value in row.get("timeframe_concentration", {}).values()), default=Decimal("0"))
    period_concentration = max((Decimal(value) for value in row.get("period_concentration", {}).values()), default=Decimal("0"))
    if symbol_concentration > Decimal("0.30"):
        reasons.append("single-symbol contribution is material and must be monitored in paper testing")
    if timeframe_concentration > Decimal("0.55"):
        reasons.append("timeframe contribution is concentrated and should be reviewed by timeframe")
    if period_concentration > Decimal("0.45"):
        reasons.append("period contribution is concentrated and may not persist")
    reasons.append("candle-only backtest lacks order-book, funding, partial-fill, and live reject modeling")
    reasons.append("forward testing must be paper-only before any runtime lane discussion")
    return reasons


if __name__ == "__main__":
    report = build_goal_strat2_report()
    write_goal_strat2_outputs(report)
    print(report["decision"])
    for candidate in report["selected_candidates"]:
        print(candidate["strategy_id"])
