"""Strongly typed domain models for the trading platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    ExecutionReadinessOutcome,
    HealthStatus,
    InstrumentResolutionMode,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    PositionStatus,
    ProductType,
    RiskEvaluationOutcome,
    RiskSeverity,
    RouteReadinessAuditStatus,
    RoutingAssessmentDecisionStatus,
    RoutingAutomationApprovalAction,
    RoutingAutomationApprovalStatus,
    RoutingAutomationMode,
    RoutingAutomationPlanOutcome,
    RoutingAutomationStepStatus,
    RoutingCandidateEligibilityStatus,
    RoutingTargetChoiceConversionStatus,
    RoutingTargetRecommendationStatus,
    RoutingTargetChoiceStatus,
    SignalType,
    StackingPolicy,
    StrategyDecisionStatus,
    StrategyFamily,
    StrategyValidationFillTiming,
    SubmittedOrderStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderRecoveryCategory,
    SystemComponent,
    Timeframe,
    TradeTargetScope,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)


@dataclass(slots=True)
class Instrument:
    instrument_key: str
    instrument_ref_id: str | None
    canonical_symbol: str
    market_type: MarketType
    product_type: ProductType
    base_asset: str
    quote_asset: str
    settlement_asset: str | None
    is_active: bool


@dataclass(slots=True)
class Client:
    client_key: str
    client_ref_id: str | None
    display_name: str
    is_active: bool


@dataclass(slots=True)
class VenueAccount:
    venue_account_key: str
    venue_account_ref_id: str | None
    client_key: str
    client_ref_id: str | None
    venue: str
    environment: Environment
    venue_native_account_id: str
    account_address: str | None
    account_label: str | None
    subaccount_label: str | None
    credentials_ref: str | None
    wallet_ref: str | None
    is_active: bool
    trading_enabled: bool


@dataclass(slots=True)
class StrategyMandate:
    mandate_key: str
    mandate_ref_id: str | None
    client_key: str
    client_ref_id: str | None
    family: StrategyFamily
    enabled: bool
    allow_builder_deployed_for_strategy: bool
    allow_builder_deployed_for_trading: bool
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MandateAccountBinding:
    binding_key: str
    binding_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str
    venue_account_key: str
    venue_account_ref_id: str | None
    enabled: bool
    strategy_eligible: bool
    routing_eligible: bool
    trading_enabled: bool
    allow_builder_deployed_for_strategy: bool
    allow_builder_deployed_for_trading: bool
    target_recommendation_priority: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyComponentConfig:
    component_config_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_account_binding_ref_id: str | None
    component_key: str
    component_type: str
    timeframe: Timeframe | None
    enabled: bool
    capital_allocation_pct: Decimal
    max_open_risk_pct: Decimal
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_override: bool = False
    source_component_config_ref_id: str | None = None


@dataclass(slots=True)
class MandateMarketDataSourcePolicy:
    policy_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str
    source_mode: MarketDataSourceMode
    source_venue: str
    market_type: MarketType | None
    product_type: ProductType | None
    instrument_resolution_mode: InstrumentResolutionMode
    runtime_exchange_venue: str
    runtime_exchange_matches_source: bool
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActiveMandateBindingContext:
    binding: MandateAccountBinding
    venue_account: VenueAccount
    component_configs: list[StrategyComponentConfig]


@dataclass(slots=True)
class ActiveMandateContext:
    client: Client
    mandate: StrategyMandate
    market_data_source_policy: MandateMarketDataSourcePolicy
    bindings: list[ActiveMandateBindingContext]


@dataclass(slots=True)
class SymbolMetadata:
    instrument_key: str
    instrument_ref_id: str | None
    venue: str
    symbol: str
    exchange_symbol: str
    venue_asset_id: str | None
    market_type: MarketType
    product_type: ProductType
    base_asset: str
    quote_asset: str
    settlement_asset: str | None
    price_tick_size: Decimal
    quantity_step_size: Decimal
    min_order_size: Decimal
    is_active: bool
    asset_id: int | None = None
    is_perpetual: bool = True
    is_builder_deployed: bool = False
    is_strategy_eligible: bool = True
    is_trading_eligible: bool = True
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Candle:
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    timeframe: Timeframe
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int | None = None


@dataclass(slots=True)
class IndicatorSnapshot:
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    timeframe: Timeframe
    as_of: datetime
    ema_5: Decimal | None = None
    ema_10: Decimal | None = None
    sma_20: Decimal | None = None
    rsi_14: Decimal | None = None
    macd: Decimal | None = None
    macd_signal: Decimal | None = None
    macd_histogram: Decimal | None = None


@dataclass(slots=True)
class SignalEvent:
    signal_id: str
    evaluation_key: str
    family: StrategyFamily
    sleeve_id: str
    component_key: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    timeframe: Timeframe
    signal_type: SignalType
    generated_at: datetime
    reason_code: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StrategySleeve:
    sleeve_id: str
    timeframe: Timeframe
    enabled: bool
    capital_allocation_pct: Decimal
    max_open_risk_pct: Decimal


@dataclass(slots=True)
class SleeveAllocation:
    sleeve_id: str
    environment: Environment
    target_allocation_pct: Decimal
    allocated_equity: Decimal
    open_risk_pct: Decimal
    effective_from: datetime


@dataclass(slots=True)
class Position:
    position_id: str
    instrument_key: str | None
    instrument_ref_id: str | None
    venue_account_ref_id: str | None
    sleeve_id: str | None
    venue: str
    account_address: str | None
    symbol: str
    environment: Environment
    side: OrderSide
    status: PositionStatus
    attribution_status: AttributionStatus
    venue_position_id: str | None
    quantity: Decimal
    avg_entry_price: Decimal
    mark_price: Decimal | None
    unrealized_pnl: Decimal | None
    opened_at: datetime
    closed_at: datetime | None = None


@dataclass(slots=True)
class OrderIntent:
    """Downstream binding/account-targeted child intent.

    This is intentionally not the mandate-level desired-trade object. Future
    routing and execution phases should create one or more order intents from a
    mandate-level desired trade once binding/account targeting is chosen, or
    earlier when the target binding/account is already naturally known for a
    binding-scoped action such as reduce/close.
    """

    intent_id: str
    sleeve_id: str
    component_key: str | None
    decision_id: str
    action: DecisionAction | None
    mandate_desired_trade_ref_id: str | None
    desired_trade_key: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    environment: Environment
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None
    reduce_only: bool
    ttl_seconds: int
    status: OrderIntentStatus
    idempotency_key: str
    created_at: datetime
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionReadinessAssessment:
    readiness_evaluation_id: str
    readiness_evaluation_key: str
    environment: Environment
    intent_ref_id: str | None
    intent_id: str
    mandate_desired_trade_ref_id: str | None
    desired_trade_key: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    venue: str
    support_level: VenueSupportLevel
    preview_status: VenueOrderPreviewStatus | None
    outcome: ExecutionReadinessOutcome
    eligible_for_submission_in_principle: bool
    live_submission_phase_enabled: bool
    venue_supports_order_submission: bool
    adapter_supports_order_submission: bool
    adapter_supports_order_cancel: bool
    adapter_supports_order_amend: bool
    submission_authorized: bool
    account_connected: bool
    private_state_required: bool
    private_state_ready: bool
    reason_codes: list[str] = field(default_factory=list)
    message: str | None = None
    prepared_order: PreparedVenueOrder | None = None
    evaluated_at: datetime | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SubmittedOrder:
    submitted_order_id: str
    instrument_key: str | None
    instrument_ref_id: str | None
    venue_account_ref_id: str | None
    venue: str
    account_address: str | None
    intent_id: str | None
    client_order_id: str | None
    exchange_order_id: str | None
    status: SubmittedOrderStatus
    submitted_at: datetime
    reconciliation_status: SubmittedOrderReconciliationStatus = SubmittedOrderReconciliationStatus.NOT_ATTEMPTED
    acknowledged_at: datetime | None = None
    symbol: str | None = None
    side: OrderSide | None = None
    order_type: OrderType | None = None
    limit_price: Decimal | None = None
    original_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    filled_quantity: Decimal | None = None
    average_fill_price: Decimal | None = None
    last_fill_at: datetime | None = None
    last_reconciled_at: datetime | None = None
    status_reason_code: str | None = None
    status_message: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    cancelable_in_principle: bool = False
    amendable_in_principle: bool = False
    reduce_only: bool = False
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VenuePrivateOpenOrder:
    venue: str
    venue_account_ref_id: str | None
    account_address: str | None
    exchange_order_id: str | None
    client_order_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str | None
    exchange_symbol: str | None
    status: SubmittedOrderStatus
    observed_at: datetime
    side: OrderSide | None = None
    order_type: OrderType | None = None
    limit_price: Decimal | None = None
    original_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    filled_quantity: Decimal | None = None
    average_fill_price: Decimal | None = None
    last_fill_at: datetime | None = None
    status_reason_code: str | None = None
    status_message: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    cancelable_in_principle: bool = False
    amendable_in_principle: bool = False
    reduce_only: bool = False
    linked_submitted_order_id: str | None = None
    linked_order_intent_id: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SubmittedOrderLifecycleEvent:
    event_id: str
    submitted_order_id: str
    intent_id: str | None
    venue_account_ref_id: str | None
    venue: str
    status: SubmittedOrderStatus
    reconciliation_status: SubmittedOrderReconciliationStatus
    event_type: str
    reason_codes: list[str] = field(default_factory=list)
    message: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    observed_at: datetime | None = None
    routed_origin: bool = False
    routed_lifecycle_context: SubmittedOrderRoutedLifecycleContext | None = None


@dataclass(slots=True)
class SubmittedOrderLifecycleUpdate:
    submitted_order_id: str
    venue: str
    venue_account_ref_id: str | None
    status: SubmittedOrderStatus
    reconciliation_status: SubmittedOrderReconciliationStatus
    event_type: str
    exchange_order_id: str | None = None
    limit_price: Decimal | None = None
    original_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    filled_quantity: Decimal | None = None
    average_fill_price: Decimal | None = None
    last_fill_at: datetime | None = None
    acknowledged_at: datetime | None = None
    status_reason_code: str | None = None
    status_message: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    cancelable_in_principle: bool | None = None
    amendable_in_principle: bool | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    observed_at: datetime | None = None


@dataclass(slots=True)
class SubmittedOrderRoutedLifecycleContext:
    routed_origin: bool
    intent_id: str | None
    desired_trade_key: str | None
    routing_assessment_id: str | None
    route_readiness_audit_id: str | None
    routing_target_recommendation_id: str | None
    routing_target_choice_id: str | None
    recommendation_policy_name: str | None
    selected_binding_ref_id: str | None
    selected_binding_key: str | None
    selected_venue_account_ref_id: str | None
    selected_venue_account_key: str | None
    selected_venue: str | None
    selected_exchange_symbol: str | None
    readiness_evaluation_id: str | None
    explicit_action_required: bool | None
    auto_submit: bool | None
    fanout_created: bool | None
    allocation_created: bool | None
    scoring_created: bool | None
    route_executor_created: bool | None
    target_reselection: bool | None
    submitted_order_created: bool | None
    same_target_only: bool = True
    same_account_only: bool = True
    same_venue_only: bool = True
    boundary_reason_codes: list[str] = field(default_factory=list)
    route_lineage_malformed: bool = False
    missing_lineage_fields: list[str] = field(default_factory=list)
    malformed_lineage_fields: list[str] = field(default_factory=list)
    routed_order_shape_policy: dict[str, Any] | None = None


@dataclass(slots=True)
class SubmittedOrderRecoveryRecommendation:
    submitted_order_id: str
    intent_id: str | None
    venue_account_ref_id: str | None
    venue: str
    category: SubmittedOrderRecoveryCategory
    retryable: bool
    operator_action_required: bool
    venue_state_uncertain: bool
    account_policy_block: bool
    reason_codes: list[str] = field(default_factory=list)
    message: str | None = None
    recommended_action: str | None = None
    routed_origin: bool = False
    routed_lifecycle_context: SubmittedOrderRoutedLifecycleContext | None = None


@dataclass(slots=True)
class SubmittedOrderRecoveryExecutionResult:
    submitted_order_id: str
    venue_account_ref_id: str | None
    venue: str
    action: str
    executed: bool
    blocked: bool
    reason_codes: list[str] = field(default_factory=list)
    message: str | None = None
    resulting_submitted_order_id: str | None = None
    resulting_order: SubmittedOrder | None = None
    routed_origin: bool = False
    routed_lifecycle_context: SubmittedOrderRoutedLifecycleContext | None = None


@dataclass(slots=True)
class SubmittedOrderActionability:
    submitted_order_id: str
    venue_account_ref_id: str | None
    venue: str
    status: SubmittedOrderStatus
    reconciliation_status: SubmittedOrderReconciliationStatus
    cancel_supported: bool
    cancel_allowed_now: bool
    amend_supported: bool
    amend_allowed_now: bool
    cancel_reason_codes: list[str] = field(default_factory=list)
    amend_reason_codes: list[str] = field(default_factory=list)
    message: str | None = None
    routed_origin: bool = False
    routed_lifecycle_context: SubmittedOrderRoutedLifecycleContext | None = None


@dataclass(slots=True)
class Fill:
    fill_id: str
    instrument_key: str | None
    instrument_ref_id: str | None
    venue_account_ref_id: str | None
    venue: str
    account_address: str | None
    submitted_order_id: str
    exchange_order_id: str | None
    symbol: str
    price: Decimal
    quantity: Decimal
    fee: Decimal
    filled_at: datetime


@dataclass(slots=True)
class SubmittedOrderPrivateFillEvidence:
    source: str
    evidence_scope: str
    fills: list[Fill] = field(default_factory=list)
    message: str | None = None


@dataclass(slots=True)
class PortfolioSnapshot:
    snapshot_id: str
    environment: Environment
    account_equity: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    drawdown_pct: Decimal
    captured_at: datetime


@dataclass(slots=True)
class RiskEvent:
    risk_event_id: str
    environment: Environment
    severity: RiskSeverity
    message: str
    sleeve_id: str | None
    symbol: str | None
    triggered_at: datetime


@dataclass(slots=True)
class RiskEvaluation:
    risk_evaluation_id: str
    risk_evaluation_key: str
    environment: Environment
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    market_data_source_policy_ref_id: str | None
    planning_source_venue: str | None
    decision_id: str
    decision_evaluation_key: str | None
    component_key: str | None
    target_scope: TradeTargetScope | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    action: DecisionAction
    decision_status: StrategyDecisionStatus
    outcome: RiskEvaluationOutcome
    reason_code: str | None
    message: str
    desired_trade_ref_id: str | None
    desired_trade_key: str | None
    desired_trade_status: MandateDesiredTradeStatus | None
    child_intent_ref_id: str | None
    child_intent_id: str | None
    child_intent_status: OrderIntentStatus | None
    policy_checks: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime | None = None


@dataclass(slots=True)
class HealthEvent:
    health_event_id: str
    component: SystemComponent
    status: HealthStatus
    message: str
    observed_at: datetime


@dataclass(slots=True)
class SystemConfig:
    environment: Environment
    trading_enabled: bool
    kill_switch_enabled: bool
    stacking_policy: StackingPolicy


@dataclass(slots=True)
class ExchangeSessionState:
    venue: str
    environment: Environment
    connected: bool
    last_heartbeat_at: datetime | None
    session_sequence: int
    state_scope: str = "adapter_runtime"


@dataclass(slots=True)
class StrategyDecision:
    """Strategy-layer proposal artifact before risk approval and routing."""

    decision_id: str
    evaluation_key: str
    family: StrategyFamily
    sleeve_id: str
    component_key: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    signal_id: str | None
    symbol: str
    action: DecisionAction
    status: StrategyDecisionStatus
    reason_code: str | None
    confidence: Decimal | None
    rationale: str
    decided_at: datetime
    provenance: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MandateDesiredTrade:
    """Mandate-level desired action after strategy and future risk approval.

    This object remains above account-targeted child intents. It may optionally
    point at a specific binding when the desired action is naturally tied to an
    existing position on one account.
    """

    desired_trade_key: str
    desired_trade_ref_id: str | None
    evaluated_state_fingerprint: str
    environment: Environment
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    family: StrategyFamily
    component_key: str | None
    market_data_source_policy_ref_id: str | None
    planning_source_venue: str
    planning_source_mode: MarketDataSourceMode
    planning_as_of: datetime | None
    target_scope: TradeTargetScope
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    action: DecisionAction
    side: OrderSide | None
    desired_quantity: Decimal | None
    desired_notional: Decimal | None
    source_decision_ids: list[str] = field(default_factory=list)
    source_evaluation_keys: list[str] = field(default_factory=list)
    source_binding_keys: list[str] = field(default_factory=list)
    status: MandateDesiredTradeStatus = MandateDesiredTradeStatus.DRAFT
    status_reason_code: str | None = None
    status_message: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None


@dataclass(slots=True)
class DesiredTradeConvertibilityAssessment:
    decision_id: str
    convertible: bool
    decision_status: StrategyDecisionStatus
    action: DecisionAction
    target_scope: TradeTargetScope | None
    reason_code: str | None
    message: str
    instrument_key: str | None
    desired_trade_key_preview: str | None = None


@dataclass(slots=True)
class VenueQuoteSnapshot:
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    exchange_symbol: str
    bid_price: Decimal | None
    ask_price: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    observed_at: datetime | None
    available: bool
    reason_unavailable: str | None = None


@dataclass(slots=True)
class BindingQuoteSnapshot:
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue_account_key: str | None
    venue: str
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    quote_snapshot: VenueQuoteSnapshot | None
    account_connectivity_status: str
    trading_eligible: bool
    routing_eligible: bool


@dataclass(slots=True)
class BindingRoutingCandidate:
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    market_data_source_policy_ref_id: str | None
    planning_source_venue: str
    binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue_account_key: str | None
    venue: str
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    strategy_eligible: bool
    trading_eligible: bool
    routing_eligible: bool
    account_connected: bool
    quote_available: bool
    available_balance_hint: Decimal | None
    venue_capabilities: VenueCapabilities
    account_connectivity: VenueAccountConnectivity
    quote_snapshot: BindingQuoteSnapshot | None
    eligibility_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RoutingRequest:
    routing_request_id: str
    environment: Environment
    desired_trade_ref_id: str | None
    desired_trade_key: str
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    market_data_source_policy_ref_id: str | None
    planning_source_venue: str
    planning_source_mode: MarketDataSourceMode
    target_scope: TradeTargetScope
    action: DecisionAction
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    component_key: str | None
    requested_at: datetime


@dataclass(slots=True)
class RoutingCandidateAssessment:
    assessment_id: str
    binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue_account_key: str | None
    venue: str
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    eligibility_status: RoutingCandidateEligibilityStatus
    reason_codes: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    fact_snapshot: dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime | None = None


@dataclass(slots=True)
class RoutingAssessment:
    assessment_id: str
    environment: Environment
    desired_trade_ref_id: str | None
    desired_trade_key: str
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    market_data_source_policy_ref_id: str | None
    planning_source_venue: str
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    action: DecisionAction
    target_scope: TradeTargetScope
    decision_status: RoutingAssessmentDecisionStatus
    eligible_binding_count: int
    ineligible_binding_count: int
    request: RoutingRequest
    candidates: list[RoutingCandidateAssessment] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    evaluated_at: datetime | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RouteReadinessCandidateAudit:
    route_readiness_audit_id: str
    binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue_account_key: str | None
    venue: str
    instrument_ref_id: str | None
    instrument_key: str | None
    symbol: str
    exchange_symbol: str | None
    status: RouteReadinessAuditStatus
    reason_codes: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    stale_data: list[str] = field(default_factory=list)
    unsupported_data: list[str] = field(default_factory=list)
    unavailable_data: list[str] = field(default_factory=list)
    policy_blocks: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    fact_snapshot: dict[str, Any] = field(default_factory=dict)
    data_sources: dict[str, str] = field(default_factory=dict)
    evaluated_at: datetime | None = None


@dataclass(slots=True)
class RouteReadinessAudit:
    route_readiness_audit_id: str
    environment: Environment
    desired_trade_ref_id: str | None
    desired_trade_key: str
    routing_assessment_ref_id: str | None
    routing_assessment_id: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    instrument_ref_id: str | None
    instrument_key: str | None
    symbol: str
    action: DecisionAction
    target_scope: TradeTargetScope
    evaluated_at: datetime
    overall_status: RouteReadinessAuditStatus
    candidate_count: int
    ready_candidate_count: int
    blocked_candidate_count: int
    insufficient_data_candidate_count: int
    global_reason_codes: list[str] = field(default_factory=list)
    global_missing_data: list[str] = field(default_factory=list)
    global_stale_data: list[str] = field(default_factory=list)
    global_blocking_reasons: list[str] = field(default_factory=list)
    candidates: list[RouteReadinessCandidateAudit] = field(default_factory=list)
    non_selecting: bool = True
    recommendation_created: bool = False
    target_choice_created: bool = False
    child_intent_created: bool = False
    submitted_order_created: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingTargetRecommendation:
    routing_target_recommendation_id: str
    environment: Environment
    route_readiness_audit_ref_id: str | None
    route_readiness_audit_id: str
    routing_assessment_ref_id: str | None
    routing_assessment_id: str | None
    desired_trade_ref_id: str | None
    desired_trade_key: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    instrument_ref_id: str | None
    instrument_key: str | None
    symbol: str | None
    action: DecisionAction | None
    target_scope: TradeTargetScope | None
    status: RoutingTargetRecommendationStatus
    policy_name: str
    recommended_binding_ref_id: str | None = None
    recommended_binding_key: str | None = None
    recommended_venue_account_ref_id: str | None = None
    recommended_venue_account_key: str | None = None
    recommended_venue: str | None = None
    recommended_exchange_symbol: str | None = None
    candidate_count: int = 0
    ready_candidate_count: int = 0
    reason_codes: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    stale_data: list[str] = field(default_factory=list)
    non_executing: bool = True
    target_choice_created: bool = False
    child_intent_created: bool = False
    submitted_order_created: bool = False
    created_at: datetime | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingTargetChoice:
    target_choice_id: str
    environment: Environment
    routing_assessment_ref_id: str | None
    routing_assessment_id: str
    desired_trade_ref_id: str | None
    desired_trade_key: str | None
    selected_binding_ref_id: str | None
    selected_binding_key: str | None
    selected_venue_account_ref_id: str | None
    selected_venue_account_key: str | None
    selected_venue: str | None
    status: RoutingTargetChoiceStatus
    reason_codes: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    approval_note: str | None = None
    requested_by: str | None = None
    non_executing: bool = True
    created_at: datetime | None = None
    selected_at: datetime | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingTargetChoiceConversionResult:
    target_choice_id: str
    environment: Environment
    status: RoutingTargetChoiceConversionStatus
    routing_assessment_id: str | None = None
    desired_trade_key: str | None = None
    routing_target_recommendation_id: str | None = None
    route_readiness_audit_id: str | None = None
    selected_binding_ref_id: str | None = None
    selected_binding_key: str | None = None
    selected_venue_account_ref_id: str | None = None
    selected_venue_account_key: str | None = None
    selected_venue: str | None = None
    selected_exchange_symbol: str | None = None
    intent_id: str | None = None
    child_intent: OrderIntent | None = None
    reason_codes: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    non_submitting: bool = True
    child_intent_created: bool = False
    child_intent_reused: bool = False
    prepared_order_created: bool = False
    readiness_assessment_created: bool = False
    submitted_order_created: bool = False
    converted_at: datetime | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationPolicy:
    mode: RoutingAutomationMode
    policy_name: str
    dry_run_supported: bool
    operator_approval_required: bool
    recommendation_acceptance: RoutingAutomationStepStatus
    target_choice_conversion: RoutingAutomationStepStatus
    preview_readiness: RoutingAutomationStepStatus
    submit: RoutingAutomationStepStatus
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationPlanStep:
    name: str
    status: RoutingAutomationStepStatus
    artifact_id: str | None = None
    would_create_artifact_type: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    manual_only: bool = False
    approval_required: bool = False
    automatable: bool = False
    dry_run_only: bool = False
    blocked: bool = False
    lineage: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationPlan:
    automation_plan_id: str
    desired_trade_key: str
    environment: Environment
    generated_at: datetime
    dry_run: bool
    persisted: bool
    found: bool
    outcome: RoutingAutomationPlanOutcome
    policy: RoutingAutomationPolicy
    current_status_summary: dict[str, Any]
    steps: list[RoutingAutomationPlanStep]
    reason_codes: list[str] = field(default_factory=list)
    blocking_reason_codes: list[str] = field(default_factory=list)
    manual_only_reason_codes: list[str] = field(default_factory=list)
    approval_required_reason_codes: list[str] = field(default_factory=list)
    automatable_action_names: list[str] = field(default_factory=list)
    manual_action_names: list[str] = field(default_factory=list)
    blocked_action_names: list[str] = field(default_factory=list)
    approval_gate_states: dict[str, Any] = field(default_factory=dict)
    routed_lineage: dict[str, Any] | None = None
    same_target_lifecycle_summary: dict[str, Any] | None = None
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    artifacts_created_by_plan: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationApproval:
    approval_id: str
    desired_trade_key: str
    environment: Environment
    action_name: RoutingAutomationApprovalAction
    status: RoutingAutomationApprovalStatus
    approved_by: str
    approved_at: datetime
    policy_name: str
    automation_mode: RoutingAutomationMode
    lineage_fingerprint: str | None = None
    approval_scope_key: str | None = None
    route_readiness_audit_id: str | None = None
    routing_assessment_id: str | None = None
    routing_target_recommendation_id: str | None = None
    routing_target_choice_id: str | None = None
    intent_id: str | None = None
    readiness_evaluation_id: str | None = None
    submitted_order_id: str | None = None
    selected_binding_ref_id: str | None = None
    selected_binding_key: str | None = None
    selected_venue_account_ref_id: str | None = None
    selected_venue_account_key: str | None = None
    selected_venue: str | None = None
    selected_exchange_symbol: str | None = None
    expires_at: datetime | None = None
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    consumed_by: str | None = None
    consumed_at: datetime | None = None
    notes: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    policy_snapshot: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class RoutingAutomationApprovalGateState:
    action_name: RoutingAutomationApprovalAction
    status: str
    approval_id: str | None = None
    artifact_id: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationApprovalInspection:
    desired_trade_key: str
    environment: Environment
    found: bool
    generated_at: datetime
    approvals: list[RoutingAutomationApproval]
    step_gate_states: dict[str, RoutingAutomationApprovalGateState]
    routed_lineage: dict[str, Any] | None = None
    same_target_lifecycle_summary: dict[str, Any] | None = None
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    artifacts_created_by_inspection: bool = False
    reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RoutingAutomationRecommendationAcceptanceResult:
    approval_id: str
    routing_target_recommendation_id: str
    target_choice_id: str
    desired_trade_key: str | None
    environment: Environment
    approval: RoutingAutomationApproval
    target_choice: RoutingTargetChoice
    approval_consumed: bool
    target_choice_created_or_reused: bool
    child_intent_created: bool = False
    prepared_order_created: bool = False
    readiness_assessment_created: bool = False
    submitted_order_created: bool = False
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationTargetChoiceConversionResult:
    approval_id: str
    target_choice_id: str
    intent_id: str | None
    desired_trade_key: str | None
    environment: Environment
    approval: RoutingAutomationApproval
    conversion: RoutingTargetChoiceConversionResult
    approval_consumed: bool
    child_intent_created_or_reused: bool
    prepared_order_created: bool = False
    readiness_assessment_created: bool = False
    submitted_order_created: bool = False
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationPreviewReadinessResult:
    approval_id: str
    intent_id: str
    desired_trade_key: str | None
    environment: Environment
    approval: RoutingAutomationApproval
    prepared_order_preview: PreparedVenueOrder
    readiness: ExecutionReadinessAssessment
    prepared_order_preview_key: str
    readiness_evaluation_id: str
    approval_consumed: bool
    prepared_order_preview_created_or_reused: bool
    readiness_assessment_created_or_reused: bool
    readiness_assessment_created: bool = False
    readiness_assessment_reused: bool = False
    submitted_order_created: bool = False
    exchange_submit_called: bool = False
    auto_submit: bool = False
    route_executor_used: bool = False
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutingAutomationSubmittedOrderHandoffResult:
    approval_id: str
    intent_id: str
    desired_trade_key: str | None
    environment: Environment
    approval: RoutingAutomationApproval
    submitted_order: SubmittedOrder
    submitted_order_id: str
    readiness_evaluation_id: str | None
    approval_consumed: bool
    submitted_order_created_or_reused: bool
    submitted_order_created: bool = False
    submitted_order_reused: bool = False
    exchange_submit_called: bool = True
    auto_submit: bool = False
    route_executor_used: bool = False
    reason_codes: list[str] = field(default_factory=list)
    boundary_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoutedOrderShapePolicyInput:
    order_type: OrderType | None = None
    limit_price: Decimal | None = None
    reduce_only: bool | None = None
    policy_source: str | None = None
    requested_by: str | None = None


@dataclass(slots=True)
class AuditLogEntry:
    audit_log_id: str
    environment: Environment
    actor: str
    action: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    created_at: datetime


@dataclass(slots=True)
class ExchangeAccountSnapshot:
    venue_account_ref_id: str | None
    venue: str
    environment: Environment
    account_address: str
    equity: Decimal
    available_balance: Decimal
    margin_used: Decimal
    unrealized_pnl: Decimal
    total_position_notional: Decimal
    observed_at: datetime


@dataclass(slots=True)
class ExchangeStatus:
    venue: str
    environment: Environment
    connected: bool
    api_base_url: str
    websocket_base_url: str
    can_sign_orders: bool
    wallet_address_configured: bool
    account_identifier_configured: bool
    credentials_configured: bool
    read_only_mode: bool
    dry_run_mode: bool
    support_level: VenueSupportLevel
    adapter_supports_order_submission: bool
    adapter_supports_order_cancel: bool
    adapter_supports_order_amend: bool
    adapter_supports_user_streams: bool
    submission_authorized: bool
    live_submission_phase_enabled: bool
    last_success_at: datetime | None
    last_error: str | None = None
    submission_enabled: bool = False
    private_lifecycle_update_mode: str = "polling"


@dataclass(slots=True)
class MarketDataHealth:
    venue: str
    environment: Environment
    tracked_symbols: int
    tracked_timeframes: int
    stale_streams: int
    last_candle_at: datetime | None
    last_sync_at: datetime | None
    last_error: str | None = None


@dataclass(slots=True)
class VenueCapabilities:
    venue: Venue
    support_level: VenueSupportLevel
    supports_spot: bool
    supports_perpetuals: bool
    supports_futures: bool
    supports_options: bool
    supports_hedge_mode: bool
    supports_websocket_market_data: bool
    supports_user_streams: bool
    supports_account_sync: bool
    supports_top_of_book: bool
    supports_depth_summary: bool
    supports_order_submission: bool
    supports_order_cancel: bool
    supports_order_amend: bool
    supports_recent_fills_query: bool
    adapter_supports_order_submission: bool
    adapter_supports_order_cancel: bool
    adapter_supports_order_amend: bool
    adapter_supports_user_streams: bool
    supports_order_preview: bool
    supports_account_snapshot: bool
    supports_open_orders_query: bool
    supports_open_positions_query: bool
    supports_reduce_only_orders: bool
    supports_client_order_ids: bool
    supports_demo_mode: bool
    supports_subaccounts: bool
    account_model: str
    supported_order_types: list[OrderType] = field(default_factory=list)
    supported_time_in_force: list[str] = field(default_factory=list)
    notes: str | None = None
    private_lifecycle_update_mode: str = "polling"


@dataclass(slots=True)
class VenueAccountConnectivity:
    venue: str
    environment: Environment
    support_level: VenueSupportLevel
    account_model: str
    account_identifier: str | None
    account_label: str | None
    subaccount_label: str | None
    credentials_ref: str | None
    account_identifier_configured: bool
    credentials_configured: bool
    read_only_mode: bool
    dry_run_mode: bool
    submission_authorized: bool
    private_account_sync_enabled: bool
    account_snapshot_available: bool
    open_orders_query_available: bool
    open_positions_query_available: bool
    last_success_at: datetime | None
    last_error: str | None = None
    submission_enabled: bool = False


@dataclass(slots=True)
class VenueIntegrationSummary:
    venue: str
    display_name: str
    enabled: bool
    read_only_mode: bool
    dry_run_mode: bool
    execution_authorized: bool
    adapter_submission_implemented: bool
    live_submission_phase_enabled: bool
    support_level: VenueSupportLevel
    submission_enabled: bool = False


@dataclass(slots=True)
class VenueOrderConstraints:
    venue: str
    support_level: VenueSupportLevel
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    market_type: MarketType | None
    product_type: ProductType | None
    price_tick_size: Decimal | None
    quantity_step_size: Decimal | None
    min_order_size: Decimal | None
    supports_order_preview: bool
    supports_reduce_only_orders: bool
    supports_client_order_ids: bool
    supported_order_types: list[OrderType] = field(default_factory=list)
    supported_time_in_force: list[str] = field(default_factory=list)
    constraint_metadata_complete: bool = False
    notes: str | None = None


@dataclass(slots=True)
class PreparedVenueOrder:
    intent_id: str
    desired_trade_key: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue: str
    support_level: VenueSupportLevel
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None
    reduce_only: bool
    time_in_force: str | None
    client_order_id: str | None
    preview_status: VenueOrderPreviewStatus
    reason_codes: list[str] = field(default_factory=list)
    payload: dict[str, Any] | None = None
    constraints: VenueOrderConstraints | None = None
    venue_capabilities: VenueCapabilities | None = None
    account_connectivity: VenueAccountConnectivity | None = None
    prepared_at: datetime | None = None


@dataclass(slots=True)
class VenuePrivateStateSummary:
    venue: str
    support_level: VenueSupportLevel
    account_model: str
    account_identifier: str | None
    read_only_mode: bool
    dry_run_mode: bool
    private_account_sync_enabled: bool
    account_snapshot_available: bool
    balances_visible: bool
    open_orders_query_available: bool
    open_orders_count: int
    open_orders_source: str
    open_positions_query_available: bool
    open_positions_count: int
    open_positions_source: str
    recent_fills_query_available: bool
    recent_fills_count: int
    recent_fills_source: str
    equity: Decimal | None
    available_balance: Decimal | None
    last_success_at: datetime | None
    last_error: str | None = None
    adapter_supports_user_streams: bool = False
    private_lifecycle_update_mode: str = "polling"


@dataclass(slots=True)
class TopOfBookSnapshot:
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    bid_price: Decimal | None
    bid_size: Decimal | None
    ask_price: Decimal | None
    ask_size: Decimal | None
    observed_at: datetime


@dataclass(slots=True)
class OrderBookDepthSummary:
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    best_bid_price: Decimal | None
    best_ask_price: Decimal | None
    spread_bps: Decimal | None
    bid_notional_top_n: Decimal | None
    ask_notional_top_n: Decimal | None
    levels_considered: int
    observed_at: datetime


@dataclass(slots=True)
class CandleSyncCheckpoint:
    venue: str
    environment: Environment
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    timeframe: Timeframe
    last_requested_start_time: datetime | None
    last_requested_end_time: datetime | None
    last_persisted_open_time: datetime | None
    last_persisted_close_time: datetime | None
    next_sync_start_time: datetime | None
    overlap_bars: int
    last_sync_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None = None


@dataclass(slots=True)
class PositionAttributionOverlay:
    overlay_id: str
    position_id: str
    venue_account_ref_id: str | None
    sleeve_id: str
    attributed_quantity: Decimal
    attributed_notional: Decimal | None
    as_of: datetime


@dataclass(slots=True)
class PortfolioBootstrapSummary:
    client_key: str | None
    mandate_key: str | None
    venue: str
    environment: Environment
    account_snapshot: ExchangeAccountSnapshot | None
    bound_accounts: int
    open_positions: int
    recent_fills: int
    open_orders: int
    recent_submitted_orders: int
    unattributed_positions: int
    gross_exposure: Decimal
    net_exposure: Decimal


@dataclass(slots=True)
class StrategyEvaluationInput:
    family: StrategyFamily
    sleeve_id: str
    component_key: str
    timeframe: Timeframe
    evaluation_key: str
    client_ref_id: str | None
    client_key: str | None
    strategy_mandate_ref_id: str | None
    mandate_key: str | None
    market_data_source_policy_ref_id: str | None
    market_data_source_venue: str
    market_data_source_mode: MarketDataSourceMode
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    venue_account_key: str | None
    account_address: str | None
    instrument_key: str
    instrument_ref_id: str
    venue: str
    symbol: str
    indicator_snapshot: IndicatorSnapshot | None
    latest_candle: Candle | None
    current_position: Position | None
    market_data_fresh: bool
    instrument_active: bool
    instrument_strategy_eligible: bool
    sleeve_enabled: bool
    history_bars: int
    latest_candle_close: datetime | None
    indicator_boundary_aligned: bool
    config_fingerprint: str
    position_state_fingerprint: str | None
    family_config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyEvaluationResult:
    signal_event: SignalEvent | None
    decision: StrategyDecision


@dataclass(slots=True)
class StrategyValidationAssumptions:
    initial_capital: Decimal
    fee_bps: Decimal
    slippage_bps: Decimal
    position_notional_pct: Decimal
    fill_timing: StrategyValidationFillTiming = (
        StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY
    )
    reduce_action_model: str = "full_exit"
    force_close_open_trade_at_end: bool = True
    drawdown_methodology: str = "closed_trade_and_mark_to_market"


@dataclass(slots=True)
class StrategyValidationRequest:
    strategy_family: StrategyFamily
    environment: Environment
    venue: str
    symbol: str
    start_at: datetime
    end_at: datetime
    assumptions: StrategyValidationAssumptions
    component_keys: tuple[str, ...] = ()
    instrument_key: str | None = None
    instrument_ref_id: str | None = None


@dataclass(slots=True)
class StrategyValidationTrade:
    trade_id: str
    strategy_family: StrategyFamily
    component_key: str
    timeframe: Timeframe
    symbol: str
    side: OrderSide
    entry_time: datetime
    exit_time: datetime
    raw_entry_price: Decimal
    raw_exit_price: Decimal
    entry_price: Decimal
    exit_price: Decimal
    size: Decimal
    entry_notional: Decimal
    exit_notional: Decimal
    fees: Decimal
    slippage_cost: Decimal
    gross_pnl: Decimal
    net_pnl: Decimal
    return_pct: Decimal
    max_adverse_excursion: Decimal | None
    max_favorable_excursion: Decimal | None
    entry_reason: str | None
    exit_reason: str | None
    entry_evaluation_key: str
    exit_evaluation_key: str
    duration_seconds: int
    entry_signal_time: datetime | None = None
    exit_signal_time: datetime | None = None
    fill_timing: StrategyValidationFillTiming = (
        StrategyValidationFillTiming.SAME_CANDLE_CLOSE_RESEARCH_ONLY
    )
    entry_fill_source: str = "signal_candle_close"
    exit_fill_source: str = "signal_candle_close"
    forced_exit: bool = False
    entry_market_regime: str = "unknown_or_insufficient_data"
    entry_volatility_regime: str = "unknown_or_insufficient_data"
    exit_market_regime: str = "unknown_or_insufficient_data"
    exit_volatility_regime: str = "unknown_or_insufficient_data"


@dataclass(slots=True)
class StrategyValidationDataCoverage:
    requested_start_at: datetime
    requested_end_at: datetime
    window_convention: str
    first_candle_available_at: datetime | None
    last_candle_available_at: datetime | None
    expected_candle_count: int | None
    actual_candle_count: int
    missing_candle_count: int | None
    coverage_percent: Decimal | None
    gap_count: int | None
    largest_gap_seconds: int | None
    warning_reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StrategyValidationRegimeSummary:
    regime_type: str
    regime_label: str
    candle_count: int
    evaluated_candle_count: int
    trade_count: int
    net_pnl: Decimal
    win_rate: Decimal | None
    mark_to_market_max_drawdown: Decimal | None
    no_trade_reason_counts: dict[str, int] = field(default_factory=dict)
    invalid_reason_counts: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyValidationMetrics:
    number_of_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal | None
    loss_rate: Decimal | None
    average_win: Decimal | None
    average_loss: Decimal | None
    profit_factor: Decimal | None
    gross_pnl: Decimal
    net_pnl: Decimal
    total_fees: Decimal
    total_slippage_cost: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal | None
    closed_trade_max_drawdown: Decimal
    closed_trade_max_drawdown_pct: Decimal | None
    mark_to_market_max_drawdown: Decimal | None
    mark_to_market_max_drawdown_pct: Decimal | None
    drawdown_methodology: str
    average_trade_duration_seconds: Decimal | None
    best_trade_id: str | None
    best_trade_net_pnl: Decimal | None
    worst_trade_id: str | None
    worst_trade_net_pnl: Decimal | None
    return_on_initial_capital: Decimal
    trades_by_component_timeframe: dict[str, int] = field(default_factory=dict)
    no_trade_reason_counts: dict[str, int] = field(default_factory=dict)
    invalid_reason_counts: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyValidationComponentReport:
    component_key: str
    timeframe: Timeframe
    candle_count: int
    evaluated_candles: int
    trades: list[StrategyValidationTrade]
    metrics: StrategyValidationMetrics
    data_coverage: StrategyValidationDataCoverage | None = None
    regime_methodology: dict[str, Any] = field(default_factory=dict)
    regime_summaries: list[StrategyValidationRegimeSummary] = field(default_factory=list)
    no_trade_reason_counts: dict[str, int] = field(default_factory=dict)
    invalid_reason_counts: dict[str, int] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StrategyValidationReport:
    report_id: str
    strategy_family: StrategyFamily
    environment: Environment
    venue: str
    symbol: str
    instrument_key: str | None
    instrument_ref_id: str | None
    start_at: datetime
    end_at: datetime
    assumptions: StrategyValidationAssumptions
    component_reports: list[StrategyValidationComponentReport]
    aggregate_metrics: StrategyValidationMetrics
    component_comparison: dict[str, Any] = field(default_factory=dict)
    data_coverage_summary: dict[str, Any] = field(default_factory=dict)
    regime_comparison: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    no_live_execution_artifacts_created: bool = True
    exchange_adapters_called: bool = False


@dataclass(slots=True)
class StrategyValidationBatchRequest:
    runs: tuple[StrategyValidationRequest, ...]
    batch_name: str | None = None


@dataclass(slots=True)
class StrategyValidationBatchRunReport:
    run_id: str
    run_index: int
    request: StrategyValidationRequest
    status: str
    report: StrategyValidationReport | None = None
    report_id: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass(slots=True)
class StrategyValidationBatchReport:
    batch_id: str
    batch_name: str | None
    strategy_family: StrategyFamily
    run_reports: list[StrategyValidationBatchRunReport]
    assumptions_matrix: dict[str, Any]
    comparison_summary: dict[str, Any]
    limitations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    no_live_execution_artifacts_created: bool = True
    exchange_adapters_called: bool = False


@dataclass(slots=True)
class StrategyFamilyStatus:
    family: StrategyFamily
    components: list[str]
    enabled_components: int
    latest_decision_at: datetime | None
    mandate_key: str | None = None
