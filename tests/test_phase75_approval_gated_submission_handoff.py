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
    SubmittedOrderStatus,
)
from core.domain.models import RoutingAutomationPlanStep
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    OrderIntentSubmissionLeaseModel,
    RoutingAutomationApprovalModel,
    SubmittedOrderModel,
)
from services.exchange.base import VenueAdapterError
from services.execution.service import SubmissionBlockedError, SubmissionFailedError
from services.routing.service import RoutingAssessmentError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _mutate_ready_candidate_quote_observed_at,
)
from tests.test_phase67_recommendation_backed_submission import (
    _recommendation_backed_submission_context,
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


def _submission_handoff_context(session_factory):
    routing, audit, recommendation, choice, desired_trade_key, conversion, execution, adapter = (
        _recommendation_backed_submission_context(session_factory)
    )
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    approval = asyncio.run(
        routing.create_routing_automation_approval(
            desired_trade_key,
            action_name=RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value,
            approved_by="submit-operator",
        )
    )
    return (
        routing,
        audit,
        recommendation,
        choice,
        desired_trade_key,
        conversion,
        readiness,
        approval,
        execution,
        adapter,
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


def _assert_no_submission(session_factory, adapter) -> None:
    assert _counts(session_factory)["submitted_orders"] == 0
    assert adapter.submit_calls == 0


def test_approval_gated_submission_handoff_consumes_approval_and_submits_once() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        recommendation,
        choice,
        desired_trade_key,
        conversion,
        readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    before = _counts(session_factory)

    result = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=approval.approval_id,
            consumed_by="handoff-operator",
            execution_service=execution,
        )
    )
    after = _counts(session_factory)

    assert result.intent_id == conversion.intent_id
    assert result.readiness_evaluation_id == readiness.readiness_evaluation_id
    assert result.submitted_order.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert result.submitted_order.intent_id == conversion.intent_id
    assert result.submitted_order_created is True
    assert result.submitted_order_reused is False
    assert result.exchange_submit_called is True
    assert result.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert result.approval.submitted_order_id == result.submitted_order_id
    assert result.approval.provenance["approval_gated_submitted_order_handoff"] is True
    assert result.approval.provenance["auto_submit"] is False
    assert result.approval.provenance["route_executor"] is False
    assert result.boundary_flags["fanout"] is False
    assert result.boundary_flags["cbbo"] is False
    assert result.boundary_flags["ranking"] is False
    assert result.boundary_flags["scoring"] is False
    assert result.boundary_flags["target_reselection"] is False
    assert result.boundary_flags["route_executor"] is False
    assert result.boundary_flags["auto_submit"] is False

    routed_payload = result.submitted_order.raw_payload["routed_submission"]
    assert routed_payload["readiness_evaluation_id"] == readiness.readiness_evaluation_id
    assert routed_payload["routing_assessment_id"] == audit.routing_assessment_id
    assert routed_payload["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert routed_payload["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert routed_payload["routing_target_choice_id"] == choice.target_choice_id
    assert routed_payload["intent_id"] == conversion.intent_id
    assert routed_payload["selected_venue"] == choice.selected_venue
    assert routed_payload["selected_exchange_symbol"] == conversion.selected_exchange_symbol
    assert routed_payload["explicit_submit_action"] is True
    assert routed_payload["auto_submit"] is False
    assert routed_payload["fanout_created"] is False
    assert routed_payload["scoring_created"] is False
    assert routed_payload["route_executor_created"] is False
    assert routed_payload["target_reselection"] is False

    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"] + 1
    assert adapter.submit_calls == 1

    plan = asyncio.run(
        routing.plan_routing_automation_for_desired_trade(
            desired_trade_key,
            policy=routing.routing_automation_policy(mode=RoutingAutomationMode.APPROVAL_REQUIRED),
        )
    )
    assert plan.approval_gate_states["submitted_order_handoff"]["status"] == (
        "already_satisfied"
    )
    assert plan.approval_gate_states["submitted_order_handoff"]["approval_id"] == (
        approval.approval_id
    )


def test_approval_gated_submission_handoff_is_idempotent_for_same_approval() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)

    first = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=approval.approval_id,
            consumed_by="handoff-operator",
            execution_service=execution,
        )
    )
    before_repeat = _counts(session_factory)
    second = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=approval.approval_id,
            consumed_by="handoff-operator",
            execution_service=execution,
        )
    )
    after_repeat = _counts(session_factory)

    assert second.submitted_order_id == first.submitted_order_id
    assert second.submitted_order_created is False
    assert second.submitted_order_reused is True
    assert second.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert second.approval.consumed_at == first.approval.consumed_at
    assert adapter.submit_calls == 1
    assert after_repeat == before_repeat


