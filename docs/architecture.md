# Architecture

This is the canonical architecture document at head.

## Current System Posture

The platform is a client-centric, mandate-driven, multi-account, multi-venue trading system.

It is not:
- a single-exchange bot
- a routing engine
- a best-binding selector
- a CBBO engine
- a mandate-scoped open auto-submission or bypass-submission engine

At head, the platform has a controlled routing substrate with non-executing routing assessment / target-choice audit, non-selecting route-readiness/data-sufficiency audit, controlled non-executing target recommendation, explicit recommendation acceptance into a non-executing target choice, one explicit target-choice-to-child-intent conversion path, routed child-intent preparation/readiness inspection, a controlled explicit routed submission handoff, routed post-submit lifecycle/actionability inspection, routed reconciliation/lifecycle-event audit visibility, explicit routed order-shape policy input, and Phase 5.10 closeout regression coverage across that lifecycle. Phase 5.10.1 adds durable `RouteReadinessAudit` records that answer whether required facts are present before recommendation; Phase 5.10.2 tightens that audit so quote source labels describe the audit runtime path, desired-trade side/quantity validity blocks readiness, malformed/non-finite/non-positive quote prices block without crashing, and default MARKET order shape is labeled defaulted rather than explicit. Phase 6.0.0 adds durable `RoutingTargetRecommendation` records created only from a `RouteReadinessAudit` under the default `single_ready_candidate_only`: exactly one ready candidate can be recommended, zero ready candidates block, and multiple ready candidates block without ranking, scoring, price comparison, CBBO, allocation, fanout, target-choice creation, child-intent creation, readiness creation, or submission. Phase 6.0.1 hotpatches that recommendation boundary so success also revalidates current mandate enablement, desired-trade symbol identity, and active/trading-eligible venue symbol mapping truth before recording `recommended_single_ready_candidate`; Phase 6.0.2 also rechecks the recommended candidate's stored quote observation freshness at recommendation time and marks the source route-readiness audit as having a recommendation record after persistence. Phase 6.1 adds the optional `explicit_binding_priority` policy: callers must request it explicitly, priority comes from nullable `MandateAccountBinding.target_recommendation_priority`, lower positive integers win, missing/malformed priorities block, and priority ties block. Phase 6.1.1 bounds recommendation `policy_name` input to the accepted policies, rejects malformed direct policy names before persistence, makes priority clearing explicit through `clear_target_recommendation_priority`, and verifies priority-selected candidates still obey recommendation-time quote freshness. Phase 6.2 adds explicit operator-triggered acceptance of a successful recommendation into exactly one `RoutingTargetChoice`; acceptance revalidates recommendation status, audit freshness, quote freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency, then stops at target choice. Phase 6.2.1 hardens that acceptance idempotency so one route-readiness audit cannot produce multiple accepted target choices, duplicate successful same-audit recommendations return the original target choice, and original recommendation/audit acceptance timestamps remain stable while idempotent checks are recorded separately. Phase 6.2.2 gates same-audit idempotency behind successful-recommendation preflight so blocked same-audit recommendations cannot be marked `target_choice_created` or stamped with accepted-looking provenance. Phase 6.3 adds explicit operator-triggered conversion from an accepted recommendation-backed target choice into exactly one routed child `OrderIntent`, reusing the existing target-choice conversion path, preserving recommendation/audit/target-choice lineage, revalidating current truth before new child-intent creation, and returning an existing child intent on repeated or same-audit duplicate conversion attempts. Phase 6.4 lets recommendation-backed child intents enter the existing prepared-order preview and execution-readiness inspection paths, surfaces recommendation/audit/target-choice/order-shape lineage on preview/readiness API responses, and revalidates current mandate/binding/account/symbol plus stored quote-observation truth before eligible readiness. Phase 6.4.1 additionally blocks preview/readiness if the stored routed order-shape policy is missing, malformed, or no longer matches the current child intent order_type, limit_price, or reduce_only fields, and it uses `quote_stale_at_readiness` for readiness-time stale quote observations. Phase 6.5 adds a manual internal JSON inspection harness that can call those existing explicit service paths step-by-step from a desired trade through readiness and report ids, statuses, reason codes, selected target facts, and routed lineage; it defaults to inspection-only and blocks submit attempts unless the danger-confirmation flag is supplied. Phase 6.6 adds local monotonic per-step timing to that harness through top-level `timing_ms` and per-step `elapsed_ms`; this is local operator/developer measurement, not production routing telemetry or exchange latency unless a live path is explicitly invoked. Phase 6.7-6.10 closes Phase 6 as explicit recommendation-backed single-target routed execution: the accepted recommendation-backed child intent can create exactly one `SubmittedOrder` only through the existing explicit gated submit path; submitted-order detail/list, actionability, recovery, reconciliation, lifecycle-event, and same-target retry surfaces preserve recommendation/audit/target-choice/readiness lineage; and `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}` aggregates existing records read-only for operator inspection. Phase 6.10.1 adds a narrow `order_intent_submission_leases` guard acquired after readiness/live/routed gates and before adapter submission so concurrent explicit submit calls for one child intent cannot both reach the adapter before a `SubmittedOrder` exists; it also preserves first submitted-order provenance while exposing latest/retry submitted-order ids separately, and renames the workflow endpoint's static route facts to `same_target_lifecycle_summary` instead of actionability/recovery summaries. Phase 6.10.2 preserves post-adapter/pre-persistence uncertainty by marking adapter-returned/local-persistence-failed attempts as `adapter_submit_persistence_unknown`; later submit attempts for that child intent block with manual reconciliation required and cannot clear the uncertainty by TTL. This is operator preference, audit workflow, and local observability only, not venue quality, price, fee, spread, liquidity, rank, score, CBBO, best-binding selection, route execution, route-executor automation, or auto-submit. Reconciliation remains venue/account truth; route lineage and target recommendations are audit metadata, not execution instructions. It is still before auto-submit, fanout, target reselection, smart routing, route executor behavior, cross-binding recovery, cross-venue retry, and cross-binding execution orchestration.

SV1.18 closes the current Strategy Validation evidence cycle at the architecture boundary. It freezes only Hyperliquid ETH `sleeve_1h` baseline current rules as a UAT observation candidate and defines UAT as plumbing and behavior validation. It does not add exchange connectivity, paper/live trading, route execution, strategy-rule changes, new execution artifacts, or order submission paths.

UAT0 completes a safety/security/runtime readiness audit at the architecture boundary. It adds no exchange connectivity and makes no exchange calls. UAT0.1 adds scoped bearer authentication/authorization for sensitive `/api/v1` control-plane routes and an inspectable `RuntimeSafetyPolicy` with fail-safe defaults: paper trading, live trading, exchange order submission, and private exchange endpoints are disabled unless a later explicit phase enables and verifies them. UAT0.2 adds adapter-level runtime-policy guards before private/signed/order transport, classifies public read-only adapter methods, defines a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction tests. UAT0.3 adds fixture-only top-20 observation-universe resolution policy, Hyperliquid public read-only info-type classification for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`, plus a fixture-tested runtime drawdown monitor model. UAT1 verifies actual public-read-only Hyperliquid endpoint behavior and public no-key top-volume source ingestion under explicit `--uat1-public-read-only --allow-public-read-only-network` gating. It resolves observation-only Hyperliquid supported assets from the public top-20 source and creates a compact report/summary, but it still does not call private/signed/order endpoints, use API keys, submit orders, add paper/live behavior, add routing behavior, run Money Flow live, create strategy/execution artifacts, generate evidence packs, or change Money Flow rules. UAT1.1 adds model/report-only shadow signal audit records, UAT2 timing assumption representation, no-live-artifact boundary checks, UAT1 universe snapshot loading, operator-visible shadow drawdown state, and representative API-error / structured-log redaction verification. UAT2 adds an explicit bounded no-order shadow runner using the UAT1 observation universe and public Hyperliquid `candleSnapshot` data. It evaluates current baseline Money Flow rule logic without creating `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approval, routing, paper, or live artifacts. UAT2 shadow timing compares `next_candle_open` and `next_candle_close`; `same_candle_close_research_only` remains research-only. UAT2.1 adds static dashboard visualization for the UAT2 summary JSON, including signal matrix filters, would-open/no-trade review, ETH candidate status, timing/drawdown cards, boundary flags, and an informational UAT3 blocked readiness panel. UAT3.0 defines the future sandbox-order design and readiness requirements only: the initial sandbox subset is Hyperliquid ETH `sleeve_1h`, actual UAT3.1 sandbox submission remains blocked, and sandbox runtime enablement, sandbox account drawdown feed wiring, approval-scope verification, submit-lease lifecycle verification, risk gates, and sandbox artifact labeling are still required. UAT3.0.1 adds fixture-only readiness primitives for those requirements: fail-closed sandbox runtime policy, sandbox artifact-label validation, actual-submission approval-scope validation, sandbox risk-gate evaluation, sandbox drawdown feed fixture, and submit-lease duplicate-prevention checks. UAT3.0.2 hardens those primitives by propagating all runtime-policy blockers into risk/preflight output, rejecting non-positive sandbox numeric inputs, and adding a unified dry-run sandbox gate preflight that still creates no artifacts and calls no exchanges. UAT3.0.3 adds pure sandbox artifact label boundary helpers for persistence/API/dashboard/report surfaces and a dry-run executable gate service that composes runtime, label, approval, risk, drawdown, and submit-lease checks without side effects. UAT3.0.4 adds private read-only sandbox account/drawdown policy, credential approval/boundary validation, endpoint-category separation, redaction checks, and sandbox account drawdown feed modeling. UAT3.0.5 validates the exact private-read-only approval boundary, verifies sandbox/testnet credential environment checks, blocks live Hyperliquid endpoints, performs one Hyperliquid testnet read-only account-state request, and computes a `sandbox_account` / `not_live_account` drawdown feed with `sandbox_drawdown_feed_live_fed_verified`. UAT3.0.6 adds a non-persistent sandbox submission plan and dry-run submit-path gate service that consumes the live-fed drawdown status, requires separate founder actual-submission approval, validates sandbox labels before future persistence/API/dashboard/report boundaries, wires approval scope, risk, submit-lease, and endpoint-classification checks, and still reports `creates_order_intent=false`, `creates_prepared_order=false`, `creates_submitted_order=false`, `creates_executable_approval=false`, and `calls_exchange=false`. It sends no API key/private key, calls no order/cancel/amend/retry endpoint, creates no order artifacts or executable approvals, adds no order-enabling approval action, and changes no runtime execution behavior.

