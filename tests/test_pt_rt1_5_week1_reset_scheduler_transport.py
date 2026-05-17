from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts.run_pt_rt1_paper_observation import _build_pt_rt1_5_testnet_order_lifecycle_rows
from services.paper_runtime.pt_rt1 import (
    PT_RT1_5_ACTIVE_REVIEW_START_UTC,
    PT_RT1_5_ACTIVE_TIMEFRAMES,
    PT_RT1_5_ARCHIVED_RUNTIME_SCOPES,
    PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS,
    PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
    PT_RT1_5_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_RUNTIME_SCOPE,
    PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_INFO_URL,
    PT_RT15BaselineTestnetOrderPolicy,
    PT_RT15TestnetOrderCandidate,
    build_pt_rt1_5_scheduler_status,
    build_pt_rt1_summary,
)


def test_pt_rt1_5_active_week_reset_scope_and_timeframes() -> None:
    summary = build_pt_rt1_summary()

    assert PT_RT1_5_RUNTIME_SCOPE == "pt_rt1_5_week1_active"
    assert PT_RT1_5_RUNTIME_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_5_week1_active"
    assert PT_RT1_5_ACTIVE_TIMEFRAMES == ("1h", "4h", "1d")
    assert "pt_rt1_1c_24h_dry_run" in PT_RT1_5_ARCHIVED_RUNTIME_SCOPES
    assert summary["pt_rt1_5_active_review_scope"]["default_show_archived_rows"] is False
    assert summary["pt_rt1_5_active_review_scope"]["old_runtime_rows_archived_not_deleted"] is True
    assert summary["pt_rt1_5_active_review_scope"]["active_review_start_utc"] == PT_RT1_5_ACTIVE_REVIEW_START_UTC


def test_pt_rt1_5_scheduler_waits_for_grace_and_deduplicates_closed_candles() -> None:
    before_grace = build_pt_rt1_5_scheduler_status(
        now=datetime(2026, 5, 17, 14, 0, 30, tzinfo=UTC),
        last_evaluated_closed_candle_by_timeframe={"1h": "2026-05-17T13:00:00Z"},
    )
    after_grace = build_pt_rt1_5_scheduler_status(now=datetime(2026, 5, 17, 14, 2, 0, tzinfo=UTC))
    duplicate = build_pt_rt1_5_scheduler_status(
        now=datetime(2026, 5, 17, 14, 2, 0, tzinfo=UTC),
        last_evaluated_closed_candle_by_timeframe={"1h": "2026-05-17T14:00:00Z"},
    )

    assert PT_RT1_5_CANDLE_CLOSE_GRACE_SECONDS["1h"] == 90
    assert before_grace["timeframes"]["1h"]["is_due"] is False
    assert "market_refresh_only_no_signal_evaluation" in before_grace["timeframes"]["1h"]["reason_codes"]
    assert after_grace["timeframes"]["1h"]["is_due"] is True
    assert after_grace["timeframes"]["1h"]["closed_candle_time"] == "2026-05-17T14:00:00Z"
    assert duplicate["timeframes"]["1h"]["is_due"] is False
    assert "duplicate_candle_signal_ignored" in duplicate["timeframes"]["1h"]["reason_codes"]


def test_pt_rt1_5_baseline_only_testnet_policy_builds_fixed_25usdc_shape() -> None:
    policy = PT_RT15BaselineTestnetOrderPolicy()
    result = policy.evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            synthetic_signal_notional=Decimal("10000"),
            fixed_notional=Decimal("25"),
            price=Decimal("2500"),
        )
    )

    assert result.eligible is True
    assert result.order_shape is not None
    assert result.order_shape["notional_usdc"] == "25"
    assert result.order_shape["testnet_fixed_notional"] == "25"
    assert result.order_shape["sizing_source"] == "fixed_testnet_plumbing_notional"
    assert result.order_shape["synthetic_signal_notional"] == "10000"
    assert result.order_shape["testnet_fills_update_strategy_pnl"] is False
    assert "vaultAddress" not in result.order_shape
    assert result.order_shape["action"]["orders"][0]["t"]["limit"]["tif"] == "Alo"


