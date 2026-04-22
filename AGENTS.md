# AGENTS

## Purpose

This repository uses explicit operational-memory files. They are part of the normal workflow, not optional cleanup.

Before changing code, future agents must read the current repo memory. After changing code, future agents must update the repo memory to match the new state.

Required operational docs:

- [`AGENTS.md`](AGENTS.md)
- [`CHANGELOG.md`](CHANGELOG.md)
- [`REPO_TREE.md`](REPO_TREE.md)
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- [`TODO.md`](TODO.md)

Required read-only strategic memory:

- [`money_flow_project_memory.md`](money_flow_project_memory.md)
  - Required pre-task context.
  - Read-only in normal phase work.
  - Maintained only by the architecture review team unless explicitly directed otherwise.

## Pre-Task Workflow

Before starting substantial work, agents must:

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`CHANGELOG.md`](CHANGELOG.md).
3. Read [`REPO_TREE.md`](REPO_TREE.md).
4. Read [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
5. Read [`TODO.md`](TODO.md).
6. Read [`money_flow_project_memory.md`](money_flow_project_memory.md) as read-only strategic context.
7. Confirm they understand the current repo state before changing code.

Minimum confirmation means:

- current implemented phase and scope are understood
- known unresolved issues relevant to the task are understood
- deferred work boundaries are understood
- strategic context from [`money_flow_project_memory.md`](money_flow_project_memory.md) is understood
- the repo areas likely to be touched are understood

## Post-Task Workflow

Before finishing, agents must:

1. Update [`CHANGELOG.md`](CHANGELOG.md).
2. Update [`REPO_TREE.md`](REPO_TREE.md) if structure or ownership changed.
3. Update [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) when relevant.
4. Update [`TODO.md`](TODO.md) when relevant.
5. Re-read the touched sections of all affected operational docs.
6. Explicitly validate that docs still match repo state.
7. After each completed phase, create a clean handoff ZIP in `/Users/tercirafael/` using [`scripts/create_review_bundle.py`](scripts/create_review_bundle.py). Use `.archiveignore` as the exclusion source so `.env`, local virtualenvs, caches, generated archives, database/socket data, and other non-review artifacts are not included. Do not hand-build archives that may include keys or unnecessary local files.

Minimum validation means:

- required operational docs still exist
- new or renamed files are reflected in repo memory
- deferred work remains clearly marked
- implemented vs future behavior is described truthfully
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
