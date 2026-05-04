# REPO_TREE

Last reviewed: `2026-05-04T19:48:32Z`

## Top-Level Structure

```text
.
├── .archiveignore
├── .env.example
├── .gitignore
├── AGENTS.md
├── CHANGELOG.md
├── KNOWN_ISSUES.md
├── TODO.md
├── REPO_TREE.md
├── money_flow_project_memory.md
├── README.md
├── apps/
├── core/
├── configs/
├── db/
├── docs/
├── infra/
├── money-flow/
├── scripts/
├── services/
└── tests/
```

## Responsibilities By Area

`.gitignore`
- Source-control hygiene guard for the `master` baseline.
- Excludes local secrets, virtualenvs, caches, local database/runtime state, logs, review bundles, handoff archives, generated strategy-validation evidence packs, Obsidian app state under `/money-flow/.obsidian/`, OS/editor files, and build artifacts while keeping `.env.example`, sample configs, and tracked Obsidian markdown notes trackable.

`.archiveignore`
- Review-bundle hygiene guard consumed by `scripts/create_review_bundle.py`.
- Excludes Git metadata, local secrets, virtualenvs, caches, generated archives, generated strategy-validation evidence packs, database/socket state, and Obsidian app state such as `money-flow/.obsidian/` from handoff ZIPs while keeping sample configs and tracked Obsidian markdown notes reviewable.

`configs/strategy_validation/`
- Strategy Validation research campaign configs.
- SV1.3 adds `money_flow_research_campaign.example.json` as a non-secret sample showing explicit symbols, components, fill timings, named windows, fees/slippage, capital, sizing, output directory, report formats, and the `(start_at, end_at]` candle-close window convention.
- SV1.4 adds `configs/strategy_validation/campaigns/` with canonical editable Money Flow evidence campaigns, currently `money_flow_core_btc.json` and `money_flow_core_multi_symbol.json`, for founder/operator review and data-readiness auditing. These configs contain no secrets and require only persisted historical candles.
- SV1.11 adds `configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json`, an example-only offline/manual manifest for research-only BTC/ETH/SOL Hyperliquid perpetual USDC `instruments` and `symbols` rows required before candle imports. SV1.11.1 marks the example as requiring operator verification before non-dry-run writes, and SV1.11.2 keeps the research seed non-trading by rejecting true strategy/trading eligibility.

`money-flow/`
- Tracked Obsidian strategic brain.
- Contains command center, current phase, decision log, agent coordination, component/workflow maps, and the moved full project memory.
- Phase 8.0.1 accepted the previously dirty Obsidian memory refresh as the strategic baseline and updated it to current Phase 8.0/8.0.1 truth.
- Phase 8.0.2 updates current-phase/coordination/decision notes for active submit-lease operator-summary truth only; full project memory remains untouched.
- SV1.0.1 updates current-phase/coordination/decision notes for strategy-validation research-truth/report hardening only; full project memory remains untouched.
- SV1.1 updates current-phase/coordination/decision notes for comparative strategy-validation batch reporting only; full project memory remains untouched.
- SV1.2 updates current-phase/coordination/decision notes for market-regime and data-coverage strategy-validation reporting only; full project memory remains untouched.
- SV1.2.1 updates current-phase/coordination/decision notes for window-boundary, coverage, and grouped-comparison research-truth hardening only; full project memory remains untouched.
- SV1.3 updates current-phase/coordination/decision notes for repeatable Money Flow research campaign/evidence-pack workflow only; full project memory remains untouched.
- SV1.4 updates current-phase/coordination/decision notes for evidence-pack review discipline and data-readiness baseline only; full project memory remains untouched.
- SV1.4.1 updates current-phase/coordination/decision notes for evidence-pack collision/overwrite integrity only; full project memory remains untouched.
- SV1.5 updates current-phase/coordination/decision notes for historical data-readiness and first canonical evidence-pack support only; full project memory remains untouched.
- SV1.5.1 updates current-phase/coordination/decision notes for candle-import and campaign-config research-truth hardening only; full project memory remains untouched.
- SV1.6 updates current-phase/coordination/decision notes for first canonical evidence-review summaries only; full project memory remains untouched.
- SV1.7 updates current-phase/coordination/decision notes for first real canonical evidence-review/data-gap reporting only; full project memory remains untouched.
- SV1.8 updates current-phase/coordination/decision notes for historical-data bootstrap and DB/schema/migration truth only; full project memory remains untouched.
- SV1.8.1 updates current-phase/coordination/decision notes for evidence-review schema-gate/report-truth only; full project memory remains untouched.
- SV1.9 updates current-phase/coordination/decision notes for intended strategy-validation DB target truth, canonical candle import requirements, and first-real evidence status only; full project memory remains untouched.
- SV1.10 updates current-phase/coordination/decision notes for intended local DB creation/migration truth, canonical candle import requirement grouping, and first-real evidence status only; full project memory remains untouched.
- SV1.11.2 updates current-phase/coordination/decision/current-state/roadmap notes for market-identity non-trading guard and complete requirement-aware preflight mapping only; full project memory remains untouched.
- Obsidian app state under `money-flow/.obsidian/` remains ignored.

`apps/api/`
- FastAPI control plane.
- Operator inspection and action endpoints for mandates/runtime, planning, non-executing routing assessments, route-readiness/data-sufficiency audits, controlled non-executing routing target recommendations, explicit recommendation acceptance into non-executing routing target choices, explicit target-choice-to-child-intent conversion, routed child-intent preparation/readiness inspection, explicit gated routed child-intent submission, routed submitted-order lineage, post-submit lifecycle/actionability, reconciliation and lifecycle-event audit inspection, read-only routed workflow aggregation, Phase 7.0 non-executing routing automation policy / dry-run plan inspection, Phase 7.1 durable routing automation approval / revocation / administrative consumption gate inspection, Phase 7.1.2 approvable-step policy truth, Phase 7.2 / 7.2.1 approval-gated recommendation acceptance into target choice only with coherent approval consumption, Phase 7.3 approval-gated target-choice conversion into one child intent only, Phase 7.4 approval-gated prepared-order preview/readiness inspection only, Phase 7.5 approval-gated submitted-order handoff through the existing explicit submit path only, Phase 7.5.1 post-submit approval-consumption pending truth, Phase 7.6 closeout regression coverage over the existing Phase 7 surfaces, execution readiness, submitted-order lifecycle, recovery, cancel, amendability/actionability, adapter/runtime session state, and private order/account-state visibility.

`apps/dashboard/`
- Placeholder only. No production dashboard UI is implemented yet.

`core/config/`
- Pydantic settings, environment profiles, runtime selection, and per-venue / strategy configuration.

`core/domain/`
- Shared typed domain models and enums.
- Includes canonical instrument identity, exchange/account truth, mandate/binding/component hierarchy, source-policy, strategy decisions, desired trades, routing assessment, route-readiness audit, routing target recommendation, routing target choice, Phase 7.0 routing automation policy/plan models, Phase 7.1 / 7.1.1 / 7.1.2 routing automation approval/gate models and lineage-scoped / current-policy approval status truth, Phase 7.2 approval-gated recommendation acceptance result models, Phase 7.3 approval-gated target-choice conversion result models, Phase 7.4 approval-gated preview/readiness result models, Phase 7.5 approval-gated submitted-order handoff result models, Phase 7.5.1 `consumption_pending` approval status truth, child intents, readiness, submitted orders, routed submitted-order lifecycle context, lifecycle-event audit context, and recovery/actionability models.
- SV1.0 adds strategy-validation request, assumption, simulated-trade, metrics, component-report, and report dataclasses. SV1.0.1 extends them with explicit fill timing, fill-source metadata, closed-trade and mark-to-market drawdown fields, and component comparison report data. SV1.1 adds batch request/run/report dataclasses for comparative validation across explicit component, fill-timing, symbol, date-window, fee, and slippage assumptions. SV1.2 adds data-coverage and regime-summary report dataclasses for deterministic market-regime/data-quality research diagnostics. SV1.2.1 adds explicit data-coverage window-convention truth. These are research/backtest artifacts only and are separate from `SubmittedOrder` and live execution artifacts.
- Includes `core/domain/routed_lifecycle.py`, the shared parser for routed submitted-order audit payloads so execution service and API surfaces use one missing/malformed lineage truth source.

`core/interfaces/`
- Shared protocols and service boundaries.
- Includes exchange, market data, indicators, portfolio, planning, risk, routing assessment / readiness-audit / recommendation / target-choice, execution, and Strategy Validation service boundaries through SV1.7.

`core/schemas/`
- API request/response schemas.
- Includes route-readiness and routing-target-recommendation request/response schemas plus Phase 7.0 routing automation policy/plan schemas, Phase 7.1 / 7.1.1 / 7.1.2 routing automation approval/revocation/consumption schemas with approval scope/fingerprint fields and current-policy gate-state truth, Phase 7.2 approval-gated recommendation acceptance request/response schemas, Phase 7.3 approval-gated target-choice conversion request/response schemas, Phase 7.4 approval-gated preview/readiness request/response schemas, Phase 7.5 approval-gated submitted-order handoff request/response schemas, derived routed submitted-order lineage, lifecycle-context, lifecycle-event, prepared-order-preview, execution-readiness, read-only routed workflow inspection response fields, and Phase 8.0 read-only operator routed workflow summary response fields so API clients can inspect routed-origin, recommendation-backed audit metadata, approval state, manual-resolution needs, submitted-order safety, and submit-lease state without parsing raw payload directly.

