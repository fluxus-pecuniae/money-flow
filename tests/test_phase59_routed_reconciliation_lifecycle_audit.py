from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    OrderType,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
)
from core.domain.models import RoutedOrderShapePolicyInput, SubmittedOrderLifecycleUpdate
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import _routing_assessment_with_trade
from tests.test_phase52_target_choice_conversion import _recorded_choice
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase57_routed_post_submit_lifecycle import (
    _api_get_json,
    _insert_hyperliquid_submitted_order,
)


def _api_post_json(execution, path: str) -> dict[str, object]:
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        with TestClient(app) as client:
            response = client.post(path)
    finally:
        app.dependency_overrides.pop(get_execution_service, None)
    assert response.status_code == 200
    return response.json()


def _install_reconcile_update(adapter, *, raw_payload: dict[str, object] | None = None) -> None:
    async def reconcile_submitted_order(submitted):
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted.submitted_order_id,
            venue=submitted.venue,
            venue_account_ref_id=submitted.venue_account_ref_id,
            exchange_order_id=submitted.exchange_order_id,
            status=SubmittedOrderStatus.ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_open",
            original_quantity=submitted.original_quantity,
            remaining_quantity=submitted.remaining_quantity,
            filled_quantity=submitted.filled_quantity,
            average_fill_price=submitted.average_fill_price,
            last_fill_at=submitted.last_fill_at,
            acknowledged_at=submitted.acknowledged_at,
            status_reason_code="reconciliation_open",
            status_message="Submitted order remains open on the selected venue account.",
            reason_codes=["reconciliation_open"],
            cancelable_in_principle=True,
            amendable_in_principle=submitted.order_type == OrderType.LIMIT,
            raw_payload=raw_payload
            or {
                "venue_reconciliation": {
                    "source": "phase59_test_adapter",
                    "status": "open",
                }
            },
            observed_at=datetime.now(UTC),
        )

    adapter.reconcile_submitted_order = reconcile_submitted_order


def _execution_record_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _submit_second_binding_routed_order(session_factory):
    routing, _initial_assessment, desired_trade_key, context = _routing_assessment_with_trade(
        session_factory
    )
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="phase59-secondary",
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    selected_candidate = next(
        candidate for candidate in assessment.candidates if candidate.binding_key == second_binding_key
    )
    other_candidate = next(
        candidate for candidate in assessment.candidates if candidate.binding_key != second_binding_key
    )
    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=second_binding_key,
        )
    )
    assert choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    conversion = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    assert conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    return execution, adapter, assessment, choice, submitted, selected_candidate, other_candidate


