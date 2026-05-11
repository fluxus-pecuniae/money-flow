"""SV2.0 Hyperliquid public-data helpers.

This module is deliberately read-only from an exchange perspective. It builds
mainnet public metadata/candle requests, resolves market identity, normalizes
public candleSnapshot rows, and prepares founder-readable readiness/evidence
summary structures. It does not call private, signed, testnet, or order
endpoints.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


HYPERLIQUID_MAINNET_PUBLIC_INFO_URL = "https://api.hyperliquid.xyz/info"
SV20_REPORT_NAME = "sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild"
SV20_READINESS_REPORT_NAME = "sv2_0_historical_data_refresh_1d_and_expanded_universe_readiness"
SV20_MONEY_FLOW_VERSION = "money_flow_v1_2"
SV20_TARGET_START_AT = "2025-01-01T00:00:00Z"
SV20_REQUESTED_SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "DOGE", "HYPE", "BNB", "SUI", "AVAX", "SHIB")
SV20_TIMEFRAMES = ("15m", "1h", "4h", "1d")
SV20_TIMEFRAME_DISPLAY_LABELS = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}
SV20_COMPONENT_BY_TIMEFRAME = {
    "15m": "sleeve_15m",
    "1h": "sleeve_1h",
    "4h": "sleeve_4h",
    "1d": "sleeve_1d",
}
SV20_HYPERLIQUID_INTERVAL_BY_TIMEFRAME = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}
SV20_TIMEFRAME_SECONDS = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
}
SV20_PUBLIC_CANDLE_LIMIT = 5000

SV20_SLEEVE_SETTINGS = {
    "sleeve_15m": {
        "timeframe": "15m",
        "history": 35,
        "rsi_band": "52-66",
        "overbought": 72,
        "trim": 78,
        "max_ema5_extension_pct": "1.8%",
        "macd": "required",
    },
    "sleeve_1h": {
        "timeframe": "1h",
        "history": 35,
        "rsi_band": "50-68",
        "overbought": 74,
        "trim": 80,
        "max_ema5_extension_pct": "2.0%",
        "macd": "required",
    },
    "sleeve_4h": {
        "timeframe": "4h",
        "history": 40,
        "rsi_band": "48-70",
        "overbought": 76,
        "trim": 82,
        "max_ema5_extension_pct": "2.5%",
        "macd": "required",
    },
    "sleeve_1d": {
        "timeframe": "1d",
        "display_timeframe": "1D",
        "history": 50,
        "rsi_band": "46-72",
        "overbought": 78,
        "trim": 84,
        "max_ema5_extension_pct": "3.0%",
        "macd": "required",
        "baseline_status": "initial_baseline_not_optimized",
    },
}


@dataclass(frozen=True, slots=True)
class SV20MarketIdentity:
    requested_symbol: str
    resolved_venue_symbol: str | None
    canonical_symbol: str
    asset_id: int | None
    sz_decimals: int | None
    market_type: str
    product_type: str
    base_asset: str | None
    quote_asset: str | None
    settlement_asset: str | None
    active: bool
    supported: bool
    strategy_validation_eligible: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SV20CandleDataset:
    requested_symbol: str
    resolved_venue_symbol: str | None
    timeframe: str
    fetch_attempted: bool
    fetched: bool
    normalized: bool
    raw_file_written: bool
    staged_for_replay: bool
    db_imported: bool
    canonical_evidence_ready: bool
    target_window_ready: bool
    candles: tuple[dict[str, Any], ...]
    import_reason_codes: tuple[str, ...] = ()
    fetch_reason_codes: tuple[str, ...] = ()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-explicit: {value}")
    return parsed.astimezone(UTC)


def unix_ms(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp() * 1000)


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def hyperliquid_meta_payload() -> dict[str, Any]:
    return {"type": "meta"}


def hyperliquid_candle_snapshot_payload(
    *,
    coin: str,
    timeframe: str,
    start_at: datetime,
    end_at: datetime,
) -> dict[str, Any]:
    canonical_timeframe = canonical_sv20_timeframe(timeframe)
    interval = SV20_HYPERLIQUID_INTERVAL_BY_TIMEFRAME[canonical_timeframe]
    return {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": unix_ms(start_at),
            "endTime": unix_ms(end_at),
        },
    }


def fetch_hyperliquid_public_info(
    payload: dict[str, Any],
    *,
    url: str = HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    timeout_seconds: float = 20.0,
) -> Any:
    if url != HYPERLIQUID_MAINNET_PUBLIC_INFO_URL:
        raise ValueError("sv2_requires_hyperliquid_mainnet_public_info_endpoint")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def extract_hyperliquid_universe(meta_payload: Any) -> list[dict[str, Any]]:
    if isinstance(meta_payload, dict) and isinstance(meta_payload.get("universe"), list):
        return list(meta_payload["universe"])
    if (
        isinstance(meta_payload, list)
        and meta_payload
        and isinstance(meta_payload[0], dict)
        and isinstance(meta_payload[0].get("universe"), list)
    ):
        return list(meta_payload[0]["universe"])
    return []


def resolve_hyperliquid_market_identities(
    meta_payload: Any,
    *,
    requested_symbols: tuple[str, ...] = SV20_REQUESTED_SYMBOLS,
) -> list[SV20MarketIdentity]:
    universe = extract_hyperliquid_universe(meta_payload)
    by_upper = {str(row.get("name") or "").upper(): (index, row) for index, row in enumerate(universe)}
    identities: list[SV20MarketIdentity] = []
    for requested_symbol in requested_symbols:
        lookup = requested_symbol.upper()
        index_row = by_upper.get(lookup)
        reason_codes: list[str] = []
        alias_detected = False
        if index_row is None and lookup == "SHIB":
            candidate_keys = {
                candidate.upper()
                for candidate in ("SHIB", "KSHIB", "kSHIB", "1000SHIB", "SHIB1000")
                if candidate.upper() in by_upper
            }
            candidates = sorted(candidate_keys)
            if len(candidates) == 1:
                index_row = by_upper[candidates[0]]
                reason_codes.append("venue_symbol_alias_detected")
                alias_detected = True
            elif len(candidates) > 1:
                identities.append(
                    SV20MarketIdentity(
                        requested_symbol=requested_symbol,
                        resolved_venue_symbol=None,
                        canonical_symbol=requested_symbol,
                        asset_id=None,
                        sz_decimals=None,
                        market_type="perpetual",
                        product_type="linear",
                        base_asset=None,
                        quote_asset=None,
                        settlement_asset=None,
                        active=False,
                        supported=False,
                        strategy_validation_eligible=False,
                        reason_codes=("venue_symbol_alias_unverified",),
                    )
                )
                continue
        if index_row is None:
            identities.append(
                SV20MarketIdentity(
                    requested_symbol=requested_symbol,
                    resolved_venue_symbol=None,
                    canonical_symbol=requested_symbol,
                    asset_id=None,
                    sz_decimals=None,
                    market_type="perpetual",
                    product_type="linear",
                    base_asset=None,
                    quote_asset=None,
                    settlement_asset=None,
                    active=False,
                    supported=False,
                    strategy_validation_eligible=False,
                    reason_codes=("symbol_not_in_hyperliquid_meta",),
                )
            )
            continue
        asset_id, row = index_row
        resolved_symbol = str(row.get("name") or "")
        active = not bool(row.get("isDelisted") or row.get("delisted"))
        if not alias_detected:
            reason_codes.append("symbol_supported")
        else:
            reason_codes.append("symbol_supported")
        if not active:
            reason_codes.append("market_not_active")
        sz_decimals = row.get("szDecimals")
        if sz_decimals is None:
            reason_codes.append("paper_precision_metadata_missing")
        supported = bool(active and resolved_symbol and sz_decimals is not None)
        identities.append(
            SV20MarketIdentity(
                requested_symbol=requested_symbol,
                resolved_venue_symbol=resolved_symbol,
                canonical_symbol=requested_symbol,
                asset_id=asset_id,
                sz_decimals=int(sz_decimals) if sz_decimals is not None else None,
                market_type="perpetual",
                product_type="linear",
                base_asset=requested_symbol,
                quote_asset="USDC",
                settlement_asset="USDC",
                active=active,
                supported=supported,
                strategy_validation_eligible=supported,
                reason_codes=tuple(reason_codes),
            )
        )
    return identities


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value}") from exc


def _parse_millis(value: Any) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def canonical_sv20_timeframe(value: str) -> str:
    normalized = str(value).strip()
    if normalized == "1D":
        return "1d"
    if normalized in SV20_TIMEFRAMES:
        return normalized
    raise ValueError(f"unsupported_sv20_timeframe:{value}")


def display_sv20_timeframe(value: str) -> str:
    return SV20_TIMEFRAME_DISPLAY_LABELS.get(canonical_sv20_timeframe(value), value)


def normalize_hyperliquid_candle_snapshot(
    payload: Any,
    *,
    requested_symbol: str,
    resolved_venue_symbol: str,
    timeframe: str,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(payload, list):
        raise ValueError("hyperliquid_candleSnapshot_payload_not_list")
    canonical_timeframe = canonical_sv20_timeframe(timeframe)
    seconds = SV20_TIMEFRAME_SECONDS[canonical_timeframe]
    rows: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError("hyperliquid_candleSnapshot_row_not_object")
        open_time = _parse_millis(row.get("t"))
        raw_venue_close_time = (
            _parse_millis(row["T"]) if row.get("T") is not None else open_time + timedelta(seconds=seconds)
        )
        close_time = open_time + timedelta(seconds=seconds)
        open_price = _decimal(row.get("o"))
        high = _decimal(row.get("h"))
        low = _decimal(row.get("l"))
        close = _decimal(row.get("c"))
        volume = _decimal(row.get("v") or "0")
        if min(open_price, high, low, close) <= 0:
            raise ValueError("historical_import_blocked_invalid_ohlc")
        if volume < 0:
            raise ValueError("historical_import_blocked_negative_volume")
        if close_time <= open_time:
            raise ValueError("historical_import_blocked_invalid_duration")
        if int((close_time - open_time).total_seconds()) != seconds:
            raise ValueError("historical_import_blocked_invalid_duration")
        rows.append(
            {
                "symbol": requested_symbol,
                "venue_symbol": resolved_venue_symbol,
                "timeframe": canonical_timeframe,
                "display_timeframe": display_sv20_timeframe(canonical_timeframe),
                "open_time": iso_utc(open_time),
                "close_time": iso_utc(close_time),
                "raw_venue_close_time": iso_utc(raw_venue_close_time),
                "open": str(open_price),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": str(volume),
                "trade_count": int(row["n"]) if row.get("n") is not None else None,
                "source": "hyperliquid_public_mainnet_candleSnapshot",
            }
        )
    return tuple(rows)


def expected_count_from_target(*, latest: str | None, timeframe: str) -> int | None:
    if not latest:
        return None
    seconds = SV20_TIMEFRAME_SECONDS[canonical_sv20_timeframe(timeframe)]
    latest_dt = parse_utc(latest)
    target_dt = parse_utc(SV20_TARGET_START_AT)
    delta = int((latest_dt - target_dt).total_seconds())
    if delta <= 0:
        return 0
    return delta // seconds


def coverage_percent(candle_count: int, expected: int | None) -> str | None:
    if expected is None or expected <= 0:
        return None
    return f"{(Decimal(candle_count) / Decimal(expected)):.8f}"


def target_start_is_covered(earliest: str | None, timeframe: str) -> bool:
    if not earliest:
        return False
    earliest_dt = parse_utc(earliest)
    target_dt = parse_utc(SV20_TARGET_START_AT)
    return earliest_dt <= target_dt + timedelta(seconds=SV20_TIMEFRAME_SECONDS[canonical_sv20_timeframe(timeframe)])


def build_sv20_canonical_evidence_status(
    evidence_pack_paths: list[str] | None,
    *,
    readiness_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    paths = evidence_pack_paths or []
    has_db_ready_rows = any(bool(row.get("db_imported")) and bool(row.get("canonical_evidence_ready")) for row in readiness_rows)
    if paths and has_db_ready_rows:
        return {
            "status": "canonical",
            "evidence_pack_paths": paths,
            "compact_replay_rows_are_canonical_evidence": False,
            "reason_codes": ["canonical_sv2_evidence_packs_generated"],
        }
    return {
        "status": "blocked",
        "evidence_pack_paths": paths,
        "compact_replay_rows_are_canonical_evidence": False,
        "reason_codes": [
            "canonical_sv2_evidence_packs_missing",
            "compact_replay_rows_not_canonical_evidence",
            "db_imported_false_for_staged_summary",
        ],
    }


def build_sv20_readiness_rows(
    identities: list[SV20MarketIdentity],
    datasets: list[SV20CandleDataset],
) -> list[dict[str, Any]]:
    dataset_by_key = {(row.requested_symbol, canonical_sv20_timeframe(row.timeframe)): row for row in datasets}
    rows: list[dict[str, Any]] = []
    for identity in identities:
        for timeframe in SV20_TIMEFRAMES:
            dataset = dataset_by_key.get((identity.requested_symbol, timeframe))
            candles = list(dataset.candles) if dataset else []
            earliest = candles[0]["close_time"] if candles else None
            latest = candles[-1]["close_time"] if candles else None
            target_start_met = target_start_is_covered(earliest, timeframe)
            expected = expected_count_from_target(latest=latest, timeframe=timeframe)
            reasons = list(identity.reason_codes)
            if not identity.supported:
                reasons.append("historical_data_source_missing")
            if candles:
                reasons.append("historical_candles_available")
                if target_start_met:
                    reasons.append("historical_target_start_available")
                else:
                    reasons.extend(
                        [
                            "historical_target_start_not_available",
                            "historical_earliest_available_after_target",
                        ]
                    )
                if len(candles) >= SV20_PUBLIC_CANDLE_LIMIT:
                    reasons.append("hyperliquid_public_5000_candle_limit")
            else:
                reasons.append("historical_candles_unavailable")
                if identity.supported:
                    reasons.append("historical_data_source_missing")
            if dataset:
                reasons.extend(dataset.fetch_reason_codes)
                reasons.extend(dataset.import_reason_codes)
                if dataset.staged_for_replay and not dataset.db_imported:
                    reasons.extend(
                        [
                            "historical_staged_for_replay_only",
                            "db_import_not_attempted",
                            "canonical_hardened_import_not_run",
                        ]
                    )
                if not dataset.canonical_evidence_ready:
                    reasons.append("canonical_sv2_evidence_packs_missing")
            elif identity.supported:
                reasons.extend(["historical_fetch_not_requested", "canonical_sv2_evidence_packs_missing"])
            candle_count = len(candles)
            db_imported = bool(dataset and dataset.db_imported)
            canonical_evidence_ready = bool(dataset and dataset.canonical_evidence_ready and db_imported)
            staged_for_replay = bool(dataset and dataset.staged_for_replay)
            rows.append(
                {
                    "requested_symbol": identity.requested_symbol,
                    "symbol": identity.requested_symbol,
                    "resolved_venue_symbol": identity.resolved_venue_symbol,
                    "timeframe": timeframe,
                    "display_timeframe": display_sv20_timeframe(timeframe),
                    "component": SV20_COMPONENT_BY_TIMEFRAME[timeframe],
                    "supported": identity.supported,
                    "source": "Hyperliquid public mainnet candleSnapshot",
                    "fetch_attempted": bool(dataset and dataset.fetch_attempted),
                    "data_available": candle_count > 0,
                    "fetched": bool(dataset and dataset.fetched),
                    "normalized": bool(dataset and dataset.normalized),
                    "raw_file_written": bool(dataset and dataset.raw_file_written),
                    "staged_for_replay": staged_for_replay,
                    "db_imported": db_imported,
                    "imported": db_imported,
                    "canonical_evidence_ready": canonical_evidence_ready,
                    "target_window_ready": bool(dataset and dataset.target_window_ready),
                    "earliest_candle": earliest,
                    "latest_candle": latest,
                    "target_start_at": SV20_TARGET_START_AT,
                    "target_start_met": target_start_met,
                    "candle_count": candle_count,
                    "expected_candle_count": expected,
                    "coverage_percent": coverage_percent(candle_count, expected),
                    "reason_codes": sorted(set(reasons)),
                    "replay_ready": identity.supported and staged_for_replay and candle_count > 0,
                    "compact_replay_ready": identity.supported and staged_for_replay and candle_count > 0,
                    "evidence_ready": canonical_evidence_ready,
                }
            )
    return rows


def sv20_market_identity_to_dict(identity: SV20MarketIdentity) -> dict[str, Any]:
    return asdict(identity)


def build_sv20_summary(
    *,
    identities: list[SV20MarketIdentity],
    readiness_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]] | None = None,
    evidence_pack_paths: list[str] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    evidence_pack_paths = evidence_pack_paths or []
    evidence_rows = evidence_rows or []
    supported = [row.requested_symbol for row in identities if row.supported]
    excluded = [
        {
            "requested_symbol": row.requested_symbol,
            "reason_codes": list(row.reason_codes),
        }
        for row in identities
        if not row.supported
    ]
    if not evidence_rows:
        for row in readiness_rows:
            evidence_rows.append(
                {
                    "symbol": row["requested_symbol"],
                    "timeframe": row["timeframe"],
                    "display_timeframe": row.get("display_timeframe", display_sv20_timeframe(row["timeframe"])),
                    "component": row["component"],
                    "status": "evidence_ready" if row["evidence_ready"] else "blocked",
                    "ending_equity": None,
                    "net_pnl": None,
                    "trade_count": None,
                    "win_rate": None,
                    "max_drawdown": None,
                    "reason_codes": row["reason_codes"],
                }
            )
    canonical_evidence_status = build_sv20_canonical_evidence_status(
        evidence_pack_paths,
        readiness_rows=readiness_rows,
    )
    return {
        "report": SV20_REPORT_NAME,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "money_flow_version": SV20_MONEY_FLOW_VERSION,
        "requested_universe": list(SV20_REQUESTED_SYMBOLS),
        "supported_universe": supported,
        "excluded_symbols": excluded,
        "symbols": list(SV20_REQUESTED_SYMBOLS),
        "timeframes": list(SV20_TIMEFRAMES),
        "display_timeframes": [display_sv20_timeframe(timeframe) for timeframe in SV20_TIMEFRAMES],
        "timeframe_display_labels": SV20_TIMEFRAME_DISPLAY_LABELS,
        "components": [SV20_COMPONENT_BY_TIMEFRAME[timeframe] for timeframe in SV20_TIMEFRAMES],
        "target_start_at": SV20_TARGET_START_AT,
        "source": {
            "historical_strategy_truth": "Hyperliquid public mainnet candleSnapshot",
            "endpoint": HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
            "endpoint_category": "public_read_only_mainnet",
            "testnet_prices_used_as_strategy_truth": False,
            "private_or_signed_endpoints_used": False,
            "order_endpoints_used": False,
            "api_keys_used": False,
        },
        "sleeve_settings": SV20_SLEEVE_SETTINGS,
        "market_identities": [sv20_market_identity_to_dict(row) for row in identities],
        "data_readiness": readiness_rows,
        "datasets": readiness_rows,
        "evidence_rows": evidence_rows,
        "comparison": evidence_rows,
        "evidence_pack_paths": evidence_pack_paths,
        "canonical_evidence_status": canonical_evidence_status,
        "boundary_flags": {
            "adds_real_1d_money_flow_sleeve": True,
            "preserves_15m_1h_4h_rules": True,
            "uses_hyperliquid_public_mainnet_candles": True,
            "uses_testnet_prices_as_strategy_truth": False,
            "submits_orders": False,
            "calls_order_endpoints": False,
            "calls_private_or_signed_endpoints": False,
            "uses_api_keys": False,
            "optimizes_parameters": False,
            "compact_replay_rows_are_canonical_evidence": False,
        },
    }


def run_sv20_baseline_evidence_rows(datasets: list[SV20CandleDataset]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        timeframe = canonical_sv20_timeframe(dataset.timeframe)
        component = SV20_COMPONENT_BY_TIMEFRAME[timeframe]
        if not dataset.candles:
            rows.append(
                {
                    "symbol": dataset.requested_symbol,
                    "timeframe": timeframe,
                    "display_timeframe": display_sv20_timeframe(timeframe),
                    "component": component,
                    "status": "blocked",
                    "ending_equity": None,
                    "net_pnl": None,
                    "trade_count": 0,
                    "win_rate": None,
                    "max_drawdown": None,
                    "open_position_at_end": False,
                    "forced_close_applied": False,
                    "mark_to_market_applied": False,
                    "final_mtm_price": None,
                    "forced_close_price": None,
                    "forced_close_time": None,
                    "open_position_unrealized_pnl": None,
                    "excluded_from_final_metrics": False,
                    "evidence_classification": "compact_provisional_replay_not_canonical_evidence",
                    "reason_codes": list(dataset.fetch_reason_codes + dataset.import_reason_codes),
                }
            )
            continue
        rows.append(_run_single_dataset_evidence(dataset, component))
    return rows


def _run_single_dataset_evidence(dataset: SV20CandleDataset, component: str) -> dict[str, Any]:
    closes = [_decimal(row["close"]) for row in dataset.candles]
    opens = [_decimal(row["open"]) for row in dataset.candles]
    indicators = _indicator_rows(closes)
    params = SV20_SLEEVE_SETTINGS[component]
    min_history = int(params["history"])
    rsi_floor, rsi_ceiling = [Decimal(value) for value in str(params["rsi_band"]).split("-")]
    overbought = Decimal(str(params["overbought"]))
    trim = Decimal(str(params["trim"]))
    max_extension = Decimal(str(params["max_ema5_extension_pct"]).rstrip("%")) / Decimal("100")
    equity = Decimal("10000")
    peak_equity = equity
    max_drawdown = Decimal("0")
    trade_count = 0
    wins = 0
    open_position: dict[str, Any] | None = None
    open_position_at_end = False
    forced_close_applied = False
    mark_to_market_applied = False
    final_mtm_price: Decimal | None = None
    forced_close_price: Decimal | None = None
    forced_close_time: str | None = None
    open_position_unrealized_pnl: Decimal | None = None
    fee_bps = Decimal("5")
    slippage_bps = Decimal("3")
    for index in range(min_history, len(dataset.candles) - 1):
        row = indicators[index]
        if not _indicators_ready(row):
            continue
        close = closes[index]
        next_open = opens[index + 1]
        ema5 = row["ema5"]
        ema10 = row["ema10"]
        sma20 = row["sma20"]
        rsi = row["rsi"]
        macd = row["macd"]
        macd_signal = row["macd_signal"]
        macd_hist = row["macd_hist"]
        assert None not in (ema5, ema10, sma20, rsi, macd, macd_signal, macd_hist)
        if open_position is not None:
            mtm_equity = equity + ((close - open_position["entry_price"]) * open_position["quantity"])
            peak_equity = max(peak_equity, mtm_equity)
            max_drawdown = max(max_drawdown, peak_equity - mtm_equity)
            mark_to_market_applied = True
            exit_reason = None
            if ema5 <= ema10 or ema10 <= sma20 or close < ema10:
                exit_reason = "ma_alignment_break"
            elif close < sma20 or ema5 <= ema10:
                exit_reason = "trend_invalidated"
            elif macd < macd_signal or macd_hist < 0:
                exit_reason = "macd_rollover"
            elif rsi >= trim:
                exit_reason = "rsi_trim_reduction"
            if exit_reason:
                exit_price = next_open * (Decimal("1") - slippage_bps / Decimal("10000"))
                notional = open_position["quantity"] * exit_price
                exit_fee = notional * fee_bps / Decimal("10000")
                gross = (exit_price - open_position["entry_price"]) * open_position["quantity"]
                net = gross - exit_fee
                equity += net
                peak_equity = max(peak_equity, equity)
                max_drawdown = max(max_drawdown, peak_equity - equity)
                trade_count += 1
                if net > 0:
                    wins += 1
                open_position = None
            continue
        bullish = ema5 > ema10 > sma20
        rsi_ok = rsi_floor <= rsi <= rsi_ceiling
        macd_ok = macd > macd_signal and macd_hist >= 0
        pullback_ok = close >= ema10 and close <= ema5 * (Decimal("1") + max_extension)
        continuation_ok = close > ema5 and close <= ema5 * (Decimal("1") + max_extension)
        extension = (close / ema5) - Decimal("1") if ema5 else Decimal("0")
        if bullish and rsi_ok and rsi < overbought and macd_ok and (pullback_ok or continuation_ok) and extension <= max_extension:
            entry_price = next_open * (Decimal("1") + slippage_bps / Decimal("10000"))
            notional = equity
            quantity = notional / entry_price
            entry_fee = notional * fee_bps / Decimal("10000")
            equity -= entry_fee
            peak_equity = max(peak_equity, equity)
            max_drawdown = max(max_drawdown, peak_equity - equity)
            open_position = {
                "entry_price": entry_price,
                "quantity": quantity,
                "entry_fee": entry_fee,
                "entry_time": dataset.candles[index + 1]["close_time"],
            }
    if open_position is not None:
        open_position_at_end = True
        forced_close_applied = True
        mark_to_market_applied = True
        final_mtm_price = closes[-1]
        forced_close_price = final_mtm_price * (Decimal("1") - slippage_bps / Decimal("10000"))
        forced_close_time = str(dataset.candles[-1]["close_time"])
        open_position_unrealized_pnl = (final_mtm_price - open_position["entry_price"]) * open_position["quantity"]
        mtm_equity = equity + open_position_unrealized_pnl
        peak_equity = max(peak_equity, mtm_equity)
        max_drawdown = max(max_drawdown, peak_equity - mtm_equity)
        exit_notional = open_position["quantity"] * forced_close_price
        exit_fee = exit_notional * fee_bps / Decimal("10000")
        gross = (forced_close_price - open_position["entry_price"]) * open_position["quantity"]
        net = gross - exit_fee
        equity += net
        peak_equity = max(peak_equity, equity)
        max_drawdown = max(max_drawdown, peak_equity - equity)
        trade_count += 1
        if net > 0:
            wins += 1
    net_pnl = equity - Decimal("10000")
    reason_codes = [
        "dynamic_equity_pct",
        "next_candle_open",
        "fee_5bps",
        "slippage_3bps",
        "entry_fee_counted_at_open",
        "compact_replay_rows_not_canonical_evidence",
    ]
    if forced_close_applied:
        reason_codes.append("force_close_at_dataset_end")
    return {
        "symbol": dataset.requested_symbol,
        "timeframe": canonical_sv20_timeframe(dataset.timeframe),
        "display_timeframe": display_sv20_timeframe(dataset.timeframe),
        "component": component,
        "status": "evidence_rebuilt" if trade_count else "evidence_rebuilt_no_trades",
        "ending_equity": str(equity.quantize(Decimal("0.00000001"))),
        "net_pnl": str(net_pnl.quantize(Decimal("0.00000001"))),
        "trade_count": trade_count,
        "win_rate": str((Decimal(wins) / Decimal(trade_count)).quantize(Decimal("0.00000001"))) if trade_count else None,
        "max_drawdown": str(max_drawdown.quantize(Decimal("0.00000001"))),
        "open_position_at_end": open_position_at_end,
        "forced_close_applied": forced_close_applied,
        "mark_to_market_applied": mark_to_market_applied,
        "final_mtm_price": str(final_mtm_price) if final_mtm_price is not None else None,
        "forced_close_price": str(forced_close_price) if forced_close_price is not None else None,
        "forced_close_time": forced_close_time,
        "open_position_unrealized_pnl": (
            str(open_position_unrealized_pnl.quantize(Decimal("0.00000001")))
            if open_position_unrealized_pnl is not None
            else None
        ),
        "excluded_from_final_metrics": False,
        "evidence_classification": "compact_provisional_replay_not_canonical_evidence",
        "reason_codes": reason_codes,
    }


def _indicator_rows(closes: list[Decimal]) -> list[dict[str, Decimal | None]]:
    ema5 = _ema(closes, 5)
    ema10 = _ema(closes, 10)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = [a - b if a is not None and b is not None else None for a, b in zip(ema12, ema26, strict=False)]
    macd_signal = _ema_optional(macd, 9)
    rsi = _rsi(closes, 14)
    sma20 = _sma(closes, 20)
    rows = []
    for index in range(len(closes)):
        hist = (
            macd[index] - macd_signal[index]
            if macd[index] is not None and macd_signal[index] is not None
            else None
        )
        rows.append(
            {
                "ema5": ema5[index],
                "ema10": ema10[index],
                "sma20": sma20[index],
                "rsi": rsi[index],
                "macd": macd[index],
                "macd_signal": macd_signal[index],
                "macd_hist": hist,
            }
        )
    return rows


def _indicators_ready(row: dict[str, Decimal | None]) -> bool:
    return all(row.get(key) is not None for key in ("ema5", "ema10", "sma20", "rsi", "macd", "macd_signal", "macd_hist"))


def _sma(values: list[Decimal], period: int) -> list[Decimal | None]:
    rows: list[Decimal | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            rows.append(None)
        else:
            rows.append(sum(values[index + 1 - period : index + 1]) / Decimal(period))
    return rows


def _ema(values: list[Decimal], period: int) -> list[Decimal | None]:
    rows: list[Decimal | None] = []
    multiplier = Decimal("2") / Decimal(period + 1)
    current: Decimal | None = None
    for index, value in enumerate(values):
        if index + 1 < period:
            rows.append(None)
            continue
        if current is None:
            current = sum(values[index + 1 - period : index + 1]) / Decimal(period)
        else:
            current = ((value - current) * multiplier) + current
        rows.append(current)
    return rows


def _ema_optional(values: list[Decimal | None], period: int) -> list[Decimal | None]:
    rows: list[Decimal | None] = []
    multiplier = Decimal("2") / Decimal(period + 1)
    current: Decimal | None = None
    ready_values: list[Decimal] = []
    for value in values:
        if value is None:
            rows.append(None)
            continue
        ready_values.append(value)
        if len(ready_values) < period:
            rows.append(None)
            continue
        if current is None:
            current = sum(ready_values[-period:]) / Decimal(period)
        else:
            current = ((value - current) * multiplier) + current
        rows.append(current)
    return rows


def _rsi(values: list[Decimal], period: int) -> list[Decimal | None]:
    rows: list[Decimal | None] = [None]
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    avg_gain: Decimal | None = None
    avg_loss: Decimal | None = None
    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]
        gain = max(delta, Decimal("0"))
        loss = max(-delta, Decimal("0"))
        gains.append(gain)
        losses.append(loss)
        if index < period:
            rows.append(None)
            continue
        if index == period:
            avg_gain = sum(gains[-period:]) / Decimal(period)
            avg_loss = sum(losses[-period:]) / Decimal(period)
        else:
            assert avg_gain is not None and avg_loss is not None
            avg_gain = ((avg_gain * Decimal(period - 1)) + gain) / Decimal(period)
            avg_loss = ((avg_loss * Decimal(period - 1)) + loss) / Decimal(period)
        if avg_loss == 0:
            rows.append(Decimal("100"))
        else:
            rs = avg_gain / avg_loss
            rows.append(Decimal("100") - (Decimal("100") / (Decimal("1") + rs)))
    return rows