Phase 6.10.3 seals the earlier explicit-submit adapter-in-flight uncertainty gap. The execution service now writes terminal `adapter_submit_may_have_started` before calling the venue adapter. If a process dies, a transport timeout occurs, or an unknown adapter failure happens after that mark, later submits for the child intent block before adapter submission with manual reconciliation required. Stale pre-adapter `active` leases remain replaceable, `adapter_submit_persistence_unknown` still covers adapter-returned/local-persistence-failed attempts, and `SubmittedOrder` remains post-submit exchange/account truth rather than a pre-submit reservation.

Phase 7.0 adds a non-executing automation substrate, not automation execution. The routing service exposes explicit automation policy modes (`disabled`, `dry_run_only`, `approval_required`, and `explicit_automation_permitted`) and a dry-run plan over the existing desired-trade routed workflow. The plan classifies recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff as already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked while preserving lineage and boundary flags. The default policy is disabled. Phase 7.0 does not create artifacts, submit, select targets, rank venues, use CBBO, fan out, reselect targets, or introduce a route executor.

Phase 7.1 adds durable routing automation approval records and reversible action gating below action-taking automation. Approval records are one-action gates for the existing same-target chain, with states `active`, `revoked`, `consumed`, and `expired`; they preserve desired-trade, recommendation, target-choice, child-intent, readiness/submitted-order lineage where present, policy snapshots, selected binding/account/venue/symbol facts, and explicit no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit flags. Approval creation, inspection, revocation, and consumption do not execute the approved action and do not create target choices, child intents, readiness evaluations, submitted orders, exchange calls, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.

Phase 7.1.1 hardens that approval substrate so approvals are current-truth-bound rather than reusable by desired trade and action alone. The routing service now computes a deterministic approval scope/fingerprint from the desired trade, action, route-readiness audit, routing assessment, recommendation, target choice, child intent, readiness/submitted-order lineage where present, and selected binding/account/venue/symbol facts. Expired approvals are marked expired before reuse, stale-lineage approvals are marked `stale_lineage` and no longer satisfy the current gate, and a narrow partial unique active-scope index prevents multiple active approvals for the same current action scope. This is approval truth only; it adds no action execution or routing intelligence.

Phase 7.1.2 closes the final pre-action approval-truth gap. Approval creation is now valid only for current steps classified as `approval_required` or explicitly `automation_eligible`; `dry_run_only`, `manual_only`, `disabled`, `deferred`, `blocked`, and `already_satisfied` steps are not approvable. Gate-state inspection keeps current policy truth above stored approval metadata, so legacy or stale active approval rows cannot make a current manual-only or dry-run-only step appear approved. This still adds no recommendation acceptance execution, target-choice conversion execution, preview/readiness execution, submitted-order execution, route executor behavior, ranking/scoring, CBBO, fanout, target reselection, or auto-submit.

Phase 7.2 adds the first approval-consuming action hook and keeps it limited to recommendation acceptance. A valid active, non-expired, current-lineage `recommendation_acceptance` approval can be consumed to call the existing Phase 6.2 recommendation acceptance path for the exact approved recommendation, creating or reusing one `RoutingTargetChoice`. The approval is marked consumed with the actor, target choice id, and explicit no-child-intent/no-readiness/no-submission provenance only after target-choice creation/reuse succeeds. Expired, revoked, stale-lineage, consumed-for-another-action, wrong-action, wrong-recommendation, dry-run-only, and manual-only cases block before target-choice creation. Phase 7.2 does not automate target-choice conversion, preview/readiness, submitted-order handoff, exchange calls, route executor behavior, ranking/scoring, CBBO, fanout, target reselection, or auto-submit.

Phase 7.2.1 hardens the approval-gated recommendation acceptance action so target-choice creation/reuse and approval consumption are coherent in one session/commit. The routing service now uses an internal in-session acceptance helper for the approval-gated path: approval validation, target-choice creation or reuse, recommendation/audit target-choice-created truth, approval status consumption, and approval provenance update commit together. If approval consumption fails after a target choice is flushed but before commit, the transaction rolls back and leaves no persisted target choice or accepted-looking approval side effect. The generic approval consume endpoint remains administrative only and does not execute the approved action.

Phase 7.3 integrates the Obsidian strategic brain and adds approval-gated target-choice conversion only. The Obsidian vault under `money-flow/` now holds long-horizon strategic memory, phase context, decisions, and cross-agent coordination while repo operational docs remain implemented-code truth. The new `target_choice_conversion` action hook consumes one valid current-lineage approval to convert the exact approved `RoutingTargetChoice` into one child `OrderIntent` through the existing conversion validation and persistence helpers; approval consumption records the child intent id and no-prepared-order/no-readiness/no-submission truth. It does not automate preview/readiness, submitted-order handoff, recovery, exchange calls, route executor behavior, ranking/scoring, CBBO, fanout, target reselection, or auto-submit.

Phase 7.4 adds approval-gated prepared-order preview and execution-readiness inspection only. The new `prepared_order_preview_and_readiness` action hook consumes one valid current-lineage approval to run the existing child-intent preview/readiness machinery for the exact approved routed child `OrderIntent`; approval consumption records the preview key, readiness evaluation id, readiness outcome/reason codes, and no-submitted-order/no-exchange-submit/no-auto-submit truth. Approval authorizes the inspection, not eligibility or submission: blocked and phase-blocked readiness outcomes remain reason-coded, and stale-lineage, disabled, blocked, deferred, already-satisfied, dry-run-only, manual-only, wrong-action, wrong-child-intent, expired, revoked, or consumed-for-different-child cases reject before action. It does not create `SubmittedOrder`, call adapter submit, automate submitted-order handoff, recover/cancel/amend, use route executor behavior, rank/score, use CBBO, fan out, reselect targets, or auto-submit.

Phase 7.5 adds approval-gated submitted-order handoff only. The new `submitted_order_handoff` action hook consumes one valid current-lineage approval to call the existing explicit child-intent submit path for the exact approved routed child `OrderIntent`; approval does not bypass execution-readiness truth, live-submit gating, routed-submit gating, adapter/account authorization, routed lineage/order-shape checks, or the submit lease/uncertainty guards. The approval is consumed only after a `SubmittedOrder` is persisted or safely reused. If readiness or submit gates block, the approval remains unconsumed and the block stays reason-coded. If adapter-submit uncertainty occurs, the existing manual-reconciliation-required lease state remains authoritative. Phase 7.5 does not select or reselect targets, create extra child intents, fan out, rank/score, use CBBO, introduce route executor behavior, retry elsewhere, or add broad auto-submit.

Phase 7.5.1 hardens the submitted-order handoff approval truth boundary. If a `SubmittedOrder` is persisted or safely reused but approval consumption fails afterward, the approval is marked `consumption_pending`, linked to the submitted order and child intent, and stamped with `submitted_order_created_approval_consumption_pending`, `approval_consumption_failed_after_submitted_order`, and `manual_approval_reconciliation_required` provenance. A repeat call with the same approval reuses the existing submitted order and attempts to finish consumption without another adapter submit. This is not a new execution action, retry mechanism, route executor, fanout, target reselection, or broad auto-submit path.

Phase 7.6 closes the controlled automation chain with safety-diligence regression coverage and documentation alignment. It adds no new action stage or production routing behavior; instead it proves the existing Phase 7 chain remains approval-gated, same-target, current-lineage-bound, and inspectable from dry-run planning through approval creation, stage-specific action execution, `consumption_pending` inspection, and submitted-order handoff. Phase 7.6 explicitly keeps administrative approval consumption separate from action execution and proves no smart routing, best-binding selection, CBBO, ranking/scoring, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit appears.

Phase 8.0 adds operator-grade observability and manual-resolution inspection without adding a trading action. `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}` aggregates existing desired-trade, routing, automation approval, readiness, submitted-order, and submit-lease facts into a read-only operator summary. It surfaces manual-resolution requirements for `consumption_pending`, stale-lineage/expired approvals, blocked recommendations/readiness, and submit uncertainty (`adapter_submit_may_have_started` / `adapter_submit_persistence_unknown`), plus submitted-order handoff safety facts, repeat-submit policy, and next safe operator action. It creates no artifacts, consumes no approvals, resolves no manual state, calls no exchange adapter, and does not submit/cancel/amend/retry.

Phase 8.0.2 corrects that summary's active submit-lease truth. An unexpired `active` child-intent submit lease is now reported as `submission_in_progress`, makes `submission_safety.repeat_submit_blocked=true`, sets `repeat_submit_policy=blocked_while_submission_in_progress`, and changes the next safe operator action to `submission_in_progress` with `safe_to_automate=false`. Terminal submit uncertainty remains manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and the endpoint stays read-only with no artifact creation, approval consumption, manual-resolution mutation, adapter call, route executor behavior, fanout, target reselection, ranking/scoring, CBBO, or auto-submit.

