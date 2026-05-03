"""Money Flow evidence-pack review helpers.

SV1.9.1 is a research-review/data-gap layer over existing campaign audits and
evidence packs. It does not change Money Flow rules, create live artifacts, or
call exchange adapters.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import func, inspect as sqlalchemy_inspect, select, text
from sqlalchemy.engine import make_url

from db.models import CandleModel, InstrumentModel, SymbolModel
from services.strategy_validation.campaigns import (
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    MoneyFlowResearchCampaignConfig,
    MoneyFlowResearchCampaignDataReadinessAudit,
    MoneyFlowResearchCampaignDataReadinessRow,
    MoneyFlowResearchCampaignResult,
    _campaign_expected_close_slot_count,
    _campaign_timeframe_delta,
    _data_readiness_summary,
    _WINDOW_CONVENTION_DISPLAY,
    audit_money_flow_research_campaign_data_readiness,
    load_money_flow_research_campaign_config,
    money_flow_evidence_pack_review_checklist,
    money_flow_manual_paper_trading_readiness_criteria,
    money_flow_research_campaign_data_readiness_to_dict,
    money_flow_research_campaign_data_readiness_to_markdown,
    run_money_flow_research_campaign_sync,
)
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    strategy_validation_batch_report_to_dict,
)

CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS = (
    Path("configs/strategy_validation/campaigns/money_flow_core_btc.json"),
    Path("configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json"),
)

PAPER_READINESS_REVIEW_STATUSES = (
    "not_reviewed",
    "insufficient_data",
    "partial_evidence_ready_with_data_gaps",
    "ready_for_founder_review",
    "paper_trading_design_not_yet_justified",
    "paper_trading_design_candidate",
)

_BANNED_RECOMMENDATION_LANGUAGE = (
    "best strategy",
    "recommended strategy",
    "recommended component",
    "optimal",
    "proven profitable",
    "paper trading approved",
)
_MAINTENANCE_DATABASE_NAMES = ("postgres", "template0", "template1")

REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES = (
    CandleModel.__tablename__,
    InstrumentModel.__tablename__,
    SymbolModel.__tablename__,
)


@dataclass(frozen=True, slots=True)
class MoneyFlowEvidenceReviewDatabaseStatus:
    configured_database_url: str
    database_driver: str | None
    database_host: str | None
    database_port: int | None
    database_name: str | None
    database_username: str | None
    database_target_role: str
    intended_strategy_validation_database: bool
    database_target_warning_reason_codes: tuple[str, ...]
    database_target_ready_for_evidence_generation: bool
    database_target_blocking_reason_codes: tuple[str, ...]
    inspection_source: str
    reachable: bool
    candles_table_exists: bool
    persisted_candle_count: int | None
    schema_ready_for_evidence_generation: bool = False
    required_schema_tables: tuple[str, ...] = REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES
    required_schema_tables_present: tuple[str, ...] = ()
    required_schema_tables_missing: tuple[str, ...] = ()
    alembic_version_table_exists: bool = False
    applied_migration_revisions: tuple[str, ...] = ()
    migration_head_revisions: tuple[str, ...] = ()
    migrations_current: bool | None = None
    schema_status: str = "database_status_unknown"
    schema_status_reason_codes: tuple[str, ...] = ()
    migration_command_hint: str = (
        "Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD for the intended "
        "Money Flow database, then run `.venv/bin/python -m alembic upgrade head`."
    )
    db_environment_override_hint: str = (
        "Strategy validation uses the normal AppSettings database fields. Override "
        "DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD to point evidence review "
        "at the local migrated Money Flow database."
    )
    blocking_error_type: str | None = None
    blocking_error_message: str | None = None


@dataclass(frozen=True, slots=True)
class MoneyFlowEvidenceReviewCampaignResult:
    campaign_name: str
    config_path: str
    readiness_status: str
    data_readiness_audit: MoneyFlowResearchCampaignDataReadinessAudit
    audit_markdown: str
    evidence_pack_generated: bool
    evidence_pack_path: str | None
    evidence_pack_manifest: dict[str, Any] | None
    generated_evidence_final_run_id: str | None
    blocked_or_gap_reason_codes: tuple[str, ...]
    observations: dict[str, Any]
    no_live_artifacts_created: bool
    exchange_adapters_called: bool


@dataclass(frozen=True, slots=True)
class MoneyFlowEvidenceReviewSummary:
    review_id: str
    generated_at_utc: datetime
    campaign_results: tuple[MoneyFlowEvidenceReviewCampaignResult, ...]
    database_status: MoneyFlowEvidenceReviewDatabaseStatus
    paper_readiness_review_status: str
    paper_readiness_status_methodology: str
    manual_paper_trading_readiness_criteria: tuple[str, ...]
    canonical_candle_import_requirements: tuple[dict[str, Any], ...]
    generated_evidence_pack_paths: tuple[str, ...]
    blocked_campaign_count: int
    generated_campaign_count: int
    window_convention: str
    limitations: tuple[str, ...]
    creates_live_artifacts: bool = False
    calls_exchange_adapters: bool = False
    calls_private_exchange_endpoints: bool = False
    calls_exchange_order_endpoints: bool = False
    optimization_or_recommendation_language_used: bool = False


def review_money_flow_evidence(
    campaign_config_paths: Sequence[str | Path] | None = None,
    *,
    service: MoneyFlowBacktestService | None = None,
    output_dir: str | Path | None = None,
    generate_evidence_packs: bool = True,
    run_timestamp: datetime | None = None,
    generated_at: datetime | None = None,
    evidence_pack_collision_policy: str = MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
) -> MoneyFlowEvidenceReviewSummary:
    """Audit canonical campaign configs and generate packs only when data is sufficient."""

    validation_service = service or MoneyFlowBacktestService()
    timestamp = _coerce_utc(generated_at or datetime.now(UTC)).replace(microsecond=0)
    database_status = inspect_strategy_validation_database_status(validation_service)
    paths = tuple(campaign_config_paths or CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS)
    results: list[MoneyFlowEvidenceReviewCampaignResult] = []
    for path in paths:
        config_path = Path(path)
        config = load_money_flow_research_campaign_config(config_path)
        if not _schema_ready_for_evidence_generation(database_status):
            audit = _database_blocked_data_readiness_audit(
                config=config,
                service=validation_service,
                generated_at=timestamp,
                database_status=database_status,
            )
        else:
            audit = audit_money_flow_research_campaign_data_readiness(
                config,
                service=validation_service,
                generated_at=timestamp,
            )
        audit_payload = money_flow_research_campaign_data_readiness_to_dict(audit)
        audit_markdown = money_flow_research_campaign_data_readiness_to_markdown(audit)
        can_generate = _audit_has_sufficient_data(audit_payload)
        campaign_run: MoneyFlowResearchCampaignResult | None = None
        observations: dict[str, Any]
        if generate_evidence_packs and can_generate:
            campaign_run = run_money_flow_research_campaign_sync(
                config,
                service=validation_service,
                output_dir=output_dir,
                run_timestamp=run_timestamp,
                evidence_pack_collision_policy=evidence_pack_collision_policy,
            )
            batch_payload = strategy_validation_batch_report_to_dict(
                campaign_run.batch_report
            )
            observations = _observations_from_batch_payload(batch_payload)
            readiness_status = _campaign_status_from_generated_pack(campaign_run)
        elif can_generate:
            observations = _not_generated_observations()
            readiness_status = "not_reviewed"
        else:
            observations = _insufficient_data_observations(audit_payload)
            readiness_status = "insufficient_data"
        reason_codes = _blocked_or_gap_reason_codes(audit_payload)
        results.append(
            MoneyFlowEvidenceReviewCampaignResult(
                campaign_name=config.campaign_name,
                config_path=str(config_path),
                readiness_status=readiness_status,
                data_readiness_audit=audit,
                audit_markdown=audit_markdown,
                evidence_pack_generated=campaign_run is not None,
                evidence_pack_path=(
                    str(campaign_run.evidence_pack_dir)
                    if campaign_run is not None
                    else None
                ),
                evidence_pack_manifest=(
                    dict(campaign_run.manifest) if campaign_run is not None else None
                ),
                generated_evidence_final_run_id=(
                    campaign_run.manifest.get("final_run_id")
                    if campaign_run is not None
                    else None
                ),
                blocked_or_gap_reason_codes=reason_codes,
                observations=observations,
                no_live_artifacts_created=(
                    True
                    if campaign_run is None
                    else bool(
                        campaign_run.batch_report.no_live_execution_artifacts_created
                    )
                ),
                exchange_adapters_called=(
                    False
                    if campaign_run is None
                    else bool(campaign_run.batch_report.exchange_adapters_called)
                ),
            )
        )

    generated_paths = tuple(
        result.evidence_pack_path
        for result in results
        if result.evidence_pack_path is not None
    )
    overall_status = _overall_paper_readiness_status(results)
    review_id = _review_id(paths=paths, generated_at=timestamp)
    import_requirements = _canonical_candle_import_requirements_from_results(results)
    return MoneyFlowEvidenceReviewSummary(
        review_id=review_id,
        generated_at_utc=timestamp,
        campaign_results=tuple(results),
        database_status=database_status,
        paper_readiness_review_status=overall_status,
        paper_readiness_status_methodology=(
            "manual_review_status_only_no_automatic_paper_trading_decision"
        ),
        manual_paper_trading_readiness_criteria=tuple(
            money_flow_manual_paper_trading_readiness_criteria()
        ),
        canonical_candle_import_requirements=import_requirements,
        generated_evidence_pack_paths=generated_paths,
        blocked_campaign_count=sum(
            1 for result in results if result.readiness_status == "insufficient_data"
        ),
        generated_campaign_count=len(generated_paths),
        window_convention=STRATEGY_VALIDATION_WINDOW_CONVENTION,
        limitations=(
            "This review is research-only and does not create paper trades, live trades, routing artifacts, approvals, child intents, readiness evaluations, or submitted orders.",
            "Missing or thin data is a data-readiness gap, not a Money Flow strategy failure.",
            "Evidence-pack generation requires migrated/current schema truth; a candles table alone is not sufficient.",
            "Evidence-pack generation also requires a clearly intended non-maintenance strategy-validation DB target.",
            "Evidence packs and backtests do not prove future profitability.",
            "Paper-readiness status is manual review context only, not an automated go/no-go decision.",
            "No exchange adapters, private exchange endpoints, or order endpoints are called.",
            "Money Flow rules are not changed or optimized by this review.",
        ),
        creates_live_artifacts=_creates_live_artifacts_from_campaign_results(results),
        calls_exchange_adapters=_calls_exchange_adapters_from_campaign_results(results),
    )


def inspect_strategy_validation_database_status(
    service: MoneyFlowBacktestService | None = None,
) -> MoneyFlowEvidenceReviewDatabaseStatus:
    """Return sanitized DB reachability, migration, schema, and candle-table truth."""

    validation_service = service or MoneyFlowBacktestService()
    target_metadata = _database_target_metadata(
        validation_service.settings.database.sqlalchemy_url
    )
    target_blocking_reason_codes = _database_target_blocking_reason_codes(target_metadata)
    configured_url = _sanitize_database_url(
        validation_service.settings.database.sqlalchemy_url
    )
    migration_heads = _migration_head_revisions()
    try:
        with validation_service._session_factory() as session:
            session.execute(text("SELECT 1"))
            bind = session.get_bind()
            inspector = sqlalchemy_inspect(bind)
            required_table_presence = {
                table_name: inspector.has_table(table_name)
                for table_name in REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES
            }
            required_tables_present = tuple(
                sorted(
                    table_name
                    for table_name, is_present in required_table_presence.items()
                    if is_present
                )
            )
            required_tables_missing = tuple(
                sorted(
                    table_name
                    for table_name, is_present in required_table_presence.items()
                    if not is_present
                )
            )
            candles_table_exists = required_table_presence[CandleModel.__tablename__]
            alembic_version_table_exists = inspector.has_table("alembic_version")
            applied_revisions = _applied_migration_revisions(
                session,
                alembic_version_table_exists=alembic_version_table_exists,
            )
            candle_count = None
            if candles_table_exists:
                candle_count = int(
                    session.scalar(select(func.count()).select_from(CandleModel)) or 0
                )
            migrations_current = _migrations_current(
                applied_revisions=applied_revisions,
                migration_heads=migration_heads,
                alembic_version_table_exists=alembic_version_table_exists,
            )
            schema_status, reason_codes = _schema_status(
                reachable=True,
                candles_table_exists=candles_table_exists,
                alembic_version_table_exists=alembic_version_table_exists,
                migrations_current=migrations_current,
                required_schema_tables_missing=required_tables_missing,
            )
            schema_ready = schema_status == "migrated_schema_ready"
            return MoneyFlowEvidenceReviewDatabaseStatus(
                configured_database_url=configured_url,
                database_driver=target_metadata["database_driver"],
                database_host=target_metadata["database_host"],
                database_port=target_metadata["database_port"],
                database_name=target_metadata["database_name"],
                database_username=target_metadata["database_username"],
                database_target_role=target_metadata["database_target_role"],
                intended_strategy_validation_database=target_metadata[
                    "intended_strategy_validation_database"
                ],
                database_target_warning_reason_codes=target_metadata[
                    "database_target_warning_reason_codes"
                ],
                database_target_ready_for_evidence_generation=not target_blocking_reason_codes,
                database_target_blocking_reason_codes=target_blocking_reason_codes,
                inspection_source="strategy_validation_session_factory",
                reachable=True,
                candles_table_exists=candles_table_exists,
                persisted_candle_count=candle_count,
                schema_ready_for_evidence_generation=schema_ready,
                required_schema_tables=REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES,
                required_schema_tables_present=required_tables_present,
                required_schema_tables_missing=required_tables_missing,
                alembic_version_table_exists=alembic_version_table_exists,
                applied_migration_revisions=applied_revisions,
                migration_head_revisions=migration_heads,
                migrations_current=migrations_current,
                schema_status=schema_status,
                schema_status_reason_codes=reason_codes,
            )
    except Exception as exc:  # noqa: BLE001 - report DB failures instead of hiding them.
        schema_status, reason_codes = _schema_status(
            reachable=False,
            candles_table_exists=False,
            alembic_version_table_exists=False,
            migrations_current=None,
            required_schema_tables_missing=REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES,
        )
        return MoneyFlowEvidenceReviewDatabaseStatus(
            configured_database_url=configured_url,
            database_driver=target_metadata["database_driver"],
            database_host=target_metadata["database_host"],
            database_port=target_metadata["database_port"],
            database_name=target_metadata["database_name"],
            database_username=target_metadata["database_username"],
            database_target_role=target_metadata["database_target_role"],
            intended_strategy_validation_database=target_metadata[
                "intended_strategy_validation_database"
            ],
            database_target_warning_reason_codes=target_metadata[
                "database_target_warning_reason_codes"
            ],
            database_target_ready_for_evidence_generation=not target_blocking_reason_codes,
            database_target_blocking_reason_codes=target_blocking_reason_codes,
            inspection_source="strategy_validation_session_factory",
            reachable=False,
            candles_table_exists=False,
            persisted_candle_count=None,
            schema_ready_for_evidence_generation=False,
            required_schema_tables=REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES,
            required_schema_tables_present=(),
            required_schema_tables_missing=REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES,
            migration_head_revisions=migration_heads,
            schema_status=schema_status,
            schema_status_reason_codes=reason_codes,
            blocking_error_type=type(exc).__name__,
            blocking_error_message=_safe_error_message(exc),
        )


def money_flow_evidence_review_to_dict(
    review: MoneyFlowEvidenceReviewSummary,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready evidence review representation."""

    return _json_ready(asdict(review))


