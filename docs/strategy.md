# Strategy Layer

This is the canonical strategy document at head.

## Current Boundary

The platform is no longer just a signal engine, and it now has a controlled routing substrate with assessment, non-selecting route-readiness/data-sufficiency audit, controlled non-executing target recommendation, explicit recommendation acceptance into a non-executing target-choice audit record, explicit one-child-intent conversion, routed child-intent preparation/readiness inspection, gated explicit routed submission handoff, routed post-submit lifecycle/actionability inspection, routed reconciliation/lifecycle-event audit visibility, explicit routed order-shape policy input, and Phase 5.10 closeout regression coverage across those existing surfaces. Phase 5.10.1 adds a persisted `RouteReadinessAudit` layer that answers whether enough truthful data exists for recommendation; Phase 5.10.2 tightens that audit so quote data-source labels describe the audit runtime path, desired-trade side/quantity validity blocks readiness, malformed/non-finite/non-positive quote prices block without crashing, and default MARKET order shape is defaulted rather than explicit. Phase 6.0.x adds persisted `RoutingTargetRecommendation` records under the default `single_ready_candidate_only`: exactly one ready candidate can be recommended, zero ready candidates block, and multiple ready candidates block without rank, score, price comparison, CBBO, target-choice creation, child-intent creation, or submission. Phase 6.1 adds optional `explicit_binding_priority`, a deterministic operator-preference policy using nullable `MandateAccountBinding.target_recommendation_priority`; lower positive integers win, missing/malformed priorities block, and ties block. Phase 6.1.1 bounds accepted `policy_name` input, makes `target_recommendation_priority` clearing explicit, and proves the priority-selected candidate still blocks when its stored quote observation is stale at recommendation time. Phase 6.2 adds explicit operator-triggered acceptance of a successful recommendation into exactly one `RoutingTargetChoice`; acceptance revalidates recommendation status, audit freshness, quote freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency, then stops at target choice. Phase 6.2.1 extends that idempotency across duplicate successful recommendations from the same route-readiness audit and preserves original recommendation/audit acceptance timestamps while recording later checks separately. Phase 6.2.2 ensures blocked recommendations from an already accepted audit cannot use same-audit idempotency to become accepted-looking or `target_choice_created=true`. Phase 6.3 adds explicit operator-triggered conversion from an accepted recommendation-backed target choice into exactly one routed child `OrderIntent`, reusing the Phase 5.2 conversion machinery, preserving recommendation/audit/target-choice lineage, and returning an existing child intent for repeated or same-audit duplicate conversion attempts. Phase 6.4 lets recommendation-backed child intents use the existing prepared-order preview and submission-readiness endpoints, exposes recommendation/audit/target-choice/order-shape lineage as routed lineage in those responses, and revalidates current mandate/binding/account/symbol plus stored quote-observation truth before eligible readiness. Phase 6.4.1 blocks preview/readiness when the stored routed order-shape policy is missing, malformed, or drifts from the current `OrderIntent` order_type, limit_price, or reduce_only fields, and uses the readiness-time `quote_stale_at_readiness` reason code for stale stored quote observations at this surface. Phase 6.5 adds an internal JSON manual routed-flow harness that can explicitly call the existing controlled service path from desired trade through readiness and print artifact ids, statuses, reason codes, selected target facts, and routed lineage; default invocation inspects only and submission requires a separate danger-confirmation flag plus the existing gates. Phase 6.6 adds local harness timing for each executed manual-flow step through `elapsed_ms` plus a top-level `timing_ms.total`, while skipped steps remain omitted rather than represented as fake zero work. Phase 6.7-6.10 close Phase 6 by allowing explicit recommendation-backed single-target routed submission only through the existing gated submit path, preserving recommendation/audit/target-choice/readiness lineage on submitted orders and post-submit surfaces, adding read-only routed workflow inspection by desired trade, and freezing the end-to-end regression boundary. Phase 6.10.1 adds a persistence-backed explicit child-intent submit lease before adapter submission, preserves first submitted-order provenance while recording latest/retry submitted-order ids separately, and renames workflow static route facts to `same_target_lifecycle_summary` rather than actionability/recovery summaries. Phase 6.10.2 adds terminal `adapter_submit_persistence_unknown` lease truth so adapter-returned/local-persistence-failed attempts block later submits until operator reconciliation/manual cleanup instead of becoming stale-TTL replaceable. These measurements and routed workflow inspection are local/operator visibility only, not production route-executor telemetry. Phase 5.8 adds optional explicit MARKET/LIMIT policy input at conversion, but Phase 6 closeout still does not create hidden submitted orders, exchange submit calls outside the explicit submit action, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit. Reconciliation remains venue/account truth and route lineage/recommendation remains audit metadata only. It is still deliberately below auto-submit, splitting, target reselection, smart routing, route executor behavior, cross-binding/cross-venue recovery, and venue-quality optimization.

Phase 6.10.3 closes the adapter-in-flight uncertainty gap in explicit submission. The child-intent submit lease is now durably marked `adapter_submit_may_have_started` before `adapter.submit_order()` is called, so crashes, transport ambiguity, timeouts, or unknown adapter exceptions after that point cannot become TTL-retryable. Later submit attempts block with `submission_state_uncertain` and `manual_reconciliation_required` until operator reconciliation/manual cleanup. Stale pre-adapter `active` leases remain replaceable, and `SubmittedOrder` stays post-submit truth only.

Phase 7.0 introduces automation policy and dry-run automation planning without introducing automatic routing or automatic submission. The strategy/routing boundary now has explicit automation modes: `disabled`, `dry_run_only`, `approval_required`, and `explicit_automation_permitted`. Dry-run planning inspects an existing desired-trade routed workflow and reports which same-target steps are already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked. Operator approval remains first-class, and submitted-order handoff remains manual-only in Phase 7.0. The plan preserves route-readiness audit, recommendation, target-choice, child-intent, readiness, submitted-order, selected binding/account/venue/symbol, and no-fanout/no-CBBO/no-scoring/no-ranking/no-target-reselection/no-route-executor/no-auto-submit truth.

Phase 7.1 makes operator approval durable and reversible before any action-taking automation exists. Approval records authorize one same-target action stage only and can be active, revoked, consumed, or expired. They keep the plan/approval/action boundaries separate: approval records preserve lineage and policy snapshots, but they do not accept recommendations, convert target choices, create previews/readiness, submit orders, or call exchange adapters. Revocation is explicit while the approval is unused, and consumption only marks that a later action hook used the gate; it is not the action itself.

Phase 7.1.1 tightens approval truth before any action-taking automation exists. Approval records are reusable only when the current action-stage lineage fingerprint still matches the approval's stored scope; expired approvals are marked expired before reuse, stale-lineage approvals become `stale_lineage`, and gate inspection reports approved only for a non-expired active approval matching the current recommendation/audit/target-choice/child-intent/readiness/submitted-order and selected binding/account/venue/symbol facts. Approval remains separate from execution.

Phase 7.1.2 tightens that gate truth against the current automation policy. Active approvals can be created only for current steps that are `approval_required` or explicitly `automation_eligible`; `dry_run_only` and `manual_only` steps remain non-approvable, and gate inspection reports them as `dry_run_only` or `manual_only` even if an old active approval row exists. Approval still cannot outrun current policy, and no action execution is added.

Phase 7.2 adds the first action hook, but only for approval-gated recommendation acceptance. One valid current `recommendation_acceptance` approval can accept the exact approved `RoutingTargetRecommendation` into a created or reused `RoutingTargetChoice` through the existing acceptance logic, then records the approval as consumed with the target choice id. The hook preserves approval/action separation because it stops at target choice and creates no child intent, prepared-order preview, readiness assessment, submitted order, exchange call, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.

Phase 7.2.1 hardens that hook so the first approval-consuming action is not split across misleading partial commits. Approval validation, target-choice creation or reuse, recommendation/audit target-choice-created truth, approval consumption, and approval provenance update now commit together or roll back together. The generic approval consume endpoint remains administrative state marking only and still does not execute recommendation acceptance, conversion, readiness, or submission.

Phase 7.3 adds the second approval-consuming action hook and keeps it limited to target-choice conversion. One valid current `target_choice_conversion` approval can convert the exact approved `RoutingTargetChoice` into a created or reused child `OrderIntent` through the existing conversion validation/persistence helpers, then consumes the approval with child-intent and routed order-shape policy provenance. It creates no prepared order, readiness assessment, submitted order, exchange call, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit. Phase 7.3 also moves long-horizon strategic memory and cross-agent coordination into the Obsidian vault under `money-flow/`; repo operational docs remain implemented-code truth.

Phase 7.4 adds the third approval-consuming action hook and keeps it limited to prepared-order preview plus execution-readiness inspection. One valid current `prepared_order_preview_and_readiness` approval can run the existing preview/readiness path for the exact approved routed child `OrderIntent`, then consumes the approval with actor, intent id, preview key, readiness id/outcome/reason codes, and explicit no-submission provenance. Approval authorizes the inspection only; it does not force readiness eligibility, call adapter submit, create `SubmittedOrder`, invoke recovery/cancel/amend, use a route executor, fan out, rank/score, use CBBO, reselect targets, or auto-submit.

