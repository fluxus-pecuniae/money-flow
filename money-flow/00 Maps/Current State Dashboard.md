# Current State Dashboard

Up: [[Money Flow Command Center]]

## Today In One Sentence

Money Flow is a mandate-driven, multi-venue-aware trading strategy platform whose current deepest execution path is controlled single-target recommendation-backed routed execution, with Strategy Validation now providing canonical Money Flow campaign evidence review, DB/candle-table data-gap truth, collision-safe evidence packs where data is sufficient, and hardened historical candle import/data-readiness review before any paper-trading decision.

## Current Implemented Phase

- Phase observed in repo memory: `SV1.9.1`.
- Latest implemented scope: evidence-target truth, candle-import timestamp/provenance truth, and Obsidian memory-governance hotfix before first real canonical evidence packs.
- Current action hooks: approval-gated `recommendation_acceptance`, `target_choice_conversion`, `prepared_order_preview_and_readiness`, and `submitted_order_handoff`.
- Phase 7.5.1 added `consumption_pending` approval truth for submitted-order-created / approval-consumption-failed cases.
- Phase 7.6 added closeout tests and docs only; it added no production behavior.
- Phase 8.0 added read-only operator-grade observability and manual-resolution inspection.
- SV1.0-SV1.3 added Money Flow validation, comparative reports, regime/coverage diagnostics, and repeatable evidence packs.
- SV1.4 added canonical editable campaign configs, campaign `--audit-only` data-readiness inspection, evidence-pack review checklist, and manual paper-trading readiness criteria.
- SV1.4.1 added collision-safe evidence-pack writes so repeated same-timestamp campaign runs do not silently overwrite prior evidence.
- SV1.5 validates campaign window-convention metadata, adds founder-readable Markdown data-readiness audits, and adds offline public candle import/upsert tooling for research backfills.
- SV1.5.1 rejects contradictory window-convention text plus candle import identity conflicts, timeframe-duration mismatches, malformed OHLCV rows, and partial invalid imports before first real evidence review.
- SV1.6 audits canonical BTC and multi-symbol campaigns, reports insufficient data as a data-readiness gap, optionally generates collision-safe evidence packs where audits are clean, and emits manual paper-readiness review status without approving paper trading.
- SV1.7 reports sanitized DB reachability/candle-table truth before audits, blocks canonical campaigns clearly when DB/schema data is unavailable, adds `partial_evidence_ready_with_data_gaps`, and recorded that the local reachable DB lacks `candles`, so no first real packs were generated.
- SV1.8 adds DB/schema/migration bootstrap truth and `--db-status-only`; the explicit local maintenance DB target was reachable in that phase but unmigrated.
- SV1.8.1 gates evidence-pack generation on `migrated_schema_ready` plus required `candles`, `instruments`, and `symbols` tables.
- SV1.9 reports sanitized DB target role/intended-target truth and canonical candle import requirements; no first real packs were generated.
- SV1.9.1 blocks ambiguous/non-intended maintenance DB targets from evidence generation by default, rejects timezone-naive candle imports by default unless a provenance-marked non-canonical override is used, and refreshes Obsidian current truth through SV1.9.
- Proposed next phase: migrate/populate a reachable non-maintenance Money Flow DB or import enough timezone-explicit historical candles, rerun canonical evidence review with generated packs only when DB target/schema/data readiness are clean, then scope paper-trading design only if founder/operator review justifies it.

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

## Current Strategy Validation Layer

SV1.9.1 keeps validation research-only. Canonical campaign configs live under `configs/strategy_validation/campaigns/`, campaign windows use `(start_at, end_at]`, config `window_convention` metadata is strictly validated against that platform convention, data-readiness audits can render Markdown founder summaries, and evidence-pack writes use explicit collision policy instead of silent overwrite. Offline public CSV/JSON candle imports can duplicate-safely upsert matching existing candle rows for research backfills only, but reject identity conflicts, timeframe-duration mismatches, malformed/non-finite/inconsistent OHLCV rows, negative trade counts, timezone-naive timestamps by default, and invalid files without partial commits. The evidence review CLI reports sanitized DB target/reachability/schema/migration/candle-table truth before canonical audits, blocks ambiguous/non-intended maintenance DB targets and unready schema/data clearly, and can generate packs only when target, schema, and data readiness are clean; it does not create live artifacts, approve paper trading, or call exchange/private/order endpoints.

## Deferred Boundaries

See [[20 Workflows/Deferred Smart Routing]] and [[40 Operations/Future Work Roadmap]].

- Smart routing, best-binding selection, CBBO, ranking, scoring, route plans, fanout, target reselection, cross-binding recovery, cross-venue retry, route executor behavior, and auto-submit are not implemented.
- Dashboard UI remains placeholder only.
- Alerts remain deferred; Money Flow backtesting/validation now exists as a research-only surface, not paper trading or live execution.
- Top-of-book/depth interfaces exist, but live execution-quality market data is not wired.
- Full attribution and mandate-level account aggregation remain deferred.
