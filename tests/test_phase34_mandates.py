from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from core.domain.enums import (
    AttributionStatus,
    DecisionAction,
    Environment,
    OrderSide,
    PositionStatus,
    StrategyFamily,
    Timeframe,
)
from db.models import (
    ClientModel,
    MandateAccountBindingModel,
    PositionModel,
    StrategyComponentConfigModel,
    StrategyDecisionModel,
    StrategyMandateModel,
    VenueAccountModel,
)
from services.indicators.service import DefaultIndicatorService
from services.portfolio.service import DefaultPortfolioService
from services.runtime.context import DefaultRuntimeContextService
from services.strategy.engine import MandateStrategyEngine
from tests.test_phase3_strategy import (
    bearish_break_closes,
    build_settings,
    build_test_session_factory,
    seed_candles,
    seed_open_position,
    seed_symbol,
)


def test_runtime_context_bootstraps_default_mandate_hierarchy() -> None:
    settings = build_settings()
    session_factory = build_test_session_factory()

    runtime_context = DefaultRuntimeContextService(settings, session_factory=session_factory)
    context = asyncio.run(runtime_context.ensure_active_context())

    assert context.client.client_key == settings.runtime_selection.active_client_key
    assert context.mandate.mandate_key == settings.runtime_selection.active_mandate_key
    assert len(context.bindings) == 1
    assert [item.component_key for item in context.bindings[0].component_configs] == [
        "sleeve_15m",
        "sleeve_1h",
        "sleeve_4h",
    ]

    with session_factory() as session:
        assert session.scalar(select(ClientModel.client_key)) == settings.runtime_selection.active_client_key
        assert session.scalar(select(VenueAccountModel.venue_account_key)) == settings.runtime_selection.focused_account_key
        assert session.scalar(select(StrategyMandateModel.mandate_key)) == settings.runtime_selection.active_mandate_key
        assert session.scalar(select(MandateAccountBindingModel.binding_key)) is not None


