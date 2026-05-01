# Money Flow

Production-minded scaffold for a modular multi-strategy trading platform targeting Hyperliquid first, with multi-venue hardening underway. The repository now includes architecture, domain contracts, configuration, persistence, API, exchange/data/state sync foundations, deterministic indicators, the first strategy family, hardening around instrument identity and idempotent strategy evaluation, a first-class `Client -> VenueAccount -> StrategyMandate -> MandateAccountBinding -> StrategyComponentConfig` hierarchy, multi-venue adapters for Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken, a refined planning boundary between strategy decisions, mandate-level desired trades, routing-required assessment, route-readiness/data-sufficiency audit, controlled non-executing target recommendation, explicit recommendation acceptance into a non-executing target choice, controlled target-choice conversion, binding-targeted child intents, routed child-intent preparation/readiness inspection, explicit routed submission handoff, routed post-submit lifecycle/actionability inspection, routed reconciliation/lifecycle audit visibility, and explicit routed order-shape policy input, the first real desired-trade approval layer, venue-native prepared-order preview/preflight surfaces for the current venue set, a persisted execution-readiness gate above prepared child intents, and code/test-proven account-targeted submit paths for the currently implemented venue/product scopes. The platform already generates inspectable strategy decisions, evaluates them into approved/rejected or routing-required desired trades, can create non-executing routing assessments that enumerate eligible and ineligible mandate-account bindings, can create non-selecting route-readiness audits that expose whether current facts are sufficient for recommendation-readiness without recommending or ranking, can create a persisted non-executing `RoutingTargetRecommendation` under the default `single_ready_candidate_only` policy or the explicit `explicit_binding_priority` operator-preference policy while rechecking current mandate/desired-trade/binding/account/symbol/quote freshness truth, can explicitly accept a successful recommendation into exactly one non-executing `RoutingTargetChoice` after revalidating current truth again, can record one operator-requested non-executing target choice from a valid assessment and still-valid source desired trade, can convert one explicit valid target choice or one accepted recommendation-backed target choice into exactly one binding/account-targeted child intent using default MARKET shape or explicit MARKET/LIMIT order-shape policy, can let that converted child intent enter the existing prepared-order preview and readiness inspection paths after route-origin lineage is revalidated, can submit that same selected routed child intent only through an explicit submit action when both the normal live-submission gate and the routed-submission phase gate are enabled and a narrow submit lease is acquired before adapter submission, and can inspect routed submitted-order lifecycle/actionability/reconciliation-event context without parsing raw payload manually. Phase 5.8 keeps routed behavior narrow: LIMIT is an explicit conversion-time order-shape policy input requiring a positive finite limit price and modeled support, not target selection or price discovery; Phase 5.9 exposes routed context on reconciliation and lifecycle-event responses while reconciliation remains venue/account truth; Phase 5.10 closes Phase 5 with end-to-end regression coverage proving the routed lifecycle surfaces remain consistent, bounded, selected-account scoped, and non-routing; Phase 5.10.1 adds route-readiness/data-sufficiency audit as the gate Phase 6 recommendation must satisfy; Phase 5.10.2 hotpatches that audit so quote data-source labels describe the audit runtime path, desired-trade side/quantity validity blocks recommendation-readiness, malformed or non-finite quote prices block without crashing, and default MARKET order shape is labeled defaulted rather than explicit; Phase 6.0.x adds controlled recommendation only for exactly one ready candidate by default, rechecks current truth and quote freshness, and flips the source audit's `recommendation_created` truth when a recommendation record is persisted; Phase 6.1 adds optional deterministic `explicit_binding_priority`, using nullable binding-level `target_recommendation_priority` where lower positive integers win, missing/malformed priorities block, ties block, and no price, fee, venue-quality, liquidity, CBBO, rank, or score selection occurs; Phase 6.1.1 bounds recommendation `policy_name` input to the accepted policies, makes priority clearing explicit with `clear_target_recommendation_priority`, and verifies priority-selected candidates still block on stale quote observations; Phase 6.2 adds explicit operator-triggered recommendation acceptance into target choice only, with current-truth and quote-freshness revalidation; Phase 6.2.1 hardens acceptance idempotency so one route-readiness audit cannot produce multiple accepted target choices, duplicate same-audit recommendations return the original target choice, and the original recommendation/audit acceptance timestamp remains stable while idempotent checks are recorded separately; Phase 6.2.2 tightens that idempotency so only otherwise successful recommendations can reuse an existing same-audit target choice, while blocked recommendations remain unaccepted and `target_choice_created=false`; Phase 6.3 adds explicit operator-triggered conversion from an accepted recommendation-backed target choice to exactly one routed child `OrderIntent`, preserving recommendation/audit/target-choice lineage, revalidating current truth before new child-intent creation, and reusing an existing child intent for repeated or same-audit duplicate conversion attempts; Phase 6.4 lets recommendation-backed child intents use the existing prepared-order preview and submission-readiness inspection endpoints, exposes recommendation/audit/target-choice/order-shape lineage as routed lineage in those responses, revalidates current mandate/binding/account/symbol and stored quote-observation truth before eligible readiness, and creates no `SubmittedOrder` by inspection; Phase 6.4.1 blocks preview/readiness if the current child intent order_type, limit_price, or reduce_only drifts away from its stored routed order-shape policy and reports stale quote observations at this surface with `quote_stale_at_readiness`; Phase 6.5 adds the manual routed-flow inspection harness; Phase 6.6 adds local per-step timing visibility to that harness so operators can see service/harness latency without adding production telemetry or routing behavior; Phase 6.7 through Phase 6.10 close Phase 6 by proving explicit recommendation-backed single-target routed execution through the existing gated submit path, preserving recommendation/audit/target-choice/intent/readiness lineage on `SubmittedOrder`, exposing recommendation-aware post-submit lifecycle/reconciliation context, adding a read-only routed workflow inspection API, and freezing end-to-end regression coverage. Phase 6.10.1 serializes concurrent explicit child-intent submit calls with `order_intent_submission_leases` before adapter submission, preserves first submitted-order provenance while exposing latest/retry submitted-order ids separately, and renames the routed workflow static lineage summary to `same_target_lifecycle_summary` so it is not mislabeled as actionability or recovery evaluation. Phase 6.10.2 preserves post-adapter uncertainty: if adapter submit returns but local `SubmittedOrder` persistence fails, the lease is set to `adapter_submit_persistence_unknown` and later submit attempts block with manual reconciliation required rather than becoming TTL-replaceable. Recovery/actionability context remains route-aware but same-target, same-account, and same-venue only; same-target retry of a routed submitted order preserves the existing routed lineage on the retried `SubmittedOrder`; no routed auto-submit, fanout, scoring, CBBO, target reselection, venue ranking, route executor, cross-binding/cross-venue recovery, smart routing, automatic conversion, prepared-order auto-creation, readiness auto-creation, or submitted-order creation directly from recommendation/acceptance/conversion/readiness exists. Non-routed binding-scoped child intents continue through the existing explicit submission path only when a live-submission action is invoked, all enablement/readiness checks pass, the venue-local auth/signing path is real for that scope, the signed request representation matches the transmitted request representation for the claimed submit paths, and the child intent already targets a real `VenueAccount`.

For a non-technical explanation of what Money Flow is today and where it is going next, start with [Money Flow For Investors](docs/investors.md).

At current head, public execution capability/status surfaces report cancel and amend separately. Native amend is currently code/test-proven only for Hyperliquid perpetual limit orders, current scoped OKX limit-order paths, Coinbase Advanced Trade spot limit orders, and Kraken spot limit orders; Aster and Binance expose truthful cancel support without implying amend support. Persisted fill evidence now updates lifecycle quantities without rewriting canceled, expired, or cancel-pending submitted orders into misleading generic partial-fill state. Private order/account-state truth is now deeper and explicitly polling-first: adapter/runtime session state, private-state summary, venue-private open-order visibility, recent-fill visibility, and open-position inspection are exposed without pretending adapter-level user-stream parity where it has not actually been implemented.

Phase 6.10.3 seals the explicit submit adapter-in-flight uncertainty gap. After readiness, live, and routed gates pass and the child-intent submit lease is acquired, the execution service writes terminal `adapter_submit_may_have_started` before calling `adapter.submit_order()`. Transport failures, timeouts, unknown adapter exceptions, or crashes after that point block later submits for that child intent with manual reconciliation required; `adapter_submit_persistence_unknown` still covers the separate adapter-returned/local-persistence-failed case. Stale pre-adapter `active` leases remain replaceable. The lease is a serialization and uncertainty guard only, not a `SubmittedOrder` reservation; `SubmittedOrder` remains post-submit exchange/account truth.

Phase 7.0 adds the first controlled automation substrate above the accepted single-target recommendation-backed path. It introduces explicit automation modes (`disabled`, `dry_run_only`, `approval_required`, and `explicit_automation_permitted`), a kill-switch-default policy inspection surface, and a dry-run automation plan API that reads the existing routed workflow and classifies each bounded same-target step as already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked. The plan preserves recommendation/audit/target-choice/child-intent/readiness/submitted-order lineage and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit boundary flags. Phase 7.0 creates no target choice, child intent, readiness evaluation, submitted order, exchange call, route executor, ranking, scoring, CBBO, fanout, target reselection, or auto-submit behavior.

Phase 7.1 adds the durable operator approval and reversible action-gating substrate above Phase 7.0 plans. Operators can create one approval record for a specific same-target action stage, inspect approval state by desired trade, revoke an unused approval, or mark an approval consumed for a future action hook. Approval records preserve policy snapshots, routed lineage, selected binding/account/venue/symbol facts, and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit boundary truth. Approval is not execution: creating, revoking, inspecting, or consuming an approval does not accept a recommendation, convert a target choice, create readiness, submit an order, call an exchange, or advance workflow state.

Phase 7.1.1 hardens approval truth before any action-taking automation exists. Approval reuse is now scoped to the current desired-trade/action/lineage fingerprint, including recommendation, audit, target choice, child intent, readiness/submitted-order ids where present, and selected binding/account/venue/symbol facts. Expired approvals are marked expired before create/inspection can reuse them, stale-lineage approvals are marked `stale_lineage` and stop authorizing the current gate, and a narrow active-scope uniqueness guard prevents duplicate active approvals for the same current action scope. This still executes no action and adds no smart routing, route executor, fanout, target reselection, ranking/scoring, CBBO, or auto-submit.

Phase 7.1.2 closes the remaining approval-truth gap before action hooks exist. Approval creation is allowed only for current steps that are truly `approval_required` or explicitly `automation_eligible`; `dry_run_only`, `manual_only`, `disabled`, `deferred`, `blocked`, and `already_satisfied` steps cannot receive active approvals. Gate-state inspection now keeps the current step policy authoritative, so a stored approval record is never surfaced as plain `approved` when the current plan says the step is manual-only or dry-run-only. This is still approval truth only and executes no action.

