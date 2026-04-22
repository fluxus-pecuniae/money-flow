"""Hyperliquid-specific domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from core.domain.enums import Environment


@dataclass(slots=True)
class HyperliquidUniverseAsset:
    venue: str
    canonical_symbol: str
    exchange_symbol: str
    asset_id: int
    base_asset: str
    quote_asset: str
    is_perpetual: bool
    is_builder_deployed: bool
    raw_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class UniversePolicy:
    include_standard_perp_universe: bool
    include_builder_deployed_in_catalog: bool
    allow_builder_deployed_for_strategy: bool
    allow_builder_deployed_for_trading: bool


@dataclass(slots=True)
class HyperliquidWalletContext:
    environment: Environment
    api_base_url: str
    websocket_base_url: str
    account_address: str
    signer_label: str
    can_sign_orders: bool


@dataclass(slots=True)
class HyperliquidAccountState:
    environment: Environment
    account_address: str
    equity: Decimal
    available_balance: Decimal
    margin_used: Decimal
    unrealized_pnl: Decimal
    observed_at: datetime


@dataclass(slots=True)
class HyperliquidReconciliationSnapshot:
    environment: Environment
    venue: str
    open_order_ids: list[str] = field(default_factory=list)
    fill_ids: list[str] = field(default_factory=list)
    position_ids: list[str] = field(default_factory=list)
    reconciled_at: datetime | None = None
    cursor: str | None = None
