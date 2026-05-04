"""Research-only historical candle import helpers for Strategy Validation."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select

from core.domain.enums import Environment, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from db.session import SessionLocal


@dataclass(frozen=True, slots=True)
class StrategyValidationCandleImportResult:
    source_path: str
    source_file_name: str
    source_file_sha256: str
    source_label: str | None
    environment: Environment
    venue: str
    timeframe: Timeframe
    rows_seen: int
    row_count: int
    inserted_count: int
    updated_count: int
    unchanged_count: int
    skipped_count: int
    rejected_count: int
    timestamp_assumption: str
    naive_timestamp_override_used: bool
    warning_reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    creates_live_artifacts: bool = False
    calls_exchange_adapters: bool = False
    calls_private_exchange_endpoints: bool = False
    calls_exchange_order_endpoints: bool = False


def import_strategy_validation_candles_from_path(
    path: str | Path,
    *,
    environment: Environment,
    venue: str,
    timeframe: Timeframe,
    source_label: str | None = None,
    file_format: str = "auto",
    assume_naive_utc: bool = False,
    session_factory: Any = SessionLocal,
) -> StrategyValidationCandleImportResult:
    """Import public/offline historical candles with duplicate-safe upsert semantics.

    The import path is intentionally research-only. It writes only `CandleModel`
    rows and does not create strategy decisions, desired trades, execution
    artifacts, approvals, routing artifacts, or exchange calls.
    """

    import_path = Path(path)
    file_hash = _sha256_file(import_path)
    rows = _load_candle_rows(import_path, file_format=file_format)
    inserted_count = 0
    updated_count = 0
    unchanged_count = 0
    skipped_count = 0
    rejected_count = 0
    warnings: set[str] = set()
    if assume_naive_utc:
        warnings.add("naive_timestamp_override_used")
        warnings.add("timestamp_assumption_assume_naive_utc")

    with session_factory() as session:
        try:
            for row in rows:
                parsed = _parse_candle_row(
                    row,
                    timeframe=timeframe,
                    assume_naive_utc=assume_naive_utc,
                    warning_reason_codes=warnings,
                )
                symbol_model = _resolve_symbol_model(
                    session=session,
                    venue=venue,
                    symbol=parsed["symbol"],
                    instrument_key=parsed.get("instrument_key"),
                )
                existing = session.scalar(
                    select(CandleModel).where(
                        CandleModel.environment == environment,
                        CandleModel.venue == venue,
                        CandleModel.symbol == parsed["symbol"],
                        CandleModel.timeframe == timeframe,
                        CandleModel.open_time == parsed["open_time"],
                    )
                )
                if existing is None:
                    session.add(
                        CandleModel(
                            environment=environment,
                            venue=venue,
                            instrument_ref_id=symbol_model.instrument_ref_id,
                            symbol_id=symbol_model.id,
                            symbol=parsed["symbol"],
                            timeframe=timeframe,
                            open_time=parsed["open_time"],
                            close_time=parsed["close_time"],
                            open=parsed["open"],
                            high=parsed["high"],
                            low=parsed["low"],
                            close=parsed["close"],
                            volume=parsed["volume"],
                            trade_count=parsed["trade_count"],
                        )
                    )
                    inserted_count += 1
                    continue
                _raise_if_identity_conflict(
                    existing=existing,
                    symbol_model=symbol_model,
                    venue=venue,
                    symbol=parsed["symbol"],
                    timeframe=timeframe,
                    open_time=parsed["open_time"],
                )
                if _existing_candle_matches(existing, parsed, symbol_model):
                    unchanged_count += 1
                    continue
                existing.close_time = parsed["close_time"]
                existing.open = parsed["open"]
                existing.high = parsed["high"]
                existing.low = parsed["low"]
                existing.close = parsed["close"]
                existing.volume = parsed["volume"]
                existing.trade_count = parsed["trade_count"]
                updated_count += 1
            session.commit()
        except Exception:
            session.rollback()
            raise

    if source_label:
        warnings.add("source_label_recorded_in_import_summary_only")
    return StrategyValidationCandleImportResult(
        source_path=str(import_path),
        source_file_name=import_path.name,
        source_file_sha256=file_hash,
        source_label=source_label,
        environment=environment,
        venue=venue,
        timeframe=timeframe,
        rows_seen=len(rows),
        row_count=len(rows),
        inserted_count=inserted_count,
        updated_count=updated_count,
        unchanged_count=unchanged_count,
        skipped_count=skipped_count,
        rejected_count=rejected_count,
        timestamp_assumption=(
            "assume_naive_utc" if assume_naive_utc else "timezone_explicit_required"
        ),
        naive_timestamp_override_used=assume_naive_utc,
        warning_reason_codes=tuple(sorted(warnings)),
        limitations=(
            "offline_public_historical_candle_import_only",
            "candle_model_has_no_dedicated_source_provenance_field",
            "source_label_is_reported_in_import_summary_not_persisted_per_candle",
            "timezone_explicit_source_data_is_preferred_for_canonical_evidence",
            "no_strategy_decisions_or_live_execution_artifacts_created",
            "no_exchange_adapter_private_or_order_endpoints_called",
        ),
    )


def strategy_validation_candle_import_result_to_dict(
    result: StrategyValidationCandleImportResult,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready import summary."""

    return _json_ready(asdict(result))


