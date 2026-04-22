from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingAssessmentModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderLifecycleEventModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase53_routed_child_intent_readiness import _build_execution
from tests.test_phase600_routing_target_recommendation import _ready_audit
from tests.test_phase64_recommendation_backed_readiness import (
    _recommendation_backed_child_intent,
)
from tests.test_phase67_recommendation_backed_submission import (
    _submit_recommendation_backed_child_intent,
)


def _repo_counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
            "routing_assessments": session.scalar(
                select(func.count()).select_from(RoutingAssessmentModel)
            ),
            "route_readiness_audits": session.scalar(
                select(func.count()).select_from(RouteReadinessAuditModel)
            ),
            "routing_target_recommendations": session.scalar(
                select(func.count()).select_from(RoutingTargetRecommendationModel)
            ),
            "routing_target_choices": session.scalar(
                select(func.count()).select_from(RoutingTargetChoiceModel)
            ),
            "child_intents": session.scalar(select(func.count()).select_from(OrderIntentModel)),
            "readiness_evaluations": session.scalar(
                select(func.count()).select_from(ExecutionReadinessEvaluationModel)
            ),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
            "lifecycle_events": session.scalar(
                select(func.count()).select_from(SubmittedOrderLifecycleEventModel)
            ),
        }


def _workflow_response(routing, desired_trade_key: str) -> dict[str, object]:
    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/routed-workflows/by-desired-trade/{desired_trade_key}"
            )
    finally:
        app.dependency_overrides.pop(get_routing_assessment_service, None)
    assert response.status_code == 200
    return response.json()


def test_routed_workflow_inspection_returns_full_submitted_recommendation_chain_without_mutation() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        recommendation,
        choice,
        desired_trade_key,
        conversion,
        _execution,
        _adapter,
        submitted,
    ) = _submit_recommendation_backed_child_intent(session_factory)
    before_counts = _repo_counts(session_factory)

    payload = _workflow_response(routing, desired_trade_key)

    assert payload["found"] is True
    assert payload["artifacts_created_by_inspection"] is False
    assert payload["current_status_summary"]["state"] == "submitted_order_created"
    assert payload["artifact_counts"] == {
        "routing_assessments": 1,
        "route_readiness_audits": 1,
        "routing_target_recommendations": 1,
        "routing_target_choices": 1,
        "child_intents": 1,
        "readiness_evaluations": 1,
        "submitted_orders": 1,
        "lifecycle_events": 1,
    }
    assert payload["desired_trade"]["desired_trade_key"] == desired_trade_key
    assert payload["routing_assessments"][0]["assessment_id"] == audit.routing_assessment_id
    assert payload["route_readiness_audits"][0]["route_readiness_audit_id"] == (
        audit.route_readiness_audit_id
    )
    assert payload["routing_target_recommendations"][0][
        "routing_target_recommendation_id"
    ] == recommendation.routing_target_recommendation_id
    assert payload["routing_target_choices"][0]["target_choice_id"] == choice.target_choice_id
    assert payload["child_intents"][0]["intent_id"] == conversion.intent_id
    assert payload["submitted_orders"][0]["submitted_order_id"] == submitted.submitted_order_id
    assert payload["lifecycle_events"][0]["submitted_order_id"] == submitted.submitted_order_id
    lineage = payload["routed_lineage"]
    assert lineage["routing_assessment_id"] == audit.routing_assessment_id
    assert lineage["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert lineage["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert lineage["routing_target_choice_id"] == choice.target_choice_id
    assert lineage["intent_id"] == conversion.intent_id
    assert lineage["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert lineage["selected_venue"] == choice.selected_venue
    assert lineage["selected_exchange_symbol"] == conversion.selected_exchange_symbol
    assert payload["actionability_summary"]["same_target_only"] is True
    assert payload["recovery_summary"]["same_account_only"] is True
    assert payload["actionability_summary"]["route_executor_created"] is False
    assert _repo_counts(session_factory) == before_counts


def test_routed_workflow_inspection_returns_partial_recommendation_chain_without_creating_artifacts() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before_counts = _repo_counts(session_factory)

    payload = _workflow_response(routing, desired_trade_key)

    assert payload["found"] is True
    assert payload["current_status_summary"]["state"] == "recommendation_created"
    assert payload["artifact_counts"]["routing_assessments"] == 1
    assert payload["artifact_counts"]["route_readiness_audits"] == 1
    assert payload["artifact_counts"]["routing_target_recommendations"] == 1
    assert payload["artifact_counts"]["routing_target_choices"] == 0
    assert payload["artifact_counts"]["child_intents"] == 0
    assert payload["artifact_counts"]["readiness_evaluations"] == 0
    assert payload["artifact_counts"]["submitted_orders"] == 0
    assert payload["routing_target_recommendations"][0][
        "routing_target_recommendation_id"
    ] == recommendation.routing_target_recommendation_id
    assert payload["routed_lineage"] is None
    assert payload["actionability_summary"] is None
    assert payload["recovery_summary"] is None
    assert payload["artifacts_created_by_inspection"] is False
    assert _repo_counts(session_factory) == before_counts


def test_routed_workflow_inspection_returns_partial_readiness_chain_without_submission() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation, choice, desired_trade_key, conversion = (
        _recommendation_backed_child_intent(session_factory)
    )
    execution, adapter = _build_execution(session_factory)
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))
    before_counts = _repo_counts(session_factory)

    payload = _workflow_response(routing, desired_trade_key)

    assert payload["found"] is True
    assert payload["current_status_summary"]["state"] == "readiness_inspected"
    assert payload["artifact_counts"]["routing_target_choices"] == 1
    assert payload["artifact_counts"]["child_intents"] == 1
    assert payload["artifact_counts"]["readiness_evaluations"] == 1
    assert payload["artifact_counts"]["submitted_orders"] == 0
    assert payload["route_readiness_audits"][0]["route_readiness_audit_id"] == (
        audit.route_readiness_audit_id
    )
    assert payload["routing_target_recommendations"][0][
        "routing_target_recommendation_id"
    ] == recommendation.routing_target_recommendation_id
    assert payload["routing_target_choices"][0]["target_choice_id"] == choice.target_choice_id
    assert payload["child_intents"][0]["intent_id"] == conversion.intent_id
    assert payload["readiness_evaluations"][0]["readiness_evaluation_id"] == (
        readiness.readiness_evaluation_id
    )
    assert payload["routed_lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert "routed_submission_deferred" in payload["blocking_reason_codes"]
    assert adapter.submit_calls == 0
    assert _repo_counts(session_factory) == before_counts


def test_routed_workflow_inspection_unknown_desired_trade_is_clean_and_read_only() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _desired_trade_key = _ready_audit(session_factory)
    before_counts = _repo_counts(session_factory)

    payload = _workflow_response(routing, "missing-desired-trade-key")

    assert payload["found"] is False
    assert payload["current_status_summary"]["state"] == "desired_trade_not_found"
    assert payload["blocking_reason_codes"] == ["desired_trade_not_found"]
    assert payload["desired_trade"] is None
    assert payload["routing_assessments"] == []
    assert payload["route_readiness_audits"] == []
    assert payload["routing_target_recommendations"] == []
    assert payload["routing_target_choices"] == []
    assert payload["child_intents"] == []
    assert payload["readiness_evaluations"] == []
    assert payload["submitted_orders"] == []
    assert payload["lifecycle_events"] == []
    assert payload["artifacts_created_by_inspection"] is False
    assert _repo_counts(session_factory) == before_counts
