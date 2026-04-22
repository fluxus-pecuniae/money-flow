from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import RoutingTargetRecommendationStatus
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
)
from services.routing.service import RoutingAssessmentError
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase600_routing_target_recommendation import (
    _assert_no_routing_leakage,
    _multi_ready_audit,
    _mutate_ready_candidate_quote_observed_at,
    _ready_audit,
    _set_binding_recommendation_priorities,
)


client = TestClient(app)


def _assert_artifact_counts(
    session_factory,
    *,
    recommendations: int,
    target_choices: int,
) -> None:
    with session_factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(RoutingTargetRecommendationModel))
            == recommendations
        )
        assert (
            session.scalar(select(func.count()).select_from(RoutingTargetChoiceModel))
            == target_choices
        )
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert (
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel))
            == 0
        )
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def _utc_normalized(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def test_successful_single_ready_recommendation_acceptance_creates_one_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id,
            approval_note="operator accepted single ready candidate",
            requested_by="phase_6_2_test_operator",
        )
    )
    fetched_recommendation = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation.routing_target_recommendation_id
        )
    )
    fetched_audit = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    assert choice.selected_binding_ref_id == recommendation.recommended_binding_ref_id
    assert choice.selected_binding_key == recommendation.recommended_binding_key
    assert choice.selected_binding_ref_id == ready_candidate.binding_ref_id
    assert choice.selected_venue_account_ref_id == recommendation.recommended_venue_account_ref_id
    assert choice.selected_venue_account_key == recommendation.recommended_venue_account_key
    assert choice.selected_venue == recommendation.recommended_venue
    assert choice.non_executing is True
    assert "routing_target_recommendation_accepted" in choice.reason_codes
    assert choice.provenance["source"] == "routing_target_recommendation"
    assert (
        choice.provenance["routing_target_recommendation_id"]
        == recommendation.routing_target_recommendation_id
    )
    assert choice.provenance["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert choice.provenance["routing_assessment_id"] == audit.routing_assessment_id
    assert choice.provenance["recommended_exchange_symbol"] == ready_candidate.exchange_symbol
    assert choice.provenance["child_intent_created"] is False
    assert choice.provenance["readiness_assessment_created"] is False
    assert choice.provenance["submitted_order_created"] is False
    assert fetched_recommendation.target_choice_created is True
    assert (
        fetched_recommendation.provenance["routing_target_choice_id"]
        == choice.target_choice_id
    )
    assert fetched_recommendation.child_intent_created is False
    assert fetched_recommendation.submitted_order_created is False
    assert fetched_audit.target_choice_created is True
    _assert_no_routing_leakage(asdict(choice))
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=1)


def test_blocked_recommendation_cannot_be_accepted() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_to_target_choice(
                recommendation.routing_target_recommendation_id
            )
        )

    assert exc.value.reason_code == "routing_target_recommendation_not_recommended"
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=0)


def test_unknown_recommendation_cannot_be_accepted() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _desired_trade_key = _ready_audit(session_factory)

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_to_target_choice(
                "rtreco_missing"
            )
        )

    assert exc.value.reason_code == "routing_target_recommendation_not_found"
    _assert_artifact_counts(session_factory, recommendations=0, target_choices=0)


def test_current_binding_truth_drift_blocks_recommendation_acceptance() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, ready_candidate.binding_ref_id)
        assert binding is not None
        binding.enabled = False
        session.commit()

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_to_target_choice(
                recommendation.routing_target_recommendation_id
            )
        )

    assert exc.value.reason_code == "binding_disabled"
    fetched_recommendation = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation.routing_target_recommendation_id
        )
    )
    assert fetched_recommendation.target_choice_created is False
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=0)


def test_stale_quote_blocks_recommendation_acceptance() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=ready_candidate.binding_key,
    )

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_to_target_choice(
                recommendation.routing_target_recommendation_id
            )
        )

    assert exc.value.reason_code == "quote_stale_at_recommendation"
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=0)


