# UAT Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

UAT validates plumbing and behavior. It does not prove profitability.

Current status: UAT0 safety/security/runtime audit is complete, UAT0.1 API auth/authz plus runtime lockout hardening is complete, UAT0.2 adapter runtime-policy / read-only allowlist / representative redaction hardening is complete, UAT0.3 top-20 universe / drawdown readiness preflight is complete, UAT1 public read-only connectivity / top-20 universe resolution is complete, UAT1.1 shadow readiness is complete, UAT2 bounded no-order shadow strategy observation is complete, UAT2.1 dashboard visualization is complete, UAT3.0 sandbox-order design/readiness is complete, UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete, UAT3.0.2 sandbox gate integration dry-run / policy hardening is complete, UAT3.0.3 sandbox gate wiring / label-enforcement hardening is complete, UAT3.0.4 sandbox private read-only drawdown readiness is complete, UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete, UAT3.0.6 sandbox submit path dry-run wiring is complete, UAT3.1 first sandbox/testnet lifecycle probe is complete, UAT3.2 fixed-key preflight / second sandbox lifecycle attempt is complete as blocked before order transport, UAT3.3 Hyperliquid account-targeting / precision hardening is complete with a later successful follow-up lifecycle, UAT3.4 fixed-target sandbox routing / routed-order ledger is complete, UAT4.0 read-only dashboard/chart cockpit is complete, and UAT4.1 exchange-style dashboard redesign is complete. Additional sandbox orders require separate approval.

## Frozen Observation Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

- Hyperliquid ETH USDC perpetual.
- `sleeve_1h`.
- Current baseline Money Flow rules.
- Observation / shadow first.
- No additional exchange order submission until a later explicitly gated UAT phase.

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

## UAT3.0.1 - Sandbox Runtime / Approval / Risk Readiness Hardening

Objective: convert UAT3.0 design requirements into fixture-testable readiness primitives without enabling actual sandbox order submission.

Status: complete. Fail-closed sandbox runtime policy, sandbox artifact label validation, actual-submission approval scope validation, sandbox risk gate evaluator, sandbox drawdown feed fixture, and submit-lease duplicate-prevention fixture checks exist and are tested. Dashboard UAT view shows fixture/readiness status.

Allowed behavior: fixture/stub validation, docs, dashboard readiness labels, tests.

Forbidden behavior: actual sandbox order submission, live endpoints, private/signed/order endpoint calls, API-key use, executable approvals, real order intents, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: UAT3.1 blockers are more precise and readiness primitives fail closed without creating artifacts.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md`, `apps/dashboard/`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.1 sandbox readiness tests, dashboard no-order-control tests, operational-doc current-state tests.

## UAT3.0.2 - Sandbox Gate Integration Dry-Run + Policy Hardening

Objective: harden UAT3.0.1 fixture primitives and combine them into one dry-run sandbox gate preflight without enabling actual sandbox order submission.

Status: complete. Sandbox risk gates now propagate all runtime-policy blockers, non-positive sandbox numeric values are explicitly rejected, and the unified dry-run preflight evaluates runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status.

Allowed behavior: fixture-only integration checks, reason-code hardening, docs, dashboard readiness labels, tests.

Forbidden behavior: actual sandbox order submission, live endpoints, private/signed/order endpoint calls, API-key use, executable approvals, real order intents, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: future UAT3.1 submit path remains blocked unless all runtime, approval, risk, drawdown, artifact-label, and submit-preflight gates pass and founder actual-submission approval exists.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_2_sandbox_gate_integration_dry_run.md`, `apps/dashboard/`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.2 sandbox dry-run preflight tests, dashboard no-order-control tests, operational-doc current-state tests.

## UAT3.0.3 - Sandbox Artifact Label Enforcement + Executable Gate Wiring Dry-Run

Objective: enforce sandbox artifact labels through dry-run boundary helpers and compose executable-gate readiness checks without enabling actual sandbox order submission.

Status: complete. Sandbox artifact boundary validators now cover persistence, API serialization, dashboard display, and report generation helpers. A dry-run executable gate service composes runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks into one side-effect-free result.

Allowed behavior: fixture-only boundary checks, dry-run gate wiring, reason-code hardening, docs, dashboard readiness labels, tests.

