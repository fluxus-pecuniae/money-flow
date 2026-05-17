from __future__ import annotations

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


def _assets() -> tuple[str, str, str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    design = Path("apps/dashboard/DESIGN.md").read_text(encoding="utf-8")
    root_design = Path("DESIGN.md").read_text(encoding="utf-8")
    return html, js, css, design, root_design


def test_design_doc_is_rebuilt_and_root_design_points_to_dashboard_doc() -> None:
    _html, _js, _css, design, root_design = _assets()

    assert "# Money Flow Founder Dashboard Design" in design
    assert "The dashboard is not an order-entry terminal." in design
    assert "market list on the left" in design
    assert "central TradingView-style chart region" in design
    assert "right-side order book / market context / risk context" in design
    assert "bottom blotter" in design
    assert "The dashboard is not an order-entry terminal." in design
    assert "Current operating surface: `Paper Trading` dashboard tab" in design
    assert "fixed 25 USDC Hyperliquid testnet transport is baseline-only" in design
    assert "Live trading: not approved" in design
    assert "[`apps/dashboard/DESIGN.md`](apps/dashboard/DESIGN.md)" in root_design


def test_exchange_style_layout_sections_exist() -> None:
    html, js, css, _design, _root_design = _assets()
    dashboard = f"{html}\n{js}\n{css}"

    assert "uat-topbar" in html
    assert "uat-left-rail" in html
    assert "uat-center-cockpit" in html
    assert "uat-right-rail" in html
    assert "uat-bottom-blotter" in html
    assert "uat-order-book-panel" in html
    assert "uat-market-info-panel" in html
    assert "uat-signal-context-panel" in html
    assert "uat-risk-context-panel" in html
    assert "exchange-chart-shell" in dashboard
    assert "renderUatRightRail" in js
    assert "renderUatBottomTabs" in js
    assert "renderUatLifecyclePanel" in js
    assert "renderUatAuditPanel" in js


def test_bottom_blotter_tabs_and_lifecycle_visibility_exist() -> None:
    html, js, _css, _design, _root_design = _assets()
    dashboard = f"{html}\n{js}"

    assert "data-uat-bottom-tab=\"routed\"" in html
    assert "data-uat-bottom-tab=\"shadow\"" in html
    assert "data-uat-bottom-tab=\"balances\"" in html
    assert "data-uat-bottom-tab=\"lifecycle\"" in html
    assert "data-uat-bottom-tab=\"audit\"" in html
    assert "accepted/open -> canceled -> reconciled lifecycle" in js
    assert "order_accepted_open" in dashboard
    assert "cancel status" in dashboard
    assert "open order remains" in dashboard


def test_watchlist_assets_are_visible_observation_only_and_filtered() -> None:
    _html, js, _css, _design, _root_design = _assets()

    for symbol in WATCHLIST:
        assert f"\"{symbol}\"" in js

    assert "watchlistFilter" in js
    assert "Would-open" in js
    assert "No-trade" in js
    assert "Active sandbox route" in js
    assert "Missing data" in js
    assert "paper/sandbox only" in js
    assert "paper/sandbox eligible under PT0 gates" in js
    assert "active ETH sandbox route; approval and risk gates required" in js


def test_indicators_markers_and_right_rail_context_are_safe() -> None:
    html, js, _css, _design, _root_design = _assets()
    dashboard = f"{html}\n{js}"

    for label in ("EMA5", "EMA10", "SMA20", "RSI", "MACD", "MACD signal", "MACD histogram"):
        assert label in dashboard

    assert "green marker: shadow would-open" in dashboard
    assert "green marker: sandbox order accepted/open" in dashboard
    assert "red marker: sandbox cancel" in dashboard
    assert "not actual trade" in dashboard
    assert "not performance validation" in dashboard
    assert "order_book_unavailable" in dashboard
    assert "public_read_only" in dashboard
    assert "Private endpoint" in dashboard
    assert "not used" in dashboard


def test_no_order_private_or_paper_live_controls_are_present() -> None:
    html, js, _css, _design, _root_design = _assets()
    dashboard = f"{html}\n{js}".lower()

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
        "order submission approved",
        "profitable",
        "proven",
    )
    for phrase in forbidden:
        assert phrase not in dashboard

    assert "paper trading is approved for hyperliquid testnet/sandbox only" in dashboard
    assert "live trading is not approved" in dashboard
    assert "order controls are disabled" in dashboard
    assert "broader top-20 supported paper/sandbox trading is approved" in dashboard
