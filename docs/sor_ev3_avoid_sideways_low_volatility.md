# SOR-EV3 Avoid Sideways / Low-Volatility Drilldown

Recorded at: `2026-05-12T19:31:31Z`

Status: `avoid_sideways_low_volatility_true_forward_replay_ready_for_founder_review`

SOR-EV3 is evidence-only research for the founder-selected `avoid_sideways_low_volatility` candidate family. It uses canonical SV2.0.2 DB-imported evidence packs and true-forward replay. Production Money Flow rules are unchanged, no order endpoints are called, no private/signed endpoints are called, and no variant is approved for production.

## Executive Summary

- Baseline: `SV2.0.2 canonical DB-imported evidence packs` at `20260512T064916Z`.
- Baseline parity: `{'baseline_parity_passed': 72}`.
- Variants tested: `avoid_flat_ema10_slope, avoid_flat_sma20_slope, avoid_low_atr_percentile_20, avoid_low_atr_percentile_30, avoid_low_rolling_range_20, avoid_low_rolling_range_50, avoid_macd_flat_chop, avoid_sideways_low_volatility_conservative`.
- Candidate variants: `none`.
- Rejected variants: `avoid_flat_ema10_slope, avoid_flat_sma20_slope, avoid_low_atr_percentile_20, avoid_low_atr_percentile_30, avoid_low_rolling_range_20, avoid_low_rolling_range_50, avoid_macd_flat_chop, avoid_sideways_low_volatility_conservative`.
- Dashboard date filters remain display-only and are not canonical evidence.

## Founder-Selected Candidate

`avoid_sideways_low_volatility` targets entries during compressed, flat, or low-directional-progress conditions. This phase tests objective definitions only; it does not approve a rule.

## Baseline Reference

- Canonical pack paths inspected: `36`.
- Money Flow version: `money_flow_v1_2`.
- Symbols: `BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX`.
- Timeframes: `15m, 1h, 4h, 1d`.
- Capital mode: `dynamic_equity_pct` with `10000` USDC per independent scenario.

## Feature Definitions

| Feature | Definition |
|---|---|
| `atr_pct` | ATR14 divided by candle close. |
| `atr_percentile_lookback_50` | Current ATR percentage percentile over the prior/current 50 closed candles. |
| `atr_percentile_lookback_100` | Current ATR percentage percentile over the prior/current 100 closed candles. |
| `candle_range_pct` | Current high-low range divided by close. |
| `rolling_range_pct_20` | 20-candle high-low range divided by close. |
| `rolling_range_pct_50` | 50-candle high-low range divided by close. |
| `sma20_slope_pct` | SMA20 percentage change versus 10 closed candles earlier. |
| `ema10_slope_pct` | EMA10 percentage change versus 10 closed candles earlier. |
| `ema5_ema10_spread_pct` | EMA5 minus EMA10 divided by close. |
| `ema10_sma20_spread_pct` | EMA10 minus SMA20 divided by close. |
| `price_distance_from_sma20_pct` | Close minus SMA20 divided by SMA20. |
| `high_low_range_20_pct` | Alias of the 20-candle high-low compression range. |
| `close_range_position_20` | Close location inside the 20-candle high-low range, 0=low and 1=high. |
| `macd_histogram_abs_pct` | Absolute MACD histogram divided by close. |
| `macd_histogram_slope_pct` | MACD histogram change from prior candle divided by close. |
| `macd_signal_spread_abs_pct` | Absolute MACD-signal spread divided by close. |
| `many_crosses_ema10_sma20_lookback_20` | EMA10/SMA20 spread sign changes over the last 20 candles. |
| `price_whipsaw_count_lookback_20` | Close crossing EMA10 count over the last 20 candles. |
| `low_directional_progress_lookback_20` | 20-candle net close progress divided by 20-candle range is below 0.2. |

## Variant Comparison

