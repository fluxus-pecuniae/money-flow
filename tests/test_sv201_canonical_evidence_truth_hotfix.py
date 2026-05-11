from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.config.settings import AppSettings
from core.domain.enums import Timeframe
from services.strategy_validation import sv2
from services.strategy_validation.sv2 import (
    SV20CandleDataset,
    build_sv20_readiness_rows,
    build_sv20_summary,
    normalize_hyperliquid_candle_snapshot,
    resolve_hyperliquid_market_identities,
    run_sv20_baseline_evidence_rows,
)


def _constant_candles(*, count: int = 45, price: Decimal = Decimal("104")) -> tuple[dict[str, str], ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows: list[dict[str, str]] = []
    for index in range(count):
        open_time = start + timedelta(hours=index)
        close_time = open_time + timedelta(hours=1)
        rows.append(
            {
                "open_time": open_time.isoformat().replace("+00:00", "Z"),
                "close_time": close_time.isoformat().replace("+00:00", "Z"),
                "open": str(price),
                "high": str(price + Decimal("1")),
                "low": str(price - Decimal("1")),
                "close": str(price),
                "volume": "1",
            }
        )
    return tuple(rows)


def test_hyperliquid_close_times_normalize_to_canonical_boundaries() -> None:
    daily = normalize_hyperliquid_candle_snapshot(
        [
            {
                "t": 1735689600000,
                "T": 1735775999999,
                "o": "100",
                "h": "110",
                "l": "90",
                "c": "105",
                "v": "1",
            }
        ],
        requested_symbol="BTC",
        resolved_venue_symbol="BTC",
        timeframe="1D",
    )[0]
    four_hour = normalize_hyperliquid_candle_snapshot(
        [
            {
                "t": 1735689600000,
                "T": 1735703999999,
                "o": "100",
                "h": "110",
                "l": "90",
                "c": "105",
                "v": "1",
            }
        ],
        requested_symbol="BTC",
        resolved_venue_symbol="BTC",
        timeframe="4h",
    )[0]

    assert daily["timeframe"] == "1d"
    assert daily["display_timeframe"] == "1D"
    assert daily["close_time"] == "2025-01-02T00:00:00Z"
    assert daily["raw_venue_close_time"] == "2025-01-01T23:59:59.999000Z"
    assert four_hour["close_time"] == "2025-01-01T04:00:00Z"
    assert four_hour["raw_venue_close_time"] == "2025-01-01T03:59:59.999000Z"


def test_staged_only_data_cannot_report_imported_or_canonical_evidence_ready() -> None:
    identity = resolve_hyperliquid_market_identities(
        {"universe": [{"name": "ETH", "szDecimals": 4}]},
        requested_symbols=("ETH",),
    )[0]
    dataset = SV20CandleDataset(
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
        target_window_ready=True,
        candles=normalize_hyperliquid_candle_snapshot(
            [
                {
                    "t": 1735689600000,
                    "T": 1735775999999,
                    "o": "100",
                    "h": "110",
                    "l": "90",
                    "c": "105",
                    "v": "1",
                }
            ],
            requested_symbol="ETH",
            resolved_venue_symbol="ETH",
            timeframe="1d",
        ),
        fetch_reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
        import_reason_codes=("historical_staged_for_replay_only",),
    )

    row = next(row for row in build_sv20_readiness_rows([identity], [dataset]) if row["timeframe"] == "1d")

    assert row["data_available"] is True
    assert row["staged_for_replay"] is True
    assert row["db_imported"] is False
    assert row["imported"] is False
    assert row["canonical_evidence_ready"] is False
    assert row["evidence_ready"] is False
    assert "canonical_sv2_evidence_packs_missing" in row["reason_codes"]
    assert "db_import_not_attempted" in row["reason_codes"]


def test_compact_sv2_rows_force_close_final_open_position_and_count_entry_fee(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_indicator_rows(closes: list[Decimal]) -> list[dict[str, Decimal]]:
        return [
            {
                "ema5": Decimal("105"),
                "ema10": Decimal("103"),
                "sma20": Decimal("100"),
                "rsi": Decimal("60"),
                "macd": Decimal("2"),
                "macd_signal": Decimal("1"),
                "macd_hist": Decimal("1"),
            }
            for _ in closes
        ]

    monkeypatch.setattr(sv2, "_indicator_rows", fake_indicator_rows)
    dataset = SV20CandleDataset(
        requested_symbol="BTC",
        resolved_venue_symbol="BTC",
        timeframe="1h",
        fetch_attempted=True,
        fetched=True,
        normalized=True,
        raw_file_written=False,
        staged_for_replay=True,
        db_imported=False,
        canonical_evidence_ready=False,
        target_window_ready=False,
        candles=_constant_candles(),
        fetch_reason_codes=(),
        import_reason_codes=(),
    )

    row = run_sv20_baseline_evidence_rows([dataset])[0]

    assert row["evidence_classification"] == "compact_provisional_replay_not_canonical_evidence"
    assert row["open_position_at_end"] is True
    assert row["forced_close_applied"] is True
    assert row["mark_to_market_applied"] is True
    assert row["final_mtm_price"] == "104"
    assert row["forced_close_price"] is not None
    assert row["forced_close_time"] is not None
    assert row["trade_count"] == 1
    assert Decimal(str(row["ending_equity"])) < Decimal("10000")
    assert Decimal(str(row["max_drawdown"])) > Decimal("0")
    assert "entry_fee_counted_at_open" in row["reason_codes"]
    assert "force_close_at_dataset_end" in row["reason_codes"]


def test_canonical_evidence_status_blocks_when_only_compact_rows_exist() -> None:
    identity = resolve_hyperliquid_market_identities(
        {"universe": [{"name": "BTC", "szDecimals": 5}]},
        requested_symbols=("BTC",),
    )[0]
    readiness = build_sv20_readiness_rows([identity], [])
    summary = build_sv20_summary(identities=[identity], readiness_rows=readiness)

    assert summary["canonical_evidence_status"]["status"] == "blocked"
    assert summary["canonical_evidence_status"]["evidence_pack_paths"] == []
    assert summary["canonical_evidence_status"]["compact_replay_rows_are_canonical_evidence"] is False
    assert "canonical_sv2_evidence_packs_missing" in summary["canonical_evidence_status"]["reason_codes"]


def test_sleeve_allocation_budget_is_even_and_validated() -> None:
    settings = AppSettings(_env_file=None)
    allocations = {sleeve.sleeve_id: sleeve.capital_allocation_pct for sleeve in settings.sleeves}

    assert allocations == {
        "sleeve_15m": Decimal("0.25"),
        "sleeve_1h": Decimal("0.25"),
        "sleeve_4h": Decimal("0.25"),
        "sleeve_1d": Decimal("0.25"),
    }
    assert sum(allocations.values()) == Decimal("1.00")

    with pytest.raises(ValidationError, match="enabled_sleeve_capital_allocation_pct_sum_exceeds_1_0"):
        AppSettings(
            _env_file=None,
            SLEEVE_15M_CAPITAL_ALLOCATION_PCT=0.5,
            SLEEVE_1H_CAPITAL_ALLOCATION_PCT=0.25,
            SLEEVE_4H_CAPITAL_ALLOCATION_PCT=0.25,
            SLEEVE_1D_CAPITAL_ALLOCATION_PCT=0.25,
        )


def test_internal_timeframe_is_1d_and_dashboard_label_is_1d() -> None:
    assert Timeframe.D1.value == "1d"
    assert sv2.canonical_sv20_timeframe("1D") == "1d"
    assert sv2.display_sv20_timeframe("1d") == "1D"
    assert sv2.SV20_COMPONENT_BY_TIMEFRAME[Timeframe.D1.value] == "sleeve_1d"
