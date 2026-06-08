from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts.run_pt_rt1_paper_observation import (
    _build_pt_rt1_5_2_transport_smoke_lifecycle_row,
    _resolve_testnet_meta_for_symbol,
)
from services.paper_runtime.pt_rt1 import (
    Candle,
    PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    PT_RT1_6_3_EXACT_XRP_TESTNET_METADATA_SMOKE_APPROVAL,
    PT_RT1_6_3_TRANSPORT_SMOKE_OUTPUT_DIR,
    PT_RT1_6_3_TRANSPORT_SMOKE_SCOPE,
    PT_RT1_TESTNET_INFO_URL,
)


def _scanner_row(symbol: str, asset_id: int, sz_decimals: int) -> SimpleNamespace:
    return SimpleNamespace(
        requested_symbol=symbol,
        canonical_symbol=symbol,
        resolved_venue_symbol=symbol,
        scanner_eligible=True,
        blocked=False,
        reason_codes=("symbol_supported",),
        precision_ready=True,
        asset_id=asset_id,
        szDecimals=sz_decimals,
    )


def _candle(symbol: str, close: str) -> Candle:
    return Candle(
        symbol=symbol,
        timeframe="1h",
        open_time=datetime(2026, 6, 8, 8, 0, tzinfo=UTC),
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
    )


def test_pt_rt1_6_3_constants_and_cli_are_explicit() -> None:
    runner = Path("scripts/run_pt_rt1_paper_observation.py").read_text(encoding="utf-8")

    assert PT_RT1_6_3_TRANSPORT_SMOKE_SCOPE == "pt_rt1_6_3_xrp_transport_smoke"
    assert PT_RT1_6_3_TRANSPORT_SMOKE_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke"
    assert "--founder-approved-pt-rt1-6-3-xrp-testnet-metadata-smoke" in runner
    assert "--pt-rt1-6-3-testnet-smoke-symbol" in runner
    assert "pt_rt1_6_3_xrp_transport_smoke_example" in runner


def test_pt_rt1_6_3_report_and_summary_exist() -> None:
    assert Path("docs/pt_rt1_6_3_testnet_metadata_resolver_hotfix.md").exists()
    assert Path("docs/pt_rt1_6_3_testnet_metadata_resolver_hotfix_summary.json").exists()


def test_blocked_symbol_metadata_resolver_records_present_and_missing_states() -> None:
    resolved, resolved_reasons = _resolve_testnet_meta_for_symbol(
        "XRP",
        {"XRP": {"asset_id": 14, "venue_symbol": "XRP", "szDecimals": 1, "isDelisted": False}},
    )
    missing, missing_reasons = _resolve_testnet_meta_for_symbol("XRP", {"BTC": {"asset_id": 0}})

    assert resolved is not None
    assert resolved["asset_id"] == 14
    assert "testnet_metadata_blocked_symbol_resolved" in resolved_reasons
    assert missing is None
    assert "testnet_metadata_symbol_not_on_testnet" in missing_reasons


def test_xrp_transport_smoke_targets_xrp_and_does_not_use_btc_fallback() -> None:
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
        scanner_rows=[_scanner_row("BTC", 0, 5), _scanner_row("XRP", 14, 1)],
        latest_closed_by_key={("BTC", "1h"): _candle("BTC", "70000"), ("XRP", "1h"): _candle("XRP", "0.52")},
        testnet_meta_by_symbol={
            "BTC": {"asset_id": 0, "venue_symbol": "BTC", "szDecimals": 5, "isDelisted": False},
            "XRP": {"asset_id": 14, "venue_symbol": "XRP", "szDecimals": 1, "isDelisted": False},
        },
        testnet_metadata_reason_codes=["testnet_metadata_resolved"],
        enabled=True,
        approval_text=PT_RT1_6_3_EXACT_XRP_TESTNET_METADATA_SMOKE_APPROVAL,
        notional_usdc=PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=fake_transport,
        max_testnet_orders_this_phase=1,
        smoke_symbol="XRP",
    )

    assert len(rows) == 1
    assert rows[0]["symbol"] == "XRP"
    assert rows[0]["trigger_type"] == "transport_smoke_not_strategy_signal"
    assert rows[0]["strategy_pnl_update_from_testnet"] is False
    assert rows[0]["synthetic_trade_created"] is False
    assert "testnet_transport_smoke_xrp_targeted" in rows[0]["reason_codes"]
    assert "testnet_metadata_blocked_symbol_resolved" in rows[0]["testnet_metadata_reason_codes"]
    assert transport_calls[0]["asset_id"] == 14
    assert stats["transport_smoke_used_this_cycle"] is True
    assert "pt_rt1_6_3|transport_smoke_not_strategy_signal|XRP|25usdc|buy" in keys


def test_xrp_transport_smoke_blocks_locally_if_xrp_metadata_is_missing() -> None:
    transport_calls: list[dict[str, object]] = []

    rows, stats, keys = _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
        scanner_rows=[_scanner_row("BTC", 0, 5), _scanner_row("XRP", 14, 1)],
        latest_closed_by_key={("BTC", "1h"): _candle("BTC", "70000"), ("XRP", "1h"): _candle("XRP", "0.52")},
        testnet_meta_by_symbol={
            "BTC": {"asset_id": 0, "venue_symbol": "BTC", "szDecimals": 5, "isDelisted": False},
        },
        testnet_metadata_reason_codes=["testnet_metadata_resolved"],
        enabled=True,
        approval_text=PT_RT1_6_3_EXACT_XRP_TESTNET_METADATA_SMOKE_APPROVAL,
        notional_usdc=PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=lambda order_shape, lifecycle_row: transport_calls.append(order_shape) or {},
        max_testnet_orders_this_phase=1,
        smoke_symbol="XRP",
    )

    assert rows[0]["symbol"] == "XRP"
    assert rows[0]["status"] == "blocked"
    assert "testnet_transport_smoke_xrp_targeted" in rows[0]["reason_codes"]
    assert "testnet_metadata_unavailable" in rows[0]["reason_codes"]
    assert "testnet_metadata_symbol_not_on_testnet" in rows[0]["testnet_metadata_reason_codes"]
    assert rows[0]["order_endpoint_called"] is False
    assert rows[0]["signed_order_endpoint_called"] is False
    assert transport_calls == []
    assert stats["transport_smoke_blocked"] is True
    assert keys == set()
