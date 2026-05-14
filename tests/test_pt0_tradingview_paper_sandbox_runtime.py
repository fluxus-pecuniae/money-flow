from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from services.uat.pt0_runtime import (
    PT0_APPROVAL_STATEMENT,
    PT0_REPORT_NAME,
    PT0RuntimeLimits,
    PT0RouteCandidate,
    PT0SizingPolicy,
    build_pt0_paper_equity_ledger,
    build_pt0_paper_universe,
    evaluate_pt0_route_candidate,
)


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


def _summary() -> dict:
    return json.loads(Path("docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json").read_text())


def _dashboard() -> str:
    return "\n".join(
        [
            Path("apps/dashboard/index.html").read_text(encoding="utf-8"),
            Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8"),
            Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8"),
        ]
    )


def test_pt0_approval_statements_and_report_exist() -> None:
    summary = _summary()
    report = Path("docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md").read_text()

    assert summary["report"] == PT0_REPORT_NAME
    assert summary["approval_statements"]["paper_trading"] == PT0_APPROVAL_STATEMENT
    assert "PAPER TRADING IS APPROVED." in report
    assert "BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED." in report
    assert "LIVE TRADING IS NOT APPROVED." in report
    assert "REAL-CAPITAL TRADING IS NOT APPROVED." in report
    assert "PT0.1 — Supervised Top-20 Paper/Sandbox Runtime Week" in report


def test_tradingview_lightweight_charts_local_bundle_is_used() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    bundle = Path("apps/dashboard/vendor/lightweight-charts.standalone.production.js").read_text(encoding="utf-8")
    package = json.loads(Path("apps/dashboard/vendor/package.json").read_text())

    assert package["name"] == "lightweight-charts"
    assert package["version"] == "5.2.0"
    assert "TradingView Lightweight Charts™ v5.2.0" in bundle
    assert "Apache License 2.0" in bundle
    assert "vendor/lightweight-charts.standalone.production.js" in html
    assert "LightweightCharts" in js
    assert "CandlestickSeries" in js
    assert "CANDLE_UP_COLOR" in js
    assert "CANDLE_DOWN_COLOR" in js
    assert "CHART_BACKGROUND_COLOR" in js
    assert "borderUpColor: chartColors.candleBorder" in js
    assert "borderDownColor: chartColors.candleBorder" in js
    assert "HistogramSeries" in js
    assert "LineSeries" in js
    assert "createSeriesMarkers" in js
    assert "s.tradingview.com" not in html + js
    assert "tv.js" not in html + js


def test_dashboard_uses_candlesticks_markers_and_pt0_summary() -> None:
    dashboard = _dashboard()

    assert "DEFAULT_PT0_SUMMARY_FILES" in dashboard
    assert "pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json" in dashboard
    assert "tradingview-lightweight-chart" in dashboard
    assert "TradingView Lightweight Charts" in dashboard
    assert "green marker: paper would-open" in dashboard
    assert "red marker: paper would-close" in dashboard
    assert "green marker: sandbox order accepted/open" in dashboard
    assert "red marker: sandbox cancel" in dashboard
    assert "PAPER TRADING IS APPROVED FOR HYPERLIQUID TESTNET/SANDBOX ONLY" in dashboard
    assert "BROADER TOP-20 SUPPORTED PAPER/SANDBOX TRADING IS APPROVED" in dashboard


def test_top20_universe_and_unsupported_assets_are_explicit() -> None:
    summary = _summary()
    universe = summary["paper_universe"]
    by_symbol = {row["symbol"]: row for row in universe}

    assert [row["symbol"] for row in universe] == WATCHLIST
    assert {row["symbol"] for row in universe if row["paper_eligibility"] == "blocked_not_supported_on_testnet"} == {
        "XRP",
        "TRX",
        "UNI",
    }
    assert by_symbol["ETH"]["paper_eligibility"] == "eligible"
    assert "paper_symbol_not_supported_on_testnet" in by_symbol["XRP"]["reason_codes"]