SV1.0 adds a separate strategy-validation/backtesting boundary. `services/strategy_validation` reads existing persisted candle rows, computes indicator snapshots in memory, reuses current Money Flow strategy evaluation, simulates research-only trades with explicit assumptions, and returns deterministic report models plus JSON/Markdown CLI output. It is intentionally outside routing and execution: it does not create `MandateDesiredTrade`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approval records, routing artifacts, exchange adapter calls, or live automation side effects. Simulated trades are report artifacts, not exchange/account truth.

SV1.0.1 hardens that research boundary by making simulation truth more explicit. Strategy-validation assumptions now include fill timing (`same_candle_close_research_only`, `next_candle_open`, or `next_candle_close`), and reports label same-candle close fills as research-only and potentially optimistic. Metrics expose closed-trade drawdown separately from mark-to-market drawdown, with mark-to-market drawdown derived from intrabar adverse movement while simulated long positions are open. Markdown and JSON reports include expanded assumptions, limitations, component metrics/comparison, trade summary, and reason-count sections. No Money Flow strategy rules, routing behavior, execution automation, live artifacts, or exchange calls changed.

SV1.1 adds a comparative strategy-validation batch layer on top of the single-run report. `StrategyValidationBatchRequest` contains explicit Money Flow validation runs, and `StrategyValidationBatchReport` returns deterministic per-run metrics, an assumptions matrix, fill-timing comparison, component/timeframe comparison, optional symbol/date-window comparison, warnings, and limitations. The batch layer is descriptive research only: it reports observed outcomes across selected assumptions and does not optimize parameters, recommend a strategy variant, change Money Flow rules, create live trading artifacts, call exchanges, route, submit, or connect validation output to execution automation.

SV1.2 adds data-coverage and market-regime analysis to that research boundary. Validation reports now include requested-versus-available candle coverage, missing-candle/gap warnings where timeframe spacing makes them derivable, deterministic trend and volatility regime labels from candle closes, and regime-grouped performance metrics. Regime labels are descriptive only, assigned to trade metrics by entry signal candle, and never feed back into Money Flow rules, routing, paper trading, live execution, exchange adapters, or automation.

SV1.2.1 hardens the research-truth layer for windows, coverage, and batch comparisons before any SV1.3 campaign/evidence-pack work. The validation boundary now applies one candle-close interval convention everywhere: `(start_at, end_at]`. Strategy evaluation, data coverage, regime summaries, forced end-of-window close lookup, batch date-window comparison, CLI wording, JSON, and Markdown all treat the start boundary as excluded and the end boundary as included. Coverage expected counts are based on expected close slots, unaligned boundaries produce explicit warnings, coverage percent is capped at 100%, and grouped comparisons include blocked-run counts/reasons while computing metrics only from completed runs. Money Flow rules, optimization, paper/live trading, routing, execution automation, exchange calls, and live artifacts remain unchanged.

SV1.3 adds a repeatable research-campaign workflow on top of the existing Strategy Validation batch boundary. Campaign configs are explicit JSON research inputs that name the campaign, symbols/instruments, components, fill timings, named date windows, fee/slippage assumptions, capital/sizing assumptions, output directory, and report formats. The campaign runner expands those inputs into normal `StrategyValidationBatchRequest` runs, writes an evidence-pack directory with normalized config, manifest, JSON report, Markdown report, and README, and preserves the `(start_at, end_at]` candle-close window convention in config docs, manifest, and reports. This is saved research evidence only; it adds no strategy-rule changes, parameter optimization, paper/live trading, routing behavior, execution automation, live artifacts, or exchange adapter calls.

SV1.4 adds the first evidence-pack review and data-readiness baseline. Canonical editable campaign configs live under `configs/strategy_validation/campaigns/`, while the campaign CLI can run an `--audit-only` persisted-candle readiness check that reports expected/actual/missing candle counts, coverage percent, gap facts, warning reason codes, and likely blocked windows before strategy validation is interpreted. Evidence-pack manifests and Markdown reports now carry a founder/operator review checklist plus manual paper-trading readiness criteria. These are research governance artifacts only: they do not auto-approve paper trading, create paper trades, create live execution artifacts, change Money Flow rules, optimize parameters, route, submit, or call exchange adapters.

SV1.4.1 hardens evidence-pack integrity before first real SV1.5 campaign evidence generation. Campaign evidence-pack directories now use an explicit collision policy. The default `unique_suffix` policy creates a new suffixed run directory when the requested run id already exists, while `fail_if_exists` raises a clear collision error. Pack files are written once and refuse existing paths. Manifests record requested run id, final run id, final evidence-pack path, collision policy, collision occurrence, and suffix truth. This changes saved research write safety only; it does not change Money Flow rules, optimize parameters, create live artifacts, route, submit, or call exchange adapters.

SV1.5 adds historical data-readiness support for first canonical Money Flow evidence-pack runs. Campaign configs may include human-readable `window_convention` metadata, but the loader validates it against the platform convention instead of allowing users to imply a different behavior; validation remains candle closes in `(start_at, end_at]`. Campaign readiness audits can now render Markdown founder/operator summaries showing covered, thin, missing, blocked, and likely-blocked rows plus remediation notes. The new offline candle importer upserts public/CSV/JSON candle rows into the existing `candles` table for research backfills only. SV1.5.1 hardens that importer and config validator: contradictory inclusive-start window text fails, existing candles cannot be silently retargeted to a different resolved instrument/symbol identity, row duration must match the selected timeframe, non-finite or invalid OHLCV/trade-count values fail, and invalid import files roll back without partial inserts or updates. It calls no exchange adapters, private endpoints, or order endpoints, records source labels in the import summary because `CandleModel` has no per-candle provenance column, and creates no strategy decisions, desired trades, routing artifacts, approvals, child intents, readiness evaluations, submitted orders, paper trades, or live execution artifacts.

SV1.6 adds the first canonical Money Flow evidence-review layer. `services.strategy_validation.evidence_review` audits the canonical BTC and multi-symbol campaign configs, classifies campaigns as `insufficient_data`, `not_reviewed`, `ready_for_founder_review`, or manually not-justified review states, and generates evidence packs only when the existing data-readiness audit reports no missing, thin, or blocked rows. The review summary includes data gaps, evidence-pack paths, fill timing/component/regime/drawdown/cost observations, no-trade and invalid reason counts, and manual paper-readiness status. It reuses the SV1.4.1 collision-safe writer and preserves SV1.5.1 candle import integrity. It creates no live artifacts, does not call exchange adapters, does not optimize or recommend Money Flow variants, and does not approve paper trading.

SV1.7 turns that review into a first-real-run/data-gap workflow. The evidence review now records sanitized DB access status, reachability, candle-table existence, persisted candle count when available, and blocking DB/schema errors. If the configured DB is unreachable or lacks `candles`, canonical campaign rows are represented as blocked data-readiness gaps instead of throwing an uncaught connection error or creating packs. The overall status can now be `partial_evidence_ready_with_data_gaps` when at least one campaign generates a pack while another remains blocked. The local SV1.7 run found the default `postgres` host unresolved and the reachable local Postgres endpoint missing the Money Flow `candles` table, so no first real evidence packs were generated.

SV1.8 makes the DB/schema bootstrap truth explicit before first real evidence packs. The same read-only evidence-review path now reports Alembic version-table existence, applied migration revisions, repo migration heads, migration-current truth when derivable, schema status, migration command hints, DB override hints, candle-table existence, and persisted candle count. The review CLI adds `--db-status-only` for read-only DB/schema/candle checks without campaign audits or evidence-pack writes. The local SV1.8 run found the default `postgres` host still unresolved and the explicit `127.0.0.1:54322/postgres` target reachable but not migrated: no `alembic_version` table, no `candles` table, no canonical evidence packs. This remains research/data readiness only and changes no strategy, routing, execution, or live artifact behavior.

SV1.8.1 hardens that evidence-review schema gate before first real evidence-pack generation. Evidence packs now require `migrated_schema_ready`; raw `candles` table presence is not enough. The status check also verifies the required strategy-validation tables used by canonical symbol/instrument resolution (`candles`, `instruments`, and `symbols`) and blocks cleanly when Alembic truth is missing, migrations are outdated or unknown, or required schema is partial. Top-level `creates_live_artifacts` and `calls_exchange_adapters` are aggregated from campaign results rather than relying on dataclass defaults. This remains schema/report truth only and adds no strategy, routing, execution, paper trading, exchange calls, or evidence-pack generation.

SV1.9 keeps the same research-only boundary while making the practical DB/candle blocker explicit. Canonical evidence-review output now reports the configured DB target components (driver, host, port, database name, user, target role, and target warning reason codes) and emits canonical candle import requirements for blocked/missing campaign rows. The local SV1.9 run did not find an accessible migrated Money Flow database: the default `postgres` host was unresolved, the `127.0.0.1:54322/postgres` override was unreachable and flagged as an ambiguous maintenance database target, no offline candle files were available to import, and no evidence packs were generated. This is DB/schema/historical-data readiness only, not a strategy result.

