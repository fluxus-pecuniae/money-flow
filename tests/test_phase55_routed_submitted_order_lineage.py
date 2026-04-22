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
    OrderIntentStatus,
    OrderSide,
    OrderType,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Venue,
)
from core.domain.models import VenueCapabilities
from db.models import OrderIntentModel, SubmittedOrderModel
from tests.test_phase3_strategy import build_test_session_factory
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


def _insert_non_routed_submitted_order(
    session_factory,
    *,
    submitted_order_id: str = "submitted-normal-binding-scoped",
    raw_payload: dict[str, object] | None = None,
) -> str:
    with session_factory() as session:
        model = SubmittedOrderModel(
            environment=Environment.TESTNET,
            submitted_order_id=submitted_order_id,
            intent_id=f"intent-{submitted_order_id}",
            client_order_id=f"client-{submitted_order_id}",
            venue_account_ref_id="venue-account-normal",
            venue=Venue.ASTER.value,
            account_address="aster-account-normal",
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
            status_message="Seeded non-routed submitted order.",
            reason_codes=["submitted"],
            cancelable_in_principle=True,
            amendable_in_principle=False,
            raw_payload=raw_payload or {"adapter_submit_called": True},
        )
        session.add(model)
        session.commit()
    return submitted_order_id


def _execution_counts(session_factory) -> tuple[int, int]:
    with session_factory() as session:
        return (
            session.scalar(select(func.count()).select_from(OrderIntentModel)),
            session.scalar(select(func.count()).select_from(SubmittedOrderModel)),
        )


def test_routed_submitted_order_detail_exposes_derived_lineage_without_raw_payload_parsing() -> None:
    session_factory = build_test_session_factory()
    execution, _adapter, assessment, choice, _result, submitted = _submit_routed_child_intent(
        session_factory
    )

    payload = _api_get_json(
        execution,
        f"/api/v1/submitted-orders/{submitted.submitted_order_id}",
    )

    assert payload["routed_origin"] is True
    lineage = payload["routed_lineage"]
    assert lineage["routed_origin"] is True
    assert lineage["route_lineage_malformed"] is False
    assert lineage["missing_lineage_fields"] == []
    assert lineage["desired_trade_key"] == submitted.raw_payload["routed_submission"]["desired_trade_key"]
    assert lineage["routing_assessment_id"] == assessment.assessment_id
    assert lineage["routing_target_choice_id"] == choice.target_choice_id
    assert lineage["selected_binding_ref_id"] == choice.selected_binding_ref_id
    assert lineage["selected_binding_key"] == choice.selected_binding_key
    assert lineage["selected_venue_account_ref_id"] == choice.selected_venue_account_ref_id
    assert lineage["selected_venue_account_key"] == choice.selected_venue_account_key
    assert lineage["selected_venue"] == choice.selected_venue
    assert lineage["selected_exchange_symbol"] == submitted.raw_payload["routed_submission"][
        "selected_exchange_symbol"
    ]
    assert lineage["readiness_evaluation_id"] == submitted.raw_payload["routed_submission"][
        "readiness_evaluation_id"
    ]
    assert lineage["explicit_action_required"] is True
    assert lineage["auto_submit"] is False
    assert lineage["fanout_created"] is False
    assert lineage["scoring_created"] is False
    assert lineage["target_reselection"] is False


def test_non_routed_submitted_order_detail_does_not_fabricate_routed_lineage() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _insert_non_routed_submitted_order(session_factory)
    execution, _adapter = _build_execution(session_factory, routed_submission_enabled=True)

    payload = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted_order_id}")

    assert payload["routed_origin"] is False
    assert payload["routed_lineage"] is None
    assert "routed_submission" not in payload["raw_payload"]


def test_submitted_order_list_preserves_routed_origin_classification() -> None:
    session_factory = build_test_session_factory()
    execution, _adapter, assessment, choice, _result, submitted = _submit_routed_child_intent(
        session_factory
    )
    normal_submitted_order_id = _insert_non_routed_submitted_order(session_factory)

    payload = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    by_id = {item["submitted_order_id"]: item for item in payload}

    routed_item = by_id[submitted.submitted_order_id]
    assert routed_item["routed_origin"] is True
    assert routed_item["routed_lineage"]["routing_assessment_id"] == assessment.assessment_id
    assert routed_item["routed_lineage"]["routing_target_choice_id"] == choice.target_choice_id
    assert routed_item["routed_lineage"]["selected_venue_account_ref_id"] == (
        choice.selected_venue_account_ref_id
    )

    normal_item = by_id[normal_submitted_order_id]
    assert normal_item["routed_origin"] is False
    assert normal_item["routed_lineage"] is None


