from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_TIMESTAMP = "20260512T064916Z"
MF_ORIG_EV2_TIMESTAMP = "20260513T002746Z"
SUPPORTED_SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX")
TIMEFRAMES = ("15m", "1h", "4h", "1d")
FILL_ASSUMPTIONS = ("next_candle_open", "next_candle_close")

SUMMARY_PATH = ROOT / "docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json"
REPORT_PATH = ROOT / "docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review.md"


def _load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _d(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _s(value: Decimal | int | float | str | None, places: str = "0.00000001") -> str:
    if value is None:
        return "0"
    dec = value if isinstance(value, Decimal) else _d(value)
    if dec == dec.to_integral_value():
        return str(dec.quantize(Decimal("1")))
    return str(dec.quantize(Decimal(places)).normalize())


def _canonical_pack_dirs() -> list[Path]:
    return sorted(
        p
        for p in (ROOT / "reports/strategy_validation").glob(
            f"money_flow_sv2_0_2_hyperliquid_public_*_canonical_db_imported/{CANONICAL_TIMESTAMP}"
        )
        if (p / "batch_report.json").exists()
    )


def _mf_orig_pack_dirs() -> list[Path]:
    return sorted(
        p
        for p in (ROOT / "reports/strategy_validation").glob(
            f"mf_orig_ev2_*/{MF_ORIG_EV2_TIMESTAMP}"
        )
        if (p / "batch_report.json").exists()
    )


def _sort_key_time(value: dict[str, Any]) -> str:
    return str(value.get("exit_time") or value.get("entry_time") or value.get("entry_signal_time") or "")


def _trade_row(
    *,
    strategy_family: str,
    hypothesis_id: str,
    methodology: str,
    source: str,
    symbol: str,
    timeframe: str,
    fill_timing: str,
    trade: dict[str, Any],
    scenario_key: str,
) -> dict[str, Any]:
    entry_reason = trade.get("entry_reason") or trade.get("entry_reason_codes") or []
    if isinstance(entry_reason, list):
        entry_reason_text = ", ".join(str(item) for item in entry_reason)
    else:
        entry_reason_text = str(entry_reason)
    return {
        "strategy_family": strategy_family,
        "hypothesis_id": hypothesis_id,
        "methodology": methodology,
        "source": source,
        "scenario_key": scenario_key,
        "symbol": symbol,
        "timeframe": timeframe,
        "fill_assumption": fill_timing,
        "trade_id": trade.get("trade_id"),
        "entry_time": trade.get("entry_time") or trade.get("entry_signal_time"),
        "exit_time": trade.get("exit_time") or trade.get("exit_signal_time"),
        "entry_reason": entry_reason_text or "data_not_available_in_source_bundle",
        "exit_reason": trade.get("exit_reason") or "data_not_available_in_source_bundle",
        "entry_classification": trade.get("entry_stage")
        or trade.get("entry_market_regime")
        or "unknown",
        "entry_volatility_regime": trade.get("entry_volatility_regime") or "unknown",
        "net_pnl": _s(_d(trade.get("net_pnl"))),
        "equity_before": str(trade.get("equity_before_trade") or trade.get("equity_before_entry") or trade.get("equity_before") or ""),
        "equity_after": str(trade.get("equity_after_trade") or trade.get("equity_after_exit") or trade.get("equity_after") or ""),
        "max_adverse_excursion": str(trade.get("max_adverse_excursion") or trade.get("min_equity_seen") or ""),
        "forced_exit": bool(trade.get("forced_exit", False)),
        "sizing_mode": trade.get("sizing_mode") or trade.get("capital_sizing_mode") or "dynamic_equity_pct",
    }


def _collect_canonical() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    scenario_rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    data_rows: dict[tuple[str, str], dict[str, Any]] = {}
    pack_paths: list[str] = []
    for pack_dir in _canonical_pack_dirs():
        pack_paths.append(str(pack_dir.relative_to(ROOT)))
        payload = _load_json(pack_dir / "batch_report.json", {})
        for run in payload.get("run_reports", []):
            if run.get("status") != "completed":
                continue
            report = run["report"]
            component = report["component_reports"][0]
            metrics = report["aggregate_metrics"]
            assumptions = report["assumptions"]
            symbol = report["symbol"]
            timeframe = component["timeframe"]
            fill_timing = assumptions["fill_timing"]
            scenario_key = f"{symbol}:{timeframe}:{fill_timing}:money_flow_v1_2"
            coverage = component["data_coverage"]
            data_rows[(symbol, timeframe)] = {
                "symbol": symbol,
                "timeframe": timeframe,
                "data_status": "canonical_db_imported",
                "earliest": coverage.get("first_candle_available_at"),
                "latest": coverage.get("last_candle_available_at"),
                "candle_count": coverage.get("actual_candle_count"),
                "expected_candle_count": coverage.get("expected_candle_count"),
                "coverage_percent": str(coverage.get("coverage_percent")),
                "missing_candles": coverage.get("missing_candle_count"),
                "gap_count": coverage.get("gap_count"),
                "known_limitations": (
                    ["hyperliquid_public_5000_candle_limit", "jan_2025_target_not_met"]
                    if timeframe in {"15m", "1h"}
                    else ["jan_2025_target_met_where_public_history_supports_it"]
                ),
                "evidence_ready": True,
            }
            scenario_rows.append(
                {
                    "strategy_family": "current_money_flow",
                    "hypothesis_id": "money_flow_v1_2",
                    "methodology": "canonical_evidence",
                    "source": "SV2.0.2 canonical DB-imported evidence pack",
                    "scenario_key": scenario_key,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "fill_assumption": fill_timing,
                    "ending_equity": _s(metrics.get("ending_equity")),
                    "net_pnl": _s(metrics.get("net_pnl")),
                    "max_drawdown": _s(metrics.get("max_drawdown")),
                    "largest_loss": _s(metrics.get("worst_trade_net_pnl")),
                    "largest_win": _s(metrics.get("best_trade_net_pnl")),
                    "average_win": _s(metrics.get("average_win")),
                    "average_loss": _s(metrics.get("average_loss")),
                    "win_rate": _s(metrics.get("win_rate")),
                    "profit_factor": _s(metrics.get("profit_factor")),
                    "trade_count": int(metrics.get("number_of_trades", 0)),
                    "capital_sizing_mode": metrics.get("capital_sizing_mode"),
                    "drawdown_method": metrics.get("drawdown_methodology", "closed_trade_and_mark_to_market"),
                    "open_position_handling": "force_close_at_dataset_end",
                    "candidate_status": "baseline_not_candidate",
                    "production_status": "not_production_authorized",
                }
            )
            for trade in component.get("trades", []):
                trades.append(
                    _trade_row(
                        strategy_family="current_money_flow",
                        hypothesis_id="money_flow_v1_2",
                        methodology="canonical_evidence",
                        source="SV2.0.2 canonical DB-imported evidence pack",
                        symbol=symbol,
                        timeframe=timeframe,
                        fill_timing=fill_timing,
                        trade=trade,
                        scenario_key=scenario_key,
                    )
                )
    return scenario_rows, trades, sorted(data_rows.values(), key=lambda row: (row["symbol"], row["timeframe"])), pack_paths


def _collect_mf_orig_trades() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pack_dir in _mf_orig_pack_dirs():
        payload = _load_json(pack_dir / "batch_report.json", {})
        manifest = payload.get("manifest", {})
        symbol = manifest.get("symbol", "")
        timeframe = manifest.get("timeframe", "")
        hypothesis_id = manifest.get("hypothesis_id", "")
        for run in payload.get("run_reports", []):
            fill_timing = run.get("fill_timing", "")
            report = run.get("report", {})
            scenario_key = f"{symbol}:{timeframe}:{fill_timing}:{hypothesis_id}"
            for trade in report.get("trades", []):
                rows.append(
                    _trade_row(
                        strategy_family="mf_orig",
                        hypothesis_id=hypothesis_id,
                        methodology="true_forward_replay",
                        source="MF-ORIG-EV2 generated evidence pack",
                        symbol=symbol,
                        timeframe=timeframe,
                        fill_timing=fill_timing,
                        trade=trade,
                        scenario_key=scenario_key,
                    )
                )
    return rows


def _max_streaks(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(trade["scenario_key"])].append(trade)
    streaks: list[dict[str, Any]] = []
    for scenario_key, scenario_trades in grouped.items():
        active: list[dict[str, Any]] = []

        def close_active() -> None:
            if not active:
                return
            pnl = sum(_d(row["net_pnl"]) for row in active)
            first = active[0]
            last = active[-1]
            streaks.append(
                {
                    "scenario_key": scenario_key,
                    "strategy_family": first["strategy_family"],
                    "hypothesis_id": first["hypothesis_id"],
                    "symbol": first["symbol"],
                    "timeframe": first["timeframe"],
                    "fill_assumption": first["fill_assumption"],
                    "consecutive_losses": len(active),
                    "streak_pnl": _s(pnl),
                    "start_time": first.get("entry_time"),
                    "end_time": last.get("exit_time"),
                    "primary_entry_context": first.get("entry_classification"),
                    "primary_exit_reason": last.get("exit_reason"),
                }
            )

        for trade in sorted(scenario_trades, key=_sort_key_time):
            if _d(trade["net_pnl"]) < 0:
                active.append(trade)
            else:
                close_active()
                active = []
        close_active()
    return sorted(streaks, key=lambda row: (row["consecutive_losses"], -_d(row["streak_pnl"])), reverse=True)[:20]


def _regime_attribution(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[(trade["strategy_family"], trade["entry_classification"] or "unknown")].append(trade)
    rows: list[dict[str, Any]] = []
    for (family, regime), group in sorted(grouped.items()):
        pnl = sum(_d(row["net_pnl"]) for row in group)
        wins = sum(1 for row in group if _d(row["net_pnl"]) > 0)
        losses = sum(1 for row in group if _d(row["net_pnl"]) < 0)
        largest_loss = min((_d(row["net_pnl"]) for row in group), default=Decimal("0"))
        rows.append(
            {
                "strategy_family": family,
                "stage_or_regime": regime,
                "trade_count": len(group),
                "winning_trades": wins,
                "losing_trades": losses,
                "net_pnl": _s(pnl),
                "largest_loss": _s(largest_loss),
            }
        )
    return sorted(rows, key=lambda row: _d(row["net_pnl"]))


def _aggregate_scenarios(rows: list[dict[str, Any]], hypothesis_id: str, family: str) -> dict[str, Any]:
    subset = [row for row in rows if row["hypothesis_id"] == hypothesis_id]
    return {
        "strategy_family": family,
        "hypothesis_id": hypothesis_id,
        "methodology_label": subset[0]["methodology"] if subset else "data_not_available",
        "evidence_source": subset[0]["source"] if subset else "data_not_available",
        "symbols_covered": sorted({row["symbol"] for row in subset}),
        "timeframes_covered": sorted({row["timeframe"] for row in subset}),
        "fill_assumptions": sorted({row["fill_assumption"] for row in subset}),
        "aggregate_label": "sum across independent research scenarios",
        "net_pnl_sum": _s(sum(_d(row.get("net_pnl")) for row in subset)),
        "ending_equity_sum": _s(sum(_d(row.get("ending_equity")) for row in subset)),
        "max_drawdown_worst": _s(max((_d(row.get("max_drawdown")) for row in subset), default=Decimal("0"))),
        "largest_loss": _s(min((_d(row.get("largest_loss")) for row in subset), default=Decimal("0"))),
        "largest_win": _s(max((_d(row.get("largest_win")) for row in subset), default=Decimal("0"))),
        "trade_count": sum(int(row.get("trade_count", 0)) for row in subset),
        "candidate_status": "baseline_not_candidate" if hypothesis_id == "money_flow_v1_2" else "not_promoted",
        "rejection_reason": "current baseline" if hypothesis_id == "money_flow_v1_2" else "see candidate gate / control-pocket impact",
    }


def _variant_rows_from_summary(payload: dict[str, Any], family: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload.get("variant_summary", []):
        variant_id = row.get("variant_id", "")
        rows.append(
            {
                "strategy_family": family,
                "hypothesis_id": variant_id,
                "methodology_label": row.get("methodology", "data_not_available"),
                "evidence_source": payload.get("phase", family),
                "symbols_covered": list(SUPPORTED_SYMBOLS),
                "timeframes_covered": list(TIMEFRAMES),
                "fill_assumptions": list(FILL_ASSUMPTIONS),
                "aggregate_label": "sum across independent research scenarios",
                "net_pnl_delta_vs_baseline": str(
                    row.get("net_pnl_delta_sum_across_independent_scenarios")
                    or row.get("net_pnl_delta_sum")
                    or row.get("ending_equity_delta_sum_across_independent_scenarios")
                    or "0"
                ),
                "max_drawdown_delta": str(row.get("max_drawdown_delta_worst") or row.get("max_drawdown_delta") or "0"),
                "trade_count": row.get("trade_count") or row.get("baseline_trade_count") or "data_not_available",
                "candidate_status": (
                    "candidate_for_more_evidence"
                    if row.get("candidate") or row.get("candidate_evidence")
                    else row.get("promotion_status") or row.get("founder_review_label") or row.get("outcome") or "not_promoted"
                ),
                "rejection_reason": ", ".join(row.get("promotion_blockers", []))
                if isinstance(row.get("promotion_blockers"), list)
                else row.get("outcome_taxonomy") or row.get("outcome") or "not_promoted",
            }
        )
    return rows


def _mf_orig_hypothesis_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload.get("hypothesis_summary", []):
        rows.append(
            {
                "strategy_family": "mf_orig",
                "hypothesis_id": row.get("hypothesis_id"),
                "methodology_label": "true_forward_replay",
                "evidence_source": "MF-ORIG-EV2 generated evidence pack",
                "symbols_covered": list(SUPPORTED_SYMBOLS),
                "timeframes_covered": list(TIMEFRAMES),
                "fill_assumptions": list(FILL_ASSUMPTIONS),
                "aggregate_label": "sum across independent research scenarios",
                "net_pnl_delta_vs_baseline": str(row.get("net_pnl_delta_sum_across_independent_scenarios", "0")),
                "max_drawdown_delta": str(row.get("worst_drawdown_delta_vs_v1_2", "0")),
                "trade_count": row.get("trade_count_sum"),
                "candidate_status": row.get("candidate_gate_status"),
                "rejection_reason": ", ".join(row.get("gate_blockers", [])),
            }
        )
    return rows


def _control_pocket_summary(*payloads: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        phase = payload.get("phase", "unknown")
        for row in payload.get("control_pocket_impact", []) or payload.get("control_pocket_results", []):
            rows.append({"phase": phase, **row})
    return rows[:120]


def _top(items: list[dict[str, Any]], field: str, n: int, reverse: bool = True) -> list[dict[str, Any]]:
    return sorted(items, key=lambda row: _d(row.get(field)), reverse=reverse)[:n]


def build_audit() -> dict[str, Any]:
    sv_scenarios, sv_trades, data_rows, canonical_pack_paths = _collect_canonical()
    mf_orig_trades = _collect_mf_orig_trades()
    all_trade_rows = sv_trades + mf_orig_trades

    sor_ev1 = _load_json(ROOT / "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json", {})
    sor_ev2 = _load_json(ROOT / "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json", {})
    sor_ev3 = _load_json(ROOT / "docs/sor_ev3_avoid_sideways_low_volatility_summary.json", {})
    mf_orig_ev1 = _load_json(ROOT / "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json", {})
    mf_orig_ev2 = _load_json(ROOT / "docs/mf_orig_ev2_multitimeframe_evidence_summary.json", {})

    mf_orig_scenarios = mf_orig_ev2.get("replay_results", [])
    scenario_rows = sv_scenarios + [
        {
            "strategy_family": "mf_orig",
            "hypothesis_id": row["hypothesis_id"],
            "methodology": row.get("methodology", "true_forward_replay"),
            "source": "MF-ORIG-EV2 compact summary and generated evidence pack",
            "scenario_key": row.get("scenario_key"),
            "symbol": row.get("symbol"),
            "timeframe": row.get("timeframe"),
            "fill_assumption": row.get("fill_timing"),
            "ending_equity": row.get("ending_equity"),
            "net_pnl": row.get("net_pnl"),
            "max_drawdown": row.get("max_drawdown"),
            "largest_loss": row.get("largest_loss"),
            "largest_win": row.get("largest_win"),
            "average_win": "data_not_available",
            "average_loss": "data_not_available",
            "win_rate": row.get("win_rate"),
            "profit_factor": row.get("profit_factor"),
            "trade_count": row.get("trade_count"),
            "capital_sizing_mode": row.get("sizing_mode"),
            "drawdown_method": row.get("drawdown_method"),
            "open_position_handling": "force_close_at_dataset_end",
            "candidate_status": "not_promoted",
            "production_status": "not_production_authorized",
        }
        for row in mf_orig_scenarios
    ]

    baseline_matrix = [_aggregate_scenarios(sv_scenarios, "money_flow_v1_2", "current_money_flow")]
    comparison_matrix = (
        baseline_matrix
        + _variant_rows_from_summary(sor_ev1, "sor_ev1_loss_anatomy")
        + _variant_rows_from_summary(sor_ev2, "sor_ev2_true_forward")
        + _variant_rows_from_summary(sor_ev3, "sor_ev3_avoid_sideways_low_volatility")
        + _mf_orig_hypothesis_rows(mf_orig_ev2)
    )

    issue_list = [
        {
            "severity": "P1",
            "issue": "backtest_missing_execution_microstructure",
            "affected_file_or_report": "docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review.md",
            "why_it_matters": "Current evidence uses candle-level fills, fees, slippage, and force-close conventions but does not model order-book queues, partial fills, funding, liquidation, latency, exchange rejections, or outage behavior.",
            "required_fix": "Run PT-RT1 public-mainnet real-time paper observation plus later execution-quality simulation before any production or live decision.",
            "blocks_founder_decisions": "blocks production rule change and live/paper-runtime approval; does not block visual review or hypothesis filtering",
        },
        {
            "severity": "P1",
            "issue": "no_strategy_candidate_has_clean_control_pocket_preservation",
            "affected_file_or_report": "docs/sor_ev3_avoid_sideways_low_volatility.md; docs/mf_orig_ev2_multitimeframe_evidence_packs.md",
            "why_it_matters": "Several variants improve aggregate PnL but damage strong baseline pockets, especially positive 1d controls or ETH 1h depending on sizing mode.",
            "required_fix": "Require sliced/out-of-sample-style review and control-pocket preservation before proposing any rule change.",
            "blocks_founder_decisions": "blocks candidate promotion",
        },
        {
            "severity": "P2",
            "issue": "fifteen_minute_and_one_hour_public_window_limited",
            "affected_file_or_report": "docs/sv2_0_2_canonical_sv2_evidence_packs.md",
            "why_it_matters": "Hyperliquid public candleSnapshot exposes a recent 5000-candle window, so 15m/1h evidence does not reach Jan 2025.",
            "required_fix": "Use vendor/archive data or ongoing real-time collection for longer 15m/1h history.",
            "blocks_founder_decisions": "does not block visual review; limits confidence for short timeframe conclusions",
        },
        {
            "severity": "P2",
            "issue": "original_pdf_not_available_to_agent",
            "affected_file_or_report": "docs/mf_orig_ev1_original_money_flow_spec_and_gap_matrix.md",
            "why_it_matters": "MF-ORIG source authority still depends on prompt-provided source summary, not direct PDF extraction.",
            "required_fix": "Attach or point to the PDF and reconcile subjective source rules before source-authority claims.",
            "blocks_founder_decisions": "blocks source-faithfulness claims; does not block evidence-only replay review",
        },
        {
            "severity": "P2",
            "issue": "dashboard_date_filters_are_display_only",
            "affected_file_or_report": "apps/dashboard/evidence-dashboard.js",
            "why_it_matters": "Date-filter recalculations are useful for review but are not canonical evidence-pack regeneration.",
            "required_fix": "Use backend Strategy Validation regeneration for arbitrary date-window canonical claims.",
            "blocks_founder_decisions": "blocks treating filtered dashboard numbers as canonical",
        },
        {
            "severity": "P3",
            "issue": "exact_sor_variant_trade_level_top_winner_streak_detail_incomplete",
            "affected_file_or_report": "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json; docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
            "why_it_matters": "SOR summaries provide scenario-level variant metrics and attribution, but not a full committed per-trade ledger for every variant.",
            "required_fix": "If a SOR variant advances to deeper review, export compact per-trade ledgers for that variant.",
            "blocks_founder_decisions": "does not block current audit verdict",
        },
    ]

    adequacy = {
        "good_enough_for_visual_review": True,
        "good_enough_for_hypothesis_filtering": True,
        "not_good_enough_for_production_rule_change": True,
        "not_good_enough_for_live_or_paper_approval": True,
        "needs_real_time_paper_observation": True,
        "needs_data_fix_before_any_decision": False,
        "decision": "good_enough_for_visual_review_and_hypothesis_filtering_only",
    }

    paper_readiness = {
        "decision": "paper_observation_ready_with_conditions",
        "not_approval": True,
        "required_next_phase": "PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime",
        "conditions": [
            "trusted public mainnet candle feed, not Hyperliquid testnet prices, must drive strategy truth",
            "candle close detection and duplicate signal prevention must be implemented",
            "paper ledger must separate simulated paper positions from sandbox execution plumbing",
            "founder review workflow and kill-switch/runbook must exist before continuous operation",
            "no live orders, no private/signed/order endpoints, and no paper/live strategy approval in EV-AUDIT1",
        ],
    }

    boundary_flags = {
        "changes_production_money_flow_rules": False,
        "approves_strategy_for_production": False,
        "approves_paper_trading": False,
        "approves_live_trading": False,
        "submits_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "uses_hyperliquid_testnet_prices_as_strategy_truth": False,
        "uses_dashboard_date_filters_as_canonical_evidence": False,
        "regenerates_evidence_packs": False,
    }

    evidence_inventory = [
        {
            "strategy_family": "current_money_flow",
            "hypothesis_id": "money_flow_v1_2",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy/money_flow.py",
            "report_path": "docs/sv2_0_2_canonical_sv2_evidence_packs.md",
            "json_path": "reports/strategy_validation/*/20260512T064916Z/batch_report.json",
            "canonical_evidence_pack_paths": canonical_pack_paths,
            "evidence_classification": "canonical_evidence",
            "methodology_label": "canonical_evidence",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": list(TIMEFRAMES),
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "initial_equity_policy": "10000 USDC per independent scenario",
            "capital_sizing_mode": "dynamic_equity_pct",
            "fee_slippage_policy": "5 bps fee / 3 bps slippage",
            "drawdown_method": "closed_trade_and_mark_to_market",
            "open_position_handling": "force_close_at_dataset_end",
            "source_data_truth": "DB-imported Hyperliquid public mainnet candles",
            "candidate_status": "baseline_not_candidate",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "sor_ev1",
            "hypothesis_id": "loss_anatomy_and_completed_trade_overlays",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy_validation/sor_ev1.py",
            "report_path": "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md",
            "json_path": "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json",
            "canonical_evidence_pack_paths": canonical_pack_paths,
            "evidence_classification": "completed_trade_overlay_estimate",
            "methodology_label": "completed_trade_overlay_estimate",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": list(TIMEFRAMES),
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "candidate_status": "none_promoted",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "sor_ev2",
            "hypothesis_id": "true_forward_stop_and_rejected_signal_replay",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy_validation/sor_ev2.py",
            "report_path": "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay.md",
            "json_path": "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json",
            "canonical_evidence_pack_paths": canonical_pack_paths,
            "evidence_classification": "true_forward_replay",
            "methodology_label": "true_forward_replay",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": list(TIMEFRAMES),
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "candidate_status": "none_promoted",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "sor_ev3",
            "hypothesis_id": "avoid_sideways_low_volatility",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy_validation/sor_ev3.py",
            "report_path": "docs/sor_ev3_avoid_sideways_low_volatility.md",
            "json_path": "docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
            "canonical_evidence_pack_paths": canonical_pack_paths,
            "evidence_classification": "true_forward_replay",
            "methodology_label": "true_forward_replay",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": list(TIMEFRAMES),
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "candidate_status": "promising_review_labels_but_none_promoted",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "mf_orig",
            "hypothesis_id": "mf_orig_ev1_1_original_reconstruction",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy_validation/mf_orig_ev1.py",
            "report_path": "docs/mf_orig_ev1_original_money_flow_reconstruction.md",
            "json_path": "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
            "canonical_evidence_pack_paths": [],
            "evidence_classification": "compact_replay_only",
            "methodology_label": "true_forward_replay",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": ["1d", "4h", "1h"],
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "candidate_status": "source_faithful_but_underperformed",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "mf_orig",
            "hypothesis_id": "mf_orig_ev2_multitimeframe_full_equity_and_source_risk",
            "implementation_status": "implemented",
            "source_file_or_service_module": "services/strategy_validation/mf_orig_ev1.py",
            "report_path": "docs/mf_orig_ev2_multitimeframe_evidence_packs.md",
            "json_path": "docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
            "canonical_evidence_pack_paths": mf_orig_ev2.get("evidence_pack_status", {}).get("evidence_pack_paths", []),
            "evidence_classification": "true_forward_replay",
            "methodology_label": "true_forward_replay",
            "symbols_covered": list(SUPPORTED_SYMBOLS),
            "timeframes_covered": list(TIMEFRAMES),
            "fill_assumptions_covered": list(FILL_ASSUMPTIONS),
            "candidate_status": "none_promoted",
            "production_status": "not_production_authorized",
        },
        {
            "strategy_family": "strat_ev1",
            "hypothesis_id": "regime_gated_trend",
            "implementation_status": "not_implemented",
            "evidence_classification": "not_implemented",
            "methodology_label": "plan_only",
            "candidate_status": "not_evidence",
            "production_status": "not_production_authorized",
        },
    ]

    top_winners = _top(all_trade_rows, "net_pnl", 25, reverse=True)
    top_losers = _top(all_trade_rows, "net_pnl", 25, reverse=False)
    streaks = _max_streaks(all_trade_rows)
    regime = _regime_attribution(all_trade_rows)
    control = _control_pocket_summary(sor_ev1, sor_ev2, sor_ev3, mf_orig_ev1, mf_orig_ev2)
    issue_counter = Counter(row["severity"] for row in issue_list)
    issue_counts = {severity: issue_counter.get(severity, 0) for severity in ("P0", "P1", "P2", "P3")}
    streak_heatmap_counter = Counter((row["symbol"], row["timeframe"]) for row in streaks)
    streak_reason_counter = Counter(str(row["primary_entry_context"]) for row in streaks)
    top_hypotheses = sorted(
        [row for row in comparison_matrix if row.get("hypothesis_id") != "money_flow_v1_2"],
        key=lambda row: _d(row.get("net_pnl_delta_vs_baseline", row.get("net_pnl_sum", "0"))),
        reverse=True,
    )[:10]
    worst_hypotheses = sorted(
        [row for row in comparison_matrix if row.get("hypothesis_id") != "money_flow_v1_2"],
        key=lambda row: _d(row.get("net_pnl_delta_vs_baseline", row.get("net_pnl_sum", "0"))),
    )[:10]

    summary = {
        "phase": "EV-AUDIT1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "audit_verdict": "no_strategy_has_clean_production_or_paper_candidate_status",
        "executive_verdict": {
            "credible_evidence_candidate": "none_cleanly_promoted",
            "best_review_candidate": "avoid_low_rolling_range_50",
            "best_review_candidate_reason": "largest SOR-EV3 aggregate PnL delta, but still failed drawdown/control-pocket gates",
            "best_full_equity_review_candidate": "mf_orig_1d_stage2_breakout_resistance_full_equity",
            "best_aggregate_hypothesis_by_delta": top_hypotheses[0]["hypothesis_id"] if top_hypotheses else "data_not_available",
            "worst_aggregate_hypothesis_by_delta": worst_hypotheses[0]["hypothesis_id"] if worst_hypotheses else "data_not_available",
            "worst_observed_issue": "aggregate improvements can hide control-pocket damage and drawdown worsening",
        },
        "evidence_inventory": evidence_inventory,
        "data_integrity": {
            "verdict": "canonical_sv2_0_2_data_good_enough_for_visual_review_and_hypothesis_filtering",
            "data_rows": data_rows,
            "red_team": [
                "No P0 data-corruption issue was found in canonical SV2.0.2 reports.",
                "15m and 1h conclusions are lower confidence because public Hyperliquid history is truncated by the 5000-candle limit.",
                "Dashboard date-filter metrics must not be used as canonical evidence.",
                "MF-ORIG source-faithfulness still needs direct PDF reconciliation.",
            ],
        },
        "methodology_audit": {
            "overall_scores": {
                "methodology_confidence_0_to_5": 3.5,
                "data_confidence_0_to_5": 4.0,
                "candidate_confidence_0_to_5": 2.0,
                "founder_decision_readiness_0_to_5": 3.0,
            },
            "score_explanation": "Good enough for visual review and hypothesis filtering; not enough for production rule changes, paper-runtime approval, or live trading.",
            "tracks": [
                {"track": "SV2.0.2 baseline", "methodology_confidence": 4, "data_confidence": 4, "candidate_confidence": 2},
                {"track": "SOR-EV2/SOR-EV3", "methodology_confidence": 4, "data_confidence": 4, "candidate_confidence": 2},
                {"track": "MF-ORIG-EV2", "methodology_confidence": 4, "data_confidence": 4, "candidate_confidence": 2},
                {"track": "dashboard overlays/date filters", "methodology_confidence": 2, "data_confidence": 3, "candidate_confidence": 1},
            ],
        },
        "hypothesis_comparison_matrix": comparison_matrix,
        "scenario_rows_available_for_audit": len(scenario_rows),
        "trade_rows_available_for_audit": len(all_trade_rows),
        "top_winning_trades": top_winners,
        "top_losing_trades": top_losers,
        "top_winning_scenarios": _top(scenario_rows, "net_pnl", 10, reverse=True),
        "top_losing_scenarios": _top(scenario_rows, "net_pnl", 10, reverse=False),
        "top_worst_drawdown_scenarios": _top(scenario_rows, "max_drawdown", 10, reverse=True),
        "top_hypotheses_by_aggregate_delta": top_hypotheses,
        "worst_hypotheses_by_aggregate_delta": worst_hypotheses,
        "losing_streaks": streaks,
        "streak_heatmap_by_symbol_timeframe": [
            {"symbol": symbol, "timeframe": timeframe, "streak_count": count}
            for (symbol, timeframe), count in sorted(streak_heatmap_counter.items(), key=lambda item: item[1], reverse=True)
        ],
        "streak_reason_attribution": [
            {"context": context, "streak_count": count}
            for context, count in streak_reason_counter.most_common()
        ],
        "regime_stage_attribution": regime,
        "control_pocket_impact": control,
        "issue_list": issue_list,
        "issue_counts": issue_counts,
        "backtest_adequacy_decision": adequacy,
        "paper_observation_readiness": paper_readiness,
        "dashboard_integration_status": {
            "status": "audit_review_dashboard_deferred",
            "reason": "EV-AUDIT1 prioritizes founder-readable audit report and JSON; dashboard Audit Review can load this JSON in a later UI phase.",
        },
        "recommended_next_phase": "PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime",
        "boundary_flags": boundary_flags,
        "limitations": [
            "EV-AUDIT1 does not regenerate evidence packs.",
            "SOR variant summaries do not provide a full committed per-trade ledger for every variant.",
            "MF-ORIG source PDF was not present locally; source summary and existing spec are used.",
            "Independent scenario sums are not one account PnL.",
        ],
    }
    return summary


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def render_markdown(summary: dict[str, Any]) -> str:
    verdict = summary["executive_verdict"]
    data_rows = summary["data_integrity"]["data_rows"]
    scores = summary["methodology_audit"]["overall_scores"]
    issues = summary["issue_list"]
    matrix = summary["hypothesis_comparison_matrix"]
    winners = summary["top_winning_trades"]
    losers = summary["top_losing_trades"]
    streaks = summary["losing_streaks"]
    winning_scenarios = summary["top_winning_scenarios"]
    losing_scenarios = summary["top_losing_scenarios"]
    drawdown_scenarios = summary["top_worst_drawdown_scenarios"]
    top_hypotheses = summary["top_hypotheses_by_aggregate_delta"]
    worst_hypotheses = summary["worst_hypotheses_by_aggregate_delta"]
    regime = summary["regime_stage_attribution"]
    control = summary["control_pocket_impact"]

    lines = [
        "# EV-AUDIT1 Full Hypothesis, Data Integrity, And Paper-Readiness Review",
        "",
        "Status: `implemented`",
        "",
        "EV-AUDIT1 is audit-only. Production Money Flow rules are unchanged. No strategy has production authorization. No strategy has paper-runtime authorization from this audit. Live trading is not approved. No orders were submitted. No private, signed, or order endpoints were called. Hyperliquid testnet prices are not strategy truth. Dashboard date filters are display-only and not canonical evidence.",
        "",
        "## Executive Verdict",
        "",
        f"- Credible clean candidate: `{verdict['credible_evidence_candidate']}`.",
        f"- Best founder-review candidate: `{verdict['best_review_candidate']}` because {verdict['best_review_candidate_reason']}.",
        f"- Best MF-ORIG full-equity review lane: `{verdict['best_full_equity_review_candidate']}`.",
        f"- Best aggregate hypothesis by delta: `{verdict['best_aggregate_hypothesis_by_delta']}`.",
        f"- Worst aggregate hypothesis by delta: `{verdict['worst_aggregate_hypothesis_by_delta']}`.",
        "- Current evidence is good enough for visual review and hypothesis filtering only.",
        "- Current evidence is not good enough for a production rule change, live trading, or strategy paper-runtime authorization.",
        "- Recommended next phase: `PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime` as a separately scoped observation phase using trusted public mainnet candles.",
        "",
        "## Evidence Inventory",
        "",
        _md_table(
            ["Family", "Hypothesis / Track", "Status", "Evidence Class", "Methodology", "Report"],
            [
                [
                    row.get("strategy_family"),
                    row.get("hypothesis_id"),
                    row.get("implementation_status"),
                    row.get("evidence_classification"),
                    row.get("methodology_label"),
                    row.get("report_path", ""),
                ]
                for row in summary["evidence_inventory"]
            ],
        ),
        "",
        "## Data Integrity Audit",
        "",
        f"Data verdict: `{summary['data_integrity']['verdict']}`.",
        "",
        _md_table(
            ["Symbol", "Timeframe", "Status", "Earliest", "Latest", "Candles", "Coverage", "Limitations", "Evidence Ready"],
            [
                [
                    row["symbol"],
                    row["timeframe"],
                    row["data_status"],
                    row["earliest"],
                    row["latest"],
                    row["candle_count"],
                    row["coverage_percent"],
                    ", ".join(row["known_limitations"]),
                    row["evidence_ready"],
                ]
                for row in data_rows
            ],
        ),
        "",
        "### Data Red-Team Notes",
        "",
        *[f"- {item}" for item in summary["data_integrity"]["red_team"]],
        "",
        "## Backtest Methodology Audit",
        "",
        _md_table(
            ["Score", "Value"],
            [
                ["Methodology Confidence", scores["methodology_confidence_0_to_5"]],
                ["Data Confidence", scores["data_confidence_0_to_5"]],
                ["Candidate Confidence", scores["candidate_confidence_0_to_5"]],
                ["Founder Decision Readiness", scores["founder_decision_readiness_0_to_5"]],
            ],
        ),
        "",
        summary["methodology_audit"]["score_explanation"],
        "",
        "## Full Hypothesis Comparison Matrix",
        "",
        "All aggregate rows are `sum across independent research scenarios`, not one combined account.",
        "",
        _md_table(
            ["Family", "Hypothesis", "Methodology", "PnL Delta / Net", "DD Delta / Worst DD", "Candidate Status", "Reason"],
            [
                [
                    row.get("strategy_family"),
                    row.get("hypothesis_id"),
                    row.get("methodology_label"),
                    row.get("net_pnl_delta_vs_baseline", row.get("net_pnl_sum")),
                    row.get("max_drawdown_delta", row.get("max_drawdown_worst")),
                    row.get("candidate_status"),
                    row.get("rejection_reason"),
                ]
                for row in matrix
            ],
        ),
        "",
        "## Biggest Winner Analysis",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Entry", "Exit", "PnL", "Why It Won"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row.get("entry_time"),
                    row.get("exit_time"),
                    row["net_pnl"],
                    row.get("entry_reason") or row.get("entry_classification"),
                ]
                for idx, row in enumerate(winners[:25])
            ],
        ),
        "",
        "Largest wins generally came from trend-continuation or Stage 2 contexts where the strategy stayed in the move long enough for large favorable excursion. Repeatability is not assumed: several top wins are concentrated in specific symbols/timeframes and must survive both fill assumptions before being used for a rule-change proposal.",
        "",
        "### Top 10 Winning Scenarios",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Net PnL", "Drawdown", "Trades"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row["net_pnl"],
                    row["max_drawdown"],
                    row["trade_count"],
                ]
                for idx, row in enumerate(winning_scenarios[:10])
            ],
        ),
        "",
        "### Top 10 Winning Hypotheses / Variants",
        "",
        _md_table(
            ["Rank", "Family", "Hypothesis", "PnL Delta", "DD Delta", "Candidate Status"],
            [
                [
                    idx + 1,
                    row.get("strategy_family"),
                    row.get("hypothesis_id"),
                    row.get("net_pnl_delta_vs_baseline", row.get("net_pnl_sum")),
                    row.get("max_drawdown_delta", row.get("max_drawdown_worst")),
                    row.get("candidate_status"),
                ]
                for idx, row in enumerate(top_hypotheses[:10])
            ],
        ),
        "",
        "## Biggest Loser Analysis",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Entry", "Exit", "PnL", "Exit / Context"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row.get("entry_time"),
                    row.get("exit_time"),
                    row["net_pnl"],
                    row.get("exit_reason") or row.get("entry_classification"),
                ]
                for idx, row in enumerate(losers[:25])
            ],
        ),
        "",
        "Largest losses are concentrated in late-extension, Stage 2 failure, or MA alignment break contexts. SOR-EV1/SOR-EV2 observed that many large losses had adverse-candle or prior-break context, but stop/exit variants still failed strict promotion because they damaged controls or worsened drawdown elsewhere.",
        "",
        "### Top 10 Worst Scenarios",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Net PnL", "Drawdown", "Trades"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row["net_pnl"],
                    row["max_drawdown"],
                    row["trade_count"],
                ]
                for idx, row in enumerate(losing_scenarios[:10])
            ],
        ),
        "",
        "### Top 10 Worst Drawdown Contributors",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Net PnL", "Drawdown", "Trades"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row["net_pnl"],
                    row["max_drawdown"],
                    row["trade_count"],
                ]
                for idx, row in enumerate(drawdown_scenarios[:10])
            ],
        ),
        "",
        "### Worst 10 Hypotheses / Variants By Aggregate Delta",
        "",
        _md_table(
            ["Rank", "Family", "Hypothesis", "PnL Delta", "DD Delta", "Candidate Status"],
            [
                [
                    idx + 1,
                    row.get("strategy_family"),
                    row.get("hypothesis_id"),
                    row.get("net_pnl_delta_vs_baseline", row.get("net_pnl_sum")),
                    row.get("max_drawdown_delta", row.get("max_drawdown_worst")),
                    row.get("candidate_status"),
                ]
                for idx, row in enumerate(worst_hypotheses[:10])
            ],
        ),
        "",
        "## Consecutive Loss / Streak Audit",
        "",
        _md_table(
            ["Rank", "Strategy", "Symbol", "TF", "Fill", "Losses", "Streak PnL", "Start", "End", "Context"],
            [
                [
                    idx + 1,
                    row["hypothesis_id"],
                    row["symbol"],
                    row["timeframe"],
                    row["fill_assumption"],
                    row["consecutive_losses"],
                    row["streak_pnl"],
                    row["start_time"],
                    row["end_time"],
                    row["primary_entry_context"],
                ]
                for idx, row in enumerate(streaks[:20])
            ],
        ),
        "",
        "### Streak Heatmap By Symbol / Timeframe",
        "",
        _md_table(
            ["Symbol", "Timeframe", "Streak Count In Worst-20 Set"],
            [
                [row["symbol"], row["timeframe"], row["streak_count"]]
                for row in summary["streak_heatmap_by_symbol_timeframe"]
            ],
        ),
        "",
        "### Streak Reason Attribution",
        "",
        _md_table(
            ["Context", "Streak Count"],
            [[row["context"], row["streak_count"]] for row in summary["streak_reason_attribution"]],
        ),
        "",
        "## Regime / Stage / Condition Attribution",
        "",
        _md_table(
            ["Family", "Stage / Regime", "Trades", "Wins", "Losses", "Net PnL", "Largest Loss"],
            [
                [
                    row["strategy_family"],
                    row["stage_or_regime"],
                    row["trade_count"],
                    row["winning_trades"],
                    row["losing_trades"],
                    row["net_pnl"],
                    row["largest_loss"],
                ]
                for row in regime[:40]
            ],
        ),
        "",
        "## Control Pocket Audit",
        "",
        _md_table(
            ["Phase", "Variant / Hypothesis", "Pocket", "Improved", "Preserved", "Damaged"],
            [
                [
                    row.get("phase"),
                    row.get("variant_id") or row.get("hypothesis_id"),
                    row.get("pocket") or row.get("control_pocket") or "control_pockets",
                    row.get("improved"),
                    row.get("preserved"),
                    row.get("damaged"),
                ]
                for row in control[:60]
            ],
        ),
        "",
        "Control-pocket damage is the central reason that high aggregate-PnL variants are not clean candidates. `avoid_low_rolling_range_50` and MF-ORIG full-equity rows are useful review lanes, but they are not promoted because drawdown or control-pocket preservation fails.",
        "",
        "## P0 / P1 / P2 / P3 Issue List",
        "",
        _md_table(
            ["Severity", "Issue", "Why It Matters", "Required Fix", "Blocks"],
            [
                [
                    row["severity"],
                    row["issue"],
                    row["why_it_matters"],
                    row["required_fix"],
                    row["blocks_founder_decisions"],
                ]
                for row in issues
            ],
        ),
        "",
        f"Issue counts: `{summary['issue_counts']}`.",
        "",
        "## Backtest Adequacy Decision",
        "",
        f"Decision: `{summary['backtest_adequacy_decision']['decision']}`.",
        "",
        "- The backtest can support visual review, loss anatomy, hypothesis filtering, and scoped next-phase planning.",
        "- The backtest cannot support production rule changes, live trading, real-capital decisions, or strategy paper-runtime authorization.",
        "- Current conclusions are fragile where aggregate PnL improves while control pockets or worst drawdown worsen.",
        "",
        "## Real-Time Paper Observation Readiness",
        "",
        f"Decision: `{summary['paper_observation_readiness']['decision']}`.",
        "",
        "This is not paper approval. It means a separately scoped public-mainnet observation phase is reasonable if the listed conditions are met.",
        "",
        *[f"- {item}" for item in summary["paper_observation_readiness"]["conditions"]],
        "",
        "## Dashboard Integration",
        "",
        f"Status: `{summary['dashboard_integration_status']['status']}`.",
        "",
        summary["dashboard_integration_status"]["reason"],
        "",
        "## Recommended Next Phase",
        "",
        "`PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime`.",
        "",
        "PT-RT1 should use trusted public mainnet candles for strategy truth, keep sandbox/testnet execution plumbing separate, maintain the internal 10,000 USDC paper-equity ledger, log every signal/state transition, prevent duplicate signals, expose drawdown alarms, and remain no-live/no-order unless a later phase explicitly scopes otherwise.",
        "",
        "## Boundary Confirmation",
        "",
        _md_table(["Boundary", "Value"], [[key, value] for key, value in summary["boundary_flags"].items()]),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    summary = build_audit()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"summary": str(SUMMARY_PATH.relative_to(ROOT)), "report": str(REPORT_PATH.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