def test_submitted_order_persistence_then_approval_consumption_failure_is_bounded(
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
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    original_consume = routing._consume_submitted_order_handoff_approval

    def fail_consumption(*args, **kwargs):
        raise RuntimeError("forced approval consumption failure after submit")

    monkeypatch.setattr(
        routing,
        "_consume_submitted_order_handoff_approval",
        fail_consumption,
    )
    before = _counts(session_factory)

    with pytest.raises(RuntimeError, match="forced approval consumption failure"):
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
    after = _counts(session_factory)

    assert adapter.submit_calls == 1
    assert after["child_intents"] == before["child_intents"]
    assert after["readiness_evaluations"] == before["readiness_evaluations"]
    assert after["submitted_orders"] == before["submitted_orders"] + 1

    with session_factory() as session:
        submitted_order = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.intent_id == conversion.intent_id
            )
        )
        assert submitted_order is not None
        stored = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert stored is not None
        assert stored.status == RoutingAutomationApprovalStatus.CONSUMPTION_PENDING.value
        assert stored.submitted_order_id == submitted_order.submitted_order_id
        assert "submitted_order_handoff_consumption_failed" in stored.reason_codes_json
        assert (
            "submitted_order_created_approval_consumption_pending"
            in stored.reason_codes_json
        )
        assert (
            "approval_consumption_failed_after_submitted_order"
            in stored.reason_codes_json
        )
        assert "manual_approval_reconciliation_required" in stored.reason_codes_json
        assert stored.provenance_json["approval_consumed"] is False
        assert stored.provenance_json["approval_consumption_pending"] is True
        assert (
            stored.provenance_json[
                "submitted_order_created_approval_consumption_pending"
            ]
            is True
        )
        assert stored.provenance_json["submitted_order_id"] == (
            submitted_order.submitted_order_id
        )
        assert stored.provenance_json["intent_id"] == conversion.intent_id
        assert stored.provenance_json["manual_approval_reconciliation_required"] is True
        assert stored.provenance_json["route_executor"] is False
        assert stored.provenance_json["auto_submit"] is False

    monkeypatch.setattr(
        routing,
        "_consume_submitted_order_handoff_approval",
        original_consume,
    )


def test_repeat_after_approval_consumption_failure_reuses_order_and_completes_consumption(
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
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    original_consume = routing._consume_submitted_order_handoff_approval

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
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
    assert adapter.submit_calls == 1
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
            consumed_by="handoff-operator",
            execution_service=execution,
        )
    )
    after_repeat = _counts(session_factory)

    assert repeat.submitted_order_created is False
    assert repeat.submitted_order_reused is True
    assert repeat.approval.status == RoutingAutomationApprovalStatus.CONSUMED
    assert repeat.approval.submitted_order_id == repeat.submitted_order_id
    assert repeat.approval.provenance["approval_gated_submitted_order_handoff"] is True
    assert repeat.approval.provenance["submitted_order_reused"] is True
    assert adapter.submit_calls == 1
    assert after_repeat == before_repeat


