# MF-ORIG-EV1.1 Original Money Flow Reconstruction Accounting Hotpatch

## Executive Summary

MF-ORIG-EV1.1 hotpatches MF-ORIG-EV1 accounting and drawdown truth, regenerates the original Money Flow reconstruction reports, and compares the corrected evidence with canonical Money Flow v1.2 SV2.0.2 evidence. Pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions were quarantined until this regeneration. Production Money Flow rules are unchanged. No orders are submitted. No private/signed/order endpoints are called.

## Hotpatch Accounting Convention

- Accounting model: `event_ledger_accounting`.
- Entry fees are counted exactly once as `entry_fee` accounting events.
- Trim realized PnL is counted exactly once as `trim_close` accounting events.
- Final close events close only remaining quantity and do not re-add prior trim PnL.
- Trade `net_pnl` is the sum of accounting-event `net_amount` values.
- `equity_after_trade - equity_before_trade == net_pnl` for generated trades.
- Drawdown method: `peak_to_trough`.
- Candidate gate drawdown metric: `mark_to_market_max_drawdown`.

## Source Limitation

The PDF file was not present in the repository or common local Downloads/Documents search paths during MF-ORIG-EV1, so source extraction is limited to the prompt-supplied source summary.

## Hypotheses

- `mf_orig_1d_stage2_5_20_crossover`
- `mf_orig_1d_stage2_breakout_resistance`
- `mf_orig_stage2_pullback_reclaim`
- `mf_orig_stage_filter_only`

## Data Source

- Canonical baseline: `SV2.0.2 DB-imported Money Flow v1.2 evidence packs`
- Canonical timestamp: `20260512T064916Z`
- Strategy truth: DB-imported Hyperliquid public mainnet candles from SV2.0.2 pack requests.
- Hyperliquid testnet prices are not used as strategy truth.

## Baseline Parity

- Status counts: `{'baseline_parity_passed': 54}`

## Hypothesis Summary

