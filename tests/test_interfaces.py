from core.interfaces.hyperliquid import HyperliquidAdapterContract
from core.interfaces.repositories import EventRepository, Repository
from core.interfaces.services import (
    AlertService,
    BacktestEngine,
    ExchangeAdapter,
    ExecutionService,
    HealthService,
    IndicatorService,
    MarketDataService,
    PortfolioService,
    RiskEngine,
    RoutingAssessmentService,
    StrategyEngine,
)


def test_service_interfaces_import() -> None:
    assert ExchangeAdapter is not None
    assert MarketDataService is not None
    assert IndicatorService is not None
    assert StrategyEngine is not None
    assert RiskEngine is not None
    assert RoutingAssessmentService is not None
    assert PortfolioService is not None
    assert ExecutionService is not None
    assert AlertService is not None
    assert BacktestEngine is not None
    assert HealthService is not None
    assert Repository is not None
    assert EventRepository is not None
    assert HyperliquidAdapterContract is not None


def test_risk_and_execution_interfaces_reflect_desired_trade_boundary() -> None:
    assert hasattr(RiskEngine, "evaluate_strategy_decision")
    assert hasattr(RiskEngine, "evaluate_desired_trade")
    assert hasattr(RiskEngine, "recent_evaluations")
    assert not hasattr(RiskEngine, "approve_desired_trade")
    assert hasattr(ExecutionService, "create_child_intent")
    assert hasattr(ExecutionService, "list_child_intents")
    assert hasattr(ExecutionService, "get_child_intent")
    assert hasattr(ExecutionService, "preview_child_intent")
    assert hasattr(ExecutionService, "assess_child_intent_readiness")
    assert hasattr(ExecutionService, "list_readiness_assessments")
    assert hasattr(ExecutionService, "submit_prepared_intent")
    assert hasattr(ExecutionService, "get_submitted_order")
    assert hasattr(ExecutionService, "list_submitted_orders")
    assert hasattr(ExecutionService, "reconcile_submitted_order")
    assert hasattr(ExecutionService, "cancel_submitted_order")
    assert hasattr(ExecutionService, "amend_submitted_order")
    assert hasattr(ExecutionService, "get_submitted_order_recovery_recommendation")
    assert hasattr(ExecutionService, "execute_submitted_order_recovery")
    assert hasattr(ExecutionService, "get_submitted_order_actionability")
    assert hasattr(ExecutionService, "list_submitted_order_events")
    assert not hasattr(ExecutionService, "create_order_intent")
    assert hasattr(RoutingAssessmentService, "create_assessment_from_desired_trade")
    assert hasattr(RoutingAssessmentService, "get_routing_assessment")
    assert hasattr(RoutingAssessmentService, "record_target_choice_from_assessment")
    assert hasattr(RoutingAssessmentService, "get_routing_target_choice")
    assert hasattr(RoutingAssessmentService, "list_routing_target_choices_for_assessment")
    assert hasattr(RoutingAssessmentService, "convert_target_choice_to_child_intent")
    assert not hasattr(RoutingAssessmentService, "submit")
