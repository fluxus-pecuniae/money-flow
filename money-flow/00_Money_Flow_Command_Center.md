# Money Flow Command Center

This is the required Obsidian brain entrypoint for Money Flow agents.

## North Star

Money Flow is a mandate-driven, multi-venue trading platform where strategy alpha remains central. Routing and automation must serve the strategy workflow; they must not replace it with fake smart-routing or hidden execution behavior.

## Current Phase

- Current phase: `Phase 7.5.1`
- Purpose: harden approval-consumption truth after approval-gated submitted-order handoff.
- Current accepted action hooks before this phase: approval-gated recommendation acceptance, target-choice conversion, prepared-order preview/readiness inspection, and submitted-order handoff.

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

Phase 7.5.1 does not add a new automation transition. It only bounds the failure case where `SubmittedOrder` persistence succeeds but approval consumption fails afterward. Such approvals become `consumption_pending` and repeat calls must reuse the existing submitted order before completing or preserving approval reconciliation truth. The platform still must not automate target selection, recovery, route execution, target reselection, fanout, scoring, ranking, CBBO, best-binding selection, cross-venue retry, or broad auto-submit.

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
- [[20 Workflows/Deferred Smart Routing|Deferred Smart Routing]]

## Standing Reminders

- Strategy alpha remains central.
- Approval is not execution unless a narrow action endpoint consumes it.
- `consumption_pending` approval truth means a submitted order already exists and approval reconciliation must be finished or inspected; it is not permission to submit again.
- Submitted-order handoff approval does not bypass readiness or submit gates.
- Preview/readiness approval is separate from submitted-order authorization.
- Target-choice conversion is not readiness and not submission.
- `SubmittedOrder` remains post-submit exchange/account truth.
- Future agents must update their own coordination row instead of overwriting another agent's work.
