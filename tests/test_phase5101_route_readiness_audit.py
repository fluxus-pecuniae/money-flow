from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    RouteReadinessAuditStatus,
    RoutingAssessmentDecisionStatus,
    TradeTargetScope,
    Venue,
)
from core.domain.models import TopOfBookSnapshot
from db.models import (
    ExchangeAccountSnapshotModel,
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RouteReadinessAuditModel,
    RouteReadinessCandidateAuditModel,
    RoutingAssessmentCandidateModel,
    RoutingTargetChoiceModel,
    SubmittedOrderModel,
    SymbolModel,
    VenueAccountModel,
)
from tests.test_phase3_strategy import build_test_session_factory, seed_symbol
from tests.test_phase50_routing_substrate import (
    _build_routing_service,
    _quote,
    _seed_desired_trade,
    _seed_second_hyperliquid_binding,
)


client = TestClient(app)


def _top_of_book(
    *,
    instrument_key: str,
    instrument_ref_id: str,
    observed_at: datetime,
) -> TopOfBookSnapshot:
    return TopOfBookSnapshot(
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        venue=Venue.HYPERLIQUID.value,
        symbol="BTC",
        bid_price=Decimal("100"),
        bid_size=Decimal("2"),
        ask_price=Decimal("101"),
        ask_size=Decimal("3"),
        observed_at=observed_at,
    )


def _seed_assessment(session_factory, *, top_of_book: TopOfBookSnapshot | None = None):
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    quote = (
        top_of_book
        if top_of_book is not None
        else _quote(
            Venue.HYPERLIQUID.value,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
        )
    )
    _settings, runtime, routing = _build_routing_service(
        session_factory,
        top_of_book=quote,
    )
    context = asyncio.run(runtime.ensure_active_context())
    desired_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
    )
    assessment = asyncio.run(routing.create_assessment_from_desired_trade(desired_trade_key))
    return routing, assessment, desired_trade_key, context


def _assert_no_downstream_artifacts(session_factory) -> None:
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RoutingTargetChoiceModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def _make_route_readiness_candidate_otherwise_ready(session_factory) -> None:
    with session_factory() as session:
        candidate = session.scalar(select(RoutingAssessmentCandidateModel))
        assert candidate is not None
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        symbol = session.scalar(select(SymbolModel))
        assert account is not None
        assert symbol is not None
        symbol.raw_metadata = {"minimum_notional": "10"}
        candidate.fact_snapshot_json = {
            **candidate.fact_snapshot_json,
            "account_snapshot_available": True,
            "fee_data_available": True,
            "margin_sufficiency_known": True,
            "recovery_support_known": True,
            "stale_quote_protection_known": True,
            "depth_required": False,
            "slippage_guard_present": True,
        }
        session.add(
            ExchangeAccountSnapshotModel(
                environment=Environment.TESTNET,
                venue_account_ref_id=account.id,
                venue=account.venue,
                account_address=account.account_address or "acct",
                equity=Decimal("10000"),
                available_balance=Decimal("10000"),
                margin_used=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_position_notional=Decimal("0"),
                cross_margin_summary={},
                margin_summary={},
                raw_payload={"source": "test"},
                observed_at=datetime.now(UTC),
            )
        )
        session.commit()