| Variant | Outcome | Scenarios | Net PnL Delta | DD Delta Worst | Blocked Signals | Matched Trades | Avoided Losers | Missed Winners | Trade Reduction % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `avoid_flat_ema10_slope` | `deteriorated_vs_baseline` | 72 | 14679.99888902 | 387.95776834 | 8361 | 4228 | 3144 | 1084 | 15.02719646 |
| `avoid_flat_sma20_slope` | `deteriorated_vs_baseline` | 72 | 14414.66327302 | 2451.97220482 | 13606 | 3941 | 2936 | 1005 | 23.83147414 |
| `avoid_low_atr_percentile_20` | `deteriorated_vs_baseline` | 72 | 3352.75625247 | 1473.07030333 | 11164 | 3070 | 2278 | 792 | 21.14870471 |
| `avoid_low_atr_percentile_30` | `deteriorated_vs_baseline` | 72 | -12481.40606772 | 1234.04290198 | 15772 | 4054 | 2990 | 1064 | 29.87922928 |
| `avoid_low_rolling_range_20` | `overfit_risk` | 72 | 48845.55526731 | 119.72046323 | 19321 | 4570 | 3480 | 1090 | 37.23610215 |
| `avoid_low_rolling_range_50` | `higher_return_but_higher_drawdown` | 72 | 55197.69963174 | 410.24876203 | 23647 | 5107 | 3827 | 1280 | 45.14612335 |
| `avoid_macd_flat_chop` | `deteriorated_vs_baseline` | 72 | 580.18568893 | 29.98203801 | 98 | 81 | 72 | 9 | 0.44251867 |
| `avoid_sideways_low_volatility_conservative` | `deteriorated_vs_baseline` | 72 | 24268.20619967 | 2451.97220482 | 18640 | 5326 | 3975 | 1351 | 34.08315663 |

## Baseline Loss Concentration In Sideways / Low-Vol Regimes

| Variant Definition | Losing Trades Flagged % | Winning Trades Flagged % | Flagged Losing Trades | Flagged Winning Trades |
|---|---:|---:|---:|---:|
| `avoid_flat_ema10_slope` | 39.81762918 | 36.76719756 | 3144 | 1085 |
| `avoid_flat_sma20_slope` | 37.22137791 | 34.05625212 | 2939 | 1005 |
| `avoid_low_atr_percentile_20` | 28.85005066 | 26.90613351 | 2278 | 794 |
| `avoid_low_atr_percentile_30` | 37.90526849 | 36.05557438 | 2993 | 1064 |
| `avoid_low_rolling_range_20` | 44.16160081 | 37.00440529 | 3487 | 1092 |
| `avoid_low_rolling_range_50` | 48.46757852 | 43.37512708 | 3827 | 1280 |
| `avoid_macd_flat_chop` | 0.9118541 | 0.30498136 | 72 | 9 |
| `avoid_sideways_low_volatility_conservative` | 50.39260385 | 45.91663843 | 3979 | 1355 |

## Blocked-Entry Attribution

- Total blocked open signals measured: `110609`.
- Canonical blocked baseline trades with matched PnL attribution: `30377`.

