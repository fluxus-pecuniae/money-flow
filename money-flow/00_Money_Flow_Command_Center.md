# Money Flow Command Center

This is the canonical Obsidian command center for Money Flow agents and founder review.

## Current Truth

| Field | Current State |
| --- | --- |
| Current implemented milestone | `UAT0.2` adapter runtime-policy and redaction hardening complete |
| Current major track | Strategy Validation evidence cycle is closed |
| Next proposed phase | Remaining UAT0 P1 blocker remediation before `UAT1` |
| UAT status | UAT1 read-only connectivity is blocked |
| Paper trading | Not approved |
| Live trading | Not approved |
| Exchange order submission | Not approved |
| Routing / SOR expansion | Deferred |
| Production Money Flow rules | Unchanged |

SV1.18 is complete. UAT0 is complete as a safety/security/runtime audit. UAT0.1 closes the P0 API auth/authz baseline for sensitive `/api/v1` routes and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT1 is still blocked until remaining P1 blockers are closed. UAT is plumbing and behavior validation. The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline. Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow first |
| Execution status | No exchange order submission approved |

This candidate is not a production strategy, not paper-trading approval, and not live-trading approval. It is the narrowest current evidence candidate for UAT behavior observation.

## UAT Observation Universe

Future UAT observation is not ETH-only. UAT1/UAT2 should use a top 20 high-volume crypto asset universe supported by the selected UAT venue/environment to validate platform behavior, no-trade reasoning, rejected-signal behavior, symbol mapping, risk visibility, and operator explainability. Top-20 inclusion is not strategy approval.

Future UAT2 shadow timing must compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## What Money Flow Is Today

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform. The platform has strategy, planning, risk, routing-assessment, approval-gated action hooks, execution-readiness, submitted-order lifecycle, and operator observability foundations. The current business focus is not more routing scope; it is making the strongest observed Money Flow scenario safe to observe in UAT.

## Track Map

- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Phase Timeline|Phase Timeline]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[00 Maps/Platform Architecture Map|Platform Architecture Map]]

## Strategy Validation Closeout

SV1.18 closed the current Hyperliquid public-candle evidence cycle. It established:

- ETH `sleeve_1h` baseline is the strongest observed candidate.
- 15m, 4h, BTC/SOL 1h, lower-RSI variants, market-structure variants, and cross-venue candidates are excluded from current UAT scope.
- Current evidence is useful for UAT planning, but it does not prove edge.
- Strategy Validation did not model funding, liquidation, production margin, order-book fills, partial fills, latency, outages, or live reject/reconcile behavior.

Read [[00 Maps/Strategy Validation Map|Strategy Validation Map]] and [[30 Strategy/SV Evidence Closeout|SV Evidence Closeout]] before interpreting SV results.

## UAT0 / UAT0.1 / UAT0.2 Result

UAT0 found UAT1 is blocked. UAT0.1 closes the P0 API authentication/authorization and central runtime-policy baseline:

- Sensitive `/api/v1` routes require scoped bearer authentication.
- Administrative consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes.
- Test auth bypass is limited to `API_RUNTIME_MODE=test`.
- `RuntimeSafetyPolicy` defaults paper trading, live trading, exchange order submission, and private exchange endpoints to disabled.

UAT0.2 closes or partially closes the next safety layer:

- Adapter private/signed/order helpers block before transport when runtime policy disables them.
- Hyperliquid has a testable future-UAT1 read-only allowlist artifact.
- Representative bearer/API-key/secret/password/DB URL redaction is tested.
- Adapter-helper error messages redact obvious secrets before logging/raising.

Remaining blockers before UAT1 include broader structured application log/API error redaction verification, Hyperliquid public read-only endpoint URL and sandbox/testnet verification, runtime drawdown monitoring, and top-20 symbol/market identity resolution.

Read [[00 Maps/UAT Roadmap|UAT Roadmap]] and [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]] before any UAT work.

## Required Agent Workflow

Before substantial work, read:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- this command center
- [[01_Current_Phase|Current Phase]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- the current track map relevant to the task

Before editing overlapping files, update your own row in [[05_Agent_Coordination|Agent Coordination]]. After work, mark the row `done` or `blocked`.

Do not create duplicate command centers or competing current-phase notes.

## Repo Truth Sources

Repo operational truth remains in:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

Obsidian is strategic memory and coordination. It does not replace repo operational docs.
