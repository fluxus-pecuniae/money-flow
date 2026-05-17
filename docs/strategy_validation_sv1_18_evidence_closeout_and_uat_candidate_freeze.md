> Historical note.
> This report is retained for audit/history.
> Current truth lives in [[00_Money_Flow_Command_Center]] and the latest PT-RT / SV / audit docs.
> Do not use this file as current operating instructions unless a current-phase note links to it explicitly.

# SV1.18 Evidence Credibility Closeout And UAT Candidate Freeze

Recorded at: `2026-05-09T12:32:14Z`

Status: `evidence_cycle_closed_uat0_candidate_ready_for_founder_decision`

SV1.18 closes the current Hyperliquid Strategy Validation evidence cycle. It does not change Money Flow rules, does not approve paper trading, does not approve live trading, does not call exchanges, and does not create execution artifacts.

## Evidence Credibility Closeout

Current evidence does not prove edge. Backtest and replay evidence is useful for research ranking, diagnostics, and operational planning, but it is incomplete for performance claims.

The only scenario suitable for tightly scoped UAT observation is ETH `sleeve_1h` using current baseline Money Flow rules on Hyperliquid USDC perpetual data. This is the least-bad and strongest currently observed scenario, not a production strategy.

Excluded from this UAT scope:

- `sleeve_15m`: excluded because current evidence is broadly weak and shows overtrading / cost drag.
- `sleeve_4h`: excluded because current evidence is broadly weak and shows slow or late invalidation in the tested window.
- BTC `sleeve_1h` and SOL `sleeve_1h`: excluded because results are mixed / weaker than ETH.
- Lower-RSI variants: excluded because true replay variants did not beat the ETH `sleeve_1h` baseline.
- Market-structure variants: excluded because they remain research diagnostics or replay-only experiments, not production rules.
- Aster, Binance, OKX, Coinbase, and Kraken: excluded from this UAT scope. Cross-venue evidence remains deferred.

Known evidence limitations:

- Short public campaign window.
- Hyperliquid-only USDC perpetual evidence.
- No funding model.
- No liquidation model.
- No production exchange margin model.
- No order book fill model.
- No partial fill model.
- No latency model.
- No exchange outage model.
- No live reject / cancel / fill reconciliation behavior.
- No portfolio-level capital constraint model across BTC / ETH / SOL.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Frozen Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Strategy rules | Current baseline Money Flow rules |
| Evidence basis | Hyperliquid public-candle Strategy Validation research |
| Capital model in evidence | `dynamic_equity_pct` research simulation |
| Position behavior for UAT | Observation / shadow first |
| Execution in SV1.18 | None |
| Execution before later gate | Forbidden |
| Status | UAT observation candidate only |

This candidate is not a production strategy. It is not paper-trading authorization. It is not live-trading authorization.

## Evidence Basis For The Candidate

SV1.17 full-suite true replay results identify ETH `sleeve_1h` baseline as the only above-starting-equity pocket in the BTC/ETH/SOL x 15m/1h/4h matrix.

| Scenario | Trades | Ending Equity | Net Account PnL | Mark-To-Market Max Drawdown | Profit Factor |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH `sleeve_1h` baseline | 117 | `$11,388.93` | `$1,388.93` | `$1,753.27` | `1.22` |

These are research observations. They are not performance validation for real trading.

## Excluded Candidates

| Candidate | Reason Excluded |
| --- | --- |
| 15m sleeve | Weak / negative evidence, overtrading, and cost drag. |
| 4h sleeve | Weak / negative evidence, slow / late invalidation in the tested window. |
| BTC 1h | Mixed / weaker than ETH 1h baseline. |
| SOL 1h | Mixed / weaker than ETH 1h baseline. |
| Lower-RSI variants | Did not beat ETH 1h baseline in true replay. |
| Market-structure variants | Diagnostic / replay-only and not production rules. |
| Aster / Binance | Later comparative candidates, not current UAT scope. |
| OKX / Coinbase / Kraken | Source, trade-count, or public-history policy gaps remain unresolved. |

