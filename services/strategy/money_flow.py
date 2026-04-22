"""Money Flow strategy family implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.config.settings import AppSettings, MoneyFlowSleeveConfig, get_settings
from core.domain.enums import DecisionAction, SignalType, StrategyDecisionStatus, StrategyFamily
from core.domain.models import (
    IndicatorSnapshot,
    SignalEvent,
    StrategyDecision,
    StrategyEvaluationInput,
    StrategyEvaluationResult,
    StrategyFamilyStatus,
)
from services.strategy.base import StrategyFamilyModule


def _now() -> datetime:
    return datetime.now(UTC)


class MoneyFlowStrategyFamily(StrategyFamilyModule):
    STRATEGY_VERSION = "money_flow_v1_1"

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or get_settings()

    async def evaluate(self, evaluation_input: StrategyEvaluationInput) -> StrategyEvaluationResult:
        sleeve = MoneyFlowSleeveConfig.model_validate(evaluation_input.family_config)
        decision_time = _now()
        base_provenance = {
            "strategy_version": self.STRATEGY_VERSION,
            "config_fingerprint": evaluation_input.config_fingerprint,
            "indicator_as_of": (
                evaluation_input.indicator_snapshot.as_of.isoformat()
                if evaluation_input.indicator_snapshot is not None
                else None
            ),
            "latest_candle_close": (
                evaluation_input.latest_candle_close.isoformat()
                if evaluation_input.latest_candle_close is not None
                else None
            ),
            "market_data_source_policy_ref_id": evaluation_input.market_data_source_policy_ref_id,
            "market_data_source_venue": evaluation_input.market_data_source_venue,
            "market_data_source_mode": evaluation_input.market_data_source_mode.value,
            "position_state_fingerprint": evaluation_input.position_state_fingerprint,
            "mandate_key": evaluation_input.mandate_key,
            "binding_key": evaluation_input.binding_key,
            "venue_account_key": evaluation_input.venue_account_key,
        }

        if not self.settings.money_flow.strategy_enabled:
            signal = _build_signal(
                evaluation_input=evaluation_input,
                signal_type=SignalType.NO_TRADE,
                generated_at=decision_time,
                reason_code="strategy_family_disabled",
                provenance=base_provenance,
                features={"status": "invalid"},
            )
            decision = _build_decision(
                evaluation_input=evaluation_input,
                decided_at=decision_time,
                action=DecisionAction.NOOP,
                status=StrategyDecisionStatus.INVALID,
                reason_code="strategy_family_disabled",
                confidence=None,
                rationale="Money Flow family disabled in configuration.",
                provenance=base_provenance,
                features=signal.features,
                signal_id=signal.signal_id,
            )
            return StrategyEvaluationResult(signal_event=signal, decision=decision)

        invalid_reason = _validate_input(evaluation_input, sleeve)
        if invalid_reason is not None:
            signal = _build_signal(
                evaluation_input=evaluation_input,
                signal_type=SignalType.NO_TRADE,
                generated_at=decision_time,
                reason_code=invalid_reason,
                provenance=base_provenance,
                features={"status": "invalid"},
            )
            decision = _build_decision(
                evaluation_input=evaluation_input,
                decided_at=decision_time,
                action=DecisionAction.NOOP,
                status=StrategyDecisionStatus.INVALID,
                reason_code=invalid_reason,
                confidence=None,
                rationale=f"Money Flow invalid-state rejection: {invalid_reason}.",
                provenance=base_provenance,
                features=signal.features,
                signal_id=signal.signal_id,
            )
            return StrategyEvaluationResult(signal_event=signal, decision=decision)

        snapshot = evaluation_input.indicator_snapshot
        assert snapshot is not None
        assert evaluation_input.latest_candle is not None

        features = _money_flow_features(
            snapshot=snapshot,
            sleeve=sleeve,
            latest_close=float(evaluation_input.latest_candle.close),
        )

        if evaluation_input.current_position is not None:
            action, signal_type, reason_code, rationale = _decide_exit_or_hold(features, sleeve=sleeve)
            decision = _build_decision(
                evaluation_input=evaluation_input,
                decided_at=decision_time,
                action=action,
                status=StrategyDecisionStatus.PROPOSED,
                reason_code=reason_code,
                confidence=_confidence(features),
                rationale=rationale,
                provenance=base_provenance,
                features=features,
                signal_id=None,
            )
            signal = None
            if signal_type is not None:
                signal = _build_signal(
                    evaluation_input=evaluation_input,
                    signal_type=signal_type,
                    generated_at=decision_time,
                    reason_code=reason_code,
                    provenance=base_provenance,
                    features=features,
                )
                decision.signal_id = signal.signal_id
            return StrategyEvaluationResult(signal_event=signal, decision=decision)

        reason_code = _decide_entry_reason(features, sleeve=sleeve)
        if reason_code is not None:
            signal = _build_signal(
                evaluation_input=evaluation_input,
                signal_type=SignalType.NO_TRADE,
                generated_at=decision_time,
                reason_code=reason_code,
                provenance=base_provenance,
                features=features,
            )
            decision = _build_decision(
                evaluation_input=evaluation_input,
                decided_at=decision_time,
                action=DecisionAction.NOOP,
                status=StrategyDecisionStatus.NO_TRADE,
                reason_code=reason_code,
                confidence=_confidence(features),
                rationale=f"Money Flow no-trade: {reason_code}.",
                provenance=base_provenance,
                features=features,
                signal_id=signal.signal_id,
            )
            return StrategyEvaluationResult(signal_event=signal, decision=decision)

        signal = _build_signal(
            evaluation_input=evaluation_input,
            signal_type=SignalType.ENTRY,
            generated_at=decision_time,
            reason_code=None,
            provenance=base_provenance,
            features=features,
        )
        decision = _build_decision(
            evaluation_input=evaluation_input,
            decided_at=decision_time,
            action=DecisionAction.OPEN,
            status=StrategyDecisionStatus.PROPOSED,
            reason_code=None,
            confidence=_confidence(features),
            rationale="Money Flow bullish alignment with acceptable pullback/continuation quality.",
            provenance=base_provenance,
            features=features,
            signal_id=signal.signal_id,
        )
        return StrategyEvaluationResult(signal_event=signal, decision=decision)

    async def get_family_status(self) -> StrategyFamilyStatus:
        sleeves = [sleeve.sleeve_id for sleeve in self.settings.money_flow.sleeves]
        enabled = sum(1 for sleeve in self.settings.money_flow.sleeves if sleeve.enabled)
        return StrategyFamilyStatus(
            family=StrategyFamily.MONEY_FLOW,
            components=sleeves,
            enabled_components=enabled,
            latest_decision_at=None,
        )


def _validate_input(
    evaluation_input: StrategyEvaluationInput,
    sleeve: MoneyFlowSleeveConfig,
) -> str | None:
    if not _self_enabled(evaluation_input, sleeve):
        return "sleeve_disabled"
    if not evaluation_input.instrument_active:
        return "instrument_inactive"
    if not evaluation_input.instrument_strategy_eligible:
        return "instrument_not_strategy_eligible"
    if not evaluation_input.market_data_fresh:
        return "stale_market_data"
    if evaluation_input.indicator_snapshot is None:
        return "missing_indicator_snapshot"
    if evaluation_input.latest_candle is None:
        return "missing_latest_candle"
    if not evaluation_input.indicator_boundary_aligned:
        return "stale_indicator_snapshot"
    if evaluation_input.history_bars < sleeve.min_history_bars:
        return "insufficient_history"
    if evaluation_input.instrument_key == "":
        return "malformed_instrument_mapping"
    return None


def _self_enabled(evaluation_input: StrategyEvaluationInput, sleeve: MoneyFlowSleeveConfig) -> bool:
    return bool(_self_enabled_family(evaluation_input) and sleeve.enabled and evaluation_input.sleeve_enabled)


def _self_enabled_family(evaluation_input: StrategyEvaluationInput) -> bool:
    return evaluation_input.family == StrategyFamily.MONEY_FLOW


def _money_flow_features(
    *,
    snapshot: IndicatorSnapshot,
    sleeve: MoneyFlowSleeveConfig,
    latest_close: float,
) -> dict[str, object]:
    ema5 = float(snapshot.ema_5 or 0)
    ema10 = float(snapshot.ema_10 or 0)
    sma20 = float(snapshot.sma_20 or 0)
    rsi = float(snapshot.rsi_14 or 0)
    macd = float(snapshot.macd or 0)
    macd_signal = float(snapshot.macd_signal or 0)
    macd_hist = float(snapshot.macd_histogram or 0)

    bullish_alignment = ema5 > ema10 > sma20
    bearish_alignment_break = ema5 <= ema10 or ema10 <= sma20 or latest_close < ema10
    trend_invalidated = latest_close < sma20 or ema5 <= ema10
    macd_constructive = macd > macd_signal and macd_hist >= 0
    macd_rollover = macd < macd_signal or macd_hist < 0
    pullback_quality = latest_close >= ema10 and latest_close <= ema5 * (1 + sleeve.max_extension_pct_above_ema5)
    continuation_quality = latest_close > ema5 and latest_close <= ema5 * (1 + sleeve.max_extension_pct_above_ema5)
    rsi_constructive = sleeve.rsi_floor <= rsi <= sleeve.rsi_ceiling
    rsi_overbought = rsi >= sleeve.overbought_rsi
    rsi_trim = rsi >= sleeve.trim_rsi
    extension_pct_above_ema5 = ((latest_close / ema5) - 1.0) if ema5 else 0.0
    return {
        "bullish_alignment": bullish_alignment,
        "bearish_alignment_break": bearish_alignment_break,
        "trend_invalidated": trend_invalidated,
        "pullback_quality": pullback_quality,
        "continuation_quality": continuation_quality,
        "rsi_value": rsi,
        "rsi_constructive": rsi_constructive,
        "rsi_overbought": rsi_overbought,
        "rsi_trim": rsi_trim,
        "macd_value": macd,
        "macd_signal_value": macd_signal,
        "macd_histogram": macd_hist,
        "macd_constructive": macd_constructive,
        "macd_rollover": macd_rollover,
        "extension_pct_above_ema5": extension_pct_above_ema5,
        "latest_close": latest_close,
        "ema5": ema5,
        "ema10": ema10,
        "sma20": sma20,
    }


def _decide_entry_reason(features: dict[str, object], sleeve: MoneyFlowSleeveConfig) -> str | None:
    if not bool(features["bullish_alignment"]):
        return "bearish_alignment"
    if bool(features["rsi_overbought"]):
        return "overextended_rsi"
    if not bool(features["rsi_constructive"]):
        return "rsi_not_constructive"
    if sleeve.require_macd_confirmation and not bool(features["macd_constructive"]):
        return "macd_not_constructive"
    pullback_ok = sleeve.allow_pullback_entries and bool(features["pullback_quality"])
    continuation_ok = sleeve.allow_continuation_entries and bool(features["continuation_quality"])
    if not (pullback_ok or continuation_ok):
        return "entry_quality_not_constructive"
    if float(features["extension_pct_above_ema5"]) > sleeve.max_extension_pct_above_ema5:
        return "price_too_extended"
    return None


def _decide_exit_or_hold(
    features: dict[str, object],
    *,
    sleeve: MoneyFlowSleeveConfig,
) -> tuple[DecisionAction, SignalType | None, str | None, str]:
    if sleeve.close_on_ma_break and bool(features["bearish_alignment_break"]):
        return (
            DecisionAction.CLOSE,
            SignalType.EXIT,
            "ma_alignment_break",
            "Money Flow exit: moving-average alignment broke below acceptable holding state.",
        )
    if bool(features["trend_invalidated"]):
        return (
            DecisionAction.CLOSE,
            SignalType.EXIT,
            "trend_invalidated",
            "Money Flow exit: price/trend state invalidated the holding condition.",
        )
    if sleeve.close_on_macd_rollover and bool(features["macd_rollover"]):
        return (
            DecisionAction.CLOSE,
            SignalType.EXIT,
            "macd_rollover",
            "Money Flow exit: MACD deteriorated against the holding trend.",
        )
    if sleeve.trim_on_overbought_rsi and bool(features["rsi_trim"]):
        return (
            DecisionAction.REDUCE,
            SignalType.RISK_REDUCTION,
            "trim_on_overbought_rsi",
            "Money Flow reduce: RSI extension reached the configured trim threshold.",
        )
    return (
        DecisionAction.HOLD,
        None,
        None,
        "Money Flow hold: position remains constructive and no exit condition is active.",
    )


def _confidence(features: dict[str, object]) -> Decimal:
    score = 0.45
    if bool(features["bullish_alignment"]):
        score += 0.2
    if bool(features["rsi_constructive"]):
        score += 0.1
    if bool(features["macd_constructive"]):
        score += 0.15
    if bool(features["pullback_quality"]) or bool(features["continuation_quality"]):
        score += 0.1
    return Decimal(str(min(score, 0.99))).quantize(Decimal("0.0001"))


def _build_signal(
    *,
    evaluation_input: StrategyEvaluationInput,
    signal_type: SignalType,
    generated_at: datetime,
    reason_code: str | None,
    provenance: dict[str, object],
    features: dict[str, object],
) -> SignalEvent:
    return SignalEvent(
        signal_id=f"sig-{evaluation_input.evaluation_key[:24]}",
        evaluation_key=evaluation_input.evaluation_key,
        family=StrategyFamily.MONEY_FLOW,
        sleeve_id=evaluation_input.sleeve_id,
        component_key=evaluation_input.component_key,
        client_ref_id=evaluation_input.client_ref_id,
        strategy_mandate_ref_id=evaluation_input.strategy_mandate_ref_id,
        mandate_key=evaluation_input.mandate_key,
        mandate_account_binding_ref_id=evaluation_input.mandate_account_binding_ref_id,
        binding_key=evaluation_input.binding_key,
        venue_account_ref_id=evaluation_input.venue_account_ref_id,
        instrument_key=evaluation_input.instrument_key,
        instrument_ref_id=evaluation_input.instrument_ref_id,
        symbol=evaluation_input.symbol,
        timeframe=evaluation_input.timeframe,
        signal_type=signal_type,
        generated_at=generated_at,
        reason_code=reason_code,
        provenance=provenance,
        features=features,
    )


def _build_decision(
    *,
    evaluation_input: StrategyEvaluationInput,
    decided_at: datetime,
    action: DecisionAction,
    status: StrategyDecisionStatus,
    reason_code: str | None,
    confidence: Decimal | None,
    rationale: str,
    provenance: dict[str, object],
    features: dict[str, object],
    signal_id: str | None,
) -> StrategyDecision:
    return StrategyDecision(
        decision_id=f"dec-{evaluation_input.evaluation_key[:24]}",
        evaluation_key=evaluation_input.evaluation_key,
        family=StrategyFamily.MONEY_FLOW,
        sleeve_id=evaluation_input.sleeve_id,
        component_key=evaluation_input.component_key,
        client_ref_id=evaluation_input.client_ref_id,
        strategy_mandate_ref_id=evaluation_input.strategy_mandate_ref_id,
        mandate_key=evaluation_input.mandate_key,
        mandate_account_binding_ref_id=evaluation_input.mandate_account_binding_ref_id,
        binding_key=evaluation_input.binding_key,
        venue_account_ref_id=evaluation_input.venue_account_ref_id,
        instrument_key=evaluation_input.instrument_key,
        instrument_ref_id=evaluation_input.instrument_ref_id,
        signal_id=signal_id,
        symbol=evaluation_input.symbol,
        action=action,
        status=status,
        reason_code=reason_code,
        confidence=confidence,
        rationale=rationale,
        decided_at=decided_at,
        provenance=provenance,
        features=features,
    )