Phase 7.2 adds the first narrow approval-consuming action hook. `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation` consumes one active, non-expired, current-lineage `recommendation_acceptance` approval to accept the exact approved `RoutingTargetRecommendation` into a created or reused `RoutingTargetChoice` through the existing Phase 6.2 acceptance logic. Consumption records who used the approval, the target choice id, and explicit no-child-intent/no-readiness/no-submission facts. It does not convert the target choice, create child intents, preview/readiness, submit, call exchanges, rank/score, use CBBO, fan out, reselect targets, create a route executor, or auto-submit.

Phase 7.2.1 hardens that first action hook so target-choice creation/reuse and approval consumption are transactionally coherent. The approval-gated recommendation-acceptance path validates the current approval, creates or reuses the target choice, marks recommendation/audit target-choice truth, and consumes the approval in one session/commit. If approval consumption fails after target-choice persistence is flushed but before commit, the whole action rolls back instead of leaving a target choice with a misleading active approval. The generic approval consume endpoint remains administrative only: it marks approval state and does not execute recommendation acceptance or any downstream action.

Phase 7.3 adds the second narrow approval-consuming action hook and integrates the Obsidian brain workflow. `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice` consumes one active, non-expired, current-lineage `target_choice_conversion` approval to convert the exact approved `RoutingTargetChoice` into a created or reused child `OrderIntent` through the existing conversion validation and persistence helpers. Consumption records who used the approval, the child intent id, routed order-shape policy facts, and explicit no-prepared-order/no-readiness/no-submission facts. It does not create prepared orders, readiness assessments, submitted orders, exchange calls, route executor behavior, ranking/scoring, CBBO, fanout, target reselection, or auto-submit. The Obsidian vault under `money-flow/` is now the strategic-memory and cross-agent coordination layer; repo operational docs remain implemented-code truth.

Phase 7.4 adds the third narrow approval-consuming action hook. `POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness` consumes one active, non-expired, current-lineage `prepared_order_preview_and_readiness` approval to run the existing prepared-order preview and execution-readiness inspection path for the exact approved routed child `OrderIntent`. It persists or reuses the readiness assessment, records the preview key, readiness id/outcome/reason codes, and consumes the approval only after inspection succeeds. Approval lets the inspection run; it does not force readiness to become eligible. Blocked, phase-blocked, stale-lineage, dry-run-only, manual-only, disabled, deferred, already-satisfied, wrong-action, wrong-child-intent, expired, revoked, or consumed-for-different-child cases remain reason-coded. Phase 7.4 creates no `SubmittedOrder`, calls no adapter submit path or exchange submit endpoint, and adds no route executor, smart routing, ranking/scoring, CBBO, fanout, target reselection, or auto-submit.

Phase 7.5 adds the fourth narrow approval-consuming action hook. `POST /api/v1/routing-automation/approvals/{approval_id}/submit` consumes one active, non-expired, current-lineage `submitted_order_handoff` approval to submit the exact approved routed child `OrderIntent` through the existing explicit child-intent submit path only after the current readiness, live-submit gate, routed-submit gate, adapter/account authorization, lineage drift checks, and submit lease/uncertainty guards still pass. The approval is consumed only after a `SubmittedOrder` is persisted or safely reused, and the approval provenance records the submitted order id plus explicit no-route-executor/no-fanout/no-ranking/no-CBBO/no-target-reselection/no-broad-auto-submit truth. If readiness or submit gates block, approval does not force submission. If adapter-submit uncertainty occurs, existing manual-reconciliation-required lease truth remains authoritative and the approval is not misleadingly consumed. Phase 7.5 selects no new target, creates no extra child intent, does not fan out, does not retry elsewhere, and adds no smart routing, best-binding selection, route executor behavior, or broad auto-submit.

Phase 7.5.1 hardens approval-consumption truth after a successful submitted-order handoff. If the existing submit path persists or reuses a `SubmittedOrder` but approval consumption fails afterward, the approval is moved into `consumption_pending` with submitted order id, child intent id, failure reason codes, and `manual_approval_reconciliation_required` provenance instead of remaining clean-active. A repeat call with the same approval reuses the existing submitted order and attempts to finish approval consumption without calling adapter submit again. This is approval truth only; it adds no new action hook, route executor, target reselection, fanout, retry behavior, or broad auto-submit.

Phase 7.6 closes controlled automation with safety-diligence regression instead of new behavior. The closeout test walks the full approval-gated chain from recommendation acceptance through target-choice conversion, preview/readiness, and submitted-order handoff, proving each action consumes only its exact current-lineage approval, dry-run and administrative consume stay non-executing, `consumption_pending` remains bounded and inspectable, and no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit appears.

Phase 8.0 adds the first operator-grade observability and manual-resolution inspection layer. `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}` is read-only and aggregates the existing routed workflow, approval states, gate truth, manual-resolution requirements, submitted-order handoff safety facts, and submit lease/concurrency state. It surfaces `consumption_pending`, stale-lineage/expired approvals, blocked recommendations/readiness, `adapter_submit_may_have_started`, `adapter_submit_persistence_unknown`, repeat-submit policy, and the next safe operator action without creating artifacts, consuming approvals, resolving manual states, submitting/canceling/amending/retrying, selecting/reselecting targets, ranking/scoring, using CBBO, fanning out, or introducing route executor behavior.

Phase 8.0.2 hotpatches operator-summary truth for active submit leases. If an unexpired `active` child-intent submit lease exists, the read-only operator summary reports `submission_in_progress`, blocks repeat-submit safety with `repeat_submit_policy=blocked_while_submission_in_progress`, and reports `next_safe_operator_action.action=submission_in_progress` with `safe_to_automate=false`. Terminal uncertainty states remain manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and no trading behavior, new automation action stage, manual-resolution mutation, route executor behavior, fanout, target reselection, ranking/scoring, CBBO, cross-venue retry, or auto-submit is added. Phase 8.1 remains deferred; Strategy Validation can begin after this hotfix is accepted.

## Operational Memory

This repo now uses explicit operational-memory files plus an Obsidian strategic brain. Future work is expected to read them before changes and update them after changes.

Machine-local artifacts such as `.git/`, `.venv/`, `.pgdata/`, `.pgsocket/`, `.pytest_cache/`, `.DS_Store`, and Obsidian app state under `money-flow/.obsidian/` are not part of the repo handoff surface. Review/archive packaging now uses `.archiveignore` plus the committed bundling command below so those local artifacts and `.env` do not leak into future review bundles. The tracked Obsidian markdown notes under `money-flow/` are part of the review surface.

## Source Control Baseline

The source-control baseline is on `master`. Source, tests, migrations, docs, operational memory, `.gitignore`, and `.env.example` are tracked; `.env`, virtualenvs, caches, local database/runtime state, logs, review ZIPs, and handoff archives are intentionally ignored. Future phase work should use short-lived branches off `master` and keep review bundles outside source control.

Review bundle command:

```bash
.venv/bin/python scripts/create_review_bundle.py --output /tmp/money-flow-review.zip
```

## Manual Routed-Flow Inspection

Phase 6.5 adds an internal developer/operator harness for manually exercising the existing controlled routed chain without adding smart routing or automation:

```bash
.venv/bin/python scripts/manual_routed_flow.py --desired-trade-key <desired_trade_key> --run-through-readiness
```

The harness emits JSON by default. It starts from an existing desired trade key, can explicitly create or inspect the current routing assessment, route-readiness audit, routing target recommendation, recommendation acceptance, target-choice conversion, prepared-order preview, and execution-readiness assessment, and prints artifact ids, statuses, reason codes, selected binding/account/venue/symbol facts, routed lineage, no-fanout/no-allocation/no-ranking/no-scoring/no-CBBO/no-route-executor/no-auto-submit boundary flags, and Phase 6.6 local timing fields. Default invocation only inspects the desired trade and skips submission; `--run-through-readiness` stops after readiness inspection and still creates no `SubmittedOrder`.

Phase 6.6 timing is local harness timing only. Output includes top-level `timing_ms` values, including `total`, and each executed step includes `elapsed_ms`. Skipped steps are omitted from `timing_ms` rather than represented as fake zero-latency work. These timings measure local harness/service-call overhead and are not production routing latency, route-executor telemetry, or exchange/network latency unless an operator explicitly triggers a live submit path.

Submission is intentionally hard to trigger from the harness. A submit attempt requires both `--submit` and `--i-understand-this-can-place-a-live-order`, and even then the existing execution service readiness, live-submit, routed-submit, adapter, and account gates still decide the outcome. Without the danger-confirmation flag, the harness blocks locally with `manual_submission_confirmation_required` before service submission is called and records timing for that local block. This is manual inspection tooling only, not best-binding selection, smart routing, a route executor, target reselection, fanout, ranking/scoring, CBBO, or auto-submit.

## Routing Automation Planning

Phase 7.0 exposes non-executing automation policy and dry-run planning:

```bash
GET /api/v1/routing-automation/policy
POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}
POST /api/v1/routing-automation/approvals
GET /api/v1/routing-automation/approvals/{approval_id}
GET /api/v1/routing-automation/approvals/by-desired-trade/{desired_trade_key}
POST /api/v1/routing-automation/approvals/{approval_id}/revoke
POST /api/v1/routing-automation/approvals/{approval_id}/consume
POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation
POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice
POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness
POST /api/v1/routing-automation/approvals/{approval_id}/submit
```

The default policy is `disabled`. A plan request can supply an explicit policy mode, but automation planning still only reports what would be disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, blocked, approved, revoked, consumed, or expired. Approval records are durable gates for later explicit same-target action hooks; they are not the action itself and do not submit.

Phase 7.1.1 makes those gate states current-truth-bound: an approval is shown as approved only when its active record has not expired and its lineage fingerprint still matches the current routed workflow stage. Stale approvals remain inspectable as history but are not reusable as current approval truth. Phase 7.1.2 also keeps current policy truth above stored approval metadata: manual-only and dry-run-only steps remain `manual_only` or `dry_run_only` in gate-state output and cannot be converted into active approvals.

Phase 7.2 connects approval to exactly one action stage: recommendation acceptance. Phase 7.2.1 makes that action coherent in one transaction: approval validation, target-choice creation/reuse, recommendation/audit target-choice truth, and approval consumption commit together or roll back together. Phase 7.3 connects approval to the next action stage only: target-choice conversion into one child intent. The conversion hook requires a valid current `target_choice_conversion` approval, reuses the existing target-choice conversion validation/persistence helpers, preserves order-shape policy provenance, and consumes the approval only after child-intent creation/reuse succeeds. Phase 7.4 connects approval to prepared-order preview and execution-readiness inspection only. The preview/readiness hook requires a valid current `prepared_order_preview_and_readiness` approval, reuses the existing child-intent preview/readiness path, persists or reuses the readiness assessment, consumes the approval only after inspection succeeds, and never submits. Phase 7.5 connects approval to submitted-order handoff only. The submit hook requires a valid current `submitted_order_handoff` approval and still reuses the existing explicit submit path, current readiness, live/routed submit gates, and submit lease/uncertainty handling before one `SubmittedOrder` can be persisted or reused. Phase 7.5.1 adds `consumption_pending` approval truth for the narrow case where submitted-order persistence succeeds but approval consumption fails, and repeat calls reuse the existing submitted order before completing or preserving bounded approval reconciliation truth. Phase 7.6 closes the controlled automation chain with end-to-end safety assertions and no new action stage. Phase 8.0 adds read-only operator summary inspection over that chain so an operator can see workflow state, approval/gate state, manual-resolution requirements, submitted-order safety facts, submit leases, and next safe operator action without executing or resolving anything. Consumed approvals expose the artifact they authorized, while dry-run-only/manual-only policy states, revoked/expired/stale-lineage approvals, wrong actions, wrong target choices/child intents/readiness, wrong lineages, blocked readiness, submit-gate blocks, and uncertainty states block or remain reason-coded before action completion. Generic approval consumption is administrative state marking only, not action execution.

