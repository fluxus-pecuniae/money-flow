from __future__ import annotations

from sqlalchemy import func, select

from core.domain.enums import ExecutionReadinessOutcome, VenueOrderPreviewStatus
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from scripts.manual_routed_flow import (
    SUBMISSION_CONFIRMATION_REASON,
    SUBMISSION_SKIPPED_REASON,
    run_manual_routed_flow,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase53_routed_child_intent_readiness import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _make_all_route_readiness_candidates_ready,
    _ready_audit,
)


class _ReadyAfterAssessmentRoutingService:
    def __init__(self, inner, session_factory) -> None:
        self._inner = inner
        self._session_factory = session_factory

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def create_assessment_from_desired_trade(self, desired_trade_key: str):
        assessment = await self._inner.create_assessment_from_desired_trade(desired_trade_key)
        _make_all_route_readiness_candidates_ready(self._session_factory)
        return assessment


def _counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
            "recommendations": session.scalar(
                select(func.count()).select_from(RoutingTargetRecommendationModel)
            ),
            "target_choices": session.scalar(
                select(func.count()).select_from(RoutingTargetChoiceModel)
            ),
            "child_intents": session.scalar(select(func.count()).select_from(OrderIntentModel)),
            "readiness": session.scalar(
                select(func.count()).select_from(ExecutionReadinessEvaluationModel)
            ),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
        }


def test_manual_routed_flow_runs_from_desired_trade_through_readiness() -> None:
    session_factory = build_test_session_factory()
    routing, _seed_audit, desired_trade_key = _ready_audit(session_factory)
    execution, adapter = _build_execution(session_factory)

    trace = run_manual_routed_flow(
        desired_trade_key=desired_trade_key,
        run_through_readiness=True,
        routing_service=_ReadyAfterAssessmentRoutingService(routing, session_factory),
        execution_service=execution,
        session_factory=session_factory,
    )

    assert trace["ok"] is True
    assert trace["phase"] == "phase_6_5_manual_routed_flow"
    assert trace["boundaries"]["smart_routing"] is False
    assert trace["boundaries"]["route_executor"] is False
    assert trace["boundaries"]["auto_submit"] is False
    assert [step["name"] for step in trace["steps"]] == [
        "desired_trade",
        "routing_assessment",
        "route_readiness_audit",
        "routing_target_recommendation",
        "routing_target_choice",
        "child_intent_conversion",
        "prepared_order_preview",
        "execution_readiness",
    ]

    artifacts = trace["artifacts"]
    assert artifacts["desired_trade_key"] == desired_trade_key
    assert artifacts["routing_assessment_id"]
    assert artifacts["route_readiness_audit_id"]
    assert artifacts["overall_status"] == "ready_for_recommendation"
    assert artifacts["candidate_count"] == 1
    assert artifacts["ready_candidate_count"] == 1
    assert artifacts["routing_target_recommendation_id"]
    assert artifacts["status"] == "child_intent_created"
    assert artifacts["policy_name"] == "single_ready_candidate_only"
    assert artifacts["target_choice_id"]
    assert artifacts["intent_id"]
    assert artifacts["prepared_order_preview_status"] == VenueOrderPreviewStatus.PREPARABLE.value
    assert artifacts["readiness_evaluation_id"]
    assert artifacts["readiness_outcome"] == ExecutionReadinessOutcome.PHASE_BLOCKED.value
    assert "routed_submission_deferred" in artifacts["readiness_reason_codes"]

    lineage = artifacts["routed_lineage"]
    assert lineage["recommendation_backed_child_intent"] is True
    assert lineage["routing_target_recommendation_id"] == artifacts[
        "routing_target_recommendation_id"
    ]
    assert lineage["route_readiness_audit_id"] == artifacts["route_readiness_audit_id"]
    assert lineage["routing_assessment_id"] == artifacts["routing_assessment_id"]
    assert lineage["routing_target_choice_id"] == artifacts["target_choice_id"]
    assert lineage["selected_binding_ref_id"] == artifacts["selected_binding_ref_id"]
    assert lineage["selected_venue_account_ref_id"] == artifacts[
        "selected_venue_account_ref_id"
    ]
    assert lineage["selected_venue"] == artifacts["selected_venue"]
    assert lineage["selected_exchange_symbol"] == artifacts["selected_exchange_symbol"]
    assert lineage["auto_submit"] is False
    assert lineage["fanout_created"] is False
    assert lineage["allocation_created"] is False
    assert lineage["scoring_created"] is False
    assert lineage["target_reselection"] is False

    assert trace["submission"]["requested"] is False
    assert trace["submission"]["attempted"] is False
    assert trace["submission"]["skipped"] is True
    assert trace["submission"]["reason_codes"] == [SUBMISSION_SKIPPED_REASON]
    assert adapter.submit_calls == 0
    counts = _counts(session_factory)
    assert counts["target_choices"] == 1
    assert counts["child_intents"] == 1
    assert counts["readiness"] == 1
    assert counts["submitted_orders"] == 0


def test_manual_routed_flow_default_inspects_only_and_does_not_submit() -> None:
    session_factory = build_test_session_factory()
    routing, _seed_audit, desired_trade_key = _ready_audit(session_factory)
    execution, adapter = _build_execution(session_factory)

    trace = run_manual_routed_flow(
        desired_trade_key=desired_trade_key,
        routing_service=_ReadyAfterAssessmentRoutingService(routing, session_factory),
        execution_service=execution,
        session_factory=session_factory,
    )

    assert trace["ok"] is True
    assert [step["name"] for step in trace["steps"]] == ["desired_trade"]
    assert trace["artifacts"]["desired_trade_key"] == desired_trade_key
    assert "routing_assessment_id" not in trace["artifacts"]
    assert trace["submission"]["requested"] is False
    assert trace["submission"]["attempted"] is False
    assert trace["submission"]["skipped"] is True
    assert trace["submission"]["reason_codes"] == [SUBMISSION_SKIPPED_REASON]
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    counts = _counts(session_factory)
    assert counts["recommendations"] == 0
    assert counts["target_choices"] == 0
    assert counts["child_intents"] == 0
    assert counts["readiness"] == 0
    assert counts["submitted_orders"] == 0


def test_manual_routed_flow_submit_without_danger_confirmation_blocks_locally() -> None:
    session_factory = build_test_session_factory()
    routing, _seed_audit, desired_trade_key = _ready_audit(session_factory)
    execution, adapter = _build_execution(session_factory)

    trace = run_manual_routed_flow(
        desired_trade_key=desired_trade_key,
        run_through_readiness=True,
        submit=True,
        danger_confirmed=False,
        routing_service=_ReadyAfterAssessmentRoutingService(routing, session_factory),
        execution_service=execution,
        session_factory=session_factory,
    )

    assert trace["ok"] is False
    assert trace["submission"]["requested"] is True
    assert trace["submission"]["danger_confirmed"] is False
    assert trace["submission"]["attempted"] is False
    assert trace["submission"]["blocked"] is True
    assert trace["submission"]["skipped"] is True
    assert trace["submission"]["reason_codes"] == [SUBMISSION_CONFIRMATION_REASON]
    assert trace["steps"][-1]["name"] == "submission"
    assert trace["steps"][-1]["status"] == "blocked_before_service_submission"
    assert trace["steps"][-1]["reason_codes"] == [SUBMISSION_CONFIRMATION_REASON]
    assert adapter.submit_calls == 0
    counts = _counts(session_factory)
    assert counts["child_intents"] == 1
    assert counts["readiness"] == 1
    assert counts["submitted_orders"] == 0
