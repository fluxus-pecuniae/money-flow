"""Runtime mandate context bootstrap and lookup."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
import re
from typing import Any

from sqlalchemy import select, update

from core.config.settings import AppSettings, MoneyFlowSleeveConfig, get_settings
from core.domain.enums import StrategyFamily
from core.domain.models import (
    ActiveMandateBindingContext,
    ActiveMandateContext,
    Client,
    MandateAccountBinding,
    MandateMarketDataSourcePolicy,
    StrategyComponentConfig,
    StrategyMandate,
    VenueAccount,
)
from core.interfaces.services import RuntimeContextService
from db.models import (
    ClientModel,
    ExchangeAccountSnapshotModel,
    FillModel,
    MandateAccountBindingModel,
    MandateMarketDataSourcePolicyModel,
    OrderIntentModel,
    PortfolioSnapshotModel,
    PositionAttributionOverlayModel,
    PositionModel,
    SignalEventModel,
    StrategyComponentConfigModel,
    StrategyDecisionModel,
    StrategyMandateModel,
    SubmittedOrderModel,
    VenueAccountModel,
)
from db.session import SessionLocal

MANDATE_DEFAULT_SCOPE = "__mandate_default__"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "default"


def _display_name_from_key(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


class DefaultRuntimeContextService(RuntimeContextService):
    def __init__(self, settings: AppSettings | None = None, *, session_factory: Any = SessionLocal) -> None:
        self.settings = settings or get_settings()
        self._session_factory = session_factory

    async def ensure_active_context(self) -> ActiveMandateContext:
        with self._session_factory() as session:
            client_model = self._ensure_client(session)
            self._ensure_discovered_accounts(session, client_model)
            focused_account_model = self._ensure_focused_account(session, client_model)
            mandate_model = self._ensure_active_mandate(session, client_model)
            self._ensure_mandate_binding(session, mandate_model, focused_account_model)
            self._ensure_mandate_market_data_source_policy(session, mandate_model)
            self._ensure_mandate_default_components(session, mandate_model)
            self._ensure_binding_component_overrides(session, mandate_model, focused_account_model)
            self._backfill_active_context(session, client_model, mandate_model)
            session.commit()
            return self._load_context(session, mandate_model.mandate_key)

    async def get_active_context(self) -> ActiveMandateContext:
        return await self.ensure_active_context()

    async def list_clients(self) -> Sequence[Client]:
        with self._session_factory() as session:
            models = session.scalars(select(ClientModel).order_by(ClientModel.client_key.asc())).all()
        return [self._client_from_model(model) for model in models]

    async def list_venue_accounts(self, client_key: str | None = None) -> Sequence[VenueAccount]:
        await self.ensure_active_context()
        with self._session_factory() as session:
            query = select(VenueAccountModel).order_by(VenueAccountModel.venue_account_key.asc())
            if client_key is not None:
                client = session.scalar(select(ClientModel).where(ClientModel.client_key == client_key))
                if client is None:
                    return []
                query = query.where(VenueAccountModel.client_ref_id == client.id)
            models = session.scalars(query).all()
            client_ids = {model.client_ref_id for model in models}
            clients = {
                model.id: model
                for model in session.scalars(select(ClientModel).where(ClientModel.id.in_(client_ids))).all()
            }
        return [self._venue_account_from_model(model, clients[model.client_ref_id]) for model in models]

    async def list_mandates(self, client_key: str | None = None) -> Sequence[StrategyMandate]:
        await self.ensure_active_context()
        with self._session_factory() as session:
            query = select(StrategyMandateModel).order_by(StrategyMandateModel.mandate_key.asc())
            if client_key is not None:
                client = session.scalar(select(ClientModel).where(ClientModel.client_key == client_key))
                if client is None:
                    return []
                query = query.where(StrategyMandateModel.client_ref_id == client.id)
            mandate_models = session.scalars(query).all()
            client_ids = {model.client_ref_id for model in mandate_models}
            clients = {
                model.id: model
                for model in session.scalars(select(ClientModel).where(ClientModel.id.in_(client_ids))).all()
            }
        return [self._mandate_from_model(model, clients[model.client_ref_id]) for model in mandate_models]

    async def list_bindings(self, mandate_key: str | None = None) -> Sequence[MandateAccountBinding]:
        context = await self.ensure_active_context()
        target_key = mandate_key or context.mandate.mandate_key
        with self._session_factory() as session:
            mandate_model = session.scalar(
                select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == target_key)
            )
            if mandate_model is None:
                return []
            binding_models = session.scalars(
                select(MandateAccountBindingModel)
                .where(MandateAccountBindingModel.strategy_mandate_ref_id == mandate_model.id)
                .order_by(MandateAccountBindingModel.binding_key.asc())
            ).all()
            accounts = {
                model.id: model
                for model in session.scalars(
                    select(VenueAccountModel).where(
                        VenueAccountModel.id.in_({model.venue_account_ref_id for model in binding_models})
                    )
                ).all()
            }
        return [self._binding_from_model(model, mandate_model, accounts[model.venue_account_ref_id]) for model in binding_models]

    async def list_effective_component_configs(
        self,
        binding_key: str | None = None,
    ) -> Sequence[StrategyComponentConfig]:
        context = await self.ensure_active_context()
        target_binding_key = binding_key or (context.bindings[0].binding.binding_key if context.bindings else None)
        if target_binding_key is None:
            return []
        with self._session_factory() as session:
            binding_model = session.scalar(
                select(MandateAccountBindingModel).where(MandateAccountBindingModel.binding_key == target_binding_key)
            )
            if binding_model is None:
                return []
            mandate_model = session.scalar(
                select(StrategyMandateModel).where(StrategyMandateModel.id == binding_model.strategy_mandate_ref_id)
            )
            assert mandate_model is not None
            return self._load_effective_component_configs(session, mandate_model, binding_model)

    async def create_mandate(
        self,
        *,
        mandate_key: str,
        family: StrategyFamily,
        enabled: bool = True,
        notes: str | None = None,
    ) -> StrategyMandate:
        with self._session_factory() as session:
            client_model = self._ensure_client(session)
            model = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
            if model is None:
                model = StrategyMandateModel(
                    mandate_key=mandate_key,
                    client_ref_id=client_model.id,
                    family=family,
                    enabled=enabled,
                    allow_builder_deployed_for_strategy=self.settings.universe_policy.allow_builder_deployed_for_strategy,
                    allow_builder_deployed_for_trading=self.settings.universe_policy.allow_builder_deployed_for_trading,
                    notes=notes,
                    metadata_json={},
                )
                session.add(model)
                session.flush()
            self._ensure_mandate_market_data_source_policy(session, model)
            self._ensure_mandate_default_components(session, model)
            session.commit()
            return self._mandate_from_model(model, client_model)

    async def bind_account(
        self,
        *,
        mandate_key: str,
        venue_account_key: str,
        binding_key: str | None = None,
        enabled: bool = True,
        strategy_eligible: bool = True,
        routing_eligible: bool = True,
        trading_enabled: bool = True,
        target_recommendation_priority: int | None = None,
        clear_target_recommendation_priority: bool = False,
    ) -> MandateAccountBinding:
        if clear_target_recommendation_priority and target_recommendation_priority is not None:
            raise ValueError(
                "clear_target_recommendation_priority cannot be true when "
                "target_recommendation_priority is provided."
            )
        with self._session_factory() as session:
            mandate_model = session.scalar(
                select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key)
            )
            account_model = session.scalar(
                select(VenueAccountModel).where(VenueAccountModel.venue_account_key == venue_account_key)
            )
            if mandate_model is None or account_model is None:
                raise ValueError("Mandate or venue account not found.")
            model = self._ensure_binding(
                session,
                mandate_model=mandate_model,
                account_model=account_model,
                binding_key=binding_key,
                enabled=enabled,
                strategy_eligible=strategy_eligible,
                routing_eligible=routing_eligible,
                trading_enabled=trading_enabled,
                target_recommendation_priority=target_recommendation_priority,
                clear_target_recommendation_priority=clear_target_recommendation_priority,
            )
            session.commit()
            return self._binding_from_model(model, mandate_model, account_model)

    def _ensure_client(self, session: Any) -> ClientModel:
        client_key = self.settings.runtime_selection.active_client_key
        model = session.scalar(select(ClientModel).where(ClientModel.client_key == client_key))
        if model is None:
            model = ClientModel(
                client_key=client_key,
                display_name=_display_name_from_key(client_key),
                is_active=True,
            )
            session.add(model)
            session.flush()
        else:
            model.display_name = model.display_name or _display_name_from_key(client_key)
            model.is_active = True
        return model

    def _ensure_discovered_accounts(self, session: Any, client_model: ClientModel) -> None:
        addresses: set[str] = set()
        for model_cls in (ExchangeAccountSnapshotModel, PositionModel, SubmittedOrderModel, FillModel):
            values = session.scalars(
                select(model_cls.account_address).where(
                    model_cls.environment == self.settings.app.environment,
                    model_cls.venue == self.settings.exchange.venue,
                    model_cls.account_address.is_not(None),
                )
            ).all()
            for value in values:
                if value:
                    addresses.add(str(value))
        for address in sorted(addresses):
            account_key = self._derived_account_key(address)
            model = session.scalar(
                select(VenueAccountModel).where(VenueAccountModel.venue_account_key == account_key)
            )
            if model is None:
                session.add(
                    VenueAccountModel(
                        venue_account_key=account_key,
                        client_ref_id=client_model.id,
                        venue=self.settings.exchange.venue,
                        environment=self.settings.app.environment,
                        venue_native_account_id=address,
                        account_address=address,
                        account_label="imported",
                        subaccount_label=None,
                        credentials_ref=None,
                        wallet_ref=None,
                        is_active=True,
                        trading_enabled=True,
                        raw_metadata={"discovered_from_existing_data": True},
                    )
                )

    def _ensure_focused_account(self, session: Any, client_model: ClientModel) -> VenueAccountModel:
        selection = self.settings.runtime_selection
        account_key = selection.focused_account_key or self.settings.default_account_key
        account_address = self.settings.exchange.account_address or None
        model = session.scalar(select(VenueAccountModel).where(VenueAccountModel.venue_account_key == account_key))
        if model is None and account_address:
            model = session.scalar(
                select(VenueAccountModel).where(
                    VenueAccountModel.client_ref_id == client_model.id,
                    VenueAccountModel.venue == self.settings.exchange.venue,
                    VenueAccountModel.environment == self.settings.app.environment,
                    VenueAccountModel.account_address == account_address,
                )
            )
        native_id = account_address or account_key
        if model is None:
            model = VenueAccountModel(
                venue_account_key=account_key,
                client_ref_id=client_model.id,
                venue=self.settings.exchange.venue,
                environment=self.settings.app.environment,
                venue_native_account_id=native_id,
                account_address=account_address,
                account_label=self.settings.exchange.account_label,
                subaccount_label=None,
                credentials_ref=self.settings.exchange.credentials_ref or None,
                wallet_ref=self.settings.exchange.wallet_ref or None,
                is_active=True,
                trading_enabled=self.settings.risk.trading_enabled,
                raw_metadata={"bootstrapped_from_settings": True},
            )
            session.add(model)
            session.flush()
        else:
            model.client_ref_id = client_model.id
            model.venue = self.settings.exchange.venue
            model.environment = self.settings.app.environment
            model.venue_native_account_id = native_id
            model.account_address = account_address or model.account_address
            model.account_label = self.settings.exchange.account_label or model.account_label
            model.credentials_ref = self.settings.exchange.credentials_ref or model.credentials_ref
            model.wallet_ref = self.settings.exchange.wallet_ref or model.wallet_ref
            model.is_active = True
            model.trading_enabled = self.settings.risk.trading_enabled
        return model

    def _ensure_active_mandate(self, session: Any, client_model: ClientModel) -> StrategyMandateModel:
        mandate_key = self.settings.runtime_selection.active_mandate_key
        model = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        if model is None:
            model = StrategyMandateModel(
                mandate_key=mandate_key,
                client_ref_id=client_model.id,
                family=StrategyFamily.MONEY_FLOW,
                enabled=self.settings.money_flow.strategy_enabled,
                allow_builder_deployed_for_strategy=self.settings.universe_policy.allow_builder_deployed_for_strategy,
                allow_builder_deployed_for_trading=self.settings.universe_policy.allow_builder_deployed_for_trading,
                notes="Bootstrapped from existing single-process Money Flow runtime settings.",
                metadata_json={"bootstrapped_from_settings": True},
            )
            session.add(model)
            session.flush()
        else:
            model.client_ref_id = client_model.id
            model.family = StrategyFamily.MONEY_FLOW
            model.enabled = self.settings.money_flow.strategy_enabled
            model.allow_builder_deployed_for_strategy = self.settings.universe_policy.allow_builder_deployed_for_strategy
            model.allow_builder_deployed_for_trading = self.settings.universe_policy.allow_builder_deployed_for_trading
        return model

    def _ensure_mandate_binding(
        self,
        session: Any,
        mandate_model: StrategyMandateModel,
        account_model: VenueAccountModel,
    ) -> MandateAccountBindingModel:
        return self._ensure_binding(
            session,
            mandate_model=mandate_model,
            account_model=account_model,
            binding_key=None,
            enabled=True,
            strategy_eligible=True,
            routing_eligible=True,
            trading_enabled=account_model.trading_enabled,
            target_recommendation_priority=None,
        )

    def _ensure_binding(
        self,
        session: Any,
        *,
        mandate_model: StrategyMandateModel,
        account_model: VenueAccountModel,
        binding_key: str | None,
        enabled: bool,
        strategy_eligible: bool,
        routing_eligible: bool,
        trading_enabled: bool,
        target_recommendation_priority: int | None = None,
        clear_target_recommendation_priority: bool = False,
    ) -> MandateAccountBindingModel:
        resolved_binding_key = binding_key or f"{mandate_model.mandate_key}::{account_model.venue_account_key}"
        model = session.scalar(
            select(MandateAccountBindingModel).where(MandateAccountBindingModel.binding_key == resolved_binding_key)
        )
        if model is None:
            model = session.scalar(
                select(MandateAccountBindingModel).where(
                    MandateAccountBindingModel.strategy_mandate_ref_id == mandate_model.id,
                    MandateAccountBindingModel.venue_account_ref_id == account_model.id,
                )
            )
        if model is None:
            model = MandateAccountBindingModel(
                binding_key=resolved_binding_key,
                strategy_mandate_ref_id=mandate_model.id,
                venue_account_ref_id=account_model.id,
                enabled=enabled,
                strategy_eligible=strategy_eligible,
                routing_eligible=routing_eligible,
                trading_enabled=trading_enabled,
                target_recommendation_priority=target_recommendation_priority,
                allow_builder_deployed_for_strategy=mandate_model.allow_builder_deployed_for_strategy,
                allow_builder_deployed_for_trading=mandate_model.allow_builder_deployed_for_trading,
                notes=None,
                metadata_json={},
            )
            session.add(model)
            session.flush()
        else:
            model.binding_key = resolved_binding_key
            model.strategy_mandate_ref_id = mandate_model.id
            model.venue_account_ref_id = account_model.id
            model.enabled = enabled
            model.strategy_eligible = strategy_eligible
            model.routing_eligible = routing_eligible
            model.trading_enabled = trading_enabled
            if clear_target_recommendation_priority:
                model.target_recommendation_priority = None
            elif target_recommendation_priority is not None:
                model.target_recommendation_priority = target_recommendation_priority
        return model

    def _ensure_mandate_default_components(
        self,
        session: Any,
        mandate_model: StrategyMandateModel,
    ) -> list[StrategyComponentConfigModel]:
        family_sleeves = {model.sleeve_id: model for model in self.settings.money_flow.sleeves}
        components: list[StrategyComponentConfigModel] = []
        for sleeve in self.settings.components:
            family_sleeve = family_sleeves[sleeve.sleeve_id]
            model = session.scalar(
                select(StrategyComponentConfigModel).where(
                    StrategyComponentConfigModel.strategy_mandate_ref_id == mandate_model.id,
                    StrategyComponentConfigModel.binding_scope_key == MANDATE_DEFAULT_SCOPE,
                    StrategyComponentConfigModel.component_key == sleeve.sleeve_id,
                )
            )
            payload = family_sleeve.model_dump(mode="json")
            if model is None:
                model = StrategyComponentConfigModel(
                    strategy_mandate_ref_id=mandate_model.id,
                    mandate_account_binding_ref_id=None,
                    binding_scope_key=MANDATE_DEFAULT_SCOPE,
                    component_key=sleeve.sleeve_id,
                    component_type="money_flow_sleeve",
                    timeframe=sleeve.timeframe,
                    enabled=sleeve.enabled,
                    capital_allocation_pct=Decimal(str(sleeve.capital_allocation_pct)),
                    max_open_risk_pct=Decimal(str(sleeve.max_open_risk_pct)),
                    parameters_json=payload,
                    metadata_json={"origin": "mandate_default"},
                    is_override=False,
                )
                session.add(model)
                session.flush()
            components.append(model)
        return components

    def _ensure_binding_component_overrides(
        self,
        session: Any,
        mandate_model: StrategyMandateModel,
        account_model: VenueAccountModel,
    ) -> None:
        binding_model = session.scalar(
            select(MandateAccountBindingModel).where(
                MandateAccountBindingModel.strategy_mandate_ref_id == mandate_model.id,
                MandateAccountBindingModel.venue_account_ref_id == account_model.id,
            )
        )
        if binding_model is None:
            return
        default_components = {
            model.component_key: model
            for model in session.scalars(
                select(StrategyComponentConfigModel).where(
                    StrategyComponentConfigModel.strategy_mandate_ref_id == mandate_model.id,
                    StrategyComponentConfigModel.binding_scope_key == MANDATE_DEFAULT_SCOPE,
                )
            ).all()
        }
        family_sleeves = {model.sleeve_id: model for model in self.settings.money_flow.sleeves}
        for sleeve in self.settings.components:
            family_sleeve = family_sleeves[sleeve.sleeve_id]
            default_model = default_components[sleeve.sleeve_id]
            payload = family_sleeve.model_dump(mode="json")
            differs_from_default = (
                default_model.enabled != sleeve.enabled
                or default_model.timeframe != sleeve.timeframe
                or default_model.capital_allocation_pct != Decimal(str(sleeve.capital_allocation_pct))
                or default_model.max_open_risk_pct != Decimal(str(sleeve.max_open_risk_pct))
                or dict(default_model.parameters_json or {}) != payload
            )
            existing_override = session.scalar(
                select(StrategyComponentConfigModel).where(
                    StrategyComponentConfigModel.strategy_mandate_ref_id == mandate_model.id,
                    StrategyComponentConfigModel.mandate_account_binding_ref_id == binding_model.id,
                    StrategyComponentConfigModel.component_key == sleeve.sleeve_id,
                )
            )
            if not differs_from_default:
                continue
            if existing_override is None:
                session.add(
                    StrategyComponentConfigModel(
                        strategy_mandate_ref_id=mandate_model.id,
                        mandate_account_binding_ref_id=binding_model.id,
                        binding_scope_key=binding_model.binding_key,
                        component_key=sleeve.sleeve_id,
                        component_type="money_flow_sleeve",
                        timeframe=sleeve.timeframe,
                        enabled=sleeve.enabled,
                        capital_allocation_pct=Decimal(str(sleeve.capital_allocation_pct)),
                        max_open_risk_pct=Decimal(str(sleeve.max_open_risk_pct)),
                        parameters_json=payload,
                        metadata_json={"origin": "binding_override"},
                        is_override=True,
                        source_component_config_ref_id=default_model.id,
                    )
                )
            else:
                existing_override.binding_scope_key = binding_model.binding_key
                existing_override.component_type = "money_flow_sleeve"
                existing_override.timeframe = sleeve.timeframe
                existing_override.enabled = sleeve.enabled
                existing_override.capital_allocation_pct = Decimal(str(sleeve.capital_allocation_pct))
                existing_override.max_open_risk_pct = Decimal(str(sleeve.max_open_risk_pct))
                existing_override.parameters_json = payload
                existing_override.is_override = True
                existing_override.source_component_config_ref_id = default_model.id

    def _ensure_mandate_market_data_source_policy(
        self,
        session: Any,
        mandate_model: StrategyMandateModel,
    ) -> MandateMarketDataSourcePolicyModel:
        policy_model = session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == mandate_model.id
            )
        )
        configured_policy = self.settings.mandate_market_data_source_policy
        if policy_model is None:
            policy_model = MandateMarketDataSourcePolicyModel(
                strategy_mandate_ref_id=mandate_model.id,
                source_mode=configured_policy.source_mode,
                source_venue=configured_policy.source_venue,
                market_type=configured_policy.market_type,
                product_type=configured_policy.product_type,
                instrument_resolution_mode=configured_policy.instrument_resolution_mode,
                notes="bootstrapped_from_runtime_settings",
                metadata_json={},
            )
            session.add(policy_model)
            session.flush()
        else:
            policy_model.source_mode = policy_model.source_mode or configured_policy.source_mode
            policy_model.source_venue = policy_model.source_venue or configured_policy.source_venue
            policy_model.market_type = policy_model.market_type or configured_policy.market_type
            policy_model.product_type = policy_model.product_type or configured_policy.product_type
            policy_model.instrument_resolution_mode = (
                policy_model.instrument_resolution_mode or configured_policy.instrument_resolution_mode
            )
            policy_model.notes = policy_model.notes or "bootstrapped_from_runtime_settings"
        return policy_model

    def _backfill_active_context(
        self,
        session: Any,
        client_model: ClientModel,
        mandate_model: StrategyMandateModel,
    ) -> None:
        binding_models = session.scalars(
            select(MandateAccountBindingModel).where(
                MandateAccountBindingModel.strategy_mandate_ref_id == mandate_model.id
            )
        ).all()
        if not binding_models:
            return
        focused_binding = sorted(binding_models, key=lambda item: item.binding_key)[0]
        focused_account = session.scalar(
            select(VenueAccountModel).where(VenueAccountModel.id == focused_binding.venue_account_ref_id)
        )
        assert focused_account is not None

        session.execute(
            update(PositionModel)
            .where(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.venue == self.settings.exchange.venue,
                PositionModel.venue_account_ref_id.is_(None),
                (
                    PositionModel.account_address == focused_account.account_address
                    if focused_account.account_address
                    else PositionModel.account_address.is_(None)
                ),
            )
            .values(venue_account_ref_id=focused_account.id)
        )
        session.execute(
            update(SubmittedOrderModel)
            .where(
                SubmittedOrderModel.environment == self.settings.app.environment,
                SubmittedOrderModel.venue == self.settings.exchange.venue,
                SubmittedOrderModel.venue_account_ref_id.is_(None),
                (
                    SubmittedOrderModel.account_address == focused_account.account_address
                    if focused_account.account_address
                    else SubmittedOrderModel.account_address.is_(None)
                ),
            )
            .values(venue_account_ref_id=focused_account.id)
        )
        session.execute(
            update(PortfolioSnapshotModel)
            .where(
                PortfolioSnapshotModel.environment == self.settings.app.environment,
                PortfolioSnapshotModel.venue_account_ref_id.is_(None),
            )
            .values(venue_account_ref_id=focused_account.id)
        )
        session.execute(
            update(FillModel)
            .where(
                FillModel.environment == self.settings.app.environment,
                FillModel.venue == self.settings.exchange.venue,
                FillModel.venue_account_ref_id.is_(None),
                (
                    FillModel.account_address == focused_account.account_address
                    if focused_account.account_address
                    else FillModel.account_address.is_(None)
                ),
            )
            .values(venue_account_ref_id=focused_account.id)
        )
        session.execute(
            update(ExchangeAccountSnapshotModel)
            .where(
                ExchangeAccountSnapshotModel.environment == self.settings.app.environment,
                ExchangeAccountSnapshotModel.venue == self.settings.exchange.venue,
                ExchangeAccountSnapshotModel.venue_account_ref_id.is_(None),
                (
                    ExchangeAccountSnapshotModel.account_address == focused_account.account_address
                    if focused_account.account_address
                    else ExchangeAccountSnapshotModel.account_address.is_(None)
                ),
            )
            .values(venue_account_ref_id=focused_account.id)
        )

        position_ids = session.scalars(
            select(PositionModel.position_id).where(
                PositionModel.environment == self.settings.app.environment,
                PositionModel.venue == self.settings.exchange.venue,
                PositionModel.venue_account_ref_id == focused_account.id,
            )
        ).all()
        if position_ids:
            session.execute(
                update(PositionAttributionOverlayModel)
                .where(
                    PositionAttributionOverlayModel.environment == self.settings.app.environment,
                    PositionAttributionOverlayModel.venue == self.settings.exchange.venue,
                    PositionAttributionOverlayModel.venue_account_ref_id.is_(None),
                    PositionAttributionOverlayModel.position_id.in_(position_ids),
                )
                .values(venue_account_ref_id=focused_account.id)
            )

        session.execute(
            update(SignalEventModel)
            .where(
                SignalEventModel.environment == self.settings.app.environment,
                SignalEventModel.family == StrategyFamily.MONEY_FLOW,
                SignalEventModel.strategy_mandate_ref_id.is_(None),
            )
            .values(
                client_ref_id=client_model.id,
                strategy_mandate_ref_id=mandate_model.id,
                mandate_key=mandate_model.mandate_key,
                mandate_account_binding_ref_id=focused_binding.id,
                binding_key=focused_binding.binding_key,
                venue_account_ref_id=focused_account.id,
                component_key=SignalEventModel.sleeve_id,
            )
        )
        session.execute(
            update(StrategyDecisionModel)
            .where(
                StrategyDecisionModel.environment == self.settings.app.environment,
                StrategyDecisionModel.family == StrategyFamily.MONEY_FLOW,
                StrategyDecisionModel.strategy_mandate_ref_id.is_(None),
            )
            .values(
                client_ref_id=client_model.id,
                strategy_mandate_ref_id=mandate_model.id,
                mandate_key=mandate_model.mandate_key,
                mandate_account_binding_ref_id=focused_binding.id,
                binding_key=focused_binding.binding_key,
                venue_account_ref_id=focused_account.id,
                component_key=StrategyDecisionModel.sleeve_id,
            )
        )
        session.execute(
            update(OrderIntentModel)
            .where(
                OrderIntentModel.environment == self.settings.app.environment,
                OrderIntentModel.strategy_mandate_ref_id.is_(None),
            )
            .values(
                client_ref_id=client_model.id,
                strategy_mandate_ref_id=mandate_model.id,
                mandate_account_binding_ref_id=focused_binding.id,
                venue_account_ref_id=focused_account.id,
                component_key=OrderIntentModel.sleeve_id,
            )
        )

    def _derived_account_key(self, account_address: str | None) -> str:
        suffix = (
            _slug(self.settings.exchange.account_label)
            if not account_address and self.settings.exchange.account_label
            else _slug(account_address[-8:] if account_address else "primary")
        )
        return f"{self.settings.exchange.venue}_{self.settings.app.environment.value}_{suffix}"

    def _client_from_model(self, model: ClientModel) -> Client:
        return Client(
            client_key=model.client_key,
            client_ref_id=model.id,
            display_name=model.display_name,
            is_active=model.is_active,
        )

    def _venue_account_from_model(self, model: VenueAccountModel, client_model: ClientModel) -> VenueAccount:
        return VenueAccount(
            venue_account_key=model.venue_account_key,
            venue_account_ref_id=model.id,
            client_key=client_model.client_key,
            client_ref_id=client_model.id,
            venue=model.venue,
            environment=model.environment,
            venue_native_account_id=model.venue_native_account_id,
            account_address=model.account_address,
            account_label=model.account_label,
            subaccount_label=model.subaccount_label,
            credentials_ref=model.credentials_ref,
            wallet_ref=model.wallet_ref,
            is_active=model.is_active,
            trading_enabled=model.trading_enabled,
        )

    def _mandate_from_model(self, model: StrategyMandateModel, client_model: ClientModel) -> StrategyMandate:
        return StrategyMandate(
            mandate_key=model.mandate_key,
            mandate_ref_id=model.id,
            client_key=client_model.client_key,
            client_ref_id=client_model.id,
            family=model.family,
            enabled=model.enabled,
            allow_builder_deployed_for_strategy=model.allow_builder_deployed_for_strategy,
            allow_builder_deployed_for_trading=model.allow_builder_deployed_for_trading,
            notes=model.notes,
            metadata=dict(model.metadata_json or {}),
        )

    def _source_policy_from_model(
        self,
        model: MandateMarketDataSourcePolicyModel,
        mandate_model: StrategyMandateModel,
    ) -> MandateMarketDataSourcePolicy:
        runtime_exchange_venue = self.settings.exchange.venue
        return MandateMarketDataSourcePolicy(
            policy_ref_id=model.id,
            strategy_mandate_ref_id=mandate_model.id,
            mandate_key=mandate_model.mandate_key,
            source_mode=model.source_mode,
            source_venue=model.source_venue,
            market_type=model.market_type,
            product_type=model.product_type,
            instrument_resolution_mode=model.instrument_resolution_mode,
            runtime_exchange_venue=runtime_exchange_venue,
            runtime_exchange_matches_source=(model.source_venue == runtime_exchange_venue),
            notes=model.notes,
            metadata=dict(model.metadata_json or {}),
        )

    def _binding_from_model(
        self,
        model: MandateAccountBindingModel,
        mandate_model: StrategyMandateModel,
        account_model: VenueAccountModel,
    ) -> MandateAccountBinding:
        return MandateAccountBinding(
            binding_key=model.binding_key,
            binding_ref_id=model.id,
            strategy_mandate_ref_id=mandate_model.id,
            mandate_key=mandate_model.mandate_key,
            venue_account_key=account_model.venue_account_key,
            venue_account_ref_id=account_model.id,
            enabled=model.enabled,
            strategy_eligible=model.strategy_eligible,
            routing_eligible=model.routing_eligible,
            trading_enabled=model.trading_enabled,
            allow_builder_deployed_for_strategy=model.allow_builder_deployed_for_strategy,
            allow_builder_deployed_for_trading=model.allow_builder_deployed_for_trading,
            target_recommendation_priority=model.target_recommendation_priority,
            notes=model.notes,
            metadata=dict(model.metadata_json or {}),
        )

    def _component_config_from_model(self, model: StrategyComponentConfigModel) -> StrategyComponentConfig:
        return StrategyComponentConfig(
            component_config_ref_id=model.id,
            strategy_mandate_ref_id=model.strategy_mandate_ref_id,
            mandate_account_binding_ref_id=model.mandate_account_binding_ref_id,
            component_key=model.component_key,
            component_type=model.component_type,
            timeframe=model.timeframe,
            enabled=model.enabled,
            capital_allocation_pct=model.capital_allocation_pct,
            max_open_risk_pct=model.max_open_risk_pct,
            parameters=dict(model.parameters_json or {}),
            metadata=dict(model.metadata_json or {}),
            is_override=model.is_override,
            source_component_config_ref_id=model.source_component_config_ref_id,
        )

    def _load_effective_component_configs(
        self,
        session: Any,
        mandate_model: StrategyMandateModel,
        binding_model: MandateAccountBindingModel,
    ) -> list[StrategyComponentConfig]:
        default_models = session.scalars(
            select(StrategyComponentConfigModel)
            .where(
                StrategyComponentConfigModel.strategy_mandate_ref_id == mandate_model.id,
                StrategyComponentConfigModel.binding_scope_key == MANDATE_DEFAULT_SCOPE,
            )
            .order_by(StrategyComponentConfigModel.component_key.asc())
        ).all()
        override_models = {
            model.component_key: model
            for model in session.scalars(
                select(StrategyComponentConfigModel).where(
                    StrategyComponentConfigModel.strategy_mandate_ref_id == mandate_model.id,
                    StrategyComponentConfigModel.mandate_account_binding_ref_id == binding_model.id,
                )
            ).all()
        }
        effective_configs: list[StrategyComponentConfig] = []
        for default_model in default_models:
            override_model = override_models.get(default_model.component_key)
            if override_model is None:
                effective = self._component_config_from_model(default_model)
                effective.mandate_account_binding_ref_id = binding_model.id
                effective.metadata = {**effective.metadata, "effective_scope": "binding_inherited_default"}
                effective_configs.append(effective)
                continue
            merged = self._component_config_from_model(override_model)
            merged.source_component_config_ref_id = default_model.id
            merged.metadata = {
                **dict(default_model.metadata_json or {}),
                **dict(override_model.metadata_json or {}),
                "effective_scope": "binding_override",
            }
            effective_configs.append(merged)
        return effective_configs

    def _load_context(self, session: Any, mandate_key: str) -> ActiveMandateContext:
        mandate_model = session.scalar(select(StrategyMandateModel).where(StrategyMandateModel.mandate_key == mandate_key))
        assert mandate_model is not None
        client_model = session.scalar(select(ClientModel).where(ClientModel.id == mandate_model.client_ref_id))
        assert client_model is not None
        source_policy_model = session.scalar(
            select(MandateMarketDataSourcePolicyModel).where(
                MandateMarketDataSourcePolicyModel.strategy_mandate_ref_id == mandate_model.id
            )
        )
        if source_policy_model is None:
            source_policy_model = self._ensure_mandate_market_data_source_policy(session, mandate_model)
        binding_models = session.scalars(
            select(MandateAccountBindingModel)
            .where(MandateAccountBindingModel.strategy_mandate_ref_id == mandate_model.id)
            .order_by(MandateAccountBindingModel.binding_key.asc())
        ).all()
        account_models = {
            model.id: model
            for model in session.scalars(
                select(VenueAccountModel).where(
                    VenueAccountModel.id.in_({binding.venue_account_ref_id for binding in binding_models})
                )
            ).all()
        }
        bindings = [
            ActiveMandateBindingContext(
                binding=self._binding_from_model(binding_model, mandate_model, account_models[binding_model.venue_account_ref_id]),
                venue_account=self._venue_account_from_model(account_models[binding_model.venue_account_ref_id], client_model),
                component_configs=self._load_effective_component_configs(
                    session,
                    mandate_model,
                    binding_model,
                ),
            )
            for binding_model in binding_models
        ]
        return ActiveMandateContext(
            client=self._client_from_model(client_model),
            mandate=self._mandate_from_model(mandate_model, client_model),
            market_data_source_policy=self._source_policy_from_model(source_policy_model, mandate_model),
            bindings=bindings,
        )


def money_flow_sleeve_config_from_component(config: StrategyComponentConfig) -> MoneyFlowSleeveConfig:
    payload = dict(config.parameters)
    payload.setdefault("sleeve_id", config.component_key)
    if config.timeframe is not None:
        payload.setdefault("timeframe", config.timeframe)
    payload.setdefault("enabled", config.enabled)
    return MoneyFlowSleeveConfig.model_validate(payload)
