from __future__ import annotations

from pathlib import Path


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def test_chart_container_has_stable_explicit_height_and_bounded_parents() -> None:
    _html, _js, css = _dashboard_assets()

    assert ".tradingview-lightweight-chart" in css
    assert "height: clamp(420px, 56vh, 680px);" in css
    assert "min-height: 0;" in css
    assert "max-height: 680px;" in css
    assert "contain: layout paint size;" in css
    assert ".exchange-chart-shell" in css
    assert "contain: layout paint;" in css
    assert ".uat-center-cockpit" in css
    assert "overflow: hidden;" in css


def test_chart_refresh_reuses_existing_series_instead_of_recreating_chart() -> None:
    _html, js, _css = _dashboard_assets()

    update_index = js.index("if (chartState.ready && chartState.key === chartKey")
    destroy_index = js.index("destroyTradingViewChart();", update_index)
    assert update_index < destroy_index
    assert "updateTradingViewChartData(candles);" in js
    assert "chartState.candleSeries.setData(chartPriceRows(candles));" in js
    assert "chartState.volumeSeries.setData(chartVolumeRows(candles));" in js
    assert "chartState.indicatorSeries[label]?.setData(indicatorSeries(candles, label, period));" in js
    assert "chartState.key = chartKey;" in js
    assert "chartState.key = `${state.uatCockpit.symbol}|${state.uatCockpit.timeframe}|${candles.at(-1)?.time}`" not in js


def test_autosize_feedback_loop_and_refresh_fitcontent_are_removed() -> None:
    _html, js, _css = _dashboard_assets()

    assert "autoSize: true" not in js
    assert "applyOptions({ autoSize: true })" not in js
    assert "new ResizeObserver(scheduleTradingViewResize)" in js
    assert "chart.resize(width, height)" in js
    assert js.count(".fitContent()") == 1
    assert "chartState.fitContentApplied = true;" in js


def test_live_polling_is_single_instance_and_can_be_disabled_by_query() -> None:
    _html, js, _css = _dashboard_assets()

    assert "LIVE_MARKET_REFRESH_MS = 15000" in js
    assert "if (!state.liveMarketData.enabled || state.liveMarketData.timer || typeof fetch !== \"function\") return;" in js
    assert "state.liveMarketData.timer = window.setInterval(refreshLiveMarketData, LIVE_MARKET_REFRESH_MS);" in js
    assert "disableLivePolling" in js
    assert "livePolling" in js
    assert "live_public_polling_disabled" in js
    assert "query_flag" in js


def test_public_read_only_boundaries_and_no_order_controls_remain() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    assert "https://api.hyperliquid-testnet.xyz/info" in js
    assert "https://api.hyperliquid.xyz/info" not in js
    assert "allMids" in js
    assert "candleSnapshot" in js
    assert "dashboard_live_chart_private_or_order_payload_forbidden" in js
    assert "No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used" in js

    forbidden = (
        "submit order button",
        "cancel order button",
        "retry button",
        "amend button",
        "approve order button",
        "market buy",
        "market sell",
        "paper/live toggle",
        "auto-trade toggle",
        "live trading approved",
    )
    for phrase in forbidden:
        assert phrase not in dashboard

    assert "order controls are disabled" in dashboard
    assert "live trading is not approved" in dashboard
