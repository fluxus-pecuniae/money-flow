"""Dependency providers for the API layer."""

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from core.security import APIAuthScope, APIPrincipal
from core.config.settings import AppSettings, get_settings
from core.interfaces.hyperliquid import HyperliquidAdapterContract
from core.interfaces.services import (
    ExchangeAdapter,
    ExecutionService,
    IndicatorService,
    MandateTradePlanningService,
    MarketDataService,
    PortfolioService,
    RiskEngine,
    RoutingAssessmentService,
    RuntimeContextService,
    StrategyEngine,
    VenueRegistryService,
)
from services.execution.service import DefaultExecutionService
from services.exchange.aster.adapter import AsterExchangeAdapter
from services.exchange.coinbase.adapter import CoinbaseAdvancedTradeExchangeAdapter
from services.exchange.hyperliquid.adapter import HyperliquidExchangeAdapter
from services.exchange.okx.adapter import OkxExchangeAdapter
from services.exchange.registry import DefaultVenueRegistryService
from services.indicators.service import DefaultIndicatorService
from services.market_data.service import DefaultMarketDataService
from services.portfolio.service import DefaultPortfolioService
from services.planning.service import DefaultTradePlanningService
from services.risk.engine import DefaultRiskEngine
from services.routing.service import DefaultRoutingAssessmentService
from services.runtime.context import DefaultRuntimeContextService
from services.strategy.engine import MandateStrategyEngine


def get_app_settings() -> AppSettings:
    return get_settings()


def _token_principals(settings: AppSettings) -> dict[str, APIPrincipal]:
    principals: dict[str, APIPrincipal] = {}
    auth = settings.api_auth
    if auth.read_only_operator_token:
        principals[auth.read_only_operator_token] = APIPrincipal(
            principal_id="read_only_operator",
            scopes=frozenset({APIAuthScope.READ_ONLY_OPERATOR}),
            auth_mode="bearer",
        )
    if auth.operator_token:
        principals[auth.operator_token] = APIPrincipal(
            principal_id="operator",
            scopes=frozenset({APIAuthScope.READ_ONLY_OPERATOR, APIAuthScope.OPERATOR}),
            auth_mode="bearer",
        )
    if auth.automation_admin_token:
        principals[auth.automation_admin_token] = APIPrincipal(
            principal_id="automation_admin",
            scopes=frozenset(
                {
                    APIAuthScope.READ_ONLY_OPERATOR,
                    APIAuthScope.OPERATOR,
                    APIAuthScope.AUTOMATION_ADMIN,
                }
            ),
            auth_mode="bearer",
        )
    if auth.uat_admin_token:
        principals[auth.uat_admin_token] = APIPrincipal(
            principal_id="uat_admin",
            scopes=frozenset(
                {
                    APIAuthScope.READ_ONLY_OPERATOR,
                    APIAuthScope.OPERATOR,
                    APIAuthScope.UAT_ADMIN,
                }
            ),
            auth_mode="bearer",
        )
    if auth.admin_token:
        principals[auth.admin_token] = APIPrincipal(
            principal_id="admin",
            scopes=frozenset({APIAuthScope.ADMIN}),
            auth_mode="bearer",
        )
    return principals


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def require_api_scope(required_scope: APIAuthScope) -> Callable[..., APIPrincipal]:
    async def _require_api_scope(
        authorization: str | None = Header(default=None),
        settings: AppSettings = Depends(get_app_settings),
    ) -> APIPrincipal:
        auth = settings.api_auth
        runtime_mode = settings.runtime_safety.runtime_mode
        if not auth.enabled:
            if auth.disabled_for_tests and runtime_mode == "test":
                return APIPrincipal(
                    principal_id="test_auth_disabled",
                    scopes=frozenset({APIAuthScope.ADMIN}),
                    auth_mode="test_bypass",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API authentication is disabled only for explicit test runtime.",
            )
        if auth.disabled_for_tests and runtime_mode == "test":
            return APIPrincipal(
                principal_id="test_auth_disabled",
                scopes=frozenset({APIAuthScope.ADMIN}),
                auth_mode="test_bypass",
            )
        token = _extract_bearer_token(authorization)
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        principal = _token_principals(settings).get(token)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not principal.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient API authorization scope: {required_scope.value}.",
            )
        return principal

    return _require_api_scope


