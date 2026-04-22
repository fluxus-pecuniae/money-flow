"""Phase 4.0.2 source policy and desired-trade aggregation hardening.

Revision ID: 20260406_0011
Revises: 20260405_0010
Create Date: 2026-04-06 10:15:00.000000
"""

from __future__ import annotations

import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_0011"
down_revision = "20260405_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    market_data_source_mode_type = postgresql.ENUM(
        "single_venue",
        "composite",
        name="marketdatasourcemode",
    )
    instrument_resolution_mode_type = postgresql.ENUM(
        "require_instrument_key",
        "canonical_symbol_if_unambiguous",
        name="instrumentresolutionmode",
    )
    market_data_source_mode_type.create(bind, checkfirst=True)
    instrument_resolution_mode_type.create(bind, checkfirst=True)

    market_data_source_mode = postgresql.ENUM(
        "single_venue",
        "composite",
        name="marketdatasourcemode",
        create_type=False,
    )
    instrument_resolution_mode = postgresql.ENUM(
        "require_instrument_key",
        "canonical_symbol_if_unambiguous",
        name="instrumentresolutionmode",
        create_type=False,
    )

    op.create_table(
        "mandate_market_data_source_policies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=False),
        sa.Column("source_mode", market_data_source_mode, nullable=False),
        sa.Column("source_venue", sa.String(length=32), nullable=False),
        sa.Column(
            "market_type",
            postgresql.ENUM(name="markettype", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "product_type",
            postgresql.ENUM(name="producttype", create_type=False),
            nullable=True,
        ),
        sa.Column("instrument_resolution_mode", instrument_resolution_mode, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_mandate_ref_id"], ["strategy_mandates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mandate_market_data_source_policies_mandate_unique",
        "mandate_market_data_source_policies",
        ["strategy_mandate_ref_id"],
        unique=True,
    )
    op.create_index(
        "ix_mandate_market_data_source_policies_source_venue",
        "mandate_market_data_source_policies",
        ["source_venue", "source_mode"],
        unique=False,
    )

    with op.batch_alter_table("mandate_market_data_source_policies") as batch_op:
        batch_op.alter_column("metadata_json", server_default=None)

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.add_column(sa.Column("market_data_source_policy_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("planning_source_venue", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("planning_source_mode", market_data_source_mode, nullable=True))
        batch_op.add_column(sa.Column("planning_as_of", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("source_evaluation_keys_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json"))
        )
        batch_op.add_column(
            sa.Column("source_binding_keys_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json"))
        )
        batch_op.create_foreign_key(
            "fk_mandate_desired_trades_market_data_source_policy_ref_id",
            "mandate_market_data_source_policies",
            ["market_data_source_policy_ref_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_mandate_desired_trades_market_data_source_policy_ref_id",
            ["market_data_source_policy_ref_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_mandate_desired_trades_planning_source_venue",
            ["planning_source_venue"],
            unique=False,
        )
        batch_op.create_index(
            "ix_mandate_desired_trades_planning_as_of",
            ["planning_as_of"],
            unique=False,
        )

    mandate_rows = bind.execute(
        sa.text("SELECT id, mandate_key FROM strategy_mandates ORDER BY created_at ASC")
    ).mappings().all()
    policy_rows: list[dict[str, object]] = []
    policy_by_mandate: dict[str, str] = {}
    policy_venue_by_mandate: dict[str, str] = {}
    now_value = bind.execute(sa.text("SELECT now()")).scalar()
    for row in mandate_rows:
        mandate_id = row["id"]
        source_venue = bind.execute(
            sa.text(
                """
                SELECT COALESCE(symbols.venue, venue_accounts.venue) AS source_venue
                FROM strategy_decisions
                LEFT JOIN symbols ON symbols.id = strategy_decisions.symbol_id
                LEFT JOIN venue_accounts ON venue_accounts.id = strategy_decisions.venue_account_ref_id
                WHERE strategy_decisions.strategy_mandate_ref_id = :mandate_id
                ORDER BY strategy_decisions.decided_at DESC
                LIMIT 1
                """
            ),
            {"mandate_id": mandate_id},
        ).scalar()
        if source_venue is None:
            source_venue = bind.execute(
                sa.text(
                    """
                    SELECT venue_accounts.venue
                    FROM mandate_account_bindings
                    JOIN venue_accounts
                      ON venue_accounts.id = mandate_account_bindings.venue_account_ref_id
                    WHERE mandate_account_bindings.strategy_mandate_ref_id = :mandate_id
                    ORDER BY mandate_account_bindings.created_at ASC
                    LIMIT 1
                    """
                ),
                {"mandate_id": mandate_id},
            ).scalar()
        source_venue = str(source_venue or "hyperliquid")
        policy_id = str(uuid4())
        policy_rows.append(
            {
                "id": policy_id,
                "strategy_mandate_ref_id": mandate_id,
                "source_mode": "single_venue",
                "source_venue": source_venue,
                "market_type": None,
                "product_type": None,
                "instrument_resolution_mode": "canonical_symbol_if_unambiguous",
                "notes": "backfilled_from_phase_4_0_1_state",
                "metadata_json": json.dumps({}),
                "created_at": now_value,
                "updated_at": now_value,
            }
        )
        policy_by_mandate[mandate_id] = policy_id
        policy_venue_by_mandate[mandate_id] = source_venue
    if policy_rows:
        for row in policy_rows:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO mandate_market_data_source_policies (
                        id,
                        strategy_mandate_ref_id,
                        source_mode,
                        source_venue,
                        market_type,
                        product_type,
                        instrument_resolution_mode,
                        notes,
                        metadata_json,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :strategy_mandate_ref_id,
                        CAST(:source_mode AS marketdatasourcemode),
                        :source_venue,
                        CAST(:market_type AS markettype),
                        CAST(:product_type AS producttype),
                        CAST(:instrument_resolution_mode AS instrumentresolutionmode),
                        :notes,
                        CAST(:metadata_json AS JSON),
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                row,
            )

    desired_trade_rows = bind.execute(
        sa.text(
            """
            SELECT id, strategy_mandate_ref_id, binding_key, provenance
            FROM mandate_desired_trades
            """
        )
    ).mappings().all()
    for row in desired_trade_rows:
        provenance = row["provenance"] or {}
        planning_as_of = provenance.get("indicator_as_of") or provenance.get("latest_candle_close")
        source_evaluation_keys = []
        if provenance.get("source_evaluation_key"):
            source_evaluation_keys = [provenance["source_evaluation_key"]]
        source_binding_keys = []
        if row["binding_key"]:
            source_binding_keys = [row["binding_key"]]
        elif provenance.get("binding_key"):
            source_binding_keys = [provenance["binding_key"]]
        bind.execute(
            sa.text(
                """
                UPDATE mandate_desired_trades
                SET market_data_source_policy_ref_id = :policy_id,
                    planning_source_venue = :source_venue,
                    planning_source_mode = CAST(:source_mode AS marketdatasourcemode),
                    planning_as_of = :planning_as_of,
                    source_evaluation_keys_json = CAST(:source_evaluation_keys_json AS JSON),
                    source_binding_keys_json = CAST(:source_binding_keys_json AS JSON)
                WHERE id = :desired_trade_id
                """
            ),
            {
                "policy_id": policy_by_mandate.get(row["strategy_mandate_ref_id"]),
                "source_venue": policy_venue_by_mandate.get(row["strategy_mandate_ref_id"], "hyperliquid"),
                "source_mode": "single_venue",
                "planning_as_of": planning_as_of,
                "source_evaluation_keys_json": json.dumps(source_evaluation_keys),
                "source_binding_keys_json": json.dumps(source_binding_keys),
                "desired_trade_id": row["id"],
            },
        )

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.alter_column("planning_source_venue", nullable=False)
        batch_op.alter_column("planning_source_mode", nullable=False)
        batch_op.alter_column("source_evaluation_keys_json", server_default=None)
        batch_op.alter_column("source_binding_keys_json", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    market_data_source_mode = postgresql.ENUM(
        "single_venue",
        "composite",
        name="marketdatasourcemode",
    )
    instrument_resolution_mode = postgresql.ENUM(
        "require_instrument_key",
        "canonical_symbol_if_unambiguous",
        name="instrumentresolutionmode",
    )

    with op.batch_alter_table("mandate_desired_trades") as batch_op:
        batch_op.drop_index("ix_mandate_desired_trades_planning_as_of")
        batch_op.drop_index("ix_mandate_desired_trades_planning_source_venue")
        batch_op.drop_index("ix_mandate_desired_trades_market_data_source_policy_ref_id")
        batch_op.drop_constraint(
            "fk_mandate_desired_trades_market_data_source_policy_ref_id",
            type_="foreignkey",
        )
        batch_op.drop_column("source_binding_keys_json")
        batch_op.drop_column("source_evaluation_keys_json")
        batch_op.drop_column("planning_as_of")
        batch_op.drop_column("planning_source_mode")
        batch_op.drop_column("planning_source_venue")
        batch_op.drop_column("market_data_source_policy_ref_id")

    op.drop_index(
        "ix_mandate_market_data_source_policies_source_venue",
        table_name="mandate_market_data_source_policies",
    )
    op.drop_index(
        "ix_mandate_market_data_source_policies_mandate_unique",
        table_name="mandate_market_data_source_policies",
    )
    op.drop_table("mandate_market_data_source_policies")

    instrument_resolution_mode.drop(bind, checkfirst=True)
    market_data_source_mode.drop(bind, checkfirst=True)
