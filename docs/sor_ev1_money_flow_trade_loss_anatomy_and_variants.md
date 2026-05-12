# SOR-EV1 Money Flow Trade Loss Anatomy And Evidence-Only Variants

Recorded at: `2026-05-12T10:08:46Z`

Status: `evidence_only_loss_anatomy_ready_for_founder_review`

SOR-EV1 is evidence-only research. It uses only the canonical SV2.0.2 DB-imported evidence packs as baseline truth. Production Money Flow rules are unchanged, no order endpoints are called, and no stop-loss or entry variant is approved.

## Executive Summary

- Baseline source: `SV2.0.2 canonical DB-imported evidence packs` at `20260512T064916Z`.
- Canonical pack paths inspected: `36`.
- Baseline scenarios: `72` independent runs, not one combined account.
- Baseline trades: `10847`; losing trades: `7896`.
- Worst observed trade: `SUI 1d next_candle_close -2888.16856889`.
- Fixed-stop diagnostics reduced some completed-trade losses in overlay estimates, but these are not true-forward replay results and are not production candidates.
- RSI/MACD rejected-entry admission remains deferred for true replay because the canonical packs do not contain full rejected-candle indicator traces.

## Canonical SV2.0.2 Baseline Reference

Allowed baseline: canonical SV2.0.2 evidence packs only.

Forbidden inputs excluded: `sv1_13_dynamic_equity_packs`, `compact_sv2_rows`, `pt0_0_3_aggregated_historical_replay`, `dashboard_chart_data_json`, `dashboard_date_filter_fresh_10k`, `hyperliquid_testnet_prices`

## Dataset / Evidence-Pack Source

| Field | Value |
|---|---|
| Timestamp | `20260512T064916Z` |
| Symbols | `BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX` |
| Timeframes | `15m, 1h, 4h, 1d` |
| Capital mode | `dynamic_equity_pct` |
| Initial equity | `10000` per independent scenario |

## Biggest Loss Anatomy

