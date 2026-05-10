"""UAT1 public-read-only connectivity helpers.

The helpers in this module only support explicitly enabled public read-only
network calls. They do not use API keys, private endpoints, signed endpoints,
order endpoints, strategy evaluation, or trading artifacts.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import json
from typing import Any

import httpx

from core.security import redact_sensitive_text
from services.exchange.safety import (
    HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST,
    ExchangeEndpointCategory,
    classify_hyperliquid_info_payload,
)
from services.uat.universe import (
    Top20UniverseResolver,
    TopVolumeSourceAsset,
    UATObservationCandidate,
    UATUniverseExclusionReason,
    VenueMarketIdentity,
)


HYPERLIQUID_PUBLIC_INFO_URL = "https://api.hyperliquid.xyz/info"
COINGECKO_TOP_VOLUME_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=volume_desc&per_page=20&page=1&sparkline=false"
)


@dataclass(frozen=True)
class UAT1PublicReadOnlyMode:
    runtime_mode: str = "uat"
    uat1_public_read_only: bool = False
    allow_public_read_only_network: bool = False
    private_endpoints_allowed: bool = False
    signed_endpoints_allowed: bool = False
    order_endpoints_allowed: bool = False
    api_keys_used: bool = False


@dataclass(frozen=True)
class UAT1EndpointAccessDecision:
    allowed: bool
    category: ExchangeEndpointCategory
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PublicHTTPResult:
    url: str
    method: str
    status_code: int | None
    payload: Any | None
    response_headers: dict[str, str]
    success: bool
    sanitized_error: str | None = None


@dataclass(frozen=True)
class HyperliquidInfoTypeResult:
    info_type: str
    attempted: bool
    category: ExchangeEndpointCategory
    endpoint_url: str
    success: bool
    http_status: int | None
    response_shape_usable: bool
    sanitized_error: str | None
    private_or_signed_or_key_required: bool
    needs_followup: bool


@dataclass(frozen=True)
class Top20SourceResult:
    provider: str
    url: str
    attempted: bool
    success: bool
    source_timestamp_utc: datetime | None
    source_freshness_seconds: int | None
    assets: tuple[TopVolumeSourceAsset, ...]
    sanitized_error: str | None = None
    used_api_key: bool = False


@dataclass(frozen=True)
class UAT1AssetMarketDataSample:
    global_symbol: str
    venue_symbol: str | None
    market_metadata_available: bool
    mid_available: bool
    candle_sample_available: bool
    order_book_sample_available: bool
    funding_context_available: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class UAT1ConnectivityResult:
    mode: UAT1PublicReadOnlyMode
    hyperliquid_info_type_results: tuple[HyperliquidInfoTypeResult, ...]
    top20_source_result: Top20SourceResult
    included_candidates: tuple[UATObservationCandidate, ...]
    excluded_candidates: tuple[UATObservationCandidate, ...]
    market_data_samples: tuple[UAT1AssetMarketDataSample, ...]
    uat2_readiness_decision: str
    remaining_blockers: tuple[str, ...]


Transport = Callable[[str, str, dict[str, Any] | None], PublicHTTPResult]


def evaluate_uat1_endpoint_access(
    *,
    category: ExchangeEndpointCategory,
    mode: UAT1PublicReadOnlyMode,
) -> UAT1EndpointAccessDecision:
    reason_codes: list[str] = []
    if category != ExchangeEndpointCategory.PUBLIC_READ_ONLY:
        reason_codes.append("uat1_only_public_read_only_endpoints_allowed")
    if category == ExchangeEndpointCategory.UNKNOWN:
        reason_codes.append("exchange_endpoint_category_unknown")
    if category == ExchangeEndpointCategory.PUBLIC_READ_ONLY and not mode.uat1_public_read_only:
        reason_codes.append("uat1_public_read_only_mode_not_enabled")
    if category == ExchangeEndpointCategory.PUBLIC_READ_ONLY and not mode.allow_public_read_only_network:
        reason_codes.append("public_read_only_network_not_explicitly_allowed")
    if mode.api_keys_used:
        reason_codes.append("api_keys_forbidden_in_uat1")
    if mode.private_endpoints_allowed:
        reason_codes.append("private_endpoints_forbidden_in_uat1")
    if mode.signed_endpoints_allowed:
        reason_codes.append("signed_endpoints_forbidden_in_uat1")
    if mode.order_endpoints_allowed:
        reason_codes.append("order_endpoints_forbidden_in_uat1")
    return UAT1EndpointAccessDecision(
        allowed=not reason_codes,
        category=category,
        reason_codes=tuple(reason_codes),
    )


def _default_transport(method: str, url: str, payload: dict[str, Any] | None) -> PublicHTTPResult:
    headers = {"User-Agent": "money-flow-uat1-public-read-only/1.0"}
    try:
        with httpx.Client(timeout=20.0, headers=headers) as client:
            if method == "GET":
                response = client.get(url)
            else:
                response = client.post(url, json=payload or {})
            status_code = response.status_code
            response.raise_for_status()
            return PublicHTTPResult(
                url=url,
                method=method,
                status_code=status_code,
                payload=response.json(),
                response_headers={str(k): str(v) for k, v in response.headers.items()},
                success=True,
            )
    except Exception as exc:  # noqa: BLE001
        status_code = None
        response = getattr(exc, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=status_code,
            payload=None,
            response_headers={},
            success=False,
            sanitized_error=redact_sensitive_text(str(exc)),
        )


def hyperliquid_info_payload(
    info_type: str,
    *,
    coin: str = "ETH",
    now: datetime | None = None,
) -> dict[str, Any]:
    observed_at = now or datetime.now(UTC)
    end_ms = int(observed_at.timestamp() * 1000)
    if info_type in {"meta", "metaAndAssetCtxs", "allMids"}:
        return {"type": info_type}
    if info_type == "l2Book":
        return {"type": "l2Book", "coin": coin}
    if info_type == "candleSnapshot":
        return {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": "1h",
                "startTime": end_ms - int(timedelta(hours=3).total_seconds() * 1000),
                "endTime": end_ms,
            },
        }
    if info_type == "fundingHistory":
        return {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": end_ms - int(timedelta(days=1).total_seconds() * 1000),
            "endTime": end_ms,
        }
    return {"type": info_type}


def response_shape_usable(info_type: str, payload: Any) -> bool:
    if info_type == "meta":
        return isinstance(payload, dict) and isinstance(payload.get("universe"), list)
    if info_type == "metaAndAssetCtxs":
        return (
            isinstance(payload, list)
            and len(payload) >= 2
            and isinstance(payload[0], dict)
            and isinstance(payload[0].get("universe"), list)
        )
    if info_type == "allMids":
        return isinstance(payload, dict) and bool(payload)
    if info_type == "l2Book":
        return isinstance(payload, dict) and "levels" in payload
    if info_type == "candleSnapshot":
        return isinstance(payload, list)
    if info_type == "fundingHistory":
        return isinstance(payload, list)
    return False


def verify_hyperliquid_info_type(
    *,
    info_type: str,
    mode: UAT1PublicReadOnlyMode,
    transport: Transport | None = None,
    coin: str = "ETH",
    now: datetime | None = None,
) -> tuple[HyperliquidInfoTypeResult, Any | None]:
    payload = hyperliquid_info_payload(info_type, coin=coin, now=now)
    category = classify_hyperliquid_info_payload(payload)
    access = evaluate_uat1_endpoint_access(category=category, mode=mode)
    if info_type not in HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST.allowed_public_info_types:
        access = UAT1EndpointAccessDecision(
            allowed=False,
            category=category,
            reason_codes=access.reason_codes + ("info_type_not_in_uat1_allowlist",),
        )
    if not access.allowed:
        return (
            HyperliquidInfoTypeResult(
                info_type=info_type,
                attempted=False,
                category=category,
                endpoint_url=HYPERLIQUID_PUBLIC_INFO_URL,
                success=False,
                http_status=None,
                response_shape_usable=False,
                sanitized_error=",".join(access.reason_codes),
                private_or_signed_or_key_required=False,
                needs_followup=True,
            ),
            None,
        )
    http = (transport or _default_transport)("POST", HYPERLIQUID_PUBLIC_INFO_URL, payload)
    usable = bool(http.success and response_shape_usable(info_type, http.payload))
    return (
        HyperliquidInfoTypeResult(
            info_type=info_type,
            attempted=True,
            category=category,
            endpoint_url=HYPERLIQUID_PUBLIC_INFO_URL,
            success=http.success,
            http_status=http.status_code,
            response_shape_usable=usable,
            sanitized_error=http.sanitized_error,
            private_or_signed_or_key_required=False,
            needs_followup=not usable,
        ),
        http.payload if http.success else None,
    )


def _decimal_or_none(value: Any) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def parse_coingecko_top_volume_assets(
    payload: Any,
    *,
    source_url: str,
    source_timestamp_utc: datetime,
) -> tuple[TopVolumeSourceAsset, ...]:
    if not isinstance(payload, list):
        return ()
    assets: list[TopVolumeSourceAsset] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        assets.append(
            TopVolumeSourceAsset(
                global_symbol=symbol,
                source_rank=index,
                volume_24h_usd=_decimal_or_none(item.get("total_volume")),
                source_provider="coingecko_public_markets",
                source_url=source_url,
                source_timestamp_utc=source_timestamp_utc,
                source_asset_id=str(item.get("id") or symbol.lower()),
            )
        )
    return tuple(sorted(assets, key=lambda asset: (asset.source_rank, asset.global_symbol))[:20])


def _source_timestamp_from_headers(headers: dict[str, str], fallback: datetime) -> datetime:
    raw_date = headers.get("date") or headers.get("Date")
    if raw_date:
        try:
            return parsedate_to_datetime(raw_date).astimezone(UTC)
        except (TypeError, ValueError, AttributeError):
            return fallback
    return fallback


def fetch_top20_source(
    *,
    mode: UAT1PublicReadOnlyMode,
    transport: Transport | None = None,
    now: datetime | None = None,
    url: str = COINGECKO_TOP_VOLUME_URL,
) -> Top20SourceResult:
    observed_at = now or datetime.now(UTC)
    access = evaluate_uat1_endpoint_access(
        category=ExchangeEndpointCategory.PUBLIC_READ_ONLY,
        mode=mode,
    )
    if not access.allowed:
        return Top20SourceResult(
            provider="coingecko_public_markets",
            url=url,
            attempted=False,
            success=False,
            source_timestamp_utc=None,
            source_freshness_seconds=None,
            assets=(),
            sanitized_error=",".join(access.reason_codes),
        )
    http = (transport or _default_transport)("GET", url, None)
    if not http.success:
        return Top20SourceResult(
            provider="coingecko_public_markets",
            url=url,
            attempted=True,
            success=False,
            source_timestamp_utc=None,
            source_freshness_seconds=None,
            assets=(),
            sanitized_error=http.sanitized_error,
        )
    source_timestamp = _source_timestamp_from_headers(http.response_headers, observed_at)
    assets = parse_coingecko_top_volume_assets(
        http.payload,
        source_url=url,
        source_timestamp_utc=source_timestamp,
    )
    freshness = max(0, int((observed_at - source_timestamp).total_seconds()))
    return Top20SourceResult(
        provider="coingecko_public_markets",
        url=url,
        attempted=True,
        success=bool(assets),
        source_timestamp_utc=source_timestamp,
        source_freshness_seconds=freshness,
        assets=assets,
        sanitized_error=None if assets else "top20_source_payload_unusable",
    )


def hyperliquid_markets_from_meta(payload: Any) -> tuple[VenueMarketIdentity, ...]:
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        payload = payload[0]
    universe = payload.get("universe") if isinstance(payload, dict) else None
    if not isinstance(universe, list):
        return ()
    markets: list[VenueMarketIdentity] = []
    for index, asset in enumerate(universe):
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "").strip().upper()
        if not name:
            continue
        is_delisted = bool(asset.get("isDelisted") or asset.get("delisted"))
        markets.append(
            VenueMarketIdentity(
                global_symbol=name,
                venue="hyperliquid",
                venue_symbol=name,
                market_type="perpetual",
                product_type="perp",
                quote_asset="USDC",
                settlement_asset="USDC",
                venue_asset_id=str(asset.get("assetId") if asset.get("assetId") is not None else index),
                public_market_data_supported=not is_delisted,
                enabled_for_uat=not is_delisted,
            )
        )
    return tuple(markets)


def sample_market_data_for_candidates(
    *,
    included_candidates: tuple[UATObservationCandidate, ...],
    endpoint_payloads: dict[str, Any],
    mode: UAT1PublicReadOnlyMode,
    transport: Transport | None,
    now: datetime,
) -> tuple[UAT1AssetMarketDataSample, ...]:
    all_mids = endpoint_payloads.get("allMids")
    samples: list[UAT1AssetMarketDataSample] = []
    for candidate in included_candidates:
        venue_symbol = candidate.venue_symbol
        mid_available = (
            isinstance(all_mids, dict)
            and venue_symbol is not None
            and (venue_symbol in all_mids or f"{venue_symbol}-PERP" in all_mids)
        )
        errors: list[str] = []
        if not mid_available:
            errors.append("mid_unavailable")
        candle_result, _ = verify_hyperliquid_info_type(
            info_type="candleSnapshot",
            mode=mode,
            transport=transport,
            coin=venue_symbol or candidate.global_symbol,
            now=now,
        )
        l2_result, _ = verify_hyperliquid_info_type(
            info_type="l2Book",
            mode=mode,
            transport=transport,
            coin=venue_symbol or candidate.global_symbol,
            now=now,
        )
        funding_result, _ = verify_hyperliquid_info_type(
            info_type="fundingHistory",
            mode=mode,
            transport=transport,
            coin=venue_symbol or candidate.global_symbol,
            now=now,
        )
        if not candle_result.response_shape_usable:
            errors.append("candle_sample_unavailable")
        if not l2_result.response_shape_usable:
            errors.append("order_book_sample_unavailable")
        if not funding_result.response_shape_usable:
            errors.append("funding_context_unavailable")
        samples.append(
            UAT1AssetMarketDataSample(
                global_symbol=candidate.global_symbol,
                venue_symbol=venue_symbol,
                market_metadata_available=True,
                mid_available=mid_available,
                candle_sample_available=candle_result.response_shape_usable,
                order_book_sample_available=l2_result.response_shape_usable,
                funding_context_available=funding_result.response_shape_usable,
                errors=tuple(errors),
            )
        )
    return tuple(samples)


def run_uat1_public_read_only_check(
    *,
    mode: UAT1PublicReadOnlyMode,
    transport: Transport | None = None,
    now: datetime | None = None,
) -> UAT1ConnectivityResult:
    observed_at = now or datetime.now(UTC)
    info_results: list[HyperliquidInfoTypeResult] = []
    endpoint_payloads: dict[str, Any] = {}
    for info_type in HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST.allowed_public_info_types:
        result, payload = verify_hyperliquid_info_type(
            info_type=info_type,
            mode=mode,
            transport=transport,
            now=observed_at,
        )
        info_results.append(result)
        if payload is not None:
            endpoint_payloads[info_type] = payload

    top20 = fetch_top20_source(mode=mode, transport=transport, now=observed_at)
    meta_payload = endpoint_payloads.get("meta") or endpoint_payloads.get("metaAndAssetCtxs")
    venue_markets = hyperliquid_markets_from_meta(meta_payload)
    if top20.success and venue_markets:
        resolution = Top20UniverseResolver().resolve(
            source_assets=top20.assets,
            venue_markets=venue_markets,
            as_of_utc=observed_at,
        )
        included = resolution.included
        excluded = resolution.excluded
    else:
        included = ()
        excluded = tuple(
            UATObservationCandidate(
                global_symbol=asset.global_symbol,
                source_rank=asset.source_rank,
                source_24h_volume_usd=asset.volume_24h_usd,
                source_provider=asset.source_provider,
                source_url=asset.source_url,
                source_timestamp_utc=asset.source_timestamp_utc,
                venue="hyperliquid",
                venue_symbol=None,
                market_type=None,
                product_type=None,
                quote_asset=None,
                settlement_asset=None,
                venue_asset_id=None,
                included=False,
                exclusion_reason_codes=(UATUniverseExclusionReason.PUBLIC_READ_ONLY_FETCH_FAILED,),
            )
            for asset in top20.assets
        )

    samples = sample_market_data_for_candidates(
        included_candidates=included,
        endpoint_payloads=endpoint_payloads,
        mode=mode,
        transport=transport,
        now=observed_at,
    )
    endpoint_success = all(result.success and result.response_shape_usable for result in info_results)
    samples_available = all(
        sample.market_metadata_available and sample.mid_available and sample.candle_sample_available
        for sample in samples
    )
    remaining_blockers: list[str] = []
    if not endpoint_success:
        remaining_blockers.append("hyperliquid_public_read_only_endpoint_followup")
    if not top20.success:
        remaining_blockers.append("top20_public_source_fetch_followup")
    if not included:
        remaining_blockers.append("top20_hyperliquid_supported_universe_empty")
    if not samples_available:
        remaining_blockers.append("included_asset_public_market_data_sample_followup")
    remaining_blockers.extend(
        [
            "uat2_operator_visible_shadow_drawdown_state",
            "uat2_shadow_signal_audit_surface",
            "broader_structured_log_api_error_redaction_before_uat2_or_uat3",
        ]
    )
    uat2_decision = "UAT2 is blocked"
    return UAT1ConnectivityResult(
        mode=mode,
        hyperliquid_info_type_results=tuple(info_results),
        top20_source_result=top20,
        included_candidates=included,
        excluded_candidates=excluded,
        market_data_samples=samples,
        uat2_readiness_decision=uat2_decision,
        remaining_blockers=tuple(dict.fromkeys(remaining_blockers)),
    )


def _money(value: Decimal | None) -> str:
    if value is None:
        return "missing"
    return f"{value:.2f}"


def render_uat1_report(result: UAT1ConnectivityResult) -> str:
    lines: list[str] = [
        "# UAT1 Public Read-Only Connectivity And Top-20 Universe",
        "",
        f"Recorded at: `{datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}`",
        "",
        "## Scope",
        "",
        "UAT1 is public read-only connectivity and universe resolution only. It does not run Money Flow, submit orders, use API keys, call private endpoints, call signed endpoints, call order endpoints, add paper trading, add live trading, add routing behavior, change Money Flow rules, or generate evidence packs.",
        "",
        "Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.",
        "",
        "## Runtime Mode And Network Gate",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Runtime mode | `{result.mode.runtime_mode}` |",
        f"| UAT1 public read-only mode | `{str(result.mode.uat1_public_read_only).lower()}` |",
        f"| Public read-only network allowed | `{str(result.mode.allow_public_read_only_network).lower()}` |",
        f"| Private endpoints allowed | `{str(result.mode.private_endpoints_allowed).lower()}` |",
        f"| Signed endpoints allowed | `{str(result.mode.signed_endpoints_allowed).lower()}` |",
        f"| Order endpoints allowed | `{str(result.mode.order_endpoints_allowed).lower()}` |",
        f"| API keys used | `{str(result.mode.api_keys_used).lower()}` |",
        "",
        "## Hyperliquid Public Info Type Results",
        "",
        "| Info type | Attempted | Classification | Endpoint URL | Success | HTTP status | Shape usable | Needs follow-up | Sanitized error |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for item in result.hyperliquid_info_type_results:
        lines.append(
            "| "
            f"`{item.info_type}` | `{str(item.attempted).lower()}` | `{item.category.value}` | "
            f"`{item.endpoint_url}` | `{str(item.success).lower()}` | "
            f"{item.http_status if item.http_status is not None else 'n/a'} | "
            f"`{str(item.response_shape_usable).lower()}` | `{str(item.needs_followup).lower()}` | "
            f"{item.sanitized_error or ''} |"
        )
    source = result.top20_source_result
    lines.extend(
        [
            "",
            "## Top-20 Source",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Provider | `{source.provider}` |",
            f"| URL | `{source.url}` |",
            f"| Attempted | `{str(source.attempted).lower()}` |",
            f"| Success | `{str(source.success).lower()}` |",
            f"| Source timestamp | `{source.source_timestamp_utc.isoformat() if source.source_timestamp_utc else 'n/a'}` |",
            f"| Source freshness seconds | `{source.source_freshness_seconds if source.source_freshness_seconds is not None else 'n/a'}` |",
            f"| Ranking field | `source_order_from_volume_desc_response` |",
            f"| Volume metric | `24h_volume_usd` |",
            f"| API key used | `{str(source.used_api_key).lower()}` |",
            f"| Sanitized error | {source.sanitized_error or ''} |",
            "",
            "## Top-20 Raw List Summary",
            "",
            "| Rank | Symbol | 24h volume USD | Source asset id |",
            "| ---: | --- | ---: | --- |",
        ]
    )
    for asset in source.assets:
        lines.append(
            f"| {asset.source_rank} | `{asset.global_symbol}` | {_money(asset.volume_24h_usd)} | `{asset.source_asset_id}` |"
        )
    lines.extend(
        [
            "",
            "## Hyperliquid Intersection Summary",
            "",
            f"Included assets: `{len(result.included_candidates)}`.",
            "",
            f"Excluded assets: `{len(result.excluded_candidates)}`.",
            "",
            "Top-20 inclusion means observation candidate only. It is not strategy approval, paper-trading approval, live-trading approval, or order-submission approval.",
            "",
            "## Included Assets",
            "",
            "| Symbol | Rank | 24h volume USD | Venue symbol | Market type | Product type | Quote | Settlement | Asset id | Observation only | Strategy approved | Paper approved | Live approved |",
            "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for candidate in result.included_candidates:
        lines.append(
            "| "
            f"`{candidate.global_symbol}` | {candidate.source_rank} | {_money(candidate.source_24h_volume_usd)} | "
            f"`{candidate.venue_symbol}` | `{candidate.market_type}` | `{candidate.product_type}` | "
            f"`{candidate.quote_asset}` | `{candidate.settlement_asset}` | `{candidate.venue_asset_id}` | "
            f"`{str(candidate.observation_only).lower()}` | `{str(candidate.strategy_approved).lower()}` | "
            f"`{str(candidate.paper_trading_approved).lower()}` | `{str(candidate.live_trading_approved).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Excluded Assets",
            "",
            "| Symbol | Rank | 24h volume USD | Reason codes |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for candidate in result.excluded_candidates:
        reasons = ", ".join(f"`{reason.value}`" for reason in candidate.exclusion_reason_codes)
        lines.append(
            f"| `{candidate.global_symbol}` | {candidate.source_rank} | {_money(candidate.source_24h_volume_usd)} | {reasons} |"
        )
    lines.extend(
        [
            "",
            "## Public Market-Data Sample Status",
            "",
            "| Symbol | Metadata | Mid/ticker | Candle sample | Order book sample | Funding context | Errors |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for sample in result.market_data_samples:
        lines.append(
            "| "
            f"`{sample.global_symbol}` | `{str(sample.market_metadata_available).lower()}` | "
            f"`{str(sample.mid_available).lower()}` | `{str(sample.candle_sample_available).lower()}` | "
            f"`{str(sample.order_book_sample_available).lower()}` | `{str(sample.funding_context_available).lower()}` | "
            f"{', '.join(f'`{err}`' for err in sample.errors)} |"
        )
    lines.extend(
        [
            "",
            "## No-Private / No-Order Confirmation",
            "",
            "- Private endpoints used: `false`.",
            "- Signed endpoints used: `false`.",
            "- Order endpoints used: `false`.",
            "- API keys used: `false`.",
            "- Orders submitted: `false`.",
            "- Strategy decisions created: `false`.",
            "- Order intents created: `false`.",
            "- Submitted orders created: `false`.",
            "",
            "## UAT2 Readiness Decision",
            "",
            f"`{result.uat2_readiness_decision}`.",
            "",
            "Remaining blockers:",
        ]
    )
    for blocker in result.remaining_blockers:
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "UAT2, when allowed, remains shadow-only and must compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.",
            "",
            "## Boundary Confirmation",
            "",
            "UAT1 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, order endpoint calls, evidence packs, strategy variants, or Money Flow rule changes.",
            "",
        ]
    )
    return "\n".join(lines)


def result_to_jsonable(result: UAT1ConnectivityResult) -> dict[str, Any]:
    return json.loads(
        json.dumps(
            asdict(result),
            default=lambda obj: obj.value
            if hasattr(obj, "value")
            else obj.isoformat()
            if isinstance(obj, datetime)
            else str(obj),
        )
    )
