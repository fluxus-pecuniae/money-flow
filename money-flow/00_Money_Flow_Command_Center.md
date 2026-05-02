# Money Flow Command Center

This is the required Obsidian brain entrypoint for Money Flow agents.

## North Star

Money Flow is a mandate-driven, multi-venue trading platform where strategy alpha remains central. Routing and automation must serve the strategy workflow; they must not replace it with fake smart-routing or hidden execution behavior.

## Current Phase

- Current implemented phase: `SV1.5`
- Phase 7 status: accepted complete.
- Proposed next phase: SV1.6 first real canonical evidence review / saved evidence comparison after sufficient historical candle data is imported or confirmed; `Phase 8.1` remains deferred until explicitly scoped.
- Phase 8.0 status: implemented read-only operator observability/manual-resolution inspection.
- Phase 8.0.1 status: Obsidian memory and working-tree baseline cleanup; no product behavior changed.
- Phase 8.0.2 status: active submit-lease operator-summary truth hotfix; no product behavior changed.
- SV1.0 status: first Money Flow strategy-validation/backtesting framework; no live trading artifacts or strategy-rule optimization.
- SV1.0.1 status: strategy-validation report-truth hardening; explicit fill timing, explicit drawdown methodology, expanded Markdown; no strategy-rule changes.
- SV1.1 status: comparative strategy-validation batch reporting; explicit components/fill-timing/symbol/window/cost matrix; descriptive research only with no optimization, recommendation, live artifacts, routing, or execution changes.
- SV1.2 status: market-regime and data-coverage validation reporting; descriptive regimes and coverage diagnostics only with no strategy-rule changes, paper/live trading, routing, exchange calls, or execution changes.
- SV1.2.1 status: window-boundary, coverage, and grouped-comparison research-truth hotfix; no strategy-rule changes, paper/live trading, routing, exchange calls, or execution changes.
- SV1.3 status: repeatable research campaign/evidence-pack workflow; no strategy-rule changes, optimization, paper/live trading, routing, exchange calls, or execution changes.
- SV1.4 status: evidence-pack review discipline and historical data-readiness baseline; no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.4.1 status: evidence-pack collision/overwrite integrity hotfix; no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.5 status: historical-data readiness and first canonical evidence-pack support; validates campaign window-convention metadata, adds Markdown readiness summaries, adds offline public candle import/upsert tooling, preserves collision-safe evidence packs, and adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- Current accepted action hooks: approval-gated recommendation acceptance, target-choice conversion, prepared-order preview/readiness inspection, and submitted-order handoff.

## Current Architectural Boundary

The accepted routed chain remains:

```text
MandateDesiredTrade
-> RouteReadinessAudit
-> RoutingTargetRecommendation
-> RoutingTargetChoice
-> OrderIntent
-> PreparedVenueOrder
-> ExecutionReadinessAssessment
-> SubmittedOrder
```

Phase 7.5 is accepted as automating only:

```text
ExecutionReadinessAssessment -> SubmittedOrder
```

Phase 7.6 adds no new automation transition. It closes out the Phase 7 controlled automation chain by proving the existing approval-gated stages remain exact-lineage-bound, same-target, non-fanout, non-reselecting, and distinct from dry-run / approval creation / generic administrative consumption. `consumption_pending` remains a bounded approval-reconciliation state; repeat calls must reuse the existing submitted order rather than submit again.

Phase 8.0 adds no new trading transition. It makes the existing chain easier to inspect, debug, reconcile, and manually manage through read-only operator summary inspection. It surfaces current workflow state, approval state, submit-lease uncertainty, `consumption_pending`, blocked readiness/recommendation facts, and next safe manual operator action without submitting, canceling, amending, retrying, selecting a new target, ranking, scoring, using CBBO, fanout, or route-executor behavior.

Phase 8.0.1 resolves the dirty Obsidian memory baseline left after Phase 8.0. The earlier full-project-memory refresh is accepted as intentional strategic-memory work, stale "proposed Phase 8.0" wording is cleaned up, and the repo-root memory file remains a pointer only.

Phase 8.0.2 fixes read-only operator-summary truth for active submit leases. An unexpired `active` child-intent submit lease is reported as `submission_in_progress`, blocks repeat-submit safety, and blocks the next safe operator action from reporting approval-gated submit as safe. Terminal submit uncertainty remains manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and no trading behavior or manual-resolution mutation is added.

SV1.0 adds a separate Strategy Validation boundary for Money Flow. It reads persisted candles, computes indicators in memory, reuses current strategy rules, simulates research-only trades with explicit assumptions, and emits deterministic reports. It does not create desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing artifacts, approval changes, exchange calls, smart routing, or new automation behavior.

SV1.0.1 hardens that report truth. Fill timing is explicit (`same_candle_close_research_only`, `next_candle_open`, or `next_candle_close`), same-candle close fills are labeled research-only and potentially optimistic, closed-trade drawdown is separated from mark-to-market drawdown, and Markdown reports include assumptions, component metrics/comparison, trade summaries, reason counts, and limitations. Money Flow strategy rules are unchanged.

SV1.1 adds comparative validation on top of the single-run report. Batch reports compare explicit components/timeframes, fill timings, symbols, date windows, and cost assumptions using descriptive observed metrics only. They do not optimize, recommend a variant, alter Money Flow rules, create live artifacts, route, submit, or call exchange adapters.

