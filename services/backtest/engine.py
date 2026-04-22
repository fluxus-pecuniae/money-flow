"""Backtest engine placeholder."""

from core.interfaces.services import BacktestEngine


class HistoricalBacktestEngine(BacktestEngine):
    async def run_strategy_window(self, sleeve_id: str, start_at: str, end_at: str) -> str:
        raise NotImplementedError("Backtesting is explicitly out of Phase 1 scope.")

