# TODO

Last reviewed: `2026-04-22T19:49:16Z`

## Active Follow-Ups

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
- `summary`: `Consider a narrow persistence-level uniqueness guard or serialized acceptance/conversion path for concurrent Phase 6.2+ recommendation acceptance and Phase 6.3 accepted target-choice conversion if multiple workers can act on the same route-readiness audit simultaneously. Phase 6.2.1 uses application-level idempotency to return the existing target choice for repeated same-recommendation and duplicate successful same-audit acceptance, Phase 6.2.2 gates that same-audit reuse so blocked recommendations cannot appear accepted, and Phase 6.3 uses service-level same-desired-trade/same-audit child-intent reuse to prevent duplicate child intents in normal controlled flow. These phases preserve original timestamps and add no broad workflow engine; future DB-level serialization remains a possible hardening item before automation.`

### T-027

- `priority`: `medium`
- `status`: `done`
- `summary`: `Initialized source-control hygiene for the Phase 6.3 baseline on the `master` branch. The baseline tracks source, tests, migrations, docs, operational memory, `.gitignore`, and `.env.example`, while `.env`, virtualenvs, caches, local database/runtime state, logs, review ZIPs, and handoff archives are intentionally ignored. Future phase work should use short-lived branches off `master`.`

### T-028

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.4 implemented the recommendation-backed child-intent preparation/readiness inspection handoff. Accepted recommendation-backed child intents now use the existing prepared-order preview and submission-readiness paths with additional validation for source recommendation, route-readiness audit, candidate quote freshness, current mandate, binding/account, and active/trading-eligible symbol mapping. Preview/readiness API responses expose routed lineage including recommendation/audit/target-choice/selected-target/order-shape facts. The phase creates no submitted orders, exchange submit calls, route executor behavior, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit.`

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