Phase 7.5 adds the fourth approval-consuming action hook and keeps it limited to submitted-order handoff for one already-ready routed child intent. One valid current `submitted_order_handoff` approval can call the existing explicit child-intent submit path for the exact approved child `OrderIntent`, and only if current readiness, live-submit and routed-submit gates, adapter/account authorization, routed lineage/order-shape truth, and submit lease/uncertainty guards still pass. Approval does not select targets, force readiness eligibility, bypass submit gates, retry elsewhere, fan out, rank/score, use CBBO, reselect targets, create a route executor, or add broad auto-submit. If submission blocks or becomes uncertain, the reason-coded execution truth and manual-reconciliation lease state remain authoritative.

Phase 7.5.1 hardens the approval side of that handoff. If the existing submit path persists or safely reuses a `SubmittedOrder` but the approval consumption update fails afterward, the approval becomes `consumption_pending` and records the submitted-order id, child-intent id, failure class/message, and manual approval reconciliation requirement. A repeat call with the same approval reuses that submitted order and attempts to complete consumption without another adapter submit. This preserves strategy/routing truth by making the partial approval state visible instead of leaving a clean active approval after a real handoff.

Phase 7.6 closes the controlled automation phase with safety-diligence regression. It does not add another action hook. The closeout proof exercises the full approval-gated chain and directly asserts that dry-run planning, approval creation, administrative approval consumption, action-specific consumption, `consumption_pending`, and submitted-order handoff remain distinct states. It also proves no best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit has appeared.

Phase 8.0 adds operator observability and manual-resolution inspection, not new trading behavior. The new operator summary by desired trade exposes existing routed workflow artifacts, approval states, gate truth, manual-resolution requirements, submitted-order handoff safety, submit-lease uncertainty, and next safe operator action without creating artifacts, consuming approvals, resolving manual states, or calling exchange submission. It helps operators see `consumption_pending`, stale-lineage/expired approvals, blocked recommendation/readiness, and `adapter_submit_may_have_started` / `adapter_submit_persistence_unknown` states before any future SOR work.

Phase 8.0.2 fixes a read-only truth gap in that operator summary. While an unexpired `active` child-intent submit lease exists, the summary now treats repeat submit as blocked by `submission_in_progress` and reports the next safe operator action as `submission_in_progress` with `safe_to_automate=false`; expired pre-adapter active leases remain stale-replaceable and terminal uncertainty remains manual-reconciliation-required. This is observability truth only, not a new action stage, trading behavior, manual-resolution mutation, route executor, fanout, target reselection, ranking/scoring, CBBO, cross-venue retry, or auto-submit. Phase 8.1 remains deferred, and SV1.0 now begins Strategy Validation as a separate research track.

UAT4.0 is dashboard/chart cockpit observability only. It visualizes committed UAT2 shadow records and UAT3.4 routed sandbox lifecycle records in the static dashboard with watchlist, market-data coverage, indicator labels, shadow/sandbox markers, route/equity-source cards, and routed-order ledger filters. It does not create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, strategy rule changes, routing expansion, private/signed/order endpoint calls, exchange API-key use, or dashboard order controls.

UAT4.1 is dashboard redesign only. It rebuilds the UAT dashboard into an exchange-style static workstation with a compact top bar, observation-only market rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs while preserving the same read-only local UAT2/UAT3.4 data boundary. It does not create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, strategy rule changes, routing expansion, private/signed/order endpoint calls, exchange API-key use, or dashboard order controls.

UAT0 completes a safety/security/runtime audit without changing Money Flow strategy rules. UAT0.1 adds scoped bearer authentication for sensitive `/api/v1` routes and an inspectable fail-safe runtime safety policy. UAT0.2 adds adapter runtime-policy guards before private/signed/order transport, public read-only classification, a Hyperliquid future-UAT1 read-only allowlist artifact, and representative redaction tests. UAT0.3 adds fixture-only top-20 observation-universe resolver policy, Hyperliquid public read-only info-type classification, and a fixture-tested runtime drawdown monitor model. UAT1 verifies actual public-read-only Hyperliquid endpoint behavior and a public no-key top-volume source under explicit public-read-only network gating, then resolves observation-only Hyperliquid supported assets. UAT1 does not run Money Flow live, approve paper trading, approve live trading, submit orders, call private/signed/order endpoints, use API keys, add routing behavior, or change Money Flow rules. UAT1.1 adds model/report-only shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification without running UAT2 or creating strategy/execution artifacts. UAT2 runs the current baseline Money Flow rule logic as no-order shadow observation across the UAT1 Hyperliquid top-20 universe using only public read-only candle snapshots. It writes shadow audit/report records only and creates no `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approval, routing, paper, or live artifacts. UAT2.1 visualizes that UAT2 output in the static dashboard and adds an informational UAT3 blocked readiness panel without enabling approval or order actions. UAT3.0 through UAT3.0.6 define and dry-run the sandbox/testnet order gate chain without changing strategy behavior. UAT3.1 uses that gate chain for one founder-approved manual sandbox lifecycle probe, which Hyperliquid rejected with sanitized account/API-wallet truth. UAT3.2 uses a separate approval and fixed-key readiness preflight and blocks before transport. UAT3.3 fixes Hyperliquid account targeting and precision for the same manual sandbox lifecycle boundary: normal master/user mode omits `vaultAddress`, subaccount/vault mode uses only the explicit target, and ETH price/size formatting follows Hyperliquid metadata precision rules; a later founder-approved follow-up verified accepted/open -> cancel -> reconcile with no open order. UAT3.4 operationalizes that success as a fixed-target sandbox routing pipeline and routed-order ledger for Hyperliquid testnet ETH only, with standard-perp equity active and unified/portfolio spot-clearinghouse equity fallback preserved. UAT3.1-UAT3.4 created no `StrategyDecision`, `SignalEvent`, production `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, smart routing/SOR/fanout/target reselection, evidence pack, or Money Flow rule change. The frozen evidence candidate remains Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline, but UAT observation is not ETH-only: it uses a top-20 high-volume supported-asset universe to validate platform behavior, symbol mapping, no-trade reasoning, risk visibility, and operator explainability. Top-20 inclusion is not strategy approval. UAT2 shadow reports compare `next_candle_open` and `next_candle_close`; `same_candle_close_research_only` remains research-only.

UAT3.0.5 does not change Money Flow strategy behavior. The exact private-read-only approval text is recorded, sandbox/testnet credential environment variables are verified locally, and one Hyperliquid testnet read-only account-state request produced `sandbox_drawdown_feed_live_fed_verified`. UAT3.0.6 still does not change strategy behavior: it wires a dry-run sandbox submit-path plan and gate chain around actual-submission approval, live-fed drawdown status, approval scope, risk, submit-lease, endpoint classification, and sandbox labels. UAT3.1 through UAT3.4 also do not change strategy behavior: every approved sandbox/testnet attempt is labeled `manual_sandbox_lifecycle_probe`, `not_strategy_signal`, and `not_performance_validation`. UAT3.4 is fixed-target sandbox routing operationalization, not Money Flow signal execution. Paper trading, live trading, additional sandbox orders beyond explicit founder approval, private order endpoints beyond explicitly approved lifecycle scopes, broad order/cancel/amend/retry behavior, and top-20 order submission remain unapproved.

SV1.0 begins Strategy Validation and shifts the immediate question back to Money Flow edge. The new validation boundary reads persisted historical candles, computes the same EMA/SMA/RSI/MACD indicators in memory, reuses the current Money Flow rules without optimization, and emits deterministic simulated-trade reports with explicit capital, fee, slippage, and sizing assumptions. Validation artifacts are research outputs only: `StrategyValidationTrade` is separate from `SubmittedOrder`, and the runner creates no desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing records, approval state changes, or exchange adapter calls.

SV1.0.1 improves research truth and report readability without changing Money Flow rules. Validation requests/reports now expose the fill timing assumption (`same_candle_close_research_only`, `next_candle_open`, or `next_candle_close`), explicitly label same-candle close fills as research-only and potentially optimistic, and report closed-trade drawdown separately from mark-to-market drawdown. The Markdown report now includes report identity/context, assumptions, aggregate metrics, component metrics/comparison, trade summary, no-trade/invalid reason counts, and prominent limitations. This is still not optimization, paper trading, live execution, routing automation, or proof of profitability.

SV1.1 adds comparative validation without changing the Money Flow strategy. The new batch report compares explicit sets of components/timeframes, fill-timing assumptions, symbols, date windows, and cost assumptions by running the existing validation engine repeatedly and summarizing observed metrics. It is intentionally descriptive: the report can show which run had the highest observed net PnL, lowest observed net PnL, highest observed win rate, largest observed mark-to-market drawdown, most trades, or least trades, but it does not call any variant optimal or recommended and it does not alter rules, optimize parameters, paper trade, live trade, route, submit, or call exchange adapters.

