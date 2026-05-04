from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

from db.models import CandleModel, SymbolModel
from services.strategy_validation import (
    MoneyFlowBacktestService,
    evaluate_strategy_validation_import_readiness,
    run_strategy_validation_guarded_import_attempt,
    strategy_validation_guarded_import_attempt_result_to_dict,
    strategy_validation_import_readiness_to_dict,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv1111_market_identity_preflight_hardening import _manifest_copy, _write_csv
from test_sv19_evidence_status import _seed_current_alembic_version


def _service(session_factory) -> MoneyFlowBacktestService:
    return MoneyFlowBacktestService(build_settings(), session_factory=session_factory)


def _canonical_requirements(session_factory) -> list[dict[str, object]]:
    result = evaluate_strategy_validation_import_readiness(
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_import_readiness_to_dict(result)
    return list(payload["canonical_candle_file_requirements"])


def _write_requirement_file(directory: Path, requirement: dict[str, object]) -> Path:
    path = directory / str(requirement["suggested_filename"])
    _write_csv(path, _rows_for_requirement(requirement))
    return path


def _write_all_requirement_files(
    directory: Path,
    requirements: list[dict[str, object]],
) -> None:
    for requirement in requirements:
        _write_requirement_file(directory, requirement)


def _rows_for_requirement(requirement: dict[str, object]) -> list[dict[str, object]]:
    timeframe = str(requirement["timeframe"])
    duration = {
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
    }[timeframe]
    start = datetime.fromisoformat(str(requirement["requested_start_at"]))
    count = int(requirement["expected_candle_count"])
    rows: list[dict[str, object]] = []
    for index in range(count):
        close_time = start + duration * (index + 1)
        open_time = close_time - duration
        base = 100 + (index % 100)
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


def test_sv1123_no_operator_verification_does_not_seed_identity(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    result = run_strategy_validation_guarded_import_attempt(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=False,
    )
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)

    assert payload["identity_seeded"] is False
    assert payload["identity_seed_status"] == "not_requested"
    assert payload["final_status"] == "identity_missing"
    assert "market_identity_operator_verification_required" in payload["reason_codes"]
    assert payload["guarded_import"]["import_attempted"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1123_verified_seed_remains_non_trading_when_files_missing(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    result = run_strategy_validation_guarded_import_attempt(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="test_operator",
        market_identity_values_checked_offline=True,
    )
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)

    assert payload["identity_seeded"] is True
    assert payload["identity_seed_status"] == "seeded"
    assert payload["final_status"] == "files_missing"
    assert payload["guarded_import"]["import_attempted"] is False
    assert len(payload["input_files_missing"]) == 18
    with session_factory() as session:
        symbols = session.scalars(select(SymbolModel)).all()
        assert {symbol.symbol for symbol in symbols} == {"BTC", "ETH", "SOL"}
        for symbol in symbols:
            assert symbol.is_strategy_eligible is False
            assert symbol.is_trading_eligible is False
            assert symbol.raw_metadata["operator_verified"] is True
            assert symbol.raw_metadata["verified_by"] == "test_operator"
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1123_incomplete_file_mapping_blocks_import(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    requirements = _canonical_requirements(session_factory)
    first_file = _write_requirement_file(tmp_path, requirements[0])

    result = run_strategy_validation_guarded_import_attempt(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="test_operator",
        market_identity_values_checked_offline=True,
        input_paths=(first_file,),
    )
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)

    assert payload["final_status"] == "files_missing"
    assert payload["guarded_import"]["import_attempted"] is False
    assert "requirement_missing_input_file" in payload["reason_codes"]
    assert "canonical_candle_files_missing" in payload["reason_codes"]
    assert len(payload["input_files_missing"]) == 17
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1123_failed_preflight_blocks_import(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    requirements = _canonical_requirements(session_factory)
    _write_all_requirement_files(tmp_path, requirements)
    first_file = tmp_path / str(requirements[0]["suggested_filename"])
    rows = _rows_for_requirement(requirements[0])
    rows[0]["open_time"] = rows[1]["open_time"]
    rows[0]["close_time"] = rows[1]["close_time"]
    _write_csv(first_file, rows)

    result = run_strategy_validation_guarded_import_attempt(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="test_operator",
        market_identity_values_checked_offline=True,
        input_dir=tmp_path,
    )
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)

    assert payload["final_status"] == "preflight_blocked"
    assert payload["guarded_import"]["import_attempted"] is False
    assert "requirement_duplicate_close_time_slots" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1123_successful_guarded_import_with_synthetic_complete_bundle(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    requirements = _canonical_requirements(session_factory)
    _write_all_requirement_files(tmp_path, requirements)
    expected_rows = sum(int(item["expected_candle_count"]) for item in requirements)

    result = run_strategy_validation_guarded_import_attempt(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="test_operator",
        market_identity_values_checked_offline=True,
        input_dir=tmp_path,
    )
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)

    assert payload["final_status"] == "canonical_import_complete"
    assert payload["sv113_evidence_review_can_proceed"] is True
    assert payload["guarded_import"]["import_attempted"] is True
    assert payload["guarded_import"]["import_completed"] is True
    assert payload["guarded_import"]["rows_inserted"] == expected_rows
    assert payload["guarded_import"]["rows_updated"] == 0
    assert payload["guarded_import"]["rows_unchanged"] == 0
    assert payload["evidence_packs_generated"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == expected_rows
    _assert_no_live_artifacts(session_factory)


def test_sv1123_boundary_flags_create_no_live_or_evidence_artifacts(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    payload = strategy_validation_guarded_import_attempt_result_to_dict(
        run_strategy_validation_guarded_import_attempt(
            service=_service(session_factory),
            session_factory=session_factory,
            manifest_path=_manifest_copy(tmp_path),
        )
    )

    assert payload["evidence_packs_generated"] is False
    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert payload["calls_private_exchange_endpoints"] is False
    assert payload["calls_exchange_order_endpoints"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)
