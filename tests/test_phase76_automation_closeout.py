from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select

from core.domain.enums import (
    ExecutionReadinessOutcome,
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingTargetChoiceStatus,
    RoutingTargetRecommendationStatus,
    SubmittedOrderStatus,
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
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase600_routing_target_recommendation import _ready_audit
from tests.test_phase69_routed_workflow_inspection import _workflow_response
from tests.test_phase75_approval_gated_submission_handoff import (
    _submission_handoff_context,
)


NO_SOR_FALSE_FLAGS = (
    "smart_routing",
    "best_binding_selection",
    "cbbo",
    "fanout",
    "split_allocation",
    "ranking",
    "scoring",
    "target_reselection",
    "route_executor",
    "auto_submit",
    "cross_binding_recovery",
    "cross_venue_retry",
)


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


def _assert_no_sor_flags(flags: dict[str, object]) -> None:
    assert flags["same_target_only"] is True
    assert flags["same_account_only"] is True
    assert flags["same_venue_only"] is True
    for flag in NO_SOR_FALSE_FLAGS:
        assert flags[flag] is False


def _create_recommendation(session_factory):
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    return routing, audit, desired_trade_key, recommendation


def _create_approval(routing, desired_trade_key: str, action: RoutingAutomationApprovalAction):
    return asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=action.value,
            approved_by="phase76-operator",
        )
    )


def _approval_model(session_factory, approval_id: str) -> RoutingAutomationApprovalModel:
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval_id
            )
        )
        assert model is not None
        session.expunge(model)
        return model


