"""Phase 2.1 hardening for instruments, checkpoints, and identity semantics."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0003"
down_revision = "20260402_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    environment_enum = postgresql.ENUM(
        "dev", "backtest", "paper", "testnet", "live", name="environment", create_type=False
    )
    timeframe_enum = postgresql.ENUM(
        "1m", "5m", "15m", "1h", "4h", "1d", name="timeframe", create_type=False
    )
    market_type_enum = postgresql.ENUM(
        "spot", "perpetual", "future", "option", name="markettype", create_type=False
    )
    product_type_enum = postgresql.ENUM(
        "linear", "inverse", "spot", name="producttype", create_type=False
    )
    attribution_status_enum = postgresql.ENUM(
        "unassigned", "partial", "fully_attributed", name="attributionstatus", create_type=False
    )

    market_type_enum.create(op.get_bind(), checkfirst=True)
    product_type_enum.create(op.get_bind(), checkfirst=True)
    attribution_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "instruments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("instrument_id", sa.String(length=128), nullable=False),
        sa.Column("canonical_symbol", sa.String(length=64), nullable=False),
        sa.Column("market_type", market_type_enum, nullable=False),
        sa.Column("product_type", product_type_enum, nullable=False),
        sa.Column("base_asset", sa.String(length=32), nullable=False),
        sa.Column("quote_asset", sa.String(length=32), nullable=False),
        sa.Column("settlement_asset", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_instruments_instrument_id", "instruments", ["instrument_id"], unique=True)
    op.create_index(
        "ix_instruments_market_product_base_quote_settlement",
        "instruments",
        ["market_type", "product_type", "base_asset", "quote_asset", "settlement_asset"],
        unique=True,
    )

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("venue_asset_id", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column(
                "market_type",
                market_type_enum,
                nullable=False,
                server_default="perpetual",
            )
        )
        batch_op.add_column(
            sa.Column(
                "product_type",
                product_type_enum,
                nullable=False,
                server_default="linear",
            )
        )
        batch_op.add_column(sa.Column("settlement_asset", sa.String(length=32), nullable=True))
        batch_op.create_foreign_key("fk_symbols_instrument_id_instruments", "instruments", ["instrument_id"], ["id"])
        batch_op.create_index("ix_symbols_venue_exchange_symbol", ["venue", "exchange_symbol"], unique=True)
        batch_op.create_index("ix_symbols_instrument_id", ["instrument_id"], unique=False)

    op.execute(
        """
        INSERT INTO instruments (
            id, instrument_id, canonical_symbol, market_type, product_type,
            base_asset, quote_asset, settlement_asset, is_active, created_at, updated_at
        )
        SELECT
            md5('perpetual:linear:' || base_asset || ':' || quote_asset || ':' || COALESCE(quote_asset, quote_asset)),
            'perpetual:linear:' || base_asset || ':' || quote_asset || ':' || COALESCE(quote_asset, quote_asset),
            symbol,
            'perpetual',
            'linear',
            base_asset,
            quote_asset,
            quote_asset,
            is_active,
            created_at,
            updated_at
        FROM symbols
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE symbols s
        SET
            instrument_id = i.id,
            venue_asset_id = CASE WHEN s.asset_id IS NOT NULL THEN s.asset_id::text ELSE NULL END,
            settlement_asset = COALESCE(s.settlement_asset, s.quote_asset)
        FROM instruments i
        WHERE
            i.market_type = 'perpetual'
            AND i.product_type = 'linear'
            AND i.base_asset = s.base_asset
            AND i.quote_asset = s.quote_asset
            AND COALESCE(i.settlement_asset, '') = COALESCE(s.quote_asset, '')
        """
    )

    with op.batch_alter_table("candles") as batch_op:
        batch_op.drop_index("ix_candles_venue_symbol_timeframe_open_time")
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_candles_instrument_id_instruments", "instruments", ["instrument_id"], ["id"])
        batch_op.create_index(
            "ix_candles_env_venue_symbol_timeframe_open_time",
            ["environment", "venue", "symbol", "timeframe", "open_time"],
            unique=True,
        )

    op.execute(
        """
        UPDATE candles c
        SET instrument_id = s.instrument_id
        FROM symbols s
        WHERE c.symbol_id = s.id
        """
    )

    with op.batch_alter_table("positions") as batch_op:
        batch_op.add_column(sa.Column("exchange_position_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("account_position_key", sa.String(length=256), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "attribution_status",
                attribution_status_enum,
                nullable=False,
                server_default="unassigned",
            )
        )
        batch_op.alter_column("sleeve_id", existing_type=sa.String(length=32), nullable=True)
        batch_op.create_foreign_key("fk_positions_instrument_id_instruments", "instruments", ["instrument_id"], ["id"])
        batch_op.create_index(
            "ix_positions_env_venue_account_instrument_status",
            ["environment", "venue", "account_address", "instrument_id", "status"],
            unique=False,
        )

    op.execute(
        """
        UPDATE positions p
        SET
            instrument_id = s.instrument_id,
            account_position_key = p.environment::text || ':' || p.venue || ':' || COALESCE(p.account_address, '') || ':' || COALESCE(s.instrument_id, '') || ':' || 'one_way'
        FROM symbols s
        WHERE p.symbol_id = s.id
        """
    )
    op.execute(
        """
        UPDATE positions
        SET account_position_key = environment::text || ':' || venue || ':' || COALESCE(account_address, '') || ':' || COALESCE(symbol, '') || ':' || 'one_way'
        WHERE account_position_key = ''
        """
    )

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.add_column(sa.Column("client_order_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_submitted_orders_instrument_id_instruments",
            "instruments",
            ["instrument_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_submitted_orders_env_venue_account_instrument_status",
            ["environment", "venue", "account_address", "instrument_id", "status"],
            unique=False,
        )

    op.execute(
        """
        UPDATE submitted_orders o
        SET instrument_id = s.instrument_id
        FROM symbols s
        WHERE o.symbol_id = s.id
        """
    )

    with op.batch_alter_table("fills") as batch_op:
        batch_op.add_column(sa.Column("venue_fill_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_fills_instrument_id_instruments", "instruments", ["instrument_id"], ["id"])
        batch_op.create_index(
            "ix_fills_env_venue_account_instrument_filled_at",
            ["environment", "venue", "account_address", "instrument_id", "filled_at"],
            unique=False,
        )

    op.execute(
        """
        UPDATE fills f
        SET instrument_id = s.instrument_id
        FROM symbols s
        WHERE f.symbol_id = s.id
        """
    )

    op.create_table(
        "market_data_checkpoints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("last_requested_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_requested_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_persisted_open_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_persisted_close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_sync_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overlap_bars", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], name="fk_market_data_checkpoints_instrument_id_instruments"),
    )
    op.create_index(
        "ix_market_data_checkpoints_env_venue_symbol_timeframe",
        "market_data_checkpoints",
        ["environment", "venue", "symbol", "timeframe"],
        unique=True,
    )

    op.create_table(
        "position_attribution_overlays",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("overlay_id", sa.String(length=64), nullable=False),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("position_id", sa.String(length=64), nullable=False),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("attributed_quantity", sa.Numeric(24, 12), nullable=False),
        sa.Column("attributed_notional", sa.Numeric(24, 12), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_position_attribution_overlays_position_sleeve_as_of",
        "position_attribution_overlays",
        ["position_id", "sleeve_id", "as_of"],
    )
    op.create_index(
        "ix_position_attribution_overlays_overlay_id",
        "position_attribution_overlays",
        ["overlay_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_position_attribution_overlays_overlay_id", table_name="position_attribution_overlays")
    op.drop_index(
        "ix_position_attribution_overlays_position_sleeve_as_of",
        table_name="position_attribution_overlays",
    )
    op.drop_table("position_attribution_overlays")

    op.drop_index(
        "ix_market_data_checkpoints_env_venue_symbol_timeframe",
        table_name="market_data_checkpoints",
    )
    op.drop_table("market_data_checkpoints")

    op.drop_index(
        "ix_fills_env_venue_account_instrument_filled_at",
        table_name="fills",
    )
    with op.batch_alter_table("fills") as batch_op:
        batch_op.drop_constraint("fk_fills_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("venue_fill_id")

    op.drop_index(
        "ix_submitted_orders_env_venue_account_instrument_status",
        table_name="submitted_orders",
    )
    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.drop_constraint("fk_submitted_orders_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("client_order_id")

    op.drop_index(
        "ix_positions_env_venue_account_instrument_status",
        table_name="positions",
    )
    with op.batch_alter_table("positions") as batch_op:
        batch_op.drop_constraint("fk_positions_instrument_id_instruments", type_="foreignkey")
        batch_op.alter_column("sleeve_id", existing_type=sa.String(length=32), nullable=False)
        batch_op.drop_column("attribution_status")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("account_position_key")
        batch_op.drop_column("exchange_position_key")

    with op.batch_alter_table("candles") as batch_op:
        batch_op.drop_index("ix_candles_env_venue_symbol_timeframe_open_time")
        batch_op.drop_constraint("fk_candles_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("instrument_id")
        batch_op.create_index(
            "ix_candles_venue_symbol_timeframe_open_time",
            ["venue", "symbol", "timeframe", "open_time"],
            unique=True,
        )

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.drop_index("ix_symbols_instrument_id")
        batch_op.drop_index("ix_symbols_venue_exchange_symbol")
        batch_op.drop_constraint("fk_symbols_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("settlement_asset")
        batch_op.drop_column("product_type")
        batch_op.drop_column("market_type")
        batch_op.drop_column("venue_asset_id")
        batch_op.drop_column("instrument_id")

    op.drop_index("ix_instruments_market_product_base_quote_settlement", table_name="instruments")
    op.drop_index("ix_instruments_instrument_id", table_name="instruments")
    op.drop_table("instruments")

    attribution_status_enum = postgresql.ENUM(
        "unassigned", "partial", "fully_attributed", name="attributionstatus", create_type=False
    )
    product_type_enum = postgresql.ENUM(
        "linear", "inverse", "spot", name="producttype", create_type=False
    )
    market_type_enum = postgresql.ENUM(
        "spot", "perpetual", "future", "option", name="markettype", create_type=False
    )
    attribution_status_enum.drop(op.get_bind(), checkfirst=True)
    product_type_enum.drop(op.get_bind(), checkfirst=True)
    market_type_enum.drop(op.get_bind(), checkfirst=True)
