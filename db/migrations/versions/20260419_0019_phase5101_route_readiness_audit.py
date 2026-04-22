"""Phase 5.10.1 route-readiness data-sufficiency audit.

Revision ID: 20260419_0019
Revises: 20260418_0018
Create Date: 2026-04-19 06:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260419_0019"
down_revision = "20260418_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    route_readiness_status_type = postgresql.ENUM(
        "ready_for_recommendation",
        "blocked",
        "insufficient_data",
        "stale_data",
        "policy_blocked",
        "unsupported",
        name="routereadinessauditstatus",
    )
    route_readiness_status_type.create(bind, checkfirst=True)
    route_readiness_status = postgresql.ENUM(
        "ready_for_recommendation",
        "blocked",
        "insufficient_data",
        "stale_data",
        "policy_blocked",
        "unsupported",
        name="routereadinessauditstatus",
        create_type=False,
    )

    op.create_table(
        "route_readiness_audits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", postgresql.ENUM(name="environment", create_type=False), nullable=False),
        sa.Column("route_readiness_audit_id", sa.String(length=64), nullable=False),
        sa.Column("desired_trade_ref_id", sa.String(length=36), nullable=True),
        sa.Column("desired_trade_key", sa.String(length=128), nullable=False),
        sa.Column("routing_assessment_ref_id", sa.String(length=36), nullable=True),
        sa.Column("routing_assessment_id", sa.String(length=64), nullable=True),
        sa.Column("client_ref_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=True),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("action", postgresql.ENUM(name="decisionaction", create_type=False), nullable=False),
        sa.Column("target_scope", postgresql.ENUM(name="tradetargetscope", create_type=False), nullable=False),
        sa.Column("overall_status", route_readiness_status, nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("ready_candidate_count", sa.Integer(), nullable=False),
        sa.Column("blocked_candidate_count", sa.Integer(), nullable=False),
        sa.Column("insufficient_data_candidate_count", sa.Integer(), nullable=False),
        sa.Column("global_reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("global_missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("global_stale_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("global_blocking_reasons_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("non_selecting", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("recommendation_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_choice_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("child_intent_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("submitted_order_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["desired_trade_ref_id"], ["mandate_desired_trades.id"]),
        sa.ForeignKeyConstraint(["routing_assessment_ref_id"], ["routing_assessments.id"]),
        sa.ForeignKeyConstraint(["client_ref_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_route_readiness_audits_route_readiness_audit_id",
        "route_readiness_audits",
        ["route_readiness_audit_id"],
        unique=True,
    )
    op.create_index(
        "ix_route_readiness_audits_env_desired_trade_evaluated_at",
        "route_readiness_audits",
        ["environment", "desired_trade_ref_id", "evaluated_at"],
        unique=False,
    )
    op.create_index(
        "ix_route_readiness_audits_env_status_evaluated_at",
        "route_readiness_audits",
        ["environment", "overall_status", "evaluated_at"],
        unique=False,
    )

    op.create_table(
        "route_readiness_candidate_audits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("route_readiness_audit_ref_id", sa.String(length=36), nullable=False),
        sa.Column("route_readiness_audit_id", sa.String(length=64), nullable=False),
        sa.Column("routing_assessment_candidate_ref_id", sa.String(length=36), nullable=True),
        sa.Column("binding_ref_id", sa.String(length=36), nullable=True),
        sa.Column("binding_key", sa.String(length=128), nullable=True),
        sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True),
        sa.Column("venue_account_key", sa.String(length=128), nullable=True),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("instrument_ref_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_key", sa.String(length=128), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("exchange_symbol", sa.String(length=64), nullable=True),
        sa.Column("status", route_readiness_status, nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("missing_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("stale_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("unsupported_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("unavailable_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("policy_blocks_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("blocking_reasons_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("fact_snapshot_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("data_sources_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["route_readiness_audit_ref_id"], ["route_readiness_audits.id"]),
        sa.ForeignKeyConstraint(["routing_assessment_candidate_ref_id"], ["routing_assessment_candidates.id"]),
        sa.ForeignKeyConstraint(["binding_ref_id"], ["mandate_account_bindings.id"]),
        sa.ForeignKeyConstraint(["venue_account_ref_id"], ["venue_accounts.id"]),
        sa.ForeignKeyConstraint(["instrument_ref_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_route_readiness_candidates_audit_status",
        "route_readiness_candidate_audits",
        ["route_readiness_audit_ref_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_route_readiness_candidates_binding",
        "route_readiness_candidate_audits",
        ["binding_ref_id", "evaluated_at"],
        unique=False,
    )

    for table_name, columns in {
        "route_readiness_audits": [
            "global_reason_codes_json",
            "global_missing_data_json",
            "global_stale_data_json",
            "global_blocking_reasons_json",
            "non_selecting",
            "recommendation_created",
            "target_choice_created",
            "child_intent_created",
            "submitted_order_created",
            "provenance_json",
        ],
        "route_readiness_candidate_audits": [
            "reason_codes_json",
            "missing_data_json",
            "stale_data_json",
            "unsupported_data_json",
            "unavailable_data_json",
            "policy_blocks_json",
            "blocking_reasons_json",
            "fact_snapshot_json",
            "data_sources_json",
        ],
    }.items():
        with op.batch_alter_table(table_name) as batch_op:
            for column in columns:
                batch_op.alter_column(column, server_default=None)


def downgrade() -> None:
    op.drop_index("ix_route_readiness_candidates_binding", table_name="route_readiness_candidate_audits")
    op.drop_index("ix_route_readiness_candidates_audit_status", table_name="route_readiness_candidate_audits")
    op.drop_table("route_readiness_candidate_audits")
    op.drop_index("ix_route_readiness_audits_env_status_evaluated_at", table_name="route_readiness_audits")
    op.drop_index("ix_route_readiness_audits_env_desired_trade_evaluated_at", table_name="route_readiness_audits")
    op.drop_index("ix_route_readiness_audits_route_readiness_audit_id", table_name="route_readiness_audits")
    op.drop_table("route_readiness_audits")
    postgresql.ENUM(name="routereadinessauditstatus").drop(op.get_bind(), checkfirst=True)
