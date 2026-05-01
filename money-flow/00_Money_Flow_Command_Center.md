# Money Flow Command Center

This is the required Obsidian brain entrypoint for Money Flow agents.

## North Star

Money Flow is a mandate-driven, multi-venue trading platform where strategy alpha remains central. Routing and automation must serve the strategy workflow; they must not replace it with fake smart-routing or hidden execution behavior.

## Current Phase

- Current implemented phase: `Phase 8.0.2`
- Phase 7 status: accepted complete.
- Proposed next phase: `Strategy Validation` after Phase 8.0.2 acceptance; `Phase 8.1` remains deferred until explicitly scoped.
- Phase 8.0 status: implemented read-only operator observability/manual-resolution inspection.
- Phase 8.0.1 status: Obsidian memory and working-tree baseline cleanup; no product behavior changed.
- Phase 8.0.2 status: active submit-lease operator-summary truth hotfix; no product behavior changed.
- Current accepted action hooks: approval-gated recommendation acceptance, target-choice conversion, prepared-order preview/readiness inspection, and submitted-order handoff.

## Current Architectural Boundary

The accepted routed chain remains:

```text
MandateDesiredTrade
-> RouteReadinessAudit
-> RoutingTargetRecommendation
-> RoutingTargetChoice
-> OrderIntent
-> PreparedVenueOrder
-> ExecutionReadinessAssessment
-> SubmittedOrder
```

Phase 7.5 is accepted as automating only:

```text
ExecutionReadinessAssessment -> SubmittedOrder
```

Phase 7.6 adds no new automation transition. It closes out the Phase 7 controlled automation chain by proving the existing approval-gated stages remain exact-lineage-bound, same-target, non-fanout, non-reselecting, and distinct from dry-run / approval creation / generic administrative consumption. `consumption_pending` remains a bounded approval-reconciliation state; repeat calls must reuse the existing submitted order rather than submit again.

Phase 8.0 adds no new trading transition. It makes the existing chain easier to inspect, debug, reconcile, and manually manage through read-only operator summary inspection. It surfaces current workflow state, approval state, submit-lease uncertainty, `consumption_pending`, blocked readiness/recommendation facts, and next safe manual operator action without submitting, canceling, amending, retrying, selecting a new target, ranking, scoring, using CBBO, fanout, or route-executor behavior.

Phase 8.0.1 resolves the dirty Obsidian memory baseline left after Phase 8.0. The earlier full-project-memory refresh is accepted as intentional strategic-memory work, stale "proposed Phase 8.0" wording is cleaned up, and the repo-root memory file remains a pointer only.

Phase 8.0.2 fixes read-only operator-summary truth for active submit leases. An unexpired `active` child-intent submit lease is reported as `submission_in_progress`, blocks repeat-submit safety, and blocks the next safe operator action from reporting approval-gated submit as safe. Terminal submit uncertainty remains manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and no trading behavior or manual-resolution mutation is added.

## Repo Truth Sources

Repo operational truth remains in:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

Obsidian is the long-horizon project brain for founder intent, phase context, decisions, and cross-agent coordination. It does not replace the repo changelog or operational docs.

## Required Links

- [[01_Current_Phase|Current Phase]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[40 Operations/Future Work Roadmap|Future Work Roadmap]]
- [[40 Operations/Phase 8 Focus|Phase 8 Focus]]
- [[20 Workflows/Operator Observability and Manual Resolution|Operator Observability and Manual Resolution]]
- [[20 Workflows/Deferred Smart Routing|Deferred Smart Routing]]

## Standing Reminders

- Strategy alpha remains central.
- Approval is not execution unless a narrow action endpoint consumes it.
- `consumption_pending` approval truth means a submitted order already exists and approval reconciliation must be finished or inspected; it is not permission to submit again.
- Submitted-order handoff approval does not bypass readiness or submit gates.
- Preview/readiness approval is separate from submitted-order authorization.
- Target-choice conversion is not readiness and not submission.
- `SubmittedOrder` remains post-submit exchange/account truth.
- Phase 8.0 is observability/manual-resolution inspection, not smart routing.
- Phase 8.0.2 is a truth-surface hotfix only; Strategy Validation can start after acceptance while Phase 8.1 remains deferred.
- Manual-resolution inspection must not silently resolve venue or approval truth.
- Future agents must update their own coordination row instead of overwriting another agent's work.
