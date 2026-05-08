# SV1.17 True Replay Experiment Round 1

Recorded at: `2026-05-08T07:55:11Z`

Status: `true_replay_round_1_ready_for_founder_review`

This report is research-only. It uses the SV1.16/SV1.16.1 true replay substrate to test a small set of lower-RSI and market-structure variants for the Hyperliquid USDC perpetual full BTC/ETH/SOL x 15m/1h/4h public campaign suite under `dynamic_equity_pct` sizing. Production Money Flow rules did not change, no parameters were globally optimized, no evidence packs were generated, paper/live trading is not approved, and no exchange or routing artifacts were created.

## Methodology

- Scope: Hyperliquid USDC perpetual public-candle research, full BTC/ETH/SOL x 15m/1h/4h public campaign suite.
- Symbols: `BTC, ETH, SOL`.
- Components: `sleeve_15m, sleeve_1h, sleeve_4h`.
- Each variant is a true forward replay over evaluated candles, not a completed-trade overlay.
- Each scenario keeps position occupancy and dynamic-equity sizing on its own replay path.
- SV1.16.1 semantics apply: production-rule context is evaluated in the current replay state after divergence, and variant-admitted candles are counted separately from variant no-trade.
- These are round-one research variants. They are not production rules, not recommendations, and not paper/live authorization.

## Baseline Comparison

