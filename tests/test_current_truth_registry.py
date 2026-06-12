"""Consistency test: current_truth.json must equal a fresh export from canonical anchors.

Any hand-edit or anchor drift fails this test, forcing re-export.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.export_current_truth import build_truth
from services.paper_runtime.pt_rt1 import (
    PT_RT2_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT2_ACTIVE_TIMEFRAMES,
    PT_RT2_ARCHIVED_STRATEGY_LANE_IDS,
    PT_RT2_DISABLED_TIMEFRAMES,
    PT_RT2_UNIVERSE_SYMBOLS,
    pt_rt2_lane_testnet_eligible,
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
        PT_RT2_ACTIVE_STRATEGY_LANE_IDS
    )


def test_archived_lanes_match_anchor() -> None:
    truth = _fresh()
    assert [lane["lane_id"] for lane in truth["archived_lanes"]] == list(
        PT_RT2_ARCHIVED_STRATEGY_LANE_IDS
    )


def test_active_timeframes_match_anchor() -> None:
    truth = _fresh()
    assert truth["active_timeframes"] == list(PT_RT2_ACTIVE_TIMEFRAMES)


def test_paused_timeframes_match_anchor() -> None:
    truth = _fresh()
    assert truth["paused_timeframes"] == list(PT_RT2_DISABLED_TIMEFRAMES)
    for timeframe in ("15m", "1h", "4h"):
        assert timeframe in truth["paused_timeframes"]
        assert timeframe not in truth["active_timeframes"]


def test_no_lane_is_testnet_eligible() -> None:
    truth = _fresh()
    assert truth["testnet_eligible_lanes"] == []
    for lane in [*truth["active_lanes"], *truth["archived_lanes"]]:
        assert lane["testnet_eligible"] is False
        assert pt_rt2_lane_testnet_eligible(lane["lane_id"]) is False


def test_observed_universe_matches_anchor() -> None:
    truth = _fresh()
    assert truth["observed_universe_symbols"] == list(PT_RT2_UNIVERSE_SYMBOLS)
    assert len(truth["observed_universe_symbols"]) == 7
    for symbol in ("HYPE", "SUI"):
        assert symbol in truth["configured_symbols"]
        assert symbol not in truth["observed_universe_symbols"]
        assert symbol in truth["configured_not_traded_symbols"]


def test_committed_characterization_carried_in_truth() -> None:
    truth = _fresh()
    block = truth["committed_characterization"]
    assert block["standalone_label"] == "defensive_trend_mechanic_not_validated_alpha"
    assert block["trade_level_label"] == "source_faithful_but_underperformed"
    assert block["regime_overlay_verdict"] == "regime_filter_does_not_reduce_drawdown_oos"
    assert "not a validated control" in block["regime_overlay_label"]


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


def test_testnet_policy_is_paper_only() -> None:
    truth = _fresh()
    assert "NO lane is testnet eligible" in truth["testnet_policy"]


def test_scope_is_pt_rt2_mf_signal_observation() -> None:
    truth = _fresh()
    assert truth["scope"] == "pt_rt2_mf_signal_observation"
