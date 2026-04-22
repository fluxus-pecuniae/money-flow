# Phase 5 Changes Since Phase 5.4 And Phase 6.5 Handoff

Generated for handoff. This file summarizes changes after the Phase 5.4 baseline, covering Phase 5.4.1 through Phase 5.10.2, Phase 6.0.0, Phase 6.0.1, Phase 6.0.2, Phase 6.1, Phase 6.1.1, Phase 6.2, Phase 6.2.1, Phase 6.2.2, Phase 6.3, Phase 6.4, Phase 6.4.1, Phase 6.5, and the operational handoff-bundle workflow added after Phase 5.4.

Source of truth reviewed: `CHANGELOG.md`, `README.md`, `docs/architecture.md`, `docs/strategy.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, and `TODO.md`.

## Baseline At Phase 5.4

Phase 5.4 introduced the first controlled explicit routed submission handoff:

- one already converted routed child intent
- one selected binding/account
- explicit submit only
- normal live-submit gate plus separate routed-submit gate required
- no auto-submit
- no target reselection
- no fanout or split allocation
- no CBBO, venue ranking, execution-quality scoring, or smart routing

Everything below is after that baseline.

## Phase 6.5: Manual Routed-Flow Inspection Harness

Changelog entry: `v2026.04.22.004`.

Implemented:

- Added `scripts/manual_routed_flow.py`, an internal developer/operator JSON harness for manually exercising the current controlled routed chain from an existing desired trade key.
- Default invocation inspects only the desired trade and skips submission.
- `--run-through-readiness` explicitly calls the existing service paths for routing assessment, route-readiness audit, target recommendation, recommendation acceptance, target-choice conversion, prepared-order preview, and execution-readiness inspection, then stops before submission.
- Trace output includes artifact ids, statuses, reason codes, candidate/readiness counts, selected binding/account/venue/symbol facts, routed lineage, and no-smart-routing/no-ranking/no-scoring/no-CBBO/no-fanout/no-target-reselection/no-route-executor/no-auto-submit flags.
- `--submit` is blocked locally unless paired with `--i-understand-this-can-place-a-live-order`; confirmed submit attempts still go through existing readiness, live-submit, routed-submit, adapter, and account gates.
- Added direct Phase 6.5 tests for run-through-readiness output, default no-submission behavior, no `SubmittedOrder` creation, and local submit blocking before service submission.

Touched files:

- `scripts/manual_routed_flow.py`
- `tests/test_phase65_manual_routed_flow.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, API endpoint, smart routing, best-binding selection, ranking, scoring, CBBO, fanout, target reselection, route executor behavior, auto-submit, new exchange support, or `money_flow_project_memory.md` update was added.

## Phase 6.4.1: Recommendation-Backed Readiness Truth Hotpatch

Changelog entry: `v2026.04.22.003`.

Implemented:

- Added routed order-shape policy/current-intent drift validation to the existing routed child-intent lineage validator used before preview/readiness.
- Preview/readiness now block if stored routed order-shape policy is missing, malformed, or mismatched against current `OrderIntent` `order_type`, `limit_price`, or `reduce_only`.
- Recommendation-backed stale stored quote observations at preview/readiness time now emit `quote_stale_at_readiness` in reason codes and routed-lineage stale data.
- Strengthened Phase 6.4 tests for order-type drift, explicit LIMIT price drift, reduce-only drift, missing order-shape policy, readiness-time stale quote reason codes, and the no-submission/no-adapter-submit boundary.
- Cleaned stale roadmap/docs wording that still described recommendation-to-child-intent conversion as future work; Phase 6.3 already added explicit accepted recommendation-backed target-choice conversion into one child intent, and Phase 6.4/6.4.1 only harden preview/readiness inspection.

Touched files:

- `services/execution/service.py`
- `tests/test_phase64_recommendation_backed_readiness.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, endpoint, submitted-order creation, exchange submit call, route executor, fanout, allocation, ranking, scoring, CBBO, target reselection, auto-submit, new exchange support, or `money_flow_project_memory.md` update was added.

## Phase 6.4: Recommendation-Backed Preview/Readiness Inspection

Changelog entry: `v2026.04.22.002`.

Implemented:

- Added the controlled recommendation-backed child-intent preparation/readiness inspection handoff.
- Accepted recommendation-backed child intents now use the existing prepared-order preview and submission-readiness paths.
- Routed lineage validation now includes source `RoutingTargetRecommendation`, source `RouteReadinessAudit`, route-readiness candidate quote freshness, current mandate, current binding/account, active/trading-eligible symbol mapping, target choice, routing assessment, desired trade, selected-target provenance, and routed order-shape facts before eligible readiness.
- Prepared-order preview and execution-readiness API responses expose routed lineage as a top-level field so operators can inspect recommendation id, route-readiness audit id, routing assessment id, target-choice id, selected binding/account/venue/symbol, recommendation policy, order-shape policy, and no-downstream-artifact flags without parsing raw payload/provenance.
- Disabled binding/account truth, inactive/non-trading symbol mapping truth, and stale stored quote observations block readiness before adapter preparation.
- Explicit positive finite LIMIT order-shape policy remains visible through preview/readiness.
- Phase 6.4 may create/return prepared-order preview data and `ExecutionReadinessAssessment` inspection records through existing paths, but creates no `SubmittedOrder`.

Touched files:

- `services/execution/service.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `tests/test_phase64_recommendation_backed_readiness.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, submitted-order creation, exchange submit call, route executor, fanout, allocation, ranking, scoring, CBBO, target reselection, auto-submit, new exchange support, or `money_flow_project_memory.md` update was added.

## Phase 6.3: Explicit Accepted Recommendation Target-Choice Conversion

Changelog entry: `v2026.04.20.004`.

Implemented:

- Added the first controlled post-recommendation child-intent action.
- An accepted recommendation-backed `RoutingTargetChoice` can now be explicitly converted by an operator into exactly one routed child `OrderIntent`.
- The implementation reuses the existing target-choice conversion path instead of adding a route executor or parallel conversion framework.
- Conversion validates recommendation-backed target-choice provenance, successful linked `RoutingTargetRecommendation` truth, source `RouteReadinessAudit`, source `RoutingAssessment`, stored quote freshness, desired-trade, mandate, binding, account, symbol mapping, and order-shape policy truth before creating a new child intent.
- Repeated conversion of the same target choice returns the existing child intent.
- Duplicate same-audit target-choice paths return the existing child intent and cannot create a second child intent in normal controlled flow.
- Child-intent provenance preserves routing target recommendation id, route-readiness audit id, routing assessment id, routing target choice id, selected binding/account/venue/symbol, recommendation policy name, operator conversion timestamp, no-prepared/no-readiness/no-submission flags, and routed order-shape policy facts.
- Recommendation and source route-readiness audit inspection truth now set `child_intent_created=true` only after a valid child intent exists.
- Conversion stops at `OrderIntent`; no prepared order, execution-readiness assessment, submitted order, exchange adapter call, route executor, fanout, ranking, scoring, CBBO, target reselection, or auto-submit behavior is added.

Touched files:

- `core/domain/models.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase63_recommendation_target_choice_conversion.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, ranking/scoring, fanout, route executor behavior, automatic conversion, auto-submit, prepared-order creation, readiness creation, submitted-order creation, exchange-support expansion, or `money_flow_project_memory.md` update was added.

