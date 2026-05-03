# TODO

Last reviewed: `2026-05-03T22:02:39Z`

## Active Follow-Ups

### T-033

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.0 implemented the first controlled automation substrate without executing automation. It adds explicit routing automation modes (`disabled`, `dry_run_only`, `approval_required`, `explicit_automation_permitted`), a disabled-by-default policy inspection surface, and dry-run automation plans by desired trade that classify existing same-target recommendation-backed workflow steps as already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked. Plans preserve desired-trade, route-readiness audit, recommendation, target-choice, child-intent, readiness, submitted-order, selected target, and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit truth. Phase 7.0 creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-034

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1 implemented durable operator approval records and reversible action gating below action-taking automation. Approval records authorize exactly one same-target action stage, preserve policy snapshots plus desired-trade/recommendation/target-choice/child-intent/readiness/submitted-order lineage where present, and expose active/revoked/consumed/expired state through service/API inspection. Revocation is explicit while unused, consumption marks only that a future action hook used the gate, and approval creation/inspection/revocation/consumption does not accept recommendations, convert target choices, create readiness, submit orders, call exchanges, create a route executor, fan out, rank/score, use CBBO, reselect targets, or auto-submit.`

### T-035

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1.1 hardened approval truth before action-taking automation. Approval creation and inspection now expire old active records before reuse, mark approvals whose stored lineage no longer matches the current action-stage lineage as stale_lineage, expose lineage_fingerprint / approval_scope_key on approval records, and use a narrow partial unique active-scope index so repeated or concurrent creation cannot produce multiple active approvals for one desired trade / action / current lineage scope. Approval remains separate from execution and still creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-036

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1.2 finished the approval-truth substrate before action hooks exist. Approval creation now rejects dry-run-only, manual-only, disabled, deferred, blocked, and already-satisfied current steps; only approval-required and explicitly automation-eligible steps can create active approvals. Gate-state inspection keeps current policy truth authoritative, so existing approval metadata cannot make a manual-only or dry-run-only step appear approved. Approval remains separate from execution and still creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-037

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.2 implemented the first approval-consuming action hook and kept it limited to recommendation acceptance. One active, non-expired, current-lineage `recommendation_acceptance` approval can now accept the exact approved recommendation into a created or reused target choice through the existing Phase 6.2 acceptance path, then mark the approval consumed with actor, target choice id, and no-downstream-artifact provenance. Expired, revoked, stale-lineage, wrong-action, wrong-recommendation, consumed-for-different-recommendation, dry-run-only, and manual-only cases block before target-choice creation. Phase 7.2 creates no child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-038

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.2.1 hardened approval-gated recommendation acceptance coherence. The action now validates approval, creates or reuses the target choice, updates recommendation/audit target-choice truth, consumes the approval, and records approval provenance in one session/commit. A forced failure between target-choice flush and approval consumption rolls back without leaving a target choice or misleading active approval side effect. Repeated calls with the same consumed approval remain idempotent and preserve consumed_at. Generic approval consumption remains administrative only and executes no recommendation acceptance, conversion, readiness, submitted-order handoff, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-039

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.3 implemented the second narrow approval-consuming action hook and integrated the Obsidian strategic brain. One active, non-expired, current-lineage `target_choice_conversion` approval can now convert the exact approved `RoutingTargetChoice` into a created or reused child `OrderIntent` through existing conversion validation/persistence helpers, then consume the approval with actor, child-intent id, routed order-shape policy, and no-downstream-artifact provenance in one coherent session/commit. Invalid, expired, revoked, stale-lineage, wrong-action, wrong-target-choice, dry-run-only, and manual-only cases block before child-intent creation. Phase 7.3 also moved full strategic memory into `money-flow/Project_Memory/money_flow_project_memory.md`, made Obsidian command/current-phase/decision/coordination notes part of the required agent workflow, and left repo-root `money_flow_project_memory.md` as a pointer only. It creates no prepared order, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-040

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.3.1 hardened focused target-choice conversion tests before Phase 7.4. Direct tests now cover approval-gated conversion rejection for disabled, blocked, deferred, and already-satisfied current step states plus wrong recommendation id, wrong route-readiness audit id, and wrong desired-trade lineage. Each negative case asserts no new child intent, no readiness assessment, no submitted order, and truthful unconsumed or stale-lineage approval state. No product behavior, migration, config, preview/readiness automation, submission automation, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit was added.`

