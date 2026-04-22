"""Hyperliquid exchange adapter and reconciliation primitives."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from typing import Any

import httpx
from sqlalchemy import select
import websockets

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    AttributionStatus,
    Environment,
    MarketType,
    OrderSide,
    OrderType,
    PositionStatus,
    ProductType,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    Timeframe,
    Venue,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
)
from core.domain.hyperliquid import (
    HyperliquidAccountState,
    HyperliquidReconciliationSnapshot,
    HyperliquidUniverseAsset,
    HyperliquidWalletContext,
    UniversePolicy,
)
from core.domain.models import (
    Candle,
    ExchangeAccountSnapshot,
    ExchangeSessionState,
    ExchangeStatus,
    Fill,
    Instrument,
    OrderBookDepthSummary,
    OrderIntent,
    Position,
    PreparedVenueOrder,
    SubmittedOrder,
    SubmittedOrderLifecycleUpdate,
    SubmittedOrderPrivateFillEvidence,
    SymbolMetadata,
    TopOfBookSnapshot,
    VenueAccountConnectivity,
    VenueCapabilities,
    VenueOrderConstraints,
    VenuePrivateOpenOrder,
    VenuePrivateStateSummary,
)
from core.interfaces.hyperliquid import HyperliquidAdapterContract
from core.interfaces.services import ExchangeAdapter
from core.logging.setup import get_logger
from db.models import (
    ExchangeAccountSnapshotModel,
    FillModel,
    InstrumentModel,
    PositionModel,
    SubmittedOrderModel,
    SymbolModel,
    SystemStateModel,
    VenueAccountModel,
)
from db.session import SessionLocal
from services.runtime.context import DefaultRuntimeContextService
from services.exchange.base import (
    ReadOnlyVenueAdapter,
    ResolvedVenueCredentials,
    VenueAccountExecutionContext,
    VenueAdapterError,
)
from services.exchange.common import list_instruments_for_venue
from services.exchange.hyperliquid.signing import float_to_wire, sign_l1_action, signer_address

INFO_PATH = "/info"
STATE_KEY_LAST_EXCHANGE_SYNC = "hyperliquid:last_exchange_sync"
VENUE_NAME = "hyperliquid"
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"


class HyperliquidAdapterError(VenueAdapterError):
    """Raised when an adapter request or reconciliation step fails."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _decimal(value: Any, default: str = "0") -> Decimal:
    raw = default if value in (None, "") else str(value)
    return Decimal(raw)


def _position_mark_price(position_data: dict[str, Any]) -> Decimal | None:
    mark_px = position_data.get("markPx")
    if mark_px not in (None, ""):
        return _decimal(mark_px)
    position_value = position_data.get("positionValue")
    size = position_data.get("szi")
    if position_value in (None, "") or size in (None, ""):
        return None
    quantity = _decimal(size)
    if quantity == Decimal("0"):
        return None
    return abs(_decimal(position_value) / quantity)


def _timeframe_to_interval(timeframe: str | Timeframe) -> str:
    tf = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
    mapping = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
    }
    if tf not in mapping:
        raise HyperliquidAdapterError(f"Unsupported Hyperliquid timeframe: {tf}")
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


