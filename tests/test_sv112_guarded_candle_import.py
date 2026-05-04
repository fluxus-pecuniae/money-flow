from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

import services.strategy_validation.candle_bundle_import as candle_bundle_import_service
from core.domain.enums import Environment, Timeframe
from db.models import CandleModel, SymbolModel
from services.strategy_validation import (
    MoneyFlowBacktestService,
    guarded_import_strategy_validation_candle_bundle,
    strategy_validation_canonical_candle_bundle_import_result_to_dict,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory, seed_symbol
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv1111_market_identity_preflight_hardening import (
    _requirement,
    _row,
    _seed_verified_identity,
    _write_csv,
)
from test_sv19_evidence_status import _seed_current_alembic_version


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _service(session_factory, **settings_overrides) -> MoneyFlowBacktestService:
    return MoneyFlowBacktestService(
        build_settings(**settings_overrides),
        session_factory=session_factory,
    )


def _three_rows() -> list[dict[str, object]]:
    return [
        _row(),
        _row(
            open_time="2026-01-01T00:15:00Z",
            close_time="2026-01-01T00:30:00Z",
            open="100.5",
            high="102",
            low="100",
            close="101.5",
        ),
        _row(
            open_time="2026-01-01T00:30:00Z",
            close_time="2026-01-01T00:45:00Z",
            open="101.5",
            high="103",
            low="101",
            close="102.5",
        ),
    ]


def _guarded_import(
    *,
    tmp_path: Path,
    session_factory,
    rows: list[dict[str, object]] | None = None,
    requirement: dict[str, object] | None = None,
    input_requirement_map: dict[str, object] | None = None,
    service: MoneyFlowBacktestService | None = None,
    input_paths: tuple[Path, ...] | None = None,
    requirements: list[dict[str, object]] | None = None,
):
    csv_path = tmp_path / "btc_15m.csv"
    requirement_path = tmp_path / "requirements.json"
    if input_paths is None:
        _write_csv(csv_path, rows if rows is not None else _three_rows())
        input_paths = (csv_path,)
    _write_json(requirement_path, requirements or [requirement or _requirement()])
    return guarded_import_strategy_validation_candle_bundle(
        input_paths=input_paths,
        requirement_json_paths=(requirement_path,),
        input_requirement_map=input_requirement_map,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        source_label_prefix="sv112_test",
        service=service or _service(session_factory),
        session_factory=session_factory,
    )


def test_guarded_import_requires_intended_migrated_strategy_validation_db(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        service=_service(session_factory, DB_NAME="postgres"),
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert payload["import_completed"] is False
    assert "strategy_validation_db_target_ambiguous" in payload["reason_codes"]
    assert "canonical_candle_import_blocked_by_db_target_truth" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_requires_operator_verified_non_trading_identity(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    seed_symbol(session_factory, "BTC")

    result = _guarded_import(tmp_path=tmp_path, session_factory=session_factory)
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert "operator_verified_market_identity_not_ready" in payload["reason_codes"]
    assert "strategy_validation_identity_strategy_eligible" in payload["reason_codes"]
    assert "strategy_validation_identity_trading_eligible" in payload["reason_codes"]
    assert "operator_verified_market_identity_missing" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_preserves_non_trading_identity_on_success(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _guarded_import(tmp_path=tmp_path, session_factory=session_factory)
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_completed"] is True
    assert payload["rows_inserted"] == 3
    assert payload["evidence_packs_generated"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 3
        btc = session.scalar(select(SymbolModel).where(SymbolModel.symbol == "BTC"))
        assert btc is not None
        assert btc.is_strategy_eligible is False
        assert btc.is_trading_eligible is False
        assert btc.raw_metadata["operator_verified"] is True
        assert btc.raw_metadata["verified_by"] == "test_operator"
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_blocks_timezone_naive_canonical_file(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(
                open_time="2026-01-01T00:00:00",
                close_time="2026-01-01T00:15:00",
            )
        ],
        requirement=_requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z"),
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert "candle_import_naive_timestamp" in payload["reason_codes"]
    assert "timezone_required_for_candle_import" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_requires_complete_one_to_one_mapping(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    _write_csv(first, [_row()])
    _write_csv(
        second,
        [
            _row(
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
            )
        ],
    )

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        input_paths=(first, second),
        requirement=_requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z"),
        input_requirement_map={str(first): 0},
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert "input_file_missing_requirement_mapping" in payload["reason_codes"]
    assert "requirement_mapping_incomplete" in payload["reason_codes"]
    assert str(second) in payload["unmapped_input_files"]
    blocked_files = {
        item["input_path"]: item for item in payload["file_import_results"] if item["input_path"]
    }
    assert blocked_files[str(second)]["file_status"] == "unmapped_input_file_blocked"
    assert "unmapped_input_file_blocked" in blocked_files[str(second)]["reason_codes"]
    assert payload["files_blocked"] >= 1
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_requires_exact_requirement_coverage(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(),
            _row(
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
            ),
        ],
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert "requirement_missing_close_time_slots" in payload["reason_codes"]
    assert "requirement_actual_candle_count_mismatch" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_reports_missing_requirement_placeholder(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "first.csv"
    _write_csv(first, [_row()])
    requirements = [
        _requirement(
            expected_candle_count=1,
            requested_end_at="2026-01-01T00:15:00Z",
            window_label="first",
        ),
        _requirement(
            requested_start_at="2026-01-01T00:15:00Z",
            requested_end_at="2026-01-01T00:30:00Z",
            expected_candle_count=1,
            window_label="second",
        ),
    ]

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        input_paths=(first,),
        requirements=requirements,
        input_requirement_map={str(first): 0},
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert payload["requirements_seen"] == 2
    assert payload["requirements_missing"] == 1
    assert "requirement_missing_input_file" in payload["reason_codes"]
    assert "missing_requirement_blocked" in payload["reason_codes"]
    missing_file_rows = [
        item
        for item in payload["file_import_results"]
        if item["file_status"] == "missing_requirement_blocked"
    ]
    assert len(missing_file_rows) == 1
    assert missing_file_rows[0]["input_path"] is None
    assert "requirement_missing_input_file" in missing_file_rows[0]["reason_codes"]
    missing_requirement_rows = [
        item
        for item in payload["requirement_import_results"]
        if item["requirement_status"] == "missing_input_file"
    ]
    assert len(missing_requirement_rows) == 1
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_late_file_failure_reports_explicit_partial_persistence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    _write_csv(first, [_row()])
    _write_csv(
        second,
        [
            _row(
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
            )
        ],
    )
    requirements = [
        _requirement(
            expected_candle_count=1,
            requested_end_at="2026-01-01T00:15:00Z",
            window_label="first",
        ),
        _requirement(
            requested_start_at="2026-01-01T00:15:00Z",
            requested_end_at="2026-01-01T00:30:00Z",
            expected_candle_count=1,
            window_label="second",
        ),
    ]
    original_import = (
        candle_bundle_import_service.import_strategy_validation_candles_from_path
    )
    calls: list[str] = []

    def fail_second_file(*args, **kwargs):
        calls.append(str(args[0]))
        if len(calls) == 2:
            raise RuntimeError("forced second file import failure")
        return original_import(*args, **kwargs)

    monkeypatch.setattr(
        candle_bundle_import_service,
        "import_strategy_validation_candles_from_path",
        fail_second_file,
    )

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        input_paths=(first, second),
        requirements=requirements,
        input_requirement_map={str(first): 0, str(second): 1},
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is True
    assert payload["import_completed"] is False
    assert payload["bundle_import_failure_policy"] == "explicit_partial_with_resume"
    assert payload["bundle_import_final_status"] == "partial_import"
    assert payload["partial_persistence_occurred"] is True
    assert payload["files_imported"] == 1
    assert payload["files_blocked"] == 1
    assert len(payload["imported_requirement_ids"]) == 1
    assert len(payload["failed_requirement_ids"]) == 1
    assert "canonical_candle_bundle_partial_persistence" in payload["reason_codes"]
    failed_files = [
        item
        for item in payload["file_import_results"]
        if item["file_status"] == "failed"
    ]
    assert len(failed_files) == 1
    assert failed_files[0]["input_path"] == str(second)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 1
    _assert_no_live_artifacts(session_factory)


def test_guarded_import_failed_preflight_remains_all_or_nothing(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _guarded_import(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(),
            _row(
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
                high="90",
            ),
            _row(
                open_time="2026-01-01T00:30:00Z",
                close_time="2026-01-01T00:45:00Z",
            ),
        ],
    )
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)

    assert payload["import_attempted"] is False
    assert "candle_import_invalid_ohlcv" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)