`db/models/`
- SQLAlchemy persistence models for canonical instruments, symbol mappings, client/account/mandate hierarchy, source-policy, candles, indicators, strategy decisions, desired trades, routing assessments, route-readiness audits, routing target recommendations, routing target choices, routing automation approvals, readiness evaluations, child intents, explicit child-intent submission leases, submitted orders, fills, lifecycle events, checkpoints, and overlays.

`db/migrations/`
- Alembic migration history.
- Current head includes the Phase 6.1 binding-priority migration, after the Phase 6.0.0 routing-target-recommendation migration, the Phase 5.10.1 route-readiness audit migration, the Phase 5.1 routing target-choice migration, and the Phase 5.0 `routing_assessments` / `routing_assessment_candidates` substrate.
- Phases 5.2, 5.2.1, 5.3, and 5.3.1 add no migration; target-choice conversion and routed preparation/readiness lineage use existing `order_intents`, `execution_readiness_evaluations`, and structured provenance/idempotency.
- Phase 5.4 adds no migration; explicit routed submission uses existing `order_intents`, `execution_readiness_evaluations`, `submitted_orders`, and structured provenance/raw payload lineage.
- Phases 5.5, 5.6, 5.7, 5.7.1, 5.8, 5.8.1, 5.8.2, 5.9, 5.9.1, 5.9.2, 5.10, and 5.10.2 add no migration; routed submitted-order lineage/lifecycle/reconciliation-event inspection is derived from existing `submitted_orders.raw_payload`, reconciliation/update payload collisions cannot create, overwrite, or mutate platform `routed_submission` audit lineage, routed order-shape policy input/decision facts plus non-finite limit-price validation/reason-surface cleanup are handled through existing API/service models and child-intent provenance, Phase 5.10 closes the routing substrate with regression coverage rather than schema changes, and Phase 5.10.2 tightens route-readiness audit truth in service/tests/docs only.
- Phase 5.10.1 adds `20260419_0019_phase5101_route_readiness_audit.py`, a small durable audit migration for `route_readiness_audits` and `route_readiness_candidate_audits`; the tables are non-selecting data-sufficiency audit records only and do not store recommendations, rankings, scores, allocations, route plans, target choices, child intents, readiness evaluations, or submitted orders.
- Phase 6.0.0 adds `20260419_0020_phase600_routing_target_recommendation.py`, a small durable audit migration for `routing_target_recommendations`; the table stores non-executing `single_ready_candidate_only` recommendation/block outcomes and does not store rankings, scores, allocations, route plans, target choices, child intents, readiness evaluations, submitted orders, fanout, CBBO, or submit instructions.
- Phase 6.0.1 adds no migration; it hotpatches recommendation current-truth revalidation in service/tests/docs only.
- Phase 6.0.2 adds no migration; it hotpatches recommendation-time quote observation freshness checks and source audit `recommendation_created` truth in service/tests/docs only.
- Phase 6.1 adds `20260419_0021_phase61_binding_recommendation_priority.py`, a minimal nullable `target_recommendation_priority` field on `mandate_account_bindings` for the optional `explicit_binding_priority` recommendation policy. The field is operator preference only and does not store rank, score, venue quality, allocation, route plan, submit instruction, or execution behavior. Phase 6.1.1 adds no migration; it bounds accepted recommendation `policy_name` input, rejects malformed direct service policy names before persistence, and makes priority clearing explicit through existing binding APIs. Phase 6.2 adds no migration; recommendation acceptance uses existing routing target-choice rows plus existing recommendation/audit `target_choice_created` flags and provenance linkage. Phase 6.2.1 adds no migration; it hardens same-audit acceptance idempotency and timestamp provenance in service/tests/docs only. Phase 6.2.2 adds no migration; it gates same-audit idempotency so blocked recommendations cannot be marked accepted by an already accepted audit. Phase 6.3 adds no migration; accepted recommendation-backed target-choice conversion reuses existing `order_intents`, recommendation/audit `child_intent_created` flags, idempotency keys, and provenance lineage. Phase 6.4 adds no migration; recommendation-backed preview/readiness reuses existing `PreparedVenueOrder` and `ExecutionReadinessEvaluationModel` paths plus provenance-derived routed-lineage response fields. Phase 6.4.1 adds no migration; it hotpatches routed order-shape policy/current-intent drift checks plus readiness-time stale quote reason codes in service/tests/docs only. Phase 6.5 adds no migration; the manual routed-flow harness is tooling/tests/docs only and reuses existing service paths. Phase 6.6 adds no migration; manual harness timing is local tooling/tests/docs only and adds no telemetry persistence, route executor, config, or service-wide instrumentation. Phase 6.7 through Phase 6.10 add no migration; closeout reuses existing `order_intents`, `execution_readiness_evaluations`, `submitted_orders`, lifecycle-event rows, raw payload/provenance lineage, and read-only aggregation without new tables or config. Phase 6.10.1 adds `20260423_0022_phase6101_submission_leases.py`, a narrow `order_intent_submission_leases` guard table keyed by environment, intent id, and purpose so concurrent explicit submit calls for the same child intent cannot both reach adapter submission before a `SubmittedOrder` exists. Phase 6.10.2 adds `20260423_0023_phase6102_submission_lease_uncertainty.py`, widening only the lease status column so terminal `adapter_submit_persistence_unknown` can be stored when adapter submit returned but local submitted-order persistence failed. Phase 6.10.3 adds no migration because the widened status column and metadata JSON can store terminal `adapter_submit_may_have_started` state before adapter submission can begin. Phase 7.0 adds no migration; automation policy and dry-run plans are non-persisted API/service inspection models over existing routed workflow records. Phase 7.1 adds `20260426_0024_phase71_routing_automation_approvals.py`, a narrow durable `routing_automation_approvals` table for one-action operator approval gates with active/revoked/consumed/expired state, policy snapshots, lineage, and boundary flags. Phase 7.1.1 adds `20260430_0025_phase711_approval_truth_scope.py`, a narrow approval-truth migration adding lineage fingerprint/scope columns plus a partial unique active-scope index so only one active approval can exist for one current desired-trade/action/lineage scope. Phase 7.1.2 adds no migration; it tightens approval validation and gate-state truth so manual-only / dry-run-only / disabled / deferred / blocked / already-satisfied steps cannot create active approvals or appear approved. Phase 7.2 adds no migration; it consumes existing approval rows to call the existing recommendation acceptance path and records target-choice/no-downstream provenance in approval JSON fields. Phase 7.2.1 adds no migration; it refactors approval-gated acceptance to use one session/commit for target-choice creation or reuse plus approval consumption. Phase 7.3 adds no migration; it consumes existing approval rows to call the existing target-choice conversion validation/persistence helpers and records child-intent/no-downstream provenance in approval JSON fields. Phase 7.4 adds no migration; it consumes existing approval rows to call the existing child-intent prepared-order preview/readiness path and records preview/readiness/no-submission provenance in approval JSON fields. Phase 7.5 adds no migration; it consumes existing approval rows to call the existing explicit child-intent submit path, records submitted-order/no-route-executor/no-fanout/no-broad-auto-submit provenance in approval JSON fields, and relies on existing `submitted_orders` plus `order_intent_submission_leases`. Phase 7.5.1 adds no migration because the approval status column is already string-backed and approval JSON fields can record `consumption_pending` post-submit approval-consumption failure truth. Phase 7.6 adds no migration; it is closeout regression/docs coverage only and adds no action stage, persistence table, config, route executor, or broad auto-submit. Phase 8.0 adds no migration; operator workflow summaries are read-only aggregation over existing workflow, approval, readiness, submitted-order, and submission-lease records. Phase 8.0.1 also adds no migration; it is Obsidian/repo-memory hygiene only. Phase 8.0.2 adds no migration; it tightens read-only operator-summary truth for active unexpired submit leases in service/tests/docs only. SV1.0, SV1.0.1, SV1.1, SV1.2, SV1.2.1, SV1.3, SV1.4, SV1.4.1, SV1.5, and SV1.5.1 add no migration; strategy-validation reports, comparative batches, data-coverage diagnostics, market-regime summaries, window/coverage/grouped-comparison truth, campaign configs, evidence packs, canonical campaign configs, campaign data-readiness audits, review checklists, collision-safe evidence-pack write paths, Markdown readiness summaries, offline candle import/upsert tooling, and import-integrity validation use existing candle rows/tables and existing Money Flow logic, and simulated trades are not persisted as `SubmittedOrder` or live execution truth. Approval records do not act as `SubmittedOrder` reservations, and Phase 7.5 through SV1.5.1 add no route executor or broad auto-submit.
- SV1.6 through SV1.11.2 add no migration; canonical evidence-review summaries, DB target / reachability / schema / migration / candle-table gap truth, required strategy-validation table checks, canonical candle import requirements, partial-evidence status, first-real-run historical-data bootstrap reporting, schema-gated evidence-pack generation, DB-target evidence-generation blocking, candle-import timestamp/provenance summary hardening, intended local DB readiness reporting, de-duplicated import requirement grouping, research-only market-identity seed/verify, non-trading seed governance, and requirement-aware candle preflight use existing campaign configs/tables and saved research outputs only.
- Phases 4.6 through 4.10.2 add no new migration and instead deepen lifecycle/private-state truth in service/adapter code.

`docs/architecture.md`
- Canonical architecture document at head.
- Consolidated source of truth for platform hierarchy, venue matrix, execution boundary, and below-routing lifecycle depth.

