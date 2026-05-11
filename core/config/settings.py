"""Environment-aware application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from decimal import Decimal

from pydantic import BaseModel, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.config.profiles import (
    BacktestProfile,
    BaseEnvironmentProfile,
    DevProfile,
    LiveProfile,
    PaperProfile,
    TestnetProfile,
)
from core.domain.enums import (
    Environment,
    InstrumentResolutionMode,
    MarketDataSourceMode,
    MarketType,
    ProductType,
    StackingPolicy,
    Timeframe,
    Venue,
)


class AppRuntimeConfig(BaseModel):
    name: str = "money-flow"
    environment: Environment = Environment.DEV
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "money_flow"
    user: str = "money_flow"
    password: str = "money_flow"
    echo: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )


class RedisConfig(BaseModel):
    enabled: bool = False
    url: str = "redis://localhost:6379/0"


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_logs: bool = True


class APIAuthConfig(BaseModel):
    enabled: bool = True
    disabled_for_tests: bool = False
    operator_token: str = ""
    read_only_operator_token: str = ""
    admin_token: str = ""
    automation_admin_token: str = ""
    uat_admin_token: str = ""


class RuntimeSafetyPolicy(BaseModel):
    runtime_mode: Literal["development", "test", "uat", "sandbox", "paper", "live"] = "development"
    uat_mode_enabled: bool = False
    sandbox_mode_required: bool = True
    paper_trading_enabled: bool = False
    live_trading_enabled: bool = False
    exchange_order_submission_enabled: bool = False
    private_exchange_endpoints_enabled: bool = False

    @property
    def live_endpoint_lockout_enabled(self) -> bool:
        return not self.live_trading_enabled

    @property
    def order_endpoint_lockout_enabled(self) -> bool:
        return not self.exchange_order_submission_enabled

    @property
    def private_endpoint_lockout_enabled(self) -> bool:
        return not self.private_exchange_endpoints_enabled


class ExchangeConfig(BaseModel):
    venue: str = "hyperliquid"
    name: str = "hyperliquid"
    use_testnet: bool = True
    api_base_url: str = "https://api.hyperliquid.xyz"
    ws_base_url: str = "wss://api.hyperliquid.xyz/ws"
    api_key: str = ""
    api_secret: str = ""
    account_address: str = ""
    account_label: str = "primary"
    credentials_ref: str = ""
    wallet_ref: str = ""
    signing_private_key: str = ""
    dex_name: str = ""
    request_timeout_seconds: float = 10.0
    allow_live_mode_without_api_key: bool = False


class VenueIntegrationConfig(BaseModel):
    venue: Venue
    name: str
    enabled: bool = True
    read_only_mode: bool = True
    dry_run_mode: bool = True
    submission_enabled: bool = False
    use_testnet: bool = False
    use_demo_mode: bool = False
    api_base_url: str = ""
    ws_base_url: str = ""
    account_identifier: str = ""
    account_address: str = ""
    account_label: str = ""
    subaccount_label: str = ""
    credentials_ref: str = ""
    wallet_ref: str = ""
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""
    signing_private_key: str = ""
    jwt_key_name: str = ""
    jwt_private_key_pem: str = ""
    submission_authorized: bool = False


class UniversePolicyConfig(BaseModel):
    include_standard_perp_universe: bool = True
    include_builder_deployed_in_catalog: bool = True
    allow_builder_deployed_for_strategy: bool = False
    allow_builder_deployed_for_trading: bool = False


class GlobalRiskConfig(BaseModel):
    trading_enabled: bool = True
    kill_switch_enabled: bool = True
    stacking_policy: StackingPolicy = StackingPolicy.NET_LIMIT
    global_max_gross_exposure_pct: float = Field(default=1.0, ge=0.0)
    global_max_account_drawdown_pct: float = Field(default=0.15, ge=0.0)
    global_max_symbol_concentration_pct: float = Field(default=0.25, ge=0.0)
    binding_reduce_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    reject_on_source_policy_runtime_mismatch: bool = True


class ExecutionConfig(BaseModel):
    default_order_ttl_seconds: int = 30
    max_slippage_bps: int = 10
    dry_run: bool = True
    live_submission_phase_enabled: bool = False
    routed_submission_phase_enabled: bool = False
    require_private_state_for_submission_readiness: bool = True


class AlertConfig(BaseModel):
    enabled: bool = False
    default_channel: str = "stdout"


class MarketDataConfig(BaseModel):
    rest_bootstrap_bars: int = 500
    sync_batch_size: int = 500
    stale_after_seconds: int = 180
    checkpoint_overlap_bars: int = 1
    tracked_timeframes: tuple[Timeframe, ...] = (
        Timeframe.M1,
        Timeframe.M5,
        Timeframe.M15,
        Timeframe.H1,
        Timeframe.H4,
        Timeframe.D1,
    )


class SleeveConfig(BaseModel):
    sleeve_id: str
    timeframe: Timeframe
    enabled: bool = True
    capital_allocation_pct: float = Field(ge=0.0, le=1.0)
    max_open_risk_pct: float = Field(ge=0.0, le=1.0)


class MoneyFlowSleeveConfig(BaseModel):
    sleeve_id: str
    timeframe: Timeframe
    enabled: bool = True
    min_history_bars: int = 35
    rsi_floor: float = 50.0
    rsi_ceiling: float = 68.0
    overbought_rsi: float = 72.0
    require_macd_confirmation: bool = True
    allow_pullback_entries: bool = True
    allow_continuation_entries: bool = True
    max_extension_pct_above_ema5: float = 0.02
    trim_on_overbought_rsi: bool = True
    trim_rsi: float = 78.0
    close_on_ma_break: bool = True
    close_on_macd_rollover: bool = True


class MoneyFlowConfig(BaseModel):
    family_name: str = "money_flow"
    strategy_enabled: bool = True
    sleeves: tuple[MoneyFlowSleeveConfig, ...]


class RuntimeSelectionConfig(BaseModel):
    active_client_key: str
    active_mandate_key: str
    focused_account_key: str | None = None


class MandateMarketDataSourcePolicyConfig(BaseModel):
    source_mode: MarketDataSourceMode = MarketDataSourceMode.SINGLE_VENUE
    source_venue: str = Venue.HYPERLIQUID.value
    market_type: MarketType | None = None
    product_type: ProductType | None = None
    instrument_resolution_mode: InstrumentResolutionMode = (
        InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS
    )


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="money-flow", alias="APP_NAME")
    app_env: Environment = Field(default=Environment.DEV, alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_api_host: str = Field(default="0.0.0.0", alias="APP_API_HOST")
    app_api_port: int = Field(default=8000, alias="APP_API_PORT")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="money_flow", alias="DB_NAME")
    db_user: str = Field(default="money_flow", alias="DB_USER")
    db_password: str = Field(default="money_flow", alias="DB_PASSWORD")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    redis_enabled: bool = Field(default=False, alias="REDIS_ENABLED")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    api_runtime_mode: Literal["development", "test", "uat", "sandbox", "paper", "live"] = Field(
        default="development",
        alias="API_RUNTIME_MODE",
    )
    api_auth_enabled: bool = Field(default=True, alias="API_AUTH_ENABLED")
    api_auth_disabled_for_tests: bool = Field(default=False, alias="API_AUTH_DISABLED_FOR_TESTS")
    api_read_only_operator_token: str = Field(default="", alias="API_READ_ONLY_OPERATOR_TOKEN")
    api_operator_token: str = Field(default="", alias="API_OPERATOR_TOKEN")
    api_admin_token: str = Field(default="", alias="API_ADMIN_TOKEN")
    api_automation_admin_token: str = Field(default="", alias="API_AUTOMATION_ADMIN_TOKEN")
    api_uat_admin_token: str = Field(default="", alias="API_UAT_ADMIN_TOKEN")

    uat_mode_enabled: bool = Field(default=False, alias="UAT_MODE_ENABLED")
    sandbox_mode_required: bool = Field(default=True, alias="SANDBOX_MODE_REQUIRED")
    paper_trading_enabled: bool = Field(default=False, alias="PAPER_TRADING_ENABLED")
    live_trading_enabled: bool = Field(default=False, alias="LIVE_TRADING_ENABLED")
    exchange_order_submission_enabled: bool = Field(
        default=False,
        alias="EXCHANGE_ORDER_SUBMISSION_ENABLED",
    )
    private_exchange_endpoints_enabled: bool = Field(
        default=False,
        alias="PRIVATE_EXCHANGE_ENDPOINTS_ENABLED",
    )

    exchange_name: str = Field(default="hyperliquid", alias="EXCHANGE_NAME")
    exchange_venue: str = Field(default="hyperliquid", alias="EXCHANGE_VENUE")
    exchange_use_testnet: bool = Field(default=True, alias="EXCHANGE_USE_TESTNET")
    exchange_api_base_url: str = Field(
        default="https://api.hyperliquid.xyz",
        alias="EXCHANGE_API_BASE_URL",
    )
    exchange_ws_base_url: str = Field(
        default="wss://api.hyperliquid.xyz/ws",
        alias="EXCHANGE_WS_BASE_URL",
    )
    exchange_api_key: str = Field(default="", alias="EXCHANGE_API_KEY")
    exchange_api_secret: str = Field(default="", alias="EXCHANGE_API_SECRET")
    exchange_account_address: str = Field(default="", alias="EXCHANGE_ACCOUNT_ADDRESS")
    exchange_account_label: str = Field(default="primary", alias="EXCHANGE_ACCOUNT_LABEL")
    exchange_credentials_ref: str = Field(default="", alias="EXCHANGE_CREDENTIALS_REF")
    exchange_wallet_ref: str = Field(default="", alias="EXCHANGE_WALLET_REF")
    exchange_signing_private_key: str = Field(default="", alias="EXCHANGE_SIGNING_PRIVATE_KEY")
    exchange_dex_name: str = Field(default="", alias="EXCHANGE_DEX_NAME")
    exchange_request_timeout_seconds: float = Field(
        default=10.0,
        alias="EXCHANGE_REQUEST_TIMEOUT_SECONDS",
    )
    exchange_allow_live_mode_without_api_key: bool = Field(
        default=False,
        alias="EXCHANGE_ALLOW_LIVE_MODE_WITHOUT_API_KEY",
    )
    exchange_universe_include_standard_perp: bool = Field(
        default=True,
        alias="EXCHANGE_UNIVERSE_INCLUDE_STANDARD_PERP",
    )
    exchange_universe_include_builder_deployed_in_catalog: bool = Field(
        default=True,
        alias="EXCHANGE_UNIVERSE_INCLUDE_BUILDER_DEPLOYED_IN_CATALOG",
    )
    exchange_universe_allow_builder_deployed_for_strategy: bool = Field(
        default=False,
        alias="EXCHANGE_UNIVERSE_ALLOW_BUILDER_DEPLOYED_FOR_STRATEGY",
    )
    exchange_universe_allow_builder_deployed_for_trading: bool = Field(
        default=False,
        alias="EXCHANGE_UNIVERSE_ALLOW_BUILDER_DEPLOYED_FOR_TRADING",
    )
    hyperliquid_read_only_mode: bool = Field(default=True, alias="HYPERLIQUID_READ_ONLY_MODE")
    hyperliquid_dry_run_mode: bool = Field(default=True, alias="HYPERLIQUID_DRY_RUN_MODE")
    hyperliquid_submission_enabled: bool = Field(
        default=False,
        alias="HYPERLIQUID_SUBMISSION_ENABLED",
    )
    hyperliquid_submission_authorized: bool = Field(
        default=False,
        alias="HYPERLIQUID_SUBMISSION_AUTHORIZED",
    )

    aster_enabled: bool = Field(default=True, alias="ASTER_ENABLED")
    aster_read_only_mode: bool = Field(default=True, alias="ASTER_READ_ONLY_MODE")
    aster_dry_run_mode: bool = Field(default=True, alias="ASTER_DRY_RUN_MODE")
    aster_submission_enabled: bool = Field(default=False, alias="ASTER_SUBMISSION_ENABLED")
    aster_use_testnet: bool = Field(default=False, alias="ASTER_USE_TESTNET")
    aster_use_demo_mode: bool = Field(default=False, alias="ASTER_USE_DEMO_MODE")
    aster_api_base_url: str = Field(default="https://fapi.asterdex.com", alias="ASTER_API_BASE_URL")
    aster_ws_base_url: str = Field(default="", alias="ASTER_WS_BASE_URL")
    aster_account_identifier: str = Field(default="", alias="ASTER_ACCOUNT_IDENTIFIER")
    aster_account_label: str = Field(default="", alias="ASTER_ACCOUNT_LABEL")
    aster_credentials_ref: str = Field(default="", alias="ASTER_CREDENTIALS_REF")
    aster_api_key: str = Field(default="", alias="ASTER_API_KEY")
    aster_api_secret: str = Field(default="", alias="ASTER_API_SECRET")
    aster_submission_authorized: bool = Field(default=False, alias="ASTER_SUBMISSION_AUTHORIZED")

    okx_enabled: bool = Field(default=True, alias="OKX_ENABLED")
    okx_read_only_mode: bool = Field(default=True, alias="OKX_READ_ONLY_MODE")
    okx_dry_run_mode: bool = Field(default=True, alias="OKX_DRY_RUN_MODE")
    okx_submission_enabled: bool = Field(default=False, alias="OKX_SUBMISSION_ENABLED")
    okx_use_testnet: bool = Field(default=False, alias="OKX_USE_TESTNET")
    okx_use_demo_mode: bool = Field(default=True, alias="OKX_USE_DEMO_MODE")
    okx_api_base_url: str = Field(default="https://www.okx.com", alias="OKX_API_BASE_URL")
    okx_ws_base_url: str = Field(default="wss://ws.okx.com:8443/ws/v5/public", alias="OKX_WS_BASE_URL")
    okx_account_identifier: str = Field(default="", alias="OKX_ACCOUNT_IDENTIFIER")
    okx_account_label: str = Field(default="", alias="OKX_ACCOUNT_LABEL")
    okx_subaccount_label: str = Field(default="", alias="OKX_SUBACCOUNT_LABEL")
    okx_credentials_ref: str = Field(default="", alias="OKX_CREDENTIALS_REF")
    okx_api_key: str = Field(default="", alias="OKX_API_KEY")
    okx_api_secret: str = Field(default="", alias="OKX_API_SECRET")
    okx_api_passphrase: str = Field(default="", alias="OKX_API_PASSPHRASE")
    okx_submission_authorized: bool = Field(default=False, alias="OKX_SUBMISSION_AUTHORIZED")

    coinbase_advanced_enabled: bool = Field(default=True, alias="COINBASE_ADVANCED_ENABLED")
    coinbase_advanced_read_only_mode: bool = Field(default=True, alias="COINBASE_ADVANCED_READ_ONLY_MODE")
    coinbase_advanced_dry_run_mode: bool = Field(default=True, alias="COINBASE_ADVANCED_DRY_RUN_MODE")
    coinbase_advanced_submission_enabled: bool = Field(
        default=False,
        alias="COINBASE_ADVANCED_SUBMISSION_ENABLED",
    )
    coinbase_advanced_use_testnet: bool = Field(default=False, alias="COINBASE_ADVANCED_USE_TESTNET")
    coinbase_advanced_use_demo_mode: bool = Field(default=False, alias="COINBASE_ADVANCED_USE_DEMO_MODE")
    coinbase_advanced_api_base_url: str = Field(
        default="https://api.coinbase.com",
        alias="COINBASE_ADVANCED_API_BASE_URL",
    )
    coinbase_advanced_ws_base_url: str = Field(
        default="wss://advanced-trade-ws.coinbase.com",
        alias="COINBASE_ADVANCED_WS_BASE_URL",
    )
    coinbase_advanced_account_identifier: str = Field(
        default="",
        alias="COINBASE_ADVANCED_ACCOUNT_IDENTIFIER",
    )
    coinbase_advanced_account_label: str = Field(default="", alias="COINBASE_ADVANCED_ACCOUNT_LABEL")
    coinbase_advanced_credentials_ref: str = Field(
        default="",
        alias="COINBASE_ADVANCED_CREDENTIALS_REF",
    )
    coinbase_advanced_api_key: str = Field(default="", alias="COINBASE_ADVANCED_API_KEY")
    coinbase_advanced_api_secret: str = Field(default="", alias="COINBASE_ADVANCED_API_SECRET")
    coinbase_advanced_jwt_key_name: str = Field(
        default="",
        alias="COINBASE_ADVANCED_JWT_KEY_NAME",
    )
    coinbase_advanced_jwt_private_key_pem: str = Field(
        default="",
        alias="COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM",
    )
    coinbase_advanced_submission_authorized: bool = Field(
        default=False,
        alias="COINBASE_ADVANCED_SUBMISSION_AUTHORIZED",
    )

    binance_enabled: bool = Field(default=True, alias="BINANCE_ENABLED")
    binance_read_only_mode: bool = Field(default=True, alias="BINANCE_READ_ONLY_MODE")
    binance_dry_run_mode: bool = Field(default=True, alias="BINANCE_DRY_RUN_MODE")
    binance_submission_enabled: bool = Field(default=False, alias="BINANCE_SUBMISSION_ENABLED")
    binance_use_testnet: bool = Field(default=False, alias="BINANCE_USE_TESTNET")
    binance_use_demo_mode: bool = Field(default=False, alias="BINANCE_USE_DEMO_MODE")
    binance_api_base_url: str = Field(default="https://api.binance.com", alias="BINANCE_API_BASE_URL")
    binance_ws_base_url: str = Field(
        default="wss://stream.binance.com:9443/ws",
        alias="BINANCE_WS_BASE_URL",
    )
    binance_account_identifier: str = Field(default="", alias="BINANCE_ACCOUNT_IDENTIFIER")
    binance_account_label: str = Field(default="", alias="BINANCE_ACCOUNT_LABEL")
    binance_subaccount_label: str = Field(default="", alias="BINANCE_SUBACCOUNT_LABEL")
    binance_credentials_ref: str = Field(default="", alias="BINANCE_CREDENTIALS_REF")
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    binance_submission_authorized: bool = Field(
        default=False,
        alias="BINANCE_SUBMISSION_AUTHORIZED",
    )

    kraken_enabled: bool = Field(default=True, alias="KRAKEN_ENABLED")
    kraken_read_only_mode: bool = Field(default=True, alias="KRAKEN_READ_ONLY_MODE")
    kraken_dry_run_mode: bool = Field(default=True, alias="KRAKEN_DRY_RUN_MODE")
    kraken_submission_enabled: bool = Field(default=False, alias="KRAKEN_SUBMISSION_ENABLED")
    kraken_use_testnet: bool = Field(default=False, alias="KRAKEN_USE_TESTNET")
    kraken_use_demo_mode: bool = Field(default=False, alias="KRAKEN_USE_DEMO_MODE")
    kraken_api_base_url: str = Field(default="https://api.kraken.com", alias="KRAKEN_API_BASE_URL")
    kraken_ws_base_url: str = Field(default="wss://ws.kraken.com", alias="KRAKEN_WS_BASE_URL")
    kraken_account_identifier: str = Field(default="", alias="KRAKEN_ACCOUNT_IDENTIFIER")
    kraken_account_label: str = Field(default="", alias="KRAKEN_ACCOUNT_LABEL")
    kraken_subaccount_label: str = Field(default="", alias="KRAKEN_SUBACCOUNT_LABEL")
    kraken_credentials_ref: str = Field(default="", alias="KRAKEN_CREDENTIALS_REF")
    kraken_api_key: str = Field(default="", alias="KRAKEN_API_KEY")
    kraken_api_secret: str = Field(default="", alias="KRAKEN_API_SECRET")
    kraken_submission_authorized: bool = Field(
        default=False,
        alias="KRAKEN_SUBMISSION_AUTHORIZED",
    )

    active_client_key: str = Field(default="default_client", alias="ACTIVE_CLIENT_KEY")
    active_account_key: str = Field(default="", alias="ACTIVE_ACCOUNT_KEY")
    active_mandate_key: str = Field(default="", alias="ACTIVE_MANDATE_KEY")
    mandate_market_data_source_mode: MarketDataSourceMode = Field(
        default=MarketDataSourceMode.SINGLE_VENUE,
        alias="MANDATE_MARKET_DATA_SOURCE_MODE",
    )
    mandate_market_data_source_venue: str = Field(default="", alias="MANDATE_MARKET_DATA_SOURCE_VENUE")
    mandate_market_data_source_market_type: MarketType | None = Field(
        default=None,
        alias="MANDATE_MARKET_DATA_SOURCE_MARKET_TYPE",
    )
    mandate_market_data_source_product_type: ProductType | None = Field(
        default=None,
        alias="MANDATE_MARKET_DATA_SOURCE_PRODUCT_TYPE",
    )
    mandate_instrument_resolution_mode: InstrumentResolutionMode = Field(
        default=InstrumentResolutionMode.CANONICAL_SYMBOL_IF_UNAMBIGUOUS,
        alias="MANDATE_INSTRUMENT_RESOLUTION_MODE",
    )

    risk_global_max_gross_exposure_pct: float = Field(
        default=1.0,
        alias="RISK_GLOBAL_MAX_GROSS_EXPOSURE_PCT",
    )
    risk_global_max_account_drawdown_pct: float = Field(
        default=0.15,
        alias="RISK_GLOBAL_MAX_ACCOUNT_DRAWDOWN_PCT",
    )
    risk_global_max_symbol_concentration_pct: float = Field(
        default=0.25,
        alias="RISK_GLOBAL_MAX_SYMBOL_CONCENTRATION_PCT",
    )
    risk_trading_enabled: bool = Field(default=True, alias="RISK_TRADING_ENABLED")
    risk_kill_switch_enabled: bool = Field(default=True, alias="RISK_KILL_SWITCH_ENABLED")
    risk_stacking_policy: StackingPolicy = Field(
        default=StackingPolicy.NET_LIMIT,
        alias="RISK_STACKING_POLICY",
    )
    risk_binding_reduce_fraction: float = Field(
        default=0.5,
        alias="RISK_BINDING_REDUCE_FRACTION",
    )
    risk_reject_on_source_policy_runtime_mismatch: bool = Field(
        default=True,
        alias="RISK_REJECT_ON_SOURCE_POLICY_RUNTIME_MISMATCH",
    )

    execution_default_order_ttl_seconds: int = Field(
        default=30,
        alias="EXECUTION_DEFAULT_ORDER_TTL_SECONDS",
    )
    execution_max_slippage_bps: int = Field(default=10, alias="EXECUTION_MAX_SLIPPAGE_BPS")
    execution_dry_run: bool = Field(default=True, alias="EXECUTION_DRY_RUN")
    execution_live_submission_phase_enabled: bool = Field(
        default=False,
        alias="EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED",
    )
    execution_routed_submission_phase_enabled: bool = Field(
        default=False,
        alias="EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED",
    )
    execution_require_private_state_for_submission_readiness: bool = Field(
        default=True,
        alias="EXECUTION_REQUIRE_PRIVATE_STATE_FOR_SUBMISSION_READINESS",
    )

    alerts_enabled: bool = Field(default=False, alias="ALERTS_ENABLED")
    alerts_default_channel: str = Field(default="stdout", alias="ALERTS_DEFAULT_CHANNEL")

    market_data_rest_bootstrap_bars: int = Field(
        default=500,
        alias="MARKET_DATA_REST_BOOTSTRAP_BARS",
    )
    market_data_sync_batch_size: int = Field(default=500, alias="MARKET_DATA_SYNC_BATCH_SIZE")
    market_data_stale_after_seconds: int = Field(
        default=180,
        alias="MARKET_DATA_STALE_AFTER_SECONDS",
    )
    market_data_checkpoint_overlap_bars: int = Field(
        default=1,
        alias="MARKET_DATA_CHECKPOINT_OVERLAP_BARS",
    )

    sleeve_15m_enabled: bool = Field(default=True, alias="SLEEVE_15M_ENABLED")
    sleeve_15m_timeframe: Timeframe = Field(default=Timeframe.M15, alias="SLEEVE_15M_TIMEFRAME")
    sleeve_15m_capital_allocation_pct: float = Field(
        default=0.25,
        alias="SLEEVE_15M_CAPITAL_ALLOCATION_PCT",
    )
    sleeve_15m_max_open_risk_pct: float = Field(
        default=0.02,
        alias="SLEEVE_15M_MAX_OPEN_RISK_PCT",
    )

    sleeve_1h_enabled: bool = Field(default=True, alias="SLEEVE_1H_ENABLED")
    sleeve_1h_timeframe: Timeframe = Field(default=Timeframe.H1, alias="SLEEVE_1H_TIMEFRAME")
    sleeve_1h_capital_allocation_pct: float = Field(
        default=0.25,
        alias="SLEEVE_1H_CAPITAL_ALLOCATION_PCT",
    )
    sleeve_1h_max_open_risk_pct: float = Field(
        default=0.02,
        alias="SLEEVE_1H_MAX_OPEN_RISK_PCT",
    )

    sleeve_4h_enabled: bool = Field(default=True, alias="SLEEVE_4H_ENABLED")
    sleeve_4h_timeframe: Timeframe = Field(default=Timeframe.H4, alias="SLEEVE_4H_TIMEFRAME")
    sleeve_4h_capital_allocation_pct: float = Field(
        default=0.25,
        alias="SLEEVE_4H_CAPITAL_ALLOCATION_PCT",
    )
    sleeve_4h_max_open_risk_pct: float = Field(
        default=0.02,
        alias="SLEEVE_4H_MAX_OPEN_RISK_PCT",
    )
    sleeve_1d_enabled: bool = Field(default=True, alias="SLEEVE_1D_ENABLED")
    sleeve_1d_timeframe: Timeframe = Field(default=Timeframe.D1, alias="SLEEVE_1D_TIMEFRAME")
    sleeve_1d_capital_allocation_pct: float = Field(
        default=0.25,
        alias="SLEEVE_1D_CAPITAL_ALLOCATION_PCT",
    )
    sleeve_1d_max_open_risk_pct: float = Field(
        default=0.02,
        alias="SLEEVE_1D_MAX_OPEN_RISK_PCT",
    )

    @model_validator(mode="after")
    def validate_enabled_sleeve_allocation_budget(self) -> "AppSettings":
        enabled_allocations = (
            Decimal(str(self.sleeve_15m_capital_allocation_pct)) if self.sleeve_15m_enabled else Decimal("0"),
            Decimal(str(self.sleeve_1h_capital_allocation_pct)) if self.sleeve_1h_enabled else Decimal("0"),
            Decimal(str(self.sleeve_4h_capital_allocation_pct)) if self.sleeve_4h_enabled else Decimal("0"),
            Decimal(str(self.sleeve_1d_capital_allocation_pct)) if self.sleeve_1d_enabled else Decimal("0"),
        )
        if sum(enabled_allocations) > Decimal("1.0"):
            raise ValueError("enabled_sleeve_capital_allocation_pct_sum_exceeds_1_0")
        return self

    money_flow_strategy_enabled: bool = Field(default=True, alias="MONEY_FLOW_STRATEGY_ENABLED")

    money_flow_15m_min_history_bars: int = Field(default=35, alias="MONEY_FLOW_15M_MIN_HISTORY_BARS")
    money_flow_15m_rsi_floor: float = Field(default=52.0, alias="MONEY_FLOW_15M_RSI_FLOOR")
    money_flow_15m_rsi_ceiling: float = Field(default=66.0, alias="MONEY_FLOW_15M_RSI_CEILING")
    money_flow_15m_overbought_rsi: float = Field(default=72.0, alias="MONEY_FLOW_15M_OVERBOUGHT_RSI")
    money_flow_15m_require_macd_confirmation: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_REQUIRE_MACD_CONFIRMATION",
    )
    money_flow_15m_allow_pullback_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_ALLOW_PULLBACK_ENTRIES",
    )
    money_flow_15m_allow_continuation_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_ALLOW_CONTINUATION_ENTRIES",
    )
    money_flow_15m_max_extension_pct_above_ema5: float = Field(
        default=0.018,
        alias="MONEY_FLOW_15M_MAX_EXTENSION_PCT_ABOVE_EMA5",
    )
    money_flow_15m_trim_on_overbought_rsi: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_TRIM_ON_OVERBOUGHT_RSI",
    )
    money_flow_15m_trim_rsi: float = Field(default=78.0, alias="MONEY_FLOW_15M_TRIM_RSI")
    money_flow_15m_close_on_ma_break: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_CLOSE_ON_MA_BREAK",
    )
    money_flow_15m_close_on_macd_rollover: bool = Field(
        default=True,
        alias="MONEY_FLOW_15M_CLOSE_ON_MACD_ROLLOVER",
    )

    money_flow_1h_min_history_bars: int = Field(default=35, alias="MONEY_FLOW_1H_MIN_HISTORY_BARS")
    money_flow_1h_rsi_floor: float = Field(default=50.0, alias="MONEY_FLOW_1H_RSI_FLOOR")
    money_flow_1h_rsi_ceiling: float = Field(default=68.0, alias="MONEY_FLOW_1H_RSI_CEILING")
    money_flow_1h_overbought_rsi: float = Field(default=74.0, alias="MONEY_FLOW_1H_OVERBOUGHT_RSI")
    money_flow_1h_require_macd_confirmation: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_REQUIRE_MACD_CONFIRMATION",
    )
    money_flow_1h_allow_pullback_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_ALLOW_PULLBACK_ENTRIES",
    )
    money_flow_1h_allow_continuation_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_ALLOW_CONTINUATION_ENTRIES",
    )
    money_flow_1h_max_extension_pct_above_ema5: float = Field(
        default=0.02,
        alias="MONEY_FLOW_1H_MAX_EXTENSION_PCT_ABOVE_EMA5",
    )
    money_flow_1h_trim_on_overbought_rsi: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_TRIM_ON_OVERBOUGHT_RSI",
    )
    money_flow_1h_trim_rsi: float = Field(default=80.0, alias="MONEY_FLOW_1H_TRIM_RSI")
    money_flow_1h_close_on_ma_break: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_CLOSE_ON_MA_BREAK",
    )
    money_flow_1h_close_on_macd_rollover: bool = Field(
        default=True,
        alias="MONEY_FLOW_1H_CLOSE_ON_MACD_ROLLOVER",
    )

    money_flow_4h_min_history_bars: int = Field(default=40, alias="MONEY_FLOW_4H_MIN_HISTORY_BARS")
    money_flow_4h_rsi_floor: float = Field(default=48.0, alias="MONEY_FLOW_4H_RSI_FLOOR")
    money_flow_4h_rsi_ceiling: float = Field(default=70.0, alias="MONEY_FLOW_4H_RSI_CEILING")
    money_flow_4h_overbought_rsi: float = Field(default=76.0, alias="MONEY_FLOW_4H_OVERBOUGHT_RSI")
    money_flow_4h_require_macd_confirmation: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_REQUIRE_MACD_CONFIRMATION",
    )
    money_flow_4h_allow_pullback_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_ALLOW_PULLBACK_ENTRIES",
    )
    money_flow_4h_allow_continuation_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_ALLOW_CONTINUATION_ENTRIES",
    )
    money_flow_4h_max_extension_pct_above_ema5: float = Field(
        default=0.025,
        alias="MONEY_FLOW_4H_MAX_EXTENSION_PCT_ABOVE_EMA5",
    )
    money_flow_4h_trim_on_overbought_rsi: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_TRIM_ON_OVERBOUGHT_RSI",
    )
    money_flow_4h_trim_rsi: float = Field(default=82.0, alias="MONEY_FLOW_4H_TRIM_RSI")
    money_flow_4h_close_on_ma_break: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_CLOSE_ON_MA_BREAK",
    )
    money_flow_4h_close_on_macd_rollover: bool = Field(
        default=True,
        alias="MONEY_FLOW_4H_CLOSE_ON_MACD_ROLLOVER",
    )
    money_flow_1d_min_history_bars: int = Field(default=50, alias="MONEY_FLOW_1D_MIN_HISTORY_BARS")
    money_flow_1d_rsi_floor: float = Field(default=46.0, alias="MONEY_FLOW_1D_RSI_FLOOR")
    money_flow_1d_rsi_ceiling: float = Field(default=72.0, alias="MONEY_FLOW_1D_RSI_CEILING")
    money_flow_1d_overbought_rsi: float = Field(default=78.0, alias="MONEY_FLOW_1D_OVERBOUGHT_RSI")
    money_flow_1d_require_macd_confirmation: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_REQUIRE_MACD_CONFIRMATION",
    )
    money_flow_1d_allow_pullback_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_ALLOW_PULLBACK_ENTRIES",
    )
    money_flow_1d_allow_continuation_entries: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_ALLOW_CONTINUATION_ENTRIES",
    )
    money_flow_1d_max_extension_pct_above_ema5: float = Field(
        default=0.03,
        alias="MONEY_FLOW_1D_MAX_EXTENSION_PCT_ABOVE_EMA5",
    )
    money_flow_1d_trim_on_overbought_rsi: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_TRIM_ON_OVERBOUGHT_RSI",
    )
    money_flow_1d_trim_rsi: float = Field(default=84.0, alias="MONEY_FLOW_1D_TRIM_RSI")
    money_flow_1d_close_on_ma_break: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_CLOSE_ON_MA_BREAK",
    )
    money_flow_1d_close_on_macd_rollover: bool = Field(
        default=True,
        alias="MONEY_FLOW_1D_CLOSE_ON_MACD_ROLLOVER",
    )

    @property
    def app(self) -> AppRuntimeConfig:
        return AppRuntimeConfig(
            name=self.app_name,
            environment=self.app_env,
            debug=self.app_debug,
            api_host=self.app_api_host,
            api_port=self.app_api_port,
        )

    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=self.db_host,
            port=self.db_port,
            name=self.db_name,
            user=self.db_user,
            password=self.db_password,
            echo=self.db_echo,
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(enabled=self.redis_enabled, url=self.redis_url)

    @property
    def logging(self) -> LoggingConfig:
        return LoggingConfig(level=self.log_level, json_logs=self.log_json)

    @property
    def api_auth(self) -> APIAuthConfig:
        return APIAuthConfig(
            enabled=self.api_auth_enabled,
            disabled_for_tests=self.api_auth_disabled_for_tests,
            operator_token=self.api_operator_token,
            read_only_operator_token=self.api_read_only_operator_token,
            admin_token=self.api_admin_token,
            automation_admin_token=self.api_automation_admin_token,
            uat_admin_token=self.api_uat_admin_token,
        )

    @property
    def runtime_safety(self) -> RuntimeSafetyPolicy:
        return RuntimeSafetyPolicy(
            runtime_mode=self.api_runtime_mode,
            uat_mode_enabled=self.uat_mode_enabled,
            sandbox_mode_required=self.sandbox_mode_required,
            paper_trading_enabled=self.paper_trading_enabled,
            live_trading_enabled=self.live_trading_enabled,
            exchange_order_submission_enabled=self.exchange_order_submission_enabled,
            private_exchange_endpoints_enabled=self.private_exchange_endpoints_enabled,
        )

    @property
    def exchange(self) -> ExchangeConfig:
        return ExchangeConfig(
            venue=self.exchange_venue,
            name=self.exchange_name,
            use_testnet=self.exchange_use_testnet,
            api_base_url=self.exchange_api_base_url,
            ws_base_url=self.exchange_ws_base_url,
            api_key=self.exchange_api_key,
            api_secret=self.exchange_api_secret,
            account_address=self.exchange_account_address,
            account_label=self.exchange_account_label,
            credentials_ref=self.exchange_credentials_ref,
            wallet_ref=self.exchange_wallet_ref,
            signing_private_key=self.exchange_signing_private_key,
            dex_name=self.exchange_dex_name,
            request_timeout_seconds=self.exchange_request_timeout_seconds,
            allow_live_mode_without_api_key=self.exchange_allow_live_mode_without_api_key,
        )

    @property
    def universe_policy(self) -> UniversePolicyConfig:
        return UniversePolicyConfig(
            include_standard_perp_universe=self.exchange_universe_include_standard_perp,
            include_builder_deployed_in_catalog=self.exchange_universe_include_builder_deployed_in_catalog,
            allow_builder_deployed_for_strategy=self.exchange_universe_allow_builder_deployed_for_strategy,
            allow_builder_deployed_for_trading=self.exchange_universe_allow_builder_deployed_for_trading,
        )

    @property
    def hyperliquid_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.HYPERLIQUID,
            name="Hyperliquid",
            enabled=True,
            read_only_mode=self.hyperliquid_read_only_mode,
            dry_run_mode=self.hyperliquid_dry_run_mode,
            submission_enabled=self.hyperliquid_submission_enabled,
            use_testnet=self.exchange_use_testnet,
            use_demo_mode=False,
            api_base_url=self.exchange.api_base_url,
            ws_base_url=self.exchange.ws_base_url,
            account_identifier=self.exchange.account_address,
            account_address=self.exchange.account_address,
            account_label=self.exchange.account_label,
            subaccount_label="",
            credentials_ref=self.exchange.credentials_ref,
            wallet_ref=self.exchange.wallet_ref,
            api_key=self.exchange.api_key,
            api_secret=self.exchange.api_secret,
            signing_private_key=self.exchange.signing_private_key or self.exchange.api_secret,
            submission_authorized=self.hyperliquid_submission_authorized,
        )

    @property
    def aster_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.ASTER,
            name="Aster",
            enabled=self.aster_enabled,
            read_only_mode=self.aster_read_only_mode,
            dry_run_mode=self.aster_dry_run_mode,
            submission_enabled=self.aster_submission_enabled,
            use_testnet=self.aster_use_testnet,
            use_demo_mode=self.aster_use_demo_mode,
            api_base_url=self.aster_api_base_url,
            ws_base_url=self.aster_ws_base_url,
            account_identifier=self.aster_account_identifier,
            account_label=self.aster_account_label,
            credentials_ref=self.aster_credentials_ref,
            api_key=self.aster_api_key,
            api_secret=self.aster_api_secret,
            submission_authorized=self.aster_submission_authorized,
        )

    @property
    def okx_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.OKX,
            name="OKX",
            enabled=self.okx_enabled,
            read_only_mode=self.okx_read_only_mode,
            dry_run_mode=self.okx_dry_run_mode,
            submission_enabled=self.okx_submission_enabled,
            use_testnet=self.okx_use_testnet,
            use_demo_mode=self.okx_use_demo_mode,
            api_base_url=self.okx_api_base_url,
            ws_base_url=self.okx_ws_base_url,
            account_identifier=self.okx_account_identifier,
            account_label=self.okx_account_label,
            subaccount_label=self.okx_subaccount_label,
            credentials_ref=self.okx_credentials_ref,
            api_key=self.okx_api_key,
            api_secret=self.okx_api_secret,
            api_passphrase=self.okx_api_passphrase,
            submission_authorized=self.okx_submission_authorized,
        )

    @property
    def coinbase_advanced_trade_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.COINBASE_ADVANCED_TRADE,
            name="Coinbase Advanced Trade",
            enabled=self.coinbase_advanced_enabled,
            read_only_mode=self.coinbase_advanced_read_only_mode,
            dry_run_mode=self.coinbase_advanced_dry_run_mode,
            submission_enabled=self.coinbase_advanced_submission_enabled,
            use_testnet=self.coinbase_advanced_use_testnet,
            use_demo_mode=self.coinbase_advanced_use_demo_mode,
            api_base_url=self.coinbase_advanced_api_base_url,
            ws_base_url=self.coinbase_advanced_ws_base_url,
            account_identifier=self.coinbase_advanced_account_identifier,
            account_label=self.coinbase_advanced_account_label,
            credentials_ref=self.coinbase_advanced_credentials_ref,
            api_key=self.coinbase_advanced_api_key,
            api_secret=self.coinbase_advanced_api_secret,
            jwt_key_name=self.coinbase_advanced_jwt_key_name or self.coinbase_advanced_api_key,
            jwt_private_key_pem=(
                self.coinbase_advanced_jwt_private_key_pem or self.coinbase_advanced_api_secret
            ),
            submission_authorized=self.coinbase_advanced_submission_authorized,
        )

    @property
    def binance_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.BINANCE,
            name="Binance",
            enabled=self.binance_enabled,
            read_only_mode=self.binance_read_only_mode,
            dry_run_mode=self.binance_dry_run_mode,
            submission_enabled=self.binance_submission_enabled,
            use_testnet=self.binance_use_testnet,
            use_demo_mode=self.binance_use_demo_mode,
            api_base_url=self.binance_api_base_url,
            ws_base_url=self.binance_ws_base_url,
            account_identifier=self.binance_account_identifier,
            account_label=self.binance_account_label,
            subaccount_label=self.binance_subaccount_label,
            credentials_ref=self.binance_credentials_ref,
            api_key=self.binance_api_key,
            api_secret=self.binance_api_secret,
            submission_authorized=self.binance_submission_authorized,
        )

    @property
    def kraken_integration(self) -> VenueIntegrationConfig:
        return VenueIntegrationConfig(
            venue=Venue.KRAKEN,
            name="Kraken",
            enabled=self.kraken_enabled,
            read_only_mode=self.kraken_read_only_mode,
            dry_run_mode=self.kraken_dry_run_mode,
            submission_enabled=self.kraken_submission_enabled,
            use_testnet=self.kraken_use_testnet,
            use_demo_mode=self.kraken_use_demo_mode,
            api_base_url=self.kraken_api_base_url,
            ws_base_url=self.kraken_ws_base_url,
            account_identifier=self.kraken_account_identifier,
            account_label=self.kraken_account_label,
            subaccount_label=self.kraken_subaccount_label,
            credentials_ref=self.kraken_credentials_ref,
            api_key=self.kraken_api_key,
            api_secret=self.kraken_api_secret,
            submission_authorized=self.kraken_submission_authorized,
        )

    @property
    def venue_integrations(self) -> dict[Venue, VenueIntegrationConfig]:
        return {
            Venue.HYPERLIQUID: self.hyperliquid_integration,
            Venue.ASTER: self.aster_integration,
            Venue.OKX: self.okx_integration,
            Venue.COINBASE_ADVANCED_TRADE: self.coinbase_advanced_trade_integration,
            Venue.BINANCE: self.binance_integration,
            Venue.KRAKEN: self.kraken_integration,
        }

    @property
    def risk(self) -> GlobalRiskConfig:
        return GlobalRiskConfig(
            trading_enabled=self.risk_trading_enabled,
            kill_switch_enabled=self.risk_kill_switch_enabled,
            stacking_policy=self.risk_stacking_policy,
            global_max_gross_exposure_pct=self.risk_global_max_gross_exposure_pct,
            global_max_account_drawdown_pct=self.risk_global_max_account_drawdown_pct,
            global_max_symbol_concentration_pct=self.risk_global_max_symbol_concentration_pct,
            binding_reduce_fraction=self.risk_binding_reduce_fraction,
            reject_on_source_policy_runtime_mismatch=self.risk_reject_on_source_policy_runtime_mismatch,
        )

    @property
    def execution(self) -> ExecutionConfig:
        return ExecutionConfig(
            default_order_ttl_seconds=self.execution_default_order_ttl_seconds,
            max_slippage_bps=self.execution_max_slippage_bps,
            dry_run=self.execution_dry_run,
            live_submission_phase_enabled=self.execution_live_submission_phase_enabled,
            routed_submission_phase_enabled=self.execution_routed_submission_phase_enabled,
            require_private_state_for_submission_readiness=(
                self.execution_require_private_state_for_submission_readiness
            ),
        )

    @property
    def alerts(self) -> AlertConfig:
        return AlertConfig(
            enabled=self.alerts_enabled,
            default_channel=self.alerts_default_channel,
        )

    @property
    def market_data(self) -> MarketDataConfig:
        return MarketDataConfig(
            rest_bootstrap_bars=self.market_data_rest_bootstrap_bars,
            sync_batch_size=self.market_data_sync_batch_size,
            stale_after_seconds=self.market_data_stale_after_seconds,
            checkpoint_overlap_bars=self.market_data_checkpoint_overlap_bars,
        )

    @property
    def components(self) -> list[SleeveConfig]:
        return [
            SleeveConfig(
                sleeve_id="sleeve_15m",
                timeframe=self.sleeve_15m_timeframe,
                enabled=self.sleeve_15m_enabled,
                capital_allocation_pct=self.sleeve_15m_capital_allocation_pct,
                max_open_risk_pct=self.sleeve_15m_max_open_risk_pct,
            ),
            SleeveConfig(
                sleeve_id="sleeve_1h",
                timeframe=self.sleeve_1h_timeframe,
                enabled=self.sleeve_1h_enabled,
                capital_allocation_pct=self.sleeve_1h_capital_allocation_pct,
                max_open_risk_pct=self.sleeve_1h_max_open_risk_pct,
            ),
            SleeveConfig(
                sleeve_id="sleeve_4h",
                timeframe=self.sleeve_4h_timeframe,
                enabled=self.sleeve_4h_enabled,
                capital_allocation_pct=self.sleeve_4h_capital_allocation_pct,
                max_open_risk_pct=self.sleeve_4h_max_open_risk_pct,
            ),
            SleeveConfig(
                sleeve_id="sleeve_1d",
                timeframe=self.sleeve_1d_timeframe,
                enabled=self.sleeve_1d_enabled,
                capital_allocation_pct=self.sleeve_1d_capital_allocation_pct,
                max_open_risk_pct=self.sleeve_1d_max_open_risk_pct,
            ),
        ]

    @property
    def sleeves(self) -> list[SleeveConfig]:
        return self.components

    @property
    def money_flow(self) -> MoneyFlowConfig:
        return MoneyFlowConfig(
            strategy_enabled=self.money_flow_strategy_enabled,
            sleeves=(
                MoneyFlowSleeveConfig(
                    sleeve_id="sleeve_15m",
                    timeframe=self.sleeve_15m_timeframe,
                    enabled=self.sleeve_15m_enabled,
                    min_history_bars=self.money_flow_15m_min_history_bars,
                    rsi_floor=self.money_flow_15m_rsi_floor,
                    rsi_ceiling=self.money_flow_15m_rsi_ceiling,
                    overbought_rsi=self.money_flow_15m_overbought_rsi,
                    require_macd_confirmation=self.money_flow_15m_require_macd_confirmation,
                    allow_pullback_entries=self.money_flow_15m_allow_pullback_entries,
                    allow_continuation_entries=self.money_flow_15m_allow_continuation_entries,
                    max_extension_pct_above_ema5=self.money_flow_15m_max_extension_pct_above_ema5,
                    trim_on_overbought_rsi=self.money_flow_15m_trim_on_overbought_rsi,
                    trim_rsi=self.money_flow_15m_trim_rsi,
                    close_on_ma_break=self.money_flow_15m_close_on_ma_break,
                    close_on_macd_rollover=self.money_flow_15m_close_on_macd_rollover,
                ),
                MoneyFlowSleeveConfig(
                    sleeve_id="sleeve_1h",
                    timeframe=self.sleeve_1h_timeframe,
                    enabled=self.sleeve_1h_enabled,
                    min_history_bars=self.money_flow_1h_min_history_bars,
                    rsi_floor=self.money_flow_1h_rsi_floor,
                    rsi_ceiling=self.money_flow_1h_rsi_ceiling,
                    overbought_rsi=self.money_flow_1h_overbought_rsi,
                    require_macd_confirmation=self.money_flow_1h_require_macd_confirmation,
                    allow_pullback_entries=self.money_flow_1h_allow_pullback_entries,
                    allow_continuation_entries=self.money_flow_1h_allow_continuation_entries,
                    max_extension_pct_above_ema5=self.money_flow_1h_max_extension_pct_above_ema5,
                    trim_on_overbought_rsi=self.money_flow_1h_trim_on_overbought_rsi,
                    trim_rsi=self.money_flow_1h_trim_rsi,
                    close_on_ma_break=self.money_flow_1h_close_on_ma_break,
                    close_on_macd_rollover=self.money_flow_1h_close_on_macd_rollover,
                ),
                MoneyFlowSleeveConfig(
                    sleeve_id="sleeve_4h",
                    timeframe=self.sleeve_4h_timeframe,
                    enabled=self.sleeve_4h_enabled,
                    min_history_bars=self.money_flow_4h_min_history_bars,
                    rsi_floor=self.money_flow_4h_rsi_floor,
                    rsi_ceiling=self.money_flow_4h_rsi_ceiling,
                    overbought_rsi=self.money_flow_4h_overbought_rsi,
                    require_macd_confirmation=self.money_flow_4h_require_macd_confirmation,
                    allow_pullback_entries=self.money_flow_4h_allow_pullback_entries,
                    allow_continuation_entries=self.money_flow_4h_allow_continuation_entries,
                    max_extension_pct_above_ema5=self.money_flow_4h_max_extension_pct_above_ema5,
                    trim_on_overbought_rsi=self.money_flow_4h_trim_on_overbought_rsi,
                    trim_rsi=self.money_flow_4h_trim_rsi,
                    close_on_ma_break=self.money_flow_4h_close_on_ma_break,
                    close_on_macd_rollover=self.money_flow_4h_close_on_macd_rollover,
                ),
                MoneyFlowSleeveConfig(
                    sleeve_id="sleeve_1d",
                    timeframe=self.sleeve_1d_timeframe,
                    enabled=self.sleeve_1d_enabled,
                    min_history_bars=self.money_flow_1d_min_history_bars,
                    rsi_floor=self.money_flow_1d_rsi_floor,
                    rsi_ceiling=self.money_flow_1d_rsi_ceiling,
                    overbought_rsi=self.money_flow_1d_overbought_rsi,
                    require_macd_confirmation=self.money_flow_1d_require_macd_confirmation,
                    allow_pullback_entries=self.money_flow_1d_allow_pullback_entries,
                    allow_continuation_entries=self.money_flow_1d_allow_continuation_entries,
                    max_extension_pct_above_ema5=self.money_flow_1d_max_extension_pct_above_ema5,
                    trim_on_overbought_rsi=self.money_flow_1d_trim_on_overbought_rsi,
                    trim_rsi=self.money_flow_1d_trim_rsi,
                    close_on_ma_break=self.money_flow_1d_close_on_ma_break,
                    close_on_macd_rollover=self.money_flow_1d_close_on_macd_rollover,
                ),
            ),
        )

    @property
    def default_account_key(self) -> str:
        venue = self.exchange_venue.lower()
        environment = self.app_env.value
        account_suffix = (
            self.exchange_account_label.strip().lower().replace(" ", "_")
            or (self.exchange_account_address[-8:].lower() if self.exchange_account_address else "primary")
        )
        return f"{venue}_{environment}_{account_suffix}"

    @property
    def default_mandate_key(self) -> str:
        return f"{self.money_flow.family_name}::{self.default_account_key}"

    @property
    def runtime_selection(self) -> RuntimeSelectionConfig:
        return RuntimeSelectionConfig(
            active_client_key=self.active_client_key,
            active_mandate_key=self.active_mandate_key or self.default_mandate_key,
            focused_account_key=self.active_account_key or self.default_account_key,
        )

    @property
    def mandate_market_data_source_policy(self) -> MandateMarketDataSourcePolicyConfig:
        source_venue = (self.mandate_market_data_source_venue or self.exchange_venue).strip().lower()
        return MandateMarketDataSourcePolicyConfig(
            source_mode=self.mandate_market_data_source_mode,
            source_venue=source_venue,
            market_type=self.mandate_market_data_source_market_type,
            product_type=self.mandate_market_data_source_product_type,
            instrument_resolution_mode=self.mandate_instrument_resolution_mode,
        )

    @property
    def profile(self) -> BaseEnvironmentProfile:
        profiles: dict[Environment, BaseEnvironmentProfile] = {
            Environment.DEV: DevProfile(),
            Environment.BACKTEST: BacktestProfile(),
            Environment.PAPER: PaperProfile(),
            Environment.TESTNET: TestnetProfile(),
            Environment.LIVE: LiveProfile(),
        }
        return profiles[self.app.environment]


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