| Symbol | Component | Variant | Trades | Ending Equity | Net Account PnL | Delta Vs Baseline | MTM Drawdown | Win Rate | Profit Factor | Variant Entries | Candidates | Near Support Entries | Near Resistance Entries | Falling-Knife Candidate Proxy | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BTC | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | 268 | $6,305.93 | $-3,694.07 | $-585.14 | $3,732.18 | 17.16% | 0.39 | 78 | 2438 | 61 | 73 | 2328 | `observed_deteriorated_vs_baseline` |
| BTC | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | 240 | $6,707.45 | $-3,292.55 | $-183.63 | $3,333.10 | 19.17% | 0.41 | 43 | 2480 | 30 | 41 | 2347 | `observed_deteriorated_vs_baseline` |
| BTC | sleeve_15m | `lower_rsi_support_confirmed_v1` | 223 | $6,880.67 | $-3,119.33 | $-10.41 | $3,160.92 | 18.39% | 0.42 | 3 | 2519 | 3 | 0 | 2359 | `observed_deteriorated_vs_baseline` |
| BTC | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | 223 | $6,850.81 | $-3,149.19 | $-40.27 | $3,190.60 | 18.39% | 0.41 | 3 | 2518 | 1 | 0 | 2360 | `observed_deteriorated_vs_baseline` |
| BTC | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | 142 | $9,872.93 | $-127.07 | $187.50 | $1,846.74 | 27.46% | 0.98 | 17 | 1396 | 2 | 8 | 1369 | `observed_improved_vs_baseline_needs_more_evidence` |
| BTC | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | 140 | $9,703.29 | $-296.71 | $17.86 | $1,921.02 | 27.14% | 0.95 | 13 | 1401 | 2 | 8 | 1371 | `observed_improved_vs_baseline_needs_more_evidence` |
| BTC | sleeve_1h | `lower_rsi_support_confirmed_v1` | 135 | $9,685.43 | $-314.57 | $0.00 | $1,857.05 | 26.67% | 0.94 | 0 | 1415 | 0 | 0 | 1374 | `observed_unchanged_vs_baseline` |
| BTC | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | 137 | $9,909.74 | $-90.26 | $224.31 | $1,726.15 | 27.74% | 0.98 | 6 | 1402 | 0 | 0 | 1373 | `observed_improved_vs_baseline_needs_more_evidence` |
| BTC | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | 39 | $8,889.22 | $-1,110.78 | $331.64 | $1,721.19 | 30.77% | 0.59 | 2 | 318 | 0 | 0 | 316 | `observed_improved_vs_baseline_needs_more_evidence` |
| BTC | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | 39 | $8,715.62 | $-1,284.38 | $158.04 | $1,891.74 | 30.77% | 0.56 | 1 | 320 | 0 | 0 | 316 | `observed_improved_vs_baseline_needs_more_evidence` |
| BTC | sleeve_4h | `lower_rsi_support_confirmed_v1` | 39 | $8,557.58 | $-1,442.42 | $0.00 | $2,047.00 | 30.77% | 0.52 | 0 | 320 | 0 | 0 | 316 | `observed_unchanged_vs_baseline` |
| BTC | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | 39 | $8,770.15 | $-1,229.85 | $212.58 | $1,838.17 | 30.77% | 0.57 | 1 | 318 | 0 | 0 | 316 | `observed_improved_vs_baseline_needs_more_evidence` |
| ETH | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | 261 | $6,453.52 | $-3,546.48 | $-407.54 | $3,823.10 | 16.48% | 0.50 | 80 | 2442 | 52 | 66 | 2338 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | 236 | $6,774.62 | $-3,225.38 | $-86.44 | $3,503.76 | 16.95% | 0.52 | 42 | 2498 | 28 | 37 | 2356 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_15m | `lower_rsi_support_confirmed_v1` | 211 | $6,840.74 | $-3,159.26 | $-20.32 | $3,438.00 | 18.01% | 0.48 | 1 | 2540 | 1 | 0 | 2376 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | 214 | $7,245.73 | $-2,754.27 | $384.67 | $3,035.23 | 18.69% | 0.57 | 7 | 2532 | 1 | 0 | 2375 | `observed_improved_vs_baseline_needs_more_evidence` |
| ETH | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | 137 | $10,902.09 | $902.09 | $-486.84 | $1,777.46 | 30.66% | 1.13 | 29 | 1428 | 4 | 11 | 1392 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | 129 | $10,792.72 | $792.72 | $-596.21 | $1,829.09 | 31.78% | 1.12 | 18 | 1445 | 4 | 9 | 1399 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_1h | `lower_rsi_support_confirmed_v1` | 117 | $11,388.93 | $1,388.93 | $0.00 | $1,753.27 | 35.04% | 1.22 | 0 | 1472 | 0 | 0 | 1408 | `observed_unchanged_vs_baseline` |
| ETH | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | 126 | $11,293.73 | $1,293.73 | $-95.20 | $1,537.82 | 32.54% | 1.19 | 14 | 1444 | 0 | 0 | 1401 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | 35 | $8,104.29 | $-1,895.71 | $-35.17 | $2,733.75 | 25.71% | 0.47 | 2 | 339 | 0 | 0 | 337 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | 35 | $8,104.29 | $-1,895.71 | $-35.17 | $2,733.75 | 25.71% | 0.47 | 2 | 339 | 0 | 0 | 337 | `observed_deteriorated_vs_baseline` |
| ETH | sleeve_4h | `lower_rsi_support_confirmed_v1` | 34 | $8,139.46 | $-1,860.54 | $0.00 | $2,699.41 | 23.53% | 0.48 | 0 | 340 | 0 | 0 | 338 | `observed_unchanged_vs_baseline` |
| ETH | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | 34 | $8,139.46 | $-1,860.54 | $0.00 | $2,699.41 | 23.53% | 0.48 | 0 | 340 | 0 | 0 | 338 | `observed_unchanged_vs_baseline` |
| SOL | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | 255 | $5,942.98 | $-4,057.02 | $-521.38 | $4,104.92 | 16.86% | 0.38 | 80 | 2589 | 53 | 67 | 2474 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | 234 | $6,275.25 | $-3,724.75 | $-189.11 | $3,773.61 | 16.67% | 0.39 | 48 | 2640 | 30 | 41 | 2490 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_15m | `lower_rsi_support_confirmed_v1` | 215 | $6,435.60 | $-3,564.40 | $-28.76 | $3,602.58 | 16.74% | 0.39 | 1 | 2676 | 1 | 0 | 2505 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | 217 | $6,376.67 | $-3,623.33 | $-87.69 | $3,661.34 | 17.05% | 0.39 | 8 | 2668 | 0 | 0 | 2503 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | 139 | $9,166.83 | $-833.17 | $-110.90 | $2,106.62 | 30.94% | 0.88 | 27 | 1486 | 3 | 9 | 1449 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | 136 | $9,196.95 | $-803.05 | $-80.78 | $2,078.78 | 31.62% | 0.88 | 23 | 1495 | 3 | 8 | 1450 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_1h | `lower_rsi_support_confirmed_v1` | 126 | $9,249.97 | $-750.03 | $-27.76 | $2,232.40 | 30.95% | 0.89 | 1 | 1516 | 1 | 0 | 1456 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | 132 | $9,124.24 | $-875.76 | $-153.49 | $2,152.32 | 30.30% | 0.87 | 12 | 1501 | 0 | 0 | 1453 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | 42 | $6,250.24 | $-3,749.76 | $-522.11 | $4,121.22 | 23.81% | 0.21 | 7 | 330 | 0 | 0 | 322 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | 41 | $6,248.43 | $-3,751.57 | $-523.91 | $4,123.02 | 21.95% | 0.21 | 6 | 335 | 0 | 0 | 322 | `observed_deteriorated_vs_baseline` |
| SOL | sleeve_4h | `lower_rsi_support_confirmed_v1` | 36 | $6,772.35 | $-3,227.65 | $0.00 | $3,953.10 | 25.00% | 0.24 | 0 | 341 | 0 | 0 | 325 | `observed_unchanged_vs_baseline` |
| SOL | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | 41 | $6,351.24 | $-3,648.76 | $-421.11 | $4,092.51 | 24.39% | 0.21 | 5 | 331 | 0 | 0 | 323 | `observed_deteriorated_vs_baseline` |

