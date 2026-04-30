from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingTargetChoiceStatus,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RoutingAutomationApprovalModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from services.routing.service import RoutingAssessmentError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase600_routing_target_recommendation import _ready_audit


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


def _recommendation_and_approval(session_factory):
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
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
    return routing, audit, desired_trade_key, recommendation, approval


def test_approval_gated_recommendation_acceptance_consumes_approval_only_to_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )
    before = _counts(session_factory)

    result = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    after = _counts(session_factory)

    assert result.target_choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    assert result.target_choice.provenance["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert result.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert result.approval.routing_target_choice_id == result.target_choice_id
    assert result.approval.consumed_by == "automation-operator"
    assert result.approval.provenance["approval_gated_recommendation_acceptance"] is True
    assert result.approval.provenance["routing_target_choice_id"] == result.target_choice_id
    assert result.approval.provenance["child_intent_created"] is False
    assert result.child_intent_created is False
    assert result.prepared_order_created is False
    assert result.readiness_assessment_created is False
    assert result.submitted_order_created is False
    assert result.boundary_flags["fanout"] is False
    assert result.boundary_flags["cbbo"] is False
    assert result.boundary_flags["ranking"] is False
    assert result.boundary_flags["scoring"] is False
    assert result.boundary_flags["target_reselection"] is False
    assert result.boundary_flags["route_executor"] is False
    assert result.boundary_flags["auto_submit"] is False
    assert after["target_choices"] == before["target_choices"] + 1
    assert after["automation_approvals"] == before["automation_approvals"]
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]

    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED),
        )
    )
    assert plan.approval_gate_states["recommendation_acceptance"]["status"] == (
        "already_satisfied"
    )
    assert plan.approval_gate_states["recommendation_acceptance"]["approval_id"] == (
        approval.approval_id
    )


def test_approval_gated_recommendation_acceptance_is_idempotent_for_same_approval() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )

    first = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    before_repeat = _counts(session_factory)
    second = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    after_repeat = _counts(session_factory)

    assert second.target_choice_id == first.target_choice_id
    assert second.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert second.approval.consumed_at == first.approval.consumed_at
    assert after_repeat == before_repeat


def test_invalid_approvals_cannot_authorize_recommendation_acceptance() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )

    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    with pytest.raises(RoutingAssessmentError) as expired_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert expired_exc.value.reason_code == "routing_automation_approval_expired"
    assert _counts(session_factory)["target_choices"] == 0

    replacement = asyncio.run(
        routing.create_routing_automation_approval(
            recommendation.desired_trade_key or "",
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-b",
        )
    )
    revoked = asyncio.run(
        routing.revoke_routing_automation_approval(
            replacement.approval_id,
            revoked_by="operator-b",
        )
    )
    assert revoked.status == RoutingAutomationApprovalStatus.REVOKED
    with pytest.raises(RoutingAssessmentError) as revoked_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=replacement.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert revoked_exc.value.reason_code == "routing_automation_approval_revoked"

    wrong_action = asyncio.run(
        routing.create_routing_automation_approval(
            recommendation.desired_trade_key or "",
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-c",
        )
    )
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == wrong_action.approval_id
            )
        )
        assert model is not None
        model.action_name = RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value
        session.commit()
    with pytest.raises(RoutingAssessmentError) as wrong_action_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=wrong_action.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert wrong_action_exc.value.reason_code == "routing_automation_approval_wrong_action"

    second_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert second_recommendation.routing_target_recommendation_id != (
        recommendation.routing_target_recommendation_id
    )
    stale_approval = asyncio.run(
        routing.create_routing_automation_approval(
            recommendation.desired_trade_key or "",
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-d",
        )
    )
    with pytest.raises(RoutingAssessmentError) as wrong_recommendation_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=stale_approval.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert wrong_recommendation_exc.value.reason_code in {
        "routing_automation_approval_wrong_recommendation",
        "routing_automation_approval_lineage_stale",
    }
    assert _counts(session_factory)["child_intents"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0


def test_consumed_approval_cannot_authorize_a_different_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )
    first = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    second_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                second_recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_consumed_for_different_action"
    assert _counts(session_factory)["target_choices"] == 1
    assert first.target_choice_id is not None


def test_dry_run_and_manual_only_policy_cannot_execute_approval_gated_acceptance() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )

    with pytest.raises(RoutingAssessmentError) as dry_run_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
                policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
            )
        )
    assert dry_run_exc.value.reason_code == "routing_automation_approval_action_dry_run_only"

    with pytest.raises(RoutingAssessmentError) as manual_exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
                policy=routing.routing_automation_policy(
                    mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
                    allow_recommendation_acceptance=False,
                ),
            )
        )
    assert manual_exc.value.reason_code == "routing_automation_approval_action_manual_only"
    assert _counts(session_factory)["target_choices"] == 0
    assert _counts(session_factory)["child_intents"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0


def test_approval_gated_recommendation_acceptance_api_returns_choice_and_consumed_approval() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _desired_trade_key, recommendation, approval = _recommendation_and_approval(
        session_factory
    )
    before = _counts(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routing-automation/approvals/{approval.approval_id}/accept-recommendation",
                json={
                    "routing_target_recommendation_id": (
                        recommendation.routing_target_recommendation_id
                    ),
                    "actor": "automation-operator",
                    "approval_note": "consume approval for recommendation acceptance only",
                },
            )
    finally:
        app.dependency_overrides.pop(get_routing_assessment_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval"]["status"] == "consumed"
    assert payload["approval"]["routing_target_choice_id"] == payload["target_choice_id"]
    assert payload["target_choice"]["status"] == "target_choice_recorded"
    assert payload["child_intent_created"] is False
    assert payload["readiness_assessment_created"] is False
    assert payload["submitted_order_created"] is False
    assert payload["boundary_flags"]["route_executor"] is False
    assert payload["boundary_flags"]["auto_submit"] is False
    after = _counts(session_factory)
    assert after["target_choices"] == before["target_choices"] + 1
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]
