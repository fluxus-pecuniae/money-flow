from __future__ import annotations

import asyncio
from dataclasses import asdict

from sqlalchemy import func, select

from core.domain.enums import (
    DecisionAction,
    MandateDesiredTradeStatus,
    RoutingAssessmentDecisionStatus,
    RoutingTargetChoiceStatus,
    TradeTargetScope,
    Venue,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RoutingTargetChoiceModel,
    SubmittedOrderModel,
    VenueAccountModel,
)
from tests.test_phase3_strategy import build_test_session_factory, seed_symbol
from tests.test_phase50_routing_substrate import (
    _build_routing_service,
    _quote,
    _seed_desired_trade,
    _seed_second_hyperliquid_binding,
)


def _routing_assessment_with_trade(session_factory, *, top_of_book=True, supports_order_submission=True):
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=(
            _quote(
                Venue.HYPERLIQUID.value,
                instrument_key=instrument_key,
                instrument_ref_id=instrument_ref_id,
            )
            if top_of_book
            else None
        ),
        supports_order_submission=supports_order_submission,
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    return routing, assessment, desired_trade_key, context


def _execution_object_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _assert_no_execution_leakage(
    session_factory,
    desired_trade_key: str,
    *,
    expected_status: MandateDesiredTradeStatus = MandateDesiredTradeStatus.ROUTING_REQUIRED,
) -> None:
    assert _execution_object_counts(session_factory) == (0, 0, 0)
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        assert desired_trade is not None
        assert desired_trade.status == expected_status


def _mutate_desired_trade(session_factory, desired_trade_key: str, **updates) -> None:
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        assert desired_trade is not None
        for field_name, value in updates.items():
            setattr(desired_trade, field_name, value)
        session.commit()


def _record_first_candidate_choice(routing, assessment):
    return asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=assessment.candidates[0].binding_key,
        )
    )


def test_successful_operator_target_choice_is_non_executing() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    candidate = assessment.candidates[0]

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=candidate.binding_key,
            approval_note="operator picked this eligible binding",
            requested_by="operator@example.test",
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    assert choice.routing_assessment_id == assessment.assessment_id
    assert choice.desired_trade_key == desired_trade_key
    assert choice.selected_binding_ref_id == candidate.binding_ref_id
    assert choice.selected_binding_key == candidate.binding_key
    assert choice.selected_venue_account_ref_id == candidate.venue_account_ref_id
    assert choice.selected_venue_account_key == candidate.venue_account_key
    assert choice.selected_venue == candidate.venue
    assert choice.non_executing is True
    assert "target_choice_recorded" in choice.reason_codes
    assert "child_intent_conversion_deferred" in choice.reason_codes

    _assert_no_execution_leakage(session_factory, desired_trade_key)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RoutingTargetChoiceModel)) == 1

    fetched = asyncio.run(routing.get_routing_target_choice(choice.target_choice_id))
    listed = asyncio.run(routing.list_routing_target_choices_for_assessment(assessment.assessment_id))
    assert fetched.target_choice_id == choice.target_choice_id
    assert [item.target_choice_id for item in listed] == [choice.target_choice_id]


def test_target_choice_does_not_auto_pick_when_binding_not_specified() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    _seed_second_hyperliquid_binding(session_factory, mandate_key=context.mandate.mandate_key)
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    assert assessment.eligible_binding_count == 2

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            requested_by="operator@example.test",
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_CANDIDATE_NOT_FOUND
    assert choice.selected_binding_ref_id is None
    assert "routing_candidate_not_specified" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_ineligible_candidate_is_blocked() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    ineligible_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="disabled",
    )
    with session_factory() as session:
        binding = session.scalar(
            select(MandateAccountBindingModel).where(
                MandateAccountBindingModel.binding_key == ineligible_binding_key,
            )
        )
        assert binding is not None
        binding.enabled = False
        session.commit()

    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    assert assessment.decision_status == RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY
    ineligible_candidate = next(
        candidate for candidate in assessment.candidates if candidate.binding_key == ineligible_binding_key
    )

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=ineligible_binding_key,
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_CANDIDATE_INELIGIBLE
    assert choice.selected_binding_ref_id == ineligible_candidate.binding_ref_id
    assert "routing_candidate_ineligible" in choice.reason_codes
    assert "binding_disabled" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_insufficient_data_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(
        session_factory,
        top_of_book=False,
    )
    assert assessment.decision_status == RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=assessment.candidates[0].binding_key,
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_ASSESSMENT_INSUFFICIENT_DATA
    assert "routing_assessment_insufficient_data" in choice.reason_codes
    assert choice.missing_data == ["missing_quote_snapshot"]
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_no_eligible_bindings_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(
        session_factory,
        supports_order_submission=False,
    )
    assert assessment.decision_status == RoutingAssessmentDecisionStatus.NO_ELIGIBLE_BINDINGS

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=assessment.candidates[0].binding_key,
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_NO_ELIGIBLE_BINDING
    assert "routing_assessment_no_eligible_bindings" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_stale_binding_and_account_truth_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    candidate = assessment.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        assert binding is not None
        assert account is not None
        binding.routing_eligible = False
        account.is_active = False
        session.commit()

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_ref_id=candidate.binding_ref_id,
        )
    )

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "binding_not_routing_eligible" in choice.reason_codes
    assert "venue_account_inactive" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_target_choice_payload_has_no_order_or_scoring_fields() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _routing_assessment_with_trade(session_factory)

    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=assessment.candidates[0].binding_key,
        )
    )
    payload = asdict(choice)
    forbidden = {
        "order_intent_id",
        "prepared_venue_order_id",
        "execution_readiness_assessment_id",
        "submitted_order_id",
        "allocation_weights",
        "venue_ranking",
        "price_score",
        "venue_score",
        "confidence_score",
        "submit_payload",
    }

    assert not (set(payload) & forbidden)


def test_canceled_desired_trade_after_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        status=MandateDesiredTradeStatus.CANCELED,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "desired_trade_not_routing_required" in choice.reason_codes
    assert "target_choice_recorded" not in choice.reason_codes
    _assert_no_execution_leakage(
        session_factory,
        desired_trade_key,
        expected_status=MandateDesiredTradeStatus.CANCELED,
    )


def test_routed_desired_trade_after_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        status=MandateDesiredTradeStatus.ROUTED,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "desired_trade_not_routing_required" in choice.reason_codes
    _assert_no_execution_leakage(
        session_factory,
        desired_trade_key,
        expected_status=MandateDesiredTradeStatus.ROUTED,
    )


def test_already_targeted_desired_trade_after_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    candidate = assessment.candidates[0]
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        mandate_account_binding_ref_id=candidate.binding_ref_id,
        binding_key=candidate.binding_key,
        venue_account_ref_id=candidate.venue_account_ref_id,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "desired_trade_already_targeted" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_non_mandate_scoped_desired_trade_after_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        target_scope=TradeTargetScope.BINDING,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "desired_trade_not_mandate_scoped" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_non_open_desired_trade_after_assessment_blocks_target_choice() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        action=DecisionAction.REDUCE,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
    assert "desired_trade_action_not_open" in choice.reason_codes
    _assert_no_execution_leakage(session_factory, desired_trade_key)


def test_blocked_stale_desired_trade_target_choice_is_persisted() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        status=MandateDesiredTradeStatus.CANCELED,
    )

    choice = _record_first_candidate_choice(routing, assessment)

    with session_factory() as session:
        persisted = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert persisted is not None
        assert persisted.status == RoutingTargetChoiceStatus.BLOCKED_STALE_ASSESSMENT
        assert "desired_trade_not_routing_required" in persisted.reason_codes_json