def test_paper_equity_and_sizing_use_current_internal_equity() -> None:
    ledger = build_pt0_paper_equity_ledger(realized_pnl=Decimal("-100"), unrealized_pnl=Decimal("25"))
    policy = PT0SizingPolicy()
    summary = _summary()

    assert summary["paper_equity"]["initial_paper_equity"] == "10000"
    assert summary["paper_equity"]["current_paper_equity"] == "10000"
    assert ledger.current_paper_equity == Decimal("9925")
    assert ledger.realized_equity == Decimal("9900")
    assert policy.sizing_equity(ledger) == Decimal("9900")
    assert policy.sizing_equity(ledger) != Decimal("10000")
    assert summary["sizing_policy"]["use_static_initial_equity"] is False


def test_balance_polling_is_60_second_sandbox_private_read_only_only() -> None:
    polling = _summary()["balance_position_polling"]

    assert polling["poll_interval_seconds"] == 60
    assert polling["source"] == "sandbox_private_read_only"
    assert polling["not_live_account"] is True
    assert polling["order_endpoints_called"] is False
    assert polling["cancel_amend_retry_endpoints_called"] is False


def test_route_candidate_risk_limits_and_default_routing_lockout() -> None:
    universe = build_pt0_paper_universe(precision_validation=_summary()["paper_universe"])
    ledger = build_pt0_paper_equity_ledger()

    default_block = evaluate_pt0_route_candidate(PT0RouteCandidate(symbol="ETH", order_notional=Decimal("15")))
    over_notional = evaluate_pt0_route_candidate(
        PT0RouteCandidate(symbol="ETH", order_notional=Decimal("150"), routing_enabled=True),
        ledger=ledger,
        universe_assets=universe,
    )
    unsupported = evaluate_pt0_route_candidate(
        PT0RouteCandidate(symbol="XRP", order_notional=Decimal("10"), routing_enabled=True),
        universe_assets=universe,
    )

    assert default_block.allowed is False
    assert "pt0_sandbox_order_routing_disabled_by_default" in default_block.reason_codes
    assert "pt0_max_order_notional_exceeded" in over_notional.reason_codes
    assert "paper_symbol_not_supported_on_testnet" in unsupported.reason_codes
    assert default_block.calls_exchange is False
    assert default_block.creates_order_intent is False
    assert default_block.creates_submitted_order is False


def test_sor_fanout_target_reselection_and_kill_switch_block() -> None:
    decision = evaluate_pt0_route_candidate(
        PT0RouteCandidate(
            symbol="ETH",
            order_notional=Decimal("10"),
            routing_enabled=True,
            sor_requested=True,
            fanout_requested=True,
            target_reselection_requested=True,
            cross_venue_requested=True,
            kill_switch_enabled=True,
            live_endpoint_access=True,
        )
    )

    assert "pt0_sor_forbidden" in decision.reason_codes
    assert "pt0_top20_broad_fanout_forbidden" in decision.reason_codes
    assert "pt0_target_reselection_forbidden" in decision.reason_codes
    assert "pt0_cross_venue_routing_forbidden" in decision.reason_codes
    assert "pt0_kill_switch_enabled" in decision.reason_codes
    assert "pt0_live_endpoint_forbidden" in decision.reason_codes


def test_no_order_controls_or_live_endpoint_are_added() -> None:
    dashboard = _dashboard().lower()
    summary = _summary()

    forbidden = (
        "submit order button",
        "cancel order button",
        "retry button",
        "amend button",
        "approve order button",
        "market buy",
        "market sell",
        "auto-trade toggle",
        "live trading approved",
        "real-capital trading approved",
    )
    for phrase in forbidden:
        assert phrase not in dashboard

    assert "https://api.hyperliquid.xyz" not in dashboard
    assert summary["side_effect_flags"]["live_endpoint_called"] is False
    assert summary["side_effect_flags"]["sandbox_orders_submitted_by_pt0"] is False
    assert summary["side_effect_flags"]["order_controls_added"] is False


def test_runtime_limits_are_documented() -> None:
    limits = PT0RuntimeLimits()
    summary = _summary()["runtime_limits"]

    assert limits.max_order_notional_pct_of_paper_equity == Decimal("0.01")
    assert summary["max_order_notional_absolute"] == "100"
    assert summary["max_orders_per_day"] == 5
    assert summary["max_open_positions"] == 3
    assert summary["max_open_positions_per_symbol"] == 1
    assert summary["allowed_venue"] == "hyperliquid"
    assert summary["live_endpoint_access"] is False
