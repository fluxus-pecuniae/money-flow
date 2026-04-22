"""Market data bootstrap, persistence, checkpointing, and freshness tracking."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import Timeframe
from core.domain.models import (
    Candle,
    CandleSyncCheckpoint,
    MarketDataHealth,
    OrderBookDepthSummary,
    TopOfBookSnapshot,
)
from core.interfaces.services import CandleSnapshotProvider, ExecutionMarketDataProvider, MarketDataService
from core.logging.setup import get_logger
from db.models import (
    CandleModel,
    InstrumentModel,
    MarketDataCheckpointModel,
    MarketDataHealthModel,
    SymbolModel,
)
from db.session import SessionLocal
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter, _timeframe_delta


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class DefaultMarketDataService(MarketDataService):
    """REST bootstrap and incremental candle sync for tracked symbols.

    Checkpoint semantics:
    - `last_requested_*` stores the exact request window sent to the venue
    - `last_persisted_*` stores the latest persisted candle boundary seen locally
    - `next_sync_start_time` intentionally rewinds by `checkpoint_overlap_bars`
      from the last persisted candle open to tolerate duplicate windows and late
      candle revisions
    """

    def __init__(
        self,
        adapter: CandleSnapshotProvider | ExecutionMarketDataProvider | None = None,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
    ) -> None:
        self.settings = settings or get_settings()
        self.adapter = adapter or HyperliquidExchangeAdapter(self.settings, session_factory=session_factory)
        self._session_factory = session_factory
        self._logger = get_logger(__name__)

    async def bootstrap_candles(
        self,
        symbols: Sequence[str],
        timeframes: Sequence[str],
        lookback_bars: int,
    ) -> int:
        persisted = 0
        for symbol in symbols:
            for timeframe in timeframes:
                persisted += len(await self.ingest_latest_candles(symbol, timeframe, lookback_bars))
        return persisted

    async def ingest_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[Candle]:
        tf_enum = Timeframe(timeframe)
        end_time = _utcnow()
        checkpoint = await self.get_checkpoint(symbol, tf_enum.value)
        start_time = self._resolve_start_time(
            timeframe=tf_enum,
            end_time=end_time,
            limit=limit,
            checkpoint=checkpoint,
        )
        candles = await self.adapter.fetch_candle_snapshot(
            symbol=symbol,
            timeframe=tf_enum.value,
            start_time_ms=int(start_time.timestamp() * 1000),
            end_time_ms=int(end_time.timestamp() * 1000),
        )
        persisted = self._persist_candles(
            symbol=symbol,
            timeframe=tf_enum,
            candles=candles,
            requested_start_time=start_time,
            requested_end_time=end_time,
        )
        self._logger.info(
            "market_data_candles_synced",
            symbol=symbol,
            timeframe=tf_enum.value,
            fetched=len(candles),
            persisted=persisted,
            requested_start_time=start_time.isoformat(),
            requested_end_time=end_time.isoformat(),
        )
        return candles

    async def get_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[Candle]:
        with self._session_factory() as session:
            models = session.scalars(
                select(CandleModel)
                .where(
                    CandleModel.environment == self.settings.app.environment,
                    CandleModel.venue == self.settings.exchange.venue,
                    CandleModel.symbol == symbol,
                    CandleModel.timeframe == Timeframe(timeframe),
                )
                .order_by(CandleModel.open_time.desc())
                .limit(limit)
            ).all()
        return [
            Candle(
                instrument_key=None,
                instrument_ref_id=model.instrument_ref_id,
                venue=model.venue,
                symbol=model.symbol,
                timeframe=model.timeframe,
                open_time=model.open_time,
                close_time=model.close_time,
                open=model.open,
                high=model.high,
                low=model.low,
                close=model.close,
                volume=model.volume,
                trade_count=model.trade_count,
            )
            for model in reversed(models)
        ]

    async def get_health(self) -> MarketDataHealth:
        with self._session_factory() as session:
            last_sync_at = session.scalar(
                select(func.max(MarketDataHealthModel.last_synced_at)).where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == self.settings.exchange.venue,
                )
            )
            last_candle_at = session.scalar(
                select(func.max(MarketDataHealthModel.last_candle_close_time)).where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == self.settings.exchange.venue,
                )
            )
            tracked_symbols = session.scalar(
                select(func.count(SymbolModel.id)).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.is_active.is_(True),
                )
            ) or 0
            tracked_streams = session.scalar(
                select(func.count(MarketDataHealthModel.id)).where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == self.settings.exchange.venue,
                )
            ) or 0
            stale_streams = session.scalar(
                select(func.count(MarketDataHealthModel.id)).where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == self.settings.exchange.venue,
                    MarketDataHealthModel.is_stale.is_(True),
                )
            ) or 0
            latest_error = session.scalar(
                select(MarketDataHealthModel.last_error)
                .where(
                    MarketDataHealthModel.environment == self.settings.app.environment,
                    MarketDataHealthModel.venue == self.settings.exchange.venue,
                    MarketDataHealthModel.last_error.is_not(None),
                )
                .order_by(MarketDataHealthModel.updated_at.desc())
                .limit(1)
            )
        return MarketDataHealth(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            tracked_symbols=int(tracked_symbols),
            tracked_timeframes=int(tracked_streams),
            stale_streams=int(stale_streams),
            last_candle_at=last_candle_at,
            last_sync_at=last_sync_at,
            last_error=latest_error,
        )

    async def get_checkpoint(
        self,
        symbol: str,
        timeframe: str,
    ) -> CandleSyncCheckpoint | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(MarketDataCheckpointModel).where(
                    MarketDataCheckpointModel.environment == self.settings.app.environment,
                    MarketDataCheckpointModel.venue == self.settings.exchange.venue,
                    MarketDataCheckpointModel.symbol == symbol,
                    MarketDataCheckpointModel.timeframe == Timeframe(timeframe),
                )
            )
        if model is None:
            return None
        return CandleSyncCheckpoint(
            venue=model.venue,
            environment=model.environment,
            instrument_key=None,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            timeframe=model.timeframe,
            last_requested_start_time=_coerce_utc(model.last_requested_start_time),
            last_requested_end_time=_coerce_utc(model.last_requested_end_time),
            last_persisted_open_time=_coerce_utc(model.last_persisted_open_time),
            last_persisted_close_time=_coerce_utc(model.last_persisted_close_time),
            next_sync_start_time=_coerce_utc(model.next_sync_start_time),
            overlap_bars=model.overlap_bars,
            last_sync_at=_coerce_utc(model.last_sync_at),
            last_success_at=_coerce_utc(model.last_success_at),
            last_error=model.last_error,
        )

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        provider = self.adapter
        if not hasattr(provider, "get_top_of_book"):
            return None
        return await provider.get_top_of_book(symbol)

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None:
        provider = self.adapter
        if not hasattr(provider, "get_depth_summary"):
            return None
        return await provider.get_depth_summary(symbol, depth_levels=depth_levels)

    async def stream_candles_once(
        self,
        symbols: Sequence[str],
        timeframes: Sequence[str],
        *,
        max_messages: int = 1,
    ) -> int:
        if not hasattr(self.adapter, "stream_candles"):
            return 0
        return await self.adapter.stream_candles(
            symbols=symbols,
            timeframes=timeframes,
            on_message=self.process_stream_message,
            max_messages=max_messages,
        )

    async def process_stream_message(self, payload: dict[str, Any]) -> None:
        channel = payload.get("channel")
        if channel not in {"candle", "subscriptionResponse"}:
            return
        if channel == "subscriptionResponse":
            return
        data = payload.get("data")
        if not isinstance(data, dict):
            return
        symbol = str(data.get("s") or data.get("coin") or "").upper()
        if not symbol:
            return
        timeframe = Timeframe(str(data.get("i") or data.get("interval")).lower())
        candle = Candle(
            instrument_key=await self._lookup_instrument_key(symbol),
            instrument_ref_id=await self._lookup_instrument_ref_id(symbol),
            venue=self.settings.exchange.venue,
            symbol=symbol,
            timeframe=timeframe,
            open_time=datetime.fromtimestamp(int(data["t"]) / 1000, tz=UTC),
            close_time=datetime.fromtimestamp(int(data["T"]) / 1000, tz=UTC),
            open=self._to_decimal(data["o"]),
            high=self._to_decimal(data["h"]),
            low=self._to_decimal(data["l"]),
            close=self._to_decimal(data["c"]),
            volume=self._to_decimal(data.get("v", "0")),
            trade_count=None,
        )
        self._persist_candles(
            symbol,
            timeframe,
            [candle],
            requested_start_time=candle.open_time,
            requested_end_time=candle.close_time,
        )

    def _resolve_start_time(
        self,
        *,
        timeframe: Timeframe,
        end_time: datetime,
        limit: int,
        checkpoint: CandleSyncCheckpoint | None,
    ) -> datetime:
        if checkpoint and checkpoint.next_sync_start_time is not None:
            return min(checkpoint.next_sync_start_time, end_time)
        return end_time - (_timeframe_delta(timeframe) * limit)

    def _persist_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        candles: Sequence[Candle],
        *,
        requested_start_time: datetime,
        requested_end_time: datetime,
    ) -> int:
        persisted = 0
        with self._session_factory() as session:
            symbol_model = session.scalar(
                select(SymbolModel).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
            if symbol_model is None:
                raise ValueError(f"Unknown symbol for market data sync: {symbol}")

            latest_open_time: datetime | None = None
            latest_close_time: datetime | None = None
            for candle in candles:
                open_time = candle.open_time.astimezone(UTC)
                close_time = candle.close_time.astimezone(UTC)
                latest_open_time = open_time
                latest_close_time = close_time
                model = session.scalar(
                    select(CandleModel).where(
                        CandleModel.environment == self.settings.app.environment,
                        CandleModel.venue == self.settings.exchange.venue,
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                        CandleModel.open_time == open_time,
                    )
                )
                if model is None:
                    session.add(
                        CandleModel(
                            environment=self.settings.app.environment,
                            venue=self.settings.exchange.venue,
                            instrument_ref_id=symbol_model.instrument_ref_id,
                            symbol_id=symbol_model.id,
                            symbol=symbol,
                            timeframe=timeframe,
                            open_time=open_time,
                            close_time=close_time,
                            open=candle.open,
                            high=candle.high,
                            low=candle.low,
                            close=candle.close,
                            volume=candle.volume,
                            trade_count=candle.trade_count,
                        )
                    )
                    persisted += 1
                else:
                    model.close_time = close_time
                    model.open = candle.open
                    model.high = candle.high
                    model.low = candle.low
                    model.close = candle.close
                    model.volume = candle.volume
                    model.trade_count = candle.trade_count

            self._upsert_health(
                session=session,
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
                last_error=None,
            )
            self._upsert_checkpoint(
                session=session,
                symbol_model=symbol_model,
                symbol=symbol,
                timeframe=timeframe,
                requested_start_time=requested_start_time,
                requested_end_time=requested_end_time,
                latest_open_time=latest_open_time,
                latest_close_time=latest_close_time,
                last_error=None,
            )
            session.commit()
        return persisted

    def _upsert_checkpoint(
        self,
        *,
        session: Any,
        symbol_model: SymbolModel,
        symbol: str,
        timeframe: Timeframe,
        requested_start_time: datetime,
        requested_end_time: datetime,
        latest_open_time: datetime | None,
        latest_close_time: datetime | None,
        last_error: str | None,
    ) -> None:
        model = session.scalar(
            select(MarketDataCheckpointModel).where(
                MarketDataCheckpointModel.environment == self.settings.app.environment,
                MarketDataCheckpointModel.venue == self.settings.exchange.venue,
                MarketDataCheckpointModel.symbol == symbol,
                MarketDataCheckpointModel.timeframe == timeframe,
            )
        )
        overlap_bars = self.settings.market_data.checkpoint_overlap_bars
        next_sync_start_time = None
        if latest_open_time is not None:
            next_sync_start_time = latest_open_time - (_timeframe_delta(timeframe) * overlap_bars)
        now = _utcnow()
        if model is None:
            session.add(
                MarketDataCheckpointModel(
                    environment=self.settings.app.environment,
                    venue=self.settings.exchange.venue,
                    instrument_ref_id=symbol_model.instrument_ref_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    last_requested_start_time=requested_start_time,
                    last_requested_end_time=requested_end_time,
                    last_persisted_open_time=latest_open_time,
                    last_persisted_close_time=latest_close_time,
                    next_sync_start_time=next_sync_start_time,
                    overlap_bars=overlap_bars,
                    last_sync_at=now,
                    last_success_at=now if last_error is None else None,
                    last_error=last_error,
                )
            )
            return
        model.instrument_ref_id = symbol_model.instrument_ref_id
        model.last_requested_start_time = requested_start_time
        model.last_requested_end_time = requested_end_time
        model.last_persisted_open_time = latest_open_time
        model.last_persisted_close_time = latest_close_time
        model.next_sync_start_time = next_sync_start_time
        model.overlap_bars = overlap_bars
        model.last_sync_at = now
        if last_error is None:
            model.last_success_at = now
        model.last_error = last_error

    def _upsert_health(
        self,
        *,
        session: Any,
        symbol: str,
        timeframe: Timeframe,
        candles: Sequence[Candle],
        last_error: str | None,
    ) -> None:
        model = session.scalar(
            select(MarketDataHealthModel).where(
                MarketDataHealthModel.environment == self.settings.app.environment,
                MarketDataHealthModel.venue == self.settings.exchange.venue,
                MarketDataHealthModel.symbol == symbol,
                MarketDataHealthModel.timeframe == timeframe,
            )
        )
        last_candle_open = candles[-1].open_time if candles else None
        last_candle_close = candles[-1].close_time if candles else None
        is_stale = False
        if last_candle_close is not None:
            age_seconds = (_utcnow() - last_candle_close).total_seconds()
            is_stale = age_seconds > self.settings.market_data.stale_after_seconds
        if model is None:
            session.add(
                MarketDataHealthModel(
                    environment=self.settings.app.environment,
                    venue=self.settings.exchange.venue,
                    symbol=symbol,
                    timeframe=timeframe,
                    last_candle_open_time=last_candle_open,
                    last_candle_close_time=last_candle_close,
                    last_synced_at=_utcnow(),
                    last_success_at=_utcnow() if last_error is None else None,
                    stale_after_seconds=self.settings.market_data.stale_after_seconds,
                    is_stale=is_stale,
                    last_error=last_error,
                )
            )
            return
        model.last_candle_open_time = last_candle_open
        model.last_candle_close_time = last_candle_close
        model.last_synced_at = _utcnow()
        if last_error is None:
            model.last_success_at = _utcnow()
        model.stale_after_seconds = self.settings.market_data.stale_after_seconds
        model.is_stale = is_stale
        model.last_error = last_error

    async def _lookup_instrument_ref_id(self, symbol: str) -> str | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(SymbolModel.instrument_ref_id).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
        return str(model) if model else None

    async def _lookup_instrument_key(self, symbol: str) -> str | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(InstrumentModel.instrument_key)
                .join(SymbolModel, SymbolModel.instrument_ref_id == InstrumentModel.id)
                .where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
        return str(model) if model else None

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        return Decimal(str(value))