SV1.9.1 makes ambiguous/non-intended maintenance DB targets generation-blocking by default and rejects timezone-naive candle imports by default unless an explicit provenance-marked exploratory override is used. SV1.10 then makes the intended local strategy-validation DB usable for imports: `money_flow` on `127.0.0.1:5432` was created locally, migrated to Alembic head `20260430_0025`, and verified to contain `candles`, `instruments`, and `symbols`. Canonical evidence review still reports `insufficient_data` because persisted candle count is zero, so no evidence packs were generated. The review now groups overlapping canonical BTC requirements across campaigns, producing 18 unique BTC/ETH/SOL candle import requirements with timezone-explicit timestamp expectations. SV1.11 adds research-only market-identity bootstrap and candle-import preflight so operators can seed/verify canonical BTC/ETH/SOL Hyperliquid perpetual USDC `instruments` / `symbols` rows before importing candles, and can validate candle files/mappings without writing candles. SV1.11.1 hardens that workflow by requiring explicit operator verification and `verified_by` provenance for non-dry-run identity writes, and by adding requirement-aware preflight that maps a candle file to a canonical requirement and checks exact `(start_at, end_at]` close-time slot coverage. SV1.11.2 keeps research identity non-trading by rejecting seed manifests that set strategy/trading eligibility true and makes requirement-aware preflight require complete one-to-one input-to-requirement mapping. SV1.12 adds a guarded canonical candle bundle import wrapper that imports only after the intended migrated DB, operator-verified non-trading identity, timezone-explicit files, one-to-one mapping, exact requirement-aware preflight, and hardened importer all pass. SV1.12.1 makes bundle-level partial persistence explicit (`explicit_partial_with_resume`) and adds per-file/per-requirement blocked output for unmapped inputs and missing requirements before the first operational import. SV1.12.2 adds a readiness/reporting layer that does not import candles: it checks whether operator-verified research identity can be seeded, emits the exact 18 canonical candle-file requirements, and can run requirement-aware preflight only when files are supplied. SV1.12.3 adds the guarded import attempt wrapper: it seeds identity only with explicit operator verification plus offline value confirmation, auto-maps files by the canonical suggested filenames, and runs guarded import only after all gates pass. The local SV1.12.3 run remained blocked because operator verification and candle files were absent. The 2026-05-05 SV1.12.4 research pass keeps January 2026 as archival/vendor-data-required and adds a public-data-friendly campaign plan with 9 local public Hyperliquid CSVs for `1h`/`4h` 2026 YTD and recent 51-day `15m`. SV1.12.5 first records supported-venue public candle readiness, then implements the operator-approved Hyperliquid public-campaign import bridge: BTC/ETH/SOL Hyperliquid identity is seeded as research-only non-trading/non-strategy-eligible identity, the 9 public files pass requirement-aware preflight, and guarded import writes `25848` candles into the intended migrated DB. SV1.12.5.1 verifies and commits the resulting repo/import state, including expected BTC/ETH/SOL symbol/timeframe counts and the no-evidence-pack boundary, before SV1.13. SV1.13 generates the first Hyperliquid public campaign evidence packs from those imported candles by expanding the public config into component-scoped evidence configs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`; generated packs remain ignored local research outputs and the committed founder report is `docs/strategy_validation_sv1_13_hyperliquid_public_evidence_review.md`. SV1.13.1 adds interpretation truth: grouped aggregate sums are labeled as research-run sums rather than one account/scenario PnL, scenario-level component/symbol/fill/cost/drawdown evidence is surfaced, and ETH `sleeve_1h` concentration is explicit for founder review. SV1.13.2 adds `dynamic_equity_pct` so a validation scenario can size each new trade from current realized equity and report ending equity; it remains per-scenario research simulation, not full margin/funding/liquidation or multi-symbol portfolio simulation. SV1.14 adds a read-only diagnostics layer for trade anatomy and market structure. It reads existing evidence reports plus persisted candles, computes descriptive recent swing high/low proximity, summarizes entry/exit/no-trade reasons, and produces hypotheses for later controlled tests without changing Money Flow rules or using market structure as a filter. SV1.15 adds a Strategy Validation-only controlled experiment layer over the dynamic-equity Hyperliquid evidence, comparing isolated overlay hypotheses against the baseline and documenting lower-RSI attribution while deferring true below-floor entry admission until rejected-signal replay data exists. SV1.15.1 hardens that layer's methodology truth: completed-trade overlays are diagnostic estimates rather than true forward replays, recent-low invalidation is a lookahead diagnostic upper bound that needs exact exit replay, and no hypothesis is authorized as a rule change. SV1.16 adds a Strategy Validation-only replay substrate that captures per-candle baseline decisions, rejected entry reasons, RSI zones, EMA/MACD state, price-extension facts, market regimes, and recent swing high/low diagnostics, then replays narrow variants chronologically with position occupancy and `dynamic_equity_pct` sizing. The first lower-RSI trend-intact ETH `sleeve_1h` true replay example underperformed the current baseline sampled scenario, so it is research substrate evidence only. Aster/Binance remain later comparative candidates, OKX/Coinbase remain blocked by public trade-count policy, and Kraken remains blocked by incomplete public REST coverage. This remains research evidence only and changes no strategy rules, routing, execution, paper trading, exchange calls, or live-artifact behavior.

## Core Hierarchy

The active hierarchy is:

- `Client`
- `VenueAccount`
- `StrategyMandate`
- `MandateAccountBinding`
- `StrategyComponentConfig`

What that means:

- one client can own many venue accounts
- one client can own many mandates
- one venue account can participate in many mandates
- bindings are the future account-group / routing surface
- components are the generic family-specific internal configuration model

`VenueAccount` remains exchange/account truth.
Balances, positions, orders, fills, snapshots, and venue-private state stay venue-account scoped.
Strategy attribution remains a separate overlay concern.

## Load-Bearing Execution Boundary

The current execution boundary is:

- `StrategyDecision`
- `MandateDesiredTrade`
- `OrderIntent`
- `PreparedVenueOrder`
- `ExecutionReadinessAssessment`
- `SubmittedOrder`

Below `SubmittedOrder`, the platform now supports bounded post-submit lifecycle work:

- reconciliation
- cancel
- selective amend
- recovery recommendation
- same-target recovery execution
- polling-based private order/account-state inspection

This boundary must not collapse back into direct strategy-to-order behavior.

Above and at the child-intent boundary, Phases 5.0 through 5.2 add a controlled routing substrate:

- `RoutingRequest`
- `RoutingAssessment`
- `RoutingCandidateAssessment`
- `RouteReadinessAudit`
- `RoutingTargetRecommendation`
- `RoutingTargetChoice`

Routing assessment and target choice are assessment/audit surfaces only. They enumerate candidate bindings, eligibility/ineligibility facts, missing data, and operator-requested single-binding target-choice records for routing-required mandate-scoped opens. Phase 5.2 can convert one explicit valid target choice into exactly one binding/account-targeted `OrderIntent`. Phase 5.8 makes that conversion call a bounded routed order-shape policy helper that accepts optional explicit MARKET/LIMIT input and records the selected or blocked shape decision in provenance. Phase 5.3 lets that converted child intent enter existing prepared-order preview/readiness inspection only after route-lineage revalidation, and Phase 5.3.1 tightens that validation against mutable provenance / intent / target-choice drift. Phase 5.4 can submit that same selected child intent only through an explicit submit action when both submission gates pass. It does not create splits, ranked venue lists, price-quality comparisons, target reselection, fanout, or smart routing.

`RouteReadinessAudit` is distinct from `RoutingAssessment`: assessments enumerate candidates, while route-readiness audits evaluate data sufficiency for recommendation. They expose global and per-candidate missing, stale, unsupported, unavailable, policy-blocked, and blocking facts with data-source labels. They are non-selecting, non-ranking, non-scoring, and non-executing; they do not create target choices, child intents, prepared orders, readiness evaluations, submitted orders, route plans, allocations, or recommendations.

`RoutingTargetRecommendation` is distinct from `RoutingTargetChoice`: recommendations are persisted system-generated audit records from a route-readiness audit, while target choices remain explicit operator-requested audit records. `single_ready_candidate_only` remains the default, so multiple ready candidates still block unless the caller explicitly requests `explicit_binding_priority`. The API accepts only those two recommendation policy names, while direct service policy input is bounded before persistence. The priority policy uses only operator-configured binding priority; lower positive integers win, missing or malformed priority data blocks, ties block, omitted priority updates preserve existing priority, and `clear_target_recommendation_priority=true` intentionally clears it. Phase 6.0.1/6.0.2 current-truth revalidation still applies before success. Phase 6.2 lets an operator explicitly accept a successful recommendation into one `RoutingTargetChoice`; Phase 6.2.1 makes acceptance idempotent across successful recommendations from the same route-readiness audit. Repeated or duplicate successful same-audit acceptance returns the original target choice, marks the later successful recommendation as `target_choice_created`, and preserves original acceptance timestamp truth in recommendation/audit provenance while recording later checks separately. Phase 6.2.2 ensures blocked recommendations cannot use that same-audit idempotency path; they remain blocked, retain `target_choice_created=false`, and do not receive accepted-looking provenance. Phase 6.3 lets an operator explicitly convert an accepted recommendation-backed target choice through the same target-choice-to-child-intent machinery used by Phase 5.2. Phase 6.4 lets that recommendation-backed child intent use the existing prepared-order preview and submission-readiness endpoints with recommendation/audit/candidate quote/current-truth revalidation and top-level routed-lineage response fields. Phase 6.4.1 keeps that path honest by comparing stored routed order-shape policy facts against the current child intent shape before adapter preview/readiness can proceed. Phase 6.7 allows that same child intent to submit only through the existing explicit gated child-intent submit action, after readiness and routed/live gates pass. A recommendation does not automatically create a target choice, child intent, readiness evaluation, submitted order, route plan, allocation, fanout, or submit instruction.

## Service Boundaries

- `services.exchange.hyperliquid`: perpetual adapter with truthful submit, deeper reconciliation, cancel acknowledgement, and native limit-order amend for the current proven scope
- `services.exchange.aster`: perpetual adapter with truthful submit, reconcile, cancel, and strict client-order-id retry truth; native amend remains unsupported
- `services.exchange.okx`: spot and perpetual/swap adapter with truthful submit, reconcile, cancel lifecycle, and native amend for the current scoped limit-order path
- `services.exchange.coinbase`: Coinbase Advanced Trade spot adapter with truthful JWT submit, reconcile, cancel lifecycle, and native amend for the current spot limit-order path
- `services.exchange.binance`: spot adapter with truthful submit, reconcile, cancel, and strict client-order-id retry truth; native amend remains unsupported
- `services.exchange.kraken`: spot adapter with truthful submit, reconcile, cancel lifecycle, and native amend for the current spot limit-order scope
- `services.exchange.registry`: venue registry and capability inspection surface
- `services.market_data`: candle ingestion, checkpointing, and freshness handling
- `services.indicators`: deterministic indicator computation and snapshot persistence
- `services.strategy`: family-level evaluation and component-level orchestration
- `services.planning`: mandate-level desired-trade drafting, source-policy inspection, convertibility checks, routing-candidate inspection, and quote normalization ahead of routing assessment and target-choice audit
- `services.risk`: first-pass desired-trade approval and rejection
- `services.routing`: routing assessment, route-readiness/data-sufficiency audit, controlled single-ready-candidate recommendation, target-choice audit, and explicit one-child-intent conversion substrate over routing-required mandate-scoped opens
- `services.routing`: also exposes Phase 7.0 non-executing automation policy and dry-run automation-plan inspection over the already accepted single-target recommendation-backed workflow
- `services.routing`: also owns Phase 7.1 durable automation approval records, revocation, consumption, and approval-state inspection without executing the approved action; Phase 7.1.1 scopes active approval reuse to the current workflow lineage fingerprint and marks expired or stale-lineage approvals non-current before gate inspection; Phase 7.1.2 allows approvals only for truly approvable current steps and reports manual-only / dry-run-only gate truth ahead of stored approval metadata; Phase 7.2 consumes one valid recommendation-acceptance approval to create or reuse one target choice through the existing acceptance path and stops there; Phase 7.2.1 makes that target-choice creation/reuse plus approval consumption one coherent transaction; Phase 7.3 consumes one valid target-choice-conversion approval to create or reuse one child intent through the existing conversion validation/persistence helpers; Phase 7.4 consumes one valid preview/readiness approval to run existing child-intent preview/readiness inspection; Phase 7.5 consumes one valid submitted-order-handoff approval to call the existing explicit child-intent submit path for that same child intent while preserving readiness, submit-gate, and submit-lease authority; Phase 7.5.1 records `consumption_pending` approval truth if submitted-order persistence succeeds but approval consumption fails afterward; Phase 7.6 adds closeout regression coverage proving those boundaries remain true without adding production behavior.
- `services.routing`: also exposes Phase 8.0 read-only operator workflow summaries that combine existing routed workflow aggregation, approval/gate state, manual-resolution requirements, submitted-order safety, and submit-lease/concurrency facts without creating or mutating trading artifacts. Phase 8.0.2 makes active unexpired submit leases block repeat-submit safety and next-safe-action truth as `submission_in_progress` while preserving terminal uncertainty and stale pre-adapter lease semantics.
- `services.strategy_validation`: Money Flow research/backtest boundary. SV1.0/SV1.0.1 provide single-run reports with explicit fill timing and drawdown truth; SV1.1 adds descriptive batch comparison; SV1.2/SV1.2.1 add data-coverage, regime, and window-truth diagnostics; SV1.3 adds repeatable campaign evidence packs; SV1.4 adds canonical campaign configs, pre-run persisted-candle readiness audit, evidence-pack review checklist, and manual paper-trading readiness criteria; SV1.4.1 makes evidence-pack writes collision-safe with explicit `unique_suffix` / `fail_if_exists` policy truth in manifests; SV1.5 validates campaign window-convention metadata, adds Markdown data-readiness summaries, and adds offline public candle import/upsert helpers for research data gaps; SV1.5.1 hardens import identity, timeframe-duration, OHLCV, and all-or-nothing import truth; SV1.6 adds canonical evidence-review summaries and manual paper-readiness status without approving paper trading; SV1.7 adds DB reachability/candle-table data-gap truth and partial-evidence status; SV1.8 adds DB/schema/migration bootstrap status and a status-only CLI path before evidence generation; SV1.8.1 gates evidence-pack generation on migrated/current schema truth and required `candles` / `instruments` / `symbols` table presence; SV1.9 adds explicit DB target role/host/port/name reporting and canonical candle import requirements while preserving the no-pack-on-unready-schema gate; SV1.9.1 blocks ambiguous or non-intended maintenance DB targets from evidence generation by default, rejects timezone-naive candle imports by default, and records stronger import source/timestamp provenance in summary output; SV1.10 records intended local DB readiness and groups canonical missing candle requirements into unique actionable rows; SV1.11 adds research-only market identity seed/verify helpers, candle-import preflight, and evidence-review canonical identity readiness; SV1.11.1 requires operator-verified identity writes and adds requirement-aware candle preflight coverage proof; SV1.11.2 blocks strategy/trading eligibility promotion through the research seed and requires complete one-to-one preflight mapping; SV1.12 adds guarded canonical candle bundle import that composes DB/schema, operator-verified non-trading identity, preflight, and importer truth before writing candles; SV1.12.1 makes partial bundle persistence explicit and exposes unmapped inputs/missing requirements directly in import output; SV1.12.2 adds import-readiness reporting and the 18-file canonical checklist before actual guarded import; SV1.12.3 adds an operational guarded import attempt wrapper that can seed only explicitly verified research identity and can import only a complete preflight-passed canonical bundle; SV1.12.4 adds a public-data-friendly campaign config/report for 9 public Hyperliquid YTD/recent files while keeping January as archival/vendor-data-required; SV1.12.5 adds the 9-file public campaign import wrapper, supported-venue inventory, and an operator-approved Hyperliquid import run that writes `25848` research candles; SV1.12.5.1 verifies the resulting import/repo state before evidence generation; SV1.13 expands the public campaign into component-scoped evidence configs and generates Hyperliquid-only evidence packs for founder review; SV1.13.1 clarifies grouped aggregate semantics and founder interpretation without changing evidence numbers; SV1.13.2 adds `dynamic_equity_pct` sequential capital sizing, equity-account metrics, and a founder dynamic-equity report while preserving constant-notional replay as the default; SV1.14 adds `trade_anatomy` diagnostics and CLI reporting for entry/exit/no-trade reasons plus descriptive market-structure context while preserving strategy rules; SV1.15 adds `hypothesis_experiments` and CLI reporting for research-only isolated overlays and attribution against the dynamic-equity baseline while preserving production Money Flow rules; SV1.16 adds research-only rejected-signal true replay instrumentation; SV1.16.1 hardens replay semantics by distinguishing production-rule evaluations in replay state from independent baseline truth and by separating production-rule rejection, variant-admitted-from-rejection, and variant no-trade counters; SV1.17 adds a first ETH `sleeve_1h` true replay experiment round for lower-RSI plus market-structure variants. It creates no live trading artifacts and does not call exchange adapters.
- SV1.17 full-suite expansion runs those lower-RSI plus market-structure replay variants across BTC/ETH/SOL and `sleeve_15m`/`sleeve_1h`/`sleeve_4h`; each scenario remains independent and is compared only to its same-symbol/same-component baseline.
- `services.portfolio`: venue/account truth loaders and portfolio summaries
- `services.execution`: child-intent preparation, routed child-intent route-lineage validation before preview/readiness/submission, prepared-order preview/preflight, readiness gating, explicit non-routed submission, explicit gated routed submission for already selected child intents, submitted-order lifecycle, routed post-submit lifecycle/actionability/reconciliation-event context derivation through the shared domain parser, reconciliation, cancel, selective amend, recovery recommendation, and bounded same-target recovery execution
- `apps.api`: operator-facing inspection and control plane, including adapter/runtime session-state and private order/account-state visibility below routing
- `apps.api`: also exposes routing assessment, target-choice creation/inspection, explicit target-choice conversion endpoints, existing child-intent preview/readiness endpoints for converted routed child-intent inspection, and the narrow Phase 7.2/7.3/7.4/7.5 approval-consuming action endpoints for recommendation acceptance, target-choice conversion, preview/readiness inspection, and submitted-order handoff.
- `apps.dashboard`: static local founder/operator review surface for Strategy Validation evidence packs, Strategy Validation experiment/replay summaries, and UAT2 shadow observation summaries. It loads ignored local evidence-review JSON and component batch reports from `reports/strategy_validation*`, committed replay/summary JSON under `docs/`, or accepts manual JSON file selection in the browser. UAT2.1 adds a UAT2 Shadow Run tab for read-only visualization of `docs/uat2_shadow_strategy_top20_observation_summary.json`; UAT3.0 adds an informational sandbox-order design/readiness panel to that view; UAT3.0.1 updates it with fixture/readiness validator status; UAT3.0.2 adds unified dry-run preflight, full runtime blocker propagation, numeric edge-case validation, and artifact-label persistence blocker status; UAT3.0.3 updates it with boundary-label enforcement and dry-run executable gate wiring status; UAT3.0.4, UAT3.0.5, and UAT3.0.6 do not change dashboard behavior. The dashboard creates no evidence packs, imports, approvals, exchange calls, routing/execution artifacts, order intents, submitted orders, or strategy-rule changes.

## Canonical Identity And Planning Rules

The platform keeps canonical instrument identity separate from venue-native symbol identity:

- `instrument_key` is the canonical business identity
- `instrument_ref_id` is the persistence row identity
- venue symbol mappings remain venue/product specific

This matters because the current venue set mixes:

- Hyperliquid perpetuals
- Aster perpetuals
- OKX spot plus perpetual/swap
- Coinbase Advanced Trade spot
- Binance spot
- Kraken spot

The planning/source venue is also distinct from future routing venues.
`MandateMarketDataSourcePolicy` defines where the mandate currently gets planning truth.
That does not imply later execution venue or binding choice.

## Current Venue Matrix

Current integrated venues:

- Hyperliquid
- Aster
- OKX
- Coinbase Advanced Trade
- Binance
- Kraken

Current truthful scope at head:

- all six are on the execution-preparable branch
- all six have code/test-proven account-targeted submit paths for their currently implemented scopes
- all six have meaningful post-submit reconciliation depth, but lifecycle parity is still uneven
- cancel depth is broader than amend depth
- amend is currently native only where code/test-proven in the implemented account/product path
- public capability surfaces now report cancel and amend separately instead of using one misleading combined capability flag
- private order/account-state depth is now explicit and polling-first rather than implied through one fake maturity flag

Current amend truth:

- Hyperliquid: native amend for the current perpetual limit-order scope
- OKX: native amend for the current scoped limit-order path
- Coinbase Advanced Trade: native amend for the current spot limit-order scope
- Kraken: native amend for the current spot limit-order scope
- Aster: amend unsupported
- Binance: amend unsupported

Current retry truth:

- retry remains same-target, same-account, same-venue only
- Binance and Aster use fresh retry client order ids because their venue semantics make naive reuse unsafe
- retry is still blocked when duplicate exposure risk cannot be ruled out
- Aster and Binance private trade checks use submitted-at-bounded `startTime` queries and block retry conservatively on same-account/same-symbol ambiguity when the submitted order has no exchange order id; this is not represented as targeted order fill proof
- stale same-account/same-symbol private fills before `SubmittedOrder.submitted_at` do not block retry on those time-bounded paths, while exact exchange-order-id matches remain `order_scoped`
- ambiguous Aster/Binance retry evidence stays inside the scoped `SubmittedOrderPrivateFillEvidence` envelope and is not exposed as plain submitted-order fill truth
- if a direct private fill evidence query fails during retry safety checks, retry blocks with an explicit unavailable-evidence lifecycle event instead of proceeding optimistically

## Current Routing Substrate

Phase 5.0 introduced routing assessment. Phase 5.1 adds operator-requested target-choice audit records. Phase 5.2 adds explicit target-choice-to-child-intent conversion without preparation, readiness assessment, submission, fanout, scoring, or target reselection. Phase 5.2.1 hardens conversion lineage checks without adding new routing behavior. Phase 5.3 lets converted routed child intents use existing prepared-order preview and readiness inspection after route-lineage revalidation. Phase 5.3.1 tightens that routed readiness validation. Phase 5.4 adds a controlled explicit routed submission handoff for the already selected child intent, gated separately from normal live submission. Phase 5.5 exposes routed submitted-order lineage, Phase 5.6 makes routed conversion order shape explicit through a policy-backed current default, Phase 5.7 exposes routed post-submit lifecycle/actionability context while keeping recovery same-target only, Phase 5.7.1 preserves routed lineage through same-target retry without adding target reselection, Phase 5.8 expands routed order-shape policy to optional explicit MARKET/LIMIT input without routing behavior, Phase 5.8.1 hardens non-finite LIMIT price validation without adding routing scope, Phase 5.8.2 cleans the blocked-policy reason surface so malformed/non-finite prices are not labeled as accepted explicit prices, Phase 5.9 deepens routed reconciliation/lifecycle audit visibility without changing reconciliation or recovery semantics, Phase 5.9.1 makes current platform routed lineage authoritative over colliding reconciliation/update payloads, Phase 5.9.2 prevents update payloads from fabricating platform routed lineage on non-routed submitted orders, Phase 5.10 closes the routed lifecycle substrate with end-to-end regression coverage, Phase 5.10.1 adds route-readiness/data-sufficiency audit as a non-selecting gate before recommendation, Phase 5.10.2 fixes route-readiness audit source/shape/quote-price truth, Phase 6.0.0 adds controlled non-executing target recommendation only when one route-readiness audit has exactly one ready candidate, Phase 6.0.1 hardens recommendation success against stale mandate and symbol truth after the audit, Phase 6.0.2 rechecks stored quote observation freshness at recommendation time while updating source-audit recommendation-created truth, Phase 6.1 adds optional deterministic binding-priority recommendation, Phase 6.2 accepts successful recommendations into target choices, Phase 6.3 converts accepted recommendation-backed target choices into exactly one child intent, Phase 6.4 lets that child intent use existing preview/readiness inspection with recommendation-aware lineage and current-truth validation, Phase 7.2 consumes approval for recommendation acceptance only, Phase 7.3 consumes approval for target-choice conversion only, Phase 7.4 consumes approval for preview/readiness inspection only, Phase 7.5 consumes approval for submitted-order handoff only through the existing explicit submit path, Phase 7.6 closes the controlled automation proof with regression coverage instead of adding another action stage, and Phase 8.0 adds read-only operator workflow/manual-resolution summary inspection before any future SOR work.

Allowed current output:

- routing request facts for one existing `routing_required` mandate desired trade
- evaluated `MandateAccountBinding` candidate inventory
- binary per-binding status:
  - `eligible_for_future_selection`
  - `ineligible_for_future_selection`
- route-readiness/data-sufficiency audit status:
  - `ready_for_recommendation`
  - `blocked`
  - `insufficient_data`
  - `stale_data`
  - `policy_blocked`
  - `unsupported`
- routing target recommendation status:
  - `recommended_single_ready_candidate`
  - `blocked_audit_not_found`
  - `blocked_audit_not_ready`
  - `blocked_no_ready_candidate`
  - `blocked_multiple_ready_candidates`
  - `blocked_stale_audit`
  - `blocked_stale_desired_trade`
  - `blocked_stale_candidate`
  - `blocked_invalid_audit`
- explicit reason codes
- explicit missing-data facts
- explicit stale, unsupported, unavailable, policy-blocked, and blocking facts
- explicit data-source labels such as `persistence`, `venue_query`, `adapter_capability`, `static_config`, `derived_from_existing_assessment`, and `unavailable`; current route-readiness audits derived from routing-assessment snapshots label quote facts as `derived_from_existing_assessment` rather than pretending a fresh venue query occurred
- persisted audit trail in `routing_assessments` and `routing_assessment_candidates`
- persisted audit trail in `route_readiness_audits` and `route_readiness_candidate_audits`
- persisted audit trail in `routing_target_recommendations`
- routed lineage on recommendation-backed prepared-order preview and execution-readiness responses

Allowed current assessment status:

- `assessment_only`
- `no_eligible_bindings`
- `insufficient_data`

Current routing assessment uses only truth the platform already has:

- desired-trade identity and status
- mandate and source-policy context
- binding enablement and routing eligibility
- venue-account active/trading flags
- symbol mapping availability
- venue and adapter submission capability truth
- account identifier / connectivity facts
- quote availability as missing-data truth, not as ranking input

Current routing assessment does not:

- rank venues
- produce allocation weights
- compare execution quality
- create `OrderIntent` records
- prepare venue orders
- submit
- split one desired trade across bindings
- perform cross-venue or cross-binding retry

Current route-readiness audit can:

- start from a routing-required desired trade or an existing routing assessment
- create candidate enumeration from the desired trade only as assessment input
- re-check current desired-trade side, desired quantity, mandate, binding, venue-account, symbol, capability, quote, economic, private-state, and order-shape facts
- block recommendation-readiness when desired-trade side is missing, quantity is missing/zero/negative, or persisted quote prices are malformed, non-finite, zero, or negative
- expose per-candidate missing, stale, unsupported, unavailable, policy-blocked, and blocking facts
- expose data-source labels so persistence-backed, adapter-capability, venue-query, static-config, and unavailable truth are not conflated
- report `ready_for_recommendation` only as data sufficiency for a future recommendation phase

Current route-readiness audit does not:

- recommend a target
- choose or rank a binding
- score venue quality
- compare prices or use CBBO
- create `RoutingTargetChoice`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, or `SubmittedOrder`
- submit, fan out, split, or execute

Current routing target recommendation can:

- start only from an existing `RouteReadinessAudit`
- require the audit to be fresh under the current quote-freshness threshold
- require the recommended candidate's stored `quote_observed_at` to still be fresh at recommendation creation time
- require exactly one candidate with `ready_for_recommendation`
- re-check current desired-trade status, target scope, action, side, and positive finite quantity
- re-check current mandate existence and enablement
- re-check current desired-trade symbol / symbol-id / instrument identity against the audit
- re-check current binding enabled/trading/routing eligibility and venue-account active/trading truth
- re-check current venue symbol mapping existence, active flag, trading eligibility, platform symbol, exchange symbol, venue, and instrument truth
- persist a non-executing recommendation for the one ready candidate under `single_ready_candidate_only`
- persist a non-executing recommendation for an explicitly requested `explicit_binding_priority` result only when exactly one ready candidate has the winning lower positive binding priority and all current-truth checks still pass
- persist blocked recommendation records for zero ready candidates, default-policy multiple ready candidates, missing/malformed/tied binding priority, stale/not-ready/invalid audits, stale desired-trade truth, and stale candidate truth
- reject oversized or whitespace policy names before recommendation persistence
- preserve existing binding priority when an update omits `target_recommendation_priority`, and clear it only through `clear_target_recommendation_priority=true`
- mark the source route-readiness audit `recommendation_created=true` after any recommendation record is persisted from it
- be explicitly accepted into exactly one non-executing `RoutingTargetChoice` only after current truth and stored quote freshness are revalidated again

Current routing target recommendation does not:

- recommend among multiple ready candidates unless `explicit_binding_priority` is explicitly requested and one operator-priority winner exists
- choose among bindings, venues, or price outcomes by price, fee, spread, liquidity, venue quality, rank, score, or CBBO
- rank, score, compare prices, or use CBBO
- automatically create `RoutingTargetChoice`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, or `SubmittedOrder`
- submit, fan out, split, allocate, reselect targets, or execute

Current target choice can:

- reference one persisted routing assessment
- record one explicitly requested candidate binding from that assessment
- record one explicitly accepted successful routing target recommendation, with source recommendation, route-readiness audit, policy, selected binding/account/venue/symbol, and accepted-at lineage in provenance
- validate that the assessment is still `assessment_only`
- validate that the candidate is still `eligible_for_future_selection`
- validate that candidate missing-data facts are empty
- re-check that the source desired trade still exists, is still `routing_required`, is still mandate-scoped/open, and is not already binding/account targeted
- re-check that the binding and venue account still exist and are enabled / active / trading eligible
- persist recorded and blocked outcomes as audit facts in `routing_target_choices`

Current target choice status:

- `target_choice_recorded`
- `blocked_no_eligible_binding`
- `blocked_candidate_ineligible`
- `blocked_assessment_insufficient_data`
- `blocked_assessment_not_found`
- `blocked_candidate_not_found`
- `blocked_stale_assessment`

Current target choice does not:

- auto-pick a candidate
- automatically accept a recommendation
- mutate `MandateDesiredTrade.status`; the desired trade remains `routing_required`
- create `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, or `SubmittedOrder`
- submit
- split one desired trade across bindings
- compare venue prices or quality
- perform cross-venue or cross-binding recovery

