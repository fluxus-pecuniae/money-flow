# UAT Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT validates plumbing and behavior. It does not prove profitability.

## Frozen Observation Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

- Hyperliquid ETH USDC perpetual.
- `sleeve_1h`.
- Current baseline Money Flow rules.
- Observation / shadow first.
- No exchange order submission until a later explicitly gated UAT phase.

## UAT0 - Safety / Security / Runtime Hardening

Objective: make the platform safe enough to connect to sandbox/read-only systems later.

Allowed behavior: config hardening, auth review, secret hygiene, mode gating, risk/drawdown visibility, kill-switch verification, audit checks, tests, docs.

Forbidden behavior: exchange calls, private endpoints, signed endpoints, order endpoints, sandbox orders, paper trades, live trades.

Success criteria: UAT0 blocker checklist is closed or explicitly accepted by founder.

Likely files/modules: `core/config/`, `apps/api/`, `services/risk/`, `services/execution/`, dashboard docs, operational docs.

Required docs/tests: security/runtime tests, no-secret tests, mode-gating tests, operator runbook.

## UAT1 - Exchange Sandbox Read-Only Connectivity

Objective: verify sandbox/testnet read-only connectivity after UAT0 passes.

Allowed behavior: explicitly approved sandbox/testnet read-only endpoint calls.

Forbidden behavior: order endpoints, live endpoints, private/signed calls not approved by UAT1.

Success criteria: read-only lifecycle works, logs are sanitized, mode gating is proven.

Likely files/modules: exchange adapters, config, runtime sessions.

Required docs/tests: read-only adapter tests, secret hygiene tests, sandbox runbook.

## UAT2 - Shadow Strategy Run, No Orders

Objective: observe ETH `sleeve_1h` signals and would-trade decisions without order submission.

Allowed behavior: shadow signal generation, would-trade logging, risk observation, dashboard/operator inspection.

Forbidden behavior: order submission, live-capital paths, auto-submit.

Success criteria: signals are explainable, gated, auditable, and safe under runtime failures.

Likely files/modules: strategy runtime, API inspection, dashboard.

Required docs/tests: shadow-mode tests, decision/audit tests, dashboard labeling tests.

## UAT3 - Approval-Gated Sandbox Orders

Objective: test sandbox order lifecycle only after UAT0-UAT2 pass.

Allowed behavior: explicitly approved small sandbox orders.

Forbidden behavior: live endpoints, unrestricted automation, route expansion.

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
