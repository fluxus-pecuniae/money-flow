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
- UAT0 safety/security/runtime readiness plus UAT0.1 API/runtime lockout, UAT0.2 adapter-policy/redaction hardening, UAT0.3 top-20 universe/drawdown readiness preflight, and UAT1 public read-only connectivity/universe resolution.

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

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 / UAT1 Outcome

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT0.2 adapter runtime-policy, read-only allowlist, and representative redaction hardening is complete. UAT0.3 top-20 universe and drawdown readiness preflight is complete. UAT1 public read-only connectivity is complete. UAT1.1 shadow readiness is complete. UAT2 shadow strategy run may proceed as a future no-order phase.

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

Remaining UAT blockers:

- Representative structured application log/API error redaction is verified for UAT2; deployment-specific middleware/logging smoke tests remain before UAT3.
- UAT1.1 adds operator-visible shadow drawdown state for UAT2.
- UAT1.1 adds a shadow signal audit surface for would-trade/no-trade/risk-block explainability.
- UAT3 needs sandbox/live account drawdown feed wiring.
- Existing approval gates, execution defaults, venue submit flags, and submit-lease uncertainty protections are useful but require later UAT-specific verification.

Future UAT observation is not ETH-only. UAT1/UAT2 should cover the top 20 high-volume crypto assets supported by the selected UAT venue/environment for platform behavior validation. Top-20 inclusion is not strategy approval.

Future UAT2 shadow timing should compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

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
- UAT2: next shadow strategy run across top-20 supported assets, no orders.
- UAT3: approval-gated sandbox orders.
- UAT4: sandbox / simulated trading review.

UAT1 public read-only connectivity is complete under strict constraints. UAT1 used no API keys, private endpoints, signed endpoints, order endpoints, paper trading, live trading, or order submission.

## Major Deferred Items

- deployment-specific structured log/API error redaction smoke tests before UAT3.
- secret hygiene beyond representative helper tests.
- fail-safe sandbox/live mode separation verification.
- risk-limit enforcement.
- UAT3 sandbox/live drawdown feed wiring and verification.
- UAT2 implementation using the shadow signal audit and shadow drawdown surfaces.
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
