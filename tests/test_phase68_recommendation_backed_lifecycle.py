from __future__ import annotations

import asyncio
from sqlalchemy import func, select

from core.domain.enums import SubmittedOrderStatus
from db.models import (
    OrderIntentModel,
    RouteReadinessAuditModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderLifecycleEventModel,
    SubmittedOrderModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase45_execution_lifecycle import _mark_submitted_order_retryable_rejected
from tests.test_phase57_routed_post_submit_lifecycle import (
    _allow_same_target_retry_private_checks,
    _api_get_json,
    _enable_actionability_capabilities,
    _insert_hyperliquid_submitted_order,
)
from tests.test_phase59_routed_reconciliation_lifecycle_audit import (
    _api_post_json,
    _install_reconcile_update,
)
from tests.test_phase67_recommendation_backed_submission import (
    _submit_recommendation_backed_child_intent,
)


def _record_counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
            "child_intents": session.scalar(select(func.count()).select_from(OrderIntentModel)),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
            "lifecycle_events": session.scalar(
                select(func.count()).select_from(SubmittedOrderLifecycleEventModel)
            ),
        }


def test_recommendation_backed_submitted_order_detail_list_and_lifecycle_expose_lineage() -> None:
    session_factory = build_test_session_factory()
    (
        _routing,
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
    _install_reconcile_update(adapter)
    before_actionability_counts = _record_counts(session_factory)

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
    listed = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    list_item = next(
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

    for payload in (detail, list_item, actionability, recovery):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        assert context["intent_id"] == conversion.intent_id
        assert context["desired_trade_key"] == desired_trade_key
        assert context["routing_assessment_id"] == audit.routing_assessment_id
        assert context["route_readiness_audit_id"] == audit.route_readiness_audit_id
        assert context["routing_target_recommendation_id"] == (
            recommendation.routing_target_recommendation_id
        )
        assert context["routing_target_choice_id"] == choice.target_choice_id
        assert context["recommendation_policy_name"] == recommendation.policy_name
        assert context["selected_binding_ref_id"] == choice.selected_binding_ref_id
        assert context["selected_venue_account_ref_id"] == (
            choice.selected_venue_account_ref_id
        )
        assert context["selected_venue"] == choice.selected_venue
        assert context["selected_exchange_symbol"] == conversion.selected_exchange_symbol
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

    assert detail["routed_lineage"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert detail["routed_lineage"]["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert _record_counts(session_factory) == before_actionability_counts

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

    for payload in (reconciled, reconciliation_event):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        assert context["routing_target_recommendation_id"] == (
            recommendation.routing_target_recommendation_id
        )
        assert context["route_readiness_audit_id"] == audit.route_readiness_audit_id
        assert context["routing_target_choice_id"] == choice.target_choice_id
        assert context["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True
        assert context["auto_submit"] is False
        assert context["fanout_created"] is False
        assert context["target_reselection"] is False


def test_recommendation_backed_reconciliation_cannot_overwrite_platform_lineage() -> None:
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
        submitted,
    ) = _submit_recommendation_backed_child_intent(session_factory)
    original_lineage = dict(submitted.raw_payload["routed_submission"])
    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "source": "venue_collision",
                "route_readiness_audit_id": "fake-audit",
                "routing_target_recommendation_id": "fake-recommendation",
                "routing_target_choice_id": "fake-choice",
                "intent_id": "fake-intent",
                "recommendation_policy_name": "fake-policy",
                "selected_venue_account_ref_id": "fake-account",
                "selected_venue": "fake-venue",
                "selected_exchange_symbol": "FAKE-SYMBOL",
            },
            "venue_reconciliation": {"source": "phase68_collision_adapter"},
        },
    )
    before_counts = _record_counts(session_factory)

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile",
    )
    events = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events",
    )

    assert reconciled["raw_payload"]["routed_submission"] == original_lineage
    context = reconciled["routed_lifecycle_context"]
    assert context["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert context["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert context["routing_target_choice_id"] == choice.target_choice_id
    assert context["intent_id"] == conversion.intent_id
    assert context["recommendation_policy_name"] == recommendation.policy_name
    assert context["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert context["selected_venue"] == choice.selected_venue
    assert context["selected_exchange_symbol"] == conversion.selected_exchange_symbol
    assert reconciled["raw_payload"]["venue_reconciliation"]["source"] == (
        "phase68_collision_adapter"
    )
    assert _record_counts(session_factory)["child_intents"] == before_counts["child_intents"]
    assert _record_counts(session_factory)["submitted_orders"] == before_counts["submitted_orders"]

    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    assert reconciliation_event["raw_payload"]["routed_submission"]["source"] == "venue_collision"
    assert reconciliation_event["routed_lifecycle_context"]["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )


def test_non_routed_reconciliation_cannot_fabricate_recommendation_lineage() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase68-non-routed-collision",
        raw_payload={"adapter_submit_called": True},
    )
    (
        _routing,
        _audit,
        _recommendation,
        _choice,
        _desired_trade_key,
        _conversion,
        execution,
        adapter,
        _submitted,
    ) = _submit_recommendation_backed_child_intent(session_factory)
    _install_reconcile_update(
        adapter,
        raw_payload={
            "routed_submission": {
                "routing_target_recommendation_id": "fake-recommendation",
                "route_readiness_audit_id": "fake-audit",
                "routing_target_choice_id": "fake-choice",
            },
            "venue_reconciliation": {"source": "phase68_non_routed_collision_adapter"},
        },
    )

    reconciled = _api_post_json(
        execution,
        f"/api/v1/submitted-orders/{submitted_order_id}/reconcile",
    )
    events = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted_order_id}/events")

    assert reconciled["routed_origin"] is False
    assert reconciled["routed_lineage"] is None
    assert reconciled["routed_lifecycle_context"] is None
    assert "routed_submission" not in reconciled["raw_payload"]
    reconciliation_event = next(
        event for event in events if event["event_type"] == "reconciliation_open"
    )
    assert reconciliation_event["routed_origin"] is False
    assert reconciliation_event["routed_lifecycle_context"] is None


def test_same_target_retry_preserves_recommendation_backed_lineage() -> None:
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
        submitted,
    ) = _submit_recommendation_backed_child_intent(session_factory)
    _allow_same_target_retry_private_checks(adapter)
    _mark_submitted_order_retryable_rejected(session_factory, submitted.submitted_order_id)

    retry_result = asyncio.run(
        execution.execute_submitted_order_recovery(submitted.submitted_order_id)
    )

    assert retry_result.action == "retry_same_target"
    assert retry_result.executed is True
    assert retry_result.resulting_order is not None
    retried = retry_result.resulting_order
    routed_payload = retried.raw_payload["routed_submission"]
    assert retried.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert routed_payload["intent_id"] == conversion.intent_id
    assert routed_payload["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert routed_payload["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert routed_payload["routing_target_choice_id"] == choice.target_choice_id
    assert routed_payload["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert routed_payload["selected_venue"] == choice.selected_venue
    assert routed_payload["auto_submit"] is False
    assert routed_payload["fanout_created"] is False
    assert routed_payload["allocation_created"] is False
    assert routed_payload["route_executor_created"] is False
    assert routed_payload["target_reselection"] is False

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
        for provenance in (
            recommendation_model.provenance_json,
            audit_model.provenance_json,
        ):
            assert provenance["submitted_order_id"] == submitted.submitted_order_id
            assert provenance["first_submitted_order_id"] == submitted.submitted_order_id
            assert provenance["first_submitted_order_created_at"] == (
                provenance["submitted_order_created_at"]
            )
            assert provenance["latest_submitted_order_id"] == retried.submitted_order_id
            assert provenance["submitted_order_ids"] == [
                submitted.submitted_order_id,
                retried.submitted_order_id,
            ]
            assert provenance["auto_submit"] is False
            assert provenance["fanout_created"] is False
            assert provenance["route_executor_created"] is False
            assert provenance["target_reselection"] is False
