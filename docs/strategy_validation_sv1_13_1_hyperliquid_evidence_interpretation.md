# SV1.13.1 Hyperliquid Evidence Interpretation

## Executive Interpretation

SV1.13.1 interprets the first Hyperliquid public campaign evidence packs generated in SV1.13. It does not rerun imports, does not generate new evidence packs, does not change Money Flow rules, and does not approve paper or live trading.

The evidence is research-only Hyperliquid USDC perpetual public-candle evidence. Grouped totals in the evidence packs are descriptive sums across multiple research runs. They are not one tradable account result, because each group can include multiple symbols, fill timings, fee assumptions, slippage assumptions, and component/window scenarios.

Sizing also matters: the SV1.13 evidence uses constant initial-capital notional per trade. With initial capital `10000` and position notional pct `1.0`, every opened trade uses `10000` notional. Realized equity changes PnL and drawdown metrics, but it does not reduce, compound, or stop the next trade size.

High-level interpretation:

- `sleeve_15m` was negative across all 36 tested scenarios.
- `sleeve_1h` was positive in aggregate across research runs, but the positive result was concentrated in ETH.
- `sleeve_4h` was negative across all 36 tested scenarios.
- ETH `sleeve_1h` was positive across all tested fill timing and fee/slippage scenarios.
- BTC `sleeve_1h` was positive under same-candle-close and next-candle-open assumptions for 3 of 4 cost scenarios, but negative under all next-candle-close cost scenarios.
- SOL `sleeve_1h` was mixed and weakened materially under next-candle-close and higher cost assumptions.

Final interpretation status: `ready_for_founder_review`.

Paper-trading design remains deferred until the founder manually accepts scope, risk, and follow-up validation requirements.

## Evidence Packs Analyzed

Evidence packs analyzed in this report are the three component-scoped SV1.13 Hyperliquid public campaign packs.

| component | evidence pack path | batch report |
| --- | --- | --- |
| `sleeve_15m` | `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_15m/20260506T231210Z` | `batch_report.json`, `batch_report.md`, `manifest.json` |
| `sleeve_1h` | `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_1h/20260506T231210Z` | `batch_report.json`, `batch_report.md`, `manifest.json` |
| `sleeve_4h` | `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_4h/20260506T231210Z` | `batch_report.json`, `batch_report.md`, `manifest.json` |

Campaign config used: `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json`.

Scope: Hyperliquid USDC perpetual public candles only. Aster, Binance, OKX, Coinbase, and Kraken remain deferred comparative work and are not part of this evidence. The cross-venue comparison remains deferred.

## Imported Candle Counts

| symbol | 15m | 1h | 4h | total |
| --- | ---: | ---: | ---: | ---: |
| BTC | 4,896 | 2,976 | 744 | 8,616 |
| ETH | 4,896 | 2,976 | 744 | 8,616 |
| SOL | 4,896 | 2,976 | 744 | 8,616 |
| total | 14,688 | 8,928 | 2,232 | 25,848 |

Window convention remains `(start_at, end_at]`: candle closes exactly at `start_at` are excluded, and closes on or before `end_at` are included.

## Grouped Aggregate Semantics

SV1.13 batch reports group runs by fill timing, component, symbol, date window, and regime. In those grouped rows:

- `sum_net_pnl_across_research_runs` is a sum across completed research runs in the group.
- `sum_trades_across_research_runs` is a sum across completed research runs in the group.
- Fee and slippage totals are also sums across completed research runs in the group.
- `average_net_pnl_per_completed_run` is the mean across completed runs in the group.
- These are descriptive aggregate research metrics, not one account-level or one-scenario strategy PnL.

Do not read a grouped sum such as ETH plus BTC plus SOL across multiple fill timing and fee/slippage assumptions as one deployable strategy result. Scenario-level rows are the correct evidence surface for assumption-specific interpretation.

## Capital Sizing Semantics

SV1.13 uses `constant_initial_capital_notional_per_trade`.

