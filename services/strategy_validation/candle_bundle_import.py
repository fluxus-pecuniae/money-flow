"""Guarded canonical candle bundle import for Strategy Validation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import select

from core.domain.enums import Environment, Timeframe
from db.models import InstrumentModel, SymbolModel
from services.strategy_validation.candles import import_strategy_validation_candles_from_path
from services.strategy_validation.evidence_review import (
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_database_status_to_dict,
)
from services.strategy_validation.market_identity import (
    CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
    CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
    CANONICAL_MARKET_IDENTITY_QUOTE_ASSET,
    CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET,
    preflight_strategy_validation_candle_import,
    strategy_validation_candle_import_preflight_result_to_dict,
)
from services.strategy_validation.service import MoneyFlowBacktestService


@dataclass(frozen=True, slots=True)
class StrategyValidationCanonicalCandleBundleImportResult:
    environment: str
    venue: str
    ready_for_import: bool
    import_attempted: bool
    import_completed: bool
    database_status: dict[str, Any]
    preflight: dict[str, Any]
    operator_verified_market_identity_requirements: tuple[dict[str, Any], ...]
    file_import_results: tuple[dict[str, Any], ...]
    input_files_seen: int
    files_imported: int
    files_blocked: int
    rows_inserted: int
    rows_updated: int
    rows_unchanged: int
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_packs_generated: bool = False
    creates_live_artifacts: bool = False
    calls_exchange_adapters: bool = False
    calls_private_exchange_endpoints: bool = False
    calls_exchange_order_endpoints: bool = False


def guarded_import_strategy_validation_candle_bundle(
    *,
    input_paths: Sequence[str | Path],
    environment: Environment,
    venue: str,
    requirements_from_review_json: str | Path | None = None,
    requirement_json_paths: Sequence[str | Path] = (),
    input_requirement_map: dict[str, Any] | None = None,
    input_requirement_map_path: str | Path | None = None,
    timeframe: Timeframe | None = None,
    file_format: str = "auto",
    source_label_prefix: str | None = None,
    service: MoneyFlowBacktestService | None = None,
    session_factory: Any | None = None,
) -> StrategyValidationCanonicalCandleBundleImportResult:
    """Import canonical candle files only after all SV1.12 guardrails pass."""

    validation_service = service or MoneyFlowBacktestService()
    effective_session_factory = session_factory or validation_service._session_factory
    database_status = inspect_strategy_validation_database_status(validation_service)
    database_payload = money_flow_evidence_review_database_status_to_dict(database_status)
    reason_codes: set[str] = set()
    warnings: set[str] = set()

    reason_codes.update(_database_import_blocking_reason_codes(database_payload))

    requirement_paths = tuple(Path(path) for path in requirement_json_paths)
    if requirements_from_review_json is not None:
        requirement_paths = (*requirement_paths, Path(requirements_from_review_json))

    preflight = preflight_strategy_validation_candle_import(
        input_paths=tuple(Path(path) for path in input_paths),
        requirements_from_review_json=(
            Path(requirements_from_review_json)
            if requirements_from_review_json is not None
            else None
        ),
        requirement_json_paths=requirement_paths,
        input_requirement_map=input_requirement_map,
        input_requirement_map_path=(
            Path(input_requirement_map_path)
            if input_requirement_map_path is not None
            else None
        ),
        environment=environment.value,
        venue=venue,
        timeframe=timeframe,
        file_format=file_format,
        session_factory=effective_session_factory,
    )
    preflight_payload = strategy_validation_candle_import_preflight_result_to_dict(preflight)
    if not preflight_payload["requirement_aware_results"]:
        reason_codes.add("canonical_candle_import_requires_requirement_aware_preflight")
    if not preflight_payload["ready"]:
        reason_codes.add("canonical_candle_import_preflight_not_ready")
        reason_codes.update(preflight_payload["reason_codes"])
    warnings.update(preflight_payload["warnings"])

    identity_requirements = _operator_verified_market_identity_requirements(
        preflight_payload["requirement_aware_results"],
        venue=venue,
        session_factory=effective_session_factory,
    )
    for requirement in identity_requirements:
        if requirement["operator_verified_market_identity_status"] != "ready":
            reason_codes.add("operator_verified_market_identity_not_ready")
            reason_codes.update(requirement["reason_codes"])

    ready_for_import = not reason_codes
    file_import_results: list[dict[str, Any]] = []
    rows_inserted = 0
    rows_updated = 0
    rows_unchanged = 0

    if ready_for_import:
        for requirement_result in preflight_payload["requirement_aware_results"]:
            input_path = Path(requirement_result["input_path"])
            source_label = _source_label_for_input(
                source_label_prefix=source_label_prefix,
                input_path=input_path,
                requirement_result=requirement_result,
            )
            try:
                import_result = import_strategy_validation_candles_from_path(
                    input_path,
                    environment=environment,
                    venue=venue,
                    timeframe=Timeframe(requirement_result["timeframe"]),
                    source_label=source_label,
                    file_format=file_format,
                    assume_naive_utc=False,
                    session_factory=effective_session_factory,
                )
                import_payload = import_result_to_dict(import_result)
                rows_inserted += int(import_payload["inserted_count"])
                rows_updated += int(import_payload["updated_count"])
                rows_unchanged += int(import_payload["unchanged_count"])
                file_import_results.append(
                    {
                        "input_path": str(input_path),
                        "requirement_identifier": requirement_result[
                            "requirement_identifier"
                        ],
                        "symbol": requirement_result["symbol"],
                        "timeframe": requirement_result["timeframe"],
                        "import_attempted": True,
                        "import_succeeded": True,
                        "ready_for_import": True,
                        "source_label": source_label,
                        "import_result": import_payload,
                        "reason_codes": (),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - return explicit file status.
                reason_codes.add("canonical_candle_file_import_failed")
                file_import_results.append(
                    {
                        "input_path": str(input_path),
                        "requirement_identifier": requirement_result[
                            "requirement_identifier"
                        ],
                        "symbol": requirement_result["symbol"],
                        "timeframe": requirement_result["timeframe"],
                        "import_attempted": True,
                        "import_succeeded": False,
                        "ready_for_import": True,
                        "source_label": source_label,
                        "error_message": str(exc).splitlines()[0],
                        "reason_codes": ("canonical_candle_file_import_failed",),
                    }
                )
                break
    else:
        for requirement_result in preflight_payload["requirement_aware_results"]:
            file_import_results.append(
                {
                    "input_path": requirement_result["input_path"],
                    "requirement_identifier": requirement_result[
                        "requirement_identifier"
                    ],
                    "symbol": requirement_result["symbol"],
                    "timeframe": requirement_result["timeframe"],
                    "import_attempted": False,
                    "import_succeeded": False,
                    "ready_for_import": False,
                    "source_label": None,
                    "reason_codes": tuple(sorted(reason_codes)),
                }
            )

    import_attempted = any(item["import_attempted"] for item in file_import_results)
    import_completed = (
        ready_for_import
        and bool(file_import_results)
        and all(item["import_succeeded"] for item in file_import_results)
    )
    if not import_completed and import_attempted:
        reason_codes.add("canonical_candle_bundle_import_incomplete")

    return StrategyValidationCanonicalCandleBundleImportResult(
        environment=environment.value,
        venue=venue,
        ready_for_import=ready_for_import,
        import_attempted=import_attempted,
        import_completed=import_completed,
        database_status=database_payload,
        preflight=preflight_payload,
        operator_verified_market_identity_requirements=tuple(
            _json_ready(item) for item in identity_requirements
        ),
        file_import_results=tuple(_json_ready(item) for item in file_import_results),
        input_files_seen=len(input_paths),
        files_imported=sum(1 for item in file_import_results if item["import_succeeded"]),
        files_blocked=sum(1 for item in file_import_results if not item["import_succeeded"]),
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        rows_unchanged=rows_unchanged,
        reason_codes=tuple(sorted(reason_codes)),
        warnings=tuple(sorted(warnings)),
    )


def strategy_validation_canonical_candle_bundle_import_result_to_dict(
    result: StrategyValidationCanonicalCandleBundleImportResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_canonical_candle_bundle_import_result_to_json(
    result: StrategyValidationCanonicalCandleBundleImportResult,
) -> str:
    return json.dumps(
        strategy_validation_canonical_candle_bundle_import_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_canonical_candle_bundle_import_result_to_markdown(
    result: StrategyValidationCanonicalCandleBundleImportResult,
) -> str:
    payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(result)
    db_status = payload["database_status"]
    lines = [
        "# Strategy Validation Canonical Candle Import Status",
        "",
        "This guarded import is research-only. It imports historical candles only after "
        "DB, schema, operator-verified non-trading identity, and requirement-aware "
        "preflight gates pass. It generates no evidence packs, calls no exchanges, "
        "routes nothing, and creates no paper/live artifacts.",
        "",
        "## Summary",
        "",
        f"- Environment: `{payload['environment']}`",
        f"- Venue: `{payload['venue']}`",
        f"- Ready for import: `{payload['ready_for_import']}`",
        f"- Import attempted: `{payload['import_attempted']}`",
        f"- Import completed: `{payload['import_completed']}`",
        f"- Input files seen: `{payload['input_files_seen']}`",
        f"- Files imported: `{payload['files_imported']}`",
        f"- Files blocked: `{payload['files_blocked']}`",
        f"- Rows inserted: `{payload['rows_inserted']}`",
        f"- Rows updated: `{payload['rows_updated']}`",
        f"- Rows unchanged: `{payload['rows_unchanged']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        "",
        "## Database Gate",
        "",
        f"- Configured DB URL: `{db_status['configured_database_url']}`",
        f"- Target role: `{db_status['database_target_role']}`",
        f"- Intended strategy-validation DB: `{db_status['intended_strategy_validation_database']}`",
        f"- DB reachable: `{db_status['reachable']}`",
        f"- Schema status: `{db_status['schema_status']}`",
        f"- Migrations current: `{db_status['migrations_current']}`",
        f"- Required tables missing: `{db_status['required_schema_tables_missing']}`",
        f"- Target blocking reasons: `{db_status['database_target_blocking_reason_codes']}`",
        "",
        "## Operator-Verified Market Identity",
        "",
        "| symbol | instrument key | status | strategy eligible | trading eligible | verified by | reason codes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["operator_verified_market_identity_requirements"]:
        lines.append(
            "| "
            f"`{item['symbol']}` | "
            f"`{item['instrument_key']}` | "
            f"`{item['operator_verified_market_identity_status']}` | "
            f"`{item['is_strategy_eligible']}` | "
            f"`{item['is_trading_eligible']}` | "
            f"`{item['verified_by']}` | "
            f"`{item['reason_codes']}` |"
        )
    lines.extend(["", "## Preflight", ""])
    lines.extend(
        [
            f"- Preflight ready: `{payload['preflight']['ready']}`",
            f"- Preflight reason codes: `{payload['preflight']['reason_codes']}`",
            f"- Requirement-aware files: `{len(payload['preflight']['requirement_aware_results'])}`",
            "",
            "## File Import Results",
            "",
        ]
    )
    if payload["file_import_results"]:
        for item in payload["file_import_results"]:
            lines.extend(
                [
                    f"### `{item['input_path']}`",
                    "",
                    f"- Requirement identifier: `{item['requirement_identifier']}`",
                    f"- Symbol: `{item['symbol']}`",
                    f"- Timeframe: `{item['timeframe']}`",
                    f"- Import attempted: `{item['import_attempted']}`",
                    f"- Import succeeded: `{item['import_succeeded']}`",
                    f"- Source label: `{item['source_label']}`",
                    f"- Reason codes: `{item['reason_codes']}`",
                    "",
                ]
            )
    else:
        lines.append("- No files were imported or blocked because no requirement-aware files were supplied.")
        lines.append("")
    lines.extend(
        [
            "## Research Boundary",
            "",
            f"- Evidence packs generated: `{payload['evidence_packs_generated']}`",
            f"- Creates live artifacts: `{payload['creates_live_artifacts']}`",
            f"- Calls exchange adapters: `{payload['calls_exchange_adapters']}`",
            f"- Calls private exchange endpoints: `{payload['calls_private_exchange_endpoints']}`",
            f"- Calls exchange order endpoints: `{payload['calls_exchange_order_endpoints']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _database_import_blocking_reason_codes(database_payload: dict[str, Any]) -> set[str]:
    reason_codes: set[str] = set(database_payload["database_target_blocking_reason_codes"])
    if not database_payload["database_target_ready_for_evidence_generation"]:
        reason_codes.add("canonical_candle_import_blocked_by_db_target_truth")
    if not database_payload["reachable"]:
        reason_codes.add("database_unreachable")
    if database_payload["schema_status"] != "migrated_schema_ready":
        reason_codes.add("schema_not_ready_for_canonical_candle_import")
    if database_payload["migrations_current"] is not True:
        reason_codes.add("database_migrations_not_current")
    if database_payload["required_schema_tables_missing"]:
        reason_codes.add("required_strategy_validation_schema_tables_missing")
    for table_name in ("alembic_version", "candles", "instruments", "symbols"):
        if table_name == "alembic_version":
            if not database_payload["alembic_version_table_exists"]:
                reason_codes.add("alembic_version_missing")
        elif table_name in database_payload["required_schema_tables_missing"]:
            reason_codes.add(f"required_schema_table_missing_{table_name}")
    return reason_codes


def _operator_verified_market_identity_requirements(
    requirement_results: Sequence[dict[str, Any]],
    *,
    venue: str,
    session_factory: Any,
) -> tuple[dict[str, Any], ...]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for result in requirement_results:
        unique[(str(result["symbol"]), str(result["instrument_key"]))] = result
    rows: list[dict[str, Any]] = []
    with session_factory() as session:
        for (_symbol, _instrument_key), result in sorted(unique.items()):
            symbol = str(result["symbol"])
            instrument_key = str(result["instrument_key"])
            reason_codes: set[str] = set()
            instrument = session.scalar(
                select(InstrumentModel).where(
                    InstrumentModel.instrument_key == instrument_key
                )
            )
            symbol_model = None
            if instrument is None:
                reason_codes.add("missing_instrument")
            else:
                symbol_model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == venue,
                        SymbolModel.symbol == symbol,
                        SymbolModel.market_type == CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
                        SymbolModel.product_type == CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
                        SymbolModel.quote_asset == CANONICAL_MARKET_IDENTITY_QUOTE_ASSET,
                        SymbolModel.settlement_asset
                        == CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET,
                    )
                )
            if symbol_model is None:
                reason_codes.add("missing_symbol_mapping")
            elif instrument is not None and symbol_model.instrument_ref_id != instrument.id:
                reason_codes.add("market_identity_symbol_instrument_conflict")
            if symbol_model is not None:
                metadata = dict(symbol_model.raw_metadata or {})
                if symbol_model.is_strategy_eligible:
                    reason_codes.add("strategy_validation_identity_strategy_eligible")
                if symbol_model.is_trading_eligible:
                    reason_codes.add("strategy_validation_identity_trading_eligible")
                if metadata.get("research_only_market_identity_seed") is not True:
                    reason_codes.add("research_only_market_identity_seed_missing")
                if metadata.get("source") != "manual_offline_manifest":
                    reason_codes.add("manual_offline_manifest_source_missing")
                if metadata.get("operator_verified") is not True:
                    reason_codes.add("operator_verified_market_identity_missing")
                if not metadata.get("verified_by"):
                    reason_codes.add("operator_verified_market_identity_verified_by_missing")
                if not metadata.get("verified_at"):
                    reason_codes.add("operator_verified_market_identity_verified_at_missing")
                status = "ready" if not reason_codes else "operator_verification_missing"
                if (
                    "strategy_validation_identity_strategy_eligible" in reason_codes
                    or "strategy_validation_identity_trading_eligible" in reason_codes
                ):
                    status = "not_research_only_non_trading"
                elif "market_identity_symbol_instrument_conflict" in reason_codes:
                    status = "conflict"
            else:
                metadata = {}
                status = "missing_market_identity"
            rows.append(
                {
                    "symbol": symbol,
                    "venue": venue,
                    "instrument_key": instrument_key,
                    "operator_verified_market_identity_status": status,
                    "instrument_exists": instrument is not None,
                    "symbol_mapping_exists": symbol_model is not None,
                    "instrument_ref_id": getattr(instrument, "id", None),
                    "symbol_id": getattr(symbol_model, "id", None),
                    "is_strategy_eligible": getattr(symbol_model, "is_strategy_eligible", None),
                    "is_trading_eligible": getattr(symbol_model, "is_trading_eligible", None),
                    "research_only_market_identity_seed": metadata.get(
                        "research_only_market_identity_seed"
                    ),
                    "source": metadata.get("source"),
                    "operator_verified": metadata.get("operator_verified"),
                    "verified_by": metadata.get("verified_by"),
                    "verified_at": metadata.get("verified_at"),
                    "reason_codes": tuple(sorted(reason_codes)),
                }
            )
    return tuple(rows)


def _source_label_for_input(
    *,
    source_label_prefix: str | None,
    input_path: Path,
    requirement_result: dict[str, Any],
) -> str:
    prefix = source_label_prefix or "canonical_strategy_validation_candle_bundle"
    return (
        f"{prefix}:{requirement_result['symbol']}:"
        f"{requirement_result['timeframe']}:{input_path.name}"
    )


def import_result_to_dict(result: Any) -> dict[str, Any]:
    return _json_ready(asdict(result))


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


__all__ = [
    "StrategyValidationCanonicalCandleBundleImportResult",
    "guarded_import_strategy_validation_candle_bundle",
    "strategy_validation_canonical_candle_bundle_import_result_to_dict",
    "strategy_validation_canonical_candle_bundle_import_result_to_json",
    "strategy_validation_canonical_candle_bundle_import_result_to_markdown",
]
