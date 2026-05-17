from __future__ import annotations

import json
from pathlib import Path


SUMMARY_PATH = Path("docs/pt_rt_week1_day_summary.json")
REPORT_PATH = Path("docs/pt_rt_week1_day_summary.md")


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_pt_rt1_4_1_daily_review_pack_exists() -> None:
    assert REPORT_PATH.exists()
    assert SUMMARY_PATH.exists()

    report = REPORT_PATH.read_text(encoding="utf-8")
    summary = _summary()

    assert summary["phase"] == "PT-RT1.4.1"
    assert "PT-RT1.4.1 verifies the active Week 1 runtime cutover" in report
    assert "24h / daily observation only" in report
    assert "not evidence of edge" in report
    assert "not production approval" in report
    assert "synthetic paper only" in report


def test_pt_rt1_4_1_cutover_verification_is_reported() -> None:
    cutover = _summary()["cutover_verification"]

    assert cutover["active_timeframes"] == ["1h", "4h", "1d"]
    assert cutover["disabled_timeframes"][0]["timeframe"] == "15m"
    assert cutover["disabled_timeframes"][0]["status"] == "disabled_for_week1_noise_reduction"
    assert cutover["all_active_scoreboard_excludes_15m"] is True
    assert cutover["legacy_15m_rows_visible"] is True
    assert cutover["legacy_15m_rows_excluded_from_active_score"] is True
    assert cutover["retired_runtime_cutover_not_applied"] is True
    assert cutover["retired_runtime_new_15m_entries_after_cutover"] > 0
    assert cutover["active_runtime_new_15m_entries_after_restart"] == 0
    assert cutover["active_runtime_15m_rows_after_restart"] == 0
    assert cutover["new_15m_entries_after_cutover"] == 0
    assert cutover["verification_status"] == "active_runtime_cutover_verified_after_restart"


def test_pt_rt1_4_1_lane_metrics_are_active_timeframe_scoped() -> None:
    summary = _summary()
    lanes = summary["lane_review"]

    assert len(lanes) == 10
    assert {row["starting_equity"] for row in lanes} == {"10000"}
    assert all("total_equity" in row for row in lanes)
    assert all("open_positions" in row for row in lanes)
    assert all("closed_trades" in row for row in lanes)
    assert all("data_health_blocks" in row for row in lanes)
    assert all("duplicate_blocks" in row for row in lanes)
    assert any(row["status"] == "active_timeframe_observed" for row in lanes)
    assert summary["daily_observation_summary"]["top_lane_by_total_synthetic_equity"]["lane_id"]
    assert summary["daily_observation_summary"]["worst_lane_by_total_synthetic_equity"]["lane_id"]


def test_pt_rt1_4_1_timeframe_open_closed_and_decision_reviews_exist() -> None:
    summary = _summary()
    timeframe_by_id = {row["timeframe"]: row for row in summary["timeframe_review"]}

    assert set(timeframe_by_id) == {"1h", "4h", "1d", "15m"}
    assert timeframe_by_id["1h"]["status"] == "active_week_timeframe"
    assert timeframe_by_id["4h"]["status"] == "active_week_timeframe"
    assert timeframe_by_id["1d"]["status"] == "active_week_timeframe"
    assert timeframe_by_id["15m"]["status"] == "paused_legacy_not_active_score"
    assert timeframe_by_id["15m"]["net_pnl"] == "legacy_not_active_score"
    assert summary["open_position_review"]["active_positions_count"] >= 0
    assert summary["open_position_review"]["legacy_15m_positions_count"] >= 0
    assert "summary_cards" in summary["closed_trade_review"]
    assert "action_counts" in summary["decision_review"]
    assert "top_reason_codes" in summary["decision_review"]
    assert "paper decision" in summary["decision_review"]["labels"]
    assert "synthetic entry" in summary["decision_review"]["labels"]
    assert "not exchange order" in summary["decision_review"]["labels"]


def test_pt_rt1_4_1_testnet_boundaries_and_go_decision() -> None:
    summary = _summary()
    boundaries = summary["boundaries"]
    testnet = summary["testnet_label_audit"]

    assert testnet["testnet_order_transport"] == "disabled"
    assert testnet["signed_testnet_orders"] == 0
    assert testnet["strategy_pnl_update_from_testnet"] is False
    assert testnet["live_trading"] == "not approved"
    assert testnet["testnet_probe_label_still_ambiguous"] is False
    assert boundaries["production_money_flow_rules_changed"] is False
    assert boundaries["strategy_production_approved"] is False
    assert boundaries["live_trading_approved"] is False
    assert boundaries["live_orders_submitted"] is False
    assert boundaries["testnet_orders_submitted"] is False
    assert boundaries["testnet_order_transport_enabled"] is False
    assert boundaries["private_signed_order_endpoints_called_from_strategy_truth"] is False
    assert boundaries["historical_evidence_packs_regenerated"] is False
    assert summary["dashboard_qa"]["no_order_controls"] is True
    assert summary["go_no_go"]["decision"] == "Week 1 paper observation may continue"


def test_pt_rt1_4_1_runtime_artifacts_are_ignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    archiveignore = Path(".archiveignore").read_text(encoding="utf-8")

    assert "reports/paper_runtime/" in gitignore
    assert "reports/paper_runtime" in archiveignore
    assert "reports/paper_runtime/**" in archiveignore
