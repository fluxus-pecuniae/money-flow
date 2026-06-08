from __future__ import annotations

import json
from pathlib import Path


REPORT = Path("docs/pt_rt1_6_2_week2_operating_review.md")
SUMMARY = Path("docs/pt_rt1_6_2_week2_operating_review_summary.json")
ACTIVE_LANES = [
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
]


def summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def test_pt_rt1_6_2_report_and_summary_exist() -> None:
    assert REPORT.exists()
    assert SUMMARY.exists()
    report = REPORT.read_text(encoding="utf-8")
    assert "Week 2 paper observation may continue unchanged" in report
    assert "No live trading was approved" in report
    assert "No strategy was production-approved" in report


def test_pt_rt1_6_2_runtime_scope_and_lane_boundaries() -> None:
    data = summary()
    assert data["active_runtime_scope"] == "pt_rt1_6_week2_active"
    assert data["active_lanes"] == ACTIVE_LANES
    assert data["archived_lane_count"] == 7
    assert data["active_timeframes"] == ["1h", "4h", "1d"]
    assert data["disabled_timeframes"] == ["15m"]
    assert data["decision_summary"]["fifteen_minute_rows"] == 0
    assert data["decision_summary"]["lane_counts"] == {lane: 352 for lane in ACTIVE_LANES}


def test_pt_rt1_6_2_testnet_boundaries() -> None:
    data = summary()
    testnet = data["testnet_lifecycle_summary"]
    assert testnet["trigger_lanes"] == {"money_flow_v1_2_baseline": 33}
    assert testnet["candidate_lane_trigger_count"] == 0
    assert testnet["unknown_open_state_count"] == 0
    assert testnet["testnet_pnl_update_count"] == 0
    assert set(testnet["blocked_reason_codes"]) == {
        "testnet_order_precision_missing",
        "testnet_metadata_unavailable",
    }


def test_pt_rt1_6_2_no_live_or_production_approval() -> None:
    data = summary()
    boundaries = data["boundaries"]
    assert boundaries["public_mainnet_data_is_strategy_truth"] is True
    assert boundaries["synthetic_ledger_is_pnl_truth"] is True
    assert boundaries["testnet_lifecycle_separate_from_synthetic_trades"] is True
    assert boundaries["testnet_fills_update_synthetic_pnl"] is False
    assert boundaries["candidate_lanes_testnet_eligible"] is False
    assert boundaries["baseline_only_testnet_transport"] is True
    assert boundaries["fifteen_minute_active_scoring"] is False
    assert boundaries["live_trading_approved"] is False
    assert boundaries["production_strategy_approved"] is False
