# Operational Memory

Up: [[Money Flow Command Center]]

## Canonical Repo Memory

The required operational docs are:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `money-flow/Project_Memory/money_flow_project_memory.md` as strategic context

See [[90 Reference/Canonical Repo Docs]].

## Working Rule

Before substantial repo work, read the memory. After code changes, update the operational docs. Keep implemented behavior and future behavior separate.

## Vault Rule

This Obsidian vault is now the strategic project brain. It stores founder intent, long-horizon memory, decisions, current phase context, and cross-agent coordination. It does not replace the repo operational docs or changelog.

## Current Important Memory Facts

- Current implemented line includes accepted Phase 8.0.1.
- Phase 7.3 integrated this Obsidian workflow into agent rules and added approval-gated target-choice conversion only.
- Phase 7.4 through Phase 7.5 added preview/readiness and submitted-order handoff hooks as separate approval-consuming actions.
- Phase 7.5.1 added `consumption_pending` approval truth.
- Phase 7.6 closed Phase 7 with safety regression and no production behavior change.
- Phase 8.0 added read-only operator observability/manual-resolution inspection, still below smart routing.
- Phase 8.0.1 cleaned the Obsidian memory baseline and working tree without product behavior changes.
- Approval is not execution.
- Recommendation is not action.
- SubmittedOrder is post-submit truth.
- Venue-private state is not platform submitted-order identity.
- Inspection is not manual resolution unless an explicit audited marker endpoint is designed.

## Related Notes

- [[00 Maps/Current State Dashboard]]
- [[40 Operations/Known Issues Index]]
- [[40 Operations/Future Work Roadmap]]
