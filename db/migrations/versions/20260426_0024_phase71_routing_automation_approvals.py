"""Phase 7.1 routing automation approval gates.

Revision ID: 20260426_0024
Revises: 20260423_0023
Create Date: 2026-04-26 15:08:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260426_0024"
down_revision = "20260423_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "routing_automation_approvals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "environment",
            postgresql.ENUM(name="environment", create_type=False),
            nullable=False,
        ),
        sa.Column("approval_id", sa.String(length=64), nullable=False),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=False),
        sa.Column("action_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approved_by", sa.String(length=128), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_name", sa.String(length=128), nullable=False),
        sa.Column("automation_mode", sa.String(length=64), nullable=False),
        sa.Column("route_readiness_audit_id", sa.String(length=64), nullable=True),
        sa.Column("routing_assessment_id", sa.String(length=64), nullable=True),
        sa.Column("routing_target_recommendation_id", sa.String(length=64), nullable=True),
        sa.Column("routing_target_choice_id", sa.String(length=64), nullable=True),
        sa.Column("intent_id", sa.String(length=64), nullable=True),
        sa.Column("readiness_evaluation_id", sa.String(length=64), nullable=True),
        sa.Column("submitted_order_id", sa.String(length=64), nullable=True),
        sa.Column("selected_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("selected_binding_key", sa.String(length=128), nullable=True),
        sa.Column("selected_venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("selected_venue_account_key", sa.String(length=128), nullable=True),
        sa.Column("selected_venue", sa.String(length=32), nullable=True),
        sa.Column("selected_exchange_symbol", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(length=128), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_by", sa.String(length=128), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("boundary_flags_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("policy_snapshot_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("lineage_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_id", name="uq_routing_automation_approvals_approval_id"),
    )
    op.create_index(
        "ix_routing_automation_approvals_approval_id",
        "routing_automation_approvals",
        ["approval_id"],
        unique=True,
    )
    op.create_index(
        "ix_routing_automation_approvals_desired_action_created",
        "routing_automation_approvals",
        ["environment", "desired_trade_key", "action_name", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_automation_approvals_status_created",
        "routing_automation_approvals",
        ["environment", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_automation_approvals_target_choice",
        "routing_automation_approvals",
        ["routing_target_choice_id", "action_name"],
        unique=False,
    )
    op.create_index(
        "ix_routing_automation_approvals_intent",
        "routing_automation_approvals",
        ["intent_id", "action_name"],
        unique=False,
    )
    with op.batch_alter_table("routing_automation_approvals") as batch_op:
        batch_op.alter_column("reason_codes_json", server_default=None)
        batch_op.alter_column("boundary_flags_json", server_default=None)
        batch_op.alter_column("policy_snapshot_json", server_default=None)
        batch_op.alter_column("lineage_json", server_default=None)
        batch_op.alter_column("provenance_json", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_routing_automation_approvals_intent", table_name="routing_automation_approvals")
    op.drop_index("ix_routing_automation_approvals_target_choice", table_name="routing_automation_approvals")
    op.drop_index("ix_routing_automation_approvals_status_created", table_name="routing_automation_approvals")
    op.drop_index(
        "ix_routing_automation_approvals_desired_action_created",
        table_name="routing_automation_approvals",
    )
    op.drop_index("ix_routing_automation_approvals_approval_id", table_name="routing_automation_approvals")
    op.drop_table("routing_automation_approvals")
