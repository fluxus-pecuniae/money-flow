# Future Work Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Immediate Future

Current implemented milestone: `UAT3.0.1` sandbox runtime / approval / risk readiness hardening complete.

Next proposed phase: `UAT3.1` first approval-gated sandbox order remains blocked.

UAT1 public read-only connectivity is complete under strict constraints: no private endpoints, no signed endpoints, no order endpoints, no API keys, no paper trading, no live trading, and no order submission. UAT1.1 adds model/report-only shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured log/API error redaction verification. UAT2 bounded no-order shadow observation is complete. UAT2.1 dashboard visualization is complete and adds a review-only UAT2 dashboard view without approval/order actions. UAT3.0 sandbox-order design/readiness is complete and documents the narrow ETH `sleeve_1h` initial sandbox subset plus approval/runtime/drawdown/lifecycle/artifact/submit-lease/risk prerequisites. UAT3.0.1 adds fixture-only sandbox runtime policy, artifact-label validation, approval-scope validation, risk gate evaluation, drawdown feed fixture, and submit-lease duplicate-prevention checks. UAT3.1 actual sandbox submission remains blocked.

UAT0 was plumbing and behavior validation preparation only. UAT0.1 closes the P0 sensitive-route auth/authz and central runtime-lockout baseline. UAT0.2 closes the adapter-level runtime-policy baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction tests. UAT0.3 adds fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verified allowed public-read-only Hyperliquid endpoint behavior and resolved the no-key public top-volume source against Hyperliquid supported markets. It did not implement private/signed endpoint calls, exchange order submission, paper trading, live trading, routing expansion, strategy execution, or Money Flow rule changes.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Current Strategy Validation Outcome

SV1 is closed for now. The current evidence cycle selected exactly one UAT observation candidate:

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

It is Hyperliquid ETH USDC perpetual, `sleeve_1h`, current baseline Money Flow rules, observation / shadow first.

Current evidence does not prove edge. It was sufficient only to justify a tightly scoped UAT0 safety/runtime audit and later shadow observation if blockers close.

Future UAT observation is not ETH-only. UAT1/UAT2 should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment for platform behavior validation only.

## UAT Roadmap

See [[00 Maps/UAT Roadmap|UAT Roadmap]].

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy and redaction hardening complete.
- UAT0.3: top-20 universe and drawdown readiness preflight complete.
- UAT1: top-20 universe plus read-only venue/market metadata complete under strict public-read-only constraints.
- UAT2: bounded no-order shadow strategy run across top-20 supported assets with `next_candle_open` / `next_candle_close` complete.
- UAT2.1: dashboard visualization and founder readiness pack complete; no approval action or order-enabling behavior added.
- UAT3.0: sandbox-order design/readiness complete; no order submission, no real order intents/submitted orders, and no executable approvals.
- UAT3.0.1: sandbox runtime / approval / risk readiness hardening complete with fixture-only validators; no order submission, real order intents/submitted orders, executable approvals, private/signed endpoint calls, API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.
- UAT3.1: first approval-gated sandbox order blocked pending explicit approval, live-fed sandbox drawdown, real sandbox submit path wiring, executable approval-scope gate wiring, risk gate wiring, submit-lease integration verification, and sandbox artifact-label persistence enforcement.
- UAT4: sandbox / simulated trading review.

## Pre-Paper / Live Trading Blockers

Before paper/live trading or production-like deployment, the project must address:

- deployment-level structured application log/API error redaction verification beyond representative UAT1.1 tests.
- key and secret hygiene beyond representative helper tests.
- fail-safe live/demo separation.
- configured risk-limit enforcement.
- real drawdown calculation and monitoring.
- kill switch behavior.
- debug stack trace exposure.
- audit logging and no-secret logs.
- operator confirmation gates.
- duplicate-order prevention.
- submit-lease uncertainty handling.
- sandbox/live endpoint isolation.

## Later Strategy Validation

Future research may revisit:

- broader true replay fill/cost sensitivity.
- out-of-sample windows.
- exact stop/invalidation exit replay.
- portfolio-level simulation.
- cross-venue comparisons after venue-specific identity/source gaps close.

No later research item is approved as a production rule.

## Deferred Platform Work

- Phase 8.1 manual-resolution marker design.
- Smart routing / SOR foundations.
- Best-binding selection.
- CBBO.
- Fanout / split allocation.
- Route executor behavior.
- Cross-binding or cross-venue recovery.
- Broader dashboard/control-plane UI beyond review surfaces.

## Non-Negotiable Boundary

Do not implement optimization, paper trading, live trading, exchange order submission, or routing expansion from this roadmap without a separate approved phase.