def test_pt_rt1_5_testnet_policy_blocks_candidates_15m_duplicates_kill_switch_and_live_url() -> None:
    policy = PT_RT15BaselineTestnetOrderPolicy()
    base = PT_RT15TestnetOrderCandidate(
        order_transport_enabled=True,
        kill_switch=False,
        approval_text=PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
        base_url=PT_RT1_TESTNET_INFO_URL,
    )

    candidate = policy.evaluate(base.__class__(**{**base.__dict__, "lane_id": "avoid_low_rolling_range_50"}))
    fifteen = policy.evaluate(base.__class__(**{**base.__dict__, "timeframe": "15m"}))
    duplicate = policy.evaluate(base.__class__(**{**base.__dict__, "duplicate_order_key_seen": True}))
    killed = policy.evaluate(base.__class__(**{**base.__dict__, "kill_switch": True}))
    live_url = policy.evaluate(base.__class__(**{**base.__dict__, "base_url": "https://api.hyperliquid.xyz/info"}))

    assert "testnet_order_blocked_non_baseline_lane" in candidate.reason_codes
    assert "testnet_order_blocked_inactive_timeframe" in fifteen.reason_codes
    assert "testnet_duplicate_order_blocked" in duplicate.reason_codes
    assert "testnet_order_transport_kill_switch_active" in killed.reason_codes
    assert "live_endpoint_forbidden" in live_url.reason_codes


def test_pt_rt1_5_lifecycle_builder_can_call_configured_testnet_transport() -> None:
    class FakeTransport:
        def __call__(self, order_shape: dict, lifecycle_row: dict) -> dict:
            assert order_shape["notional_usdc"] == "25"
            assert lifecycle_row["testnet_order_key"].startswith("money_flow_v1_2_baseline|")
            return {
                "status": "reconciled",
                "order_endpoint_called": True,
                "signed_order_endpoint_called": True,
                "venue_order_id": "123",
                "cancel_status": "canceled",
                "reconcile_status": "reconciled",
                "reason_codes": ["testnet_order_lifecycle_recorded"],
                "testnet_fills_update_strategy_pnl": False,
            }

    rows, stats, keys = _build_pt_rt1_5_testnet_order_lifecycle_rows(
        decision_rows=[
            {
                "lane_id": "money_flow_v1_2_baseline",
                "strategy_id": "money_flow_v1_2_baseline",
                "symbol": "ETH",
                "timeframe": "1h",
                "action": "paper_opened",
                "signal_candle_close_time": "2026-05-17T14:00:00Z",
                "scheduled_closed_candle_evaluation": True,
                "equity_before": "10000",
            }
        ],
        scanner_rows=[
            SimpleNamespace(
                requested_symbol="ETH",
                canonical_symbol="ETH",
                scanner_eligible=True,
                blocked=False,
                reason_codes=("symbol_supported",),
                precision_ready=True,
                asset_id=1,
                szDecimals=4,
            )
        ],
        latest_closed_by_key={("ETH", "1h"): SimpleNamespace(close=Decimal("2500"))},
        transport_enabled=True,
        approval_text=PT_RT1_5_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
        notional_usdc=Decimal("25"),
        daily_cap=25,
        per_symbol_daily_cap=3,
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=FakeTransport(),
    )

    assert rows[0]["status"] == "reconciled"
    assert rows[0]["order_endpoint_called"] is True
    assert stats["order_endpoint_called"] is True
    assert stats["signed_order_endpoint_called"] is True
    assert len(keys) == 1


def test_pt_rt1_5_summary_policy_and_runner_command_are_boundary_labeled() -> None:
    summary = build_pt_rt1_summary()
    runner = Path("scripts/run_pt_rt1_paper_observation.py").read_text(encoding="utf-8")
    dashboard = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")

    assert summary["pt_rt1_5_testnet_order_policy"]["fixed_notional_usdc"] == str(PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC)
    assert summary["pt_rt1_5_testnet_order_policy"]["candidate_lanes_can_send_testnet_orders"] is False
    assert summary["signal_evaluation_policy"]["mode"] == "candle_close_only"
    assert "--pt-rt1-5-week1-active" in runner
    assert "--enable-pt-rt1-5-baseline-testnet-orders" in runner
    assert "--pt-rt1-5-testnet-order-notional-usdc" in runner
    assert "signal_evaluation_mode=\"candle_close_only\"" not in runner
    assert "candle_close_only" in runner
    assert "pt_rt1_5_week1_active" in dashboard
    assert "paper-observation-testnet-lifecycle" in html
    assert "fixed 25 USDC baseline-only testnet lifecycle gates" in html


def test_pt_rt1_5_all_lanes_remain_synthetic_and_non_production() -> None:
    for lane in PT_RT1_STRATEGY_LANES:
        assert lane.initial_equity == Decimal("10000")
        assert lane.paper_only is True
        assert lane.production_approved is False
        assert lane.live_approved is False