def test_recommendation_acceptance_is_idempotent() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    first_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id
        )
    )
    first_fetched_recommendation = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation.routing_target_recommendation_id
        )
    )
    first_fetched_audit = asyncio.run(
        routing.get_route_readiness_audit(audit.route_readiness_audit_id)
    )
    first_recommendation_accepted_at = (
        first_fetched_recommendation.provenance["recommendation_accepted_at"]
    )
    first_audit_accepted_at = first_fetched_audit.provenance["recommendation_accepted_at"]

    second_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id
        )
    )
    fetched_recommendation = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation.routing_target_recommendation_id
        )
    )

    assert second_choice.target_choice_id == first_choice.target_choice_id
    assert _utc_normalized(second_choice.selected_at) == _utc_normalized(first_choice.selected_at)
    assert (
        fetched_recommendation.provenance["routing_target_choice_id"]
        == first_choice.target_choice_id
    )
    assert (
        fetched_recommendation.provenance["recommendation_accepted_at"]
        == first_recommendation_accepted_at
    )
    assert fetched_recommendation.provenance["recommendation_acceptance_idempotent"] is True
    assert "recommendation_acceptance_last_checked_at" in fetched_recommendation.provenance
    assert "idempotent_reacceptance_checked_at" in fetched_recommendation.provenance
    fetched_audit = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))
    assert fetched_audit.provenance["recommendation_accepted_at"] == first_audit_accepted_at
    assert "recommendation_acceptance_last_checked_at" in fetched_audit.provenance
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=1)


def test_duplicate_recommendations_from_one_audit_return_existing_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    recommendation_a = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    recommendation_b = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation_a.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    assert recommendation_b.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )

    first_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_a.routing_target_recommendation_id
        )
    )
    second_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_b.routing_target_recommendation_id
        )
    )
    fetched_b = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation_b.routing_target_recommendation_id
        )
    )

    assert second_choice.target_choice_id == first_choice.target_choice_id
    assert fetched_b.target_choice_created is True
    assert (
        fetched_b.provenance["routing_target_choice_id"]
        == first_choice.target_choice_id
    )
    assert fetched_b.provenance["recommendation_acceptance_idempotent"] is True
    assert (
        fetched_b.provenance["recommendation_acceptance_existing_audit_target_choice"]
        is True
    )
    assert (
        fetched_b.provenance["route_readiness_audit_target_choice_already_created"]
        is True
    )
    assert (
        fetched_b.provenance["original_routing_target_recommendation_id"]
        == recommendation_a.routing_target_recommendation_id
    )
    _assert_artifact_counts(session_factory, recommendations=2, target_choices=1)


def test_duplicate_recommendation_same_audit_preserves_original_accepted_timestamp() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    recommendation_a = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    recommendation_b = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    first_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_a.routing_target_recommendation_id
        )
    )
    fetched_a_after_first = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation_a.routing_target_recommendation_id
        )
    )
    fetched_audit_after_first = asyncio.run(
        routing.get_route_readiness_audit(audit.route_readiness_audit_id)
    )
    original_recommendation_accepted_at = (
        fetched_a_after_first.provenance["recommendation_accepted_at"]
    )
    original_audit_accepted_at = (
        fetched_audit_after_first.provenance["recommendation_accepted_at"]
    )

    second_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_b.routing_target_recommendation_id
        )
    )
    fetched_a_after_second = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation_a.routing_target_recommendation_id
        )
    )
    fetched_b_after_second = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation_b.routing_target_recommendation_id
        )
    )
    fetched_audit_after_second = asyncio.run(
        routing.get_route_readiness_audit(audit.route_readiness_audit_id)
    )

    assert second_choice.target_choice_id == first_choice.target_choice_id
    assert (
        fetched_a_after_second.provenance["recommendation_accepted_at"]
        == original_recommendation_accepted_at
    )
    assert (
        fetched_b_after_second.provenance["recommendation_accepted_at"]
        == original_recommendation_accepted_at
    )
    assert (
        fetched_audit_after_second.provenance["recommendation_accepted_at"]
        == original_audit_accepted_at
    )
    assert (
        fetched_audit_after_second.provenance["routing_target_recommendation_id"]
        == recommendation_a.routing_target_recommendation_id
    )
    assert (
        fetched_audit_after_second.provenance[
            "recommendation_acceptance_last_checked_recommendation_id"
        ]
        == recommendation_b.routing_target_recommendation_id
    )
    assert (
        fetched_b_after_second.provenance["recommendation_acceptance_existing_audit_target_choice"]
        is True
    )
    _assert_artifact_counts(session_factory, recommendations=2, target_choices=1)


