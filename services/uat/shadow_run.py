"""UAT2 no-order Money Flow shadow run helpers.

This module runs bounded shadow evaluation over public read-only candle data.
It emits UAT shadow audit records only. It does not call private/signed/order
endpoints, use API keys, create production strategy decisions, create order
artifacts, approve paper/live trading, or change Money Flow rules.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from typing import Any

import httpx

from core.config.settings import AppSettings, MoneyFlowSleeveConfig, get_settings
from core.domain.enums import Timeframe
from core.domain.models import Candle
from core.security import redact_sensitive_text
from services.exchange.safety import ExchangeEndpointCategory, classify_hyperliquid_info_payload
from services.indicators.service import DefaultIndicatorService, _snapshot_complete
from services.strategy.money_flow import _decide_entry_reason, _money_flow_features
from services.uat.drawdown import UATDrawdownObservation, UATDrawdownPolicy
from services.uat.public_read_only import HYPERLIQUID_PUBLIC_INFO_URL, PublicHTTPResult
from services.uat.shadow import (
    UATShadowDrawdownState,
    UATShadowRiskSummary,
    UATShadowSignalAuditRecord,
    UATShadowSignalStatus,
    UATShadowTimingAssumption,
    UATShadowTimingStatus,
    build_shadow_drawdown_state_from_equity_path,
    create_shadow_signal_audit_record,
    load_uat1_universe_snapshot,
)


UAT2_EVIDENCE_CANDIDATE_ID = "money_flow_hyperliquid_eth_1h_baseline_uat_candidate"
UAT2_UNIVERSE_SCOPE = "top20_hyperliquid_observation_universe"
UAT2_PUBLIC_USER_AGENT = "money-flow-uat2-shadow-public-read-only/1.0"


@dataclass(frozen=True)
class UAT2ShadowMode:
    runtime_mode: str = "uat"
    uat2_shadow_run: bool = False
    shadow_only: bool = False
    public_read_only: bool = False
    allow_public_read_only_network: bool = False
    private_endpoints_allowed: bool = False
    signed_endpoints_allowed: bool = False
    order_endpoints_allowed: bool = False
    api_keys_used: bool = False
    order_submission_enabled: bool = False
    paper_trading_enabled: bool = False
    live_trading_enabled: bool = False

    @property
    def explicit_and_safe(self) -> bool:
        return (
            self.runtime_mode in {"uat", "test"}
            and self.uat2_shadow_run
            and self.shadow_only
            and self.public_read_only
            and self.allow_public_read_only_network
            and not self.private_endpoints_allowed
            and not self.signed_endpoints_allowed
            and not self.order_endpoints_allowed
            and not self.api_keys_used
            and not self.order_submission_enabled
            and not self.paper_trading_enabled
            and not self.live_trading_enabled
        )


@dataclass(frozen=True)
class UAT2CandleFetchResult:
    symbol: str
    component: str
    timeframe: str
    attempted: bool
    success: bool
    http_status: int | None
    candle_count: int
    sanitized_error: str | None = None
    endpoint_category: ExchangeEndpointCategory = ExchangeEndpointCategory.PUBLIC_READ_ONLY


@dataclass(frozen=True)
class UAT2SymbolComponentSummary:
    symbol: str
    component: str
    timeframe: str
    no_trade_count: int
    would_open_count: int
    would_hold_count: int
    would_reduce_count: int
    would_close_count: int
    invalid_count: int
    risk_blocked_count: int
    top_no_trade_reasons: tuple[tuple[str, int], ...]
    top_invalid_reasons: tuple[tuple[str, int], ...]
    top_risk_block_reasons: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class UAT2ShadowRunResult:
    run_id: str
    started_at_utc: datetime
    completed_at_utc: datetime
    mode: UAT2ShadowMode
    source_provider: str
    source_timestamp_utc: str | None
    symbols_requested: tuple[str, ...]
    symbols_evaluated: tuple[str, ...]
    components_evaluated: tuple[str, ...]
    public_data_lookback_candles: int
    evaluation_candle_policy: str
    candle_fetch_results: tuple[UAT2CandleFetchResult, ...]
    audit_records: tuple[UATShadowSignalAuditRecord, ...]
    summaries: tuple[UAT2SymbolComponentSummary, ...]
    shadow_drawdown_state: UATShadowDrawdownState
    uat3_readiness_decision: str
    remaining_blockers: tuple[str, ...]
    boundary_flags: dict[str, bool]


Transport = Callable[[str, str, dict[str, Any] | None], PublicHTTPResult]


def require_uat2_shadow_mode(mode: UAT2ShadowMode) -> None:
    if not mode.explicit_and_safe:
        raise ValueError(
            "UAT2 shadow run requires explicit --uat2-shadow-run, --shadow-only, "
            "--public-read-only, and --allow-public-read-only-network with private, signed, "
            "order, API-key, paper, and live paths disabled."
        )


def _default_transport(method: str, url: str, payload: dict[str, Any] | None) -> PublicHTTPResult:
    headers = {"User-Agent": UAT2_PUBLIC_USER_AGENT}
    try:
        with httpx.Client(timeout=20.0, headers=headers) as client:
            response = client.post(url, json=payload or {}) if method == "POST" else client.get(url)
            status_code = response.status_code
            response.raise_for_status()
            return PublicHTTPResult(
                url=url,
                method=method,
                status_code=status_code,
                payload=response.json(),
                response_headers={str(k): str(v) for k, v in response.headers.items()},
                success=True,
            )
    except Exception as exc:  # noqa: BLE001
        status_code = None
        response = getattr(exc, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)
        return PublicHTTPResult(
            url=url,
            method=method,
            status_code=status_code,
            payload=None,
            response_headers={},
            success=False,
            sanitized_error=redact_sensitive_text(str(exc)),
        )


def _duration_for_timeframe(timeframe: Timeframe) -> timedelta:
    if timeframe == Timeframe.M15:
        return timedelta(minutes=15)
    if timeframe == Timeframe.H1:
        return timedelta(hours=1)
    if timeframe == Timeframe.H4:
        return timedelta(hours=4)
    raise ValueError(f"Unsupported UAT2 Money Flow timeframe: {timeframe}")


def _hyperliquid_candle_payload(
    *,
    symbol: str,
    timeframe: Timeframe,
    lookback_candles: int,
    now: datetime,
) -> dict[str, Any]:
    duration = _duration_for_timeframe(timeframe)
    end_ms = int(now.timestamp() * 1000)
    start_ms = int((now - (duration * max(lookback_candles + 4, 40))).timestamp() * 1000)
    return {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": timeframe.value,
            "startTime": start_ms,
            "endTime": end_ms,
        },
    }


def _decimal_from_payload(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid candle numeric value: {value!r}") from exc


def _candle_from_payload_row(
    row: dict[str, Any],
    *,
    symbol: str,
    timeframe: Timeframe,
) -> Candle:
    open_ms = int(row.get("t"))
    close_ms = int(row.get("T") or (open_ms + int(_duration_for_timeframe(timeframe).total_seconds() * 1000)))
    trade_count = row.get("n")
    return Candle(
        instrument_key=f"hyperliquid:perp:USDC:{symbol}",
        instrument_ref_id=None,
        venue="hyperliquid",
        symbol=symbol,
        timeframe=timeframe,
        open_time=datetime.fromtimestamp(open_ms / 1000, tz=UTC),
        close_time=datetime.fromtimestamp(close_ms / 1000, tz=UTC),
        open=_decimal_from_payload(row.get("o")),
        high=_decimal_from_payload(row.get("h")),
        low=_decimal_from_payload(row.get("l")),
        close=_decimal_from_payload(row.get("c")),
        volume=_decimal_from_payload(row.get("v", "0")),
        trade_count=int(trade_count) if trade_count is not None else None,
    )


def fetch_public_candles(
    *,
    symbol: str,
    component: str,
    timeframe: Timeframe,
    mode: UAT2ShadowMode,
    lookback_candles: int,
    now: datetime,
    transport: Transport | None = None,
) -> tuple[UAT2CandleFetchResult, tuple[Candle, ...]]:
    require_uat2_shadow_mode(mode)
    payload = _hyperliquid_candle_payload(
        symbol=symbol,
        timeframe=timeframe,
        lookback_candles=lookback_candles,
        now=now,
    )
    category = classify_hyperliquid_info_payload(payload)
    if category != ExchangeEndpointCategory.PUBLIC_READ_ONLY:
        return (
            UAT2CandleFetchResult(
                symbol=symbol,
                component=component,
                timeframe=timeframe.value,
                attempted=False,
                success=False,
                http_status=None,
                candle_count=0,
                sanitized_error="uat2_blocked_non_public_read_only_candle_payload",
                endpoint_category=category,
            ),
            (),
        )
    result = (transport or _default_transport)("POST", HYPERLIQUID_PUBLIC_INFO_URL, payload)
    if not result.success:
        return (
            UAT2CandleFetchResult(
                symbol=symbol,
                component=component,
                timeframe=timeframe.value,
                attempted=True,
                success=False,
                http_status=result.status_code,
                candle_count=0,
                sanitized_error=result.sanitized_error or "public_read_only_fetch_failed",
                endpoint_category=category,
            ),
            (),
        )
    try:
        rows = result.payload if isinstance(result.payload, list) else []
        candles = tuple(
            sorted(
                (_candle_from_payload_row(row, symbol=symbol, timeframe=timeframe) for row in rows),
                key=lambda candle: candle.close_time,
            )
        )
    except Exception as exc:  # noqa: BLE001
        return (
            UAT2CandleFetchResult(
                symbol=symbol,
                component=component,
                timeframe=timeframe.value,
                attempted=True,
                success=False,
                http_status=result.status_code,
                candle_count=0,
                sanitized_error=redact_sensitive_text(str(exc)),
                endpoint_category=category,
            ),
            (),
        )
    return (
        UAT2CandleFetchResult(
            symbol=symbol,
            component=component,
            timeframe=timeframe.value,
            attempted=True,
            success=bool(candles),
            http_status=result.status_code,
            candle_count=len(candles),
            endpoint_category=category,
        ),
        candles,
    )


def _component_sleeves(settings: AppSettings, components: Iterable[str] | None = None) -> tuple[MoneyFlowSleeveConfig, ...]:
    wanted = tuple(components) if components is not None else ("sleeve_15m", "sleeve_1h", "sleeve_4h")
    by_id = {sleeve.sleeve_id: sleeve for sleeve in settings.money_flow.sleeves}
    return tuple(by_id[component] for component in wanted if component in by_id)


def _record_from_status(
    *,
    run_id: str,
    timestamp_utc: datetime,
    symbol: str,
    component: str,
    timeframe: Timeframe,
    candle_close_time: datetime,
    status: UATShadowSignalStatus,
    reason_codes: tuple[str, ...],
    indicator_summary: dict[str, Any],
    timing_status: dict[str, UATShadowTimingStatus],
    risk_status: str = "risk_visibility_deferred_no_live_artifacts",
) -> UATShadowSignalAuditRecord:
    candidate_id = UAT2_EVIDENCE_CANDIDATE_ID if symbol == "ETH" and component == "sleeve_1h" else None
    risk_summary = UATShadowRiskSummary(
        risk_status=risk_status,
        risk_reason_codes=(risk_status,),
        notional_limit_visible=False,
        drawdown_state_visible=True,
        order_submission_enabled=False,
    )
    return create_shadow_signal_audit_record(
        run_id=run_id,
        timestamp_utc=timestamp_utc,
        venue="hyperliquid",
        symbol=symbol,
        market_type="perpetual",
        product_type="perp",
        quote_asset="USDC",
        settlement_asset="USDC",
        component=component,
        timeframe=timeframe.value,
        candle_close_time_utc=candle_close_time,
        signal_status=status,
        reason_codes=reason_codes,
        indicator_summary=indicator_summary,
        risk_summary=risk_summary,
        candidate_id=candidate_id,
        top20_universe_member=True,
        timing_status_by_assumption=timing_status,
        operator_visible_explanation=_operator_explanation(status, reason_codes, symbol=symbol, component=component),
    )


def _operator_explanation(
    status: UATShadowSignalStatus,
    reason_codes: tuple[str, ...],
    *,
    symbol: str,
    component: str,
) -> str:
    joined = ", ".join(reason_codes) if reason_codes else "current Money Flow entry conditions were satisfied"
    if status == UATShadowSignalStatus.WOULD_OPEN:
        return (
            f"{symbol} {component} produced a shadow would-open under current baseline Money Flow rules. "
            "No order artifact was created; risk is visible as deferred because UAT2 avoids order-intent construction."
        )
    if status == UATShadowSignalStatus.INVALID:
        return f"{symbol} {component} could not be evaluated: {joined}."
    return f"{symbol} {component} produced no shadow trade: {joined}."


def evaluate_shadow_signal_for_candles(
    *,
    run_id: str,
    timestamp_utc: datetime,
    symbol: str,
    sleeve: MoneyFlowSleeveConfig,
    candles: Sequence[Candle],
    indicator_service: DefaultIndicatorService | None = None,
) -> UATShadowSignalAuditRecord:
    if len(candles) < sleeve.min_history_bars + 2:
        return _record_from_status(
            run_id=run_id,
            timestamp_utc=timestamp_utc,
            symbol=symbol,
            component=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            candle_close_time=candles[-1].close_time if candles else timestamp_utc,
            status=UATShadowSignalStatus.INVALID,
            reason_codes=("insufficient_public_candle_history",),
            indicator_summary={"candle_count": len(candles), "min_history_bars": sleeve.min_history_bars},
            timing_status={
                UATShadowTimingAssumption.NEXT_CANDLE_OPEN.value: UATShadowTimingStatus.BLOCKED,
                UATShadowTimingAssumption.NEXT_CANDLE_CLOSE.value: UATShadowTimingStatus.BLOCKED,
            },
            risk_status="risk_visibility_deferred_no_live_artifacts",
        )

    indicator_service = indicator_service or DefaultIndicatorService()
    snapshots = indicator_service._compute_snapshots(candles)  # noqa: SLF001 - UAT shadow uses in-memory indicators only.
    evaluation_index = len(candles) - 2
    candle = candles[evaluation_index]
    next_candle = candles[evaluation_index + 1]
    snapshot = snapshots[evaluation_index]
    if not _snapshot_complete(snapshot):
        return _record_from_status(
            run_id=run_id,
            timestamp_utc=timestamp_utc,
            symbol=symbol,
            component=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            candle_close_time=candle.close_time,
            status=UATShadowSignalStatus.INVALID,
            reason_codes=("incomplete_indicator_snapshot",),
            indicator_summary={"candle_count": len(candles), "indicator_as_of": snapshot.as_of.isoformat()},
            timing_status={
                UATShadowTimingAssumption.NEXT_CANDLE_OPEN.value: UATShadowTimingStatus.BLOCKED,
                UATShadowTimingAssumption.NEXT_CANDLE_CLOSE.value: UATShadowTimingStatus.BLOCKED,
            },
        )

    features = _money_flow_features(snapshot=snapshot, sleeve=sleeve, latest_close=float(candle.close))
    reason = _decide_entry_reason(features, sleeve=sleeve)
    status = UATShadowSignalStatus.NO_TRADE if reason else UATShadowSignalStatus.WOULD_OPEN
    reason_codes = (reason,) if reason else ("current_money_flow_entry_conditions_met",)
    indicator_summary = {
        "evaluation_candle_policy": "latest_candle_with_next_candle_available",
        "candle_count": len(candles),
        "indicator_as_of": snapshot.as_of.isoformat(),
        "rsi14": str(snapshot.rsi_14),
        "ema5": str(snapshot.ema_5),
        "ema10": str(snapshot.ema_10),
        "sma20": str(snapshot.sma_20),
        "macd": str(snapshot.macd),
        "macd_signal": str(snapshot.macd_signal),
        "macd_histogram": str(snapshot.macd_histogram),
        "latest_close": str(candle.close),
        "next_candle_open": str(next_candle.open),
        "next_candle_close": str(next_candle.close),
        "same_candle_close_research_only": "excluded_from_uat2_primary_assumption",
    }
    timing_status = {
        UATShadowTimingAssumption.NEXT_CANDLE_OPEN.value: UATShadowTimingStatus.AVAILABLE,
        UATShadowTimingAssumption.NEXT_CANDLE_CLOSE.value: UATShadowTimingStatus.AVAILABLE,
    }
    return _record_from_status(
        run_id=run_id,
        timestamp_utc=timestamp_utc,
        symbol=symbol,
        component=sleeve.sleeve_id,
        timeframe=sleeve.timeframe,
        candle_close_time=candle.close_time,
        status=status,
        reason_codes=reason_codes,
        indicator_summary=indicator_summary,
        timing_status=timing_status,
    )


def _summarize_records(records: Sequence[UATShadowSignalAuditRecord]) -> tuple[UAT2SymbolComponentSummary, ...]:
    grouped: dict[tuple[str, str, str], list[UATShadowSignalAuditRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.symbol, record.component, record.timeframe)].append(record)

    summaries: list[UAT2SymbolComponentSummary] = []
    for (symbol, component, timeframe), group in sorted(grouped.items()):
        status_counts = Counter(record.signal_status.value for record in group)
        no_trade_reasons = Counter(
            reason
            for record in group
            if record.signal_status == UATShadowSignalStatus.NO_TRADE
            for reason in record.reason_codes
        )
        invalid_reasons = Counter(
            reason
            for record in group
            if record.signal_status == UATShadowSignalStatus.INVALID
            for reason in record.reason_codes
        )
        risk_reasons = Counter(
            reason
            for record in group
            if record.signal_status == UATShadowSignalStatus.RISK_BLOCKED
            for reason in record.risk_summary.risk_reason_codes
        )
        summaries.append(
            UAT2SymbolComponentSummary(
                symbol=symbol,
                component=component,
                timeframe=timeframe,
                no_trade_count=status_counts[UATShadowSignalStatus.NO_TRADE.value],
                would_open_count=status_counts[UATShadowSignalStatus.WOULD_OPEN.value],
                would_hold_count=status_counts[UATShadowSignalStatus.WOULD_HOLD.value],
                would_reduce_count=status_counts[UATShadowSignalStatus.WOULD_REDUCE.value],
                would_close_count=status_counts[UATShadowSignalStatus.WOULD_CLOSE.value],
                invalid_count=status_counts[UATShadowSignalStatus.INVALID.value],
                risk_blocked_count=status_counts[UATShadowSignalStatus.RISK_BLOCKED.value],
                top_no_trade_reasons=tuple(no_trade_reasons.most_common(5)),
                top_invalid_reasons=tuple(invalid_reasons.most_common(5)),
                top_risk_block_reasons=tuple(risk_reasons.most_common(5)),
            )
        )
    return tuple(summaries)


def run_uat2_shadow_strategy(
    *,
    mode: UAT2ShadowMode,
    run_id: str | None = None,
    components: Iterable[str] | None = None,
    symbols: Iterable[str] | None = None,
    lookback_candles: int = 80,
    now: datetime | None = None,
    transport: Transport | None = None,
    settings: AppSettings | None = None,
) -> UAT2ShadowRunResult:
    require_uat2_shadow_mode(mode)
    settings = settings or get_settings()
    started_at = now or datetime.now(UTC)
    run_id = run_id or f"uat2-shadow-{started_at.strftime('%Y%m%dT%H%M%SZ')}"
    snapshot = load_uat1_universe_snapshot()
    if not snapshot.observation_only:
        raise ValueError("UAT1 universe snapshot must be observation-only for UAT2")
    requested_symbols = tuple(symbols) if symbols is not None else snapshot.included_assets
    universe_symbols = tuple(symbol for symbol in requested_symbols if symbol in snapshot.included_assets)
    sleeves = _component_sleeves(settings, components)
    records: list[UATShadowSignalAuditRecord] = []
    fetch_results: list[UAT2CandleFetchResult] = []

    for symbol in universe_symbols:
        for sleeve in sleeves:
            fetch_result, candles = fetch_public_candles(
                symbol=symbol,
                component=sleeve.sleeve_id,
                timeframe=sleeve.timeframe,
                mode=mode,
                lookback_candles=lookback_candles,
                now=started_at,
                transport=transport,
            )
            fetch_results.append(fetch_result)
            if not fetch_result.success:
                records.append(
                    _record_from_status(
                        run_id=run_id,
                        timestamp_utc=started_at,
                        symbol=symbol,
                        component=sleeve.sleeve_id,
                        timeframe=sleeve.timeframe,
                        candle_close_time=started_at,
                        status=UATShadowSignalStatus.INVALID,
                        reason_codes=("public_read_only_fetch_failed",),
                        indicator_summary={
                            "sanitized_error": fetch_result.sanitized_error,
                            "http_status": fetch_result.http_status,
                        },
                        timing_status={
                            UATShadowTimingAssumption.NEXT_CANDLE_OPEN.value: UATShadowTimingStatus.BLOCKED,
                            UATShadowTimingAssumption.NEXT_CANDLE_CLOSE.value: UATShadowTimingStatus.BLOCKED,
                        },
                    )
                )
                continue
            records.append(
                evaluate_shadow_signal_for_candles(
                    run_id=run_id,
                    timestamp_utc=started_at,
                    symbol=symbol,
                    sleeve=sleeve,
                    candles=candles,
                )
            )

    summaries = _summarize_records(records)
    equity_path = _shadow_equity_path_from_records(run_id=run_id, started_at=started_at, records=records)
    drawdown_state = build_shadow_drawdown_state_from_equity_path(
        run_id=run_id,
        candidate_id=UAT2_EVIDENCE_CANDIDATE_ID,
        universe_scope=UAT2_UNIVERSE_SCOPE,
        observations=equity_path,
        policy=UATDrawdownPolicy(threshold_pct=Decimal("0.10")),
    )
    remaining_blockers = (
        "founder_operator_explicit_approval_required_before_uat3_sandbox_order_design",
        "sandbox_account_drawdown_feed_wiring_required_before_uat3",
        "uat3_approval_submit_lease_lifecycle_verification_required",
    )
    completed_at = datetime.now(UTC)
    return UAT2ShadowRunResult(
        run_id=run_id,
        started_at_utc=started_at,
        completed_at_utc=completed_at,
        mode=mode,
        source_provider=snapshot.source_provider,
        source_timestamp_utc=snapshot.source_timestamp_utc,
        symbols_requested=tuple(requested_symbols),
        symbols_evaluated=universe_symbols,
        components_evaluated=tuple(sleeve.sleeve_id for sleeve in sleeves),
        public_data_lookback_candles=lookback_candles,
        evaluation_candle_policy="latest_candle_with_next_candle_available",
        candle_fetch_results=tuple(fetch_results),
        audit_records=tuple(records),
        summaries=summaries,
        shadow_drawdown_state=drawdown_state,
        uat3_readiness_decision="UAT3 is blocked",
        remaining_blockers=remaining_blockers,
        boundary_flags={
            "public_read_only_allowed": mode.public_read_only and mode.allow_public_read_only_network,
            "private_endpoints_called": False,
            "signed_endpoints_called": False,
            "order_endpoints_called": False,
            "api_keys_used": False,
            "orders_submitted": False,
            "strategy_decisions_created": False,
            "signal_events_created": False,
            "order_intents_created": False,
            "prepared_orders_created": False,
            "execution_readiness_assessments_created": False,
            "submitted_orders_created": False,
            "approvals_created": False,
            "routing_artifacts_created": False,
            "paper_trading_added": False,
            "live_trading_added": False,
            "money_flow_rules_changed": False,
            "evidence_packs_generated": False,
        },
    )


def _shadow_equity_path_from_records(
    *,
    run_id: str,
    started_at: datetime,
    records: Sequence[UATShadowSignalAuditRecord],
) -> tuple[UATDrawdownObservation, ...]:
    # UAT2 is signal-only, so there is no PnL simulation. Keep equity flat and
    # explicit so drawdown visibility exists without implying performance.
    del run_id
    observed = Decimal("10000")
    count = max(1, len(records))
    return tuple(
        UATDrawdownObservation(
            timestamp_utc=started_at + timedelta(seconds=index),
            observed_equity=observed,
            realized_pnl=Decimal("0"),
            unrealized_pnl=Decimal("0"),
        )
        for index in range(count)
    )


def _format_reason_counts(reason_counts: tuple[tuple[str, int], ...]) -> str:
    if not reason_counts:
        return ""
    return ", ".join(f"`{reason}`: `{count}`" for reason, count in reason_counts)


def render_uat2_report(result: UAT2ShadowRunResult) -> str:
    included_symbols = ", ".join(f"`{symbol}`" for symbol in result.symbols_evaluated) or "none"
    fetch_successes = sum(1 for item in result.candle_fetch_results if item.success)
    fetch_failures = sum(1 for item in result.candle_fetch_results if not item.success)
    signal_counts = Counter(record.signal_status.value for record in result.audit_records)
    would_trade = signal_counts[UATShadowSignalStatus.WOULD_OPEN.value]
    no_trade = signal_counts[UATShadowSignalStatus.NO_TRADE.value]
    invalid = signal_counts[UATShadowSignalStatus.INVALID.value]
    risk_blocked = signal_counts[UATShadowSignalStatus.RISK_BLOCKED.value]
    eth_1h = [
        record
        for record in result.audit_records
        if record.symbol == "ETH" and record.component == "sleeve_1h"
    ]
    eth_1h_status = eth_1h[0].signal_status.value if eth_1h else "not_evaluated"
    eth_1h_reasons = ", ".join(eth_1h[0].reason_codes) if eth_1h else "not_evaluated"
    lines = [
        "# UAT2 Shadow Strategy Top-20 Observation",
        "",
        f"Recorded at: `{datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}`",
        "",
        "## Scope",
        "",
        "UAT2 is a bounded no-order shadow strategy observation run over public read-only market data. It does not submit orders, does not use API keys, does not call private or signed endpoints, does not create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approval, routing, paper-trade, or live-trade artifacts, does not change Money Flow rules, and does not generate evidence packs.",
        "",
        "Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.",
        "",
        "## Runtime Mode",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Run id | `{result.run_id}` |",
        f"| Runtime mode | `{result.mode.runtime_mode}` |",
        f"| UAT2 shadow mode | `{str(result.mode.uat2_shadow_run).lower()}` |",
        f"| Shadow only | `{str(result.mode.shadow_only).lower()}` |",
        f"| Public read-only allowed | `{str(result.mode.public_read_only and result.mode.allow_public_read_only_network).lower()}` |",
        f"| Private endpoints allowed | `{str(result.mode.private_endpoints_allowed).lower()}` |",
        f"| Signed endpoints allowed | `{str(result.mode.signed_endpoints_allowed).lower()}` |",
        f"| Order endpoints allowed | `{str(result.mode.order_endpoints_allowed).lower()}` |",
        f"| API keys used | `{str(result.mode.api_keys_used).lower()}` |",
        f"| Order submission enabled | `{str(result.mode.order_submission_enabled).lower()}` |",
        f"| Paper trading enabled | `{str(result.mode.paper_trading_enabled).lower()}` |",
        f"| Live trading enabled | `{str(result.mode.live_trading_enabled).lower()}` |",
        "",
        "## Universe Snapshot Used",
        "",
        f"- Source provider: `{result.source_provider}`",
        f"- Source timestamp: `{result.source_timestamp_utc}`",
        f"- Included observation-only symbols evaluated: {included_symbols}",
        "- Top-20 inclusion remains observation-only and is not strategy approval, paper-trading approval, live-trading approval, or order-submission approval.",
        "",
        "## Bounded Run Definition",
        "",
        f"- Started at: `{result.started_at_utc.isoformat()}`",
        f"- Completed at: `{result.completed_at_utc.isoformat()}`",
        f"- Components evaluated: `{', '.join(result.components_evaluated)}`",
        f"- Public data lookback candles per symbol/component: `{result.public_data_lookback_candles}`",
        f"- Evaluation candle policy: `{result.evaluation_candle_policy}`",
        "- Continuous daemon: `false`",
        "",
        "## Public Read-Only Data Status",
        "",
        f"- Candle fetch successes: `{fetch_successes}`",
        f"- Candle fetch failures: `{fetch_failures}`",
        "- Endpoint category used: `public_read_only` / Hyperliquid `candleSnapshot`.",
        "",
        "## Signal Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Shadow audit records | `{len(result.audit_records)}` |",
        f"| `would_open` | `{would_trade}` |",
        f"| `no_trade` | `{no_trade}` |",
        f"| `invalid` | `{invalid}` |",
        f"| `risk_blocked` | `{risk_blocked}` |",
        "",
        "## Signal Summary By Symbol / Component",
        "",
        "| Symbol | Component | Timeframe | No trade | Would open | Would hold | Would reduce | Would close | Invalid | Risk blocked | Top no-trade reasons | Top invalid reasons | Top risk-block reasons |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for summary in result.summaries:
        lines.append(
            "| "
            f"`{summary.symbol}` | `{summary.component}` | `{summary.timeframe}` | "
            f"`{summary.no_trade_count}` | `{summary.would_open_count}` | "
            f"`{summary.would_hold_count}` | `{summary.would_reduce_count}` | `{summary.would_close_count}` | "
            f"`{summary.invalid_count}` | `{summary.risk_blocked_count}` | "
            f"{_format_reason_counts(summary.top_no_trade_reasons)} | "
            f"{_format_reason_counts(summary.top_invalid_reasons)} | "
            f"{_format_reason_counts(summary.top_risk_block_reasons)} |"
        )
    lines.extend(
        [
            "",
            "## Timing Assumptions",
            "",
            "- `next_candle_open` is represented in each shadow audit record.",
            "- `next_candle_close` is represented in each shadow audit record.",
            "- `same_candle_close_research_only` remains research-only and is excluded from UAT2 action assumptions.",
            "- Timing status is `available` when the bounded public candle window includes the next candle; otherwise it is `pending_next_candle`, `not_applicable`, or `blocked`.",
            "",
            "## Shadow Drawdown State",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Source | `{result.shadow_drawdown_state.source.value}` |",
            f"| Not live account drawdown | `{str(result.shadow_drawdown_state.not_live_account_drawdown).lower()}` |",
            f"| Shadow simulated drawdown | `{str(result.shadow_drawdown_state.shadow_simulated_drawdown).lower()}` |",
            f"| Initial shadow equity | `{result.shadow_drawdown_state.initial_shadow_equity}` |",
            f"| Current shadow equity | `{result.shadow_drawdown_state.current_shadow_equity}` |",
            f"| Max drawdown amount | `{result.shadow_drawdown_state.max_drawdown_amount}` |",
            f"| Max drawdown percent | `{result.shadow_drawdown_state.max_drawdown_percent}` |",
            f"| Threshold breached | `{str(result.shadow_drawdown_state.threshold_breached).lower()}` |",
            "",
            "UAT2 is signal-only and does not simulate PnL. Shadow equity is held flat for operator visibility; this is `shadow_drawdown_not_computed_for_no_order_signal_only_run` and `not_live_account_drawdown`, not live account equity and not performance validation.",
            "",
            "## Risk Visibility",
            "",
            "`risk_visibility_deferred_no_live_artifacts` appears on would-trade/no-trade records because UAT2 does not create order intents or execution-readiness artifacts. Drawdown state is visible, order submission remains disabled, and risk must be wired more deeply before any UAT3 sandbox-order phase.",
            "",
            "## Evidence Candidate Section",
            "",
            f"- Evidence candidate: `{UAT2_EVIDENCE_CANDIDATE_ID}`",
            "- Scope: Hyperliquid ETH USDC perpetual, `sleeve_1h`, current baseline Money Flow rules.",
            f"- UAT2 ETH `sleeve_1h` shadow status: `{eth_1h_status}`",
            f"- UAT2 ETH `sleeve_1h` reason codes: `{eth_1h_reasons}`",
            "- This remains the evidence candidate only. It is not proof of profitability and not paper/live/order approval.",
            "",
            "## Boundary Confirmation",
            "",
        ]
    )
    for flag, value in sorted(result.boundary_flags.items()):
        lines.append(f"- `{flag}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## UAT3 Readiness Decision",
            "",
            f"`{result.uat3_readiness_decision}`.",
            "",
            "Remaining blockers:",
            *(f"- `{blocker}`" for blocker in result.remaining_blockers),
            "",
            "UAT3 may not submit sandbox orders until a later explicit phase scopes approval-gated sandbox order design and the founder/operator explicitly accepts that scope.",
        ]
    )
    return "\n".join(lines)


def result_to_jsonable(result: UAT2ShadowRunResult) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if hasattr(value, "value"):
            return value.value
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        return value

    return convert(asdict(result))


def save_uat2_result_json(result: UAT2ShadowRunResult, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result_to_jsonable(result), handle, indent=2, sort_keys=True)
