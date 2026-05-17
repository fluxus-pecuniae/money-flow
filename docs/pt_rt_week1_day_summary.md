# PT-RT Week 1 Daily Summary

## Executive Summary

PT-RT1.4.1 verifies the active Week 1 runtime cutover and creates the first daily founder review pack. This is 24h / daily observation only, not evidence of edge, not production approval, and synthetic paper only.

- Generated at UTC: `2026-05-17T11:51:26Z`
- Cutover timestamp: `2026-05-17T09:47:55Z`
- Active timeframes: `1h, 4h, 1d`
- 15m status: `disabled_for_week1_noise_reduction`; legacy rows are visible but excluded from active scoring.
- Retired pre-cutover runtime 15m opens after cutover: `79`
- Restarted active runtime 15m opens: `0`
- Restarted active runtime 15m rows: `0`
- Cutover verification: `active_runtime_cutover_verified_after_restart`
- Go/no-go: `Week 1 paper observation may continue`

The retired runtime is labeled `pre_pt_rt1_4_weekend_burn_in` and must not be used for active Week 1 scoring because it continued producing 15m entries after the PT-RT1.4 cutover. A fresh active-week runtime was restarted in `reports/paper_runtime/pt_rt1_4_1_active_week/`; its first artifact cycle contains no 15m rows.

## Runtime Health

- Public mainnet connection: `connected`
- Last update UTC: `2026-05-17T11:46:43Z`
- Endpoint category: `public_read_only`
- No API keys: `True`
- No private/signed/order endpoints from strategy truth: `True`
- Market rows checked: `66`
- Market rows unavailable: `0`
- Lane-expanded data unavailable decisions: `0`

## Daily Observation

- Top lane by total synthetic equity: `wildcard_btc_regime_guard` at `10,000.00`
- Worst lane by total synthetic equity: `money_flow_v1_2_baseline` at `9,885.63`
- Open positions: `154` active, `82` legacy 15m
- Closed trades: `0`
- Data-health blocks: `0`
- Duplicate blocks: `0`

## Lane Review

| lane | realized | unrealized | total | net pnl | open | closed | win rate | drawdown | data blocks | duplicate blocks | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| money_flow_v1_2_baseline | 9,885.63 | 0.00 | 9,885.63 | -114.37 | 23 | 0 | no_closed_trades | 114.37 | 0 | 0 | active_timeframe_observed |
| avoid_low_rolling_range_20 | 9,935.19 | 0.00 | 9,935.19 | -64.81 | 13 | 0 | no_closed_trades | 64.81 | 0 | 0 | active_timeframe_observed |
| avoid_low_rolling_range_50 | 9,895.52 | 0.00 | 9,895.52 | -104.48 | 21 | 0 | no_closed_trades | 104.48 | 0 | 0 | active_timeframe_observed |
| mf_orig_stage_filter_only_full_equity | 9,885.63 | 0.00 | 9,885.63 | -114.37 | 23 | 0 | no_closed_trades | 114.37 | 0 | 0 | active_timeframe_observed |
| mf_orig_stage2_pullback_reclaim_full_equity | 9,885.63 | 0.00 | 9,885.63 | -114.37 | 23 | 0 | no_closed_trades | 114.37 | 0 | 0 | active_timeframe_observed |
| mf_orig_1d_stage2_5_20_crossover_full_equity | 9,885.63 | 0.00 | 9,885.63 | -114.37 | 23 | 0 | no_closed_trades | 114.37 | 0 | 0 | active_timeframe_observed |
| mf_orig_1d_stage2_breakout_resistance_full_equity | 9,885.63 | 0.00 | 9,885.63 | -114.37 | 23 | 0 | no_closed_trades | 114.37 | 0 | 0 | active_timeframe_observed |
| wildcard_btc_regime_guard | 10,000.00 | 0.00 | 10,000.00 | 0.00 | 0 | 0 | no_closed_trades | 0.00 | 0 | 0 | active_timeframe_observed |
| wildcard_multi_timeframe_alignment | 10,000.00 | 0.00 | 10,000.00 | 0.00 | 0 | 0 | no_closed_trades | 0.00 | 0 | 0 | active_timeframe_observed |
| wildcard_volatility_expansion_breakout | 9,975.02 | 0.00 | 9,975.02 | -24.98 | 5 | 0 | no_closed_trades | 24.98 | 0 | 0 | active_timeframe_observed |

## Timeframe Review

| timeframe | decisions | opens | closes | open positions | closed trades | net pnl | max drawdown | data blocks | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1h | 355 | 135 | 0 | 135 | 0 | 0 | 0 | 0 | active_week_timeframe |
| 4h | 225 | 5 | 0 | 5 | 0 | 0 | 0 | 0 | active_week_timeframe |
| 1d | 234 | 14 | 0 | 14 | 0 | 0 | 0 | 0 | active_week_timeframe |
| 15m | 24362 | 702 | 580 | 82 | legacy_not_active_score | legacy_not_active_score | legacy_not_active_score | 2360 | paused_legacy_not_active_score |

