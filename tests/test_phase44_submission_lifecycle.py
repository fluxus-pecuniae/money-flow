from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
import urllib.parse

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    OrderIntentStatus,
    OrderType,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Venue,
)
from core.domain.models import SubmittedOrder, SubmittedOrderLifecycleUpdate
from db.models import FillModel, OrderIntentModel, SubmittedOrderLifecycleEventModel, SubmittedOrderModel
from services.execution.service import DefaultExecutionService
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService
from tests.test_phase3_strategy import build_settings, build_test_session_factory
from tests.test_phase42_execution_readiness import _seed_intent


async def _aster_success_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/fapi/v2/balance":
        return [
            {
                "balance": "1000",
                "availableBalance": "800",
                "crossWalletBalance": "200",
                "crossUnPnl": "10",
                "maxWithdrawAmount": "800",
            }
        ]
    if method == "POST" and path == "/fapi/v1/order":
        parsed = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
        return {
            "orderId": "aster-order-44",
            "clientOrderId": parsed.get("newClientOrderId"),
            "status": "accepted",
        }
    raise AssertionError((method, path, params, body, headers))


async def _aster_rejected_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/fapi/v2/balance":
        return [
            {
                "balance": "1000",
                "availableBalance": "800",
                "crossWalletBalance": "200",
                "crossUnPnl": "10",
                "maxWithdrawAmount": "800",
            }
        ]
    if method == "POST" and path == "/fapi/v1/order":
        return {"code": "-2010", "msg": "Order would immediately trigger."}
    raise AssertionError((method, path, params, body, headers))


async def _aster_ambiguous_transport(method: str, path: str, params=None, body=None, headers=None):
    if method == "GET" and path == "/fapi/v2/balance":
        return [
            {
                "balance": "1000",
                "availableBalance": "800",
                "crossWalletBalance": "200",
                "crossUnPnl": "10",
                "maxWithdrawAmount": "800",
            }
        ]
    if method == "POST" and path == "/fapi/v1/order":
        return {"status": "accepted"}
    raise AssertionError((method, path, params, body, headers))


