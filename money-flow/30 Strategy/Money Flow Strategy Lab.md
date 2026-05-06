# Money Flow Strategy Lab

Up: [[Money Flow Command Center]]

## Purpose

Keep the strategy thread visible while routing and execution work becomes complex.

## Current Money Flow Role

Money Flow is the first strategy family. It is not the universal vocabulary of the platform.

Current Strategy Validation focus: `SV1.13` founder review of first Hyperliquid public campaign evidence packs. Public Hyperliquid BTC/ETH/SOL identity values are verified and seeded as research-only/non-trading, the 9 local Hyperliquid public `1h`/`4h` YTD plus recent `15m` files were imported with `25848` persisted candles, and SV1.13 generated component-scoped evidence packs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`. January 2026 remains archival/vendor-data-required. SV1.12.5 added an all-supported-venue public-data plan: Aster/Binance have 18 additional native-trade-count candidate files under `/tmp/money-flow-sv1125-supported-venues-public/csv`, OKX/Coinbase need a trade-count source or contract decision, and Kraken needs archive/vendor/operator coverage. Paper trading is not approved.

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

Important caution: this is review commentary, not an accepted strategy-rule change. First Hyperliquid public campaign evidence packs now exist for founder review, but they do not prove future outcomes or approve paper trading. Do not add stop-losses, optimize RSI bands, change MACD exits, or alter sizing until evidence review justifies a separate strategy-change phase and that phase is explicitly approved.

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
