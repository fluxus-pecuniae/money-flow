"""Money Flow research campaign and evidence-pack helpers.

The campaign layer is a research workflow wrapper around the existing
Strategy Validation batch runner. It creates saved, repeatable evidence packs
without changing Money Flow rules or touching live routing/execution state.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import select

from core.domain.enums import Environment, StrategyFamily, StrategyValidationFillTiming
from core.domain.models import (
    StrategyValidationAssumptions,
    StrategyValidationBatchReport,
    StrategyValidationBatchRequest,
    StrategyValidationRequest,
)
from db.models import CandleModel, InstrumentModel
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    strategy_validation_batch_report_to_dict,
    strategy_validation_batch_report_to_markdown,
)

_WINDOW_CONVENTION_DISPLAY = "(start_at, end_at]"
_APPROVED_WINDOW_CONVENTION_TEXTS = {
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    _WINDOW_CONVENTION_DISPLAY,
    "(start_at, end_at] candle closes; closes exactly at start are excluded and closes on or before end are included.",
    "(start_at, end_at] candle closes; platform convention is authoritative.",
}
_CONTRADICTORY_WINDOW_CONVENTION_PATTERNS = (
    r"\[start(?:_at)?\s*,",
    r"\[start(?:_at)?\s*,\s*end(?:_at)?\]",
    r"inclusive\s+start",
    r"start(?:_at)?\s+is\s+included",
    r"start(?:_at)?\s+included",
    r"start(?:_at)?\s+boundary\s+is\s+included",
    r"closes\s+exactly\s+at\s+start(?:_at)?\s+are\s+included",
)
_REPORT_FORMATS = {"json", "markdown"}
_DATA_READINESS_WARNING_THRESHOLD = Decimal("0.80")
MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY = "unique_suffix"
_EVIDENCE_PACK_COLLISION_POLICIES = {
    MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
    "fail_if_exists",
}
_EVIDENCE_PACK_MAX_SUFFIX_ATTEMPTS = 999


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignSymbol:
    symbol: str
    instrument_key: str | None = None
    instrument_ref_id: str | None = None


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignWindow:
    label: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    expected_regime_label: str | None = None


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignConfig:
    campaign_name: str
    description: str
    environment: Environment
    venue: str
    symbols: tuple[MoneyFlowResearchCampaignSymbol, ...]
    components: tuple[str, ...]
    fill_timings: tuple[StrategyValidationFillTiming, ...]
    windows: tuple[MoneyFlowResearchCampaignWindow, ...]
    fee_bps_values: tuple[Decimal, ...]
    slippage_bps_values: tuple[Decimal, ...]
    initial_capital: Decimal
    position_notional_pct: Decimal
    output_dir: str
    report_formats: tuple[str, ...] = ("json", "markdown")


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignResult:
    campaign_name: str
    evidence_pack_dir: Path
    manifest: dict[str, Any]
    batch_report: StrategyValidationBatchReport


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignDataReadinessRow:
    symbol: str
    instrument_key: str | None
    instrument_ref_id: str | None
    component: str
    timeframe: str | None
    window_label: str
    requested_start_at: datetime
    requested_end_at: datetime
    window_convention: str
    expected_candle_count: int | None
    actual_candle_count: int
    missing_candle_count: int | None
    coverage_percent: Decimal | None
    gap_count: int | None
    largest_gap_seconds: int | None
    first_candle_available_at: datetime | None
    last_candle_available_at: datetime | None
    readiness_status: str
    warning_reason_codes: tuple[str, ...]
    likely_blocked: bool
    likely_blocked_reason_codes: tuple[str, ...]
    impacted_run_count: int


@dataclass(frozen=True, slots=True)
class MoneyFlowResearchCampaignDataReadinessAudit:
    campaign_name: str
    generated_at_utc: datetime
    environment: Environment
    venue: str
    window_convention: str
    window_convention_display: str
    rows: tuple[MoneyFlowResearchCampaignDataReadinessRow, ...]
    summary: dict[str, Any]
    review_checklist: dict[str, list[str]]
    manual_paper_trading_readiness_criteria: list[str]


def load_money_flow_research_campaign_config(path: str | Path) -> MoneyFlowResearchCampaignConfig:
    """Load a Money Flow research campaign config from JSON."""

    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return money_flow_research_campaign_config_from_dict(raw)


def money_flow_research_campaign_config_from_dict(
    raw: dict[str, Any],
) -> MoneyFlowResearchCampaignConfig:
    """Parse and validate a campaign config dictionary."""

    _validate_campaign_window_convention(raw)
    campaign_name = _required_str(raw, "campaign_name")
    description = _required_str(raw, "description")
    environment = Environment(_required_str(raw, "environment"))
    venue = _required_str(raw, "venue")
    symbols = tuple(_parse_symbols(_required_list(raw, "symbols")))
    components = tuple(_string_list(_required_list(raw, "components"), "components"))
    fill_timings = tuple(
        StrategyValidationFillTiming(value)
        for value in _string_list(_required_list(raw, "fill_timings"), "fill_timings")
    )
    windows = tuple(_parse_windows(_required_list(raw, "windows")))
    fee_bps_values = tuple(_decimal_list(_required_list(raw, "fee_bps_values"), "fee_bps_values"))
    slippage_bps_values = tuple(
        _decimal_list(_required_list(raw, "slippage_bps_values"), "slippage_bps_values")
    )
    initial_capital = Decimal(str(raw["initial_capital"]))
    position_notional_pct = Decimal(str(raw["position_notional_pct"]))
    output_dir = _required_str(raw, "output_dir")
    report_formats = tuple(
        _normalize_report_formats(raw.get("report_formats", ["json", "markdown"]))
    )

    if not symbols:
        raise ValueError("campaign symbols must not be empty.")
    if not components:
        raise ValueError("campaign components must not be empty.")
    if not fill_timings:
        raise ValueError("campaign fill_timings must not be empty.")
    if not windows:
        raise ValueError("campaign windows must not be empty.")
    if not fee_bps_values:
        raise ValueError("campaign fee_bps_values must not be empty.")
    if not slippage_bps_values:
        raise ValueError("campaign slippage_bps_values must not be empty.")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive.")
    if position_notional_pct <= 0 or position_notional_pct > 1:
        raise ValueError("position_notional_pct must be within (0, 1].")
    labels = [window.label for window in windows]
    duplicate_labels = sorted(label for label, count in Counter(labels).items() if count > 1)
    if duplicate_labels:
        raise ValueError(f"campaign window labels must be unique: {', '.join(duplicate_labels)}")

    return MoneyFlowResearchCampaignConfig(
        campaign_name=campaign_name,
        description=description,
        environment=environment,
        venue=venue,
        symbols=symbols,
        components=components,
        fill_timings=fill_timings,
        windows=windows,
        fee_bps_values=fee_bps_values,
        slippage_bps_values=slippage_bps_values,
        initial_capital=initial_capital,
        position_notional_pct=position_notional_pct,
        output_dir=output_dir,
        report_formats=report_formats,
    )


def money_flow_research_campaign_config_to_dict(
    config: MoneyFlowResearchCampaignConfig,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready campaign config representation."""

    return _json_ready(asdict(config))


