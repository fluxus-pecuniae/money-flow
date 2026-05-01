# Money Flow Command Center

This is the Obsidian brain for Money Flow. Start with [[00_Money_Flow_Command_Center|00 Money Flow Command Center]] for the required short entrypoint.

Repo operational truth still lives one level up in the repo docs: `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`. Strategic project memory now lives in [[Project_Memory/money_flow_project_memory|Project Memory]] inside this vault; the repo-root `money_flow_project_memory.md` is only a pointer.

## Start Here

- [[00 Maps/Current State Dashboard|Current State Dashboard]] - what Money Flow is today.
- [[00 Maps/System Map|System Map]] - the platform layers and how they connect.
- [[00 Maps/Workflow Map|Workflow Map]] - the current strategy to submitted-order path.
- [[00 Maps/Component Map|Component Map]] - landing page for every major subsystem.
- [[40 Operations/Future Work Roadmap|Future Work Roadmap]] - what remains deferred.
- [[40 Operations/Phase 8 Focus|Phase 8 Focus]] - current operator-control phase context and Phase 8.1 handoff.
- [[01_Current_Phase|Current Phase]] - current phase purpose and boundaries.
- [[05_Agent_Coordination|Agent Coordination]] - active agent/subagent work and handoffs.
- [[90 Reference/Glossary|Glossary]] - project language in one place.

## Current Truth

- Current branch observed: `phase-7.6`.
- Current implemented posture after Phase 7.6: Phase 7 is accepted complete, with four narrow approval-consuming hooks and closeout safety coverage.
- Money Flow is a Python/FastAPI strategy platform with Money Flow as the first strategy family.
- The platform already has mandate-aware planning, risk boundaries, multi-venue execution substrate, non-executing routing assessment/audit/recommendation, explicit recommendation acceptance, target-choice conversion, readiness, explicit gated submitted-order handoff, routed lifecycle inspection, dry-run automation plans, approval gates, approval-gated action hooks through submitted-order handoff, `consumption_pending` approval truth, and Phase 7.6 no-SOR closeout tests.
- Phase 8.0 is implemented as operator-grade observability and manual-resolution inspection only.
- Phase 8.0.1 cleaned the Obsidian memory / working-tree baseline without product behavior changes.

## What It Is Not Yet

- Not full smart order routing.
- Not best-binding selection.
- Not CBBO.
- Not fanout or split execution.
- Not automatic target reselection.
- Not a route executor.
- Not broad auto-submit.
- Not a production dashboard UI.

## The Main Mental Model

```text
StrategyDecision
-> MandateDesiredTrade
-> RiskEvaluation
-> RoutingAssessment
-> RouteReadinessAudit
-> RoutingTargetRecommendation
-> RoutingTargetChoice
-> OrderIntent
-> PreparedVenueOrder
-> ExecutionReadinessAssessment
-> SubmittedOrder
-> Lifecycle / actionability / reconciliation inspection
```

The Phase 7 brain sits above this path:

```text
RoutingAutomationPolicy
-> dry-run plan
-> approval gate
-> approval-gated recommendation acceptance
-> approval-gated target-choice conversion
-> approval-gated preview/readiness inspection
-> approval-gated submitted-order handoff
-> Phase 7.6 closeout safety proof
```

## Main Landing Pages

- [[30 Strategy/Product North Star|Product North Star]]
- [[30 Strategy/Money Flow Strategy Lab|Money Flow Strategy Lab]]
- [[10 Components/Domain Model|Domain Model]]
- [[10 Components/Runtime and Config|Runtime and Config]]
- [[10 Components/API Control Plane|API Control Plane]]
- [[10 Components/Market Data and Indicators|Market Data and Indicators]]
- [[10 Components/Strategy Engine|Strategy Engine]]
- [[10 Components/Planning and Risk|Planning and Risk]]
- [[10 Components/Routing Service|Routing Service]]
- [[10 Components/Execution Service|Execution Service]]
- [[10 Components/Exchange Adapters|Exchange Adapters]]
- [[10 Components/Database and Migrations|Database and Migrations]]
- [[10 Components/Tests and Validation|Tests and Validation]]
- [[20 Workflows/Current Routed Workflow|Current Routed Workflow]]
- [[20 Workflows/Approval Gated Recommendation Acceptance|Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Execution Lifecycle|Execution Lifecycle]]
- [[20 Workflows/Manual Routed Flow Harness|Manual Routed Flow Harness]]
- [[20 Workflows/Deferred Smart Routing|Deferred Smart Routing]]
- [[40 Operations/Operational Memory|Operational Memory]]
- [[40 Operations/Phase 8 Focus|Phase 8 Focus]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[40 Operations/Known Issues Index|Known Issues Index]]
- [[40 Operations/Phase 7 Focus|Phase 7 Focus]]
- [[90 Reference/Canonical Repo Docs|Canonical Repo Docs]]
- [[90 Reference/File Ownership Quick Reference|File Ownership Quick Reference]]

## Operating Rule

Use this vault to see the shape of the project quickly and coordinate long-horizon work. When code, tests, or repo docs disagree with a note here about implemented behavior, the repo wins and the note should be corrected.
