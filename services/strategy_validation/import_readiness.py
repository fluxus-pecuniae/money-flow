"""SV1.12.2 identity and canonical candle-file readiness helpers."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import select

from core.domain.enums import Environment, Timeframe
from db.models import InstrumentModel, SymbolModel
from db.session import SessionLocal
from services.strategy_validation.evidence_review import (
    CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
    money_flow_evidence_review_to_dict,
    review_money_flow_evidence,
)
from services.strategy_validation.market_identity import (
    CANONICAL_MARKET_IDENTITY_MARKET_TYPE,
    CANONICAL_MARKET_IDENTITY_PRODUCT_TYPE,
    CANONICAL_MARKET_IDENTITY_QUOTE_ASSET,
    CANONICAL_MARKET_IDENTITY_SETTLEMENT_ASSET,
    CANONICAL_MARKET_IDENTITY_SYMBOLS,
    CANONICAL_MARKET_IDENTITY_VENUE,
    StrategyValidationCandleImportPreflightResult,
    canonical_market_identity_instrument_key,
    preflight_strategy_validation_candle_import,
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_candle_import_preflight_result_to_dict,
    strategy_validation_market_identity_seed_result_to_dict,
)
from services.strategy_validation.service import MoneyFlowBacktestService

DEFAULT_MARKET_IDENTITY_MANIFEST_PATH = Path(
    "configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json"
)
EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT = 18
CANONICAL_CANDLE_REQUIRED_COLUMNS = (
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
)
CANONICAL_TIMESTAMP_REQUIREMENT = (
    "timezone-explicit ISO-8601 timestamps ending in Z or carrying an explicit UTC offset; "
    "timezone-naive timestamps are rejected for canonical import."
)


@dataclass(frozen=True, slots=True)
class StrategyValidationImportReadinessResult:
    generated_at_utc: datetime
    database_status: dict[str, Any]
    market_identity_manifest_path: str
    market_identity_seed_attempted: bool
    market_identity_seeded: bool
    operator_verified: bool
    verified_by: str | None
    identity_seed_status: str
    identity_seed_summary: dict[str, Any] | None
    identity_verification_checklist: tuple[dict[str, Any], ...]
    operator_verified_market_identity_requirements: tuple[dict[str, Any], ...]
    canonical_candle_file_requirements: tuple[dict[str, Any], ...]
    expected_canonical_requirement_count: int
    actual_canonical_requirement_count: int
    canonical_requirement_count_matches_expected: bool
    available_input_files: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]
    missing_suggested_filenames: tuple[str, ...]
    preflight_run: bool
    preflight_summary: dict[str, Any] | None
    ready_for_sv1123_guarded_import: bool
    candles_imported: bool
    evidence_packs_generated: bool
    creates_live_artifacts: bool
    calls_exchange_adapters: bool
    calls_private_exchange_endpoints: bool
    calls_exchange_order_endpoints: bool
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]


def evaluate_strategy_validation_import_readiness(
    *,
    service: MoneyFlowBacktestService | None = None,
    session_factory: Any = SessionLocal,
    manifest_path: str | Path = DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    seed_identity: bool = False,
    operator_verified: bool = False,
    verified_by: str | None = None,
    input_paths: Sequence[str | Path] = (),
    requirements_from_review_json: str | Path | None = None,
    requirement_json_paths: Sequence[str | Path] = (),
    input_requirement_map: dict[str, Any] | None = None,
    input_requirement_map_path: str | Path | None = None,
    environment: Environment | str = Environment.TESTNET,
    venue: str = CANONICAL_MARKET_IDENTITY_VENUE,
    timeframe: Timeframe | None = None,
    file_format: str = "auto",
    generated_at: datetime | None = None,
) -> StrategyValidationImportReadinessResult:
    """Report identity/file readiness without importing candles or generating evidence packs."""

    generated_at_utc = _coerce_utc(generated_at or datetime.now(UTC)).replace(microsecond=0)
    validation_service = service or MoneyFlowBacktestService()
    manifest = Path(manifest_path)
    warnings: set[str] = set()
    reason_codes: set[str] = set()

    seed_summary: dict[str, Any] | None = None
    seed_attempted = False
    seed_written = False
    identity_seed_status = "not_requested"
    if seed_identity:
        seed_attempted = True
        if not operator_verified:
            identity_seed_status = "blocked_operator_verification_required"
            reason_codes.add("market_identity_operator_verification_required")
            warnings.add("identity_seed_not_run_without_operator_verification")
        elif not verified_by:
            identity_seed_status = "blocked_verified_by_required"
            reason_codes.add("market_identity_verified_by_required")
            warnings.add("identity_seed_not_run_without_verified_by")
        else:
            seed_result = seed_strategy_validation_market_identity_from_manifest(
                manifest,
                operator_verified=True,
                verified_by=verified_by,
                session_factory=session_factory,
            )
            seed_summary = strategy_validation_market_identity_seed_result_to_dict(
                seed_result
            )
            seed_written = not seed_summary["conflicts"]
            identity_seed_status = "seeded" if seed_written else "blocked_by_conflicts"
            if seed_summary["conflicts"]:
                reason_codes.add("market_identity_seed_conflicts")
    else:
        warnings.add("market_identity_seed_not_requested")

    review = review_money_flow_evidence(
        CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS,
        service=validation_service,
        generate_evidence_packs=False,
        generated_at=generated_at_utc,
    )
    review_payload = money_flow_evidence_review_to_dict(review)
    db_status = review_payload["database_status"]
    candle_requirements = _canonical_candle_file_requirements(
        review_payload["canonical_candle_import_requirements"]
    )
    if len(candle_requirements) != EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT:
        reason_codes.add("canonical_candle_requirement_count_unexpected")

    identity_requirements = _operator_verified_identity_requirements(
        candle_requirements,
        venue=venue,
        session_factory=session_factory,
    )
    identity_ready = bool(identity_requirements) and all(
        item["operator_verified_market_identity_status"] == "ready"
        for item in identity_requirements
    )
    if not identity_ready:
        reason_codes.add("operator_verified_research_market_identity_not_ready")
    checklist = _identity_verification_checklist(
        manifest,
        identity_requirements=identity_requirements,
        operator_verified=operator_verified,
        verified_by=verified_by,
    )

    input_path_strings = tuple(str(Path(path)) for path in input_paths)
    preflight_result: StrategyValidationCandleImportPreflightResult | None = None
    preflight_payload: dict[str, Any] | None = None
    if input_paths or requirements_from_review_json is not None or requirement_json_paths:
        preflight_result = preflight_strategy_validation_candle_import(
            input_paths=input_paths,
            requirements_from_review_json=requirements_from_review_json,
            requirement_json_paths=requirement_json_paths,
            input_requirement_map=input_requirement_map,
            input_requirement_map_path=input_requirement_map_path,
            environment=(
                environment.value if isinstance(environment, Environment) else str(environment)
            ),
            venue=venue,
            timeframe=timeframe,
            file_format=file_format,
            session_factory=session_factory,
        )
        preflight_payload = strategy_validation_candle_import_preflight_result_to_dict(
            preflight_result
        )
        reason_codes.update(preflight_payload["reason_codes"])
    else:
        warnings.add("canonical_candle_files_not_supplied")
        reason_codes.add("canonical_candle_files_missing")

    covered_requirement_ids = _covered_requirement_ids(preflight_payload)
    all_requirement_ids = tuple(item["requirement_identifier"] for item in candle_requirements)
    missing_requirement_ids = tuple(
        identifier for identifier in all_requirement_ids if identifier not in covered_requirement_ids
    )
    missing_suggested_filenames = tuple(
        item["suggested_filename"]
        for item in candle_requirements
        if item["requirement_identifier"] in set(missing_requirement_ids)
    )
    if missing_requirement_ids:
        reason_codes.add("canonical_candle_files_missing")
        reason_codes.add("canonical_candle_requirement_preflight_incomplete")

    preflight_ready = bool(preflight_payload and preflight_payload["ready"])
    ready_for_guarded_import = (
        identity_ready
        and not missing_requirement_ids
        and preflight_ready
        and len(candle_requirements) == EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT
    )
    if not ready_for_guarded_import:
        reason_codes.add("sv1123_guarded_import_not_ready")

    return StrategyValidationImportReadinessResult(
        generated_at_utc=generated_at_utc,
        database_status=_json_ready(db_status),
        market_identity_manifest_path=str(manifest),
        market_identity_seed_attempted=seed_attempted,
        market_identity_seeded=seed_written,
        operator_verified=operator_verified,
        verified_by=verified_by,
        identity_seed_status=identity_seed_status,
        identity_seed_summary=_json_ready(seed_summary) if seed_summary else None,
        identity_verification_checklist=tuple(_json_ready(item) for item in checklist),
        operator_verified_market_identity_requirements=tuple(
            _json_ready(item) for item in identity_requirements
        ),
        canonical_candle_file_requirements=tuple(
            _json_ready(item) for item in candle_requirements
        ),
        expected_canonical_requirement_count=EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT,
        actual_canonical_requirement_count=len(candle_requirements),
        canonical_requirement_count_matches_expected=(
            len(candle_requirements) == EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT
        ),
        available_input_files=input_path_strings,
        missing_requirement_ids=missing_requirement_ids,
        missing_suggested_filenames=missing_suggested_filenames,
        preflight_run=preflight_result is not None,
        preflight_summary=_json_ready(preflight_payload) if preflight_payload else None,
        ready_for_sv1123_guarded_import=ready_for_guarded_import,
        candles_imported=False,
        evidence_packs_generated=False,
        creates_live_artifacts=False,
        calls_exchange_adapters=False,
        calls_private_exchange_endpoints=False,
        calls_exchange_order_endpoints=False,
        reason_codes=tuple(sorted(reason_codes)),
        warnings=tuple(sorted(warnings)),
    )


def strategy_validation_import_readiness_to_dict(
    result: StrategyValidationImportReadinessResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_import_readiness_to_json(
    result: StrategyValidationImportReadinessResult,
) -> str:
    return json.dumps(
        strategy_validation_import_readiness_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_import_readiness_to_markdown(
    result: StrategyValidationImportReadinessResult,
) -> str:
    payload = strategy_validation_import_readiness_to_dict(result)
    db = payload["database_status"]
    lines = [
        "# SV1.12.2 Identity And Canonical Candle-File Readiness",
        "",
        "This readiness report is research-only. It can verify/seed operator-confirmed "
        "market identity and preflight supplied candle files, but it does not import candles "
        "and does not generate evidence packs.",
        "",
        "## Summary",
        "",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- DB target: `{db.get('configured_database_url')}`",
        f"- DB reachable: `{db.get('reachable')}`",
        f"- Schema status: `{db.get('schema_status')}`",
        f"- Persisted candle count: `{db.get('persisted_candle_count')}`",
        f"- Identity seed attempted: `{payload['market_identity_seed_attempted']}`",
        f"- Identity seed status: `{payload['identity_seed_status']}`",
        f"- Operator verified: `{payload['operator_verified']}`",
        f"- Verified by: `{payload['verified_by']}`",
        f"- Canonical requirements: `{payload['actual_canonical_requirement_count']}` / `{payload['expected_canonical_requirement_count']}`",
        f"- Available input files supplied: `{len(payload['available_input_files'])}`",
        f"- Missing requirement files: `{len(payload['missing_requirement_ids'])}`",
        f"- Preflight run: `{payload['preflight_run']}`",
        f"- Ready for SV1.12.3 guarded import: `{payload['ready_for_sv1123_guarded_import']}`",
        f"- Candles imported: `{payload['candles_imported']}`",
        f"- Evidence packs generated: `{payload['evidence_packs_generated']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        "",
        "## Market Identity",
        "",
        "| symbol | instrument key | status | strategy eligible | trading eligible | reason codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["operator_verified_market_identity_requirements"]:
        lines.append(
            f"| `{item['symbol']}` | `{item['instrument_key']}` | "
            f"`{item['operator_verified_market_identity_status']}` | "
            f"`{item['is_strategy_eligible']}` | `{item['is_trading_eligible']}` | "
            f"`{item['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Identity Verification Checklist",
            "",
            "| symbol | required checks | seed allowed | reason codes |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload["identity_verification_checklist"]:
        lines.append(
            f"| `{item['symbol']}` | `{', '.join(item['required_checks'])}` | "
            f"`{item['seed_allowed']}` | `{item['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Canonical Candle File Requirements",
            "",
            "Every canonical file must use the `(start_at, end_at]` close-time convention and timezone-explicit timestamps.",
            "",
            "| requirement id | suggested filename | symbol | timeframe | component | window | expected | impacted campaigns |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["canonical_candle_file_requirements"]:
        lines.append(
            f"| `{item['requirement_identifier']}` | `{item['suggested_filename']}` | "
            f"`{item['symbol']}` | `{item['timeframe']}` | `{item['component']}` | "
            f"`({item['requested_start_at']}, {item['requested_end_at']}]` | "
            f"`{item['expected_candle_count']}` | `{item['campaigns_impacted']}` |"
        )
    lines.extend(
        [
            "",
            "## File Requirements",
            "",
            f"- Timestamp requirement: `{CANONICAL_TIMESTAMP_REQUIREMENT}`",
            f"- Required columns: `{CANONICAL_CANDLE_REQUIRED_COLUMNS}`",
            "- Required file format: `CSV or JSON accepted by scripts/import_strategy_validation_candles.py`",
            "- Requirement-aware preflight must pass before guarded import.",
            "- Row-level preflight alone is not canonical coverage proof.",
            "",
            "## Available Files And Preflight",
            "",
        ]
    )
    if payload["available_input_files"]:
        for path in payload["available_input_files"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- No canonical candle input files were supplied to this readiness run.")
    if payload["preflight_summary"] is not None:
        lines.extend(
            [
                "",
                f"- Preflight ready: `{payload['preflight_summary']['ready']}`",
                f"- Preflight reason codes: `{payload['preflight_summary']['reason_codes']}`",
            ]
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
            "- No Money Flow rules were changed.",
            "- No candle rows are imported by this readiness report.",
            "- No evidence packs are generated by this readiness report.",
        ]
    )
    return "\n".join(lines) + "\n"


def _canonical_candle_file_requirements(
    raw_requirements: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for raw in raw_requirements:
        symbol = str(raw["symbol"]).upper()
        timeframe = str(raw["timeframe"])
        start_at = str(raw["requested_start_at"])
        end_at = str(raw["requested_end_at"])
        expected = int(raw["expected_candle_count"])
        instrument_key = str(
            raw.get("instrument_key") or canonical_market_identity_instrument_key(symbol)
        )
        components = tuple(raw.get("components") or (raw.get("component"),))
        window_labels = tuple(raw.get("window_labels") or (raw.get("window_label"),))
        campaigns = tuple(raw.get("campaigns_impacted") or raw.get("campaign_names") or ())
        config_paths = tuple(raw.get("config_paths") or (raw.get("config_path"),))
        identifier = _requirement_identifier(
            symbol=symbol,
            instrument_key=instrument_key,
            timeframe=timeframe,
            requested_start_at=start_at,
            requested_end_at=end_at,
            expected_candle_count=expected,
        )
        rows.append(
            {
                "requirement_identifier": identifier,
                "symbol": symbol,
                "instrument_key": instrument_key,
                "timeframe": timeframe,
                "component": components[0],
                "components": tuple(item for item in components if item),
                "window_label": window_labels[0],
                "window_labels": tuple(item for item in window_labels if item),
                "requested_start_at": start_at,
                "requested_end_at": end_at,
                "window_convention": "(start_at, end_at]",
                "expected_candle_count": expected,
                "actual_candle_count": int(raw.get("actual_candle_count") or 0),
                "missing_candle_count": int(raw.get("missing_candle_count") or expected),
                "required_timestamp_format": CANONICAL_TIMESTAMP_REQUIREMENT,
                "required_file_format": "CSV or JSON",
                "required_columns": CANONICAL_CANDLE_REQUIRED_COLUMNS,
                "suggested_filename": _suggested_filename(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_at=start_at,
                    end_at=end_at,
                ),
                "campaigns_impacted": campaigns,
                "config_paths": config_paths,
                "example_import_command": raw.get("example_import_command"),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["symbol"]),
            str(item["timeframe"]),
            str(item["requested_start_at"]),
            str(item["requested_end_at"]),
        )
    )
    return tuple(rows)


def _operator_verified_identity_requirements(
    candle_requirements: Sequence[dict[str, Any]],
    *,
    venue: str,
    session_factory: Any,
) -> tuple[dict[str, Any], ...]:
    unique = {
        (str(item["symbol"]), str(item["instrument_key"]))
        for item in candle_requirements
    }
    rows: list[dict[str, Any]] = []
    with session_factory() as session:
        for symbol, instrument_key in sorted(unique):
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
            metadata = dict(getattr(symbol_model, "raw_metadata", None) or {})
            if symbol_model is not None:
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
            if not reason_codes:
                status = "ready"
            elif (
                "strategy_validation_identity_strategy_eligible" in reason_codes
                or "strategy_validation_identity_trading_eligible" in reason_codes
            ):
                status = "not_research_only_non_trading"
            elif "market_identity_symbol_instrument_conflict" in reason_codes:
                status = "conflict"
            elif "missing_instrument" in reason_codes or "missing_symbol_mapping" in reason_codes:
                status = "missing_market_identity"
            else:
                status = "operator_verification_missing"
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


def _identity_verification_checklist(
    manifest_path: Path,
    *,
    identity_requirements: Sequence[dict[str, Any]],
    operator_verified: bool,
    verified_by: str | None,
) -> tuple[dict[str, Any], ...]:
    manifest_payload: dict[str, Any] = {}
    if manifest_path.exists():
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_markets = {
        str(item.get("instrument", {}).get("canonical_symbol", "")).upper(): item
        for item in manifest_payload.get("markets", [])
        if isinstance(item, dict)
    }
    checklist: list[dict[str, Any]] = []
    by_symbol = {item["symbol"]: item for item in identity_requirements}
    required_checks = (
        "instrument_key",
        "canonical_symbol",
        "venue_symbol",
        "exchange_symbol",
        "market_type",
        "product_type",
        "base_asset",
        "quote_asset",
        "settlement_asset",
        "price_tick_size",
        "quantity_step_size",
        "min_order_size",
        "size_decimals",
        "max_leverage_if_present",
        "isolated_cross_constraints",
        "venue_asset_id_or_asset_id_if_present",
        "operator_verified",
        "verified_by",
        "verified_at",
        "non_trading_non_strategy_eligible",
    )
    for symbol in CANONICAL_MARKET_IDENTITY_SYMBOLS:
        requirement = by_symbol.get(symbol)
        reason_codes: set[str] = set()
        if symbol not in manifest_markets:
            reason_codes.add("market_identity_manifest_symbol_missing")
        if not operator_verified:
            reason_codes.add("market_identity_operator_verification_required")
        if operator_verified and not verified_by:
            reason_codes.add("market_identity_verified_by_required")
        if requirement is None or requirement["operator_verified_market_identity_status"] != "ready":
            reason_codes.add("operator_verified_research_market_identity_not_ready")
            if requirement is not None:
                reason_codes.update(requirement["reason_codes"])
        checklist.append(
            {
                "symbol": symbol,
                "instrument_key": canonical_market_identity_instrument_key(symbol),
                "required_checks": required_checks,
                "seed_allowed": not reason_codes,
                "manifest_entry_present": symbol in manifest_markets,
                "operator_verified": operator_verified,
                "verified_by": verified_by,
                "reason_codes": tuple(sorted(reason_codes)),
            }
        )
    return tuple(checklist)


def _covered_requirement_ids(preflight_payload: dict[str, Any] | None) -> set[str]:
    if not preflight_payload:
        return set()
    return {
        str(item["requirement_identifier"])
        for item in preflight_payload.get("requirement_aware_results", [])
        if item.get("ready_for_import") is True
    }


def _requirement_identifier(
    *,
    symbol: str,
    instrument_key: str,
    timeframe: str,
    requested_start_at: str,
    requested_end_at: str,
    expected_candle_count: int,
) -> str:
    return "|".join(
        (
            symbol,
            instrument_key,
            timeframe,
            requested_start_at,
            requested_end_at,
            str(expected_candle_count),
        )
    )


def _suggested_filename(
    *,
    symbol: str,
    timeframe: str,
    start_at: str,
    end_at: str,
) -> str:
    start_slug = _datetime_filename_slug(start_at)
    end_slug = _datetime_filename_slug(end_at)
    return f"hyperliquid_{symbol.lower()}_{timeframe}_{start_slug}_{end_slug}.csv"


def _datetime_filename_slug(value: str) -> str:
    cleaned = value.replace("+00:00", "Z")
    cleaned = re.sub(r"[^0-9TZ]", "", cleaned)
    return cleaned.replace("T", "_").replace("Z", "z")


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
    "CANONICAL_CANDLE_REQUIRED_COLUMNS",
    "CANONICAL_TIMESTAMP_REQUIREMENT",
    "DEFAULT_MARKET_IDENTITY_MANIFEST_PATH",
    "EXPECTED_CANONICAL_CANDLE_REQUIREMENT_COUNT",
    "StrategyValidationImportReadinessResult",
    "evaluate_strategy_validation_import_readiness",
    "strategy_validation_import_readiness_to_dict",
    "strategy_validation_import_readiness_to_json",
    "strategy_validation_import_readiness_to_markdown",
]
