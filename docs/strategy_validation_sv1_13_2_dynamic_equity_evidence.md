# SV1.13.2 Dynamic Equity Evidence

Recorded at: `2026-05-07T10:19:14Z`

## Status

SV1.13.2 adds `dynamic_equity_pct` as a Strategy Validation capital sizing mode. The existing default remains `constant_initial_capital_notional_per_trade`.

This phase changes capital simulation only. It does not change Money Flow rules, optimize parameters, approve paper trading, add live execution, call exchange endpoints, import candles, or create routing/execution artifacts.

Final evidence status: `dynamic_equity_research_ready_for_founder_review`

Paper-trading design remains deferred until founder/operator review explicitly scopes a later phase.

## Scope

Evidence scope is still Hyperliquid USDC perpetual public-candle research only.

Campaign data source:

- `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json`
- Imported candles: `25848`
- Symbols: `BTC`, `ETH`, `SOL`
- Components: `sleeve_15m`, `sleeve_1h`, `sleeve_4h`

Read-only dynamic-equity batch commands wrote temporary JSON outputs under `/tmp` and did not generate evidence packs.

## Capital Sizing Modes

`constant_initial_capital_notional_per_trade`:

- Each opened trade uses `initial_capital * position_notional_pct`.
- With `initial_capital=10000` and `position_notional_pct=1.0`, each opened trade uses `10000` notional.
- Realized equity changes PnL and drawdown metrics, but it does not change the next trade size.

`dynamic_equity_pct`:

- Each opened trade uses `current_realized_equity * position_notional_pct`.
- Current realized equity starts at `10000`.
- Current realized equity updates after every closed trade by adding trade net PnL.
- If current realized equity is zero or below, new entries are skipped with `dynamic_equity_depleted`.

Important limitation: dynamic equity is sequential per validation scenario. It is not full exchange margin, funding, liquidation, maintenance-margin, or multi-symbol portfolio simulation.

## Dynamic ETH 1h Results

The founder question was whether a `10000` starting account grows or shrinks under dynamic equity sizing. ETH `sleeve_1h` was the main positive pocket in SV1.13.1, so it is shown explicitly.

| fill timing | fee bps | slippage bps | trades | starting equity | ending equity | net account PnL | return on start | max closed DD | max MTM DD | profit factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `next_candle_open` | 2.5 | 1 | 117 | 10000 | 12653.58690428 | 2653.58690428 | 0.26535869 | 1418.20378153 | 1525.29695009 | 1.43935010 |
| `next_candle_open` | 2.5 | 2 | 117 | 10000 | 12360.85821349 | 2360.85821349 | 0.23608582 | 1477.10862236 | 1573.90944487 | 1.38539788 |
| `next_candle_open` | 5 | 1 | 117 | 10000 | 11934.87998294 | 1934.87998294 | 0.19348800 | 1564.40607588 | 1646.00866866 | 1.30922857 |
| `next_candle_open` | 5 | 2 | 117 | 10000 | 11658.70973919 | 1658.70973919 | 0.16587097 | 1621.42776241 | 1694.70111513 | 1.26160434 |
| `next_candle_close` | 2.5 | 1 | 115 | 10000 | 13175.56543318 | 3175.56543318 | 0.31755654 | 1285.01739029 | 1363.54078731 | 1.64102408 |
| `next_candle_close` | 2.5 | 2 | 115 | 10000 | 12875.91191609 | 2875.91191609 | 0.28759119 | 1325.77809142 | 1404.63094755 | 1.57086988 |
| `next_candle_close` | 5 | 1 | 115 | 10000 | 12439.78810177 | 2439.78810177 | 0.24397881 | 1386.45334530 | 1465.80043006 | 1.47186976 |
| `next_candle_close` | 5 | 2 | 115 | 10000 | 12156.79863880 | 2156.79863880 | 0.21567986 | 1426.15090344 | 1505.80454484 | 1.41004202 |

Observed ETH `sleeve_1h` interpretation:

- Starting equity was `10000` in every scenario.
- Ending equity stayed above `10000` across both tested fill timings and both tested cost levels.
- Highest-cost ETH `sleeve_1h` scenario ended at `11658.70973919` for `next_candle_open` and `12156.79863880` for `next_candle_close`.
- Maximum ETH `sleeve_1h` mark-to-market drawdown across these rows was `1694.70111513`.
- ETH `sleeve_1h` remained the concentrated positive area; this does not prove broad Money Flow behavior across symbols or components.

## 1h Symbol Context

| symbol | observation under dynamic equity |
| --- | --- |
| `ETH` | Ended above starting equity across all tested 1h fill/cost scenarios. |
| `BTC` | `next_candle_open` was positive in lower-cost scenarios but the highest-cost open row slipped below starting equity; all `next_candle_close` rows ended below starting equity. |
| `SOL` | Lower-cost `next_candle_open` rows were slightly above starting equity, but higher-cost open rows and all close rows ended below starting equity. |

This is still scenario-level evidence. BTC, ETH, and SOL were not simulated as one shared portfolio account.

## Component Summary

| component | window | dynamic-equity observation |
| --- | --- | --- |
| `sleeve_15m` | `2026-03-15T00:00:00Z -> 2026-05-05T00:00:00Z` | All BTC/ETH/SOL tested dynamic scenarios ended below starting equity. |
| `sleeve_1h` | `2026-01-01T00:00:00Z -> 2026-05-05T00:00:00Z` | ETH stayed above starting equity across tested assumptions; BTC/SOL were mixed and cost/fill sensitive. |
| `sleeve_4h` | `2026-01-01T00:00:00Z -> 2026-05-05T00:00:00Z` | All BTC/ETH/SOL tested dynamic scenarios ended below starting equity. |

## Fill Timing And Cost Sensitivity

- ETH `sleeve_1h` stayed above starting equity under `next_candle_open` and `next_candle_close`.
- Higher fees and slippage reduced ending equity in every ETH `sleeve_1h` row.
- BTC and SOL `sleeve_1h` were more sensitive to fill timing and cost assumptions than ETH.
- 15m and 4h did not become favorable under dynamic equity sizing in this public campaign.

## Drawdown Interpretation

- ETH `sleeve_1h` had positive net account PnL in every tested dynamic scenario, but drawdown remained material relative to starting equity.
- ETH `sleeve_1h` maximum mark-to-market drawdown ranged from `1363.54078731` to `1694.70111513`.
- Dynamic equity reduces later notional after losses and increases later notional after wins, but it does not model liquidation, funding, margin requirements, or simultaneous exposure.

## Limitations

- This is not full portfolio/account simulation across BTC/ETH/SOL.
- This is not exchange margin simulation.
- Funding, liquidation, maintenance margin, order book depth, partial fills, venue latency, taxes, borrow costs, and exact order matching are not modeled.
- Results remain Hyperliquid public-candle research only.
- Cross-venue evidence remains deferred.
- Paper trading remains deferred.

## Next Manual Review Questions

- Is ETH `sleeve_1h` concentration acceptable enough to scope a later paper-trading design experiment?
- Does the founder accept the drawdown relative to starting equity for the positive ETH scenarios?
- Should a later phase add portfolio-level capital allocation across symbols before any paper experiment design?
- Should funding/liquidation/margin modeling be added before a paper-design phase?

## SV1.13.3 / Later Deferred Work

- Portfolio-level multi-symbol simulation.
- Funding and margin/liquidation modeling.
- Out-of-sample validation.
- Paper-trading design, only if explicitly accepted and scoped later.
- Cross-venue comparative campaigns after separate identity/import/source-policy gates.
