from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.domain.enums import Environment, Timeframe
from db.models import CandleModel
from services.strategy_validation import (
    MoneyFlowBacktestService,
    import_strategy_validation_candles_from_path,
    money_flow_evidence_review_to_dict,
    review_money_flow_evidence,
    strategy_validation_candle_import_result_to_dict,
)
from test_sv10_strategy_validation import build_settings, build_test_session_factory, seed_symbol
from test_sv15_historical_data_readiness import _assert_no_live_artifacts
from test_sv151_candle_import_integrity import _valid_row, _write_csv
from test_sv19_evidence_status import _seed_current_alembic_version, _seeded_campaign_config_path


def _candle_count(session_factory) -> int:
    with session_factory() as session:
        return int(session.scalar(select(func.count()).select_from(CandleModel)) or 0)


def test_maintenance_database_target_blocks_evidence_generation_even_with_current_schema_and_candles(
    tmp_path: Path,
) -> None:
    settings = build_settings(
        DB_HOST="127.0.0.1",
        DB_PORT=54322,
        DB_NAME="postgres",
        DB_USER="postgres",
        DB_PASSWORD="postgres",
    )
    session_factory = build_test_session_factory()
    config_path = _seeded_campaign_config_path(
        tmp_path,
        session_factory,
        name="sv1_9_1_ambiguous_db_campaign",
    )
    _seed_current_alembic_version(session_factory)
    service = MoneyFlowBacktestService(settings, session_factory=session_factory)

    review = review_money_flow_evidence(
        (config_path,),
        service=service,
        output_dir=tmp_path,
        generate_evidence_packs=True,
        run_timestamp=datetime(2026, 5, 3, 22, 10, tzinfo=UTC),
        generated_at=datetime(2026, 5, 3, 22, 10, tzinfo=UTC),
    )
    payload = money_flow_evidence_review_to_dict(review)
    database_status = payload["database_status"]
    campaign = payload["campaign_results"][0]

    assert database_status["database_name"] == "postgres"
    assert database_status["database_target_role"] == (
        "maintenance_database_name_requires_operator_confirmation"
    )
    assert database_status["intended_strategy_validation_database"] is False
    assert database_status["schema_status"] == "migrated_schema_ready"
    assert database_status["schema_ready_for_evidence_generation"] is True
    assert database_status["database_target_ready_for_evidence_generation"] is False
    assert "maintenance_database_target_requires_confirmation" in database_status[
        "database_target_blocking_reason_codes"
    ]
    assert "strategy_validation_db_target_ambiguous" in database_status[
        "database_target_blocking_reason_codes"
    ]
    assert "evidence_generation_blocked_by_db_target_truth" in database_status[
        "database_target_blocking_reason_codes"
    ]
    assert payload["generated_campaign_count"] == 0
    assert payload["paper_readiness_review_status"] == "insufficient_data"
    assert campaign["evidence_pack_generated"] is False
    assert "strategy_validation_db_target_not_intended" in campaign[
        "blocked_or_gap_reason_codes"
    ]
    assert "evidence_generation_blocked_by_db_target_truth" in campaign[
        "blocked_or_gap_reason_codes"
    ]
    assert not (tmp_path / "sv1_9_1_ambiguous_db_campaign").exists()

    _assert_no_live_artifacts(session_factory)


def test_candle_import_rejects_naive_timestamps_by_default(tmp_path: Path) -> None:
    session_factory = build_test_session_factory()
    _instrument_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "naive_timestamps.csv"
    _write_csv(
        csv_path,
        [
            _valid_row(
                instrument_key,
                open_time="2026-01-01T00:00:00",
                close_time="2026-01-01T00:15:00",
            )
        ],
    )

    with pytest.raises(ValueError, match="candle_import_naive_timestamp"):
        import_strategy_validation_candles_from_path(
            csv_path,
            environment=Environment.TESTNET,
            venue="hyperliquid",
            timeframe=Timeframe.M15,
            source_label="sv191_naive_fixture",
            session_factory=session_factory,
        )

    assert _candle_count(session_factory) == 0
    _assert_no_live_artifacts(session_factory)


def test_candle_import_naive_utc_override_records_provenance_and_timestamp_assumption(
    tmp_path: Path,
) -> None:
    session_factory = build_test_session_factory()
    _instrument_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    csv_path = tmp_path / "naive_override.csv"
    _write_csv(
        csv_path,
        [
            _valid_row(
                instrument_key,
                open_time="2026-01-01T00:00:00",
                close_time="2026-01-01T00:15:00",
            )
        ],
    )

    result = import_strategy_validation_candles_from_path(
        csv_path,
        environment=Environment.TESTNET,
        venue="hyperliquid",
        timeframe=Timeframe.M15,
        source_label="sv191_naive_override_fixture",
        assume_naive_utc=True,
        session_factory=session_factory,
    )
    payload = strategy_validation_candle_import_result_to_dict(result)

    assert payload["inserted_count"] == 1
    assert payload["row_count"] == 1
    assert payload["rows_seen"] == 1
    assert payload["rejected_count"] == 0
    assert payload["source_label"] == "sv191_naive_override_fixture"
    assert payload["source_path"] == str(csv_path)
    assert payload["source_file_name"] == "naive_override.csv"
    assert len(payload["source_file_sha256"]) == 64
    assert payload["environment"] == "testnet"
    assert payload["venue"] == "hyperliquid"
    assert payload["timeframe"] == "15m"
    assert payload["timestamp_assumption"] == "assume_naive_utc"
    assert payload["naive_timestamp_override_used"] is True
    assert "naive_timestamp_override_used" in payload["warning_reason_codes"]
    assert "candle_import_naive_timestamp_assumed_utc" in payload["warning_reason_codes"]
    assert "timezone_required_for_candle_import_overridden" in payload[
        "warning_reason_codes"
    ]
    assert _candle_count(session_factory) == 1

    _assert_no_live_artifacts(session_factory)