SV1.2 adds data-coverage and market-regime analysis without changing strategy behavior. Reports now show requested versus available candle coverage, missing-candle warnings where timeframe spacing is derivable, and deterministic trend/volatility labels such as `uptrend`, `downtrend`, `sideways`, `high_volatility`, `low_volatility`, and `unknown_or_insufficient_data`. Trade-level regime grouping uses the entry signal candle. These regimes are descriptive research labels only; they are not filters, optimization inputs, recommendations, paper-trading triggers, routing inputs, or execution instructions.

SV1.2.1 fixes window/coverage/comparison research truth before SV1.3 campaign reports. Money Flow validation now uses candle closes in `(start_at, end_at]` everywhere: closes exactly at the start boundary are excluded and closes on or before the end boundary are included. Data coverage counts expected close slots under that convention, warning-codes unaligned window boundaries, and never reports coverage above 100%. Batch comparison groups now include blocked runs and blocked reason counts while computing performance metrics only from completed runs. This changes reporting truth only; it does not change Money Flow rules, optimize parameters, recommend variants, create live artifacts, route, submit, call exchange adapters, or add paper/live trading.

SV1.3 operationalizes Money Flow research as repeatable named campaigns and evidence packs. A campaign JSON config expands explicit symbols, components, fill timings, named windows, fees, slippage, capital, and sizing into the existing batch validation runner, then saves normalized config, manifest, JSON, Markdown, and README files under a timestamped evidence-pack directory. Named windows retain the `(start_at, end_at]` candle-close convention, and human expected-regime annotations are report context only; they do not override computed regimes or alter Money Flow entries/exits. Campaign output remains descriptive research evidence, not optimization, not a strategy recommendation, not paper trading, not live trading, and not routing/execution input.

SV1.4 adds evidence-pack review discipline and data-readiness checks before paper-trading decisions. Canonical editable campaign configs now live under `configs/strategy_validation/campaigns/`, and `scripts/run_money_flow_research_campaign.py --audit-only` reports persisted candle readiness by symbol, component, and named window before running or interpreting a campaign. The audit keeps the `(start_at, end_at]` convention visible and reports expected candles, actual candles, missing candles, coverage percent, gap facts, warning reason codes, and likely blocked runs. Evidence-pack manifests and Markdown now include a founder/operator review checklist plus manual paper-trading readiness criteria. These criteria are not automated approval, not a strategy recommendation, not paper trading, not live trading, and not routing or execution input.

SV1.4.1 hardens evidence-pack integrity before first real campaign evidence packs are generated. The campaign writer no longer silently overwrites an existing pack when the same campaign is run with the same second-level timestamp. The default collision policy is `unique_suffix`, which writes a new run directory such as `20260502T070000Z-001`; `fail_if_exists` is available when operators prefer explicit failure. Manifests record the requested run id, final run id, final evidence-pack path, collision policy, collision occurrence, and suffix. This is research-record write safety only and changes no Money Flow rules, optimization, paper/live trading, routing, execution automation, live artifacts, or exchange calls.

SV1.5 adds historical-data readiness and first-canonical-evidence support without changing Money Flow rules. Campaign `window_convention` fields are validated as metadata against the authoritative `(start_at, end_at]` candle-close convention, so changing config text cannot change evaluation behavior or imply inclusive starts. Campaign audits can emit founder-readable Markdown summaries of symbols/components/windows with covered, thin, missing, blocked, likely-blocked, warning, and remediation facts. The offline candle import CLI accepts public CSV/JSON candles and duplicate-safe upserts them into the existing `candles` table for research backfill only. The import summary records the source label because the current candle persistence model does not store per-candle provenance. SV1.5.1 hardens the research-data truth boundary: contradictory `window_convention` text is rejected, existing candles cannot be silently retargeted to a different resolved symbol/instrument identity, imported row duration must match the selected timeframe, non-finite or invalid OHLCV/trade-count values are rejected, and invalid import files roll back without partial candle inserts or updates. SV1.5.1 still creates no strategy decisions, desired trades, child intents, readiness evaluations, submitted orders, approvals, routing artifacts, paper trades, live trades, or exchange/private/order calls.

SV1.6 adds the first canonical Money Flow evidence review without changing Money Flow rules. The review layer audits the canonical BTC and multi-symbol campaign configs, reports blocked or insufficient data directly, and generates collision-safe evidence packs only when the existing data-readiness audit is clean. The review summary is founder/operator-readable and includes generated pack paths, data gaps, fill-timing observations, component observations, regime observations, drawdown observations, fee/slippage observations, no-trade and invalid reason counts, and a manual paper-readiness review status. That status is descriptive only; it does not approve paper trading, create paper trades, recommend a variant, optimize parameters, route, submit, create live artifacts, or call exchange adapters.

SV1.7 runs the first real canonical evidence-review path or produces a concrete data-gap report when local persisted candle data is still unavailable. Evidence review output now includes sanitized DB URL, reachability, candle-table existence, persisted candle count when available, and connection/schema blockers. If the DB is unreachable or the `candles` table is absent, canonical campaign rows are blocked with explicit data-gap reasons and no evidence packs are generated. If some campaigns generate packs while others remain blocked, the overall status is `partial_evidence_ready_with_data_gaps` rather than clean readiness. The local SV1.7 run found the default `postgres` DB host unresolved and a reachable local Postgres endpoint missing the Money Flow `candles` table, so canonical evidence remains `insufficient_data` until a migrated/populated Money Flow database is available.

SV1.8 makes the historical-data bootstrap requirement explicit before first real evidence packs. The evidence-review service and CLI now report Alembic schema status, whether the `alembic_version` table exists, repo migration heads, applied migration revisions when available, migration-current truth when derivable, candle-table existence, and persisted candle count. The CLI supports `--db-status-only` so operators can verify the configured strategy-validation DB target without running campaigns or writing evidence packs. The local SV1.8 run confirmed the default `postgres` host is still unresolved and that `127.0.0.1:54322/postgres` is reachable only with explicit override but is not migrated: it has no `alembic_version` table and no `candles` table. Canonical BTC and multi-symbol campaigns therefore remain `insufficient_data`, no evidence packs were generated, and the next required work is applying migrations to the intended Money Flow DB and importing public/offline BTC/ETH/SOL candles for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`. No Money Flow rules, optimization, paper/live trading, routing, execution automation, live artifacts, or exchange calls were added.

SV1.8.1 fixes evidence-review schema truth before first real evidence packs. Canonical evidence-pack generation now requires `migrated_schema_ready`, meaning current Alembic migration truth and required strategy-validation tables (`candles`, `instruments`, and `symbols`) are present. A database with only a `candles` table, missing Alembic truth, outdated/unknown migrations, or partial symbol/instrument schema is blocked as schema/data readiness and does not produce packs. Top-level no-live/no-exchange flags are computed from campaign results. No Money Flow rules, optimization, paper/live trading, routing, execution automation, live artifacts, exchange calls, or first-real evidence-pack generation were added.

SV1.9 makes the first-real evidence blocker operationally explicit. The evidence-review status now shows the configured DB target components, target role/warnings, migration truth, required-table truth, and canonical candle import requirements for blocked rows. The local SV1.9 run still produced `insufficient_data`: the default `postgres` host was unresolved, the `127.0.0.1:54322/postgres` override was unreachable and not treated as the intended Money Flow database, no public/offline canonical candle files were available to import, and no evidence packs were generated. This is DB/schema/historical-data readiness only, not Money Flow strategy performance.

SV1.9.1 makes ambiguous/non-intended DB targets and timezone assumptions explicit guardrails before first real evidence packs. Maintenance database names such as `postgres`, `template0`, and `template1` block evidence generation by default, and offline candle imports reject timezone-naive timestamps by default unless the explicit `--assume-naive-utc` override is used and provenance-marked as exploratory. SV1.10 then creates/migrates the intended local `money_flow` DB at `127.0.0.1:5432`, verifies Alembic head plus `candles`, `instruments`, and `symbols`, and reruns canonical evidence review. Evidence remains `insufficient_data` because persisted candle count is zero; no packs were generated. The import checklist is now de-duplicated into 18 unique BTC/ETH/SOL candle requirements with expected/missing counts and timezone-explicit file requirements. SV1.11 adds research-only canonical market-identity seed/verify tooling plus candle-import preflight so operators can prepare BTC/ETH/SOL Hyperliquid perpetual USDC identity rows before importing candle files and can validate files/mappings without writing candles. SV1.11.1 makes non-dry-run identity writes require explicit operator verification and makes requirement-aware preflight the canonical coverage gate; row-level preflight alone is not proof that a file covers a canonical window. SV1.11.2 blocks that research seed from setting strategy/trading eligibility true and requires complete one-to-one input-to-requirement mapping before requirement-aware preflight can report import readiness. SV1.12 adds guarded canonical candle bundle import only: it writes candles only after DB/schema, operator-verified non-trading identity, timezone-explicit files, one-to-one mapping, exact requirement coverage, and importer guards pass, and it does not generate evidence packs. SV1.12.1 hardens operational import truth: partial per-file persistence is reported as `partial_import` under `explicit_partial_with_resume`, unmapped input files and missing requirements appear directly in operator output, and the local run remained blocked because identity rows and candle files were missing. SV1.12.2 adds a readiness-only layer and report: it checks whether identity can be seeded only with explicit operator verification, lists the exact 18 canonical candle files, and can run requirement-aware preflight when files are supplied, but still imports no candles and generates no evidence packs. SV1.12.3 adds an operational guarded import attempt wrapper that can seed only when operator verification, `verified_by`, and offline market-value confirmation are explicit, auto-maps files by the canonical suggested filenames, and runs guarded import only if the full bundle is present and preflight-ready; the local run remained blocked because identity verification and candle files were not supplied. SV1.12.4 keeps January 2026 as archival/vendor-data-required, adds a public Hyperliquid YTD/recent campaign config, and produces 9 local timezone-explicit public CSVs for the new plan. SV1.12.5 first extends public candle-readiness across supported venue adapters, then uses explicit operator approval to seed Hyperliquid BTC/ETH/SOL research-only non-trading identity, run the 9-file public campaign preflight, and import `25848` Hyperliquid candles into the intended migrated DB. SV1.12.5.1 verifies the DB/import/repo state and confirms the expected symbol/timeframe counts plus no-evidence-pack boundary before SV1.13. SV1.13 generates the first Hyperliquid public campaign evidence packs by expanding the public config into component-scoped evidence configs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`; the result is research-only Hyperliquid USDC perpetual evidence for founder review, not a strategy recommendation, paper/live approval, cross-venue result, or Money Flow rule change. SV1.13.1 interprets those packs without changing evidence numbers: grouped aggregate sums are explicitly not one account/scenario PnL, scenario-level fill/cost/drawdown rows are visible, and ETH `sleeve_1h` concentration is called out for manual founder review. SV1.13.2 adds `dynamic_equity_pct` capital sizing so each new validation trade can size from current realized equity after prior closed-trade net PnL; constant-notional replay remains the default, dynamic equity is still per-scenario rather than full portfolio/margin simulation, and paper-trading design remains deferred. SV1.14 adds trade-anatomy and market-structure diagnostics over existing Hyperliquid public evidence. It explains that Money Flow entries require constructive EMA/RSI/MACD/pullback-or-continuation conditions, entries below the RSI sleeve floor are not allowed, recent swing high/low diagnostics are descriptive only and not filters, ETH `sleeve_1h` is the clearest positive pocket, 15m and 4h weakness is visible, and later rule-change ideas are hypotheses only. SV1.15 tests those ideas as Strategy Validation-only overlays and attribution against the dynamic-equity baseline without changing production Money Flow; SV1.15.1 makes the overlay methodology limitations explicit. SV1.16 adds the rejected-signal replay substrate needed for true variants: per-candle production-rule decision and rejection context, RSI zones, EMA/MACD state, price-extension facts, market regimes, recent swing high/low diagnostics, chronological position occupancy, and dynamic-equity sizing. SV1.16.1 clarifies that production-rule-in-replay-state fields are not independent baseline-path truth after variant divergence and separates production-rule rejection counts from variant no-trade and variant-admitted-from-rejection counts. SV1.17 runs lower-RSI plus market-structure true replay experiments across BTC/ETH/SOL and `sleeve_15m`/`sleeve_1h`/`sleeve_4h`; each row is an independent dynamic-equity scenario compared to its same-symbol/same-component baseline, some variants improve losing baselines, and ETH `sleeve_1h` baseline remains the strongest above-starting-equity pocket. These replay variants are research-only and authorize no rule change. The static `apps/dashboard` dashboard visualizes local review artifacts, committed experiment/replay summaries, the UAT2 shadow summary, UAT3 design/readiness panels, UAT3.4 routed-order ledger truth, and UAT4.1 exchange-style cockpit layout for human review. It does not run validation, generate packs, import candles, call exchange endpoints, create approvals, submit orders, approve paper/live trading, optimize, or change rules.

