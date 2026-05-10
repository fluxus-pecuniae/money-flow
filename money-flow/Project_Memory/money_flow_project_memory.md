# Money Flow Project Memory

This is the canonical long-horizon strategic project memory. Repo operational docs remain implementation truth.

## Founder Vision

Money Flow is a strategy-first, mandate-driven trading platform. The goal is not to build a generic bot or fake smart router. The goal is to validate strategy behavior, make execution boundaries safe, and eventually operate a controlled multi-venue system only when evidence and operational controls justify it.

## Project Purpose

Money Flow combines:

- Money Flow strategy research.
- historical Strategy Validation.
- mandate/account/binding-aware planning and risk.
- controlled routing-assessment and recommendation workflow.
- approval-gated action hooks.
- submitted-order lifecycle and reconciliation truth.
- operator observability.
- future UAT/sandbox behavior validation.
- UAT0 safety/security/runtime readiness plus UAT0.1 API/runtime lockout, UAT0.2 adapter-policy/redaction hardening, UAT0.3 top-20 universe/drawdown readiness preflight, UAT1 public read-only connectivity/universe resolution, UAT1.1 shadow-readiness surfaces, UAT2 bounded no-order shadow observation, UAT2.1 dashboard visualization, UAT3.0 sandbox-order design/readiness, UAT3.0.1 sandbox runtime / approval / risk readiness hardening, UAT3.0.2 sandbox gate integration dry-run / policy hardening, UAT3.0.3 sandbox gate wiring / label-enforcement hardening, UAT3.0.4 sandbox private read-only drawdown readiness, and UAT3.0.5 sandbox/testnet private read-only drawdown verification.

## Platform Tracks Completed

| Track | Outcome |
| --- | --- |
| Phase 1-4 platform foundation | Domain/API/db/service scaffold, exchange/data/state foundation, indicators, Money Flow strategy family, planning/risk/execution substrate. |
| Phase 5-6 routing substrate | Non-executing assessment, route-readiness audit, recommendation, target choice, conversion, readiness, explicit same-target handoff, workflow inspection, submit uncertainty hardening. |
| Phase 7 controlled automation | Approval-gated same-target action hooks with exact-lineage safety proof. |
| Phase 8 operator observability | Read-only routed workflow/manual-resolution inspection and active submit-lease truth. |
| Strategy Validation SV1 | Hyperliquid evidence cycle from backtest truth through dynamic equity, diagnostics, replay experiments, and UAT candidate freeze. |

## Routing / SOR Status

The platform has a controlled routing substrate. It is not a full smart order router.

Deferred:

- best-binding selection.
- CBBO.
- venue ranking/scoring.
- fanout / split allocation.
- target reselection.
- route executor behavior.
- cross-binding / cross-venue recovery.
- broad auto-submit.

Routing expansion is not the current priority.

## Strategy Validation Timeline And Outcomes

| Range | Outcome |
| --- | --- |
| SV1.0-SV1.2.1 | Baseline backtest, fill timing, drawdown, window, coverage, and regime truth. |
| SV1.3-SV1.4.1 | Campaign/evidence-pack workflow and collision safety. |
| SV1.5-SV1.9.1 | Historical data/import/DB governance, schema gates, timestamp truth. |
| SV1.10-SV1.12.5.1 | Intended DB, Hyperliquid identity, public campaign import, repo/import closeout. |
| SV1.13-SV1.13.2 | First Hyperliquid public evidence and dynamic-equity sizing. |
| SV1.14-SV1.17 | Diagnostics, experiment methodology, rejected-signal replay, and full-suite true replay. |
| SV1.18-SV1.18.1 | Evidence credibility closeout, UAT candidate freeze, Obsidian coordination closeout. |

Current accepted interpretation:

- ETH `sleeve_1h` baseline is the strongest observed Hyperliquid public-candle candidate.
- 15m and 4h are weak and excluded from current UAT scope.
- BTC/SOL 1h are mixed/weaker and excluded from current UAT scope.
- Lower-RSI variants did not beat the ETH 1h baseline control pocket.
- Market-structure variants remain research-only.
- Current evidence does not prove future performance.

