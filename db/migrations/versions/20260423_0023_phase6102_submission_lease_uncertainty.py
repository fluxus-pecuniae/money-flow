"""Phase 6.10.2 submit lease uncertainty status.

Revision ID: 20260423_0023
Revises: 20260423_0022
Create Date: 2026-04-23 06:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260423_0023"
down_revision = "20260423_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "order_intent_submission_leases",
        "status",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "order_intent_submission_leases",
        "status",
        existing_type=sa.String(length=64),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