`docs/strategy.md`
- Canonical strategy document at head.
- Consolidated source of truth for indicator, decision, desired-trade, child-intent, readiness, submitted-order, and below-routing execution behavior.

`docs/strategy_validation_sv1_7_first_evidence_review.md`
- Founder/operator-readable SV1.7 gap report from the first real canonical evidence-review attempt.
- Records sanitized DB access findings, canonical campaign audit outcomes, no-pack generation status, and the concrete historical-data/schema gap before paper-trading design can be considered.

`docs/strategy_validation_sv1_8_historical_data_bootstrap.md`
- Founder/operator-readable SV1.8 historical-data bootstrap and first-real evidence review report.
- Records sanitized DB target findings, Alembic/schema status, migration command hints, canonical campaign audit blockers, missing canonical candle requirements, and no-pack generation status.

`docs/strategy_validation_sv1_8_1_schema_truth_hotfix.md`
- Founder/operator-readable SV1.8.1 schema-truth hotfix report.

`docs/strategy_validation_sv1_9_first_real_evidence_status.md`
- Founder/operator-readable SV1.9 first-real canonical evidence status report covering intended DB target truth, migration/schema status, canonical candle gaps, import commands, and generated-pack status.
- Records that evidence-pack generation now requires `migrated_schema_ready`, current Alembic migration truth, and required `candles` / `instruments` / `symbols` table presence; no first real evidence packs are generated by this hotfix.

`docs/strategy_validation_sv1_9_1_evidence_target_truth_hotfix.md`
- Founder/operator-readable SV1.9.1 evidence-target truth hotfix report.
- Records that ambiguous/non-intended maintenance DB targets now block evidence generation by default, timezone-naive candle timestamps are rejected by default unless an explicit non-canonical override is used, import summaries include stronger source/timestamp provenance, and no first real canonical evidence packs were generated.

`docs/strategy_validation_sv1_10_first_real_evidence_status.md`
- Founder/operator-readable SV1.10 first-real evidence status report.
- Records the intended local DB target `money_flow` on `127.0.0.1:5432`, Alembic head migration truth, required table availability, zero persisted candles, 18 unique canonical import requirements, and no evidence-pack generation because candle data remains missing.

`docs/strategy_validation_sv1_11_market_identity_and_import_preflight.md`
- Founder/operator-readable SV1.11 market-identity and candle-import preflight report.
- Explains the research-only BTC/ETH/SOL Hyperliquid perpetual USDC identity manifest, dry-run / seed / verify-only commands, no-write candle preflight, and why candle import remains blocked until identity and file validation pass.

`docs/strategy_validation_sv1_11_1_preflight_and_identity_guard_hardening.md`
- Founder/operator-readable SV1.11.1 hardening report.
- Records that non-dry-run market-identity writes require explicit operator verification plus `verified_by`, row-level preflight is not canonical coverage proof, and requirement-aware preflight must map files to exact canonical close-time requirements before bulk import.

`docs/strategy_validation_sv1_11_2_seed_and_preflight_governance_hotfix.md`
- Founder/operator-readable SV1.11.2 governance hotfix report.
- Records that Strategy Validation market-identity seed cannot enable strategy/trading eligibility, requirement-aware preflight requires complete one-to-one input-to-requirement mapping, review JSON candle import requirements are preferred for candle preflight, and no candles/evidence packs are generated.

`docs/investors.md`
- Plain-language investor-facing overview.
- Explains what Money Flow is today, what it is intentionally not yet, and where the product roadmap goes next without assuming trading-systems background.

`money_flow_project_memory.md`
- Compatibility pointer to `money-flow/Project_Memory/money_flow_project_memory.md`.
- Not the canonical full strategic-memory source.

`services/exchange/hyperliquid/`
- Most mature venue adapter for reconciliation depth and current perpetual submit scope.
- Deepest current lifecycle path.
- Truthful cancel acknowledgement, native limit-order amend, deeper order-status-plus-fill reconciliation, and direct private open-order/recent-fill/open-position polling now exist for the current perpetual scope where account context is available.
- Direct open-position mark price now uses venue `markPx`, derives from `positionValue / abs(szi)` when needed, and remains `None` when no truthful mark price can be derived.

`services/exchange/aster/`
- Perpetual adapter with submit, reconcile, cancel, and bounded same-target retry support.
- Strict client-order-id reuse semantics now handled with fresh retry IDs.
- Native amend remains explicitly unsupported; reconciliation now preserves canceled/expired-after-partial-fill truth.
- Private open-order polling is direct and returned as venue-private order snapshots.
- Summary-layer recent fills remain persistence-backed, but same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks when no exchange order id exists.
- Ambiguous retry fill evidence remains scoped to `SubmittedOrderPrivateFillEvidence` and is not exposed through a plain submitted-order fill convenience method.

`services/exchange/okx/`
- Spot/perpetual adapter with submit, reconcile, truthful cancel lifecycle, bounded recovery execution, native amend, and direct private open-order/recent-fill polling with runtime-truthful source reporting.

`services/exchange/coinbase/`
- Spot adapter with JWT submit, reconcile, truthful cancel lifecycle, bounded recovery execution, native edit-order amend for the current spot limit-order scope, and direct private open-order/recent-fill polling with runtime-truthful source reporting.

`services/exchange/binance/`
- Spot adapter with submit, reconcile, cancel, and bounded same-target retry support.
- Strict client-order-id reuse semantics now handled with fresh retry IDs.
- Native amend remains explicitly unsupported at head.
- Private open-order polling is direct and returned as venue-private order snapshots.
- Summary-layer recent fills remain persistence-backed, but same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks when no exchange order id exists.
- Ambiguous retry fill evidence remains scoped to `SubmittedOrderPrivateFillEvidence` and is not exposed through a plain submitted-order fill convenience method.

`services/exchange/kraken/`
- Spot adapter with submit, reconcile, truthful cancel acknowledgement plus later cancel reconciliation, and bounded recovery execution.
- Native amend now exists for the current spot limit-order scope.
- Direct private open-order and recent-fill polling now exist for the current scope, with runtime-truthful source reporting.

`services/exchange/registry.py`
- Venue registry/factory used by the control plane to inspect Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken side by side.

`services/market_data/`
- Candle bootstrap, persistence, checkpoint semantics, and freshness handling.

`services/indicators/`
- Deterministic indicator computation and snapshot persistence.

`services/strategy/`
- Strategy framework and Money Flow strategy family.

`services/strategy_validation/`
- SV1.0 / SV1.0.1 / SV1.1 / SV1.2 / SV1.2.1 / SV1.3 / SV1.4 / SV1.4.1 / SV1.5 / SV1.5.1 / SV1.6 / SV1.7 / SV1.8 / SV1.8.1 / SV1.9 / SV1.9.1 / SV1.10 Money Flow validation/backtesting, research-campaign, evidence-readiness, evidence-integrity, historical-data readiness, evidence-review, DB/schema bootstrap, schema-gated first-real-run data-gap, evidence-target truth, candle-import timestamp/provenance, intended local DB readiness, and canonical import requirement grouping service boundary.
- Reads persisted historical candles, computes indicator snapshots in memory, reuses the current Money Flow strategy rules, simulates research-only trades with explicit fee/slippage/capital/fill-timing assumptions, and returns deterministic component and aggregate performance reports.
- SV1.0.1 supports `same_candle_close_research_only`, `next_candle_open`, and `next_candle_close` fill timing; reports closed-trade and mark-to-market drawdown separately; and emits expanded founder/operator Markdown reports with assumptions, component comparison, trade summaries, reason counts, and limitations.
- SV1.1 adds deterministic batch validation and comparison reports across explicit component, fill-timing, symbol, date-window, fee, and slippage assumptions. Comparison output is descriptive research only and does not optimize, recommend a variant, change Money Flow rules, route, or execute.
- SV1.2 adds deterministic data-coverage diagnostics, simple trend/volatility regime labels, regime-grouped performance summaries, and multi-window batch reporting support. Regimes are descriptive only and do not change strategy behavior.
- SV1.2.1 standardizes all validation windows on candle closes in `(start_at, end_at]`, counts expected close slots for coverage, warning-codes unaligned window boundaries, prevents coverage above 100%, and keeps blocked runs visible in grouped batch comparisons while computing metrics only from completed runs. It changes no Money Flow rules, optimization, routing, execution automation, exchange calls, paper/live trading, or live artifacts.
- SV1.3 adds campaign helpers that parse explicit JSON campaign configs, expand named symbols/components/fill timings/windows/cost assumptions into existing batch requests, and write timestamped evidence packs containing normalized config, manifest, JSON, Markdown, and README files. Campaign output preserves window-convention and blocked-run truth and remains research-only.
- SV1.4 adds persisted-candle campaign data-readiness audit helpers, JSON-ready audit output, evidence-pack review checklist content, and manual paper-trading readiness criteria. These surfaces are manual review aids only and create no paper/live trading artifacts.
- SV1.4.1 makes evidence-pack writes collision-safe: default `unique_suffix` creates a suffixed run directory instead of overwriting an existing pack, optional `fail_if_exists` raises explicitly, and manifests record requested/final run ids, final path, collision policy, collision occurrence, and suffix truth.
- SV1.5 validates campaign `window_convention` metadata against the platform `(start_at, end_at]` convention, adds founder-readable Markdown data-readiness audit output, and adds offline public CSV/JSON candle import/upsert helpers for research historical-data gaps.
- SV1.5.1 hardens campaign/import truth: contradictory inclusive-start `window_convention` text is rejected, existing candles cannot be silently retargeted to another resolved symbol/instrument identity, imported row duration must match the selected timeframe, malformed/non-finite/inconsistent OHLCV and negative trade counts fail, and invalid import files roll back without partial inserts or updates.
- SV1.6 adds first canonical evidence-review helpers that audit canonical configs, generate collision-safe evidence packs only when data-readiness is sufficient, summarize evidence-pack paths/data gaps/fill-timing/component/regime/drawdown/cost observations, and expose manual paper-readiness review status without approving paper trading.
- SV1.7 adds sanitized DB access inspection, candle-table existence and persisted-candle-count truth, synthetic blocked data-readiness rows for unreachable/missing-schema databases, `partial_evidence_ready_with_data_gaps` mixed-result status, and a tracked first-real-run gap report for canonical campaigns.
- SV1.8 adds DB/schema/migration bootstrap status, Alembic head/current truth, migration hints, and a status-only evidence-review CLI path before first real evidence packs.
- SV1.8.1 requires `migrated_schema_ready` plus required `candles`, `instruments`, and `symbols` tables before evidence-pack generation, and aggregates top-level live/exchange flags from campaign results.
- SV1.9 makes the strategy-validation DB target explicit in evidence-review output, including sanitized driver/host/port/name/user, target-role classification, intended-DB truth, maintenance-database warnings, and canonical candle import requirements for blocked or missing readiness rows. The local SV1.9 review generated no real evidence packs because the default `postgres` host was unresolved and the explicit `127.0.0.1:54322/postgres` override was unreachable in this shell and is also a maintenance database name requiring operator confirmation.
- SV1.9.1 makes ambiguous/non-intended maintenance DB targets generation-blocking by default, rejects timezone-naive candle imports by default, exposes `--assume-naive-utc` as a provenance-marked non-default import override, records source file name/hash/row-count/timestamp-assumption import summary truth, and refreshes Obsidian current-state memory through SV1.9.
- SV1.10 records the intended local strategy-validation target as `money_flow` on `127.0.0.1:5432`, applies Alembic head locally when available, verifies required tables, groups overlapping canonical BTC import requirements across campaigns, and reports the remaining zero-candle `insufficient_data` gap without generating evidence packs.
- SV1.11 adds research-only market identity seed/verify helpers for canonical BTC/ETH/SOL Hyperliquid perpetual USDC instruments/symbol mappings, evidence-review canonical identity readiness reporting, and candle-import preflight that validates files/mappings without writing candles. SV1.11.1 hardens this boundary so non-dry-run identity writes require explicit operator verification/verified-by provenance, and requirement-aware preflight can prove a mapped input file covers the exact canonical close-time slots before import. SV1.11.2 blocks true strategy/trading eligibility in this research seed path and requires complete one-to-one input-to-requirement mapping before requirement-aware readiness can pass.
- Creates no live desired trades, strategy decisions, child intents, prepared orders, readiness evaluations, submitted orders, routing artifacts, approval changes, private exchange calls, exchange order calls, or exchange adapter calls.

