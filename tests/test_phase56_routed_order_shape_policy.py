from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.domain.enums import (
    MandateDesiredTradeStatus,
    OrderType,
    RoutingTargetChoiceConversionStatus,
)
from core.domain.models import RoutedOrderShapePolicyInput
from db.models import OrderIntentModel, RoutingAssessmentCandidateModel
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase52_target_choice_conversion import (
    _desired_trade_status,
    _execution_counts,
    _recorded_choice,
)


def _converted_order_intent(session_factory):
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)
    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.intent_id is not None
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id)
        )
        assert intent is not None
        return result, intent


def test_default_routed_conversion_uses_policy_backed_market_order_shape() -> None:
    session_factory = build_test_session_factory()

    result, intent = _converted_order_intent(session_factory)

    assert intent.order_type == OrderType.MARKET
    assert intent.limit_price is None
    assert intent.reduce_only is False
    policy = intent.provenance["routed_order_shape_policy"]
    assert policy["phase"] == "phase_5_8"
    assert policy["policy_scope"] == "routed_target_choice_conversion_open"
    assert policy["policy_source"] == "current_default"
    assert policy["requested_order_type"] is None
    assert policy["requested_limit_price"] is None
    assert policy["requested_reduce_only"] is None
    assert policy["order_type"] == OrderType.MARKET.value
    assert policy["limit_price"] is None
    assert policy["reduce_only"] is False
    assert "routed_order_shape_policy_defaulted" in policy["reason_codes"]
    assert "market_order_default_current_phase" in policy["reason_codes"]
    assert "routed_order_shape_policy_accepted" in policy["reason_codes"]
    assert "slippage_guard_deferred" in policy["warnings"]
    assert result.provenance["routed_order_shape_policy"] == policy


def test_routed_conversion_idempotency_preserves_order_shape_policy() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    second = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 1
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == first.intent_id)
        )
        assert intent is not None
        assert intent.provenance["routed_order_shape_policy"] == (
            second.provenance["routed_order_shape_policy"]
        )


def test_explicit_market_policy_is_idempotent_with_default_market_shape() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    second = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.MARKET,
                policy_source="operator_requested",
                requested_by="operator@example.test",
            ),
        )
    )

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    assert "conversion_order_shape_policy_mismatch" not in second.reason_codes
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_current_open_routed_conversion_keeps_reduce_only_false_by_policy() -> None:
    session_factory = build_test_session_factory()

    _result, intent = _converted_order_intent(session_factory)

    policy = intent.provenance["routed_order_shape_policy"]
    assert intent.reduce_only is False
    assert policy["reduce_only"] is False
    assert "reduce_only_false_for_open" in policy["reason_codes"]


def test_explicit_market_policy_rejects_ambiguous_limit_price() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.MARKET,
                limit_price=Decimal("101"),
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "market_order_limit_price_not_allowed" in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    assert result.provenance["routed_order_shape_policy"]["blocked"] is True
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_explicit_limit_policy_with_positive_price_creates_limit_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("101.25"),
                policy_source="operator_requested",
                requested_by="operator@example.test",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.intent_id is not None
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id)
        )
        assert intent is not None
        assert intent.order_type == OrderType.LIMIT
        assert intent.limit_price == Decimal("101.250000000000")
        assert intent.reduce_only is False
        policy = intent.provenance["routed_order_shape_policy"]
    assert policy["policy_source"] == "operator_requested"
    assert policy["requested_order_type"] == OrderType.LIMIT.value
    assert policy["requested_limit_price"] == "101.25"
    assert policy["order_type"] == OrderType.LIMIT.value
    assert policy["limit_price"] == "101.25"
    assert policy["requested_by"] == "operator@example.test"
    assert "limit_order_requested" in policy["reason_codes"]
    assert "limit_price_explicit" in policy["reason_codes"]
    assert "routed_order_shape_policy_accepted" in policy["reason_codes"]
    assert result.provenance["routed_order_shape_policy"] == policy
    assert _execution_counts(session_factory) == (1, 0, 0)


@pytest.mark.parametrize(
    ("limit_price", "expected_reason"),
    [
        (None, "limit_price_missing"),
        (Decimal("0"), "invalid_limit_price"),
        (Decimal("-1"), "invalid_limit_price"),
        ("not-a-price", "malformed_limit_price"),
    ],
)
def test_invalid_limit_policy_blocks_before_child_intent_creation(
    limit_price,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=limit_price,
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert expected_reason in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    if expected_reason == "malformed_limit_price":
        assert "limit_price_explicit" not in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


@pytest.mark.parametrize(
    "limit_price",
    [
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
    ],
)
def test_non_finite_limit_policy_blocks_without_exception(limit_price) -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=limit_price,
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "malformed_limit_price" in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    assert "limit_price_explicit" not in result.reason_codes
    assert result.provenance["routed_order_shape_policy"]["blocked"] is True
    assert "limit_price_explicit" not in result.provenance["routed_order_shape_policy"]["reason_codes"]
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_unsupported_order_type_blocks_before_child_intent_creation() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.STOP,
                limit_price=Decimal("101"),
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "unsupported_routed_order_type" in result.reason_codes
    assert "routed_order_shape_policy_blocked" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_limit_policy_blocks_when_candidate_order_type_support_excludes_limit() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)
    with session_factory() as session:
        candidate = session.scalar(
            select(RoutingAssessmentCandidateModel).where(
                RoutingAssessmentCandidateModel.assessment_id == choice.routing_assessment_id,
                RoutingAssessmentCandidateModel.binding_key == choice.selected_binding_key,
            )
        )
        assert candidate is not None
        facts = dict(candidate.fact_snapshot_json or {})
        facts["supported_order_types"] = [OrderType.MARKET.value]
        candidate.fact_snapshot_json = facts
        session.commit()

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("101.25"),
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "unsupported_routed_order_type" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_reduce_only_true_is_blocked_for_routed_open_conversion() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, desired_trade_key, _context = _recorded_choice(session_factory)

    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.MARKET,
                reduce_only=True,
                policy_source="operator_requested",
            ),
        )
    )

    assert result.status == RoutingTargetChoiceConversionStatus.BLOCKED_ORDER_SHAPE_POLICY
    assert "reduce_only_not_allowed_for_open" in result.reason_codes
    assert _execution_counts(session_factory) == (0, 0, 0)
    assert _desired_trade_status(session_factory, desired_trade_key) == (
        MandateDesiredTradeStatus.ROUTING_REQUIRED
    )


def test_policy_mismatch_after_conversion_does_not_create_second_child_intent() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, choice, _desired_trade_key, _context = _recorded_choice(session_factory)

    first = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    second = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("101.25"),
                policy_source="operator_requested",
            ),
        )
    )

    assert first.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert second.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS
    assert second.intent_id == first.intent_id
    assert "conversion_order_shape_policy_mismatch" in second.reason_codes
    assert "existing_child_intent_order_shape_preserved" in second.reason_codes
    assert _execution_counts(session_factory) == (1, 0, 0)
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == first.intent_id)
        )
        assert intent is not None
        assert intent.order_type == OrderType.MARKET
        assert intent.limit_price is None


def test_limit_routed_order_shape_policy_v2_is_documented_with_slippage_deferred() -> None:
    known_issues = Path("KNOWN_ISSUES.md").read_text()
    todo = Path("TODO.md").read_text()

    assert "explicit LIMIT routed order-shape policy input" in known_issues
    assert "slippage guard" in known_issues
    assert "slippage expansion" in todo
