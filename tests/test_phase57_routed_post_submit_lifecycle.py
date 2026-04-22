from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    OrderSide,
    OrderType,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Venue,
)
from core.domain.models import (
    SubmittedOrder,
    SubmittedOrderPrivateFillEvidence,
    VenueCapabilities,
)
from db.models import OrderIntentModel, SubmittedOrderModel
from tests.test_phase3_strategy import build_test_session_factory
from tests.test_phase45_execution_lifecycle import (
    _build_okx_execution_service,
    _mark_submitted_order_retryable_rejected,
    _seed_okx_submitted_order,
)
from tests.test_phase50_routing_substrate import _seed_second_hyperliquid_binding
from tests.test_phase51_routing_target_choice import _routing_assessment_with_trade
from tests.test_phase54_routed_submission_handoff import (
    _build_execution,
    _converted_routed_child_intent,
)


def _submit_routed_child_intent(session_factory):
    _routing, assessment, choice, _desired_trade_key, _context, result = (
        _converted_routed_child_intent(session_factory)
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    intent = asyncio.run(execution.get_child_intent(result.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    return execution, adapter, assessment, choice, result, submitted


def _api_get_json(execution, path: str, *, params: dict[str, object] | None = None):
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        with TestClient(app) as client:
            response = client.get(path, params=params)
    finally:
        app.dependency_overrides.pop(get_execution_service, None)
    assert response.status_code == 200
    return response.json()


def _execution_counts(session_factory) -> tuple[int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def _hyperliquid_capabilities(adapter) -> VenueCapabilities:
    return VenueCapabilities(
        venue=Venue(adapter.venue),
        support_level=adapter.support_level,
        supports_spot=False,
        supports_perpetuals=True,
        supports_futures=False,
        supports_options=False,
        supports_hedge_mode=False,
        supports_websocket_market_data=True,
        supports_user_streams=False,
        supports_account_sync=True,
        supports_top_of_book=True,
        supports_depth_summary=False,
        supports_order_submission=True,
        supports_order_cancel=True,
        supports_order_amend=True,
        supports_recent_fills_query=False,
        adapter_supports_order_submission=True,
        adapter_supports_order_cancel=True,
        adapter_supports_order_amend=True,
        adapter_supports_user_streams=False,
        supports_order_preview=True,
        supports_account_snapshot=True,
        supports_open_orders_query=True,
        supports_open_positions_query=True,
        supports_reduce_only_orders=True,
        supports_client_order_ids=True,
        supports_demo_mode=True,
        supports_subaccounts=False,
        account_model="wallet_address",
        supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
        supported_time_in_force=["gtc", "ioc"],
        notes=None,
        private_lifecycle_update_mode="polling",
    )


def _enable_actionability_capabilities(adapter) -> None:
    async def get_venue_capabilities() -> VenueCapabilities:
        return _hyperliquid_capabilities(adapter)

    adapter.get_venue_capabilities = get_venue_capabilities


def _allow_same_target_retry_private_checks(adapter) -> None:
    async def fetch_open_orders_with_source(venue_account_ref_id: str | None = None):
        return ("venue_query", [])

    async def fetch_retry_private_fill_evidence(submitted_order, *, limit: int = 100):
        return SubmittedOrderPrivateFillEvidence(
            source="venue_query",
            evidence_scope="order_scoped",
            fills=[],
            message="No private fills matched the retry target.",
        )

    async def submit_order(intent):
        adapter.submit_calls += 1
        adapter.submitted_intents.append(intent)
        return SubmittedOrder(
            submitted_order_id=f"submitted-retry-{intent.intent_id}",
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=adapter.venue,
            account_address=f"{adapter.venue}-acct",
            intent_id=intent.intent_id,
            client_order_id=f"client-retry-{intent.intent_id}",
            exchange_order_id=f"exchange-retry-{intent.intent_id}",
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
            status_message="Accepted by routed retry test adapter.",
            reason_codes=["submitted"],
            cancelable_in_principle=True,
            amendable_in_principle=True,
            reduce_only=intent.reduce_only,
            raw_payload={"adapter_submit_called": True, "retry_same_target": True},
        )

    adapter.fetch_open_orders_with_source = fetch_open_orders_with_source
    adapter.fetch_retry_private_fill_evidence = fetch_retry_private_fill_evidence
    adapter.submit_order = submit_order


def _insert_hyperliquid_submitted_order(
    session_factory,
    *,
    submitted_order_id: str,
    raw_payload: dict[str, object],
    venue_account_ref_id: str = "venue-account-hl-phase57",
) -> str:
    with session_factory() as session:
        model = SubmittedOrderModel(
            environment=Environment.TESTNET,
            submitted_order_id=submitted_order_id,
            intent_id=f"intent-{submitted_order_id}",
            client_order_id=f"client-{submitted_order_id}",
            venue_account_ref_id=venue_account_ref_id,
            venue=Venue.HYPERLIQUID.value,
            account_address="hl-phase57-account",
            instrument_ref_id=None,
            symbol_id=None,
            symbol="BTC",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            limit_price=None,
            original_quantity=Decimal("0.01"),
            remaining_quantity=Decimal("0.01"),
            reduce_only=False,
            exchange_order_id=f"exchange-{submitted_order_id}",
            status=SubmittedOrderStatus.ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            submitted_at=datetime.now(UTC),
            acknowledged_at=datetime.now(UTC),
            filled_quantity=None,
            average_fill_price=None,
            last_fill_at=None,
            last_reconciled_at=None,
            status_reason_code="acknowledged",
            status_message="Seeded submitted order for Phase 5.7.",
            reason_codes=["submitted"],
            cancelable_in_principle=True,
            amendable_in_principle=False,
            raw_payload=raw_payload,
        )
        session.add(model)
        session.commit()
    return submitted_order_id


def test_routed_submitted_order_detail_and_list_expose_lifecycle_context() -> None:
    session_factory = build_test_session_factory()
    execution, _adapter, assessment, choice, _result, submitted = _submit_routed_child_intent(
        session_factory
    )
    normal_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase57-normal",
        raw_payload={"adapter_submit_called": True},
    )

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
    listed = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    listed_detail = next(item for item in listed if item["submitted_order_id"] == submitted.submitted_order_id)
    normal_detail = next(item for item in listed if item["submitted_order_id"] == normal_id)

    for payload in (detail, listed_detail):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        assert context["routed_origin"] is True
        assert context["desired_trade_key"] == submitted.raw_payload["routed_submission"]["desired_trade_key"]
        assert context["routing_assessment_id"] == assessment.assessment_id
        assert context["routing_target_choice_id"] == choice.target_choice_id
        assert context["selected_binding_ref_id"] == choice.selected_binding_ref_id
        assert context["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
        assert context["selected_venue"] == choice.selected_venue
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True
        assert context["auto_submit"] is False
        assert context["fanout_created"] is False
        assert context["target_reselection"] is False
        assert "routed_recovery_same_target_only" in context["boundary_reason_codes"]
        assert context["routed_order_shape_policy"]["phase"] == "phase_5_8"
        assert context["routed_order_shape_policy"]["order_type"] == OrderType.MARKET.value

    assert normal_detail["routed_origin"] is False
    assert normal_detail["routed_lineage"] is None
    assert normal_detail["routed_lifecycle_context"] is None


def test_routed_actionability_and_recovery_expose_same_target_context_without_new_records() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, _assessment, choice, _result, submitted = _submit_routed_child_intent(
        session_factory
    )
    _enable_actionability_capabilities(adapter)
    before_counts = _execution_counts(session_factory)

    actionability = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/actionability",
    )
    recovery = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/recovery",
    )

    for payload in (actionability, recovery):
        context = payload["routed_lifecycle_context"]
        assert payload["routed_origin"] is True
        assert context["selected_binding_ref_id"] == choice.selected_binding_ref_id
        assert context["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
        assert context["selected_venue"] == choice.selected_venue
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True
        assert context["auto_submit"] is False
        assert context["fanout_created"] is False
        assert context["target_reselection"] is False
        assert context["routed_order_shape_policy"]["reduce_only"] is False

    assert actionability["venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert recovery["venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert "routed_recovery_same_target_only" in recovery["reason_codes"]
    assert _execution_counts(session_factory) == before_counts


def test_malformed_routed_lifecycle_context_is_bounded_on_actionability_and_recovery() -> None:
    session_factory = build_test_session_factory()
    malformed_id = _insert_hyperliquid_submitted_order(
        session_factory,
        submitted_order_id="submitted-phase57-malformed-routed",
        raw_payload={
            "routed_submission": {
                "routing_assessment_id": 57,
                "routing_target_choice_id": "choice-phase57",
                "selected_venue_account_ref_id": "venue-account-hl-phase57",
                "auto_submit": "false",
                "routed_order_shape_policy": "not-a-policy-payload",
            }
        },
    )
    execution, adapter = _build_execution(session_factory, routed_submission_enabled=True)
    _enable_actionability_capabilities(adapter)
    before_counts = _execution_counts(session_factory)

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{malformed_id}")
    actionability = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{malformed_id}/actionability",
    )
    recovery = _api_get_json(execution, f"/api/v1/submitted-orders/{malformed_id}/recovery")

    for payload in (detail, actionability, recovery):
        context = payload["routed_lifecycle_context"]
        assert context["route_lineage_malformed"] is True
        assert "routing_assessment_id" in context["malformed_lineage_fields"]
        assert "auto_submit" in context["malformed_lineage_fields"]
        assert "routed_order_shape_policy" in context["malformed_lineage_fields"]
        assert "desired_trade_key" in context["missing_lineage_fields"]
        assert "routed_lineage_malformed" in context["boundary_reason_codes"]
        assert context["same_target_only"] is True
        assert context["same_account_only"] is True
        assert context["same_venue_only"] is True

    assert "routed_order_shape_policy" in detail["routed_lineage"]["malformed_lineage_fields"]
    assert _execution_counts(session_factory) == before_counts


def test_same_venue_multi_account_routed_post_submit_context_uses_selected_account_only() -> None:
    session_factory = build_test_session_factory()
    routing, _initial_assessment, desired_trade_key, context = _routing_assessment_with_trade(session_factory)
    second_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
        suffix="phase57-secondary",
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
    _enable_actionability_capabilities(adapter)

    intent = asyncio.run(execution.get_child_intent(conversion.intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    before_counts = _execution_counts(session_factory)
    actionability = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/actionability",
    )
    recovery = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}/recovery",
    )

    assert actionability["venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert recovery["venue_account_ref_id"] == selected_candidate.venue_account_ref_id
    assert actionability["routed_lifecycle_context"]["selected_venue_account_ref_id"] == (
        selected_candidate.venue_account_ref_id
    )
    assert recovery["routed_lifecycle_context"]["selected_binding_ref_id"] == (
        selected_candidate.binding_ref_id
    )
    assert adapter.submitted_intents[0].venue_account_ref_id == selected_candidate.venue_account_ref_id
    assert _execution_counts(session_factory) == before_counts
    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SubmittedOrderModel).where(
                    SubmittedOrderModel.venue_account_ref_id == other_candidate.venue_account_ref_id
                )
            )
            == 0
        )