Required operational docs:

- [AGENTS.md](AGENTS.md)
- [CHANGELOG.md](CHANGELOG.md)
- [REPO_TREE.md](REPO_TREE.md)
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
- [TODO.md](TODO.md)

Required Obsidian strategic brain:

- [money-flow/00_Money_Flow_Command_Center.md](money-flow/00_Money_Flow_Command_Center.md)
- [money-flow/01_Current_Phase.md](money-flow/01_Current_Phase.md)
- [money-flow/05_Agent_Coordination.md](money-flow/05_Agent_Coordination.md)
- [money-flow/Project_Memory/money_flow_project_memory.md](money-flow/Project_Memory/money_flow_project_memory.md)

The repo-root [money_flow_project_memory.md](money_flow_project_memory.md) is a pointer only. Repo operational docs remain code-state truth; Obsidian stores long-horizon memory, founder intent, decisions, phase context, and cross-agent coordination.

## Current Scope

Implemented through Phase 2.1:

- clean package structure for apps, services, core, db, infra, docs, and tests
- typed domain models, API schemas, and service interfaces
- environment-aware Pydantic settings and family/component configuration model
- SQLAlchemy models and Alembic migrations for canonical instruments, venue mappings, reconciliation state, and candle checkpoints
- FastAPI control-plane endpoints for exchange status, universe sync, candle sync, health, and bootstrap inspection
- Hyperliquid adapter foundation for universe sync, account sync, orders/fills/positions reconciliation, and candle bootstrap
- explicit normalized instrument mapping and venue capability boundaries
- deterministic market-data checkpoint semantics with overlap-safe re-fetching
- shared-account truth separated from future strategy-attribution overlays
- structured logging, Docker setup, and local developer bootstrap files
- architecture documentation and Mermaid diagrams

Implemented in Phase 3:

- deterministic indicator computation over persisted candles
- indicator snapshot persistence keyed by environment, venue, instrument reference, timeframe, and `as_of`
- modular strategy family framework
- Money Flow as the first strategy family
- three independent Money Flow sleeves for `15m`, `1h`, and `4h`
- persisted signal events and strategy decisions, including no-trade and invalid-state outcomes
- operator inspection endpoints for indicators, signals, decisions, and strategy status

Implemented in Phase 3.1:

- explicit canonical `instrument_key` vs database `instrument_ref_id` semantics
- venue-safe indicator lookup semantics aligned with the active market-data venue
- stale-indicator rejection when snapshots lag the latest persisted candle close
- idempotent strategy evaluation keyed to evaluated state instead of UUID-only outputs
- Money Flow exit-oriented decisions: `hold`, `reduce`, and `close` in addition to entry/no-trade/invalid
- account-scoped open-order bootstrap semantics distinct from recent submitted order history
- builder-deployed / HIP-3 assets cataloged by default while remaining strategy-ineligible and trading-ineligible by default
- decision provenance fields for config and evaluated-state inspection

Implemented in Phase 3.2:

- canonical repo changelog and operational-memory docs
- explicit read-before-work / log-after-work workflow in `AGENTS.md`
- lightweight validation to ensure required operational docs exist and remain referenced correctly

Implemented in Phase 3.3:

- first-class `Client` and `VenueAccount` modeling replaced the old single-account runtime assumption
- the repo gained its first explicit account/deployment hierarchy before that top-level strategy object was refined further in Phase 3.4

Implemented in Phase 3.4:

- `StrategyMandate` replaces `StrategyDeployment` as the top-level strategy umbrella
- `MandateAccountBinding` replaces the old one-account deployment relationship as the per-account participation object
- `StrategyComponentConfig` replaces the overly narrow sleeve-deployment config naming
- one mandate can bind many venue accounts, and one venue account can be reused across many mandates
- runtime selection now targets one active mandate per process, with one optional focused account only for bootstrap and inspection convenience
- strategy and portfolio services now resolve the active mandate plus all bound accounts instead of assuming one account is the whole runtime
- existing 3.3 deployment data is backfilled conservatively into one mandate plus one binding per prior deployment
- binding membership and policy are explicit, but no static routing weights are introduced

Implemented in Phase 3.5:

- legacy `StrategyDeployment` and `SleeveDeploymentConfig` baggage is removed from the active runtime and active schema at head
- runtime selection is mandate-first without a deployment-key fallback
- one client can own many mandates, and one venue account can participate in many mandates through bindings
- docs, tests, and terminology are aligned around mandate / binding / component instead of teaching the older deployment-top model
- the platform is described explicitly as signal generation plus future routing/execution preparation, not as a single-account signal bot

Implemented in Phase 4A:

- shared exchange abstractions widened so the platform is no longer silently Hyperliquid-shaped
- first-class adapters for:
  - Hyperliquid
  - Aster
  - OKX
  - Coinbase Advanced Trade
- explicit venue capability matrix covering product support, market-data support, account-sync support, demo/sandbox support, and account-model differences
- venue-safe symbol catalog handling for mixed-product venues such as OKX spot plus perpetual listings
- control-plane QA endpoints for:
  - supported venues
  - per-venue status
  - per-venue capabilities
  - per-venue instruments and symbols
  - per-venue account connectivity
  - per-venue market-data inspection
- conservative integration stance:
  - Hyperliquid remains the most mature integration
  - no live order submission is implemented for any venue in Phase 4A

Implemented in Phase 4.0.1:

- first-class `MandateDesiredTrade` model and persistence for mandate-level desired action above any future account-targeted child intent
- first-class `BindingRoutingCandidate` plus normalized venue/binding quote snapshot abstractions for future routing inspection
- explicit pipeline split:
  - `StrategyDecision`
  - risk approval
  - `MandateDesiredTrade`
  - future routing
  - downstream binding/account-targeted child intent
- `OrderIntent` is now explicitly positioned as downstream child-intent territory rather than a mandate-level planning object
- planning inspection endpoints for desired trades, routing candidates, and normalized quotes
- reduced generic platform-level `sleeve` wording where safe by adding component-oriented inspection surfaces while keeping Money Flow family-specific component keys such as `sleeve_15m`

Implemented in Phase 4.0.2:

- first-class `MandateMarketDataSourcePolicy` persistence and runtime context so mandate planning/signal source venue is explicit rather than hidden in the active exchange settings
- explicit distinction between:
  - current planning/source venue for a mandate
  - future candidate routing venues/accounts under that mandate's binding group
- mandate-scoped desired-trade aggregation and idempotency for logical `open` intent across multiple source bindings
- explicit desired-trade convertibility rules:
  - `proposed + open` -> mandate-scoped desired-trade draft
  - `proposed + reduce` / `proposed + close` -> binding-scoped desired-trade draft when binding/account context exists
  - `proposed + hold`, `no_trade`, and `invalid` -> non-convertible by default
- planning service hardening around canonical instrument identity with explicit ambiguity handling for symbol-only fallback
- risk and execution interfaces refactored so they no longer teach the old direct `StrategyDecision -> OrderIntent` path
- additional planning inspection endpoints for source-policy and convertibility checks

Implemented in Phase 4.1:

- first-pass risk evaluation over persisted strategy decisions using convertibility rules, mandate source-policy context, bound-account truth, and binding candidate policy checks
- explicit desired-trade lifecycle states at the approval layer:
  - `draft`
  - `approved`
  - `rejected`
  - `routing_required`
- persisted `risk_evaluations` for structured approval/rejection/no-intent/routing-required outcomes
- mandate-scoped `open` decisions now stop at an approved `MandateDesiredTrade` with explicit `routing_required` state instead of creating premature child intents
- binding-scoped `reduce` and `close` decisions can now produce downstream child intents when:
  - binding/account context is already known
  - a matching open bound position exists
  - binding/account policy checks pass
- initial deterministic child-intent sizing for binding-scoped actions:
  - `close` -> full reducible position size
  - `reduce` -> policy-driven fraction of the reducible bound position
- `OrderIntent` now behaves as a prepared downstream child object rather than a direct strategy output
- operator/API inspection endpoints for:
  - risk evaluations
  - desired-trade states
  - prepared child intents
- source-policy mismatch rejection when the active mandate runtime and persisted planning/source policy are inconsistent

Implemented in Phase 4.1.1:

- explicit venue support-level taxonomy:
  - `qa_read_only`
  - `execution_preparable`
  - `live_enabled`
- Hyperliquid, Aster, OKX, and Coinbase Advanced Trade now report `execution_preparable` support level while remaining read-only / dry-run by default
- venue-native prepared-order preview downstream of `OrderIntent`:
  - `PreparedVenueOrder`
  - reason-coded preflight status
  - venue-native payload preview without submission
- per-venue preflight validation for:
  - supported order types
  - reduce-only support
  - client-order-id support
  - time-in-force support
  - minimum size
  - quantity step size
  - price tick size
  - missing account or symbol context
- richer per-venue private-state inspection:
  - account snapshot visibility
  - open-order visibility
  - open-position visibility
  - venue readiness and support-level reporting
- new inspection endpoints for:
  - per-venue account snapshot
  - per-venue private-state summary
  - per-venue order constraints
  - child-intent prepared-order preview
- future newly added venues can still start at `qa_read_only`; current integrated venues were matured deliberately so Phase 4.2 can gate against real venue truth instead of weak adapter posture

Implemented in Phase 4.2:

- first-class persisted execution-readiness / submission-eligibility assessments above `PreparedVenueOrder`
- explicit distinction between:
  - prepared
  - eligible for submission in principle
  - phase-blocked from live submission
- readiness outcomes now separate:
  - venue semantic support truth
  - adapter submission implementation truth
  - account/environment authorization
  - current phase enablement
- explicit readiness reason codes such as:
  - `preview_rejected`
  - `adapter_submission_unimplemented`
  - `read_only_mode_enabled`
  - `dry_run_only`
  - `private_state_unavailable`
  - `account_not_authorized`
  - `phase_live_submit_deferred`
- persisted readiness evaluations tied to child intent, desired trade, binding/account, venue, and environment
- new inspection endpoints for:
  - child-intent submission-readiness by ID
  - recent execution-readiness evaluations
- current integrated venues remain execution-preparable, but no venue is live-enabled and no live submission occurs in this phase

Implemented in Phase 4.2.1:

- corrected readiness support-level semantics so `live_enabled` support is treated as execution-capable from the venue/support perspective rather than being blocked as non-preparable
- readiness now blocks explicitly on binding/account active-state policy:
  - `binding_disabled`
  - `binding_not_routing_eligible`
  - `venue_account_inactive`