def _load_candle_rows(path: Path, *, file_format: str) -> list[dict[str, Any]]:
    fmt = file_format
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix == ".json":
            fmt = "json"
        else:
            raise ValueError("could not infer candle import file format; use csv or json.")
    if fmt == "csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if fmt == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("candles")
        if not isinstance(payload, list):
            raise ValueError("JSON candle import must be a list or an object with `candles`.")
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError("JSON candle import entries must be objects.")
        return list(payload)
    raise ValueError("candle import format must be auto, csv, or json.")


def _parse_candle_row(
    row: dict[str, Any],
    *,
    timeframe: Timeframe,
    assume_naive_utc: bool,
    warning_reason_codes: set[str],
) -> dict[str, Any]:
    symbol = _required_str(row, "symbol")
    open_time = _parse_datetime(
        _required_str(row, "open_time"),
        field="open_time",
        symbol=symbol,
        assume_naive_utc=assume_naive_utc,
        warning_reason_codes=warning_reason_codes,
    )
    close_time = _parse_datetime(
        _required_str(row, "close_time"),
        field="close_time",
        symbol=symbol,
        assume_naive_utc=assume_naive_utc,
        warning_reason_codes=warning_reason_codes,
    )
    if close_time <= open_time:
        raise ValueError(f"candle close_time must be after open_time for symbol {symbol}.")
    expected_duration = _timeframe_duration(timeframe)
    actual_duration = close_time - open_time
    if actual_duration != expected_duration:
        raise ValueError(
            "candle_import_timeframe_duration_mismatch: "
            f"symbol={symbol} timeframe={timeframe.value} open_time={open_time.isoformat()} "
            f"close_time={close_time.isoformat()} expected_seconds="
            f"{int(expected_duration.total_seconds())} actual_seconds="
            f"{int(actual_duration.total_seconds())}"
        )
    open_price = _positive_price(row, "open", symbol)
    high = _positive_price(row, "high", symbol)
    low = _positive_price(row, "low", symbol)
    close = _positive_price(row, "close", symbol)
    volume = _non_negative_decimal(row, "volume", symbol)
    trade_count = _optional_non_negative_int(row, "trade_count", symbol)
    if high < low:
        raise ValueError(
            f"candle_import_invalid_ohlcv: high must be greater than or equal to low "
            f"for symbol {symbol}."
        )
    if high < max(open_price, close):
        raise ValueError(
            "candle_import_invalid_ohlcv: high must be greater than or equal to "
            f"max(open, close) for symbol {symbol}."
        )
    if low > min(open_price, close):
        raise ValueError(
            "candle_import_invalid_ohlcv: low must be less than or equal to "
            f"min(open, close) for symbol {symbol}."
        )
    return {
        "symbol": symbol,
        "instrument_key": _optional_str(row, "instrument_key"),
        "open_time": open_time,
        "close_time": close_time,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "trade_count": trade_count,
    }


def _resolve_symbol_model(
    *,
    session: Any,
    venue: str,
    symbol: str,
    instrument_key: str | None,
) -> SymbolModel:
    query = select(SymbolModel).where(SymbolModel.venue == venue, SymbolModel.symbol == symbol)
    if instrument_key is not None:
        instrument_id = session.scalar(
            select(InstrumentModel.id).where(InstrumentModel.instrument_key == instrument_key)
        )
        if instrument_id is None:
            raise ValueError(
                "unknown instrument_key for candle import: "
                f"{instrument_key}. Seed or verify Strategy Validation market identity first with "
                "`scripts/seed_strategy_validation_market_identity.py --manifest "
                "configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json`."
            )
        query = query.where(SymbolModel.instrument_ref_id == instrument_id)
    matches = list(session.scalars(query).all())
    if not matches:
        raise ValueError(
            "unknown symbol mapping for candle import: "
            f"venue={venue} symbol={symbol}. Seed or verify Strategy Validation market identity "
            "first with `scripts/seed_strategy_validation_market_identity.py --manifest "
            "configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json`."
        )
    if len(matches) > 1 and instrument_key is None:
        raise ValueError(
            "ambiguous symbol mapping for candle import; provide instrument_key for "
            f"venue={venue} symbol={symbol}"
        )
    return matches[0]


