"""Persistence models for trading state and audit records."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

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
    RoutingCandidateEligibilityStatus,
    RoutingTargetRecommendationStatus,
    RoutingTargetChoiceStatus,
    SignalType,
    StrategyDecisionStatus,
    StrategyFamily,
    SubmittedOrderStatus,
    SubmittedOrderReconciliationStatus,
    SystemComponent,
    Timeframe,
    TradeTargetScope,
)
from db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def enum_column(enum_cls: type[object]) -> SAEnum:
    return SAEnum(
        enum_cls,
        values_callable=lambda members: [member.value for member in members],
        native_enum=True,
        validate_strings=True,
    )


class InstrumentModel(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        Index(
            "ix_instruments_market_product_base_quote_settlement",
            "market_type",
            "product_type",
            "base_asset",
            "quote_asset",
            "settlement_asset",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    instrument_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    canonical_symbol: Mapped[str] = mapped_column(String(64), index=True)
    market_type: Mapped[MarketType] = mapped_column(enum_column(MarketType), index=True)
    product_type: Mapped[ProductType] = mapped_column(enum_column(ProductType), index=True)
    base_asset: Mapped[str] = mapped_column(String(32), index=True)
    quote_asset: Mapped[str] = mapped_column(String(32), index=True)
    settlement_asset: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SymbolModel(Base):
    __tablename__ = "symbols"
    __table_args__ = (
        Index("ix_symbols_venue_symbol", "venue", "symbol"),
        Index(
            "ix_symbols_venue_market_identity",
            "venue",
            "symbol",
            "market_type",
            "product_type",
            "quote_asset",
            "settlement_asset",
            unique=True,
        ),
        Index("ix_symbols_venue_asset_id", "venue", "asset_id", unique=True),
        Index("ix_symbols_venue_exchange_symbol", "venue", "exchange_symbol", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    exchange_symbol: Mapped[str] = mapped_column(String(64), index=True)
    venue_asset_id: Mapped[str | None] = mapped_column(String(128))
    asset_id: Mapped[int | None] = mapped_column(Integer)
    market_type: Mapped[MarketType] = mapped_column(
        enum_column(MarketType), default=MarketType.PERPETUAL, index=True
    )
    product_type: Mapped[ProductType] = mapped_column(
        enum_column(ProductType), default=ProductType.LINEAR, index=True
    )
    base_asset: Mapped[str] = mapped_column(String(32))
    quote_asset: Mapped[str] = mapped_column(String(32))
    settlement_asset: Mapped[str | None] = mapped_column(String(32))
    price_tick_size: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    quantity_step_size: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    min_order_size: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    size_decimals: Mapped[int | None] = mapped_column(Integer)
    max_leverage: Mapped[int | None] = mapped_column(Integer)
    only_isolated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_perpetual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builder_deployed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_strategy_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_trading_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ClientModel(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    client_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class VenueAccountModel(Base):
    __tablename__ = "venue_accounts"
    __table_args__ = (
        Index("ix_venue_accounts_client_venue_environment", "client_ref_id", "venue", "environment"),
        Index(
            "ix_venue_accounts_venue_environment_address",
            "venue",
            "environment",
            "account_address",
            unique=False,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    venue_account_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    client_ref_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue_native_account_id: Mapped[str] = mapped_column(String(128), index=True)
    account_address: Mapped[str | None] = mapped_column(String(128), index=True)
    account_label: Mapped[str | None] = mapped_column(String(128))
    subaccount_label: Mapped[str | None] = mapped_column(String(128))
    credentials_ref: Mapped[str | None] = mapped_column(String(128))
    wallet_ref: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StrategyMandateModel(Base):
    """Logical strategy umbrella.

    A mandate can bind many venue accounts and becomes the future routing boundary
    for mandate-level desired trades.
    """

    __tablename__ = "strategy_mandates"
    __table_args__ = (
        Index("ix_strategy_mandates_client_family_enabled", "client_ref_id", "family", "enabled"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    mandate_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    client_ref_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    family: Mapped[StrategyFamily] = mapped_column(enum_column(StrategyFamily), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_builder_deployed_for_strategy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_builder_deployed_for_trading: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MandateMarketDataSourcePolicyModel(Base):
    __tablename__ = "mandate_market_data_source_policies"
    __table_args__ = (
        Index(
            "ix_mandate_market_data_source_policies_mandate_unique",
            "strategy_mandate_ref_id",
            unique=True,
        ),
        Index(
            "ix_mandate_market_data_source_policies_source_venue",
            "source_venue",
            "source_mode",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    strategy_mandate_ref_id: Mapped[str] = mapped_column(ForeignKey("strategy_mandates.id"), index=True)
    source_mode: Mapped[MarketDataSourceMode] = mapped_column(
        enum_column(MarketDataSourceMode),
        index=True,
    )
    source_venue: Mapped[str] = mapped_column(String(32))
    market_type: Mapped[MarketType | None] = mapped_column(enum_column(MarketType), index=True)
    product_type: Mapped[ProductType | None] = mapped_column(enum_column(ProductType), index=True)
    instrument_resolution_mode: Mapped[InstrumentResolutionMode] = mapped_column(
        enum_column(InstrumentResolutionMode),
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MandateAccountBindingModel(Base):
    """Per-account membership and policy within a mandate.

    Bindings define which venue accounts participate in a mandate and carry the
    account-specific eligibility hooks that a future router will use. They do not
    encode static routing weights.
    """

    __tablename__ = "mandate_account_bindings"
    __table_args__ = (
        Index(
            "ix_mandate_account_bindings_mandate_account",
            "strategy_mandate_ref_id",
            "venue_account_ref_id",
            unique=True,
        ),
        Index(
            "ix_mandate_account_bindings_account_enabled",
            "venue_account_ref_id",
            "enabled",
            "routing_eligible",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    binding_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    strategy_mandate_ref_id: Mapped[str] = mapped_column(ForeignKey("strategy_mandates.id"), index=True)
    venue_account_ref_id: Mapped[str] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    strategy_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    routing_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_recommendation_priority: Mapped[int | None] = mapped_column(Integer)
    allow_builder_deployed_for_strategy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_builder_deployed_for_trading: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StrategyComponentConfigModel(Base):
    __tablename__ = "strategy_component_configs"
    __table_args__ = (
        Index(
            "ix_strategy_component_configs_scope_component",
            "strategy_mandate_ref_id",
            "binding_scope_key",
            "component_key",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    strategy_mandate_ref_id: Mapped[str] = mapped_column(ForeignKey("strategy_mandates.id"), index=True)
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    binding_scope_key: Mapped[str] = mapped_column(String(128), index=True)
    component_key: Mapped[str] = mapped_column(String(64), index=True)
    component_type: Mapped[str] = mapped_column(String(64), index=True)
    timeframe: Mapped[Timeframe | None] = mapped_column(enum_column(Timeframe), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capital_allocation_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    max_open_risk_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    parameters_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_component_config_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_component_configs.id"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CandleModel(Base):
    __tablename__ = "candles"
    __table_args__ = (
        Index(
            "ix_candles_env_venue_symbol_timeframe_open_time",
            "environment",
            "venue",
            "symbol",
            "timeframe",
            "open_time",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(enum_column(Timeframe), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    high: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    low: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    close: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    trade_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IndicatorSnapshotModel(Base):
    __tablename__ = "indicator_snapshots"
    __table_args__ = (
        Index(
            "ix_indicator_snapshots_env_instrument_timeframe_as_of",
            "environment",
            "venue",
            "instrument_ref_id",
            "symbol",
            "timeframe",
            "as_of",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(enum_column(Timeframe), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ema_5: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    ema_10: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    sma_20: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    macd: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    macd_histogram: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SignalEventModel(Base):
    __tablename__ = "signal_events"
    __table_args__ = (
        Index(
            "ix_signal_events_family_sleeve_symbol_generated_at",
            "family",
            "sleeve_id",
            "symbol",
            "generated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    signal_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    evaluation_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    family: Mapped[StrategyFamily] = mapped_column(enum_column(StrategyFamily), index=True)
    sleeve_id: Mapped[str] = mapped_column(String(32), index=True)
    component_key: Mapped[str | None] = mapped_column(String(64), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(enum_column(Timeframe), index=True)
    signal_type: Mapped[SignalType] = mapped_column(enum_column(SignalType), index=True)
    reason_code: Mapped[str | None] = mapped_column(String(64), index=True)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    features: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StrategyDecisionModel(Base):
    __tablename__ = "strategy_decisions"
    __table_args__ = (
        Index(
            "ix_strategy_decisions_family_sleeve_symbol_decided_at",
            "family",
            "sleeve_id",
            "symbol",
            "decided_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    decision_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    evaluation_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    family: Mapped[StrategyFamily] = mapped_column(enum_column(StrategyFamily), index=True)
    signal_id: Mapped[str | None] = mapped_column(String(64), index=True)
    sleeve_id: Mapped[str] = mapped_column(String(32), index=True)
    component_key: Mapped[str | None] = mapped_column(String(64), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction] = mapped_column(enum_column(DecisionAction), index=True)
    status: Mapped[StrategyDecisionStatus] = mapped_column(
        enum_column(StrategyDecisionStatus),
        index=True,
    )
    reason_code: Mapped[str | None] = mapped_column(String(64), index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    rationale: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    features: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SleeveAllocationModel(Base):
    __tablename__ = "sleeve_allocations"
    __table_args__ = (
        Index(
            "ix_sleeve_allocations_env_sleeve_effective_from",
            "environment",
            "sleeve_id",
            "effective_from",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    sleeve_id: Mapped[str] = mapped_column(String(32), index=True)
    target_allocation_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    allocated_equity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    open_risk_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MandateDesiredTradeModel(Base):
    """Mandate-level desired trade, above any future child order intents."""

    __tablename__ = "mandate_desired_trades"
    __table_args__ = (
        Index(
            "ix_mandate_desired_trades_env_mandate_status_created_at",
            "environment",
            "strategy_mandate_ref_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_mandate_desired_trades_env_instrument_created_at",
            "environment",
            "instrument_ref_id",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    desired_trade_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    evaluated_state_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    market_data_source_policy_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_market_data_source_policies.id"),
        index=True,
    )
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    family: Mapped[StrategyFamily] = mapped_column(enum_column(StrategyFamily), index=True)
    component_key: Mapped[str | None] = mapped_column(String(64), index=True)
    planning_source_venue: Mapped[str] = mapped_column(String(32), index=True)
    planning_source_mode: Mapped[MarketDataSourceMode] = mapped_column(
        enum_column(MarketDataSourceMode),
        index=True,
    )
    planning_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    target_scope: Mapped[TradeTargetScope] = mapped_column(enum_column(TradeTargetScope), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction] = mapped_column(enum_column(DecisionAction), index=True)
    side: Mapped[OrderSide | None] = mapped_column(enum_column(OrderSide), index=True)
    desired_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    desired_notional: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    source_decision_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_evaluation_keys_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_binding_keys_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[MandateDesiredTradeStatus] = mapped_column(
        enum_column(MandateDesiredTradeStatus),
        index=True,
    )
    status_reason_code: Mapped[str | None] = mapped_column(String(64), index=True)
    status_message: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RoutingAssessmentModel(Base):
    """Non-executing routing substrate assessment for one mandate desired trade."""

    __tablename__ = "routing_assessments"
    __table_args__ = (
        Index(
            "ix_routing_assessments_env_desired_trade_evaluated_at",
            "environment",
            "desired_trade_ref_id",
            "evaluated_at",
        ),
        Index(
            "ix_routing_assessments_env_status_evaluated_at",
            "environment",
            "decision_status",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    assessment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_desired_trades.id"), index=True)
    desired_trade_key: Mapped[str] = mapped_column(String(128), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    market_data_source_policy_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_market_data_source_policies.id"),
        index=True,
    )
    planning_source_venue: Mapped[str] = mapped_column(String(32), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction] = mapped_column(enum_column(DecisionAction), index=True)
    target_scope: Mapped[TradeTargetScope] = mapped_column(enum_column(TradeTargetScope), index=True)
    decision_status: Mapped[RoutingAssessmentDecisionStatus] = mapped_column(
        enum_column(RoutingAssessmentDecisionStatus),
        index=True,
    )
    eligible_binding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ineligible_binding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    request_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RoutingAssessmentCandidateModel(Base):
    """Per-binding eligibility facts for a non-executing routing assessment."""

    __tablename__ = "routing_assessment_candidates"
    __table_args__ = (
        Index(
            "ix_routing_assessment_candidates_assessment_status",
            "assessment_ref_id",
            "eligibility_status",
        ),
        Index(
            "ix_routing_assessment_candidates_binding",
            "binding_ref_id",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_ref_id: Mapped[str] = mapped_column(ForeignKey("routing_assessments.id"), index=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True)
    binding_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_account_bindings.id"), index=True)
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue_account_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    exchange_symbol: Mapped[str | None] = mapped_column(String(64), index=True)
    eligibility_status: Mapped[RoutingCandidateEligibilityStatus] = mapped_column(
        enum_column(RoutingCandidateEligibilityStatus),
        index=True,
    )
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    fact_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RouteReadinessAuditModel(Base):
    """Non-selecting data-sufficiency audit before future target recommendation."""

    __tablename__ = "route_readiness_audits"
    __table_args__ = (
        Index(
            "ix_route_readiness_audits_env_desired_trade_evaluated_at",
            "environment",
            "desired_trade_ref_id",
            "evaluated_at",
        ),
        Index(
            "ix_route_readiness_audits_env_status_evaluated_at",
            "environment",
            "overall_status",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    route_readiness_audit_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_desired_trades.id"), index=True)
    desired_trade_key: Mapped[str] = mapped_column(String(128), index=True)
    routing_assessment_ref_id: Mapped[str | None] = mapped_column(ForeignKey("routing_assessments.id"), index=True)
    routing_assessment_id: Mapped[str | None] = mapped_column(String(64), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction] = mapped_column(enum_column(DecisionAction), index=True)
    target_scope: Mapped[TradeTargetScope] = mapped_column(enum_column(TradeTargetScope), index=True)
    overall_status: Mapped[RouteReadinessAuditStatus] = mapped_column(
        enum_column(RouteReadinessAuditStatus),
        index=True,
    )
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ready_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    blocked_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    insufficient_data_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    global_reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    global_missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    global_stale_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    global_blocking_reasons_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    non_selecting: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recommendation_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_choice_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    child_intent_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_order_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RouteReadinessCandidateAuditModel(Base):
    """Per-candidate non-selecting data-sufficiency facts for a route-readiness audit."""

    __tablename__ = "route_readiness_candidate_audits"
    __table_args__ = (
        Index(
            "ix_route_readiness_candidates_audit_status",
            "route_readiness_audit_ref_id",
            "status",
        ),
        Index(
            "ix_route_readiness_candidates_binding",
            "binding_ref_id",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    route_readiness_audit_ref_id: Mapped[str] = mapped_column(
        ForeignKey("route_readiness_audits.id"),
        index=True,
    )
    route_readiness_audit_id: Mapped[str] = mapped_column(String(64), index=True)
    routing_assessment_candidate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("routing_assessment_candidates.id"),
        index=True,
    )
    binding_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_account_bindings.id"), index=True)
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue_account_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    exchange_symbol: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[RouteReadinessAuditStatus] = mapped_column(
        enum_column(RouteReadinessAuditStatus),
        index=True,
    )
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    stale_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    unsupported_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    unavailable_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    policy_blocks_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    blocking_reasons_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    fact_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    data_sources_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RoutingTargetRecommendationModel(Base):
    """Non-executing single-ready-candidate target recommendation audit record."""

    __tablename__ = "routing_target_recommendations"
    __table_args__ = (
        Index(
            "ix_rtrec_recommendation_id",
            "routing_target_recommendation_id",
            unique=True,
        ),
        Index(
            "ix_routing_target_recommendations_audit_created_at",
            "route_readiness_audit_id",
            "created_at",
        ),
        Index(
            "ix_routing_target_recommendations_desired_trade_created_at",
            "desired_trade_key",
            "created_at",
        ),
        Index(
            "ix_routing_target_recommendations_status_created_at",
            "status",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    routing_target_recommendation_id: Mapped[str] = mapped_column(String(64))
    route_readiness_audit_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("route_readiness_audits.id"),
        index=True,
    )
    route_readiness_audit_id: Mapped[str] = mapped_column(String(64), index=True)
    routing_assessment_ref_id: Mapped[str | None] = mapped_column(ForeignKey("routing_assessments.id"), index=True)
    routing_assessment_id: Mapped[str | None] = mapped_column(String(64), index=True)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_desired_trades.id"), index=True)
    desired_trade_key: Mapped[str | None] = mapped_column(String(128), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction | None] = mapped_column(enum_column(DecisionAction), index=True)
    target_scope: Mapped[TradeTargetScope | None] = mapped_column(enum_column(TradeTargetScope), index=True)
    status: Mapped[RoutingTargetRecommendationStatus] = mapped_column(
        enum_column(RoutingTargetRecommendationStatus),
        index=True,
    )
    policy_name: Mapped[str] = mapped_column(String(64), index=True)
    recommended_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    recommended_binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    recommended_venue_account_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("venue_accounts.id"),
        index=True,
    )
    recommended_venue_account_key: Mapped[str | None] = mapped_column(String(128), index=True)
    recommended_venue: Mapped[str | None] = mapped_column(String(32), index=True)
    recommended_exchange_symbol: Mapped[str | None] = mapped_column(String(64), index=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ready_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    blocking_reasons_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    stale_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    non_executing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_choice_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    child_intent_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_order_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class RoutingTargetChoiceModel(Base):
    """Operator-requested non-executing target-choice audit record."""

    __tablename__ = "routing_target_choices"
    __table_args__ = (
        Index(
            "ix_routing_target_choices_assessment_created_at",
            "routing_assessment_id",
            "created_at",
        ),
        Index(
            "ix_routing_target_choices_desired_trade_created_at",
            "desired_trade_key",
            "created_at",
        ),
        Index(
            "ix_routing_target_choices_binding_status",
            "selected_binding_ref_id",
            "status",
        ),
        Index(
            "ix_routing_target_choices_status_created_at",
            "status",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    target_choice_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    routing_assessment_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("routing_assessments.id"),
        index=True,
    )
    routing_assessment_id: Mapped[str] = mapped_column(String(64), index=True)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_desired_trades.id"), index=True)
    desired_trade_key: Mapped[str | None] = mapped_column(String(128), index=True)
    selected_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    selected_binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    selected_venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    selected_venue_account_key: Mapped[str | None] = mapped_column(String(128), index=True)
    selected_venue: Mapped[str | None] = mapped_column(String(32), index=True)
    status: Mapped[RoutingTargetChoiceStatus] = mapped_column(enum_column(RoutingTargetChoiceStatus), index=True)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_data_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    approval_note: Mapped[str | None] = mapped_column(Text)
    requested_by: Mapped[str | None] = mapped_column(String(128), index=True)
    non_executing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class RoutingAutomationApprovalModel(Base):
    """Durable operator approval gate for one explicit same-target automation action."""

    __tablename__ = "routing_automation_approvals"
    __table_args__ = (
        Index(
            "ix_routing_automation_approvals_desired_action_created",
            "environment",
            "desired_trade_key",
            "action_name",
            "created_at",
        ),
        Index(
            "ix_routing_automation_approvals_status_created",
            "environment",
            "status",
            "created_at",
        ),
        Index(
            "ix_routing_automation_approvals_target_choice",
            "routing_target_choice_id",
            "action_name",
        ),
        Index(
            "ix_routing_automation_approvals_intent",
            "intent_id",
            "action_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    approval_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(ForeignKey("mandate_desired_trades.id"), index=True)
    desired_trade_key: Mapped[str] = mapped_column(String(128), index=True)
    action_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    approved_by: Mapped[str] = mapped_column(String(128), index=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    policy_name: Mapped[str] = mapped_column(String(128), index=True)
    automation_mode: Mapped[str] = mapped_column(String(64), index=True)
    route_readiness_audit_id: Mapped[str | None] = mapped_column(String(64), index=True)
    routing_assessment_id: Mapped[str | None] = mapped_column(String(64), index=True)
    routing_target_recommendation_id: Mapped[str | None] = mapped_column(String(64), index=True)
    routing_target_choice_id: Mapped[str | None] = mapped_column(String(64), index=True)
    intent_id: Mapped[str | None] = mapped_column(String(64), index=True)
    readiness_evaluation_id: Mapped[str | None] = mapped_column(String(64), index=True)
    submitted_order_id: Mapped[str | None] = mapped_column(String(64), index=True)
    selected_binding_ref_id: Mapped[str | None] = mapped_column(String(36), index=True)
    selected_binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    selected_venue_account_ref_id: Mapped[str | None] = mapped_column(String(36), index=True)
    selected_venue_account_key: Mapped[str | None] = mapped_column(String(128), index=True)
    selected_venue: Mapped[str | None] = mapped_column(String(32), index=True)
    selected_exchange_symbol: Mapped[str | None] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    revoked_by: Mapped[str | None] = mapped_column(String(128), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    consumed_by: Mapped[str | None] = mapped_column(String(128), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    boundary_flags_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    policy_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    lineage_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PositionModel(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index(
            "ix_positions_env_venue_sleeve_symbol_status",
            "environment",
            "venue",
            "sleeve_id",
            "symbol",
            "status",
        ),
        Index(
            "ix_positions_env_venue_account_instrument_status",
            "environment",
            "venue",
            "account_address",
            "instrument_ref_id",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    position_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    exchange_position_key: Mapped[str | None] = mapped_column(String(128), index=True)
    account_position_key: Mapped[str] = mapped_column(String(256), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    sleeve_id: Mapped[str | None] = mapped_column(String(32), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    account_address: Mapped[str | None] = mapped_column(String(64), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[OrderSide] = mapped_column(enum_column(OrderSide))
    status: Mapped[PositionStatus] = mapped_column(enum_column(PositionStatus), index=True)
    attribution_status: Mapped[AttributionStatus] = mapped_column(
        enum_column(AttributionStatus),
        default=AttributionStatus.UNASSIGNED,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    avg_entry_price: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    mark_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    position_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    margin_used: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    liquidation_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    leverage_type: Mapped[str | None] = mapped_column(String(32))
    leverage_value: Mapped[int | None] = mapped_column(Integer)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class OrderIntentModel(Base):
    """Downstream binding/account-targeted child intent.

    This table intentionally sits below mandate-level desired trades. Phase 4B
    and later routing work should attach order intents to a parent desired
    trade once routing chooses a specific binding/account path, or earlier when
    the target binding/account is already naturally known for a binding-scoped
    reduce/close action.
    """

    __tablename__ = "order_intents"
    __table_args__ = (
        Index("ix_order_intents_env_status_created_at", "environment", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    intent_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    decision_id: Mapped[str | None] = mapped_column(String(64), index=True)
    action: Mapped[DecisionAction | None] = mapped_column(enum_column(DecisionAction), index=True)
    mandate_desired_trade_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_desired_trades.id"),
        index=True,
    )
    desired_trade_key: Mapped[str | None] = mapped_column(String(128), index=True)
    sleeve_id: Mapped[str] = mapped_column(String(32), index=True)
    component_key: Mapped[str | None] = mapped_column(String(64), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[OrderSide] = mapped_column(enum_column(OrderSide))
    order_type: Mapped[OrderType] = mapped_column(enum_column(OrderType))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ttl_seconds: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderIntentStatus] = mapped_column(enum_column(OrderIntentStatus), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExecutionReadinessEvaluationModel(Base):
    __tablename__ = "execution_readiness_evaluations"
    __table_args__ = (
        Index(
            "ix_execution_readiness_env_outcome_evaluated_at",
            "environment",
            "outcome",
            "evaluated_at",
        ),
        Index(
            "ix_execution_readiness_env_venue_evaluated_at",
            "environment",
            "venue",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    readiness_evaluation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    readiness_evaluation_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    intent_ref_id: Mapped[str | None] = mapped_column(ForeignKey("order_intents.id"), index=True)
    intent_id: Mapped[str] = mapped_column(String(64), index=True)
    mandate_desired_trade_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_desired_trades.id"),
        index=True,
    )
    desired_trade_key: Mapped[str | None] = mapped_column(String(128), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    support_level: Mapped[str] = mapped_column(String(32))
    preview_status: Mapped[str | None] = mapped_column(String(32), index=True)
    outcome: Mapped[ExecutionReadinessOutcome] = mapped_column(
        enum_column(ExecutionReadinessOutcome),
        index=True,
    )
    eligible_for_submission_in_principle: Mapped[bool] = mapped_column(Boolean, nullable=False)
    live_submission_phase_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    venue_supports_order_submission: Mapped[bool] = mapped_column(Boolean, nullable=False)
    adapter_supports_order_submission: Mapped[bool] = mapped_column(Boolean, nullable=False)
    adapter_supports_cancel_amend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submission_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False)
    account_connected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    private_state_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    private_state_ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskEvaluationModel(Base):
    __tablename__ = "risk_evaluations"
    __table_args__ = (
        Index(
            "ix_risk_evaluations_env_outcome_evaluated_at",
            "environment",
            "outcome",
            "evaluated_at",
        ),
        Index(
            "ix_risk_evaluations_env_mandate_evaluated_at",
            "environment",
            "strategy_mandate_ref_id",
            "evaluated_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    risk_evaluation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    risk_evaluation_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    decision_id: Mapped[str] = mapped_column(String(64), index=True)
    decision_evaluation_key: Mapped[str | None] = mapped_column(String(128), index=True)
    client_ref_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), index=True)
    strategy_mandate_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_mandates.id"),
        index=True,
    )
    mandate_key: Mapped[str | None] = mapped_column(String(128), index=True)
    market_data_source_policy_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_market_data_source_policies.id"),
        index=True,
    )
    planning_source_venue: Mapped[str | None] = mapped_column(String(32), index=True)
    component_key: Mapped[str | None] = mapped_column(String(64), index=True)
    target_scope: Mapped[TradeTargetScope | None] = mapped_column(enum_column(TradeTargetScope), index=True)
    mandate_account_binding_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_account_bindings.id"),
        index=True,
    )
    binding_key: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    instrument_key: Mapped[str | None] = mapped_column(String(128), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[DecisionAction] = mapped_column(enum_column(DecisionAction), index=True)
    decision_status: Mapped[StrategyDecisionStatus] = mapped_column(
        enum_column(StrategyDecisionStatus),
        index=True,
    )
    outcome: Mapped[RiskEvaluationOutcome] = mapped_column(
        enum_column(RiskEvaluationOutcome),
        index=True,
    )
    reason_code: Mapped[str | None] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    desired_trade_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("mandate_desired_trades.id"),
        index=True,
    )
    desired_trade_key: Mapped[str | None] = mapped_column(String(128), index=True)
    desired_trade_status: Mapped[MandateDesiredTradeStatus | None] = mapped_column(
        enum_column(MandateDesiredTradeStatus),
        index=True,
    )
    child_intent_ref_id: Mapped[str | None] = mapped_column(ForeignKey("order_intents.id"), index=True)
    child_intent_id: Mapped[str | None] = mapped_column(String(64), index=True)
    child_intent_status: Mapped[OrderIntentStatus | None] = mapped_column(
        enum_column(OrderIntentStatus),
        index=True,
    )
    policy_checks: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SubmittedOrderModel(Base):
    __tablename__ = "submitted_orders"
    __table_args__ = (
        Index(
            "ix_submitted_orders_env_venue_exchange_order_id",
            "environment",
            "venue",
            "account_address",
            "exchange_order_id",
        ),
        Index(
            "ix_submitted_orders_env_venue_account_instrument_status",
            "environment",
            "venue",
            "account_address",
            "instrument_ref_id",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    submitted_order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    intent_id: Mapped[str | None] = mapped_column(String(64), index=True)
    client_order_id: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    account_address: Mapped[str | None] = mapped_column(String(64), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    side: Mapped[OrderSide | None] = mapped_column(enum_column(OrderSide))
    order_type: Mapped[OrderType | None] = mapped_column(enum_column(OrderType))
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    original_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    remaining_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exchange_order_id: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[SubmittedOrderStatus] = mapped_column(enum_column(SubmittedOrderStatus), index=True)
    reconciliation_status: Mapped[SubmittedOrderReconciliationStatus] = mapped_column(
        enum_column(SubmittedOrderReconciliationStatus),
        default=SubmittedOrderReconciliationStatus.NOT_ATTEMPTED,
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    filled_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    average_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    last_fill_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_reason_code: Mapped[str | None] = mapped_column(String(128), index=True)
    status_message: Mapped[str | None] = mapped_column(Text)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    cancelable_in_principle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    amendable_in_principle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OrderIntentSubmissionLeaseModel(Base):
    """Short-lived guard for explicit child-intent submit calls.

    This is deliberately not a submitted-order reservation. It serializes the
    adapter-call boundary while SubmittedOrder remains post-submit truth only.
    """

    __tablename__ = "order_intent_submission_leases"
    __table_args__ = (
        UniqueConstraint(
            "environment",
            "intent_id",
            "purpose",
            name="uq_order_intent_submission_leases_env_intent_purpose",
        ),
        Index(
            "ix_order_intent_submission_leases_status_expires",
            "status",
            "expires_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    lease_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    intent_id: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), index=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason_code: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SubmittedOrderLifecycleEventModel(Base):
    __tablename__ = "submitted_order_lifecycle_events"
    __table_args__ = (
        Index(
            "ix_so_lifecycle_env_order_obs",
            "environment",
            "submitted_order_id",
            "observed_at",
        ),
        Index(
            "ix_so_lifecycle_env_intent_obs",
            "environment",
            "intent_id",
            "observed_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    submitted_order_id: Mapped[str] = mapped_column(String(64), index=True)
    intent_id: Mapped[str | None] = mapped_column(String(64), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[SubmittedOrderStatus] = mapped_column(enum_column(SubmittedOrderStatus), index=True)
    reconciliation_status: Mapped[SubmittedOrderReconciliationStatus] = mapped_column(
        enum_column(SubmittedOrderReconciliationStatus),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FillModel(Base):
    __tablename__ = "fills"
    __table_args__ = (
        Index(
            "ix_fills_env_venue_symbol_filled_at",
            "environment",
            "venue",
            "symbol",
            "filled_at",
        ),
        Index(
            "ix_fills_env_venue_account_instrument_filled_at",
            "environment",
            "venue",
            "account_address",
            "instrument_ref_id",
            "filled_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    fill_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    venue_fill_id: Mapped[str | None] = mapped_column(String(128), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), default="hyperliquid", index=True)
    account_address: Mapped[str | None] = mapped_column(String(64), index=True)
    submitted_order_id: Mapped[str] = mapped_column(String(64), index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(128), index=True)
    position_id: Mapped[str | None] = mapped_column(String(64), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol_id: Mapped[str | None] = mapped_column(ForeignKey("symbols.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[OrderSide | None] = mapped_column(enum_column(OrderSide))
    price: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    fee: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    fee_token: Mapped[str | None] = mapped_column(String(32))
    closed_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PortfolioSnapshotModel(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        Index("ix_portfolio_snapshots_env_captured_at", "environment", "captured_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    account_equity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    gross_exposure: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    net_exposure: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    drawdown_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    sleeve_exposures: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskEventModel(Base):
    __tablename__ = "risk_events"
    __table_args__ = (
        Index("ix_risk_events_env_severity_triggered_at", "environment", "severity", "triggered_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    risk_event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    decision_id: Mapped[str | None] = mapped_column(String(64), index=True)
    sleeve_id: Mapped[str | None] = mapped_column(String(32), index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    severity: Mapped[RiskSeverity] = mapped_column(enum_column(RiskSeverity), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HealthEventModel(Base):
    __tablename__ = "health_events"
    __table_args__ = (
        Index("ix_health_events_component_observed_at", "component", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    health_event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    component: Mapped[SystemComponent] = mapped_column(enum_column(SystemComponent), index=True)
    status: Mapped[HealthStatus] = mapped_column(enum_column(HealthStatus), index=True)
    message: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_env_entity_created_at", "environment", "entity_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    audit_log_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    actor: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemStateModel(Base):
    """Flexible control-plane state only.

    Keep this table limited to operator controls and service checkpoints.
    Core trading truth belongs in the dedicated trading/account tables.
    """

    __tablename__ = "system_state"
    __table_args__ = (
        Index("ix_system_state_env_state_key", "environment", "state_key", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    state_key: Mapped[str] = mapped_column(String(128))
    state_value: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ExchangeAccountSnapshotModel(Base):
    __tablename__ = "exchange_account_snapshots"
    __table_args__ = (
        Index(
            "ix_exchange_account_snapshots_env_venue_observed_at",
            "environment",
            "venue",
            "observed_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    account_address: Mapped[str] = mapped_column(String(64), index=True)
    equity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    margin_used: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    total_position_notional: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    cross_margin_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    margin_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketDataHealthModel(Base):
    __tablename__ = "market_data_health"
    __table_args__ = (
        Index(
            "ix_market_data_health_env_venue_symbol_timeframe",
            "environment",
            "venue",
            "symbol",
            "timeframe",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(enum_column(Timeframe), index=True)
    last_candle_open_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_candle_close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stale_after_seconds: Mapped[int] = mapped_column(Integer, default=180)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MarketDataCheckpointModel(Base):
    __tablename__ = "market_data_checkpoints"
    __table_args__ = (
        Index(
            "ix_market_data_checkpoints_env_venue_symbol_timeframe",
            "environment",
            "venue",
            "symbol",
            "timeframe",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    instrument_ref_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(enum_column(Timeframe), index=True)
    last_requested_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_requested_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_persisted_open_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_persisted_close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_sync_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    overlap_bars: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PositionAttributionOverlayModel(Base):
    __tablename__ = "position_attribution_overlays"
    __table_args__ = (
        Index(
            "ix_position_attribution_overlays_position_sleeve_as_of",
            "position_id",
            "sleeve_id",
            "as_of",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    overlay_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    environment: Mapped[Environment] = mapped_column(enum_column(Environment), index=True)
    venue: Mapped[str] = mapped_column(String(32), index=True)
    position_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_account_ref_id: Mapped[str | None] = mapped_column(ForeignKey("venue_accounts.id"), index=True)
    sleeve_id: Mapped[str] = mapped_column(String(32), index=True)
    attributed_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    attributed_notional: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
