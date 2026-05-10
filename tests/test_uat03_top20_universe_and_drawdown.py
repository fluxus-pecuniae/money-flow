from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from core.security import redact_sensitive_structure
from services.exchange.safety import (
    HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST,
    classify_hyperliquid_info_payload,
    ExchangeEndpointCategory,
)
from services.uat.drawdown import UATDrawdownMonitor, UATDrawdownObservation, UATDrawdownPolicy
from services.uat.universe import (
    Top20UniverseResolver,
    TopVolumeSourceAsset,
    UATObservationUniversePolicy,
    UATUniverseExclusionReason,
    VenueMarketIdentity,
)


def _source_asset(symbol: str, rank: int, volume: Decimal | None = Decimal("1000000")) -> TopVolumeSourceAsset:
    return TopVolumeSourceAsset(
        global_symbol=symbol,
        source_rank=rank,
        volume_24h_usd=volume,
        source_provider="fixture_public_provider",
        source_url="https://public.example.invalid/top-volume",
        source_timestamp_utc=datetime(2026, 5, 10, 6, 0, tzinfo=UTC),
        source_asset_id=f"fixture:{symbol.lower()}",
    )


def _venue_market(
    symbol: str,
    *,
    venue_symbol: str | None = None,
    market_type: str | None = "perpetual",
    product_type: str | None = "perp",
    quote_asset: str | None = "USDC",
    settlement_asset: str | None = "USDC",
    venue_asset_id: str | None = None,
    public_market_data_supported: bool = True,
    enabled_for_uat: bool = True,
) -> VenueMarketIdentity:
    return VenueMarketIdentity(
        global_symbol=symbol,
        venue="hyperliquid",
        venue_symbol=venue_symbol or symbol,
        market_type=market_type,
        product_type=product_type,
        quote_asset=quote_asset,
        settlement_asset=settlement_asset,
        venue_asset_id=venue_asset_id or symbol,
        public_market_data_supported=public_market_data_supported,
        enabled_for_uat=enabled_for_uat,
    )


def test_top20_universe_policy_exists_with_safe_source_requirements() -> None:
    policy = UATObservationUniversePolicy()

    assert policy.top_n == 20
    assert policy.volume_metric == "24h_volume_usd"
    assert policy.selected_venue == "hyperliquid"
    assert policy.public_source_required is True
    assert policy.private_api_keys_allowed is False
    assert policy.signed_endpoints_allowed is False
    assert policy.identity_required is True
    assert policy.venue_support_required is True


def test_top20_resolver_uses_fixture_data_and_preserves_observation_only_truth() -> None:
    resolver = Top20UniverseResolver()

    result = resolver.resolve(
        source_assets=[_source_asset("ETH", 1), _source_asset("BTC", 2)],
        venue_markets=[_venue_market("ETH"), _venue_market("BTC")],
        as_of_utc=datetime(2026, 5, 10, 6, 15, tzinfo=UTC),
    )

    assert [candidate.global_symbol for candidate in result.included] == ["ETH", "BTC"]
    for candidate in result.included:
        assert candidate.included is True
        assert candidate.observation_only is True
        assert candidate.strategy_approved is False
        assert candidate.paper_trading_approved is False
        assert candidate.live_trading_approved is False


def test_top20_resolver_excludes_unsupported_and_identity_mismatch_assets() -> None:
    resolver = Top20UniverseResolver()
    stale_asset = TopVolumeSourceAsset(
        global_symbol="DOGE",
        source_rank=5,
        volume_24h_usd=Decimal("1000000"),
        source_provider="fixture_public_provider",
        source_url="https://public.example.invalid/top-volume",
        source_timestamp_utc=datetime(2026, 5, 10, 3, 0, tzinfo=UTC),
    )

    result = resolver.resolve(
        source_assets=[
            _source_asset("ETH", 1),
            _source_asset("SOL", 2),
            _source_asset("XRP", 3, None),
            _source_asset("ADA", 4),
            stale_asset,
        ],
        venue_markets=[
            _venue_market("ETH"),
            VenueMarketIdentity(
                global_symbol="SOL",
                venue="hyperliquid",
                venue_symbol=None,
                market_type=None,
                product_type="perp",
                quote_asset="USDC",
                settlement_asset="USDC",
                venue_asset_id=None,
                public_market_data_supported=True,
            ),
            _venue_market("XRP", quote_asset="USDT"),
            _venue_market("ADA", settlement_asset="USDT"),
        ],
        as_of_utc=datetime(2026, 5, 10, 6, 15, tzinfo=UTC),
    )

    excluded = {candidate.global_symbol: candidate for candidate in result.excluded}

    assert "ETH" in {candidate.global_symbol for candidate in result.included}
    assert UATUniverseExclusionReason.MISSING_MARKET_IDENTITY in excluded["SOL"].exclusion_reason_codes
    assert UATUniverseExclusionReason.TOP20_SOURCE_MISSING_VOLUME in excluded["XRP"].exclusion_reason_codes
    assert UATUniverseExclusionReason.QUOTE_ASSET_MISMATCH in excluded["XRP"].exclusion_reason_codes
    assert UATUniverseExclusionReason.SETTLEMENT_ASSET_MISMATCH in excluded["ADA"].exclusion_reason_codes
    assert UATUniverseExclusionReason.UNSUPPORTED_BY_VENUE in excluded["DOGE"].exclusion_reason_codes
    assert UATUniverseExclusionReason.TOP20_SOURCE_STALE in excluded["DOGE"].exclusion_reason_codes


