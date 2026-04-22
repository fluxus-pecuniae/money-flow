"""Explicit Hyperliquid adapter contract for future exchange implementation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from core.domain.hyperliquid import (
    HyperliquidAccountState,
    HyperliquidReconciliationSnapshot,
    HyperliquidUniverseAsset,
    HyperliquidWalletContext,
    UniversePolicy,
)
from core.domain.models import Candle, ExchangeStatus, Instrument, OrderBookDepthSummary, TopOfBookSnapshot, VenueCapabilities


class HyperliquidAdapterContract(Protocol):
    async def sync_universe(self, policy: UniversePolicy) -> Sequence[HyperliquidUniverseAsset]: ...

    async def get_exchange_status(self) -> ExchangeStatus: ...

    async def get_venue_capabilities(self) -> VenueCapabilities: ...

    async def list_instruments(self) -> Sequence[Instrument]: ...

    async def normalize_perp_symbol(self, raw_symbol: str) -> str: ...

    async def map_asset_id(self, canonical_symbol: str) -> int | None: ...

    async def get_wallet_context(self) -> HyperliquidWalletContext: ...

    async def sync_account_state(self) -> HyperliquidAccountState: ...

    async def reconcile_open_orders(self) -> HyperliquidReconciliationSnapshot: ...

    async def reconcile_fills(self, limit: int = 100) -> HyperliquidReconciliationSnapshot: ...

    async def reconcile_positions(self) -> HyperliquidReconciliationSnapshot: ...

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]: ...

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None: ...

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None: ...

    async def switch_environment(self, use_testnet: bool) -> None: ...
