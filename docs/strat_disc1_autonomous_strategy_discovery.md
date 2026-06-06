# STRAT-DISC1 Autonomous Strategy Discovery

## Summary

STRAT-DISC1 is research-only. No strategy is production-approved. Live trading is not approved.

- Conclusion: `no_three_candidates_found_without_overfitting`
- Candidate runs: `12`
- Passing candidates: `0`
- Datasets accepted: `50`

## Data Inventory

| symbol | timeframe | candles | earliest | latest | status | reason codes |
| --- | --- | ---: | --- | --- | --- | --- |
| AAVE | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| ADA | 1d | 864 | 2024-01-02T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
| ASTER | 1d | 237 | 2025-09-20T00:00:00Z | 2026-05-14T00:00:00Z | accepted | dataset_accepted |
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

## Strategy Families Tested

- `mean_reversion`
- `money_flow_repair`
- `original_money_flow_stage`
- `pairs_spread_research`
- `relative_strength_rotation`
- `trend_breakout`
- `trend_following`
- `volatility_expansion`

## Candidate Gate

- `positive_net_pnl_after_fees_slippage`: `True`
- `out_of_sample_net_pnl_nonnegative`: `True`
- `profit_factor_min`: `1.15`
- `max_drawdown_pct_max`: `0.30`
- `largest_single_trade_loss_pct_max`: `0.08`
- `min_trades_total_1h_4h`: `50`
- `min_trades_total_1d`: `20`
- `single_symbol_net_pnl_share_max`: `0.45`
- `single_period_net_pnl_share_max`: `0.60`
- `fifteen_minute_is_diagnostic_not_promotion`: `True`
- `lookahead_allowed`: `False`
- `same_candle_optimistic_fill_allowed`: `False`
- `production_or_live_approval`: `False`

## Top Candidates

No strategy passed the full candidate gate.

## Near Misses

- `mf_orig_stage2_pullback_reclaim`: `rejected_drawdown`, net PnL `42023.57608493`, PF `1.07873655`, blockers `profit_factor_below_threshold, rejected_drawdown, largest_single_trade_loss_too_large`
- `mf_repair_macd_histogram_reaccelerating`: `rejected_drawdown`, net PnL `-3134.04938473`, PF `0.99451373`, blockers `rejected_no_edge, profit_factor_below_threshold, rejected_drawdown, largest_single_trade_loss_too_large`
- `relative_strength_top3_trend_proxy`: `rejected_drawdown`, net PnL `-4188.15260248`, PF `0.99130349`, blockers `rejected_no_edge, profit_factor_below_threshold, rejected_drawdown, largest_single_trade_loss_too_large`
- `volatility_expansion_breakout_rr50`: `rejected_drawdown`, net PnL `56830.64611877`, PF `1.21566610`, blockers `rejected_drawdown, largest_single_trade_loss_too_large`
- `volatility_expansion_breakout_rr20`: `rejected_drawdown`, net PnL `57690.51388766`, PF `1.21178089`, blockers `rejected_drawdown, largest_single_trade_loss_too_large`

## Boundaries

- `research_only`: `True`
- `changes_production_money_flow_rules`: `False`
- `mutates_active_pt_rt_runtime`: `False`
- `creates_order_intent`: `False`
- `creates_prepared_venue_order`: `False`
- `creates_submitted_order`: `False`
- `submits_live_orders`: `False`
- `submits_testnet_orders`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `uses_testnet_data_as_strategy_truth`: `False`
- `approves_live_trading`: `False`
- `approves_production_strategy`: `False`
- `uses_dashboard_date_filters_as_canonical_evidence`: `False`

## Decision

Three strategies were not found without overfitting. No strategy should be promoted yet.
