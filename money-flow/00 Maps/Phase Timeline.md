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
| UAT | UAT0-UAT4 | UAT2 bounded no-order shadow observation complete; UAT3 sandbox orders remain blocked; sandbox review remains planned. |

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

Current implemented milestone: `UAT2` bounded no-order shadow strategy observation complete.

Next proposed phase: `UAT3` approval-gated sandbox order design may be scoped only after explicit founder/operator approval.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## UAT Track

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy baseline, Hyperliquid future-UAT1 read-only allowlist artifact, and representative redaction verification complete.
- UAT0.3: fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlist, runtime drawdown monitor policy/model, and UAT1 readiness preflight complete.
- UAT1: top-20 universe plus public read-only venue/market metadata complete under no-private/no-signed/no-order/no-API-key constraints.
- UAT2: bounded no-order shadow strategy run across top-20 supported assets with `next_candle_open` and `next_candle_close` complete.
- UAT3: approval-gated sandbox order design blocked pending explicit founder/operator approval and sandbox lifecycle prerequisites.
- UAT4: sandbox / simulated trading review.

See [[00 Maps/UAT Roadmap|UAT Roadmap]].
