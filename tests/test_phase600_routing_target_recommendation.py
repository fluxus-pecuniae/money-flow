from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.app.dependencies import get_routing_assessment_service
from apps.api.app.main import app
from core.domain.enums import (
    Environment,
    MandateDesiredTradeStatus,
    RouteReadinessAuditStatus,
    RoutingTargetRecommendationStatus,
    TradeTargetScope,
    Venue,
)
from db.models import (
    ExchangeAccountSnapshotModel,
    ExecutionReadinessEvaluationModel,
    MandateAccountBindingModel,
    MandateDesiredTradeModel,
    OrderIntentModel,
    RouteReadinessCandidateAuditModel,
    RouteReadinessAuditModel,
    RoutingAssessmentCandidateModel,
    RoutingTargetChoiceModel,
    RoutingTargetRecommendationModel,
    SubmittedOrderModel,
    StrategyMandateModel,
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
from tests.test_phase5101_route_readiness_audit import _seed_assessment
from services.routing.service import RoutingAssessmentError
from services.runtime.context import DefaultRuntimeContextService


client = TestClient(app)


def _make_all_route_readiness_candidates_ready(session_factory) -> None:
    with session_factory() as session:
        symbol = session.scalar(select(SymbolModel))
        assert symbol is not None
        symbol.raw_metadata = {"minimum_notional": "10"}
        candidates = list(
            session.scalars(
                select(RoutingAssessmentCandidateModel).order_by(
                    RoutingAssessmentCandidateModel.binding_key.asc()
                )
            ).all()
        )
        assert candidates
        for candidate in candidates:
            account = session.get(VenueAccountModel, candidate.venue_account_ref_id)
            assert account is not None
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
                    account_address=account.account_address or account.venue_account_key,
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


def _ready_audit(session_factory):
    routing, assessment, desired_trade_key, _context = _seed_assessment(session_factory)
    _make_all_route_readiness_candidates_ready(session_factory)
    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    assert audit.overall_status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
    assert audit.ready_candidate_count == 1
    return routing, audit, desired_trade_key


def _multi_ready_audit(session_factory):
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
    _seed_second_hyperliquid_binding(
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
    _make_all_route_readiness_candidates_ready(session_factory)
    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    assert audit.overall_status == RouteReadinessAuditStatus.READY_FOR_RECOMMENDATION
    assert audit.ready_candidate_count == 2
    return routing, audit


def _set_binding_recommendation_priorities(
    session_factory,
    priorities_by_binding_key: dict[str, object],
) -> None:
    with session_factory() as session:
        for binding_key, priority in priorities_by_binding_key.items():
            binding = session.scalar(
                select(MandateAccountBindingModel).where(
                    MandateAccountBindingModel.binding_key == binding_key
                )
            )
            assert binding is not None
            binding.target_recommendation_priority = priority  # type: ignore[assignment]
        session.commit()


def _assert_no_downstream_artifacts(session_factory, *, recommendations: int = 1) -> None:
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RoutingTargetRecommendationModel)) == recommendations
        assert session.scalar(select(func.count()).select_from(RoutingTargetChoiceModel)) == 0
        assert session.scalar(select(func.count()).select_from(OrderIntentModel)) == 0
        assert session.scalar(select(func.count()).select_from(ExecutionReadinessEvaluationModel)) == 0
        assert session.scalar(select(func.count()).select_from(SubmittedOrderModel)) == 0


def _assert_no_routing_leakage(payload: object) -> None:
    forbidden = {
        "best_binding",
        "optimal_venue",
        "rank",
        "score",
        "price_score",
        "quality_score",
        "venue_score",
        "confidence_score",
        "allocation",
        "allocation_weight",
        "route_plan",
        "route_executor",
        "auto_submit",
        "target_reselection",
    }
    if isinstance(payload, dict):
        assert not (set(payload) & forbidden)
        for value in payload.values():
            _assert_no_routing_leakage(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_routing_leakage(value)


def _mutate_ready_candidate_quote_observed_at(
    session_factory,
    audit,
    observed_at: object,
    *,
    threshold_seconds: object = 60,
    binding_key: str | None = None,
) -> None:
    with session_factory() as session:
        audit_model = session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.route_readiness_audit_id == audit.route_readiness_audit_id
            )
        )
        candidate_query = select(RouteReadinessCandidateAuditModel).where(
            RouteReadinessCandidateAuditModel.route_readiness_audit_id
            == audit.route_readiness_audit_id
        )
        if binding_key is not None:
            candidate_query = candidate_query.where(
                RouteReadinessCandidateAuditModel.binding_key == binding_key
            )
        candidate_model = session.scalar(candidate_query)
        assert audit_model is not None
        assert candidate_model is not None
        audit_model.evaluated_at = datetime.now(UTC)
        candidate_model.fact_snapshot_json = {
            **candidate_model.fact_snapshot_json,
            "quote_observed_at": observed_at,
            "quote_freshness_threshold_seconds": threshold_seconds,
        }
        session.commit()


