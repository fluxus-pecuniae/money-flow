"""Phase 4.5.1 truthful intermediate cancel lifecycle statuses."""

from __future__ import annotations

from alembic import op


revision = "20260408_0016"
down_revision = "20260408_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE submittedorderstatus ADD VALUE IF NOT EXISTS 'cancel_requested'")
    op.execute("ALTER TYPE submittedorderstatus ADD VALUE IF NOT EXISTS 'cancel_acknowledged'")


def downgrade() -> None:
    # PostgreSQL enum values are intentionally left in place on downgrade.
    pass
