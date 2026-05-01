from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service, get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    ExecutionReadinessOutcome,
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingAutomationStepStatus,
    VenueOrderPreviewStatus,
)
from core.domain.models import RoutingAutomationPlanStep
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    RoutingAutomationApprovalModel,
    SubmittedOrderModel,
)
from services.routing.service import RoutingAssessmentError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase53_routed_child_intent_readiness import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _mutate_ready_candidate_quote_observed_at,
)
from tests.test_phase73_approval_gated_target_choice_conversion import (
    _accepted_choice_and_conversion_approval,
)


def _counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
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


def _preview_readiness_context(session_factory):
    routing, audit, recommendation, choice, desired_trade_key, conversion_approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    conversion = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=conversion_approval.approval_id,
            consumed_by="conversion-operator",
        )
    )
    assert conversion.intent_id is not None
    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.PREVIEW_READINESS.value,
            approved_by="operator-a",
        )
    )
    execution, adapter = _build_execution(session_factory)
    return routing, audit, recommendation, choice, desired_trade_key, conversion, approval, execution, adapter


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


def _assert_counts_unchanged(session_factory, before: dict[str, int]) -> None:
    after = _counts(session_factory)
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]


def _assert_no_submission(session_factory, adapter) -> None:
    assert _counts(session_factory)["submitted_orders"] == 0
    assert adapter.submit_calls == 0


def test_approval_gated_preview_readiness_consumes_approval_without_submission() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        recommendation,
        choice,
        desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    before = _counts(session_factory)

    result = asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=approval.approval_id,
            consumed_by="readiness-operator",
            execution_service=execution,
        )
    )
    after = _counts(session_factory)

    assert result.intent_id == conversion.intent_id
    assert result.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert result.approval.intent_id == conversion.intent_id
    assert result.approval.readiness_evaluation_id == result.readiness_evaluation_id
    assert result.prepared_order_preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert result.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in result.readiness.reason_codes
    assert result.approval.provenance["approval_gated_prepared_order_preview_and_readiness"] is True
    assert result.approval.provenance["submitted_order_created"] is False
    assert result.approval.provenance["exchange_submit_called"] is False
    assert result.approval.provenance["auto_submit"] is False
    assert result.approval.provenance["route_executor"] is False
    assert result.boundary_flags["fanout"] is False
    assert result.boundary_flags["cbbo"] is False
    assert result.boundary_flags["ranking"] is False
    assert result.boundary_flags["scoring"] is False
    assert result.boundary_flags["target_reselection"] is False
    assert result.boundary_flags["route_executor"] is False
    assert result.boundary_flags["auto_submit"] is False
    assert result.prepared_order_preview.payload["routed_lineage"][
        "routing_target_recommendation_id"
    ] == recommendation.routing_target_recommendation_id
    assert result.readiness.provenance["routed_lineage"]["route_readiness_audit_id"] == (
        audit.route_readiness_audit_id
    )
    assert result.readiness.provenance["routed_lineage"]["routing_target_choice_id"] == (
        choice.target_choice_id
    )
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"] + 1
    assert after["automation_approvals"] == before["automation_approvals"]
    _assert_no_submission(session_factory, adapter)

    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED),
        )
    )
    assert plan.approval_gate_states["prepared_order_preview_and_readiness"]["status"] == (
        "already_satisfied"
    )
    assert plan.approval_gate_states["prepared_order_preview_and_readiness"]["approval_id"] == (
        approval.approval_id
    )


def test_approval_gated_preview_readiness_is_idempotent_for_same_approval() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)

    first = asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=approval.approval_id,
            consumed_by="readiness-operator",
            execution_service=execution,
        )
    )
    before_repeat = _counts(session_factory)
    second = asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=approval.approval_id,
            consumed_by="readiness-operator",
            execution_service=execution,
        )
    )
    after_repeat = _counts(session_factory)

    assert second.readiness_evaluation_id == first.readiness_evaluation_id
    assert second.readiness_assessment_created is False
    assert second.readiness_assessment_reused is True
    assert second.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert second.approval.consumed_at == first.approval.consumed_at
    assert after_repeat == before_repeat
    _assert_no_submission(session_factory, adapter)


def test_preview_readiness_rolls_back_if_approval_consumption_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)

    def fail_consumption(*_args, **kwargs):
        assert kwargs["readiness"].readiness_evaluation_id.startswith("ready-")
        raise RuntimeError("forced preview/readiness approval consumption failure")

    monkeypatch.setattr(routing, "_consume_preview_readiness_approval_model", fail_consumption)

    with pytest.raises(
        RuntimeError,
        match="forced preview/readiness approval consumption failure",
    ):
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )

    assert _counts(session_factory)["readiness_evaluations"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0
    model = _approval_model(session_factory, approval.approval_id)
    assert model.status == RoutingAutomationApprovalStatus.ACTIVE.value
    assert model.readiness_evaluation_id is None
    assert model.consumed_at is None
    assert model.consumed_by is None
    assert dict(model.provenance_json or {}).get(
        "approval_gated_prepared_order_preview_and_readiness"
    ) is not True
    _assert_no_submission(session_factory, adapter)


def test_invalid_approval_states_cannot_authorize_preview_readiness() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)

    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    before = _counts(session_factory)
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_expired"
    _assert_counts_unchanged(session_factory, before)

    revoked = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.PREVIEW_READINESS.value,
            approved_by="operator-a",
        )
    )
    asyncio.run(
        routing.revoke_routing_automation_approval(
            revoked.approval_id,
            revoked_by="operator-a",
            reason="test_revocation",
        )
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=revoked.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_revoked"

    wrong_action = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.PREVIEW_READINESS.value,
            approved_by="operator-a",
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
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=wrong_action.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"
    assert _counts(session_factory)["readiness_evaluations"] == 0
    _assert_no_submission(session_factory, adapter)


def test_consumed_preview_readiness_approval_cannot_authorize_a_different_child_intent() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=approval.approval_id,
            consumed_by="readiness-operator",
            execution_service=execution,
        )
    )
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.intent_id = "different-child-intent"
        session.commit()

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_consumed_for_different_action"
    assert _counts(session_factory)["readiness_evaluations"] == 1
    _assert_no_submission(session_factory, adapter)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("routing_target_recommendation_id", "wrong-routing-target-recommendation-id"),
        ("route_readiness_audit_id", "wrong-route-readiness-audit-id"),
        ("routing_target_choice_id", "wrong-routing-target-choice-id"),
        ("desired_trade_key", "wrong-desired-trade-key"),
    ],
)
def test_wrong_approval_lineage_blocks_preview_readiness(
    field_name: str,
    bad_value: str,
) -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        setattr(model, field_name, bad_value)
        session.commit()
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_lineage_stale"
    _assert_counts_unchanged(session_factory, before)
    model = _approval_model(session_factory, approval.approval_id)
    assert model.status == RoutingAutomationApprovalStatus.STALE_LINEAGE.value
    assert "routing_automation_approval_lineage_stale" in (model.reason_codes_json or [])
    _assert_no_submission(session_factory, adapter)