| field | SV1.13 value |
| --- | --- |
| initial capital | `10000` |
| position notional pct | `1.0` |
| entry notional formula | `initial_capital * position_notional_pct` |
| entry notional per opened trade | `10000` |
| equity effect on next trade size | `none` |
| realized equity usage | `net PnL, closed-trade drawdown, mark-to-market drawdown, return on initial capital` |

Trade quantity is calculated from the constant entry notional and the simulated slippage-adjusted entry price:

```text
size = entry_notional / entry_price
```

Losses and gains are included in realized equity for drawdown and return calculations. They are not used to shrink the next trade, compound after wins, halt entries after losses, or model available account margin. This evidence is therefore a constant-notional research replay, not a dynamic account-equity portfolio simulation.

Founder interpretation implication: drawdown and return-on-initial-capital are still useful risk diagnostics, but the scenario rows should not be read as dynamic equity sizing results. A future evidence phase should add a separate `dynamic_equity_pct` capital mode before paper-trading design uses account-style sizing assumptions.

## Component And Symbol Summary

| component | symbol | positive scenarios | net PnL range | sum net PnL across research runs | sum trades across research runs |
| --- | --- | ---: | ---: | ---: | ---: |
| `sleeve_15m` | BTC | 0/12 | -3,691.63 to -1,443.97 | -30,705.18 | 2,616 |
| `sleeve_15m` | ETH | 0/12 | -3,710.69 to -1,183.85 | -30,119.19 | 2,500 |
| `sleeve_15m` | SOL | 0/12 | -4,327.01 to -1,693.70 | -36,964.20 | 2,544 |
| `sleeve_1h` | BTC | 6/12 | -1,756.10 to 1,147.77 | -615.10 | 1,608 |
| `sleeve_1h` | ETH | 12/12 | 1,509.74 to 3,044.47 | 26,706.06 | 1,396 |
| `sleeve_1h` | SOL | 5/12 | -1,192.99 to 670.94 | -2,041.03 | 1,480 |
| `sleeve_4h` | BTC | 0/12 | -1,512.06 to -158.07 | -11,867.54 | 452 |
| `sleeve_4h` | ETH | 0/12 | -3,189.72 to -1,630.85 | -26,505.79 | 404 |
| `sleeve_4h` | SOL | 0/12 | -3,823.40 to -3,068.05 | -42,008.90 | 424 |

## Scenario-Level Results

The table below keeps fee/slippage/fill-timing scenario truth visible while compressing the four fee/slippage rows for each component, symbol, and fill timing into ranges. The four tested fee/slippage pairs are `2/1`, `2/3`, `5/1`, and `5/3`.

