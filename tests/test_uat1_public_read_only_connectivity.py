from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from services.exchange.safety import ExchangeEndpointCategory, classify_hyperliquid_info_payload
from services.uat.public_read_only import (
    COINGECKO_TOP_VOLUME_URL,
    HYPERLIQUID_PUBLIC_INFO_URL,
    PublicHTTPResult,
    UAT1PublicReadOnlyMode,
    evaluate_uat1_endpoint_access,
    parse_coingecko_top_volume_assets,
    render_uat1_report,
    run_uat1_public_read_only_check,
)
from services.uat.universe import (
    Top20UniverseResolver,
    TopVolumeSourceAsset,
    UATUniverseExclusionReason,
    VenueMarketIdentity,
)


def _fake_transport(method: str, url: str, payload: dict[str, Any] | None) -> PublicHTTPResult:
    if method == "GET" and url == COINGECKO_TOP_VOLUME_URL:
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={"date": "Sun, 10 May 2026 07:00:00 GMT"},
            success=True,
            payload=[
                {"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1, "total_volume": 1000},
                {"id": "ethereum", "symbol": "eth", "market_cap_rank": 2, "total_volume": 900},
                {"id": "solana", "symbol": "sol", "market_cap_rank": 3, "total_volume": 800},
                {"id": "dogecoin", "symbol": "doge", "market_cap_rank": 4, "total_volume": 700},
            ],
        )
    assert method == "POST"
    assert url == HYPERLIQUID_PUBLIC_INFO_URL
    assert payload is not None
    info_type = payload["type"]
    if info_type == "meta":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload={
                "universe": [
                    {"name": "BTC", "szDecimals": 5},
                    {"name": "ETH", "szDecimals": 4},
                    {"name": "SOL", "szDecimals": 2},
                ]
            },
        )
    if info_type == "metaAndAssetCtxs":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload=[
                {
                    "universe": [
                        {"name": "BTC", "szDecimals": 5},
                        {"name": "ETH", "szDecimals": 4},
                        {"name": "SOL", "szDecimals": 2},
                    ]
                },
                [{"markPx": "100"}],
            ],
        )
    if info_type == "allMids":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload={"BTC": "100000", "ETH": "4000", "SOL": "200"},
        )
    if info_type == "l2Book":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload={"coin": payload["coin"], "levels": [[], []]},
        )
    if info_type == "candleSnapshot":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload=[{"t": 1, "T": 2, "o": "1", "h": "2", "l": "1", "c": "2", "v": "1"}],
        )
    if info_type == "fundingHistory":
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=200,
            response_headers={},
            success=True,
            payload=[{"coin": "ETH", "fundingRate": "0.0001"}],
        )
    raise AssertionError(f"unexpected payload: {payload}")


def test_public_read_only_network_mode_must_be_explicit() -> None:
    default_mode = UAT1PublicReadOnlyMode()
    allowed_mode = UAT1PublicReadOnlyMode(
        uat1_public_read_only=True,
        allow_public_read_only_network=True,
    )

    blocked = evaluate_uat1_endpoint_access(
        category=ExchangeEndpointCategory.PUBLIC_READ_ONLY,
        mode=default_mode,
    )
    allowed = evaluate_uat1_endpoint_access(
        category=ExchangeEndpointCategory.PUBLIC_READ_ONLY,
        mode=allowed_mode,
    )

    assert blocked.allowed is False
    assert "uat1_public_read_only_mode_not_enabled" in blocked.reason_codes
    assert "public_read_only_network_not_explicitly_allowed" in blocked.reason_codes
    assert allowed.allowed is True


def test_private_signed_order_and_unknown_categories_remain_blocked() -> None:
    mode = UAT1PublicReadOnlyMode(
        uat1_public_read_only=True,
        allow_public_read_only_network=True,
    )

    for category in (
        ExchangeEndpointCategory.PRIVATE_READ_ONLY,
        ExchangeEndpointCategory.PRIVATE_SIGNED,
        ExchangeEndpointCategory.ORDER_SUBMISSION,
        ExchangeEndpointCategory.ORDER_CANCEL,
        ExchangeEndpointCategory.ORDER_AMEND,
        ExchangeEndpointCategory.ORDER_RETRY_OR_RECOVERY,
        ExchangeEndpointCategory.UNKNOWN,
    ):
        decision = evaluate_uat1_endpoint_access(category=category, mode=mode)
        assert decision.allowed is False
        assert "uat1_only_public_read_only_endpoints_allowed" in decision.reason_codes


def test_allowed_and_disallowed_hyperliquid_info_types_are_classified() -> None:
    for info_type in ("meta", "metaAndAssetCtxs", "allMids", "l2Book", "candleSnapshot", "fundingHistory"):
        assert (
            classify_hyperliquid_info_payload({"type": info_type})
            == ExchangeEndpointCategory.PUBLIC_READ_ONLY
        )

    assert (
        classify_hyperliquid_info_payload({"type": "clearinghouseState", "user": "0xabc"})
        == ExchangeEndpointCategory.PRIVATE_READ_ONLY
    )
    assert classify_hyperliquid_info_payload({"type": "notAllowed"}) == ExchangeEndpointCategory.UNKNOWN


