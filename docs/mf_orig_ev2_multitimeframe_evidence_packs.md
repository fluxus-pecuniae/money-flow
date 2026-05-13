# MF-ORIG-EV2 Multi-Timeframe Original Money Flow Evidence Packs

## Executive Summary

MF-ORIG-EV2 extends the corrected MF-ORIG-EV1.1 Original Money Flow reconstruction across all canonical SV2.0.2 supported symbols and all four timeframes for founder review. It is evidence-only. Production Money Flow v1.2 is unchanged. No orders are submitted. No private/signed/order endpoints are called.

## Scope

- Hypotheses: the four source 1% risk-size MF-ORIG hypotheses plus four founder-requested `_full_equity` counterparts.
- Sizing modes: `source_1pct_risk` keeps the source-faithful 1% risk-budget sizing; `full_equity_notional` sizes each entry from current realized equity for direct comparison with full-equity replay expectations.
- Symbols: `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `HYPE`, `BNB`, `SUI`, `AVAX`.
- Timeframes: `15m`, `1h`, `4h`, `1d`.
- Fill assumptions: `next_candle_open`, `next_candle_close`.
- Accounting: `event_ledger_accounting` with `peak_to_trough` drawdown.
- Baseline: canonical SV2.0.2 Money Flow v1.2 DB-imported evidence timestamp `20260512T064916Z`.

## Timeframe Interpretation

| Timeframe | Role |
| --- | --- |
| `1d` | `source_primary_original_money_flow_timeframe` |
| `4h` | `swing_fractal_adaptation` |
| `1h` | `intraday_fractal_adaptation` |
| `15m` | `stress_test_short_term_fractal_adaptation_not_source_primary` |

## Evidence Pack Status

- Status: `generated`
- Pack count: `288`
- Generated evidence-pack directories are review artifacts and are not committed as large generated packs.

## Hypothesis Summary

| Hypothesis | Scenarios | 1D Scenarios | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades | Candidate Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `mf_orig_1d_stage2_5_20_crossover` | 72 | 18 | 84790.69465207 | 301.86520478 | 7843 | `higher_return_but_higher_drawdown` |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | 72 | 18 | 1428.96251453 | 4911.61191553 | 7843 | `higher_return_but_higher_drawdown` |
| `mf_orig_1d_stage2_breakout_resistance` | 72 | 18 | 105383.2973339 | -895.20263528 | 3466 | `source_faithful_but_underperformed` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | 72 | 18 | 41169.79498246 | 4802.88301572 | 3466 | `higher_return_but_higher_drawdown` |
| `mf_orig_stage2_pullback_reclaim` | 72 | 18 | 84225.75375911 | 340.33254385 | 7807 | `higher_return_but_higher_drawdown` |
| `mf_orig_stage2_pullback_reclaim_full_equity` | 72 | 18 | 9071.70800637 | 2045.01454028 | 7807 | `higher_return_but_higher_drawdown` |
| `mf_orig_stage_filter_only` | 72 | 18 | 95173.09439264 | -127.07516591 | 6433 | `source_faithful_but_underperformed` |
| `mf_orig_stage_filter_only_full_equity` | 72 | 18 | 16994.05580631 | 4821.01281543 | 6433 | `higher_return_but_higher_drawdown` |

## Per-Timeframe Results

| Timeframe | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |
| --- | ---: | ---: | ---: | ---: |
| `15m` | 144 | 172755.16886459 | 510.03731931 | 19980 |
| `1d` | 144 | -123341.42568788 | 4911.61191553 | 1576 |
| `1h` | 144 | 260621.78567758 | 2069.22510861 | 18740 |
| `4h` | 144 | 128201.8325931 | 2259.29175648 | 10802 |

## Per-Symbol Results

| Symbol | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |
| --- | ---: | ---: | ---: | ---: |
| `AVAX` | 64 | 34170.83247757 | 1560.15654487 | 5728 |
| `BNB` | 64 | 71298.9059605 | 1918.43258468 | 5562 |
| `BTC` | 64 | 44557.93542951 | 1169.26200154 | 5756 |
| `DOGE` | 64 | -6126.10714566 | 477.08859668 | 5528 |
| `ETH` | 64 | -3615.38600887 | 3067.46676736 | 5840 |
| `HYPE` | 64 | 9505.41465819 | 4911.61191553 | 5576 |
| `SOL` | 64 | 92935.58592406 | 2259.29175648 | 5690 |
| `SUI` | 64 | 217629.18548214 | 2022.15593796 | 5608 |
| `XRP` | 64 | -22119.00533005 | 2025.19987172 | 5810 |

## Candidate Gate

| Hypothesis | Status | Gate Blockers |
| --- | --- | --- |
| `mf_orig_1d_stage2_5_20_crossover` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_1d_stage2_breakout_resistance` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_stage2_pullback_reclaim` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_stage2_pullback_reclaim_full_equity` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_stage_filter_only` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_stage_filter_only_full_equity` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |

