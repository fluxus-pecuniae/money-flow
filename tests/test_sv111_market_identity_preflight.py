from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import Environment, MarketType, ProductType, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    MoneyFlowBacktestService,
    preflight_strategy_validation_candle_import,
    review_money_flow_evidence,
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_candle_import_preflight_result_to_dict,
    money_flow_evidence_review_to_dict,
    strategy_validation_market_identity_seed_result_to_dict,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv19_evidence_status import _seed_current_alembic_version


EXAMPLE_MANIFEST = Path(
    "configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json"
)


def _manifest_copy(tmp_path: Path, *, mutate=None) -> Path:
    payload = json.loads(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(payload)
    path = tmp_path / "market_identity.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    headers = [
        "symbol",
        "instrument_key",
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trade_count",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(header, "")) for header in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_candle_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "symbol": "BTC",
        "instrument_key": "perpetual:linear:BTC:USDC:USDC",
        "open_time": "2026-01-01T00:00:00Z",
        "close_time": "2026-01-01T00:15:00Z",
        "open": "100",
        "high": "101",
        "low": "99",
        "close": "100.5",
        "volume": "10",
        "trade_count": "2",
    }
    row.update(overrides)
    return row


def _seed_manifest(path: Path, *, session_factory) -> None:
    seed_strategy_validation_market_identity_from_manifest(
        path,
        operator_verified=True,
        verified_by="test_operator",
        session_factory=session_factory,
    )


def test_valid_offline_manifest_inserts_btc_eth_sol_instruments_and_symbols(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        operator_verified=True,
        verified_by="test_operator",
        session_factory=session_factory,
    )
    payload = strategy_validation_market_identity_seed_result_to_dict(result)

    assert payload["instruments_inserted"] == 3
    assert payload["symbols_inserted"] == 3
    assert payload["conflicts"] == []
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 3
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 3
        btc_symbol = session.scalar(
            select(SymbolModel).where(SymbolModel.symbol == "BTC")
        )
        assert btc_symbol is not None
        assert btc_symbol.is_strategy_eligible is False
        assert btc_symbol.is_trading_eligible is False
        assert btc_symbol.raw_metadata["research_only_market_identity_seed"] is True
        assert btc_symbol.raw_metadata["source"] == "manual_offline_manifest"
        assert btc_symbol.raw_metadata["sv_phase"] == "SV1.11.2"
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_dry_run_writes_nothing(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        dry_run=True,
        session_factory=session_factory,
    )

    assert result.instruments_inserted == 3
    assert result.symbols_inserted == 3
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_market_identity_verify_only_fails_when_rows_are_missing(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        verify_only=True,
        session_factory=session_factory,
    )

    reason_codes = {conflict["reason_code"] for conflict in result.conflicts}
    assert "missing_instrument" in reason_codes
    assert "missing_symbol_mapping" in reason_codes
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_market_identity_verify_only_passes_when_rows_exist(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    manifest = _manifest_copy(tmp_path)
    _seed_manifest(manifest, session_factory=session_factory)
    result = seed_strategy_validation_market_identity_from_manifest(
        manifest,
        verify_only=True,
        session_factory=session_factory,
    )

    assert result.conflicts == ()
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_rejects_conflicting_existing_symbol_mapping(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    with session_factory() as session:
        wrong_instrument = InstrumentModel(
            instrument_key="perpetual:linear:BTC:USDT:USDT",
            canonical_symbol="BTC",
            market_type=MarketType.PERPETUAL,
            product_type=ProductType.LINEAR,
            base_asset="BTC",
            quote_asset="USDT",
            settlement_asset="USDT",
            is_active=True,
        )
        session.add(wrong_instrument)
        session.flush()
        session.add(
            SymbolModel(
                instrument_ref_id=wrong_instrument.id,
                venue="hyperliquid",
                symbol="BTC",
                exchange_symbol="BTC",
                venue_asset_id=None,
                asset_id=None,
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset="BTC",
                quote_asset="USDC",
                settlement_asset="USDC",
                price_tick_size=Decimal("1"),
                quantity_step_size=Decimal("0.001"),
                min_order_size=Decimal("0.001"),
                size_decimals=None,
                max_leverage=None,
                only_isolated=False,
                is_perpetual=True,
                is_builder_deployed=False,
                is_strategy_eligible=False,
                is_trading_eligible=False,
                is_active=True,
                raw_metadata={},
            )
        )
        session.commit()

    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        operator_verified=True,
        verified_by="test_operator",
        session_factory=session_factory,
    )

    assert any(
        conflict["reason_code"] == "market_identity_symbol_instrument_conflict"
        for conflict in result.conflicts
    )
    with session_factory() as session:
        assert session.scalar(
            select(func.count()).select_from(InstrumentModel)
        ) == 1
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_rejects_malformed_decimal_fields(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()

    def mutate(payload: dict[str, object]) -> None:
        markets = payload["markets"]
        assert isinstance(markets, list)
        bad = deepcopy(markets[0])
        bad["symbol"]["price_tick_size"] = "NaN"
        markets[0] = bad

    try:
        seed_strategy_validation_market_identity_from_manifest(
            _manifest_copy(tmp_path, mutate=mutate),
            session_factory=session_factory,
        )
    except ValueError as exc:
        assert "finite and > 0" in str(exc)
    else:  # pragma: no cover - explicit failure path for readability.
        raise AssertionError("malformed Decimal manifest unexpectedly passed")
    _assert_no_live_artifacts(session_factory)


def test_evidence_review_reports_missing_identity_then_ready_identity(
    tmp_path: Path,
) -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    missing_review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
    )
    review_payload = money_flow_evidence_review_to_dict(missing_review)
    missing_identity = review_payload["canonical_market_identity_requirements"]
    assert {item["market_identity_status"] for item in missing_identity} == {
        "missing_instrument"
    }

    _seed_manifest(_manifest_copy(tmp_path), session_factory=session_factory)
    ready_review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=service,
        generate_evidence_packs=True,
        output_dir=tmp_path / "packs",
    )
    ready_payload = money_flow_evidence_review_to_dict(ready_review)
    assert {item["market_identity_status"] for item in ready_payload["canonical_market_identity_requirements"]} == {
        "ready"
    }
    assert ready_review.paper_readiness_review_status == "insufficient_data"
    assert ready_review.generated_campaign_count == 0
    assert not (tmp_path / "packs" / "money_flow_core_btc").exists()
    _assert_no_live_artifacts(session_factory)