## SV1.17 Outcome Taxonomy Clarification

SV1.17 full-suite replay rows that improved weak baselines should not be read as UAT candidates when the scenario still ended below starting equity.

Safer labels for future reports:

- `loss_reduced_but_still_below_starting_equity`
- `lower_drawdown_but_lower_return`
- `no_op_no_replay_entries`
- `deteriorated_vs_baseline`
- `damages_eth_1h_control_pocket`

No SV1.17 variant is frozen for UAT. The ETH `sleeve_1h` current-rule baseline remains the control pocket.

## UAT Purpose

UAT is plumbing and behavior validation. It is not performance validation.

UAT should answer:

- Does the strategy produce live or near-live signals at the expected frequency?
- Are signals explainable to an operator?
- Does the platform create the correct would-trade decisions in shadow mode?
- Are risk checks visible before any later sandbox order phase?
- Are approval gates enforced?
- Are orders gated from accidental submission?
- Does exchange lifecycle handling work in a later sandbox phase?
- Are rejects, cancels, fills, and reconciliation handled safely in a later sandbox phase?
- Are logs and audits clear?
- Are drawdown alarms visible?
- Does the operator understand what is happening?

## UAT Pass Criteria

| Area | Pass Criteria |
| --- | --- |
| Runtime | Strategy process runs without crashing and enters a safe state on failures. |
| Signals | Signals are generated, timestamped, logged, and explainable. |
| Orders | No unapproved order submission path is reachable. |
| Capital safety | No live-capital path is reachable from UAT scope. |
| Approvals | Approval gates work and remain visible. |
| Risk | Risk limits and drawdown monitoring are visible. |
| Inspection | Operator can inspect signal reasons, state, and audit history. |
| Lifecycle | Later sandbox rejects, cancels, fills, and reconciliation are handled safely. |
| Duplicate prevention | No duplicate unintended orders can be produced. |
| Kill switch | Disable / kill switch stops strategy action paths. |
| Audit | Audit trail is clear and contains no secrets. |

## UAT Fail Criteria

| Area | Fail Criteria |
| --- | --- |
| Orders | Strategy can submit without explicit approval. |
| Lifecycle | Order lifecycle cannot reconcile safely. |
| Duplicate prevention | Duplicate orders occur or uncertainty handling retries unsafely. |
| Risk | Drawdown is not monitored or visible. |
| Reject handling | Exchange reject causes unsafe retry or unclear state. |
| Explainability | Operator cannot explain a signal or would-trade action. |
| Endpoint safety | Live endpoint can be reached accidentally from sandbox mode. |
| Secrets | Secrets appear in logs, reports, or UI. |
| Runtime | System crashes without a safe state. |
| Dashboard | Dashboards mislabel research, UAT, paper, or live state. |

## UAT0 Safety / Security / Runtime Hardening

| Blocker | SV1.18 Status | Required Before |
| --- | --- | --- |
| API authentication / authorization readiness | `needs_verification` | Any operator-facing UAT surface. |
| Key and secret hygiene | `needs_verification` | Any sandbox credential setup. |
| No secrets in logs | `needs_verification` | Any exchange connectivity. |
| Fail-safe live/demo mode separation | `needs_verification` | Any sandbox connectivity. |
| Sandbox/testnet environment gating | `missing_or_unverified` | Any exchange adapter use. |
| Risk limit enforcement | `needs_verification` | Shadow decisions and sandbox orders. |
| Drawdown calculation and monitoring | `needs_verification` | Shadow decisions and sandbox orders. |
| Kill switch / disable switch | `needs_verification` | Shadow decisions and sandbox orders. |
| Debug stack traces not exposed to users | `needs_verification` | Any non-local UI/API use. |
| Audit logging | `partially_implemented_needs_uat_verification` | Shadow decisions and sandbox orders. |
| Operator confirmation gates | `partially_implemented_needs_uat_verification` | Any sandbox order path. |
| Duplicate order prevention | `partially_implemented_needs_uat_verification` | Any sandbox order path. |
| Submit lease / uncertainty handling remains active | `partially_implemented_needs_uat_verification` | Any sandbox order path. |
| No private endpoint calls before explicit UAT phase | `process_gate_required` | UAT1. |
| No live endpoint access in sandbox mode | `missing_or_unverified` | UAT1. |