def audit_money_flow_research_campaign_data_readiness(
    config: MoneyFlowResearchCampaignConfig,
    *,
    service: MoneyFlowBacktestService | None = None,
    generated_at: datetime | None = None,
) -> MoneyFlowResearchCampaignDataReadinessAudit:
    """Audit persisted candle readiness for a campaign without running strategy logic."""

    validation_service = service or MoneyFlowBacktestService()
    sleeves_by_key = {
        sleeve.sleeve_id: sleeve
        for sleeve in validation_service.settings.money_flow.sleeves
    }
    rows: list[MoneyFlowResearchCampaignDataReadinessRow] = []
    impacted_run_count = (
        len(config.fill_timings)
        * len(config.fee_bps_values)
        * len(config.slippage_bps_values)
    )
    with validation_service._session_factory() as session:
        for symbol in config.symbols:
            for window in config.windows:
                for component in config.components:
                    sleeve = sleeves_by_key.get(component)
                    if sleeve is None:
                        rows.append(
                            _blocked_data_readiness_row(
                                symbol=symbol,
                                component=component,
                                window=window,
                                timeframe=None,
                                reason_codes=("unknown_money_flow_component",),
                                impacted_run_count=impacted_run_count,
                            )
                        )
                        continue
                    instrument_ref_id = symbol.instrument_ref_id
                    if symbol.instrument_key is not None and instrument_ref_id is None:
                        instrument_ref_id = session.scalar(
                            select(InstrumentModel.id).where(
                                InstrumentModel.instrument_key == symbol.instrument_key
                            )
                        )
                        if instrument_ref_id is None:
                            rows.append(
                                _blocked_data_readiness_row(
                                    symbol=symbol,
                                    component=component,
                                    window=window,
                                    timeframe=sleeve.timeframe.value,
                                    reason_codes=("unknown_instrument_key",),
                                    impacted_run_count=impacted_run_count,
                                )
                            )
                            continue
                    query = (
                        select(CandleModel.close_time)
                        .where(
                            CandleModel.environment == config.environment,
                            CandleModel.venue == config.venue,
                            CandleModel.symbol == symbol.symbol,
                            CandleModel.timeframe == sleeve.timeframe,
                            CandleModel.close_time > window.start_at,
                            CandleModel.close_time <= window.end_at,
                        )
                        .order_by(CandleModel.close_time.asc())
                    )
                    if instrument_ref_id is not None:
                        query = query.where(CandleModel.instrument_ref_id == instrument_ref_id)
                    close_times = [_coerce_utc(value) for value in session.scalars(query).all()]
                    rows.append(
                        _data_readiness_row_from_close_times(
                            symbol=symbol,
                            component=component,
                            timeframe=sleeve.timeframe.value,
                            window=window,
                            close_times=close_times,
                            impacted_run_count=impacted_run_count,
                        )
                    )

    return MoneyFlowResearchCampaignDataReadinessAudit(
        campaign_name=config.campaign_name,
        generated_at_utc=_coerce_utc(generated_at or datetime.now(UTC)).replace(microsecond=0),
        environment=config.environment,
        venue=config.venue,
        window_convention=STRATEGY_VALIDATION_WINDOW_CONVENTION,
        window_convention_display=_WINDOW_CONVENTION_DISPLAY,
        rows=tuple(rows),
        summary=_data_readiness_summary(rows),
        review_checklist=money_flow_evidence_pack_review_checklist(),
        manual_paper_trading_readiness_criteria=(
            money_flow_manual_paper_trading_readiness_criteria()
        ),
    )