## Phase 5.4.1: Routed Submission Truth Hotpatches

Changelog entries: `v2026.04.18.043`, `v2026.04.18.044`.

Implemented:

- Fixed phase-boundary routed submit blocks so they preserve child-intent status instead of marking `submission_failed` when no adapter submission occurred.
- Routed submit blocks now write `provenance.last_submission_block` instead of `last_submission_failure` for phase-boundary blocks such as `routed_submission_deferred` and `phase_live_submit_deferred`.
- Routed prepared-order preview remains non-submitting and explicit-submit-only, but now reports actual routed/live gate truth.
- When both routed and live gates are disabled, routed readiness and submit-block provenance report both deferrals.
- Adapter submit is not called and no `SubmittedOrder` is created for phase-blocked routed submit attempts.

Touched files:

- `services/execution/service.py`
- `tests/test_phase54_routed_submission_handoff.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No migrations, new endpoints, route executor, auto-submit, fanout, target reselection, CBBO, scoring, or exchange changes were added.

## Operational Handoff Bundle Workflow

Changelog entry: `v2026.04.18.045`.

Implemented:

- Added the operational requirement that each completed phase produces a clean review ZIP in `/Users/tercirafael/`.
- Review bundles are built with `scripts/create_review_bundle.py` and `.archiveignore`.
- Bundles are expected to exclude `.env` files, keys, local virtualenvs, caches, generated archives, database/socket data, and unnecessary local artifacts.

Touched files:

- `AGENTS.md`
- `CHANGELOG.md`

No application behavior, routing scope, API endpoint, migration, or exchange behavior changed.

## Phase 5.5: Routed Submitted-Order Lineage Inspection

Changelog entry: `v2026.04.18.046`.

Implemented:

- Added read-only routed submitted-order lineage inspection.
- `SubmittedOrder` API responses now expose routed-origin lineage derived from existing `raw_payload["routed_submission"]`.
- Exposed desired trade, routing assessment, routing target choice, selected binding/account, selected venue, selected exchange symbol, readiness evaluation, and no-auto-submit / no-fanout / no-scoring / no-target-reselection audit flags.
- Non-routed submitted orders do not fabricate routed lineage.
- Malformed routed payloads are bounded with `route_lineage_malformed` and `missing_lineage_fields` instead of breaking list/detail responses.
- Routed order-shape policy was documented as deferred at this point.

Touched files:

- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase55_routed_submitted_order_lineage.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No migration, config change, endpoint expansion, target reselection, fanout, scoring, CBBO, auto-submit, route executor behavior, or exchange changes were added.

## Phase 5.6: Routed Order-Shape Policy Current Default And Lineage Type Truth

Changelog entry: `v2026.04.18.047`.

Implemented:

- Fixed Phase 5.5 malformed-lineage handling so wrong-typed routed lineage fields are marked malformed.
- Added `malformed_lineage_fields` alongside `missing_lineage_fields`.
- Kept submitted-order list/detail responses bounded and non-crashing for malformed routed payloads.
- Added the first explicit routed order-shape policy for target-choice conversion.
- Converted routed child intents now receive `MARKET / limit_price=None / reduce_only=false` from a policy-backed `RoutedOrderShapeDecision` instead of an implicit hardcoded default.
- Child-intent provenance exposes routed order-shape policy facts.
- LIMIT routed order-shape policy, routed limit-price source, and slippage guard semantics remained deferred in Phase 5.6.

Touched files:

- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase55_routed_submitted_order_lineage.py`
- `tests/test_phase56_routed_order_shape_policy.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No migration, config change, API endpoint, auto-submit, fanout, scoring, target reselection, route executor behavior, cross-binding recovery, cross-venue retry, or exchange changes were added.

## Phase 5.7: Routed Post-Submit Lifecycle And Actionability Inspection

Changelog entry: `v2026.04.18.048`.

Implemented:

- Added routed post-submit lifecycle/actionability inspection for already submitted routed child intents.
- Submitted-order detail/list responses expose read-only `routed_lifecycle_context` alongside routed lineage.
- Recovery recommendation, recovery execution response, and actionability responses expose selected route context for inspection.
- Operators can inspect desired-trade, routing assessment, target choice, selected binding/account, selected venue, selected exchange symbol, readiness, and routed order-shape policy facts without parsing raw payload manually.
- Routed recovery/actionability remains same-target, same-account, and same-venue only.
- Malformed routed payloads remain bounded with missing/malformed lineage facts.
- Non-routed submitted orders do not fabricate routed lifecycle context.

Touched files:

- `core/domain/models.py`
- `core/schemas/api.py`
- `services/execution/service.py`
- `apps/api/app/api/routes.py`
- `tests/test_phase57_routed_post_submit_lifecycle.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No auto-submit, fanout, CBBO, venue ranking/scoring, target reselection, route executor behavior, LIMIT/slippage expansion, cross-binding recovery, cross-venue retry/failover, migration, config change, endpoint, or exchange changes were added.

