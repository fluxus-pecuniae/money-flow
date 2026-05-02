from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.domain.enums import Environment, MarketType, ProductType, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    import_strategy_validation_candles_from_path,
    money_flow_research_campaign_config_from_dict,
)
from test_sv10_strategy_validation import build_test_session_factory, seed_symbol
from test_sv15_historical_data_readiness import _assert_no_live_artifacts, _campaign_raw


def _valid_row(instrument_key: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "symbol": "BTC",
        "instrument_key": instrument_key,
        "open_time": "2026-01-01T00:00:00Z",
        "close_time": "2026-01-01T00:15:00Z",
        "open": "100",
        "high": "101",
        "low": "99",
        "close": "100.5",
        "volume": "10",
        "trade_count": "2",
    }
    row.update(overrides)
    return row


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    headers = [
        "symbol",
        "instrument_key",
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trade_count",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(header, "")) for header in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _seed_spot_btc_symbol(session_factory) -> tuple[str, str, str]:
    instrument_key = "spot:spot:BTC:USD"
    with session_factory() as session:
        instrument = InstrumentModel(
            instrument_key=instrument_key,
            canonical_symbol="BTC",
            market_type=MarketType.SPOT,
            product_type=ProductType.SPOT,
            base_asset="BTC",
            quote_asset="USD",
            settlement_asset=None,
            is_active=True,
        )
        session.add(instrument)
        session.flush()
        symbol_model = SymbolModel(
            instrument_ref_id=instrument.id,
            venue="hyperliquid",
            symbol="BTC",
            exchange_symbol="BTC-SPOT",
            venue_asset_id="1",
            asset_id=1,
            market_type=MarketType.SPOT,
            product_type=ProductType.SPOT,
            base_asset="BTC",
            quote_asset="USD",
            settlement_asset=None,
            price_tick_size=Decimal("0.1"),
            quantity_step_size=Decimal("0.001"),
            min_order_size=Decimal("0.001"),
            size_decimals=3,
            max_leverage=1,
            only_isolated=False,
            is_perpetual=False,
            is_builder_deployed=False,
            is_strategy_eligible=True,
            is_trading_eligible=True,
            is_active=True,
            raw_metadata={},
        )
        session.add(symbol_model)
        session.commit()
        return instrument.id, symbol_model.id, instrument_key


def _import_csv(path: Path, session_factory) -> None:
    import_strategy_validation_candles_from_path(
        path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        source_label="sv151_fixture",
        session_factory=session_factory,
    )


def _candle_count(session_factory) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(CandleModel))


def test_campaign_window_convention_strictly_rejects_contradictions(
    tmp_path: Path,
) -> None:
    raw = _campaign_raw(
        output_dir=tmp_path,
        instrument_key="perpetual:linear:BTC:USDC:USDC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    raw["window_convention"] = "(start_at, end_at]"
    assert money_flow_research_campaign_config_from_dict(raw).campaign_name == "money_flow_core_btc"

    for conflicting_text in (
        "[start_at, end_at]",
        "(start_at, end_at] inclusive start",
        "(start_at, end_at] start included",
        "(start_at, end_at] start is included",
    ):
        invalid = dict(raw)
        invalid["window_convention"] = conflicting_text
        with pytest.raises(ValueError, match="window_convention.*platform convention"):
            money_flow_research_campaign_config_from_dict(invalid)


def test_candle_import_identity_conflict_does_not_retarget_existing_candle(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    original_instrument_id, original_symbol_id, _original_key = seed_symbol(session_factory)
    _spot_instrument_id, _spot_symbol_id, spot_key = _seed_spot_btc_symbol(session_factory)
    open_time = datetime(2026, 1, 1, tzinfo=UTC)
    close_time = datetime(2026, 1, 1, 0, 15, tzinfo=UTC)
    with session_factory() as session:
        session.add(
            CandleModel(
                environment=Environment.TESTNET,
                venue="hyperliquid",
                instrument_ref_id=original_instrument_id,
                symbol_id=original_symbol_id,
                symbol="BTC",
                timeframe=Timeframe.M15,
                open_time=open_time,
                close_time=close_time,
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100.5"),
                volume=Decimal("10"),
                trade_count=2,
            )
        )
        session.commit()
    csv_path = tmp_path / "identity_conflict.csv"
    _write_csv(csv_path, [_valid_row(spot_key, high="102", close="101.5")])

    with pytest.raises(ValueError, match="candle_import_identity_conflict"):
        _import_csv(csv_path, session_factory)

    with session_factory() as session:
        candles = list(session.scalars(select(CandleModel)).all())
        assert len(candles) == 1
        assert candles[0].instrument_ref_id == original_instrument_id
        assert candles[0].symbol_id == original_symbol_id
        assert candles[0].close == Decimal("100.5")
    _assert_no_live_artifacts(session_factory)


def test_candle_import_same_identity_remains_duplicate_safe(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    instrument_id, symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "candles.csv"
    _write_csv(csv_path, [_valid_row(instrument_key)])

    first = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )
    second = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )
    _write_csv(csv_path, [_valid_row(instrument_key, high="103", close="102", volume="12")])
    third = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )

    assert first.inserted_count == 1
    assert second.unchanged_count == 1
    assert third.updated_count == 1
    with session_factory() as session:
        candle = session.scalar(select(CandleModel))
        assert candle is not None
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 1
        assert candle.instrument_ref_id == instrument_id
        assert candle.symbol_id == symbol_id
        assert candle.high == Decimal("103")
        assert candle.close == Decimal("102")
        assert candle.volume == Decimal("12")
    _assert_no_live_artifacts(session_factory)


