"""REGIME2 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - the pre-registered selection criterion picks on TRAIN drawdown (not
    Sharpe), applies the whipsaw tie-break inside the tie band, and never
    sees OOS (the selection function only accepts train-window inputs);
  - the search space is REGIME1's exact grid, unwidened;
  - the v2 gate holds REGIME1's bars unchanged and adds the pre-stated
    return-retention tolerance — each reason fires; a pass still always
    carries the not-alpha qualifier;
  - the importable gate's deployed default is the REGIME2-selected config
    with the honest verdict note on every surface;
  - the committed summary records the pre-registration, the honest FAIL
    (process stability), the labeled fixed-config fold texture, and the
    full whipsaw cost; the Research Log outcome is authored honestly.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from services.strategy_validation import regime1 as rg
from services.strategy_validation import regime2 as rg2
from services.strategy_validation import strategy_types

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "regime2_objective_aligned_regime_filter_evidence_summary.json"


# ---------------------------------------------------------------------------
# The pre-registered selection criterion
# ---------------------------------------------------------------------------


def test_selection_picks_lowest_train_drawdown_not_sharpe():
    rows = [
        # The "fast filter" REGIME1's Sharpe criterion would love: great
        # Sharpe-like profile but worse train drawdown. Must NOT be chosen.
        {"config_id": "fast", "train_max_drawdown_pct": Decimal("50"), "train_flips": 120},
        {"config_id": "slow", "train_max_drawdown_pct": Decimal("37"), "train_flips": 60},
        {"config_id": "mid", "train_max_drawdown_pct": Decimal("45"), "train_flips": 80},
    ]
    selection = rg2.select_by_train_drawdown(rows)
    assert selection["chosen"]["config_id"] == "slow"
    assert [r["config_id"] for r in selection["ranking"]] == ["slow", "mid", "fast"]


def test_whipsaw_tie_break_prefers_fewest_flips_inside_the_band():
    rows = [
        {"config_id": "a_whippy", "train_max_drawdown_pct": Decimal("37.0"), "train_flips": 140},
        {"config_id": "b_calm", "train_max_drawdown_pct": Decimal("38.5"), "train_flips": 40},
        {"config_id": "c_outside_band", "train_max_drawdown_pct": Decimal("39.5"), "train_flips": 5},
    ]
    selection = rg2.select_by_train_drawdown(rows)
    # a (37.0) and b (38.5) are within the 2.0pp tie band; c (39.5) is not.
    assert selection["ties_considered"] == ["a_whippy", "b_calm"]
    assert selection["chosen"]["config_id"] == "b_calm"  # fewest flips wins
    # Deterministic final tie-break on config_id.
    rows_eq = [
        {"config_id": "b", "train_max_drawdown_pct": Decimal("37"), "train_flips": 10},
        {"config_id": "a", "train_max_drawdown_pct": Decimal("37"), "train_flips": 10},
    ]
    assert rg2.select_by_train_drawdown(rows_eq)["chosen"]["config_id"] == "a"


def test_selection_input_carries_no_oos_fields():
    # The selection function's contract is train-only; passing an OOS field
    # has no effect on the outcome (it is never read), and the runner only
    # builds rows from curve_stats(up_to=split) + train-window flips.
    rows = [
        {"config_id": "x", "train_max_drawdown_pct": Decimal("40"), "train_flips": 10,
         "oos_anything": Decimal("-999")},
        {"config_id": "y", "train_max_drawdown_pct": Decimal("30"), "train_flips": 99},
    ]
    assert rg2.select_by_train_drawdown(rows)["chosen"]["config_id"] == "y"
    with pytest.raises(ValueError):
        rg2.select_by_train_drawdown([{"config_id": "z", "train_max_drawdown_pct": None, "train_flips": 0}])


def test_search_space_is_regime1_grid_unwidened():
    configs = rg.generate_regime_configs()
    assert len(configs) == 18
    assert rg.REGIME_LOOKBACKS == (30, 60, 90)
    assert rg.BREADTH_THRESHOLDS == (Decimal("0.4"), Decimal("0.5"), Decimal("0.6"))
    assert rg.BTC_RULES == ("vote", "required")
    assert "NOT widened" in rg2.PRE_REGISTRATION["search_space"]


def test_train_flips_counts_only_up_to_cutoff():
    from datetime import UTC, datetime, timedelta

    t0 = datetime(2025, 1, 1, tzinfo=UTC)
    series = [
        (t0 + timedelta(days=i), {"risk_on": bool(i % 2)})  # flips every day
        for i in range(10)
    ]
    assert rg2.train_flips(series, up_to=t0 + timedelta(days=4)) == 4
    assert rg2.train_flips(series, up_to=t0 + timedelta(days=9)) == 9


# ---------------------------------------------------------------------------
# The v2 gate: REGIME1 bars unchanged + return-retention
# ---------------------------------------------------------------------------


def _healthy():
    return {
        "always_oos_stats": {
            "days": 300, "max_drawdown_pct": Decimal("60"),
            "sharpe_annual": Decimal("0.2"), "total_return_pct": Decimal("10"),
        },
        "gated_oos_stats": {
            "days": 300, "max_drawdown_pct": Decimal("30"),
            "sharpe_annual": Decimal("0.6"), "total_return_pct": Decimal("5"),
        },
        "fold_dd_reductions": [
            {"gated_max_drawdown_pct": Decimal("20"), "always_max_drawdown_pct": Decimal("40")},
            {"gated_max_drawdown_pct": Decimal("30"), "always_max_drawdown_pct": Decimal("60")},
        ],
        "no_lookahead_verified": True,
    }


def test_gate_v2_holds_regime1_bars_and_adds_return_tolerance():
    gate = rg2.evaluate_regime_filter_gate_v2(**_healthy())
    assert gate["passed"] and gate["status"] == rg2.VERDICT_PASS
    assert "risk_tool_not_alpha_no_profit_claim" in gate["qualifiers"]
    assert gate["pre_registration"] == rg2.PRE_REGISTRATION
    # REGIME1 reasons still fire through the v2 gate.
    kwargs = _healthy()
    kwargs["fold_dd_reductions"] = [
        {"gated_max_drawdown_pct": Decimal("50"), "always_max_drawdown_pct": Decimal("40")}
    ]
    gate = rg2.evaluate_regime_filter_gate_v2(**kwargs)
    assert not gate["passed"]
    assert "walk_forward_drawdown_not_reduced_in_every_fold" in gate["reason_codes"]
    # The new return-retention bar fires at the pre-stated tolerance.
    kwargs = _healthy()
    kwargs["gated_oos_stats"] = dict(kwargs["gated_oos_stats"], total_return_pct=Decimal("-20"))
    gate = rg2.evaluate_regime_filter_gate_v2(**kwargs)
    assert not gate["passed"]
    assert "oos_return_given_up_beyond_tolerance" in gate["reason_codes"]
    # Inside the tolerance it does not fire.
    kwargs = _healthy()
    kwargs["gated_oos_stats"] = dict(kwargs["gated_oos_stats"], total_return_pct=Decimal("-14"))
    gate = rg2.evaluate_regime_filter_gate_v2(**kwargs)
    assert "oos_return_given_up_beyond_tolerance" not in gate["reason_codes"]
    assert rg2.RETURN_TOLERANCE_PP == Decimal("25")


# ---------------------------------------------------------------------------
# Deployed default + committed summary honesty
# ---------------------------------------------------------------------------


def test_deployed_default_is_the_regime2_selection_with_honest_note():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["train_only_choice"]["chosen_config"] == rg.DEFAULT_CONFIG.config_id
    assert rg.DEFAULT_CONFIG.config_id == "regime1_lb90_br6_btc_required_1d"
    assert "REGIME2" in rg.COMMITTED_VERDICT_NOTE
    assert "not a validated control" in rg.COMMITTED_VERDICT_NOTE
    builder = strategy_types.resolve_regime_filter()
    assert builder is rg.build_regime_gate  # seam unchanged, default updated


def test_committed_summary_records_preregistration_and_honest_fail():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["phase"] == rg2.PHASE
    assert summary["verdict"] == rg2.VERDICT_FAIL  # the committed honest fail
    assert summary["disclaimer"] == rg.DISCLAIMER
    assert summary["pre_registration"] == rg2.PRE_REGISTRATION
    assert "committed to git BEFORE" in summary["pre_registration_confirmation"]
    gate = summary["regime_filter_gate"]
    assert gate["status"] == rg2.VERDICT_FAIL
    assert gate["reason_codes"] == ["walk_forward_drawdown_not_reduced_in_every_fold"]
    # Endpoint bars passed and are visible: the 30% bar was cleared.
    assert Decimal(summary["headline"]["oos_max_drawdown_reduction_pct"]) >= Decimal("30")
    # The fixed-config fold texture is surfaced and labeled.
    texture = summary["fixed_config_fold_texture_not_a_verdict"]
    assert "NOT A VERDICT" in texture["note"]
    for fold in texture["folds"]:
        assert Decimal(fold["gated_max_drawdown_pct"]) < Decimal(fold["always_max_drawdown_pct"])
    # Whipsaw cost surfaced; boundaries honest; grid honest.
    assert summary["whipsaw_cost"]["oos_window"]["state_flips"] > 0
    assert summary["boundaries"]["criterion_and_gates_pre_registered_before_selection"] is True
    assert summary["boundaries"]["search_space_not_widened_from_regime1"] is True
    assert summary["boundaries"]["regime1_bars_held_unchanged"] is True
    assert len(summary["per_config_results"]) == 18
    assert summary["no_lookahead"]["verified"] is True
    # Research Log honesty: the authored outcome for this phase is fail.
    decision_log = (REPO_ROOT / "money-flow" / "03_Decision_Log.md").read_text(encoding="utf-8")
    block_start = decision_log.find("phase: REGIME2")
    assert block_start != -1, "REGIME2 research_log block must exist"
    assert "outcome: fail" in decision_log[block_start : block_start + 400]