## Current UAT Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

- Venue: Hyperliquid.
- Product: USDC perpetual.
- Symbol: ETH.
- Component: `sleeve_1h`.
- Rules: current baseline Money Flow rules.
- Initial mode: observation / shadow first.
- Execution: none until later explicit UAT gate.

Excluded from current UAT:

- 15m.
- 4h.
- BTC 1h.
- SOL 1h.
- lower-RSI variants.
- market-structure variants.
- Aster / Binance / OKX / Coinbase / Kraken.
- cross-venue comparison.

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 / UAT1 / UAT1.1 / UAT2 / UAT2.1 / UAT3.0 / UAT3.0.1 / UAT3.0.2 / UAT3.0.3 / UAT3.0.4 / UAT3.0.5 Outcome

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT0.2 adapter runtime-policy, read-only allowlist, and representative redaction hardening is complete. UAT0.3 top-20 universe and drawdown readiness preflight is complete. UAT1 public read-only connectivity is complete. UAT1.1 shadow readiness is complete. UAT2 bounded no-order shadow observation is complete. UAT2.1 dashboard visualization is complete. UAT3.0 sandbox order design is complete. UAT3.0 sandbox-order readiness is documented. UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete. UAT3.0.2 sandbox gate integration dry-run / policy hardening is complete. UAT3.0.3 sandbox gate wiring / label-enforcement hardening is complete. UAT3.0.4 sandbox private read-only drawdown readiness is complete. UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete. UAT3.1 actual sandbox order submission remains blocked.

Closed by UAT0.1:

- Sensitive `/api/v1` routes require scoped bearer authentication.
- High-risk admin consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes.
- Test auth bypass is limited to `API_RUNTIME_MODE=test`.
- `RuntimeSafetyPolicy` exposes fail-safe defaults for paper trading, live trading, exchange order submission, and private exchange endpoints.

Closed or partially closed by UAT0.2:

- Adapter private/signed/order calls are guarded by runtime policy before transport.
- Public read-only adapter methods are classified.
- Hyperliquid has a future-UAT1 read-only allowlist artifact.
- Representative bearer/API-key/secret/password/DB URL redaction is tested.

Closed by UAT0.3:

- Fixture-tested top-20 resolver policy and Hyperliquid market-intersection logic.
- Hyperliquid public read-only info-type allowlist for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- Fixture-tested runtime drawdown monitor policy/model.
- UAT1 public read-only connectivity may proceed under no-private/no-signed/no-order/no-API-key constraints. This preflight condition was exercised by UAT1.

Closed by UAT1:

- Explicit public-read-only network mode is required before UAT1 public calls.
- Hyperliquid public `info` endpoint behavior is verified for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- CoinGecko public markets data was fetched without API keys as the top-volume source.
- The UAT1 report resolved 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets from the public top-20 source at run time.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, paper/live behavior, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT1.1:

- Representative structured application log/API error redaction is verified for UAT2; deployment-specific middleware/logging smoke tests remain before UAT3.
- Operator-visible shadow drawdown state exists for UAT2.
- A shadow signal audit surface exists for would-trade/no-trade/risk-block explainability.

Closed by UAT2:

