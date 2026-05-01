# Current Phase

## Phase

`Phase 7.4`

## Purpose

Phase 7.4 adds the third narrow approval-consuming action hook:

- Consume one valid current `prepared_order_preview_and_readiness` approval.
- Run existing prepared-order preview and execution-readiness inspection for the exact approved routed child `OrderIntent`.
- Consume the approval only after preview/readiness inspection succeeds or reuses existing readiness.
- Preserve no-submission and no-route-executor boundaries.

## Accepted Baseline

- Phase 7.0 added non-executing routing automation policy and dry-run plans.
- Phase 7.1 added durable approval records and revocation/consumption state.
- Phase 7.1.1 made approvals expiry-safe, lineage-scoped, and active-scope unique.
- Phase 7.1.2 prevented manual-only and dry-run-only steps from receiving active approvals.
- Phase 7.2 added approval-gated recommendation acceptance into one target choice.
- Phase 7.2.1 made recommendation acceptance and approval consumption coherent in one commit.
- Phase 7.3 added approval-gated target-choice conversion into one child intent and integrated Obsidian workflow.
- Phase 7.3.1 hardened target-choice conversion negative tests.

## Hard Boundaries

Do not build:

- smart routing
- best-binding selection
- CBBO
- ranking/scoring
- fanout or split allocation
- target reselection
- route executor behavior
- automatic submitted-order handoff
- auto-submit
- cross-binding or cross-venue recovery
- new exchange behavior

## Success

Phase 7.4 is successful when one valid current approval can run preview/readiness for exactly one approved child intent, invalid approvals and non-approvable step states block before action, readiness truth remains reason-coded, and no submitted order or exchange submit call occurs.

## Current Outcome

- Obsidian command center/current phase/decision log/coordination notes are now part of the required agent workflow.
- Full strategic project memory lives at `money-flow/Project_Memory/money_flow_project_memory.md`.
- Repo-root `money_flow_project_memory.md` is a compatibility pointer only.
- The approval-gated `target_choice_conversion` action hook creates or reuses one child intent and consumes the matching approval.
- Phase 7.4 adds approval-gated `prepared_order_preview_and_readiness` inspection for exactly one existing child intent.
- Submitted-order handoff, recovery, route execution, fanout, scoring, CBBO, target reselection, and auto-submit remain deferred.

## Next Likely Phase

The next controlled automation phase should consider approval-gated submitted-order handoff only after Phase 7.4 review and only through existing live/routed gates plus submit-lease uncertainty guards.
