# Money Flow Command Center

This is the required Obsidian brain entrypoint for Money Flow agents.

## North Star

Money Flow is a mandate-driven, multi-venue trading platform where strategy alpha remains central. Routing and automation must serve the strategy workflow; they must not replace it with fake smart-routing or hidden execution behavior.

## Current Phase

- Current implemented phase: `SV1.9.1`
- Phase 7 status: accepted complete.
- Proposed next phase: point strategy validation at a reachable migrated non-maintenance Money Flow database, import/verify enough timezone-explicit public/offline canonical BTC/ETH/SOL candles from the SV1.9 import requirements, rerun canonical evidence review with generated evidence packs only after DB target truth, `migrated_schema_ready`, and data-readiness are clean, and only then scope paper-trading design if founder/operator review justifies it; `Phase 8.1` remains deferred until explicitly scoped.
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
- SV1.5.1 status: candle import and campaign-config research-truth hotfix; rejects contradictory window-convention text, identity conflicts, timeframe-duration mismatches, malformed OHLCV rows, and partial invalid imports without strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.6 status: first canonical Money Flow evidence review; audits canonical BTC and multi-symbol campaigns, reports insufficient data or generated evidence-pack paths, adds manual paper-readiness review status, and adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.7 status: first real canonical Money Flow evidence review/data-gap report; reports sanitized DB reachability/candle-table truth, blocks campaigns clearly when DB/schema data is unavailable, adds `partial_evidence_ready_with_data_gaps`, found no usable local `candles` table, generated no evidence packs, and adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.8 status: historical-data bootstrap and first real evidence-pack generation attempt; reports DB/schema/migration/candle-table truth, adds `--db-status-only`, confirms the explicit local DB is reachable but unmigrated with no `alembic_version` or `candles`, generated no evidence packs, and adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.8.1 status: evidence-review schema-truth/report-truth hotfix; requires `migrated_schema_ready` plus required `candles` / `instruments` / `symbols` tables before evidence-pack generation, aggregates top-level no-live/no-exchange flags from campaign results, generated no first real evidence packs, and adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.9 status: intended DB target and first-real evidence status phase; reports sanitized DB driver/host/port/name/user, intended strategy-validation DB truth, maintenance-database warnings, canonical candle import requirements, and confirms no real evidence packs were generated because the default intended `money_flow` DB host was unresolved and the explicit `127.0.0.1:54322/postgres` override was unreachable/ambiguous in this shell. It adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
- SV1.9.1 status: evidence-target truth, candle-import timestamp/provenance truth, and Obsidian memory-governance hotfix; ambiguous/non-intended maintenance DB targets now block evidence generation by default, timezone-naive imports are rejected by default unless a provenance-marked non-canonical override is used, stale Obsidian current truth is refreshed through SV1.9, and no first real canonical evidence packs were generated. It adds no strategy-rule changes, optimization, recommendations, paper/live trading, routing, exchange calls, or execution changes.
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

SV1.5.1 hardens that import/config truth before first real evidence review. Campaign `window_convention` text now uses strict approved metadata and rejects contradictory inclusive-start phrasing. Offline candle imports block existing-candle identity conflicts instead of retargeting symbol/instrument ids, enforce selected-timeframe row duration, reject non-finite/zero/negative/inconsistent OHLCV values and negative trade counts, and roll back invalid files without partial inserts or updates. Money Flow rules, routing, execution automation, exchange calls, paper/live trading, optimization, and evidence-review behavior remain unchanged.

SV1.6 adds first canonical evidence-review summaries. The review layer audits the canonical BTC and multi-symbol campaign configs, treats missing/thin/blocked data as a data-readiness gap rather than strategy failure, generates collision-safe evidence packs only when readiness audits are clean, and summarizes fill-timing/component/regime/drawdown/cost/no-trade/invalid observations plus manual paper-readiness review status. It is descriptive research only and does not approve paper trading.

SV1.7 turns the canonical evidence review into a first-real-run/data-gap workflow. Review output includes sanitized DB URL/source, DB reachability, `candles` table existence, persisted candle count when available, and blocking DB/schema errors. If the DB is unreachable or missing `candles`, canonical campaign rows are blocked with data-gap reasons and no evidence packs are generated. Mixed generated/blocked outcomes use `partial_evidence_ready_with_data_gaps`. The local SV1.7 run found the default `postgres` host unresolved and a reachable local Postgres endpoint without the Money Flow `candles` table, so canonical evidence remains insufficient until the DB is migrated/populated or candles are imported.