- capability truth, adapter implementation truth, account/environment authorization, and phase-level live-submit deferral remain distinct and test-covered
- repo governance now requires contributors to read the Obsidian strategic brain, starting with [money-flow/00_Money_Flow_Command_Center.md](money-flow/00_Money_Flow_Command_Center.md) and [money-flow/Project_Memory/money_flow_project_memory.md](money-flow/Project_Memory/money_flow_project_memory.md), before substantial work; the repo-root [money_flow_project_memory.md](money_flow_project_memory.md) is only a pointer
- small platform wording cleanup continues to prefer `component` for generic platform surfaces while leaving Money Flow family-specific `sleeve_*` identifiers in place where they are already part of stable behavior

Implemented in Phase 4.3:

- the explicit submit transition below readiness was introduced:
  - `OrderIntent`
  - `PreparedVenueOrder`
  - `ExecutionReadinessAssessment`
  - `SubmittedOrder`
- live submission still requires all of:
  - venue semantic support
  - repo adapter submit-path implementation
  - per-venue submission enablement
  - per-account/environment submission authorization
  - global live-submission phase enablement
  - favorable execution-readiness outcome
- explicit submission flow now preserves the lifecycle:
  - `OrderIntent`
  - `PreparedVenueOrder`
  - `ExecutionReadinessAssessment`
  - `SubmittedOrder`
- submitted-order truth is now persisted with venue/account identity, client/exchange order IDs, initial order status, timestamps, and raw submission payload
- prepared child intents remain distinct from eligible child intents, and eligible child intents remain distinct from submitted orders
- mandate-scoped `open` desired trades still stop above routing and do not create or submit child intents directly
- new execution inspection surfaces expose:
  - explicit submission action for one prepared child intent
  - recent submitted orders
  - failure reasons when submission is blocked or rejected before persistence

Implemented in Phase 4.3.2:

- corrected the remaining 4.3/4.3.1 execution-truth gaps so submission claims now depend on venue-local auth/signing reality and the targeted `VenueAccount` execution context rather than a venue-global integration shortcut
- current venue/product scopes with truthful submit-path implementations are now:
  - Hyperliquid perpetuals
  - Aster perpetuals
  - OKX spot and perpetual/swap products
  - Coinbase Advanced Trade spot products
  - Binance spot products
  - Kraken spot products
- venue-specific signing, auth headers, and request composition now live in the venue adapters instead of falling back to a generic unsigned submit path
- Coinbase Advanced Trade now uses the documented JWT bearer model for its current spot submission scope
- Hyperliquid now uses an SDK-faithful L1 signing flow for its current perpetual submission scope
- same-venue multi-account submission now resolves the targeted `VenueAccount` execution context correctly, including account identifier / wallet / subaccount / credential selection and submitted-order persistence
- `credentials_ref` and `wallet_ref` are treated as reference labels only; actual auth material now resolves explicitly from targeted account auth metadata or documented integration defaults rather than being silently treated as raw secrets
- docs, capability signaling, and tests now distinguish more honestly between:
  - semantic venue support
  - preview/preflight support
  - adapter submit-path implementation
  - truthful account-targeted auth/signing
  - account/environment authorization
  - phase-level live-submit enablement

Implemented in Phase 4.3.3:

- fixed the remaining execution-truth gap where several signed submit paths were still relying on generic HTTP helpers that could serialize a different body than the one used for signing
- Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken now use explicit exact-body request helpers for submission so the signed JSON/form representation matches the transmitted JSON/form representation for the currently implemented scopes
- Hyperliquid submission truth remains scoped to its SDK-faithful L1 signing model and now stays documented as signing the same action payload that is transmitted under the exchange request wrapper
- same-venue multi-account submission targeting remains explicit and test-covered:
  - submission resolves from the targeted `venue_account_ref_id`
  - no silent venue-global account fallback is relied on in the claimed submission paths
- docs and capability language are now intentionally limited to code/test-proven submit-path truth; no broader live-order validation claim is implied

Implemented in Phase 4.4:

- `SubmittedOrder` now has an explicit post-submit lifecycle instead of stopping at one initial submission acknowledgment:
  - `submitted`
  - `acknowledged`
  - `cancel_requested`
  - `cancel_acknowledged`
  - `partially_filled`
  - `filled`
  - `canceled`
  - `expired`
  - `rejected`
  - `unknown`
- reconciliation is now explicit and separate from order status:
  - `not_attempted`
  - `pending`
  - `reconciled`
  - `unavailable`
  - `failed`
- submitted-order lifecycle audit history is now persisted in a dedicated lifecycle-event table rather than hidden only inside mutable provenance JSON
- execution now supports single-target post-submit orchestration for already-targeted child intents:
  - prepare
  - assess readiness
  - submit
  - persist submitted order truth
  - reconcile later against venue/account truth where the adapter can support it honestly
- persisted fill evidence can now advance submitted-order state from:
  - `acknowledged` -> `partially_filled`
  - `partially_filled` -> `filled`
- venue rejection, ambiguous outcome, reconciliation-unavailable, and reconciliation-failed paths now produce explicit reason codes and lifecycle events instead of leaving order state implicit
- cancel/amend groundwork now exists through:
  - `cancelable_in_principle`
  - `amendable_in_principle`
  but no live cancel/amend behavior is implemented
- Hyperliquid currently has the deepest live venue/account reconciliation path in the repo; other venues participate honestly with thinner lifecycle depth where order-state query support is not yet implemented

Corrected in Phase 4.4.1:

- Hyperliquid reconciliation now combines open-order truth and fill truth before finalizing lifecycle status:
  - if the order is still open and fills already exist, the reconciled status is now `partially_filled`
  - if fill evidence completes the order, the reconciled status is now `filled` even when the venue-side open-order view is stale
- submit-time venue rejection no longer leaves the child intent in a success-leaning `submitted` state:
  - `SubmittedOrder` preserves the exchange/account-side `rejected` truth
  - `OrderIntent` is now marked `rejected`
  - lifecycle events preserve the rejection reason/message explicitly

Implemented in Phase 4.5:

- post-submit reconciliation is now materially broader than the Hyperliquid-first path:
  - Aster perpetuals
  - OKX spot and perpetual/swap products
  - Coinbase Advanced Trade spot products
  - Binance spot products
  - Kraken spot products
  now expose first-pass order-state reconciliation that can distinguish open/working, partial fill, fill completion, cancellation, expiration, rejection, and missing/unknown venue-state outcomes where the current adapter scope can support that truthfully
- recovery guidance is now explicit and inspectable for submitted orders:
  - `no_action_required`
  - `retryable`
  - `non_retryable`
  - `operator_action_required`
  - `venue_state_uncertain`
  - `account_policy_block`
- truthful live cancel execution now exists for the currently supported HTTP venue/account scopes:
  - Aster
  - OKX
  - Coinbase Advanced Trade
  - Binance
  - Kraken
  while Hyperliquid cancel still remained deferred at the end of Phase 4.5
- for OKX and Coinbase Advanced Trade, successful cancel submission is now modeled truthfully as an intermediate lifecycle:
  - explicit cancel action -> `cancel_requested`
  - venue acceptance -> `cancel_acknowledged`
  - only later reconciliation -> final `canceled`
- cancel/amend is now split more honestly:
  - cancel has explicit support/actionability for the scoped venues above
  - amend remains groundwork/actionability inspection only and is not claimed as a live behavior yet
- operator-facing post-submit inspection now includes:
  - submitted-order recovery recommendation
  - submitted-order actionability
  - explicit cancel action
- acceptance-critical tests are now isolated from workspace `.env` contamination, and repo review bundles are hardened against including `.env`, `.venv`, `.pgdata`, `.pgsocket`, `.pytest_cache`, `.DS_Store`, and similar local artifacts

Corrected in Phase 4.5.1:

- cancel lifecycle truth is now explicit for the non-terminal venue scopes:
  - `cancel_requested`
  - `cancel_acknowledged`
- OKX and Coinbase Advanced Trade no longer map cancel acceptance directly to final `canceled`
- for those scopes:
  - explicit cancel action persists `cancel_requested`
  - venue acceptance persists `cancel_acknowledged`
  - only later reconciliation can finalize `canceled`
- lifecycle history now records those intermediate cancel stages explicitly instead of collapsing them into one terminal cancel result

Implemented in Phase 4.6:

- post-submit orchestration now exists strictly downstream of `SubmittedOrder`:
  - `reconcile_now`
  - `cancel_now`
  - `retry_same_target`
- recovery execution is bounded and operator-safe:
  - retry executes only on explicitly retryable rejected orders
  - retry stays on the same venue/account target
  - on strict client-order-id reuse venues such as Aster and Binance, retry now uses a fresh retry client order id instead of silently reusing the original deterministic one
  - retry is blocked when duplicate exposure cannot be ruled out, including when sibling submitted-order attempts already exist for the same child intent
- amend moves beyond groundwork only where the venue path is currently code/test-proven:
  - OKX now supports native limit-order amend for the current scoped path
  - Aster, Coinbase Advanced Trade, Binance, Kraken, and Hyperliquid still exposed amendability/actionability truth only at the end of Phase 4.6
- lifecycle event history now includes explicit downstream action events such as:
  - `recovery_execution_requested`
  - `recovery_retry_submitted`
  - `recovery_retry_blocked`
  - `amend_acknowledged`
  - `amend_rejected`
- operator-facing execution APIs now expose:
  - explicit recovery execution trigger
  - explicit amend trigger
  - resulting submitted-order truth without collapsing it into preparation or readiness layers
- Hyperliquid remained the main lifecycle benchmark for reconciliation depth, but Phase 4.6 still left Hyperliquid cancel/amend deferred until the later 4.7 parity pass

Implemented in Phase 4.7:

- cancel/amend parity is now materially deeper without crossing into routing:
  - Hyperliquid now supports truthful account-targeted cancel acknowledgement plus native limit-order amend for the current perpetual scope
  - Coinbase Advanced Trade now supports native edit-order amend for the current spot limit-order scope
  - OKX remains the benchmark native amend path for the currently implemented swap/spot limit-order scope
  - Aster, Binance, and Kraken still exposed amendability/actionability honestly at the end of Phase 4.7; Kraken later gained a scoped native spot limit-order amend path, while Aster and Binance remain non-native-amend at current head
- cancel depth is now more even across the current venue set:
  - Hyperliquid, OKX, Coinbase Advanced Trade, and Kraken now preserve non-terminal cancel truth through `cancel_requested` / `cancel_acknowledged` before later reconciliation confirms final `canceled`
  - Aster and Binance keep their current scoped cancel behavior where the implemented path already returns terminal cancel truth
- Hyperliquid reconciliation is now deeper and safer:
  - order-status plus fill truth drives cancel/amend follow-up
  - canceled-with-zero-remaining no longer gets misclassified as fully filled when there is no fill evidence
  - open-order plus fill coexistence still reconciles to `partially_filled`
- venue reconciliation truth is now less lossy across thinner venues too:
  - Kraken cancel follow-up no longer overclaims finality before reconciliation
  - Aster canceled/expired states now preserve partial-fill evidence instead of collapsing into a generic partial-fill result
- recovery execution is broader but still bounded:
  - `amend_acknowledged` now routes to explicit same-target `reconcile_now` recovery guidance instead of pretending the amended working state is already final
  - no cross-venue retry, routing, or target reselection was introduced

