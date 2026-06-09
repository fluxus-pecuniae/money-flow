# SV2.3 Realistic Backtest

## Verdict

- Status: `realistic_backtest_complete`
- Purpose: realistic next-candle-open evidence layer for the founder-selected Week 2 strategies.
- Default decision surface: Evidence, not Historical Replay.
- Historical Replay remains visual inspection only.
- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.
- Trading boundary: no orders, private/signed/order endpoints, API keys, testnet strategy truth, live approval, or production approval.

## Realistic Execution Model

- Primary fill assumption: `next_candle_open`
- Disabled promotion fills: `same_candle_close_research_only, next_candle_close`
- Signals are evaluated after candle close; fills occur at the next candle open with fees, slippage, and scenario stress.
- SV2.3 does not use same-candle fills for promotion-facing results.

## Scope

- Generated at UTC: `2026-06-08T12:52:22Z`
- Strategies: `money_flow_v1_2_baseline, avoid_low_rolling_range_20, mf_orig_1d_stage2_breakout_resistance_full_equity`
- Timeframes: `1h, 4h, 1d`
- Disabled timeframes: `15m`
- Result rows: `621`

## Strategy Gate Summary

| Strategy | Status | Reasons |
| --- | --- | --- |
| `avoid_low_rolling_range_20` | `not_promoted_realistic_gate_failed` | `base_next_open_failed, conservative_next_open_failed, stress_next_open_net_pnl_negative` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `not_promoted_realistic_gate_failed` | `base_next_open_failed, conservative_next_open_failed` |
| `money_flow_v1_2_baseline` | `not_promoted_realistic_gate_failed` | `base_next_open_failed, conservative_next_open_failed, stress_next_open_net_pnl_negative` |

## Aggregate Results

| Strategy | Scenario | Net PnL | Trades | Profit Factor | Worst DD | Gate |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `avoid_low_rolling_range_20` | `base_next_open` | `-77394.55050274` | `10080` | `0.60689683` | `37760.60119535` | `fails_aggregate_realistic_gate` |
| `avoid_low_rolling_range_20` | `conservative_next_open` | `-155254.99799294` | `10080` | `0.39836763` | `37190.82871496` | `fails_aggregate_realistic_gate` |
| `avoid_low_rolling_range_20` | `stress_next_open` | `-241147.09720998` | `10080` | `0.26667460` | `36387.95980433` | `fails_aggregate_realistic_gate` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `base_next_open` | `155140.87686128` | `2992` | `2.28971790` | `103199.68356062` | `fails_aggregate_realistic_gate` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `conservative_next_open` | `119776.22299882` | `2992` | `1.86445328` | `102467.07322298` | `fails_aggregate_realistic_gate` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `stress_next_open` | `73473.05378781` | `2992` | `1.44908425` | `101436.36282134` | `fails_aggregate_realistic_gate` |
| `money_flow_v1_2_baseline` | `base_next_open` | `-85740.74865029` | `11134` | `0.58221549` | `37760.60119535` | `fails_aggregate_realistic_gate` |
| `money_flow_v1_2_baseline` | `conservative_next_open` | `-168633.91144830` | `11134` | `0.37873227` | `37190.82871496` | `fails_aggregate_realistic_gate` |
| `money_flow_v1_2_baseline` | `stress_next_open` | `-257964.81857104` | `11134` | `0.25369977` | `36387.95980433` | `fails_aggregate_realistic_gate` |

## Boundaries

- Public Hyperliquid mainnet candles from SV2.2 remain strategy truth.
- Testnet data is not strategy truth.
- Testnet fills do not update PnL.
- No live trading is approved.
- No strategy is production-approved.