def money_flow_evidence_review_database_status_to_dict(
    status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready database/schema status representation."""

    return _json_ready(asdict(status))


def money_flow_evidence_review_database_status_to_json(
    status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> str:
    """Serialize database/schema status with deterministic key ordering."""

    return json.dumps(
        money_flow_evidence_review_database_status_to_dict(status),
        indent=2,
        sort_keys=True,
    ) + "\n"


def money_flow_evidence_review_database_status_to_markdown(
    status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> str:
    """Render DB/schema/candle readiness status for operator review."""

    payload = money_flow_evidence_review_database_status_to_dict(status)
    lines = [
        "# Money Flow Strategy Validation DB Status",
        "",
        "This status is research-only. It does not run strategy validation, create "
        "live artifacts, call exchanges, route, submit, or approve paper trading.",
        "",
        "## Database Target",
        "",
        f"- Configured DB URL: `{payload['configured_database_url']}`",
        f"- DB driver: `{payload['database_driver']}`",
        f"- DB host: `{payload['database_host']}`",
        f"- DB port: `{payload['database_port']}`",
        f"- DB name: `{payload['database_name']}`",
        f"- DB user: `{payload['database_username']}`",
        f"- Target role: `{payload['database_target_role']}`",
        f"- Intended strategy-validation DB: `{payload['intended_strategy_validation_database']}`",
        f"- Target warning reason codes: `{payload['database_target_warning_reason_codes']}`",
        f"- Target ready for evidence generation: `{payload['database_target_ready_for_evidence_generation']}`",
        f"- Target blocking reason codes: `{payload['database_target_blocking_reason_codes']}`",
        f"- Inspection source: `{payload['inspection_source']}`",
        f"- DB reachable: `{payload['reachable']}`",
        f"- DB override hint: {payload['db_environment_override_hint']}",
        "",
        "## Schema And Migrations",
        "",
        f"- Schema status: `{payload['schema_status']}`",
        f"- Schema reason codes: `{payload['schema_status_reason_codes']}`",
        f"- Schema ready for evidence generation: `{payload['schema_ready_for_evidence_generation']}`",
        f"- Required schema tables: `{payload['required_schema_tables']}`",
        f"- Required schema tables present: `{payload['required_schema_tables_present']}`",
        f"- Required schema tables missing: `{payload['required_schema_tables_missing']}`",
        f"- Alembic version table exists: `{payload['alembic_version_table_exists']}`",
        f"- Applied migration revisions: `{payload['applied_migration_revisions']}`",
        f"- Repo migration heads: `{payload['migration_head_revisions']}`",
        f"- Migrations current: `{payload['migrations_current']}`",
        f"- Migration command hint: {payload['migration_command_hint']}",
        "",
        "Evidence-pack generation requires a clearly intended non-maintenance DB target plus `migrated_schema_ready`: Alembic migration truth must be current and required strategy-validation tables must exist. A `candles` table alone is not sufficient.",
        "",
        "## Candle Table",
        "",
        f"- Candles table exists: `{payload['candles_table_exists']}`",
        f"- Persisted candle count: `{payload['persisted_candle_count']}`",
        f"- Blocking error type: `{payload['blocking_error_type']}`",
        f"- Blocking error message: `{payload['blocking_error_message']}`",
    ]
    return "\n".join(lines) + "\n"


def money_flow_evidence_review_to_markdown(
    review: MoneyFlowEvidenceReviewSummary,
) -> str:
    """Render a founder/operator-readable canonical evidence review summary."""

    payload = money_flow_evidence_review_to_dict(review)
    database_status = payload["database_status"]
    lines = [
        "# Money Flow First Real Canonical Evidence Review",
        "",
        "This canonical evidence review is descriptive research only. It is not paper trading, "
        "not live execution, not optimization, not a strategy recommendation, and "
        "not proof of future profitability.",
        "",
        "## Review Context",
        "",
        f"- Review id: `{payload['review_id']}`",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- Window convention: `{payload['window_convention']}`",
        "- Candle closes exactly at `start_at` are excluded.",
        "- Candle closes on or before `end_at` are included.",
        f"- Paper-readiness review status: `{payload['paper_readiness_review_status']}`",
        f"- Status methodology: `{payload['paper_readiness_status_methodology']}`",
        f"- Generated campaign count: `{payload['generated_campaign_count']}`",
        f"- Blocked campaign count: `{payload['blocked_campaign_count']}`",
        "- Insufficient data means persisted candles are missing, thin, or blocked for at least one reviewed campaign; it is not a strategy failure.",
        f"- Live artifacts created: `{payload['creates_live_artifacts']}`",
        f"- Exchange adapters called: `{payload['calls_exchange_adapters']}`",
        "",
        "## Database Access",
        "",
        f"- Configured DB URL: `{database_status['configured_database_url']}`",
        f"- DB driver: `{database_status['database_driver']}`",
        f"- DB host: `{database_status['database_host']}`",
        f"- DB port: `{database_status['database_port']}`",
        f"- DB name: `{database_status['database_name']}`",
        f"- DB user: `{database_status['database_username']}`",
        f"- Target role: `{database_status['database_target_role']}`",
        f"- Intended strategy-validation DB: `{database_status['intended_strategy_validation_database']}`",
        f"- Target warning reason codes: `{database_status['database_target_warning_reason_codes']}`",
        f"- Target ready for evidence generation: `{database_status['database_target_ready_for_evidence_generation']}`",
        f"- Target blocking reason codes: `{database_status['database_target_blocking_reason_codes']}`",
        f"- Inspection source: `{database_status['inspection_source']}`",
        f"- DB reachable: `{database_status['reachable']}`",
        f"- Schema status: `{database_status['schema_status']}`",
        f"- Schema reason codes: `{database_status['schema_status_reason_codes']}`",
        f"- Schema ready for evidence generation: `{database_status['schema_ready_for_evidence_generation']}`",
        f"- Required schema tables: `{database_status['required_schema_tables']}`",
        f"- Required schema tables present: `{database_status['required_schema_tables_present']}`",
        f"- Required schema tables missing: `{database_status['required_schema_tables_missing']}`",
        f"- Alembic version table exists: `{database_status['alembic_version_table_exists']}`",
        f"- Applied migration revisions: `{database_status['applied_migration_revisions']}`",
        f"- Repo migration heads: `{database_status['migration_head_revisions']}`",
        f"- Migrations current: `{database_status['migrations_current']}`",
        f"- Candles table exists: `{database_status['candles_table_exists']}`",
        f"- Persisted candle count: `{database_status['persisted_candle_count']}`",
        f"- Blocking error type: `{database_status['blocking_error_type']}`",
        f"- Blocking error message: `{database_status['blocking_error_message']}`",
        f"- DB override hint: {database_status['db_environment_override_hint']}",
        f"- Migration command hint: {database_status['migration_command_hint']}",
        "",
        "Evidence-pack generation requires a clearly intended non-maintenance DB target plus `migrated_schema_ready`: Alembic migration truth must be current and required strategy-validation tables must exist. A `candles` table alone is not sufficient.",
        "",
        "If the DB target is ambiguous or non-intended, the DB is unreachable, migrations/schema are missing or unknown, required strategy-validation tables are absent, or persisted candles are absent, campaign rows are reported as data-readiness gaps and no evidence packs are generated.",
        "",
        "## Canonical Campaign Review",
        "",
        "| campaign | status | evidence pack generated | evidence pack path | blocked/gap reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in payload["campaign_results"]:
        lines.append(
            "| "
            f"`{result['campaign_name']}` | "
            f"`{result['readiness_status']}` | "
            f"`{result['evidence_pack_generated']}` | "
            f"`{result['evidence_pack_path']}` | "
            f"`{result['blocked_or_gap_reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Data-Readiness Findings",
            "",
        ]
    )
    for result in payload["campaign_results"]:
        summary = result["data_readiness_audit"]["summary"]
        lines.extend(
            [
                f"### `{result['campaign_name']}`",
                "",
                f"- Rows checked: `{summary['row_count']}`",
                f"- Covered rows: `{summary['covered_row_count']}`",
                f"- Thin rows: `{summary['thin_row_count']}`",
                f"- Missing rows: `{summary['missing_row_count']}`",
                f"- Blocked rows: `{summary['blocked_row_count']}`",
                f"- Likely blocked impacted runs: `{summary['likely_blocked_impacted_run_count']}`",
                f"- Symbols with data: `{summary['symbols_with_data']}`",
                f"- Symbols missing data: `{summary['symbols_missing_data']}`",
                f"- Components with data: `{summary['components_with_data']}`",
                f"- Components missing data: `{summary['components_missing_data']}`",
                f"- Windows covered: `{summary['windows_covered']}`",
                f"- Windows thin: `{summary['windows_thin']}`",
                f"- Windows missing: `{summary['windows_missing']}`",
                f"- Warning reason counts: `{summary['warning_reason_counts']}`",
                f"- Likely blocked reason counts: `{summary['likely_blocked_reason_counts']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Canonical Candle Import Requirements",
            "",
            "Use these rows only after the intended database is reachable and reports `migrated_schema_ready`. Imports must use public/offline historical candles and the hardened SV1.5.1 importer.",
            "",
        ]
    )
    if payload["canonical_candle_import_requirements"]:
        for requirement in payload["canonical_candle_import_requirements"]:
            lines.extend(
                [
                    f"### `{requirement['campaign_name']}` / `{requirement['symbol']}` / `{requirement['component']}` / `{requirement['window_label']}`",
                    "",
                    f"- Instrument key: `{requirement['instrument_key']}`",
                    f"- Timeframe: `{requirement['timeframe']}`",
                    f"- Window: `({requirement['requested_start_at']}, {requirement['requested_end_at']}]`",
                    f"- Expected candles: `{requirement['expected_candle_count']}`",
                    f"- Actual candles: `{requirement['actual_candle_count']}`",
                    f"- Missing candles: `{requirement['missing_candle_count']}`",
                    f"- Readiness status: `{requirement['readiness_status']}`",
                    f"- Reason codes: `{requirement['reason_codes']}`",
                    f"- Required file format: `{requirement['required_file_format']}`",
                    f"- Required fields: `{requirement['required_file_fields']}`",
                    f"- Example import command: `{requirement['example_import_command']}`",
                    "",
                ]
            )
    else:
        lines.append("- No missing canonical candle import requirements were detected.")
        lines.append("")
    lines.extend(
        [
            "## Evidence-Pack Paths",
            "",
        ]
    )
    if payload["generated_evidence_pack_paths"]:
        lines.extend(f"- `{path}`" for path in payload["generated_evidence_pack_paths"])
    else:
        lines.append("- No evidence packs were generated because no audited campaign had sufficient persisted candle coverage.")
    lines.extend(
        [
            "",
            "## Observations",
            "",
        ]
    )
    for result in payload["campaign_results"]:
        observations = result["observations"]
        lines.extend(
            [
                f"### `{result['campaign_name']}`",
                "",
                f"- Fill timing observations: `{observations.get('fill_timing_observations')}`",
                f"- Component observations: `{observations.get('component_observations')}`",
                f"- Regime observations: `{observations.get('regime_observations')}`",
                f"- Worst drawdown observations: `{observations.get('worst_drawdown_observations')}`",
                f"- Fee/slippage sensitivity observations: `{observations.get('fee_slippage_sensitivity_observations')}`",
                f"- No-trade reason counts: `{observations.get('no_trade_reason_counts')}`",
                f"- Invalid reason counts: `{observations.get('invalid_reason_counts')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Manual Paper-Readiness Review Status",
            "",
            f"- Current status: `{payload['paper_readiness_review_status']}`",
            "- `partial_evidence_ready_with_data_gaps` means at least one campaign generated a pack while another canonical campaign remains blocked or insufficient.",
            "- This is not an automatic approval and does not start paper trading.",
            "- Founder/operator review is required before any paper-trading design is scoped.",
            "",
            "### Manual Criteria",
            "",
        ]
    )
    lines.extend(
        f"- [ ] {item}" for item in payload["manual_paper_trading_readiness_criteria"]
    )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.extend(
        [
            "",
            "## Next Research Actions",
            "",
            "- If campaigns are blocked, import or verify public historical candles for the missing symbol/component/window rows and rerun the review.",
            "- If evidence packs were generated, review fill timing robustness, data coverage, regime grouping, drawdown, fees, slippage, no-trade, and invalid reason counts manually.",
            "- Do not treat this review as paper-trading approval, live execution readiness, or strategy-rule guidance.",
        ]
    )
    markdown = "\n".join(lines) + "\n"
    _assert_no_banned_recommendation_language(markdown)
    return markdown


def _audit_has_sufficient_data(audit_payload: dict[str, Any]) -> bool:
    summary = audit_payload["summary"]
    return (
        summary["row_count"] > 0
        and summary["thin_row_count"] == 0
        and summary["missing_row_count"] == 0
        and summary["blocked_row_count"] == 0
        and summary["likely_blocked_impacted_run_count"] == 0
    )


def _campaign_status_from_generated_pack(
    campaign_run: MoneyFlowResearchCampaignResult,
) -> str:
    if any(run.status != "completed" for run in campaign_run.batch_report.run_reports):
        return "paper_trading_design_not_yet_justified"
    return "ready_for_founder_review"


def _overall_paper_readiness_status(
    results: Sequence[MoneyFlowEvidenceReviewCampaignResult],
) -> str:
    if not results:
        return "not_reviewed"
    if all(result.readiness_status == "insufficient_data" for result in results):
        return "insufficient_data"
    if any(result.evidence_pack_generated for result in results) and any(
        result.readiness_status == "insufficient_data" for result in results
    ):
        return "partial_evidence_ready_with_data_gaps"
    if any(
        result.readiness_status == "paper_trading_design_not_yet_justified"
        for result in results
    ):
        return "paper_trading_design_not_yet_justified"
    if any(result.readiness_status == "ready_for_founder_review" for result in results):
        return "ready_for_founder_review"
    return "not_reviewed"


def _database_blocked_data_readiness_audit(
    *,
    config: MoneyFlowResearchCampaignConfig,
    service: MoneyFlowBacktestService,
    generated_at: datetime,
    database_status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> MoneyFlowResearchCampaignDataReadinessAudit:
    reason_codes = _database_gap_reason_codes(database_status)
    sleeves_by_key = {sleeve.sleeve_id: sleeve for sleeve in service.settings.money_flow.sleeves}
    impacted_run_count = (
        len(config.fill_timings)
        * len(config.fee_bps_values)
        * len(config.slippage_bps_values)
    )
    rows: list[MoneyFlowResearchCampaignDataReadinessRow] = []
    for symbol in config.symbols:
        for window in config.windows:
            for component in config.components:
                sleeve = sleeves_by_key.get(component)
                timeframe = sleeve.timeframe.value if sleeve is not None else None
                expected_count = None
                if timeframe is not None:
                    timeframe_delta = _campaign_timeframe_delta(timeframe)
                    if timeframe_delta is not None:
                        expected_count = _campaign_expected_close_slot_count(
                            start_at=window.start_at,
                            end_at=window.end_at,
                            timeframe_delta_seconds=timeframe_delta,
                        )
                row_reason_codes = reason_codes
                if sleeve is None:
                    row_reason_codes = tuple(
                        sorted({*reason_codes, "unknown_money_flow_component"})
                    )
                rows.append(
                    MoneyFlowResearchCampaignDataReadinessRow(
                        symbol=symbol.symbol,
                        instrument_key=symbol.instrument_key,
                        instrument_ref_id=symbol.instrument_ref_id,
                        component=component,
                        timeframe=timeframe,
                        window_label=window.label,
                        requested_start_at=window.start_at,
                        requested_end_at=window.end_at,
                        window_convention=STRATEGY_VALIDATION_WINDOW_CONVENTION,
                        expected_candle_count=expected_count,
                        actual_candle_count=0,
                        missing_candle_count=expected_count,
                        coverage_percent=Decimal("0.00000000")
                        if expected_count is not None and expected_count > 0
                        else None,
                        gap_count=None,
                        largest_gap_seconds=None,
                        first_candle_available_at=None,
                        last_candle_available_at=None,
                        readiness_status="blocked",
                        warning_reason_codes=row_reason_codes,
                        likely_blocked=True,
                        likely_blocked_reason_codes=row_reason_codes,
                        impacted_run_count=impacted_run_count,
                    )
                )
    summary = _data_readiness_summary(rows)
    summary["database_status"] = _json_ready(database_status)
    return MoneyFlowResearchCampaignDataReadinessAudit(
        campaign_name=config.campaign_name,
        generated_at_utc=_coerce_utc(generated_at).replace(microsecond=0),
        environment=config.environment,
        venue=config.venue,
        window_convention=STRATEGY_VALIDATION_WINDOW_CONVENTION,
        window_convention_display=_WINDOW_CONVENTION_DISPLAY,
        rows=tuple(rows),
        summary=summary,
        review_checklist=money_flow_evidence_pack_review_checklist(),
        manual_paper_trading_readiness_criteria=(
            money_flow_manual_paper_trading_readiness_criteria()
        ),
    )


def _database_gap_reason_codes(
    database_status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> tuple[str, ...]:
    reason_codes: set[str] = set(database_status.schema_status_reason_codes)
    reason_codes.update(database_status.database_target_blocking_reason_codes)
    if not database_status.database_target_ready_for_evidence_generation:
        reason_codes.add("evidence_generation_blocked_by_db_target_truth")
    if not database_status.reachable:
        reason_codes.add("database_unreachable")
        message = (database_status.blocking_error_message or "").lower()
        if "resolve host" in message or "nodename" in message or "name or service" in message:
            reason_codes.add("database_host_unresolved")
        if "connection refused" in message:
            reason_codes.add("database_connection_refused")
    elif not database_status.schema_ready_for_evidence_generation:
        reason_codes.add("schema_not_ready_for_evidence_generation")
        if not database_status.candles_table_exists:
            reason_codes.add("candles_table_missing")
        if not database_status.alembic_version_table_exists:
            reason_codes.add("alembic_version_missing")
        for table_name in database_status.required_schema_tables_missing:
            reason_codes.add(f"required_schema_table_missing_{table_name}")
    elif not database_status.candles_table_exists:
        reason_codes.add("candles_table_missing")
    if not reason_codes:
        reason_codes.add("database_status_unknown")
    return tuple(sorted(reason_codes))


def _schema_ready_for_evidence_generation(
    database_status: MoneyFlowEvidenceReviewDatabaseStatus,
) -> bool:
    return (
        database_status.reachable
        and database_status.database_target_ready_for_evidence_generation
        and not database_status.database_target_blocking_reason_codes
        and database_status.schema_ready_for_evidence_generation
        and database_status.schema_status == "migrated_schema_ready"
        and database_status.migrations_current is True
        and database_status.candles_table_exists
        and not database_status.required_schema_tables_missing
    )


def _creates_live_artifacts_from_campaign_results(
    results: Sequence[MoneyFlowEvidenceReviewCampaignResult],
) -> bool:
    return any(not result.no_live_artifacts_created for result in results)


def _calls_exchange_adapters_from_campaign_results(
    results: Sequence[MoneyFlowEvidenceReviewCampaignResult],
) -> bool:
    return any(result.exchange_adapters_called for result in results)


def _canonical_candle_import_requirements_from_results(
    results: Sequence[MoneyFlowEvidenceReviewCampaignResult],
) -> tuple[dict[str, Any], ...]:
    requirements: list[dict[str, Any]] = []
    for result in results:
        for row in result.data_readiness_audit.rows:
            if row.readiness_status == "covered" and not row.likely_blocked:
                continue
            reason_codes = tuple(
                sorted({*row.warning_reason_codes, *row.likely_blocked_reason_codes})
            )
            requirements.append(
                {
                    "campaign_name": result.campaign_name,
                    "config_path": result.config_path,
                    "symbol": row.symbol,
                    "instrument_key": row.instrument_key,
                    "instrument_ref_id": row.instrument_ref_id,
                    "component": row.component,
                    "timeframe": row.timeframe,
                    "window_label": row.window_label,
                    "requested_start_at": row.requested_start_at,
                    "requested_end_at": row.requested_end_at,
                    "window_convention": STRATEGY_VALIDATION_WINDOW_CONVENTION,
                    "expected_candle_count": row.expected_candle_count,
                    "actual_candle_count": row.actual_candle_count,
                    "missing_candle_count": row.missing_candle_count,
                    "readiness_status": row.readiness_status,
                    "reason_codes": reason_codes,
                    "requires_migrated_schema_before_import": True,
                    "required_file_format": "CSV or JSON accepted by scripts/import_strategy_validation_candles.py",
                    "required_file_fields": (
                        "symbol",
                        "open_time",
                        "close_time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "instrument_key_optional_but_recommended",
                        "trade_count_optional",
                    ),
                    "example_import_command": _example_import_command(row),
                }
            )
    requirements.sort(
        key=lambda item: (
            str(item["campaign_name"]),
            str(item["symbol"]),
            str(item["component"]),
            str(item["window_label"]),
        )
    )
    return tuple(_json_ready(item) for item in requirements)


def _migration_head_revisions() -> tuple[str, ...]:
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        return ()
    try:
        config = AlembicConfig(str(alembic_ini))
        script = ScriptDirectory.from_config(config)
        return tuple(sorted(script.get_heads()))
    except Exception:  # noqa: BLE001 - schema status should stay diagnostic-only.
        return ()


def _database_target_metadata(database_url: str) -> dict[str, Any]:
    try:
        parsed = make_url(database_url)
    except Exception:  # noqa: BLE001 - DB target reporting should stay diagnostic-only.
        return {
            "database_driver": None,
            "database_host": None,
            "database_port": None,
            "database_name": None,
            "database_username": None,
            "database_target_role": "unparseable_database_url",
            "intended_strategy_validation_database": False,
            "database_target_warning_reason_codes": ("database_url_unparseable",),
        }
    warnings: set[str] = set()
    database_name = parsed.database
    role = "configured_money_flow_database"
    intended = True
    if not database_name:
        role = "database_name_missing"
        intended = False
        warnings.add("database_name_missing")
    elif database_name in _MAINTENANCE_DATABASE_NAMES:
        role = "maintenance_database_name_requires_operator_confirmation"
        intended = False
        warnings.add("database_name_is_maintenance_database")
        warnings.add("strategy_validation_db_target_ambiguous")
    elif database_name != "money_flow":
        role = "non_default_configured_database"
        warnings.add("non_default_database_name")
    return {
        "database_driver": parsed.drivername,
        "database_host": parsed.host,
        "database_port": parsed.port,
        "database_name": database_name,
        "database_username": parsed.username,
        "database_target_role": role,
        "intended_strategy_validation_database": intended,
        "database_target_warning_reason_codes": tuple(sorted(warnings)),
    }


def _database_target_blocking_reason_codes(
    target_metadata: dict[str, Any],
) -> tuple[str, ...]:
    role = str(target_metadata.get("database_target_role") or "")
    intended = bool(target_metadata.get("intended_strategy_validation_database"))
    warnings = set(target_metadata.get("database_target_warning_reason_codes") or ())
    reasons: set[str] = set()
    if not intended:
        reasons.add("strategy_validation_db_target_not_intended")
    if role == "maintenance_database_name_requires_operator_confirmation":
        reasons.add("maintenance_database_target_requires_confirmation")
        reasons.add("strategy_validation_db_target_ambiguous")
    if role in {"database_name_missing", "unparseable_database_url"}:
        reasons.add("strategy_validation_db_target_ambiguous")
    if "strategy_validation_db_target_ambiguous" in warnings:
        reasons.add("strategy_validation_db_target_ambiguous")
    if reasons:
        reasons.add("evidence_generation_blocked_by_db_target_truth")
    return tuple(sorted(reasons))


def _applied_migration_revisions(
    session: Any,
    *,
    alembic_version_table_exists: bool,
) -> tuple[str, ...]:
    if not alembic_version_table_exists:
        return ()
    try:
        revisions = session.execute(text("SELECT version_num FROM alembic_version")).scalars()
        return tuple(sorted(str(revision) for revision in revisions if revision is not None))
    except Exception:  # noqa: BLE001 - a malformed alembic table is a schema-status signal.
        return ()


def _migrations_current(
    *,
    applied_revisions: Sequence[str],
    migration_heads: Sequence[str],
    alembic_version_table_exists: bool,
) -> bool | None:
    if not migration_heads or not alembic_version_table_exists:
        return None
    return set(applied_revisions) == set(migration_heads)


def _schema_status(
    *,
    reachable: bool,
    candles_table_exists: bool,
    alembic_version_table_exists: bool,
    migrations_current: bool | None,
    required_schema_tables_missing: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    reason_codes: set[str] = set()
    if not reachable:
        return (
            "database_unreachable",
            ("database_unreachable", "schema_not_ready_for_evidence_generation"),
        )
    if not alembic_version_table_exists:
        reason_codes.add("alembic_version_missing")
        reason_codes.add("alembic_version_table_missing")
    if not candles_table_exists:
        reason_codes.add("candles_table_missing")
    for table_name in required_schema_tables_missing:
        reason_codes.add(f"required_schema_table_missing_{table_name}")
    if required_schema_tables_missing:
        reason_codes.add("required_schema_missing")
    if not alembic_version_table_exists or required_schema_tables_missing:
        reason_codes.add("database_schema_not_migrated")
        reason_codes.add("database_migration_state_unknown")
        reason_codes.add("schema_not_ready_for_evidence_generation")
    if not candles_table_exists and not alembic_version_table_exists:
        reason_codes.add("schema_missing")
        return "schema_missing", tuple(sorted(reason_codes))
    if migrations_current is False:
        reason_codes.add("database_schema_outdated")
        reason_codes.add("migrations_out_of_date")
        reason_codes.add("schema_not_ready_for_evidence_generation")
        return "migrations_out_of_date", tuple(sorted(reason_codes))
    if not candles_table_exists:
        reason_codes.add("schema_not_ready_for_evidence_generation")
        return "candles_table_missing", tuple(sorted(reason_codes))
    if required_schema_tables_missing:
        return "required_schema_missing", tuple(sorted(reason_codes))
    if migrations_current is True:
        return "migrated_schema_ready", tuple(sorted(reason_codes))
    if not alembic_version_table_exists:
        reason_codes.add("schema_present_migration_version_unknown")
        return "schema_present_migration_version_unknown", tuple(sorted(reason_codes))
    reason_codes.add("schema_status_unknown")
    return "schema_status_unknown", tuple(sorted(reason_codes))


def _sanitize_database_url(value: str) -> str:
    try:
        return make_url(value).render_as_string(hide_password=True)
    except Exception:  # noqa: BLE001 - URL is diagnostic only.
        return "<unparseable_database_url>"


def _example_import_command(row: MoneyFlowResearchCampaignDataReadinessRow) -> str:
    symbol = row.symbol.lower().replace("/", "_")
    timeframe = row.timeframe or "<timeframe>"
    window_label = row.window_label.replace(" ", "_")
    input_path = f"/path/to/{symbol}_{timeframe}_{window_label}.csv"
    source_label = f"public_offline_{symbol}_{timeframe}_{window_label}"
    instrument_arg = " # include instrument_key column in the file"
    if row.instrument_key:
        instrument_arg = f" # file rows should include instrument_key={row.instrument_key}"
    return (
        "DB_HOST=<host> DB_PORT=<port> DB_USER=<user> "
        "DB_PASSWORD=<redacted> DB_NAME=<intended_money_flow_db> "
        ".venv/bin/python scripts/import_strategy_validation_candles.py "
        f"--input {input_path} "
        "--environment testnet "
        "--venue hyperliquid "
        f"--timeframe {timeframe} "
        f"--source-label {source_label}"
        f"{instrument_arg}"
    )


def _safe_error_message(exc: Exception) -> str:
    first_line = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    return first_line.replace("\n", " ")[:500]


def _blocked_or_gap_reason_codes(audit_payload: dict[str, Any]) -> tuple[str, ...]:
    summary = audit_payload["summary"]
    reasons: set[str] = set(summary.get("warning_reason_counts", {}).keys())
    reasons.update(summary.get("likely_blocked_reason_counts", {}).keys())
    if summary["thin_row_count"]:
        reasons.add("thin_data_coverage")
    if summary["missing_row_count"]:
        reasons.add("missing_persisted_candles")
    if summary["blocked_row_count"]:
        reasons.add("blocked_campaign_rows")
    return tuple(sorted(reasons))


def _insufficient_data_observations(audit_payload: dict[str, Any]) -> dict[str, Any]:
    summary = audit_payload["summary"]
    return {
        "methodology": "audit_only_no_strategy_validation_run",
        "status": "insufficient_data",
        "fill_timing_observations": "unavailable_until_campaign_runs_complete",
        "component_observations": "unavailable_until_campaign_runs_complete",
        "regime_observations": "unavailable_until_campaign_runs_complete",
        "worst_drawdown_observations": "unavailable_until_campaign_runs_complete",
        "fee_slippage_sensitivity_observations": "unavailable_until_campaign_runs_complete",
        "no_trade_reason_counts": {},
        "invalid_reason_counts": {},
        "data_gap_summary": {
            "symbols_missing_data": summary["symbols_missing_data"],
            "components_missing_data": summary["components_missing_data"],
            "windows_thin": summary["windows_thin"],
            "windows_missing": summary["windows_missing"],
            "windows_blocked": summary["windows_blocked"],
            "warning_reason_counts": summary["warning_reason_counts"],
            "likely_blocked_reason_counts": summary["likely_blocked_reason_counts"],
        },
    }


def _not_generated_observations() -> dict[str, Any]:
    return {
        "methodology": "audit_sufficient_but_evidence_generation_not_requested",
        "status": "not_reviewed",
        "fill_timing_observations": "not_generated",
        "component_observations": "not_generated",
        "regime_observations": "not_generated",
        "worst_drawdown_observations": "not_generated",
        "fee_slippage_sensitivity_observations": "not_generated",
        "no_trade_reason_counts": {},
        "invalid_reason_counts": {},
        "data_gap_summary": {},
    }


def _observations_from_batch_payload(batch_payload: dict[str, Any]) -> dict[str, Any]:
    summary = batch_payload["comparison_summary"]
    run_summaries = summary.get("run_summaries", [])
    no_trade_counts: Counter[str] = Counter()
    invalid_counts: Counter[str] = Counter()
    fee_slippage_rows: list[dict[str, Any]] = []
    for run in run_summaries:
        metrics = run.get("metrics") or {}
        no_trade_counts.update(metrics.get("no_trade_reason_counts") or {})
        invalid_counts.update(metrics.get("invalid_reason_counts") or {})
        fee_slippage_rows.append(
            {
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "fee_bps": run.get("fee_bps"),
                "slippage_bps": run.get("slippage_bps"),
                "net_pnl": metrics.get("net_pnl"),
                "total_fees": metrics.get("total_fees"),
                "total_slippage_cost": metrics.get("total_slippage_cost"),
            }
        )
    return {
        "methodology": "descriptive_observations_only_no_optimization_or_recommendation",
        "status": "evidence_pack_generated",
        "fill_timing_observations": summary.get("fill_timing_comparison"),
        "component_observations": summary.get("component_comparison"),
        "regime_observations": summary.get("regime_comparison"),
        "worst_drawdown_observations": (
            summary.get("largest_observed_mark_to_market_drawdown_run")
        ),
        "fee_slippage_sensitivity_observations": fee_slippage_rows,
        "no_trade_reason_counts": dict(sorted(no_trade_counts.items())),
        "invalid_reason_counts": dict(sorted(invalid_counts.items())),
        "highest_observed_net_pnl_run": summary.get("highest_observed_net_pnl_run"),
        "lowest_observed_net_pnl_run": summary.get("lowest_observed_net_pnl_run"),
        "data_coverage_observations": summary.get("data_coverage_comparison"),
        "blocked_run_count": sum(1 for run in run_summaries if run.get("status") != "completed"),
    }


def _review_id(*, paths: Sequence[str | Path], generated_at: datetime) -> str:
    names = "-".join(Path(path).stem for path in paths) or "money-flow-evidence-review"
    return f"{names}-{_coerce_utc(generated_at).strftime('%Y%m%dT%H%M%SZ')}"


def _assert_no_banned_recommendation_language(markdown: str) -> None:
    normalized = markdown.lower()
    for phrase in _BANNED_RECOMMENDATION_LANGUAGE:
        if phrase in normalized:
            raise ValueError(
                f"evidence review markdown contains prohibited recommendation language: {phrase}"
            )


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _coerce_utc(value).isoformat()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def money_flow_evidence_review_to_json(review: MoneyFlowEvidenceReviewSummary) -> str:
    """Serialize a review summary with deterministic key ordering."""

    return json.dumps(
        money_flow_evidence_review_to_dict(review),
        indent=2,
        sort_keys=True,
    ) + "\n"


__all__ = [
    "CANONICAL_MONEY_FLOW_CAMPAIGN_CONFIG_PATHS",
    "PAPER_READINESS_REVIEW_STATUSES",
    "REQUIRED_STRATEGY_VALIDATION_SCHEMA_TABLES",
    "MoneyFlowEvidenceReviewDatabaseStatus",
    "MoneyFlowEvidenceReviewCampaignResult",
    "MoneyFlowEvidenceReviewSummary",
    "inspect_strategy_validation_database_status",
    "money_flow_evidence_review_database_status_to_dict",
    "money_flow_evidence_review_database_status_to_json",
    "money_flow_evidence_review_database_status_to_markdown",
    "money_flow_evidence_review_to_dict",
    "money_flow_evidence_review_to_json",
    "money_flow_evidence_review_to_markdown",
    "review_money_flow_evidence",
]
