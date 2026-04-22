from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    MandateDesiredTradeStatus,
    OrderType,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    RoutingTargetRecommendationStatus,
)
from core.domain.models import RoutedOrderShapePolicyInput
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase600_routing_target_recommendation import (
    _multi_ready_audit,
    _mutate_ready_candidate_quote_observed_at,
    _ready_audit,
    _set_binding_recommendation_priorities,
)


client = TestClient(app)


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
            "readiness": session.scalar(
                select(func.count()).select_from(ExecutionReadinessEvaluationModel)
            ),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
        }


def _accepted_choice(session_factory):
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id,
            requested_by="phase_6_3_test_operator",
        )
    )
    assert choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    return routing, audit, recommendation, choice, desired_trade_key


def _insert_duplicate_recommendation_target_choice(
    session_factory,
    *,
    source_choice_id: str,
    recommendation_id: str,
) -> str:
    with session_factory() as session:
        source_choice = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == source_choice_id
            )
        )
        recommendation = session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation_id
            )
        )
        assert source_choice is not None
        assert recommendation is not None
        provenance = dict(source_choice.provenance_json or {})
        provenance.update(
            {
                "routing_target_recommendation_id": recommendation_id,
                "duplicate_same_audit_test_choice": True,
            }
        )
        duplicate = RoutingTargetChoiceModel(
            environment=source_choice.environment,
            target_choice_id=f"{source_choice.target_choice_id}-duplicate",
            routing_assessment_ref_id=source_choice.routing_assessment_ref_id,
            routing_assessment_id=source_choice.routing_assessment_id,
            desired_trade_ref_id=source_choice.desired_trade_ref_id,
            desired_trade_key=source_choice.desired_trade_key,
            selected_binding_ref_id=source_choice.selected_binding_ref_id,
            selected_binding_key=source_choice.selected_binding_key,
            selected_venue_account_ref_id=source_choice.selected_venue_account_ref_id,
            selected_venue_account_key=source_choice.selected_venue_account_key,
            selected_venue=source_choice.selected_venue,
            status=RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED,
            reason_codes_json=list(source_choice.reason_codes_json or []),
            missing_data_json=[],
            approval_note="duplicate same-audit test choice",
            requested_by="phase_6_3_test_operator",
            non_executing=True,
            provenance_json=provenance,
            selected_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        session.add(duplicate)
        recommendation.target_choice_created = True
        session.commit()
        return duplicate.target_choice_id


def _assert_no_downstream_after_child_intent(session_factory, *, child_intents: int) -> None:
    counts = _counts(session_factory)
    assert counts["child_intents"] == child_intents
    assert counts["readiness"] == 0
    assert counts["submitted_orders"] == 0


def test_accepted_recommendation_target_choice_converts_to_one_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation, choice, desired_trade_key = _accepted_choice(session_factory)
    ready_candidate = audit.candidates[0]

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.child_intent_created is True
    assert result.child_intent_reused is False
    assert result.routing_target_recommendation_id == recommendation.routing_target_recommendation_id
    assert result.route_readiness_audit_id == audit.route_readiness_audit_id
    assert result.selected_binding_ref_id == ready_candidate.binding_ref_id
    assert result.selected_binding_key == ready_candidate.binding_key
    assert result.selected_venue_account_ref_id == ready_candidate.venue_account_ref_id
    assert result.selected_venue_account_key == ready_candidate.venue_account_key
    assert result.selected_venue == ready_candidate.venue
    assert result.selected_exchange_symbol == ready_candidate.exchange_symbol
    assert result.prepared_order_created is False
    assert result.readiness_assessment_created is False
    assert result.submitted_order_created is False
    assert result.provenance["child_intent_created"] is True
    assert result.provenance["fanout_created"] is False
    assert result.provenance["auto_submit"] is False
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)

    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key
            )
        )
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id)
        )
        recommendation_model = session.scalar(
            select(RoutingTargetRecommendationModel).where(
                RoutingTargetRecommendationModel.routing_target_recommendation_id
                == recommendation.routing_target_recommendation_id
            )
        )
        assert desired_trade is not None
        assert intent is not None
        assert recommendation_model is not None
        assert desired_trade.status == MandateDesiredTradeStatus.ROUTED
        assert intent.provenance["phase_boundary"] == (
            "phase_6_3_recommendation_target_choice_conversion"
        )
        assert (
            intent.provenance["routing_target_recommendation_id"]
            == recommendation.routing_target_recommendation_id
        )
        assert intent.provenance["routing_target_choice_id"] == choice.target_choice_id
        assert intent.provenance["route_readiness_audit_id"] == audit.route_readiness_audit_id
        assert intent.provenance["recommendation_policy_name"] == recommendation.policy_name
        assert intent.provenance["operator_conversion_at"]
        assert intent.provenance["prepared_order_created"] is False
        assert intent.provenance["readiness_assessment_created"] is False
        assert intent.provenance["submitted_order_created"] is False
        assert recommendation_model.child_intent_created is True
        assert recommendation_model.provenance_json["child_intent_id"] == result.intent_id

    fetched_audit = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))
    assert fetched_audit.child_intent_created is True
    assert fetched_audit.provenance["child_intent_id"] == result.intent_id


def test_repeated_conversion_returns_existing_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key = _accepted_choice(
        session_factory
    )

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    second = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    assert second.child_intent_reused is True
    assert "child_intent_already_exists" in second.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)


