"""Phase 4.0.1 mandate desired trade and child-intent boundary.

Revision ID: 20260405_0010
Revises: 20260405_0009
Create Date: 2026-04-05 18:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260405_0010"
down_revision = "20260405_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    mandate_desired_trade_status_type = postgresql.ENUM(
        "draft",
        "approved",
        "routing_pending",
        "routed",
        "canceled",
        name="mandatedesiredtradestatus",
    )
    trade_target_scope_type = postgresql.ENUM("mandate", "binding", name="tradetargetscope")
    mandate_desired_trade_status_type.create(bind, checkfirst=True)
    trade_target_scope_type.create(bind, checkfirst=True)
    mandate_desired_trade_status = postgresql.ENUM(
        "draft",
        "approved",
        "routing_pending",
        "routed",
        "canceled",
        name="mandatedesiredtradestatus",
        create_type=False,
    )
    trade_target_scope = postgresql.ENUM(
        "mandate",
        "binding",
        name="tradetargetscope",
        create_type=False,
    )

    op.create_table(
        "mandate_desired_trades",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "environment",
            postgresql.ENUM(name="environment", create_type=False),
            nullable=False,
        ),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=False),
        sa.Column("evaluated_state_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=True),
        sa.Column("binding_key", sa.String(length=128), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column(
            "family",
            postgresql.ENUM(name="strategyfamily", create_type=False),
            nullable=False,
        ),
        sa.Column("component_key", sa.String(length=64), nullable=True),
        sa.Column("target_scope", trade_target_scope, nullable=False),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column(
            "action",
            postgresql.ENUM(name="decisionaction", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "side",
            postgresql.ENUM(name="orderside", create_type=False),
            nullable=True,
        ),
        sa.Column("desired_quantity", sa.Numeric(24, 12), nullable=True),
        sa.Column("desired_notional", sa.Numeric(24, 12), nullable=True),
        sa.Column("source_decision_ids_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("status", mandate_desired_trade_status, nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["mandate_account_binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mandate_desired_trades_env_mandate_status_created_at",
        "mandate_desired_trades",
        ["environment", "strategy_mandate_ref_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_mandate_desired_trades_env_instrument_created_at",
        "mandate_desired_trades",
        ["environment", "instrument_ref_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_mandate_desired_trades_desired_trade_key",
        "mandate_desired_trades",
        ["desired_trade_key"],
        unique=True,
    )
    op.create_index(
        "ix_mandate_desired_trades_evaluated_state_fingerprint",
        "mandate_desired_trades",
        ["evaluated_state_fingerprint"],
        unique=False,
    )

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("mandate_desired_trade_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("desired_trade_key", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key(
            "fk_order_intents_mandate_desired_trade_ref_id",
            "mandate_desired_trades",
            ["mandate_desired_trade_ref_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_order_intents_mandate_desired_trade_ref_id",
            ["mandate_desired_trade_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_order_intents_desired_trade_key", ["desired_trade_key"], unique=False)

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.alter_column("source_decision_ids_json", server_default=None)
        batch_op.alter_column("provenance", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    mandate_desired_trade_status = postgresql.ENUM(
        "draft",
        "approved",
        "routing_pending",
        "routed",
        "canceled",
        name="mandatedesiredtradestatus",
    )
    trade_target_scope = postgresql.ENUM("mandate", "binding", name="tradetargetscope")

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_desired_trade_key")
        batch_op.drop_index("ix_order_intents_mandate_desired_trade_ref_id")
        batch_op.drop_constraint("fk_order_intents_mandate_desired_trade_ref_id", type_="foreignkey")
        batch_op.drop_column("desired_trade_key")
        batch_op.drop_column("mandate_desired_trade_ref_id")

    op.drop_index(
        "ix_mandate_desired_trades_evaluated_state_fingerprint",
        table_name="mandate_desired_trades",
    )
    op.drop_index(
        "ix_mandate_desired_trades_desired_trade_key",
        table_name="mandate_desired_trades",
    )
    op.drop_index(
        "ix_mandate_desired_trades_env_instrument_created_at",
        table_name="mandate_desired_trades",
    )
    op.drop_index(
        "ix_mandate_desired_trades_env_mandate_status_created_at",
        table_name="mandate_desired_trades",
    )
    op.drop_table("mandate_desired_trades")

    trade_target_scope.drop(bind, checkfirst=True)
    mandate_desired_trade_status.drop(bind, checkfirst=True)
