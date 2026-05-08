"""Research-only Money Flow replay instrumentation for Strategy Validation.

SV1.16 records per-candle production-rule decision context and provides a narrow true
replay substrate for future hypothesis testing. It creates only in-memory
research artifacts; it does not persist strategy decisions, signals, orders, or
other live execution records.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from core.config.settings import AppSettings, MoneyFlowSleeveConfig, get_settings
from core.domain.enums import (
    DecisionAction,
    StrategyDecisionStatus,
    StrategyFamily,
    StrategyValidationCapitalSizingMode,
    Timeframe,
)
from core.domain.models import (
    Candle,
    StrategyValidationDataCoverage,
    StrategyValidationMetrics,
    StrategyValidationRequest,
    StrategyValidationTrade,
)
from db.session import SessionLocal
from services.strategy_validation.service import (
    MoneyFlowBacktestService,
    StrategyValidationError,
    _CandleRegime,
    _ResolvedFill,
    _build_metrics,
    _coerce_utc,
    _data_coverage,
    _dynamic_equity_is_depleted,
    _json_ready,
    _last_candle_in_window,
    _label_candle_regimes,
    _money,
    _open_trade,
    _position_from_open_position,
    _resolve_fill,
    _stable_hash,
    _close_trade,
)

REPLAY_CONTEXT_METHODOLOGY = "per_candle_true_replay_context_research_only"
LOWER_RSI_TREND_INTACT_VARIANT_ID = "lower_rsi_floor_trend_intact_v1"
BASELINE_REPLAY_VARIANT_ID = "baseline_current_money_flow_rules"
REPLAY_MARKET_STRUCTURE_LOOKBACK_CANDLES = 20


@dataclass(frozen=True, slots=True)
class MoneyFlowReplayVariant:
    variant_id: str
    name: str
    description: str
    methodology: str
    status: str = "experimental_research_only"
    lower_rsi_floor_by_component: dict[str, Decimal] = field(default_factory=dict)
    requires_trend_intact: bool = True
    requires_macd_constructive: bool = True
    requires_pullback_or_support: bool = True
    changes_production_rules: bool = False


@dataclass(frozen=True, slots=True)
class MoneyFlowReplayMarketStructure:
    lookback_candles: int
    recent_swing_high: Decimal | None
    recent_swing_low: Decimal | None
    distance_to_recent_swing_high_pct: Decimal | None
    distance_to_recent_swing_low_pct: Decimal | None
    near_support: bool
    near_resistance: bool
    breakout_context: bool


@dataclass(frozen=True, slots=True)
class MoneyFlowReplayCandleContext:
    symbol: str
    component_key: str
    timeframe: Timeframe
    candle_open_time: datetime
    candle_close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    ema5: Decimal | None
    ema10: Decimal | None
    sma20: Decimal | None
    rsi14: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    production_rule_action_in_replay_state: str
    production_rule_status_in_replay_state: str
    production_rule_reason_codes_in_replay_state: tuple[str, ...]
    production_rule_entry_allowed_in_replay_state: bool
    production_rule_entry_rejected_in_replay_state: bool
    baseline_action: str
    baseline_status: str
    baseline_reason_codes: tuple[str, ...]
    baseline_entry_allowed: bool
    baseline_entry_rejected: bool
    entry_rejection_reason: str | None
    rsi_value: Decimal | None
    rsi_sleeve_floor: Decimal
    rsi_sleeve_ceiling: Decimal
    rsi_zone: str
    ema_trend_stack_state: str
    macd_constructive: bool
    price_extension_from_ema5: Decimal | None
    market_regime_label: str
    volatility_regime_label: str
    market_structure: MoneyFlowReplayMarketStructure
    variant_state_has_diverged_from_baseline: bool = False
    variant_position_active: bool = False
    baseline_reference_position_active: bool | None = None
    replay_state_source: str = "production_baseline_state"
    variant_candidate: bool = False
    variant_candidate_reason_codes: tuple[str, ...] = ()
    variant_entry_allowed: bool = False
    variant_entry_reason: str | None = None
    variant_admitted_from_production_rule_rejection: bool = False


@dataclass(frozen=True, slots=True)
class MoneyFlowTrueReplayResult:
    replay_id: str
    variant: MoneyFlowReplayVariant
    request: StrategyValidationRequest
    component_key: str
    timeframe: Timeframe
    data_coverage: StrategyValidationDataCoverage
    contexts: list[MoneyFlowReplayCandleContext]
    trades: list[StrategyValidationTrade]
    metrics: StrategyValidationMetrics
    rejected_signal_summary: dict[str, Any]
    variant_summary: dict[str, Any]
    limitations: list[str]
    boundary_flags: dict[str, bool]


def lower_rsi_floor_trend_intact_variant(
    *,
    floor_delta: Decimal = Decimal("5"),
) -> MoneyFlowReplayVariant:
    return MoneyFlowReplayVariant(
        variant_id=LOWER_RSI_TREND_INTACT_VARIANT_ID,
        name="Lower RSI floor trend-intact replay v1",
        description=(
            "Research-only true replay that admits below-baseline-floor RSI entries only when "
            "EMA trend remains intact, MACD is constructive, price is not extended, and price is "
            "near EMA10 or recent swing support."
        ),
        methodology="true_forward_replay",
        lower_rsi_floor_by_component={
            "sleeve_15m": Decimal("52") - floor_delta,
            "sleeve_1h": Decimal("50") - floor_delta,
            "sleeve_4h": Decimal("48") - floor_delta,
        },
    )


def baseline_replay_variant() -> MoneyFlowReplayVariant:
    return MoneyFlowReplayVariant(
        variant_id=BASELINE_REPLAY_VARIANT_ID,
        name="Baseline current Money Flow replay",
        description="Current Money Flow rules replayed candle by candle for methodology comparison.",
        methodology="true_forward_replay",
        status="baseline_research_only",
    )


class MoneyFlowVariantReplayService:
    """Runs Strategy Validation true replays without touching production rules."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        backtest_service: MoneyFlowBacktestService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._backtest_service = backtest_service or MoneyFlowBacktestService(
            self.settings,
            session_factory=session_factory,
        )

    async def run_money_flow_true_replay(
        self,
        request: StrategyValidationRequest,
        *,
        variant: MoneyFlowReplayVariant | None = None,
    ) -> list[MoneyFlowTrueReplayResult]:
        if request.strategy_family != StrategyFamily.MONEY_FLOW:
            raise StrategyValidationError("SV1.16 replay only supports Money Flow.")
        variant = variant or baseline_replay_variant()
        start_at = _coerce_utc(request.start_at)
        end_at = _coerce_utc(request.end_at)
        if end_at <= start_at:
            raise StrategyValidationError("end_at must be after start_at.")
        results: list[MoneyFlowTrueReplayResult] = []
        for sleeve in self._backtest_service._requested_sleeves(request.component_keys):
            results.append(
                await self._run_component_replay(
                    request=request,
                    sleeve=sleeve,
                    variant=variant,
                    start_at=start_at,
                    end_at=end_at,
                )
            )
        return results

    async def _run_component_replay(
        self,
        *,
        request: StrategyValidationRequest,
        sleeve: MoneyFlowSleeveConfig,
        variant: MoneyFlowReplayVariant,
        start_at: datetime,
        end_at: datetime,
    ) -> MoneyFlowTrueReplayResult:
        candles = self._backtest_service._load_candles(
            request=request,
            timeframe=sleeve.timeframe,
            end_at=end_at,
        )
        snapshots = self._backtest_service._indicator_service._compute_snapshots(candles)
        data_coverage = _data_coverage(candles, timeframe=sleeve.timeframe, start_at=start_at, end_at=end_at)
        regime_by_close_time = _label_candle_regimes(candles)
        contexts: list[MoneyFlowReplayCandleContext] = []
        trades: list[StrategyValidationTrade] = []
        no_trade_reasons: Counter[str] = Counter()
        invalid_reasons: Counter[str] = Counter()
        variant_candidate_reasons: Counter[str] = Counter()
        variant_rejected_reasons: Counter[str] = Counter()
        production_rule_rejection_reasons: Counter[str] = Counter()
        variant_admitted_from_rejection_reasons: Counter[str] = Counter()
        variant_no_trade_reasons: Counter[str] = Counter()
        limitations: list[str] = list(data_coverage.warning_reason_codes)
        if not candles:
            limitations.append("no_persisted_candles_for_component")

        open_position: Any | None = None
        variant_state_has_diverged_from_baseline = False
        realized_equity = request.assumptions.initial_capital
        closed_trade_equity_points: list[Decimal] = [request.assumptions.initial_capital]
        mark_to_market_equity_points: list[Decimal] = [request.assumptions.initial_capital]
        trades_skipped_due_to_insufficient_equity = 0

        for signal_index, (candle, snapshot) in enumerate(zip(candles, snapshots, strict=False)):
            history_index = signal_index + 1
            candle_close_time = _coerce_utc(candle.close_time)
            if candle_close_time <= start_at or candle_close_time > end_at:
                continue
            regime = regime_by_close_time.get(
                candle_close_time,
                _CandleRegime.unknown(candle_close_time),
            )
            position_active_for_evaluation = (
                open_position is not None and candle_close_time > open_position.entry_time
            )
            current_position = (
                _position_from_open_position(open_position, request=request, candle=candle)
                if position_active_for_evaluation
                else None
            )
            evaluation_input = self._backtest_service._evaluation_input(
                request=request,
                sleeve=sleeve,
                candle=candle,
                snapshot=snapshot,
                history_bars=history_index,
                current_position=current_position,
                position_state_fingerprint=(
                    open_position.position_state_fingerprint if position_active_for_evaluation else None
                ),
            )
            evaluation = await self._backtest_service._strategy_family.evaluate(evaluation_input)
            decision = evaluation.decision
            market_structure = _market_structure_context(
                candles=candles,
                signal_index=signal_index,
                lookback=REPLAY_MARKET_STRUCTURE_LOOKBACK_CANDLES,
            )
            context = _build_replay_context(
                request=request,
                sleeve=sleeve,
                candle=candle,
                decision=decision,
                market_structure=market_structure,
                regime=regime,
                variant=variant,
                variant_state_has_diverged_from_baseline=variant_state_has_diverged_from_baseline,
                variant_position_active=position_active_for_evaluation,
            )

            if open_position is not None:
                if candle_close_time > open_position.entry_time:
                    open_position.record_excursion(candle)
                    mark_to_market_equity_points.append(
                        open_position.mark_to_market_equity(realized_equity, candle.low)
                    )
                if candle_close_time <= open_position.entry_time:
                    contexts.append(context)
                    continue
                if decision.action in {DecisionAction.CLOSE, DecisionAction.REDUCE}:
                    if decision.action == DecisionAction.REDUCE:
                        limitations.append("reduce_actions_are_simulated_as_full_exits_for_sv_replay")
                    fill = _resolve_fill(
                        candles=candles,
                        signal_index=signal_index,
                        fill_timing=request.assumptions.fill_timing,
                    )
                    if fill is None:
                        limitations.append(
                            f"{decision.action.value}_signal_skipped_no_fill_candle_for_"
                            f"{request.assumptions.fill_timing.value}"
                        )
                        contexts.append(context)
                        continue
                    trade = _close_trade(
                        request=request,
                        open_position=open_position,
                        fill=fill,
                        exit_signal_time=candle_close_time,
                        exit_reason=decision.reason_code or decision.action.value,
                        exit_evaluation_key=decision.evaluation_key,
                        exit_market_regime=regime.trend_label,
                        exit_volatility_regime=regime.volatility_label,
                        forced_exit=False,
                    )
                    trades.append(trade)
                    realized_equity = _money(realized_equity + trade.net_pnl)
                    closed_trade_equity_points.append(realized_equity)
                    mark_to_market_equity_points.append(realized_equity)
                    open_position = None
                contexts.append(context)
                continue

            if decision.status == StrategyDecisionStatus.INVALID:
                reason = decision.reason_code or "invalid_without_reason"
                invalid_reasons[reason] += 1
                contexts.append(context)
                continue

            should_open = decision.action == DecisionAction.OPEN
            entry_reason = decision.reason_code
            if decision.status == StrategyDecisionStatus.NO_TRADE:
                reason = decision.reason_code or "no_trade_without_reason"
                production_rule_rejection_reasons[reason] += 1
                if context.variant_candidate:
                    for code in context.variant_candidate_reason_codes:
                        variant_candidate_reasons[code] += 1
                    if context.variant_entry_allowed:
                        should_open = True
                        entry_reason = context.variant_entry_reason
                        variant_admitted_from_rejection_reasons[reason] += 1
                    else:
                        variant_rejected_reasons["variant_candidate_rejected"] += 1
                        variant_no_trade_reasons[reason] += 1
                        no_trade_reasons[reason] += 1
                else:
                    variant_no_trade_reasons[reason] += 1
                    no_trade_reasons[reason] += 1

            if should_open:
                if _dynamic_equity_is_depleted(request.assumptions, realized_equity):
                    invalid_reasons["dynamic_equity_depleted"] += 1
                    trades_skipped_due_to_insufficient_equity += 1
                    limitations.append("dynamic_equity_depleted_no_new_trades_opened")
                    contexts.append(context)
                    continue
                fill = _resolve_fill(
                    candles=candles,
                    signal_index=signal_index,
                    fill_timing=request.assumptions.fill_timing,
                )
                if fill is None:
                    limitations.append(
                        f"open_signal_skipped_no_fill_candle_for_{request.assumptions.fill_timing.value}"
                    )
                    contexts.append(context)
                    continue
                open_position = _open_trade(
                    request=request,
                    sleeve=sleeve,
                    fill=fill,
                    entry_signal_time=candle_close_time,
                    entry_reason=entry_reason,
                    entry_evaluation_key=decision.evaluation_key,
                    entry_market_regime=regime.trend_label,
                    entry_volatility_regime=regime.volatility_label,
                    current_realized_equity=realized_equity,
                )
                if context.variant_admitted_from_production_rule_rejection:
                    variant_state_has_diverged_from_baseline = True
                if _coerce_utc(fill.candle.close_time) > open_position.entry_time:
                    open_position.record_excursion(fill.candle)
                    mark_to_market_equity_points.append(
                        open_position.mark_to_market_equity(realized_equity, fill.candle.low)
                    )
            contexts.append(context)

        if open_position is not None and request.assumptions.force_close_open_trade_at_end:
            last_candle = _last_candle_in_window(candles, start_at=start_at, end_at=end_at)
            if last_candle is not None:
                force_fill = _ResolvedFill(
                    candle=last_candle,
                    raw_price=last_candle.close,
                    time=_coerce_utc(last_candle.close_time),
                    source="end_of_window_close",
                )
                trade = _close_trade(
                    request=request,
                    open_position=open_position,
                    fill=force_fill,
                    exit_signal_time=_coerce_utc(last_candle.close_time),
                    exit_reason="end_of_window_forced_close",
                    exit_evaluation_key=f"{open_position.entry_evaluation_key}:forced_exit",
                    exit_market_regime=regime_by_close_time.get(
                        _coerce_utc(last_candle.close_time),
                        _CandleRegime.unknown(_coerce_utc(last_candle.close_time)),
                    ).trend_label,
                    exit_volatility_regime=regime_by_close_time.get(
                        _coerce_utc(last_candle.close_time),
                        _CandleRegime.unknown(_coerce_utc(last_candle.close_time)),
                    ).volatility_label,
                    forced_exit=True,
                )
                trades.append(trade)
                realized_equity = _money(realized_equity + trade.net_pnl)
                closed_trade_equity_points.append(realized_equity)
                mark_to_market_equity_points.append(realized_equity)
                limitations.append("open_positions_are_force_closed_at_window_end_for_sv_replay")

        metrics = _build_metrics(
            trades=trades,
            initial_capital=request.assumptions.initial_capital,
            no_trade_reason_counts=dict(sorted(no_trade_reasons.items())),
            invalid_reason_counts=dict(sorted(invalid_reasons.items())),
            closed_trade_equity_points=closed_trade_equity_points,
            mark_to_market_equity_points=mark_to_market_equity_points,
            capital_sizing_mode=request.assumptions.capital_sizing_mode,
            position_notional_pct=request.assumptions.position_notional_pct,
            trades_skipped_due_to_insufficient_equity=trades_skipped_due_to_insufficient_equity,
        )
        rejected_summary = _rejected_signal_summary(contexts)
        variant_summary = {
            "variant_id": variant.variant_id,
            "methodology": variant.methodology,
            "contexts_evaluated": len(contexts),
            "baseline_entries_allowed": sum(1 for context in contexts if context.baseline_entry_allowed),
            "baseline_entries_rejected": sum(1 for context in contexts if context.baseline_entry_rejected),
            "production_rule_entries_allowed_in_replay_state": sum(
                1 for context in contexts if context.production_rule_entry_allowed_in_replay_state
            ),
            "production_rule_entries_rejected_in_replay_state": sum(
                1 for context in contexts if context.production_rule_entry_rejected_in_replay_state
            ),
            "variant_candidate_contexts": sum(1 for context in contexts if context.variant_candidate),
            "variant_entries_allowed": sum(1 for context in contexts if context.variant_entry_allowed),
            "variant_admitted_entry_count": sum(
                1 for context in contexts if context.variant_admitted_from_production_rule_rejection
            ),
            "variant_state_has_diverged_from_baseline": any(
                context.variant_state_has_diverged_from_baseline for context in contexts
            ),
            "independent_baseline_reference_per_candle": False,
            "replay_state_semantics": (
                "production_rule_* fields are Money Flow production-rule evaluations under the "
                "current replay state; after variant-only admission they are not an independent "
                "baseline path."
            ),
            "production_rule_rejection_reason_counts": dict(
                sorted(production_rule_rejection_reasons.items())
            ),
            "variant_admitted_from_rejection_reason_counts": dict(
                sorted(variant_admitted_from_rejection_reasons.items())
            ),
            "variant_no_trade_reason_counts": dict(sorted(variant_no_trade_reasons.items())),
            "variant_candidate_reason_counts": dict(sorted(variant_candidate_reasons.items())),
            "variant_rejected_candidate_reason_counts": dict(sorted(variant_rejected_reasons.items())),
            "variant_rejected_reason_counts": dict(sorted(variant_rejected_reasons.items())),
            "changes_production_rules": variant.changes_production_rules,
            "uses_dynamic_equity": (
                request.assumptions.capital_sizing_mode
                == StrategyValidationCapitalSizingMode.DYNAMIC_EQUITY_PCT
            ),
        }
        replay_payload = {
            "variant_id": variant.variant_id,
            "request": {
                "symbol": request.symbol,
                "component": sleeve.sleeve_id,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "fill_timing": request.assumptions.fill_timing.value,
                "capital_sizing_mode": request.assumptions.capital_sizing_mode.value,
            },
            "trade_ids": [trade.trade_id for trade in trades],
        }
        return MoneyFlowTrueReplayResult(
            replay_id=f"svrpl-{_stable_hash(replay_payload)[:24]}",
            variant=variant,
            request=request,
            component_key=sleeve.sleeve_id,
            timeframe=sleeve.timeframe,
            data_coverage=data_coverage,
            contexts=contexts,
            trades=trades,
            metrics=metrics,
            rejected_signal_summary=rejected_summary,
            variant_summary=variant_summary,
            limitations=sorted(set(limitations)),
            boundary_flags={
                "research_only": True,
                "changes_production_money_flow_rules": False,
                "optimizes_parameters": False,
                "approves_paper_trading": False,
                "creates_live_artifacts": False,
                "creates_routing_artifacts": False,
                "calls_exchange_adapters": False,
            },
        )