| component | symbol | fill timing | fee/slippage scenarios | net PnL range | gross PnL range | fees range | slippage cost range | trades range | win-rate range | profit-factor range | closed DD range | MTM DD range | best/worst trade range | positive scenarios |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `15m` | `BTC` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -3691.63 to -1482.66 | -156.84 to -156.81 | 883.70 to 2209.70 | 441.94 to 1325.56 | 221 to 221 | 0.1855 to 0.2398 | 0.4126 to 0.6732 | 1691.43 to 3745.65 | 1724.54 to 3753.52 | -100.05 to -90.11 / 325.60 to 335.83 | 0/4 |
| `15m` | `BTC` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -3689.97 to -1481.01 | -155.19 to -155.16 | 883.70 to 2209.70 | 441.94 to 1325.56 | 221 to 221 | 0.1855 to 0.2398 | 0.4127 to 0.6734 | 1688.72 to 3742.99 | 1721.97 to 3750.99 | -100.18 to -90.25 / 325.59 to 335.83 | 0/4 |
| `15m` | `BTC` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -3562.96 to -1443.97 | -172.15 to -172.11 | 847.71 to 2119.70 | 423.94 to 1271.57 | 212 to 212 | 0.2406 to 0.2972 | 0.4062 to 0.6750 | 1443.97 to 3562.96 | 1599.33 to 3617.09 | -173.56 to -163.68 / 420.75 to 431.05 | 0/4 |
| `15m` | `ETH` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -3709.35 to -1610.48 | -350.71 to -350.64 | 839.68 to 2099.61 | 419.92 to 1259.52 | 210 to 210 | 0.1714 to 0.2143 | 0.4890 to 0.7113 | 1897.60 to 3956.27 | 1967.87 to 4006.50 | -130.82 to -120.91 / 374.89 to 385.16 | 0/4 |
| `15m` | `ETH` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -3710.69 to -1611.82 | -352.05 to -351.98 | 839.68 to 2099.61 | 419.92 to 1259.52 | 210 to 210 | 0.1810 to 0.2143 | 0.4889 to 0.7113 | 1900.42 to 3959.09 | 1969.81 to 4009.33 | -133.40 to -123.48 / 375.86 to 386.13 | 0/4 |
| `15m` | `ETH` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -3233.02 to -1183.85 | 46.03 to 46.04 | 819.76 to 2049.82 | 409.96 to 1229.64 | 205 to 205 | 0.2293 to 0.3415 | 0.5250 to 0.7785 | 1830.44 to 3789.15 | 1892.14 to 3853.76 | -241.09 to -231.25 / 574.51 to 584.92 | 0/4 |
| `15m` | `SOL` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -4327.01 to -2188.54 | -904.94 to -904.76 | 855.56 to 2139.33 | 427.87 to 1283.34 | 214 to 214 | 0.1682 to 0.2430 | 0.4012 to 0.6036 | 2249.98 to 4332.53 | 2325.91 to 4374.42 | -168.14 to -158.25 / 321.83 to 332.06 | 0/4 |
| `15m` | `SOL` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -4319.21 to -2180.74 | -897.13 to -896.95 | 855.56 to 2139.34 | 427.87 to 1283.35 | 214 to 214 | 0.1682 to 0.2523 | 0.4009 to 0.6043 | 2242.44 to 4325.56 | 2324.97 to 4373.48 | -167.28 to -157.39 / 322.43 to 332.66 | 0/4 |
| `15m` | `SOL` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -3772.51 to -1693.70 | -445.96 to -445.87 | 831.66 to 2079.57 | 415.91 to 1247.49 | 208 to 208 | 0.2548 to 0.2981 | 0.4522 to 0.6848 | 2247.78 to 4239.89 | 2367.49 to 4355.72 | -162.61 to -152.71 / 350.76 to 361.01 | 0/4 |
| `1h` | `BTC` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -205.17 to 1145.63 | 1955.75 to 1956.14 | 540.23 to 1350.84 | 270.17 to 810.34 | 135 to 135 | 0.2667 to 0.2963 | 0.9655 to 1.2301 | 1420.75 to 1889.75 | 1547.92 to 1950.85 | -314.46 to -304.67 / 693.82 to 704.31 | 3/4 |
| `1h` | `BTC` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -203.03 to 1147.77 | 1957.89 to 1958.28 | 540.23 to 1350.84 | 270.17 to 810.34 | 135 to 135 | 0.2667 to 0.2963 | 0.9659 to 1.2306 | 1420.94 to 1889.95 | 1548.82 to 1950.89 | -314.57 to -304.78 / 693.82 to 704.31 | 3/4 |
| `1h` | `BTC` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -1756.10 to -436.41 | 355.55 to 355.62 | 527.91 to 1320.05 | 264.01 to 791.87 | 132 to 132 | 0.2955 to 0.3182 | 0.7216 to 0.9190 | 1495.63 to 2034.58 | 1574.25 to 2133.27 | -302.15 to -292.35 / 524.34 to 534.71 | 0/4 |
| `sleeve_1h` | `ETH` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | 1526.59 to 2698.47 | 3400.74 to 3401.42 | 468.54 to 1171.58 | 234.32 to 702.81 | 117 to 117 | 0.3504 to 0.3761 | 1.2398 to 1.4806 | 1423.97 to 1782.89 | 1556.32 to 1870.44 | -357.47 to -347.72 / 836.68 to 847.27 | 4/4 |
| `sleeve_1h` | `ETH` | `next_candle_open` | `2/1,2/3,5/1,5/3` | 1509.74 to 2681.62 | 3383.89 to 3384.56 | 468.54 to 1171.58 | 234.32 to 702.80 | 117 to 117 | 0.3504 to 0.3675 | 1.2367 to 1.4766 | 1432.87 to 1791.86 | 1557.80 to 1872.82 | -357.47 to -347.72 / 835.01 to 845.60 | 4/4 |
| `sleeve_1h` | `ETH` | `next_candle_close` | `2/1,2/3,5/1,5/3` | 1892.34 to 3044.47 | 3734.78 to 3735.53 | 460.61 to 1151.75 | 230.35 to 690.91 | 115 to 115 | 0.3913 to 0.4609 | 1.3577 to 1.6587 | 1260.54 to 1499.65 | 1345.10 to 1589.20 | -355.53 to -345.77 / 694.40 to 704.90 | 4/4 |
| `1h` | `SOL` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -579.53 to 670.94 | 1421.01 to 1421.29 | 500.13 to 1250.59 | 250.12 to 750.20 | 125 to 125 | 0.3040 to 0.3680 | 0.9174 to 1.1082 | 1915.97 to 2294.63 | 1992.70 to 2359.06 | -369.75 to -360.00 / 597.67 to 608.09 | 2/4 |
| `1h` | `SOL` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -588.09 to 662.37 | 1412.44 to 1412.72 | 500.13 to 1250.58 | 250.12 to 750.20 | 125 to 125 | 0.3120 to 0.3680 | 0.9163 to 1.1066 | 1920.94 to 2299.60 | 2002.41 to 2364.78 | -369.77 to -360.03 / 598.12 to 608.55 | 2/4 |
| `1h` | `SOL` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -1192.99 to 7.01 | 727.01 to 727.16 | 480.00 to 1200.24 | 240.05 to 720.00 | 120 to 120 | 0.3417 to 0.3917 | 0.8358 to 1.0011 | 1250.43 to 1579.58 | 1377.55 to 1786.81 | -365.20 to -355.45 / 604.03 to 614.46 | 1/4 |
| `4h` | `BTC` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -1511.00 to -1121.78 | -888.07 to -887.89 | 155.78 to 389.52 | 77.90 to 233.66 | 39 to 39 | 0.3077 to 0.3077 | 0.5318 to 0.6209 | 1639.10 to 1977.95 | 1800.16 to 2149.19 | -308.81 to -299.02 / 403.23 to 413.52 | 0/4 |
| `4h` | `BTC` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -1512.06 to -1122.85 | -889.14 to -888.96 | 155.78 to 389.52 | 77.90 to 233.66 | 39 to 39 | 0.3077 to 0.3077 | 0.5317 to 0.6208 | 1640.72 to 1979.57 | 1801.68 to 2150.70 | -308.25 to -298.46 / 403.45 to 413.74 | 0/4 |
| `4h` | `BTC` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -507.96 to -158.07 | 51.92 to 51.93 | 139.97 to 349.99 | 70.00 to 209.95 | 35 to 35 | 0.4000 to 0.4000 | 0.7968 to 0.9310 | 1054.92 to 1268.92 | 1262.26 to 1506.07 | -325.36 to -315.58 / 395.28 to 405.56 | 0/4 |
| `4h` | `ETH` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -1969.85 to -1630.99 | -1427.44 to -1427.16 | 135.67 to 339.25 | 67.85 to 203.51 | 34 to 34 | 0.2353 to 0.2353 | 0.4807 to 0.5387 | 2260.93 to 2559.35 | 2559.85 to 2858.48 | -464.93 to -455.25 / 780.45 to 791.00 | 0/4 |
| `4h` | `ETH` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -1969.70 to -1630.85 | -1427.29 to -1427.01 | 135.67 to 339.25 | 67.85 to 203.51 | 34 to 34 | 0.2353 to 0.2353 | 0.4806 to 0.5386 | 2263.64 to 2562.05 | 2561.80 to 2860.44 | -465.91 to -456.23 / 780.41 to 790.96 | 0/4 |
| `4h` | `ETH` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -3189.72 to -2861.72 | -2664.54 to -2664.01 | 131.43 to 328.63 | 65.73 to 197.14 | 33 to 33 | 0.2727 to 0.3030 | 0.3592 to 0.3976 | 3598.64 to 3876.13 | 3774.67 to 4062.42 | -525.52 to -515.88 / 608.08 to 618.51 | 0/4 |
| `4h` | `SOL` | `same_candle_close_research_only` | `2/1,2/3,5/1,5/3` | -3799.40 to -3441.81 | -3226.80 to -3226.15 | 143.31 to 358.35 | 71.67 to 214.97 | 36 to 36 | 0.2500 to 0.2500 | 0.2361 to 0.2688 | 3762.95 to 4070.31 | 4226.69 to 4524.13 | -519.00 to -509.36 / 259.85 to 270.04 | 0/4 |
| `4h` | `SOL` | `next_candle_open` | `2/1,2/3,5/1,5/3` | -3823.40 to -3465.83 | -3250.82 to -3250.17 | 143.31 to 358.34 | 71.67 to 214.96 | 36 to 36 | 0.2500 to 0.2500 | 0.2338 to 0.2662 | 3780.77 to 4088.12 | 4247.45 to 4544.87 | -523.23 to -513.59 / 257.81 to 268.00 | 0/4 |
| `4h` | `SOL` | `next_candle_close` | `2/1,2/3,5/1,5/3` | -3405.90 to -3068.05 | -2864.93 to -2864.35 | 135.39 to 338.53 | 67.71 to 203.08 | 34 to 34 | 0.2941 to 0.2941 | 0.3842 to 0.4206 | 3229.35 to 3460.31 | 3514.66 to 3671.44 | -613.78 to -604.21 / 690.55 to 701.04 | 0/4 |

