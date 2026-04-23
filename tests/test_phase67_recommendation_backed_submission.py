from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    ExecutionReadinessOutcome,
    OrderType,
    RoutingTargetChoiceConversionStatus,
    SubmittedOrderStatus,
)
from db.models import (
    OrderIntentSubmissionLeaseModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from services.execution.service import SubmissionBlockedError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _mutate_ready_candidate_quote_observed_at,
)
from tests.test_phase64_recommendation_backed_readiness import (
    _mutate_child_intent,
    _recommendation_backed_child_intent,
)


client = TestClient(app)


def _submitted_order_count(session_factory) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(SubmittedOrderModel))


def _recommendation_backed_submission_context(
    session_factory,
    *,
    routed_submission_enabled: bool = True,
    live_submission_enabled: bool = True,
):
    routing, audit, recommendation, choice, desired_trade_key, conversion = (
        _recommendation_backed_child_intent(session_factory)
    )
    assert conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    execution, adapter = _build_execution(
        session_factory,
        routed_submission_enabled=routed_submission_enabled,
        live_submission_enabled=live_submission_enabled,
    )
    return routing, audit, recommendation, choice, desired_trade_key, conversion, execution, adapter


def _submit_recommendation_backed_child_intent(
    session_factory,
    *,
    routed_submission_enabled: bool = True,
    live_submission_enabled: bool = True,
):
    context = _recommendation_backed_submission_context(
        session_factory,
        routed_submission_enabled=routed_submission_enabled,
        live_submission_enabled=live_submission_enabled,
    )
    _routing, _audit, _recommendation, _choice, _desired_trade_key, conversion, execution, adapter = (
        context
    )
    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    return (*context, submitted)


def test_recommendation_backed_child_intent_submits_through_existing_gated_submit_path() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        audit,
        recommendation,
        choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)

    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    routed_payload = submitted.raw_payload["routed_submission"]
    assert submitted.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert submitted.intent_id == conversion.intent_id
    assert routed_payload["source"] == "routing_target_recommendation"
    assert routed_payload["intent_id"] == conversion.intent_id
    assert routed_payload["readiness_evaluation_id"] == readiness.readiness_evaluation_id
    assert routed_payload["routing_assessment_id"] == audit.routing_assessment_id
    assert routed_payload["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert routed_payload["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert routed_payload["routing_target_choice_id"] == choice.target_choice_id
    assert routed_payload["recommendation_policy_name"] == recommendation.policy_name
    assert routed_payload["selected_binding_ref_id"] == choice.selected_binding_ref_id
    assert routed_payload["selected_venue_account_ref_id"] == (
        choice.selected_venue_account_ref_id
    )
    assert routed_payload["selected_venue"] == choice.selected_venue
    assert routed_payload["selected_exchange_symbol"] == conversion.selected_exchange_symbol
    assert routed_payload["explicit_submit_action"] is True
    assert routed_payload["same_target_only"] is True
    assert routed_payload["same_account_only"] is True
    assert routed_payload["same_venue_only"] is True
    assert routed_payload["auto_submit"] is False
    assert routed_payload["fanout_created"] is False
    assert routed_payload["allocation_created"] is False
    assert routed_payload["scoring_created"] is False
    assert routed_payload["route_executor_created"] is False
    assert routed_payload["target_reselection"] is False
    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 1

    with session_factory() as session:
        recommendation_model = session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation.routing_target_recommendation_id
            )
        )
        audit_model = session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.route_readiness_audit_id
                == audit.route_readiness_audit_id
            )
        )
        assert recommendation_model is not None
        assert audit_model is not None
        assert recommendation_model.submitted_order_created is True
        assert audit_model.submitted_order_created is True
        assert recommendation_model.provenance_json["submitted_order_id"] == (
            submitted.submitted_order_id
        )
        assert audit_model.provenance_json["submitted_order_id"] == submitted.submitted_order_id

    duplicate = asyncio.run(execution.submit_prepared_intent(intent))
    assert duplicate.submitted_order_id == submitted.submitted_order_id
    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 1