def _assert_no_routing_leakage(payload: object) -> None:
    forbidden = {
        "recommended_binding",
        "best_binding",
        "best_venue",
        "optimal_venue",
        "rank",
        "score",
        "price_score",
        "quality_score",
        "venue_score",
        "allocation",
        "allocation_weights",
        "route_plan",
        "route_executor",
        "target_reselection",
        "auto_submit",
    }
    if isinstance(payload, dict):
        assert not (set(payload) & forbidden)
        for value in payload.values():
            _assert_no_routing_leakage(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_routing_leakage(value)


def test_route_readiness_audit_from_desired_trade_is_persisted_and_non_selecting() -> None:
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

    audit = asyncio.run(routing.create_route_readiness_audit_from_desired_trade(desired_trade_key))
    fetched = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))

    assert audit.route_readiness_audit_id.startswith("rtraudit_")
    assert fetched.route_readiness_audit_id == audit.route_readiness_audit_id
    assert audit.routing_assessment_id is not None
    assert audit.non_selecting is True
    assert audit.recommendation_created is False
    assert audit.target_choice_created is False
    assert audit.child_intent_created is False
    assert audit.submitted_order_created is False
    assert audit.overall_status == RouteReadinessAuditStatus.INSUFFICIENT_DATA
    assert audit.provenance["target_recommendation"] == "not_created_by_route_readiness_audit"
    assert (
        audit.provenance["target_recommendation_next_step"]
        == "phase_6_0_0_single_ready_candidate_only"
    )
    assert audit.provenance["ready_for_recommendation_means"].startswith("required facts")
    assert len(audit.candidates) == 1
    candidate = audit.candidates[0]
    assert candidate.data_sources["quote"] == "derived_from_existing_assessment"
    assert candidate.fact_snapshot["quote_audit_source"] == "derived_from_existing_assessment"
    assert candidate.fact_snapshot["quote_original_source"] == "adapter_top_of_book"
    assert candidate.data_sources["balance"] == "unavailable"
    assert "fee_data_missing" in candidate.unavailable_data
    assert "balance_snapshot_missing" in candidate.missing_data
    assert "slippage_guard_missing" in candidate.missing_data
    assert "order_shape_policy_defaulted" in candidate.fact_snapshot["order_shape_policy_reason_codes"]
    assert "market_order_policy_defaulted" in candidate.fact_snapshot["order_shape_policy_reason_codes"]
    assert "market_order_policy_explicit" not in candidate.fact_snapshot["order_shape_policy_reason_codes"]
    assert candidate.fact_snapshot["non_selecting"] is True
    _assert_no_downstream_artifacts(session_factory)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RouteReadinessAuditModel)) == 1
        assert session.scalar(select(func.count()).select_from(RouteReadinessCandidateAuditModel)) == 1


def test_route_readiness_audit_from_existing_assessment_links_and_inspects() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _seed_assessment(session_factory)

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))

    assert audit.routing_assessment_id == assessment.assessment_id
    assert audit.desired_trade_key == desired_trade_key
    assert audit.candidate_count == len(assessment.candidates)
    assert "route_readiness_audit_non_selecting" in audit.global_reason_codes
    assert "recommendation_not_created" in audit.global_reason_codes
    assert audit.target_scope == TradeTargetScope.MANDATE
    assert audit.candidates[0].data_sources["quote"] == "derived_from_existing_assessment"
    assert audit.candidates[0].data_sources["quote"] != "venue_query"
    _assert_no_downstream_artifacts(session_factory)