def test_one_mandate_can_bind_multiple_accounts() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)

    mandate_key = "money_flow::client_group"
    settings_a = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_a",
        ACTIVE_ACCOUNT_KEY="acct_a_key",
        ACTIVE_MANDATE_KEY=mandate_key,
    )
    settings_b = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_b",
        EXCHANGE_ACCOUNT_LABEL="secondary",
        ACTIVE_ACCOUNT_KEY="acct_b_key",
        ACTIVE_MANDATE_KEY=mandate_key,
    )

    runtime_a = DefaultRuntimeContextService(settings_a, session_factory=session_factory)
    runtime_b = DefaultRuntimeContextService(settings_b, session_factory=session_factory)
    context_a = asyncio.run(runtime_a.ensure_active_context())
    context_b = asyncio.run(runtime_b.ensure_active_context())

    assert context_a.mandate.mandate_key == mandate_key
    assert context_b.mandate.mandate_key == mandate_key
    assert len(context_b.bindings) == 2

    with session_factory() as session:
        session.add_all(
            [
                PositionModel(
                    environment=Environment.TESTNET,
                    position_id="pos-acct-a",
                    exchange_position_key="btc-one-way-a",
                    account_position_key="acct_a:btc:one_way",
                    venue_account_ref_id=context_a.bindings[0].venue_account.venue_account_ref_id,
                    sleeve_id=None,
                    venue="hyperliquid",
                    account_address="acct_a",
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=symbol_id,
                    symbol="BTC",
                    side=OrderSide.BUY,
                    status=PositionStatus.OPEN,
                    attribution_status=AttributionStatus.UNASSIGNED,
                    quantity=Decimal("0.10"),
                    avg_entry_price=Decimal("100"),
                    mark_price=Decimal("101"),
                    unrealized_pnl=Decimal("1"),
                    position_value=Decimal("10.1"),
                    margin_used=Decimal("1"),
                    liquidation_price=Decimal("80"),
                    leverage_type="cross",
                    leverage_value=5,
                    raw_payload={},
                    opened_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
                PositionModel(
                    environment=Environment.TESTNET,
                    position_id="pos-acct-b",
                    exchange_position_key="btc-one-way-b",
                    account_position_key="acct_b:btc:one_way",
                    venue_account_ref_id=context_b.bindings[1].venue_account.venue_account_ref_id,
                    sleeve_id=None,
                    venue="hyperliquid",
                    account_address="acct_b",
                    instrument_ref_id=instrument_ref_id,
                    symbol_id=symbol_id,
                    symbol="BTC",
                    side=OrderSide.BUY,
                    status=PositionStatus.OPEN,
                    attribution_status=AttributionStatus.UNASSIGNED,
                    quantity=Decimal("0.20"),
                    avg_entry_price=Decimal("100"),
                    mark_price=Decimal("102"),
                    unrealized_pnl=Decimal("2"),
                    position_value=Decimal("20.4"),
                    margin_used=Decimal("2"),
                    liquidation_price=Decimal("80"),
                    leverage_type="cross",
                    leverage_value=5,
                    raw_payload={},
                    opened_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
            ]
        )
        session.commit()

    portfolio = DefaultPortfolioService(settings_b, session_factory=session_factory, runtime_context_service=runtime_b)
    positions_a = asyncio.run(
        portfolio.get_open_positions(venue_account_ref_id=context_b.bindings[0].venue_account.venue_account_ref_id)
    )
    positions_b = asyncio.run(
        portfolio.get_open_positions(venue_account_ref_id=context_b.bindings[1].venue_account.venue_account_ref_id)
    )

    assert [position.position_id for position in positions_a] == ["pos-acct-a"]
    assert [position.position_id for position in positions_b] == ["pos-acct-b"]


def test_one_account_can_be_reused_across_multiple_mandates() -> None:
    session_factory = build_test_session_factory()
    settings_a = build_settings(EXCHANGE_ACCOUNT_ADDRESS="acct_shared", ACTIVE_MANDATE_KEY="money_flow::alpha")
    settings_b = build_settings(EXCHANGE_ACCOUNT_ADDRESS="acct_shared", ACTIVE_MANDATE_KEY="money_flow::beta")

    runtime_a = DefaultRuntimeContextService(settings_a, session_factory=session_factory)
    runtime_b = DefaultRuntimeContextService(settings_b, session_factory=session_factory)
    context_a = asyncio.run(runtime_a.ensure_active_context())
    context_b = asyncio.run(runtime_b.ensure_active_context())

    assert context_a.bindings[0].venue_account.venue_account_ref_id == context_b.bindings[0].venue_account.venue_account_ref_id
    assert context_a.mandate.mandate_key != context_b.mandate.mandate_key


def test_one_client_can_own_multiple_mandates() -> None:
    session_factory = build_test_session_factory()
    settings = build_settings(EXCHANGE_ACCOUNT_ADDRESS="acct_shared", ACTIVE_MANDATE_KEY="money_flow::alpha")
    runtime = DefaultRuntimeContextService(settings, session_factory=session_factory)

    asyncio.run(runtime.ensure_active_context())
    asyncio.run(
        runtime.create_mandate(
            mandate_key="money_flow::beta",
            family=StrategyFamily.MONEY_FLOW,
            enabled=True,
        )
    )

    mandates = asyncio.run(runtime.list_mandates(client_key=settings.runtime_selection.active_client_key))
    mandate_keys = {mandate.mandate_key for mandate in mandates}
    assert mandate_keys == {"money_flow::alpha", "money_flow::beta"}


def test_binding_specific_component_overrides_can_differ_within_one_mandate() -> None:
    session_factory = build_test_session_factory()
    mandate_key = "money_flow::shared_mandate"
    settings_primary = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_a",
        ACTIVE_ACCOUNT_KEY="acct_a_key",
        ACTIVE_MANDATE_KEY=mandate_key,
    )
    settings_secondary = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_b",
        EXCHANGE_ACCOUNT_LABEL="secondary",
        ACTIVE_ACCOUNT_KEY="acct_b_key",
        ACTIVE_MANDATE_KEY=mandate_key,
        SLEEVE_15M_ENABLED=False,
    )

    runtime_primary = DefaultRuntimeContextService(settings_primary, session_factory=session_factory)
    runtime_secondary = DefaultRuntimeContextService(settings_secondary, session_factory=session_factory)

    context_primary = asyncio.run(runtime_primary.ensure_active_context())
    context_secondary = asyncio.run(runtime_secondary.ensure_active_context())

    primary_components = {
        component.component_key: component
        for component in context_primary.bindings[0].component_configs
    }
    secondary_binding = next(
        binding for binding in context_secondary.bindings if binding.venue_account.account_address == "acct_b"
    )
    secondary_components = {
        component.component_key: component
        for component in secondary_binding.component_configs
    }

    assert primary_components["sleeve_15m"].enabled is True
    assert secondary_components["sleeve_15m"].enabled is False
    assert secondary_components["sleeve_15m"].is_override is True

    with session_factory() as session:
        override = session.scalar(
            select(StrategyComponentConfigModel).where(
                StrategyComponentConfigModel.mandate_account_binding_ref_id == secondary_binding.binding.binding_ref_id,
                StrategyComponentConfigModel.component_key == "sleeve_15m",
            )
        )
    assert override is not None


