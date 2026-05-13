from __future__ import annotations

import json
from pathlib import Path


SUMMARY_PATH = Path("docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json")
REPORT_PATH = Path("docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review.md")


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_ev_audit1_report_and_summary_exist() -> None:
    assert REPORT_PATH.exists()
    assert SUMMARY_PATH.exists()
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "EV-AUDIT1 is audit-only" in report
    assert "Production Money Flow rules are unchanged" in report
    assert "No orders were submitted" in report
    assert "Dashboard date filters are display-only and not canonical evidence" in report


def test_ev_audit1_inventory_covers_all_required_tracks() -> None:
    payload = _summary()
    inventory = payload["evidence_inventory"]
    ids = {row["hypothesis_id"] for row in inventory}
    families = {row["strategy_family"] for row in inventory}

    assert payload["phase"] == "EV-AUDIT1"
    assert "money_flow_v1_2" in ids
    assert "loss_anatomy_and_completed_trade_overlays" in ids
    assert "true_forward_stop_and_rejected_signal_replay" in ids
    assert "avoid_sideways_low_volatility" in ids
    assert "mf_orig_ev1_1_original_reconstruction" in ids
    assert "mf_orig_ev2_multitimeframe_full_equity_and_source_risk" in ids
    assert "regime_gated_trend" in ids
    assert {"current_money_flow", "sor_ev1", "sor_ev2", "sor_ev3", "mf_orig", "strat_ev1"} <= families
    assert any(row["evidence_classification"] == "canonical_evidence" for row in inventory)
    assert any(row["evidence_classification"] == "completed_trade_overlay_estimate" for row in inventory)
    assert any(row["evidence_classification"] == "compact_replay_only" for row in inventory)
    assert any(row["evidence_classification"] == "not_implemented" for row in inventory)


def test_ev_audit1_data_integrity_and_methodology_scorecard_exist() -> None:
    payload = _summary()
    data_rows = payload["data_integrity"]["data_rows"]
    symbols = {row["symbol"] for row in data_rows}
    timeframes = {row["timeframe"] for row in data_rows}
    scores = payload["methodology_audit"]["overall_scores"]

    assert len(data_rows) == 9 * 4
    assert symbols == {"BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX"}
    assert timeframes == {"15m", "1h", "4h", "1d"}
    assert all(row["evidence_ready"] is True for row in data_rows)
    assert any("hyperliquid_public_5000_candle_limit" in row["known_limitations"] for row in data_rows)
    assert scores["methodology_confidence_0_to_5"] == 3.5
    assert scores["data_confidence_0_to_5"] == 4.0
    assert scores["candidate_confidence_0_to_5"] == 2.0
    assert scores["founder_decision_readiness_0_to_5"] == 3.0


def test_ev_audit1_comparison_winners_losers_streaks_and_regime_sections_exist() -> None:
    payload = _summary()
    matrix_ids = {row["hypothesis_id"] for row in payload["hypothesis_comparison_matrix"]}

    assert "money_flow_v1_2" in matrix_ids
    assert "avoid_low_rolling_range_20" in matrix_ids
    assert "avoid_low_rolling_range_50" in matrix_ids
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" in matrix_ids
    assert payload["executive_verdict"]["credible_evidence_candidate"] == "none_cleanly_promoted"
    assert payload["executive_verdict"]["best_review_candidate"] == "avoid_low_rolling_range_50"
    assert payload["top_winning_trades"]
    assert payload["top_losing_trades"]
    assert payload["top_winning_scenarios"]
    assert payload["top_losing_scenarios"]
    assert payload["top_worst_drawdown_scenarios"]
    assert payload["top_hypotheses_by_aggregate_delta"]
    assert payload["worst_hypotheses_by_aggregate_delta"]
    assert payload["losing_streaks"]
    assert payload["streak_heatmap_by_symbol_timeframe"]
    assert payload["streak_reason_attribution"]
    assert payload["regime_stage_attribution"]
    assert payload["control_pocket_impact"]


def test_ev_audit1_issue_list_backtest_and_paper_readiness_are_clear() -> None:
    payload = _summary()
    issue_counts = payload["issue_counts"]
    adequacy = payload["backtest_adequacy_decision"]
    readiness = payload["paper_observation_readiness"]

    assert issue_counts["P0"] == 0
    assert issue_counts["P1"] >= 1
    assert issue_counts["P2"] >= 1
    assert issue_counts["P3"] >= 1
    assert adequacy["good_enough_for_visual_review"] is True
    assert adequacy["good_enough_for_hypothesis_filtering"] is True
    assert adequacy["not_good_enough_for_production_rule_change"] is True
    assert adequacy["not_good_enough_for_live_or_paper_approval"] is True
    assert readiness["decision"] == "paper_observation_ready_with_conditions"
    assert readiness["not_approval"] is True
    assert readiness["required_next_phase"].startswith("PT-RT1")
    assert payload["dashboard_integration_status"]["status"] == "audit_review_dashboard_deferred"


def test_ev_audit1_boundaries_and_no_forbidden_language() -> None:
    payload = _summary()
    flags = payload["boundary_flags"]
    combined = REPORT_PATH.read_text(encoding="utf-8").lower() + SUMMARY_PATH.read_text(encoding="utf-8").lower()

    assert flags["changes_production_money_flow_rules"] is False
    assert flags["approves_strategy_for_production"] is False
    assert flags["approves_paper_trading"] is False
    assert flags["approves_live_trading"] is False
    assert flags["submits_orders"] is False
    assert flags["calls_private_signed_or_order_endpoints"] is False
    assert flags["uses_hyperliquid_testnet_prices_as_strategy_truth"] is False
    assert flags["uses_dashboard_date_filters_as_canonical_evidence"] is False
    assert flags["regenerates_evidence_packs"] is False
    for forbidden in (
        "proven",
        "optimal",
        "guaranteed",
        "approved for live",
        "approved for production",
        "ready for real capital",
        "production-approved",
    ):
        assert forbidden not in combined


def test_ev_audit1_does_not_modify_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text(encoding="utf-8")
    assert "EV-AUDIT1" not in source
    assert "avoid_low_rolling_range_50" not in source
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" not in source