def test_disabled_preview_readiness_step_blocks_approval_gated_action() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
                policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DISABLED),
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_action_not_available"
    _assert_counts_unchanged(session_factory, before)
    _assert_no_submission(session_factory, adapter)


@pytest.mark.parametrize(
    ("step_status", "step_reason", "expected_reason"),
    [
        (
            RoutingAutomationStepStatus.BLOCKED,
            "forced_preview_readiness_blocked_for_test",
            "routing_automation_approval_action_blocked",
        ),
        (
            RoutingAutomationStepStatus.DEFERRED,
            "forced_preview_readiness_deferred_for_test",
            "routing_automation_approval_action_not_available",
        ),
        (
            RoutingAutomationStepStatus.ALREADY_SATISFIED,
            "forced_preview_readiness_already_satisfied_for_test",
            "routing_automation_approval_action_already_satisfied",
        ),
    ],
)
def test_non_approvable_preview_readiness_step_blocks_action(
    monkeypatch: pytest.MonkeyPatch,
    step_status: RoutingAutomationStepStatus,
    step_reason: str,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    original_step_for_action = routing._routing_automation_step_for_action

    def forced_preview_readiness_step(plan, action):
        if action != RoutingAutomationApprovalAction.PREVIEW_READINESS:
            return original_step_for_action(plan, action)
        base_step = original_step_for_action(plan, action)
        return RoutingAutomationPlanStep(
            name=action.value,
            status=step_status,
            artifact_id=base_step.artifact_id,
            would_create_artifact_type="PreparedVenueOrderPreviewAndExecutionReadinessAssessment",
            reason_codes=[step_reason],
            blocked=step_status == RoutingAutomationStepStatus.BLOCKED,
            lineage=dict(base_step.lineage),
        )

    monkeypatch.setattr(routing, "_routing_automation_step_for_action", forced_preview_readiness_step)
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
            )
        )

    assert exc.value.reason_code == expected_reason
    _assert_counts_unchanged(session_factory, before)
    _assert_no_submission(session_factory, adapter)


def test_dry_run_and_manual_only_policies_block_preview_readiness_action() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=approval.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
                policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_action_dry_run_only"

    fresh = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.PREVIEW_READINESS.value,
            approved_by="operator-a",
        )
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.preview_and_assess_child_intent_readiness_with_approval(
                conversion.intent_id or "",
                approval_id=fresh.approval_id,
                consumed_by="readiness-operator",
                execution_service=execution,
                policy=routing.routing_automation_policy(
                    mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
                    allow_preview_readiness=False,
                ),
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_action_manual_only"
    assert _counts(session_factory)["readiness_evaluations"] == 0
    _assert_no_submission(session_factory, adapter)


def test_blocked_readiness_remains_reason_coded_and_non_submitting() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        adapter,
    ) = _preview_readiness_context(session_factory)
    ready_candidate = audit.candidates[0]
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=ready_candidate.binding_key,
    )

    result = asyncio.run(
        routing.preview_and_assess_child_intent_readiness_with_approval(
            conversion.intent_id or "",
            approval_id=approval.approval_id,
            consumed_by="readiness-operator",
            execution_service=execution,
        )
    )

    assert result.prepared_order_preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert result.readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "quote_stale_at_readiness" in result.readiness.reason_codes
    assert result.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert adapter.prepare_calls == 0
    _assert_no_submission(session_factory, adapter)


def test_approval_gated_preview_readiness_api_returns_consumed_approval_and_readiness() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        approval,
        execution,
        _adapter,
    ) = _preview_readiness_context(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routing-automation/approvals/{approval.approval_id}/preview-readiness",
                json={
                    "intent_id": conversion.intent_id,
                    "actor": "api-operator",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["approval"]["status"] == "consumed"
    assert payload["approval"]["intent_id"] == payload["intent_id"]
    assert payload["approval"]["readiness_evaluation_id"] == payload["readiness_evaluation_id"]
    assert payload["prepared_order_preview"]["preview_status"] == "preparable"
    assert payload["readiness"]["outcome"] == "phase_blocked"
    assert payload["submitted_order_created"] is False
    assert payload["exchange_submit_called"] is False
    assert payload["auto_submit"] is False
    assert payload["route_executor_used"] is False
    assert _counts(session_factory)["readiness_evaluations"] == 1
    assert _counts(session_factory)["submitted_orders"] == 0
