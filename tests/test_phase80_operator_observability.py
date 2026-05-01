from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    ExecutionReadinessOutcome,
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingTargetRecommendationStatus,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    OrderIntentSubmissionLeaseModel,
    RoutingAutomationApprovalModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from services.exchange.base import VenueAdapterError
from services.execution.service import SubmissionFailedError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _multi_ready_audit,
    _ready_audit,
)
from tests.test_phase67_recommendation_backed_submission import (
    _recommendation_backed_submission_context,
)
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
            "submission_leases": session.scalar(
                select(func.count()).select_from(OrderIntentSubmissionLeaseModel)
            ),
        }


def _operator_summary_response(routing, desired_trade_key: str) -> dict[str, object]:
    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}"
            )
    finally:
        app.dependency_overrides.pop(get_routing_assessment_service, None)
    assert response.status_code == 200
    return response.json()


def _manual_codes(payload: dict[str, object]) -> set[str]:
    return {
        str(item["code"])
        for item in payload["manual_resolution_requirements"]
        if isinstance(item, dict)
    }


def _approval_states_by_action(payload: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    states: dict[str, list[dict[str, object]]] = {}
    for state in payload["approval_states"]:
        states.setdefault(str(state["action_name"]), []).append(state)
    return states


def _assert_no_sor_flags(flags: dict[str, object]) -> None:
    assert flags["same_target_only"] is True
    assert flags["same_account_only"] is True
    assert flags["same_venue_only"] is True
    assert flags["read_only_operator_inspection"] is True
    for flag in NO_SOR_FALSE_FLAGS:
        assert flags[flag] is False


def _create_approval(routing, desired_trade_key: str, action: RoutingAutomationApprovalAction):
    return asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=action.value,
            approved_by="phase80-operator",
            policy=routing.routing_automation_policy(
                mode=RoutingAutomationMode.APPROVAL_REQUIRED
            ),
        )
    )


def test_operator_summary_returns_full_phase7_chain_without_mutation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    acceptance_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE,
    )
    acceptance = asyncio.run(
        routing.accept_routing_target_recommendation_with_approval(
            recommendation.routing_target_recommendation_id,
            approval_id=acceptance_approval.approval_id,
            consumed_by="phase80-operator",
        )
    )
    conversion_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION,
    )
    conversion = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            acceptance.target_choice_id,
            approval_id=conversion_approval.approval_id,
            consumed_by="phase80-operator",
        )
    )
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
            consumed_by="phase80-operator",
            execution_service=execution,
        )
    )
    submit_approval = _create_approval(
        routing,
        desired_trade_key,
        RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF,
    )
    handoff = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id or "",
            approval_id=submit_approval.approval_id,
            consumed_by="phase80-operator",
            execution_service=execution,
        )
    )
    before = _counts(session_factory)
    submit_calls_before = adapter.submit_calls

    payload = _operator_summary_response(routing, desired_trade_key)

    assert payload["read_only"] is True
    assert payload["artifacts_created_by_inspection"] is False
    assert payload["actions_executed_by_inspection"] is False
    assert payload["approvals_consumed_by_inspection"] is False
    assert payload["manual_resolution_markers_created"] is False
    assert payload["workflow"]["current_status_summary"]["state"] == (
        "submitted_order_created"
    )
    assert payload["artifact_states"]["target_recommendation"]["latest_artifact_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert payload["artifact_states"]["target_choice"]["latest_artifact_id"] == (
        acceptance.target_choice_id
    )
    assert payload["artifact_states"]["child_intent"]["latest_artifact_id"] == (
        conversion.intent_id
    )
    assert payload["artifact_states"]["readiness"]["latest_artifact_id"] == (
        preview.readiness_evaluation_id
    )
    assert payload["artifact_states"]["submitted_order"]["latest_artifact_id"] == (
        handoff.submitted_order_id
    )
    by_action = _approval_states_by_action(payload)
    assert {
        states[-1]["effective_status"] for states in by_action.values()
    } == {RoutingAutomationApprovalStatus.CONSUMED.value}
    assert payload["submission_safety"]["submitted_order_persisted"] is True
    assert payload["submission_safety"]["approval_consumed"] is True
    assert payload["submission_safety"]["approval_consumption_pending"] is False
    assert payload["submission_safety"]["repeat_submit_policy"] == (
        "reuse_existing_submitted_order_truth"
    )
    assert payload["next_safe_operator_action"]["action"] == (
        "inspect_submitted_order_lifecycle"
    )
    _assert_no_sor_flags(payload["boundary_flags"])
    assert _counts(session_factory) == before
    assert adapter.submit_calls == submit_calls_before


