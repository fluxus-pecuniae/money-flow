"""Binance venue adapter."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
    SubmittedOrderPrivateFillEvidence,
    SymbolMetadata,
    TopOfBookSnapshot,
    VenueCapabilities,
    VenuePrivateOpenOrder,
)
from db.session import SessionLocal
from services.exchange.base import ReadOnlyVenueAdapter, VenueAdapterError, decimal_or
from services.exchange.common import build_instrument_key


def _timeframe_to_binance(timeframe: str | Timeframe) -> str:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
    if tf not in mapping:
        raise VenueAdapterError(f"Unsupported Binance timeframe: {tf}")
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


def _submitted_order_start_time_ms(submitted_order: SubmittedOrder) -> int:
    submitted_at = submitted_order.submitted_at
    if submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=UTC)
    else:
        submitted_at = submitted_at.astimezone(UTC)
    return int(submitted_at.timestamp() * 1000)


class BinanceExchangeAdapter(ReadOnlyVenueAdapter):
    account_model = "api_account"
    support_level = VenueSupportLevel.EXECUTION_PREPARABLE
    adapter_supports_order_submission = True
    adapter_supports_order_cancel = True
    retry_requires_fresh_client_order_id = True
    supports_order_preview = True
    supports_account_snapshot = True
    supports_open_orders_query = True
    supports_open_positions_query = False
    supports_recent_fills_query = False
    supports_reduce_only_orders = False
    supports_client_order_ids = True
    supported_order_types = (OrderType.MARKET, OrderType.LIMIT)
    supported_time_in_force = ("gtc", "ioc", "fok")
    open_orders_state_source = "venue_query"

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        transport=None,
        session_factory=SessionLocal,
    ) -> None:
        resolved_settings = settings or get_settings()
        super().__init__(
            resolved_settings.binance_integration,
            resolved_settings,
            transport=transport,
            session_factory=session_factory,
        )

    async def _ping(self) -> None:
        await self._request("GET", "/api/v3/ping", None)

    async def _fetch_symbol_metadata(self) -> Sequence[SymbolMetadata]:
        payload = await self._request("GET", "/api/v3/exchangeInfo", None)
        metadata: list[SymbolMetadata] = []
        for item in payload.get("symbols", []):
            if item.get("status") != "TRADING":
                continue
            base_asset = str(item.get("baseAsset", "")).upper()
            quote_asset = str(item.get("quoteAsset", "")).upper()
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
                    venue=Venue.BINANCE.value,
                    symbol=base_asset,
                    exchange_symbol=str(item["symbol"]).upper(),
                    venue_asset_id=str(item["symbol"]).upper(),
                    market_type=MarketType.SPOT,
                    product_type=ProductType.SPOT,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    settlement_asset=None,
                    price_tick_size=decimal_or(_filter_value(item, "PRICE_FILTER", "tickSize"), "0.01"),
                    quantity_step_size=decimal_or(_filter_value(item, "LOT_SIZE", "stepSize"), "0.000001"),
                    min_order_size=decimal_or(_filter_value(item, "LOT_SIZE", "minQty"), "0.000001"),
                    is_active=True,
                    asset_id=None,
                    is_perpetual=False,
                    is_builder_deployed=False,
                    is_strategy_eligible=True,
                    is_trading_eligible=False,
                    raw_metadata={"venue": "binance", "symbol_status": item.get("status")},
                )
            )
        return metadata

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue.BINANCE,
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
            supports_order_amend=False,
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
            supports_demo_mode=True,
            supports_subaccounts=False,
            supported_order_types=list(self.supported_order_types),
            supported_time_in_force=list(self.supported_time_in_force),
            account_model=self.account_model,
            notes=(
                "Binance currently covers spot catalog sync, top-of-book, preview/preflight, "
                "an account-targeted signed submit path, direct private open-order polling, "
                "and persistence-backed fill visibility."
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
        exchange_symbol = f"{symbol.upper()}USDT"
        payload = await self._request(
            "GET",
            "/api/v3/klines",
            {
                "symbol": exchange_symbol,
                "interval": _timeframe_to_binance(timeframe),
                "startTime": start_time_ms,
                "endTime": end_time_ms,
            },
        )
        candles: list[Candle] = []
        delta = _timeframe_delta(timeframe)
        for row in payload:
            open_time = datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC)
            candles.append(
                Candle(
                    instrument_key=build_instrument_key(
                        market_type=MarketType.SPOT,
                        product_type=ProductType.SPOT,
                        base_asset=symbol.upper(),
                        quote_asset="USDT",
                        settlement_asset=None,
                    ),
                    instrument_ref_id=None,
                    venue=Venue.BINANCE.value,
                    symbol=symbol.upper(),
                    timeframe=Timeframe(_timeframe_to_binance(timeframe)),
                    open_time=open_time,
                    close_time=open_time + delta,
                    open=decimal_or(row[1]),
                    high=decimal_or(row[2]),
                    low=decimal_or(row[3]),
                    close=decimal_or(row[4]),
                    volume=decimal_or(row[5]),
                    trade_count=None,
                )
            )
        return candles

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        payload = await self._request(
            "GET",
            "/api/v3/ticker/bookTicker",
            {"symbol": f"{symbol.upper()}USDT"},
        )
        return TopOfBookSnapshot(
            instrument_key=build_instrument_key(
                market_type=MarketType.SPOT,
                product_type=ProductType.SPOT,
                base_asset=symbol.upper(),
                quote_asset="USDT",
                settlement_asset=None,
            ),
            instrument_ref_id=None,
            venue=Venue.BINANCE.value,
            symbol=symbol.upper(),
            bid_price=decimal_or(payload.get("bidPrice")),
            bid_size=decimal_or(payload.get("bidQty")),
            ask_price=decimal_or(payload.get("askPrice")),
            ask_size=decimal_or(payload.get("askQty")),
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
        params = {
            "timestamp": int(datetime.now(UTC).timestamp() * 1000),
            "recvWindow": 5000,
        }
        signing_payload = urllib.parse.urlencode(sorted(params.items()))
        params["signature"] = self._hmac_sha256_hex(api_secret, signing_payload)
        payload = await self._request(
            "GET",
            "/api/v3/account",
            params,
            headers={"X-MBX-APIKEY": api_key},
        )
        balances = payload.get("balances", [])
        preferred = next(
            (row for row in balances if str(row.get("asset", "")).upper() in {"USDT", "USD", "USDC"}),
            balances[0] if balances else None,
        )
        if preferred is None:
            return None
        free = decimal_or(preferred.get("free"), "0")
        locked = decimal_or(preferred.get("locked"), "0")
        return ExchangeAccountSnapshot(
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.BINANCE.value,
            environment=self._integration_environment,
            account_address=context.account_address or context.account_identifier,
            equity=free + locked,
            available_balance=free,
            margin_used=locked,
            unrealized_pnl=decimal_or("0"),
            total_position_notional=decimal_or("0"),
            observed_at=datetime.now(UTC),
        )

    async def submit_order(self, intent: OrderIntent):
        if intent is None:
            raise VenueAdapterError(
                "Binance submission requires a concrete child intent.",
                reason_codes=["missing_order_intent"],
            )
        preview = await self.prepare_order_preview(intent)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE or preview.payload is None:
            raise VenueAdapterError(
                "Binance order is not venue-preparable.",
                reason_codes=list(preview.reason_codes or ["preview_rejected"]),
                payload={"prepared_order_preview": preview.payload or {}},
            )
        context = self._resolve_execution_context(intent.venue_account_ref_id)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Binance submission requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        endpoint, body = self._submission_request_from_preview(preview)
        signed_body = dict(body)
        signed_body["timestamp"] = int(datetime.now(UTC).timestamp() * 1000)
        signed_body["recvWindow"] = 5000
        signing_payload = self._render_form_body(sorted(signed_body.items()))
        rendered_body = f"{signing_payload}&signature={self._hmac_sha256_hex(api_secret, signing_payload)}"
        headers = {
            "X-MBX-APIKEY": api_key,
        }
        response = await self._request_form_exact("POST", endpoint, rendered_body=rendered_body, headers=headers)
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
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Binance reconciliation requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        if exchange_symbol is None or submitted_order.exchange_order_id is None:
            return self._missing_order_update(submitted_order, {})
        params = self._signed_private_params(
            api_secret,
            symbol=exchange_symbol,
            orderId=submitted_order.exchange_order_id,
        )
        payload = await self._request(
            "GET",
            "/api/v3/order",
            params,
            headers={"X-MBX-APIKEY": api_key},
        )
        if payload.get("code") not in (None, 0, "0"):
            return self._missing_order_update(submitted_order, payload)
        return self._reconciliation_update_from_order_payload(submitted_order, payload)

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret:
            raise VenueAdapterError(
                "Binance cancellation requires targeted API key and secret material.",
                reason_codes=["missing_auth_material"],
            )
        if exchange_symbol is None or submitted_order.exchange_order_id is None:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_missing_order_identity"],
                message="Binance cancellation requires the targeted exchange symbol and exchange order id.",
            )
        params = self._signed_private_params(
            api_secret,
            symbol=exchange_symbol,
            orderId=submitted_order.exchange_order_id,
        )
        response = await self._request(
            "DELETE",
            "/api/v3/order",
            params,
            headers={"X-MBX-APIKEY": api_key},
        )
        if response.get("code") not in (None, 0, "0"):
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_rejected"],
                message=str(response.get("msg") or "Binance rejected cancellation."),
                raw_payload=response,
            )
        return self._cancel_success_update(
            submitted_order=submitted_order,
            message="Binance acknowledged cancellation for the submitted order.",
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
        params = self._signed_private_params(api_secret)
        payload = await self._request(
            "GET",
            "/api/v3/openOrders",
            params,
            headers={"X-MBX-APIKEY": api_key},
        )
        if not isinstance(payload, list):
            return ("venue_query", [])
        return (
            "venue_query",
            [
                self._open_order_from_payload(payload=item, context=context)
                for item in payload
                if isinstance(item, dict)
            ],
        )

    async def fetch_retry_private_fill_evidence(
        self,
        submitted_order: SubmittedOrder,
        *,
        limit: int = 100,
    ) -> SubmittedOrderPrivateFillEvidence:
        context = self._context_for_submitted_order(submitted_order)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret or exchange_symbol is None:
            return SubmittedOrderPrivateFillEvidence(
                source="unavailable",
                evidence_scope="unavailable",
                fills=[],
                message="Binance private trade evidence was unavailable because auth or symbol context was missing.",
            )
        start_time_ms = _submitted_order_start_time_ms(submitted_order)
        params = self._signed_private_params(
            api_secret,
            symbol=exchange_symbol,
            startTime=start_time_ms,
            limit=min(limit, 1000),
        )
        try:
            payload = await self._request(
                "GET",
                "/api/v3/myTrades",
                params,
                headers={"X-MBX-APIKEY": api_key},
            )
        except VenueAdapterError as exc:
            return SubmittedOrderPrivateFillEvidence(
                source="unavailable",
                evidence_scope="query_failed",
                fills=[],
                message=str(exc),
            )
        if not isinstance(payload, list):
            return SubmittedOrderPrivateFillEvidence(
                source="venue_query",
                evidence_scope="unavailable",
                fills=[],
                message="Binance private trade query returned no list payload.",
            )
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else submitted_order.instrument_ref_id
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else submitted_order.symbol
        fills: list[Fill] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if (
                submitted_order.exchange_order_id is not None
                and str(item.get("orderId")) != str(submitted_order.exchange_order_id)
            ):
                continue
            observed_ms = item.get("time")
            filled_at = (
                datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
                if observed_ms not in (None, "", 0, "0")
                else datetime.now(UTC)
            )
            if observed_ms not in (None, "", 0, "0") and int(observed_ms) < start_time_ms:
                continue
            fills.append(
                Fill(
                    fill_id=f"fill-binance-{item.get('id') or item.get('orderId') or filled_at.timestamp()}",
                    instrument_key=instrument_key,
                    instrument_ref_id=instrument_ref_id,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    venue=Venue.BINANCE.value,
                    account_address=context.account_address or context.account_identifier,
                    submitted_order_id=submitted_order.submitted_order_id,
                    exchange_order_id=(
                        str(item.get("orderId")) if item.get("orderId") not in (None, "") else submitted_order.exchange_order_id
                    ),
                    symbol=symbol,
                    price=decimal_or(item.get("price"), "0"),
                    quantity=abs(decimal_or(item.get("qty"), "0")),
                    fee=abs(decimal_or(item.get("commission"), "0")),
                    filled_at=filled_at,
                )
            )
        scope = (
            "order_scoped"
            if submitted_order.exchange_order_id not in (None, "")
            else "same_account_same_symbol_ambiguous"
        )
        message = (
            (
                "Binance private trade evidence was matched by exchange order id."
                if fills
                else "Binance private trade query was filtered by exchange order id; no matching fills were returned."
            )
            if scope == "order_scoped"
            else (
                "Binance private trade evidence is submitted-at-bounded same-account/same-symbol only; "
                "the submitted order has no exchange order id, so targeted order fill proof is unavailable."
            )
        )
        return SubmittedOrderPrivateFillEvidence(
            source="venue_query",
            evidence_scope=scope,
            fills=fills[:limit],
            message=message,
        )

    def _open_order_from_payload(
        self,
        *,
        payload: dict[str, Any],
        context,
    ) -> VenuePrivateOpenOrder:
        exchange_symbol = str(payload.get("symbol") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.replace("USDT", "")
        original_quantity = decimal_or(payload.get("origQty"), "0")
        filled_quantity = decimal_or(payload.get("executedQty"), "0")
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        cummulative_quote = decimal_or(payload.get("cummulativeQuoteQty"), "0")
        average_fill_price = (
            cummulative_quote / filled_quantity
            if filled_quantity > Decimal("0") and cummulative_quote > Decimal("0")
            else None
        )
        observed_ms = payload.get("updateTime") or payload.get("time") or payload.get("transactTime")
        observed_at = (
            datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
            if observed_ms not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        status = (
            SubmittedOrderStatus.PARTIALLY_FILLED
            if filled_quantity > Decimal("0")
            else SubmittedOrderStatus.ACKNOWLEDGED
        )
        client_order_id = (
            str(payload.get("clientOrderId"))
            if payload.get("clientOrderId") not in (None, "")
            else None
        )
        exchange_order_id = str(payload.get("orderId")) if payload.get("orderId") not in (None, "") else None
        linked_submitted_order_id, linked_order_intent_id = self._linked_submitted_order_identity(
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
        )
        return VenuePrivateOpenOrder(
            venue=Venue.BINANCE.value,
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
            order_type=OrderType(str(payload.get("type", "limit")).lower()),
            limit_price=(
                decimal_or(payload.get("price"), "0")
                if payload.get("price") not in (None, "", "0", 0)
                else None
            ),
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price,
            last_fill_at=observed_at if filled_quantity > Decimal("0") else None,
            status_reason_code=(
                "reconciliation_partial_fill" if status == SubmittedOrderStatus.PARTIALLY_FILLED else "reconciliation_open_order"
            ),
            status_message="Binance private open-order query returned a working order snapshot.",
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

    def _build_order_preview_payload(
        self,
        *,
        intent: OrderIntent,
        exchange_symbol: str,
        time_in_force: str | None,
        client_order_id: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "endpoint": "/api/v3/order",
            "symbol": exchange_symbol,
            "side": intent.side.value.upper(),
            "type": intent.order_type.value.upper(),
            "quantity": str(intent.quantity),
        }
        if intent.limit_price is not None:
            payload["price"] = str(intent.limit_price)
        if time_in_force is not None and intent.order_type != OrderType.MARKET:
            payload["timeInForce"] = time_in_force.upper()
        if client_order_id is not None:
            payload["newClientOrderId"] = client_order_id
        return payload

    @staticmethod
    def _signed_private_params(api_secret: str, **params: object) -> dict[str, object]:
        signed = dict(params)
        signed["timestamp"] = int(datetime.now(UTC).timestamp() * 1000)
        signed["recvWindow"] = 5000
        signing_payload = urllib.parse.urlencode(sorted(signed.items()))
        signed["signature"] = ReadOnlyVenueAdapter._hmac_sha256_hex(api_secret, signing_payload)
        return signed

    def _missing_order_update(
        self,
        submitted_order: SubmittedOrder,
        payload: dict[str, Any],
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.BINANCE.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message=str(payload.get("msg") or "Binance reconciliation did not find the order."),
            reason_codes=["reconciliation_missing_order"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=payload,
            observed_at=datetime.now(UTC),
        )

    def _reconciliation_update_from_order_payload(
        self,
        submitted_order: SubmittedOrder,
        payload: dict[str, Any],
    ) -> SubmittedOrderLifecycleUpdate:
        remote_status = str(payload.get("status", "")).upper()
        original_quantity = decimal_or(payload.get("origQty"), str(submitted_order.original_quantity or "0"))
        filled_quantity = decimal_or(payload.get("executedQty"), str(submitted_order.filled_quantity or "0"))
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        cummulative_quote = decimal_or(payload.get("cummulativeQuoteQty"), "0")
        average_fill_price = (
            cummulative_quote / filled_quantity
            if filled_quantity > Decimal("0") and cummulative_quote > Decimal("0")
            else None
        )
        updated_at = payload.get("updateTime") or payload.get("transactTime")
        observed_at = (
            datetime.fromtimestamp(int(updated_at) / 1000, tz=UTC)
            if updated_at not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        if original_quantity > Decimal("0") and filled_quantity >= original_quantity:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.BINANCE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.FILLED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_completed_fill",
                remaining_quantity=Decimal("0"),
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price,
                last_fill_at=observed_at,
                status_reason_code="reconciliation_completed_fill",
                status_message="Binance reconciled the submitted order to fully filled.",
                reason_codes=["reconciliation_completed_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if remote_status in {"NEW", "PARTIALLY_FILLED"}:
            if filled_quantity > Decimal("0"):
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.BINANCE.value,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    exchange_order_id=submitted_order.exchange_order_id,
                    status=SubmittedOrderStatus.PARTIALLY_FILLED,
                    reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                    event_type="reconciliation_partial_fill",
                    remaining_quantity=remaining_quantity,
                    filled_quantity=filled_quantity,
                    average_fill_price=average_fill_price,
                    last_fill_at=observed_at,
                    status_reason_code="reconciliation_partial_fill",
                    status_message="Binance reconciled the submitted order to partially filled.",
                    reason_codes=["reconciliation_partial_fill"],
                    cancelable_in_principle=True,
                    amendable_in_principle=False,
                    raw_payload=payload,
                    observed_at=observed_at,
                )
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.BINANCE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_open_order",
                remaining_quantity=remaining_quantity,
                acknowledged_at=submitted_order.acknowledged_at,
                status_reason_code="reconciliation_open_order",
                status_message="Binance still reports the submitted order as open.",
                reason_codes=["reconciliation_open_order"],
                cancelable_in_principle=True,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if remote_status in {"CANCELED", "CANCELLED"}:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.BINANCE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.CANCELED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_canceled",
                remaining_quantity=remaining_quantity,
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price,
                last_fill_at=observed_at if filled_quantity > Decimal("0") else submitted_order.last_fill_at,
                status_reason_code="reconciliation_canceled",
                status_message=(
                    "Binance reports the submitted order as canceled after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Binance reports the submitted order as canceled."
                ),
                reason_codes=["reconciliation_canceled"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if remote_status in {"EXPIRED", "EXPIRED_IN_MATCH"}:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.BINANCE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.EXPIRED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_expired",
                remaining_quantity=remaining_quantity,
                filled_quantity=filled_quantity,
                average_fill_price=average_fill_price,
                last_fill_at=observed_at if filled_quantity > Decimal("0") else submitted_order.last_fill_at,
                status_reason_code="reconciliation_expired",
                status_message=(
                    "Binance reports the submitted order as expired after partial execution."
                    if filled_quantity > Decimal("0")
                    else "Binance reports the submitted order as expired."
                ),
                reason_codes=["reconciliation_expired"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if remote_status == "REJECTED":
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.BINANCE.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.REJECTED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_rejected",
                status_reason_code="venue_rejected",
                status_message="Binance reports the submitted order as rejected.",
                reason_codes=["venue_rejected"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.BINANCE.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_unknown_status",
            status_reason_code="reconciliation_unknown_status",
            status_message=f"Binance returned an unrecognized order status: {remote_status or 'missing'}",
            reason_codes=["reconciliation_unknown_status"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=payload,
            observed_at=observed_at,
        )


def _filter_value(item: dict[str, Any], filter_type: str, key: str) -> str | None:
    for payload in item.get("filters", []):
        if payload.get("filterType") == filter_type:
            return payload.get(key)
    return None
