"""SV1.12.5 Hyperliquid public campaign seed/preflight/import workflow."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from core.domain.enums import Environment, Timeframe
from db.session import SessionLocal
from services.strategy_validation.candle_bundle_import import (
    StrategyValidationCanonicalCandleBundleImportResult,
    guarded_import_strategy_validation_candle_bundle,
    strategy_validation_canonical_candle_bundle_import_result_to_dict,
)
from services.strategy_validation.candles import (
    _load_candle_rows,
    _parse_candle_row,
    _timeframe_duration,
)
from services.strategy_validation.evidence_review import (
    inspect_strategy_validation_database_status,
    money_flow_evidence_review_database_status_to_dict,
)
from services.strategy_validation.import_readiness import (
    CANONICAL_CANDLE_REQUIRED_COLUMNS,
    CANONICAL_TIMESTAMP_REQUIREMENT,
    DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    _operator_verified_identity_requirements,
)
from services.strategy_validation.market_identity import (
    seed_strategy_validation_market_identity_from_manifest,
    strategy_validation_market_identity_seed_result_to_dict,
)
from services.strategy_validation.service import MoneyFlowBacktestService


PUBLIC_CAMPAIGN_CONFIG_PATH = Path(
    "configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json"
)
EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT = 9
PUBLIC_CAMPAIGN_SOURCE_LABEL_PREFIX = "hyperliquid_public_ytd_recent_candle_bundle"


@dataclass(frozen=True, slots=True)
class StrategyValidationPublicCampaignImportResult:
    generated_at_utc: datetime
    campaign_config_path: str
    campaign_name: str
    environment: str
    venue: str
    operator_verified: bool
    verified_by: str | None
    market_identity_values_checked_offline: bool
    identity_seed_approved: bool
    identity_seed_requested: bool
    identity_seed_attempted: bool
    identity_seeded: bool
    identity_seed_status: str
    identity_seed_summary: dict[str, Any] | None
    database_status: dict[str, Any]
    public_requirements_expected: int
    public_requirements_seen: int
    public_campaign_uses_9_file_expectation: bool
    january_18_file_campaign_used: bool
    public_candle_file_requirements: tuple[dict[str, Any], ...]
    input_directory: str | None
    input_files_found: tuple[str, ...]
    input_files_missing: tuple[str, ...]
    input_requirement_map: dict[str, str]
    public_file_coverage_results: tuple[dict[str, Any], ...]
    identity_readiness_results: tuple[dict[str, Any], ...]
    guarded_import: dict[str, Any]
    final_status: str
    sv113_evidence_review_can_proceed: bool
    candles_imported: bool
    evidence_packs_generated: bool
    supported_venue_inventory: tuple[dict[str, Any], ...]
    creates_live_artifacts: bool
    calls_exchange_adapters: bool
    calls_private_exchange_endpoints: bool
    calls_exchange_order_endpoints: bool
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]


def run_strategy_validation_public_campaign_import(
    *,
    campaign_config_path: str | Path = PUBLIC_CAMPAIGN_CONFIG_PATH,
    manifest_path: str | Path = DEFAULT_MARKET_IDENTITY_MANIFEST_PATH,
    seed_identity: bool = False,
    operator_verified: bool = False,
    verified_by: str | None = None,
    market_identity_values_checked_offline: bool = False,
    input_paths: Sequence[str | Path] = (),
    input_dir: str | Path | None = None,
    regenerate_missing_public_candles: bool = False,
    environment: Environment | str = Environment.TESTNET,
    venue: str | None = None,
    file_format: str = "auto",
    source_label_prefix: str = PUBLIC_CAMPAIGN_SOURCE_LABEL_PREFIX,
    service: MoneyFlowBacktestService | None = None,
    session_factory: Any = SessionLocal,
    generated_at: datetime | None = None,
) -> StrategyValidationPublicCampaignImportResult:
    """Seed/preflight/import the SV1.12.5 Hyperliquid public campaign if safe."""

    generated_at_utc = _coerce_utc(generated_at or datetime.now(UTC)).replace(
        microsecond=0
    )
    validation_service = service or MoneyFlowBacktestService()
    campaign_path = Path(campaign_config_path)
    config = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign_name = str(config["campaign_name"])
    campaign_venue = venue or str(config.get("venue") or "hyperliquid")
    environment_value = (
        environment.value if isinstance(environment, Environment) else str(environment)
    )
    input_directory = Path(input_dir) if input_dir is not None else _config_input_dir(config)
    reason_codes: set[str] = set()
    warnings: set[str] = set()

    requirements = build_public_campaign_candle_requirements(
        campaign_config_path=campaign_path
    )
    if len(requirements) != EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT:
        reason_codes.add("public_campaign_requirement_count_unexpected")
    if len(requirements) == 18:
        reason_codes.add("january_18_file_campaign_used_for_public_import")

    seed_summary: dict[str, Any] | None = None
    seed_attempted = False
    seed_written = False
    identity_seed_status = "not_requested"
    seed_allowed = (
        seed_identity
        and operator_verified
        and bool(verified_by)
        and market_identity_values_checked_offline
    )
    if seed_identity:
        if not operator_verified:
            identity_seed_status = "blocked_operator_verification_required"
            reason_codes.add("market_identity_operator_verification_required")
            warnings.add("identity_seed_not_run_without_operator_verification")
        elif not verified_by:
            identity_seed_status = "blocked_verified_by_required"
            reason_codes.add("market_identity_verified_by_required")
            warnings.add("identity_seed_not_run_without_verified_by")
        elif not market_identity_values_checked_offline:
            identity_seed_status = "blocked_offline_value_confirmation_required"
            reason_codes.add("market_identity_values_offline_confirmation_required")
            warnings.add("identity_seed_not_run_without_offline_value_confirmation")
        else:
            seed_attempted = True
            seed_result = seed_strategy_validation_market_identity_from_manifest(
                manifest_path,
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

    if seed_identity and not seed_allowed:
        seed_written = False

    if regenerate_missing_public_candles and input_directory is not None:
        regenerate_results = regenerate_missing_hyperliquid_public_candles(
            requirements=requirements,
            output_dir=input_directory,
        )
        for item in regenerate_results:
            if not item["generated"]:
                reason_codes.add("public_candle_regeneration_incomplete")
                warnings.add(str(item["reason_code"]))

    resolved_inputs, input_map, missing_files = _resolve_public_input_files(
        requirements=requirements,
        input_paths=input_paths,
        input_dir=input_directory,
    )
    if missing_files:
        reason_codes.add("public_campaign_candle_files_missing")
        reason_codes.add("public_campaign_requirement_preflight_incomplete")

    db_status = money_flow_evidence_review_database_status_to_dict(
        inspect_strategy_validation_database_status(validation_service)
    )
    identity_requirements = _operator_verified_identity_requirements(
        requirements,
        venue=campaign_venue,
        session_factory=session_factory,
    )
    identity_ready = all(
        item["operator_verified_market_identity_status"] == "ready"
        for item in identity_requirements
    )
    if not identity_ready:
        reason_codes.add("operator_verified_research_market_identity_not_ready")

    coverage_results = tuple(
        _file_coverage_result(
            requirement=requirement,
            input_path=_path_for_requirement(requirement, resolved_inputs),
            file_format=file_format,
        )
        for requirement in requirements
    )

    with tempfile.TemporaryDirectory(prefix="money_flow_sv1125_requirements_") as temp_dir:
        requirement_path = Path(temp_dir) / "public_campaign_candle_requirements.json"
        requirement_path.write_text(
            json.dumps(
                {"canonical_candle_import_requirements": list(requirements)},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        import_result = guarded_import_strategy_validation_candle_bundle(
            input_paths=resolved_inputs,
            requirement_json_paths=(requirement_path,),
            input_requirement_map=input_map,
            environment=Environment(environment_value),
            venue=campaign_venue,
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
        import_result=import_result,
        identity_ready=identity_ready,
        missing_files=missing_files,
        requirements=requirements,
    )
    return StrategyValidationPublicCampaignImportResult(
        generated_at_utc=generated_at_utc,
        campaign_config_path=str(campaign_path),
        campaign_name=campaign_name,
        environment=environment_value,
        venue=campaign_venue,
        operator_verified=operator_verified,
        verified_by=verified_by,
        market_identity_values_checked_offline=market_identity_values_checked_offline,
        identity_seed_approved=seed_allowed,
        identity_seed_requested=seed_identity,
        identity_seed_attempted=seed_attempted,
        identity_seeded=seed_written,
        identity_seed_status=identity_seed_status,
        identity_seed_summary=_json_ready(seed_summary) if seed_summary else None,
        database_status=_json_ready(db_status),
        public_requirements_expected=EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT,
        public_requirements_seen=len(requirements),
        public_campaign_uses_9_file_expectation=(
            len(requirements) == EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT
        ),
        january_18_file_campaign_used=False,
        public_candle_file_requirements=tuple(_json_ready(item) for item in requirements),
        input_directory=str(input_directory) if input_directory is not None else None,
        input_files_found=tuple(str(path) for path in resolved_inputs),
        input_files_missing=tuple(missing_files),
        input_requirement_map={str(path): str(identifier) for path, identifier in input_map.items()},
        public_file_coverage_results=tuple(_json_ready(item) for item in coverage_results),
        identity_readiness_results=tuple(
            _json_ready(item) for item in identity_requirements
        ),
        guarded_import=import_payload,
        final_status=final_status,
        sv113_evidence_review_can_proceed=(
            final_status == "public_campaign_import_complete"
        ),
        candles_imported=(
            int(import_payload["rows_inserted"])
            + int(import_payload["rows_updated"])
            + int(import_payload["rows_unchanged"])
        )
        > 0,
        evidence_packs_generated=False,
        supported_venue_inventory=SUPPORTED_VENUE_INVENTORY,
        creates_live_artifacts=False,
        calls_exchange_adapters=False,
        calls_private_exchange_endpoints=False,
        calls_exchange_order_endpoints=False,
        reason_codes=tuple(sorted(reason_codes)),
        warnings=tuple(sorted(warnings)),
    )


def build_public_campaign_candle_requirements(
    *,
    campaign_config_path: str | Path = PUBLIC_CAMPAIGN_CONFIG_PATH,
) -> tuple[dict[str, Any], ...]:
    """Build the 9-file Hyperliquid public campaign import requirements."""

    path = Path(campaign_config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for symbol_config in config["symbols"]:
        symbol = str(symbol_config["symbol"]).upper()
        instrument_key = str(symbol_config["instrument_key"])
        for window in config["timeframe_windows"]:
            timeframe = str(window["timeframe"])
            start_at = _parse_utc(str(window["start"]))
            end_at = _parse_utc(str(window["end"]))
            expected = int(window["expected_candles_per_symbol"])
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
                    "component": str(window["component"]),
                    "components": (str(window["component"]),),
                    "window_label": str(window["label"]),
                    "window_labels": (str(window["label"]),),
                    "requested_start_at": start_at.isoformat(),
                    "requested_end_at": end_at.isoformat(),
                    "window_convention": "(start_at, end_at]",
                    "expected_candle_count": expected,
                    "actual_candle_count": 0,
                    "missing_candle_count": expected,
                    "required_timestamp_format": CANONICAL_TIMESTAMP_REQUIREMENT,
                    "required_file_format": "CSV",
                    "required_columns": CANONICAL_CANDLE_REQUIRED_COLUMNS,
                    "suggested_filename": _suggested_filename(
                        venue=str(config.get("venue") or "hyperliquid"),
                        symbol=symbol,
                        timeframe=timeframe,
                        start_at=start_at,
                        end_at=end_at,
                    ),
                    "campaigns_impacted": (str(config["campaign_name"]),),
                    "config_paths": (str(path),),
                    "source": str(window.get("source") or "hyperliquid_public_candleSnapshot"),
                    "source_status": str(window.get("status") or ""),
                }
            )
    rows.sort(key=lambda item: (item["symbol"], item["timeframe"]))
    return tuple(rows)


def strategy_validation_public_campaign_import_result_to_dict(
    result: StrategyValidationPublicCampaignImportResult,
) -> dict[str, Any]:
    return _json_ready(asdict(result))


def strategy_validation_public_campaign_import_result_to_json(
    result: StrategyValidationPublicCampaignImportResult,
) -> str:
    return json.dumps(
        strategy_validation_public_campaign_import_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def strategy_validation_public_campaign_import_result_to_markdown(
    result: StrategyValidationPublicCampaignImportResult,
) -> str:
    payload = strategy_validation_public_campaign_import_result_to_dict(result)
    db = payload["database_status"]
    guarded = payload["guarded_import"]
    lines = [
        "# SV1.12.5 Public Campaign Import Result",
        "",
        "SV1.12.5 is research-only. It seeds only founder/operator-approved "
        "Hyperliquid BTC/ETH/SOL market identity as non-trading identity, then "
        "preflights and imports the 9-file public YTD/recent campaign only if every "
        "guard passes. It does not generate evidence packs, approve paper trading, "
        "route, submit, or call exchange adapters.",
        "",
        "## Summary",
        "",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- Final status: `{payload['final_status']}`",
        f"- SV1.13 evidence review can proceed: `{payload['sv113_evidence_review_can_proceed']}`",
        f"- Campaign: `{payload['campaign_name']}`",
        f"- Campaign config: `{payload['campaign_config_path']}`",
        f"- Public requirement count: `{payload['public_requirements_seen']}` / `{payload['public_requirements_expected']}`",
        f"- Uses 9-file public expectation: `{payload['public_campaign_uses_9_file_expectation']}`",
        f"- January 18-file campaign used: `{payload['january_18_file_campaign_used']}`",
        f"- Identity seed approved: `{payload['identity_seed_approved']}`",
        f"- Identity seed requested: `{payload['identity_seed_requested']}`",
        f"- Identity seed attempted: `{payload['identity_seed_attempted']}`",
        f"- Identity seeded: `{payload['identity_seeded']}`",
        f"- Identity seed status: `{payload['identity_seed_status']}`",
        f"- Verified by: `{payload['verified_by']}`",
        f"- Input files found: `{len(payload['input_files_found'])}`",
        f"- Input files missing: `{len(payload['input_files_missing'])}`",
        f"- Import attempted: `{guarded['import_attempted']}`",
        f"- Import completed: `{guarded['import_completed']}`",
        f"- Bundle final status: `{guarded['bundle_import_final_status']}`",
        f"- Bundle failure policy: `{guarded['bundle_import_failure_policy']}`",
        f"- Rows inserted: `{guarded['rows_inserted']}`",
        f"- Rows updated: `{guarded['rows_updated']}`",
        f"- Rows unchanged: `{guarded['rows_unchanged']}`",
        f"- Evidence packs generated: `{payload['evidence_packs_generated']}`",
        f"- Reason codes: `{payload['reason_codes']}`",
        f"- Warnings: `{payload['warnings']}`",
        "",
        "## DB And Schema",
        "",
        f"- DB target: `{db.get('configured_database_url')}`",
        f"- DB reachable: `{db.get('reachable')}`",
        f"- Target role: `{db.get('database_target_role')}`",
        f"- Intended strategy-validation DB: `{db.get('intended_strategy_validation_database')}`",
        f"- Schema status: `{db.get('schema_status')}`",
        f"- Migrations current: `{db.get('migrations_current')}`",
        f"- Required tables missing: `{db.get('required_schema_tables_missing')}`",
        f"- Persisted candle count before attempt: `{db.get('persisted_candle_count')}`",
        "",
        "## Identity Readiness",
        "",
        "| symbol | instrument key | status | operator verified | strategy eligible | trading eligible | verified by | reason codes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["identity_readiness_results"]:
        lines.append(
            f"| `{item['symbol']}` | `{item['instrument_key']}` | "
            f"`{item['operator_verified_market_identity_status']}` | "
            f"`{item['operator_verified']}` | `{item['is_strategy_eligible']}` | "
            f"`{item['is_trading_eligible']}` | `{item['verified_by']}` | "
            f"`{item['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Public Candle Requirements",
            "",
            "These are the 9 Hyperliquid public campaign files. The archival January 18-file campaign is not used here.",
            "",
            "| requirement id | suggested filename | symbol | timeframe | window | expected | timestamp requirement |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["public_candle_file_requirements"]:
        lines.append(
            f"| `{item['requirement_identifier']}` | `{item['suggested_filename']}` | "
            f"`{item['symbol']}` | `{item['timeframe']}` | "
            f"`({item['requested_start_at']}, {item['requested_end_at']}]` | "
            f"`{item['expected_candle_count']}` | `{item['required_timestamp_format']}` |"
        )
    lines.extend(
        [
            "",
            "## File Coverage Truth",
            "",
            "| file | symbol | timeframe | rows parsed | expected slots | missing slots | duplicate slots | extra slots | coverage complete | row level ready | reason codes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["public_file_coverage_results"]:
        lines.append(
            f"| `{item['input_path']}` | `{item['symbol']}` | `{item['timeframe']}` | "
            f"`{item['rows_parsed']}` | `{item['expected_candle_count']}` | "
            f"`{len(item['missing_close_time_slots'])}` | "
            f"`{len(item['duplicate_close_time_slots'])}` | "
            f"`{len(item['extra_close_time_slots'])}` | "
            f"`{item['coverage_complete']}` | `{item['row_level_ready']}` | "
            f"`{item['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Guarded Import Results",
            "",
            f"- Preflight ready: `{guarded['preflight']['ready']}`",
            f"- Preflight reason codes: `{guarded['preflight']['reason_codes']}`",
            f"- Imported requirement IDs: `{guarded['imported_requirement_ids']}`",
            f"- Failed requirement IDs: `{guarded['failed_requirement_ids']}`",
            f"- Missing requirement IDs: `{guarded['missing_requirement_ids']}`",
            f"- Safe rerun/resume: {guarded['safe_rerun_resume_instructions']}",
            "",
            "### Per-File Import Rows",
            "",
        ]
    )
    if guarded["file_import_results"]:
        for item in guarded["file_import_results"]:
            lines.extend(
                [
                    f"#### `{item['input_path']}`",
                    "",
                    f"- Requirement identifier: `{item['requirement_identifier']}`",
                    f"- Symbol: `{item['symbol']}`",
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
            "## Supported-Venue Inventory",
            "",
            "| venue | product | quote | settlement | trade count | import recommendation | blocked reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["supported_venue_inventory"]:
        lines.append(
            f"| `{item['venue']}` | `{item['product_type']}` | `{item['quote_asset']}` | "
            f"`{item['settlement_asset']}` | `{item['native_trade_count_available']}` | "
            f"`{item['import_recommendation']}` | `{item['blocked_reason']}` |"
        )
    lines.extend(
        [
            "",
            "Supported venues are segmented by venue, product type, market type, quote asset, settlement asset, source, and trade-count availability. Hyperliquid USDC perpetual data is not interchangeable with Aster/OKX USDT perps, Binance USDT spot, or Coinbase/Kraken USD spot.",
            "",
            "## Research Boundary",
            "",
            f"- Creates live artifacts: `{payload['creates_live_artifacts']}`",
            f"- Calls exchange adapters: `{payload['calls_exchange_adapters']}`",
            f"- Calls private exchange endpoints: `{payload['calls_private_exchange_endpoints']}`",
            f"- Calls exchange order endpoints: `{payload['calls_exchange_order_endpoints']}`",
            "- No evidence packs are generated in SV1.12.5.",
            "- No Money Flow rules are changed.",
            "- This is not paper trading, live trading, proof of profitability, or a strategy recommendation.",
        ]
    )
    return "\n".join(lines) + "\n"


def regenerate_missing_hyperliquid_public_candles(
    *,
    requirements: Sequence[dict[str, Any]],
    output_dir: str | Path,
) -> tuple[dict[str, Any], ...]:
    """Regenerate missing public Hyperliquid CSVs from candleSnapshot."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for requirement in requirements:
        output_path = directory / str(requirement["suggested_filename"])
        if output_path.exists():
            rows.append(
                {
                    "input_path": str(output_path),
                    "requirement_identifier": requirement["requirement_identifier"],
                    "generated": False,
                    "reason_code": "public_candle_file_already_exists",
                }
            )
            continue
        try:
            candle_rows = _fetch_hyperliquid_candle_snapshot(requirement)
            _write_public_candle_csv(output_path, requirement, candle_rows)
            rows.append(
                {
                    "input_path": str(output_path),
                    "requirement_identifier": requirement["requirement_identifier"],
                    "generated": True,
                    "row_count": len(candle_rows),
                    "reason_code": "public_candle_file_generated",
                }
            )
        except Exception as exc:  # noqa: BLE001 - report missing public file context.
            rows.append(
                {
                    "input_path": str(output_path),
                    "requirement_identifier": requirement["requirement_identifier"],
                    "generated": False,
                    "reason_code": "public_candle_regeneration_failed",
                    "error_message": str(exc).splitlines()[0],
                }
            )
    return tuple(rows)


