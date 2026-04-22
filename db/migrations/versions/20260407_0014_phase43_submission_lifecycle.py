"""Phase 4.3 submission lifecycle states for child intents.

Revision ID: 20260407_0014
Revises: 20260406_0013
Create Date: 2026-04-07 09:40:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260407_0014"
down_revision = "20260406_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE orderintentstatus ADD VALUE IF NOT EXISTS 'submitted'")
    op.execute("ALTER TYPE orderintentstatus ADD VALUE IF NOT EXISTS 'submission_failed'")


def downgrade() -> None:
    # PostgreSQL enum values are intentionally left in place. Removing them
    # would require rewriting dependent columns and provides little rollback
    # value for this phase transition.
    pass