SV1.2 adds data-coverage and market-regime diagnostics. Reports now show requested versus available candles, missing/gap/coverage warnings, deterministic trend and volatility labels, and regime-grouped performance metrics. Regime labels are descriptive only and are not used to alter strategy behavior.

SV1.2.1 fixes research-truth issues before campaign/evidence-pack work. Validation windows now use one convention everywhere: candle closes in `(start_at, end_at]`. Coverage counts expected close slots under that convention, unaligned boundaries are warning-coded, coverage cannot exceed 100%, and grouped comparisons keep blocked runs visible with blocked reason counts. Money Flow rules are unchanged.

SV1.3 adds repeatable research campaign evidence packs on top of the existing Strategy Validation batch runner. Named JSON configs expand explicit symbols, components, fill timings, named `(start_at, end_at]` windows, fees, slippage, capital, and sizing into batch runs, then save normalized config, manifest, JSON, Markdown, and README outputs under timestamped evidence-pack directories. Blocked runs remain visible in manifests/reports. Campaign output is research evidence only, not optimization, not a recommendation, not paper/live trading, and not routing or execution input.

SV1.4 adds evidence-pack review discipline and data-readiness checks before paper-trading decisions. Canonical editable campaign configs live under `configs/strategy_validation/campaigns/`, and the campaign CLI can run `--audit-only` persisted-candle readiness checks by symbol, component, and named window. Evidence-pack manifests and Markdown now include founder/operator review checklists plus manual paper-trading readiness criteria. These criteria are manual review inputs only; they do not auto-approve paper trading, create paper trades, create live artifacts, route, submit, or call exchanges.

SV1.4.1 makes evidence packs collision-safe before first real SV1.5 outputs. The default `unique_suffix` policy writes a suffixed run directory when the requested campaign/timestamp directory already exists, and `fail_if_exists` can raise explicitly instead. Manifests record requested run id, final run id, final path, collision policy, collision occurrence, and suffix truth. No strategy rules, optimization, recommendations, paper/live trading, routing, execution automation, live artifacts, or exchange calls are added.

SV1.5 prepares the research layer for first canonical evidence runs against real persisted candles. Campaign `window_convention` text is validated against the authoritative `(start_at, end_at]` candle-close convention, readiness audits can render founder-readable Markdown summaries, and offline public CSV/JSON candles can be duplicate-safely imported into existing candle rows for research backfills. Import source labels are summary-only because the current candle model has no per-candle provenance column. No live artifacts, strategy decisions, routing artifacts, approvals, submitted orders, paper trades, exchange private/order calls, or adapter calls are added.

## Repo Truth Sources

Repo operational truth remains in:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

Obsidian is the long-horizon project brain for founder intent, phase context, decisions, and cross-agent coordination. It does not replace the repo changelog or operational docs.

## Required Links

- [[01_Current_Phase|Current Phase]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[40 Operations/Future Work Roadmap|Future Work Roadmap]]
- [[40 Operations/Phase 8 Focus|Phase 8 Focus]]
- [[20 Workflows/Operator Observability and Manual Resolution|Operator Observability and Manual Resolution]]
- [[20 Workflows/Deferred Smart Routing|Deferred Smart Routing]]

## Standing Reminders

- Strategy alpha remains central.
- Approval is not execution unless a narrow action endpoint consumes it.
- `consumption_pending` approval truth means a submitted order already exists and approval reconciliation must be finished or inspected; it is not permission to submit again.
- Submitted-order handoff approval does not bypass readiness or submit gates.
- Preview/readiness approval is separate from submitted-order authorization.
- Target-choice conversion is not readiness and not submission.
- `SubmittedOrder` remains post-submit exchange/account truth.
- Phase 8.0 is observability/manual-resolution inspection, not smart routing.
- Phase 8.0.2 is a truth-surface hotfix only; SV1.0 now starts Strategy Validation while Phase 8.1 remains deferred.
- SV1.0.1 reports are research evidence, not proof of profitability and not live execution truth.
- SV1.1 comparison reports are descriptive evidence, not optimization, not strategy recommendations, and not paper/live trading authorization.
- SV1.2 regime labels are descriptive diagnostics, not filters, recommendations, or paper/live trading authorization.
- SV1.2.1 window/coverage semantics are load-bearing for future campaign reports: adjacent windows must not double-count boundary candles, and blocked runs must not disappear from grouped comparisons.
- SV1.3 evidence packs are repeatable research bundles, not proof of profitability, not optimization, and not authorization for paper/live trading.
- SV1.4 readiness audits and paper-trading criteria are manual founder/operator review aids only; they are not automated go/no-go decisions.
- SV1.4.1 evidence packs must be treated as immutable research records; repeated runs should create a new suffixed pack or fail explicitly, never silently overwrite prior evidence.
- SV1.5 candle imports are public/offline research data backfills only; they upsert candles and do not imply strategy edge, paper-trading approval, live execution readiness, exchange truth, or per-candle source provenance.
- Simulated validation trades must remain separate from `SubmittedOrder`.
- Manual-resolution inspection must not silently resolve venue or approval truth.
- Future agents must update their own coordination row instead of overwriting another agent's work.