SUPPORTED_VENUE_INVENTORY: tuple[dict[str, Any], ...] = (
    {
        "venue": "hyperliquid",
        "market_type": "perpetual",
        "product_type": "linear",
        "quote_asset": "USDC",
        "settlement_asset": "USDC",
        "data_source": "public candleSnapshot",
        "files_expected": 9,
        "files_produced": 9,
        "files_structurally_complete": 9,
        "native_trade_count_available": True,
        "import_recommendation": "current_candidate",
        "blocked_reason": None,
    },
    {
        "venue": "aster",
        "market_type": "perpetual",
        "product_type": "linear",
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "data_source": "public candles",
        "files_expected": 9,
        "files_produced": 9,
        "files_structurally_complete": 9,
        "native_trade_count_available": True,
        "import_recommendation": "later_candidate",
        "blocked_reason": "separate_identity_verification_required",
    },
    {
        "venue": "binance",
        "market_type": "spot",
        "product_type": "spot",
        "quote_asset": "USDT",
        "settlement_asset": "none",
        "data_source": "public klines",
        "files_expected": 9,
        "files_produced": 9,
        "files_structurally_complete": 9,
        "native_trade_count_available": True,
        "import_recommendation": "later_candidate",
        "blocked_reason": "spot_usdt_separate_comparison_category",
    },
    {
        "venue": "okx",
        "market_type": "perpetual",
        "product_type": "linear",
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "data_source": "public candles",
        "files_expected": 9,
        "files_produced": 9,
        "files_structurally_complete": 9,
        "native_trade_count_available": False,
        "import_recommendation": "blocked",
        "blocked_reason": "trade_count_source_policy_unresolved_placeholder_trade_count_not_canonical",
    },
    {
        "venue": "coinbase",
        "market_type": "spot",
        "product_type": "spot",
        "quote_asset": "USD",
        "settlement_asset": "none",
        "data_source": "public candles",
        "files_expected": 9,
        "files_produced": 9,
        "files_structurally_complete": 9,
        "native_trade_count_available": False,
        "import_recommendation": "blocked",
        "blocked_reason": "trade_count_source_policy_unresolved_placeholder_trade_count_not_canonical",
    },
    {
        "venue": "kraken",
        "market_type": "spot",
        "product_type": "spot",
        "quote_asset": "USD",
        "settlement_asset": "none",
        "data_source": "public candles",
        "files_expected": 9,
        "files_produced": 0,
        "files_structurally_complete": 0,
        "native_trade_count_available": False,
        "import_recommendation": "blocked",
        "blocked_reason": "public_rest_history_limit_incomplete",
    },
)