Forbidden behavior: actual sandbox order submission, live endpoints, private/signed/order endpoint calls, API-key use, executable approvals, real order intents, prepared orders, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: future UAT3.1 submit path remains blocked unless sandbox labels, approval, risk, drawdown, submit-lease, runtime, real submit path, and founder actual-submission approval gates all pass.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md`, `apps/dashboard/`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.3 sandbox gate wiring tests, dashboard no-order-control tests, operational-doc current-state tests.

## UAT3.0.4 - Sandbox Private Read-Only Drawdown Feed + Credential Boundary Preflight

Objective: define and test fail-closed sandbox/testnet private read-only account-state and drawdown readiness without using credentials unless explicit approval exists.

Status: complete. Private read-only sandbox account policy, required credential approval text, credential-boundary validation, redaction helpers, endpoint category separation, and sandbox account drawdown feed modeling exist. Explicit private-read-only credential approval was not present, so no API keys were used and no private endpoints were called.

Allowed behavior: fixture-only policy validation, credential redaction checks, private read-only endpoint classification, sandbox account drawdown feed modeling, docs, tests.

Forbidden behavior: order submission, cancel, amend, retry, live endpoints, unapproved API-key use, executable approvals, real order intents, prepared orders, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: future UAT3.1 remains blocked unless private read-only credential approval exists, live-fed sandbox account drawdown is verified, and all sandbox order gates are separately wired and approved.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_4_sandbox_private_read_only_drawdown.md`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.4 private read-only sandbox drawdown tests, operational-doc current-state tests, review-bundle hygiene checks.

## UAT3.0.5 - Sandbox/Testnet Private Read-Only Credential + Drawdown Feed Verification

Objective: validate the explicit private-read-only approval boundary, sandbox/testnet credential environment boundary, and sandbox account-state drawdown-feed parsing without submitting orders or calling order-capable endpoints.

Status: complete. The exact founder/operator private-read-only approval text is present, sandbox/testnet credential env checks exist, live Hyperliquid base URLs are blocked, and Hyperliquid sandbox account-state payload parsing can build a not-live-account drawdown feed. The approved rerun used the Hyperliquid testnet base URL for one read-only account-state request, returned HTTP 200, and produced `sandbox_drawdown_feed_live_fed_verified`. No API key/private key was sent and no order endpoint was called.

Allowed behavior: approval-text validation, sandbox/testnet env boundary checks, redaction tests, fixture account-state parsing, no-order endpoint lockout verification, docs, tests.

Forbidden behavior: order submission, cancel, amend, retry, live endpoints, live API-key use, executable approvals, real order intents, prepared orders, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: future UAT3.1 remains blocked unless all sandbox order gates are separately wired and approved; private read-only live-fed sandbox account drawdown is now verified for the UAT3.0.5 account-state boundary.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.5 sandbox private read-only drawdown verification tests, operational-doc current-state tests, review-bundle hygiene checks.

## UAT3.0.6 - Sandbox Submit Path Dry-Run Wiring + Executable Gate Integration

Objective: wire the future sandbox submit path in dry-run mode without submitting orders or creating real execution artifacts.

Status: complete. A non-persistent sandbox submission plan and dry-run submit gate chain now compose runtime policy, founder actual-submission approval status, sandbox artifact labels, approval scope validation, live-fed sandbox drawdown status, risk gates, submit-lease duplicate prevention, and adapter endpoint classification. The future endpoint category is classified as `sandbox_order_submission`, but transport is not invoked and `calls_exchange=false`.

Allowed behavior: dry-run plan construction, fixture/live-fed status consumption, gate-chain integration checks, reason-code reporting, docs, tests.

Forbidden behavior: order submission, cancel, amend, retry, live endpoints, live API-key use, executable approvals, real order intents, prepared orders, submitted orders, paper trades, live trades, route expansion, automatic top-20 order submission.

Success criteria: future UAT3.1 remains blocked unless actual-submission approval exists, live-fed sandbox drawdown is current, approval/risk/submit-lease/artifact-label/endpoint gates pass, and a later explicit phase enables actual sandbox/testnet transport.

Likely files/modules: `services/uat/sandbox.py`, `docs/uat3_0_6_sandbox_submit_path_dry_run_wiring.md`, operational docs, Obsidian notes.

Required docs/tests: UAT3.0.6 sandbox submit path dry-run tests, operational-doc current-state tests, review-bundle hygiene checks.

## UAT3.1 - First Approval-Gated Sandbox Order

Objective: test one tiny approval-gated sandbox/testnet order only after all UAT3.0 blockers are closed and explicit founder/operator approval authorizes actual sandbox submission.

Status: complete. Exact founder/operator approval was present, the UAT3.0.6 gate chain was used, and exactly one Hyperliquid testnet ETH post-only limit attempt under 10 USDC notional was made. Hyperliquid rejected the attempt with a sanitized user/API-wallet-not-found response, no cancel was required, and reconciliation found no open order. No production execution artifact, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.

