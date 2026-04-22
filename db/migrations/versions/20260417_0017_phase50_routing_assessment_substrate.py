"""Phase 5.0 non-executing routing assessment substrate.

Revision ID: 20260417_0017
Revises: 20260408_0016
Create Date: 2026-04-17 02:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260417_0017"
down_revision = "20260408_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    routing_assessment_decision_status_type = postgresql.ENUM(
        "assessment_only",
        "no_eligible_bindings",
        "insufficient_data",
        name="routingassessmentdecisionstatus",
    )
    routing_candidate_eligibility_status_type = postgresql.ENUM(
        "eligible_for_future_selection",
        "ineligible_for_future_selection",
        name="routingcandidateeligibilitystatus",
    )
    routing_assessment_decision_status_type.create(bind, checkfirst=True)
    routing_candidate_eligibility_status_type.create(bind, checkfirst=True)

    routing_assessment_decision_status = postgresql.ENUM(
        "assessment_only",
        "no_eligible_bindings",
        "insufficient_data",
        name="routingassessmentdecisionstatus",
        create_type=False,
    )
    routing_candidate_eligibility_status = postgresql.ENUM(
        "eligible_for_future_selection",
        "ineligible_for_future_selection",
        name="routingcandidateeligibilitystatus",
        create_type=False,
    )

    op.create_table(
        "routing_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("assessment_id", sa.String(length=64), nullable=False),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=True),
        sa.Column("market_data_source_policy_ref_id", sa.String(length=36), nullable=True),
        sa.Column("planning_source_venue", sa.String(length=32), nullable=False),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("action", postgresql.ENUM(name="decisionaction", create_type=False), nullable=False),
        sa.Column("target_scope", postgresql.ENUM(name="tradetargetscope", create_type=False), nullable=False),
        sa.Column("decision_status", routing_assessment_decision_status, nullable=False),
        sa.Column("eligible_binding_count", sa.Integer(), nullable=False),
        sa.Column("ineligible_binding_count", sa.Integer(), nullable=False),
        sa.Column("request_snapshot_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["market_data_source_policy_ref_id"], ["mandate_market_data_source_policies.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routing_assessments_assessment_id", "routing_assessments", ["assessment_id"], unique=True)
    op.create_index(
        "ix_routing_assessments_env_desired_trade_evaluated_at",
        "routing_assessments",
        ["environment", "desired_trade_ref_id", "evaluated_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_assessments_env_status_evaluated_at",
        "routing_assessments",
        ["environment", "decision_status", "evaluated_at"],
        unique=False,
    )

    op.create_table(
        "routing_assessment_candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assessment_ref_id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=64), nullable=False),
        sa.Column("binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("binding_key", sa.String(length=128), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("venue_account_key", sa.String(length=128), nullable=True),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("exchange_symbol", sa.String(length=64), nullable=True),
        sa.Column("eligibility_status", routing_candidate_eligibility_status, nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("fact_snapshot_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_ref_id"], ["routing_assessments.id"]),
        sa.ForeignKeyConstraint(["binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_routing_assessment_candidates_assessment_id",
        "routing_assessment_candidates",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        "ix_routing_assessment_candidates_assessment_status",
        "routing_assessment_candidates",
        ["assessment_ref_id", "eligibility_status"],
        unique=False,
    )
    op.create_index(
        "ix_routing_assessment_candidates_binding",
        "routing_assessment_candidates",
        ["binding_ref_id", "evaluated_at"],
        unique=False,
    )

    with op.batch_alter_table("routing_assessments") as batch_op:
        batch_op.alter_column("request_snapshot_json", server_default=None)
        batch_op.alter_column("reason_codes_json", server_default=None)
        batch_op.alter_column("missing_data_json", server_default=None)
        batch_op.alter_column("provenance_json", server_default=None)
    with op.batch_alter_table("routing_assessment_candidates") as batch_op:
        batch_op.alter_column("reason_codes_json", server_default=None)
        batch_op.alter_column("missing_data_json", server_default=None)
        batch_op.alter_column("fact_snapshot_json", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_routing_assessment_candidates_binding", table_name="routing_assessment_candidates")
    op.drop_index(
        "ix_routing_assessment_candidates_assessment_status",
        table_name="routing_assessment_candidates",
    )
    op.drop_index("ix_routing_assessment_candidates_assessment_id", table_name="routing_assessment_candidates")
    op.drop_table("routing_assessment_candidates")

    op.drop_index("ix_routing_assessments_env_status_evaluated_at", table_name="routing_assessments")
    op.drop_index(
        "ix_routing_assessments_env_desired_trade_evaluated_at",
        table_name="routing_assessments",
    )
    op.drop_index("ix_routing_assessments_assessment_id", table_name="routing_assessments")
    op.drop_table("routing_assessments")

    postgresql.ENUM(name="routingcandidateeligibilitystatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="routingassessmentdecisionstatus").drop(op.get_bind(), checkfirst=True)
