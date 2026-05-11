from __future__ import annotations

import json
from pathlib import Path


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def test_uat2_dashboard_tab_loads_summary_json_and_required_sections() -> None:
    html, js, css = _dashboard_assets()
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]

    assert "data-view=\"uat-shadow\"" not in nav
    assert "data-view-panel=\"uat-shadow\"" in html
    assert "UAT2 Shadow Run" in html
    assert "uat-summary-cards" in html
    assert "uat-signal-matrix" in html
    assert "uat-would-open-table" in html
    assert "uat-no-trade-overall" in html
    assert "uat-eth-candidate-card" in html
    assert "uat-timing-panel" in html
    assert "uat-drawdown-card" in html
    assert "uat3-readiness-panel" in html
    assert "uat3-design-panel" in html
    assert "uat-boundary-panel" in html
    assert "uat-routed-orders-summary" in html
    assert "uat-routed-orders-table" in html
    assert "uat2_shadow_strategy_top20_observation_summary.json" in js
    assert "uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json" in js
    assert "uat2_shadow_summary" in js
    assert "uat34_routed_orders_summary" in js
    assert "renderUatDashboard" in js
    assert "renderUatRoutedOrders" in js
    assert ".boundary-grid" in css
    assert ".uat-filter-grid" in css


def test_uat2_dashboard_summary_json_has_expected_counts_and_boundaries() -> None:
    payload = json.loads(Path("docs/uat2_shadow_strategy_top20_observation_summary.json").read_text())
    records = payload["audit_records"]
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["signal_status"]] = status_counts.get(record["signal_status"], 0) + 1

    assert len(records) == 45
    assert status_counts["would_open"] == 11
    assert status_counts["no_trade"] == 34
    assert len(payload["symbols_evaluated"]) == 15
    assert payload["components_evaluated"] == ["sleeve_15m", "sleeve_1h", "sleeve_4h"]
    assert payload["boundary_flags"]["api_keys_used"] is False
    assert payload["boundary_flags"]["private_endpoints_called"] is False
    assert payload["boundary_flags"]["signed_endpoints_called"] is False
    assert payload["boundary_flags"]["order_endpoints_called"] is False
    assert payload["boundary_flags"]["orders_submitted"] is False
    assert payload["boundary_flags"]["strategy_decisions_created"] is False
    assert payload["boundary_flags"]["order_intents_created"] is False
    assert payload["boundary_flags"]["submitted_orders_created"] is False


def test_uat2_dashboard_exposes_would_open_warning_timing_and_drawdown_truth() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    assert "would-open means the shadow strategy conditions were met" in dashboard
    assert "no order intent was created" in dashboard
    assert "no order was submitted" in dashboard
    assert "next_candle_open" in dashboard
    assert "next_candle_close" in dashboard
    assert "same_candle_close_research_only" in dashboard
    assert "excluded from uat2 primary action assumptions" in dashboard
    assert "not live account drawdown" in dashboard
    assert "this is not performance validation" in dashboard
    assert "uat3 is blocked" in dashboard
    assert "uat3.0 design/readiness only" in dashboard
    assert "actual sandbox order submission is not approved" in dashboard
    assert "sandbox runtime policy" in dashboard
    assert "fixture/implemented" in dashboard
    assert "approval scope validator" in dashboard
    assert "risk gate evaluator" in dashboard
    assert "submit lease duplicate-prevention" in dashboard
    assert "unified dry-run preflight" in dashboard
    assert "runtime full-blocker propagation" in dashboard
    assert "numeric edge-case validation" in dashboard
    assert "artifact label boundary enforcement" in dashboard
    assert "dry-run executable gate service" in dashboard
    assert "global orders disabled; sandbox orders separately gated" in dashboard
    assert "uat routed orders" in dashboard
    assert "sandbox/testnet routed-order ledger visibility only" in dashboard
    assert "the dashboard has no order controls" in dashboard
    assert "no interactive approval action exists" in dashboard


def test_uat2_dashboard_eth_candidate_and_no_trade_reasons_are_visible() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"
    payload = json.loads(Path("docs/uat2_shadow_strategy_top20_observation_summary.json").read_text())
    payload_text = json.dumps(payload)

    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in dashboard
    assert "Hyperliquid ETH USDC perpetual / sleeve_1h" in dashboard
    assert "macd_not_constructive" in payload_text
    for reason in (
        "bearish_alignment",
        "rsi_not_constructive",
        "overextended_rsi",
        "entry_quality_not_constructive",
    ):
        assert reason in payload_text


def test_uat2_dashboard_has_no_order_enabling_approval_button_or_forbidden_language() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}".lower()

    assert "create approval" not in dashboard
    assert "approval button" not in dashboard
    assert "enable orders" not in dashboard
    assert "submit sandbox order" not in dashboard
    assert "paper trading is approved for hyperliquid testnet/sandbox only" in dashboard
    assert "live trading approved" not in dashboard
    assert "order submission approved" not in dashboard
    assert "profitable" not in dashboard
    assert "proven" not in dashboard