The load-bearing strategy-to-execution boundary is:

- `StrategyDecision`
- `MandateDesiredTrade`
- `OrderIntent`
- `PreparedVenueOrder`
- `ExecutionReadinessAssessment`
- `SubmittedOrder`

Strategy decides what the mandate wants.
Planning and risk decide whether that desire is valid.
Routing assessment enumerates candidate bindings, and target choice can record one explicitly requested eligible binding as a non-executing audit fact.
Phase 5.2 can convert one explicit valid target choice into one binding/account-targeted child intent after revalidating current truth; Phase 5.8 makes that conversion use an explicit routed order-shape policy input/decision path instead of an implicit hardcoded shape.
Phase 5.3 can inspect preparation/readiness for that converted child intent after revalidating route-origin lineage, and Phase 5.3.1 hardens that validation against selected-target provenance drift, child-intent client/mandate drift, target-choice desired-trade drift, and explicit routed submit attempts.
Phase 5.4 can submit that same already selected child intent only when an explicit submit action is invoked, route-lineage validation still passes, normal readiness is eligible, and both the normal live-submit gate and the separate routed-submit gate are enabled.
Execution acts only when a target binding/account is already known through a downstream child intent.
Mandate-scoped `open` no longer bypasses routing: it must pass through routing assessment and target choice before Phase 5.2 can create one child intent, and any routed submission must then pass preparation/readiness plus the Phase 5.4 explicit gated submit path.

## Money Flow As The First Strategy Family

Money Flow is the first strategy family, not the platform vocabulary.

Current Money Flow components:

- `sleeve_15m`
- `sleeve_1h`
- `sleeve_4h`

Money Flow currently supports:

- `open`
- `hold`
- `reduce`
- `close`
- `no_trade`
- `invalid`

The generic platform term is `component`.
Money Flow-specific `sleeve_*` naming remains family vocabulary only.

## What Is Implemented At Head

- deterministic indicator computation from persisted candles
- persisted indicator snapshots
- stale-indicator rejection against the latest candle boundary
- idempotent evaluation keys and persisted provenance
- modular strategy family framework
- Money Flow as the first implemented strategy family
- mandate-aware strategy evaluation context
- explicit source-policy-aware planning
- desired-trade drafting and convertibility rules
- first-pass desired-trade approval and rejection
- child-intent preparation only for naturally known binding/account targets
- venue-native prepared-order preview and preflight
- execution-readiness gating above prepared child intents
- truthful account-targeted submission for the currently implemented venue scopes
- submitted-order lifecycle below submission
- post-submit reconciliation
- truthful cancel lifecycle on supported scopes
- bounded same-target recovery execution beneath `SubmittedOrder`
- polling-based private order/account-state inspection beneath `SubmittedOrder`
  - venue-private open-order views remain distinct from platform `SubmittedOrder` truth
- non-executing routing assessment for routing-required mandate-scoped `open` desired trades:
  - `RoutingRequest`
  - `RoutingAssessment`
  - `RoutingCandidateAssessment`
  - persisted candidate inventory, eligibility/ineligibility reasons, and missing-data facts
- non-executing operator-requested target choice for one eligible candidate from a routing assessment:
  - `RoutingTargetChoice`
  - persisted recorded/blocked audit status
  - explicit reason codes, missing-data facts, and non-executing provenance
- non-selecting route-readiness/data-sufficiency audit:
  - `RouteReadinessAudit`
  - `RouteReadinessCandidateAudit`
  - persisted global and per-candidate missing, stale, unsupported, unavailable, policy-blocked, and blocking facts
  - data-source labels that distinguish persistence, venue query, adapter capability, static config, derived assessment truth, and unavailable truth
  - `ready_for_recommendation` as a data-sufficiency status only, with no recommended binding, rank, score, allocation, route plan, target choice, child intent, readiness evaluation, or submitted order
- controlled non-executing target recommendation:
  - `RoutingTargetRecommendation`
  - created only from an existing route-readiness audit
  - `single_ready_candidate_only` policy
  - exactly one ready candidate can be recommended
  - zero ready candidates and multiple ready candidates block
  - re-checks audit freshness, desired-trade truth, current mandate enablement, binding/account truth, desired-trade symbol identity, and active/trading-eligible symbol mapping truth before success
  - does not automatically create target choice, child intent, prepared order, execution-readiness assessment, submitted order, rank, score, allocation, route plan, fanout, CBBO, target reselection, or auto-submit
- explicit recommendation acceptance:
  - consumes one successful `RoutingTargetRecommendation`
  - creates exactly one non-executing `RoutingTargetChoice` only after another current-truth and quote-freshness revalidation
  - returns the original target choice for repeated acceptance of the same recommendation or duplicate successful recommendations from the same route-readiness audit
  - blocks same-audit reuse for blocked recommendations, leaving them `target_choice_created=false` and without accepted-looking provenance
  - records source recommendation, route-readiness audit, policy name, recommended binding/account/venue/symbol, accepted timestamp, and no-downstream-artifact flags in target-choice provenance
  - updates recommendation and source-audit inspection truth with `target_choice_created=true`
  - preserves the first recommendation/audit `recommendation_accepted_at` timestamp and records idempotent retry checks separately
  - creates no child intent, prepared order, execution-readiness assessment, submitted order, rank, score, allocation, route plan, fanout, CBBO, target reselection, or auto-submit
