# Money Flow Strategy Lab

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Purpose

Keep the Money Flow strategy thread visible while platform, routing, execution, and UAT planning work becomes complex.

## Current Money Flow Role

Money Flow is the first strategy family. It is not the universal vocabulary of the platform.

Current Strategy Validation state: SV1 is closed for now. SV1.18 froze exactly one evidence candidate, Hyperliquid ETH `sleeve_1h` baseline current Money Flow rules, after the Hyperliquid public campaign evidence cycle, dynamic-equity simulation, trade-anatomy diagnostics, and true replay experiments. UAT0 safety / security / runtime audit is complete, UAT0.1 API auth/authz and runtime lockout hardening is complete, UAT0.2 adapter runtime-policy / read-only allowlist / representative redaction hardening is complete, UAT0.3 top-20 universe / runtime drawdown / UAT1 preflight is complete, UAT1 public read-only connectivity is complete, and UAT1.1 shadow-readiness hardening is complete. UAT2 shadow strategy run may proceed as a future no-order phase.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved. Production Money Flow rules are unchanged.

## Strategy Logic Summary

Current Money Flow entries require constructive momentum / controlled pullback behavior:

- EMA5 > EMA10 > SMA20.
- RSI inside the sleeve band.
- RSI below overbought.
- MACD constructive when required.
- Pullback or continuation quality.
- Price not too extended above EMA5.

The strategy does not enter long when RSI is below the sleeve floor. It is not a deep-oversold mean-reversion system.

## Current Evidence Interpretation

The strongest observed scenario is ETH `sleeve_1h` baseline on Hyperliquid USDC perpetual public candles. That is a UAT observation candidate only. Current evidence does not prove future outcomes and does not authorize paper/live trading.

Future UAT observation is not ETH-only. UAT1/UAT2 should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment to validate platform behavior, no-trade reasoning, symbol mapping, risk visibility, and operator explainability. Top-20 inclusion is not strategy approval.

Excluded from current UAT scope:

- 15m sleeve.
- 4h sleeve.
- BTC 1h.
- SOL 1h.
- lower-RSI variants.
- market-structure variants.
- cross-venue candidates.

## Questions To Keep Alive

- Does ETH `sleeve_1h` behave coherently in UAT shadow observation?
- Are signals explainable in real runtime conditions?
- Do risk and drawdown controls work before any sandbox order phase?
- Which evidence limitations matter most before paper-trading design can be discussed?
- What strategy families should come after Money Flow?

## Related Notes

- [[00 Maps/Strategy Validation Map]]
- [[30 Strategy/Strategy Validation Summary]]
- [[30 Strategy/UAT Candidate Freeze]]
- [[30 Strategy/Excluded Strategy Candidates]]
- [[10 Components/Strategy Engine]]
- [[10 Components/Market Data and Indicators]]
- [[30 Strategy/Product North Star]]
