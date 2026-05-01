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

from core.domain.enums import Environment, StrategyFamily, StrategyValidationFillTiming
from core.domain.models import (
    StrategyValidationAssumptions,
    StrategyValidationBatchReport,
    StrategyValidationBatchRequest,
    StrategyValidationRequest,
)
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    STRATEGY_VALIDATION_WINDOW_CONVENTION,
    strategy_validation_batch_report_to_dict,
    strategy_validation_batch_report_to_markdown,
)

_WINDOW_CONVENTION_DISPLAY = "(start_at, end_at]"
_REPORT_FORMATS = {"json", "markdown"}


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


def load_money_flow_research_campaign_config(path: str | Path) -> MoneyFlowResearchCampaignConfig:
    """Load a Money Flow research campaign config from JSON."""

    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return money_flow_research_campaign_config_from_dict(raw)


def money_flow_research_campaign_config_from_dict(
    raw: dict[str, Any],
) -> MoneyFlowResearchCampaignConfig:
    """Parse and validate a campaign config dictionary."""

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
) -> MoneyFlowResearchCampaignResult:
    """Synchronous convenience wrapper for CLI callers."""

    return asyncio.run(
        run_money_flow_research_campaign(
            config,
            service=service,
            output_dir=output_dir,
            report_formats=report_formats,
            run_timestamp=run_timestamp,
        )
    )


def write_money_flow_research_campaign_evidence_pack(
    config: MoneyFlowResearchCampaignConfig,
    batch_report: StrategyValidationBatchReport,
    *,
    output_dir: str | Path | None = None,
    report_formats: Sequence[str] | None = None,
    run_timestamp: datetime | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Write a campaign evidence pack directory and return its manifest."""

    formats = tuple(_normalize_report_formats(report_formats or config.report_formats))
    timestamp = _coerce_utc(run_timestamp or datetime.now(UTC)).replace(microsecond=0)
    evidence_pack_dir = (
        Path(output_dir or config.output_dir)
        / _safe_slug(config.campaign_name)
        / timestamp.strftime("%Y%m%dT%H%M%SZ")
    )
    evidence_pack_dir.mkdir(parents=True, exist_ok=True)

    config_payload = money_flow_research_campaign_config_to_dict(config)
    batch_payload = strategy_validation_batch_report_to_dict(batch_report)
    run_contexts = money_flow_research_campaign_run_contexts(config, batch_report)
    manifest = _campaign_manifest(
        config=config,
        batch_report=batch_report,
        run_timestamp=timestamp,
        run_contexts=run_contexts,
        formats=formats,
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
        (evidence_pack_dir / "batch_report.md").write_text(markdown, encoding="utf-8")

    _write_json(evidence_pack_dir / "manifest.json", manifest)
    (evidence_pack_dir / "README.md").write_text(
        _evidence_pack_readme(config, manifest),
        encoding="utf-8",
    )
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
) -> dict[str, Any]:
    blocked = [run for run in batch_report.run_reports if run.status != "completed"]
    blocked_reason_counts: Counter[str] = Counter()
    for run in blocked:
        blocked_reason_counts.update(run.reason_codes or ["strategy_validation_run_blocked"])
    config_payload = money_flow_research_campaign_config_to_dict(config)
    return {
        "campaign_name": config.campaign_name,
        "description": config.description,
        "run_timestamp_utc": _coerce_utc(run_timestamp).isoformat(),
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
            "This directory is an SV1.3 research evidence pack.",
            "",
            "- `campaign_config.json` is the normalized campaign input.",
            "- `manifest.json` records run metadata, assumptions hash, window convention, blocked-run counts, and report paths.",
            "- `batch_report.json` and `batch_report.md` contain the batch validation output when those formats are requested.",
            "- The window convention is `(start_at, end_at]`: candle closes exactly at `start_at` are excluded and closes on or before `end_at` are included.",
            "- Outputs are research-only. They are not paper trading, live execution, routing, optimization, or proof of future profitability.",
            "",
            f"Run timestamp UTC: `{manifest['run_timestamp_utc']}`",
        ]
    ) + "\n"


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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    "MoneyFlowResearchCampaignConfig",
    "MoneyFlowResearchCampaignResult",
    "MoneyFlowResearchCampaignSymbol",
    "MoneyFlowResearchCampaignWindow",
    "build_money_flow_research_campaign_batch_request",
    "load_money_flow_research_campaign_config",
    "money_flow_research_campaign_config_from_dict",
    "money_flow_research_campaign_config_to_dict",
    "money_flow_research_campaign_report_to_markdown",
    "money_flow_research_campaign_run_contexts",
    "run_money_flow_research_campaign",
    "run_money_flow_research_campaign_sync",
    "write_money_flow_research_campaign_evidence_pack",
]