class _LifecycleAsterAdapter(AsterExchangeAdapter):
    def __init__(self, *args, lifecycle_update=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._lifecycle_update = lifecycle_update

    async def reconcile_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        if self._lifecycle_update is not None:
            return self._lifecycle_update(submitted_order)
        return await super().reconcile_submitted_order(submitted_order)


def _build_submission_settings(**overrides: object):
    base = {
        "APP_ENV": Environment.TESTNET,
        "EXCHANGE_VENUE": Venue.ASTER.value,
        "EXCHANGE_USE_TESTNET": True,
        "EXECUTION_DRY_RUN": False,
        "EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED": True,
        "ASTER_ENABLED": True,
        "ASTER_READ_ONLY_MODE": False,
        "ASTER_DRY_RUN_MODE": False,
        "ASTER_SUBMISSION_ENABLED": True,
        "ASTER_SUBMISSION_AUTHORIZED": True,
        "ASTER_CREDENTIALS_REF": "secret://acct",
        "ASTER_API_KEY": "aster-key",
        "ASTER_API_SECRET": "aster-secret",
        "ASTER_ACCOUNT_IDENTIFIER": "aster-main",
    }
    base.update(overrides)
    return build_settings(**base)


def _build_execution_service(
    session_factory,
    *,
    transport=_aster_success_transport,
    lifecycle_update=None,
    settings=None,
) -> DefaultExecutionService:
    resolved = settings or _build_submission_settings()
    adapter = _LifecycleAsterAdapter(
        resolved,
        transport=transport,
        lifecycle_update=lifecycle_update,
        session_factory=session_factory,
    )
    registry = DefaultVenueRegistryService(
        resolved,
        session_factory=session_factory,
        adapter_overrides={Venue.ASTER.value: adapter},
    )
    return DefaultExecutionService(
        resolved,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


async def _hyperliquid_partial_fill_transport(payload):
    request_type = payload.get("type")
    if request_type == "orderStatus":
        return {
            "order": {
                "order": {
                    "coin": "BTC",
                    "side": "S",
                    "orderType": "Limit",
                    "limitPx": "100000",
                    "origSz": "0.01",
                    "sz": "0.006",
                    "reduceOnly": True,
                    "oid": 12345,
                    "timestamp": 1700002100000,
                },
                "status": "open",
                "statusTimestamp": 1700002100000,
            }
        }
    if request_type == "userFills":
        return [
            {
                "coin": "BTC",
                "side": "S",
                "px": "100100",
                "sz": "0.004",
                "fee": "0.25",
                "closedPnl": "0",
                "oid": 12345,
                "hash": "0xfill-1",
                "time": 1700002200000,
            }
        ]
    raise AssertionError(payload)


def _build_hyperliquid_execution_service(
    session_factory,
    *,
    transport=_hyperliquid_partial_fill_transport,
) -> DefaultExecutionService:
    settings = build_settings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE=Venue.HYPERLIQUID.value,
        EXCHANGE_USE_TESTNET=True,
        EXECUTION_DRY_RUN=False,
        EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=True,
        HYPERLIQUID_READ_ONLY_MODE=False,
        HYPERLIQUID_DRY_RUN_MODE=False,
        HYPERLIQUID_SUBMISSION_ENABLED=True,
        HYPERLIQUID_SUBMISSION_AUTHORIZED=True,
    )
    adapter = HyperliquidExchangeAdapter(
        settings,
        transport=transport,
        session_factory=session_factory,
    )
    registry = DefaultVenueRegistryService(
        settings,
        session_factory=session_factory,
        adapter_overrides={Venue.HYPERLIQUID.value: adapter},
    )
    return DefaultExecutionService(
        settings,
        session_factory=session_factory,
        venue_registry_service=registry,
    )


def _seed_fill(
    session_factory,
    *,
    submitted_order_id: str,
    exchange_order_id: str | None,
    venue_account_ref_id: str | None,
    account_address: str | None,
    instrument_ref_id: str | None,
    symbol: str,
    quantity: str,
    price: str,
    fill_id: str,
) -> None:
    with session_factory() as session:
        session.add(
            FillModel(
                environment=Environment.TESTNET,
                fill_id=fill_id,
                venue_fill_id=fill_id,
                venue_account_ref_id=venue_account_ref_id,
                venue=Venue.ASTER.value,
                account_address=account_address,
                submitted_order_id=submitted_order_id,
                exchange_order_id=exchange_order_id,
                position_id=None,
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol=symbol,
                side="sell",
                price=Decimal(price),
                quantity=Decimal(quantity),
                fee=Decimal("0"),
                fee_token="USDT",
                closed_pnl=None,
                raw_payload={"fill_id": fill_id},
                filled_at=datetime.now(UTC),
            )
        )
        session.commit()


def _seed_hyperliquid_submitted_order(session_factory) -> str:
    intent_id = _seed_intent(session_factory, venue=Venue.HYPERLIQUID.value)
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert intent is not None
        intent.order_type = OrderType.LIMIT
        intent.limit_price = Decimal("100000")
        intent.status = OrderIntentStatus.SUBMITTED
        session.add(intent)
        session.flush()
        submitted = SubmittedOrderModel(
            environment=Environment.TESTNET,
            submitted_order_id="subm-hl-partial-open",
            intent_id=intent.intent_id,
            client_order_id="intent-hl-client",
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=Venue.HYPERLIQUID.value,
            account_address="hyperliquid-acct",
            instrument_ref_id=intent.instrument_ref_id,
            symbol_id=intent.symbol_id,
            symbol=intent.symbol,
            side=intent.side,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("100000"),
            original_quantity=Decimal("0.01"),
            remaining_quantity=Decimal("0.01"),
            reduce_only=True,
            exchange_order_id="12345",
            status=SubmittedOrderStatus.ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
            submitted_at=datetime.now(UTC),
            acknowledged_at=datetime.now(UTC),
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            last_fill_at=None,
            last_reconciled_at=None,
            status_reason_code=None,
            status_message=None,
            reason_codes=[],
            cancelable_in_principle=True,
            amendable_in_principle=True,
            raw_payload={"seeded": True},
        )
        session.add(submitted)
        session.commit()
    return "subm-hl-partial-open"


def test_submit_persists_lifecycle_and_initial_event() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory)

    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert submitted.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert submitted.reconciliation_status == SubmittedOrderReconciliationStatus.NOT_ATTEMPTED
    assert submitted.cancelable_in_principle is True
    assert submitted.amendable_in_principle is False

    with session_factory() as session:
        model = session.scalar(select(SubmittedOrderModel))
        assert model is not None
        assert model.status == SubmittedOrderStatus.ACKNOWLEDGED
        assert model.reconciliation_status == SubmittedOrderReconciliationStatus.NOT_ATTEMPTED
        events = session.scalars(select(SubmittedOrderLifecycleEventModel)).all()
        assert len(events) == 1
        assert events[0].event_type == "submission_acknowledged"