- explicit recommendation-backed target-choice conversion:
  - consumes one accepted recommendation-backed `RoutingTargetChoice`
  - reuses the existing target-choice-to-child-intent conversion path
  - creates or returns exactly one routed child `OrderIntent`
  - revalidates recommendation/audit/quote/desired-trade/mandate/binding/account/symbol truth before any new child intent
  - preserves routing target recommendation, route-readiness audit, routing assessment, target choice, selected binding/account/venue/symbol, recommendation policy, order-shape policy, and operator conversion timestamp in child-intent provenance
  - returns the existing child intent for repeated conversion of the same target choice or duplicate same-audit target-choice paths
  - creates no prepared order, execution-readiness assessment, submitted order, rank, score, allocation, route plan, fanout, CBBO, target reselection, route executor behavior, or auto-submit
- recommendation-backed child-intent preview/readiness:
  - uses the existing child-intent prepared-order preview and submission-readiness endpoints
  - validates source recommendation, route-readiness audit, route-readiness candidate quote freshness, current mandate, binding/account, active/trading-eligible symbol mapping, target choice, and routed child-intent lineage before eligible readiness
  - blocks if stored routed order-shape policy is missing, malformed, or no longer matches current child-intent order_type, limit_price, or reduce_only facts
  - reports stale stored quote observations at preview/readiness time with `quote_stale_at_readiness`
  - exposes recommendation id, route-readiness audit id, routing assessment id, target-choice id, selected binding/account/venue/symbol, recommendation policy, routed order-shape policy, and no-fanout/no-allocation/no-scoring/no-target-reselection/no-auto-submit flags as routed lineage in preview/readiness responses
  - can create/read `PreparedVenueOrder` preview data and `ExecutionReadinessAssessment` inspection records through the existing path, but creates no `SubmittedOrder`, exchange submit call, route executor behavior, fanout, CBBO, ranking/scoring, target reselection, or auto-submit
- explicit recommendation-backed submitted-order handoff and inspection:
  - starts from the same accepted recommendation-backed child intent after preview/readiness
  - uses only the existing explicit child-intent submit path and requires normal live-submit, routed-submit, readiness, adapter, and account gates
  - creates exactly one `SubmittedOrder` for the selected binding/account/venue/symbol when all gates pass
  - preserves desired-trade, routing assessment, route-readiness audit, routing target recommendation, target choice, child intent, readiness, selected target, recommendation policy, and routed order-shape lineage on submitted-order and lifecycle surfaces
  - exposes the chain through read-only routed workflow inspection without creating or mutating artifacts
  - remains same-target only and adds no auto-submit, route executor behavior, fanout, CBBO, ranking/scoring, target reselection, cross-binding recovery, or cross-venue retry
- Phase 7.0 routing automation substrate:
  - exposes policy inspection and dry-run plan APIs for the existing single-target recommendation-backed workflow
  - keeps the default automation policy disabled as an explicit kill switch
  - distinguishes dry-run-only, operator-approval-required, explicitly automation-eligible, manual-only, deferred, and blocked steps
  - creates no target choice, child intent, prepared order, readiness assessment, submitted order, exchange submit call, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit
- Phase 7.1 routing automation approval gates:
  - persist one approval record per explicit same-target action stage
  - expose approval creation, desired-trade inspection, revocation, and consumption state changes
  - Phase 7.1.1 scopes approval reuse to the current workflow lineage fingerprint, marks expired approvals expired before reuse, and marks stale-lineage approvals non-current
  - Phase 7.1.2 keeps manual-only and dry-run-only steps non-approvable and prevents gate-state output from showing them as approved
  - Phase 7.2 consumes a valid current recommendation-acceptance approval for exactly one approved recommendation and creates or reuses only the corresponding target choice
  - Phase 7.2.1 makes that target-choice creation/reuse and approval consumption commit together or roll back together
  - Phase 7.3 consumes a valid current target-choice-conversion approval for exactly one approved target choice and creates or reuses only the corresponding child intent
  - Phase 7.4 consumes a valid current preview/readiness approval for exactly one approved child intent and creates or reuses only the corresponding readiness inspection
  - Phase 7.5 consumes a valid current submitted-order-handoff approval for exactly one approved ready child intent and submits only through the existing explicit submit path when current readiness and submit gates pass
  - Phase 7.5.1 records `consumption_pending` if the submitted order exists but approval consumption fails after handoff, and repeat calls reuse the submitted order instead of submitting again
  - Phase 7.6 closes the controlled automation chain with regression proof and adds no new action stage
  - Phase 8.0 exposes read-only operator summary inspection for workflow state, approval/gate state, manual-resolution requirements, submit-lease uncertainty, submitted-order safety, and next safe operator action
  - preserve routed lineage, policy snapshots, selected binding/account/venue/symbol, and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit flags
  - execute no target reselection, alternate-route retry, fanout, ranking/scoring, CBBO, route executor behavior, or broad auto-submit; Phase 7.5 uses the existing explicit submit path only after one valid current approval is consumed and existing gates pass
- manual routed-flow inspection harness:
  - `scripts/manual_routed_flow.py` starts from an existing desired trade key and emits JSON trace output for operator/developer validation
  - default invocation inspects the desired trade only and skips submission
  - `--run-through-readiness` explicitly calls the existing assessment, audit, recommendation, acceptance, conversion, preview, and readiness service paths and stops before submission
  - Phase 6.6 adds top-level `timing_ms` plus per-step `elapsed_ms` using local monotonic timing so operators can see where harness/service-call latency is concentrated
  - timing values are local harness measurements, not production routing telemetry or venue/network latency unless a live path is explicitly invoked
  - `--submit` is blocked locally unless `--i-understand-this-can-place-a-live-order` is supplied; confirmed submit attempts still use the existing service-layer readiness/live/routed/adapter gates
  - adds no smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, or new exchange behavior
- explicit target-choice-to-child-intent conversion:
  - consumes one `RoutingTargetChoice`
  - creates exactly one binding/account-targeted `OrderIntent`
  - preserves routing assessment / target-choice lineage in child-intent provenance
  - records routed order-shape policy facts in child-intent provenance
  - defaults to MARKET/no-limit/non-reduce-only when no policy input is supplied
  - supports explicit LIMIT only with a positive finite limit_price and modeled order-type support
  - blocks invalid, unsupported, or policy-mismatched order-shape requests before duplicate child-intent creation
  - hardens conversion against assessment id/ref/environment drift, desired-trade ownership/source drift, and binding mandate ownership drift
  - does not create prepared orders, readiness evaluations, submitted orders, fanout, scoring, or submission
- routed child-intent preparation/readiness inspection:
  - revalidates routing assessment / target-choice / desired-trade / binding / venue-account / symbol lineage before preview or readiness
  - Phase 5.3.1 also cross-checks selected-target provenance fields, child-intent client/mandate identity, target-choice desired-trade linkage, and venue-account client ownership before adapter preparation
  - uses the existing prepared-order preview and execution-readiness machinery
  - blocks stale or mismatched routed lineage with explicit reason codes
  - phase-blocks valid routed readiness with `routed_submission_deferred` unless the separate routed-submit gate is enabled
- controlled explicit routed submission handoff:
  - requires an explicit submit action for the already converted child intent
  - requires route-lineage validation, normal readiness, `EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED`, and `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED`
  - creates exactly one `SubmittedOrder` for the selected binding/account when all checks pass
  - records routing assessment / target-choice / selected target lineage in submitted-order raw payload
  - does not create extra child intents, fanout, scoring, CBBO, target reselection, route execution orchestration, or auto-submit
- routed post-submit lifecycle/actionability inspection:
  - submitted-order detail/list, recovery recommendation, recovery execution response, and actionability responses expose read-only routed lifecycle context where routed-origin raw payload exists
  - submitted-order reconciliation responses preserve routed audit payload and expose routed lifecycle context through the normal submitted-order response shape
  - submitted-order lifecycle-event responses expose read-only routed lifecycle context derived from the associated submitted order, not from duplicate parser logic
  - routed lifecycle context includes desired-trade key, routing assessment id, routing target-choice id, selected binding/account, selected venue, selected exchange symbol, readiness id, routed order-shape policy facts, and explicit same-target / same-account / same-venue boundaries
  - same-target retry of a routed submitted order preserves the existing routed lineage on the retry result without selecting another target
  - malformed routed payloads remain bounded with missing/malformed lineage facts on recovery/actionability surfaces as well as list/detail
  - routed recovery/actionability/reconciliation audit remains same-target only and does not permit alternate binding recovery, alternate venue recovery, target reselection, fanout, route executor behavior, scoring, CBBO, or auto-submit
- Phase 5.10 routing-substrate closeout:
  - end-to-end regression coverage proves the existing routed chain stays exactly-one-child-intent and explicit-submit-only
  - typed submitted-order lineage, routed lifecycle context, actionability/recovery, reconciliation, and lifecycle-event surfaces agree on selected route facts
  - update-payload `routed_submission` remains non-authoritative; platform-authored submitted-order raw payload lineage is the only route-origin source
  - selected same-venue secondary account targeting remains scoped to the chosen binding/account only
  - no fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, cross-binding/cross-venue recovery, or auto-submit is introduced