Allowed behavior: explicitly approved tiny sandbox/testnet orders for a small operator-approved subset, starting with Hyperliquid ETH `sleeve_1h`.

Forbidden behavior: live endpoints, real-capital paper trading, unrestricted automation, route expansion, automatic top-20 order submission.

Success criteria: the first submit/reject/reconcile path is safe and auditable against sandbox/testnet account truth. Accepted/open -> cancel lifecycle coverage remains a future separately approved UAT3.2 candidate after sandbox account/API-wallet configuration is reviewed.

Likely files/modules: execution service, exchange adapter, order lifecycle, approvals, runtime policy, risk, dashboard.

Required docs/tests: sandbox lifecycle tests, duplicate-prevention tests, sandbox approval tests, sandbox drawdown feed tests, artifact-labeling tests.

## UAT3.2 - Fixed-Key Preflight + Second Approval-Gated Sandbox/Testnet Lifecycle Attempt

Objective: verify the fixed Hyperliquid testnet key/account/API-wallet setup before a second one-shot sandbox lifecycle attempt.

Status: complete as blocked before order transport. Exact founder/operator approval was present, the runner verified testnet endpoint identity and live-fed sandbox drawdown, and fixed-key account/API-wallet readiness blocked before `/exchange` because the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient. Order attempt count was `0`; no order/cancel/amend/retry endpoint was called.

Allowed behavior: approval-text validation, sandbox/testnet account/API-wallet readiness, public read-only market data for nonmarketable order shaping, private read-only sandbox account/drawdown checks, and exactly one order attempt only if all gates pass.

Forbidden behavior: live endpoints, live API keys, paper trades, live trades, broad top-20 order submission, repeated orders, fanout, SOR, target reselection, route executor behavior, production auto-submit, Money Flow rule changes, and evidence packs.

Success criteria: fixed-key readiness must pass before any second order transport. The recorded UAT3.2 run did not meet that gate and therefore correctly blocked.

Likely files/modules: `services/uat/sandbox_order.py`, `scripts/run_uat32_second_sandbox_order.py`, `docs/uat3_2_second_sandbox_order_attempt.md`, operational docs, Obsidian notes.

Required docs/tests: UAT3.2 fixed-key readiness tests, one-attempt gating tests, secret-redaction tests, operational-doc current-state tests, review-bundle hygiene checks.

## UAT3.3 - Hyperliquid Account Targeting + Tick/Lot Precision + One Sandbox Lifecycle Attempt

Objective: fix Hyperliquid account-targeting semantics and tick/lot precision before a one-shot sandbox lifecycle attempt.

Status: complete. Founder/operator approval was present; normal master/user mode now omits `vaultAddress`; subaccount/vault mode uses only the configured explicit target; API-wallet signer identity is separate from target account identity; ETH order price/size formatting follows Hyperliquid `szDecimals`, five-significant-figure, and perp max-decimal rules; and UAT-universe precision validation is reported. The recorded UAT3.3 attempt reached `/exchange` after gates passed and was rejected by minimum order value truth; a later founder-approved follow-up verified accepted/open -> cancel -> reconcile with no open order remaining.

Allowed behavior: approval-text validation, sandbox/testnet account targeting, public read-only market data for precision/nonmarketable order shaping, private read-only sandbox account/drawdown checks, UAT-universe precision validation, and exactly one order attempt only if all gates pass.

Forbidden behavior: live endpoints, live API keys, paper trades, live trades, broad top-20 order submission, repeated orders, fanout, SOR, target reselection, route executor behavior, production auto-submit, Money Flow rule changes, and evidence packs.

Success criteria: account targeting and precision must be unambiguous before any order transport. UAT3.3 met those gates, and the later follow-up validated the corrected route lifecycle without live endpoints or secret exposure.

Likely files/modules: `services/exchange/hyperliquid/precision.py`, `services/uat/sandbox_order.py`, `scripts/run_uat33_hyperliquid_precision_order.py`, `docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md`, operational docs, Obsidian notes.

Required docs/tests: UAT3.3 account-targeting tests, Hyperliquid precision tests, one-attempt gating tests, secret-redaction checks, operational-doc current-state tests, review-bundle hygiene checks.

## UAT3.4 - Production-Like Sandbox Routing Pipeline + Routed Orders Ledger

Objective: operationalize the successful Hyperliquid testnet ETH route as a repeatable fixed-target sandbox routing pipeline with routed-order ledger visibility and unified-mode equity compatibility.

