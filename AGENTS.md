# AGENTS

## Purpose

This repository uses explicit operational-memory files plus an Obsidian project brain. They are part of the normal workflow, not optional cleanup.

Before changing code, future agents must read the current repo memory and the Obsidian brain. After changing code, future agents must update the repo memory and relevant Obsidian notes to match the new state.

Required operational docs:

- [`AGENTS.md`](AGENTS.md)
- [`CHANGELOG.md`](CHANGELOG.md) (recent rolling window)
- [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md) (full older history)
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
- Current track maps, when relevant:
  - [`money-flow/00 Maps/Current State Dashboard.md`](money-flow/00%20Maps/Current%20State%20Dashboard.md)
  - [`money-flow/00 Maps/Strategy Validation Map.md`](money-flow/00%20Maps/Strategy%20Validation%20Map.md)
  - [`money-flow/00 Maps/UAT Roadmap.md`](money-flow/00%20Maps/UAT%20Roadmap.md)

Compatibility pointer:

- [`money_flow_project_memory.md`](money_flow_project_memory.md)
  - Repo-root pointer only.
  - Not the canonical full strategic memory source.

## Canonical Current-Truth Registry

[`CURRENT_TRUTH.md`](CURRENT_TRUTH.md) is the single source of truth for active lanes, timeframes, symbols, testnet eligibility, and approval boundaries. It is generated from Python anchors in `services/paper_runtime/pt_rt1.py` and `core/config/settings.py` and kept in sync by `tests/test_current_truth_registry.py`.

**Implementation prompts must reference `CURRENT_TRUTH.md` and enforce its boundaries instead of re-embedding lane IDs, timeframes, or approval status inline.** If the on-disk registry needs updating after an anchor change, run:

```bash
python scripts/export_current_truth.py
```

Then re-render the human sections of `CURRENT_TRUTH.md` to match. Never hand-edit the Machine Block inside `CURRENT_TRUTH.md`.

## Pre-Task Workflow

DOC-LEAN1 reading discipline: read the lean current-state set every task;
consult the heavier logs only when the task actually needs them. This trims
mandatory READS only — the post-task UPDATE list below is unchanged.

Before starting substantial work, agents must read the **lean current-state set**:

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`CURRENT_TRUTH.md`](CURRENT_TRUTH.md) — the canonical current state (active lanes, timeframes, symbols, testnet eligibility, approval boundaries).
3. Read [`money-flow/01_Current_Phase.md`](money-flow/01_Current_Phase.md).
4. Read the recent [`CHANGELOG.md`](CHANGELOG.md) (a small rolling window after DOC-LEAN1).
5. Check [`money-flow/05_Agent_Coordination.md`](money-flow/05_Agent_Coordination.md) for active work/conflicts.
6. Read the specific component doc(s) relevant to the task (for example [`docs/architecture.md`](docs/architecture.md) / [`docs/strategy.md`](docs/strategy.md) for platform phases, [`apps/dashboard/DESIGN.md`](apps/dashboard/DESIGN.md) for dashboard work, or the relevant `docs/<phase>_*.md`).
7. Confirm they understand the current repo state before changing code.

Consult **on demand when relevant to the task** (not mandatory full reads):

- [`REPO_TREE.md`](REPO_TREE.md) — structure/ownership lookups.
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — when touching an area with known issues.
- [`TODO.md`](TODO.md) — when picking up or deferring scoped work.
- [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md) — older history beyond the recent window.
- [`README.md`](README.md) and the `money-flow/00 Maps/` track maps (such as [`money-flow/00 Maps/UAT Roadmap.md`](money-flow/00%20Maps/UAT%20Roadmap.md) or [`money-flow/00 Maps/Strategy Validation Map.md`](money-flow/00%20Maps/Strategy%20Validation%20Map.md)).
- [`money-flow/00_Money_Flow_Command_Center.md`](money-flow/00_Money_Flow_Command_Center.md) and [`money-flow/Project_Memory/money_flow_project_memory.md`](money-flow/Project_Memory/money_flow_project_memory.md) — long-horizon strategic context for substantial phase work.

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
2. Add new in-progress rows under `Active Work`; list the phase/task, expected files, status, timestamps, warnings, and handoff summary.
3. Avoid overwriting another agent/subagent row except for an agreed handoff.
4. Record conflicts or suspected overlap instead of silently resolving them.
5. Keep repo operational docs and Obsidian notes consistent without treating Obsidian as a substitute for the changelog.
6. Do not create duplicate command centers or competing current-phase notes.

## Codex Subagents

Project-scoped Codex subagents live in `.codex/agents/`.

Current subagents:

- `runtime_reviewer`
- `dashboard_reviewer`
- `quant_reviewer`

They are read-only by default and should be used for bounded review/triage, not parallel write-heavy implementation. See [`docs/codex_subagents_money_flow_workflow.md`](docs/codex_subagents_money_flow_workflow.md) for invocation examples and conflict-avoidance rules.

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
10. Mark your coordination row complete by moving/updating it under `Finished Work` with status `done` or `blocked`; do not leave completed work marked active.

Minimum validation means:

- required operational docs still exist
- required Obsidian brain notes still exist
- new or renamed files are reflected in repo memory
- deferred work remains clearly marked
- implemented vs future behavior is described truthfully
- Obsidian strategic memory and coordination notes are current for substantial phase work
- the phase handoff ZIP was created from the review-bundle workflow when a phase was completed

## Changelog Rules

The changelog is split into a recent rolling window plus a full archive (DOC-LEAN1):

- [`CHANGELOG.md`](CHANGELOG.md) holds the **recent rolling window** (newest-first). All new entries are written here.
- [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md) holds the **full older history**, rotated out verbatim (newest-first; nothing deleted).
- **Both are canonical** — recent window + archive together are the complete changelog, not competing changelogs.
- When `CHANGELOG.md` exceeds ~25 entries, roll the oldest entries verbatim into the top of the archive's entry list as part of the post-task update.

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
- Obsidian strategic memory is not a substitute for [`CHANGELOG.md`](CHANGELOG.md) / [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md), [`REPO_TREE.md`](REPO_TREE.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), or [`TODO.md`](TODO.md).