def test_malformed_routed_payload_is_bounded_on_detail_and_list() -> None:
    session_factory = build_test_session_factory()
    malformed_id = _insert_non_routed_submitted_order(
        session_factory,
        submitted_order_id="submitted-malformed-routed-payload",
        raw_payload={
            "routed_submission": {
                "routing_assessment_id": "rtassess-partial",
                "auto_submit": False,
            }
        },
    )
    execution, _adapter = _build_execution(session_factory, routed_submission_enabled=True)

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{malformed_id}")
    listed = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    listed_detail = next(item for item in listed if item["submitted_order_id"] == malformed_id)

    for payload in (detail, listed_detail):
        assert payload["routed_origin"] is True
        lineage = payload["routed_lineage"]
        assert lineage["route_lineage_malformed"] is True
        assert lineage["routing_assessment_id"] == "rtassess-partial"
        assert lineage["auto_submit"] is False
        assert "desired_trade_key" in lineage["missing_lineage_fields"]
        assert "routing_target_choice_id" in lineage["missing_lineage_fields"]
        assert "selected_venue_account_ref_id" in lineage["missing_lineage_fields"]


def test_wrong_typed_routed_lineage_fields_are_marked_malformed() -> None:
    session_factory = build_test_session_factory()
    malformed_id = _insert_non_routed_submitted_order(
        session_factory,
        submitted_order_id="submitted-wrong-typed-routed-payload",
        raw_payload={
            "routed_submission": {
                "desired_trade_key": "desired-route-typed",
                "routing_assessment_id": "rtassess-typed",
                "routing_target_choice_id": "rtchoice-typed",
                "selected_binding_ref_id": "binding-ref-typed",
                "selected_binding_key": "binding-key-typed",
                "selected_venue_account_ref_id": "account-ref-typed",
                "selected_venue_account_key": "account-key-typed",
                "selected_venue": Venue.HYPERLIQUID.value,
                "selected_exchange_symbol": "BTC-PERP",
                "readiness_evaluation_id": "ready-typed",
                "explicit_action_required": "true",
                "auto_submit": "false",
                "fanout_created": False,
                "scoring_created": False,
                "target_reselection": False,
            }
        },
    )
    execution, _adapter = _build_execution(session_factory, routed_submission_enabled=True)

    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{malformed_id}")
    listed = _api_get_json(execution, "/api/v1/submitted-orders", params={"limit": 10})
    listed_detail = next(item for item in listed if item["submitted_order_id"] == malformed_id)

    for payload in (detail, listed_detail):
        assert payload["routed_origin"] is True
        lineage = payload["routed_lineage"]
        assert lineage["route_lineage_malformed"] is True
        assert lineage["explicit_action_required"] is None
        assert lineage["auto_submit"] is None
        assert "explicit_action_required" in lineage["malformed_lineage_fields"]
        assert "auto_submit" in lineage["malformed_lineage_fields"]
        assert "explicit_action_required" not in lineage["missing_lineage_fields"]
        assert "auto_submit" not in lineage["missing_lineage_fields"]


def test_routed_submitted_order_actionability_remains_same_target_and_inspection_only() -> None:
    session_factory = build_test_session_factory()
    execution, adapter, _assessment, choice, result, submitted = _submit_routed_child_intent(
        session_factory
    )
    before_counts = _execution_counts(session_factory)

    async def get_venue_capabilities() -> VenueCapabilities:
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

    adapter.get_venue_capabilities = get_venue_capabilities

    actionability = asyncio.run(execution.get_submitted_order_actionability(submitted.submitted_order_id))
    detail = _api_get_json(execution, f"/api/v1/submitted-orders/{submitted.submitted_order_id}")

    assert actionability.venue_account_ref_id == choice.selected_venue_account_ref_id
    assert actionability.venue == choice.selected_venue
    assert detail["routed_lineage"]["selected_venue_account_ref_id"] == (
        choice.selected_venue_account_ref_id
    )
    assert detail["routed_lineage"]["fanout_created"] is False
    assert detail["routed_lineage"]["target_reselection"] is False
    assert _execution_counts(session_factory) == before_counts
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == result.intent_id))
        assert intent is not None
        assert intent.status == OrderIntentStatus.SUBMITTED