- Phase 5.10.1 route-readiness/data-sufficiency audit:
  - audits routing-required desired trades or existing routing assessments before controlled target recommendation
  - exposes missing/stale market data, quote freshness, symbol/constraint gaps, binding/account blockers, unsupported order shape, fee/balance/private-state availability, and data-source labels
  - labels quote facts from persisted assessment snapshots as derived from the existing assessment, not as a fresh audit-time venue query
  - treats missing side, missing/zero/negative quantity, and malformed/non-finite/non-positive quote prices as recommendation-readiness blockers
  - records default MARKET order-shape policy as defaulted rather than explicit
  - remains non-selecting, non-ranking, non-scoring, and non-executing
  - creates no `RoutingTargetChoice`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, fanout, CBBO, route plan, route executor behavior, target reselection, or auto-submit
- Phase 6.0.0 / 6.0.1 / 6.0.2 / 6.1 / 6.2 controlled target recommendation and acceptance:
  - creates persisted `RoutingTargetRecommendation` audit records only from route-readiness audits
  - keeps `single_ready_candidate_only` as default: exactly one ready candidate can recommend and multiple ready candidates block
  - adds optional `explicit_binding_priority`: lower positive operator-configured binding priority wins only when exactly one ready candidate has the winning priority
  - blocks zero ready candidates, missing/malformed/tied priorities, stale audits, stale desired trades, and stale candidate truth
  - marks the source route-readiness audit as `recommendation_created=true` after a recommendation record is persisted
  - Phase 6.2 can explicitly accept a successful recommendation into exactly one non-executing target choice and marks recommendation/source-audit `target_choice_created=true`
  - Phase 6.2.2 keeps same-audit idempotency limited to otherwise successful recommendations, so blocked recommendations cannot be marked accepted by an audit that already has a target choice
  - creates no child intent, prepared order, execution-readiness assessment, submitted order, fanout, CBBO, rank, score, allocation, route plan, route executor behavior, target reselection, or auto-submit
- native amend only on the currently proven venue/account/product scopes:
  - Hyperliquid perpetual limit orders
  - OKX current scoped limit-order paths
  - Coinbase Advanced Trade spot limit orders
  - Kraken spot limit orders

## What Is Not Implemented

- live routing execution beyond explicit same-target routed child-intent submission
- recommendation among multiple ready candidates beyond explicit operator-configured binding priority
- best-binding selection
- CBBO
- child-intent fanout or splitting across bindings
- mandate-scoped open submission that bypasses assessment / target choice / conversion / readiness
- routed auto-submit or target reselection
- route-executor automation
- broad native amend parity across the full venue set
- cross-binding or cross-venue recovery execution
- broader portfolio-grade risk parity

## Indicator Pipeline

Indicators are computed from persisted candles, not from ad hoc in-memory exchange messages.

Current indicator set:

- `EMA(5)`
- `EMA(10)`
- `SMA(20)`
- `RSI(14)`
- `MACD(12,26,9)`

Current persistence rules:

- snapshots are keyed by environment, venue, instrument reference, timeframe, and `as_of`
- recomputation is idempotent
- incomplete states do not persist as full snapshots
- strategy evaluation requires the latest snapshot to align with the latest persisted candle close for the planning/source venue
- indicators remain venue/source scoped, not duplicated per account

## Strategy Framework

Current structure:

- `services.strategy.base`
- `services.strategy.engine`
- `services.strategy.money_flow`
- `services.runtime.context`

Current hierarchy assumptions for strategy:

- `StrategyMandate` is the logical strategy umbrella
- `MandateAccountBinding` is per-account participation and future routing eligibility
- `StrategyComponentConfig` is the family-specific internal component model
- one client can own many mandates
- one venue account can participate in many mandates through bindings

The platform should now be understood as:

- a strategy and planning system with first-pass approval today
- a mandate-aware umbrella over one or more venue accounts
- an execution-deeper platform with a routing assessment / target-choice substrate, one explicit target-choice-to-child-intent conversion path, routed preparation/readiness inspection, and explicit gated routed submission for the already selected child intent, but still not auto-submit, full live routing execution, fanout, target reselection, or venue-quality optimization

## Planning Source Policy

`MandateMarketDataSourcePolicy` is explicit and persisted.

It defines:

- the current planning/source venue
- optional market-type and product-type expectations
- how strict planning should be about canonical instrument identity

Important distinction:

- the planning/source venue is where the mandate currently gets signal and planning truth
- future routing venues are the bindings a later router may choose among

Those are related, but they are not the same concept.

## Money Flow Decision Flow

Money Flow currently evaluates:

- enough history exists
- component is enabled
- instrument is active
- instrument is strategy-eligible
- market data is fresh
- indicator snapshot exists
- indicator snapshot is aligned to the latest candle boundary
- bullish alignment: `EMA5 > EMA10 > SMA20`
- constructive RSI and MACD state where required
- pullback / continuation quality
- extension / overbought rejection

Possible outcomes:

- `proposed` with `open`
- `proposed` with `hold`
- `proposed` with `reduce`
- `proposed` with `close`
- `no_trade`
- `invalid`

Representative no-trade / invalid reasons:

- `insufficient_history`
- `missing_indicator_snapshot`
- `stale_market_data`
- `stale_indicator_snapshot`
- `sleeve_disabled`
- `instrument_inactive`
- `instrument_not_strategy_eligible`
- `overextended_rsi`
- `macd_not_constructive`
- `entry_quality_not_constructive`

## Desired Trade Versus Child Intent

This is one of the load-bearing platform boundaries.

Current convertibility rules:

- `proposed + open` -> mandate-scoped desired-trade draft
- `proposed + reduce` -> binding-scoped desired-trade draft when binding/account context exists
- `proposed + close` -> binding-scoped desired-trade draft when binding/account context exists and a bound open position exists
- `proposed + hold` -> non-convertible by default
- `no_trade` -> non-convertible
- `invalid` -> non-convertible

Current approval rules:

- approved mandate-scoped `open` desired trades stop at `routing_required`
- routing-required mandate-scoped `open` desired trades can now produce non-executing routing assessments and non-executing target-choice audit records
- approved binding-scoped `reduce` and `close` may create prepared child intents when target binding/account context is already known and policy checks pass
- `hold`, `no_trade`, and `invalid` do not create desired trades or child intents by default

Current routing assessment rules:

- routing assessment starts from a real `routing_required` `MandateDesiredTrade`
- routing assessment enumerates bound accounts as `eligible_for_future_selection` or `ineligible_for_future_selection`
- routing assessment records explicit reason codes and missing-data facts
- routing assessment may end as `assessment_only`, `no_eligible_bindings`, or `insufficient_data`
- routing assessment does not choose a binding, does not rank venues, does not create `OrderIntent`, and does not submit

Current route-readiness audit rules:

- route-readiness audit starts from a real routing-required `MandateDesiredTrade` or an existing `RoutingAssessment`
- when started from a desired trade, it may create candidate enumeration only as the assessment input to the audit
- route-readiness audit re-checks current desired-trade side and quantity, mandate, binding, venue-account, symbol, quote, capability, private-state, economic, and order-shape facts
- route-readiness audit does not claim quote `venue_query` unless a fresh audit-time query actually happens; current assessment-backed audits use `derived_from_existing_assessment`
- malformed, non-finite, zero, or negative quote prices are reason-coded as insufficient data and do not enter notional math
- default MARKET order-shape policy is `order_shape_policy_defaulted` / `market_order_policy_defaulted`, not explicit
- route-readiness audit records global and per-candidate missing, stale, unsupported, unavailable, policy-blocked, and blocking facts plus data-source labels
- `ready_for_recommendation` means required facts are currently data-sufficient for the recommendation layer; it does not itself mean any binding was recommended
- route-readiness audit does not create target choices, child intents, prepared orders, execution-readiness assessments, submitted orders, ranks, scores, allocations, route plans, fanout, CBBO, target reselection, or submissions

Current routing target recommendation rules:

- recommendation starts from one persisted `RouteReadinessAudit`
- API `policy_name` input accepts only omitted/null, `single_ready_candidate_only`, or `explicit_binding_priority`; malformed direct service policy input is rejected before persistence
- default recommendation succeeds only when the audit is fresh, the audit has exactly one candidate with `ready_for_recommendation`, the candidate's stored `quote_observed_at` remains fresh at recommendation creation time, and current desired-trade/mandate/binding/account/symbol truth still matches
- `explicit_binding_priority` must be requested explicitly and succeeds only when one ready candidate has the lowest positive `target_recommendation_priority`; missing priority, malformed/out-of-range priority, and priority ties block
- omitted binding-priority updates preserve the existing value; operators clear it only with `clear_target_recommendation_priority=true`
- disabled or missing mandates block recommendation success
- desired-trade symbol drift blocks recommendation success
- inactive or non-trading-eligible venue symbol mappings block recommendation success
- missing, malformed, timezone-invalid, or stale candidate quote observation facts block recommendation success
- zero ready candidates block with `blocked_no_ready_candidate`
- multiple ready candidates block by default with `blocked_multiple_ready_candidates`; no price, fee, venue-quality, rank, score, or CBBO selection occurs under any policy
- stale/not-ready/invalid audits, stale desired-trade truth, stale mandate truth, stale quote observation facts, and stale binding/account/symbol truth persist blocked recommendation records with explicit reason codes; audit-level global blockers remain visible even when zero-ready or multiple-ready candidate status is primary
- successful recommendation records the single ready candidate's binding, venue account, venue, and exchange symbol as audit metadata
- any persisted recommendation record updates the source route-readiness audit's `recommendation_created` inspection truth
- recommendation does not automatically create `RoutingTargetChoice`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, fanout, allocation, route plan, CBBO, target reselection, route executor behavior, auto-submit, or venue submission