| Variant | Blocked Signals | Matched Baseline Trades | Avoided Losers | Missed Winners | Large Losses Reduced | Reason Counts |
|---|---:|---:|---:|---:|---:|---|
| `avoid_low_atr_percentile_20` | 11164 | 3070 | 2278 | 792 | 35 | `{'blocked_low_atr_percentile': 11164}` |
| `avoid_low_atr_percentile_30` | 15772 | 4054 | 2990 | 1064 | 45 | `{'blocked_low_atr_percentile': 15772}` |
| `avoid_flat_sma20_slope` | 13606 | 3941 | 2936 | 1005 | 3 | `{'blocked_flat_sma20_slope': 13606}` |
| `avoid_flat_ema10_slope` | 8361 | 4228 | 3144 | 1084 | 13 | `{'blocked_flat_ema10_slope': 8361}` |
| `avoid_low_rolling_range_20` | 19321 | 4570 | 3480 | 1090 | 2 | `{'blocked_low_rolling_range': 19321}` |
| `avoid_low_rolling_range_50` | 23647 | 5107 | 3827 | 1280 | 2 | `{'blocked_low_rolling_range': 23647}` |
| `avoid_macd_flat_chop` | 98 | 81 | 72 | 9 | 0 | `{'blocked_macd_flat_chop': 98}` |
| `avoid_sideways_low_volatility_conservative` | 18640 | 5326 | 3975 | 1351 | 4 | `{'blocked_combined_sideways_low_volatility': 18640, 'blocked_flat_sma20_slope': 14013, 'blocked_low_rolling_range': 17790, 'blocked_flat_ema10_slope': 1992, 'blocked_low_atr_percentile': 11061, 'blocked_macd_flat_chop': 341}` |

## Control-Pocket Impact

| Variant | Controls | Improved | Preserved | Damaged | Return Reduced | Drawdown Reduced | Trade Count Reduced Too Much |
|---|---:|---:|---:|---:|---:|---:|---:|
| `avoid_flat_ema10_slope` | 15 | 3 | 4 | 8 | 8 | 4 | 0 |
| `avoid_flat_sma20_slope` | 15 | 1 | 2 | 12 | 12 | 6 | 0 |
| `avoid_low_atr_percentile_20` | 15 | 5 | 0 | 10 | 10 | 12 | 0 |
| `avoid_low_atr_percentile_30` | 15 | 4 | 0 | 11 | 11 | 12 | 0 |
| `avoid_low_rolling_range_20` | 15 | 0 | 13 | 2 | 2 | 1 | 0 |
| `avoid_low_rolling_range_50` | 15 | 2 | 11 | 2 | 2 | 1 | 0 |
| `avoid_macd_flat_chop` | 15 | 0 | 15 | 0 | 0 | 0 | 0 |
| `avoid_sideways_low_volatility_conservative` | 15 | 2 | 2 | 11 | 11 | 4 | 0 |

## Candidate / Rejected Variants

- Candidate for more evidence: `none`.
- Rejected / not promoted: `avoid_flat_ema10_slope, avoid_flat_sma20_slope, avoid_low_atr_percentile_20, avoid_low_atr_percentile_30, avoid_low_rolling_range_20, avoid_low_rolling_range_50, avoid_macd_flat_chop, avoid_sideways_low_volatility_conservative`.

## Limitations

- `dashboard_date_filters_are_display_only_not_canonical_evidence`
- `exit_signal_skipped_no_fill_candle_for_next_candle_close`
- `exit_signal_skipped_no_fill_candle_for_next_candle_open`
- `independent_scenarios_are_not_one_combined_account`
- `no_variant_is_production_approved`
- `open_positions_are_force_closed_at_window_end_for_sor_ev3`
- `reduce_actions_are_simulated_as_full_exits_for_sor_ev3`
- `sor_ev3_tests_only_founder_selected_sideways_low_volatility_family`

## Recommended Next Phase

If the founder wants to continue, SOR-EV4 should take only a narrow candidate from this report, rerun it with out-of-sample-style date slices, and require control-pocket preservation before any rule-change proposal. If no candidate is clean, reject the sideways/low-volatility idea for now.

## Boundary Confirmation

- `adds_sor_fanout_cbbo_or_target_reselection`: `False`
- `approves_live_trading`: `False`
- `broad_parameter_grid_search`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `changes_production_money_flow_rules`: `False`
- `creates_orders`: `False`
- `optimizes_parameters_blindly`: `False`
- `uses_dashboard_chart_data_as_canonical_evidence`: `False`
- `uses_dashboard_date_filter_recalculation`: `False`
- `uses_hyperliquid_testnet_prices`: `False`
- `uses_only_canonical_sv2_0_2_pack_paths`: `True`
