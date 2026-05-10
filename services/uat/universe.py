"""UAT observation-universe policy and fixture-only resolver."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class UATUniverseExclusionReason(StrEnum):
    UNSUPPORTED_BY_VENUE = "unsupported_by_venue"
    UNSUPPORTED_MARKET_TYPE = "unsupported_market_type"
    MISSING_MARKET_IDENTITY = "missing_market_identity"
    QUOTE_ASSET_MISMATCH = "quote_asset_mismatch"
    SETTLEMENT_ASSET_MISMATCH = "settlement_asset_mismatch"
    INSUFFICIENT_PUBLIC_MARKET_DATA = "insufficient_public_market_data"
    NOT_ENABLED_FOR_UAT = "not_enabled_for_uat"
    TOP20_SOURCE_MISSING_VOLUME = "top20_source_missing_volume"
    TOP20_SOURCE_STALE = "top20_source_stale"
    PUBLIC_READ_ONLY_FETCH_FAILED = "public_read_only_fetch_failed"


@dataclass(frozen=True)
class TopVolumeSourceAsset:
    global_symbol: str
    source_rank: int
    volume_24h_usd: Decimal | None
    source_provider: str
    source_url: str
    source_timestamp_utc: datetime
    source_asset_id: str = ""


@dataclass(frozen=True)
class VenueMarketIdentity:
    global_symbol: str
    venue: str
    venue_symbol: str | None
    market_type: str | None
    product_type: str | None
    quote_asset: str | None
    settlement_asset: str | None
    venue_asset_id: str | None
    public_market_data_supported: bool
    enabled_for_uat: bool = True


@dataclass(frozen=True)
class UATObservationUniversePolicy:
    source_ranking_provider: str = "trusted_public_market_data_source_required_in_uat1"
    top_n: int = 20
    volume_metric: str = "24h_volume_usd"
    selected_venue: str = "hyperliquid"
    market_type_requirement: str = "perpetual"
    product_type_requirement: str = "perp"
    quote_asset_requirement: str = "USDC"
    settlement_asset_requirement: str = "USDC"
    identity_required: bool = True
    venue_support_required: bool = True
    public_source_required: bool = True
    private_api_keys_allowed: bool = False
    signed_endpoints_allowed: bool = False
    max_source_age_seconds: int = 3600
    deterministic_tie_breaking: str = "source_rank_then_global_symbol"


@dataclass(frozen=True)
class UATObservationCandidate:
    global_symbol: str
    source_rank: int
    source_24h_volume_usd: Decimal | None
    source_provider: str
    source_url: str
    source_timestamp_utc: datetime
    venue: str
    venue_symbol: str | None
    market_type: str | None
    product_type: str | None
    quote_asset: str | None
    settlement_asset: str | None
    venue_asset_id: str | None
    included: bool
    exclusion_reason_codes: tuple[UATUniverseExclusionReason, ...]
    observation_only: bool = True
    strategy_approved: bool = False
    paper_trading_approved: bool = False
    live_trading_approved: bool = False


@dataclass(frozen=True)
class UATUniverseResolution:
    policy: UATObservationUniversePolicy
    included: tuple[UATObservationCandidate, ...]
    excluded: tuple[UATObservationCandidate, ...]

    @property
    def candidates(self) -> tuple[UATObservationCandidate, ...]:
        return self.included + self.excluded


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _source_is_stale(
    *,
    source_timestamp_utc: datetime,
    as_of_utc: datetime,
    max_source_age_seconds: int,
) -> bool:
    timestamp = source_timestamp_utc
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    as_of = as_of_utc
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    return (as_of - timestamp).total_seconds() > max_source_age_seconds


class Top20UniverseResolver:
    """Resolve fixture top-volume assets into a UAT observation universe.

    This resolver consumes caller-supplied source and venue metadata. It never
    fetches market data or contacts an exchange.
    """

    def __init__(self, policy: UATObservationUniversePolicy | None = None) -> None:
        self.policy = policy or UATObservationUniversePolicy()

    def resolve(
        self,
        *,
        source_assets: list[TopVolumeSourceAsset] | tuple[TopVolumeSourceAsset, ...],
        venue_markets: list[VenueMarketIdentity] | tuple[VenueMarketIdentity, ...],
        as_of_utc: datetime,
    ) -> UATUniverseResolution:
        venue_by_symbol = {
            _normalize_symbol(market.global_symbol): market
            for market in venue_markets
            if market.venue.lower() == self.policy.selected_venue.lower()
        }
        ranked_assets = sorted(
            source_assets,
            key=lambda asset: (asset.source_rank, _normalize_symbol(asset.global_symbol)),
        )[: self.policy.top_n]

        included: list[UATObservationCandidate] = []
        excluded: list[UATObservationCandidate] = []

        for asset in ranked_assets:
            symbol = _normalize_symbol(asset.global_symbol)
            market = venue_by_symbol.get(symbol)
            reasons: list[UATUniverseExclusionReason] = []
            if asset.volume_24h_usd is None:
                reasons.append(UATUniverseExclusionReason.TOP20_SOURCE_MISSING_VOLUME)
            if _source_is_stale(
                source_timestamp_utc=asset.source_timestamp_utc,
                as_of_utc=as_of_utc,
                max_source_age_seconds=self.policy.max_source_age_seconds,
            ):
                reasons.append(UATUniverseExclusionReason.TOP20_SOURCE_STALE)
            if market is None:
                reasons.append(UATUniverseExclusionReason.UNSUPPORTED_BY_VENUE)
                candidate = UATObservationCandidate(
                    global_symbol=symbol,
                    source_rank=asset.source_rank,
                    source_24h_volume_usd=asset.volume_24h_usd,
                    source_provider=asset.source_provider,
                    source_url=asset.source_url,
                    source_timestamp_utc=asset.source_timestamp_utc,
                    venue=self.policy.selected_venue,
                    venue_symbol=None,
                    market_type=None,
                    product_type=None,
                    quote_asset=None,
                    settlement_asset=None,
                    venue_asset_id=None,
                    included=False,
                    exclusion_reason_codes=tuple(reasons),
                )
                excluded.append(candidate)
                continue

            if self.policy.identity_required and (
                not market.venue_symbol
                or not market.market_type
                or not market.product_type
                or not market.quote_asset
                or not market.settlement_asset
                or not market.venue_asset_id
            ):
                reasons.append(UATUniverseExclusionReason.MISSING_MARKET_IDENTITY)
            if (market.market_type or "").lower() != self.policy.market_type_requirement.lower():
                reasons.append(UATUniverseExclusionReason.UNSUPPORTED_MARKET_TYPE)
            if (market.product_type or "").lower() != self.policy.product_type_requirement.lower():
                reasons.append(UATUniverseExclusionReason.UNSUPPORTED_MARKET_TYPE)
            if (market.quote_asset or "").upper() != self.policy.quote_asset_requirement.upper():
                reasons.append(UATUniverseExclusionReason.QUOTE_ASSET_MISMATCH)
            if (market.settlement_asset or "").upper() != self.policy.settlement_asset_requirement.upper():
                reasons.append(UATUniverseExclusionReason.SETTLEMENT_ASSET_MISMATCH)
            if not market.public_market_data_supported:
                reasons.append(UATUniverseExclusionReason.INSUFFICIENT_PUBLIC_MARKET_DATA)
            if not market.enabled_for_uat:
                reasons.append(UATUniverseExclusionReason.NOT_ENABLED_FOR_UAT)

            candidate = UATObservationCandidate(
                global_symbol=symbol,
                source_rank=asset.source_rank,
                source_24h_volume_usd=asset.volume_24h_usd,
                source_provider=asset.source_provider,
                source_url=asset.source_url,
                source_timestamp_utc=asset.source_timestamp_utc,
                venue=market.venue,
                venue_symbol=market.venue_symbol,
                market_type=market.market_type,
                product_type=market.product_type,
                quote_asset=market.quote_asset,
                settlement_asset=market.settlement_asset,
                venue_asset_id=market.venue_asset_id,
                included=not reasons,
                exclusion_reason_codes=tuple(reasons),
            )
            if candidate.included:
                included.append(candidate)
            else:
                excluded.append(candidate)

        return UATUniverseResolution(
            policy=self.policy,
            included=tuple(included),
            excluded=tuple(excluded),
        )