def _file_coverage_result(
    *,
    requirement: dict[str, Any],
    input_path: Path | None,
    file_format: str,
) -> dict[str, Any]:
    reason_codes: set[str] = set()
    warnings: set[str] = set()
    if input_path is None or not input_path.exists():
        return {
            "input_path": str(input_path) if input_path is not None else None,
            "requirement_identifier": requirement["requirement_identifier"],
            "symbol": requirement["symbol"],
            "instrument_key": requirement["instrument_key"],
            "timeframe": requirement["timeframe"],
            "row_level_ready": False,
            "coverage_complete": False,
            "rows_seen": 0,
            "rows_parsed": 0,
            "expected_candle_count": requirement["expected_candle_count"],
            "missing_close_time_slots": _expected_close_slots(requirement),
            "duplicate_close_time_slots": (),
            "extra_close_time_slots": (),
            "source_file_sha256": None,
            "reason_codes": ("public_campaign_candle_file_missing",),
        }

    parsed_rows: list[dict[str, Any]] = []
    timeframe = Timeframe(str(requirement["timeframe"]))
    try:
        raw_rows = _load_candle_rows(input_path, file_format=file_format)
        for raw in raw_rows:
            parsed = _parse_candle_row(
                raw,
                timeframe=timeframe,
                assume_naive_utc=False,
                warning_reason_codes=warnings,
            )
            if parsed["symbol"] != requirement["symbol"]:
                reason_codes.add("requirement_symbol_mismatch")
            if parsed.get("instrument_key") != requirement["instrument_key"]:
                reason_codes.add("requirement_instrument_key_mismatch")
            parsed_rows.append(parsed)
    except Exception as exc:  # noqa: BLE001 - file-level status is more useful here.
        reason_codes.add(str(exc).split(":")[0])
        return {
            "input_path": str(input_path),
            "requirement_identifier": requirement["requirement_identifier"],
            "symbol": requirement["symbol"],
            "instrument_key": requirement["instrument_key"],
            "timeframe": requirement["timeframe"],
            "row_level_ready": False,
            "coverage_complete": False,
            "rows_seen": 0,
            "rows_parsed": 0,
            "expected_candle_count": requirement["expected_candle_count"],
            "missing_close_time_slots": _expected_close_slots(requirement),
            "duplicate_close_time_slots": (),
            "extra_close_time_slots": (),
            "source_file_sha256": _sha256_file(input_path) if input_path.exists() else None,
            "error_message": str(exc).splitlines()[0],
            "reason_codes": tuple(sorted(reason_codes)),
        }

    expected_slots = set(_expected_close_slots(requirement))
    seen_slots = [_coerce_utc(row["close_time"]).isoformat() for row in parsed_rows]
    seen_slot_set = set(seen_slots)
    duplicate_slots = tuple(
        sorted(slot for slot in seen_slot_set if seen_slots.count(slot) > 1)
    )
    missing_slots = tuple(sorted(expected_slots - seen_slot_set))
    extra_slots = tuple(sorted(seen_slot_set - expected_slots))
    if duplicate_slots:
        reason_codes.add("requirement_duplicate_close_time_slots")
    if missing_slots:
        reason_codes.add("requirement_missing_close_time_slots")
    if extra_slots:
        reason_codes.add("requirement_extra_close_time_slots")
    if len(parsed_rows) != int(requirement["expected_candle_count"]):
        reason_codes.add("requirement_actual_candle_count_mismatch")
    row_level_ready = not any(
        code
        in {
            "candle_import_naive_timestamp",
            "candle_import_invalid_ohlcv",
            "candle_import_timeframe_duration_mismatch",
        }
        for code in reason_codes
    )
    coverage_complete = (
        row_level_ready
        and not missing_slots
        and not duplicate_slots
        and not extra_slots
        and len(parsed_rows) == int(requirement["expected_candle_count"])
        and "requirement_symbol_mismatch" not in reason_codes
        and "requirement_instrument_key_mismatch" not in reason_codes
    )
    return {
        "input_path": str(input_path),
        "requirement_identifier": requirement["requirement_identifier"],
        "symbol": requirement["symbol"],
        "instrument_key": requirement["instrument_key"],
        "timeframe": requirement["timeframe"],
        "row_level_ready": row_level_ready,
        "coverage_complete": coverage_complete,
        "rows_seen": len(parsed_rows),
        "rows_parsed": len(parsed_rows),
        "expected_candle_count": requirement["expected_candle_count"],
        "missing_close_time_slots": missing_slots,
        "duplicate_close_time_slots": duplicate_slots,
        "extra_close_time_slots": extra_slots,
        "source_file_sha256": _sha256_file(input_path),
        "reason_codes": tuple(sorted(reason_codes)),
    }


