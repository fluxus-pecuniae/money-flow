# PT0.0.2 Historical Strategy Replay Cockpit

## Scope

| Area | Status | Notes |
| --- | --- | --- |
| Historical replay cockpit | implemented | Dashboard now has a `Historical Replay` tab for BTC/ETH/SOL strategy replay review. |
| Strategy truth source | verified | Replay uses historical public candle replay data from the SV1.17 baseline export. |
| Testnet strategy truth | verified | Hyperliquid testnet market data is not strategy truth. Testnet remains sandbox execution plumbing only. |
| Orders | verified | No orders are submitted by PT0.0.2. No order controls were added. |
| Money Flow rules | verified | Money Flow rules are unchanged. The baseline replay remains the OG replay/strategy; the MACD-removed replay is research-only. |

## Why Testnet Is Not Strategy Truth

Hyperliquid testnet prices and order books are not representative enough for strategy validation. PT0.0.2 separates the project into three lanes:

| Lane | Source | Purpose |
| --- | --- | --- |
| Lane A - Historical Strategy Truth | historical/mainnet/public candle replay data | Visual validation of Money Flow entries, exits, costs, and dynamic equity. |
| Lane B - Paper Runtime Truth | internal 10,000 USDC paper-equity ledger | Simulated account equity and PnL tracking. |
| Lane C - Sandbox Execution Plumbing | Hyperliquid testnet/sandbox | Submit/cancel/reconcile plumbing only. |

## Historical Data Source

| Item | Status | Notes |
| --- | --- | --- |
| Source kind | implemented | `trusted_offline_historical_candles` from `/tmp/money-flow-sv117-full-suite.json`. |
| Source hash | verified | Recorded in `docs/pt0_0_2_historical_strategy_replay_summary.json`. |
| Persisted DB audit | needs_verification | Default local DB host was unreachable in this shell, so the committed replay summary records `historical_db_unreachable` while using the trusted offline SV1.17 export. |
| Replay JSON | implemented | `docs/pt0_0_2_historical_strategy_replay_summary.json`. |

## Replay Strategy Variants

| Strategy | Status | Scope |
| --- | --- | --- |
| OG replay / strategy | implemented | Current baseline Money Flow rules with MACD entry confirmation and MACD-rollover exits. |
| MACD removed | implemented | Research-only replay variant across all BTC/ETH/SOL 15m/1h/4h datasets. MACD entry confirmation and MACD-rollover exit checks are removed; other entry, exit, fill, cost, and dynamic-equity rules remain unchanged. |

The dashboard `Historical Replay` tab now has a replay-strategy dropdown so the founder can switch between the OG replay/strategy and the MACD-removed research replay without treating the variant as production strategy truth.

## Replay-Ready Datasets

| Symbol | 15m | 1h | 4h |
| --- | --- | --- | --- |
| BTC | verified | verified | verified |
| ETH | verified | verified | verified |
| SOL | verified | verified | verified |

All nine symbol/timeframe datasets are available. The dashboard summary now includes 18 replay combinations: nine OG baseline replays and nine MACD-removed research replays.

## Fill And Cost Assumptions

| Assumption | Status | Notes |
| --- | --- | --- |
| `next_candle_open` | implemented | Default founder view. |
| `next_candle_close` | implemented | Available selector option. |
| `same_candle_close_research_only` | implemented | Clearly labeled research-only. |
| Fees | implemented | `fee_bps = 5`. |
| Slippage | implemented | `slippage_bps = 3`. |

## Dynamic Equity Policy

| Item | Status | Notes |
| --- | --- | --- |
| Initial equity | implemented | 10,000 USDC. |
| Capital sizing | implemented | `dynamic_equity_pct`. |
| Sizing basis | implemented | `realized_equity`. |
| Risk display basis | implemented | `realized_plus_unrealized`. |
| Static reset | verified | Replay does not reset each trade to 10,000 USDC. |

## Dashboard Replay Cockpit