### T-041

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.4 implemented the third narrow approval-consuming action hook and kept it limited to prepared-order preview plus execution-readiness inspection. One active, non-expired, current-lineage `prepared_order_preview_and_readiness` approval can now run the existing child-intent preview/readiness path for the exact routed child `OrderIntent`, persist or reuse the readiness assessment, and then consume the approval with actor, intent id, preview key, readiness id/outcome/reason codes, and explicit no-submitted-order/no-exchange-submit/no-auto-submit provenance. Expired, revoked, consumed-for-different-child, wrong-action, wrong-child-intent, stale-lineage, disabled, blocked, deferred, already-satisfied, dry-run-only, and manual-only cases block before preview/readiness execution. Phase 7.4 creates no `SubmittedOrder`, calls no adapter submit path, and adds no route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-042

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.5 implemented the fourth narrow approval-consuming action hook: submitted-order handoff for one already-ready routed child intent only. One active, non-expired, current-lineage `submitted_order_handoff` approval can now call the existing explicit child-intent submit path, and only when current readiness, live-submit and routed-submit gates, adapter/account authorization, routed lineage/order-shape truth, and submit lease/uncertainty guards pass. Approval is consumed only after `SubmittedOrder` persistence or safe reuse; blocked readiness/gates and submit uncertainty remain reason-coded and authoritative. Phase 7.5 adds no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, new exchange behavior, or broad auto-submit.`

### T-043

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.5.1 hardened approval-gated submitted-order handoff truth. If the existing explicit submit path persists or safely reuses a `SubmittedOrder` but approval consumption fails afterward, the approval is moved to `consumption_pending` with submitted-order id, child-intent id, failure provenance, and manual approval reconciliation reason codes. Repeating the same approval-gated submit call reuses the existing submitted order and attempts to complete approval consumption without another adapter submit. Existing adapter-in-flight / adapter-returned persistence uncertainty and submit lease behavior remain intact. No new action hook, route executor, broad auto-submit, fanout, ranking/scoring, CBBO, target reselection, cross-binding/cross-venue recovery, or new exchange behavior was added.`

### T-044

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.6 closed out the controlled automation chain with safety-diligence regression coverage and docs alignment rather than a new action hook. The closeout test walks the full approval-gated chain from existing recommendation through recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff; proves each step consumes only the correct current-lineage approval; proves dry-run, approval creation, administrative consumption, action hooks, and submitted-order handoff remain distinct; proves `consumption_pending` is bounded and repeat calls reuse the existing submitted order without another adapter submit; and asserts no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit. No production behavior, migration, config, or new action stage was added.`

### T-045

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0 implemented the first operator-grade observability/manual-resolution inspection layer without adding trading behavior. The new read-only operator summary by desired trade aggregates existing routed workflow artifacts, approval states, approval gate truth, manual-resolution requirements, submitted-order handoff safety facts, submit-lease/concurrency state, blocking/uncertainty reason codes, no-SOR boundary flags, and next safe operator action. It surfaces `consumption_pending`, stale-lineage/expired approvals, blocked recommendations/readiness, `adapter_submit_may_have_started`, and `adapter_submit_persistence_unknown` without creating artifacts, consuming approvals, resolving manual states, calling exchange adapters, submitting/canceling/amending/retrying, ranking/scoring, using CBBO, fanning out, reselecting targets, or adding route executor behavior.`

### T-046

- `priority`: `high`
- `status`: `future`
- `summary`: `Define Phase 8.1 through architecture review before adding manual-resolution mutation. Candidate work should add explicit, actor-stamped, reason-coded manual-resolution markers or administrative reconciliation workflows for `consumption_pending` and submit-lease uncertainty, while keeping operator acknowledgement separate from exchange/account truth. SV1.0 begins Strategy Validation before Phase 8.1; Phase 8.1 remains deferred until that work is explicitly scoped. Smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, new action stages, and broad auto-submit remain deferred until explicitly designed and accepted.`

### T-047

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0.1 resolved the dirty Obsidian memory / working-tree baseline left after Phase 8.0. The earlier Obsidian refresh for accepted Phase 7.6 and proposed Phase 8.0 was accepted as intentional strategic-memory work, then updated to describe Phase 8.0 as implemented and Phase 8.0.1 as workflow hygiene only. The repo-root `money_flow_project_memory.md` remains a pointer only, the full project memory remains in `money-flow/Project_Memory/money_flow_project_memory.md`, and no product behavior, routing/execution logic, API behavior, schema, migration, smart routing, route executor behavior, auto-submit, or manual-resolution mutation was added.`

### T-048

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0.2 fixed operator-summary truth for active unexpired child-intent submit leases. The read-only operator routed workflow summary now treats an active lease as `submission_in_progress`, blocks repeat-submit safety with `blocked_while_submission_in_progress`, and reports the next safe operator action as `submission_in_progress` / `safe_to_automate=false`. Terminal adapter uncertainty remains manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and no trading behavior, new action stage, manual-resolution mutation, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, cross-venue retry, or auto-submit was added. SV1.0 now begins Strategy Validation as a separate research track; Phase 8.1 remains deferred until explicitly scoped.`

### T-049

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.0 adds the first Money Flow strategy-validation/backtesting framework. The new service reads persisted candles, computes indicators in memory, reuses current Money Flow strategy rules, simulates research-only trades with explicit capital/fee/slippage/sizing assumptions, and reports deterministic aggregate/component metrics plus no-trade and invalid reason counts. A CLI can emit JSON or Markdown reports. Validation artifacts remain separate from live execution: SV1.0 creates no desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing artifacts, approval state changes, or exchange adapter calls, and it does not optimize strategy rules.`

### T-051

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.0.1 hardens Money Flow validation report truth without changing strategy rules. Fill timing is now explicit and selectable as `same_candle_close_research_only`, `next_candle_open`, or `next_candle_close`; same-candle close is labeled research-only and potentially optimistic. Reports separate closed-trade drawdown from mark-to-market drawdown, add deterministic component comparison/reporting fields, expand Markdown with context, assumptions, aggregate metrics, component metrics, trade summary, reason counts, and limitations, and preserve validation as research-only output with no live desired trades, child intents, readiness, submitted orders, routing artifacts, approval changes, exchange calls, or strategy optimization.`

