"""Phase 4A venue-safe symbol uniqueness for multi-product venues.

Revision ID: 20260405_0009
Revises: 20260405_0008
Create Date: 2026-04-05 15:35:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260405_0009"
down_revision = "20260405_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_symbols_venue_symbol", table_name="symbols")
    op.create_index("ix_symbols_venue_symbol", "symbols", ["venue", "symbol"], unique=False)
    op.create_index(
        "ix_symbols_venue_market_identity",
        "symbols",
        ["venue", "symbol", "market_type", "product_type", "quote_asset", "settlement_asset"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_symbols_venue_market_identity", table_name="symbols")
    op.drop_index("ix_symbols_venue_symbol", table_name="symbols")
    op.create_index("ix_symbols_venue_symbol", "symbols", ["venue", "symbol"], unique=True)
