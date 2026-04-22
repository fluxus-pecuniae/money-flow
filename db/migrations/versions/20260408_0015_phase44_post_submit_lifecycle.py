"""Phase 4.4 post-submit lifecycle and reconciliation depth."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260408_0015"
down_revision = "20260407_0014"
branch_labels = None
depends_on = None


submitted_order_reconciliation_status_enum = postgresql.ENUM(
    "not_attempted",
    "pending",
    "reconciled",
    "unavailable",
    "failed",
    name="submittedorderreconciliationstatus",
    create_type=False,
)

environment_enum = postgresql.ENUM(name="environment", create_type=False)
submitted_order_status_enum = postgresql.ENUM(name="submittedorderstatus", create_type=False)


def upgrade() -> None:
    op.execute("ALTER TYPE submittedorderstatus ADD VALUE IF NOT EXISTS 'submitted'")
    op.execute("ALTER TYPE submittedorderstatus ADD VALUE IF NOT EXISTS 'expired'")
    op.execute("ALTER TYPE submittedorderstatus ADD VALUE IF NOT EXISTS 'unknown'")
    submitted_order_reconciliation_status_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.add_column(
            sa.Column(
                "reconciliation_status",
                submitted_order_reconciliation_status_enum,
                nullable=False,
                server_default="not_attempted",
            )
        )
        batch_op.add_column(sa.Column("filled_quantity", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("average_fill_price", sa.Numeric(24, 12), nullable=True))
        batch_op.add_column(sa.Column("last_fill_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("status_reason_code", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("status_message", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "reason_codes",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'::json"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "cancelable_in_principle",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "amendable_in_principle",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.create_index(
            "ix_submitted_orders_status_reason_code",
            ["status_reason_code"],
            unique=False,
        )

    op.create_table(
        "submitted_order_lifecycle_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("submitted_order_id", sa.String(length=64), nullable=False),
        sa.Column("intent_id", sa.String(length=64), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("status", submitted_order_status_enum, nullable=False),
        sa.Column(
            "reconciliation_status",
            submitted_order_reconciliation_status_enum,
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_submitted_order_lifecycle_events_event_id",
        "submitted_order_lifecycle_events",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_so_lifecycle_env_order_obs",
        "submitted_order_lifecycle_events",
        ["environment", "submitted_order_id", "observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_so_lifecycle_env_intent_obs",
        "submitted_order_lifecycle_events",
        ["environment", "intent_id", "observed_at"],
        unique=False,
    )

    op.execute(
        """
        UPDATE submitted_orders
        SET
            reconciliation_status = CASE
                WHEN status = 'rejected' THEN 'reconciled'::submittedorderreconciliationstatus
                ELSE 'not_attempted'::submittedorderreconciliationstatus
            END,
            filled_quantity = CASE
                WHEN original_quantity IS NOT NULL AND remaining_quantity IS NOT NULL
                THEN GREATEST(original_quantity - remaining_quantity, 0)
                ELSE NULL
            END,
            cancelable_in_principle = CASE
                WHEN status IN ('new', 'acknowledged', 'partially_filled') THEN true
                ELSE false
            END,
            amendable_in_principle = CASE
                WHEN order_type = 'limit' AND status IN ('new', 'acknowledged', 'partially_filled')
                THEN true
                ELSE false
            END,
            reason_codes = '[]'::json,
            updated_at = COALESCE(acknowledged_at, submitted_at, CURRENT_TIMESTAMP)
        """
    )

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.alter_column("reconciliation_status", server_default=None)
        batch_op.alter_column("reason_codes", server_default=None)
        batch_op.alter_column("cancelable_in_principle", server_default=None)
        batch_op.alter_column("amendable_in_principle", server_default=None)
        batch_op.alter_column("updated_at", server_default=None)


def downgrade() -> None:
    op.drop_index(
        "ix_so_lifecycle_env_intent_obs",
        table_name="submitted_order_lifecycle_events",
    )
    op.drop_index(
        "ix_so_lifecycle_env_order_obs",
        table_name="submitted_order_lifecycle_events",
    )
    op.drop_index(
        "ix_submitted_order_lifecycle_events_event_id",
        table_name="submitted_order_lifecycle_events",
    )
    op.drop_table("submitted_order_lifecycle_events")

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.drop_index("ix_submitted_orders_status_reason_code")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("amendable_in_principle")
        batch_op.drop_column("cancelable_in_principle")
        batch_op.drop_column("reason_codes")
        batch_op.drop_column("status_message")
        batch_op.drop_column("status_reason_code")
        batch_op.drop_column("last_reconciled_at")
        batch_op.drop_column("last_fill_at")
        batch_op.drop_column("average_fill_price")
        batch_op.drop_column("filled_quantity")
        batch_op.drop_column("reconciliation_status")

    submitted_order_reconciliation_status_enum.drop(op.get_bind(), checkfirst=True)
