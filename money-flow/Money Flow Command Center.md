# Money Flow Command Center

This is the Obsidian brain for Money Flow. Start with [[00_Money_Flow_Command_Center|00 Money Flow Command Center]] for the required short entrypoint.

Repo operational truth still lives one level up in the repo docs: `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`. Strategic project memory now lives in [[Project_Memory/money_flow_project_memory|Project Memory]] inside this vault; the repo-root `money_flow_project_memory.md` is only a pointer.

## Start Here

- [[00 Maps/Current State Dashboard|Current State Dashboard]] - what Money Flow is today.
- [[00 Maps/System Map|System Map]] - the platform layers and how they connect.
- [[00 Maps/Workflow Map|Workflow Map]] - the current strategy to submitted-order path.
- [[00 Maps/Component Map|Component Map]] - landing page for every major subsystem.
- [[40 Operations/Future Work Roadmap|Future Work Roadmap]] - what remains deferred.
- [[01_Current_Phase|Current Phase]] - current phase purpose and boundaries.
- [[05_Agent_Coordination|Agent Coordination]] - active agent/subagent work and handoffs.
- [[90 Reference/Glossary|Glossary]] - project language in one place.

## Current Truth

- Current branch observed: `phase-7.3`.
- Current implemented posture after Phase 7.3 changes: Obsidian is the required strategic-memory / coordination layer, and approval-gated target-choice conversion can create or reuse one child `OrderIntent`.
- Money Flow is a Python/FastAPI strategy platform with Money Flow as the first strategy family.
- The platform already has mandate-aware planning, risk boundaries, multi-venue execution substrate, non-executing routing assessment/audit/recommendation, explicit recommendation acceptance, target-choice conversion, readiness, explicit gated submitted-order handoff, routed lifecycle inspection, dry-run automation plans, approval gates, and one approval-consuming action hook.
- Phase 7.3 added only one next narrow action hook: an active current-lineage `target_choice_conversion` approval can create or reuse one child `OrderIntent`.

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
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[40 Operations/Known Issues Index|Known Issues Index]]
- [[40 Operations/Phase 7 Focus|Phase 7 Focus]]
- [[90 Reference/Canonical Repo Docs|Canonical Repo Docs]]
- [[90 Reference/File Ownership Quick Reference|File Ownership Quick Reference]]

## Operating Rule

Use this vault to see the shape of the project quickly and coordinate long-horizon work. When code, tests, or repo docs disagree with a note here about implemented behavior, the repo wins and the note should be corrected.
