from __future__ import annotations

import asyncio
from dataclasses import asdict

from sqlalchemy import func, select

from core.domain.enums import (
    MandateDesiredTradeStatus,
    Environment,
    RoutingAssessmentDecisionStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    Venue,
)
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RoutingAssessmentModel,
    RoutingTargetChoiceModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import (
    _mutate_desired_trade,
    _record_first_candidate_choice,
    _routing_assessment_with_trade,
)


def _execution_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _desired_trade_status(session_factory, desired_trade_key: str) -> MandateDesiredTradeStatus:
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        assert desired_trade is not None
        return desired_trade.status


def _recorded_choice(session_factory):
    routing, assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    choice = _record_first_candidate_choice(routing, assessment)
    assert choice.status == RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED
    return routing, assessment, choice, desired_trade_key, context


def test_successful_target_choice_conversion_creates_exactly_one_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    candidate = assessment.candidates[0]

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.intent_id is not None
    assert result.non_submitting is True
    assert result.prepared_order_created is False
    assert result.readiness_assessment_created is False
    assert result.submitted_order_created is False
    assert _execution_counts(session_factory) == (1, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTED

    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        assert intent.desired_trade_key == desired_trade_key
        assert intent.mandate_desired_trade_ref_id == choice.desired_trade_ref_id
        assert intent.mandate_account_binding_ref_id == candidate.binding_ref_id
        assert intent.binding_key == candidate.binding_key
        assert intent.venue_account_ref_id == candidate.venue_account_ref_id
        assert intent.instrument_key == candidate.instrument_key
        assert intent.instrument_ref_id == candidate.instrument_ref_id
        assert intent.provenance["routing_assessment_id"] == assessment.assessment_id
        assert intent.provenance["routing_target_choice_id"] == choice.target_choice_id
        assert intent.provenance["selected_binding_key"] == candidate.binding_key
        assert intent.provenance["selected_venue_account_ref_id"] == candidate.venue_account_ref_id
        assert intent.provenance["selected_venue"] == Venue.HYPERLIQUID.value
        assert intent.provenance["conversion_non_submitting"] is True
        assert intent.provenance["prepared_order_created"] is False
        assert intent.provenance["readiness_assessment_created"] is False
        assert intent.provenance["submitted_order_created"] is False


def test_conversion_requires_explicit_target_choice_id_surface() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, _choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    assert hasattr(routing, "convert_target_choice_to_child_intent")
    assert not hasattr(routing, "convert_assessment_to_child_intent")
    assert not hasattr(routing, "convert_desired_trade_to_child_intent")


def test_blocked_target_choice_cannot_convert() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _routing_assessment_with_trade(
        session_factory,
        supports_order_submission=False,
    )
    assert assessment.decision_status == RoutingAssessmentDecisionStatus.NO_ELIGIBLE_BINDINGS
    choice = _record_first_candidate_choice(routing, assessment)
    assert choice.status == RoutingTargetChoiceStatus.BLOCKED_NO_ELIGIBLE_BINDING

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_NOT_RECORDED
    assert "routing_target_choice_not_recorded" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_stale_desired_trade_cannot_convert() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    _mutate_desired_trade(
        session_factory,
        desired_trade_key,
        status=MandateDesiredTradeStatus.CANCELED,
    )

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_DESIRED_TRADE
    assert "desired_trade_not_routing_required" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.CANCELED


def test_stale_binding_and_account_cannot_convert() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    candidate = assessment.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        assert binding is not None
        assert account is not None
        binding.routing_eligible = False
        account.is_active = False
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert "binding_not_routing_eligible" in result.reason_codes
    assert "venue_account_inactive" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_candidate_target_mismatch_cannot_convert() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert model is not None
        model.selected_venue_account_ref_id = "mismatched-account"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_CANDIDATE_MISMATCH
    assert "candidate_venue_account_ref_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_assessment_id_mismatch_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert model is not None
        model.routing_assessment_id = "rtassess-mismatched"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_FOUND
    assert "routing_assessment_id_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_assessment_ref_mismatch_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert model is not None
        model.routing_assessment_ref_id = "rtassess-ref-mismatched"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_FOUND
    assert "routing_assessment_ref_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_assessment_environment_mismatch_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        assessment_model = session.scalar(
            select(RoutingAssessmentModel).where(
                RoutingAssessmentModel.assessment_id == assessment.assessment_id,
            )
        )
        assert assessment_model is not None
        assessment_model.environment = Environment.PAPER
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_FOUND
    assert "routing_assessment_environment_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_desired_trade_client_mismatch_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        assert desired_trade is not None
        desired_trade.client_ref_id = "mismatched-client"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_DESIRED_TRADE
    assert "desired_trade_client_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_binding_mandate_mismatch_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    candidate = assessment.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        assert binding is not None
        binding.strategy_mandate_ref_id = "mismatched-mandate"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert "binding_strategy_mandate_mismatch" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_missing_desired_trade_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        choice_model = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assessment_model = session.scalar(
            select(RoutingAssessmentModel).where(
                RoutingAssessmentModel.assessment_id == assessment.assessment_id,
            )
        )
        assert choice_model is not None
        assert assessment_model is not None
        choice_model.desired_trade_ref_id = "missing-desired-trade-ref"
        choice_model.desired_trade_key = "missing-desired-trade-key"
        assessment_model.desired_trade_ref_id = "missing-desired-trade-ref"
        assessment_model.desired_trade_key = "missing-desired-trade-key"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_DESIRED_TRADE
    assert "desired_trade_not_found" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_symbol_mapping_change_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    candidate = assessment.candidates[0]
    with session_factory() as session:
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == candidate.instrument_ref_id,
                SymbolModel.venue == candidate.venue,
                SymbolModel.symbol == candidate.symbol,
                SymbolModel.exchange_symbol == candidate.exchange_symbol,
            )
        )
        assert symbol is not None
        symbol.exchange_symbol = f"{symbol.exchange_symbol}_STALE"
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_STALE_TARGET
    assert result.missing_data == ["symbol_mapping_missing_or_changed"]
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_assessment_status_drift_blocks_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        assessment_model = session.scalar(
            select(RoutingAssessmentModel).where(
                RoutingAssessmentModel.assessment_id == assessment.assessment_id,
            )
        )
        assert assessment_model is not None
        assessment_model.decision_status = RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA
        assessment_model.missing_data_json = ["missing_quote_snapshot"]
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ASSESSMENT_NOT_ASSESSMENT_ONLY
    assert "routing_assessment_not_assessment_only" in result.reason_codes
    assert result.missing_data == ["missing_quote_snapshot"]
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_incomplete_target_choice_fields_block_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        model = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert model is not None
        model.selected_binding_ref_id = None
        session.commit()

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_TARGET_CHOICE_INCOMPLETE
    assert "target_choice_missing_binding_ref" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == MandateDesiredTradeStatus.ROUTING_REQUIRED


