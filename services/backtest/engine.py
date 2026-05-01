"""Legacy backtest interface.

SV1.0 adds the explicit Money Flow validation runner under
``services.strategy_validation``. This legacy interface remains unimplemented
because it does not carry the explicit assumptions required by SV1.0 reports.
"""

from core.interfaces.services import BacktestEngine


class HistoricalBacktestEngine(BacktestEngine):
    async def run_strategy_window(self, sleeve_id: str, start_at: str, end_at: str) -> str:
        raise NotImplementedError(
            "Use services.strategy_validation.MoneyFlowBacktestService with explicit fee, slippage, "
            "capital, venue, symbol, and component assumptions."
        )
