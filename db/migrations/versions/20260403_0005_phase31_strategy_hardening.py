"""Phase 3.1 strategy hardening.

Revision ID: 20260403_0005
Revises: 20260403_0004
Create Date: 2026-04-03 18:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_0005"
down_revision = "20260403_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE decisionaction ADD VALUE IF NOT EXISTS 'hold'")

    op.alter_column("instruments", "instrument_id", new_column_name="instrument_key")
    op.execute("ALTER INDEX IF EXISTS ix_instruments_instrument_id RENAME TO ix_instruments_instrument_key")

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.alter_column("instrument_id", new_column_name="instrument_ref_id")
        batch_op.add_column(
            sa.Column("is_strategy_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true"))
        )
        batch_op.add_column(
            sa.Column("is_trading_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true"))
        )
    op.execute(
        """
        UPDATE symbols
        SET is_strategy_eligible = CASE WHEN is_builder_deployed THEN FALSE ELSE TRUE END,
            is_trading_eligible = CASE WHEN is_builder_deployed THEN FALSE ELSE TRUE END
        """
    )

    op.alter_column("candles", "instrument_id", new_column_name="instrument_ref_id")

    with op.batch_alter_table("indicator_snapshots") as batch_op:
        batch_op.alter_column("instrument_id", new_column_name="instrument_ref_id")
        batch_op.drop_index("ix_indicator_snapshots_env_instrument_timeframe_as_of")
        batch_op.create_index(
            "ix_indicator_snapshots_env_instrument_timeframe_as_of",
            ["environment", "venue", "instrument_ref_id", "symbol", "timeframe", "as_of"],
            unique=True,
        )

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.alter_column("instrument_id", new_column_name="instrument_ref_id")
        batch_op.add_column(sa.Column("evaluation_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.create_index("ix_signal_events_evaluation_key", ["evaluation_key"], unique=True)
    op.execute("UPDATE signal_events SET evaluation_key = signal_id WHERE evaluation_key IS NULL")
    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.alter_column("evaluation_key", nullable=False)

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.alter_column("instrument_id", new_column_name="instrument_ref_id")
        batch_op.add_column(sa.Column("evaluation_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.create_index("ix_strategy_decisions_evaluation_key", ["evaluation_key"], unique=True)
    op.execute("UPDATE strategy_decisions SET evaluation_key = decision_id WHERE evaluation_key IS NULL")
    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.alter_column("evaluation_key", nullable=False)

    op.alter_column("positions", "instrument_id", new_column_name="instrument_ref_id")

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("instrument_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("instrument_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_order_intents_instrument_ref_id_instruments",
            "instruments",
            ["instrument_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_order_intents_instrument_key", ["instrument_key"], unique=False)
        batch_op.create_index("ix_order_intents_instrument_ref_id", ["instrument_ref_id"], unique=False)
    op.execute(
        """
        UPDATE order_intents oi
        SET instrument_ref_id = s.instrument_ref_id,
            instrument_key = i.instrument_key
        FROM symbols s
        LEFT JOIN instruments i ON i.id = s.instrument_ref_id
        WHERE oi.symbol_id = s.id
        """
    )

    op.alter_column("submitted_orders", "instrument_id", new_column_name="instrument_ref_id")
    op.alter_column("fills", "instrument_id", new_column_name="instrument_ref_id")
    op.alter_column("market_data_checkpoints", "instrument_id", new_column_name="instrument_ref_id")

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.alter_column("is_strategy_eligible", server_default=None)
        batch_op.alter_column("is_trading_eligible", server_default=None)
    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.alter_column("provenance", server_default=None)
    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.alter_column("provenance", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("market_data_checkpoints") as batch_op:
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")
    with op.batch_alter_table("fills") as batch_op:
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")
    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_instrument_ref_id")
        batch_op.drop_index("ix_order_intents_instrument_key")
        batch_op.drop_constraint("fk_order_intents_instrument_ref_id_instruments", type_="foreignkey")
        batch_op.drop_column("instrument_ref_id")
        batch_op.drop_column("instrument_key")

    with op.batch_alter_table("positions") as batch_op:
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.drop_index("ix_strategy_decisions_evaluation_key")
        batch_op.drop_column("provenance")
        batch_op.drop_column("evaluation_key")
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.drop_index("ix_signal_events_evaluation_key")
        batch_op.drop_column("provenance")
        batch_op.drop_column("evaluation_key")
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("indicator_snapshots") as batch_op:
        batch_op.drop_index("ix_indicator_snapshots_env_instrument_timeframe_as_of")
        batch_op.create_index(
            "ix_indicator_snapshots_env_instrument_timeframe_as_of",
            ["environment", "instrument_id", "symbol", "timeframe", "as_of"],
            unique=True,
        )
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("symbols") as batch_op:
        batch_op.drop_column("is_trading_eligible")
        batch_op.drop_column("is_strategy_eligible")
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    with op.batch_alter_table("candles") as batch_op:
        batch_op.alter_column("instrument_ref_id", new_column_name="instrument_id")

    op.execute("ALTER INDEX IF EXISTS ix_instruments_instrument_key RENAME TO ix_instruments_instrument_id")
    op.alter_column("instruments", "instrument_key", new_column_name="instrument_id")
