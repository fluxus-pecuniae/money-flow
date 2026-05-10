"""Hyperliquid order precision helpers.

Hyperliquid perpetual metadata exposes size precision as ``szDecimals`` while
price validity is governed by venue precision rules rather than a simple tick
field in ``meta``.  These helpers keep Decimal formatting deterministic and
avoid binary float rounding.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


@dataclass(frozen=True)
class HyperliquidFormattedValue:
    raw_value: Decimal
    formatted_value: Decimal
    wire_value: str
    reason: str


@dataclass(frozen=True)
class HyperliquidPrecisionFormatter:
    asset_id: int
    symbol: str
    sz_decimals: int

    @property
    def max_price_decimals(self) -> int:
        return max(0, 6 - int(self.sz_decimals))

    @property
    def size_step(self) -> Decimal:
        return Decimal("1").scaleb(-int(self.sz_decimals))

    def _decimal_places_allowed_by_significant_figures(self, value: Decimal) -> int:
        if value <= 0:
            return 0
        normalized = value.normalize()
        if normalized == normalized.to_integral_value():
            # Hyperliquid allows integer prices even when they exceed five
            # significant figures.
            return 0
        adjusted = normalized.adjusted()
        return max(0, 5 - adjusted - 1)

    @staticmethod
    def _quantize_down(value: Decimal, decimal_places: int) -> Decimal:
        exponent = Decimal("1").scaleb(-decimal_places)
        return value.quantize(exponent, rounding=ROUND_DOWN)

    @staticmethod
    def _wire(value: Decimal) -> str:
        normalized = value.normalize()
        return f"{normalized:f}"

    def format_price_down(self, value: Decimal) -> HyperliquidFormattedValue:
        if value <= 0:
            return HyperliquidFormattedValue(
                raw_value=value,
                formatted_value=Decimal("0"),
                wire_value="0",
                reason="price_non_positive",
            )
        allowed_decimals = min(
            self.max_price_decimals,
            self._decimal_places_allowed_by_significant_figures(value),
        )
        formatted = self._quantize_down(value, allowed_decimals)
        return HyperliquidFormattedValue(
            raw_value=value,
            formatted_value=formatted,
            wire_value=self._wire(formatted),
            reason=(
                "price_formatted_down_5_sig_figs_and_"
                f"max_{self.max_price_decimals}_decimals"
            ),
        )

    def format_size_down(self, value: Decimal) -> HyperliquidFormattedValue:
        if value <= 0:
            return HyperliquidFormattedValue(
                raw_value=value,
                formatted_value=Decimal("0"),
                wire_value="0",
                reason="size_non_positive",
            )
        step = self.size_step
        formatted = (value // step) * step
        return HyperliquidFormattedValue(
            raw_value=value,
            formatted_value=formatted,
            wire_value=self._wire(formatted),
            reason=f"size_formatted_down_sz_decimals_{self.sz_decimals}",
        )


def hyperliquid_formatter_from_meta_asset(
    *,
    asset_id: int,
    asset: dict[str, object],
) -> HyperliquidPrecisionFormatter:
    return HyperliquidPrecisionFormatter(
        asset_id=asset_id,
        symbol=str(asset.get("name", "")).upper(),
        sz_decimals=int(asset.get("szDecimals", 0)),
    )
