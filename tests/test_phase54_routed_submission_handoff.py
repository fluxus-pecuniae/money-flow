from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    ExecutionReadinessOutcome,
    OrderIntentStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Venue,
    VenueSupportLevel,
)
from core.domain.models import SubmittedOrder
from db.models import (
    MandateAccountBindingModel,
    OrderIntentModel,
    RoutingTargetChoiceModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from services.execution.service import DefaultExecutionService, SubmissionBlockedError
from tests.test_phase3_strategy import build_settings, build_test_session_factory
from tests.test_phase42_execution_readiness import _StubVenueRegistry
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import _routing_assessment_with_trade
from tests.test_phase52_target_choice_conversion import _recorded_choice
from tests.test_phase53_routed_child_intent_readiness import _CountingVenueAdapter


class _RoutedSubmittingAdapter(_CountingVenueAdapter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.submitted_intents = []

    async def submit_order(self, intent):
        self.submit_calls += 1
        self.submitted_intents.append(intent)
        return SubmittedOrder(
            submitted_order_id=f"submitted-{intent.intent_id}",
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=self.venue,
            account_address=f"{self.venue}-acct",
            intent_id=intent.intent_id,
            client_order_id=f"client-{intent.intent_id}",
            exchange_order_id=f"exchange-{intent.intent_id}",
            status=SubmittedOrderStatus.ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            submitted_at=datetime.now(UTC),
            acknowledged_at=datetime.now(UTC),
            symbol=intent.symbol,
            side=intent.side,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            original_quantity=intent.quantity,
            remaining_quantity=intent.quantity,
            filled_quantity=None,
            average_fill_price=None,
            status_reason_code="acknowledged",
            status_message="Accepted by routed submission test adapter.",
            reason_codes=["submitted"],
            cancelable_in_principle=True,
            amendable_in_principle=True,
            reduce_only=intent.reduce_only,
            raw_payload={"adapter_submit_called": True},
        )


def _build_execution(
    session_factory,
    *,
    routed_submission_enabled: bool,
    live_submission_enabled: bool = True,
):
    settings = build_settings(
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=live_submission_enabled,
        EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED=routed_submission_enabled,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
    )
    adapter = _RoutedSubmittingAdapter(
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


def _execution_counts(session_factory) -> tuple[int, int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.status == SubmittedOrderStatus.ACKNOWLEDGED
                )
            ),
        )


def _intent_status(session_factory, intent_id: str) -> OrderIntentStatus:
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert intent is not None
        return intent.status


def test_routed_submission_disabled_preserves_phase_block_without_failed_intent_status() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=False)

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in readiness.reason_codes
    assert readiness.provenance["routed_submission_enabled"] is False

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)
    assert _intent_status(session_factory, result.intent_id) == OrderIntentStatus.PREPARED
    with session_factory() as session:
        stored = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert stored is not None
        block = stored.provenance["last_submission_block"]
        assert block["routed_submission_deferred"] is True
        assert block["live_submission_deferred"] is False
        assert block["routed_submission_enabled"] is False
        assert block["live_submission_enabled"] is True
        assert block["adapter_submit_called"] is False
        assert "last_submission_failure" not in stored.provenance


def test_routed_submit_blocked_by_live_gate_preserves_phase_block_status() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(
        session_factory,
        routed_submission_enabled=True,
        live_submission_enabled=False,
    )

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "phase_live_submit_deferred" in readiness.reason_codes
    assert "routed_submission_deferred" not in readiness.reason_codes
    assert readiness.provenance["routed_submission_enabled"] is True

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "phase_live_submit_deferred" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)
    assert _intent_status(session_factory, result.intent_id) == OrderIntentStatus.PREPARED
    with session_factory() as session:
        stored = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert stored is not None
        block = stored.provenance["last_submission_block"]
        assert "phase_live_submit_deferred" in block["reason_codes"]
        assert block["routed_submission_deferred"] is False
        assert block["live_submission_deferred"] is True
        assert block["routed_submission_enabled"] is True
        assert block["live_submission_enabled"] is False
        assert block["adapter_submit_called"] is False
        assert "last_submission_failure" not in stored.provenance