def test_blocked_readiness_does_not_force_approval_gated_submission() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    ready_candidate = audit.candidates[0]
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=ready_candidate.binding_key,
    )

    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )

    assert "quote_stale_at_readiness" in exc.value.readiness.reason_codes
    stored = _approval_model(session_factory, approval.approval_id)
    assert stored.status == RoutingAutomationApprovalStatus.ACTIVE.value
    assert stored.submitted_order_id is None
    assert "quote_stale_at_readiness" in stored.reason_codes_json
    assert stored.provenance_json["approval_consumed"] is False
    assert stored.provenance_json["submitted_order_handoff_completed"] is False
    _assert_no_submission(session_factory, adapter)


@pytest.mark.parametrize(
    ("routed_submission_enabled", "live_submission_enabled", "expected_reason"),
    [
        (False, True, "routed_submission_deferred"),
        (True, False, "phase_live_submit_deferred"),
    ],
)
def test_submit_gates_remain_authoritative_for_approval_gated_submission(
    routed_submission_enabled: bool,
    live_submission_enabled: bool,
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
        _readiness,
        approval,
        _enabled_execution,
        enabled_adapter,
    ) = _submission_handoff_context(session_factory)
    disabled_execution, disabled_adapter = _build_execution(
        session_factory,
        routed_submission_enabled=routed_submission_enabled,
        live_submission_enabled=live_submission_enabled,
    )

    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=disabled_execution,
            )
        )

    assert expected_reason in exc.value.readiness.reason_codes
    assert enabled_adapter.submit_calls == 0
    assert disabled_adapter.submit_calls == 0
    assert _counts(session_factory)["submitted_orders"] == 0
    stored = _approval_model(session_factory, approval.approval_id)
    assert stored.status == RoutingAutomationApprovalStatus.ACTIVE.value
    assert stored.submitted_order_id is None


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        ({"action_name": RoutingAutomationApprovalAction.PREVIEW_READINESS.value}, "routing_automation_approval_wrong_action"),
        ({"intent_id": "wrong-intent"}, "routing_automation_approval_wrong_child_intent"),
        ({"readiness_evaluation_id": "wrong-readiness"}, "routing_automation_approval_lineage_stale"),
        ({"routing_target_choice_id": "wrong-choice"}, "routing_automation_approval_lineage_stale"),
        ({"routing_target_recommendation_id": "wrong-recommendation"}, "routing_automation_approval_lineage_stale"),
        ({"route_readiness_audit_id": "wrong-audit"}, "routing_automation_approval_lineage_stale"),
        ({"desired_trade_key": "wrong-desired-trade"}, "routing_automation_approval_lineage_stale"),
    ],
)
def test_invalid_approval_lineage_cannot_authorize_submission_handoff(
    mutation: dict[str, str],
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
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        for field_name, value in mutation.items():
            setattr(model, field_name, value)
        session.commit()

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )

    assert exc.value.reason_code == expected_reason
    stored = _approval_model(session_factory, approval.approval_id)
    assert stored.status != RoutingAutomationApprovalStatus.CONSUMED.value
    assert stored.submitted_order_id is None
    _assert_no_submission(session_factory, adapter)