## Baseline Anchor

| Symbol | Component | Baseline Variant | Trades | Ending Equity | Net Account PnL | MTM Drawdown | Win Rate | Profit Factor |
|---|---|---|---:|---:|---:|---:|---:|---:|
| BTC | sleeve_15m | `baseline_current_money_flow_rules` | 221 | $6,891.08 | $-3,108.92 | $3,150.58 | 18.55% | 0.41 |
| BTC | sleeve_1h | `baseline_current_money_flow_rules` | 135 | $9,685.43 | $-314.57 | $1,857.05 | 26.67% | 0.94 |
| BTC | sleeve_4h | `baseline_current_money_flow_rules` | 39 | $8,557.58 | $-1,442.42 | $2,047.00 | 30.77% | 0.52 |
| ETH | sleeve_15m | `baseline_current_money_flow_rules` | 210 | $6,861.06 | $-3,138.94 | $3,417.79 | 18.10% | 0.48 |
| ETH | sleeve_1h | `baseline_current_money_flow_rules` | 117 | $11,388.93 | $1,388.93 | $1,753.27 | 35.04% | 1.22 |
| ETH | sleeve_4h | `baseline_current_money_flow_rules` | 34 | $8,139.46 | $-1,860.54 | $2,699.41 | 23.53% | 0.48 |
| SOL | sleeve_15m | `baseline_current_money_flow_rules` | 214 | $6,464.36 | $-3,535.64 | $3,573.90 | 16.82% | 0.39 |
| SOL | sleeve_1h | `baseline_current_money_flow_rules` | 125 | $9,277.73 | $-722.27 | $2,208.10 | 31.20% | 0.89 |
| SOL | sleeve_4h | `baseline_current_money_flow_rules` | 36 | $6,772.35 | $-3,227.65 | $3,953.10 | 25.00% | 0.24 |

## Variant Counter Truth

