from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts.run_pt_rt1_paper_observation import (
    HyperliquidPT_RT15TestnetOrderTransport,
    _build_pt_rt1_5_2_transport_smoke_lifecycle_row,
    _build_pt_rt1_5_testnet_order_lifecycle_rows,
)
from services.paper_runtime.pt_rt1 import (
    Candle,
    PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
    PT_RT1_5_3_TRANSPORT_SMOKE_OUTPUT_DIR,
    PT_RT1_5_3_TRANSPORT_SMOKE_SCOPE,
    PT_RT1_TESTNET_INFO_URL,
    PT_RT15BaselineTestnetOrderPolicy,
    PT_RT15TestnetOrderCandidate,
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
        open_time=datetime(2026, 5, 17, 15, 0, tzinfo=UTC),
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
    )


def _baseline_open(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "lane_id": "money_flow_v1_2_baseline",
        "strategy_id": "money_flow_v1_2_baseline",
        "symbol": "ETH",
        "timeframe": "1h",
        "action": "paper_opened",
        "signal_candle_close_time": "2026-05-17T15:00:00Z",
        "scheduled_closed_candle_evaluation": True,
        "fresh_signal_after_runtime_start": True,
        "equity_before": "100000",
        "reason_codes": ["fresh_entry_signal_after_runtime_start"],
    }
    row.update(overrides)
    return row


def test_pt_rt1_5_3_constants_and_cli_are_explicit() -> None:
    runner = Path("scripts/run_pt_rt1_paper_observation.py").read_text(encoding="utf-8")

    assert PT_RT1_5_3_TRANSPORT_SMOKE_SCOPE == "pt_rt1_5_3_transport_smoke"
    assert PT_RT1_5_3_TRANSPORT_SMOKE_OUTPUT_DIR == "reports/paper_runtime/pt_rt1_5_3_transport_smoke"
    assert "--founder-approved-pt-rt1-5-3-testnet-size-hotfix-smoke" in runner
    assert "testnet_size_precision_hotfix" in runner
    assert "testnet_metadata_resolved" in runner


def test_fixed_25usdc_order_computes_and_formats_quantity_from_sz_decimals() -> None:
    result = PT_RT15BaselineTestnetOrderPolicy().evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            fresh_signal_after_runtime_start=True,
            symbol="BTC",
            asset_id=0,
            sz_decimals=5,
            price=Decimal("74114.25"),
            fixed_notional=Decimal("25"),
            synthetic_signal_notional=Decimal("5000"),
        )
    )

    assert result.eligible is True
    assert result.order_shape is not None
    assert result.lifecycle_row["testnet_fixed_notional"] == "25"
    assert result.lifecycle_row["synthetic_signal_notional"] == "5000"
    assert result.lifecycle_row["raw_quantity"].startswith("0.000337")
    assert result.lifecycle_row["formatted_quantity"] == "0.00033"
    assert Decimal(result.lifecycle_row["estimated_testnet_notional"]) > Decimal("24")
    assert result.order_shape["action"]["orders"][0]["s"] == "0.00033"
    assert result.order_shape["szDecimals"] == 5


def test_invalid_formatted_quantity_blocks_before_submit() -> None:
    result = PT_RT15BaselineTestnetOrderPolicy().evaluate(
        PT_RT15TestnetOrderCandidate(
            order_transport_enabled=True,
            kill_switch=False,
            approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
            base_url=PT_RT1_TESTNET_INFO_URL,
            fresh_signal_after_runtime_start=True,
            symbol="BTC",
            asset_id=0,
            sz_decimals=3,
            price=Decimal("74114.25"),
            fixed_notional=Decimal("25"),
        )
    )

    assert result.eligible is False
    assert result.order_shape is None
    assert "testnet_order_invalid_size_preflight" in result.reason_codes
    assert result.lifecycle_row["formatted_quantity"] == "0"
    assert result.lifecycle_row["order_endpoint_called"] is False
    assert result.lifecycle_row["signed_order_endpoint_called"] is False


