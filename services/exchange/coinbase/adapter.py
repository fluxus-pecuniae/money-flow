"""Coinbase Advanced Trade venue adapter."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from urllib.parse import urlparse

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
from services.exchange.coinbase.jwt_auth import build_coinbase_rest_jwt
from services.exchange.base import ReadOnlyVenueAdapter, VenueAdapterError, decimal_or
from services.exchange.common import build_instrument_key


def _coinbase_granularity(timeframe: str | Timeframe) -> str:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {"1m": "ONE_MINUTE", "5m": "FIVE_MINUTE", "15m": "FIFTEEN_MINUTE", "1h": "ONE_HOUR", "4h": "FOUR_HOUR", "1d": "ONE_DAY"}
    if tf not in mapping:
        raise VenueAdapterError(f"Unsupported Coinbase Advanced timeframe: {tf}")
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


class CoinbaseAdvancedTradeExchangeAdapter(ReadOnlyVenueAdapter):
    account_model = "brokerage_account"
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
    supported_time_in_force = ("gtc", "ioc", "fok")
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
            resolved_settings.coinbase_advanced_trade_integration,
            resolved_settings,
            transport=transport,
            session_factory=session_factory,
        )

    async def _ping(self) -> None:
        await self._request("GET", "/api/v3/brokerage/time", None)

    async def _fetch_symbol_metadata(self) -> Sequence[SymbolMetadata]:
        payload = await self._request("GET", "/api/v3/brokerage/products", None)
        metadata: list[SymbolMetadata] = []
        for item in payload.get("products", []):
            if item.get("product_type", "SPOT") != "SPOT":
                continue
            base_asset = str(item.get("base_currency_id")).upper()
            quote_asset = str(item.get("quote_currency_id")).upper()
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
                    venue=Venue.COINBASE_ADVANCED_TRADE.value,
                    symbol=base_asset,
                    exchange_symbol=str(item["product_id"]).upper(),
                    venue_asset_id=str(item.get("product_id")),
                    market_type=MarketType.SPOT,
                    product_type=ProductType.SPOT,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    settlement_asset=None,
                    price_tick_size=decimal_or(item.get("quote_increment"), "0.01"),
                    quantity_step_size=decimal_or(item.get("base_increment"), "0.00000001"),
                    min_order_size=decimal_or(item.get("base_min_size"), "0.00000001"),
                    is_active=not bool(item.get("trading_disabled", False)),
                    asset_id=None,
                    is_perpetual=False,
                    is_builder_deployed=False,
                    is_strategy_eligible=True,
                    is_trading_eligible=False,
                    raw_metadata={"product_type": item.get("product_type", "SPOT"), "venue": "coinbase_advanced_trade"},
                )
            )
        return metadata

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue.COINBASE_ADVANCED_TRADE,
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
            supports_depth_summary=False,
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
                "Coinbase Advanced Trade currently covers spot catalog sync, preview/preflight, "
                "an account-targeted JWT-authenticated submit path, truthful cancel acknowledgement, "
                "native edit-order support for the current spot scope, and direct private open-order "
                "plus recent-fill polling."
            ),
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def submit_order(self, intent: OrderIntent):
        if intent is None:
            raise VenueAdapterError(
                "Coinbase Advanced Trade submission requires a concrete child intent.",
                reason_codes=["missing_order_intent"],
            )
        preview = await self.prepare_order_preview(intent)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE or preview.payload is None:
            raise VenueAdapterError(
                "Coinbase Advanced Trade order is not venue-preparable.",
                reason_codes=list(preview.reason_codes or ["preview_rejected"]),
                payload={"prepared_order_preview": preview.payload or {}},
            )
        context = self._resolve_execution_context(intent.venue_account_ref_id)
        self._assert_submission_controls(context)
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            raise VenueAdapterError(
                "Coinbase Advanced Trade submission requires a targeted JWT key name and EC private key.",
                reason_codes=list(self._resolve_credentials(context).reason_codes or ["missing_auth_material"]),
            )
        endpoint, body = self._submission_request_from_preview(preview)
        request_host = urlparse(self.integration.api_base_url).netloc or "api.coinbase.com"
        try:
            bearer = build_coinbase_rest_jwt(
                key_name=jwt_key_name,
                private_key_pem=jwt_private_key,
                request_method="POST",
                request_host=request_host,
                request_path=endpoint,
            )
        except Exception as exc:  # noqa: BLE001
            raise VenueAdapterError(
                "Coinbase Advanced Trade could not construct a submission JWT for the targeted account.",
                reason_codes=["auth_signing_failed"],
            ) from exc
        headers = {
            "Authorization": f"Bearer {bearer}",
        }
        rendered_body = self._render_json_body(body, sort_keys=True)
        response = await self._request_json_exact(
            "POST",
            endpoint,
            body=body,
            headers=headers,
            rendered_body=rendered_body,
        )
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
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            raise VenueAdapterError(
                "Coinbase Advanced Trade reconciliation requires targeted JWT auth material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.exchange_order_id is None:
            return self._missing_order_update(submitted_order, {})
        endpoint = f"/api/v3/brokerage/orders/historical/{submitted_order.exchange_order_id}"
        headers = self._jwt_headers_for_context(context, request_method="GET", request_path=endpoint)
        payload = await self._request("GET", endpoint, None, headers=headers)
        order = payload.get("order")
        if not isinstance(order, dict):
            return self._missing_order_update(submitted_order, payload)
        return self._reconciliation_update_from_order_payload(submitted_order, order)

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        self._assert_submission_controls(context)
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            raise VenueAdapterError(
                "Coinbase Advanced Trade cancellation requires targeted JWT auth material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.exchange_order_id is None:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_missing_order_identity"],
                message="Coinbase Advanced Trade cancellation requires an exchange order id.",
            )
        endpoint = "/api/v3/brokerage/orders/batch_cancel"
        body = {"order_ids": [submitted_order.exchange_order_id]}
        headers = self._jwt_headers_for_context(context, request_method="POST", request_path=endpoint)
        rendered_body = self._render_json_body(body, sort_keys=True)
        response = await self._request_json_exact(
            "POST",
            endpoint,
            body=body,
            headers=headers,
            rendered_body=rendered_body,
        )
        results = response.get("results", [])
        first = results[0] if results else {}
        if first.get("success") is True or str(first.get("success")).lower() == "true":
            return self._cancel_success_update(
                submitted_order=submitted_order,
                status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
                event_type="cancel_acknowledged",
                status_reason_code="cancel_acknowledged",
                remaining_quantity=submitted_order.remaining_quantity,
                message="Coinbase Advanced Trade accepted the cancel request; reconciliation must still confirm final canceled state.",
                reason_codes=["cancel_acknowledged"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=response,
            )
        failure_reason = first.get("failure_reason") or response.get("error_response") or response.get("message")
        return self._cancel_rejected_update(
            submitted_order=submitted_order,
            reason_codes=["cancel_rejected"],
            message=str(failure_reason or "Coinbase Advanced Trade rejected cancellation."),
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
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            raise VenueAdapterError(
                "Coinbase Advanced Trade amendment requires targeted JWT auth material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.order_type != OrderType.LIMIT:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_not_supported_for_order_type"],
                message="Coinbase Advanced Trade amendment is currently limited to limit orders in the implemented scope.",
            )
        if submitted_order.exchange_order_id is None:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_missing_order_identity"],
                message="Coinbase Advanced Trade amendment requires an exchange order id.",
            )
        if new_quantity is None and new_limit_price is None:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_no_changes_requested"],
                message="Coinbase Advanced Trade amendment requires at least one explicit quantity or limit-price change.",
            )
        filled_quantity = submitted_order.filled_quantity or Decimal("0")
        if new_quantity is not None and new_quantity <= filled_quantity:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_quantity_below_filled"],
                message="Coinbase Advanced Trade amendment cannot reduce the order quantity below already filled size.",
            )
        endpoint = "/api/v3/brokerage/orders/edit"
        body: dict[str, object] = {
            "order_id": submitted_order.exchange_order_id,
            "size": str(new_quantity) if new_quantity is not None else str(submitted_order.original_quantity),
            "price": (
                str(new_limit_price)
                if new_limit_price is not None
                else (str(submitted_order.limit_price) if submitted_order.limit_price is not None else None)
            ),
        }
        headers = self._jwt_headers_for_context(
            context,
            request_method="POST",
            request_path=endpoint,
        )
        rendered_body = self._render_json_body(body, sort_keys=True)
        response = await self._request_json_exact(
            "POST",
            endpoint,
            body=body,
            headers=headers,
            rendered_body=rendered_body,
        )
        if response.get("success") is False or response.get("error_response") or response.get("errors"):
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_rejected"],
                message=str(
                    response.get("error_response")
                    or response.get("message")
                    or response.get("errors")
                    or "Coinbase Advanced Trade rejected amendment."
                ),
                raw_payload=response,
            )
        return self._amend_acknowledged_update(
            submitted_order=submitted_order,
            new_quantity=new_quantity,
            new_limit_price=new_limit_price,
            message="Coinbase Advanced Trade accepted the amend request; reconciliation must still confirm the refreshed working state.",
            raw_payload=response,
        )

    async def _fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            return await super()._fetch_open_orders_with_source(venue_account_ref_id=venue_account_ref_id)
        endpoint = "/api/v3/brokerage/orders/historical/batch"
        headers = self._jwt_headers_for_context(context, request_method="GET", request_path=endpoint)
        payload = await self._request(
            "GET",
            endpoint,
            {"order_status": "OPEN"},
            headers=headers,
        )
        orders = payload.get("orders", []) if isinstance(payload, dict) else []
        return (
            "venue_query",
            [
                self._open_order_from_payload(payload=item, context=context)
                for item in orders
                if isinstance(item, dict)
            ],
        )

    async def _fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            return await super()._fetch_recent_fills_with_source(
                limit=limit,
                venue_account_ref_id=venue_account_ref_id,
            )
        endpoint = "/api/v3/brokerage/orders/historical/fills"
        headers = self._jwt_headers_for_context(context, request_method="GET", request_path=endpoint)
        payload = await self._request("GET", endpoint, {"limit": limit}, headers=headers)
        fills = payload.get("fills", []) if isinstance(payload, dict) else []
        return (
            "venue_query",
            [
                self._fill_from_payload(payload=item, context=context)
                for item in fills[:limit]
                if isinstance(item, dict)
            ],
        )

    def _open_order_from_payload(
        self,
        *,
        payload: dict[str, Any],
        context,
    ) -> VenuePrivateOpenOrder:
        exchange_symbol = str(payload.get("product_id") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.split("-")[0]
        original_quantity = self._coinbase_original_quantity(payload, None)
        filled_quantity = decimal_or(payload.get("filled_size"), "0")
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(payload.get("average_filled_price"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        observed_at = datetime.now(UTC)
        status = (
            SubmittedOrderStatus.PARTIALLY_FILLED
            if filled_quantity > Decimal("0")
            else SubmittedOrderStatus.ACKNOWLEDGED
        )
        limit_price = self._coinbase_limit_price(payload)
        order_type = OrderType.LIMIT if limit_price is not None else OrderType.MARKET
        client_order_id = (
            str(payload.get("client_order_id"))
            if payload.get("client_order_id") not in (None, "")
            else None
        )
        exchange_order_id = str(payload.get("order_id")) if payload.get("order_id") not in (None, "") else None
        linked_submitted_order_id, linked_order_intent_id = self._linked_submitted_order_identity(
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
        )
        return VenuePrivateOpenOrder(
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
            exchange_symbol=exchange_symbol or None,
            status=status,
            observed_at=observed_at,
            side=OrderSide.BUY if str(payload.get("side", "")).upper() == "BUY" else OrderSide.SELL,
            order_type=order_type,
            limit_price=limit_price,
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price_value,
            last_fill_at=observed_at if filled_quantity > Decimal("0") else None,
            status_reason_code=(
                "reconciliation_partial_fill" if status == SubmittedOrderStatus.PARTIALLY_FILLED else "reconciliation_open_order"
            ),
            status_message="Coinbase Advanced Trade private open-order query returned a working order snapshot.",
            reason_codes=(
                ["reconciliation_partial_fill"]
                if status == SubmittedOrderStatus.PARTIALLY_FILLED
                else ["reconciliation_open_order"]
            ),
            cancelable_in_principle=True,
            amendable_in_principle=order_type == OrderType.LIMIT,
            reduce_only=False,
            linked_submitted_order_id=linked_submitted_order_id,
            linked_order_intent_id=linked_order_intent_id,
            raw_payload=dict(payload),
        )

    def _fill_from_payload(
        self,
        *,
        payload: dict[str, Any],
        context,
    ) -> Fill:
        exchange_symbol = str(payload.get("product_id") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.split("-")[0]
        filled_at_raw = payload.get("trade_time") or payload.get("created_time")
        if filled_at_raw:
            filled_at = datetime.fromisoformat(str(filled_at_raw).replace("Z", "+00:00"))
        else:
            filled_at = datetime.now(UTC)
        return Fill(
            fill_id=f"fill-coinbase-{payload.get('trade_id') or payload.get('entry_id') or payload.get('order_id')}",
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            account_address=context.account_address or context.account_identifier,
            submitted_order_id=str(payload.get("order_id")) if payload.get("order_id") not in (None, "") else "",
            exchange_order_id=str(payload.get("order_id")) if payload.get("order_id") not in (None, "") else None,
            symbol=symbol,
            price=decimal_or(payload.get("price"), "0"),
            quantity=abs(decimal_or(payload.get("size"), "0")),
            fee=abs(decimal_or(payload.get("commission"), "0")),
            filled_at=filled_at,
        )

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]:
        product_id = f"{symbol.upper()}-USD"
        payload = await self._request(
            "GET",
            f"/api/v3/brokerage/products/{product_id}/candles",
            {
                "start": int(start_time_ms / 1000),
                "end": int(end_time_ms / 1000),
                "granularity": _coinbase_granularity(timeframe),
            },
        )
        candles: list[Candle] = []
        delta = _timeframe_delta(timeframe)
        for row in payload.get("candles", []):
            open_time = datetime.fromtimestamp(int(row["start"]) , tz=UTC)
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
                    venue=Venue.COINBASE_ADVANCED_TRADE.value,
                    symbol=symbol.upper(),
                    timeframe=Timeframe(timeframe),
                    open_time=open_time,
                    close_time=open_time + delta,
                    open=decimal_or(row["open"]),
                    high=decimal_or(row["high"]),
                    low=decimal_or(row["low"]),
                    close=decimal_or(row["close"]),
                    volume=decimal_or(row["volume"]),
                    trade_count=None,
                )
            )
        return candles

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        payload = await self._request(
            "GET",
            "/api/v3/brokerage/best_bid_ask",
            {"product_ids": f"{symbol.upper()}-USD"},
        )
        pricebooks = payload.get("pricebooks", [])
        if not pricebooks:
            return None
        row = pricebooks[0]
        bids = row.get("bids", [])
        asks = row.get("asks", [])
        bid = bids[0] if bids else {}
        ask = asks[0] if asks else {}
        return TopOfBookSnapshot(
            instrument_key=build_instrument_key(
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset=symbol.upper(),
                quote_asset="USD",
                settlement_asset=None,
            ),
            instrument_ref_id=None,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            symbol=symbol.upper(),
            bid_price=decimal_or(bid.get("price"), "0"),
            bid_size=decimal_or(bid.get("size"), "0"),
            ask_price=decimal_or(ask.get("price"), "0"),
            ask_size=decimal_or(ask.get("size"), "0"),
            observed_at=datetime.now(UTC),
        )

    async def read_account_snapshot(self) -> ExchangeAccountSnapshot | None:
        default_context = self._resolve_execution_context(None)
        return await self._read_account_snapshot_for_context(default_context)

    async def _read_account_snapshot_for_context(self, context) -> ExchangeAccountSnapshot | None:
        jwt_key_name = self._jwt_key_name_for_context(context)
        jwt_private_key = self._jwt_private_key_pem_for_context(context)
        if not jwt_key_name or not jwt_private_key:
            return None
        request_host = urlparse(self.integration.api_base_url).netloc or "api.coinbase.com"
        try:
            bearer = build_coinbase_rest_jwt(
                key_name=jwt_key_name,
                private_key_pem=jwt_private_key,
                request_method="GET",
                request_host=request_host,
                request_path="/api/v3/brokerage/accounts",
            )
        except Exception:  # noqa: BLE001
            return None
        headers = {"Authorization": f"Bearer {bearer}"}
        payload = await self._request("GET", "/api/v3/brokerage/accounts", None, headers=headers)
        accounts = payload.get("accounts", [])
        if not accounts:
            return None
        cash = accounts[0]
        balance = cash.get("available_balance", {})
        return ExchangeAccountSnapshot(
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            environment=self._integration_environment,
            account_address=context.account_address or context.account_identifier,
            equity=decimal_or(balance.get("value"), "0"),
            available_balance=decimal_or(balance.get("value"), "0"),
            margin_used=decimal_or("0"),
            unrealized_pnl=decimal_or("0"),
            total_position_notional=decimal_or("0"),
            observed_at=datetime.now(UTC),
        )

    def _default_time_in_force(self, order_type: OrderType) -> str | None:
        if order_type == OrderType.MARKET:
            return "ioc"
        return "gtc"

    def _build_order_preview_payload(
        self,
        *,
        intent: OrderIntent,
        exchange_symbol: str,
        time_in_force: str | None,
        client_order_id: str | None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "endpoint": "/api/v3/brokerage/orders",
            "product_id": exchange_symbol,
            "side": intent.side.value.upper(),
            "order_configuration": {},
        }
        if client_order_id is not None:
            payload["client_order_id"] = client_order_id
        if intent.order_type == OrderType.MARKET:
            payload["order_configuration"] = {
                "market_market_ioc": {
                    "base_size": str(intent.quantity),
                }
            }
        else:
            payload["order_configuration"] = {
                "limit_limit_gtc": {
                    "base_size": str(intent.quantity),
                    "limit_price": str(intent.limit_price) if intent.limit_price is not None else None,
                    "post_only": False,
                }
            }
            if time_in_force is not None:
                payload["time_in_force"] = time_in_force
        return payload

    def _jwt_headers_for_context(
        self,
        context,
        *,
        request_method: str,
        request_path: str,
    ) -> dict[str, str]:
        request_host = urlparse(self.integration.api_base_url).netloc or "api.coinbase.com"
        bearer = build_coinbase_rest_jwt(
            key_name=self._jwt_key_name_for_context(context) or "",
            private_key_pem=self._jwt_private_key_pem_for_context(context) or "",
            request_method=request_method,
            request_host=request_host,
            request_path=request_path,
        )
        return {"Authorization": f"Bearer {bearer}"}

    def _missing_order_update(
        self,
        submitted_order: SubmittedOrder,
        payload: dict[str, object],
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message="Coinbase Advanced Trade reconciliation did not find the order.",
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
        status = str(order.get("status", "")).upper()
        filled_quantity = decimal_or(order.get("filled_size"), str(submitted_order.filled_quantity or "0"))
        original_quantity = self._coinbase_original_quantity(order, submitted_order)
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(order.get("average_filled_price"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        observed_at = datetime.now(UTC)
        if original_quantity > Decimal("0") and filled_quantity >= original_quantity:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
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
                status_message="Coinbase Advanced Trade reconciled the submitted order to fully filled.",
                reason_codes=["reconciliation_completed_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status in {"OPEN", "PENDING"}:
            if filled_quantity > Decimal("0"):
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.COINBASE_ADVANCED_TRADE.value,
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
                    status_message="Coinbase Advanced Trade reconciled the submitted order to partially filled.",
                    reason_codes=["reconciliation_partial_fill"],
                    cancelable_in_principle=True,
                    amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                    raw_payload=order,
                    observed_at=observed_at,
                )
            if submitted_order.status in {
                SubmittedOrderStatus.CANCEL_REQUESTED,
                SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            }:
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.COINBASE_ADVANCED_TRADE.value,
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
                    status_message="Coinbase Advanced Trade still reports the submitted order as open after accepting the cancel request.",
                    reason_codes=["reconciliation_cancel_pending"],
                    cancelable_in_principle=False,
                    amendable_in_principle=False,
                    raw_payload=order,
                    observed_at=observed_at,
                )
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_open_order",
                remaining_quantity=remaining_quantity,
                acknowledged_at=submitted_order.acknowledged_at,
                status_reason_code="reconciliation_open_order",
                status_message="Coinbase Advanced Trade still reports the submitted order as open.",
                reason_codes=["reconciliation_open_order"],
                cancelable_in_principle=True,
                amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status in {"CANCELLED", "CANCELED"}:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
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
                    "Coinbase Advanced Trade reports the submitted order as canceled after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Coinbase Advanced Trade reports the submitted order as canceled."
                ),
                reason_codes=["reconciliation_canceled"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status == "EXPIRED":
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
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
                    "Coinbase Advanced Trade reports the submitted order as expired after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Coinbase Advanced Trade reports the submitted order as expired."
                ),
                reason_codes=["reconciliation_expired"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        if status in {"FAILED", "REJECTED"}:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.COINBASE_ADVANCED_TRADE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.REJECTED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_rejected",
                status_reason_code="venue_rejected",
                status_message="Coinbase Advanced Trade reports the submitted order as rejected.",
                reason_codes=["venue_rejected"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=order,
                observed_at=observed_at,
            )
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.COINBASE_ADVANCED_TRADE.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_unknown_status",
            status_reason_code="reconciliation_unknown_status",
            status_message=f"Coinbase Advanced Trade returned an unrecognized order status: {status or 'missing'}",
            reason_codes=["reconciliation_unknown_status"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=order,
            observed_at=observed_at,
        )

    @staticmethod
    def _coinbase_original_quantity(
        order: dict[str, object],
        submitted_order: SubmittedOrder | None,
    ) -> Decimal:
        if submitted_order is not None and submitted_order.original_quantity is not None:
            return submitted_order.original_quantity
        order_configuration = order.get("order_configuration")
        if not isinstance(order_configuration, dict):
            return Decimal("0")
        for value in order_configuration.values():
            if isinstance(value, dict) and value.get("base_size") not in (None, ""):
                return decimal_or(value.get("base_size"), "0")
        return Decimal("0")

    @staticmethod
    def _coinbase_limit_price(order: dict[str, object]) -> Decimal | None:
        order_configuration = order.get("order_configuration")
        if not isinstance(order_configuration, dict):
            return None
        for value in order_configuration.values():
            if isinstance(value, dict) and value.get("limit_price") not in (None, "", "0", 0):
                price = decimal_or(value.get("limit_price"), "0")
                return price if price > Decimal("0") else None
        return None
