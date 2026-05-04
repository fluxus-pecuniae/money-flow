"""SV1.12.3 guarded canonical candle import attempt workflow."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from core.domain.enums import Environment, Timeframe
from db.session import SessionLocal
from services.strategy_validation.candle_bundle_import import (
    StrategyValidationCanonicalCandleBundleImportResult,
    guarded_import_strategy_validation_candle_bundle,
    strategy_validation_canonical_candle_bundle_import_result_to_dict,
)
from services.strategy_validation.import_readiness import (
    DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT,
    evaluate_strategy_validation_import_readiness,
    strategy_validation_import_readiness_to_dict,
)
from services.strategy_validation.service import MoneyFlowBacktestService


@dataclass(frozen=True, slots=True)
class StrategyValidationGuardedImportAttemptResult:
    generated_at_utc: datetime
    environment: str
    venue: str
    operator_verified: bool
    verified_by: str | None
    market_identity_values_checked_offline: bool
    seed_identity_requested: bool
    identity_seed_attempted: bool
    identity_seeded: bool
    identity_seed_status: str
    readiness: dict[str, Any]
    guarded_import: dict[str, Any]
    canonical_requirements_expected: int
    canonical_requirements_seen: int
    input_files_seen: int
    input_files_present: tuple[str, ...]
    input_files_missing: tuple[str, ...]
    input_requirement_map: dict[str, str]
    final_status: str
    sv113_evidence_review_can_proceed: bool
    candles_imported: bool
    evidence_packs_generated: bool
    creates_live_artifacts: bool
    calls_exchange_adapters: bool
    calls_private_exchange_endpoints: bool
    calls_exchange_order_endpoints: bool
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]


def run_strategy_validation_guarded_import_attempt(
    *,
    manifest_path: str | Path = DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    seed_identity: bool = False,
    operator_verified: bool = False,
    verified_by: str | None = None,
    market_identity_values_checked_offline: bool = False,
    input_paths: Sequence[str | Path] = (),
    input_dir: str | Path | None = None,
    input_requirement_map: dict[str, Any] | None = None,
    input_requirement_map_path: str | Path | None = None,
    environment: Environment | str = Environment.TESTNET,
    venue: str = "hyperliquid",
    file_format: str = "auto",
    source_label_prefix: str = "canonical_strategy_validation_candle_bundle",
    service: MoneyFlowBacktestService | None = None,
    session_factory: Any = SessionLocal,
    generated_at: datetime | None = None,
) -> StrategyValidationGuardedImportAttemptResult:
    """Attempt the SV1.12.3 guarded import workflow without generating evidence packs."""

    generated_at_utc = _coerce_utc(generated_at or datetime.now(UTC)).replace(
        microsecond=0
    )
    validation_service = service or MoneyFlowBacktestService()
    reason_codes: set[str] = set()
    warnings: set[str] = set()

    seed_allowed = (
        seed_identity
        and operator_verified
        and bool(verified_by)
        and market_identity_values_checked_offline
    )
    if seed_identity and not operator_verified:
        reason_codes.add("market_identity_operator_verification_required")
        warnings.add("identity_seed_not_run_without_operator_verification")
    if seed_identity and operator_verified and not verified_by:
        reason_codes.add("market_identity_verified_by_required")
        warnings.add("identity_seed_not_run_without_verified_by")
    if seed_identity and operator_verified and verified_by and not market_identity_values_checked_offline:
        reason_codes.add("market_identity_values_offline_confirmation_required")
        warnings.add("identity_seed_not_run_without_offline_value_confirmation")

    readiness = evaluate_strategy_validation_import_readiness(
        service=validation_service,
        session_factory=session_factory,
        manifest_path=manifest_path,
        seed_identity=seed_allowed,
        operator_verified=operator_verified,
        verified_by=verified_by,
        environment=environment,
        venue=venue,
        file_format=file_format,
        generated_at=generated_at_utc,
    )
    readiness_payload = strategy_validation_import_readiness_to_dict(readiness)
    reason_codes.update(readiness_payload["reason_codes"])
    warnings.update(readiness_payload["warnings"])

    canonical_requirements = tuple(readiness_payload["canonical_candle_file_requirements"])
    resolved_inputs, auto_map, missing_files = _resolve_canonical_input_files(
        canonical_requirements=canonical_requirements,
        input_paths=input_paths,
        input_dir=input_dir,
    )
    effective_input_map: dict[str, Any] = dict(auto_map)
    if input_requirement_map_path is not None:
        raw_mapping = json.loads(Path(input_requirement_map_path).read_text(encoding="utf-8"))
        if not isinstance(raw_mapping, dict):
            raise ValueError("input requirement map must be a JSON object keyed by input path.")
        effective_input_map.update(raw_mapping)
    if input_requirement_map:
        effective_input_map.update(input_requirement_map)

    if missing_files:
        reason_codes.add("canonical_candle_files_missing")
        reason_codes.add("canonical_candle_requirement_preflight_incomplete")
    if len(canonical_requirements) != EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT:
        reason_codes.add("canonical_candle_requirement_count_unexpected")

    environment_value = environment.value if isinstance(environment, Environment) else str(environment)
    with tempfile.TemporaryDirectory(prefix="money_flow_sv1123_requirements_") as temp_dir:
        requirement_path = Path(temp_dir) / "canonical_candle_requirements.json"
        requirement_path.write_text(
            json.dumps(
                {"canonical_candle_import_requirements": list(canonical_requirements)},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        import_result = guarded_import_strategy_validation_candle_bundle(
            input_paths=resolved_inputs,
            requirement_json_paths=(requirement_path,),
            input_requirement_map=effective_input_map,
            environment=Environment(environment_value),
            venue=venue,
            timeframe=None,
            file_format=file_format,
            source_label_prefix=source_label_prefix,
            service=validation_service,
            session_factory=session_factory,
        )
    import_payload = strategy_validation_canonical_candle_bundle_import_result_to_dict(
        import_result
    )
    reason_codes.update(import_payload["reason_codes"])
    warnings.update(import_payload["warnings"])

    final_status = _final_status(
        readiness_payload=readiness_payload,
        import_result=import_result,
        missing_files=missing_files,
    )
    return StrategyValidationGuardedImportAttemptResult(
        generated_at_utc=generated_at_utc,
        environment=environment_value,
        venue=venue,
        operator_verified=operator_verified,
        verified_by=verified_by,
        market_identity_values_checked_offline=market_identity_values_checked_offline,
        seed_identity_requested=seed_identity,
        identity_seed_attempted=bool(readiness_payload["market_identity_seed_attempted"]),
        identity_seeded=bool(readiness_payload["market_identity_seeded"]),
        identity_seed_status=str(readiness_payload["identity_seed_status"]),
        readiness=readiness_payload,
        guarded_import=import_payload,
        canonical_requirements_expected=EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT,
        canonical_requirements_seen=len(canonical_requirements),
        input_files_seen=len(resolved_inputs),
        input_files_present=tuple(str(path) for path in resolved_inputs),
        input_files_missing=tuple(missing_files),
        input_requirement_map={
            str(Path(path)): _mapping_identifier(value)
            for path, value in effective_input_map.items()
        },
        final_status=final_status,
        sv113_evidence_review_can_proceed=final_status == "canonical_import_complete",
        candles_imported=(
            int(import_payload["rows_inserted"])
            + int(import_payload["rows_updated"])
            + int(import_payload["rows_unchanged"])
        )
        > 0,
        evidence_packs_generated=False,
        creates_live_artifacts=False,
        calls_exchange_adapters=False,
        calls_private_exchange_endpoints=False,
        calls_exchange_order_endpoints=False,
        reason_codes=tuple(sorted(reason_codes)),
        warnings=tuple(sorted(warnings)),
    )


def strategy_validation_guarded_import_attempt_result_to_dict(
    result: StrategyValidationGuardedImportAttemptResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_guarded_import_attempt_result_to_json(
    result: StrategyValidationGuardedImportAttemptResult,
) -> str:
    return json.dumps(
        strategy_validation_guarded_import_attempt_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_guarded_import_attempt_result_to_markdown(
    result: StrategyValidationGuardedImportAttemptResult,
) -> str:
    payload = strategy_validation_guarded_import_attempt_result_to_dict(result)
    db_status = payload["readiness"]["database_status"]
    guarded = payload["guarded_import"]
    lines = [
        "# SV1.12.3 Guarded Canonical Candle Import Result",
        "",
        "SV1.12.3 is research-only. It can seed explicitly operator-verified "
        "non-trading market identity and run guarded canonical candle import only "
        "after all 18 timezone-explicit files pass requirement-aware preflight. It "
        "does not generate evidence packs, approve paper trading, route, submit, or "
        "call exchange adapters.",
        "",
        "## Summary",
        "",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- Final status: `{payload['final_status']}`",
        f"- SV1.13 evidence review can proceed: `{payload['sv113_evidence_review_can_proceed']}`",
        f"- Environment: `{payload['environment']}`",
        f"- Venue: `{payload['venue']}`",
        f"- Operator verified: `{payload['operator_verified']}`",
        f"- Verified by: `{payload['verified_by']}`",
        f"- Offline market identity values checked: `{payload['market_identity_values_checked_offline']}`",
        f"- Identity seed requested: `{payload['seed_identity_requested']}`",
        f"- Identity seed attempted: `{payload['identity_seed_attempted']}`",
        f"- Identity seeded: `{payload['identity_seeded']}`",
        f"- Identity seed status: `{payload['identity_seed_status']}`",
        f"- Input files seen: `{payload['input_files_seen']}`",
        f"- Missing files: `{len(payload['input_files_missing'])}`",
        f"- Import attempted: `{guarded['import_attempted']}`",
        f"- Import completed: `{guarded['import_completed']}`",
        f"- Bundle final status: `{guarded['bundle_import_final_status']}`",
        f"- Bundle failure policy: `{guarded['bundle_import_failure_policy']}`",
        f"- Partial persistence occurred: `{guarded['partial_persistence_occurred']}`",
        f"- Rows inserted: `{guarded['rows_inserted']}`",
        f"- Rows updated: `{guarded['rows_updated']}`",
        f"- Rows unchanged: `{guarded['rows_unchanged']}`",
        f"- Candles imported: `{payload['candles_imported']}`",
        f"- Evidence packs generated: `{payload['evidence_packs_generated']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        "",
        "## DB And Schema",
        "",
        f"- DB target: `{db_status['configured_database_url']}`",
        f"- DB reachable: `{db_status['reachable']}`",
        f"- Target role: `{db_status['database_target_role']}`",
        f"- Intended strategy-validation DB: `{db_status['intended_strategy_validation_database']}`",
        f"- Schema status: `{db_status['schema_status']}`",
        f"- Migrations current: `{db_status['migrations_current']}`",
        f"- Required tables missing: `{db_status['required_schema_tables_missing']}`",
        f"- Persisted candle count before attempt: `{db_status['persisted_candle_count']}`",
        "",
        "## Market Identity",
        "",
        "| symbol | instrument key | status | strategy eligible | trading eligible | verified by | reason codes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["readiness"]["operator_verified_market_identity_requirements"]:
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
    lines.extend(
        [
            "",
            "## File Availability",
            "",
            f"- Canonical requirements seen: `{payload['canonical_requirements_seen']}` / `{payload['canonical_requirements_expected']}`",
            "",
            "### Present Files",
            "",
        ]
    )
    if payload["input_files_present"]:
        lines.extend(f"- `{path}`" for path in payload["input_files_present"])
    else:
        lines.append("- None.")
    lines.extend(["", "### Missing Files", ""])
    if payload["input_files_missing"]:
        lines.extend(f"- `{path}`" for path in payload["input_files_missing"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Preflight And Import",
            "",
            f"- Preflight ready: `{guarded['preflight']['ready']}`",
            f"- Preflight reason codes: `{guarded['preflight']['reason_codes']}`",
            f"- Imported requirement IDs: `{guarded['imported_requirement_ids']}`",
            f"- Failed requirement IDs: `{guarded['failed_requirement_ids']}`",
            f"- Missing requirement IDs: `{guarded['missing_requirement_ids']}`",
            f"- Safe rerun/resume: {guarded['safe_rerun_resume_instructions']}",
            "",
            "## File Import Results",
            "",
        ]
    )
    if guarded["file_import_results"]:
        for item in guarded["file_import_results"]:
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
                    f"- Reason codes: `{item['reason_codes']}`",
                    "",
                ]
            )
    else:
        lines.append("- No file import rows were produced.")
        lines.append("")
    lines.extend(
        [
            "## Research Boundary",
            "",
            f"- Creates live artifacts: `{payload['creates_live_artifacts']}`",
            f"- Calls exchange adapters: `{payload['calls_exchange_adapters']}`",
            f"- Calls private exchange endpoints: `{payload['calls_private_exchange_endpoints']}`",
            f"- Calls exchange order endpoints: `{payload['calls_exchange_order_endpoints']}`",
            "- No evidence packs are generated in SV1.12.3.",
            "- SV1.13 evidence review remains deferred unless final status is `canonical_import_complete`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _resolve_canonical_input_files(
    *,
    canonical_requirements: Sequence[dict[str, Any]],
    input_paths: Sequence[str | Path],
    input_dir: str | Path | None,
) -> tuple[tuple[Path, ...], dict[str, str], tuple[str, ...]]:
    requirements_by_filename = {
        str(item["suggested_filename"]): str(item["requirement_identifier"])
        for item in canonical_requirements
    }
    present: list[Path] = []
    seen_paths: set[str] = set()
    for input_path in input_paths:
        path = Path(input_path)
        key = str(path)
        if key not in seen_paths:
            present.append(path)
            seen_paths.add(key)
    if input_dir is not None:
        directory = Path(input_dir)
        for filename in requirements_by_filename:
            path = directory / filename
            key = str(path)
            if path.exists() and key not in seen_paths:
                present.append(path)
                seen_paths.add(key)
    auto_map = {
        str(path): requirements_by_filename[path.name]
        for path in present
        if path.name in requirements_by_filename
    }
    mapped_requirement_ids = set(auto_map.values())
    missing_files = tuple(
        str(Path(input_dir) / item["suggested_filename"])
        if input_dir is not None
        else str(item["suggested_filename"])
        for item in canonical_requirements
        if str(item["requirement_identifier"]) not in mapped_requirement_ids
    )
    return tuple(present), auto_map, missing_files


def _mapping_identifier(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("requirement_identifier"):
            return str(value["requirement_identifier"])
        return "|".join(
            str(value.get(key))
            for key in (
                "symbol",
                "instrument_key",
                "timeframe",
                "requested_start_at",
                "requested_end_at",
                "expected_candle_count",
            )
        )
    return str(value)


def _final_status(
    *,
    readiness_payload: dict[str, Any],
    import_result: StrategyValidationCanonicalCandleBundleImportResult,
    missing_files: Sequence[str],
) -> str:
    if import_result.bundle_import_final_status == "canonical_import_complete":
        return "canonical_import_complete"
    if import_result.bundle_import_final_status == "partial_import":
        return "partial_import"
    identity_ready = all(
        item["operator_verified_market_identity_status"] == "ready"
        for item in readiness_payload["operator_verified_market_identity_requirements"]
    )
    if not identity_ready:
        return "identity_missing"
    if missing_files:
        return "files_missing"
    if not import_result.preflight.get("ready"):
        return "preflight_blocked"
    if import_result.reason_codes:
        return "import_blocked"
    return "import_blocked"


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, set):
        return [_json_ready(item) for item in sorted(value)]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = [
    "StrategyValidationGuardedImportAttemptResult",
    "run_strategy_validation_guarded_import_attempt",
    "strategy_validation_guarded_import_attempt_result_to_dict",
    "strategy_validation_guarded_import_attempt_result_to_json",
    "strategy_validation_guarded_import_attempt_result_to_markdown",
]