`services/planning/`
- Mandate-level desired-trade drafting, source-policy inspection, convertibility checks, routing-candidate derivation, and normalized quote inspection ahead of later routing.

`services/routing/`
- Routing assessment, route-readiness audit, controlled non-executing target recommendation, target-choice audit, and explicit one-child-intent conversion substrate for `routing_required` mandate-scoped opens.
- Phase 7.0 adds non-executing routing automation policy and dry-run plan inspection over existing routed workflow records; it creates no artifacts and advances no workflow state.
- Phase 7.1 adds durable operator approval records for explicit same-target automation action gates; Phase 7.1.1 makes reuse lineage-scoped and current-truth-bound, and Phase 7.1.2 keeps approval validity bounded to currently approvable policy states, so approvals can be active, revoked, consumed, expired, stale-lineage, or Phase 7.5.1 `consumption_pending` after post-submit approval-consumption failure. Phase 7.2 adds the first approval-consuming action hook: recommendation acceptance into a target choice only. Phase 7.2.1 keeps that hook coherent by committing target-choice creation/reuse and approval consumption together. Phase 7.3 adds the second approval-consuming action hook: target-choice conversion into one child intent only. Phase 7.4 adds the third approval-consuming action hook: prepared-order preview/readiness inspection for one existing child intent only. Phase 7.5 adds the fourth approval-consuming action hook: submitted-order handoff for one already-ready child intent through the existing explicit submit path only. Phase 7.5.1 ensures a submitted order plus failed approval consumption is inspectable and repeatable without another adapter submit. Phase 7.6 adds closeout regression coverage proving the accepted Phase 7 chain remains approval-gated, current-lineage-bound, same-target, and separate from dry-run/admin-consume behavior.
- Phase 8.0 adds read-only operator routed workflow summaries by desired trade, combining existing routed workflow records, approval/gate state, manual-resolution requirements, submitted-order handoff safety, and submit-lease/concurrency state without creating artifacts, consuming approvals, resolving manual states, calling adapters, or adding trading behavior. Phase 8.0.2 makes unexpired active submit leases block repeat-submit safety and next-safe-action truth as `submission_in_progress`, while terminal uncertainty remains manual-reconciliation-required and expired pre-adapter active leases remain stale-replaceable.
- Persists candidate inventory, binary binding eligibility/ineligibility status, reason codes, missing-data facts, and operator-requested target-choice audit records; Phase 5.2 can convert one explicit valid target choice into one binding/account-targeted child intent without preparation, readiness evaluation, submission, splitting, ranking, or scoring, and Phase 5.2.1 hardens assessment / desired-trade / binding lineage checks before conversion.
- Converted routed child intents use Phase 5.8 explicit order-shape policy input/decision: omitted policy remains market order, no limit price, and reduce_only=false; explicit LIMIT requires a positive finite requested limit price and modeled order-type support. Phase 5.8.1 blocks non-finite LIMIT prices before child-intent creation, and Phase 5.8.2 keeps malformed/non-finite blocks from claiming `limit_price_explicit`. Slippage guards and market-data-derived price sources remain deferred.
- Phase 5.10.1 adds a non-selecting route-readiness/data-sufficiency audit beside routing assessment. It can audit a routing-required desired trade or existing routing assessment for missing, stale, unsupported, unavailable, policy-blocked, and blocking facts per candidate, with explicit data-source labels and `ready_for_recommendation` meaning data-sufficient only; it does not recommend, rank, score, choose, convert, prepare, assess execution readiness, submit, or execute. Phase 5.10.2 hotpatches audit truth so assessment-backed quote facts are not mislabeled as fresh venue queries, missing/invalid desired-trade side or quantity blocks readiness, malformed/non-finite/non-positive quote prices are reason-coded before notional math, and default MARKET policy is labeled defaulted rather than explicit.
- Phase 6.0.0 adds persisted non-executing `RoutingTargetRecommendation` records from route-readiness audits only. Phase 6.0.1 hotpatches current-truth revalidation so success also requires current mandate enablement, desired-trade symbol identity, and active/trading-eligible venue symbol mapping truth. Phase 6.0.2 hotpatches recommendation-time freshness so the recommended candidate's stored `quote_observed_at` must still be fresh and the source audit reports `recommendation_created=true` after any recommendation record is persisted. Phase 6.1 keeps `single_ready_candidate_only` as the default policy and adds optional `explicit_binding_priority`: lower positive operator-configured `MandateAccountBinding.target_recommendation_priority` wins only when one ready candidate has the winning priority; missing/malformed priority and ties block. Phase 6.1.1 bounds `policy_name` input to accepted values at the API boundary, keeps malformed/oversized direct service policy input out of persistence, preserves omitted priority on binding updates, clears priority only through `clear_target_recommendation_priority=true`, and verifies priority-selected candidates still block on stale quote observations. Phase 6.2 adds explicit operator-triggered recommendation acceptance into exactly one non-executing `RoutingTargetChoice` after revalidating recommendation status, audit/recommendation freshness, stored quote observation freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency; repeated acceptance returns the existing choice. Phase 6.2.1 prevents duplicate successful recommendations from one route-readiness audit from creating multiple accepted target choices, returns the original choice, marks the later recommendation as linked, and preserves the original recommendation/audit acceptance timestamp while recording idempotent checks separately. Phase 6.2.2 gates same-audit idempotency behind successful-recommendation preflight so blocked recommendations from an already accepted audit cannot be marked `target_choice_created` or stamped with accepted-looking provenance. Phase 6.3 reuses the existing target-choice conversion path so an accepted recommendation-backed target choice can be explicitly converted into exactly one routed child `OrderIntent` after recommendation/audit/quote/current-truth revalidation, while repeated and same-audit duplicate conversion attempts return the existing child intent. Phase 6.4 lets those recommendation-backed child intents use the existing prepared-order preview and submission-readiness inspection paths with recommendation/audit/candidate quote/current-truth validation and top-level routed-lineage API response fields. Phase 6.4.1 blocks readiness if stored routed order-shape policy is missing, malformed, or mismatched against current child-intent order_type, limit_price, or reduce_only facts, and it reports stale stored quote observations at this surface with `quote_stale_at_readiness`. Phase 6.9 adds read-only routed workflow inspection by desired trade, aggregating existing desired trade, assessment, audit, recommendation, target choice, child intent, readiness, submitted-order, and lifecycle-event records without creating or mutating artifacts. Recommendations still do not use ranking, scoring, price comparison, CBBO, automatic target-choice creation, automatic child-intent creation, fanout, allocation, route plans, target reselection, or route executor behavior; submitted orders occur only after explicit child-intent submit gates pass.

