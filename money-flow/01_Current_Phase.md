# Current Phase

## Current Implemented Milestone

`SV1.18.1` is complete.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one UAT observation candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap and left UAT0 as the next proposed phase.

SV1.18 is complete.

## Next Proposed Phase

`UAT0` safety / security / runtime hardening.

UAT0 is plumbing and behavior validation preparation only. It is not paper trading, live trading, exchange order submission, routing expansion, or strategy optimization.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| UAT mode | Observation / shadow first |
| Execution | None until a later explicitly gated UAT phase |

The frozen candidate is Hyperliquid ETH `sleeve_1h` current baseline.

## Explicit Non-Approvals

- Paper trading is not approved.
- Live trading is not approved.
- Exchange order submission is not approved.
- Production Money Flow rule changes are not approved.
- Lower-RSI variants are not approved.
- Market-structure variants are not approved.
- Cross-venue evidence is not current UAT scope.
- Routing / SOR expansion is not current priority.

## Current Evidence Meaning

Current backtest/replay evidence does not prove profitability or future edge. It is sufficient only to justify founder review and a tightly scoped UAT0 safety/runtime phase.

SV1.18 selected ETH `sleeve_1h` baseline because it is the strongest observed Hyperliquid public-candle scenario. That does not make it a production strategy.

Excluded from UAT scope:

- `sleeve_15m`
- `sleeve_4h`
- BTC `sleeve_1h`
- SOL `sleeve_1h`
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## UAT0 Purpose

UAT0 should verify:

- API authentication / authorization readiness
- key and secret hygiene
- no secrets in logs
- fail-safe sandbox/live separation
- sandbox/testnet environment gating
- risk-limit enforcement
- drawdown monitoring
- kill switch / disable switch
- debug stack traces not exposed to users
- audit logging
- operator confirmation gates
- duplicate-order prevention
- submit-lease uncertainty handling
- no private endpoint calls before explicit UAT authorization
- no accidental live endpoint reachability

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
