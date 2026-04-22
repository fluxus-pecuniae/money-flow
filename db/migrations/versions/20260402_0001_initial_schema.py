"""Initial schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


environment_enum = postgresql.ENUM(
    "dev", "backtest", "paper", "testnet", "live", name="environment", create_type=False
)
timeframe_enum = postgresql.ENUM("15m", "1h", "4h", name="timeframe", create_type=False)
signal_type_enum = postgresql.ENUM(
    "entry", "exit", "rebalance", "risk_reduction", name="signaltype", create_type=False
)
decision_action_enum = postgresql.ENUM(
    "noop", "open", "add", "reduce", "close", name="decisionaction", create_type=False
)
order_side_enum = postgresql.ENUM("buy", "sell", name="orderside", create_type=False)
order_type_enum = postgresql.ENUM("market", "limit", "stop", name="ordertype", create_type=False)
order_intent_status_enum = postgresql.ENUM(
    "pending_risk",
    "approved",
    "rejected",
    "expired",
    name="orderintentstatus",
    create_type=False,
)
submitted_order_status_enum = postgresql.ENUM(
    "new",
    "acknowledged",
    "partially_filled",
    "filled",
    "canceled",
    "rejected",
    name="submittedorderstatus",
    create_type=False,
)
position_status_enum = postgresql.ENUM("open", "closed", name="positionstatus", create_type=False)
risk_severity_enum = postgresql.ENUM(
    "info", "warning", "critical", name="riskseverity", create_type=False
)
health_status_enum = postgresql.ENUM(
    "healthy", "degraded", "unavailable", name="healthstatus", create_type=False
)
system_component_enum = postgresql.ENUM(
    "api",
    "exchange",
    "market_data",
    "indicators",
    "strategy",
    "risk",
    "portfolio",
    "execution",
    "alerts",
    "database",
    name="systemcomponent",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    environment_enum.create(bind, checkfirst=True)
    timeframe_enum.create(bind, checkfirst=True)
    signal_type_enum.create(bind, checkfirst=True)
    decision_action_enum.create(bind, checkfirst=True)
    order_side_enum.create(bind, checkfirst=True)
    order_type_enum.create(bind, checkfirst=True)
    order_intent_status_enum.create(bind, checkfirst=True)
    submitted_order_status_enum.create(bind, checkfirst=True)
    position_status_enum.create(bind, checkfirst=True)
    risk_severity_enum.create(bind, checkfirst=True)
    health_status_enum.create(bind, checkfirst=True)
    system_component_enum.create(bind, checkfirst=True)

    op.create_table(
        "symbols",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("base_asset", sa.String(length=32), nullable=False),
        sa.Column("quote_asset", sa.String(length=32), nullable=False),
        sa.Column("price_tick_size", sa.Numeric(24, 12), nullable=False),
        sa.Column("quantity_step_size", sa.Numeric(24, 12), nullable=False),
        sa.Column("min_order_size", sa.Numeric(24, 12), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_symbols_symbol", "symbols", ["symbol"])

    op.create_table(
        "candles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(24, 12), nullable=False),
        sa.Column("high", sa.Numeric(24, 12), nullable=False),
        sa.Column("low", sa.Numeric(24, 12), nullable=False),
        sa.Column("close", sa.Numeric(24, 12), nullable=False),
        sa.Column("volume", sa.Numeric(24, 12), nullable=False),
        sa.Column("trade_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candles_environment", "candles", ["environment"])
    op.create_index("ix_candles_symbol", "candles", ["symbol"])
    op.create_index("ix_candles_timeframe", "candles", ["timeframe"])
    op.create_index("ix_candles_open_time", "candles", ["open_time"])
    op.create_index(
        "ix_candles_symbol_timeframe_open_time",
        "candles",
        ["symbol", "timeframe", "open_time"],
        unique=True,
    )

    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ema_5", sa.Numeric(24, 12), nullable=True),
        sa.Column("ema_10", sa.Numeric(24, 12), nullable=True),
        sa.Column("sma_20", sa.Numeric(24, 12), nullable=True),
        sa.Column("rsi_14", sa.Numeric(10, 4), nullable=True),
        sa.Column("macd", sa.Numeric(24, 12), nullable=True),
        sa.Column("macd_signal", sa.Numeric(24, 12), nullable=True),
        sa.Column("macd_histogram", sa.Numeric(24, 12), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_indicator_snapshots_environment", "indicator_snapshots", ["environment"])
    op.create_index("ix_indicator_snapshots_symbol", "indicator_snapshots", ["symbol"])
    op.create_index("ix_indicator_snapshots_timeframe", "indicator_snapshots", ["timeframe"])
    op.create_index("ix_indicator_snapshots_as_of", "indicator_snapshots", ["as_of"])
    op.create_index(
        "ix_indicator_snapshots_symbol_timeframe_as_of",
        "indicator_snapshots",
        ["symbol", "timeframe", "as_of"],
        unique=True,
    )

    op.create_table(
        "signal_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("signal_id", sa.String(length=64), nullable=False),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("signal_type", signal_type_enum, nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("signal_id"),
    )
    op.create_index("ix_signal_events_environment", "signal_events", ["environment"])
    op.create_index("ix_signal_events_signal_id", "signal_events", ["signal_id"])
    op.create_index("ix_signal_events_symbol", "signal_events", ["symbol"])
    op.create_index("ix_signal_events_timeframe", "signal_events", ["timeframe"])
    op.create_index("ix_signal_events_sleeve_id", "signal_events", ["sleeve_id"])
    op.create_index("ix_signal_events_generated_at", "signal_events", ["generated_at"])
    op.create_index(
        "ix_signal_events_sleeve_symbol_generated_at",
        "signal_events",
        ["sleeve_id", "symbol", "generated_at"],
    )

    op.create_table(
        "strategy_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=False),
        sa.Column("signal_id", sa.String(length=64), nullable=True),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("action", decision_action_enum, nullable=False),
        sa.Column("confidence", sa.Numeric(10, 4), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("decision_id"),
    )
    op.create_index("ix_strategy_decisions_environment", "strategy_decisions", ["environment"])
    op.create_index("ix_strategy_decisions_decision_id", "strategy_decisions", ["decision_id"])
    op.create_index("ix_strategy_decisions_signal_id", "strategy_decisions", ["signal_id"])
    op.create_index("ix_strategy_decisions_sleeve_id", "strategy_decisions", ["sleeve_id"])
    op.create_index("ix_strategy_decisions_symbol", "strategy_decisions", ["symbol"])
    op.create_index("ix_strategy_decisions_action", "strategy_decisions", ["action"])
    op.create_index("ix_strategy_decisions_decided_at", "strategy_decisions", ["decided_at"])
    op.create_index(
        "ix_strategy_decisions_sleeve_symbol_decided_at",
        "strategy_decisions",
        ["sleeve_id", "symbol", "decided_at"],
    )

    op.create_table(
        "sleeve_allocations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("target_allocation_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("allocated_equity", sa.Numeric(24, 12), nullable=False),
        sa.Column("open_risk_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sleeve_allocations_environment", "sleeve_allocations", ["environment"])
    op.create_index("ix_sleeve_allocations_sleeve_id", "sleeve_allocations", ["sleeve_id"])
    op.create_index("ix_sleeve_allocations_effective_from", "sleeve_allocations", ["effective_from"])
    op.create_index(
        "ix_sleeve_allocations_env_sleeve_effective_from",
        "sleeve_allocations",
        ["environment", "sleeve_id", "effective_from"],
        unique=True,
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("position_id", sa.String(length=64), nullable=False),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", order_side_enum, nullable=False),
        sa.Column("status", position_status_enum, nullable=False),
        sa.Column("quantity", sa.Numeric(24, 12), nullable=False),
        sa.Column("avg_entry_price", sa.Numeric(24, 12), nullable=False),
        sa.Column("mark_price", sa.Numeric(24, 12), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(24, 12), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("position_id"),
    )
    op.create_index("ix_positions_environment", "positions", ["environment"])
    op.create_index("ix_positions_position_id", "positions", ["position_id"])
    op.create_index("ix_positions_sleeve_id", "positions", ["sleeve_id"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])
    op.create_index("ix_positions_status", "positions", ["status"])
    op.create_index("ix_positions_opened_at", "positions", ["opened_at"])
    op.create_index(
        "ix_positions_env_sleeve_symbol_status",
        "positions",
        ["environment", "sleeve_id", "symbol", "status"],
    )

    op.create_table(
        "order_intents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=True),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", order_side_enum, nullable=False),
        sa.Column("order_type", order_type_enum, nullable=False),
        sa.Column("quantity", sa.Numeric(24, 12), nullable=False),
        sa.Column("limit_price", sa.Numeric(24, 12), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False),
        sa.Column("status", order_intent_status_enum, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("intent_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_order_intents_environment", "order_intents", ["environment"])
    op.create_index("ix_order_intents_intent_id", "order_intents", ["intent_id"])
    op.create_index("ix_order_intents_decision_id", "order_intents", ["decision_id"])
    op.create_index("ix_order_intents_sleeve_id", "order_intents", ["sleeve_id"])
    op.create_index("ix_order_intents_symbol", "order_intents", ["symbol"])
    op.create_index("ix_order_intents_status", "order_intents", ["status"])
    op.create_index("ix_order_intents_idempotency_key", "order_intents", ["idempotency_key"])
    op.create_index("ix_order_intents_created_at", "order_intents", ["created_at"])
    op.create_index(
        "ix_order_intents_env_status_created_at",
        "order_intents",
        ["environment", "status", "created_at"],
    )

    op.create_table(
        "submitted_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("submitted_order_id", sa.String(length=64), nullable=False),
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("exchange_order_id", sa.String(length=128), nullable=True),
        sa.Column("status", submitted_order_status_enum, nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submitted_order_id"),
    )
    op.create_index("ix_submitted_orders_environment", "submitted_orders", ["environment"])
    op.create_index("ix_submitted_orders_submitted_order_id", "submitted_orders", ["submitted_order_id"])
    op.create_index("ix_submitted_orders_exchange_order_id", "submitted_orders", ["exchange_order_id"])
    op.create_index("ix_submitted_orders_status", "submitted_orders", ["status"])
    op.create_index("ix_submitted_orders_submitted_at", "submitted_orders", ["submitted_at"])
    op.create_index(
        "ix_submitted_orders_env_exchange_order_id",
        "submitted_orders",
        ["environment", "exchange_order_id"],
    )

    op.create_table(
        "fills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("fill_id", sa.String(length=64), nullable=False),
        sa.Column("submitted_order_id", sa.String(length=64), nullable=False),
        sa.Column("position_id", sa.String(length=64), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), sa.ForeignKey("symbols.id"), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(24, 12), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 12), nullable=False),
        sa.Column("fee", sa.Numeric(24, 12), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fill_id"),
    )
    op.create_index("ix_fills_environment", "fills", ["environment"])
    op.create_index("ix_fills_fill_id", "fills", ["fill_id"])
    op.create_index("ix_fills_submitted_order_id", "fills", ["submitted_order_id"])
    op.create_index("ix_fills_position_id", "fills", ["position_id"])
    op.create_index("ix_fills_symbol", "fills", ["symbol"])
    op.create_index("ix_fills_filled_at", "fills", ["filled_at"])
    op.create_index("ix_fills_env_symbol_filled_at", "fills", ["environment", "symbol", "filled_at"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("account_equity", sa.Numeric(24, 12), nullable=False),
        sa.Column("gross_exposure", sa.Numeric(24, 12), nullable=False),
        sa.Column("net_exposure", sa.Numeric(24, 12), nullable=False),
        sa.Column("drawdown_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("sleeve_exposures", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("snapshot_id"),
    )
    op.create_index("ix_portfolio_snapshots_environment", "portfolio_snapshots", ["environment"])
    op.create_index("ix_portfolio_snapshots_snapshot_id", "portfolio_snapshots", ["snapshot_id"])
    op.create_index("ix_portfolio_snapshots_captured_at", "portfolio_snapshots", ["captured_at"])
    op.create_index(
        "ix_portfolio_snapshots_env_captured_at",
        "portfolio_snapshots",
        ["environment", "captured_at"],
    )

    op.create_table(
        "risk_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("risk_event_id", sa.String(length=64), nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=True),
        sa.Column("sleeve_id", sa.String(length=32), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("severity", risk_severity_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("risk_event_id"),
    )
    op.create_index("ix_risk_events_environment", "risk_events", ["environment"])
    op.create_index("ix_risk_events_risk_event_id", "risk_events", ["risk_event_id"])
    op.create_index("ix_risk_events_decision_id", "risk_events", ["decision_id"])
    op.create_index("ix_risk_events_sleeve_id", "risk_events", ["sleeve_id"])
    op.create_index("ix_risk_events_symbol", "risk_events", ["symbol"])
    op.create_index("ix_risk_events_severity", "risk_events", ["severity"])
    op.create_index("ix_risk_events_triggered_at", "risk_events", ["triggered_at"])
    op.create_index(
        "ix_risk_events_env_severity_triggered_at",
        "risk_events",
        ["environment", "severity", "triggered_at"],
    )

    op.create_table(
        "health_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("health_event_id", sa.String(length=64), nullable=False),
        sa.Column("component", system_component_enum, nullable=False),
        sa.Column("status", health_status_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("health_event_id"),
    )
    op.create_index("ix_health_events_environment", "health_events", ["environment"])
    op.create_index("ix_health_events_health_event_id", "health_events", ["health_event_id"])
    op.create_index("ix_health_events_component", "health_events", ["component"])
    op.create_index("ix_health_events_status", "health_events", ["status"])
    op.create_index("ix_health_events_observed_at", "health_events", ["observed_at"])
    op.create_index(
        "ix_health_events_component_observed_at",
        "health_events",
        ["component", "observed_at"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("audit_log_id"),
    )
    op.create_index("ix_audit_logs_environment", "audit_logs", ["environment"])
    op.create_index("ix_audit_logs_audit_log_id", "audit_logs", ["audit_log_id"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index(
        "ix_audit_logs_env_entity_created_at",
        "audit_logs",
        ["environment", "entity_type", "created_at"],
    )

    op.create_table(
        "system_state",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("state_key", sa.String(length=128), nullable=False),
        sa.Column("state_value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        comment="Control-plane state only: kill switches, operator lockouts, cursors, checkpoints.",
    )
    op.create_index("ix_system_state_environment", "system_state", ["environment"])
    op.create_index(
        "ix_system_state_env_state_key",
        "system_state",
        ["environment", "state_key"],
        unique=True,
    )


def downgrade() -> None:
    for table_name in [
        "system_state",
        "audit_logs",
        "health_events",
        "risk_events",
        "portfolio_snapshots",
        "fills",
        "submitted_orders",
        "order_intents",
        "positions",
        "sleeve_allocations",
        "strategy_decisions",
        "signal_events",
        "indicator_snapshots",
        "candles",
        "symbols",
    ]:
        op.drop_table(table_name)

    bind = op.get_bind()
    system_component_enum.drop(bind, checkfirst=True)
    health_status_enum.drop(bind, checkfirst=True)
    risk_severity_enum.drop(bind, checkfirst=True)
    position_status_enum.drop(bind, checkfirst=True)
    submitted_order_status_enum.drop(bind, checkfirst=True)
    order_intent_status_enum.drop(bind, checkfirst=True)
    order_type_enum.drop(bind, checkfirst=True)
    order_side_enum.drop(bind, checkfirst=True)
    decision_action_enum.drop(bind, checkfirst=True)
    signal_type_enum.drop(bind, checkfirst=True)
    timeframe_enum.drop(bind, checkfirst=True)
    environment_enum.drop(bind, checkfirst=True)