Current target-choice conversion can:

- consume one explicit `target_choice_id`
- revalidate current target-choice, assessment, candidate, desired-trade, binding, venue-account, and symbol-mapping truth
- block when routing assessment id/ref/environment lineage, desired-trade client/mandate/source identity, or selected binding mandate ownership has drifted
- create exactly one binding/account-targeted `OrderIntent`
- preserve routing assessment / target-choice / selected binding-account lineage in child-intent provenance
- mark the source desired trade `routed`, meaning one child intent was created from the recorded target choice, not that anything was submitted
- return the existing child intent on repeated conversion of the same target choice

Current target-choice conversion does not:

- infer or auto-pick a target choice
- create `PreparedVenueOrder`, `ExecutionReadinessAssessment`, or `SubmittedOrder`
- submit
- fan out or split across bindings
- rank venues
- score venue quality or price
- use CBBO
- replace a target choice with a different binding

Current routed preparation/readiness can:

- inspect a converted routed `OrderIntent` through the existing child-intent prepared-order preview path
- inspect routed child-intent readiness through the existing readiness evaluation path
- revalidate `OrderIntent` provenance, source desired trade, routing assessment, target choice, selected candidate, current binding, current venue account, and symbol mapping before preview/readiness
- block selected-target provenance drift, child-intent client/mandate drift, target-choice desired-trade linkage drift, and explicit routed submit attempts before adapter submission
- return blocked preview/readiness facts with explicit reason codes when desired-trade status, route lineage, binding/account state, or symbol mapping has drifted
- preserve routing assessment / target-choice lineage in preview payload and readiness provenance
- keep routed preview non-submitting and explicit-submit-only while reporting actual routed/live gate state; `submission_deferred` is true only when one or both phase gates still block explicit routed submission
- phase-block valid routed readiness with `routed_submission_deferred` while `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED=false`, or `phase_live_submit_deferred` while the normal live-submit gate remains disabled
- return eligible routed readiness when route-lineage validation, normal readiness checks, `EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED`, and `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED` all pass

