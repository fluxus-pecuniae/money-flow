"""Shared venue adapter helpers."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from core.domain.enums import MarketType, ProductType
from core.domain.models import Instrument, SymbolMetadata
from db.models import InstrumentModel, SymbolModel


def build_instrument_key(
    *,
    market_type: MarketType,
    product_type: ProductType,
    base_asset: str,
    quote_asset: str,
    settlement_asset: str | None,
) -> str:
    return (
        f"{market_type.value}:{product_type.value}:{base_asset.upper()}:"
        f"{quote_asset.upper()}:{(settlement_asset or '').upper()}"
    )


def persist_symbol_catalog(
    session_factory: Any,
    *,
    venue: str,
    symbols: Sequence[SymbolMetadata],
) -> None:
    with session_factory() as session:
        for item in symbols:
            instrument_model = session.scalar(
                select(InstrumentModel).where(InstrumentModel.instrument_key == item.instrument_key)
            )
            if instrument_model is None:
                instrument_model = InstrumentModel(
                    instrument_key=item.instrument_key,
                    canonical_symbol=item.base_asset,
                    market_type=item.market_type,
                    product_type=item.product_type,
                    base_asset=item.base_asset,
                    quote_asset=item.quote_asset,
                    settlement_asset=item.settlement_asset,
                    is_active=item.is_active,
                )
                session.add(instrument_model)
                session.flush()
            else:
                instrument_model.canonical_symbol = item.base_asset
                instrument_model.market_type = item.market_type
                instrument_model.product_type = item.product_type
                instrument_model.base_asset = item.base_asset
                instrument_model.quote_asset = item.quote_asset
                instrument_model.settlement_asset = item.settlement_asset
                instrument_model.is_active = item.is_active

            model = session.scalar(
                select(SymbolModel).where(
                    SymbolModel.venue == venue,
                    SymbolModel.exchange_symbol == item.exchange_symbol,
                )
            )
            if model is None:
                model = SymbolModel(
                    instrument_ref_id=instrument_model.id,
                    venue=venue,
                    symbol=item.symbol,
                    exchange_symbol=item.exchange_symbol,
                    venue_asset_id=item.venue_asset_id,
                    asset_id=item.asset_id,
                    market_type=item.market_type,
                    product_type=item.product_type,
                    base_asset=item.base_asset,
                    quote_asset=item.quote_asset,
                    settlement_asset=item.settlement_asset,
                    price_tick_size=item.price_tick_size,
                    quantity_step_size=item.quantity_step_size,
                    min_order_size=item.min_order_size,
                    size_decimals=_size_decimals(item.quantity_step_size),
                    max_leverage=item.raw_metadata.get("max_leverage") if isinstance(item.raw_metadata, dict) else None,
                    only_isolated=bool(item.raw_metadata.get("only_isolated", False))
                    if isinstance(item.raw_metadata, dict)
                    else False,
                    is_perpetual=item.is_perpetual,
                    is_builder_deployed=item.is_builder_deployed,
                    is_strategy_eligible=item.is_strategy_eligible,
                    is_trading_eligible=item.is_trading_eligible,
                    is_active=item.is_active,
                    raw_metadata=item.raw_metadata,
                )
                session.add(model)
            else:
                model.instrument_ref_id = instrument_model.id
                model.symbol = item.symbol
                model.venue_asset_id = item.venue_asset_id
                model.asset_id = item.asset_id
                model.market_type = item.market_type
                model.product_type = item.product_type
                model.base_asset = item.base_asset
                model.quote_asset = item.quote_asset
                model.settlement_asset = item.settlement_asset
                model.price_tick_size = item.price_tick_size
                model.quantity_step_size = item.quantity_step_size
                model.min_order_size = item.min_order_size
                model.size_decimals = _size_decimals(item.quantity_step_size)
                model.max_leverage = (
                    item.raw_metadata.get("max_leverage") if isinstance(item.raw_metadata, dict) else None
                )
                model.only_isolated = (
                    bool(item.raw_metadata.get("only_isolated", False))
                    if isinstance(item.raw_metadata, dict)
                    else False
                )
                model.is_perpetual = item.is_perpetual
                model.is_builder_deployed = item.is_builder_deployed
                model.is_strategy_eligible = item.is_strategy_eligible
                model.is_trading_eligible = item.is_trading_eligible
                model.is_active = item.is_active
                model.raw_metadata = item.raw_metadata
        session.commit()


def list_instruments_for_venue(session_factory: Any, *, venue: str) -> list[Instrument]:
    with session_factory() as session:
        rows = session.execute(
            select(InstrumentModel, SymbolModel)
            .join(SymbolModel, SymbolModel.instrument_ref_id == InstrumentModel.id)
            .where(SymbolModel.venue == venue)
            .order_by(InstrumentModel.base_asset.asc(), SymbolModel.exchange_symbol.asc())
        ).all()
    seen: set[str] = set()
    instruments: list[Instrument] = []
    for instrument_model, _ in rows:
        if instrument_model.id in seen:
            continue
        seen.add(instrument_model.id)
        instruments.append(
            Instrument(
                instrument_key=instrument_model.instrument_key,
                instrument_ref_id=instrument_model.id,
                canonical_symbol=instrument_model.canonical_symbol,
                market_type=instrument_model.market_type,
                product_type=instrument_model.product_type,
                base_asset=instrument_model.base_asset,
                quote_asset=instrument_model.quote_asset,
                settlement_asset=instrument_model.settlement_asset,
                is_active=instrument_model.is_active,
            )
        )
    return instruments


def _size_decimals(step: Decimal) -> int | None:
    normalized = step.normalize()
    if normalized == normalized.to_integral():
        return 0
    return abs(normalized.as_tuple().exponent)
