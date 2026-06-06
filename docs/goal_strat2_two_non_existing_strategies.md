# GOAL-STRAT2 Two Non-Existing Strategies Worth Testing

GOAL-STRAT2 is research-only. No strategy is production-approved. Live trading is not approved.

## Decision

- Decision: `two_non_existing_strategies_worth_testing`
- Candidate runs screened: `121`
- Eligible non-existing candidates: `4`
- Selected candidates: `2`

## Selected Candidates

### 1. `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34`

- Family: `relative_strength_rotation`
- Entry / exit / risk / regime: `top_n_trend_strength` / `atr_trail` / `equity_5pct` / `sma200`
- Active net PnL: `3324.52698075`
- Profit factor: `1.34770034`
- Max drawdown pct: `0.30169678`
- Trade count: `534`
- Chronological OOS net PnL: `249.29807586`
- Anchored OOS net PnL: `78.69597719`
- Why worth testing: `non-existing strategy family relative to current PT runtime lanes; positive active net PnL 3324.52698075 after fees/slippage; profit factor 1.34770034 exceeds paper-testing gate; 534 trades is enough for forward paper-testing triage; drawdown 0.30169678 stays inside paper-testing gate; both OOS checks are positive`
- Why it may fail: `drawdown is near the upper testing bound; single-symbol contribution is material and must be monitored in paper testing; timeframe contribution is concentrated and should be reviewed by timeframe; period contribution is concentrated and may not persist; candle-only backtest lacks order-book, funding, partial-fill, and live reject modeling; forward testing must be paper-only before any runtime lane discussion`

### 2. `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20`

- Family: `trend_breakout`
- Entry / exit / risk / regime: `donchian_breakout` / `atr_trail` / `equity_5pct` / `sma200`
- Active net PnL: `5086.37911867`
- Profit factor: `1.57118130`
- Max drawdown pct: `0.16370536`
- Trade count: `945`
- Chronological OOS net PnL: `-200.10597846`
- Anchored OOS net PnL: `-376.52358465`
- Why worth testing: `non-existing strategy family relative to current PT runtime lanes; positive active net PnL 5086.37911867 after fees/slippage; profit factor 1.57118130 exceeds paper-testing gate; 945 trades is enough for forward paper-testing triage; drawdown 0.16370536 stays inside paper-testing gate; OOS losses are small enough to justify forward testing but not promotion`
- Why it may fail: `chronological OOS is negative; anchored OOS is negative; single-symbol contribution is material and must be monitored in paper testing; timeframe contribution is concentrated and should be reviewed by timeframe; period contribution is concentrated and may not persist; candle-only backtest lacks order-book, funding, partial-fill, and live reject modeling; forward testing must be paper-only before any runtime lane discussion`

## Gate

- Minimum profit factor: `1.30`
- Maximum drawdown pct: `0.32`
- Minimum trade count: `200`
- Minimum chronological OOS net PnL: `-500`
- Minimum anchored OOS net PnL: `-500`
- Existing Money Flow/SOR/MF-ORIG/wildcard-adjacent families and entry models are excluded.

## Boundaries

- `research_only`: `True`
- `mutates_active_pt_rt_runtime`: `False`
- `creates_runtime_artifacts`: `False`
- `submits_live_orders`: `False`
- `submits_testnet_orders`: `False`
- `calls_private_signed_order_endpoints`: `False`
- `uses_testnet_data_as_strategy_truth`: `False`
- `uses_testnet_fills_as_pnl_truth`: `False`
- `changes_production_money_flow_rules`: `False`
- `approves_production_strategy`: `False`
- `approves_live_trading`: `False`
- `creates_order_intent`: `False`
- `creates_prepared_venue_order`: `False`
- `creates_submitted_order`: `False`
