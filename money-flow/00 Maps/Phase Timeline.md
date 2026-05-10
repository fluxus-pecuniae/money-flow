# Phase Timeline

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Major Tracks

| Track | Range | Outcome |
| --- | --- | --- |
| Platform foundation | Phase 1-4 | Strategy, planning, risk, execution, exchange/data/state, and submitted-order lifecycle substrate. |
| Routing substrate | Phase 5-6 | Non-executing routing assessment, route-readiness audit, recommendation, target choice, conversion, readiness, and explicit same-target handoff. |
| Controlled automation | Phase 7 | Approval-gated same-target action hooks with safety closeout; no full SOR. |
| Operator observability | Phase 8 | Read-only routed workflow/manual-resolution inspection and submit-lease truth. |
| Strategy Validation | SV1.0-SV1.18.1 | Hyperliquid public evidence cycle, dynamic equity, diagnostics, replay experiments, and UAT candidate freeze. |
| UAT | UAT0-UAT4 | UAT3.3 Hyperliquid account-targeting / precision hardening complete as blocked before order transport; UAT3.4 requires separate approval plus sufficient testnet equity on the configured target. |

Strategy Validation is now its own major track. It is not an active sub-phase of Phase 8.

## Phase 1-4

- Phase 1: platform scaffold, domain boundaries, API/db/service shape.
- Phase 2: exchange/data/state foundation.
- Phase 3: indicators, Money Flow strategy family, decisions, repo governance.
- Phase 3.3-3.5: client, venue account, mandate, binding, component hierarchy.
- Phase 4: multi-venue adapters, desired-trade planning, risk, readiness, submission, lifecycle.

## Phase 5-8

- Phase 5: non-executing routing substrate and routed lifecycle inspection.
- Phase 6: controlled non-executing recommendation, acceptance, recommendation-backed conversion/readiness/submission, workflow inspection, and submit uncertainty hardening.
- Phase 7: approval-gated automation hooks for the existing same-target chain, closed with safety proof.
- Phase 8: operator observability and manual-resolution inspection, not smart routing.

## Strategy Validation Track

- SV1.0-SV1.2.1: baseline backtest truth, fill timing, drawdown, window, coverage, regime truth.
- SV1.3-SV1.4.1: campaigns, evidence packs, evidence review discipline, collision safety.
- SV1.5-SV1.9.1: historical data/import/DB governance.
- SV1.10-SV1.12.5.1: intended DB, Hyperliquid identity, public campaign candle readiness/import, repo/import closeout.
- SV1.13-SV1.13.2: first Hyperliquid public evidence, interpretation, dynamic equity.
- SV1.14-SV1.17: diagnostics, hypothesis methodology, rejected-signal replay, full-suite true replay experiments.
- SV1.18-SV1.18.1: evidence credibility closeout, one UAT candidate freeze, Obsidian coordination closeout.

## Current State

Current implemented milestone: `UAT3.3` Hyperliquid account targeting / precision hardening complete as blocked before order transport.

Next proposed phase: `UAT3.4` is blocked until separate approval plus sufficient testnet equity on the configured target account/subaccount.

Paper trading is not approved. Live trading is not approved. Additional exchange order submission is not approved.

## UAT Track

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy baseline, Hyperliquid future-UAT1 read-only allowlist artifact, and representative redaction verification complete.
- UAT0.3: fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlist, runtime drawdown monitor policy/model, and UAT1 readiness preflight complete.
- UAT1: top-20 universe plus public read-only venue/market metadata complete under no-private/no-signed/no-order/no-API-key constraints.
- UAT2: bounded no-order shadow strategy run across top-20 supported assets with `next_candle_open` and `next_candle_close` complete.
- UAT2.1: dashboard visualization and founder approval readiness pack complete.
- UAT3.0: sandbox order design/readiness complete with no orders, no order intents, no submitted orders, and no executable approvals.
- UAT3.0.1: fixture-only sandbox runtime policy, sandbox artifact label validation, approval-scope validation, risk gate evaluation, sandbox drawdown feed fixture, and submit-lease duplicate-prevention checks complete.
- UAT3.0.2: fixture-only sandbox gate dry-run preflight, full runtime blocker propagation, and invalid numeric rejection complete.
- UAT3.0.3: sandbox artifact label boundary helpers and dry-run executable gate service complete.
- UAT3.1: first approval-gated sandbox/testnet lifecycle probe complete; one Hyperliquid testnet ETH post-only limit attempt was rejected by venue user/API-wallet validation, no cancel was required, and reconciliation found no open order.
- UAT3.2: fixed-key preflight / second sandbox lifecycle attempt complete as blocked before order transport; separate approval was verified, account/API-wallet readiness failed, order attempt count was `0`, and no order endpoint was called.
- UAT3.3: Hyperliquid account-targeting / precision hardening complete as blocked before order transport; account targeting and ETH precision are fixed, but target subaccount equity is `0.0`.
- UAT3.4: additional sandbox lifecycle testing is blocked; it requires separate founder/operator approval and sufficient sandbox equity before accepted/open -> cancel coverage.
- UAT4.0: live UAT trading dashboard / chart cockpit requested as a future roadmap phase only.

See [[00 Maps/UAT Roadmap|UAT Roadmap]].