def test_candle_import_rejects_timeframe_duration_mismatch(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _instrument_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "bad_duration.csv"
    _write_csv(csv_path, [_valid_row(instrument_key, close_time="2026-01-01T00:30:00Z")])

    with pytest.raises(ValueError, match="candle_import_timeframe_duration_mismatch"):
        _import_csv(csv_path, session_factory)

    assert _candle_count(session_factory) == 0
    _assert_no_live_artifacts(session_factory)


@pytest.mark.parametrize(
    "overrides",
    [
        {"open": "NaN"},
        {"open": "sNaN"},
        {"open": "Infinity"},
        {"open": "-Infinity"},
        {"open": "0"},
        {"low": "-1"},
        {"volume": "-1"},
        {"trade_count": "-1"},
        {"high": "99", "low": "100"},
        {"high": "99", "low": "98", "open": "100", "close": "100.5"},
        {"low": "101", "open": "100", "high": "102", "close": "100.5"},
    ],
)
def test_candle_import_rejects_malformed_ohlcv_rows(
    tmp_path: Path,
    overrides: dict[str, str],
) -> None:
    session_factory = build_test_session_factory()
    _instrument_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "bad_ohlcv.csv"
    _write_csv(csv_path, [_valid_row(instrument_key, **overrides)])

    with pytest.raises(ValueError, match="candle_import_invalid_ohlcv"):
        _import_csv(csv_path, session_factory)

    assert _candle_count(session_factory) == 0
    _assert_no_live_artifacts(session_factory)


def test_invalid_import_file_rolls_back_inserts_and_updates(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    instrument_id, symbol_id, instrument_key = seed_symbol(session_factory)
    existing_open = datetime(2026, 1, 1, tzinfo=UTC)
    existing_close = datetime(2026, 1, 1, 0, 15, tzinfo=UTC)
    with session_factory() as session:
        session.add(
            CandleModel(
                environment=Environment.TESTNET,
                venue="hyperliquid",
                instrument_ref_id=instrument_id,
                symbol_id=symbol_id,
                symbol="BTC",
                timeframe=Timeframe.M15,
                open_time=existing_open,
                close_time=existing_close,
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100.5"),
                volume=Decimal("10"),
                trade_count=2,
            )
        )
        session.commit()
    csv_path = tmp_path / "partial_failure.csv"
    _write_csv(
        csv_path,
        [
            _valid_row(instrument_key, high="104", close="103"),
            _valid_row(
                instrument_key,
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
                open="103",
                high="104",
                low="102",
                close="0",
            ),
        ],
    )

    with pytest.raises(ValueError, match="candle_import_invalid_ohlcv"):
        _import_csv(csv_path, session_factory)

    with session_factory() as session:
        candles = list(session.scalars(select(CandleModel)).all())
        assert len(candles) == 1
        assert candles[0].close == Decimal("100.5")
        assert candles[0].high == Decimal("101")
        assert candles[0].volume == Decimal("10")
    _assert_no_live_artifacts(session_factory)


def test_invalid_import_file_does_not_leave_partial_new_candles(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _instrument_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "partial_new_failure.csv"
    _write_csv(
        csv_path,
        [
            _valid_row(instrument_key),
            _valid_row(
                instrument_key,
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
                open="100.5",
                high="102",
                low="100",
                close="101.5",
                volume="-1",
            ),
        ],
    )

    with pytest.raises(ValueError, match="candle_import_invalid_ohlcv"):
        _import_csv(csv_path, session_factory)

    assert _candle_count(session_factory) == 0
    _assert_no_live_artifacts(session_factory)
