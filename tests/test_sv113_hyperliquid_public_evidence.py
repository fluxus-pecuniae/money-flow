from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import MarketType, ProductType, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    MoneyFlowBacktestService,
    load_money_flow_public_campaign_evidence_configs,
    money_flow_evidence_review_to_dict,
    money_flow_evidence_review_to_markdown,
    review_money_flow_evidence,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory, seed_candles
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv19_evidence_status import _seed_current_alembic_version


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _public_campaign_path(tmp_path: Path, *, expected_count: int = 36) -> Path:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    windows = [
        ("sleeve_15m", "15m", timedelta(minutes=15), "recent_public_15m"),
        ("sleeve_1h", "1h", timedelta(hours=1), "ytd_public_1h"),
        ("sleeve_4h", "4h", timedelta(hours=4), "ytd_public_4h"),
    ]
    payload = {
        "campaign_name": "money_flow_hyperliquid_public_ytd_recent",
        "description": "Synthetic public Hyperliquid campaign for SV1.13 tests.",
        "window_convention": (
            "(start_at, end_at] candle closes; closes exactly at start are "
            "excluded and closes on or before end are included."
        ),
        "venue": "hyperliquid",
        "environment": "testnet",
        "symbols": [
            {"symbol": "BTC", "instrument_key": "perpetual:linear:BTC:USDC:USDC"},
            {"symbol": "ETH", "instrument_key": "perpetual:linear:ETH:USDC:USDC"},
            {"symbol": "SOL", "instrument_key": "perpetual:linear:SOL:USDC:USDC"},
        ],
        "components": ["sleeve_15m", "sleeve_1h", "sleeve_4h"],
        "timeframe_windows": [
            {
                "component": component,
                "timeframe": timeframe,
                "label": label,
                "start": _iso(start),
                "end": _iso(start + delta * expected_count),
                "expected_candles_per_symbol": expected_count,
                "source": "hyperliquid_public_candleSnapshot",
                "status": "synthetic_complete",
            }
            for component, timeframe, delta, label in windows
        ],
        "fill_timings": [
            "same_candle_close_research_only",
            "next_candle_open",
            "next_candle_close",
        ],
        "fee_bps_values": ["2", "5"],
        "slippage_bps_values": ["1", "3"],
        "initial_capital": "10000",
        "position_notional_pct": "1.0",
        "output_dir": str(tmp_path / "evidence"),
        "report_formats": ["json", "markdown"],
    }
    path = tmp_path / "money_flow_hyperliquid_public_ytd_recent.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _seed_public_campaign_candles(session_factory, *, count: int = 36) -> None:
    timeframe_by_component = {
        "sleeve_15m": Timeframe.M15,
        "sleeve_1h": Timeframe.H1,
        "sleeve_4h": Timeframe.H4,
    }
    for asset_id, symbol in enumerate(("BTC", "ETH", "SOL")):
        instrument_ref_id, symbol_id, _instrument_key = _seed_research_symbol(
            session_factory,
            symbol=symbol,
            asset_id=asset_id,
        )
        for timeframe in timeframe_by_component.values():
            seed_candles(
                session_factory,
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol=symbol,
                timeframe=timeframe,
                closes=[Decimal(str(100 + index)) for index in range(count)],
            )


def _seed_research_symbol(
    session_factory,
    *,
    symbol: str,
    asset_id: int,
) -> tuple[str, str, str]:
    instrument_key = f"perpetual:linear:{symbol}:USDC:USDC"
    with session_factory() as session:
        instrument = InstrumentModel(
            instrument_key=instrument_key,
            canonical_symbol=symbol,
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset=symbol,
            quote_asset="USDC",
            settlement_asset="USDC",
            is_active=True,
        )
        session.add(instrument)
        session.flush()
        symbol_model = SymbolModel(
            instrument_ref_id=instrument.id,
            venue="hyperliquid",
            symbol=symbol,
            exchange_symbol=symbol,
            venue_asset_id=str(asset_id),
            asset_id=asset_id,
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset=symbol,
            quote_asset="USDC",
            settlement_asset="USDC",
            price_tick_size=Decimal("0.1"),
            quantity_step_size=Decimal("0.001"),
            min_order_size=Decimal("0.001"),
            size_decimals=3,
            max_leverage=20,
            only_isolated=False,
            is_perpetual=True,
            is_builder_deployed=False,
            is_strategy_eligible=False,
            is_trading_eligible=False,
            is_active=True,
            raw_metadata={
                "operator_verified": True,
                "verified_by": "Tercirafael",
                "verified_at": "2026-05-06T00:00:00+00:00",
                "research_only_market_identity_seed": True,
            },
        )
        session.add(symbol_model)
        session.commit()
        return instrument.id, symbol_model.id, instrument_key