## Phase 5.7.1: Routed Retry Lineage Preservation And Parser Deduplication

Changelog entry: `v2026.04.18.049`.

Implemented:

- Fixed routed same-target retry so retried `SubmittedOrder` records preserve routed lineage before persistence.
- Routed retry results remain inspectable as routed-origin.
- Preserved `recovery_parent_submitted_order_id` provenance and same-target / same-account / same-venue retry semantics.
- Non-routed same-target retry still does not fabricate routed lineage.
- Collapsed duplicated routed submitted-order lineage/lifecycle parsing into shared `core/domain/routed_lifecycle.py`.
- API response mapping and execution service now share the same parser semantics for missing/malformed lineage and routed order-shape policy validation.

Touched files:

- `core/domain/routed_lifecycle.py`
- `services/execution/service.py`
- `apps/api/app/api/routes.py`
- `tests/test_phase57_routed_post_submit_lifecycle.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No target reselection, fanout, route executor behavior, auto-submit, CBBO, scoring, LIMIT/slippage expansion, migration, config, endpoint, or exchange changes were added.

## Phase 5.8: Routed Order-Shape Policy V2

Changelog entry: `v2026.04.18.050`.

Implemented:

- Added explicit routed order-shape policy input for controlled target-choice-to-child-intent conversion.
- Conversion now accepts optional `MARKET` or `LIMIT` order-shape policy input.
- Omitted input remains backward-compatible: `MARKET / limit_price=None / reduce_only=false`.
- Explicit `LIMIT` requires a positive finite `limit_price` and current modeled order-type support from the candidate assessment.
- Missing, malformed, zero, negative, unsupported, `MARKET + limit_price`, and `reduce_only=true` for mandate-scoped OPEN block before child-intent creation.
- Accepted and blocked order-shape decisions are visible in conversion provenance.
- Accepted decisions are persisted in child-intent provenance.
- Repeated conversion remains idempotent.
- A different policy after conversion cannot create a second child intent or silently mutate the existing one.

Touched files:

- `core/domain/enums.py`
- `core/domain/models.py`
- `core/interfaces/services.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase56_routed_order_shape_policy.py`
- `tests/test_phase57_routed_post_submit_lifecycle.py`
- `tests/test_api.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`

No migration, config, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, or exchange changes were added.

## Phase 5.8.1: Routed LIMIT Non-Finite Price Validation Hotpatch

Changelog entry: `v2026.04.18.051`.

Implemented:

- Fixed the Phase 5.8 P0 where non-finite routed LIMIT prices could crash conversion or be accepted as invalid child-intent price truth.
- Routed conversion API input no longer models `limit_price` as a plain `float`.
- API routing maps the decimal request value directly into `RoutedOrderShapePolicyInput` instead of converting through float stringification.
- Routing service limit-price coercion rejects `NaN`, `sNaN`, `Infinity`, and `-Infinity` before any Decimal comparison.
- Direct service conversion blocks non-finite LIMIT prices with `blocked_order_shape_policy`, `malformed_limit_price`, and `routed_order_shape_policy_blocked`.
- Blocked non-finite policy creates no child intent, does not create prepared/readiness/submitted objects, and leaves the desired trade `routing_required`.
- API non-finite representations return client errors rather than 500s; finite explicit LIMIT conversion still succeeds.

Touched files:

- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase56_routed_order_shape_policy.py`
- `tests/test_api.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, or exchange changes were added.

## Phase 5.8.2: Routed LIMIT Malformed Price Reason-Surface Cleanup

Changelog entry: `v2026.04.18.052`.

Implemented:

- Cleaned the Phase 5.8.1 blocked-policy reason surface.
- Malformed and non-finite LIMIT price input still blocks with `malformed_limit_price` and `routed_order_shape_policy_blocked`.
- Malformed and non-finite LIMIT price input no longer reports `limit_price_explicit`.
- Finite positive LIMIT input still reports `limit_price_explicit` when accepted as the selected child-intent limit price.
- Blocked malformed/non-finite policy still creates no child intent and leaves the desired trade `routing_required`.

Touched files:

- `services/routing/service.py`
- `tests/test_phase56_routed_order_shape_policy.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, or exchange changes were added.

## Phase 5.9: Routed Reconciliation And Lifecycle-Event Audit Visibility

Changelog entry: `v2026.04.19.001`.

Implemented:

- Preserved existing routed submitted-order audit lineage through reconciliation/lifecycle updates when venue reconciliation returns a new raw payload.
- Submitted-order reconciliation responses now keep routed-origin context inspectable through the normal `SubmittedOrderResponse` shape.
- Submitted-order lifecycle-event responses now expose read-only routed lifecycle context derived from the associated `SubmittedOrder` through the shared parser.
- Routed lifecycle-event context includes selected binding/account/venue/exchange-symbol facts, routed order-shape policy facts, same-target boundaries, and missing/malformed lineage facts where applicable.
- Non-routed reconciliation and lifecycle-event responses do not fabricate routed context.
- Malformed routed payloads remain bounded and non-crashing on reconciliation and lifecycle-event inspection.
- Same-venue multi-account routed reconciliation context remains scoped to the selected venue account.
- Phase 5.8.2 malformed/non-finite LIMIT reason-code truth remains intact.

Touched files:

- `core/domain/models.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/execution/service.py`
- `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, cross-binding recovery, cross-venue retry, or exchange changes were added.

## Phase 5.9.1: Routed Reconciliation Payload-Collision Hotpatch

Changelog entry: `v2026.04.19.002`.

Implemented:

- Hardened reconciliation/lifecycle raw-payload merging so an existing platform `raw_payload["routed_submission"]` audit payload always wins over a colliding top-level `routed_submission` key in adapter/update payloads.
- Preserved normal update payload fields such as venue reconciliation facts while preventing adapter/venue payloads from erasing or mutating platform route lineage.
- Kept lifecycle-event routed context derived from the associated `SubmittedOrder` raw payload rather than treating event raw payload as authoritative route lineage.
- Added direct regression coverage for collision payloads, proving reconciled submitted-order responses and lifecycle-event responses still expose original routing assessment, target choice, selected binding/account, selected venue, selected exchange symbol, and routed order-shape policy context.

Touched files:

- `services/execution/service.py`
- `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, cross-binding recovery, cross-venue retry, or exchange changes were added.

## Phase 5.9.2: Routed Submission Namespace Reservation Hotpatch

Changelog entry: `v2026.04.19.003`.

Implemented:

- Reserved the top-level submitted-order raw-payload `routed_submission` namespace for platform-authored routed audit lineage only.
- Reconciliation/lifecycle update payloads now have their top-level `routed_submission` key stripped before submitted-order raw-payload persistence.
- Existing routed submitted orders still keep their current platform `routed_submission` lineage when an update payload includes a collision.
- Non-routed submitted orders can no longer become routed-origin because an adapter/update payload included `routed_submission`.
- Lifecycle-event routed context remains derived from the associated `SubmittedOrder` raw payload; event raw payload may retain adapter collision facts but remains non-authoritative route context.
- Added direct regression coverage for non-routed collision payloads while preserving the routed collision regression.

Touched files:

- `services/execution/service.py`
- `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, cross-binding recovery, cross-venue retry, or exchange changes were added.

## Phase 5.10: Final Routing-Substrate Closeout Audit

Changelog entry: `v2026.04.19.004`.

Implemented:

- Added a focused end-to-end Phase 5.10 closeout regression for the accepted routed lifecycle.
- The test exercises `MandateDesiredTrade -> RoutingAssessment -> RoutingTargetChoice -> OrderIntent -> PreparedVenueOrder preview -> ExecutionReadinessAssessment -> SubmittedOrder -> actionability/recovery -> reconciliation -> lifecycle event` using the existing services and API surfaces.
- Verified exactly one child intent is created by explicit target-choice conversion and exactly one submitted order is created by explicit gated routed submission.
- Verified selected same-venue multi-account targeting uses only the selected binding/account.
- Verified typed routed lineage consistency across submitted-order detail/list `routed_lineage`, submitted-order `routed_lifecycle_context`, actionability/recovery context, reconciliation response context, and lifecycle-event context.
- Verified update-payload `routed_submission` remains non-authoritative: submitted-order raw payload keeps platform-authored routed lineage, while event raw payload may retain adapter collision facts without driving route context.
- Verified no fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, auto-submit, extra child intent, or extra submitted order appears in the closeout path.
- Updated operational and canonical docs to mark Phase 5 as closed routing substrate only and to defer controlled single-target selection to Phase 6.

Touched files:

- `tests/test_phase510_routing_substrate_closeout.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No source behavior, migration, config, new endpoint, routing behavior, auto-submit, target reselection, fanout, route executor, best-binding selection, smart routing, CBBO, venue ranking, execution-quality scoring, cross-binding recovery, cross-venue retry, or exchange changes were added.

## Phase 5.10.1: Route-Readiness Data-Sufficiency Audit

Changelog entry: `v2026.04.19.005`.

Implemented:

- Added first-class persisted `RouteReadinessAudit` and `RouteReadinessCandidateAudit` records.
- Audits can be created from a routing-required desired trade or an existing routing assessment and later fetched by id.
- Audit output is non-selecting, non-ranking, non-scoring, and non-executing.
- Per-candidate facts expose missing data, stale data, unsupported data, unavailable data, policy blocks, blocking reasons, fact snapshots, and data-source labels.
- Global facts expose reason codes, missing data, stale data, and blocking reasons.
- `ready_for_recommendation` means data-sufficient only; it is not a recommendation, selected target, rank, score, allocation, or route plan.
- Added direct tests for missing/stale quote truth, inactive binding/account blockers, missing symbol mapping, unsupported order-shape facts, fee/balance/private-state visibility, same-venue multi-account separation, API inspection, and no downstream artifacts.

Touched files:

- `core/domain/enums.py`
- `core/domain/models.py`
- `core/interfaces/services.py`
- `core/schemas/api.py`
- `db/models/__init__.py`
- `db/models/trading.py`
- `db/migrations/versions/20260419_0019_phase5101_route_readiness_audit.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase5101_route_readiness_audit.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No target recommendation, best-binding selection, smart routing, CBBO, price ranking, venue ranking, scoring, fanout, split allocation, route executor behavior, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, config, or money_flow_project_memory.md update was added.

## Phase 5.10.2: Route-Readiness Audit Truth Hotpatch

Changelog entry: `v2026.04.19.006`.

Implemented:

- Route-readiness audits no longer label quote facts read from persisted routing-assessment snapshots as fresh `venue_query`; current audit runtime source is `derived_from_existing_assessment`.
- Existing quote acquisition truth is preserved separately in candidate fact snapshots as original quote source.
- Desired-trade missing side, missing quantity, zero quantity, and negative quantity now block recommendation-readiness through global reason codes.
- Malformed, non-finite, zero, or negative quote prices now block with explicit quote-price reason codes and do not enter notional math.
- Default MARKET order-shape audit facts now use `market_order_policy_defaulted`; explicit wording remains reserved for actual explicit policy input.
- Strengthened direct tests for quote source truth, missing quote source fallback, desired-trade shape blockers, invalid quote-price safety, default MARKET wording, API response truth, and no downstream artifacts.

Touched files:

- `services/routing/service.py`
- `tests/test_phase5101_route_readiness_audit.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No target recommendation, best-binding selection, smart routing, CBBO, price ranking, venue ranking, scoring, fanout, split allocation, route executor behavior, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, migration, config, endpoint, or money_flow_project_memory.md update was added.

## Phase 6.0.0: Controlled Single-Ready-Candidate Recommendation

Changelog entry: `v2026.04.19.007`.

Implemented:

- Added persisted non-executing `RoutingTargetRecommendation` records created only from an existing `RouteReadinessAudit`.
- Added the `single_ready_candidate_only` policy: exactly one `ready_for_recommendation` candidate records that candidate as the recommended binding/account/venue/exchange-symbol.
- Zero ready candidates persist a blocked recommendation outcome.
- Multiple ready candidates persist a blocked ambiguous outcome; the service does not pick the first candidate, sort candidates, rank venues, score candidates, compare prices, or use CBBO.
- Recommendation creation re-checks audit freshness, desired-trade status/scope/action/side/quantity, current binding/account truth, and symbol mapping before recording success.
- Stale/not-ready/invalid audits, stale desired-trade truth, and stale binding/account/symbol truth persist reason-coded blocked outcomes.
- Added narrow API create/get endpoints for recommendation inspection.
- Recommendation is audit metadata only and does not create `RoutingTargetChoice`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, allocation, route plan, fanout, route executor behavior, target reselection, or submit instructions.

Touched files:

- `core/domain/enums.py`
- `core/domain/models.py`
- `core/interfaces/services.py`
- `core/schemas/api.py`
- `db/models/__init__.py`
- `db/models/trading.py`
- `db/migrations/versions/20260419_0020_phase600_routing_target_recommendation.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No smart routing, best-binding selection, recommendation among multiple ready candidates, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, config, or money_flow_project_memory.md update was added.

## Phase 6.0.1: Recommendation Current-Truth Hotpatch

Changelog entry: `v2026.04.19.008`.

Implemented:

- Hardened `RoutingTargetRecommendation` success so it no longer trusts route-readiness audit snapshots for mutable mandate/symbol truth.
- Recommendation creation now revalidates the current `StrategyMandate`; missing or disabled mandates block with `mandate_missing` / `mandate_inactive`.
- Recommendation creation now blocks current desired-trade symbol drift with `desired_trade_symbol_mismatch` and checks symbol-id identity when modeled.
- Recommendation creation now revalidates the current venue symbol mapping exists, is active, is trading eligible, and still matches the candidate instrument, platform symbol, exchange symbol, and venue.
- Blocked recommendation outputs keep route-readiness audit not-ready/global blockers visible even when zero-ready or multiple-ready candidate status is the primary blocked outcome.
- Added direct regression tests for disabled mandate, inactive symbol mapping, non-trading-eligible symbol mapping, desired-trade symbol drift, audit-level blocker visibility, and no downstream artifacts.

Touched files:

- `services/routing/service.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, endpoint, smart routing, best-binding selection, deterministic multiple-candidate policy, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, target-choice auto-creation, child-intent auto-creation, readiness creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Phase 6.1: Explicit Binding-Priority Recommendation Policy

Changelog entry: `v2026.04.19.010`.

Implemented:

- Kept `single_ready_candidate_only` as the default recommendation policy: exactly one ready candidate can recommend, zero ready candidates block, and multiple ready candidates block unless the caller explicitly requests another supported policy.
- Added optional request-level `explicit_binding_priority`.
- Added nullable `MandateAccountBinding.target_recommendation_priority` as operator-configured recommendation preference only.
- `explicit_binding_priority` uses lower positive integer priority as the winner, blocks if any ready candidate is missing priority, blocks malformed/out-of-range priority, and blocks ties.
- Reused Phase 6.0.2 current-truth checks after priority selection, including audit freshness, stored candidate quote freshness, desired-trade/mandate/binding/account/symbol truth.
- Added direct tests for default multiple-ready blocking, explicit priority success, missing priority, priority tie, malformed priority, current-truth revalidation after priority selection, unknown policy blocking, and no downstream artifacts.

Touched files:

- `core/domain/models.py`
- `core/interfaces/services.py`
- `core/schemas/api.py`
- `db/models/trading.py`
- `db/migrations/versions/20260419_0021_phase61_binding_recommendation_priority.py`
- `apps/api/app/api/routes.py`
- `services/runtime/context.py`
- `services/routing/service.py`
- `tests/test_api.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No smart routing, best-binding selection, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, target-choice auto-creation, child-intent auto-creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, config, or money_flow_project_memory.md update was added.

## Phase 6.1.1: Recommendation Policy Input And Priority-Clearing Cleanup

Changelog entry: `v2026.04.19.011`.

Implemented:

- Bounded recommendation API `policy_name` input to only omitted/null, `single_ready_candidate_only`, or `explicit_binding_priority`.
- Direct service policy input now rejects whitespace-only or oversized policy names before persistence, preventing DB-length failures.
- Binding upsert semantics are explicit: omitted `target_recommendation_priority` preserves the existing priority, while `clear_target_recommendation_priority=true` intentionally clears it.
- Clear-plus-value binding requests are rejected instead of silently choosing one interpretation.
- Added a direct regression proving `explicit_binding_priority` still blocks if the priority-selected candidate's stored `quote_observed_at` is stale at recommendation time.

Touched files:

- `core/interfaces/services.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/runtime/context.py`
- `services/routing/service.py`
- `tests/test_api.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, target-choice auto-creation, child-intent auto-creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Phase 6.2: Explicit Recommendation Acceptance Into Target Choice

Changelog entry: `v2026.04.20.001`.

Implemented:

- Added an explicit operator-triggered recommendation acceptance action that creates a `RoutingTargetChoice` from a successful `RoutingTargetRecommendation`.
- Acceptance requires `recommended_single_ready_candidate`, `non_executing=true`, selected binding/account/venue/exchange-symbol facts, source audit lineage, and another current-truth check before target-choice creation.
- Reuses existing `RoutingTargetChoice` storage and response semantics; source recommendation id, route-readiness audit id, routing assessment id, policy name, recommended target facts, accepted timestamp, and no-downstream-artifact flags are carried in target-choice provenance.
- Repeated acceptance of the same recommendation returns the existing target choice instead of creating duplicates.
- Successful acceptance sets `RoutingTargetRecommendation.target_choice_created=true` and source `RouteReadinessAudit.target_choice_created=true`; target-choice id linkage is exposed through provenance.
- Blocked recommendations, unknown recommendations, stale recommendation/audit/quote facts, and current binding/account/symbol/desired-trade drift block acceptance without creating target choices.
- Added focused Phase 6.2 tests for successful default-policy acceptance, explicit binding-priority acceptance, blocked/unknown recommendation rejection, disabled-binding and stale-quote blockers, idempotency, API acceptance, lineage, and no downstream artifacts.

Touched files:

- `core/interfaces/services.py`
- `core/schemas/api.py`
- `apps/api/app/api/routes.py`
- `services/routing/service.py`
- `tests/test_phase62_recommendation_acceptance.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, child-intent creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Phase 6.2.1: Recommendation Acceptance Idempotency Hotpatch

Changelog entry: `v2026.04.20.002`.

Implemented:

- Fixed the Phase 6.2 gap where two successful recommendations from the same `RouteReadinessAudit` could each be accepted into separate `RoutingTargetChoice` records.
- Acceptance now checks for an existing target choice produced by any recommendation tied to the same route-readiness audit before creating a new one.
- Duplicate same-audit recommendation acceptance returns the original target choice, marks the later recommendation as `target_choice_created=true`, and records `recommendation_acceptance_existing_audit_target_choice` / `route_readiness_audit_target_choice_already_created` provenance.
- Re-accepting the same recommendation or a duplicate same-audit recommendation preserves the original recommendation/audit `recommendation_accepted_at` timestamp.
- Idempotent retry/check timestamps are recorded separately as last-checked metadata instead of overwriting original acceptance truth.
- Added focused Phase 6.2.1 tests for duplicate same-audit recommendations, same-recommendation timestamp preservation, duplicate-recommendation timestamp preservation, existing blocking behavior, and no downstream artifacts.

Touched files:

- `services/routing/service.py`
- `tests/test_phase62_recommendation_acceptance.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, child-intent creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Phase 6.2.2: Recommendation Acceptance Same-Audit Validity Hotpatch

Changelog entry: `v2026.04.20.003`.

Implemented:

- Fixed the Phase 6.2.1 same-audit idempotency truth bug where a blocked recommendation from an already accepted audit could return that audit's existing target choice and be marked `target_choice_created=true`.
- Acceptance now runs a basic successful-recommendation preflight before same-audit idempotency can return an existing target choice.
- Blocked same-audit recommendations now fail through the normal acceptance blocker path, remain `target_choice_created=false`, and do not receive `recommendation_acceptance_existing_audit_target_choice`, `route_readiness_audit_target_choice_already_created`, `recommendation_accepted_at`, or `routing_target_choice_id` provenance.
- Duplicate successful recommendations from one route-readiness audit still return the original target choice and preserve original recommendation/audit acceptance timestamps.
- Added direct Phase 6.2.2 regression coverage for blocked recommendations from an already accepted audit plus retained Phase 6.2/6.2.1 idempotency and non-execution assertions.

Touched files:

- `services/routing/service.py`
- `tests/test_phase62_recommendation_acceptance.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, new recommendation policy, smart routing, best-binding selection, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, child-intent creation, readiness creation, submitted-order creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Phase 6.0.2: Recommendation Quote-Freshness And Audit-Linkage Hotpatch

Changelog entry: `v2026.04.19.009`.

Implemented:

- Recommendation creation now rechecks the recommended candidate's stored `fact_snapshot["quote_observed_at"]` at recommendation time instead of relying only on the source audit's `evaluated_at` age.
- The stored candidate `quote_freshness_threshold_seconds` is used when valid; the existing route-readiness freshness threshold is used only when the candidate snapshot does not carry a threshold.
- Missing, malformed, timezone-invalid, or stale quote observation facts block recommendation with explicit reason/stale-data codes such as `quote_freshness_unknown`, `quote_observed_at_malformed`, or `quote_stale_at_recommendation`.
- Persisting any `RoutingTargetRecommendation` from a source audit now marks `RouteReadinessAuditModel.recommendation_created=True`, including blocked recommendation records.
- Added direct tests for quote fresh-at-audit but stale-at-recommendation, missing/malformed quote observation timestamps, service/API `recommendation_created` audit truth, and continued no-downstream-artifact behavior.

Touched files:

- `services/routing/service.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