- Explicit UAT2 shadow mode and public-read-only flags are required.
- The UAT1 universe snapshot was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- UAT2 created 45 shadow audit records: 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked`.
- ETH `sleeve_1h` produced `no_trade` with `macd_not_constructive`.
- UAT2 represented `next_candle_open` and `next_candle_close`; `same_candle_close_research_only` remained research-only.
- Shadow drawdown was labeled `shadow_simulated_drawdown` / `not_live_account_drawdown` and did not imply live account equity or performance.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were used or created.

Closed by UAT2.1:

- The existing static dashboard now has a UAT2 Shadow Run view that loads `docs/uat2_shadow_strategy_top20_observation_summary.json`.
- The dashboard shows UAT2 summary cards, a filterable 45-record signal matrix, would-open records, no-trade reason breakdowns, ETH `sleeve_1h` candidate truth, `next_candle_open` / `next_candle_close` timing status, `same_candle_close_research_only` research-only status, not-live-account shadow drawdown, UAT3 blockers, and forbidden-artifact boundary flags.
- UAT2.1 adds no interactive approval action and cannot enable order submission.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, signal events, order intents, prepared orders, execution readiness assessments, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were used or created.

Closed by UAT3.0:

- The future initial sandbox-order subset is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- The founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- The dashboard UAT view has an informational UAT3.0/UAT3.0.1/UAT3.0.2/UAT3.0.3 design/readiness panel.
- UAT3.1 actual sandbox order submission remains blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.1:

- Fail-closed `SandboxRuntimePolicy` fixture/readiness helper exists and defaults sandbox submission, private endpoints, live endpoint access, paper/live trading, and generic exchange order submission to disabled.
- Sandbox artifact label validation exists and fails unsafe/missing sandbox/testnet/not-live/not-paper labels.
- Future UAT3.1 actual-submission approval wording is separate from design/scoping approval and requires exact venue, environment, symbol, component, max size/count, order type, time window, sandbox account, kill switch, and lifecycle scope.
- Approval scope validation, sandbox risk gate evaluation, sandbox drawdown feed fixture support, and submit-lease duplicate-prevention fixture checks exist and are test-covered.
- Dashboard UAT view shows fixture/readiness status.
- UAT3.1 actual sandbox order submission remains blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.2:

- Sandbox risk gates now propagate all `SandboxRuntimePolicy` blockers into risk/preflight reason codes.
- Approval scopes, risk limits, risk requests, and drawdown fixtures reject invalid non-positive sandbox numeric values.
- `evaluate_uat3_sandbox_submission_preflight` combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status into one fixture-only dry-run result.
- The dry-run preflight explicitly reports no order intent, submitted order, executable approval, or exchange call creation.
- UAT3.1 actual sandbox order submission remains blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.3:

- Sandbox artifact label boundary helpers validate required sandbox/testnet/not-live/not-paper/no-real-capital labels before future persistence, API serialization, dashboard display, and report generation boundaries.
- `UAT3SandboxDryRunGateService` and `evaluate_uat3_sandbox_executable_gate_dry_run` compose runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks into a dry-run executable gate result.
- Runtime policy semantics now explicitly separate broad/global exchange order submission from sandbox/testnet-only submission gating.
- The dry-run executable gate reports no order intent, prepared order, submitted order, executable approval, or exchange call creation.
- UAT3.1 actual sandbox order submission remains blocked.
- No orders, real order intents, prepared orders, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.4:

- Private read-only sandbox account policy exists and fails closed without exact founder/operator credential approval.
- Credential boundary validation and redaction helpers exist for sandbox/testnet-only credentials.
- Sandbox private read-only account/balance/position/equity categories are separated from order/cancel/amend/retry/live-private endpoint categories.
- Sandbox account drawdown feed modeling exists with `sandbox_account` / `not_live_account` labels and explicit unavailable-field truth.
- UAT3 dry-run preflight can consume `sandbox_drawdown_feed_live_fed_verified`, but live-fed sandbox drawdown is not verified because the exact private-read-only credential approval was not present.
- UAT3.1 actual sandbox order submission remains blocked.
- No credentials were used, no private endpoints were called, no order/cancel/amend/retry endpoints were called, and no orders, real order intents, prepared orders, submitted orders, executable approvals, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.5:

- The exact founder/operator approval text for sandbox/testnet private read-only account-state/drawdown verification is present and validated.
- Sandbox/testnet credential environment status is inspectable without retaining private key values.
- Live Hyperliquid endpoint URLs are blocked by sandbox/testnet boundary validation.
- Hyperliquid sandbox account-state payload parsing can produce `sandbox_account` / `not_live_account` drawdown feed truth from caller-supplied sandbox account payloads.
- Local `HYPERLIQUID_UAT_SANDBOX_*` env vars were missing, so no credentials were loaded, no API keys were used, no private endpoints were called, and live-fed sandbox drawdown remains `sandbox_drawdown_feed_missing`.
- UAT3.1 actual sandbox order submission remains blocked.
- No order/cancel/amend/retry endpoints were called, and no orders, real order intents, prepared orders, submitted orders, executable approvals, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Remaining UAT blockers:

- UAT3.1 requires explicit founder/operator approval before actual sandbox order submission.
- UAT3.1 needs sandbox runtime submission enablement and sandbox-only private endpoint separation wired to a real sandbox/testnet account.
- UAT3.1 needs live-fed sandbox account drawdown feed wiring; UAT3.0.5 could not verify it because local sandbox/testnet credential env vars were missing.
- Approval scope validation and risk gates must be wired to executable UAT3.1 gates.
- Submit lease / duplicate-prevention must be integration-verified with the future sandbox submit path.
- Boundary-label helper enforcement exists, but future UAT3.1 still needs those helpers wired to real persistence/API/dashboard/report flows.

Future UAT observation is not ETH-only. UAT1/UAT2 cover the top 20 high-volume crypto assets supported by the selected UAT venue/environment for platform behavior validation. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compares `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## Paper / Live Status

