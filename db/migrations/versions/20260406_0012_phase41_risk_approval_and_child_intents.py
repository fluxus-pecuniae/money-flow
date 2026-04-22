"""Phase 4.1 risk approval and selective child-intent preparation.

Revision ID: 20260406_0012
Revises: 20260406_0011
Create Date: 2026-04-06 13:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_0012"
down_revision = "20260406_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TYPE orderintentstatus ADD VALUE IF NOT EXISTS 'prepared'")
    op.execute("ALTER TYPE mandatedesiredtradestatus ADD VALUE IF NOT EXISTS 'rejected'")
    op.execute("ALTER TYPE mandatedesiredtradestatus ADD VALUE IF NOT EXISTS 'routing_required'")

    risk_evaluation_outcome_type = postgresql.ENUM(
        "approved_desired_trade",
        "rejected_desired_trade",
        "no_desired_trade",
        "routing_required",
        "invalid_input",
        name="riskevaluationoutcome",
    )
    risk_evaluation_outcome_type.create(bind, checkfirst=True)

    risk_evaluation_outcome = postgresql.ENUM(
        "approved_desired_trade",
        "rejected_desired_trade",
        "no_desired_trade",
        "routing_required",
        "invalid_input",
        name="riskevaluationoutcome",
        create_type=False,
    )
    order_intent_status = postgresql.ENUM(name="orderintentstatus", create_type=False)
    mandate_desired_trade_status = postgresql.ENUM(name="mandatedesiredtradestatus", create_type=False)
    decision_action = postgresql.ENUM(name="decisionaction", create_type=False)
    trade_target_scope = postgresql.ENUM(name="tradetargetscope", create_type=False)
    strategy_decision_status = postgresql.ENUM(name="strategydecisionstatus", create_type=False)

    op.create_table(
        "risk_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("risk_evaluation_id", sa.String(length=64), nullable=False),
        sa.Column("risk_evaluation_key", sa.String(length=128), nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=False),
        sa.Column("decision_evaluation_key", sa.String(length=128), nullable=True),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=True),
        sa.Column("market_data_source_policy_ref_id", sa.String(length=36), nullable=True),
        sa.Column("planning_source_venue", sa.String(length=32), nullable=True),
        sa.Column("component_key", sa.String(length=64), nullable=True),
        sa.Column("target_scope", trade_target_scope, nullable=True),
        sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("binding_key", sa.String(length=128), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("action", decision_action, nullable=False),
        sa.Column("decision_status", strategy_decision_status, nullable=False),
        sa.Column("outcome", risk_evaluation_outcome, nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=True),
        sa.Column("desired_trade_status", mandate_desired_trade_status, nullable=True),
        sa.Column("child_intent_ref_id", sa.String(length=36), nullable=True),
        sa.Column("child_intent_id", sa.String(length=64), nullable=True),
        sa.Column("child_intent_status", order_intent_status, nullable=True),
        sa.Column("policy_checks", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["market_data_source_policy_ref_id"], ["mandate_market_data_source_policies.id"]),
        sa.ForeignKeyConstraint(["mandate_account_binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["child_intent_ref_id"], ["order_intents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_evaluations_env_outcome_evaluated_at",
        "risk_evaluations",
        ["environment", "outcome", "evaluated_at"],
        unique=False,
    )
    op.create_index(
        "ix_risk_evaluations_env_mandate_evaluated_at",
        "risk_evaluations",
        ["environment", "strategy_mandate_ref_id", "evaluated_at"],
        unique=False,
    )
    op.create_index("ix_risk_evaluations_risk_evaluation_id", "risk_evaluations", ["risk_evaluation_id"], unique=True)
    op.create_index(
        "ix_risk_evaluations_risk_evaluation_key",
        "risk_evaluations",
        ["risk_evaluation_key"],
        unique=True,
    )

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.add_column(sa.Column("status_reason_code", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("status_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(
            "ix_mandate_desired_trades_status_reason_code",
            ["status_reason_code"],
            unique=False,
        )

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("action", decision_action, nullable=True))
        batch_op.add_column(sa.Column("binding_key", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json"))
        )
        batch_op.create_index("ix_order_intents_action", ["action"], unique=False)
        batch_op.create_index("ix_order_intents_binding_key", ["binding_key"], unique=False)

    bind.execute(
        sa.text(
            """
            UPDATE order_intents
            SET action = COALESCE(
                    (SELECT mdt.action FROM mandate_desired_trades AS mdt WHERE mdt.id = order_intents.mandate_desired_trade_ref_id),
                    (SELECT sd.action FROM strategy_decisions AS sd WHERE sd.decision_id = order_intents.decision_id)
                ),
                binding_key = COALESCE(
                    (SELECT mdt.binding_key FROM mandate_desired_trades AS mdt WHERE mdt.id = order_intents.mandate_desired_trade_ref_id),
                    (SELECT sd.binding_key FROM strategy_decisions AS sd WHERE sd.decision_id = order_intents.decision_id)
                ),
                reduce_only = CASE
                    WHEN COALESCE(
                        (SELECT mdt.action FROM mandate_desired_trades AS mdt WHERE mdt.id = order_intents.mandate_desired_trade_ref_id),
                        (SELECT sd.action FROM strategy_decisions AS sd WHERE sd.decision_id = order_intents.decision_id)
                    ) IN ('reduce', 'close') THEN TRUE
                    ELSE FALSE
                END,
                provenance = CAST(:payload AS JSON)
            """
        ),
        {"payload": "{}"},
    )

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.alter_column("reduce_only", server_default=None)
        batch_op.alter_column("provenance", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_binding_key")
        batch_op.drop_index("ix_order_intents_action")
        batch_op.drop_column("provenance")
        batch_op.drop_column("reduce_only")
        batch_op.drop_column("binding_key")
        batch_op.drop_column("action")

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.drop_index("ix_mandate_desired_trades_status_reason_code")
        batch_op.drop_column("rejected_at")
        batch_op.drop_column("status_message")
        batch_op.drop_column("status_reason_code")

    op.drop_index("ix_risk_evaluations_risk_evaluation_key", table_name="risk_evaluations")
    op.drop_index("ix_risk_evaluations_risk_evaluation_id", table_name="risk_evaluations")
    op.drop_index("ix_risk_evaluations_env_mandate_evaluated_at", table_name="risk_evaluations")
    op.drop_index("ix_risk_evaluations_env_outcome_evaluated_at", table_name="risk_evaluations")
    op.drop_table("risk_evaluations")

    postgresql.ENUM(name="riskevaluationoutcome").drop(op.get_bind(), checkfirst=True)
