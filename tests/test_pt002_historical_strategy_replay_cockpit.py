from __future__ import annotations

import json
from pathlib import Path

from services.strategy_validation.historical_replay import (
    PT002_BASELINE_STRATEGY_ID,
    PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID,
    PT002_NO_MACD_STRATEGY_ID,
    PT002_REPORT_NAME,
    PT002_SYMBOLS,
    PT002_TIMEFRAMES,
    build_pt002_historical_replay_summary_from_sv117_payload,
)


SUMMARY_PATH = Path("docs/pt0_0_2_historical_strategy_replay_summary.json")
REPORT_PATH = Path("docs/pt0_0_2_historical_strategy_replay_cockpit.md")


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text())


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def test_historical_replay_summary_uses_historical_truth_not_testnet_prices() -> None:
    summary = _summary()

    assert summary["report"] == PT002_REPORT_NAME
    assert summary["source"]["strategy_truth_lane"] == "historical_strategy_truth"
    assert summary["source"]["source_kind"] == "trusted_offline_historical_candles"
    assert summary["source"]["testnet_prices_used_as_strategy_truth"] is False
    assert summary["source"]["private_or_signed_endpoints_used"] is False
    assert summary["source"]["order_endpoints_used"] is False
    assert summary["boundary_flags"]["uses_historical_candles_only_for_replay"] is True
    assert summary["boundary_flags"]["submits_orders"] is False
    assert summary["boundary_flags"]["calls_order_endpoints"] is False
    assert summary["sandbox_execution_ledger_separate"] is True


def test_btc_eth_sol_15m_1h_4h_datasets_are_audited_and_replay_ready() -> None:
    summary = _summary()
    datasets = {(row["symbol"], row["timeframe"]): row for row in summary["datasets"]}

    assert set(datasets) == {(symbol, timeframe) for symbol in PT002_SYMBOLS for timeframe in PT002_TIMEFRAMES}
    for symbol in PT002_SYMBOLS:
        for timeframe in PT002_TIMEFRAMES:
            row = datasets[(symbol, timeframe)]
            assert row["available"] is True
            assert row["replay_ready"] is True
            assert row["candle_count"] > 0
            assert "historical_candles_available" in row["reason_codes"]

    assert "db_audit" in summary
    if summary["db_audit"]:
        assert "historical_db_unreachable" in summary["db_audit"][0]["reason_codes"]


def test_historical_replay_contains_all_research_strategies_for_all_symbols_and_timeframes() -> None:
    summary = _summary()
    strategies = {row["id"]: row for row in summary["strategies"]}
    replay_keys = {
        (row["strategy_id"], row["symbol"], row["timeframe"])
        for row in summary["replays"]
    }

    assert PT002_BASELINE_STRATEGY_ID in strategies
    assert strategies[PT002_BASELINE_STRATEGY_ID]["label"] == "OG replay / strategy"
    assert strategies[PT002_BASELINE_STRATEGY_ID]["research_only"] is False
    assert PT002_NO_MACD_STRATEGY_ID in strategies
    assert strategies[PT002_NO_MACD_STRATEGY_ID]["label"] == "MACD removed"
    assert strategies[PT002_NO_MACD_STRATEGY_ID]["research_only"] is True
    assert strategies[PT002_NO_MACD_STRATEGY_ID]["changes_production_rules"] is False
    assert PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID in strategies
    assert strategies[PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID]["label"] == "Only close on 5/20 cross"
    assert strategies[PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID]["research_only"] is True
    assert strategies[PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID]["changes_production_rules"] is False
    assert len(summary["replays"]) == len(PT002_SYMBOLS) * len(PT002_TIMEFRAMES) * len(summary["strategies"])

    expected = {
        (strategy_id, symbol, timeframe)
        for strategy_id in (
            PT002_BASELINE_STRATEGY_ID,
            PT002_NO_MACD_STRATEGY_ID,
            PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID,
        )
        for symbol in PT002_SYMBOLS
        for timeframe in PT002_TIMEFRAMES
    }
    assert replay_keys == expected


def test_macd_removed_replay_removes_macd_entry_and_rollover_exit_gates_without_changing_production_rules() -> None:
    summary = _summary()
    macd_removed = [
        row for row in summary["replays"]
        if row["strategy_id"] == PT002_NO_MACD_STRATEGY_ID
    ]
    baseline = [
        row for row in summary["replays"]
        if row["strategy_id"] == PT002_BASELINE_STRATEGY_ID
    ]

    assert macd_removed
    assert all(row["research_only"] is True for row in macd_removed)
    assert all(row["research_only"] is False for row in baseline)
    assert any(
        "macd_removed_entry_allowed" in row["reason_counts"]["entry_reason_counts"]
        for row in macd_removed
    )
    assert all(
        "macd_rollover" not in row["reason_counts"]["exit_reason_counts"]
        for row in macd_removed
    )
    assert summary["boundary_flags"]["changes_money_flow_rules"] is False