def test_single_ready_candidate_creates_non_executing_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )
    fetched = asyncio.run(
        routing.get_routing_target_recommendation(recommendation.routing_target_recommendation_id)
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    assert fetched.routing_target_recommendation_id == recommendation.routing_target_recommendation_id
    assert recommendation.policy_name == "single_ready_candidate_only"
    assert recommendation.recommended_binding_ref_id == ready_candidate.binding_ref_id
    assert recommendation.recommended_binding_key == ready_candidate.binding_key
    assert recommendation.recommended_venue_account_ref_id == ready_candidate.venue_account_ref_id
    assert recommendation.recommended_venue_account_key == ready_candidate.venue_account_key
    assert recommendation.recommended_venue == ready_candidate.venue
    assert recommendation.recommended_exchange_symbol == ready_candidate.exchange_symbol
    assert recommendation.non_executing is True
    assert recommendation.target_choice_created is False
    assert recommendation.child_intent_created is False
    assert recommendation.submitted_order_created is False
    assert "recommended_single_ready_candidate" in recommendation.reason_codes
    assert recommendation.provenance["non_ranking"] is True
    assert recommendation.provenance["non_scoring"] is True
    fetched_audit = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))
    assert fetched_audit.recommendation_created is True
    assert "cbbo_used" not in recommendation.provenance
    assert "fanout_created" not in recommendation.provenance
    assert "auto_submit" not in recommendation.provenance
    assert "target_reselection" not in recommendation.provenance
    _assert_no_routing_leakage(asdict(recommendation))
    _assert_no_downstream_artifacts(session_factory)


def test_quote_fresh_at_audit_but_stale_at_recommendation_blocks() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert recommendation.recommended_binding_ref_id is None
    assert "quote_stale_at_recommendation" in recommendation.reason_codes
    assert "quote_stale_at_recommendation" in recommendation.stale_data
    assert "quote_stale_at_recommendation" in recommendation.blocking_reasons
    fetched_audit = asyncio.run(routing.get_route_readiness_audit(audit.route_readiness_audit_id))
    assert fetched_audit.recommendation_created is True
    _assert_no_downstream_artifacts(session_factory)