def test_reconciliation_advances_status_from_fill_evidence() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory)
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    _seed_fill(
        session_factory,
        submitted_order_id=submitted.submitted_order_id,
        exchange_order_id=submitted.exchange_order_id,
        venue_account_ref_id=submitted.venue_account_ref_id,
        account_address=submitted.account_address,
        instrument_ref_id=submitted.instrument_ref_id,
        symbol=submitted.symbol or "BTC",
        quantity="0.004",
        price="100000",
        fill_id="fill-partial",
    )
    partial = asyncio.run(execution.reconcile_submitted_order(submitted.submitted_order_id))
    assert partial.status == SubmittedOrderStatus.PARTIALLY_FILLED
    assert partial.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert partial.status_reason_code == "reconciliation_partial_fill"
    assert partial.cancelable_in_principle is True

    _seed_fill(
        session_factory,
        submitted_order_id=submitted.submitted_order_id,
        exchange_order_id=submitted.exchange_order_id,
        venue_account_ref_id=submitted.venue_account_ref_id,
        account_address=submitted.account_address,
        instrument_ref_id=submitted.instrument_ref_id,
        symbol=submitted.symbol or "BTC",
        quantity="0.006",
        price="100100",
        fill_id="fill-complete",
    )
    filled = asyncio.run(execution.reconcile_submitted_order(submitted.submitted_order_id))
    assert filled.status == SubmittedOrderStatus.FILLED
    assert filled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert filled.status_reason_code == "reconciliation_completed_fill"
    assert filled.cancelable_in_principle is False


def test_submit_rejection_is_persisted_honestly() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory, transport=_aster_rejected_transport)

    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert submitted.status == SubmittedOrderStatus.REJECTED
    assert submitted.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert submitted.status_reason_code == "venue_rejected"
    assert "venue_rejected" in submitted.reason_codes
    assert submitted.status_message == "Order would immediately trigger."
    assert submitted.remaining_quantity == Decimal("0")

    with session_factory() as session:
        stored_intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert stored_intent is not None
        assert stored_intent.status == OrderIntentStatus.REJECTED
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.intent_id == intent_id
            )
        ).all()
        assert len(events) == 1
        assert events[0].event_type == "submission_rejected"
        assert events[0].message == "Order would immediately trigger."