def test_ema5_sma20_cross_close_replay_waits_for_bearish_cross_close() -> None:
    summary = _summary()
    cross_close = [
        row for row in summary["replays"]
        if row["strategy_id"] == PT002_EMA5_SMA20_CROSS_CLOSE_STRATEGY_ID
    ]

    assert cross_close
    assert all(row["research_only"] is True for row in cross_close)
    assert any(
        "ema5_sma20_bearish_cross_close" in row["reason_counts"]["exit_reason_counts"]
        for row in cross_close
    )
    assert all(
        "ma_alignment_break" not in row["reason_counts"]["exit_reason_counts"]
        for row in cross_close
    )
    assert all(
        "macd_rollover" not in row["reason_counts"]["exit_reason_counts"]
        for row in cross_close
    )
    assert summary["boundary_flags"]["changes_money_flow_rules"] is False


def test_replay_export_contains_candles_indicators_markers_trades_and_equity_curve() -> None:
    summary = _summary()
    replay = next(row for row in summary["replays"] if row["symbol"] == "ETH" and row["timeframe"] == "1h")

    assert replay["candles"]
    assert replay["indicators"]
    assert replay["markers"]
    assert replay["trades"]
    assert replay["equity_curve"]
    assert replay["strategy_truth_lane"] == "historical_strategy_truth"
    assert replay["testnet_prices_used_as_strategy_truth"] is False
    assert {"EMA5", "EMA10", "SMA20", "RSI", "MACD", "MACD_signal", "MACD_histogram"}.issubset(
        replay["indicators"][0].keys()
    )


def test_dynamic_equity_starts_at_10000_and_updates_after_winning_and_losing_trades() -> None:
    summary = _summary()
    all_trades = [trade for replay in summary["replays"] for trade in replay["trades"]]

    assert summary["initial_equity"] == "10000"
    assert summary["capital_sizing_mode"] == "dynamic_equity_pct"
    assert summary["sizing_policy"]["sizing_basis"] == "realized_equity"
    assert summary["sizing_policy"]["does_not_reset_each_trade_to_static_10000"] is True
    assert any(float(trade["net_pnl"]) < 0 for trade in all_trades)
    assert any(float(trade["net_pnl"]) > 0 for trade in all_trades)

    eth_1h = next(row for row in summary["replays"] if row["symbol"] == "ETH" and row["timeframe"] == "1h")
    first, second = eth_1h["trades"][0], eth_1h["trades"][1]
    assert first["equity_before_trade"] == "10000.00000000"
    assert second["equity_before_trade"] == first["equity_after_trade"]
    assert second["notional_used"] != "10000.00000000"


def test_fill_assumptions_and_costs_are_visible() -> None:
    summary = _summary()
    fills = {row["id"]: row for row in summary["fill_assumptions"]}

    assert fills["next_candle_open"]["default"] is True
    assert fills["next_candle_close"]["research_only"] is False
    assert fills["same_candle_close_research_only"]["research_only"] is True
    assert summary["selected_fill_assumption"] == "next_candle_open"
    assert summary["cost_assumptions"] == {"fee_bps": "5", "slippage_bps": "3"}


def test_green_and_red_markers_represent_historical_entry_and_exit_fills() -> None:
    summary = _summary()
    markers = [marker for replay in summary["replays"] for marker in replay["markers"]]

    assert any(marker["color_role"] == "green" and marker["marker_type"] == "entry_fill" for marker in markers)
    assert any(marker["color_role"] == "red" and marker["marker_type"] == "exit_fill" for marker in markers)
    assert all(marker["source"] == "historical_replay" for marker in markers)
    assert all("live" not in marker["label"].lower() for marker in markers)


def test_builder_marks_missing_dataset_with_clear_reason_code() -> None:
    minimal_payload = {
        "baseline_results": [
            {
                "request": {"symbol": "BTC", "component_keys": ["sleeve_15m"], "start_at": "2026-01-01T00:00:00Z", "end_at": "2026-01-02T00:00:00Z"},
                "timeframe": "15m",
                "contexts": [
                    {
                        "candle_close_time": "2026-01-01T00:15:00Z",
                        "candle_open_time": "2026-01-01T00:00:00Z",
                        "open": "1",
                        "high": "2",
                        "low": "1",
                        "close": "2",
                    }
                ],
                "trades": [],
                "metrics": {"starting_equity": "10000", "ending_equity": "10000", "number_of_trades": 0},
                "data_coverage": {"actual_candle_count": 1, "expected_candle_count": 1, "coverage_percent": "1.00000000"},
            }
        ]
    }
    summary = build_pt002_historical_replay_summary_from_sv117_payload(minimal_payload)
    missing = [row for row in summary["datasets"] if not row["available"]]

    assert len(missing) == 8
    assert all("historical_candles_missing" in row["reason_codes"] for row in missing)