## Robustness Summary

| question | observed answer |
| --- | --- |
| Positive under all tested fill timings and cost assumptions | `sleeve_1h` ETH only |
| Positive under `next_candle_open` across all tested cost assumptions | `sleeve_1h` ETH only |
| Positive under `next_candle_close` across all tested cost assumptions | `sleeve_1h` ETH only |
| Positive under highest tested cost assumptions (`5` fee bps, `3` slippage bps) | `sleeve_1h` ETH remained positive across all fill timings; BTC and SOL did not |
| Negative under all tested assumptions | all `sleeve_15m` symbol scenarios and all `sleeve_4h` symbol scenarios |
| Fill timing sensitivity | BTC and SOL `sleeve_1h` weakened materially under `next_candle_close`; ETH `sleeve_1h` did not |
| Fee/slippage sensitivity | All components weakened under higher costs; `sleeve_1h` aggregate dropped from 11,621.89 at `2/1` costs to 403.75 at `5/3` costs |
| Weak profit factor | `sleeve_15m` and `sleeve_4h` are consistently below 1.0; BTC/SOL `sleeve_1h` include below-1.0 high-cost or next-close cases |
| Drawdown versus net PnL concern | Drawdowns are large relative to several positive `sleeve_1h` scenarios and dominate negative 15m/4h scenarios |

