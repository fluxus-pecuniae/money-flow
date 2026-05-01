# Current Phase

## Phase

`Phase 7.5`

## Purpose

Phase 7.5 adds the fourth narrow approval-consuming action hook:

- Consume one valid current `submitted_order_handoff` approval.
- Submit the exact approved routed child `OrderIntent` through the existing explicit submit path.
- Consume the approval only after `SubmittedOrder` persistence or safe reuse.
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

Phase 7.5 is successful when one valid current approval can submit exactly one already-ready routed child intent through the existing explicit submit path, invalid approvals and non-approvable step states block before action, readiness and submit gates remain authoritative, submit uncertainty remains conservative, and no target reselection, fanout, route executor behavior, or broad auto-submit occurs.

## Current Outcome

- Obsidian command center/current phase/decision log/coordination notes are now part of the required agent workflow.
- Full strategic project memory lives at `money-flow/Project_Memory/money_flow_project_memory.md`.
- Repo-root `money_flow_project_memory.md` is a compatibility pointer only.
- The approval-gated `target_choice_conversion` action hook creates or reuses one child intent and consumes the matching approval.
- Phase 7.4 adds approval-gated `prepared_order_preview_and_readiness` inspection for exactly one existing child intent.
- Phase 7.5 adds approval-gated `submitted_order_handoff` for exactly one already-ready child intent through the existing explicit submit path.
- Recovery, route execution, fanout, scoring, CBBO, target reselection, cross-venue retry, and broad auto-submit remain deferred.

## Next Likely Phase

The next controlled automation phase should focus on closeout/regression or hardening of the controlled approval-gated chain before any broader automation is considered.
