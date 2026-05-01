from __future__ import annotations

import asyncio
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
    RoutingAutomationStepStatus,
    RoutingTargetChoiceConversionStatus,
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
from tests.test_phase63_recommendation_target_choice_conversion import (
    _accepted_choice,
    _insert_duplicate_recommendation_target_choice,
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


def _accepted_choice_and_conversion_approval(session_factory):
    routing, audit, recommendation, choice, desired_trade_key = _accepted_choice(session_factory)
    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
            approved_by="operator-a",
        )
    )
    return routing, audit, recommendation, choice, desired_trade_key, approval


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


def _assert_approval_unconsumed(
    session_factory,
    approval_id: str,
    *,
    status: RoutingAutomationApprovalStatus = RoutingAutomationApprovalStatus.ACTIVE,
) -> RoutingAutomationApprovalModel:
    model = _approval_model(session_factory, approval_id)
    assert model.status == status.value
    assert model.intent_id is None
    assert model.consumed_at is None
    assert model.consumed_by is None
    return model


def test_approval_gated_target_choice_conversion_consumes_approval_only_to_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    before = _counts(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    after = _counts(session_factory)

    assert result.conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.child_intent_created_or_reused is True
    assert result.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert result.approval.routing_target_choice_id == choice.target_choice_id
    assert result.approval.intent_id == result.intent_id
    assert result.approval.consumed_by == "automation-operator"
    assert result.approval.provenance["approval_gated_target_choice_conversion"] is True
    assert result.approval.provenance["prepared_order_created"] is False
    assert result.approval.provenance["readiness_assessment_created"] is False
    assert result.approval.provenance["submitted_order_created"] is False
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
    assert after["child_intents"] == before["child_intents"] + 1
    assert after["automation_approvals"] == before["automation_approvals"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"]

    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED),
        )
    )
    assert plan.approval_gate_states["target_choice_conversion"]["status"] == (
        "already_satisfied"
    )
    assert plan.approval_gate_states["target_choice_conversion"]["approval_id"] == (
        approval.approval_id
    )


def test_approval_gated_target_choice_conversion_is_idempotent_for_same_approval() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )

    first = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    before_repeat = _counts(session_factory)
    second = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    after_repeat = _counts(session_factory)

    assert second.intent_id == first.intent_id
    assert second.conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert second.approval.consumed_at == first.approval.consumed_at
    assert after_repeat == before_repeat


def test_approval_gated_conversion_rolls_back_if_approval_consumption_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )

    def fail_consumption(*_args, **kwargs):
        assert kwargs["conversion"].intent_id is not None
        raise RuntimeError("forced target-choice approval consumption failure")

    monkeypatch.setattr(
        routing,
        "_consume_target_choice_conversion_approval_model",
        fail_consumption,
    )

    with pytest.raises(RuntimeError, match="forced target-choice approval consumption failure"):
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )

    assert _counts(session_factory)["child_intents"] == 0
    assert _counts(session_factory)["readiness_evaluations"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0
    with session_factory() as session:
        approval_model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert approval_model is not None
        assert approval_model.status == RoutingAutomationApprovalStatus.ACTIVE.value
        assert approval_model.intent_id is None
        assert approval_model.consumed_at is None
        assert approval_model.consumed_by is None
        assert dict(approval_model.provenance_json or {}).get(
            "approval_gated_target_choice_conversion"
        ) is not True


def test_invalid_approvals_cannot_authorize_target_choice_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, recommendation, choice, desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
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
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_expired"

    revoked = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
            approved_by="operator-a",
        )
    )
    asyncio.run(
        routing.revoke_routing_automation_approval(
            revoked.approval_id,
            revoked_by="operator-b",
            reason="operator_revoked",
        )
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=revoked.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_revoked"

    wrong_action = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
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
        model.action_name = RoutingAutomationApprovalAction.RECOMMENDATION_ACCEPTANCE.value
        session.commit()
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=wrong_action.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_action"

    wrong_target = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
            approved_by="operator-a",
        )
    )
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == wrong_target.approval_id
            )
        )
        assert model is not None
        model.routing_target_choice_id = "different-target-choice"
        session.commit()
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=wrong_target.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_wrong_target_choice"
    assert _counts(session_factory)["child_intents"] == 0