| Rank | Symbol | TF | Fill | Entry | Exit | Bars | Entry | Exit Price | Net PnL | MAE | MFE | Entry Class | Exit Reason |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | SUI | 1d | `next_candle_close` | 2025-10-10T00:00:00+00:00 | 2025-10-12T00:00:00+00:00 | 2 | 3.40832219 | 2.54093749 | -2888.16856889 | -9375.93631338 | 239.58583946 | `late_extension_entry` | `ma_alignment_break` |
| 2 | DOGE | 1d | `next_candle_close` | 2025-10-10T00:00:00+00:00 | 2025-10-12T00:00:00+00:00 | 2 | 0.24869459 | 0.18506446 | -2757.8302426 | -7064.65234135 | 243.61614873 | `late_extension_entry` | `ma_alignment_break` |
| 3 | HYPE | 1d | `next_candle_open` | 2025-05-28T00:00:00+00:00 | 2025-05-30T00:00:00+00:00 | 2 | 35.7827316 | 31.3845818 | -2622.62099832 | -2639.94041785 | 358.02823421 | `late_extension_entry` | `ma_alignment_break` |
| 4 | ETH | 1d | `next_candle_close` | 2025-10-06T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | 5 | 4517.55486 | 3821.15331 | -2183.61746845 | -3974.06209143 | 752.42242264 | `late_extension_entry` | `ma_alignment_break` |
| 5 | HYPE | 1d | `next_candle_close` | 2026-01-07T00:00:00+00:00 | 2026-01-10T00:00:00+00:00 | 3 | 28.2494723 | 25.0464838 | -2119.1224135 | -2185.63197665 | 91.20469671 | `late_extension_entry` | `ma_alignment_break` |
| 6 | XRP | 4h | `next_candle_open` | 2025-03-03T08:00:00+00:00 | 2025-03-03T20:00:00+00:00 | 3 | 2.68900646 | 2.34749554 | -2058.79583042 | -2065.80249749 | 178.33405106 | `late_extension_entry` | `ma_alignment_break` |
| 7 | ETH | 1d | `next_candle_close` | 2025-08-13T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | 7 | 4594.17784 | 4072.47789 | -1875.48247407 | -1878.5726249 | 729.11008122 | `late_extension_entry` | `ma_alignment_break` |
| 8 | SUI | 1d | `next_candle_open` | 2025-02-23T00:00:00+00:00 | 2025-02-25T00:00:00+00:00 | 2 | 3.42372681 | 2.82605193 | -1754.81223448 | -1833.96641977 | 190.14367563 | `late_extension_entry` | `ma_alignment_break` |
| 9 | HYPE | 1d | `next_candle_close` | 2025-08-13T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | 7 | 44.8194418 | 41.2856106 | -1592.33862305 | -1728.61388476 | 2129.7164112 | `late_extension_entry` | `ma_alignment_break` |
| 10 | HYPE | 1d | `next_candle_close` | 2026-04-14T00:00:00+00:00 | 2026-04-21T00:00:00+00:00 | 7 | 44.3523017 | 40.6927885 | -1590.57090634 | -1649.41727468 | 611.81823369 | `late_extension_entry` | `ma_alignment_break` |
| 11 | HYPE | 1d | `next_candle_close` | 2025-07-16T00:00:00+00:00 | 2025-07-20T00:00:00+00:00 | 4 | 47.894364 | 44.4816515 | -1553.12140604 | -2236.57711638 | 315.66225915 | `late_extension_entry` | `ma_alignment_break` |
| 12 | XRP | 4h | `next_candle_close` | 2025-03-03T12:00:00+00:00 | 2025-03-04T00:00:00+00:00 | 3 | 2.6347902 | 2.38378465 | -1525.60939771 | -2045.46068998 | 505.49778746 | `late_extension_entry` | `ma_alignment_break` |
| 13 | BNB | 4h | `next_candle_close` | 2025-10-13T08:00:00+00:00 | 2025-10-14T12:00:00+00:00 | 7 | 1342.90275 | 1169.44906 | -1493.50259315 | -1549.83817735 | 277.82537652 | `late_extension_entry` | `ma_alignment_break` |
| 14 | HYPE | 1d | `next_candle_close` | 2025-06-14T00:00:00+00:00 | 2025-06-19T00:00:00+00:00 | 5 | 42.31269 | 39.448162 | -1475.11738828 | -2401.48861143 | 1799.33945854 | `late_extension_entry` | `macd_rollover` |
| 15 | DOGE | 4h | `next_candle_close` | 2025-08-13T20:00:00+00:00 | 2025-08-14T16:00:00+00:00 | 5 | 0.24414322 | 0.22536237 | -1402.44339908 | -2009.01115797 | 887.23950919 | `late_extension_entry` | `ma_alignment_break` |
| 16 | SOL | 1d | `next_candle_close` | 2025-10-08T00:00:00+00:00 | 2025-10-11T00:00:00+00:00 | 3 | 220.136021 | 187.473741 | -1375.59829835 | -3455.51944881 | 412.68679464 | `late_extension_entry` | `ma_alignment_break` |
| 17 | DOGE | 1d | `next_candle_close` | 2025-08-17T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | 3 | 0.23119934 | 0.2092772 | -1348.19337629 | -1369.96805838 | 703.85914466 | `late_extension_entry` | `ma_alignment_break` |
| 18 | AVAX | 4h | `next_candle_close` | 2025-03-02T20:00:00+00:00 | 2025-03-03T20:00:00+00:00 | 6 | 24.70741 | 20.923721 | -1309.28287787 | -1303.60597807 | 148.24648458 | `late_extension_entry` | `ma_alignment_break` |
| 19 | AVAX | 1d | `next_candle_close` | 2025-08-18T00:00:00+00:00 | 2025-08-20T00:00:00+00:00 | 2 | 25.0805219 | 22.3362971 | -1300.60139409 | -1307.2111227 | 115.59091883 | `late_extension_entry` | `ma_alignment_break` |
| 20 | BTC | 1d | `next_candle_close` | 2025-10-06T00:00:00+00:00 | 2025-10-12T00:00:00+00:00 | 6 | 123607.071 | 110558.8224 | -1267.1564935 | -2188.03973637 | 262.47236885 | `late_extension_entry` | `ma_alignment_break` |

## Large Red Candle / Adverse Move Analysis

Exact red-candle attribution is limited because canonical SV2.0.2 batch reports do not embed full candle payloads. SOR-EV1 therefore uses completed-trade MAE as reporting-only adverse-move attribution and labels exact candle attribution as deferred unless a replay/candle trace is added.

| Class | Count |
|---|---:|
| `adverse_move_not_stop_solvable` | 5563 |
| `exact_red_candle_classification_deferred` | 7896 |
| `losses_from_large_down_candles` | 877 |
| `stop_would_have_helped` | 1456 |

