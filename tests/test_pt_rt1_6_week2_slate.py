from __future__ import annotations

from services.paper_runtime.pt_rt1 import (
    PT_RT1_4_DISABLED_TIMEFRAMES,
    PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT1_6_ACTIVE_STRATEGY_LANES,
    PT_RT1_6_ACTIVE_TIMEFRAMES,
    PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS,
    PT_RT1_6_ARCHIVED_STRATEGY_LANES,
    build_pt_rt1_summary,
    pt_rt1_6_lane_testnet_eligible,
)


ACTIVE_WEEK2_LANES = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
)
ARCHIVED_WEEK2_LANES = (
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
)


def test_pt_rt1_6_active_and_archived_lane_sets_are_exact() -> None:
    assert PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS == ACTIVE_WEEK2_LANES
    assert tuple(lane.lane_id for lane in PT_RT1_6_ACTIVE_STRATEGY_LANES) == ACTIVE_WEEK2_LANES
    assert PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS == ARCHIVED_WEEK2_LANES
    assert tuple(lane.lane_id for lane in PT_RT1_6_ARCHIVED_STRATEGY_LANES) == ARCHIVED_WEEK2_LANES


def test_pt_rt1_6_timeframe_policy_keeps_15m_paused() -> None:
    assert PT_RT1_6_ACTIVE_TIMEFRAMES == ("1h", "4h", "1d")
    assert "15m" not in PT_RT1_6_ACTIVE_TIMEFRAMES
    assert PT_RT1_4_DISABLED_TIMEFRAMES == ("15m",)


def test_pt_rt1_6_only_baseline_is_testnet_eligible() -> None:
    assert [lane_id for lane_id in ACTIVE_WEEK2_LANES if pt_rt1_6_lane_testnet_eligible(lane_id)] == [
        "money_flow_v1_2_baseline"
    ]
    assert pt_rt1_6_lane_testnet_eligible("avoid_low_rolling_range_20") is False
    assert pt_rt1_6_lane_testnet_eligible("mf_orig_1d_stage2_breakout_resistance_full_equity") is False
    for lane_id in ARCHIVED_WEEK2_LANES:
        assert pt_rt1_6_lane_testnet_eligible(lane_id) is False


def test_pt_rt1_6_summary_exposes_active_archived_and_boundaries() -> None:
    summary = build_pt_rt1_summary()
    active_rows = summary["active_strategy_lanes"]
    archived_rows = summary["archived_strategy_lanes"]

    assert [row["lane_id"] for row in active_rows] == list(ACTIVE_WEEK2_LANES)
    assert [row["lane_id"] for row in archived_rows] == list(ARCHIVED_WEEK2_LANES)
    assert summary["dashboard_status"]["strategy_lanes_visible"] == 3
    assert summary["dashboard_status"]["historical_strategy_lanes_available"] == 10
    assert summary["dashboard_status"]["default_archived_lanes_hidden_from_active_scoreboard"] is True
    assert summary["pt_rt1_6_week2_active_scope"]["runtime_started_by_pt_rt1_6"] is False

    rows_by_id = {row["lane_id"]: row for row in [*active_rows, *archived_rows]}
    assert rows_by_id["money_flow_v1_2_baseline"]["testnet_eligible"] is True
    assert rows_by_id["avoid_low_rolling_range_20"]["testnet_eligible"] is False
    assert rows_by_id["mf_orig_1d_stage2_breakout_resistance_full_equity"]["testnet_eligible"] is False
    assert all(row["production_approved"] is False for row in rows_by_id.values())
    assert all(row["live_approved"] is False for row in rows_by_id.values())
    assert all(row["pnl_source"] == "Synthetic Ledger" for row in rows_by_id.values())
    assert all(row["signal_truth"] == "Public Mainnet Candles" for row in rows_by_id.values())


def test_pt_rt1_6_dashboard_static_labels_exist() -> None:
    js = open("apps/dashboard/evidence-dashboard.js", encoding="utf-8").read()
    html = open("apps/dashboard/index.html", encoding="utf-8").read()

    assert "PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS" in js
    assert "money_flow_v1_2_baseline" in js
    assert "avoid_low_rolling_range_20" in js
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" in js
    assert "Control / Baseline" in js
    assert "Diagnostic Comparator" in js
    assert "MF-ORIG Source-Faithful Candidate" in js
    assert "Synthetic Ledger" in js
    assert "Testnet lifecycle" in js
    assert "Separate from synthetic PnL" in js
    assert "pt_rt1_6_week2_active" in html
    assert "Week 2 active founder-selected slate" in html