def test_recommendation_api_rejects_invalid_policy_names_without_500() -> None:
    cases = [
        " ",
        "x" * 65,
        "price_ranker",
    ]
    for policy_name in cases:
        session_factory = build_test_session_factory()
        routing, audit, _desired_trade_key = _ready_audit(session_factory)
        app.dependency_overrides[get_routing_assessment_service] = lambda: routing
        try:
            response = client.post(
                "/api/v1/routing-target-recommendations/from-route-readiness-audit",
                json={
                    "route_readiness_audit_id": audit.route_readiness_audit_id,
                    "policy_name": policy_name,
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422
        assert response.status_code != 500
        _assert_no_downstream_artifacts(session_factory, recommendations=0)


def test_service_rejects_malformed_policy_names_before_persistence() -> None:
    cases = [
        " ",
        "x" * 65,
    ]
    for policy_name in cases:
        session_factory = build_test_session_factory()
        routing, audit, _desired_trade_key = _ready_audit(session_factory)

        with pytest.raises(RoutingAssessmentError) as exc:
            asyncio.run(
                routing.create_routing_target_recommendation_from_route_readiness_audit(
                    audit.route_readiness_audit_id,
                    policy_name=policy_name,
                )
            )

        assert exc.value.reason_code == "routing_target_recommendation_policy_invalid"
        _assert_no_downstream_artifacts(session_factory, recommendations=0)


def test_missing_or_malformed_quote_observed_at_blocks_recommendation() -> None:
    cases = [
        (None, "quote_freshness_unknown"),
        ("not-a-datetime", "quote_observed_at_malformed"),
        (datetime.now().isoformat(), "quote_observed_at_malformed"),
    ]
    for observed_at, expected_reason in cases:
        session_factory = build_test_session_factory()
        routing, audit, _desired_trade_key = _ready_audit(session_factory)
        _mutate_ready_candidate_quote_observed_at(session_factory, audit, observed_at)

        recommendation = asyncio.run(
            routing.create_routing_target_recommendation_from_route_readiness_audit(
                audit.route_readiness_audit_id
            )
        )

        assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
        assert recommendation.recommended_binding_ref_id is None
        assert expected_reason in recommendation.reason_codes
        assert expected_reason in recommendation.missing_data
        assert expected_reason in recommendation.blocking_reasons
        _assert_no_downstream_artifacts(session_factory)


def test_zero_ready_candidates_blocks_without_downstream_artifacts() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)
    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    assert audit.ready_candidate_count == 0

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_NO_READY_CANDIDATE
    assert recommendation.recommended_binding_ref_id is None
    assert "no_ready_candidate" in recommendation.reason_codes
    assert "no_ready_candidate" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_multiple_ready_candidates_blocks_without_sort_order_selection() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES
    )
    assert recommendation.ready_candidate_count == 2
    assert recommendation.recommended_binding_ref_id is None
    assert "multiple_ready_candidates" in recommendation.reason_codes
    assert "multiple_ready_candidates_without_priority_policy" in recommendation.reason_codes
    _assert_no_routing_leakage(asdict(recommendation))
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_recommends_single_winning_priority_candidate() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: 20,
            second_candidate.binding_key: 10,
        },
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
    )
    assert recommendation.policy_name == "explicit_binding_priority"
    assert recommendation.recommended_binding_ref_id == second_candidate.binding_ref_id
    assert recommendation.recommended_binding_key == second_candidate.binding_key
    assert recommendation.recommended_venue_account_ref_id == second_candidate.venue_account_ref_id
    assert recommendation.recommended_venue_account_key == second_candidate.venue_account_key
    assert recommendation.recommended_venue == second_candidate.venue
    assert recommendation.recommended_exchange_symbol == second_candidate.exchange_symbol
    assert "explicit_binding_priority_policy_requested" in recommendation.reason_codes
    assert "binding_priority_selected" in recommendation.reason_codes
    policy_facts = recommendation.provenance["policy_facts"]
    assert policy_facts["priority_source"] == "mandate_account_bindings.target_recommendation_priority"
    assert policy_facts["priority_order"] == "lower_integer_wins"
    assert policy_facts["selected_priority"] == 10
    _assert_no_routing_leakage(asdict(recommendation))
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_missing_priority_blocks() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, _second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {first_candidate.binding_key: 1},
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    assert recommendation.recommended_binding_ref_id is None
    assert "binding_priority_missing" in recommendation.reason_codes
    assert "binding_priority_missing" in recommendation.missing_data
    assert "binding_priority_missing" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_tie_blocks() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: 1,
            second_candidate.binding_key: 1,
        },
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_MULTIPLE_READY_CANDIDATES
    )
    assert recommendation.recommended_binding_ref_id is None
    assert "binding_priority_tie" in recommendation.reason_codes
    assert "binding_priority_tie" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_malformed_priority_blocks() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: "not-an-int",
            second_candidate.binding_key: 1,
        },
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    assert recommendation.recommended_binding_ref_id is None
    assert "binding_priority_malformed" in recommendation.reason_codes
    assert "binding_priority_malformed" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_still_revalidates_current_binding_truth() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: 20,
            second_candidate.binding_key: 10,
        },
    )
    with session_factory() as session:
        selected_binding = session.get(MandateAccountBindingModel, second_candidate.binding_ref_id)
        assert selected_binding is not None
        selected_binding.enabled = False
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert recommendation.recommended_binding_ref_id is None
    assert "binding_priority_selected" in recommendation.reason_codes
    assert "binding_disabled" in recommendation.reason_codes
    assert "binding_disabled" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_explicit_binding_priority_selected_stale_quote_blocks() -> None:
    session_factory = build_test_session_factory()
    routing, audit = _multi_ready_audit(session_factory)
    first_candidate, second_candidate = audit.candidates
    _set_binding_recommendation_priorities(
        session_factory,
        {
            first_candidate.binding_key: 20,
            second_candidate.binding_key: 10,
        },
    )
    _mutate_ready_candidate_quote_observed_at(
        session_factory,
        audit,
        (datetime.now(UTC) - timedelta(seconds=90)).isoformat(),
        threshold_seconds=60,
        binding_key=second_candidate.binding_key,
    )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert recommendation.recommended_binding_ref_id is None
    assert recommendation.recommended_venue_account_ref_id is None
    assert recommendation.recommended_venue is None
    assert "binding_priority_selected" in recommendation.reason_codes
    assert "quote_stale_at_recommendation" in recommendation.reason_codes
    assert "quote_stale_at_recommendation" in recommendation.stale_data
    assert "quote_stale_at_recommendation" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_target_recommendation_priority_clear_semantics_are_explicit() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    candidate = audit.candidates[0]
    assert audit.mandate_key is not None
    assert candidate.venue_account_key is not None
    assert candidate.binding_key is not None
    runtime = DefaultRuntimeContextService(routing.settings, session_factory=session_factory)

    updated = asyncio.run(
        runtime.bind_account(
            mandate_key=audit.mandate_key,
            venue_account_key=candidate.venue_account_key,
            binding_key=candidate.binding_key,
            target_recommendation_priority=7,
        )
    )
    assert updated.target_recommendation_priority == 7

    preserved = asyncio.run(
        runtime.bind_account(
            mandate_key=audit.mandate_key,
            venue_account_key=candidate.venue_account_key,
            binding_key=candidate.binding_key,
        )
    )
    assert preserved.target_recommendation_priority == 7

    cleared = asyncio.run(
        runtime.bind_account(
            mandate_key=audit.mandate_key,
            venue_account_key=candidate.venue_account_key,
            binding_key=candidate.binding_key,
            clear_target_recommendation_priority=True,
        )
    )
    assert cleared.target_recommendation_priority is None
    with pytest.raises(ValueError):
        asyncio.run(
            runtime.bind_account(
                mandate_key=audit.mandate_key,
                venue_account_key=candidate.venue_account_key,
                binding_key=candidate.binding_key,
                target_recommendation_priority=3,
                clear_target_recommendation_priority=True,
            )
        )

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="explicit_binding_priority",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    assert recommendation.recommended_binding_ref_id is None
    assert "binding_priority_missing" in recommendation.reason_codes
    assert "binding_priority_missing" in recommendation.missing_data
    assert "binding_priority_missing" in recommendation.blocking_reasons
    _assert_no_downstream_artifacts(session_factory)