def test_stale_lineage_and_policy_boundaries_block_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.selected_binding_key = "stale-binding-key"
        session.commit()
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_lineage_stale"

    fresh = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION.value,
            approved_by="operator-a",
        )
    )
    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=fresh.approval_id,
                consumed_by="automation-operator",
                policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DRY_RUN_ONLY),
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_action_dry_run_only"

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=fresh.approval_id,
                consumed_by="automation-operator",
                policy=routing.routing_automation_policy(
                    mode=RoutingAutomationMode.EXPLICIT_AUTOMATION_PERMITTED,
                    allow_target_choice_conversion=False,
                ),
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_action_manual_only"
    assert _counts(session_factory)["child_intents"] == 0
    assert _counts(session_factory)["readiness_evaluations"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0


def test_consumed_conversion_approval_cannot_authorize_a_different_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    first = asyncio.run(
        routing.convert_target_choice_to_child_intent_with_approval(
            choice.target_choice_id,
            approval_id=approval.approval_id,
            consumed_by="automation-operator",
        )
    )
    duplicate_choice_id = _insert_duplicate_recommendation_target_choice(
        session_factory,
        source_choice_id=choice.target_choice_id,
        recommendation_id=recommendation.routing_target_recommendation_id,
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                duplicate_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )
    assert exc.value.reason_code == "routing_automation_approval_consumed_for_different_action"
    assert _counts(session_factory)["child_intents"] == 1
    assert first.intent_id is not None


def test_disabled_conversion_step_blocks_approval_gated_target_choice_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
                policy=routing.routing_automation_policy(mode=RoutingAutomationMode.DISABLED),
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_action_not_available"
    _assert_counts_unchanged(session_factory, before)
    model = _assert_approval_unconsumed(session_factory, approval.approval_id)
    assert "routing_automation_approval_consumed" not in (model.reason_codes_json or [])


@pytest.mark.parametrize(
    ("step_status", "step_reason", "expected_reason"),
    [
        (
            RoutingAutomationStepStatus.BLOCKED,
            "forced_target_choice_conversion_blocked_for_test",
            "routing_automation_approval_action_blocked",
        ),
        (
            RoutingAutomationStepStatus.DEFERRED,
            "forced_target_choice_conversion_deferred_for_test",
            "routing_automation_approval_action_not_available",
        ),
        (
            RoutingAutomationStepStatus.ALREADY_SATISFIED,
            "forced_target_choice_conversion_already_satisfied_for_test",
            "routing_automation_approval_action_already_satisfied",
        ),
    ],
)
def test_non_approvable_conversion_step_blocks_approval_gated_target_choice_conversion(
    monkeypatch: pytest.MonkeyPatch,
    step_status: RoutingAutomationStepStatus,
    step_reason: str,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
    original_step_for_action = routing._routing_automation_step_for_action

    def forced_target_choice_conversion_step(plan, action):
        if action != RoutingAutomationApprovalAction.TARGET_CHOICE_CONVERSION:
            return original_step_for_action(plan, action)
        base_step = original_step_for_action(plan, action)
        return RoutingAutomationPlanStep(
            name=action.value,
            status=step_status,
            artifact_id=base_step.artifact_id,
            would_create_artifact_type="OrderIntent",
            reason_codes=[step_reason],
            blocked=step_status == RoutingAutomationStepStatus.BLOCKED,
            lineage=dict(base_step.lineage),
        )

    monkeypatch.setattr(
        routing,
        "_routing_automation_step_for_action",
        forced_target_choice_conversion_step,
    )
    before = _counts(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )

    assert exc.value.reason_code == expected_reason
    _assert_counts_unchanged(session_factory, before)
    _assert_approval_unconsumed(session_factory, approval.approval_id)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("routing_target_recommendation_id", "wrong-routing-target-recommendation-id"),
        ("route_readiness_audit_id", "wrong-route-readiness-audit-id"),
        ("desired_trade_key", "wrong-desired-trade-key"),
    ],
)
def test_wrong_approval_lineage_blocks_target_choice_conversion(
    field_name: str,
    bad_value: str,
) -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )
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
            routing.convert_target_choice_to_child_intent_with_approval(
                choice.target_choice_id,
                approval_id=approval.approval_id,
                consumed_by="automation-operator",
            )
        )

    assert exc.value.reason_code == "routing_automation_approval_lineage_stale"
    _assert_counts_unchanged(session_factory, before)
    model = _assert_approval_unconsumed(
        session_factory,
        approval.approval_id,
        status=RoutingAutomationApprovalStatus.STALE_LINEAGE,
    )
    assert "routing_automation_approval_lineage_stale" in (model.reason_codes_json or [])
    assert dict(model.provenance_json or {}).get("approval_lineage_stale") is True
    assert dict(model.provenance_json or {}).get("action_executed") is False


def test_approval_gated_target_choice_conversion_api_returns_child_intent_and_consumed_approval() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key, approval = (
        _accepted_choice_and_conversion_approval(session_factory)
    )

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routing-automation/approvals/{approval.approval_id}/convert-target-choice",
                json={
                    "target_choice_id": choice.target_choice_id,
                    "actor": "api-operator",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["approval"]["status"] == "consumed"
    assert payload["approval"]["intent_id"] == payload["intent_id"]
    assert payload["conversion"]["child_intent_created"] is True
    assert payload["prepared_order_created"] is False
    assert payload["readiness_assessment_created"] is False
    assert payload["submitted_order_created"] is False
    assert _counts(session_factory)["child_intents"] == 1
    assert _counts(session_factory)["readiness_evaluations"] == 0
    assert _counts(session_factory)["submitted_orders"] == 0
