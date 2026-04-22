"""Portfolio loader primitives backed by persisted exchange state."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import PositionStatus, SubmittedOrderStatus
from core.domain.models import (
    ExchangeAccountSnapshot,
    Fill,
    PortfolioBootstrapSummary,
    PortfolioSnapshot,
    Position,
    PositionAttributionOverlay,
    SubmittedOrder,
)
from core.interfaces.services import PortfolioService
from db.models import (
    ExchangeAccountSnapshotModel,
    FillModel,
    PortfolioSnapshotModel,
    PositionAttributionOverlayModel,
    PositionModel,
    SubmittedOrderModel,
)
from db.session import SessionLocal
from services.runtime.context import DefaultRuntimeContextService


class DefaultPortfolioService(PortfolioService):
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        session_factory=SessionLocal,
        runtime_context_service: DefaultRuntimeContextService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory
        self.runtime_context_service = runtime_context_service or DefaultRuntimeContextService(
            self.settings,
            session_factory=session_factory,
        )

    @staticmethod
    def _focused_binding(context: Any) -> Any | None:
        return context.bindings[0] if context.bindings else None

    async def get_open_positions(
        self,
        venue_account_ref_id: str | None = None,
        account_address: str | None = None,
    ) -> Sequence[Position]:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        scoped_address = account_address or (
            focused_binding.venue_account.account_address if focused_binding is not None else None
        )
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
        return [_position_from_model(model) for model in models]

    async def get_position_attribution_overlays(
        self,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[PositionAttributionOverlay]:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        with self._session_factory() as session:
            query = select(PositionAttributionOverlayModel).where(
                PositionAttributionOverlayModel.environment == self.settings.app.environment,
                PositionAttributionOverlayModel.venue == self.settings.exchange.venue,
            )
            if scoped_account_ref is not None:
                query = query.where(PositionAttributionOverlayModel.venue_account_ref_id == scoped_account_ref)
            models = session.scalars(query.order_by(PositionAttributionOverlayModel.as_of.desc())).all()
        return [
            PositionAttributionOverlay(
                overlay_id=model.overlay_id,
                position_id=model.position_id,
                venue_account_ref_id=model.venue_account_ref_id,
                sleeve_id=model.sleeve_id,
                attributed_quantity=model.attributed_quantity,
                attributed_notional=model.attributed_notional,
                as_of=model.as_of,
            )
            for model in models
        ]

    async def get_latest_account_snapshot(
        self,
        venue_account_ref_id: str | None = None,
    ) -> ExchangeAccountSnapshot | None:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        with self._session_factory() as session:
            query = select(ExchangeAccountSnapshotModel).where(
                ExchangeAccountSnapshotModel.environment == self.settings.app.environment,
                ExchangeAccountSnapshotModel.venue == self.settings.exchange.venue,
            )
            if scoped_account_ref is not None:
                query = query.where(ExchangeAccountSnapshotModel.venue_account_ref_id == scoped_account_ref)
            model = session.scalar(query.order_by(ExchangeAccountSnapshotModel.observed_at.desc()).limit(1))
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

    async def get_recent_fills(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[Fill]:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        with self._session_factory() as session:
            query = select(FillModel).where(
                FillModel.environment == self.settings.app.environment,
                FillModel.venue == self.settings.exchange.venue,
            )
            if scoped_account_ref is not None:
                query = query.where(FillModel.venue_account_ref_id == scoped_account_ref)
            models = session.scalars(query.order_by(FillModel.filled_at.desc()).limit(limit)).all()
        return [
            Fill(
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
            for model in models
        ]

    async def get_recent_submitted_orders(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
    ) -> Sequence[SubmittedOrder]:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        with self._session_factory() as session:
            query = select(SubmittedOrderModel).where(
                SubmittedOrderModel.environment == self.settings.app.environment,
                SubmittedOrderModel.venue == self.settings.exchange.venue,
            )
            if scoped_account_ref is not None:
                query = query.where(SubmittedOrderModel.venue_account_ref_id == scoped_account_ref)
            models = session.scalars(query.order_by(SubmittedOrderModel.submitted_at.desc()).limit(limit)).all()
        return [
            SubmittedOrder(
                submitted_order_id=model.submitted_order_id,
                instrument_key=None,
                instrument_ref_id=model.instrument_ref_id,
                venue_account_ref_id=model.venue_account_ref_id,
                venue=model.venue,
                account_address=model.account_address,
                intent_id=model.intent_id,
                client_order_id=model.client_order_id,
                exchange_order_id=model.exchange_order_id,
                status=model.status,
                reconciliation_status=model.reconciliation_status,
                submitted_at=model.submitted_at,
                acknowledged_at=model.acknowledged_at,
                symbol=model.symbol,
                side=model.side,
                order_type=model.order_type,
                limit_price=model.limit_price,
                original_quantity=model.original_quantity,
                remaining_quantity=model.remaining_quantity,
                filled_quantity=model.filled_quantity,
                average_fill_price=model.average_fill_price,
                last_fill_at=model.last_fill_at,
                last_reconciled_at=model.last_reconciled_at,
                status_reason_code=model.status_reason_code,
                status_message=model.status_message,
                reason_codes=list(model.reason_codes or []),
                cancelable_in_principle=model.cancelable_in_principle,
                amendable_in_principle=model.amendable_in_principle,
                reduce_only=model.reduce_only,
                raw_payload=dict(model.raw_payload or {}),
            )
            for model in models
        ]

    async def get_open_submitted_orders(
        self,
        limit: int = 100,
        venue_account_ref_id: str | None = None,
        account_address: str | None = None,
    ) -> Sequence[SubmittedOrder]:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        scoped_account_ref = venue_account_ref_id or (
            focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
        )
        scoped_address = account_address or (
            focused_binding.venue_account.account_address if focused_binding is not None else None
        )
        with self._session_factory() as session:
            query = select(SubmittedOrderModel).where(
                SubmittedOrderModel.environment == self.settings.app.environment,
                SubmittedOrderModel.venue == self.settings.exchange.venue,
                SubmittedOrderModel.status.in_(
                    [
                        SubmittedOrderStatus.NEW,
                        SubmittedOrderStatus.SUBMITTED,
                        SubmittedOrderStatus.ACKNOWLEDGED,
                        SubmittedOrderStatus.PARTIALLY_FILLED,
                    ]
                ),
            )
            if scoped_account_ref is not None:
                query = query.where(SubmittedOrderModel.venue_account_ref_id == scoped_account_ref)
            elif scoped_address is not None:
                query = query.where(SubmittedOrderModel.account_address == scoped_address)
            models = session.scalars(query.order_by(SubmittedOrderModel.submitted_at.desc()).limit(limit)).all()
        return [
            SubmittedOrder(
                submitted_order_id=model.submitted_order_id,
                instrument_key=None,
                instrument_ref_id=model.instrument_ref_id,
                venue_account_ref_id=model.venue_account_ref_id,
                venue=model.venue,
                account_address=model.account_address,
                intent_id=model.intent_id,
                client_order_id=model.client_order_id,
                exchange_order_id=model.exchange_order_id,
                status=model.status,
                reconciliation_status=model.reconciliation_status,
                submitted_at=model.submitted_at,
                acknowledged_at=model.acknowledged_at,
                symbol=model.symbol,
                side=model.side,
                order_type=model.order_type,
                limit_price=model.limit_price,
                original_quantity=model.original_quantity,
                remaining_quantity=model.remaining_quantity,
                filled_quantity=model.filled_quantity,
                average_fill_price=model.average_fill_price,
                last_fill_at=model.last_fill_at,
                last_reconciled_at=model.last_reconciled_at,
                status_reason_code=model.status_reason_code,
                status_message=model.status_message,
                reason_codes=list(model.reason_codes or []),
                cancelable_in_principle=model.cancelable_in_principle,
                amendable_in_principle=model.amendable_in_principle,
                reduce_only=model.reduce_only,
                raw_payload=dict(model.raw_payload or {}),
            )
            for model in models
        ]

    async def get_bootstrap_summary(self) -> PortfolioBootstrapSummary:
        context = await self.runtime_context_service.ensure_active_context()
        account_refs = [binding.venue_account.venue_account_ref_id for binding in context.bindings if binding.venue_account.venue_account_ref_id]
        account_snapshot = (
            await self.get_latest_account_snapshot(account_refs[0])
            if len(account_refs) == 1
            else None
        )
        open_positions: list[Position] = []
        overlays: list[PositionAttributionOverlay] = []
        recent_fills: list[Fill] = []
        recent_submitted_orders: list[SubmittedOrder] = []
        open_orders: list[SubmittedOrder] = []
        for binding in context.bindings:
            account_ref = binding.venue_account.venue_account_ref_id
            open_positions.extend(
                await self.get_open_positions(
                    venue_account_ref_id=account_ref,
                    account_address=binding.venue_account.account_address,
                )
            )
            overlays.extend(await self.get_position_attribution_overlays(account_ref))
            recent_fills.extend(await self.get_recent_fills(limit=100, venue_account_ref_id=account_ref))
            recent_submitted_orders.extend(
                await self.get_recent_submitted_orders(limit=100, venue_account_ref_id=account_ref)
            )
            open_orders.extend(
                await self.get_open_submitted_orders(
                    limit=100,
                    venue_account_ref_id=account_ref,
                    account_address=binding.venue_account.account_address,
                )
            )
        gross_exposure = sum(
            (position.quantity * (position.mark_price or position.avg_entry_price)) for position in open_positions
        )
        net_exposure = sum(
            (
                (position.quantity * (position.mark_price or position.avg_entry_price))
                if position.side.value == "buy"
                else -(position.quantity * (position.mark_price or position.avg_entry_price))
            )
            for position in open_positions
        )
        latest_overlay_by_position: dict[str, PositionAttributionOverlay] = {}
        for overlay in sorted(overlays, key=lambda item: item.as_of, reverse=True):
            latest_overlay_by_position.setdefault(overlay.position_id, overlay)
        attributed_position_ids = {
            position_id
            for position_id, overlay in latest_overlay_by_position.items()
            if overlay.attributed_quantity > 0
        }
        return PortfolioBootstrapSummary(
            client_key=context.client.client_key,
            mandate_key=context.mandate.mandate_key,
            venue=self.settings.exchange.venue,
            environment=self.settings.app.environment,
            account_snapshot=account_snapshot,
            bound_accounts=len(context.bindings),
            open_positions=len(open_positions),
            recent_fills=len(recent_fills),
            open_orders=len(open_orders),
            recent_submitted_orders=len(recent_submitted_orders),
            unattributed_positions=max(
                len([position for position in open_positions if position.position_id not in attributed_position_ids]),
                0,
            ),
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
        )

    async def get_latest_snapshot(self) -> PortfolioSnapshot | None:
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        with self._session_factory() as session:
            model = session.scalar(
                select(PortfolioSnapshotModel)
                .where(
                    PortfolioSnapshotModel.environment == self.settings.app.environment,
                    PortfolioSnapshotModel.venue_account_ref_id
                    == (focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None),
                )
                .order_by(PortfolioSnapshotModel.captured_at.desc())
                .limit(1)
            )
        if model is None:
            return None
        return PortfolioSnapshot(
            snapshot_id=model.snapshot_id,
            environment=model.environment,
            account_equity=model.account_equity,
            gross_exposure=model.gross_exposure,
            net_exposure=model.net_exposure,
            drawdown_pct=model.drawdown_pct,
            captured_at=model.captured_at,
        )

    async def refresh_snapshot(self) -> PortfolioSnapshot:
        summary = await self.get_bootstrap_summary()
        context = await self.runtime_context_service.ensure_active_context()
        focused_binding = self._focused_binding(context)
        account_equity = summary.account_snapshot.equity if summary.account_snapshot else Decimal("0")
        snapshot = PortfolioSnapshot(
            snapshot_id=f"bootstrap-{uuid4()}",
            environment=self.settings.app.environment,
            account_equity=account_equity,
            gross_exposure=summary.gross_exposure,
            net_exposure=summary.net_exposure,
            drawdown_pct=Decimal("0"),
            captured_at=(summary.account_snapshot.observed_at if summary.account_snapshot else None)
            or datetime.now(UTC),
        )
        with self._session_factory() as session:
            session.add(
                PortfolioSnapshotModel(
                    environment=snapshot.environment,
                    snapshot_id=snapshot.snapshot_id,
                    venue_account_ref_id=(
                        focused_binding.venue_account.venue_account_ref_id if focused_binding is not None else None
                    ),
                    account_equity=snapshot.account_equity,
                    gross_exposure=snapshot.gross_exposure,
                    net_exposure=snapshot.net_exposure,
                    drawdown_pct=snapshot.drawdown_pct,
                    sleeve_exposures={},
                    captured_at=snapshot.captured_at,
                )
            )
            session.commit()
        return snapshot


def _position_from_model(model: PositionModel) -> Position:
    return Position(
        position_id=model.position_id,
        instrument_key=None,
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