## Late-Entry Analysis

| Classification | Losing Trades |
|---|---:|
| `chop_entry` | 4763 |
| `continuation_entry` | 1747 |
| `late_extension_entry` | 1342 |
| `unknown` | 44 |

## RSI / MACD Rejection Analysis

Status: `deferred_requires_rejected_signal_replay`.

| Rejection Reason | Count |
|---|---:|
| `entry_quality_not_constructive` | 2285 |
| `macd_not_constructive` | 11601 |
| `other` | 137531 |
| `rsi_not_constructive` | 12226 |

## Variant Comparison Tables

| Variant | Methodology | Outcome | Scenarios | Net PnL Delta Sum | Max DD Delta | Stop Exits | Avoided Losers | Missed Winners |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `atr_stop_1_5x` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `atr_stop_2x` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `avoid_macd_flat_chop` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `avoid_sideways_low_volatility` | `completed_trade_overlay_estimate` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `fixed_stop_loss_pct_1` | `completed_trade_overlay_estimate` | `deteriorated_vs_baseline` | 72 | 12772.36098593 | 4094.73445914 | 3719 | 2250 | 449 |
| `fixed_stop_loss_pct_1_5` | `completed_trade_overlay_estimate` | `overfit_risk` | 72 | 17055.45398882 | 4925.15766316 | 2560 | 1488 | 227 |
| `fixed_stop_loss_pct_2` | `completed_trade_overlay_estimate` | `overfit_risk` | 72 | 9900.39603028 | 2622.79044822 | 1783 | 1021 | 121 |
| `large_bear_candle_exit` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `lower_rsi_trend_intact_entry` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `macd_histogram_above_negative_threshold` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `macd_histogram_improving_entry` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `recent_low_stop_lookback_10` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `recent_low_stop_lookback_5` | `deferred_requires_rejected_signal_replay` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `reject_entry_if_price_too_far_above_ema10` | `completed_trade_overlay_estimate` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |
| `reject_entry_if_price_too_far_above_sma20` | `completed_trade_overlay_estimate` | `insufficient_data` | 72 | 0 | 0 | 0 | 0 | 0 |

## Stop-Loss Evidence

Fixed stops are completed-trade overlay estimates based on reported MAE. They can identify whether a stop might have capped an already observed loss, but they do not model changed position occupancy, later trades, intrabar fill quality, or exact stop execution.

## Extension-Filter Evidence

Extension-filter variants are marked `insufficient_data` because the canonical packs do not carry complete EMA10/SMA20 extension traces for every entry. They should be replayed with per-candle contexts before candidate review.

## Control-Pocket Section

Control pockets are positive baseline scenarios, including ETH 1h where present. A variant that helps weak sleeves but damages these controls is not a clean improvement.

| Variant | Control Pockets | Improved | Preserved | Damaged |
|---|---:|---:|---:|---:|
| `atr_stop_1_5x` | 15 | 0 | 15 | 0 |
| `atr_stop_2x` | 15 | 0 | 15 | 0 |
| `avoid_macd_flat_chop` | 15 | 0 | 15 | 0 |
| `avoid_sideways_low_volatility` | 15 | 0 | 15 | 0 |
| `fixed_stop_loss_pct_1` | 15 | 6 | 0 | 9 |
| `fixed_stop_loss_pct_1_5` | 15 | 5 | 0 | 10 |
| `fixed_stop_loss_pct_2` | 15 | 9 | 0 | 6 |
| `large_bear_candle_exit` | 15 | 0 | 15 | 0 |
| `lower_rsi_trend_intact_entry` | 15 | 0 | 15 | 0 |
| `macd_histogram_above_negative_threshold` | 15 | 0 | 15 | 0 |
| `macd_histogram_improving_entry` | 15 | 0 | 15 | 0 |
| `recent_low_stop_lookback_10` | 15 | 0 | 15 | 0 |
| `recent_low_stop_lookback_5` | 15 | 0 | 15 | 0 |
| `reject_entry_if_price_too_far_above_ema10` | 15 | 0 | 15 | 0 |
| `reject_entry_if_price_too_far_above_sma20` | 15 | 0 | 15 | 0 |

## Symbol Comparison