## Dashboard Status

- Historical Replay: `implemented`
- Evidence UI: `implemented`
- Date-filter warning: `display_filtered_not_canonical_pack_regeneration`

The dashboard date filters are display-only recalculations from loaded evidence trades. Exact arbitrary-date canonical evidence requires backend Strategy Validation regeneration.

## Control Pockets

| Hypothesis | Pocket | Status | PnL Delta | Drawdown Delta |
| --- | --- | --- | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | `ETH 1h current baseline` | `improved` | 3977.68857083 | -1977.36153675 |
| `mf_orig_1d_stage2_5_20_crossover` | `positive 1d pockets` | `damaged` | -31161.37309375 | -1373.85837354 |
| `mf_orig_1d_stage2_5_20_crossover` | `all_1d_pockets` | `damaged` | -21479.11068129 | -1373.85837354 |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | `ETH 1h current baseline` | `damaged` | 917.27118242 | 332.91154704 |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | `positive 1d pockets` | `damaged` | -16557.7741039 | 4911.61191553 |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | `all_1d_pockets` | `damaged` | -4042.1239264 | 4911.61191553 |
| `mf_orig_1d_stage2_breakout_resistance` | `ETH 1h current baseline` | `improved` | 4614.06140916 | -3181.89295235 |
| `mf_orig_1d_stage2_breakout_resistance` | `positive 1d pockets` | `damaged` | -32564.72850052 | -1281.40684308 |
| `mf_orig_1d_stage2_breakout_resistance` | `all_1d_pockets` | `damaged` | -23198.24309566 | -1281.40684308 |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `ETH 1h current baseline` | `improved` | 2152.48329524 | -1314.22667286 |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `positive 1d pockets` | `damaged` | -28052.52086072 | 4802.88301572 |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `all_1d_pockets` | `damaged` | -20743.63602291 | 4802.88301572 |
| `mf_orig_stage2_pullback_reclaim` | `ETH 1h current baseline` | `improved` | 3957.02311967 | -1976.01427067 |
| `mf_orig_stage2_pullback_reclaim` | `positive 1d pockets` | `damaged` | -30664.48130514 | -1374.31876925 |
| `mf_orig_stage2_pullback_reclaim` | `all_1d_pockets` | `damaged` | -21121.18871483 | -1374.31876925 |
| `mf_orig_stage2_pullback_reclaim_full_equity` | `ETH 1h current baseline` | `damaged` | 838.69816073 | 336.45825558 |
| `mf_orig_stage2_pullback_reclaim_full_equity` | `positive 1d pockets` | `damaged` | -11074.50741196 | 1838.73947684 |
| `mf_orig_stage2_pullback_reclaim_full_equity` | `all_1d_pockets` | `damaged` | -3119.82878015 | 1838.73947684 |
| `mf_orig_stage_filter_only` | `ETH 1h current baseline` | `improved` | 4836.59786961 | -2582.04521532 |
| `mf_orig_stage_filter_only` | `positive 1d pockets` | `damaged` | -31116.45602185 | -1419.91150772 |
| `mf_orig_stage_filter_only` | `all_1d_pockets` | `damaged` | -21593.64858825 | -1419.91150772 |
| `mf_orig_stage_filter_only_full_equity` | `ETH 1h current baseline` | `improved` | 2221.10944032 | -773.06989715 |
| `mf_orig_stage_filter_only_full_equity` | `positive 1d pockets` | `damaged` | -16231.92585193 | 4821.01281543 |
| `mf_orig_stage_filter_only_full_equity` | `all_1d_pockets` | `damaged` | -8043.64587839 | 4821.01281543 |

## Limitations

- `15m_is_stress_test_not_source_primary`
- `dashboard_date_filters_are_display_only_not_canonical_evidence`
- `exit_signal_skipped_no_fill_candle_for_next_candle_close`
- `exit_signal_skipped_no_fill_candle_for_next_candle_open`
- `independent_scenarios_are_not_one_combined_account`
- `mf_orig_ev2_extends_source_reconstruction_across_fractal_timeframes`
- `open_positions_are_force_closed_at_dataset_end`
- `open_signal_skipped_no_fill_candle_for_next_candle_close`
- `open_signal_skipped_no_fill_candle_for_next_candle_open`
- `source_pdf_not_available_to_agent_prompt_summary_used`
- `support_resistance_modeled_with_simple_prior_support_low_proxy`
- `tsi_deferred_macd_used_as_substitute`

## Boundary Confirmation

- MF-ORIG-EV2 is evidence-only.
- Production Money Flow v1.2 remains unchanged.
- No MF-ORIG hypothesis is approved for production.
- No paper-runtime approval follows from this phase.
- Live trading is not approved.
- No orders were submitted.
- Hyperliquid testnet prices are not strategy truth.
- Independent scenario sums are not one account PnL.

## Recommended Next Phase

`MF-ORIG-EV3` should only proceed after founder review of the multi-timeframe replay charts and comparison tables.