def test_hyperliquid_reconciliation_marks_partial_fill_even_while_order_stays_open() -> None:
    session_factory = build_test_session_factory()
    submitted_order_id = _seed_hyperliquid_submitted_order(session_factory)
    execution = _build_hyperliquid_execution_service(session_factory)

    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted_order_id))

    assert reconciled.status == SubmittedOrderStatus.PARTIALLY_FILLED
    assert reconciled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert reconciled.status_reason_code == "reconciliation_partial_fill"
    assert reconciled.filled_quantity == Decimal("0.004")
    assert reconciled.remaining_quantity == Decimal("0.006")
    assert reconciled.cancelable_in_principle is True
    assert reconciled.amendable_in_principle is True

    with session_factory() as session:
        stored = session.scalar(
            select(SubmittedOrderModel).where(
                SubmittedOrderModel.submitted_order_id == submitted_order_id
            )
        )
        assert stored is not None
        assert stored.status == SubmittedOrderStatus.PARTIALLY_FILLED
        assert stored.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
        assert stored.filled_quantity == Decimal("0.004")
        assert stored.remaining_quantity == Decimal("0.006")
        events = session.scalars(
            select(SubmittedOrderLifecycleEventModel).where(
                SubmittedOrderLifecycleEventModel.submitted_order_id == submitted_order_id
            )
        ).all()
        assert any(event.event_type == "reconciliation_partial_fill" for event in events)


def test_ambiguous_submit_can_reconcile_to_unknown() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)

    def _unknown_update(submitted_order: SubmittedOrder) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=submitted_order.venue,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message="Order was absent from venue state and no fills were found.",
            reason_codes=["reconciliation_missing_order"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload={"matched_order": False},
            observed_at=datetime.now(UTC),
        )

    execution = _build_execution_service(
        session_factory,
        transport=_aster_ambiguous_transport,
        lifecycle_update=_unknown_update,
    )

    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    assert submitted.status == SubmittedOrderStatus.SUBMITTED

    reconciled = asyncio.run(execution.reconcile_submitted_order(submitted.submitted_order_id))
    assert reconciled.status == SubmittedOrderStatus.UNKNOWN
    assert reconciled.reconciliation_status == SubmittedOrderReconciliationStatus.RECONCILED
    assert reconciled.status_reason_code == "reconciliation_missing_order"


def test_api_exposes_submitted_order_lifecycle_views() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory)
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    _seed_fill(
        session_factory,
        submitted_order_id=submitted.submitted_order_id,
        exchange_order_id=submitted.exchange_order_id,
        venue_account_ref_id=submitted.venue_account_ref_id,
        account_address=submitted.account_address,
        instrument_ref_id=submitted.instrument_ref_id,
        symbol=submitted.symbol or "BTC",
        quantity="0.004",
        price="100000",
        fill_id="fill-api",
    )

    client = TestClient(app)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        detail_before = client.get(f"/api/v1/submitted-orders/{submitted.submitted_order_id}")
        reconcile = client.post(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/reconcile")
        events = client.get(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/events")
        fills = client.get(f"/api/v1/submitted-orders/{submitted.submitted_order_id}/fills")
    finally:
        app.dependency_overrides.clear()

    assert detail_before.status_code == 200
    assert detail_before.json()["status"] == SubmittedOrderStatus.ACKNOWLEDGED.value
    assert reconcile.status_code == 200
    assert reconcile.json()["status"] == SubmittedOrderStatus.PARTIALLY_FILLED.value
    assert reconcile.json()["reconciliation_status"] == SubmittedOrderReconciliationStatus.RECONCILED.value
    assert events.status_code == 200
    assert any(item["event_type"] == "submission_acknowledged" for item in events.json())
    assert any(item["event_type"] == "reconciliation_partial_fill" for item in events.json())
    assert fills.status_code == 200
    assert fills.json()[0]["fill_id"] == "fill-api"


def test_limit_order_shows_amend_groundwork_without_executing_amend() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    with session_factory() as session:
        intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert intent is not None
        intent.order_type = OrderType.LIMIT
        intent.limit_price = Decimal("100000")
        session.add(intent)
        session.commit()

    execution = _build_execution_service(session_factory)
    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))
    assert submitted.cancelable_in_principle is True
    assert submitted.amendable_in_principle is True