def test_sv113_public_campaign_expands_to_hyperliquid_component_scoped_configs(
    tmp_path: Path,
) -> None:
    config_path = _public_campaign_path(tmp_path)

    configs = load_money_flow_public_campaign_evidence_configs(config_path)

    assert [config.campaign_name for _path, config in configs] == [
        "money_flow_hyperliquid_public_ytd_recent_sleeve_15m",
        "money_flow_hyperliquid_public_ytd_recent_sleeve_1h",
        "money_flow_hyperliquid_public_ytd_recent_sleeve_4h",
    ]
    assert {config.venue for _path, config in configs} == {"hyperliquid"}
    assert {tuple(config.components) for _path, config in configs} == {
        ("sleeve_15m",),
        ("sleeve_1h",),
        ("sleeve_4h",),
    }
    assert all(len(config.windows) == 1 for _path, config in configs)


def test_sv113_public_campaign_missing_candles_blocks_evidence_generation(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    for asset_id, symbol in enumerate(("BTC", "ETH", "SOL")):
        _seed_research_symbol(session_factory, symbol=symbol, asset_id=asset_id)
    service = MoneyFlowBacktestService(build_settings(), session_factory=session_factory)
    config_path = _public_campaign_path(tmp_path)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        generate_evidence_packs=True,
        generated_at=datetime(2026, 5, 6, 23, 30, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)

    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert payload["generated_campaign_count"] == 0
    assert payload["blocked_campaign_count"] == 3
    assert all(not result["evidence_pack_generated"] for result in payload["campaign_results"])
    assert all(
        "missing_persisted_candles" in result["blocked_or_gap_reason_codes"]
        for result in payload["campaign_results"]
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv113_seeded_public_campaign_generates_component_evidence_packs(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_public_campaign_candles(session_factory)
    service = MoneyFlowBacktestService(build_settings(), session_factory=session_factory)
    config_path = _public_campaign_path(tmp_path)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 6, 23, 31, tzinfo=UTC),
        generated_at=datetime(2026, 5, 6, 23, 31, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    markdown = money_flow_evidence_review_to_markdown(review)

    assert payload["paper_readiness_review_status"] == "ready_for_founder_review"
    assert payload["generated_campaign_count"] == 3
    assert payload["blocked_campaign_count"] == 0
    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert payload["calls_private_exchange_endpoints"] is False
    assert payload["calls_exchange_order_endpoints"] is False
    for result in payload["campaign_results"]:
        assert result["evidence_pack_generated"] is True
        assert result["readiness_status"] == "ready_for_founder_review"
        manifest = result["evidence_pack_manifest"]
        assert manifest["venue"] == "hyperliquid"
        assert manifest["sanitized_db_target"]
        assert "***" in manifest["sanitized_db_target"]
        assert manifest["no_live_execution_artifacts_created"] is True
        assert manifest["exchange_adapters_called"] is False
        assert manifest["no_exchange_adapters_called"] is True
        assert manifest["calls_private_exchange_endpoints"] is False
        assert manifest["calls_exchange_order_endpoints"] is False
        assert manifest["no_routing_artifacts_created"] is True
        assert manifest["routing_artifacts_created"] is False
        assert manifest["paper_trading_auto_approved"] is False
        assert manifest["live_trading_approved"] is False
        assert "hyperliquid" in result["campaign_name"]
        assert Path(result["evidence_pack_path"]).exists()
    assert "not proof of future profitability" in markdown
    assert "not an automatic approval" in markdown
    assert "paper trading approved" not in markdown.lower()
    assert "recommended strategy" not in markdown.lower()
    assert "proven profitable" not in markdown.lower()
    _assert_no_live_artifacts(session_factory)
