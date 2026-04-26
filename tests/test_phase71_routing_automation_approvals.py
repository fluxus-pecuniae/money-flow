from __future__ import annotations

import asyncio
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingAutomationPlanOutcome,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingAssessmentModel,
    RoutingAutomationApprovalModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from services.routing.service import RoutingAssessmentError
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
            "automation_approvals": session.scalar(
                select(func.count()).select_from(RoutingAutomationApprovalModel)
            ),
        }


def test_approval_creation_preserves_lineage_and_does_not_execute() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before = _counts(session_factory)

    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-a",
        )
    )
    after = _counts(session_factory)

    assert approval.status == RoutingAutomationApprovalStatus.ACTIVE
    assert approval.approved_by == "operator-a"
    assert approval.action_name == RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE
    assert approval.routing_target_recommendation_id == recommendation.routing_target_recommendation_id
    assert approval.route_readiness_audit_id == audit.route_readiness_audit_id
    assert approval.lineage["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert approval.boundary_flags["same_target_only"] is True
    assert approval.boundary_flags["fanout"] is False
    assert approval.boundary_flags["cbbo"] is False
    assert approval.boundary_flags["ranking"] is False
    assert approval.boundary_flags["scoring"] is False
    assert approval.boundary_flags["target_reselection"] is False
    assert approval.boundary_flags["route_executor"] is False
    assert approval.boundary_flags["auto_submit"] is False
    assert approval.provenance["action_executed"] is False
    assert after["automation_approvals"] == before["automation_approvals"] + 1
    assert after | {"automation_approvals": before["automation_approvals"]} == before

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    gate = asdict(inspection)["step_gate_states"]["recommendation_acceptance"]
    assert gate["status"] == "approved"
    assert gate["approval_id"] == approval.approval_id
    assert inspection.artifacts_created_by_inspection is False
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED),
        )
    )
    assert plan.approval_gate_states["recommendation_acceptance"]["status"] == "approved"
    assert plan.approval_gate_states["recommendation_acceptance"]["approval_id"] == approval.approval_id


def test_approval_revocation_blocks_gate_and_does_not_consume_or_execute() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-a",
        )
    )
    before = _counts(session_factory)

    revoked = asyncio.run(
        routing.revoke_routing_automation_approval(
            approval.approval_id,
            revoked_by="operator-b",
            reason="operator_changed_mind",
        )
    )

    assert revoked.status == RoutingAutomationApprovalStatus.REVOKED
    assert revoked.revoked_by == "operator-b"
    assert "routing_automation_approval_revoked" in revoked.reason_codes
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.consume_routing_automation_approval(
                approval.approval_id,
                consumed_by="future-action-hook",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_not_consumable"
    assert _counts(session_factory) == before

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    gate = asdict(inspection)["step_gate_states"]["recommendation_acceptance"]
    assert gate["status"] == "revoked"
    assert gate["approval_id"] == approval.approval_id


def test_consumed_approval_cannot_be_reused_and_remains_separate_from_action() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-a",
        )
    )
    before = _counts(session_factory)

    consumed = asyncio.run(
        routing.consume_routing_automation_approval(
            approval.approval_id,
            consumed_by="future-action-hook",
        )
    )

    assert consumed.status == RoutingAutomationApprovalStatus.CONSUMED
    assert consumed.provenance["action_execution_not_performed_by_approval_service"] is True
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.consume_routing_automation_approval(
                approval.approval_id,
                consumed_by="future-action-hook",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_not_consumable"
    with pytest.raises(RoutingAssessmentError) as revoke_exc:
        asyncio.run(
            routing.revoke_routing_automation_approval(
                approval.approval_id,
                revoked_by="operator-b",
            )
        )
    assert revoke_exc.value.reason_code == "routing_automation_approval_not_revocable"
    assert _counts(session_factory) == before


def test_blocked_recommendation_cannot_receive_approval() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.create_routing_automation_approval(
                recommendation.desired_trade_key or "",
                action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                approved_by="operator-a",
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_action_blocked"
    assert _counts(session_factory) == before


def test_target_choice_conversion_and_submit_approvals_remain_non_executing() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation, choice, desired_trade_key = _accepted_choice(session_factory)
    before = _counts(session_factory)

    conversion_approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
            approved_by="operator-a",
        )
    )

    assert conversion_approval.status == RoutingAutomationApprovalStatus.ACTIVE
    assert conversion_approval.routing_target_choice_id == choice.target_choice_id
    assert conversion_approval.routing_target_recommendation_id == (
        recommendation.routing_target_recommendation_id
    )
    after = _counts(session_factory)
    assert after["automation_approvals"] == before["automation_approvals"] + 1
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]

    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
        )
    )
    assert plan.outcome == RoutingAutomationPlanOutcome.DRY_RUN_ONLY
    assert plan.artifacts_created_by_plan is False
    assert _counts(session_factory) == after


def test_routing_automation_approval_api_create_inspect_revoke() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before = _counts(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/routing-automation/approvals",
                json={
                    "desired_trade_key": desired_trade_key,
                    "action_name": "recommendation_acceptance",
                    "approved_by": "operator-a",
                    "notes": "approve controlled acceptance gate only",
                },
            )
            approval_id = create_response.json()["approval_id"]
            inspect_response = client.get(
                f"/api/v1/routing-automation/approvals/by-desired-trade/{desired_trade_key}"
            )
            revoke_response = client.post(
                f"/api/v1/routing-automation/approvals/{approval_id}/revoke",
                json={"actor": "operator-b", "reason": "operator_revoked"},
            )
    finally:
        app.dependency_overrides.pop(get_routing_assessment_service, None)

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "active"
    assert created["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert created["provenance"]["action_executed"] is False
    assert created["boundary_flags"]["route_executor"] is False
    assert created["boundary_flags"]["auto_submit"] is False

    assert inspect_response.status_code == 200
    inspection = inspect_response.json()
    assert inspection["artifacts_created_by_inspection"] is False
    assert inspection["step_gate_states"]["recommendation_acceptance"]["status"] == "approved"
    assert inspection["step_gate_states"]["recommendation_acceptance"]["approval_id"] == approval_id

    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"
    after = _counts(session_factory)
    assert after["automation_approvals"] == before["automation_approvals"] + 1
    assert after["routing_target_choices"] == before["routing_target_choices"]
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]
