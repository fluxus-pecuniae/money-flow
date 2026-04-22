"""Environment profiles describing operational behavior by runtime mode."""

from __future__ import annotations

from pydantic import BaseModel

from core.domain.enums import Environment


class BaseEnvironmentProfile(BaseModel):
    environment: Environment
    order_submission_enabled: bool
    market_data_realtime: bool
    exchange_connectivity_required: bool
    database_required: bool
    notes: str


class DevProfile(BaseEnvironmentProfile):
    environment: Environment = Environment.DEV
    order_submission_enabled: bool = False
    market_data_realtime: bool = False
    exchange_connectivity_required: bool = False
    database_required: bool = True
    notes: str = "Local development profile with safe defaults."


class BacktestProfile(BaseEnvironmentProfile):
    environment: Environment = Environment.BACKTEST
    order_submission_enabled: bool = False
    market_data_realtime: bool = False
    exchange_connectivity_required: bool = False
    database_required: bool = True
    notes: str = "Historical simulation profile using replayed data."


class PaperProfile(BaseEnvironmentProfile):
    environment: Environment = Environment.PAPER
    order_submission_enabled: bool = False
    market_data_realtime: bool = True
    exchange_connectivity_required: bool = False
    database_required: bool = True
    notes: str = "Live-market paper trading profile with simulated execution."


class TestnetProfile(BaseEnvironmentProfile):
    environment: Environment = Environment.TESTNET
    order_submission_enabled: bool = True
    market_data_realtime: bool = True
    exchange_connectivity_required: bool = True
    database_required: bool = True
    notes: str = "Exchange-connected validation profile against testnet infrastructure."


class LiveProfile(BaseEnvironmentProfile):
    environment: Environment = Environment.LIVE
    order_submission_enabled: bool = True
    market_data_realtime: bool = True
    exchange_connectivity_required: bool = True
    database_required: bool = True
    notes: str = "Production profile for real capital and real exchange sessions."

