"""Phase 4.2 execution readiness gating above prepared child intents.

Revision ID: 20260406_0013
Revises: 20260406_0012
Create Date: 2026-04-06 16:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_0013"
down_revision = "20260406_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    execution_readiness_outcome_type = postgresql.ENUM(
        "ineligible",
        "blocked_by_policy",
        "blocked_by_venue",
        "blocked_by_adapter",
        "blocked_by_environment",
        "phase_blocked",
        "eligible_for_submission",
        name="executionreadinessoutcome",
    )
    execution_readiness_outcome_type.create(bind, checkfirst=True)

    outcome_enum = postgresql.ENUM(
        "ineligible",
        "blocked_by_policy",
        "blocked_by_venue",
        "blocked_by_adapter",
        "blocked_by_environment",
        "phase_blocked",
        "eligible_for_submission",
        name="executionreadinessoutcome",
        create_type=False,
    )

    op.create_table(
        "execution_readiness_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("readiness_evaluation_id", sa.String(length=64), nullable=False),
        sa.Column("readiness_evaluation_key", sa.String(length=128), nullable=False),
        sa.Column("intent_ref_id", sa.String(length=36), nullable=True),
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("mandate_desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=True),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("binding_key", sa.String(length=128), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("support_level", sa.String(length=32), nullable=False),
        sa.Column("preview_status", sa.String(length=32), nullable=True),
        sa.Column("outcome", outcome_enum, nullable=False),
        sa.Column("eligible_for_submission_in_principle", sa.Boolean(), nullable=False),
        sa.Column("live_submission_phase_enabled", sa.Boolean(), nullable=False),
        sa.Column("venue_supports_order_submission", sa.Boolean(), nullable=False),
        sa.Column("adapter_supports_order_submission", sa.Boolean(), nullable=False),
        sa.Column("adapter_supports_cancel_amend", sa.Boolean(), nullable=False),
        sa.Column("submission_authorized", sa.Boolean(), nullable=False),
        sa.Column("account_connected", sa.Boolean(), nullable=False),
        sa.Column("private_state_required", sa.Boolean(), nullable=False),
        sa.Column("private_state_ready", sa.Boolean(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["intent_ref_id"], ["order_intents.id"]),
        sa.ForeignKeyConstraint(["mandate_desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["mandate_account_binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_execution_readiness_env_outcome_evaluated_at",
        "execution_readiness_evaluations",
        ["environment", "outcome", "evaluated_at"],
        unique=False,
    )
    op.create_index(
        "ix_execution_readiness_env_venue_evaluated_at",
        "execution_readiness_evaluations",
        ["environment", "venue", "evaluated_at"],
        unique=False,
    )
    op.create_index(
        "ix_execution_readiness_readiness_evaluation_id",
        "execution_readiness_evaluations",
        ["readiness_evaluation_id"],
        unique=True,
    )
    op.create_index(
        "ix_execution_readiness_readiness_evaluation_key",
        "execution_readiness_evaluations",
        ["readiness_evaluation_key"],
        unique=True,
    )

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.create_index(
            "ix_order_intents_env_desired_trade_created_at",
            ["environment", "desired_trade_key", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_env_desired_trade_created_at")

    op.drop_index("ix_execution_readiness_readiness_evaluation_key", table_name="execution_readiness_evaluations")
    op.drop_index("ix_execution_readiness_readiness_evaluation_id", table_name="execution_readiness_evaluations")
    op.drop_index("ix_execution_readiness_env_venue_evaluated_at", table_name="execution_readiness_evaluations")
    op.drop_index("ix_execution_readiness_env_outcome_evaluated_at", table_name="execution_readiness_evaluations")
    op.drop_table("execution_readiness_evaluations")

    postgresql.ENUM(name="executionreadinessoutcome").drop(op.get_bind(), checkfirst=True)
