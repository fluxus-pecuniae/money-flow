"""Phase 6.10.1 explicit child-intent submit lease.

Revision ID: 20260423_0022
Revises: 20260419_0021
Create Date: 2026-04-23 00:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260423_0022"
down_revision = "20260419_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "order_intent_submission_leases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "environment",
            postgresql.ENUM(name="environment", create_type=False),
            nullable=False,
        ),
        sa.Column("lease_id", sa.String(length=64), nullable=False),
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "environment",
            "intent_id",
            "purpose",
            name="uq_order_intent_submission_leases_env_intent_purpose",
        ),
    )
    op.create_index(
        "ix_order_intent_submission_leases_lease_id",
        "order_intent_submission_leases",
        ["lease_id"],
        unique=True,
    )
    op.create_index(
        "ix_order_intent_submission_leases_intent_id",
        "order_intent_submission_leases",
        ["intent_id"],
        unique=False,
    )
    op.create_index(
        "ix_order_intent_submission_leases_environment",
        "order_intent_submission_leases",
        ["environment"],
        unique=False,
    )
    op.create_index(
        "ix_order_intent_submission_leases_status",
        "order_intent_submission_leases",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_order_intent_submission_leases_status_expires",
        "order_intent_submission_leases",
        ["status", "expires_at"],
        unique=False,
    )
    with op.batch_alter_table("order_intent_submission_leases") as batch_op:
        batch_op.alter_column("metadata_json", server_default=None)


def downgrade() -> None:
    op.drop_index(
        "ix_order_intent_submission_leases_status_expires",
        table_name="order_intent_submission_leases",
    )
    op.drop_index(
        "ix_order_intent_submission_leases_status",
        table_name="order_intent_submission_leases",
    )
    op.drop_index(
        "ix_order_intent_submission_leases_environment",
        table_name="order_intent_submission_leases",
    )
    op.drop_index(
        "ix_order_intent_submission_leases_intent_id",
        table_name="order_intent_submission_leases",
    )
    op.drop_index(
        "ix_order_intent_submission_leases_lease_id",
        table_name="order_intent_submission_leases",
    )
    op.drop_table("order_intent_submission_leases")
