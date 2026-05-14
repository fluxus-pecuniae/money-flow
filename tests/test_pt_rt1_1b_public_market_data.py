from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.paper_runtime.hyperliquid_public_market_data import (
    HyperliquidPublicMarketDataConnector,
    normalize_candle_snapshot_payload,
    resolve_watchlist_from_public_data,
)
from services.paper_runtime.pt_rt1 import (
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_INFO_URL,
    Candle,
    DataHealth,
    evaluate_paper_decision,
    validate_strategy_truth_payload,
)


def _transport(_endpoint: str, payload: dict, _timeout: float):
    if payload["type"] == "meta":
        return {
            "universe": [
                {"name": "BTC", "szDecimals": 5},
                {"name": "ETH", "szDecimals": 4},
                {"name": "TRX", "szDecimals": 1},
                {"name": "POL", "szDecimals": 1},
                {"name": "MATIC", "szDecimals": 1, "isDelisted": True},
            ]
        }
    if payload["type"] == "allMids":
        return {"BTC": "100000", "ETH": "4000", "TRX": "0.12", "POL": "0.4", "MATIC": "1"}
    if payload["type"] == "candleSnapshot":
        start = int(payload["req"]["startTime"])
        return [
            {"t": start + i * 3600000, "T": start + (i + 1) * 3600000, "o": str(100 + i), "h": str(102 + i), "l": str(99 + i), "c": str(101 + i), "v": "10"}
            for i in range(40)
        ]
    raise AssertionError(payload)


def test_public_mainnet_connector_allows_only_public_read_payloads() -> None:
    connector = HyperliquidPublicMarketDataConnector(transport=_transport)

    assert connector.endpoint == PT_RT1_MAINNET_INFO_URL
    assert connector.fetch_meta().ok is True
    assert connector.fetch_all_mids().ok is True
    assert validate_strategy_truth_payload(endpoint=PT_RT1_TESTNET_INFO_URL, payload={"type": "allMids"}).allowed is False
    assert validate_strategy_truth_payload(endpoint=PT_RT1_MAINNET_INFO_URL, payload={"type": "openOrders"}).allowed is False
    assert validate_strategy_truth_payload(endpoint=PT_RT1_MAINNET_INFO_URL, payload={"type": "meta"}, headers={"Authorization": "x"}).allowed is False


def test_watchlist_resolution_from_public_meta_keeps_blocked_symbols_visible() -> None:
    connector = HyperliquidPublicMarketDataConnector(transport=_transport)
    rows = resolve_watchlist_from_public_data(meta_payload=connector.fetch_meta().payload, mids_payload=connector.fetch_all_mids().payload)
    by_request = {row.requested_symbol: row for row in rows}

    assert by_request["TRON"].resolved_venue_symbol == "TRX"
    assert by_request["TRON"].scanner_eligible is True
    assert by_request["PEPE"].resolved_venue_symbol == "kPEPE"
    assert by_request["PEPE"].blocked is True
    assert "pepe_kpepe_unit_semantics_deferred" in by_request["PEPE"].reason_codes
    assert by_request["OKB"].blocked is True
    assert "okb_support_not_confirmed" in by_request["OKB"].reason_codes
    assert by_request["POL"].resolved_venue_symbol == "POL"
    assert "pol_matic_delisted_mapping_blocked" not in by_request["POL"].reason_codes


def test_candle_snapshot_normalization_and_decision_event_use_closed_candles() -> None:
    start = datetime(2026, 5, 14, tzinfo=UTC)
    payload = [
        {
            "t": int((start + timedelta(hours=i)).timestamp() * 1000),
            "T": int((start + timedelta(hours=i + 1)).timestamp() * 1000),
            "o": str(100 + i),
            "h": str(103 + i),
            "l": str(99 + i),
            "c": str(102 + i),
            "v": "10",
        }
        for i in range(40)
    ]
    result = normalize_candle_snapshot_payload(payload, symbol="ETH", timeframe="1h")
    lane = next(lane for lane in PT_RT1_STRATEGY_LANES if lane.strategy_id == "money_flow_v1_2_baseline")
    decision = evaluate_paper_decision(
        lane=lane,
        symbol="ETH",
        timeframe="1h",
        candles=result.candles,
        now=start + timedelta(hours=41),
    )

    assert result.ok is True
    assert decision.candle_closed is True
    assert decision.signal_candle_close_time == "2026-05-15T16:00:00Z"
    assert decision.action in {"paper_opened", "no_trade", "paper_hold"}
    assert decision.production_artifact_created is False


def test_incomplete_candle_and_missing_indicators_do_not_create_fake_signal() -> None:
    lane = PT_RT1_STRATEGY_LANES[0]
    candle = Candle(
        symbol="ETH",
        timeframe="1h",
        open_time=datetime(2026, 5, 14, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("1"),
    )

    incomplete = evaluate_paper_decision(lane=lane, symbol="ETH", timeframe="1h", candles=[candle], now=candle.open_time + timedelta(minutes=30))
    missing = evaluate_paper_decision(lane=lane, symbol="ETH", timeframe="1h", candles=[candle], now=candle.open_time + timedelta(hours=2))
    unavailable = evaluate_paper_decision(lane=lane, symbol="ETH", timeframe="1h", candles=[candle], now=candle.open_time + timedelta(hours=2), data_health=DataHealth.UNAVAILABLE)

    assert incomplete.action == "no_trade"
    assert "candle_not_closed" in incomplete.reason_codes
    assert missing.action == "data_unavailable"
    assert "missing_indicator_field" in missing.reason_codes
    assert unavailable.action == "data_unavailable"
    assert "public_market_data_unavailable" in unavailable.reason_codes


def test_runtime_command_and_founder_outputs_exist() -> None:
    script = Path("scripts/run_pt_rt1_paper_observation.py")
    report = Path("docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness.md")
    summary = Path("docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json")

    assert script.exists()
    text = script.read_text(encoding="utf-8")
    assert "--disable-testnet-probes" in text
    assert "--public-mainnet-only" in text
    assert "reports/paper_runtime/" in text
    assert report.exists()
    assert summary.exists()