Implemented in Phase 4.8:

- private order/account-state truth is materially deeper below routing:
  - all six venues now expose explicit adapter/runtime session-state and private-state-summary inspection surfaces
  - direct open-order polling now exists for Aster, Binance, OKX, Coinbase Advanced Trade, and Kraken
  - direct recent-fill polling now exists for Hyperliquid, OKX, Coinbase Advanced Trade, and Kraken
  - at the end of 4.8, Hyperliquid open-order truth still remained persistence-backed
  - at the end of 4.8, Aster and Binance recent-fill truth still remained persistence-backed
  - venue-private open-order views are now distinct from platform `SubmittedOrder` truth and only expose optional linkage back to persisted submitted orders when correlation is possible
  - private-state summary source fields now describe the runtime path actually used for that call: `venue_query`, `persistence`, or `unavailable`
- user-stream truth is now explicit rather than implied:
  - some venues expose semantic `supports_user_streams`
  - no current adapter claims implemented user-stream parity
  - private lifecycle updates remain polling-driven at head
- same-venue multi-account targeting remains intact through the deeper private-state paths:
  - private open-order reads and private recent-fill reads continue resolving from the targeted `VenueAccount`
  - no silent venue-global fallback was introduced
- bounded post-submit orchestration remains below routing:
  - the action set is still `reconcile_now`, `cancel_now`, and `retry_same_target`
  - 4.8 deepens the private-state substrate those actions reconcile against rather than inventing hidden routing behavior

Implemented in Phase 4.9:

- direct private-state parity is deeper where 4.8 still had persistence-backed gaps:
  - Hyperliquid private open orders now use direct account-targeted venue query
  - Aster and Binance still do not expose full account-wide recent-fill parity in the summary layer, but same-target retry safety now uses submitted-at-bounded direct same-account/same-symbol private trade checks when auth and symbol context exist
- same-target recovery execution is stricter without crossing into routing:
  - retry now checks live venue-private open-order evidence before submitting a new same-target retry
  - retry now checks live venue-private fill evidence before retrying on the supported direct-query scopes
  - if direct venue truth shows an order is still open or has already filled, retry is blocked rather than risking duplicate exposure
- native amend parity is modestly broader and still scope-bound:
  - Kraken now supports native amend only for the current spot limit-order scope
  - Aster and Binance still remain explicit native-amend unsupported venues
- per-surface runtime-source truth is now operator-visible on the private-state endpoints themselves:
  - open orders
  - recent fills
  - open positions
  - static capability is still kept separate from runtime source truth
- user-stream parity is still not implemented at adapter level:
  - no adapter currently claims implemented user-stream parity
  - lifecycle updates remain polling/reconciliation-first at head

Implemented in Phase 4.10.0:

- the Phase 4.9 retry-fill evidence surface was narrowed:
  - Aster and Binance retry checks no longer describe private trade evidence as targeted order proof when the rejected submitted order has no exchange order id
  - same-account/same-symbol fill evidence blocks retry conservatively with `retry_same_account_symbol_fill_ambiguous`; Phase 4.10.1 narrowed this to submitted-at-bounded evidence on Aster and Binance
  - failed direct private fill evidence queries now block retry with `retry_private_fill_evidence_unavailable` rather than proceeding on optimistic uncertainty
  - lifecycle events include `fill_evidence_scope` so operators can distinguish targeted proof from ambiguity
- Hyperliquid private open positions now use direct account-targeted `clearinghouseState` polling when an account address is available:
  - `open_positions_source` can now be `venue_query` for Hyperliquid
  - direct query failure or missing account context falls back to the existing persistence path without reporting false venue-query success
- user-stream/session parity remains intentionally narrow:
  - no adapter-level user-stream implementation was added
  - `/session-state` remains adapter/runtime connection bookkeeping
- native amend parity did not broaden in this phase:
  - Hyperliquid, OKX, Coinbase Advanced Trade, and Kraken remain the only code/test-proven native amend scopes
  - Aster and Binance remain explicit native-amend unsupported venues

Implemented in Phase 4.10.1:

- Hyperliquid direct open-position parsing no longer fabricates `mark_price=0` when `clearinghouseState` omits `markPx`:
  - `markPx` is used when present
  - when `markPx` is absent, `positionValue / abs(szi)` is used only when both values are available and size is nonzero
  - otherwise `mark_price` remains `None`
- Aster and Binance same-target retry fill checks are now submitted-at-bounded where their private trade endpoints support `startTime`:
  - stale same-account/same-symbol fills before `SubmittedOrder.submitted_at` do not block retry
  - same-account/same-symbol fills at or after `submitted_at` still block retry as ambiguity when no exchange order id exists
  - exact exchange-order-id matches remain `order_scoped`
- Binance private-trade query failures are now directly regression-tested to block `retry_same_target` before a new submitted order can be created.

Implemented in Phase 4.10.2:

- the unsafe submitted-order private-fill convenience wrapper was removed from the adapters:
  - ambiguous Aster/Binance same-account/same-symbol retry evidence now remains only inside `SubmittedOrderPrivateFillEvidence`
  - ambiguous retry evidence can still block `retry_same_target`
  - ambiguous retry evidence can no longer be collapsed into plain submitted-order fills with the evidence scope discarded
- exact exchange-order-id evidence remains `order_scoped` and still returns matched fills through `fetch_retry_private_fill_evidence`
- zero-match exact-id private trade queries now report that no matching fills were returned instead of claiming a match occurred.

Implemented in Phase 5.0:

- first-class non-executing routing substrate for routing-required mandate-scoped open desired trades
- `RoutingRequest`, `RoutingAssessment`, and per-binding `RoutingCandidateAssessment` domain/API surfaces
- persisted `routing_assessments` and `routing_assessment_candidates` audit tables containing assessment facts only:
  - desired-trade linkage
  - evaluated binding inventory
  - eligibility status
  - reason codes
  - missing-data facts
  - evaluated timestamps
- operator endpoints:
  - `POST /api/v1/routing-assessments/from-desired-trade`
  - `GET /api/v1/routing-assessments/{assessment_id}`
- routing assessment output is deliberately limited to:
  - `assessment_only`
  - `no_eligible_bindings`
  - `insufficient_data`
- Phase 5.0 does not choose a binding, does not rank venues, does not create child intents, and does not submit.

Implemented in Phase 5.1:

- cleaned up Phase 5.0 candidate semantics so every `RoutingCandidateAssessment.assessment_id` refers to the persisted routing assessment id, never the request id
- added `RoutingTargetChoice` plus persisted `routing_target_choices` audit records for operator-requested target choice from an existing routing assessment
- target choice is explicit and non-executing:
  - the caller must specify a binding key or binding row id
  - the assessment must be `assessment_only`
  - the candidate must belong to that assessment and be `eligible_for_future_selection`
  - candidate missing-data facts must be empty
  - the source desired trade must still be a routing-required mandate-scoped open and must not already be binding/account targeted
  - the selected binding and venue account must still exist and remain enabled / active / trading eligible
