from __future__ import annotations

import asyncio
from dataclasses import asdict

import pytest
from sqlalchemy import func, select

from core.domain.enums import (
    Environment,
    ExecutionReadinessOutcome,
    MandateDesiredTradeStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
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
from services.execution.service import DefaultExecutionService, SubmissionBlockedError
from tests.test_phase3_strategy import build_settings, build_test_session_factory
from tests.test_phase42_execution_readiness import _StubVenueAdapter, _StubVenueRegistry
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import _routing_assessment_with_trade
from tests.test_phase52_target_choice_conversion import _recorded_choice


class _CountingVenueAdapter(_StubVenueAdapter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prepare_calls = 0
        self.submit_calls = 0

    async def prepare_order_preview(self, intent):
        self.prepare_calls += 1
        return await super().prepare_order_preview(intent)

    async def submit_order(self, intent):
        self.submit_calls += 1
        raise AssertionError("Routed child-intent submit must stay blocked before adapter submission.")


def _execution_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _build_execution(session_factory):
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
    )
    adapter = _CountingVenueAdapter(
        venue=Venue.HYPERLIQUID.value,
        support_level=VenueSupportLevel.LIVE_ENABLED,
        adapter_supports_submission=True,
        adapter_supports_order_cancel=True,
        adapter_supports_order_amend=True,
        submission_authorized=True,
        read_only_mode=False,
        dry_run_mode=False,
        private_state_available=True,
        private_account_sync_enabled=True,
    )
    return (
        DefaultExecutionService(
            settings,
            session_factory=session_factory,
            venue_registry_service=_StubVenueRegistry({Venue.HYPERLIQUID.value: adapter}),
        ),
        adapter,
    )


def _converted_routed_child_intent(session_factory):
    routing, assessment, choice, desired_trade_key, context = _recorded_choice(session_factory)
    result = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    assert result.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    assert result.intent_id is not None
    return routing, assessment, choice, desired_trade_key, context, result


def test_converted_routed_child_intent_can_preview_existing_preparation_path() -> None:
    session_factory = build_test_session_factory()
    _routing, assessment, choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert preview.venue == Venue.HYPERLIQUID.value
    assert preview.venue_account_ref_id == choice.selected_venue_account_ref_id
    assert adapter.prepare_calls == 1
    assert preview.payload is not None
    assert preview.payload["non_submitting"] is True
    lineage = preview.payload["routed_lineage"]
    assert lineage["routing_assessment_id"] == assessment.assessment_id
    assert lineage["routing_target_choice_id"] == choice.target_choice_id
    assert lineage["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert lineage["valid"] is True
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_converted_routed_child_intent_can_assess_readiness_without_submission() -> None:
    session_factory = build_test_session_factory()
    _routing, assessment, choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(session_factory)

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in readiness.reason_codes
    assert readiness.preview_status == VenueOrderPreviewStatus.PREPARABLE
    assert readiness.provenance["prepared_order_preview"]["preview_status"] == "preparable"
    assert readiness.provenance["phase_boundary"] == "phase_5_3_routed_preparation_readiness"
    assert readiness.provenance["routed_submission_deferred"] is True
    assert readiness.provenance["routed_lineage"]["routing_assessment_id"] == assessment.assessment_id
    assert readiness.provenance["routed_lineage"]["routing_target_choice_id"] == choice.target_choice_id
    assert readiness.provenance["submitted_order_created"] is False
    assert adapter.prepare_calls == 1
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_stale_desired_trade_status_blocks_routed_preview_and_readiness() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key,
            )
        )
        assert desired_trade is not None
        desired_trade.status = MandateDesiredTradeStatus.CANCELED
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "desired_trade_not_routed" in preview.reason_codes
    assert "routed_lineage_invalid" in preview.reason_codes
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "desired_trade_not_routed" in readiness.reason_codes
    assert adapter.prepare_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_stale_binding_and_account_block_routed_preview_and_readiness() -> None:
    session_factory = build_test_session_factory()
    _routing, assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    candidate = assessment.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        assert binding is not None
        assert account is not None
        binding.enabled = False
        account.is_active = False
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "binding_disabled" in preview.reason_codes
    assert "venue_account_inactive" in preview.reason_codes
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "binding_disabled" in readiness.reason_codes
    assert "venue_account_inactive" in readiness.reason_codes
    assert adapter.prepare_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_mismatched_route_lineage_blocks_routed_preview_and_readiness() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        provenance = dict(intent.provenance or {})
        provenance["routing_assessment_id"] = "rtassess-missing"
        provenance["routing_target_choice_id"] = "rtchoice-missing"
        intent.provenance = provenance
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "routing_assessment_not_found" in preview.reason_codes
    assert "routing_target_choice_not_found" in preview.reason_codes
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "routing_assessment_not_found" in readiness.reason_codes
    assert "routing_target_choice_not_found" in readiness.reason_codes
    assert adapter.prepare_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_provenance_selected_target_drift_blocks_before_adapter_preparation() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        provenance = dict(intent.provenance or {})
        provenance["selected_binding_ref_id"] = "stale-binding-ref"
        provenance["selected_binding_key"] = "stale-binding-key"
        provenance["selected_venue_account_ref_id"] = "stale-account-ref"
        provenance["selected_venue_account_key"] = "stale-account-key"
        provenance["selected_venue"] = Venue.BINANCE.value
        provenance["selected_exchange_symbol"] = "BTCUSDT_STALE"
        intent.provenance = provenance
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    expected_reason_codes = {
        "routed_provenance_binding_ref_mismatch",
        "routed_provenance_binding_key_mismatch",
        "routed_provenance_venue_account_ref_mismatch",
        "routed_provenance_venue_account_key_mismatch",
        "routed_provenance_venue_mismatch",
        "routed_provenance_exchange_symbol_mismatch",
    }
    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert expected_reason_codes.issubset(set(preview.reason_codes))
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert expected_reason_codes.issubset(set(readiness.reason_codes))
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_intent_client_and_mandate_drift_blocks_before_adapter_preparation() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        intent.client_ref_id = "stale-client-ref"
        intent.strategy_mandate_ref_id = "stale-mandate-ref"
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "intent_client_mismatch" in preview.reason_codes
    assert "intent_strategy_mandate_mismatch" in preview.reason_codes
    assert "venue_account_client_mismatch" in preview.reason_codes
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "intent_client_mismatch" in readiness.reason_codes
    assert "intent_strategy_mandate_mismatch" in readiness.reason_codes
    assert "venue_account_client_mismatch" in readiness.reason_codes
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_target_choice_desired_trade_drift_blocks_before_adapter_preparation() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        target_choice = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert target_choice is not None
        target_choice.desired_trade_ref_id = "stale-desired-trade-ref"
        target_choice.desired_trade_key = "stale-desired-trade-key"
        session.commit()
    execution, adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))

    assert preview.preview_status == VenueOrderPreviewStatus.REJECTED
    assert "routing_target_choice_desired_trade_ref_mismatch" in preview.reason_codes
    assert "routing_target_choice_desired_trade_key_mismatch" in preview.reason_codes
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "routing_target_choice_desired_trade_ref_mismatch" in readiness.reason_codes
    assert "routing_target_choice_desired_trade_key_mismatch" in readiness.reason_codes
    assert adapter.prepare_calls == 0
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_explicit_routed_submit_remains_blocked_before_adapter_submission() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(session_factory)
    intent = asyncio.run(execution.get_child_intent(result.intent_id))

    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in exc.value.readiness.reason_codes
    assert adapter.prepare_calls == 1
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_same_venue_multi_account_routed_readiness_uses_selected_account_only() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="phase53-secondary",
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    selected_candidate = next(
        candidate for candidate in assessment.candidates if candidate.binding_key == second_binding_key
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
    execution, _adapter = _build_execution(session_factory)

    preview = asyncio.run(execution.preview_child_intent(conversion.intent_id))
    readiness = asyncio.run(execution.assess_child_intent_readiness(conversion.intent_id))

    assert preview.venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert preview.binding_key == selected_candidate.binding_key
    assert readiness.venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert readiness.binding_key == selected_candidate.binding_key
    assert readiness.provenance["routed_lineage"]["selected_venue_account_ref_id"] == (
        selected_candidate.venue_account_ref_id
    )
    assert _execution_counts(session_factory) == (1, 1, 0)


def test_routed_readiness_payload_has_no_routing_execution_fields() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, _adapter = _build_execution(session_factory)

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))
    payload = asdict(readiness)
    preview_payload = readiness.prepared_order.payload if readiness.prepared_order is not None else {}
    forbidden = {
        "execution_plan",
        "child_intent_plan",
        "allocation_weights",
        "venue_ranking",
        "price_score",
        "quality_score",
        "confidence_score",
        "submitted_order_id",
        "submit_payload",
        "route_executor",
    }

    assert not (set(payload) & forbidden)
    assert not (set(preview_payload or {}) & forbidden)
    assert readiness.provenance["auto_submit"] is False
    assert readiness.provenance["fanout_created"] is False
    assert readiness.provenance["scoring_created"] is False
    assert readiness.provenance["target_reselection"] is False
    assert _execution_counts(session_factory) == (1, 1, 0)
