from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from services.uat.live_monitor import (
    UAT42_BALANCE_POLL_INTERVAL_SECONDS,
    UAT42_INITIAL_PAPER_EQUITY,
    UAT42_WATCHLIST,
    UAT42BalancePollingPolicy,
    UAT42Candle,
    UAT42PublicMarketDataPolicy,
    UAT42SizingPolicy,
    build_paper_equity_ledger,
    build_uat42_monitor_summary,
    compute_uat42_indicators,
    evaluate_uat42_public_market_payload,
)
from services.uat.public_read_only import hyperliquid_info_payload


def _dashboard_assets() -> tuple[str, str, str]:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    css = Path("apps/dashboard/evidence-dashboard.css").read_text(encoding="utf-8")
    return html, js, css


def _summary() -> dict:
    return json.loads(Path("docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json").read_text())


def test_live_public_market_data_policy_allows_public_info_only() -> None:
    policy = UAT42PublicMarketDataPolicy()
    allowed, reasons = evaluate_uat42_public_market_payload(hyperliquid_info_payload("allMids"), policy=policy)
    blocked, blocked_reasons = evaluate_uat42_public_market_payload(
        {"type": "clearinghouseState", "user": "0x0000000000000000000000000000000000000000"},
        policy=policy,
    )

    assert allowed is True
    assert reasons == ()
    assert blocked is False
    assert "uat42_public_read_only_payload_required" in blocked_reasons


def test_summary_covers_uat_watchlist_and_public_read_only_market_data() -> None:
    summary = _summary()
    market_rows = summary["market_data"]
    symbols = {row["symbol"] for row in market_rows}

    assert summary["report"] == "uat4_2_live_market_dashboard_and_paper_equity_monitor"
    assert tuple(summary["watchlist"]) == UAT42_WATCHLIST
    assert symbols == set(UAT42_WATCHLIST)
    assert all(row["endpoint_category"] == "public_read_only" for row in market_rows)
    assert all(row["public_read_only_confirmation"] is True for row in market_rows)
    assert all(row["private_signed_order_endpoints_called"] is False for row in market_rows)


def test_indicators_are_computed_and_insufficient_history_is_explicit() -> None:
    summary = _summary()
    indicator = summary["indicator_snapshots"][0]
    short_candles = tuple(
        UAT42Candle(
            timestamp_utc=f"2026-05-11T00:0{index}:00Z",
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100") + Decimal(index),
            volume=Decimal("1"),
        )
        for index in range(4)
    )
    short_snapshot = compute_uat42_indicators(short_candles, symbol="ETH", timeframe="1h")

    for label in ("EMA5", "EMA10", "SMA20", "RSI", "MACD", "MACD signal", "MACD histogram"):
        assert label in indicator

    assert short_snapshot.ema5.enough_history is False
    assert short_snapshot.ema5.reason == "indicator_unavailable_insufficient_history"
    assert short_snapshot.macd_histogram.enough_history is False
    assert short_snapshot.macd_histogram.reason == "indicator_unavailable_insufficient_history"


def test_strategy_scanner_is_observation_only_and_creates_no_artifacts() -> None:
    summary = _summary()
    records = summary["strategy_scanner"]["records"]

    assert records
    assert "StrategyDecision" in summary["strategy_scanner"]["forbidden_outputs"]
    assert "OrderIntent" in summary["strategy_scanner"]["forbidden_outputs"]
    assert "SubmittedOrder" in summary["strategy_scanner"]["forbidden_outputs"]
    assert all(row["source"] == "paper_observation_signal" for row in records)
    assert all(row["creates_strategy_decision"] is False for row in records)
    assert all(row["creates_order_intent"] is False for row in records)
    assert all(row["creates_prepared_order"] is False for row in records)
    assert all(row["creates_submitted_order"] is False for row in records)
    assert all(row["creates_executable_approval"] is False for row in records)


def test_balance_polling_policy_is_60_second_sandbox_private_read_only_only() -> None:
    policy = UAT42BalancePollingPolicy()
    allowed, reasons = policy.evaluate()
    blocked_policy = UAT42BalancePollingPolicy(order_endpoints_called=True)
    blocked, blocked_reasons = blocked_policy.evaluate()
    summary = _summary()

    assert policy.poll_interval_seconds == UAT42_BALANCE_POLL_INTERVAL_SECONDS
    assert allowed is True
    assert reasons == ()
    assert blocked is False
    assert "uat42_balance_poll_order_endpoint_forbidden" in blocked_reasons
    assert "sandbox_order_submission" in policy.forbidden_categories
    assert summary["balance_position_polling"]["poll_interval_seconds"] == 60
    assert summary["balance_position_polling"]["sandbox_account_confirmation"]["not_live_account"] is True
    assert summary["balance_position_polling"]["sandbox_account_confirmation"]["private_order_endpoints_called"] is False


