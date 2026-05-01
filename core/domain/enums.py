"""Domain enumerations shared across services."""

from enum import StrEnum


class Environment(StrEnum):
    DEV = "dev"
    BACKTEST = "backtest"
    PAPER = "paper"
    TESTNET = "testnet"
    LIVE = "live"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class Venue(StrEnum):
    HYPERLIQUID = "hyperliquid"
    ASTER = "aster"
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"
    COINBASE = "coinbase"
    COINBASE_ADVANCED_TRADE = "coinbase_advanced_trade"
    KRAKEN = "kraken"


class MarketType(StrEnum):
    SPOT = "spot"
    PERPETUAL = "perpetual"
    FUTURE = "future"
    OPTION = "option"


class ProductType(StrEnum):
    LINEAR = "linear"
    INVERSE = "inverse"
    SPOT = "spot"


class AttributionStatus(StrEnum):
    UNASSIGNED = "unassigned"
    PARTIAL = "partial"
    FULLY_ATTRIBUTED = "fully_attributed"


class SignalType(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"
    REBALANCE = "rebalance"
    RISK_REDUCTION = "risk_reduction"
    NO_TRADE = "no_trade"


class DecisionAction(StrEnum):
    NOOP = "noop"
    HOLD = "hold"
    OPEN = "open"
    ADD = "add"
    REDUCE = "reduce"
    CLOSE = "close"


class StrategyDecisionStatus(StrEnum):
    PROPOSED = "proposed"
    NO_TRADE = "no_trade"
    INVALID = "invalid"


class StrategyFamily(StrEnum):
    MONEY_FLOW = "money_flow"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderIntentStatus(StrEnum):
    PENDING_RISK = "pending_risk"
    PREPARED = "prepared"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    SUBMISSION_FAILED = "submission_failed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VenueSupportLevel(StrEnum):
    QA_READ_ONLY = "qa_read_only"
    EXECUTION_PREPARABLE = "execution_preparable"
    LIVE_ENABLED = "live_enabled"


class VenueOrderPreviewStatus(StrEnum):
    PREPARABLE = "preparable"
    REJECTED = "rejected"


class ExecutionReadinessOutcome(StrEnum):
    INELIGIBLE = "ineligible"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    BLOCKED_BY_VENUE = "blocked_by_venue"
    BLOCKED_BY_ADAPTER = "blocked_by_adapter"
    BLOCKED_BY_ENVIRONMENT = "blocked_by_environment"
    PHASE_BLOCKED = "phase_blocked"
    ELIGIBLE_FOR_SUBMISSION = "eligible_for_submission"


class MandateDesiredTradeStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROUTING_REQUIRED = "routing_required"
    ROUTING_PENDING = "routing_pending"
    ROUTED = "routed"
    CANCELED = "canceled"


class RoutingAssessmentDecisionStatus(StrEnum):
    ASSESSMENT_ONLY = "assessment_only"
    NO_ELIGIBLE_BINDINGS = "no_eligible_bindings"
    INSUFFICIENT_DATA = "insufficient_data"


class RoutingCandidateEligibilityStatus(StrEnum):
    ELIGIBLE_FOR_FUTURE_SELECTION = "eligible_for_future_selection"
    INELIGIBLE_FOR_FUTURE_SELECTION = "ineligible_for_future_selection"


class RouteReadinessAuditStatus(StrEnum):
    READY_FOR_RECOMMENDATION = "ready_for_recommendation"
    BLOCKED = "blocked"
    INSUFFICIENT_DATA = "insufficient_data"
    STALE_DATA = "stale_data"
    POLICY_BLOCKED = "policy_blocked"
    UNSUPPORTED = "unsupported"


class RoutingTargetRecommendationStatus(StrEnum):
    RECOMMENDED_SINGLE_READY_CANDIDATE = "recommended_single_ready_candidate"
    BLOCKED_AUDIT_NOT_FOUND = "blocked_audit_not_found"
    BLOCKED_AUDIT_NOT_READY = "blocked_audit_not_ready"
    BLOCKED_NO_READY_CANDIDATE = "blocked_no_ready_candidate"
    BLOCKED_MULTIPLE_READY_CANDIDATES = "blocked_multiple_ready_candidates"
    BLOCKED_STALE_AUDIT = "blocked_stale_audit"
    BLOCKED_STALE_DESIRED_TRADE = "blocked_stale_desired_trade"
    BLOCKED_STALE_CANDIDATE = "blocked_stale_candidate"
    BLOCKED_INVALID_AUDIT = "blocked_invalid_audit"


class RoutingTargetChoiceStatus(StrEnum):
    TARGET_CHOICE_RECORDED = "target_choice_recorded"
    BLOCKED_NO_ELIGIBLE_BINDING = "blocked_no_eligible_binding"
    BLOCKED_CANDIDATE_INELIGIBLE = "blocked_candidate_ineligible"
    BLOCKED_ASSESSMENT_INSUFFICIENT_DATA = "blocked_assessment_insufficient_data"
    BLOCKED_ASSESSMENT_NOT_FOUND = "blocked_assessment_not_found"
    BLOCKED_CANDIDATE_NOT_FOUND = "blocked_candidate_not_found"
    BLOCKED_STALE_ASSESSMENT = "blocked_stale_assessment"


class RoutingTargetChoiceConversionStatus(StrEnum):
    CHILD_INTENT_CREATED = "child_intent_created"
    CHILD_INTENT_ALREADY_EXISTS = "child_intent_already_exists"
    BLOCKED_TARGET_CHOICE_NOT_FOUND = "blocked_target_choice_not_found"
    BLOCKED_TARGET_CHOICE_NOT_RECORDED = "blocked_target_choice_not_recorded"
    BLOCKED_TARGET_CHOICE_INCOMPLETE = "blocked_target_choice_incomplete"
    BLOCKED_ORDER_SHAPE_POLICY = "blocked_order_shape_policy"
    BLOCKED_ASSESSMENT_NOT_FOUND = "blocked_assessment_not_found"
    BLOCKED_ASSESSMENT_NOT_ASSESSMENT_ONLY = "blocked_assessment_not_assessment_only"
    BLOCKED_CANDIDATE_NOT_FOUND = "blocked_candidate_not_found"
    BLOCKED_CANDIDATE_INELIGIBLE = "blocked_candidate_ineligible"
    BLOCKED_CANDIDATE_MISMATCH = "blocked_candidate_mismatch"
    BLOCKED_STALE_DESIRED_TRADE = "blocked_stale_desired_trade"
    BLOCKED_STALE_TARGET = "blocked_stale_target"
    BLOCKED_INVALID_DESIRED_TRADE = "blocked_invalid_desired_trade"


class RoutingAutomationMode(StrEnum):
    DISABLED = "disabled"
    DRY_RUN_ONLY = "dry_run_only"
    APPROVAL_REQUIRED = "approval_required"
    EXPLICIT_AUTOMATION_PERMITTED = "explicit_automation_permitted"


class RoutingAutomationPlanOutcome(StrEnum):
    DISABLED = "disabled"
    DRY_RUN_ONLY = "dry_run_only"
    APPROVAL_REQUIRED = "approval_required"
    AUTOMATION_ELIGIBLE = "automation_eligible"
    MANUAL_REVIEW_ONLY = "manual_review_only"
    BLOCKED = "blocked"


class RoutingAutomationStepStatus(StrEnum):
    ALREADY_SATISFIED = "already_satisfied"
    DISABLED = "disabled"
    DRY_RUN_ONLY = "dry_run_only"
    APPROVAL_REQUIRED = "approval_required"
    AUTOMATION_ELIGIBLE = "automation_eligible"
    MANUAL_ONLY = "manual_only"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


class RoutingAutomationApprovalAction(StrEnum):
    RECOMMENDATION_ACCEPTANCE = "recommendation_acceptance"
    TARGET_CHOICE_CONVERSION = "target_choice_conversion"
    PREVIEW_READINESS = "prepared_order_preview_and_readiness"
    SUBMITTED_ORDER_HANDOFF = "submitted_order_handoff"


class RoutingAutomationApprovalStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    CONSUMED = "consumed"
    CONSUMPTION_PENDING = "consumption_pending"
    EXPIRED = "expired"
    STALE_LINEAGE = "stale_lineage"


class RiskEvaluationOutcome(StrEnum):
    APPROVED_DESIRED_TRADE = "approved_desired_trade"
    REJECTED_DESIRED_TRADE = "rejected_desired_trade"
    NO_DESIRED_TRADE = "no_desired_trade"
    ROUTING_REQUIRED = "routing_required"
    INVALID_INPUT = "invalid_input"


class TradeTargetScope(StrEnum):
    MANDATE = "mandate"
    BINDING = "binding"


class MarketDataSourceMode(StrEnum):
    SINGLE_VENUE = "single_venue"
    COMPOSITE = "composite"


class InstrumentResolutionMode(StrEnum):
    REQUIRE_INSTRUMENT_KEY = "require_instrument_key"
    CANONICAL_SYMBOL_IF_UNAMBIGUOUS = "canonical_symbol_if_unambiguous"


class SubmittedOrderStatus(StrEnum):
    NEW = "new"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    CANCEL_REQUESTED = "cancel_requested"
    CANCEL_ACKNOWLEDGED = "cancel_acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class SubmittedOrderReconciliationStatus(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    PENDING = "pending"
    RECONCILED = "reconciled"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class SubmittedOrderRecoveryCategory(StrEnum):
    NO_ACTION_REQUIRED = "no_action_required"
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    OPERATOR_ACTION_REQUIRED = "operator_action_required"
    VENUE_STATE_UNCERTAIN = "venue_state_uncertain"
    ACCOUNT_POLICY_BLOCK = "account_policy_block"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class RiskSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class SystemComponent(StrEnum):
    API = "api"
    EXCHANGE = "exchange"
    MARKET_DATA = "market_data"
    INDICATORS = "indicators"
    STRATEGY = "strategy"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    EXECUTION = "execution"
    ALERTS = "alerts"
    DATABASE = "database"


class StackingPolicy(StrEnum):
    NONE = "none"
    NET_LIMIT = "net_limit"
    STRICT_SINGLE_SLEEVE = "strict_single_sleeve"