def test_routed_submit_with_both_gates_disabled_records_both_phase_deferrals() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(
        session_factory,
        routed_submission_enabled=False,
        live_submission_enabled=False,
    )

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in readiness.reason_codes
    assert "phase_live_submit_deferred" in readiness.reason_codes
    assert readiness.provenance["routed_submission_enabled"] is False
    assert readiness.live_submission_phase_enabled is False

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
    assert "routed_submission_deferred" in exc.value.readiness.reason_codes
    assert "phase_live_submit_deferred" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)
    assert _intent_status(session_factory, result.intent_id) == OrderIntentStatus.PREPARED
    with session_factory() as session:
        stored = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert stored is not None
        block = stored.provenance["last_submission_block"]
        assert "routed_submission_deferred" in block["reason_codes"]
        assert "phase_live_submit_deferred" in block["reason_codes"]
        assert block["routed_submission_deferred"] is True
        assert block["live_submission_deferred"] is True
        assert block["routed_submission_enabled"] is False
        assert block["live_submission_enabled"] is False
        assert block["adapter_submit_called"] is False
        assert "last_submission_failure" not in stored.provenance


def test_routed_preview_payload_reports_enabled_gate_truth_without_false_deferral() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, _adapter = _build_execution(session_factory, routed_submission_enabled=True)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))

    assert preview.payload is not None
    assert preview.payload["non_submitting"] is True
    assert preview.payload["explicit_submit_required"] is True
    assert preview.payload["routed_submission_enabled"] is True
    assert preview.payload["live_submission_enabled"] is True
    assert preview.payload["submission_deferred"] is False
    assert preview.payload["submission_deferred_reason_codes"] == []


def test_routed_preview_payload_reports_disabled_routed_gate_deferral() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, _adapter = _build_execution(session_factory, routed_submission_enabled=False)

    preview = asyncio.run(execution.preview_child_intent(result.intent_id))

    assert preview.payload is not None
    assert preview.payload["non_submitting"] is True
    assert preview.payload["explicit_submit_required"] is True
    assert preview.payload["routed_submission_enabled"] is False
    assert preview.payload["live_submission_enabled"] is True
    assert preview.payload["submission_deferred"] is True
    assert "routed_submission_deferred" in preview.payload["submission_deferred_reason_codes"]