def _resolve_public_input_files(
    *,
    requirements: Sequence[dict[str, Any]],
    input_paths: Sequence[str | Path],
    input_dir: Path | None,
) -> tuple[tuple[Path, ...], dict[str, str], tuple[str, ...]]:
    requirements_by_filename = {
        str(item["suggested_filename"]): str(item["requirement_identifier"])
        for item in requirements
    }
    present: list[Path] = []
    seen: set[str] = set()
    for input_path in input_paths:
        path = Path(input_path)
        if str(path) not in seen:
            present.append(path)
            seen.add(str(path))
    if input_dir is not None:
        for filename in requirements_by_filename:
            path = input_dir / filename
            if path.exists() and str(path) not in seen:
                present.append(path)
                seen.add(str(path))
    auto_map = {
        str(path): requirements_by_filename[path.name]
        for path in present
        if path.name in requirements_by_filename
    }
    mapped_ids = set(auto_map.values())
    missing = tuple(
        str((input_dir / item["suggested_filename"]) if input_dir is not None else item["suggested_filename"])
        for item in requirements
        if str(item["requirement_identifier"]) not in mapped_ids
    )
    return tuple(present), auto_map, missing


def _path_for_requirement(
    requirement: dict[str, Any],
    input_paths: Sequence[Path],
) -> Path | None:
    filename = str(requirement["suggested_filename"])
    for input_path in input_paths:
        if input_path.name == filename:
            return input_path
    return None


