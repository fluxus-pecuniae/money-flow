from core.config.settings import AppSettings, get_settings
from core.domain.enums import Environment, InstrumentResolutionMode, MarketDataSourceMode, Venue


def test_settings_load_default_sleeves() -> None:
    settings = get_settings()
    assert [s.sleeve_id for s in settings.sleeves] == ["sleeve_15m", "sleeve_1h", "sleeve_4h"]
    assert [component.sleeve_id for component in settings.components] == [
        "sleeve_15m",
        "sleeve_1h",
        "sleeve_4h",
    ]


def test_default_universe_policy() -> None:
    settings = get_settings()
    assert settings.universe_policy.include_standard_perp_universe is True
    assert settings.universe_policy.include_builder_deployed_in_catalog is True
    assert settings.universe_policy.allow_builder_deployed_for_strategy is False
    assert settings.universe_policy.allow_builder_deployed_for_trading is False


def test_testnet_profile_loads() -> None:
    settings = AppSettings(APP_ENV=Environment.TESTNET, EXCHANGE_USE_TESTNET=True)
    assert settings.profile.environment == Environment.TESTNET
    assert settings.exchange.use_testnet is True


def test_live_profile_loads() -> None:
    settings = AppSettings(APP_ENV=Environment.LIVE, EXCHANGE_USE_TESTNET=False)
    assert settings.profile.environment == Environment.LIVE
    assert settings.exchange.use_testnet is False


def test_money_flow_config_loads() -> None:
    settings = get_settings()
    assert settings.money_flow.strategy_enabled is True
    assert [s.sleeve_id for s in settings.money_flow.sleeves] == ["sleeve_15m", "sleeve_1h", "sleeve_4h"]


def test_runtime_selection_defaults_are_explicit() -> None:
    settings = AppSettings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE="hyperliquid",
        EXCHANGE_ACCOUNT_ADDRESS="0xabc12345",
        EXCHANGE_ACCOUNT_LABEL="primary",
    )
    assert settings.runtime_selection.active_client_key == "default_client"
    assert settings.runtime_selection.focused_account_key is not None
    assert settings.runtime_selection.focused_account_key.startswith("hyperliquid_testnet_")
    assert settings.runtime_selection.active_mandate_key.startswith("money_flow::")


def test_default_mandate_market_data_source_policy_is_explicit() -> None:
    settings = AppSettings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE="hyperliquid",
        EXCHANGE_ACCOUNT_ADDRESS="0xabc12345",
        EXCHANGE_ACCOUNT_LABEL="primary",
    )
    policy = settings.mandate_market_data_source_policy
    assert policy.source_mode == MarketDataSourceMode.SINGLE_VENUE
    assert policy.source_venue == "hyperliquid"
    assert policy.instrument_resolution_mode == InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS
    assert policy.market_type is None
    assert policy.product_type is None


def test_runtime_selection_does_not_fall_back_to_legacy_deployment_key() -> None:
    settings = AppSettings(
        APP_ENV=Environment.TESTNET,
        EXCHANGE_VENUE="hyperliquid",
        EXCHANGE_ACCOUNT_ADDRESS="0xabc12345",
        EXCHANGE_ACCOUNT_LABEL="primary",
        ACTIVE_DEPLOYMENT_KEY="legacy::deployment",
    )
    assert settings.runtime_selection.active_mandate_key == settings.default_mandate_key


def test_multi_venue_integrations_default_to_safe_modes() -> None:
    settings = get_settings()
    integrations = settings.venue_integrations
    assert set(integrations) >= {
        Venue.HYPERLIQUID,
        Venue.ASTER,
        Venue.BINANCE,
        Venue.OKX,
        Venue.COINBASE_ADVANCED_TRADE,
        Venue.KRAKEN,
    }
    assert integrations[Venue.ASTER].read_only_mode is True
    assert integrations[Venue.ASTER].dry_run_mode is True
    assert integrations[Venue.ASTER].submission_enabled is False
    assert integrations[Venue.ASTER].submission_authorized is False
    assert integrations[Venue.OKX].use_demo_mode is True
    assert integrations[Venue.OKX].submission_enabled is False
    assert integrations[Venue.OKX].submission_authorized is False
    assert integrations[Venue.COINBASE_ADVANCED_TRADE].read_only_mode is True
    assert integrations[Venue.COINBASE_ADVANCED_TRADE].submission_enabled is False
    assert integrations[Venue.COINBASE_ADVANCED_TRADE].submission_authorized is False
    assert integrations[Venue.BINANCE].read_only_mode is True
    assert integrations[Venue.BINANCE].submission_enabled is False
    assert integrations[Venue.BINANCE].submission_authorized is False
    assert integrations[Venue.KRAKEN].read_only_mode is True
    assert integrations[Venue.KRAKEN].submission_enabled is False
    assert integrations[Venue.KRAKEN].submission_authorized is False
    assert settings.execution.live_submission_phase_enabled is False
    assert settings.execution.routed_submission_phase_enabled is False
    assert settings.execution.require_private_state_for_submission_readiness is True


def test_pytest_bootstrap_disables_local_env_file_loading() -> None:
    assert AppSettings.model_config.get("env_file") is None
