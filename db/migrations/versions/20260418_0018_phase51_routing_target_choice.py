"""Phase 5.1 non-executing routing target choice audit.

Revision ID: 20260418_0018
Revises: 20260417_0017
Create Date: 2026-04-18 03:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260418_0018"
down_revision = "20260417_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    routing_target_choice_status_type = postgresql.ENUM(
        "target_choice_recorded",
        "blocked_no_eligible_binding",
        "blocked_candidate_ineligible",
        "blocked_assessment_insufficient_data",
        "blocked_assessment_not_found",
        "blocked_candidate_not_found",
        "blocked_stale_assessment",
        name="routingtargetchoicestatus",
    )
    routing_target_choice_status_type.create(bind, checkfirst=True)
    routing_target_choice_status = postgresql.ENUM(
        "target_choice_recorded",
        "blocked_no_eligible_binding",
        "blocked_candidate_ineligible",
        "blocked_assessment_insufficient_data",
        "blocked_assessment_not_found",
        "blocked_candidate_not_found",
        "blocked_stale_assessment",
        name="routingtargetchoicestatus",
        create_type=False,
    )

    op.create_table(
        "routing_target_choices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("target_choice_id", sa.String(length=64), nullable=False),
        sa.Column("routing_assessment_ref_id", sa.String(length=36), nullable=True),
        sa.Column("routing_assessment_id", sa.String(length=64), nullable=False),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=True),
        sa.Column("selected_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("selected_binding_key", sa.String(length=128), nullable=True),
        sa.Column("selected_venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("selected_venue_account_key", sa.String(length=128), nullable=True),
        sa.Column("selected_venue", sa.String(length=32), nullable=True),
        sa.Column("status", routing_target_choice_status, nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("approval_note", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(length=128), nullable=True),
        sa.Column("non_executing", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["routing_assessment_ref_id"], ["routing_assessments.id"]),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["selected_binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["selected_venue_account_ref_id"], ["venue_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routing_target_choices_target_choice_id", "routing_target_choices", ["target_choice_id"], unique=True)
    op.create_index(
        "ix_routing_target_choices_assessment_created_at",
        "routing_target_choices",
        ["routing_assessment_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_target_choices_desired_trade_created_at",
        "routing_target_choices",
        ["desired_trade_key", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_target_choices_binding_status",
        "routing_target_choices",
        ["selected_binding_ref_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_routing_target_choices_status_created_at",
        "routing_target_choices",
        ["status", "created_at"],
        unique=False,
    )

    with op.batch_alter_table("routing_target_choices") as batch_op:
        batch_op.alter_column("reason_codes_json", server_default=None)
        batch_op.alter_column("missing_data_json", server_default=None)
        batch_op.alter_column("non_executing", server_default=None)
        batch_op.alter_column("provenance_json", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_routing_target_choices_status_created_at", table_name="routing_target_choices")
    op.drop_index("ix_routing_target_choices_binding_status", table_name="routing_target_choices")
    op.drop_index("ix_routing_target_choices_desired_trade_created_at", table_name="routing_target_choices")
    op.drop_index("ix_routing_target_choices_assessment_created_at", table_name="routing_target_choices")
    op.drop_index("ix_routing_target_choices_target_choice_id", table_name="routing_target_choices")
    op.drop_table("routing_target_choices")
    postgresql.ENUM(name="routingtargetchoicestatus").drop(op.get_bind(), checkfirst=True)