def test_expired_revoked_and_consumed_approvals_cannot_authorize_submission_handoff() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingAutomationApprovalModel).where(
                RoutingAutomationApprovalModel.approval_id == approval.approval_id
            )
        )
        assert model is not None
        model.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()

    with pytest.raises(RoutingAssessmentError) as expired:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
    assert expired.value.reason_code == "routing_automation_approval_expired"
    _assert_no_submission(session_factory, adapter)

    fresh = asyncio.run(
        routing.create_routing_automation_approval(
            _desired_trade_key,
            action_name=RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value,
            approved_by="submit-operator",
        )
    )
    asyncio.run(
        routing.revoke_routing_automation_approval(
            fresh.approval_id,
            revoked_by="submit-operator",
            reason="operator changed mind",
        )
    )
    with pytest.raises(RoutingAssessmentError) as revoked:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=fresh.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
    assert revoked.value.reason_code == "routing_automation_approval_revoked"
    _assert_no_submission(session_factory, adapter)

    valid = asyncio.run(
        routing.create_routing_automation_approval(
            _desired_trade_key,
            action_name=RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF.value,
            approved_by="submit-operator",
        )
    )
    result = asyncio.run(
        routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=valid.approval_id,
            consumed_by="handoff-operator",
            execution_service=execution,
        )
    )
    with session_factory() as session:
        source = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == conversion.intent_id)
        )
        assert source is not None
        clone = OrderIntentModel(
            environment=source.environment,
            intent_id=f"{conversion.intent_id}-other",
            decision_id=source.decision_id,
            action=source.action,
            mandate_desired_trade_ref_id=source.mandate_desired_trade_ref_id,
            desired_trade_key=source.desired_trade_key,
            sleeve_id=source.sleeve_id,
            component_key=source.component_key,
            client_ref_id=source.client_ref_id,
            strategy_mandate_ref_id=source.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=source.mandate_account_binding_ref_id,
            binding_key=source.binding_key,
            venue_account_ref_id=source.venue_account_ref_id,
            instrument_key=source.instrument_key,
            instrument_ref_id=source.instrument_ref_id,
            symbol_id=source.symbol_id,
            symbol=source.symbol,
            side=source.side,
            order_type=source.order_type,
            quantity=source.quantity,
            limit_price=source.limit_price,
            reduce_only=source.reduce_only,
            ttl_seconds=source.ttl_seconds,
            status=source.status,
            idempotency_key=f"{source.idempotency_key}-other",
            provenance=dict(source.provenance or {}),
            created_at=datetime.now(UTC),
        )
        session.add(clone)
        session.commit()

    with pytest.raises(RoutingAssessmentError) as consumed:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                f"{conversion.intent_id}-other",
                approval_id=valid.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
    assert consumed.value.reason_code == "routing_automation_approval_consumed_for_different_action"
    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 1
    assert result.submitted_order_id is not None


@pytest.mark.parametrize(
    ("step_status", "step_reason", "expected_reason"),
    [
        (RoutingAutomationStepStatus.DISABLED, "forced_submit_disabled_for_test", "routing_automation_approval_action_not_available"),
        (RoutingAutomationStepStatus.BLOCKED, "forced_submit_blocked_for_test", "routing_automation_approval_action_blocked"),
        (RoutingAutomationStepStatus.DEFERRED, "forced_submit_deferred_for_test", "routing_automation_approval_action_not_available"),
        (RoutingAutomationStepStatus.ALREADY_SATISFIED, "forced_submit_already_satisfied_for_test", "routing_automation_approval_action_already_satisfied"),
        (RoutingAutomationStepStatus.DRY_RUN_ONLY, "forced_submit_dry_run_only_for_test", "routing_automation_approval_action_dry_run_only"),
        (RoutingAutomationStepStatus.MANUAL_ONLY, "forced_submit_manual_only_for_test", "routing_automation_approval_action_manual_only"),
    ],
)
def test_non_executable_step_statuses_block_submission_handoff(
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
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)
    original_step_for_action = routing._routing_automation_step_for_action

    def forced_submit_step(plan, action):
        if action != RoutingAutomationApprovalAction.SUBMITTED_ORDER_HANDOFF:
            return original_step_for_action(plan, action)
        base_step = original_step_for_action(plan, action)
        return RoutingAutomationPlanStep(
            name=action.value,
            status=step_status,
            artifact_id=base_step.artifact_id,
            would_create_artifact_type="SubmittedOrder",
            reason_codes=[step_reason],
            blocked=step_status == RoutingAutomationStepStatus.BLOCKED,
            lineage=dict(base_step.lineage),
        )

    monkeypatch.setattr(routing, "_routing_automation_step_for_action", forced_submit_step)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )

    assert exc.value.reason_code == expected_reason
    _assert_no_submission(session_factory, adapter)
    stored = _approval_model(session_factory, approval.approval_id)
    assert stored.status == RoutingAutomationApprovalStatus.ACTIVE.value
    assert stored.submitted_order_id is None


