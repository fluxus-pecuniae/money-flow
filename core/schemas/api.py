"""API response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from core.config.settings import AppSettings
from core.domain.enums import (
    DecisionAction,
    Environment,
    ExecutionReadinessOutcome,
    InstrumentResolutionMode,
    MandateDesiredTradeStatus,
    MarketDataSourceMode,
    MarketType,
    OrderType,
    OrderIntentStatus,
    OrderSide,
    ProductType,
    RiskEvaluationOutcome,
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
    StrategyDecisionStatus,
    StrategyFamily,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderRecoveryCategory,
    Timeframe,
    TradeTargetScope,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    environment: Environment
    checks: dict[str, bool]


class ConfigSummaryResponse(BaseModel):
    app_name: str
    environment: Environment
    environment_notes: str
    exchange_name: str
    exchange_testnet: bool
    universe_include_standard_perp: bool
    universe_include_builder_deployed_in_catalog: bool
    universe_allow_builder_deployed_for_strategy: bool
    universe_allow_builder_deployed_for_trading: bool
    active_client_key: str
    active_mandate_key: str
    focused_account_key: str | None
    mandate_market_data_source_mode: MarketDataSourceMode
    mandate_market_data_source_venue: str
    mandate_market_data_source_market_type: MarketType | None
    mandate_market_data_source_product_type: ProductType | None
    mandate_instrument_resolution_mode: InstrumentResolutionMode
    risk_binding_reduce_fraction: float
    risk_reject_on_source_policy_runtime_mismatch: bool
    execution_live_submission_phase_enabled: bool
    execution_routed_submission_phase_enabled: bool
    execution_require_private_state_for_submission_readiness: bool
    components: list[str]

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "ConfigSummaryResponse":
        return cls(
            app_name=settings.app.name,
            environment=settings.app.environment,
            environment_notes=settings.profile.notes,
            exchange_name=settings.exchange.name,
            exchange_testnet=settings.exchange.use_testnet,
            universe_include_standard_perp=settings.universe_policy.include_standard_perp_universe,
            universe_include_builder_deployed_in_catalog=settings.universe_policy.include_builder_deployed_in_catalog,
            universe_allow_builder_deployed_for_strategy=settings.universe_policy.allow_builder_deployed_for_strategy,
            universe_allow_builder_deployed_for_trading=settings.universe_policy.allow_builder_deployed_for_trading,
            active_client_key=settings.runtime_selection.active_client_key,
            active_mandate_key=settings.runtime_selection.active_mandate_key,
            focused_account_key=settings.runtime_selection.focused_account_key,
            mandate_market_data_source_mode=settings.mandate_market_data_source_policy.source_mode,
            mandate_market_data_source_venue=settings.mandate_market_data_source_policy.source_venue,
            mandate_market_data_source_market_type=settings.mandate_market_data_source_policy.market_type,
            mandate_market_data_source_product_type=settings.mandate_market_data_source_policy.product_type,
            mandate_instrument_resolution_mode=(
                settings.mandate_market_data_source_policy.instrument_resolution_mode
            ),
            risk_binding_reduce_fraction=settings.risk.binding_reduce_fraction,
            risk_reject_on_source_policy_runtime_mismatch=(
                settings.risk.reject_on_source_policy_runtime_mismatch
            ),
            execution_live_submission_phase_enabled=(
                settings.execution.live_submission_phase_enabled
            ),
            execution_routed_submission_phase_enabled=(
                settings.execution.routed_submission_phase_enabled
            ),
            execution_require_private_state_for_submission_readiness=(
                settings.execution.require_private_state_for_submission_readiness
            ),
            components=[component.sleeve_id for component in settings.components],
        )


class ClientResponse(BaseModel):
    client_key: str
    client_ref_id: str | None
    display_name: str
    is_active: bool


class VenueAccountResponse(BaseModel):
    venue_account_key: str
    venue_account_ref_id: str | None
    client_key: str
    venue: str
    environment: Environment
    venue_native_account_id: str
    account_address: str | None
    account_label: str | None
    credentials_ref: str | None
    wallet_ref: str | None
    is_active: bool
    trading_enabled: bool


class StrategyMandateResponse(BaseModel):
    mandate_key: str
    mandate_ref_id: str | None
    client_key: str
    family: StrategyFamily
    enabled: bool
    allow_builder_deployed_for_strategy: bool
    allow_builder_deployed_for_trading: bool
    notes: str | None


class MandateAccountBindingResponse(BaseModel):
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
    target_recommendation_priority: int | None
    allow_builder_deployed_for_strategy: bool
    allow_builder_deployed_for_trading: bool
    notes: str | None


class StrategyComponentConfigResponse(BaseModel):
    component_config_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_account_binding_ref_id: str | None
    component_key: str
    component_type: str
    timeframe: Timeframe | None
    enabled: bool
    capital_allocation_pct: float
    max_open_risk_pct: float
    parameters: dict[str, object]
    metadata: dict[str, object]
    is_override: bool
    source_component_config_ref_id: str | None


class ActiveRuntimeContextResponse(BaseModel):
    active_client_key: str
    active_mandate_key: str
    family: StrategyFamily
    environment: Environment
    market_data_source_venue: str
    market_data_source_mode: MarketDataSourceMode
    market_data_source_market_type: MarketType | None
    market_data_source_product_type: ProductType | None
    mandate_instrument_resolution_mode: InstrumentResolutionMode
    bound_accounts: list[str]
    components: list[str]


class SleeveStatusResponse(BaseModel):
    sleeve_id: str
    timeframe: Timeframe
    enabled: bool
    capital_allocation_pct: float
    max_open_risk_pct: float
    trading_enabled: bool


class StrategyComponentStatusResponse(BaseModel):
    component_key: str
    timeframe: Timeframe
    enabled: bool
    capital_allocation_pct: float
    max_open_risk_pct: float
    trading_enabled: bool


class PortfolioSummaryResponse(BaseModel):
    environment: Environment
    account_equity: float
    total_gross_exposure: float
    total_net_exposure: float
    drawdown_pct: float
    kill_switch_engaged: bool


class PositionResponse(BaseModel):
    position_id: str
    sleeve_id: str | None
    symbol: str
    quantity: float
    avg_entry_price: float
    unrealized_pnl: float | None = None


class RiskEventResponse(BaseModel):
    risk_event_id: str
    severity: str
    message: str
    triggered_at: datetime


class ExchangeStatusResponse(BaseModel):
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
    submission_enabled: bool
    support_level: VenueSupportLevel
    adapter_supports_order_submission: bool
    adapter_supports_order_cancel: bool
    adapter_supports_order_amend: bool
    adapter_supports_user_streams: bool
    submission_authorized: bool
    live_submission_phase_enabled: bool
    last_success_at: datetime | None
    last_error: str | None = None
    private_lifecycle_update_mode: str = "polling"


class ExchangeCapabilitiesResponse(BaseModel):
    venue: str
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
    supported_order_types: list[str]
    supported_time_in_force: list[str]
    account_model: str
    notes: str | None = None
    private_lifecycle_update_mode: str = "polling"


class VenueIntegrationSummaryResponse(BaseModel):
    venue: str
    display_name: str
    enabled: bool
    read_only_mode: bool
    dry_run_mode: bool
    submission_enabled: bool
    execution_authorized: bool
    adapter_submission_implemented: bool
    live_submission_phase_enabled: bool
    support_level: VenueSupportLevel


class VenueAccountConnectivityResponse(BaseModel):
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
    submission_enabled: bool
    submission_authorized: bool
    private_account_sync_enabled: bool
    account_snapshot_available: bool
    open_orders_query_available: bool
    open_positions_query_available: bool
    last_success_at: datetime | None
    last_error: str | None = None


class ExchangeAccountSnapshotResponse(BaseModel):
    venue_account_ref_id: str | None
    venue: str
    environment: Environment
    account_address: str
    equity: float
    available_balance: float
    margin_used: float
    unrealized_pnl: float
    total_position_notional: float
    observed_at: datetime


class VenuePrivateStateSummaryResponse(BaseModel):
    venue: str
    support_level: VenueSupportLevel
    account_model: str
    account_identifier: str | None
    read_only_mode: bool
    dry_run_mode: bool
    private_account_sync_enabled: bool
    account_snapshot_available: bool
    balances_visible: bool
    open_orders_query_available: bool = Field(
        description="True when this summary call had an open-order view available through either a direct venue query or a persistence fallback."
    )
    open_orders_count: int
    open_orders_source: str = Field(
        description="Runtime source actually used for open-order visibility in this call: venue_query, persistence, or unavailable."
    )
    open_positions_query_available: bool
    open_positions_count: int
    open_positions_source: str = Field(
        description="Runtime source actually used for open-position visibility in this call: venue_query, persistence, or unavailable."
    )
    recent_fills_query_available: bool = Field(
        description="True when this summary call had a recent-fill view available through either a direct venue query or a persistence fallback."
    )
    recent_fills_count: int
    recent_fills_source: str = Field(
        description="Runtime source actually used for recent-fill visibility in this call: venue_query, persistence, or unavailable."
    )
    equity: float | None
    available_balance: float | None
    last_success_at: datetime | None
    last_error: str | None = None
    adapter_supports_user_streams: bool = False
    private_lifecycle_update_mode: str = Field(
        default="polling",
        description="Implemented private lifecycle update mode at head. Polling means no adapter-level user stream is driving lifecycle updates."
    )


class ExchangeSessionStateResponse(BaseModel):
    state_scope: str = Field(
        default="adapter_runtime",
        description="This surface reports adapter/runtime connection bookkeeping rather than deep venue-private account session truth."
    )
    venue: str
    environment: Environment
    connected: bool
    last_heartbeat_at: datetime | None
    session_sequence: int


class VenuePrivateOpenOrderResponse(BaseModel):
    venue: str
    venue_account_ref_id: str | None
    account_address: str | None
    exchange_order_id: str | None
    client_order_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str | None
    exchange_symbol: str | None
    status: str
    observed_at: datetime
    side: OrderSide | None
    order_type: str | None
    limit_price: float | None
    original_quantity: float | None
    remaining_quantity: float | None
    filled_quantity: float | None
    average_fill_price: float | None
    last_fill_at: datetime | None
    status_reason_code: str | None = None
    status_message: str | None = None
    reason_codes: list[str]
    cancelable_in_principle: bool
    amendable_in_principle: bool
    reduce_only: bool
    linked_submitted_order_id: str | None = Field(
        default=None,
        description="Optional correlation to a persisted platform SubmittedOrder when one can be matched."
    )
    linked_order_intent_id: str | None = Field(
        default=None,
        description="Optional correlation to the originating platform OrderIntent when one can be matched."
    )
    raw_payload: dict[str, object]


class VenuePrivateOpenOrdersViewResponse(BaseModel):
    venue: str
    venue_account_ref_id: str | None
    source: str = Field(
        description="Runtime source actually used for this open-order view: venue_query, stream, persistence, or unavailable."
    )
    items: list[VenuePrivateOpenOrderResponse]


class VenueOrderConstraintsResponse(BaseModel):
    venue: str
    support_level: VenueSupportLevel
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    exchange_symbol: str | None
    market_type: MarketType | None
    product_type: ProductType | None
    price_tick_size: float | None
    quantity_step_size: float | None
    min_order_size: float | None
    supports_order_preview: bool
    supports_reduce_only_orders: bool
    supports_client_order_ids: bool
    supported_order_types: list[str]
    supported_time_in_force: list[str]
    constraint_metadata_complete: bool
    notes: str | None = None


class PreparedVenueOrderResponse(BaseModel):
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
    quantity: float
    order_type: str
    limit_price: float | None
    reduce_only: bool
    time_in_force: str | None
    client_order_id: str | None
    preview_status: VenueOrderPreviewStatus
    reason_codes: list[str]
    payload: dict[str, object] | None
    routed_lineage: dict[str, object] | None = None
    constraints: VenueOrderConstraintsResponse | None
    venue_capabilities: ExchangeCapabilitiesResponse | None
    account_connectivity: VenueAccountConnectivityResponse | None
    prepared_at: datetime | None


class RoutedSubmittedOrderLineageResponse(BaseModel):
    routed_origin: bool
    intent_id: str | None
    desired_trade_key: str | None
    routing_assessment_id: str | None
    route_readiness_audit_id: str | None = None
    routing_target_recommendation_id: str | None = None
    routing_target_choice_id: str | None
    recommendation_policy_name: str | None = None
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
    allocation_created: bool | None = None
    scoring_created: bool | None
    route_executor_created: bool | None = None
    target_reselection: bool | None
    submitted_order_created: bool | None = None
    route_lineage_malformed: bool = False
    missing_lineage_fields: list[str] = Field(default_factory=list)
    malformed_lineage_fields: list[str] = Field(default_factory=list)


class RoutedSubmittedOrderLifecycleContextResponse(BaseModel):
    routed_origin: bool
    intent_id: str | None
    desired_trade_key: str | None
    routing_assessment_id: str | None
    route_readiness_audit_id: str | None = None
    routing_target_recommendation_id: str | None = None
    routing_target_choice_id: str | None
    recommendation_policy_name: str | None = None
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
    allocation_created: bool | None = None
    scoring_created: bool | None
    route_executor_created: bool | None = None
    target_reselection: bool | None
    submitted_order_created: bool | None = None
    same_target_only: bool = True
    same_account_only: bool = True
    same_venue_only: bool = True
    boundary_reason_codes: list[str] = Field(default_factory=list)
    route_lineage_malformed: bool = False
    missing_lineage_fields: list[str] = Field(default_factory=list)
    malformed_lineage_fields: list[str] = Field(default_factory=list)
    routed_order_shape_policy: dict[str, object] | None = None


class RoutedWorkflowInspectionResponse(BaseModel):
    desired_trade_key: str
    found: bool
    current_status_summary: dict[str, object]
    desired_trade: dict[str, object] | None = None
    routing_assessments: list[dict[str, object]] = Field(default_factory=list)
    route_readiness_audits: list[dict[str, object]] = Field(default_factory=list)
    routing_target_recommendations: list[dict[str, object]] = Field(default_factory=list)
    routing_target_choices: list[dict[str, object]] = Field(default_factory=list)
    child_intents: list[dict[str, object]] = Field(default_factory=list)
    readiness_evaluations: list[dict[str, object]] = Field(default_factory=list)
    submitted_orders: list[dict[str, object]] = Field(default_factory=list)
    lifecycle_events: list[dict[str, object]] = Field(default_factory=list)
    same_target_lifecycle_summary: dict[str, object] | None = None
    routed_lineage: dict[str, object] | None = None
    blocking_reason_codes: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    stale_data: list[str] = Field(default_factory=list)
    artifact_counts: dict[str, int] = Field(default_factory=dict)
    artifacts_created_by_inspection: bool = False


class RoutingAutomationPolicyRequest(BaseModel):
    mode: RoutingAutomationMode = Field(
        default=RoutingAutomationMode.DISABLED,
        description=(
            "Explicit automation mode. Disabled is the kill-switch default; dry-run-only "
            "plans but cannot automate; approval-required keeps operator approval first; "
            "explicit-automation-permitted only marks allowed same-target steps eligible."
        ),
    )
    policy_name: str = Field(default="phase_7_0_single_target_operator_controlled")
    allow_recommendation_acceptance: bool = Field(default=False)
    allow_target_choice_conversion: bool = Field(default=False)
    allow_preview_readiness: bool = Field(default=False)
    allow_submit: bool = Field(default=False)


class RoutingAutomationPolicyResponse(BaseModel):
    mode: RoutingAutomationMode
    policy_name: str
    dry_run_supported: bool
    operator_approval_required: bool
    recommendation_acceptance: RoutingAutomationStepStatus
    target_choice_conversion: RoutingAutomationStepStatus
    preview_readiness: RoutingAutomationStepStatus
    submit: RoutingAutomationStepStatus
    reason_codes: list[str]
    boundary_flags: dict[str, bool]
    provenance: dict[str, object]


class RoutingAutomationPlanRequest(BaseModel):
    dry_run: bool = Field(
        default=True,
        description="Phase 7.0 dry-run planning creates no routing or execution artifacts.",
    )
    policy: RoutingAutomationPolicyRequest | None = None


class RoutingAutomationPlanStepResponse(BaseModel):
    name: str
    status: RoutingAutomationStepStatus
    artifact_id: str | None = None
    would_create_artifact_type: str | None = None
    reason_codes: list[str]
    manual_only: bool
    approval_required: bool
    automatable: bool
    dry_run_only: bool
    blocked: bool
    lineage: dict[str, object]


class RoutingAutomationPlanResponse(BaseModel):
    automation_plan_id: str
    desired_trade_key: str
    environment: Environment
    generated_at: datetime
    dry_run: bool
    persisted: bool
    found: bool
    outcome: RoutingAutomationPlanOutcome
    policy: RoutingAutomationPolicyResponse
    current_status_summary: dict[str, object]
    steps: list[RoutingAutomationPlanStepResponse]
    reason_codes: list[str]
    blocking_reason_codes: list[str]
    manual_only_reason_codes: list[str]
    approval_required_reason_codes: list[str]
    automatable_action_names: list[str]
    manual_action_names: list[str]
    blocked_action_names: list[str]
    approval_gate_states: dict[str, object]
    routed_lineage: dict[str, object] | None = None
    same_target_lifecycle_summary: dict[str, object] | None = None
    boundary_flags: dict[str, bool]
    artifacts_created_by_plan: bool
    provenance: dict[str, object]


class RoutingAutomationApprovalCreateRequest(BaseModel):
    desired_trade_key: str
    action_name: RoutingAutomationApprovalAction
    approved_by: str
    notes: str | None = None
    expires_at: datetime | None = None
    policy: RoutingAutomationPolicyRequest | None = None


class RoutingAutomationApprovalStateChangeRequest(BaseModel):
    actor: str
    reason: str | None = None


class RoutingAutomationRecommendationAcceptanceRequest(BaseModel):
    routing_target_recommendation_id: str
    actor: str
    approval_note: str | None = None
    policy: RoutingAutomationPolicyRequest | None = None


class RoutingAutomationApprovalResponse(BaseModel):
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
    reason_codes: list[str]
    boundary_flags: dict[str, bool]
    policy_snapshot: dict[str, object]
    lineage: dict[str, object]
    provenance: dict[str, object]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoutingAutomationApprovalGateStateResponse(BaseModel):
    action_name: RoutingAutomationApprovalAction
    status: str
    approval_id: str | None = None
    artifact_id: str | None = None
    reason_codes: list[str]
    lineage: dict[str, object]


class RoutingAutomationApprovalInspectionResponse(BaseModel):
    desired_trade_key: str
    environment: Environment
    found: bool
    generated_at: datetime
    approvals: list[RoutingAutomationApprovalResponse]
    step_gate_states: dict[str, RoutingAutomationApprovalGateStateResponse]
    routed_lineage: dict[str, object] | None = None
    same_target_lifecycle_summary: dict[str, object] | None = None
    boundary_flags: dict[str, bool]
    artifacts_created_by_inspection: bool
    reason_codes: list[str]


class SubmittedOrderResponse(BaseModel):
    submitted_order_id: str
    instrument_key: str | None
    instrument_ref_id: str | None
    venue_account_ref_id: str | None
    venue: str
    account_address: str | None
    intent_id: str | None
    client_order_id: str | None
    exchange_order_id: str | None
    symbol: str | None
    side: OrderSide | None
    order_type: str | None
    limit_price: float | None
    original_quantity: float | None
    remaining_quantity: float | None
    reduce_only: bool
    status: str
    reconciliation_status: SubmittedOrderReconciliationStatus
    submitted_at: datetime
    acknowledged_at: datetime | None
    filled_quantity: float | None
    average_fill_price: float | None
    last_fill_at: datetime | None
    last_reconciled_at: datetime | None
    status_reason_code: str | None
    status_message: str | None
    reason_codes: list[str]
    cancelable_in_principle: bool
    amendable_in_principle: bool
    routed_origin: bool = False
    routed_lineage: RoutedSubmittedOrderLineageResponse | None = None
    routed_lifecycle_context: RoutedSubmittedOrderLifecycleContextResponse | None = None
    raw_payload: dict[str, object]


class SubmittedOrderLifecycleEventResponse(BaseModel):
    event_id: str
    submitted_order_id: str
    intent_id: str | None
    venue_account_ref_id: str | None
    venue: str
    status: str
    reconciliation_status: SubmittedOrderReconciliationStatus
    event_type: str
    reason_codes: list[str]
    message: str | None
    raw_payload: dict[str, object]
    observed_at: datetime | None
    routed_origin: bool = False
    routed_lifecycle_context: RoutedSubmittedOrderLifecycleContextResponse | None = None


class SubmittedOrderRecoveryRecommendationResponse(BaseModel):
    submitted_order_id: str
    intent_id: str | None
    venue_account_ref_id: str | None
    venue: str
    category: SubmittedOrderRecoveryCategory
    retryable: bool
    operator_action_required: bool
    venue_state_uncertain: bool
    account_policy_block: bool
    reason_codes: list[str]
    message: str | None
    recommended_action: str | None
    routed_origin: bool = False
    routed_lifecycle_context: RoutedSubmittedOrderLifecycleContextResponse | None = None


class SubmittedOrderActionabilityResponse(BaseModel):
    submitted_order_id: str
    venue_account_ref_id: str | None
    venue: str
    status: str
    reconciliation_status: SubmittedOrderReconciliationStatus
    cancel_supported: bool
    cancel_allowed_now: bool
    amend_supported: bool
    amend_allowed_now: bool
    cancel_reason_codes: list[str]
    amend_reason_codes: list[str]
    message: str | None
    routed_origin: bool = False
    routed_lifecycle_context: RoutedSubmittedOrderLifecycleContextResponse | None = None


class SubmittedOrderRecoveryExecutionRequest(BaseModel):
    action: str | None = None


class SubmittedOrderRecoveryExecutionResponse(BaseModel):
    submitted_order_id: str
    venue_account_ref_id: str | None
    venue: str
    action: str
    executed: bool
    blocked: bool
    reason_codes: list[str]
    message: str | None
    resulting_submitted_order_id: str | None
    resulting_order: SubmittedOrderResponse | None
    routed_origin: bool = False
    routed_lifecycle_context: RoutedSubmittedOrderLifecycleContextResponse | None = None


class SubmittedOrderAmendRequest(BaseModel):
    quantity: float | None = None
    limit_price: float | None = None


class FillResponse(BaseModel):
    fill_id: str
    instrument_key: str | None
    instrument_ref_id: str | None
    venue_account_ref_id: str | None
    venue: str
    account_address: str | None
    submitted_order_id: str
    exchange_order_id: str | None
    symbol: str
    price: float
    quantity: float
    fee: float
    filled_at: datetime


class VenuePrivateRecentFillsViewResponse(BaseModel):
    venue: str
    venue_account_ref_id: str | None
    source: str = Field(
        description="Runtime source actually used for this recent-fill view: venue_query, stream, persistence, or unavailable."
    )
    items: list[FillResponse]


class VenuePrivateOpenPositionsViewResponse(BaseModel):
    venue: str
    venue_account_ref_id: str | None
    source: str = Field(
        description="Runtime source actually used for this open-position view: venue_query, stream, persistence, or unavailable."
    )
    items: list[PositionResponse]


class ExecutionReadinessAssessmentResponse(BaseModel):
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
    reason_codes: list[str]
    message: str | None
    prepared_order: PreparedVenueOrderResponse | None
    routed_lineage: dict[str, object] | None = None
    evaluated_at: datetime | None
    provenance: dict[str, object]


class TopOfBookResponse(BaseModel):
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    bid_price: float | None
    bid_size: float | None
    ask_price: float | None
    ask_size: float | None
    observed_at: datetime


class InstrumentResponse(BaseModel):
    instrument_key: str
    instrument_ref_id: str | None
    canonical_symbol: str
    market_type: str
    product_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str | None
    is_active: bool


class ExchangeSymbolResponse(BaseModel):
    venue: str
    symbol: str
    exchange_symbol: str
    asset_id: int | None
    is_builder_deployed: bool
    is_strategy_eligible: bool
    is_trading_eligible: bool
    is_active: bool


class ExchangeSyncResponse(BaseModel):
    synced: int
    observed_at: datetime


class CreateMandateRequest(BaseModel):
    mandate_key: str
    family: StrategyFamily = StrategyFamily.MONEY_FLOW
    enabled: bool = True
    notes: str | None = None


class CreateBindingRequest(BaseModel):
    venue_account_key: str
    binding_key: str | None = None
    enabled: bool = True
    strategy_eligible: bool = True
    routing_eligible: bool = True
    trading_enabled: bool = True
    target_recommendation_priority: int | None = Field(
        default=None,
        ge=1,
        le=1_000_000,
        description=(
            "Optional operator-configured binding priority for the explicit_binding_priority "
            "recommendation policy. Lower positive integers win; this is not venue scoring."
        ),
    )
    clear_target_recommendation_priority: bool = Field(
        default=False,
        description=(
            "When true, intentionally clears the binding's target_recommendation_priority. "
            "Omitting target_recommendation_priority preserves the existing priority on updates."
        ),
    )

    @model_validator(mode="after")
    def _validate_priority_clear_request(self) -> "CreateBindingRequest":
        if self.clear_target_recommendation_priority and self.target_recommendation_priority is not None:
            raise ValueError(
                "clear_target_recommendation_priority cannot be true when "
                "target_recommendation_priority is provided"
            )
        return self


class CandleSyncRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    timeframes: list[Timeframe] = Field(default_factory=lambda: [Timeframe.M15, Timeframe.H1, Timeframe.H4])
    lookback_bars: int = 500


class CandleSyncResponse(BaseModel):
    synced_candles: int
    observed_at: datetime


class MarketDataHealthResponse(BaseModel):
    venue: str
    environment: Environment
    tracked_symbols: int
    tracked_timeframes: int
    stale_streams: int
    last_candle_at: datetime | None
    last_sync_at: datetime | None
    last_error: str | None = None


class MarketDataCheckpointResponse(BaseModel):
    venue: str
    environment: Environment
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


class IndicatorSyncRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    timeframes: list[Timeframe] = Field(default_factory=lambda: [Timeframe.M15, Timeframe.H1, Timeframe.H4])


class IndicatorSyncResponse(BaseModel):
    persisted_snapshots: int
    observed_at: datetime


class IndicatorSnapshotResponse(BaseModel):
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    timeframe: Timeframe
    as_of: datetime
    ema_5: float | None
    ema_10: float | None
    sma_20: float | None
    rsi_14: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None


class StrategyEvaluateRequest(BaseModel):
    component_keys: list[str] = Field(default_factory=list)
    sleeve_ids: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)


class VenueQuoteSnapshotResponse(BaseModel):
    instrument_key: str | None
    instrument_ref_id: str | None
    venue: str
    symbol: str
    exchange_symbol: str
    bid_price: float | None
    ask_price: float | None
    bid_size: float | None
    ask_size: float | None
    observed_at: datetime | None
    available: bool
    reason_unavailable: str | None = None


class BindingQuoteSnapshotResponse(BaseModel):
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
    quote_snapshot: VenueQuoteSnapshotResponse | None
    account_connectivity_status: str
    trading_eligible: bool
    routing_eligible: bool


class BindingRoutingCandidateResponse(BaseModel):
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
    available_balance_hint: float | None
    venue_capabilities: ExchangeCapabilitiesResponse
    account_connectivity: VenueAccountConnectivityResponse
    quote_snapshot: BindingQuoteSnapshotResponse | None
    eligibility_reasons: list[str]


class RoutingAssessmentFromDesiredTradeRequest(BaseModel):
    desired_trade_key: str = Field(
        ...,
        description="Existing routing_required mandate desired trade key to assess without execution.",
    )


class RoutingRequestResponse(BaseModel):
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


class RoutingCandidateAssessmentResponse(BaseModel):
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
    reason_codes: list[str]
    missing_data: list[str]
    fact_snapshot: dict[str, object]
    evaluated_at: datetime | None


class RoutingAssessmentResponse(BaseModel):
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
    request: RoutingRequestResponse
    candidates: list[RoutingCandidateAssessmentResponse]
    reason_codes: list[str]
    missing_data: list[str]
    evaluated_at: datetime | None
    provenance: dict[str, object]


class RouteReadinessAuditFromDesiredTradeRequest(BaseModel):
    desired_trade_key: str = Field(
        ...,
        description=(
            "Routing-required desired trade key to audit for future recommendation data sufficiency. "
            "This does not recommend, choose, convert, or submit."
        ),
    )


class RouteReadinessAuditFromAssessmentRequest(BaseModel):
    routing_assessment_id: str = Field(
        ...,
        description=(
            "Existing routing assessment id to audit for future recommendation data sufficiency. "
            "This does not recommend, choose, convert, or submit."
        ),
    )


class RouteReadinessCandidateAuditResponse(BaseModel):
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
    reason_codes: list[str]
    missing_data: list[str]
    stale_data: list[str]
    unsupported_data: list[str]
    unavailable_data: list[str]
    policy_blocks: list[str]
    blocking_reasons: list[str]
    fact_snapshot: dict[str, object]
    data_sources: dict[str, str]
    evaluated_at: datetime | None


class RouteReadinessAuditResponse(BaseModel):
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
    global_reason_codes: list[str]
    global_missing_data: list[str]
    global_stale_data: list[str]
    global_blocking_reasons: list[str]
    candidates: list[RouteReadinessCandidateAuditResponse]
    non_selecting: bool
    recommendation_created: bool
    target_choice_created: bool
    child_intent_created: bool
    submitted_order_created: bool
    provenance: dict[str, object]


class RoutingTargetRecommendationFromRouteReadinessAuditRequest(BaseModel):
    route_readiness_audit_id: str = Field(
        ...,
        description=(
            "Existing route-readiness audit id used to create a non-executing "
            "single_ready_candidate_only recommendation. This does not create a target choice, "
            "child intent, readiness evaluation, or submitted order."
        ),
    )
    policy_name: Literal["single_ready_candidate_only", "explicit_binding_priority"] | None = Field(
        default=None,
        description=(
            "Optional explicit recommendation policy. Omit to use single_ready_candidate_only. "
            "The only optional multi-candidate policy is explicit_binding_priority."
        ),
    )


class RoutingTargetRecommendationResponse(BaseModel):
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
    recommended_binding_ref_id: str | None
    recommended_binding_key: str | None
    recommended_venue_account_ref_id: str | None
    recommended_venue_account_key: str | None
    recommended_venue: str | None
    recommended_exchange_symbol: str | None
    candidate_count: int
    ready_candidate_count: int
    reason_codes: list[str]
    blocking_reasons: list[str]
    missing_data: list[str]
    stale_data: list[str]
    non_executing: bool
    target_choice_created: bool
    child_intent_created: bool
    submitted_order_created: bool
    created_at: datetime | None
    provenance: dict[str, object]


class RoutingTargetRecommendationAcceptRequest(BaseModel):
    approval_note: str | None = Field(
        default=None,
        description=(
            "Optional operator note for explicitly accepting a successful recommendation "
            "into a non-executing target choice."
        ),
    )
    requested_by: str | None = Field(
        default=None,
        description=(
            "Optional operator label for recommendation acceptance. This does not create "
            "child intents, readiness evaluations, submitted orders, or execution instructions."
        ),
    )


class RoutingTargetChoiceFromAssessmentRequest(BaseModel):
    routing_assessment_id: str = Field(
        ...,
        description="Existing routing assessment id used for a non-executing target-choice record.",
    )
    binding_ref_id: str | None = Field(
        default=None,
        description="Candidate binding row id requested for the explicit non-executing target-choice audit record.",
    )
    binding_key: str | None = Field(
        default=None,
        description="Candidate binding key requested for the explicit non-executing target-choice audit record.",
    )
    approval_note: str | None = Field(
        default=None,
        description=(
            "Optional operator note for the non-executing target-choice audit record; "
            "this is metadata, not approval-policy enforcement."
        ),
    )
    requested_by: str | None = Field(
        default=None,
        description="Optional operator or system label that requested the target-choice audit record.",
    )


class RoutingTargetChoiceResponse(BaseModel):
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
    reason_codes: list[str]
    missing_data: list[str]
    approval_note: str | None
    requested_by: str | None
    non_executing: bool
    created_at: datetime | None
    selected_at: datetime | None
    provenance: dict[str, object]


class RoutingAutomationRecommendationAcceptanceResponse(BaseModel):
    approval_id: str
    routing_target_recommendation_id: str
    target_choice_id: str
    desired_trade_key: str | None
    environment: Environment
    approval: RoutingAutomationApprovalResponse
    target_choice: RoutingTargetChoiceResponse
    approval_consumed: bool
    target_choice_created_or_reused: bool
    child_intent_created: bool
    prepared_order_created: bool
    readiness_assessment_created: bool
    submitted_order_created: bool
    reason_codes: list[str]
    boundary_flags: dict[str, bool]
    provenance: dict[str, object]


class RoutingTargetChoiceConversionResponse(BaseModel):
    target_choice_id: str
    environment: Environment
    status: RoutingTargetChoiceConversionStatus
    routing_assessment_id: str | None
    desired_trade_key: str | None
    routing_target_recommendation_id: str | None = None
    route_readiness_audit_id: str | None = None
    selected_binding_ref_id: str | None = None
    selected_binding_key: str | None = None
    selected_venue_account_ref_id: str | None = None
    selected_venue_account_key: str | None = None
    selected_venue: str | None = None
    selected_exchange_symbol: str | None = None
    intent_id: str | None
    reason_codes: list[str]
    missing_data: list[str]
    non_submitting: bool
    child_intent_created: bool = False
    child_intent_reused: bool = False
    prepared_order_created: bool
    readiness_assessment_created: bool
    submitted_order_created: bool
    converted_at: datetime | None
    provenance: dict[str, object]


class RoutedOrderShapePolicyRequest(BaseModel):
    order_type: OrderType | None = Field(
        default=None,
        description="Optional explicit routed conversion order type. Phase 5.8 supports MARKET or LIMIT only.",
    )
    limit_price: Decimal | None = Field(
        default=None,
        description=(
            "Explicit positive finite decimal limit price. Required for LIMIT and rejected for MARKET."
        ),
    )
    reduce_only: bool | None = Field(
        default=None,
        description="Must remain false for mandate-scoped OPEN routed conversion.",
    )
    policy_source: str | None = Field(
        default=None,
        description="Optional narrow policy source label; defaults to operator_requested when a policy body is supplied.",
    )
    requested_by: str | None = Field(
        default=None,
        description="Optional operator/system label for order-shape policy audit metadata.",
    )


class RoutingTargetChoiceConversionRequest(BaseModel):
    routed_order_shape_policy: RoutedOrderShapePolicyRequest | None = Field(
        default=None,
        description=(
            "Optional Phase 5.8 routed order-shape policy input for the explicit "
            "target-choice conversion. Omitted requests keep the current MARKET/no-limit/non-reduce-only default."
        ),
    )


class MandateDesiredTradeResponse(BaseModel):
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
    desired_quantity: float | None
    desired_notional: float | None
    source_decision_ids: list[str]
    source_evaluation_keys: list[str]
    source_binding_keys: list[str]
    status: MandateDesiredTradeStatus
    status_reason_code: str | None
    status_message: str | None
    provenance: dict[str, object]
    created_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None


class MandateMarketDataSourcePolicyResponse(BaseModel):
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
    notes: str | None
    metadata: dict[str, object]


class DesiredTradeConvertibilityResponse(BaseModel):
    decision_id: str
    convertible: bool
    decision_status: StrategyDecisionStatus
    action: DecisionAction
    target_scope: TradeTargetScope | None
    reason_code: str | None
    message: str
    instrument_key: str | None
    desired_trade_key_preview: str | None


class OrderIntentResponse(BaseModel):
    intent_id: str
    decision_id: str
    action: DecisionAction | None
    desired_trade_key: str | None
    mandate_desired_trade_ref_id: str | None
    client_ref_id: str | None
    strategy_mandate_ref_id: str | None
    mandate_account_binding_ref_id: str | None
    binding_key: str | None
    venue_account_ref_id: str | None
    instrument_key: str | None
    instrument_ref_id: str | None
    symbol: str
    side: OrderSide
    order_type: str
    quantity: float
    limit_price: float | None
    reduce_only: bool
    ttl_seconds: int
    status: OrderIntentStatus
    idempotency_key: str
    created_at: datetime
    provenance: dict[str, object]


class RiskEvaluationResponse(BaseModel):
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
    policy_checks: dict[str, object]
    provenance: dict[str, object]
    evaluated_at: datetime | None


class StrategySignalResponse(BaseModel):
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
    reason_code: str | None
    provenance: dict[str, object]
    features: dict[str, object]


class StrategyDecisionResponse(BaseModel):
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
    confidence: float | None
    rationale: str
    provenance: dict[str, object]
    features: dict[str, object]
    decided_at: datetime


class StrategyFamilyStatusResponse(BaseModel):
    family: StrategyFamily
    components: list[str]
    enabled_components: int
    latest_decision_at: datetime | None
    mandate_key: str | None = None


class StrategyEvaluateResponse(BaseModel):
    evaluated: int
    observed_at: datetime


class PortfolioBootstrapSummaryResponse(BaseModel):
    client_key: str | None
    mandate_key: str | None
    venue: str
    environment: Environment
    has_account_snapshot: bool
    bound_accounts: int
    open_positions: int
    recent_fills: int
    open_orders: int
    recent_submitted_orders: int
    unattributed_positions: int
    gross_exposure: float
    net_exposure: float
    account_equity: float | None = None