def test_blocked_recommendation_from_accepted_audit_cannot_reuse_existing_choice() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    recommendation_a = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    first_choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_a.routing_target_recommendation_id
        )
    )

    blocked_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )
    assert blocked_recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    assert blocked_recommendation.target_choice_created is False
    assert blocked_recommendation.recommended_binding_ref_id is None
    assert "binding_priority_missing" in blocked_recommendation.reason_codes

    with pytest.raises(RoutingAssessmentError) as exc:
        asyncio.run(
            routing.accept_routing_target_recommendation_to_target_choice(
                blocked_recommendation.routing_target_recommendation_id
            )
        )

    fetched_blocked_recommendation = asyncio.run(
        routing.get_routing_target_recommendation(
            blocked_recommendation.routing_target_recommendation_id
        )
    )

    assert exc.value.reason_code == "routing_target_recommendation_not_recommended"
    assert fetched_blocked_recommendation.target_choice_created is False
    assert "routing_target_choice_id" not in fetched_blocked_recommendation.provenance
    assert "recommendation_accepted_at" not in fetched_blocked_recommendation.provenance
    assert (
        "recommendation_acceptance_existing_audit_target_choice"
        not in fetched_blocked_recommendation.provenance
    )
    assert (
        "route_readiness_audit_target_choice_already_created"
        not in fetched_blocked_recommendation.provenance
    )
    _assert_artifact_counts(session_factory, recommendations=2, target_choices=1)
    with session_factory() as session:
        target_choice_ids = list(
            session.scalars(select(RoutingTargetChoiceModel.target_choice_id)).all()
        )
    assert target_choice_ids == [first_choice.target_choice_id]


def test_explicit_binding_priority_recommendation_can_be_accepted() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: 20,
            second_candidate.binding_key: 10,
        },
    )
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )
    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )

    choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id
        )
    )

    assert choice.selected_binding_ref_id == second_candidate.binding_ref_id
    assert choice.selected_binding_key == second_candidate.binding_key
    assert choice.selected_venue_account_ref_id == second_candidate.venue_account_ref_id
    assert choice.provenance["policy_name"] == "explicit_binding_priority"
    assert (
        choice.provenance["routing_target_recommendation_id"]
        == recommendation.routing_target_recommendation_id
    )
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=1)


def test_recommendation_acceptance_api_returns_target_choice_and_updates_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        accept_response = client.post(
            "/api/v1/routing-target-recommendations/"
            f"{recommendation.routing_target_recommendation_id}/accept",
            json={"requested_by": "api_operator"},
        )
        recommendation_response = client.get(
            "/api/v1/routing-target-recommendations/"
            f"{recommendation.routing_target_recommendation_id}"
        )
    finally:
        app.dependency_overrides.clear()

    assert accept_response.status_code == 200
    assert recommendation_response.status_code == 200
    choice_payload = accept_response.json()
    recommendation_payload = recommendation_response.json()
    assert choice_payload["status"] == "target_choice_recorded"
    assert choice_payload["provenance"]["source"] == "routing_target_recommendation"
    assert (
        choice_payload["provenance"]["routing_target_recommendation_id"]
        == recommendation.routing_target_recommendation_id
    )
    assert recommendation_payload["target_choice_created"] is True
    assert (
        recommendation_payload["provenance"]["routing_target_choice_id"]
        == choice_payload["target_choice_id"]
    )
    _assert_artifact_counts(session_factory, recommendations=1, target_choices=1)