`services/risk/`
- First-pass desired-trade approval/rejection layer.

`services/execution/`
- Child-intent preparation, hardened routed child-intent lineage validation before preview/readiness/submission, venue-native preview/preflight, execution readiness, submission for supported non-routed child-intent paths, explicit gated routed submission for already selected converted child intents, submitted-order lifecycle, routed post-submit lifecycle/actionability/reconciliation-event context, recovery recommendations, bounded same-target recovery execution, truthful cancel on supported scopes, selective native amend execution, amend-acknowledgement follow-up through later reconciliation, fill-merge preservation of terminal / cancel-pending submitted-order truth, and deeper downstream reliance on venue/account private-state inspection.
- Recommendation-backed routed preview/readiness validates source recommendation/audit/current truth, stored quote observation freshness, and stored routed order-shape policy against the current child intent shape before adapter preparation can proceed. Phase 6.7 submitted-order handoff uses the existing explicit submit path for the already selected recommendation-backed child intent, requires the normal live-submit and routed-submit gates plus current readiness, and stamps desired-trade, assessment, route-readiness audit, recommendation, target choice, intent, readiness, selected target, recommendation policy, routed order-shape policy, and no-fanout/no-allocation/no-scoring/no-target-reselection/no-auto-submit flags into the submitted-order routed payload. Phase 6.10.1 adds a narrow persistence-backed child-intent submit lease before adapter submission so concurrent explicit submit calls for one intent cannot both reach the adapter before a `SubmittedOrder` exists. Phase 6.10.2 marks adapter-returned/local-persistence-failed attempts as terminal `adapter_submit_persistence_unknown`, records manual-reconciliation metadata, and blocks future submits for that intent before adapter submission even after TTL. Phase 6.10.3 marks terminal `adapter_submit_may_have_started` before calling the adapter, so crashes, timeouts, transport ambiguity, and unknown post-call adapter exceptions cannot become TTL-retryable; stale pre-adapter `active` leases remain replaceable. The lease is not submitted-order truth or a route executor.
- Routed submitted-order lineage remains read-only audit metadata derived from platform-authored `SubmittedOrder.raw_payload["routed_submission"]`; missing, partial, or wrong-typed routed payloads are bounded through the shared domain parser and do not drive target reselection or lifecycle behavior. Phase 5.7 exposes routed lifecycle context on recovery/actionability surfaces while keeping recovery same-target / same-account / same-venue only, Phase 5.7.1 preserves that lineage on same-target routed retry results, Phase 5.9 preserves routed audit payload through reconciliation updates while exposing routed context on lifecycle-event responses, Phase 5.9.1 makes current platform lineage authoritative over colliding update-payload `routed_submission` keys, Phase 5.9.2 strips update-payload `routed_submission` from non-routed submitted-order raw payloads so adapters cannot fabricate routed origin, and Phase 5.10 closeout coverage verifies those existing surfaces remain consistent without adding execution behavior.
- Retry evidence remains same-target and conservative: live venue-private open-order proof blocks retry, while Aster/Binance private trade evidence without an exchange order id is recorded as submitted-at-bounded same-account/same-symbol ambiguity rather than targeted order fill proof and cannot be fetched as plain submitted-order fill truth.

`services/portfolio/`
- Portfolio/account-truth loaders and related summaries.

`scripts/`
- Local developer and review-support utilities.
- Includes `scripts/create_review_bundle.py` for deterministic review ZIP creation based on `.archiveignore`.
- Includes `scripts/manual_routed_flow.py` for Phase 6.5 manual routed-flow inspection from an existing desired trade key through optional existing service calls to readiness. It emits JSON, includes Phase 6.6 local `timing_ms` / per-step `elapsed_ms` fields, skips submission by default, and blocks submit attempts unless the explicit danger-confirmation flag is supplied.
- Includes `scripts/run_money_flow_backtest.py` for SV1.0/SV1.0.1 read-only Money Flow strategy-validation reports over persisted candles with explicit assumptions, selectable fill timing, and JSON/Markdown output.
- Includes `scripts/run_money_flow_validation_batch.py` for SV1.1/SV1.2/SV1.2.1 read-only comparative Money Flow validation across explicit matrices of components, fill timings, symbols, date windows, and cost assumptions, including repeated `--window start,end` support using candle closes in `(start, end]`.
- Includes `scripts/run_money_flow_research_campaign.py` for SV1.3/SV1.4/SV1.4.1/SV1.5 read-only Money Flow campaign configs, evidence-pack output, `--audit-only` persisted-candle readiness inspection, Markdown audit output, and explicit evidence-pack collision policy. It writes saved research reports only when not in audit-only mode and does not optimize, recommend, route, trade, or call exchange adapters.
- Includes `scripts/import_strategy_validation_candles.py` for SV1.5/SV1.5.1/SV1.9.1 offline/public CSV or JSON candle imports into existing `candles` rows. It is duplicate-safe for matching candle identity, rejects identity conflicts, timeframe-duration mismatches, malformed/non-finite/inconsistent OHLCV rows, negative trade counts, and timezone-naive timestamps by default, rolls back invalid files, records source file/hash/timestamp-assumption summary provenance, and remains research-only; it does not call exchange adapters, private endpoints, order endpoints, or create live trading artifacts.
- Includes `scripts/review_money_flow_evidence_packs.py` for SV1.6/SV1.7/SV1.8/SV1.8.1/SV1.9/SV1.9.1 read-only canonical evidence review. It audits canonical campaign configs by default, reports sanitized DB target/reachability/schema/migration/candle-table status, supports `--db-status-only`, optionally generates collision-safe evidence packs only when schema, target, and data-readiness are sufficient, emits JSON/Markdown review summaries plus canonical candle import requirements for blocked rows, and does not optimize, recommend, route, trade, or call exchange adapters.
- Includes `scripts/seed_strategy_validation_market_identity.py` for SV1.11/SV1.11.2 offline/manual research-only market identity seed/verify from manifest. It upserts only `instruments` and `symbols`, refuses symbol/instrument retargeting conflicts, rejects true strategy/trading eligibility, supports `--dry-run` / `--verify-only`, requires `--operator-verified --verified-by` for non-dry-run writes, and creates no candles, evidence packs, exchange calls, routing artifacts, or live artifacts.
- Includes `scripts/preflight_strategy_validation_candle_import.py` for SV1.11/SV1.11.2 candle-import preflight. It validates CSV/JSON candle files and/or evidence-review requirements without writing candles, rejects timezone-naive timestamps by default through the same validation semantics, verifies symbol/instrument mappings, supports requirement-aware complete one-to-one input-to-requirement coverage checks, prefers candle import requirements from review JSON when present, and creates no evidence packs, exchange calls, routing artifacts, or live artifacts.

## Operational Entrypoints

- API app: `apps.api.app.main:app`
- Alembic: `alembic upgrade head`
- Test suite: `.venv/bin/pytest -q`
- Review bundle: `.venv/bin/python scripts/create_review_bundle.py --output /tmp/money-flow-review.zip`
- Manual routed-flow inspection: `.venv/bin/python scripts/manual_routed_flow.py --desired-trade-key <desired_trade_key> --run-through-readiness`
- Money Flow strategy validation: `.venv/bin/python scripts/run_money_flow_backtest.py --venue <venue> --symbol <symbol> --component sleeve_15m --start <iso> --end <iso> --initial-capital <amount> --fee-bps <bps> --slippage-bps <bps> --fill-timing next_candle_open`
- Money Flow comparative validation batch: `.venv/bin/python scripts/run_money_flow_validation_batch.py --venue <venue> --symbol <symbol> --component sleeve_15m --component sleeve_1h --fill-timing same_candle_close_research_only --fill-timing next_candle_open --start <iso> --end <iso> --initial-capital <amount> --fee-bps <bps> --slippage-bps <bps> --format markdown`; validation windows use candle closes in `(start, end]`.
- Money Flow research campaign evidence pack: `.venv/bin/python scripts/run_money_flow_research_campaign.py --config configs/strategy_validation/money_flow_research_campaign.example.json --format both`; campaign windows use candle closes in `(start, end]`, generated packs are written under `reports/strategy_validation/` by default, and the default `unique_suffix` collision policy prevents silent overwrite on duplicate run ids.
- Money Flow campaign data-readiness audit: `.venv/bin/python scripts/run_money_flow_research_campaign.py --config configs/strategy_validation/campaigns/money_flow_core_btc.json --audit-only --audit-format markdown`; audit output is read-only JSON or Markdown over persisted candle coverage and creates no evidence pack or live artifacts.
- Money Flow historical candle import: `.venv/bin/python scripts/import_strategy_validation_candles.py --input /path/to/candles.csv --environment testnet --venue hyperliquid --timeframe 15m --source-label public_dataset`; imports are duplicate-safe candle upserts only, require timezone-explicit timestamps by default, can use non-default `--assume-naive-utc` only with provenance-marked exploratory/non-canonical intent, and do not create strategy, routing, approval, or execution artifacts.
- Strategy Validation market identity seed/verify: `.venv/bin/python scripts/seed_strategy_validation_market_identity.py --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json --dry-run`; seed writes only canonical research `instruments` / `symbols` rows when not dry-run and does not create candles or live artifacts.
- Strategy Validation candle import preflight: `.venv/bin/python scripts/preflight_strategy_validation_candle_import.py --input /path/to/candles.csv --environment testnet --venue hyperliquid --timeframe 15m`; preflight writes no candles and validates file/mapping readiness before the importer is run.
- Money Flow canonical evidence review: `.venv/bin/python scripts/review_money_flow_evidence_packs.py --format markdown`; add `--db-status-only` for DB target/schema/candle readiness checks, and add `--generate-evidence-packs` to generate collision-safe packs only for campaigns whose DB target is clearly intended/non-maintenance, whose DB schema reports `migrated_schema_ready`, and whose data-readiness audit has no missing, thin, or blocked rows. The review reports sanitized DB driver/host/port/name/user, intended strategy-validation DB truth, reachability/schema/migration/candle-table status, canonical candle import requirements, can report `partial_evidence_ready_with_data_gaps`, and remains manual/descriptive only; it does not approve paper trading.
- Routing automation policy/plan/approval inspection and the narrow Phase 7.2 / 7.3 / 7.4 / 7.5 action hooks: `GET /api/v1/routing-automation/policy`, `POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}`, `POST /api/v1/routing-automation/approvals`, `GET /api/v1/routing-automation/approvals/{approval_id}`, `GET /api/v1/routing-automation/approvals/by-desired-trade/{desired_trade_key}`, `POST /api/v1/routing-automation/approvals/{approval_id}/revoke`, administrative `POST /api/v1/routing-automation/approvals/{approval_id}/consume`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness`, and action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/submit`
- Phase 8.0 operator routed workflow summary: `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}`

