# SV1.17 True Replay Experiment Round 1

Recorded at: `2026-05-08T06:50:11Z`

Status: `true_replay_round_1_ready_for_founder_review`

This report is research-only. It uses the SV1.16/SV1.16.1 true replay substrate to test a small set of lower-RSI and market-structure variants for Hyperliquid ETH `sleeve_1h` under `dynamic_equity_pct` sizing. Production Money Flow rules did not change, no parameters were globally optimized, no evidence packs were generated, paper/live trading is not approved, and no exchange or routing artifacts were created.

## Methodology

- Scope: Hyperliquid USDC perpetual public-candle research, primary ETH `sleeve_1h` scenario.
- Each variant is a true forward replay over evaluated candles, not a completed-trade overlay.
- Each scenario keeps position occupancy and dynamic-equity sizing on its own replay path.
- SV1.16.1 semantics apply: production-rule context is evaluated in the current replay state after divergence, and variant-admitted candles are counted separately from variant no-trade.
- These are round-one research variants. They are not production rules, not recommendations, and not paper/live authorization.

## Baseline Comparison

| Component | Variant | Trades | Ending Equity | Net Account PnL | Delta Vs Baseline | MTM Drawdown | Win Rate | Profit Factor | Variant Entries | Candidates | Near Support Entries | Near Resistance Entries | Falling-Knife Candidate Proxy | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sleeve_1h | `lower_rsi_floor_trend_intact_v1` | 137 | $10,902.09 | $902.09 | $-486.84 | $1,777.46 | 30.66% | 1.13 | 29 | 1428 | 4 | 11 | 1392 | `observed_deteriorated_vs_baseline` |
| sleeve_1h | `lower_rsi_floor_trend_intact_v2_narrow` | 129 | $10,792.72 | $792.72 | $-596.21 | $1,829.09 | 31.78% | 1.12 | 18 | 1445 | 4 | 9 | 1399 | `observed_deteriorated_vs_baseline` |
| sleeve_1h | `lower_rsi_support_confirmed_v1` | 117 | $11,388.93 | $1,388.93 | $0.00 | $1,753.27 | 35.04% | 1.22 | 0 | 1472 | 0 | 0 | 1408 | `observed_unchanged_vs_baseline` |
| sleeve_1h | `lower_rsi_ema10_hold_no_resistance_v1` | 126 | $11,293.73 | $1,293.73 | $-95.20 | $1,537.82 | 32.54% | 1.19 | 14 | 1444 | 0 | 0 | 1401 | `observed_deteriorated_vs_baseline` |

## Baseline Anchor

| Component | Baseline Variant | Trades | Ending Equity | Net Account PnL | MTM Drawdown | Win Rate | Profit Factor |
|---|---|---:|---:|---:|---:|---:|---:|
| sleeve_1h | `baseline_current_money_flow_rules` | 117 | $11,388.93 | $1,388.93 | $1,753.27 | 35.04% | 1.22 |

## Variant Counter Truth

| Variant | Production-Rule Rejections | Admitted From Rejection | Variant No-Trade Reasons | Rejected Variant Candidates | Admitted Regimes |
|---|---|---|---|---|---|
| `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=88 | `rsi_not_constructive`=29 | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=59 | `variant_candidate_rejected`=1399 | `sideways`=24, `uptrend`=5 |
| `lower_rsi_floor_trend_intact_v2_narrow` | `bearish_alignment`=1695, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=100 | `rsi_not_constructive`=18 | `bearish_alignment`=1695, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=82 | `variant_candidate_rejected`=1427 | `sideways`=14, `uptrend`=4 |
| `lower_rsi_support_confirmed_v1` | `bearish_alignment`=1702, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=120 | `none` | `bearish_alignment`=1702, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=120 | `variant_candidate_rejected`=1472 | `none` |
| `lower_rsi_ema10_hold_no_resistance_v1` | `bearish_alignment`=1697, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=97 | `rsi_not_constructive`=14 | `bearish_alignment`=1697, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=83 | `variant_candidate_rejected`=1430 | `sideways`=10, `uptrend`=4 |

## Interpretation

- A variant only deserves broader validation if it improves ending equity versus baseline without simply adding many weak below-floor trades or increasing drawdown.
- `near support` and `near resistance` use the SV1.16 prior-20-candle swing context. These are research diagnostics, not production filters.
- `falling-knife candidate proxy` counts below-floor candidate candles where trend stack, MACD, or SMA20 context is not constructive. This proxy is descriptive and is not used as a trade rule.
- If a variant improves this sampled ETH `sleeve_1h` scenario, it still needs broader symbols, fill/cost assumptions, out-of-sample windows, and exact risk/stop replay before any founder paper-design discussion.

## Boundary Flags

- `changes_production_money_flow_rules`: `False`
- `optimizes_parameters`: `False`
- `approves_paper_trading`: `False`
- `creates_live_artifacts`: `False`
- `creates_routing_artifacts`: `False`
- `calls_exchange_adapters`: `False`
- `research_only`: `True`

## Deferred Work

- Broader BTC/ETH/SOL and 15m/1h/4h replay validation.
- Multiple fill timing and fee/slippage sensitivity for any variant that survives ETH `sleeve_1h` round one.
- Exact recent-low or ATR stop replay with real exit timing and fill assumptions.
- Paper-trading design remains deferred until founder review explicitly scopes it later.
