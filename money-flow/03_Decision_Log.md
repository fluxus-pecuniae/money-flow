# Decision Log

Append entries only. Do not rewrite prior decisions except to add a dated correction.

## 2026-05-01T05:39:34Z - Phase 7.3 - Obsidian Becomes Strategic Brain

- `decision`: Move full strategic project memory into the Obsidian vault and keep the repo-root `money_flow_project_memory.md` only as a compatibility pointer.
- `why`: Repo operational docs should stay concise and code-state focused, while founder intent, long-horizon memory, phase context, and cross-agent coordination need a richer project brain.
- `rejected_alternatives`: Keeping full strategic memory at repo root; treating Obsidian as a replacement for `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, or `TODO.md`.
- `follow_up_implications`: Future agents must read the Obsidian command center, current phase note, project memory, and coordination note before substantial work, then update relevant Obsidian notes after substantial work.

## 2026-05-01T05:58:03Z - Phase 7.3 - Approval-Gated Target-Choice Conversion Only

- `decision`: Add only the `target_choice_conversion` approval-consuming action hook for Phase 7.3.
- `why`: Phase 7.2/7.2.1 already proved approval-gated recommendation acceptance. The next safe automation step is converting the exact approved target choice into one child intent while keeping preview/readiness and submission explicit and separate.
- `rejected_alternatives`: Automating preview/readiness in the same phase; automating submitted-order handoff; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future action hooks must continue to consume one current-lineage approval for one same-target stage and must preserve dry-run/manual policy truth plus no-downstream-artifact boundaries.

## 2026-05-01T07:28:41Z - Phase 7.4 - Approval-Gated Preview/Readiness Only

- `decision`: Add only the `prepared_order_preview_and_readiness` approval-consuming action hook for Phase 7.4.
- `why`: Phase 7.3 already proved approval-gated target-choice conversion. The next safe automation step is running existing preview/readiness inspection for the exact approved child intent while keeping submitted-order handoff explicit and separate.
- `rejected_alternatives`: Treating approval as readiness eligibility; automating submitted-order handoff; calling adapter submit; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future submitted-order automation must remain a separate phase and must consume its own current-lineage approval plus existing readiness, live/routed gates, and submit-lease uncertainty guards.

## 2026-05-01T08:41:37Z - Phase 7.5 - Approval-Gated Submitted-Order Handoff Only

- `decision`: Add only the `submitted_order_handoff` approval-consuming action hook for Phase 7.5.
- `why`: Phase 7.4 already proved approval-gated preview/readiness inspection. The next bounded step is submitting the exact already-ready child intent through the existing explicit submit path while keeping readiness, live/routed gates, adapter/account authorization, and submit-lease uncertainty protections authoritative.
- `rejected_alternatives`: Treating approval as a readiness override; adding a route executor; adding broad auto-submit; retrying or failing over to another target; adding ranking/scoring/fanout/CBBO/target reselection.
- `follow_up_implications`: Future phases should harden/close out operator inspection, regression, and concurrency/uncertainty observability before considering any broader automation.

## 2026-05-01T09:40:47Z - Phase 7.5.1 - Post-Submit Approval Consumption Truth

- `decision`: Represent submitted-order-created / approval-consumption-failed truth as `consumption_pending` on the approval record.
- `why`: A persisted `SubmittedOrder` is real exchange/account truth. If approval consumption fails after that point, leaving the approval clean-active would be misleading and could obscure which approval authorized the handoff.
- `rejected_alternatives`: Rolling back `SubmittedOrder` truth after submit persistence; treating the approval as clean active; adding a retry executor; submitting again to repair approval state.
- `follow_up_implications`: Future operator tooling can inspect `consumption_pending` approvals and complete or manually reconcile approval state without creating another submitted order.

## 2026-05-01T12:02:56Z - Phase 7.6 - Close Controlled Automation With Safety Proof

- `decision`: Close Phase 7 with end-to-end safety regression and docs alignment rather than adding another automation action hook.
- `why`: The full controlled chain now exists. Before broader automation, the project needs proof that the chain remains exact-lineage-bound, same-target, no-SOR, no-fanout, no-reselection, and distinct across dry-run, approval, administrative consumption, action execution, readiness, and submitted-order handoff.
- `rejected_alternatives`: Adding a route executor; adding smart routing or best-binding selection; adding fanout; adding target reselection; expanding broad auto-submit; treating generic administrative approval consumption as action execution.
- `follow_up_implications`: The next major phase should be architecture-reviewed and should prioritize operator-grade observability, reconciliation/manual-resolution, concurrency/serialization hardening, and dashboard/read-only inspection depth before any broader automation scope.

## 2026-05-01T12:59:46Z - Phase 8.0 Direction - Operator Observability Before SOR

- `decision`: Shape Phase 8.0 as operator-grade observability and manual-resolution inspection for the accepted Phase 7 controlled automation chain.
- `why`: The platform now has enough approval-gated workflow depth that operators need a structured way to inspect desired-trade state, approvals, readiness, submitted-order handoff, uncertainty, submit leases, and next safe manual action before any future smart-routing work.
- `rejected_alternatives`: Jumping directly into smart routing; adding best-binding selection, CBBO, ranking/scoring, fanout, target reselection, or route-executor behavior; auto-resolving uncertainty; treating operator acknowledgement as exchange/account truth.
- `follow_up_implications`: Phase 8.0 should default to read-only inspection. Manual-resolution marker mutation should be deferred or kept strictly append-only, actor-stamped, reason-coded, audited, and non-executing.

## 2026-05-01T13:20:57Z - Phase 8.0 - Read-Only Operator Summary

- `decision`: Add a read-only operator routed workflow summary by desired trade and defer manual-resolution marker mutation to a later phase.
- `why`: Operators need one structured view of workflow artifacts, approval/gate state, manual-resolution requirements, submitted-order safety, submit lease uncertainty, and next safe action before any broader routing or automation work.
- `rejected_alternatives`: Adding marker mutation in the first observability phase; auto-resolving `consumption_pending` or submit-lease uncertainty; attaching submit/cancel/amend/retry to inspection; introducing smart routing, ranking/scoring, CBBO, fanout, target reselection, or route executor behavior.
- `follow_up_implications`: Phase 8.1 can design explicit actor-stamped manual-resolution markers or administrative reconciliation flows, but those must remain separate from exchange/account truth and trading actions.

## 2026-05-01T14:19:39Z - Phase 8.0.1 - Accept Obsidian Memory Refresh As Baseline

- `decision`: Accept the dirty Obsidian full-project-memory refresh as intentional strategic-memory baseline, update stale "Phase 8.0 proposed" wording to implemented Phase 8.0 / cleanup Phase 8.0.1 truth, and keep the repo-root `money_flow_project_memory.md` as a pointer only.
- `why`: Phase 8.0 code was accepted, but the working tree remained dirty because the earlier Obsidian refresh had not been committed. Future agents need a clean baseline and current Obsidian context before Phase 8.1.
- `rejected_alternatives`: Reverting the full project-memory refresh; moving accepted strategic notes into drafts; leaving the working tree dirty; treating the root pointer as canonical full memory again.
- `follow_up_implications`: Phase 8.1 can start from a clean repo/Obsidian baseline. Repo operational docs remain code-state truth, and Obsidian remains strategic memory and coordination.

## 2026-05-01T15:04:52Z - Phase 8.0.2 - Active Submit Lease Blocks Operator Summary

- `decision`: Treat unexpired `active` child-intent submit leases as `submission_in_progress` blockers in the read-only operator summary's submission-safety and next-safe-action truth.
- `why`: The summary already surfaced active leases but could still report approval-gated submit as safe while a submit lease was in progress, which is unsafe operator guidance even though no trading behavior changed.
- `rejected_alternatives`: Converting expired pre-adapter active leases into terminal uncertainty; adding manual-resolution mutation; changing submit behavior; adding a new action stage.
- `follow_up_implications`: Strategy Validation can begin after this hotfix is accepted. Phase 8.1 remains deferred until manual-resolution marker semantics are explicitly scoped.

## 2026-05-01T17:40:40Z - SV1.0 - Validate Strategy Before More Routing Scope

- `decision`: Add Money Flow strategy validation as a separate research/backtest boundary instead of expanding routing or execution automation.
- `why`: Phase 7 and Phase 8.0 made the controlled execution chain inspectable and safe enough to pause routing expansion. The highest business uncertainty is whether Money Flow produces measurable edge after fees and slippage.
- `rejected_alternatives`: Adding smart routing, best-binding selection, new automation action hooks, strategy-rule optimization, paper trading, or live execution changes in SV1.0.
- `follow_up_implications`: SV1.x should review deterministic reports and deepen validation before strategy optimization or paper trading. Validation artifacts must remain separate from live `SubmittedOrder` and routing/execution truth.

## 2026-05-01T18:12:47Z - SV1.0.1 - Make Backtest Assumptions Review-Safe

- `decision`: Harden the SV1.0 report truth by making fill timing explicit, separating closed-trade drawdown from mark-to-market drawdown, and expanding Markdown/JSON report detail.
- `why`: Founder/operator review can be misled if same-candle close fills or closed-trade-only drawdown are presented as neutral performance truth. Research reports need to show timing bias, drawdown methodology, assumptions, limitations, component metrics, and trade details before any paper/live decision.
- `rejected_alternatives`: Changing Money Flow strategy rules, optimizing parameters, adding paper trading, connecting validation to routing/execution, or treating backtest output as proof of profitability.
- `follow_up_implications`: SV1.1 can deepen data/regime coverage and review workflows, but strategy changes should wait for evidence and architecture review.

## 2026-05-01T18:41:11Z - SV1.1 - Comparative Validation Before Paper Trading

- `decision`: Add comparative Money Flow batch validation reports as descriptive research, not optimization or recommendation.
- `why`: One backtest does not answer whether Money Flow has edge. The founder needs to compare components/timeframes, fill-timing assumptions, symbols, windows, and cost assumptions before deciding whether paper trading is justified.
- `rejected_alternatives`: Changing Money Flow rules, adding parameter optimization, recommending a strategy variant, creating paper/live trading artifacts, connecting validation to routing/execution automation, or calling exchange adapters.
- `follow_up_implications`: SV1.2 should review comparative outputs and likely deepen data coverage and market-regime labeling before any paper-trading or strategy-rule changes.

## 2026-05-01T19:20:34Z - SV1.2 - Regime And Coverage Before Paper Trading

- `decision`: Add data-coverage and deterministic market-regime reporting to Money Flow validation as descriptive research diagnostics.
- `why`: A strategy can appear profitable overall while relying on one market regime or weak historical data coverage. Founder/operator review needs coverage warnings and regime-grouped performance before paper trading is considered.
- `rejected_alternatives`: Changing Money Flow rules, optimizing parameters, recommending a variant, adding paper/live trading, connecting validation to routing/execution, or using regimes as strategy filters.
- `follow_up_implications`: Future Strategy Validation should broaden historical data ingestion/coverage and review regime evidence before any paper-trading readiness or strategy-rule change is scoped.

## 2026-05-01T20:12:36Z - SV1.2.1 - Standardize Validation Window Truth

- `decision`: Use candle closes in `(start_at, end_at]` everywhere in Strategy Validation and keep blocked runs visible in grouped batch comparisons.
- `why`: SV1.3 campaign/evidence-pack reports would be misleading if adjacent windows double-counted boundary candles, if coverage could exceed 100% on unaligned windows, or if blocked runs disappeared from grouped comparison tables.
- `rejected_alternatives`: Keeping mixed inclusive/exclusive semantics; treating unaligned coverage as exact without warnings; filtering grouped comparisons down to completed runs only; changing Money Flow strategy rules or optimizing parameters.
- `follow_up_implications`: SV1.3 can build repeatable research campaigns on a cleaner window/coverage truth layer, while validation remains research-only and disconnected from live routing/execution.

## 2026-05-01T21:08:26Z - SV1.3 - Repeatable Research Campaign Evidence Packs

- `decision`: Add explicit JSON Money Flow research campaign configs plus timestamped evidence-pack output on top of the existing Strategy Validation batch runner.
- `why`: Founder/operator review needs repeatable evidence across symbols, components, fill timings, windows, fees, and slippage assumptions rather than isolated one-off backtests.
- `rejected_alternatives`: Adding parameter optimization; recommending a strategy variant; changing Money Flow rules; adding paper/live trading; connecting validation output to routing/execution automation; storing evidence as live execution artifacts.
- `follow_up_implications`: Future SV work should review campaign evidence packs, broaden historical data coverage where needed, and scope paper-trading readiness only after evidence review.

## 2026-05-02T05:22:25Z - SV1.4 - Evidence Readiness Before Paper Trading

- `decision`: Add canonical editable Money Flow campaign configs, campaign data-readiness audit, evidence-pack review checklist, and manual paper-trading readiness criteria without changing strategy rules.
- `why`: Evidence packs are useful only when data coverage and blocked runs are explicit and founder/operator review criteria are defined before any paper-trading decision.
- `rejected_alternatives`: Auto-approving paper trading from campaign reports; optimizing Money Flow rules; recommending a strategy variant; adding paper/live trading artifacts; connecting validation outputs to routing or execution automation.
- `follow_up_implications`: Next SV work should run/review canonical campaigns on real persisted data, backfill historical candle gaps where the audit shows weakness, and scope paper-trading readiness only after manual evidence review.

## 2026-05-02T06:57:28Z - SV1.4.1 - Evidence Packs Must Not Overwrite

- `decision`: Use `unique_suffix` as the default evidence-pack collision policy, with `fail_if_exists` available for explicit fail-fast workflows.
- `why`: Research evidence packs must behave like durable records. A same-campaign same-timestamp rerun should never silently replace an existing `manifest.json`, report, config copy, or README before SV1.5 starts generating real evidence.
- `rejected_alternatives`: Keeping `mkdir(..., exist_ok=True)` and overwriting files; relying on operators to avoid same-second runs; making the default fail unexpectedly for founder/operator workflows.
- `follow_up_implications`: SV1.5 can generate first real campaign evidence packs using stable final run ids and manifest collision truth. Future comparison tooling should use `final_run_id` / `final_evidence_pack_path` rather than assuming requested timestamps are unique.

## 2026-05-02T07:36:56Z - SV1.5 - Offline Public Candle Import Before Evidence Review

- `decision`: Use validated campaign window-convention metadata plus offline/public CSV/JSON candle import/upsert tooling as the first historical-data remediation path for canonical Money Flow evidence runs.
- `why`: SV1.5 needs a safe way to make missing persisted candles visible and remediable before first meaningful evidence-pack review. Offline/public imports are narrower than adapter-driven backfill, avoid private or order endpoints, and keep Strategy Validation separate from routing/execution automation.
- `rejected_alternatives`: Treating config `window_convention` text as behavior-changing; requiring live public adapter backfill for SV1.5; calling private exchange or order endpoints; creating live desired trades, approvals, routing artifacts, paper trades, or submitted orders from validation; changing Money Flow rules to fit available data.
- `follow_up_implications`: Future evidence review should rerun canonical audits after sufficient candle data is imported or confirmed. If per-candle source provenance becomes required, the candle persistence model may need a separate schema change; current import source labels are summary-only.

## 2026-05-02T08:21:54Z - SV1.5.1 - Historical Candle Import Truth Before Evidence Review

- `decision`: Harden campaign window-convention validation and offline candle imports before SV1.6 uses imported candles for first real evidence review.
- `why`: Evidence packs can be misleading if config text implies inclusive-start windows, if an existing candle can be silently retargeted to a different symbol/instrument identity, if row duration does not match the selected timeframe, or if malformed OHLCV rows partially persist. Import integrity must be fixed before saved campaign evidence is reviewed.
- `rejected_alternatives`: Treating contradictory `window_convention` text as harmless metadata; allowing existing candle identity retargeting during upsert; accepting timeframe-duration mismatches; accepting non-finite, zero, negative, or internally inconsistent OHLCV rows; allowing partial invalid-file imports; changing Money Flow rules, adding optimization, adding paper/live trading, routing, or execution behavior.
- `follow_up_implications`: SV1.6 can review canonical evidence packs on a safer historical candle substrate. Future provenance work may still add per-candle source fields, but SV1.5.1 remains schema-free and source labels remain import-summary-only.

## 2026-05-03T05:27:59Z - SV1.6 - First Canonical Evidence Review Is Descriptive Only

- `decision`: Add a canonical Money Flow evidence-review layer that audits canonical campaign configs, reports insufficient data directly, and generates collision-safe evidence packs only when data-readiness audits are clean.
- `why`: The founder needs a repeatable way to see which canonical campaigns can run, which are blocked by data, where generated packs are located, and whether evidence is ready for manual review without treating missing data as strategy failure or treating backtests as approval for paper trading.
- `rejected_alternatives`: Auto-approving paper trading from evidence summaries; treating insufficient data as a Money Flow failure; changing or optimizing Money Flow rules; adding strategy recommendations; adding paper/live trading artifacts; calling exchange adapters, private endpoints, or order endpoints; connecting validation output to routing/execution automation.
- `follow_up_implications`: Next work should import or verify enough public historical candles, rerun the canonical review with evidence generation enabled, and use founder/operator review before any paper-trading design is scoped.

## 2026-05-03T08:08:05Z - SV1.7 - Evidence Review Must Report DB/Data Gaps Before Packs

- `decision`: Make canonical Money Flow evidence review inspect and report sanitized DB reachability, candle-table existence, persisted candle count, and DB/schema blockers before attempting campaign evidence generation.
- `why`: SV1.6 showed the default `postgres` host could be unresolved in the local shell. First real evidence review must not hide connection/schema failures or present missing persisted candles as a strategy result.
- `rejected_alternatives`: Treating DB connection failure as a test-only concern; generating evidence packs from incomplete audits; treating a reachable database without `candles` as ready; changing Money Flow rules; importing data automatically from exchange/private/order endpoints; connecting validation to routing/execution automation.
- `follow_up_implications`: Evidence remains `insufficient_data` until a reachable migrated Money Flow database is available and populated with enough canonical BTC/ETH/SOL candles. Mixed future outcomes should use `partial_evidence_ready_with_data_gaps` so generated packs cannot be mistaken for complete canonical evidence.

## 2026-05-03T14:04:33Z - SV1.8 - Evidence Review Must Distinguish DB Reachability From Migrated Schema

- `decision`: Extend canonical Money Flow evidence review with DB/schema/migration bootstrap status and a read-only `--db-status-only` CLI path before evidence-pack generation.
- `why`: SV1.7 established that a local Postgres endpoint can be reachable yet still unusable for evidence review. Founder/operator review needs to know whether the intended DB is migrated, whether Alembic has recorded a current revision, whether `candles` exists, and whether canonical candles are present before interpreting campaign gaps.
- `rejected_alternatives`: Treating reachable-but-unmigrated DBs as simple candle-data gaps; applying migrations automatically to an ambiguous `postgres` database; generating placeholder evidence packs; importing candles without an explicit migrated DB target; changing Money Flow rules; adding optimization, recommendations, paper/live trading, routing, or execution behavior.
- `follow_up_implications`: Next Strategy Validation work should point at or create the intended Money Flow database, run Alembic to head, import public/offline BTC/ETH/SOL candles for the canonical windows/timeframes, rerun canonical evidence review with `--generate-evidence-packs`, and keep paper-trading design deferred until founder/operator review of real packs.

## 2026-05-03T14:40:50Z - SV1.8.1 - Evidence Packs Require Migrated Schema Truth

- `decision`: Gate canonical evidence-pack generation on `migrated_schema_ready`, current Alembic migration truth, and required strategy-validation tables (`candles`, `instruments`, and `symbols`) rather than raw `candles` table presence.
- `why`: Evidence packs should not be generated from a database whose schema state is unknown or partial. A `candles` table without Alembic truth or required symbol/instrument schema can mislead founder/operator research review before first real evidence packs.
- `rejected_alternatives`: Treating a `candles` table as sufficient schema truth; letting missing Alembic truth proceed to evidence-pack generation; allowing partial required schema to fail downstream during canonical review; relying on top-level no-live/no-exchange dataclass defaults rather than aggregating campaign results.
- `follow_up_implications`: First real evidence-pack work must use a reachable DB that reports `migrated_schema_ready` before generating packs. Missing/outdated migration truth remains a schema/data readiness gap, not a Money Flow strategy result.

## 2026-05-03T20:11:02Z - SV1.9 - Evidence Review Must Expose Intended DB Target And Import Requirements

- `decision`: Extend canonical Money Flow evidence review with sanitized DB target metadata, intended-database classification, maintenance-database warnings, and canonical candle import requirements before first real evidence packs.
- `why`: SV1.8/SV1.8.1 made schema readiness authoritative, but founder/operator review still needed clarity on which configured DB was intended for strategy validation and exactly which canonical candles are missing. A `postgres` maintenance database target should not be silently treated as canonical Money Flow evidence storage.
- `rejected_alternatives`: Treating any reachable Postgres database as intended; generating evidence packs from an ambiguous maintenance database; hiding canonical candle gaps behind generic blocked runs; changing Money Flow rules; adding optimization, recommendations, paper/live trading, routing, exchange calls, or execution behavior.
- `follow_up_implications`: Next work should use a reachable migrated non-maintenance Money Flow database, import or verify the reported canonical BTC/ETH/SOL candle requirements, and rerun evidence review with `--generate-evidence-packs` only after schema and data readiness are clean.

## 2026-05-03T22:02:39Z - SV1.9.1 - Evidence Generation Requires Intended DB Target And Explicit Candle Timezones

- `decision`: Block evidence-pack generation from ambiguous or non-intended maintenance DB targets by default, reject timezone-naive candle imports by default, and refresh Obsidian current-truth memory through SV1.9 before first real evidence packs.
- `why`: A migrated `postgres` maintenance database with candles would otherwise be able to produce canonical-looking evidence despite not being the intended strategy-validation DB. Similarly, silently treating naive public CSV/JSON timestamps as UTC could corrupt historical candle truth before first real evidence review.
- `rejected_alternatives`: Treating maintenance DB ambiguity as a warning only; adding a broad ambiguous-DB override in this phase; silently assuming UTC for naive timestamps; treating override-derived imports as clean canonical evidence; generating first real evidence packs before target/schema/candle truth is clean.
- `follow_up_implications`: SV1.10 can prepare a migrated non-maintenance Money Flow DB and import timezone-explicit canonical candles. If an override is ever added for ambiguous DB targets, it must be explicit, provenance-rich, and non-canonical by default.

## 2026-05-04T05:14:29Z - SV1.10 - Use Local `money_flow` DB But Do Not Generate Packs Without Candles

- `decision`: Treat `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow` as the intended local strategy-validation DB for this shell, migrate it to Alembic head, and keep canonical evidence generation blocked until real persisted candles exist.
- `why`: SV1.9/SV1.9.1 established that maintenance DBs and unknown schema cannot produce credible evidence. SV1.10 made the non-maintenance local DB concrete and current, but evidence review still found zero persisted candles, so generating packs would be misleading.
- `rejected_alternatives`: Using the `postgres` maintenance database; weakening DB-target/schema gates; generating placeholder evidence packs; treating missing candles as Money Flow failure; changing Money Flow rules; importing timezone-naive data as canonical.
- `follow_up_implications`: Next SV work should import timezone-explicit BTC/ETH/SOL candles for the 18 unique canonical requirements, rerun evidence review with generation enabled, and keep paper-trading design deferred until founder/operator review sees real evidence.

## 2026-05-04T06:06:09Z - SV1.11 - Seed Market Identity Before Candle Import

- `decision`: Add an offline/manual research-only market identity manifest plus seed/verify CLI before importing canonical candles.
- `why`: SV1.10 produced a migrated intended DB but no canonical BTC/ETH/SOL instrument or symbol rows. The candle importer correctly requires those mappings before candle writes, so evidence work needs a safe identity-readiness step before file import.
- `rejected_alternatives`: Auto-fetching exchange metadata; treating placeholder manifest values as live trading eligibility; importing candles without symbol/instrument mappings; changing Money Flow rules; generating evidence packs in this phase.
- `follow_up_implications`: Next SV work should have the founder/operator verify manifest tick/size values, seed or verify market identity, preflight timezone-explicit candle files, import candles only after preflight passes, and generate evidence packs only after target/schema/identity/data readiness is clean.
