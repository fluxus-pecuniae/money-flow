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


def test_expired_approval_is_not_reused_and_replacement_becomes_current() -> None:
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
            expires_at=datetime.now(UTC) + timedelta(seconds=1),
        )
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

    replacement = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-b",
        )
    )

    assert replacement.approval_id != approval.approval_id
    assert replacement.status == RoutingAutomationApprovalStatus.ACTIVE
    with session_factory() as session:
        models = list(
            session.scalars(
                select(RoutingAutomationApprovalModel)
                .where(
                    RoutingAutomationApprovalModel.desired_trade_key == desired_trade_key,
                    RoutingAutomationApprovalModel.action_name
                    == RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                )
                .order_by(RoutingAutomationApprovalModel.created_at.asc())
            )
        )
    assert [model.status for model in models] == [
        RoutingAutomationApprovalStatus.EXPIRED.value,
        RoutingAutomationApprovalStatus.ACTIVE.value,
    ]

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    gate = asdict(inspection)["step_gate_states"]["recommendation_acceptance"]
    assert gate["status"] == "approved"
    assert gate["approval_id"] == replacement.approval_id


def test_stale_lineage_approval_is_not_reused_for_new_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    first_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    first_approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-a",
        )
    )

    second_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert second_recommendation.routing_target_recommendation_id != (
        first_recommendation.routing_target_recommendation_id
    )

    stale_inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    stale_gate = asdict(stale_inspection)["step_gate_states"]["recommendation_acceptance"]
    assert stale_gate["status"] == RoutingAutomationApprovalStatus.STALE_LINEAGE.value
    assert stale_gate["approval_id"] == first_approval.approval_id
    assert "routing_automation_approval_lineage_stale" in stale_gate["reason_codes"]

    replacement = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-b",
        )
    )

    assert replacement.approval_id != first_approval.approval_id
    assert replacement.routing_target_recommendation_id == (
        second_recommendation.routing_target_recommendation_id
    )
    with session_factory() as session:
        models = list(
            session.scalars(
                select(RoutingAutomationApprovalModel)
                .where(
                    RoutingAutomationApprovalModel.desired_trade_key == desired_trade_key,
                    RoutingAutomationApprovalModel.action_name
                    == RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                )
                .order_by(RoutingAutomationApprovalModel.created_at.asc())
            )
        )
    assert [model.status for model in models] == [
        RoutingAutomationApprovalStatus.STALE_LINEAGE.value,
        RoutingAutomationApprovalStatus.ACTIVE.value,
    ]

    current_inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    current_gate = asdict(current_inspection)["step_gate_states"]["recommendation_acceptance"]
    assert current_gate["status"] == "approved"
    assert current_gate["approval_id"] == replacement.approval_id


def test_repeated_create_reuses_one_active_approval_for_current_lineage_scope() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    first = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-a",
        )
    )
    second = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            approved_by="operator-b",
        )
    )

    assert second.approval_id == first.approval_id
    assert second.approval_scope_key == first.approval_scope_key
    with session_factory() as session:
        active_count = session.scalar(
            select(func.count())
            .select_from(RoutingAutomationApprovalModel)
            .where(
                RoutingAutomationApprovalModel.desired_trade_key == desired_trade_key,
                RoutingAutomationApprovalModel.action_name
                == RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                RoutingAutomationApprovalModel.status
                == RoutingAutomationApprovalStatus.ACTIVE.value,
                RoutingAutomationApprovalModel.approval_scope_key == first.approval_scope_key,
            )
        )
        total_count = session.scalar(
            select(func.count())
            .select_from(RoutingAutomationApprovalModel)
            .where(
                RoutingAutomationApprovalModel.desired_trade_key == desired_trade_key,
                RoutingAutomationApprovalModel.action_name
                == RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
            )
        )
    assert active_count == 1
    assert total_count == 1


def test_dry_run_only_step_cannot_receive_active_approval() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.create_routing_automation_approval(
                desired_trade_key,
                action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                approved_by="operator-a",
                policy=routing.routing_automation_policy(
                    mode=RoutingAutomationMode.DRY_RUN_ONLY
                ),
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_action_dry_run_only"
    assert _counts(session_factory) == before


def test_manual_only_step_cannot_receive_active_approval_even_with_custom_policy() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.create_routing_automation_approval(
                desired_trade_key,
                action_name=RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value,
                approved_by="operator-a",
                policy=routing.routing_automation_policy(
                    mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
                    allow_recommendation_acceptance=False,
                ),
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_action_manual_only"
    assert _counts(session_factory) == before


def test_plan_gate_status_does_not_approve_dry_run_or_manual_current_steps() -> None:
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

    dry_run_plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
        )
    )
    dry_run_gate = dry_run_plan.approval_gate_states["recommendation_acceptance"]
    assert dry_run_gate["status"] == "dry_run_only"
    assert dry_run_gate["approval_id"] == approval.approval_id
    assert "routing_automation_dry_run_only" in dry_run_gate["reason_codes"]

    manual_plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(
                mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
                allow_recommendation_acceptance=False,
            ),
        )
    )
    manual_gate = manual_plan.approval_gate_states["recommendation_acceptance"]
    assert manual_gate["status"] == "manual_only"
    assert manual_gate["approval_id"] == approval.approval_id
    assert "manual_only_by_policy" in manual_gate["reason_codes"]


def test_approval_inspection_does_not_mark_manual_only_step_approved() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    now = datetime.now(UTC)
    scope = routing._routing_automation_approval_scope(
        action=RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF,
        desired_trade_key=desired_trade_key,
        lineage={},
    )
    with session_factory() as session:
        session.add(
            RoutingAutomationApprovalModel(
                environment=routing.settings.app.environment,
                approval_id="rtaap_legacy_manual_submit",
                desired_trade_key=desired_trade_key,
                action_name=RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value,
                status=RoutingAutomationApprovalStatus.ACTIVE.value,
                lineage_fingerprint=scope["lineage_fingerprint"],
                approval_scope_key=scope["approval_scope_key"],
                approved_by="legacy-operator",
                approved_at=now,
                policy_name="legacy_manual_submit_fixture",
                automation_mode=RoutingAutomationMode.APPROVAL_REQUIRED.value,
                reason_codes_json=["legacy_active_submit_approval_fixture"],
                boundary_flags_json=routing._routing_automation_boundary_flags(),
                policy_snapshot_json={},
                lineage_json={},
                provenance_json={
                    "legacy_fixture": True,
                    "action_executed": False,
                },
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(desired_trade_key)
    )
    gate = asdict(inspection)["step_gate_states"]["submitted_order_handoff"]
    assert gate["status"] == "manual_only"
    assert gate["approval_id"] == "rtaap_legacy_manual_submit"
    assert "submitted_order_handoff_remains_explicit_manual_phase_7_0" in gate["reason_codes"]


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
