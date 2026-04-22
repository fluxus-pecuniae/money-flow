"""Phase 3.4 mandate hierarchy refactor.

Revision ID: 20260405_0007
Revises: 20260404_0006
Create Date: 2026-04-05 10:00:00.000000
"""

from __future__ import annotations

import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260405_0007"
down_revision = "20260404_0006"
branch_labels = None
depends_on = None


strategy_family_enum = postgresql.ENUM(name="strategyfamily", create_type=False)
timeframe_enum = postgresql.ENUM(name="timeframe", create_type=False)

MANDATE_DEFAULT_SCOPE = "__mandate_default__"


def upgrade() -> None:
    op.create_table(
        "strategy_mandates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("mandate_key", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), sa.ForeignKey("clients.id"), nullable=False),
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
    op.create_index("ix_strategy_mandates_mandate_key", "strategy_mandates", ["mandate_key"], unique=True)
    op.create_index(
        "ix_strategy_mandates_client_family_enabled",
        "strategy_mandates",
        ["client_ref_id", "family", "enabled"],
        unique=False,
    )

    op.create_table(
        "mandate_account_bindings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("binding_key", sa.String(length=128), nullable=False),
        sa.Column(
            "strategy_mandate_ref_id",
            sa.String(length=36),
            sa.ForeignKey("strategy_mandates.id"),
            nullable=False,
        ),
        sa.Column(
            "venue_account_ref_id",
            sa.String(length=36),
            sa.ForeignKey("venue_accounts.id"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("strategy_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("routing_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("trading_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
    op.create_index("ix_mandate_account_bindings_binding_key", "mandate_account_bindings", ["binding_key"], unique=True)
    op.create_index(
        "ix_mandate_account_bindings_mandate_account",
        "mandate_account_bindings",
        ["strategy_mandate_ref_id", "venue_account_ref_id"],
        unique=True,
    )
    op.create_index(
        "ix_mandate_account_bindings_account_enabled",
        "mandate_account_bindings",
        ["venue_account_ref_id", "enabled", "routing_eligible"],
        unique=False,
    )

    op.create_table(
        "strategy_component_configs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "strategy_mandate_ref_id",
            sa.String(length=36),
            sa.ForeignKey("strategy_mandates.id"),
            nullable=False,
        ),
        sa.Column(
            "mandate_account_binding_ref_id",
            sa.String(length=36),
            sa.ForeignKey("mandate_account_bindings.id"),
            nullable=True,
        ),
        sa.Column("binding_scope_key", sa.String(length=128), nullable=False),
        sa.Column("component_key", sa.String(length=64), nullable=False),
        sa.Column("component_type", sa.String(length=64), nullable=False),
        sa.Column("timeframe", timeframe_enum, nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capital_allocation_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("max_open_risk_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("is_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "source_component_config_ref_id",
            sa.String(length=36),
            sa.ForeignKey("strategy_component_configs.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_strategy_component_configs_scope_component",
        "strategy_component_configs",
        ["strategy_mandate_ref_id", "binding_scope_key", "component_key"],
        unique=True,
    )

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.add_column(sa.Column("component_key", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("mandate_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("binding_key", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key("fk_sig_mandate", "strategy_mandates", ["strategy_mandate_ref_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_sig_binding",
            "mandate_account_bindings",
            ["mandate_account_binding_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_signal_events_component_key", ["component_key"], unique=False)
        batch_op.create_index("ix_signal_events_strategy_mandate_ref_id", ["strategy_mandate_ref_id"], unique=False)
        batch_op.create_index(
            "ix_signal_events_mandate_account_binding_ref_id",
            ["mandate_account_binding_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_signal_events_mandate_key", ["mandate_key"], unique=False)
        batch_op.create_index("ix_signal_events_binding_key", ["binding_key"], unique=False)

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.add_column(sa.Column("component_key", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("mandate_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("binding_key", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key("fk_dec_mandate", "strategy_mandates", ["strategy_mandate_ref_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_dec_binding",
            "mandate_account_bindings",
            ["mandate_account_binding_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_strategy_decisions_component_key", ["component_key"], unique=False)
        batch_op.create_index(
            "ix_strategy_decisions_strategy_mandate_ref_id",
            ["strategy_mandate_ref_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_strategy_decisions_mandate_account_binding_ref_id",
            ["mandate_account_binding_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_strategy_decisions_mandate_key", ["mandate_key"], unique=False)
        batch_op.create_index("ix_strategy_decisions_binding_key", ["binding_key"], unique=False)

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("component_key", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("strategy_mandate_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("mandate_account_binding_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_intent_mandate", "strategy_mandates", ["strategy_mandate_ref_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_intent_binding",
            "mandate_account_bindings",
            ["mandate_account_binding_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_order_intents_component_key", ["component_key"], unique=False)
        batch_op.create_index("ix_order_intents_strategy_mandate_ref_id", ["strategy_mandate_ref_id"], unique=False)
        batch_op.create_index(
            "ix_order_intents_mandate_account_binding_ref_id",
            ["mandate_account_binding_ref_id"],
            unique=False,
        )

    bind = op.get_bind()
    deployments = bind.execute(
        sa.text(
            """
            SELECT id, deployment_key, client_ref_id, venue_account_ref_id, family, enabled,
                   allow_builder_deployed_for_strategy, allow_builder_deployed_for_trading,
                   notes, metadata_json
            FROM strategy_deployments
            ORDER BY created_at ASC
            """
        )
    ).mappings().all()

    for deployment in deployments:
        venue_account = bind.execute(
            sa.text("SELECT venue_account_key FROM venue_accounts WHERE id = :id"),
            {"id": deployment["venue_account_ref_id"]},
        ).mappings().first()
        if venue_account is None:
            continue
        mandate_id = str(uuid4())
        binding_id = str(uuid4())
        mandate_key = deployment["deployment_key"]
        binding_key = f"{mandate_key}::{venue_account['venue_account_key']}"
        metadata_json = dict(deployment["metadata_json"] or {})
        metadata_json["migrated_from_strategy_deployment"] = deployment["id"]

        bind.execute(
            sa.text(
                """
                INSERT INTO strategy_mandates (
                    id, mandate_key, client_ref_id, family, enabled,
                    allow_builder_deployed_for_strategy, allow_builder_deployed_for_trading,
                    notes, metadata_json
                ) VALUES (
                    :id, :mandate_key, :client_ref_id, :family, :enabled,
                    :allow_builder_deployed_for_strategy, :allow_builder_deployed_for_trading,
                    :notes, CAST(:metadata_json AS json)
                )
                """
            ),
            {
                "id": mandate_id,
                "mandate_key": mandate_key,
                "client_ref_id": deployment["client_ref_id"],
                "family": deployment["family"],
                "enabled": deployment["enabled"],
                "allow_builder_deployed_for_strategy": deployment["allow_builder_deployed_for_strategy"],
                "allow_builder_deployed_for_trading": deployment["allow_builder_deployed_for_trading"],
                "notes": deployment["notes"],
                "metadata_json": json.dumps(metadata_json, sort_keys=True),
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO mandate_account_bindings (
                    id, binding_key, strategy_mandate_ref_id, venue_account_ref_id,
                    enabled, strategy_eligible, routing_eligible, trading_enabled,
                    allow_builder_deployed_for_strategy, allow_builder_deployed_for_trading,
                    notes, metadata_json
                ) VALUES (
                    :id, :binding_key, :strategy_mandate_ref_id, :venue_account_ref_id,
                    :enabled, true, true, true,
                    :allow_builder_deployed_for_strategy, :allow_builder_deployed_for_trading,
                    :notes, CAST(:metadata_json AS json)
                )
                """
            ),
            {
                "id": binding_id,
                "binding_key": binding_key,
                "strategy_mandate_ref_id": mandate_id,
                "venue_account_ref_id": deployment["venue_account_ref_id"],
                "enabled": deployment["enabled"],
                "allow_builder_deployed_for_strategy": deployment["allow_builder_deployed_for_strategy"],
                "allow_builder_deployed_for_trading": deployment["allow_builder_deployed_for_trading"],
                "notes": deployment["notes"],
                "metadata_json": json.dumps(
                    {"migrated_from_strategy_deployment": deployment["id"]},
                    sort_keys=True,
                ),
            },
        )

        sleeve_rows = bind.execute(
            sa.text(
                """
                SELECT id, sleeve_id, timeframe, enabled, capital_allocation_pct, max_open_risk_pct, strategy_overrides
                FROM sleeve_deployment_configs
                WHERE strategy_deployment_ref_id = :strategy_deployment_ref_id
                ORDER BY sleeve_id ASC
                """
            ),
            {"strategy_deployment_ref_id": deployment["id"]},
        ).mappings().all()
        for sleeve in sleeve_rows:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO strategy_component_configs (
                        id, strategy_mandate_ref_id, mandate_account_binding_ref_id,
                        binding_scope_key, component_key, component_type, timeframe,
                        enabled, capital_allocation_pct, max_open_risk_pct,
                        parameters_json, metadata_json, is_override, source_component_config_ref_id
                    ) VALUES (
                        :id, :strategy_mandate_ref_id, NULL,
                        :binding_scope_key, :component_key, :component_type, :timeframe,
                        :enabled, :capital_allocation_pct, :max_open_risk_pct,
                        CAST(:parameters_json AS json), CAST(:metadata_json AS json), false, NULL
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "strategy_mandate_ref_id": mandate_id,
                    "binding_scope_key": MANDATE_DEFAULT_SCOPE,
                    "component_key": sleeve["sleeve_id"],
                    "component_type": "money_flow_sleeve",
                    "timeframe": sleeve["timeframe"],
                    "enabled": sleeve["enabled"],
                    "capital_allocation_pct": sleeve["capital_allocation_pct"],
                    "max_open_risk_pct": sleeve["max_open_risk_pct"],
                    "parameters_json": json.dumps(dict(sleeve["strategy_overrides"] or {}), sort_keys=True),
                    "metadata_json": json.dumps(
                        {"migrated_from_sleeve_deployment_config": sleeve["id"]},
                        sort_keys=True,
                    ),
                },
            )

        bind.execute(
            sa.text(
                """
                UPDATE signal_events
                   SET component_key = COALESCE(component_key, sleeve_id),
                       strategy_mandate_ref_id = :strategy_mandate_ref_id,
                       mandate_account_binding_ref_id = :mandate_account_binding_ref_id,
                       mandate_key = :mandate_key,
                       binding_key = :binding_key
                 WHERE strategy_deployment_ref_id = :strategy_deployment_ref_id
                   AND strategy_mandate_ref_id IS NULL
                """
            ),
            {
                "strategy_mandate_ref_id": mandate_id,
                "mandate_account_binding_ref_id": binding_id,
                "mandate_key": mandate_key,
                "binding_key": binding_key,
                "strategy_deployment_ref_id": deployment["id"],
            },
        )
        bind.execute(
            sa.text(
                """
                UPDATE strategy_decisions
                   SET component_key = COALESCE(component_key, sleeve_id),
                       strategy_mandate_ref_id = :strategy_mandate_ref_id,
                       mandate_account_binding_ref_id = :mandate_account_binding_ref_id,
                       mandate_key = :mandate_key,
                       binding_key = :binding_key
                 WHERE strategy_deployment_ref_id = :strategy_deployment_ref_id
                   AND strategy_mandate_ref_id IS NULL
                """
            ),
            {
                "strategy_mandate_ref_id": mandate_id,
                "mandate_account_binding_ref_id": binding_id,
                "mandate_key": mandate_key,
                "binding_key": binding_key,
                "strategy_deployment_ref_id": deployment["id"],
            },
        )
        bind.execute(
            sa.text(
                """
                UPDATE order_intents
                   SET component_key = COALESCE(component_key, sleeve_id),
                       strategy_mandate_ref_id = :strategy_mandate_ref_id,
                       mandate_account_binding_ref_id = :mandate_account_binding_ref_id
                 WHERE strategy_deployment_ref_id = :strategy_deployment_ref_id
                   AND strategy_mandate_ref_id IS NULL
                """
            ),
            {
                "strategy_mandate_ref_id": mandate_id,
                "mandate_account_binding_ref_id": binding_id,
                "strategy_deployment_ref_id": deployment["id"],
            },
        )


def downgrade() -> None:
    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_mandate_account_binding_ref_id")
        batch_op.drop_index("ix_order_intents_strategy_mandate_ref_id")
        batch_op.drop_index("ix_order_intents_component_key")
        batch_op.drop_constraint("fk_intent_binding", type_="foreignkey")
        batch_op.drop_constraint("fk_intent_mandate", type_="foreignkey")
        batch_op.drop_column("mandate_account_binding_ref_id")
        batch_op.drop_column("strategy_mandate_ref_id")
        batch_op.drop_column("component_key")

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.drop_index("ix_strategy_decisions_binding_key")
        batch_op.drop_index("ix_strategy_decisions_mandate_key")
        batch_op.drop_index("ix_strategy_decisions_mandate_account_binding_ref_id")
        batch_op.drop_index("ix_strategy_decisions_strategy_mandate_ref_id")
        batch_op.drop_index("ix_strategy_decisions_component_key")
        batch_op.drop_constraint("fk_dec_binding", type_="foreignkey")
        batch_op.drop_constraint("fk_dec_mandate", type_="foreignkey")
        batch_op.drop_column("binding_key")
        batch_op.drop_column("mandate_key")
        batch_op.drop_column("mandate_account_binding_ref_id")
        batch_op.drop_column("strategy_mandate_ref_id")
        batch_op.drop_column("component_key")

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.drop_index("ix_signal_events_binding_key")
        batch_op.drop_index("ix_signal_events_mandate_key")
        batch_op.drop_index("ix_signal_events_mandate_account_binding_ref_id")
        batch_op.drop_index("ix_signal_events_strategy_mandate_ref_id")
        batch_op.drop_index("ix_signal_events_component_key")
        batch_op.drop_constraint("fk_sig_binding", type_="foreignkey")
        batch_op.drop_constraint("fk_sig_mandate", type_="foreignkey")
        batch_op.drop_column("binding_key")
        batch_op.drop_column("mandate_key")
        batch_op.drop_column("mandate_account_binding_ref_id")
        batch_op.drop_column("strategy_mandate_ref_id")
        batch_op.drop_column("component_key")

    op.drop_index("ix_strategy_component_configs_scope_component", table_name="strategy_component_configs")
    op.drop_table("strategy_component_configs")

    op.drop_index("ix_mandate_account_bindings_account_enabled", table_name="mandate_account_bindings")
    op.drop_index("ix_mandate_account_bindings_mandate_account", table_name="mandate_account_bindings")
    op.drop_index("ix_mandate_account_bindings_binding_key", table_name="mandate_account_bindings")
    op.drop_table("mandate_account_bindings")

    op.drop_index("ix_strategy_mandates_client_family_enabled", table_name="strategy_mandates")
    op.drop_index("ix_strategy_mandates_mandate_key", table_name="strategy_mandates")
    op.drop_table("strategy_mandates")
