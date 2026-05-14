"""Hyperliquid public-mainnet market-data connector for PT-RT1.1B.

This module is deliberately public-read-only. It accepts only the Hyperliquid
mainnet ``/info`` endpoint and the PT-RT1 strategy-truth allowlist. It has no
API-key, private-account, signed, or order path.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

from services.paper_runtime.pt_rt1 import (
    DEFAULT_SCANNER_SOURCES,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_REQUESTED_SCANNER_SYMBOLS,
    TIMEFRAME_DURATIONS,
    Candle,
    DataHealth,
    ScannerUniverseRow,
    canonical_candle_close,
    resolve_top20_universe,
    validate_strategy_truth_payload,
)


PublicInfoTransport = Callable[[str, Mapping[str, Any], float], Any]


@dataclass(frozen=True)
class PublicInfoResult:
    ok: bool
    endpoint: str
    endpoint_category: str
    info_type: str
    fetched_at_utc: str
    payload: Any | None
    data_health: DataHealth
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CandleSnapshotResult:
    ok: bool
    symbol: str
    timeframe: str
    candles: tuple[Candle, ...]
    latest_candle_update: str | None
    data_health: DataHealth
    reason_codes: tuple[str, ...]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ms_to_dt(value: Any) -> datetime:
    return datetime.fromtimestamp(float(Decimal(str(value)) / Decimal("1000")), tz=UTC)


def _default_transport(endpoint: str, payload: Mapping[str, Any], timeout_seconds: float) -> Any:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 - public mainnet endpoint only, validated by caller.
        body = response.read().decode("utf-8")
    return json.loads(body)


class HyperliquidPublicMarketDataConnector:
    """Public-read-only Hyperliquid mainnet info connector."""

    endpoint = PT_RT1_MAINNET_INFO_URL
    endpoint_category = "public_read_only"

    def __init__(
        self,
        *,
        endpoint: str = PT_RT1_MAINNET_INFO_URL,
        timeout_seconds: float = 10.0,
        transport: PublicInfoTransport | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    def post_info(self, info_type: str, req: Mapping[str, Any] | None = None) -> PublicInfoResult:
        payload: dict[str, Any] = {"type": info_type}
        if req is not None:
            payload["req"] = dict(req)
        validation = validate_strategy_truth_payload(endpoint=self.endpoint, payload=payload, headers={})
        if not validation.allowed:
            return PublicInfoResult(
                ok=False,
                endpoint=self.endpoint,
                endpoint_category=self.endpoint_category,
                info_type=info_type,
                fetched_at_utc=_now_iso(),
                payload=None,
                data_health=DataHealth.UNAVAILABLE,
                reason_codes=validation.reason_codes,
            )
        try:
            response_payload = self._transport(self.endpoint, payload, self.timeout_seconds)
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            return PublicInfoResult(
                ok=False,
                endpoint=self.endpoint,
                endpoint_category=self.endpoint_category,
                info_type=info_type,
                fetched_at_utc=_now_iso(),
                payload=None,
                data_health=DataHealth.UNAVAILABLE,
                reason_codes=(f"public_mainnet_{info_type}_unavailable", "public_mainnet_network_unavailable", exc.__class__.__name__),
            )
        return PublicInfoResult(
            ok=True,
            endpoint=self.endpoint,
            endpoint_category=self.endpoint_category,
            info_type=info_type,
            fetched_at_utc=_now_iso(),
            payload=response_payload,
            data_health=DataHealth.HEALTHY,
            reason_codes=("public_mainnet_data_connected",),
        )

    def fetch_meta(self) -> PublicInfoResult:
        return self.post_info("meta")

    def fetch_meta_and_asset_contexts(self) -> PublicInfoResult:
        return self.post_info("metaAndAssetCtxs")

    def fetch_all_mids(self) -> PublicInfoResult:
        return self.post_info("allMids")

    def fetch_candle_snapshot(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> CandleSnapshotResult:
        req = {
            "coin": symbol,
            "interval": timeframe,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
        }
        result = self.post_info("candleSnapshot", req=req)
        if not result.ok or not isinstance(result.payload, list):
            return CandleSnapshotResult(
                ok=False,
                symbol=symbol.upper(),
                timeframe=timeframe,
                candles=(),
                latest_candle_update=None,
                data_health=result.data_health,
                reason_codes=result.reason_codes or ("public_mainnet_candles_unavailable",),
            )
        return normalize_candle_snapshot_payload(result.payload, symbol=symbol, timeframe=timeframe)


def normalize_meta_universe(payload: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(payload, Mapping):
        universe = payload.get("universe", [])
    elif isinstance(payload, Sequence) and payload and isinstance(payload[0], Mapping):
        universe = payload[0].get("universe", [])
    else:
        universe = []
    return tuple(item for item in universe if isinstance(item, Mapping))


def normalize_all_mids(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    return {str(key).upper(): value for key, value in payload.items()}


def normalize_candle_snapshot_payload(payload: Sequence[Mapping[str, Any]], *, symbol: str, timeframe: str) -> CandleSnapshotResult:
    reasons: list[str] = []
    candles: list[Candle] = []
    previous_open: datetime | None = None
    for row in payload:
        try:
            open_time = _ms_to_dt(row.get("t"))
            candle = Candle(
                symbol=symbol.upper(),
                timeframe=timeframe,
                open_time=open_time,
                close_time=open_time + TIMEFRAME_DURATIONS[timeframe],
                open=Decimal(str(row.get("o"))),
                high=Decimal(str(row.get("h"))),
                low=Decimal(str(row.get("l"))),
                close=Decimal(str(row.get("c"))),
                volume=Decimal(str(row.get("v", "0"))),
            )
        except Exception:  # noqa: BLE001 - convert malformed public rows to data-health reasons.
            reasons.append("public_mainnet_candle_row_malformed")
            continue
        validation_reasons = candle.validate()
        if validation_reasons:
            reasons.extend(validation_reasons)
        if previous_open is not None and candle.open_time <= previous_open:
            reasons.append("out_of_order_candle")
        previous_open = candle.open_time
        candles.append(candle)
    if not candles:
        reasons.append("public_mainnet_candles_unavailable")
    latest = canonical_candle_close(candles[-1]) if candles else None
    health = DataHealth.HEALTHY if candles and not reasons else DataHealth.DEGRADED if candles else DataHealth.UNAVAILABLE
    if candles and not reasons:
        reasons.append("public_mainnet_data_connected")
    return CandleSnapshotResult(
        ok=bool(candles) and health == DataHealth.HEALTHY,
        symbol=symbol.upper(),
        timeframe=timeframe,
        candles=tuple(candles),
        latest_candle_update=latest.replace(microsecond=0).isoformat().replace("+00:00", "Z") if latest else None,
        data_health=health,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def resolve_watchlist_from_public_data(
    *,
    meta_payload: Any,
    mids_payload: Any,
    requested_symbols: Sequence[str] = PT_RT1_REQUESTED_SCANNER_SYMBOLS,
) -> tuple[ScannerUniverseRow, ...]:
    return resolve_top20_universe(
        requested_symbols,
        hyperliquid_meta=normalize_meta_universe(meta_payload),
        mids=normalize_all_mids(mids_payload),
        symbol_sources=DEFAULT_SCANNER_SOURCES,
    )


def candle_request_window(*, timeframe: str, now: datetime, bars: int = 260) -> tuple[datetime, datetime]:
    duration = TIMEFRAME_DURATIONS[timeframe]
    end_time = now.astimezone(UTC)
    start_time = end_time - (duration * bars)
    return start_time, end_time
