from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path("services/strategy_validation/goal_strat2.py")
    spec = importlib.util.spec_from_file_location("goal_strat2", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_goal_strat2_selects_two_non_existing_research_candidates() -> None:
    goal_strat2 = _load_module()
    report = goal_strat2.build_goal_strat2_report()

    assert report["decision"] == "two_non_existing_strategies_worth_testing"
    assert len(report["selected_candidates"]) == 2
    assert report["eligible_non_existing_candidates"] >= 2
    families = {candidate["strategy_family"] for candidate in report["selected_candidates"]}
    assert len(families) == 2
    assert "relative_strength_rotation" in families
    assert "trend_breakout" in families
    for candidate in report["selected_candidates"]:
        assert candidate["testing_status"] == goal_strat2.CANDIDATE_LABEL
        assert candidate["not_existing_strategy"] is True
        assert candidate["strategy_id"] not in goal_strat2.EXISTING_RUNTIME_LANES
        assert candidate["strategy_family"] not in goal_strat2.EXCLUDED_EXISTING_OR_ADJACENT_FAMILIES
        assert candidate["entry_model"] not in goal_strat2.EXISTING_OR_ADJACENT_ENTRY_MODELS
        assert candidate["research_status"] == goal_strat2.RESEARCH_ONLY_LABEL
        assert float(candidate["active_timeframe_metrics"]["net_pnl"]) > 0
        assert float(candidate["active_timeframe_metrics"]["profit_factor"]) >= 1.30
        assert float(candidate["active_timeframe_metrics"]["max_drawdown_pct"]) <= 0.32
        assert int(candidate["active_timeframe_metrics"]["trade_count"]) >= 200


def test_goal_strat2_reports_and_boundaries_are_research_only(tmp_path: Path) -> None:
    goal_strat2 = _load_module()
    report = goal_strat2.build_goal_strat2_report()
    report_path = tmp_path / "report.md"
    summary_path = tmp_path / "summary.json"

    cwd = Path.cwd()
    try:
        # Candidate report paths are relative to cwd by design. Use repo cwd but
        # direct main report/summary into tmp for the focused write check.
        goal_strat2.write_goal_strat2_outputs(report, report_path, summary_path, tmp_path)
    finally:
        assert Path.cwd() == cwd

    assert report_path.exists()
    assert summary_path.exists()
    assert len(list(tmp_path.glob("goal_strat2_candidate_*.md"))) == 2
    markdown = report_path.read_text(encoding="utf-8")
    summary = summary_path.read_text(encoding="utf-8")
    assert "GOAL-STRAT2 is research-only" in markdown
    assert "No strategy is production-approved" in markdown
    assert "Live trading is not approved" in markdown
    assert "two_non_existing_strategies_worth_testing" in summary
    flags = report["boundary_flags"]
    assert flags["research_only"] is True
    assert flags["mutates_active_pt_rt_runtime"] is False
    assert flags["creates_runtime_artifacts"] is False
    assert flags["submits_live_orders"] is False
    assert flags["submits_testnet_orders"] is False
    assert flags["calls_private_signed_order_endpoints"] is False
    assert flags["uses_testnet_data_as_strategy_truth"] is False
    assert flags["changes_production_money_flow_rules"] is False
    assert flags["approves_production_strategy"] is False
    assert flags["approves_live_trading"] is False
    assert flags["creates_order_intent"] is False
    assert flags["creates_prepared_venue_order"] is False
    assert flags["creates_submitted_order"] is False


def test_goal_strat2_static_module_has_no_order_artifact_paths() -> None:
    source = Path("services/strategy_validation/goal_strat2.py").read_text(encoding="utf-8")
    forbidden = (
        "OrderIntent(",
        "PreparedVenueOrder(",
        "SubmittedOrder(",
        ".submit_order(",
        "private/signed/order endpoint",
    )
    for fragment in forbidden:
        assert fragment not in source