## Main Test Surfaces

`tests/test_config.py`
- settings defaults and hermetic env/bootstrap behavior

`tests/test_api.py`
- API startup and control-plane endpoints, including adapter/runtime session-state and private order/account-state inspection surfaces

`tests/test_phase2_services.py`
- exchange/data/state and portfolio bootstrap semantics

`tests/test_phase3_strategy.py`
- indicators, strategy evaluation, idempotency, stale-indicator rejection, and Money Flow decision paths

`tests/test_sv10_strategy_validation.py`
- SV1.0/SV1.0.1 Money Flow strategy-validation framework: verifies deterministic backtest reports over persisted candles, simulated trade generation, explicit fill-timing behavior, mark-to-market drawdown truth, expanded Markdown sections/limitations, fee/slippage impact on net PnL, no-trade reason surfacing, component/timeframe report truth, CLI request assumptions, and no live desired-trade / child-intent / readiness / submitted-order / persisted signal or decision artifacts.

`tests/test_sv11_strategy_validation_batch.py`
- SV1.1 comparative Money Flow validation: verifies batch reports across components and fill timings, deterministic JSON output, founder-readable comparison Markdown tables, per-run missing-candle limitations, no optimization/recommendation language, and no live desired-trade / routing / approval / child-intent / readiness / submitted-order / persisted signal or decision artifacts.

`tests/test_sv12_strategy_validation_regimes.py`
- SV1.2/SV1.2.1 data-coverage, market-regime, and window-truth validation: verifies complete/thin coverage diagnostics, deterministic uptrend/downtrend/sideways/unknown labels, regime-grouped trade metrics, Markdown regime/data sections, repeated CLI windows, `(start, end]` adjacent-window boundary truth, unaligned-window coverage warnings, blocked-run grouped comparison visibility, no optimization/recommendation language, and no live artifacts.

`tests/test_sv13_research_campaigns.py`
- SV1.3 research campaign/evidence-pack validation: verifies campaign config parsing, named windows to batch requests, single-run CLI `(start, end]` help wording, evidence-pack file creation, manifest metadata, window-convention visibility, adjacent-window no-double-counting, blocked-run visibility, campaign CLI help, no optimization/recommendation wording, and no live artifacts.

`tests/test_sv14_evidence_readiness.py`
- SV1.4 evidence readiness validation: verifies canonical campaign configs parse, data-readiness audit reports covered/thin/missing windows and manual-only flags, evidence packs include review checklist plus manual paper-trading readiness criteria, audit-only CLI help is truthful, and no live artifacts are created.
- SV1.4.1 evidence-pack integrity validation: verifies duplicate same-timestamp campaign runs do not overwrite the first pack, `unique_suffix` manifests record final run identity/collision truth, `fail_if_exists` raises explicitly without mutating the original pack, generated evidence packs remain excluded from review bundles, and no live artifacts are created.

`tests/test_sv15_historical_data_readiness.py`
- SV1.5 historical-data readiness validation: verifies campaign `window_convention` mismatch handling, canonical campaign audit summaries for missing/thin data, founder-readable audit Markdown, duplicate-safe offline candle import/upsert behavior, first canonical evidence-pack generation path with collision safety, research-only CLI help, and no live artifacts.

`tests/test_sv151_candle_import_integrity.py`
- SV1.5.1 candle import and campaign-config research-truth validation: verifies strict window-convention contradiction rejection, candle identity-conflict blocking without retargeting or duplicate insert, same-identity duplicate-safe upsert behavior, timeframe-duration mismatch rejection, malformed/non-finite/invalid OHLCV and trade-count rejection, all-or-nothing rollback for invalid import files, and no live artifacts.

`tests/test_sv16_evidence_review.py`
- SV1.6 first canonical evidence-review validation: verifies canonical campaign audits report insufficient data without generated packs, seeded sufficient campaigns produce evidence-pack paths in review summaries, collision-safe duplicate runs still suffix instead of overwriting, review Markdown uses manual/descriptive status language, the review CLI is research-only, audit-only review creates no packs, and no live artifacts are created.

`tests/test_sv17_evidence_review_real_data_gaps.py`
- SV1.7 first-real canonical evidence-review/data-gap validation: verifies unreachable database status is surfaced as blocked canonical campaign rows, reachable databases without `candles` are reported as schema/data gaps, mixed generated/blocked outcomes use `partial_evidence_ready_with_data_gaps`, generated packs remain collision-safe where seeded data is sufficient, no recommendation/optimization wording appears, and no live artifacts are created.

`tests/test_sv18_historical_data_bootstrap.py`
- SV1.8 historical-data bootstrap validation: verifies DB/schema/migration status reporting, status-only evidence-review output, missing Alembic/candle-table gaps, seeded sufficient evidence generation behind schema checks, no recommendation/optimization wording, and no live artifacts.

`tests/test_sv181_evidence_schema_truth.py`
- SV1.8.1 evidence schema-truth validation: verifies evidence-pack generation is blocked without current Alembic truth or required `candles` / `instruments` / `symbols` tables, partial schema gaps report cleanly, top-level live/exchange flags aggregate from campaign results, and no live artifacts are created.

`tests/test_sv19_evidence_status.py`
- SV1.9 first-real evidence status validation: verifies DB target metadata reports sanitized host/port/name/user and intended-database truth, outdated migration revisions block evidence generation, canonical missing-candle rows emit import requirements, seeded sufficient data can still generate evidence packs with current schema truth, top-level live/exchange flags remain aggregated, and no live artifacts are created.

`tests/test_sv191_evidence_target_and_import_truth.py`
- SV1.9.1 evidence-target and candle-import truth validation: verifies migrated/current maintenance DB targets still block evidence generation by default, blocked results expose DB-target reason codes and write no pack, timezone-naive imports fail by default without persisted candles, explicit `--assume-naive-utc` service override succeeds only with provenance/timestamp-assumption warnings, and no live artifacts are created.

`tests/test_sv110_evidence_db_readiness.py`
- SV1.10 intended DB/candle readiness validation: verifies intended DB target reporting, required table inspection, unique canonical import-requirement grouping, timezone-explicit import requirement guidance, insufficient/seeded canonical audit paths, artifact hygiene, and no live artifacts.

`tests/test_sv111_market_identity_preflight.py`
- SV1.11 market-identity and preflight validation: verifies offline manifest parsing, dry-run/verify-only/seed behavior for canonical BTC/ETH/SOL identity rows, conflict and Decimal guards, evidence-review identity readiness, row-level candle preflight, and no candle/evidence/live artifacts.

`tests/test_sv1111_market_identity_preflight_hardening.py`
- SV1.11.1 hardening validation: verifies unverified non-dry-run identity writes block, dry-run/verify-only still work without verification, operator-verified writes record metadata without flipping eligibility, requirement-aware preflight detects wrong windows/duplicates/missing slots/wrong identity, complete synthetic requirements pass, and no candle/evidence/live artifacts are created.

`tests/test_sv1112_market_identity_preflight_governance.py`
- SV1.11.2 governance validation: verifies the research market-identity seed rejects strategy/trading eligibility promotion without writes, successful seed remains research-only/non-trading, dry-run reports invalid eligibility truth, verify-only stays non-writing, requirement-aware preflight blocks unmapped inputs/unmapped requirements/duplicate mappings, complete one-to-one mappings can pass, review JSON selection prefers candle import requirements, and no candle/evidence/live artifacts are created.

`tests/test_phase34_mandates.py`
- mandate hierarchy bootstrap, multi-binding scoping, reusable accounts across mandates, and differing component configs

`tests/test_phase35_cleanup.py`
- deployment-era cleanup validation and repo hygiene ignores

`tests/test_phase4a_venues.py`
- multi-venue adapter wiring, capability matrices, catalog normalization, and venue maturity surfaces

`tests/test_phase401_trade_planning.py`
- desired-trade drafting, source-policy, convertibility, routing-candidates, and quote normalization

`tests/test_phase41_risk.py`
- desired-trade approval/rejection and selective child-intent preparation

`tests/test_phase411_venue_preparation.py`
- support levels, venue-native prepared-order previews, and preflight rejection reasons

`tests/test_phase42_execution_readiness.py`
- readiness outcomes above prepared child intents

