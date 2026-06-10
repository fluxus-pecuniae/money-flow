# DOC-LEAN1 — Changelog Rotation + Lean Pre-Task Reading

Docs/tooling only. No runtime, strategy, code-behavior, order, or approval
change. **No changelog history was lost** — older entries were archived
verbatim, not deleted.

## Why

`CHANGELOG.md` had grown to 800 KB / 9,257 lines / 292 entries, and the
AGENTS.md pre-task workflow made every agent read it — plus `REPO_TREE.md`
(238 KB), `KNOWN_ISSUES.md` (67 KB), and `TODO.md` (134 KB) — before any task.
That is expensive and unnecessary: the lean current state lives in
`CURRENT_TRUTH.md`, `01_Current_Phase.md`, and the recent changelog window.

## Must 1 — Rotation (verified lossless)

| File | Entries | Size |
| --- | ---: | ---: |
| `CHANGELOG.md` before | 292 | 800 KB / 9,257 lines |
| `CHANGELOG.md` after (recent window) | **20** (`v2026.06.10.006` … `v2026.06.08.002`) | 45 KB / 555 lines |
| `CHANGELOG_ARCHIVE.md` (new) | **272** (`v2026.06.08.001` … `v2026.04.06.017`) | 756 KB |

Programmatic verification performed at rotation time:

- entry-heading count across both files = **292** (20 + 272), none dropped;
- no version appears in both files (no duplicates);
- recent + archived version lists concatenated equal the original list in
  order; and
- the concatenated entry text of both files reproduces the original entry
  region **byte-for-byte** (verbatim archive).

`CHANGELOG.md` keeps its header + schema note and carries the archive pointer;
`CHANGELOG_ARCHIVE.md` carries the same schema note and points back at the
recent window. A new `tests/test_operational_docs.py` guard
(`test_changelog_archive_rotation_is_lossless_shape`) pins the shape: no
overlap, no shrink below 272 archived entries, newest-first continuity, and
the rolling cap.

## Must 2 — Rotation rule (AGENTS.md Changelog Rules)

"Single canonical changelog" replaced with: `CHANGELOG.md` holds the **recent
rolling window** (all new entries are written there); `CHANGELOG_ARCHIVE.md`
holds the **full older history** rotated out verbatim; **both are canonical**
— recent window + archive together are the complete changelog. When
`CHANGELOG.md` exceeds **~25 entries**, the oldest roll into the archive as
part of the post-task update (CI-enforced at 25 by the operational-docs
guard).

## Must 3 — Lean pre-task reading discipline (AGENTS.md Pre-Task Workflow)

Read **every task** (the lean current-state set):

1. `AGENTS.md`
2. `CURRENT_TRUTH.md` (canonical current state)
3. `money-flow/01_Current_Phase.md`
4. the recent `CHANGELOG.md` (now small)
5. `money-flow/05_Agent_Coordination.md` (active-work conflicts)
6. the specific component doc(s) relevant to the task

Consult **on demand when relevant to the task** (no longer mandatory full
reads): `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `CHANGELOG_ARCHIVE.md`,
`README.md` + the `00 Maps/` track maps, the Command Center, and Project
Memory.

**The post-task UPDATE list is unchanged** — agents still update CHANGELOG /
REPO_TREE / KNOWN_ISSUES / TODO / Obsidian after work. DOC-LEAN1 trims reads,
not writes.

## Must 4 — Guard updates (`tests/test_operational_docs.py`)

- `CHANGELOG_ARCHIVE.md` added to the existence list and to the
  stale-draft-reference guard.
- `test_changelog_has_versioned_entries` now also asserts the archive pointer
  and the ≤25-entry rolling cap (the rotation trigger is CI-enforced).
- New `test_changelog_archive_rotation_is_lossless_shape`: ≥272 archived
  entries, no entry in both files, no duplicates, newest-first continuity,
  archive points back at the recent window.
- `test_agents_references_required_operational_docs` asserts the lean-set
  wording, `CURRENT_TRUTH.md`, the rotation rule, and that "single canonical
  changelog" is gone.
- All 20 operational-docs tests green.

## Boundaries

Docs/tests only. No runtime mutation, no strategy-rule change, no
code-behavior change, no orders, no testnet behavior change, no production or
live approval. No history lost.