| Symbol | Component | Variant | Production-Rule Rejections | Admitted From Rejection | Variant No-Trade Reasons | Rejected Variant Candidates | Admitted Regimes |
|---|---|---|---|---|---|---|---|
| BTC | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=2682, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=212 | `rsi_not_constructive`=78 | `bearish_alignment`=2682, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=134 | `variant_candidate_rejected`=2360 | `sideways`=78 |
| BTC | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=2702, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=235 | `rsi_not_constructive`=43 | `bearish_alignment`=2702, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=192 | `variant_candidate_rejected`=2437 | `sideways`=43 |
| BTC | sleeve_15m | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=2712, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=264 | `rsi_not_constructive`=3 | `bearish_alignment`=2712, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=261 | `variant_candidate_rejected`=2516 | `sideways`=3 |
| BTC | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=2713, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=262 | `rsi_not_constructive`=3 | `bearish_alignment`=2713, `entry_quality_not_constructive`=11, `macd_not_constructive`=315, `overextended_rsi`=79, `rsi_not_constructive`=259 | `variant_candidate_rejected`=2515 | `sideways`=3 |
| BTC | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1685, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=70 | `rsi_not_constructive`=17 | `bearish_alignment`=1685, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=53 | `variant_candidate_rejected`=1379 | `sideways`=12, `uptrend`=5 |
| BTC | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=1687, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=73 | `rsi_not_constructive`=13 | `bearish_alignment`=1687, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=60 | `variant_candidate_rejected`=1388 | `sideways`=10, `uptrend`=3 |
| BTC | sleeve_1h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=1688, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=86 | `none` | `bearish_alignment`=1688, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=86 | `variant_candidate_rejected`=1415 | `none` |
| BTC | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=1688, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=73 | `rsi_not_constructive`=6 | `bearish_alignment`=1688, `entry_quality_not_constructive`=9, `macd_not_constructive`=153, `overextended_rsi`=29, `rsi_not_constructive`=67 | `variant_candidate_rejected`=1396 | `sideways`=2, `uptrend`=4 |
| BTC | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=8 | `rsi_not_constructive`=2 | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=6 | `variant_candidate_rejected`=316 | `sideways`=1, `uptrend`=1 |
| BTC | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=10 | `rsi_not_constructive`=1 | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=9 | `variant_candidate_rejected`=319 | `downtrend`=1 |
| BTC | sleeve_4h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=10 | `none` | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=10 | `variant_candidate_rejected`=320 | `none` |
| BTC | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=8 | `rsi_not_constructive`=1 | `bearish_alignment`=392, `entry_quality_not_constructive`=3, `macd_not_constructive`=34, `rsi_not_constructive`=7 | `variant_candidate_rejected`=317 | `uptrend`=1 |
| ETH | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=2673, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=238 | `rsi_not_constructive`=80 | `bearish_alignment`=2673, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=158 | `variant_candidate_rejected`=2362 | `sideways`=79, `uptrend`=1 |
| ETH | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=2686, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=281 | `rsi_not_constructive`=42 | `bearish_alignment`=2686, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=239 | `variant_candidate_rejected`=2456 | `sideways`=42 |
| ETH | sleeve_15m | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=2698, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=113, `rsi_not_constructive`=311 | `rsi_not_constructive`=1 | `bearish_alignment`=2698, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=113, `rsi_not_constructive`=310 | `variant_candidate_rejected`=2539 | `sideways`=1 |
| ETH | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=2697, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=304 | `rsi_not_constructive`=7 | `bearish_alignment`=2697, `entry_quality_not_constructive`=19, `macd_not_constructive`=350, `overextended_rsi`=112, `rsi_not_constructive`=297 | `variant_candidate_rejected`=2525 | `sideways`=6, `uptrend`=1 |
| ETH | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=88 | `rsi_not_constructive`=29 | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=59 | `variant_candidate_rejected`=1399 | `sideways`=24, `uptrend`=5 |
| ETH | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=1695, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=100 | `rsi_not_constructive`=18 | `bearish_alignment`=1695, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=82 | `variant_candidate_rejected`=1427 | `sideways`=14, `uptrend`=4 |
| ETH | sleeve_1h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=1702, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=120 | `none` | `bearish_alignment`=1702, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=120 | `variant_candidate_rejected`=1472 | `none` |
| ETH | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=1697, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=97 | `rsi_not_constructive`=14 | `bearish_alignment`=1697, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=83 | `variant_candidate_rejected`=1430 | `sideways`=10, `uptrend`=4 |
| ETH | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=417, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `rsi_not_constructive`=2 | `bearish_alignment`=417, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=20 | `variant_candidate_rejected`=337 | `sideways`=1, `uptrend`=1 |
| ETH | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=417, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `rsi_not_constructive`=2 | `bearish_alignment`=417, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=20 | `variant_candidate_rejected`=337 | `sideways`=1, `uptrend`=1 |
| ETH | sleeve_4h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=418, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `none` | `bearish_alignment`=418, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `variant_candidate_rejected`=340 | `none` |
| ETH | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=418, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `none` | `bearish_alignment`=418, `entry_quality_not_constructive`=12, `macd_not_constructive`=30, `rsi_not_constructive`=22 | `variant_candidate_rejected`=340 | `none` |
| SOL | sleeve_15m | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=2747, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=207 | `rsi_not_constructive`=80 | `bearish_alignment`=2747, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=127 | `variant_candidate_rejected`=2509 | `sideways`=77, `uptrend`=3 |
| SOL | sleeve_15m | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=2759, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=246 | `rsi_not_constructive`=48 | `bearish_alignment`=2759, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=198 | `variant_candidate_rejected`=2592 | `sideways`=46, `uptrend`=2 |
| SOL | sleeve_15m | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=2771, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=270 | `rsi_not_constructive`=1 | `bearish_alignment`=2771, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=269 | `variant_candidate_rejected`=2675 | `sideways`=1 |
| SOL | sleeve_15m | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=2770, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=263 | `rsi_not_constructive`=8 | `bearish_alignment`=2770, `entry_quality_not_constructive`=14, `macd_not_constructive`=293, `overextended_rsi`=56, `rsi_not_constructive`=255 | `variant_candidate_rejected`=2660 | `sideways`=6, `uptrend`=2 |
| SOL | sleeve_1h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1732, `entry_quality_not_constructive`=18, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=81 | `rsi_not_constructive`=27 | `bearish_alignment`=1732, `entry_quality_not_constructive`=18, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=54 | `variant_candidate_rejected`=1459 | `sideways`=23, `uptrend`=4 |
| SOL | sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=1733, `entry_quality_not_constructive`=18, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=89 | `rsi_not_constructive`=23 | `bearish_alignment`=1733, `entry_quality_not_constructive`=18, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=66 | `variant_candidate_rejected`=1472 | `sideways`=19, `uptrend`=4 |
| SOL | sleeve_1h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=1738, `entry_quality_not_constructive`=19, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=105 | `rsi_not_constructive`=1 | `bearish_alignment`=1738, `entry_quality_not_constructive`=19, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=104 | `variant_candidate_rejected`=1515 | `sideways`=1 |
| SOL | sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=1736, `entry_quality_not_constructive`=19, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=92 | `rsi_not_constructive`=12 | `bearish_alignment`=1736, `entry_quality_not_constructive`=19, `macd_not_constructive`=121, `overextended_rsi`=18, `rsi_not_constructive`=80 | `variant_candidate_rejected`=1489 | `sideways`=9, `uptrend`=3 |
| SOL | sleeve_4h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=430, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=14 | `rsi_not_constructive`=7 | `bearish_alignment`=430, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=7 | `variant_candidate_rejected`=323 | `sideways`=6, `uptrend`=1 |
| SOL | sleeve_4h | `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=430, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=19 | `rsi_not_constructive`=6 | `bearish_alignment`=430, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=13 | `variant_candidate_rejected`=329 | `sideways`=5, `uptrend`=1 |
| SOL | sleeve_4h | `lower_rsi_support_confirmed_v1` | `bearish_alignment`=433, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=22 | `none` | `bearish_alignment`=433, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=22 | `variant_candidate_rejected`=341 | `none` |
| SOL | sleeve_4h | `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=431, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=14 | `rsi_not_constructive`=5 | `bearish_alignment`=431, `entry_quality_not_constructive`=16, `macd_not_constructive`=11, `rsi_not_constructive`=9 | `variant_candidate_rejected`=326 | `sideways`=4, `uptrend`=1 |

## Interpretation

- A variant only deserves broader validation if it improves ending equity versus baseline without simply adding many weak below-floor trades or increasing drawdown.
- `near support` and `near resistance` use the SV1.16 prior-20-candle swing context. These are research diagnostics, not production filters.
- `falling-knife candidate proxy` counts below-floor candidate candles where trend stack, MACD, or SMA20 context is not constructive. This proxy is descriptive and is not used as a trade rule.
- If a variant improves any sampled scenario, it still needs fill/cost assumptions, out-of-sample windows, and exact risk/stop replay before any founder paper-design discussion.

## Boundary Flags

- `changes_production_money_flow_rules`: `False`
- `optimizes_parameters`: `False`
- `approves_paper_trading`: `False`
- `creates_live_artifacts`: `False`
- `creates_routing_artifacts`: `False`
- `calls_exchange_adapters`: `False`
- `research_only`: `True`

## Deferred Work

- Multiple fill timing and fee/slippage sensitivity for any variant that survives ETH `sleeve_1h` round one.
- Exact recent-low or ATR stop replay with real exit timing and fill assumptions.
- Paper-trading design remains deferred until founder review explicitly scopes it later.
