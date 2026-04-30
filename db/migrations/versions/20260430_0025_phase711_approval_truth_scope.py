"""Phase 7.1.1 routing automation approval truth scope.

Revision ID: 20260430_0025
Revises: 20260426_0024
Create Date: 2026-04-30 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260430_0025"
down_revision = "20260426_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("routing_automation_approvals") as batch_op:
        batch_op.add_column(sa.Column("lineage_fingerprint", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("approval_scope_key", sa.String(length=64), nullable=True))

    op.create_index(
        "ix_routing_automation_approvals_lineage_fingerprint",
        "routing_automation_approvals",
        ["lineage_fingerprint"],
        unique=False,
    )
    op.create_index(
        "ix_routing_automation_approvals_approval_scope_key",
        "routing_automation_approvals",
        ["approval_scope_key"],
        unique=False,
    )
    op.create_index(
        "ux_routing_automation_approvals_active_scope",
        "routing_automation_approvals",
        ["environment", "desired_trade_key", "action_name", "approval_scope_key"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND approval_scope_key IS NOT NULL"),
        sqlite_where=sa.text("status = 'active' AND approval_scope_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_routing_automation_approvals_active_scope",
        table_name="routing_automation_approvals",
    )
    op.drop_index(
        "ix_routing_automation_approvals_approval_scope_key",
        table_name="routing_automation_approvals",
    )
    op.drop_index(
        "ix_routing_automation_approvals_lineage_fingerprint",
        table_name="routing_automation_approvals",
    )
    with op.batch_alter_table("routing_automation_approvals") as batch_op:
        batch_op.drop_column("approval_scope_key")
        batch_op.drop_column("lineage_fingerprint")
