from __future__ import annotations

import json
from pathlib import Path


SUMMARY_PATH = Path("docs/mf_orig_ev2_multitimeframe_evidence_summary.json")
REPORT_PATH = Path("docs/mf_orig_ev2_multitimeframe_evidence_packs.md")
EXPECTED_SYMBOLS = {"BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX"}
EXPECTED_TIMEFRAMES = {"15m", "1h", "4h", "1d"}
EXPECTED_FILLS = {"next_candle_open", "next_candle_close"}
EXPECTED_HYPOTHESES = {
    "mf_orig_1d_stage2_5_20_crossover",
    "mf_orig_1d_stage2_breakout_resistance",
    "mf_orig_stage2_pullback_reclaim",
    "mf_orig_stage_filter_only",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_stage_filter_only_full_equity",
}


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_mf_orig_ev2_report_and_summary_exist() -> None:
    assert REPORT_PATH.exists()
    assert SUMMARY_PATH.exists()
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "MF-ORIG-EV2 is evidence-only" in report
    assert "Production Money Flow v1.2 remains unchanged" in report
    assert "No orders were submitted" in report
    assert "display-only recalculations" in report


def test_mf_orig_ev2_full_grid_is_present() -> None:
    payload = _summary()
    rows = payload["replay_results"]
    assert payload["phase"] == "MF-ORIG-EV2"
    assert {row["hypothesis_id"] for row in rows} == EXPECTED_HYPOTHESES
    assert {row["symbol"] for row in rows} == EXPECTED_SYMBOLS
    assert {row["timeframe"] for row in rows} == EXPECTED_TIMEFRAMES
    assert {row["fill_timing"] for row in rows} == EXPECTED_FILLS
    assert len(rows) == 8 * 9 * 4 * 2
    assert payload["ev2_scope"]["scenario_count_expected"] == 576
    assert set(payload["ev2_scope"]["sizing_modes"]) == {"source_1pct_risk", "full_equity_notional"}
    assert len(payload["ev2_scope"]["source_1pct_risk_hypotheses"]) == 4
    assert len(payload["ev2_scope"]["full_equity_notional_hypotheses"]) == 4
    assert {row["sizing_mode"] for row in rows} == {"source_1pct_risk", "full_equity_notional"}


def test_mf_orig_ev2_timeframe_roles_are_truthfully_labeled() -> None:
    payload = _summary()
    policy = payload["timeframe_interpretation"]
    assert policy["1d"] == "source_primary_original_money_flow_timeframe"
    assert policy["4h"] == "swing_fractal_adaptation"
    assert policy["1h"] == "intraday_fractal_adaptation"
    assert policy["15m"] == "stress_test_short_term_fractal_adaptation_not_source_primary"
    assert all(
        row["timeframe_role"] == policy[row["timeframe"]]
        for row in payload["replay_results"]
    )


def test_mf_orig_ev2_accounting_and_drawdown_invariants_are_preserved() -> None:
    payload = _summary()
    accounting = payload["accounting_invariant_summary"]
    assert payload["accounting_convention"]["model"] == "event_ledger_accounting"
    assert payload["accounting_convention"]["drawdown_method"] == "peak_to_trough"
    assert accounting["status"] == "passed"
    assert accounting["equity_delta_violations"] == 0
    assert accounting["fee_sum_violations"] == 0
    assert accounting["remaining_quantity_violations"] == 0
    assert accounting["entry_fee_event_violations"] == 0
    assert all(row["drawdown_method"] == "peak_to_trough" for row in payload["replay_results"])
    assert all(row["initial_equity"] == "10000" for row in payload["replay_results"])


def test_mf_orig_ev2_evidence_packs_and_baseline_comparison_are_recorded() -> None:
    payload = _summary()
    assert payload["baseline_parity_summary"]["status_counts"] == {"baseline_parity_passed": 72}
    assert payload["evidence_pack_status"]["status"] == "generated"
    assert payload["evidence_pack_status"]["pack_count"] == 288
    assert len(payload["evidence_pack_status"]["evidence_pack_paths"]) == 288
    assert all("mf_orig_ev2_" in path for path in payload["evidence_pack_status"]["evidence_pack_paths"])
    assert payload["baseline_delta_summary"]["comparison_baseline"] == "Money Flow v1.2 canonical SV2.0.2 evidence"
    assert payload["baseline_delta_summary"]["not_one_account_pnl"] is True


def test_mf_orig_ev2_candidate_gate_has_no_production_approval() -> None:
    payload = _summary()
    statuses = {row["hypothesis_id"]: row["status"] for row in payload["candidate_status"]}
    assert set(statuses) == EXPECTED_HYPOTHESES
    assert "candidate_for_more_evidence" not in set(statuses.values())
    assert all(row["production_approved"] is False for row in payload["candidate_status"])
    assert payload["boundary_flags"]["changes_production_money_flow_rules"] is False
    assert payload["boundary_flags"]["approves_original_strategy_for_production"] is False
    assert payload["boundary_flags"]["submits_orders"] is False
    assert payload["boundary_flags"]["calls_private_signed_or_order_endpoints"] is False
    assert payload["boundary_flags"]["uses_hyperliquid_testnet_prices"] is False


def test_mf_orig_ev2_dashboard_hooks_are_present() -> None:
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    dashboard = _summary()["dashboard_integration_status"]
    chart_files = dashboard["chart_data_files"]
    assert "MF_ORIG_EV2_DASHBOARD_CHART_FILES" in js
    assert "mf_orig_ev2_dashboard_chart_data" in js
    assert "mf_orig_ev2_multitimeframe_evidence_summary.json" in js
    assert "date filters are display-only, not canonical pack regeneration" in js
    assert dashboard["historical_replay"] == "implemented"
    assert dashboard["evidence_ui"] == "implemented"
    assert len(chart_files) == 36 + (8 * 9 * 4 * 2)
    assert sum("/selected/" in path for path in chart_files) == 8 * 9 * 4 * 2
    assert any("full_equity" in path for path in chart_files)
    assert "mf_orig_stage2_5_20_crossover" in SUMMARY_PATH.read_text(encoding="utf-8")
    assert "mf_orig_stage2_5_20_crossover_full_equity" in SUMMARY_PATH.read_text(encoding="utf-8")


def test_mf_orig_ev2_no_forbidden_approval_language() -> None:
    combined = REPORT_PATH.read_text(encoding="utf-8") + SUMMARY_PATH.read_text(encoding="utf-8")
    lowered = combined.lower()
    forbidden = [
        "proven",
        "optimal",
        "approved_for_live",
        "approved_for_paper",
        "ready_for_real_capital",
        "production-approved",
    ]
    assert not any(term in lowered for term in forbidden)