### T-050

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.1 adds comparative Money Flow validation batch reports. The batch runner executes explicit matrices of components/timeframes, fill-timing assumptions, symbols, date windows, fees, and slippage assumptions, then reports deterministic per-run metrics, assumptions matrix, fill-timing comparison, component comparison, optional symbol/date-window comparisons, observed top/bottom runs, warnings, and limitations. This is descriptive research only: it does not optimize Money Flow parameters, recommend a strategy variant, add paper/live trading, create live trading artifacts, call exchanges, route, or connect validation to execution automation.`

### T-052

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.2 adds data-coverage and market-regime analysis to Money Flow validation. Single-run and batch reports now include requested-versus-available candle coverage, expected/actual/missing candle counts where timeframe spacing is derivable, warning reason codes for thin/missing/gapped data, deterministic trend and volatility regime labels, regime-grouped performance summaries, and repeated CLI `--window start,end` support for multi-window comparison. Regimes are descriptive only and assigned by entry signal candle for trade metrics; they do not change Money Flow rules, optimize parameters, recommend variants, add paper/live trading, create live artifacts, call exchanges, route, or execute.`

### T-054

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.2.1 hardens Money Flow strategy-validation research truth before SV1.3 campaign/evidence-pack work. Validation windows now consistently use candle closes in `(start_at, end_at]` across strategy evaluation, data coverage, regime summaries, forced-close lookup, batch windows, CLI wording, JSON, and Markdown. Coverage expected counts now use expected close slots, unaligned window boundaries are warning-coded, coverage percent cannot exceed 100%, and grouped batch comparisons include blocked-run counts and reason counts while computing performance metrics only from completed runs. No Money Flow rules, optimization, strategy recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, or auto-submit were added.`

### T-053

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.5 adds historical-data readiness and first canonical evidence-pack support after SV1.4.1. Campaign `window_convention` metadata is validated against the authoritative `(start_at, end_at]` candle-close convention, canonical campaign audits can emit founder-readable Markdown summaries of covered/thin/missing/blocked rows and missing-data remediation notes, and the new offline public CSV/JSON candle import CLI duplicate-safely upserts existing `candles` rows for research backfills. Collision-safe evidence-pack generation remains intact. SV1.5 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchange private/order endpoints or adapters, and does not connect validation to routing or execution automation.`

### T-055

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.3 adds repeatable Money Flow research campaigns and saved evidence packs. A JSON campaign config names explicit symbols/instruments, components, fill timings, named `(start_at, end_at]` windows, fee/slippage assumptions, capital, sizing, output directory, and report formats. The campaign runner expands that matrix through the existing Strategy Validation batch service, writes normalized config, manifest, JSON report, Markdown report, and README files under `reports/strategy_validation/<campaign_name>/<run_timestamp>/`, preserves blocked-run visibility, and fixes the remaining single-run CLI wording mismatch so `--start` is no longer described as inclusive. SV1.3 changes no Money Flow rules, performs no optimization, recommends no variant, creates no live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-056

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.4 adds Money Flow evidence-pack review discipline and data-readiness baseline. Canonical editable campaign configs now live under `configs/strategy_validation/campaigns/`, the research campaign CLI supports `--audit-only` persisted-candle coverage/readiness inspection, evidence-pack manifests/Markdown include a founder/operator review checklist plus manual paper-trading readiness criteria, and operational-doc tests now assert the current phase line instead of stale historical text. SV1.4 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-057

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.4.1 hardens Money Flow evidence-pack integrity before SV1.5. Campaign evidence-pack writes now use an explicit collision policy: default `unique_suffix` creates a suffixed run directory when the same campaign/timestamp already exists, while `fail_if_exists` raises an explicit collision error. Pack files refuse overwrite, and manifests record requested run id, final run id, final evidence-pack path, collision policy, collision occurrence, and suffix truth. SV1.4.1 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-058

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.6 adds the first canonical Money Flow evidence-review layer. The review service and CLI audit the canonical BTC and multi-symbol campaign configs, report insufficient/missing/thin data directly, optionally generate collision-safe evidence packs only when the existing data-readiness audit is clean, and emit JSON/Markdown summaries with generated pack paths, data gaps, fill-timing/component/regime/drawdown/cost observations, no-trade/invalid reason counts, and manual paper-readiness review status. This is descriptive founder/operator research review only: no Money Flow rules were changed, no optimization or strategy recommendation was added, no paper/live artifacts are created, no exchange calls are made, and validation remains separate from routing/execution automation.`

### T-059

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.5.1 hardens the historical candle import and campaign-config research-truth boundary before SV1.6 evidence review. Campaign `window_convention` metadata now uses strict approved text and rejects contradictory inclusive-start phrasing. Offline public candle imports now block existing-candle identity conflicts instead of silently retargeting symbol/instrument ids, enforce row duration matching the selected timeframe, reject non-finite/zero/negative/inconsistent OHLCV values and negative trade counts, and roll back invalid files without partial inserts or updates. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or evidence-review behavior.`