| Feature | Status | Notes |
| --- | --- | --- |
| Historical Replay tab | implemented | Added to the dashboard navigation. |
| Replay strategy selector | implemented | Dropdown supports `OG replay / strategy` and `MACD removed`. |
| TradingView chart | implemented | Historical candlesticks with visible price scale and bounded chart height. |
| Indicator overlays | implemented | EMA5, EMA10, and SMA20 render on chart; RSI/MACD values remain available in the trade inspector/export. MACD values are inspectable even when the MACD-removed replay variant does not use MACD as a gate. |
| Entry markers | implemented | Green markers represent historical replay entry fills only. |
| Exit markers | implemented | Red markers represent historical replay exit fills; yellow markers represent trim/reduce events when present. |
| Trade inspector | implemented | Shows entry/exit timing, reasons, indicators, costs, PnL, equity, drawdown, and regime. |
| Equity curve panel | implemented | Shows initial/ending equity, net PnL, drawdown, trade count, and selected-trade equity. |
| BTC/ETH/SOL comparison | implemented | Compares each symbol/timeframe independently. |
| Sandbox ledger separation | implemented | UAT3.4 sandbox execution ledger remains visible but separate from historical replay equity. |

## OG Replay / Strategy Comparison Summary

| Scenario | Ending Equity | Net PnL | Trades | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| BTC 15m | 6,891.08 | -3,108.92 | 221 | 3,145.09 |
| BTC 1h | 9,685.43 | -314.57 | 135 | 1,799.77 |
| BTC 4h | 8,557.58 | -1,442.42 | 39 | 1,880.42 |
| ETH 15m | 6,861.06 | -3,138.94 | 210 | 3,383.23 |
| ETH 1h | 11,388.93 | 1,388.93 | 117 | 1,677.71 |
| ETH 4h | 8,139.46 | -1,860.54 | 34 | 2,420.26 |
| SOL 15m | 6,464.36 | -3,535.64 | 214 | 3,539.74 |
| SOL 1h | 9,277.73 | -722.27 | 125 | 2,150.85 |
| SOL 4h | 6,772.35 | -3,227.65 | 36 | 3,492.34 |

## MACD Removed Research Replay Comparison Summary

| Scenario | Ending Equity | Net PnL | Trades | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| BTC 15m | 6,337.87 | -3,662.13 | 274 | 3,697.14 |
| BTC 1h | 9,242.95 | -757.05 | 157 | 1,856.12 |
| BTC 4h | 9,196.61 | -803.39 | 40 | 1,321.60 |
| ETH 15m | 6,136.50 | -3,863.50 | 276 | 4,390.04 |
| ETH 1h | 10,140.55 | 140.55 | 149 | 1,842.01 |
| ETH 4h | 7,988.11 | -2,011.89 | 40 | 2,569.40 |
| SOL 15m | 5,433.45 | -4,566.55 | 276 | 4,600.42 |
| SOL 1h | 8,260.51 | -1,739.49 | 143 | 2,854.24 |
| SOL 4h | 6,628.20 | -3,371.80 | 37 | 3,371.80 |

## Limitations

| Limitation | Status | Notes |
| --- | --- | --- |
| Playback controls | deferred | Static replay display is implemented first; play/pause and step-one-candle controls are deferred to PT0.0.3. |
| DB-backed live replay regeneration | needs_verification | Local DB connectivity must be restored or explicitly configured before regenerating directly from persisted candles. |
| RSI/MACD chart panes | deferred | RSI/MACD values are exported and shown in the trade inspector; separate chart panes can be added later. |
| MACD-removed production interpretation | deferred | The MACD-removed result is research-only and does not approve a Money Flow rule change. |

## Next Recommended Phase

`PT0.0.3 - Historical Replay Playback Controls + Market Structure Inspector` may be scoped next for play/pause, candle stepping, selected-trade replay, support/resistance diagnostics, recent high/low context, ATR, and invalidation context.

`PT0.1 - Supervised Paper Runtime Using Trusted Market Data` remains a later phase. It should use trusted market data for strategy truth, keep testnet as execution plumbing, and preserve the internal 10,000 USDC paper-equity ledger.

## Boundary Confirmation

| Boundary | Status |
| --- | --- |
| PT0.0.2 is historical replay visualization | verified |
| Historical/mainnet candle data is strategy truth | verified |
| Hyperliquid testnet market data is not strategy truth | verified |
| Testnet remains execution plumbing only | verified |
| Paper trading remains approved for Hyperliquid testnet/sandbox | verified |
| Live trading is not approved | verified |
| No orders are submitted by PT0.0.2 | verified |
| Money Flow rules are unchanged | verified |
| MACD removed is research-only | verified |
