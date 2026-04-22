from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from core.domain.enums import (
    ExecutionReadinessOutcome,
    OrderType,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    OrderIntentModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import _routing_assessment_with_trade
from tests.test_phase54_routed_submission_handoff import _build_execution
from tests.test_phase57_routed_post_submit_lifecycle import (
    _api_get_json,
    _enable_actionability_capabilities,
)
from tests.test_phase59_routed_reconciliation_lifecycle_audit import (
    _api_post_json,
    _install_reconcile_update,
)


def _execution_record_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _assert_no_route_expansion_fields(payload: dict[str, object]) -> None:
    for forbidden in (
        "route_plan",
        "route_executor",
        "allocation",
        "allocation_weights",
        "price_score",
        "quality_score",
        "venue_score",
        "confidence_score",
        "best_binding",
        "optimal_venue",
        "cbbo",
    ):
        assert forbidden not in payload


def _assert_selected_route_context(
    context: dict[str, object],
    *,
    desired_trade_key: str,
    assessment_id: str,
    target_choice_id: str,
    selected_candidate,
    readiness_evaluation_id: str,
) -> None:
    assert context["routed_origin"] is True
    assert context["desired_trade_key"] == desired_trade_key
    assert context["routing_assessment_id"] == assessment_id
    assert context["routing_target_choice_id"] == target_choice_id
    assert context["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert context["selected_binding_key"] == selected_candidate.binding_key
    assert context["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert context["selected_venue_account_key"] == selected_candidate.venue_account_key
    assert context["selected_venue"] == selected_candidate.venue
    assert context["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert context["readiness_evaluation_id"] == readiness_evaluation_id
    assert context["explicit_action_required"] is True
    assert context["auto_submit"] is False
    assert context["fanout_created"] is False
    assert context["scoring_created"] is False
    assert context["target_reselection"] is False
    assert context["same_target_only"] is True
    assert context["same_account_only"] is True
    assert context["same_venue_only"] is True
    assert context["route_lineage_malformed"] is False
    assert context["missing_lineage_fields"] == []
    assert context["malformed_lineage_fields"] == []
    assert "routed_recovery_same_target_only" in context["boundary_reason_codes"]
    assert "no_fanout" in context["boundary_reason_codes"]
    assert "no_target_reselection" in context["boundary_reason_codes"]
    order_shape = context["routed_order_shape_policy"]
    assert order_shape["phase"] == "phase_5_8"
    assert order_shape["order_type"] == OrderType.MARKET.value
    assert order_shape["limit_price"] is None
    assert order_shape["reduce_only"] is False


def test_phase5_closeout_routed_lifecycle_surfaces_remain_consistent_and_bounded() -> None:
    session_factory = build_test_session_factory()
    routing, _initial_assessment, desired_trade_key, context = _routing_assessment_with_trade(
        session_factory
    )
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="phase510-secondary",
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
    assert _execution_record_counts(session_factory) == (0, 0, 0)

    conversion = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert conversion.intent_id is not None
    assert conversion.prepared_order_created is False
    assert conversion.readiness_assessment_created is False
    assert conversion.submitted_order_created is False
    assert conversion.provenance["fanout_created"] is False
    assert conversion.provenance["allocation_created"] is False
    assert conversion.provenance["auto_submit"] is False
    assert _execution_record_counts(session_factory) == (1, 0, 0)

    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    _enable_actionability_capabilities(adapter)
    preview = asyncio.run(execution.preview_child_intent(conversion.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))

    assert preview.payload is not None
    assert preview.payload["non_submitting"] is True
    assert preview.payload["explicit_submit_required"] is True
    assert preview.payload["routed_submission_enabled"] is True
    assert preview.payload["live_submission_enabled"] is True
    assert preview.payload["submission_deferred"] is False
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    assert adapter.submit_calls == 0
    assert _execution_record_counts(session_factory)[2] == 0

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert adapter.submit_calls == 1
    assert len(adapter.submitted_intents) == 1
    assert adapter.submitted_intents[0].venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert submitted.intent_id == conversion.intent_id
    assert submitted.venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert _execution_record_counts(session_factory)[0] == 1
    assert _execution_record_counts(session_factory)[2] == 1

    routed_submission = submitted.raw_payload["routed_submission"]
    readiness_evaluation_id = routed_submission["readiness_evaluation_id"]
    assert routed_submission["routing_assessment_id"] == assessment.assessment_id
    assert routed_submission["routing_target_choice_id"] == choice.target_choice_id
    assert routed_submission["selected_binding_ref_id"] == selected_candidate.binding_ref_id
    assert routed_submission["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert routed_submission["selected_venue"] == selected_candidate.venue
    assert routed_submission["selected_exchange_symbol"] == selected_candidate.exchange_symbol
    assert routed_submission["auto_submit"] is False
    assert routed_submission["fanout_created"] is False
    assert routed_submission["scoring_created"] is False
    assert routed_submission["target_reselection"] is False
    assert routed_submission["routed_order_shape_policy"]["order_type"] == OrderType.MARKET.value

    post_submit_counts = _execution_record_counts(session_factory)
    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
    listed = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    listed_detail = next(
        item for item in listed if item["submitted_order_id"] == submitted.submitted_order_id
    )
    actionability = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/actionability",
    )
    recovery = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/recovery",
    )

    for payload in (detail, listed_detail, actionability, recovery):
        _assert_no_route_expansion_fields(payload)
        assert payload["routed_origin"] is True
        assert payload["venue_account_ref_id"] == selected_candidate.venue_account_ref_id
        _assert_selected_route_context(
            payload["routed_lifecycle_context"],
            desired_trade_key=desired_trade_key,
            assessment_id=assessment.assessment_id,
            target_choice_id=choice.target_choice_id,
            selected_candidate=selected_candidate,
            readiness_evaluation_id=readiness_evaluation_id,
        )

    for payload in (detail, listed_detail):
        lineage = payload["routed_lineage"]
        assert lineage["routing_assessment_id"] == assessment.assessment_id
        assert lineage["routing_target_choice_id"] == choice.target_choice_id
        assert lineage["selected_binding_ref_id"] == selected_candidate.binding_ref_id
        assert lineage["selected_venue_account_ref_id"] == selected_candidate.venue_account_ref_id
        assert lineage["readiness_evaluation_id"] == readiness_evaluation_id
        assert lineage["auto_submit"] is False
        assert lineage["fanout_created"] is False
        assert lineage["scoring_created"] is False
        assert lineage["target_reselection"] is False
        assert "routed_order_shape_policy" not in lineage

    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "source": "phase510_update_payload_collision",
                "routing_assessment_id": "fake-assessment",
            },
            "venue_reconciliation": {
                "source": "phase510_closeout_adapter",
                "status": "open",
            },
        },
    )
    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile",
    )
    events = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events",
    )
    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )

    _assert_no_route_expansion_fields(reconciled)
    assert reconciled["raw_payload"]["venue_reconciliation"]["source"] == (
        "phase510_closeout_adapter"
    )
    assert reconciled["raw_payload"]["routed_submission"] == routed_submission
    assert reconciled["raw_payload"]["routed_submission"].get("source") != (
        "phase510_update_payload_collision"
    )
    _assert_selected_route_context(
        reconciled["routed_lifecycle_context"],
        desired_trade_key=desired_trade_key,
        assessment_id=assessment.assessment_id,
        target_choice_id=choice.target_choice_id,
        selected_candidate=selected_candidate,
        readiness_evaluation_id=readiness_evaluation_id,
    )

    assert reconciliation_event["routed_origin"] is True
    assert reconciliation_event["raw_payload"]["routed_submission"]["source"] == (
        "phase510_update_payload_collision"
    )
    _assert_selected_route_context(
        reconciliation_event["routed_lifecycle_context"],
        desired_trade_key=desired_trade_key,
        assessment_id=assessment.assessment_id,
        target_choice_id=choice.target_choice_id,
        selected_candidate=selected_candidate,
        readiness_evaluation_id=readiness_evaluation_id,
    )
    assert _execution_record_counts(session_factory) == post_submit_counts
    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.venue_account_ref_id == other_candidate.venue_account_ref_id
                )
            )
            == 0
        )