def test_unknown_recommendation_policy_persists_blocked_record() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id,
            policy_name="price_ranker",
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_INVALID_AUDIT
    assert recommendation.policy_name == "price_ranker"
    assert recommendation.recommended_binding_ref_id is None
    assert "routing_target_recommendation_policy_unknown" in recommendation.reason_codes
    assert "routing_target_recommendation_policy_unknown" in recommendation.blocking_reasons
    _assert_no_routing_leakage(asdict(recommendation))
    _assert_no_downstream_artifacts(session_factory)


def test_audit_not_ready_blocks_even_with_ready_candidate_drift() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    with session_factory() as session:
        audit_model = session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.route_readiness_audit_id == audit.route_readiness_audit_id
            )
        )
        assert audit_model is not None
        audit_model.overall_status = RouteReadinessAuditStatus.POLICY_BLOCKED
        audit_model.global_blocking_reasons_json = ["policy_blocked"]
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_AUDIT_NOT_READY
    assert "route_readiness_audit_not_ready" in recommendation.reason_codes
    assert "policy_blocked" in recommendation.reason_codes
    assert "policy_blocked" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_stale_audit_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    with session_factory() as session:
        audit_model = session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.route_readiness_audit_id == audit.route_readiness_audit_id
            )
        )
        assert audit_model is not None
        audit_model.evaluated_at = datetime.now(UTC) - timedelta(minutes=5)
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_AUDIT
    assert "route_readiness_audit_stale" in recommendation.reason_codes
    assert "route_readiness_audit_stale" in recommendation.stale_data
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_stale_desired_trade_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key
            )
        )
        assert desired_trade is not None
        desired_trade.status = MandateDesiredTradeStatus.ROUTED
        desired_trade.side = None
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_STALE_DESIRED_TRADE
    )
    assert "desired_trade_not_routing_required" in recommendation.reason_codes
    assert "desired_trade_missing_side" in recommendation.reason_codes
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_disabled_mandate_after_ready_audit_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    with session_factory() as session:
        mandate = session.get(StrategyMandateModel, audit.strategy_mandate_ref_id)
        assert mandate is not None
        mandate.enabled = False
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_STALE_DESIRED_TRADE
    )
    assert "mandate_inactive" in recommendation.reason_codes
    assert "mandate_inactive" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_inactive_symbol_mapping_after_ready_audit_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    with session_factory() as session:
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == ready_candidate.instrument_ref_id,
                SymbolModel.venue == ready_candidate.venue,
                SymbolModel.symbol == ready_candidate.symbol,
                SymbolModel.exchange_symbol == ready_candidate.exchange_symbol,
            )
        )
        assert symbol is not None
        symbol.is_active = False
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert "symbol_inactive" in recommendation.reason_codes
    assert "symbol_inactive" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_non_trading_symbol_mapping_after_ready_audit_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    with session_factory() as session:
        symbol = session.scalar(
            select(SymbolModel).where(
                SymbolModel.instrument_ref_id == ready_candidate.instrument_ref_id,
                SymbolModel.venue == ready_candidate.venue,
                SymbolModel.symbol == ready_candidate.symbol,
                SymbolModel.exchange_symbol == ready_candidate.exchange_symbol,
            )
        )
        assert symbol is not None
        symbol.is_trading_eligible = False
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert "symbol_not_trading_eligible" in recommendation.reason_codes
    assert "symbol_not_trading_eligible" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_desired_trade_symbol_drift_after_ready_audit_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, desired_trade_key = _ready_audit(session_factory)
    with session_factory() as session:
        desired_trade = session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key
            )
        )
        assert desired_trade is not None
        desired_trade.symbol = "ETH"
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == (
        RoutingTargetRecommendationStatus.BLOCKED_STALE_DESIRED_TRADE
    )
    assert "desired_trade_symbol_mismatch" in recommendation.reason_codes
    assert "desired_trade_symbol_mismatch" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_stale_binding_or_account_blocks_recommendation() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    ready_candidate = audit.candidates[0]
    with session_factory() as session:
        binding = session.get(MandateAccountBindingModel, ready_candidate.binding_ref_id)
        account = session.get(VenueAccountModel, ready_candidate.venue_account_ref_id)
        assert binding is not None
        assert account is not None
        binding.enabled = False
        account.trading_enabled = False
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_STALE_CANDIDATE
    assert "binding_disabled" in recommendation.reason_codes
    assert "venue_account_trading_disabled" in recommendation.reason_codes
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_audit_level_blockers_remain_visible_when_zero_ready_candidates_block() -> None:
    session_factory = build_test_session_factory()
    routing, assessment, _desired_trade_key, _context = _seed_assessment(session_factory)
    audit = asyncio.run(routing.create_route_readiness_audit_from_assessment(assessment.assessment_id))
    assert audit.ready_candidate_count == 0
    with session_factory() as session:
        audit_model = session.scalar(
            select(RouteReadinessAuditModel).where(
                RouteReadinessAuditModel.route_readiness_audit_id == audit.route_readiness_audit_id
            )
        )
        assert audit_model is not None
        audit_model.global_blocking_reasons_json = ["audit_global_blocker_visible"]
        session.commit()

    recommendation = asyncio.run(
        routing.create_routing_target_recommendation_from_route_readiness_audit(
            audit.route_readiness_audit_id
        )
    )

    assert recommendation.status == RoutingTargetRecommendationStatus.BLOCKED_NO_READY_CANDIDATE
    assert "no_ready_candidate" in recommendation.reason_codes
    assert "route_readiness_audit_not_ready" in recommendation.reason_codes
    assert "route_readiness_audit_status_insufficient_data" in recommendation.reason_codes
    assert "route_readiness_audit_global_blockers_present" in recommendation.reason_codes
    assert "audit_global_blocker_visible" in recommendation.reason_codes
    assert "audit_global_blocker_visible" in recommendation.blocking_reasons
    assert recommendation.recommended_binding_ref_id is None
    _assert_no_downstream_artifacts(session_factory)


