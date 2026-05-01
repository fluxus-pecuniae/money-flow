# Current Phase

## Phase

`Phase 7.6`

## Purpose

Phase 7.6 closes out the controlled automation chain with safety-diligence proof:

- Walk the full approval-gated chain from existing recommendation through submitted-order handoff.
- Prove each action consumes only the exact current-lineage approval for its stage.
- Prove dry-run, approval creation, generic administrative consumption, action-specific consumption, readiness, and submitted-order handoff remain distinct.
- Prove `consumption_pending` is bounded and repeat calls reuse existing submitted-order truth without another adapter submit.
- Preserve readiness, live-submit, routed-submit, adapter/account, submit lease, and uncertainty gates as authoritative.

## Accepted Baseline

- Phase 7.0 added non-executing routing automation policy and dry-run plans.
- Phase 7.1 added durable approval records and revocation/consumption state.
- Phase 7.1.1 made approvals expiry-safe, lineage-scoped, and active-scope unique.
- Phase 7.1.2 prevented manual-only and dry-run-only steps from receiving active approvals.
- Phase 7.2 added approval-gated recommendation acceptance into one target choice.
- Phase 7.2.1 made recommendation acceptance and approval consumption coherent in one commit.
- Phase 7.3 added approval-gated target-choice conversion into one child intent and integrated Obsidian workflow.
- Phase 7.3.1 hardened target-choice conversion negative tests.
- Phase 7.4 added approval-gated prepared-order preview/readiness inspection only.
- Phase 7.5 added approval-gated submitted-order handoff only.
- Phase 7.5.1 recorded `consumption_pending` approval truth when submitted-order persistence succeeds but approval consumption fails afterward.

## Hard Boundaries

Do not build:

- smart routing
- best-binding selection
- CBBO
- ranking/scoring
- fanout or split allocation
- target reselection
- route executor behavior
- broad auto-submit
- cross-binding or cross-venue recovery
- new exchange behavior

## Success

Phase 7.6 is successful when the full Phase 7 chain has an end-to-end safety regression proving exact-stage approval consumption, current-lineage truth, same-target behavior, bounded `consumption_pending`, no hidden SOR behavior, and no new action stage or production behavior.

## Current Outcome

- Obsidian command center/current phase/decision log/coordination notes are now part of the required agent workflow.
- Full strategic project memory lives at `money-flow/Project_Memory/money_flow_project_memory.md`.
- Repo-root `money_flow_project_memory.md` is a compatibility pointer only.
- The approval-gated `recommendation_acceptance` action hook creates or reuses one target choice and consumes the matching approval.
- The approval-gated `target_choice_conversion` action hook creates or reuses one child intent and consumes the matching approval.
- The approval-gated `prepared_order_preview_and_readiness` hook runs preview/readiness inspection for exactly one existing child intent.
- The approval-gated `submitted_order_handoff` hook submits exactly one already-ready child intent through the existing explicit submit path.
- Phase 7.5.1 records `consumption_pending` approval state if submitted-order persistence succeeds but approval consumption fails afterward.
- Phase 7.6 adds closeout regression coverage proving the accepted hooks remain stage-specific and no-SOR.
- Recovery, route execution, fanout, scoring, CBBO, target reselection, cross-venue retry, and broad auto-submit remain deferred.

## Next Likely Phase

The next major phase should be architecture-reviewed before implementation. Candidate Phase 8 work should focus on operator-grade automation observability, reconciliation/manual-resolution workflow, concurrency/serialization hardening, and dashboard/read-only inspection depth before any broader automation is considered.
