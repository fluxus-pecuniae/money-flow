# Money Flow Command Center

This is the canonical Obsidian command center for Money Flow agents and founder review.

## Current Truth

| Field | Current State |
| --- | --- |
| Current implemented milestone | `UAT1.1` shadow signal audit, drawdown visibility, and redaction verification complete |
| Current major track | Strategy Validation evidence cycle is closed |
| Next proposed phase | `UAT2` shadow strategy run as no-order observation |
| UAT status | UAT1 public read-only connectivity is complete; UAT1.1 shadow readiness is complete; UAT2 may proceed next |
| Paper trading | Not approved |
| Live trading | Not approved |
| Exchange order submission | Not approved |
| Routing / SOR expansion | Deferred |
| Production Money Flow rules | Unchanged |

SV1.18 is complete. UAT0 is complete as a safety/security/runtime audit. UAT0.1 closes the P0 API auth/authz baseline for sensitive `/api/v1` routes and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds a fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and a fixture-tested runtime drawdown monitor model. UAT1 verified explicit public-read-only Hyperliquid endpoint behavior, fetched a no-key public CoinGecko top-volume source, intersected it with Hyperliquid USDC perpetual metadata, and kept all included assets observation-only. UAT1.1 adds model/report-only shadow signal audit records, operator-visible shadow drawdown, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 shadow strategy run may proceed as a future no-order phase. UAT is plumbing and behavior validation. The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline. Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

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

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 Result

UAT0 initially found UAT1 blocked. UAT0.1 closed the P0 API authentication/authorization and central runtime-policy baseline:

- Sensitive `/api/v1` routes require scoped bearer authentication.
- Administrative consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes.
- Test auth bypass is limited to `API_RUNTIME_MODE=test`.
- `RuntimeSafetyPolicy` defaults paper trading, live trading, exchange order submission, and private exchange endpoints to disabled.

UAT0.2 closed or partially closed the next safety layer:

- Adapter private/signed/order helpers block before transport when runtime policy disables them.
- Hyperliquid has a testable future-UAT1 read-only allowlist artifact.
- Representative bearer/API-key/secret/password/DB URL redaction is tested.
- Adapter-helper error messages redact obvious secrets before logging/raising.

UAT0.3 closes the UAT1 preflight baseline:

- Top-20 source/intersection resolver policy exists and is fixture-tested.
- Hyperliquid public read-only info types are allowlisted for future UAT1: `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- Runtime drawdown monitor policy/model exists and is fixture-tested from caller-supplied observed equity.
- UAT1 public read-only connectivity preflight was satisfied and UAT1 has now completed under strict constraints.

Remaining blockers before UAT3 include sandbox account drawdown feed wiring, UAT-specific risk/kill-switch/audit visibility verification, and sandbox lifecycle verification. UAT2 implementation remains future work but its start blockers are closed by UAT1.1.

## UAT1 / UAT1.1 Result

UAT1 public read-only connectivity is complete:

- Explicit UAT1 public-read-only network mode was required before network access.
- Hyperliquid public `info` endpoint behavior was verified for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- CoinGecko public markets data was used as a no-key top-volume source.
- The top-20 source list resolved to 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets in the generated UAT1 report.
- No API keys, private endpoints, signed endpoints, order endpoints, order submissions, paper/live behavior, Money Flow live strategy evaluation, evidence packs, or live artifacts were used or created.

UAT1.1 shadow readiness is complete:

- Model/report-only shadow signal audit records exist for future no-trade / would-trade / risk-block inspection.
- Operator-visible shadow drawdown state exists and is labeled `shadow_simulated_drawdown` / `not_live_account_drawdown`.
- UAT1 universe snapshot loading is available for UAT2.
- Representative API-error and structured-log redaction verification exists.
- UAT2 shadow strategy run may proceed as a future no-order phase.

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