### T-060

- `priority`: `high`
- `status`: `future`
- `summary`: `After SV1.9.1, point evidence review at a reachable migrated non-maintenance Money Flow database, import or verify enough timezone-explicit public historical candles for the canonical BTC/ETH/SOL campaign windows and `sleeve_15m` / `sleeve_1h` / `sleeve_4h` timeframes, rerun canonical evidence review with `--generate-evidence-packs`, and have the founder/operator manually review saved evidence before any paper-trading design is scoped. SV1.9 classifies the default configured `postgresql+psycopg://money_flow:***@postgres:5432/money_flow` target as the intended Money Flow DB but the host was unresolved in this shell; it also classifies `postgresql+psycopg://postgres:***@127.0.0.1:54322/postgres` as a maintenance database name. SV1.9.1 makes ambiguous/non-intended maintenance DB targets evidence-generation blockers by default and rejects naive candle timestamps by default unless the non-default `--assume-naive-utc` import override is explicitly used and provenance-marked as exploratory/non-canonical. SV1.8.1/SV1.9.1 require a clearly intended DB target, `migrated_schema_ready`, current Alembic truth, and required `candles` / `instruments` / `symbols` tables before evidence packs can generate. Canonical evidence remains `insufficient_data`, and SV1.9 reports exact import requirements for missing canonical candles. Do not optimize Money Flow rules, recommend a variant, add paper/live trading, create live artifacts, call exchanges, or connect validation outputs to routing/execution automation until manual evidence review explicitly justifies a new phase.`

### T-061

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.7 added first-real canonical Money Flow evidence-review/data-gap reporting. The review service and CLI now inspect sanitized DB URL/source, reachability, candle-table existence, persisted candle count when available, and blocking DB/schema errors before canonical campaign audits. Unreachable databases or databases missing `candles` produce explicit blocked data-readiness rows instead of uncaught failures or misleading evidence packs. Mixed generated/blocked outcomes use `partial_evidence_ready_with_data_gaps`. The local SV1.7 run audited `money_flow_core_btc.json` and `money_flow_core_multi_symbol.json`, found no usable persisted candle table, generated no evidence packs, and recorded the gap in `docs/strategy_validation_sv1_7_first_evidence_review.md` without changing Money Flow rules, optimizing, recommending a variant, adding paper/live trading, creating live artifacts, calling exchanges, routing, or connecting validation outputs to execution automation.`

### T-062

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.8 added historical data bootstrap and first-real evidence-pack generation truth. Evidence-review DB status now reports sanitized DB target, reachability, Alembic version-table existence, applied revisions, repo migration heads, migration-current status when derivable, schema status/reason codes, migration and DB override hints, `candles` table existence, and persisted candle count. The evidence-review CLI now supports `--db-status-only` for read-only DB/schema/candle readiness inspection. The local SV1.8 run found the default `postgres` host unresolved and the explicit `127.0.0.1:54322/postgres` target reachable but unmigrated with no `alembic_version` table and no `candles` table, so canonical BTC and multi-symbol campaigns remain `insufficient_data` and no evidence packs were generated. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, or exchange calls.`

### T-063

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.8.1 hardened evidence-review schema truth before first real evidence packs. Evidence-pack generation now requires `migrated_schema_ready`, current Alembic migration truth, and required strategy-validation tables (`candles`, `instruments`, and `symbols`); a DB with only `candles` is blocked if Alembic truth is missing, migrations are outdated/unknown, or symbol/instrument schema is partial. Top-level no-live/no-exchange flags now aggregate from campaign results. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or first-real evidence-pack generation.`

### T-064

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.9 made first-real canonical evidence status more operationally precise. Evidence-review DB status now reports sanitized driver, host, port, database name, username, intended strategy-validation DB truth, and target-role warnings; maintenance database names such as `postgres` are flagged as ambiguous instead of silently treated as the Money Flow strategy-validation DB. Evidence-review summaries now emit canonical candle import requirements for blocked/missing readiness rows, including symbol, timeframe, window, expected/actual/missing counts, file format expectations, and example offline importer commands. The SV1.9 local probes found the default intended `money_flow` DB host unresolved and the explicit `127.0.0.1:54322/postgres` override unreachable in this shell, so no first real canonical evidence packs were generated. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or import integrity behavior.`