def test_routed_reconciliation_and_lifecycle_events_expose_selected_route_context() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, assessment, choice, submitted, selected_candidate, other_candidate = (
        _submit_second_binding_routed_order(session_factory)
    )
    _install_reconcile_update(adapter)
    before_counts = _execution_record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile",
    )
    events = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events",
    )

    context = reconciled["routed_lifecycle_context"]
    assert reconciled["routed_origin"] is True
    assert context["routing_assessment_id"] == assessment.assessment_id
    assert context["routing_target_choice_id"] == choice.target_choice_id
    assert context["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert context["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert context["selected_venue"] == selected_candidate.venue
    assert context["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert context["same_target_only"] is True
    assert context["same_account_only"] is True
    assert context["same_venue_only"] is True
    assert context["auto_submit"] is False
    assert context["fanout_created"] is False
    assert context["scoring_created"] is False
    assert context["target_reselection"] is False
    assert "route_plan" not in reconciled
    assert "allocation" not in reconciled
    assert "score" not in reconciled
    assert reconciled["raw_payload"]["venue_reconciliation"]["status"] == "open"
    assert reconciled["raw_payload"]["routed_submission"]["routing_assessment_id"] == (
        assessment.assessment_id
    )

    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    event_context = reconciliation_event["routed_lifecycle_context"]
    assert reconciliation_event["routed_origin"] is True
    assert event_context["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert event_context["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert event_context["selected_venue"] == selected_candidate.venue
    assert event_context["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert event_context["routed_order_shape_policy"]["phase"] == "phase_5_8"
    assert event_context["routed_order_shape_policy"]["order_type"] == OrderType.MARKET.value

    assert _execution_record_counts(session_factory) == before_counts
    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.venue_account_ref_id == other_candidate.venue_account_ref_id
                )
            )
            == 0
        )


def test_routed_reconciliation_payload_collision_cannot_overwrite_platform_lineage() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, assessment, choice, submitted, selected_candidate, other_candidate = (
        _submit_second_binding_routed_order(session_factory)
    )
    original_routed_payload = dict(submitted.raw_payload["routed_submission"])
    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "source": "venue_collision",
                "routing_assessment_id": "wrong-assessment",
                "routing_target_choice_id": "wrong-choice",
                "selected_binding_ref_id": "wrong-binding",
                "selected_venue_account_ref_id": "wrong-account",
                "selected_venue": "wrong-venue",
                "selected_exchange_symbol": "WRONG",
            },
            "venue_reconciliation": {
                "source": "phase591_collision_adapter",
                "status": "open",
            },
        },
    )
    before_counts = _execution_record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile",
    )
    events = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events",
    )

    raw_routed_payload = reconciled["raw_payload"]["routed_submission"]
    assert raw_routed_payload == original_routed_payload
    assert raw_routed_payload["routing_assessment_id"] == assessment.assessment_id
    assert raw_routed_payload["routing_target_choice_id"] == choice.target_choice_id
    assert raw_routed_payload["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert raw_routed_payload["selected_binding_key"] == selected_candidate.binding_key
    assert raw_routed_payload["selected_venue_account_ref_id"] == (
        selected_candidate.venue_account_ref_id
    )
    assert raw_routed_payload["selected_venue_account_key"] == (
        selected_candidate.venue_account_key
    )
    assert raw_routed_payload["selected_venue"] == selected_candidate.venue
    assert raw_routed_payload["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert raw_routed_payload["routed_order_shape_policy"]["phase"] == "phase_5_8"
    assert raw_routed_payload["routed_order_shape_policy"]["order_type"] == OrderType.MARKET.value
    assert raw_routed_payload.get("source") != "venue_collision"
    assert reconciled["raw_payload"]["venue_reconciliation"]["source"] == (
        "phase591_collision_adapter"
    )

    context = reconciled["routed_lifecycle_context"]
    assert reconciled["routed_origin"] is True
    assert context["routing_assessment_id"] == assessment.assessment_id
    assert context["routing_target_choice_id"] == choice.target_choice_id
    assert context["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert context["selected_binding_key"] == selected_candidate.binding_key
    assert context["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert context["selected_venue_account_key"] == selected_candidate.venue_account_key
    assert context["selected_venue"] == selected_candidate.venue
    assert context["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert context["routed_order_shape_policy"]["phase"] == "phase_5_8"
    assert context["same_target_only"] is True
    assert context["same_account_only"] is True
    assert context["same_venue_only"] is True
    assert context["auto_submit"] is False
    assert context["fanout_created"] is False
    assert context["target_reselection"] is False
    assert "route_plan" not in reconciled
    assert "allocation" not in reconciled
    assert "score" not in reconciled

    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    event_context = reconciliation_event["routed_lifecycle_context"]
    assert reconciliation_event["routed_origin"] is True
    assert reconciliation_event["raw_payload"]["routed_submission"]["source"] == (
        "venue_collision"
    )
    assert event_context["routing_assessment_id"] == assessment.assessment_id
    assert event_context["routing_target_choice_id"] == choice.target_choice_id
    assert event_context["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert event_context["selected_venue_account_ref_id"] == (
        selected_candidate.venue_account_ref_id
    )
    assert event_context["selected_venue"] == selected_candidate.venue
    assert event_context["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert event_context["routed_order_shape_policy"]["phase"] == "phase_5_8"

    assert _execution_record_counts(session_factory) == before_counts
    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.venue_account_ref_id == other_candidate.venue_account_ref_id
                )
            )
            == 0
        )


def test_non_routed_reconciliation_and_events_do_not_fabricate_route_context() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase59-normal",
        raw_payload={"adapter_submit_called": True},
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    _install_reconcile_update(adapter)
    before_counts = _execution_record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted_order_id}/reconcile",
    )
    events = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted_order_id}/events")

    assert reconciled["routed_origin"] is False
    assert reconciled["routed_lineage"] is None
    assert reconciled["routed_lifecycle_context"] is None
    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    assert reconciliation_event["routed_origin"] is False
    assert reconciliation_event["routed_lifecycle_context"] is None
    assert _execution_record_counts(session_factory) == before_counts