SV1.8 makes the historical-data bootstrap path explicit before first real evidence packs. Evidence-review output now includes Alembic version-table existence, applied migration revisions, repo migration heads, migration-current truth when derivable, schema status, migration hints, DB override hints, candle-table existence, and persisted candle count. The review CLI supports `--db-status-only` for read-only DB/schema/candle checks. The local SV1.8 run found the default `postgres` host still unresolved and the explicit `127.0.0.1:54322/postgres` target reachable but not migrated: no `alembic_version`, no `candles`, and no evidence packs.

SV1.8.1 hardens the evidence-review gate so first real evidence packs cannot be generated from schema truth that is merely partial or unknown. Evidence-pack generation now requires `migrated_schema_ready`, current Alembic migration truth, and required strategy-validation tables (`candles`, `instruments`, and `symbols`). A DB with only `candles`, missing Alembic truth, outdated/unknown migrations, or missing symbol/instrument schema is blocked as schema/data readiness. Top-level live-artifact and exchange-adapter flags are aggregated from campaign results rather than dataclass defaults. No first real evidence packs were generated in this hotfix.

SV1.9 makes the remaining first-real evidence blocker operationally explicit. Evidence-review DB status now reports sanitized driver, host, port, database name, username, target-role classification, and whether the configured target appears to be the intended strategy-validation database. Maintenance database names such as `postgres` are warning-coded instead of silently treated as canonical Money Flow DBs. Evidence-review summaries now include canonical candle import requirements for blocked/missing rows, including expected and missing counts plus example offline importer commands. The local SV1.9 probes generated no evidence packs: the default intended `money_flow` target used unresolved host `postgres`, and the explicit `127.0.0.1:54322/postgres` override was unreachable in this shell and is a maintenance database target requiring operator confirmation.

SV1.9.1 makes that target truth generation-blocking before first real evidence packs. Evidence-pack generation now requires a clearly intended non-maintenance strategy-validation DB target in addition to migrated/current schema and sufficient candles. Maintenance DB names such as `postgres`, `template0`, and `template1` block by default even if schema and candles are present. Offline candle imports reject timezone-naive timestamps by default; the explicit `--assume-naive-utc` override records `timestamp_assumption=assume_naive_utc` and warning/source provenance and should be treated as exploratory/non-canonical unless explicitly accepted by founder/operator review. Obsidian current-state notes and full project memory are refreshed through SV1.9, and no first real canonical evidence packs exist yet.

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
- SV1.5.1 candle imports must not silently retarget existing candle identity, accept timeframe-duration mismatches, persist malformed OHLCV rows, or leave partial new/updated candles after a failed file import.
- SV1.6 evidence review status is manual/descriptive only; `ready_for_founder_review` is not paper-trading approval, and `insufficient_data` is a data gap, not a Money Flow strategy failure.
- SV1.7 data-gap reports must not be treated as strategy results. A reachable DB without `candles` means schema/data readiness is missing, not that Money Flow failed.
- SV1.8 data-gap reports must not be treated as strategy results. A reachable DB without Alembic schema and `candles` means migrations and historical data are missing before canonical evidence can be reviewed.
- SV1.8.1 schema-gap reports must not be treated as strategy results. A `candles` table alone is not sufficient; canonical evidence packs require current Alembic truth and the required strategy-validation schema.
- SV1.9 evidence status reports must not be treated as strategy results. DB target ambiguity, unreachable hosts, missing migrated schema, and missing canonical candles are operational data-readiness gaps before Money Flow evidence review.
- SV1.9.1 target-truth reports must not be treated as strategy results. Ambiguous/non-intended maintenance DB targets cannot generate canonical evidence packs by default, and timezone-explicit candle sources remain preferred for first canonical evidence.
- Simulated validation trades must remain separate from `SubmittedOrder`.
- Manual-resolution inspection must not silently resolve venue or approval truth.
- Future agents must update their own coordination row instead of overwriting another agent's work.