### T-065

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.9.1 hardened evidence-target truth, candle-import timestamp/provenance truth, and Obsidian memory governance before SV1.10 attempts first real evidence packs. Evidence-pack generation now blocks ambiguous/non-intended maintenance DB targets such as `postgres`, `template0`, and `template1` by default even if schema/candles are otherwise present. No DB-target override was added. Offline candle imports now reject timezone-naive timestamps by default, and the non-default `--assume-naive-utc` override records `timestamp_assumption=assume_naive_utc`, source label, file path/name/hash, row counts, imported environment/venue/timeframe, override truth, and warning reason codes in the import summary. Obsidian command/current/dashboard/timeline/roadmap/project-memory notes were refreshed through SV1.9, operational docs tests now catch stale current-truth drift, and generated research/import outputs remain ignored by Git/review bundles. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or first-real evidence-pack generation.`

### T-001

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.0 implemented the first controlled routing substrate: non-executing routing request/assessment models, persisted candidate inventory, binary binding eligibility/ineligibility facts, explicit reason codes, missing-data facts, and operator inspection endpoints without best-binding selection, CBBO, child-intent fanout, mandate-scoped OPEN submission, or hidden cross-venue recovery.`

### T-011

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.1 added operator-requested non-executing target-choice audit records from persisted routing assessments, with explicit assessment/candidate/binding/account validation, blocked statuses, and no child-intent conversion, submission, fanout, CBBO, price/quality scoring, or mandate-scoped OPEN live submission. Phase 5.1.1 now revalidates the current source desired trade before recording a successful target choice.`

### T-012

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.2 implemented controlled target-choice-to-child-intent conversion, and Phase 5.2.1 hardened its lineage checks. One explicit recorded target choice can create exactly one binding/account-targeted child intent only after revalidating target choice, assessment id/ref/environment, candidate, desired-trade client/mandate/source identity, binding mandate ownership, venue-account, and symbol truth. Conversion is idempotent and still avoids preparation, readiness assessment, submission, fanout, CBBO, price/quality scoring, and live routing execution.`

### T-013

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.3 implemented the controlled routed child-intent preparation/readiness handoff, and Phase 5.3.1 hardened its lineage checks. Converted routed child intents can use existing prepared-order preview and readiness inspection only after route-lineage validation; stale desired-trade, routing assessment, target-choice, binding/account, selected-target provenance, child-intent client/mandate identity, target-choice desired-trade linkage, or symbol-mapping drift blocks explicitly. Phase 5.4 now controls routed submission behind a separate explicit gate, while Phase 5.3/5.3.1 still avoid fanout, CBBO, price/quality scoring, and target reselection.`

### T-014

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.4 added the controlled explicit routed submission handoff, and Phase 5.4.1 tightened its phase-boundary truth. A converted routed child intent can submit only through an explicit submit action after Phase 5.3.1 route-lineage validation, normal readiness, the normal live-submit gate, and the separate routed-submit gate pass. Routed phase-boundary submit blocks, including routed-gate and normal live-gate deferrals, preserve child-intent status and write last_submission_block rather than last_submission_failure. The path still avoids auto-submit, fanout, CBBO, venue scoring, target reselection, route executor behavior, and cross-binding recovery.`

### T-015

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.5 added the first routed submitted-order lineage inspection layer, Phase 5.6 tightened malformed-lineage type truth, Phase 5.7 added routed post-submit lifecycle/actionability context, Phase 5.7.1 preserved routed lineage through same-target routed retry while centralizing the routed lineage parser, Phase 5.9 extended that audit context to reconciliation/lifecycle-event surfaces, Phase 5.9.1 made existing platform routed_submission lineage authoritative over colliding reconciliation/update payload keys, and Phase 5.9.2 prevents update payloads from creating routed_submission lineage on non-routed orders. SubmittedOrder API responses now expose read-only routed-origin audit metadata derived from existing submitted-order raw payload; recovery recommendation, recovery execution response, actionability responses, reconciliation responses, and lifecycle-event responses expose same-target routed lifecycle context; non-routed orders/retries/events do not fabricate route ids; malformed routed payloads are bounded with missing-lineage and malformed-lineage facts; and same-target lifecycle behavior remains unchanged. No auto-submit, fanout, CBBO, venue scoring, target reselection, route executor behavior, migration, config, endpoint, or new execution behavior was added.`

### T-016

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.7 implemented the next controlled post-submit routed lifecycle inspection layer after Phase 5.5/5.6, Phase 5.7.1 hotpatched routed same-target retry lineage preservation plus parser deduplication, Phase 5.9 extended the same read-only context to reconciliation/lifecycle-event audit surfaces, Phase 5.9.1 prevents adapter/update payloads from overwriting platform-owned routed_submission audit lineage, and Phase 5.9.2 prevents adapter/update payloads from creating that lineage on non-routed orders. Routed submitted-order recovery/actionability/reconciliation/lifecycle-event surfaces are now route-aware but same-target / same-account / same-venue only, expose routed lifecycle context and malformed-lineage facts, preserve routed audit lineage on same-target retry and reconciliation update results, and still do not add auto-submit, fanout, CBBO, venue scoring, target reselection, cross-binding recovery, cross-venue retry, or route executor behavior.`