## ETH Concentration Analysis

ETH `sleeve_1h` is the only component/symbol pair with positive net PnL across all tested fill timings and cost assumptions.

| fill timing | fee/slippage | net PnL | gross PnL | fees | slippage cost | trades | win rate | profit factor | closed DD | MTM DD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_candle_close_research_only` | `2/1` | 2,698.47 | 3,401.42 | 468.63 | 234.32 | 117 | 0.3761 | 1.4806 | 1,423.97 | 1,556.32 |
| `same_candle_close_research_only` | `2/3` | 2,229.40 | 3,400.74 | 468.54 | 702.81 | 117 | 0.3504 | 1.3771 | 1,567.32 | 1,679.74 |
| `same_candle_close_research_only` | `5/1` | 1,995.52 | 3,401.42 | 1,171.58 | 234.32 | 117 | 0.3504 | 1.3290 | 1,639.51 | 1,741.95 |
| `same_candle_close_research_only` | `5/3` | 1,526.59 | 3,400.74 | 1,171.35 | 702.81 | 117 | 0.3504 | 1.2398 | 1,782.89 | 1,870.44 |
| `next_candle_open` | `2/1` | 2,681.62 | 3,384.56 | 468.63 | 234.32 | 117 | 0.3675 | 1.4766 | 1,432.87 | 1,557.80 |
| `next_candle_open` | `2/3` | 2,212.55 | 3,383.89 | 468.54 | 702.80 | 117 | 0.3504 | 1.3735 | 1,576.29 | 1,681.22 |
| `next_candle_open` | `5/1` | 1,978.67 | 3,384.56 | 1,171.58 | 234.32 | 117 | 0.3504 | 1.3257 | 1,648.48 | 1,743.43 |
| `next_candle_open` | `5/3` | 1,509.74 | 3,383.89 | 1,171.34 | 702.80 | 117 | 0.3504 | 1.2367 | 1,791.86 | 1,872.82 |
| `next_candle_close` | `2/1` | 3,044.47 | 3,735.53 | 460.70 | 230.35 | 115 | 0.4609 | 1.6587 | 1,260.54 | 1,345.10 |
| `next_candle_close` | `2/3` | 2,583.26 | 3,734.78 | 460.61 | 690.91 | 115 | 0.4174 | 1.5296 | 1,356.03 | 1,442.58 |
| `next_candle_close` | `5/1` | 2,353.42 | 3,735.53 | 1,151.75 | 230.35 | 115 | 0.4087 | 1.4695 | 1,404.19 | 1,491.75 |
| `next_candle_close` | `5/3` | 1,892.34 | 3,734.78 | 1,151.52 | 690.91 | 115 | 0.3913 | 1.3577 | 1,499.65 | 1,589.20 |

BTC and SOL comparison:

- BTC `sleeve_1h` had 6 positive scenarios out of 12, but every `next_candle_close` scenario was negative.
- SOL `sleeve_1h` had 5 positive scenarios out of 12, and only one `next_candle_close` scenario was barely positive at `7.01` net PnL.
- ETH contributed `26,706.06` summed net PnL across research runs while BTC summed to `-615.10` and SOL summed to `-2,041.03`.

Founder review question: is the 1h result broad Money Flow behavior, or mostly an ETH-specific pocket during this public-candle window?

## Regime Dependence

Regime labels are descriptive diagnostics assigned from entry-candle conditions. They are not filters and were not used to change strategy behavior.

| component | regime observation |
| --- | --- |
| `sleeve_15m` | Sideways trend entries dominated trade count and summed to `-91,641.74`; uptrend entries also summed negative at `-6,146.82`. Low-volatility entries summed to `-99,524.95`. |
| `sleeve_1h` | Uptrend entries summed positive at `33,956.02`; sideways entries summed negative at `-9,212.31`; downtrend entries were limited and summed `-693.79`. Normal-volatility entries summed positive at `32,937.55`, while high- and low-volatility entries summed negative. |
| `sleeve_4h` | Uptrend entries summed strongly negative at `-66,558.99`; sideways entries summed `-13,634.42`; downtrend entries were limited and slightly negative at `-188.82`. |

Interpretation: the 1h positive evidence is regime-dependent and appears driven by uptrend/normal-volatility contribution. The 15m and 4h components did not show positive grouped regime evidence in this campaign.

## Drawdown Interpretation

Largest observed drawdowns:

- Largest mark-to-market drawdown: `4,544.87` in SOL `sleeve_4h`, `next_candle_open`, `5/3` costs, with net PnL `-3,823.40`.
- Largest closed-trade drawdown: `4,332.53` in SOL `sleeve_15m`, same-candle-close, `5/3` costs, with net PnL `-4,327.01`.
- ETH `sleeve_1h` positive scenarios still had mark-to-market drawdowns from `1,345.10` to `1,872.82`.
- BTC `sleeve_1h` positive same/open scenarios had mark-to-market drawdowns around `1,547.92` to `1,950.89`, while next-close scenarios were negative.

Founder review should assess whether the ETH 1h drawdown profile is acceptable relative to observed net PnL and trade count. This report does not decide that automatically.

## Cost Sensitivity

| component | low-cost `2/1` summed net PnL | high-cost `5/3` summed net PnL | positive high-cost scenarios |
| --- | ---: | ---: | ---: |
| `sleeve_15m` | -14,876.77 | -34,016.36 | 0/9 |
| `sleeve_1h` | 11,621.89 | 403.75 | 3/9 |
| `sleeve_4h` | -18,501.94 | -21,688.99 | 0/9 |

Interpretation: higher fee/slippage assumptions materially reduce all components. ETH `sleeve_1h` remains positive under the highest tested cost pair, but the grouped 1h sum is much thinner after cost stress because BTC and SOL do not survive high-cost assumptions.

## Fill Timing Interpretation

| component/symbol | same-candle-close | next-candle-open | next-candle-close |
| --- | ---: | ---: | ---: |
| BTC `sleeve_1h` | 3/4 positive | 3/4 positive | 0/4 positive |
| ETH `sleeve_1h` | 4/4 positive | 4/4 positive | 4/4 positive |
| SOL `sleeve_1h` | 2/4 positive | 2/4 positive | 1/4 positive |
| all `sleeve_15m` rows | 0/12 positive | 0/12 positive | 0/12 positive |
| all `sleeve_4h` rows | 0/12 positive | 0/12 positive | 0/12 positive |

Interpretation: ETH `sleeve_1h` did not rely on same-candle close. BTC and SOL `sleeve_1h` are materially weaker under next-candle-close fills.

## No-Trade And Invalid Reason Summary

| component | bearish alignment | MACD not constructive | RSI not constructive | overextended RSI | entry quality not constructive | insufficient history invalids |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sleeve_15m` | 97,976 | 11,396 | 10,076 | 2,976 | 524 | 1,224 |
| `sleeve_1h` | 61,372 | 5,300 | 3,696 | 1,148 | 456 | 1,224 |
| `sleeve_4h` | 14,884 | 892 | 648 | 0 | 368 | 1,404 |

