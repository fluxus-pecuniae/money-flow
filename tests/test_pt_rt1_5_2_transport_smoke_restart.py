from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts.run_pt_rt1_paper_observation import (
    _build_pt_rt1_5_2_transport_smoke_lifecycle_row,
    pt_rt1_5_2_signed_transport_env_status,
)
from services.paper_runtime.pt_rt1 import (
    Candle,
    PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
    PT_RT1_5_2_RUNTIME_OUTPUT_DIR,
    PT_RT1_5_2_RUNTIME_SCOPE,
    PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP,
    PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR,
    PT_RT1_5_2_TRANSPORT_SMOKE_SCOPE,
    PT_RT1_MAINNET_API_URL,
    PT_RT1_TESTNET_API_URL,
    PT_RT1_TESTNET_INFO_URL,
    PT_RT15BaselineTestnetOrderPolicy,
    PT_RT15TestnetOrderCandidate,
)
from services.uat.sandbox import (
    HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
    HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
)


def _scanner_row() -> SimpleNamespace:
    return SimpleNamespace(
        requested_symbol="ETH",
        canonical_symbol="ETH",
        resolved_venue_symbol="ETH",
        scanner_eligible=True,
        blocked=False,
        reason_codes=("symbol_supported",),
        precision_ready=True,
        asset_id=1,
        szDecimals=4,
    )


def _candle() -> Candle:
    return Candle(
        symbol="ETH",
        timeframe="1h",
        open_time=datetime(2026, 5, 17, 15, 0, tzinfo=UTC),
        open=Decimal("2500"),
        high=Decimal("2550"),
        low=Decimal("2490"),
        close=Decimal("2525"),
        volume=Decimal("100"),
    )


def test_pt_rt1_5_2_constants_and_runner_flags_are_explicit() -> None:
    runner = Path("scripts/run_pt_rt1_paper_observation.py").read_text(encoding="utf-8")

    assert PT_RT1_5_2_TRANSPORT_SMOKE_SCOPE == "pt_rt1_5_2_transport_smoke"
    assert PT_RT1_5_2_TRANSPORT_SMOKE_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_5_2_transport_smoke"
    assert PT_RT1_5_2_RUNTIME_SCOPE == "pt_rt1_5_2_week1_active"
    assert PT_RT1_5_2_RUNTIME_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_5_2_week1_active"
    assert PT_RT1_5_2_TESTNET_SMOKE_PHASE_CAP == 1
    assert "--founder-approved-pt-rt1-5-2-testnet-transport-smoke" in runner
    assert "--founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc" in runner
    assert "--max-testnet-orders-this-phase" in runner
    assert "testnet_transport_smoke_not_strategy_signal" in runner


def test_pt_rt1_5_2_approval_allows_fixed_25usdc_testnet_shape() -> None:
    result = PT_RT15BaselineTestnetOrderPolicy().evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            fresh_signal_after_runtime_start=True,
            price=Decimal("2500"),
            fixed_notional=Decimal("25"),
            synthetic_signal_notional=Decimal("100000"),
        )
    )

    assert result.eligible is True
    assert result.order_shape is not None
    assert result.order_shape["notional_usdc"] == "25"
    assert result.order_shape["synthetic_signal_notional"] == "100000"


def test_pt_rt1_5_2_policy_accepts_testnet_api_root_and_rejects_live_root() -> None:
    testnet_root = PT_RT15BaselineTestnetOrderPolicy().evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
            base_url=PT_RT1_TESTNET_API_URL,
            fresh_signal_after_runtime_start=True,
            price=Decimal("2500"),
            fixed_notional=Decimal("25"),
        )
    )
    live_root = PT_RT15BaselineTestnetOrderPolicy().evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
            base_url=PT_RT1_MAINNET_API_URL,
            fresh_signal_after_runtime_start=True,
            price=Decimal("2500"),
            fixed_notional=Decimal("25"),
        )
    )

    assert testnet_root.eligible is True
    assert live_root.eligible is False
    assert "live_endpoint_forbidden" in live_root.reason_codes


def test_signed_transport_env_status_fails_closed_without_printing_secrets(monkeypatch) -> None:
    for key in (
        HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY_ENV,
        HYPERLIQUID_UAT_SANDBOX_ACCOUNT_ENV,
        HYPERLIQUID_UAT_SANDBOX_BASE_URL_ENV,
    ):
        monkeypatch.delenv(key, raising=False)

    status = pt_rt1_5_2_signed_transport_env_status()

    assert status["transport_client_configured"] is False
    assert status["private_key_printed"] is False
    assert "signed_testnet_private_key_missing" in status["reason_codes"]
    assert "signed_testnet_target_account_missing" in status["reason_codes"]


def test_transport_smoke_row_is_labeled_separate_from_strategy_pnl() -> None:
    transport_calls: list[dict[str, object]] = []

    def fake_transport(order_shape: dict[str, object], lifecycle_row: dict[str, object]) -> dict[str, object]:
        transport_calls.append(order_shape)
        return {
            "status": "reconciled",
            "order_endpoint_called": True,
            "signed_order_endpoint_called": True,
            "cancel_status": "canceled",
            "reconcile_status": "reconciled",
            "venue_response": {"status": "ok"},
            "reason_codes": ["testnet_order_accepted_open", "testnet_order_canceled_reconciled"],
        }

    rows, stats, keys = _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
        scanner_rows=[_scanner_row()],
        latest_closed_by_key={("ETH", "1h"): _candle()},
        enabled=True,
        approval_text=PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
        notional_usdc=Decimal("25"),
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=fake_transport,
        max_testnet_orders_this_phase=1,
    )

    assert len(rows) == 1
    assert len(transport_calls) == 1
    assert rows[0]["trigger_type"] == "transport_smoke_not_strategy_signal"
    assert rows[0]["trigger_lane"] == "none"
    assert rows[0]["synthetic_trade_created"] is False
    assert rows[0]["strategy_pnl_update_from_testnet"] is False
    assert rows[0]["order_endpoint_called"] is True
    assert rows[0]["signed_order_endpoint_called"] is True
    assert stats["transport_smoke_used_this_cycle"] is True
    assert "pt_rt1_5_2|transport_smoke_not_strategy_signal|25usdc|buy" in keys


def test_transport_smoke_cap_blocks_second_submit() -> None:
    rows, stats, keys = _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
        scanner_rows=[_scanner_row()],
        latest_closed_by_key={("ETH", "1h"): _candle()},
        enabled=True,
        approval_text=PT_RT1_5_2_EXACT_TESTNET_TRANSPORT_SMOKE_APPROVAL,
        notional_usdc=Decimal("25"),
        existing_order_keys={"pt_rt1_5_2|transport_smoke_not_strategy_signal|25usdc|buy"},
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=None,
        max_testnet_orders_this_phase=1,
    )

    assert rows[0]["status"] == "blocked"
    assert "pt_rt1_5_2_testnet_smoke_cap_reached" in rows[0]["reason_codes"]
    assert stats["transport_smoke_blocked"] is True
    assert keys == {"pt_rt1_5_2|transport_smoke_not_strategy_signal|25usdc|buy"}


def test_pt_rt1_5_2_report_and_summary_paths_are_documented() -> None:
    assert Path("docs/pt_rt1_5_2_signed_testnet_transport_smoke_and_active_restart.md").exists()
    assert Path("docs/pt_rt1_5_2_signed_testnet_transport_smoke_and_active_restart_summary.json").exists()