### T-017

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.6 defined the first explicit routed order-shape policy for target-choice conversion, Phase 5.8 expanded that policy to accept optional explicit MARKET/LIMIT inputs, Phase 5.8.1 hardened non-finite LIMIT price validation, and Phase 5.8.2 cleaned the malformed/non-finite LIMIT reason surface. Current default conversion remains MARKET / no limit price / reduce_only=false and remains visible in child-intent provenance. Explicit LIMIT now requires a positive finite limit_price and modeled order-type support, while slippage expansion, market-data-derived limit-price sources, auto-submit, fanout, target reselection, route executor work, and broader routed submission expansion remain future work.`

### T-018

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.8 added bounded explicit LIMIT order-shape policy input for routed target-choice conversion, Phase 5.8.1 blocks non-finite LIMIT prices before child-intent creation, and Phase 5.8.2 prevents malformed/non-finite blocks from reporting limit_price_explicit. LIMIT is not inferred and only works with an explicit positive finite limit_price plus modeled order-type support; invalid, non-finite, or unsupported policy blocks before child-intent creation. Slippage guard semantics and market-data-derived limit-price sources remain deferred without target reselection, fanout, CBBO, venue scoring, or auto-submit.`

### T-019

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.9 added routed post-submit reconciliation and lifecycle-event audit visibility only where code/test-proven, Phase 5.9.1 hardened reconciliation raw-payload merging so existing platform routed_submission audit lineage always wins over colliding update payload keys, and Phase 5.9.2 reserves that namespace so update payloads cannot create routed lineage on non-routed orders. Reconciliation responses preserve routed audit payload and expose routed lifecycle context, lifecycle-event responses derive the same context through the shared parser, malformed routed payloads remain bounded, non-routed events do not fabricate route ids, and recovery remains same-target / same-account / same-venue with no target reselection, route executor behavior, fanout, CBBO, venue scoring, auto-submit, cross-binding recovery, or cross-venue retry/failover.`

### T-020

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.10 closed the routing substrate with a focused end-to-end regression pass instead of new routing behavior. The closeout test exercises routing-required desired trade -> routing assessment -> explicit target choice -> exactly-one child-intent conversion -> routed preview/readiness -> explicit gated routed submission -> submitted-order detail/list -> actionability/recovery -> reconciliation with a colliding update-payload routed_submission -> lifecycle-event routed context, while proving selected-account scoping, platform-owned routed_submission namespace truth, typed routed lineage consistency, no extra child intents/submitted orders, and no fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, or auto-submit.`

### T-021

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.10.1 added the non-selecting route-readiness/data-sufficiency audit gate before future recommendation, and Phase 5.10.2 hotpatched its truth surface. Audits can be created from routing-required desired trades or existing routing assessments, persist global and per-candidate facts, expose missing/stale/unsupported/unavailable/policy-blocked/blocking reason codes plus data-source labels, label assessment-backed quote facts as derived from the existing assessment rather than fresh venue queries, block missing side and missing/zero/negative quantity, block malformed/non-finite/non-positive quote prices without crashing, and report ready_for_recommendation only as data sufficiency. Default MARKET audit policy is defaulted, not explicit. The audit does not recommend, choose, rank, score, create target choices, create child intents, prepare orders, assess execution readiness, submit, fan out, use CBBO, reselect targets, or execute.`

### T-022

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.0.0 begins controlled single-target recommendation above Phase 5.10.1 / 5.10.2 route-readiness audits, Phase 6.0.1 hotpatches its current-truth boundary, Phase 6.0.2 hotpatches recommendation-time quote freshness plus source-audit recommendation-created truth, Phase 6.1 adds optional deterministic binding-priority recommendation, Phase 6.1.1 tightens policy input / priority clearing truth, Phase 6.2 adds explicit recommendation acceptance into target choice only, Phase 6.2.1 hardens same-audit acceptance idempotency plus original timestamp truth, Phase 6.2.2 gates same-audit idempotency so blocked recommendations cannot be marked accepted, and Phase 6.3 adds explicit accepted recommendation-backed target-choice conversion into exactly one routed child intent. `RoutingTargetRecommendation` records are persisted from route-readiness audits only. The default policy remains `single_ready_candidate_only`: exactly one ready candidate can be recommended after audit freshness, stored candidate quote observation freshness, and current desired-trade/mandate/binding/account/symbol truth are re-checked. The optional `explicit_binding_priority` policy must be requested explicitly, uses nullable `MandateAccountBinding.target_recommendation_priority`, treats lower positive integers as the operator-preference winner, and blocks missing priority, malformed/out-of-range priority, ties, and stale quote observations for the selected candidate. API `policy_name` input is bounded to accepted policies; omitted priority updates preserve existing priority, and `clear_target_recommendation_priority=true` intentionally clears it. Successful recommendations can be explicitly accepted into exactly one non-executing `RoutingTargetChoice` after another current-truth and quote-freshness check; repeated same-recommendation or duplicate successful same-audit acceptance returns the existing target choice and preserves the original recommendation/audit accepted timestamp. Blocked same-audit recommendations remain blocked, retain `target_choice_created=false`, and do not receive accepted-looking provenance. Accepted recommendation-backed target choices can now be explicitly converted through the existing conversion path into exactly one child `OrderIntent`; repeated or duplicate same-audit conversion returns the existing child intent. Conversion still creates no prepared order, readiness evaluation, submitted order, rank, score, allocation, route plan, fanout, CBBO, route executor behavior, target reselection, exchange call, or auto-submit.`

