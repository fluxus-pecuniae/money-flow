"""Kraken venue adapter."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import urllib.parse
from typing import Any

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    MarketType,
    OrderSide,
    OrderType,
    ProductType,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Timeframe,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.models import (
    Candle,
    ExchangeAccountSnapshot,
    Fill,
    OrderIntent,
    SubmittedOrder,
    SubmittedOrderLifecycleUpdate,
    SymbolMetadata,
    TopOfBookSnapshot,
    VenueCapabilities,
    VenuePrivateOpenOrder,
)
from db.session import SessionLocal
from services.exchange.base import ReadOnlyVenueAdapter, VenueAdapterError, decimal_or
from services.exchange.common import build_instrument_key

_PAIR_MAP = {
    "BTC": "XBT/USD",
    "ETH": "ETH/USD",
}


def _kraken_pair(symbol: str) -> str:
    return _PAIR_MAP.get(symbol.upper(), f"{symbol.upper()}/USD")


def _kraken_timeframe(timeframe: str | Timeframe) -> int:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
    if tf not in mapping:
        raise VenueAdapterError(f"Unsupported Kraken timeframe: {tf}")
    return mapping[tf]


def _timeframe_delta(timeframe: str | Timeframe) -> timedelta:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    return mapping[tf]


class KrakenExchangeAdapter(ReadOnlyVenueAdapter):
    account_model = "api_account"
    support_level = VenueSupportLevel.EXECUTION_PREPARABLE
    adapter_supports_order_submission = True
    adapter_supports_order_cancel = True
    adapter_supports_order_amend = True
    supports_order_preview = True
    supports_account_snapshot = True
    supports_open_orders_query = True
    supports_open_positions_query = False
    supports_recent_fills_query = True
    supports_reduce_only_orders = False
    supports_client_order_ids = True
    supported_order_types = (OrderType.MARKET, OrderType.LIMIT)
    supported_time_in_force = ("gtc", "ioc")
    open_orders_state_source = "venue_query"
    recent_fills_state_source = "venue_query"

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        transport=None,
        session_factory=SessionLocal,
    ) -> None:
        resolved_settings = settings or get_settings()
        super().__init__(
            resolved_settings.kraken_integration,
            resolved_settings,
            transport=transport,
            session_factory=session_factory,
        )

    async def _ping(self) -> None:
        await self._request("GET", "/0/public/Time", None)

    async def _fetch_symbol_metadata(self) -> Sequence[SymbolMetadata]:
        payload = await self._request("GET", "/0/public/AssetPairs", None)
        metadata: list[SymbolMetadata] = []
        for pair_name, item in payload.get("result", {}).items():
            if ".d" in pair_name.lower():
                continue
            base_asset = str(item.get("base", "")).replace("XBT", "BTC").replace("Z", "").upper()
            quote_asset = str(item.get("quote", "")).replace("Z", "").replace("XBT", "BTC").upper()
            if not base_asset or not quote_asset:
                continue
            metadata.append(
                SymbolMetadata(
                    instrument_key=build_instrument_key(
                        market_type=MarketType.SPOT,
                        product_type=ProductType.SPOT,
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        settlement_asset=None,
                    ),
                    instrument_ref_id=None,
                    venue=Venue.KRAKEN.value,
                    symbol=base_asset,
                    exchange_symbol=pair_name.upper(),
                    venue_asset_id=pair_name.upper(),
                    market_type=MarketType.SPOT,
                    product_type=ProductType.SPOT,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    settlement_asset=None,
                    price_tick_size=decimal_or(item.get("tick_size"), "0.1"),
                    quantity_step_size=decimal_or(item.get("ordermin"), "0.0001"),
                    min_order_size=decimal_or(item.get("ordermin"), "0.0001"),
                    is_active=True,
                    asset_id=None,
                    is_perpetual=False,
                    is_builder_deployed=False,
                    is_strategy_eligible=True,
                    is_trading_eligible=False,
                    raw_metadata={"venue": "kraken"},
                )
            )
        return metadata

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue.KRAKEN,
            support_level=self.support_level,
            supports_spot=True,
            supports_perpetuals=False,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=True,
            supports_account_sync=True,
            supports_top_of_book=True,
            supports_depth_summary=True,
            supports_order_submission=True,
            supports_order_cancel=True,
            supports_order_amend=True,
            supports_recent_fills_query=self.supports_recent_fills_query,
            adapter_supports_order_submission=self.adapter_supports_order_submission,
            adapter_supports_order_cancel=self.adapter_supports_order_cancel,
            adapter_supports_order_amend=self.adapter_supports_order_amend,
            adapter_supports_user_streams=self.adapter_supports_user_streams,
            supports_order_preview=True,
            supports_account_snapshot=True,
            supports_open_orders_query=self.supports_open_orders_query,
            supports_open_positions_query=False,
            supports_reduce_only_orders=False,
            supports_client_order_ids=True,
            supports_demo_mode=False,
            supports_subaccounts=False,
            supported_order_types=list(self.supported_order_types),
            supported_time_in_force=list(self.supported_time_in_force),
            account_model=self.account_model,
            notes=(
                "Kraken currently covers spot catalog sync, top-of-book, preview/preflight, "
                "an account-targeted signed submit path, truthful cancel acknowledgement, "
                "native limit-order amend for the current spot scope, reconciliation for the "
                "current spot scope, and direct private open-order plus recent-fill polling."
            ),
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]:
        pair = _kraken_pair(symbol)
        payload = await self._request(
            "GET",
            "/0/public/OHLC",
            {
                "pair": pair,
                "interval": _kraken_timeframe(timeframe),
                "since": int(start_time_ms / 1000),
            },
        )
        result = payload.get("result", {})
        rows = next((value for key, value in result.items() if key != "last"), [])
        candles: list[Candle] = []
        delta = _timeframe_delta(timeframe)
        for row in rows:
            open_time = datetime.fromtimestamp(int(row[0]), tz=UTC)
            candles.append(
                Candle(
                    instrument_key=build_instrument_key(
                        market_type=MarketType.SPOT,
                        product_type=ProductType.SPOT,
                        base_asset=symbol.upper(),
                        quote_asset="USD",
                        settlement_asset=None,
                    ),
                    instrument_ref_id=None,
                    venue=Venue.KRAKEN.value,
                    symbol=symbol.upper(),
                    timeframe=Timeframe(timeframe),
                    open_time=open_time,
                    close_time=open_time + delta,
                    open=decimal_or(row[1]),
                    high=decimal_or(row[2]),
                    low=decimal_or(row[3]),
                    close=decimal_or(row[4]),
                    volume=decimal_or(row[6]),
                    trade_count=None,
                )
            )
        return candles

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        payload = await self._request("GET", "/0/public/Depth", {"pair": _kraken_pair(symbol), "count": 1})
        result = payload.get("result", {})
        book = next(iter(result.values()), {})
        bid = (book.get("bids") or [[None, None]])[0]
        ask = (book.get("asks") or [[None, None]])[0]
        return TopOfBookSnapshot(
            instrument_key=build_instrument_key(
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset=symbol.upper(),
                quote_asset="USD",
                settlement_asset=None,
            ),
            instrument_ref_id=None,
            venue=Venue.KRAKEN.value,
            symbol=symbol.upper(),
            bid_price=decimal_or(bid[0], "0"),
            bid_size=decimal_or(bid[1], "0"),
            ask_price=decimal_or(ask[0], "0"),
            ask_size=decimal_or(ask[1], "0"),
            observed_at=datetime.now(UTC),
        )

    async def read_account_snapshot(self) -> ExchangeAccountSnapshot | None:
        default_context = self._resolve_execution_context(None)
        return await self._read_account_snapshot_for_context(default_context)

    async def _read_account_snapshot_for_context(self, context) -> ExchangeAccountSnapshot | None:
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            return None
        endpoint = "/0/private/Balance"
        nonce = str(int(datetime.now(UTC).timestamp() * 1000))
        body = {"nonce": nonce}
        post_data = urllib.parse.urlencode(sorted(body.items()))
        sha256_payload = hashlib.sha256((nonce + post_data).encode("utf-8")).digest()
        signature_payload = endpoint.encode("utf-8") + sha256_payload
        headers = {
            "API-Key": api_key,
            "API-Sign": self._hmac_sha512_base64(api_secret, signature_payload),
        }
        payload = await self._request("POST", endpoint, body=body, headers=headers)
        balances = payload.get("result", {})
        usd_balance = decimal_or(balances.get("ZUSD") or balances.get("USD"), "0")
        return ExchangeAccountSnapshot(
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.KRAKEN.value,
            environment=self._integration_environment,
            account_address=context.account_address or context.account_identifier,
            equity=usd_balance,
            available_balance=usd_balance,
            margin_used=decimal_or("0"),
            unrealized_pnl=decimal_or("0"),
            total_position_notional=decimal_or("0"),
            observed_at=datetime.now(UTC),
        )

    async def submit_order(self, intent: OrderIntent):
        if intent is None:
            raise VenueAdapterError(
                "Kraken submission requires a concrete child intent.",
                reason_codes=["missing_order_intent"],
            )
        preview = await self.prepare_order_preview(intent)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE or preview.payload is None:
            raise VenueAdapterError(
                "Kraken order is not venue-preparable.",
                reason_codes=list(preview.reason_codes or ["preview_rejected"]),
                payload={"prepared_order_preview": preview.payload or {}},
            )
        context = self._resolve_execution_context(intent.venue_account_ref_id)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Kraken submission requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        endpoint, body = self._submission_request_from_preview(preview)
        nonce = str(int(datetime.now(UTC).timestamp() * 1000))
        signed_body = {"nonce": nonce, **body}
        post_data = self._render_form_body(sorted(signed_body.items()))
        sha256_payload = hashlib.sha256((nonce + post_data).encode("utf-8")).digest()
        signature_payload = endpoint.encode("utf-8") + sha256_payload
        headers = {
            "API-Key": api_key,
            "API-Sign": self._hmac_sha512_base64(api_secret, signature_payload),
        }
        response = await self._request_form_exact("POST", endpoint, rendered_body=post_data, headers=headers)
        return self._submitted_order_from_response(
            intent=intent,
            preview=preview,
            response=response,
            context=context,
        )

    async def reconcile_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Kraken reconciliation requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.exchange_order_id is None:
            return self._missing_order_update(submitted_order, {})
        endpoint = "/0/private/QueryOrders"
        payload = await self._signed_private_request(
            context,
            endpoint=endpoint,
            body={
                "txid": submitted_order.exchange_order_id,
                "trades": True,
            },
        )
        if payload.get("error"):
            return self._missing_order_update(submitted_order, payload)
        result = payload.get("result", {})
        order = result.get(submitted_order.exchange_order_id) if isinstance(result, dict) else None
        if not isinstance(order, dict):
            return self._missing_order_update(submitted_order, payload)
        return self._reconciliation_update_from_order_payload(submitted_order, order)

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Kraken cancellation requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.exchange_order_id is None:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_missing_order_identity"],
                message="Kraken cancellation requires an exchange order id.",
            )
        response = await self._signed_private_request(
            context,
            endpoint="/0/private/CancelOrder",
            body={"txid": submitted_order.exchange_order_id},
        )
        if payload_errors := response.get("error"):
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_rejected"],
                message=str(payload_errors[0] if isinstance(payload_errors, list) and payload_errors else payload_errors),
                raw_payload=response,
            )
        result = response.get("result", {})
        if int(result.get("count", 0) or 0) <= 0:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_rejected"],
                message="Kraken did not acknowledge cancellation for the submitted order.",
                raw_payload=response,
            )
        return self._cancel_success_update(
            submitted_order=submitted_order,
            status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            event_type="cancel_acknowledged",
            status_reason_code="cancel_acknowledged",
            remaining_quantity=submitted_order.remaining_quantity,
            message="Kraken accepted the cancel request; reconciliation must still confirm final canceled state.",
            reason_codes=["cancel_acknowledged"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=response,
        )

    async def amend_order(
        self,
        submitted_order: SubmittedOrder,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Kraken amendment requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.order_type != OrderType.LIMIT:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_not_supported_for_order_type"],
                message="Kraken amendment is currently limited to limit orders in the implemented spot scope.",
            )
        if new_quantity is None and new_limit_price is None:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_no_changes_requested"],
                message="Kraken amendment requires at least one explicit quantity or limit-price change.",
            )
        filled_quantity = submitted_order.filled_quantity or Decimal("0")
        if new_quantity is not None and new_quantity <= filled_quantity:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_quantity_below_filled"],
                message="Kraken amendment cannot reduce the order quantity below already filled size in the current modeled scope.",
            )
        body: dict[str, object] = {}
        if submitted_order.exchange_order_id is not None:
            body["txid"] = submitted_order.exchange_order_id
        elif submitted_order.client_order_id:
            body["cl_ord_id"] = submitted_order.client_order_id
        else:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_missing_order_identity"],
                message="Kraken amendment requires the targeted exchange order id or client order id.",
            )
        if new_quantity is not None:
            body["order_qty"] = str(new_quantity)
        if new_limit_price is not None:
            body["limit_price"] = str(new_limit_price)
        response = await self._signed_private_request(
            context,
            endpoint="/0/private/AmendOrder",
            body=body,
        )
        if payload_errors := response.get("error"):
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_rejected"],
                message=str(payload_errors[0] if isinstance(payload_errors, list) and payload_errors else payload_errors),
                raw_payload=response,
            )
        return self._amend_acknowledged_update(
            submitted_order=submitted_order,
            new_quantity=new_quantity,
            new_limit_price=new_limit_price,
            message="Kraken accepted the amend request; reconciliation must still confirm the refreshed working state.",
            raw_payload=response,
        )

    async def _fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            return await super()._fetch_open_orders_with_source(venue_account_ref_id=venue_account_ref_id)
        payload = await self._signed_private_request(
            context,
            endpoint="/0/private/OpenOrders",
            body={"trades": True},
        )
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        open_orders = result.get("open", {}) if isinstance(result, dict) else {}
        return (
            "venue_query",
            [
                self._open_order_from_payload(order_id=order_id, payload=item, context=context)
                for order_id, item in open_orders.items()
                if isinstance(item, dict)
            ],
        )

    async def _fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            return await super()._fetch_recent_fills_with_source(
                limit=limit,
                venue_account_ref_id=venue_account_ref_id,
            )
        payload = await self._signed_private_request(
            context,
            endpoint="/0/private/TradesHistory",
            body={"trades": True},
        )
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        trades = result.get("trades", {}) if isinstance(result, dict) else {}
        fills = [
            self._fill_from_trade_payload(trade_id=trade_id, payload=item, context=context)
            for trade_id, item in trades.items()
            if isinstance(item, dict)
        ]
        return ("venue_query", sorted(fills, key=lambda item: item.filled_at, reverse=True)[:limit])

    def _open_order_from_payload(
        self,
        *,
        order_id: str,
        payload: dict[str, Any],
        context,
    ) -> VenuePrivateOpenOrder:
        description = payload.get("descr", {}) if isinstance(payload.get("descr"), dict) else {}
        exchange_symbol = str(description.get("pair") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.replace("/USD", "")
        original_quantity = decimal_or(payload.get("vol"), "0")
        filled_quantity = decimal_or(payload.get("vol_exec"), "0")
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(payload.get("price"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        opened_at = payload.get("opentm")
        observed_at = (
            datetime.fromtimestamp(float(opened_at), tz=UTC)
            if opened_at not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        status = (
            SubmittedOrderStatus.PARTIALLY_FILLED
            if filled_quantity > Decimal("0")
            else SubmittedOrderStatus.ACKNOWLEDGED
        )
        order_type_raw = str(description.get("ordertype", "limit")).lower()
        normalized_order_type = "limit" if order_type_raw not in {"market", "stop"} else order_type_raw
        client_order_id = str(payload.get("cl_ord_id")) if payload.get("cl_ord_id") not in (None, "") else None
        linked_submitted_order_id, linked_order_intent_id = self._linked_submitted_order_identity(
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=order_id,
            client_order_id=client_order_id,
        )
        return VenuePrivateOpenOrder(
            venue=Venue.KRAKEN.value,
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=order_id,
            client_order_id=client_order_id,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
            exchange_symbol=exchange_symbol or None,
            status=status,
            observed_at=observed_at,
            side=OrderSide.BUY if str(description.get("type", "")).lower() == "buy" else OrderSide.SELL,
            order_type=OrderType(normalized_order_type),
            limit_price=average_fill_price_value,
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price_value,
            last_fill_at=observed_at if filled_quantity > Decimal("0") else None,
            status_reason_code=(
                "reconciliation_partial_fill" if status == SubmittedOrderStatus.PARTIALLY_FILLED else "reconciliation_open_order"
            ),
            status_message="Kraken private open-order query returned a working order snapshot.",
            reason_codes=(
                ["reconciliation_partial_fill"]
                if status == SubmittedOrderStatus.PARTIALLY_FILLED
                else ["reconciliation_open_order"]
            ),
            cancelable_in_principle=True,
            amendable_in_principle=False,
            reduce_only=False,
            linked_submitted_order_id=linked_submitted_order_id,
            linked_order_intent_id=linked_order_intent_id,
            raw_payload=dict(payload),
        )

    def _fill_from_trade_payload(
        self,
        *,
        trade_id: str,
        payload: dict[str, Any],
        context,
    ) -> Fill:
        exchange_symbol = str(payload.get("pair") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.replace("/USD", "")
        trade_time = payload.get("time")
        filled_at = (
            datetime.fromtimestamp(float(trade_time), tz=UTC)
            if trade_time not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        ordertxid = payload.get("ordertxid")
        return Fill(
            fill_id=f"fill-kraken-{trade_id}",
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.KRAKEN.value,
            account_address=context.account_address or context.account_identifier,
            submitted_order_id=str(ordertxid) if ordertxid not in (None, "") else "",
            exchange_order_id=str(ordertxid) if ordertxid not in (None, "") else None,
            symbol=symbol,
            price=decimal_or(payload.get("price"), "0"),
            quantity=abs(decimal_or(payload.get("vol"), "0")),
            fee=abs(decimal_or(payload.get("fee"), "0")),
            filled_at=filled_at,
        )

    def _build_order_preview_payload(
        self,
        *,
        intent: OrderIntent,
        exchange_symbol: str,
        time_in_force: str | None,
        client_order_id: str | None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "endpoint": "/0/private/AddOrder",
            "pair": exchange_symbol,
            "type": intent.side.value,
            "ordertype": intent.order_type.value,
            "volume": str(intent.quantity),
        }
        if intent.limit_price is not None:
            payload["price"] = str(intent.limit_price)
        if time_in_force is not None:
            payload["timeinforce"] = time_in_force
        if client_order_id is not None:
            payload["userref"] = client_order_id
        return payload

    async def _signed_private_request(
        self,
        context,
        *,
        endpoint: str,
        body: dict[str, object],
    ) -> Any:
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        nonce = str(int(datetime.now(UTC).timestamp() * 1000))
        signed_body = {"nonce": nonce, **body}
        post_data = self._render_form_body(sorted(signed_body.items()))
        sha256_payload = hashlib.sha256((nonce + post_data).encode("utf-8")).digest()
        signature_payload = endpoint.encode("utf-8") + sha256_payload
        headers = {
            "API-Key": api_key or "",
            "API-Sign": self._hmac_sha512_base64(api_secret or "", signature_payload),
        }
        return await self._request_form_exact("POST", endpoint, rendered_body=post_data, headers=headers)

    def _missing_order_update(
        self,
        submitted_order: SubmittedOrder,
        payload: dict[str, object],
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.KRAKEN.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message="Kraken reconciliation did not find the order.",
            reason_codes=["reconciliation_missing_order"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=dict(payload),
            observed_at=datetime.now(UTC),
        )

    def _reconciliation_update_from_order_payload(
        self,
        submitted_order: SubmittedOrder,
        order: dict[str, object],
    ) -> SubmittedOrderLifecycleUpdate:
        status = str(order.get("status", "")).lower()
        original_quantity = decimal_or(order.get("vol"), str(submitted_order.original_quantity or "0"))
        filled_quantity = decimal_or(order.get("vol_exec"), str(submitted_order.filled_quantity or "0"))
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(order.get("price"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        observed_at = datetime.now(UTC)
        if original_quantity > Decimal("0") and filled_quantity >= original_quantity:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.KRAKEN.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.FILLED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_completed_fill",
                remaining_quantity=Decimal("0"),
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price_value,
                last_fill_at=observed_at,
                status_reason_code="reconciliation_completed_fill",
                status_message="Kraken reconciled the submitted order to fully filled.",
                reason_codes=["reconciliation_completed_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status in {"pending", "open"}:
            if filled_quantity > Decimal("0"):
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.KRAKEN.value,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    exchange_order_id=submitted_order.exchange_order_id,
                    status=SubmittedOrderStatus.PARTIALLY_FILLED,
                    reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                    event_type="reconciliation_partial_fill",
                    remaining_quantity=remaining_quantity,
                    filled_quantity=filled_quantity,
                    average_fill_price=average_fill_price_value,
                    last_fill_at=observed_at,
                    status_reason_code="reconciliation_partial_fill",
                    status_message="Kraken reconciled the submitted order to partially filled.",
                    reason_codes=["reconciliation_partial_fill"],
                    cancelable_in_principle=True,
                    amendable_in_principle=False,
                    raw_payload=order,
                    observed_at=observed_at,
                )
            if submitted_order.status in {
                SubmittedOrderStatus.CANCEL_REQUESTED,
                SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            }:
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.KRAKEN.value,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    exchange_order_id=submitted_order.exchange_order_id,
                    status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
                    reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                    event_type="reconciliation_cancel_pending",
                    remaining_quantity=remaining_quantity,
                    filled_quantity=filled_quantity,
                    average_fill_price=average_fill_price_value,
                    last_fill_at=observed_at if filled_quantity > Decimal("0") else submitted_order.last_fill_at,
                    acknowledged_at=submitted_order.acknowledged_at,
                    status_reason_code="reconciliation_cancel_pending",
                    status_message="Kraken still reports the submitted order as open after accepting the cancel request.",
                    reason_codes=["reconciliation_cancel_pending"],
                    cancelable_in_principle=False,
                    amendable_in_principle=False,
                    raw_payload=order,
                    observed_at=observed_at,
                )
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.KRAKEN.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_open_order",
                remaining_quantity=remaining_quantity,
                acknowledged_at=submitted_order.acknowledged_at,
                status_reason_code="reconciliation_open_order",
                status_message="Kraken still reports the submitted order as open.",
                reason_codes=["reconciliation_open_order"],
                cancelable_in_principle=True,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status == "canceled":
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.KRAKEN.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.CANCELED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_canceled",
                remaining_quantity=remaining_quantity,
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price_value,
                last_fill_at=observed_at if filled_quantity > Decimal("0") else submitted_order.last_fill_at,
                status_reason_code="reconciliation_canceled",
                status_message=(
                    "Kraken reports the submitted order as canceled after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Kraken reports the submitted order as canceled."
                ),
                reason_codes=["reconciliation_canceled"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status == "expired":
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.KRAKEN.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.EXPIRED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_expired",
                remaining_quantity=remaining_quantity,
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price_value,
                last_fill_at=observed_at if filled_quantity > Decimal("0") else submitted_order.last_fill_at,
                status_reason_code="reconciliation_expired",
                status_message=(
                    "Kraken reports the submitted order as expired after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Kraken reports the submitted order as expired."
                ),
                reason_codes=["reconciliation_expired"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.KRAKEN.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_unknown_status",
            status_reason_code="reconciliation_unknown_status",
            status_message=f"Kraken returned an unrecognized order status: {status or 'missing'}",
            reason_codes=["reconciliation_unknown_status"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=order,
            observed_at=observed_at,
        )
