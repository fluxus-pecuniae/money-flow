from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    ExecutionReadinessOutcome,
    OrderType,
    RoutingTargetChoiceConversionStatus,
    VenueOrderPreviewStatus,
)
from core.domain.models import RoutedOrderShapePolicyInput
from db.models import (
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase53_routed_child_intent_readiness import _build_execution
from tests.test_phase600_routing_target_recommendation import (
    _mutate_ready_candidate_quote_observed_at,
)
from tests.test_phase63_recommendation_target_choice_conversion import _accepted_choice


client = TestClient(app)


def _artifact_counts(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {
            "child_intents": session.scalar(select(func.count()).select_from(OrderIntentModel)),
            "readiness": session.scalar(
                select(func.count()).select_from(ExecutionReadinessEvaluationModel)
            ),
            "submitted_orders": session.scalar(
                select(func.count()).select_from(SubmittedOrderModel)
            ),
        }


def _recommendation_backed_child_intent(session_factory, *, policy_input=None):
    routing, audit, recommendation, choice, desired_trade_key = _accepted_choice(session_factory)
    result = asyncio.run(
        routing.convert_target_choice_to_child_intent(
            choice.target_choice_id,
            policy_input,
        )
    )
    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.intent_id is not None
    return routing, audit, recommendation, choice, desired_trade_key, result


def _assert_no_submission_boundary(session_factory, *, child_intents: int, readiness: int) -> None:
    counts = _artifact_counts(session_factory)
    assert counts["child_intents"] == child_intents
    assert counts["readiness"] == readiness
    assert counts["submitted_orders"] == 0


def test_recommendation_backed_child_intent_uses_existing_preview_and_readiness_paths() -> None:
    session_factory = build_test_session_factory()
    _routing, audit, recommendation, choice, _desired_trade_key, result = (
        _recommendation_backed_child_intent(session_factory)
    )
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in readiness.reason_codes
    assert adapter.prepare_calls == 2
    assert adapter.submit_calls == 0
    preview_lineage = preview.payload["routed_lineage"]
    readiness_lineage = readiness.provenance["routed_lineage"]
    for lineage in (preview_lineage, readiness_lineage):
        assert lineage["recommendation_backed_child_intent"] is True
        assert lineage["routing_target_recommendation_id"] == (
            recommendation.routing_target_recommendation_id
        )
        assert lineage["route_readiness_audit_id"] == audit.route_readiness_audit_id
        assert lineage["routing_target_choice_id"] == choice.target_choice_id
        assert lineage["selected_binding_ref_id"] == choice.selected_binding_ref_id
        assert lineage["selected_binding_key"] == choice.selected_binding_key
        assert lineage["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
        assert lineage["selected_venue_account_key"] == choice.selected_venue_account_key
        assert lineage["selected_venue"] == choice.selected_venue
        assert lineage["selected_exchange_symbol"] == audit.candidates[0].exchange_symbol
        assert lineage["recommendation_policy_name"] == recommendation.policy_name
        assert lineage["valid"] is True
        assert lineage["submitted_order_created"] is False
        assert lineage["auto_submit"] is False
        assert lineage["fanout_created"] is False
        assert lineage["allocation_created"] is False
        assert lineage["scoring_created"] is False
        assert lineage["target_reselection"] is False
        assert "routed_order_shape_policy_defaulted" in (
            lineage["routed_order_shape_policy"]["reason_codes"]
        )
    _assert_no_submission_boundary(session_factory, child_intents=1, readiness=1)


def test_recommendation_backed_readiness_blocks_current_truth_drift_before_adapter_preview() -> None:
    session_factory = build_test_session_factory()
    _routing, audit, _recommendation, choice, _desired_trade_key, result = (
        _recommendation_backed_child_intent(session_factory)
    )
    ready_candidate = audit.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, choice.selected_binding_ref_id)
        account = session.get(VenueAccountModel, choice.selected_venue_account_ref_id)
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == ready_candidate.instrument_ref_id,
                SymbolModel.venue == ready_candidate.venue,
                SymbolModel.symbol == ready_candidate.symbol,
                SymbolModel.exchange_symbol == ready_candidate.exchange_symbol,
            )
        )
        assert binding is not None
        assert account is not None
        assert symbol is not None
        binding.enabled = False
        account.is_active = False
        symbol.is_active = False
        symbol.is_trading_eligible = False
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    expected = {
        "binding_disabled",
        "venue_account_inactive",
        "symbol_inactive",
        "symbol_not_trading_eligible",
        "routed_lineage_invalid",
    }
    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert expected.issubset(set(preview.reason_codes))
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert expected.issubset(set(readiness.reason_codes))
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    _assert_no_submission_boundary(session_factory, child_intents=1, readiness=1)