def test_eth_evidence_candidate_is_distinct_from_top20_observation_universe() -> None:
    report = Path("docs/uat0_3_top20_universe_and_drawdown_readiness.md").read_text()

    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in report
    assert "ETH evidence candidate" in report
    assert "top-20 supported assets" in report
    assert "Top-20 inclusion is not strategy approval" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report


def test_hyperliquid_read_only_allowlist_includes_required_public_info_types() -> None:
    required = {
        "meta",
        "metaAndAssetCtxs",
        "allMids",
        "l2Book",
        "candleSnapshot",
        "fundingHistory",
    }

    assert required.issubset(set(HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST.allowed_public_info_types))
    for info_type in required:
        assert (
            classify_hyperliquid_info_payload({"type": info_type})
            == ExchangeEndpointCategory.PUBLIC_READ_ONLY
        )
    assert HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST.endpoint_url_status == "needs_verification"


def test_drawdown_monitor_computes_max_drawdown_and_threshold_reason_code() -> None:
    monitor = UATDrawdownMonitor(
        candidate_id="money_flow_hyperliquid_eth_1h_baseline_uat_candidate",
        universe_asset_id="ETH",
        initial_observed_equity=Decimal("10000"),
        policy=UATDrawdownPolicy(threshold_pct=Decimal("0.10")),
    )

    first = monitor.observe(
        UATDrawdownObservation(
            timestamp_utc=datetime(2026, 5, 10, 6, 0, tzinfo=UTC),
            observed_equity=Decimal("11000"),
        )
    )
    second = monitor.observe(
        UATDrawdownObservation(
            timestamp_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
            observed_equity=Decimal("9700"),
            realized_pnl=Decimal("-300"),
            unrealized_pnl=Decimal("-1000"),
        )
    )

    assert first.max_drawdown_amount == Decimal("0")
    assert second.max_observed_equity == Decimal("11000")
    assert second.max_drawdown_amount == Decimal("1300")
    assert second.max_drawdown_pct == Decimal("1300") / Decimal("11000")
    assert second.threshold_breached is True
    assert "uat_drawdown_threshold_breached" in second.reason_codes
    assert "shadow_or_simulated_drawdown_not_account_truth" in second.reason_codes


def test_structured_redaction_fixture_covers_api_error_like_payloads() -> None:
    payload = {
        "message": "Authorization: Bearer abc123",
        "detail": {
            "api_key": "key123",
            "dsn": "postgresql+psycopg://user:pass123@host:5432/db",
            "nested": ["secret=sec123", "safe"],
        },
    }

    redacted = redact_sensitive_structure(payload)
    rendered = repr(redacted)

    for secret in ("abc123", "key123", "pass123", "sec123"):
        assert secret not in rendered
    assert "<redacted>" in rendered


def test_uat03_report_records_readiness_decision_and_boundaries() -> None:
    report = Path("docs/uat0_3_top20_universe_and_drawdown_readiness.md").read_text()

    assert "Top-20 Universe Policy" in report
    assert "Hyperliquid Market Intersection Logic" in report
    assert "Runtime Drawdown Monitoring Policy" in report
    assert "Redaction Verification Status" in report
    assert "`UAT1 read-only connectivity may proceed`" in report
    assert "does not connect to exchanges" in report
    assert "does not submit orders" in report
    assert "does not fetch real top-20 assets" in report
    assert "Paper trading is not approved" in report
    assert "Live trading is not approved" in report
    forbidden = (
        "approved for paper trading",
        "ready for live trading",
        "proven profitable",
    )
    lower_report = report.lower()
    for phrase in forbidden:
        assert phrase not in lower_report
