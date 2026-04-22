"""Indicator computation and persistence service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import Timeframe
from core.domain.models import Candle, IndicatorSnapshot
from core.interfaces.services import IndicatorService
from core.logging.setup import get_logger
from db.models import CandleModel, IndicatorSnapshotModel, InstrumentModel, SymbolModel
from db.session import SessionLocal

MIN_COMPLETE_BARS = 35


def _to_decimal(value: float | None, places: str = "0.000000000001") -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(places))


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class DefaultIndicatorService(IndicatorService):
    def __init__(self, settings: AppSettings | None = None, *, session_factory: Any = SessionLocal) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self._logger = get_logger(__name__)

    async def compute_snapshot(self, candles: Sequence[Candle]) -> IndicatorSnapshot:
        snapshots = self._compute_snapshots(candles)
        complete = [snapshot for snapshot in snapshots if _snapshot_complete(snapshot)]
        if not complete:
            raise ValueError("Insufficient candle history to compute a complete indicator snapshot.")
        return complete[-1]

    async def refresh_snapshots(
        self,
        instrument_ref_id: str,
        symbol: str,
        venue: str,
        timeframe: str,
    ) -> int:
        candles = await self._load_candles(
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
            venue=venue,
            timeframe=timeframe,
        )
        snapshots = self._compute_snapshots(candles)
        persisted = 0
        with self._session_factory() as session:
            symbol_model = session.scalar(
                select(SymbolModel).where(
                    SymbolModel.instrument_ref_id == instrument_ref_id,
                    SymbolModel.symbol == symbol,
                    SymbolModel.venue == venue,
                )
            )
            if symbol_model is None:
                raise ValueError(f"Unknown symbol/instrument mapping for indicator refresh: {symbol}")
            for snapshot in snapshots:
                if not _snapshot_complete(snapshot):
                    continue
                model = session.scalar(
                    select(IndicatorSnapshotModel).where(
                        IndicatorSnapshotModel.environment == self.settings.app.environment,
                        IndicatorSnapshotModel.venue == venue,
                        IndicatorSnapshotModel.instrument_ref_id == instrument_ref_id,
                        IndicatorSnapshotModel.timeframe == snapshot.timeframe,
                        IndicatorSnapshotModel.as_of == snapshot.as_of,
                    )
                )
                if model is None:
                    model = IndicatorSnapshotModel(
                        environment=self.settings.app.environment,
                        venue=venue,
                        instrument_ref_id=instrument_ref_id,
                        symbol_id=symbol_model.id,
                        symbol=symbol,
                        timeframe=snapshot.timeframe,
                        as_of=snapshot.as_of,
                        ema_5=snapshot.ema_5,
                        ema_10=snapshot.ema_10,
                        sma_20=snapshot.sma_20,
                        rsi_14=snapshot.rsi_14,
                        macd=snapshot.macd,
                        macd_signal=snapshot.macd_signal,
                        macd_histogram=snapshot.macd_histogram,
                    )
                    session.add(model)
                    persisted += 1
                else:
                    model.ema_5 = snapshot.ema_5
                    model.ema_10 = snapshot.ema_10
                    model.sma_20 = snapshot.sma_20
                    model.rsi_14 = snapshot.rsi_14
                    model.macd = snapshot.macd
                    model.macd_signal = snapshot.macd_signal
                    model.macd_histogram = snapshot.macd_histogram
            session.commit()
        self._logger.info(
            "indicator_snapshots_refreshed",
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
            venue=venue,
            timeframe=timeframe,
            persisted=persisted,
            total_complete=sum(1 for snapshot in snapshots if _snapshot_complete(snapshot)),
        )
        return persisted

    async def load_latest_snapshot(
        self,
        instrument_ref_id: str,
        venue: str,
        timeframe: str,
    ) -> IndicatorSnapshot | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(IndicatorSnapshotModel)
                .where(
                    IndicatorSnapshotModel.environment == self.settings.app.environment,
                    IndicatorSnapshotModel.venue == venue,
                    IndicatorSnapshotModel.instrument_ref_id == instrument_ref_id,
                    IndicatorSnapshotModel.timeframe == Timeframe(timeframe),
                )
                .order_by(IndicatorSnapshotModel.as_of.desc())
                .limit(1)
            )
            instrument_key = None
            if model is not None and model.instrument_ref_id is not None:
                instrument_key = session.scalar(
                    select(InstrumentModel.instrument_key).where(InstrumentModel.id == model.instrument_ref_id)
                )
        if model is None:
            return None
        return IndicatorSnapshot(
            instrument_key=str(instrument_key) if instrument_key is not None else None,
            instrument_ref_id=model.instrument_ref_id,
            venue=model.venue,
            symbol=model.symbol,
            timeframe=model.timeframe,
            as_of=model.as_of,
            ema_5=model.ema_5,
            ema_10=model.ema_10,
            sma_20=model.sma_20,
            rsi_14=model.rsi_14,
            macd=model.macd,
            macd_signal=model.macd_signal,
            macd_histogram=model.macd_histogram,
        )

    async def _load_candles(
        self,
        *,
        instrument_ref_id: str,
        symbol: str,
        venue: str,
        timeframe: str,
    ) -> Sequence[Candle]:
        with self._session_factory() as session:
            models = session.scalars(
                select(CandleModel)
                .where(
                    CandleModel.environment == self.settings.app.environment,
                    CandleModel.venue == venue,
                    CandleModel.instrument_ref_id == instrument_ref_id,
                    CandleModel.symbol == symbol,
                    CandleModel.timeframe == Timeframe(timeframe),
                )
                .order_by(CandleModel.open_time.asc())
            ).all()
            instrument_key = session.scalar(
                select(InstrumentModel.instrument_key).where(InstrumentModel.id == instrument_ref_id)
            )
        return [
            Candle(
                instrument_key=str(instrument_key) if instrument_key is not None else None,
                instrument_ref_id=model.instrument_ref_id,
                venue=model.venue,
                symbol=model.symbol,
                timeframe=model.timeframe,
                open_time=_coerce_utc(model.open_time),
                close_time=_coerce_utc(model.close_time),
                open=model.open,
                high=model.high,
                low=model.low,
                close=model.close,
                volume=model.volume,
                trade_count=model.trade_count,
            )
            for model in models
        ]

    def _compute_snapshots(self, candles: Sequence[Candle]) -> list[IndicatorSnapshot]:
        if not candles:
            return []
        closes = [float(candle.close) for candle in candles]
        ema5 = _ema_series(closes, 5)
        ema10 = _ema_series(closes, 10)
        sma20 = _sma_series(closes, 20)
        rsi14 = _rsi_series(closes, 14)
        macd_line, signal_line, histogram = _macd_series(closes)
        snapshots: list[IndicatorSnapshot] = []
        for index, candle in enumerate(candles):
            snapshots.append(
                IndicatorSnapshot(
                    instrument_key=candle.instrument_key,
                    instrument_ref_id=candle.instrument_ref_id,
                    venue=candle.venue,
                    symbol=candle.symbol,
                    timeframe=candle.timeframe,
                    as_of=candle.close_time.astimezone(UTC),
                    ema_5=_to_decimal(ema5[index]),
                    ema_10=_to_decimal(ema10[index]),
                    sma_20=_to_decimal(sma20[index]),
                    rsi_14=_to_decimal(rsi14[index], places="0.0001"),
                    macd=_to_decimal(macd_line[index]),
                    macd_signal=_to_decimal(signal_line[index]),
                    macd_histogram=_to_decimal(histogram[index]),
                )
            )
        return snapshots


def _sma_series(values: Sequence[float], period: int) -> list[float | None]:
    output: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            output.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        output.append(sum(window) / period)
    return output


def _ema_series(values: Sequence[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return output
    seed = sum(values[:period]) / period
    multiplier = 2.0 / (period + 1)
    ema = seed
    output[period - 1] = ema
    for index in range(period, len(values)):
        ema = ((values[index] - ema) * multiplier) + ema
        output[index] = ema
    return output


def _rsi_series(values: Sequence[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return output
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, period + 1):
        delta = values[index] - values[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    output[period] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
    for index in range(period + 1, len(values)):
        delta = values[index] - values[index - 1]
        gain = max(delta, 0.0)
        loss = abs(min(delta, 0.0))
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        output[index] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
    return output


def _macd_series(values: Sequence[float]) -> tuple[list[float | None], list[float | None], list[float | None]]:
    ema12 = _ema_series(values, 12)
    ema26 = _ema_series(values, 26)
    macd_line: list[float | None] = []
    for fast, slow in zip(ema12, ema26, strict=False):
        if fast is None or slow is None:
            macd_line.append(None)
        else:
            macd_line.append(fast - slow)

    signal_line: list[float | None] = [None] * len(values)
    macd_values = [value for value in macd_line if value is not None]
    if len(macd_values) >= 9:
        seed = sum(macd_values[:9]) / 9
        multiplier = 2.0 / (9 + 1)
        ema = seed
        first_index = macd_line.index(macd_values[8])
        signal_line[first_index] = ema
        for index in range(first_index + 1, len(values)):
            current = macd_line[index]
            if current is None:
                continue
            ema = ((current - ema) * multiplier) + ema
            signal_line[index] = ema

    histogram: list[float | None] = []
    for macd_value, signal_value in zip(macd_line, signal_line, strict=False):
        if macd_value is None or signal_value is None:
            histogram.append(None)
        else:
            histogram.append(macd_value - signal_value)
    return macd_line, signal_line, histogram


def _snapshot_complete(snapshot: IndicatorSnapshot) -> bool:
    return all(
        value is not None
        for value in (
            snapshot.ema_5,
            snapshot.ema_10,
            snapshot.sma_20,
            snapshot.rsi_14,
            snapshot.macd,
            snapshot.macd_signal,
            snapshot.macd_histogram,
        )
    )
