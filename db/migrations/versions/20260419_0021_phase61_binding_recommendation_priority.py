"""Phase 6.1 binding recommendation priority.

Revision ID: 20260419_0021
Revises: 20260419_0020
Create Date: 2026-04-19 13:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260419_0021"
down_revision = "20260419_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mandate_account_bindings",
        sa.Column("target_recommendation_priority", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mandate_account_bindings", "target_recommendation_priority")
