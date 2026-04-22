from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import urllib.parse

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_execution_service
from apps.api.app.main import app
from core.domain.enums import (
    DecisionAction,
    Environment,
    ExecutionReadinessOutcome,
    OrderIntentStatus,
    StrategyFamily,
    SubmittedOrderStatus,
    Venue,
)
from db.models import (
    ClientModel,
    InstrumentModel,
    MandateAccountBindingModel,
    OrderIntentModel,
    StrategyMandateModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from services.execution.service import (
    DefaultExecutionService,
    SubmissionBlockedError,
)
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService
from tests.test_phase3_strategy import build_settings, build_test_session_factory
from tests.test_phase42_execution_readiness import _seed_intent


async def _aster_submission_transport(
    method: str,
    path: str,
    params=None,
    body=None,
    headers=None,
):
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
        parsed_body = dict(urllib.parse.parse_qsl(body or "", keep_blank_values=True))
        return {
            "orderId": "aster-order-1",
            "clientOrderId": parsed_body.get("newClientOrderId"),
            "status": "accepted",
        }
    raise AssertionError((method, path, params, body, headers))


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


def _build_execution_service(session_factory, settings=None) -> DefaultExecutionService:
    resolved = settings or _build_submission_settings()
    adapter = AsterExchangeAdapter(
        resolved,
        transport=_aster_submission_transport,
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


def _seed_unbound_child_intent(session_factory) -> str:
    with session_factory() as session:
        client = ClientModel(client_key="client-unbound", display_name="Client Unbound", is_active=True)
        session.add(client)
        session.flush()
        mandate = StrategyMandateModel(
            client_ref_id=client.id,
            mandate_key="money_flow::unbound",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
            allow_builder_deployed_for_strategy=False,
            allow_builder_deployed_for_trading=False,
            metadata_json={},
        )
        session.add(mandate)
        session.flush()
        instrument = InstrumentModel(
            instrument_key="perpetual:linear:BTC:USDT:USDT",
            canonical_symbol="BTC",
            market_type="perpetual",
            product_type="linear",
            base_asset="BTC",
            quote_asset="USDT",
            settlement_asset="USDT",
            is_active=True,
        )
        session.add(instrument)
        session.flush()
        symbol = SymbolModel(
            instrument_ref_id=instrument.id,
            venue=Venue.ASTER.value,
            symbol="BTC",
            exchange_symbol="BTCUSDT",
            venue_asset_id="btc-usdt",
            asset_id=None,
            market_type="perpetual",
            product_type="linear",
            base_asset="BTC",
            quote_asset="USDT",
            settlement_asset="USDT",
            price_tick_size="0.1",
            quantity_step_size="0.001",
            min_order_size="0.001",
            size_decimals=3,
            max_leverage=20,
            only_isolated=False,
            is_perpetual=True,
            is_builder_deployed=False,
            is_strategy_eligible=True,
            is_trading_eligible=True,
            is_active=True,
            raw_metadata={},
        )
        session.add(symbol)
        session.flush()
        intent = OrderIntentModel(
            environment=Environment.TESTNET,
            intent_id="intent-unbound",
            decision_id="decision-unbound",
            action=DecisionAction.OPEN,
            mandate_desired_trade_ref_id=None,
            desired_trade_key="trade-unbound",
            sleeve_id="sleeve_1h",
            component_key="sleeve_1h",
            client_ref_id=client.id,
            strategy_mandate_ref_id=mandate.id,
            mandate_account_binding_ref_id=None,
            binding_key=None,
            venue_account_ref_id=None,
            instrument_key=instrument.instrument_key,
            instrument_ref_id=instrument.id,
            symbol_id=symbol.id,
            symbol="BTC",
            side="buy",
            order_type="market",
            quantity="0.01",
            limit_price=None,
            reduce_only=False,
            ttl_seconds=30,
            status=OrderIntentStatus.PREPARED,
            idempotency_key="idem-unbound",
            provenance={"phase_boundary": "phase_4_3"},
            created_at=datetime.now(UTC),
        )
        session.add(intent)
        session.commit()
        return intent.intent_id


def test_current_integrated_venues_now_report_submission_paths_as_implemented() -> None:
    registry = DefaultVenueRegistryService(build_settings())
    summaries = asyncio.run(registry.list_supported_venues())
    by_venue = {item.venue: item for item in summaries}

    assert by_venue[Venue.HYPERLIQUID.value].adapter_submission_implemented is True
    assert by_venue[Venue.ASTER.value].adapter_submission_implemented is True
    assert by_venue[Venue.BINANCE.value].adapter_submission_implemented is True
    assert by_venue[Venue.OKX.value].adapter_submission_implemented is True
    assert by_venue[Venue.COINBASE_ADVANCED_TRADE.value].adapter_submission_implemented is True
    assert by_venue[Venue.KRAKEN.value].adapter_submission_implemented is True
    assert by_venue[Venue.ASTER.value].submission_enabled is False


def test_binding_targeted_child_intent_can_move_from_prepared_to_submitted() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory)

    readiness = asyncio.run(execution.assess_child_intent_readiness(intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.ELIGIBLE_FOR_SUBMISSION

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0

    intent = asyncio.run(execution.get_child_intent(intent_id))
    submitted = asyncio.run(execution.submit_prepared_intent(intent))

    assert submitted.status == SubmittedOrderStatus.ACKNOWLEDGED
    assert submitted.exchange_order_id == "aster-order-1"
    assert submitted.intent_id == intent_id

    with session_factory() as session:
        stored_intent = session.scalar(select(OrderIntentModel).where(OrderIntentModel.intent_id == intent_id))
        assert stored_intent is not None
        assert stored_intent.status == OrderIntentStatus.SUBMITTED
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 1
        stored_order = session.scalar(select(SubmittedOrderModel))
        assert stored_order is not None
        assert stored_order.exchange_order_id == "aster-order-1"
        assert stored_order.status == SubmittedOrderStatus.ACKNOWLEDGED
        assert stored_order.intent_id == intent_id


def test_phase_gate_blocks_actual_submission_even_when_intent_is_preparable() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    settings = _build_submission_settings(EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED=False)
    execution = _build_execution_service(session_factory, settings=settings)

    readiness = asyncio.run(execution.assess_child_intent_readiness(intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED

    intent = asyncio.run(execution.get_child_intent(intent_id))
    try:
        asyncio.run(execution.submit_prepared_intent(intent))
    except SubmissionBlockedError as exc:
        assert exc.readiness.outcome == ExecutionReadinessOutcome.PHASE_BLOCKED
        assert "phase_live_submit_deferred" in exc.readiness.reason_codes
    else:
        raise AssertionError("submission unexpectedly succeeded while live phase gate was disabled")

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def test_unauthorized_account_cannot_submit_prepared_intent() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    settings = _build_submission_settings(ASTER_SUBMISSION_AUTHORIZED=False)
    execution = _build_execution_service(session_factory, settings=settings)

    readiness = asyncio.run(execution.assess_child_intent_readiness(intent_id))
    assert readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
    assert "account_not_authorized" in readiness.reason_codes

    intent = asyncio.run(execution.get_child_intent(intent_id))
    try:
        asyncio.run(execution.submit_prepared_intent(intent))
    except SubmissionBlockedError as exc:
        assert exc.readiness.outcome == ExecutionReadinessOutcome.BLOCKED_BY_ENVIRONMENT
        assert "account_not_authorized" in exc.readiness.reason_codes
    else:
        raise AssertionError("unauthorized account unexpectedly submitted")

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def test_mandate_scoped_open_cannot_be_submitted_without_binding_target() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_unbound_child_intent(session_factory)
    execution = _build_execution_service(session_factory)
    intent = asyncio.run(execution.get_child_intent(intent_id))

    try:
        asyncio.run(execution.submit_prepared_intent(intent))
    except ValueError as exc:
        assert "Mandate-scoped OPEN desired trades must remain above routing" in str(exc)
    else:
        raise AssertionError("unbound mandate-scoped open unexpectedly reached submission")


def test_submission_endpoints_show_prepared_vs_submitted_transition() -> None:
    session_factory = build_test_session_factory()
    intent_id = _seed_intent(session_factory, venue=Venue.ASTER.value)
    execution = _build_execution_service(session_factory)
    client = TestClient(app)
    app.dependency_overrides[get_execution_service] = lambda: execution
    try:
        before = client.get("/api/v1/submitted-orders", params={"intent_id": intent_id})
        submit = client.post(f"/api/v1/child-intents/{intent_id}/submit")
        after = client.get("/api/v1/submitted-orders", params={"intent_id": intent_id})
    finally:
        app.dependency_overrides.clear()

    assert before.status_code == 200
    assert before.json() == []
    assert submit.status_code == 200
    assert submit.json()["status"] == SubmittedOrderStatus.ACKNOWLEDGED.value
    assert submit.json()["intent_id"] == intent_id
    assert after.status_code == 200
    assert len(after.json()) == 1
    assert after.json()[0]["exchange_order_id"] == "aster-order-1"
