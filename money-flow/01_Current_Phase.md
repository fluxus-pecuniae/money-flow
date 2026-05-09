# Current Phase

## Current Implemented Milestone

`UAT0` safety / security / runtime audit is complete.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named P0/P1 gaps are closed.

SV1.18 is complete.

## Next Proposed Phase

UAT0 blocker remediation before `UAT1` read-only top-20 universe and market metadata work.

UAT1 is blocked. UAT remains plumbing and behavior validation only. It is not paper trading, live trading, exchange order submission, routing expansion, or strategy optimization.

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

The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline.

## UAT Observation Universe And Timing

Future UAT observation is not ETH-only. UAT1/UAT2 should use top 20 high-volume crypto assets supported by the selected UAT venue/environment to validate platform behavior, market metadata, symbol mapping, risk visibility, no-trade/rejected-signal reasoning, and operator explainability. Top-20 inclusion is not strategy approval.

Future UAT2 shadow timing must compare:

- `next_candle_open`
- `next_candle_close`

`same_candle_close_research_only` remains research-only.

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

Current backtest/replay evidence does not prove profitability or future edge. It was sufficient only to justify founder review and a tightly scoped UAT0 safety/runtime audit.

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

## UAT0 Result

UAT0 found UAT1 is blocked until P0/P1 gaps are closed:

- API authentication / authorization is missing for sensitive routes.
- Fail-safe UAT mode and live endpoint lockout are not complete.
- Secret/log/error redaction needs verification.
- Runtime drawdown monitoring is missing.
- Top-20 market identity resolution is not implemented.
- Existing approval gates and submit leases are useful but require UAT3 verification before sandbox orders.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