| Symbol | Scenarios | Trades | Net PnL Sum | Positive Scenarios | Worst Drawdown |
|---|---:|---:|---:|---:|---:|
| `AVAX` | 8 | 1173 | -20436.45922238 | 1 | 7839.22806739 |
| `BNB` | 8 | 1307 | -17584.79732369 | 1 | 4969.63628919 |
| `BTC` | 8 | 1230 | -16473.24999026 | 0 | 4828.21197273 |
| `DOGE` | 8 | 1207 | -13769.76758822 | 2 | 11416.82897622 |
| `ETH` | 8 | 1193 | -12094.67792029 | 2 | 6284.26927592 |
| `HYPE` | 8 | 1217 | 1442.51115315 | 3 | 7784.03776696 |
| `SOL` | 8 | 1202 | -25999.86984874 | 0 | 8390.24466783 |
| `SUI` | 8 | 1178 | -27753.02491588 | 0 | 10867.52793936 |
| `XRP` | 8 | 1140 | -3636.50160925 | 4 | 6096.09612774 |

## Timeframe Comparison

| Timeframe | Scenarios | Trades | Net PnL Sum | Positive Scenarios | Worst Drawdown |
|---|---:|---:|---:|---:|---:|
| `15m` | 18 | 4019 | -55129.984729 | 0 | 4425.93517999 |
| `1d` | 18 | 374 | 22926.93856933 | 8 | 11416.82897622 |
| `1h` | 18 | 3950 | -65442.68570793 | 0 | 5608.75490253 |
| `4h` | 18 | 2504 | -38660.10539796 | 5 | 8390.24466783 |

## Candidate Variants

- None promoted from SOR-EV1. No overlay-only result is treated as candidate evidence.

## Rejected / Deferred Variants

- `atr_stop_1_5x`
- `atr_stop_2x`
- `avoid_macd_flat_chop`
- `avoid_sideways_low_volatility`
- `fixed_stop_loss_pct_1`
- `fixed_stop_loss_pct_1_5`
- `fixed_stop_loss_pct_2`
- `large_bear_candle_exit`
- `lower_rsi_trend_intact_entry`
- `macd_histogram_above_negative_threshold`
- `macd_histogram_improving_entry`
- `recent_low_stop_lookback_10`
- `recent_low_stop_lookback_5`
- `reject_entry_if_price_too_far_above_ema10`
- `reject_entry_if_price_too_far_above_sma20`

## Methodology Labels

- `true_forward_replay`: Chronological replay that can be considered candidate evidence if baseline parity and controls hold.
- `completed_trade_overlay_estimate`: Diagnostic adjustment to completed baseline trades; useful for hypothesis triage, not rule approval.
- `lookahead_diagnostic_proxy`: Uses information unavailable at decision time; never candidate evidence.
- `reporting_only_attribution`: Explains observed baseline trades without changing decisions.
- `deferred_requires_rejected_signal_replay`: Needs per-candle rejected-signal replay before truthful testing.

## Limitations

- `canonical_sv2_0_2_packs_do_not_include_full_per_candle_indicator_trace`
- `stop_variants_are_completed_trade_overlay_estimates_not_true_forward_replay`
- `rsi_macd_rejection_analysis_uses_pack_no_trade_counts_and_is_deferred_for_true_replay`
- `large_red_candle_attribution_requires_candle_payload_or_replay_context_for_exact_classification`
- `independent_scenarios_are_not_one_combined_account`
- `no_variant_is_approved_for_production_paper_or_live_trading`

## Recommended Next Evidence Phase

Run a true-forward SOR-EV2 replay for the most promising stop logic using per-candle DB candles and position occupancy, then separately replay rejected-signal entry variants with explicit RSI/MACD contexts. Do not change production rules until a true-forward replay preserves control pockets and improves loss behavior under both `next_candle_open` and `next_candle_close` assumptions.

## Boundary Confirmation

- `adds_sor_fanout_cbbo_or_target_reselection`: `False`
- `approves_live_trading`: `False`
- `approves_paper_trading`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `changes_production_money_flow_rules`: `False`
- `creates_orders`: `False`
- `optimizes_parameters_blindly`: `False`
- `uses_dashboard_chart_data_as_canonical_evidence`: `False`
- `uses_dashboard_date_filter_recalculation`: `False`
- `uses_hyperliquid_testnet_prices`: `False`
- `uses_only_canonical_sv2_0_2_pack_paths`: `True`

## SOR-EV2 Follow-On

SOR-EV2 has now run true-forward stop/exit and rejected-signal entry replay from persisted candle truth. It should supersede SOR-EV1 completed-trade overlays for candidate review, while SOR-EV1 remains the loss-anatomy baseline.