def money_flow_research_campaign_data_readiness_to_dict(
    audit: MoneyFlowResearchCampaignDataReadinessAudit,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready data-readiness audit representation."""

    return _json_ready(asdict(audit))


def money_flow_research_campaign_data_readiness_to_markdown(
    audit: MoneyFlowResearchCampaignDataReadinessAudit,
) -> str:
    """Render a founder/operator-readable campaign data-readiness audit."""

    payload = money_flow_research_campaign_data_readiness_to_dict(audit)
    summary = payload["summary"]
    lines = [
        f"# Money Flow Campaign Data-Readiness Audit `{audit.campaign_name}`",
        "",
        "This is a read-only research data-readiness audit. It does not run strategy validation, "
        "does not create evidence packs, does not create live artifacts, and does not call exchange adapters.",
        "",
        "## Context",
        "",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- Environment: `{payload['environment']}`",
        f"- Venue/source: `{payload['venue']}`",
        f"- Window convention: `{payload['window_convention']}` `{payload['window_convention_display']}`",
        "- Candle closes exactly at `start_at` are excluded.",
        "- Candle closes on or before `end_at` are included.",
        "",
        "## Founder Review Summary",
        "",
        f"- Total symbol/component/window rows: `{summary['row_count']}`",
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
        f"- Windows blocked: `{summary['windows_blocked']}`",
        f"- Warning reason counts: `{summary['warning_reason_counts']}`",
        f"- Likely blocked reason counts: `{summary['likely_blocked_reason_counts']}`",
        "",
        "## Data Coverage Rows",
        "",
        "| symbol | component | timeframe | window | status | expected | actual | missing | coverage | gaps | largest gap seconds | warnings | likely blocked reasons |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            f"`{row['symbol']}` | "
            f"`{row['component']}` | "
            f"`{row['timeframe']}` | "
            f"`{row['window_label']}` | "
            f"`{row['readiness_status']}` | "
            f"{row['expected_candle_count']} | "
            f"{row['actual_candle_count']} | "
            f"{row['missing_candle_count']} | "
            f"{row['coverage_percent']} | "
            f"{row['gap_count']} | "
            f"{row['largest_gap_seconds']} | "
            f"`{row['warning_reason_codes']}` | "
            f"`{row['likely_blocked_reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Missing-Data Remediation Notes",
            "",
            "- Backfill or import public historical candles for rows marked `missing`, `thin`, or `blocked` before treating campaign evidence as meaningful.",
            "- Offline candle import is preferred when persisted candles are absent and a trusted public CSV/JSON dataset is available.",
            "- Thin or missing rows should be reviewed manually; they are not strategy failures and they are not evidence of edge.",
            "- This audit is not an optimization, recommendation, paper-trading approval, or proof of profitability.",
            "",
            "## Manual Evidence-Pack Review Checklist",
            "",
        ]
    )
    for section, items in payload["review_checklist"].items():
        lines.append(f"### {section.replace('_', ' ').title()}")
        lines.append("")
        lines.extend(f"- [ ] {item}" for item in items)
        lines.append("")
    lines.extend(
        [
            "## Manual Paper-Trading Readiness Criteria",
            "",
            "These criteria are manual founder/operator review inputs only. They do not auto-approve paper trading, create paper trades, or create live artifacts.",
            "",
        ]
    )
    lines.extend(
        f"- [ ] {item}" for item in payload["manual_paper_trading_readiness_criteria"]
    )
    return "\n".join(lines) + "\n"


def money_flow_evidence_pack_review_checklist() -> dict[str, list[str]]:
    """Founder/operator checklist for manual evidence-pack review."""

    return {
        "data_quality": [
            "Review coverage percent for every symbol/component/window.",
            "Review missing candle count, gap count, largest gap, and blocked run reasons.",
            "Do not interpret thin or missing windows as absent evidence.",
        ],
        "fill_timing_robustness": [
            "Compare same-candle close, next-candle open, and next-candle close results.",
            "Treat same-candle close as research-only and potentially optimistic.",
            "Check whether observed edge disappears under next-candle fill timing.",
        ],
        "regime_behavior": [
            "Review uptrend, downtrend, sideways, high-volatility, and low-volatility groups.",
            "Check whether performance is concentrated in one narrow regime or window.",
            "Treat regime labels as descriptive only, not strategy filters.",
        ],
        "component_behavior": [
            "Compare sleeve_15m, sleeve_1h, and sleeve_4h separately.",
            "Review trade count, no-trade reasons, invalid reasons, and component drawdowns.",
            "Do not treat component comparison as parameter optimization.",
        ],
        "risk_behavior": [
            "Review mark-to-market drawdown, closed-trade drawdown, worst trade, average loss, and profit factor.",
            "Check whether drawdowns exceed founder/operator research tolerance.",
            "Review forced end-of-window closes before interpreting trade outcomes.",
        ],
        "fees_and_slippage": [
            "Compare fee and slippage assumptions across runs.",
            "Check whether small cost increases erase observed net PnL.",
            "Remember the simulator has no order-book replay, partial-fill, latency, funding, or liquidation model.",
        ],
        "paper_trading_readiness": [
            "Use the manual readiness criteria as founder/operator review inputs only.",
            "Do not auto-approve paper trading from a campaign report.",
            "Do not create paper trades, live trades, routing artifacts, or execution artifacts from validation output.",
        ],
    }


def money_flow_manual_paper_trading_readiness_criteria() -> list[str]:
    """Manual-only criteria for deciding whether paper trading is worth scoping."""

    return [
        "Selected campaign windows meet the founder-defined minimum data coverage threshold.",
        "No critical selected campaign run is blocked or missing without an understood reason.",
        "Observed performance survives next-candle open or next-candle close timing assumptions.",
        "Mark-to-market drawdown remains within founder/operator research tolerance.",
        "Profit factor and win/loss behavior remain acceptable under explicit fee and slippage assumptions.",
        "Observed outcomes are not concentrated in one tiny window, one symbol, or one regime.",
        "Fees, slippage, and no-trade/invalid reason counts are understood.",
        "Founder/operator review is complete; this is not an automated go/no-go decision.",
    ]


def build_money_flow_research_campaign_batch_request(
    config: MoneyFlowResearchCampaignConfig,
) -> StrategyValidationBatchRequest:
    """Build the explicit batch matrix represented by a campaign config."""

    runs: list[StrategyValidationRequest] = []
    for symbol in config.symbols:
        for window in config.windows:
            for component in config.components:
                for fill_timing in config.fill_timings:
                    for fee_bps in config.fee_bps_values:
                        for slippage_bps in config.slippage_bps_values:
                            runs.append(
                                StrategyValidationRequest(
                                    strategy_family=StrategyFamily.MONEY_FLOW,
                                    environment=config.environment,
                                    venue=config.venue,
                                    symbol=symbol.symbol,
                                    instrument_key=symbol.instrument_key,
                                    instrument_ref_id=symbol.instrument_ref_id,
                                    component_keys=(component,),
                                    start_at=window.start_at,
                                    end_at=window.end_at,
                                    assumptions=StrategyValidationAssumptions(
                                        initial_capital=config.initial_capital,
                                        fee_bps=fee_bps,
                                        slippage_bps=slippage_bps,
                                        fill_timing=fill_timing,
                                        position_notional_pct=config.position_notional_pct,
                                    ),
                                )
                            )
    return StrategyValidationBatchRequest(
        runs=tuple(runs),
        batch_name=config.campaign_name,
    )


def money_flow_research_campaign_run_contexts(
    config: MoneyFlowResearchCampaignConfig,
    batch_report: StrategyValidationBatchReport | None = None,
) -> list[dict[str, Any]]:
    """Return per-run campaign context aligned with batch run order."""

    contexts: list[dict[str, Any]] = []
    reports_by_index = (
        {run.run_index: run for run in batch_report.run_reports}
        if batch_report is not None
        else {}
    )
    run_index = 0
    for symbol in config.symbols:
        for window in config.windows:
            for component in config.components:
                for fill_timing in config.fill_timings:
                    for fee_bps in config.fee_bps_values:
                        for slippage_bps in config.slippage_bps_values:
                            run = reports_by_index.get(run_index)
                            context = {
                                "run_index": run_index,
                                "run_id": run.run_id if run is not None else None,
                                "report_id": run.report_id if run is not None else None,
                                "status": run.status if run is not None else None,
                                "reason_codes": list(run.reason_codes) if run is not None else [],
                                "error_message": run.error_message if run is not None else None,
                                "window_label": window.label,
                                "window_description": window.description,
                                "expected_regime_label": window.expected_regime_label,
                                "start_at": window.start_at,
                                "end_at": window.end_at,
                                "window_convention": STRATEGY_VALIDATION_WINDOW_CONVENTION,
                                "symbol": symbol.symbol,
                                "instrument_key": symbol.instrument_key,
                                "instrument_ref_id": symbol.instrument_ref_id,
                                "component": component,
                                "fill_timing": fill_timing,
                                "fee_bps": fee_bps,
                                "slippage_bps": slippage_bps,
                            }
                            contexts.append(_json_ready(context))
                            run_index += 1
    return contexts


async def run_money_flow_research_campaign(
    config: MoneyFlowResearchCampaignConfig,
    *,
    service: MoneyFlowBacktestService | None = None,
    output_dir: str | Path | None = None,
    report_formats: Sequence[str] | None = None,
    run_timestamp: datetime | None = None,
    evidence_pack_collision_policy: str = MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
) -> MoneyFlowResearchCampaignResult:
    """Run a campaign and write its evidence pack."""

    validation_service = service or MoneyFlowBacktestService()
    batch_report = await validation_service.run_money_flow_batch_backtest(
        build_money_flow_research_campaign_batch_request(config)
    )
    evidence_pack_dir, manifest = write_money_flow_research_campaign_evidence_pack(
        config,
        batch_report,
        output_dir=output_dir,
        report_formats=report_formats,
        run_timestamp=run_timestamp,
        evidence_pack_collision_policy=evidence_pack_collision_policy,
    )
    return MoneyFlowResearchCampaignResult(
        campaign_name=config.campaign_name,
        evidence_pack_dir=evidence_pack_dir,
        manifest=manifest,
        batch_report=batch_report,
    )


def run_money_flow_research_campaign_sync(
    config: MoneyFlowResearchCampaignConfig,
    *,
    service: MoneyFlowBacktestService | None = None,
    output_dir: str | Path | None = None,
    report_formats: Sequence[str] | None = None,
    run_timestamp: datetime | None = None,
    evidence_pack_collision_policy: str = MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
) -> MoneyFlowResearchCampaignResult:
    """Synchronous convenience wrapper for CLI callers."""

    return asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            output_dir=output_dir,
            report_formats=report_formats,
            run_timestamp=run_timestamp,
            evidence_pack_collision_policy=evidence_pack_collision_policy,
        )
    )


def write_money_flow_research_campaign_evidence_pack(
    config: MoneyFlowResearchCampaignConfig,
    batch_report: StrategyValidationBatchReport,
    *,
    output_dir: str | Path | None = None,
    report_formats: Sequence[str] | None = None,
    run_timestamp: datetime | None = None,
    evidence_pack_collision_policy: str = MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY,
) -> tuple[Path, dict[str, Any]]:
    """Write a campaign evidence pack directory and return its manifest."""

    formats = tuple(_normalize_report_formats(report_formats or config.report_formats))
    collision_policy = _normalize_evidence_pack_collision_policy(
        evidence_pack_collision_policy
    )
    timestamp = _coerce_utc(run_timestamp or datetime.now(UTC)).replace(microsecond=0)
    campaign_slug = _safe_slug(config.campaign_name)
    requested_run_id = timestamp.strftime("%Y%m%dT%H%M%SZ")
    evidence_pack_dir, final_run_id, collision_occurred, collision_suffix = (
        _reserve_evidence_pack_dir(
            root=Path(output_dir or config.output_dir) / campaign_slug,
            requested_run_id=requested_run_id,
            collision_policy=collision_policy,
        )
    )

    config_payload = money_flow_research_campaign_config_to_dict(config)
    batch_payload = strategy_validation_batch_report_to_dict(batch_report)
    run_contexts = money_flow_research_campaign_run_contexts(config, batch_report)
    manifest = _campaign_manifest(
        config=config,
        batch_report=batch_report,
        run_timestamp=timestamp,
        run_contexts=run_contexts,
        formats=formats,
        campaign_slug=campaign_slug,
        requested_run_id=requested_run_id,
        final_run_id=final_run_id,
        evidence_pack_dir=evidence_pack_dir,
        collision_policy=collision_policy,
        collision_occurred=collision_occurred,
        collision_suffix=collision_suffix,
    )

    _write_json(evidence_pack_dir / "campaign_config.json", config_payload)
    report_paths: dict[str, str] = {
        "campaign_config": "campaign_config.json",
        "manifest": "manifest.json",
        "readme": "README.md",
    }
    if "json" in formats:
        report_paths["batch_report_json"] = "batch_report.json"
    if "markdown" in formats:
        report_paths["batch_report_markdown"] = "batch_report.md"
    manifest["report_paths"] = report_paths

    if "json" in formats:
        _write_json(evidence_pack_dir / "batch_report.json", batch_payload)
    if "markdown" in formats:
        markdown = money_flow_research_campaign_report_to_markdown(
            config=config,
            batch_report=batch_report,
            manifest=manifest,
        )
        _write_text_once(evidence_pack_dir / "batch_report.md", markdown)

    _write_json(evidence_pack_dir / "manifest.json", manifest)
    _write_text_once(evidence_pack_dir / "README.md", _evidence_pack_readme(config, manifest))
    return evidence_pack_dir, manifest


def money_flow_research_campaign_report_to_markdown(
    *,
    config: MoneyFlowResearchCampaignConfig,
    batch_report: StrategyValidationBatchReport,
    manifest: dict[str, Any],
) -> str:
    """Render a founder/operator-readable campaign evidence-pack report."""

    batch_data = strategy_validation_batch_report_to_dict(batch_report)
    summary = batch_data["comparison_summary"]
    lines = [
        f"# Money Flow Research Campaign Evidence Pack `{config.campaign_name}`",
        "",
        "This is a repeatable research evidence pack. It is not optimization, "
        "does not recommend a strategy variant, does not create live trading artifacts, "
        "and does not prove future profitability.",
        "",
        "## Campaign Context",
        "",
        f"- Campaign name: `{config.campaign_name}`",
        f"- Description: {config.description}",
        f"- Run timestamp UTC: `{manifest['run_timestamp_utc']}`",
        f"- Requested run id: `{manifest['requested_run_id']}`",
        f"- Final run id: `{manifest['final_run_id']}`",
        f"- Evidence pack collision policy: `{manifest['evidence_pack_collision_policy']}`",
        f"- Collision occurred: `{manifest['evidence_pack_collision_occurred']}`",
        f"- Batch id: `{batch_data['batch_id']}`",
        f"- Strategy family: `{batch_data['strategy_family']}`",
        f"- Environment: `{config.environment.value}`",
        f"- Venue/source: `{config.venue}`",
        f"- Window convention: `{STRATEGY_VALIDATION_WINDOW_CONVENTION}` "
        f"`{_WINDOW_CONVENTION_DISPLAY}`",
        "- Candle closes exactly at `start_at` are excluded.",
        "- Candle closes on or before `end_at` are included.",
        f"- Live execution artifacts created: `{not batch_data['no_live_execution_artifacts_created']}`",
        f"- Exchange adapters called: `{batch_data['exchange_adapters_called']}`",
        "",
        "## Assumptions Matrix",
        "",
        f"- Symbols: `{manifest['symbols']}`",
        f"- Components: `{manifest['components']}`",
        f"- Fill timings: `{manifest['fill_timings']}`",
        f"- Fee bps values: `{manifest['fee_bps_values']}`",
        f"- Slippage bps values: `{manifest['slippage_bps_values']}`",
        f"- Initial capital: `{manifest['initial_capital']}`",
        f"- Position notional pct: `{manifest['position_notional_pct']}`",
        f"- Assumptions hash: `{manifest['assumptions_hash']}`",
        "",
        "## Named Windows",
        "",
        "| label | start | end | expected regime annotation | description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for window in manifest["windows"]:
        lines.append(
            "| "
            f"`{window['label']}` | "
            f"`{window['start_at']}` | "
            f"`{window['end_at']}` | "
            f"`{window['expected_regime_label']}` | "
            f"{window['description'] or ''} |"
        )
    lines.extend(
        [
            "",
            "Expected regime annotations are human context only. They do not alter computed regimes, entries, exits, sizing, routing, or execution.",
            "",
            "## Evidence Files",
            "",
        ]
    )
    for key, path in manifest["report_paths"].items():
        lines.append(f"- {key}: `{path}`")
    lines.extend(
        [
            "",
            "## Run Summary With Window Labels",
            "",
            "| run id | status | window label | symbol | component | fill timing | fee bps | slippage bps | reason codes |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for context in manifest["run_contexts"]:
        lines.append(
            "| "
            f"`{context['run_id']}` | "
            f"`{context['status']}` | "
            f"`{context['window_label']}` | "
            f"`{context['symbol']}` | "
            f"`{context['component']}` | "
            f"`{context['fill_timing']}` | "
            f"{context['fee_bps']} | "
            f"{context['slippage_bps']} | "
            f"`{context['reason_codes']}` |"
        )
    lines.extend(
        [
            "",
            "## Blocked Runs",
            "",
            f"- Blocked run count: `{manifest['blocked_run_count']}`",
            f"- Blocked reason counts: `{manifest['blocked_reason_counts']}`",
            "",
            "## Observed Run Extremes",
            "",
            f"- Highest observed net PnL: `{summary['highest_observed_net_pnl_run']}`",
            f"- Lowest observed net PnL: `{summary['lowest_observed_net_pnl_run']}`",
            f"- Highest observed win rate: `{summary['highest_observed_win_rate_run']}`",
            "- Largest observed mark-to-market drawdown: "
            f"`{summary['largest_observed_mark_to_market_drawdown_run']}`",
            f"- Most active run by trade count: `{summary['most_trades_run']}`",
            f"- Least active run by trade count: `{summary['least_trades_run']}`",
            "",
            "## Limitations",
            "",
            "- Campaign outputs are research-only and do not prove future profitability.",
            "- Campaign outputs are not paper trading, live trading, routing, or execution automation.",
            "- Simulated trades are not `SubmittedOrder` rows.",
            "- No exchange adapters are called.",
            "- Window labels use candle closes in `(start_at, end_at]`; adjacent windows do not double-count boundary closes.",
            "- Same-candle close fill timing is research-only and can overstate edge.",
            "- Data coverage warnings must be reviewed before interpreting run outcomes.",
            "- Blocked runs remain visible and should not be treated as absent configurations.",
            "",
            "## Evidence-Pack Review Checklist",
            "",
        ]
    )
    for section, items in manifest["review_checklist"].items():
        lines.append(f"### {section.replace('_', ' ').title()}")
        lines.append("")
        lines.extend(f"- [ ] {item}" for item in items)
        lines.append("")
    lines.extend(
        [
            "## Manual Paper-Trading Readiness Criteria",
            "",
            "These criteria are manual founder/operator review inputs only. They do not auto-approve paper trading, create paper trades, or create live artifacts.",
            "",
        ]
    )
    lines.extend(
        f"- [ ] {item}" for item in manifest["manual_paper_trading_readiness_criteria"]
    )
    lines.extend(
        [
            "",
            "## Batch Comparison Report",
            "",
        ]
    )
    lines.append(strategy_validation_batch_report_to_markdown(batch_report).rstrip())
    return "\n".join(lines) + "\n"


def _campaign_manifest(
    *,
    config: MoneyFlowResearchCampaignConfig,
    batch_report: StrategyValidationBatchReport,
    run_timestamp: datetime,
    run_contexts: list[dict[str, Any]],
    formats: tuple[str, ...],
    campaign_slug: str,
    requested_run_id: str,
    final_run_id: str,
    evidence_pack_dir: Path,
    collision_policy: str,
    collision_occurred: bool,
    collision_suffix: str | None,
) -> dict[str, Any]:
    blocked = [run for run in batch_report.run_reports if run.status != "completed"]
    blocked_reason_counts: Counter[str] = Counter()
    for run in blocked:
        blocked_reason_counts.update(run.reason_codes or ["strategy_validation_run_blocked"])
    config_payload = money_flow_research_campaign_config_to_dict(config)
    return {
        "campaign_name": config.campaign_name,
        "campaign_slug": campaign_slug,
        "description": config.description,
        "run_timestamp_utc": _coerce_utc(run_timestamp).isoformat(),
        "requested_run_timestamp_utc": _coerce_utc(run_timestamp).isoformat(),
        "requested_run_id": requested_run_id,
        "final_run_id": final_run_id,
        "final_evidence_pack_path": str(evidence_pack_dir),
        "evidence_pack_collision_policy": collision_policy,
        "evidence_pack_collision_occurred": collision_occurred,
        "evidence_pack_collision_suffix": collision_suffix,
        "strategy_family": StrategyFamily.MONEY_FLOW.value,
        "batch_id": batch_report.batch_id,
        "batch_name": batch_report.batch_name,
        "repo": _repo_metadata(),
        "assumptions_hash": _stable_hash(
            {
                "campaign_name": config.campaign_name,
                "environment": config.environment,
                "venue": config.venue,
                "symbols": config.symbols,
                "components": config.components,
                "fill_timings": config.fill_timings,
                "windows": config.windows,
                "fee_bps_values": config.fee_bps_values,
                "slippage_bps_values": config.slippage_bps_values,
                "initial_capital": config.initial_capital,
                "position_notional_pct": config.position_notional_pct,
                "window_convention": STRATEGY_VALIDATION_WINDOW_CONVENTION,
            }
        ),
        "symbols": [symbol.symbol for symbol in config.symbols],
        "symbol_details": _json_ready(config.symbols),
        "components": list(config.components),
        "windows": [
            {
                "label": window.label,
                "start_at": window.start_at,
                "end_at": window.end_at,
                "description": window.description,
                "expected_regime_label": window.expected_regime_label,
            }
            for window in config.windows
        ],
        "window_convention": STRATEGY_VALIDATION_WINDOW_CONVENTION,
        "window_convention_display": _WINDOW_CONVENTION_DISPLAY,
        "fill_timings": [item.value for item in config.fill_timings],
        "fee_bps_values": [str(value) for value in config.fee_bps_values],
        "slippage_bps_values": [str(value) for value in config.slippage_bps_values],
        "initial_capital": str(config.initial_capital),
        "position_notional_pct": str(config.position_notional_pct),
        "report_formats": list(formats),
        "run_count": len(batch_report.run_reports),
        "completed_run_count": len(batch_report.run_reports) - len(blocked),
        "blocked_run_count": len(blocked),
        "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
        "warnings": list(batch_report.warnings),
        "limitations": list(batch_report.limitations),
        "review_checklist": money_flow_evidence_pack_review_checklist(),
        "manual_paper_trading_readiness_criteria": (
            money_flow_manual_paper_trading_readiness_criteria()
        ),
        "run_contexts": run_contexts,
        "config": config_payload,
        "no_live_execution_artifacts_created": batch_report.no_live_execution_artifacts_created,
        "exchange_adapters_called": batch_report.exchange_adapters_called,
        "report_paths": {},
    }


def _evidence_pack_readme(
    config: MoneyFlowResearchCampaignConfig,
    manifest: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# Money Flow Research Campaign `{config.campaign_name}`",
            "",
            "This directory is a Money Flow Strategy Validation research evidence pack.",
            "",
            "- `campaign_config.json` is the normalized campaign input.",
            "- `manifest.json` records run metadata, assumptions hash, window convention, blocked-run counts, and report paths.",
            "- `batch_report.json` and `batch_report.md` contain the batch validation output when those formats are requested.",
            "- The report includes a manual evidence-pack review checklist and manual paper-trading readiness criteria.",
            "- Evidence packs use collision policy `unique_suffix` by default; repeated runs never silently overwrite prior packs.",
            "- The window convention is `(start_at, end_at]`: candle closes exactly at `start_at` are excluded and closes on or before `end_at` are included.",
            "- Outputs are research-only. They are not paper trading, live execution, routing, optimization, or proof of future profitability.",
            "",
            f"Run timestamp UTC: `{manifest['run_timestamp_utc']}`",
            f"Final run id: `{manifest['final_run_id']}`",
            f"Evidence pack collision policy: `{manifest['evidence_pack_collision_policy']}`",
        ]
    ) + "\n"


def _blocked_data_readiness_row(
    *,
    symbol: MoneyFlowResearchCampaignSymbol,
    component: str,
    window: MoneyFlowResearchCampaignWindow,
    timeframe: str | None,
    reason_codes: tuple[str, ...],
    impacted_run_count: int,
) -> MoneyFlowResearchCampaignDataReadinessRow:
    return MoneyFlowResearchCampaignDataReadinessRow(
        symbol=symbol.symbol,
        instrument_key=symbol.instrument_key,
        instrument_ref_id=symbol.instrument_ref_id,
        component=component,
        timeframe=timeframe,
        window_label=window.label,
        requested_start_at=window.start_at,
        requested_end_at=window.end_at,
        window_convention=STRATEGY_VALIDATION_WINDOW_CONVENTION,
        expected_candle_count=None,
        actual_candle_count=0,
        missing_candle_count=None,
        coverage_percent=None,
        gap_count=None,
        largest_gap_seconds=None,
        first_candle_available_at=None,
        last_candle_available_at=None,
        readiness_status="blocked",
        warning_reason_codes=reason_codes,
        likely_blocked=True,
        likely_blocked_reason_codes=reason_codes,
        impacted_run_count=impacted_run_count,
    )


def _data_readiness_row_from_close_times(
    *,
    symbol: MoneyFlowResearchCampaignSymbol,
    component: str,
    timeframe: str,
    window: MoneyFlowResearchCampaignWindow,
    close_times: list[datetime],
    impacted_run_count: int,
) -> MoneyFlowResearchCampaignDataReadinessRow:
    timeframe_delta = _campaign_timeframe_delta(timeframe)
    expected_count: int | None = None
    missing_count: int | None = None
    coverage_percent: Decimal | None = None
    gap_count: int | None = None
    largest_gap_seconds: int | None = None
    warnings: list[str] = []
    if timeframe_delta is None:
        warnings.append("expected_candle_count_not_derivable_for_timeframe")
    else:
        expected_count = _campaign_expected_close_slot_count(
            start_at=window.start_at,
            end_at=window.end_at,
            timeframe_delta_seconds=timeframe_delta,
        )
        missing_count = max(expected_count - len(close_times), 0)
        coverage_percent = (
            _campaign_ratio(Decimal(len(close_times)), Decimal(expected_count))
            if expected_count > 0
            else None
        )
        if coverage_percent is not None:
            coverage_percent = min(coverage_percent, Decimal("1.00000000"))
        gaps = [
            int((later - earlier).total_seconds())
            for earlier, later in zip(close_times, close_times[1:], strict=False)
            if int((later - earlier).total_seconds()) > timeframe_delta
        ]
        gap_count = len(gaps)
        largest_gap_seconds = max(gaps) if gaps else 0
        if _campaign_has_unaligned_window_boundary(
            start_at=window.start_at,
            end_at=window.end_at,
            timeframe_delta_seconds=timeframe_delta,
        ):
            warnings.append("unaligned_window_boundary")
        if len(close_times) > expected_count:
            warnings.append("actual_candles_exceed_expected_close_slots")
        if coverage_percent is not None and coverage_percent < _DATA_READINESS_WARNING_THRESHOLD:
            warnings.append("data_coverage_below_review_threshold")
        if missing_count > 0:
            warnings.append("missing_candles_in_requested_window")
        if gap_count > 0:
            warnings.append("candle_gaps_detected")
    likely_blocked_reason_codes: list[str] = []
    if not close_times:
        warnings.append("no_candles_in_requested_window")
        likely_blocked_reason_codes.append("no_candles_in_requested_window")
    if likely_blocked_reason_codes:
        readiness_status = "missing"
    elif coverage_percent is not None and coverage_percent < _DATA_READINESS_WARNING_THRESHOLD:
        readiness_status = "thin"
    elif missing_count is not None and missing_count > 0:
        readiness_status = "thin"
    else:
        readiness_status = "covered"
    return MoneyFlowResearchCampaignDataReadinessRow(
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
        actual_candle_count=len(close_times),
        missing_candle_count=missing_count,
        coverage_percent=coverage_percent,
        gap_count=gap_count,
        largest_gap_seconds=largest_gap_seconds,
        first_candle_available_at=close_times[0] if close_times else None,
        last_candle_available_at=close_times[-1] if close_times else None,
        readiness_status=readiness_status,
        warning_reason_codes=tuple(sorted(set(warnings))),
        likely_blocked=bool(likely_blocked_reason_codes),
        likely_blocked_reason_codes=tuple(sorted(set(likely_blocked_reason_codes))),
        impacted_run_count=impacted_run_count,
    )


def _data_readiness_summary(
    rows: list[MoneyFlowResearchCampaignDataReadinessRow],
) -> dict[str, Any]:
    status_counts = Counter(row.readiness_status for row in rows)
    warning_counts: Counter[str] = Counter()
    blocked_counts: Counter[str] = Counter()
    for row in rows:
        warning_counts.update(row.warning_reason_codes)
        blocked_counts.update(row.likely_blocked_reason_codes)
    coverage_values = [
        row.coverage_percent
        for row in rows
        if row.coverage_percent is not None
    ]
    symbols_with_data = sorted({row.symbol for row in rows if row.actual_candle_count > 0})
    symbols_missing_data = sorted(
        {
            row.symbol
            for row in rows
            if row.actual_candle_count == 0 or row.readiness_status in {"missing", "blocked"}
        }
    )
    components_with_data = sorted({row.component for row in rows if row.actual_candle_count > 0})
    components_missing_data = sorted(
        {
            row.component
            for row in rows
            if row.actual_candle_count == 0 or row.readiness_status in {"missing", "blocked"}
        }
    )
    return {
        "methodology": "campaign_data_readiness_audit_counts_persisted_candle_closes_only",
        "window_convention": STRATEGY_VALIDATION_WINDOW_CONVENTION,
        "window_convention_display": _WINDOW_CONVENTION_DISPLAY,
        "row_count": len(rows),
        "covered_row_count": status_counts.get("covered", 0),
        "thin_row_count": status_counts.get("thin", 0),
        "missing_row_count": status_counts.get("missing", 0),
        "blocked_row_count": status_counts.get("blocked", 0),
        "likely_blocked_impacted_run_count": sum(
            row.impacted_run_count for row in rows if row.likely_blocked
        ),
        "minimum_coverage_percent": min(coverage_values) if coverage_values else None,
        "symbols_with_data": symbols_with_data,
        "symbols_missing_data": symbols_missing_data,
        "components_with_data": components_with_data,
        "components_missing_data": components_missing_data,
        "windows_covered": sorted(
            {row.window_label for row in rows if row.readiness_status == "covered"}
        ),
        "windows_thin": sorted(
            {row.window_label for row in rows if row.readiness_status == "thin"}
        ),
        "windows_missing": sorted(
            {row.window_label for row in rows if row.readiness_status == "missing"}
        ),
        "windows_blocked": sorted(
            {row.window_label for row in rows if row.readiness_status == "blocked"}
        ),
        "warning_reason_counts": dict(sorted(warning_counts.items())),
        "likely_blocked_reason_counts": dict(sorted(blocked_counts.items())),
        "manual_review_required": True,
        "paper_trading_auto_approved": False,
        "creates_live_artifacts": False,
        "calls_exchange_adapters": False,
    }


def _campaign_timeframe_delta(timeframe: str) -> int | None:
    return {
        "1m": 60,
        "5m": 5 * 60,
        "15m": 15 * 60,
        "1h": 60 * 60,
        "4h": 4 * 60 * 60,
        "1d": 24 * 60 * 60,
    }.get(timeframe)


def _campaign_expected_close_slot_count(
    *,
    start_at: datetime,
    end_at: datetime,
    timeframe_delta_seconds: int,
) -> int:
    if end_at <= start_at or timeframe_delta_seconds <= 0:
        return 0
    start_seconds = int(start_at.timestamp())
    end_seconds = int(end_at.timestamp())
    first_close_slot = ((start_seconds // timeframe_delta_seconds) + 1) * timeframe_delta_seconds
    if first_close_slot > end_seconds:
        return 0
    return ((end_seconds - first_close_slot) // timeframe_delta_seconds) + 1


def _campaign_has_unaligned_window_boundary(
    *,
    start_at: datetime,
    end_at: datetime,
    timeframe_delta_seconds: int,
) -> bool:
    if timeframe_delta_seconds <= 0:
        return False
    return (
        int(start_at.timestamp()) % timeframe_delta_seconds != 0
        or int(end_at.timestamp()) % timeframe_delta_seconds != 0
    )


def _campaign_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(Decimal("0.00000001"))


def _validate_campaign_window_convention(raw: dict[str, Any]) -> None:
    supplied = raw.get("window_convention")
    if supplied is None:
        return
    if not isinstance(supplied, str) or not supplied.strip():
        raise ValueError(
            "campaign window_convention, when supplied, must describe the platform "
            "convention `(start_at, end_at]`."
        )
    text = supplied.strip()
    normalized = re.sub(r"\s+", " ", text.lower())
    if any(
        re.search(pattern, normalized)
        for pattern in _CONTRADICTORY_WINDOW_CONVENTION_PATTERNS
    ):
        raise ValueError(
            "campaign window_convention conflicts with the platform convention "
            f"`{STRATEGY_VALIDATION_WINDOW_CONVENTION}` `{_WINDOW_CONVENTION_DISPLAY}`: "
            "candle closes exactly at start_at are excluded and closes on or before "
            "end_at are included."
        )
    if text in _APPROVED_WINDOW_CONVENTION_TEXTS:
        return
    raise ValueError(
        "campaign window_convention is display metadata only and must use the "
        f"platform convention `{STRATEGY_VALIDATION_WINDOW_CONVENTION}` "
        f"`{_WINDOW_CONVENTION_DISPLAY}`: candle closes exactly at start_at are "
        "excluded and closes on or before end_at are included."
    )


def _parse_symbols(raw_symbols: list[Any]) -> list[MoneyFlowResearchCampaignSymbol]:
    symbols: list[MoneyFlowResearchCampaignSymbol] = []
    for item in raw_symbols:
        if isinstance(item, str):
            symbols.append(MoneyFlowResearchCampaignSymbol(symbol=item))
            continue
        if not isinstance(item, dict):
            raise ValueError("symbols entries must be strings or objects.")
        symbols.append(
            MoneyFlowResearchCampaignSymbol(
                symbol=_required_str(item, "symbol"),
                instrument_key=item.get("instrument_key"),
                instrument_ref_id=item.get("instrument_ref_id"),
            )
        )
    return symbols


def _parse_windows(raw_windows: list[Any]) -> list[MoneyFlowResearchCampaignWindow]:
    windows: list[MoneyFlowResearchCampaignWindow] = []
    for item in raw_windows:
        if not isinstance(item, dict):
            raise ValueError("window entries must be objects.")
        start_at = _parse_datetime(_required_str(item, "start"))
        end_at = _parse_datetime(_required_str(item, "end"))
        if end_at <= start_at:
            raise ValueError(f"window {item.get('label')} end must be after start.")
        windows.append(
            MoneyFlowResearchCampaignWindow(
                label=_required_str(item, "label"),
                start_at=start_at,
                end_at=end_at,
                description=item.get("description"),
                expected_regime_label=item.get("expected_regime_label"),
            )
        )
    return windows


def _required_list(raw: dict[str, Any], key: str) -> list[Any]:
    if key not in raw:
        raise ValueError(f"campaign config missing required field: {key}")
    value = raw[key]
    if not isinstance(value, list):
        raise ValueError(f"campaign config field {key} must be a list.")
    return value


def _required_str(raw: dict[str, Any], key: str) -> str:
    if key not in raw:
        raise ValueError(f"campaign config missing required field: {key}")
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"campaign config field {key} must be a non-empty string.")
    return value.strip()


def _string_list(values: list[Any], field_name: str) -> list[str]:
    output: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings.")
        output.append(value.strip())
    return output


def _decimal_list(values: list[Any], field_name: str) -> list[Decimal]:
    try:
        return [Decimal(str(value)) for value in values]
    except Exception as exc:  # noqa: BLE001 - parsing should surface field context.
        raise ValueError(f"{field_name} entries must be decimal-compatible.") from exc


def _normalize_report_formats(values: Sequence[str] | str) -> tuple[str, ...]:
    if isinstance(values, str):
        values = (values,)
    normalized: list[str] = []
    for value in values:
        if value == "both":
            normalized.extend(["json", "markdown"])
            continue
        if value not in _REPORT_FORMATS:
            raise ValueError("report formats must be json, markdown, or both.")
        normalized.append(value)
    unique = tuple(sorted(set(normalized), key=("json", "markdown").index))
    if not unique:
        raise ValueError("at least one report format is required.")
    return unique


def _normalize_evidence_pack_collision_policy(value: str) -> str:
    normalized = value.strip()
    if normalized not in _EVIDENCE_PACK_COLLISION_POLICIES:
        accepted = ", ".join(sorted(_EVIDENCE_PACK_COLLISION_POLICIES))
        raise ValueError(f"evidence pack collision policy must be one of: {accepted}.")
    return normalized


def _reserve_evidence_pack_dir(
    *,
    root: Path,
    requested_run_id: str,
    collision_policy: str,
) -> tuple[Path, str, bool, str | None]:
    """Create a new evidence-pack directory without overwriting existing packs."""

    root.mkdir(parents=True, exist_ok=True)
    for attempt in range(0, _EVIDENCE_PACK_MAX_SUFFIX_ATTEMPTS + 1):
        suffix = None if attempt == 0 else f"{attempt:03d}"
        final_run_id = requested_run_id if suffix is None else f"{requested_run_id}-{suffix}"
        evidence_pack_dir = root / final_run_id
        try:
            evidence_pack_dir.mkdir(exist_ok=False)
        except FileExistsError as exc:
            if collision_policy == "fail_if_exists":
                raise FileExistsError(
                    "evidence pack directory already exists and collision policy "
                    f"`fail_if_exists` forbids overwrite: {evidence_pack_dir}"
                ) from exc
            continue
        return evidence_pack_dir, final_run_id, suffix is not None, suffix
    raise FileExistsError(
        "could not reserve a unique evidence pack directory after "
        f"{_EVIDENCE_PACK_MAX_SUFFIX_ATTEMPTS} suffix attempts under {root}"
    )


def _write_json(path: Path, payload: Any) -> None:
    _write_text_once(
        path,
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
    )


def _write_text_once(path: Path, text: str) -> None:
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite evidence-pack file: {path}") from exc


def _repo_metadata() -> dict[str, str | None]:
    return {
        "branch": _git_output("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git_output("rev-parse", "HEAD"),
    }


def _git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ("git", *args),
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug or "money-flow-research-campaign"


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


__all__ = [
    "MONEY_FLOW_RESEARCH_CAMPAIGN_DEFAULT_COLLISION_POLICY",
    "MoneyFlowResearchCampaignConfig",
    "MoneyFlowResearchCampaignDataReadinessAudit",
    "MoneyFlowResearchCampaignDataReadinessRow",
    "MoneyFlowResearchCampaignResult",
    "MoneyFlowResearchCampaignSymbol",
    "MoneyFlowResearchCampaignWindow",
    "audit_money_flow_research_campaign_data_readiness",
    "build_money_flow_research_campaign_batch_request",
    "load_money_flow_research_campaign_config",
    "money_flow_evidence_pack_review_checklist",
    "money_flow_manual_paper_trading_readiness_criteria",
    "money_flow_research_campaign_data_readiness_to_dict",
    "money_flow_research_campaign_data_readiness_to_markdown",
    "money_flow_research_campaign_config_from_dict",
    "money_flow_research_campaign_config_to_dict",
    "money_flow_research_campaign_report_to_markdown",
    "money_flow_research_campaign_run_contexts",
    "run_money_flow_research_campaign",
    "run_money_flow_research_campaign_sync",
    "write_money_flow_research_campaign_evidence_pack",
]