def test_strategy_evaluation_is_bound_to_mandate_binding_context() -> None:
    session_factory = build_test_session_factory()
    instrument_ref_id, symbol_id, _ = seed_symbol(session_factory)
    seed_candles(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        timeframe=Timeframe.H4,
        closes=bearish_break_closes(),
    )

    settings_a = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_a",
        ACTIVE_ACCOUNT_KEY="acct_a_key",
        ACTIVE_MANDATE_KEY="money_flow::shared_mandate",
    )
    settings_b = build_settings(
        EXCHANGE_ACCOUNT_ADDRESS="acct_b",
        EXCHANGE_ACCOUNT_LABEL="secondary",
        ACTIVE_ACCOUNT_KEY="acct_b_key",
        ACTIVE_MANDATE_KEY="money_flow::shared_mandate",
    )

    runtime_a = DefaultRuntimeContextService(settings_a, session_factory=session_factory)
    runtime_b = DefaultRuntimeContextService(settings_b, session_factory=session_factory)
    asyncio.run(runtime_a.ensure_active_context())
    context = asyncio.run(runtime_b.ensure_active_context())

    seed_open_position(
        session_factory,
        instrument_ref_id=instrument_ref_id,
        symbol_id=symbol_id,
        symbol="BTC",
        quantity=Decimal("0.05"),
        avg_entry_price=Decimal("100"),
        mark_price=Decimal("99"),
    )
    with session_factory() as session:
        position = session.scalar(select(PositionModel).where(PositionModel.position_id == "pos-BTC"))
        assert position is not None
        binding_a = next(binding for binding in context.bindings if binding.venue_account.account_address == "acct_a")
        position.position_id = "pos-acct-a-btc"
        position.account_address = "acct_a"
        position.venue_account_ref_id = binding_a.venue_account.venue_account_ref_id
        binding_b = next(binding for binding in context.bindings if binding.venue_account.account_address == "acct_b")
        session.add(
            PositionModel(
                environment=Environment.TESTNET,
                position_id="pos-acct-b-btc",
                exchange_position_key="btc-b",
                account_position_key="acct_b:btc:one_way",
                venue_account_ref_id=binding_b.venue_account.venue_account_ref_id,
                sleeve_id=None,
                venue="hyperliquid",
                account_address="acct_b",
                instrument_ref_id=instrument_ref_id,
                symbol_id=symbol_id,
                symbol="BTC",
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                attribution_status=AttributionStatus.UNASSIGNED,
                quantity=Decimal("0.07"),
                avg_entry_price=Decimal("100"),
                mark_price=Decimal("99"),
                unrealized_pnl=Decimal("-0.07"),
                position_value=Decimal("6.93"),
                margin_used=Decimal("1"),
                liquidation_price=Decimal("80"),
                leverage_type="cross",
                leverage_value=5,
                raw_payload={},
                opened_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        session.commit()

    indicator = DefaultIndicatorService(settings_b, session_factory=session_factory)
    asyncio.run(indicator.refresh_snapshots(instrument_ref_id, "BTC", "hyperliquid", Timeframe.H4.value))

    engine = MandateStrategyEngine(
        settings=settings_b,
        session_factory=session_factory,
        runtime_context_service=runtime_b,
    )

    results = asyncio.run(engine.evaluate_sleeve("sleeve_4h", symbols=["BTC"]))

    assert len(results) == 2
    assert {result.decision.binding_key for result in results} == {
        binding.binding.binding_key for binding in context.bindings
    }
    assert {result.decision.mandate_key for result in results} == {context.mandate.mandate_key}
    assert {result.decision.action for result in results} == {DecisionAction.CLOSE}

    with session_factory() as session:
        decisions = session.scalars(select(StrategyDecisionModel).order_by(StrategyDecisionModel.binding_key.asc())).all()
    assert len(decisions) == 2
    assert {decision.binding_key for decision in decisions} == {
        binding.binding.binding_key for binding in context.bindings
    }