Current explicit routed submission can:

- start only from an already converted routed child intent and an explicit submit call
- re-run route-lineage validation and existing readiness immediately before adapter submission
- acquire a narrow persistence-backed child-intent submit lease after readiness/live/routed gates pass and before adapter `submit_order()` is called
- block a concurrent explicit submit for the same child intent before a second adapter call; before adapter-in-flight marking it blocks as `submission_in_progress`, after adapter-in-flight marking it blocks with `submission_state_uncertain`, or returns existing submitted-order truth when a `SubmittedOrder` already exists
- mark a lease `adapter_submit_may_have_started` with `manual_reconciliation_required` before calling `adapter.submit_order()`; this terminal state blocks future submit attempts for the intent before adapter submission and is not TTL-replaceable
- mark a lease `adapter_submit_persistence_unknown` with `manual_reconciliation_required` if adapter submit returned but local `SubmittedOrder` persistence failed; this terminal state blocks future submit attempts for the intent before adapter submission and is not TTL-replaceable
- submit only the selected binding/account/venue/instrument already stored on the child intent
- create exactly one `SubmittedOrder` through the existing venue submit path when all gates pass
- preserve desired-trade, routing assessment, route-readiness audit, routing target recommendation, target-choice, child-intent, selected binding/account, selected venue, selected exchange symbol, recommendation policy, routed order-shape policy, and readiness evaluation lineage in submitted-order raw payload
- expose that routed submitted-order lineage as read-only API audit fields derived from the submitted-order raw payload, without making route lineage a primary submitted-order identity or execution instruction
- bound missing, partial, or wrong-typed routed payloads with explicit missing/malformed-lineage facts instead of breaking submitted-order list/detail inspection
- expose read-only routed lifecycle context on submitted-order detail/list, recovery recommendation, recovery execution response, and actionability responses; this context repeats selected binding/account/venue/exchange-symbol and routed order-shape policy facts only as audit metadata
- preserve existing platform-owned `routed_submission` audit payload through reconciliation/lifecycle updates, strip colliding update-payload `routed_submission` keys from submitted-order raw payloads, keep non-routed submitted orders from becoming routed-origin through update payloads, and expose read-only routed lifecycle context on submitted-order lifecycle-event responses
- preserve that routed lifecycle context on a same-target retry result when the original/retry intent and readiness carry routed lineage
- preserve recommendation/source-audit first submitted-order provenance permanently while separately exposing latest/retry submitted-order ids after same-target retry
- keep routed recovery/actionability same-target, same-account, and same-venue only; routed lineage never authorizes target reselection, alternate binding recovery, alternate venue recovery, fanout, or route execution behavior
- keep routed target-choice conversion order shape in child-intent provenance as the current defaulted `MARKET`, no limit price, and `reduce_only=false`; explicit wording is reserved for actual explicit order-shape policy input
- record routed phase-boundary submit attempts, including routed-gate and normal live-gate deferrals, as `last_submission_block` without marking the child intent as `submission_failed`

