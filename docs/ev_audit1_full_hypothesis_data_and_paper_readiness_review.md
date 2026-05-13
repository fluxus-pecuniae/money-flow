# EV-AUDIT1 Full Hypothesis, Data Integrity, And Paper-Readiness Review

Status: `implemented`

EV-AUDIT1 is audit-only. Production Money Flow rules are unchanged. No strategy has production authorization. No strategy has paper-runtime authorization from this audit. Live trading is not approved. No orders were submitted. No private, signed, or order endpoints were called. Hyperliquid testnet prices are not strategy truth. Dashboard date filters are display-only and not canonical evidence.

## Executive Verdict

- Credible clean candidate: `none_cleanly_promoted`.
- Best founder-review candidate: `avoid_low_rolling_range_50` because largest SOR-EV3 aggregate PnL delta, but still failed drawdown/control-pocket gates.
- Best MF-ORIG full-equity review lane: `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- Best aggregate hypothesis by delta: `mf_orig_1d_stage2_breakout_resistance`.
- Worst aggregate hypothesis by delta: `macd_histogram_above_negative_threshold`.
- Current evidence is good enough for visual review and hypothesis filtering only.
- Current evidence is not good enough for a production rule change, live trading, or strategy paper-runtime authorization.
- Recommended next phase: `PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime` as a separately scoped observation phase using trusted public mainnet candles.

## Evidence Inventory

| Family | Hypothesis / Track | Status | Evidence Class | Methodology | Report |
| --- | --- | --- | --- | --- | --- |
| current_money_flow | money_flow_v1_2 | implemented | canonical_evidence | canonical_evidence | docs/sv2_0_2_canonical_sv2_evidence_packs.md |
| sor_ev1 | loss_anatomy_and_completed_trade_overlays | implemented | completed_trade_overlay_estimate | completed_trade_overlay_estimate | docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md |
| sor_ev2 | true_forward_stop_and_rejected_signal_replay | implemented | true_forward_replay | true_forward_replay | docs/sor_ev2_true_forward_stop_and_rejected_signal_replay.md |
| sor_ev3 | avoid_sideways_low_volatility | implemented | true_forward_replay | true_forward_replay | docs/sor_ev3_avoid_sideways_low_volatility.md |
| mf_orig | mf_orig_ev1_1_original_reconstruction | implemented | compact_replay_only | true_forward_replay | docs/mf_orig_ev1_original_money_flow_reconstruction.md |
| mf_orig | mf_orig_ev2_multitimeframe_full_equity_and_source_risk | implemented | true_forward_replay | true_forward_replay | docs/mf_orig_ev2_multitimeframe_evidence_packs.md |
| strat_ev1 | regime_gated_trend | not_implemented | not_implemented | plan_only |  |

## Data Integrity Audit

Data verdict: `canonical_sv2_0_2_data_good_enough_for_visual_review_and_hypothesis_filtering`.

| Symbol | Timeframe | Status | Earliest | Latest | Candles | Coverage | Limitations | Evidence Ready |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AVAX | 15m | canonical_db_imported | 2026-03-21T04:00:00+00:00 | 2026-05-12T06:45:00+00:00 | 5004 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| AVAX | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| AVAX | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| AVAX | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| BNB | 15m | canonical_db_imported | 2026-03-21T04:00:00+00:00 | 2026-05-12T06:45:00+00:00 | 5004 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| BNB | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| BNB | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| BNB | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| BTC | 15m | canonical_db_imported | 2026-03-21T03:45:00+00:00 | 2026-05-12T06:45:00+00:00 | 5005 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| BTC | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| BTC | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| BTC | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| DOGE | 15m | canonical_db_imported | 2026-03-21T04:00:00+00:00 | 2026-05-12T06:45:00+00:00 | 5004 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| DOGE | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| DOGE | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| DOGE | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| ETH | 15m | canonical_db_imported | 2026-03-21T03:45:00+00:00 | 2026-05-12T06:45:00+00:00 | 5005 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| ETH | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| ETH | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| ETH | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| HYPE | 15m | canonical_db_imported | 2026-03-21T02:00:00+00:00 | 2026-05-12T06:45:00+00:00 | 5012 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| HYPE | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| HYPE | 1h | canonical_db_imported | 2025-10-15T21:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5002 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| HYPE | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| SOL | 15m | canonical_db_imported | 2026-03-21T03:45:00+00:00 | 2026-05-12T06:45:00+00:00 | 5005 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| SOL | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| SOL | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| SOL | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| SUI | 15m | canonical_db_imported | 2026-03-21T04:15:00+00:00 | 2026-05-12T06:45:00+00:00 | 5003 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| SUI | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| SUI | 1h | canonical_db_imported | 2025-10-15T23:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 5000 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| SUI | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| XRP | 15m | canonical_db_imported | 2026-03-21T04:30:00+00:00 | 2026-05-12T06:45:00+00:00 | 5002 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| XRP | 1d | canonical_db_imported | 2025-01-02T00:00:00+00:00 | 2026-05-12T00:00:00+00:00 | 496 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |
| XRP | 1h | canonical_db_imported | 2025-10-16T00:00:00+00:00 | 2026-05-12T06:00:00+00:00 | 4999 | 1.00000000 | hyperliquid_public_5000_candle_limit, jan_2025_target_not_met | True |
| XRP | 4h | canonical_db_imported | 2025-01-01T04:00:00+00:00 | 2026-05-12T04:00:00+00:00 | 2977 | 1.00000000 | jan_2025_target_met_where_public_history_supports_it | True |

### Data Red-Team Notes

- No P0 data-corruption issue was found in canonical SV2.0.2 reports.
- 15m and 1h conclusions are lower confidence because public Hyperliquid history is truncated by the 5000-candle limit.
- Dashboard date-filter metrics must not be used as canonical evidence.
- MF-ORIG source-faithfulness still needs direct PDF reconciliation.

## Backtest Methodology Audit

| Score | Value |
| --- | --- |
| Methodology Confidence | 3.5 |
| Data Confidence | 4.0 |
| Candidate Confidence | 2.0 |
| Founder Decision Readiness | 3.0 |

Good enough for visual review and hypothesis filtering; not enough for production rule changes, paper-runtime approval, or live trading.

## Full Hypothesis Comparison Matrix

All aggregate rows are `sum across independent research scenarios`, not one combined account.

| Family | Hypothesis | Methodology | PnL Delta / Net | DD Delta / Worst DD | Candidate Status | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| current_money_flow | money_flow_v1_2 | canonical_evidence | -136305.83726556 | 8297.30277226 | baseline_not_candidate | current baseline |
| sor_ev1_loss_anatomy | atr_stop_1_5x | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | atr_stop_2x | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | avoid_macd_flat_chop | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | avoid_sideways_low_volatility | completed_trade_overlay_estimate | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | fixed_stop_loss_pct_1 | completed_trade_overlay_estimate | 12772.36098593 | 4094.73445914 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev1_loss_anatomy | fixed_stop_loss_pct_1_5 | completed_trade_overlay_estimate | 17055.45398882 | 4925.15766316 | overfit_risk | overfit_risk |
| sor_ev1_loss_anatomy | fixed_stop_loss_pct_2 | completed_trade_overlay_estimate | 9900.39603028 | 2622.79044822 | overfit_risk | overfit_risk |
| sor_ev1_loss_anatomy | large_bear_candle_exit | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | lower_rsi_trend_intact_entry | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | macd_histogram_above_negative_threshold | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | macd_histogram_improving_entry | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | recent_low_stop_lookback_10 | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | recent_low_stop_lookback_5 | deferred_requires_rejected_signal_replay | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | reject_entry_if_price_too_far_above_ema10 | completed_trade_overlay_estimate | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev1_loss_anatomy | reject_entry_if_price_too_far_above_sma20 | completed_trade_overlay_estimate | 0 | 0 | insufficient_data | insufficient_data |
| sor_ev2_true_forward | atr_stop_1_5x | true_forward_replay | -1330.72433027 | 224.70709479 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | atr_stop_2x | true_forward_replay | 1110.96407618 | 724.89448725 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | avoid_macd_flat_chop | true_forward_replay | 24480.81717549 | 912.10224812 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | avoid_sideways_low_volatility | true_forward_replay | 39290.77523169 | 122.86442415 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | fixed_stop_loss_pct_1 | true_forward_replay | -22131.22202431 | 1728.65517153 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | fixed_stop_loss_pct_1_5 | true_forward_replay | -915.96963562 | 1473.11610247 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | fixed_stop_loss_pct_2 | true_forward_replay | 7547.16213364 | 1371.66992427 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | large_bear_candle_exit | true_forward_replay | -3598.28775776 | 907.68924658 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | lower_rsi_trend_intact_entry | true_forward_replay | -25834.02207001 | 1153.56227228 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | macd_histogram_above_negative_threshold | true_forward_replay | -28400.83065884 | 1781.74648658 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | macd_histogram_improving_entry | true_forward_replay | -28085.24717214 | 1781.74648658 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | recent_low_stop_lookback_10 | true_forward_replay | 0 | 0 | no_op | no_op |
| sor_ev2_true_forward | recent_low_stop_lookback_5 | true_forward_replay | -652.11626058 | 73.20255892 | deteriorated_vs_baseline | deteriorated_vs_baseline |
| sor_ev2_true_forward | reject_entry_if_price_too_far_above_ema10 | true_forward_replay | 25590.80798278 | 804.09390751 | overfit_risk | overfit_risk |
| sor_ev2_true_forward | reject_entry_if_price_too_far_above_sma20 | true_forward_replay | 30321.20937498 | 669.85332718 | overfit_risk | overfit_risk |
| sor_ev3_avoid_sideways_low_volatility | avoid_flat_ema10_slope | true_forward_replay | 14679.99888902 | 387.95776834 | not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_flat_sma20_slope | true_forward_replay | 14414.66327302 | 2451.97220482 | not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_low_atr_percentile_20 | true_forward_replay | 3352.75625247 | 1473.07030333 | not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_low_atr_percentile_30 | true_forward_replay | -12481.40606772 | 1234.04290198 | not_promoted | aggregate_net_pnl_delta_not_positive, worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_low_rolling_range_20 | true_forward_replay | 48845.55526731 | 119.72046323 | promising_not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_low_rolling_range_50 | true_forward_replay | 55197.69963174 | 410.24876203 | promising_not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| sor_ev3_avoid_sideways_low_volatility | avoid_macd_flat_chop | true_forward_replay | 580.18568893 | 29.98203801 | not_promoted | worst_drawdown_worsened |
| sor_ev3_avoid_sideways_low_volatility | avoid_sideways_low_volatility_conservative | true_forward_replay | 24268.20619967 | 2451.97220482 | not_promoted | worst_drawdown_worsened, control_pockets_damaged |
| mf_orig | mf_orig_1d_stage2_5_20_crossover | true_forward_replay | 84790.69465207 | 301.86520478 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |
| mf_orig | mf_orig_1d_stage2_5_20_crossover_full_equity | true_forward_replay | 1428.96251453 | 4911.61191553 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |
| mf_orig | mf_orig_1d_stage2_breakout_resistance | true_forward_replay | 105383.2973339 | -895.20263528 | source_faithful_but_underperformed | control_pocket_not_preserved |
| mf_orig | mf_orig_1d_stage2_breakout_resistance_full_equity | true_forward_replay | 41169.79498246 | 4802.88301572 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |
| mf_orig | mf_orig_stage2_pullback_reclaim | true_forward_replay | 84225.75375911 | 340.33254385 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |
| mf_orig | mf_orig_stage2_pullback_reclaim_full_equity | true_forward_replay | 9071.70800637 | 2045.01454028 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |
| mf_orig | mf_orig_stage_filter_only | true_forward_replay | 95173.09439264 | -127.07516591 | source_faithful_but_underperformed | control_pocket_not_preserved |
| mf_orig | mf_orig_stage_filter_only_full_equity | true_forward_replay | 16994.05580631 | 4821.01281543 | higher_return_but_higher_drawdown | control_pocket_not_preserved, drawdown_worse_than_v1_2 |

## Biggest Winner Analysis

| Rank | Strategy | Symbol | TF | Fill | Entry | Exit | PnL | Why It Won |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_open | 2025-04-12T00:00:00+00:00 | 2025-06-20T00:00:00+00:00 | 12174.04947068 | stage2_price_above_sma20, ema5_cross_above_sma20, macd_confirmation_or_improving |
| 2 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_open | 2025-04-18T00:00:00+00:00 | 2025-06-20T00:00:00+00:00 | 11477.65150257 | stage2_resistance_breakout, price_above_sma20, ema5_above_sma20, macd_confirmation_or_improving |
| 3 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_open | 2025-04-13T00:00:00+00:00 | 2025-06-20T00:00:00+00:00 | 11297.57900537 | current_v1_2_like_entry_with_original_stage2_filter |
| 4 | money_flow_v1_2 | HYPE | 1d | next_candle_close | 2025-04-30T00:00:00+00:00 | 2025-05-27T00:00:00+00:00 | 11200.61621767 | data_not_available_in_source_bundle |
| 5 | money_flow_v1_2 | HYPE | 1d | next_candle_open | 2025-04-29T00:00:00+00:00 | 2025-05-26T00:00:00+00:00 | 11054.39226948 | data_not_available_in_source_bundle |
| 6 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_close | 2025-04-14T00:00:00+00:00 | 2025-06-21T00:00:00+00:00 | 10405.03907996 | current_v1_2_like_entry_with_original_stage2_filter |
| 7 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_open | 2025-04-29T00:00:00+00:00 | 2025-06-20T00:00:00+00:00 | 9712.63142783 | stage2_pullback_near_ema10_or_sma20, price_reclaimed_ema5_or_ema10, macd_not_strong_bearish |
| 8 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_close | 2025-04-19T00:00:00+00:00 | 2025-06-21T00:00:00+00:00 | 9535.52210975 | stage2_resistance_breakout, price_above_sma20, ema5_above_sma20, macd_confirmation_or_improving |
| 9 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_close | 2025-04-13T00:00:00+00:00 | 2025-06-21T00:00:00+00:00 | 9282.92083343 | stage2_price_above_sma20, ema5_cross_above_sma20, macd_confirmation_or_improving |
| 10 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_close | 2025-04-30T00:00:00+00:00 | 2025-06-21T00:00:00+00:00 | 7900.93376157 | stage2_pullback_near_ema10_or_sma20, price_reclaimed_ema5_or_ema10, macd_not_strong_bearish |
| 11 | money_flow_v1_2 | DOGE | 1d | next_candle_close | 2025-07-08T00:00:00+00:00 | 2025-07-22T00:00:00+00:00 | 5669.89042517 | data_not_available_in_source_bundle |
| 12 | money_flow_v1_2 | XRP | 1d | next_candle_close | 2025-07-02T00:00:00+00:00 | 2025-07-19T00:00:00+00:00 | 5119.59718519 | data_not_available_in_source_bundle |
| 13 | mf_orig_stage_filter_only_full_equity | XRP | 4h | next_candle_close | 2025-07-06T20:00:00+00:00 | 2025-07-22T12:00:00+00:00 | 5012.32815051 | current_v1_2_like_entry_with_original_stage2_filter |
| 14 | money_flow_v1_2 | ETH | 1d | next_candle_close | 2025-07-05T00:00:00+00:00 | 2025-07-20T00:00:00+00:00 | 4931.62278067 | data_not_available_in_source_bundle |
| 15 | money_flow_v1_2 | XRP | 1d | next_candle_open | 2025-07-03T00:00:00+00:00 | 2025-07-18T00:00:00+00:00 | 4844.29314369 | data_not_available_in_source_bundle |
| 16 | mf_orig_1d_stage2_breakout_resistance_full_equity | XRP | 4h | next_candle_close | 2025-07-07T20:00:00+00:00 | 2025-07-22T12:00:00+00:00 | 4669.91986767 | stage2_resistance_breakout, price_above_sma20, ema5_above_sma20, macd_confirmation_or_improving |
| 17 | mf_orig_1d_stage2_5_20_crossover_full_equity | SUI | 4h | next_candle_open | 2025-04-21T04:00:00+00:00 | 2025-04-28T16:00:00+00:00 | 4620.2052672 | stage2_price_above_sma20, ema5_cross_above_sma20, macd_confirmation_or_improving |
| 18 | mf_orig_stage_filter_only_full_equity | XRP | 4h | next_candle_open | 2025-07-06T16:00:00+00:00 | 2025-07-22T08:00:00+00:00 | 4571.54378971 | current_v1_2_like_entry_with_original_stage2_filter |
| 19 | money_flow_v1_2 | DOGE | 1d | next_candle_open | 2025-07-07T00:00:00+00:00 | 2025-07-21T00:00:00+00:00 | 4529.78029681 | data_not_available_in_source_bundle |
| 20 | mf_orig_1d_stage2_5_20_crossover_full_equity | XRP | 4h | next_candle_close | 2025-07-06T20:00:00+00:00 | 2025-07-22T12:00:00+00:00 | 4483.54083769 | stage2_price_above_sma20, ema5_cross_above_sma20, macd_confirmation_or_improving |
| 21 | money_flow_v1_2 | ETH | 1d | next_candle_open | 2025-07-04T00:00:00+00:00 | 2025-07-19T00:00:00+00:00 | 4474.48120693 | data_not_available_in_source_bundle |
| 22 | mf_orig_stage2_pullback_reclaim_full_equity | XRP | 4h | next_candle_close | 2025-07-06T20:00:00+00:00 | 2025-07-22T12:00:00+00:00 | 4459.92390874 | stage2_pullback_near_ema10_or_sma20, price_reclaimed_ema5_or_ema10, macd_not_strong_bearish |
| 23 | mf_orig_stage_filter_only_full_equity | ETH | 1d | next_candle_open | 2025-07-03T00:00:00+00:00 | 2025-08-02T00:00:00+00:00 | 4357.61730199 | current_v1_2_like_entry_with_original_stage2_filter |
| 24 | mf_orig_stage2_pullback_reclaim_full_equity | SUI | 4h | next_candle_open | 2025-04-21T04:00:00+00:00 | 2025-04-28T16:00:00+00:00 | 4312.85017765 | stage2_pullback_near_ema10_or_sma20, price_reclaimed_ema5_or_ema10, macd_not_strong_bearish |
| 25 | mf_orig_1d_stage2_5_20_crossover_full_equity | XRP | 4h | next_candle_open | 2025-07-06T16:00:00+00:00 | 2025-07-22T08:00:00+00:00 | 4309.52773177 | stage2_price_above_sma20, ema5_cross_above_sma20, macd_confirmation_or_improving |

Largest wins generally came from trend-continuation or Stage 2 contexts where the strategy stayed in the move long enough for large favorable excursion. Repeatability is not assumed: several top wins are concentrated in specific symbols/timeframes and must survive both fill assumptions before being used for a rule-change proposal.

### Top 10 Winning Scenarios

| Rank | Strategy | Symbol | TF | Fill | Net PnL | Drawdown | Trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_open | 11335.34955943 | 9138.21536702 | 11 |
| 2 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_open | 10324.95150262 | 8015.75633962 | 9 |
| 3 | money_flow_v1_2 | HYPE | 1d | next_candle_open | 8597.96652902 | 6161.74212371 | 20 |
| 4 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_open | 8124.40005959 | 8937.18694764 | 7 |
| 5 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_open | 7600.86597636 | 10521.76463552 | 11 |
| 6 | money_flow_v1_2 | HYPE | 1d | next_candle_close | 7222.76102579 | 7011.59260042 | 19 |
| 7 | money_flow_v1_2 | ETH | 1d | next_candle_open | 5175.17008829 | 2258.88425669 | 19 |
| 8 | mf_orig_stage_filter_only_full_equity | SUI | 1d | next_candle_open | 4875.89351669 | 3825.64650255 | 11 |
| 9 | mf_orig_1d_stage2_5_20_crossover_full_equity | SUI | 1d | next_candle_open | 4803.79079666 | 4072.22688572 | 12 |
| 10 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_close | 4701.5413525 | 9622.7772438 | 9 |

### Top 10 Winning Hypotheses / Variants

| Rank | Family | Hypothesis | PnL Delta | DD Delta | Candidate Status |
| --- | --- | --- | --- | --- | --- |
| 1 | mf_orig | mf_orig_1d_stage2_breakout_resistance | 105383.2973339 | -895.20263528 | source_faithful_but_underperformed |
| 2 | mf_orig | mf_orig_stage_filter_only | 95173.09439264 | -127.07516591 | source_faithful_but_underperformed |
| 3 | mf_orig | mf_orig_1d_stage2_5_20_crossover | 84790.69465207 | 301.86520478 | higher_return_but_higher_drawdown |
| 4 | mf_orig | mf_orig_stage2_pullback_reclaim | 84225.75375911 | 340.33254385 | higher_return_but_higher_drawdown |
| 5 | sor_ev3_avoid_sideways_low_volatility | avoid_low_rolling_range_50 | 55197.69963174 | 410.24876203 | promising_not_promoted |
| 6 | sor_ev3_avoid_sideways_low_volatility | avoid_low_rolling_range_20 | 48845.55526731 | 119.72046323 | promising_not_promoted |
| 7 | mf_orig | mf_orig_1d_stage2_breakout_resistance_full_equity | 41169.79498246 | 4802.88301572 | higher_return_but_higher_drawdown |
| 8 | sor_ev2_true_forward | avoid_sideways_low_volatility | 39290.77523169 | 122.86442415 | deteriorated_vs_baseline |
| 9 | sor_ev2_true_forward | reject_entry_if_price_too_far_above_sma20 | 30321.20937498 | 669.85332718 | overfit_risk |
| 10 | sor_ev2_true_forward | reject_entry_if_price_too_far_above_ema10 | 25590.80798278 | 804.09390751 | overfit_risk |

## Biggest Loser Analysis

| Rank | Strategy | Symbol | TF | Fill | Entry | Exit | PnL | Exit / Context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_close | 2025-10-27T00:00:00+00:00 | 2025-11-05T00:00:00+00:00 | -3498.12580096 | price_close_below_sma20_exit |
| 2 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_open | 2025-10-27T00:00:00+00:00 | 2025-11-04T00:00:00+00:00 | -3447.12197364 | price_close_below_sma20_exit |
| 3 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_close | 2025-10-28T00:00:00+00:00 | 2025-11-05T00:00:00+00:00 | -3379.20657717 | price_close_below_sma20_exit |
| 4 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_close | 2025-10-27T00:00:00+00:00 | 2025-11-05T00:00:00+00:00 | -3103.13139564 | price_close_below_sma20_exit |
| 5 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_open | 2025-08-14T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | -2891.50280911 | price_close_below_sma20_exit |
| 6 | money_flow_v1_2 | SUI | 1d | next_candle_close | 2025-10-10T00:00:00+00:00 | 2025-10-12T00:00:00+00:00 | -2888.16856889 | ma_alignment_break |
| 7 | money_flow_v1_2 | DOGE | 1d | next_candle_close | 2025-10-10T00:00:00+00:00 | 2025-10-12T00:00:00+00:00 | -2757.8302426 | ma_alignment_break |
| 8 | mf_orig_1d_stage2_breakout_resistance_full_equity | ETH | 1d | next_candle_open | 2025-10-07T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | -2703.83602682 | structure_stop_hit |
| 9 | money_flow_v1_2 | HYPE | 1d | next_candle_open | 2025-05-28T00:00:00+00:00 | 2025-05-30T00:00:00+00:00 | -2622.62099832 | ma_alignment_break |
| 10 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_close | 2025-09-11T00:00:00+00:00 | 2025-09-23T00:00:00+00:00 | -2486.14854694 | price_close_below_sma20_exit |
| 11 | mf_orig_1d_stage2_5_20_crossover_full_equity | ETH | 1d | next_candle_open | 2025-10-04T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | -2443.97627535 | structure_stop_hit |
| 12 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_close | 2026-01-29T00:00:00+00:00 | 2026-02-12T00:00:00+00:00 | -2297.20710482 | price_close_below_sma20_exit |
| 13 | mf_orig_stage_filter_only_full_equity | ETH | 1d | next_candle_open | 2025-10-05T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | -2268.26374992 | structure_stop_hit |
| 14 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_open | 2025-10-26T00:00:00+00:00 | 2025-11-04T00:00:00+00:00 | -2193.17348062 | price_close_below_sma20_exit |
| 15 | money_flow_v1_2 | ETH | 1d | next_candle_close | 2025-10-06T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | -2183.61746845 | ma_alignment_break |
| 16 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_close | 2026-01-29T00:00:00+00:00 | 2026-02-12T00:00:00+00:00 | -2171.38640691 | price_close_below_sma20_exit |
| 17 | money_flow_v1_2 | HYPE | 1d | next_candle_close | 2026-01-07T00:00:00+00:00 | 2026-01-10T00:00:00+00:00 | -2119.1224135 | ma_alignment_break |
| 18 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_close | 2026-01-29T00:00:00+00:00 | 2026-02-12T00:00:00+00:00 | -2105.31776329 | price_close_below_sma20_exit |
| 19 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_open | 2025-08-11T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | -2085.54785057 | price_close_below_sma20_exit |
| 20 | money_flow_v1_2 | XRP | 4h | next_candle_open | 2025-03-03T08:00:00+00:00 | 2025-03-03T20:00:00+00:00 | -2058.79583042 | ma_alignment_break |
| 21 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_open | 2025-10-26T00:00:00+00:00 | 2025-11-04T00:00:00+00:00 | -2031.93842156 | price_close_below_sma20_exit |
| 22 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_open | 2025-08-15T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | -2020.10051569 | price_close_below_sma20_exit |
| 23 | mf_orig_1d_stage2_breakout_resistance_full_equity | SUI | 1d | next_candle_open | 2025-09-19T00:00:00+00:00 | 2025-09-23T00:00:00+00:00 | -1995.76390345 | structure_stop_hit |
| 24 | mf_orig_stage_filter_only_full_equity | ETH | 1d | next_candle_close | 2025-10-06T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | -1964.78120574 | structure_stop_hit |
| 25 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_close | 2025-08-16T00:00:00+00:00 | 2025-08-21T00:00:00+00:00 | -1903.45687444 | price_close_below_sma20_exit |

Largest losses are concentrated in late-extension, Stage 2 failure, or MA alignment break contexts. SOR-EV1/SOR-EV2 observed that many large losses had adverse-candle or prior-break context, but stop/exit variants still failed strict promotion because they damaged controls or worsened drawdown elsewhere.

### Top 10 Worst Scenarios

| Rank | Strategy | Symbol | TF | Fill | Net PnL | Drawdown | Trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_stage_filter_only_full_equity | SOL | 4h | next_candle_close | -6565.49830101 | 10649.53642431 | 80 |
| 2 | money_flow_v1_2 | SUI | 4h | next_candle_close | -6466.26235683 | 7503.99538686 | 130 |
| 3 | mf_orig_1d_stage2_5_20_crossover_full_equity | AVAX | 4h | next_candle_close | -6277.37126431 | 7418.44176107 | 89 |
| 4 | mf_orig_1d_stage2_5_20_crossover_full_equity | ETH | 4h | next_candle_open | -6139.72963585 | 6554.62137758 | 93 |
| 5 | mf_orig_1d_stage2_5_20_crossover_full_equity | SOL | 4h | next_candle_close | -6071.62377781 | 9866.57524892 | 91 |
| 6 | mf_orig_1d_stage2_5_20_crossover_full_equity | ETH | 4h | next_candle_close | -5992.71875845 | 6446.04315845 | 92 |
| 7 | mf_orig_stage2_pullback_reclaim_full_equity | AVAX | 4h | next_candle_close | -5853.21680143 | 7013.47677223 | 88 |
| 8 | money_flow_v1_2 | SUI | 4h | next_candle_open | -5811.52955766 | 6637.07020301 | 136 |
| 9 | mf_orig_1d_stage2_breakout_resistance_full_equity | ETH | 4h | next_candle_close | -5779.18840468 | 5786.63323809 | 41 |
| 10 | mf_orig_stage2_pullback_reclaim_full_equity | SOL | 4h | next_candle_close | -5750.93604005 | 9550.34162655 | 87 |

### Top 10 Worst Drawdown Contributors

| Rank | Strategy | Symbol | TF | Fill | Net PnL | Drawdown | Trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_close | 3470.21568073 | 12695.64968249 | 11 |
| 2 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_close | 4699.30316414 | 12605.05058239 | 11 |
| 3 | mf_orig_1d_stage2_breakout_resistance_full_equity | HYPE | 1d | next_candle_close | 3851.79715571 | 12586.92078268 | 7 |
| 4 | mf_orig_stage_filter_only_full_equity | SOL | 4h | next_candle_close | -6565.49830101 | 10649.53642431 | 80 |
| 5 | mf_orig_stage_filter_only_full_equity | HYPE | 1d | next_candle_open | 7600.86597636 | 10521.76463552 | 11 |
| 6 | mf_orig_stage_filter_only_full_equity | SOL | 4h | next_candle_open | -5686.71704669 | 9921.5018451 | 81 |
| 7 | mf_orig_1d_stage2_5_20_crossover_full_equity | SOL | 4h | next_candle_close | -6071.62377781 | 9866.57524892 | 91 |
| 8 | mf_orig_stage2_pullback_reclaim_full_equity | HYPE | 1d | next_candle_close | 4701.5413525 | 9622.7772438 | 9 |
| 9 | mf_orig_stage2_pullback_reclaim_full_equity | SOL | 4h | next_candle_close | -5750.93604005 | 9550.34162655 | 87 |
| 10 | mf_orig_1d_stage2_5_20_crossover_full_equity | HYPE | 1d | next_candle_open | 11335.34955943 | 9138.21536702 | 11 |

### Worst 10 Hypotheses / Variants By Aggregate Delta

| Rank | Family | Hypothesis | PnL Delta | DD Delta | Candidate Status |
| --- | --- | --- | --- | --- | --- |
| 1 | sor_ev2_true_forward | macd_histogram_above_negative_threshold | -28400.83065884 | 1781.74648658 | deteriorated_vs_baseline |
| 2 | sor_ev2_true_forward | macd_histogram_improving_entry | -28085.24717214 | 1781.74648658 | deteriorated_vs_baseline |
| 3 | sor_ev2_true_forward | lower_rsi_trend_intact_entry | -25834.02207001 | 1153.56227228 | deteriorated_vs_baseline |
| 4 | sor_ev2_true_forward | fixed_stop_loss_pct_1 | -22131.22202431 | 1728.65517153 | deteriorated_vs_baseline |
| 5 | sor_ev3_avoid_sideways_low_volatility | avoid_low_atr_percentile_30 | -12481.40606772 | 1234.04290198 | not_promoted |
| 6 | sor_ev2_true_forward | large_bear_candle_exit | -3598.28775776 | 907.68924658 | deteriorated_vs_baseline |
| 7 | sor_ev2_true_forward | atr_stop_1_5x | -1330.72433027 | 224.70709479 | deteriorated_vs_baseline |
| 8 | sor_ev2_true_forward | fixed_stop_loss_pct_1_5 | -915.96963562 | 1473.11610247 | deteriorated_vs_baseline |
| 9 | sor_ev2_true_forward | recent_low_stop_lookback_5 | -652.11626058 | 73.20255892 | deteriorated_vs_baseline |
| 10 | sor_ev1_loss_anatomy | atr_stop_1_5x | 0 | 0 | insufficient_data |

## Consecutive Loss / Streak Audit

| Rank | Strategy | Symbol | TF | Fill | Losses | Streak PnL | Start | End | Context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mf_orig_stage_filter_only_full_equity | SUI | 15m | next_candle_close | 25 | -1059.36511964 | 2026-04-20T02:00:00+00:00 | 2026-04-28T17:30:00+00:00 | stage_2_markup |
| 2 | mf_orig_stage_filter_only | SUI | 15m | next_candle_close | 25 | -866.10799173 | 2026-04-20T02:00:00+00:00 | 2026-04-28T17:30:00+00:00 | stage_2_markup |
| 3 | money_flow_v1_2 | BTC | 15m | next_candle_open | 24 | -557.25666153 | 2026-04-03T09:00:00+00:00 | 2026-04-07T19:00:00+00:00 | sideways |
| 4 | money_flow_v1_2 | DOGE | 15m | next_candle_open | 23 | -658.80332698 | 2026-04-23T23:45:00+00:00 | 2026-04-26T21:00:00+00:00 | sideways |
| 5 | money_flow_v1_2 | BTC | 15m | next_candle_close | 23 | -657.20789661 | 2026-04-03T09:15:00+00:00 | 2026-04-07T19:15:00+00:00 | sideways |
| 6 | mf_orig_1d_stage2_5_20_crossover | BNB | 15m | next_candle_open | 22 | -482.61398139 | 2026-04-23T20:45:00+00:00 | 2026-04-28T06:45:00+00:00 | stage_2_markup |
| 7 | mf_orig_1d_stage2_5_20_crossover_full_equity | BNB | 15m | next_candle_open | 22 | -482.2401069 | 2026-04-23T20:45:00+00:00 | 2026-04-28T06:45:00+00:00 | stage_2_markup |
| 8 | mf_orig_stage2_pullback_reclaim | BNB | 15m | next_candle_open | 22 | -480.50356591 | 2026-04-23T20:45:00+00:00 | 2026-04-28T06:45:00+00:00 | stage_2_markup |
| 9 | mf_orig_stage2_pullback_reclaim_full_equity | BNB | 15m | next_candle_open | 22 | -480.13132628 | 2026-04-23T20:45:00+00:00 | 2026-04-28T06:45:00+00:00 | stage_2_markup |
| 10 | money_flow_v1_2 | SOL | 4h | next_candle_close | 21 | -6437.02274839 | 2025-01-24T20:00:00+00:00 | 2025-04-10T20:00:00+00:00 | uptrend |
| 11 | money_flow_v1_2 | AVAX | 1h | next_candle_open | 21 | -2110.1699138 | 2025-11-10T11:00:00+00:00 | 2025-11-24T10:00:00+00:00 | sideways |
| 12 | mf_orig_1d_stage2_5_20_crossover_full_equity | BTC | 1h | next_candle_open | 21 | -1201.40616042 | 2026-01-08T18:00:00+00:00 | 2026-02-01T13:00:00+00:00 | stage_2_markup |
| 13 | mf_orig_stage2_pullback_reclaim_full_equity | BTC | 1h | next_candle_open | 21 | -1201.40616042 | 2026-01-08T18:00:00+00:00 | 2026-02-01T13:00:00+00:00 | stage_2_markup |
| 14 | mf_orig_1d_stage2_5_20_crossover | BTC | 1h | next_candle_open | 21 | -889.55579772 | 2026-01-08T18:00:00+00:00 | 2026-02-01T13:00:00+00:00 | stage_2_markup |
| 15 | mf_orig_stage2_pullback_reclaim | BTC | 1h | next_candle_open | 21 | -889.55579772 | 2026-01-08T18:00:00+00:00 | 2026-02-01T13:00:00+00:00 | stage_2_markup |
| 16 | mf_orig_1d_stage2_breakout_resistance_full_equity | AVAX | 15m | next_candle_close | 20 | -1792.71919898 | 2026-04-12T13:00:00+00:00 | 2026-04-26T01:15:00+00:00 | stage_2_markup |
| 17 | mf_orig_1d_stage2_5_20_crossover_full_equity | BTC | 1h | next_candle_close | 20 | -1179.30012731 | 2026-01-08T19:00:00+00:00 | 2026-02-01T15:00:00+00:00 | stage_2_markup |
| 18 | mf_orig_stage2_pullback_reclaim_full_equity | BTC | 1h | next_candle_close | 20 | -1179.30012731 | 2026-01-08T19:00:00+00:00 | 2026-02-01T15:00:00+00:00 | stage_2_markup |
| 19 | mf_orig_1d_stage2_breakout_resistance | AVAX | 15m | next_candle_close | 20 | -1030.92391202 | 2026-04-12T13:00:00+00:00 | 2026-04-26T01:15:00+00:00 | stage_2_markup |
| 20 | mf_orig_1d_stage2_5_20_crossover | BTC | 1h | next_candle_close | 20 | -890.81230952 | 2026-01-08T19:00:00+00:00 | 2026-02-01T15:00:00+00:00 | stage_2_markup |

### Streak Heatmap By Symbol / Timeframe

| Symbol | Timeframe | Streak Count In Worst-20 Set |
| --- | --- | --- |
| BTC | 1h | 7 |
| BNB | 15m | 4 |
| SUI | 15m | 2 |
| BTC | 15m | 2 |
| AVAX | 15m | 2 |
| DOGE | 15m | 1 |
| SOL | 4h | 1 |
| AVAX | 1h | 1 |

### Streak Reason Attribution

| Context | Streak Count |
| --- | --- |
| stage_2_markup | 15 |
| sideways | 4 |
| uptrend | 1 |

## Regime / Stage / Condition Attribution

| Family | Stage / Regime | Trades | Wins | Losses | Net PnL | Largest Loss |
| --- | --- | --- | --- | --- | --- | --- |
| mf_orig | stage_2_markup | 51098 | 13294 | 37804 | -652209.33667711 | -3498.12580096 |
| current_money_flow | sideways | 6377 | 1614 | 4763 | -76684.63835351 | -1082.24863266 |
| current_money_flow | uptrend | 4317 | 1293 | 3024 | -61365.79606943 | -2888.16856889 |
| current_money_flow | downtrend | 153 | 44 | 109 | 1744.59715738 | -1754.81223448 |

## Control Pocket Audit

| Phase | Variant / Hypothesis | Pocket | Improved | Preserved | Damaged |
| --- | --- | --- | --- | --- | --- |
| SOR-EV1 | atr_stop_1_5x | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | atr_stop_2x | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | avoid_macd_flat_chop | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | avoid_sideways_low_volatility | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | fixed_stop_loss_pct_1 | control_pockets | 6 | 0 | 9 |
| SOR-EV1 | fixed_stop_loss_pct_1_5 | control_pockets | 5 | 0 | 10 |
| SOR-EV1 | fixed_stop_loss_pct_2 | control_pockets | 9 | 0 | 6 |
| SOR-EV1 | large_bear_candle_exit | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | lower_rsi_trend_intact_entry | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | macd_histogram_above_negative_threshold | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | macd_histogram_improving_entry | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | recent_low_stop_lookback_10 | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | recent_low_stop_lookback_5 | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | reject_entry_if_price_too_far_above_ema10 | control_pockets | 0 | 15 | 0 |
| SOR-EV1 | reject_entry_if_price_too_far_above_sma20 | control_pockets | 0 | 15 | 0 |
| SOR-EV2 | atr_stop_1_5x | control_pockets | 3 | 9 | 3 |
| SOR-EV2 | atr_stop_2x | control_pockets | 2 | 12 | 1 |
| SOR-EV2 | avoid_macd_flat_chop | control_pockets | 4 | 8 | 3 |
| SOR-EV2 | avoid_sideways_low_volatility | control_pockets | 4 | 11 | 0 |
| SOR-EV2 | fixed_stop_loss_pct_1 | control_pockets | 4 | 0 | 11 |
| SOR-EV2 | fixed_stop_loss_pct_1_5 | control_pockets | 5 | 0 | 10 |
| SOR-EV2 | fixed_stop_loss_pct_2 | control_pockets | 4 | 2 | 9 |
| SOR-EV2 | large_bear_candle_exit | control_pockets | 4 | 2 | 9 |
| SOR-EV2 | lower_rsi_trend_intact_entry | control_pockets | 5 | 4 | 6 |
| SOR-EV2 | macd_histogram_above_negative_threshold | control_pockets | 4 | 3 | 8 |
| SOR-EV2 | macd_histogram_improving_entry | control_pockets | 5 | 4 | 6 |
| SOR-EV2 | recent_low_stop_lookback_10 | control_pockets | 0 | 15 | 0 |
| SOR-EV2 | recent_low_stop_lookback_5 | control_pockets | 1 | 13 | 1 |
| SOR-EV2 | reject_entry_if_price_too_far_above_ema10 | control_pockets | 8 | 2 | 5 |
| SOR-EV2 | reject_entry_if_price_too_far_above_sma20 | control_pockets | 9 | 2 | 4 |
| SOR-EV3 | avoid_flat_ema10_slope | control_pockets | 3 | 4 | 8 |
| SOR-EV3 | avoid_flat_sma20_slope | control_pockets | 1 | 2 | 12 |
| SOR-EV3 | avoid_low_atr_percentile_20 | control_pockets | 5 | 0 | 10 |
| SOR-EV3 | avoid_low_atr_percentile_30 | control_pockets | 4 | 0 | 11 |
| SOR-EV3 | avoid_low_rolling_range_20 | control_pockets | 0 | 13 | 2 |
| SOR-EV3 | avoid_low_rolling_range_50 | control_pockets | 2 | 11 | 2 |
| SOR-EV3 | avoid_macd_flat_chop | control_pockets | 0 | 15 | 0 |
| SOR-EV3 | avoid_sideways_low_volatility_conservative | control_pockets | 2 | 2 | 11 |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_5_20_crossover | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_5_20_crossover | positive 1d pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_5_20_crossover | all_1d_pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_breakout_resistance | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_breakout_resistance | positive 1d pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_1d_stage2_breakout_resistance | all_1d_pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage2_pullback_reclaim | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage2_pullback_reclaim | positive 1d pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage2_pullback_reclaim | all_1d_pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage_filter_only | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage_filter_only | positive 1d pockets | None | None | None |
| MF-ORIG-EV1.1 | mf_orig_stage_filter_only | all_1d_pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover | positive 1d pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover | all_1d_pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover_full_equity | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover_full_equity | positive 1d pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_5_20_crossover_full_equity | all_1d_pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_breakout_resistance | ETH 1h current baseline | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_breakout_resistance | positive 1d pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_breakout_resistance | all_1d_pockets | None | None | None |
| MF-ORIG-EV2 | mf_orig_1d_stage2_breakout_resistance_full_equity | ETH 1h current baseline | None | None | None |

Control-pocket damage is the central reason that high aggregate-PnL variants are not clean candidates. `avoid_low_rolling_range_50` and MF-ORIG full-equity rows are useful review lanes, but they are not promoted because drawdown or control-pocket preservation fails.

## P0 / P1 / P2 / P3 Issue List

| Severity | Issue | Why It Matters | Required Fix | Blocks |
| --- | --- | --- | --- | --- |
| P1 | backtest_missing_execution_microstructure | Current evidence uses candle-level fills, fees, slippage, and force-close conventions but does not model order-book queues, partial fills, funding, liquidation, latency, exchange rejections, or outage behavior. | Run PT-RT1 public-mainnet real-time paper observation plus later execution-quality simulation before any production or live decision. | blocks production rule change and live/paper-runtime approval; does not block visual review or hypothesis filtering |
| P1 | no_strategy_candidate_has_clean_control_pocket_preservation | Several variants improve aggregate PnL but damage strong baseline pockets, especially positive 1d controls or ETH 1h depending on sizing mode. | Require sliced/out-of-sample-style review and control-pocket preservation before proposing any rule change. | blocks candidate promotion |
| P2 | fifteen_minute_and_one_hour_public_window_limited | Hyperliquid public candleSnapshot exposes a recent 5000-candle window, so 15m/1h evidence does not reach Jan 2025. | Use vendor/archive data or ongoing real-time collection for longer 15m/1h history. | does not block visual review; limits confidence for short timeframe conclusions |
| P2 | original_pdf_not_available_to_agent | MF-ORIG source authority still depends on prompt-provided source summary, not direct PDF extraction. | Attach or point to the PDF and reconcile subjective source rules before source-authority claims. | blocks source-faithfulness claims; does not block evidence-only replay review |
| P2 | dashboard_date_filters_are_display_only | Date-filter recalculations are useful for review but are not canonical evidence-pack regeneration. | Use backend Strategy Validation regeneration for arbitrary date-window canonical claims. | blocks treating filtered dashboard numbers as canonical |
| P3 | exact_sor_variant_trade_level_top_winner_streak_detail_incomplete | SOR summaries provide scenario-level variant metrics and attribution, but not a full committed per-trade ledger for every variant. | If a SOR variant advances to deeper review, export compact per-trade ledgers for that variant. | does not block current audit verdict |

Issue counts: `{'P0': 0, 'P1': 2, 'P2': 3, 'P3': 1}`.

## Backtest Adequacy Decision

Decision: `good_enough_for_visual_review_and_hypothesis_filtering_only`.

- The backtest can support visual review, loss anatomy, hypothesis filtering, and scoped next-phase planning.
- The backtest cannot support production rule changes, live trading, real-capital decisions, or strategy paper-runtime authorization.
- Current conclusions are fragile where aggregate PnL improves while control pockets or worst drawdown worsen.

## Real-Time Paper Observation Readiness

Decision: `paper_observation_ready_with_conditions`.

This is not paper approval. It means a separately scoped public-mainnet observation phase is reasonable if the listed conditions are met.

- trusted public mainnet candle feed, not Hyperliquid testnet prices, must drive strategy truth
- candle close detection and duplicate signal prevention must be implemented
- paper ledger must separate simulated paper positions from sandbox execution plumbing
- founder review workflow and kill-switch/runbook must exist before continuous operation
- no live orders, no private/signed/order endpoints, and no paper/live strategy approval in EV-AUDIT1

## Dashboard Integration

Status: `audit_review_dashboard_deferred`.

EV-AUDIT1 prioritizes founder-readable audit report and JSON; dashboard Audit Review can load this JSON in a later UI phase.

## Recommended Next Phase

`PT-RT1 - Real-Time Public Market Data + Paper Observation Runtime`.

PT-RT1 should use trusted public mainnet candles for strategy truth, keep sandbox/testnet execution plumbing separate, maintain the internal 10,000 USDC paper-equity ledger, log every signal/state transition, prevent duplicate signals, expose drawdown alarms, and remain no-live/no-order unless a later phase explicitly scopes otherwise.

## Boundary Confirmation

| Boundary | Value |
| --- | --- |
| changes_production_money_flow_rules | False |
| approves_strategy_for_production | False |
| approves_paper_trading | False |
| approves_live_trading | False |
| submits_orders | False |
| calls_private_signed_or_order_endpoints | False |
| uses_hyperliquid_testnet_prices_as_strategy_truth | False |
| uses_dashboard_date_filters_as_canonical_evidence | False |
| regenerates_evidence_packs | False |