def test_operator_summary_surfaces_consumption_pending_without_resubmitting(
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

    def fail_consumption(*args, **kwargs):
        raise RuntimeError("forced approval consumption failure after submit")

    monkeypatch.setattr(
        routing,
        "_consume_submitted_order_handoff_approval",
        fail_consumption,
    )
    with pytest.raises(RuntimeError, match="forced approval consumption failure"):
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="phase80-operator",
                execution_service=execution,
            )
        )
    before = _counts(session_factory)
    submit_calls_before = adapter.submit_calls

    payload = _operator_summary_response(routing, desired_trade_key)

    assert "approval_consumption_pending" in _manual_codes(payload)
    submit_states = _approval_states_by_action(payload)[
        RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value
    ]
    assert submit_states[-1]["effective_status"] == (
        RoutingAutomationApprovalStatus.CONSUMPTION_PENDING.value
    )
    assert submit_states[-1]["consumption_pending"] is True
    assert payload["submission_safety"]["submitted_order_persisted"] is True
    assert payload["submission_safety"]["approval_consumption_pending"] is True
    assert payload["submission_safety"]["repeat_submit_policy"] == (
        "blocked_until_manual_reconciliation"
    )
    assert payload["next_safe_operator_action"]["action"] == (
        "manual_reconciliation_required"
    )
    assert _counts(session_factory) == before
    assert adapter.submit_calls == submit_calls_before


def test_operator_summary_surfaces_adapter_submit_uncertainty_and_blocks_retry_visibility() -> None:
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

    async def ambiguous_submit_order(_submit_intent):
        adapter.submit_calls += 1
        raise VenueAdapterError(
            "transport timeout after submit request may have been transmitted",
            reason_codes=["transport_timeout"],
        )

    adapter.submit_order = ambiguous_submit_order
    with pytest.raises(SubmissionFailedError):
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="phase80-operator",
                execution_service=execution,
            )
        )
    before = _counts(session_factory)

    payload = _operator_summary_response(routing, desired_trade_key)

    assert "adapter_submit_may_have_started" in _manual_codes(payload)
    assert payload["submission_safety"]["submit_uncertainty"] is True
    assert payload["submission_safety"]["manual_reconciliation_required"] is True
    assert payload["submission_safety"]["repeat_submit_blocked"] is True
    assert payload["concurrency"]["terminal_uncertain_lease_count"] == 1
    assert payload["concurrency"]["submit_leases"][0]["status"] == (
        "adapter_submit_may_have_started"
    )
    assert "manual_reconciliation_required" in payload["uncertainty_reason_codes"]
    assert adapter.submit_calls == 1
    assert _counts(session_factory) == before


def test_operator_summary_surfaces_blocked_recommendation_blocked_readiness_and_stale_approval() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES

    blocked_payload = _operator_summary_response(routing, audit.desired_trade_key)
    assert "routing_target_recommendation_blocked" in _manual_codes(blocked_payload)
    assert blocked_payload["next_safe_operator_action"]["safe_to_automate"] is False

    (
        routing,
        _audit,
        _recommendation,
        _choice,
        desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(
        build_test_session_factory(),
        live_submission_enabled=False,
    )
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    readiness_payload = _operator_summary_response(routing, desired_trade_key)
    assert "execution_readiness_blocked" in _manual_codes(readiness_payload)
    assert adapter.submit_calls == 0

    (
        stale_routing,
        _stale_audit,
        _stale_recommendation,
        _stale_choice,
        stale_desired_trade_key,
        _stale_conversion,
        _stale_readiness,
        approval,
        _stale_execution,
        _stale_adapter,
    ) = _submission_handoff_context(build_test_session_factory())
    with stale_routing._session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.approval_scope_key = "stale-scope-for-phase80-test"
        session.add(model)
        session.commit()

    stale_payload = _operator_summary_response(stale_routing, stale_desired_trade_key)
    assert "stale_lineage_approval" in _manual_codes(stale_payload)
    submit_states = _approval_states_by_action(stale_payload)[
        RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value
    ]
    assert submit_states[-1]["effective_status"] == (
        RoutingAutomationApprovalStatus.STALE_LINEAGE.value
    )
    assert stale_payload["actions_executed_by_inspection"] is False