def test_concurrent_explicit_submit_for_same_routed_child_intent_calls_adapter_once() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))

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
        first_submit = asyncio.create_task(execution.submit_prepared_intent(intent))
        await started.wait()

        with pytest.raises(SubmissionBlockedError) as exc:
            await execution.submit_prepared_intent(intent)

        assert "submission_in_progress" in exc.value.readiness.reason_codes
        assert adapter_invocations == 1
        assert adapter.submit_calls == 0
        assert _submitted_order_count(session_factory) == 0

        release.set()
        submitted = await first_submit
        duplicate = await execution.submit_prepared_intent(intent)
        return submitted, duplicate, adapter_invocations

    submitted, duplicate, adapter_invocations = asyncio.run(run_concurrent_submits())

    assert submitted.submitted_order_id == duplicate.submitted_order_id
    assert adapter_invocations == 1
    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 1
    with session_factory() as session:
        lease = session.scalar(
            select(OrderIntentSubmissionLeaseModel).where(
                OrderIntentSubmissionLeaseModel.intent_id == conversion.intent_id
            )
        )
        assert lease is not None
        assert lease.status == "submitted"
        assert lease.reason_code == "submitted_order_persisted"


def test_adapter_returned_persistence_failure_marks_submission_lease_uncertain(
    monkeypatch,
) -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))

    def fail_persist(*_args, **_kwargs):
        raise RuntimeError("local submitted-order persistence failed after adapter return")

    monkeypatch.setattr(execution, "_persist_submitted_order", fail_persist)

    with pytest.raises(RuntimeError, match="persistence failed"):
        asyncio.run(execution.submit_prepared_intent(intent))

    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 0

    with session_factory() as session:
        lease = session.scalar(
            select(OrderIntentSubmissionLeaseModel).where(
                OrderIntentSubmissionLeaseModel.intent_id == conversion.intent_id
            )
        )
        assert lease is not None
        assert lease.status == "adapter_submit_persistence_unknown"
        assert lease.reason_code == "adapter_submit_returned_persistence_failed"
        assert lease.metadata_json["intent_id"] == conversion.intent_id
        assert lease.metadata_json["adapter_submit_called"] is True
        assert lease.metadata_json["adapter_submit_returned"] is True
        assert lease.metadata_json["submitted_order_persisted"] is False
        assert lease.metadata_json["requires_reconciliation"] is True
        assert lease.metadata_json["submitted_order_id"] == f"submitted-{conversion.intent_id}"
        assert lease.metadata_json["exchange_order_id"] == f"exchange-{conversion.intent_id}"
        assert lease.metadata_json["client_order_id"] == f"client-{conversion.intent_id}"
        assert lease.metadata_json["persistence_failure_class"] == "RuntimeError"
        assert "persistence failed" in lease.metadata_json["persistence_failure_message"]

        lease.expires_at = datetime.now(UTC) - timedelta(minutes=30)
        session.add(lease)
        session.commit()

    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "submission_state_uncertain" in exc.value.readiness.reason_codes
    assert "adapter_submit_persistence_unknown" in exc.value.readiness.reason_codes
    assert "manual_reconciliation_required" in exc.value.readiness.reason_codes
    assert (
        exc.value.readiness.provenance["submission_lease"]["status"]
        == "adapter_submit_persistence_unknown"
    )
    assert (
        exc.value.readiness.provenance["submission_lease"]["requires_reconciliation"]
        is True
    )
    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 0