def test_routed_submission_enabled_creates_one_submitted_order_with_route_lineage() -> None:
    session_factory = build_test_session_factory()
    _routing, assessment, choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)

    readiness = asyncio.run(execution.assess_child_intent_readiness(result.intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION
    assert "routed_submission_deferred" not in readiness.reason_codes
    assert readiness.provenance["routed_submission_enabled"] is True

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert submitted.intent_id == result.intent_id
    assert submitted.venue_account_ref_id == choice.selected_venue_account_ref_id
    assert submitted.raw_payload["routed_submission"]["routed_submission_enabled"] is True
    assert submitted.raw_payload["routed_submission"]["routing_assessment_id"] == assessment.assessment_id
    assert submitted.raw_payload["routed_submission"]["routing_target_choice_id"] == choice.target_choice_id
    assert submitted.raw_payload["routed_submission"]["selected_binding_ref_id"] == (
        choice.selected_binding_ref_id
    )
    assert submitted.raw_payload["routed_submission"]["selected_venue_account_ref_id"] == (
        choice.selected_venue_account_ref_id
    )
    assert adapter.submit_calls == 1
    assert len(adapter.submitted_intents) == 1
    assert _execution_counts(session_factory) == (1, 1, 1)


def test_routed_submission_enabled_still_blocks_provenance_drift_before_adapter_submit() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        provenance = dict(intent.provenance or {})
        provenance["selected_venue_account_ref_id"] = "stale-account-ref"
        intent.provenance = provenance
        session.commit()
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert exc.value.readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_POLICY
    assert "routed_provenance_venue_account_ref_mismatch" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_routed_submission_enabled_blocks_intent_and_target_choice_drift_before_submit() -> None:
    session_factory = build_test_session_factory()
    _routing, _assessment, choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        target_choice = session.scalar(
            select(RoutingTargetChoiceModel).where(
                RoutingTargetChoiceModel.target_choice_id == choice.target_choice_id,
            )
        )
        assert intent is not None
        assert target_choice is not None
        intent.client_ref_id = "stale-client-ref"
        intent.strategy_mandate_ref_id = "stale-mandate-ref"
        target_choice.desired_trade_key = "stale-desired-trade-key"
        session.commit()
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "intent_client_mismatch" in exc.value.readiness.reason_codes
    assert "intent_strategy_mandate_mismatch" in exc.value.readiness.reason_codes
    assert "routing_target_choice_desired_trade_key_mismatch" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_routed_submission_enabled_blocks_stale_target_and_changed_symbol_mapping() -> None:
    session_factory = build_test_session_factory()
    _routing, assessment, _choice, _desired_trade_key, _context, result = _converted_routed_child_intent(
        session_factory
    )
    candidate = assessment.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == candidate.instrument_ref_id,
                SymbolModel.venue == candidate.venue,
                SymbolModel.symbol == candidate.symbol,
            )
        )
        assert binding is not None
        assert account is not None
        assert symbol is not None
        binding.enabled = False
        account.is_active = False
        session.delete(symbol)
        session.commit()
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)

    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    with pytest.raises(SubmissionBlockedError) as exc:
        asyncio.run(execution.submit_prepared_intent(intent))

    assert "binding_disabled" in exc.value.readiness.reason_codes
    assert "venue_account_inactive" in exc.value.readiness.reason_codes
    assert "symbol_mapping_missing_or_changed" in exc.value.readiness.reason_codes
    assert adapter.submit_calls == 0
    assert _execution_counts(session_factory) == (1, 0, 0)


def test_same_venue_multi_account_routed_submission_uses_selected_account_only() -> None:
    session_factory = build_test_session_factory()
    routing, _initial_assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="phase54-secondary",
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
    conversion = asyncio.run(routing.convert_target_choice_to_child_intent(choice.target_choice_id))
    assert conversion.status == RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert adapter.submit_calls == 1
    assert adapter.submitted_intents[0].venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert submitted.venue_account_ref_id == selected_candidate.venue_account_ref_id
    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.venue_account_ref_id == other_candidate.venue_account_ref_id
                )
            )
            == 0
        )


def test_api_routed_submit_reports_gate_block_and_success_truthfully() -> None:
    disabled_session_factory = build_test_session_factory()
    _routing, _assessment, _choice, _desired_trade_key, _context, disabled_result = (
        _converted_routed_child_intent(disabled_session_factory)
    )
    disabled_execution, disabled_adapter = _build_execution(
        disabled_session_factory,
        routed_submission_enabled=False,
    )
    app.dependency_overrides[get_execution_service] = lambda: disabled_execution
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/child-intents/{disabled_result.intent_id}/submit")
    finally:
        app.dependency_overrides.pop(get_execution_service, None)
    assert response.status_code == 409
    assert response.json()["detail"]["outcome"] == ExecutionReadinessOutcome.PHASE_BLOCKED.value
    assert "routed_submission_deferred" in response.json()["detail"]["reason_codes"]
    assert disabled_adapter.submit_calls == 0

    enabled_session_factory = build_test_session_factory()
    _routing, _assessment, choice, _desired_trade_key, _context, enabled_result = (
        _converted_routed_child_intent(enabled_session_factory)
    )
    enabled_execution, enabled_adapter = _build_execution(
        enabled_session_factory,
        routed_submission_enabled=True,
    )
    app.dependency_overrides[get_execution_service] = lambda: enabled_execution
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/child-intents/{enabled_result.intent_id}/submit")
    finally:
        app.dependency_overrides.pop(get_execution_service, None)
    assert response.status_code == 200
    payload = response.json()
    assert payload["venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert payload["raw_payload"]["routed_submission"]["routed_submission_enabled"] is True
    assert enabled_adapter.submit_calls == 1
