from __future__ import annotations

import json
from pathlib import Path

from services.strategy_validation.historical_replay import (
    PT002_SYMBOLS,
    PT003_REPORT_NAME,
    PT003_TARGET_START_AT,
    PT003_TIMEFRAMES,
)


SUMMARY_PATH = Path("docs/pt0_0_3_historical_strategy_replay_summary.json")
REPORT_PATH = Path("docs/pt0_0_3_historical_data_horizon_and_1d_readiness.md")


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def test_pt003_summary_targets_jan_2025_and_adds_1d_timeframe() -> None:
    summary = _summary()

    assert summary["report"] == PT003_REPORT_NAME
    assert PT003_TARGET_START_AT == "2025-01-01T00:00:00Z"
    assert summary["target_start_at"] == PT003_TARGET_START_AT
    assert summary["timeframes"] == list(PT003_TIMEFRAMES)
    assert "1D" in summary["timeframes"]
    assert summary["boundary_flags"]["uses_historical_candles_only_for_replay"] is True
    assert summary["boundary_flags"]["testnet_prices_used_as_strategy_truth"] is False
    assert summary["boundary_flags"]["changes_money_flow_rules"] is False
    assert summary["boundary_flags"]["submits_orders"] is False
    assert summary["boundary_flags"]["calls_order_endpoints"] is False
    assert summary["boundary_flags"]["creates_1d_money_flow_sleeve"] is False


def test_data_readiness_audits_btc_eth_sol_across_15m_1h_4h_1d() -> None:
    summary = _summary()
    readiness = {(row["symbol"], row["timeframe"]): row for row in summary["data_readiness"]}

    assert set(readiness) == {(symbol, timeframe) for symbol in PT002_SYMBOLS for timeframe in PT003_TIMEFRAMES}
    for symbol in PT002_SYMBOLS:
        for timeframe in PT003_TIMEFRAMES:
            row = readiness[(symbol, timeframe)]
            assert row["target_start_at"] == PT003_TARGET_START_AT
            assert row["available"] is True
            assert row["replay_ready"] is True
            assert row["candle_count"] > 0
            assert "historical_candles_available" in row["reason_codes"]


def test_actual_earliest_available_is_reported_when_jan_2025_target_is_not_met() -> None:
    summary = _summary()

    for row in summary["data_readiness"]:
        assert row["target_start_met"] is False
        assert row["actual_earliest_available"] > PT003_TARGET_START_AT
        assert "historical_target_start_not_available" in row["reason_codes"]
        assert "historical_earliest_available_after_target" in row["reason_codes"]
        assert row["target_coverage_percent"] != "1.00000000"


def test_1d_readiness_uses_labeled_utc_aggregation_from_4h_without_new_strategy_sleeve() -> None:
    summary = _summary()
    daily_rows = [row for row in summary["data_readiness"] if row["timeframe"] == "1D"]

    assert len(daily_rows) == len(PT002_SYMBOLS)
    for row in daily_rows:
        assert row["source_kind"] == "deterministic_aggregation_from_historical_replay_candles"
        assert row["aggregation_used"] is True
        assert row["aggregation_source_timeframe"] == "4h"
        assert row["aggregation_convention"] == "UTC day OHLCV from complete/in-range source candles"
        assert row["creates_new_money_flow_sleeve"] is False
        assert "historical_aggregation_used" in row["reason_codes"]
        assert "not_a_new_1d_money_flow_sleeve" in row["reason_codes"]


def test_1d_replay_exports_candles_indicators_markers_trades_and_dynamic_equity() -> None:
    summary = _summary()
    daily_replays = [row for row in summary["replays"] if row["timeframe"] == "1D"]

    assert len(daily_replays) == len(PT002_SYMBOLS) * len(summary["strategies"])
    assert summary["initial_equity"] == "10000"
    assert summary["sizing_policy"]["does_not_reset_each_trade_to_static_10000"] is True
    for replay in daily_replays:
        assert replay["strategy_truth_lane"] == "historical_strategy_truth"
        assert replay["testnet_prices_used_as_strategy_truth"] is False
        assert replay["daily_aggregation"]["status"] == "implemented"
        assert replay["daily_aggregation"]["source_timeframe"] == "4h"
        assert replay["daily_aggregation"]["creates_new_money_flow_sleeve"] is False
        assert replay["candles"]
        assert replay["indicators"]
        assert replay["markers"]
        assert replay["trades"]
        assert replay["equity_curve"]
        assert replay["dynamic_equity_summary"]["initial_equity"] == "10000"
        assert replay["dynamic_equity_summary"]["uses_dynamic_equity"] is True


def test_dashboard_supports_1d_selector_and_data_horizon_panel() -> None:
    html, js, css = _dashboard_assets()

    assert "historical-data-horizon-panel" in html
    assert "pt0_0_3_historical_strategy_replay_summary.json" in js
    assert "break;" in js
    assert "Target start:" not in js
    assert "Target start" in js
    assert "Historical data horizon" in js
    assert "1D candles aggregated from" in js
    assert "not testnet strategy truth" in js
    assert "renderHistoricalDataHorizonPanel" in js
    assert ".historical-data-horizon-panel" in css
    assert "grid-template-columns: repeat(6, minmax(0, 1fr));" in css


def test_pt003_preserves_no_order_no_private_endpoint_boundaries() -> None:
    summary = _summary()
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    assert summary["source"]["private_or_signed_endpoints_used"] is False
    assert summary["source"]["order_endpoints_used"] is False
    assert summary["source"]["testnet_prices_used_as_strategy_truth"] is False
    assert "https://api.hyperliquid.xyz/info" not in js
    for phrase in (
        "submit order button",
        "cancel order button",
        "retry button",
        "amend button",
        "approve order button",
        "market buy",
        "market sell",
        "paper/live toggle",
        "auto-trade toggle",
    ):
        assert phrase not in dashboard


def test_pt003_report_exists_and_records_missing_horizon_truth() -> None:
    assert REPORT_PATH.exists()
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "PT0.0.3 Historical Data Horizon + 1D Replay Support" in report
    assert "2025-01-01T00:00:00Z" in report
    assert "1D candles aggregated from 4h historical replay candles" in report
    assert "Hyperliquid testnet market data is not strategy truth" in report
    assert "No orders were submitted" in report
    assert "Money Flow rules are unchanged" in report
