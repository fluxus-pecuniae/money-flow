from __future__ import annotations

from sqlalchemy import func, select

from db.models import (
    OrderIntentModel,
    RoutingTargetChoiceModel,
    SubmittedOrderLifecycleEventModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase57_routed_post_submit_lifecycle import (
    _api_get_json,
    _enable_actionability_capabilities,
)
from tests.test_phase59_routed_reconciliation_lifecycle_audit import (
    _api_post_json,
    _install_reconcile_update,
)
from tests.test_phase67_recommendation_backed_submission import (
    _submit_recommendation_backed_child_intent,
)
from tests.test_phase69_routed_workflow_inspection import _workflow_response


def _closeout_counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
            "target_choices": session.scalar(
                select(func.count()).select_from(RoutingTargetChoiceModel)
            ),
            "child_intents": session.scalar(select(func.count()).select_from(OrderIntentModel)),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
            "lifecycle_events": session.scalar(
                select(func.count()).select_from(SubmittedOrderLifecycleEventModel)
            ),
        }


def test_phase6_closeout_recommendation_backed_single_target_execution_flow() -> None:
    session_factory = build_test_session_factory()
    (
        routing,
        audit,
        recommendation,
        choice,
        desired_trade_key,
        conversion,
        execution,
        adapter,
        submitted,
    ) = _submit_recommendation_backed_child_intent(session_factory)
    _enable_actionability_capabilities(adapter)
    original_routed_payload = dict(submitted.raw_payload["routed_submission"])
    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "source": "venue_collision",
                "routing_assessment_id": "fake-assessment",
                "route_readiness_audit_id": "fake-audit",
                "routing_target_recommendation_id": "fake-recommendation",
                "routing_target_choice_id": "fake-choice",
                "selected_venue_account_ref_id": "fake-account",
                "selected_venue": "fake-venue",
                "selected_exchange_symbol": "FAKE",
            },
            "venue_reconciliation": {"source": "phase610_collision_adapter"},
        },
    )

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
    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile",
    )
    events = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events",
    )
    workflow = _workflow_response(routing, desired_trade_key)

    counts = _closeout_counts(session_factory)
    assert counts["target_choices"] == 1
    assert counts["child_intents"] == 1
    assert counts["submitted_orders"] == 1
    assert counts["lifecycle_events"] == 2
    assert adapter.submit_calls == 1

    expected = {
        "desired_trade_key": desired_trade_key,
        "routing_assessment_id": audit.routing_assessment_id,
        "route_readiness_audit_id": audit.route_readiness_audit_id,
        "routing_target_recommendation_id": (
            recommendation.routing_target_recommendation_id
        ),
        "routing_target_choice_id": choice.target_choice_id,
        "intent_id": conversion.intent_id,
        "selected_binding_ref_id": choice.selected_binding_ref_id,
        "selected_venue_account_ref_id": choice.selected_venue_account_ref_id,
        "selected_venue": choice.selected_venue,
        "selected_exchange_symbol": conversion.selected_exchange_symbol,
        "recommendation_policy_name": recommendation.policy_name,
    }

    for payload in (detail, listed_detail, actionability, recovery, reconciled):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        for key, value in expected.items():
            assert context[key] == value
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True
        assert context["auto_submit"] is False
        assert context["fanout_created"] is False
        assert context["allocation_created"] is False
        assert context["scoring_created"] is False
        assert context["route_executor_created"] is False
        assert context["target_reselection"] is False
        assert context["submitted_order_created"] is True
        assert "route_plan" not in payload
        assert "allocation" not in payload
        assert "score" not in payload

    assert reconciled["raw_payload"]["routed_submission"] == original_routed_payload
    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    assert reconciliation_event["raw_payload"]["routed_submission"]["source"] == (
        "venue_collision"
    )
    assert reconciliation_event["routed_lifecycle_context"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )

    workflow_lineage = workflow["routed_lineage"]
    assert workflow["found"] is True
    assert workflow["current_status_summary"]["state"] == "submitted_order_created"
    assert workflow["artifacts_created_by_inspection"] is False
    assert workflow["artifact_counts"]["routing_target_choices"] == 1
    assert workflow["artifact_counts"]["child_intents"] == 1
    assert workflow["artifact_counts"]["submitted_orders"] == 1
    assert workflow["artifact_counts"]["lifecycle_events"] == 2
    for key, value in expected.items():
        assert workflow_lineage[key] == value
    assert workflow["submitted_orders"][0]["submitted_order_id"] == submitted.submitted_order_id
    assert "actionability_summary" not in workflow
    assert "recovery_summary" not in workflow
    assert workflow["same_target_lifecycle_summary"]["same_target_only"] is True
    assert workflow["same_target_lifecycle_summary"]["same_venue_only"] is True
    assert workflow["same_target_lifecycle_summary"]["fanout_created"] is False
    assert workflow["same_target_lifecycle_summary"]["allocation_created"] is False
    assert workflow["same_target_lifecycle_summary"]["scoring_created"] is False
    assert workflow["same_target_lifecycle_summary"]["route_executor_created"] is False
    assert workflow["same_target_lifecycle_summary"]["target_reselection"] is False
