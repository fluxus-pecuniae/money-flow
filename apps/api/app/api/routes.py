"""API routers for operational visibility and control."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from apps.api.app.dependencies import (
    get_app_settings,
    get_execution_service,
    get_exchange_adapter,
    get_hyperliquid_adapter,
    get_indicator_service,
    get_market_data_service,
    get_portfolio_service,
    get_risk_engine,
    get_routing_assessment_service,
    get_runtime_context_service,
    get_strategy_engine,
    get_trade_planning_service,
    get_venue_registry_service,
    require_admin,
    require_automation_admin,
    require_operator,
    require_read_only_operator,
)
from core.config.settings import AppSettings
from core.domain.enums import ExecutionReadinessOutcome, MandateDesiredTradeStatus, RiskEvaluationOutcome, Timeframe
from core.domain.models import (
    BindingQuoteSnapshot,
    BindingRoutingCandidate,
    DesiredTradeConvertibilityAssessment,
    ExchangeAccountSnapshot,
    ExchangeSessionState,
    ExecutionReadinessAssessment,
    MandateMarketDataSourcePolicy,
    MandateDesiredTrade,
    MarketDataHealth,
    OrderIntent,
    PreparedVenueOrder,
    RouteReadinessAudit,
    RiskEvaluation,
    RoutingAssessment,
    RoutingAutomationPolicy,
    RoutingCandidateAssessment,
    RoutingRequest,
    RoutingTargetRecommendation,
    RoutingTargetChoice,
    RoutingTargetChoiceConversionResult,
    RoutedOrderShapePolicyInput,
    Fill,
    SubmittedOrder,
    SubmittedOrderActionability,
    SubmittedOrderLifecycleEvent,
    SubmittedOrderRecoveryExecutionResult,
    SubmittedOrderRecoveryRecommendation,
    SubmittedOrderRoutedLifecycleContext,
    TopOfBookSnapshot,
    VenueOrderConstraints,
    VenuePrivateOpenOrder,
    VenuePrivateStateSummary,
    VenueQuoteSnapshot,
)
from core.domain.routed_lifecycle import (
    submitted_order_routed_lifecycle_context_from_raw_payload,
)
from core.domain.hyperliquid import UniversePolicy
from core.schemas.api import (
    ActiveRuntimeContextResponse,
    CandleSyncRequest,
    CandleSyncResponse,
    ClientResponse,
    ConfigSummaryResponse,
    CreateBindingRequest,
    CreateMandateRequest,
    BindingQuoteSnapshotResponse,
    BindingRoutingCandidateResponse,
    DesiredTradeConvertibilityResponse,
    ExchangeCapabilitiesResponse,
    ExchangeAccountSnapshotResponse,
    ExchangeSessionStateResponse,
    ExchangeStatusResponse,
    FillResponse,
    ExecutionReadinessAssessmentResponse,
    ExchangeSymbolResponse,
    ExchangeSyncResponse,
    HealthResponse,
    InstrumentResponse,
    IndicatorSnapshotResponse,
    IndicatorSyncRequest,
    IndicatorSyncResponse,
    MarketDataCheckpointResponse,
    MarketDataHealthResponse,
    MandateMarketDataSourcePolicyResponse,
    MandateDesiredTradeResponse,
    MandateAccountBindingResponse,
    OrderIntentResponse,
    PreparedVenueOrderResponse,
    PortfolioSummaryResponse,
    PortfolioBootstrapSummaryResponse,
    PositionResponse,
    ReadinessResponse,
    RiskEvaluationResponse,
    RiskEventResponse,
    RouteReadinessAuditFromAssessmentRequest,
    RouteReadinessAuditFromDesiredTradeRequest,
    RouteReadinessAuditResponse,
    RouteReadinessCandidateAuditResponse,
    RoutingTargetRecommendationAcceptRequest,
    RoutingTargetRecommendationFromRouteReadinessAuditRequest,
    RoutingTargetRecommendationResponse,
    RoutingAssessmentFromDesiredTradeRequest,
    RoutingAssessmentResponse,
    RoutingAutomationApprovalCreateRequest,
    RoutingAutomationApprovalInspectionResponse,
    RoutingAutomationRecommendationAcceptanceRequest,
    RoutingAutomationRecommendationAcceptanceResponse,
    RoutingAutomationPreviewReadinessRequest,
    RoutingAutomationPreviewReadinessResponse,
    RoutingAutomationSubmittedOrderHandoffRequest,
    RoutingAutomationSubmittedOrderHandoffResponse,
    RoutingAutomationTargetChoiceConversionRequest,
    RoutingAutomationTargetChoiceConversionResponse,
    RoutingAutomationApprovalResponse,
    RoutingAutomationApprovalStateChangeRequest,
    RoutingAutomationPlanRequest,
    RoutingAutomationPlanResponse,
    RoutingAutomationPolicyRequest,
    RoutingAutomationPolicyResponse,
    RoutingCandidateAssessmentResponse,
    RoutingRequestResponse,
    RoutingTargetChoiceFromAssessmentRequest,
    RoutingTargetChoiceConversionRequest,
    RoutingTargetChoiceConversionResponse,
    RoutingTargetChoiceResponse,
    RoutedWorkflowInspectionResponse,
    RoutedWorkflowOperatorSummaryResponse,
    RoutedSubmittedOrderLifecycleContextResponse,
    RoutedSubmittedOrderLineageResponse,
    SubmittedOrderResponse,
    SubmittedOrderLifecycleEventResponse,
    SubmittedOrderActionabilityResponse,
    SubmittedOrderAmendRequest,
    SubmittedOrderRecoveryExecutionRequest,
    SubmittedOrderRecoveryExecutionResponse,
    SubmittedOrderRecoveryRecommendationResponse,
    StrategyComponentConfigResponse,
    StrategyComponentStatusResponse,
    SleeveStatusResponse,
    StrategyDecisionResponse,
    StrategyEvaluateRequest,
    StrategyEvaluateResponse,
    StrategyFamilyStatusResponse,
    StrategyMandateResponse,
    StrategySignalResponse,
    TopOfBookResponse,
    VenueAccountResponse,
    VenueAccountConnectivityResponse,
    VenueIntegrationSummaryResponse,
    VenueOrderConstraintsResponse,
    VenuePrivateOpenOrderResponse,
    VenuePrivateOpenOrdersViewResponse,
    VenuePrivateOpenPositionsViewResponse,
    VenuePrivateRecentFillsViewResponse,
    VenuePrivateStateSummaryResponse,
    VenueQuoteSnapshotResponse,
)
from db.models import MarketDataHealthModel, SymbolModel
from db.session import SessionLocal
from core.interfaces.hyperliquid import HyperliquidAdapterContract
from core.interfaces.services import (
    ExchangeAdapter,
    ExecutionService,
    IndicatorService,
    MandateTradePlanningService,
    MarketDataService,
    PortfolioService,
    RiskEngine,
    RoutingAssessmentService,
    RuntimeContextService,
    StrategyEngine,
    VenueRegistryService,
)
from sqlalchemy import select
from services.planning.service import DesiredTradeConversionError
from services.routing.service import RoutingAssessmentError
from services.execution.service import SubmissionBlockedError, SubmissionFailedError, SubmittedOrderActionError

router = APIRouter()
v1 = APIRouter(prefix="/api/v1", dependencies=[Depends(require_read_only_operator)])


def _instrument_response(item) -> InstrumentResponse:
    return InstrumentResponse(
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        canonical_symbol=item.canonical_symbol,
        market_type=item.market_type.value,
        product_type=item.product_type.value,
        base_asset=item.base_asset,
        quote_asset=item.quote_asset,
        settlement_asset=item.settlement_asset,
        is_active=item.is_active,
    )


def _symbol_response(model: SymbolModel) -> ExchangeSymbolResponse:
    return ExchangeSymbolResponse(
        venue=model.venue,
        symbol=model.symbol,
        exchange_symbol=model.exchange_symbol,
        asset_id=model.asset_id,
        is_builder_deployed=model.is_builder_deployed,
        is_strategy_eligible=model.is_strategy_eligible,
        is_trading_eligible=model.is_trading_eligible,
        is_active=model.is_active,
    )


def _top_of_book_response(snapshot: TopOfBookSnapshot) -> TopOfBookResponse:
    return TopOfBookResponse(
        instrument_key=snapshot.instrument_key,
        instrument_ref_id=snapshot.instrument_ref_id,
        venue=snapshot.venue,
        symbol=snapshot.symbol,
        bid_price=float(snapshot.bid_price) if snapshot.bid_price is not None else None,
        bid_size=float(snapshot.bid_size) if snapshot.bid_size is not None else None,
        ask_price=float(snapshot.ask_price) if snapshot.ask_price is not None else None,
        ask_size=float(snapshot.ask_size) if snapshot.ask_size is not None else None,
        observed_at=snapshot.observed_at,
    )


def _exchange_account_snapshot_response(snapshot: ExchangeAccountSnapshot) -> ExchangeAccountSnapshotResponse:
    return ExchangeAccountSnapshotResponse(
        venue_account_ref_id=snapshot.venue_account_ref_id,
        venue=snapshot.venue,
        environment=snapshot.environment,
        account_address=snapshot.account_address,
        equity=float(snapshot.equity),
        available_balance=float(snapshot.available_balance),
        margin_used=float(snapshot.margin_used),
        unrealized_pnl=float(snapshot.unrealized_pnl),
        total_position_notional=float(snapshot.total_position_notional),
        observed_at=snapshot.observed_at,
    )


def _exchange_session_state_response(state: ExchangeSessionState) -> ExchangeSessionStateResponse:
    return ExchangeSessionStateResponse(
        state_scope=state.state_scope,
        venue=state.venue,
        environment=state.environment,
        connected=state.connected,
        last_heartbeat_at=state.last_heartbeat_at,
        session_sequence=state.session_sequence,
    )


def _component_status_response(
    component,
    *,
    trading_enabled: bool,
) -> StrategyComponentStatusResponse:
    return StrategyComponentStatusResponse(
        component_key=component.component_key,
        timeframe=component.timeframe or Timeframe.M15,
        enabled=component.enabled,
        capital_allocation_pct=float(component.capital_allocation_pct),
        max_open_risk_pct=float(component.max_open_risk_pct),
        trading_enabled=trading_enabled,
    )


def _venue_quote_response(snapshot: VenueQuoteSnapshot) -> VenueQuoteSnapshotResponse:
    return VenueQuoteSnapshotResponse(
        instrument_key=snapshot.instrument_key,
        instrument_ref_id=snapshot.instrument_ref_id,
        venue=snapshot.venue,
        symbol=snapshot.symbol,
        exchange_symbol=snapshot.exchange_symbol,
        bid_price=float(snapshot.bid_price) if snapshot.bid_price is not None else None,
        ask_price=float(snapshot.ask_price) if snapshot.ask_price is not None else None,
        bid_size=float(snapshot.bid_size) if snapshot.bid_size is not None else None,
        ask_size=float(snapshot.ask_size) if snapshot.ask_size is not None else None,
        observed_at=snapshot.observed_at,
        available=snapshot.available,
        reason_unavailable=snapshot.reason_unavailable,
    )


def _binding_quote_response(snapshot: BindingQuoteSnapshot) -> BindingQuoteSnapshotResponse:
    return BindingQuoteSnapshotResponse(
        client_ref_id=snapshot.client_ref_id,
        strategy_mandate_ref_id=snapshot.strategy_mandate_ref_id,
        mandate_key=snapshot.mandate_key,
        binding_ref_id=snapshot.binding_ref_id,
        binding_key=snapshot.binding_key,
        venue_account_ref_id=snapshot.venue_account_ref_id,
        venue_account_key=snapshot.venue_account_key,
        venue=snapshot.venue,
        instrument_key=snapshot.instrument_key,
        instrument_ref_id=snapshot.instrument_ref_id,
        symbol=snapshot.symbol,
        exchange_symbol=snapshot.exchange_symbol,
        quote_snapshot=(
            _venue_quote_response(snapshot.quote_snapshot) if snapshot.quote_snapshot is not None else None
        ),
        account_connectivity_status=snapshot.account_connectivity_status,
        trading_eligible=snapshot.trading_eligible,
        routing_eligible=snapshot.routing_eligible,
    )


def _exchange_capabilities_response(item) -> ExchangeCapabilitiesResponse:
    return ExchangeCapabilitiesResponse(
        venue=item.venue.value if hasattr(item.venue, "value") else item.venue,
        support_level=item.support_level,
        supports_spot=item.supports_spot,
        supports_perpetuals=item.supports_perpetuals,
        supports_futures=item.supports_futures,
        supports_options=item.supports_options,
        supports_hedge_mode=item.supports_hedge_mode,
        supports_websocket_market_data=item.supports_websocket_market_data,
        supports_user_streams=item.supports_user_streams,
        supports_account_sync=item.supports_account_sync,
        supports_top_of_book=item.supports_top_of_book,
        supports_depth_summary=item.supports_depth_summary,
        supports_order_submission=item.supports_order_submission,
        supports_order_cancel=item.supports_order_cancel,
        supports_order_amend=item.supports_order_amend,
        supports_recent_fills_query=item.supports_recent_fills_query,
        adapter_supports_order_submission=item.adapter_supports_order_submission,
        adapter_supports_order_cancel=item.adapter_supports_order_cancel,
        adapter_supports_order_amend=item.adapter_supports_order_amend,
        adapter_supports_user_streams=item.adapter_supports_user_streams,
        supports_order_preview=item.supports_order_preview,
        supports_account_snapshot=item.supports_account_snapshot,
        supports_open_orders_query=item.supports_open_orders_query,
        supports_open_positions_query=item.supports_open_positions_query,
        supports_reduce_only_orders=item.supports_reduce_only_orders,
        supports_client_order_ids=item.supports_client_order_ids,
        supports_demo_mode=item.supports_demo_mode,
        supports_subaccounts=item.supports_subaccounts,
        supported_order_types=[
            order_type.value if hasattr(order_type, "value") else str(order_type)
            for order_type in item.supported_order_types
        ],
        supported_time_in_force=list(item.supported_time_in_force),
        account_model=item.account_model,
        notes=item.notes,
        private_lifecycle_update_mode=item.private_lifecycle_update_mode,
    )


def _venue_account_connectivity_response(item) -> VenueAccountConnectivityResponse:
    return VenueAccountConnectivityResponse(
        venue=item.venue,
        environment=item.environment,
        support_level=item.support_level,
        account_model=item.account_model,
        account_identifier=item.account_identifier,
        account_label=item.account_label,
        subaccount_label=item.subaccount_label,
        credentials_ref=item.credentials_ref,
        account_identifier_configured=item.account_identifier_configured,
        credentials_configured=item.credentials_configured,
        read_only_mode=item.read_only_mode,
        dry_run_mode=item.dry_run_mode,
        submission_enabled=item.submission_enabled,
        submission_authorized=item.submission_authorized,
        private_account_sync_enabled=item.private_account_sync_enabled,
        account_snapshot_available=item.account_snapshot_available,
        open_orders_query_available=item.open_orders_query_available,
        open_positions_query_available=item.open_positions_query_available,
        last_success_at=item.last_success_at,
        last_error=item.last_error,
    )


def _venue_private_state_summary_response(item: VenuePrivateStateSummary) -> VenuePrivateStateSummaryResponse:
    return VenuePrivateStateSummaryResponse(
        venue=item.venue,
        support_level=item.support_level,
        account_model=item.account_model,
        account_identifier=item.account_identifier,
        read_only_mode=item.read_only_mode,
        dry_run_mode=item.dry_run_mode,
        private_account_sync_enabled=item.private_account_sync_enabled,
        account_snapshot_available=item.account_snapshot_available,
        balances_visible=item.balances_visible,
        open_orders_query_available=item.open_orders_query_available,
        open_orders_count=item.open_orders_count,
        open_orders_source=item.open_orders_source,
        open_positions_query_available=item.open_positions_query_available,
        open_positions_count=item.open_positions_count,
        open_positions_source=item.open_positions_source,
        recent_fills_query_available=item.recent_fills_query_available,
        recent_fills_count=item.recent_fills_count,
        recent_fills_source=item.recent_fills_source,
        equity=float(item.equity) if item.equity is not None else None,
        available_balance=float(item.available_balance) if item.available_balance is not None else None,
        last_success_at=item.last_success_at,
        last_error=item.last_error,
        adapter_supports_user_streams=item.adapter_supports_user_streams,
        private_lifecycle_update_mode=item.private_lifecycle_update_mode,
    )


def _venue_private_open_order_response(item: VenuePrivateOpenOrder) -> VenuePrivateOpenOrderResponse:
    return VenuePrivateOpenOrderResponse(
        venue=item.venue,
        venue_account_ref_id=item.venue_account_ref_id,
        account_address=item.account_address,
        exchange_order_id=item.exchange_order_id,
        client_order_id=item.client_order_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        status=item.status.value if hasattr(item.status, "value") else str(item.status),
        observed_at=item.observed_at,
        side=item.side,
        order_type=item.order_type.value if hasattr(item.order_type, "value") else item.order_type,
        limit_price=float(item.limit_price) if item.limit_price is not None else None,
        original_quantity=float(item.original_quantity) if item.original_quantity is not None else None,
        remaining_quantity=float(item.remaining_quantity) if item.remaining_quantity is not None else None,
        filled_quantity=float(item.filled_quantity) if item.filled_quantity is not None else None,
        average_fill_price=float(item.average_fill_price) if item.average_fill_price is not None else None,
        last_fill_at=item.last_fill_at,
        status_reason_code=item.status_reason_code,
        status_message=item.status_message,
        reason_codes=list(item.reason_codes),
        cancelable_in_principle=item.cancelable_in_principle,
        amendable_in_principle=item.amendable_in_principle,
        reduce_only=item.reduce_only,
        linked_submitted_order_id=item.linked_submitted_order_id,
        linked_order_intent_id=item.linked_order_intent_id,
        raw_payload=dict(item.raw_payload),
    )


def _venue_private_open_orders_view_response(
    *,
    venue: str,
    venue_account_ref_id: str | None,
    source: str,
    items: list[VenuePrivateOpenOrder],
) -> VenuePrivateOpenOrdersViewResponse:
    return VenuePrivateOpenOrdersViewResponse(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=[_venue_private_open_order_response(item) for item in items],
    )


def _venue_private_recent_fills_view_response(
    *,
    venue: str,
    venue_account_ref_id: str | None,
    source: str,
    items: list[Fill],
) -> VenuePrivateRecentFillsViewResponse:
    return VenuePrivateRecentFillsViewResponse(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=[_fill_response(item) for item in items],
    )


def _venue_private_open_positions_view_response(
    *,
    venue: str,
    venue_account_ref_id: str | None,
    source: str,
    items: list,
) -> VenuePrivateOpenPositionsViewResponse:
    return VenuePrivateOpenPositionsViewResponse(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=[_position_response(item) for item in items],
    )


def _venue_order_constraints_response(item: VenueOrderConstraints) -> VenueOrderConstraintsResponse:
    return VenueOrderConstraintsResponse(
        venue=item.venue,
        support_level=item.support_level,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        market_type=item.market_type,
        product_type=item.product_type,
        price_tick_size=float(item.price_tick_size) if item.price_tick_size is not None else None,
        quantity_step_size=float(item.quantity_step_size) if item.quantity_step_size is not None else None,
        min_order_size=float(item.min_order_size) if item.min_order_size is not None else None,
        supports_order_preview=item.supports_order_preview,
        supports_reduce_only_orders=item.supports_reduce_only_orders,
        supports_client_order_ids=item.supports_client_order_ids,
        supported_order_types=[
            order_type.value if hasattr(order_type, "value") else str(order_type)
            for order_type in item.supported_order_types
        ],
        supported_time_in_force=list(item.supported_time_in_force),
        constraint_metadata_complete=item.constraint_metadata_complete,
        notes=item.notes,
    )


def _prepared_venue_order_response(item: PreparedVenueOrder) -> PreparedVenueOrderResponse:
    payload = dict(item.payload or {})
    routed_lineage = payload.get("routed_lineage")
    return PreparedVenueOrderResponse(
        intent_id=item.intent_id,
        desired_trade_key=item.desired_trade_key,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        support_level=item.support_level,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        side=item.side,
        quantity=float(item.quantity),
        order_type=item.order_type.value,
        limit_price=float(item.limit_price) if item.limit_price is not None else None,
        reduce_only=item.reduce_only,
        time_in_force=item.time_in_force,
        client_order_id=item.client_order_id,
        preview_status=item.preview_status,
        reason_codes=list(item.reason_codes),
        payload=item.payload,
        routed_lineage=routed_lineage if isinstance(routed_lineage, dict) else None,
        constraints=(
            _venue_order_constraints_response(item.constraints) if item.constraints is not None else None
        ),
        venue_capabilities=(
            _exchange_capabilities_response(item.venue_capabilities)
            if item.venue_capabilities is not None
            else None
        ),
        account_connectivity=(
            _venue_account_connectivity_response(item.account_connectivity)
            if item.account_connectivity is not None
            else None
        ),
        prepared_at=item.prepared_at,
    )


def _submitted_order_recovery_response(
    item: SubmittedOrderRecoveryRecommendation,
) -> SubmittedOrderRecoveryRecommendationResponse:
    return SubmittedOrderRecoveryRecommendationResponse(
        submitted_order_id=item.submitted_order_id,
        intent_id=item.intent_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        category=item.category,
        retryable=item.retryable,
        operator_action_required=item.operator_action_required,
        venue_state_uncertain=item.venue_state_uncertain,
        account_policy_block=item.account_policy_block,
        reason_codes=list(item.reason_codes),
        message=item.message,
        recommended_action=item.recommended_action,
        routed_origin=item.routed_origin,
        routed_lifecycle_context=_routed_lifecycle_context_response(
            item.routed_lifecycle_context
        ),
    )


def _submitted_order_actionability_response(
    item: SubmittedOrderActionability,
) -> SubmittedOrderActionabilityResponse:
    return SubmittedOrderActionabilityResponse(
        submitted_order_id=item.submitted_order_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        status=item.status.value,
        reconciliation_status=item.reconciliation_status,
        cancel_supported=item.cancel_supported,
        cancel_allowed_now=item.cancel_allowed_now,
        amend_supported=item.amend_supported,
        amend_allowed_now=item.amend_allowed_now,
        cancel_reason_codes=list(item.cancel_reason_codes),
        amend_reason_codes=list(item.amend_reason_codes),
        message=item.message,
        routed_origin=item.routed_origin,
        routed_lifecycle_context=_routed_lifecycle_context_response(
            item.routed_lifecycle_context
        ),
    )


def _submitted_order_recovery_execution_response(
    item: SubmittedOrderRecoveryExecutionResult,
) -> SubmittedOrderRecoveryExecutionResponse:
    return SubmittedOrderRecoveryExecutionResponse(
        submitted_order_id=item.submitted_order_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        action=item.action,
        executed=item.executed,
        blocked=item.blocked,
        reason_codes=list(item.reason_codes),
        message=item.message,
        resulting_submitted_order_id=item.resulting_submitted_order_id,
        resulting_order=(
            _submitted_order_response(item.resulting_order)
            if item.resulting_order is not None
            else None
        ),
        routed_origin=item.routed_origin,
        routed_lifecycle_context=_routed_lifecycle_context_response(
            item.routed_lifecycle_context
        ),
    )


def _routed_lifecycle_context_response(
    item: SubmittedOrderRoutedLifecycleContext | None,
) -> RoutedSubmittedOrderLifecycleContextResponse | None:
    if item is None:
        return None
    return RoutedSubmittedOrderLifecycleContextResponse(
        routed_origin=item.routed_origin,
        intent_id=item.intent_id,
        desired_trade_key=item.desired_trade_key,
        routing_assessment_id=item.routing_assessment_id,
        route_readiness_audit_id=item.route_readiness_audit_id,
        routing_target_recommendation_id=item.routing_target_recommendation_id,
        routing_target_choice_id=item.routing_target_choice_id,
        recommendation_policy_name=item.recommendation_policy_name,
        selected_binding_ref_id=item.selected_binding_ref_id,
        selected_binding_key=item.selected_binding_key,
        selected_venue_account_ref_id=item.selected_venue_account_ref_id,
        selected_venue_account_key=item.selected_venue_account_key,
        selected_venue=item.selected_venue,
        selected_exchange_symbol=item.selected_exchange_symbol,
        readiness_evaluation_id=item.readiness_evaluation_id,
        explicit_action_required=item.explicit_action_required,
        auto_submit=item.auto_submit,
        fanout_created=item.fanout_created,
        allocation_created=item.allocation_created,
        scoring_created=item.scoring_created,
        route_executor_created=item.route_executor_created,
        target_reselection=item.target_reselection,
        submitted_order_created=item.submitted_order_created,
        same_target_only=item.same_target_only,
        same_account_only=item.same_account_only,
        same_venue_only=item.same_venue_only,
        boundary_reason_codes=list(item.boundary_reason_codes),
        route_lineage_malformed=item.route_lineage_malformed,
        missing_lineage_fields=list(item.missing_lineage_fields),
        malformed_lineage_fields=list(item.malformed_lineage_fields),
        routed_order_shape_policy=(
            dict(item.routed_order_shape_policy)
            if item.routed_order_shape_policy is not None
            else None
        ),
    )


def _routed_submitted_order_lineage_response(
    item: SubmittedOrderRoutedLifecycleContext | None,
) -> tuple[bool, RoutedSubmittedOrderLineageResponse | None]:
    if item is None:
        return False, None

    return True, RoutedSubmittedOrderLineageResponse(
        routed_origin=item.routed_origin,
        intent_id=item.intent_id,
        desired_trade_key=item.desired_trade_key,
        routing_assessment_id=item.routing_assessment_id,
        route_readiness_audit_id=item.route_readiness_audit_id,
        routing_target_recommendation_id=item.routing_target_recommendation_id,
        routing_target_choice_id=item.routing_target_choice_id,
        recommendation_policy_name=item.recommendation_policy_name,
        selected_binding_ref_id=item.selected_binding_ref_id,
        selected_binding_key=item.selected_binding_key,
        selected_venue_account_ref_id=item.selected_venue_account_ref_id,
        selected_venue_account_key=item.selected_venue_account_key,
        selected_venue=item.selected_venue,
        selected_exchange_symbol=item.selected_exchange_symbol,
        readiness_evaluation_id=item.readiness_evaluation_id,
        explicit_action_required=item.explicit_action_required,
        auto_submit=item.auto_submit,
        fanout_created=item.fanout_created,
        allocation_created=item.allocation_created,
        scoring_created=item.scoring_created,
        route_executor_created=item.route_executor_created,
        target_reselection=item.target_reselection,
        submitted_order_created=item.submitted_order_created,
        route_lineage_malformed=item.route_lineage_malformed,
        missing_lineage_fields=list(item.missing_lineage_fields),
        malformed_lineage_fields=list(item.malformed_lineage_fields),
    )


def _submitted_order_response(item: SubmittedOrder) -> SubmittedOrderResponse:
    routed_lifecycle_context = submitted_order_routed_lifecycle_context_from_raw_payload(
        item.raw_payload
    )
    routed_origin, routed_lineage = _routed_submitted_order_lineage_response(
        routed_lifecycle_context
    )
    return SubmittedOrderResponse(
        submitted_order_id=item.submitted_order_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        account_address=item.account_address,
        intent_id=item.intent_id,
        client_order_id=item.client_order_id,
        exchange_order_id=item.exchange_order_id,
        symbol=item.symbol,
        side=item.side,
        order_type=item.order_type.value if item.order_type is not None else None,
        limit_price=float(item.limit_price) if item.limit_price is not None else None,
        original_quantity=(
            float(item.original_quantity) if item.original_quantity is not None else None
        ),
        remaining_quantity=(
            float(item.remaining_quantity) if item.remaining_quantity is not None else None
        ),
        reduce_only=item.reduce_only,
        status=item.status.value,
        reconciliation_status=item.reconciliation_status,
        submitted_at=item.submitted_at,
        acknowledged_at=item.acknowledged_at,
        filled_quantity=float(item.filled_quantity) if item.filled_quantity is not None else None,
        average_fill_price=(
            float(item.average_fill_price) if item.average_fill_price is not None else None
        ),
        last_fill_at=item.last_fill_at,
        last_reconciled_at=item.last_reconciled_at,
        status_reason_code=item.status_reason_code,
        status_message=item.status_message,
        reason_codes=list(item.reason_codes),
        cancelable_in_principle=item.cancelable_in_principle,
        amendable_in_principle=item.amendable_in_principle,
        routed_origin=routed_origin,
        routed_lineage=routed_lineage,
        routed_lifecycle_context=_routed_lifecycle_context_response(
            routed_lifecycle_context
        ),
        raw_payload=item.raw_payload,
    )


def _submitted_order_event_response(
    item: SubmittedOrderLifecycleEvent,
) -> SubmittedOrderLifecycleEventResponse:
    return SubmittedOrderLifecycleEventResponse(
        event_id=item.event_id,
        submitted_order_id=item.submitted_order_id,
        intent_id=item.intent_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        status=item.status.value,
        reconciliation_status=item.reconciliation_status,
        event_type=item.event_type,
        reason_codes=list(item.reason_codes),
        message=item.message,
        raw_payload=item.raw_payload,
        observed_at=item.observed_at,
        routed_origin=item.routed_origin,
        routed_lifecycle_context=_routed_lifecycle_context_response(
            item.routed_lifecycle_context
        ),
    )


def _fill_response(item: Fill) -> FillResponse:
    return FillResponse(
        fill_id=item.fill_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        venue_account_ref_id=item.venue_account_ref_id,
        venue=item.venue,
        account_address=item.account_address,
        submitted_order_id=item.submitted_order_id,
        exchange_order_id=item.exchange_order_id,
        symbol=item.symbol,
        price=float(item.price),
        quantity=float(item.quantity),
        fee=float(item.fee),
        filled_at=item.filled_at,
    )


def _desired_trade_response(item: MandateDesiredTrade) -> MandateDesiredTradeResponse:
    return MandateDesiredTradeResponse(
        desired_trade_key=item.desired_trade_key,
        desired_trade_ref_id=item.desired_trade_ref_id,
        evaluated_state_fingerprint=item.evaluated_state_fingerprint,
        environment=item.environment,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        family=item.family,
        component_key=item.component_key,
        market_data_source_policy_ref_id=item.market_data_source_policy_ref_id,
        planning_source_venue=item.planning_source_venue,
        planning_source_mode=item.planning_source_mode,
        planning_as_of=item.planning_as_of,
        target_scope=item.target_scope,
        mandate_account_binding_ref_id=item.mandate_account_binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        action=item.action,
        side=item.side,
        desired_quantity=float(item.desired_quantity) if item.desired_quantity is not None else None,
        desired_notional=float(item.desired_notional) if item.desired_notional is not None else None,
        source_decision_ids=list(item.source_decision_ids),
        source_evaluation_keys=list(item.source_evaluation_keys),
        source_binding_keys=list(item.source_binding_keys),
        status=item.status,
        status_reason_code=item.status_reason_code,
        status_message=item.status_message,
        provenance=item.provenance,
        created_at=item.created_at,
        approved_at=item.approved_at,
        rejected_at=item.rejected_at,
    )


def _execution_readiness_response(
    item: ExecutionReadinessAssessment,
) -> ExecutionReadinessAssessmentResponse:
    routed_lineage = item.provenance.get("routed_lineage")
    return ExecutionReadinessAssessmentResponse(
        readiness_evaluation_id=item.readiness_evaluation_id,
        readiness_evaluation_key=item.readiness_evaluation_key,
        environment=item.environment,
        intent_ref_id=item.intent_ref_id,
        intent_id=item.intent_id,
        mandate_desired_trade_ref_id=item.mandate_desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_account_binding_ref_id=item.mandate_account_binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        venue=item.venue,
        support_level=item.support_level,
        preview_status=item.preview_status,
        outcome=item.outcome,
        eligible_for_submission_in_principle=item.eligible_for_submission_in_principle,
        live_submission_phase_enabled=item.live_submission_phase_enabled,
        venue_supports_order_submission=item.venue_supports_order_submission,
        adapter_supports_order_submission=item.adapter_supports_order_submission,
        adapter_supports_order_cancel=item.adapter_supports_order_cancel,
        adapter_supports_order_amend=item.adapter_supports_order_amend,
        submission_authorized=item.submission_authorized,
        account_connected=item.account_connected,
        private_state_required=item.private_state_required,
        private_state_ready=item.private_state_ready,
        reason_codes=list(item.reason_codes),
        message=item.message,
        prepared_order=(
            _prepared_venue_order_response(item.prepared_order)
            if item.prepared_order is not None
            else None
        ),
        routed_lineage=routed_lineage if isinstance(routed_lineage, dict) else None,
        evaluated_at=item.evaluated_at,
        provenance=item.provenance,
    )


def _order_intent_response(item: OrderIntent) -> OrderIntentResponse:
    return OrderIntentResponse(
        intent_id=item.intent_id,
        decision_id=item.decision_id,
        action=item.action,
        desired_trade_key=item.desired_trade_key,
        mandate_desired_trade_ref_id=item.mandate_desired_trade_ref_id,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_account_binding_ref_id=item.mandate_account_binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        side=item.side,
        order_type=item.order_type.value,
        quantity=float(item.quantity),
        limit_price=float(item.limit_price) if item.limit_price is not None else None,
        reduce_only=item.reduce_only,
        ttl_seconds=item.ttl_seconds,
        status=item.status,
        idempotency_key=item.idempotency_key,
        created_at=item.created_at,
        provenance=item.provenance,
    )


def _risk_evaluation_response(item: RiskEvaluation) -> RiskEvaluationResponse:
    return RiskEvaluationResponse(
        risk_evaluation_id=item.risk_evaluation_id,
        risk_evaluation_key=item.risk_evaluation_key,
        environment=item.environment,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        market_data_source_policy_ref_id=item.market_data_source_policy_ref_id,
        planning_source_venue=item.planning_source_venue,
        decision_id=item.decision_id,
        decision_evaluation_key=item.decision_evaluation_key,
        component_key=item.component_key,
        target_scope=item.target_scope,
        mandate_account_binding_ref_id=item.mandate_account_binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        action=item.action,
        decision_status=item.decision_status,
        outcome=item.outcome,
        reason_code=item.reason_code,
        message=item.message,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        desired_trade_status=item.desired_trade_status,
        child_intent_ref_id=item.child_intent_ref_id,
        child_intent_id=item.child_intent_id,
        child_intent_status=item.child_intent_status,
        policy_checks=item.policy_checks,
        provenance=item.provenance,
        evaluated_at=item.evaluated_at,
    )


def _routing_candidate_response(item: BindingRoutingCandidate) -> BindingRoutingCandidateResponse:
    return BindingRoutingCandidateResponse(
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        market_data_source_policy_ref_id=item.market_data_source_policy_ref_id,
        planning_source_venue=item.planning_source_venue,
        binding_ref_id=item.binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        venue_account_key=item.venue_account_key,
        venue=item.venue,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        strategy_eligible=item.strategy_eligible,
        trading_eligible=item.trading_eligible,
        routing_eligible=item.routing_eligible,
        account_connected=item.account_connected,
        quote_available=item.quote_available,
        available_balance_hint=(
            float(item.available_balance_hint) if item.available_balance_hint is not None else None
        ),
        venue_capabilities=_exchange_capabilities_response(item.venue_capabilities),
        account_connectivity=_venue_account_connectivity_response(item.account_connectivity),
        quote_snapshot=(
            _binding_quote_response(item.quote_snapshot) if item.quote_snapshot is not None else None
        ),
        eligibility_reasons=list(item.eligibility_reasons),
    )


def _routing_request_response(item: RoutingRequest) -> RoutingRequestResponse:
    return RoutingRequestResponse(
        routing_request_id=item.routing_request_id,
        environment=item.environment,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        market_data_source_policy_ref_id=item.market_data_source_policy_ref_id,
        planning_source_venue=item.planning_source_venue,
        planning_source_mode=item.planning_source_mode,
        target_scope=item.target_scope,
        action=item.action,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        component_key=item.component_key,
        requested_at=item.requested_at,
    )


def _routing_candidate_assessment_response(
    item: RoutingCandidateAssessment,
) -> RoutingCandidateAssessmentResponse:
    return RoutingCandidateAssessmentResponse(
        assessment_id=item.assessment_id,
        binding_ref_id=item.binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        venue_account_key=item.venue_account_key,
        venue=item.venue,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        eligibility_status=item.eligibility_status,
        reason_codes=list(item.reason_codes),
        missing_data=list(item.missing_data),
        fact_snapshot=dict(item.fact_snapshot),
        evaluated_at=item.evaluated_at,
    )


def _routing_assessment_response(item: RoutingAssessment) -> RoutingAssessmentResponse:
    return RoutingAssessmentResponse(
        assessment_id=item.assessment_id,
        environment=item.environment,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        market_data_source_policy_ref_id=item.market_data_source_policy_ref_id,
        planning_source_venue=item.planning_source_venue,
        instrument_key=item.instrument_key,
        instrument_ref_id=item.instrument_ref_id,
        symbol=item.symbol,
        action=item.action,
        target_scope=item.target_scope,
        decision_status=item.decision_status,
        eligible_binding_count=item.eligible_binding_count,
        ineligible_binding_count=item.ineligible_binding_count,
        request=_routing_request_response(item.request),
        candidates=[_routing_candidate_assessment_response(candidate) for candidate in item.candidates],
        reason_codes=list(item.reason_codes),
        missing_data=list(item.missing_data),
        evaluated_at=item.evaluated_at,
        provenance=item.provenance,
    )


def _route_readiness_candidate_audit_response(
    item,
) -> RouteReadinessCandidateAuditResponse:
    return RouteReadinessCandidateAuditResponse(
        binding_ref_id=item.binding_ref_id,
        binding_key=item.binding_key,
        venue_account_ref_id=item.venue_account_ref_id,
        venue_account_key=item.venue_account_key,
        venue=item.venue,
        instrument_ref_id=item.instrument_ref_id,
        instrument_key=item.instrument_key,
        symbol=item.symbol,
        exchange_symbol=item.exchange_symbol,
        status=item.status,
        reason_codes=list(item.reason_codes),
        missing_data=list(item.missing_data),
        stale_data=list(item.stale_data),
        unsupported_data=list(item.unsupported_data),
        unavailable_data=list(item.unavailable_data),
        policy_blocks=list(item.policy_blocks),
        blocking_reasons=list(item.blocking_reasons),
        fact_snapshot=dict(item.fact_snapshot),
        data_sources=dict(item.data_sources),
        evaluated_at=item.evaluated_at,
    )


def _route_readiness_audit_response(item: RouteReadinessAudit) -> RouteReadinessAuditResponse:
    return RouteReadinessAuditResponse(
        route_readiness_audit_id=item.route_readiness_audit_id,
        environment=item.environment,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        routing_assessment_ref_id=item.routing_assessment_ref_id,
        routing_assessment_id=item.routing_assessment_id,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        instrument_ref_id=item.instrument_ref_id,
        instrument_key=item.instrument_key,
        symbol=item.symbol,
        action=item.action,
        target_scope=item.target_scope,
        evaluated_at=item.evaluated_at,
        overall_status=item.overall_status,
        candidate_count=item.candidate_count,
        ready_candidate_count=item.ready_candidate_count,
        blocked_candidate_count=item.blocked_candidate_count,
        insufficient_data_candidate_count=item.insufficient_data_candidate_count,
        global_reason_codes=list(item.global_reason_codes),
        global_missing_data=list(item.global_missing_data),
        global_stale_data=list(item.global_stale_data),
        global_blocking_reasons=list(item.global_blocking_reasons),
        candidates=[
            _route_readiness_candidate_audit_response(candidate) for candidate in item.candidates
        ],
        non_selecting=item.non_selecting,
        recommendation_created=item.recommendation_created,
        target_choice_created=item.target_choice_created,
        child_intent_created=item.child_intent_created,
        submitted_order_created=item.submitted_order_created,
        provenance=dict(item.provenance),
    )


def _routing_target_recommendation_response(
    item: RoutingTargetRecommendation,
) -> RoutingTargetRecommendationResponse:
    return RoutingTargetRecommendationResponse(
        routing_target_recommendation_id=item.routing_target_recommendation_id,
        environment=item.environment,
        route_readiness_audit_ref_id=item.route_readiness_audit_ref_id,
        route_readiness_audit_id=item.route_readiness_audit_id,
        routing_assessment_ref_id=item.routing_assessment_ref_id,
        routing_assessment_id=item.routing_assessment_id,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        client_ref_id=item.client_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        instrument_ref_id=item.instrument_ref_id,
        instrument_key=item.instrument_key,
        symbol=item.symbol,
        action=item.action,
        target_scope=item.target_scope,
        status=item.status,
        policy_name=item.policy_name,
        recommended_binding_ref_id=item.recommended_binding_ref_id,
        recommended_binding_key=item.recommended_binding_key,
        recommended_venue_account_ref_id=item.recommended_venue_account_ref_id,
        recommended_venue_account_key=item.recommended_venue_account_key,
        recommended_venue=item.recommended_venue,
        recommended_exchange_symbol=item.recommended_exchange_symbol,
        candidate_count=item.candidate_count,
        ready_candidate_count=item.ready_candidate_count,
        reason_codes=list(item.reason_codes),
        blocking_reasons=list(item.blocking_reasons),
        missing_data=list(item.missing_data),
        stale_data=list(item.stale_data),
        non_executing=item.non_executing,
        target_choice_created=item.target_choice_created,
        child_intent_created=item.child_intent_created,
        submitted_order_created=item.submitted_order_created,
        created_at=item.created_at,
        provenance=dict(item.provenance),
    )


def _routing_target_choice_response(item: RoutingTargetChoice) -> RoutingTargetChoiceResponse:
    return RoutingTargetChoiceResponse(
        target_choice_id=item.target_choice_id,
        environment=item.environment,
        routing_assessment_ref_id=item.routing_assessment_ref_id,
        routing_assessment_id=item.routing_assessment_id,
        desired_trade_ref_id=item.desired_trade_ref_id,
        desired_trade_key=item.desired_trade_key,
        selected_binding_ref_id=item.selected_binding_ref_id,
        selected_binding_key=item.selected_binding_key,
        selected_venue_account_ref_id=item.selected_venue_account_ref_id,
        selected_venue_account_key=item.selected_venue_account_key,
        selected_venue=item.selected_venue,
        status=item.status,
        reason_codes=list(item.reason_codes),
        missing_data=list(item.missing_data),
        approval_note=item.approval_note,
        requested_by=item.requested_by,
        non_executing=item.non_executing,
        created_at=item.created_at,
        selected_at=item.selected_at,
        provenance=dict(item.provenance),
    )


def _routing_target_choice_conversion_response(
    item: RoutingTargetChoiceConversionResult,
) -> RoutingTargetChoiceConversionResponse:
    return RoutingTargetChoiceConversionResponse(
        target_choice_id=item.target_choice_id,
        environment=item.environment,
        status=item.status,
        routing_assessment_id=item.routing_assessment_id,
        desired_trade_key=item.desired_trade_key,
        routing_target_recommendation_id=item.routing_target_recommendation_id,
        route_readiness_audit_id=item.route_readiness_audit_id,
        selected_binding_ref_id=item.selected_binding_ref_id,
        selected_binding_key=item.selected_binding_key,
        selected_venue_account_ref_id=item.selected_venue_account_ref_id,
        selected_venue_account_key=item.selected_venue_account_key,
        selected_venue=item.selected_venue,
        selected_exchange_symbol=item.selected_exchange_symbol,
        intent_id=item.intent_id,
        reason_codes=list(item.reason_codes),
        missing_data=list(item.missing_data),
        non_submitting=item.non_submitting,
        child_intent_created=item.child_intent_created,
        child_intent_reused=item.child_intent_reused,
        prepared_order_created=item.prepared_order_created,
        readiness_assessment_created=item.readiness_assessment_created,
        submitted_order_created=item.submitted_order_created,
        converted_at=item.converted_at,
        provenance=dict(item.provenance),
    )


def _source_policy_response(item: MandateMarketDataSourcePolicy) -> MandateMarketDataSourcePolicyResponse:
    return MandateMarketDataSourcePolicyResponse(
        policy_ref_id=item.policy_ref_id,
        strategy_mandate_ref_id=item.strategy_mandate_ref_id,
        mandate_key=item.mandate_key,
        source_mode=item.source_mode,
        source_venue=item.source_venue,
        market_type=item.market_type,
        product_type=item.product_type,
        instrument_resolution_mode=item.instrument_resolution_mode,
        runtime_exchange_venue=item.runtime_exchange_venue,
        runtime_exchange_matches_source=item.runtime_exchange_matches_source,
        notes=item.notes,
        metadata=item.metadata,
    )


def _convertibility_response(
    item: DesiredTradeConvertibilityAssessment,
) -> DesiredTradeConvertibilityResponse:
    return DesiredTradeConvertibilityResponse(
        decision_id=item.decision_id,
        convertible=item.convertible,
        decision_status=item.decision_status,
        action=item.action,
        target_scope=item.target_scope,
        reason_code=item.reason_code,
        message=item.message,
        instrument_key=item.instrument_key,
        desired_trade_key_preview=item.desired_trade_key_preview,
    )


def _market_data_health_for_venue(
    venue: str,
    settings: AppSettings,
) -> MarketDataHealthResponse:
    with SessionLocal() as session:
        rows = session.scalars(
            select(MarketDataHealthModel).where(
                MarketDataHealthModel.environment == settings.app.environment,
                MarketDataHealthModel.venue == venue,
            )
        ).all()
    payload = MarketDataHealth(
        venue=venue,
        environment=settings.app.environment,
        tracked_symbols=len({row.symbol for row in rows}),
        tracked_timeframes=len({row.timeframe for row in rows}),
        stale_streams=sum(1 for row in rows if row.is_stale),
        last_candle_at=max((row.last_candle_close_time for row in rows), default=None),
        last_sync_at=max((row.last_synced_at for row in rows), default=None),
        last_error=next((row.last_error for row in rows if row.last_error), None),
    )
    return MarketDataHealthResponse(**asdict(payload))


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(UTC))


@router.get("/readiness", response_model=ReadinessResponse, tags=["ops"])
def readiness(settings: AppSettings = Depends(get_app_settings)) -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        environment=settings.app.environment,
        checks={"config_loaded": True, "db_config_present": True},
    )


@v1.get("/config/summary", response_model=ConfigSummaryResponse, tags=["config"])
def config_summary(settings: AppSettings = Depends(get_app_settings)) -> ConfigSummaryResponse:
    return ConfigSummaryResponse.from_settings(settings)


@v1.get("/sleeves", response_model=list[SleeveStatusResponse], tags=["sleeves"])
async def sleeve_status(
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
    settings: AppSettings = Depends(get_app_settings),
) -> list[SleeveStatusResponse]:
    context = await runtime_context_service.ensure_active_context()
    primary_binding = context.bindings[0] if context.bindings else None
    components = primary_binding.component_configs if primary_binding is not None else []
    return [
        SleeveStatusResponse(
            sleeve_id=component.component_key,
            timeframe=component.timeframe or Timeframe.M15,
            enabled=component.enabled,
            capital_allocation_pct=float(component.capital_allocation_pct),
            max_open_risk_pct=float(component.max_open_risk_pct),
            trading_enabled=settings.risk.trading_enabled,
        )
        for component in components
    ]


@v1.get("/components", response_model=list[StrategyComponentStatusResponse], tags=["strategy"])
async def component_status(
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
    settings: AppSettings = Depends(get_app_settings),
) -> list[StrategyComponentStatusResponse]:
    context = await runtime_context_service.ensure_active_context()
    primary_binding = context.bindings[0] if context.bindings else None
    components = primary_binding.component_configs if primary_binding is not None else []
    return [
        _component_status_response(component, trading_enabled=settings.risk.trading_enabled)
        for component in components
    ]


@v1.get("/portfolio/summary", response_model=PortfolioSummaryResponse, tags=["portfolio"])
def portfolio_summary(settings: AppSettings = Depends(get_app_settings)) -> PortfolioSummaryResponse:
    return PortfolioSummaryResponse(
        environment=settings.app.environment,
        account_equity=0.0,
        total_gross_exposure=0.0,
        total_net_exposure=0.0,
        drawdown_pct=0.0,
        kill_switch_engaged=False,
    )


@v1.get("/positions", response_model=list[PositionResponse], tags=["portfolio"])
async def open_positions(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> list[PositionResponse]:
    positions = await portfolio_service.get_open_positions()
    return [
        PositionResponse(
            position_id=position.position_id,
            sleeve_id=position.sleeve_id,
            symbol=position.symbol,
            quantity=float(position.quantity),
            avg_entry_price=float(position.avg_entry_price),
            unrealized_pnl=float(position.unrealized_pnl) if position.unrealized_pnl is not None else None,
        )
        for position in positions
    ]


@v1.get("/risk/events", response_model=list[RiskEventResponse], tags=["risk"])
def recent_risk_events() -> list[RiskEventResponse]:
    return []


@v1.get("/risk/evaluations", response_model=list[RiskEvaluationResponse], tags=["risk"])
async def recent_risk_evaluations(
    outcome: RiskEvaluationOutcome | None = None,
    desired_trade_status: MandateDesiredTradeStatus | None = None,
    limit: int = 100,
    risk_engine: RiskEngine = Depends(get_risk_engine),
) -> list[RiskEvaluationResponse]:
    evaluations = await risk_engine.recent_evaluations(
        outcome=outcome.value if outcome is not None else None,
        desired_trade_status=desired_trade_status,
        limit=limit,
    )
    return [_risk_evaluation_response(item) for item in evaluations]


@v1.post(
    "/risk/evaluations/from-decision/{decision_id}",
    response_model=RiskEvaluationResponse,
    tags=["risk"],
    dependencies=[Depends(require_operator)],
)
async def evaluate_risk_for_decision(
    decision_id: str,
    risk_engine: RiskEngine = Depends(get_risk_engine),
) -> RiskEvaluationResponse:
    try:
        evaluation = await risk_engine.evaluate_strategy_decision(decision_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _risk_evaluation_response(evaluation)


@v1.get("/exchange/status", response_model=ExchangeStatusResponse, tags=["exchange"])
async def exchange_status(
    adapter: ExchangeAdapter = Depends(get_exchange_adapter),
) -> ExchangeStatusResponse:
    status = await adapter.get_exchange_status()
    return ExchangeStatusResponse(**asdict(status))


@v1.get("/exchange/capabilities", response_model=ExchangeCapabilitiesResponse, tags=["exchange"])
async def exchange_capabilities(
    adapter: ExchangeAdapter = Depends(get_exchange_adapter),
) -> ExchangeCapabilitiesResponse:
    capabilities = await adapter.get_venue_capabilities()
    return _exchange_capabilities_response(capabilities)


@v1.get("/exchange/instruments", response_model=list[InstrumentResponse], tags=["exchange"])
async def exchange_instruments(
    adapter: ExchangeAdapter = Depends(get_exchange_adapter),
) -> list[InstrumentResponse]:
    instruments = await adapter.list_instruments()
    return [_instrument_response(item) for item in instruments]


@v1.get("/venues", response_model=list[VenueIntegrationSummaryResponse], tags=["venues"])
async def supported_venues(
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> list[VenueIntegrationSummaryResponse]:
    venues = await registry.list_supported_venues()
    return [VenueIntegrationSummaryResponse(**asdict(item)) for item in venues]


@v1.get("/venues/{venue}/status", response_model=ExchangeStatusResponse, tags=["venues"])
async def venue_status(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> ExchangeStatusResponse:
    adapter = await registry.get_adapter(venue)
    status = await adapter.get_exchange_status()
    return ExchangeStatusResponse(**asdict(status))


@v1.get("/venues/{venue}/capabilities", response_model=ExchangeCapabilitiesResponse, tags=["venues"])
async def venue_capabilities(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> ExchangeCapabilitiesResponse:
    adapter = await registry.get_adapter(venue)
    capabilities = await adapter.get_venue_capabilities()
    return _exchange_capabilities_response(capabilities)


@v1.get("/venues/{venue}/instruments", response_model=list[InstrumentResponse], tags=["venues"])
async def venue_instruments(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> list[InstrumentResponse]:
    adapter = await registry.get_adapter(venue)
    instruments = await adapter.list_instruments()
    return [_instrument_response(item) for item in instruments]


@v1.get("/venues/{venue}/symbols", response_model=list[ExchangeSymbolResponse], tags=["venues"])
async def venue_symbols(venue: str) -> list[ExchangeSymbolResponse]:
    with SessionLocal() as session:
        models = session.scalars(
            select(SymbolModel).where(SymbolModel.venue == venue).order_by(SymbolModel.symbol.asc())
        ).all()
    return [_symbol_response(model) for model in models]


@v1.post(
    "/venues/{venue}/sync/catalog",
    response_model=ExchangeSyncResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
)
async def sync_venue_catalog(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> ExchangeSyncResponse:
    adapter = await registry.get_adapter(venue)
    symbols = await adapter.sync_symbols()
    return ExchangeSyncResponse(synced=len(symbols), observed_at=datetime.now(UTC))


@v1.get(
    "/venues/{venue}/account-connectivity",
    response_model=VenueAccountConnectivityResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
)
async def venue_account_connectivity(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenueAccountConnectivityResponse:
    adapter = await registry.get_adapter(venue)
    connectivity = await adapter.get_account_connectivity()
    return _venue_account_connectivity_response(connectivity)


@v1.get(
    "/venues/{venue}/account-snapshot",
    response_model=ExchangeAccountSnapshotResponse | None,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
)
async def venue_account_snapshot(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> ExchangeAccountSnapshotResponse | None:
    adapter = await registry.get_adapter(venue)
    snapshot = await adapter.read_account_snapshot()
    if snapshot is None:
        return None
    return _exchange_account_snapshot_response(snapshot)


@v1.get(
    "/venues/{venue}/session-state",
    response_model=ExchangeSessionStateResponse,
    tags=["venues"],
    summary="Adapter/runtime session state",
    description=(
        "Returns adapter/runtime connection bookkeeping for the selected venue integration. "
        "This surface does not imply deep venue-private account session truth."
    ),
)
async def venue_session_state(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> ExchangeSessionStateResponse:
    adapter = await registry.get_adapter(venue)
    state = await adapter.get_session_state()
    return _exchange_session_state_response(state)


@v1.get(
    "/venues/{venue}/private-state-summary",
    response_model=VenuePrivateStateSummaryResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
    description=(
        "Returns a private-state summary for the adapter's current default venue/account context. "
        "The open-order and recent-fill source fields describe the runtime path actually used for this call."
    ),
)
async def venue_private_state_summary(
    venue: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenuePrivateStateSummaryResponse:
    adapter = await registry.get_adapter(venue)
    summary = await adapter.get_private_state_summary()
    return _venue_private_state_summary_response(summary)


@v1.get(
    "/venues/{venue}/private-state/open-orders",
    response_model=VenuePrivateOpenOrdersViewResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
    description=(
        "Returns venue-private open-order snapshots for the targeted venue account. "
        "These are distinct from platform SubmittedOrder records; optional linkage fields are correlation-only. "
        "The source field reports the runtime path actually used for this call."
    ),
)
async def venue_private_open_orders(
    venue: str,
    venue_account_ref_id: str | None = None,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenuePrivateOpenOrdersViewResponse:
    adapter = await registry.get_adapter(venue)
    source, orders = await adapter.fetch_open_orders_with_source(venue_account_ref_id=venue_account_ref_id)
    return _venue_private_open_orders_view_response(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=list(orders),
    )


@v1.get(
    "/venues/{venue}/private-state/recent-fills",
    response_model=VenuePrivateRecentFillsViewResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
    description="Returns recent private fills for the targeted venue account and reports the runtime source actually used for this call.",
)
async def venue_private_recent_fills(
    venue: str,
    venue_account_ref_id: str | None = None,
    limit: int = 100,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenuePrivateRecentFillsViewResponse:
    adapter = await registry.get_adapter(venue)
    source, fills = await adapter.fetch_recent_fills_with_source(
        limit=limit,
        venue_account_ref_id=venue_account_ref_id,
    )
    return _venue_private_recent_fills_view_response(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=list(fills),
    )


@v1.get(
    "/venues/{venue}/private-state/open-positions",
    response_model=VenuePrivateOpenPositionsViewResponse,
    tags=["venues"],
    dependencies=[Depends(require_admin)],
    description="Returns private open positions for the targeted venue account and reports the runtime source actually used for this call.",
)
async def venue_private_open_positions(
    venue: str,
    venue_account_ref_id: str | None = None,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenuePrivateOpenPositionsViewResponse:
    adapter = await registry.get_adapter(venue)
    source, positions = await adapter.fetch_open_positions_with_source(
        venue_account_ref_id=venue_account_ref_id
    )
    return _venue_private_open_positions_view_response(
        venue=venue,
        venue_account_ref_id=venue_account_ref_id,
        source=source,
        items=list(positions),
    )


@v1.get(
    "/venues/{venue}/order-constraints",
    response_model=VenueOrderConstraintsResponse | None,
    tags=["venues"],
)
async def venue_order_constraints(
    venue: str,
    instrument_key: str | None = None,
    instrument_ref_id: str | None = None,
    symbol: str | None = None,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> VenueOrderConstraintsResponse | None:
    adapter = await registry.get_adapter(venue)
    constraints = await adapter.get_order_constraints(
        instrument_key=instrument_key,
        instrument_ref_id=instrument_ref_id,
        symbol=symbol.upper() if symbol is not None else None,
    )
    if constraints is None:
        return None
    return _venue_order_constraints_response(constraints)


@v1.get(
    "/venues/{venue}/market-data/health",
    response_model=MarketDataHealthResponse,
    tags=["venues"],
)
async def venue_market_data_health(
    venue: str,
    settings: AppSettings = Depends(get_app_settings),
) -> MarketDataHealthResponse:
    return _market_data_health_for_venue(venue, settings)


@v1.get(
    "/venues/{venue}/market-data/top-of-book",
    response_model=TopOfBookResponse | None,
    tags=["venues"],
)
async def venue_top_of_book(
    venue: str,
    symbol: str,
    registry: VenueRegistryService = Depends(get_venue_registry_service),
) -> TopOfBookResponse | None:
    adapter = await registry.get_adapter(venue)
    snapshot = await adapter.get_top_of_book(symbol.upper())
    if snapshot is None:
        return None
    return _top_of_book_response(snapshot)


@v1.get("/clients", response_model=list[ClientResponse], tags=["runtime"])
async def list_clients(
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> list[ClientResponse]:
    clients = await runtime_context_service.list_clients()
    return [ClientResponse(**asdict(client)) for client in clients]


@v1.get(
    "/accounts",
    response_model=list[VenueAccountResponse],
    tags=["runtime"],
    dependencies=[Depends(require_admin)],
)
async def list_accounts(
    client_key: str | None = None,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> list[VenueAccountResponse]:
    accounts = await runtime_context_service.list_venue_accounts(client_key=client_key)
    return [VenueAccountResponse(**asdict(account)) for account in accounts]


@v1.get("/mandates", response_model=list[StrategyMandateResponse], tags=["runtime"])
async def list_mandates(
    client_key: str | None = None,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> list[StrategyMandateResponse]:
    mandates = await runtime_context_service.list_mandates(client_key=client_key)
    return [StrategyMandateResponse(**asdict(mandate)) for mandate in mandates]


@v1.post(
    "/mandates",
    response_model=StrategyMandateResponse,
    tags=["runtime"],
    dependencies=[Depends(require_admin)],
)
async def create_mandate(
    request: CreateMandateRequest,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> StrategyMandateResponse:
    mandate = await runtime_context_service.create_mandate(
        mandate_key=request.mandate_key,
        family=request.family,
        enabled=request.enabled,
        notes=request.notes,
    )
    return StrategyMandateResponse(**asdict(mandate))


@v1.get("/mandates/{mandate_key}/bindings", response_model=list[MandateAccountBindingResponse], tags=["runtime"])
async def list_mandate_bindings(
    mandate_key: str,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> list[MandateAccountBindingResponse]:
    bindings = await runtime_context_service.list_bindings(mandate_key=mandate_key)
    return [MandateAccountBindingResponse(**asdict(binding)) for binding in bindings]


@v1.post(
    "/mandates/{mandate_key}/bindings",
    response_model=MandateAccountBindingResponse,
    tags=["runtime"],
    dependencies=[Depends(require_admin)],
)
async def create_mandate_binding(
    mandate_key: str,
    request: CreateBindingRequest,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> MandateAccountBindingResponse:
    binding = await runtime_context_service.bind_account(
        mandate_key=mandate_key,
        venue_account_key=request.venue_account_key,
        binding_key=request.binding_key,
        enabled=request.enabled,
        strategy_eligible=request.strategy_eligible,
        routing_eligible=request.routing_eligible,
        trading_enabled=request.trading_enabled,
        target_recommendation_priority=request.target_recommendation_priority,
        clear_target_recommendation_priority=request.clear_target_recommendation_priority,
    )
    return MandateAccountBindingResponse(**asdict(binding))


@v1.get(
    "/bindings/{binding_key}/components",
    response_model=list[StrategyComponentConfigResponse],
    tags=["runtime"],
)
async def list_binding_components(
    binding_key: str,
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> list[StrategyComponentConfigResponse]:
    components = await runtime_context_service.list_effective_component_configs(binding_key=binding_key)
    return [
        StrategyComponentConfigResponse(
            component_config_ref_id=component.component_config_ref_id,
            strategy_mandate_ref_id=component.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=component.mandate_account_binding_ref_id,
            component_key=component.component_key,
            component_type=component.component_type,
            timeframe=component.timeframe,
            enabled=component.enabled,
            capital_allocation_pct=float(component.capital_allocation_pct),
            max_open_risk_pct=float(component.max_open_risk_pct),
            parameters=component.parameters,
            metadata=component.metadata,
            is_override=component.is_override,
            source_component_config_ref_id=component.source_component_config_ref_id,
        )
        for component in components
    ]


@v1.get("/runtime/context", response_model=ActiveRuntimeContextResponse, tags=["runtime"])
async def runtime_context(
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
    settings: AppSettings = Depends(get_app_settings),
) -> ActiveRuntimeContextResponse:
    context = await runtime_context_service.ensure_active_context()
    return ActiveRuntimeContextResponse(
        active_client_key=context.client.client_key,
        active_mandate_key=context.mandate.mandate_key,
        family=context.mandate.family,
        environment=context.bindings[0].venue_account.environment if context.bindings else settings.app.environment,
        market_data_source_venue=context.market_data_source_policy.source_venue,
        market_data_source_mode=context.market_data_source_policy.source_mode,
        market_data_source_market_type=context.market_data_source_policy.market_type,
        market_data_source_product_type=context.market_data_source_policy.product_type,
        mandate_instrument_resolution_mode=(
            context.market_data_source_policy.instrument_resolution_mode
        ),
        bound_accounts=[binding.venue_account.venue_account_key for binding in context.bindings],
        components=sorted(
            {component.component_key for binding in context.bindings for component in binding.component_configs}
        ),
    )


@v1.get("/exchange/symbols", response_model=list[ExchangeSymbolResponse], tags=["exchange"])
def exchange_symbols(settings: AppSettings = Depends(get_app_settings)) -> list[ExchangeSymbolResponse]:
    with SessionLocal() as session:
        models = session.scalars(
            select(SymbolModel)
            .where(SymbolModel.venue == settings.exchange.venue)
            .order_by(SymbolModel.symbol.asc())
        ).all()
    return [_symbol_response(model) for model in models]


@v1.post(
    "/exchange/sync/universe",
    response_model=ExchangeSyncResponse,
    tags=["exchange"],
    dependencies=[Depends(require_admin)],
)
async def sync_exchange_universe(
    settings: AppSettings = Depends(get_app_settings),
    adapter: HyperliquidAdapterContract = Depends(get_hyperliquid_adapter),
) -> ExchangeSyncResponse:
    assets = await adapter.sync_universe(
        UniversePolicy(
            include_standard_perp_universe=settings.universe_policy.include_standard_perp_universe,
            include_builder_deployed_in_catalog=settings.universe_policy.include_builder_deployed_in_catalog,
            allow_builder_deployed_for_strategy=settings.universe_policy.allow_builder_deployed_for_strategy,
            allow_builder_deployed_for_trading=settings.universe_policy.allow_builder_deployed_for_trading,
        )
    )
    return ExchangeSyncResponse(synced=len(assets), observed_at=datetime.now(UTC))


@v1.post(
    "/exchange/sync/account",
    response_model=ExchangeSyncResponse,
    tags=["exchange"],
    dependencies=[Depends(require_admin)],
)
async def sync_exchange_account(
    adapter: HyperliquidAdapterContract = Depends(get_hyperliquid_adapter),
) -> ExchangeSyncResponse:
    await adapter.sync_account_state()
    positions = await adapter.reconcile_positions()
    orders = await adapter.reconcile_open_orders()
    fills = await adapter.reconcile_fills(limit=500)
    synced = len(positions.position_ids) + len(orders.open_order_ids) + len(fills.fill_ids)
    return ExchangeSyncResponse(synced=synced, observed_at=datetime.now(UTC))


@v1.post(
    "/market-data/sync/candles",
    response_model=CandleSyncResponse,
    tags=["market-data"],
    dependencies=[Depends(require_operator)],
)
async def sync_market_data_candles(
    request: CandleSyncRequest,
    settings: AppSettings = Depends(get_app_settings),
    market_data_service: MarketDataService = Depends(get_market_data_service),
) -> CandleSyncResponse:
    symbols = request.symbols
    if not symbols:
        with SessionLocal() as session:
            symbols = list(
                session.scalars(
                    select(SymbolModel.symbol).where(
                        SymbolModel.venue == settings.exchange.venue,
                        SymbolModel.is_active.is_(True),
                    )
                ).all()
            )
    synced = await market_data_service.bootstrap_candles(
        symbols=symbols,
        timeframes=[timeframe.value for timeframe in request.timeframes],
        lookback_bars=request.lookback_bars,
    )
    return CandleSyncResponse(synced_candles=synced, observed_at=datetime.now(UTC))


@v1.get("/market-data/health", response_model=MarketDataHealthResponse, tags=["market-data"])
async def market_data_health(
    market_data_service: MarketDataService = Depends(get_market_data_service),
) -> MarketDataHealthResponse:
    health = await market_data_service.get_health()
    return MarketDataHealthResponse(**asdict(health))


@v1.get(
    "/market-data/checkpoints/{symbol}/{timeframe}",
    response_model=MarketDataCheckpointResponse | None,
    tags=["market-data"],
)
async def market_data_checkpoint(
    symbol: str,
    timeframe: Timeframe,
    market_data_service: MarketDataService = Depends(get_market_data_service),
) -> MarketDataCheckpointResponse | None:
    checkpoint = await market_data_service.get_checkpoint(symbol.upper(), timeframe.value)
    if checkpoint is None:
        return None
    return MarketDataCheckpointResponse(**asdict(checkpoint))


@v1.post(
    "/indicators/sync",
    response_model=IndicatorSyncResponse,
    tags=["indicators"],
    dependencies=[Depends(require_operator)],
)
async def sync_indicators(
    request: IndicatorSyncRequest,
    settings: AppSettings = Depends(get_app_settings),
    indicator_service: IndicatorService = Depends(get_indicator_service),
) -> IndicatorSyncResponse:
    persisted = 0
    with SessionLocal() as session:
        query = select(SymbolModel).where(
            SymbolModel.venue == settings.exchange.venue,
            SymbolModel.is_active.is_(True),
        )
        if request.symbols:
            query = query.where(SymbolModel.symbol.in_(request.symbols))
        symbol_models = session.scalars(query.order_by(SymbolModel.symbol.asc())).all()
    for model in symbol_models:
        if not model.instrument_ref_id:
            continue
        for timeframe in request.timeframes:
            persisted += await indicator_service.refresh_snapshots(
                instrument_ref_id=model.instrument_ref_id,
                symbol=model.symbol,
                venue=model.venue,
                timeframe=timeframe.value,
            )
    return IndicatorSyncResponse(persisted_snapshots=persisted, observed_at=datetime.now(UTC))


@v1.get(
    "/indicators/latest",
    response_model=list[IndicatorSnapshotResponse],
    tags=["indicators"],
)
async def latest_indicator_snapshots(
    timeframe: Timeframe | None = None,
    symbol: str | None = None,
    limit: int = 100,
    strategy_engine: StrategyEngine = Depends(get_strategy_engine),
) -> list[IndicatorSnapshotResponse]:
    snapshots = await strategy_engine.latest_indicator_snapshots(
        timeframe=timeframe.value if timeframe is not None else None,
        symbol=symbol.upper() if symbol is not None else None,
        limit=limit,
    )
    return [
        IndicatorSnapshotResponse(
            instrument_key=snapshot.instrument_key,
            instrument_ref_id=snapshot.instrument_ref_id,
            venue=snapshot.venue,
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            as_of=snapshot.as_of,
            ema_5=float(snapshot.ema_5) if snapshot.ema_5 is not None else None,
            ema_10=float(snapshot.ema_10) if snapshot.ema_10 is not None else None,
            sma_20=float(snapshot.sma_20) if snapshot.sma_20 is not None else None,
            rsi_14=float(snapshot.rsi_14) if snapshot.rsi_14 is not None else None,
            macd=float(snapshot.macd) if snapshot.macd is not None else None,
            macd_signal=float(snapshot.macd_signal) if snapshot.macd_signal is not None else None,
            macd_histogram=float(snapshot.macd_histogram)
            if snapshot.macd_histogram is not None
            else None,
        )
        for snapshot in snapshots
    ]


@v1.post(
    "/strategy/evaluate",
    response_model=StrategyEvaluateResponse,
    tags=["strategy"],
    dependencies=[Depends(require_operator)],
)
async def evaluate_strategy(
    request: StrategyEvaluateRequest,
    strategy_engine: StrategyEngine = Depends(get_strategy_engine),
    runtime_context_service: RuntimeContextService = Depends(get_runtime_context_service),
) -> StrategyEvaluateResponse:
    context = await runtime_context_service.ensure_active_context()
    component_ids = request.component_keys or request.sleeve_ids or sorted(
        {component.component_key for binding in context.bindings for component in binding.component_configs}
    )
    evaluated = 0
    for sleeve_id in component_ids:
        results = await strategy_engine.evaluate_sleeve(
            sleeve_id,
            symbols=[symbol.upper() for symbol in request.symbols] if request.symbols else None,
        )
        evaluated += len(results)
    return StrategyEvaluateResponse(evaluated=evaluated, observed_at=datetime.now(UTC))


@v1.get("/strategy/status", response_model=StrategyFamilyStatusResponse, tags=["strategy"])
async def strategy_status(
    strategy_engine: StrategyEngine = Depends(get_strategy_engine),
) -> StrategyFamilyStatusResponse:
    status = await strategy_engine.get_family_status()
    return StrategyFamilyStatusResponse(**asdict(status))


@v1.get("/strategy/signals", response_model=list[StrategySignalResponse], tags=["strategy"])
async def latest_strategy_signals(
    sleeve_id: str | None = None,
    component_key: str | None = None,
    limit: int = 100,
    strategy_engine: StrategyEngine = Depends(get_strategy_engine),
) -> list[StrategySignalResponse]:
    signals = await strategy_engine.recent_signals(sleeve_id=component_key or sleeve_id, limit=limit)
    return [StrategySignalResponse(**asdict(signal)) for signal in signals]


@v1.get("/strategy/decisions", response_model=list[StrategyDecisionResponse], tags=["strategy"])
async def latest_strategy_decisions(
    sleeve_id: str | None = None,
    component_key: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
    strategy_engine: StrategyEngine = Depends(get_strategy_engine),
) -> list[StrategyDecisionResponse]:
    decisions = await strategy_engine.recent_decisions(
        sleeve_id=component_key or sleeve_id,
        symbol=symbol.upper() if symbol is not None else None,
        limit=limit,
    )
    return [
        StrategyDecisionResponse(
            decision_id=decision.decision_id,
            evaluation_key=decision.evaluation_key,
            family=decision.family,
            sleeve_id=decision.sleeve_id,
            component_key=decision.component_key,
            client_ref_id=decision.client_ref_id,
            strategy_mandate_ref_id=decision.strategy_mandate_ref_id,
            mandate_key=decision.mandate_key,
            mandate_account_binding_ref_id=decision.mandate_account_binding_ref_id,
            binding_key=decision.binding_key,
            venue_account_ref_id=decision.venue_account_ref_id,
            instrument_key=decision.instrument_key,
            instrument_ref_id=decision.instrument_ref_id,
            signal_id=decision.signal_id,
            symbol=decision.symbol,
            action=decision.action,
            status=decision.status,
            reason_code=decision.reason_code,
            confidence=float(decision.confidence) if decision.confidence is not None else None,
            rationale=decision.rationale,
            provenance=decision.provenance,
            features=decision.features,
            decided_at=decision.decided_at,
        )
        for decision in decisions
    ]


@v1.get(
    "/planning/source-policy",
    response_model=MandateMarketDataSourcePolicyResponse,
    tags=["planning"],
)
async def planning_source_policy(
    mandate_key: str | None = None,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> MandateMarketDataSourcePolicyResponse:
    policy = await planning_service.get_market_data_source_policy(mandate_key=mandate_key)
    return _source_policy_response(policy)


@v1.get(
    "/planning/decision-convertibility/{decision_id}",
    response_model=DesiredTradeConvertibilityResponse,
    tags=["planning"],
)
async def planning_decision_convertibility(
    decision_id: str,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> DesiredTradeConvertibilityResponse:
    assessment = await planning_service.inspect_decision_convertibility(decision_id)
    return _convertibility_response(assessment)


@v1.get(
    "/planning/desired-trades",
    response_model=list[MandateDesiredTradeResponse],
    tags=["planning"],
)
async def list_mandate_desired_trades(
    mandate_key: str | None = None,
    component_key: str | None = None,
    status: MandateDesiredTradeStatus | None = None,
    limit: int = 100,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> list[MandateDesiredTradeResponse]:
    trades = await planning_service.list_desired_trades(
        mandate_key=mandate_key,
        component_key=component_key,
        status=status,
        limit=limit,
    )
    return [_desired_trade_response(item) for item in trades]


@v1.post(
    "/planning/desired-trades/from-decision/{decision_id}",
    response_model=MandateDesiredTradeResponse,
    tags=["planning"],
    dependencies=[Depends(require_operator)],
)
async def preview_mandate_desired_trade_from_decision(
    decision_id: str,
    persist: bool = False,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> MandateDesiredTradeResponse:
    try:
        trade = await planning_service.preview_desired_trade_from_decision(decision_id, persist=persist)
    except DesiredTradeConversionError as exc:
        raise HTTPException(status_code=409, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _desired_trade_response(trade)


@v1.get(
    "/planning/routing-candidates",
    response_model=list[BindingRoutingCandidateResponse],
    tags=["planning"],
)
async def planning_routing_candidates(
    symbol: str | None = None,
    instrument_key: str | None = None,
    component_key: str | None = None,
    mandate_key: str | None = None,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> list[BindingRoutingCandidateResponse]:
    try:
        candidates = await planning_service.list_routing_candidates(
            symbol=symbol.upper() if symbol is not None else None,
            instrument_key=instrument_key,
            component_key=component_key,
            mandate_key=mandate_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_routing_candidate_response(item) for item in candidates]


@v1.post(
    "/routing-assessments/from-desired-trade",
    response_model=RoutingAssessmentResponse,
    tags=["routing-assessments"],
    dependencies=[Depends(require_operator)],
)
async def create_routing_assessment_from_desired_trade(
    request: RoutingAssessmentFromDesiredTradeRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAssessmentResponse:
    try:
        assessment = await routing_service.create_assessment_from_desired_trade(request.desired_trade_key)
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=409, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_assessment_response(assessment)


@v1.get(
    "/routing-assessments/{assessment_id}",
    response_model=RoutingAssessmentResponse,
    tags=["routing-assessments"],
)
async def get_routing_assessment(
    assessment_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAssessmentResponse:
    try:
        assessment = await routing_service.get_routing_assessment(assessment_id)
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_assessment_response(assessment)


@v1.post(
    "/route-readiness-audits/from-desired-trade",
    response_model=RouteReadinessAuditResponse,
    tags=["route-readiness-audits"],
    dependencies=[Depends(require_operator)],
)
async def create_route_readiness_audit_from_desired_trade(
    request: RouteReadinessAuditFromDesiredTradeRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RouteReadinessAuditResponse:
    try:
        audit = await routing_service.create_route_readiness_audit_from_desired_trade(
            request.desired_trade_key
        )
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=409, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _route_readiness_audit_response(audit)


@v1.post(
    "/route-readiness-audits/from-assessment",
    response_model=RouteReadinessAuditResponse,
    tags=["route-readiness-audits"],
    dependencies=[Depends(require_operator)],
)
async def create_route_readiness_audit_from_assessment(
    request: RouteReadinessAuditFromAssessmentRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RouteReadinessAuditResponse:
    try:
        audit = await routing_service.create_route_readiness_audit_from_assessment(
            request.routing_assessment_id
        )
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _route_readiness_audit_response(audit)


@v1.get(
    "/route-readiness-audits/{route_readiness_audit_id}",
    response_model=RouteReadinessAuditResponse,
    tags=["route-readiness-audits"],
)
async def get_route_readiness_audit(
    route_readiness_audit_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RouteReadinessAuditResponse:
    try:
        audit = await routing_service.get_route_readiness_audit(route_readiness_audit_id)
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _route_readiness_audit_response(audit)


@v1.post(
    "/routing-target-recommendations/from-route-readiness-audit",
    response_model=RoutingTargetRecommendationResponse,
    tags=["routing-target-recommendations"],
    dependencies=[Depends(require_operator)],
)
async def create_routing_target_recommendation_from_route_readiness_audit(
    request: RoutingTargetRecommendationFromRouteReadinessAuditRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetRecommendationResponse:
    try:
        recommendation = (
            await routing_service.create_routing_target_recommendation_from_route_readiness_audit(
                request.route_readiness_audit_id,
                policy_name=request.policy_name,
            )
        )
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_target_recommendation_response(recommendation)


@v1.get(
    "/routing-target-recommendations/{routing_target_recommendation_id}",
    response_model=RoutingTargetRecommendationResponse,
    tags=["routing-target-recommendations"],
)
async def get_routing_target_recommendation(
    routing_target_recommendation_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetRecommendationResponse:
    try:
        recommendation = await routing_service.get_routing_target_recommendation(
            routing_target_recommendation_id
        )
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_target_recommendation_response(recommendation)


@v1.post(
    "/routing-target-recommendations/{routing_target_recommendation_id}/accept",
    response_model=RoutingTargetChoiceResponse,
    tags=["routing-target-recommendations"],
    dependencies=[Depends(require_operator)],
)
async def accept_routing_target_recommendation(
    routing_target_recommendation_id: str,
    request: RoutingTargetRecommendationAcceptRequest | None = None,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetChoiceResponse:
    try:
        choice = await routing_service.accept_routing_target_recommendation_to_target_choice(
            routing_target_recommendation_id,
            approval_note=request.approval_note if request is not None else None,
            requested_by=request.requested_by if request is not None else None,
        )
    except RoutingAssessmentError as exc:
        status_code = 404 if exc.reason_code == "routing_target_recommendation_not_found" else 409
        raise HTTPException(status_code=status_code, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_target_choice_response(choice)


@v1.post(
    "/routing-target-choices/from-assessment",
    response_model=RoutingTargetChoiceResponse,
    tags=["routing-target-choices"],
    dependencies=[Depends(require_operator)],
)
async def create_routing_target_choice_from_assessment(
    request: RoutingTargetChoiceFromAssessmentRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetChoiceResponse:
    choice = await routing_service.record_target_choice_from_assessment(
        routing_assessment_id=request.routing_assessment_id,
        binding_ref_id=request.binding_ref_id,
        binding_key=request.binding_key,
        approval_note=request.approval_note,
        requested_by=request.requested_by,
    )
    return _routing_target_choice_response(choice)


@v1.get(
    "/routing-target-choices/{target_choice_id}",
    response_model=RoutingTargetChoiceResponse,
    tags=["routing-target-choices"],
)
async def get_routing_target_choice(
    target_choice_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetChoiceResponse:
    try:
        choice = await routing_service.get_routing_target_choice(target_choice_id)
    except RoutingAssessmentError as exc:
        raise HTTPException(status_code=404, detail={"reason_code": exc.reason_code, "message": str(exc)}) from exc
    return _routing_target_choice_response(choice)


@v1.post(
    "/routing-target-choices/{target_choice_id}/convert-to-child-intent",
    response_model=RoutingTargetChoiceConversionResponse,
    tags=["routing-target-choices"],
    dependencies=[Depends(require_operator)],
)
async def convert_routing_target_choice_to_child_intent(
    target_choice_id: str,
    request: RoutingTargetChoiceConversionRequest | None = None,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingTargetChoiceConversionResponse:
    order_shape_policy = None
    if request is not None and request.routed_order_shape_policy is not None:
        policy_request = request.routed_order_shape_policy
        order_shape_policy = RoutedOrderShapePolicyInput(
            order_type=policy_request.order_type,
            limit_price=policy_request.limit_price,
            reduce_only=policy_request.reduce_only,
            policy_source=policy_request.policy_source,
            requested_by=policy_request.requested_by,
        )
    result = await routing_service.convert_target_choice_to_child_intent(
        target_choice_id,
        order_shape_policy,
    )
    return _routing_target_choice_conversion_response(result)


@v1.get(
    "/routing-assessments/{assessment_id}/target-choices",
    response_model=list[RoutingTargetChoiceResponse],
    tags=["routing-target-choices"],
)
async def list_routing_target_choices_for_assessment(
    assessment_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> list[RoutingTargetChoiceResponse]:
    choices = await routing_service.list_routing_target_choices_for_assessment(assessment_id)
    return [_routing_target_choice_response(choice) for choice in choices]


@v1.get(
    "/routed-workflows/by-desired-trade/{desired_trade_key}",
    response_model=RoutedWorkflowInspectionResponse,
    tags=["routed-workflows"],
)
async def routed_workflow_by_desired_trade(
    desired_trade_key: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutedWorkflowInspectionResponse:
    inspection = await routing_service.inspect_routed_workflow_by_desired_trade(
        desired_trade_key
    )
    return RoutedWorkflowInspectionResponse(**inspection)


@v1.get(
    "/operator-routed-workflows/by-desired-trade/{desired_trade_key}",
    response_model=RoutedWorkflowOperatorSummaryResponse,
    tags=["operator-observability"],
)
async def operator_routed_workflow_summary_by_desired_trade(
    desired_trade_key: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutedWorkflowOperatorSummaryResponse:
    summary = await routing_service.inspect_routed_workflow_operator_summary_by_desired_trade(
        desired_trade_key
    )
    return RoutedWorkflowOperatorSummaryResponse(**summary)


def _routing_automation_policy_from_request(
    routing_service: RoutingAssessmentService,
    request: RoutingAutomationPolicyRequest | None,
) -> RoutingAutomationPolicy | None:
    if request is None:
        return None
    if not hasattr(routing_service, "routing_automation_policy"):
        raise HTTPException(
            status_code=500,
            detail="Routing service does not expose automation policy inspection.",
        )
    return routing_service.routing_automation_policy(
        mode=request.mode,
        policy_name=request.policy_name,
        allow_recommendation_acceptance=request.allow_recommendation_acceptance,
        allow_target_choice_conversion=request.allow_target_choice_conversion,
        allow_preview_readiness=request.allow_preview_readiness,
        allow_submit=request.allow_submit,
    )


@v1.get(
    "/routing-automation/policy",
    response_model=RoutingAutomationPolicyResponse,
    tags=["routing-automation"],
)
async def routing_automation_policy(
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationPolicyResponse:
    policy = await routing_service.inspect_routing_automation_policy()
    return RoutingAutomationPolicyResponse(**asdict(policy))


@v1.post(
    "/routing-automation/plans/by-desired-trade/{desired_trade_key}",
    response_model=RoutingAutomationPlanResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_operator)],
)
async def routing_automation_plan_by_desired_trade(
    desired_trade_key: str,
    request: RoutingAutomationPlanRequest | None = None,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationPlanResponse:
    policy = _routing_automation_policy_from_request(
        routing_service,
        request.policy if request is not None else None,
    )
    plan = await routing_service.plan_routing_automation_for_desired_trade(
        desired_trade_key,
        policy=policy,
        dry_run=True if request is None else request.dry_run,
    )
    return RoutingAutomationPlanResponse(**asdict(plan))


@v1.post(
    "/routing-automation/approvals",
    response_model=RoutingAutomationApprovalResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_operator)],
)
async def create_routing_automation_approval(
    request: RoutingAutomationApprovalCreateRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationApprovalResponse:
    policy = _routing_automation_policy_from_request(routing_service, request.policy)
    try:
        approval = await routing_service.create_routing_automation_approval(
            request.desired_trade_key,
            action_name=request.action_name.value,
            approved_by=request.approved_by,
            policy=policy,
            notes=request.notes,
            expires_at=request.expires_at,
        )
    except RoutingAssessmentError as exc:
        status_code = (
            404
            if exc.reason_code
            in {
                "routing_automation_approval_desired_trade_not_found",
                "routing_automation_approval_not_found",
            }
            else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationApprovalResponse(**asdict(approval))


@v1.get(
    "/routing-automation/approvals/{approval_id}",
    response_model=RoutingAutomationApprovalResponse,
    tags=["routing-automation"],
)
async def get_routing_automation_approval(
    approval_id: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationApprovalResponse:
    try:
        approval = await routing_service.get_routing_automation_approval(approval_id)
    except RoutingAssessmentError as exc:
        raise HTTPException(
            status_code=404,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationApprovalResponse(**asdict(approval))


@v1.get(
    "/routing-automation/approvals/by-desired-trade/{desired_trade_key}",
    response_model=RoutingAutomationApprovalInspectionResponse,
    tags=["routing-automation"],
)
async def routing_automation_approval_inspection_by_desired_trade(
    desired_trade_key: str,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationApprovalInspectionResponse:
    inspection = await routing_service.inspect_routing_automation_approvals_for_desired_trade(
        desired_trade_key
    )
    return RoutingAutomationApprovalInspectionResponse(**asdict(inspection))


@v1.post(
    "/routing-automation/approvals/{approval_id}/revoke",
    response_model=RoutingAutomationApprovalResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_operator)],
)
async def revoke_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationApprovalStateChangeRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationApprovalResponse:
    try:
        approval = await routing_service.revoke_routing_automation_approval(
            approval_id,
            revoked_by=request.actor,
            reason=request.reason,
        )
    except RoutingAssessmentError as exc:
        status_code = 404 if exc.reason_code == "routing_automation_approval_not_found" else 409
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationApprovalResponse(**asdict(approval))


@v1.post(
    "/routing-automation/approvals/{approval_id}/accept-recommendation",
    response_model=RoutingAutomationRecommendationAcceptanceResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_automation_admin)],
)
async def accept_recommendation_with_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationRecommendationAcceptanceRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationRecommendationAcceptanceResponse:
    policy = _routing_automation_policy_from_request(routing_service, request.policy)
    try:
        result = await routing_service.accept_routing_target_recommendation_with_approval(
            request.routing_target_recommendation_id,
            approval_id=approval_id,
            consumed_by=request.actor,
            approval_note=request.approval_note,
            policy=policy,
        )
    except RoutingAssessmentError as exc:
        status_code = (
            404
            if exc.reason_code
            in {
                "routing_automation_approval_not_found",
                "routing_target_recommendation_not_found",
            }
            else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationRecommendationAcceptanceResponse(
        approval_id=result.approval_id,
        routing_target_recommendation_id=result.routing_target_recommendation_id,
        target_choice_id=result.target_choice_id,
        desired_trade_key=result.desired_trade_key,
        environment=result.environment,
        approval=RoutingAutomationApprovalResponse(**asdict(result.approval)),
        target_choice=_routing_target_choice_response(result.target_choice),
        approval_consumed=result.approval_consumed,
        target_choice_created_or_reused=result.target_choice_created_or_reused,
        child_intent_created=result.child_intent_created,
        prepared_order_created=result.prepared_order_created,
        readiness_assessment_created=result.readiness_assessment_created,
        submitted_order_created=result.submitted_order_created,
        reason_codes=list(result.reason_codes),
        boundary_flags=dict(result.boundary_flags),
        provenance=dict(result.provenance),
    )


@v1.post(
    "/routing-automation/approvals/{approval_id}/convert-target-choice",
    response_model=RoutingAutomationTargetChoiceConversionResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_automation_admin)],
)
async def convert_target_choice_with_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationTargetChoiceConversionRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationTargetChoiceConversionResponse:
    policy = _routing_automation_policy_from_request(routing_service, request.policy)
    try:
        result = await routing_service.convert_target_choice_to_child_intent_with_approval(
            request.target_choice_id,
            approval_id=approval_id,
            consumed_by=request.actor,
            policy=policy,
        )
    except RoutingAssessmentError as exc:
        status_code = (
            404
            if exc.reason_code
            in {
                "routing_automation_approval_not_found",
                "routing_target_choice_not_found",
            }
            else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationTargetChoiceConversionResponse(
        approval_id=result.approval_id,
        target_choice_id=result.target_choice_id,
        intent_id=result.intent_id,
        desired_trade_key=result.desired_trade_key,
        environment=result.environment,
        approval=RoutingAutomationApprovalResponse(**asdict(result.approval)),
        conversion=_routing_target_choice_conversion_response(result.conversion),
        approval_consumed=result.approval_consumed,
        child_intent_created_or_reused=result.child_intent_created_or_reused,
        prepared_order_created=result.prepared_order_created,
        readiness_assessment_created=result.readiness_assessment_created,
        submitted_order_created=result.submitted_order_created,
        reason_codes=list(result.reason_codes),
        boundary_flags=dict(result.boundary_flags),
        provenance=dict(result.provenance),
    )


@v1.post(
    "/routing-automation/approvals/{approval_id}/preview-readiness",
    response_model=RoutingAutomationPreviewReadinessResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_automation_admin)],
)
async def preview_readiness_with_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationPreviewReadinessRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> RoutingAutomationPreviewReadinessResponse:
    policy = _routing_automation_policy_from_request(routing_service, request.policy)
    try:
        result = await routing_service.preview_and_assess_child_intent_readiness_with_approval(
            request.intent_id,
            approval_id=approval_id,
            consumed_by=request.actor,
            execution_service=execution_service,
            policy=policy,
        )
    except RoutingAssessmentError as exc:
        status_code = (
            404
            if exc.reason_code
            in {
                "routing_automation_approval_not_found",
                "order_intent_not_found",
            }
            else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationPreviewReadinessResponse(
        approval_id=result.approval_id,
        intent_id=result.intent_id,
        desired_trade_key=result.desired_trade_key,
        environment=result.environment,
        approval=RoutingAutomationApprovalResponse(**asdict(result.approval)),
        prepared_order_preview=_prepared_venue_order_response(result.prepared_order_preview),
        readiness=_execution_readiness_response(result.readiness),
        prepared_order_preview_key=result.prepared_order_preview_key,
        readiness_evaluation_id=result.readiness_evaluation_id,
        approval_consumed=result.approval_consumed,
        prepared_order_preview_created_or_reused=(
            result.prepared_order_preview_created_or_reused
        ),
        readiness_assessment_created_or_reused=(
            result.readiness_assessment_created_or_reused
        ),
        readiness_assessment_created=result.readiness_assessment_created,
        readiness_assessment_reused=result.readiness_assessment_reused,
        submitted_order_created=result.submitted_order_created,
        exchange_submit_called=result.exchange_submit_called,
        auto_submit=result.auto_submit,
        route_executor_used=result.route_executor_used,
        reason_codes=list(result.reason_codes),
        boundary_flags=dict(result.boundary_flags),
        provenance=dict(result.provenance),
    )


@v1.post(
    "/routing-automation/approvals/{approval_id}/submit",
    response_model=RoutingAutomationSubmittedOrderHandoffResponse,
    tags=["routing-automation"],
    dependencies=[Depends(require_admin)],
)
async def submit_child_intent_with_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationSubmittedOrderHandoffRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> RoutingAutomationSubmittedOrderHandoffResponse:
    policy = _routing_automation_policy_from_request(routing_service, request.policy)
    try:
        result = await routing_service.submit_child_intent_with_approval(
            request.intent_id,
            approval_id=approval_id,
            consumed_by=request.actor,
            execution_service=execution_service,
            policy=policy,
        )
    except RoutingAssessmentError as exc:
        status_code = (
            404
            if exc.reason_code
            in {
                "routing_automation_approval_not_found",
                "order_intent_not_found",
                "submitted_order_not_found",
            }
            else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    except SubmissionBlockedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "intent_id": exc.intent_id,
                "outcome": exc.readiness.outcome.value,
                "reason_codes": list(exc.readiness.reason_codes),
                "provenance": dict(exc.readiness.provenance),
            },
        ) from exc
    except SubmissionFailedError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "intent_id": exc.intent_id,
                "venue": exc.venue,
                "reason_codes": list(exc.reason_codes),
            },
        ) from exc
    return RoutingAutomationSubmittedOrderHandoffResponse(
        approval_id=result.approval_id,
        intent_id=result.intent_id,
        desired_trade_key=result.desired_trade_key,
        environment=result.environment,
        approval=RoutingAutomationApprovalResponse(**asdict(result.approval)),
        submitted_order=_submitted_order_response(result.submitted_order),
        submitted_order_id=result.submitted_order_id,
        readiness_evaluation_id=result.readiness_evaluation_id,
        approval_consumed=result.approval_consumed,
        submitted_order_created_or_reused=result.submitted_order_created_or_reused,
        submitted_order_created=result.submitted_order_created,
        submitted_order_reused=result.submitted_order_reused,
        exchange_submit_called=result.exchange_submit_called,
        auto_submit=result.auto_submit,
        route_executor_used=result.route_executor_used,
        reason_codes=list(result.reason_codes),
        boundary_flags=dict(result.boundary_flags),
        provenance=dict(result.provenance),
    )


@v1.post(
    "/routing-automation/approvals/{approval_id}/consume",
    response_model=RoutingAutomationApprovalResponse,
    dependencies=[Depends(require_automation_admin)],
    description=(
        "Administrative approval-state transition only. This marks an approval consumed "
        "without executing the approved action; stage-specific action endpoints perform "
        "bounded action execution."
    ),
    tags=["routing-automation"],
)
async def consume_routing_automation_approval(
    approval_id: str,
    request: RoutingAutomationApprovalStateChangeRequest,
    routing_service: RoutingAssessmentService = Depends(get_routing_assessment_service),
) -> RoutingAutomationApprovalResponse:
    try:
        approval = await routing_service.consume_routing_automation_approval(
            approval_id,
            consumed_by=request.actor,
            reason=request.reason,
        )
    except RoutingAssessmentError as exc:
        status_code = 404 if exc.reason_code == "routing_automation_approval_not_found" else 409
        raise HTTPException(
            status_code=status_code,
            detail={"reason_code": exc.reason_code, "message": str(exc)},
        ) from exc
    return RoutingAutomationApprovalResponse(**asdict(approval))


@v1.get(
    "/planning/quotes",
    response_model=list[BindingQuoteSnapshotResponse],
    tags=["planning"],
)
async def planning_quotes(
    symbol: str | None = None,
    instrument_key: str | None = None,
    component_key: str | None = None,
    mandate_key: str | None = None,
    planning_service: MandateTradePlanningService = Depends(get_trade_planning_service),
) -> list[BindingQuoteSnapshotResponse]:
    try:
        quotes = await planning_service.list_binding_quotes(
            symbol=symbol.upper() if symbol is not None else None,
            instrument_key=instrument_key,
            component_key=component_key,
            mandate_key=mandate_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_binding_quote_response(item) for item in quotes]


@v1.get("/child-intents", response_model=list[OrderIntentResponse], tags=["execution"])
async def list_child_intents(
    desired_trade_key: str | None = None,
    binding_key: str | None = None,
    limit: int = 100,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[OrderIntentResponse]:
    intents = await execution_service.list_child_intents(
        desired_trade_key=desired_trade_key,
        binding_key=binding_key,
        limit=limit,
    )
    return [_order_intent_response(item) for item in intents]


@v1.post(
    "/child-intents/{intent_id}/submit",
    response_model=SubmittedOrderResponse,
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def submit_child_intent(
    intent_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderResponse:
    try:
        intent = await execution_service.get_child_intent(intent_id)
        submitted = await execution_service.submit_prepared_intent(intent)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SubmissionBlockedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "intent_id": exc.intent_id,
                "outcome": exc.readiness.outcome.value,
                "reason_codes": list(exc.readiness.reason_codes),
            },
        ) from exc
    except SubmissionFailedError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "intent_id": exc.intent_id,
                "venue": exc.venue,
                "reason_codes": list(exc.reason_codes),
            },
        ) from exc
    return _submitted_order_response(submitted)


@v1.get(
    "/child-intents/{intent_id}/prepared-order-preview",
    response_model=PreparedVenueOrderResponse,
    tags=["execution"],
    dependencies=[Depends(require_operator)],
)
async def preview_child_intent(
    intent_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> PreparedVenueOrderResponse:
    try:
        preview = await execution_service.preview_child_intent(intent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _prepared_venue_order_response(preview)


@v1.get(
    "/child-intents/{intent_id}/submission-readiness",
    response_model=ExecutionReadinessAssessmentResponse,
    tags=["execution"],
    dependencies=[Depends(require_operator)],
)
async def child_intent_submission_readiness(
    intent_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> ExecutionReadinessAssessmentResponse:
    try:
        assessment = await execution_service.assess_child_intent_readiness(intent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _execution_readiness_response(assessment)


@v1.get(
    "/execution-readiness",
    response_model=list[ExecutionReadinessAssessmentResponse],
    tags=["execution"],
)
async def execution_readiness_evaluations(
    intent_id: str | None = None,
    outcome: ExecutionReadinessOutcome | None = None,
    limit: int = 100,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[ExecutionReadinessAssessmentResponse]:
    assessments = await execution_service.list_readiness_assessments(
        intent_id=intent_id,
        outcome=outcome,
        limit=limit,
    )
    return [_execution_readiness_response(item) for item in assessments]


@v1.get(
    "/submitted-orders",
    response_model=list[SubmittedOrderResponse],
    tags=["execution"],
)
async def submitted_orders(
    intent_id: str | None = None,
    binding_key: str | None = None,
    venue_account_ref_id: str | None = None,
    venue: str | None = None,
    limit: int = 100,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[SubmittedOrderResponse]:
    orders = await execution_service.list_submitted_orders(
        intent_id=intent_id,
        binding_key=binding_key,
        venue_account_ref_id=venue_account_ref_id,
        venue=venue,
        limit=limit,
    )
    return [_submitted_order_response(item) for item in orders]


@v1.get(
    "/submitted-orders/{submitted_order_id}",
    response_model=SubmittedOrderResponse,
    tags=["execution"],
)
async def submitted_order_detail(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderResponse:
    try:
        order = await execution_service.get_submitted_order(submitted_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _submitted_order_response(order)


@v1.get(
    "/submitted-orders/{submitted_order_id}/recovery",
    response_model=SubmittedOrderRecoveryRecommendationResponse,
    tags=["execution"],
)
async def submitted_order_recovery(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderRecoveryRecommendationResponse:
    try:
        recommendation = await execution_service.get_submitted_order_recovery_recommendation(
            submitted_order_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _submitted_order_recovery_response(recommendation)


@v1.get(
    "/submitted-orders/{submitted_order_id}/actionability",
    response_model=SubmittedOrderActionabilityResponse,
    tags=["execution"],
)
async def submitted_order_actionability(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderActionabilityResponse:
    try:
        actionability = await execution_service.get_submitted_order_actionability(submitted_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _submitted_order_actionability_response(actionability)


@v1.post(
    "/submitted-orders/{submitted_order_id}/reconcile",
    response_model=SubmittedOrderResponse,
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def reconcile_submitted_order(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderResponse:
    try:
        order = await execution_service.reconcile_submitted_order(submitted_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _submitted_order_response(order)


@v1.post(
    "/submitted-orders/{submitted_order_id}/cancel",
    response_model=SubmittedOrderResponse,
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def cancel_submitted_order(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderResponse:
    try:
        order = await execution_service.cancel_submitted_order(submitted_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SubmittedOrderActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _submitted_order_response(order)


@v1.post(
    "/submitted-orders/{submitted_order_id}/amend",
    response_model=SubmittedOrderResponse,
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def amend_submitted_order(
    submitted_order_id: str,
    request: SubmittedOrderAmendRequest,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderResponse:
    try:
        order = await execution_service.amend_submitted_order(
            submitted_order_id,
            new_quantity=(
                Decimal(str(request.quantity)) if request.quantity is not None else None
            ),
            new_limit_price=(
                Decimal(str(request.limit_price)) if request.limit_price is not None else None
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SubmittedOrderActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _submitted_order_response(order)


@v1.post(
    "/submitted-orders/{submitted_order_id}/recovery/execute",
    response_model=SubmittedOrderRecoveryExecutionResponse,
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def execute_submitted_order_recovery(
    submitted_order_id: str,
    request: SubmittedOrderRecoveryExecutionRequest,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> SubmittedOrderRecoveryExecutionResponse:
    try:
        result = await execution_service.execute_submitted_order_recovery(
            submitted_order_id,
            action=request.action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SubmittedOrderActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _submitted_order_recovery_execution_response(result)


@v1.get(
    "/submitted-orders/{submitted_order_id}/fills",
    response_model=list[FillResponse],
    tags=["execution"],
    dependencies=[Depends(require_admin)],
)
async def submitted_order_fills(
    submitted_order_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[FillResponse]:
    try:
        fills = await execution_service.reconcile_fills(submitted_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [_fill_response(item) for item in fills]


@v1.get(
    "/submitted-orders/{submitted_order_id}/events",
    response_model=list[SubmittedOrderLifecycleEventResponse],
    tags=["execution"],
)
async def submitted_order_events(
    submitted_order_id: str,
    limit: int = 100,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[SubmittedOrderLifecycleEventResponse]:
    events = await execution_service.list_submitted_order_events(
        submitted_order_id=submitted_order_id,
        limit=limit,
    )
    return [_submitted_order_event_response(item) for item in events]


@v1.get(
    "/portfolio/bootstrap-summary",
    response_model=PortfolioBootstrapSummaryResponse,
    tags=["portfolio"],
    dependencies=[Depends(require_admin)],
)
async def portfolio_bootstrap_summary(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioBootstrapSummaryResponse:
    summary = await portfolio_service.get_bootstrap_summary()
    return PortfolioBootstrapSummaryResponse(
        client_key=summary.client_key,
        mandate_key=summary.mandate_key,
        venue=summary.venue,
        environment=summary.environment,
        has_account_snapshot=summary.account_snapshot is not None,
        bound_accounts=summary.bound_accounts,
        open_positions=summary.open_positions,
        recent_fills=summary.recent_fills,
        open_orders=summary.open_orders,
        recent_submitted_orders=summary.recent_submitted_orders,
        unattributed_positions=summary.unattributed_positions,
        gross_exposure=float(summary.gross_exposure),
        net_exposure=float(summary.net_exposure),
        account_equity=(
            float(summary.account_snapshot.equity) if summary.account_snapshot is not None else None
        ),
    )


router.include_router(v1)