### T-023

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.1 implemented the deterministic multiple-ready-candidate policy as explicit `explicit_binding_priority`, Phase 6.1.1 cleaned up its input and priority-clear semantics, and Phase 6.2 preserves that recommendation behavior while adding explicit acceptance into target choice only. The priority policy is request-level only, uses operator-configured binding priority, accepts only bounded known policy names through the API, preserves omitted priority on updates, clears priority only through `clear_target_recommendation_priority=true`, blocks missing/malformed/tied priority facts, blocks stale selected-candidate quote observations, and still does not create child intents, readiness evaluations, submitted orders, rank, score, allocation, route plans, fanout, CBBO, route executor behavior, target reselection, or auto-submit.`

### T-024

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.2 implemented the recommendation-to-target-choice workflow as an explicit operator-triggered acceptance action, Phase 6.2.1 hardens idempotency across duplicate successful recommendations from the same route-readiness audit, Phase 6.2.2 prevents blocked same-audit recommendations from bypassing validity through idempotency, and Phase 6.3 adds explicit accepted recommendation target-choice conversion into exactly one routed child intent. Acceptance creates or returns exactly one non-executing target choice, accepts only successful recommendations before new target-choice creation or same-audit reuse, revalidates recommendation status, audit/recommendation freshness, stored quote freshness, desired-trade/mandate/binding/account/symbol truth, records recommendation/audit/policy lineage in target-choice provenance, updates recommendation/source-audit `target_choice_created=true` only for valid acceptance, returns the existing target choice on repeated or duplicate successful same-audit acceptance, preserves the first recommendation/audit `recommendation_accepted_at`, and records idempotent retry checks separately. Blocked recommendations from an audit that already has a target choice remain `target_choice_created=false` and are not stamped with acceptance provenance. Phase 6.3 conversion validates accepted recommendation-backed lineage, reuses existing child intent conversion, updates recommendation/source-audit `child_intent_created=true` only after a valid child intent exists, and returns existing child intents for repeated or duplicate same-audit conversions. It does not create prepared orders, readiness evaluations, submitted orders, fanout, CBBO, ranking/scoring, auto-submit, cross-binding/cross-venue recovery, or route-executor behavior.`

### T-025

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.3 implemented the recommendation-accepted target-choice-to-child-intent workflow as a separate explicit operator-triggered phase. It reuses the existing target-choice conversion path, validates accepted recommendation-backed lineage and current truth before new child-intent creation, creates or returns exactly one routed child `OrderIntent`, preserves recommendation/audit/target-choice/order-shape lineage, and still does not create prepared orders, readiness evaluations, submitted orders, fanout, CBBO, ranking/scoring, auto-submit, cross-binding/cross-venue recovery, or route-executor behavior.`

### T-026

- `priority`: `medium`
- `status`: `future`
- `summary`: `Consider remaining persistence-level uniqueness guards or serialized paths for concurrent Phase 6 recommendation acceptance and accepted target-choice conversion if multiple workers can act on the same route-readiness audit or child intent simultaneously. Phase 6.2.1 uses application-level idempotency to return the existing target choice for repeated same-recommendation and duplicate successful same-audit acceptance, Phase 6.2.2 gates that same-audit reuse so blocked recommendations cannot appear accepted, Phase 6.3 uses service-level same-desired-trade/same-audit child-intent reuse, Phase 6.10.1 adds a narrow persistence-backed explicit child-intent submit lease so concurrent submit calls for one intent cannot both reach adapter submission before a SubmittedOrder exists, Phase 6.10.2 makes adapter-returned/local-persistence-failed submit uncertainty terminal until operator reconciliation/manual cleanup, and Phase 6.10.3 makes adapter-in-flight uncertainty terminal before the adapter call begins. These phases preserve original timestamps and add no broad workflow engine; future DB-level serialization for recommendation acceptance/conversion remains a hardening item before automation or multi-worker route execution.`

### T-027

- `priority`: `medium`
- `status`: `done`
- `summary`: `Initialized source-control hygiene for the Phase 6.3 baseline on the `master` branch. The baseline tracks source, tests, migrations, docs, operational memory, `.gitignore`, and `.env.example`, while `.env`, virtualenvs, caches, local database/runtime state, logs, review ZIPs, and handoff archives are intentionally ignored. Future phase work should use short-lived branches off `master`.`

### T-028

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.4 implemented the recommendation-backed child-intent preparation/readiness inspection handoff. Accepted recommendation-backed child intents now use the existing prepared-order preview and submission-readiness paths with additional validation for source recommendation, route-readiness audit, candidate quote freshness, current mandate, binding/account, and active/trading-eligible symbol mapping. Preview/readiness API responses expose routed lineage including recommendation/audit/target-choice/selected-target/order-shape facts. The phase creates no submitted orders, exchange submit calls, route executor behavior, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-029

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.4.1 hotpatched recommendation-backed preview/readiness truth. Routed child-intent lineage validation now blocks when stored routed order-shape policy is missing, malformed, or mismatched against the current OrderIntent order_type, limit_price, or reduce_only fields; readiness-time stale stored quote observations now use quote_stale_at_readiness. Tests prove order-type, LIMIT-price, reduce-only, missing-policy, and stale-quote blockers occur before adapter preparation/submission. No migration, config, endpoint, submitted order, exchange submit call, route executor, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit was added.`