def test_internal_paper_equity_starts_at_10000_and_updates_from_pnl() -> None:
    flat = build_paper_equity_ledger()
    changed = build_paper_equity_ledger(realized_pnl=Decimal("-250"), unrealized_pnl=Decimal("75"))
    policy = UAT42SizingPolicy()

    assert flat.initial_paper_equity == UAT42_INITIAL_PAPER_EQUITY
    assert flat.current_paper_equity == Decimal("10000")
    assert changed.current_paper_equity == Decimal("9825")
    assert changed.realized_equity == Decimal("9750")
    assert policy.sizing_equity(changed) == Decimal("9750")
    assert policy.sizing_equity(changed) != changed.initial_paper_equity


def test_dashboard_loads_uat42_summary_and_renders_live_monitor_surfaces() -> None:
    html, js, css = _dashboard_assets()
    dashboard = f"{html}\n{js}\n{css}"

    assert "DEFAULT_UAT42_SUMMARY_FILES" in js
    assert "uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json" in js
    assert "uat-paper-equity-card" in html
    assert "uat-balance-poll-card" in html
    assert "uat-positions-panel" in html
    assert "paper observation scanner" in js
    assert "Internal Paper Equity" in js
    assert "sandbox_private_read_only" in js
    assert "60 seconds" in js
    assert "UAT4.2 local refresh JSON" in html
    assert ".market-change.positive" in css


def test_dashboard_live_charting_polls_public_testnet_only() -> None:
    html, js, _css = _dashboard_assets()

    assert "uat-live-chart-status" in html
    assert "https://api.hyperliquid-testnet.xyz/info" in js
    assert "LIVE_MARKET_REFRESH_MS = 15000" in js
    assert "allMids" in js
    assert "candleSnapshot" in js
    assert "live_public_read_only_connected" in js
    assert "hyperliquid_testnet_public_read_only_browser_poll" in js
    assert "dashboard_live_chart_private_or_order_payload_forbidden" in js
    assert "No API keys, private order endpoints, signed order endpoints, or live endpoints are used" in js
    assert "order endpoints are also not used" in js
    assert "https://api.hyperliquid.xyz/info" not in js


def test_dashboard_watchlist_indicators_markers_and_no_order_controls() -> None:
    html, js, _css = _dashboard_assets()
    dashboard = f"{html}\n{js}"
    lowered = dashboard.lower()

    for symbol in UAT42_WATCHLIST:
        assert f"\"{symbol}\"" in js
    for label in ("EMA5", "EMA10", "SMA20", "RSI", "MACD", "MACD signal", "MACD histogram"):
        assert label in dashboard

    assert "observation only" in dashboard
    assert "not approved for orders" in dashboard
    assert "green marker: paper observation would-open" in dashboard
    assert "red marker: paper observation would-close" in dashboard
    assert "green marker: shadow would-open, not actual trade" in dashboard
    assert "red marker: sandbox cancel" in dashboard
    assert "paper-equity simulation" in dashboard

    forbidden = (
        "submit order button",
        "cancel order button",
        "retry button",
        "amend button",
        "approve order button",
        "paper/live toggle",
        "auto-trade toggle",
        "paper trading approved",
        "live trading approved",
    )
    for phrase in forbidden:
        assert phrase not in lowered

    assert "order controls are disabled" in lowered
    assert "live trading is not approved" in lowered


def test_uat42_report_and_pt0_roadmap_are_captured() -> None:
    report = Path("docs/uat4_2_live_market_dashboard_and_paper_equity_monitor.md").read_text()
    roadmap = Path("money-flow/00 Maps/UAT Roadmap.md").read_text()

    assert "UAT4.2 Live Market Dashboard + Paper-Equity Runtime Monitor" in report
    assert "Internal 10,000 USDC Paper-Equity Ledger" in report
    assert "60-second poll policy" in report
    assert "No-order-control confirmation" in report
    assert "PT0" in report
    assert "PT0 — Approval-Gated Paper/Sandbox Trading Runtime" in roadmap
