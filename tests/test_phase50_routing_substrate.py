from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from core.domain.enums import (
    DecisionAction,
    Environment,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderSide,
    OrderType,
    ProductType,
    RoutingAssessmentDecisionStatus,
    RoutingCandidateEligibilityStatus,
    StrategyFamily,
    TradeTargetScope,
    Venue,
    VenueSupportLevel,
)
from core.domain.models import ExchangeStatus, TopOfBookSnapshot, VenueCapabilities
from db.models import (
    ClientModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    MandateMarketDataSourcePolicyModel,
    OrderIntentModel,
    RoutingAssessmentCandidateModel,
    RoutingAssessmentModel,
    StrategyMandateModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from services.planning.service import DefaultTradePlanningService
from services.routing.service import DefaultRoutingAssessmentService, RoutingAssessmentError
from services.runtime.context import DefaultRuntimeContextService
from tests.test_phase3_strategy import build_settings, build_test_session_factory, seed_symbol


class _RoutingStubVenueAdapter:
    def __init__(
        self,
        *,
        venue: str,
        top_of_book: TopOfBookSnapshot | None,
        read_only: bool = False,
        supports_order_submission: bool = True,
    ) -> None:
        self._venue = venue
        self._top_of_book = top_of_book
        self._read_only = read_only
        self._supports_order_submission = supports_order_submission

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue(self._venue),
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            supports_spot=self._venue != Venue.HYPERLIQUID.value,
            supports_perpetuals=True,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=False,
            supports_account_sync=True,
            supports_top_of_book=True,
            supports_depth_summary=False,
            supports_order_submission=self._supports_order_submission,
            supports_order_cancel=True,
            supports_order_amend=self._venue in {Venue.HYPERLIQUID.value, Venue.OKX.value},
            supports_recent_fills_query=False,
            adapter_supports_order_submission=self._supports_order_submission,
            adapter_supports_order_cancel=True,
            adapter_supports_order_amend=self._venue in {Venue.HYPERLIQUID.value, Venue.OKX.value},
            adapter_supports_user_streams=False,
            supports_order_preview=True,
            supports_account_snapshot=True,
            supports_open_orders_query=True,
            supports_open_positions_query=self._venue == Venue.HYPERLIQUID.value,
            supports_reduce_only_orders=True,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=self._venue == Venue.OKX.value,
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT],
            supported_time_in_force=["gtc", "ioc"],
            account_model="wallet_address" if self._venue == Venue.HYPERLIQUID.value else "account_with_subaccounts",
            private_lifecycle_update_mode="polling",
        )

    async def get_exchange_status(self) -> ExchangeStatus:
        return ExchangeStatus(
            venue=self._venue,
            environment=Environment.TESTNET,
            connected=True,
            api_base_url=f"https://{self._venue}.example",
            websocket_base_url=f"wss://{self._venue}.example/ws",
            can_sign_orders=False,
            wallet_address_configured=self._venue == Venue.HYPERLIQUID.value,
            account_identifier_configured=True,
            credentials_configured=self._venue != Venue.HYPERLIQUID.value,
            read_only_mode=self._read_only,
            dry_run_mode=True,
            support_level=VenueSupportLevel.EXECUTION_PREPARABLE,
            adapter_supports_order_submission=self._supports_order_submission,
            adapter_supports_order_cancel=True,
            adapter_supports_order_amend=self._venue in {Venue.HYPERLIQUID.value, Venue.OKX.value},
            adapter_supports_user_streams=False,
            submission_authorized=False,
            live_submission_phase_enabled=False,
            last_success_at=datetime.now(UTC),
            last_error=None,
            private_lifecycle_update_mode="polling",
        )

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        return self._top_of_book


class _RoutingStubVenueRegistry:
    def __init__(self, adapters: dict[str, _RoutingStubVenueAdapter]) -> None:
        self._adapters = adapters

    async def list_supported_venues(self):
        raise NotImplementedError

    async def get_adapter(self, venue: str):
        return self._adapters[venue]


def _quote(venue: str, *, instrument_key: str, instrument_ref_id: str) -> TopOfBookSnapshot:
    return TopOfBookSnapshot(
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        venue=venue,
        symbol="BTC",
        bid_price=Decimal("100"),
        bid_size=Decimal("2"),
        ask_price=Decimal("101"),
        ask_size=Decimal("3"),
        observed_at=datetime.now(UTC),
    )