def test_recommendation_backed_readiness_blocks_stale_quote_observation() -> None:
    session_factory = build_test_session_factory()
    _routing, audit, _recommendation, _choice, _desired_trade_key, result = (
        _recommendation_backed_child_intent(session_factory)
    )
    ready_candidate = audit.candidates[0]
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=ready_candidate.binding_key,
    )
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "quote_stale_at_recommendation" in preview.reason_codes
    assert "quote_stale_at_recommendation" in readiness.reason_codes
    assert readiness.provenance["routed_lineage"]["stale_data"] == [
        "quote_stale_at_recommendation"
    ]
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    _assert_no_submission_boundary(session_factory, child_intents=1, readiness=1)


def test_recommendation_backed_explicit_limit_policy_reaches_readiness_when_valid() -> None:
    session_factory = build_test_session_factory()
    _routing, _audit, _recommendation, _choice, _desired_trade_key, result = (
        _recommendation_backed_child_intent(
            session_factory,
            policy_input=RoutedOrderShapePolicyInput(
                order_type=OrderType.LIMIT,
                limit_price=Decimal("101.25"),
                policy_source="operator_requested",
                requested_by="phase_6_4_test_operator",
            ),
        )
    )
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert preview.order_type == OrderType.LIMIT
    assert preview.limit_price == Decimal("101.250000000000")
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    lineage = readiness.provenance["routed_lineage"]
    assert lineage["routed_order_shape_policy"]["order_type"] == "limit"
    assert lineage["routed_order_shape_policy"]["limit_price"] == "101.25"
    assert "limit_price_explicit" in lineage["routed_order_shape_policy"]["reason_codes"]
    assert adapter.submit_calls == 0
    _assert_no_submission_boundary(session_factory, child_intents=1, readiness=1)


def test_preview_and_readiness_api_expose_recommendation_lineage_without_submission() -> None:
    session_factory = build_test_session_factory()
    _routing, audit, recommendation, choice, _desired_trade_key, result = (
        _recommendation_backed_child_intent(session_factory)
    )
    execution, adapter = _build_execution(session_factory)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        preview_response = client.get(
            f"/api/v1/child-intents/{result.intent_id}/prepared-order-preview"
        )
        readiness_response = client.get(
            f"/api/v1/child-intents/{result.intent_id}/submission-readiness"
        )
    finally:
        app.dependency_overrides.clear()

    assert preview_response.status_code == 200
    assert readiness_response.status_code == 200
    preview_payload = preview_response.json()
    readiness_payload = readiness_response.json()
    for payload in (preview_payload, readiness_payload):
        lineage = payload["routed_lineage"]
        assert lineage["routing_target_recommendation_id"] == (
            recommendation.routing_target_recommendation_id
        )
        assert lineage["route_readiness_audit_id"] == audit.route_readiness_audit_id
        assert lineage["routing_target_choice_id"] == choice.target_choice_id
        assert lineage["selected_binding_key"] == choice.selected_binding_key
        assert lineage["selected_venue_account_key"] == choice.selected_venue_account_key
        assert lineage["selected_venue"] == choice.selected_venue
        assert lineage["recommendation_backed_child_intent"] is True
        assert lineage["submitted_order_created"] is False
        assert lineage["auto_submit"] is False
        assert lineage["fanout_created"] is False
        assert lineage["allocation_created"] is False
        assert lineage["scoring_created"] is False
        assert lineage["target_reselection"] is False
    assert readiness_payload["outcome"] == ExecutionReadinessOutcome.PHASE_BLOCKED.value
    assert adapter.submit_calls == 0
    _assert_no_submission_boundary(session_factory, child_intents=1, readiness=1)
