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
    requirement_import_results: tuple[dict[str, Any], ...]
    input_files_seen: int
    requirements_seen: int
    files_imported: int
    files_blocked: int
    requirements_missing: int
    rows_inserted: int
    rows_updated: int
    rows_unchanged: int
    bundle_import_failure_policy: str
    bundle_import_final_status: str
    partial_persistence_occurred: bool
    imported_requirement_ids: tuple[str, ...]
    failed_requirement_ids: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]
    unmapped_input_files: tuple[str, ...]
    safe_rerun_resume_instructions: str
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
    requirement_results = list(preflight_payload["requirement_results"])
    requirement_aware_results = list(preflight_payload["requirement_aware_results"])
    supplied_input_paths = tuple(str(Path(path)) for path in input_paths)
    mapped_input_paths = {
        str(Path(item["input_path"]))
        for item in requirement_aware_results
        if item.get("input_path")
    }
    unmapped_input_files = tuple(
        input_path for input_path in supplied_input_paths if input_path not in mapped_input_paths
    )
    mapped_requirement_ids = {
        str(item["requirement_identifier"])
        for item in requirement_aware_results
        if item.get("requirement_identifier")
    }
    missing_requirement_rows = tuple(
        item
        for item in requirement_results
        if item.get("requirement_identifier")
        and str(item["requirement_identifier"]) not in mapped_requirement_ids
    )
    if unmapped_input_files:
        reason_codes.add("unmapped_input_file_blocked")
    if missing_requirement_rows:
        reason_codes.add("missing_requirement_blocked")
    if not preflight_payload["requirement_aware_results"]:
        reason_codes.add("canonical_candle_import_requires_requirement_aware_preflight")
    if not preflight_payload["ready"]:
        reason_codes.add("canonical_candle_import_preflight_not_ready")
        reason_codes.update(preflight_payload["reason_codes"])
    warnings.update(preflight_payload["warnings"])

    identity_requirements = _operator_verified_market_identity_requirements(
        (*requirement_results, *requirement_aware_results),
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
    imported_requirement_ids: list[str] = []
    failed_requirement_ids: list[str] = []

    if ready_for_import:
        stopped_after_failure = False
        for requirement_result in requirement_aware_results:
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
                imported_requirement_ids.append(requirement_result["requirement_identifier"])
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
                        "file_status": "imported",
                        "ready_for_import": True,
                        "source_label": source_label,
                        "import_result": import_payload,
                        "reason_codes": (),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - return explicit file status.
                reason_codes.add("canonical_candle_file_import_failed")
                failed_requirement_ids.append(requirement_result["requirement_identifier"])
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
                        "file_status": "failed",
                        "ready_for_import": True,
                        "source_label": source_label,
                        "error_message": str(exc).splitlines()[0],
                        "reason_codes": ("canonical_candle_file_import_failed",),
                    }
                )
                stopped_after_failure = True
                break
        if stopped_after_failure:
            completed_paths = {item["input_path"] for item in file_import_results}
            for requirement_result in requirement_aware_results:
                if requirement_result["input_path"] in completed_paths:
                    continue
                failed_requirement_ids.append(requirement_result["requirement_identifier"])
                file_import_results.append(
                    _blocked_mapped_requirement_file_result(
                        requirement_result,
                        reason_codes=(
                            "canonical_candle_bundle_import_stopped_after_failure",
                        ),
                    )
                )
    else:
        for requirement_result in requirement_aware_results:
            file_import_results.append(
                _blocked_mapped_requirement_file_result(
                    requirement_result,
                    reason_codes=tuple(
                        sorted(set(reason_codes) | set(requirement_result["reason_codes"]))
                    ),
                )
            )
    for input_path in unmapped_input_files:
        file_import_results.append(_unmapped_input_file_result(input_path))
    for requirement in missing_requirement_rows:
        file_import_results.append(_missing_requirement_file_result(requirement))

    import_attempted = any(item["import_attempted"] for item in file_import_results)
    import_completed = (
        ready_for_import
        and bool(file_import_results)
        and all(item["import_succeeded"] for item in file_import_results)
        and not missing_requirement_rows
        and not unmapped_input_files
    )
    if not import_completed and import_attempted:
        reason_codes.add("canonical_candle_bundle_import_incomplete")
    partial_persistence_occurred = (
        import_attempted and bool(imported_requirement_ids) and not import_completed
    )
    if partial_persistence_occurred:
        reason_codes.add("canonical_candle_bundle_partial_persistence")
    requirement_import_results = _requirement_import_results(
        requirement_results=requirement_results,
        requirement_aware_results=requirement_aware_results,
        file_import_results=file_import_results,
    )
    missing_requirement_ids = tuple(
        str(item["requirement_identifier"])
        for item in missing_requirement_rows
        if item.get("requirement_identifier")
    )
    bundle_import_final_status = _bundle_import_final_status(
        import_completed=import_completed,
        import_attempted=import_attempted,
        partial_persistence_occurred=partial_persistence_occurred,
        reason_codes=reason_codes,
    )

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
        requirement_import_results=tuple(
            _json_ready(item) for item in requirement_import_results
        ),
        input_files_seen=len(input_paths),
        requirements_seen=len(requirement_results) or len(requirement_aware_results),
        files_imported=sum(
            1
            for item in file_import_results
            if item.get("input_path") is not None and item["import_succeeded"]
        ),
        files_blocked=sum(
            1
            for item in file_import_results
            if item.get("input_path") is not None and not item["import_succeeded"]
        ),
        requirements_missing=len(missing_requirement_rows),
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        rows_unchanged=rows_unchanged,
        bundle_import_failure_policy="explicit_partial_with_resume",
        bundle_import_final_status=bundle_import_final_status,
        partial_persistence_occurred=partial_persistence_occurred,
        imported_requirement_ids=tuple(imported_requirement_ids),
        failed_requirement_ids=tuple(failed_requirement_ids),
        missing_requirement_ids=missing_requirement_ids,
        unmapped_input_files=unmapped_input_files,
        safe_rerun_resume_instructions=(
            "If partial persistence occurred, fix failed or missing files and rerun the "
            "guarded bundle import. Candle upsert is duplicate-safe for the same identity, "
            "but SV1.13 evidence review must not proceed until bundle_import_final_status "
            "is canonical_import_complete."
        ),
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


