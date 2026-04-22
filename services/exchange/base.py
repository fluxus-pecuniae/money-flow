"""Shared venue adapter base classes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from decimal import Decimal
import base64
import hashlib
import hmac
import json
import urllib.parse
from typing import Any

import httpx
from sqlalchemy import select

from core.config.settings import AppSettings, VenueIntegrationConfig, get_settings
from core.domain.enums import (
    AttributionStatus,
    Environment,
    OrderSide,
    OrderType,
    PositionStatus,
    SubmittedOrderReconciliationStatus,
    SubmittedOrderStatus,
    VenueOrderPreviewStatus,
    VenueSupportLevel,
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
from core.interfaces.services import ExchangeAdapter
from core.logging.setup import get_logger
from db.models import FillModel, InstrumentModel, PositionModel, SubmittedOrderModel, SymbolModel, VenueAccountModel
from db.session import SessionLocal
from services.exchange.common import list_instruments_for_venue, persist_symbol_catalog

TransportCallable = Callable[..., Awaitable[Any]]


class VenueAdapterError(RuntimeError):
    """Raised when a venue adapter request fails or an unsupported action is attempted."""

    def __init__(
        self,
        message: str,
        *,
        reason_codes: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason_codes = list(reason_codes or [])
        self.payload = payload


def utcnow() -> datetime:
    return datetime.now(UTC)


def decimal_or(value: Any, default: str = "0") -> Decimal:
    raw = default if value in (None, "") else str(value)
    return Decimal(raw)


@dataclass(slots=True)
class VenueAccountExecutionContext:
    venue_account_ref_id: str | None
    venue_account_key: str | None
    venue_native_account_id: str | None
    account_identifier: str | None
    account_address: str | None
    account_label: str | None
    subaccount_label: str | None
    credentials_ref: str | None
    wallet_ref: str | None
    raw_metadata: dict[str, Any]


@dataclass(slots=True)
class ResolvedVenueCredentials:
    source: str
    reason_codes: list[str]
    api_key: str | None
    api_secret: str | None
    api_passphrase: str | None
    signing_private_key: str | None
    jwt_key_name: str | None
    jwt_private_key_pem: str | None

    @property
    def is_resolved(self) -> bool:
        return not self.reason_codes

    @property
    def has_auth_material(self) -> bool:
        return bool(
            self.api_key
            or self.api_secret
            or self.api_passphrase
            or self.signing_private_key
            or self.jwt_key_name
            or self.jwt_private_key_pem
        )


class ReadOnlyVenueAdapter(ExchangeAdapter):
    """Base class for venue integrations.

    The class name is preserved for compatibility, but current integrated
    venues may now implement truthful live-submit paths behind explicit
    readiness and environment authorization gates.
    """

    account_model = "account_id"
    support_level = VenueSupportLevel.QA_READ_ONLY
    adapter_supports_order_submission = False
    adapter_supports_order_cancel = False
    adapter_supports_order_amend = False
    adapter_supports_user_streams = False
    retry_requires_fresh_client_order_id = False
    supports_order_preview = False
    supports_account_snapshot = False
    supports_open_orders_query = False
    supports_open_positions_query = False
    supports_recent_fills_query = False
    supports_reduce_only_orders = False
    supports_client_order_ids = False
    supported_order_types: tuple[OrderType, ...] = ()
    supported_time_in_force: tuple[str, ...] = ()
    private_lifecycle_update_mode = "polling"
    open_orders_state_source = "persistence"
    recent_fills_state_source = "persistence"

    def __init__(
        self,
        integration: VenueIntegrationConfig,
        settings: AppSettings | None = None,
        *,
        transport: TransportCallable | None = None,
        session_factory: Callable[[], Any] = SessionLocal,
    ) -> None:
        self.settings = settings or get_settings()
        self.integration = integration
        self._transport = transport
        self._session_factory = session_factory
        self._http_client: httpx.AsyncClient | None = None
        self._session_sequence = 0
        self._last_success_at: datetime | None = None
        self._last_error: str | None = None
        self._logger = get_logger(__name__)

    async def connect(self) -> ExchangeSessionState:
        if not self.integration.enabled:
            return ExchangeSessionState(
                venue=self.integration.venue.value,
                environment=self.settings.app.environment,
                connected=False,
                last_heartbeat_at=None,
                session_sequence=self._session_sequence,
            )
        try:
            await self._ping()
            self._session_sequence += 1
            self._last_success_at = utcnow()
            self._last_error = None
            return ExchangeSessionState(
                venue=self.integration.venue.value,
                environment=self.settings.app.environment,
                connected=True,
                last_heartbeat_at=self._last_success_at,
                session_sequence=self._session_sequence,
            )
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            return ExchangeSessionState(
                venue=self.integration.venue.value,
                environment=self.settings.app.environment,
                connected=False,
                last_heartbeat_at=None,
                session_sequence=self._session_sequence,
            )

    async def disconnect(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def sync_symbols(self) -> Sequence[SymbolMetadata]:
        symbols = await self._fetch_symbol_metadata()
        persist_symbol_catalog(
            self._session_factory,
            venue=self.integration.venue.value,
            symbols=symbols,
        )
        self._last_success_at = utcnow()
        self._last_error = None
        return symbols

    async def list_instruments(self) -> Sequence[Instrument]:
        return list_instruments_for_venue(self._session_factory, venue=self.integration.venue.value)

    async def get_session_state(self) -> ExchangeSessionState:
        return ExchangeSessionState(
            venue=self.integration.venue.value,
            environment=self.settings.app.environment,
            connected=self._last_success_at is not None and self._last_error is None,
            last_heartbeat_at=self._last_success_at,
            session_sequence=self._session_sequence,
        )

    async def submit_order(self, intent: OrderIntent) -> SubmittedOrder:
        raise VenueAdapterError(
            f"{self.integration.name} submit path must be implemented in the venue adapter.",
            reason_codes=["adapter_submission_unimplemented"],
        )

    async def reconcile_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.integration.venue.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=submitted_order.status,
            reconciliation_status=SubmittedOrderReconciliationStatus.UNAVAILABLE,
            event_type="reconciliation_unavailable",
            status_reason_code="venue_state_unavailable",
            status_message=(
                f"{self.integration.name} does not yet implement post-submit order-state reconciliation "
                "for the current venue scope."
            ),
            reason_codes=["venue_state_unavailable"],
            cancelable_in_principle=submitted_order.cancelable_in_principle,
            amendable_in_principle=submitted_order.amendable_in_principle,
            raw_payload={},
            observed_at=utcnow(),
        )

    def _assert_submission_controls(self, context: VenueAccountExecutionContext) -> None:
        if not self.integration.enabled:
            raise VenueAdapterError(
                f"{self.integration.name} integration is disabled.",
                reason_codes=["venue_integration_disabled"],
            )
        if self.support_level == VenueSupportLevel.QA_READ_ONLY:
            raise VenueAdapterError(
                f"{self.integration.name} remains qa_read_only for submission.",
                reason_codes=["venue_not_execution_preparable"],
            )
        if not self.integration.submission_enabled:
            raise VenueAdapterError(
                f"{self.integration.name} live submission is not enabled.",
                reason_codes=["venue_submission_not_enabled"],
            )
        if self.integration.read_only_mode:
            raise VenueAdapterError(
                f"{self.integration.name} is configured in read-only mode.",
                reason_codes=["read_only_mode_enabled"],
            )
        if self.integration.dry_run_mode or self.settings.execution.dry_run:
            raise VenueAdapterError(
                f"{self.integration.name} is configured in dry-run mode.",
                reason_codes=["dry_run_only"],
            )
        if not self.integration.submission_authorized:
            raise VenueAdapterError(
                f"{self.integration.name} submission is not authorized for the configured account/environment.",
                reason_codes=["account_not_authorized"],
            )
        if not context.account_identifier:
            raise VenueAdapterError(
                f"{self.integration.name} submission is missing a targeted account identifier.",
                reason_codes=["account_identifier_missing"],
            )
        resolved = self._resolve_credentials(context)
        if resolved.reason_codes:
            raise VenueAdapterError(
                f"{self.integration.name} targeted credentials could not be resolved.",
                reason_codes=list(resolved.reason_codes),
            )

    def _submission_request_from_preview(
        self,
        preview: PreparedVenueOrder,
    ) -> tuple[str, dict[str, Any]]:
        payload = dict(preview.payload or {})
        endpoint = payload.pop("endpoint", None)
        if endpoint is None:
            raise VenueAdapterError(
                f"{self.integration.name} preview payload is missing a submission endpoint.",
                reason_codes=["submission_endpoint_missing"],
                payload={"prepared_order_preview": asdict(preview)},
            )
        return str(endpoint), payload

    def _submission_headers(
        self,
        preview: PreparedVenueOrder,
        context: VenueAccountExecutionContext,
    ) -> dict[str, str] | None:
        return None

    @staticmethod
    def _render_json_body(
        body: dict[str, Any],
        *,
        sort_keys: bool = False,
    ) -> str:
        return json.dumps(body, separators=(",", ":"), sort_keys=sort_keys, default=str)

    @staticmethod
    def _render_form_body(
        fields: Sequence[tuple[str, Any]] | dict[str, Any],
    ) -> str:
        if isinstance(fields, dict):
            items: Sequence[tuple[str, Any]] = tuple(fields.items())
        else:
            items = fields
        return urllib.parse.urlencode(items)

    async def _request_json_exact(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any],
        headers: dict[str, str] | None = None,
        rendered_body: str | None = None,
    ) -> Any:
        request_headers = dict(headers or {})
        request_headers.setdefault("Content-Type", "application/json")
        return await self._request_exact(
            method,
            path,
            rendered_body=rendered_body or self._render_json_body(body),
            headers=request_headers,
        )

    async def _request_form_exact(
        self,
        method: str,
        path: str,
        *,
        rendered_body: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        request_headers = dict(headers or {})
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        return await self._request_exact(
            method,
            path,
            rendered_body=rendered_body,
            headers=request_headers,
        )

    async def _request_exact(
        self,
        method: str,
        path: str,
        *,
        rendered_body: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            if self._transport is not None:
                try:
                    result = await self._transport(method, path, None, rendered_body, headers)
                except TypeError:
                    result = await self._transport(
                        method,
                        path,
                        {
                            "params": None,
                            "body": rendered_body,
                            "headers": headers,
                        },
                    )
            else:
                client = await self._client()
                response = await client.request(
                    method,
                    path,
                    content=rendered_body.encode("utf-8"),
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
            self._last_success_at = utcnow()
            self._last_error = None
            return result
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._logger.error(
                "venue_exact_request_failed",
                venue=self.integration.venue.value,
                method=method,
                path=path,
                error=str(exc),
            )
            raise VenueAdapterError(f"{self.integration.name} exact request failed for {path}: {exc}") from exc

    def _submitted_order_from_response(
        self,
        *,
        intent: OrderIntent,
        preview: PreparedVenueOrder,
        response: Any,
        context: VenueAccountExecutionContext,
    ) -> SubmittedOrder:
        exchange_order_id = self._extract_exchange_order_id(response)
        client_order_id = self._extract_client_order_id(response) or preview.client_order_id
        status = self._normalize_submission_status(response, exchange_order_id=exchange_order_id)
        status_message = ReadOnlyVenueAdapter._extract_submission_message(response)
        submitted_at = utcnow()
        raw_payload = response if isinstance(response, dict) else {"response": response}
        identity_payload = {
            "venue": self.integration.venue.value,
            "intent_id": intent.intent_id,
            "exchange_order_id": exchange_order_id,
            "client_order_id": client_order_id,
            "submitted_at": submitted_at.isoformat(),
        }
        digest = hashlib.sha256(
            json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return SubmittedOrder(
            submitted_order_id=f"subm-{digest[:24]}",
            instrument_key=intent.instrument_key,
            instrument_ref_id=intent.instrument_ref_id,
            venue_account_ref_id=intent.venue_account_ref_id,
            venue=self.integration.venue.value,
            account_address=context.account_address or context.account_identifier,
            intent_id=intent.intent_id,
            client_order_id=client_order_id,
            exchange_order_id=exchange_order_id,
            status=status,
            reconciliation_status=(
                SubmittedOrderReconciliationStatus.RECONCILED
                if status == SubmittedOrderStatus.REJECTED
                else SubmittedOrderReconciliationStatus.NOT_ATTEMPTED
            ),
            submitted_at=submitted_at,
            acknowledged_at=(
                submitted_at
                if status
                in {
                    SubmittedOrderStatus.ACKNOWLEDGED,
                    SubmittedOrderStatus.CANCEL_REQUESTED,
                    SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
                    SubmittedOrderStatus.PARTIALLY_FILLED,
                    SubmittedOrderStatus.FILLED,
                    SubmittedOrderStatus.CANCELED,
                    SubmittedOrderStatus.EXPIRED,
                    SubmittedOrderStatus.REJECTED,
                }
                else None
            ),
            symbol=preview.symbol,
            side=preview.side,
            order_type=preview.order_type,
            limit_price=preview.limit_price,
            original_quantity=preview.quantity,
            remaining_quantity=(
                Decimal("0") if status == SubmittedOrderStatus.REJECTED else preview.quantity
            ),
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            last_fill_at=None,
            last_reconciled_at=None,
            status_reason_code=(
                "venue_rejected" if status == SubmittedOrderStatus.REJECTED else None
            ),
            status_message=status_message,
            reason_codes=(["venue_rejected"] if status == SubmittedOrderStatus.REJECTED else []),
            cancelable_in_principle=status
            in {
                SubmittedOrderStatus.NEW,
                SubmittedOrderStatus.SUBMITTED,
                SubmittedOrderStatus.ACKNOWLEDGED,
                SubmittedOrderStatus.PARTIALLY_FILLED,
            },
            amendable_in_principle=(
                status != SubmittedOrderStatus.REJECTED
                and preview.order_type == OrderType.LIMIT
            )
            and status
            in {
                SubmittedOrderStatus.NEW,
                SubmittedOrderStatus.SUBMITTED,
                SubmittedOrderStatus.ACKNOWLEDGED,
                SubmittedOrderStatus.PARTIALLY_FILLED,
            },
            reduce_only=preview.reduce_only,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _extract_submission_message(response: Any) -> str | None:
        if not isinstance(response, dict):
            return None
        for key in ("msg", "message", "error"):
            value = response.get(key)
            if value:
                return str(value)
        error_response = response.get("error_response")
        if error_response:
            return str(error_response)
        errors = response.get("errors")
        if isinstance(errors, list) and errors:
            return str(errors[0])
        if errors:
            return str(errors)
        data = response.get("data")
        if isinstance(data, list) and data:
            return ReadOnlyVenueAdapter._extract_submission_message(data[0])
        if isinstance(response.get("success_response"), dict):
            return ReadOnlyVenueAdapter._extract_submission_message(response["success_response"])
        if isinstance(response.get("result"), dict):
            return ReadOnlyVenueAdapter._extract_submission_message(response["result"])
        return None

    async def cancel_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> SubmittedOrderLifecycleUpdate:
        raise VenueAdapterError(
            f"{self.integration.name} cancellation remains deferred. "
            "Order cancellation is intentionally disabled.",
            reason_codes=["cancel_not_supported"],
        )

    async def amend_order(
        self,
        submitted_order: SubmittedOrder,
        *,
        new_quantity: Decimal | None = None,
        new_limit_price: Decimal | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        raise VenueAdapterError(
            f"{self.integration.name} amendment remains deferred for the current execution scope.",
            reason_codes=["amend_not_supported"],
            payload={
                "submitted_order_id": submitted_order.submitted_order_id,
                "new_quantity": str(new_quantity) if new_quantity is not None else None,
                "new_limit_price": str(new_limit_price) if new_limit_price is not None else None,
            },
        )

    async def _fetch_open_positions_with_source(
        self,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Position]]:
        with self._session_factory() as session:
            query = session.query(PositionModel).filter(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.venue == self.integration.venue.value,
                PositionModel.status == PositionStatus.OPEN,
            )
            if venue_account_ref_id is not None:
                query = query.filter(PositionModel.venue_account_ref_id == venue_account_ref_id)
            models = query.order_by(PositionModel.updated_at.desc()).all()
        positions = [
            Position(
                position_id=model.position_id,
                instrument_key=model.symbol,
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
            for model in models
        ]
        return ("persistence", positions)

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

    def _linked_submitted_order_identity(
        self,
        *,
        venue_account_ref_id: str | None,
        account_address: str | None,
        exchange_order_id: str | None,
        client_order_id: str | None,
    ) -> tuple[str | None, str | None]:
        if exchange_order_id in (None, "") and client_order_id in (None, ""):
            return (None, None)
        with self._session_factory() as session:
            query = select(SubmittedOrderModel).where(
                SubmittedOrderModel.environment == self.settings.app.environment,
                SubmittedOrderModel.venue == self.integration.venue.value,
            )
            if venue_account_ref_id is not None:
                query = query.where(SubmittedOrderModel.venue_account_ref_id == venue_account_ref_id)
            elif account_address is not None:
                query = query.where(SubmittedOrderModel.account_address == account_address)
            if exchange_order_id not in (None, ""):
                query = query.where(SubmittedOrderModel.exchange_order_id == exchange_order_id)
            else:
                query = query.where(SubmittedOrderModel.client_order_id == client_order_id)
            query = query.order_by(SubmittedOrderModel.submitted_at.desc())
            model = session.scalars(query).first()
        if model is None:
            return (None, None)
        return (model.submitted_order_id, model.intent_id)

    def _private_open_order_from_submitted_model(
        self,
        model: SubmittedOrderModel,
    ) -> VenuePrivateOpenOrder:
        symbol_model = self._lookup_symbol_model(
            instrument_key=None,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
        )
        instrument_key = self._instrument_key_for_instrument_ref(model.instrument_ref_id)
        return VenuePrivateOpenOrder(
            venue=model.venue,
            venue_account_ref_id=model.venue_account_ref_id,
            account_address=model.account_address,
            exchange_order_id=model.exchange_order_id,
            client_order_id=model.client_order_id,
            instrument_key=instrument_key,
            instrument_ref_id=model.instrument_ref_id,
            symbol=model.symbol,
            exchange_symbol=symbol_model.exchange_symbol if symbol_model is not None else None,
            status=model.status,
            observed_at=model.last_reconciled_at or model.acknowledged_at or model.submitted_at,
            side=model.side,
            order_type=model.order_type,
            limit_price=model.limit_price,
            original_quantity=model.original_quantity,
            remaining_quantity=model.remaining_quantity,
            filled_quantity=model.filled_quantity,
            average_fill_price=model.average_fill_price,
            last_fill_at=model.last_fill_at,
            status_reason_code=model.status_reason_code,
            status_message=model.status_message,
            reason_codes=list(model.reason_codes or []),
            cancelable_in_principle=model.cancelable_in_principle,
            amendable_in_principle=model.amendable_in_principle,
            reduce_only=model.reduce_only,
            linked_submitted_order_id=model.submitted_order_id,
            linked_order_intent_id=model.intent_id,
            raw_payload=dict(model.raw_payload or {}),
        )

    async def _fetch_recent_fills_with_source(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> tuple[str, Sequence[Fill]]:
        with self._session_factory() as session:
            query = session.query(FillModel).filter(
                FillModel.environment == self.settings.app.environment,
                FillModel.venue == self.integration.venue.value,
            )
            if venue_account_ref_id is not None:
                query = query.filter(FillModel.venue_account_ref_id == venue_account_ref_id)
            models = query.order_by(FillModel.filled_at.desc()).limit(limit).all()
        fills = [
            Fill(
                fill_id=model.fill_id,
                instrument_key=model.symbol,
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
            for model in models
        ]
        return ("persistence", fills)

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
        open_statuses = (
            SubmittedOrderStatus.NEW,
            SubmittedOrderStatus.SUBMITTED,
            SubmittedOrderStatus.ACKNOWLEDGED,
            SubmittedOrderStatus.CANCEL_REQUESTED,
            SubmittedOrderStatus.CANCEL_ACKNOWLEDGED,
            SubmittedOrderStatus.PARTIALLY_FILLED,
        )
        with self._session_factory() as session:
            query = session.query(SubmittedOrderModel).filter(
                SubmittedOrderModel.environment == self.settings.app.environment,
                SubmittedOrderModel.venue == self.integration.venue.value,
                SubmittedOrderModel.status.in_(open_statuses),
            )
            if venue_account_ref_id is not None:
                query = query.filter(SubmittedOrderModel.venue_account_ref_id == venue_account_ref_id)
            models = query.order_by(SubmittedOrderModel.submitted_at.desc()).all()
        return (
            "persistence",
            [self._private_open_order_from_submitted_model(model) for model in models],
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
        if source != "venue_query" or submitted_order.exchange_order_id in (None, ""):
            return SubmittedOrderPrivateFillEvidence(
                source=source,
                evidence_scope="unavailable",
                fills=[],
                message="No submitted-order-scoped private fill evidence was available.",
            )
        matched = [
            item
            for item in fills
            if item.exchange_order_id == submitted_order.exchange_order_id
        ]
        return SubmittedOrderPrivateFillEvidence(
            source=source,
            evidence_scope="order_scoped",
            fills=list(matched[:limit]),
            message=(
                "Private fill evidence was matched by exchange order id."
                if matched
                else "Private fill query was filtered by exchange order id; no matching fills were returned."
            ),
        )

    async def get_exchange_status(self) -> ExchangeStatus:
        context = self._resolve_execution_context(None)
        connected = self._last_success_at is not None and self._last_error is None
        return ExchangeStatus(
            venue=self.integration.venue.value,
            environment=self._integration_environment,
            connected=connected,
            api_base_url=self.integration.api_base_url,
            websocket_base_url=self.integration.ws_base_url,
            can_sign_orders=self._credentials_configured(context),
            wallet_address_configured=bool(context.account_address),
            account_identifier_configured=bool(context.account_identifier),
            credentials_configured=self._credentials_configured(context),
            read_only_mode=self.integration.read_only_mode,
            dry_run_mode=self.integration.dry_run_mode,
            submission_enabled=self.integration.submission_enabled,
            support_level=self.support_level,
            adapter_supports_order_submission=self.adapter_supports_order_submission,
            adapter_supports_order_cancel=self.adapter_supports_order_cancel,
            adapter_supports_order_amend=self.adapter_supports_order_amend,
            adapter_supports_user_streams=self.adapter_supports_user_streams,
            submission_authorized=self.integration.submission_authorized,
            live_submission_phase_enabled=self.settings.execution.live_submission_phase_enabled,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
            private_lifecycle_update_mode=self.private_lifecycle_update_mode,
        )

    async def get_account_connectivity(self) -> VenueAccountConnectivity:
        context = self._resolve_execution_context(None)
        snapshot = await self._read_account_snapshot_for_context(context)
        return self._account_connectivity_for_context(context, snapshot=snapshot)

    def _account_connectivity_for_context(
        self,
        context: VenueAccountExecutionContext,
        *,
        snapshot: ExchangeAccountSnapshot | None,
    ) -> VenueAccountConnectivity:
        return VenueAccountConnectivity(
            venue=self.integration.venue.value,
            environment=self._integration_environment,
            support_level=self.support_level,
            account_model=self.account_model,
            account_identifier=context.account_identifier,
            account_label=context.account_label,
            subaccount_label=context.subaccount_label,
            credentials_ref=context.credentials_ref,
            account_identifier_configured=bool(context.account_identifier),
            credentials_configured=self._credentials_configured(context),
            read_only_mode=self.integration.read_only_mode,
            dry_run_mode=self.integration.dry_run_mode,
            submission_enabled=self.integration.submission_enabled,
            submission_authorized=(
                self.integration.submission_authorized and self._credentials_configured(context)
            ),
            private_account_sync_enabled=self._credentials_configured(context),
            account_snapshot_available=snapshot is not None,
            open_orders_query_available=self.supports_open_orders_query,
            open_positions_query_available=self.supports_open_positions_query,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
        )

    async def read_account_snapshot(self) -> ExchangeAccountSnapshot | None:
        return None

    async def _read_account_snapshot_for_context(
        self,
        context: VenueAccountExecutionContext,
    ) -> ExchangeAccountSnapshot | None:
        return await self.read_account_snapshot()

    async def get_private_state_summary(self) -> VenuePrivateStateSummary:
        connectivity = await self.get_account_connectivity()
        snapshot = await self.read_account_snapshot()
        open_orders_source, open_orders = await self.fetch_open_orders_with_source()
        recent_fills_source, recent_fills = await self.fetch_recent_fills_with_source()
        open_positions_source, open_positions = await self.fetch_open_positions_with_source()
        return VenuePrivateStateSummary(
            venue=self.integration.venue.value,
            support_level=self.support_level,
            account_model=connectivity.account_model,
            account_identifier=connectivity.account_identifier,
            read_only_mode=connectivity.read_only_mode,
            dry_run_mode=connectivity.dry_run_mode,
            private_account_sync_enabled=connectivity.private_account_sync_enabled,
            account_snapshot_available=snapshot is not None,
            balances_visible=snapshot is not None,
            open_orders_query_available=open_orders_source != "unavailable",
            open_orders_count=len(open_orders),
            open_orders_source=open_orders_source,
            open_positions_query_available=open_positions_source != "unavailable",
            open_positions_count=len(open_positions),
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
            venue=self.integration.venue.value,
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
        context = self._resolve_execution_context(intent.venue_account_ref_id)
        snapshot = await self._read_account_snapshot_for_context(context)
        connectivity = self._account_connectivity_for_context(context, snapshot=snapshot)
        account_model = self._lookup_venue_account(intent.venue_account_ref_id)
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
        client_order_id = None
        if capabilities.supports_client_order_ids:
            client_order_id = self._client_order_id_override(intent) or self._client_order_id(intent)
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
            venue=self.integration.venue.value,
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
            prepared_at=utcnow(),
        )

    async def get_top_of_book(self, symbol: str) -> TopOfBookSnapshot | None:
        return None

    async def get_depth_summary(
        self,
        symbol: str,
        depth_levels: int = 5,
    ) -> OrderBookDepthSummary | None:
        return None

    def _lookup_symbol_model(
        self,
        *,
        instrument_key: str | None,
        instrument_ref_id: str | None,
        symbol: str | None,
    ) -> SymbolModel | None:
        with self._session_factory() as session:
            query = select(SymbolModel).where(
                SymbolModel.venue == self.integration.venue.value,
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
                    SymbolModel.venue == self.integration.venue.value,
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

    def _default_time_in_force(self, order_type: OrderType) -> str | None:
        if order_type == OrderType.LIMIT and self.supported_time_in_force:
            return self.supported_time_in_force[0]
        return None

    def _resolve_execution_context(
        self,
        venue_account_ref_id: str | None,
    ) -> VenueAccountExecutionContext:
        model = self._lookup_venue_account(venue_account_ref_id)
        if model is not None:
            account_identifier = model.venue_native_account_id or model.account_address or None
            return VenueAccountExecutionContext(
                venue_account_ref_id=model.id,
                venue_account_key=model.venue_account_key,
                venue_native_account_id=model.venue_native_account_id,
                account_identifier=account_identifier,
                account_address=model.account_address,
                account_label=model.account_label or None,
                subaccount_label=model.subaccount_label or None,
                credentials_ref=model.credentials_ref or self.integration.credentials_ref or None,
                wallet_ref=model.wallet_ref or self.integration.wallet_ref or None,
                raw_metadata=dict(model.raw_metadata or {}),
            )
        account_identifier = self.integration.account_identifier or self.integration.account_address or None
        return VenueAccountExecutionContext(
            venue_account_ref_id=venue_account_ref_id,
            venue_account_key=None,
            venue_native_account_id=self.integration.account_identifier or None,
            account_identifier=account_identifier,
            account_address=self.integration.account_address or None,
            account_label=self.integration.account_label or None,
            subaccount_label=self.integration.subaccount_label or None,
            credentials_ref=self.integration.credentials_ref or None,
            wallet_ref=self.integration.wallet_ref or None,
            raw_metadata={},
        )

    def _context_for_submitted_order(
        self,
        submitted_order: SubmittedOrder,
    ) -> VenueAccountExecutionContext:
        context = self._resolve_execution_context(submitted_order.venue_account_ref_id)
        if submitted_order.account_address and context.account_address != submitted_order.account_address:
            context = replace(
                context,
                account_address=submitted_order.account_address,
                account_identifier=context.account_identifier or submitted_order.account_address,
            )
        return context

    def _credentials_configured(self, context: VenueAccountExecutionContext) -> bool:
        resolved = self._resolve_credentials(context)
        return resolved.is_resolved and resolved.has_auth_material

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
            api_key = normalized_auth.get("api_key")
            api_secret = normalized_auth.get("api_secret")
            api_passphrase = normalized_auth.get("api_passphrase")
            signing_private_key = normalized_auth.get("signing_private_key")
            jwt_key_name = normalized_auth.get("jwt_key_name") or api_key
            jwt_private_key_pem = normalized_auth.get("jwt_private_key_pem") or api_secret
        elif reason_codes:
            source = "unresolved_reference"
            api_key = None
            api_secret = None
            api_passphrase = None
            signing_private_key = None
            jwt_key_name = None
            jwt_private_key_pem = None
        else:
            source = "integration_defaults"
            api_key = self.integration.api_key or None
            api_secret = self.integration.api_secret or None
            api_passphrase = self.integration.api_passphrase or None
            signing_private_key = self.integration.signing_private_key or None
            jwt_key_name = self.integration.jwt_key_name or api_key
            jwt_private_key_pem = self.integration.jwt_private_key_pem or api_secret

        return ResolvedVenueCredentials(
            source=source,
            reason_codes=reason_codes,
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            signing_private_key=signing_private_key,
            jwt_key_name=jwt_key_name,
            jwt_private_key_pem=jwt_private_key_pem,
        )

    def _api_key_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).api_key

    def _api_secret_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).api_secret

    def _api_passphrase_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).api_passphrase

    def _signing_private_key_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).signing_private_key

    def _jwt_key_name_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).jwt_key_name

    def _jwt_private_key_pem_for_context(self, context: VenueAccountExecutionContext) -> str | None:
        return self._resolve_credentials(context).jwt_private_key_pem

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

    def _exchange_symbol_for_submitted_order(self, submitted_order: SubmittedOrder) -> str | None:
        with self._session_factory() as session:
            query = select(SymbolModel).where(SymbolModel.venue == self.integration.venue.value)
            if submitted_order.instrument_ref_id is not None:
                query = query.where(SymbolModel.instrument_ref_id == submitted_order.instrument_ref_id)
                model = session.scalar(query.order_by(SymbolModel.exchange_symbol.asc()))
                return model.exchange_symbol if model is not None else None
            if submitted_order.symbol is None:
                return None
            models = session.scalars(
                query.where(SymbolModel.symbol == submitted_order.symbol.upper()).order_by(
                    SymbolModel.exchange_symbol.asc()
                )
            ).all()
        if len(models) != 1:
            return None
        return models[0].exchange_symbol

    @staticmethod
    def _client_order_id_override(intent: OrderIntent) -> str | None:
        overrides = intent.provenance.get("submission_overrides")
        if not isinstance(overrides, dict):
            return None
        override = overrides.get("client_order_id")
        if override in (None, ""):
            return None
        return str(override)

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
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": exchange_symbol,
            "side": intent.side.value.upper(),
            "type": intent.order_type.value,
            "quantity": str(intent.quantity),
            "reduce_only": intent.reduce_only,
        }
        if intent.limit_price is not None:
            payload["limit_price"] = str(intent.limit_price)
        if time_in_force is not None:
            payload["time_in_force"] = time_in_force
        if client_order_id is not None:
            payload["client_order_id"] = client_order_id
        return payload

    @staticmethod
    def _hmac_sha256_hex(secret: str, message: str) -> str:
        return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _hmac_sha256_base64(secret: str, message: str) -> str:
        digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _hmac_sha512_base64(secret: str, message: bytes) -> str:
        try:
            secret_bytes = base64.b64decode(secret)
        except Exception:  # noqa: BLE001
            secret_bytes = secret.encode("utf-8")
        digest = hmac.new(secret_bytes, message, hashlib.sha512).digest()
        return base64.b64encode(digest).decode("utf-8")

    @property
    def _integration_environment(self) -> Environment:
        if self.integration.use_testnet and self.settings.app.environment == Environment.LIVE:
            return Environment.TESTNET
        return self.settings.app.environment

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(base_url=self.integration.api_base_url, timeout=10.0)
        return self._http_client

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            if self._transport is not None:
                if body is None and headers is None:
                    result = await self._transport(method, path, params)
                else:
                    try:
                        result = await self._transport(method, path, params, body, headers)
                    except TypeError:
                        result = await self._transport(
                            method,
                            path,
                            {
                                "params": params,
                                "body": body,
                                "headers": headers,
                            },
                        )
            else:
                client = await self._client()
                response = await client.request(method, path, params=params, json=body, headers=headers)
                response.raise_for_status()
                result = response.json()
            self._last_success_at = utcnow()
            self._last_error = None
            return result
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._logger.error(
                "venue_request_failed",
                venue=self.integration.venue.value,
                method=method,
                path=path,
                error=str(exc),
            )
            raise VenueAdapterError(f"{self.integration.name} request failed for {path}: {exc}") from exc

    async def _ping(self) -> None:
        raise NotImplementedError

    async def _fetch_symbol_metadata(self) -> Sequence[SymbolMetadata]:
        raise NotImplementedError

    @staticmethod
    def _extract_exchange_order_id(response: Any) -> str | None:
        if isinstance(response, dict):
            for key in ("exchange_order_id", "order_id", "orderId", "ordId", "id"):
                value = response.get(key)
                if value:
                    return str(value)
            txid = response.get("txid")
            if isinstance(txid, list) and txid:
                return str(txid[0])
            data = response.get("data")
            if isinstance(data, list) and data:
                return ReadOnlyVenueAdapter._extract_exchange_order_id(data[0])
            if isinstance(response.get("success_response"), dict):
                return ReadOnlyVenueAdapter._extract_exchange_order_id(response["success_response"])
            if isinstance(response.get("result"), dict):
                return ReadOnlyVenueAdapter._extract_exchange_order_id(response["result"])
        return None

    @staticmethod
    def _extract_client_order_id(response: Any) -> str | None:
        if isinstance(response, dict):
            for key in ("client_order_id", "clientOrderId", "clOrdId"):
                value = response.get(key)
                if value:
                    return str(value)
            data = response.get("data")
            if isinstance(data, list) and data:
                return ReadOnlyVenueAdapter._extract_client_order_id(data[0])
            if isinstance(response.get("success_response"), dict):
                return ReadOnlyVenueAdapter._extract_client_order_id(response["success_response"])
            if isinstance(response.get("result"), dict):
                return ReadOnlyVenueAdapter._extract_client_order_id(response["result"])
        return None

    @staticmethod
    def _normalize_submission_status(
        response: Any,
        *,
        exchange_order_id: str | None,
    ) -> SubmittedOrderStatus:
        if isinstance(response, dict):
            if response.get("success") is False or response.get("success") == "false":
                return SubmittedOrderStatus.REJECTED
            code = response.get("code")
            if code not in (None, 0, "0"):
                return SubmittedOrderStatus.REJECTED
            if response.get("error") or response.get("error_response") or response.get("errors"):
                return SubmittedOrderStatus.REJECTED
            status = str(response.get("status", "")).lower()
            if status in {"rejected", "error", "failed"}:
                return SubmittedOrderStatus.REJECTED
            if status in {"new", "accepted"} and exchange_order_id is None:
                return SubmittedOrderStatus.SUBMITTED
        return SubmittedOrderStatus.ACKNOWLEDGED if exchange_order_id is not None else SubmittedOrderStatus.SUBMITTED

    def _cancel_success_update(
        self,
        *,
        submitted_order: SubmittedOrder,
        exchange_order_id: str | None = None,
        status: SubmittedOrderStatus = SubmittedOrderStatus.CANCELED,
        reconciliation_status: SubmittedOrderReconciliationStatus = SubmittedOrderReconciliationStatus.RECONCILED,
        event_type: str | None = None,
        status_reason_code: str | None = None,
        message: str | None = None,
        reason_codes: list[str] | None = None,
        remaining_quantity: Decimal | None = None,
        cancelable_in_principle: bool | None = None,
        amendable_in_principle: bool | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        resolved_event_type = event_type or (
            "cancel_acknowledged"
            if status == SubmittedOrderStatus.CANCEL_ACKNOWLEDGED
            else "cancel_confirmed"
        )
        resolved_reason_code = status_reason_code or resolved_event_type
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.integration.venue.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=exchange_order_id or submitted_order.exchange_order_id,
            status=status,
            reconciliation_status=reconciliation_status,
            event_type=resolved_event_type,
            remaining_quantity=(
                remaining_quantity
                if remaining_quantity is not None
                else (Decimal("0") if status == SubmittedOrderStatus.CANCELED else submitted_order.remaining_quantity)
            ),
            filled_quantity=submitted_order.filled_quantity,
            average_fill_price=submitted_order.average_fill_price,
            last_fill_at=submitted_order.last_fill_at,
            acknowledged_at=submitted_order.acknowledged_at,
            status_reason_code=resolved_reason_code,
            status_message=message or f"{self.integration.name} acknowledged cancellation for the submitted order.",
            reason_codes=list(reason_codes or [resolved_reason_code]),
            cancelable_in_principle=(
                cancelable_in_principle if cancelable_in_principle is not None else False
            ),
            amendable_in_principle=(
                amendable_in_principle if amendable_in_principle is not None else False
            ),
            raw_payload=dict(raw_payload or {}),
            observed_at=utcnow(),
        )

    def _cancel_rejected_update(
        self,
        *,
        submitted_order: SubmittedOrder,
        reason_codes: list[str] | None = None,
        message: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.integration.venue.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=submitted_order.status,
            reconciliation_status=submitted_order.reconciliation_status,
            event_type="cancel_rejected",
            remaining_quantity=submitted_order.remaining_quantity,
            filled_quantity=submitted_order.filled_quantity,
            average_fill_price=submitted_order.average_fill_price,
            last_fill_at=submitted_order.last_fill_at,
            acknowledged_at=submitted_order.acknowledged_at,
            status_reason_code=(reason_codes[0] if reason_codes else "cancel_rejected"),
            status_message=message or f"{self.integration.name} rejected cancellation for the submitted order.",
            reason_codes=list(reason_codes or ["cancel_rejected"]),
            cancelable_in_principle=submitted_order.cancelable_in_principle,
            amendable_in_principle=submitted_order.amendable_in_principle,
            raw_payload=dict(raw_payload or {}),
            observed_at=utcnow(),
        )

    def _amend_acknowledged_update(
        self,
        *,
        submitted_order: SubmittedOrder,
        new_quantity: Decimal | None,
        new_limit_price: Decimal | None,
        message: str,
        raw_payload: dict[str, Any] | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        original_quantity = new_quantity if new_quantity is not None else submitted_order.original_quantity
        filled_quantity = submitted_order.filled_quantity or Decimal("0")
        remaining_quantity = submitted_order.remaining_quantity
        if original_quantity is not None:
            remaining_quantity = max(original_quantity - filled_quantity, Decimal("0"))
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.integration.venue.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=(
                SubmittedOrderStatus.PARTIALLY_FILLED
                if (submitted_order.filled_quantity or Decimal("0")) > Decimal("0")
                else SubmittedOrderStatus.ACKNOWLEDGED
            ),
            reconciliation_status=SubmittedOrderReconciliationStatus.PENDING,
            event_type="amend_acknowledged",
            limit_price=new_limit_price if new_limit_price is not None else submitted_order.limit_price,
            original_quantity=original_quantity,
            remaining_quantity=remaining_quantity,
            filled_quantity=submitted_order.filled_quantity,
            average_fill_price=submitted_order.average_fill_price,
            last_fill_at=submitted_order.last_fill_at,
            acknowledged_at=submitted_order.acknowledged_at,
            status_reason_code="amend_acknowledged",
            status_message=message,
            reason_codes=["amend_acknowledged"],
            cancelable_in_principle=True,
            amendable_in_principle=True,
            raw_payload=dict(raw_payload or {}),
            observed_at=utcnow(),
        )

    def _amend_rejected_update(
        self,
        *,
        submitted_order: SubmittedOrder,
        reason_codes: list[str] | None = None,
        message: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> SubmittedOrderLifecycleUpdate:
        return SubmittedOrderLifecycleUpdate(
            submitted_order_id=submitted_order.submitted_order_id,
            venue=self.integration.venue.value,
            venue_account_ref_id=submitted_order.venue_account_ref_id,
            exchange_order_id=submitted_order.exchange_order_id,
            status=submitted_order.status,
            reconciliation_status=submitted_order.reconciliation_status,
            event_type="amend_rejected",
            limit_price=submitted_order.limit_price,
            original_quantity=submitted_order.original_quantity,
            remaining_quantity=submitted_order.remaining_quantity,
            filled_quantity=submitted_order.filled_quantity,
            average_fill_price=submitted_order.average_fill_price,
            last_fill_at=submitted_order.last_fill_at,
            acknowledged_at=submitted_order.acknowledged_at,
            status_reason_code=(reason_codes[0] if reason_codes else "amend_rejected"),
            status_message=message or f"{self.integration.name} rejected amendment for the submitted order.",
            reason_codes=list(reason_codes or ["amend_rejected"]),
            cancelable_in_principle=submitted_order.cancelable_in_principle,
            amendable_in_principle=submitted_order.amendable_in_principle,
            raw_payload=dict(raw_payload or {}),
            observed_at=utcnow(),
        )


def _conforms_to_increment(value: Decimal, increment: Decimal) -> bool:
    if increment <= Decimal("0"):
        return False
    normalized = (value / increment).normalize()
    return normalized == normalized.to_integral_value()
