# UAT Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT validates plumbing and behavior. It does not prove profitability.

Current status: UAT0 safety/security/runtime audit is complete, UAT0.1 API auth/authz plus runtime lockout hardening is complete, UAT0.2 adapter runtime-policy / read-only allowlist / representative redaction hardening is complete, UAT0.3 top-20 universe / drawdown readiness preflight is complete, UAT1 public read-only connectivity / top-20 universe resolution is complete, UAT1.1 shadow readiness is complete, UAT2 bounded no-order shadow strategy observation is complete, UAT2.1 dashboard visualization is complete, and UAT3.0 sandbox-order design/readiness is complete. UAT3.1 actual sandbox order submission remains blocked.

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

UAT2 shadow reports compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## UAT0 - Safety / Security / Runtime Hardening

Objective: make the platform safe enough to connect to sandbox/read-only systems later.

Status: audit complete; UAT0.1 closed the P0 API auth/authz and central runtime-policy baseline; UAT0.2 closed the adapter-level runtime-policy baseline and added a Hyperliquid future-UAT1 read-only allowlist artifact; UAT0.3 added top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 later completed the public-read-only connectivity verification.

Allowed behavior: config hardening, auth review, secret hygiene, mode gating, risk/drawdown visibility, kill-switch verification, audit checks, tests, docs.

Forbidden behavior: exchange calls, private endpoints, signed endpoints, order endpoints, sandbox orders, paper trades, live trades.

Success criteria: UAT0 blocker checklist is closed or explicitly accepted by founder.

Likely files/modules: `core/config/`, `apps/api/`, `services/risk/`, `services/execution/`, dashboard docs, operational docs.

Required docs/tests: security/runtime tests, no-secret tests, mode-gating tests, operator runbook.

## UAT1 - Top-20 Universe + Read-Only Venue/Market Metadata

Objective: build the top-20 supported-asset observation universe and verify sandbox/testnet or public read-only market metadata after UAT0 blockers are closed.

Status: complete. UAT1 verified allowed public Hyperliquid info types, fetched a no-key public top-volume source, resolved 15 included Hyperliquid USDC perpetual observation candidates and 5 excluded assets in the generated report, and kept all assets observation-only.

Allowed behavior: fetch public market metadata, fetch public top-20 volume list from a trusted source, intersect top-20 with selected venue-supported assets, verify symbol mapping, verify public read-only market data paths.

Forbidden behavior: private endpoints, signed endpoints, order endpoints, paper trades, live trades.

Success criteria: read-only lifecycle works, logs are sanitized, mode gating is proven.

Likely files/modules: exchange adapters, config, runtime sessions, market identity, symbol mapping.

Required docs/tests: read-only adapter tests, secret hygiene tests, sandbox runbook.

## UAT2 - Shadow Strategy Run Across Top-20 Universe

Objective: observe signals and would-trade decisions across the top-20 supported-asset universe without order submission.

Status: complete. UAT2 ran a bounded no-order shadow evaluation over the UAT1 Hyperliquid observation universe using public read-only candles and shadow audit records only. UAT2.1 then added the review-only dashboard visualization for the UAT2 summary JSON.

Allowed behavior: shadow signal generation, would-trade logging, compare `next_candle_open`, compare `next_candle_close`, no-trade logging, risk observation, dashboard/operator inspection.

Forbidden behavior: order submission, live-capital paths, auto-submit.

Success criteria: signals are explainable, gated, auditable, and safe under runtime failures. UAT2 produced 45 shadow audit records across 15 symbols and 3 sleeves, with 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked` records.

Likely files/modules: strategy runtime, API inspection, dashboard.

Required docs/tests: shadow-mode tests, decision/audit tests, dashboard labeling tests. UAT2.1 covers the current dashboard visualization layer and keeps UAT3 approval readiness informational only.

## UAT2.1 - Dashboard Visualization + Founder Approval Readiness Pack

Objective: make the UAT2 shadow run visually reviewable without enabling orders or approval actions.

Status: complete. The static dashboard has a UAT2 Shadow Run view that loads `docs/uat2_shadow_strategy_top20_observation_summary.json`, displays summary cards, a filterable signal matrix, would-open records, no-trade reason breakdowns, the ETH evidence-candidate card, timing assumptions, shadow drawdown, boundary flags, and UAT3 blockers.

Allowed behavior: local dashboard visualization, manual JSON loading, founder/operator review, docs/tests.

Forbidden behavior: order submission, executable approvals, paper trades, live trades, private/signed endpoints, API keys, routing expansion, Money Flow rule changes.

Success criteria: the founder can review the UAT2 shadow run and UAT3.1 blockers while seeing that would-open records are not orders and that actual sandbox order submission remains blocked.

Likely files/modules: `apps/dashboard/`, `docs/uat2_1_dashboard_visualization_and_approval_readiness.md`, operational docs.

Required docs/tests: dashboard static asset tests, UAT2.1 visualization tests, operational-doc current-state tests.

## UAT3.0 - Sandbox Order Design + Approval/Lifecycle Readiness

Objective: define the future approval-gated sandbox-order scope, lifecycle, and safety gates without submitting orders.

Status: complete. The initial future sandbox subset is Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only. The founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labels, submit-lease / duplicate-prevention requirements, approval scope, risk gates, and dashboard readiness are documented.

Allowed behavior: design/reporting, fixture/stub thinking, dashboard readiness panel, tests, docs.

Forbidden behavior: actual sandbox order submission, live endpoints, private/signed endpoint calls, API-key use, executable approvals, order intents, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: the founder can see exactly what UAT3.1 would require before any sandbox order.

Likely files/modules: `docs/uat3_0_sandbox_order_design_and_readiness.md`, `apps/dashboard/`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0 report tests, dashboard no-order-control tests, operational-doc current-state tests.

## UAT3.1 - First Approval-Gated Sandbox Order

Objective: test one tiny approval-gated sandbox/testnet order only after all UAT3.0 blockers are closed and explicit founder/operator approval authorizes actual sandbox submission.

Status: blocked.

Allowed behavior: explicitly approved tiny sandbox/testnet orders for a small operator-approved subset, starting with Hyperliquid ETH `sleeve_1h`.

Forbidden behavior: live endpoints, real-capital paper trading, unrestricted automation, route expansion, automatic top-20 order submission.

Success criteria: submit, reject, cancel, fill, uncertainty, and reconcile paths are safe and auditable against sandbox/testnet account truth.

Likely files/modules: execution service, exchange adapter, order lifecycle, approvals, runtime policy, risk, dashboard.

Required docs/tests: sandbox lifecycle tests, duplicate-prevention tests, sandbox approval tests, sandbox drawdown feed tests, artifact-labeling tests.

## UAT3 - Approval-Gated Sandbox Orders

Objective: test sandbox order lifecycle only after UAT0-UAT2 pass and explicit founder/operator approval accepts sandbox-order design scope.

Status: split into UAT3.0 design/readiness complete and UAT3.1 actual sandbox submission blocked. UAT2 did not clear sandbox order execution; it only completed no-order shadow observation.

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