`tests/test_phase43_submission.py`
- explicit submit flow and submitted-order persistence

`tests/test_phase431_submission_truth.py`
- signed/transmitted submit-body fidelity, auth/signing truth, and same-venue multi-account targeting

`tests/test_phase44_submission_lifecycle.py`
- submitted-order lifecycle truth, Hyperliquid partial-fill/open-order coexistence, and rejection propagation

`tests/test_phase45_execution_lifecycle.py`
- broader venue reconciliation, recovery recommendations, truthful cancel lifecycle, same-target retry/cancel/amend/reconcile behavior, strict client-order-id retry truth for Aster/Binance, direct live open-order retry blocking, submitted-at-bounded ambiguity-scoped Aster/Binance private fill retry blocking without plain submitted-order fill leakage, Binance fill-query-failure retry blocking, Hyperliquid nullable/derived mark-price truth, polling-first private-state truth, venue-private open-order boundary truth, runtime source truth, and same-venue multi-account targeting through private open-order/recent-fill reads

`tests/test_phase50_routing_substrate.py`
- Phase 5.0 non-executing routing assessment substrate: routing-required mandate-scoped opens produce persisted assessments, bindings are enumerated without creating target-choice records during assessment, missing-data/no-eligible cases are explicit, same-venue multi-account candidate inventory remains intact, no child intents or submitted orders are created, and public routing surfaces avoid live-routing/optimization wording.

`tests/test_phase51_routing_target_choice.py`
- Phase 5.1 non-executing routing target-choice substrate: operators can request one explicit eligible binding from a valid routing assessment, assessment/candidate id semantics stay correct, no auto-pick occurs, stale desired-trade truth plus ineligible or stale binding/account truth blocks target choice, desired trades are not mutated by target choice, and no child intents or submitted orders are created.

`tests/test_phase52_target_choice_conversion.py`
- Phase 5.2 target-choice conversion substrate plus Phase 5.2.1 lineage hardening: one explicit recorded target choice can create exactly one binding/account-targeted child intent with routing assessment / target-choice lineage, idempotent duplicate handling, stale desired-trade/binding/account/candidate mismatch blocking, assessment id/environment mismatch blocking, desired-trade ownership drift blocking, binding mandate ownership blocking, symbol-mapping drift blocking, same-venue multi-account targeting, and no prepared orders, readiness evaluations, submitted orders, fanout, scoring, CBBO, or submission.

`tests/test_phase53_routed_child_intent_readiness.py`
- Phase 5.3 routed child-intent preparation/readiness handoff plus Phase 5.3.1 hardening: converted routed child intents can use existing preview/readiness paths after route-lineage validation; stale desired-trade/binding/account/route-lineage drift, selected-target provenance drift, child-intent client/mandate drift, target-choice desired-trade drift, and routed submit attempts with the routed gate disabled block before adapter submission; same-venue multi-account routed readiness uses only the selected account; and no extra child intents, fanout, scoring, CBBO, target reselection, or auto-submit are created.

`tests/test_phase54_routed_submission_handoff.py`
- Phase 5.4 explicit routed submission handoff plus Phase 5.4.1 truth hotpatch: routed submission remains phase-blocked while either the separate routed gate or normal live gate blocks submission, phase-boundary submit attempts preserve child-intent status and record `last_submission_block`, routed preview payloads report actual routed/live gate deferral truth, enabled routed submission creates exactly one SubmittedOrder for the already selected binding/account after lineage/readiness validation, routed lineage is preserved in submitted-order raw payload, stale lineage/binding/account/symbol truth blocks before adapter submit, same-venue multi-account routed submission uses only the selected account, and API behavior stays explicit without auto-submit, fanout, CBBO, scoring, target reselection, or route executor behavior.

`tests/test_phase55_routed_submitted_order_lineage.py`
- Phase 5.5 routed submitted-order lineage inspection plus Phase 5.6 malformed-type hardening: routed submitted-order detail/list responses expose derived routed-origin lineage without raw-payload parsing, non-routed submitted orders do not fabricate routing ids, malformed routed payloads are bounded with missing-lineage and malformed-lineage facts, same-target actionability remains selected-account scoped, and inspection creates no extra child intents or submitted orders.

`tests/test_phase56_routed_order_shape_policy.py`
- Phase 5.6 / Phase 5.8 / Phase 5.8.1 / Phase 5.8.2 routed order-shape policy: target-choice conversion uses explicit policy-backed MARKET / no-limit / reduce_only=false default shape, accepts explicit MARKET/LIMIT policy input, blocks invalid or non-finite LIMIT / unsupported order types / reduce_only=true before child-intent creation, keeps malformed/non-finite LIMIT blocks from reporting `limit_price_explicit`, preserves idempotency, prevents policy mismatch from creating a second child intent, and keeps slippage / market-data-derived price guard expansion deferred.

`tests/test_phase57_routed_post_submit_lifecycle.py`
- Phase 5.7 routed post-submit lifecycle/actionability inspection plus Phase 5.7.1 hotpatch coverage: routed submitted-order detail/list/recovery/actionability responses expose read-only lifecycle context, routed same-target retry preserves routed lineage, non-routed retry/orders do not fabricate routed context, malformed routed payloads remain bounded through the shared parser, same-venue multi-account actionability uses only the selected account, and inspection creates no extra child intents or submitted orders.

`tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- Phase 5.9 routed reconciliation/lifecycle audit visibility plus Phase 5.9.1/5.9.2 namespace hotpatch coverage: routed reconciliation responses preserve and expose selected route context, existing platform `routed_submission` lineage wins over colliding update payloads, non-routed update-payload collisions cannot create platform routed lineage, lifecycle-event responses derive routed context through the shared parser, non-routed reconciliation/events do not fabricate route context, malformed routed payloads stay bounded, same-venue multi-account reconciliation context remains selected-account scoped, and audit inspection creates no extra child intents, readiness evaluations, submitted orders, fanout, scoring, allocation, target reselection, or route plans.

`tests/test_phase510_routing_substrate_closeout.py`
- Phase 5.10 final routing-substrate closeout regression: exercises the accepted routed chain from routing-required desired trade through assessment, explicit target choice, exactly-one conversion, routed preview/readiness, explicit gated routed submission, submitted-order detail/list, actionability/recovery, reconciliation with a colliding update-payload `routed_submission`, and lifecycle-event context. Verifies typed routed lineage consistency, selected-account same-venue targeting, platform-owned routed_submission namespace truth, and absence of fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, auto-submit, extra child intents, or extra submitted orders.

`tests/test_phase5101_route_readiness_audit.py`
- Phase 5.10.1 / 5.10.2 non-selecting route-readiness/data-sufficiency audit: verifies audits can be created from routing-required desired trades and existing routing assessments, persisted and fetched by id, reason-code missing/stale market data, inactive binding/account and symbol-mapping blockers, unsupported order-shape facts, economic fee/balance/private-state visibility, same-venue multi-account account-scoped facts, API inspection, quote source labels derived from existing assessment snapshots rather than fresh venue-query overclaims, desired-trade side/quantity blockers, malformed/non-finite/non-positive quote-price safety, defaulted MARKET order-shape wording, and no target choice, child intent, readiness evaluation, submitted order, fanout, scoring, CBBO, route plan, target reselection, route executor behavior, or auto-submit.

`tests/test_phase600_routing_target_recommendation.py`
- Phase 6.0.0 / 6.0.1 / 6.0.2 / 6.1 / 6.1.1 controlled non-executing target recommendation: verifies persisted recommendations can be created from route-readiness audits, default `single_ready_candidate_only` behavior remains backward-compatible, multiple ready candidates still block by default, explicit `explicit_binding_priority` can recommend exactly one lower-priority ready binding, missing priority blocks, priority ties block, malformed priority blocks, current-truth revalidation still blocks after priority selection, priority-selected stale quotes block, invalid API policy names return validation errors without persistence, malformed direct service policy names are rejected before persistence, priority clear/preserve semantics are explicit, unknown short direct-service policy attempts persist a controlled blocked record, quote observation freshness remains enforced, source audits report recommendation-created truth after a recommendation record is persisted, API create/get inspection works, and no target choice, child intent, readiness evaluation, submitted order, fanout, CBBO, rank, score, allocation, route plan, target reselection, route executor behavior, or auto-submit is created during recommendation creation.

`tests/test_phase62_recommendation_acceptance.py`
- Phase 6.2 / 6.2.1 / 6.2.2 explicit recommendation acceptance: verifies successful `single_ready_candidate_only` and `explicit_binding_priority` recommendations can be accepted into exactly one non-executing target choice, blocked or unknown recommendations cannot be accepted, blocked recommendations from an already accepted audit cannot reuse same-audit idempotency or be stamped as accepted, disabled binding and stale quote facts block new acceptance, repeated acceptance returns the existing target choice, duplicate successful recommendations from one route-readiness audit cannot create multiple target choices, original recommendation/audit acceptance timestamps remain stable after idempotent retries, recommendation/source-audit `target_choice_created` truth updates only after valid acceptance, target-choice provenance carries recommendation/audit/policy/selected-target lineage, API acceptance returns target-choice inspection, and no child intent, readiness evaluation, submitted order, fanout, CBBO, rank, score, allocation, route plan, target reselection, route executor behavior, or auto-submit is created.

`tests/test_phase63_recommendation_target_choice_conversion.py`
- Phase 6.3 explicit accepted-recommendation target-choice conversion: verifies accepted recommendation-backed target choices convert into exactly one routed child `OrderIntent`, conversion response and child-intent provenance expose recommendation/audit/target-choice/selected-target/order-shape lineage, repeated conversion returns the existing child intent, duplicate same-audit target-choice paths cannot create multiple child intents, blocked recommendation-backed target choices cannot be laundered into conversion, disabled binding/account, inactive/non-trading symbol mapping, and stale quote facts block new conversion, explicit positive finite LIMIT policy succeeds, invalid LIMIT policy blocks before child-intent creation, `explicit_binding_priority` recommendations can convert after acceptance, API conversion exposes recommendation lineage, and no prepared order, readiness assessment, submitted order, fanout, CBBO, rank, score, route plan, target reselection, route executor behavior, or auto-submit is created.

`tests/test_phase64_recommendation_backed_readiness.py`
- Phase 6.4 / 6.4.1 recommendation-backed child-intent preview/readiness inspection: verifies accepted recommendation-backed child intents use existing prepared-order preview and submission-readiness paths, preview/readiness API responses expose recommendation/audit/target-choice/selected-target/order-shape lineage, disabled binding/account and inactive/non-trading symbol truth block before adapter preparation, stale stored quote observations block readiness with `quote_stale_at_readiness`, stored routed order-shape policy drift for order_type / LIMIT price / reduce_only blocks before adapter preparation, missing policy blocks, explicit positive finite LIMIT policy remains visible through readiness, and no submitted order, exchange submit call, route executor behavior, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit is created.

`tests/test_phase65_manual_routed_flow.py`
- Phase 6.5 / 6.6 manual routed-flow harness coverage: verifies the internal JSON harness can run from an existing routing-required desired trade through readiness inspection using existing services, output key artifact ids/statuses/reason codes/routed lineage, include local top-level `timing_ms` and per-step `elapsed_ms` for executed steps, omit skipped-step timing rather than fabricating zero work, skip submission by default, create no `SubmittedOrder` by default, and block `--submit` without the danger-confirmation flag before service submission while recording local submission-block timing.

`tests/test_phase67_recommendation_backed_submission.py`
- Phase 6.7 / 6.10.1 / 6.10.2 / 6.10.3 explicit recommendation-backed submitted-order handoff: verifies a recommendation-backed child intent submits only through the existing explicit gated submit path when live and routed gates pass, serializes concurrent explicit submit attempts with the submission lease before adapter submission, writes terminal `adapter_submit_may_have_started` before adapter submission can begin, preserves post-adapter/pre-persistence uncertainty as terminal `adapter_submit_persistence_unknown`, blocks later submits for that intent before adapter submission even after TTL, keeps stale pre-adapter active leases replaceable, blocks before adapter submit when gates, quote truth, recommendation lineage, or routed order-shape policy drift fail, creates exactly one SubmittedOrder, exposes recommendation/audit/target-choice/intent/readiness lineage, preserves first submitted-order provenance across same-target retry, and still adds no fanout, allocation, scoring, CBBO, target reselection, route executor behavior, or auto-submit.

`tests/test_phase68_recommendation_backed_lifecycle.py`
- Phase 6.8 recommendation-backed post-submit lifecycle inspection: verifies submitted-order detail/list/actionability/recovery/reconciliation/lifecycle-event surfaces expose recommendation-aware routed lifecycle context, reconciliation cannot overwrite platform-owned recommendation lineage, non-routed orders cannot fabricate recommendation lineage from update payload collisions, and same-target retry preserves recommendation/audit/target-choice lineage without alternate binding or venue recovery.

`tests/test_phase69_routed_workflow_inspection.py`
- Phase 6.9 / 6.10.1 read-only routed workflow inspection API: verifies `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}` aggregates full and partial routed chains without creating artifacts, distinguishes unknown desired trades cleanly, exposes consistent routed lineage, artifact counts, and a truthful `same_target_lifecycle_summary`, and never submits or advances workflow state.

`tests/test_phase70_routing_automation.py`
- Phase 7.0 controlled automation substrate: verifies default disabled policy, dry-run-only plans, approval-required plans, explicit same-target automation eligibility, blocked-recommendation behavior, API policy/plan surfaces, lineage preservation, no dry-run mutation, and absence of smart routing, fanout, ranking/scoring, CBBO, target reselection, route executor behavior, or auto-submit.

`tests/test_phase71_routing_automation_approvals.py`
- Phase 7.1 / 7.1.1 / 7.1.2 operator approval and reversible gating substrate: verifies approval creation, routed lineage and policy snapshot preservation, approval inspection by desired trade, expiry replacement, stale-lineage replacement, active-scope idempotency/uniqueness, rejection of dry-run-only and manual-only approvals, gate-state truth for non-approvable current steps, revocation, consumed approvals not being reusable, blocked recommendations not receiving approval, API create/inspect/revoke surfaces, continued dry-run non-execution, and no target choice, child intent, readiness, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects.

`tests/test_phase72_approval_gated_recommendation_acceptance.py`
- Phase 7.2 / 7.2.1 approval-gated recommendation acceptance action hook: verifies a valid current recommendation-acceptance approval can create/reuse exactly one target choice and be consumed, repeated calls are idempotent, a forced failure between target-choice flush and approval consumption rolls back without misleading state, generic approval consumption is administrative only, expired/revoked/wrong-action/wrong-recommendation/consumed-for-different-recommendation approvals block, dry-run-only/manual-only policies cannot execute, API response exposes consumed approval plus target choice, and no child intent, readiness evaluation, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase73_approval_gated_target_choice_conversion.py`
- Phase 7.3 approval-gated target-choice conversion action hook plus Phase 7.3.1 negative-test hardening: verifies a valid current target-choice-conversion approval can create/reuse exactly one child intent and be consumed, repeated calls are idempotent, a forced failure between child-intent flush and approval consumption rolls back without misleading state, expired/revoked/wrong-action/wrong-target-choice/stale-lineage/consumed-for-different-target-choice approvals block, dry-run-only/manual-only policies cannot execute, disabled/blocked/deferred/already-satisfied current step states reject conversion directly, wrong recommendation / route-readiness audit / desired-trade lineage rejects without consuming approval, API response exposes consumed approval plus child intent, Obsidian workflow requirements are operational-test-covered, and no prepared order, readiness evaluation, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase74_approval_gated_preview_readiness.py`
- Phase 7.4 approval-gated preview/readiness action hook: verifies a valid current `prepared_order_preview_and_readiness` approval can run existing child-intent preview/readiness, persist or reuse exactly one readiness assessment, and be consumed; repeated calls are idempotent; forced approval-consumption failure rolls back readiness persistence; expired/revoked/wrong-action/stale-lineage/consumed-for-different-child approvals block; disabled/blocked/deferred/already-satisfied/dry-run-only/manual-only step states reject action; blocked readiness remains reason-coded; API response exposes consumed approval plus preview/readiness; and no submitted order, adapter submit call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase75_approval_gated_submission_handoff.py`
- Phase 7.5 / 7.5.1 approval-gated submitted-order handoff action hook: verifies a valid current `submitted_order_handoff` approval submits exactly one already-ready routed child intent through the existing explicit submit path, consumes approval only after submitted-order persistence or safe reuse, preserves idempotency, keeps live/routed submit gates and readiness blockers authoritative, rejects expired/revoked/wrong-action/wrong-lineage/consumed-for-different-child approvals and non-executable current step states, preserves submit lease/concurrency/uncertainty behavior, records `consumption_pending` if approval consumption fails after submitted-order persistence, retries that pending approval by reusing the existing submitted order without another adapter submit, exposes API response truth, and adds no extra child intents, fanout, ranking/scoring, CBBO, target reselection, route executor behavior, cross-venue retry, or broad auto-submit.

`tests/test_phase76_automation_closeout.py`
- Phase 7.6 controlled automation closeout safety proof: walks the full approval-gated chain from existing recommendation through recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff; verifies each stage consumes only the exact current-lineage approval and creates/reuses only its expected artifact; proves dry-run, approval creation, generic administrative consume, action-specific consume, readiness, and submitted-order handoff remain distinct; proves stale-lineage and cross-stage approvals cannot authorize actions; proves `consumption_pending` is bounded and repeat calls reuse the existing submitted order without another adapter submit; and asserts no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, split allocation, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit.

`tests/test_phase80_operator_observability.py`
- Phase 8.0 / 8.0.2 operator observability/manual-resolution inspection: verifies the read-only operator routed workflow summary returns the full Phase 7 chain without mutation, exposes approval states and gate truth, surfaces `consumption_pending`, adapter-submit uncertainty, active `submission_in_progress` leases, blocked recommendation/readiness, stale-lineage approvals, submitted-order handoff safety, submit lease/concurrency state, next safe operator action, and no-SOR/no-fanout/no-reselection/no-route-executor boundary flags without creating artifacts, consuming approvals, resolving manual states, calling exchange adapters, or submitting orders.

`tests/test_phase610_phase6_closeout.py`
- Phase 6.10 Phase 6 closeout regression: exercises the complete accepted explicit recommendation-backed single-target path through submitted order, detail/list, actionability/recovery, reconciliation collision protection, lifecycle events, and read-only workflow inspection while proving exactly one target choice, one child intent, and one submitted order with no fanout, allocation, scoring, CBBO, target reselection, route executor behavior, auto-submit, cross-binding recovery, or cross-venue retry.

`tests/conftest.py`
- pytest bootstrap isolation from local `.env` and developer-machine env contamination

`tests/test_operational_docs.py`
- operational-doc existence/reference validation plus review-bundle hygiene validation against an actually produced ZIP
