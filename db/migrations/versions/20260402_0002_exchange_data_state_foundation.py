"""Phase 2 exchange, market data, and reconciliation foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0002"
down_revision = "20260402_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    environment_enum = postgresql.ENUM(
        "dev", "backtest", "paper", "testnet", "live", name="environment", create_type=False
    )
    timeframe_enum = postgresql.ENUM(
        "1m", "5m", "15m", "1h", "4h", "1d", name="timeframe", create_type=False
    )
    order_side_enum = postgresql.ENUM("buy", "sell", name="orderside", create_type=False)
    order_type_enum = postgresql.ENUM(
        "market", "limit", "stop", name="ordertype", create_type=False
    )

    op.execute("ALTER TYPE timeframe ADD VALUE IF NOT EXISTS '1m'")
    op.execute("ALTER TYPE timeframe ADD VALUE IF NOT EXISTS '5m'")
    op.execute("ALTER TYPE timeframe ADD VALUE IF NOT EXISTS '1d'")

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.add_column(sa.Column("exchange_symbol", sa.String(length=64), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("asset_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("size_decimals", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("max_leverage", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("only_isolated", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("is_perpetual", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("is_builder_deployed", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("raw_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.drop_constraint("uq_symbols_symbol", type_="unique")
        batch_op.create_index("ix_symbols_venue_symbol", ["venue", "symbol"], unique=True)
        batch_op.create_index("ix_symbols_venue_asset_id", ["venue", "asset_id"], unique=True)

    op.drop_index("ix_candles_symbol_timeframe_open_time", table_name="candles")
    with op.batch_alter_table("candles") as batch_op:
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.create_index(
            "ix_candles_venue_symbol_timeframe_open_time",
            ["venue", "symbol", "timeframe", "open_time"],
            unique=True,
        )

    op.drop_index("ix_positions_env_sleeve_symbol_status", table_name="positions")
    with op.batch_alter_table("positions") as batch_op:
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.add_column(sa.Column("account_address", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("position_value", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("margin_used", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("liquidation_price", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("leverage_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("leverage_value", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.create_index(
            "ix_positions_env_venue_sleeve_symbol_status",
            ["environment", "venue", "sleeve_id", "symbol", "status"],
            unique=False,
        )

    op.drop_index("ix_submitted_orders_env_exchange_order_id", table_name="submitted_orders")
    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.alter_column("intent_id", existing_type=sa.String(length=64), nullable=True)
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.add_column(sa.Column("account_address", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("symbol_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("symbol", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("side", order_side_enum, nullable=True))
        batch_op.add_column(sa.Column("order_type", order_type_enum, nullable=True))
        batch_op.add_column(sa.Column("limit_price", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("original_quantity", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("remaining_quantity", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.create_foreign_key(
            "fk_submitted_orders_symbol_id_symbols",
            "symbols",
            ["symbol_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_submitted_orders_env_venue_exchange_order_id",
            ["environment", "venue", "exchange_order_id"],
            unique=False,
        )

    op.drop_index("ix_fills_env_symbol_filled_at", table_name="fills")
    with op.batch_alter_table("fills") as batch_op:
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.add_column(sa.Column("account_address", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("exchange_order_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("side", order_side_enum, nullable=True))
        batch_op.add_column(sa.Column("fee_token", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("closed_pnl", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.create_index(
            "ix_fills_env_venue_symbol_filled_at",
            ["environment", "venue", "symbol", "filled_at"],
            unique=False,
        )

    op.create_table(
        "exchange_account_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("account_address", sa.String(length=64), nullable=False),
        sa.Column("equity", sa.Numeric(24, 12), nullable=False),
        sa.Column("available_balance", sa.Numeric(24, 12), nullable=False),
        sa.Column("margin_used", sa.Numeric(24, 12), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(24, 12), nullable=False),
        sa.Column("total_position_notional", sa.Numeric(24, 12), nullable=False),
        sa.Column("cross_margin_summary", sa.JSON(), nullable=False),
        sa.Column("margin_summary", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_exchange_account_snapshots_env_venue_observed_at",
        "exchange_account_snapshots",
        ["environment", "venue", "observed_at"],
    )

    op.create_table(
        "market_data_health",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("last_candle_open_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_candle_close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stale_after_seconds", sa.Integer(), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_market_data_health_env_venue_symbol_timeframe",
        "market_data_health",
        ["environment", "venue", "symbol", "timeframe"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_market_data_health_env_venue_symbol_timeframe", table_name="market_data_health")
    op.drop_table("market_data_health")
    op.drop_index(
        "ix_exchange_account_snapshots_env_venue_observed_at",
        table_name="exchange_account_snapshots",
    )
    op.drop_table("exchange_account_snapshots")

    op.drop_index("ix_fills_env_venue_symbol_filled_at", table_name="fills")
    with op.batch_alter_table("fills") as batch_op:
        batch_op.drop_column("raw_payload")
        batch_op.drop_column("closed_pnl")
        batch_op.drop_column("fee_token")
        batch_op.drop_column("side")
        batch_op.drop_column("exchange_order_id")
        batch_op.drop_column("account_address")
        batch_op.drop_column("venue")
    op.create_index("ix_fills_env_symbol_filled_at", "fills", ["environment", "symbol", "filled_at"])

    op.drop_index("ix_submitted_orders_env_venue_exchange_order_id", table_name="submitted_orders")
    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.drop_constraint("fk_submitted_orders_symbol_id_symbols", type_="foreignkey")
        batch_op.drop_column("raw_payload")
        batch_op.drop_column("reduce_only")
        batch_op.drop_column("remaining_quantity")
        batch_op.drop_column("original_quantity")
        batch_op.drop_column("limit_price")
        batch_op.drop_column("order_type")
        batch_op.drop_column("side")
        batch_op.drop_column("symbol")
        batch_op.drop_column("symbol_id")
        batch_op.drop_column("account_address")
        batch_op.drop_column("venue")
        batch_op.alter_column("intent_id", existing_type=sa.String(length=64), nullable=False)
    op.create_index(
        "ix_submitted_orders_env_exchange_order_id",
        "submitted_orders",
        ["environment", "exchange_order_id"],
    )

    op.drop_index("ix_positions_env_venue_sleeve_symbol_status", table_name="positions")
    with op.batch_alter_table("positions") as batch_op:
        batch_op.drop_column("raw_payload")
        batch_op.drop_column("leverage_value")
        batch_op.drop_column("leverage_type")
        batch_op.drop_column("liquidation_price")
        batch_op.drop_column("margin_used")
        batch_op.drop_column("position_value")
        batch_op.drop_column("account_address")
        batch_op.drop_column("venue")
    op.create_index(
        "ix_positions_env_sleeve_symbol_status",
        "positions",
        ["environment", "sleeve_id", "symbol", "status"],
    )

    op.drop_index("ix_candles_venue_symbol_timeframe_open_time", table_name="candles")
    with op.batch_alter_table("candles") as batch_op:
        batch_op.drop_column("venue")
    op.create_index(
        "ix_candles_symbol_timeframe_open_time",
        "candles",
        ["symbol", "timeframe", "open_time"],
        unique=True,
    )

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.drop_index("ix_symbols_venue_asset_id")
        batch_op.drop_index("ix_symbols_venue_symbol")
        batch_op.create_unique_constraint("uq_symbols_symbol", ["symbol"])
        batch_op.drop_column("raw_metadata")
        batch_op.drop_column("is_builder_deployed")
        batch_op.drop_column("is_perpetual")
        batch_op.drop_column("only_isolated")
        batch_op.drop_column("max_leverage")
        batch_op.drop_column("size_decimals")
        batch_op.drop_column("asset_id")
        batch_op.drop_column("exchange_symbol")
        batch_op.drop_column("venue")
