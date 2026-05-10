# UAT Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT validates plumbing and behavior. It does not prove profitability.

Current status: UAT0 safety/security/runtime audit is complete, UAT0.1 API auth/authz plus runtime lockout hardening is complete, UAT0.2 adapter runtime-policy / read-only allowlist / representative redaction hardening is complete, and UAT0.3 top-20 universe / drawdown readiness preflight is complete. UAT1 public read-only connectivity may proceed under strict no-private/no-signed/no-order/no-API-key constraints.

## Frozen Observation Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

- Hyperliquid ETH USDC perpetual.
- `sleeve_1h`.
- Current baseline Money Flow rules.
- Observation / shadow first.
- No exchange order submission until a later explicitly gated UAT phase.

This is the evidence candidate, not the whole UAT observation universe.

## UAT Observation Universe Policy

Future UAT observation should cover the top 20 high-volume crypto assets supported by the selected UAT venue/environment. The top-20 universe validates platform behavior, no-trade reasoning, rejected-signal behavior, market metadata resolution, symbol mapping, venue support, risk visibility, shadow would-trade behavior, and dashboard/operator visibility.

Top-20 inclusion is not strategy approval. Unsupported or mismatched assets must be excluded with explicit reason codes.

Future UAT2 shadow reports must compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## UAT0 - Safety / Security / Runtime Hardening

Objective: make the platform safe enough to connect to sandbox/read-only systems later.

Status: audit complete; UAT0.1 closed the P0 API auth/authz and central runtime-policy baseline; UAT0.2 closed the adapter-level runtime-policy baseline and added a Hyperliquid future-UAT1 read-only allowlist artifact; UAT0.3 added top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 public read-only connectivity may proceed under strict constraints.

Allowed behavior: config hardening, auth review, secret hygiene, mode gating, risk/drawdown visibility, kill-switch verification, audit checks, tests, docs.

Forbidden behavior: exchange calls, private endpoints, signed endpoints, order endpoints, sandbox orders, paper trades, live trades.

Success criteria: UAT0 blocker checklist is closed or explicitly accepted by founder.

Likely files/modules: `core/config/`, `apps/api/`, `services/risk/`, `services/execution/`, dashboard docs, operational docs.

Required docs/tests: security/runtime tests, no-secret tests, mode-gating tests, operator runbook.

## UAT1 - Top-20 Universe + Read-Only Venue/Market Metadata

Objective: build the top-20 supported-asset observation universe and verify sandbox/testnet or public read-only market metadata after UAT0 blockers are closed.

Allowed behavior: fetch public market metadata, fetch public top-20 volume list from a trusted source, intersect top-20 with selected venue-supported assets, verify symbol mapping, verify public read-only market data paths.

Forbidden behavior: private endpoints, signed endpoints, order endpoints, paper trades, live trades.

Success criteria: read-only lifecycle works, logs are sanitized, mode gating is proven.

Likely files/modules: exchange adapters, config, runtime sessions, market identity, symbol mapping.

Required docs/tests: read-only adapter tests, secret hygiene tests, sandbox runbook.

## UAT2 - Shadow Strategy Run Across Top-20 Universe

Objective: observe signals and would-trade decisions across the top-20 supported-asset universe without order submission.

Allowed behavior: shadow signal generation, would-trade logging, compare `next_candle_open`, compare `next_candle_close`, no-trade logging, risk observation, dashboard/operator inspection.

Forbidden behavior: order submission, live-capital paths, auto-submit.

Success criteria: signals are explainable, gated, auditable, and safe under runtime failures.

Likely files/modules: strategy runtime, API inspection, dashboard.

Required docs/tests: shadow-mode tests, decision/audit tests, dashboard labeling tests.

## UAT3 - Approval-Gated Sandbox Orders

Objective: test sandbox order lifecycle only after UAT0-UAT2 pass.

Allowed behavior: explicitly approved tiny sandbox/testnet orders, starting with a small operator-approved subset.

Forbidden behavior: live endpoints, unrestricted automation, route expansion, automatic top-20 order submission.

Success criteria: submit, reject, cancel, fill, and reconcile paths are safe and auditable.

Likely files/modules: execution service, exchange adapter, order lifecycle, approvals.

Required docs/tests: sandbox lifecycle tests, duplicate-prevention tests, operator approval tests.

## UAT4 - Sandbox / Simulated Trading Review

Objective: review sandbox behavior and decide whether more work is justified.

Allowed behavior: founder review, incident review, runbook updates.

Forbidden behavior: claims of edge, production rollout, live trading.

Success criteria: founder can decide whether to continue research, revise strategy, or stop.

Likely files/modules: docs, reports, dashboard.

Required docs/tests: founder review report and regression suite.

## Standing UAT Boundary

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved before explicit UAT3 scope.