def test_stale_pre_adapter_active_submission_lease_can_still_be_replaced() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    stale_time = datetime.now(UTC) - timedelta(minutes=30)
    with session_factory() as session:
        session.add(
            OrderIntentSubmissionLeaseModel(
                environment=execution.settings.app.environment,
                lease_id="stale-pre-adapter-lease",
                intent_id=conversion.intent_id,
                purpose="explicit_child_intent_submit",
                status="active",
                acquired_at=stale_time,
                expires_at=stale_time,
                released_at=None,
                reason_code=None,
                metadata_json={"purpose": "explicit_child_intent_submit"},
                created_at=stale_time,
                updated_at=stale_time,
            )
        )
        session.commit()

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert submitted.submitted_order_id == f"submitted-{conversion.intent_id}"
    assert adapter.submit_calls == 1
    assert _submitted_order_count(session_factory) == 1
    with session_factory() as session:
        lease = session.scalar(
            select(OrderIntentSubmissionLeaseModel).where(
                OrderIntentSubmissionLeaseModel.intent_id == conversion.intent_id
            )
        )
        assert lease is not None
        assert lease.lease_id != "stale-pre-adapter-lease"
        assert lease.status == "submitted"
        assert lease.reason_code == "submitted_order_persisted"
        assert lease.metadata_json["previous_lease_id"] == "stale-pre-adapter-lease"
        assert lease.metadata_json["acquire_reason"] == "stale_submission_lease_replaced"


@pytest.mark.parametrize(
    ("routed_submission_enabled", "live_submission_enabled", "expected_reason"),
    [
        (False, True, "routed_submission_deferred"),
        (True, False, "phase_live_submit_deferred"),
    ],
)
def test_recommendation_backed_submission_requires_existing_live_and_routed_gates(
    routed_submission_enabled: bool,
    live_submission_enabled: bool,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(
        session_factory,
        routed_submission_enabled=routed_submission_enabled,
        live_submission_enabled=live_submission_enabled,
    )

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert expected_reason in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _submitted_order_count(session_factory) == 0


def test_recommendation_backed_submission_blocks_stale_quote_before_adapter_submit() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(minutes=10)).isoformat(),
    )

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "quote_stale_at_readiness" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _submitted_order_count(session_factory) == 0


def test_recommendation_backed_submission_blocks_recommendation_lineage_drift_before_adapter_submit() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    with session_factory() as session:
        recommendation_model = session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation.routing_target_recommendation_id
            )
        )
        assert recommendation_model is not None
        recommendation_model.recommended_exchange_symbol = "STALE-EXCHANGE-SYMBOL"
        session.commit()

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "recommendation_exchange_symbol_mismatch" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _submitted_order_count(session_factory) == 0


def test_recommendation_backed_submission_blocks_order_shape_policy_drift_before_adapter_submit() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    _mutate_child_intent(
        session_factory,
        conversion.intent_id,
        order_type=OrderType.LIMIT,
    )

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "routed_order_type_policy_mismatch" in exc.value.readiness.reason_codes
    assert "routed_order_shape_policy_intent_mismatch" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _submitted_order_count(session_factory) == 0


def test_api_recommendation_backed_submit_exposes_typed_recommendation_lineage() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
        audit,
        recommendation,
        choice,
        _desired_trade_key,
        conversion,
        execution,
        adapter,
    ) = _recommendation_backed_submission_context(session_factory)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        with TestClient(app) as api_client:
            response = api_client.post(f"/api/v1/child-intents/{conversion.intent_id}/submit")
    finally:
        app.dependency_overrides.pop(get_execution_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["routed_origin"] is True
    assert payload["routed_lineage"]["route_readiness_audit_id"] == (
        audit.route_readiness_audit_id
    )
    assert payload["routed_lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert payload["routed_lineage"]["routing_target_choice_id"] == choice.target_choice_id
    assert payload["routed_lineage"]["recommendation_policy_name"] == recommendation.policy_name
    assert payload["routed_lineage"]["intent_id"] == conversion.intent_id
    assert payload["routed_lineage"]["allocation_created"] is False
    assert payload["routed_lineage"]["route_executor_created"] is False
    assert payload["routed_lineage"]["submitted_order_created"] is True
    assert adapter.submit_calls == 1
