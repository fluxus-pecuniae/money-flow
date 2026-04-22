"""Venue adapter registry and factory."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from core.config.settings import AppSettings, get_settings
from core.domain.enums import Venue
from core.domain.models import VenueIntegrationSummary
from core.interfaces.services import ExchangeAdapter, VenueRegistryService
from db.session import SessionLocal
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.binance.adapter import BinanceExchangeAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.kraken.adapter import KrakenExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from services.runtime.context import DefaultRuntimeContextService

_VENUE_SUPPORT_LEVELS = {
    Venue.HYPERLIQUID: HyperliquidExchangeAdapter.support_level,
    Venue.ASTER: AsterExchangeAdapter.support_level,
    Venue.BINANCE: BinanceExchangeAdapter.support_level,
    Venue.OKX: OkxExchangeAdapter.support_level,
    Venue.COINBASE_ADVANCED_TRADE: CoinbaseAdvancedTradeExchangeAdapter.support_level,
    Venue.KRAKEN: KrakenExchangeAdapter.support_level,
}

_ADAPTER_SUBMISSION_IMPLEMENTATION = {
    Venue.HYPERLIQUID: HyperliquidExchangeAdapter.adapter_supports_order_submission,
    Venue.ASTER: AsterExchangeAdapter.adapter_supports_order_submission,
    Venue.BINANCE: BinanceExchangeAdapter.adapter_supports_order_submission,
    Venue.OKX: OkxExchangeAdapter.adapter_supports_order_submission,
    Venue.COINBASE_ADVANCED_TRADE: CoinbaseAdvancedTradeExchangeAdapter.adapter_supports_order_submission,
    Venue.KRAKEN: KrakenExchangeAdapter.adapter_supports_order_submission,
}


class DefaultVenueRegistryService(VenueRegistryService):
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory: Any = SessionLocal,
        adapter_overrides: dict[str, ExchangeAdapter] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self._adapter_overrides = adapter_overrides or {}
        self._cache: dict[str, ExchangeAdapter] = {}

    async def list_supported_venues(self) -> Sequence[VenueIntegrationSummary]:
        summaries: list[VenueIntegrationSummary] = []
        for venue, integration in self.settings.venue_integrations.items():
            summaries.append(
                VenueIntegrationSummary(
                    venue=venue.value,
                    display_name=integration.name,
                    enabled=integration.enabled,
                    read_only_mode=integration.read_only_mode,
                    dry_run_mode=integration.dry_run_mode,
                    submission_enabled=integration.submission_enabled,
                    execution_authorized=integration.submission_authorized,
                    adapter_submission_implemented=_ADAPTER_SUBMISSION_IMPLEMENTATION[venue],
                    live_submission_phase_enabled=self.settings.execution.live_submission_phase_enabled,
                    support_level=_VENUE_SUPPORT_LEVELS[venue],
                )
            )
        return summaries

    async def get_adapter(self, venue: str) -> ExchangeAdapter:
        venue_key = venue.lower()
        if venue_key in self._adapter_overrides:
            return self._adapter_overrides[venue_key]
        if venue_key in self._cache:
            return self._cache[venue_key]

        runtime_context = DefaultRuntimeContextService(self.settings, session_factory=self._session_factory)
        if venue_key == Venue.HYPERLIQUID.value:
            adapter: ExchangeAdapter = HyperliquidExchangeAdapter(
                self.settings,
                session_factory=self._session_factory,
                runtime_context_service=runtime_context,
            )
        elif venue_key == Venue.ASTER.value:
            adapter = AsterExchangeAdapter(self.settings, session_factory=self._session_factory)
        elif venue_key == Venue.BINANCE.value:
            adapter = BinanceExchangeAdapter(self.settings, session_factory=self._session_factory)
        elif venue_key == Venue.OKX.value:
            adapter = OkxExchangeAdapter(self.settings, session_factory=self._session_factory)
        elif venue_key in {Venue.COINBASE_ADVANCED_TRADE.value, Venue.COINBASE.value}:
            adapter = CoinbaseAdvancedTradeExchangeAdapter(
                self.settings,
                session_factory=self._session_factory,
            )
        elif venue_key == Venue.KRAKEN.value:
            adapter = KrakenExchangeAdapter(self.settings, session_factory=self._session_factory)
        else:
            raise ValueError(f"Unsupported venue: {venue}")

        self._cache[venue_key] = adapter
        return adapter
