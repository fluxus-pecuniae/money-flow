"""Execution service for downstream child-intent preparation and readiness gating."""

from __future__ import annotations

from dataclasses import asdict, replace
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    DecisionAction,
    ExecutionReadinessOutcome,
    MandateDesiredTradeStatus,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    RouteReadinessAuditStatus,
    RoutingAssessmentDecisionStatus,
    RoutingCandidateEligibilityStatus,
    RoutingTargetRecommendationStatus,
    RoutingTargetChoiceStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderRecoveryCategory,
    SubmittedOrderStatus,
    TradeTargetScope,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.models import (
    BindingRoutingCandidate,
    ExecutionReadinessAssessment,
    Fill,
    MandateDesiredTrade,
    OrderIntent,
    PreparedVenueOrder,
    SubmittedOrder,
    SubmittedOrderActionability,
    SubmittedOrderLifecycleEvent,
    SubmittedOrderLifecycleUpdate,
    SubmittedOrderRecoveryExecutionResult,
    SubmittedOrderRecoveryRecommendation,
    SubmittedOrderRoutedLifecycleContext,
)
from core.domain.routed_lifecycle import (
    submitted_order_routed_lifecycle_context_from_raw_payload,
)
from core.interfaces.services import ExecutionService, VenueRegistryService
from db.models import (
    ExecutionReadinessEvaluationModel,
    FillModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    OrderIntentSubmissionLeaseModel,
    RouteReadinessAuditModel,
    RouteReadinessCandidateAuditModel,
    RoutingAssessmentCandidateModel,
    RoutingAssessmentModel,
    RoutingTargetRecommendationModel,
    RoutingTargetChoiceModel,
    StrategyMandateModel,
    SubmittedOrderLifecycleEventModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from db.session import SessionLocal
from services.exchange.base import VenueAdapterError
from services.exchange.registry import DefaultVenueRegistryService


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _jsonable(payload: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(payload, default=str))


_ROUTED_QUOTE_FRESHNESS_SECONDS = 60
_SUBMISSION_LEASE_PURPOSE = "explicit_child_intent_submit"
_SUBMISSION_LEASE_TTL_SECONDS = 15 * 60
_SUBMISSION_LEASE_STATUS_UNCERTAIN = "adapter_submit_persistence_unknown"
_SUBMISSION_LEASE_STATUS_ADAPTER_MAY_HAVE_STARTED = "adapter_submit_may_have_started"
_SUBMISSION_LEASE_TERMINAL_UNCERTAIN_STATUSES = {
    _SUBMISSION_LEASE_STATUS_UNCERTAIN,
    _SUBMISSION_LEASE_STATUS_ADAPTER_MAY_HAVE_STARTED,
}
_PRE_ADAPTER_SAFE_FAILURE_REASON_CODES = {
    "account_identifier_missing",
    "account_not_authorized",
    "adapter_submission_unimplemented",
    "credentials_missing",
    "dry_run_only",
    "read_only_mode_enabled",
    "submission_endpoint_missing",
    "venue_integration_disabled",
    "venue_not_execution_preparable",
    "venue_submission_not_enabled",
}


class ChildIntentPreparationError(ValueError):
    def __init__(self, preview: PreparedVenueOrder) -> None:
        reason = preview.reason_codes[0] if preview.reason_codes else "child_intent_not_preparable"
        super().__init__(f"Child intent is not venue-preparable: {reason}")
        self.preview = preview


class SubmissionBlockedError(RuntimeError):
    def __init__(
        self,
        intent_id: str,
        readiness: ExecutionReadinessAssessment,
    ) -> None:
        super().__init__(
            "Child intent is not eligible for submission: "
            f"{readiness.outcome.value} ({', '.join(readiness.reason_codes) or 'no_reason'})"
        )
        self.intent_id = intent_id
        self.readiness = readiness


class SubmissionFailedError(RuntimeError):
    def __init__(
        self,
        *,
        intent_id: str,
        venue: str,
        reason_codes: list[str],
        message: str,
    ) -> None:
        super().__init__(message)
        self.intent_id = intent_id
        self.venue = venue
        self.reason_codes = list(reason_codes)


class SubmittedOrderActionError(RuntimeError):
    def __init__(self, submitted_order_id: str, message: str) -> None:
        super().__init__(message)
        self.submitted_order_id = submitted_order_id


class DefaultExecutionService(ExecutionService):
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        venue_registry_service: VenueRegistryService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self.venue_registry_service = venue_registry_service or DefaultVenueRegistryService(
            self.settings,
            session_factory=session_factory,
        )

    async def create_child_intent(
        self,
        desired_trade: MandateDesiredTrade,
        candidate: BindingRoutingCandidate,
    ) -> OrderIntent:
        if desired_trade.target_scope.value != "binding":
            raise ValueError("Child intents require a binding-scoped desired trade.")
        if desired_trade.desired_quantity is None or desired_trade.desired_quantity <= Decimal("0"):
            raise ValueError("Child intents require a positive desired quantity.")
        binding_key = desired_trade.binding_key or candidate.binding_key
        if not binding_key or not candidate.venue_account_ref_id:
            raise ValueError("Child intents require explicit binding/account targeting.")

        draft_intent = self._draft_child_intent(desired_trade=desired_trade, candidate=candidate)
        idempotency_key = _json_fingerprint(
            {
                "environment": draft_intent.environment.value,
                "desired_trade_key": draft_intent.desired_trade_key,
                "binding_key": draft_intent.binding_key,
                "venue_account_ref_id": draft_intent.venue_account_ref_id,
                "instrument_key": draft_intent.instrument_key,
                "instrument_ref_id": draft_intent.instrument_ref_id,
                "action": draft_intent.action.value if draft_intent.action is not None else None,
                "side": draft_intent.side.value,
                "quantity": str(draft_intent.quantity),
                "order_type": draft_intent.order_type.value,
                "reduce_only": draft_intent.reduce_only,
            }
        )
        draft_intent.intent_id = f"intent-{idempotency_key[:24]}"
        draft_intent.idempotency_key = idempotency_key
        preview = await self._prepare_preview_for_intent(draft_intent, venue=candidate.venue)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE:
            raise ChildIntentPreparationError(preview)

        with self._session_factory() as session:
            existing = session.scalar(
                select(OrderIntentModel).where(OrderIntentModel.idempotency_key == idempotency_key)
            )
            if existing is not None:
                if "prepared_order_preview" not in (existing.provenance or {}):
                    existing.provenance = {
                        **dict(existing.provenance or {}),
                        "prepared_order_preview": self._preview_summary(preview),
                    }
                    session.add(existing)
                    session.commit()
                return self._order_intent_from_model(existing)

            now_value = _utcnow()
            model = OrderIntentModel(
                environment=draft_intent.environment,
                intent_id=f"intent-{idempotency_key[:24]}",
                decision_id=draft_intent.decision_id,
                action=draft_intent.action,
                mandate_desired_trade_ref_id=draft_intent.mandate_desired_trade_ref_id,
                desired_trade_key=draft_intent.desired_trade_key,
                sleeve_id=draft_intent.sleeve_id,
                component_key=draft_intent.component_key,
                client_ref_id=draft_intent.client_ref_id,
                strategy_mandate_ref_id=draft_intent.strategy_mandate_ref_id,
                mandate_account_binding_ref_id=draft_intent.mandate_account_binding_ref_id,
                binding_key=draft_intent.binding_key,
                venue_account_ref_id=draft_intent.venue_account_ref_id,
                instrument_key=draft_intent.instrument_key,
                instrument_ref_id=draft_intent.instrument_ref_id,
                symbol_id=self._lookup_symbol_id(
                    session,
                    instrument_ref_id=draft_intent.instrument_ref_id,
                    venue=candidate.venue,
                    symbol=draft_intent.symbol,
                ),
                symbol=draft_intent.symbol,
                side=draft_intent.side,
                order_type=draft_intent.order_type,
                quantity=draft_intent.quantity,
                limit_price=draft_intent.limit_price,
                reduce_only=draft_intent.reduce_only,
                ttl_seconds=self.settings.execution.default_order_ttl_seconds,
                status=OrderIntentStatus.PREPARED,
                idempotency_key=idempotency_key,
                provenance={
                    "phase_boundary": "phase_4_1_1",
                    "desired_trade_key": draft_intent.desired_trade_key,
                    "planning_source_venue": desired_trade.planning_source_venue,
                    "binding_key": draft_intent.binding_key,
                    "candidate_venue": candidate.venue,
                    "candidate_eligibility_reasons": list(candidate.eligibility_reasons),
                    "execution_submission_deferred": True,
                    "prepared_order_preview": self._preview_summary(preview),
                },
                created_at=now_value,
            )
            session.add(model)
            session.commit()
            return self._order_intent_from_model(model)

    async def list_child_intents(
        self,
        *,
        desired_trade_key: str | None = None,
        binding_key: str | None = None,
        limit: int = 100,
    ) -> Sequence[OrderIntent]:
        with self._session_factory() as session:
            query = select(OrderIntentModel).where(
                OrderIntentModel.environment == self.settings.app.environment
            )
            if desired_trade_key is not None:
                query = query.where(OrderIntentModel.desired_trade_key == desired_trade_key)
            if binding_key is not None:
                query = query.where(OrderIntentModel.binding_key == binding_key)
            models = session.scalars(
                query.order_by(OrderIntentModel.created_at.desc()).limit(limit)
            ).all()
        return [self._order_intent_from_model(model) for model in models]

    async def get_child_intent(self, intent_id: str) -> OrderIntent:
        with self._session_factory() as session:
            model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == intent_id,
                )
            )
            if model is None:
                raise ValueError(f"Child intent not found: {intent_id}")
            return self._order_intent_from_model(model)

    async def submit_prepared_intent(self, intent: OrderIntent) -> SubmittedOrder:
        current_intent = await self.get_child_intent(intent.intent_id)
        if current_intent.venue_account_ref_id is None or current_intent.binding_key is None:
            raise ValueError(
                "Only binding/account-targeted child intents can be submitted. "
                "Mandate-scoped OPEN desired trades must remain above routing."
            )
        with self._session_factory() as session:
            existing = session.scalar(
                select(SubmittedOrderModel).where(
                    SubmittedOrderModel.environment == self.settings.app.environment,
                    SubmittedOrderModel.intent_id == current_intent.intent_id,
                )
            )
            if existing is not None:
                return self._submitted_order_from_model(existing)
        readiness = await self.assess_child_intent_readiness(intent.intent_id)
        if readiness.outcome != ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION:
            preserve_phase_block_status = self._is_routed_phase_boundary_submission_block(readiness)
            await self._record_submission_block(
                intent_id=current_intent.intent_id,
                readiness=readiness,
                reason_codes=list(readiness.reason_codes or [readiness.outcome.value]),
                message=readiness.message
                or "Child intent did not satisfy submission readiness requirements.",
                preserve_status=preserve_phase_block_status,
                failure_key=(
                    "last_submission_block"
                    if preserve_phase_block_status
                    else "last_submission_failure"
                ),
            )
            raise SubmissionBlockedError(current_intent.intent_id, readiness)

        lease_id = self._acquire_intent_submission_lease(
            current_intent.intent_id,
            readiness=readiness,
        )
        with self._session_factory() as session:
            existing = session.scalar(
                select(SubmittedOrderModel).where(
                    SubmittedOrderModel.environment == self.settings.app.environment,
                    SubmittedOrderModel.intent_id == current_intent.intent_id,
                )
            )
            if existing is not None:
                self._release_intent_submission_lease(
                    current_intent.intent_id,
                    lease_id,
                    status="existing_submitted_order",
                    reason_code="submitted_order_already_exists",
                    metadata={"submitted_order_id": existing.submitted_order_id},
                )
                return self._submitted_order_from_model(existing)
            model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == current_intent.intent_id,
                )
            )
            if model is None:
                self._release_intent_submission_lease(
                    current_intent.intent_id,
                    lease_id,
                    status="failed",
                    reason_code="child_intent_missing_after_lease",
                )
                raise ValueError(f"Child intent not found: {current_intent.intent_id}")
            venue = self._resolve_venue_for_intent(session, model)
        try:
            adapter = await self.venue_registry_service.get_adapter(venue)
        except Exception:
            self._release_intent_submission_lease(
                current_intent.intent_id,
                lease_id,
                status="failed",
                reason_code="adapter_unavailable_before_submit",
                metadata={"venue": venue},
            )
            raise
        self._mark_intent_submission_lease_adapter_may_have_started(
            current_intent.intent_id,
            lease_id,
            readiness=readiness,
            venue=venue,
        )
        try:
            submitted = await adapter.submit_order(current_intent)
        except VenueAdapterError as exc:
            reason_codes = list(getattr(exc, "reason_codes", []) or ["submission_failed"])
            if self._is_pre_adapter_safe_failure(reason_codes):
                self._release_intent_submission_lease(
                    current_intent.intent_id,
                    lease_id,
                    status="failed",
                    reason_code=reason_codes[0],
                    metadata={
                        "venue": venue,
                        "adapter_submit_may_have_started": False,
                        "requires_reconciliation": False,
                    },
                )
            else:
                self._mark_intent_submission_lease_adapter_outcome_unknown(
                    current_intent.intent_id,
                    lease_id,
                    readiness=readiness,
                    venue=venue,
                    exception=exc,
                    reason_codes=reason_codes,
                )
            await self._mark_submission_failure(
                intent_id=current_intent.intent_id,
                readiness=readiness,
                reason_codes=reason_codes,
                message=str(exc),
                payload=getattr(exc, "payload", None),
            )
            raise SubmissionFailedError(
                intent_id=current_intent.intent_id,
                venue=venue,
                reason_codes=reason_codes,
                message=str(exc),
            ) from exc
        except Exception as exc:
            self._mark_intent_submission_lease_adapter_outcome_unknown(
                current_intent.intent_id,
                lease_id,
                readiness=readiness,
                venue=venue,
                exception=exc,
                reason_codes=["adapter_submit_outcome_unknown"],
            )
            raise
        try:
            submitted = self._submitted_order_with_routed_lineage(
                submitted,
                intent=current_intent,
                readiness=readiness,
            )
            persisted = self._persist_submitted_order(current_intent, readiness, submitted)
        except Exception as exc:
            self._mark_intent_submission_lease_uncertain(
                current_intent.intent_id,
                lease_id,
                readiness=readiness,
                venue=venue,
                submitted=submitted,
                exception=exc,
            )
            raise
        self._release_intent_submission_lease(
            current_intent.intent_id,
            lease_id,
            status="submitted",
            reason_code="submitted_order_persisted",
            metadata={"submitted_order_id": persisted.submitted_order_id, "venue": venue},
        )
        return persisted

    @staticmethod
    def _lease_expires_at_is_stale(expires_at: datetime, now_value: datetime) -> bool:
        comparable = expires_at
        if comparable.tzinfo is None:
            comparable = comparable.replace(tzinfo=UTC)
        return comparable <= now_value

    @staticmethod
    def _submission_in_progress_readiness(
        readiness: ExecutionReadinessAssessment,
        lease: OrderIntentSubmissionLeaseModel | None,
    ) -> ExecutionReadinessAssessment:
        reason_codes = list(readiness.reason_codes or [])
        if "submission_in_progress" not in reason_codes:
            reason_codes.append("submission_in_progress")
        provenance = dict(readiness.provenance or {})
        provenance["submission_lease"] = {
            "purpose": _SUBMISSION_LEASE_PURPOSE,
            "status": "active",
            "lease_id": lease.lease_id if lease is not None else None,
            "acquired_at": lease.acquired_at.isoformat() if lease is not None else None,
            "expires_at": lease.expires_at.isoformat() if lease is not None else None,
            "reason_code": "submission_in_progress",
        }
        return replace(
            readiness,
            outcome=ExecutionReadinessOutcome.PHASE_BLOCKED,
            reason_codes=reason_codes,
            message=(
                "Another explicit child-intent submission is already in progress. "
                "No adapter submit call was made for this request."
            ),
            provenance=provenance,
        )

    @staticmethod
    def _submission_state_uncertain_readiness(
        readiness: ExecutionReadinessAssessment,
        lease: OrderIntentSubmissionLeaseModel | None,
    ) -> ExecutionReadinessAssessment:
        reason_codes = list(readiness.reason_codes or [])
        uncertain_status = (
            lease.status if lease is not None else _SUBMISSION_LEASE_STATUS_UNCERTAIN
        )
        for code in (
            "submission_state_uncertain",
            uncertain_status,
            "manual_reconciliation_required",
        ):
            if code not in reason_codes:
                reason_codes.append(code)
        if (
            uncertain_status == _SUBMISSION_LEASE_STATUS_ADAPTER_MAY_HAVE_STARTED
            and "adapter_submit_outcome_unknown" not in reason_codes
        ):
            reason_codes.append("adapter_submit_outcome_unknown")
        provenance = dict(readiness.provenance or {})
        metadata = dict(lease.metadata_json or {}) if lease is not None else {}
        provenance["submission_lease"] = {
            "purpose": _SUBMISSION_LEASE_PURPOSE,
            "status": uncertain_status,
            "lease_id": lease.lease_id if lease is not None else None,
            "acquired_at": lease.acquired_at.isoformat() if lease is not None else None,
            "expires_at": lease.expires_at.isoformat() if lease is not None else None,
            "released_at": lease.released_at.isoformat()
            if lease is not None and lease.released_at is not None
            else None,
            "reason_code": lease.reason_code if lease is not None else None,
            "requires_reconciliation": True,
            "metadata": _jsonable(metadata),
        }
        return replace(
            readiness,
            outcome=ExecutionReadinessOutcome.PHASE_BLOCKED,
            reason_codes=reason_codes,
            message=(
                "Venue may already have received this order. Manual reconciliation is "
                "required before another submit attempt for this intent."
            ),
            provenance=provenance,
        )

    @staticmethod
    def _is_pre_adapter_safe_failure(reason_codes: Sequence[str]) -> bool:
        return bool(reason_codes) and all(
            code in _PRE_ADAPTER_SAFE_FAILURE_REASON_CODES for code in reason_codes
        )

    def _acquire_intent_submission_lease(
        self,
        intent_id: str,
        *,
        readiness: ExecutionReadinessAssessment,
    ) -> str:
        now_value = _utcnow()
        expires_at = now_value + timedelta(seconds=_SUBMISSION_LEASE_TTL_SECONDS)
        for _attempt in range(2):
            lease_id = f"sublease_{uuid4().hex}"
            with self._session_factory() as session:
                existing = session.scalar(
                    select(OrderIntentSubmissionLeaseModel).where(
                        OrderIntentSubmissionLeaseModel.environment
                        == self.settings.app.environment,
                        OrderIntentSubmissionLeaseModel.intent_id == intent_id,
                        OrderIntentSubmissionLeaseModel.purpose
                        == _SUBMISSION_LEASE_PURPOSE,
                    )
                )
                if existing is None:
                    lease = OrderIntentSubmissionLeaseModel(
                        environment=self.settings.app.environment,
                        lease_id=lease_id,
                        intent_id=intent_id,
                        purpose=_SUBMISSION_LEASE_PURPOSE,
                        status="active",
                        acquired_at=now_value,
                        expires_at=expires_at,
                        released_at=None,
                        reason_code=None,
                        metadata_json={
                            "purpose": _SUBMISSION_LEASE_PURPOSE,
                            "acquire_reason": "explicit_submit_ready",
                        },
                        created_at=now_value,
                        updated_at=now_value,
                    )
                    session.add(lease)
                    try:
                        session.commit()
                    except IntegrityError:
                        session.rollback()
                        continue
                    return lease_id

                if existing.status in _SUBMISSION_LEASE_TERMINAL_UNCERTAIN_STATUSES:
                    raise SubmissionBlockedError(
                        intent_id,
                        self._submission_state_uncertain_readiness(readiness, existing),
                    )

                lease_is_active = (
                    existing.status == "active"
                    and existing.released_at is None
                    and not self._lease_expires_at_is_stale(existing.expires_at, now_value)
                )
                if lease_is_active:
                    raise SubmissionBlockedError(
                        intent_id,
                        self._submission_in_progress_readiness(readiness, existing),
                    )

                reason_code = (
                    "stale_submission_lease_replaced"
                    if existing.status == "active"
                    else "submission_lease_reacquired"
                )
                result = session.execute(
                    update(OrderIntentSubmissionLeaseModel)
                    .where(
                        OrderIntentSubmissionLeaseModel.id == existing.id,
                        or_(
                            OrderIntentSubmissionLeaseModel.status != "active",
                            OrderIntentSubmissionLeaseModel.released_at.is_not(None),
                            OrderIntentSubmissionLeaseModel.expires_at <= now_value,
                        ),
                    )
                    .values(
                        lease_id=lease_id,
                        status="active",
                        acquired_at=now_value,
                        expires_at=expires_at,
                        released_at=None,
                        reason_code=reason_code,
                        metadata_json={
                            "purpose": _SUBMISSION_LEASE_PURPOSE,
                            "acquire_reason": reason_code,
                            "previous_lease_id": existing.lease_id,
                        },
                        updated_at=now_value,
                    )
                    .execution_options(synchronize_session=False)
                )
                if result.rowcount == 1:
                    session.commit()
                    return lease_id
                session.rollback()

        with self._session_factory() as session:
            lease = session.scalar(
                select(OrderIntentSubmissionLeaseModel).where(
                    OrderIntentSubmissionLeaseModel.environment
                    == self.settings.app.environment,
                    OrderIntentSubmissionLeaseModel.intent_id == intent_id,
                    OrderIntentSubmissionLeaseModel.purpose == _SUBMISSION_LEASE_PURPOSE,
                )
            )
        raise SubmissionBlockedError(
            intent_id,
            (
                self._submission_state_uncertain_readiness(readiness, lease)
                if lease is not None
                and lease.status in _SUBMISSION_LEASE_TERMINAL_UNCERTAIN_STATUSES
                else self._submission_in_progress_readiness(readiness, lease)
            ),
        )

    def _release_intent_submission_lease(
        self,
        intent_id: str,
        lease_id: str,
        *,
        status: str,
        reason_code: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        now_value = _utcnow()
        with self._session_factory() as session:
            lease = session.scalar(
                select(OrderIntentSubmissionLeaseModel).where(
                    OrderIntentSubmissionLeaseModel.environment
                    == self.settings.app.environment,
                    OrderIntentSubmissionLeaseModel.intent_id == intent_id,
                    OrderIntentSubmissionLeaseModel.lease_id == lease_id,
                    OrderIntentSubmissionLeaseModel.purpose == _SUBMISSION_LEASE_PURPOSE,
                )
            )
            if lease is None:
                return
            lease.status = status
            lease.released_at = now_value
            lease.reason_code = reason_code
            lease.updated_at = now_value
            metadata_json = dict(lease.metadata_json or {})
            metadata_json.update(
                {
                    "release_reason": reason_code,
                    "released_at": now_value.isoformat(),
                }
            )
            if metadata:
                metadata_json.update(_jsonable(metadata))
            lease.metadata_json = _jsonable(metadata_json)
            session.add(lease)
            session.commit()

    def _mark_intent_submission_lease_adapter_may_have_started(
        self,
        intent_id: str,
        lease_id: str,
        *,
        readiness: ExecutionReadinessAssessment,
        venue: str,
    ) -> None:
        now_value = _utcnow()
        self._release_intent_submission_lease(
            intent_id,
            lease_id,
            status=_SUBMISSION_LEASE_STATUS_ADAPTER_MAY_HAVE_STARTED,
            reason_code="adapter_submit_may_have_started",
            metadata={
                "intent_id": intent_id,
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "venue": venue,
                "adapter_submit_called": True,
                "adapter_submit_may_have_started": True,
                "adapter_submit_returned": False,
                "submitted_order_persisted": False,
                "requires_reconciliation": True,
                "lease_id": lease_id,
                "adapter_submit_may_have_started_at": now_value.isoformat(),
            },
        )

    def _mark_intent_submission_lease_adapter_outcome_unknown(
        self,
        intent_id: str,
        lease_id: str,
        *,
        readiness: ExecutionReadinessAssessment,
        venue: str,
        exception: Exception,
        reason_codes: Sequence[str],
    ) -> None:
        self._release_intent_submission_lease(
            intent_id,
            lease_id,
            status=_SUBMISSION_LEASE_STATUS_ADAPTER_MAY_HAVE_STARTED,
            reason_code="adapter_submit_outcome_unknown",
            metadata={
                "intent_id": intent_id,
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "venue": venue,
                "adapter_submit_called": True,
                "adapter_submit_may_have_started": True,
                "adapter_submit_returned": False,
                "submitted_order_persisted": False,
                "requires_reconciliation": True,
                "adapter_failure_class": exception.__class__.__name__,
                "adapter_failure_message": str(exception),
                "adapter_failure_reason_codes": list(reason_codes),
            },
        )

    def _mark_intent_submission_lease_uncertain(
        self,
        intent_id: str,
        lease_id: str,
        *,
        readiness: ExecutionReadinessAssessment,
        venue: str,
        submitted: SubmittedOrder,
        exception: Exception,
    ) -> None:
        self._release_intent_submission_lease(
            intent_id,
            lease_id,
            status=_SUBMISSION_LEASE_STATUS_UNCERTAIN,
            reason_code="adapter_submit_returned_persistence_failed",
            metadata={
                "intent_id": intent_id,
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "venue": venue,
                "adapter_submit_called": True,
                "adapter_submit_returned": True,
                "submitted_order_persisted": False,
                "requires_reconciliation": True,
                "submitted_order_id": submitted.submitted_order_id,
                "exchange_order_id": submitted.exchange_order_id,
                "client_order_id": submitted.client_order_id,
                "persistence_failure_class": exception.__class__.__name__,
                "persistence_failure_message": str(exception),
            },
        )

    async def list_submitted_orders(
        self,
        *,
        intent_id: str | None = None,
        binding_key: str | None = None,
        venue_account_ref_id: str | None = None,
        venue: str | None = None,
        limit: int = 100,
    ) -> Sequence[SubmittedOrder]:
        with self._session_factory() as session:
            query = select(SubmittedOrderModel).where(
                SubmittedOrderModel.environment == self.settings.app.environment
            )
            if intent_id is not None:
                query = query.where(SubmittedOrderModel.intent_id == intent_id)
            if binding_key is not None:
                query = query.join(
                    OrderIntentModel,
                    OrderIntentModel.intent_id == SubmittedOrderModel.intent_id,
                ).where(OrderIntentModel.binding_key == binding_key)
            if venue_account_ref_id is not None:
                query = query.where(SubmittedOrderModel.venue_account_ref_id == venue_account_ref_id)
            if venue is not None:
                query = query.where(SubmittedOrderModel.venue == venue)
            models = session.scalars(
                query.order_by(SubmittedOrderModel.submitted_at.desc()).limit(limit)
            ).all()
        return [self._submitted_order_from_model(model) for model in models]

    async def get_submitted_order(self, submitted_order_id: str) -> SubmittedOrder:
        with self._session_factory() as session:
            model = session.scalar(
                select(SubmittedOrderModel).where(
                    SubmittedOrderModel.environment == self.settings.app.environment,
                    SubmittedOrderModel.submitted_order_id == submitted_order_id,
                )
            )
            if model is None:
                raise ValueError(f"Submitted order not found: {submitted_order_id}")
            return self._submitted_order_from_model(model)

    async def reconcile_submitted_order(self, submitted_order_id: str) -> SubmittedOrder:
        current = await self.get_submitted_order(submitted_order_id)
        adapter = await self.venue_registry_service.get_adapter(current.venue)
        fills = await self._get_fills_for_submitted_order(submitted_order_id)
        try:
            update = await adapter.reconcile_submitted_order(current)
        except VenueAdapterError as exc:
            update = SubmittedOrderLifecycleUpdate(
                submitted_order_id=current.submitted_order_id,
                venue=current.venue,
                venue_account_ref_id=current.venue_account_ref_id,
                exchange_order_id=current.exchange_order_id,
                status=current.status,
                reconciliation_status=SubmittedOrderReconciliationStatus.FAILED,
                event_type="reconciliation_failed",
                status_reason_code=(exc.reason_codes[0] if exc.reason_codes else "reconciliation_failed"),
                status_message=str(exc),
                reason_codes=list(exc.reason_codes or ["reconciliation_failed"]),
                cancelable_in_principle=current.cancelable_in_principle,
                amendable_in_principle=current.amendable_in_principle,
                raw_payload=_jsonable(getattr(exc, "payload", None) or {}),
                observed_at=_utcnow(),
            )
        merged = self._merge_lifecycle_update_with_fills(current=current, update=update, fills=fills)
        return self._apply_submitted_order_update(current=current, update=merged)

    async def reconcile_fills(self, submitted_order_id: str) -> Sequence[Fill]:
        await self.get_submitted_order(submitted_order_id)
        return await self._get_fills_for_submitted_order(submitted_order_id)

    async def cancel_submitted_order(self, submitted_order_id: str) -> SubmittedOrder:
        current = await self.get_submitted_order(submitted_order_id)
        actionability = await self.get_submitted_order_actionability(submitted_order_id)
        if not actionability.cancel_allowed_now:
            update = SubmittedOrderLifecycleUpdate(
                submitted_order_id=current.submitted_order_id,
                venue=current.venue,
                venue_account_ref_id=current.venue_account_ref_id,
                exchange_order_id=current.exchange_order_id,
                status=current.status,
                reconciliation_status=current.reconciliation_status,
                event_type="cancel_blocked",
                remaining_quantity=current.remaining_quantity,
                filled_quantity=current.filled_quantity,
                average_fill_price=current.average_fill_price,
                last_fill_at=current.last_fill_at,
                acknowledged_at=current.acknowledged_at,
                status_reason_code=(actionability.cancel_reason_codes[0] if actionability.cancel_reason_codes else "cancel_blocked"),
                status_message=actionability.message or "Submitted order is not cancelable in the current state.",
                reason_codes=list(actionability.cancel_reason_codes or ["cancel_blocked"]),
                cancelable_in_principle=current.cancelable_in_principle,
                amendable_in_principle=current.amendable_in_principle,
                raw_payload={"actionability": asdict(actionability)},
                observed_at=_utcnow(),
            )
            self._apply_submitted_order_update(current=current, update=update)
            raise SubmittedOrderActionError(submitted_order_id, update.status_message or "Cancel blocked.")
        requested_update = SubmittedOrderLifecycleUpdate(
            submitted_order_id=current.submitted_order_id,
            venue=current.venue,
            venue_account_ref_id=current.venue_account_ref_id,
            exchange_order_id=current.exchange_order_id,
            status=SubmittedOrderStatus.CANCEL_REQUESTED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            event_type="cancel_requested",
            remaining_quantity=current.remaining_quantity,
            filled_quantity=current.filled_quantity,
            average_fill_price=current.average_fill_price,
            last_fill_at=current.last_fill_at,
            acknowledged_at=current.acknowledged_at,
            status_reason_code="cancel_requested",
            status_message="Cancellation was requested for the submitted order.",
            reason_codes=["cancel_requested"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload={},
            observed_at=_utcnow(),
        )
        requested = self._apply_submitted_order_update(current=current, update=requested_update)
        adapter = await self.venue_registry_service.get_adapter(current.venue)
        try:
            update = await adapter.cancel_order(requested)
        except VenueAdapterError as exc:
            update = SubmittedOrderLifecycleUpdate(
                submitted_order_id=requested.submitted_order_id,
                venue=requested.venue,
                venue_account_ref_id=requested.venue_account_ref_id,
                exchange_order_id=requested.exchange_order_id,
                status=current.status,
                reconciliation_status=current.reconciliation_status,
                event_type="cancel_rejected",
                remaining_quantity=current.remaining_quantity,
                filled_quantity=current.filled_quantity,
                average_fill_price=current.average_fill_price,
                last_fill_at=current.last_fill_at,
                acknowledged_at=current.acknowledged_at,
                status_reason_code=(exc.reason_codes[0] if exc.reason_codes else "cancel_rejected"),
                status_message=str(exc),
                reason_codes=list(exc.reason_codes or ["cancel_rejected"]),
                cancelable_in_principle=current.cancelable_in_principle,
                amendable_in_principle=current.amendable_in_principle,
                raw_payload=_jsonable(getattr(exc, "payload", None) or {}),
                observed_at=_utcnow(),
            )
        return self._apply_submitted_order_update(current=requested, update=update)

    async def amend_submitted_order(
        self,
        submitted_order_id: str,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrder:
        current = await self.get_submitted_order(submitted_order_id)
        actionability = await self.get_submitted_order_actionability(submitted_order_id)
        if not actionability.amend_allowed_now:
            self._record_submitted_order_event(
                current,
                event_type="amend_blocked",
                observed_at=_utcnow(),
                message=actionability.message or "Submitted order is not amendable in the current state.",
                reason_codes=list(actionability.amend_reason_codes or ["amend_blocked"]),
                raw_payload={
                    "actionability": asdict(actionability),
                    "requested_quantity": str(new_quantity) if new_quantity is not None else None,
                    "requested_limit_price": (
                        str(new_limit_price) if new_limit_price is not None else None
                    ),
                },
            )
            raise SubmittedOrderActionError(
                submitted_order_id,
                actionability.message or "Amend blocked.",
            )
        self._record_submitted_order_event(
            current,
            event_type="amend_requested",
            observed_at=_utcnow(),
            message="Amendment was requested for the submitted order.",
            reason_codes=["amend_requested"],
            raw_payload={
                "requested_quantity": str(new_quantity) if new_quantity is not None else None,
                "requested_limit_price": (
                    str(new_limit_price) if new_limit_price is not None else None
                ),
            },
        )
        adapter = await self.venue_registry_service.get_adapter(current.venue)
        try:
            update = await adapter.amend_order(
                current,
                new_quantity=new_quantity,
                new_limit_price=new_limit_price,
            )
        except VenueAdapterError as exc:
            update = SubmittedOrderLifecycleUpdate(
                submitted_order_id=current.submitted_order_id,
                venue=current.venue,
                venue_account_ref_id=current.venue_account_ref_id,
                exchange_order_id=current.exchange_order_id,
                status=current.status,
                reconciliation_status=current.reconciliation_status,
                event_type="amend_rejected",
                limit_price=current.limit_price,
                original_quantity=current.original_quantity,
                remaining_quantity=current.remaining_quantity,
                filled_quantity=current.filled_quantity,
                average_fill_price=current.average_fill_price,
                last_fill_at=current.last_fill_at,
                acknowledged_at=current.acknowledged_at,
                status_reason_code=(exc.reason_codes[0] if exc.reason_codes else "amend_rejected"),
                status_message=str(exc),
                reason_codes=list(exc.reason_codes or ["amend_rejected"]),
                cancelable_in_principle=current.cancelable_in_principle,
                amendable_in_principle=current.amendable_in_principle,
                raw_payload=_jsonable(getattr(exc, "payload", None) or {}),
                observed_at=_utcnow(),
            )
        return self._apply_submitted_order_update(current=current, update=update)

    async def execute_submitted_order_recovery(
        self,
        submitted_order_id: str,
        *,
        action: str | None = None,
    ) -> SubmittedOrderRecoveryExecutionResult:
        current = await self.get_submitted_order(submitted_order_id)
        recommendation = await self.get_submitted_order_recovery_recommendation(submitted_order_id)
        routed_context = self._routed_lifecycle_context_for_submitted_order(current)
        resolved_action = action or self._default_recovery_action(current, recommendation)
        self._record_submitted_order_event(
            current,
            event_type="recovery_execution_requested",
            observed_at=_utcnow(),
            message=f"Recovery execution requested: {resolved_action}.",
            reason_codes=[resolved_action],
            raw_payload={
                "requested_action": resolved_action,
                "routed_lifecycle_context": (
                    _jsonable(asdict(routed_context)) if routed_context is not None else None
                ),
            },
        )
        if resolved_action == "reconcile_now":
            resulting = await self.reconcile_submitted_order(submitted_order_id)
            return SubmittedOrderRecoveryExecutionResult(
                submitted_order_id=current.submitted_order_id,
                venue_account_ref_id=current.venue_account_ref_id,
                venue=current.venue,
                action=resolved_action,
                executed=True,
                blocked=False,
                reason_codes=["recovery_reconciled"],
                message="Recovery execution reconciled the submitted order against venue truth.",
                resulting_submitted_order_id=resulting.submitted_order_id,
                resulting_order=resulting,
                routed_origin=routed_context is not None,
                routed_lifecycle_context=routed_context,
            )
        if resolved_action == "cancel_now":
            resulting = await self.cancel_submitted_order(submitted_order_id)
            return SubmittedOrderRecoveryExecutionResult(
                submitted_order_id=current.submitted_order_id,
                venue_account_ref_id=current.venue_account_ref_id,
                venue=current.venue,
                action=resolved_action,
                executed=True,
                blocked=False,
                reason_codes=["recovery_cancel_requested"],
                message="Recovery execution issued a same-target cancel request.",
                resulting_submitted_order_id=resulting.submitted_order_id,
                resulting_order=resulting,
                routed_origin=routed_context is not None,
                routed_lifecycle_context=routed_context,
            )
        if resolved_action == "retry_same_target":
            resulting = await self._retry_submitted_order_same_target(current, recommendation)
            return SubmittedOrderRecoveryExecutionResult(
                submitted_order_id=current.submitted_order_id,
                venue_account_ref_id=current.venue_account_ref_id,
                venue=current.venue,
                action=resolved_action,
                executed=True,
                blocked=False,
                reason_codes=["recovery_retry_submitted"],
                message="Recovery execution submitted a same-target retry after an explicitly retryable rejection.",
                resulting_submitted_order_id=resulting.submitted_order_id,
                resulting_order=resulting,
                routed_origin=routed_context is not None,
                routed_lifecycle_context=routed_context,
            )
        self._record_submitted_order_event(
            current,
            event_type="recovery_execution_blocked",
            observed_at=_utcnow(),
            message=f"Unsupported recovery action requested: {resolved_action}.",
            reason_codes=["recovery_action_unsupported"],
            raw_payload={"requested_action": resolved_action},
        )
        raise SubmittedOrderActionError(
            submitted_order_id,
            f"Unsupported recovery action: {resolved_action}",
        )

    async def get_submitted_order_recovery_recommendation(
        self,
        submitted_order_id: str,
    ) -> SubmittedOrderRecoveryRecommendation:
        submitted = await self.get_submitted_order(submitted_order_id)
        return self._recovery_recommendation_for_submitted_order(submitted)

    async def get_submitted_order_actionability(
        self,
        submitted_order_id: str,
    ) -> SubmittedOrderActionability:
        submitted = await self.get_submitted_order(submitted_order_id)
        routed_context = self._routed_lifecycle_context_for_submitted_order(submitted)
        adapter = await self.venue_registry_service.get_adapter(submitted.venue)
        capabilities = await adapter.get_venue_capabilities()
        cancel_reason_codes: list[str] = []
        amend_reason_codes: list[str] = []
        cancel_supported = bool(capabilities.adapter_supports_order_cancel)
        amend_supported = bool(capabilities.adapter_supports_order_amend)

        open_statuses = {
            SubmittedOrderStatus.NEW,
            SubmittedOrderStatus.SUBMITTED,
            SubmittedOrderStatus.ACKNOWLEDGED,
            SubmittedOrderStatus.PARTIALLY_FILLED,
        }
        if not cancel_supported:
            cancel_reason_codes.append("cancel_not_supported")
        elif submitted.status not in open_statuses:
            cancel_reason_codes.append("cancel_not_permitted")
        elif not submitted.cancelable_in_principle:
            cancel_reason_codes.append("cancel_not_permitted")

        if not amend_supported:
            amend_reason_codes.append("amend_not_supported")
        elif submitted.order_type != OrderType.LIMIT:
            amend_reason_codes.append("amend_not_supported_for_order_type")
        elif (
            submitted.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
            and submitted.status_reason_code == "amend_acknowledged"
        ):
            amend_reason_codes.append("amend_reconciliation_pending")
        elif submitted.status not in open_statuses:
            amend_reason_codes.append("amend_not_permitted")
        elif not submitted.amendable_in_principle:
            amend_reason_codes.append("amend_not_permitted")

        message = None
        if cancel_reason_codes:
            message = f"Submitted order is not cancelable now: {cancel_reason_codes[0]}."
        elif amend_reason_codes:
            message = f"Submitted order is not amendable now: {amend_reason_codes[0]}."

        return SubmittedOrderActionability(
            submitted_order_id=submitted.submitted_order_id,
            venue_account_ref_id=submitted.venue_account_ref_id,
            venue=submitted.venue,
            status=submitted.status,
            reconciliation_status=submitted.reconciliation_status,
            cancel_supported=cancel_supported,
            cancel_allowed_now=(cancel_supported and not cancel_reason_codes),
            amend_supported=amend_supported,
            amend_allowed_now=(amend_supported and not amend_reason_codes),
            cancel_reason_codes=cancel_reason_codes,
            amend_reason_codes=amend_reason_codes,
            message=message,
            routed_origin=routed_context is not None,
            routed_lifecycle_context=routed_context,
        )

    async def list_submitted_order_events(
        self,
        *,
        submitted_order_id: str | None = None,
        intent_id: str | None = None,
        limit: int = 100,
    ) -> Sequence[SubmittedOrderLifecycleEvent]:
        with self._session_factory() as session:
            query = select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.environment == self.settings.app.environment
            )
            if submitted_order_id is not None:
                query = query.where(
                    SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
                )
            if intent_id is not None:
                query = query.where(SubmittedOrderLifecycleEventModel.intent_id == intent_id)
            models = session.scalars(
                query.order_by(SubmittedOrderLifecycleEventModel.observed_at.desc()).limit(limit)
            ).all()
            submitted_order_ids = {model.submitted_order_id for model in models}
            routed_context_by_order_id: dict[
                str,
                SubmittedOrderRoutedLifecycleContext | None,
            ] = {}
            if submitted_order_ids:
                submitted_models = session.scalars(
                    select(SubmittedOrderModel).where(
                        SubmittedOrderModel.environment == self.settings.app.environment,
                        SubmittedOrderModel.submitted_order_id.in_(submitted_order_ids),
                    )
                ).all()
                routed_context_by_order_id = {
                    model.submitted_order_id: submitted_order_routed_lifecycle_context_from_raw_payload(
                        model.raw_payload
                    )
                    for model in submitted_models
                }
        return [
            self._submitted_order_event_from_model(
                model,
                routed_lifecycle_context=routed_context_by_order_id.get(
                    model.submitted_order_id
                ),
            )
            for model in models
        ]

    async def preview_child_intent(self, intent_id: str) -> PreparedVenueOrder:
        with self._session_factory() as session:
            model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == intent_id,
                )
            )
            if model is None:
                raise ValueError(f"Child intent not found: {intent_id}")
            intent = self._order_intent_from_model(model)
            routed, route_reason_codes, route_missing_data, route_lineage = (
                self._validate_routed_child_intent_lineage(session, model)
            )
            if routed and (route_reason_codes or route_missing_data):
                return self._blocked_routed_prepared_order(
                    intent,
                    reason_codes=route_reason_codes,
                    missing_data=route_missing_data,
                    route_lineage=route_lineage,
                )
            venue = (
                str(route_lineage.get("selected_venue") or route_lineage.get("venue"))
                if routed
                else self._resolve_venue_for_intent(session, model)
            )
        preview = await self._prepare_preview_for_intent(intent, venue=venue)
        if routed:
            preview = self._attach_routed_lineage_to_preview(preview, route_lineage)
        return preview

    async def assess_child_intent_readiness(
        self,
        intent_id: str,
    ) -> ExecutionReadinessAssessment:
        with self._session_factory() as session:
            model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == intent_id,
                )
            )
            if model is None:
                raise ValueError(f"Child intent not found: {intent_id}")
            _preview, assessment = await self._build_child_intent_readiness_in_session(
                session,
                model,
            )
        return self._persist_readiness_assessment(assessment)

    async def preview_and_assess_child_intent_readiness_in_session(
        self,
        session: Any,
        intent_model: OrderIntentModel,
    ) -> tuple[PreparedVenueOrder, ExecutionReadinessAssessment, bool]:
        """Build existing preview/readiness and persist readiness in the caller's transaction."""

        preview, assessment = await self._build_child_intent_readiness_in_session(
            session,
            intent_model,
        )
        readiness, created = self._persist_readiness_assessment_in_session(
            session,
            assessment,
        )
        return preview, readiness, created

    async def _build_child_intent_readiness_in_session(
        self,
        session: Any,
        model: OrderIntentModel,
    ) -> tuple[PreparedVenueOrder, ExecutionReadinessAssessment]:
        intent = self._order_intent_from_model(model)
        routed, route_reason_codes, route_missing_data, route_lineage = (
            self._validate_routed_child_intent_lineage(session, model)
        )
        if routed and (route_reason_codes or route_missing_data):
            preview = self._blocked_routed_prepared_order(
                intent,
                reason_codes=route_reason_codes,
                missing_data=route_missing_data,
                route_lineage=route_lineage,
            )
            assessment = self._build_routed_lineage_blocked_readiness(
                intent=intent,
                intent_ref_id=model.id,
                preview=preview,
                reason_codes=route_reason_codes,
                missing_data=route_missing_data,
                route_lineage=route_lineage,
            )
            return preview, assessment
        venue = (
            str(route_lineage.get("selected_venue") or route_lineage.get("venue"))
            if routed
            else self._resolve_venue_for_intent(session, model)
        )
        binding_model = (
            session.get(MandateAccountBindingModel, model.mandate_account_binding_ref_id)
            if model.mandate_account_binding_ref_id is not None
            else None
        )
        venue_account_model = (
            session.get(VenueAccountModel, model.venue_account_ref_id)
            if model.venue_account_ref_id is not None
            else None
        )
        preview = await self._prepare_preview_for_intent(intent, venue=venue)
        if routed:
            preview = self._attach_routed_lineage_to_preview(preview, route_lineage)
        assessment = self._build_readiness_assessment(
            intent=intent,
            intent_ref_id=model.id,
            venue=venue,
            preview=preview,
            binding_model=binding_model,
            venue_account_model=venue_account_model,
            routed_lineage=route_lineage if routed else None,
        )
        return preview, assessment

    def _persist_readiness_assessment(
        self,
        assessment: ExecutionReadinessAssessment,
    ) -> ExecutionReadinessAssessment:
        with self._session_factory() as session:
            readiness, _created = self._persist_readiness_assessment_in_session(
                session,
                assessment,
            )
            session.commit()
            return readiness

    def _persist_readiness_assessment_in_session(
        self,
        session: Any,
        assessment: ExecutionReadinessAssessment,
    ) -> tuple[ExecutionReadinessAssessment, bool]:
        existing = session.scalar(
            select(ExecutionReadinessEvaluationModel).where(
                ExecutionReadinessEvaluationModel.readiness_evaluation_key
                == assessment.readiness_evaluation_key
            )
        )
        if existing is not None:
            return self._execution_readiness_from_model(existing), False
        stored = ExecutionReadinessEvaluationModel(
            environment=assessment.environment,
            readiness_evaluation_id=assessment.readiness_evaluation_id,
            readiness_evaluation_key=assessment.readiness_evaluation_key,
            intent_ref_id=assessment.intent_ref_id,
            intent_id=assessment.intent_id,
            mandate_desired_trade_ref_id=assessment.mandate_desired_trade_ref_id,
            desired_trade_key=assessment.desired_trade_key,
            client_ref_id=assessment.client_ref_id,
            strategy_mandate_ref_id=assessment.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=assessment.mandate_account_binding_ref_id,
            binding_key=assessment.binding_key,
            venue_account_ref_id=assessment.venue_account_ref_id,
            instrument_key=assessment.instrument_key,
            instrument_ref_id=assessment.instrument_ref_id,
            symbol=assessment.symbol,
            venue=assessment.venue,
            support_level=assessment.support_level.value,
            preview_status=(
                assessment.preview_status.value
                if assessment.preview_status is not None
                else None
            ),
            outcome=assessment.outcome,
            eligible_for_submission_in_principle=assessment.eligible_for_submission_in_principle,
            live_submission_phase_enabled=assessment.live_submission_phase_enabled,
            venue_supports_order_submission=assessment.venue_supports_order_submission,
            adapter_supports_order_submission=assessment.adapter_supports_order_submission,
            adapter_supports_cancel_amend=assessment.adapter_supports_order_cancel,
            submission_authorized=assessment.submission_authorized,
            account_connected=assessment.account_connected,
            private_state_required=assessment.private_state_required,
            private_state_ready=assessment.private_state_ready,
            reason_codes=list(assessment.reason_codes),
            message=assessment.message,
            provenance=_jsonable(assessment.provenance),
            evaluated_at=assessment.evaluated_at or _utcnow(),
        )
        session.add(stored)
        session.flush()
        return self._execution_readiness_from_model(stored), True

    async def list_readiness_assessments(
        self,
        *,
        intent_id: str | None = None,
        outcome: ExecutionReadinessOutcome | None = None,
        limit: int = 100,
    ) -> Sequence[ExecutionReadinessAssessment]:
        with self._session_factory() as session:
            query = select(ExecutionReadinessEvaluationModel).where(
                ExecutionReadinessEvaluationModel.environment == self.settings.app.environment
            )
            if intent_id is not None:
                query = query.where(ExecutionReadinessEvaluationModel.intent_id == intent_id)
            if outcome is not None:
                query = query.where(ExecutionReadinessEvaluationModel.outcome == outcome)
            models = session.scalars(
                query.order_by(ExecutionReadinessEvaluationModel.evaluated_at.desc()).limit(limit)
            ).all()
        return [self._execution_readiness_from_model(model) for model in models]

    @staticmethod
    def _lookup_symbol_id(
        session: Any,
        *,
        instrument_ref_id: str | None,
        venue: str,
        symbol: str,
    ) -> str | None:
        if instrument_ref_id is None:
            return None
        return session.scalar(
            select(SymbolModel.id).where(
                SymbolModel.instrument_ref_id == instrument_ref_id,
                SymbolModel.venue == venue,
                SymbolModel.symbol == symbol,
            )
        )

    @staticmethod
    def _side_for_action(action: DecisionAction) -> OrderSide | None:
        if action in {DecisionAction.OPEN, DecisionAction.ADD}:
            return OrderSide.BUY
        if action in {DecisionAction.REDUCE, DecisionAction.CLOSE}:
            return OrderSide.SELL
        return None

    def _draft_child_intent(
        self,
        *,
        desired_trade: MandateDesiredTrade,
        candidate: BindingRoutingCandidate,
    ) -> OrderIntent:
        binding_key = desired_trade.binding_key or candidate.binding_key
        if not binding_key or not candidate.venue_account_ref_id:
            raise ValueError("Child intents require explicit binding/account targeting.")
        side = desired_trade.side or self._side_for_action(desired_trade.action)
        if side is None:
            raise ValueError("Child intents require a deterministic side.")
        if desired_trade.desired_quantity is None or desired_trade.desired_quantity <= Decimal("0"):
            raise ValueError("Child intents require a positive desired quantity.")
        return OrderIntent(
            intent_id=f"preview-{desired_trade.desired_trade_key or binding_key}",
            sleeve_id=desired_trade.component_key or "component",
            component_key=desired_trade.component_key,
            decision_id=(desired_trade.source_decision_ids[0] if desired_trade.source_decision_ids else ""),
            action=desired_trade.action,
            mandate_desired_trade_ref_id=desired_trade.desired_trade_ref_id,
            desired_trade_key=desired_trade.desired_trade_key,
            client_ref_id=desired_trade.client_ref_id,
            strategy_mandate_ref_id=desired_trade.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=desired_trade.mandate_account_binding_ref_id or candidate.binding_ref_id,
            binding_key=binding_key,
            venue_account_ref_id=desired_trade.venue_account_ref_id or candidate.venue_account_ref_id,
            instrument_key=desired_trade.instrument_key,
            instrument_ref_id=desired_trade.instrument_ref_id,
            symbol=desired_trade.symbol,
            environment=desired_trade.environment,
            side=side,
            order_type=OrderType.MARKET,
            quantity=desired_trade.desired_quantity,
            limit_price=None,
            reduce_only=desired_trade.action in {DecisionAction.REDUCE, DecisionAction.CLOSE},
            ttl_seconds=self.settings.execution.default_order_ttl_seconds,
            status=OrderIntentStatus.PREPARED,
            idempotency_key="preview-only",
            created_at=_utcnow(),
            provenance={
                "phase_boundary": "phase_4_1_1",
                "preview_only": True,
            },
        )

    async def _prepare_preview_for_intent(
        self,
        intent: OrderIntent,
        *,
        venue: str,
    ) -> PreparedVenueOrder:
        adapter = await self.venue_registry_service.get_adapter(venue)
        return await adapter.prepare_order_preview(intent)

    @staticmethod
    def _preview_summary(preview: PreparedVenueOrder) -> dict[str, object]:
        return _jsonable(asdict(preview))

    @staticmethod
    def _is_routed_child_intent_model(model: OrderIntentModel) -> bool:
        provenance = dict(model.provenance or {})
        return bool(
            provenance.get("phase_boundary") == "phase_5_2_target_choice_conversion"
            or provenance.get("routing_assessment_id")
            or provenance.get("routing_target_choice_id")
        )

    def _validate_routed_child_intent_lineage(
        self,
        session: Any,
        model: OrderIntentModel,
    ) -> tuple[bool, list[str], list[str], dict[str, object]]:
        if not self._is_routed_child_intent_model(model):
            return False, [], [], {}

        provenance = dict(model.provenance or {})
        route_readiness_audit_id = provenance.get("route_readiness_audit_id")
        routing_target_recommendation_id = provenance.get(
            "routing_target_recommendation_id"
        )
        recommendation_policy_name = provenance.get("recommendation_policy_name")
        routed_order_shape_policy_raw = provenance.get("routed_order_shape_policy")
        routed_order_shape_policy = (
            dict(routed_order_shape_policy_raw)
            if isinstance(routed_order_shape_policy_raw, dict)
            else {}
        )
        recommendation_backed_child_intent = bool(
            routing_target_recommendation_id
            or provenance.get("accepted_recommendation_target_choice_conversion")
            or provenance.get("child_intent_created_from_accepted_recommendation")
        )
        reason_codes: list[str] = []
        missing_data: list[str] = []
        stale_data: list[str] = []
        route_lineage: dict[str, object] = {
            "phase_boundary": "phase_5_3_routed_preparation_readiness",
            "routed_child_intent": True,
            "recommendation_backed_child_intent": recommendation_backed_child_intent,
            "non_submitting": True,
            "intent_id": model.intent_id,
            "desired_trade_key": model.desired_trade_key,
            "routing_assessment_id": provenance.get("routing_assessment_id"),
            "route_readiness_audit_id": route_readiness_audit_id,
            "routing_target_recommendation_id": routing_target_recommendation_id,
            "routing_target_choice_id": provenance.get("routing_target_choice_id"),
            "recommendation_policy_name": recommendation_policy_name,
            "target_choice_source": provenance.get("target_choice_source"),
            "selected_binding_ref_id": provenance.get("selected_binding_ref_id"),
            "selected_binding_key": provenance.get("selected_binding_key"),
            "selected_venue_account_ref_id": provenance.get("selected_venue_account_ref_id"),
            "selected_venue_account_key": provenance.get("selected_venue_account_key"),
            "selected_venue": provenance.get("selected_venue"),
            "selected_exchange_symbol": provenance.get("selected_exchange_symbol"),
            "routed_order_shape_policy": _jsonable(routed_order_shape_policy),
            "prepared_order_created": False,
            "readiness_assessment_created": False,
            "submitted_order_created": False,
            "auto_submit": False,
            "fanout_created": False,
            "allocation_created": False,
            "scoring_created": False,
            "target_reselection": False,
        }

        assessment_id = provenance.get("routing_assessment_id")
        target_choice_id = provenance.get("routing_target_choice_id")
        if not assessment_id:
            reason_codes.append("routed_lineage_missing_routing_assessment_id")
        if not target_choice_id:
            reason_codes.append("routed_lineage_missing_routing_target_choice_id")
        shape_reason_codes, shape_missing_data = (
            self._routed_order_shape_policy_blockers(
                model,
                routed_order_shape_policy_raw,
            )
        )
        reason_codes.extend(shape_reason_codes)
        missing_data.extend(shape_missing_data)

        assessment_model = None
        if assessment_id:
            assessment_model = session.scalar(
                select(RoutingAssessmentModel).where(
                    RoutingAssessmentModel.environment == self.settings.app.environment,
                    RoutingAssessmentModel.assessment_id == assessment_id,
                )
            )
            if assessment_model is None:
                reason_codes.append("routing_assessment_not_found")
            else:
                route_lineage["routing_assessment_ref_id"] = assessment_model.id
                if assessment_model.id != provenance.get("routing_assessment_ref_id"):
                    reason_codes.append("routing_assessment_ref_mismatch")
                if assessment_model.decision_status != RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY:
                    reason_codes.append("routing_assessment_not_assessment_only")

        choice_model = None
        if target_choice_id:
            choice_model = session.scalar(
                select(RoutingTargetChoiceModel).where(
                    RoutingTargetChoiceModel.environment == self.settings.app.environment,
                    RoutingTargetChoiceModel.target_choice_id == target_choice_id,
                )
            )
            if choice_model is None:
                reason_codes.append("routing_target_choice_not_found")
            else:
                route_lineage["routing_target_choice_ref_id"] = choice_model.id
                if choice_model.id != provenance.get("routing_target_choice_ref_id"):
                    reason_codes.append("routing_target_choice_ref_mismatch")
                if choice_model.status != RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED:
                    reason_codes.append("routing_target_choice_not_recorded")
                if not choice_model.non_executing:
                    reason_codes.append("routing_target_choice_not_non_executing")
                if assessment_model is not None:
                    if choice_model.routing_assessment_ref_id != assessment_model.id:
                        reason_codes.append("routing_target_choice_assessment_ref_mismatch")
                    if choice_model.routing_assessment_id != assessment_model.assessment_id:
                        reason_codes.append("routing_target_choice_assessment_id_mismatch")

        desired_trade_model = (
            session.get(MandateDesiredTradeModel, model.mandate_desired_trade_ref_id)
            if model.mandate_desired_trade_ref_id is not None
            else None
        )
        if desired_trade_model is None and model.desired_trade_key is not None:
            desired_trade_model = session.scalar(
                select(MandateDesiredTradeModel).where(
                    MandateDesiredTradeModel.environment == self.settings.app.environment,
                    MandateDesiredTradeModel.desired_trade_key == model.desired_trade_key,
                )
            )
        if desired_trade_model is None:
            reason_codes.append("desired_trade_not_found")
        else:
            route_lineage["desired_trade_ref_id"] = desired_trade_model.id
            if model.mandate_desired_trade_ref_id != desired_trade_model.id:
                reason_codes.append("intent_desired_trade_ref_mismatch")
            if model.desired_trade_key != desired_trade_model.desired_trade_key:
                reason_codes.append("intent_desired_trade_key_mismatch")
            if model.client_ref_id != desired_trade_model.client_ref_id:
                reason_codes.append("intent_client_mismatch")
            if model.strategy_mandate_ref_id != desired_trade_model.strategy_mandate_ref_id:
                reason_codes.append("intent_strategy_mandate_mismatch")
            if desired_trade_model.status != MandateDesiredTradeStatus.ROUTED:
                reason_codes.append("desired_trade_not_routed")
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
            if assessment_model is not None:
                if desired_trade_model.id != assessment_model.desired_trade_ref_id:
                    reason_codes.append("desired_trade_assessment_ref_mismatch")
                if desired_trade_model.desired_trade_key != assessment_model.desired_trade_key:
                    reason_codes.append("desired_trade_assessment_key_mismatch")
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
                if model.client_ref_id != assessment_model.client_ref_id:
                    reason_codes.append("intent_client_mismatch")
                if model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id:
                    reason_codes.append("intent_strategy_mandate_mismatch")
                if model.instrument_key != assessment_model.instrument_key:
                    reason_codes.append("intent_instrument_key_assessment_mismatch")
                if model.instrument_ref_id != assessment_model.instrument_ref_id:
                    reason_codes.append("intent_instrument_ref_assessment_mismatch")
                if model.symbol != assessment_model.symbol:
                    reason_codes.append("intent_symbol_assessment_mismatch")

        mandate_model = (
            session.get(StrategyMandateModel, model.strategy_mandate_ref_id)
            if model.strategy_mandate_ref_id is not None
            else None
        )
        if mandate_model is None:
            reason_codes.append("mandate_missing")
        else:
            route_lineage["current_mandate_ref_id"] = mandate_model.id
            route_lineage["current_mandate_key"] = mandate_model.mandate_key
            if not mandate_model.enabled:
                reason_codes.append("mandate_inactive")
            if desired_trade_model is not None and (
                mandate_model.id != desired_trade_model.strategy_mandate_ref_id
            ):
                reason_codes.append("mandate_desired_trade_mismatch")
            if assessment_model is not None and (
                mandate_model.id != assessment_model.strategy_mandate_ref_id
            ):
                reason_codes.append("mandate_assessment_mismatch")

        if choice_model is not None:
            target_choice_desired_trade_ref_mismatch = False
            target_choice_desired_trade_key_mismatch = False
            desired_trade_ref_values = [model.mandate_desired_trade_ref_id]
            desired_trade_key_values = [model.desired_trade_key]
            if desired_trade_model is not None:
                desired_trade_ref_values.append(desired_trade_model.id)
                desired_trade_key_values.append(desired_trade_model.desired_trade_key)
            if assessment_model is not None:
                desired_trade_ref_values.append(assessment_model.desired_trade_ref_id)
                desired_trade_key_values.append(assessment_model.desired_trade_key)
            for desired_trade_ref_id in desired_trade_ref_values:
                if choice_model.desired_trade_ref_id != desired_trade_ref_id:
                    target_choice_desired_trade_ref_mismatch = True
            for desired_trade_key in desired_trade_key_values:
                if choice_model.desired_trade_key != desired_trade_key:
                    target_choice_desired_trade_key_mismatch = True
            if target_choice_desired_trade_ref_mismatch:
                reason_codes.append("routing_target_choice_desired_trade_ref_mismatch")
            if target_choice_desired_trade_key_mismatch:
                reason_codes.append("routing_target_choice_desired_trade_key_mismatch")

        candidate_model = None
        if assessment_model is not None:
            candidate_model = session.scalar(
                select(RoutingAssessmentCandidateModel).where(
                    RoutingAssessmentCandidateModel.assessment_ref_id == assessment_model.id,
                    RoutingAssessmentCandidateModel.binding_ref_id
                    == (choice_model.selected_binding_ref_id if choice_model is not None else model.mandate_account_binding_ref_id),
                    RoutingAssessmentCandidateModel.venue_account_ref_id
                    == (choice_model.selected_venue_account_ref_id if choice_model is not None else model.venue_account_ref_id),
                )
            )
            if candidate_model is None:
                reason_codes.append("routing_candidate_not_found")
            else:
                route_lineage["routing_candidate_ref_id"] = candidate_model.id
                if (
                    candidate_model.eligibility_status
                    != RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
                ):
                    reason_codes.append("routing_candidate_not_eligible")
                if candidate_model.missing_data_json:
                    reason_codes.append("routing_candidate_missing_data")
                    missing_data.extend(candidate_model.missing_data_json)
                candidate_comparisons = {
                    "intent_binding_candidate_mismatch": (
                        model.mandate_account_binding_ref_id,
                        candidate_model.binding_ref_id,
                    ),
                    "intent_binding_key_candidate_mismatch": (
                        model.binding_key,
                        candidate_model.binding_key,
                    ),
                    "intent_venue_account_candidate_mismatch": (
                        model.venue_account_ref_id,
                        candidate_model.venue_account_ref_id,
                    ),
                    "intent_instrument_ref_candidate_mismatch": (
                        model.instrument_ref_id,
                        candidate_model.instrument_ref_id,
                    ),
                    "intent_instrument_key_candidate_mismatch": (
                        model.instrument_key,
                        candidate_model.instrument_key,
                    ),
                    "intent_symbol_candidate_mismatch": (model.symbol, candidate_model.symbol),
                }
                for reason_code, (left, right) in candidate_comparisons.items():
                    if left != right:
                        reason_codes.append(reason_code)
                symbol_reason_codes, symbol_missing_data = (
                    self._candidate_symbol_mapping_blockers(session, candidate_model)
                )
                reason_codes.extend(symbol_reason_codes)
                missing_data.extend(symbol_missing_data)

        if choice_model is not None:
            choice_comparisons = {
                "intent_binding_target_choice_mismatch": (
                    model.mandate_account_binding_ref_id,
                    choice_model.selected_binding_ref_id,
                ),
                "intent_binding_key_target_choice_mismatch": (
                    model.binding_key,
                    choice_model.selected_binding_key,
                ),
                "intent_venue_account_target_choice_mismatch": (
                    model.venue_account_ref_id,
                    choice_model.selected_venue_account_ref_id,
                ),
            }
            for reason_code, (left, right) in choice_comparisons.items():
                if left != right:
                    reason_codes.append(reason_code)

        provenance_selected_binding_ref_id = provenance.get("selected_binding_ref_id")
        provenance_selected_binding_key = provenance.get("selected_binding_key")
        provenance_selected_venue_account_ref_id = provenance.get("selected_venue_account_ref_id")
        provenance_selected_venue_account_key = provenance.get("selected_venue_account_key")
        provenance_selected_venue = provenance.get("selected_venue")
        provenance_selected_exchange_symbol = provenance.get("selected_exchange_symbol")

        binding_model = (
            session.get(MandateAccountBindingModel, model.mandate_account_binding_ref_id)
            if model.mandate_account_binding_ref_id is not None
            else None
        )
        if binding_model is None:
            reason_codes.append("binding_record_missing")
        else:
            route_lineage["current_binding_ref_id"] = binding_model.id
            route_lineage["current_binding_key"] = binding_model.binding_key
            if not binding_model.enabled:
                reason_codes.append("binding_disabled")
            if not binding_model.routing_eligible:
                reason_codes.append("binding_not_routing_eligible")
            if not binding_model.trading_enabled:
                reason_codes.append("binding_trading_disabled")
            if binding_model.binding_key != model.binding_key:
                reason_codes.append("binding_intent_key_mismatch")
            if binding_model.venue_account_ref_id != model.venue_account_ref_id:
                reason_codes.append("binding_venue_account_mismatch")
            if desired_trade_model is not None and (
                binding_model.strategy_mandate_ref_id != desired_trade_model.strategy_mandate_ref_id
            ):
                reason_codes.append("binding_desired_trade_mandate_mismatch")
            if assessment_model is not None and (
                binding_model.strategy_mandate_ref_id != assessment_model.strategy_mandate_ref_id
            ):
                reason_codes.append("binding_assessment_mandate_mismatch")

        account_model = (
            session.get(VenueAccountModel, model.venue_account_ref_id)
            if model.venue_account_ref_id is not None
            else None
        )
        if account_model is None:
            reason_codes.append("venue_account_record_missing")
        else:
            route_lineage["current_venue_account_ref_id"] = account_model.id
            route_lineage["current_venue_account_key"] = account_model.venue_account_key
            route_lineage["venue"] = account_model.venue
            if not account_model.is_active:
                reason_codes.append("venue_account_inactive")
            if not account_model.trading_enabled:
                reason_codes.append("venue_account_trading_disabled")
            if choice_model is not None:
                if account_model.venue_account_key != choice_model.selected_venue_account_key:
                    reason_codes.append("venue_account_target_choice_key_mismatch")
                if account_model.venue != choice_model.selected_venue:
                    reason_codes.append("venue_account_target_choice_venue_mismatch")
            if candidate_model is not None:
                if account_model.venue_account_key != candidate_model.venue_account_key:
                    reason_codes.append("venue_account_candidate_key_mismatch")
                if account_model.venue != candidate_model.venue:
                    reason_codes.append("venue_account_candidate_venue_mismatch")
            if model.client_ref_id is not None and account_model.client_ref_id != model.client_ref_id:
                reason_codes.append("venue_account_client_mismatch")
            if desired_trade_model is not None and (
                account_model.client_ref_id != desired_trade_model.client_ref_id
            ):
                reason_codes.append("venue_account_client_mismatch")
            if assessment_model is not None and (
                account_model.client_ref_id != assessment_model.client_ref_id
            ):
                reason_codes.append("venue_account_client_mismatch")

        recommendation_model = None
        audit_model = None
        readiness_candidate_model = None
        if recommendation_backed_child_intent:
            if not routing_target_recommendation_id:
                reason_codes.append("routing_target_recommendation_id_missing")
            else:
                recommendation_model = session.scalar(
                    select(RoutingTargetRecommendationModel).where(
                        RoutingTargetRecommendationModel.environment
                        == self.settings.app.environment,
                        RoutingTargetRecommendationModel.routing_target_recommendation_id
                        == routing_target_recommendation_id,
                    )
                )
                if recommendation_model is None:
                    reason_codes.append("routing_target_recommendation_not_found")
                else:
                    route_lineage["routing_target_recommendation_ref_id"] = (
                        recommendation_model.id
                    )
                    route_lineage["submitted_order_created"] = bool(
                        recommendation_model.submitted_order_created
                    )
                    if (
                        recommendation_model.status
                        != RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
                    ):
                        reason_codes.append("routing_target_recommendation_not_recommended")
                    if not recommendation_model.non_executing:
                        reason_codes.append("routing_target_recommendation_not_non_executing")
                    if not recommendation_model.child_intent_created:
                        reason_codes.append(
                            "routing_target_recommendation_child_intent_not_created"
                        )
                    recommendation_checks = {
                        "recommendation_route_readiness_audit_id_mismatch": (
                            route_readiness_audit_id,
                            recommendation_model.route_readiness_audit_id,
                        ),
                        "recommendation_routing_assessment_id_mismatch": (
                            assessment_id,
                            recommendation_model.routing_assessment_id,
                        ),
                        "recommendation_desired_trade_key_mismatch": (
                            model.desired_trade_key,
                            recommendation_model.desired_trade_key,
                        ),
                        "recommendation_binding_ref_mismatch": (
                            model.mandate_account_binding_ref_id,
                            recommendation_model.recommended_binding_ref_id,
                        ),
                        "recommendation_binding_key_mismatch": (
                            model.binding_key,
                            recommendation_model.recommended_binding_key,
                        ),
                        "recommendation_venue_account_ref_mismatch": (
                            model.venue_account_ref_id,
                            recommendation_model.recommended_venue_account_ref_id,
                        ),
                        "recommendation_venue_account_key_mismatch": (
                            provenance_selected_venue_account_key,
                            recommendation_model.recommended_venue_account_key,
                        ),
                        "recommendation_venue_mismatch": (
                            provenance_selected_venue,
                            recommendation_model.recommended_venue,
                        ),
                        "recommendation_exchange_symbol_mismatch": (
                            provenance_selected_exchange_symbol,
                            recommendation_model.recommended_exchange_symbol,
                        ),
                        "recommendation_policy_name_mismatch": (
                            recommendation_policy_name,
                            recommendation_model.policy_name,
                        ),
                    }
                    for reason_code, (left, right) in recommendation_checks.items():
                        if left != right:
                            reason_codes.append(reason_code)

                    if recommendation_model.route_readiness_audit_ref_id is not None:
                        audit_model = session.get(
                            RouteReadinessAuditModel,
                            recommendation_model.route_readiness_audit_ref_id,
                        )
                    if audit_model is None and recommendation_model.route_readiness_audit_id:
                        audit_model = session.scalar(
                            select(RouteReadinessAuditModel).where(
                                RouteReadinessAuditModel.environment
                                == self.settings.app.environment,
                                RouteReadinessAuditModel.route_readiness_audit_id
                                == recommendation_model.route_readiness_audit_id,
                            )
                        )
                    if audit_model is None:
                        reason_codes.append("route_readiness_audit_not_found")
                    else:
                        route_lineage["route_readiness_audit_ref_id"] = audit_model.id
                        route_lineage["route_readiness_audit_submitted_order_created"] = bool(
                            audit_model.submitted_order_created
                        )
                        if (
                            audit_model.overall_status
                            != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
                        ):
                            reason_codes.append("route_readiness_audit_not_ready")
                            reason_codes.append(
                                f"route_readiness_audit_status_{audit_model.overall_status.value}"
                            )
                        if not audit_model.child_intent_created:
                            reason_codes.append(
                                "route_readiness_audit_child_intent_not_created"
                            )
                        audit_checks = {
                            "audit_routing_assessment_id_mismatch": (
                                assessment_id,
                                audit_model.routing_assessment_id,
                            ),
                            "audit_desired_trade_key_mismatch": (
                                model.desired_trade_key,
                                audit_model.desired_trade_key,
                            ),
                            "audit_instrument_ref_mismatch": (
                                model.instrument_ref_id,
                                audit_model.instrument_ref_id,
                            ),
                            "audit_instrument_key_mismatch": (
                                model.instrument_key,
                                audit_model.instrument_key,
                            ),
                            "audit_symbol_mismatch": (model.symbol, audit_model.symbol),
                        }
                        for reason_code, (left, right) in audit_checks.items():
                            if left != right:
                                reason_codes.append(reason_code)

                        readiness_candidate_model = session.scalar(
                            select(RouteReadinessCandidateAuditModel).where(
                                RouteReadinessCandidateAuditModel.route_readiness_audit_ref_id
                                == audit_model.id,
                                RouteReadinessCandidateAuditModel.binding_ref_id
                                == model.mandate_account_binding_ref_id,
                                RouteReadinessCandidateAuditModel.venue_account_ref_id
                                == model.venue_account_ref_id,
                            )
                        )
                        if readiness_candidate_model is None:
                            reason_codes.append("route_readiness_candidate_not_found")
                        else:
                            route_lineage["route_readiness_candidate_ref_id"] = (
                                readiness_candidate_model.id
                            )
                            if (
                                readiness_candidate_model.status
                                != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
                            ):
                                reason_codes.append("route_readiness_candidate_not_ready")
                            candidate_checks = {
                                "route_readiness_candidate_binding_ref_mismatch": (
                                    model.mandate_account_binding_ref_id,
                                    readiness_candidate_model.binding_ref_id,
                                ),
                                "route_readiness_candidate_binding_key_mismatch": (
                                    model.binding_key,
                                    readiness_candidate_model.binding_key,
                                ),
                                "route_readiness_candidate_venue_account_ref_mismatch": (
                                    model.venue_account_ref_id,
                                    readiness_candidate_model.venue_account_ref_id,
                                ),
                                "route_readiness_candidate_venue_account_key_mismatch": (
                                    provenance_selected_venue_account_key,
                                    readiness_candidate_model.venue_account_key,
                                ),
                                "route_readiness_candidate_venue_mismatch": (
                                    provenance_selected_venue,
                                    readiness_candidate_model.venue,
                                ),
                                "route_readiness_candidate_exchange_symbol_mismatch": (
                                    provenance_selected_exchange_symbol,
                                    readiness_candidate_model.exchange_symbol,
                                ),
                            }
                            for reason_code, (left, right) in candidate_checks.items():
                                if left != right:
                                    reason_codes.append(reason_code)
                            (
                                quote_reason_codes,
                                quote_missing_data,
                                quote_stale_data,
                            ) = self._route_readiness_candidate_quote_freshness_blockers(
                                readiness_candidate_model,
                                checked_at=_utcnow(),
                            )
                            reason_codes.extend(quote_reason_codes)
                            missing_data.extend(quote_missing_data)
                            stale_data.extend(quote_stale_data)

        provenance_binding_ref_targets = [model.mandate_account_binding_ref_id]
        provenance_binding_key_targets = [model.binding_key]
        provenance_venue_account_ref_targets = [model.venue_account_ref_id]
        provenance_venue_account_key_targets: list[object] = []
        provenance_venue_targets: list[object] = []
        provenance_exchange_symbol_targets: list[object] = []

        if choice_model is not None:
            provenance_binding_ref_targets.append(choice_model.selected_binding_ref_id)
            provenance_binding_key_targets.append(choice_model.selected_binding_key)
            provenance_venue_account_ref_targets.append(choice_model.selected_venue_account_ref_id)
            provenance_venue_account_key_targets.append(choice_model.selected_venue_account_key)
            provenance_venue_targets.append(choice_model.selected_venue)
        if candidate_model is not None:
            provenance_binding_ref_targets.append(candidate_model.binding_ref_id)
            provenance_binding_key_targets.append(candidate_model.binding_key)
            provenance_venue_account_ref_targets.append(candidate_model.venue_account_ref_id)
            provenance_venue_account_key_targets.append(candidate_model.venue_account_key)
            provenance_venue_targets.append(candidate_model.venue)
            provenance_exchange_symbol_targets.append(candidate_model.exchange_symbol)
        if binding_model is not None:
            provenance_binding_ref_targets.append(binding_model.id)
            provenance_binding_key_targets.append(binding_model.binding_key)
        if account_model is not None:
            provenance_venue_account_ref_targets.append(account_model.id)
            provenance_venue_account_key_targets.append(account_model.venue_account_key)
            provenance_venue_targets.append(account_model.venue)

        provenance_checks = {
            "routed_provenance_binding_ref_mismatch": (
                provenance_selected_binding_ref_id,
                provenance_binding_ref_targets,
            ),
            "routed_provenance_binding_key_mismatch": (
                provenance_selected_binding_key,
                provenance_binding_key_targets,
            ),
            "routed_provenance_venue_account_ref_mismatch": (
                provenance_selected_venue_account_ref_id,
                provenance_venue_account_ref_targets,
            ),
            "routed_provenance_venue_account_key_mismatch": (
                provenance_selected_venue_account_key,
                provenance_venue_account_key_targets,
            ),
            "routed_provenance_venue_mismatch": (
                provenance_selected_venue,
                provenance_venue_targets,
            ),
            "routed_provenance_exchange_symbol_mismatch": (
                provenance_selected_exchange_symbol,
                provenance_exchange_symbol_targets,
            ),
        }
        for reason_code, (provenance_value, expected_values) in provenance_checks.items():
            if not expected_values or any(provenance_value != expected for expected in expected_values):
                reason_codes.append(reason_code)

        reason_codes = sorted(set(reason_codes))
        missing_data = sorted(set(missing_data))
        stale_data = sorted(set(stale_data))
        route_lineage["valid"] = not reason_codes and not missing_data and not stale_data
        route_lineage["reason_codes"] = reason_codes
        route_lineage["missing_data"] = missing_data
        route_lineage["stale_data"] = stale_data
        return True, reason_codes, missing_data, route_lineage

    @classmethod
    def _routed_order_shape_policy_blockers(
        cls,
        model: OrderIntentModel,
        policy_raw: object,
    ) -> tuple[list[str], list[str]]:
        if policy_raw is None:
            return ["routed_order_shape_policy_missing"], [
                "routed_order_shape_policy_missing"
            ]
        if not isinstance(policy_raw, dict) or not policy_raw:
            return ["routed_order_shape_policy_malformed"], []

        reason_codes: list[str] = []
        mismatch_codes: list[str] = []

        policy_order_type = cls._coerce_routed_policy_order_type(
            policy_raw.get("order_type")
        )
        if policy_order_type is None:
            reason_codes.append("routed_order_shape_policy_malformed")
        elif policy_order_type != model.order_type:
            mismatch_codes.append("routed_order_type_policy_mismatch")

        policy_limit_price, limit_price_malformed = (
            cls._coerce_routed_policy_limit_price(policy_raw.get("limit_price"))
        )
        if limit_price_malformed:
            reason_codes.append("routed_order_shape_policy_malformed")
        else:
            if policy_order_type == OrderType.LIMIT:
                if policy_limit_price is None or policy_limit_price <= Decimal("0"):
                    reason_codes.append("routed_order_shape_policy_malformed")
            elif policy_order_type == OrderType.MARKET and policy_limit_price is not None:
                reason_codes.append("routed_order_shape_policy_malformed")
            if policy_limit_price != model.limit_price:
                mismatch_codes.append("routed_limit_price_policy_mismatch")

        policy_reduce_only = policy_raw.get("reduce_only")
        if not isinstance(policy_reduce_only, bool):
            reason_codes.append("routed_order_shape_policy_malformed")
        elif policy_reduce_only != bool(model.reduce_only):
            mismatch_codes.append("routed_reduce_only_policy_mismatch")

        if policy_raw.get("blocked") is not False:
            reason_codes.append("routed_order_shape_policy_malformed")

        if mismatch_codes:
            reason_codes.append("routed_order_shape_policy_intent_mismatch")
            reason_codes.extend(mismatch_codes)

        return sorted(set(reason_codes)), []

    @staticmethod
    def _coerce_routed_policy_order_type(value: object) -> OrderType | None:
        if isinstance(value, OrderType):
            return value
        if isinstance(value, str) and value:
            try:
                return OrderType(value)
            except ValueError:
                try:
                    return OrderType[value.upper()]
                except KeyError:
                    return None
        return None

    @staticmethod
    def _coerce_routed_policy_limit_price(
        value: object,
    ) -> tuple[Decimal | None, bool]:
        if value is None or value == "":
            return None, False
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None, True
        try:
            if not parsed.is_finite():
                return None, True
        except InvalidOperation:
            return None, True
        return parsed, False

    @staticmethod
    def _candidate_symbol_mapping_blockers(
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

    @classmethod
    def _route_readiness_candidate_quote_freshness_blockers(
        cls,
        candidate_model: RouteReadinessCandidateAuditModel,
        *,
        checked_at: datetime,
    ) -> tuple[list[str], list[str], list[str]]:
        fact_snapshot = dict(candidate_model.fact_snapshot_json or {})
        observed_at_raw = fact_snapshot.get("quote_observed_at")
        if observed_at_raw is None or observed_at_raw == "":
            return ["quote_freshness_unknown"], ["quote_freshness_unknown"], []
        observed_at = cls._parse_routed_quote_observed_at(observed_at_raw)
        if observed_at is None:
            return ["quote_observed_at_malformed"], ["quote_observed_at_malformed"], []
        threshold_seconds = cls._routed_quote_freshness_threshold_seconds(
            fact_snapshot.get("quote_freshness_threshold_seconds")
        )
        if threshold_seconds is None:
            return (
                ["quote_freshness_threshold_invalid"],
                ["quote_freshness_threshold_invalid"],
                [],
            )
        checked_at_aware = (
            checked_at if checked_at.tzinfo is not None else checked_at.replace(tzinfo=UTC)
        )
        age_seconds = Decimal(str((checked_at_aware - observed_at).total_seconds()))
        if age_seconds > threshold_seconds:
            return ["quote_stale_at_readiness"], [], ["quote_stale_at_readiness"]
        return [], [], []

    @staticmethod
    def _parse_routed_quote_observed_at(value: object) -> datetime | None:
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
    def _routed_quote_freshness_threshold_seconds(value: object) -> Decimal | None:
        if value is None or value == "":
            return Decimal(str(_ROUTED_QUOTE_FRESHNESS_SECONDS))
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

    def _attach_routed_lineage_to_preview(
        self,
        preview: PreparedVenueOrder,
        route_lineage: dict[str, object],
    ) -> PreparedVenueOrder:
        routed_submission_enabled = self.settings.execution.routed_submission_phase_enabled
        live_submission_enabled = self.settings.execution.live_submission_phase_enabled
        submission_deferred_reason_codes: list[str] = []
        if not routed_submission_enabled:
            submission_deferred_reason_codes.append("routed_submission_deferred")
        if not live_submission_enabled:
            submission_deferred_reason_codes.append("phase_live_submit_deferred")
        payload = dict(preview.payload or {})
        payload["routed_lineage"] = _jsonable(route_lineage)
        payload["routed_submission_enabled"] = routed_submission_enabled
        payload["live_submission_enabled"] = live_submission_enabled
        payload["non_submitting"] = True
        payload["explicit_submit_required"] = True
        payload["submission_deferred"] = bool(submission_deferred_reason_codes)
        payload["submission_deferred_reason_codes"] = submission_deferred_reason_codes
        return replace(preview, payload=payload)

    def _blocked_routed_prepared_order(
        self,
        intent: OrderIntent,
        *,
        reason_codes: list[str],
        missing_data: list[str],
        route_lineage: dict[str, object],
    ) -> PreparedVenueOrder:
        normalized_reason_codes = sorted(
            set(["routed_lineage_invalid", *reason_codes, *missing_data])
        )
        payload = {
            "phase_boundary": "phase_5_3_routed_preparation_readiness",
            "routed_lineage": _jsonable(route_lineage),
            "missing_data": list(missing_data),
            "non_submitting": True,
            "submission_deferred": True,
            "prepared_order_created": False,
            "submitted_order_created": False,
            "auto_submit": False,
            "fanout_created": False,
            "scoring_created": False,
            "target_reselection": False,
        }
        return PreparedVenueOrder(
            intent_id=intent.intent_id,
            desired_trade_key=intent.desired_trade_key,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=str(route_lineage.get("selected_venue") or route_lineage.get("venue") or "unknown"),
            support_level=VenueSupportLevel.QA_READ_ONLY,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            exchange_symbol=(
                str(route_lineage["selected_exchange_symbol"])
                if route_lineage.get("selected_exchange_symbol") is not None
                else None
            ),
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            reduce_only=intent.reduce_only,
            time_in_force=None,
            client_order_id=None,
            preview_status=VenueOrderPreviewStatus.REJECTED,
            reason_codes=normalized_reason_codes,
            payload=payload,
            constraints=None,
            venue_capabilities=None,
            account_connectivity=None,
            prepared_at=_utcnow(),
        )

    def _build_readiness_assessment(
        self,
        *,
        intent: OrderIntent,
        intent_ref_id: str | None,
        venue: str,
        preview: PreparedVenueOrder,
        binding_model: MandateAccountBindingModel | None,
        venue_account_model: VenueAccountModel | None,
        routed_lineage: dict[str, object] | None = None,
    ) -> ExecutionReadinessAssessment:
        capabilities = preview.venue_capabilities
        connectivity = preview.account_connectivity
        if capabilities is None or connectivity is None:
            raise ValueError("Prepared venue order is missing capability or connectivity context.")

        reason_codes: list[str] = []
        outcome = ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
        live_phase_enabled = self.settings.execution.live_submission_phase_enabled
        routed_submission_enabled = self.settings.execution.routed_submission_phase_enabled
        private_state_required = self.settings.execution.require_private_state_for_submission_readiness

        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE:
            outcome = ExecutionReadinessOutcome.INELIGIBLE
            reason_codes.extend(preview.reason_codes or ["preview_rejected"])
            if "preview_rejected" not in reason_codes:
                reason_codes.insert(0, "preview_rejected")
        else:
            if intent.venue_account_ref_id is None or intent.binding_key is None:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("missing_binding_or_account_context")
            elif binding_model is not None and not binding_model.enabled:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("binding_disabled")
            elif binding_model is not None and not binding_model.routing_eligible:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("binding_not_routing_eligible")
            elif binding_model is not None and not binding_model.trading_enabled:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("binding_trading_disabled")
            elif venue_account_model is not None and not venue_account_model.is_active:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("venue_account_inactive")
            elif venue_account_model is not None and not venue_account_model.trading_enabled:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_POLICY
                reason_codes.append("venue_account_trading_disabled")
            elif intent.instrument_key is None or intent.instrument_ref_id is None:
                outcome = ExecutionReadinessOutcome.INELIGIBLE
                reason_codes.append("instrument_identity_missing")
            elif not capabilities.supports_order_submission:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_VENUE
                reason_codes.append("venue_submission_unsupported")
            elif capabilities.support_level == VenueSupportLevel.QA_READ_ONLY:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_VENUE
                reason_codes.append("venue_not_execution_preparable")
            elif not capabilities.adapter_supports_order_submission:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ADAPTER
                reason_codes.append("adapter_submission_unimplemented")
            elif preview.exchange_symbol is None:
                outcome = ExecutionReadinessOutcome.INELIGIBLE
                reason_codes.append("missing_symbol_mapping")
            elif connectivity.read_only_mode:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("read_only_mode_enabled")
            elif connectivity.dry_run_mode or self.settings.execution.dry_run:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("dry_run_only")
            elif not connectivity.account_identifier_configured:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("account_identifier_missing")
            elif not connectivity.submission_authorized:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("account_not_authorized")
            elif not connectivity.account_snapshot_available and private_state_required:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("private_state_unavailable")
            elif not connectivity.private_account_sync_enabled and private_state_required:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("private_state_sync_disabled")
            elif not capabilities.supports_account_sync and private_state_required:
                outcome = ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
                reason_codes.append("venue_private_state_unavailable")
            elif routed_lineage is not None and (
                not routed_submission_enabled or not live_phase_enabled
            ):
                outcome = ExecutionReadinessOutcome.PHASE_BLOCKED
                if not routed_submission_enabled:
                    reason_codes.append("routed_submission_deferred")
                if not live_phase_enabled:
                    reason_codes.append("phase_live_submit_deferred")
            elif not live_phase_enabled:
                outcome = ExecutionReadinessOutcome.PHASE_BLOCKED
                reason_codes.append("phase_live_submit_deferred")

        eligible_in_principle = outcome in {
            ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION,
            ExecutionReadinessOutcome.PHASE_BLOCKED,
        }
        message = self._readiness_message(outcome, reason_codes)
        fingerprint_payload = {
            "intent_id": intent.intent_id,
            "desired_trade_key": intent.desired_trade_key,
            "binding_key": intent.binding_key,
            "venue": venue,
            "preview_status": preview.preview_status.value,
            "preview_reason_codes": list(preview.reason_codes),
            "support_level": preview.support_level.value,
            "venue_supports_order_submission": capabilities.supports_order_submission,
            "adapter_supports_order_submission": capabilities.adapter_supports_order_submission,
            "submission_authorized": connectivity.submission_authorized,
            "account_connected": connectivity.account_identifier_configured,
            "private_state_required": private_state_required,
            "private_state_ready": (
                connectivity.private_account_sync_enabled and connectivity.account_snapshot_available
            ),
            "read_only_mode": connectivity.read_only_mode,
            "dry_run_mode": connectivity.dry_run_mode or self.settings.execution.dry_run,
            "live_submission_phase_enabled": live_phase_enabled,
            "routed_submission_phase_enabled": routed_submission_enabled,
            "binding_enabled": binding_model.enabled if binding_model is not None else None,
            "binding_routing_eligible": (
                binding_model.routing_eligible if binding_model is not None else None
            ),
            "binding_trading_enabled": binding_model.trading_enabled if binding_model is not None else None,
            "venue_account_active": venue_account_model.is_active if venue_account_model is not None else None,
            "venue_account_trading_enabled": (
                venue_account_model.trading_enabled if venue_account_model is not None else None
            ),
            "routed_child_intent": routed_lineage is not None,
            "routing_assessment_id": (
                routed_lineage.get("routing_assessment_id") if routed_lineage is not None else None
            ),
            "routing_target_choice_id": (
                routed_lineage.get("routing_target_choice_id") if routed_lineage is not None else None
            ),
        }
        readiness_key = _json_fingerprint(fingerprint_payload)
        return ExecutionReadinessAssessment(
            readiness_evaluation_id=f"ready-{readiness_key[:24]}",
            readiness_evaluation_key=readiness_key,
            environment=intent.environment,
            intent_ref_id=intent_ref_id,
            intent_id=intent.intent_id,
            mandate_desired_trade_ref_id=intent.mandate_desired_trade_ref_id,
            desired_trade_key=intent.desired_trade_key,
            client_ref_id=intent.client_ref_id,
            strategy_mandate_ref_id=intent.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=intent.mandate_account_binding_ref_id,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            venue=venue,
            support_level=preview.support_level,
            preview_status=preview.preview_status,
            outcome=outcome,
            eligible_for_submission_in_principle=eligible_in_principle,
            live_submission_phase_enabled=live_phase_enabled,
            venue_supports_order_submission=capabilities.supports_order_submission,
            adapter_supports_order_submission=capabilities.adapter_supports_order_submission,
            adapter_supports_order_cancel=capabilities.adapter_supports_order_cancel,
            adapter_supports_order_amend=capabilities.adapter_supports_order_amend,
            submission_authorized=connectivity.submission_authorized,
            account_connected=connectivity.account_identifier_configured,
            private_state_required=private_state_required,
            private_state_ready=(
                connectivity.private_account_sync_enabled and connectivity.account_snapshot_available
            ),
            reason_codes=reason_codes,
            message=message,
            prepared_order=preview,
            evaluated_at=_utcnow(),
            provenance={
                "phase_boundary": (
                    "phase_5_3_routed_preparation_readiness"
                    if routed_lineage is not None
                    else "phase_4_3"
                ),
                "fingerprint_payload": fingerprint_payload,
                "prepared_order_preview": self._preview_summary(preview),
                "venue_capabilities": _jsonable(asdict(capabilities)),
                "account_connectivity": _jsonable(asdict(connectivity)),
                "routed_lineage": _jsonable(routed_lineage or {}),
                "routed_submission_enabled": (
                    routed_submission_enabled if routed_lineage is not None else False
                ),
                "routed_submission_deferred": (
                    routed_lineage is not None and "routed_submission_deferred" in reason_codes
                ),
                "submitted_order_created": False,
                "auto_submit": False,
                "fanout_created": False,
                "scoring_created": False,
                "target_reselection": False,
            },
        )

    def _build_routed_lineage_blocked_readiness(
        self,
        *,
        intent: OrderIntent,
        intent_ref_id: str | None,
        preview: PreparedVenueOrder,
        reason_codes: list[str],
        missing_data: list[str],
        route_lineage: dict[str, object],
    ) -> ExecutionReadinessAssessment:
        normalized_reason_codes = sorted(
            set(["routed_lineage_invalid", *reason_codes, *missing_data])
        )
        fingerprint_payload = {
            "intent_id": intent.intent_id,
            "desired_trade_key": intent.desired_trade_key,
            "binding_key": intent.binding_key,
            "venue_account_ref_id": intent.venue_account_ref_id,
            "reason_codes": normalized_reason_codes,
            "missing_data": list(missing_data),
            "routing_assessment_id": route_lineage.get("routing_assessment_id"),
            "routing_target_choice_id": route_lineage.get("routing_target_choice_id"),
            "phase_boundary": "phase_5_3_routed_preparation_readiness",
        }
        readiness_key = _json_fingerprint(fingerprint_payload)
        return ExecutionReadinessAssessment(
            readiness_evaluation_id=f"ready-{readiness_key[:24]}",
            readiness_evaluation_key=readiness_key,
            environment=intent.environment,
            intent_ref_id=intent_ref_id,
            intent_id=intent.intent_id,
            mandate_desired_trade_ref_id=intent.mandate_desired_trade_ref_id,
            desired_trade_key=intent.desired_trade_key,
            client_ref_id=intent.client_ref_id,
            strategy_mandate_ref_id=intent.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=intent.mandate_account_binding_ref_id,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            venue=preview.venue,
            support_level=preview.support_level,
            preview_status=preview.preview_status,
            outcome=ExecutionReadinessOutcome.BLOCKED_BY_POLICY,
            eligible_for_submission_in_principle=False,
            live_submission_phase_enabled=self.settings.execution.live_submission_phase_enabled,
            venue_supports_order_submission=False,
            adapter_supports_order_submission=False,
            adapter_supports_order_cancel=False,
            adapter_supports_order_amend=False,
            submission_authorized=False,
            account_connected=False,
            private_state_required=self.settings.execution.require_private_state_for_submission_readiness,
            private_state_ready=False,
            reason_codes=normalized_reason_codes,
            message="Routed child intent failed route-lineage validation before preparation/readiness.",
            prepared_order=preview,
            evaluated_at=_utcnow(),
            provenance={
                "phase_boundary": "phase_5_3_routed_preparation_readiness",
                "fingerprint_payload": fingerprint_payload,
                "prepared_order_preview": self._preview_summary(preview),
                "routed_lineage": _jsonable(route_lineage),
                "missing_data": list(missing_data),
                "non_submitting": True,
                "submitted_order_created": False,
                "auto_submit": False,
                "fanout_created": False,
                "scoring_created": False,
                "target_reselection": False,
            },
        )

    async def _mark_submission_failure(
        self,
        *,
        intent_id: str,
        readiness: ExecutionReadinessAssessment,
        reason_codes: list[str],
        message: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        await self._record_submission_block(
            intent_id=intent_id,
            readiness=readiness,
            reason_codes=reason_codes,
            message=message,
            payload=payload,
            preserve_status=False,
            failure_key="last_submission_failure",
            adapter_submit_called=True,
        )

    @staticmethod
    def _is_routed_phase_boundary_submission_block(
        readiness: ExecutionReadinessAssessment,
    ) -> bool:
        reason_codes = set(readiness.reason_codes or [])
        provenance = dict(readiness.provenance or {})
        routed_lineage = dict(provenance.get("routed_lineage") or {})
        return (
            readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
            and bool(routed_lineage)
            and bool(
                reason_codes
                & {
                    "routed_submission_deferred",
                    "phase_live_submit_deferred",
                }
            )
        )

    async def _record_submission_block(
        self,
        *,
        intent_id: str,
        readiness: ExecutionReadinessAssessment,
        reason_codes: list[str],
        message: str,
        payload: dict[str, object] | None = None,
        preserve_status: bool = False,
        failure_key: str = "last_submission_block",
        adapter_submit_called: bool = False,
    ) -> None:
        with self._session_factory() as session:
            model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == intent_id,
                )
            )
            if model is None:
                return
            provenance = dict(model.provenance or {})
            attempts = list(provenance.get("submission_attempts", []))
            attempt_payload = {
                "attempted_at": _utcnow().isoformat(),
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "readiness_outcome": readiness.outcome.value,
                "reason_codes": list(reason_codes),
                "message": message,
                "payload": _jsonable(payload or {}),
                "submitted_order_created": False,
                "adapter_submit_called": adapter_submit_called,
            }
            if self._is_routed_phase_boundary_submission_block(readiness):
                reason_code_set = set(reason_codes)
                readiness_provenance = dict(readiness.provenance or {})
                routed_submission_enabled = bool(
                    readiness_provenance.get("routed_submission_enabled", False)
                )
                attempt_payload["phase_boundary"] = "phase_5_4_routed_submission_gate"
                attempt_payload["routed_submission_deferred"] = (
                    "routed_submission_deferred" in reason_code_set
                )
                attempt_payload["live_submission_deferred"] = (
                    "phase_live_submit_deferred" in reason_code_set
                )
                attempt_payload["routed_submission_enabled"] = routed_submission_enabled
                attempt_payload["live_submission_enabled"] = readiness.live_submission_phase_enabled
                attempt_payload["routed_lineage"] = _jsonable(
                    dict(readiness_provenance.get("routed_lineage") or {})
                )
            attempts.append(
                attempt_payload
            )
            provenance["submission_attempts"] = attempts
            provenance[failure_key] = attempts[-1]
            model.provenance = provenance
            if not preserve_status:
                model.status = OrderIntentStatus.SUBMISSION_FAILED
            session.add(model)
            session.commit()

    @staticmethod
    def _submitted_order_with_routed_lineage(
        submitted: SubmittedOrder,
        *,
        intent: OrderIntent,
        readiness: ExecutionReadinessAssessment,
    ) -> SubmittedOrder:
        routed_lineage = dict(readiness.provenance.get("routed_lineage") or {})
        if not routed_lineage:
            return submitted
        raw_payload = dict(submitted.raw_payload or {})
        intent_provenance = dict(intent.provenance or {})
        routed_order_shape_policy = intent_provenance.get("routed_order_shape_policy")
        routed_submission_payload = {
            "phase_boundary": "phase_5_4_explicit_routed_submission_handoff",
            "source": (
                "routing_target_recommendation"
                if routed_lineage.get("recommendation_backed_child_intent")
                else "routing_target_choice"
            ),
            "explicit_action_required": True,
            "explicit_submit_action": True,
            "auto_submit": False,
            "fanout_created": False,
            "allocation_created": False,
            "scoring_created": False,
            "route_executor_created": False,
            "target_reselection": False,
            "same_target_only": True,
            "same_account_only": True,
            "same_venue_only": True,
            "submitted_order_created": True,
            "routed_submission_enabled": True,
            "intent_id": intent.intent_id,
            "readiness_evaluation_id": readiness.readiness_evaluation_id,
            "desired_trade_key": intent.desired_trade_key,
            "routing_assessment_id": routed_lineage.get("routing_assessment_id"),
            "route_readiness_audit_id": routed_lineage.get("route_readiness_audit_id"),
            "routing_target_recommendation_id": routed_lineage.get(
                "routing_target_recommendation_id"
            ),
            "routing_target_choice_id": routed_lineage.get("routing_target_choice_id"),
            "recommendation_policy_name": routed_lineage.get(
                "recommendation_policy_name"
            ),
            "selected_binding_ref_id": routed_lineage.get("selected_binding_ref_id"),
            "selected_binding_key": routed_lineage.get("selected_binding_key"),
            "selected_venue_account_ref_id": routed_lineage.get("selected_venue_account_ref_id"),
            "selected_venue_account_key": routed_lineage.get("selected_venue_account_key"),
            "selected_venue": routed_lineage.get("selected_venue"),
            "selected_exchange_symbol": routed_lineage.get("selected_exchange_symbol"),
            "routed_lineage": _jsonable(routed_lineage),
        }
        if isinstance(routed_order_shape_policy, dict):
            routed_submission_payload["routed_order_shape_policy"] = _jsonable(
                routed_order_shape_policy
            )
        raw_payload["routed_submission"] = routed_submission_payload
        return replace(submitted, raw_payload=_jsonable(raw_payload))

    def _persist_submitted_order(
        self,
        intent: OrderIntent,
        readiness: ExecutionReadinessAssessment,
        submitted: SubmittedOrder,
        *,
        allow_multiple_for_intent: bool = False,
        recovery_parent_submitted_order_id: str | None = None,
    ) -> SubmittedOrder:
        event_type = self._submission_event_type(submitted.status)
        observed_at = submitted.acknowledged_at or submitted.submitted_at
        with self._session_factory() as session:
            existing = None
            if not allow_multiple_for_intent:
                existing = session.scalar(
                    select(SubmittedOrderModel).where(
                        SubmittedOrderModel.environment == self.settings.app.environment,
                        SubmittedOrderModel.intent_id == intent.intent_id,
                    )
                )
            if existing is None:
                model = SubmittedOrderModel(
                    environment=intent.environment,
                    submitted_order_id=submitted.submitted_order_id,
                    intent_id=intent.intent_id,
                    client_order_id=submitted.client_order_id,
                    venue_account_ref_id=submitted.venue_account_ref_id,
                    venue=submitted.venue,
                    account_address=submitted.account_address,
                    instrument_ref_id=submitted.instrument_ref_id,
                    symbol_id=self._lookup_symbol_id(
                        session,
                        instrument_ref_id=submitted.instrument_ref_id,
                        venue=submitted.venue,
                        symbol=submitted.symbol or intent.symbol,
                    ),
                    symbol=submitted.symbol or intent.symbol,
                    side=submitted.side or intent.side,
                    order_type=submitted.order_type or intent.order_type,
                    limit_price=submitted.limit_price,
                    original_quantity=(
                        submitted.original_quantity
                        if submitted.original_quantity is not None
                        else intent.quantity
                    ),
                    remaining_quantity=(
                        submitted.remaining_quantity
                        if submitted.remaining_quantity is not None
                        else intent.quantity
                    ),
                    reduce_only=submitted.reduce_only,
                    exchange_order_id=submitted.exchange_order_id,
                    status=submitted.status,
                    reconciliation_status=submitted.reconciliation_status,
                    submitted_at=submitted.submitted_at,
                    acknowledged_at=submitted.acknowledged_at,
                    filled_quantity=(
                        submitted.filled_quantity
                        if submitted.filled_quantity is not None
                        else Decimal("0")
                    ),
                    average_fill_price=submitted.average_fill_price,
                    last_fill_at=submitted.last_fill_at,
                    last_reconciled_at=submitted.last_reconciled_at,
                    status_reason_code=submitted.status_reason_code,
                    status_message=submitted.status_message,
                    reason_codes=list(submitted.reason_codes),
                    cancelable_in_principle=submitted.cancelable_in_principle,
                    amendable_in_principle=submitted.amendable_in_principle,
                    raw_payload=_jsonable(submitted.raw_payload),
                )
                session.add(model)
            else:
                existing.client_order_id = submitted.client_order_id
                existing.venue_account_ref_id = submitted.venue_account_ref_id
                existing.venue = submitted.venue
                existing.account_address = submitted.account_address
                existing.instrument_ref_id = submitted.instrument_ref_id
                existing.symbol = submitted.symbol or intent.symbol
                existing.side = submitted.side or intent.side
                existing.order_type = submitted.order_type or intent.order_type
                existing.limit_price = submitted.limit_price
                existing.original_quantity = (
                    submitted.original_quantity
                    if submitted.original_quantity is not None
                    else intent.quantity
                )
                existing.remaining_quantity = (
                    submitted.remaining_quantity
                    if submitted.remaining_quantity is not None
                    else intent.quantity
                )
                existing.reduce_only = submitted.reduce_only
                existing.exchange_order_id = submitted.exchange_order_id
                existing.status = submitted.status
                existing.reconciliation_status = submitted.reconciliation_status
                existing.submitted_at = submitted.submitted_at
                existing.acknowledged_at = submitted.acknowledged_at
                existing.filled_quantity = (
                    submitted.filled_quantity
                    if submitted.filled_quantity is not None
                    else Decimal("0")
                )
                existing.average_fill_price = submitted.average_fill_price
                existing.last_fill_at = submitted.last_fill_at
                existing.last_reconciled_at = submitted.last_reconciled_at
                existing.status_reason_code = submitted.status_reason_code
                existing.status_message = submitted.status_message
                existing.reason_codes = list(submitted.reason_codes)
                existing.cancelable_in_principle = submitted.cancelable_in_principle
                existing.amendable_in_principle = submitted.amendable_in_principle
                existing.raw_payload = _jsonable(submitted.raw_payload)
                model = existing
                session.add(existing)
            self._add_submitted_order_event_model(
                session,
                submitted=submitted,
                event_type=event_type,
                observed_at=observed_at,
                message=submitted.status_message,
                reason_codes=list(submitted.reason_codes),
                raw_payload=submitted.raw_payload,
            )
            intent_model = session.scalar(
                select(OrderIntentModel).where(
                    OrderIntentModel.environment == self.settings.app.environment,
                    OrderIntentModel.intent_id == intent.intent_id,
                )
            )
            if intent_model is not None:
                provenance = dict(intent_model.provenance or {})
                attempt_payload = {
                    "submitted_order_id": submitted.submitted_order_id,
                    "exchange_order_id": submitted.exchange_order_id,
                    "client_order_id": submitted.client_order_id,
                    "status": submitted.status.value,
                    "reconciliation_status": submitted.reconciliation_status.value,
                    "reason_codes": list(submitted.reason_codes),
                    "status_reason_code": submitted.status_reason_code,
                    "status_message": submitted.status_message,
                    "submitted_at": submitted.submitted_at.isoformat(),
                    "acknowledged_at": (
                        submitted.acknowledged_at.isoformat()
                        if submitted.acknowledged_at is not None
                        else None
                    ),
                    "readiness_evaluation_id": readiness.readiness_evaluation_id,
                }
                if recovery_parent_submitted_order_id is not None:
                    attempt_payload["recovery_parent_submitted_order_id"] = recovery_parent_submitted_order_id
                attempts = list(provenance.get("submission_attempts", []))
                attempts.append(attempt_payload)
                provenance["submission_attempts"] = attempts
                provenance["latest_submission"] = attempt_payload
                provenance["submission"] = attempt_payload
                intent_model.provenance = provenance
                intent_model.status = (
                    OrderIntentStatus.REJECTED
                    if submitted.status == SubmittedOrderStatus.REJECTED
                    else OrderIntentStatus.SUBMITTED
                )
                session.add(intent_model)
                self._mark_recommendation_submitted_order_created(
                    session,
                    intent_model=intent_model,
                    submitted=submitted,
                    readiness=readiness,
                )
            session.commit()
            return self._submitted_order_from_model(model)

    def _mark_recommendation_submitted_order_created(
        self,
        session: Any,
        *,
        intent_model: OrderIntentModel,
        submitted: SubmittedOrder,
        readiness: ExecutionReadinessAssessment,
    ) -> None:
        intent_provenance = dict(intent_model.provenance or {})
        recommendation_id = intent_provenance.get("routing_target_recommendation_id")
        if not isinstance(recommendation_id, str) or not recommendation_id:
            return
        recommendation_model = session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.environment == self.settings.app.environment,
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation_id,
            )
        )
        if recommendation_model is None:
            return
        submitted_at = submitted.submitted_at or _utcnow()
        submitted_at_iso = submitted_at.isoformat()
        recommendation_model.submitted_order_created = True
        recommendation_provenance = dict(recommendation_model.provenance_json or {})
        submitted_order_ids = [
            str(item)
            for item in recommendation_provenance.get("submitted_order_ids", [])
            if isinstance(item, str) and item
        ]
        first_submitted_order_id = (
            recommendation_provenance.get("first_submitted_order_id")
            or recommendation_provenance.get("submitted_order_id")
            or submitted.submitted_order_id
        )
        first_submitted_at = (
            recommendation_provenance.get("first_submitted_order_created_at")
            or recommendation_provenance.get("submitted_order_created_at")
            or submitted_at_iso
        )
        if submitted.submitted_order_id not in submitted_order_ids:
            submitted_order_ids.append(submitted.submitted_order_id)
        recommendation_provenance.update(
            {
                "submitted_order_created": True,
                "submitted_order_id": str(first_submitted_order_id),
                "first_submitted_order_id": str(first_submitted_order_id),
                "first_submitted_order_created_at": str(first_submitted_at),
                "latest_submitted_order_id": submitted.submitted_order_id,
                "latest_submitted_order_checked_at": submitted_at_iso,
                "submitted_order_ids": submitted_order_ids,
                "intent_id": intent_model.intent_id,
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "submitted_order_created_at": str(first_submitted_at),
                "submitted_order_last_checked_at": submitted_at_iso,
                "explicit_submit_action": True,
                "auto_submit": False,
                "fanout_created": False,
                "allocation_created": False,
                "scoring_created": False,
                "route_executor_created": False,
                "target_reselection": False,
            }
        )
        recommendation_model.provenance_json = _jsonable(recommendation_provenance)
        session.add(recommendation_model)

        audit_model = None
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
        audit_model.submitted_order_created = True
        audit_provenance = dict(audit_model.provenance_json or {})
        audit_submitted_order_ids = [
            str(item)
            for item in audit_provenance.get("submitted_order_ids", [])
            if isinstance(item, str) and item
        ]
        audit_first_submitted_order_id = (
            audit_provenance.get("first_submitted_order_id")
            or audit_provenance.get("submitted_order_id")
            or first_submitted_order_id
        )
        audit_first_submitted_at = (
            audit_provenance.get("first_submitted_order_created_at")
            or audit_provenance.get("submitted_order_created_at")
            or first_submitted_at
        )
        if submitted.submitted_order_id not in audit_submitted_order_ids:
            audit_submitted_order_ids.append(submitted.submitted_order_id)
        audit_provenance.update(
            {
                "submitted_order_created": True,
                "submitted_order_id": str(audit_first_submitted_order_id),
                "first_submitted_order_id": str(audit_first_submitted_order_id),
                "first_submitted_order_created_at": str(audit_first_submitted_at),
                "latest_submitted_order_id": submitted.submitted_order_id,
                "latest_submitted_order_checked_at": submitted_at_iso,
                "submitted_order_ids": audit_submitted_order_ids,
                "intent_id": intent_model.intent_id,
                "readiness_evaluation_id": readiness.readiness_evaluation_id,
                "routing_target_recommendation_id": recommendation_id,
                "submitted_order_created_at": str(audit_first_submitted_at),
                "submitted_order_last_checked_at": submitted_at_iso,
                "explicit_submit_action": True,
                "auto_submit": False,
                "fanout_created": False,
                "allocation_created": False,
                "scoring_created": False,
                "route_executor_created": False,
                "target_reselection": False,
            }
        )
        audit_model.provenance_json = _jsonable(audit_provenance)
        session.add(audit_model)

    def _default_recovery_action(
        self,
        submitted: SubmittedOrder,
        recommendation: SubmittedOrderRecoveryRecommendation,
    ) -> str:
        if (
            submitted.reconciliation_status == SubmittedOrderReconciliationStatus.PENDING
            and submitted.status_reason_code == "amend_acknowledged"
        ):
            return "reconcile_now"
        if submitted.status in {
            SubmittedOrderStatus.CANCEL_REQUESTED,
            SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            SubmittedOrderStatus.UNKNOWN,
        }:
            return "reconcile_now"
        if submitted.reconciliation_status in {
            SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
            SubmittedOrderReconciliationStatus.PENDING,
            SubmittedOrderReconciliationStatus.FAILED,
            SubmittedOrderReconciliationStatus.UNAVAILABLE,
        } and submitted.status in {
            SubmittedOrderStatus.ACKNOWLEDGED,
            SubmittedOrderStatus.PARTIALLY_FILLED,
        }:
            return "reconcile_now"
        if recommendation.category == SubmittedOrderRecoveryCategory.RETRYABLE:
            return "retry_same_target"
        if recommendation.category == SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN:
            return "reconcile_now"
        raise SubmittedOrderActionError(
            submitted.submitted_order_id,
            recommendation.message or "No safe recovery action is currently available.",
        )

    async def _retry_submitted_order_same_target(
        self,
        submitted: SubmittedOrder,
        recommendation: SubmittedOrderRecoveryRecommendation,
    ) -> SubmittedOrder:
        if recommendation.category != SubmittedOrderRecoveryCategory.RETRYABLE:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because the submitted order is not classified as retryable.",
                reason_codes=["retry_not_recommended"],
                raw_payload={"category": recommendation.category.value},
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry is not recommended for this submitted order.",
            )
        if submitted.status != SubmittedOrderStatus.REJECTED:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because the submitted order is not in a rejected state.",
                reason_codes=["retry_requires_rejected_order"],
                raw_payload={"status": submitted.status.value},
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry requires a rejected submitted order.",
            )
        if submitted.exchange_order_id is not None or (submitted.filled_quantity or Decimal("0")) > Decimal("0"):
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because venue-side acknowledgement or fill evidence makes duplicate exposure unclear.",
                reason_codes=["retry_duplicate_exposure_uncertain"],
                raw_payload={
                    "exchange_order_id": submitted.exchange_order_id,
                    "filled_quantity": str(submitted.filled_quantity or Decimal("0")),
                },
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry is unsafe because duplicate exposure risk has not been ruled out.",
            )
        if submitted.intent_id is None:
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry requires the original binding/account-targeted child intent.",
            )
        intent = await self.get_child_intent(submitted.intent_id)
        with self._session_factory() as session:
            siblings = session.scalars(
                select(SubmittedOrderModel).where(
                    SubmittedOrderModel.environment == self.settings.app.environment,
                    SubmittedOrderModel.intent_id == intent.intent_id,
                    SubmittedOrderModel.submitted_order_id != submitted.submitted_order_id,
                )
            ).all()
        if siblings:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because other submitted-order attempts already exist for the same child intent.",
                reason_codes=["retry_existing_attempt_present"],
                raw_payload={
                    "sibling_submitted_order_ids": [row.submitted_order_id for row in siblings],
                },
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry is unsafe because another submitted-order attempt already exists for this child intent.",
            )
        adapter = await self.venue_registry_service.get_adapter(submitted.venue)
        open_order_source, matching_private_orders = await self._matching_private_open_orders_for_submitted_order(
            submitted,
            adapter=adapter,
        )
        if open_order_source == "venue_query" and matching_private_orders:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because live venue-private open-order state still shows the targeted order working.",
                reason_codes=["retry_live_order_still_open"],
                raw_payload={
                    "open_orders_source": open_order_source,
                    "matching_exchange_order_ids": [
                        item.exchange_order_id for item in matching_private_orders
                    ],
                    "matching_client_order_ids": [
                        item.client_order_id for item in matching_private_orders
                    ],
                },
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry is unsafe because live venue-private open-order state still shows the targeted order working.",
            )
        fill_evidence = await adapter.fetch_retry_private_fill_evidence(
            submitted,
            limit=100,
        )
        if fill_evidence.evidence_scope == "query_failed":
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message=(
                    "Retry was blocked because private fill evidence could not be queried "
                    "truthfully before retry."
                ),
                reason_codes=["retry_private_fill_evidence_unavailable"],
                raw_payload={
                    "fills_source": fill_evidence.source,
                    "fill_evidence_scope": fill_evidence.evidence_scope,
                    "fill_evidence_message": fill_evidence.message,
                },
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                "Retry is unsafe because private fill evidence could not be queried truthfully before retry.",
            )
        if fill_evidence.source == "venue_query" and fill_evidence.fills:
            targeted_order_proof = fill_evidence.evidence_scope == "order_scoped"
            reason_code = (
                "retry_live_fill_evidence_present"
                if targeted_order_proof
                else "retry_same_account_symbol_fill_ambiguous"
            )
            message = (
                "Retry was blocked because live venue-private fill evidence exists for the targeted order."
                if targeted_order_proof
                else (
                    "Retry was blocked because venue-private fill evidence exists for the same "
                    "account and symbol at or after this submitted order's submission time, but the "
                    "submitted order has no exchange order id to prove the fills belong to that exact order."
                )
            )
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message=message,
                reason_codes=[reason_code],
                raw_payload={
                    "fills_source": fill_evidence.source,
                    "fill_evidence_scope": fill_evidence.evidence_scope,
                    "fill_evidence_message": fill_evidence.message,
                    "matching_fill_ids": [item.fill_id for item in fill_evidence.fills],
                    "matching_exchange_order_ids": [
                        item.exchange_order_id for item in fill_evidence.fills
                    ],
                },
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                (
                    "Retry is unsafe because live venue-private fill evidence exists for the targeted order."
                    if targeted_order_proof
                    else (
                        "Retry is unsafe because same-account/same-symbol private fill evidence exists, "
                        "but targeted order fill proof is unavailable."
                    )
                ),
            )
        readiness = await self.assess_child_intent_readiness(intent.intent_id)
        if readiness.outcome != ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_blocked",
                observed_at=_utcnow(),
                message="Retry was blocked because the child intent is no longer submission-ready.",
                reason_codes=list(readiness.reason_codes or ["retry_readiness_blocked"]),
                raw_payload={"readiness_outcome": readiness.outcome.value},
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                readiness.message or "Retry blocked by current readiness state.",
            )
        retry_intent = self._intent_for_same_target_retry(intent, submitted, adapter)
        try:
            retried = await adapter.submit_order(retry_intent)
        except VenueAdapterError as exc:
            self._record_submitted_order_event(
                submitted,
                event_type="recovery_retry_rejected",
                observed_at=_utcnow(),
                message=str(exc),
                reason_codes=list(exc.reason_codes or ["recovery_retry_rejected"]),
                raw_payload=_jsonable(getattr(exc, "payload", None) or {}),
            )
            raise SubmittedOrderActionError(
                submitted.submitted_order_id,
                str(exc),
            ) from exc
        retried = self._submitted_order_with_routed_lineage(
            retried,
            intent=retry_intent,
            readiness=readiness,
        )
        persisted = self._persist_submitted_order(
            retry_intent,
            readiness,
            retried,
            allow_multiple_for_intent=True,
            recovery_parent_submitted_order_id=submitted.submitted_order_id,
        )
        self._record_submitted_order_event(
            submitted,
            event_type="recovery_retry_submitted",
            observed_at=_utcnow(),
            message="Submitted a same-target retry for the rejected order.",
            reason_codes=["recovery_retry_submitted"],
            raw_payload={
                "resulting_submitted_order_id": persisted.submitted_order_id,
                "retry_client_order_id": persisted.client_order_id,
            },
        )
        return persisted

    async def _matching_private_open_orders_for_submitted_order(
        self,
        submitted: SubmittedOrder,
        *,
        adapter: Any,
    ) -> tuple[str, list[Any]]:
        source, orders = await adapter.fetch_open_orders_with_source(
            venue_account_ref_id=submitted.venue_account_ref_id
        )
        matches = [
            item
            for item in orders
            if (
                item.linked_submitted_order_id == submitted.submitted_order_id
                or (
                    submitted.exchange_order_id is not None
                    and item.exchange_order_id == submitted.exchange_order_id
                )
                or (
                    submitted.client_order_id is not None
                    and item.client_order_id == submitted.client_order_id
                )
            )
        ]
        return (source, matches)

    def _intent_for_same_target_retry(
        self,
        intent: OrderIntent,
        submitted: SubmittedOrder,
        adapter: Any,
    ) -> OrderIntent:
        if not bool(getattr(adapter, "supports_client_order_ids", False)):
            return intent
        if not bool(getattr(adapter, "retry_requires_fresh_client_order_id", False)):
            return intent
        retry_client_order_id = self._fresh_retry_client_order_id(intent, submitted)
        provenance = dict(intent.provenance or {})
        overrides = dict(provenance.get("submission_overrides") or {})
        overrides["client_order_id"] = retry_client_order_id
        provenance["submission_overrides"] = overrides
        provenance["recovery_parent_submitted_order_id"] = submitted.submitted_order_id
        return replace(intent, provenance=provenance)

    @staticmethod
    def _fresh_retry_client_order_id(
        intent: OrderIntent,
        submitted: SubmittedOrder,
    ) -> str:
        seed = (
            f"{submitted.venue}:"
            f"{submitted.venue_account_ref_id}:"
            f"{intent.intent_id}:"
            f"{submitted.submitted_order_id}:"
            f"{_utcnow().isoformat()}"
        )
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        return f"mf-r-{digest}"

    async def _get_fills_for_submitted_order(self, submitted_order_id: str) -> list[Fill]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(FillModel).where(
                    FillModel.environment == self.settings.app.environment,
                    FillModel.submitted_order_id == submitted_order_id,
                ).order_by(FillModel.filled_at.asc())
            ).all()
        return [
            Fill(
                fill_id=row.fill_id,
                instrument_key=row.symbol,
                instrument_ref_id=row.instrument_ref_id,
                venue_account_ref_id=row.venue_account_ref_id,
                venue=row.venue,
                account_address=row.account_address,
                submitted_order_id=row.submitted_order_id,
                exchange_order_id=row.exchange_order_id,
                symbol=row.symbol,
                price=row.price,
                quantity=row.quantity,
                fee=row.fee,
                filled_at=row.filled_at,
            )
            for row in rows
        ]

    def _merge_lifecycle_update_with_fills(
        self,
        *,
        current: SubmittedOrder,
        update: SubmittedOrderLifecycleUpdate,
        fills: Sequence[Fill],
    ) -> SubmittedOrderLifecycleUpdate:
        if not fills:
            if update.reconciliation_status == SubmittedOrderReconciliationStatus.NOT_ATTEMPTED:
                update.reconciliation_status = SubmittedOrderReconciliationStatus.PENDING
            return update

        total_quantity = sum((fill.quantity for fill in fills), start=Decimal("0"))
        weighted_notional = sum((fill.price * fill.quantity for fill in fills), start=Decimal("0"))
        average_fill_price = (
            weighted_notional / total_quantity if total_quantity > Decimal("0") else None
        )
        last_fill_at = max(fill.filled_at for fill in fills)
        original_quantity = current.original_quantity or Decimal("0")
        remaining_quantity = max(original_quantity - total_quantity, Decimal("0"))
        update.filled_quantity = total_quantity
        update.average_fill_price = average_fill_price
        update.last_fill_at = last_fill_at
        update.remaining_quantity = remaining_quantity
        update.reconciliation_status = SubmittedOrderReconciliationStatus.RECONCILED

        if original_quantity > Decimal("0") and total_quantity >= original_quantity:
            update.status = SubmittedOrderStatus.FILLED
            update.event_type = "reconciliation_completed_fill"
            update.status_reason_code = "reconciliation_completed_fill"
            update.reason_codes = ["reconciliation_completed_fill"]
            update.status_message = "Submitted order reconciled to fully filled using persisted fill evidence."
            update.cancelable_in_principle = False
            update.amendable_in_principle = False
            return update

        protected_statuses = {
            SubmittedOrderStatus.CANCELED,
            SubmittedOrderStatus.EXPIRED,
            SubmittedOrderStatus.REJECTED,
            SubmittedOrderStatus.CANCEL_REQUESTED,
            SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
        }
        if update.status in protected_statuses:
            update.cancelable_in_principle = False
            update.amendable_in_principle = False
            return update

        update.status = SubmittedOrderStatus.PARTIALLY_FILLED
        update.event_type = "reconciliation_partial_fill"
        update.status_reason_code = "reconciliation_partial_fill"
        update.reason_codes = ["reconciliation_partial_fill"]
        update.status_message = "Submitted order reconciled to partially filled using persisted fill evidence."
        update.cancelable_in_principle = True
        update.amendable_in_principle = current.order_type == OrderType.LIMIT
        return update

    def _apply_submitted_order_update(
        self,
        *,
        current: SubmittedOrder,
        update: SubmittedOrderLifecycleUpdate,
    ) -> SubmittedOrder:
        with self._session_factory() as session:
            model = session.scalar(
                select(SubmittedOrderModel).where(
                    SubmittedOrderModel.environment == self.settings.app.environment,
                    SubmittedOrderModel.submitted_order_id == current.submitted_order_id,
                )
            )
            if model is None:
                raise ValueError(f"Submitted order not found: {current.submitted_order_id}")
            model.exchange_order_id = update.exchange_order_id or model.exchange_order_id
            model.status = update.status
            model.reconciliation_status = update.reconciliation_status
            if update.acknowledged_at is not None:
                model.acknowledged_at = update.acknowledged_at
            if update.limit_price is not None:
                model.limit_price = update.limit_price
            if update.original_quantity is not None:
                model.original_quantity = update.original_quantity
            model.remaining_quantity = (
                update.remaining_quantity if update.remaining_quantity is not None else model.remaining_quantity
            )
            model.filled_quantity = (
                update.filled_quantity if update.filled_quantity is not None else model.filled_quantity
            )
            model.average_fill_price = (
                update.average_fill_price
                if update.average_fill_price is not None
                else model.average_fill_price
            )
            model.last_fill_at = update.last_fill_at or model.last_fill_at
            model.last_reconciled_at = update.observed_at or _utcnow()
            model.status_reason_code = update.status_reason_code
            model.status_message = update.status_message
            model.reason_codes = list(update.reason_codes)
            if update.cancelable_in_principle is not None:
                model.cancelable_in_principle = update.cancelable_in_principle
            if update.amendable_in_principle is not None:
                model.amendable_in_principle = update.amendable_in_principle
            if update.raw_payload:
                model.raw_payload = self._merge_lifecycle_update_raw_payload(
                    current=current,
                    update_payload=update.raw_payload,
                )
            session.add(model)
            self._add_submitted_order_event_model(
                session,
                submitted=self._submitted_order_from_model(model),
                event_type=update.event_type,
                observed_at=update.observed_at or _utcnow(),
                message=update.status_message,
                reason_codes=list(update.reason_codes),
                raw_payload=update.raw_payload,
            )
            session.commit()
            return self._submitted_order_from_model(model)

    def _record_submitted_order_event(
        self,
        submitted: SubmittedOrder,
        *,
        event_type: str,
        observed_at: datetime,
        message: str | None,
        reason_codes: list[str],
        raw_payload: dict[str, object] | None = None,
    ) -> None:
        with self._session_factory() as session:
            self._add_submitted_order_event_model(
                session,
                submitted=submitted,
                event_type=event_type,
                observed_at=observed_at,
                message=message,
                reason_codes=list(reason_codes),
                raw_payload=raw_payload,
            )
            session.commit()

    @staticmethod
    def _merge_lifecycle_update_raw_payload(
        *,
        current: SubmittedOrder,
        update_payload: dict[str, object],
    ) -> dict[str, object]:
        merged_payload = _jsonable(update_payload)
        current_payload = _jsonable(dict(current.raw_payload or {}))
        merged_payload.pop("routed_submission", None)
        if "routed_submission" in current_payload:
            merged_payload["routed_submission"] = current_payload["routed_submission"]
        return merged_payload

    def _add_submitted_order_event_model(
        self,
        session: Any,
        *,
        submitted: SubmittedOrder,
        event_type: str,
        observed_at: datetime,
        message: str | None,
        reason_codes: list[str],
        raw_payload: dict[str, object] | None,
    ) -> None:
        fingerprint = _json_fingerprint(
            {
                "submitted_order_id": submitted.submitted_order_id,
                "event_type": event_type,
                "status": submitted.status.value,
                "reconciliation_status": submitted.reconciliation_status.value,
                "observed_at": observed_at.isoformat(),
                "reason_codes": list(reason_codes),
            }
        )
        event_id = f"soe-{fingerprint[:24]}"
        existing = session.scalar(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.environment == self.settings.app.environment,
                SubmittedOrderLifecycleEventModel.event_id == event_id,
            )
        )
        if existing is not None:
            return
        session.add(
            SubmittedOrderLifecycleEventModel(
                environment=self.settings.app.environment,
                event_id=event_id,
                submitted_order_id=submitted.submitted_order_id,
                intent_id=submitted.intent_id,
                venue_account_ref_id=submitted.venue_account_ref_id,
                venue=submitted.venue,
                status=submitted.status,
                reconciliation_status=submitted.reconciliation_status,
                event_type=event_type,
                reason_codes=list(reason_codes),
                message=message,
                raw_payload=_jsonable(raw_payload or {}),
                observed_at=observed_at,
            )
        )

    @staticmethod
    def _submission_event_type(status: SubmittedOrderStatus) -> str:
        if status == SubmittedOrderStatus.REJECTED:
            return "submission_rejected"
        if status == SubmittedOrderStatus.ACKNOWLEDGED:
            return "submission_acknowledged"
        return "submission_submitted"

    @staticmethod
    def _readiness_message(
        outcome: ExecutionReadinessOutcome,
        reason_codes: list[str],
    ) -> str:
        if outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION:
            return "Prepared child intent satisfies all modeled readiness checks for submission."
        if outcome == ExecutionReadinessOutcome.PHASE_BLOCKED:
            return (
                "Prepared child intent is eligible in principle, but live submission remains "
                "intentionally deferred in the current phase."
            )
        if not reason_codes:
            return "Prepared child intent is not submission-ready."
        return f"Prepared child intent is not submission-ready: {reason_codes[0]}."

    @staticmethod
    def _routed_lifecycle_context_for_submitted_order(
        submitted: SubmittedOrder,
    ) -> SubmittedOrderRoutedLifecycleContext | None:
        return submitted_order_routed_lifecycle_context_from_raw_payload(submitted.raw_payload)

    @staticmethod
    def _recovery_recommendation_for_submitted_order(
        submitted: SubmittedOrder,
    ) -> SubmittedOrderRecoveryRecommendation:
        reason_codes = list(submitted.reason_codes or [])
        routed_context = DefaultExecutionService._routed_lifecycle_context_for_submitted_order(
            submitted
        )
        category = SubmittedOrderRecoveryCategory.NO_ACTION_REQUIRED
        message = submitted.status_message
        recommended_action = "No rejection recovery action is currently required."

        retryable_codes = {
            "reconciliation_failed",
            "venue_state_unavailable",
            "temporarily_unavailable",
            "rate_limited",
        }
        non_retryable_codes = {
            "venue_rejected",
            "unsupported_order_type",
            "below_min_order_size",
            "invalid_quantity_step",
            "missing_symbol_mapping",
            "cancel_rejected",
            "cancel_not_supported",
        }
        policy_codes = {
            "account_not_authorized",
            "binding_disabled",
            "binding_not_routing_eligible",
            "binding_trading_disabled",
            "venue_account_inactive",
            "venue_account_trading_disabled",
        }
        uncertain_codes = {
            "reconciliation_missing_order",
            "reconciliation_unknown_status",
            "reconciliation_unavailable",
            "reconciliation_cancel_pending",
            "amend_acknowledged",
        }

        if submitted.status in {
            SubmittedOrderStatus.CANCEL_REQUESTED,
            SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
        }:
            category = SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN
            recommended_action = "Reconcile the order again to confirm final cancel state."
        elif submitted.status_reason_code == "amend_acknowledged":
            category = SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN
            recommended_action = "Reconcile the order again to confirm the amended working state."
        elif submitted.reconciliation_status in {
            SubmittedOrderReconciliationStatus.FAILED,
            SubmittedOrderReconciliationStatus.UNAVAILABLE,
        } or any(code in uncertain_codes for code in reason_codes) or submitted.status == SubmittedOrderStatus.UNKNOWN:
            category = SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN
            recommended_action = "Inspect venue/account state before any retry or operator intervention."
        elif any(code in policy_codes for code in reason_codes):
            category = SubmittedOrderRecoveryCategory.ACCOUNT_POLICY_BLOCK
            recommended_action = "Resolve account or policy authorization before retrying."
        elif submitted.status == SubmittedOrderStatus.REJECTED:
            if any(code in retryable_codes for code in reason_codes):
                category = SubmittedOrderRecoveryCategory.RETRYABLE
                recommended_action = "Retry only after the transient venue-side failure condition clears."
            elif any(code in non_retryable_codes for code in reason_codes):
                category = SubmittedOrderRecoveryCategory.NON_RETRYABLE
                recommended_action = "Do not auto-retry; the rejected order parameters or venue state need review."
            else:
                category = SubmittedOrderRecoveryCategory.OPERATOR_ACTION_REQUIRED
                recommended_action = "Operator review is required before any retry or manual recovery."

        if routed_context is not None:
            reason_codes = sorted(set([*reason_codes, *routed_context.boundary_reason_codes]))

        return SubmittedOrderRecoveryRecommendation(
            submitted_order_id=submitted.submitted_order_id,
            intent_id=submitted.intent_id,
            venue_account_ref_id=submitted.venue_account_ref_id,
            venue=submitted.venue,
            category=category,
            retryable=category == SubmittedOrderRecoveryCategory.RETRYABLE,
            operator_action_required=category == SubmittedOrderRecoveryCategory.OPERATOR_ACTION_REQUIRED,
            venue_state_uncertain=category == SubmittedOrderRecoveryCategory.VENUE_STATE_UNCERTAIN,
            account_policy_block=category == SubmittedOrderRecoveryCategory.ACCOUNT_POLICY_BLOCK,
            reason_codes=reason_codes,
            message=message,
            recommended_action=recommended_action,
            routed_origin=routed_context is not None,
            routed_lifecycle_context=routed_context,
        )

    @staticmethod
    def _resolve_venue_for_intent(session: Any, model: OrderIntentModel) -> str:
        if model.venue_account_ref_id is None:
            raise ValueError("Child intent is missing venue-account context.")
        venue_account = session.get(VenueAccountModel, model.venue_account_ref_id)
        if venue_account is None:
            raise ValueError(f"Venue account not found for child intent: {model.venue_account_ref_id}")
        return venue_account.venue

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

    @staticmethod
    def _submitted_order_from_model(model: SubmittedOrderModel) -> SubmittedOrder:
        return SubmittedOrder(
            submitted_order_id=model.submitted_order_id,
            instrument_key=model.symbol,
            instrument_ref_id=model.instrument_ref_id,
            venue_account_ref_id=model.venue_account_ref_id,
            venue=model.venue,
            account_address=model.account_address,
            intent_id=model.intent_id,
            client_order_id=model.client_order_id,
            exchange_order_id=model.exchange_order_id,
            status=model.status,
            reconciliation_status=model.reconciliation_status,
            submitted_at=model.submitted_at,
            acknowledged_at=model.acknowledged_at,
            symbol=model.symbol,
            side=model.side,
            order_type=model.order_type,
            limit_price=model.limit_price,
            original_quantity=model.original_quantity,
            remaining_quantity=model.remaining_quantity,
            filled_quantity=model.filled_quantity,
            average_fill_price=model.average_fill_price,
            last_fill_at=model.last_fill_at,
            last_reconciled_at=model.last_reconciled_at,
            status_reason_code=model.status_reason_code,
            status_message=model.status_message,
            reason_codes=list(model.reason_codes or []),
            cancelable_in_principle=model.cancelable_in_principle,
            amendable_in_principle=model.amendable_in_principle,
            reduce_only=model.reduce_only,
            raw_payload=dict(model.raw_payload or {}),
        )

    @staticmethod
    def _submitted_order_event_from_model(
        model: SubmittedOrderLifecycleEventModel,
        *,
        routed_lifecycle_context: SubmittedOrderRoutedLifecycleContext | None = None,
    ) -> SubmittedOrderLifecycleEvent:
        return SubmittedOrderLifecycleEvent(
            event_id=model.event_id,
            submitted_order_id=model.submitted_order_id,
            intent_id=model.intent_id,
            venue_account_ref_id=model.venue_account_ref_id,
            venue=model.venue,
            status=model.status,
            reconciliation_status=model.reconciliation_status,
            event_type=model.event_type,
            reason_codes=list(model.reason_codes or []),
            message=model.message,
            raw_payload=dict(model.raw_payload or {}),
            observed_at=model.observed_at,
            routed_origin=routed_lifecycle_context is not None,
            routed_lifecycle_context=routed_lifecycle_context,
        )

    @staticmethod
    def _execution_readiness_from_model(
        model: ExecutionReadinessEvaluationModel,
    ) -> ExecutionReadinessAssessment:
        return ExecutionReadinessAssessment(
            readiness_evaluation_id=model.readiness_evaluation_id,
            readiness_evaluation_key=model.readiness_evaluation_key,
            environment=model.environment,
            intent_ref_id=model.intent_ref_id,
            intent_id=model.intent_id,
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
            venue=model.venue,
            support_level=VenueSupportLevel(model.support_level),
            preview_status=(
                VenueOrderPreviewStatus(model.preview_status)
                if model.preview_status is not None
                else None
            ),
            outcome=model.outcome,
            eligible_for_submission_in_principle=model.eligible_for_submission_in_principle,
            live_submission_phase_enabled=model.live_submission_phase_enabled,
            venue_supports_order_submission=model.venue_supports_order_submission,
            adapter_supports_order_submission=model.adapter_supports_order_submission,
            adapter_supports_order_cancel=model.adapter_supports_cancel_amend,
            adapter_supports_order_amend=bool(
                (model.provenance or {})
                .get("venue_capabilities", {})
                .get("adapter_supports_order_amend", False)
            ),
            submission_authorized=model.submission_authorized,
            account_connected=model.account_connected,
            private_state_required=model.private_state_required,
            private_state_ready=model.private_state_ready,
            reason_codes=list(model.reason_codes or []),
            message=model.message,
            prepared_order=None,
            evaluated_at=model.evaluated_at,
            provenance=dict(model.provenance or {}),
        )