## UAT Roadmap

| Phase | Objective | Allowed Behavior | Forbidden Behavior | Success Criteria | Likely Files / Modules | Docs / Tests Needed |
| --- | --- | --- | --- | --- | --- | --- |
| UAT0 - Safety / Security / Runtime Hardening | Make the platform safe enough to connect to a sandbox later. | Config hardening, auth review, risk/drawdown visibility, kill-switch verification, audit checks. | Exchange calls, private endpoints, signed endpoints, orders. | UAT0 blocker checklist is closed or explicitly accepted by founder. | `core/config/`, `apps/api/`, `services/execution/`, `services/risk/`, dashboard docs. | Security/runtime tests, no-secret tests, mode-gating tests, operator runbook. |
| UAT1 - Exchange Sandbox Read-Only Connectivity | Verify sandbox connectivity without order submission. | Sandbox/testnet read-only endpoints after explicit approval. | Order endpoints, live endpoints, private calls without UAT1 authorization. | Read-only lifecycle works, logs are sanitized, mode gating is proven. | Exchange adapters, config, runtime sessions. | Read-only adapter tests, secret hygiene tests, sandbox runbook. |
| UAT2 - Shadow Strategy Run, No Orders | Observe ETH `sleeve_1h` signals and would-trade decisions without submission. | Shadow signal generation, would-trade logging, risk observation. | Order intents submitted to an exchange, live-capital paths, auto-submit. | Signals are explainable, gated, auditable, and safe under runtime failures. | Strategy runtime, API inspection, dashboard. | Shadow-mode tests, decision/audit tests, dashboard labeling tests. |
| UAT3 - Approval-Gated Sandbox Orders | Test sandbox order lifecycle only after UAT0-UAT2 pass. | Explicitly approved small sandbox orders. | Live endpoints, automated unrestricted submission, route expansion. | Submit, reject, cancel, fill, and reconcile paths are safe and auditable. | Execution service, exchange adapter, order lifecycle, approvals. | Sandbox lifecycle tests, duplicate-prevention tests, operator approval tests. |
| UAT4 - Sandbox / Simulated Trading Review | Review sandbox behavior and decide whether more work is justified. | Founder review, incident review, runbook updates. | Claims of edge, production rollout, live trading. | Founder can decide whether to continue research, revise strategy, or stop. | Docs, reports, dashboard. | Founder review report and regression suite. |

## Boundary Confirmation

- `changes_production_money_flow_rules`: `false`
- `optimizes_parameters`: `false`
- `creates_live_artifacts`: `false`
- `creates_routing_artifacts`: `false`
- `calls_exchange_adapters`: `false`
- `uses_api_keys`: `false`
- `generates_evidence_packs`: `false`
- `approves_paper_trading`: `false`
- `approves_live_trading`: `false`

Paper trading remains deferred. Live trading remains deferred. Money Flow rules remain unchanged.

## Founder Decision Point

The founder can decide whether to proceed to UAT0. That decision should be based on accepting the evidence limitations and agreeing that UAT0 is safety, runtime, and operational hardening only.

Intentionally deferred:

- Paper-trading design.
- Live trading.
- Exchange order submission.
- Routing / SOR expansion.
- Cross-venue evidence.
- Lower-RSI or market-structure production rules.
- Funding, liquidation, full order-book, and portfolio-level simulation.