def _build_instrument_key(
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


def _classify_builder_deployed_asset(raw_asset: dict[str, Any]) -> bool:
    """Best-effort Hyperliquid venue classification.

    Prefer explicit metadata flags when present; fall back to symbol naming only
    when the payload does not expose a stronger signal.
    """

    explicit_flags = (
        raw_asset.get("isHip3"),
        raw_asset.get("isBuilderDeployed"),
        raw_asset.get("builderDeployed"),
        raw_asset.get("deployAuction"),
        raw_asset.get("builder"),
        raw_asset.get("deployer"),
    )
    if any(bool(flag) for flag in explicit_flags):
        return True
    return ":" in str(raw_asset.get("name", "")).upper()


class HyperliquidExchangeAdapter(ExchangeAdapter, HyperliquidAdapterContract):
    """Hyperliquid REST adapter with persistence-backed sync and reconciliation helpers."""

    support_level = VenueSupportLevel.EXECUTION_PREPARABLE
    adapter_supports_order_submission = True
    adapter_supports_order_cancel = True
    adapter_supports_order_amend = True
    adapter_supports_user_streams = False
    supports_order_preview = True
    supports_account_snapshot = True
    supports_open_orders_query = True
    supports_open_positions_query = True
    supports_recent_fills_query = True
    supports_reduce_only_orders = True
    supports_client_order_ids = True
    supported_order_types = (OrderType.MARKET, OrderType.LIMIT)
    supported_time_in_force = ("gtc", "ioc", "alo")
    private_lifecycle_update_mode = "polling"
    open_orders_state_source = "venue_query"
    recent_fills_state_source = "venue_query"
    _extract_exchange_order_id = staticmethod(ReadOnlyVenueAdapter._extract_exchange_order_id)
    _extract_client_order_id = staticmethod(ReadOnlyVenueAdapter._extract_client_order_id)
    _normalize_submission_status = staticmethod(ReadOnlyVenueAdapter._normalize_submission_status)

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        transport: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
        session_factory: Callable[[], Any] = SessionLocal,
        runtime_context_service: DefaultRuntimeContextService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.integration = self.settings.hyperliquid_integration
        self._transport = transport
        self._session_factory = session_factory
        self.runtime_context_service = runtime_context_service or DefaultRuntimeContextService(
            self.settings,
            session_factory=session_factory,
        )
        self._logger = get_logger(__name__)
        self._http_client: httpx.AsyncClient | None = None
        self._session_sequence = 0
        self._last_success_at: datetime | None = None
        self._last_error: str | None = None

    @staticmethod
    def _focused_binding(context: Any) -> Any | None:
        return context.bindings[0] if context.bindings else None

    async def connect(self) -> ExchangeSessionState:
        await self._info_request({"type": "allMids", "dex": self.settings.exchange.dex_name})
        self._session_sequence += 1
        self._last_success_at = _utcnow()
        self._write_control_state(
            STATE_KEY_LAST_EXCHANGE_SYNC,
            {
                "connected": True,
                "last_success_at": self._last_success_at.isoformat(),
                "environment": self.settings.app.environment.value,
                "api_base_url": self._api_base_url,
            },
        )
        return ExchangeSessionState(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            connected=True,
            last_heartbeat_at=self._last_success_at,
            session_sequence=self._session_sequence,
        )

    async def disconnect(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        self._write_control_state(
            STATE_KEY_LAST_EXCHANGE_SYNC,
            {
                "connected": False,
                "last_success_at": self._last_success_at.isoformat() if self._last_success_at else None,
                "last_error": self._last_error,
            },
        )

    async def sync_symbols(self) -> Sequence[SymbolMetadata]:
        universe_assets = await self.sync_universe(
            UniversePolicy(
                include_standard_perp_universe=self.settings.universe_policy.include_standard_perp_universe,
                include_builder_deployed_in_catalog=self.settings.universe_policy.include_builder_deployed_in_catalog,
                allow_builder_deployed_for_strategy=self.settings.universe_policy.allow_builder_deployed_for_strategy,
                allow_builder_deployed_for_trading=self.settings.universe_policy.allow_builder_deployed_for_trading,
            )
        )
        return [
            SymbolMetadata(
                instrument_key=_build_instrument_key(
                    market_type=MarketType.PERPETUAL,
                    product_type=ProductType.LINEAR,
                    base_asset=asset.base_asset,
                    quote_asset=asset.quote_asset,
                    settlement_asset=asset.quote_asset,
                ),
                instrument_ref_id=None,
                venue=asset.venue,
                symbol=asset.canonical_symbol,
                exchange_symbol=asset.exchange_symbol,
                venue_asset_id=str(asset.asset_id) if asset.asset_id is not None else None,
                market_type=MarketType.PERPETUAL,
                product_type=ProductType.LINEAR,
                base_asset=asset.base_asset,
                quote_asset=asset.quote_asset,
                settlement_asset=asset.quote_asset,
                price_tick_size=_derive_price_tick_size(asset.raw_metadata),
                quantity_step_size=_derive_quantity_step_size(asset.raw_metadata),
                min_order_size=_derive_quantity_step_size(asset.raw_metadata),
                is_active=True,
                asset_id=asset.asset_id,
                is_perpetual=asset.is_perpetual,
                is_builder_deployed=asset.is_builder_deployed,
                is_strategy_eligible=(
                    not asset.is_builder_deployed
                    or self.settings.universe_policy.allow_builder_deployed_for_strategy
                ),
                is_trading_eligible=(
                    not asset.is_builder_deployed
                    or self.settings.universe_policy.allow_builder_deployed_for_trading
                ),
                raw_metadata=asset.raw_metadata,
            )
            for asset in universe_assets
        ]

    async def get_session_state(self) -> ExchangeSessionState:
        state = self._read_control_state(STATE_KEY_LAST_EXCHANGE_SYNC)
        return ExchangeSessionState(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            connected=bool(state and state.get("connected")),
            last_heartbeat_at=(
                datetime.fromisoformat(state["last_success_at"])
                if state and state.get("last_success_at")
                else self._last_success_at
            ),
            session_sequence=self._session_sequence,
        )

    async def get_venue_capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(
            venue=Venue.HYPERLIQUID,
            support_level=self.support_level,
            supports_spot=False,
            supports_perpetuals=True,
            supports_futures=False,
            supports_options=False,
            supports_hedge_mode=False,
            supports_websocket_market_data=True,
            supports_user_streams=False,
            supports_account_sync=True,
            supports_top_of_book=False,
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
            supports_open_orders_query=True,
            supports_open_positions_query=True,
            supports_reduce_only_orders=True,
            supports_client_order_ids=True,
            supports_demo_mode=True,
            supports_subaccounts=False,
            supported_order_types=list(self.supported_order_types),
            supported_time_in_force=list(self.supported_time_in_force),
            account_model="wallet_address",
            notes=(
                "Hyperliquid currently covers catalog sync, exchange/account truth, preview/preflight, "
                "account-targeted SDK-faithful L1 signed submission, truthful cancel acknowledgement, "
                "native limit-order amend, richer order-status reconciliation for the current perpetual scope, "
                "and direct recent-fill polling."
            ),
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def list_instruments(self) -> Sequence[Instrument]:
        return list_instruments_for_venue(
            self._session_factory,
            venue=self.settings.exchange.venue,
        )

    async def submit_order(self, intent: OrderIntent) -> SubmittedOrder:
        if intent is None:
            raise HyperliquidAdapterError(
                "Hyperliquid submission requires a concrete child intent.",
                reason_codes=["missing_order_intent"],
            )
        preview = await self.prepare_order_preview(intent)
        if preview.preview_status != VenueOrderPreviewStatus.PREPARABLE or preview.payload is None:
            raise HyperliquidAdapterError(
                "Hyperliquid order is not venue-preparable: "
                f"{(preview.reason_codes or ['preview_rejected'])[0]}",
                reason_codes=list(preview.reason_codes or ["preview_rejected"]),
            )
        execution_context = self._resolve_execution_context(intent.venue_account_ref_id)
        self._assert_submission_controls(execution_context)
        credentials = self._resolve_credentials(execution_context)
        if not credentials.signing_private_key:
            raise HyperliquidAdapterError(
                "Hyperliquid submission requires a targeted signing private key.",
                reason_codes=list(credentials.reason_codes or ["missing_auth_material"]),
            )
        endpoint = str(preview.payload.get("endpoint", "/exchange"))
        action = dict(preview.payload.get("action") or {})
        payload = self._signed_exchange_payload(
            action=action,
            context=execution_context,
            signing_private_key=credentials.signing_private_key,
        )
        response = await self._exchange_request(payload, path=endpoint)
        return ReadOnlyVenueAdapter._submitted_order_from_response(
            self,
            intent=intent,
            preview=preview,
            response=response,
            context=execution_context,
        )

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._resolve_execution_context(submitted_order.venue_account_ref_id)
        self._assert_submission_controls(context)
        credentials = self._resolve_credentials(context)
        if not credentials.signing_private_key:
            raise HyperliquidAdapterError(
                "Hyperliquid cancellation requires a targeted signing private key.",
                reason_codes=list(credentials.reason_codes or ["missing_auth_material"]),
            )
        asset_id = self._asset_id_for_submitted_order(submitted_order)
        if asset_id is None or submitted_order.exchange_order_id is None:
            return ReadOnlyVenueAdapter._cancel_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["cancel_missing_order_identity"],
                message="Hyperliquid cancellation requires the targeted asset id and exchange order id.",
            )
        action = {
            "type": "cancel",
            "cancels": [{"a": int(asset_id), "o": int(submitted_order.exchange_order_id)}],
        }
        response = await self._exchange_request(
            self._signed_exchange_payload(
                action=action,
                context=context,
                signing_private_key=credentials.signing_private_key,
            )
        )
        if not self._hyperliquid_action_succeeded(response):
            return ReadOnlyVenueAdapter._cancel_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["cancel_rejected"],
                message="Hyperliquid rejected cancellation for the submitted order.",
                raw_payload=response if isinstance(response, dict) else {"response": response},
            )
        return ReadOnlyVenueAdapter._cancel_success_update(
            self,
            submitted_order=submitted_order,
            status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            event_type="cancel_acknowledged",
            status_reason_code="cancel_acknowledged",
            remaining_quantity=submitted_order.remaining_quantity,
            message="Hyperliquid accepted the cancel request; reconciliation must still confirm final canceled state.",
            reason_codes=["cancel_acknowledged"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=response if isinstance(response, dict) else {"response": response},
        )

    async def amend_order(
        self,
        submitted_order: SubmittedOrder,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        context = self._resolve_execution_context(submitted_order.venue_account_ref_id)
        self._assert_submission_controls(context)
        credentials = self._resolve_credentials(context)
        if not credentials.signing_private_key:
            raise HyperliquidAdapterError(
                "Hyperliquid amendment requires a targeted signing private key.",
                reason_codes=list(credentials.reason_codes or ["missing_auth_material"]),
            )
        if submitted_order.order_type != OrderType.LIMIT:
            return ReadOnlyVenueAdapter._amend_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["amend_not_supported_for_order_type"],
                message="Hyperliquid amendment is currently limited to limit orders in the implemented scope.",
            )
        asset_id = self._asset_id_for_submitted_order(submitted_order)
        if asset_id is None or submitted_order.exchange_order_id is None:
            return ReadOnlyVenueAdapter._amend_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["amend_missing_order_identity"],
                message="Hyperliquid amendment requires the targeted asset id and exchange order id.",
            )
        if new_quantity is None and new_limit_price is None:
            return ReadOnlyVenueAdapter._amend_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["amend_no_changes_requested"],
                message="Hyperliquid amendment requires at least one explicit quantity or limit-price change.",
            )
        filled_quantity = submitted_order.filled_quantity or Decimal("0")
        if new_quantity is not None and new_quantity <= filled_quantity:
            return ReadOnlyVenueAdapter._amend_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["amend_quantity_below_filled"],
                message="Hyperliquid amendment cannot reduce the order quantity below already filled size.",
            )
        action = {
            "type": "modify",
            "oid": int(submitted_order.exchange_order_id),
            "order": self._hyperliquid_modify_order_wire(
                submitted_order=submitted_order,
                asset_id=asset_id,
                new_quantity=new_quantity,
                new_limit_price=new_limit_price,
            ),
        }
        response = await self._exchange_request(
            self._signed_exchange_payload(
                action=action,
                context=context,
                signing_private_key=credentials.signing_private_key,
            )
        )
        if not self._hyperliquid_action_succeeded(response):
            return ReadOnlyVenueAdapter._amend_rejected_update(
                self,
                submitted_order=submitted_order,
                reason_codes=["amend_rejected"],
                message="Hyperliquid rejected the amend request for the submitted order.",
                raw_payload=response if isinstance(response, dict) else {"response": response},
            )
        return ReadOnlyVenueAdapter._amend_acknowledged_update(
            self,
            submitted_order=submitted_order,
            new_quantity=new_quantity,
            new_limit_price=new_limit_price,
            message="Hyperliquid accepted the amend request; reconciliation must still confirm the refreshed working state.",
            raw_payload=response if isinstance(response, dict) else {"response": response},
        )

    async def reconcile_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        account_address = submitted_order.account_address
        if not account_address:
            context = await self.runtime_context_service.ensure_active_context()
            focused_binding = self._focused_binding(context)
            account_address = (
                focused_binding.venue_account.account_address if focused_binding is not None else None
            )
        if not account_address:
            raise HyperliquidAdapterError(
                "Hyperliquid order reconciliation requires a targeted account address.",
                reason_codes=["account_identifier_missing"],
            )

        exchange_order_id = submitted_order.exchange_order_id
        status_payload: dict[str, Any] | None = None
        raw_order: dict[str, Any] | None = None
        remote_status: str | None = None
        status_timestamp: datetime | None = None
        if exchange_order_id is not None or submitted_order.client_order_id is not None:
            status_lookup = await self._info_request(
                {
                    "type": "orderStatus",
                    "user": account_address,
                    "oid": (
                        int(exchange_order_id)
                        if exchange_order_id is not None
                        else str(submitted_order.client_order_id)
                    ),
                }
            )
            if isinstance(status_lookup, dict):
                order_wrapper = status_lookup.get("order")
                if isinstance(order_wrapper, dict):
                    raw_order = (
                        dict(order_wrapper.get("order"))
                        if isinstance(order_wrapper.get("order"), dict)
                        else None
                    )
                    remote_status = str(order_wrapper.get("status") or "").lower() or None
                    observed_ms = order_wrapper.get("statusTimestamp")
                    if observed_ms not in (None, "", 0, "0"):
                        status_timestamp = datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
                    status_payload = status_lookup
                    if raw_order is not None and exchange_order_id is None and raw_order.get("oid") is not None:
                        exchange_order_id = str(raw_order.get("oid"))
        fills = await self._info_request(
            {
                "type": "userFills",
                "user": account_address,
                "aggregateByTime": False,
            }
        )
        matching_fills = [
            raw_fill
            for raw_fill in fills
            if exchange_order_id is not None and str(raw_fill.get("oid")) == str(exchange_order_id)
        ]
        total_quantity = sum(
            (abs(_decimal(item.get("sz"), "0")) for item in matching_fills),
            start=Decimal("0"),
        )
        weighted_notional = sum(
            (_decimal(item.get("px"), "0") * abs(_decimal(item.get("sz"), "0")) for item in matching_fills),
            start=Decimal("0"),
        )
        average_fill_price = (
            weighted_notional / total_quantity if total_quantity > Decimal("0") else None
        )
        original_quantity = submitted_order.original_quantity or Decimal("0")
        if raw_order is not None and raw_order.get("origSz") not in (None, ""):
            original_quantity = _decimal(raw_order.get("origSz"), str(original_quantity or "0"))
        if (
            total_quantity <= Decimal("0")
            and raw_order is not None
            and original_quantity > Decimal("0")
            and remote_status in {"open", "triggered"}
        ):
            remaining_from_order = _decimal(raw_order.get("sz"), "0")
            total_quantity = max(original_quantity - remaining_from_order, Decimal("0"))
        remaining_quantity = max(original_quantity - total_quantity, Decimal("0"))
        last_fill_at = (
            max(datetime.fromtimestamp(int(item["time"]) / 1000, tz=UTC) for item in matching_fills)
            if matching_fills
            else (status_timestamp if total_quantity > Decimal("0") else submitted_order.last_fill_at)
        )
        acknowledged_at = (
            datetime.fromtimestamp(int(raw_order["timestamp"]) / 1000, tz=UTC)
            if raw_order is not None and raw_order.get("timestamp") not in (None, "", 0, "0")
            else submitted_order.acknowledged_at
        )
        raw_payload = {
            "order_status": status_payload or {},
            "fills": [dict(item) for item in matching_fills],
        }

        if remote_status == "filled" or (
            original_quantity > Decimal("0") and total_quantity >= original_quantity
        ):
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=self.settings.exchange.venue,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=exchange_order_id,
                status=SubmittedOrderStatus.FILLED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_completed_fill",
                remaining_quantity=Decimal("0"),
                filled_quantity=(original_quantity if original_quantity > Decimal("0") else total_quantity),
                average_fill_price=average_fill_price,
                acknowledged_at=acknowledged_at,
                last_fill_at=last_fill_at,
                status_reason_code="reconciliation_completed_fill",
                status_message="Hyperliquid reconciled the submitted order to fully filled.",
                reason_codes=["reconciliation_completed_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=raw_payload,
                observed_at=_utcnow(),
            )

        if remote_status is not None and remote_status.endswith("canceled"):
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=self.settings.exchange.venue,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=exchange_order_id,
                status=SubmittedOrderStatus.CANCELED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_canceled",
                remaining_quantity=remaining_quantity,
                filled_quantity=total_quantity if total_quantity > Decimal("0") else submitted_order.filled_quantity,
                average_fill_price=average_fill_price,
                last_fill_at=last_fill_at,
                acknowledged_at=acknowledged_at,
                status_reason_code="reconciliation_canceled",
                status_message=(
                    "Hyperliquid reports the submitted order as canceled after partial execution."
                    if total_quantity > Decimal("0")
                    else "Hyperliquid reports the submitted order as canceled."
                ),
                reason_codes=["reconciliation_canceled"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=raw_payload,
                observed_at=_utcnow(),
            )

        if remote_status is not None and remote_status.endswith("rejected"):
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=self.settings.exchange.venue,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=exchange_order_id,
                status=SubmittedOrderStatus.REJECTED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_rejected",
                remaining_quantity=remaining_quantity,
                filled_quantity=total_quantity if total_quantity > Decimal("0") else submitted_order.filled_quantity,
                average_fill_price=average_fill_price,
                last_fill_at=last_fill_at,
                acknowledged_at=acknowledged_at,
                status_reason_code="venue_rejected",
                status_message=f"Hyperliquid reports the submitted order as {remote_status}.",
                reason_codes=["venue_rejected"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=raw_payload,
                observed_at=_utcnow(),
            )

        if remote_status in {"open", "triggered"} or raw_order is not None:
            if total_quantity > Decimal("0"):
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=self.settings.exchange.venue,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    exchange_order_id=exchange_order_id,
                    status=SubmittedOrderStatus.PARTIALLY_FILLED,
                    reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                    event_type="reconciliation_partial_fill",
                    remaining_quantity=remaining_quantity,
                    filled_quantity=total_quantity,
                    average_fill_price=average_fill_price,
                    acknowledged_at=acknowledged_at,
                    last_fill_at=last_fill_at,
                    status_reason_code="reconciliation_partial_fill",
                    status_message=(
                        "Hyperliquid still reports the order as working, and fill evidence confirms a partial fill."
                    ),
                    reason_codes=["reconciliation_partial_fill"],
                    cancelable_in_principle=True,
                    amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                    raw_payload=raw_payload,
                    observed_at=_utcnow(),
                )
            if submitted_order.status in {
                SubmittedOrderStatus.CANCEL_REQUESTED,
                SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            }:
                return SubmittedOrderLifecycleUpdate(
                    submitted_order_id=submitted_order.submitted_order_id,
                    venue=self.settings.exchange.venue,
                    venue_account_ref_id=submitted_order.venue_account_ref_id,
                    exchange_order_id=exchange_order_id,
                    status=SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
                    reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                    event_type="reconciliation_cancel_pending",
                    remaining_quantity=remaining_quantity,
                    acknowledged_at=acknowledged_at,
                    status_reason_code="reconciliation_cancel_pending",
                    status_message="Hyperliquid still reports the submitted order as open after accepting the cancel request.",
                    reason_codes=["reconciliation_cancel_pending"],
                    cancelable_in_principle=False,
                    amendable_in_principle=False,
                    raw_payload=raw_payload,
                    observed_at=_utcnow(),
                )
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=self.settings.exchange.venue,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=exchange_order_id,
                status=SubmittedOrderStatus.ACKNOWLEDGED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_open_order",
                remaining_quantity=remaining_quantity,
                acknowledged_at=acknowledged_at,
                status_reason_code="reconciliation_open_order",
                status_message="Hyperliquid still reports the submitted order as open.",
                reason_codes=["reconciliation_open_order"],
                cancelable_in_principle=True,
                amendable_in_principle=submitted_order.order_type == OrderType.LIMIT,
                raw_payload=raw_payload,
                observed_at=_utcnow(),
            )

        if total_quantity > Decimal("0"):
            return SubmittedOrderLifecycleUpdate(
                submitted_order_id=submitted_order.submitted_order_id,
                venue=self.settings.exchange.venue,
                venue_account_ref_id=submitted_order.venue_account_ref_id,
                exchange_order_id=exchange_order_id,
                status=SubmittedOrderStatus.PARTIALLY_FILLED,
                reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
                event_type="reconciliation_partial_fill",
                remaining_quantity=remaining_quantity,
                filled_quantity=total_quantity,
                average_fill_price=average_fill_price,
                acknowledged_at=acknowledged_at,
                last_fill_at=last_fill_at,
                status_reason_code="reconciliation_partial_fill",
                status_message="Hyperliquid fills reconciled the submitted order to a partial fill.",
                reason_codes=["reconciliation_partial_fill"],
                cancelable_in_principle=False,
                amendable_in_principle=False,
                raw_payload=raw_payload,
                observed_at=_utcnow(),
            )

        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.settings.exchange.venue,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=exchange_order_id,
            status=SubmittedOrderStatus.UNKNOWN,
            reconciliation_status=SubmittedOrderReconciliationStatus.RECONCILED,
            event_type="reconciliation_missing_order",
            status_reason_code="reconciliation_missing_order",
            status_message=(
                "Hyperliquid reconciliation did not resolve the order from order-status or fill evidence."
            ),
            reason_codes=["reconciliation_missing_order"],
            cancelable_in_principle=False,
            amendable_in_principle=False,
            raw_payload=raw_payload,
            observed_at=_utcnow(),
        )

    async def _fetch_open_positions_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Position]]:
        context = self._resolve_execution_context(venue_account_ref_id)
        account_address = context.account_address or context.account_identifier
        if account_address:
            try:
                response = await self._info_request(
                    {
                        "type": "clearinghouseState",
                        "user": account_address,
                        "dex": self.settings.exchange.dex_name,
                    }
                )
            except HyperliquidAdapterError:
                response = None
            if isinstance(response, dict):
                observed_at = datetime.fromtimestamp(
                    int(response.get("time", int(_utcnow().timestamp() * 1000))) / 1000,
                    tz=UTC,
                )
                positions: list[Position] = []
                for raw_position in response.get("assetPositions", []):
                    if not isinstance(raw_position, dict):
                        continue
                    position_data = raw_position.get("position")
                    if not isinstance(position_data, dict):
                        continue
                    quantity = _decimal(position_data.get("szi"))
                    if quantity == Decimal("0"):
                        continue
                    raw_coin = str(position_data.get("coin") or "")
                    symbol = await self.normalize_perp_symbol(raw_coin)
                    symbol_model = (
                        self._lookup_symbol_model_by_exchange_symbol(raw_coin)
                        or self._lookup_symbol_model(
                            instrument_key=None,
                            instrument_ref_id=None,
                            symbol=symbol,
                        )
                    )
                    instrument_ref_id = symbol_model.instrument_ref_id if symbol_model else None
                    venue_value = (
                        self.settings.exchange.venue.value
                        if isinstance(self.settings.exchange.venue, Venue)
                        else str(self.settings.exchange.venue)
                    )
                    positions.append(
                        Position(
                            position_id=(
                                f"hl-pos:{self.settings.app.environment.value}:"
                                f"{account_address}:{symbol}"
                            ),
                            instrument_key=self._instrument_key_for_instrument_ref(instrument_ref_id),
                            instrument_ref_id=instrument_ref_id,
                            venue_account_ref_id=context.venue_account_ref_id,
                            sleeve_id=None,
                            venue=venue_value,
                            account_address=account_address,
                            symbol=symbol,
                            environment=self.settings.app.environment,
                            side=OrderSide.BUY if quantity >= 0 else OrderSide.SELL,
                            status=PositionStatus.OPEN,
                            attribution_status=AttributionStatus.UNASSIGNED,
                            venue_position_id=str(
                                raw_position.get("type") or position_data.get("coin") or symbol
                            ),
                            quantity=abs(quantity),
                            avg_entry_price=_decimal(position_data.get("entryPx")),
                            mark_price=_position_mark_price(position_data),
                            unrealized_pnl=_decimal(position_data.get("unrealizedPnl")),
                            opened_at=observed_at,
                            closed_at=None,
                        )
                    )
                return ("venue_query", positions)

        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        scoped_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        with self._session_factory() as session:
            query = select(PositionModel).where(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.venue == self.settings.exchange.venue,
                PositionModel.status == PositionStatus.OPEN,
            )
            if scoped_account_ref is not None:
                query = query.where(PositionModel.venue_account_ref_id == scoped_account_ref)
            elif scoped_address is not None:
                query = query.where(PositionModel.account_address == scoped_address)
            models = session.scalars(query.order_by(PositionModel.updated_at.desc())).all()
        return ("persistence", [_position_from_model(model) for model in models])

    async def fetch_open_positions_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Position]]:
        return await self._fetch_open_positions_with_source(
            venue_account_ref_id=venue_account_ref_id
        )

    async def fetch_open_positions(self, venue_account_ref_id: str | None = None) -> Sequence[Position]:
        _, positions = await self.fetch_open_positions_with_source(
            venue_account_ref_id=venue_account_ref_id
        )
        return positions

    async def _fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]:
        execution_context = self._resolve_execution_context(venue_account_ref_id)
        account_address = execution_context.account_address or execution_context.account_identifier
        if not account_address:
            context = await self.runtime_context_service.ensure_active_context()
            focused_binding = self._focused_binding(context)
            account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            return await ReadOnlyVenueAdapter._fetch_recent_fills_with_source(
                self,
                limit=limit,
                venue_account_ref_id=venue_account_ref_id,
            )
        fills = await self._info_request(
            {
                "type": "userFills",
                "user": account_address,
                "aggregateByTime": False,
            }
        )
        if not isinstance(fills, list):
            return ("venue_query", [])
        result: list[Fill] = []
        for raw_fill in fills[:limit]:
            if not isinstance(raw_fill, dict):
                continue
            exchange_symbol = str(raw_fill.get("coin") or "").upper()
            symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
            instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
            instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
            symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol
            observed_ms = raw_fill.get("time")
            filled_at = (
                datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
                if observed_ms not in (None, "", 0, "0")
                else _utcnow()
            )
            order_id = raw_fill.get("oid")
            result.append(
                Fill(
                    fill_id=f"fill-hyperliquid-{raw_fill.get('tid') or raw_fill.get('hash') or order_id or filled_at.timestamp()}",
                    instrument_key=instrument_key,
                    instrument_ref_id=instrument_ref_id,
                    venue_account_ref_id=execution_context.venue_account_ref_id,
                    venue=Venue.HYPERLIQUID.value,
                    account_address=account_address,
                    submitted_order_id=str(order_id) if order_id not in (None, "") else "",
                    exchange_order_id=str(order_id) if order_id not in (None, "") else None,
                    symbol=symbol,
                    price=_decimal(raw_fill.get("px"), "0"),
                    quantity=abs(_decimal(raw_fill.get("sz"), "0")),
                    fee=abs(_decimal(raw_fill.get("fee"), "0")),
                    filled_at=filled_at,
                )
            )
        return ("venue_query", result)

    async def fetch_recent_fills(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[Fill]:
        _, fills = await self.fetch_recent_fills_with_source(
            limit=limit,
            venue_account_ref_id=venue_account_ref_id,
        )
        return fills

    async def fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]:
        return await self._fetch_recent_fills_with_source(
            limit=limit,
            venue_account_ref_id=venue_account_ref_id,
        )

    async def _fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]:
        execution_context = self._resolve_execution_context(venue_account_ref_id)
        account_address = execution_context.account_address or execution_context.account_identifier
        if not account_address:
            context = await self.runtime_context_service.ensure_active_context()
            focused_binding = self._focused_binding(context)
            account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            return await ReadOnlyVenueAdapter._fetch_open_orders_with_source(
                self,
                venue_account_ref_id=venue_account_ref_id,
            )
        payload = await self._info_request(
            {
                "type": "frontendOpenOrders",
                "user": account_address,
                "dex": self.settings.exchange.dex_name,
            }
        )
        if not isinstance(payload, list):
            return ("venue_query", [])
        return (
            "venue_query",
            [
                self._open_order_from_payload(payload=item, account_address=account_address, execution_context=execution_context)
                for item in payload
                if isinstance(item, dict)
            ],
        )

    async def fetch_open_orders(
        self,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[VenuePrivateOpenOrder]:
        _, orders = await self.fetch_open_orders_with_source(
            venue_account_ref_id=venue_account_ref_id
        )
        return orders

    async def fetch_open_orders_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[VenuePrivateOpenOrder]]:
        return await self._fetch_open_orders_with_source(
            venue_account_ref_id=venue_account_ref_id
        )

    def _open_order_from_payload(
        self,
        *,
        payload: dict[str, Any],
        account_address: str,
        execution_context: VenueAccountExecutionContext,
    ) -> VenuePrivateOpenOrder:
        exchange_symbol = str(payload.get("coin") or "").upper()
        symbol_model = self._lookup_symbol_model_by_exchange_symbol(exchange_symbol)
        instrument_ref_id = symbol_model.instrument_ref_id if symbol_model is not None else None
        instrument_key = self._instrument_key_for_instrument_ref(instrument_ref_id)
        symbol = symbol_model.symbol if symbol_model is not None else exchange_symbol
        original_quantity = _decimal(payload.get("origSz"), payload.get("sz") or "0")
        remaining_quantity = _decimal(payload.get("sz"), str(original_quantity))
        filled_quantity = max(original_quantity - remaining_quantity, Decimal("0"))
        average_fill_price = _decimal(payload.get("avgPx"), "0")
        average_fill_price_value = average_fill_price if average_fill_price > Decimal("0") else None
        observed_ms = payload.get("timestamp") or payload.get("time")
        observed_at = (
            datetime.fromtimestamp(int(observed_ms) / 1000, tz=UTC)
            if observed_ms not in (None, "", 0, "0")
            else _utcnow()
        )
        order_type_raw = str(payload.get("orderType") or payload.get("order_type") or "limit").lower()
        order_type = OrderType.STOP if "trigger" in order_type_raw or "stop" in order_type_raw else OrderType.LIMIT
        client_order_id = str(payload.get("cloid")) if payload.get("cloid") not in (None, "") else None
        exchange_order_id = str(payload.get("oid")) if payload.get("oid") not in (None, "") else None
        linked_submitted_order_id, linked_order_intent_id = ReadOnlyVenueAdapter._linked_submitted_order_identity(
            self,
            venue_account_ref_id=execution_context.venue_account_ref_id,
            account_address=account_address,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
        )
        status = (
            SubmittedOrderStatus.PARTIALLY_FILLED
            if filled_quantity > Decimal("0")
            else SubmittedOrderStatus.ACKNOWLEDGED
        )
        return VenuePrivateOpenOrder(
            venue=Venue.HYPERLIQUID.value,
            venue_account_ref_id=execution_context.venue_account_ref_id,
            account_address=account_address,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
            exchange_symbol=exchange_symbol or None,
            status=status,
            observed_at=observed_at,
            side=OrderSide.BUY if str(payload.get("side", "B")).upper() in {"B", "BUY"} else OrderSide.SELL,
            order_type=order_type,
            limit_price=(
                _decimal(payload.get("limitPx"), "0")
                if payload.get("limitPx") not in (None, "", "0", 0)
                else None
            ),
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price_value,
            last_fill_at=observed_at if filled_quantity > Decimal("0") else None,
            status_reason_code=(
                "reconciliation_partial_fill"
                if status == SubmittedOrderStatus.PARTIALLY_FILLED
                else "reconciliation_open_order"
            ),
            status_message="Hyperliquid direct private open-order query returned a working order snapshot.",
            reason_codes=(
                ["reconciliation_partial_fill"]
                if status == SubmittedOrderStatus.PARTIALLY_FILLED
                else ["reconciliation_open_order"]
            ),
            cancelable_in_principle=True,
            amendable_in_principle=order_type == OrderType.LIMIT,
            reduce_only=bool(payload.get("reduceOnly", False)),
            linked_submitted_order_id=linked_submitted_order_id,
            linked_order_intent_id=linked_order_intent_id,
            raw_payload=dict(payload),
        )

    async def fetch_retry_private_fill_evidence(
        self,
        submitted_order: SubmittedOrder,
        *,
        limit: int = 100,
    ) -> SubmittedOrderPrivateFillEvidence:
        source, fills = await self.fetch_recent_fills_with_source(
            limit=limit,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
        )
        if source != "venue_query":
            return SubmittedOrderPrivateFillEvidence(
                source=source,
                evidence_scope="unavailable",
                fills=[],
                message="No direct private fill query was available.",
            )
        matched = [
            item
            for item in fills
            if submitted_order.exchange_order_id is not None
            and item.exchange_order_id == submitted_order.exchange_order_id
        ]
        return SubmittedOrderPrivateFillEvidence(
            source=source,
            evidence_scope="order_scoped" if submitted_order.exchange_order_id is not None else "unavailable",
            fills=list(matched),
            message=(
                (
                    "Private fill evidence was matched by exchange order id."
                    if matched
                    else "Private fill query was filtered by exchange order id; no matching fills were returned."
                )
                if submitted_order.exchange_order_id is not None
                else "No exchange order id was available for submitted-order-scoped fill matching."
            ),
        )

    async def sync_universe(self, policy: UniversePolicy) -> Sequence[HyperliquidUniverseAsset]:
        response = await self._info_request({"type": "meta", "dex": self.settings.exchange.dex_name})
        universe = response.get("universe", [])
        assets: list[HyperliquidUniverseAsset] = []
        with self._session_factory() as session:
            for asset_id, raw_asset in enumerate(universe):
                exchange_symbol = str(raw_asset["name"]).upper()
                is_builder_deployed = _classify_builder_deployed_asset(dict(raw_asset))
                if is_builder_deployed and not policy.include_builder_deployed_in_catalog:
                    continue
                canonical_symbol = await self.normalize_perp_symbol(exchange_symbol)
                instrument_key = _build_instrument_key(
                    market_type=MarketType.PERPETUAL,
                    product_type=ProductType.LINEAR,
                    base_asset=canonical_symbol,
                    quote_asset="USDC",
                    settlement_asset="USDC",
                )
                asset = HyperliquidUniverseAsset(
                    venue=self.settings.exchange.venue,
                    canonical_symbol=canonical_symbol,
                    exchange_symbol=exchange_symbol,
                    asset_id=asset_id,
                    base_asset=canonical_symbol,
                    quote_asset="USDC",
                    is_perpetual=True,
                    is_builder_deployed=is_builder_deployed,
                    raw_metadata=dict(raw_asset),
                )
                assets.append(asset)

                instrument_model = session.scalar(
                    select(InstrumentModel).where(InstrumentModel.instrument_key == instrument_key)
                )
                if instrument_model is None:
                    instrument_model = InstrumentModel(
                        instrument_key=instrument_key,
                        canonical_symbol=canonical_symbol,
                        market_type=MarketType.PERPETUAL,
                        product_type=ProductType.LINEAR,
                        base_asset=canonical_symbol,
                        quote_asset="USDC",
                        settlement_asset="USDC",
                        is_active=True,
                    )
                    session.add(instrument_model)
                    session.flush()
                else:
                    instrument_model.canonical_symbol = canonical_symbol
                    instrument_model.is_active = True

                model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == self.settings.exchange.venue,
                        SymbolModel.symbol == canonical_symbol,
                    )
                )
                is_strategy_eligible = (
                    not is_builder_deployed or policy.allow_builder_deployed_for_strategy
                )
                is_trading_eligible = (
                    not is_builder_deployed or policy.allow_builder_deployed_for_trading
                )
                if model is None:
                    model = SymbolModel(
                        instrument_ref_id=instrument_model.id,
                        venue=self.settings.exchange.venue,
                        symbol=canonical_symbol,
                        exchange_symbol=exchange_symbol,
                        venue_asset_id=str(asset_id),
                        asset_id=asset_id,
                        market_type=MarketType.PERPETUAL,
                        product_type=ProductType.LINEAR,
                        base_asset=canonical_symbol,
                        quote_asset="USDC",
                        settlement_asset="USDC",
                        price_tick_size=_derive_price_tick_size(raw_asset),
                        quantity_step_size=_derive_quantity_step_size(raw_asset),
                        min_order_size=_derive_quantity_step_size(raw_asset),
                        size_decimals=raw_asset.get("szDecimals"),
                        max_leverage=raw_asset.get("maxLeverage"),
                        only_isolated=bool(raw_asset.get("onlyIsolated", False)),
                        is_perpetual=True,
                        is_builder_deployed=is_builder_deployed,
                        is_strategy_eligible=is_strategy_eligible,
                        is_trading_eligible=is_trading_eligible,
                        is_active=True,
                        raw_metadata=dict(raw_asset),
                    )
                    session.add(model)
                else:
                    model.instrument_ref_id = instrument_model.id
                    model.exchange_symbol = exchange_symbol
                    model.venue_asset_id = str(asset_id)
                    model.asset_id = asset_id
                    model.market_type = MarketType.PERPETUAL
                    model.product_type = ProductType.LINEAR
                    model.settlement_asset = "USDC"
                    model.price_tick_size = _derive_price_tick_size(raw_asset)
                    model.quantity_step_size = _derive_quantity_step_size(raw_asset)
                    model.min_order_size = _derive_quantity_step_size(raw_asset)
                    model.size_decimals = raw_asset.get("szDecimals")
                    model.max_leverage = raw_asset.get("maxLeverage")
                    model.only_isolated = bool(raw_asset.get("onlyIsolated", False))
                    model.is_builder_deployed = is_builder_deployed
                    model.is_strategy_eligible = is_strategy_eligible
                    model.is_trading_eligible = is_trading_eligible
                    model.raw_metadata = dict(raw_asset)
                    model.is_active = True
            session.commit()
        self._last_success_at = _utcnow()
        return assets

    async def get_exchange_status(self) -> ExchangeStatus:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        execution_context = self._resolve_execution_context(
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        credentials = self._resolve_credentials(execution_context)
        state = self._read_control_state(STATE_KEY_LAST_EXCHANGE_SYNC) or {}
        return ExchangeStatus(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            connected=bool(state.get("connected", self._last_success_at is not None)),
            api_base_url=self._api_base_url,
            websocket_base_url=self._ws_base_url,
            can_sign_orders=bool(execution_context.account_address and credentials.signing_private_key),
            wallet_address_configured=bool(execution_context.account_address),
            account_identifier_configured=bool(execution_context.account_identifier),
            credentials_configured=credentials.is_resolved and credentials.has_auth_material,
            read_only_mode=self.settings.hyperliquid_read_only_mode,
            dry_run_mode=self.settings.hyperliquid_dry_run_mode,
            submission_enabled=self.settings.hyperliquid_submission_enabled,
            support_level=self.support_level,
            adapter_supports_order_submission=self.adapter_supports_order_submission,
            adapter_supports_order_cancel=self.adapter_supports_order_cancel,
            adapter_supports_order_amend=self.adapter_supports_order_amend,
            adapter_supports_user_streams=self.adapter_supports_user_streams,
            submission_authorized=self.settings.hyperliquid_submission_authorized,
            live_submission_phase_enabled=self.settings.execution.live_submission_phase_enabled,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        return None

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None:
        return None

    async def get_account_connectivity(self) -> VenueAccountConnectivity:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        execution_context = self._resolve_execution_context(
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        credentials = self._resolve_credentials(execution_context)
        return VenueAccountConnectivity(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            support_level=self.support_level,
            account_model="wallet_address",
            account_identifier=execution_context.account_identifier,
            account_label=execution_context.account_label or None,
            subaccount_label=None,
            credentials_ref=execution_context.credentials_ref,
            account_identifier_configured=bool(execution_context.account_identifier),
            credentials_configured=credentials.is_resolved and credentials.has_auth_material,
            read_only_mode=self.settings.hyperliquid_read_only_mode,
            dry_run_mode=self.settings.hyperliquid_dry_run_mode,
            submission_enabled=self.settings.hyperliquid_submission_enabled,
            submission_authorized=bool(
                self.settings.hyperliquid_submission_authorized
                and credentials.is_resolved
                and credentials.signing_private_key
            ),
            private_account_sync_enabled=bool(execution_context.account_address),
            account_snapshot_available=(
                await self._read_account_snapshot_for_account(execution_context.venue_account_ref_id)
            )
            is not None,
            open_orders_query_available=self.supports_open_orders_query,
            open_positions_query_available=self.supports_open_positions_query,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
        )

    async def get_private_state_summary(self) -> VenuePrivateStateSummary:
        connectivity = await self.get_account_connectivity()
        snapshot = await self.read_account_snapshot()
        open_orders_source, open_orders = await self.fetch_open_orders_with_source()
        recent_fills_source, recent_fills = await self.fetch_recent_fills_with_source()
        open_positions_source, open_positions = await self.fetch_open_positions_with_source()
        return VenuePrivateStateSummary(
            venue=self.settings.exchange.venue,
            support_level=self.support_level,
            account_model=connectivity.account_model,
            account_identifier=connectivity.account_identifier,
            read_only_mode=connectivity.read_only_mode,
            dry_run_mode=connectivity.dry_run_mode,
            private_account_sync_enabled=connectivity.private_account_sync_enabled,
            account_snapshot_available=snapshot is not None,
            balances_visible=snapshot is not None,
            open_orders_query_available=open_orders_source != "unavailable",
            open_orders_count=len(open_orders) if open_orders_source != "unavailable" else 0,
            open_orders_source=open_orders_source,
            open_positions_query_available=open_positions_source != "unavailable",
            open_positions_count=len(open_positions) if open_positions_source != "unavailable" else 0,
            open_positions_source=open_positions_source,
            recent_fills_query_available=recent_fills_source != "unavailable",
            recent_fills_count=len(recent_fills),
            recent_fills_source=recent_fills_source,
            equity=snapshot.equity if snapshot is not None else None,
            available_balance=snapshot.available_balance if snapshot is not None else None,
            last_success_at=connectivity.last_success_at,
            last_error=connectivity.last_error,
            adapter_supports_user_streams=self.adapter_supports_user_streams,
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def get_order_constraints(
        self,
        *,
        instrument_key: str | None = None,
        instrument_ref_id: str | None = None,
        symbol: str | None = None,
    ) -> VenueOrderConstraints | None:
        symbol_model = self._lookup_symbol_model(
            instrument_key=instrument_key,
            instrument_ref_id=instrument_ref_id,
            symbol=symbol,
        )
        capabilities = await self.get_venue_capabilities()
        if symbol_model is None:
            return None
        instrument_key_value = None
        if symbol_model.instrument_ref_id is not None:
            with self._session_factory() as session:
                instrument_key_value = session.scalar(
                    select(InstrumentModel.instrument_key).where(
                        InstrumentModel.id == symbol_model.instrument_ref_id
                    )
                )
        return VenueOrderConstraints(
            venue=self.settings.exchange.venue,
            support_level=self.support_level,
            instrument_key=instrument_key_value,
            instrument_ref_id=symbol_model.instrument_ref_id,
            symbol=symbol_model.symbol,
            exchange_symbol=symbol_model.exchange_symbol,
            market_type=symbol_model.market_type,
            product_type=symbol_model.product_type,
            price_tick_size=symbol_model.price_tick_size,
            quantity_step_size=symbol_model.quantity_step_size,
            min_order_size=symbol_model.min_order_size,
            supports_order_preview=capabilities.supports_order_preview,
            supports_reduce_only_orders=capabilities.supports_reduce_only_orders,
            supports_client_order_ids=capabilities.supports_client_order_ids,
            supported_order_types=list(capabilities.supported_order_types),
            supported_time_in_force=list(capabilities.supported_time_in_force),
            constraint_metadata_complete=all(
                value is not None and value > Decimal("0")
                for value in (
                    symbol_model.price_tick_size,
                    symbol_model.quantity_step_size,
                    symbol_model.min_order_size,
                )
            ),
            notes=None,
        )

    async def prepare_order_preview(self, intent: OrderIntent) -> PreparedVenueOrder:
        capabilities = await self.get_venue_capabilities()
        execution_context = self._resolve_execution_context(intent.venue_account_ref_id)
        account_model = self._lookup_venue_account(intent.venue_account_ref_id)
        credentials = self._resolve_credentials(execution_context)
        snapshot = await self._read_account_snapshot_for_account(intent.venue_account_ref_id)
        connectivity = VenueAccountConnectivity(
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            support_level=self.support_level,
            account_model="wallet_address",
            account_identifier=execution_context.account_identifier,
            account_label=execution_context.account_label,
            subaccount_label=None,
            credentials_ref=execution_context.credentials_ref,
            account_identifier_configured=bool(execution_context.account_identifier),
            credentials_configured=credentials.is_resolved and credentials.has_auth_material,
            read_only_mode=self.settings.hyperliquid_read_only_mode,
            dry_run_mode=self.settings.hyperliquid_dry_run_mode,
            submission_enabled=self.settings.hyperliquid_submission_enabled,
            submission_authorized=bool(
                self.settings.hyperliquid_submission_authorized
                and credentials.is_resolved
                and credentials.signing_private_key
            ),
            private_account_sync_enabled=bool(execution_context.account_address),
            account_snapshot_available=snapshot is not None,
            open_orders_query_available=self.supports_open_orders_query,
            open_positions_query_available=self.supports_open_positions_query,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
        )
        constraints = await self.get_order_constraints(
            instrument_ref_id=intent.instrument_ref_id,
            instrument_key=intent.instrument_key,
            symbol=intent.symbol,
        )
        reason_codes: list[str] = []
        exchange_symbol = constraints.exchange_symbol if constraints is not None else None
        if self.support_level == VenueSupportLevel.QA_READ_ONLY:
            reason_codes.append("venue_not_execution_preparable")
        if not capabilities.supports_order_preview:
            reason_codes.append("venue_order_preview_unsupported")
        if intent.venue_account_ref_id is None:
            reason_codes.append("missing_account_context")
        elif account_model is None:
            reason_codes.append("venue_account_not_found")
        for code in credentials.reason_codes:
            if code not in reason_codes:
                reason_codes.append(code)
        if constraints is None or exchange_symbol is None:
            reason_codes.append("missing_symbol_mapping")
        else:
            if not constraints.constraint_metadata_complete:
                reason_codes.append("insufficient_constraint_metadata")
            if intent.order_type not in constraints.supported_order_types:
                reason_codes.append("unsupported_order_type")
            if intent.reduce_only and not constraints.supports_reduce_only_orders:
                reason_codes.append("reduce_only_not_supported")
            if intent.quantity <= Decimal("0"):
                reason_codes.append("invalid_quantity")
            elif constraints.min_order_size is not None and intent.quantity < constraints.min_order_size:
                reason_codes.append("below_min_order_size")
            if (
                constraints.quantity_step_size is not None
                and constraints.quantity_step_size > Decimal("0")
                and intent.quantity > Decimal("0")
                and not _conforms_to_increment(intent.quantity, constraints.quantity_step_size)
            ):
                reason_codes.append("invalid_quantity_step")
            if intent.order_type == OrderType.LIMIT:
                if intent.limit_price is None:
                    reason_codes.append("limit_price_required")
                elif (
                    constraints.price_tick_size is not None
                    and constraints.price_tick_size > Decimal("0")
                    and not _conforms_to_increment(intent.limit_price, constraints.price_tick_size)
                ):
                    reason_codes.append("invalid_price_tick")
        time_in_force = self._default_time_in_force(intent.order_type)
        if time_in_force is not None and time_in_force not in capabilities.supported_time_in_force:
            reason_codes.append("unsupported_time_in_force")
        client_order_id = self._hyperliquid_cloid(intent)
        payload = None
        if not reason_codes and constraints is not None and exchange_symbol is not None:
            payload = self._build_order_preview_payload(
                intent=intent,
                exchange_symbol=exchange_symbol,
                time_in_force=time_in_force,
                client_order_id=client_order_id,
            )
        return PreparedVenueOrder(
            intent_id=intent.intent_id,
            desired_trade_key=intent.desired_trade_key,
            binding_key=intent.binding_key,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=self.settings.exchange.venue,
            support_level=self.support_level,
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            symbol=intent.symbol,
            exchange_symbol=exchange_symbol,
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            limit_price=intent.limit_price,
            reduce_only=intent.reduce_only,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            preview_status=(
                VenueOrderPreviewStatus.PREPARABLE
                if not reason_codes
                else VenueOrderPreviewStatus.REJECTED
            ),
            reason_codes=reason_codes,
            payload=payload,
            constraints=constraints,
            venue_capabilities=capabilities,
            account_connectivity=connectivity,
            prepared_at=_utcnow(),
        )

    async def read_account_snapshot(self) -> ExchangeAccountSnapshot | None:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        return await self._read_account_snapshot_for_account(scoped_account_ref)

    async def _read_account_snapshot_for_account(
        self,
        venue_account_ref_id: str | None,
    ) -> ExchangeAccountSnapshot | None:
        with self._session_factory() as session:
            query = select(ExchangeAccountSnapshotModel).where(
                ExchangeAccountSnapshotModel.environment == self.settings.app.environment,
                ExchangeAccountSnapshotModel.venue == self.settings.exchange.venue,
            )
            if venue_account_ref_id is not None:
                query = query.where(ExchangeAccountSnapshotModel.venue_account_ref_id == venue_account_ref_id)
            model = session.scalar(query.order_by(ExchangeAccountSnapshotModel.observed_at.desc()))
        if model is None:
            return None
        return ExchangeAccountSnapshot(
            venue_account_ref_id=model.venue_account_ref_id,
            venue=model.venue,
            environment=model.environment,
            account_address=model.account_address,
            equity=model.equity,
            available_balance=model.available_balance,
            margin_used=model.margin_used,
            unrealized_pnl=model.unrealized_pnl,
            total_position_notional=model.total_position_notional,
            observed_at=model.observed_at,
        )

    def _default_time_in_force(self, order_type: OrderType) -> str | None:
        if order_type == OrderType.MARKET:
            return "ioc"
        return "gtc"

    def _lookup_symbol_model(
        self,
        *,
        instrument_key: str | None,
        instrument_ref_id: str | None,
        symbol: str | None,
    ) -> SymbolModel | None:
        with self._session_factory() as session:
            query = select(SymbolModel).where(
                SymbolModel.venue == self.settings.exchange.venue,
                SymbolModel.is_active.is_(True),
            )
            if instrument_ref_id is not None:
                query = query.where(SymbolModel.instrument_ref_id == instrument_ref_id)
                return session.scalar(query.order_by(SymbolModel.exchange_symbol.asc()))
            if instrument_key is not None:
                query = query.join(
                    InstrumentModel,
                    InstrumentModel.id == SymbolModel.instrument_ref_id,
                ).where(InstrumentModel.instrument_key == instrument_key)
                return session.scalar(query.order_by(SymbolModel.exchange_symbol.asc()))
            if symbol is None:
                return None
            models = session.scalars(
                query.where(SymbolModel.symbol == symbol.upper()).order_by(SymbolModel.exchange_symbol.asc())
            ).all()
            if len(models) != 1:
                return None
            return models[0]

    def _lookup_symbol_model_by_exchange_symbol(self, exchange_symbol: str | None) -> SymbolModel | None:
        if exchange_symbol in (None, ""):
            return None
        with self._session_factory() as session:
            return session.scalar(
                select(SymbolModel).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.exchange_symbol == str(exchange_symbol),
                    SymbolModel.is_active.is_(True),
                )
            )

    def _instrument_key_for_instrument_ref(self, instrument_ref_id: str | None) -> str | None:
        if instrument_ref_id is None:
            return None
        with self._session_factory() as session:
            return session.scalar(
                select(InstrumentModel.instrument_key).where(InstrumentModel.id == instrument_ref_id)
            )

    def _lookup_venue_account(self, venue_account_ref_id: str | None) -> VenueAccountModel | None:
        if venue_account_ref_id is None:
            return None
        with self._session_factory() as session:
            model = session.get(VenueAccountModel, venue_account_ref_id)
        if model is None:
            return None
        if model.venue != self.integration.venue.value:
            return None
        if model.environment != self.settings.app.environment:
            return None
        return model

    @staticmethod
    def _client_order_id(intent: OrderIntent) -> str:
        digest = hashlib.sha256(intent.intent_id.encode("utf-8")).hexdigest()[:20]
        return f"mf-{digest}"

    def _build_order_preview_payload(
        self,
        *,
        intent: OrderIntent,
        exchange_symbol: str,
        time_in_force: str | None,
        client_order_id: str | None,
    ) -> dict[str, object]:
        symbol_model = self._lookup_symbol_model(
            instrument_ref_id=intent.instrument_ref_id,
            instrument_key=intent.instrument_key,
            symbol=intent.symbol,
        )
        if symbol_model is None or symbol_model.asset_id is None:
            raise HyperliquidAdapterError(
                "Hyperliquid order preview requires a mapped asset id.",
                reason_codes=["missing_symbol_mapping"],
            )
        limit_price = intent.limit_price
        tif = "Gtc"
        if intent.order_type == OrderType.MARKET:
            limit_price = self._market_order_price(symbol_model, is_buy=intent.side == OrderSide.BUY)
            tif = "Ioc"
        elif time_in_force is not None:
            tif_map = {"gtc": "Gtc", "ioc": "Ioc", "alo": "Alo"}
            tif = tif_map.get(time_in_force.lower(), "Gtc")
        order_wire: dict[str, object] = {
            "a": int(symbol_model.asset_id),
            "b": intent.side == OrderSide.BUY,
            "p": float_to_wire(limit_price or Decimal("0")),
            "s": float_to_wire(intent.quantity),
            "r": intent.reduce_only,
            "t": {"limit": {"tif": tif}},
        }
        if client_order_id is not None:
            order_wire["c"] = client_order_id
        return {
            "endpoint": "/exchange",
            "action": {
                "type": "order",
                "orders": [order_wire],
                "grouping": "na",
            },
        }

    def _asset_id_for_submitted_order(self, submitted_order: SubmittedOrder) -> int | None:
        symbol_model = self._lookup_symbol_model(
            instrument_ref_id=submitted_order.instrument_ref_id,
            instrument_key=submitted_order.instrument_key,
            symbol=submitted_order.symbol,
        )
        if symbol_model is None or symbol_model.asset_id is None:
            return None
        return int(symbol_model.asset_id)

    def _hyperliquid_modify_order_wire(
        self,
        *,
        submitted_order: SubmittedOrder,
        asset_id: int,
        new_quantity: Decimal | None,
        new_limit_price: Decimal | None,
    ) -> dict[str, object]:
        quantity = new_quantity if new_quantity is not None else submitted_order.original_quantity
        price = new_limit_price if new_limit_price is not None else submitted_order.limit_price
        if quantity is None or price is None:
            raise HyperliquidAdapterError(
                "Hyperliquid amendment requires a concrete quantity and limit price.",
                reason_codes=["amend_missing_order_shape"],
            )
        order_wire: dict[str, object] = {
            "a": int(asset_id),
            "b": submitted_order.side == OrderSide.BUY,
            "p": float_to_wire(price),
            "s": float_to_wire(quantity),
            "r": submitted_order.reduce_only,
            "t": {"limit": {"tif": "Gtc"}},
        }
        if submitted_order.client_order_id is not None:
            order_wire["c"] = submitted_order.client_order_id
        return order_wire

    def _signed_exchange_payload(
        self,
        *,
        action: dict[str, Any],
        context: VenueAccountExecutionContext,
        signing_private_key: str,
    ) -> dict[str, Any]:
        nonce = int(_utcnow().timestamp() * 1000)
        signer = signer_address(signing_private_key)
        vault_address = None
        if context.account_address and signer != context.account_address.lower():
            vault_address = context.account_address.lower()
        try:
            signature = sign_l1_action(
                private_key=signing_private_key,
                action=action,
                vault_address=vault_address,
                nonce=nonce,
                expires_after=None,
                is_mainnet=not self.settings.exchange.use_testnet,
            )
        except Exception as exc:  # noqa: BLE001
            raise HyperliquidAdapterError(
                "Hyperliquid could not construct an exchange signature for the targeted account.",
                reason_codes=["auth_signing_failed"],
            ) from exc
        return {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "vaultAddress": vault_address,
            "expiresAfter": None,
        }

    @staticmethod
    def _hyperliquid_action_succeeded(response: Any) -> bool:
        if not isinstance(response, dict):
            return False
        if response.get("status") != "ok":
            return False
        inner = response.get("response")
        if not isinstance(inner, dict):
            return True
        data = inner.get("data")
        if isinstance(data, dict) and data.get("statuses"):
            statuses = data.get("statuses") or []
            return all(isinstance(item, dict) and "error" not in item for item in statuses)
        if isinstance(data, dict) and data.get("status") is not None:
            return str(data.get("status")).lower() in {"ok", "success"}
        return "error" not in inner

    async def normalize_perp_symbol(self, raw_symbol: str) -> str:
        """Hyperliquid perp normalization only.

        This method intentionally remains venue-specific. Do not reuse its rules
        as cross-venue symbol logic.
        """
        symbol = raw_symbol.strip().upper()
        if symbol.endswith("/USDC"):
            symbol = symbol.removesuffix("/USDC")
        if symbol.endswith("-PERP"):
            symbol = symbol.removesuffix("-PERP")
        return symbol

    async def map_asset_id(self, canonical_symbol: str) -> int | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(SymbolModel.asset_id).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == canonical_symbol,
                )
            )
        return int(model) if model is not None else None

    async def get_wallet_context(self) -> HyperliquidWalletContext:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_address = (
            focused_binding.venue_account.account_address if focused_binding is not None else None
        ) or self.settings.exchange.account_address
        if self.settings.app.environment == Environment.LIVE and not (
            self.settings.exchange.api_key or self.settings.exchange.allow_live_mode_without_api_key
        ):
            raise HyperliquidAdapterError(
                "Live environment requires exchange credentials or explicit override."
            )
        return HyperliquidWalletContext(
            environment=self.settings.app.environment,
            api_base_url=self._api_base_url,
            websocket_base_url=self._ws_base_url,
            account_address=account_address or "",
            signer_label="api_wallet" if self.settings.exchange.api_key else "read_only",
            can_sign_orders=bool(account_address and self.settings.exchange.api_key),
        )

    async def sync_account_state(self) -> HyperliquidAccountState:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            raise HyperliquidAdapterError("EXCHANGE_ACCOUNT_ADDRESS must be configured.")
        response = await self._info_request(
            {
                "type": "clearinghouseState",
                "user": account_address,
                "dex": self.settings.exchange.dex_name,
            }
        )
        margin_summary = response.get("marginSummary", {})
        asset_positions = response.get("assetPositions", [])
        total_position_notional = sum(
            _decimal(position["position"].get("positionValue")) for position in asset_positions
        )
        observed_at = datetime.fromtimestamp(int(response.get("time", int(_utcnow().timestamp() * 1000))) / 1000, tz=UTC)
        snapshot = HyperliquidAccountState(
            environment=self.settings.app.environment,
            account_address=account_address,
            equity=_decimal(margin_summary.get("accountValue")),
            available_balance=_decimal(response.get("withdrawable")),
            margin_used=_decimal(margin_summary.get("totalMarginUsed")),
            unrealized_pnl=sum(
                _decimal(position["position"].get("unrealizedPnl")) for position in asset_positions
            ),
            observed_at=observed_at,
        )

        with self._session_factory() as session:
            session.add(
                ExchangeAccountSnapshotModel(
                    environment=self.settings.app.environment,
                    venue_account_ref_id=(
                        focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                    ),
                    venue=self.settings.exchange.venue,
                    account_address=account_address,
                    equity=snapshot.equity,
                    available_balance=snapshot.available_balance,
                    margin_used=snapshot.margin_used,
                    unrealized_pnl=snapshot.unrealized_pnl,
                    total_position_notional=total_position_notional,
                    cross_margin_summary=dict(response.get("crossMarginSummary", {})),
                    margin_summary=dict(margin_summary),
                    raw_payload=dict(response),
                    observed_at=observed_at,
                )
            )
            session.commit()

        self._write_control_state(
            "hyperliquid:account_sync",
            {
                "observed_at": observed_at.isoformat(),
                "account_address": account_address,
                "venue_account_key": (
                    focused_binding.venue_account.venue_account_key if focused_binding is not None else None
                ),
            },
        )
        self._last_success_at = _utcnow()
        return snapshot

    async def reconcile_open_orders(self) -> HyperliquidReconciliationSnapshot:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            raise HyperliquidAdapterError("EXCHANGE_ACCOUNT_ADDRESS must be configured.")
        response = await self._info_request(
            {
                "type": "frontendOpenOrders",
                "user": account_address,
                "dex": self.settings.exchange.dex_name,
            }
        )
        order_ids: list[str] = []
        with self._session_factory() as session:
            for raw_order in response:
                exchange_order_id = str(raw_order["oid"])
                symbol = await self.normalize_perp_symbol(raw_order["coin"])
                symbol_model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == self.settings.exchange.venue,
                        SymbolModel.symbol == symbol,
                    )
                )
                model = session.scalar(
                    select(SubmittedOrderModel).where(
                        SubmittedOrderModel.environment == self.settings.app.environment,
                        SubmittedOrderModel.venue == self.settings.exchange.venue,
                        SubmittedOrderModel.exchange_order_id == exchange_order_id,
                    )
                )
                if model is None:
                    model = SubmittedOrderModel(
                        environment=self.settings.app.environment,
                        submitted_order_id=f"hl-order-{exchange_order_id}",
                        intent_id=None,
                        client_order_id=None,
                        venue_account_ref_id=(
                            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                        ),
                        venue=self.settings.exchange.venue,
                        account_address=account_address,
                        instrument_ref_id=symbol_model.instrument_ref_id if symbol_model else None,
                        symbol_id=symbol_model.id if symbol_model else None,
                        symbol=symbol,
                        side=OrderSide.BUY if raw_order.get("side", "B") in {"B", "buy"} else OrderSide.SELL,
                        order_type=_map_order_type(raw_order.get("orderType")),
                        limit_price=_decimal(raw_order.get("limitPx"), "0"),
                        original_quantity=_decimal(raw_order.get("origSz"), "0"),
                        remaining_quantity=_decimal(raw_order.get("sz"), "0"),
                        reduce_only=bool(raw_order.get("reduceOnly", False)),
                        exchange_order_id=exchange_order_id,
                        status=SubmittedOrderStatus.ACKNOWLEDGED,
                        submitted_at=datetime.fromtimestamp(int(raw_order["timestamp"]) / 1000, tz=UTC),
                        acknowledged_at=datetime.fromtimestamp(int(raw_order["timestamp"]) / 1000, tz=UTC),
                        raw_payload=dict(raw_order),
                    )
                    session.add(model)
                else:
                    model.venue_account_ref_id = (
                        focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                    )
                    model.instrument_ref_id = symbol_model.instrument_ref_id if symbol_model else None
                    model.symbol = symbol
                    model.remaining_quantity = _decimal(raw_order.get("sz"), "0")
                    model.reduce_only = bool(raw_order.get("reduceOnly", False))
                    model.status = SubmittedOrderStatus.ACKNOWLEDGED
                    model.raw_payload = dict(raw_order)
                order_ids.append(model.submitted_order_id)
            session.commit()
        reconciled_at = _utcnow()
        self._write_control_state(
            "hyperliquid:open_orders_cursor",
            {
                "reconciled_at": reconciled_at.isoformat(),
                "count": len(order_ids),
                "venue_account_key": (
                    focused_binding.venue_account.venue_account_key if focused_binding is not None else None
                ),
            },
        )
        return HyperliquidReconciliationSnapshot(
            environment=self.settings.app.environment,
            venue=self.settings.exchange.venue,
            open_order_ids=order_ids,
            reconciled_at=reconciled_at,
            cursor=reconciled_at.isoformat(),
        )

    async def reconcile_fills(self, limit: int = 100) -> HyperliquidReconciliationSnapshot:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            raise HyperliquidAdapterError("EXCHANGE_ACCOUNT_ADDRESS must be configured.")
        response = await self._info_request(
            {
                "type": "userFills",
                "user": account_address,
                "aggregateByTime": False,
            }
        )
        fill_ids: list[str] = []
        with self._session_factory() as session:
            for raw_fill in response[:limit]:
                fill_id = str(raw_fill.get("tid") or f"{raw_fill.get('hash', 'fill')}:{raw_fill.get('oid')}")
                symbol = await self.normalize_perp_symbol(raw_fill["coin"])
                symbol_model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == self.settings.exchange.venue,
                        SymbolModel.symbol == symbol,
                    )
                )
                model = session.scalar(
                    select(FillModel).where(
                        FillModel.environment == self.settings.app.environment,
                        FillModel.venue == self.settings.exchange.venue,
                        FillModel.fill_id == fill_id,
                    )
                )
                if model is None:
                    model = FillModel(
                        environment=self.settings.app.environment,
                        fill_id=fill_id,
                        venue_fill_id=str(raw_fill.get("tid")) if raw_fill.get("tid") is not None else None,
                        venue_account_ref_id=(
                            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                        ),
                        venue=self.settings.exchange.venue,
                        account_address=account_address,
                        submitted_order_id=f"hl-order-{raw_fill.get('oid')}",
                        exchange_order_id=str(raw_fill.get("oid")) if raw_fill.get("oid") is not None else None,
                        position_id=(
                            f"hl-pos:{self.settings.app.environment.value}:{account_address}:{symbol}"
                        ),
                        instrument_ref_id=symbol_model.instrument_ref_id if symbol_model else None,
                        symbol_id=symbol_model.id if symbol_model else None,
                        symbol=symbol,
                        side=OrderSide.BUY if raw_fill.get("side") == "B" else OrderSide.SELL,
                        price=_decimal(raw_fill.get("px")),
                        quantity=abs(_decimal(raw_fill.get("sz"))),
                        fee=_decimal(raw_fill.get("fee", "0")),
                        fee_token=raw_fill.get("feeToken"),
                        closed_pnl=_decimal(raw_fill.get("closedPnl", "0")),
                        raw_payload=dict(raw_fill),
                        filled_at=datetime.fromtimestamp(int(raw_fill["time"]) / 1000, tz=UTC),
                    )
                    session.add(model)
                else:
                    model.venue_fill_id = (
                        str(raw_fill.get("tid")) if raw_fill.get("tid") is not None else model.venue_fill_id
                    )
                    model.venue_account_ref_id = (
                        focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                    )
                    model.instrument_ref_id = symbol_model.instrument_ref_id if symbol_model else None
                    model.raw_payload = dict(raw_fill)
                fill_ids.append(fill_id)
            session.commit()
        reconciled_at = _utcnow()
        self._write_control_state(
            "hyperliquid:fills_cursor",
            {
                "reconciled_at": reconciled_at.isoformat(),
                "count": len(fill_ids),
                "venue_account_key": (
                    focused_binding.venue_account.venue_account_key if focused_binding is not None else None
                ),
            },
        )
        return HyperliquidReconciliationSnapshot(
            environment=self.settings.app.environment,
            venue=self.settings.exchange.venue,
            fill_ids=fill_ids,
            reconciled_at=reconciled_at,
            cursor=reconciled_at.isoformat(),
        )

    async def reconcile_positions(self) -> HyperliquidReconciliationSnapshot:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_address = focused_binding.venue_account.account_address if focused_binding is not None else None
        if not account_address:
            raise HyperliquidAdapterError("EXCHANGE_ACCOUNT_ADDRESS must be configured.")
        response = await self._info_request(
            {
                "type": "clearinghouseState",
                "user": account_address,
                "dex": self.settings.exchange.dex_name,
            }
        )
        position_ids: list[str] = []
        observed_at = datetime.fromtimestamp(int(response.get("time", int(_utcnow().timestamp() * 1000))) / 1000, tz=UTC)
        with self._session_factory() as session:
            for raw_position in response.get("assetPositions", []):
                position_data = raw_position["position"]
                symbol = await self.normalize_perp_symbol(position_data["coin"])
                symbol_model = session.scalar(
                    select(SymbolModel).where(
                        SymbolModel.venue == self.settings.exchange.venue,
                        SymbolModel.symbol == symbol,
                    )
                )
                exchange_position_key = str(raw_position.get("type") or position_data.get("coin") or symbol)
                position_id = f"hl-pos:{self.settings.app.environment.value}:{account_address}:{symbol}"
                account_position_key = (
                    f"{self.settings.app.environment.value}:{self.settings.exchange.venue}:"
                    f"{account_address}:{symbol_model.instrument_ref_id if symbol_model else symbol}:one_way"
                )
                quantity = _decimal(position_data.get("szi"))
                model = session.scalar(
                    select(PositionModel).where(
                        PositionModel.environment == self.settings.app.environment,
                        PositionModel.venue == self.settings.exchange.venue,
                        PositionModel.position_id == position_id,
                    )
                )
                status = PositionStatus.OPEN if quantity != 0 else PositionStatus.CLOSED
                side = OrderSide.BUY if quantity >= 0 else OrderSide.SELL
                if model is None:
                    model = PositionModel(
                        environment=self.settings.app.environment,
                        position_id=position_id,
                        exchange_position_key=exchange_position_key,
                        account_position_key=account_position_key,
                        venue_account_ref_id=(
                            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                        ),
                        sleeve_id=None,
                        venue=self.settings.exchange.venue,
                        account_address=account_address,
                        instrument_ref_id=symbol_model.instrument_ref_id if symbol_model else None,
                        symbol_id=symbol_model.id if symbol_model else None,
                        symbol=symbol,
                        side=side,
                        status=status,
                        attribution_status=AttributionStatus.UNASSIGNED,
                        quantity=abs(quantity),
                        avg_entry_price=_decimal(position_data.get("entryPx")),
                        mark_price=_position_mark_price(position_data),
                        unrealized_pnl=_decimal(position_data.get("unrealizedPnl")),
                        position_value=_decimal(position_data.get("positionValue", "0")),
                        margin_used=_decimal(position_data.get("marginUsed", "0")),
                        liquidation_price=_decimal(position_data.get("liquidationPx", "0")),
                        leverage_type=str(position_data.get("leverage", {}).get("type", "")) or None,
                        leverage_value=position_data.get("leverage", {}).get("value"),
                        raw_payload=dict(raw_position),
                        opened_at=observed_at,
                    )
                    session.add(model)
                else:
                    model.exchange_position_key = exchange_position_key
                    model.account_position_key = account_position_key
                    model.venue_account_ref_id = (
                        focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                    )
                    model.instrument_ref_id = symbol_model.instrument_ref_id if symbol_model else None
                    model.status = status
                    model.side = side
                    model.quantity = abs(quantity)
                    model.avg_entry_price = _decimal(position_data.get("entryPx"))
                    model.mark_price = _position_mark_price(position_data)
                    model.unrealized_pnl = _decimal(position_data.get("unrealizedPnl"))
                    model.position_value = _decimal(position_data.get("positionValue", "0"))
                    model.margin_used = _decimal(position_data.get("marginUsed", "0"))
                    model.liquidation_price = _decimal(position_data.get("liquidationPx", "0"))
                    model.leverage_type = str(position_data.get("leverage", {}).get("type", "")) or None
                    model.leverage_value = position_data.get("leverage", {}).get("value")
                    model.raw_payload = dict(raw_position)
                    if status == PositionStatus.CLOSED:
                        model.closed_at = observed_at
                position_ids.append(position_id)
            session.commit()
        self._write_control_state(
            "hyperliquid:positions_cursor",
            {
                "reconciled_at": observed_at.isoformat(),
                "count": len(position_ids),
                "venue_account_key": (
                    focused_binding.venue_account.venue_account_key if focused_binding is not None else None
                ),
            },
        )
        return HyperliquidReconciliationSnapshot(
            environment=self.settings.app.environment,
            venue=self.settings.exchange.venue,
            position_ids=position_ids,
            reconciled_at=observed_at,
            cursor=observed_at.isoformat(),
        )

    async def fetch_candle_snapshot(
        self,
        symbol: str,
        timeframe: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> Sequence[Candle]:
        interval = _timeframe_to_interval(timeframe)
        exchange_symbol = await self._lookup_exchange_symbol(symbol)
        response = await self._info_request(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": exchange_symbol,
                    "interval": interval,
                    "startTime": start_time_ms,
                    "endTime": end_time_ms,
                },
            }
        )
        candles: list[Candle] = []
        for item in response:
            open_time = datetime.fromtimestamp(int(item["t"]) / 1000, tz=UTC)
            close_time = datetime.fromtimestamp(int(item["T"]) / 1000, tz=UTC)
            candles.append(
                Candle(
                    instrument_key=await self._lookup_instrument_key(symbol),
                    instrument_ref_id=await self._lookup_instrument_ref_id(symbol),
                    venue=self.settings.exchange.venue,
                    symbol=symbol,
                    timeframe=Timeframe(interval),
                    open_time=open_time,
                    close_time=close_time,
                    open=_decimal(item["o"]),
                    high=_decimal(item["h"]),
                    low=_decimal(item["l"]),
                    close=_decimal(item["c"]),
                    volume=_decimal(item.get("v", "0")),
                    trade_count=None,
                )
            )
        return candles

    async def switch_environment(self, use_testnet: bool) -> None:
        self.settings.exchange.use_testnet = use_testnet
        self.settings.exchange.api_base_url = TESTNET_API_URL if use_testnet else "https://api.hyperliquid.xyz"
        self.settings.exchange.ws_base_url = TESTNET_WS_URL if use_testnet else "wss://api.hyperliquid.xyz/ws"
        await self.disconnect()

    async def build_candle_subscription(self, symbol: str, timeframe: str) -> dict[str, Any]:
        return {
            "method": "subscribe",
            "subscription": {
                "type": "candle",
                "coin": await self._lookup_exchange_symbol(symbol),
                "interval": _timeframe_to_interval(timeframe),
            },
        }

    async def stream_candles(
        self,
        symbols: Sequence[str],
        timeframes: Sequence[str],
        on_message: Callable[[dict[str, Any]], Awaitable[None]],
        *,
        max_messages: int | None = None,
    ) -> int:
        processed = 0
        async with websockets.connect(self._ws_base_url) as websocket:
            for symbol in symbols:
                for timeframe in timeframes:
                    await websocket.send(json.dumps(await self.build_candle_subscription(symbol, timeframe)))
            while max_messages is None or processed < max_messages:
                raw_message = await websocket.recv()
                payload = json.loads(raw_message)
                await on_message(payload)
                processed += 1
        return processed

    @property
    def _api_base_url(self) -> str:
        if self.settings.exchange.use_testnet and self.settings.exchange.api_base_url == "https://api.hyperliquid.xyz":
            return TESTNET_API_URL
        return self.settings.exchange.api_base_url

    @property
    def _ws_base_url(self) -> str:
        if self.settings.exchange.use_testnet and self.settings.exchange.ws_base_url == "wss://api.hyperliquid.xyz/ws":
            return TESTNET_WS_URL
        return self.settings.exchange.ws_base_url

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self._api_base_url,
                timeout=self.settings.exchange.request_timeout_seconds,
            )
        return self._http_client

    async def _info_request(self, payload: dict[str, Any]) -> Any:
        try:
            if self._transport is not None:
                result = await self._transport(payload)
            else:
                client = await self._client()
                response = await client.post(INFO_PATH, json=payload)
                response.raise_for_status()
                result = response.json()
            self._last_success_at = _utcnow()
            self._last_error = None
            return result
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._logger.error(
                "hyperliquid_info_request_failed",
                payload_type=payload.get("type"),
                environment=self.settings.app.environment.value,
                error=str(exc),
            )
            raise HyperliquidAdapterError(f"Hyperliquid request failed for {payload.get('type')}: {exc}") from exc

    async def _exchange_request(self, payload: dict[str, Any], *, path: str = "/exchange") -> Any:
        try:
            if self._transport is not None:
                result = await self._transport(payload)
            else:
                client = await self._client()
                response = await client.post(path, json=payload)
                response.raise_for_status()
                result = response.json()
            self._last_success_at = _utcnow()
            self._last_error = None
            return result
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._logger.error(
                "hyperliquid_exchange_request_failed",
                path=path,
                environment=self.settings.app.environment.value,
                error=str(exc),
            )
            raise HyperliquidAdapterError(f"Hyperliquid submission failed for {path}: {exc}") from exc

    def _resolve_execution_context(
        self,
        venue_account_ref_id: str | None,
    ) -> VenueAccountExecutionContext:
        model = self._lookup_venue_account(venue_account_ref_id)
        if model is not None:
            return VenueAccountExecutionContext(
                venue_account_ref_id=model.id,
                venue_account_key=model.venue_account_key,
                venue_native_account_id=model.venue_native_account_id,
                account_identifier=model.account_address or model.venue_native_account_id,
                account_address=model.account_address,
                account_label=model.account_label or None,
                subaccount_label=model.subaccount_label or None,
                credentials_ref=model.credentials_ref or self.integration.credentials_ref or None,
                wallet_ref=model.wallet_ref or self.integration.wallet_ref or None,
                raw_metadata=dict(model.raw_metadata or {}),
            )
        return VenueAccountExecutionContext(
            venue_account_ref_id=venue_account_ref_id,
            venue_account_key=None,
            venue_native_account_id=self.integration.account_identifier or None,
            account_identifier=self.integration.account_address or self.integration.account_identifier or None,
            account_address=self.integration.account_address or None,
            account_label=self.integration.account_label or None,
            subaccount_label=self.integration.subaccount_label or None,
            credentials_ref=self.integration.credentials_ref or None,
            wallet_ref=self.integration.wallet_ref or None,
            raw_metadata={},
        )

    def _resolve_credentials(self, context: VenueAccountExecutionContext) -> ResolvedVenueCredentials:
        account_auth = context.raw_metadata.get("auth", {})
        if not isinstance(account_auth, dict):
            account_auth = {}
        normalized_auth = {
            str(key): str(value)
            for key, value in account_auth.items()
            if value not in (None, "")
        }
        reason_codes: list[str] = []
        if not normalized_auth:
            if context.credentials_ref and context.credentials_ref != (self.integration.credentials_ref or None):
                reason_codes.append("credential_reference_unresolved")
            if context.wallet_ref and context.wallet_ref != (self.integration.wallet_ref or None):
                reason_codes.append("wallet_reference_unresolved")
        if normalized_auth:
            source = "venue_account_auth"
            signing_private_key = (
                normalized_auth.get("signing_private_key")
                or normalized_auth.get("wallet_private_key")
                or normalized_auth.get("private_key")
            )
        elif reason_codes:
            source = "unresolved_reference"
            signing_private_key = None
        else:
            source = "integration_defaults"
            signing_private_key = self.integration.signing_private_key or None
        return ResolvedVenueCredentials(
            source=source,
            reason_codes=reason_codes,
            api_key=None,
            api_secret=None,
            api_passphrase=None,
            signing_private_key=signing_private_key,
            jwt_key_name=None,
            jwt_private_key_pem=None,
        )

    @staticmethod
    def _hyperliquid_cloid(intent: OrderIntent) -> str:
        return f"0x{hashlib.sha256(intent.intent_id.encode('utf-8')).hexdigest()[:32]}"

    def _market_order_price(self, symbol_model: SymbolModel, *, is_buy: bool) -> Decimal:
        mids = self._read_control_state("hyperliquid:last_all_mids") or {}
        raw_mid = mids.get(symbol_model.exchange_symbol)
        if raw_mid is None:
            raise HyperliquidAdapterError(
                "Hyperliquid market-style order requires current mid price state.",
                reason_codes=["missing_market_price_context"],
            )
        mid_price = Decimal(str(raw_mid))
        slippage = Decimal("1.05") if is_buy else Decimal("0.95")
        px = mid_price * slippage
        rounded = Decimal(f"{px:.5g}")
        price_decimals = (8 if symbol_model.asset_id and symbol_model.asset_id >= 10000 else 6) - (
            symbol_model.size_decimals or 0
        )
        if price_decimals >= 0:
            quant = Decimal("1").scaleb(-price_decimals)
            return rounded.quantize(quant)
        return rounded

    def _assert_submission_controls(self, context: VenueAccountExecutionContext) -> None:
        if not self.integration.enabled:
            raise HyperliquidAdapterError(
                "Hyperliquid integration is disabled.",
                reason_codes=["venue_integration_disabled"],
            )
        if self.support_level == VenueSupportLevel.QA_READ_ONLY:
            raise HyperliquidAdapterError(
                "Hyperliquid is not execution-preparable.",
                reason_codes=["venue_not_execution_preparable"],
            )
        if not self.settings.hyperliquid_submission_enabled:
            raise HyperliquidAdapterError(
                "Hyperliquid live submission is not enabled.",
                reason_codes=["venue_submission_not_enabled"],
            )
        if self.settings.hyperliquid_read_only_mode:
            raise HyperliquidAdapterError(
                "Hyperliquid is configured in read-only mode.",
                reason_codes=["read_only_mode_enabled"],
            )
        if self.settings.hyperliquid_dry_run_mode or self.settings.execution.dry_run:
            raise HyperliquidAdapterError(
                "Hyperliquid is configured in dry-run mode.",
                reason_codes=["dry_run_only"],
            )
        if not self.settings.hyperliquid_submission_authorized:
            raise HyperliquidAdapterError(
                "Hyperliquid submission is not authorized for the configured account/environment.",
                reason_codes=["account_not_authorized"],
            )
        if not context.account_address:
            raise HyperliquidAdapterError(
                "Hyperliquid submission requires a targeted wallet/account address.",
                reason_codes=["account_identifier_missing"],
            )
        credentials = self._resolve_credentials(context)
        if credentials.reason_codes:
            raise HyperliquidAdapterError(
                "Hyperliquid submission could not resolve targeted signing credentials.",
                reason_codes=list(credentials.reason_codes),
            )
        if not credentials.signing_private_key:
            raise HyperliquidAdapterError(
                "Hyperliquid submission requires targeted signing material.",
                reason_codes=["missing_auth_material"],
            )

    async def _lookup_exchange_symbol(self, symbol: str) -> str:
        with self._session_factory() as session:
            model = session.scalar(
                select(SymbolModel.exchange_symbol).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
        return str(model) if model else symbol

    async def _lookup_instrument_ref_id(self, symbol: str) -> str | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(SymbolModel.instrument_ref_id).where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
        return str(model) if model else None

    async def _lookup_instrument_key(self, symbol: str) -> str | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(InstrumentModel.instrument_key)
                .join(SymbolModel, SymbolModel.instrument_ref_id == InstrumentModel.id)
                .where(
                    SymbolModel.venue == self.settings.exchange.venue,
                    SymbolModel.symbol == symbol,
                )
            )
        return str(model) if model else None

    def _read_control_state(self, state_key: str) -> dict[str, Any] | None:
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(SystemStateModel).where(
                        SystemStateModel.environment == self.settings.app.environment,
                        SystemStateModel.state_key == state_key,
                    )
                )
                return dict(model.state_value) if model else None
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            return None

    def _write_control_state(self, state_key: str, state_value: dict[str, Any]) -> None:
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(SystemStateModel).where(
                        SystemStateModel.environment == self.settings.app.environment,
                        SystemStateModel.state_key == state_key,
                    )
                )
                if model is None:
                    model = SystemStateModel(
                        environment=self.settings.app.environment,
                        state_key=state_key,
                        state_value=state_value,
                    )
                    session.add(model)
                else:
                    model.state_value = state_value
                session.commit()
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)