Status: complete. UAT3.4 uses `fixed_target_hyperliquid_testnet_eth`, account role `user`, `vaultAddress` omitted, standard perp clearinghouse equity selected for the active route, and unified/portfolio spot-clearinghouse USDC fallback preserved for compatibility. The approved run made exactly one ETH post-only testnet attempt under the 20 USDC cap, received accepted/open, canceled successfully, and reconciled to no open order. A routed-order ledger summary is available to the dashboard. UAT3.5 remains blocked because current Hyperliquid testnet metadata did not support precision validation for every UAT observation-universe symbol.

Allowed behavior: fixed-target Hyperliquid testnet ETH sandbox lifecycle probes under explicit approval, routed-order ledger reporting, dashboard ledger visibility, standard/unified equity-source reporting, cancel-if-open, and reconciliation.

Forbidden behavior: live endpoints, live API keys, paper trades, live trades, broad top-20 order submission, repeated unbounded orders, fanout, SOR, CBBO, best-binding selection, target reselection, route executor behavior, production auto-submit, Money Flow rule changes, and evidence packs.

## UAT4.0 - Live UAT Trading Dashboard / Chart Cockpit

Objective: dashboard phase requested by founder for UAT review, implemented as read-only local chart/watchlist/routed-ledger visualization.

Status: complete. The static dashboard now has a `UAT Chart Cockpit` tab sourced from committed UAT2 shadow and UAT3.4 routed-order summary JSON. It shows watchlist, market-data coverage, chart snapshots, indicator labels, shadow/sandbox lifecycle markers, active route/equity status, routed-order filters, and safety/no-order labels.

Implemented capabilities: local static chart snapshots for watched pairs, green shadow/sandbox-entry markers, red sandbox-cancel markers, routed orders tab, observed watchlist, market-data coverage, EMA5 / EMA10 / SMA20 / RSI / MACD labels, UAT order lifecycle overlay, sandbox/not-live labels, and no paper/live confusion.

Deferred capabilities: public-read-only live refresh and richer charting can be scoped as UAT4.2. Private/signed/order endpoints, API keys, and order controls remain forbidden.

## UAT4.1 - Exchange-Style Dashboard Redesign + DESIGN.md Rebuild

Objective: rebuild the UAT dashboard around a usable exchange-like trading workstation layout without adding any order controls or exchange calls.

Status: complete. The static dashboard now uses a compact top bar, persistent safety banner, left observation-only market rail, central chart cockpit, right order-book / market-info / signal-context / risk-context rail, and bottom blotter tabs for Routed Orders, Shadow Signals, Balances / Positions, Lifecycle, and Audit / Logs. The canonical dashboard design doc is `apps/dashboard/DESIGN.md`; root `DESIGN.md` is only a pointer.

Allowed behavior: local dashboard visualization, committed UAT2/UAT3.4 summary loading, marker/indicator/routed-ledger organization, no-order safety labeling, docs, and tests.

Forbidden behavior: order buttons, cancel/retry/amend/approval controls, paper/live toggles, private/signed/order endpoints, exchange API keys, live trading, paper trading, Money Flow rule changes, smart routing/SOR/fanout/target reselection, broad top-20 orders, production auto-submit, and evidence packs.

Deferred capabilities: UAT4.2 may scope public-read-only live refresh, a real chart library, and richer public market-data coverage while preserving no-key/no-private/no-signed/no-order boundaries.

## UAT3.2 - Additional Sandbox Lifecycle Testing

Objective: only if separately approved, test accepted/open -> cancel lifecycle after the Hyperliquid testnet account/API-wallet configuration is corrected.

Status: not approved.

Allowed behavior: one separately approved sandbox/testnet lifecycle probe at a time with explicit scope and the same gate chain.

Forbidden behavior: live endpoints, real-capital paper trading, unrestricted automation, broad top-20 order submission, repeated orders, route expansion, production auto-submit, Money Flow performance validation, or strategy-rule changes.

Success criteria: accepted/open/rejected/canceled/reconciled lifecycle states remain bounded, labeled sandbox/not-live/not-paper, and create no production execution artifacts outside the approved UAT scope.

## UAT3 - Approval-Gated Sandbox Orders

Objective: test sandbox order lifecycle only after UAT0-UAT2 pass and explicit founder/operator approval accepts sandbox-order design scope.

Status: UAT3.0 design/readiness is complete and UAT3.1 first sandbox/testnet lifecycle probe is complete. UAT2 did not clear sandbox order execution; it only completed no-order shadow observation. UAT3.1 was a separate one-shot founder-approved sandbox/testnet plumbing probe.

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

Paper trading is not approved. Live trading is not approved. Additional exchange order submission is not approved before explicit later UAT scope.
