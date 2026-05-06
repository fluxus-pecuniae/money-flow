"""Research-only market identity bootstrap and candle-import preflight helpers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlalchemy import select

from core.domain.enums import MarketType, ProductType, Timeframe
from db.models import InstrumentModel, SymbolModel
from db.session import SessionLocal
from services.strategy_validation.candles import (
    _load_candle_rows,
    _parse_candle_row,
    _resolve_symbol_model,
    _timeframe_duration,
)

CANONICAL_MARKET_IDENTITY_SYMBOLS = ("BTC", "ETH", "SOL")
CANONICAL_MARKET_IDENTITY_VENUE = "hyperliquid"
CANONICAL_MARKET_IDENTITY_QUOTE_ASSET = "USDC"
CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET = "USDC"
CANONICAL_MARKET_IDENTITY_MARKET_TYPE = MarketType.PERPETUAL
CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE = ProductType.LINEAR


@dataclass(frozen=True, slots=True)
class StrategyValidationMarketIdentitySeedResult:
    manifest_path: str
    manifest_name: str | None
    dry_run: bool
    verify_only: bool
    operator_verified: bool
    verified_by: str | None
    verified_at_utc: str | None
    venue: str
    required_symbols: tuple[str, ...]
    missing_required_symbols: tuple[str, ...]
    instruments_seen: int
    instruments_inserted: int
    instruments_updated: int
    instruments_unchanged: int
    symbols_seen: int
    symbols_inserted: int
    symbols_updated: int
    symbols_unchanged: int
    conflicts: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    creates_live_artifacts: bool = False
    calls_exchange_adapters: bool = False
    calls_private_exchange_endpoints: bool = False
    calls_exchange_order_endpoints: bool = False


@dataclass(frozen=True, slots=True)
class StrategyValidationCandleImportPreflightResult:
    environment: str
    venue: str
    ready: bool
    input_files_seen: int
    input_rows_seen: int
    requirements_seen: int
    input_file_results: tuple[dict[str, Any], ...]
    requirement_results: tuple[dict[str, Any], ...]
    requirement_aware_results: tuple[dict[str, Any], ...]
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    creates_live_artifacts: bool = False
    calls_exchange_adapters: bool = False
    calls_private_exchange_endpoints: bool = False
    calls_exchange_order_endpoints: bool = False


def canonical_market_identity_instrument_key(symbol: str) -> str:
    asset = symbol.upper()
    return f"perpetual:linear:{asset}:USDC:USDC"


def seed_strategy_validation_market_identity_from_manifest(
    manifest_path: str | Path,
    *,
    dry_run: bool = False,
    verify_only: bool = False,
    operator_verified: bool = False,
    verified_by: str | None = None,
    session_factory: Any = SessionLocal,
) -> StrategyValidationMarketIdentitySeedResult:
    """Seed or verify canonical research-only market identity from a manifest."""

    path = Path(manifest_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries, manifest_warnings = _validated_manifest_entries(payload)
    if _manifest_appears_example_or_placeholder(payload, path):
        manifest_warnings.add("example_or_placeholder_manifest_requires_operator_verification")
    missing_required = _missing_required_symbols(entries)
    if missing_required:
        raise ValueError(
            "strategy_validation_market_identity_manifest_missing_required_symbols: "
            f"missing={','.join(missing_required)}"
        )
    manifest_operator_verified = payload.get("operator_verified") is True
    manifest_verified_by = _optional_str(payload, "verified_by")
    effective_operator_verified = bool(operator_verified or manifest_operator_verified)
    effective_verified_by = verified_by or manifest_verified_by
    verified_at = datetime.now(UTC).replace(microsecond=0)

    write_requested = not dry_run and not verify_only
    verification_conflicts: list[dict[str, Any]] = []
    if write_requested and not effective_operator_verified:
        verification_conflicts.append(
            _manifest_conflict(
                "market_identity_operator_verification_required",
                payload,
                path,
            )
        )
    if write_requested and effective_operator_verified and not effective_verified_by:
        verification_conflicts.append(
            _manifest_conflict(
                "market_identity_verified_by_required",
                payload,
                path,
            )
        )
    if verification_conflicts:
        return StrategyValidationMarketIdentitySeedResult(
            manifest_path=str(path),
            manifest_name=_optional_str(payload, "manifest_name"),
            dry_run=dry_run,
            verify_only=verify_only,
            operator_verified=effective_operator_verified,
            verified_by=effective_verified_by,
            verified_at_utc=None,
            venue=_manifest_venue(entries),
            required_symbols=CANONICAL_MARKET_IDENTITY_SYMBOLS,
            missing_required_symbols=missing_required,
            instruments_seen=len(entries),
            instruments_inserted=0,
            instruments_updated=0,
            instruments_unchanged=0,
            symbols_seen=len(entries),
            symbols_inserted=0,
            symbols_updated=0,
            symbols_unchanged=0,
            conflicts=tuple(_json_ready(item) for item in verification_conflicts),
            warnings=tuple(sorted(manifest_warnings)),
        )
    if write_requested:
        _apply_operator_verification_metadata(
            entries,
            verified_by=str(effective_verified_by),
            verified_at=verified_at,
        )

    counts = {
        "instruments_inserted": 0,
        "instruments_updated": 0,
        "instruments_unchanged": 0,
        "symbols_inserted": 0,
        "symbols_updated": 0,
        "symbols_unchanged": 0,
    }
    conflicts: list[dict[str, Any]] = []

    with session_factory() as session:
        for entry in entries:
            instrument_payload = entry["instrument"]
            symbol_payload = entry["symbol"]
            instrument = session.scalar(
                select(InstrumentModel).where(
                    InstrumentModel.instrument_key == instrument_payload["instrument_key"]
                )
            )
            symbol_model = _find_symbol_mapping(session, symbol_payload)

            if verify_only:
                if instrument is None:
                    conflicts.append(
                        _conflict(
                            "missing_instrument",
                            entry,
                            requested_instrument_ref_id=None,
                            existing_instrument_ref_id=None,
                            existing_symbol_id=getattr(symbol_model, "id", None),
                        )
                    )
                elif _instrument_changes(instrument, instrument_payload):
                    conflicts.append(
                        _conflict(
                            "instrument_manifest_drift",
                            entry,
                            requested_instrument_ref_id=instrument.id,
                            existing_instrument_ref_id=instrument.id,
                            existing_symbol_id=getattr(symbol_model, "id", None),
                        )
                    )
                if symbol_model is None:
                    conflicts.append(
                        _conflict(
                            "missing_symbol_mapping",
                            entry,
                            requested_instrument_ref_id=getattr(instrument, "id", None),
                            existing_instrument_ref_id=None,
                            existing_symbol_id=None,
                        )
                    )
                elif instrument is not None and symbol_model.instrument_ref_id != instrument.id:
                    conflicts.append(
                        _conflict(
                            "market_identity_symbol_instrument_conflict",
                            entry,
                            requested_instrument_ref_id=instrument.id,
                            existing_instrument_ref_id=symbol_model.instrument_ref_id,
                            existing_symbol_id=symbol_model.id,
                        )
                    )
                elif _symbol_changes(symbol_model, symbol_payload, instrument.id):
                    conflicts.append(
                        _conflict(
                            "symbol_manifest_drift",
                            entry,
                            requested_instrument_ref_id=instrument.id,
                            existing_instrument_ref_id=symbol_model.instrument_ref_id,
                            existing_symbol_id=symbol_model.id,
                        )
                    )
                continue

            if instrument is None:
                counts["instruments_inserted"] += 1
                if not dry_run:
                    instrument = InstrumentModel(**instrument_payload)
                    session.add(instrument)
                    session.flush()
            else:
                changes = _instrument_changes(instrument, instrument_payload)
                if changes:
                    counts["instruments_updated"] += 1
                    if not dry_run:
                        _apply_instrument_payload(instrument, instrument_payload)
                else:
                    counts["instruments_unchanged"] += 1

            requested_instrument_ref_id = getattr(instrument, "id", None)
            if symbol_model is not None:
                if requested_instrument_ref_id is None:
                    conflicts.append(
                        _conflict(
                            "market_identity_symbol_would_retarget_to_new_instrument",
                            entry,
                            requested_instrument_ref_id=None,
                            existing_instrument_ref_id=symbol_model.instrument_ref_id,
                            existing_symbol_id=symbol_model.id,
                        )
                    )
                    continue
                if symbol_model.instrument_ref_id != requested_instrument_ref_id:
                    conflicts.append(
                        _conflict(
                            "market_identity_symbol_instrument_conflict",
                            entry,
                            requested_instrument_ref_id=requested_instrument_ref_id,
                            existing_instrument_ref_id=symbol_model.instrument_ref_id,
                            existing_symbol_id=symbol_model.id,
                        )
                    )
                    continue

            if symbol_model is None:
                counts["symbols_inserted"] += 1
                if not dry_run:
                    if requested_instrument_ref_id is None:
                        raise ValueError(
                            "strategy_validation_market_identity_internal_error: "
                            "instrument_ref_id missing before symbol insert"
                        )
                    session.add(
                        SymbolModel(
                            instrument_ref_id=requested_instrument_ref_id,
                            **symbol_payload,
                        )
                    )
            else:
                if requested_instrument_ref_id is None:
                    requested_instrument_ref_id = symbol_model.instrument_ref_id
                changes = _symbol_changes(
                    symbol_model,
                    symbol_payload,
                    requested_instrument_ref_id,
                    compare_raw_metadata=True,
                )
                if changes:
                    counts["symbols_updated"] += 1
                    if not dry_run:
                        _apply_symbol_payload(
                            symbol_model,
                            symbol_payload,
                            requested_instrument_ref_id,
                        )
                else:
                    counts["symbols_unchanged"] += 1

        if conflicts or dry_run:
            session.rollback()
        else:
            session.commit()

    return StrategyValidationMarketIdentitySeedResult(
        manifest_path=str(path),
        manifest_name=_optional_str(payload, "manifest_name"),
        dry_run=dry_run,
        verify_only=verify_only,
        operator_verified=effective_operator_verified,
        verified_by=effective_verified_by,
        verified_at_utc=verified_at.isoformat() if write_requested else None,
        venue=_manifest_venue(entries),
        required_symbols=CANONICAL_MARKET_IDENTITY_SYMBOLS,
        missing_required_symbols=missing_required,
        instruments_seen=len(entries),
        instruments_inserted=counts["instruments_inserted"],
        instruments_updated=counts["instruments_updated"],
        instruments_unchanged=counts["instruments_unchanged"],
        symbols_seen=len(entries),
        symbols_inserted=counts["symbols_inserted"],
        symbols_updated=counts["symbols_updated"],
        symbols_unchanged=counts["symbols_unchanged"],
        conflicts=tuple(_json_ready(item) for item in conflicts),
        warnings=tuple(sorted(manifest_warnings)),
    )


def strategy_validation_market_identity_seed_result_to_dict(
    result: StrategyValidationMarketIdentitySeedResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_market_identity_seed_result_to_json(
    result: StrategyValidationMarketIdentitySeedResult,
) -> str:
    return json.dumps(
        strategy_validation_market_identity_seed_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_market_identity_seed_result_to_markdown(
    result: StrategyValidationMarketIdentitySeedResult,
) -> str:
    payload = strategy_validation_market_identity_seed_result_to_dict(result)
    lines = [
        "# Strategy Validation Market Identity Seed Summary",
        "",
        "This summary is research-only. It creates no candles, strategy decisions, "
        "signals, orders, routing artifacts, paper trades, live trades, or exchange calls.",
        "",
        f"- Manifest path: `{payload['manifest_path']}`",
        f"- Manifest name: `{payload['manifest_name']}`",
        f"- Venue: `{payload['venue']}`",
        f"- Dry run: `{payload['dry_run']}`",
        f"- Verify only: `{payload['verify_only']}`",
        f"- Operator verified: `{payload['operator_verified']}`",
        f"- Verified by: `{payload['verified_by']}`",
        f"- Verified at UTC: `{payload['verified_at_utc']}`",
        f"- Required symbols: `{payload['required_symbols']}`",
        f"- Missing required symbols: `{payload['missing_required_symbols']}`",
        "",
        "## Counts",
        "",
        f"- Instruments seen: `{payload['instruments_seen']}`",
        f"- Instruments inserted: `{payload['instruments_inserted']}`",
        f"- Instruments updated: `{payload['instruments_updated']}`",
        f"- Instruments unchanged: `{payload['instruments_unchanged']}`",
        f"- Symbols seen: `{payload['symbols_seen']}`",
        f"- Symbols inserted: `{payload['symbols_inserted']}`",
        f"- Symbols updated: `{payload['symbols_updated']}`",
        f"- Symbols unchanged: `{payload['symbols_unchanged']}`",
        "",
        "## Conflicts",
        "",
    ]
    if payload["conflicts"]:
        lines.extend(f"- `{item}`" for item in payload["conflicts"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    if payload["warnings"]:
        lines.extend(f"- `{item}`" for item in payload["warnings"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Research Boundary",
            "",
            f"- Creates live artifacts: `{payload['creates_live_artifacts']}`",
            f"- Calls exchange adapters: `{payload['calls_exchange_adapters']}`",
            f"- Calls private exchange endpoints: `{payload['calls_private_exchange_endpoints']}`",
            f"- Calls exchange order endpoints: `{payload['calls_exchange_order_endpoints']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def canonical_market_identity_requirements(
    *,
    symbols: Iterable[dict[str, str | None]],
    venue: str,
    session_factory: Any,
    schema_ready: bool,
) -> tuple[dict[str, Any], ...]:
    """Inspect canonical instrument/symbol readiness without mutating rows."""

    unique: dict[tuple[str, str | None, str], dict[str, str | None]] = {}
    for item in symbols:
        symbol = str(item["symbol"]).upper()
        instrument_key = item.get("instrument_key")
        unique[(venue, symbol, instrument_key)] = {
            "venue": venue,
            "symbol": symbol,
            "instrument_key": instrument_key,
        }
    if not schema_ready:
        return tuple(
            {
                "symbol": item["symbol"],
                "venue": item["venue"],
                "instrument_key": item["instrument_key"],
                "instrument_exists": False,
                "symbol_mapping_exists": False,
                "instrument_ref_id": None,
                "symbol_id": None,
                "market_identity_status": "missing_instrument",
                "reason_codes": (
                    "schema_not_ready_for_market_identity_check",
                    "market_identity_readiness_not_verified",
                ),
            }
            for item in sorted(unique.values(), key=lambda value: value["symbol"] or "")
        )

    rows: list[dict[str, Any]] = []
    with session_factory() as session:
        for item in sorted(unique.values(), key=lambda value: value["symbol"] or ""):
            instrument = None
            if item["instrument_key"] is not None:
                instrument = session.scalar(
                    select(InstrumentModel).where(
                        InstrumentModel.instrument_key == item["instrument_key"]
                    )
                )
            symbol_model = None
            if instrument is not None:
                symbol_model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == item["venue"],
                        SymbolModel.symbol == item["symbol"],
                        SymbolModel.market_type == CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
                        SymbolModel.product_type == CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
                        SymbolModel.quote_asset == CANONICAL_MARKET_IDENTITY_QUOTE_ASSET,
                        SymbolModel.settlement_asset
                        == CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET,
                    )
                )
            reason_codes: set[str] = set()
            status = "ready"
            if instrument is None:
                status = "missing_instrument"
                reason_codes.add("missing_instrument")
                reason_codes.add("unknown_instrument_key")
            elif symbol_model is None:
                status = "missing_symbol_mapping"
                reason_codes.add("missing_symbol_mapping")
            elif symbol_model.instrument_ref_id != instrument.id:
                status = "conflict"
                reason_codes.add("market_identity_symbol_instrument_conflict")
            rows.append(
                {
                    "symbol": item["symbol"],
                    "venue": item["venue"],
                    "instrument_key": item["instrument_key"],
                    "instrument_exists": instrument is not None,
                    "symbol_mapping_exists": symbol_model is not None,
                    "instrument_ref_id": getattr(instrument, "id", None),
                    "symbol_id": getattr(symbol_model, "id", None),
                    "market_identity_status": status,
                    "reason_codes": tuple(sorted(reason_codes)),
                }
            )
    return tuple(_json_ready(row) for row in rows)


def preflight_strategy_validation_candle_import(
    *,
    input_paths: Sequence[str | Path] = (),
    requirements_from_review_json: str | Path | None = None,
    requirement_json_paths: Sequence[str | Path] = (),
    input_requirement_map: dict[str, Any] | None = None,
    input_requirement_map_path: str | Path | None = None,
    environment: str,
    venue: str,
    timeframe: Timeframe | None = None,
    file_format: str = "auto",
    session_factory: Any = SessionLocal,
) -> StrategyValidationCandleImportPreflightResult:
    """Validate candle files and canonical identity requirements without writing candles."""

    input_results: list[dict[str, Any]] = []
    requirement_results: list[dict[str, Any]] = []
    requirement_aware_results: list[dict[str, Any]] = []
    reason_codes: set[str] = set()
    warnings: set[str] = set()
    input_rows_seen = 0
    requirement_by_input, supplied_requirements = _load_input_requirement_mapping(
        input_paths=input_paths,
        requirement_json_paths=requirement_json_paths,
        input_requirement_map=input_requirement_map,
        input_requirement_map_path=input_requirement_map_path,
    )
    requirement_aware_requested = bool(
        requirement_json_paths or input_requirement_map or input_requirement_map_path
    )
    if requirement_aware_requested and not requirement_by_input:
        warnings.add("input_requirement_mapping_missing")
        reason_codes.add("input_requirement_mapping_missing")
    if requirement_aware_requested:
        mapping_reason_codes = _requirement_mapping_reason_codes(
            input_paths=input_paths,
            requirement_by_input=requirement_by_input,
            supplied_requirements=supplied_requirements,
        )
        reason_codes.update(mapping_reason_codes)
    if supplied_requirements:
        requirement_results = list(
            _preflight_supplied_candle_requirements(
                supplied_requirements,
                venue=venue,
                session_factory=session_factory,
            )
        )
        for result in requirement_results:
            reason_codes.update(result["reason_codes"])

    for input_path in input_paths:
        row_level_timeframe = timeframe
        mapped_requirement = requirement_by_input.get(str(Path(input_path)))
        if row_level_timeframe is None and mapped_requirement is not None:
            row_level_timeframe = mapped_requirement["timeframe"]
        result = _preflight_input_path(
            Path(input_path),
            venue=venue,
            timeframe=row_level_timeframe,
            file_format=file_format,
            session_factory=session_factory,
        )
        input_rows_seen += int(result["rows_seen"])
        input_results.append(result)
        reason_codes.update(result["reason_codes"])
        if str(Path(input_path)) in requirement_by_input:
            requirement_result = _preflight_input_path_against_requirement(
                Path(input_path),
                requirement_by_input[str(Path(input_path))],
                venue=venue,
                timeframe=timeframe,
                file_format=file_format,
                session_factory=session_factory,
            )
            requirement_aware_results.append(requirement_result)
            reason_codes.update(requirement_result["reason_codes"])

    if requirements_from_review_json is not None and not requirement_results:
        requirement_results = list(
            _preflight_requirements_from_review_json(
                Path(requirements_from_review_json),
                venue=venue,
                session_factory=session_factory,
            )
        )
        for result in requirement_results:
            reason_codes.update(result["reason_codes"])

    ready = not reason_codes and all(
        bool(item["ready"]) for item in [*input_results, *requirement_results]
    )
    if requirement_aware_results:
        ready = ready and all(
            bool(item["ready_for_import"]) for item in requirement_aware_results
        )
    elif input_paths:
        warnings.add("row_level_preflight_not_canonical_coverage_proof")
    if (
        not input_paths
        and requirements_from_review_json is None
        and not requirement_json_paths
        and input_requirement_map_path is None
        and not input_requirement_map
    ):
        warnings.add("no_preflight_inputs_or_requirements_supplied")
        reason_codes.add("no_preflight_inputs_or_requirements_supplied")
        ready = False
    return StrategyValidationCandleImportPreflightResult(
        environment=environment,
        venue=venue,
        ready=ready,
        input_files_seen=len(input_paths),
        input_rows_seen=input_rows_seen,
        requirements_seen=len(requirement_results),
        input_file_results=tuple(_json_ready(item) for item in input_results),
        requirement_results=tuple(_json_ready(item) for item in requirement_results),
        requirement_aware_results=tuple(_json_ready(item) for item in requirement_aware_results),
        reason_codes=tuple(sorted(reason_codes)),
        warnings=tuple(sorted(warnings)),
    )


def strategy_validation_candle_import_preflight_result_to_dict(
    result: StrategyValidationCandleImportPreflightResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_candle_import_preflight_result_to_json(
    result: StrategyValidationCandleImportPreflightResult,
) -> str:
    return json.dumps(
        strategy_validation_candle_import_preflight_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_candle_import_preflight_result_to_markdown(
    result: StrategyValidationCandleImportPreflightResult,
) -> str:
    payload = strategy_validation_candle_import_preflight_result_to_dict(result)
    lines = [
        "# Strategy Validation Candle Import Preflight",
        "",
        "This preflight is research-only. It validates files and market identity mappings "
        "without writing candles, generating evidence packs, calling exchanges, routing, "
        "or creating live artifacts.",
        "",
        f"- Environment: `{payload['environment']}`",
        f"- Venue: `{payload['venue']}`",
        f"- Ready: `{payload['ready']}`",
        f"- Input files seen: `{payload['input_files_seen']}`",
        f"- Input rows seen: `{payload['input_rows_seen']}`",
        f"- Requirements seen: `{payload['requirements_seen']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        "",
        "## Input Files",
        "",
    ]
    if payload["input_file_results"]:
        for item in payload["input_file_results"]:
            lines.extend(
                [
                    f"### `{item['input_path']}`",
                    "",
                    f"- Ready: `{item['ready']}`",
                    f"- Row-level ready: `{item.get('row_level_ready')}`",
                    f"- Identity ready: `{item.get('identity_ready')}`",
                    f"- Requirement coverage ready: `{item.get('requirement_coverage_ready')}`",
                    f"- Ready for import: `{item.get('ready_for_import')}`",
                    f"- Rows seen: `{item['rows_seen']}`",
                    f"- Reason codes: `{item['reason_codes']}`",
                    f"- Row results: `{item['row_results']}`",
                    "",
                ]
            )
    else:
        lines.append("- No input files supplied.")
        lines.append("")
    lines.extend(["## Review Requirements", ""])
    if payload["requirement_results"]:
        for item in payload["requirement_results"]:
            lines.extend(
                [
                    f"- `{item['symbol']}` / `{item['instrument_key']}`: "
                    f"`{item['market_identity_status']}` timeframe=`{item.get('timeframe')}` "
                    f"window=`({item.get('requested_start_at')}, {item.get('requested_end_at')}]` "
                    f"reasons=`{item['reason_codes']}`",
                ]
            )
    else:
        lines.append("- No review JSON requirements supplied.")
    lines.extend(["", "## Requirement-Aware Input Coverage", ""])
    if payload["requirement_aware_results"]:
        for item in payload["requirement_aware_results"]:
            lines.extend(
                [
                    f"### `{item['input_path']}`",
                    "",
                    f"- Requirement identifier: `{item['requirement_identifier']}`",
                    f"- Row-level ready: `{item['row_level_ready']}`",
                    f"- Identity ready: `{item['identity_ready']}`",
                    f"- Requirement coverage ready: `{item['requirement_coverage_ready']}`",
                    f"- Ready for import: `{item['ready_for_import']}`",
                    f"- Expected candle count: `{item['expected_candle_count']}`",
                    f"- Actual candle count: `{item['actual_candle_count']}`",
                    f"- Missing close slots: `{item['missing_close_time_slots']}`",
                    f"- Duplicate close slots: `{item['duplicate_close_time_slots']}`",
                    f"- Extra close slots: `{item['extra_close_time_slots']}`",
                    f"- Reason codes: `{item['reason_codes']}`",
                    "",
                ]
            )
    else:
        lines.append(
            "- No requirement-aware input mapping supplied; row-level preflight alone is "
            "not proof of canonical requirement coverage."
        )
    lines.extend(
        [
            "",
            "## Research Boundary",
            "",
            f"- Creates live artifacts: `{payload['creates_live_artifacts']}`",
            f"- Calls exchange adapters: `{payload['calls_exchange_adapters']}`",
            f"- Calls private exchange endpoints: `{payload['calls_private_exchange_endpoints']}`",
            f"- Calls exchange order endpoints: `{payload['calls_exchange_order_endpoints']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _validated_manifest_entries(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    if not isinstance(payload, dict):
        raise ValueError("strategy validation market identity manifest must be a JSON object.")
    markets = payload.get("markets")
    if not isinstance(markets, list) or not markets:
        raise ValueError("strategy validation market identity manifest requires non-empty markets.")
    warnings: set[str] = set()
    entries: list[dict[str, Any]] = []
    for raw_entry in markets:
        if not isinstance(raw_entry, dict):
            raise ValueError("strategy validation market identity manifest markets must be objects.")
        instrument_payload = _validated_instrument_payload(raw_entry.get("instrument"))
        symbol_payload, symbol_warnings = _validated_symbol_payload(raw_entry.get("symbol"))
        warnings.update(symbol_warnings)
        _validate_canonical_alignment(instrument_payload, symbol_payload)
        entries.append({"instrument": instrument_payload, "symbol": symbol_payload})
    return entries, warnings


def _manifest_appears_example_or_placeholder(payload: dict[str, Any], path: Path) -> bool:
    haystack = " ".join(
        str(value)
        for value in (
            path.name,
            payload.get("manifest_name"),
            payload.get("description"),
            payload.get("source"),
        )
        if value is not None
    ).lower()
    if "example" in haystack or "placeholder" in haystack:
        return True
    for item in payload.get("markets") or ():
        if not isinstance(item, dict):
            continue
        raw_metadata = (item.get("symbol") or {}).get("raw_metadata") if isinstance(item.get("symbol"), dict) else {}
        if isinstance(raw_metadata, dict):
            text = json.dumps(raw_metadata, sort_keys=True).lower()
            if "example" in text or "placeholder" in text:
                return True
    return False


def _manifest_conflict(reason_code: str, payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "reason_code": reason_code,
        "manifest_path": str(path),
        "manifest_name": _optional_str(payload, "manifest_name"),
        "operator_verified": payload.get("operator_verified") is True,
        "verified_by": _optional_str(payload, "verified_by"),
    }


def _apply_operator_verification_metadata(
    entries: Sequence[dict[str, Any]],
    *,
    verified_by: str,
    verified_at: datetime,
) -> None:
    for entry in entries:
        raw_metadata = dict(entry["symbol"].get("raw_metadata") or {})
        raw_metadata.update(
            {
                "operator_verified": True,
                "verified_by": verified_by,
                "verified_at": verified_at.isoformat(),
                "research_only_market_identity_seed": True,
            }
        )
        raw_metadata.setdefault("sv_phase", "SV1.11.2")
        raw_metadata.setdefault("source", "manual_offline_manifest")
        entry["symbol"]["raw_metadata"] = raw_metadata


def _validated_instrument_payload(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("market identity manifest entry missing instrument object.")
    payload = {
        "instrument_key": _required_str(raw, "instrument_key"),
        "canonical_symbol": _required_str(raw, "canonical_symbol").upper(),
        "market_type": MarketType(_required_str(raw, "market_type")),
        "product_type": ProductType(_required_str(raw, "product_type")),
        "base_asset": _required_str(raw, "base_asset").upper(),
        "quote_asset": _required_str(raw, "quote_asset").upper(),
        "settlement_asset": _optional_str(raw, "settlement_asset"),
        "is_active": _required_bool(raw, "is_active"),
    }
    if payload["settlement_asset"] is not None:
        payload["settlement_asset"] = payload["settlement_asset"].upper()
    return payload


def _validated_symbol_payload(raw: Any) -> tuple[dict[str, Any], set[str]]:
    if not isinstance(raw, dict):
        raise ValueError("market identity manifest entry missing symbol object.")
    warnings: set[str] = set()
    raw_metadata = raw.get("raw_metadata") or {}
    if not isinstance(raw_metadata, dict):
        raise ValueError("market identity manifest raw_metadata must be an object.")
    is_strategy_eligible = raw.get("is_strategy_eligible")
    is_trading_eligible = raw.get("is_trading_eligible")
    if is_strategy_eligible is None:
        is_strategy_eligible = False
        warnings.add("is_strategy_eligible_defaulted_false_for_research_seed")
    elif not isinstance(is_strategy_eligible, bool):
        raise ValueError(
            "strategy validation market identity field is_strategy_eligible must be boolean."
        )
    elif is_strategy_eligible:
        raise ValueError(
            "strategy_validation_seed_cannot_mark_symbol_strategy_eligible: "
            "research_market_identity_seed_must_remain_non_trading"
        )
    if is_trading_eligible is None:
        is_trading_eligible = False
        warnings.add("is_trading_eligible_defaulted_false_for_research_seed")
    elif not isinstance(is_trading_eligible, bool):
        raise ValueError(
            "strategy validation market identity field is_trading_eligible must be boolean."
        )
    elif is_trading_eligible:
        raise ValueError(
            "strategy_validation_seed_cannot_mark_symbol_trading_eligible: "
            "research_market_identity_seed_must_remain_non_trading"
        )
    payload = {
        "venue": _required_str(raw, "venue"),
        "symbol": _required_str(raw, "symbol").upper(),
        "exchange_symbol": _required_str(raw, "exchange_symbol"),
        "venue_asset_id": _optional_str(raw, "venue_asset_id"),
        "asset_id": _optional_int(raw, "asset_id", minimum=0),
        "market_type": MarketType(_required_str(raw, "market_type")),
        "product_type": ProductType(_required_str(raw, "product_type")),
        "base_asset": _required_str(raw, "base_asset").upper(),
        "quote_asset": _required_str(raw, "quote_asset").upper(),
        "settlement_asset": _optional_str(raw, "settlement_asset"),
        "price_tick_size": _positive_decimal(raw, "price_tick_size"),
        "quantity_step_size": _positive_decimal(raw, "quantity_step_size"),
        "min_order_size": _positive_decimal(raw, "min_order_size"),
        "size_decimals": _optional_int(raw, "size_decimals", minimum=0),
        "max_leverage": _optional_int(raw, "max_leverage", minimum=1),
        "only_isolated": _required_bool(raw, "only_isolated"),
        "is_perpetual": _required_bool(raw, "is_perpetual"),
        "is_builder_deployed": _required_bool(raw, "is_builder_deployed"),
        "is_strategy_eligible": bool(is_strategy_eligible),
        "is_trading_eligible": bool(is_trading_eligible),
        "is_active": _required_bool(raw, "is_active"),
        "raw_metadata": {
            **raw_metadata,
            "research_only_market_identity_seed": True,
            "source": raw_metadata.get("source", "manual_offline_manifest"),
            "sv_phase": raw_metadata.get("sv_phase", "SV1.11.2"),
        },
    }
    if payload["settlement_asset"] is not None:
        payload["settlement_asset"] = payload["settlement_asset"].upper()
    return payload, warnings


def _validate_canonical_alignment(
    instrument: dict[str, Any],
    symbol: dict[str, Any],
) -> None:
    asset = symbol["symbol"]
    expected_key = canonical_market_identity_instrument_key(asset)
    if instrument["instrument_key"] != expected_key:
        raise ValueError(
            "strategy_validation_market_identity_manifest_not_canonical: "
            f"symbol={asset} expected_instrument_key={expected_key} "
            f"actual_instrument_key={instrument['instrument_key']}"
        )
    checks = {
        "canonical_symbol": instrument["canonical_symbol"] == asset,
        "instrument_market_type": instrument["market_type"]
        == CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
        "instrument_product_type": instrument["product_type"]
        == CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
        "symbol_market_type": symbol["market_type"] == CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
        "symbol_product_type": symbol["product_type"] == CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
        "venue": symbol["venue"] == CANONICAL_MARKET_IDENTITY_VENUE,
        "base_asset": instrument["base_asset"] == symbol["base_asset"] == asset,
        "quote_asset": instrument["quote_asset"]
        == symbol["quote_asset"]
        == CANONICAL_MARKET_IDENTITY_QUOTE_ASSET,
        "settlement_asset": instrument["settlement_asset"]
        == symbol["settlement_asset"]
        == CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET,
        "is_perpetual": symbol["is_perpetual"] is True,
    }
    failed = tuple(name for name, ok in checks.items() if not ok)
    if failed:
        raise ValueError(
            "strategy_validation_market_identity_manifest_not_canonical: "
            f"symbol={asset} failed_checks={failed}"
        )


def _find_symbol_mapping(session: Any, payload: dict[str, Any]) -> SymbolModel | None:
    return session.scalar(
        select(SymbolModel).where(
            SymbolModel.venue == payload["venue"],
            SymbolModel.symbol == payload["symbol"],
            SymbolModel.market_type == payload["market_type"],
            SymbolModel.product_type == payload["product_type"],
            SymbolModel.quote_asset == payload["quote_asset"],
            SymbolModel.settlement_asset == payload["settlement_asset"],
        )
    )


def _instrument_changes(model: InstrumentModel, payload: dict[str, Any]) -> bool:
    return any(getattr(model, key) != value for key, value in payload.items())


def _symbol_changes(
    model: SymbolModel,
    payload: dict[str, Any],
    instrument_ref_id: str,
    *,
    compare_raw_metadata: bool = False,
) -> bool:
    if model.instrument_ref_id != instrument_ref_id:
        return True
    for key, value in payload.items():
        if key == "raw_metadata" and not compare_raw_metadata:
            continue
        if getattr(model, key) != value:
            return True
    return False


def _apply_instrument_payload(model: InstrumentModel, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        setattr(model, key, value)


def _apply_symbol_payload(
    model: SymbolModel,
    payload: dict[str, Any],
    instrument_ref_id: str,
) -> None:
    model.instrument_ref_id = instrument_ref_id
    for key, value in payload.items():
        setattr(model, key, value)


def _conflict(
    reason_code: str,
    entry: dict[str, Any],
    *,
    requested_instrument_ref_id: str | None,
    existing_instrument_ref_id: str | None,
    existing_symbol_id: str | None,
) -> dict[str, Any]:
    symbol = entry["symbol"]
    instrument = entry["instrument"]
    return {
        "reason_code": reason_code,
        "venue": symbol["venue"],
        "symbol": symbol["symbol"],
        "instrument_key": instrument["instrument_key"],
        "requested_instrument_ref_id": requested_instrument_ref_id,
        "existing_instrument_ref_id": existing_instrument_ref_id,
        "existing_symbol_id": existing_symbol_id,
    }


def _preflight_input_path(
    path: Path,
    *,
    venue: str,
    timeframe: Timeframe | None,
    file_format: str,
    session_factory: Any,
) -> dict[str, Any]:
    rows = _load_candle_rows(path, file_format=file_format)
    row_results: list[dict[str, Any]] = []
    reason_codes: set[str] = set()
    with session_factory() as session:
        for index, row in enumerate(rows, start=1):
            row_reason_codes: set[str] = set()
            row_timeframe = timeframe
            try:
                if row_timeframe is None:
                    row_timeframe = Timeframe(_required_str(row, "timeframe"))
                parsed = _parse_candle_row(
                    row,
                    timeframe=row_timeframe,
                    assume_naive_utc=False,
                    warning_reason_codes=set(),
                )
                symbol_model = _resolve_symbol_model(
                    session=session,
                    venue=venue,
                    symbol=parsed["symbol"],
                    instrument_key=parsed.get("instrument_key"),
                )
                row_result = {
                    "row_number": index,
                    "ready": True,
                    "symbol": parsed["symbol"],
                    "instrument_key": parsed.get("instrument_key"),
                    "symbol_id": symbol_model.id,
                    "instrument_ref_id": symbol_model.instrument_ref_id,
                    "timeframe": row_timeframe.value,
                    "open_time": parsed["open_time"],
                    "close_time": parsed["close_time"],
                    "reason_codes": (),
                }
            except Exception as exc:  # noqa: BLE001 - preflight reports row failures.
                row_reason_codes.update(_reason_codes_from_preflight_error(exc))
                row_result = {
                    "row_number": index,
                    "ready": False,
                    "symbol": row.get("symbol"),
                    "instrument_key": row.get("instrument_key"),
                    "timeframe": row.get("timeframe") or getattr(row_timeframe, "value", None),
                    "reason_codes": tuple(sorted(row_reason_codes)),
                    "error_message": str(exc).splitlines()[0],
                }
            reason_codes.update(row_result["reason_codes"])
            row_results.append(row_result)
    return {
        "input_path": str(path),
        "source_file_name": path.name,
        "source_file_sha256": _sha256_file(path),
        "ready": not reason_codes,
        "row_level_ready": not reason_codes,
        "identity_ready": not reason_codes,
        "requirement_coverage_ready": None,
        "ready_for_import": not reason_codes,
        "preflight_scope": "row_level_file_shape_and_identity_only",
        "rows_seen": len(rows),
        "reason_codes": tuple(sorted(reason_codes)),
        "row_results": tuple(_json_ready(item) for item in row_results),
    }


def _load_input_requirement_mapping(
    *,
    input_paths: Sequence[str | Path],
    requirement_json_paths: Sequence[str | Path],
    input_requirement_map: dict[str, Any] | None,
    input_requirement_map_path: str | Path | None,
) -> tuple[dict[str, dict[str, Any]], tuple[dict[str, Any], ...]]:
    requirements: list[dict[str, Any]] = []
    for path in requirement_json_paths:
        requirements.extend(
            _normalise_requirement_payload(item)
            for item in _load_requirement_payloads(Path(path))
        )
    mapping_payload: dict[str, Any] = {}
    if input_requirement_map_path is not None:
        raw_mapping = json.loads(Path(input_requirement_map_path).read_text(encoding="utf-8"))
        if not isinstance(raw_mapping, dict):
            raise ValueError("input requirement map must be a JSON object keyed by input path.")
        mapping_payload.update(raw_mapping)
    if input_requirement_map:
        mapping_payload.update(input_requirement_map)

    mapping: dict[str, dict[str, Any]] = {}
    if mapping_payload:
        requirements_by_identifier = {
            _requirement_identifier(_normalise_requirement_payload(item)): item
            for item in requirements
        }
        for input_path, value in mapping_payload.items():
            if isinstance(value, dict):
                mapping[str(Path(input_path))] = _normalise_requirement_payload(value)
            elif isinstance(value, int):
                mapping[str(Path(input_path))] = requirements[value]
            elif isinstance(value, str):
                requirement = requirements_by_identifier.get(value)
                if requirement is None:
                    raise ValueError(
                        "input requirement map references unknown requirement identifier: "
                        f"{value}"
                    )
                mapping[str(Path(input_path))] = requirement
            else:
                raise ValueError(
                    "input requirement map values must be requirement objects, indexes, "
                    "or requirement identifiers."
                )
        return mapping, tuple(requirements)

    if requirement_json_paths and len(requirements) == len(input_paths):
        return {
            str(Path(input_path)): _normalise_requirement_payload(requirement)
            for input_path, requirement in zip(input_paths, requirements, strict=True)
        }, tuple(requirements)
    if requirement_json_paths and len(requirements) == 1 and len(input_paths) == 1:
        return {str(Path(input_paths[0])): requirements[0]}, tuple(requirements)
    return {}, tuple(requirements)


def _requirement_mapping_reason_codes(
    *,
    input_paths: Sequence[str | Path],
    requirement_by_input: dict[str, dict[str, Any]],
    supplied_requirements: Sequence[dict[str, Any]],
) -> set[str]:
    reason_codes: set[str] = set()
    input_keys = {str(Path(input_path)) for input_path in input_paths}
    mapped_keys = set(requirement_by_input)
    missing_input_mappings = input_keys - mapped_keys
    extra_mapped_inputs = mapped_keys - input_keys
    if missing_input_mappings:
        reason_codes.add("input_file_missing_requirement_mapping")
        reason_codes.add("requirement_mapping_incomplete")
    if extra_mapped_inputs:
        reason_codes.add("input_requirement_mapping_references_unknown_input_file")
        reason_codes.add("requirement_mapping_incomplete")

    mapped_identifiers = [
        _requirement_identifier(requirement)
        for input_key, requirement in requirement_by_input.items()
        if input_key in input_keys
    ]
    mapped_counts = Counter(mapped_identifiers)
    if any(count > 1 for count in mapped_counts.values()):
        reason_codes.add("requirement_mapped_to_multiple_input_files")
        reason_codes.add("requirement_mapping_not_one_to_one")

    if supplied_requirements:
        supplied_counts = Counter(
            _requirement_identifier(requirement) for requirement in supplied_requirements
        )
        if any(count > 1 for count in supplied_counts.values()):
            reason_codes.add("requirement_mapping_not_one_to_one")
        missing_requirements = [
            identifier
            for identifier, expected_count in supplied_counts.items()
            if mapped_counts.get(identifier, 0) < expected_count
        ]
        if missing_requirements:
            reason_codes.add("requirement_missing_input_file")
            reason_codes.add("requirement_mapping_incomplete")
    return reason_codes


def _load_requirement_payloads(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("canonical_candle_import_requirements"), list):
            candidates = payload["canonical_candle_import_requirements"]
        elif isinstance(payload.get("requirements"), list):
            candidates = payload["requirements"]
        else:
            candidates = [payload]
    else:
        raise ValueError("requirement JSON must be an object or list.")
    if not all(isinstance(item, dict) for item in candidates):
        raise ValueError("requirement JSON entries must be objects.")
    return [dict(item) for item in candidates]


def _normalise_requirement_payload(raw: dict[str, Any]) -> dict[str, Any]:
    symbol = _required_str(raw, "symbol").upper()
    instrument_key = _required_str(raw, "instrument_key")
    timeframe = Timeframe(_required_str(raw, "timeframe"))
    requested_start_at = _parse_requirement_datetime(
        _required_str(raw, "requested_start_at"),
        field="requested_start_at",
        symbol=symbol,
    )
    requested_end_at = _parse_requirement_datetime(
        _required_str(raw, "requested_end_at"),
        field="requested_end_at",
        symbol=symbol,
    )
    if requested_end_at <= requested_start_at:
        raise ValueError(
            "requirement_window_invalid: requested_end_at must be after requested_start_at "
            f"for symbol={symbol}"
        )
    expected_candle_count = raw.get("expected_candle_count")
    if expected_candle_count is None:
        raise ValueError("requirement missing expected_candle_count.")
    expected_candle_count = int(expected_candle_count)
    if expected_candle_count < 0:
        raise ValueError("requirement expected_candle_count must be >= 0.")
    return {
        "symbol": symbol,
        "instrument_key": instrument_key,
        "timeframe": timeframe,
        "requested_start_at": requested_start_at,
        "requested_end_at": requested_end_at,
        "expected_candle_count": expected_candle_count,
        "window_label": raw.get("window_label"),
    }


def _parse_requirement_datetime(value: str, *, field: str, symbol: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(
            "requirement_timestamp_timezone_required: "
            f"symbol={symbol} field={field} value={value}"
        )
    return parsed.astimezone(UTC)


def _requirement_identifier(requirement: dict[str, Any]) -> str:
    return "|".join(
        (
            requirement["symbol"],
            requirement["instrument_key"],
            requirement["timeframe"].value,
            requirement["requested_start_at"].isoformat(),
            requirement["requested_end_at"].isoformat(),
            str(requirement["expected_candle_count"]),
        )
    )


def _preflight_input_path_against_requirement(
    path: Path,
    requirement: dict[str, Any],
    *,
    venue: str,
    timeframe: Timeframe | None,
    file_format: str,
    session_factory: Any,
) -> dict[str, Any]:
    requirement = _normalise_requirement_payload(requirement)
    reason_codes: set[str] = set()
    row_reason_codes: set[str] = set()
    identity_reason_codes: set[str] = set()
    coverage_reason_codes: set[str] = set()
    row_results: list[dict[str, Any]] = []
    parsed_rows: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if not path.exists():
        reason_codes.add("requirement_input_file_missing")
        row_reason_codes.add("requirement_input_file_missing")
    else:
        try:
            rows = _load_candle_rows(path, file_format=file_format)
        except Exception as exc:  # noqa: BLE001 - preflight reports failures.
            reason_codes.add("requirement_input_file_unreadable")
            row_reason_codes.add("requirement_input_file_unreadable")
            row_results.append({"row_number": None, "ready": False, "error_message": str(exc)})

    expected_slots = _expected_close_time_slots(
        start_at=requirement["requested_start_at"],
        end_at=requirement["requested_end_at"],
        timeframe=requirement["timeframe"],
    )
    if requirement["expected_candle_count"] != len(expected_slots):
        coverage_reason_codes.add("requirement_expected_candle_count_mismatch")

    identity = canonical_market_identity_requirements(
        symbols=(
            {
                "symbol": requirement["symbol"],
                "instrument_key": requirement["instrument_key"],
            },
        ),
        venue=venue,
        session_factory=session_factory,
        schema_ready=True,
    )[0]
    if identity["market_identity_status"] != "ready":
        identity_reason_codes.update(identity["reason_codes"])
        identity_reason_codes.add("requirement_market_identity_not_ready")

    with session_factory() as session:
        for index, row in enumerate(rows, start=1):
            row_timeframe = timeframe
            row_codes: set[str] = set()
            row_validation_codes: set[str] = set()
            try:
                if row_timeframe is None:
                    raw_timeframe = row.get("timeframe")
                    row_timeframe = (
                        Timeframe(str(raw_timeframe).strip())
                        if raw_timeframe is not None and str(raw_timeframe).strip()
                        else requirement["timeframe"]
                    )
                parsed = _parse_candle_row(
                    row,
                    timeframe=row_timeframe,
                    assume_naive_utc=False,
                    warning_reason_codes=set(),
                )
                if row_timeframe != requirement["timeframe"]:
                    coverage_reason_codes.add("requirement_timeframe_mismatch")
                    row_codes.add("requirement_timeframe_mismatch")
                if parsed["symbol"] != requirement["symbol"]:
                    coverage_reason_codes.add("requirement_symbol_mismatch")
                    row_codes.add("requirement_symbol_mismatch")
                if parsed.get("instrument_key") != requirement["instrument_key"]:
                    coverage_reason_codes.add("requirement_instrument_key_mismatch")
                    row_codes.add("requirement_instrument_key_mismatch")
                symbol_model = _resolve_symbol_model(
                    session=session,
                    venue=venue,
                    symbol=parsed["symbol"],
                    instrument_key=parsed.get("instrument_key"),
                )
                if (
                    identity["instrument_ref_id"] is not None
                    and symbol_model.instrument_ref_id != identity["instrument_ref_id"]
                ):
                    identity_reason_codes.add("requirement_symbol_identity_mismatch")
                    row_codes.add("requirement_symbol_identity_mismatch")
                close_time = parsed["close_time"]
                if not (
                    requirement["requested_start_at"]
                    < close_time
                    <= requirement["requested_end_at"]
                ):
                    coverage_reason_codes.add("requirement_close_time_outside_window")
                    row_codes.add("requirement_close_time_outside_window")
                parsed_rows.append(parsed)
                row_result = {
                    "row_number": index,
                    "ready": not row_codes,
                    "symbol": parsed["symbol"],
                    "instrument_key": parsed.get("instrument_key"),
                    "timeframe": row_timeframe.value,
                    "close_time": close_time,
                    "reason_codes": tuple(sorted(row_codes)),
                }
            except Exception as exc:  # noqa: BLE001 - preflight reports row failures.
                row_validation_codes.update(_reason_codes_from_preflight_error(exc))
                row_codes.update(row_validation_codes)
                row_result = {
                    "row_number": index,
                    "ready": False,
                    "symbol": row.get("symbol"),
                    "instrument_key": row.get("instrument_key"),
                    "timeframe": row.get("timeframe") or getattr(row_timeframe, "value", None),
                    "reason_codes": tuple(sorted(row_codes)),
                    "error_message": str(exc).splitlines()[0],
                }
            row_reason_codes.update(row_validation_codes)
            row_results.append(row_result)

    close_counts: dict[datetime, int] = {}
    for parsed in parsed_rows:
        close_counts[parsed["close_time"]] = close_counts.get(parsed["close_time"], 0) + 1
    expected_slot_set = set(expected_slots)
    actual_slot_set = set(close_counts)
    duplicate_slots = sorted(
        close_time for close_time, count in close_counts.items() if count > 1
    )
    missing_slots = sorted(expected_slot_set - actual_slot_set)
    extra_slots = sorted(actual_slot_set - expected_slot_set)
    if duplicate_slots:
        coverage_reason_codes.add("requirement_duplicate_close_time_slots")
    if missing_slots:
        coverage_reason_codes.add("requirement_missing_close_time_slots")
    if extra_slots:
        coverage_reason_codes.add("requirement_extra_close_time_slots")
    if len(parsed_rows) != requirement["expected_candle_count"]:
        coverage_reason_codes.add("requirement_actual_candle_count_mismatch")

    row_level_ready = not row_reason_codes
    identity_ready = not identity_reason_codes
    requirement_coverage_ready = not coverage_reason_codes and row_level_ready
    ready_for_import = row_level_ready and identity_ready and requirement_coverage_ready
    reason_codes.update(row_reason_codes)
    reason_codes.update(identity_reason_codes)
    reason_codes.update(coverage_reason_codes)
    return {
        "input_path": str(path),
        "source_file_name": path.name,
        "source_file_sha256": _sha256_file(path) if path.exists() else None,
        "requirement_identifier": _requirement_identifier(requirement),
        "symbol": requirement["symbol"],
        "instrument_key": requirement["instrument_key"],
        "timeframe": requirement["timeframe"].value,
        "requested_start_at": requirement["requested_start_at"],
        "requested_end_at": requirement["requested_end_at"],
        "window_label": requirement["window_label"],
        "row_level_ready": row_level_ready,
        "identity_ready": identity_ready,
        "requirement_coverage_ready": requirement_coverage_ready,
        "ready_for_import": ready_for_import,
        "expected_candle_count": requirement["expected_candle_count"],
        "expected_close_time_slots": tuple(expected_slots),
        "actual_candle_count": len(parsed_rows),
        "missing_close_time_slots": tuple(missing_slots),
        "duplicate_close_time_slots": tuple(duplicate_slots),
        "extra_close_time_slots": tuple(extra_slots),
        "market_identity_status": identity["market_identity_status"],
        "row_results": tuple(_json_ready(item) for item in row_results),
        "reason_codes": tuple(sorted(reason_codes)),
    }


def _expected_close_time_slots(
    *,
    start_at: datetime,
    end_at: datetime,
    timeframe: Timeframe,
) -> tuple[datetime, ...]:
    duration = _timeframe_duration(timeframe)
    slots: list[datetime] = []
    cursor = start_at + duration
    while cursor <= end_at:
        slots.append(cursor)
        cursor += duration
    return tuple(slots)


def _preflight_supplied_candle_requirements(
    requirements: Sequence[dict[str, Any]],
    *,
    venue: str,
    session_factory: Any,
) -> tuple[dict[str, Any], ...]:
    results: list[dict[str, Any]] = []
    for raw in requirements:
        requirement = _normalise_requirement_payload(raw)
        identity = canonical_market_identity_requirements(
            symbols=(
                {
                    "symbol": requirement["symbol"],
                    "instrument_key": requirement["instrument_key"],
                },
            ),
            venue=venue,
            session_factory=session_factory,
            schema_ready=True,
        )[0]
        results.append(
            {
                **identity,
                "ready": identity["market_identity_status"] == "ready",
                "requirement_kind": "canonical_candle_import_requirements",
                "requirement_identifier": _requirement_identifier(requirement),
                "timeframe": requirement["timeframe"].value,
                "requested_start_at": requirement["requested_start_at"],
                "requested_end_at": requirement["requested_end_at"],
                "window_label": requirement["window_label"],
                "window_labels": None,
                "expected_candle_count": requirement["expected_candle_count"],
                "actual_candle_count": None,
                "missing_candle_count": None,
            }
        )
    return tuple(results)


def _preflight_requirements_from_review_json(
    path: Path,
    *,
    venue: str,
    session_factory: Any,
) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    requirement_kind = "canonical_candle_import_requirements"
    requirements = payload.get(requirement_kind)
    if requirements is None:
        requirement_kind = "canonical_market_identity_requirements"
        requirements = payload.get(requirement_kind)
    if not isinstance(requirements, list):
        raise ValueError(
            "requirements review JSON must contain canonical_market_identity_requirements "
            "or canonical_candle_import_requirements."
        )
    results: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict) or not item.get("symbol"):
            continue
        identity = canonical_market_identity_requirements(
            symbols=(
                {
                    "symbol": str(item.get("symbol")),
                    "instrument_key": item.get("instrument_key"),
                },
            ),
            venue=venue,
            session_factory=session_factory,
            schema_ready=True,
        )[0]
        results.append(
            {
                **identity,
                "ready": identity["market_identity_status"] == "ready",
                "requirement_kind": requirement_kind,
                "requirement_identifier": (
                    _requirement_identifier(_normalise_requirement_payload(item))
                    if requirement_kind == "canonical_candle_import_requirements"
                    and item.get("timeframe")
                    and item.get("requested_start_at")
                    and item.get("requested_end_at")
                    and item.get("expected_candle_count") is not None
                    else None
                ),
                "timeframe": item.get("timeframe"),
                "requested_start_at": item.get("requested_start_at"),
                "requested_end_at": item.get("requested_end_at"),
                "window_label": item.get("window_label"),
                "window_labels": item.get("window_labels"),
                "expected_candle_count": item.get("expected_candle_count"),
                "actual_candle_count": item.get("actual_candle_count"),
                "missing_candle_count": item.get("missing_candle_count"),
            }
        )
    return tuple(results)


def _reason_codes_from_preflight_error(exc: Exception) -> tuple[str, ...]:
    message = str(exc)
    reason_codes: set[str] = set()
    for code in (
        "candle_import_naive_timestamp",
        "timezone_required_for_candle_import",
        "candle_import_timeframe_duration_mismatch",
        "candle_import_invalid_ohlcv",
        "unknown_instrument_key",
        "unknown_symbol_mapping",
        "ambiguous_symbol_mapping",
    ):
        if code in message:
            reason_codes.add(code)
    if "missing required field" in message:
        reason_codes.add("missing_required_candle_field")
    if "unknown symbol mapping" in message:
        reason_codes.add("unknown_symbol_mapping")
    if "unknown instrument_key" in message:
        reason_codes.add("unknown_instrument_key")
    if not reason_codes:
        reason_codes.add("candle_import_preflight_failed")
    return tuple(sorted(reason_codes))


def _missing_required_symbols(entries: Sequence[dict[str, Any]]) -> tuple[str, ...]:
    seen = {entry["symbol"]["symbol"] for entry in entries}
    return tuple(symbol for symbol in CANONICAL_MARKET_IDENTITY_SYMBOLS if symbol not in seen)


def _manifest_venue(entries: Sequence[dict[str, Any]]) -> str:
    venues = sorted({entry["symbol"]["venue"] for entry in entries})
    return venues[0] if venues else CANONICAL_MARKET_IDENTITY_VENUE


def _required_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"strategy validation market identity missing required field: {key}")
    return str(value).strip()


def _optional_str(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _required_bool(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    if isinstance(value, bool):
        return value
    raise ValueError(f"strategy validation market identity field {key} must be boolean.")


def _optional_int(row: dict[str, Any], key: str, *, minimum: int) -> int | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except Exception as exc:  # noqa: BLE001 - field context is more useful.
        raise ValueError(
            f"strategy validation market identity field {key} must be integer-compatible."
        ) from exc
    if parsed < minimum:
        raise ValueError(
            f"strategy validation market identity field {key} must be >= {minimum}."
        )
    return parsed


def _positive_decimal(row: dict[str, Any], key: str) -> Decimal:
    value = row.get(key)
    try:
        parsed = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001 - field context is more useful.
        raise ValueError(
            f"strategy validation market identity field {key} must be Decimal-compatible."
        ) from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(
            f"strategy validation market identity field {key} must be finite and > 0."
        )
    return parsed


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


__all__ = [
    "CANONICAL_MARKET_IDENTITY_SYMBOLS",
    "StrategyValidationCandleImportPreflightResult",
    "StrategyValidationMarketIdentitySeedResult",
    "canonical_market_identity_instrument_key",
    "canonical_market_identity_requirements",
    "preflight_strategy_validation_candle_import",
    "seed_strategy_validation_market_identity_from_manifest",
    "strategy_validation_candle_import_preflight_result_to_dict",
    "strategy_validation_candle_import_preflight_result_to_json",
    "strategy_validation_candle_import_preflight_result_to_markdown",
    "strategy_validation_market_identity_seed_result_to_dict",
    "strategy_validation_market_identity_seed_result_to_json",
    "strategy_validation_market_identity_seed_result_to_markdown",
]