def _derive_quantity_step_size(raw_asset: dict[str, Any]) -> Decimal:
    sz_decimals = int(raw_asset.get("szDecimals", 0))
    return Decimal("1").scaleb(-sz_decimals)


def _derive_price_tick_size(raw_asset: dict[str, Any]) -> Decimal:
    """Approximate price tick size from Hyperliquid precision rules.

    Hyperliquid price precision is not returned as a simple fixed tick in `meta`.
    This uses the documented decimal precision bound as a conservative lower step.
    """

    sz_decimals = int(raw_asset.get("szDecimals", 0))
    price_decimals = max(0, 6 - sz_decimals)
    return Decimal("1").scaleb(-price_decimals)


def _map_order_type(raw_type: str | None) -> OrderType:
    normalized = (raw_type or "limit").lower()
    if "market" in normalized:
        return OrderType.MARKET
    if "stop" in normalized or "trigger" in normalized:
        return OrderType.STOP
    return OrderType.LIMIT


def _position_from_model(model: PositionModel) -> Position:
    return Position(
        position_id=model.position_id,
        instrument_key=_lookup_instrument_key_from_model(model),
        instrument_ref_id=model.instrument_ref_id,
        venue_account_ref_id=model.venue_account_ref_id,
        sleeve_id=model.sleeve_id,
        venue=model.venue,
        account_address=model.account_address,
        symbol=model.symbol,
        environment=model.environment,
        side=model.side,
        status=model.status,
        attribution_status=model.attribution_status,
        venue_position_id=model.exchange_position_key,
        quantity=model.quantity,
        avg_entry_price=model.avg_entry_price,
        mark_price=model.mark_price,
        unrealized_pnl=model.unrealized_pnl,
        opened_at=model.opened_at,
        closed_at=model.closed_at,
    )


def _fill_from_model(model: FillModel) -> Fill:
    return Fill(
        fill_id=model.fill_id,
        instrument_key=None,
        instrument_ref_id=model.instrument_ref_id,
        venue_account_ref_id=model.venue_account_ref_id,
        venue=model.venue,
        account_address=model.account_address,
        submitted_order_id=model.submitted_order_id,
        exchange_order_id=model.exchange_order_id,
        symbol=model.symbol,
        price=model.price,
        quantity=model.quantity,
        fee=model.fee,
        filled_at=model.filled_at,
    )


def _lookup_instrument_key_from_model(model: PositionModel) -> str | None:
    raw_payload = model.raw_payload or {}
    position_data = raw_payload.get("position")
    if isinstance(position_data, dict):
        coin = position_data.get("coin")
        if coin:
            return str(coin).upper()
    return model.symbol


def _conforms_to_increment(value: Decimal, increment: Decimal) -> bool:
    if increment <= Decimal("0"):
        return False
    normalized = (value / increment).normalize()
    return normalized == normalized.to_integral_value()
