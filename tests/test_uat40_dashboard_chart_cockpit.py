from __future__ import annotations

import json
from pathlib import Path


WATCHLIST = [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "ZEC",
    "BNB",
    "SUI",
    "TON",
    "DOGE",
    "TRX",
    "LAYER",
    "CHIP",
    "UNI",
    "ONDO",
    "AAVE",
]


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def test_uat_chart_cockpit_tab_and_sections_exist() -> None:
    html, js, css = _dashboard_assets()
    dashboard = f"{html}\n{js}"
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]

    assert "data-view=\"uat-cockpit\"" not in nav
    assert "data-view-panel=\"uat-cockpit\"" in html
    assert "UAT Chart Cockpit" in html
    assert "Live UAT Charts" in html
    assert "uat-workstation-grid" in html
    assert "uat-watchlist-table" in html
    assert "uat-market-data-coverage" in html
    assert "uat-price-chart" in html
    assert "uat-indicator-panel" in html
    assert "uat-marker-panel" in html
    assert "uat-order-book-panel" in html
    assert "uat-market-info-panel" in html
    assert "uat-signal-context-panel" in html
    assert "uat-risk-context-panel" in html
    assert "uat-route-status-card" in html
    assert "uat-equity-source-card" in html
    assert "uat-cockpit-routed-orders-table" in html
    assert "uat-shadow-signal-overlay" in html
    assert "renderUatCockpit" in js
    assert "UAT_WATCHLIST_SYMBOLS" in js
    assert ".exchange-chart-shell" in css
    assert ".uat-left-rail" in css
    assert ".uat-right-rail" in css
    assert ".uat-bottom-blotter" in css
    assert ".marker-pill.green" in css
    assert ".marker-pill.red" in css
    assert "docs/uat2_shadow_strategy_top20_observation_summary.json" in dashboard
    assert "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json" in dashboard
    assert "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json" in dashboard
    assert "docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json" in dashboard


def test_uat_watchlist_assets_are_paper_sandbox_eligible_and_not_live_approved() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"

    for symbol in WATCHLIST:
        assert f"\"{symbol}\"" in js

    assert "paper/sandbox only" in dashboard
    assert "active ETH sandbox route; approval and risk gates required" in dashboard
    assert "paper/sandbox eligible under PT0 gates" in dashboard
    assert "PAPER TRADING IS APPROVED FOR HYPERLIQUID TESTNET/SANDBOX ONLY" in dashboard
    assert "Live trading is not approved" in dashboard
    assert "BROADER TOP-20 SUPPORTED PAPER/SANDBOX TRADING IS APPROVED" in dashboard


def test_uat_chart_indicators_and_marker_semantics_are_safe() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"

    for label in ("EMA5", "EMA10", "SMA20", "RSI", "MACD", "MACD signal", "MACD histogram"):
        assert label in dashboard

    assert "indicator_unavailable_insufficient_history" in dashboard
    assert "green marker: shadow would-open" in dashboard
    assert "green marker: sandbox order accepted/open" in dashboard
    assert "red marker: sandbox cancel" in dashboard
    assert "not actual trade" in dashboard
    assert "sandbox/testnet lifecycle probe; not live; not performance validation" in dashboard
    assert "same_candle_close_research_only remains research-only" in dashboard


def test_routed_orders_tab_renders_uat34_lifecycle_fields() -> None:
    payload = json.loads(Path("docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json").read_text())
    record = payload["ledger_records"][0]
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"

    assert "Routed Orders" in html
    assert "fixed_target_hyperliquid_testnet_eth" in json.dumps(payload)
    assert record["lifecycle_status"] == "canceled"
    assert record["cancel_status"] == "success"
    assert record["reconciliation_status"] == "completed"
    assert record["open_order_remains"] is False
    assert record["selected_equity_source"] == "standard_perp_clearinghouse"
    assert record["sandbox_labels"]["sandbox"] is True
    assert record["sandbox_labels"]["not_live"] is True
    assert record["sandbox_labels"]["not_paper"] is True
    assert "lifecycle_status" in dashboard
    assert "sanitized_exchange_response" in dashboard


def test_market_data_coverage_uses_public_read_only_local_summaries() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"

    assert "refreshed_public_read_only_local_json" in dashboard
    assert "market_data_unavailable" in dashboard
    assert "public_read_only / local_summary_json" in dashboard
    assert "PT0/UAT4.2 local summary JSON" in dashboard
    assert "No API keys, private order endpoints, signed order endpoints, order endpoints, or live endpoints are used" in dashboard


def test_dashboard_has_no_order_or_paper_live_controls() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    forbidden = (
        "submit order button",
        "cancel order button",
        "retry button",
        "amend button",
        "approve order button",
        "route order button",
        "auto-trade toggle",
        "paper/live toggle",
        "live trading approved",
        "order submission approved",
        "profitable",
        "proven",
    )
    for phrase in forbidden:
        assert phrase not in dashboard

    assert "order controls are disabled" in dashboard
    assert "no order controls" in dashboard
