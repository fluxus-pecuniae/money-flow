import json
from decimal import Decimal
from pathlib import Path

from scripts import run_sv23_realistic_backtest as sv23


def test_sv23_execution_scenarios_are_next_open_only() -> None:
    assert sv23.PRIMARY_FILL_ASSUMPTION == "next_candle_open"
    assert {row.scenario_id for row in sv23.EXECUTION_SCENARIOS} == {
        "base_next_open",
        "conservative_next_open",
        "stress_next_open",
    }
    assert "same_candle_close_research_only" in sv23.PROMOTION_DISABLED_FILL_ASSUMPTIONS


def test_sv23_execution_price_is_adverse_after_slippage() -> None:
    scenario = sv23.EXECUTION_SCENARIOS[1]
    raw = Decimal("100")

    buy = sv23.execution_price(raw_price=raw, scenario=scenario, side="buy", adverse_gap=Decimal("10"))
    sell = sv23.execution_price(raw_price=raw, scenario=scenario, side="sell", adverse_gap=Decimal("10"))

    assert buy > raw
    assert sell < raw


def test_sv23_summary_exists_and_preserves_boundaries() -> None:
    summary_path = Path("docs/sv2_3_realistic_backtest_summary.json")
    report_path = Path("docs/sv2_3_realistic_backtest.md")

    assert summary_path.exists()
    assert report_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["phase"] == "SV2.3"
    assert summary["report"] == "sv2_3_realistic_backtest"
    assert summary["status"] == "realistic_backtest_complete"
    assert summary["timeframes"] == ["1h", "4h", "1d"]
    assert summary["disabled_timeframes"] == ["15m"]
    assert summary["primary_fill_assumption"] == "next_candle_open"
    assert summary["candidate_gate"]["same_candle_promotion_results_allowed"] is False
    assert summary["boundaries"]["calls_order_endpoints"] is False
    assert summary["boundaries"]["calls_private_or_signed_endpoints"] is False
    assert summary["boundaries"]["enables_live_trading"] is False
    assert summary["boundaries"]["approves_production_strategy"] is False


def test_sv23_summary_covers_week2_strategies_and_cost_scenarios() -> None:
    summary = json.loads(Path("docs/sv2_3_realistic_backtest_summary.json").read_text(encoding="utf-8"))

    assert summary["strategy_ids"] == [
        "money_flow_v1_2_baseline",
        "avoid_low_rolling_range_20",
        "mf_orig_1d_stage2_breakout_resistance_full_equity",
    ]
    assert {row["scenario_id"] for row in summary["execution_scenarios"]} == {
        "base_next_open",
        "conservative_next_open",
        "stress_next_open",
    }
    assert summary["result_count"] == len(summary["results"])
    assert summary["result_count"] > 0
    assert all(row["fill_assumption"] == "next_candle_open" for row in summary["results"])
    assert all(row["production_approved"] is False for row in summary["results"])
    assert all(row["testnet_prices_used_as_strategy_truth"] is False for row in summary["results"])