Current routed preparation/readiness/submission does not:

- create additional child intents
- fan out or split across bindings
- rank or score venues
- use CBBO
- reselect or repair stale routing targets
- infer LIMIT, price, or venue quality from market data; explicit LIMIT requires a positive finite requested limit price and modeled order-type support
- implement slippage guard semantics or market-data-derived routed limit-price sources
- create a route executor or route plan
- auto-submit
- submit when the routed submission gate is disabled
- use routed lifecycle context to choose a different target, widen account scope, or recover across bindings/venues
- treat `order_intent_submission_leases` as submitted-order reservations or exchange/account truth
- silently clear `adapter_submit_may_have_started` or `adapter_submit_persistence_unknown` leases by TTL; operator reconciliation/manual cleanup is required because the venue may already have accepted the first order

Phase 5 is closed as routing substrate plus data-sufficiency audit only. Phase 6 is closed as controlled explicit single-target recommendation-backed routed execution. Phase 6.0.x adds controlled single-target recommendation deliberately above this substrate and requires the Phase 5.10.1 / 5.10.2 route-readiness audit to prove data sufficiency first; Phase 6.1 adds one optional deterministic operator-priority policy for multiple ready candidates; Phase 6.1.1 tightens input/clearing truth around that policy; Phase 6.2 adds explicit recommendation acceptance into target choice only; Phase 6.2.1 prevents one route-readiness audit from producing multiple accepted target choices while preserving original acceptance timestamps; Phase 6.2.2 prevents blocked recommendations from being marked accepted through same-audit idempotency; Phase 6.3 adds explicit accepted recommendation target-choice conversion into exactly one child intent; Phase 6.4 lets that child intent use existing preview/readiness inspection without submission; Phase 6.4.1 blocks readiness on routed order-shape policy/current-intent drift plus readiness-time stale quote truth; Phase 6.5/6.6 add manual JSON tooling and local timing for exercising the explicit path; Phase 6.7-6.10 complete explicit submitted-order handoff, post-submit lineage inspection, read-only workflow aggregation, and closeout regression; and Phase 6.10.1-6.10.3 harden explicit submit leases across concurrent submit, post-adapter persistence uncertainty, and adapter-in-flight uncertainty. Phase 7.0-7.6 is closed as controlled automation around that same single-target path: policy/dry-run planning, durable approvals, approval-gated recommendation acceptance, target-choice conversion, preview/readiness, submitted-order handoff, `consumption_pending` truth, and closeout safety assertions. Recommendation acceptance, target-choice conversion, preview/readiness, submitted-order handoff, and the manual harness are still not best-binding selection, venue ranking, price ranking, CBBO, fanout, route execution orchestration, target reselection, or broad automatic submission.

Operator endpoints:

