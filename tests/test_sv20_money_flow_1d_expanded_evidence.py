from __future__ import annotations

import json
from pathlib import Path

from core.config.settings import AppSettings
from core.domain.enums import Timeframe
from services.strategy.money_flow import MoneyFlowStrategyFamily
from services.strategy_validation.sv2 import (
    HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    SV20_COMPONENT_BY_TIMEFRAME,
    SV20_HYPERLIQUID_INTERVAL_BY_TIMEFRAME,
    SV20_REQUESTED_SYMBOLS,
    SV20_SLEEVE_SETTINGS,
    SV20_TARGET_START_AT,
    SV20_TIMEFRAMES,
    SV20CandleDataset,
    build_sv20_readiness_rows,
    build_sv20_summary,
    hyperliquid_candle_snapshot_payload,
    normalize_hyperliquid_candle_snapshot,
    parse_utc,
    resolve_hyperliquid_market_identities,
)


def test_money_flow_v12_includes_real_1d_sleeve_and_preserves_existing_sleeves() -> None:
    settings = AppSettings(_env_file=None)
    sleeves = {sleeve.sleeve_id: sleeve for sleeve in settings.money_flow.sleeves}

    assert MoneyFlowStrategyFamily.STRATEGY_VERSION == "money_flow_v1_2"
    assert tuple(sleeves) == ("sleeve_15m", "sleeve_1h", "sleeve_4h", "sleeve_1d")
    assert sleeves["sleeve_15m"].model_dump(exclude={"sleeve_id", "timeframe"}) == {
        "enabled": True,
        "min_history_bars": 35,
        "rsi_floor": 52.0,
        "rsi_ceiling": 66.0,
        "overbought_rsi": 72.0,
        "require_macd_confirmation": True,
        "allow_pullback_entries": True,
        "allow_continuation_entries": True,
        "max_extension_pct_above_ema5": 0.018,
        "trim_on_overbought_rsi": True,
        "trim_rsi": 78.0,
        "close_on_ma_break": True,
        "close_on_macd_rollover": True,
    }
    assert sleeves["sleeve_1h"].rsi_floor == 50.0
    assert sleeves["sleeve_1h"].rsi_ceiling == 68.0
    assert sleeves["sleeve_4h"].rsi_floor == 48.0
    assert sleeves["sleeve_4h"].rsi_ceiling == 70.0

    one_day = sleeves["sleeve_1d"]
    assert one_day.timeframe == Timeframe.D1
    assert one_day.min_history_bars == 50
    assert one_day.rsi_floor == 46.0
    assert one_day.rsi_ceiling == 72.0
    assert one_day.overbought_rsi == 78.0
    assert one_day.trim_rsi == 84.0
    assert one_day.max_extension_pct_above_ema5 == 0.03
    assert one_day.require_macd_confirmation is True


def test_sv20_requested_universe_timeframes_and_candle_payload_are_mainnet_public() -> None:
    assert SV20_REQUESTED_SYMBOLS == ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX", "SHIB")
    assert SV20_TIMEFRAMES == ("15m", "1h", "4h", "1d")
    assert SV20_COMPONENT_BY_TIMEFRAME["1d"] == "sleeve_1d"
    assert SV20_HYPERLIQUID_INTERVAL_BY_TIMEFRAME["1d"] == "1d"
    assert HYPERLIQUID_MAINNET_PUBLIC_INFO_URL == "https://api.hyperliquid.xyz/info"

    payload = hyperliquid_candle_snapshot_payload(
        coin="ETH",
        timeframe="1D",
        start_at=parse_utc(SV20_TARGET_START_AT),
        end_at=parse_utc("2026-05-11T00:00:00Z"),
    )
    assert payload["type"] == "candleSnapshot"
    assert payload["req"]["interval"] == "1d"
    assert payload["req"]["startTime"] == 1735689600000
    assert "testnet" not in json.dumps(payload).lower()
    assert "order" not in json.dumps(payload).lower()


def test_hyperliquid_market_identity_resolver_reports_aliases_and_unsupported_symbols() -> None:
    meta = {
        "universe": [
            {"name": "BTC", "szDecimals": 5},
            {"name": "ETH", "szDecimals": 4},
            {"name": "kSHIB", "szDecimals": 0},
        ]
    }

    identities = resolve_hyperliquid_market_identities(
        meta,
        requested_symbols=("BTC", "SHIB", "AVAX"),
    )
    by_symbol = {row.requested_symbol: row for row in identities}

    assert by_symbol["BTC"].supported is True
    assert by_symbol["BTC"].asset_id == 0
    assert "symbol_supported" in by_symbol["BTC"].reason_codes
    assert by_symbol["SHIB"].supported is True
    assert by_symbol["SHIB"].resolved_venue_symbol == "kSHIB"
    assert "venue_symbol_alias_detected" in by_symbol["SHIB"].reason_codes
    assert by_symbol["AVAX"].supported is False
    assert by_symbol["AVAX"].reason_codes == ("symbol_not_in_hyperliquid_meta",)


