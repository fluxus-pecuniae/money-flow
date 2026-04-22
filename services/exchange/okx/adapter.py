"""OKX venue adapter."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
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


def _okx_timeframe(timeframe: str | Timeframe) -> str:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1H", "4h": "4H", "1d": "1D"}
    if tf not in mapping:
        raise VenueAdapterError(f"Unsupported OKX timeframe: {tf}")
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


def _product_type_for_okx(market_type: MarketType, settle_asset: str | None, quote_asset: str) -> ProductType:
    if market_type == MarketType.SPOT:
        return ProductType.SPOT
    if settle_asset and settle_asset.upper() != quote_asset.upper():
        return ProductType.INVERSE
    return ProductType.LINEAR


class OkxExchangeAdapter(ReadOnlyVenueAdapter):
    account_model = "account_with_subaccounts"
    support_level = VenueSupportLevel.EXECUTION_PREPARABLE
    adapter_supports_order_submission = True
    adapter_supports_order_cancel = True
    adapter_supports_order_amend = True
    supports_order_preview = True
    supports_account_snapshot = True
    supports_open_orders_query = True
    supports_open_positions_query = False
    supports_recent_fills_query = True
    supports_reduce_only_orders = True
    supports_client_order_ids = True
    supported_order_types = (OrderType.MARKET, OrderType.LIMIT, OrderType.STOP)
    supported_time_in_force = ("gtc", "ioc", "fok", "post_only")
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
            resolved_settings.okx_integration,
            resolved_settings,
            transport=transport,
            session_factory=session_factory,
        )

    async def _ping(self) -> None:
        await self._request("GET", "/api/v5/public/time", None)

    async def _fetch_symbol_metadata(self) -> Sequence[SymbolMetadata]:
        metadata: list[SymbolMetadata] = []
        for inst_type in ("SPOT", "SWAP"):
            payload = await self._request(
                "GET",
                "/api/v5/public/instruments",
                {"instType": inst_type},
            )
            for item in payload.get("data", []):
                market_type = MarketType.SPOT if inst_type == "SPOT" else MarketType.PERPETUAL
                base_asset = str(item.get("baseCcy") or item.get("uly", "").split("-")[0]).upper()
                quote_asset = str(item.get("quoteCcy") or item.get("settleCcy") or "USDT").upper()
                settlement_asset = str(item.get("settleCcy") or quote_asset).upper() if inst_type != "SPOT" else None
                product_type = _product_type_for_okx(market_type, settlement_asset, quote_asset)
                canonical_symbol = base_asset
                metadata.append(
                    SymbolMetadata(
                        instrument_key=build_instrument_key(
                            market_type=market_type,
                            product_type=product_type,
                            base_asset=base_asset,
                            quote_asset=quote_asset,
                            settlement_asset=settlement_asset,
                        ),
                        instrument_ref_id=None,
                        venue=Venue.OKX.value,
                        symbol=canonical_symbol,
                        exchange_symbol=str(item["instId"]).upper(),
                        venue_asset_id=str(item["instId"]),
                        market_type=market_type,
                        product_type=product_type,
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        settlement_asset=settlement_asset,
                        price_tick_size=decimal_or(item.get("tickSz"), "0.1"),
                        quantity_step_size=decimal_or(item.get("lotSz"), "0.001"),
                        min_order_size=decimal_or(item.get("minSz"), "0.001"),
                        is_active=item.get("state", "live") == "live",
                        asset_id=None,
                        is_perpetual=market_type == MarketType.PERPETUAL,
                        is_builder_deployed=False,
                        is_strategy_eligible=True,
                        is_trading_eligible=False,
                        raw_metadata={"instType": inst_type, "settleCcy": settlement_asset, "venue": "okx"},
                    )
                )
        return metadata

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue.OKX,
            support_level=self.support_level,
            supports_spot=True,
            supports_perpetuals=True,
            supports_futures=True,
            supports_options=True,
            supports_hedge_mode=True,
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
            supports_reduce_only_orders=True,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=True,
            supported_order_types=list(self.supported_order_types),
            supported_time_in_force=list(self.supported_time_in_force),
            account_model=self.account_model,
            notes=(
                "OKX currently covers spot and perpetual catalog sync, preview/preflight, "
                "an account-targeted signed submit path, direct private open-order and recent-fill polling, "
                "and bounded amend/cancel lifecycle depth at the current execution boundary."
            ),
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def submit_order(self, intent: OrderIntent):
        if intent is None:
            raise VenueAdapterError(
                "OKX submission requires a concrete child intent.",
                reason_codes=["missing_order_intent"],
            )
        preview = await self.prepare_order_preview(intent)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE or preview.payload is None:
            raise VenueAdapterError(
                "OKX order is not venue-preparable.",
                reason_codes=list(preview.reason_codes or ["preview_rejected"]),
                payload={"prepared_order_preview": preview.payload or {}},
            )
        context = self._resolve_execution_context(intent.venue_account_ref_id)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        passphrase = self._api_passphrase_for_context(context)
        if not api_key or not api_secret or not passphrase:
            raise VenueAdapterError(
                "OKX submission requires targeted API key, secret, and passphrase material.",
                reason_codes=["missing_auth_material"],
            )
        endpoint, body = self._submission_request_from_preview(preview)
        rendered_body = self._render_json_body(body, sort_keys=True)
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        signing_payload = f"{timestamp}POST{endpoint}{rendered_body}"
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, signing_payload),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
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
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        passphrase = self._api_passphrase_for_context(context)
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret or not passphrase:
            raise VenueAdapterError(
                "OKX reconciliation requires targeted API key, secret, and passphrase material.",
                reason_codes=["missing_auth_material"],
            )
        if exchange_symbol is None or submitted_order.exchange_order_id is None:
            return self._missing_order_update(submitted_order, {})
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        endpoint = "/api/v5/trade/order"
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(
                api_secret,
                f"{timestamp}GET{endpoint}?instId={exchange_symbol}&ordId={submitted_order.exchange_order_id}",
            ),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        payload = await self._request(
            "GET",
            endpoint,
            {"instId": exchange_symbol, "ordId": submitted_order.exchange_order_id},
            headers=headers,
        )
        data = payload.get("data", [])
        if payload.get("code") not in (None, 0, "0") or not data:
            return self._missing_order_update(submitted_order, payload)
        return self._reconciliation_update_from_order_payload(submitted_order, data[0])

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._context_for_submitted_order(submitted_order)
        self._assert_submission_controls(context)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        passphrase = self._api_passphrase_for_context(context)
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret or not passphrase:
            raise VenueAdapterError(
                "OKX cancellation requires targeted API key, secret, and passphrase material.",
                reason_codes=["missing_auth_material"],
            )
        if exchange_symbol is None or submitted_order.exchange_order_id is None:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_missing_order_identity"],
                message="OKX cancellation requires the targeted exchange symbol and exchange order id.",
            )
        endpoint = "/api/v5/trade/cancel-order"
        body = {"instId": exchange_symbol, "ordId": submitted_order.exchange_order_id}
        rendered_body = self._render_json_body(body, sort_keys=True)
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, f"{timestamp}POST{endpoint}{rendered_body}"),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        response = await self._request_json_exact(
            "POST",
            endpoint,
            body=body,
            headers=headers,
            rendered_body=rendered_body,
        )
        data = response.get("data", [])
        first = data[0] if data else {}
        if response.get("code") not in (None, 0, "0") or str(first.get("sCode") or "0") not in {"0", ""}:
            return self._cancel_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["cancel_rejected"],
                message=str(first.get("sMsg") or response.get("msg") or "OKX rejected cancellation."),
                raw_payload=response,
            )
        return self._cancel_success_update(
            submitted_order=submitted_order,
            status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            event_type="cancel_acknowledged",
            status_reason_code="cancel_acknowledged",
            remaining_quantity=submitted_order.remaining_quantity,
            message="OKX accepted the cancel request; reconciliation must still confirm final canceled state.",
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
        passphrase = self._api_passphrase_for_context(context)
        exchange_symbol = self._exchange_symbol_for_submitted_order(submitted_order)
        if not api_key or not api_secret or not passphrase:
            raise VenueAdapterError(
                "OKX amendment requires targeted API key, secret, and passphrase material.",
                reason_codes=["missing_auth_material"],
            )
        if submitted_order.order_type != OrderType.LIMIT:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_not_supported_for_order_type"],
                message="OKX amendment is currently limited to limit orders in the implemented scope.",
            )
        if exchange_symbol is None or submitted_order.exchange_order_id is None:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_missing_order_identity"],
                message="OKX amendment requires the targeted exchange symbol and exchange order id.",
            )
        if new_quantity is None and new_limit_price is None:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_no_changes_requested"],
                message="OKX amendment requires at least one explicit quantity or limit-price change.",
            )
        filled_quantity = submitted_order.filled_quantity or Decimal("0")
        if new_quantity is not None and new_quantity <= filled_quantity:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_quantity_below_filled"],
                message="OKX amendment cannot reduce the order quantity below already filled size.",
            )
        endpoint = "/api/v5/trade/amend-order"
        body: dict[str, Any] = {"instId": exchange_symbol, "ordId": submitted_order.exchange_order_id}
        if new_limit_price is not None:
            body["newPx"] = str(new_limit_price)
        if new_quantity is not None:
            body["newSz"] = str(new_quantity)
        rendered_body = self._render_json_body(body, sort_keys=True)
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, f"{timestamp}POST{endpoint}{rendered_body}"),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        response = await self._request_json_exact(
            "POST",
            endpoint,
            body=body,
            headers=headers,
            rendered_body=rendered_body,
        )
        data = response.get("data", [])
        first = data[0] if data else {}
        if response.get("code") not in (None, 0, "0") or str(first.get("sCode") or "0") not in {"0", ""}:
            return self._amend_rejected_update(
                submitted_order=submitted_order,
                reason_codes=["amend_rejected"],
                message=str(first.get("sMsg") or response.get("msg") or "OKX rejected amendment."),
                raw_payload=response,
            )
        return self._amend_acknowledged_update(
            submitted_order=submitted_order,
            new_quantity=new_quantity,
            new_limit_price=new_limit_price,
            message="OKX accepted the amend request; reconciliation must still confirm the refreshed working state.",
            raw_payload=response,
        )

    async def _fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        api_key = self._api_key_for_context(context)
        api_secret = self._api_secret_for_context(context)
        passphrase = self._api_passphrase_for_context(context)
        if not api_key or not api_secret or not passphrase:
            return await super()._fetch_open_orders_with_source(venue_account_ref_id=venue_account_ref_id)
        endpoint = "/api/v5/trade/orders-pending"
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, f"{timestamp}GET{endpoint}"),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        payload = await self._request("GET", endpoint, None, headers=headers)
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return (
            "venue_query",
            [
                self._open_order_from_payload(payload=item, context=context)
                for item in data
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
        passphrase = self._api_passphrase_for_context(context)
        if not api_key or not api_secret or not passphrase:
            return await super()._fetch_recent_fills_with_source(
                limit=limit,
                venue_account_ref_id=venue_account_ref_id,
            )
        endpoint = "/api/v5/trade/fills"
        params = {"limit": min(limit, 100)}
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        signing_suffix = urllib.parse.urlencode(params)
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, f"{timestamp}GET{endpoint}?{signing_suffix}"),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        payload = await self._request("GET", endpoint, params, headers=headers)
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return (
            "venue_query",
            [
                self._fill_from_payload(payload=item, context=context)
                for item in data[:limit]
                if isinstance(item, dict)
            ],
        )

    def _open_order_from_payload(
        self,
        *,
        payload: dict[str, Any],
        context,
    ) -> VenuePrivateOpenOrder:
        exchange_symbol = str(payload.get("instId") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.split("-")[0]
        original_quantity = decimal_or(payload.get("sz"), "0")
        filled_quantity = decimal_or(payload.get("accFillSz"), "0")
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(payload.get("avgPx"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        observed_ms = payload.get("uTime") or payload.get("cTime")
        observed_at = (
            datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
            if observed_ms not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        state = str(payload.get("state", "")).lower()
        status = (
            SubmittedOrderStatus.PARTIALLY_FILLED
            if state == "partially_filled" or filled_quantity > Decimal("0")
            else SubmittedOrderStatus.ACKNOWLEDGED
        )
        client_order_id = str(payload.get("clOrdId")) if payload.get("clOrdId") not in (None, "") else None
        exchange_order_id = str(payload.get("ordId")) if payload.get("ordId") not in (None, "") else None
        linked_submitted_order_id, linked_order_intent_id = self._linked_submitted_order_identity(
            venue_account_ref_id=context.venue_account_ref_id,
            account_address=context.account_address or context.account_identifier,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
        )
        return VenuePrivateOpenOrder(
            venue=Venue.OKX.value,
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
            side=OrderSide.BUY if str(payload.get("side", "")).lower() == "buy" else OrderSide.SELL,
            order_type=OrderType(str(payload.get("ordType", "limit")).lower().replace("post_only", "limit")),
            limit_price=(
                decimal_or(payload.get("px"), "0")
                if payload.get("px") not in (None, "", "0", 0)
                else None
            ),
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price_value,
            last_fill_at=observed_at if filled_quantity > Decimal("0") else None,
            status_reason_code=(
                "reconciliation_partial_fill" if status == SubmittedOrderStatus.PARTIALLY_FILLED else "reconciliation_open_order"
            ),
            status_message="OKX private open-order query returned a working order snapshot.",
            reason_codes=(
                ["reconciliation_partial_fill"]
                if status == SubmittedOrderStatus.PARTIALLY_FILLED
                else ["reconciliation_open_order"]
            ),
            cancelable_in_principle=True,
            amendable_in_principle=True,
            reduce_only=str(payload.get("reduceOnly", "")).lower() == "true",
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
        exchange_symbol = str(payload.get("instId") or "")
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol.split("-")[0]
        observed_ms = payload.get("ts") or payload.get("fillTime")
        filled_at = (
            datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
            if observed_ms not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        return Fill(
            fill_id=f"fill-okx-{payload.get('tradeId') or payload.get('billId') or payload.get('ordId')}",
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.OKX.value,
            account_address=context.account_address or context.account_identifier,
            submitted_order_id=str(payload.get("ordId")) if payload.get("ordId") not in (None, "") else "",
            exchange_order_id=str(payload.get("ordId")) if payload.get("ordId") not in (None, "") else None,
            symbol=symbol,
            price=decimal_or(payload.get("fillPx"), "0"),
            quantity=abs(decimal_or(payload.get("fillSz"), "0")),
            fee=abs(decimal_or(payload.get("fee"), "0")),
            filled_at=filled_at,
        )

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]:
        inst_id = f"{symbol.upper()}-USDT-SWAP"
        payload = await self._request(
            "GET",
            "/api/v5/market/candles",
            {"instId": inst_id, "bar": _okx_timeframe(timeframe), "before": end_time_ms, "after": start_time_ms},
        )
        candles: list[Candle] = []
        delta = _timeframe_delta(timeframe)
        for row in payload.get("data", []):
            open_time = datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC)
            candles.append(
                Candle(
                    instrument_key=build_instrument_key(
                        market_type=MarketType.PERPETUAL,
                        product_type=ProductType.LINEAR,
                        base_asset=symbol.upper(),
                        quote_asset="USDT",
                        settlement_asset="USDT",
                    ),
                    instrument_ref_id=None,
                    venue=Venue.OKX.value,
                    symbol=symbol.upper(),
                    timeframe=Timeframe(timeframe),
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
        return list(reversed(candles))

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        payload = await self._request("GET", "/api/v5/market/books", {"instId": f"{symbol.upper()}-USDT-SWAP", "sz": 1})
        data = payload.get("data", [])
        if not data:
            return None
        book = data[0]
        bid = (book.get("bids") or [[None, None]])[0]
        ask = (book.get("asks") or [[None, None]])[0]
        return TopOfBookSnapshot(
            instrument_key=build_instrument_key(
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset=symbol.upper(),
                quote_asset="USDT",
                settlement_asset="USDT",
            ),
            instrument_ref_id=None,
            venue=Venue.OKX.value,
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
        passphrase = self._api_passphrase_for_context(context)
        if not api_key or not api_secret or not passphrase:
            return None
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": self._hmac_sha256_base64(api_secret, f"{timestamp}GET/api/v5/account/balance"),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if self.integration.use_demo_mode:
            headers["x-simulated-trading"] = "1"
        payload = await self._request("GET", "/api/v5/account/balance", None, headers=headers)
        data = payload.get("data", [])
        if not data:
            return None
        row = data[0]
        details = row.get("details", [])
        available = decimal_or(details[0].get("availEq"), "0") if details else decimal_or(row.get("availEq"), "0")
        equity = decimal_or(row.get("totalEq"), "0")
        return ExchangeAccountSnapshot(
            venue_account_ref_id=context.venue_account_ref_id,
            venue=Venue.OKX.value,
            environment=self._integration_environment,
            account_address=context.account_address or context.account_identifier,
            equity=equity,
            available_balance=available,
            margin_used=decimal_or(row.get("imr"), "0"),
            unrealized_pnl=decimal_or(row.get("upl"), "0"),
            total_position_notional=decimal_or(row.get("notionalUsd"), "0"),
            observed_at=datetime.now(UTC),
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
            "endpoint": "/api/v5/trade/order",
            "instId": exchange_symbol,
            "tdMode": "cross",
            "side": intent.side.value,
            "ordType": intent.order_type.value,
            "sz": str(intent.quantity),
            "reduceOnly": intent.reduce_only,
        }
        if intent.limit_price is not None:
            payload["px"] = str(intent.limit_price)
        if time_in_force is not None and intent.order_type != OrderType.MARKET:
            payload["tif"] = time_in_force
        if client_order_id is not None:
            payload["clOrdId"] = client_order_id
        return payload

    def _missing_order_update(
        self,
        submitted_order: SubmittedOrder,
        payload: dict[str, Any],
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.OKX.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message=str(payload.get("msg") or "OKX reconciliation did not find the order."),
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
        state = str(payload.get("state", "")).lower()
        original_quantity = decimal_or(payload.get("sz"), str(submitted_order.original_quantity or "0"))
        filled_quantity = decimal_or(payload.get("accFillSz"), str(submitted_order.filled_quantity or "0"))
        remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        average_fill_price = decimal_or(payload.get("avgPx"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        fill_time = payload.get("fillTime") or payload.get("uTime")
        observed_at = (
            datetime.fromtimestamp(int(fill_time) / 1000, tz=UTC)
            if fill_time not in (None, "", 0, "0")
            else datetime.now(UTC)
        )
        if original_quantity > Decimal("0") and filled_quantity >= original_quantity:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.OKX.value,
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
                status_message="OKX reconciled the submitted order to fully filled.",
                reason_codes=["reconciliation_completed_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if state in {"live", "partially_filled"}:
            if filled_quantity > Decimal("0"):
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.OKX.value,
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
                    status_message="OKX reconciled the submitted order to partially filled.",
                    reason_codes=["reconciliation_partial_fill"],
                    cancelable_in_principle=True,
                    amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                    raw_payload=payload,
                    observed_at=observed_at,
                )
            if submitted_order.status in {
                SubmittedOrderStatus.CANCEL_REQUESTED,
                SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            }:
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=Venue.OKX.value,
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
                    status_message="OKX still reports the submitted order as open after accepting the cancel request.",
                    reason_codes=["reconciliation_cancel_pending"],
                    cancelable_in_principle=False,
                    amendable_in_principle=False,
                    raw_payload=payload,
                    observed_at=observed_at,
                )
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.OKX.value,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=submitted_order.exchange_order_id,
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_open_order",
                remaining_quantity=remaining_quantity,
                acknowledged_at=submitted_order.acknowledged_at,
                status_reason_code="reconciliation_open_order",
                status_message="OKX still reports the submitted order as open.",
                reason_codes=["reconciliation_open_order"],
                cancelable_in_principle=True,
                amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                raw_payload=payload,
                observed_at=observed_at,
            )
        if state in {"canceled", "mmp_canceled"}:
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=Venue.OKX.value,
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
                    "OKX reports the submitted order as canceled after partial execution."
                    if filled_quantity > Decimal("0")
                    else "OKX reports the submitted order as canceled."
                ),
                reason_codes=["reconciliation_canceled"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=payload,
                observed_at=observed_at,
            )
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=Venue.OKX.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_unknown_status",
            status_reason_code="reconciliation_unknown_status",
            status_message=f"OKX returned an unrecognized order state: {state or 'missing'}",
            reason_codes=["reconciliation_unknown_status"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=payload,
            observed_at=observed_at,
        )
