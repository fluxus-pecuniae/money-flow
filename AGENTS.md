# AGENTS

## Purpose

This repository uses explicit operational-memory files plus an Obsidian project brain. They are part of the normal workflow, not optional cleanup.

Before changing code, future agents must read the current repo memory and the Obsidian brain. After changing code, future agents must update the repo memory and relevant Obsidian notes to match the new state.

Required operational docs:

- [`AGENTS.md`](AGENTS.md)
- [`CHANGELOG.md`](CHANGELOG.md)
- [`REPO_TREE.md`](REPO_TREE.md)
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- [`TODO.md`](TODO.md)

Required Obsidian strategic brain:

- [`money-flow/00_Money_Flow_Command_Center.md`](money-flow/00_Money_Flow_Command_Center.md)
  - Required strategic-memory entrypoint before substantial work.
- [`money-flow/01_Current_Phase.md`](money-flow/01_Current_Phase.md)
  - Current phase purpose, accepted baseline, and hard boundaries.
- [`money-flow/05_Agent_Coordination.md`](money-flow/05_Agent_Coordination.md)
  - Cross-agent/subagent coordination and active work rows.
- [`money-flow/Project_Memory/money_flow_project_memory.md`](money-flow/Project_Memory/money_flow_project_memory.md)
  - Full long-horizon strategic project memory.
  - Required pre-task context.
  - Maintained as the Obsidian strategic-memory source.

Compatibility pointer:

- [`money_flow_project_memory.md`](money_flow_project_memory.md)
  - Repo-root pointer only.
  - Not the canonical full strategic memory source.

## Pre-Task Workflow

Before starting substantial work, agents must:

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`CHANGELOG.md`](CHANGELOG.md).
3. Read [`REPO_TREE.md`](REPO_TREE.md).
4. Read [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
5. Read [`TODO.md`](TODO.md).
6. Read canonical docs that matter to the task, especially [`README.md`](README.md), [`docs/architecture.md`](docs/architecture.md), and [`docs/strategy.md`](docs/strategy.md) for platform phases.
7. Read [`money-flow/00_Money_Flow_Command_Center.md`](money-flow/00_Money_Flow_Command_Center.md).
8. Read [`money-flow/01_Current_Phase.md`](money-flow/01_Current_Phase.md).
9. Read [`money-flow/Project_Memory/money_flow_project_memory.md`](money-flow/Project_Memory/money_flow_project_memory.md) as strategic context.
10. Check [`money-flow/05_Agent_Coordination.md`](money-flow/05_Agent_Coordination.md) for active work/conflicts.
11. Confirm they understand the current repo state before changing code.

Minimum confirmation means:

- current implemented phase and scope are understood
- known unresolved issues relevant to the task are understood
- deferred work boundaries are understood
- strategic context from [`money-flow/Project_Memory/money_flow_project_memory.md`](money-flow/Project_Memory/money_flow_project_memory.md) is understood
- active agent/subagent coordination state is understood
- the repo areas likely to be touched are understood

## During-Task Coordination

For substantial work, agents must:

1. Add or update their own row in [`money-flow/05_Agent_Coordination.md`](money-flow/05_Agent_Coordination.md) before changing overlapping files.
2. List the phase/task, expected files, status, timestamps, warnings, and handoff summary.
3. Avoid overwriting another agent/subagent row except for an agreed handoff.
4. Record conflicts or suspected overlap instead of silently resolving them.
5. Keep repo operational docs and Obsidian notes consistent without treating Obsidian as a substitute for the changelog.

## Post-Task Workflow

Before finishing, agents must:

1. Update [`CHANGELOG.md`](CHANGELOG.md).
2. Update [`REPO_TREE.md`](REPO_TREE.md) if structure or ownership changed.
3. Update [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) when relevant.
4. Update [`TODO.md`](TODO.md) when relevant.
5. Re-read the touched sections of all affected operational docs.
6. Update relevant Obsidian notes:
   - [`money-flow/01_Current_Phase.md`](money-flow/01_Current_Phase.md) for phase status and next phase context.
   - [`money-flow/03_Decision_Log.md`](money-flow/03_Decision_Log.md) for lasting architecture/founder decisions.
   - [`money-flow/05_Agent_Coordination.md`](money-flow/05_Agent_Coordination.md) for status and handoff.
   - [`money-flow/Project_Memory/money_flow_project_memory.md`](money-flow/Project_Memory/money_flow_project_memory.md) when the phase changes long-term strategic context.
7. Re-read the touched sections of affected Obsidian notes.
8. Explicitly validate that repo docs and Obsidian context still match repo state.
9. After each completed phase, create a clean handoff ZIP in `/Users/tercirafael/` using [`scripts/create_review_bundle.py`](scripts/create_review_bundle.py). Use `.archiveignore` as the exclusion source so `.env`, local virtualenvs, caches, generated archives, database/socket data, Obsidian app workspace state, and other non-review artifacts are not included. Do not hand-build archives that may include keys or unnecessary local files.

Minimum validation means:

- required operational docs still exist
- required Obsidian brain notes still exist
- new or renamed files are reflected in repo memory
- deferred work remains clearly marked
- implemented vs future behavior is described truthfully
- Obsidian strategic memory and coordination notes are current for substantial phase work
- the phase handoff ZIP was created from the review-bundle workflow when a phase was completed

## Changelog Rules

Use [`CHANGELOG.md`](CHANGELOG.md) as the single canonical changelog.

Each entry must include:

- `version`
- `recorded_at_utc`
- `scope`
- `intent`
- `affected_files`
- `validation_performed`

Version format:

- `vYYYY.MM.DD.NNN`

Timestamp format:

- `2026-03-30T13:02:45Z`

If an entry was reconstructed from repo history instead of written at the time, mark it clearly as reconstructed.

## Operational Guidance

- Use repo-relative paths in operational docs.
- Keep operational docs concise, structured, and truthful.
- Do not describe future phases as already implemented.
- Do not leave material repo changes undocumented.
- If a task intentionally defers work, record that in [`TODO.md`](TODO.md) or [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) when appropriate.
- Repo docs remain the source of truth for implemented code state.
- Obsidian is the source of truth for long-horizon project memory, founder intent, decisions, and cross-agent coordination.
- Obsidian strategic memory is not a substitute for [`CHANGELOG.md`](CHANGELOG.md), [`REPO_TREE.md`](REPO_TREE.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), or [`TODO.md`](TODO.md).
