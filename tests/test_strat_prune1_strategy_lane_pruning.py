from __future__ import annotations

import json
from pathlib import Path


SUMMARY_PATH = Path("docs/strat_prune1_strategy_lane_pruning_summary.json")
REPORT_PATH = Path("docs/strat_prune1_strategy_lane_pruning.md")
BASELINE = "money_flow_v1_2_baseline"


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_strat_prune1_report_and_summary_exist() -> None:
    assert REPORT_PATH.exists()
    assert SUMMARY_PATH.exists()
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "STRAT-PRUNE1 implements none of those runtime changes" in report
    assert "No strategy is production-approved" in report
    assert "Live trading is not approved" in report


def test_recommended_slate_is_small_active_timeframe_and_synthetic_only() -> None:
    summary = _summary()
    slate = summary["recommended_next_paper_slate"]
    assert BASELINE in slate
    candidate_lanes = [lane for lane in slate if lane != BASELINE]
    assert len(candidate_lanes) <= 4
    assert summary["candidate_lane_count_excluding_baseline"] == len(candidate_lanes)
    assert summary["active_timeframes"] == ["1h", "4h", "1d"]
    assert all(row["timeframe"] != "15m" or row["status"] == "paused" for row in summary["disabled_timeframes"])

    items = {item["lane_id"]: item for item in summary["items"]}
    for lane_id in candidate_lanes:
        assert items[lane_id]["paper_eligible"] is True
        assert items[lane_id]["testnet_eligible"] is False
        assert items[lane_id]["production_eligible"] is False
        assert "candidate_synthetic_only" in items[lane_id]["reason_codes"] or lane_id == "avoid_low_rolling_range_20"


def test_only_baseline_is_testnet_eligible_and_no_lane_is_production_eligible() -> None:
    summary = _summary()
    testnet_eligible = [item["lane_id"] for item in summary["items"] if item["testnet_eligible"]]
    production_eligible = [item["lane_id"] for item in summary["items"] if item["production_eligible"]]
    assert testnet_eligible == [BASELINE]
    assert production_eligible == []
    assert summary["boundary_flags"]["candidate_lanes_testnet_eligible"] is False
    assert summary["boundary_flags"]["implements_new_runtime_lanes"] is False
    assert summary["boundary_flags"]["submits_live_orders"] is False
    assert summary["boundary_flags"]["submits_testnet_orders"] is False


def test_future_add_candidates_are_recommendation_only_not_runtime_lanes() -> None:
    summary = _summary()
    add_candidates = [item for item in summary["items"] if item["recommendation"] == "add_candidate_for_future_phase"]
    assert {item["lane_id"] for item in add_candidates} == {
        "relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34",
        "trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20",
    }
    for item in add_candidates:
        assert item["current_status"] == "research_only_not_runtime"
        assert item["implementation_phase"] == "PT-RT1.6_candidate_recommendation_only"
        assert item["testnet_eligible"] is False
        assert item["production_eligible"] is False


def test_all_existing_pt_rt_lanes_are_classified() -> None:
    summary = _summary()
    classified = {item["lane_id"] for item in summary["items"]}
    existing_lanes = {
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
    assert existing_lanes <= classified