### T-030

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.5 added a manual routed-flow inspection harness in scripts/manual_routed_flow.py. It starts from an existing desired trade key, emits JSON artifact traces, can explicitly call the current routing assessment, route-readiness audit, target recommendation, recommendation acceptance, target-choice conversion, prepared-order preview, and execution-readiness service paths through --run-through-readiness, and skips submission by default. Submit attempts are locally blocked without --i-understand-this-can-place-a-live-order and any confirmed submit still relies on existing service gates. Tests cover readiness-through flow output, default no-submission behavior, no SubmittedOrder creation, and local submit blocking. No smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, new exchange behavior, config, or migration was added.`

### T-031

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.6 added local per-step timing visibility to the manual routed-flow harness. scripts/manual_routed_flow.py now emits top-level timing_ms, including total runtime, and adds elapsed_ms to each executed step using monotonic timing. Default inspect-only still runs only the desired-trade step, --run-through-readiness still stops before submission, and --submit without the danger-confirmation flag still blocks locally before service submission while recording local submission-block timing. Tests verify timing shape, non-negative numeric values, omitted skipped-step timing, and continued no-submission behavior. No smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, new exchange behavior, telemetry persistence, config, or migration was added.`

### T-032

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.7 through Phase 6.10 close Phase 6 as controlled explicit single-target recommendation-backed routed execution, and Phase 6.10.1/6.10.2/6.10.3 hotpatch submit/workflow truth before merge. The accepted recommendation-backed child intent can create exactly one SubmittedOrder only through the existing explicit gated child-intent submit path; concurrent explicit submit calls are serialized with a persistence-backed child-intent submit lease before adapter submission; adapter-in-flight attempts are marked `adapter_submit_may_have_started` before adapter submission can begin; adapter-returned/local-persistence-failed attempts are marked `adapter_submit_persistence_unknown`; both uncertainty states block future submits until operator reconciliation/manual cleanup; submitted-order and lifecycle/actionability/recovery/reconciliation surfaces expose recommendation/audit/target-choice/intent/readiness lineage; same-target retry preserves the first submitted-order id while exposing latest/retry submitted ids separately; reconciliation payload collisions cannot overwrite platform-owned routed lineage or fabricate recommendation lineage on non-routed orders; and a read-only routed workflow inspection endpoint aggregates existing records by desired trade without creating or mutating artifacts. Closeout regression proves exactly one target choice, one child intent, one submitted order, selected account/venue/symbol consistency, and no hidden auto-submit, route executor, fanout, allocation, ranking/scoring, CBBO, target reselection, cross-binding recovery, or cross-venue retry.`

### T-002

- `priority`: `high`
- `status`: `future`
- `summary`: `Deepen the approval layer into broader mandate/account exposure, drawdown, concentration, and binding-policy checks without collapsing desired-trade approval into routing or execution.`

### T-003

- `priority`: `high`
- `status`: `future`
- `summary`: `Implement later routed execution orchestration only after the Phase 5.4 explicit selected-child-intent submission handoff has enough post-submit lifecycle depth. Target reselection, fanout, CBBO, price/quality scoring, and auto-submit remain out of scope until separately designed and tested.`

### T-004

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement execution-quality market data for top-of-book and depth summary across Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken with clearer parity expectations.`

### T-005

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement richer portfolio accounting and attribution overlays for mandate-aware and venue-account-scoped policy evaluation.`

### T-006

- `priority`: `medium`
- `status`: `future`
- `summary`: `Add additional strategy families without hardcoding the platform around Money Flow.`

### T-007

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement mandate-level routing across a binding account group after the live-execution layer below routing is mature enough, including later best-binding selection, CBBO support, quote comparison across bindings, and child-intent orchestration without static allocation weights.`

### T-008

- `priority`: `medium`
- `status`: `future`
- `summary`: `Extend mandate market-data / pricing source policy beyond the current single-source mode into richer source-policy behavior, including later composite pricing support and fuller decoupling between planning-source selection and routing venues.`

### T-009

- `priority`: `low`
- `status`: `future`
- `summary`: `Extend the six current venues beyond the current Phase 4.10.2 submit/reconcile/cancel/amend/recovery/private-state depth into broader truthful amend parity for Aster/Binance where support can be proven, fuller private-account streams, richer direct account-state/event parity, and deeper order-state visibility without blurring venue-private views into platform submitted-order identity.`

### T-010

- `priority`: `low`
- `status`: `future`
- `summary`: `Evaluate optional external execution backends such as CoinRoutes after the native decision/risk/intent/execution path is mature enough.`