def test_candle_import_preflight_rejects_unknown_symbol_mapping(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    csv_path = tmp_path / "candles.csv"
    _write_csv(csv_path, [_valid_candle_row(instrument_key="")])

    result = preflight_strategy_validation_candle_import(
        input_paths=(csv_path,),
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "unknown_symbol_mapping" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_candle_import_preflight_checks_review_json_requirements(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    review_json = tmp_path / "review.json"
    review_json.write_text(
        json.dumps(
            {
                "canonical_candle_import_requirements": [
                    {
                        "symbol": "BTC",
                        "instrument_key": "perpetual:linear:BTC:USDC:USDC",
                        "timeframe": "15m",
                        "requested_start_at": "2026-01-01T00:00:00+00:00",
                        "requested_end_at": "2026-01-15T00:00:00+00:00",
                        "window_label": "core_window_1",
                        "expected_candle_count": 1344,
                        "actual_candle_count": 0,
                        "missing_candle_count": 1344,
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = preflight_strategy_validation_candle_import(
        requirements_from_review_json=review_json,
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert payload["requirements_seen"] == 1
    requirement = payload["requirement_results"][0]
    assert requirement["timeframe"] == "15m"
    assert requirement["requested_start_at"] == "2026-01-01T00:00:00+00:00"
    assert requirement["market_identity_status"] == "missing_instrument"
    assert "missing_instrument" in payload["reason_codes"]
    _assert_no_live_artifacts(session_factory)


def test_candle_import_preflight_rejects_timezone_naive_timestamps(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_manifest(_manifest_copy(tmp_path), session_factory=session_factory)
    csv_path = tmp_path / "naive.csv"
    _write_csv(
        csv_path,
        [
            _valid_candle_row(
                open_time="2026-01-01T00:00:00",
                close_time="2026-01-01T00:15:00",
            )
        ],
    )

    result = preflight_strategy_validation_candle_import(
        input_paths=(csv_path,),
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "candle_import_naive_timestamp" in payload["reason_codes"]
    assert "timezone_required_for_candle_import" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_candle_import_preflight_accepts_valid_timezone_rows_without_writing(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_manifest(_manifest_copy(tmp_path), session_factory=session_factory)
    csv_path = tmp_path / "valid.csv"
    _write_csv(csv_path, [_valid_candle_row()])

    result = preflight_strategy_validation_candle_import(
        input_paths=(csv_path,),
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is True
    assert payload["reason_codes"] == []
    assert payload["input_rows_seen"] == 1
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)