def test_testnet_metadata_size_preflight_skips_invalid_high_price_symbol_for_smoke() -> None:
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
        scanner_rows=[_scanner_row("BTC", 0, 5), _scanner_row("ETH", 1, 4)],
        latest_closed_by_key={("BTC", "1h"): _candle("BTC", "78015"), ("ETH", "1h"): _candle("ETH", "2525")},
        testnet_meta_by_symbol={
            "BTC": {"asset_id": 0, "venue_symbol": "BTC", "szDecimals": 3, "isDelisted": False, "metadata_source": "hyperliquid_testnet_public_meta"},
            "ETH": {"asset_id": 1, "venue_symbol": "ETH", "szDecimals": 4, "isDelisted": False, "metadata_source": "hyperliquid_testnet_public_meta"},
        },
        testnet_metadata_reason_codes=["testnet_metadata_resolved"],
        enabled=True,
        approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
        notional_usdc=Decimal("25"),
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=fake_transport,
        max_testnet_orders_this_phase=1,
    )

    assert len(rows) == 1
    assert rows[0]["symbol"] == "ETH"
    assert rows[0]["asset_id"] == 1
    assert rows[0]["szDecimals"] == 4
    assert rows[0]["testnet_metadata_source"] == "hyperliquid_testnet_public_meta"
    assert rows[0]["formatted_quantity"] != "0"
    assert transport_calls[0]["asset_id"] == 1
    assert stats["transport_smoke_used_this_cycle"] is True
    assert "pt_rt1_5_3|transport_smoke_not_strategy_signal|25usdc|buy" in keys


def test_all_invalid_smoke_size_blocks_locally_before_exchange() -> None:
    transport_calls: list[dict[str, object]] = []

    rows, stats, keys = _build_pt_rt1_5_2_transport_smoke_lifecycle_row(
        scanner_rows=[_scanner_row("BTC", 0, 5)],
        latest_closed_by_key={("BTC", "1h"): _candle("BTC", "78015")},
        testnet_meta_by_symbol={
            "BTC": {"asset_id": 0, "venue_symbol": "BTC", "szDecimals": 3, "isDelisted": False, "metadata_source": "hyperliquid_testnet_public_meta"},
        },
        testnet_metadata_reason_codes=["testnet_metadata_resolved"],
        enabled=True,
        approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
        notional_usdc=Decimal("25"),
        existing_order_keys=set(),
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
        transport=lambda order_shape, lifecycle_row: transport_calls.append(order_shape) or {},
        max_testnet_orders_this_phase=1,
    )

    assert rows[0]["status"] == "blocked"
    assert "testnet_order_invalid_size_preflight" in rows[0]["reason_codes"]
    assert rows[0]["order_endpoint_called"] is False
    assert rows[0]["signed_order_endpoint_called"] is False
    assert transport_calls == []
    assert stats["transport_smoke_blocked"] is True
    assert keys == set()


def test_venue_invalid_size_reject_is_reason_coded() -> None:
    status, oid, reasons = HyperliquidPT_RT15TestnetOrderTransport._parse_order_response(
        {"status": "ok", "response": {"data": {"statuses": [{"error": "Order has invalid size."}]}}}
    )

    assert status == "rejected"
    assert oid is None
    assert "testnet_order_rejected_invalid_size" in reasons
    assert "venue_reject_order_has_invalid_size" in reasons
    assert "testnet_order_rejected_lot_size" in reasons


