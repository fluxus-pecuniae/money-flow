# MF-ORIG-EV2 Multi-Timeframe Original Money Flow Evidence Packs

## Executive Summary

MF-ORIG-EV2 extends the corrected MF-ORIG-EV1.1 Original Money Flow reconstruction across all canonical SV2.0.2 supported symbols and all four timeframes for founder review. It is evidence-only. Production Money Flow v1.2 is unchanged. No orders are submitted. No private/signed/order endpoints are called.

## Scope

- Hypotheses: `mf_orig_stage2_5_20_crossover`, `mf_orig_stage2_breakout_resistance`, `mf_orig_stage2_pullback_reclaim`, `mf_orig_stage_filter_only`.
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
- Pack count: `144`
- Generated evidence-pack directories are review artifacts and are not committed as large generated packs.

## Hypothesis Summary

| Hypothesis | Scenarios | 1D Scenarios | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades | Candidate Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `mf_orig_1d_stage2_5_20_crossover` | 72 | 18 | 84790.69465207 | 301.86520478 | 7843 | `higher_return_but_higher_drawdown` |
| `mf_orig_1d_stage2_breakout_resistance` | 72 | 18 | 105383.2973339 | -895.20263528 | 3466 | `source_faithful_but_underperformed` |
| `mf_orig_stage2_pullback_reclaim` | 72 | 18 | 84225.75375911 | 340.33254385 | 7807 | `higher_return_but_higher_drawdown` |
| `mf_orig_stage_filter_only` | 72 | 18 | 95173.09439264 | -127.07516591 | 6433 | `source_faithful_but_underperformed` |

## Per-Timeframe Results

| Timeframe | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |
| --- | ---: | ---: | ---: | ---: |
| `15m` | 72 | 89358.93786244 | 340.33254385 | 9990 |
| `1d` | 72 | -87392.19108003 | -1281.40684308 | 788 |
| `1h` | 72 | 202991.80570203 | -349.29468305 | 9370 |
| `4h` | 72 | 164614.28765328 | -2004.80559245 | 5401 |

## Per-Symbol Results

| Symbol | Rows | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades |
| --- | ---: | ---: | ---: | ---: |
| `AVAX` | 32 | 57294.65016356 | -122.24410859 | 2864 |
| `BNB` | 32 | 39408.14258451 | -279.66875709 | 2781 |
| `BTC` | 32 | 35014.23024512 | -349.29468305 | 2878 |
| `DOGE` | 32 | 31959.28077987 | -749.33313857 | 2764 |
| `ETH` | 32 | 18652.23225485 | 326.14367512 | 2920 |
| `HYPE` | 32 | -6653.56979945 | -1474.97201378 | 2788 |
| `SOL` | 32 | 70520.48533988 | -376.08839056 | 2845 |
| `SUI` | 32 | 115862.57069388 | -901.2118589 | 2804 |
| `XRP` | 32 | 7514.8178755 | 340.33254385 | 2905 |

## Candidate Gate

| Hypothesis | Status | Gate Blockers |
| --- | --- | --- |
| `mf_orig_1d_stage2_5_20_crossover` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_1d_stage2_breakout_resistance` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_stage2_pullback_reclaim` | `higher_return_but_higher_drawdown` | `control_pocket_not_preserved, drawdown_worse_than_v1_2` |
| `mf_orig_stage_filter_only` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |

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
| `mf_orig_1d_stage2_breakout_resistance` | `ETH 1h current baseline` | `improved` | 4614.06140916 | -3181.89295235 |
| `mf_orig_1d_stage2_breakout_resistance` | `positive 1d pockets` | `damaged` | -32564.72850052 | -1281.40684308 |
| `mf_orig_1d_stage2_breakout_resistance` | `all_1d_pockets` | `damaged` | -23198.24309566 | -1281.40684308 |
| `mf_orig_stage2_pullback_reclaim` | `ETH 1h current baseline` | `improved` | 3957.02311967 | -1976.01427067 |
| `mf_orig_stage2_pullback_reclaim` | `positive 1d pockets` | `damaged` | -30664.48130514 | -1374.31876925 |
| `mf_orig_stage2_pullback_reclaim` | `all_1d_pockets` | `damaged` | -21121.18871483 | -1374.31876925 |
| `mf_orig_stage_filter_only` | `ETH 1h current baseline` | `improved` | 4836.59786961 | -2582.04521532 |
| `mf_orig_stage_filter_only` | `positive 1d pockets` | `damaged` | -31116.45602185 | -1419.91150772 |
| `mf_orig_stage_filter_only` | `all_1d_pockets` | `damaged` | -21593.64858825 | -1419.91150772 |

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