No migration, config, endpoint, smart routing, best-binding selection, recommendation among multiple ready candidates, CBBO, price ranking, venue ranking, execution-quality scoring, fanout, split allocation, route executor behavior, target-choice auto-creation, child-intent auto-creation, readiness creation, auto-submit, target reselection, cross-binding recovery, cross-venue retry/failover, new exchange support, new live execution behavior, or money_flow_project_memory.md update was added.

## Consolidated Source Areas Changed Since Phase 5.4

Domain and interfaces:

- `core/domain/enums.py`
- `core/domain/models.py`
- `core/domain/routed_lifecycle.py`
- `core/interfaces/services.py`

API schemas and routes:

- `core/schemas/api.py`
- `apps/api/app/api/routes.py`

Services:

- `services/execution/service.py`
- `services/routing/service.py`
- `services/runtime/context.py`

Persistence:

- `db/models/__init__.py`
- `db/models/trading.py`
- `db/migrations/versions/20260419_0019_phase5101_route_readiness_audit.py`
- `db/migrations/versions/20260419_0020_phase600_routing_target_recommendation.py`
- `db/migrations/versions/20260419_0021_phase61_binding_recommendation_priority.py`

Tests:

- `tests/test_api.py`
- `tests/test_phase54_routed_submission_handoff.py`
- `tests/test_phase55_routed_submitted_order_lineage.py`
- `tests/test_phase56_routed_order_shape_policy.py`
- `tests/test_phase57_routed_post_submit_lifecycle.py`
- `tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- `tests/test_phase510_routing_substrate_closeout.py`
- `tests/test_phase5101_route_readiness_audit.py`
- `tests/test_phase600_routing_target_recommendation.py`
- `tests/test_phase62_recommendation_acceptance.py`
- `tests/test_phase63_recommendation_target_choice_conversion.py`

Operational and canonical docs:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `PHASE_5_CHANGES_SINCE_5_4.md`

## Handoff Bundles Produced Since Phase 5.4

Review bundle workflow was added after Phase 5.4. Current Phase 5 review bundles in `/Users/tercirafael/phase5_handoffs/review_bundles/` include:

- `money-flow-phase-5.4.1-cleanup-review.zip`
- `money-flow-phase-5.5-review.zip`
- `money-flow-phase-5.6-review.zip`
- `money-flow-phase-5.7-review.zip`
- `money-flow-phase-5.7.1-review.zip`
- `money-flow-phase-5.8-review.zip`
- `money-flow-phase-5.8.1-review.zip`
- `money-flow-phase-5.8.2-review.zip`
- `money-flow-phase-5.9-review.zip`
- `money-flow-phase-5.9.1-review.zip`
- `money-flow-phase-5.9.2-review.zip`
- `money-flow-phase-5.10-review.zip`
- `money-flow-phase-5.10.1-review.zip`
- `money-flow-phase-5.10.2-review.zip`
- `money-flow-phase-6.0.0-review.zip`
- `money-flow-phase-6.0.1-review.zip`
- `money-flow-phase-6.0.2-review.zip`
- `money-flow-phase-6.1-review.zip`
- `money-flow-phase-6.1.1-review.zip`
- `money-flow-phase-6.2-review.zip`
- `money-flow-phase-6.2.1-review.zip`
- `money-flow-phase-6.2.2-review.zip`
- `money-flow-phase-6.3-review.zip`

Each bundle is expected to exclude sensitive and unnecessary local files such as `.env`, `.venv`, caches, generated archives, local database/socket data, and `.DS_Store`.

## Validation Coverage Recorded Since Phase 5.4

Recorded validation repeatedly covered:

- `compileall` across `core`, `services`, `apps`, and `tests`
- Phase 5 routing tests from Phase 5.0 through Phase 5.10.2 route-readiness audit truth hotpatch plus Phase 6.0.0 / 6.0.1 / 6.0.2 / 6.1 controlled recommendation tests, Phase 6.2 / 6.2.1 / 6.2.2 recommendation-acceptance tests, and Phase 6.3 accepted recommendation target-choice conversion tests
- routed submission handoff tests
- routed submitted-order lineage tests
- routed post-submit lifecycle tests
- routed reconciliation/lifecycle-event audit tests
- API tests
- operational docs tests
- adjacent execution readiness, submission, lifecycle, interfaces, and config tests
- PostgreSQL migration smoke tests when the local test database was available
- review bundle creation and exclusion verification

## Boundaries Preserved Since Phase 5.4

The following remain intentionally unimplemented:

- auto-submit
- target reselection
- fanout or split allocation
- cross-binding recovery
- cross-venue retry/failover
- route executor behavior
- best-binding selection
- smart routing
- CBBO
- venue ranking
- execution-quality scoring
- market-data-derived routed limit-price sources
- routed slippage guards
- recommendation among multiple ready candidates beyond explicit operator binding priority
- new exchanges
- CoinRoutes
- mandate-scoped OPEN bypass

## Current Head Summary After Phase 6.5

The platform has a controlled routed flow:

`StrategyDecision -> MandateDesiredTrade -> RoutingAssessment -> RouteReadinessAudit -> RoutingTargetRecommendation -> RoutingTargetChoice -> OrderIntent -> PreparedVenueOrder -> ExecutionReadinessAssessment -> SubmittedOrder`

`RouteReadinessAudit` sits beside `RoutingAssessment` as a non-selecting data-sufficiency audit. `RoutingTargetRecommendation` now sits above that audit as a non-executing recommendation record under default `single_ready_candidate_only` or explicit `explicit_binding_priority`, with bounded policy-name input and explicit binding-priority clear semantics. Phase 6.2 can explicitly accept a successful recommendation into one non-executing `RoutingTargetChoice`, Phase 6.2.1 ensures one route-readiness audit cannot produce multiple accepted target choices through duplicate successful recommendation records, and Phase 6.2.2 ensures blocked same-audit recommendations cannot be marked accepted by that idempotency path. Phase 6.3 can explicitly convert an accepted recommendation-backed target choice into exactly one routed child `OrderIntent` through the existing target-choice conversion path. Phase 6.4/6.4.1 allow that child intent to use existing preview/readiness inspection only after recommendation/audit/current-truth, stored quote, and routed order-shape policy/current-intent validation. Phase 6.5 adds manual JSON tooling for explicitly exercising those existing service paths through readiness from a desired trade key. Recommendation remains non-executing and is not a readiness, submission, reconciliation, or lifecycle instruction.

The routed flow now supports:

- non-executing routing assessment
- non-selecting route-readiness/data-sufficiency audit before recommendation, with truthful quote source labels, desired-trade side/quantity blockers, safe malformed quote-price handling, and defaulted MARKET order-shape wording
- controlled non-executing recommendation from an existing route-readiness audit only, with default single-ready-candidate behavior and optional explicit binding-priority operator preference
- priority-based recommendation uses only nullable binding-level `target_recommendation_priority`; lower positive integers win, missing/malformed priority blocks, and ties block
- API `policy_name` input is limited to accepted recommendation policies; malformed direct service policy input is rejected before persistence
- omitted binding-priority updates preserve the existing value, and `clear_target_recommendation_priority=true` intentionally clears it
- current mandate/desired-trade/binding/account/symbol truth and stored candidate quote observation freshness are revalidated before success under every recommendation policy
- source route-readiness audits report `recommendation_created=true` after a recommendation record is persisted from them
- explicit recommendation acceptance into exactly one target choice after revalidating recommendation status, audit/recommendation freshness, quote freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency
- same-audit recommendation acceptance idempotency: duplicate successful recommendations from one route-readiness audit return the original target choice instead of creating a second one
- same-audit idempotency validity: blocked recommendations from an already accepted audit remain blocked, retain `target_choice_created=false`, and do not receive accepted-looking provenance
- stable acceptance timestamp truth: same-recommendation and duplicate same-audit re-acceptance preserve original recommendation/audit `recommendation_accepted_at` and record later checks separately
- recommendation/source-audit `target_choice_created=true` truth after successful acceptance, with target-choice id linkage in provenance
- explicit accepted recommendation-backed target-choice conversion into exactly one routed child `OrderIntent`
- same-target-choice and same-audit child-intent conversion idempotency: repeated or duplicate accepted target-choice conversion returns the existing child intent instead of creating a second one
- recommendation/source-audit `child_intent_created=true` truth only after a valid child intent exists
- child-intent provenance preserves routing target recommendation id, route-readiness audit id, routing assessment id, routing target choice id, selected binding/account/venue/symbol, recommendation policy name, operator conversion timestamp, and routed order-shape policy facts
- recommendation-backed preview/readiness through existing child-intent endpoints, with direct routed-lineage response fields
- order-shape policy/current-intent drift blocking for order type, explicit LIMIT price, and reduce_only before adapter preparation
- readiness-time stale quote reason code `quote_stale_at_readiness`
- manual routed-flow inspection through `scripts/manual_routed_flow.py`, defaulting to desired-trade inspection only, with `--run-through-readiness` available for explicit service-by-service trace output and `--submit` locally blocked unless the danger-confirmation flag is supplied
- operator-requested target-choice audit records
- exactly-one child-intent conversion
- explicit routed order-shape policy input and decision output
- non-finite routed LIMIT price blocking before child-intent creation
- malformed/non-finite LIMIT price blocks do not claim `limit_price_explicit`
- routed readiness inspection
- explicit gated routed submission of the already selected child intent
- routed submitted-order lineage inspection
- route-aware same-target post-submit lifecycle/actionability inspection
- route-aware reconciliation and lifecycle-event audit inspection
- platform-owned routed audit lineage namespace reservation against reconciliation/update payload collisions and non-routed fabrication
- routed same-target retry lineage preservation
- final Phase 5 closeout regression coverage proving the substrate stays coherent, selected-account scoped, and non-routing

Phase 5 is closed as routing substrate plus route-readiness audit. Phase 6.5 keeps controlled recommendation limited to default single-ready-candidate behavior plus optional explicit binding-priority operator preference when multiple candidates are ready, explicit acceptance into target choice, explicit accepted target-choice conversion into one child intent, existing preview/readiness inspection, and manual operator/developer trace tooling only. The platform still does not implement smart order routing, best-binding selection, price/fee/venue-quality ranking, scoring, CBBO, fanout, route execution orchestration, automatic target-choice creation, automatic child-intent conversion, readiness auto-creation, submitted-order creation from recommendation, prepared-order auto-creation, or auto-submit. Route lineage remains audit metadata, `ready_for_recommendation` means data-sufficient only, and a `RoutingTargetRecommendation` remains non-executing.
