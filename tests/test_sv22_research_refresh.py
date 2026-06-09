from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.run_sv22_hyperliquid_research_refresh import (
    ACTIVE_TIMEFRAMES,
    DISABLED_TIMEFRAMES,
    FOUNDER_APPROVED_RESOLVED_SYMBOLS,
    NO_ORDER_FLAGS,
    SV22Dataset,
    SV22ReplayResult,
    WEEK2_REPLAY_STRATEGY_IDS,
    build_summary,
    latest_closed_timeframe,
    render_report,
)


def test_sv22_timeframe_policy_excludes_15m() -> None:
    assert ACTIVE_TIMEFRAMES == ("1h", "4h", "1d")
    assert DISABLED_TIMEFRAMES == ("15m",)
    assert "15m" not in ACTIVE_TIMEFRAMES


def test_sv22_founder_universe_is_23_resolved_symbols() -> None:
    assert len(FOUNDER_APPROVED_RESOLVED_SYMBOLS) == 23
    assert "TRX" in FOUNDER_APPROVED_RESOLVED_SYMBOLS
    assert "PEPE" not in FOUNDER_APPROVED_RESOLVED_SYMBOLS
    assert "OKB" not in FOUNDER_APPROVED_RESOLVED_SYMBOLS


def test_sv22_latest_closed_timeframe_floors_utc() -> None:
    value = datetime(2026, 6, 8, 10, 19, 55, tzinfo=UTC)

    assert latest_closed_timeframe(value, "1h").isoformat().endswith("10:00:00+00:00")
    assert latest_closed_timeframe(value, "4h").isoformat().endswith("08:00:00+00:00")
    assert latest_closed_timeframe(value, "1d").isoformat().endswith("00:00:00+00:00")


def test_sv22_summary_and_report_are_research_only() -> None:
    replay = SV22ReplayResult(
        strategy_id="money_flow_v1_2_baseline",
        strategy_label="Control / Baseline - Money Flow v1.2",
        symbol="BTC",
        timeframe="1h",
        fill_assumption="next_candle_open",
        period="SV2.2",
        status="completed",
        starting_equity="10000.00000000",
        ending_equity="10025.00000000",
        net_pnl="25.00000000",
        max_drawdown="10.00000000",
        max_drawdown_pct="0.00100000",
        trade_count=1,
        win_rate="1.00000000",
        profit_factor=None,
        largest_win="25.00000000",
        largest_loss="0.00000000",
        evidence_pack_path="reports/strategy_validation/example/20260608T101955Z",
        chart_data_path="reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data/example.json",
        reason_counts={"paper_opened": 1},
        reason_codes=("sv2_2_latest_public_mainnet_replay_completed",),
    )
    summary = build_summary(
        generated_at=datetime(2026, 6, 8, 10, 19, 55, tzinfo=UTC),
        run_timestamp="20260608T101955Z",
        datasets=[
            SV22Dataset(
                symbol="BTC",
                venue_symbol="BTC",
                timeframe="1h",
                rows=5000,
                earliest_close="2025-11-12T03:00:00Z",
                latest_close="2026-06-08T10:00:00Z",
                raw_path="/tmp/example.json",
                chart_data_path=None,
                status="refreshed",
                reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
            )
        ],
        fetch_public_data=True,
        chart_root=Path("reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data"),
        selected_symbols=["BTC"],
        timeframes=("1h",),
        replay_results=[replay],
    )
    report = render_report(summary)

    assert summary["phase"] == "SV2.2"
    assert summary["report"] == "sv2_2_hyperliquid_research_refresh"
    assert summary["status"] == "latest_replay_complete"
    assert summary["week2_replay_strategy_ids"] == list(WEEK2_REPLAY_STRATEGY_IDS)
    assert summary["completed_replay_count"] == 1
    assert summary["replay_results"][0]["strategy_id"] == "money_flow_v1_2_baseline"
    assert summary["boundaries"] == NO_ORDER_FLAGS
    assert summary["source"]["environment"] == "mainnet"
    assert summary["source"]["testnet_strategy_truth"] is False
    assert summary["dashboard_status"]["artifact_mode"] == "latest_public_mainnet_week2_strategy_replay"
    assert summary["dashboard_status"]["not_a_replay_strategy"] is True
    assert "SV2.2 public candle refresh" not in report
    assert "No strategy is production-approved." in report
    assert "No live trading is approved." in report


def test_sv22_committed_summary_exists_and_is_current_refresh_contract() -> None:
    summary = json.loads(Path("docs/sv2_2_hyperliquid_research_refresh_summary.json").read_text(encoding="utf-8"))
    report = Path("docs/sv2_2_hyperliquid_research_refresh.md").read_text(encoding="utf-8")

    assert summary["phase"] == "SV2.2"
    assert summary["timeframes"] == ["1h", "4h", "1d"]
    assert summary["disabled_timeframes"] == ["15m"]
    assert summary["refreshed_dataset_count"] == 69
    assert summary["completed_replay_count"] == 414
    assert summary["replay_result_count"] == 414
    assert set(summary["week2_replay_strategy_ids"]) == set(WEEK2_REPLAY_STRATEGY_IDS)
    assert {row["strategy_id"] for row in summary["replay_results"]} == set(WEEK2_REPLAY_STRATEGY_IDS)
    assert {row["fill_assumption"] for row in summary["replay_results"]} == {"next_candle_open", "next_candle_close"}
    assert {row["timeframe"] for row in summary["replay_results"]} == {"1h", "4h", "1d"}
    assert "sv2_2_public_candle_refresh" not in json.dumps(summary)
    assert summary["boundaries"]["calls_order_endpoints"] is False
    assert summary["boundaries"]["calls_private_or_signed_endpoints"] is False
    assert "SV2.2 Hyperliquid Latest Public-Mainnet Replay Refresh" in report
    assert "SV2.2 is not itself a replay strategy" in report


def test_dashboard_loads_sv22_and_defaults_to_historical_replay() -> None:
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    nav = html[html.index('<nav class="view-tabs"') : html.index("</nav>", html.index('<nav class="view-tabs"'))]

    assert 'data-view="historical-replay" aria-selected="true"' in nav
    assert 'data-view="paper-observation" aria-selected="false"' in nav
    assert 'activeView: "historical-replay"' in js
    assert 'strategyId: "money_flow_v1_2_baseline"' in js
    assert 'period: "SV2.2"' in js
    assert 'fillAssumption: "next_candle_open"' in js
    assert "DEFAULT_SV22_RESEARCH_REFRESH_SUMMARY_FILES" in js
    assert "sv2_2_hyperliquid_research_refresh_summary.json" in js
    assert "sv2_2_week2_replay_dashboard_chart_data" in js
    assert "sv22LatestReplayRows" in js
    assert "sv2_2_public_candle_refresh" not in js
    assert "sv2_2_refresh_chart_data_not_canonical_evidence" not in js