- `POST /api/v1/routing-assessments/from-desired-trade`
- `GET /api/v1/routing-assessments/{assessment_id}`
- `POST /api/v1/route-readiness-audits/from-desired-trade`
- `POST /api/v1/route-readiness-audits/from-assessment`
- `GET /api/v1/route-readiness-audits/{route_readiness_audit_id}`
- `POST /api/v1/routing-target-recommendations/from-route-readiness-audit`
- `GET /api/v1/routing-target-recommendations/{routing_target_recommendation_id}`
- `POST /api/v1/routing-target-recommendations/{routing_target_recommendation_id}/accept`
- `POST /api/v1/routing-target-choices/from-assessment`
- `GET /api/v1/routing-target-choices/{target_choice_id}`
- `POST /api/v1/routing-target-choices/{target_choice_id}/convert-to-child-intent`
- `GET /api/v1/routing-assessments/{assessment_id}/target-choices`
- `GET /api/v1/child-intents/{intent_id}/prepared-order-preview`
- `GET /api/v1/child-intents/{intent_id}/submission-readiness`
- `POST /api/v1/child-intents/{intent_id}/submit` for explicit non-routed submission and Phase 5.4 gated explicit routed submission
- `GET /api/v1/submitted-orders/{submitted_order_id}/actionability` and `/recovery` expose Phase 5.7 routed lifecycle context where the submitted order has routed-origin audit payload
- `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}` aggregates existing routed workflow records read-only for operator inspection
- `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}` aggregates existing routed workflow, approval, manual-resolution, submitted-order safety, and submit-lease state read-only for operator inspection
- `GET /api/v1/routing-automation/policy`, `POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}`, and the routing-automation approval endpoints inspect/create/revoke/consume approval gates
- `POST /api/v1/routing-automation/approvals/{approval_id}/consume` is an administrative approval-state transition only; it does not execute the approved action
- `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation` consumes a valid recommendation-acceptance approval and creates or reuses only the target choice in one coherent action
- `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice` consumes a valid target-choice-conversion approval and creates or reuses only the child `OrderIntent` in one coherent action

The routed workflow response exposes static same-target route facts as `same_target_lifecycle_summary`. It intentionally does not expose `actionability_summary` or `recovery_summary` unless a future implementation returns real actionability/recovery evaluations from the corresponding execution services.

Manual developer/operator harness:

- `.venv/bin/python scripts/manual_routed_flow.py --desired-trade-key <desired_trade_key>` inspects a desired trade and skips submission by default
- `.venv/bin/python scripts/manual_routed_flow.py --desired-trade-key <desired_trade_key> --run-through-readiness` explicitly calls the existing assessment, audit, recommendation, acceptance, conversion, preview, and readiness service paths and emits JSON trace output
- `--submit` is blocked locally unless paired with `--i-understand-this-can-place-a-live-order`; confirmed submission still uses the existing readiness/live/routed/adapter gates and does not bypass service-layer checks

## Current Private-State And Session Truth

Current head stays explicit about the difference between venue semantics and adapter implementation:

- `supports_user_streams` can be true semantically for a venue without claiming adapter-level stream parity
- `adapter_supports_user_streams` remains false for the current six adapters
- `private_lifecycle_update_mode` is `polling` across the current venue set

Current per-venue private-state truth:

- venue-private open-order views are distinct from platform `SubmittedOrder` records
- optional linkage back to persisted `SubmittedOrder` or `OrderIntent` is correlation-only
- `open_orders_source` and `recent_fills_source` now report the runtime path actually used for the summary call, not just static adapter capability

- Hyperliquid:
  - adapter/runtime session-state inspection exists
  - account snapshot remains persistence-backed
  - open-order visibility uses direct venue query
  - recent-fill visibility uses direct venue query
  - open-position visibility uses direct venue query when an account address is available
  - direct open-position `mark_price` uses `markPx` when present, derives from `positionValue / abs(szi)` when possible, and remains `None` when no truthful mark price exists
- Aster:
  - adapter/runtime session-state inspection exists
  - open-order visibility now uses direct venue query
  - recent-fill summary remains persistence-backed
  - same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks
- OKX:
  - adapter/runtime session-state inspection exists
  - open-order visibility uses direct venue query
  - recent-fill visibility uses direct venue query
- Coinbase Advanced Trade:
  - adapter/runtime session-state inspection exists
  - open-order visibility uses direct venue query
  - recent-fill visibility uses direct venue query
- Binance:
  - adapter/runtime session-state inspection exists
  - open-order visibility uses direct venue query
  - recent-fill summary remains persistence-backed
  - same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks
- Kraken:
  - adapter/runtime session-state inspection exists
  - open-order visibility uses direct venue query
  - recent-fill visibility uses direct venue query
  - native amend is currently limited to spot limit orders in the implemented scope

Current venue-by-venue private-state matrix at head:

| Venue | Open Orders | Recent Fills | Open Positions | Account Snapshot | Session / Runtime State | User Streams | Native Amend | Same-Target Retry Safety Evidence | Fallback Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hyperliquid | direct venue query | direct venue query | direct venue query when account address is available | persistence-backed snapshot/sync path | adapter/runtime only | semantic only, adapter not implemented | perpetual limit orders only | live open-order proof and order-id fill proof where ids exist | persistence fallback when account context or direct query is unavailable |
| Aster | direct venue query | persistence-backed summary | persistence-backed | persistence-backed | adapter/runtime only | semantic only, adapter not implemented | unsupported | live open-order proof; submitted-at-bounded direct same-account/same-symbol fill ambiguity when no exchange order id exists; exact order-id matches remain order-scoped; ambiguous evidence is retry-scoped only | persistence fallback for summary fills/positions and unavailable direct paths |
| OKX | direct venue query | direct venue query | persistence-backed | persistence-backed | adapter/runtime only | semantic only, adapter not implemented | current scoped limit-order path | live open-order proof plus direct fill evidence where available | persistence fallback for positions and unavailable direct paths |
| Coinbase Advanced Trade | direct venue query | direct venue query | persistence-backed | persistence-backed | adapter/runtime only | semantic only, adapter not implemented | spot limit orders only | live open-order proof plus direct fill evidence where available | persistence fallback for positions and unavailable direct paths |
| Binance | direct venue query | persistence-backed summary | persistence-backed | persistence-backed | adapter/runtime only | semantic only, adapter not implemented | unsupported | live open-order proof; submitted-at-bounded direct same-account/same-symbol fill ambiguity when no exchange order id exists; exact order-id matches remain order-scoped; ambiguous evidence is retry-scoped only | persistence fallback for summary fills/positions and unavailable direct paths |
| Kraken | direct venue query | direct venue query | persistence-backed | persistence-backed | adapter/runtime only | semantic only, adapter not implemented | spot limit orders only | live open-order proof plus direct fill evidence where available | persistence fallback for positions and unavailable direct paths |

This is deeper venue/account truth below routing, but it is still not full user-stream parity.

Current cancel truth:

- cancel request and cancel acknowledgement remain distinct from final canceled state where venue semantics require later reconciliation
- partially filled canceled or expired orders remain terminal after persisted fill merge; fill evidence now updates quantities without rewriting terminal or cancel-pending truth

## Current Post-Submit Layer

Below `SubmittedOrder`, the platform now supports:

- explicit reconciliation state
- lifecycle event history
- cancel request and cancel acknowledgement tracking
- final canceled state only after later reconciliation where venue semantics require it
- rejection classification and recovery recommendation
- bounded same-target recovery execution:
  - `reconcile_now`
  - `cancel_now`
  - `retry_same_target`
- selective amend execution where the adapter path is truthful

Recovery execution remains deliberately narrow:

- same submitted order
- same venue
- same account
- same target path
- no routing
- no failover
- no cross-binding retry

The 4.8 change at this layer is substrate depth, not a new routing-like action set:

- existing same-target actions still reconcile against one already-targeted venue/account path
- deeper adapter/runtime session-state, venue-private open-order, recent-fill, and open-position inspection now exist to support operator inspection and later reconciliation depth
- no cross-venue or target-reselection behavior was added

## Hyperliquid Status

Hyperliquid is no longer a special-case holdout for cancel/amend at head.

Current truthful Hyperliquid scope:

- account-targeted submit for perpetuals
- order-state-plus-fill reconciliation
- cancel acknowledgement with later reconciliation-driven final state
- native limit-order amend for the current perpetual scope
- capability and status surfaces now report cancel and amend support explicitly for that current proven scope

What is still not implied:

- full venue parity with every other exchange
- routing
- cross-binding recovery
- hidden cancel-and-replace mislabeled as amend

## What Remains Deferred

Still deferred at head:

- live routing execution
- best-binding selection
- CBBO
- child-intent fanout or splitting across bindings
- mandate-scoped open submission that bypasses routing assessment / target choice / conversion / readiness
- routed auto-submit or routed submission orchestration beyond one explicit already-selected child intent
- target reselection, route executor behavior, cross-binding recovery, and cross-venue retry/failover
- multi-binding execution orchestration
- broader amend parity for Aster and Binance unless support is proven later
- user-stream / event-driven private lifecycle parity
- fuller account-wide recent-fill parity for Aster and Binance
- routing-grade execution-market-data depth
- portfolio-grade risk and exposure parity beyond the current approval boundary

## Operational Memory

The repo uses explicit operational-memory files:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

The Obsidian brain is the required strategic-memory and cross-agent coordination layer:

- `money-flow/00_Money_Flow_Command_Center.md`
- `money-flow/01_Current_Phase.md`
- `money-flow/03_Decision_Log.md`
- `money-flow/05_Agent_Coordination.md`
- `money-flow/Project_Memory/money_flow_project_memory.md`

The repo-root `money_flow_project_memory.md` is a compatibility pointer only. Obsidian does not replace the changelog, repo tree, known issues, TODO, README, or canonical architecture/strategy docs.

## Review Bundle Workflow

Use the committed review-bundle workflow instead of manual zipping:

```bash
.venv/bin/python scripts/create_review_bundle.py --output /tmp/money-flow-review.zip
```

`.archiveignore` defines which local artifacts must stay out of the review bundle.