def test_routed_post_submit_inspection_does_not_create_routing_or_execution_records() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, _assessment, _choice, _result, submitted = _submit_routed_child_intent(
        session_factory
    )
    _enable_actionability_capabilities(adapter)
    before_counts = _execution_counts(session_factory)

    _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
    _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}/actionability")
    _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}/recovery")

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
    context = detail["routed_lifecycle_context"]
    assert context["auto_submit"] is False
    assert context["fanout_created"] is False
    assert context["scoring_created"] is False
    assert context["target_reselection"] is False
    assert _execution_counts(session_factory) == before_counts


def test_routed_same_target_retry_preserves_routed_lineage() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, _assessment, choice, result, submitted = _submit_routed_child_intent(
        session_factory
    )
    _allow_same_target_retry_private_checks(adapter)
    original_lineage = submitted.raw_payload["routed_submission"]
    _mark_submitted_order_retryable_rejected(session_factory, submitted.submitted_order_id)

    retry_result = asyncio.run(
        execution.execute_submitted_order_recovery(submitted.submitted_order_id)
    )

    assert retry_result.action == "retry_same_target"
    assert retry_result.executed is True
    assert retry_result.resulting_order is not None
    retried = retry_result.resulting_order
    assert retried.submitted_order_id != submitted.submitted_order_id
    assert retried.raw_payload["routed_submission"]["selected_binding_ref_id"] == (
        original_lineage["selected_binding_ref_id"]
    )
    assert retried.raw_payload["routed_submission"]["selected_venue_account_ref_id"] == (
        original_lineage["selected_venue_account_ref_id"]
    )
    assert retried.raw_payload["routed_submission"]["selected_venue"] == (
        original_lineage["selected_venue"]
    )
    assert retried.raw_payload["routed_submission"]["selected_exchange_symbol"] == (
        original_lineage["selected_exchange_symbol"]
    )
    assert retried.raw_payload["routed_submission"]["auto_submit"] is False
    assert retried.raw_payload["routed_submission"]["fanout_created"] is False
    assert retried.raw_payload["routed_submission"]["target_reselection"] is False

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{retried.submitted_order_id}")
    context = detail["routed_lifecycle_context"]
    assert detail["routed_origin"] is True
    assert context["selected_binding_ref_id"] == choice.selected_binding_ref_id
    assert context["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert context["selected_venue"] == choice.selected_venue
    assert context["selected_exchange_symbol"] == original_lineage["selected_exchange_symbol"]
    assert context["auto_submit"] is False
    assert context["fanout_created"] is False
    assert context["target_reselection"] is False
    assert context["same_target_only"] is True
    assert _execution_counts(session_factory) == (1, 2)
    with session_factory() as session:
        intent = session.scalar(
            select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id)
        )
        assert intent is not None
        assert intent.provenance["latest_submission"]["recovery_parent_submitted_order_id"] == (
            submitted.submitted_order_id
        )