These reason counts are summed across research scenarios and should be interpreted as descriptive diagnostics, not one live decision stream.

## Limitations

- This is Hyperliquid USDC perpetual public-candle research only.
- The public campaign has one recent `15m` window and one YTD `1h`/`4h` window; it is not out-of-sample validation.
- Grouped sums aggregate separate research scenarios and are not account-level PnL.
- Trade sizing is constant initial-capital notional per opened trade; realized equity does not change next-trade size.
- Same-candle-close rows remain research-only and potentially optimistic.
- Fees and slippage are configured assumptions, not venue-account realized cost truth.
- Simulated trades are validation artifacts, not `SubmittedOrder` records.
- Cross-venue comparison remains deferred because product type, quote asset, settlement asset, trade-count availability, and data-source quality differ by venue.

## Manual Founder Review Checklist

- Review ETH `sleeve_1h` scenario rows first, especially next-candle-open and next-candle-close under `5/3` costs.
- Decide whether BTC/SOL mixed 1h behavior supports or weakens the Money Flow hypothesis.
- Treat 15m and 4h as negative evidence for this public campaign unless a later scoped investigation explains otherwise.
- Review drawdown versus net PnL before any paper-trading design is scoped.
- Account-style sizing remains deferred; dynamic-equity evidence should be a separate later phase if founder review needs it.
- Review regime dependence, especially whether uptrend/normal-volatility dependence is acceptable.
- Require out-of-sample and longer-window validation before rule changes or paper-trading scope.
- Keep paper-trading design deferred unless the founder manually accepts a bounded experiment in a later phase.

## Paper-Readiness Status

Status: `ready_for_founder_review`.

This means the evidence is organized enough for founder review. It does not mean paper trading is authorized, does not mean live trading is authorized, and does not connect Strategy Validation output to routing or execution automation.

Paper-trading design remains deferred until the founder manually accepts the risk and scope in a later explicitly scoped phase.
