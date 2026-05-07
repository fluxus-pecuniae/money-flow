# Current State Dashboard

Up: [[Money Flow Command Center]]

## Today In One Sentence

Money Flow is a mandate-driven, multi-venue-aware trading strategy platform whose current deepest execution path is controlled single-target recommendation-backed routed execution, with Strategy Validation now providing canonical Money Flow campaign evidence review, DB/schema/identity/candle data-gap truth, collision-safe evidence packs where data is sufficient, hardened historical candle import, and candle-import preflight before any paper-trading decision.

## Current Implemented Phase

- Phase observed in repo memory: `SV1.13.1` Hyperliquid evidence interpretation truth / founder review pack.
- Latest implemented scope: Hyperliquid-first public evidence review. BTC/ETH/SOL Hyperliquid research identity is operator-verified by `Tercirafael`, non-trading, and non-strategy-eligible; the intended migrated `money_flow` DB contains `25848` imported public campaign candles; evidence review generated component-scoped packs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`; status is `ready_for_founder_review`. Aster/Binance remain later comparative candidates, OKX/Coinbase are blocked by missing public trade count, and Kraken is blocked by incomplete public REST coverage.
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
- SV1.10 creates/migrates the intended local `money_flow` DB, verifies required tables, reruns canonical review, and reports zero persisted candles plus 18 unique timezone-explicit import requirements; no first real packs were generated.
- SV1.11 adds research-only BTC/ETH/SOL Hyperliquid perpetual USDC market-identity seed/verify tooling, evidence-review identity readiness, and candle-import preflight; it writes no candles and generates no evidence packs.
- SV1.11.2 keeps the research identity seed from enabling strategy/trading eligibility and requires complete one-to-one requirement-aware preflight so files must prove exact canonical close-slot coverage before import; it writes no candles and generates no evidence packs.
- SV1.12 adds guarded canonical candle bundle import; it writes candles only when every gate passes and generates no evidence packs.
- SV1.12.1 checked the intended local DB, found it reachable/current with zero candles, found BTC/ETH/SOL identity rows and repo/session candle files missing, attempted no operational import, and hardened partial/import-blocked operator output.
- SV1.12.2 checked readiness for identity/file prerequisites, did not seed because operator verification was not supplied, documented the exact 18 timezone-explicit file requirements, found no repo/session candle files, imported no candles, and generated no evidence packs.
- SV1.12.3 attempted the guarded import workflow, confirmed the intended DB remains reachable/current, did not seed because explicit operator verification was absent, found no canonical candle files, imported no candles, and generated no evidence packs.
- SV1.13 dashboard update: `apps/dashboard/` is now a static local evidence-pack visualization dashboard for founder/operator review of ignored local SV1.13 review and batch-report JSON files.
- Proposed next phase: manual founder/operator review of the Hyperliquid-only evidence interpretation, using the dashboard where helpful, before any explicitly scoped paper-trading design phase. Aster/Binance identity verification/import and OKX/Coinbase/Kraken source blockers are broader venue-comparison follow-ups; paper/live trading remains deferred.

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

SV1.13.1 keeps validation research-only. Canonical campaign configs live under `configs/strategy_validation/campaigns/`, campaign windows use `(start_at, end_at]`, config `window_convention` metadata is strictly validated against that platform convention, data-readiness audits can render Markdown founder summaries, and evidence-pack writes use explicit collision policy instead of silent overwrite. Offline public CSV/JSON candle imports can duplicate-safely upsert matching existing candle rows for research backfills only, but reject identity conflicts, timeframe-duration mismatches, malformed/non-finite/inconsistent OHLCV rows, negative trade counts, timezone-naive timestamps by default, and invalid files without partial commits. The evidence review CLI reports sanitized DB target/reachability/schema/migration/candle-table truth plus canonical market identity readiness before canonical audits, blocks ambiguous/non-intended maintenance DB targets and unready schema/data clearly, and can generate packs only when target, schema, and data readiness are clean. The operator-approved SV1.12.5 Hyperliquid bridge imported all 9 public YTD/recent files from `/tmp/money-flow-sv1124-public-ytd-recent/csv` and inserted `25848` candles after identity and preflight gates passed. SV1.13 then generated three Hyperliquid-only public campaign evidence packs from those candles and records status `ready_for_founder_review`. SV1.13.1 adds the interpretation layer: grouped aggregate totals are research-run sums, not one account/scenario PnL; scenario-level fill/cost/drawdown evidence is visible; and ETH `sleeve_1h` concentration is explicit. `apps/dashboard/` visualizes local evidence artifacts for human review only. This is research evidence, not paper/live approval, not a strategy recommendation, and not cross-venue performance. SV1.12.5 also records supported-venue public readiness with 18 Aster/Binance native-trade-count candidate files, OKX/Coinbase trade-count blockers, and Kraken coverage blockers under `/tmp/money-flow-sv1125-supported-venues-public`.

## Deferred Boundaries

See [[20 Workflows/Deferred Smart Routing]] and [[40 Operations/Future Work Roadmap]].

- Smart routing, best-binding selection, CBBO, ranking, scoring, route plans, fanout, target reselection, cross-binding recovery, cross-venue retry, route executor behavior, and auto-submit are not implemented.
- Dashboard UI now has a static local Strategy Validation evidence visualization surface; it is read-only review UI, not execution or evidence generation.
- Alerts remain deferred; Money Flow backtesting/validation now exists as a research-only surface, not paper trading or live execution.
- Top-of-book/depth interfaces exist, but live execution-quality market data is not wired.
- Full attribution and mandate-level account aggregation remain deferred.
