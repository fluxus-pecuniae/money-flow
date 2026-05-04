from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.domain.enums import Environment, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    preflight_strategy_validation_candle_import,
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_candle_import_preflight_result_to_dict,
)
from test_sv10_strategy_validation import build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv111_market_identity_preflight import _manifest_copy
from test_sv1111_market_identity_preflight_hardening import (
    _requirement,
    _row,
    _seed_verified_identity,
    _write_csv,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _manifest_with_symbol_field(
    tmp_path: Path,
    *,
    field: str,
    value: bool,
) -> Path:
    def mutate(payload: dict[str, object]) -> None:
        markets = payload["markets"]
        assert isinstance(markets, list)
        edited = deepcopy(markets[0])
        edited["symbol"][field] = value
        markets[0] = edited

    return _manifest_copy(tmp_path, mutate=mutate)


def _write_requirement_file(path: Path, requirements: list[dict[str, object]]) -> None:
    _write_json(path, requirements)


def _run_mapped_preflight(
    *,
    input_paths: tuple[Path, ...],
    requirement_path: Path,
    input_requirement_map: dict[str, object] | None,
    session_factory,
):
    return preflight_strategy_validation_candle_import(
        input_paths=input_paths,
        requirement_json_paths=(requirement_path,),
        input_requirement_map=input_requirement_map,
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        session_factory=session_factory,
    )


def test_market_identity_seed_rejects_trading_eligible_true_without_writes(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    manifest = _manifest_with_symbol_field(
        tmp_path,
        field="is_trading_eligible",
        value=True,
    )

    with pytest.raises(ValueError) as exc_info:
        seed_strategy_validation_market_identity_from_manifest(
            manifest,
            operator_verified=True,
            verified_by="test_operator",
            session_factory=session_factory,
        )

    assert "strategy_validation_seed_cannot_mark_symbol_trading_eligible" in str(
        exc_info.value
    )
    assert "research_market_identity_seed_must_remain_non_trading" in str(
        exc_info.value
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_rejects_strategy_eligible_true_without_writes(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    manifest = _manifest_with_symbol_field(
        tmp_path,
        field="is_strategy_eligible",
        value=True,
    )

    with pytest.raises(ValueError) as exc_info:
        seed_strategy_validation_market_identity_from_manifest(
            manifest,
            operator_verified=True,
            verified_by="test_operator",
            session_factory=session_factory,
        )

    assert "strategy_validation_seed_cannot_mark_symbol_strategy_eligible" in str(
        exc_info.value
    )
    assert "research_market_identity_seed_must_remain_non_trading" in str(
        exc_info.value
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_allows_explicit_false_eligibility_when_verified(
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
        assert btc.is_strategy_eligible is False
        assert btc.is_trading_eligible is False
        assert btc.raw_metadata["research_only_market_identity_seed"] is True
        assert btc.raw_metadata["source"] == "manual_offline_manifest"
        assert btc.raw_metadata["operator_verified"] is True
        assert btc.raw_metadata["verified_by"] == "test_operator"
        assert btc.raw_metadata["verified_at"]
    _assert_no_live_artifacts(session_factory)


def test_market_identity_seed_dry_run_reports_invalid_eligibility_truth(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    manifest = _manifest_with_symbol_field(
        tmp_path,
        field="is_trading_eligible",
        value=True,
    )

    with pytest.raises(ValueError) as exc_info:
        seed_strategy_validation_market_identity_from_manifest(
            manifest,
            dry_run=True,
            session_factory=session_factory,
        )

    assert "strategy_validation_seed_cannot_mark_symbol_trading_eligible" in str(
        exc_info.value
    )
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_market_identity_verify_only_remains_non_writing(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()

    result = seed_strategy_validation_market_identity_from_manifest(
        _manifest_copy(tmp_path),
        verify_only=True,
        session_factory=session_factory,
    )

    assert result.conflicts
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_blocks_unmapped_input_file(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "btc_1.csv"
    second = tmp_path / "btc_2.csv"
    requirements_path = tmp_path / "requirements.json"
    _write_csv(first, [_row()])
    _write_csv(second, [_row(open_time="2026-01-01T00:15:00Z", close_time="2026-01-01T00:30:00Z")])
    _write_requirement_file(requirements_path, [_requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z")])

    result = _run_mapped_preflight(
        input_paths=(first, second),
        requirement_path=requirements_path,
        input_requirement_map={str(first): 0},
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "input_file_missing_requirement_mapping" in payload["reason_codes"]
    assert "requirement_mapping_incomplete" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_blocks_unmapped_requirement(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "btc.csv"
    requirements_path = tmp_path / "requirements.json"
    _write_csv(first, [_row()])
    _write_requirement_file(
        requirements_path,
        [
            _requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z"),
            _requirement(
                symbol="ETH",
                instrument_key="perpetual:linear:ETH:USDC:USDC",
                expected_candle_count=1,
                requested_end_at="2026-01-01T00:15:00Z",
                window_label="synthetic_eth_15m",
            ),
        ],
    )

    result = _run_mapped_preflight(
        input_paths=(first,),
        requirement_path=requirements_path,
        input_requirement_map={str(first): 0},
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "requirement_missing_input_file" in payload["reason_codes"]
    assert "requirement_mapping_incomplete" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_blocks_duplicate_requirement_mapping(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    first = tmp_path / "btc_1.csv"
    second = tmp_path / "btc_2.csv"
    requirements_path = tmp_path / "requirements.json"
    _write_csv(first, [_row()])
    _write_csv(second, [_row(open_time="2026-01-01T00:15:00Z", close_time="2026-01-01T00:30:00Z")])
    _write_requirement_file(requirements_path, [_requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z")])

    result = _run_mapped_preflight(
        input_paths=(first, second),
        requirement_path=requirements_path,
        input_requirement_map={str(first): 0, str(second): 0},
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is False
    assert "requirement_mapped_to_multiple_input_files" in payload["reason_codes"]
    assert "requirement_mapping_not_one_to_one" in payload["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_requirement_aware_preflight_complete_one_to_one_mapping_can_pass(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    btc = tmp_path / "btc.csv"
    eth = tmp_path / "eth.csv"
    requirements_path = tmp_path / "requirements.json"
    _write_csv(btc, [_row()])
    _write_csv(
        eth,
        [
            _row(
                symbol="ETH",
                instrument_key="perpetual:linear:ETH:USDC:USDC",
            )
        ],
    )
    _write_requirement_file(
        requirements_path,
        [
            _requirement(expected_candle_count=1, requested_end_at="2026-01-01T00:15:00Z"),
            _requirement(
                symbol="ETH",
                instrument_key="perpetual:linear:ETH:USDC:USDC",
                expected_candle_count=1,
                requested_end_at="2026-01-01T00:15:00Z",
                window_label="synthetic_eth_15m",
            ),
        ],
    )

    result = _run_mapped_preflight(
        input_paths=(btc, eth),
        requirement_path=requirements_path,
        input_requirement_map={str(btc): 0, str(eth): 1},
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is True
    assert len(payload["requirement_aware_results"]) == 2
    assert all(item["ready_for_import"] for item in payload["requirement_aware_results"])
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_review_json_with_identity_and_candle_requirements_uses_candle_requirements(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    review_path = tmp_path / "review.json"
    _write_json(
        review_path,
        {
            "canonical_market_identity_requirements": [
                {
                    "symbol": "SOL",
                    "venue": "hyperliquid",
                    "instrument_key": "perpetual:linear:SOL:USDC:USDC",
                }
            ],
            "canonical_candle_import_requirements": [
                {
                    **_requirement(
                        symbol="BTC",
                        instrument_key="perpetual:linear:BTC:USDC:USDC",
                        expected_candle_count=1,
                        requested_end_at="2026-01-01T00:15:00Z",
                    ),
                    "actual_candle_count": 0,
                    "missing_candle_count": 1,
                }
            ],
        },
    )

    result = preflight_strategy_validation_candle_import(
        requirements_from_review_json=review_path,
        environment=Environment.TESTNET.value,
        venue="hyperliquid",
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)

    assert payload["ready"] is True
    assert len(payload["requirement_results"]) == 1
    requirement = payload["requirement_results"][0]
    assert requirement["symbol"] == "BTC"
    assert requirement["requirement_kind"] == "canonical_candle_import_requirements"
    _assert_no_live_artifacts(session_factory)