def test_non_routed_same_target_retry_does_not_fabricate_routed_lineage() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_okx_submitted_order(
        session_factory,
        suffix="phase57-non-routed-retry",
        api_key="okx-key-phase57-non-routed-retry",
    )
    _mark_submitted_order_retryable_rejected(session_factory, submitted_order_id)

    async def _transport(method: str, path: str, params=None, body=None, headers=None):
        if method == "GET" and path == "/api/v5/account/balance":
            return {
                "code": "0",
                "data": [{"totalEq": "1000", "availEq": "800", "upl": "0", "notionalUsd": "0"}],
            }
        if method == "GET" and path == "/api/v5/trade/orders-pending":
            return {"code": "0", "data": []}
        if method == "GET" and path == "/api/v5/trade/fills":
            return {"code": "0", "data": []}
        if method == "POST" and path == "/api/v5/trade/order":
            return {
                "code": "0",
                "data": [{"ordId": "okx-phase57-retry-new", "clOrdId": "mf-retry"}],
            }
        raise AssertionError((method, path, params, body, headers))

    execution = _build_okx_execution_service(session_factory, transport=_transport)

    retry_result = asyncio.run(execution.execute_submitted_order_recovery(submitted_order_id))

    assert retry_result.action == "retry_same_target"
    assert retry_result.executed is True
    assert retry_result.resulting_order is not None
    detail = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{retry_result.resulting_order.submitted_order_id}",
    )
    assert detail["routed_origin"] is False
    assert detail["routed_lineage"] is None
    assert detail["routed_lifecycle_context"] is None