def test_candle_normalization_and_readiness_emit_5000_limit_and_missing_target_reason() -> None:
    candles = normalize_hyperliquid_candle_snapshot(
        [
            {
                "t": 1767225600000,
                "T": 1767312000000,
                "o": "100",
                "h": "110",
                "l": "95",
                "c": "105",
                "v": "123.4",
            }
        ],
        requested_symbol="ETH",
        resolved_venue_symbol="ETH",
        timeframe="1D",
    )
    assert candles[0]["open_time"] == "2026-01-01T00:00:00Z"
    assert candles[0]["close_time"] == "2026-01-02T00:00:00Z"
    assert candles[0]["raw_venue_close_time"] == "2026-01-02T00:00:00Z"

    identity = resolve_hyperliquid_market_identities({"universe": [{"name": "ETH", "szDecimals": 4}]}, requested_symbols=("ETH",))[0]
    rows = build_sv20_readiness_rows(
        [identity],
        [
            SV20CandleDataset(
                requested_symbol="ETH",
                resolved_venue_symbol="ETH",
                timeframe="1d",
                fetch_attempted=True,
                fetched=True,
                normalized=True,
                raw_file_written=False,
                staged_for_replay=True,
                db_imported=False,
                canonical_evidence_ready=False,
                target_window_ready=False,
                candles=candles * 5000,
                fetch_reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
                import_reason_codes=("historical_staged_for_replay_only",),
            )
        ],
    )
    daily = next(row for row in rows if row["timeframe"] == "1d")
    assert daily["candle_count"] == 5000
    assert daily["display_timeframe"] == "1D"
    assert daily["db_imported"] is False
    assert daily["imported"] is False
    assert daily["staged_for_replay"] is True
    assert daily["evidence_ready"] is False
    assert "hyperliquid_public_5000_candle_limit" in daily["reason_codes"]
    assert "historical_target_start_not_available" in daily["reason_codes"]
    assert "historical_earliest_available_after_target" in daily["reason_codes"]
    assert "canonical_sv2_evidence_packs_missing" in daily["reason_codes"]


def test_sv20_summary_and_dashboard_assets_expose_real_1d_and_expanded_universe() -> None:
    identities = resolve_hyperliquid_market_identities(
        {"universe": [{"name": symbol, "szDecimals": 3} for symbol in SV20_REQUESTED_SYMBOLS]},
    )
    readiness = build_sv20_readiness_rows(identities, [])
    summary = build_sv20_summary(identities=identities, readiness_rows=readiness)

    assert summary["money_flow_version"] == "money_flow_v1_2"
    assert summary["boundary_flags"]["adds_real_1d_money_flow_sleeve"] is True
    assert summary["boundary_flags"]["uses_testnet_prices_as_strategy_truth"] is False
    assert summary["boundary_flags"]["submits_orders"] is False
    assert summary["sleeve_settings"]["sleeve_1d"] == SV20_SLEEVE_SETTINGS["sleeve_1d"]
    assert len(summary["data_readiness"]) == 40
    assert summary["timeframes"] == ["15m", "1h", "4h", "1d"]
    assert summary["display_timeframes"] == ["15m", "1h", "4h", "1D"]
    assert summary["canonical_evidence_status"]["status"] == "blocked"
    assert summary["canonical_evidence_status"]["compact_replay_rows_are_canonical_evidence"] is False

    js = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
    assert "sv2_0_historical_data_refresh_summary.json" in js
    assert "sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild" in js
    assert "Money Flow v1.2" in html
    assert "sleeve_1d" in html


def test_sv20_reports_exist_and_record_no_order_boundaries() -> None:
    readiness_report = Path("docs/sv2_0_historical_data_refresh_1d_and_expanded_universe_readiness.md")
    evidence_report = Path("docs/sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild.md")
    assert readiness_report.exists()
    assert evidence_report.exists()
    combined = readiness_report.read_text(encoding="utf-8") + evidence_report.read_text(encoding="utf-8")
    assert "Money Flow v1.2" in combined
    assert "sleeve_1d" in combined
    assert "BTC / ETH / SOL / XRP / DOGE / HYPE / BNB / SUI / AVAX / SHIB" in combined
    assert "Hyperliquid public mainnet" in combined
    assert "No orders were submitted" in combined
    assert "Testnet market data is not strategy truth" in combined