def _blocked_mapped_requirement_file_result(
    requirement_result: dict[str, Any],
    *,
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    return {
        "input_path": requirement_result["input_path"],
        "requirement_identifier": requirement_result["requirement_identifier"],
        "symbol": requirement_result["symbol"],
        "instrument_key": requirement_result["instrument_key"],
        "timeframe": requirement_result["timeframe"],
        "import_attempted": False,
        "import_succeeded": False,
        "file_status": "blocked",
        "ready_for_import": False,
        "source_label": None,
        "reason_codes": tuple(sorted(set(reason_codes))),
    }


def _unmapped_input_file_result(input_path: str) -> dict[str, Any]:
    return {
        "input_path": input_path,
        "requirement_identifier": None,
        "symbol": None,
        "instrument_key": None,
        "timeframe": None,
        "import_attempted": False,
        "import_succeeded": False,
        "file_status": "unmapped_input_file_blocked",
        "ready_for_import": False,
        "source_label": None,
        "reason_codes": (
            "input_file_missing_requirement_mapping",
            "unmapped_input_file_blocked",
        ),
    }


def _missing_requirement_file_result(requirement: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_path": None,
        "requirement_identifier": requirement.get("requirement_identifier"),
        "symbol": requirement.get("symbol"),
        "instrument_key": requirement.get("instrument_key"),
        "timeframe": requirement.get("timeframe"),
        "import_attempted": False,
        "import_succeeded": False,
        "file_status": "missing_requirement_blocked",
        "ready_for_import": False,
        "source_label": None,
        "reason_codes": (
            "requirement_missing_input_file",
            "missing_requirement_blocked",
        ),
    }


def _requirement_import_results(
    *,
    requirement_results: Sequence[dict[str, Any]],
    requirement_aware_results: Sequence[dict[str, Any]],
    file_import_results: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    requirements_by_id: dict[str, dict[str, Any]] = {}
    for item in (*requirement_results, *requirement_aware_results):
        identifier = item.get("requirement_identifier")
        if identifier:
            requirements_by_id[str(identifier)] = item
    file_results_by_requirement = {
        str(item["requirement_identifier"]): item
        for item in file_import_results
        if item.get("requirement_identifier")
    }
    rows: list[dict[str, Any]] = []
    for identifier, requirement in sorted(requirements_by_id.items()):
        file_result = file_results_by_requirement.get(identifier)
        if file_result is None:
            status = "missing_input_file"
            input_path = None
            import_attempted = False
            import_succeeded = False
            reason_codes = ("requirement_missing_input_file",)
        else:
            input_path = file_result.get("input_path")
            import_attempted = bool(file_result.get("import_attempted"))
            import_succeeded = bool(file_result.get("import_succeeded"))
            reason_codes = tuple(file_result.get("reason_codes", ()))
            if import_succeeded:
                status = "imported"
            elif input_path is None:
                status = "missing_input_file"
            elif import_attempted:
                status = "failed"
            else:
                status = str(file_result.get("file_status") or "blocked")
        rows.append(
            {
                "requirement_identifier": identifier,
                "input_path": input_path,
                "symbol": requirement.get("symbol"),
                "instrument_key": requirement.get("instrument_key"),
                "timeframe": requirement.get("timeframe"),
                "requested_start_at": requirement.get("requested_start_at"),
                "requested_end_at": requirement.get("requested_end_at"),
                "expected_candle_count": requirement.get("expected_candle_count"),
                "requirement_status": status,
                "import_attempted": import_attempted,
                "import_succeeded": import_succeeded,
                "reason_codes": reason_codes,
            }
        )
    return tuple(rows)


def _bundle_import_final_status(
    *,
    import_completed: bool,
    import_attempted: bool,
    partial_persistence_occurred: bool,
    reason_codes: set[str],
) -> str:
    if import_completed:
        return "canonical_import_complete"
    if partial_persistence_occurred:
        return "partial_import"
    if reason_codes:
        return "import_blocked"
    if import_attempted:
        return "import_blocked"
    return "import_not_attempted"


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
        f"- Final status: `{payload['bundle_import_final_status']}`",
        f"- Bundle failure policy: `{payload['bundle_import_failure_policy']}`",
        f"- Partial persistence occurred: `{payload['partial_persistence_occurred']}`",
        f"- Input files seen: `{payload['input_files_seen']}`",
        f"- Requirements seen: `{payload['requirements_seen']}`",
        f"- Files imported: `{payload['files_imported']}`",
        f"- Files blocked: `{payload['files_blocked']}`",
        f"- Requirements missing files: `{payload['requirements_missing']}`",
        f"- Rows inserted: `{payload['rows_inserted']}`",
        f"- Rows updated: `{payload['rows_updated']}`",
        f"- Rows unchanged: `{payload['rows_unchanged']}`",
        f"- Imported requirement IDs: `{payload['imported_requirement_ids']}`",
        f"- Failed requirement IDs: `{payload['failed_requirement_ids']}`",
        f"- Missing requirement IDs: `{payload['missing_requirement_ids']}`",
        f"- Unmapped input files: `{payload['unmapped_input_files']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        f"- Safe rerun/resume: {payload['safe_rerun_resume_instructions']}",
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
            title = item["input_path"] if item["input_path"] is not None else "<missing input file>"
            lines.extend(
                [
                    f"### `{title}`",
                    "",
                    f"- Requirement identifier: `{item['requirement_identifier']}`",
                    f"- Symbol: `{item['symbol']}`",
                    f"- Instrument key: `{item.get('instrument_key')}`",
                    f"- Timeframe: `{item['timeframe']}`",
                    f"- Import attempted: `{item['import_attempted']}`",
                    f"- Import succeeded: `{item['import_succeeded']}`",
                    f"- File status: `{item.get('file_status')}`",
                    f"- Source label: `{item['source_label']}`",
                    f"- Reason codes: `{item['reason_codes']}`",
                    "",
                ]
            )
    else:
        lines.append("- No files were imported or blocked because no requirement-aware files were supplied.")
        lines.append("")
    lines.extend(["## Requirement Import Results", ""])
    if payload["requirement_import_results"]:
        lines.append(
            "| requirement | input path | symbol | timeframe | status | reason codes |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in payload["requirement_import_results"]:
            lines.append(
                "| "
                f"`{item['requirement_identifier']}` | "
                f"`{item['input_path']}` | "
                f"`{item['symbol']}` | "
                f"`{item['timeframe']}` | "
                f"`{item['requirement_status']}` | "
                f"`{item['reason_codes']}` |"
            )
        lines.append("")
    else:
        lines.append("- No canonical requirements were supplied.")
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
                if metadata.get("source") not in {
                    "manual_offline_manifest",
                    "hyperliquid_public_info_meta",
                }:
                    reason_codes.add("research_market_identity_source_missing")
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