- recorded and blocked target-choice outcomes use explicit statuses and reason codes, including `target_choice_recorded`, `blocked_candidate_ineligible`, `blocked_assessment_insufficient_data`, `blocked_no_eligible_binding`, `blocked_candidate_not_found`, `blocked_assessment_not_found`, and `blocked_stale_assessment`
- `MandateDesiredTrade.status` remains `routing_required`; target choice does not create `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, fanout, allocation, venue scoring, or submission.

Implemented in Phase 5.2:

- added explicit `RoutingTargetChoice` -> one `OrderIntent` conversion through `convert_target_choice_to_child_intent`
- conversion starts only from an explicit `target_choice_id`; it does not infer the latest assessment, desired trade, or candidate
- conversion revalidates current target-choice, assessment, candidate, desired-trade, binding, venue-account, and symbol-mapping truth before creating a child intent
- Phase 5.2.1 hardens conversion lineage by checking routing assessment id/ref/environment consistency, desired-trade client/mandate/source identity, and current binding mandate ownership before any child intent can be created
- successful conversion creates exactly one binding/account-targeted `OrderIntent`, marks the source desired trade `routed`, and stores routing assessment / target-choice lineage in stable child-intent provenance
- repeated conversion of the same target choice is idempotent and returns the existing child intent instead of creating duplicates
- conversion does not create a prepared venue order, execution-readiness assessment, submitted order, fanout, allocation, venue scoring, CBBO, or submission.

Implemented in Phase 5.3:

- converted routed child intents can use the existing `GET /api/v1/child-intents/{intent_id}/prepared-order-preview` and `GET /api/v1/child-intents/{intent_id}/submission-readiness` inspection paths
- before routed preview/readiness, the execution service revalidates route-origin lineage from `OrderIntent.provenance`, the source `MandateDesiredTrade`, `RoutingAssessment`, `RoutingTargetChoice`, selected candidate, current `MandateAccountBinding`, current `VenueAccount`, and symbol mapping
- Phase 5.3.1 tightens that validator so selected-target provenance fields, child-intent client/mandate identity, target-choice desired-trade linkage, current venue-account client ownership, and explicit routed submit attempts cannot drift into a misleading readiness result
- stale or mismatched routed lineage returns explicit blocked preview/readiness facts instead of silently repairing or retargeting
- valid routed readiness carries routing assessment / target-choice lineage in provenance and remains phase-blocked with `routed_submission_deferred` unless Phase 5.4 routed submission is explicitly enabled
- Phase 5.3 / 5.3.1 does not create submitted orders, extra child intents, fanout, allocation, venue ranking, price/quality scoring, CBBO, target reselection, or live routed submission.

Implemented in Phase 5.4:

- added `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED=false` as a separate routed submission gate from `EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED`
- routed child-intent readiness remains phase-blocked with `routed_submission_deferred` while the routed gate is disabled and with `phase_live_submit_deferred` while the normal live gate is disabled; those routed phase-boundary submit attempts are recorded as `last_submission_block` without changing the child intent to `submission_failed`
- routed prepared-order preview remains non-submitting and explicit-submit-only, but its `submission_deferred` payload flag now reflects the current routed/live gate state instead of being unconditional
- when both live submission and routed submission gates are enabled, an explicit `POST /api/v1/child-intents/{intent_id}/submit` can submit the already converted routed child intent only after Phase 5.3.1 route-lineage validation and normal readiness checks pass
- successful routed submission creates exactly one `SubmittedOrder` for the existing selected binding/account and records routing assessment, target choice, selected binding/account, selected venue, selected exchange symbol, and readiness evaluation lineage in submitted-order raw payload
- Phase 5.4.1 is a truth hotpatch only; it still does not auto-submit, reselect targets, fan out, split quantity, rank venues, score execution quality, use CBBO, or create a route executor.

Implemented in Phase 5.5:

- submitted-order API responses now expose read-only routed-origin audit fields derived from existing submitted-order raw payload, so operators can inspect routed `SubmittedOrder` lineage without parsing `raw_payload["routed_submission"]` manually
- routed submitted-order lineage includes desired-trade key, routing assessment id, routing target-choice id, selected binding/account, selected venue, selected exchange symbol, readiness evaluation id, and explicit no-auto-submit / no-fanout / no-scoring / no-target-reselection flags
- non-routed submitted orders report `routed_origin=false` and do not fabricate routing ids
- malformed or partial routed payloads are bounded with `route_lineage_malformed` and `missing_lineage_fields` instead of breaking submitted-order list/detail responses
- routed `SubmittedOrder` remains exchange/account truth; the routed lineage response is audit metadata only and never becomes an execution instruction, target reselection surface, route plan, or quality score
- routed child-intent conversion still defaults to `OrderType.MARKET`, `limit_price=None`, and `reduce_only=false`; this is a current controlled-handoff limitation and a deferred blocker before any broader routed execution, auto-submit, fanout, target reselection, or route executor work.

Implemented in Phase 5.6:

- routed submitted-order lineage inspection now treats wrong-typed routed payload fields as malformed, not merely nullable; `malformed_lineage_fields` identifies invalid field types while list/detail endpoints remain bounded and non-crashing
- routed target-choice conversion now uses an explicit `RoutedOrderShapeDecision` policy helper instead of an implicit hardcoded order shape
- the current routed conversion policy remains conservative and behavior-equivalent: `OrderType.MARKET`, `limit_price=None`, and `reduce_only=false` for mandate-scoped `open`
- converted child-intent provenance includes `routed_order_shape_policy` with policy source, selected order type, limit price, reduce-only truth, reason codes, and warnings
- Phase 5.8 now expands this policy with explicit MARKET/LIMIT input; slippage guard logic and market-data-derived limit-price sources remain deferred.

Implemented in Phase 5.7:

- submitted-order detail/list responses now include read-only `routed_lifecycle_context` for routed-origin orders alongside the Phase 5.5/5.6 lineage fields
- routed recovery recommendation, actionability, and recovery-execution responses expose the same routed lifecycle context so operators can see desired-trade, routing assessment, target-choice, selected binding/account, selected venue, selected exchange symbol, readiness, and routed order-shape policy facts without raw-payload parsing
- routed lifecycle context makes the post-submit boundary explicit: same-target only, same-account only, same-venue only, no auto-submit, no fanout, no scoring, and no target reselection
- malformed routed payloads remain bounded on recovery/actionability surfaces with missing/malformed lineage facts; malformed lineage never authorizes target changes or wider recovery
- non-routed submitted orders do not fabricate routed lifecycle context, and Phase 5.7 adds no migration, config, endpoint, submission behavior, LIMIT/slippage expansion, route executor, smart routing, or cross-binding/cross-venue recovery.

Hotpatched in Phase 5.7.1:

- routed same-target retry now stamps the existing route lineage onto the retried `SubmittedOrder` before persistence, so retried routed orders remain inspectable as routed-origin
- non-routed same-target retry still does not fabricate routed lineage
- routed submitted-order lineage/lifecycle parsing is centralized in one shared domain helper used by both execution service and API mapping, preserving bounded missing/malformed lineage behavior without duplicate parser logic
- no target reselection, fanout, route executor behavior, auto-submit, CBBO, scoring, LIMIT/slippage expansion, migration, config, or endpoint was added.

Implemented in Phase 5.8:

- target-choice conversion accepts optional `routed_order_shape_policy` input through the existing conversion API/service surface
- omitted policy input stays backward-compatible: `OrderType.MARKET`, `limit_price=None`, and `reduce_only=false`
- explicit `MARKET` policy is accepted only without `limit_price`
- explicit `LIMIT` policy requires a positive finite decimal `limit_price` and modeled candidate order-type support; missing, malformed, non-finite, zero, negative, or unsupported limit policy blocks before child-intent creation
- `reduce_only=true` remains blocked for mandate-scoped `open`
- repeated conversion stays idempotent; an already converted target choice cannot create a second child intent or silently mutate order shape when a different policy is later requested
- accepted and blocked decisions are visible in conversion result provenance and accepted child-intent provenance
- this is order-shape policy only, not venue ranking, CBBO, price discovery, fanout, target reselection, auto-submit, or route executor behavior.

Phase 5.8 conversion examples:

- default MARKET conversion: `POST /api/v1/routing-target-choices/{target_choice_id}/convert-to-child-intent` with no body
- explicit LIMIT conversion:

```json
{
  "routed_order_shape_policy": {
    "order_type": "limit",
    "limit_price": "101.25",
    "policy_source": "operator_requested",
    "requested_by": "operator@example.test"
  }
}
```

- blocked LIMIT without price: same body with `"order_type": "limit"` and no `limit_price` returns `blocked_order_shape_policy` with `limit_price_missing`
- blocked policy mismatch after conversion: once a target choice has created one child intent, a later request with a different order shape returns the existing child intent with `conversion_order_shape_policy_mismatch` and does not mutate or duplicate it

Intentionally deferred:

- broader live-execution rollout, native amend parity beyond Hyperliquid/OKX/Coinbase Advanced Trade/Kraken, and multi-order execution orchestration
- broader live routing execution, best-binding selection, and CBBO aggregation beyond the current explicit single-target path
- routed auto-submit, route execution orchestration, and target reselection
- slippage expansion for routed order-shape policy, including market-data-derived routed limit-price sources and price-guard semantics beyond explicit operator/requested limit prices
- child-intent fanout/splitting across bindings
- full portfolio accounting and final strategy-attribution overlays
- backtesting, paper trading, dashboard UI, and alerts delivery

## Architecture Summary

The platform now uses this hierarchy:

- `Client`
- `VenueAccount`
- `StrategyMandate`
- `MandateAccountBinding`
- `StrategyComponentConfig`

That means the repo is no longer architecturally hardcoded to one permanent exchange account, one permanent strategy-on-account object, one permanent global component set, or one permanent source venue hidden in process-global exchange settings.

Current runtime behavior remains conservative:

- Hyperliquid is the oldest and most complete integration
- Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken now join the current execution-preparable maturity branch with code/test-proven scoped submit-path implementations, but post-submit lifecycle depth is still thinner than Hyperliquid and live submission still stays disabled by default unless explicitly enabled
- one process still targets one selected mandate at a time
- the active mandate can include many bound accounts
- those bound accounts form the future account group a router will later choose among
- the active mandate also owns an explicit market-data / pricing source policy for planning and signal truth today
- Money Flow still runs three components today:
  - `sleeve_15m`
  - `sleeve_1h`
  - `sleeve_4h`

For Money Flow, each component currently maps to a timeframe-driven sleeve, but the hierarchy no longer assumes every future strategy family must use sleeves in the same way. Shared services still manage venue-account truth such as exposure, reconciliation, monitoring, and future policy/execution.

The explicit planning/approval pipeline at this point is:

- `StrategyDecision`: strategy-layer proposal
- risk evaluation: decides whether that proposal becomes:
  - no desired trade
  - rejected desired trade
  - approved desired trade
  - routing-required desired trade
- `MandateDesiredTrade`: mandate-level desired trade, optionally binding-scoped when the action is naturally tied to one account's open position
- routing assessment: `RoutingAssessment` enumerates eligible/ineligible binding candidates and missing data for routing-required mandate-scoped opens without choosing a live target
- target-choice audit: `RoutingTargetChoice` records one explicitly requested eligible binding from a routing assessment without submission
- target-choice conversion: Phase 5.2 can convert one explicit valid target choice into one binding/account-targeted `OrderIntent`; Phase 5.2.1 hardens the lineage checks before conversion; conversion itself does not prepare, assess readiness, submit, fan out, score, or compare venues
- routed child-intent preparation/readiness: Phase 5.3 lets converted routed child intents enter existing preview/readiness inspection after route-lineage revalidation, and Phase 5.3.1 hardens selected-target provenance / child-intent ownership / target-choice desired-trade linkage checks
- explicit routed submission handoff: Phase 5.4 allows one already converted routed child intent to submit only when route-lineage validation, normal readiness checks, the normal live-submit gate, and the separate routed-submit gate all pass
- routed post-submit inspection: Phase 5.7 exposes routed lifecycle/actionability context for already submitted routed child intents while keeping recovery same-target / same-account / same-venue only
- downstream child intent: `OrderIntent` remains the binding/account-targeted child-intent layer and is only prepared when target binding/account context is already known
- venue-native prepared order preview: `PreparedVenueOrder` shows how a child intent maps onto one venue request shape, with explicit preflight result and rejection reasons
- execution readiness assessment: a persisted gate above `PreparedVenueOrder` that says whether the prepared child intent is ineligible, blocked, eligible in principle, or only phase-blocked from live submission
- later routing work: later phases may deepen routed post-submit lifecycle/reconciliation audit, but target reselection, fanout, CBBO, venue scoring, route executor behavior, cross-binding/cross-venue recovery, and smart routing remain deferred

Current routing boundary rule:

- approved mandate-scoped `open` desired trades can now produce non-executing routing assessments and target-choice audit records; one valid explicit target choice can later create exactly one child intent after conversion revalidation
- an operator can record one non-executing target choice from a valid routing assessment, Phase 5.2 can later convert that explicit target choice into one child intent after revalidation, and Phase 5.3 can inspect preparation/readiness for that child intent without submission
- binding-scoped `reduce` and `close` desired trades may create prepared child intents when the target account is already known

The source/planning venue and future routing venues are now explicitly different concepts:

- `MandateMarketDataSourcePolicy` defines the market-data / pricing source used for signal and planning truth today
- `MandateAccountBinding`s define the future account group a router may later choose from
- the source venue may be one venue today even while routing later considers multiple candidate bindings/accounts

Core design choices:

- explicit domain contracts before implementations
- strict separation between domain models, persistence models, and API schemas
- environment-safe configuration with dev, backtest, paper, testnet, and live profiles
- append-friendly audit and event tables for operational traceability
- idempotency and restart-safe state modeling in the database
- canonical internal instruments separated from venue-native mappings
- exchange truth separated from future attribution overlays
- market-data checkpoints stored explicitly instead of ad hoc JSON state
- client/account/mandate hierarchy separated from venue-scoped market data
- strategy umbrellas separated from venue-account truth so a future router can target one or more eligible bindings later
- venue adapters explicitly declare support levels and account/product-model differences instead of hiding them in Hyperliquid-specific assumptions

## Repository Structure

```text
.
├── .gitignore
├── apps
│   ├── api
│   └── dashboard
├── core
│   ├── config
│   ├── domain
│   ├── interfaces
│   ├── logging
│   └── schemas
├── db
│   ├── migrations
│   └── models
├── docs
├── infra
│   └── docker
├── services
│   ├── alerts
│   ├── backtest
│   ├── exchange
│   ├── execution
│   ├── indicators
│   ├── market_data
│   ├── planning
│   ├── portfolio
│   ├── risk
│   ├── routing
│   └── strategy
└── tests
```

## Local Setup

### Prerequisites

- Python 3.12
- `uv` recommended for environment and dependency management
- Docker and Docker Compose

### Bootstrap

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
```

### Run API Locally