def test_dashboard_has_historical_replay_tab_and_stable_chart_container() -> None:
    html, js, css = _dashboard_assets()

    assert 'data-view="historical-replay"' in html
    assert "Historical Replay" in html
    assert "historical-replay-strategy-filter" in html
    assert "Replay strategy" in html
    assert "historical-replay-arrow-descriptions-toggle" in html
    assert "historical-replay-date-start" in html
    assert "historical-replay-date-end" in html
    assert "historical-replay-date-clear" in html
    assert "Show arrow descriptions" in html
    assert "historical-replay-chart" in html
    assert "Trade Inspector" in html
    assert "Click a chart arrow or trade row" in html
    assert "BTC / ETH / SOL Comparison" in html
    assert "Sandbox Execution Plumbing" in html
    assert "pt0_0_2_historical_strategy_replay_summary.json" in js
    assert "baseline_current_money_flow_rules" in js
    assert "macd_removed_research_only" in js
    assert "only_close_on_5_20_cross_research_only" in js
    assert ".filter((strategy) => isHistoricalReplayStrategyVisible(strategy.value))" in js
    assert "MACD removed" not in js
    assert "Only close on 5/20 cross" not in js
    assert "strategy_id" in js
    assert "Replay strategy:" in js
    assert '["15m", "1h", "4h", "1d"]' in js
    assert 'return canonical === "1d" ? "1D" : canonical;' in js
    assert "renderHistoricalReplayChart" in js
    assert "filteredHistoricalReplay" in js
    assert "historical-replay-date-start" in html
    assert "historicalDateRange" in js
    assert "Date filter:" not in js
    assert "Research-only:" not in js
    assert "Target met:" not in js
    assert "fresh 10k date-window replay" in js
    assert "chart-price-axis-readout-inline" in js
    assert "historical-chart-stage" in js
    assert "historicalOscillatorRows" in js
    assert "historicalMacdHistogramRows" in js
    assert "const HISTORICAL_RSI_PANE = 0;" in js
    assert "const HISTORICAL_PRICE_PANE = 1;" in js
    assert "HISTORICAL_RSI_PANE" in js
    assert "HISTORICAL_MACD_PANE" in js
    assert "Pane order: RSI, candles, MACD" in js
    assert "setHistoricalReplayPaneHeights" in js
    assert "setStretchFactor" in js
    assert "Math.round(height * 0.15)" in js
    assert "Math.round(height * 0.7)" in js
    assert "chart.panes" in js
    assert "historicalConstantRows" in js
    assert "createPriceLine" in js
    assert "historicalChartMarkers" in js
    assert "historicalMarkerLines" in js
    assert "historicalMarkerObjectId" in js
    assert "markerTradeIds" in js
    assert "subscribeClick" in js
    assert "hoveredObjectId" in js
    assert "selectHistoricalReplayTrade" in js
    assert "Trade Inspector Focus Mode" in js
    assert "overlay-inspector-grid trade-inspector-focus-grid" in js
    assert "historical-replay-focus-card" in js
    assert "showArrowDescriptions: false" in js
    assert "historicalMarkerPnlLine" in js
    assert "if (!state.historicalReplay.showArrowDescriptions)" in js
    assert ".flatMap((marker)" in js
    assert "size: index === 0 ? 1 : 0" in js
    assert "Net PnL:" in js
    assert "PnL:" in js
    assert "Entry:" in js
    assert "Exit:" in js
    assert "marker.fill_assumption" not in js
    assert "CANDLE_UP_COLOR" in js
    assert "CANDLE_DOWN_COLOR" in js
    assert "CHART_BACKGROUND_COLOR" in js
    assert "borderVisible: true" in js
    assert ".historical-replay-chart .tradingview-lightweight-chart" in css
    assert "height: clamp(720px, 82vh, 1040px);" in css
    assert "contain: layout paint size;" in css
    assert ".historical-chart-stage" in css
    assert ".chart-price-axis-readout-inline" in css
    assert ".historical-overlay-legend" in css
    assert ".legend-dot.rsi" in css
    assert ".legend-dot.macd-signal" in css
    assert ".historical-replay-controls label.checkbox-control" in css
    assert ".trade-inspector-card" in css
    assert ".historical-replay-focus-card" in css
    assert ".trade-inspector-focus-grid" in css
    assert ".overlay-inspector-grid dd.positive" in css
    assert ".trade-inspector-hero" in css
    assert ".reason-chip" in css


def test_dashboard_separates_historical_replay_from_sandbox_execution_and_has_no_order_controls() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    assert "testnet prices are not used for strategy validation" in dashboard
    assert "historical replay data only" in dashboard
    assert "sandbox execution ledger remains separate" not in dashboard
    assert "sandbox execution plumbing" in dashboard
    assert "Paper Observation" in html
    assert "HYPERLIQUID_MAINNET_PUBLIC_INFO_URL" in js
    assert "renderHistoricalReplay" in js
    assert "historical replay" in dashboard
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


def test_pt002_report_exists_and_records_boundaries() -> None:
    assert REPORT_PATH.exists()
    report = REPORT_PATH.read_text()

    assert "PT0.0.2 Historical Strategy Replay Cockpit" in report
    assert "Hyperliquid testnet market data is not strategy truth" in report
    assert "MACD removed" in report
    assert "Only close on 5/20 cross" in report
    assert "ema5_sma20_bearish_cross_close" in report
    assert "research-only" in report
    assert "No orders are submitted by PT0.0.2" in report
    assert "Money Flow rules are unchanged" in report