def test_concurrent_approval_gated_submission_uses_existing_submit_lease() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)

    async def run_concurrent_submits():
        started = asyncio.Event()
        release = asyncio.Event()
        original_submit_order = adapter.submit_order
        adapter_invocations = 0

        async def slow_submit_order(submit_intent):
            nonlocal adapter_invocations
            adapter_invocations += 1
            started.set()
            await release.wait()
            return await original_submit_order(submit_intent)

        adapter.submit_order = slow_submit_order
        first_submit = asyncio.create_task(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )
        await started.wait()

        with pytest.raises(SubmissionBlockedError) as exc:
            await routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )

        assert "submission_state_uncertain" in exc.value.readiness.reason_codes
        assert "adapter_submit_may_have_started" in exc.value.readiness.reason_codes
        assert "manual_reconciliation_required" in exc.value.readiness.reason_codes
        assert adapter_invocations == 1
        assert adapter.submit_calls == 0
        assert _counts(session_factory)["submitted_orders"] == 0

        release.set()
        first_result = await first_submit
        repeat_result = await routing.submit_child_intent_with_approval(
            conversion.intent_id,
            approval_id=approval.approval_id,
            consumed_by="handoff-operator",
            execution_service=execution,
        )
        return first_result, repeat_result, adapter_invocations

    first, repeat, adapter_invocations = asyncio.run(run_concurrent_submits())

    assert first.submitted_order_id == repeat.submitted_order_id
    assert adapter_invocations == 1
    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 1
    assert repeat.submitted_order_reused is True
    with session_factory() as session:
        lease = session.scalar(
            select(OrderIntentSubmissionLeaseModel).where(
                OrderIntentSubmissionLeaseModel.intent_id == conversion.intent_id
            )
        )
        assert lease is not None
        assert lease.status == "submitted"
        assert lease.reason_code == "submitted_order_persisted"


def test_submit_uncertainty_keeps_approval_unconsumed_and_blocks_retry() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
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
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )

    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 0
    stored = _approval_model(session_factory, approval.approval_id)
    assert stored.status == RoutingAutomationApprovalStatus.ACTIVE.value
    assert stored.submitted_order_id is None
    assert stored.provenance_json["approval_consumed"] is False
    assert stored.provenance_json["submission_uncertain"] is True
    assert stored.provenance_json["manual_reconciliation_required"] is True
    assert "submission_state_uncertain" in stored.reason_codes_json
    assert "manual_reconciliation_required" in stored.reason_codes_json

    with session_factory() as session:
        lease = session.scalar(
            select(OrderIntentSubmissionLeaseModel).where(
                OrderIntentSubmissionLeaseModel.intent_id == conversion.intent_id
            )
        )
        assert lease is not None
        assert lease.status == "adapter_submit_may_have_started"
        lease.expires_at = datetime.now(UTC) - timedelta(minutes=30)
        session.add(lease)
        session.commit()

    with pytest.raises(SubmissionBlockedError) as blocked:
        asyncio.run(
            routing.submit_child_intent_with_approval(
                conversion.intent_id,
                approval_id=approval.approval_id,
                consumed_by="handoff-operator",
                execution_service=execution,
            )
        )

    assert "submission_state_uncertain" in blocked.value.readiness.reason_codes
    assert "manual_reconciliation_required" in blocked.value.readiness.reason_codes
    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 0


def test_approval_gated_submission_handoff_api_returns_consumed_approval_and_submission() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        _readiness,
        approval,
        execution,
        adapter,
    ) = _submission_handoff_context(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routing-automation/approvals/{approval.approval_id}/submit",
                json={
                    "intent_id": conversion.intent_id,
                    "actor": "api-handoff-operator",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["approval"]["status"] == "consumed"
    assert payload["approval"]["submitted_order_id"] == payload["submitted_order_id"]
    assert payload["submitted_order"]["intent_id"] == conversion.intent_id
    assert payload["submitted_order_created"] is True
    assert payload["submitted_order_reused"] is False
    assert payload["exchange_submit_called"] is True
    assert payload["auto_submit"] is False
    assert payload["route_executor_used"] is False
    assert adapter.submit_calls == 1
    assert _counts(session_factory)["submitted_orders"] == 1