def test_phase7_closeout_end_to_end_approval_gated_chain_stays_single_target() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key, recommendation = _create_recommendation(
        session_factory
    )
    counts_after_recommendation = _counts(session_factory)

    dry_run_plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(
                mode=RoutingAutomationMode.APPROVAL_REQUIRED
            ),
            dry_run=True,
        )
    )
    assert dry_run_plan.artifacts_created_by_plan is False
    assert dry_run_plan.persisted is False
    _assert_no_sor_flags(dry_run_plan.boundary_flags)
    assert _counts(session_factory) == counts_after_recommendation

    acceptance_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    counts_after_acceptance_approval = _counts(session_factory)
    assert counts_after_acceptance_approval["automation_approvals"] == (
        counts_after_recommendation["automation_approvals"] + 1
    )
    assert counts_after_acceptance_approval["target_choices"] == 0

    acceptance = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=acceptance_approval.approval_id,
            consumed_by="phase76-operator",
        )
    )
    choice = acceptance.target_choice
    assert choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    assert acceptance.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert acceptance.approval.routing_target_choice_id == choice.target_choice_id
    assert acceptance.child_intent_created is False
    assert acceptance.readiness_assessment_created is False
    assert acceptance.submitted_order_created is False
    _assert_no_sor_flags(acceptance.boundary_flags)
    assert _counts(session_factory)["target_choices"] == 1
    assert _counts(session_factory)["child_intents"] == 0

    conversion_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION,
    )
    conversion = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=conversion_approval.approval_id,
            consumed_by="phase76-operator",
        )
    )
    assert conversion.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert conversion.approval.routing_target_choice_id == choice.target_choice_id
    assert conversion.approval.intent_id == conversion.intent_id
    assert conversion.prepared_order_created is False
    assert conversion.readiness_assessment_created is False
    assert conversion.submitted_order_created is False
    _assert_no_sor_flags(conversion.boundary_flags)
    assert _counts(session_factory)["child_intents"] == 1
    assert _counts(session_factory)["readiness_evaluations"] == 0

    execution, adapter = _build_execution(
        session_factory,
        routed_submission_enabled=True,
        live_submission_enabled=True,
    )
    preview_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.PREVIEW_READINESS,
    )
    preview = asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=preview_approval.approval_id,
            consumed_by="phase76-operator",
            execution_service=execution,
        )
    )
    assert preview.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert preview.approval.intent_id == conversion.intent_id
    assert preview.approval.readiness_evaluation_id == preview.readiness_evaluation_id
    assert preview.readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    assert preview.submitted_order_created is False
    assert preview.exchange_submit_called is False
    assert preview.auto_submit is False
    assert preview.route_executor_used is False
    _assert_no_sor_flags(preview.boundary_flags)
    assert adapter.submit_calls == 0
    assert _counts(session_factory)["readiness_evaluations"] == 1
    assert _counts(session_factory)["submitted_orders"] == 0

    submit_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF,
    )
    handoff = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id or "",
            approval_id=submit_approval.approval_id,
            consumed_by="phase76-operator",
            execution_service=execution,
        )
    )
    assert handoff.submitted_order.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert handoff.submitted_order.intent_id == conversion.intent_id
    assert handoff.submitted_order_created is True
    assert handoff.exchange_submit_called is True
    assert handoff.auto_submit is False
    assert handoff.route_executor_used is False
    assert handoff.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert handoff.approval.submitted_order_id == handoff.submitted_order_id
    _assert_no_sor_flags(handoff.boundary_flags)
    assert adapter.submit_calls == 1

    final_counts = _counts(session_factory)
    assert final_counts == {
        "recommendations": 1,
        "target_choices": 1,
        "child_intents": 1,
        "readiness_evaluations": 1,
        "submitted_orders": 1,
        "automation_approvals": 4,
    }

    expected_route_lineage = {
        "desired_trade_key": desired_trade_key,
        "routing_assessment_id": audit.routing_assessment_id,
        "route_readiness_audit_id": audit.route_readiness_audit_id,
        "routing_target_recommendation_id": recommendation.routing_target_recommendation_id,
        "routing_target_choice_id": choice.target_choice_id,
        "intent_id": conversion.intent_id,
        "selected_binding_ref_id": choice.selected_binding_ref_id,
        "selected_venue_account_ref_id": choice.selected_venue_account_ref_id,
        "selected_venue": choice.selected_venue,
        "selected_exchange_symbol": conversion.conversion.selected_exchange_symbol,
    }
    routed_payload = handoff.submitted_order.raw_payload["routed_submission"]
    for key, value in expected_route_lineage.items():
        assert routed_payload[key] == value
    assert routed_payload["readiness_evaluation_id"] == preview.readiness_evaluation_id
    assert handoff.submitted_order.submitted_order_id == handoff.submitted_order_id
    assert routed_payload["explicit_submit_action"] is True
    assert routed_payload["auto_submit"] is False
    assert routed_payload["fanout_created"] is False
    assert routed_payload["allocation_created"] is False
    assert routed_payload["scoring_created"] is False
    assert routed_payload["route_executor_created"] is False
    assert routed_payload["target_reselection"] is False

    workflow = _workflow_response(routing, desired_trade_key)
    assert workflow["artifacts_created_by_inspection"] is False
    assert workflow["artifact_counts"]["routing_target_recommendations"] == 1
    assert workflow["artifact_counts"]["routing_target_choices"] == 1
    assert workflow["artifact_counts"]["child_intents"] == 1
    assert workflow["artifact_counts"]["readiness_evaluations"] == 1
    assert workflow["artifact_counts"]["submitted_orders"] == 1
    for key, value in expected_route_lineage.items():
        assert workflow["routed_lineage"][key] == value
    assert workflow["readiness_evaluations"][0]["readiness_evaluation_id"] == (
        preview.readiness_evaluation_id
    )
    assert workflow["submitted_orders"][0]["submitted_order_id"] == handoff.submitted_order_id
    lifecycle_summary = workflow["same_target_lifecycle_summary"]
    assert lifecycle_summary["same_target_only"] is True
    assert lifecycle_summary["same_account_only"] is True
    assert lifecycle_summary["same_venue_only"] is True
    assert lifecycle_summary["fanout_created"] is False
    assert lifecycle_summary["allocation_created"] is False
    assert lifecycle_summary["scoring_created"] is False
    assert lifecycle_summary["route_executor_created"] is False
    assert lifecycle_summary["target_reselection"] is False

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(
            desired_trade_key
        )
    )
    assert inspection.artifacts_created_by_inspection is False
    _assert_no_sor_flags(inspection.boundary_flags)
    assert {approval.action_name for approval in inspection.approvals} == set(
        RoutingAutomationApprovalAction
    )
    assert all(
        approval.status == RoutingAutomationApprovalStatus.CONSUMED
        for approval in inspection.approvals
    )
    assert inspection.step_gate_states["recommendation_acceptance"].status == (
        "already_satisfied"
    )
    assert inspection.step_gate_states["target_choice_conversion"].status == (
        "already_satisfied"
    )
    assert inspection.step_gate_states["prepared_order_preview_and_readiness"].status == (
        "already_satisfied"
    )
    assert inspection.step_gate_states["submitted_order_handoff"].status == (
        "already_satisfied"
    )


def test_phase7_closeout_approvals_cannot_be_mixed_across_action_stages() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, desired_trade_key, recommendation = _create_recommendation(
        session_factory
    )
    acceptance_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id,
            requested_by="phase76-manual-operator",
        )
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=acceptance_approval.approval_id,
                consumed_by="phase76-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"
    assert _counts(session_factory)["child_intents"] == 0

    conversion_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION,
    )
    conversion = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    assert _counts(session_factory)["child_intents"] == 1
    execution, adapter = _build_execution(
        session_factory,
        routed_submission_enabled=True,
        live_submission_enabled=True,
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=conversion_approval.approval_id,
                consumed_by="phase76-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"
    assert _counts(session_factory)["readiness_evaluations"] == 0

    preview_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.PREVIEW_READINESS,
    )
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id or ""))
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id or "",
                approval_id=preview_approval.approval_id,
                consumed_by="phase76-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"
    assert adapter.submit_calls == 0
    assert _counts(session_factory)["submitted_orders"] == 0

    submit_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF,
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=submit_approval.approval_id,
                consumed_by="phase76-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"
    assert _counts(session_factory)["submitted_orders"] == 0
    assert adapter.submit_calls == 0


