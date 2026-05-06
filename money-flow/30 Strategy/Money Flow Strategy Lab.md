# Money Flow Strategy Lab

Up: [[Money Flow Command Center]]

## Purpose

Keep the strategy thread visible while routing and execution work becomes complex.

## Current Money Flow Role

Money Flow is the first strategy family. It is not the universal vocabulary of the platform.

Current Strategy Validation focus: `SV1.12.5` remains guarded canonical candle import readiness before first real canonical evidence packs. Public Hyperliquid BTC/ETH/SOL identity values are verified, January 2026 is archival/vendor-data-required, and 9 local Hyperliquid public `1h`/`4h` YTD plus recent `15m` files exist under `/tmp/money-flow-sv1124-public-ytd-recent/csv`, but identity is not seeded and preflight is blocked. SV1.12.5 added an all-supported-venue public-data plan: Aster/Binance have 18 additional native-trade-count candidate files under `/tmp/money-flow-sv1125-supported-venues-public/csv`, OKX/Coinbase need a trade-count source or contract decision, and Kraken needs archive/vendor/operator coverage. No first real canonical Money Flow evidence packs have been generated yet, and paper trading is not approved.

The original strategy idea involved:

- 5 EMA
- 10 EMA
- 20 SMA
- RSI
- MACD
- 15m / 1h / 4h lanes

## Current Code Surface

- `services/strategy/money_flow.py`
- `services/strategy/engine.py`
- `services/indicators/service.py`
- `services/planning/service.py`

## Questions To Keep Alive

- Are the 15m, 1h, and 4h behaviors still faithful to the intended Money Flow logic?
- What evidence proves or disproves the strategy alpha?
- What strategy families should come after Money Flow?
- Which execution controls are needed because the strategy actually needs them, not because the router can do them?

## Related Notes

- [[10 Components/Strategy Engine]]
- [[10 Components/Market Data and Indicators]]
- [[30 Strategy/Product North Star]]

## Strategy Validation Cautions From External Review

The 2026-05-06 external strategy review described Money Flow as a coherent but unvalidated long-only momentum strategy across the 15m, 1h, and 4h sleeves. Current entry logic requires bullish moving-average stack, RSI in a relatively narrow momentum band, MACD confirmation, and limited price extension above EMA5. Exits are indicator-based through moving-average alignment break, MACD rollover, or RSI trim trigger.

Important caution: this is review commentary, not an accepted strategy-rule change. No first real evidence packs have been generated yet, so the strategy remains unproven. Do not add stop-losses, optimize RSI bands, change MACD exits, or alter sizing until the Strategy Validation evidence track has produced reviewable results and a separate strategy-change phase is explicitly approved.

Concerns to track before paper trading or rule changes:

- No hard stop-loss exists; indicator exits may be too slow in fast crypto selloffs.
- RSI bands may be narrow and could suppress trade frequency or miss trend continuation.
- MACD exits, especially on higher timeframes, may lag and give back gains.
- Backtest sizing assumptions need review; 100% notional per trade can distort drawdown interpretation.
- Same-candle close fill timing is research-only/optimistic and must not be used for paper/live readiness claims.
- Long-only behavior is exposed to bear markets unless filters or risk controls prove sufficient.
- Confidence score may be cosmetic if it clusters near 0.90-0.99 after any valid entry.
- Parameters may be handcrafted; out-of-sample validation is required before trusting them.

Future evidence review should prioritize next-candle-open fill timing, explicit fee/slippage/drawdown truth, Sharpe/Sortino or equivalent risk-adjusted metrics, out-of-sample validation, and only then a scoped discussion of ATR stops or other rule changes.