def test_route_readiness_missing_and_stale_quote_blocks_recommendation_readiness() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, _symbol_id, instrument_key = seed_symbol(session_factory)
    _settings, runtime, routing = _build_routing_service(session_factory, top_of_book=None)
    context = asyncio.run(runtime.ensure_active_context())
    missing_quote_trade_key = _seed_desired_trade(
        session_factory,
        context=context,
        instrument_ref_id=instrument_ref_id,
        instrument_key=instrument_key,
        desired_trade_key="phase5101-missing-quote",
    )
    missing_assessment = asyncio.run(
        routing.create_assessment_from_desired_trade(missing_quote_trade_key)
    )
    missing_audit = asyncio.run(
        routing.create_route_readiness_audit_from_assessment(missing_assessment.assessment_id)
    )

    assert missing_assessment.decision_status == RoutingAssessmentDecisionStatus.INSUFFICIENT_DATA
    assert missing_audit.overall_status == RouteReadinessAuditStatus.INSUFFICIENT_DATA
    assert "quote_missing" in missing_audit.candidates[0].missing_data
    assert "missing_quote_snapshot" in missing_audit.candidates[0].missing_data
    assert missing_audit.candidates[0].data_sources["quote"] == "unavailable"

    stale_session_factory = build_test_session_factory()
    stale_instrument_ref_id, _symbol_id, stale_instrument_key = seed_symbol(stale_session_factory)
    stale_quote = _top_of_book(
        instrument_key=stale_instrument_key,
        instrument_ref_id=stale_instrument_ref_id,
        observed_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    _settings, stale_runtime, stale_routing = _build_routing_service(
        stale_session_factory,
        top_of_book=stale_quote,
    )
    stale_context = asyncio.run(stale_runtime.ensure_active_context())
    stale_trade_key = _seed_desired_trade(
        stale_session_factory,
        context=stale_context,
        instrument_ref_id=stale_instrument_ref_id,
        instrument_key=stale_instrument_key,
        desired_trade_key="phase5101-stale-quote",
    )
    stale_assessment = asyncio.run(stale_routing.create_assessment_from_desired_trade(stale_trade_key))
    stale_audit = asyncio.run(
        stale_routing.create_route_readiness_audit_from_assessment(stale_assessment.assessment_id)
    )

    assert stale_audit.overall_status == RouteReadinessAuditStatus.STALE_DATA
    assert "quote_stale" in stale_audit.candidates[0].stale_data


def test_route_readiness_candidate_blockers_are_reason_coded_before_selection() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)

    with session_factory() as session:
        candidate = session.scalar(select(RoutingAssessmentCandidateModel))
        assert candidate is not None
        binding = session.get(MandateAccountBindingModel, candidate.binding_ref_id)
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        symbol = session.scalar(
            select(SymbolModel).where(SymbolModel.id == candidate.fact_snapshot_json.get("symbol_id"))
        )
        if symbol is None:
            symbol = session.scalar(select(SymbolModel))
        assert binding is not None
        assert account is not None
        assert symbol is not None
        binding.enabled = False
        account.is_active = False
        symbol.is_active = False
        candidate.fact_snapshot_json = {
            **candidate.fact_snapshot_json,
            "supported_order_types": ["limit"],
        }
        session.commit()

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    candidate_audit = audit.candidates[0]

    assert audit.overall_status == RouteReadinessAuditStatus.POLICY_BLOCKED
    assert "binding_disabled" in candidate_audit.blocking_reasons
    assert "venue_account_inactive" in candidate_audit.blocking_reasons
    assert "symbol_mapping_missing" in candidate_audit.missing_data
    assert "order_type_unsupported" in candidate_audit.policy_blocks
    _assert_no_downstream_artifacts(session_factory)


def test_route_readiness_economic_truth_and_balance_source_are_explicit() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)

    with session_factory() as session:
        candidate = session.scalar(select(RoutingAssessmentCandidateModel))
        assert candidate is not None
        account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
        assert account is not None
        session.add(
            ExchangeAccountSnapshotModel(
                environment=Environment.TESTNET,
                venue_account_ref_id=account.id,
                venue=account.venue,
                account_address=account.account_address or "acct",
                equity=Decimal("10000"),
                available_balance=Decimal("10000"),
                margin_used=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_position_notional=Decimal("0"),
                cross_margin_summary={},
                margin_summary={},
                raw_payload={"source": "test"},
                observed_at=datetime.now(UTC),
            )
        )
        session.commit()

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    candidate_audit = audit.candidates[0]

    assert candidate_audit.data_sources["balance"] == "persistence"
    assert candidate_audit.fact_snapshot["available_balance"] == "10000.000000000000"
    assert candidate_audit.fact_snapshot["notional_sufficiency_source"] == "persistence_plus_top_of_book"
    assert "fee_data_missing" in candidate_audit.unavailable_data
    assert "margin_sufficiency_unknown" in candidate_audit.unavailable_data


def test_route_readiness_can_report_ready_for_recommendation_without_selecting() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)

    _make_route_readiness_candidate_otherwise_ready(session_factory)

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))

    assert audit.overall_status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
    assert audit.ready_candidate_count == 1
    assert audit.recommendation_created is False
    assert audit.target_choice_created is False
    assert audit.candidates[0].status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
    assert audit.candidates[0].missing_data == []
    assert audit.candidates[0].unavailable_data == []
    assert audit.candidates[0].data_sources["fees"] == "static_config"
    assert audit.candidates[0].data_sources["quote"] == "derived_from_existing_assessment"
    _assert_no_downstream_artifacts(session_factory)


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_reason"),
    [
        ("side", None, "desired_trade_missing_side"),
        ("desired_quantity", None, "desired_trade_missing_quantity"),
        ("desired_quantity", Decimal("0"), "desired_trade_invalid_quantity"),
        ("desired_quantity", Decimal("-0.01"), "desired_trade_invalid_quantity"),
    ],
)
def test_route_readiness_desired_trade_side_and_quantity_block_recommendation_readiness(
    field_name: str,
    field_value,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    routing, assessment, desired_trade_key, _context = _seed_assessment(session_factory)
    _make_route_readiness_candidate_otherwise_ready(session_factory)

    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key
            )
        )
        assert desired_trade is not None
        setattr(desired_trade, field_name, field_value)
        session.commit()

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))

    assert audit.overall_status != RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
    assert expected_reason in audit.global_blocking_reasons
    assert expected_reason in audit.global_reason_codes
    assert "not_ready_for_recommendation" in audit.global_reason_codes
    _assert_no_downstream_artifacts(session_factory)


