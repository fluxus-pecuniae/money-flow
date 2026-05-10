# Current State Dashboard

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Today In One Sentence

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform; SV1 is closed for now, one Hyperliquid ETH `sleeve_1h` baseline evidence candidate is frozen, UAT0 safety / security / runtime audit is complete, UAT0.1 API auth/runtime lockout hardening is complete, UAT0.2 adapter policy/read-only allowlist/redaction hardening is complete, UAT0.3 top-20 universe/drawdown readiness preflight is complete, UAT1 public read-only connectivity is complete, UAT1.1 shadow readiness is complete, and UAT2 bounded no-order shadow strategy observation is complete. UAT3 sandbox orders remain blocked.

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
| UAT0 | audit complete | Safety/security/runtime blockers are documented. |
| UAT0.1 | hardening complete | Sensitive API routes now require scoped auth and runtime lockout defaults are inspectable. |
| UAT0.2 | hardening complete | Adapter private/signed/order paths are runtime-policy guarded before transport; Hyperliquid has a future-UAT1 read-only allowlist artifact; representative redaction is tested. |
| UAT0.3 | preflight complete | Fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlist, and runtime drawdown monitor model exist. |
| UAT1 | complete | Explicit public-read-only Hyperliquid endpoint verification plus no-key public top-volume source ingestion and top-20 Hyperliquid observation-universe resolution. |
| UAT1.1 | complete | Model/report-only shadow signal audit, operator-visible shadow drawdown, UAT1 universe snapshot, and representative structured redaction verification exist. |
| UAT2 | complete | Bounded no-order shadow run evaluated 15 Hyperliquid observation-only symbols across 15m, 1h, and 4h sleeves using public read-only candles and shadow audit records only. |
| UAT3 | blocked | Sandbox order design requires explicit founder/operator approval plus sandbox account drawdown, risk, approval, submit-lease, and lifecycle verification. |

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

This is the frozen evidence candidate. Future UAT observation is not ETH-only.

## UAT Observation Universe

Future UAT observation should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment. This validates platform behavior, no-trade reasoning, rejected-signal behavior, symbol mapping, venue support, risk visibility, shadow would-trade behavior, and dashboard/operator explainability. It is not strategy approval.

UAT2 shadow timing compared `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

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

`UAT3` approval-gated sandbox order design may be scoped only after explicit founder/operator approval.

UAT0.1 closed the P0 API authentication/authorization and central runtime lockout baseline. UAT0.2 closed the adapter-level runtime-policy baseline, added the Hyperliquid future-UAT1 read-only allowlist artifact, and tested representative bearer/API-key/secret/password/DB URL redaction. UAT0.3 added fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and a runtime drawdown monitor model. UAT1 verified public read-only Hyperliquid endpoint behavior and resolved the public top-20 supported observation universe without API keys, private/signed/order endpoints, order submission, or strategy execution. UAT1.1 added shadow signal audit records, shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 evaluated 15 observation-only symbols across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`, producing 45 shadow audit records with 11 `would_open` and 34 `no_trade`. Remaining later blockers include explicit founder/operator approval for UAT3 sandbox-order design, sandbox account drawdown feed wiring, and UAT-specific risk/kill-switch/audit visibility verification.

UAT is plumbing and behavior validation.

## Read Next

- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