def _seed_desired_trade(
    session_factory,
    *,
    context,
    instrument_ref_id: str,
    instrument_key: str,
    desired_trade_key: str = "phase50-routing-required-open",
    status: MandateDesiredTradeStatus = MandateDesiredTradeStatus.ROUTING_REQUIRED,
) -> str:
    with session_factory() as session:
        policy = session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id
                == context.mandate.mandate_ref_id
            )
        )
        assert policy is not None
        session.add(
            MandateDesiredTradeModel(
                environment=Environment.TESTNET,
                desired_trade_key=desired_trade_key,
                evaluated_state_fingerprint=f"fingerprint::{desired_trade_key}",
                client_ref_id=context.client.client_ref_id,
                strategy_mandate_ref_id=context.mandate.mandate_ref_id,
                market_data_source_policy_ref_id=policy.id,
                mandate_account_binding_ref_id=None,
                mandate_key=context.mandate.mandate_key,
                binding_key=None,
                venue_account_ref_id=None,
                family=StrategyFamily.MONEY_FLOW,
                component_key="sleeve_1h",
                planning_source_venue=Venue.HYPERLIQUID.value,
                planning_source_mode=MarketDataSourceMode.SINGLE_VENUE,
                planning_as_of=datetime.now(UTC),
                target_scope=TradeTargetScope.MANDATE,
                instrument_key=instrument_key,
                instrument_ref_id=instrument_ref_id,
                symbol_id=None,
                symbol="BTC",
                action=DecisionAction.OPEN,
                side=OrderSide.BUY,
                desired_quantity=Decimal("0.05"),
                desired_notional=None,
                source_decision_ids_json=["decision-open"],
                source_evaluation_keys_json=["eval-open"],
                source_binding_keys_json=[context.bindings[0].binding.binding_key],
                status=status,
                status_reason_code=(
                    "routing_required_target_not_selected"
                    if status == MandateDesiredTradeStatus.ROUTING_REQUIRED
                    else None
                ),
                status_message="Risk approved the mandate-level desired trade, but routing is required.",
                provenance={"phase": "phase_5_0_test"},
                created_at=datetime.now(UTC),
                approved_at=datetime.now(UTC),
                rejected_at=None,
            )
        )
        session.commit()
    return desired_trade_key


def _seed_second_hyperliquid_binding(session_factory, *, mandate_key: str, suffix: str = "secondary") -> str:
    with session_factory() as session:
        client = session.scalar(select(ClientModel).where(ClientModel.client_key == "default_client"))
        mandate = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        assert client is not None
        assert mandate is not None
        account = VenueAccountModel(
            venue_account_key=f"hyperliquid_testnet_{suffix}",
            client_ref_id=client.id,
            venue=Venue.HYPERLIQUID.value,
            environment=Environment.TESTNET,
            venue_native_account_id=f"acct-{suffix}",
            account_address=f"acct-{suffix}",
            account_label=suffix,
            subaccount_label=None,
            credentials_ref=None,
            wallet_ref=None,
            is_active=True,
            trading_enabled=True,
            raw_metadata={},
        )
        session.add(account)
        session.flush()
        binding_key = f"{mandate_key}::hyperliquid_testnet_{suffix}"
        session.add(
            MandateAccountBindingModel(
                binding_key=binding_key,
                strategy_mandate_ref_id=mandate.id,
                venue_account_ref_id=account.id,
                enabled=True,
                strategy_eligible=True,
                routing_eligible=True,
                trading_enabled=True,
                allow_builder_deployed_for_strategy=False,
                allow_builder_deployed_for_trading=False,
                notes=None,
                metadata_json={},
            )
        )
        session.commit()
        return binding_key


def _build_routing_service(
    session_factory,
    *,
    top_of_book: TopOfBookSnapshot | None,
    supports_order_submission: bool = True,
):
    settings = build_settings(ACTIVE_MANDATE_KEY="money_flow::phase50")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)
    registry = _RoutingStubVenueRegistry(
        {
            Venue.HYPERLIQUID.value: _RoutingStubVenueAdapter(
                venue=Venue.HYPERLIQUID.value,
                top_of_book=top_of_book,
                supports_order_submission=supports_order_submission,
            )
        }
    )
    planning = DefaultTradePlanningService(
        settings,
        session_factory=session_factory,
        runtime_context_service=runtime,
        venue_registry_service=registry,
    )
    routing = DefaultRoutingAssessmentService(
        settings,
        session_factory=session_factory,
        planning_service=planning,
    )
    return settings, runtime, routing


def _assert_no_forbidden_output_keys(payload: object) -> None:
    forbidden = {
        "selected_binding_id",
        "selected_venue",
        "best_binding",
        "recommended_binding",
        "preferred_binding",
        "route_decision",
        "execution_plan",
        "child_intent_plan",
        "allocation_weights",
        "venue_ranking",
        "confidence_score",
        "quality_score",
    }
    if isinstance(payload, dict):
        assert not (set(payload) & forbidden)
        for value in payload.values():
            _assert_no_forbidden_output_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_forbidden_output_keys(value)


