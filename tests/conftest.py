from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from core.config.settings import AppSettings, get_settings

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_SETTINGS_ENV_PREFIXES = (
    "APP_",
    "DB_",
    "REDIS_",
    "LOG_",
    "API_",
    "UAT_",
    "SANDBOX_",
    "PAPER_",
    "LIVE_",
    "PRIVATE_",
    "EXCHANGE_",
    "HYPERLIQUID_",
    "ASTER_",
    "OKX_",
    "COINBASE_ADVANCED_",
    "BINANCE_",
    "KRAKEN_",
    "ACTIVE_",
    "MANDATE_",
    "RISK_",
    "EXECUTION_",
    "ALERTS_",
    "MARKET_DATA_",
    "SLEEVE_",
    "MONEY_FLOW_",
)


@pytest.fixture(autouse=True)
def _isolate_settings_from_local_env(monkeypatch: pytest.MonkeyPatch):
    original_env_file = AppSettings.model_config.get("env_file")
    AppSettings.model_config["env_file"] = None
    get_settings.cache_clear()
    for key in list(os.environ):
        if key.startswith(_SETTINGS_ENV_PREFIXES):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("API_RUNTIME_MODE", "test")
    monkeypatch.setenv("API_AUTH_DISABLED_FOR_TESTS", "true")
    yield
    get_settings.cache_clear()
    AppSettings.model_config["env_file"] = original_env_file
