from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import Environment, Timeframe
from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation import (
    EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT,
    MoneyFlowBacktestService,
    evaluate_strategy_validation_import_readiness,
    strategy_validation_import_readiness_to_dict,
    strategy_validation_import_readiness_to_markdown,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory
from test_sv110_evidence_db_readiness import _assert_no_live_artifacts
from test_sv1111_market_identity_preflight_hardening import (
    _manifest_copy,
    _requirement,
    _row,
    _seed_verified_identity,
    _write_csv,
)
from test_sv19_evidence_status import _seed_current_alembic_version


def _service(session_factory) -> MoneyFlowBacktestService:
    return MoneyFlowBacktestService(build_settings(), session_factory=session_factory)


def test_sv1122_missing_operator_verification_produces_checklist_not_seed(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    result = evaluate_strategy_validation_import_readiness(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=False,
    )
    payload = strategy_validation_import_readiness_to_dict(result)

    assert payload["market_identity_seed_attempted"] is True
    assert payload["market_identity_seeded"] is False
    assert payload["identity_seed_status"] == "blocked_operator_verification_required"
    assert "market_identity_operator_verification_required" in payload["reason_codes"]
    assert len(payload["identity_verification_checklist"]) == 3
    assert all(not item["seed_allowed"] for item in payload["identity_verification_checklist"])
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(InstrumentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SymbolModel)) == 0
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1122_verified_seed_remains_non_trading_and_non_strategy(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    result = evaluate_strategy_validation_import_readiness(
        service=_service(session_factory),
        session_factory=session_factory,
        manifest_path=_manifest_copy(tmp_path),
        seed_identity=True,
        operator_verified=True,
        verified_by="test_operator",
    )
    payload = strategy_validation_import_readiness_to_dict(result)

    assert payload["market_identity_seeded"] is True
    assert payload["identity_seed_status"] == "seeded"
    assert payload["identity_seed_summary"]["symbols_inserted"] == 3
    assert all(
        item["operator_verified_market_identity_status"] == "ready"
        for item in payload["operator_verified_market_identity_requirements"]
    )
    with session_factory() as session:
        symbols = session.scalars(select(SymbolModel)).all()
        assert {symbol.symbol for symbol in symbols} == {"BTC", "ETH", "SOL"}
        for symbol in symbols:
            assert symbol.is_strategy_eligible is False
            assert symbol.is_trading_eligible is False
            assert symbol.raw_metadata["research_only_market_identity_seed"] is True
            assert symbol.raw_metadata["operator_verified"] is True
            assert symbol.raw_metadata["verified_by"] == "test_operator"
            assert symbol.raw_metadata["source"] == "manual_offline_manifest"
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1122_canonical_18_file_requirement_list_is_reported() -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    result = evaluate_strategy_validation_import_readiness(
        service=_service(session_factory),
        session_factory=session_factory,
    )
    payload = strategy_validation_import_readiness_to_dict(result)
    markdown = strategy_validation_import_readiness_to_markdown(result)

    assert payload["actual_canonical_requirement_count"] == (
        EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT
    )
    assert payload["canonical_requirement_count_matches_expected"] is True
    assert len(payload["canonical_candle_file_requirements"]) == 18
    assert "(start_at, end_at]" in markdown
    assert "timezone-explicit" in markdown
    assert "timezone-naive timestamps are rejected" in markdown
    assert payload["evidence_packs_generated"] is False
    assert payload["candles_imported"] is False
    btc_15m = next(
        item
        for item in payload["canonical_candle_file_requirements"]
        if item["symbol"] == "BTC"
        and item["timeframe"] == "15m"
        and item["requested_start_at"] == "2026-01-01T00:00:00+00:00"
    )
    assert btc_15m["expected_candle_count"] == 1344
    assert btc_15m["window_convention"] == "(start_at, end_at]"
    assert btc_15m["required_columns"] == [
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
    assert btc_15m["suggested_filename"].endswith(".csv")
    _assert_no_live_artifacts(session_factory)


def test_sv1122_preflight_only_path_writes_no_candles(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)
    _seed_verified_identity(tmp_path, session_factory=session_factory)
    csv_path = tmp_path / "btc_15m.csv"
    requirement = _requirement(
        expected_candle_count=1,
        requested_end_at="2026-01-01T00:15:00Z",
    )
    _write_csv(csv_path, [_row()])

    result = evaluate_strategy_validation_import_readiness(
        service=_service(session_factory),
        session_factory=session_factory,
        input_paths=(csv_path,),
        input_requirement_map={str(csv_path): requirement},
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
    )
    payload = strategy_validation_import_readiness_to_dict(result)

    assert payload["preflight_run"] is True
    assert payload["preflight_summary"]["ready"] is True
    assert payload["preflight_summary"]["requirement_aware_results"][0][
        "ready_for_import"
    ] is True
    assert payload["ready_for_sv1123_guarded_import"] is False
    assert "canonical_candle_requirement_preflight_incomplete" in payload["reason_codes"]
    assert payload["candles_imported"] is False
    assert payload["evidence_packs_generated"] is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CandleModel)) == 0
    _assert_no_live_artifacts(session_factory)


def test_sv1122_readiness_flags_create_no_live_or_exchange_artifacts() -> None:
    session_factory = build_test_session_factory()
    _seed_current_alembic_version(session_factory)

    payload = strategy_validation_import_readiness_to_dict(
        evaluate_strategy_validation_import_readiness(
            service=_service(session_factory),
            session_factory=session_factory,
        )
    )

    assert payload["creates_live_artifacts"] is False
    assert payload["calls_exchange_adapters"] is False
    assert payload["calls_private_exchange_endpoints"] is False
    assert payload["calls_exchange_order_endpoints"] is False
    assert payload["candles_imported"] is False
    assert payload["evidence_packs_generated"] is False
    assert "best strategy" not in json.dumps(payload).lower()
    assert "recommended strategy" not in json.dumps(payload).lower()
    assert "paper trading approved" not in json.dumps(payload).lower()
    _assert_no_live_artifacts(session_factory)