def _fetch_hyperliquid_candle_snapshot(requirement: dict[str, Any]) -> list[dict[str, Any]]:
    start_at = _parse_utc(str(requirement["requested_start_at"]))
    end_at = _parse_utc(str(requirement["requested_end_at"]))
    body = json.dumps(
        {
            "type": "candleSnapshot",
            "req": {
                "coin": str(requirement["symbol"]),
                "interval": str(requirement["timeframe"]),
                "startTime": int(start_at.timestamp() * 1000),
                "endTime": int(end_at.timestamp() * 1000),
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.hyperliquid.xyz/info",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - public endpoint.
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("hyperliquid candleSnapshot response was not a list.")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _write_public_candle_csv(
    path: Path,
    requirement: dict[str, Any],
    raw_rows: Sequence[dict[str, Any]],
) -> None:
    timeframe = Timeframe(str(requirement["timeframe"]))
    duration = _timeframe_duration(timeframe)
    start_at = _parse_utc(str(requirement["requested_start_at"]))
    end_at = _parse_utc(str(requirement["requested_end_at"]))
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        open_time = datetime.fromtimestamp(int(raw["t"]) / 1000, tz=UTC)
        close_time = open_time + duration
        if close_time <= start_at or close_time > end_at:
            continue
        rows.append(
            {
                "symbol": requirement["symbol"],
                "instrument_key": requirement["instrument_key"],
                "open_time": _iso_z(open_time),
                "close_time": _iso_z(close_time),
                "open": str(raw["o"]),
                "high": str(raw["h"]),
                "low": str(raw["l"]),
                "close": str(raw["c"]),
                "volume": str(raw["v"]),
                "trade_count": str(raw.get("n", "")),
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANONICAL_CANDLE_REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def _expected_close_slots(requirement: dict[str, Any]) -> tuple[str, ...]:
    timeframe = Timeframe(str(requirement["timeframe"]))
    duration = _timeframe_duration(timeframe)
    start_at = _parse_utc(str(requirement["requested_start_at"]))
    expected = int(requirement["expected_candle_count"])
    return tuple((start_at + duration * (index + 1)).isoformat() for index in range(expected))


def _requirement_identifier(
    *,
    symbol: str,
    instrument_key: str,
    timeframe: str,
    requested_start_at: datetime,
    requested_end_at: datetime,
    expected_candle_count: int,
) -> str:
    return "|".join(
        (
            symbol,
            instrument_key,
            timeframe,
            requested_start_at.isoformat(),
            requested_end_at.isoformat(),
            str(expected_candle_count),
        )
    )


def _suggested_filename(
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    start_at: datetime,
    end_at: datetime,
) -> str:
    return (
        f"{venue}_{symbol.lower()}_{timeframe}_"
        f"{_filename_timestamp(start_at)}_{_filename_timestamp(end_at)}.csv"
    )


def _filename_timestamp(value: datetime) -> str:
    return _coerce_utc(value).strftime("%Y%m%d_%H%M%Sz").lower()


def _final_status(
    *,
    import_result: StrategyValidationCanonicalCandleBundleImportResult,
    identity_ready: bool,
    missing_files: Sequence[str],
    requirements: Sequence[dict[str, Any]],
) -> str:
    if import_result.bundle_import_final_status == "canonical_import_complete":
        return "public_campaign_import_complete"
    if import_result.bundle_import_final_status == "partial_import":
        return "partial_import"
    if len(requirements) != EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT:
        return "import_blocked"
    if not identity_ready:
        return "identity_missing"
    if missing_files:
        return "files_missing"
    if not import_result.preflight.get("ready"):
        return "preflight_blocked"
    return "import_blocked"


def _config_input_dir(config: dict[str, Any]) -> Path | None:
    value = config.get("local_candle_output_dir")
    if not value:
        return None
    return Path(str(value))


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timezone required for public campaign timestamp: {value}")
    return parsed.astimezone(UTC)


def _iso_z(value: datetime) -> str:
    return _coerce_utc(value).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return _coerce_utc(value).isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    return value


__all__ = [
    "EXPECTED_PUBLIC_CAMPAIGN_FILE_COUNT",
    "PUBLIC_CAMPAIGN_CONFIG_PATH",
    "StrategyValidationPublicCampaignImportResult",
    "build_public_campaign_candle_requirements",
    "regenerate_missing_hyperliquid_public_candles",
    "run_strategy_validation_public_campaign_import",
    "strategy_validation_public_campaign_import_result_to_dict",
    "strategy_validation_public_campaign_import_result_to_json",
    "strategy_validation_public_campaign_import_result_to_markdown",
]
