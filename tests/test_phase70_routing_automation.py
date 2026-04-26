from __future__ import annotations

import asyncio
from dataclasses import asdict

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    RoutingAutomationMode,
    RoutingAutomationPlanOutcome,
    RoutingAutomationStepStatus,
    RoutingTargetRecommendationStatus,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingAssessmentModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase600_routing_target_recommendation import _multi_ready_audit, _ready_audit
from tests.test_phase63_recommendation_target_choice_conversion import _accepted_choice


def _counts(session_factory) -> dict[str, int]:
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
        }


def _step(payload: dict[str, object], name: str) -> dict[str, object]:
    for item in payload["steps"]:
        if item["name"] == name:
            return item
    raise AssertionError(f"Missing automation step {name}")


def test_default_automation_policy_is_disabled_and_dry_run_plan_mutates_nothing() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    before_counts = _counts(session_factory)

    policy = asyncio.run(routing.inspect_routing_automation_policy())
    plan = asyncio.run(routing.plan_routing_automation_for_desired_trade(desired_trade_key))

    assert policy.mode == RoutingAutomationMode.DISABLED
    assert policy.recommendation_acceptance == RoutingAutomationStepStatus.DISABLED
    assert "routing_automation_disabled" in policy.reason_codes
    assert plan.outcome == RoutingAutomationPlanOutcome.DISABLED
    assert plan.dry_run is True
    assert plan.persisted is False
    assert plan.artifacts_created_by_plan is False
    assert _step(asdict(plan), "recommendation_acceptance")[
        "status"
    ] == RoutingAutomationStepStatus.DISABLED
    assert plan.boundary_flags["smart_routing"] is False
    assert plan.boundary_flags["fanout"] is False
    assert plan.boundary_flags["ranking"] is False
    assert plan.boundary_flags["scoring"] is False
    assert plan.boundary_flags["target_reselection"] is False
    assert plan.boundary_flags["route_executor"] is False
    assert plan.boundary_flags["auto_submit"] is False
    assert _counts(session_factory) == before_counts


def test_dry_run_only_policy_marks_feasible_acceptance_without_state_mutation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before_counts = _counts(session_factory)

    policy = routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY)
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=policy,
            dry_run=True,
        )
    )

    acceptance = _step(asdict(plan), "recommendation_acceptance")
    assert plan.outcome == RoutingAutomationPlanOutcome.DRY_RUN_ONLY
    assert acceptance["status"] == RoutingAutomationStepStatus.DRY_RUN_ONLY
    assert acceptance["dry_run_only"] is True
    assert acceptance["would_create_artifact_type"] == "RoutingTargetChoice"
    assert acceptance["lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert "dry_run_no_state_mutation" in acceptance["reason_codes"]
    assert _counts(session_factory) == before_counts


def test_approval_required_policy_preserves_operator_boundary() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before_counts = _counts(session_factory)

    policy = routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED)
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=policy,
        )
    )

    assert plan.outcome == RoutingAutomationPlanOutcome.APPROVAL_REQUIRED
    acceptance = _step(asdict(plan), "recommendation_acceptance")
    assert acceptance["status"] == RoutingAutomationStepStatus.APPROVAL_REQUIRED
    assert acceptance["approval_required"] is True
    assert "operator_approval_required" in acceptance["reason_codes"]
    assert _counts(session_factory) == before_counts


def test_explicit_policy_can_mark_same_target_conversion_eligible_without_converting() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation, choice, desired_trade_key = _accepted_choice(session_factory)
    before_counts = _counts(session_factory)

    policy = routing.routing_automation_policy(
        mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
        allow_target_choice_conversion=True,
        allow_preview_readiness=True,
        allow_submit=True,
    )
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=policy,
            dry_run=True,
        )
    )

    conversion = _step(asdict(plan), "target_choice_conversion")
    submission = _step(asdict(plan), "submitted_order_handoff")
    assert plan.outcome == RoutingAutomationPlanOutcome.AUTOMATION_ELIGIBLE
    assert conversion["status"] == RoutingAutomationStepStatus.AUTOMATION_ELIGIBLE
    assert conversion["automatable"] is True
    assert conversion["lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert conversion["lineage"]["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert conversion["lineage"]["routing_target_choice_id"] == choice.target_choice_id
    assert conversion["lineage"]["selected_venue"] == choice.selected_venue
    assert submission["status"] == RoutingAutomationStepStatus.MANUAL_ONLY
    assert "auto_submit_not_enabled_by_phase_7_0" in submission["reason_codes"]
    assert plan.boundary_flags["same_target_only"] is True
    assert plan.boundary_flags["cbbo"] is False
    assert plan.boundary_flags["fanout"] is False
    assert plan.boundary_flags["ranking"] is False
    assert plan.boundary_flags["scoring"] is False
    assert plan.boundary_flags["target_reselection"] is False
    assert _counts(session_factory) == before_counts


def test_blocked_recommendation_cannot_be_laundered_into_automation_plan() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES
    before_counts = _counts(session_factory)

    policy = routing.routing_automation_policy(
        mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
        allow_recommendation_acceptance=True,
        allow_target_choice_conversion=True,
        allow_preview_readiness=True,
    )
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            recommendation.desired_trade_key or "",
            policy=policy,
        )
    )

    acceptance = _step(asdict(plan), "recommendation_acceptance")
    assert plan.outcome == RoutingAutomationPlanOutcome.BLOCKED
    assert acceptance["status"] == RoutingAutomationStepStatus.BLOCKED
    assert acceptance["blocked"] is True
    assert "routing_target_recommendation_not_recommended" in acceptance["reason_codes"]
    assert plan.artifacts_created_by_plan is False
    assert _counts(session_factory) == before_counts


def test_routing_automation_api_exposes_policy_and_dry_run_plan_without_mutation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before_counts = _counts(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            policy_response = client.get("/api/v1/routing-automation/policy")
            plan_response = client.post(
                f"/api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}",
                json={
                    "dry_run": True,
                    "policy": {
                        "mode": "dry_run_only",
                        "allow_recommendation_acceptance": True,
                    },
                },
            )
    finally:
        app.dependency_overrides.pop(get_routing_assessment_service, None)

    assert policy_response.status_code == 200
    assert policy_response.json()["mode"] == "disabled"
    assert policy_response.json()["boundary_flags"]["route_executor"] is False
    assert plan_response.status_code == 200
    payload = plan_response.json()
    assert payload["dry_run"] is True
    assert payload["persisted"] is False
    assert payload["artifacts_created_by_plan"] is False
    assert payload["outcome"] == "dry_run_only"
    acceptance = _step(payload, "recommendation_acceptance")
    assert acceptance["status"] == "dry_run_only"
    assert acceptance["lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert payload["boundary_flags"]["best_binding_selection"] is False
    assert payload["boundary_flags"]["fanout"] is False
    assert payload["boundary_flags"]["auto_submit"] is False
    assert _counts(session_factory) == before_counts
