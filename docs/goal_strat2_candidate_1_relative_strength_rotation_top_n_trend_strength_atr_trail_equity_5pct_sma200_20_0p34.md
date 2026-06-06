# GOAL-STRAT2 Candidate 1: relative_strength_rotation: top_n_trend_strength / atr_trail / equity_5pct / sma200

This is a founder paper-testing review candidate only. It is not production-approved and live trading is not approved.

## Strategy Logic

- Strategy id: `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34`
- Family: `relative_strength_rotation`
- Entry model: `top_n_trend_strength`
- Exit model: `atr_trail`
- Risk model: `equity_5pct`
- Regime filter: `sma200`
- Current PT runtime lanes excluded: yes.
- Existing Money Flow/SOR/MF-ORIG/wildcard-adjacent families excluded: yes.

## Evidence

- Active net PnL: `3324.52698075`
- Ending equity: `13324.52698075`
- Max drawdown pct: `0.30169678`
- Profit factor: `1.34770034`
- Win rate: `0.35393258`
- Trade count: `534`
- Largest win: `4387.00061342`
- Largest loss: `-183.99554639`
- Average win: `68.17988699`
- Average loss: `-27.71441061`
- Max consecutive losses: `18`
- Chronological OOS net PnL: `249.29807586`
- Anchored OOS net PnL: `78.69597719`
- Symbol concentration: `{'AAVE': '0.01790055', 'ADA': '0.05847521', 'AVAX': '0.04203360', 'BNB': '0.02158139', 'BTC': '0.01586684', 'DOGE': '0.05008703', 'DOT': '0.01787218', 'ETH': '0.04997657', 'FIL': '0.01217106', 'HYPE': '0.09010751', 'LINK': '0.02952445', 'LTC': '0.01274537', 'SOL': '0.03458012', 'SUI': '0.05495020', 'TON': '0.01032062', 'TRX': '0.01714015', 'UNI': '0.03806788', 'XMR': '0.03747871', 'XRP': '0.02318568', 'ZEC': '0.36593487'}`
- Timeframe concentration: `{'1d': '0.63753658', '4h': '0.36246342'}`
- Period concentration: `{'2024-H2': '0.17271113', '2025-H1': '0.16020522', '2025-H2': '0.53967773', '2026-H1': '0.12740592'}`

## Why It Is Worth Testing

- non-existing strategy family relative to current PT runtime lanes
- positive active net PnL 3324.52698075 after fees/slippage
- profit factor 1.34770034 exceeds paper-testing gate
- 534 trades is enough for forward paper-testing triage
- drawdown 0.30169678 stays inside paper-testing gate
- both OOS checks are positive

## Why It May Still Fail

- drawdown is near the upper testing bound
- single-symbol contribution is material and must be monitored in paper testing
- timeframe contribution is concentrated and should be reviewed by timeframe
- period contribution is concentrated and may not persist
- candle-only backtest lacks order-book, funding, partial-fill, and live reject modeling
- forward testing must be paper-only before any runtime lane discussion

## Boundary

Research-only. Do not route to testnet or live trading. Do not treat this as production approval.