Current recommendation-acceptance rules:

- acceptance starts from one persisted successful `RoutingTargetRecommendation`
- acceptance is explicit and operator-triggered through the recommendation acceptance endpoint/service call
- blocked recommendations, unknown recommendations, stale recommendations, stale quote facts, stale desired-trade truth, stale mandate truth, stale binding/account truth, and stale symbol mapping truth block acceptance
- repeated acceptance of the same recommendation returns the existing target choice rather than creating a duplicate
- duplicate successful recommendations from the same route-readiness audit return the existing target choice rather than creating a second target choice
- idempotent same-recommendation or same-audit re-acceptance preserves the original `recommendation_accepted_at` timestamp on recommendation/audit provenance and records last-checked metadata separately
- successful acceptance creates exactly one `RoutingTargetChoice` with source recommendation and route-readiness lineage in provenance
- successful acceptance updates recommendation and source route-readiness audit `target_choice_created` inspection truth
- acceptance does not create `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, fanout, allocation, route plan, CBBO, target reselection, route executor behavior, auto-submit, or venue submission

Current target-choice rules:

- target choice starts from one persisted routing assessment
- the API caller must explicitly provide the binding key or binding row id
- Phase 6.2 can also create a target choice from one explicitly accepted successful recommendation
- target choice can only record a candidate from that assessment when the assessment is `assessment_only` and the candidate is `eligible_for_future_selection`
- target choice blocks when the assessment has insufficient data, no eligible bindings, a missing candidate, an ineligible candidate, missing candidate facts, stale desired-trade truth, or stale binding/account truth
- target choice re-checks that the source desired trade is still a `routing_required` mandate-scoped `open` and is not already binding/account targeted
- target choice persists `RoutingTargetChoice` audit facts with `non_executing=true`
- target choice leaves `MandateDesiredTrade.status` as `routing_required`
- target choice does not create `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or venue submission

Current target-choice conversion rules:

- conversion starts from one explicit `target_choice_id`
- only `target_choice_recorded` target choices can convert
- conversion revalidates current assessment, candidate, desired-trade, binding, venue-account, and symbol-mapping truth
- conversion blocks if routing assessment lineage, desired-trade client/mandate/source identity, binding mandate ownership, or symbol mapping has drifted
- conversion creates exactly one `OrderIntent` for the selected binding/account
- conversion records route-origin lineage in child-intent provenance: desired trade, routing assessment, target choice, selected binding, selected venue account, venue, and exchange symbol
- conversion is idempotent by target choice; repeated conversion returns the existing child intent rather than creating another
- successful conversion marks the desired trade `routed`, meaning a child intent exists, not that execution or submission happened
- conversion does not create `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, fanout, scoring, CBBO, or submission

Current routed preparation/readiness rules:

- routed preview/readiness starts from an already converted child intent, not from an assessment or target choice directly
- the execution service verifies `OrderIntent.provenance` contains `routing_assessment_id` and `routing_target_choice_id`
- the execution service verifies selected-target provenance fields still match the converted child intent, target choice, routing candidate, current binding/account, and symbol mapping
- the execution service verifies the child intent's client/mandate identity and the target choice's desired-trade linkage still match the source desired trade and routing assessment
- the execution service verifies the current source desired trade is still `routed`, mandate-scoped, open, and not retargeted
- the execution service verifies current assessment, target choice, candidate, binding, venue account, instrument, and symbol-mapping truth still match the converted child intent
- stale desired-trade status, stale binding/account state, missing/mismatched route lineage, selected-target provenance drift, child-intent client/mandate drift, target-choice desired-trade drift, or changed symbol mapping produces blocked preview/readiness facts
- valid routed preview uses the existing venue-native prepared-order preview path and attaches routed lineage plus the current routed/live gate truth to the preview payload; preview remains non-submitting and explicit-submit-only
- valid routed readiness uses the existing `ExecutionReadinessAssessment` persistence path and records routed lineage in readiness provenance
- valid routed readiness remains phase-blocked from submission with `routed_submission_deferred` while `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED=false`, or `phase_live_submit_deferred` while the normal live-submit gate remains disabled
- valid routed readiness can become `eligible_for_submission` only when the routed-submit gate, normal live-submit gate, route-lineage validation, and normal readiness all pass

Current explicit routed submission rules:

- routed submission starts from an already converted child intent and an explicit submit action
- the execution service re-runs route-lineage validation and normal readiness immediately before adapter submission
- the execution service acquires a narrow `order_intent_submission_leases` guard after readiness/live/routed gates pass and before adapter `submit_order()`
- before the adapter submit call begins, the execution service writes terminal `adapter_submit_may_have_started`; later attempts block with `submission_state_uncertain` and manual reconciliation required until an operator resolves the uncertainty
- a concurrent explicit submit for the same child intent cannot make a second adapter call; before adapter-in-flight marking it blocks as in-progress, and after adapter-in-flight marking it blocks as uncertain, while a repeat after a `SubmittedOrder` exists returns existing submitted-order truth
- if adapter submit returns but local `SubmittedOrder` persistence fails, the lease becomes `adapter_submit_persistence_unknown` and later submit attempts block before adapter submission with `submission_state_uncertain` / `manual_reconciliation_required`
- routed phase-boundary submit blocks, including routed-gate and normal live-gate deferrals, record `last_submission_block` without marking the child intent as `submission_failed`
- successful routed submission uses only the child intent's selected binding/account/venue/instrument and creates exactly one `SubmittedOrder`
- submitted-order raw payload preserves desired-trade, routing assessment, target-choice, selected binding/account, selected venue, selected exchange symbol, and readiness evaluation lineage
- submitted-order API responses expose read-only routed-origin lineage derived from that raw payload, with missing, partial, or wrong-typed routed payloads reported as bounded missing/malformed-lineage facts instead of route decisions or execution instructions
- submitted-order API responses now also expose read-only routed lifecycle context on routed-origin detail/list, recovery, recovery-execution, and actionability surfaces; this context is audit metadata and keeps recovery scoped to the already submitted venue/account target
- submitted-order reconciliation responses and lifecycle-event responses preserve and expose the same read-only routed lifecycle context without turning route lineage into reconciliation truth; update payloads cannot create, overwrite, or mutate the platform-owned `routed_submission` audit payload
- non-routed submitted orders report no routed origin and do not fabricate routing ids
- recommendation/source-audit provenance preserves the first submitted-order id and first submitted timestamp permanently, while same-target retry updates latest/retry submitted-order ids separately
- routed submission does not create extra child intents, fanout, scoring, CBBO, target reselection, route execution orchestration, or auto-submit
- routed child-intent conversion now uses explicit routed order-shape policy input/decision: omitted input defaults to `MARKET`, no limit price, and non-reduce-only for mandate-scoped `open`; explicit `LIMIT` requires a positive finite requested limit price and modeled order-type support; non-finite prices block before child-intent creation without reporting `limit_price_explicit`; slippage guards and market-data-derived limit-price sources remain deferred before broader routed execution.

Current child-intent rules:

- `OrderIntent` is the downstream binding/account-targeted child-intent layer
- `PreparedVenueOrder` is the venue-native preview/preflight result for one intent on one venue/account path
- `ExecutionReadinessAssessment` is the persisted gate above one prepared venue order
- `SubmittedOrder` is exchange/account truth created only after explicit submission passes readiness and enablement checks

## Current Venue Truth That Strategy Can Rely On

Current integrated venue set:

- Hyperliquid
- Aster
- OKX
- Coinbase Advanced Trade
- Binance
- Kraken

Strategy can safely assume:

- canonical instruments are separate from venue-native symbols
- planning/source venue is explicit
- submit/cancel/amend/reconcile depth lives below `SubmittedOrder`
- venue-specific lifecycle depth does not change strategy semantics
- same-target recovery execution remains bounded to one already-targeted venue/account path

Current native amend truth below strategy:

- Hyperliquid: native amend in the current perpetual limit-order scope
- OKX: native amend in the current scoped limit-order path
- Coinbase Advanced Trade: native amend in the current spot limit-order scope
- Kraken: native amend in the current spot limit-order scope
- Aster: unsupported
- Binance: unsupported

Current private-state truth below strategy:

- no adapter currently claims implemented user-stream parity
- `/session-state` is adapter/runtime connection bookkeeping, not deep venue-private account session truth
- private lifecycle updates remain polling-driven at head
- Hyperliquid exposes direct open-order, recent-fill, and open-position truth for the current implemented scope when account context is available; direct open-position `mark_price` is nullable and is derived from `positionValue / abs(szi)` only when `markPx` is absent and both derivation inputs are usable
- Aster and Binance expose direct open-order truth, keep summary-layer recent-fill truth persistence-backed, and use submitted-at-bounded direct same-account/same-symbol private trade checks only as conservative retry-safety evidence when no exchange order id exists
- OKX, Coinbase Advanced Trade, and Kraken expose direct open-order and recent-fill truth for the current implemented scopes
- private-state summary source fields now describe the runtime path actually used for the call: `venue_query`, `persistence`, or `unavailable`

The venue-by-venue private-state matrix at head lives in [docs/architecture.md](architecture.md).

Current capability-surface truth below strategy:

- cancel and amend are now reported separately in public capability/status surfaces
- Aster and Binance expose truthful cancel support without implying amend support
- Hyperliquid, OKX, Coinbase Advanced Trade, and Kraken expose amend support only for the currently proven scopes

Current retry truth below strategy:

- retry is same-target only
- Aster and Binance require fresh retry client order ids
- retry remains blocked when duplicate exposure risk cannot be ruled out
- direct venue-private open-order evidence can block retry before a second live order is created
- Aster/Binance same-account/same-symbol private fill evidence is submitted-at-bounded and blocks retry as ambiguity when the submitted order has no exchange order id; stale fills before `SubmittedOrder.submitted_at` do not block on those paths, and the evidence is not treated as targeted order fill proof unless an exact exchange order id matches
- ambiguous Aster/Binance retry evidence is not exposed as plain submitted-order fill truth; it remains retry-safety evidence inside the scoped `SubmittedOrderPrivateFillEvidence` response

## Current Post-Submit Truth Below Strategy

The strategy layer should assume:

- `SubmittedOrder` is exchange/account truth
- reconciliation, cancel, amend, and recovery stay below `SubmittedOrder`
- cancel request, cancel acknowledgement, and final canceled state are distinct
- persisted fill evidence can enrich filled quantity, average fill price, and remaining quantity without degrading canceled, expired, or cancel-pending truth into generic partial-fill state
- recovery execution is same-target, same-venue, same-account only
- routing assessment and target choice remain non-executing; Phase 5.2 target-choice conversion creates a child intent only after explicit revalidation, Phase 5.3 routed readiness remains inspection-only, and Phase 5.4 routed submission requires explicit action plus separate gates
- no live routing execution beyond one explicitly selected routed child-intent submit handoff has been added
- no cross-binding retry or failover exists
- no mandate-scoped open execution exists without assessment, target choice, conversion, readiness, and explicit gated submission

## Still Deferred At Head

Still deferred:

- deeper mandate/account exposure and drawdown policy
- supersession and expiry policy for desired trades
- routed post-submit orchestration beyond read-only same-target lifecycle/actionability inspection for one explicit selected child-intent submission
- slippage expansion for routed order-shape policy beyond explicit requested limit prices, including market-data-derived price sources and price guards
- broader venue-native amend parity for Aster and Binance unless support is proven later
- user-stream / event-driven private lifecycle parity
- fuller direct order-state parity where a venue still falls back to persistence-backed truth
- routing-grade execution-quality market data

## Forward-Looking Concern

Phase 7.0 adds controlled automation policy and dry-run planning only, Phase 7.1 adds durable approval/revocation gates only, Phase 7.1.1 hardens approval expiry, lineage scope, and active-scope uniqueness before action-taking automation, Phase 7.1.2 keeps approvals limited to truly approvable current policy states, Phase 7.2 adds approval-gated recommendation acceptance only, Phase 7.2.1 makes that first action hook transactionally coherent, Phase 7.3 adds approval-gated target-choice conversion only, Phase 7.4 adds approval-gated preview/readiness inspection only, Phase 7.5 adds approval-gated submitted-order handoff only through the existing explicit submit path, Phase 7.5.1 bounds post-submitted-order approval-consumption failure truth, Phase 7.6 closes the controlled automation safety proof, Phase 8.0 adds read-only operator observability/manual-resolution inspection, SV1.0 adds the first Money Flow strategy-validation/backtesting reports without live artifacts, SV1.0.1 hardens fill-timing/drawdown/report truth without changing strategy rules, SV1.1 adds comparative validation batch reports without optimization or recommendations, SV1.2 adds data-coverage and descriptive market-regime diagnostics, SV1.2.1 fixes window/coverage/grouped-comparison truth, SV1.3 adds repeatable evidence packs, SV1.4 adds campaign data-readiness audit plus manual evidence-review criteria, SV1.4.1 makes saved evidence packs collision-safe, SV1.5 adds validated window-convention metadata, Markdown readiness summaries, and offline public candle import for research backfills, SV1.5.1 hardens import identity/duration/OHLCV/all-or-nothing truth before real evidence review, SV1.6 adds canonical evidence-review summaries plus manual paper-readiness status without approving paper trading, SV1.7 adds DB reachability/candle-table data-gap truth plus partial-evidence status after the first real local review attempt, SV1.8 adds DB/schema/migration bootstrap status plus an updated first-real data-gap report showing the reachable local DB is not migrated and has no candles, SV1.8.1 requires migrated/current schema truth plus required strategy-validation tables before evidence-pack generation, SV1.9 makes DB target identity and canonical candle import requirements explicit while evidence remains blocked, SV1.9.1 blocks ambiguous maintenance DB targets and naive timestamp imports by default, SV1.10 makes the intended local DB migrated/current while showing canonical candles are still missing, SV1.11 adds research-only canonical market identity bootstrap plus candle-import preflight, SV1.11.1 hardens operator-verified identity writes plus requirement-aware candle preflight, SV1.11.2 keeps research identity non-trading while requiring complete one-to-one preflight mapping, SV1.12 adds guarded candle import without evidence-pack generation, SV1.12.1 hardens guarded import run truth without importing candles or generating packs when identity/files are missing, SV1.12.2 adds readiness-only identity/file reporting without importing candles or generating packs, SV1.12.3 attempts the guarded import workflow but remains blocked without operator-verified identity and the 18 canonical files, SV1.12.4 creates a public-data-friendly 9-file Hyperliquid YTD/recent campaign plan while leaving January as archival/vendor-data-required, SV1.12.5 imports the operator-approved Hyperliquid 9-file public campaign after research identity/preflight gates pass while keeping supported non-Hyperliquid venues as later inventory, SV1.12.5.1 closes the import/repo state before evidence generation, SV1.13 generates first Hyperliquid public campaign evidence packs for founder review only, SV1.13.1 adds interpretation truth so grouped aggregate research sums and constant initial-capital notional sizing are not mistaken for one dynamic account-equity scenario, SV1.13.2 adds dynamic-equity per-scenario sizing/reporting while preserving constant-notional replay as default, SV1.14 adds trade-anatomy / market-structure diagnostics without using those diagnostics as filters, SV1.15 adds controlled research-only hypothesis experiments without changing production rules, SV1.15.1 clarifies that those experiments are methodology-labeled diagnostics, SV1.16 adds per-candle rejected-signal context plus a true replay runner so future lower-RSI and market-structure variants can be tested chronologically before any rule discussion, SV1.16.1 hardens replay-state field/counter truth before broader variants, SV1.17 runs full-suite true replay experiments across BTC/ETH/SOL and 15m/1h/4h, and SV1.18 closes the current evidence cycle by freezing only Hyperliquid ETH `sleeve_1h` baseline current rules as a UAT observation candidate. The next strategy-adjacent concern is UAT0 safety/security/runtime hardening for plumbing and behavior validation only, still short of paper/live trading and smart routing:

- SV1.x should use canonical evidence packs and readiness audits to decide what historical data must be backfilled before any paper-trading design, without optimizing or changing Money Flow rules until evidence justifies a research phase
- SV1.9.1 blocks evidence generation from ambiguous/non-intended DB targets such as maintenance database names (`postgres`, `template0`, `template1`) by default; first real canonical packs require a reachable migrated non-maintenance Money Flow DB target plus sufficient persisted candles
- SV1.9.1 rejects timezone-naive historical candle imports by default; the non-default `--assume-naive-utc` override is provenance-marked as `timestamp_assumption=assume_naive_utc` and should be treated as exploratory/non-canonical unless explicitly accepted by founder/operator review
- DB-level concurrency/serialization hardening should be considered before broader or multi-worker automation expands recommendation acceptance or conversion paths
- future action hooks beyond submitted-order handoff must consume one active, non-expired, current-lineage approval record for exactly one same-target action and must preserve revocation/expiry/stale-lineage/manual-only/dry-run-only truth
- slippage/price guard policy and richer market-data quality are prerequisites before any price-aware routing work
- continued mandate/account policy checks before any broader routed execution behavior
- fanout/splitting remains a later explicit phase only

Phase 7.5 and Phase 7.6 do not make the platform a routing optimizer, route executor, broad submitted-order automation system, or auto-submit system. They connect reversible operator authorization to the existing explicit submit path for one already-ready routed child intent only, then close that chain with safety assertions while preserving the separate strategy, planning, routing assessment, route-readiness audit, recommendation, target choice, child-intent creation, readiness, explicit submission, and post-submit lifecycle boundaries.