| Hypothesis | Scenarios | 1D Scenarios | PnL Delta vs v1.2 | Worst Drawdown Delta | Trades | Performance Label | Candidate Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `mf_orig_1d_stage2_5_20_crossover` | 54 | 18 | 68916.55235178 | -349.29468305 | 4748 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_1d_stage2_breakout_resistance` | 54 | 18 | 69438.32917799 | -1281.40684308 | 2160 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_stage2_pullback_reclaim` | 54 | 18 | 68828.67772013 | -349.29468305 | 4702 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_stage_filter_only` | 54 | 18 | 73030.34302538 | -977.10968817 | 3949 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |

## Source Gap Summary

| Source Rule | Current v1.2 Drift | Evidence Implication |
| --- | --- | --- |
| Stage/20SMA/5EMA trigger hierarchy comes first. | Current v1.2 is Money Flow-inspired but not source-faithful; it treats RSI/MACD as entry gates rather than secondary warning/confirmation context. | MF-ORIG-EV1 must compare a 1d-first stage/crossover system against v1.2, not overwrite v1.2. |
| RSI > 70 is profit-warning/profit-taking context. | RSI has moved from warning context to entry filter. | Original hypotheses should not reject entries solely because RSI is below a v1.2 sleeve floor. |
| Full exit is 5 EMA crossing/closing below 20 SMA or price close below 20 SMA. | Current exits can be more MACD-sensitive than the source hierarchy. | Original replay must separate full exits from profit-warning trims. |
| Stops are placed around support/resistance or pivots and risk is sized from stop distance. | Current evidence does not model source-style structure stops or 1% risk sizing. | MF-ORIG-EV1 should test risk-budget sizing and prior support/pivot stops explicitly. |

## 1D Primary Evidence

- `1d` rows: `72` across `4` hypotheses.
| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |
| --- | ---: | ---: | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | 18 | 1447.82788804 | -21479.11068129 | 237 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -271.30452633 | -23198.24309566 | 118 |
| `mf_orig_stage2_pullback_reclaim` | 18 | 1805.7498545 | -21121.18871483 | 219 |
| `mf_orig_stage_filter_only` | 18 | 1333.28998108 | -21593.64858825 | 214 |

## 4h / 1h Exploratory Evidence

- `4h` rows: `72` across `4` hypotheses.
| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |
| --- | ---: | ---: | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | 18 | 3946.33754851 | 42606.44294647 | 1652 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -1421.15154186 | 37238.9538561 | 749 |
| `mf_orig_stage2_pullback_reclaim` | 18 | 3571.20367796 | 42231.30907592 | 1622 |
| `mf_orig_stage_filter_only` | 18 | 3877.47637683 | 42537.58177479 | 1378 |
- `1h` rows: `72` across `4` hypotheses.
| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |
| --- | ---: | ---: | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | 18 | -17653.46562133 | 47789.2200866 | 2859 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -10045.06729038 | 55397.61841755 | 1293 |
| `mf_orig_stage2_pullback_reclaim` | 18 | -17724.12834889 | 47718.55735904 | 2861 |
| `mf_orig_stage_filter_only` | 18 | -13356.27586909 | 52086.40983884 | 2357 |

## Source-Rule Modeling Findings

- Stage-filtering is modeled deterministically from current/prior candles only; subjective accumulation/distribution language is proxied with whipsaw/range and MA/RSI/MACD context.
- RSI is used as profit-warning / trim context, not the same narrow v1.2 entry sleeve.
- TSI is deferred; MACD is used as the substitute because the source summary allows MACD as confirmation/warning.
- Stops use prior support / confirmed-pivot proxies available before entry; this is a simple structure model and not hand-drawn supply/demand analysis.
- Sizing uses 1% risk budget from current realized equity, entry-to-stop distance, and a current-equity notional cap.

## Accounting Invariant Audit

- Status: `passed`
- Trades checked: `15559`
- Equity-delta violations: `0`
- Fee-sum violations: `0`
- Remaining-quantity violations: `0`
- Entry-fee event violations: `0`

## Comparison Versus Current Money Flow v1.2

- PnL and drawdown deltas are compared against matching canonical SV2.0.2 Money Flow v1.2 independent scenarios.
- Independent scenario deltas are descriptive sums, not one combined account.
- Pre-gate aggregate improvement is not enough for candidate status when control pockets are damaged.
- The candidate gate was re-run after MF-ORIG-EV1.1 accounting and drawdown corrections.
- Candidate conclusions did not change after the correction: all original hypotheses remain `source_faithful_but_underperformed` because baseline-positive 1d control pockets were not preserved.

## Candidate Gate

| Hypothesis | Status | Gate Blockers |
| --- | --- | --- |
| `mf_orig_1d_stage2_5_20_crossover` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_1d_stage2_breakout_resistance` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_stage2_pullback_reclaim` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |
| `mf_orig_stage_filter_only` | `source_faithful_but_underperformed` | `control_pocket_not_preserved` |

## Stop / Risk Sizing

- Risk per trade: 1% or less of current realized equity.
- Position size: risk budget divided by entry-to-stop distance.
- Notional cap: current realized equity.
- Stop model: prior support/pivot proxy available before entry; no arbitrary fixed-percent primary stop.

## Control Pocket Label Fix

- `positive 1d pockets` now filters to baseline-positive 1d scenarios only.
- `all_1d_pockets` is reported separately as context and does not imply positivity.

## Limitations

- `dashboard_date_filters_are_display_only_not_canonical_evidence`
- `exit_signal_skipped_no_fill_candle_for_next_candle_close`
- `exit_signal_skipped_no_fill_candle_for_next_candle_open`
- `independent_scenarios_are_not_one_combined_account`
- `open_positions_are_force_closed_at_dataset_end`
- `open_signal_skipped_no_fill_candle_for_next_candle_close`
- `open_signal_skipped_no_fill_candle_for_next_candle_open`
- `source_pdf_not_available_to_agent_prompt_summary_used`
- `support_resistance_modeled_with_simple_prior_support_low_proxy`
- `tsi_deferred_macd_used_as_substitute`

## Boundary Confirmation

- MF-ORIG-EV1.1 is evidence-only.
- Current Money Flow v1.2 remains unchanged.
- Original Money Flow is not approved for production.
- Live trading is not approved.
- No orders were submitted.
- No private/signed/order endpoints were called.
- Dashboard date-filter recalculations are not canonical evidence.

## Recommended Next Phase

`MF-ORIG-EV2` should only proceed if the founder wants dashboard overlays and deeper source-rule refinement after reviewing this first reconstruction.
