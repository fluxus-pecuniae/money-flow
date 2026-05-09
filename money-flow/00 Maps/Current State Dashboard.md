# Current State Dashboard

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Today In One Sentence

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform; SV1 is closed for now, one Hyperliquid ETH `sleeve_1h` baseline UAT observation candidate is frozen, and UAT0 safety / security / runtime hardening is next.

SV1.18 is complete.

## Current Product State

Money Flow can generate strategy decisions, route through controlled same-target workflow stages, inspect readiness and submitted-order lifecycle truth, and review Strategy Validation evidence. It is not approved for paper trading, live trading, or exchange order submission.

## Completed Tracks

| Track | Status | Meaning |
| --- | --- | --- |
| Core strategy logic | built | Money Flow baseline exists with 15m, 1h, and 4h sleeves. |
| Planning / risk / execution substrate | built | Controlled execution infrastructure exists, but live operational use remains gated. |
| Routing substrate | built | Non-executing assessment/recommendation/target-choice workflow exists; this is not full SOR. |
| Approval-gated automation | built | Controlled, lineage-bound action hooks exist for the current same-target chain. |
| Operator observability | built | Routed workflow inspection exists for operator review. |
| Strategy Validation SV1 | closed | Current Hyperliquid evidence cycle is complete through SV1.18.1. |
| UAT | not started | UAT0 is next and is safety/runtime hardening only. |

## Current Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Value |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow first |

## Explicit Non-Approvals

- Paper trading is not approved.
- Live trading is not approved.
- Exchange order submission is not approved.
- Full SOR is not active.
- Strategy profitability is not proven.
- Production Money Flow rule changes are not approved.

## Strategy Validation Closeout

SV1.18 states that current evidence does not prove edge. It can justify only tightly scoped UAT behavior observation after UAT0 safety/runtime checks.

Current UAT scope excludes:

- 15m sleeve
- 4h sleeve
- BTC 1h
- SOL 1h
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## Next Phase

`UAT0` - Safety / Security / Runtime Hardening.

UAT0 validates plumbing, runtime safety, mode gating, secret hygiene, risk visibility, kill switch behavior, and operator controls. It does not validate performance.

UAT is plumbing and behavior validation.

## Read Next

- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