def test_phase7_closeout_stale_lineage_approval_does_not_satisfy_gate_truth() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, desired_trade_key, recommendation = _create_recommendation(
        session_factory
    )
    approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.approval_scope_key = "old-approval-scope"
        session.commit()

    stale_inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(
            desired_trade_key
        )
    )
    stale = next(
        item for item in stale_inspection.approvals if item.approval_id == approval.approval_id
    )
    assert stale.status == RoutingAutomationApprovalStatus.STALE_LINEAGE
    assert stale_inspection.step_gate_states["recommendation_acceptance"].status == (
        "stale_lineage"
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="phase76-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_lineage_stale"
    assert _counts(session_factory)["target_choices"] == 0

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(
            desired_trade_key
        )
    )
    stale = next(item for item in inspection.approvals if item.approval_id == approval.approval_id)
    assert stale.status == RoutingAutomationApprovalStatus.STALE_LINEAGE
    assert inspection.step_gate_states["recommendation_acceptance"].status == (
        "stale_lineage"
    )
    assert "routing_automation_approval_lineage_stale" in (
        inspection.step_gate_states["recommendation_acceptance"].reason_codes
    )

    fresh = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    assert fresh.status == RoutingAutomationApprovalStatus.ACTIVE
    assert fresh.approval_id != approval.approval_id


def test_phase7_closeout_consumption_pending_is_bounded_and_inspectable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    original_consume = routing._consume_submitted_order_handoff_approval

    def fail_consumption(*_args, **_kwargs):
        raise RuntimeError("phase76 forced post-submit approval consumption failure")

    monkeypatch.setattr(
        routing,
        "_consume_submitted_order_handoff_approval",
        fail_consumption,
    )
    with pytest.raises(RuntimeError, match="phase76 forced"):
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="phase76-operator",
                execution_service=execution,
            )
        )
    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 1

    inspection = asyncio.run(
        routing.inspect_routing_automation_approvals_for_desired_trade(
            desired_trade_key
        )
    )
    pending = next(
        item for item in inspection.approvals if item.approval_id == approval.approval_id
    )
    assert pending.status == RoutingAutomationApprovalStatus.CONSUMPTION_PENDING
    assert pending.status != RoutingAutomationApprovalStatus.ACTIVE
    assert pending.status != RoutingAutomationApprovalStatus.CONSUMED
    assert pending.submitted_order_id is not None
    assert pending.intent_id == conversion.intent_id
    assert "submitted_order_handoff_consumption_failed" in pending.reason_codes
    assert "submitted_order_created_approval_consumption_pending" in pending.reason_codes
    assert "manual_approval_reconciliation_required" in pending.reason_codes
    assert pending.provenance["approval_consumption_pending"] is True
    assert pending.provenance["manual_approval_reconciliation_required"] is True
    assert pending.provenance["auto_submit"] is False
    assert pending.provenance["route_executor"] is False
    gate = inspection.step_gate_states["submitted_order_handoff"]
    assert gate.approval_id == approval.approval_id
    assert "manual_approval_reconciliation_required" in gate.reason_codes

    before_repeat = _counts(session_factory)
    monkeypatch.setattr(
        routing,
        "_consume_submitted_order_handoff_approval",
        original_consume,
    )
    repeat = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=approval.approval_id,
            consumed_by="phase76-operator",
            execution_service=execution,
        )
    )
    after_repeat = _counts(session_factory)

    assert repeat.submitted_order_id == pending.submitted_order_id
    assert repeat.submitted_order_created is False
    assert repeat.submitted_order_reused is True
    assert repeat.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert adapter.submit_calls == 1
    assert after_repeat == before_repeat


def test_phase7_closeout_dry_run_approval_and_admin_consume_remain_non_executing() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, desired_trade_key, recommendation = _create_recommendation(
        session_factory
    )
    before_plan = _counts(session_factory)
    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
            dry_run=True,
        )
    )
    assert plan.dry_run is True
    assert plan.artifacts_created_by_plan is False
    assert _counts(session_factory) == before_plan

    approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    after_approval = _counts(session_factory)
    assert after_approval["automation_approvals"] == before_plan["automation_approvals"] + 1
    assert after_approval["target_choices"] == before_plan["target_choices"]
    assert after_approval["child_intents"] == before_plan["child_intents"]
    assert after_approval["readiness_evaluations"] == before_plan["readiness_evaluations"]
    assert after_approval["submitted_orders"] == before_plan["submitted_orders"]

    consumed = asyncio.run(
        routing.consume_routing_automation_approval(
            approval.approval_id,
            consumed_by="phase76-admin",
            reason="phase76_administrative_consume_only",
        )
    )
    after_admin_consume = _counts(session_factory)
    assert consumed.status == RoutingAutomationApprovalStatus.CONSUMED
    assert consumed.routing_target_choice_id is None
    assert consumed.intent_id is None
    assert consumed.readiness_evaluation_id is None
    assert consumed.submitted_order_id is None
    assert consumed.provenance["action_execution_not_performed_by_approval_service"] is True
    assert after_admin_consume == after_approval

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_with_approval(
                recommendation.routing_target_recommendation_id,
                approval_id=approval.approval_id,
                consumed_by="phase76-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_consumed_for_different_action"
    assert _counts(session_factory) == after_admin_consume
