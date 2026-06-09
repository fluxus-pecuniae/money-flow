"""Consistency test: current_truth.json must equal a fresh export from canonical anchors.

Any hand-edit or anchor drift fails this test, forcing re-export.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.export_current_truth import build_truth
from services.paper_runtime.pt_rt1 import (
    PT_RT1_4_DISABLED_TIMEFRAMES,
    PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT1_6_ACTIVE_TIMEFRAMES,
    PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS,
    pt_rt1_6_lane_testnet_eligible,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TRUTH_PATH = REPO_ROOT / "current_truth.json"


def _load_on_disk() -> dict:
    assert TRUTH_PATH.exists(), (
        f"{TRUTH_PATH} does not exist. Run: python scripts/export_current_truth.py"
    )
    data = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    data.pop("_generated_at_utc", None)
    return data


def _fresh() -> dict:
    data = build_truth()
    data.pop("_generated_at_utc", None)
    return data


def test_on_disk_matches_fresh_export() -> None:
    assert _load_on_disk() == _fresh(), (
        "current_truth.json is out of sync with canonical anchors. "
        "Run: python scripts/export_current_truth.py"
    )


def test_active_lanes_match_anchor() -> None:
    truth = _fresh()
    assert [lane["lane_id"] for lane in truth["active_lanes"]] == list(
        PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS
    )


def test_archived_lanes_match_anchor() -> None:
    truth = _fresh()
    assert [lane["lane_id"] for lane in truth["archived_lanes"]] == list(
        PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS
    )


def test_active_timeframes_match_anchor() -> None:
    truth = _fresh()
    assert truth["active_timeframes"] == list(PT_RT1_6_ACTIVE_TIMEFRAMES)


def test_paused_timeframes_match_anchor() -> None:
    truth = _fresh()
    assert truth["paused_timeframes"] == list(PT_RT1_4_DISABLED_TIMEFRAMES)
    assert "15m" in truth["paused_timeframes"]
    assert "15m" not in truth["active_timeframes"]


def test_testnet_eligible_lanes_baseline_only() -> None:
    truth = _fresh()
    assert truth["testnet_eligible_lanes"] == ["money_flow_v1_2_baseline"]
    for lane in truth["active_lanes"]:
        expected = pt_rt1_6_lane_testnet_eligible(lane["lane_id"])
        assert lane["testnet_eligible"] == expected


def test_production_and_live_approvals_are_false() -> None:
    truth = _fresh()
    assert truth["production_approved"] is False
    assert truth["live_trading_approved"] is False
    for lane in [*truth["active_lanes"], *truth["archived_lanes"]]:
        assert lane["production_approved"] is False
        assert lane["live_approved"] is False


def test_testnet_fills_never_update_synthetic_pnl() -> None:
    truth = _fresh()
    assert truth["testnet_fills_update_synthetic_pnl"] is False


def test_runtime_safety_policy_locked_down() -> None:
    truth = _fresh()
    policy = truth["runtime_safety_policy"]
    assert policy["live_trading_enabled"] is False
    assert policy["exchange_order_submission_enabled"] is False
    assert policy["private_exchange_endpoints_enabled"] is False
    assert policy["sandbox_mode_required"] is True


def test_configured_symbols_nine_canonical() -> None:
    truth = _fresh()
    assert len(truth["configured_symbols"]) == 9
    assert set(truth["configured_symbols"]) == {
        "BTC",
        "ETH",
        "SOL",
        "XRP",
        "DOGE",
        "HYPE",
        "BNB",
        "SUI",
        "AVAX",
    }


def test_testnet_notional_is_25_usdc() -> None:
    truth = _fresh()
    assert truth["testnet_fixed_notional_usdc"] == 25


def test_scope_is_week2_active() -> None:
    truth = _fresh()
    assert truth["scope"] == "pt_rt1_6_week2_active"
