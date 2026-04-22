"""Phase 6.0.0 routing target recommendation audit.

Revision ID: 20260419_0020
Revises: 20260419_0019
Create Date: 2026-04-19 08:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260419_0020"
down_revision = "20260419_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    recommendation_status_type = postgresql.ENUM(
        "recommended_single_ready_candidate",
        "blocked_audit_not_found",
        "blocked_audit_not_ready",
        "blocked_no_ready_candidate",
        "blocked_multiple_ready_candidates",
        "blocked_stale_audit",
        "blocked_stale_desired_trade",
        "blocked_stale_candidate",
        "blocked_invalid_audit",
        name="routingtargetrecommendationstatus",
    )
    recommendation_status_type.create(bind, checkfirst=True)
    recommendation_status = postgresql.ENUM(
        "recommended_single_ready_candidate",
        "blocked_audit_not_found",
        "blocked_audit_not_ready",
        "blocked_no_ready_candidate",
        "blocked_multiple_ready_candidates",
        "blocked_stale_audit",
        "blocked_stale_desired_trade",
        "blocked_stale_candidate",
        "blocked_invalid_audit",
        name="routingtargetrecommendationstatus",
        create_type=False,
    )

    op.create_table(
        "routing_target_recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("routing_target_recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("route_readiness_audit_ref_id", sa.String(length=36), nullable=True),
        sa.Column("route_readiness_audit_id", sa.String(length=64), nullable=False),
        sa.Column("routing_assessment_ref_id", sa.String(length=36), nullable=True),
        sa.Column("routing_assessment_id", sa.String(length=64), nullable=True),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=True),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("action", postgresql.ENUM(name="decisionaction", create_type=False), nullable=True),
        sa.Column("target_scope", postgresql.ENUM(name="tradetargetscope", create_type=False), nullable=True),
        sa.Column("status", recommendation_status, nullable=False),
        sa.Column("policy_name", sa.String(length=64), nullable=False),
        sa.Column("recommended_binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("recommended_binding_key", sa.String(length=128), nullable=True),
        sa.Column("recommended_venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("recommended_venue_account_key", sa.String(length=128), nullable=True),
        sa.Column("recommended_venue", sa.String(length=32), nullable=True),
        sa.Column("recommended_exchange_symbol", sa.String(length=64), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("ready_candidate_count", sa.Integer(), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("blocking_reasons_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("stale_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("non_executing", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("target_choice_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("child_intent_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("submitted_order_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["route_readiness_audit_ref_id"], ["route_readiness_audits.id"]),
        sa.ForeignKeyConstraint(["routing_assessment_ref_id"], ["routing_assessments.id"]),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["recommended_binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["recommended_venue_account_ref_id"], ["venue_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rtrec_recommendation_id",
        "routing_target_recommendations",
        ["routing_target_recommendation_id"],
        unique=True,
    )
    op.create_index(
        "ix_routing_target_recommendations_audit_created_at",
        "routing_target_recommendations",
        ["route_readiness_audit_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_target_recommendations_desired_trade_created_at",
        "routing_target_recommendations",
        ["desired_trade_key", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_routing_target_recommendations_status_created_at",
        "routing_target_recommendations",
        ["status", "created_at"],
        unique=False,
    )

    with op.batch_alter_table("routing_target_recommendations") as batch_op:
        for column in (
            "reason_codes_json",
            "blocking_reasons_json",
            "missing_data_json",
            "stale_data_json",
            "non_executing",
            "target_choice_created",
            "child_intent_created",
            "submitted_order_created",
            "provenance_json",
        ):
            batch_op.alter_column(column, server_default=None)


def downgrade() -> None:
    op.drop_index(
        "ix_routing_target_recommendations_status_created_at",
        table_name="routing_target_recommendations",
    )
    op.drop_index(
        "ix_routing_target_recommendations_desired_trade_created_at",
        table_name="routing_target_recommendations",
    )
    op.drop_index(
        "ix_routing_target_recommendations_audit_created_at",
        table_name="routing_target_recommendations",
    )
    op.drop_index(
        "ix_rtrec_recommendation_id",
        table_name="routing_target_recommendations",
    )
    op.drop_table("routing_target_recommendations")
    postgresql.ENUM(name="routingtargetrecommendationstatus").drop(op.get_bind(), checkfirst=True)
