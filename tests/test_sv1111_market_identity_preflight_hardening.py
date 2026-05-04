from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import Environment, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    preflight_strategy_validation_candle_import,
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_candle_import_preflight_result_to_dict,
    strategy_validation_market_identity_seed_result_to_dict,
)
from test_sv10_strategy_validation import build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv111_market_identity_preflight import EXAMPLE_MANIFEST, _manifest_copy


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


def _row(**overrides: object) -> dict[str, object]:
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


def _requirement(**overrides: object) -> dict[str, object]:
    requirement: dict[str, object] = {
        "symbol": "BTC",
        "instrument_key": "perpetual:linear:BTC:USDC:USDC",
        "timeframe": "15m",
        "requested_start_at": "2026-01-01T00:00:00Z",
        "requested_end_at": "2026-01-01T00:45:00Z",
        "expected_candle_count": 3,
        "window_label": "synthetic_btc_15m",
    }
    requirement.update(overrides)
    return requirement


def _write_requirement(path: Path, requirement: dict[str, object]) -> None:
    path.write_text(json.dumps(requirement, indent=2, sort_keys=True), encoding="utf-8")


def _seed_verified_identity(tmp_path: Path, *, session_factory) -> None:
    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        operator_verified=True,
        verified_by="test_operator",
        session_factory=session_factory,
    )
    assert result.conflicts == ()


def _run_requirement_preflight(
    *,
    tmp_path: Path,
    session_factory,
    rows: list[dict[str, object]],
    requirement: dict[str, object] | None = None,
):
    csv_path = tmp_path / "candles.csv"
    requirement_path = tmp_path / "requirement.json"
    _write_csv(csv_path, rows)
    _write_requirement(requirement_path, requirement or _requirement())
    return preflight_strategy_validation_candle_import(
        input_paths=(csv_path,),
        requirement_json_paths=(requirement_path,),
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )


def test_non_dry_run_example_manifest_without_operator_verification_blocks(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()

    result = seed_strategy_validation_market_identity_from_manifest(
        EXAMPLE_MANIFEST,
        session_factory=session_factory,
    )
    payload = strategy_validation_market_identity_seed_result_to_dict(result)

    assert payload["operator_verified"] is False
    assert payload["conflicts"][0]["reason_code"] == (
        "market_identity_operator_verification_required"
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_dry_run_example_manifest_still_works_without_operator_verification(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()

    result = seed_strategy_validation_market_identity_from_manifest(
        EXAMPLE_MANIFEST,
        dry_run=True,
        session_factory=session_factory,
    )

    assert result.conflicts == ()
    assert result.instruments_inserted == 3
    assert result.symbols_inserted == 3
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_verify_only_does_not_require_operator_verification(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()

    missing = seed_strategy_validation_market_identity_from_manifest(
        EXAMPLE_MANIFEST,
        verify_only=True,
        session_factory=session_factory,
    )
    assert missing.conflicts

    _seed_verified_identity(tmp_path, session_factory=session_factory)
    ready = seed_strategy_validation_market_identity_from_manifest(
        EXAMPLE_MANIFEST,
        verify_only=True,
        session_factory=session_factory,
    )

    assert ready.conflicts == ()
    _assert_no_live_artifacts(session_factory)


def test_operator_verified_seed_writes_verification_metadata_without_eligibility_flip(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()

    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        operator_verified=True,
        verified_by="test_operator",
        session_factory=session_factory,
    )

    assert result.conflicts == ()
    with session_factory() as session:
        btc = session.scalar(select(SymbolModel).where(SymbolModel.symbol == "BTC"))
        assert btc is not None
        assert btc.raw_metadata["operator_verified"] is True
        assert btc.raw_metadata["verified_by"] == "test_operator"
        assert btc.raw_metadata["verified_at"]
        assert btc.raw_metadata["sv_phase"] == "SV1.11.1"
        assert btc.raw_metadata["research_only_market_identity_seed"] is True
        assert btc.raw_metadata["source"] == "manual_offline_manifest"
        assert btc.is_strategy_eligible is False
        assert btc.is_trading_eligible is False
    _assert_no_live_artifacts(session_factory)


def test_operator_verified_seed_requires_verified_by(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()

    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        operator_verified=True,
        session_factory=session_factory,
    )

    reason_codes = {conflict["reason_code"] for conflict in result.conflicts}
    assert "market_identity_verified_by_required" in reason_codes
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_fails_valid_file_outside_required_window(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(
                open_time="2026-01-01T01:00:00Z",
                close_time="2026-01-01T01:15:00Z",
            )
        ],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)
    requirement_result = payload["requirement_aware_results"][0]

    assert payload["ready"] is False
    assert requirement_result["row_level_ready"] is True
    assert requirement_result["identity_ready"] is True
    assert requirement_result["requirement_coverage_ready"] is False
    assert requirement_result["ready_for_import"] is False
    assert "requirement_close_time_outside_window" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_fails_duplicate_close_slots(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        requirement=_requirement(
            requested_end_at="2026-01-01T00:30:00Z",
            expected_candle_count=2,
        ),
        rows=[
            _row(),
            _row(open="101", high="102", low="100", close="101.5"),
        ],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "requirement_duplicate_close_time_slots" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_fails_missing_close_slots(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        requirement=_requirement(
            requested_end_at="2026-01-01T00:30:00Z",
            expected_candle_count=2,
        ),
        rows=[_row()],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "requirement_missing_close_time_slots" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_fails_wrong_symbol(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(
                symbol="ETH",
                instrument_key="perpetual:linear:ETH:USDC:USDC",
            )
        ],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "requirement_symbol_mismatch" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_fails_wrong_instrument_key(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[_row(instrument_key="perpetual:linear:ETH:USDC:USDC")],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert (
        "requirement_instrument_key_mismatch" in payload["reason_codes"]
        or "unknown_symbol_mapping" in payload["reason_codes"]
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_passes_complete_synthetic_requirement_file(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)

    result = _run_requirement_preflight(
        tmp_path=tmp_path,
        session_factory=session_factory,
        rows=[
            _row(),
            _row(
                open_time="2026-01-01T00:15:00Z",
                close_time="2026-01-01T00:30:00Z",
            ),
            _row(
                open_time="2026-01-01T00:30:00Z",
                close_time="2026-01-01T00:45:00Z",
            ),
        ],
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)
    requirement_result = payload["requirement_aware_results"][0]

    assert payload["ready"] is True
    assert requirement_result["row_level_ready"] is True
    assert requirement_result["identity_ready"] is True
    assert requirement_result["requirement_coverage_ready"] is True
    assert requirement_result["ready_for_import"] is True
    assert requirement_result["actual_candle_count"] == 3
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)