def test_target_choice_conversion_is_idempotent() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    second = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_same_venue_multi_account_conversion_uses_selected_account_only() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="secondary",
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    assert assessment.eligible_binding_count == 2
    selected_candidate = next(
        candidate for candidate in assessment.candidates if candidate.binding_key == second_binding_key
    )
    choice = asyncio.run(
        routing.record_target_choice_from_assessment(
            routing_assessment_id=assessment.assessment_id,
            binding_key=second_binding_key,
        )
    )

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert _execution_counts(session_factory) == (1, 0, 0)
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        assert intent.binding_key == second_binding_key
        assert intent.venue_account_ref_id == selected_candidate.venue_account_ref_id
        assert intent.provenance["selected_venue_account_key"] == selected_candidate.venue_account_key


def test_conversion_result_has_no_scoring_fanout_or_submission_fields() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    payload = asdict(result)
    forbidden = {
        "execution_plan",
        "child_intent_plan",
        "allocation_weights",
        "venue_ranking",
        "price_score",
        "quality_score",
        "confidence_score",
        "submitted_order_id",
        "prepared_venue_order_id",
        "execution_readiness_assessment_id",
        "submit_payload",
    }

    assert not (set(payload) & forbidden)
    assert result.provenance["fanout_created"] is False
    assert result.provenance["submitted_order_created"] is False
