"""Phase 3.5 cleanup of legacy deployment-era schema.

Revision ID: 20260405_0008
Revises: 20260405_0007
Create Date: 2026-04-05 11:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260405_0008"
down_revision = "20260405_0007"
branch_labels = None
depends_on = None


strategy_family_enum = postgresql.ENUM(name="strategyfamily", create_type=False)
timeframe_enum = postgresql.ENUM(name="timeframe", create_type=False)


def upgrade() -> None:
    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_strategy_deployment_ref_id")
        batch_op.drop_column("strategy_deployment_ref_id")

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.drop_index("ix_strategy_decisions_deployment_key")
        batch_op.drop_index("ix_strategy_decisions_strategy_deployment_ref_id")
        batch_op.drop_column("deployment_key")
        batch_op.drop_column("strategy_deployment_ref_id")

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.drop_index("ix_signal_events_deployment_key")
        batch_op.drop_index("ix_signal_events_strategy_deployment_ref_id")
        batch_op.drop_column("deployment_key")
        batch_op.drop_column("strategy_deployment_ref_id")

    op.drop_index("ix_sleeve_deployment_configs_deployment_sleeve", table_name="sleeve_deployment_configs")
    op.drop_table("sleeve_deployment_configs")

    op.drop_index("ix_strategy_deployments_account_family_enabled", table_name="strategy_deployments")
    op.drop_index("ix_strategy_deployments_deployment_key", table_name="strategy_deployments")
    op.drop_table("strategy_deployments")


def downgrade() -> None:
    op.create_table(
        "strategy_deployments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deployment_key", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column(
            "venue_account_ref_id",
            sa.String(length=36),
            sa.ForeignKey("venue_accounts.id"),
            nullable=False,
        ),
        sa.Column("family", strategy_family_enum, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "allow_builder_deployed_for_strategy",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "allow_builder_deployed_for_trading",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_strategy_deployments_deployment_key", "strategy_deployments", ["deployment_key"], unique=True)
    op.create_index(
        "ix_strategy_deployments_account_family_enabled",
        "strategy_deployments",
        ["venue_account_ref_id", "family", "enabled"],
        unique=False,
    )

    op.create_table(
        "sleeve_deployment_configs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "strategy_deployment_ref_id",
            sa.String(length=36),
            sa.ForeignKey("strategy_deployments.id"),
            nullable=False,
        ),
        sa.Column("sleeve_id", sa.String(length=32), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capital_allocation_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("max_open_risk_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("strategy_overrides", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_sleeve_deployment_configs_deployment_sleeve",
        "sleeve_deployment_configs",
        ["strategy_deployment_ref_id", "sleeve_id"],
        unique=True,
    )

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("deployment_key", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_signal_events_strategy_deployment_ref_id", ["strategy_deployment_ref_id"], unique=False)
        batch_op.create_index("ix_signal_events_deployment_key", ["deployment_key"], unique=False)

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("deployment_key", sa.String(length=128), nullable=True))
        batch_op.create_index(
            "ix_strategy_decisions_strategy_deployment_ref_id",
            ["strategy_deployment_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_strategy_decisions_deployment_key", ["deployment_key"], unique=False)

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_order_intents_strategy_deployment_ref_id", ["strategy_deployment_ref_id"], unique=False)