require_read_only_operator = require_api_scope(APIAuthScope.READ_ONLY_OPERATOR)
require_operator = require_api_scope(APIAuthScope.OPERATOR)
require_admin = require_api_scope(APIAuthScope.ADMIN)
require_automation_admin = require_api_scope(APIAuthScope.AUTOMATION_ADMIN)
require_uat_admin = require_api_scope(APIAuthScope.UAT_ADMIN)


def get_hyperliquid_adapter() -> HyperliquidAdapterContract:
    settings = get_settings()
    runtime_context = DefaultRuntimeContextService(settings)
    return HyperliquidExchangeAdapter(settings, runtime_context_service=runtime_context)


def _build_exchange_adapter(settings: AppSettings) -> ExchangeAdapter:
    venue = settings.exchange.venue.lower()
    if venue == "hyperliquid":
        runtime_context = DefaultRuntimeContextService(settings)
        return HyperliquidExchangeAdapter(settings, runtime_context_service=runtime_context)
    if venue == "aster":
        return AsterExchangeAdapter(settings)
    if venue == "okx":
        return OkxExchangeAdapter(settings)
    if venue in {"coinbase", "coinbase_advanced_trade"}:
        return CoinbaseAdvancedTradeExchangeAdapter(settings)
    raise ValueError(f"Unsupported active exchange venue: {settings.exchange.venue}")


def get_exchange_adapter() -> ExchangeAdapter:
    return _build_exchange_adapter(get_settings())


def get_venue_registry_service() -> VenueRegistryService:
    return DefaultVenueRegistryService(get_settings())


def get_runtime_context_service() -> RuntimeContextService:
    return DefaultRuntimeContextService(get_settings())


def get_market_data_service() -> MarketDataService:
    settings = get_settings()
    adapter = get_exchange_adapter()
    return DefaultMarketDataService(adapter=adapter, settings=settings)


def get_indicator_service() -> IndicatorService:
    return DefaultIndicatorService(get_settings())


def get_strategy_engine() -> StrategyEngine:
    settings = get_settings()
    runtime_context = DefaultRuntimeContextService(settings)
    return MandateStrategyEngine(
        indicator_service=DefaultIndicatorService(settings),
        market_data_service=DefaultMarketDataService(settings=settings),
        portfolio_service=DefaultPortfolioService(settings, runtime_context_service=runtime_context),
        settings=settings,
        runtime_context_service=runtime_context,
    )


def get_portfolio_service() -> PortfolioService:
    settings = get_settings()
    return DefaultPortfolioService(
        settings,
        runtime_context_service=DefaultRuntimeContextService(settings),
    )


def get_trade_planning_service() -> MandateTradePlanningService:
    settings = get_settings()
    runtime_context = DefaultRuntimeContextService(settings)
    return DefaultTradePlanningService(
        settings,
        runtime_context_service=runtime_context,
        venue_registry_service=DefaultVenueRegistryService(settings),
    )


def get_execution_service() -> ExecutionService:
    settings = get_settings()
    return DefaultExecutionService(
        settings,
        venue_registry_service=DefaultVenueRegistryService(settings),
    )


def get_risk_engine() -> RiskEngine:
    settings = get_settings()
    runtime_context = DefaultRuntimeContextService(settings)
    planning_service = DefaultTradePlanningService(
        settings,
        runtime_context_service=runtime_context,
        venue_registry_service=DefaultVenueRegistryService(settings),
    )
    return DefaultRiskEngine(
        settings,
        runtime_context_service=runtime_context,
        planning_service=planning_service,
        execution_service=DefaultExecutionService(
            settings,
            venue_registry_service=DefaultVenueRegistryService(settings),
        ),
        portfolio_service=DefaultPortfolioService(settings, runtime_context_service=runtime_context),
    )


def get_routing_assessment_service() -> RoutingAssessmentService:
    settings = get_settings()
    runtime_context = DefaultRuntimeContextService(settings)
    planning_service = DefaultTradePlanningService(
        settings,
        runtime_context_service=runtime_context,
        venue_registry_service=DefaultVenueRegistryService(settings),
    )
    return DefaultRoutingAssessmentService(
        settings,
        planning_service=planning_service,
    )
