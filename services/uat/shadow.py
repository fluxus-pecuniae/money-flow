"""UAT shadow-readiness models.

These helpers define operator-visible shadow audit and drawdown structures for
future UAT2. They do not run Money Flow, call exchanges, persist trading
artifacts, or authorize paper/live/order behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
import json
from pathlib import Path
from typing import Any

from core.security import redact_api_error_payload, redact_structured_log_event
from services.uat.drawdown import UATDrawdownObservation, UATDrawdownPolicy, UATDrawdownState


class UATShadowSignalStatus(StrEnum):
    NO_TRADE = "no_trade"
    WOULD_OPEN = "would_open"
    WOULD_HOLD = "would_hold"
    WOULD_REDUCE = "would_reduce"
    WOULD_CLOSE = "would_close"
    INVALID = "invalid"
    RISK_BLOCKED = "risk_blocked"


class UATShadowTimingAssumption(StrEnum):
    NEXT_CANDLE_OPEN = "next_candle_open"
    NEXT_CANDLE_CLOSE = "next_candle_close"
    SAME_CANDLE_CLOSE_RESEARCH_ONLY = "same_candle_close_research_only"


class UATShadowDrawdownSource(StrEnum):
    SHADOW_SIMULATED = "shadow_simulated"
    FIXTURE = "fixture"
    NOT_LIVE_ACCOUNT = "not_live_account"


class UATShadowDrawdownReason(StrEnum):
    WITHIN_LIMIT = "shadow_drawdown_within_limit"
    THRESHOLD_BREACHED = "shadow_drawdown_threshold_breached"
    EQUITY_UNAVAILABLE = "shadow_equity_unavailable"
    SOURCE_NOT_LIVE_ACCOUNT = "shadow_equity_source_not_live_account"
    MONITOR_NOT_LIVE_FED = "shadow_drawdown_monitor_not_live_fed"


LIVE_ARTIFACT_TYPE_NAMES: tuple[str, ...] = (
    "MandateDesiredTrade",
    "StrategyDecision",
    "SignalEvent",
    "OrderIntent",
    "PreparedVenueOrder",
    "ExecutionReadinessAssessment",
    "SubmittedOrder",
    "RoutingAssessment",
    "RoutingTargetChoice",
    "RoutingTargetRecommendation",
    "RoutingAutomationApproval",
    "PaperTrade",
    "LiveTrade",
)


@dataclass(frozen=True)
class UATShadowTimingPolicy:
    evaluated_assumptions: tuple[UATShadowTimingAssumption, ...] = (
        UATShadowTimingAssumption.NEXT_CANDLE_OPEN,
        UATShadowTimingAssumption.NEXT_CANDLE_CLOSE,
    )
    same_candle_close_research_only: bool = True
    same_candle_close_excluded_from_uat2_primary: bool = True


@dataclass(frozen=True)
class UATShadowRiskSummary:
    risk_status: str
    risk_reason_codes: tuple[str, ...] = ()
    notional_limit_visible: bool = False
    drawdown_state_visible: bool = False
    order_submission_enabled: bool = False


@dataclass(frozen=True)
class UATShadowSignalAuditRecord:
    run_id: str
    timestamp_utc: datetime
    venue: str
    symbol: str
    market_type: str
    product_type: str
    quote_asset: str
    settlement_asset: str
    component: str
    timeframe: str
    candle_close_time_utc: datetime
    signal_status: UATShadowSignalStatus
    reason_codes: tuple[str, ...]
    indicator_summary: dict[str, Any]
    risk_summary: UATShadowRiskSummary
    candidate_id: str | None
    top20_universe_member: bool
    timing_assumptions_evaluated: tuple[UATShadowTimingAssumption, ...]
    same_candle_close_research_only: bool
    operator_visible_explanation: str
    creates_strategy_decision: bool = False
    creates_order_intent: bool = False
    creates_submitted_order: bool = False
    creates_live_artifact_type_names: tuple[str, ...] = ()

    @property
    def no_live_artifacts_created(self) -> bool:
        return (
            not self.creates_strategy_decision
            and not self.creates_order_intent
            and not self.creates_submitted_order
            and not self.creates_live_artifact_type_names
        )


@dataclass(frozen=True)
class UATShadowDrawdownState:
    run_id: str
    candidate_id: str
    universe_scope: str
    timestamp_utc: datetime
    initial_shadow_equity: Decimal
    current_shadow_equity: Decimal
    max_shadow_equity: Decimal
    min_shadow_equity: Decimal
    max_drawdown_amount: Decimal
    max_drawdown_percent: Decimal
    drawdown_threshold: Decimal
    threshold_breached: bool
    reason_codes: tuple[UATShadowDrawdownReason, ...]
    source: UATShadowDrawdownSource
    not_live_account_drawdown: bool = True
    shadow_simulated_drawdown: bool = True


@dataclass(frozen=True)
class UAT1UniverseSnapshot:
    source_provider: str
    source_timestamp_utc: str | None
    included_assets: tuple[str, ...]
    excluded_assets: tuple[str, ...]
    exclusion_reasons_by_symbol: dict[str, tuple[str, ...]]
    observation_only: bool


@dataclass(frozen=True)
class UAT11ReadinessResult:
    shadow_signal_audit_surface_status: str
    shadow_drawdown_state_status: str
    redaction_verification_status: str
    universe_snapshot_status: str
    uat2_readiness_decision: str
    remaining_blockers: tuple[str, ...]


def create_shadow_signal_audit_record(
    *,
    run_id: str,
    timestamp_utc: datetime,
    venue: str,
    symbol: str,
    market_type: str,
    product_type: str,
    quote_asset: str,
    settlement_asset: str,
    component: str,
    timeframe: str,
    candle_close_time_utc: datetime,
    signal_status: UATShadowSignalStatus,
    reason_codes: tuple[str, ...],
    operator_visible_explanation: str,
    indicator_summary: dict[str, Any] | None = None,
    risk_summary: UATShadowRiskSummary | None = None,
    candidate_id: str | None = None,
    top20_universe_member: bool = True,
    timing_policy: UATShadowTimingPolicy | None = None,
) -> UATShadowSignalAuditRecord:
    policy = timing_policy or UATShadowTimingPolicy()
    return UATShadowSignalAuditRecord(
        run_id=run_id,
        timestamp_utc=timestamp_utc,
        venue=venue,
        symbol=symbol,
        market_type=market_type,
        product_type=product_type,
        quote_asset=quote_asset,
        settlement_asset=settlement_asset,
        component=component,
        timeframe=timeframe,
        candle_close_time_utc=candle_close_time_utc,
        signal_status=signal_status,
        reason_codes=tuple(reason_codes),
        indicator_summary=indicator_summary or {},
        risk_summary=risk_summary
        or UATShadowRiskSummary(
            risk_status="not_evaluated_in_uat1_1",
            risk_reason_codes=("uat1_1_does_not_run_shadow_strategy",),
            drawdown_state_visible=True,
        ),
        candidate_id=candidate_id,
        top20_universe_member=top20_universe_member,
        timing_assumptions_evaluated=policy.evaluated_assumptions,
        same_candle_close_research_only=policy.same_candle_close_research_only,
        operator_visible_explanation=operator_visible_explanation,
    )


def build_shadow_drawdown_state(
    *,
    run_id: str,
    candidate_id: str,
    universe_scope: str,
    states: tuple[UATDrawdownState, ...],
    source: UATShadowDrawdownSource = UATShadowDrawdownSource.SHADOW_SIMULATED,
) -> UATShadowDrawdownState:
    if not states:
        raise ValueError("states must not be empty")
    latest = states[-1]
    min_equity = min(state.current_observed_equity for state in states)
    reasons: list[UATShadowDrawdownReason] = [
        UATShadowDrawdownReason.SOURCE_NOT_LIVE_ACCOUNT,
        UATShadowDrawdownReason.MONITOR_NOT_LIVE_FED,
    ]
    if latest.threshold_breached:
        reasons.append(UATShadowDrawdownReason.THRESHOLD_BREACHED)
    else:
        reasons.append(UATShadowDrawdownReason.WITHIN_LIMIT)
    return UATShadowDrawdownState(
        run_id=run_id,
        candidate_id=candidate_id,
        universe_scope=universe_scope,
        timestamp_utc=latest.timestamp_utc,
        initial_shadow_equity=latest.initial_observed_equity,
        current_shadow_equity=latest.current_observed_equity,
        max_shadow_equity=latest.max_observed_equity,
        min_shadow_equity=min_equity,
        max_drawdown_amount=latest.max_drawdown_amount,
        max_drawdown_percent=latest.max_drawdown_pct,
        drawdown_threshold=latest.drawdown_threshold_pct,
        threshold_breached=latest.threshold_breached,
        reason_codes=tuple(reasons),
        source=source,
    )


def build_shadow_drawdown_state_from_equity_path(
    *,
    run_id: str,
    candidate_id: str,
    universe_scope: str,
    observations: tuple[UATDrawdownObservation, ...],
    policy: UATDrawdownPolicy | None = None,
) -> UATShadowDrawdownState:
    if not observations:
        raise ValueError("observations must not be empty")
    from services.uat.drawdown import UATDrawdownMonitor

    monitor = UATDrawdownMonitor(
        candidate_id=candidate_id,
        universe_asset_id=universe_scope,
        initial_observed_equity=observations[0].observed_equity,
        policy=policy,
        shadow_or_simulated=True,
    )
    states = tuple(monitor.observe(observation) for observation in observations)
    return build_shadow_drawdown_state(
        run_id=run_id,
        candidate_id=candidate_id,
        universe_scope=universe_scope,
        states=states,
    )


def load_uat1_universe_snapshot(
    path: str | Path = "docs/uat1_public_read_only_connectivity_and_top20_universe_summary.json",
) -> UAT1UniverseSnapshot:
    payload = json.loads(Path(path).read_text())
    included = tuple(item["global_symbol"] for item in payload.get("included_candidates", ()))
    excluded_rows = payload.get("excluded_candidates", ())
    excluded = tuple(item["global_symbol"] for item in excluded_rows)
    reasons = {
        item["global_symbol"]: tuple(item.get("exclusion_reason_codes", ()))
        for item in excluded_rows
    }
    source = payload.get("top20_source_result", {})
    if not isinstance(source, dict):
        source = {}
    return UAT1UniverseSnapshot(
        source_provider=str(source.get("provider") or "unknown"),
        source_timestamp_utc=source.get("source_timestamp_utc"),
        included_assets=included,
        excluded_assets=excluded,
        exclusion_reasons_by_symbol=reasons,
        observation_only=all(
            bool(item.get("observation_only"))
            and not bool(item.get("strategy_approved"))
            and not bool(item.get("paper_trading_approved"))
            and not bool(item.get("live_trading_approved"))
            for item in payload.get("included_candidates", ())
        ),
    )


def verify_shadow_redaction_payloads() -> dict[str, Any]:
    """Return redacted representative API-error and structured-log payloads."""

    api_error = {
        "detail": {
            "message": "adapter failed Authorization: Bearer api-token-123",
            "config": "postgresql+psycopg://user:db-pass-123@host:5432/db",
            "exchange": {"api_key": "key-123", "secret": "secret-123"},
        }
    }
    structured_log = {
        "event": "uat_shadow_error",
        "authorization": "Bearer log-token-123",
        "exception": "secret=log-secret-123 password=log-pass-123",
        "runtime_policy": {"live_trading_enabled": False, "token": "runtime-token-123"},
    }
    return {
        "api_error": redact_api_error_payload(api_error),
        "structured_log": redact_structured_log_event(structured_log),
    }


def evaluate_uat11_readiness(*, universe_snapshot: UAT1UniverseSnapshot) -> UAT11ReadinessResult:
    remaining_blockers: list[str] = []
    if not universe_snapshot.included_assets:
        remaining_blockers.append("uat1_universe_snapshot_missing_included_assets")
    if not universe_snapshot.observation_only:
        remaining_blockers.append("uat1_universe_snapshot_not_observation_only")
    if remaining_blockers:
        decision = "UAT2 is blocked"
    else:
        decision = "UAT2 shadow strategy run may proceed"
    return UAT11ReadinessResult(
        shadow_signal_audit_surface_status="implemented",
        shadow_drawdown_state_status="implemented",
        redaction_verification_status="implemented_representative_api_error_and_structured_log_payloads",
        universe_snapshot_status="available" if not remaining_blockers else "blocked",
        uat2_readiness_decision=decision,
        remaining_blockers=tuple(remaining_blockers),
    )


def render_uat11_report(
    *,
    audit_record: UATShadowSignalAuditRecord,
    drawdown_state: UATShadowDrawdownState,
    universe_snapshot: UAT1UniverseSnapshot,
    readiness: UAT11ReadinessResult,
) -> str:
    included = ", ".join(f"`{symbol}`" for symbol in universe_snapshot.included_assets) or "none"
    excluded = ", ".join(f"`{symbol}`" for symbol in universe_snapshot.excluded_assets) or "none"
    reason_codes = ", ".join(f"`{code.value}`" for code in drawdown_state.reason_codes)
    return "\n".join(
        [
            "# UAT1.1 Shadow Signal Audit And Drawdown Readiness",
            "",
            f"Recorded at: `{datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}`",
            "",
            "## Scope",
            "",
            "UAT1.1 prepares shadow audit and drawdown visibility. It does not run the UAT2 shadow strategy loop, does not run Money Flow over live data, does not submit orders, does not call private or signed endpoints, does not use exchange API keys, does not create strategy decisions, order intents, submitted orders, approvals, paper trades, live trades, routing artifacts, evidence packs, or Money Flow rule changes.",
            "",
            "Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.",
            "",
            "## Shadow Signal Audit Surface",
            "",
            "Status: `implemented`.",
            "",
            "The UAT shadow signal audit surface is model/report-only and is separate from production trading artifacts.",
            "",
            "| Field | Example / status |",
            "| --- | --- |",
            f"| Run id | `{audit_record.run_id}` |",
            f"| Venue / symbol | `{audit_record.venue}` / `{audit_record.symbol}` |",
            f"| Component / timeframe | `{audit_record.component}` / `{audit_record.timeframe}` |",
            f"| Signal status | `{audit_record.signal_status.value}` |",
            f"| Reason codes | `{', '.join(audit_record.reason_codes)}` |",
            f"| Timing assumptions | `{', '.join(item.value for item in audit_record.timing_assumptions_evaluated)}` |",
            f"| Same-candle close status | `same_candle_close_research_only={str(audit_record.same_candle_close_research_only).lower()}` |",
            f"| Operator explanation | {audit_record.operator_visible_explanation} |",
            "",
            "Required future UAT2 signal statuses are `no_trade`, `would_open`, `would_hold`, `would_reduce`, `would_close`, `invalid`, and `risk_blocked`.",
            "",
            "## No-Live-Artifact Boundary",
            "",
            f"Shadow audit no-live-artifact check: `{str(audit_record.no_live_artifacts_created).lower()}`.",
            "",
            "The shadow audit surface does not create: `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, or live trades.",
            "",
            "## Timing Assumptions",
            "",
            "- `next_candle_open` is represented for future UAT2 shadow comparison.",
            "- `next_candle_close` is represented for future UAT2 shadow comparison.",
            "- `same_candle_close_research_only` remains research-only and is excluded from primary UAT2 shadow assumptions.",
            "",
            "## Operator-Visible Shadow Drawdown State",
            "",
            "Status: `implemented`.",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Run id | `{drawdown_state.run_id}` |",
            f"| Candidate id | `{drawdown_state.candidate_id}` |",
            f"| Universe scope | `{drawdown_state.universe_scope}` |",
            f"| Initial shadow equity | `{drawdown_state.initial_shadow_equity}` |",
            f"| Current shadow equity | `{drawdown_state.current_shadow_equity}` |",
            f"| Max shadow equity | `{drawdown_state.max_shadow_equity}` |",
            f"| Min shadow equity | `{drawdown_state.min_shadow_equity}` |",
            f"| Max drawdown amount | `{drawdown_state.max_drawdown_amount}` |",
            f"| Max drawdown percent | `{drawdown_state.max_drawdown_percent}` |",
            f"| Drawdown threshold | `{drawdown_state.drawdown_threshold}` |",
            f"| Threshold breached | `{str(drawdown_state.threshold_breached).lower()}` |",
            f"| Source | `{drawdown_state.source.value}` |",
            f"| Not live account drawdown | `{str(drawdown_state.not_live_account_drawdown).lower()}` |",
            f"| Shadow simulated drawdown | `{str(drawdown_state.shadow_simulated_drawdown).lower()}` |",
            f"| Reason codes | {reason_codes} |",
            "",
            "This is `shadow_simulated_drawdown` and `not_live_account_drawdown`. It is operational risk visibility, not performance validation.",
            "",
            "## Drawdown Threshold Reason Codes",
            "",
            "- `shadow_drawdown_within_limit`",
            "- `shadow_drawdown_threshold_breached`",
            "- `shadow_equity_unavailable`",
            "- `shadow_equity_source_not_live_account`",
            "- `shadow_drawdown_monitor_not_live_fed`",
            "",
            "## Structured Log / API Error Redaction Status",
            "",
            "Status: `implemented_representative_api_error_and_structured_log_payloads`.",
            "",
            "UAT1.1 verifies representative API-error and structured-log payloads through `core.security.redact_api_error_payload` and `core.security.redact_structured_log_event`. Structlog events also pass through `core.logging.setup.redact_structlog_event` before rendering. Covered examples include bearer tokens, authorization headers, API keys, secrets, passwords, runtime-policy tokens, exception text, and database URLs.",
            "",
            "Remaining redaction follow-up before UAT3: deployment-specific middleware and logging processors should still be smoke-tested in a sandbox-like runtime.",
            "",
            "## UAT1 Universe Snapshot For UAT2",
            "",
            "Status: `available`.",
            "",
            f"- Source provider: `{universe_snapshot.source_provider}`",
            f"- Source timestamp: `{universe_snapshot.source_timestamp_utc}`",
            f"- Included observation-only assets: {included}",
            f"- Excluded assets: {excluded}",
            f"- Observation-only flags preserved: `{str(universe_snapshot.observation_only).lower()}`",
            "",
            "The UAT1 snapshot is not permanent strategy approval, paper-trading approval, live-trading approval, or order-submission approval.",
            "",
            "## UAT2 Readiness Decision",
            "",
            f"`{readiness.uat2_readiness_decision}`.",
            "",
            "UAT2, if accepted as next work, remains no-order shadow mode. It must compare `next_candle_open` and `next_candle_close`; it must not submit orders.",
            "",
            "Remaining blockers:",
            *(f"- `{blocker}`" for blocker in readiness.remaining_blockers),
            "" if readiness.remaining_blockers else "- none for UAT2 shadow-only start; UAT3 sandbox-order blockers remain deferred.",
            "",
            "## Boundary Confirmation",
            "",
            "UAT1.1 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, exchange calls, private/signed calls, order endpoint calls, evidence packs, strategy variants, or Money Flow rule changes.",
        ]
    )