def test_top20_source_parser_handles_fixture_response() -> None:
    parsed = parse_coingecko_top_volume_assets(
        [
            {"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1, "total_volume": "123.45"},
            {"id": "missing-volume", "symbol": "mv", "market_cap_rank": 2},
        ],
        source_url=COINGECKO_TOP_VOLUME_URL,
        source_timestamp_utc=datetime(2026, 5, 10, 7, 0, tzinfo=UTC),
    )

    assert parsed[0].global_symbol == "BTC"
    assert parsed[0].volume_24h_usd == Decimal("123.45")
    assert parsed[1].global_symbol == "MV"
    assert parsed[1].volume_24h_usd is None


def test_top20_source_missing_volume_and_stale_source_exclude_assets() -> None:
    source_time = datetime(2026, 5, 10, 5, 0, tzinfo=UTC)
    resolution = Top20UniverseResolver().resolve(
        source_assets=(
            TopVolumeSourceAsset(
                global_symbol="BTC",
                source_rank=1,
                volume_24h_usd=None,
                source_provider="fixture_public_source",
                source_url="https://example.invalid/top20",
                source_timestamp_utc=source_time,
            ),
        ),
        venue_markets=(
            VenueMarketIdentity(
                global_symbol="BTC",
                venue="hyperliquid",
                venue_symbol="BTC",
                market_type="perpetual",
                product_type="perp",
                quote_asset="USDC",
                settlement_asset="USDC",
                venue_asset_id="0",
                public_market_data_supported=True,
            ),
        ),
        as_of_utc=datetime(2026, 5, 10, 7, 5, tzinfo=UTC),
    )

    assert not resolution.included
    assert resolution.excluded[0].global_symbol == "BTC"
    assert UATUniverseExclusionReason.TOP20_SOURCE_MISSING_VOLUME in resolution.excluded[0].exclusion_reason_codes
    assert UATUniverseExclusionReason.TOP20_SOURCE_STALE in resolution.excluded[0].exclusion_reason_codes


def test_uat1_run_resolves_hyperliquid_supported_universe_without_artifacts() -> None:
    mode = UAT1PublicReadOnlyMode(
        runtime_mode="uat",
        uat1_public_read_only=True,
        allow_public_read_only_network=True,
    )
    result = run_uat1_public_read_only_check(
        mode=mode,
        transport=_fake_transport,
        now=datetime(2026, 5, 10, 7, 5, tzinfo=UTC),
    )

    assert all(item.success for item in result.hyperliquid_info_type_results)
    assert result.top20_source_result.success is True
    assert [candidate.global_symbol for candidate in result.included_candidates] == ["BTC", "ETH", "SOL"]
    assert [candidate.global_symbol for candidate in result.excluded_candidates] == ["DOGE"]
    assert result.excluded_candidates[0].exclusion_reason_codes[0].value == "unsupported_by_venue"
    for candidate in result.included_candidates:
        assert candidate.observation_only is True
        assert candidate.strategy_approved is False
        assert candidate.paper_trading_approved is False
        assert candidate.live_trading_approved is False
    assert all(sample.mid_available for sample in result.market_data_samples)
    assert "uat2_operator_visible_shadow_drawdown_state" in result.remaining_blockers
    assert result.uat2_readiness_decision == "UAT2 is blocked"


def test_uat1_report_records_boundaries_and_readiness_decision() -> None:
    mode = UAT1PublicReadOnlyMode(
        runtime_mode="uat",
        uat1_public_read_only=True,
        allow_public_read_only_network=True,
    )
    result = run_uat1_public_read_only_check(
        mode=mode,
        transport=_fake_transport,
        now=datetime(2026, 5, 10, 7, 5, tzinfo=UTC),
    )
    report = render_uat1_report(result)

    assert "UAT1 Public Read-Only Connectivity And Top-20 Universe" in report
    assert "API keys used | `false`" in report
    assert "Private endpoints used: `false`" in report
    assert "Order endpoints used: `false`" in report
    assert "Strategy decisions created: `false`" in report
    assert "Order intents created: `false`" in report
    assert "Submitted orders created: `false`" in report
    assert "Top-20 inclusion means observation candidate only" in report
    assert "UAT2 is blocked" in report
    for phrase in ("proven profitable", "approved for paper trading", "ready for live trading"):
        assert phrase not in report.lower()


def test_committed_uat1_report_exists_after_generation_if_present() -> None:
    report_path = Path("docs/uat1_public_read_only_connectivity_and_top20_universe.md")
    if report_path.exists():
        report = report_path.read_text()
        assert "UAT1 is public read-only connectivity" in report
        assert "Paper trading is not approved" in report
        assert "Live trading is not approved" in report
        assert "Exchange order submission is not approved" in report
