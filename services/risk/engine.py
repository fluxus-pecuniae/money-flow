"""Risk evaluation and desired-trade approval layer."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
from typing import Any

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    DecisionAction,
    MandateDesiredTradeStatus,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    PositionStatus,
    RiskEvaluationOutcome,
    StrategyDecisionStatus,
    TradeTargetScope,
)
from core.domain.models import (
    BindingRoutingCandidate,
    MandateDesiredTrade,
    RiskEvaluation,
)
from core.interfaces.services import (
    ExecutionService,
    MandateTradePlanningService,
    PortfolioService,
    RiskEngine,
    RuntimeContextService,
)
from db.models import (
    ExchangeAccountSnapshotModel,
    InstrumentModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    PositionModel,
    RiskEvaluationModel,
    StrategyComponentConfigModel,
    StrategyDecisionModel,
    SymbolModel,
)
from db.session import SessionLocal
from services.execution.service import ChildIntentPreparationError, DefaultExecutionService
from services.planning.service import DefaultTradePlanningService
from services.portfolio.service import DefaultPortfolioService
from services.runtime.context import DefaultRuntimeContextService


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _position_quantity(position: PositionModel) -> Decimal:
    quantity = position.quantity
    return quantity.copy_abs() if hasattr(quantity, "copy_abs") else abs(quantity)


class DefaultRiskEngine(RiskEngine):
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        planning_service: MandateTradePlanningService | None = None,
        execution_service: ExecutionService | None = None,
        portfolio_service: PortfolioService | None = None,
        runtime_context_service: RuntimeContextService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self.runtime_context_service = runtime_context_service or DefaultRuntimeContextService(
            self.settings,
            session_factory=session_factory,
        )
        self.planning_service = planning_service or DefaultTradePlanningService(
            self.settings,
            session_factory=session_factory,
            runtime_context_service=self.runtime_context_service,
        )
        self.execution_service = execution_service or DefaultExecutionService(
            self.settings,
            session_factory=session_factory,
        )
        self.portfolio_service = portfolio_service or DefaultPortfolioService(
            self.settings,
            runtime_context_service=self.runtime_context_service,
        )

    async def evaluate_strategy_decision(self, decision_id: str) -> RiskEvaluation:
        with self._session_factory() as session:
            decision = self._load_decision_model(session, decision_id)
            source_policy = self._load_source_policy(session, decision.strategy_mandate_ref_id)
            instrument_key = self._lookup_instrument_key(session, decision.instrument_ref_id)
            position = self._load_bound_position(
                session,
                instrument_ref_id=decision.instrument_ref_id,
                venue_account_ref_id=decision.venue_account_ref_id,
            )

        assessment = await self.planning_service.inspect_decision_convertibility(decision_id)
        if not assessment.convertible:
            return self._persist_no_desired_trade_evaluation(
                decision=decision,
                source_policy=source_policy,
                instrument_key=instrument_key,
                reason_code=assessment.reason_code or "non_convertible",
                message=assessment.message,
                outcome=RiskEvaluationOutcome.NO_DESIRED_TRADE,
                position=position,
            )

        desired_trade = await self.planning_service.preview_desired_trade_from_decision(decision_id, persist=True)
        return await self._evaluate_desired_trade_internal(
            desired_trade,
            decision=decision,
        )

    async def evaluate_desired_trade(self, desired_trade: MandateDesiredTrade) -> RiskEvaluation:
        decision = None
        with self._session_factory() as session:
            if desired_trade.source_decision_ids:
                decision = self._load_decision_model(session, desired_trade.source_decision_ids[0])
        return await self._evaluate_desired_trade_internal(desired_trade, decision=decision)

    async def recent_evaluations(
        self,
        *,
        outcome: str | None = None,
        desired_trade_status: MandateDesiredTradeStatus | None = None,
        limit: int = 100,
    ) -> Sequence[RiskEvaluation]:
        with self._session_factory() as session:
            query = select(RiskEvaluationModel).where(
                RiskEvaluationModel.environment == self.settings.app.environment
            )
            if outcome is not None:
                query = query.where(RiskEvaluationModel.outcome == outcome)
            if desired_trade_status is not None:
                query = query.where(RiskEvaluationModel.desired_trade_status == desired_trade_status)
            models = session.scalars(
                query.order_by(RiskEvaluationModel.evaluated_at.desc()).limit(limit)
            ).all()
        return [self._risk_evaluation_from_model(model) for model in models]

    async def get_kill_switch_state(self) -> bool:
        return not self.settings.risk.trading_enabled

    async def _evaluate_desired_trade_internal(
        self,
        desired_trade: MandateDesiredTrade,
        *,
        decision: StrategyDecisionModel | None,
    ) -> RiskEvaluation:
        with self._session_factory() as session:
            decision_model = decision or (
                self._load_decision_model(session, desired_trade.source_decision_ids[0])
                if desired_trade.source_decision_ids
                else None
            )
            source_policy = self._load_source_policy(
                session,
                desired_trade.strategy_mandate_ref_id or (decision_model.strategy_mandate_ref_id if decision_model else None),
            )
            instrument_model = (
                session.get(InstrumentModel, desired_trade.instrument_ref_id)
                if desired_trade.instrument_ref_id is not None
                else None
            )
            desired_trade_model = self._load_desired_trade_model(session, desired_trade.desired_trade_key)
            position = self._load_bound_position(
                session,
                instrument_ref_id=desired_trade.instrument_ref_id,
                venue_account_ref_id=desired_trade.venue_account_ref_id,
            )
            account_snapshot = self._latest_account_snapshot(session, desired_trade.venue_account_ref_id)

        if desired_trade_model is None:
            raise ValueError(f"Desired trade not found: {desired_trade.desired_trade_key}")

        policy_checks: dict[str, object] = {
            "phase_boundary": "phase_4_1",
            "source_policy_ref_id": source_policy.id if source_policy is not None else None,
            "planning_source_venue": desired_trade.planning_source_venue,
            "runtime_exchange_matches_source": (
                source_policy.source_venue == self.settings.exchange.venue if source_policy is not None else None
            ),
            "global_trading_enabled": self.settings.risk.trading_enabled,
            "target_scope": desired_trade.target_scope.value,
        }

        if not self.settings.risk.trading_enabled:
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="global_trading_disabled",
                message="Global risk trading toggle is disabled.",
            )
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                reason_code="global_trading_disabled",
                message="Global risk trading toggle is disabled.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if source_policy is None:
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="market_data_source_policy_missing",
                message="Desired trade cannot be approved without a mandate market-data source policy.",
            )
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.INVALID_INPUT,
                reason_code="market_data_source_policy_missing",
                message="Desired trade cannot be approved without a mandate market-data source policy.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if (
            self.settings.risk.reject_on_source_policy_runtime_mismatch
            and source_policy.source_venue != self.settings.exchange.venue
        ):
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="planning_source_runtime_mismatch",
                message=(
                    "The mandate planning source venue does not match the active runtime exchange adapter, "
                    "so approval stops before child-intent preparation."
                ),
            )
            policy_checks["source_policy_runtime_mismatch"] = True
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.INVALID_INPUT,
                reason_code="planning_source_runtime_mismatch",
                message=(
                    "The mandate planning source venue does not match the active runtime exchange adapter, "
                    "so approval stops before child-intent preparation."
                ),
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if desired_trade.instrument_key is None or desired_trade.instrument_ref_id is None or instrument_model is None:
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="instrument_identity_missing",
                message="Desired-trade approval requires canonical instrument identity.",
            )
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.INVALID_INPUT,
                reason_code="instrument_identity_missing",
                message="Desired-trade approval requires canonical instrument identity.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if source_policy.market_type is not None and instrument_model.market_type != source_policy.market_type:
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="source_policy_market_type_mismatch",
                message="Desired trade instrument does not satisfy the mandate source-policy market type.",
            )
            policy_checks["source_policy_market_type_mismatch"] = True
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.INVALID_INPUT,
                reason_code="source_policy_market_type_mismatch",
                message="Desired trade instrument does not satisfy the mandate source-policy market type.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if source_policy.product_type is not None and instrument_model.product_type != source_policy.product_type:
            desired_trade = self._mark_rejected(
                desired_trade,
                reason_code="source_policy_product_type_mismatch",
                message="Desired trade instrument does not satisfy the mandate source-policy product type.",
            )
            policy_checks["source_policy_product_type_mismatch"] = True
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.INVALID_INPUT,
                reason_code="source_policy_product_type_mismatch",
                message="Desired trade instrument does not satisfy the mandate source-policy product type.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if desired_trade.target_scope == TradeTargetScope.MANDATE and desired_trade.action == DecisionAction.OPEN:
            candidates = await self.planning_service.list_routing_candidates(
                instrument_key=desired_trade.instrument_key,
                component_key=desired_trade.component_key,
                mandate_key=desired_trade.mandate_key,
            )
            eligible_candidates = [
                candidate
                for candidate in candidates
                if self._candidate_supports_instrument(candidate, instrument_model)
                and not self._mandate_open_blockers(candidate)
            ]
            policy_checks["candidate_count"] = len(candidates)
            policy_checks["eligible_candidate_keys"] = [candidate.binding_key for candidate in eligible_candidates]
            if not eligible_candidates:
                desired_trade = self._mark_rejected(
                    desired_trade,
                    reason_code="no_eligible_routing_candidates",
                    message="No eligible binding candidates are available for later routing.",
                )
                return self._persist_risk_evaluation(
                    desired_trade=desired_trade,
                    desired_trade_model=desired_trade_model,
                    decision=decision_model,
                    outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                    reason_code="no_eligible_routing_candidates",
                    message="No eligible binding candidates are available for later routing.",
                    policy_checks=policy_checks,
                    position=position,
                    account_snapshot=account_snapshot,
                    child_intent=None,
                )

            desired_trade.status = MandateDesiredTradeStatus.ROUTING_REQUIRED
            desired_trade.status_reason_code = "routing_required_target_not_selected"
            desired_trade.status_message = (
                "Risk approved the mandate-level desired trade, but routing is required before any child intent can exist."
            )
            desired_trade.approved_at = _utcnow()
            desired_trade.rejected_at = None
            desired_trade.provenance = {
                **dict(desired_trade.provenance),
                "phase_boundary": "phase_4_1",
                "routing_required_candidate_count": len(eligible_candidates),
            }
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=desired_trade_model,
                decision=decision_model,
                outcome=RiskEvaluationOutcome.ROUTING_REQUIRED,
                reason_code="routing_required_target_not_selected",
                message=desired_trade.status_message,
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=None,
            )

        if desired_trade.target_scope == TradeTargetScope.BINDING and desired_trade.action in {
            DecisionAction.REDUCE,
            DecisionAction.CLOSE,
        }:
            candidate = await self._binding_candidate_for_trade(desired_trade)
            if candidate is None:
                desired_trade = self._mark_rejected(
                    desired_trade,
                    reason_code="binding_candidate_not_found",
                    message="Binding-scoped desired trade cannot be approved without a binding candidate.",
                )
                return self._persist_risk_evaluation(
                    desired_trade=desired_trade,
                    desired_trade_model=desired_trade_model,
                    decision=decision_model,
                    outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                    reason_code="binding_candidate_not_found",
                    message="Binding-scoped desired trade cannot be approved without a binding candidate.",
                    policy_checks=policy_checks,
                    position=position,
                    account_snapshot=account_snapshot,
                    child_intent=None,
                )

            blocker_reasons = self._binding_action_blockers(candidate, instrument_model)
            policy_checks["candidate_binding_key"] = candidate.binding_key
            policy_checks["candidate_blockers"] = blocker_reasons
            policy_checks["candidate_eligibility_reasons"] = list(candidate.eligibility_reasons)
            if position is None:
                blocker_reasons.append("open_position_required")
            if blocker_reasons:
                desired_trade = self._mark_rejected(
                    desired_trade,
                    reason_code=blocker_reasons[0],
                    message="Binding-scoped desired trade failed account/policy checks.",
                )
                return self._persist_risk_evaluation(
                    desired_trade=desired_trade,
                    desired_trade_model=desired_trade_model,
                    decision=decision_model,
                    outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                    reason_code=blocker_reasons[0],
                    message="Binding-scoped desired trade failed account/policy checks.",
                    policy_checks=policy_checks,
                    position=position,
                    account_snapshot=account_snapshot,
                    child_intent=None,
                )

            assert position is not None
            desired_quantity = self._determine_binding_quantity(
                action=desired_trade.action,
                position=position,
                binding_key=desired_trade.binding_key,
                component_key=desired_trade.component_key,
                instrument_ref_id=desired_trade.instrument_ref_id,
                venue=candidate.venue,
            )
            if desired_quantity is None or desired_quantity <= Decimal("0"):
                desired_trade = self._mark_rejected(
                    desired_trade,
                    reason_code="child_intent_quantity_invalid",
                    message="Binding-scoped desired trade could not derive a positive child-intent quantity.",
                )
                return self._persist_risk_evaluation(
                    desired_trade=desired_trade,
                    desired_trade_model=desired_trade_model,
                    decision=decision_model,
                    outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                    reason_code="child_intent_quantity_invalid",
                    message="Binding-scoped desired trade could not derive a positive child-intent quantity.",
                    policy_checks=policy_checks,
                    position=position,
                    account_snapshot=account_snapshot,
                    child_intent=None,
                )

            desired_trade.desired_quantity = desired_quantity
            desired_trade.side = self._position_reduction_side(position)
            desired_trade.status = MandateDesiredTradeStatus.APPROVED
            desired_trade.status_reason_code = "binding_target_known"
            desired_trade.status_message = (
                "Risk approved the binding-scoped desired trade and prepared a child intent for the known account target."
            )
            desired_trade.approved_at = _utcnow()
            desired_trade.rejected_at = None
            desired_trade.provenance = {
                **dict(desired_trade.provenance),
                "phase_boundary": "phase_4_1",
                "binding_target_known": True,
                "execution_submission_deferred": True,
            }
            desired_trade = self._persist_desired_trade_state(desired_trade)
            try:
                child_intent = await self.execution_service.create_child_intent(desired_trade, candidate)
            except ChildIntentPreparationError as exc:
                preview = exc.preview
                desired_trade = self._mark_rejected(
                    desired_trade,
                    reason_code=preview.reason_codes[0] if preview.reason_codes else "child_intent_not_preparable",
                    message="Binding-scoped desired trade could not be transformed into a venue-native prepared child intent.",
                )
                policy_checks["child_intent_preflight_reason_codes"] = list(preview.reason_codes)
                policy_checks["child_intent_preview_status"] = preview.preview_status.value
                return self._persist_risk_evaluation(
                    desired_trade=desired_trade,
                    desired_trade_model=self._load_desired_trade_model_by_ref(desired_trade.desired_trade_ref_id),
                    decision=decision_model,
                    outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
                    reason_code=preview.reason_codes[0] if preview.reason_codes else "child_intent_not_preparable",
                    message=(
                        "Binding-scoped desired trade failed venue-native child-intent preparation preflight."
                    ),
                    policy_checks=policy_checks,
                    position=position,
                    account_snapshot=account_snapshot,
                    child_intent=None,
                )
            policy_checks["prepared_child_intent"] = child_intent.intent_id
            return self._persist_risk_evaluation(
                desired_trade=desired_trade,
                desired_trade_model=self._load_desired_trade_model_by_ref(desired_trade.desired_trade_ref_id),
                decision=decision_model,
                outcome=RiskEvaluationOutcome.APPROVED_DESIRED_TRADE,
                reason_code="child_intent_prepared",
                message="Risk approved the binding-scoped desired trade and prepared a child intent.",
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=child_intent,
            )

        desired_trade = self._mark_rejected(
            desired_trade,
            reason_code="action_not_supported_for_phase_4_1",
            message=f"Desired-trade approval is not implemented for action: {desired_trade.action.value}.",
        )
        return self._persist_risk_evaluation(
            desired_trade=desired_trade,
            desired_trade_model=desired_trade_model,
            decision=decision_model,
            outcome=RiskEvaluationOutcome.REJECTED_DESIRED_TRADE,
            reason_code="action_not_supported_for_phase_4_1",
            message=f"Desired-trade approval is not implemented for action: {desired_trade.action.value}.",
            policy_checks=policy_checks,
            position=position,
            account_snapshot=account_snapshot,
            child_intent=None,
        )

    async def _binding_candidate_for_trade(
        self,
        desired_trade: MandateDesiredTrade,
    ) -> BindingRoutingCandidate | None:
        if desired_trade.instrument_key is None:
            return None
        candidates = await self.planning_service.list_routing_candidates(
            instrument_key=desired_trade.instrument_key,
            component_key=desired_trade.component_key,
            mandate_key=desired_trade.mandate_key,
        )
        return next(
            (candidate for candidate in candidates if candidate.binding_key == desired_trade.binding_key),
            None,
        )

    def _persist_no_desired_trade_evaluation(
        self,
        *,
        decision: StrategyDecisionModel,
        source_policy: Any,
        instrument_key: str | None,
        reason_code: str,
        message: str,
        outcome: RiskEvaluationOutcome,
        position: PositionModel | None,
    ) -> RiskEvaluation:
        policy_checks = {
            "phase_boundary": "phase_4_1",
            "convertible": False,
            "source_policy_ref_id": source_policy.id if source_policy is not None else None,
            "planning_source_venue": source_policy.source_venue if source_policy is not None else None,
        }
        with self._session_factory() as session:
            model = self._upsert_risk_evaluation_model(
                session,
                decision=decision,
                desired_trade=None,
                outcome=outcome,
                reason_code=reason_code,
                message=message,
                policy_checks=policy_checks,
                position=position,
                account_snapshot=None,
                child_intent=None,
                instrument_key=instrument_key,
                planning_source_venue=source_policy.source_venue if source_policy is not None else None,
                market_data_source_policy_ref_id=source_policy.id if source_policy is not None else None,
            )
            session.commit()
            return self._risk_evaluation_from_model(model)

    def _persist_risk_evaluation(
        self,
        *,
        desired_trade: MandateDesiredTrade,
        desired_trade_model: MandateDesiredTradeModel | None,
        decision: StrategyDecisionModel | None,
        outcome: RiskEvaluationOutcome,
        reason_code: str | None,
        message: str,
        policy_checks: dict[str, object],
        position: PositionModel | None,
        account_snapshot: ExchangeAccountSnapshotModel | None,
        child_intent: Any,
    ) -> RiskEvaluation:
        desired_trade = self._persist_desired_trade_state(desired_trade)
        with self._session_factory() as session:
            refreshed_trade_model = self._load_desired_trade_model(session, desired_trade.desired_trade_key)
            model = self._upsert_risk_evaluation_model(
                session,
                decision=decision,
                desired_trade=desired_trade,
                desired_trade_model=refreshed_trade_model or desired_trade_model,
                outcome=outcome,
                reason_code=reason_code,
                message=message,
                policy_checks=policy_checks,
                position=position,
                account_snapshot=account_snapshot,
                child_intent=child_intent,
                instrument_key=desired_trade.instrument_key,
                planning_source_venue=desired_trade.planning_source_venue,
                market_data_source_policy_ref_id=desired_trade.market_data_source_policy_ref_id,
            )
            session.commit()
            return self._risk_evaluation_from_model(model)

    def _persist_desired_trade_state(self, desired_trade: MandateDesiredTrade) -> MandateDesiredTrade:
        with self._session_factory() as session:
            model = self._load_desired_trade_model(session, desired_trade.desired_trade_key)
            if model is None:
                raise ValueError(f"Desired trade not found: {desired_trade.desired_trade_key}")
            model.evaluated_state_fingerprint = desired_trade.evaluated_state_fingerprint
            model.market_data_source_policy_ref_id = desired_trade.market_data_source_policy_ref_id
            model.planning_source_venue = desired_trade.planning_source_venue
            model.planning_source_mode = desired_trade.planning_source_mode
            model.planning_as_of = desired_trade.planning_as_of
            model.target_scope = desired_trade.target_scope
            model.mandate_account_binding_ref_id = desired_trade.mandate_account_binding_ref_id
            model.binding_key = desired_trade.binding_key
            model.venue_account_ref_id = desired_trade.venue_account_ref_id
            model.component_key = desired_trade.component_key
            model.instrument_key = desired_trade.instrument_key
            model.instrument_ref_id = desired_trade.instrument_ref_id
            model.symbol = desired_trade.symbol
            model.action = desired_trade.action
            model.side = desired_trade.side
            model.desired_quantity = desired_trade.desired_quantity
            model.desired_notional = desired_trade.desired_notional
            model.source_decision_ids_json = list(desired_trade.source_decision_ids)
            model.source_evaluation_keys_json = list(desired_trade.source_evaluation_keys)
            model.source_binding_keys_json = list(desired_trade.source_binding_keys)
            model.status = desired_trade.status
            model.status_reason_code = desired_trade.status_reason_code
            model.status_message = desired_trade.status_message
            model.provenance = dict(desired_trade.provenance)
            model.approved_at = desired_trade.approved_at
            model.rejected_at = desired_trade.rejected_at
            session.commit()
            desired_trade.desired_trade_ref_id = model.id
            return desired_trade

    def _upsert_risk_evaluation_model(
        self,
        session: Any,
        *,
        decision: StrategyDecisionModel | None,
        desired_trade: MandateDesiredTrade | None,
        desired_trade_model: MandateDesiredTradeModel | None = None,
        outcome: RiskEvaluationOutcome,
        reason_code: str | None,
        message: str,
        policy_checks: dict[str, object],
        position: PositionModel | None,
        account_snapshot: ExchangeAccountSnapshotModel | None,
        child_intent: Any,
        instrument_key: str | None,
        planning_source_venue: str | None,
        market_data_source_policy_ref_id: str | None,
    ) -> RiskEvaluationModel:
        evaluated_at = _utcnow()
        risk_evaluation_key = _json_fingerprint(
            {
                "environment": self.settings.app.environment.value,
                "decision_id": decision.decision_id if decision is not None else None,
                "decision_evaluation_key": decision.evaluation_key if decision is not None else None,
                "desired_trade_key": desired_trade.desired_trade_key if desired_trade is not None else None,
                "desired_trade_status": desired_trade.status.value if desired_trade is not None else None,
                "outcome": outcome.value,
                "reason_code": reason_code,
                "binding_key": desired_trade.binding_key if desired_trade is not None else None,
                "venue_account_ref_id": desired_trade.venue_account_ref_id if desired_trade is not None else None,
                "instrument_key": instrument_key,
                "position": {
                    "position_id": position.position_id if position is not None else None,
                    "quantity": str(position.quantity) if position is not None else None,
                    "status": position.status.value if position is not None else None,
                    "updated_at": position.updated_at.isoformat() if position is not None else None,
                },
                "account_snapshot": {
                    "observed_at": (
                        account_snapshot.observed_at.isoformat() if account_snapshot is not None else None
                    ),
                    "available_balance": (
                        str(account_snapshot.available_balance) if account_snapshot is not None else None
                    ),
                },
                "child_intent_id": child_intent.intent_id if child_intent is not None else None,
                "policy_checks": policy_checks,
                "source_policy_ref_id": market_data_source_policy_ref_id,
                "planning_source_venue": planning_source_venue,
            }
        )
        model = session.scalar(
            select(RiskEvaluationModel).where(RiskEvaluationModel.risk_evaluation_key == risk_evaluation_key)
        )
        if model is None:
            model = RiskEvaluationModel(
                environment=self.settings.app.environment,
                risk_evaluation_id=f"risk-eval-{risk_evaluation_key[:24]}",
                risk_evaluation_key=risk_evaluation_key,
                decision_id=decision.decision_id if decision is not None else "",
                decision_evaluation_key=decision.evaluation_key if decision is not None else None,
                client_ref_id=(
                    desired_trade.client_ref_id
                    if desired_trade is not None
                    else (decision.client_ref_id if decision is not None else None)
                ),
                strategy_mandate_ref_id=(
                    desired_trade.strategy_mandate_ref_id
                    if desired_trade is not None
                    else (decision.strategy_mandate_ref_id if decision is not None else None)
                ),
                mandate_key=desired_trade.mandate_key if desired_trade is not None else (decision.mandate_key if decision else None),
                market_data_source_policy_ref_id=market_data_source_policy_ref_id,
                planning_source_venue=planning_source_venue,
                component_key=desired_trade.component_key if desired_trade is not None else (decision.component_key if decision else None),
                target_scope=desired_trade.target_scope if desired_trade is not None else None,
                mandate_account_binding_ref_id=(
                    desired_trade.mandate_account_binding_ref_id
                    if desired_trade is not None
                    else (decision.mandate_account_binding_ref_id if decision else None)
                ),
                binding_key=desired_trade.binding_key if desired_trade is not None else (decision.binding_key if decision else None),
                venue_account_ref_id=(
                    desired_trade.venue_account_ref_id
                    if desired_trade is not None
                    else (decision.venue_account_ref_id if decision else None)
                ),
                instrument_key=instrument_key,
                instrument_ref_id=(
                    desired_trade.instrument_ref_id
                    if desired_trade is not None
                    else (decision.instrument_ref_id if decision else None)
                ),
                symbol=desired_trade.symbol if desired_trade is not None else (decision.symbol if decision else ""),
                action=desired_trade.action if desired_trade is not None else decision.action,
                decision_status=decision.status if decision is not None else StrategyDecisionStatus.PROPOSED,
                outcome=outcome,
                reason_code=reason_code,
                message=message,
                desired_trade_ref_id=desired_trade_model.id if desired_trade_model is not None else None,
                desired_trade_key=desired_trade.desired_trade_key if desired_trade is not None else None,
                desired_trade_status=desired_trade.status if desired_trade is not None else None,
                child_intent_ref_id=None,
                child_intent_id=None,
                child_intent_status=None,
                policy_checks=dict(policy_checks),
                provenance={
                    "phase_boundary": "phase_4_1",
                    "source_decision_ids": list(desired_trade.source_decision_ids) if desired_trade else [],
                    "source_evaluation_keys": (
                        list(desired_trade.source_evaluation_keys) if desired_trade else []
                    ),
                    "source_binding_keys": list(desired_trade.source_binding_keys) if desired_trade else [],
                },
                evaluated_at=evaluated_at,
            )
            session.add(model)
            session.flush()
        model.decision_id = decision.decision_id if decision is not None else model.decision_id
        model.decision_evaluation_key = decision.evaluation_key if decision is not None else model.decision_evaluation_key
        model.client_ref_id = (
            desired_trade.client_ref_id
            if desired_trade is not None
            else (decision.client_ref_id if decision is not None else model.client_ref_id)
        )
        model.strategy_mandate_ref_id = (
            desired_trade.strategy_mandate_ref_id
            if desired_trade is not None
            else (decision.strategy_mandate_ref_id if decision is not None else model.strategy_mandate_ref_id)
        )
        model.mandate_key = desired_trade.mandate_key if desired_trade is not None else model.mandate_key
        model.market_data_source_policy_ref_id = market_data_source_policy_ref_id
        model.planning_source_venue = planning_source_venue
        model.component_key = desired_trade.component_key if desired_trade is not None else model.component_key
        model.target_scope = desired_trade.target_scope if desired_trade is not None else model.target_scope
        model.mandate_account_binding_ref_id = (
            desired_trade.mandate_account_binding_ref_id
            if desired_trade is not None
            else model.mandate_account_binding_ref_id
        )
        model.binding_key = desired_trade.binding_key if desired_trade is not None else model.binding_key
        model.venue_account_ref_id = desired_trade.venue_account_ref_id if desired_trade is not None else model.venue_account_ref_id
        model.instrument_key = instrument_key
        model.instrument_ref_id = (
            desired_trade.instrument_ref_id
            if desired_trade is not None
            else (decision.instrument_ref_id if decision is not None else model.instrument_ref_id)
        )
        model.symbol = desired_trade.symbol if desired_trade is not None else model.symbol
        model.action = desired_trade.action if desired_trade is not None else model.action
        model.decision_status = decision.status if decision is not None else model.decision_status
        model.outcome = outcome
        model.reason_code = reason_code
        model.message = message
        model.desired_trade_ref_id = desired_trade_model.id if desired_trade_model is not None else None
        model.desired_trade_key = desired_trade.desired_trade_key if desired_trade is not None else None
        model.desired_trade_status = desired_trade.status if desired_trade is not None else None
        model.child_intent_ref_id = None
        model.child_intent_id = None
        model.child_intent_status = None
        if child_intent is not None:
            intent_model = session.scalar(
                select(OrderIntentModel).where(OrderIntentModel.intent_id == child_intent.intent_id)
            )
            model.child_intent_ref_id = intent_model.id if intent_model is not None else None
            model.child_intent_id = child_intent.intent_id
            model.child_intent_status = child_intent.status
        model.policy_checks = dict(policy_checks)
        model.provenance = {
            **dict(model.provenance or {}),
            "phase_boundary": "phase_4_1",
            "source_decision_ids": list(desired_trade.source_decision_ids) if desired_trade else [],
            "source_evaluation_keys": list(desired_trade.source_evaluation_keys) if desired_trade else [],
            "source_binding_keys": list(desired_trade.source_binding_keys) if desired_trade else [],
        }
        model.evaluated_at = evaluated_at
        return model

    @staticmethod
    def _candidate_supports_instrument(candidate: BindingRoutingCandidate, instrument: InstrumentModel) -> bool:
        market_type = instrument.market_type
        if market_type == MarketType.SPOT:
            return candidate.venue_capabilities.supports_spot
        if market_type == MarketType.PERPETUAL:
            return candidate.venue_capabilities.supports_perpetuals
        if market_type == MarketType.FUTURE:
            return candidate.venue_capabilities.supports_futures
        if market_type == MarketType.OPTION:
            return candidate.venue_capabilities.supports_options
        return False

    @staticmethod
    def _mandate_open_blockers(candidate: BindingRoutingCandidate) -> list[str]:
        blockers: list[str] = []
        reason_set = set(candidate.eligibility_reasons)
        for reason in (
            "binding_disabled",
            "binding_strategy_ineligible",
            "binding_routing_ineligible",
            "binding_trading_disabled",
            "component_not_bound",
            "component_disabled",
            "instrument_unavailable_on_venue",
            "symbol_not_strategy_eligible",
            "symbol_not_trading_eligible",
            "account_identifier_missing",
        ):
            if reason in reason_set:
                blockers.append(reason)
        return blockers

    @staticmethod
    def _binding_action_blockers(
        candidate: BindingRoutingCandidate,
        instrument: InstrumentModel,
    ) -> list[str]:
        blockers: list[str] = []
        reason_set = set(candidate.eligibility_reasons)
        for reason in (
            "binding_disabled",
            "binding_strategy_ineligible",
            "binding_trading_disabled",
            "component_not_bound",
            "component_disabled",
            "instrument_unavailable_on_venue",
            "symbol_not_strategy_eligible",
            "symbol_not_trading_eligible",
            "account_identifier_missing",
        ):
            if reason in reason_set:
                blockers.append(reason)
        if not DefaultRiskEngine._candidate_supports_instrument(candidate, instrument):
            blockers.append("venue_capability_market_type_unsupported")
        return blockers

    def _determine_binding_quantity(
        self,
        *,
        action: DecisionAction,
        position: PositionModel,
        binding_key: str | None,
        component_key: str | None,
        instrument_ref_id: str | None,
        venue: str,
    ) -> Decimal | None:
        position_qty = _position_quantity(position)
        if position_qty <= Decimal("0"):
            return None
        with self._session_factory() as session:
            symbol_model = session.scalar(
                select(SymbolModel).where(
                    SymbolModel.instrument_ref_id == instrument_ref_id,
                    SymbolModel.venue == venue,
                )
            )
            step_size = symbol_model.quantity_step_size if symbol_model is not None else None
            component = None
            if binding_key is not None and component_key is not None:
                component = session.scalar(
                    select(StrategyComponentConfigModel).where(
                        StrategyComponentConfigModel.binding_scope_key == binding_key,
                        StrategyComponentConfigModel.component_key == component_key,
                    )
                )
            reduce_fraction = self.settings.risk.binding_reduce_fraction
            if component is not None:
                payload = dict(component.parameters_json or {})
                if "reduce_fraction" in payload:
                    reduce_fraction = float(payload["reduce_fraction"])

        if action == DecisionAction.CLOSE:
            return self._apply_step(position_qty, step_size)
        if action == DecisionAction.REDUCE:
            raw_qty = position_qty * Decimal(str(max(min(reduce_fraction, 1.0), 0.0)))
            return self._apply_step(raw_qty, step_size)
        return None

    @staticmethod
    def _apply_step(quantity: Decimal, step_size: Decimal | None) -> Decimal:
        if step_size is None or step_size <= Decimal("0"):
            return quantity
        steps = (quantity / step_size).to_integral_value(rounding=ROUND_DOWN)
        return (steps * step_size).normalize()

    @staticmethod
    def _position_reduction_side(position: PositionModel) -> OrderSide:
        return OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY

    @staticmethod
    def _mark_rejected(
        desired_trade: MandateDesiredTrade,
        *,
        reason_code: str,
        message: str,
    ) -> MandateDesiredTrade:
        desired_trade.status = MandateDesiredTradeStatus.REJECTED
        desired_trade.status_reason_code = reason_code
        desired_trade.status_message = message
        desired_trade.rejected_at = _utcnow()
        desired_trade.approved_at = None
        desired_trade.provenance = {
            **dict(desired_trade.provenance),
            "phase_boundary": "phase_4_1",
            "last_rejection_reason_code": reason_code,
        }
        return desired_trade

    @staticmethod
    def _load_decision_model(session: Any, decision_id: str) -> StrategyDecisionModel:
        decision = session.scalar(
            select(StrategyDecisionModel).where(StrategyDecisionModel.decision_id == decision_id)
        )
        if decision is None:
            raise ValueError(f"Strategy decision not found: {decision_id}")
        return decision

    @staticmethod
    def _load_source_policy(session: Any, strategy_mandate_ref_id: str | None):
        from db.models import MandateMarketDataSourcePolicyModel

        if strategy_mandate_ref_id is None:
            return None
        return session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == strategy_mandate_ref_id
            )
        )

    @staticmethod
    def _lookup_instrument_key(session: Any, instrument_ref_id: str | None) -> str | None:
        if instrument_ref_id is None:
            return None
        return session.scalar(select(InstrumentModel.instrument_key).where(InstrumentModel.id == instrument_ref_id))

    def _load_bound_position(
        self,
        session: Any,
        *,
        instrument_ref_id: str | None,
        venue_account_ref_id: str | None,
    ) -> PositionModel | None:
        if instrument_ref_id is None or venue_account_ref_id is None:
            return None
        return session.scalar(
            select(PositionModel).where(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.instrument_ref_id == instrument_ref_id,
                PositionModel.venue_account_ref_id == venue_account_ref_id,
                PositionModel.status == PositionStatus.OPEN,
            )
        )

    @staticmethod
    def _load_desired_trade_model(session: Any, desired_trade_key: str | None) -> MandateDesiredTradeModel | None:
        if desired_trade_key is None:
            return None
        return session.scalar(
            select(MandateDesiredTradeModel).where(MandateDesiredTradeModel.desired_trade_key == desired_trade_key)
        )

    def _load_desired_trade_model_by_ref(self, desired_trade_ref_id: str | None) -> MandateDesiredTradeModel | None:
        if desired_trade_ref_id is None:
            return None
        with self._session_factory() as session:
            return session.get(MandateDesiredTradeModel, desired_trade_ref_id)

    def _latest_account_snapshot(
        self,
        session: Any,
        venue_account_ref_id: str | None,
    ) -> ExchangeAccountSnapshotModel | None:
        if venue_account_ref_id is None:
            return None
        return session.scalar(
            select(ExchangeAccountSnapshotModel)
            .where(
                ExchangeAccountSnapshotModel.environment == self.settings.app.environment,
                ExchangeAccountSnapshotModel.venue_account_ref_id == venue_account_ref_id,
            )
            .order_by(ExchangeAccountSnapshotModel.observed_at.desc())
        )

    @staticmethod
    def _risk_evaluation_from_model(model: RiskEvaluationModel) -> RiskEvaluation:
        return RiskEvaluation(
            risk_evaluation_id=model.risk_evaluation_id,
            risk_evaluation_key=model.risk_evaluation_key,
            environment=model.environment,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            market_data_source_policy_ref_id=model.market_data_source_policy_ref_id,
            planning_source_venue=model.planning_source_venue,
            decision_id=model.decision_id,
            decision_evaluation_key=model.decision_evaluation_key,
            component_key=model.component_key,
            target_scope=model.target_scope,
            mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
            binding_key=model.binding_key,
            venue_account_ref_id=model.venue_account_ref_id,
            instrument_key=model.instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            action=model.action,
            decision_status=model.decision_status,
            outcome=model.outcome,
            reason_code=model.reason_code,
            message=model.message,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            desired_trade_status=model.desired_trade_status,
            child_intent_ref_id=model.child_intent_ref_id,
            child_intent_id=model.child_intent_id,
            child_intent_status=model.child_intent_status,
            policy_checks=dict(model.policy_checks or {}),
            provenance=dict(model.provenance or {}),
            evaluated_at=model.evaluated_at,
        )


GlobalRiskEngine = DefaultRiskEngine
