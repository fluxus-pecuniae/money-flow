# GOAL-STRAT2 Candidate 2: trend_breakout: donchian_breakout / atr_trail / equity_5pct / sma200

This is a founder paper-testing review candidate only. It is not production-approved and live trading is not approved.

## Strategy Logic

- Strategy id: `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20`
- Family: `trend_breakout`
- Entry model: `donchian_breakout`
- Exit model: `atr_trail`
- Risk model: `equity_5pct`
- Regime filter: `sma200`
- Current PT runtime lanes excluded: yes.
- Existing Money Flow/SOR/MF-ORIG/wildcard-adjacent families excluded: yes.

## Evidence

- Active net PnL: `5086.37911867`
- Ending equity: `15086.37911867`
- Max drawdown pct: `0.16370536`
- Profit factor: `1.57118130`
- Win rate: `0.36507937`
- Trade count: `945`
- Largest win: `4185.46149292`
- Largest loss: `-172.46827278`
- Average win: `40.55477122`
- Average loss: `-14.84169492`
- Max consecutive losses: `15`
- Chronological OOS net PnL: `-200.10597846`
- Anchored OOS net PnL: `-376.52358465`
- Symbol concentration: `{'AAVE': '0.02587045', 'ADA': '0.05224313', 'AVAX': '0.04513173', 'BNB': '0.02542675', 'BTC': '0.02517614', 'DOGE': '0.05368673', 'DOT': '0.00974670', 'ETH': '0.05549205', 'FIL': '0.01120948', 'HYPE': '0.10003957', 'LINK': '0.02719186', 'LTC': '0.01772433', 'SOL': '0.03711007', 'SUI': '0.07195186', 'TON': '0.00950955', 'TRX': '0.01162994', 'UNI': '0.03548255', 'XMR': '0.02477762', 'XRP': '0.03773168', 'ZEC': '0.32286780'}`
- Timeframe concentration: `{'1d': '0.55276155', '1h': '0.17365979', '4h': '0.27357865'}`
- Period concentration: `{'2024-H2': '0.17421480', '2025-H1': '0.12814031', '2025-H2': '0.46603442', '2026-H1': '0.23161047'}`

## Why It Is Worth Testing

- non-existing strategy family relative to current PT runtime lanes
- positive active net PnL 5086.37911867 after fees/slippage
- profit factor 1.57118130 exceeds paper-testing gate
- 945 trades is enough for forward paper-testing triage
- drawdown 0.16370536 stays inside paper-testing gate
- OOS losses are small enough to justify forward testing but not promotion

## Why It May Still Fail

- chronological OOS is negative
- anchored OOS is negative
- single-symbol contribution is material and must be monitored in paper testing
- timeframe contribution is concentrated and should be reviewed by timeframe
- period contribution is concentrated and may not persist
- candle-only backtest lacks order-book, funding, partial-fill, and live reject modeling
- forward testing must be paper-only before any runtime lane discussion

## Boundary

Research-only. Do not route to testnet or live trading. Do not treat this as production approval.
