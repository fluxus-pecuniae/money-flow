from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts.run_pt_rt1_paper_observation import (
    HyperliquidPT_RT15TestnetOrderTransport,
    _apply_warm_start_signal_gate,
    _build_pt_rt1_5_testnet_order_lifecycle_rows,
    _update_open_position_mtm,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
    PT_RT1_5_1_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_1_RUNTIME_SCOPE,
    PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    PT_RT1_TESTNET_INFO_URL,
    PT_RT15BaselineTestnetOrderPolicy,
    PT_RT15TestnetOrderCandidate,
    build_pt_rt1_summary,
)
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
)


def _baseline_open(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "lane_id": "money_flow_v1_2_baseline",
        "strategy_id": "money_flow_v1_2_baseline",
        "symbol": "ETH",
        "timeframe": "1h",
        "action": "paper_opened",
        "signal_candle_close_time": "2026-05-17T14:00:00Z",
        "decision_time": "2026-05-17T14:02:00Z",
        "scheduled_closed_candle_evaluation": True,
        "equity_before": "10000",
        "reason_codes": ["baseline_alignment_passed"],
    }
    row.update(overrides)
    return row


def test_pt_rt1_5_1_scope_and_summary_policy_are_explicit() -> None:
    summary = build_pt_rt1_summary()
    runner = Path("scripts/run_pt_rt1_paper_observation.py").read_text(encoding="utf-8")

    assert PT_RT1_5_1_RUNTIME_SCOPE == "pt_rt1_5_1_smoke"
    assert PT_RT1_5_1_RUNTIME_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_5_1_smoke"
    assert summary["warm_start_gate_policy"]["fresh_signal_only_after_runtime_start"] is True
    assert summary["open_position_mtm_policy"]["missing_price_displays_zero"] is False
    assert "pt_rt1_5_smoke_pre_warm_start_gate" in summary["pt_rt1_5_1_smoke_scope"]["archived_runtime_scopes"]
    assert "--fresh-signal-only-after-runtime-start" in runner
    assert "--enable-baseline-testnet-transport" in runner
    assert "--founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc" in runner


def test_warm_start_blocks_already_true_startup_open_and_marks_waiting_for_reset() -> None:
    rows, state, stats = _apply_warm_start_signal_gate(
        decision_rows=[_baseline_open(signal_candle_close_time="2026-05-17T14:00:00Z")],
        warm_start_state={},
        runtime_start_utc="2026-05-17T14:34:44Z",
        warm_start_evaluation=True,
        fresh_signal_only_after_runtime_start=True,
    )

    assert rows[0]["action"] == "no_trade"
    assert rows[0]["warm_start_signal_blocked"] is True
    assert "signal_good_but_runtime_started_after_setup" in rows[0]["reason_codes"]
    assert stats["startup_valid_signals_blocked_this_cycle"] == 1

    rows, state, stats = _apply_warm_start_signal_gate(
        decision_rows=[_baseline_open(signal_candle_close_time="2026-05-17T15:00:00Z")],
        warm_start_state=state,
        runtime_start_utc="2026-05-17T14:34:44Z",
        warm_start_evaluation=False,
        fresh_signal_only_after_runtime_start=True,
    )
    assert rows[0]["action"] == "no_trade"
    assert "entry_context_already_true_waiting_for_reset" in rows[0]["reason_codes"]
    assert stats["waiting_for_reset_signals_this_cycle"] == 1


def test_warm_start_allows_fresh_false_to_true_after_reset() -> None:
    rows, state, _ = _apply_warm_start_signal_gate(
        decision_rows=[_baseline_open(action="no_trade", signal_candle_close_time="2026-05-17T14:00:00Z")],
        warm_start_state={},
        runtime_start_utc="2026-05-17T14:34:44Z",
        warm_start_evaluation=True,
        fresh_signal_only_after_runtime_start=True,
    )
    assert rows[0]["action"] == "no_trade"

    rows, _, stats = _apply_warm_start_signal_gate(
        decision_rows=[_baseline_open(signal_candle_close_time="2026-05-17T15:00:00Z")],
        warm_start_state=state,
        runtime_start_utc="2026-05-17T14:34:44Z",
        warm_start_evaluation=False,
        fresh_signal_only_after_runtime_start=True,
    )
    assert rows[0]["action"] == "paper_opened"
    assert rows[0]["fresh_signal_after_runtime_start"] is True
    assert "fresh_entry_signal_after_runtime_start" in rows[0]["reason_codes"]
    assert stats["fresh_post_start_opens_this_cycle"] == 1