def _existing_candle_matches(
    model: CandleModel,
    parsed: dict[str, Any],
    symbol_model: SymbolModel,
) -> bool:
    return (
        model.instrument_ref_id == symbol_model.instrument_ref_id
        and model.symbol_id == symbol_model.id
        and _coerce_utc(model.close_time) == parsed["close_time"]
        and model.open == parsed["open"]
        and model.high == parsed["high"]
        and model.low == parsed["low"]
        and model.close == parsed["close"]
        and model.volume == parsed["volume"]
        and model.trade_count == parsed["trade_count"]
    )


def _raise_if_identity_conflict(
    *,
    existing: CandleModel,
    symbol_model: SymbolModel,
    venue: str,
    symbol: str,
    timeframe: Timeframe,
    open_time: datetime,
) -> None:
    if (
        existing.symbol_id == symbol_model.id
        and existing.instrument_ref_id == symbol_model.instrument_ref_id
    ):
        return
    raise ValueError(
        "candle_import_identity_conflict: existing_candle_identity_mismatch "
        f"venue={venue} symbol={symbol} timeframe={timeframe.value} "
        f"open_time={open_time.isoformat()} existing_instrument_ref_id="
        f"{existing.instrument_ref_id} existing_symbol_id={existing.symbol_id} "
        f"requested_instrument_ref_id={symbol_model.instrument_ref_id} "
        f"requested_symbol_id={symbol_model.id}"
    )


def _required_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"candle import row missing required field: {key}")
    return str(value).strip()


def _optional_str(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _decimal(row: dict[str, Any], key: str) -> Decimal:
    try:
        return Decimal(str(row[key]))
    except Exception as exc:  # noqa: BLE001 - field context is more useful here.
        raise ValueError(f"candle import row field {key} must be decimal-compatible.") from exc


def _positive_price(row: dict[str, Any], key: str, symbol: str) -> Decimal:
    value = _decimal(row, key)
    if not value.is_finite():
        raise ValueError(
            f"candle_import_invalid_ohlcv: {key} must be finite for symbol {symbol}."
        )
    if value <= 0:
        raise ValueError(
            f"candle_import_invalid_ohlcv: {key} must be greater than 0 for symbol {symbol}."
        )
    return value


def _non_negative_decimal(row: dict[str, Any], key: str, symbol: str) -> Decimal:
    value = _decimal(row, key)
    if not value.is_finite():
        raise ValueError(
            f"candle_import_invalid_ohlcv: {key} must be finite for symbol {symbol}."
        )
    if value < 0:
        raise ValueError(
            f"candle_import_invalid_ohlcv: {key} must be greater than or equal to 0 "
            f"for symbol {symbol}."
        )
    return value


def _optional_non_negative_int(row: dict[str, Any], key: str, symbol: str) -> int | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except Exception as exc:  # noqa: BLE001 - field context is more useful here.
        raise ValueError(f"candle import row field {key} must be integer-compatible.") from exc
    if parsed < 0:
        raise ValueError(
            f"candle_import_invalid_ohlcv: {key} must be greater than or equal to 0 "
            f"for symbol {symbol}."
        )
    return parsed


def _timeframe_duration(timeframe: Timeframe) -> timedelta:
    return {
        Timeframe.M1: timedelta(minutes=1),
        Timeframe.M5: timedelta(minutes=5),
        Timeframe.M15: timedelta(minutes=15),
        Timeframe.H1: timedelta(hours=1),
        Timeframe.H4: timedelta(hours=4),
        Timeframe.D1: timedelta(days=1),
    }[timeframe]


def _parse_datetime(
    value: str,
    *,
    field: str,
    symbol: str,
    assume_naive_utc: bool,
    warning_reason_codes: set[str],
) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        if not assume_naive_utc:
            raise ValueError(
                "candle_import_naive_timestamp: timezone_required_for_candle_import "
                f"symbol={symbol} field={field} value={value!r}. Use timezone-explicit "
                "ISO-8601 timestamps for canonical evidence imports."
            )
        warning_reason_codes.add("candle_import_naive_timestamp_assumed_utc")
        warning_reason_codes.add("timezone_required_for_candle_import_overridden")
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _coerce_utc(value).isoformat()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


__all__ = [
    "StrategyValidationCandleImportResult",
    "import_strategy_validation_candles_from_path",
    "strategy_validation_candle_import_result_to_dict",
]