```bash
uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Full Local Stack

```bash
docker compose up --build
```

## Configuration Approach

Configuration is loaded from environment variables using Pydantic settings. The root config object contains:

- app and environment settings
- database and optional Redis settings
- exchange adapter settings
- per-venue integration settings for Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken
- logging and alerts settings
- execution and global risk settings
- separate execution gates for normal live submission and Phase 5.4 explicit routed submission
- per-component settings for the current Money Flow `15m`, `1h`, and `4h` components
- active runtime selection for client and mandate, plus an optional focused account key for bootstrap/inspection convenience
- mandate-level market-data source policy and instrument-resolution settings for planning

The selected environment controls runtime mode:

- `dev`
- `backtest`
- `paper`
- `testnet`
- `live`

## Database and Migrations

Alembic is configured under `db/migrations`.

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

The current schema covers canonical instruments, venue symbol mappings, client/account truth, strategy mandates and bindings, mandate market-data source policies, component configs, candles, indicators, signals, strategy decisions, mandate desired trades, risk evaluations, allocations, prepared child intents, orders, fills, portfolio snapshots, market-data checkpoints, attribution overlays, risk events, health events, audit logs, and control-plane state.

Phase 3.4 and 3.5 leave the active hierarchy centered on:

- clients
- venue accounts
- strategy mandates
- mandate account bindings
- strategy component configs
- mandate/binding references on strategy-side records where needed

The old deployment-era tables are no longer part of the active schema at head.

`order_intents` now sits explicitly below mandate-level desired trades. Phase 4.0.1 adds the parent-link field so future phases can treat intents as child objects under a desired trade rather than reusing them as the mandate-level planning object, Phase 4.0.2 refines the surrounding interfaces so risk and execution no longer teach a direct decision-to-intent path, and Phase 4.1 uses `order_intents` only for binding/account-targeted child intents where the target is already naturally known.

`risk_evaluations` is now the persisted audit surface for the approval layer. It records the evaluated strategy decision, convertibility outcome, desired-trade result, rejection or routing-required reason, source-policy provenance, and any prepared child-intent linkage when a known binding target allows one.

`routing_assessments` and `routing_assessment_candidates` are the Phase 5.0 non-executing routing-substrate audit surface. They persist candidate inventory facts for routing-required mandate-scoped opens, including eligible/ineligible binding status, reason codes, missing-data facts, and evaluated timestamps. They intentionally do not persist allocation, ranked venue lists, planned child intents, or submission instructions.

`route_readiness_audits` and `route_readiness_candidate_audits` are the Phase 5.10.1 / 5.10.2 non-selecting data-sufficiency audit surface. They persist per-candidate missing, stale, unsupported, unavailable, policy-blocked, and blocking facts plus data-source labels so Phase 6.0.x recommendation can prove required facts exist before recommending. Quote source labels describe the audit runtime path, so audits derived from persisted routing-assessment facts use `derived_from_existing_assessment` instead of claiming a fresh venue query. Desired-trade side and positive quantity are readiness blockers, malformed/non-finite/non-positive quote prices block readiness without crashing, and default MARKET order shape is recorded as defaulted rather than explicit. Phase 6.0.2 sets `recommendation_created=true` on the source audit after any recommendation record is persisted from it. `ready_for_recommendation` means data-sufficient only; these tables intentionally do not persist recommended targets, ranks, scores, allocations, route plans, target choices, child intents, readiness evaluations, or submitted orders.

`routing_target_recommendations` is the Phase 6.0.x / Phase 6.1.1 non-executing recommendation audit surface, with Phase 6.2 adding explicit operator-triggered acceptance into a target choice and Phases 6.2.1 / 6.2.2 hardening same-audit acceptance idempotency. A recommendation can be created only from an existing `RouteReadinessAudit`. Omitted policy input uses `single_ready_candidate_only`: exactly one ready candidate records that candidate as the recommended target, zero ready candidates block, and multiple ready candidates block as ambiguous. Phase 6.1 adds the optional `explicit_binding_priority` policy, which is request-level and uses operator-configured `mandate_account_bindings.target_recommendation_priority`; lower positive integers win, missing or malformed priorities block, and ties block. Phase 6.1.1 validates API `policy_name` input to only the accepted policies before persistence, rejects malformed/oversized direct service policy names before any write, preserves existing binding priority when an update omits it, and clears priority only when `clear_target_recommendation_priority=true`. The service revalidates audit freshness, the recommended candidate's stored `quote_observed_at` freshness, current desired-trade status/scope/action/side/quantity/symbol identity, current mandate enablement, current binding/account truth, and current active/trading-eligible venue symbol mapping truth before success, including after `explicit_binding_priority` selects a candidate. Phase 6.2/6.2.1/6.2.2 reuses those truth checks before new acceptance, sets `target_choice_created=true` on recommendations after a target choice exists from valid acceptance, returns the original target choice for repeated or duplicate successful same-audit acceptance, preserves the original `recommendation_accepted_at` while recording idempotent retry checks separately, and prevents blocked same-audit recommendations from being marked accepted or stamped with accepted-looking provenance; linkage is carried in provenance rather than new schema. The table stores the recommended binding/account/venue/exchange-symbol only when the selected policy has exactly one valid candidate plus reason-coded blocked outcomes for stale/not-ready/invalid audit, stale or malformed recommendation-time quote facts, stale desired-trade truth, stale mandate truth, stale binding/account/symbol truth, and insufficient/malformed/tied priority facts. It intentionally does not persist child intents, readiness evaluations, submitted orders, ranks, scores, allocations, route plans, CBBO, fanout, or submit instructions.

`routing_target_choices` is the Phase 5.1 non-executing target-choice audit surface. It persists one operator-requested binding/account choice from an existing routing assessment, one explicit Phase 6.2 recommendation acceptance when the source recommendation is successful and current truth still matches, or a blocked target-choice outcome with reason codes and missing-data facts. Phase 6.2.1 prevents one route-readiness audit from producing more than one accepted recommendation target choice at the application layer; duplicate successful same-audit recommendations return the original target choice rather than creating another row. Phase 6.2.2 keeps that reuse limited to otherwise successful recommendations, so blocked recommendations from an already accepted audit remain blocked and do not acquire target-choice-created truth. Recommendation-created target choices record `routing_target_recommendation_id`, source route-readiness audit, policy name, recommended binding/account/venue/symbol, explicit operator action, and no-downstream-artifact flags in provenance. It intentionally does not persist child intents, prepared orders, readiness evaluations, submitted orders, allocation weights, price/quality scores, or submission instructions.

Routed child-intent submission uses existing `order_intents`, `execution_readiness_evaluations`, and `submitted_orders` storage. Phase 5.4 adds no migration: route lineage is retained in child-intent provenance and stamped into submitted-order raw payload only after explicit routed submission passes the separate routed gate and normal readiness. Phase 5.4.1 also uses existing provenance only: routed phase-boundary blocks write `last_submission_block` instead of `last_submission_failure`, and routed preview payloads report gate-specific submission deferral truth without adding schema. Phase 5.7 and 5.7.1 also add no migration: routed post-submit lifecycle/actionability context is read-only and derived from existing submitted-order raw payload plus already stamped route/order-shape audit facts, including routed lineage preserved through same-target retry. Phase 5.8 also uses existing provenance only: routed order-shape policy input/decision facts are stored on the converted child intent and later inherited into submitted-order audit payloads when routed submission occurs. Phase 6.10.1 adds the narrow `order_intent_submission_leases` table to serialize explicit child-intent submit calls before adapter submission; the lease is not a `SubmittedOrder` reservation and does not represent exchange/account truth. Phase 6.10.2 widens the lease status column and adds terminal `adapter_submit_persistence_unknown` state for the case where adapter submit returned but local submitted-order persistence failed; that state blocks future submit attempts until operator reconciliation/manual cleanup. Phase 6.10.3 adds no migration because the widened lease status column and metadata JSON already support terminal `adapter_submit_may_have_started` state before adapter submission can begin.

Phase 5.2 target-choice conversion uses existing `order_intents` storage plus structured provenance rather than adding a new migration. Converted child intents record `routing_assessment_id`, `routing_target_choice_id`, selected binding/account/venue identifiers, explicit non-submission flags, and Phase 5.8 routed order-shape policy input/decision facts in provenance. Idempotency is keyed to the explicit target choice so repeated conversion cannot create duplicate child intents or mutate order shape after conversion.

Phase 5.3 routed preparation/readiness uses existing prepared-order preview and `execution_readiness_evaluations` storage. Phase 5.3.1 adds no migration; it hardens routed readiness validation through service/test changes only. Routed readiness stores route-lineage validation and prepared preview summary in readiness provenance and remains non-submitting.

Phase 4A adds a venue-safe symbol uniqueness model so one venue can carry multiple product types for the same canonical asset, such as OKX spot and perpetual BTC mappings, without schema collisions.

## API Surface

Control-plane endpoints currently include:

- `GET /health`
- `GET /readiness`
- `GET /api/v1/config/summary`
- `GET /api/v1/components`
- `GET /api/v1/sleeves` as a Money Flow compatibility alias for component inspection
- `GET /api/v1/portfolio/summary`
- `GET /api/v1/positions`
- `GET /api/v1/risk/events`
- `GET /api/v1/risk/evaluations`
- `GET /api/v1/exchange/status`
- `GET /api/v1/exchange/capabilities`
- `GET /api/v1/exchange/instruments`
- `GET /api/v1/exchange/symbols`
- `GET /api/v1/venues`
- `GET /api/v1/venues/{venue}/status`
- `GET /api/v1/venues/{venue}/capabilities`
- `GET /api/v1/venues/{venue}/instruments`
- `GET /api/v1/venues/{venue}/symbols`
- `GET /api/v1/venues/{venue}/account-connectivity`
- `GET /api/v1/venues/{venue}/account-snapshot`
- `GET /api/v1/venues/{venue}/session-state`
  - adapter/runtime connection bookkeeping only; not deep venue-private account session truth
- `GET /api/v1/venues/{venue}/private-state-summary`
  - source fields report the runtime path actually used for that call
- `GET /api/v1/venues/{venue}/private-state/open-orders`
  - returns venue-private open-order snapshots, not `SubmittedOrder` records
- `GET /api/v1/venues/{venue}/private-state/recent-fills`
- `GET /api/v1/venues/{venue}/private-state/open-positions`
- `GET /api/v1/venues/{venue}/order-constraints`
- `GET /api/v1/venues/{venue}/market-data/health`
- `GET /api/v1/venues/{venue}/market-data/top-of-book`
- `GET /api/v1/clients`
- `GET /api/v1/accounts`
- `GET /api/v1/mandates`
- `GET /api/v1/mandates/{mandate_key}/bindings`
- `GET /api/v1/bindings/{binding_key}/components`
- `GET /api/v1/runtime/context`
- `GET /api/v1/planning/source-policy`
- `GET /api/v1/planning/decision-convertibility/{decision_id}`
- `GET /api/v1/planning/desired-trades`
- `GET /api/v1/planning/routing-candidates`
- `GET /api/v1/planning/quotes`
- `POST /api/v1/routing-assessments/from-desired-trade`
- `GET /api/v1/routing-assessments/{assessment_id}`
- `POST /api/v1/routing-target-choices/from-assessment`
- `GET /api/v1/routing-target-choices/{target_choice_id}`
- `POST /api/v1/routing-target-choices/{target_choice_id}/convert-to-child-intent`
- `GET /api/v1/routing-assessments/{assessment_id}/target-choices`
- `GET /api/v1/child-intents`
- `GET /api/v1/child-intents/{intent_id}/prepared-order-preview`
- `GET /api/v1/child-intents/{intent_id}/submission-readiness`
- `GET /api/v1/execution-readiness`
- `GET /api/v1/submitted-orders`
- `GET /api/v1/submitted-orders/{submitted_order_id}`
- `POST /api/v1/submitted-orders/{submitted_order_id}/reconcile`
- `GET /api/v1/submitted-orders/{submitted_order_id}/recovery`
- `POST /api/v1/submitted-orders/{submitted_order_id}/recovery/execute`
- `GET /api/v1/submitted-orders/{submitted_order_id}/actionability`
- `POST /api/v1/submitted-orders/{submitted_order_id}/cancel`
- `POST /api/v1/submitted-orders/{submitted_order_id}/amend`
- `GET /api/v1/submitted-orders/{submitted_order_id}/fills`
- `GET /api/v1/submitted-orders/{submitted_order_id}/events`
- `POST /api/v1/mandates`
- `POST /api/v1/mandates/{mandate_key}/bindings`
- `POST /api/v1/exchange/sync/universe`
- `POST /api/v1/exchange/sync/account`
- `POST /api/v1/venues/{venue}/sync/catalog`
- `POST /api/v1/market-data/sync/candles`
- `GET /api/v1/market-data/health`
- `GET /api/v1/market-data/checkpoints/{symbol}/{timeframe}`
- `POST /api/v1/indicators/sync`
- `GET /api/v1/indicators/latest`
- `POST /api/v1/strategy/evaluate`
- `GET /api/v1/strategy/status`
- `GET /api/v1/strategy/signals`
- `GET /api/v1/strategy/decisions`
- `GET /api/v1/portfolio/bootstrap-summary`
- `POST /api/v1/planning/desired-trades/from-decision/{decision_id}`
- `POST /api/v1/risk/evaluations/from-decision/{decision_id}`
- `POST /api/v1/route-readiness-audits/from-desired-trade`
- `POST /api/v1/route-readiness-audits/from-assessment`
- `GET /api/v1/route-readiness-audits/{route_readiness_audit_id}`
- `POST /api/v1/routing-target-recommendations/from-route-readiness-audit`
- `GET /api/v1/routing-target-recommendations/{routing_target_recommendation_id}`
- `POST /api/v1/routing-target-recommendations/{routing_target_recommendation_id}/accept`
- `POST /api/v1/routing-target-choices/{target_choice_id}/convert-to-child-intent`
- `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}`

## Roadmap

### Controlled Phase 5 Routing Substrate

- Phase 5.0 now defines routing-substrate models and inspection surfaces without implementing best-binding selection, CBBO, child-intent fanout, or mandate-scoped OPEN submission
- Phase 5.1 records operator-requested non-executing target choice from a valid routing assessment and still-valid source desired trade without converting it into a child intent
- Phase 5.2 converts one explicit valid target choice into one binding/account-targeted child intent, and Phase 5.2.1 hardens assessment/desired-trade/binding lineage validation before that conversion; this remains without auto-submit, fanout, CBBO, venue scoring, or preparation/readiness creation
- Phase 5.3 lets converted routed child intents enter existing preparation/readiness inspection after route-lineage revalidation, and Phase 5.3.1 hardens selected-target provenance, child-intent ownership, target-choice desired-trade linkage, and explicit submit blocking
- Phase 5.4 adds a controlled explicit routed submission handoff behind `EXECUTION_ROUTED_SUBMISSION_PHASE_ENABLED`; it submits only the already selected child intent through the existing venue path and still has no auto-submit, fanout, CBBO, venue scoring, target reselection, or route executor
- Phase 5.6 makes routed conversion order shape policy-backed and visible in child-intent provenance; Phase 5.8 adds optional explicit MARKET/LIMIT policy input while keeping default MARKET/no-limit/non-reduce-only behavior, Phase 5.8.1 blocks non-finite LIMIT prices before child-intent creation, Phase 5.8.2 prevents malformed/non-finite blocks from reporting `limit_price_explicit`, and slippage guards / market-data-derived price sources remain deferred
- Phase 5.7 adds routed post-submit lifecycle/actionability inspection for already submitted routed child intents; Phase 5.7.1 preserves routed lineage through same-target routed retry and centralizes the lineage parser; recovery remains same-target, same-account, and same-venue only with no target reselection, fanout, auto-submit, route executor, CBBO, or scoring
- Phase 5.9 adds routed reconciliation/lifecycle-event audit visibility for already submitted routed child intents, and Phase 5.9.2 reserves platform `routed_submission` lineage so reconciliation/update payloads cannot create, overwrite, or mutate it; reconciliation remains venue/account truth and route lineage remains read-only audit metadata
- Phase 5.10 closes Phase 5 with regression coverage across the existing routed lifecycle, proving typed routed lineage consistency, selected-account scoping, and no hidden fanout, allocation, scoring, CBBO, route plan, target reselection, route executor behavior, or auto-submit
- Phase 5.10.1 adds a persisted route-readiness/data-sufficiency audit for routing-required desired trades or routing assessments. Phase 5.10.2 tightens audit truth: persisted quote snapshots are labeled as derived from the existing assessment rather than fresh venue queries, missing side or missing/zero/negative quantity blocks recommendation-readiness, malformed/non-finite/non-positive quote prices are reason-coded instead of crashing notional math, and default MARKET order-shape policy is defaulted, not explicit. The audit reports whether facts are sufficient for future recommendation, but it does not recommend, choose, rank, score, create target choices, create child intents, prepare orders, assess execution readiness, submit, or execute.
- Phase 6.0.0 adds persisted non-executing `RoutingTargetRecommendation` records from an existing route-readiness audit only. Phase 6.0.1 hotpatches current-truth revalidation so success also requires current mandate enablement, desired-trade symbol identity, and active/trading-eligible symbol mapping truth. Phase 6.0.2 rechecks stored candidate quote observation freshness at recommendation time and updates the source audit's `recommendation_created` flag after any recommendation record is persisted. Phase 6.1 keeps `single_ready_candidate_only` as the default and adds optional `explicit_binding_priority`, a deterministic operator preference using nullable binding-level priority where lower positive integers win, missing/malformed priorities block, and ties block. Phase 6.1.1 bounds accepted `policy_name` input, makes binding-priority clearing explicit through `clear_target_recommendation_priority`, and confirms priority-selected candidates still block on stale quote observations. Phase 6.2 adds explicit recommendation acceptance into exactly one non-executing target choice after revalidating recommendation status, audit freshness, quote freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency. Phase 6.2.1 extends idempotency across duplicate successful recommendations from the same route-readiness audit, returns the original target choice, and preserves the original recommendation/audit acceptance timestamp while recording idempotent retry checks separately. Phase 6.2.2 prevents blocked recommendations from an already accepted audit from reusing same-audit idempotency or being stamped as accepted. Phase 6.3 explicitly converts an accepted recommendation-backed target choice into exactly one routed child intent, Phase 6.4 lets that child intent enter existing preview/readiness inspection, Phase 6.4.1 blocks readiness on routed order-shape policy/current-intent drift, Phase 6.5 adds a JSON manual inspection harness for explicitly exercising that current chain through readiness, Phase 6.6 adds local per-step timing to that harness, and Phase 6.7-6.10 close Phase 6 with explicit gated submitted-order handoff, recommendation-aware lifecycle/reconciliation lineage, a read-only routed workflow inspection API, and end-to-end closeout regression. Phase 6.10.1 adds the explicit child-intent submit lease before adapter submission, preserves first/latest submitted-order provenance across same-target retry, and exposes the workflow's static same-target facts as `same_target_lifecycle_summary` rather than actionability/recovery evaluation. Phase 6.10.2 marks adapter-returned/local-persistence-failed submit attempts as `adapter_submit_persistence_unknown`, blocks later submits for that intent until manual reconciliation, and keeps `SubmittedOrder` as post-submit truth only. It remains without ranking, scoring, sorting by price, price comparison, CBBO, readiness auto-creation, hidden submission, fanout, allocation, route executor behavior, or auto-submit.
- Phase 6.10.3 marks `adapter_submit_may_have_started` before the adapter submit call and treats that state as terminal/manual-reconciliation-required. Together with `adapter_submit_persistence_unknown`, it prevents TTL replacement after adapter-in-flight or post-adapter persistence uncertainty while keeping stale pre-adapter `active` leases replaceable and preserving `SubmittedOrder` as post-submit truth only.
- preserve current below-routing execution truth: same-target recovery only, venue-private order views distinct from `SubmittedOrder`, and no hidden cross-venue retry/failover

### Phase 6 And Later Routing / Execution Phases

- Phase 7.0 adds controlled automation policy and dry-run planning only, Phase 7.1 adds durable operator approval / revocation / consumption gates only, Phase 7.1.1 scopes approvals to the current lineage fingerprint so expired or stale-lineage approvals cannot authorize a later workflow stage, Phase 7.1.2 prevents manual-only or dry-run-only steps from receiving active approvals or appearing approved in gate-state output, Phase 7.2 consumes a valid current recommendation-acceptance approval to create or reuse exactly one target choice, Phase 7.2.1 makes that action/approval consumption coherent in one transaction, Phase 7.3 consumes a valid current target-choice-conversion approval to create or reuse exactly one child intent, Phase 7.4 consumes a valid current preview/readiness approval to run existing inspection only, Phase 7.5 consumes a valid current submitted-order-handoff approval to call the existing explicit submit path only when readiness and submit gates pass, Phase 7.5.1 bounds post-submit approval-consumption failure with `consumption_pending` truth, and Phase 7.6 closes the controlled automation chain with safety-regression proof rather than new behavior. The default policy is disabled; dry-run plans create no artifacts, generic approval consumption remains administrative only, and future action-taking automation still needs remaining DB-level concurrency/serialization hardening for broader automation, slippage/price guard policy, richer market-data quality, and operator reconciliation procedures for `adapter_submit_may_have_started` / `adapter_submit_persistence_unknown` leases.
- Phase 6 is closed as explicit recommendation-backed single-target routed execution through existing gated submit plus read-only inspection, with Phase 6.10.1/6.10.2/6.10.3 serializing explicit child-intent submit calls before adapter submission and preserving post-adapter or in-flight uncertainty without auto-submit, fanout, CBBO, venue scoring, route executor behavior, target reselection, automatic target-choice creation, child-intent auto-creation, or submitted-order creation directly from recommendation
- deepen routed order-shape policy only where truthful, including slippage guards and richer limit-price source semantics without venue ranking or CBBO
- child-intent fanout/splitting across bindings when routing selects more than one target
- market-wide best-price and CBBO-style decision support
- fuller private account/order lifecycle support beyond the current Phase 4.10 polling-first matrix
- broader live-execution rollout, richer cancel/amend behavior, and execution orchestration

### Later Phases

- paper trading and backtesting engines
- monitoring dashboard and alert integrations
- production deployment automation and runbooks

See [docs/architecture.md](docs/architecture.md) for system design detail and [docs/strategy.md](docs/strategy.md) for the strategy/indicator layer.