Paper trading is not approved.

Live trading is not approved.

Exchange order submission is not approved.

The current evidence cycle can justify UAT0 safety/runtime hardening and later shadow observation only if the founder accepts that UAT validates plumbing and behavior, not performance.

## UAT Roadmap

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy and redaction hardening complete.
- UAT0.3: top-20 universe and drawdown readiness preflight complete.
- UAT1: top-20 universe plus read-only venue/market metadata complete under strict public-read-only constraints.
- UAT2: bounded no-order shadow strategy observation across top-20 supported assets complete.
- UAT2.1: dashboard visualization and founder approval readiness pack complete; no approval action or order-enabling behavior added.
- UAT3.0: sandbox order design is complete; sandbox-order readiness documented; no order submission, real order intents/submitted orders, or executable approvals added.
- UAT3.0.1: sandbox runtime / approval / risk readiness fixture hardening complete.
- UAT3.0.2: sandbox gate integration dry-run / policy hardening complete; actual UAT3.1 sandbox order submission remains blocked.
- UAT3.0.3: sandbox gate wiring / label-enforcement hardening complete; boundary-label helpers and dry-run executable gate service exist; actual UAT3.1 sandbox order submission remains blocked.
- UAT3.0.4: sandbox private read-only drawdown readiness complete; credential approval/boundary validation, endpoint category separation, redaction, and sandbox account drawdown feed modeling exist; no credentials or private endpoints were used because explicit approval was absent.
- UAT3.0.5: sandbox/testnet private read-only drawdown verification complete; exact approval text and sandbox/testnet credential boundaries are validated, but local credential env vars were missing, so no credentials/private endpoints were used and live-fed sandbox drawdown remains blocked.
- UAT3.1: first approval-gated sandbox order remains blocked pending explicit approval and sandbox lifecycle prerequisites.
- UAT4: sandbox / simulated trading review.

UAT1 public read-only connectivity is complete under strict constraints. UAT1 used no API keys, private endpoints, signed endpoints, order endpoints, paper trading, live trading, or order submission.

## Major Deferred Items

- deployment-specific structured log/API error redaction smoke tests before UAT3.
- secret hygiene beyond representative helper tests.
- fail-safe sandbox/live mode separation verification.
- risk-limit enforcement.
- UAT3 sandbox/live drawdown feed wiring and verification.
- UAT3 explicit design approval and sandbox lifecycle prerequisites.
- kill switch behavior.
- debug stack trace exposure hardening.
- audit logging review.
- operator confirmation gates.
- duplicate-order prevention.
- submit-lease uncertainty verification.
- funding/liquidation/margin modeling.
- order-book/partial-fill/latency/outage modeling.
- out-of-sample and cross-venue evidence.
- smart routing / SOR expansion.

## Required Agent Memory Workflow

Read the canonical command center, current phase, decision log, coordination note, and this project memory before substantial work. Update your own coordination row before overlapping edits and mark it `done` or `blocked` after work.

Do not create duplicate command centers or competing current-phase notes.
