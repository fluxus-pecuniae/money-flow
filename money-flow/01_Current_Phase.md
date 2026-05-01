# Current Phase

## Phase

`Phase 7.3`

## Purpose

Phase 7.3 has two bounded responsibilities:

- Make the Obsidian vault the required strategic-memory and cross-agent coordination layer.
- Add approval-gated target-choice-to-child-intent conversion only.

## Accepted Baseline

- Phase 7.0 added non-executing routing automation policy and dry-run plans.
- Phase 7.1 added durable approval records and revocation/consumption state.
- Phase 7.1.1 made approvals expiry-safe, lineage-scoped, and active-scope unique.
- Phase 7.1.2 prevented manual-only and dry-run-only steps from receiving active approvals.
- Phase 7.2 added approval-gated recommendation acceptance into one target choice.
- Phase 7.2.1 made recommendation acceptance and approval consumption coherent in one commit.

## Hard Boundaries

Do not build:

- smart routing
- best-binding selection
- CBBO
- ranking/scoring
- fanout or split allocation
- target reselection
- route executor behavior
- automatic preview/readiness
- automatic submitted-order handoff
- auto-submit
- cross-binding or cross-venue recovery
- new exchange behavior

## Success

Phase 7.3 is successful when a valid current-lineage `target_choice_conversion` approval can create or reuse exactly one child `OrderIntent`, then consume the approval with inspectable provenance, while creating no prepared order, readiness assessment, submitted order, exchange call, route executor, fanout, scoring, CBBO, target reselection, or auto-submit behavior.

## Current Outcome

- Obsidian command center/current phase/decision log/coordination notes are now part of the required agent workflow.
- Full strategic project memory lives at `money-flow/Project_Memory/money_flow_project_memory.md`.
- Repo-root `money_flow_project_memory.md` is a compatibility pointer only.
- The approval-gated `target_choice_conversion` action hook creates or reuses one child intent and consumes the matching approval.
- Preview/readiness, submitted-order handoff, recovery, route execution, fanout, scoring, CBBO, target reselection, and auto-submit remain deferred.

## Next Likely Phase

The next controlled automation phase should consider approval-gated preview/readiness only after Phase 7.3 conversion truth is reviewed.
