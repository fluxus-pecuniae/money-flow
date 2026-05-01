# Current State Dashboard

Up: [[Money Flow Command Center]]

## Today In One Sentence

Money Flow is a mandate-driven, multi-venue-aware trading strategy platform whose current deepest path is controlled single-target recommendation-backed routed execution, with Phase 8.0 adding read-only operator observability and manual-resolution inspection over that chain.

## Current Implemented Phase

- Phase observed in repo memory: `Phase 8.0.1`.
- Latest implemented scope: Obsidian memory / working-tree cleanup after accepted Phase 8.0.
- Current action hooks: approval-gated `recommendation_acceptance`, `target_choice_conversion`, `prepared_order_preview_and_readiness`, and `submitted_order_handoff`.
- Phase 7.5.1 added `consumption_pending` approval truth for submitted-order-created / approval-consumption-failed cases.
- Phase 7.6 added closeout tests and docs only; it added no production behavior.
- Phase 8.0 added read-only operator-grade observability and manual-resolution inspection.
- Proposed next phase: Phase 8.1 manual-resolution marker / administrative reconciliation design.

## Implemented Platform Surface

- [[10 Components/Runtime and Config|Runtime and Config]]: client, venue account, mandate, binding, component context.
- [[10 Components/Market Data and Indicators|Market Data and Indicators]]: candle sync, health, deterministic indicators.
- [[10 Components/Strategy Engine|Strategy Engine]]: Money Flow strategy family and decisions.
- [[10 Components/Planning and Risk|Planning and Risk]]: mandate desired trades, source policy, risk evaluation, child-intent boundary.
- [[10 Components/Routing Service|Routing Service]]: routing assessment, route-readiness audit, recommendation, acceptance, target choice, conversion, automation plans, approvals.
- [[10 Components/Execution Service|Execution Service]]: preparation, readiness, explicit gated submit, submitted-order lifecycle, actionability, recovery, reconciliation.
- [[10 Components/Exchange Adapters|Exchange Adapters]]: Hyperliquid, Aster, OKX, Coinbase, Binance, Kraken.
- [[10 Components/API Control Plane|API Control Plane]]: FastAPI operator and inspection endpoints.

## Deepest Current Workflow

See [[20 Workflows/Current Routed Workflow]].

```text
StrategyDecision
-> MandateDesiredTrade
-> RoutingAssessment
-> RouteReadinessAudit
-> RoutingTargetRecommendation
-> RoutingTargetChoice
-> OrderIntent
-> PreparedVenueOrder
-> ExecutionReadinessAssessment
-> SubmittedOrder
-> routed lifecycle/actionability/reconciliation inspection
```

## Phase 7 Overlay

See [[40 Operations/Phase 7 Focus]] and [[20 Workflows/Approval Gated Recommendation Acceptance]].

- Phase 7.0: dry-run automation plans, no mutation.
- Phase 7.1: durable approval gates.
- Phase 7.1.1: expiry, stale lineage, scope uniqueness.
- Phase 7.1.2: only currently approvable steps can create or appear approved.
- Phase 7.2: valid approval can accept a recommendation into a target choice only.
- Phase 7.2.1: action, target-choice creation/reuse, approval consumption, and provenance update are coherent in one transaction.
- Phase 7.3: valid approval can convert the exact target choice into one child intent.
- Phase 7.4: valid approval can run preview/readiness inspection for the exact child intent.
- Phase 7.5: valid approval can submit the exact already-ready child intent through the existing explicit submit path.
- Phase 7.5.1: post-submit approval-consumption failure becomes `consumption_pending`.
- Phase 7.6: closeout regression proves the chain remains exact-lineage, same-target, no-SOR, and distinct from dry-run/admin consume.

## Current Operator Inspection Layer

See [[40 Operations/Phase 8 Focus]] and [[20 Workflows/Operator Observability and Manual Resolution]].

Phase 8.0 makes workflow state, approval state, manual-resolution needs, submit-lease uncertainty, and next safe manual operator action visible without mutating trading artifacts.

## Deferred Boundaries

See [[20 Workflows/Deferred Smart Routing]] and [[40 Operations/Future Work Roadmap]].

- Smart routing, best-binding selection, CBBO, ranking, scoring, route plans, fanout, target reselection, cross-binding recovery, cross-venue retry, route executor behavior, and auto-submit are not implemented.
- Dashboard UI remains placeholder only.
- Alerts and backtesting are placeholder/deferred surfaces.
- Top-of-book/depth interfaces exist, but live execution-quality market data is not wired.
- Full attribution and mandate-level account aggregation remain deferred.