def test_duplicate_same_audit_target_choices_reuse_existing_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation_a, choice_a, _desired_trade_key = _accepted_choice(
        session_factory
    )
    recommendation_b = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation_b.routing_target_recommendation_id
        )
    )
    duplicate_choice_id = _insert_duplicate_recommendation_target_choice(
        session_factory,
        source_choice_id=choice_a.target_choice_id,
        recommendation_id=recommendation_b.routing_target_recommendation_id,
    )

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice_a.target_choice_id))
    second = asyncio.run(routing.convert_target_choice_to_child_intent(duplicate_choice_id))

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    assert "route_readiness_audit_child_intent_already_created" in second.reason_codes
    assert "recommendation_target_choice_child_intent_reused" in second.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)

    fetched_b = asyncio.run(
        routing.get_routing_target_recommendation(
            recommendation_b.routing_target_recommendation_id
        )
    )
    assert fetched_b.child_intent_created is True
    assert fetched_b.provenance["child_intent_id"] == first.intent_id
    assert fetched_b.provenance["route_readiness_audit_child_intent_already_created"] is True
    assert recommendation_a.routing_target_recommendation_id != recommendation_b.routing_target_recommendation_id


def test_blocked_recommendation_backed_target_choice_cannot_convert() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _recommendation, choice, _desired_trade_key = _accepted_choice(session_factory)
    blocked_recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )
    assert blocked_recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    blocked_choice_id = _insert_duplicate_recommendation_target_choice(
        session_factory,
        source_choice_id=choice.target_choice_id,
        recommendation_id=blocked_recommendation.routing_target_recommendation_id,
    )

    result = asyncio.run(routing.convert_target_choice_to_child_intent(blocked_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_INCOMPLETE
    assert "routing_target_recommendation_not_recommended" in result.reason_codes
    assert result.intent_id is None
    _assert_no_downstream_after_child_intent(session_factory, child_intents=0)


def test_current_truth_drift_blocks_recommendation_target_choice_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key = _accepted_choice(
        session_factory
    )
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, choice.selected_binding_ref_id)
        account = session.get(VenueAccountModel, choice.selected_venue_account_ref_id)
        assert binding is not None
        assert account is not None
        binding.enabled = False
        account.is_active = False
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert "binding_disabled" in result.reason_codes
    assert "venue_account_inactive" in result.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=0)


def test_stale_quote_blocks_recommendation_target_choice_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _recommendation, choice, _desired_trade_key = _accepted_choice(session_factory)
    ready_candidate = audit.candidates[0]
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=ready_candidate.binding_key,
    )

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert "quote_stale_at_recommendation" in result.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=0)


def test_inactive_symbol_mapping_blocks_recommendation_target_choice_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _recommendation, choice, _desired_trade_key = _accepted_choice(session_factory)
    ready_candidate = audit.candidates[0]
    with session_factory() as session:
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == ready_candidate.instrument_ref_id,
                SymbolModel.venue == ready_candidate.venue,
                SymbolModel.symbol == ready_candidate.symbol,
                SymbolModel.exchange_symbol == ready_candidate.exchange_symbol,
            )
        )
        assert symbol is not None
        symbol.is_active = False
        symbol.is_trading_eligible = False
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert "symbol_inactive" in result.reason_codes
    assert "symbol_not_trading_eligible" in result.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=0)


def test_explicit_limit_policy_converts_only_to_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key = _accepted_choice(
        session_factory
    )

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("101.25"),
                policy_source="operator_requested",
                requested_by="phase_6_3_test_operator",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.provenance["routed_order_shape_policy"]["limit_price"] == "101.25"
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id)
        )
        assert intent is not None
        assert intent.order_type == OrderType.LIMIT
        assert intent.limit_price == Decimal("101.250000000000")
        assert (
            "limit_price_explicit"
            in intent.provenance["routed_order_shape_policy"]["reason_codes"]
        )
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)


def test_invalid_limit_policy_blocks_before_child_intent_creation() -> None:
    session_factory = build_test_session_factory()
    routing, _audit, _recommendation, choice, _desired_trade_key = _accepted_choice(
        session_factory
    )

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("0"),
                policy_source="operator_requested",
                requested_by="phase_6_3_test_operator",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "invalid_limit_price" in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    _assert_no_downstream_after_child_intent(session_factory, child_intents=0)


def test_explicit_binding_priority_recommendation_target_choice_can_convert() -> None:
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
    choice = asyncio.run(
        routing.accept_routing_target_recommendation_to_target_choice(
            recommendation.routing_target_recommendation_id
        )
    )

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.selected_binding_key == second_candidate.binding_key
    assert result.routing_target_recommendation_id == recommendation.routing_target_recommendation_id
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)


def test_conversion_api_exposes_recommendation_lineage() -> None:
    session_factory = build_test_session_factory()
    routing, audit, recommendation, choice, _desired_trade_key = _accepted_choice(session_factory)
    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        response = client.post(
            f"/api/v1/routing-target-choices/{choice.target_choice_id}/convert-to-child-intent"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED.value
    assert payload["routing_target_recommendation_id"] == (
        recommendation.routing_target_recommendation_id
    )
    assert payload["route_readiness_audit_id"] == audit.route_readiness_audit_id
    assert payload["selected_binding_key"] == choice.selected_binding_key
    assert payload["selected_venue_account_key"] == choice.selected_venue_account_key
    assert payload["selected_venue"] == choice.selected_venue
    assert payload["selected_exchange_symbol"] == audit.candidates[0].exchange_symbol
    assert payload["child_intent_created"] is True
    assert payload["prepared_order_created"] is False
    assert payload["readiness_assessment_created"] is False
    assert payload["submitted_order_created"] is False
    assert payload["provenance"]["fanout_created"] is False
    assert payload["provenance"]["auto_submit"] is False
    _assert_no_downstream_after_child_intent(session_factory, child_intents=1)