@pytest.mark.parametrize(
    ("quote_ask_price", "expected_reason"),
    [
        ("NaN", "quote_price_non_finite"),
        ("sNaN", "quote_price_non_finite"),
        ("Infinity", "quote_price_non_finite"),
        ("-Infinity", "quote_price_non_finite"),
        ("not-a-price", "quote_price_malformed"),
        ("0", "quote_price_non_positive"),
        ("-1", "quote_price_non_positive"),
    ],
)
def test_route_readiness_malformed_or_invalid_quote_prices_block_without_crashing(
    quote_ask_price: str,
    expected_reason: str,
) -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)
    _make_route_readiness_candidate_otherwise_ready(session_factory)

    with session_factory() as session:
        candidate = session.scalar(select(RoutingAssessmentCandidateModel))
        assert candidate is not None
        candidate.fact_snapshot_json = {
            **candidate.fact_snapshot_json,
            "quote_available": True,
            "quote_ask_price": quote_ask_price,
        }
        session.commit()

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    candidate_audit = audit.candidates[0]

    assert audit.overall_status == RouteReadinessAuditStatus.INSUFFICIENT_DATA
    assert candidate_audit.status == RouteReadinessAuditStatus.INSUFFICIENT_DATA
    assert expected_reason in candidate_audit.missing_data
    assert expected_reason in candidate_audit.reason_codes
    assert "notional_sufficiency_unknown" in candidate_audit.missing_data
    assert candidate_audit.fact_snapshot["quote_ask_price_valid"] is False
    assert candidate_audit.fact_snapshot["quote_ask_price_invalid_reason"] == expected_reason
    _assert_no_downstream_artifacts(session_factory)


def test_route_readiness_same_venue_multi_account_keeps_account_facts_separate() -> None:
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

    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))

    assert audit.candidate_count == 2
    assert {candidate.venue for candidate in audit.candidates} == {Venue.HYPERLIQUID.value}
    assert secondary_binding_key in {candidate.binding_key for candidate in audit.candidates}
    assert len({candidate.venue_account_ref_id for candidate in audit.candidates}) == 2
    for candidate in audit.candidates:
        assert candidate.fact_snapshot["same_venue_multi_account_scope"] == "venue_account_ref_id"
        assert candidate.fact_snapshot["venue_global_fallback"] is False


def test_route_readiness_api_is_audit_only_and_inspectable() -> None:
    session_factory = build_test_session_factory()
    routing, _assessment, desired_trade_key, _context = _seed_assessment(session_factory)

    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        create_response = client.post(
            "/api/v1/route-readiness-audits/from-desired-trade",
            json={"desired_trade_key": desired_trade_key},
        )
        assert create_response.status_code == 200
        payload = create_response.json()
        assessment_response = client.post(
            "/api/v1/route-readiness-audits/from-assessment",
            json={"routing_assessment_id": payload["routing_assessment_id"]},
        )
        get_response = client.get(
            f"/api/v1/route-readiness-audits/{payload['route_readiness_audit_id']}"
        )
    finally:
        app.dependency_overrides.clear()

    assert assessment_response.status_code == 200
    assert assessment_response.json()["routing_assessment_id"] == payload["routing_assessment_id"]
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["route_readiness_audit_id"] == payload["route_readiness_audit_id"]
    assert fetched["non_selecting"] is True
    assert fetched["recommendation_created"] is False
    assert fetched["target_choice_created"] is False
    assert fetched["child_intent_created"] is False
    assert fetched["submitted_order_created"] is False
    assert fetched["candidates"][0]["data_sources"]["quote"] == "derived_from_existing_assessment"
    assert fetched["candidates"][0]["missing_data"]
    _assert_no_routing_leakage(fetched)
    _assert_no_downstream_artifacts(session_factory)
