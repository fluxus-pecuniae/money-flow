"""Non-executing routing assessment and target-choice substrate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    DecisionAction,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    RouteReadinessAuditStatus,
    RoutingAssessmentDecisionStatus,
    RoutingCandidateEligibilityStatus,
    RoutingTargetRecommendationStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    TradeTargetScope,
)
from core.domain.models import (
    BindingRoutingCandidate,
    MandateDesiredTrade,
    OrderIntent,
    RouteReadinessAudit,
    RouteReadinessCandidateAudit,
    RoutingAssessment,
    RoutingCandidateAssessment,
    RoutingRequest,
    RoutingTargetRecommendation,
    RoutingTargetChoice,
    RoutingTargetChoiceConversionResult,
    RoutedOrderShapePolicyInput,
)
from core.interfaces.services import MandateTradePlanningService, RoutingAssessmentService
from db.models import (
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    ExchangeAccountSnapshotModel,
    InstrumentModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RouteReadinessCandidateAuditModel,
    RoutingAssessmentCandidateModel,
    RoutingAssessmentModel,
    RoutingTargetRecommendationModel,
    RoutingTargetChoiceModel,
    StrategyMandateModel,
    SymbolModel,
    VenueAccountModel,
)
from db.session import SessionLocal
from services.planning.service import DefaultTradePlanningService


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class RoutingAssessmentError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


_REASON_CODE_MAP = {
    "binding_routing_ineligible": "binding_not_routing_eligible",
    "instrument_unavailable_on_venue": "missing_symbol_mapping",
    "account_identifier_missing": "venue_account_identifier_missing",
    "quote_unavailable": "missing_quote_snapshot",
}

_MISSING_DATA_REASONS = {"quote_unavailable"}

_NON_BLOCKING_TARGET_CHOICE_REASONS = {
    "target_choice_recorded",
    "target_choice_non_executing",
    "routing_target_recommendation_accepted",
    "routing_target_choice_from_recommendation",
    "child_intent_conversion_deferred",
}

_ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS = 60
_ROUTING_TARGET_RECOMMENDATION_POLICY = "single_ready_candidate_only"
_ROUTING_TARGET_RECOMMENDATION_PRIORITY_POLICY = "explicit_binding_priority"
_ROUTING_TARGET_RECOMMENDATION_ALLOWED_POLICIES = {
    _ROUTING_TARGET_RECOMMENDATION_POLICY,
    _ROUTING_TARGET_RECOMMENDATION_PRIORITY_POLICY,
}
_ROUTING_TARGET_RECOMMENDATION_POLICY_NAME_MAX_LENGTH = 64
_TARGET_RECOMMENDATION_PRIORITY_MIN = 1
_TARGET_RECOMMENDATION_PRIORITY_MAX = 1_000_000


@dataclass(frozen=True, slots=True)
class RoutedOrderShapeDecision:
    order_type: OrderType
    limit_price: Decimal | None
    reduce_only: bool
    policy_source: str
    requested_order_type: OrderType | None
    requested_limit_price: Decimal | None
    requested_reduce_only: bool | None
    requested_by: str | None
    reason_codes: list[str]
    warnings: list[str]
    blocked: bool = False

    def provenance(self) -> dict[str, object]:
        return {
            "phase": "phase_5_8",
            "policy_scope": "routed_target_choice_conversion_open",
            "policy_source": self.policy_source,
            "requested_order_type": (
                self.requested_order_type.value if self.requested_order_type is not None else None
            ),
            "requested_limit_price": (
                str(self.requested_limit_price) if self.requested_limit_price is not None else None
            ),
            "requested_reduce_only": self.requested_reduce_only,
            "requested_by": self.requested_by,
            "order_type": self.order_type.value,
            "limit_price": str(self.limit_price) if self.limit_price is not None else None,
            "reduce_only": self.reduce_only,
            "reason_codes": list(self.reason_codes),
            "warnings": list(self.warnings),
            "blocked": self.blocked,
            "limit_order_support": "explicit_limit_price_required",
            "slippage_guard_support": "deferred",
        }


class DefaultRoutingAssessmentService(RoutingAssessmentService):
    """Creates persisted routing candidate inventories and non-executing target-choice records."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        planning_service: MandateTradePlanningService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self.planning_service = planning_service or DefaultTradePlanningService(
            self.settings,
            session_factory=session_factory,
        )

    async def create_assessment_from_desired_trade(
        self,
        desired_trade_key: str,
    ) -> RoutingAssessment:
        with self._session_factory() as session:
            desired_model = self._load_desired_trade_model(session, desired_trade_key)
            desired_trade = DefaultTradePlanningService._desired_trade_from_model(desired_model)
            self._validate_desired_trade(desired_trade)

        evaluated_at = _utcnow()
        assessment_id = f"rtassess_{uuid4().hex}"
        request = self._routing_request(desired_trade, evaluated_at=evaluated_at)
        candidates, inventory_reason, inventory_missing = await self._candidate_assessments(
            request,
            desired_trade,
            assessment_id=assessment_id,
            evaluated_at=evaluated_at,
        )
        decision_status = self._decision_status(
            candidates,
            inventory_missing=inventory_missing,
        )
        reason_codes = self._assessment_reason_codes(
            candidates,
            decision_status=decision_status,
            inventory_reason=inventory_reason,
        )
        missing_data = sorted({item for candidate in candidates for item in candidate.missing_data} | set(inventory_missing))
        assessment = RoutingAssessment(
            assessment_id=assessment_id,
            environment=desired_trade.environment,
            desired_trade_ref_id=desired_trade.desired_trade_ref_id,
            desired_trade_key=desired_trade.desired_trade_key,
            client_ref_id=desired_trade.client_ref_id,
            strategy_mandate_ref_id=desired_trade.strategy_mandate_ref_id,
            mandate_key=desired_trade.mandate_key,
            market_data_source_policy_ref_id=desired_trade.market_data_source_policy_ref_id,
            planning_source_venue=desired_trade.planning_source_venue,
            instrument_key=desired_trade.instrument_key,
            instrument_ref_id=desired_trade.instrument_ref_id,
            symbol=desired_trade.symbol,
            action=desired_trade.action,
            target_scope=desired_trade.target_scope,
            decision_status=decision_status,
            eligible_binding_count=sum(
                1
                for candidate in candidates
                if candidate.eligibility_status
                == RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
            ),
            ineligible_binding_count=sum(
                1
                for candidate in candidates
                if candidate.eligibility_status
                == RoutingCandidateEligibilityStatus.INELIGIBLE_FOR_FUTURE_SELECTION
            ),
            request=request,
            candidates=candidates,
            reason_codes=reason_codes,
            missing_data=missing_data,
            evaluated_at=evaluated_at,
            provenance={
                "phase": "phase_5_0",
                "boundary": "routing_assessment_only",
                "non_executing": True,
                "child_intents_created": False,
                "target_choice_created": False,
                "target_choice_requires_explicit_operator_request": True,
            },
        )
        return self._persist_assessment(assessment)

    async def get_routing_assessment(self, assessment_id: str) -> RoutingAssessment:
        with self._session_factory() as session:
            model = session.scalar(
                select(RoutingAssessmentModel).where(
                    RoutingAssessmentModel.environment == self.settings.app.environment,
                    RoutingAssessmentModel.assessment_id == assessment_id,
                )
            )
            if model is None:
                raise RoutingAssessmentError(
                    "routing_assessment_not_found",
                    f"Routing assessment not found: {assessment_id}",
                )
            candidate_models = session.scalars(
                select(RoutingAssessmentCandidateModel)
                .where(RoutingAssessmentCandidateModel.assessment_ref_id == model.id)
                .order_by(RoutingAssessmentCandidateModel.binding_key.asc())
            ).all()
            return self._assessment_from_model(model, list(candidate_models))

    async def create_route_readiness_audit_from_desired_trade(
        self,
        desired_trade_key: str,
    ) -> RouteReadinessAudit:
        assessment = await self.create_assessment_from_desired_trade(desired_trade_key)
        return await self.create_route_readiness_audit_from_assessment(assessment.assessment_id)

    async def create_route_readiness_audit_from_assessment(
        self,
        routing_assessment_id: str,
    ) -> RouteReadinessAudit:
        evaluated_at = _utcnow()
        with self._session_factory() as session:
            assessment_model = session.scalar(
                select(RoutingAssessmentModel).where(
                    RoutingAssessmentModel.environment == self.settings.app.environment,
                    RoutingAssessmentModel.assessment_id == routing_assessment_id,
                )
            )
            if assessment_model is None:
                raise RoutingAssessmentError(
                    "routing_assessment_not_found",
                    f"Routing assessment not found: {routing_assessment_id}",
                )
            candidate_models = list(
                session.scalars(
                    select(RoutingAssessmentCandidateModel)
                    .where(RoutingAssessmentCandidateModel.assessment_ref_id == assessment_model.id)
                    .order_by(RoutingAssessmentCandidateModel.binding_key.asc())
                ).all()
            )
            audit = self._build_route_readiness_audit(
                session,
                assessment_model,
                candidate_models,
                evaluated_at=evaluated_at,
            )
            return self._persist_route_readiness_audit(session, audit)

    async def get_route_readiness_audit(self, route_readiness_audit_id: str) -> RouteReadinessAudit:
        with self._session_factory() as session:
            model = session.scalar(
                select(RouteReadinessAuditModel).where(
                    RouteReadinessAuditModel.environment == self.settings.app.environment,
                    RouteReadinessAuditModel.route_readiness_audit_id == route_readiness_audit_id,
                )
            )
            if model is None:
                raise RoutingAssessmentError(
                    "route_readiness_audit_not_found",
                    f"Route-readiness audit not found: {route_readiness_audit_id}",
                )
            candidate_models = list(
                session.scalars(
                    select(RouteReadinessCandidateAuditModel)
                    .where(RouteReadinessCandidateAuditModel.route_readiness_audit_ref_id == model.id)
                    .order_by(RouteReadinessCandidateAuditModel.binding_key.asc())
                ).all()
            )
            return self._route_readiness_audit_from_model(model, candidate_models)

    async def create_routing_target_recommendation_from_route_readiness_audit(
        self,
        route_readiness_audit_id: str,
        *,
        policy_name: str | None = None,
    ) -> RoutingTargetRecommendation:
        created_at = _utcnow()
        requested_policy_name = self._normalize_routing_target_recommendation_policy_name(policy_name)
        with self._session_factory() as session:
            audit_model = session.scalar(
                select(RouteReadinessAuditModel).where(
                    RouteReadinessAuditModel.environment == self.settings.app.environment,
                    RouteReadinessAuditModel.route_readiness_audit_id == route_readiness_audit_id,
                )
            )
            if audit_model is None:
                recommendation = self._routing_target_recommendation_for_missing_audit(
                    route_readiness_audit_id,
                    created_at=created_at,
                    policy_name=requested_policy_name,
                )
                return self._persist_routing_target_recommendation(session, recommendation)
            candidate_models = list(
                session.scalars(
                    select(RouteReadinessCandidateAuditModel)
                    .where(RouteReadinessCandidateAuditModel.route_readiness_audit_ref_id == audit_model.id)
                    .order_by(RouteReadinessCandidateAuditModel.binding_key.asc())
                ).all()
            )
            recommendation = self._build_routing_target_recommendation(
                session,
                audit_model,
                candidate_models,
                created_at=created_at,
                policy_name=requested_policy_name,
            )
            return self._persist_routing_target_recommendation(session, recommendation)

    @staticmethod
    def _normalize_routing_target_recommendation_policy_name(policy_name: str | None) -> str:
        if policy_name is None:
            return _ROUTING_TARGET_RECOMMENDATION_POLICY
        if not isinstance(policy_name, str):
            raise RoutingAssessmentError(
                "routing_target_recommendation_policy_invalid",
                "Recommendation policy_name must be a string.",
            )
        if policy_name == "" or policy_name != policy_name.strip():
            raise RoutingAssessmentError(
                "routing_target_recommendation_policy_invalid",
                "Recommendation policy_name must be non-empty and must not include surrounding whitespace.",
            )
        if len(policy_name) > _ROUTING_TARGET_RECOMMENDATION_POLICY_NAME_MAX_LENGTH:
            raise RoutingAssessmentError(
                "routing_target_recommendation_policy_invalid",
                "Recommendation policy_name exceeds the persisted policy_name length limit.",
            )
        return policy_name

    async def get_routing_target_recommendation(
        self,
        routing_target_recommendation_id: str,
    ) -> RoutingTargetRecommendation:
        with self._session_factory() as session:
            model = session.scalar(
                select(RoutingTargetRecommendationModel).where(
                    RoutingTargetRecommendationModel.environment == self.settings.app.environment,
                    RoutingTargetRecommendationModel.routing_target_recommendation_id
                    == routing_target_recommendation_id,
                )
            )
            if model is None:
                raise RoutingAssessmentError(
                    "routing_target_recommendation_not_found",
                    f"Routing target recommendation not found: {routing_target_recommendation_id}",
                )
            return self._routing_target_recommendation_from_model(model)

    async def accept_routing_target_recommendation_to_target_choice(
        self,
        routing_target_recommendation_id: str,
        *,
        approval_note: str | None = None,
        requested_by: str | None = None,
    ) -> RoutingTargetChoice:
        accepted_at = _utcnow()
        with self._session_factory() as session:
            recommendation_model = session.scalar(
                select(RoutingTargetRecommendationModel).where(
                    RoutingTargetRecommendationModel.environment == self.settings.app.environment,
                    RoutingTargetRecommendationModel.routing_target_recommendation_id
                    == routing_target_recommendation_id,
                )
            )
            if recommendation_model is None:
                raise RoutingAssessmentError(
                    "routing_target_recommendation_not_found",
                    f"Routing target recommendation not found: {routing_target_recommendation_id}",
                )

            existing_choice = self._target_choice_for_recommendation(
                session,
                recommendation_model,
            )
            if existing_choice is not None:
                self._mark_recommendation_target_choice_created(
                    session,
                    recommendation_model,
                    existing_choice,
                    accepted_at=accepted_at,
                    idempotent=True,
                    existing_audit_target_choice=False,
                )
                session.commit()
                return self._target_choice_from_model(existing_choice)

            (
                same_audit_preflight_blockers,
                same_audit_preflight_missing,
            ) = self._recommendation_same_audit_idempotency_preflight_blockers(
                recommendation_model
            )
            if same_audit_preflight_blockers or same_audit_preflight_missing:
                reason_code = (
                    same_audit_preflight_blockers[0]
                    if same_audit_preflight_blockers
                    else same_audit_preflight_missing[0]
                )
                raise RoutingAssessmentError(
                    reason_code,
                    (
                        "Routing target recommendation cannot be accepted into a target choice: "
                        + ", ".join(
                            sorted(
                                set(
                                    same_audit_preflight_blockers
                                    + same_audit_preflight_missing
                                )
                            )
                        )
                    ),
                )

            existing_audit_choice = self._target_choice_for_route_readiness_audit(
                session,
                recommendation_model,
            )
            if existing_audit_choice is not None:
                self._mark_recommendation_target_choice_created(
                    session,
                    recommendation_model,
                    existing_audit_choice,
                    accepted_at=accepted_at,
                    idempotent=True,
                    existing_audit_target_choice=True,
                )
                session.commit()
                return self._target_choice_from_model(existing_audit_choice)

            (
                blockers,
                missing_data,
                audit_model,
                candidate_model,
                assessment_candidate_model,
            ) = self._recommendation_acceptance_blockers(
                session,
                recommendation_model,
                accepted_at=accepted_at,
            )
            if blockers or missing_data:
                reason_code = blockers[0] if blockers else missing_data[0]
                raise RoutingAssessmentError(
                    reason_code,
                    (
                        "Routing target recommendation cannot be accepted into a target choice: "
                        + ", ".join(sorted(set(blockers + missing_data)))
                    ),
                )

            if audit_model is None or candidate_model is None or assessment_candidate_model is None:
                raise RoutingAssessmentError(
                    "routing_target_recommendation_acceptance_invalid",
                    "Routing target recommendation acceptance lacked validated source lineage.",
                )

            choice = self._persist_target_choice(
                session,
                routing_assessment_id=recommendation_model.routing_assessment_id or "",
                routing_assessment_ref_id=recommendation_model.routing_assessment_ref_id,
                desired_trade_ref_id=recommendation_model.desired_trade_ref_id,
                desired_trade_key=recommendation_model.desired_trade_key,
                candidate_model=assessment_candidate_model,
                status=RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED,
                reason_codes=[
                    "target_choice_recorded",
                    "target_choice_non_executing",
                    "routing_target_recommendation_accepted",
                    "routing_target_choice_from_recommendation",
                    "child_intent_conversion_deferred",
                ],
                missing_data=[],
                approval_note=approval_note,
                requested_by=requested_by,
                created_at=accepted_at,
                selected_at=accepted_at,
                provenance_extra={
                    "phase": "phase_6_2",
                    "boundary": "routing_target_recommendation_acceptance_to_target_choice_only",
                    "source": "routing_target_recommendation",
                    "operator_triggered": True,
                    "routing_target_recommendation_id": (
                        recommendation_model.routing_target_recommendation_id
                    ),
                    "route_readiness_audit_id": recommendation_model.route_readiness_audit_id,
                    "routing_assessment_id": recommendation_model.routing_assessment_id,
                    "desired_trade_key": recommendation_model.desired_trade_key,
                    "policy_name": recommendation_model.policy_name,
                    "recommended_binding_ref_id": recommendation_model.recommended_binding_ref_id,
                    "recommended_binding_key": recommendation_model.recommended_binding_key,
                    "recommended_venue_account_ref_id": (
                        recommendation_model.recommended_venue_account_ref_id
                    ),
                    "recommended_venue_account_key": (
                        recommendation_model.recommended_venue_account_key
                    ),
                    "recommended_venue": recommendation_model.recommended_venue,
                    "recommended_exchange_symbol": (
                        recommendation_model.recommended_exchange_symbol
                    ),
                    "accepted_at": accepted_at.isoformat(),
                    "target_choice_created": True,
                    "child_intent_created": False,
                    "prepared_order_created": False,
                    "readiness_assessment_created": False,
                    "submitted_order_created": False,
                    "fanout_created": False,
                    "allocation_created": False,
                },
            )
            choice_model = session.scalar(
                select(RoutingTargetChoiceModel).where(
                    RoutingTargetChoiceModel.environment == self.settings.app.environment,
                    RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
                )
            )
            if choice_model is not None:
                refreshed_recommendation_model = session.scalar(
                    select(RoutingTargetRecommendationModel).where(
                        RoutingTargetRecommendationModel.environment
                        == self.settings.app.environment,
                        RoutingTargetRecommendationModel.routing_target_recommendation_id
                        == routing_target_recommendation_id,
                    )
                )
                if refreshed_recommendation_model is not None:
                    self._mark_recommendation_target_choice_created(
                        session,
                        refreshed_recommendation_model,
                        choice_model,
                        accepted_at=accepted_at,
                        idempotent=False,
                        existing_audit_target_choice=False,
                    )
                    session.commit()
            return choice

    async def record_target_choice_from_assessment(
        self,
        *,
        routing_assessment_id: str,
        binding_ref_id: str | None = None,
        binding_key: str | None = None,
        approval_note: str | None = None,
        requested_by: str | None = None,
    ) -> RoutingTargetChoice:
        created_at = _utcnow()
        with self._session_factory() as session:
            assessment_model = session.scalar(
                select(RoutingAssessmentModel).where(
                    RoutingAssessmentModel.environment == self.settings.app.environment,
                    RoutingAssessmentModel.assessment_id == routing_assessment_id,
                )
            )
            if assessment_model is None:
                return self._persist_target_choice(
                    session,
                    routing_assessment_id=routing_assessment_id,
                    routing_assessment_ref_id=None,
                    desired_trade_ref_id=None,
                    desired_trade_key=None,
                    candidate_model=None,
                    status=RoutingTargetChoiceStatus.BLOCKED_ASSESSMENT_NOT_FOUND,
                    reason_codes=[
                        "routing_assessment_not_found",
                        "target_choice_non_executing",
                        "child_intent_conversion_deferred",
                    ],
                    missing_data=[],
                    approval_note=approval_note,
                    requested_by=requested_by,
                    created_at=created_at,
                )

            blocked_status, blocked_reason = self._assessment_target_choice_blocker(assessment_model)
            if blocked_status is not None:
                return self._persist_target_choice(
                    session,
                    routing_assessment_id=assessment_model.assessment_id,
                    routing_assessment_ref_id=assessment_model.id,
                    desired_trade_ref_id=assessment_model.desired_trade_ref_id,
                    desired_trade_key=assessment_model.desired_trade_key,
                    candidate_model=None,
                    status=blocked_status,
                    reason_codes=[
                        blocked_reason,
                        "target_choice_non_executing",
                        "child_intent_conversion_deferred",
                    ],
                    missing_data=list(assessment_model.missing_data_json or []),
                    approval_note=approval_note,
                    requested_by=requested_by,
                    created_at=created_at,
                )

            candidate_model = self._find_target_choice_candidate(
                session,
                assessment_ref_id=assessment_model.id,
                binding_ref_id=binding_ref_id,
                binding_key=binding_key,
            )
            if candidate_model is None:
                reason_codes = [
                    "routing_candidate_not_found",
                    "target_choice_non_executing",
                    "child_intent_conversion_deferred",
                ]
                if binding_ref_id is None and binding_key is None:
                    reason_codes.insert(0, "routing_candidate_not_specified")
                return self._persist_target_choice(
                    session,
                    routing_assessment_id=assessment_model.assessment_id,
                    routing_assessment_ref_id=assessment_model.id,
                    desired_trade_ref_id=assessment_model.desired_trade_ref_id,
                    desired_trade_key=assessment_model.desired_trade_key,
                    candidate_model=None,
                    status=RoutingTargetChoiceStatus.BLOCKED_CANDIDATE_NOT_FOUND,
                    reason_codes=reason_codes,
                    missing_data=[],
                    approval_note=approval_note,
                    requested_by=requested_by,
                    created_at=created_at,
                )

            candidate_blockers, candidate_missing = self._candidate_target_choice_blockers(candidate_model)
            if candidate_blockers or candidate_missing:
                return self._persist_target_choice(
                    session,
                    routing_assessment_id=assessment_model.assessment_id,
                    routing_assessment_ref_id=assessment_model.id,
                    desired_trade_ref_id=assessment_model.desired_trade_ref_id,
                    desired_trade_key=assessment_model.desired_trade_key,
                    candidate_model=candidate_model,
                    status=RoutingTargetChoiceStatus.BLOCKED_CANDIDATE_INELIGIBLE,
                    reason_codes=sorted(
                        set(
                            candidate_blockers
                            + [
                                "target_choice_non_executing",
                                "child_intent_conversion_deferred",
                            ]
                        )
                    ),
                    missing_data=candidate_missing,
                    approval_note=approval_note,
                    requested_by=requested_by,
                    created_at=created_at,
                )

            stale_reason_codes = sorted(
                set(
                    self._current_desired_trade_target_choice_blockers(session, assessment_model)
                    + self._current_target_truth_blockers(session, candidate_model)
                )
            )
            if stale_reason_codes:
                return self._persist_target_choice(
                    session,
                    routing_assessment_id=assessment_model.assessment_id,
                    routing_assessment_ref_id=assessment_model.id,
                    desired_trade_ref_id=assessment_model.desired_trade_ref_id,
                    desired_trade_key=assessment_model.desired_trade_key,
                    candidate_model=candidate_model,
                    status=RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT,
                    reason_codes=sorted(
                        set(
                            stale_reason_codes
                            + [
                                "target_choice_non_executing",
                                "child_intent_conversion_deferred",
                            ]
                        )
                    ),
                    missing_data=[],
                    approval_note=approval_note,
                    requested_by=requested_by,
                    created_at=created_at,
                )

            return self._persist_target_choice(
                session,
                routing_assessment_id=assessment_model.assessment_id,
                routing_assessment_ref_id=assessment_model.id,
                desired_trade_ref_id=assessment_model.desired_trade_ref_id,
                desired_trade_key=assessment_model.desired_trade_key,
                candidate_model=candidate_model,
                status=RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED,
                reason_codes=[
                    "target_choice_recorded",
                    "target_choice_non_executing",
                    "child_intent_conversion_deferred",
                ],
                missing_data=[],
                approval_note=approval_note,
                requested_by=requested_by,
                created_at=created_at,
                selected_at=created_at,
            )

    async def get_routing_target_choice(self, target_choice_id: str) -> RoutingTargetChoice:
        with self._session_factory() as session:
            model = session.scalar(
                select(RoutingTargetChoiceModel).where(
                    RoutingTargetChoiceModel.environment == self.settings.app.environment,
                    RoutingTargetChoiceModel.target_choice_id == target_choice_id,
                )
            )
            if model is None:
                raise RoutingAssessmentError(
                    "routing_target_choice_not_found",
                    f"Routing target choice not found: {target_choice_id}",
                )
            return self._target_choice_from_model(model)

    async def list_routing_target_choices_for_assessment(
        self,
        routing_assessment_id: str,
    ) -> list[RoutingTargetChoice]:
        with self._session_factory() as session:
            models = session.scalars(
                select(RoutingTargetChoiceModel)
                .where(
                    RoutingTargetChoiceModel.environment == self.settings.app.environment,
                    RoutingTargetChoiceModel.routing_assessment_id == routing_assessment_id,
                )
                .order_by(RoutingTargetChoiceModel.created_at.desc())
            ).all()
            return [self._target_choice_from_model(model) for model in models]

    async def convert_target_choice_to_child_intent(
        self,
        target_choice_id: str,
        order_shape_policy: RoutedOrderShapePolicyInput | None = None,
    ) -> RoutingTargetChoiceConversionResult:
        converted_at = _utcnow()
        with self._session_factory() as session:
            choice_model = session.scalar(
                select(RoutingTargetChoiceModel).where(
                    RoutingTargetChoiceModel.environment == self.settings.app.environment,
                    RoutingTargetChoiceModel.target_choice_id == target_choice_id,
                )
            )
            if choice_model is None:
                return self._conversion_result(
                    target_choice_id=target_choice_id,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_NOT_FOUND,
                    reason_codes=["routing_target_choice_not_found", "conversion_non_submitting"],
                    converted_at=converted_at,
                )

            target_choice_blockers, target_choice_missing = self._target_choice_conversion_blockers(
                choice_model
            )
            if target_choice_blockers or target_choice_missing:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=(
                        RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_NOT_RECORDED
                        if choice_model.status != RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
                        else RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_INCOMPLETE
                    ),
                    reason_codes=target_choice_blockers + ["conversion_non_submitting"],
                    missing_data=target_choice_missing,
                    converted_at=converted_at,
                )

            idempotency_key = self._target_choice_conversion_idempotency_key(choice_model)
            existing_intent = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.idempotency_key == idempotency_key,
                )
            )
            if existing_intent is not None:
                if self._target_choice_is_recommendation_backed(choice_model):
                    recommendation_model = self._load_recommendation_for_target_choice(
                        session,
                        choice_model,
                    )
                    if recommendation_model is not None:
                        self._mark_recommendation_child_intent_created(
                            session,
                            recommendation_model,
                            choice_model,
                            existing_intent,
                            converted_at=converted_at,
                            idempotent=True,
                            existing_audit_child_intent=False,
                        )
                        session.commit()
                existing_policy_mismatch = self._existing_child_intent_policy_mismatch(
                    existing_intent,
                    order_shape_policy,
                )
                reason_codes = [
                    "child_intent_already_exists",
                    "conversion_idempotent",
                    "conversion_non_submitting",
                ]
                if existing_policy_mismatch:
                    reason_codes.extend(
                        [
                            "conversion_order_shape_policy_mismatch",
                            "existing_child_intent_order_shape_preserved",
                        ]
                    )
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS,
                    reason_codes=reason_codes,
                    child_intent=self._order_intent_from_model(existing_intent),
                    converted_at=converted_at,
                    child_intent_reused=True,
                )

            recommendation_model: RoutingTargetRecommendationModel | None = None
            if self._target_choice_is_recommendation_backed(choice_model):
                (
                    recommendation_preflight_blockers,
                    recommendation_preflight_missing,
                    recommendation_model,
                ) = self._recommendation_backed_target_choice_preflight_blockers(
                    session,
                    choice_model,
                )
                if recommendation_preflight_blockers or recommendation_preflight_missing:
                    return self._conversion_result(
                        target_choice_id=choice_model.target_choice_id,
                        routing_assessment_id=choice_model.routing_assessment_id,
                        desired_trade_key=choice_model.desired_trade_key,
                        status=RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_INCOMPLETE,
                        reason_codes=(
                            recommendation_preflight_blockers
                            + ["conversion_non_submitting"]
                        ),
                        missing_data=recommendation_preflight_missing,
                        converted_at=converted_at,
                    )

            existing_related_intent = self._existing_child_intent_for_target_choice_context(
                session,
                choice_model,
                recommendation_model,
                exclude_idempotency_key=idempotency_key,
            )
            if existing_related_intent is not None:
                if recommendation_model is not None:
                    self._mark_recommendation_child_intent_created(
                        session,
                        recommendation_model,
                        choice_model,
                        existing_related_intent,
                        converted_at=converted_at,
                        idempotent=True,
                        existing_audit_child_intent=True,
                    )
                    session.commit()
                reason_codes = [
                    "child_intent_already_exists",
                    "desired_trade_child_intent_already_created",
                    "conversion_idempotent",
                    "conversion_non_submitting",
                ]
                if recommendation_model is not None:
                    reason_codes.extend(
                        [
                            "route_readiness_audit_child_intent_already_created",
                            "recommendation_target_choice_child_intent_reused",
                        ]
                    )
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS,
                    reason_codes=reason_codes,
                    child_intent=self._order_intent_from_model(existing_related_intent),
                    converted_at=converted_at,
                    child_intent_reused=True,
                )

            if recommendation_model is not None:
                (
                    recommendation_current_blockers,
                    recommendation_current_missing,
                ) = self._recommendation_backed_target_choice_current_blockers(
                    session,
                    recommendation_model,
                    converted_at=converted_at,
                )
                if recommendation_current_blockers or recommendation_current_missing:
                    return self._conversion_result(
                        target_choice_id=choice_model.target_choice_id,
                        routing_assessment_id=choice_model.routing_assessment_id,
                        desired_trade_key=choice_model.desired_trade_key,
                        status=self._recommendation_backed_conversion_blocked_status(
                            recommendation_current_blockers
                        ),
                        reason_codes=recommendation_current_blockers
                        + ["conversion_non_submitting"],
                        missing_data=recommendation_current_missing,
                        converted_at=converted_at,
                    )

            assessment_model = self._load_assessment_for_target_choice(session, choice_model)
            if assessment_model is None:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_FOUND,
                    reason_codes=["routing_assessment_not_found", "conversion_non_submitting"],
                    converted_at=converted_at,
                )
            assessment_blockers = self._assessment_conversion_blockers(
                assessment_model,
                choice_model,
            )
            if assessment_blockers:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_FOUND,
                    reason_codes=assessment_blockers + ["conversion_non_submitting"],
                    converted_at=converted_at,
                )
            if assessment_model.decision_status != RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_ASSESSMENT_ONLY,
                    reason_codes=[
                        "routing_assessment_not_assessment_only",
                        "conversion_non_submitting",
                    ],
                    missing_data=list(assessment_model.missing_data_json or []),
                    converted_at=converted_at,
                )

            candidate_model = self._find_target_choice_candidate(
                session,
                assessment_ref_id=assessment_model.id,
                binding_ref_id=choice_model.selected_binding_ref_id,
                binding_key=choice_model.selected_binding_key,
            )
            if candidate_model is None:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_CANDIDATE_NOT_FOUND,
                    reason_codes=["routing_candidate_not_found", "conversion_non_submitting"],
                    converted_at=converted_at,
                )

            candidate_blockers, candidate_missing = self._candidate_conversion_blockers(
                candidate_model,
                choice_model,
            )
            if candidate_blockers or candidate_missing:
                status = (
                    RoutingTargetChoiceConversionStatus.BLOCKED_CANDIDATE_INELIGIBLE
                    if "routing_candidate_ineligible" in candidate_blockers
                    else RoutingTargetChoiceConversionStatus.BLOCKED_CANDIDATE_MISMATCH
                )
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=status,
                    reason_codes=candidate_blockers + ["conversion_non_submitting"],
                    missing_data=candidate_missing,
                    converted_at=converted_at,
                )

            desired_trade_model = self._load_desired_trade_for_target_choice(
                session,
                choice_model,
                assessment_model,
            )
            desired_trade_blockers = self._desired_trade_conversion_blockers(
                desired_trade_model,
                choice_model,
                assessment_model,
            )
            if desired_trade_blockers:
                status = (
                    RoutingTargetChoiceConversionStatus.BLOCKED_INVALID_DESIRED_TRADE
                    if "desired_trade_invalid_quantity" in desired_trade_blockers
                    or "desired_trade_missing_side" in desired_trade_blockers
                    else RoutingTargetChoiceConversionStatus.BLOCKED_STALE_DESIRED_TRADE
                )
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=status,
                    reason_codes=desired_trade_blockers + ["conversion_non_submitting"],
                    converted_at=converted_at,
                )

            target_blockers, target_missing = self._current_conversion_target_blockers(
                session,
                candidate_model,
                choice_model,
                assessment_model,
                desired_trade_model,
            )
            if target_blockers or target_missing:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET,
                    reason_codes=target_blockers + ["conversion_non_submitting"],
                    missing_data=target_missing,
                    converted_at=converted_at,
                )

            order_shape = self._routed_order_shape_for_conversion(
                desired_trade_model,
                candidate_model,
                order_shape_policy,
            )
            if order_shape.blocked:
                return self._conversion_result(
                    target_choice_id=choice_model.target_choice_id,
                    routing_assessment_id=choice_model.routing_assessment_id,
                    desired_trade_key=choice_model.desired_trade_key,
                    status=RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY,
                    reason_codes=order_shape.reason_codes + ["conversion_non_submitting"],
                    child_intent=None,
                    converted_at=converted_at,
                    order_shape_decision=order_shape,
                )

            child_intent = self._persist_converted_child_intent(
                session,
                choice_model=choice_model,
                assessment_model=assessment_model,
                candidate_model=candidate_model,
                desired_trade_model=desired_trade_model,
                order_shape=order_shape,
                idempotency_key=idempotency_key,
                created_at=converted_at,
            )
            session.commit()
            return self._conversion_result(
                target_choice_id=choice_model.target_choice_id,
                routing_assessment_id=choice_model.routing_assessment_id,
                desired_trade_key=choice_model.desired_trade_key,
                status=RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED,
                reason_codes=[
                    "child_intent_created",
                    "conversion_non_submitting",
                    "prepared_order_creation_deferred",
                    "readiness_assessment_deferred",
                    "submission_deferred",
                ],
                child_intent=child_intent,
                converted_at=converted_at,
            )

    async def _candidate_assessments(
        self,
        request: RoutingRequest,
        desired_trade: MandateDesiredTrade,
        *,
        assessment_id: str,
        evaluated_at: datetime,
    ) -> tuple[list[RoutingCandidateAssessment], str | None, list[str]]:
        if desired_trade.instrument_key is None:
            return [], "instrument_identity_missing", ["instrument_identity_missing"]
        try:
            candidates = await self.planning_service.list_routing_candidates(
                instrument_key=desired_trade.instrument_key,
                component_key=desired_trade.component_key,
                mandate_key=desired_trade.mandate_key,
            )
        except ValueError:
            return [], "routing_candidate_inventory_unavailable", ["candidate_inventory_unavailable"]

        assessments: list[RoutingCandidateAssessment] = []
        for candidate in candidates:
            assessments.append(
                self._assess_candidate(
                    request,
                    candidate,
                    assessment_id=assessment_id,
                    evaluated_at=evaluated_at,
                )
            )
        if not assessments:
            return [], "no_bindings_evaluated", []
        return assessments, None, []

    def _assess_candidate(
        self,
        request: RoutingRequest,
        candidate: BindingRoutingCandidate,
        *,
        assessment_id: str,
        evaluated_at: datetime,
    ) -> RoutingCandidateAssessment:
        model_reason_codes, model_facts = self._binding_and_account_truth(candidate)
        raw_reason_codes = list(candidate.eligibility_reasons)
        hard_reason_codes = [
            self._normalize_reason_code(reason)
            for reason in raw_reason_codes
            if reason not in _MISSING_DATA_REASONS
        ]
        if not candidate.venue_capabilities.adapter_supports_order_submission:
            hard_reason_codes.append("adapter_order_submission_unsupported")
        hard_reason_codes.extend(model_reason_codes)
        hard_reason_codes = sorted({reason for reason in hard_reason_codes if reason})
        missing_data = self._candidate_missing_data(candidate)

        if hard_reason_codes or missing_data:
            eligibility_status = RoutingCandidateEligibilityStatus.INELIGIBLE_FOR_FUTURE_SELECTION
            reason_codes = sorted(set(hard_reason_codes + missing_data))
        else:
            eligibility_status = RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
            reason_codes = ["binding_candidate_assessed_eligible"]

        fact_snapshot = {
            "strategy_eligible": candidate.strategy_eligible,
            "trading_eligible": candidate.trading_eligible,
            "routing_eligible": candidate.routing_eligible,
            "account_connected": candidate.account_connected,
            "quote_available": candidate.quote_available,
            "quote_source": (
                "adapter_top_of_book"
                if candidate.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot.available
                else None
            ),
            "quote_observed_at": (
                candidate.quote_snapshot.quote_snapshot.observed_at.isoformat()
                if candidate.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot.observed_at is not None
                else None
            ),
            "quote_bid_price": (
                str(candidate.quote_snapshot.quote_snapshot.bid_price)
                if candidate.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot.bid_price is not None
                else None
            ),
            "quote_ask_price": (
                str(candidate.quote_snapshot.quote_snapshot.ask_price)
                if candidate.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot is not None
                and candidate.quote_snapshot.quote_snapshot.ask_price is not None
                else None
            ),
            "available_balance_hint_present": candidate.available_balance_hint is not None,
            "venue_support_level": candidate.venue_capabilities.support_level.value,
            "supports_spot": candidate.venue_capabilities.supports_spot,
            "supports_perpetuals": candidate.venue_capabilities.supports_perpetuals,
            "supports_depth_summary": candidate.venue_capabilities.supports_depth_summary,
            "venue_supports_order_submission": candidate.venue_capabilities.supports_order_submission,
            "adapter_supports_order_submission": (
                candidate.venue_capabilities.adapter_supports_order_submission
            ),
            "adapter_supports_order_cancel": candidate.venue_capabilities.adapter_supports_order_cancel,
            "adapter_supports_order_amend": candidate.venue_capabilities.adapter_supports_order_amend,
            "supports_order_preview": candidate.venue_capabilities.supports_order_preview,
            "supported_order_types": [
                order_type.value for order_type in candidate.venue_capabilities.supported_order_types
            ],
            "private_lifecycle_update_mode": candidate.venue_capabilities.private_lifecycle_update_mode,
            "account_snapshot_available": candidate.account_connectivity.account_snapshot_available,
            "open_orders_query_available": candidate.account_connectivity.open_orders_query_available,
            "open_positions_query_available": candidate.account_connectivity.open_positions_query_available,
            "raw_candidate_reason_codes": raw_reason_codes,
            **model_facts,
        }
        return RoutingCandidateAssessment(
            assessment_id=assessment_id,
            binding_ref_id=candidate.binding_ref_id,
            binding_key=candidate.binding_key,
            venue_account_ref_id=candidate.venue_account_ref_id,
            venue_account_key=candidate.venue_account_key,
            venue=candidate.venue,
            instrument_key=candidate.instrument_key,
            instrument_ref_id=candidate.instrument_ref_id,
            symbol=candidate.symbol,
            exchange_symbol=candidate.exchange_symbol,
            eligibility_status=eligibility_status,
            reason_codes=reason_codes,
            missing_data=missing_data,
            fact_snapshot=fact_snapshot,
            evaluated_at=evaluated_at,
        )

    def _binding_and_account_truth(
        self,
        candidate: BindingRoutingCandidate,
    ) -> tuple[list[str], dict[str, object]]:
        reason_codes: list[str] = []
        facts: dict[str, object] = {
            "venue_account_active": None,
            "venue_account_trading_enabled": None,
            "binding_enabled": None,
            "binding_trading_enabled": None,
            "binding_routing_eligible": None,
        }
        with self._session_factory() as session:
            binding_model = (
                session.get(MandateAccountBindingModel, candidate.binding_ref_id)
                if candidate.binding_ref_id is not None
                else None
            )
            account_model = (
                session.get(VenueAccountModel, candidate.venue_account_ref_id)
                if candidate.venue_account_ref_id is not None
                else None
            )
            if binding_model is None:
                reason_codes.append("binding_record_missing")
            else:
                facts["binding_enabled"] = binding_model.enabled
                facts["binding_trading_enabled"] = binding_model.trading_enabled
                facts["binding_routing_eligible"] = binding_model.routing_eligible
                if not binding_model.enabled:
                    reason_codes.append("binding_disabled")
                if not binding_model.routing_eligible:
                    reason_codes.append("binding_not_routing_eligible")
                if not binding_model.trading_enabled:
                    reason_codes.append("binding_trading_disabled")
            if account_model is None:
                reason_codes.append("venue_account_record_missing")
            else:
                facts["venue_account_active"] = account_model.is_active
                facts["venue_account_trading_enabled"] = account_model.trading_enabled
                if not account_model.is_active:
                    reason_codes.append("venue_account_inactive")
                if not account_model.trading_enabled:
                    reason_codes.append("venue_account_trading_disabled")
        return reason_codes, facts

    @staticmethod
    def _candidate_missing_data(candidate: BindingRoutingCandidate) -> list[str]:
        missing_data: list[str] = []
        if "quote_unavailable" in candidate.eligibility_reasons or not candidate.quote_available:
            missing_data.append("missing_quote_snapshot")
        return sorted(set(missing_data))

    @staticmethod
    def _normalize_reason_code(reason_code: str) -> str:
        return _REASON_CODE_MAP.get(reason_code, reason_code)

    @staticmethod
    def _decision_status(
        candidates: list[RoutingCandidateAssessment],
        *,
        inventory_missing: list[str],
    ) -> RoutingAssessmentDecisionStatus:
        if any(
            candidate.eligibility_status
            == RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
            for candidate in candidates
        ):
            return RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY
        if inventory_missing or any(candidate.missing_data for candidate in candidates):
            return RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA
        return RoutingAssessmentDecisionStatus.NO_ELIGIBLE_BINDINGS

    @staticmethod
    def _assessment_reason_codes(
        candidates: list[RoutingCandidateAssessment],
        *,
        decision_status: RoutingAssessmentDecisionStatus,
        inventory_reason: str | None,
    ) -> list[str]:
        reason_codes: list[str] = []
        if inventory_reason is not None:
            reason_codes.append(inventory_reason)
        if decision_status == RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY:
            reason_codes.append("routing_assessment_only")
        elif decision_status == RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA:
            reason_codes.append("insufficient_routing_substrate_data")
        else:
            reason_codes.append("no_eligible_bindings")
        if not candidates:
            reason_codes.append("no_bindings_evaluated")
        return sorted(set(reason_codes))

    @staticmethod
    def _routing_request(
        desired_trade: MandateDesiredTrade,
        *,
        evaluated_at: datetime,
    ) -> RoutingRequest:
        return RoutingRequest(
            routing_request_id=f"rtreq_{uuid4().hex}",
            environment=desired_trade.environment,
            desired_trade_ref_id=desired_trade.desired_trade_ref_id,
            desired_trade_key=desired_trade.desired_trade_key,
            client_ref_id=desired_trade.client_ref_id,
            strategy_mandate_ref_id=desired_trade.strategy_mandate_ref_id,
            mandate_key=desired_trade.mandate_key,
            market_data_source_policy_ref_id=desired_trade.market_data_source_policy_ref_id,
            planning_source_venue=desired_trade.planning_source_venue,
            planning_source_mode=desired_trade.planning_source_mode,
            target_scope=desired_trade.target_scope,
            action=desired_trade.action,
            instrument_key=desired_trade.instrument_key,
            instrument_ref_id=desired_trade.instrument_ref_id,
            symbol=desired_trade.symbol,
            component_key=desired_trade.component_key,
            requested_at=evaluated_at,
        )

    @staticmethod
    def _validate_desired_trade(desired_trade: MandateDesiredTrade) -> None:
        if desired_trade.status != MandateDesiredTradeStatus.ROUTING_REQUIRED:
            raise RoutingAssessmentError(
                "desired_trade_not_routing_required",
                "Routing assessment requires a routing_required mandate desired trade.",
            )
        if desired_trade.target_scope != TradeTargetScope.MANDATE:
            raise RoutingAssessmentError(
                "desired_trade_not_mandate_scoped",
                "Routing assessment only supports mandate-scoped desired trades in Phase 5.0.",
            )
        if desired_trade.action != DecisionAction.OPEN:
            raise RoutingAssessmentError(
                "desired_trade_action_not_open",
                "Routing assessment only supports mandate-scoped open desired trades in Phase 5.0.",
            )
        if (
            desired_trade.mandate_account_binding_ref_id is not None
            or desired_trade.binding_key is not None
            or desired_trade.venue_account_ref_id is not None
        ):
            raise RoutingAssessmentError(
                "desired_trade_already_targeted",
                "Routing assessment cannot be created for an already binding/account-targeted desired trade.",
            )

    def _persist_assessment(self, assessment: RoutingAssessment) -> RoutingAssessment:
        with self._session_factory() as session:
            model = RoutingAssessmentModel(
                environment=assessment.environment,
                assessment_id=assessment.assessment_id,
                desired_trade_ref_id=assessment.desired_trade_ref_id,
                desired_trade_key=assessment.desired_trade_key,
                client_ref_id=assessment.client_ref_id,
                strategy_mandate_ref_id=assessment.strategy_mandate_ref_id,
                mandate_key=assessment.mandate_key,
                market_data_source_policy_ref_id=assessment.market_data_source_policy_ref_id,
                planning_source_venue=assessment.planning_source_venue,
                instrument_key=assessment.instrument_key,
                instrument_ref_id=assessment.instrument_ref_id,
                symbol=assessment.symbol,
                action=assessment.action,
                target_scope=assessment.target_scope,
                decision_status=assessment.decision_status,
                eligible_binding_count=assessment.eligible_binding_count,
                ineligible_binding_count=assessment.ineligible_binding_count,
                request_snapshot_json=self._request_snapshot(assessment.request),
                reason_codes_json=list(assessment.reason_codes),
                missing_data_json=list(assessment.missing_data),
                provenance_json=dict(assessment.provenance),
                evaluated_at=assessment.evaluated_at or _utcnow(),
            )
            session.add(model)
            session.flush()
            for candidate in assessment.candidates:
                session.add(
                    RoutingAssessmentCandidateModel(
                        assessment_ref_id=model.id,
                        assessment_id=assessment.assessment_id,
                        binding_ref_id=candidate.binding_ref_id,
                        binding_key=candidate.binding_key,
                        venue_account_ref_id=candidate.venue_account_ref_id,
                        venue_account_key=candidate.venue_account_key,
                        venue=candidate.venue,
                        instrument_key=candidate.instrument_key,
                        instrument_ref_id=candidate.instrument_ref_id,
                        symbol=candidate.symbol,
                        exchange_symbol=candidate.exchange_symbol,
                        eligibility_status=candidate.eligibility_status,
                        reason_codes_json=list(candidate.reason_codes),
                        missing_data_json=list(candidate.missing_data),
                        fact_snapshot_json=dict(candidate.fact_snapshot),
                        evaluated_at=candidate.evaluated_at or model.evaluated_at,
                    )
                )
            session.commit()
            return self._assessment_from_model(
                model,
                list(
                    session.scalars(
                        select(RoutingAssessmentCandidateModel)
                        .where(RoutingAssessmentCandidateModel.assessment_ref_id == model.id)
                        .order_by(RoutingAssessmentCandidateModel.binding_key.asc())
                    ).all()
                ),
            )

    @staticmethod
    def _request_snapshot(request: RoutingRequest) -> dict[str, object]:
        return {
            "routing_request_id": request.routing_request_id,
            "environment": request.environment.value,
            "desired_trade_ref_id": request.desired_trade_ref_id,
            "desired_trade_key": request.desired_trade_key,
            "client_ref_id": request.client_ref_id,
            "strategy_mandate_ref_id": request.strategy_mandate_ref_id,
            "mandate_key": request.mandate_key,
            "market_data_source_policy_ref_id": request.market_data_source_policy_ref_id,
            "planning_source_venue": request.planning_source_venue,
            "planning_source_mode": request.planning_source_mode.value,
            "target_scope": request.target_scope.value,
            "action": request.action.value,
            "instrument_key": request.instrument_key,
            "instrument_ref_id": request.instrument_ref_id,
            "symbol": request.symbol,
            "component_key": request.component_key,
            "requested_at": request.requested_at.isoformat(),
        }

    @staticmethod
    def _request_from_snapshot(model: RoutingAssessmentModel) -> RoutingRequest:
        snapshot = dict(model.request_snapshot_json or {})
        return RoutingRequest(
            routing_request_id=str(snapshot.get("routing_request_id") or ""),
            environment=model.environment,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            market_data_source_policy_ref_id=model.market_data_source_policy_ref_id,
            planning_source_venue=model.planning_source_venue,
            planning_source_mode=MarketDataSourceMode(str(snapshot.get("planning_source_mode"))),
            target_scope=model.target_scope,
            action=model.action,
            instrument_key=model.instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            component_key=snapshot.get("component_key") if isinstance(snapshot.get("component_key"), str) else None,
            requested_at=datetime.fromisoformat(str(snapshot.get("requested_at") or model.evaluated_at.isoformat())),
        )

    @classmethod
    def _assessment_from_model(
        cls,
        model: RoutingAssessmentModel,
        candidate_models: list[RoutingAssessmentCandidateModel],
    ) -> RoutingAssessment:
        request = cls._request_from_snapshot(model)
        candidates = [
            RoutingCandidateAssessment(
                assessment_id=candidate.assessment_id,
                binding_ref_id=candidate.binding_ref_id,
                binding_key=candidate.binding_key,
                venue_account_ref_id=candidate.venue_account_ref_id,
                venue_account_key=candidate.venue_account_key,
                venue=candidate.venue,
                instrument_key=candidate.instrument_key,
                instrument_ref_id=candidate.instrument_ref_id,
                symbol=candidate.symbol,
                exchange_symbol=candidate.exchange_symbol,
                eligibility_status=candidate.eligibility_status,
                reason_codes=list(candidate.reason_codes_json or []),
                missing_data=list(candidate.missing_data_json or []),
                fact_snapshot=dict(candidate.fact_snapshot_json or {}),
                evaluated_at=candidate.evaluated_at,
            )
            for candidate in candidate_models
        ]
        return RoutingAssessment(
            assessment_id=model.assessment_id,
            environment=model.environment,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            market_data_source_policy_ref_id=model.market_data_source_policy_ref_id,
            planning_source_venue=model.planning_source_venue,
            instrument_key=model.instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            action=model.action,
            target_scope=model.target_scope,
            decision_status=model.decision_status,
            eligible_binding_count=model.eligible_binding_count,
            ineligible_binding_count=model.ineligible_binding_count,
            request=request,
            candidates=candidates,
            reason_codes=list(model.reason_codes_json or []),
            missing_data=list(model.missing_data_json or []),
            evaluated_at=model.evaluated_at,
            provenance=dict(model.provenance_json or {}),
        )

    def _build_route_readiness_audit(
        self,
        session: Any,
        assessment_model: RoutingAssessmentModel,
        candidate_models: list[RoutingAssessmentCandidateModel],
        *,
        evaluated_at: datetime,
    ) -> RouteReadinessAudit:
        audit_id = f"rtraudit_{uuid4().hex}"
        desired_trade_model = self._load_desired_trade_for_route_readiness(
            session,
            assessment_model,
        )
        global_reason_codes, global_missing, global_stale, global_blocking = (
            self._route_readiness_global_facts(session, assessment_model, desired_trade_model)
        )
        candidates = [
            self._route_readiness_candidate_audit(
                session,
                audit_id,
                assessment_model,
                candidate_model,
                desired_trade_model,
                evaluated_at=evaluated_at,
            )
            for candidate_model in candidate_models
        ]
        if not candidate_models:
            global_blocking.append("no_candidates_evaluated")
            global_reason_codes.append("no_candidates_evaluated")

        ready_candidate_count = sum(
            1
            for candidate in candidates
            if candidate.status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
        )
        blocked_candidate_count = sum(
            1
            for candidate in candidates
            if candidate.status
            in {
                RouteReadinessAuditStatus.BLOCKED,
                RouteReadinessAuditStatus.POLICY_BLOCKED,
                RouteReadinessAuditStatus.UNSUPPORTED,
            }
        )
        insufficient_data_candidate_count = sum(
            1
            for candidate in candidates
            if candidate.status
            in {
                RouteReadinessAuditStatus.INSUFFICIENT_DATA,
                RouteReadinessAuditStatus.STALE_DATA,
            }
        )
        overall_status = self._route_readiness_overall_status(
            candidates,
            global_missing=global_missing,
            global_stale=global_stale,
            global_blocking=global_blocking,
        )
        global_reason_codes = sorted(
            set(
                global_reason_codes
                + [
                    "route_readiness_audit_non_selecting",
                    "recommendation_not_created",
                    "target_choice_creation_deferred",
                    "child_intent_creation_deferred",
                    "submission_deferred",
                ]
            )
        )
        if overall_status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION:
            global_reason_codes.append("ready_for_recommendation_data_sufficient")
        else:
            global_reason_codes.append("not_ready_for_recommendation")

        return RouteReadinessAudit(
            route_readiness_audit_id=audit_id,
            environment=assessment_model.environment,
            desired_trade_ref_id=assessment_model.desired_trade_ref_id,
            desired_trade_key=assessment_model.desired_trade_key,
            routing_assessment_ref_id=assessment_model.id,
            routing_assessment_id=assessment_model.assessment_id,
            client_ref_id=assessment_model.client_ref_id,
            strategy_mandate_ref_id=assessment_model.strategy_mandate_ref_id,
            mandate_key=assessment_model.mandate_key,
            instrument_ref_id=assessment_model.instrument_ref_id,
            instrument_key=assessment_model.instrument_key,
            symbol=assessment_model.symbol,
            action=assessment_model.action,
            target_scope=assessment_model.target_scope,
            evaluated_at=evaluated_at,
            overall_status=overall_status,
            candidate_count=len(candidates),
            ready_candidate_count=ready_candidate_count,
            blocked_candidate_count=blocked_candidate_count,
            insufficient_data_candidate_count=insufficient_data_candidate_count,
            global_reason_codes=sorted(set(global_reason_codes)),
            global_missing_data=sorted(set(global_missing)),
            global_stale_data=sorted(set(global_stale)),
            global_blocking_reasons=sorted(set(global_blocking)),
            candidates=candidates,
            non_selecting=True,
            recommendation_created=False,
            target_choice_created=False,
            child_intent_created=False,
            submitted_order_created=False,
            provenance={
                "phase": "phase_5_10_1",
                "boundary": "route_readiness_audit_only",
                "non_selecting": True,
                "non_ranking": True,
                "non_scoring": True,
                "non_executing": True,
                "recommendation_created": False,
                "target_choice_created": False,
                "child_intent_created": False,
                "prepared_order_created": False,
                "readiness_assessment_created": False,
                "submitted_order_created": False,
                "routing_assessment_id": assessment_model.assessment_id,
                "desired_trade_key": assessment_model.desired_trade_key,
                "ready_for_recommendation_means": "required facts are data-sufficient; no target was recommended",
                "staleness_model": "quote_observed_at_freshness_only",
                "desired_trade_expiry_model": "not_modeled",
                "target_recommendation": "not_created_by_route_readiness_audit",
                "target_recommendation_next_step": "phase_6_0_0_single_ready_candidate_only",
            },
        )

    def _route_readiness_global_facts(
        self,
        session: Any,
        assessment_model: RoutingAssessmentModel,
        desired_trade_model: MandateDesiredTradeModel | None,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        reason_codes: list[str] = []
        missing_data: list[str] = []
        stale_data: list[str] = []
        blocking_reasons: list[str] = []

        if desired_trade_model is None:
            blocking_reasons.append("desired_trade_missing")
            return ["desired_trade_missing"], [], [], blocking_reasons

        if desired_trade_model.status != MandateDesiredTradeStatus.ROUTING_REQUIRED:
            blocking_reasons.append("desired_trade_not_routing_required")
        if desired_trade_model.target_scope != TradeTargetScope.MANDATE:
            blocking_reasons.append("desired_trade_not_mandate_scoped")
        if desired_trade_model.action != DecisionAction.OPEN:
            blocking_reasons.append("desired_trade_action_not_open")
        if (
            desired_trade_model.mandate_account_binding_ref_id is not None
            or desired_trade_model.binding_key is not None
            or desired_trade_model.venue_account_ref_id is not None
        ):
            blocking_reasons.append("desired_trade_already_targeted")
        if desired_trade_model.status == MandateDesiredTradeStatus.ROUTED:
            blocking_reasons.append("desired_trade_already_routed")
        if desired_trade_model.client_ref_id != assessment_model.client_ref_id:
            stale_data.append("desired_trade_client_mismatch")
        if desired_trade_model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id:
            stale_data.append("desired_trade_mandate_mismatch")
        if desired_trade_model.desired_trade_key != assessment_model.desired_trade_key:
            stale_data.append("desired_trade_key_mismatch")
        if desired_trade_model.strategy_mandate_ref_id is None or desired_trade_model.mandate_key is None:
            missing_data.append("desired_trade_mandate_identity_missing")
        if desired_trade_model.instrument_ref_id is None or desired_trade_model.instrument_key is None:
            missing_data.append("desired_trade_instrument_identity_missing")
        if desired_trade_model.market_data_source_policy_ref_id is None:
            missing_data.append("market_data_source_policy_missing")
        if desired_trade_model.side is None:
            blocking_reasons.append("desired_trade_missing_side")
        quantity = desired_trade_model.desired_quantity
        if quantity is None:
            blocking_reasons.append("desired_trade_missing_quantity")
        elif not DefaultRoutingAssessmentService._decimal_is_positive_finite(quantity):
            blocking_reasons.append("desired_trade_invalid_quantity")

        mandate_model = (
            session.get(StrategyMandateModel, desired_trade_model.strategy_mandate_ref_id)
            if desired_trade_model.strategy_mandate_ref_id is not None
            else None
        )
        if mandate_model is None:
            blocking_reasons.append("mandate_missing")
        elif not mandate_model.enabled:
            blocking_reasons.append("mandate_inactive")

        reason_codes.extend(missing_data)
        reason_codes.extend(stale_data)
        reason_codes.extend(blocking_reasons)
        return (
            sorted(set(reason_codes)),
            sorted(set(missing_data)),
            sorted(set(stale_data)),
            sorted(set(blocking_reasons)),
        )

    def _route_readiness_candidate_audit(
        self,
        session: Any,
        audit_id: str,
        assessment_model: RoutingAssessmentModel,
        candidate_model: RoutingAssessmentCandidateModel,
        desired_trade_model: MandateDesiredTradeModel | None,
        *,
        evaluated_at: datetime,
    ) -> RouteReadinessCandidateAudit:
        fact_snapshot = dict(candidate_model.fact_snapshot_json or {})
        data_sources: dict[str, str] = {
            "desired_trade": "persistence",
            "mandate": "persistence",
            "binding": "persistence",
            "venue_account": "persistence",
            "instrument": "persistence",
            "symbol_mapping": "persistence",
            "venue_capability": "derived_from_existing_assessment",
            "order_shape_policy": "static_config",
            "market_data": "derived_from_existing_assessment",
            "quote": "unavailable",
            "private_state": "adapter_capability",
            "balance": "unavailable",
            "fees": "unavailable",
            "constraints": "persistence",
        }
        missing_data: list[str] = list(candidate_model.missing_data_json or [])
        stale_data: list[str] = []
        unsupported_data: list[str] = []
        unavailable_data: list[str] = []
        policy_blocks: list[str] = []
        blocking_reasons: list[str] = []
        reason_codes: list[str] = []

        binding_model = (
            session.get(MandateAccountBindingModel, candidate_model.binding_ref_id)
            if candidate_model.binding_ref_id is not None
            else None
        )
        account_model = (
            session.get(VenueAccountModel, candidate_model.venue_account_ref_id)
            if candidate_model.venue_account_ref_id is not None
            else None
        )
        symbol_model = self._symbol_for_route_readiness_candidate(session, candidate_model)
        instrument_model = (
            session.get(InstrumentModel, assessment_model.instrument_ref_id)
            if assessment_model.instrument_ref_id is not None
            else None
        )
        account_snapshot = self._latest_account_snapshot_for_route_readiness(
            session,
            candidate_model.venue_account_ref_id,
        )

        if binding_model is None:
            blocking_reasons.append("binding_missing")
        else:
            if binding_model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id:
                stale_data.append("binding_mandate_mismatch")
            if not binding_model.enabled:
                blocking_reasons.append("binding_disabled")
            if not binding_model.trading_enabled:
                blocking_reasons.append("binding_trading_disabled")
            if not binding_model.routing_eligible:
                blocking_reasons.append("binding_not_routing_eligible")

        if account_model is None:
            blocking_reasons.append("venue_account_missing")
            data_sources["venue_account"] = "unavailable"
        else:
            if account_model.client_ref_id != assessment_model.client_ref_id:
                stale_data.append("venue_account_client_mismatch")
            if account_model.id != candidate_model.venue_account_ref_id:
                stale_data.append("venue_account_ref_mismatch")
            if not account_model.is_active:
                blocking_reasons.append("venue_account_inactive")
            if not account_model.trading_enabled:
                blocking_reasons.append("venue_account_trading_disabled")

        if instrument_model is None:
            missing_data.append("instrument_missing")
            data_sources["instrument"] = "unavailable"
        elif not instrument_model.is_active:
            blocking_reasons.append("instrument_inactive")
        if assessment_model.instrument_ref_id is None or assessment_model.instrument_key is None:
            missing_data.append("instrument_identity_missing")

        if symbol_model is None:
            missing_data.extend(["symbol_mapping_missing", "exchange_symbol_missing"])
            data_sources["symbol_mapping"] = "unavailable"
            data_sources["constraints"] = "unavailable"
        else:
            if candidate_model.exchange_symbol != symbol_model.exchange_symbol:
                stale_data.append("exchange_symbol_stale")
            self._route_readiness_symbol_constraint_facts(
                symbol_model,
                missing_data=missing_data,
                unavailable_data=unavailable_data,
                fact_snapshot=fact_snapshot,
            )
            self._route_readiness_market_product_facts(
                symbol_model,
                fact_snapshot,
                unsupported_data=unsupported_data,
            )

        self._route_readiness_execution_capability_facts(
            fact_snapshot,
            missing_data=missing_data,
            unsupported_data=unsupported_data,
            unavailable_data=unavailable_data,
        )
        self._route_readiness_market_data_facts(
            fact_snapshot,
            evaluated_at=evaluated_at,
            missing_data=missing_data,
            stale_data=stale_data,
            unavailable_data=unavailable_data,
            data_sources=data_sources,
        )
        self._route_readiness_economic_facts(
            desired_trade_model,
            fact_snapshot,
            account_snapshot,
            missing_data=missing_data,
            unavailable_data=unavailable_data,
            blocking_reasons=blocking_reasons,
            data_sources=data_sources,
        )
        self._route_readiness_order_shape_facts(
            fact_snapshot,
            missing_data=missing_data,
            unsupported_data=unsupported_data,
            policy_blocks=policy_blocks,
        )

        candidate_assessment_reason_codes = set(candidate_model.reason_codes_json or [])
        candidate_missing_data = set(candidate_model.missing_data_json or [])
        hard_assessment_reason_codes = candidate_assessment_reason_codes - candidate_missing_data
        if (
            candidate_model.eligibility_status != RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
            and hard_assessment_reason_codes
        ):
            blocking_reasons.append("routing_candidate_not_eligible")
        if candidate_assessment_reason_codes:
            fact_snapshot["routing_assessment_reason_codes"] = sorted(candidate_assessment_reason_codes)

        reason_codes.extend(missing_data)
        reason_codes.extend(stale_data)
        reason_codes.extend(unsupported_data)
        reason_codes.extend(unavailable_data)
        reason_codes.extend(policy_blocks)
        reason_codes.extend(blocking_reasons)
        if not reason_codes:
            reason_codes.append("ready_for_recommendation_data_sufficient")
        else:
            reason_codes.append("route_readiness_audit_non_selecting")

        status = self._route_readiness_candidate_status(
            missing_data=missing_data,
            stale_data=stale_data,
            unsupported_data=unsupported_data,
            unavailable_data=unavailable_data,
            policy_blocks=policy_blocks,
            blocking_reasons=blocking_reasons,
        )
        fact_snapshot.update(
            {
                "default_order_shape_policy": "market_order_default_current_phase",
                "order_type_for_readiness_audit": OrderType.MARKET.value,
                "limit_price_source": "not_applicable_for_market_default",
                "system_price_discovery": "unavailable",
                "slippage_guard": "missing",
                "same_venue_multi_account_scope": "venue_account_ref_id",
                "venue_global_fallback": False,
                "recommendation_created": False,
                "target_choice_created": False,
                "child_intent_created": False,
                "submitted_order_created": False,
                "non_selecting": True,
            }
        )
        return RouteReadinessCandidateAudit(
            route_readiness_audit_id=audit_id,
            binding_ref_id=candidate_model.binding_ref_id,
            binding_key=candidate_model.binding_key,
            venue_account_ref_id=candidate_model.venue_account_ref_id,
            venue_account_key=candidate_model.venue_account_key,
            venue=candidate_model.venue,
            instrument_ref_id=candidate_model.instrument_ref_id,
            instrument_key=candidate_model.instrument_key,
            symbol=candidate_model.symbol,
            exchange_symbol=candidate_model.exchange_symbol,
            status=status,
            reason_codes=sorted(set(reason_codes)),
            missing_data=sorted(set(missing_data)),
            stale_data=sorted(set(stale_data)),
            unsupported_data=sorted(set(unsupported_data)),
            unavailable_data=sorted(set(unavailable_data)),
            policy_blocks=sorted(set(policy_blocks)),
            blocking_reasons=sorted(set(blocking_reasons)),
            fact_snapshot=self._jsonable_dict(fact_snapshot),
            data_sources=data_sources,
            evaluated_at=evaluated_at,
        )

    @staticmethod
    def _route_readiness_candidate_status(
        *,
        missing_data: list[str],
        stale_data: list[str],
        unsupported_data: list[str],
        unavailable_data: list[str],
        policy_blocks: list[str],
        blocking_reasons: list[str],
    ) -> RouteReadinessAuditStatus:
        if policy_blocks:
            return RouteReadinessAuditStatus.POLICY_BLOCKED
        if blocking_reasons:
            return RouteReadinessAuditStatus.BLOCKED
        if stale_data:
            return RouteReadinessAuditStatus.STALE_DATA
        if unsupported_data:
            return RouteReadinessAuditStatus.UNSUPPORTED
        if missing_data or unavailable_data:
            return RouteReadinessAuditStatus.INSUFFICIENT_DATA
        return RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION

    @staticmethod
    def _route_readiness_overall_status(
        candidates: list[RouteReadinessCandidateAudit],
        *,
        global_missing: list[str],
        global_stale: list[str],
        global_blocking: list[str],
    ) -> RouteReadinessAuditStatus:
        if global_blocking:
            return RouteReadinessAuditStatus.BLOCKED
        if global_stale:
            return RouteReadinessAuditStatus.STALE_DATA
        if global_missing:
            return RouteReadinessAuditStatus.INSUFFICIENT_DATA
        if any(
            candidate.status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
            for candidate in candidates
        ):
            return RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
        if any(candidate.status == RouteReadinessAuditStatus.STALE_DATA for candidate in candidates):
            return RouteReadinessAuditStatus.STALE_DATA
        if any(candidate.status == RouteReadinessAuditStatus.INSUFFICIENT_DATA for candidate in candidates):
            return RouteReadinessAuditStatus.INSUFFICIENT_DATA
        if any(candidate.status == RouteReadinessAuditStatus.POLICY_BLOCKED for candidate in candidates):
            return RouteReadinessAuditStatus.POLICY_BLOCKED
        if any(candidate.status == RouteReadinessAuditStatus.UNSUPPORTED for candidate in candidates):
            return RouteReadinessAuditStatus.UNSUPPORTED
        return RouteReadinessAuditStatus.BLOCKED

    @staticmethod
    def _route_readiness_symbol_constraint_facts(
        symbol_model: SymbolModel,
        *,
        missing_data: list[str],
        unavailable_data: list[str],
        fact_snapshot: dict[str, object],
    ) -> None:
        fact_snapshot["market_type"] = symbol_model.market_type.value
        fact_snapshot["product_type"] = symbol_model.product_type.value
        fact_snapshot["price_tick_size"] = str(symbol_model.price_tick_size)
        fact_snapshot["quantity_step_size"] = str(symbol_model.quantity_step_size)
        fact_snapshot["min_order_size"] = str(symbol_model.min_order_size)
        if symbol_model.price_tick_size <= Decimal("0"):
            missing_data.append("tick_size_missing")
        if symbol_model.quantity_step_size <= Decimal("0"):
            missing_data.append("quantity_step_size_missing")
        if symbol_model.min_order_size <= Decimal("0"):
            missing_data.append("minimum_order_size_missing")
        if not isinstance(symbol_model.raw_metadata, dict) or not (
            symbol_model.raw_metadata.get("minimum_notional")
            or symbol_model.raw_metadata.get("min_notional")
        ):
            unavailable_data.append("minimum_notional_missing")

    @staticmethod
    def _route_readiness_market_product_facts(
        symbol_model: SymbolModel,
        fact_snapshot: dict[str, object],
        *,
        unsupported_data: list[str],
    ) -> None:
        supports_spot = fact_snapshot.get("supports_spot")
        supports_perpetuals = fact_snapshot.get("supports_perpetuals")
        if symbol_model.market_type.value == "spot":
            if supports_spot is False:
                unsupported_data.append("market_type_unsupported")
        elif symbol_model.market_type.value == "perpetual" and supports_perpetuals is False:
            unsupported_data.append("market_type_unsupported")

    @staticmethod
    def _route_readiness_execution_capability_facts(
        fact_snapshot: dict[str, object],
        *,
        missing_data: list[str],
        unsupported_data: list[str],
        unavailable_data: list[str],
    ) -> None:
        supported_order_types = fact_snapshot.get("supported_order_types")
        if not isinstance(supported_order_types, list) or not supported_order_types:
            missing_data.append("order_type_support_unknown")
        if fact_snapshot.get("venue_supports_order_submission") is False:
            unsupported_data.append("venue_order_submission_unsupported")
        if fact_snapshot.get("adapter_supports_order_submission") is False:
            unsupported_data.append("adapter_order_submission_unsupported")
        if fact_snapshot.get("supports_order_preview") is False:
            unavailable_data.append("prepared_order_preview_unavailable")
        if fact_snapshot.get("private_lifecycle_update_mode") in {None, ""}:
            unavailable_data.append("private_state_visibility_unknown")
        if fact_snapshot.get("open_orders_query_available") is False:
            unavailable_data.append("open_orders_visibility_unavailable")
        if fact_snapshot.get("account_snapshot_available") is False:
            unavailable_data.append("balances_positions_visibility_unavailable")
        if fact_snapshot.get("adapter_supports_order_cancel") is None:
            unavailable_data.append("cancel_support_unknown")
        if fact_snapshot.get("adapter_supports_order_amend") is None:
            unavailable_data.append("amend_support_unknown")
        # Recovery is currently service-level same-target behavior unless explicitly audited.
        if fact_snapshot.get("recovery_support_known") is not True:
            unavailable_data.append("recovery_support_not_candidate_scoped")

    @staticmethod
    def _route_readiness_market_data_facts(
        fact_snapshot: dict[str, object],
        *,
        evaluated_at: datetime,
        missing_data: list[str],
        stale_data: list[str],
        unavailable_data: list[str],
        data_sources: dict[str, str],
    ) -> None:
        if not fact_snapshot.get("quote_available"):
            missing_data.extend(["quote_missing", "missing_quote_snapshot"])
            data_sources["quote"] = "unavailable"
        else:
            data_sources["quote"] = "derived_from_existing_assessment"
            fact_snapshot["quote_audit_source"] = "derived_from_existing_assessment"
            if not fact_snapshot.get("quote_source"):
                missing_data.append("quote_source_unknown")
            else:
                fact_snapshot["quote_original_source"] = fact_snapshot.get("quote_source")
            for price_field in ("quote_bid_price", "quote_ask_price"):
                price, price_reason = DefaultRoutingAssessmentService._positive_finite_decimal_for_audit(
                    fact_snapshot.get(price_field),
                    missing_reason="quote_price_missing",
                    malformed_reason="quote_price_malformed",
                    non_finite_reason="quote_price_non_finite",
                    non_positive_reason="quote_price_non_positive",
                )
                validity_field = f"{price_field}_valid"
                if price_reason is not None:
                    missing_data.append(price_reason)
                    fact_snapshot[validity_field] = False
                    fact_snapshot[f"{price_field}_invalid_reason"] = price_reason
                else:
                    fact_snapshot[validity_field] = True
                    fact_snapshot[f"{price_field}_decimal"] = str(price)
            observed_at = DefaultRoutingAssessmentService._parse_audit_datetime(
                fact_snapshot.get("quote_observed_at")
            )
            if observed_at is None:
                missing_data.append("quote_freshness_unknown")
            elif evaluated_at - observed_at > timedelta(seconds=_ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS):
                stale_data.append("quote_stale")
            fact_snapshot["quote_freshness_threshold_seconds"] = _ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS
        if fact_snapshot.get("stale_quote_protection_known") is not True:
            unavailable_data.append("stale_quote_protection_unknown")
        if fact_snapshot.get("depth_required") is False:
            fact_snapshot["depth_status"] = "depth_not_required"
        elif fact_snapshot.get("supports_depth_summary") is True and fact_snapshot.get("depth_available") is True:
            data_sources["market_data"] = "derived_from_existing_assessment"
        elif fact_snapshot.get("supports_depth_summary") is True:
            unavailable_data.append("depth_not_checked")
        else:
            unavailable_data.append("depth_unavailable")

    @staticmethod
    def _route_readiness_economic_facts(
        desired_trade_model: MandateDesiredTradeModel | None,
        fact_snapshot: dict[str, object],
        account_snapshot: ExchangeAccountSnapshotModel | None,
        *,
        missing_data: list[str],
        unavailable_data: list[str],
        blocking_reasons: list[str],
        data_sources: dict[str, str],
    ) -> None:
        if fact_snapshot.get("fee_data_available") is True:
            data_sources["fees"] = "static_config"
        else:
            unavailable_data.append("fee_data_missing")
        if account_snapshot is None:
            missing_data.extend(
                [
                    "balance_snapshot_missing",
                    "balance_source_unknown",
                    "available_balance_unknown",
                    "notional_sufficiency_unknown",
                    "margin_sufficiency_unknown",
                ]
            )
            data_sources["balance"] = "unavailable"
            return

        data_sources["balance"] = "persistence"
        fact_snapshot["balance_source"] = "persistence"
        fact_snapshot["available_balance"] = str(account_snapshot.available_balance)
        ask_price, price_reason = DefaultRoutingAssessmentService._positive_finite_decimal_for_audit(
            fact_snapshot.get("quote_ask_price"),
            missing_reason="quote_price_missing",
            malformed_reason="quote_price_malformed",
            non_finite_reason="quote_price_non_finite",
            non_positive_reason="quote_price_non_positive",
        )
        desired_quantity, quantity_reason = DefaultRoutingAssessmentService._positive_finite_decimal_for_audit(
            desired_trade_model.desired_quantity if desired_trade_model is not None else None,
            missing_reason="desired_trade_missing_quantity",
            malformed_reason="desired_trade_invalid_quantity",
            non_finite_reason="desired_trade_invalid_quantity",
            non_positive_reason="desired_trade_invalid_quantity",
        )
        if price_reason is not None:
            missing_data.append(price_reason)
        if quantity_reason is not None:
            missing_data.append("notional_sufficiency_unknown")
        elif price_reason is not None:
            missing_data.append("notional_sufficiency_unknown")
        elif ask_price is None or desired_quantity is None:
            missing_data.append("notional_sufficiency_unknown")
        else:
            required_notional = desired_quantity * ask_price
            fact_snapshot["required_notional_estimate"] = str(required_notional)
            fact_snapshot["notional_sufficiency_source"] = "persistence_plus_top_of_book"
            if account_snapshot.available_balance < required_notional:
                blocking_reasons.append("notional_sufficiency_blocked")
        if fact_snapshot.get("margin_sufficiency_known") is not True:
            unavailable_data.append("margin_sufficiency_unknown")

    @staticmethod
    def _route_readiness_order_shape_facts(
        fact_snapshot: dict[str, object],
        *,
        missing_data: list[str],
        unsupported_data: list[str],
        policy_blocks: list[str],
    ) -> None:
        supported_order_types = fact_snapshot.get("supported_order_types")
        if not isinstance(supported_order_types, list):
            missing_data.append("order_type_support_unknown")
            return
        if OrderType.MARKET.value not in supported_order_types:
            policy_blocks.append("order_type_unsupported")
            unsupported_data.append("order_type_unsupported")
        fact_snapshot["order_shape_policy_reason_codes"] = [
            "order_shape_policy_defaulted",
            "market_order_policy_defaulted",
        ]
        if fact_snapshot.get("slippage_guard_present") is not True:
            missing_data.append("slippage_guard_missing")
        if fact_snapshot.get("system_price_discovery_required") is True:
            missing_data.append("system_price_discovery_unavailable")

    @staticmethod
    def _parse_audit_datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _decimal_is_positive_finite(value: Decimal) -> bool:
        try:
            return value.is_finite() and value > Decimal("0")
        except InvalidOperation:
            return False

    @staticmethod
    def _positive_finite_decimal_for_audit(
        value: object,
        *,
        missing_reason: str,
        malformed_reason: str,
        non_finite_reason: str,
        non_positive_reason: str,
    ) -> tuple[Decimal | None, str | None]:
        if value is None or value == "":
            return None, missing_reason
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None, malformed_reason
        try:
            if not parsed.is_finite():
                return None, non_finite_reason
            if parsed <= Decimal("0"):
                return None, non_positive_reason
        except InvalidOperation:
            return None, malformed_reason
        return parsed, None

    @staticmethod
    def _jsonable_dict(payload: dict[str, object]) -> dict[str, object]:
        return json.loads(json.dumps(payload, default=str))

    def _load_desired_trade_for_route_readiness(
        self,
        session: Any,
        assessment_model: RoutingAssessmentModel,
    ) -> MandateDesiredTradeModel | None:
        if assessment_model.desired_trade_ref_id is not None:
            model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.environment == self.settings.app.environment,
                    MandateDesiredTradeModel.id == assessment_model.desired_trade_ref_id,
                )
            )
            if model is not None:
                return model
        return session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.environment == self.settings.app.environment,
                MandateDesiredTradeModel.desired_trade_key == assessment_model.desired_trade_key,
            )
        )

    @staticmethod
    def _symbol_for_route_readiness_candidate(
        session: Any,
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> SymbolModel | None:
        if candidate_model.instrument_ref_id is None:
            return None
        statement = select(SymbolModel).where(
            SymbolModel.instrument_ref_id == candidate_model.instrument_ref_id,
            SymbolModel.venue == candidate_model.venue,
            SymbolModel.is_active.is_(True),
        )
        if candidate_model.exchange_symbol is not None:
            statement = statement.where(SymbolModel.exchange_symbol == candidate_model.exchange_symbol)
        return session.scalar(statement.order_by(SymbolModel.exchange_symbol.asc()))

    def _latest_account_snapshot_for_route_readiness(
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

    def _persist_route_readiness_audit(
        self,
        session: Any,
        audit: RouteReadinessAudit,
    ) -> RouteReadinessAudit:
        model = RouteReadinessAuditModel(
            environment=audit.environment,
            route_readiness_audit_id=audit.route_readiness_audit_id,
            desired_trade_ref_id=audit.desired_trade_ref_id,
            desired_trade_key=audit.desired_trade_key,
            routing_assessment_ref_id=audit.routing_assessment_ref_id,
            routing_assessment_id=audit.routing_assessment_id,
            client_ref_id=audit.client_ref_id,
            strategy_mandate_ref_id=audit.strategy_mandate_ref_id,
            mandate_key=audit.mandate_key,
            instrument_ref_id=audit.instrument_ref_id,
            instrument_key=audit.instrument_key,
            symbol=audit.symbol,
            action=audit.action,
            target_scope=audit.target_scope,
            overall_status=audit.overall_status,
            candidate_count=audit.candidate_count,
            ready_candidate_count=audit.ready_candidate_count,
            blocked_candidate_count=audit.blocked_candidate_count,
            insufficient_data_candidate_count=audit.insufficient_data_candidate_count,
            global_reason_codes_json=list(audit.global_reason_codes),
            global_missing_data_json=list(audit.global_missing_data),
            global_stale_data_json=list(audit.global_stale_data),
            global_blocking_reasons_json=list(audit.global_blocking_reasons),
            non_selecting=audit.non_selecting,
            recommendation_created=audit.recommendation_created,
            target_choice_created=audit.target_choice_created,
            child_intent_created=audit.child_intent_created,
            submitted_order_created=audit.submitted_order_created,
            provenance_json=self._jsonable_dict(audit.provenance),
            evaluated_at=audit.evaluated_at,
        )
        session.add(model)
        session.flush()
        assessment_candidate_by_key = {
            (candidate.binding_ref_id, candidate.binding_key): candidate
            for candidate in session.scalars(
                select(RoutingAssessmentCandidateModel).where(
                    RoutingAssessmentCandidateModel.assessment_id == audit.routing_assessment_id
                )
            ).all()
        }
        for candidate in audit.candidates:
            assessment_candidate = assessment_candidate_by_key.get(
                (candidate.binding_ref_id, candidate.binding_key)
            )
            session.add(
                RouteReadinessCandidateAuditModel(
                    route_readiness_audit_ref_id=model.id,
                    route_readiness_audit_id=audit.route_readiness_audit_id,
                    routing_assessment_candidate_ref_id=(
                        assessment_candidate.id if assessment_candidate is not None else None
                    ),
                    binding_ref_id=candidate.binding_ref_id,
                    binding_key=candidate.binding_key,
                    venue_account_ref_id=candidate.venue_account_ref_id,
                    venue_account_key=candidate.venue_account_key,
                    venue=candidate.venue,
                    instrument_ref_id=candidate.instrument_ref_id,
                    instrument_key=candidate.instrument_key,
                    symbol=candidate.symbol,
                    exchange_symbol=candidate.exchange_symbol,
                    status=candidate.status,
                    reason_codes_json=list(candidate.reason_codes),
                    missing_data_json=list(candidate.missing_data),
                    stale_data_json=list(candidate.stale_data),
                    unsupported_data_json=list(candidate.unsupported_data),
                    unavailable_data_json=list(candidate.unavailable_data),
                    policy_blocks_json=list(candidate.policy_blocks),
                    blocking_reasons_json=list(candidate.blocking_reasons),
                    fact_snapshot_json=self._jsonable_dict(candidate.fact_snapshot),
                    data_sources_json=dict(candidate.data_sources),
                    evaluated_at=candidate.evaluated_at or audit.evaluated_at,
                )
            )
        session.commit()
        candidates = list(
            session.scalars(
                select(RouteReadinessCandidateAuditModel)
                .where(RouteReadinessCandidateAuditModel.route_readiness_audit_ref_id == model.id)
                .order_by(RouteReadinessCandidateAuditModel.binding_key.asc())
            ).all()
        )
        return self._route_readiness_audit_from_model(model, candidates)

    @classmethod
    def _route_readiness_audit_from_model(
        cls,
        model: RouteReadinessAuditModel,
        candidate_models: list[RouteReadinessCandidateAuditModel],
    ) -> RouteReadinessAudit:
        candidates = [
            RouteReadinessCandidateAudit(
                route_readiness_audit_id=candidate.route_readiness_audit_id,
                binding_ref_id=candidate.binding_ref_id,
                binding_key=candidate.binding_key,
                venue_account_ref_id=candidate.venue_account_ref_id,
                venue_account_key=candidate.venue_account_key,
                venue=candidate.venue,
                instrument_ref_id=candidate.instrument_ref_id,
                instrument_key=candidate.instrument_key,
                symbol=candidate.symbol,
                exchange_symbol=candidate.exchange_symbol,
                status=candidate.status,
                reason_codes=list(candidate.reason_codes_json or []),
                missing_data=list(candidate.missing_data_json or []),
                stale_data=list(candidate.stale_data_json or []),
                unsupported_data=list(candidate.unsupported_data_json or []),
                unavailable_data=list(candidate.unavailable_data_json or []),
                policy_blocks=list(candidate.policy_blocks_json or []),
                blocking_reasons=list(candidate.blocking_reasons_json or []),
                fact_snapshot=dict(candidate.fact_snapshot_json or {}),
                data_sources=dict(candidate.data_sources_json or {}),
                evaluated_at=candidate.evaluated_at,
            )
            for candidate in candidate_models
        ]
        return RouteReadinessAudit(
            route_readiness_audit_id=model.route_readiness_audit_id,
            environment=model.environment,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            routing_assessment_ref_id=model.routing_assessment_ref_id,
            routing_assessment_id=model.routing_assessment_id,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            instrument_ref_id=model.instrument_ref_id,
            instrument_key=model.instrument_key,
            symbol=model.symbol,
            action=model.action,
            target_scope=model.target_scope,
            evaluated_at=model.evaluated_at,
            overall_status=model.overall_status,
            candidate_count=model.candidate_count,
            ready_candidate_count=model.ready_candidate_count,
            blocked_candidate_count=model.blocked_candidate_count,
            insufficient_data_candidate_count=model.insufficient_data_candidate_count,
            global_reason_codes=list(model.global_reason_codes_json or []),
            global_missing_data=list(model.global_missing_data_json or []),
            global_stale_data=list(model.global_stale_data_json or []),
            global_blocking_reasons=list(model.global_blocking_reasons_json or []),
            candidates=candidates,
            non_selecting=model.non_selecting,
            recommendation_created=model.recommendation_created,
            target_choice_created=model.target_choice_created,
            child_intent_created=model.child_intent_created,
            submitted_order_created=model.submitted_order_created,
            provenance=dict(model.provenance_json or {}),
        )

    def _routing_target_recommendation_for_missing_audit(
        self,
        route_readiness_audit_id: str,
        *,
        created_at: datetime,
        policy_name: str,
    ) -> RoutingTargetRecommendation:
        return RoutingTargetRecommendation(
            routing_target_recommendation_id=f"rtreco_{uuid4().hex}",
            environment=self.settings.app.environment,
            route_readiness_audit_ref_id=None,
            route_readiness_audit_id=route_readiness_audit_id,
            routing_assessment_ref_id=None,
            routing_assessment_id=None,
            desired_trade_ref_id=None,
            desired_trade_key=None,
            client_ref_id=None,
            strategy_mandate_ref_id=None,
            mandate_key=None,
            instrument_ref_id=None,
            instrument_key=None,
            symbol=None,
            action=None,
            target_scope=None,
            status=RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_FOUND,
            policy_name=policy_name,
            candidate_count=0,
            ready_candidate_count=0,
            reason_codes=[
                "route_readiness_audit_not_found",
                "recommendation_blocked",
                "routing_target_recommendation_non_executing",
                policy_name,
            ],
            blocking_reasons=["route_readiness_audit_not_found"],
            non_executing=True,
            target_choice_created=False,
            child_intent_created=False,
            submitted_order_created=False,
            created_at=created_at,
            provenance=self._routing_target_recommendation_provenance(
                route_readiness_audit_id=route_readiness_audit_id,
                created_at=created_at,
                status=RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_FOUND,
                reason_codes=["route_readiness_audit_not_found"],
                policy_name=policy_name,
            ),
        )

    def _build_routing_target_recommendation(
        self,
        session: Any,
        audit_model: RouteReadinessAuditModel,
        candidate_models: list[RouteReadinessCandidateAuditModel],
        *,
        created_at: datetime,
        policy_name: str,
    ) -> RoutingTargetRecommendation:
        ready_candidates = [
            candidate
            for candidate in candidate_models
            if candidate.status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
        ]
        reason_codes = [
            "routing_target_recommendation_non_executing",
            policy_name,
            "target_choice_creation_deferred",
            "child_intent_creation_deferred",
            "submission_deferred",
        ]
        if policy_name == _ROUTING_TARGET_RECOMMENDATION_PRIORITY_POLICY:
            reason_codes.append("explicit_binding_priority_policy_requested")
        blocking_reasons: list[str] = []
        missing_data: list[str] = []
        stale_data: list[str] = []
        status = RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
        recommended_candidate: RouteReadinessCandidateAuditModel | None = None
        policy_facts: dict[str, object] = {
            "policy_name": policy_name,
            "default_policy": policy_name == _ROUTING_TARGET_RECOMMENDATION_POLICY,
            "priority_source": None,
            "priority_order": None,
            "selected_priority": None,
            "ready_candidate_priorities": [],
        }

        if audit_model.overall_status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION:
            reason_codes.extend(
                [
                    "route_readiness_audit_not_ready",
                    f"route_readiness_audit_status_{audit_model.overall_status.value}",
                ]
            )
            blocking_reasons.append("route_readiness_audit_not_ready")
        if audit_model.global_blocking_reasons_json:
            global_blockers = list(audit_model.global_blocking_reasons_json or [])
            reason_codes.append("route_readiness_audit_global_blockers_present")
            reason_codes.extend(global_blockers)
            blocking_reasons.extend(global_blockers)

        if policy_name not in _ROUTING_TARGET_RECOMMENDATION_ALLOWED_POLICIES:
            status = RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
            reason_codes.append("routing_target_recommendation_policy_unknown")
            blocking_reasons.append("routing_target_recommendation_policy_unknown")
            policy_facts["unknown_policy_name"] = policy_name
        elif self._route_readiness_audit_is_stale(audit_model, created_at):
            status = RoutingTargetRecommendationStatus.BLOCKED_STALE_AUDIT
            reason_codes.append("route_readiness_audit_stale")
            stale_data.append("route_readiness_audit_stale")
            blocking_reasons.append("route_readiness_audit_stale")
        elif len(ready_candidates) == 0:
            status = RoutingTargetRecommendationStatus.BLOCKED_NO_READY_CANDIDATE
            reason_codes.append("no_ready_candidate")
            blocking_reasons.append("no_ready_candidate")
        elif len(ready_candidates) > 1:
            if (
                audit_model.overall_status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
                or audit_model.global_blocking_reasons_json
            ):
                status = RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_READY
            elif policy_name == _ROUTING_TARGET_RECOMMENDATION_POLICY:
                status = RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES
                reason_codes.append("multiple_ready_candidates")
                reason_codes.append("multiple_ready_candidates_without_priority_policy")
                blocking_reasons.append("multiple_ready_candidates")
            else:
                (
                    recommended_candidate,
                    priority_reason_codes,
                    priority_missing_data,
                    priority_blocking_reasons,
                    priority_facts,
                    priority_status,
                ) = self._select_candidate_by_explicit_binding_priority(
                    session,
                    ready_candidates,
                )
                policy_facts.update(priority_facts)
                reason_codes.extend(priority_reason_codes)
                missing_data.extend(priority_missing_data)
                blocking_reasons.extend(priority_blocking_reasons)
                status = priority_status
        elif audit_model.overall_status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION:
            status = RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_READY
        elif audit_model.global_blocking_reasons_json:
            status = RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_READY
        elif policy_name == _ROUTING_TARGET_RECOMMENDATION_PRIORITY_POLICY:
            (
                recommended_candidate,
                priority_reason_codes,
                priority_missing_data,
                priority_blocking_reasons,
                priority_facts,
                priority_status,
            ) = self._select_candidate_by_explicit_binding_priority(
                session,
                ready_candidates,
            )
            policy_facts.update(priority_facts)
            reason_codes.extend(priority_reason_codes)
            missing_data.extend(priority_missing_data)
            blocking_reasons.extend(priority_blocking_reasons)
            status = priority_status
        else:
            recommended_candidate = ready_candidates[0]
            candidate_missing = self._routing_target_recommendation_candidate_required_missing(
                recommended_candidate
            )
            if candidate_missing:
                status = RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
                reason_codes.extend(candidate_missing)
                missing_data.extend(candidate_missing)
                blocking_reasons.append("recommended_candidate_required_fields_missing")
                recommended_candidate = None

        if (
            status == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
            and recommended_candidate is not None
        ):
            candidate_missing = self._routing_target_recommendation_candidate_required_missing(
                recommended_candidate
            )
            if candidate_missing:
                status = RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
                reason_codes.extend(candidate_missing)
                missing_data.extend(candidate_missing)
                blocking_reasons.append("recommended_candidate_required_fields_missing")
                recommended_candidate = None

        desired_trade_model = self._load_desired_trade_for_recommendation(session, audit_model)
        if (
            status == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
            and recommended_candidate is not None
        ):
            (
                quote_blockers,
                quote_missing,
                quote_stale,
                quote_status,
            ) = self._routing_target_recommendation_quote_freshness_blockers(
                recommended_candidate,
                created_at=created_at,
            )
            if quote_blockers or quote_missing or quote_stale:
                status = quote_status
                reason_codes.extend(quote_blockers)
                reason_codes.extend(quote_missing)
                reason_codes.extend(quote_stale)
                missing_data.extend(quote_missing)
                stale_data.extend(quote_stale)
                blocking_reasons.extend(quote_blockers)
                blocking_reasons.extend(quote_missing)
                blocking_reasons.extend(quote_stale)
                recommended_candidate = None
        if status == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE:
            desired_trade_blockers = self._routing_target_recommendation_desired_trade_blockers(
                session,
                desired_trade_model,
                audit_model,
            )
            if desired_trade_blockers:
                status = RoutingTargetRecommendationStatus.BLOCKED_STALE_DESIRED_TRADE
                reason_codes.extend(desired_trade_blockers)
                stale_data.extend(desired_trade_blockers)
                blocking_reasons.extend(desired_trade_blockers)
                recommended_candidate = None

        if (
            status == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
            and recommended_candidate is not None
        ):
            target_blockers, target_missing = self._routing_target_recommendation_target_blockers(
                session,
                recommended_candidate,
                audit_model,
                desired_trade_model,
            )
            if target_blockers or target_missing:
                status = RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
                reason_codes.extend(target_blockers)
                reason_codes.extend(target_missing)
                stale_data.extend(target_blockers)
                missing_data.extend(target_missing)
                blocking_reasons.extend(target_blockers)
                blocking_reasons.extend(target_missing)
                recommended_candidate = None

        if status == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE:
            reason_codes.append("recommended_single_ready_candidate")
        else:
            reason_codes.append("recommendation_blocked")

        return RoutingTargetRecommendation(
            routing_target_recommendation_id=f"rtreco_{uuid4().hex}",
            environment=audit_model.environment,
            route_readiness_audit_ref_id=audit_model.id,
            route_readiness_audit_id=audit_model.route_readiness_audit_id,
            routing_assessment_ref_id=audit_model.routing_assessment_ref_id,
            routing_assessment_id=audit_model.routing_assessment_id,
            desired_trade_ref_id=audit_model.desired_trade_ref_id,
            desired_trade_key=audit_model.desired_trade_key,
            client_ref_id=audit_model.client_ref_id,
            strategy_mandate_ref_id=audit_model.strategy_mandate_ref_id,
            mandate_key=audit_model.mandate_key,
            instrument_ref_id=audit_model.instrument_ref_id,
            instrument_key=audit_model.instrument_key,
            symbol=audit_model.symbol,
            action=audit_model.action,
            target_scope=audit_model.target_scope,
            status=status,
            policy_name=policy_name,
            recommended_binding_ref_id=(
                recommended_candidate.binding_ref_id if recommended_candidate is not None else None
            ),
            recommended_binding_key=(
                recommended_candidate.binding_key if recommended_candidate is not None else None
            ),
            recommended_venue_account_ref_id=(
                recommended_candidate.venue_account_ref_id if recommended_candidate is not None else None
            ),
            recommended_venue_account_key=(
                recommended_candidate.venue_account_key if recommended_candidate is not None else None
            ),
            recommended_venue=(
                recommended_candidate.venue if recommended_candidate is not None else None
            ),
            recommended_exchange_symbol=(
                recommended_candidate.exchange_symbol if recommended_candidate is not None else None
            ),
            candidate_count=len(candidate_models),
            ready_candidate_count=len(ready_candidates),
            reason_codes=sorted(set(reason_codes)),
            blocking_reasons=sorted(set(blocking_reasons)),
            missing_data=sorted(set(missing_data)),
            stale_data=sorted(set(stale_data)),
            non_executing=True,
            target_choice_created=False,
            child_intent_created=False,
            submitted_order_created=False,
            created_at=created_at,
            provenance=self._routing_target_recommendation_provenance(
                route_readiness_audit_id=audit_model.route_readiness_audit_id,
                created_at=created_at,
                status=status,
                reason_codes=reason_codes,
                policy_name=policy_name,
                policy_facts=policy_facts,
                audit_model=audit_model,
                recommended_candidate=recommended_candidate,
            ),
        )

    @staticmethod
    def _route_readiness_audit_is_stale(
        audit_model: RouteReadinessAuditModel,
        created_at: datetime,
    ) -> bool:
        evaluated_at = audit_model.evaluated_at
        if evaluated_at.tzinfo is None:
            evaluated_at = evaluated_at.replace(tzinfo=UTC)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        return created_at - evaluated_at > timedelta(
            seconds=_ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS
        )

    @staticmethod
    def _routing_target_recommendation_candidate_required_missing(
        candidate_model: RouteReadinessCandidateAuditModel,
    ) -> list[str]:
        missing: list[str] = []
        required_fields = {
            "recommended_binding_ref_missing": candidate_model.binding_ref_id,
            "recommended_binding_key_missing": candidate_model.binding_key,
            "recommended_venue_account_ref_missing": candidate_model.venue_account_ref_id,
            "recommended_venue_account_key_missing": candidate_model.venue_account_key,
            "recommended_venue_missing": candidate_model.venue,
            "recommended_exchange_symbol_missing": candidate_model.exchange_symbol,
        }
        for reason_code, value in required_fields.items():
            if value is None or value == "":
                missing.append(reason_code)
        return sorted(set(missing))

    def _select_candidate_by_explicit_binding_priority(
        self,
        session: Any,
        ready_candidates: list[RouteReadinessCandidateAuditModel],
    ) -> tuple[
        RouteReadinessCandidateAuditModel | None,
        list[str],
        list[str],
        list[str],
        dict[str, object],
        RoutingTargetRecommendationStatus,
    ]:
        reason_codes = ["explicit_binding_priority_policy_requested"]
        missing_data: list[str] = []
        blocking_reasons: list[str] = []
        priority_facts: dict[str, object] = {
            "priority_source": "mandate_account_bindings.target_recommendation_priority",
            "priority_order": "lower_integer_wins",
            "priority_min": _TARGET_RECOMMENDATION_PRIORITY_MIN,
            "priority_max": _TARGET_RECOMMENDATION_PRIORITY_MAX,
            "ready_candidate_priorities": [],
            "selected_priority": None,
        }
        candidate_priorities: list[tuple[RouteReadinessCandidateAuditModel, int]] = []

        for candidate in ready_candidates:
            binding_model = (
                session.get(MandateAccountBindingModel, candidate.binding_ref_id)
                if candidate.binding_ref_id is not None
                else None
            )
            if binding_model is None:
                reason_codes.append("binding_record_missing")
                reason_codes.append("binding_priority_missing")
                missing_data.append("binding_priority_missing")
                blocking_reasons.append("binding_record_missing")
                blocking_reasons.append("binding_priority_missing")
                priority_facts["ready_candidate_priorities"].append(
                    {
                        "binding_ref_id": candidate.binding_ref_id,
                        "binding_key": candidate.binding_key,
                        "priority": None,
                        "priority_status": "binding_missing",
                    }
                )
                continue

            priority = binding_model.target_recommendation_priority
            if priority is None:
                reason_codes.append("binding_priority_missing")
                missing_data.append("binding_priority_missing")
                blocking_reasons.append("binding_priority_missing")
                priority_facts["ready_candidate_priorities"].append(
                    {
                        "binding_ref_id": candidate.binding_ref_id,
                        "binding_key": candidate.binding_key,
                        "priority": None,
                        "priority_status": "missing",
                    }
                )
                continue
            if (
                not isinstance(priority, int)
                or isinstance(priority, bool)
                or priority < _TARGET_RECOMMENDATION_PRIORITY_MIN
                or priority > _TARGET_RECOMMENDATION_PRIORITY_MAX
            ):
                reason_codes.append("binding_priority_malformed")
                blocking_reasons.append("binding_priority_malformed")
                priority_facts["ready_candidate_priorities"].append(
                    {
                        "binding_ref_id": candidate.binding_ref_id,
                        "binding_key": candidate.binding_key,
                        "priority": str(priority),
                        "priority_status": "malformed",
                    }
                )
                continue

            candidate_priorities.append((candidate, priority))
            priority_facts["ready_candidate_priorities"].append(
                {
                    "binding_ref_id": candidate.binding_ref_id,
                    "binding_key": candidate.binding_key,
                    "priority": priority,
                    "priority_status": "usable",
                }
            )

        if missing_data or "binding_priority_malformed" in reason_codes or "binding_record_missing" in reason_codes:
            return (
                None,
                sorted(set(reason_codes)),
                sorted(set(missing_data)),
                sorted(set(blocking_reasons)),
                priority_facts,
                RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT,
            )

        if not candidate_priorities:
            reason_codes.append("binding_priority_missing")
            missing_data.append("binding_priority_missing")
            blocking_reasons.append("binding_priority_missing")
            return (
                None,
                sorted(set(reason_codes)),
                sorted(set(missing_data)),
                sorted(set(blocking_reasons)),
                priority_facts,
                RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT,
            )

        selected_priority = min(priority for _, priority in candidate_priorities)
        selected_candidates = [
            candidate
            for candidate, priority in candidate_priorities
            if priority == selected_priority
        ]
        priority_facts["selected_priority"] = selected_priority
        if len(selected_candidates) != 1:
            reason_codes.append("binding_priority_tie")
            blocking_reasons.append("binding_priority_tie")
            return (
                None,
                sorted(set(reason_codes)),
                [],
                sorted(set(blocking_reasons)),
                priority_facts,
                RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES,
            )

        reason_codes.append("binding_priority_selected")
        return (
            selected_candidates[0],
            sorted(set(reason_codes)),
            [],
            [],
            priority_facts,
            RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE,
        )

    @classmethod
    def _routing_target_recommendation_quote_freshness_blockers(
        cls,
        candidate_model: RouteReadinessCandidateAuditModel,
        *,
        created_at: datetime,
    ) -> tuple[list[str], list[str], list[str], RoutingTargetRecommendationStatus]:
        fact_snapshot = dict(candidate_model.fact_snapshot_json or {})
        observed_at_raw = fact_snapshot.get("quote_observed_at")
        if observed_at_raw is None or observed_at_raw == "":
            return (
                ["quote_freshness_unknown"],
                ["quote_freshness_unknown"],
                [],
                RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT,
            )

        observed_at = cls._parse_recommendation_quote_observed_at(observed_at_raw)
        if observed_at is None:
            return (
                ["quote_observed_at_malformed"],
                ["quote_observed_at_malformed"],
                [],
                RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT,
            )

        threshold_seconds = cls._recommendation_quote_freshness_threshold_seconds(
            fact_snapshot.get("quote_freshness_threshold_seconds")
        )
        if threshold_seconds is None:
            return (
                ["quote_freshness_threshold_invalid"],
                ["quote_freshness_threshold_invalid"],
                [],
                RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT,
            )

        created_at_aware = (
            created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
        )
        age_seconds = Decimal(str((created_at_aware - observed_at).total_seconds()))
        if age_seconds > threshold_seconds:
            return (
                ["quote_stale_at_recommendation"],
                [],
                ["quote_stale_at_recommendation"],
                RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE,
            )

        return (
            [],
            [],
            [],
            RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE,
        )

    @staticmethod
    def _parse_recommendation_quote_observed_at(value: object) -> datetime | None:
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                return None
            return value.astimezone(UTC)
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(UTC)

    @staticmethod
    def _recommendation_quote_freshness_threshold_seconds(value: object) -> Decimal | None:
        if value is None or value == "":
            return Decimal(str(_ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS))
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        try:
            if not parsed.is_finite() or parsed <= Decimal("0"):
                return None
        except InvalidOperation:
            return None
        return parsed

    def _load_desired_trade_for_recommendation(
        self,
        session: Any,
        audit_model: RouteReadinessAuditModel,
    ) -> MandateDesiredTradeModel | None:
        if audit_model.desired_trade_ref_id is not None:
            model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.environment == self.settings.app.environment,
                    MandateDesiredTradeModel.id == audit_model.desired_trade_ref_id,
                )
            )
            if model is not None:
                return model
        if audit_model.desired_trade_key is None:
            return None
        return session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.environment == self.settings.app.environment,
                MandateDesiredTradeModel.desired_trade_key == audit_model.desired_trade_key,
            )
        )

    def _routing_target_recommendation_desired_trade_blockers(
        self,
        session: Any,
        desired_trade_model: MandateDesiredTradeModel | None,
        audit_model: RouteReadinessAuditModel,
    ) -> list[str]:
        if desired_trade_model is None:
            return ["desired_trade_not_found"]
        reason_codes: list[str] = []
        mandate_model = self._load_strategy_mandate_for_recommendation(
            session,
            audit_model,
            desired_trade_model,
        )
        if mandate_model is None:
            reason_codes.append("mandate_missing")
        elif not mandate_model.enabled:
            reason_codes.append("mandate_inactive")
        if desired_trade_model.id != audit_model.desired_trade_ref_id:
            reason_codes.append("desired_trade_audit_ref_mismatch")
        if desired_trade_model.desired_trade_key != audit_model.desired_trade_key:
            reason_codes.append("desired_trade_audit_key_mismatch")
        if desired_trade_model.status != MandateDesiredTradeStatus.ROUTING_REQUIRED:
            reason_codes.append("desired_trade_not_routing_required")
        if desired_trade_model.target_scope != TradeTargetScope.MANDATE:
            reason_codes.append("desired_trade_not_mandate_scoped")
        if desired_trade_model.action != DecisionAction.OPEN:
            reason_codes.append("desired_trade_action_not_open")
        if desired_trade_model.side is None:
            reason_codes.append("desired_trade_missing_side")
        if desired_trade_model.desired_quantity is None:
            reason_codes.append("desired_trade_missing_quantity")
        elif not DefaultRoutingAssessmentService._decimal_is_positive_finite(
            desired_trade_model.desired_quantity
        ):
            reason_codes.append("desired_trade_invalid_quantity")
        if (
            desired_trade_model.mandate_account_binding_ref_id is not None
            or desired_trade_model.binding_key is not None
            or desired_trade_model.venue_account_ref_id is not None
        ):
            reason_codes.append("desired_trade_already_targeted")
        if desired_trade_model.client_ref_id != audit_model.client_ref_id:
            reason_codes.append("desired_trade_client_mismatch")
        if desired_trade_model.strategy_mandate_ref_id != audit_model.strategy_mandate_ref_id:
            reason_codes.append("desired_trade_strategy_mandate_mismatch")
        if desired_trade_model.mandate_key != audit_model.mandate_key:
            reason_codes.append("desired_trade_mandate_key_mismatch")
        if desired_trade_model.instrument_ref_id != audit_model.instrument_ref_id:
            reason_codes.append("desired_trade_instrument_ref_mismatch")
        if desired_trade_model.instrument_key != audit_model.instrument_key:
            reason_codes.append("desired_trade_instrument_key_mismatch")
        if desired_trade_model.symbol != audit_model.symbol:
            reason_codes.append("desired_trade_symbol_mismatch")
        symbol_id_blocker = self._desired_trade_symbol_id_blocker(
            session,
            desired_trade_model,
            audit_model,
        )
        if symbol_id_blocker is not None:
            reason_codes.append(symbol_id_blocker)
        return sorted(set(reason_codes))

    def _load_strategy_mandate_for_recommendation(
        self,
        session: Any,
        audit_model: RouteReadinessAuditModel,
        desired_trade_model: MandateDesiredTradeModel,
    ) -> StrategyMandateModel | None:
        mandate_ref_id = desired_trade_model.strategy_mandate_ref_id or audit_model.strategy_mandate_ref_id
        if mandate_ref_id is not None:
            statement = select(StrategyMandateModel).where(StrategyMandateModel.id == mandate_ref_id)
            if audit_model.client_ref_id is not None:
                statement = statement.where(
                    StrategyMandateModel.client_ref_id == audit_model.client_ref_id
                )
            mandate = session.scalar(statement)
            if mandate is not None:
                return mandate
        mandate_key = desired_trade_model.mandate_key or audit_model.mandate_key
        if mandate_key is None:
            return None
        statement = select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key)
        if audit_model.client_ref_id is not None:
            statement = statement.where(StrategyMandateModel.client_ref_id == audit_model.client_ref_id)
        return session.scalar(statement)

    @staticmethod
    def _desired_trade_symbol_id_blocker(
        session: Any,
        desired_trade_model: MandateDesiredTradeModel,
        audit_model: RouteReadinessAuditModel,
    ) -> str | None:
        if desired_trade_model.symbol_id is None:
            return None
        symbol_model = session.get(SymbolModel, desired_trade_model.symbol_id)
        if symbol_model is None:
            return "desired_trade_symbol_id_mismatch"
        if symbol_model.symbol != audit_model.symbol:
            return "desired_trade_symbol_id_mismatch"
        if (
            audit_model.instrument_ref_id is not None
            and symbol_model.instrument_ref_id != audit_model.instrument_ref_id
        ):
            return "desired_trade_symbol_id_mismatch"
        return None

    def _routing_target_recommendation_target_blockers(
        self,
        session: Any,
        candidate_model: RouteReadinessCandidateAuditModel,
        audit_model: RouteReadinessAuditModel,
        desired_trade_model: MandateDesiredTradeModel | None,
    ) -> tuple[list[str], list[str]]:
        reason_codes: list[str] = []
        missing_data: list[str] = []
        binding_model = (
            session.get(MandateAccountBindingModel, candidate_model.binding_ref_id)
            if candidate_model.binding_ref_id is not None
            else None
        )
        account_model = (
            session.get(VenueAccountModel, candidate_model.venue_account_ref_id)
            if candidate_model.venue_account_ref_id is not None
            else None
        )
        if binding_model is None:
            reason_codes.append("binding_record_missing")
        else:
            if binding_model.binding_key != candidate_model.binding_key:
                reason_codes.append("binding_key_mismatch")
            if not binding_model.enabled:
                reason_codes.append("binding_disabled")
            if not binding_model.trading_enabled:
                reason_codes.append("binding_trading_disabled")
            if not binding_model.routing_eligible:
                reason_codes.append("binding_not_routing_eligible")
            if binding_model.venue_account_ref_id != candidate_model.venue_account_ref_id:
                reason_codes.append("binding_venue_account_mismatch")
            if (
                desired_trade_model is not None
                and binding_model.strategy_mandate_ref_id
                != desired_trade_model.strategy_mandate_ref_id
            ):
                reason_codes.append("binding_strategy_mandate_mismatch")
            if binding_model.strategy_mandate_ref_id != audit_model.strategy_mandate_ref_id:
                reason_codes.append("binding_audit_mandate_mismatch")
        if account_model is None:
            reason_codes.append("venue_account_record_missing")
        else:
            if account_model.venue_account_key != candidate_model.venue_account_key:
                reason_codes.append("venue_account_key_mismatch")
            if account_model.venue != candidate_model.venue:
                reason_codes.append("venue_account_venue_mismatch")
            if not account_model.is_active:
                reason_codes.append("venue_account_inactive")
            if not account_model.trading_enabled:
                reason_codes.append("venue_account_trading_disabled")
            if (
                desired_trade_model is not None
                and account_model.client_ref_id != desired_trade_model.client_ref_id
            ):
                reason_codes.append("venue_account_client_mismatch")
        symbol_blockers, symbol_missing = self._route_readiness_candidate_symbol_mapping_blockers(
            session,
            candidate_model,
        )
        reason_codes.extend(symbol_blockers)
        missing_data.extend(symbol_missing)
        return sorted(set(reason_codes)), sorted(set(missing_data))

    @staticmethod
    def _route_readiness_candidate_symbol_mapping_blockers(
        session: Any,
        candidate_model: RouteReadinessCandidateAuditModel,
    ) -> tuple[list[str], list[str]]:
        if candidate_model.instrument_ref_id is None or candidate_model.exchange_symbol is None:
            return [], ["symbol_mapping_missing_or_changed"]
        symbol_model = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == candidate_model.instrument_ref_id,
                SymbolModel.venue == candidate_model.venue,
                SymbolModel.symbol == candidate_model.symbol,
                SymbolModel.exchange_symbol == candidate_model.exchange_symbol,
            )
        )
        if symbol_model is None:
            return [], ["symbol_mapping_missing_or_changed"]
        reason_codes: list[str] = []
        if not symbol_model.is_active:
            reason_codes.append("symbol_inactive")
        if not symbol_model.is_trading_eligible:
            reason_codes.append("symbol_not_trading_eligible")
        return sorted(set(reason_codes)), []

    @staticmethod
    def _routing_target_recommendation_provenance(
        *,
        route_readiness_audit_id: str,
        created_at: datetime,
        status: RoutingTargetRecommendationStatus,
        reason_codes: list[str],
        policy_name: str,
        policy_facts: dict[str, object] | None = None,
        audit_model: RouteReadinessAuditModel | None = None,
        recommended_candidate: RouteReadinessCandidateAuditModel | None = None,
    ) -> dict[str, object]:
        return {
            "phase": "phase_6_1",
            "boundary": "routing_target_recommendation_only",
            "policy_name": policy_name,
            "policy_facts": dict(policy_facts or {}),
            "route_readiness_audit_id": route_readiness_audit_id,
            "routing_assessment_id": audit_model.routing_assessment_id if audit_model is not None else None,
            "desired_trade_key": audit_model.desired_trade_key if audit_model is not None else None,
            "status": status.value,
            "reason_codes": sorted(set(reason_codes)),
            "created_at": created_at.isoformat(),
            "non_executing": True,
            "non_ranking": True,
            "non_scoring": True,
            "target_choice_created": False,
            "child_intent_created": False,
            "prepared_order_created": False,
            "readiness_assessment_created": False,
            "submitted_order_created": False,
            "default_policy": _ROUTING_TARGET_RECOMMENDATION_POLICY,
            "single_ready_candidate_only_behavior": "multiple_ready_candidates_block_without_explicit_policy",
            "explicit_binding_priority_behavior": "lower_operator_configured_integer_wins_when_requested",
            "recommended_candidate_source": (
                (
                    "explicit_binding_priority_ready_route_readiness_candidate"
                    if policy_name == _ROUTING_TARGET_RECOMMENDATION_PRIORITY_POLICY
                    else "single_ready_route_readiness_candidate"
                )
                if recommended_candidate is not None
                else None
            ),
        }

    def _persist_routing_target_recommendation(
        self,
        session: Any,
        recommendation: RoutingTargetRecommendation,
    ) -> RoutingTargetRecommendation:
        model = RoutingTargetRecommendationModel(
            environment=recommendation.environment,
            routing_target_recommendation_id=recommendation.routing_target_recommendation_id,
            route_readiness_audit_ref_id=recommendation.route_readiness_audit_ref_id,
            route_readiness_audit_id=recommendation.route_readiness_audit_id,
            routing_assessment_ref_id=recommendation.routing_assessment_ref_id,
            routing_assessment_id=recommendation.routing_assessment_id,
            desired_trade_ref_id=recommendation.desired_trade_ref_id,
            desired_trade_key=recommendation.desired_trade_key,
            client_ref_id=recommendation.client_ref_id,
            strategy_mandate_ref_id=recommendation.strategy_mandate_ref_id,
            mandate_key=recommendation.mandate_key,
            instrument_ref_id=recommendation.instrument_ref_id,
            instrument_key=recommendation.instrument_key,
            symbol=recommendation.symbol,
            action=recommendation.action,
            target_scope=recommendation.target_scope,
            status=recommendation.status,
            policy_name=recommendation.policy_name,
            recommended_binding_ref_id=recommendation.recommended_binding_ref_id,
            recommended_binding_key=recommendation.recommended_binding_key,
            recommended_venue_account_ref_id=recommendation.recommended_venue_account_ref_id,
            recommended_venue_account_key=recommendation.recommended_venue_account_key,
            recommended_venue=recommendation.recommended_venue,
            recommended_exchange_symbol=recommendation.recommended_exchange_symbol,
            candidate_count=recommendation.candidate_count,
            ready_candidate_count=recommendation.ready_candidate_count,
            reason_codes_json=list(recommendation.reason_codes),
            blocking_reasons_json=list(recommendation.blocking_reasons),
            missing_data_json=list(recommendation.missing_data),
            stale_data_json=list(recommendation.stale_data),
            non_executing=recommendation.non_executing,
            target_choice_created=recommendation.target_choice_created,
            child_intent_created=recommendation.child_intent_created,
            submitted_order_created=recommendation.submitted_order_created,
            provenance_json=self._jsonable_dict(recommendation.provenance),
            created_at=recommendation.created_at or _utcnow(),
        )
        session.add(model)
        if recommendation.route_readiness_audit_ref_id is not None:
            audit_model = session.get(
                RouteReadinessAuditModel,
                recommendation.route_readiness_audit_ref_id,
            )
            if audit_model is not None:
                audit_model.recommendation_created = True
        session.commit()
        return self._routing_target_recommendation_from_model(model)

    @staticmethod
    def _routing_target_recommendation_from_model(
        model: RoutingTargetRecommendationModel,
    ) -> RoutingTargetRecommendation:
        return RoutingTargetRecommendation(
            routing_target_recommendation_id=model.routing_target_recommendation_id,
            environment=model.environment,
            route_readiness_audit_ref_id=model.route_readiness_audit_ref_id,
            route_readiness_audit_id=model.route_readiness_audit_id,
            routing_assessment_ref_id=model.routing_assessment_ref_id,
            routing_assessment_id=model.routing_assessment_id,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_key=model.mandate_key,
            instrument_ref_id=model.instrument_ref_id,
            instrument_key=model.instrument_key,
            symbol=model.symbol,
            action=model.action,
            target_scope=model.target_scope,
            status=model.status,
            policy_name=model.policy_name,
            recommended_binding_ref_id=model.recommended_binding_ref_id,
            recommended_binding_key=model.recommended_binding_key,
            recommended_venue_account_ref_id=model.recommended_venue_account_ref_id,
            recommended_venue_account_key=model.recommended_venue_account_key,
            recommended_venue=model.recommended_venue,
            recommended_exchange_symbol=model.recommended_exchange_symbol,
            candidate_count=model.candidate_count,
            ready_candidate_count=model.ready_candidate_count,
            reason_codes=list(model.reason_codes_json or []),
            blocking_reasons=list(model.blocking_reasons_json or []),
            missing_data=list(model.missing_data_json or []),
            stale_data=list(model.stale_data_json or []),
            non_executing=model.non_executing,
            target_choice_created=model.target_choice_created,
            child_intent_created=model.child_intent_created,
            submitted_order_created=model.submitted_order_created,
            created_at=model.created_at,
            provenance=dict(model.provenance_json or {}),
        )

    @staticmethod
    def _recommendation_same_audit_idempotency_preflight_blockers(
        recommendation_model: RoutingTargetRecommendationModel,
    ) -> tuple[list[str], list[str]]:
        blockers: list[str] = []
        missing_data: list[str] = []
        if (
            recommendation_model.status
            != RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
        ):
            blockers.append("routing_target_recommendation_not_recommended")
        if not recommendation_model.non_executing:
            blockers.append("routing_target_recommendation_not_non_executing")
        if (
            recommendation_model.status
            == RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
            and recommendation_model.blocking_reasons_json
        ):
            blockers.append("routing_target_recommendation_has_blockers")

        required_fields = {
            "recommended_binding_ref_missing": recommendation_model.recommended_binding_ref_id,
            "recommended_binding_key_missing": recommendation_model.recommended_binding_key,
            "recommended_venue_account_ref_missing": (
                recommendation_model.recommended_venue_account_ref_id
            ),
            "recommended_venue_account_key_missing": (
                recommendation_model.recommended_venue_account_key
            ),
            "recommended_venue_missing": recommendation_model.recommended_venue,
            "recommended_exchange_symbol_missing": (
                recommendation_model.recommended_exchange_symbol
            ),
            "routing_assessment_id_missing": recommendation_model.routing_assessment_id,
            "route_readiness_audit_id_missing": recommendation_model.route_readiness_audit_id,
        }
        for reason_code, value in required_fields.items():
            if value is None or value == "":
                missing_data.append(reason_code)

        return sorted(set(blockers)), sorted(set(missing_data))

    def _target_choice_for_recommendation(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
    ) -> RoutingTargetChoiceModel | None:
        models = session.scalars(
            select(RoutingTargetChoiceModel)
            .where(
                RoutingTargetChoiceModel.environment == self.settings.app.environment,
                RoutingTargetChoiceModel.routing_assessment_id
                == recommendation_model.routing_assessment_id,
            )
            .order_by(RoutingTargetChoiceModel.created_at.asc())
        ).all()
        for model in models:
            provenance = dict(model.provenance_json or {})
            if (
                provenance.get("source") == "routing_target_recommendation"
                and provenance.get("routing_target_recommendation_id")
                == recommendation_model.routing_target_recommendation_id
            ):
                return model
        return None

    def _target_choice_for_route_readiness_audit(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
    ) -> RoutingTargetChoiceModel | None:
        if not recommendation_model.route_readiness_audit_id:
            return None
        query = (
            select(RoutingTargetChoiceModel)
            .where(
                RoutingTargetChoiceModel.environment == self.settings.app.environment,
                RoutingTargetChoiceModel.status
                == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED,
            )
            .order_by(RoutingTargetChoiceModel.created_at.asc())
        )
        if recommendation_model.routing_assessment_id:
            query = query.where(
                RoutingTargetChoiceModel.routing_assessment_id
                == recommendation_model.routing_assessment_id
            )
        models = session.scalars(query).all()
        for model in models:
            provenance = dict(model.provenance_json or {})
            if (
                provenance.get("source") == "routing_target_recommendation"
                and provenance.get("route_readiness_audit_id")
                == recommendation_model.route_readiness_audit_id
            ):
                return model
        return None

    def _recommendation_acceptance_blockers(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        *,
        accepted_at: datetime,
        allow_target_choice_created: bool = False,
    ) -> tuple[
        list[str],
        list[str],
        RouteReadinessAuditModel | None,
        RouteReadinessCandidateAuditModel | None,
        RoutingAssessmentCandidateModel | None,
    ]:
        blockers: list[str] = []
        missing_data: list[str] = []
        if (
            recommendation_model.status
            != RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
        ):
            blockers.append("routing_target_recommendation_not_recommended")
        if not recommendation_model.non_executing:
            blockers.append("routing_target_recommendation_not_non_executing")
        if recommendation_model.target_choice_created and not allow_target_choice_created:
            blockers.append("target_choice_already_created")

        required_fields = {
            "recommended_binding_ref_missing": recommendation_model.recommended_binding_ref_id,
            "recommended_binding_key_missing": recommendation_model.recommended_binding_key,
            "recommended_venue_account_ref_missing": (
                recommendation_model.recommended_venue_account_ref_id
            ),
            "recommended_venue_account_key_missing": (
                recommendation_model.recommended_venue_account_key
            ),
            "recommended_venue_missing": recommendation_model.recommended_venue,
            "recommended_exchange_symbol_missing": (
                recommendation_model.recommended_exchange_symbol
            ),
            "routing_assessment_id_missing": recommendation_model.routing_assessment_id,
            "route_readiness_audit_id_missing": recommendation_model.route_readiness_audit_id,
        }
        for reason_code, value in required_fields.items():
            if value is None or value == "":
                missing_data.append(reason_code)

        audit_model = self._load_route_readiness_audit_for_recommendation(
            session,
            recommendation_model,
        )
        if audit_model is None:
            blockers.append("route_readiness_audit_not_found")
            return sorted(set(blockers)), sorted(set(missing_data)), None, None, None

        if self._route_readiness_audit_is_stale(audit_model, accepted_at):
            blockers.append("route_readiness_audit_stale_at_acceptance")
        if audit_model.overall_status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION:
            blockers.append("route_readiness_audit_not_ready")
            blockers.append(f"route_readiness_audit_status_{audit_model.overall_status.value}")
        if audit_model.global_blocking_reasons_json:
            blockers.append("route_readiness_audit_global_blockers_present")
            blockers.extend(list(audit_model.global_blocking_reasons_json or []))
        if self._routing_target_recommendation_is_stale(
            recommendation_model,
            accepted_at,
        ):
            blockers.append("routing_target_recommendation_stale")

        candidate_model = self._route_readiness_candidate_for_recommendation(
            session,
            recommendation_model,
            audit_model,
        )
        if candidate_model is None:
            missing_data.append("recommended_candidate_not_found")
        else:
            if candidate_model.status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION:
                blockers.append("recommended_candidate_not_ready")
            candidate_mismatches = self._recommendation_candidate_identity_mismatches(
                recommendation_model,
                candidate_model,
            )
            blockers.extend(candidate_mismatches)
            (
                quote_blockers,
                quote_missing,
                quote_stale,
                _quote_status,
            ) = self._routing_target_recommendation_quote_freshness_blockers(
                candidate_model,
                created_at=accepted_at,
            )
            blockers.extend(quote_blockers)
            missing_data.extend(quote_missing)
            blockers.extend(quote_stale)

        desired_trade_model = self._load_desired_trade_for_recommendation(
            session,
            audit_model,
        )
        blockers.extend(
            self._routing_target_recommendation_desired_trade_blockers(
                session,
                desired_trade_model,
                audit_model,
            )
        )
        if candidate_model is not None:
            target_blockers, target_missing = self._routing_target_recommendation_target_blockers(
                session,
                candidate_model,
                audit_model,
                desired_trade_model,
            )
            blockers.extend(target_blockers)
            missing_data.extend(target_missing)

        assessment_model = self._load_assessment_for_recommendation_acceptance(
            session,
            recommendation_model,
            audit_model,
        )
        assessment_candidate_model: RoutingAssessmentCandidateModel | None = None
        if assessment_model is None:
            blockers.append("routing_assessment_not_found")
        else:
            assessment_blocker_status, assessment_blocker = self._assessment_target_choice_blocker(
                assessment_model
            )
            if assessment_blocker_status is not None and assessment_blocker is not None:
                blockers.append(assessment_blocker)
            assessment_candidate_model = self._assessment_candidate_for_recommendation(
                session,
                recommendation_model,
                audit_model,
                assessment_model,
                candidate_model,
            )
            if assessment_candidate_model is None:
                missing_data.append("routing_assessment_candidate_not_found")
            else:
                candidate_blockers, candidate_missing = self._candidate_target_choice_blockers(
                    assessment_candidate_model
                )
                blockers.extend(candidate_blockers)
                missing_data.extend(candidate_missing)
                blockers.extend(
                    self._assessment_candidate_recommendation_mismatches(
                        assessment_candidate_model,
                        recommendation_model,
                    )
                )

        return (
            sorted(set(blockers)),
            sorted(set(missing_data)),
            audit_model,
            candidate_model,
            assessment_candidate_model,
        )

    @staticmethod
    def _routing_target_recommendation_is_stale(
        recommendation_model: RoutingTargetRecommendationModel,
        accepted_at: datetime,
    ) -> bool:
        created_at = recommendation_model.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if accepted_at.tzinfo is None:
            accepted_at = accepted_at.replace(tzinfo=UTC)
        return accepted_at - created_at > timedelta(
            seconds=_ROUTE_READINESS_QUOTE_FRESHNESS_SECONDS
        )

    def _load_route_readiness_audit_for_recommendation(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
    ) -> RouteReadinessAuditModel | None:
        if recommendation_model.route_readiness_audit_ref_id is not None:
            model = session.get(
                RouteReadinessAuditModel,
                recommendation_model.route_readiness_audit_ref_id,
            )
            if model is not None:
                return model
        return session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.environment == self.settings.app.environment,
                RouteReadinessAuditModel.route_readiness_audit_id
                == recommendation_model.route_readiness_audit_id,
            )
        )

    def _route_readiness_candidate_for_recommendation(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        audit_model: RouteReadinessAuditModel,
    ) -> RouteReadinessCandidateAuditModel | None:
        if (
            recommendation_model.recommended_binding_ref_id is None
            or recommendation_model.recommended_binding_key is None
            or recommendation_model.recommended_venue_account_ref_id is None
            or recommendation_model.recommended_venue_account_key is None
            or recommendation_model.recommended_venue is None
            or recommendation_model.recommended_exchange_symbol is None
        ):
            return None
        return session.scalar(
            select(RouteReadinessCandidateAuditModel).where(
                RouteReadinessCandidateAuditModel.route_readiness_audit_ref_id == audit_model.id,
                RouteReadinessCandidateAuditModel.binding_ref_id
                == recommendation_model.recommended_binding_ref_id,
                RouteReadinessCandidateAuditModel.binding_key
                == recommendation_model.recommended_binding_key,
                RouteReadinessCandidateAuditModel.venue_account_ref_id
                == recommendation_model.recommended_venue_account_ref_id,
                RouteReadinessCandidateAuditModel.venue_account_key
                == recommendation_model.recommended_venue_account_key,
                RouteReadinessCandidateAuditModel.venue
                == recommendation_model.recommended_venue,
                RouteReadinessCandidateAuditModel.exchange_symbol
                == recommendation_model.recommended_exchange_symbol,
            )
        )

    @staticmethod
    def _recommendation_candidate_identity_mismatches(
        recommendation_model: RoutingTargetRecommendationModel,
        candidate_model: RouteReadinessCandidateAuditModel,
    ) -> list[str]:
        comparisons = {
            "recommended_candidate_binding_ref_mismatch": (
                recommendation_model.recommended_binding_ref_id,
                candidate_model.binding_ref_id,
            ),
            "recommended_candidate_binding_key_mismatch": (
                recommendation_model.recommended_binding_key,
                candidate_model.binding_key,
            ),
            "recommended_candidate_venue_account_ref_mismatch": (
                recommendation_model.recommended_venue_account_ref_id,
                candidate_model.venue_account_ref_id,
            ),
            "recommended_candidate_venue_account_key_mismatch": (
                recommendation_model.recommended_venue_account_key,
                candidate_model.venue_account_key,
            ),
            "recommended_candidate_venue_mismatch": (
                recommendation_model.recommended_venue,
                candidate_model.venue,
            ),
            "recommended_candidate_exchange_symbol_mismatch": (
                recommendation_model.recommended_exchange_symbol,
                candidate_model.exchange_symbol,
            ),
        }
        return sorted(
            reason_code for reason_code, (left, right) in comparisons.items() if left != right
        )

    def _load_assessment_for_recommendation_acceptance(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        audit_model: RouteReadinessAuditModel,
    ) -> RoutingAssessmentModel | None:
        assessment_ref_id = (
            recommendation_model.routing_assessment_ref_id or audit_model.routing_assessment_ref_id
        )
        if assessment_ref_id is not None:
            model = session.get(RoutingAssessmentModel, assessment_ref_id)
            if model is not None:
                return model
        assessment_id = recommendation_model.routing_assessment_id or audit_model.routing_assessment_id
        if assessment_id is None:
            return None
        return session.scalar(
            select(RoutingAssessmentModel).where(
                RoutingAssessmentModel.environment == self.settings.app.environment,
                RoutingAssessmentModel.assessment_id == assessment_id,
            )
        )

    @staticmethod
    def _assessment_candidate_for_recommendation(
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        audit_model: RouteReadinessAuditModel,
        assessment_model: RoutingAssessmentModel,
        candidate_model: RouteReadinessCandidateAuditModel | None,
    ) -> RoutingAssessmentCandidateModel | None:
        if candidate_model is not None and candidate_model.routing_assessment_candidate_ref_id is not None:
            assessment_candidate = session.get(
                RoutingAssessmentCandidateModel,
                candidate_model.routing_assessment_candidate_ref_id,
            )
            if assessment_candidate is not None:
                return assessment_candidate
        return session.scalar(
            select(RoutingAssessmentCandidateModel).where(
                RoutingAssessmentCandidateModel.assessment_ref_id == assessment_model.id,
                RoutingAssessmentCandidateModel.assessment_id
                == (recommendation_model.routing_assessment_id or audit_model.routing_assessment_id),
                RoutingAssessmentCandidateModel.binding_ref_id
                == recommendation_model.recommended_binding_ref_id,
                RoutingAssessmentCandidateModel.binding_key
                == recommendation_model.recommended_binding_key,
            )
        )

    @staticmethod
    def _assessment_candidate_recommendation_mismatches(
        assessment_candidate_model: RoutingAssessmentCandidateModel,
        recommendation_model: RoutingTargetRecommendationModel,
    ) -> list[str]:
        comparisons = {
            "assessment_candidate_binding_ref_mismatch": (
                assessment_candidate_model.binding_ref_id,
                recommendation_model.recommended_binding_ref_id,
            ),
            "assessment_candidate_binding_key_mismatch": (
                assessment_candidate_model.binding_key,
                recommendation_model.recommended_binding_key,
            ),
            "assessment_candidate_venue_account_ref_mismatch": (
                assessment_candidate_model.venue_account_ref_id,
                recommendation_model.recommended_venue_account_ref_id,
            ),
            "assessment_candidate_venue_account_key_mismatch": (
                assessment_candidate_model.venue_account_key,
                recommendation_model.recommended_venue_account_key,
            ),
            "assessment_candidate_venue_mismatch": (
                assessment_candidate_model.venue,
                recommendation_model.recommended_venue,
            ),
            "assessment_candidate_exchange_symbol_mismatch": (
                assessment_candidate_model.exchange_symbol,
                recommendation_model.recommended_exchange_symbol,
            ),
        }
        return sorted(
            reason_code for reason_code, (left, right) in comparisons.items() if left != right
        )

    def _mark_recommendation_target_choice_created(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        choice_model: RoutingTargetChoiceModel,
        *,
        accepted_at: datetime,
        idempotent: bool,
        existing_audit_target_choice: bool,
    ) -> None:
        recommendation_model.target_choice_created = True
        recommendation_provenance = dict(recommendation_model.provenance_json or {})
        choice_provenance = dict(choice_model.provenance_json or {})
        original_accepted_at = (
            recommendation_provenance.get("recommendation_accepted_at")
            or self._target_choice_original_acceptance_timestamp(choice_model)
            or accepted_at.isoformat()
        )
        current_recommendation_id = recommendation_model.routing_target_recommendation_id
        original_recommendation_id = choice_provenance.get("routing_target_recommendation_id")
        recommendation_provenance.update(
            {
                "phase": "phase_6_2",
                "target_choice_created": True,
                "routing_target_choice_id": choice_model.target_choice_id,
                "routing_target_choice_ref_id": choice_model.id,
                "recommendation_acceptance_idempotent": idempotent,
                "recommendation_accepted_at": str(original_accepted_at),
                "child_intent_created": False,
                "prepared_order_created": False,
                "readiness_assessment_created": False,
                "submitted_order_created": False,
            }
        )
        if idempotent:
            recommendation_provenance["recommendation_acceptance_last_checked_at"] = (
                accepted_at.isoformat()
            )
            recommendation_provenance["idempotent_reacceptance_checked_at"] = (
                accepted_at.isoformat()
            )
        if existing_audit_target_choice:
            recommendation_provenance.update(
                {
                    "route_readiness_audit_target_choice_already_created": True,
                    "recommendation_acceptance_existing_audit_target_choice": True,
                    "original_recommendation_accepted_at": str(original_accepted_at),
                }
            )
            if (
                isinstance(original_recommendation_id, str)
                and original_recommendation_id
                and original_recommendation_id != current_recommendation_id
            ):
                recommendation_provenance["original_routing_target_recommendation_id"] = (
                    original_recommendation_id
                )
        recommendation_model.provenance_json = self._jsonable_dict(recommendation_provenance)
        if recommendation_model.route_readiness_audit_ref_id is not None:
            audit_model = session.get(
                RouteReadinessAuditModel,
                recommendation_model.route_readiness_audit_ref_id,
            )
            if audit_model is not None:
                audit_model.target_choice_created = True
                audit_provenance = dict(audit_model.provenance_json or {})
                audit_original_accepted_at = (
                    audit_provenance.get("recommendation_accepted_at")
                    or original_accepted_at
                )
                audit_provenance.update(
                    {
                        "target_choice_created": True,
                        "routing_target_choice_id": choice_model.target_choice_id,
                        "recommendation_accepted_at": str(audit_original_accepted_at),
                    }
                )
                if "routing_target_recommendation_id" not in audit_provenance:
                    audit_provenance["routing_target_recommendation_id"] = (
                        current_recommendation_id
                    )
                if idempotent:
                    audit_provenance["recommendation_acceptance_last_checked_at"] = (
                        accepted_at.isoformat()
                    )
                    audit_provenance["idempotent_reacceptance_checked_at"] = (
                        accepted_at.isoformat()
                    )
                    audit_provenance[
                        "recommendation_acceptance_last_checked_recommendation_id"
                    ] = current_recommendation_id
                if existing_audit_target_choice:
                    audit_provenance.update(
                        {
                            "route_readiness_audit_target_choice_already_created": True,
                            "recommendation_acceptance_existing_audit_target_choice": True,
                            "original_recommendation_accepted_at": str(
                                audit_original_accepted_at
                            ),
                        }
                    )
                audit_model.provenance_json = self._jsonable_dict(audit_provenance)

    @staticmethod
    def _target_choice_original_acceptance_timestamp(
        choice_model: RoutingTargetChoiceModel,
    ) -> str | None:
        provenance = dict(choice_model.provenance_json or {})
        for key in ("recommendation_accepted_at", "accepted_at"):
            value = provenance.get(key)
            if isinstance(value, str) and value:
                return value
        if choice_model.selected_at is None:
            return None
        selected_at = choice_model.selected_at
        if selected_at.tzinfo is None:
            selected_at = selected_at.replace(tzinfo=UTC)
        return selected_at.isoformat()

    def _mark_recommendation_child_intent_created(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        choice_model: RoutingTargetChoiceModel,
        intent_model: OrderIntentModel,
        *,
        converted_at: datetime,
        idempotent: bool,
        existing_audit_child_intent: bool,
    ) -> None:
        if (
            recommendation_model.status
            != RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
        ):
            return
        recommendation_model.child_intent_created = True
        recommendation_provenance = dict(recommendation_model.provenance_json or {})
        original_converted_at = (
            recommendation_provenance.get("child_intent_converted_at")
            or dict(intent_model.provenance or {}).get("operator_conversion_at")
            or converted_at.isoformat()
        )
        recommendation_provenance.update(
            {
                "phase": "phase_6_3",
                "child_intent_created": True,
                "child_intent_id": intent_model.intent_id,
                "child_intent_ref_id": intent_model.id,
                "routing_target_choice_id": choice_model.target_choice_id,
                "routing_target_choice_ref_id": choice_model.id,
                "child_intent_converted_at": str(original_converted_at),
                "child_intent_conversion_idempotent": idempotent,
                "prepared_order_created": False,
                "readiness_assessment_created": False,
                "submitted_order_created": False,
            }
        )
        if idempotent:
            recommendation_provenance["child_intent_conversion_last_checked_at"] = (
                converted_at.isoformat()
            )
        if existing_audit_child_intent:
            recommendation_provenance.update(
                {
                    "route_readiness_audit_child_intent_already_created": True,
                    "recommendation_target_choice_child_intent_reused": True,
                }
            )
        recommendation_model.provenance_json = self._jsonable_dict(recommendation_provenance)

        audit_model: RouteReadinessAuditModel | None = None
        if recommendation_model.route_readiness_audit_ref_id is not None:
            audit_model = session.get(
                RouteReadinessAuditModel,
                recommendation_model.route_readiness_audit_ref_id,
            )
        if audit_model is None and recommendation_model.route_readiness_audit_id:
            audit_model = session.scalar(
                select(RouteReadinessAuditModel).where(
                    RouteReadinessAuditModel.environment == self.settings.app.environment,
                    RouteReadinessAuditModel.route_readiness_audit_id
                    == recommendation_model.route_readiness_audit_id,
                )
            )
        if audit_model is None:
            return
        audit_model.child_intent_created = True
        audit_provenance = dict(audit_model.provenance_json or {})
        audit_original_converted_at = (
            audit_provenance.get("child_intent_converted_at") or original_converted_at
        )
        audit_provenance.update(
            {
                "phase": "phase_6_3",
                "child_intent_created": True,
                "child_intent_id": intent_model.intent_id,
                "child_intent_ref_id": intent_model.id,
                "routing_target_choice_id": choice_model.target_choice_id,
                "child_intent_converted_at": str(audit_original_converted_at),
                "prepared_order_created": False,
                "readiness_assessment_created": False,
                "submitted_order_created": False,
            }
        )
        if "routing_target_recommendation_id" not in audit_provenance:
            audit_provenance["routing_target_recommendation_id"] = (
                recommendation_model.routing_target_recommendation_id
            )
        if idempotent:
            audit_provenance["child_intent_conversion_last_checked_at"] = (
                converted_at.isoformat()
            )
        if existing_audit_child_intent:
            audit_provenance.update(
                {
                    "route_readiness_audit_child_intent_already_created": True,
                    "recommendation_target_choice_child_intent_reused": True,
                }
            )
        audit_model.provenance_json = self._jsonable_dict(audit_provenance)

    @staticmethod
    def _assessment_target_choice_blocker(
        model: RoutingAssessmentModel,
    ) -> tuple[RoutingTargetChoiceStatus | None, str | None]:
        if model.decision_status == RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY:
            return None, None
        if model.decision_status == RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA:
            return (
                RoutingTargetChoiceStatus.BLOCKED_ASSESSMENT_INSUFFICIENT_DATA,
                "routing_assessment_insufficient_data",
            )
        if model.decision_status == RoutingAssessmentDecisionStatus.NO_ELIGIBLE_BINDINGS:
            return (
                RoutingTargetChoiceStatus.BLOCKED_NO_ELIGIBLE_BINDING,
                "routing_assessment_no_eligible_bindings",
            )
        return (
            RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT,
            "routing_assessment_not_assessment_only",
        )

    @staticmethod
    def _find_target_choice_candidate(
        session: Any,
        *,
        assessment_ref_id: str,
        binding_ref_id: str | None,
        binding_key: str | None,
    ) -> RoutingAssessmentCandidateModel | None:
        if binding_ref_id is None and binding_key is None:
            return None
        statement = select(RoutingAssessmentCandidateModel).where(
            RoutingAssessmentCandidateModel.assessment_ref_id == assessment_ref_id,
        )
        if binding_ref_id is not None:
            statement = statement.where(RoutingAssessmentCandidateModel.binding_ref_id == binding_ref_id)
        if binding_key is not None:
            statement = statement.where(RoutingAssessmentCandidateModel.binding_key == binding_key)
        return session.scalar(statement)

    @staticmethod
    def _candidate_target_choice_blockers(
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> tuple[list[str], list[str]]:
        reason_codes: list[str] = []
        missing_data = list(candidate_model.missing_data_json or [])
        if (
            candidate_model.eligibility_status
            != RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
        ):
            reason_codes.extend(list(candidate_model.reason_codes_json or []))
            reason_codes.append("routing_candidate_ineligible")
        if missing_data:
            reason_codes.append("routing_candidate_missing_data")
        if candidate_model.binding_ref_id is None:
            reason_codes.append("routing_candidate_missing_binding_ref")
        if candidate_model.venue_account_ref_id is None:
            reason_codes.append("routing_candidate_missing_venue_account_ref")
        return sorted(set(reason_codes)), sorted(set(missing_data))

    def _current_desired_trade_target_choice_blockers(
        self,
        session: Any,
        assessment_model: RoutingAssessmentModel,
    ) -> list[str]:
        desired_trade_model = None
        if assessment_model.desired_trade_ref_id is not None:
            desired_trade_model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.environment == self.settings.app.environment,
                    MandateDesiredTradeModel.id == assessment_model.desired_trade_ref_id,
                )
            )
        if desired_trade_model is None and assessment_model.desired_trade_key is not None:
            desired_trade_model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.environment == self.settings.app.environment,
                    MandateDesiredTradeModel.desired_trade_key == assessment_model.desired_trade_key,
                )
            )
        if desired_trade_model is None:
            return ["desired_trade_not_found"]

        reason_codes: list[str] = []
        if desired_trade_model.status != MandateDesiredTradeStatus.ROUTING_REQUIRED:
            reason_codes.append("desired_trade_not_routing_required")
        if desired_trade_model.target_scope != TradeTargetScope.MANDATE:
            reason_codes.append("desired_trade_not_mandate_scoped")
        if desired_trade_model.action != DecisionAction.OPEN:
            reason_codes.append("desired_trade_action_not_open")
        if (
            desired_trade_model.mandate_account_binding_ref_id is not None
            or desired_trade_model.binding_key is not None
            or desired_trade_model.venue_account_ref_id is not None
        ):
            reason_codes.append("desired_trade_already_targeted")
        return sorted(set(reason_codes))

    @staticmethod
    def _current_target_truth_blockers(
        session: Any,
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> list[str]:
        reason_codes: list[str] = []
        binding_model = (
            session.get(MandateAccountBindingModel, candidate_model.binding_ref_id)
            if candidate_model.binding_ref_id is not None
            else None
        )
        account_model = (
            session.get(VenueAccountModel, candidate_model.venue_account_ref_id)
            if candidate_model.venue_account_ref_id is not None
            else None
        )
        if binding_model is None:
            reason_codes.append("binding_record_missing")
        else:
            if not binding_model.enabled:
                reason_codes.append("binding_disabled")
            if not binding_model.trading_enabled:
                reason_codes.append("binding_trading_disabled")
            if not binding_model.routing_eligible:
                reason_codes.append("binding_not_routing_eligible")
        if account_model is None:
            reason_codes.append("venue_account_record_missing")
        else:
            if not account_model.is_active:
                reason_codes.append("venue_account_inactive")
            if not account_model.trading_enabled:
                reason_codes.append("venue_account_trading_disabled")
        return sorted(set(reason_codes))

    @staticmethod
    def _target_choice_conversion_idempotency_key(choice_model: RoutingTargetChoiceModel) -> str:
        return _json_fingerprint(
            {
                "environment": choice_model.environment.value,
                "routing_target_choice_id": choice_model.target_choice_id,
                "routing_assessment_id": choice_model.routing_assessment_id,
                "desired_trade_key": choice_model.desired_trade_key,
                "phase": "phase_5_2_target_choice_conversion",
            }
        )

    @staticmethod
    def _target_choice_conversion_blockers(
        choice_model: RoutingTargetChoiceModel,
    ) -> tuple[list[str], list[str]]:
        reason_codes: list[str] = []
        missing_data = sorted(set(choice_model.missing_data_json or []))
        if choice_model.status != RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED:
            reason_codes.append("routing_target_choice_not_recorded")
        if not choice_model.non_executing:
            reason_codes.append("routing_target_choice_not_non_executing")
        if choice_model.selected_binding_ref_id is None:
            reason_codes.append("target_choice_missing_binding_ref")
        if choice_model.selected_binding_key is None:
            reason_codes.append("target_choice_missing_binding_key")
        if choice_model.selected_venue_account_ref_id is None:
            reason_codes.append("target_choice_missing_venue_account_ref")
        if choice_model.selected_venue_account_key is None:
            reason_codes.append("target_choice_missing_venue_account_key")
        if choice_model.selected_venue is None:
            reason_codes.append("target_choice_missing_venue")
        if missing_data:
            reason_codes.append("target_choice_missing_data")
        blocking_reasons = sorted(
            set(choice_model.reason_codes_json or []) - _NON_BLOCKING_TARGET_CHOICE_REASONS
        )
        if blocking_reasons:
            reason_codes.append("target_choice_has_blocking_reason_codes")
            reason_codes.extend(blocking_reasons)
        return sorted(set(reason_codes)), missing_data

    @staticmethod
    def _target_choice_is_recommendation_backed(
        choice_model: RoutingTargetChoiceModel,
    ) -> bool:
        provenance = dict(choice_model.provenance_json or {})
        return (
            provenance.get("source") == "routing_target_recommendation"
            or isinstance(provenance.get("routing_target_recommendation_id"), str)
        )

    def _load_recommendation_for_target_choice(
        self,
        session: Any,
        choice_model: RoutingTargetChoiceModel,
    ) -> RoutingTargetRecommendationModel | None:
        provenance = dict(choice_model.provenance_json or {})
        recommendation_id = provenance.get("routing_target_recommendation_id")
        if not isinstance(recommendation_id, str) or not recommendation_id:
            return None
        return session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.environment == self.settings.app.environment,
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation_id,
            )
        )

    def _recommendation_backed_target_choice_preflight_blockers(
        self,
        session: Any,
        choice_model: RoutingTargetChoiceModel,
    ) -> tuple[list[str], list[str], RoutingTargetRecommendationModel | None]:
        provenance = dict(choice_model.provenance_json or {})
        blockers: list[str] = []
        missing_data: list[str] = []
        if provenance.get("source") != "routing_target_recommendation":
            blockers.append("target_choice_not_recommendation_backed")
        recommendation_id = provenance.get("routing_target_recommendation_id")
        if not isinstance(recommendation_id, str) or not recommendation_id:
            missing_data.append("routing_target_recommendation_id_missing")
            return sorted(set(blockers)), sorted(set(missing_data)), None
        recommendation_model = self._load_recommendation_for_target_choice(session, choice_model)
        if recommendation_model is None:
            blockers.append("routing_target_recommendation_not_found")
            return sorted(set(blockers)), sorted(set(missing_data)), None

        preflight_blockers, preflight_missing = (
            self._recommendation_same_audit_idempotency_preflight_blockers(
                recommendation_model
            )
        )
        blockers.extend(preflight_blockers)
        missing_data.extend(preflight_missing)
        if not recommendation_model.target_choice_created:
            blockers.append("routing_target_recommendation_target_choice_not_created")

        comparisons = {
            "target_choice_recommendation_id_mismatch": (
                recommendation_id,
                recommendation_model.routing_target_recommendation_id,
            ),
            "target_choice_recommendation_assessment_id_mismatch": (
                choice_model.routing_assessment_id,
                recommendation_model.routing_assessment_id,
            ),
            "target_choice_recommendation_desired_trade_key_mismatch": (
                choice_model.desired_trade_key,
                recommendation_model.desired_trade_key,
            ),
            "target_choice_recommendation_binding_ref_mismatch": (
                choice_model.selected_binding_ref_id,
                recommendation_model.recommended_binding_ref_id,
            ),
            "target_choice_recommendation_binding_key_mismatch": (
                choice_model.selected_binding_key,
                recommendation_model.recommended_binding_key,
            ),
            "target_choice_recommendation_venue_account_ref_mismatch": (
                choice_model.selected_venue_account_ref_id,
                recommendation_model.recommended_venue_account_ref_id,
            ),
            "target_choice_recommendation_venue_account_key_mismatch": (
                choice_model.selected_venue_account_key,
                recommendation_model.recommended_venue_account_key,
            ),
            "target_choice_recommendation_venue_mismatch": (
                choice_model.selected_venue,
                recommendation_model.recommended_venue,
            ),
            "target_choice_route_readiness_audit_id_mismatch": (
                provenance.get("route_readiness_audit_id"),
                recommendation_model.route_readiness_audit_id,
            ),
            "target_choice_recommended_exchange_symbol_mismatch": (
                provenance.get("recommended_exchange_symbol"),
                recommendation_model.recommended_exchange_symbol,
            ),
        }
        for reason_code, (left, right) in comparisons.items():
            if left != right:
                blockers.append(reason_code)
        required_provenance = {
            "target_choice_route_readiness_audit_id_missing": provenance.get(
                "route_readiness_audit_id"
            ),
            "target_choice_recommendation_policy_name_missing": provenance.get("policy_name"),
            "target_choice_recommended_exchange_symbol_missing": provenance.get(
                "recommended_exchange_symbol"
            ),
        }
        for reason_code, value in required_provenance.items():
            if value is None or value == "":
                missing_data.append(reason_code)
        return sorted(set(blockers)), sorted(set(missing_data)), recommendation_model

    def _recommendation_backed_target_choice_current_blockers(
        self,
        session: Any,
        recommendation_model: RoutingTargetRecommendationModel,
        *,
        converted_at: datetime,
    ) -> tuple[list[str], list[str]]:
        blockers, missing_data, _audit, _candidate, _assessment_candidate = (
            self._recommendation_acceptance_blockers(
                session,
                recommendation_model,
                accepted_at=converted_at,
                allow_target_choice_created=True,
            )
        )
        return blockers, missing_data

    @staticmethod
    def _recommendation_backed_conversion_blocked_status(
        blockers: list[str],
    ) -> RoutingTargetChoiceConversionStatus:
        if "desired_trade_invalid_quantity" in blockers or "desired_trade_missing_side" in blockers:
            return RoutingTargetChoiceConversionStatus.BLOCKED_INVALID_DESIRED_TRADE
        if any(reason.startswith("desired_trade_") for reason in blockers):
            return RoutingTargetChoiceConversionStatus.BLOCKED_STALE_DESIRED_TRADE
        return RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET

    def _existing_child_intent_for_target_choice_context(
        self,
        session: Any,
        choice_model: RoutingTargetChoiceModel,
        recommendation_model: RoutingTargetRecommendationModel | None,
        *,
        exclude_idempotency_key: str | None = None,
    ) -> OrderIntentModel | None:
        if not choice_model.desired_trade_key:
            return None
        models = session.scalars(
            select(OrderIntentModel)
            .where(
                OrderIntentModel.environment == self.settings.app.environment,
                OrderIntentModel.desired_trade_key == choice_model.desired_trade_key,
            )
            .order_by(OrderIntentModel.created_at.asc())
        ).all()
        for model in models:
            if exclude_idempotency_key is not None and model.idempotency_key == exclude_idempotency_key:
                continue
            provenance = dict(model.provenance or {})
            if (
                recommendation_model is not None
                and provenance.get("route_readiness_audit_id")
                == recommendation_model.route_readiness_audit_id
            ):
                return model
            if provenance.get("routing_assessment_id") == choice_model.routing_assessment_id:
                return model
            if provenance.get("routing_target_choice_id") == choice_model.target_choice_id:
                return model
        return None

    @staticmethod
    def _load_assessment_for_target_choice(
        session: Any,
        choice_model: RoutingTargetChoiceModel,
    ) -> RoutingAssessmentModel | None:
        if choice_model.routing_assessment_ref_id is not None:
            model = session.get(RoutingAssessmentModel, choice_model.routing_assessment_ref_id)
            if model is not None:
                return model
        return session.scalar(
            select(RoutingAssessmentModel).where(
                RoutingAssessmentModel.environment == choice_model.environment,
                RoutingAssessmentModel.assessment_id == choice_model.routing_assessment_id,
            )
        )

    @staticmethod
    def _assessment_conversion_blockers(
        assessment_model: RoutingAssessmentModel,
        choice_model: RoutingTargetChoiceModel,
    ) -> list[str]:
        reason_codes: list[str] = []
        if (
            choice_model.routing_assessment_ref_id is not None
            and assessment_model.id != choice_model.routing_assessment_ref_id
        ):
            reason_codes.append("routing_assessment_ref_mismatch")
        if assessment_model.assessment_id != choice_model.routing_assessment_id:
            reason_codes.append("routing_assessment_id_mismatch")
        if assessment_model.environment != choice_model.environment:
            reason_codes.append("routing_assessment_environment_mismatch")
        return sorted(set(reason_codes))

    @staticmethod
    def _candidate_conversion_blockers(
        candidate_model: RoutingAssessmentCandidateModel,
        choice_model: RoutingTargetChoiceModel,
    ) -> tuple[list[str], list[str]]:
        reason_codes: list[str] = []
        missing_data = sorted(set(candidate_model.missing_data_json or []))
        if (
            candidate_model.eligibility_status
            != RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
        ):
            reason_codes.append("routing_candidate_ineligible")
            reason_codes.extend(list(candidate_model.reason_codes_json or []))
        if missing_data:
            reason_codes.append("routing_candidate_missing_data")
        comparisons = {
            "candidate_binding_ref_mismatch": (
                choice_model.selected_binding_ref_id,
                candidate_model.binding_ref_id,
            ),
            "candidate_binding_key_mismatch": (
                choice_model.selected_binding_key,
                candidate_model.binding_key,
            ),
            "candidate_venue_account_ref_mismatch": (
                choice_model.selected_venue_account_ref_id,
                candidate_model.venue_account_ref_id,
            ),
            "candidate_venue_account_key_mismatch": (
                choice_model.selected_venue_account_key,
                candidate_model.venue_account_key,
            ),
            "candidate_venue_mismatch": (choice_model.selected_venue, candidate_model.venue),
        }
        for reason_code, (left, right) in comparisons.items():
            if left != right:
                reason_codes.append(reason_code)
        if candidate_model.exchange_symbol is None:
            missing_data.append("missing_symbol_mapping")
        return sorted(set(reason_codes)), sorted(set(missing_data))

    def _load_desired_trade_for_target_choice(
        self,
        session: Any,
        choice_model: RoutingTargetChoiceModel,
        assessment_model: RoutingAssessmentModel,
    ) -> MandateDesiredTradeModel | None:
        if choice_model.desired_trade_ref_id is not None:
            model = session.get(MandateDesiredTradeModel, choice_model.desired_trade_ref_id)
            if model is not None:
                return model
        if assessment_model.desired_trade_ref_id is not None:
            model = session.get(MandateDesiredTradeModel, assessment_model.desired_trade_ref_id)
            if model is not None:
                return model
        desired_trade_key = choice_model.desired_trade_key or assessment_model.desired_trade_key
        if desired_trade_key is None:
            return None
        return session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.environment == self.settings.app.environment,
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )

    @staticmethod
    def _desired_trade_conversion_blockers(
        desired_trade_model: MandateDesiredTradeModel | None,
        choice_model: RoutingTargetChoiceModel,
        assessment_model: RoutingAssessmentModel,
    ) -> list[str]:
        if desired_trade_model is None:
            return ["desired_trade_not_found"]
        reason_codes: list[str] = []
        if (
            choice_model.desired_trade_ref_id is not None
            and desired_trade_model.id != choice_model.desired_trade_ref_id
        ):
            reason_codes.append("desired_trade_target_choice_ref_mismatch")
        if desired_trade_model.id != assessment_model.desired_trade_ref_id:
            reason_codes.append("desired_trade_assessment_ref_mismatch")
        if (
            choice_model.desired_trade_key is not None
            and desired_trade_model.desired_trade_key != choice_model.desired_trade_key
        ):
            reason_codes.append("desired_trade_target_choice_key_mismatch")
        if desired_trade_model.desired_trade_key != assessment_model.desired_trade_key:
            reason_codes.append("desired_trade_assessment_key_mismatch")
        if desired_trade_model.status != MandateDesiredTradeStatus.ROUTING_REQUIRED:
            reason_codes.append("desired_trade_not_routing_required")
        if desired_trade_model.target_scope != TradeTargetScope.MANDATE:
            reason_codes.append("desired_trade_not_mandate_scoped")
        if desired_trade_model.action != DecisionAction.OPEN:
            reason_codes.append("desired_trade_action_not_open")
        if (
            desired_trade_model.mandate_account_binding_ref_id is not None
            or desired_trade_model.binding_key is not None
            or desired_trade_model.venue_account_ref_id is not None
        ):
            reason_codes.append("desired_trade_already_targeted")
        if desired_trade_model.instrument_key != assessment_model.instrument_key:
            reason_codes.append("desired_trade_instrument_key_mismatch")
        if desired_trade_model.instrument_ref_id != assessment_model.instrument_ref_id:
            reason_codes.append("desired_trade_instrument_ref_mismatch")
        if desired_trade_model.action != assessment_model.action:
            reason_codes.append("desired_trade_action_assessment_mismatch")
        if desired_trade_model.target_scope != assessment_model.target_scope:
            reason_codes.append("desired_trade_scope_assessment_mismatch")
        if desired_trade_model.client_ref_id != assessment_model.client_ref_id:
            reason_codes.append("desired_trade_client_mismatch")
        if desired_trade_model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id:
            reason_codes.append("desired_trade_strategy_mandate_mismatch")
        if desired_trade_model.mandate_key != assessment_model.mandate_key:
            reason_codes.append("desired_trade_mandate_key_mismatch")
        if (
            desired_trade_model.market_data_source_policy_ref_id
            != assessment_model.market_data_source_policy_ref_id
        ):
            reason_codes.append("desired_trade_source_policy_mismatch")
        if desired_trade_model.planning_source_venue != assessment_model.planning_source_venue:
            reason_codes.append("desired_trade_planning_source_mismatch")
        if desired_trade_model.desired_quantity is None or desired_trade_model.desired_quantity <= Decimal("0"):
            reason_codes.append("desired_trade_invalid_quantity")
        if desired_trade_model.side is None and desired_trade_model.action not in {
            DecisionAction.OPEN,
            DecisionAction.ADD,
            DecisionAction.REDUCE,
            DecisionAction.CLOSE,
        }:
            reason_codes.append("desired_trade_missing_side")
        return sorted(set(reason_codes))

    def _current_conversion_target_blockers(
        self,
        session: Any,
        candidate_model: RoutingAssessmentCandidateModel,
        choice_model: RoutingTargetChoiceModel,
        assessment_model: RoutingAssessmentModel,
        desired_trade_model: MandateDesiredTradeModel,
    ) -> tuple[list[str], list[str]]:
        reason_codes = self._current_target_truth_blockers(session, candidate_model)
        missing_data: list[str] = []
        binding_model = (
            session.get(MandateAccountBindingModel, candidate_model.binding_ref_id)
            if candidate_model.binding_ref_id is not None
            else None
        )
        account_model = (
            session.get(VenueAccountModel, candidate_model.venue_account_ref_id)
            if candidate_model.venue_account_ref_id is not None
            else None
        )
        if binding_model is not None:
            if (
                binding_model.id != candidate_model.binding_ref_id
                or binding_model.binding_key != candidate_model.binding_key
            ):
                reason_codes.append("binding_candidate_mismatch")
            if (
                binding_model.id != choice_model.selected_binding_ref_id
                or binding_model.binding_key != choice_model.selected_binding_key
            ):
                reason_codes.append("binding_target_choice_mismatch")
            if (
                binding_model.venue_account_ref_id != candidate_model.venue_account_ref_id
                or binding_model.venue_account_ref_id != choice_model.selected_venue_account_ref_id
            ):
                reason_codes.append("binding_venue_account_mismatch")
            if (
                binding_model.strategy_mandate_ref_id != desired_trade_model.strategy_mandate_ref_id
                or binding_model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id
            ):
                reason_codes.append("binding_strategy_mandate_mismatch")
        if account_model is not None:
            if account_model.venue_account_key != candidate_model.venue_account_key:
                reason_codes.append("venue_account_key_mismatch")
            if account_model.venue != candidate_model.venue:
                reason_codes.append("venue_account_venue_mismatch")
            if choice_model.selected_venue is not None and account_model.venue != choice_model.selected_venue:
                reason_codes.append("target_choice_venue_mismatch")
        symbol_blockers, symbol_missing = self._assessment_candidate_symbol_mapping_blockers(
            session,
            candidate_model,
        )
        reason_codes.extend(symbol_blockers)
        missing_data.extend(symbol_missing)
        return sorted(set(reason_codes)), sorted(set(missing_data))

    @staticmethod
    def _assessment_candidate_symbol_mapping_blockers(
        session: Any,
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> tuple[list[str], list[str]]:
        if candidate_model.instrument_ref_id is None or candidate_model.exchange_symbol is None:
            return [], ["symbol_mapping_missing_or_changed"]
        symbol_model = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == candidate_model.instrument_ref_id,
                SymbolModel.venue == candidate_model.venue,
                SymbolModel.symbol == candidate_model.symbol,
                SymbolModel.exchange_symbol == candidate_model.exchange_symbol,
            )
        )
        if symbol_model is None:
            return [], ["symbol_mapping_missing_or_changed"]
        reason_codes: list[str] = []
        if not symbol_model.is_active:
            reason_codes.append("symbol_inactive")
        if not symbol_model.is_trading_eligible:
            reason_codes.append("symbol_not_trading_eligible")
        return sorted(set(reason_codes)), []

    @staticmethod
    def _side_for_action(action: DecisionAction) -> OrderSide | None:
        if action in {DecisionAction.OPEN, DecisionAction.ADD}:
            return OrderSide.BUY
        if action in {DecisionAction.REDUCE, DecisionAction.CLOSE}:
            return OrderSide.SELL
        return None

    @staticmethod
    def _coerce_requested_order_type(value: object | None) -> OrderType | None:
        if value is None:
            return None
        if isinstance(value, OrderType):
            return value
        try:
            return OrderType(str(value).lower())
        except ValueError:
            return None

    @staticmethod
    def _coerce_limit_price(value: object | None) -> tuple[Decimal | None, bool]:
        if value is None:
            return None, False
        try:
            price = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None, True
        if not price.is_finite():
            return None, True
        return price, False

    @staticmethod
    def _candidate_supported_order_types(
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> list[OrderType] | None:
        raw_values = (candidate_model.fact_snapshot_json or {}).get("supported_order_types")
        if not isinstance(raw_values, list):
            return None
        supported: list[OrderType] = []
        for raw_value in raw_values:
            try:
                supported.append(OrderType(str(raw_value).lower()))
            except ValueError:
                continue
        return supported

    @classmethod
    def _existing_child_intent_policy_mismatch(
        cls,
        existing_intent: OrderIntentModel,
        policy_input: RoutedOrderShapePolicyInput | None,
    ) -> bool:
        if policy_input is None:
            return False
        requested_order_type = cls._coerce_requested_order_type(policy_input.order_type)
        if policy_input.order_type is not None and requested_order_type is None:
            return True
        if requested_order_type is None:
            requested_order_type = OrderType.MARKET
        requested_limit_price, malformed_limit_price = cls._coerce_limit_price(
            policy_input.limit_price
        )
        if malformed_limit_price:
            return True
        requested_reduce_only = bool(policy_input.reduce_only)
        return (
            existing_intent.order_type != requested_order_type
            or existing_intent.limit_price != requested_limit_price
            or existing_intent.reduce_only != requested_reduce_only
        )

    @classmethod
    def _routed_order_shape_for_conversion(
        cls,
        desired_trade_model: MandateDesiredTradeModel,
        candidate_model: RoutingAssessmentCandidateModel,
        policy_input: RoutedOrderShapePolicyInput | None,
    ) -> RoutedOrderShapeDecision:
        reason_codes: list[str] = []
        warnings = ["slippage_guard_deferred"]
        policy_provided = policy_input is not None
        requested_order_type = (
            cls._coerce_requested_order_type(policy_input.order_type)
            if policy_input is not None
            else None
        )
        requested_limit_price, malformed_limit_price = cls._coerce_limit_price(
            policy_input.limit_price if policy_input is not None else None
        )
        requested_reduce_only = policy_input.reduce_only if policy_input is not None else None
        requested_by = policy_input.requested_by if policy_input is not None else None
        policy_source = (
            policy_input.policy_source
            if policy_input is not None and policy_input.policy_source is not None
            else ("operator_requested" if policy_provided else "current_default")
        )
        if policy_source not in {"current_default", "operator_requested"}:
            reason_codes.append("unsupported_routed_order_shape_policy_source")
        if policy_provided:
            reason_codes.append("routed_order_shape_policy_operator_requested")
        else:
            reason_codes.extend(
                [
                    "routed_order_shape_policy_defaulted",
                    "market_order_default_current_phase",
                ]
            )

        if policy_input is not None and policy_input.order_type is not None and requested_order_type is None:
            reason_codes.append("unsupported_routed_order_type")
        if requested_order_type is None:
            selected_order_type = OrderType.MARKET
        else:
            selected_order_type = requested_order_type
        if selected_order_type not in {OrderType.MARKET, OrderType.LIMIT}:
            reason_codes.append("unsupported_routed_order_type")

        selected_limit_price: Decimal | None = None
        if malformed_limit_price:
            reason_codes.append("malformed_limit_price")
        if selected_order_type == OrderType.MARKET:
            if requested_limit_price is not None:
                reason_codes.append("market_order_limit_price_not_allowed")
            else:
                reason_codes.append("market_order_requested" if policy_provided else "market_order_defaulted")
        elif selected_order_type == OrderType.LIMIT:
            reason_codes.append("limit_order_requested")
            if not malformed_limit_price:
                if requested_limit_price is None:
                    reason_codes.append("limit_price_missing")
                elif requested_limit_price <= Decimal("0"):
                    reason_codes.append("invalid_limit_price")
                else:
                    selected_limit_price = requested_limit_price
                    reason_codes.append("limit_price_explicit")
            supported_order_types = cls._candidate_supported_order_types(candidate_model)
            if supported_order_types is None:
                reason_codes.append("routed_order_type_support_unknown")
            elif OrderType.LIMIT not in supported_order_types:
                reason_codes.append("unsupported_routed_order_type")

        selected_reduce_only = False
        if requested_reduce_only is True:
            reason_codes.append("reduce_only_not_allowed_for_open")
        elif desired_trade_model.action == DecisionAction.OPEN:
            reason_codes.append("reduce_only_false_for_open")

        blocking_reason_codes = {
            "unsupported_routed_order_shape_policy_source",
            "unsupported_routed_order_type",
            "malformed_limit_price",
            "market_order_limit_price_not_allowed",
            "limit_price_missing",
            "invalid_limit_price",
            "routed_order_type_support_unknown",
            "reduce_only_not_allowed_for_open",
        }
        blocked = any(reason in blocking_reason_codes for reason in reason_codes)
        if blocked:
            reason_codes.append("routed_order_shape_policy_blocked")
        else:
            reason_codes.append("routed_order_shape_policy_accepted")
        return RoutedOrderShapeDecision(
            order_type=selected_order_type,
            limit_price=selected_limit_price,
            reduce_only=selected_reduce_only,
            policy_source=policy_source,
            requested_order_type=requested_order_type,
            requested_limit_price=requested_limit_price,
            requested_reduce_only=requested_reduce_only,
            requested_by=requested_by,
            reason_codes=sorted(set(reason_codes)),
            warnings=warnings,
            blocked=blocked,
        )

    def _persist_converted_child_intent(
        self,
        session: Any,
        *,
        choice_model: RoutingTargetChoiceModel,
        assessment_model: RoutingAssessmentModel,
        candidate_model: RoutingAssessmentCandidateModel,
        desired_trade_model: MandateDesiredTradeModel,
        order_shape: RoutedOrderShapeDecision,
        idempotency_key: str,
        created_at: datetime,
    ) -> OrderIntent:
        side = desired_trade_model.side or self._side_for_action(desired_trade_model.action)
        if side is None:
            raise ValueError("Target-choice conversion requires a deterministic side.")
        intent_id = f"intent-choice-{idempotency_key[:18]}"
        choice_provenance = dict(choice_model.provenance_json or {})
        recommendation_id = choice_provenance.get("routing_target_recommendation_id")
        route_readiness_audit_id = choice_provenance.get("route_readiness_audit_id")
        recommendation_policy_name = choice_provenance.get("policy_name")
        provenance = {
            "phase_boundary": (
                "phase_6_3_recommendation_target_choice_conversion"
                if choice_provenance.get("source") == "routing_target_recommendation"
                else "phase_5_2_target_choice_conversion"
            ),
            "conversion_non_submitting": True,
            "operator_triggered": True,
            "operator_conversion_at": created_at.isoformat(),
            "prepared_order_created": False,
            "readiness_assessment_created": False,
            "submitted_order_created": False,
            "fanout_created": False,
            "allocation_created": False,
            "auto_submit": False,
            "desired_trade_status_transition": "routing_required->routed",
            "desired_trade_key": desired_trade_model.desired_trade_key,
            "routing_assessment_ref_id": assessment_model.id,
            "routing_assessment_id": assessment_model.assessment_id,
            "routing_target_choice_ref_id": choice_model.id,
            "routing_target_choice_id": choice_model.target_choice_id,
            "target_choice_source": choice_provenance.get("source", "operator_explicit_binding"),
            "selected_binding_ref_id": candidate_model.binding_ref_id,
            "selected_binding_key": candidate_model.binding_key,
            "selected_venue_account_ref_id": candidate_model.venue_account_ref_id,
            "selected_venue_account_key": candidate_model.venue_account_key,
            "selected_venue": candidate_model.venue,
            "selected_exchange_symbol": candidate_model.exchange_symbol,
            "conversion_idempotency_key": idempotency_key,
            "routed_order_shape_policy": order_shape.provenance(),
        }
        if isinstance(recommendation_id, str) and recommendation_id:
            provenance.update(
                {
                    "routing_target_recommendation_id": recommendation_id,
                    "route_readiness_audit_id": route_readiness_audit_id,
                    "recommendation_policy_name": recommendation_policy_name,
                    "accepted_recommendation_target_choice_conversion": True,
                    "child_intent_created_from_accepted_recommendation": True,
                }
            )
        model = OrderIntentModel(
            environment=desired_trade_model.environment,
            intent_id=intent_id,
            decision_id=(
                desired_trade_model.source_decision_ids_json[0]
                if desired_trade_model.source_decision_ids_json
                else None
            ),
            action=desired_trade_model.action,
            mandate_desired_trade_ref_id=desired_trade_model.id,
            desired_trade_key=desired_trade_model.desired_trade_key,
            sleeve_id=desired_trade_model.component_key or "component",
            component_key=desired_trade_model.component_key,
            client_ref_id=desired_trade_model.client_ref_id,
            strategy_mandate_ref_id=desired_trade_model.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=candidate_model.binding_ref_id,
            binding_key=candidate_model.binding_key,
            venue_account_ref_id=candidate_model.venue_account_ref_id,
            instrument_key=desired_trade_model.instrument_key,
            instrument_ref_id=desired_trade_model.instrument_ref_id,
            symbol_id=self._lookup_symbol_id(
                session,
                candidate_model=candidate_model,
            ),
            symbol=desired_trade_model.symbol,
            side=side,
            order_type=order_shape.order_type,
            quantity=desired_trade_model.desired_quantity,
            limit_price=order_shape.limit_price,
            reduce_only=order_shape.reduce_only,
            ttl_seconds=self.settings.execution.default_order_ttl_seconds,
            status=OrderIntentStatus.PREPARED,
            idempotency_key=idempotency_key,
            provenance=provenance,
            created_at=created_at,
        )
        session.add(model)
        desired_trade_model.status = MandateDesiredTradeStatus.ROUTED
        desired_trade_model.status_reason_code = "converted_from_routing_target_choice"
        desired_trade_model.status_message = (
            "Target-choice conversion created one binding/account-targeted child intent; "
            "submission remains deferred."
        )
        session.add(desired_trade_model)
        session.flush()
        recommendation_model = self._load_recommendation_for_target_choice(session, choice_model)
        if recommendation_model is not None:
            self._mark_recommendation_child_intent_created(
                session,
                recommendation_model,
                choice_model,
                model,
                converted_at=created_at,
                idempotent=False,
                existing_audit_child_intent=False,
            )
        return self._order_intent_from_model(model)

    @staticmethod
    def _lookup_symbol_id(
        session: Any,
        *,
        candidate_model: RoutingAssessmentCandidateModel,
    ) -> str | None:
        if candidate_model.instrument_ref_id is None or candidate_model.exchange_symbol is None:
            return None
        return session.scalar(
            select(SymbolModel.id).where(
                SymbolModel.instrument_ref_id == candidate_model.instrument_ref_id,
                SymbolModel.venue == candidate_model.venue,
                SymbolModel.symbol == candidate_model.symbol,
                SymbolModel.exchange_symbol == candidate_model.exchange_symbol,
            )
        )

    @staticmethod
    def _order_intent_from_model(model: OrderIntentModel) -> OrderIntent:
        return OrderIntent(
            intent_id=model.intent_id,
            sleeve_id=model.sleeve_id,
            component_key=model.component_key,
            decision_id=model.decision_id or "",
            action=model.action,
            mandate_desired_trade_ref_id=model.mandate_desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            client_ref_id=model.client_ref_id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
            binding_key=model.binding_key,
            venue_account_ref_id=model.venue_account_ref_id,
            instrument_key=model.instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            environment=model.environment,
            side=model.side,
            order_type=model.order_type,
            quantity=model.quantity,
            limit_price=model.limit_price,
            reduce_only=model.reduce_only,
            ttl_seconds=model.ttl_seconds,
            status=model.status,
            idempotency_key=model.idempotency_key,
            created_at=model.created_at,
            provenance=dict(model.provenance or {}),
        )

    def _conversion_result(
        self,
        *,
        target_choice_id: str,
        status: RoutingTargetChoiceConversionStatus,
        reason_codes: list[str],
        converted_at: datetime,
        routing_assessment_id: str | None = None,
        desired_trade_key: str | None = None,
        missing_data: list[str] | None = None,
        child_intent: OrderIntent | None = None,
        order_shape_decision: RoutedOrderShapeDecision | None = None,
        child_intent_reused: bool = False,
    ) -> RoutingTargetChoiceConversionResult:
        child_intent_provenance = (
            dict(child_intent.provenance or {}) if child_intent is not None else {}
        )
        routed_order_shape_policy = dict(
            child_intent_provenance.get("routed_order_shape_policy") or {}
        )
        if order_shape_decision is not None:
            routed_order_shape_policy = order_shape_decision.provenance()
        routing_target_recommendation_id = child_intent_provenance.get(
            "routing_target_recommendation_id"
        )
        route_readiness_audit_id = child_intent_provenance.get("route_readiness_audit_id")
        selected_binding_ref_id = child_intent_provenance.get("selected_binding_ref_id")
        selected_binding_key = child_intent_provenance.get("selected_binding_key")
        selected_venue_account_ref_id = child_intent_provenance.get(
            "selected_venue_account_ref_id"
        )
        selected_venue_account_key = child_intent_provenance.get(
            "selected_venue_account_key"
        )
        selected_venue = child_intent_provenance.get("selected_venue")
        selected_exchange_symbol = child_intent_provenance.get("selected_exchange_symbol")
        child_intent_created = (
            status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
            and child_intent is not None
        )
        return RoutingTargetChoiceConversionResult(
            target_choice_id=target_choice_id,
            environment=self.settings.app.environment,
            status=status,
            routing_assessment_id=routing_assessment_id,
            desired_trade_key=desired_trade_key,
            routing_target_recommendation_id=(
                str(routing_target_recommendation_id)
                if routing_target_recommendation_id is not None
                else None
            ),
            route_readiness_audit_id=(
                str(route_readiness_audit_id) if route_readiness_audit_id is not None else None
            ),
            selected_binding_ref_id=(
                str(selected_binding_ref_id) if selected_binding_ref_id is not None else None
            ),
            selected_binding_key=(
                str(selected_binding_key) if selected_binding_key is not None else None
            ),
            selected_venue_account_ref_id=(
                str(selected_venue_account_ref_id)
                if selected_venue_account_ref_id is not None
                else None
            ),
            selected_venue_account_key=(
                str(selected_venue_account_key)
                if selected_venue_account_key is not None
                else None
            ),
            selected_venue=str(selected_venue) if selected_venue is not None else None,
            selected_exchange_symbol=(
                str(selected_exchange_symbol) if selected_exchange_symbol is not None else None
            ),
            intent_id=child_intent.intent_id if child_intent is not None else None,
            child_intent=child_intent,
            reason_codes=sorted(set(reason_codes)),
            missing_data=sorted(set(missing_data or [])),
            non_submitting=True,
            child_intent_created=child_intent_created,
            child_intent_reused=child_intent_reused,
            prepared_order_created=False,
            readiness_assessment_created=False,
            submitted_order_created=False,
            converted_at=converted_at,
            provenance={
                "phase": (
                    "phase_6_3"
                    if routing_target_recommendation_id is not None
                    else "phase_5_2"
                ),
                "boundary": "target_choice_to_one_child_intent_only",
                "target_choice_id": target_choice_id,
                "routing_target_recommendation_id": routing_target_recommendation_id,
                "route_readiness_audit_id": route_readiness_audit_id,
                "routing_assessment_id": routing_assessment_id,
                "desired_trade_key": desired_trade_key,
                "intent_id": child_intent.intent_id if child_intent is not None else None,
                "non_submitting": True,
                "child_intent_created": child_intent_created,
                "child_intent_reused": child_intent_reused,
                "selected_binding_ref_id": selected_binding_ref_id,
                "selected_binding_key": selected_binding_key,
                "selected_venue_account_ref_id": selected_venue_account_ref_id,
                "selected_venue_account_key": selected_venue_account_key,
                "selected_venue": selected_venue,
                "selected_exchange_symbol": selected_exchange_symbol,
                "prepared_order_created": False,
                "readiness_assessment_created": False,
                "submitted_order_created": False,
                "fanout_created": False,
                "allocation_created": False,
                "auto_submit": False,
                "routed_order_shape_policy": routed_order_shape_policy,
            },
        )

    def _persist_target_choice(
        self,
        session: Any,
        *,
        routing_assessment_id: str,
        routing_assessment_ref_id: str | None,
        desired_trade_ref_id: str | None,
        desired_trade_key: str | None,
        candidate_model: RoutingAssessmentCandidateModel | None,
        status: RoutingTargetChoiceStatus,
        reason_codes: list[str],
        missing_data: list[str],
        approval_note: str | None,
        requested_by: str | None,
        created_at: datetime,
        selected_at: datetime | None = None,
        provenance_extra: dict[str, object] | None = None,
    ) -> RoutingTargetChoice:
        provenance = {
            "phase": "phase_5_1",
            "boundary": "routing_target_choice_only",
            "non_executing": True,
            "order_intents_created": False,
            "submitted_orders_created": False,
            "desired_trade_status_unchanged": True,
            "target_choice_policy": "operator_explicit_binding",
            "approval_policy_enforced": False,
        }
        if provenance_extra:
            provenance.update(self._jsonable_dict(provenance_extra))
        model = RoutingTargetChoiceModel(
            environment=self.settings.app.environment,
            target_choice_id=f"rtchoice_{uuid4().hex}",
            routing_assessment_ref_id=routing_assessment_ref_id,
            routing_assessment_id=routing_assessment_id,
            desired_trade_ref_id=desired_trade_ref_id,
            desired_trade_key=desired_trade_key,
            selected_binding_ref_id=candidate_model.binding_ref_id if candidate_model is not None else None,
            selected_binding_key=candidate_model.binding_key if candidate_model is not None else None,
            selected_venue_account_ref_id=(
                candidate_model.venue_account_ref_id if candidate_model is not None else None
            ),
            selected_venue_account_key=(
                candidate_model.venue_account_key if candidate_model is not None else None
            ),
            selected_venue=candidate_model.venue if candidate_model is not None else None,
            status=status,
            reason_codes_json=sorted(set(reason_codes)),
            missing_data_json=sorted(set(missing_data)),
            approval_note=approval_note,
            requested_by=requested_by,
            non_executing=True,
            provenance_json=provenance,
            selected_at=selected_at,
            created_at=created_at,
        )
        session.add(model)
        session.commit()
        return self._target_choice_from_model(model)

    @staticmethod
    def _target_choice_from_model(model: RoutingTargetChoiceModel) -> RoutingTargetChoice:
        return RoutingTargetChoice(
            target_choice_id=model.target_choice_id,
            environment=model.environment,
            routing_assessment_ref_id=model.routing_assessment_ref_id,
            routing_assessment_id=model.routing_assessment_id,
            desired_trade_ref_id=model.desired_trade_ref_id,
            desired_trade_key=model.desired_trade_key,
            selected_binding_ref_id=model.selected_binding_ref_id,
            selected_binding_key=model.selected_binding_key,
            selected_venue_account_ref_id=model.selected_venue_account_ref_id,
            selected_venue_account_key=model.selected_venue_account_key,
            selected_venue=model.selected_venue,
            status=model.status,
            reason_codes=list(model.reason_codes_json or []),
            missing_data=list(model.missing_data_json or []),
            approval_note=model.approval_note,
            requested_by=model.requested_by,
            non_executing=model.non_executing,
            created_at=model.created_at,
            selected_at=model.selected_at,
            provenance=dict(model.provenance_json or {}),
        )

    def _load_desired_trade_model(self, session: Any, desired_trade_key: str) -> MandateDesiredTradeModel:
        model = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.environment == self.settings.app.environment,
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        if model is None:
            raise RoutingAssessmentError(
                "desired_trade_not_found",
                f"Mandate desired trade not found: {desired_trade_key}",
            )
        return model