def test_repeated_invalid_size_submit_key_is_blocked_after_venue_reject() -> None:
    transport_calls = 0

    def invalid_size_transport(order_shape: dict[str, object], lifecycle_row: dict[str, object]) -> dict[str, object]:
        nonlocal transport_calls
        transport_calls += 1
        return {
            "status": "rejected",
            "order_endpoint_called": True,
            "signed_order_endpoint_called": True,
            "venue_response": {"status": "ok", "error": "Order has invalid size."},
            "reason_codes": ["testnet_order_rejected_invalid_size", "venue_reject_order_has_invalid_size"],
        }

    args = dict(
        decision_rows=[_baseline_open()],
        scanner_rows=[_scanner_row("ETH", 1, 4)],
        latest_closed_by_key={("ETH", "1h"): SimpleNamespace(close=Decimal("2525"))},
        testnet_meta_by_symbol={"ETH": {"asset_id": 1, "venue_symbol": "ETH", "szDecimals": 4, "isDelisted": False}},
        testnet_metadata_reason_codes=["testnet_metadata_resolved"],
        transport_enabled=True,
        approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
        notional_usdc=Decimal("25"),
        daily_cap=25,
        per_symbol_daily_cap=3,
        base_url=PT_RT1_TESTNET_INFO_URL,
        kill_switch=False,
    )
    rows, _stats, keys = _build_pt_rt1_5_testnet_order_lifecycle_rows(
        **args,
        existing_order_keys=set(),
        transport=invalid_size_transport,
    )
    assert transport_calls == 1
    assert rows[0]["status"] == "rejected"
    assert "venue_reject_order_has_invalid_size" in rows[0]["reason_codes"]

    duplicate_rows, duplicate_stats, duplicate_keys = _build_pt_rt1_5_testnet_order_lifecycle_rows(
        **args,
        existing_order_keys=keys,
        transport=invalid_size_transport,
    )
    assert transport_calls == 1
    assert duplicate_rows[0]["status"] == "blocked"
    assert "testnet_duplicate_order_blocked" in duplicate_rows[0]["reason_codes"]
    assert duplicate_stats["order_endpoint_called"] is False
    assert duplicate_keys == keys


def test_candidate_mf_orig_wildcard_and_15m_lanes_cannot_submit() -> None:
    policy = PT_RT15BaselineTestnetOrderPolicy()
    blocked_cases = [
        {"lane_id": "avoid_low_rolling_range_20", "strategy_id": "avoid_low_rolling_range_20", "timeframe": "1h"},
        {"lane_id": "mf_orig_stage_filter_only_full_equity", "strategy_id": "mf_orig_stage_filter_only_full_equity", "timeframe": "1h"},
        {"lane_id": "wildcard_btc_regime_guard", "strategy_id": "wildcard_btc_regime_guard", "timeframe": "1h"},
        {"lane_id": "money_flow_v1_2_baseline", "strategy_id": "money_flow_v1_2_baseline", "timeframe": "15m"},
    ]

    for case in blocked_cases:
        result = policy.evaluate(
            PT_RT15TestnetOrderCandidate(
                **case,
                order_transport_enabled=True,
                kill_switch=False,
                approval_text=PT_RT1_5_3_EXACT_TESTNET_SIZE_HOTFIX_SMOKE_APPROVAL,
                base_url=PT_RT1_TESTNET_INFO_URL,
                fresh_signal_after_runtime_start=True,
                price=Decimal("2525"),
                fixed_notional=Decimal("25"),
            )
        )
        assert result.eligible is False
        assert result.lifecycle_row["order_endpoint_called"] is False
        assert result.lifecycle_row["strategy_pnl_updated"] is False


def test_dashboard_lifecycle_table_exposes_precision_fields() -> None:
    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")

    assert "pt_rt1_5_3_transport_smoke/testnet_order_lifecycle.jsonl" in js
    assert "<th>Asset</th>" in js
    assert "<th>szDec</th>" in js
    assert "<th>Raw qty</th>" in js
    assert "<th>Formatted qty</th>" in js
    assert "<th>Est. notional</th>" in js
    assert "estimated_testnet_notional" in js


def test_pt_rt1_5_3_report_and_summary_exist() -> None:
    assert Path("docs/pt_rt1_5_3_hyperliquid_testnet_size_precision_hotfix.md").exists()
    assert Path("docs/pt_rt1_5_3_hyperliquid_testnet_size_precision_hotfix_summary.json").exists()
