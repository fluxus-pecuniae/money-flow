# GOAL-STRAT1 No Three Candidates Found

GOAL-STRAT1 remained research-only. No strategy is production-approved and live trading is not approved.

- Families tested: `mean_reversion, money_flow_repair, pairs_spread_research, relative_strength_rotation, source_faithful_money_flow, trend_breakout, volatility_expansion`
- Candidate configurations: `121`
- Passing candidates: `0`
- Exit models tested: `atr_trail, sma20_break, time_stop`
- Risk models tested: `atr_risk_1pct, equity_10pct, equity_15pct, equity_5pct`
- Regime filters tested: `btc_proxy, none, sma200`
- OOS methods tested: `chronological_70_30, anchored_walk_forward_thirds`

## Best Near Misses

- `volatility_expansion_volatility_expansion_breakout_sma20_break_equity_15pct_sma200_20_20`: `rejected_drawdown`, active net PnL `16840.15578024`, PF `1.81019463`, max DD `0.33611058`, chronological OOS `-1662.57123349`, anchored OOS `-2252.41126942`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_atr_trail_equity_15pct_sma200_20_20`: `rejected_drawdown`, active net PnL `16669.55734526`, PF `1.81182554`, max DD `0.34561218`, chronological OOS `-1609.95059805`, anchored OOS `-2199.07994569`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `trend_breakout_donchian_breakout_atr_trail_equity_15pct_sma200_20`: `rejected_drawdown`, active net PnL `14977.79918528`, PF `1.54612171`, max DD `0.50503796`, chronological OOS `-457.95872790`, anchored OOS `-1016.02968965`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `trend_breakout_donchian_breakout_sma20_break_equity_15pct_sma200_20`: `rejected_drawdown`, active net PnL `14721.88180666`, PF `1.52565373`, max DD `0.50282009`, chronological OOS `-632.46077378`, anchored OOS `-1334.39935600`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`
- `volatility_expansion_volatility_expansion_breakout_sma20_break_equity_15pct_none_20_20`: `rejected_drawdown`, active net PnL `13745.25929186`, PF `1.46072936`, max DD `0.43339411`, chronological OOS `-1462.17492332`, anchored OOS `-2379.18921744`, blockers `rejected_drawdown, chronological_oos_net_pnl_negative, anchored_walk_forward_oos_net_pnl_negative`

## Blocker Summary

- `profit_factor_below_threshold`: `84`
- `anchored_walk_forward_oos_net_pnl_negative`: `80`
- `chronological_oos_net_pnl_negative`: `74`
- `rejected_drawdown`: `72`
- `rejected_no_edge`: `66`
- `rejected_concentrated_period`: `14`
- `rejected_low_sample`: `6`
- `largest_single_trade_loss_too_large`: `2`
- `research_only_insufficient_market_structure_data`: `1`

## What The Evidence Suggests

- Positive aggregate pockets exist in volatility-expansion and Donchian-style trend breakout variants.
- Higher notional variants fail drawdown control.
- Lower-risk variants that control drawdown still fail chronological and anchored OOS checks.
- Mean-reversion and source-faithful Money Flow families did not produce a robust candidate under this data and gate.
- Pairs/spread research remains research-only because candle-only data is insufficient for hedge, funding, borrow, and execution assumptions.

## What Is Needed Next

- Only 0 candidates passed; do not promote fewer than three as a production-testing slate.
- Add longer non-overlapping OOS data and execution-quality constraints before widening parameters further.
- Prioritize candidates that fail only sample-size or OOS breadth, not candidates blocked by drawdown or concentration.

## Decision

Three strategies were not found without overfitting after full autonomous discovery.