def test_testnet_policy_requires_fresh_post_start_signal() -> None:
    policy = PT_RT15BaselineTestnetOrderPolicy()
    stale = policy.evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            price=Decimal("2500"),
            fixed_notional=PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
            fresh_signal_after_runtime_start=False,
        )
    )
    fresh = policy.evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            price=Decimal("2500"),
            fixed_notional=PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
            fresh_signal_after_runtime_start=True,
            synthetic_signal_notional=Decimal("999999"),
        )
    )

    assert "testnet_order_requires_fresh_post_start_signal" in stale.reason_codes
    assert fresh.eligible is True
    assert fresh.order_shape is not None
    assert fresh.order_shape["notional_usdc"] == "25"
    assert fresh.order_shape["synthetic_signal_notional"] == "999999"


def test_lifecycle_builder_blocks_startup_signal_and_allows_fresh_baseline_only() -> None:
    scanner_rows = [
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
    ]
    latest = {("ETH", "1h"): SimpleNamespace(close=Decimal("2500"))}

    blocked_rows, blocked_stats, _ = _build_pt_rt1_5_testnet_order_lifecycle_rows(
        decision_rows=[_baseline_open(fresh_signal_after_runtime_start=False)],
        scanner_rows=scanner_rows,
        latest_closed_by_key=latest,
        transport_enabled=True,
        approval_text=PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
        notional_usdc=Decimal("25"),
        daily_cap=25,
        per_symbol_daily_cap=3,
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=None,
    )
    assert blocked_rows[0]["status"] == "blocked"
    assert "testnet_order_requires_fresh_post_start_signal" in blocked_rows[0]["reason_codes"]
    assert blocked_stats["order_endpoint_called"] is False

    fresh_rows, fresh_stats, keys = _build_pt_rt1_5_testnet_order_lifecycle_rows(
        decision_rows=[_baseline_open(fresh_signal_after_runtime_start=True)],
        scanner_rows=scanner_rows,
        latest_closed_by_key=latest,
        transport_enabled=True,
        approval_text=PT_RT1_5_1_EXACT_BASELINE_TESTNET_ORDER_APPROVAL,
        notional_usdc=Decimal("25"),
        daily_cap=25,
        per_symbol_daily_cap=3,
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=None,
    )
    assert fresh_rows[0]["status"] == "preflight_passed"
    assert "signed_testnet_transport_client_not_configured" in fresh_rows[0]["reason_codes"]
    assert fresh_stats["fresh_baseline_open_signals_this_cycle"] == 1
    assert len(keys) == 1


def test_open_position_mtm_populates_price_and_unrealized_without_default_zero() -> None:
    open_positions = {
        "money_flow_v1_2_baseline|ETH|1h": {
            "lane_id": "money_flow_v1_2_baseline",
            "symbol": "ETH",
            "timeframe": "1h",
            "entry_price": "100",
            "quantity": "2",
            "notional": "200",
        },
        "money_flow_v1_2_baseline|MISSING|1h": {
            "lane_id": "money_flow_v1_2_baseline",
            "symbol": "MISSING",
            "timeframe": "1h",
            "entry_price": "100",
            "quantity": "2",
            "notional": "200",
        },
    }
    unrealized, stats = _update_open_position_mtm(
        open_positions_by_key=open_positions,
        scanner_rows=[
            SimpleNamespace(canonical_symbol="ETH", requested_symbol="ETH", public_mid="110"),
        ],
        latest_closed_by_key={},
        now=datetime(2026, 5, 17, 15, 0, tzinfo=UTC),
    )

    eth = open_positions["money_flow_v1_2_baseline|ETH|1h"]
    missing = open_positions["money_flow_v1_2_baseline|MISSING|1h"]
    assert eth["current_price"] == "110"
    assert eth["current_unrealized_pnl"] == "20"
    assert "mtm_unrealized_pnl_updated" in eth["mtm_reason_codes"]
    assert missing["current_price"] is None
    assert missing["current_unrealized_pnl"] is None
    assert "mtm_price_unavailable" in missing["mtm_reason_codes"]
    assert unrealized["money_flow_v1_2_baseline"] == "20"
    assert stats["open_positions_mtm_updated"] == 1


def test_signed_transport_from_env_requires_testnet_and_does_not_log_secret(monkeypatch) -> None:
    monkeypatch.setenv(HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV, "0x" + "1" * 64)
    monkeypatch.setenv(HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV, "0x" + "2" * 40)
    monkeypatch.setenv(HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV, PT_RT1_TESTNET_INFO_URL)

    transport = HyperliquidPT_RT15TestnetOrderTransport.from_env()
    assert transport is not None
    assert "1111111111111111111111111111111111111111111111111111111111111111" not in repr(transport)

