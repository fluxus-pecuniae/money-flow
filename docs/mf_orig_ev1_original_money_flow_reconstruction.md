# MF-ORIG-EV1 Original Money Flow Reconstruction

## Executive Summary

MF-ORIG-EV1 reconstructs the original Money Flow source hierarchy as an evidence-only Strategy Validation replay family and compares it with canonical Money Flow v1.2 SV2.0.2 evidence. Production Money Flow rules are unchanged. No orders are submitted. No private/signed/order endpoints are called.

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
| `mf_orig_1d_stage2_5_20_crossover` | 54 | 18 | 64649.38000426 | -247.70546258 | 4748 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_1d_stage2_breakout_resistance` | 54 | 18 | 68784.26659877 | -1505.67716745 | 2160 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_stage2_pullback_reclaim` | 54 | 18 | 64551.3733128 | -247.70546258 | 4702 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |
| `mf_orig_stage_filter_only` | 54 | 18 | 70547.38205021 | -897.89820688 | 3949 | `improved_pnl_drawdown_pre_gate` | `source_faithful_but_underperformed` |

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
| `mf_orig_1d_stage2_5_20_crossover` | 18 | 1449.29821307 | -21477.64035626 | 237 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -216.98088761 | -23143.91945694 | 118 |
| `mf_orig_stage2_pullback_reclaim` | 18 | 1812.65385952 | -21114.28470981 | 219 |
| `mf_orig_stage_filter_only` | 18 | 1357.65103563 | -21569.2875337 | 214 |

## 4h / 1h Exploratory Evidence

- `4h` rows: `72` across `4` hypotheses.
| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |
| --- | ---: | ---: | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | 18 | 3241.47688314 | 41901.5822811 | 1652 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -1642.3131035 | 37017.79229446 | 749 |
| `mf_orig_stage2_pullback_reclaim` | 18 | 2858.34716125 | 41518.45255921 | 1622 |
| `mf_orig_stage_filter_only` | 18 | 3393.0106881 | 42053.11608606 | 1378 |
- `1h` rows: `72` across `4` hypotheses.
| Hypothesis | Rows | Net PnL Sum | Delta vs v1.2 | Trades |
| --- | ---: | ---: | ---: | ---: |
| `mf_orig_1d_stage2_5_20_crossover` | 18 | -21217.24762851 | 44225.43807942 | 2859 |
| `mf_orig_1d_stage2_breakout_resistance` | 18 | -10532.29194668 | 54910.39376125 | 1293 |
| `mf_orig_stage2_pullback_reclaim` | 18 | -21295.48024453 | 44147.2054634 | 2861 |
| `mf_orig_stage_filter_only` | 18 | -15379.13221008 | 50063.55349785 | 2357 |

## Source-Rule Modeling Findings

- Stage-filtering is modeled deterministically from current/prior candles only; subjective accumulation/distribution language is proxied with whipsaw/range and MA/RSI/MACD context.
- RSI is used as profit-warning / trim context, not the same narrow v1.2 entry sleeve.
- TSI is deferred; MACD is used as the substitute because the source summary allows MACD as confirmation/warning.
- Stops use prior support / confirmed-pivot proxies available before entry; this is a simple structure model and not hand-drawn supply/demand analysis.
- Sizing uses 1% risk budget from current realized equity, entry-to-stop distance, and a current-equity notional cap.

## Comparison Versus Current Money Flow v1.2

- PnL and drawdown deltas are compared against matching canonical SV2.0.2 Money Flow v1.2 independent scenarios.
- Independent scenario deltas are descriptive sums, not one combined account.
- Pre-gate aggregate improvement is not enough for candidate status when control pockets are damaged.

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

- MF-ORIG-EV1 is evidence-only.
- Current Money Flow v1.2 remains unchanged.
- Original Money Flow is not approved for production.
- Live trading is not approved.
- No orders were submitted.
- No private/signed/order endpoints were called.
- Dashboard date-filter recalculations are not canonical evidence.

## Recommended Next Phase

`MF-ORIG-EV2` should only proceed if the founder wants dashboard overlays and deeper source-rule refinement after reviewing this first reconstruction.
