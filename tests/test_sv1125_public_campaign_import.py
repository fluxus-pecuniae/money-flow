from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

from db.models import CandleModel, SymbolModel
from services.strategy_validation import (
    EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT,
    MoneyFlowBacktestService,
    build_public_campaign_candle_requirements,
    run_strategy_validation_public_campaign_import,
    strategy_validation_public_campaign_import_result_to_dict,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv1111_market_identity_preflight_hardening import _manifest_copy, _write_csv
from test_sv19_evidence_status import _seed_current_alembic_version


def _service(session_factory) -> MoneyFlowBacktestService:
    return MoneyFlowBacktestService(build_settings(), session_factory=session_factory)


def _campaign_config(tmp_path: Path) -> Path:
    path = tmp_path / "money_flow_hyperliquid_public_ytd_recent.json"
    payload = {
        "campaign_name": "money_flow_hyperliquid_public_ytd_recent",
        "venue": "hyperliquid",
        "environment": "testnet",
        "symbols": [
            {"symbol": "BTC", "instrument_key": "perpetual:linear:BTC:USDC:USDC"},
            {"symbol": "ETH", "instrument_key": "perpetual:linear:ETH:USDC:USDC"},
            {"symbol": "SOL", "instrument_key": "perpetual:linear:SOL:USDC:USDC"},
        ],
        "timeframe_windows": [
            {
                "component": "sleeve_15m",
                "timeframe": "15m",
                "label": "synthetic_15m",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T00:30:00Z",
                "expected_candles_per_symbol": 2,
                "source": "hyperliquid_public_candleSnapshot",
            },
            {
                "component": "sleeve_1h",
                "timeframe": "1h",
                "label": "synthetic_1h",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T02:00:00Z",
                "expected_candles_per_symbol": 2,
                "source": "hyperliquid_public_candleSnapshot",
            },
            {
                "component": "sleeve_4h",
                "timeframe": "4h",
                "label": "synthetic_4h",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T08:00:00Z",
                "expected_candles_per_symbol": 2,
                "source": "hyperliquid_public_candleSnapshot",
            },
        ],
        "local_candle_output_dir": str(tmp_path / "csv"),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_public_files(
    directory: Path,
    requirements: list[dict[str, object]],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for requirement in requirements:
        _write_csv(directory / str(requirement["suggested_filename"]), _rows(requirement))


def _rows(requirement: dict[str, object]) -> list[dict[str, object]]:
    timeframe = str(requirement["timeframe"])
    duration = {
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
    }[timeframe]
    start = datetime.fromisoformat(str(requirement["requested_start_at"]))
    rows: list[dict[str, object]] = []
    for index in range(int(requirement["expected_candle_count"])):
        close_time = start + duration * (index + 1)
        open_time = close_time - duration
        base = 100 + index
        rows.append(
            {
                "symbol": requirement["symbol"],
                "instrument_key": requirement["instrument_key"],
                "open_time": _iso_z(open_time),
                "close_time": _iso_z(close_time),
                "open": str(base),
                "high": str(base + 2),
                "low": str(base - 1),
                "close": str(base + 1),
                "volume": "10",
                "trade_count": "1",
            }
        )
    return rows


def _iso_z(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def test_sv1125_no_operator_approval_does_not_seed_or_import(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=False,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["identity_seeded"] is False
    assert payload["final_status"] == "identity_missing"
    assert "market_identity_operator_verification_required" in payload["reason_codes"]
    assert payload["guarded_import"]["import_attempted"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1125_approved_identity_seed_remains_non_trading_when_files_missing(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="Tercirafael",
        market_identity_values_checked_offline=True,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["identity_seeded"] is True
    assert payload["identity_seed_status"] == "seeded"
    assert payload["final_status"] == "files_missing"
    assert len(payload["input_files_missing"]) == EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT
    with session_factory() as session:
        symbols = session.scalars(select(SymbolModel)).all()
        assert {symbol.symbol for symbol in symbols} == {"BTC", "ETH", "SOL"}
        for symbol in symbols:
            assert symbol.is_strategy_eligible is False
            assert symbol.is_trading_eligible is False
            assert symbol.raw_metadata["operator_verified"] is True
            assert symbol.raw_metadata["verified_by"] == "Tercirafael"
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1125_public_campaign_uses_9_file_expectation_not_january_18(
    tmp_path: Path,
) -> None:
    config = _campaign_config(tmp_path)
    requirements = build_public_campaign_candle_requirements(campaign_config_path=config)

    assert len(requirements) == EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT
    assert len(requirements) != 18
    assert {item["suggested_filename"] for item in requirements} == {
        "hyperliquid_btc_15m_20260101_000000z_20260101_003000z.csv",
        "hyperliquid_btc_1h_20260101_000000z_20260101_020000z.csv",
        "hyperliquid_btc_4h_20260101_000000z_20260101_080000z.csv",
        "hyperliquid_eth_15m_20260101_000000z_20260101_003000z.csv",
        "hyperliquid_eth_1h_20260101_000000z_20260101_020000z.csv",
        "hyperliquid_eth_4h_20260101_000000z_20260101_080000z.csv",
        "hyperliquid_sol_15m_20260101_000000z_20260101_003000z.csv",
        "hyperliquid_sol_1h_20260101_000000z_20260101_020000z.csv",
        "hyperliquid_sol_4h_20260101_000000z_20260101_080000z.csv",
    }


def test_sv1125_report_separates_file_coverage_from_identity_readiness(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)
    requirements = list(build_public_campaign_candle_requirements(campaign_config_path=config))
    input_dir = tmp_path / "csv"
    _write_public_files(input_dir, requirements)

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        input_dir=input_dir,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["final_status"] == "identity_missing"
    assert all(item["coverage_complete"] is True for item in payload["public_file_coverage_results"])
    assert all(item["row_level_ready"] is True for item in payload["public_file_coverage_results"])
    assert all(
        item["operator_verified_market_identity_status"] != "ready"
        for item in payload["identity_readiness_results"]
    )
    assert payload["guarded_import"]["import_attempted"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1125_incomplete_public_file_mapping_blocks_import(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)
    requirements = list(build_public_campaign_candle_requirements(campaign_config_path=config))
    input_dir = tmp_path / "csv"
    _write_public_files(input_dir, requirements[:-1])

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="Tercirafael",
        market_identity_values_checked_offline=True,
        input_dir=input_dir,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["final_status"] == "files_missing"
    assert payload["guarded_import"]["import_attempted"] is False
    assert len(payload["input_files_missing"]) == 1
    assert "requirement_missing_input_file" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1125_failed_public_preflight_blocks_import(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)
    requirements = list(build_public_campaign_candle_requirements(campaign_config_path=config))
    input_dir = tmp_path / "csv"
    _write_public_files(input_dir, requirements)
    first = input_dir / str(requirements[0]["suggested_filename"])
    duplicate_rows = _rows(requirements[0])
    duplicate_rows[1]["close_time"] = duplicate_rows[0]["close_time"]
    duplicate_rows[1]["open_time"] = duplicate_rows[0]["open_time"]
    _write_csv(first, duplicate_rows)

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="Tercirafael",
        market_identity_values_checked_offline=True,
        input_dir=input_dir,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["final_status"] == "preflight_blocked"
    assert payload["guarded_import"]["import_attempted"] is False
    assert "requirement_duplicate_close_time_slots" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1125_successful_guarded_import_with_synthetic_9_file_bundle(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)
    requirements = list(build_public_campaign_candle_requirements(campaign_config_path=config))
    input_dir = tmp_path / "csv"
    _write_public_files(input_dir, requirements)
    expected_rows = sum(int(item["expected_candle_count"]) for item in requirements)

    result = run_strategy_validation_public_campaign_import(
        campaign_config_path=config,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="Tercirafael",
        market_identity_values_checked_offline=True,
        input_dir=input_dir,
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_public_campaign_import_result_to_dict(result)

    assert payload["final_status"] == "public_campaign_import_complete"
    assert payload["public_requirements_seen"] == EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT
    assert payload["sv113_evidence_review_can_proceed"] is True
    assert payload["guarded_import"]["import_attempted"] is True
    assert payload["guarded_import"]["rows_inserted"] == expected_rows
    assert payload["guarded_import"]["rows_updated"] == 0
    assert payload["guarded_import"]["rows_unchanged"] == 0
    assert payload["evidence_packs_generated"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == expected_rows
    _assert_no_live_artifacts(session_factory)


def test_sv1125_supported_venue_inventory_keeps_non_hyperliquid_blocked_or_later(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    config = _campaign_config(tmp_path)

    payload = strategy_validation_public_campaign_import_result_to_dict(
        run_strategy_validation_public_campaign_import(
            campaign_config_path=config,
            manifest_path=_manifest_copy(tmp_path),
            service=_service(session_factory),
            session_factory=session_factory,
        )
    )
    inventory = {item["venue"]: item for item in payload["supported_venue_inventory"]}

    assert inventory["hyperliquid"]["import_recommendation"] == "current_candidate"
    assert inventory["aster"]["import_recommendation"] == "later_candidate"
    assert inventory["binance"]["import_recommendation"] == "later_candidate"
    assert inventory["okx"]["import_recommendation"] == "blocked"
    assert inventory["coinbase"]["import_recommendation"] == "blocked"
    assert inventory["kraken"]["import_recommendation"] == "blocked"
    assert inventory["okx"]["native_trade_count_available"] is False
    assert inventory["coinbase"]["native_trade_count_available"] is False
    assert "placeholder_trade_count_not_canonical" in inventory["okx"]["blocked_reason"]
    assert "placeholder_trade_count_not_canonical" in inventory["coinbase"]["blocked_reason"]
    assert payload["evidence_packs_generated"] is False
    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert payload["calls_private_exchange_endpoints"] is False
    assert payload["calls_exchange_order_endpoints"] is False
    _assert_no_live_artifacts(session_factory)
