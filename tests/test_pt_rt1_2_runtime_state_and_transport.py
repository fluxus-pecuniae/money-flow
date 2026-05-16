from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from scripts import run_pt_rt1_paper_observation as runner
from services.paper_runtime.hyperliquid_public_market_data import HyperliquidPublicMarketDataConnector
from services.paper_runtime.pt_rt1 import (
    PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    PaperDecisionEvent,
)


def _transport(_endpoint: str, payload: dict, _timeout: float):
    if payload["type"] == "meta":
        return {"universe": [{"name": "ETH", "szDecimals": 4}]}
    if payload["type"] == "allMids":
        return {"ETH": "4000"}
    if payload["type"] == "candleSnapshot":
        start = int(payload["req"]["startTime"])
        return [
            {
                "t": start + i * 3600000,
                "T": start + (i + 1) * 3600000,
                "o": str(100 + i),
                "h": str(102 + i),
                "l": str(99 + i),
                "c": str(101 + i),
                "v": "10",
            }
            for i in range(40)
        ]
    raise AssertionError(payload)


def _connector() -> HyperliquidPublicMarketDataConnector:
    return HyperliquidPublicMarketDataConnector(transport=_transport)


def _open_event(
    *,
    lane,
    symbol: str,
    timeframe: str,
    candles,
    now: datetime,
    data_health,
    last_processed_close=None,
    position_open: bool = False,
    equity_before: Decimal | None = None,
    btc_regime_constructive=None,
    higher_timeframe_constructive=None,
) -> PaperDecisionEvent:
    candle = candles[-1]
    close_time = (candle.open_time + timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return PaperDecisionEvent(
        lane_id=lane.lane_id,
        strategy_id=lane.strategy_id,
        symbol=symbol,
        timeframe=timeframe,
        signal_candle_open_time=candle.open_time.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        signal_candle_close_time=close_time,
        decision_time=now.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        candle_closed=True,
        candle_status_reason="closed_candle_ready",
        action="paper_opened",
        reason_codes=("baseline_alignment_passed",),
        indicator_snapshot={},
        position_before="open" if position_open else "flat",
        position_after="open",
        equity_before=equity_before or lane.initial_equity,
        equity_after=equity_before or lane.initial_equity,
    )


def test_pt_rt1_2_persists_open_state_and_blocks_duplicate_same_candle_opens(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "evaluate_paper_decision", _open_event)
    output_dir = tmp_path / "reports" / "paper_runtime" / "pt_rt1_2_state"
    output_dir.mkdir(parents=True)

    first = runner.run_cycle(
        connector=_connector(),
        output_dir=output_dir,
        symbols=["ETH"],
        timeframes=["1h"],
        max_candle_symbols=1,
        run_label="PT-RT1.2",
        testnet_probes_enabled=True,
        testnet_probe_approval_text=PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    )
    second = runner.run_cycle(
        connector=_connector(),
        output_dir=output_dir,
        symbols=["ETH"],
        timeframes=["1h"],
        max_candle_symbols=1,
        run_label="PT-RT1.2",
        testnet_probes_enabled=True,
        testnet_probe_approval_text=PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    )

    assert first["paper_runtime_state"]["paper_opens_this_cycle"] == len(PT_RT1_STRATEGY_LANES)
    assert first["paper_runtime_state"]["open_positions_count"] == len(PT_RT1_STRATEGY_LANES)
    assert second["paper_runtime_state"]["paper_opens_this_cycle"] == 0
    assert second["paper_runtime_state"]["duplicate_signal_blocks_this_cycle"] == len(PT_RT1_STRATEGY_LANES)
    assert second["testnet_plumbing_status"]["eligible_probe_shapes_this_cycle"] == 0
    state = json.loads((output_dir / "state.json").read_text(encoding="utf-8"))
    assert state["paper_runtime"]["processed_signal_keys"]
    assert len(state["paper_runtime"]["open_positions_by_key"]) == len(PT_RT1_STRATEGY_LANES)


def test_pt_rt1_2_data_unavailable_summary_separates_market_rows_from_lane_decisions(tmp_path: Path) -> None:
    def unavailable_transport(_endpoint: str, payload: dict, _timeout: float):
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "allMids":
            return {"ETH": "4000"}
        if payload["type"] == "candleSnapshot":
            raise TimeoutError("offline")
        raise AssertionError(payload)

    output_dir = tmp_path / "reports" / "paper_runtime" / "pt_rt1_2_unavailable"
    output_dir.mkdir(parents=True)
    summary = runner.run_cycle(
        connector=HyperliquidPublicMarketDataConnector(transport=unavailable_transport),
        output_dir=output_dir,
        symbols=["ETH"],
        timeframes=["1h"],
        max_candle_symbols=1,
        run_label="PT-RT1.2",
    )

    unavailable = summary["data_unavailable_summary"]
    assert unavailable["market_rows_checked"] == 1
    assert unavailable["market_rows_unavailable"] == 1
    assert unavailable["lane_expanded_data_unavailable_decisions"] == len(PT_RT1_STRATEGY_LANES)
    assert "One unavailable public market-data row can expand" in unavailable["lane_expansion_note"]
    assert unavailable["market_unavailable_rollup"][0]["reason"] == "public_mainnet_candleSnapshot_unavailable"


def test_pt_rt1_2_testnet_transport_is_audit_only_without_submit_request() -> None:
    lifecycle, stats = runner._apply_testnet_probe_transport(
        audit_rows=[{"eligible": True, "order_shape": {"action": {"type": "order"}}}],
        submit_enabled=False,
        transport_approval_text="",
        notional_usdc=PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    )

    assert lifecycle == []
    assert stats["transport_status"] == "audit_only_not_submitted"
    assert stats["order_endpoint_called"] is False
    assert stats["signed_order_endpoint_called"] is False


def test_pt_rt1_2_testnet_transport_requires_exact_approval_and_20usdc() -> None:
    lifecycle, stats = runner._apply_testnet_probe_transport(
        audit_rows=[{"eligible": True, "order_shape": {"action": {"type": "order"}}}],
        submit_enabled=True,
        transport_approval_text="approved-ish",
        notional_usdc=PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
    )
    wrong_notional_lifecycle, wrong_notional = runner._apply_testnet_probe_transport(
        audit_rows=[{"eligible": True, "order_shape": {"action": {"type": "order"}}}],
        submit_enabled=True,
        transport_approval_text=runner.PT_RT1_2_EXACT_TRANSPORT_APPROVAL,
        notional_usdc=Decimal("10"),
    )

    assert lifecycle == []
    assert stats["transport_status"] == "blocked_transport_approval_missing"
    assert wrong_notional_lifecycle == []
    assert wrong_notional["transport_status"] == "blocked_notional_not_20usdc"


def test_pt_rt1_2_fake_transport_records_submit_cancel_reconcile_without_paper_pnl_update() -> None:
    def fake_transport(order_shape: dict, audit_row: dict) -> dict:
        assert order_shape["action"]["type"] == "order"
        assert audit_row["notional_usdc"] == "20"
        return {
            "transport_status": "submitted_cancel_reconciled",
            "venue_order_id": "testnet-1",
            "cancel_attempted": True,
            "reconcile_attempted": True,
            "order_endpoint_called": True,
            "signed_order_endpoint_called": True,
            "sanitized_response": {"status": "ok"},
        }

    lifecycle, stats = runner._apply_testnet_probe_transport(
        audit_rows=[
            {
                "eligible": True,
                "symbol": "ETH",
                "timeframe": "1h",
                "strategy_id": "money_flow_v1_2_baseline",
                "lane_id": "money_flow_v1_2_baseline",
                "notional_usdc": "20",
                "order_shape": {"action": {"type": "order"}},
            }
        ],
        submit_enabled=True,
        transport_approval_text=runner.PT_RT1_2_EXACT_TRANSPORT_APPROVAL,
        notional_usdc=PT_RT1_TESTNET_PROBE_NOTIONAL_USDC,
        transport=fake_transport,
    )

    assert stats["transport_status"] == "submitted_cancel_reconciled"
    assert stats["submitted_this_cycle"] == 1
    assert lifecycle[0]["cancel_attempted"] is True
    assert lifecycle[0]["reconcile_attempted"] is True
    assert lifecycle[0]["testnet_fills_update_strategy_pnl"] is False
    assert lifecycle[0]["strategy_pnl_updated"] is False