def test_non_routed_reconciliation_payload_collision_cannot_create_platform_lineage() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase592-non-routed-collision",
        raw_payload={"adapter_submit_called": True},
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "source": "venue_collision",
                "routing_assessment_id": "fake-assessment",
                "routing_target_choice_id": "fake-choice",
            },
            "venue_reconciliation": {
                "source": "phase592_collision_adapter",
                "status": "open",
            },
        },
    )
    before_counts = _execution_record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted_order_id}/reconcile",
    )
    events = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted_order_id}/events")

    assert reconciled["routed_origin"] is False
    assert reconciled["routed_lineage"] is None
    assert reconciled["routed_lifecycle_context"] is None
    assert "routed_submission" not in reconciled["raw_payload"]
    assert reconciled["raw_payload"]["venue_reconciliation"]["source"] == (
        "phase592_collision_adapter"
    )
    assert "route_plan" not in reconciled
    assert "allocation" not in reconciled
    assert "score" not in reconciled

    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    assert reconciliation_event["routed_origin"] is False
    assert reconciliation_event["routed_lifecycle_context"] is None
    assert reconciliation_event["raw_payload"]["routed_submission"]["source"] == (
        "venue_collision"
    )
    assert reconciliation_event["raw_payload"]["venue_reconciliation"]["source"] == (
        "phase592_collision_adapter"
    )
    assert _execution_record_counts(session_factory) == before_counts


def test_malformed_routed_reconciliation_and_events_remain_bounded() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase59-malformed-routed",
        raw_payload={
            "routed_submission": {
                "routing_assessment_id": 59,
                "routing_target_choice_id": "choice-phase59",
                "selected_venue_account_ref_id": "venue-account-hl-phase59",
                "auto_submit": "false",
                "explicit_action_required": "true",
                "routed_order_shape_policy": "not-a-policy-payload",
            }
        },
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    _install_reconcile_update(adapter)
    before_counts = _execution_record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted_order_id}/reconcile",
    )
    events = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted_order_id}/events")

    for payload in (
        reconciled,
        next(event for event in events if event["event_type"] == "reconciliation_open"),
    ):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        assert context["route_lineage_malformed"] is True
        assert "routing_assessment_id" in context["malformed_lineage_fields"]
        assert "auto_submit" in context["malformed_lineage_fields"]
        assert "explicit_action_required" in context["malformed_lineage_fields"]
        assert "routed_order_shape_policy" in context["malformed_lineage_fields"]
        assert "desired_trade_key" in context["missing_lineage_fields"]
        assert "routed_lineage_malformed" in context["boundary_reason_codes"]
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True

    assert _execution_record_counts(session_factory) == before_counts


def test_phase58_malformed_limit_reason_truth_remains_intact() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            order_shape_policy=RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("NaN"),
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "malformed_limit_price" in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    assert "limit_price_explicit" not in result.reason_codes
    assert "limit_price_explicit" not in result.provenance["routed_order_shape_policy"]["reason_codes"]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0
