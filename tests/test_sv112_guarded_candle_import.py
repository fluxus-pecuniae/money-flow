from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

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
):
    csv_path = tmp_path / "btc_15m.csv"
    requirement_path = tmp_path / "requirements.json"
    if input_paths is None:
        _write_csv(csv_path, rows if rows is not None else _three_rows())
        input_paths = (csv_path,)
    _write_json(requirement_path, [requirement or _requirement()])
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
