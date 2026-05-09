# Phase 8 Focus

Up: [[Money Flow Command Center]]

## Status

Phase 8.0 is implemented. Phase 8.0.1 cleaned the Obsidian memory / working-tree baseline.

The accepted codebase baseline now includes Phase 8.0 read-only operator routed workflow summary inspection. Phase 7.6 remains the accepted controlled automation closeout baseline underneath it.

Current implemented phase is `SV1.18` evidence credibility closeout and UAT candidate freeze. This Phase 8 note is historical/operator-control context; current active work is Strategy Validation closeout and UAT0 planning. Hyperliquid BTC/ETH/SOL identity is operator-verified as research-only/non-trading, the 9 Hyperliquid public YTD/recent files were imported with `25848` candles, SV1.13 generated component-scoped Hyperliquid-only evidence packs for founder review, SV1.16/SV1.16.1 added per-candle rejected-signal replay context plus method-truth counters, SV1.17 tested lower-RSI plus market-structure variants across BTC/ETH/SOL and 15m/1h/4h without changing production rules, and SV1.18 freezes only Hyperliquid ETH `sleeve_1h` baseline current rules as a UAT observation candidate. It is not routing/SOR expansion or manual-resolution mutation.

## Phase 8.0 Purpose

Phase 8.0 is the first operator-grade observability and manual-resolution inspection phase.

It should help an operator answer:

- What state is this desired trade in?
- What recommendation, target choice, child intent, readiness result, and submitted-order handoff exist?
- Which approvals exist for each action stage?
- Is an approval active, revoked, consumed, expired, stale-lineage, or `consumption_pending`?
- Is anything blocked, uncertain, or manual-reconciliation-required?
- Did adapter submit possibly start?
- Was a submitted order persisted?
- Is a submit lease active or terminal-uncertain?
- What is the next safe manual operator action, if knowable?

## Implemented Shape

Phase 8.0 stayed read-only and deferred manual-resolution marker mutation.

The implemented surface provides:

- routed workflow summary by desired-trade key
- structured approval/automation state inspection
- manual-resolution issue summaries
- submitted-order handoff safety inspection
- submit lease and concurrency visibility
- explicit no-SOR / no-fanout / no-reselection facts

## Hard Boundary

Phase 8.0 must not add:

- smart routing
- best-binding selection
- CBBO
- ranking or scoring
- fanout or split allocation
- target reselection
- route executor behavior
- cross-binding or cross-venue retry
- new exchange behavior
- new automation action stages
- submit, cancel, amend, or retry from inspection
- silent manual resolution of exchange/account truth

## Phase 8.0.1 Cleanup

Phase 8.0.1 accepted the earlier Obsidian refresh as intentional strategic-memory baseline and updated stale proposed-Phase-8 wording after Phase 8.0 implementation.

The remaining scope risk is still manual-resolution markers. Defer marker endpoints to Phase 8.1 unless they are strictly append-only, actor-stamped, reason-coded, audited, and clearly separated from venue/account truth.

## Related Notes

- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Future Work Roadmap]]
- [[01_Current_Phase]]