## Open Position Review

Active 1h/4h/1d positions are shown below. Legacy 15m positions remain visible in the JSON summary and are excluded from active scoring.

| lane | symbol | tf | entry time | age | entry | current | qty | notional | unrealized | unrealized % | entry reason | health | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| avoid_low_rolling_range_20 | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.223137 | 9,990.00 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| avoid_low_rolling_range_20 | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,402.417747 | 9,980.01 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| avoid_low_rolling_range_50 | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| avoid_low_rolling_range_50 | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| mf_orig_1d_stage2_5_20_crossover_full_equity | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_1d_stage2_5_20_crossover_full_equity | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_1d_stage2_breakout_resistance_full_equity | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_1d_stage2_breakout_resistance_full_equity | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_stage2_pullback_reclaim_full_equity | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_stage2_pullback_reclaim_full_equity | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_stage_filter_only_full_equity | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| mf_orig_stage_filter_only_full_equity | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |
| money_flow_v1_2_baseline | BNB | 1d | 2026-05-17T00:00:00Z | 11h 46m | 655.910000 | 655.910000 | 15.192713 | 9,970.04 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| money_flow_v1_2_baseline | SUI | 1d | 2026-05-17T00:00:00Z | 11h 46m | 1.060900 | 1.060900 | 9,383.627010 | 9,960.07 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed | not_reported | open |
| mf_orig_1d_stage2_5_20_crossover_full_equity | TRX | 4h | 2026-05-17T08:00:00Z | 3h 46m | 0.354280 | 0.354280 | 28,057.369102 | 9,945.14 | 0.00 | 0.0000 | public_mainnet_data_connected, closed_candle_ready, baseline_alignment_passed, mf_orig_stage2_context_observed | not_reported | open |

## Closed Trade Review

- Closed trade count: `0`
- Winning trades: `0`
- Losing trades: `0`
- Largest win: `no_closed_winner`
- Largest loss: `no_closed_loser`
- Total net PnL: `0`

| lane | symbol | tf | entry | exit | duration | entry px | exit px | qty | net pnl | net pnl % | equity after | exit reason | fees/slip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_closed_trades |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Signal / Decision Review

Signal rows are paper decisions, synthetic entries, synthetic closes, or skipped/no-trade decisions. They are not exchange orders.

| action | count |
| --- | --- |
| paper_opened | 154 |
| blocked_by_candidate_filter | 205 |
| no_trade | 301 |
| paper_hold | 154 |

Top reason codes:

| reason | count |
| --- | --- |
| public_mainnet_data_connected | 814 |
| closed_candle_ready | 814 |
| baseline_alignment_passed | 384 |
| baseline_alignment_failed | 380 |
| price_below_sma20 | 380 |
| macd_histogram_not_constructive | 330 |
| mf_orig_stage2_context_observed | 196 |
| mf_orig_stage2_context_not_confirmed | 160 |
| btc_regime_context_unavailable | 66 |
| higher_timeframe_context_unavailable | 66 |
| volatility_expansion_no_recent_high_breakout | 49 |
| blocked_low_rolling_range | 12 |

Top symbols by activity:

| symbol | count |
| --- | --- |
| SUI | 44 |
| TRX | 40 |
| DOGE | 38 |
| HYPE | 38 |
| AVAX | 38 |
| TON | 38 |
| UNI | 38 |
| BNB | 37 |
| ZEC | 37 |
| XMR | 37 |

## Testnet Label Audit

- Testnet order transport: `disabled`
- Audit-only shapes: `enabled`
- Signed testnet orders: `0`
- Strategy PnL update from testnet: `False`
- Live trading: `not approved`
- Transport status: `audit_only_not_submitted`

## Dashboard QA

Paper Trading tab order verified in code/static tests:

| order | panel |
| --- | --- |
| 1 | Top health banner |
| 2 | Weekly scoreboard |
| 3 | Live chart + watchlist |
| 4 | Open positions |
| 5 | Closed trades |
| 6 | Signal / decision stream |
| 7 | Data health + testnet plumbing |

Other tabs remain reference-only: Historical Replay is historical visual reference, Evidence is canonical backtest summaries, The Lab is research variants, Audit is audit findings, and Strategy is rules/source notes.

## Boundaries

- Synthetic paper only.
- No strategy is production-approved.
- No live trading is approved.
- No live orders were submitted.
- No testnet orders were submitted.
- Testnet order transport is disabled.
- No private/signed/order endpoints were called from strategy truth.
- Hyperliquid testnet prices/fills are not strategy PnL truth.
- Historical evidence packs were not regenerated.
- Production Money Flow rules are unchanged.

## Decision

`Week 1 paper observation may continue`

The retired pre-PT-RT1.4 runtime produced 15m opens after cutover and is excluded from active scoring; the restarted active runtime has zero 15m rows.
