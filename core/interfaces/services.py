"""Service interfaces for exchange, data, strategy, risk, and execution layers."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from core.config.settings import AppSettings
from core.domain.enums import ExecutionReadinessOutcome, MandateDesiredTradeStatus
from core.domain.models import (
    ActiveMandateContext,
    BindingQuoteSnapshot,
    BindingRoutingCandidate,
    Candle,
    CandleSyncCheckpoint,
    Client,
    ExchangeAccountSnapshot,
    ExchangeSessionState,
    ExchangeStatus,
    Fill,
    HealthEvent,
    IndicatorSnapshot,
    Instrument,
    MarketDataHealth,
    MandateMarketDataSourcePolicy,
    MandateDesiredTrade,
    DesiredTradeConvertibilityAssessment,
    ExecutionReadinessAssessment,
    OrderBookDepthSummary,
    OrderIntent,
    PortfolioSnapshot,
    PortfolioBootstrapSummary,
    PreparedVenueOrder,
    Position,
    PositionAttributionOverlay,
    RiskEvaluation,
    RiskEvent,
    RouteReadinessAudit,
    RoutingAssessment,
    RoutingTargetRecommendation,
    RoutingTargetChoice,
    RoutingTargetChoiceConversionResult,
    RoutedOrderShapePolicyInput,
    SignalEvent,
    MandateAccountBinding,
    StrategyComponentConfig,
    StrategyMandate,
    StrategyEvaluationInput,
    StrategyEvaluationResult,
    StrategyDecision,
    StrategyFamilyStatus,
    SubmittedOrder,
    SubmittedOrderActionability,
    SubmittedOrderLifecycleEvent,
    SubmittedOrderLifecycleUpdate,
    SubmittedOrderPrivateFillEvidence,
    SubmittedOrderRecoveryExecutionResult,
    SubmittedOrderRecoveryRecommendation,
    SymbolMetadata,
    TopOfBookSnapshot,
    VenueAccount,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueIntegrationSummary,
    VenueOrderConstraints,
    VenuePrivateOpenOrder,
    VenuePrivateStateSummary,
)


class ExchangeAdapter(Protocol):
    async def connect(self) -> ExchangeSessionState: ...

    async def disconnect(self) -> None: ...

    async def sync_symbols(self) -> Sequence[SymbolMetadata]: ...

    async def list_instruments(self) -> Sequence[Instrument]: ...

    async def get_session_state(self) -> ExchangeSessionState: ...

    async def submit_order(self, intent: OrderIntent) -> SubmittedOrder: ...

    async def reconcile_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate: ...

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate: ...

    async def amend_order(
        self,
        submitted_order: SubmittedOrder,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrderLifecycleUpdate: ...

    async def fetch_open_positions(self, venue_account_ref_id: str | None = None) -> Sequence[Position]: ...

    async def fetch_open_positions_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Position]]: ...

    async def fetch_recent_fills(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[Fill]: ...

    async def fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]: ...

    async def fetch_open_orders(
        self,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[VenuePrivateOpenOrder]: ...

    async def fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]: ...

    async def fetch_retry_private_fill_evidence(
        self,
        submitted_order: SubmittedOrder,
        *,
        limit: int = 100,
    ) -> SubmittedOrderPrivateFillEvidence: ...

    async def get_exchange_status(self) -> ExchangeStatus: ...

    async def get_venue_capabilities(self) -> VenueCapabilities: ...

    async def get_account_connectivity(self) -> VenueAccountConnectivity: ...

    async def read_account_snapshot(self) -> ExchangeAccountSnapshot | None: ...

    async def get_private_state_summary(self) -> VenuePrivateStateSummary: ...

    async def get_order_constraints(
        self,
        *,
        instrument_key: str | None = None,
        instrument_ref_id: str | None = None,
        symbol: str | None = None,
    ) -> VenueOrderConstraints | None: ...

    async def prepare_order_preview(self, intent: OrderIntent) -> PreparedVenueOrder: ...

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]: ...

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None: ...

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None: ...


class InstrumentCatalogProvider(Protocol):
    async def sync_symbols(self) -> Sequence[SymbolMetadata]: ...

    async def list_instruments(self) -> Sequence[Instrument]: ...


class CandleSnapshotProvider(Protocol):
    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]: ...


class ExecutionMarketDataProvider(Protocol):
    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None: ...

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None: ...


class MarketDataService(Protocol):
    async def bootstrap_candles(
        self,
        symbols: Sequence[str],
        timeframes: Sequence[str],
        lookback_bars: int,
    ) -> int: ...

    async def ingest_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[Candle]: ...

    async def get_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[Candle]: ...

    async def get_health(self) -> MarketDataHealth: ...

    async def get_checkpoint(
        self,
        symbol: str,
        timeframe: str,
    ) -> CandleSyncCheckpoint | None: ...

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None: ...

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None: ...


class IndicatorService(Protocol):
    async def compute_snapshot(self, candles: Sequence[Candle]) -> IndicatorSnapshot: ...

    async def refresh_snapshots(
        self,
        instrument_ref_id: str,
        symbol: str,
        venue: str,
        timeframe: str,
    ) -> int: ...

    async def load_latest_snapshot(
        self,
        instrument_ref_id: str,
        venue: str,
        timeframe: str,
    ) -> IndicatorSnapshot | None: ...


class StrategyEngine(Protocol):
    settings: AppSettings

    async def evaluate(self, evaluation_input: StrategyEvaluationInput) -> StrategyEvaluationResult: ...

    async def emit_signal(self, decision: StrategyDecision) -> SignalEvent | None: ...

    async def get_family_status(self) -> StrategyFamilyStatus: ...

    async def evaluate_sleeve(
        self,
        sleeve_id: str,
        *,
        symbols: Sequence[str] | None = None,
    ) -> list[StrategyEvaluationResult]: ...

    async def recent_decisions(
        self,
        *,
        sleeve_id: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[StrategyDecision]: ...

    async def recent_signals(
        self,
        *,
        sleeve_id: str | None = None,
        limit: int = 100,
    ) -> list[SignalEvent]: ...

    async def latest_indicator_snapshots(
        self,
        *,
        timeframe: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[IndicatorSnapshot]: ...


class RiskEngine(Protocol):
    async def evaluate_strategy_decision(self, decision_id: str) -> RiskEvaluation: ...

    async def evaluate_desired_trade(self, desired_trade: MandateDesiredTrade) -> RiskEvaluation: ...

    async def recent_evaluations(
        self,
        *,
        outcome: str | None = None,
        desired_trade_status: MandateDesiredTradeStatus | None = None,
        limit: int = 100,
    ) -> Sequence[RiskEvaluation]: ...

    async def get_kill_switch_state(self) -> bool: ...


class PortfolioService(Protocol):
    async def get_open_positions(
        self,
        venue_account_ref_id: str | None = None,
        account_address: str | None = None,
    ) -> Sequence[Position]: ...

    async def get_position_attribution_overlays(
        self,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[PositionAttributionOverlay]: ...

    async def get_latest_account_snapshot(
        self,
        venue_account_ref_id: str | None = None,
    ) -> ExchangeAccountSnapshot | None: ...

    async def get_recent_fills(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[Fill]: ...

    async def get_recent_submitted_orders(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[SubmittedOrder]: ...

    async def get_open_submitted_orders(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
        account_address: str | None = None,
    ) -> Sequence[SubmittedOrder]: ...

    async def get_bootstrap_summary(self) -> PortfolioBootstrapSummary: ...

    async def get_latest_snapshot(self) -> PortfolioSnapshot | None: ...

    async def refresh_snapshot(self) -> PortfolioSnapshot: ...


class ExecutionService(Protocol):
    """Downstream child-intent boundary.

    Execution services should operate on binding/account-targeted child intents,
    not on mandate-level desired trades. Child intents may be prepared once a
    specific binding/account target is known, whether from future routing or
    from naturally binding-scoped reduce/close actions.
    """

    async def create_child_intent(
        self,
        desired_trade: MandateDesiredTrade,
        candidate: BindingRoutingCandidate,
    ) -> OrderIntent: ...

    async def list_child_intents(
        self,
        *,
        desired_trade_key: str | None = None,
        binding_key: str | None = None,
        limit: int = 100,
    ) -> Sequence[OrderIntent]: ...

    async def get_child_intent(self, intent_id: str) -> OrderIntent: ...

    async def submit_prepared_intent(self, intent: OrderIntent) -> SubmittedOrder: ...

    async def get_submitted_order(self, submitted_order_id: str) -> SubmittedOrder: ...

    async def list_submitted_orders(
        self,
        *,
        intent_id: str | None = None,
        binding_key: str | None = None,
        venue_account_ref_id: str | None = None,
        venue: str | None = None,
        limit: int = 100,
    ) -> Sequence[SubmittedOrder]: ...

    async def reconcile_submitted_order(self, submitted_order_id: str) -> SubmittedOrder: ...

    async def reconcile_fills(self, submitted_order_id: str) -> Sequence[Fill]: ...

    async def cancel_submitted_order(self, submitted_order_id: str) -> SubmittedOrder: ...

    async def amend_submitted_order(
        self,
        submitted_order_id: str,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrder: ...

    async def get_submitted_order_recovery_recommendation(
        self,
        submitted_order_id: str,
    ) -> SubmittedOrderRecoveryRecommendation: ...

    async def execute_submitted_order_recovery(
        self,
        submitted_order_id: str,
        *,
        action: str | None = None,
    ) -> SubmittedOrderRecoveryExecutionResult: ...

    async def get_submitted_order_actionability(
        self,
        submitted_order_id: str,
    ) -> SubmittedOrderActionability: ...

    async def list_submitted_order_events(
        self,
        *,
        submitted_order_id: str | None = None,
        intent_id: str | None = None,
        limit: int = 100,
    ) -> Sequence[SubmittedOrderLifecycleEvent]: ...

    async def preview_child_intent(self, intent_id: str) -> PreparedVenueOrder: ...

    async def assess_child_intent_readiness(
        self,
        intent_id: str,
    ) -> ExecutionReadinessAssessment: ...

    async def list_readiness_assessments(
        self,
        *,
        intent_id: str | None = None,
        outcome: ExecutionReadinessOutcome | None = None,
        limit: int = 100,
    ) -> Sequence[ExecutionReadinessAssessment]: ...


class MandateTradePlanningService(Protocol):
    async def get_market_data_source_policy(
        self,
        *,
        mandate_key: str | None = None,
    ) -> MandateMarketDataSourcePolicy: ...

    async def inspect_decision_convertibility(
        self,
        decision_id: str,
    ) -> DesiredTradeConvertibilityAssessment: ...

    async def preview_desired_trade_from_decision(
        self,
        decision_id: str,
        *,
        persist: bool = False,
    ) -> MandateDesiredTrade: ...

    async def list_desired_trades(
        self,
        *,
        mandate_key: str | None = None,
        component_key: str | None = None,
        status: MandateDesiredTradeStatus | None = None,
        limit: int = 100,
    ) -> Sequence[MandateDesiredTrade]: ...

    async def list_routing_candidates(
        self,
        *,
        symbol: str | None = None,
        instrument_key: str | None = None,
        component_key: str | None = None,
        mandate_key: str | None = None,
    ) -> Sequence[BindingRoutingCandidate]: ...

    async def list_binding_quotes(
        self,
        *,
        symbol: str | None = None,
        instrument_key: str | None = None,
        component_key: str | None = None,
        mandate_key: str | None = None,
    ) -> Sequence[BindingQuoteSnapshot]: ...


class RoutingAssessmentService(Protocol):
    async def create_assessment_from_desired_trade(
        self,
        desired_trade_key: str,
    ) -> RoutingAssessment: ...

    async def get_routing_assessment(self, assessment_id: str) -> RoutingAssessment: ...

    async def create_route_readiness_audit_from_desired_trade(
        self,
        desired_trade_key: str,
    ) -> RouteReadinessAudit: ...

    async def create_route_readiness_audit_from_assessment(
        self,
        routing_assessment_id: str,
    ) -> RouteReadinessAudit: ...

    async def get_route_readiness_audit(self, route_readiness_audit_id: str) -> RouteReadinessAudit: ...

    async def create_routing_target_recommendation_from_route_readiness_audit(
        self,
        route_readiness_audit_id: str,
        *,
        policy_name: str | None = None,
    ) -> RoutingTargetRecommendation: ...

    async def get_routing_target_recommendation(
        self,
        routing_target_recommendation_id: str,
    ) -> RoutingTargetRecommendation: ...

    async def accept_routing_target_recommendation_to_target_choice(
        self,
        routing_target_recommendation_id: str,
        *,
        approval_note: str | None = None,
        requested_by: str | None = None,
    ) -> RoutingTargetChoice: ...

    async def record_target_choice_from_assessment(
        self,
        *,
        routing_assessment_id: str,
        binding_ref_id: str | None = None,
        binding_key: str | None = None,
        approval_note: str | None = None,
        requested_by: str | None = None,
    ) -> RoutingTargetChoice: ...

    async def get_routing_target_choice(self, target_choice_id: str) -> RoutingTargetChoice: ...

    async def list_routing_target_choices_for_assessment(
        self,
        routing_assessment_id: str,
    ) -> Sequence[RoutingTargetChoice]: ...

    async def convert_target_choice_to_child_intent(
        self,
        target_choice_id: str,
        order_shape_policy: RoutedOrderShapePolicyInput | None = None,
    ) -> RoutingTargetChoiceConversionResult: ...


class AlertService(Protocol):
    async def send_alert(self, event_type: str, message: str, severity: str) -> None: ...


class BacktestEngine(Protocol):
    async def run_strategy_window(self, sleeve_id: str, start_at: str, end_at: str) -> str: ...


class HealthService(Protocol):
    async def check_components(self) -> Sequence[HealthEvent]: ...

    async def readiness(self) -> bool: ...


class RuntimeContextService(Protocol):
    async def ensure_active_context(self) -> ActiveMandateContext: ...

    async def get_active_context(self) -> ActiveMandateContext: ...

    async def list_clients(self) -> Sequence[Client]: ...

    async def list_venue_accounts(self, client_key: str | None = None) -> Sequence[VenueAccount]: ...

    async def list_mandates(self, client_key: str | None = None) -> Sequence[StrategyMandate]: ...

    async def list_bindings(self, mandate_key: str | None = None) -> Sequence[MandateAccountBinding]: ...

    async def list_effective_component_configs(
        self,
        binding_key: str | None = None,
    ) -> Sequence[StrategyComponentConfig]: ...

    async def create_mandate(
        self,
        *,
        mandate_key: str,
        family: StrategyFamily,
        enabled: bool = True,
        notes: str | None = None,
    ) -> StrategyMandate: ...

    async def bind_account(
        self,
        *,
        mandate_key: str,
        venue_account_key: str,
        binding_key: str | None = None,
        enabled: bool = True,
        strategy_eligible: bool = True,
        routing_eligible: bool = True,
        trading_enabled: bool = True,
        target_recommendation_priority: int | None = None,
        clear_target_recommendation_priority: bool = False,
    ) -> MandateAccountBinding: ...


class VenueRegistryService(Protocol):
    async def list_supported_venues(self) -> Sequence[VenueIntegrationSummary]: ...

    async def get_adapter(self, venue: str) -> ExchangeAdapter: ...