def money_flow_true_replay_result_to_dict(result: MoneyFlowTrueReplayResult) -> dict[str, Any]:
    return _json_ready(
        {
            "replay_id": result.replay_id,
            "variant": asdict(result.variant),
            "request": {
                "strategy_family": result.request.strategy_family.value,
                "environment": result.request.environment.value,
                "venue": result.request.venue,
                "symbol": result.request.symbol,
                "instrument_key": result.request.instrument_key,
                "start_at": result.request.start_at,
                "end_at": result.request.end_at,
                "component_keys": result.request.component_keys,
                "assumptions": asdict(result.request.assumptions),
            },
            "component_key": result.component_key,
            "timeframe": result.timeframe,
            "data_coverage": asdict(result.data_coverage),
            "contexts": [asdict(context) for context in result.contexts],
            "trades": [asdict(trade) for trade in result.trades],
            "metrics": asdict(result.metrics),
            "rejected_signal_summary": result.rejected_signal_summary,
            "variant_summary": result.variant_summary,
            "limitations": result.limitations,
            "boundary_flags": result.boundary_flags,
        }
    )


def money_flow_replay_report_to_markdown(
    baseline_results: list[MoneyFlowTrueReplayResult],
    variant_results: list[MoneyFlowTrueReplayResult],
    *,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(UTC)
    lines = [
        "# SV1.16 Rejected-Signal Replay Instrumentation",
        "",
        f"Recorded at: `{generated_at.replace(microsecond=0).isoformat().replace('+00:00', 'Z')}`",
        "",
        "Status: `replay_substrate_ready_for_founder_review`",
        "",
        "This report is research-only. SV1.16 records per-candle production-rule decision context and runs a narrow "
        "lower-RSI true replay example without changing production Money Flow rules, approving paper trading, "
        "adding live execution, routing, or calling exchange endpoints.",
        "",
        "## Methodology",
        "",
        f"- Replay context methodology: `{REPLAY_CONTEXT_METHODOLOGY}`",
        "- Each evaluated candle records production-rule action/reason context in the current replay state, RSI zone, indicator values, regime labels, and descriptive market-structure context.",
        "- SV1.16.1 terminology: `production_rule_*_in_replay_state` means current Money Flow rule evaluation under the active replay state. In a variant run, once a variant-only entry is admitted, later production-rule evaluations are in the variant state rather than an independent baseline path.",
        "- Legacy `baseline_*` fields remain as compatibility aliases for production-rule evaluation, but founder interpretation should use the clearer production-rule-in-replay-state fields.",
        "- Rejected production-rule entry candles are retained so later lower-RSI variants can be tested from candles rather than completed-trade overlays.",
        "- True replay maintains position occupancy and dynamic-equity path inside each independent scenario.",
        "- This is not full margin, funding, liquidation, order-book, or portfolio simulation.",
        "",
        "## Baseline Replay Parity",
        "",
        "- Focused SV1.16 tests compare the baseline true replay against the existing Strategy Validation backtest on a deterministic fixture.",
        "- The parity check covers trade count, entry times, exit times, net account PnL, and ending equity.",
        "- If a future replay variant cannot preserve baseline parity, its founder-facing output must be treated as instrumentation-only until the mismatch is resolved.",
        "",
        "## Baseline Vs Lower-RSI Trend-Intact Replay",
        "",
        "| Component | Variant | Contexts | Trades | Ending Equity | Net Account PnL | Rejected Entries | Variant Candidates | Variant Entries |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in [*baseline_results, *variant_results]:
        lines.append(
            "| {component} | `{variant}` | {contexts} | {trades} | ${ending} | ${pnl} | {rejected} | {candidates} | {variant_entries} |".format(
                component=result.component_key,
                variant=result.variant.variant_id,
                contexts=len(result.contexts),
                trades=result.metrics.number_of_trades,
                ending=_format_decimal(result.metrics.ending_equity),
                pnl=_format_decimal(result.metrics.net_account_pnl),
                rejected=result.rejected_signal_summary["baseline_entry_rejected_count"],
                candidates=result.variant_summary["variant_candidate_contexts"],
                variant_entries=result.variant_summary["variant_entries_allowed"],
            )
        )
    lines.extend(
        [
            "",
            "## SV1.16.1 Replay Methodology Truth",
            "",
            "- Variant replay can diverge from the baseline path after a variant admits a candle that production rules rejected.",
            "- The current SV1.16.1 report does not compute an independent per-candle baseline reference path after that divergence; it reports production-rule evaluation in the current replay state.",
            "- Production-rule rejection counts are separated from variant no-trade truth.",
            "- If production rules reject a candle and the variant admits it, that candle is counted under `variant_admitted_from_rejection_reason_counts`, not as a variant no-trade.",
            "- The lower-RSI result remains a sampled research replay result, not a production rule, not paper trading authorization, and not live trading authorization.",
            "",
            "## Variant Counter Separation",
            "",
            "| Component | Variant | Production-Rule Rejections In Replay State | Admitted From Rejection | Variant No-Trade Reasons | Variant Rejected Candidates |",
            "|---|---|---|---|---|---|",
        ]
    )
    for result in variant_results:
        lines.append(
            "| {component} | `{variant}` | {production_rejections} | {admitted} | {variant_no_trade} | {variant_rejected} |".format(
                component=result.component_key,
                variant=result.variant.variant_id,
                production_rejections=_format_counts(
                    result.variant_summary.get("production_rule_rejection_reason_counts", {})
                ),
                admitted=_format_counts(
                    result.variant_summary.get("variant_admitted_from_rejection_reason_counts", {})
                ),
                variant_no_trade=_format_counts(
                    result.variant_summary.get("variant_no_trade_reason_counts", {})
                ),
                variant_rejected=_format_counts(
                    result.variant_summary.get("variant_rejected_candidate_reason_counts", {})
                ),
            )
        )
    lines.extend(
        [
            "",
            "## Rejected-Signal Summary",
            "",
            "| Component | Variant | Top Rejection Reasons | RSI Zone Counts |",
            "|---|---|---|---|",
        ]
    )
    for result in variant_results:
        lines.append(
            "| {component} | `{variant}` | {reasons} | {zones} |".format(
                component=result.component_key,
                variant=result.variant.variant_id,
                reasons=_format_counts(result.rejected_signal_summary["entry_rejection_reason_counts"]),
                zones=_format_counts(result.rejected_signal_summary["rsi_zone_counts"]),
            )
        )
    lines.extend(
        [
            "",
            "## Lower-RSI Variant Boundary",
            "",
            f"- Variant id: `{LOWER_RSI_TREND_INTACT_VARIANT_ID}`",
            "- It admits below-floor RSI candidates only in the Strategy Validation replay path.",
            "- It still requires trend-intact context, constructive MACD, non-extended price, and pullback/support context.",
            "- It is not a production rule, not a recommendation, and not paper/live authorization.",
            "",
            "## Boundary Flags",
            "",
        ]
    )
    flags = variant_results[0].boundary_flags if variant_results else {}
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(flags.items()))
    lines.extend(
        [
            "",
            "## Deferred Work",
            "",
            "- Add more true replay variants only after founder review of this substrate.",
            "- Add exact stop/exit replay for recent-low invalidation separately.",
            "- Add broader windows/out-of-sample checks before any later paper-trading design phase.",
            "- Keep Aster/Binance/OKX/Coinbase/Kraken outside this Hyperliquid-only replay result.",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_replay_context(
    *,
    request: StrategyValidationRequest,
    sleeve: MoneyFlowSleeveConfig,
    candle: Candle,
    decision: Any,
    market_structure: MoneyFlowReplayMarketStructure,
    regime: _CandleRegime,
    variant: MoneyFlowReplayVariant,
    variant_state_has_diverged_from_baseline: bool,
    variant_position_active: bool,
) -> MoneyFlowReplayCandleContext:
    features = decision.features or {}
    rsi = _optional_decimal(features.get("rsi_value"))
    floor = Decimal(str(sleeve.rsi_floor))
    ceiling = Decimal(str(sleeve.rsi_ceiling))
    rsi_zone = _rsi_zone(rsi, floor=floor, ceiling=ceiling)
    baseline_status = decision.status.value
    baseline_action = decision.action.value
    if decision.status == StrategyDecisionStatus.NO_TRADE:
        baseline_action = "no_trade"
    elif decision.status == StrategyDecisionStatus.INVALID:
        baseline_action = "invalid"
    baseline_entry_allowed = decision.action == DecisionAction.OPEN
    baseline_entry_rejected = decision.status == StrategyDecisionStatus.NO_TRADE
    reason = decision.reason_code
    variant_candidate = False
    variant_reason_codes: tuple[str, ...] = ()
    variant_entry_allowed = False
    variant_entry_reason = None
    if baseline_entry_rejected and variant.variant_id == LOWER_RSI_TREND_INTACT_VARIANT_ID:
        variant_entry_allowed, variant_reason_codes = _lower_rsi_variant_allows_entry(
            variant=variant,
            sleeve=sleeve,
            features=features,
            rsi=rsi,
            rsi_zone=rsi_zone,
            market_structure=market_structure,
        )
        variant_candidate = "below_floor_rsi_candidate" in variant_reason_codes
        if variant_entry_allowed:
            variant_entry_reason = variant.variant_id
    context_has_diverged = variant_state_has_diverged_from_baseline or (
        baseline_entry_rejected and variant_entry_allowed
    )
    replay_state_source = (
        "variant_state_after_divergence" if context_has_diverged else "production_baseline_state"
    )
    return MoneyFlowReplayCandleContext(
        symbol=request.symbol,
        component_key=sleeve.sleeve_id,
        timeframe=sleeve.timeframe,
        candle_open_time=_coerce_utc(candle.open_time),
        candle_close_time=_coerce_utc(candle.close_time),
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        ema5=_optional_decimal(features.get("ema5")),
        ema10=_optional_decimal(features.get("ema10")),
        sma20=_optional_decimal(features.get("sma20")),
        rsi14=rsi,
        macd=_optional_decimal(features.get("macd_value")),
        macd_signal=_optional_decimal(features.get("macd_signal_value")),
        macd_histogram=_optional_decimal(features.get("macd_histogram")),
        production_rule_action_in_replay_state=baseline_action,
        production_rule_status_in_replay_state=baseline_status,
        production_rule_reason_codes_in_replay_state=(reason,) if reason else (),
        production_rule_entry_allowed_in_replay_state=baseline_entry_allowed,
        production_rule_entry_rejected_in_replay_state=baseline_entry_rejected,
        baseline_action=baseline_action,
        baseline_status=baseline_status,
        baseline_reason_codes=(reason,) if reason else (),
        baseline_entry_allowed=baseline_entry_allowed,
        baseline_entry_rejected=baseline_entry_rejected,
        entry_rejection_reason=reason if baseline_entry_rejected else None,
        rsi_value=rsi,
        rsi_sleeve_floor=floor,
        rsi_sleeve_ceiling=ceiling,
        rsi_zone=rsi_zone,
        ema_trend_stack_state=_ema_stack_state(features),
        macd_constructive=bool(features.get("macd_constructive")),
        price_extension_from_ema5=_optional_decimal(features.get("extension_pct_above_ema5")),
        market_regime_label=regime.trend_label,
        volatility_regime_label=regime.volatility_label,
        market_structure=market_structure,
        variant_state_has_diverged_from_baseline=context_has_diverged,
        variant_position_active=variant_position_active,
        baseline_reference_position_active=None if context_has_diverged else variant_position_active,
        replay_state_source=replay_state_source,
        variant_candidate=variant_candidate,
        variant_candidate_reason_codes=variant_reason_codes,
        variant_entry_allowed=variant_entry_allowed,
        variant_entry_reason=variant_entry_reason,
        variant_admitted_from_production_rule_rejection=baseline_entry_rejected and variant_entry_allowed,
    )


def _lower_rsi_variant_allows_entry(
    *,
    variant: MoneyFlowReplayVariant,
    sleeve: MoneyFlowSleeveConfig,
    features: dict[str, Any],
    rsi: Decimal | None,
    rsi_zone: str,
    market_structure: MoneyFlowReplayMarketStructure,
) -> tuple[bool, tuple[str, ...]]:
    codes: list[str] = []
    if rsi_zone != "below_floor":
        return False, tuple(codes)
    codes.append("below_floor_rsi_candidate")
    floor = variant.lower_rsi_floor_by_component.get(sleeve.sleeve_id)
    if floor is None:
        codes.append("variant_floor_missing")
        return False, tuple(codes)
    if rsi is None or rsi < floor:
        codes.append("rsi_below_variant_floor")
        return False, tuple(codes)
    if variant.requires_trend_intact and not bool(features.get("bullish_alignment")):
        codes.append("trend_not_intact")
        return False, tuple(codes)
    latest_close = _optional_decimal(features.get("latest_close"))
    sma20 = _optional_decimal(features.get("sma20"))
    ema10 = _optional_decimal(features.get("ema10"))
    if latest_close is None or sma20 is None or latest_close < sma20:
        codes.append("price_below_sma20")
        return False, tuple(codes)
    if variant.requires_macd_constructive and not bool(features.get("macd_constructive")):
        codes.append("macd_not_constructive")
        return False, tuple(codes)
    extension = _optional_decimal(features.get("extension_pct_above_ema5"))
    if extension is not None and extension > Decimal(str(sleeve.max_extension_pct_above_ema5)):
        codes.append("price_too_extended")
        return False, tuple(codes)
    near_ema10 = False
    if latest_close is not None and ema10 not in (None, Decimal("0")):
        near_ema10 = abs((latest_close - ema10) / ema10) <= Decimal("0.01")
    if variant.requires_pullback_or_support and not (near_ema10 or market_structure.near_support):
        codes.append("not_near_ema10_or_support")
        return False, tuple(codes)
    codes.append("lower_rsi_trend_intact_entry_allowed")
    return True, tuple(codes)


def _market_structure_context(
    *,
    candles: list[Candle],
    signal_index: int,
    lookback: int,
) -> MoneyFlowReplayMarketStructure:
    prior = candles[max(0, signal_index - lookback) : signal_index]
    close = candles[signal_index].close
    if not prior:
        return MoneyFlowReplayMarketStructure(
            lookback_candles=lookback,
            recent_swing_high=None,
            recent_swing_low=None,
            distance_to_recent_swing_high_pct=None,
            distance_to_recent_swing_low_pct=None,
            near_support=False,
            near_resistance=False,
            breakout_context=False,
        )
    high = max(candle.high for candle in prior)
    low = min(candle.low for candle in prior)
    distance_high = ((high - close) / close) if close else None
    distance_low = ((close - low) / close) if close else None
    return MoneyFlowReplayMarketStructure(
        lookback_candles=lookback,
        recent_swing_high=_money(high),
        recent_swing_low=_money(low),
        distance_to_recent_swing_high_pct=_money(distance_high) if distance_high is not None else None,
        distance_to_recent_swing_low_pct=_money(distance_low) if distance_low is not None else None,
        near_support=distance_low is not None and Decimal("0") <= distance_low <= Decimal("0.01"),
        near_resistance=distance_high is not None and Decimal("0") <= distance_high <= Decimal("0.01"),
        breakout_context=close > high,
    )


def _rejected_signal_summary(contexts: list[MoneyFlowReplayCandleContext]) -> dict[str, Any]:
    rejected = [context for context in contexts if context.baseline_entry_rejected]
    return {
        "baseline_entry_rejected_count": len(rejected),
        "entry_rejection_reason_counts": dict(
            sorted(Counter(context.entry_rejection_reason or "unknown" for context in rejected).items())
        ),
        "rsi_zone_counts": dict(sorted(Counter(context.rsi_zone for context in contexts).items())),
        "below_floor_rejected_count": sum(1 for context in rejected if context.rsi_zone == "below_floor"),
        "captured_rejected_signal_context": True,
    }


def _rsi_zone(rsi: Decimal | None, *, floor: Decimal, ceiling: Decimal) -> str:
    if rsi is None:
        return "unknown"
    if rsi < floor:
        return "below_floor"
    if rsi > ceiling:
        return "above_ceiling"
    width = ceiling - floor
    midpoint = floor + (width / Decimal("2"))
    near_upper_threshold = ceiling - (width * Decimal("0.2"))
    if rsi >= near_upper_threshold:
        return "near_upper_band"
    if rsi <= midpoint:
        return "lower_band_half"
    return "upper_band_half"


def _ema_stack_state(features: dict[str, Any]) -> str:
    if bool(features.get("bullish_alignment")):
        return "ema5_gt_ema10_gt_sma20"
    ema5 = _optional_decimal(features.get("ema5"))
    ema10 = _optional_decimal(features.get("ema10"))
    sma20 = _optional_decimal(features.get("sma20"))
    if ema5 is None or ema10 is None or sma20 is None:
        return "unknown"
    if ema5 <= ema10:
        return "ema5_not_above_ema10"
    if ema10 <= sma20:
        return "ema10_not_above_sma20"
    return "not_constructive"


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "`none`"
    return ", ".join(f"`{key}`={value}" for key, value in sorted(counts.items()))


__all__ = [
    "BASELINE_REPLAY_VARIANT_ID",
    "LOWER_RSI_TREND_INTACT_VARIANT_ID",
    "MoneyFlowReplayCandleContext",
    "MoneyFlowReplayMarketStructure",
    "MoneyFlowReplayVariant",
    "MoneyFlowTrueReplayResult",
    "MoneyFlowVariantReplayService",
    "baseline_replay_variant",
    "lower_rsi_floor_trend_intact_variant",
    "money_flow_replay_report_to_markdown",
    "money_flow_true_replay_result_to_dict",
]