def test_routing_required_open_produces_non_executing_assessment() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=_quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        ),
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )

    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))

    assert assessment.decision_status == RoutingAssessmentDecisionStatus.ASSESSMENT_ONLY
    assert assessment.eligible_binding_count == 1
    assert assessment.ineligible_binding_count == 0
    assert assessment.candidates[0].eligibility_status == (
        RoutingCandidateEligibilityStatus.ELIGIBLE_FOR_FUTURE_SELECTION
    )
    assert assessment.candidates[0].assessment_id == assessment.assessment_id
    assert assessment.candidates[0].assessment_id != assessment.request.routing_request_id
    assert assessment.candidates[0].reason_codes == ["binding_candidate_assessed_eligible"]
    assert assessment.provenance["non_executing"] is True
    assert assessment.provenance["child_intents_created"] is False

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RoutingAssessmentModel)) == 1
        assert session.scalar(select(func.count()).select_from(RoutingAssessmentCandidateModel)) == 1
        persisted_candidate = session.scalar(select(RoutingAssessmentCandidateModel))
        assert persisted_candidate is not None
        assert persisted_candidate.assessment_id == assessment.assessment_id
        assert persisted_candidate.assessment_id != assessment.request.routing_request_id
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0

    fetched = asyncio.run(routing.get_routing_assessment(assessment.assessment_id))
    assert fetched.assessment_id == assessment.assessment_id
    assert fetched.request.desired_trade_key == desired_trade_key


def test_routing_assessment_enumerates_same_venue_multi_account_bindings() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=_quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        ),
    )
    context = asyncio.run(runtime.ensure_active_context())
    secondary_binding_key = _seed_second_hyperliquid_binding(
        session_factory,
        mandate_key=context.mandate.mandate_key,
    )
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )

    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    binding_keys = {candidate.binding_key for candidate in assessment.candidates}

    assert context.bindings[0].binding.binding_key in binding_keys
    assert secondary_binding_key in binding_keys
    assert assessment.eligible_binding_count == 2
    assert {candidate.venue for candidate in assessment.candidates} == {Venue.HYPERLIQUID.value}


def test_routing_assessment_missing_data_is_explicit_and_inspectable() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(session_factory, top_of_book=None)
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )

    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))

    assert assessment.decision_status == RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA
    assert assessment.eligible_binding_count == 0
    assert assessment.ineligible_binding_count == 1
    assert assessment.missing_data == ["missing_quote_snapshot"]
    assert assessment.candidates[0].eligibility_status == (
        RoutingCandidateEligibilityStatus.INELIGIBLE_FOR_FUTURE_SELECTION
    )
    assert "missing_quote_snapshot" in assessment.candidates[0].missing_data


def test_routing_assessment_no_eligible_bindings_is_explicit() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=_quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        ),
        supports_order_submission=False,
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))

    assert assessment.decision_status == RoutingAssessmentDecisionStatus.NO_ELIGIBLE_BINDINGS
    assert assessment.eligible_binding_count == 0
    assert assessment.ineligible_binding_count == 1
    assert "no_eligible_bindings" in assessment.reason_codes
    assert "venue_order_submission_unsupported" in assessment.candidates[0].reason_codes
    assert "adapter_order_submission_unsupported" in assessment.candidates[0].reason_codes


def test_routing_assessment_refuses_non_routing_required_desired_trade() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=_quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        ),
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
        status=MandateDesiredTradeStatus.DRAFT,
    )

    try:
        asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
        assert False, "Expected routing assessment to reject non-routing-required desired trade."
    except RoutingAssessmentError as exc:
        assert exc.reason_code == "desired_trade_not_routing_required"


def test_routing_assessment_shape_does_not_contain_route_decision_fields() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=_quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        ),
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))

    payload = {
        "assessment_id": assessment.assessment_id,
        "decision_status": assessment.decision_status.value,
        "request": {
            "routing_request_id": assessment.request.routing_request_id,
            "desired_trade_key": assessment.request.desired_trade_key,
        },
        "candidates": [asdict(candidate) for candidate in assessment.candidates],
    }
    _assert_no_forbidden_output_keys(payload)


def test_phase50_public_surfaces_do_not_use_smart_route_language() -> None:
    root = Path(__file__).resolve().parents[1]
    checked_paths = [
        "apps/api/app/api/routes.py",
        "core/schemas/api.py",
        "services/routing/service.py",
        "docs/architecture.md",
        "docs/strategy.md",
        "README.md",
    ]
    forbidden_phrases = [
        "best route",
        "smart route",
        "optimal venue",
        "recommended venue",
        "best binding",
        "auto route",
        "execution plan",
        "route_decision",
        "execution_plan",
        "child_intent_plan",
        "confidence_score",
        "quality_score",
    ]
    for relative_path in checked_paths:
        text = (root / relative_path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_phrases:
            assert phrase not in text, f"{relative_path} contains forbidden routing language: {phrase}"
