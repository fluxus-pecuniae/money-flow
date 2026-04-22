"""Phase 3.3 client/account/deployment hierarchy.

Revision ID: 20260404_0006
Revises: 20260403_0005
Create Date: 2026-04-04 11:00:00.000000
"""

from __future__ import annotations

import json
import os
import re
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260404_0006"
down_revision = "20260403_0005"
branch_labels = None
depends_on = None


environment_enum = postgresql.ENUM(name="environment", create_type=False)
strategy_family_enum = postgresql.ENUM(name="strategyfamily", create_type=False)
timeframe_enum = postgresql.ENUM(name="timeframe", create_type=False)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "default"


def _flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_account_key(venue: str, environment: str, label: str, address: str) -> str:
    suffix = _slug(label) if label else _slug(address[-8:] if address else "primary")
    return f"{venue}_{environment}_{suffix}"


def upgrade() -> None:
    active_client_key = os.getenv("ACTIVE_CLIENT_KEY", "default_client")
    exchange_venue = os.getenv("EXCHANGE_VENUE", "hyperliquid")
    app_environment = os.getenv("APP_ENV", "dev")
    account_address = os.getenv("EXCHANGE_ACCOUNT_ADDRESS", "")
    account_label = os.getenv("EXCHANGE_ACCOUNT_LABEL", "primary")
    credentials_ref = os.getenv("EXCHANGE_CREDENTIALS_REF", "")
    wallet_ref = os.getenv("EXCHANGE_WALLET_REF", "")
    active_account_key = os.getenv(
        "ACTIVE_ACCOUNT_KEY",
        _default_account_key(exchange_venue, app_environment, account_label, account_address),
    )
    active_deployment_key = os.getenv("ACTIVE_DEPLOYMENT_KEY", f"money_flow::{active_account_key}")

    client_id = str(uuid4())
    venue_account_id = str(uuid4())
    strategy_deployment_id = str(uuid4())
    bind = op.get_bind()
    sleeve_ids = {
        "sleeve_15m": str(uuid4()),
        "sleeve_1h": str(uuid4()),
        "sleeve_4h": str(uuid4()),
    }

    op.create_table(
        "clients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("client_key", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_clients_client_key", "clients", ["client_key"], unique=True)

    op.create_table(
        "venue_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("venue_account_key", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("venue", sa.String(length=32), nullable=False),
        sa.Column("environment", environment_enum, nullable=False),
        sa.Column("venue_native_account_id", sa.String(length=128), nullable=False),
        sa.Column("account_address", sa.String(length=128), nullable=True),
        sa.Column("account_label", sa.String(length=128), nullable=True),
        sa.Column("subaccount_label", sa.String(length=128), nullable=True),
        sa.Column("credentials_ref", sa.String(length=128), nullable=True),
        sa.Column("wallet_ref", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("trading_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("raw_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_venue_accounts_venue_account_key", "venue_accounts", ["venue_account_key"], unique=True)
    op.create_index(
        "ix_venue_accounts_client_venue_environment",
        "venue_accounts",
        ["client_ref_id", "venue", "environment"],
        unique=False,
    )
    op.create_index(
        "ix_venue_accounts_venue_environment_address",
        "venue_accounts",
        ["venue", "environment", "account_address"],
        unique=False,
    )

    op.create_table(
        "strategy_deployments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deployment_key", sa.String(length=128), nullable=False),
        sa.Column("client_ref_id", sa.String(length=36), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("venue_account_ref_id", sa.String(length=36), sa.ForeignKey("venue_accounts.id"), nullable=False),
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
    op.create_index(
        "ix_strategy_deployments_deployment_key",
        "strategy_deployments",
        ["deployment_key"],
        unique=True,
    )
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

    with op.batch_alter_table("positions") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_pos_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_positions_venue_account_ref_id", ["venue_account_ref_id"], unique=False)

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_sub_orders_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_submitted_orders_venue_account_ref_id", ["venue_account_ref_id"], unique=False)

    with op.batch_alter_table("fills") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_fills_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_fills_venue_account_ref_id", ["venue_account_ref_id"], unique=False)

    with op.batch_alter_table("exchange_account_snapshots") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_exch_acct_snap_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_exchange_account_snapshots_venue_account_ref_id",
            ["venue_account_ref_id"],
            unique=False,
        )

    with op.batch_alter_table("portfolio_snapshots") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_portfolio_snap_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_portfolio_snapshots_venue_account_ref_id", ["venue_account_ref_id"], unique=False)

    with op.batch_alter_table("position_attribution_overlays") as batch_op:
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_pos_attr_overlay_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_position_attribution_overlays_venue_account_ref_id",
            ["venue_account_ref_id"],
            unique=False,
        )

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.add_column(sa.Column("client_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("deployment_key", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key("fk_signal_client", "clients", ["client_ref_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_signal_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_signal_deployment",
            "strategy_deployments",
            ["strategy_deployment_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_signal_events_client_ref_id", ["client_ref_id"], unique=False)
        batch_op.create_index("ix_signal_events_venue_account_ref_id", ["venue_account_ref_id"], unique=False)
        batch_op.create_index(
            "ix_signal_events_strategy_deployment_ref_id",
            ["strategy_deployment_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_signal_events_deployment_key", ["deployment_key"], unique=False)

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.add_column(sa.Column("client_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("deployment_key", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key(
            "fk_decision_client",
            "clients",
            ["client_ref_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_decision_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_decision_deployment",
            "strategy_deployments",
            ["strategy_deployment_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_strategy_decisions_client_ref_id", ["client_ref_id"], unique=False)
        batch_op.create_index("ix_strategy_decisions_venue_account_ref_id", ["venue_account_ref_id"], unique=False)
        batch_op.create_index(
            "ix_strategy_decisions_strategy_deployment_ref_id",
            ["strategy_deployment_ref_id"],
            unique=False,
        )
        batch_op.create_index("ix_strategy_decisions_deployment_key", ["deployment_key"], unique=False)

    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.add_column(sa.Column("client_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("venue_account_ref_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("strategy_deployment_ref_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_intent_client", "clients", ["client_ref_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_intent_venue_account",
            "venue_accounts",
            ["venue_account_ref_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_intent_deployment",
            "strategy_deployments",
            ["strategy_deployment_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_order_intents_client_ref_id", ["client_ref_id"], unique=False)
        batch_op.create_index("ix_order_intents_venue_account_ref_id", ["venue_account_ref_id"], unique=False)
        batch_op.create_index(
            "ix_order_intents_strategy_deployment_ref_id",
            ["strategy_deployment_ref_id"],
            unique=False,
        )

    bind.execute(
        sa.text(
            """
            INSERT INTO clients (id, client_key, display_name, is_active, created_at, updated_at)
            VALUES (:id, :client_key, :display_name, true, now(), now())
            ON CONFLICT (client_key) DO NOTHING
            """
        ),
        {
            "id": client_id,
            "client_key": active_client_key,
            "display_name": active_client_key.replace("_", " ").replace("-", " ").title(),
        },
    )
    inserted_client_id = op.get_bind().execute(
        sa.text("SELECT id FROM clients WHERE client_key = :client_key"),
        {"client_key": active_client_key},
    ).scalar_one()

    bind.execute(
        sa.text(
            """
            INSERT INTO venue_accounts (
                id,
                venue_account_key,
                client_ref_id,
                venue,
                environment,
                venue_native_account_id,
                account_address,
                account_label,
                subaccount_label,
                credentials_ref,
                wallet_ref,
                is_active,
                trading_enabled,
                raw_metadata,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :venue_account_key,
                :client_ref_id,
                :venue,
                :environment,
                :venue_native_account_id,
                :account_address,
                :account_label,
                NULL,
                :credentials_ref,
                :wallet_ref,
                true,
                true,
                CAST(:raw_metadata AS JSON),
                now(),
                now()
            )
            ON CONFLICT (venue_account_key) DO NOTHING
            """
        ),
        {
            "id": venue_account_id,
            "venue_account_key": active_account_key,
            "client_ref_id": inserted_client_id,
            "venue": exchange_venue,
            "environment": app_environment,
            "venue_native_account_id": account_address or active_account_key,
            "account_address": account_address or None,
            "account_label": account_label,
            "credentials_ref": credentials_ref or None,
            "wallet_ref": wallet_ref or None,
            "raw_metadata": json.dumps({"bootstrapped_from_migration": True}),
        },
    )
    inserted_account_id = op.get_bind().execute(
        sa.text("SELECT id FROM venue_accounts WHERE venue_account_key = :venue_account_key"),
        {"venue_account_key": active_account_key},
    ).scalar_one()

    bind.execute(
        sa.text(
            """
            INSERT INTO strategy_deployments (
                id,
                deployment_key,
                client_ref_id,
                venue_account_ref_id,
                family,
                enabled,
                allow_builder_deployed_for_strategy,
                allow_builder_deployed_for_trading,
                notes,
                metadata_json,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :deployment_key,
                :client_ref_id,
                :venue_account_ref_id,
                'money_flow',
                true,
                :allow_builder_strategy,
                :allow_builder_trading,
                :notes,
                CAST(:metadata_json AS JSON),
                now(),
                now()
            )
            ON CONFLICT (deployment_key) DO NOTHING
            """
        ),
        {
            "id": strategy_deployment_id,
            "deployment_key": active_deployment_key,
            "client_ref_id": inserted_client_id,
            "venue_account_ref_id": inserted_account_id,
            "allow_builder_strategy": _flag(
                "EXCHANGE_UNIVERSE_ALLOW_BUILDER_DEPLOYED_FOR_STRATEGY",
                False,
            ),
            "allow_builder_trading": _flag(
                "EXCHANGE_UNIVERSE_ALLOW_BUILDER_DEPLOYED_FOR_TRADING",
                False,
            ),
            "notes": "Bootstrapped from pre-Phase 4 single-account runtime.",
            "metadata_json": json.dumps({"bootstrapped_from_migration": True}),
        },
    )
    inserted_deployment_id = op.get_bind().execute(
        sa.text("SELECT id FROM strategy_deployments WHERE deployment_key = :deployment_key"),
        {"deployment_key": active_deployment_key},
    ).scalar_one()

    sleeve_rows = [
        {
            "id": sleeve_ids["sleeve_15m"],
            "strategy_deployment_ref_id": inserted_deployment_id,
            "sleeve_id": "sleeve_15m",
            "timeframe": "15m",
            "enabled": _flag("SLEEVE_15M_ENABLED", True),
            "capital_allocation_pct": "0.3400",
            "max_open_risk_pct": "0.0200",
            "strategy_overrides": json.dumps({
                "sleeve_id": "sleeve_15m",
                "timeframe": "15m",
                "enabled": _flag("SLEEVE_15M_ENABLED", True),
                "min_history_bars": 35,
                "rsi_floor": 52.0,
                "rsi_ceiling": 66.0,
                "overbought_rsi": 72.0,
                "require_macd_confirmation": True,
                "allow_pullback_entries": True,
                "allow_continuation_entries": True,
                "max_extension_pct_above_ema5": 0.018,
                "trim_on_overbought_rsi": True,
                "trim_rsi": 78.0,
                "close_on_ma_break": True,
                "close_on_macd_rollover": True,
            }),
        },
        {
            "id": sleeve_ids["sleeve_1h"],
            "strategy_deployment_ref_id": inserted_deployment_id,
            "sleeve_id": "sleeve_1h",
            "timeframe": "1h",
            "enabled": _flag("SLEEVE_1H_ENABLED", True),
            "capital_allocation_pct": "0.3300",
            "max_open_risk_pct": "0.0200",
            "strategy_overrides": json.dumps({
                "sleeve_id": "sleeve_1h",
                "timeframe": "1h",
                "enabled": _flag("SLEEVE_1H_ENABLED", True),
                "min_history_bars": 35,
                "rsi_floor": 50.0,
                "rsi_ceiling": 68.0,
                "overbought_rsi": 74.0,
                "require_macd_confirmation": True,
                "allow_pullback_entries": True,
                "allow_continuation_entries": True,
                "max_extension_pct_above_ema5": 0.02,
                "trim_on_overbought_rsi": True,
                "trim_rsi": 80.0,
                "close_on_ma_break": True,
                "close_on_macd_rollover": True,
            }),
        },
        {
            "id": sleeve_ids["sleeve_4h"],
            "strategy_deployment_ref_id": inserted_deployment_id,
            "sleeve_id": "sleeve_4h",
            "timeframe": "4h",
            "enabled": _flag("SLEEVE_4H_ENABLED", True),
            "capital_allocation_pct": "0.3300",
            "max_open_risk_pct": "0.0200",
            "strategy_overrides": json.dumps({
                "sleeve_id": "sleeve_4h",
                "timeframe": "4h",
                "enabled": _flag("SLEEVE_4H_ENABLED", True),
                "min_history_bars": 40,
                "rsi_floor": 48.0,
                "rsi_ceiling": 70.0,
                "overbought_rsi": 76.0,
                "require_macd_confirmation": True,
                "allow_pullback_entries": True,
                "allow_continuation_entries": True,
                "max_extension_pct_above_ema5": 0.025,
                "trim_on_overbought_rsi": True,
                "trim_rsi": 82.0,
                "close_on_ma_break": True,
                "close_on_macd_rollover": True,
            }),
        },
    ]
    for row in sleeve_rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO sleeve_deployment_configs (
                    id,
                    strategy_deployment_ref_id,
                    sleeve_id,
                    timeframe,
                    enabled,
                    capital_allocation_pct,
                    max_open_risk_pct,
                    strategy_overrides,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :strategy_deployment_ref_id,
                    :sleeve_id,
                    :timeframe,
                    :enabled,
                    :capital_allocation_pct,
                    :max_open_risk_pct,
                    CAST(:strategy_overrides AS JSON),
                    now(),
                    now()
                )
                ON CONFLICT (strategy_deployment_ref_id, sleeve_id) DO NOTHING
                """
            ),
            row,
        )

    bind.execute(
        sa.text(
            """
            UPDATE positions
            SET venue_account_ref_id = :venue_account_ref_id
            WHERE environment = :environment
              AND venue = :venue
              AND venue_account_ref_id IS NULL
              AND (
                  (:account_address <> '' AND account_address = :account_address)
                  OR (:account_address = '' AND account_address IS NULL)
              )
            """
        ),
        {
            "venue_account_ref_id": inserted_account_id,
            "environment": app_environment,
            "venue": exchange_venue,
            "account_address": account_address,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE submitted_orders
            SET venue_account_ref_id = :venue_account_ref_id
            WHERE environment = :environment
              AND venue = :venue
              AND venue_account_ref_id IS NULL
              AND (
                  (:account_address <> '' AND account_address = :account_address)
                  OR (:account_address = '' AND account_address IS NULL)
              )
            """
        ),
        {
            "venue_account_ref_id": inserted_account_id,
            "environment": app_environment,
            "venue": exchange_venue,
            "account_address": account_address,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE fills
            SET venue_account_ref_id = :venue_account_ref_id
            WHERE environment = :environment
              AND venue = :venue
              AND venue_account_ref_id IS NULL
              AND (
                  (:account_address <> '' AND account_address = :account_address)
                  OR (:account_address = '' AND account_address IS NULL)
              )
            """
        ),
        {
            "venue_account_ref_id": inserted_account_id,
            "environment": app_environment,
            "venue": exchange_venue,
            "account_address": account_address,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE exchange_account_snapshots
            SET venue_account_ref_id = :venue_account_ref_id
            WHERE environment = :environment
              AND venue = :venue
              AND venue_account_ref_id IS NULL
              AND (
                  (:account_address <> '' AND account_address = :account_address)
                  OR (:account_address = '' AND account_address IS NULL)
              )
            """
        ),
        {
            "venue_account_ref_id": inserted_account_id,
            "environment": app_environment,
            "venue": exchange_venue,
            "account_address": account_address,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE portfolio_snapshots
            SET venue_account_ref_id = :venue_account_ref_id
            WHERE environment = :environment
              AND venue_account_ref_id IS NULL
            """
        ),
        {
            "venue_account_ref_id": inserted_account_id,
            "environment": app_environment,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE position_attribution_overlays overlay
            SET venue_account_ref_id = positions.venue_account_ref_id
            FROM positions
            WHERE overlay.environment = :environment
              AND overlay.venue = :venue
              AND overlay.venue_account_ref_id IS NULL
              AND overlay.position_id = positions.position_id
              AND positions.venue_account_ref_id IS NOT NULL
            """
        ),
        {"environment": app_environment, "venue": exchange_venue},
    )
    bind.execute(
        sa.text(
            """
            UPDATE signal_events
            SET client_ref_id = :client_ref_id,
                venue_account_ref_id = :venue_account_ref_id,
                strategy_deployment_ref_id = :strategy_deployment_ref_id,
                deployment_key = :deployment_key
            WHERE environment = :environment
              AND strategy_deployment_ref_id IS NULL
            """
        ),
        {
            "client_ref_id": inserted_client_id,
            "venue_account_ref_id": inserted_account_id,
            "strategy_deployment_ref_id": inserted_deployment_id,
            "deployment_key": active_deployment_key,
            "environment": app_environment,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE strategy_decisions
            SET client_ref_id = :client_ref_id,
                venue_account_ref_id = :venue_account_ref_id,
                strategy_deployment_ref_id = :strategy_deployment_ref_id,
                deployment_key = :deployment_key
            WHERE environment = :environment
              AND strategy_deployment_ref_id IS NULL
            """
        ),
        {
            "client_ref_id": inserted_client_id,
            "venue_account_ref_id": inserted_account_id,
            "strategy_deployment_ref_id": inserted_deployment_id,
            "deployment_key": active_deployment_key,
            "environment": app_environment,
        },
    )
    bind.execute(
        sa.text(
            """
            UPDATE order_intents
            SET client_ref_id = :client_ref_id,
                venue_account_ref_id = :venue_account_ref_id,
                strategy_deployment_ref_id = :strategy_deployment_ref_id
            WHERE environment = :environment
              AND strategy_deployment_ref_id IS NULL
            """
        ),
        {
            "client_ref_id": inserted_client_id,
            "venue_account_ref_id": inserted_account_id,
            "strategy_deployment_ref_id": inserted_deployment_id,
            "environment": app_environment,
        },
    )

    with op.batch_alter_table("clients") as batch_op:
        batch_op.alter_column("is_active", server_default=None)
    with op.batch_alter_table("venue_accounts") as batch_op:
        batch_op.alter_column("is_active", server_default=None)
        batch_op.alter_column("trading_enabled", server_default=None)
        batch_op.alter_column("raw_metadata", server_default=None)
    with op.batch_alter_table("strategy_deployments") as batch_op:
        batch_op.alter_column("enabled", server_default=None)
        batch_op.alter_column("allow_builder_deployed_for_strategy", server_default=None)
        batch_op.alter_column("allow_builder_deployed_for_trading", server_default=None)
        batch_op.alter_column("metadata_json", server_default=None)
    with op.batch_alter_table("sleeve_deployment_configs") as batch_op:
        batch_op.alter_column("enabled", server_default=None)
        batch_op.alter_column("strategy_overrides", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("order_intents") as batch_op:
        batch_op.drop_index("ix_order_intents_strategy_deployment_ref_id")
        batch_op.drop_index("ix_order_intents_venue_account_ref_id")
        batch_op.drop_index("ix_order_intents_client_ref_id")
        batch_op.drop_constraint("fk_intent_deployment", type_="foreignkey")
        batch_op.drop_constraint("fk_intent_venue_account", type_="foreignkey")
        batch_op.drop_constraint("fk_intent_client", type_="foreignkey")
        batch_op.drop_column("strategy_deployment_ref_id")
        batch_op.drop_column("venue_account_ref_id")
        batch_op.drop_column("client_ref_id")

    with op.batch_alter_table("strategy_decisions") as batch_op:
        batch_op.drop_index("ix_strategy_decisions_deployment_key")
        batch_op.drop_index("ix_strategy_decisions_strategy_deployment_ref_id")
        batch_op.drop_index("ix_strategy_decisions_venue_account_ref_id")
        batch_op.drop_index("ix_strategy_decisions_client_ref_id")
        batch_op.drop_constraint("fk_decision_deployment", type_="foreignkey")
        batch_op.drop_constraint("fk_decision_venue_account", type_="foreignkey")
        batch_op.drop_constraint("fk_decision_client", type_="foreignkey")
        batch_op.drop_column("deployment_key")
        batch_op.drop_column("strategy_deployment_ref_id")
        batch_op.drop_column("venue_account_ref_id")
        batch_op.drop_column("client_ref_id")

    with op.batch_alter_table("signal_events") as batch_op:
        batch_op.drop_index("ix_signal_events_deployment_key")
        batch_op.drop_index("ix_signal_events_strategy_deployment_ref_id")
        batch_op.drop_index("ix_signal_events_venue_account_ref_id")
        batch_op.drop_index("ix_signal_events_client_ref_id")
        batch_op.drop_constraint("fk_signal_deployment", type_="foreignkey")
        batch_op.drop_constraint("fk_signal_venue_account", type_="foreignkey")
        batch_op.drop_constraint("fk_signal_client", type_="foreignkey")
        batch_op.drop_column("deployment_key")
        batch_op.drop_column("strategy_deployment_ref_id")
        batch_op.drop_column("venue_account_ref_id")
        batch_op.drop_column("client_ref_id")

    with op.batch_alter_table("position_attribution_overlays") as batch_op:
        batch_op.drop_index("ix_position_attribution_overlays_venue_account_ref_id")
        batch_op.drop_constraint("fk_pos_attr_overlay_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    with op.batch_alter_table("portfolio_snapshots") as batch_op:
        batch_op.drop_index("ix_portfolio_snapshots_venue_account_ref_id")
        batch_op.drop_constraint("fk_portfolio_snap_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    with op.batch_alter_table("exchange_account_snapshots") as batch_op:
        batch_op.drop_index("ix_exchange_account_snapshots_venue_account_ref_id")
        batch_op.drop_constraint("fk_exch_acct_snap_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    with op.batch_alter_table("fills") as batch_op:
        batch_op.drop_index("ix_fills_venue_account_ref_id")
        batch_op.drop_constraint("fk_fills_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    with op.batch_alter_table("submitted_orders") as batch_op:
        batch_op.drop_index("ix_submitted_orders_venue_account_ref_id")
        batch_op.drop_constraint("fk_sub_orders_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    with op.batch_alter_table("positions") as batch_op:
        batch_op.drop_index("ix_positions_venue_account_ref_id")
        batch_op.drop_constraint("fk_pos_venue_account", type_="foreignkey")
        batch_op.drop_column("venue_account_ref_id")

    op.drop_index("ix_sleeve_deployment_configs_deployment_sleeve", table_name="sleeve_deployment_configs")
    op.drop_table("sleeve_deployment_configs")
    op.drop_index("ix_strategy_deployments_account_family_enabled", table_name="strategy_deployments")
    op.drop_index("ix_strategy_deployments_deployment_key", table_name="strategy_deployments")
    op.drop_table("strategy_deployments")
    op.drop_index("ix_venue_accounts_venue_environment_address", table_name="venue_accounts")
    op.drop_index("ix_venue_accounts_client_venue_environment", table_name="venue_accounts")
    op.drop_index("ix_venue_accounts_venue_account_key", table_name="venue_accounts")
    op.drop_table("venue_accounts")
    op.drop_index("ix_clients_client_key", table_name="clients")
    op.drop_table("clients")