def test_recommendation_api_is_non_executing_and_inspectable() -> None:
    session_factory = build_test_session_factory()
    routing, audit, _desired_trade_key = _ready_audit(session_factory)
    app.dependency_overrides[get_routing_assessment_service] = lambda: routing
    try:
        create_response = client.post(
            "/api/v1/routing-target-recommendations/from-route-readiness-audit",
            json={"route_readiness_audit_id": audit.route_readiness_audit_id},
        )
        assert create_response.status_code == 200
        payload = create_response.json()
        get_response = client.get(
            "/api/v1/routing-target-recommendations/"
            f"{payload['routing_target_recommendation_id']}"
        )
        audit_response = client.get(
            f"/api/v1/route-readiness-audits/{audit.route_readiness_audit_id}"
        )
    finally:
        app.dependency_overrides.clear()

    assert get_response.status_code == 200
    assert audit_response.status_code == 200
    fetched = get_response.json()
    audit_payload = audit_response.json()
    assert payload["status"] == "recommended_single_ready_candidate"
    assert payload["policy_name"] == "single_ready_candidate_only"
    assert payload["non_executing"] is True
    assert payload["target_choice_created"] is False
    assert payload["child_intent_created"] is False
    assert payload["submitted_order_created"] is False
    assert fetched["routing_target_recommendation_id"] == payload["routing_target_recommendation_id"]
    assert audit_payload["recommendation_created"] is True
    _assert_no_routing_leakage(payload)
    _assert_no_downstream_artifacts(session_factory)
