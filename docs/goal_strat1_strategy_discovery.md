# GOAL-STRAT1 Strategy Discovery

GOAL-STRAT1 is research-only. No strategy is production-approved. Live trading is not approved.

## Summary

- Conclusion: `three_candidates_were_not_found_without_overfitting_after_full_autonomous_discovery`
- Candidate configurations tested: `121`
- Passing candidates: `0`
- Datasets accepted: `49`
- Strategy families tested: `7`
- Exit models tested: `3`
- Risk models tested: `4`
- Regime filters tested: `3`

## Data Inventory

| symbol | timeframe | candles | earliest | latest | status | reason codes |
| --- | --- | ---: | --- | --- | --- | --- |
| AAVE | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| ADA | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| ASTER | 1d | 237 | 2025-09-20T00:00:00Z | 2026-05-14T00:00:00Z | quarantined | insufficient_history |
| AVAX | 15m | 5004 | 2026-03-21T04:00:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| AVAX | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| AVAX | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| AVAX | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| BNB | 15m | 5004 | 2026-03-21T04:00:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| BNB | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| BNB | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| BNB | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| BTC | 15m | 5005 | 2026-03-21T03:45:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| BTC | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| BTC | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| BTC | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| DOGE | 15m | 5004 | 2026-03-21T04:00:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| DOGE | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| DOGE | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| DOGE | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| DOT | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| ETH | 15m | 5005 | 2026-03-21T03:45:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| ETH | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| ETH | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| ETH | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| FIL | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| HYPE | 15m | 5012 | 2026-03-21T02:00:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| HYPE | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| HYPE | 1h | 5002 | 2025-10-15T21:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| HYPE | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| LINK | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| LTC | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| POL | 1d | 608 | 2024-09-14T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| SOL | 15m | 5005 | 2026-03-21T03:45:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| SOL | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| SOL | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| SOL | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| SUI | 15m | 5003 | 2026-03-21T04:15:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| SUI | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| SUI | 1h | 5000 | 2025-10-15T23:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| SUI | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| TON | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| TRUMP | 1d | 481 | 2025-01-19T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| TRX | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| UNI | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| XMR | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| XRP | 15m | 5002 | 2026-03-21T04:30:00Z | 2026-05-12T06:45:00Z | accepted | dataset_accepted |
| XRP | 1d | 496 | 2025-01-02T00:00:00Z | 2026-05-12T00:00:00Z | accepted | dataset_accepted |
| XRP | 1h | 4999 | 2025-10-16T00:00:00Z | 2026-05-12T06:00:00Z | accepted | dataset_accepted |
| XRP | 4h | 2977 | 2025-01-01T04:00:00Z | 2026-05-12T04:00:00Z | accepted | dataset_accepted |
| ZEC | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |

## Top Candidates

No strategy passed the full GOAL-STRAT1 candidate gate.

## Best Near Misses

- `volatility_expansion_volatility_expansion_breakout_sma20_break_equity_15pct_sma200_20_20`: `rejected_drawdown`, active net PnL `16840.15578024`, PF `1.81019463`, DD `0.33611058`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_atr_trail_equity_15pct_sma200_20_20`: `rejected_drawdown`, active net PnL `16669.55734526`, PF `1.81182554`, DD `0.34561218`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `trend_breakout_donchian_breakout_atr_trail_equity_15pct_sma200_20`: `rejected_drawdown`, active net PnL `14977.79918528`, PF `1.54612171`, DD `0.50503796`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `trend_breakout_donchian_breakout_sma20_break_equity_15pct_sma200_20`: `rejected_drawdown`, active net PnL `14721.88180666`, PF `1.52565373`, DD `0.50282009`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_sma20_break_equity_15pct_none_20_20`: `rejected_drawdown`, active net PnL `13745.25929186`, PF `1.46072936`, DD `0.43339411`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_atr_trail_equity_15pct_none_20_20`: `rejected_drawdown`, active net PnL `13497.47734634`, PF `1.45831636`, DD `0.43541429`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_sma20_break_equity_10pct_sma200_20_20`: `rejected_overfit`, active net PnL `11334.64015035`, PF `1.82773995`, DD `0.22193927`, blockers `chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `relative_strength_rotation_top_n_trend_strength_sma20_break_equity_15pct_sma200_20_0p34`: `rejected_drawdown`, active net PnL `11261.85097465`, PF `1.41475597`, DD `0.71556636`, blockers `rejected_drawdown`

## Candidate Gate

- `positive_net_pnl_after_fees_slippage`: `True`
- `ending_equity_above_start`: `True`
- `profit_factor_min`: `1.15`
- `max_drawdown_pct_max`: `0.30`
- `largest_single_trade_loss_pct_max`: `0.08`
- `min_trades_total_1h_4h`: `50`
- `min_trades_total_1d`: `20`
- `chronological_70_30_oos_net_pnl_nonnegative`: `True`
- `anchored_walk_forward_thirds_oos_net_pnl_nonnegative`: `True`
- `single_symbol_net_pnl_share_max`: `0.45`
- `single_period_net_pnl_share_max`: `0.60`
- `fifteen_minute_is_diagnostic_not_promotion`: `True`
- `lookahead_allowed`: `False`
- `same_candle_optimistic_fill_allowed`: `False`
- `production_or_live_approval`: `False`

## Boundaries

- `research_only`: `True`
- `changes_production_money_flow_rules`: `False`
- `mutates_active_pt_rt_runtime`: `False`
- `mutates_runtime_artifacts`: `False`
- `creates_order_intent`: `False`
- `creates_prepared_venue_order`: `False`
- `creates_submitted_order`: `False`
- `submits_live_orders`: `False`
- `submits_testnet_orders`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `uses_testnet_data_as_strategy_truth`: `False`
- `uses_testnet_fills_as_pnl_truth`: `False`
- `approves_live_trading`: `False`
- `approves_production_strategy`: `False`
- `uses_dashboard_date_filters_as_canonical_evidence`: `False`

## Decision

Three strategies were not found without overfitting after full autonomous discovery.
