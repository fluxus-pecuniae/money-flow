"""Phase 3 indicator and strategy decision layer."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260403_0004"
down_revision = "20260402_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    timeframe_enum = postgresql.ENUM(
        "1m", "5m", "15m", "1h", "4h", "1d", name="timeframe", create_type=False
    )
    signal_type_enum = postgresql.ENUM(
        "entry",
        "exit",
        "rebalance",
        "risk_reduction",
        "no_trade",
        name="signaltype",
        create_type=False,
    )
    decision_action_enum = postgresql.ENUM(
        "noop", "open", "add", "reduce", "close", name="decisionaction", create_type=False
    )
    strategy_decision_status_enum = postgresql.ENUM(
        "proposed",
        "no_trade",
        "invalid",
        name="strategydecisionstatus",
        create_type=False,
    )
    strategy_family_enum = postgresql.ENUM(
        "money_flow",
        name="strategyfamily",
        create_type=False,
    )
    strategy_decision_status_enum.create(op.get_bind(), checkfirst=True)
    strategy_family_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TYPE signaltype ADD VALUE IF NOT EXISTS 'no_trade'")

    op.drop_index("ix_indicator_snapshots_symbol_timeframe_as_of", table_name="indicator_snapshots")
    with op.batch_alter_table("indicator_snapshots") as batch_op:
        batch_op.add_column(sa.Column("venue", sa.String(length=32), nullable=False, server_default="hyperliquid"))
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_indicator_snapshots_instrument_id_instruments",
            "instruments",
            ["instrument_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_indicator_snapshots_env_instrument_timeframe_as_of",
            ["environment", "instrument_id", "symbol", "timeframe", "as_of"],
            unique=True,
        )

    op.execute(
        """
        UPDATE indicator_snapshots s
        SET
            venue = sym.venue,
            instrument_id = sym.instrument_id
        FROM symbols sym
        WHERE s.symbol_id = sym.id
        """
    )

    op.drop_index("ix_signal_events_sleeve_symbol_generated_at", table_name="signal_events")
    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.add_column(
            sa.Column("family", strategy_family_enum, nullable=False, server_default="money_flow")
        )
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("reason_code", sa.String(length=64), nullable=True))
        batch_op.alter_column(
            "signal_type",
            existing_type=signal_type_enum,
            type_=signal_type_enum,
            existing_nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_signal_events_instrument_id_instruments",
            "instruments",
            ["instrument_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_signal_events_family_sleeve_symbol_generated_at",
            ["family", "sleeve_id", "symbol", "generated_at"],
            unique=False,
        )

    op.execute(
        """
        UPDATE signal_events s
        SET instrument_id = sym.instrument_id
        FROM symbols sym
        WHERE s.symbol_id = sym.id
        """
    )

    op.drop_index("ix_strategy_decisions_sleeve_symbol_decided_at", table_name="strategy_decisions")
    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.add_column(
            sa.Column("family", strategy_family_enum, nullable=False, server_default="money_flow")
        )
        batch_op.add_column(sa.Column("instrument_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "status",
                strategy_decision_status_enum,
                nullable=False,
                server_default="proposed",
            )
        )
        batch_op.add_column(sa.Column("reason_code", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("features", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
        batch_op.alter_column(
            "action",
            existing_type=decision_action_enum,
            type_=decision_action_enum,
            existing_nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_strategy_decisions_instrument_id_instruments",
            "instruments",
            ["instrument_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_strategy_decisions_family_sleeve_symbol_decided_at",
            ["family", "sleeve_id", "symbol", "decided_at"],
            unique=False,
        )

    op.execute(
        """
        UPDATE strategy_decisions s
        SET instrument_id = sym.instrument_id
        FROM symbols sym
        WHERE s.symbol_id = sym.id
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_decisions_family_sleeve_symbol_decided_at",
        table_name="strategy_decisions",
    )
    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.drop_constraint("fk_strategy_decisions_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("features")
        batch_op.drop_column("reason_code")
        batch_op.drop_column("status")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("family")
    op.create_index(
        "ix_strategy_decisions_sleeve_symbol_decided_at",
        "strategy_decisions",
        ["sleeve_id", "symbol", "decided_at"],
    )

    op.drop_index(
        "ix_signal_events_family_sleeve_symbol_generated_at",
        table_name="signal_events",
    )
    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.drop_constraint("fk_signal_events_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("reason_code")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("family")
    op.create_index(
        "ix_signal_events_sleeve_symbol_generated_at",
        "signal_events",
        ["sleeve_id", "symbol", "generated_at"],
    )

    op.drop_index(
        "ix_indicator_snapshots_env_instrument_timeframe_as_of",
        table_name="indicator_snapshots",
    )
    with op.batch_alter_table("indicator_snapshots") as batch_op:
        batch_op.drop_constraint("fk_indicator_snapshots_instrument_id_instruments", type_="foreignkey")
        batch_op.drop_column("instrument_id")
        batch_op.drop_column("venue")
    op.create_index(
        "ix_indicator_snapshots_symbol_timeframe_as_of",
        "indicator_snapshots",
        ["symbol", "timeframe", "as_of"],
        unique=True,
    )

    strategy_family_enum = postgresql.ENUM("money_flow", name="strategyfamily", create_type=False)
    strategy_decision_status_enum = postgresql.ENUM(
        "proposed",
        "no_trade",
        "invalid",
        name="strategydecisionstatus",
        create_type=False,
    )
    strategy_family_enum.drop(op.get_bind(), checkfirst=True)
    strategy_decision_status_enum.drop(op.get_bind(), checkfirst=True)
