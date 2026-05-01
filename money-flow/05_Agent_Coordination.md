# Agent Coordination

Agents must create or update their own row before substantial work and update it after work. Do not overwrite another agent's row unless there is an agreed handoff.

## Status Values

- `planned`
- `active`
- `blocked`
- `done`

## Active Work

| agent | task / phase | expected files | status | started_at_utc | updated_at_utc | notes / warnings | handoff summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | Phase 7.3 Obsidian workflow + approval-gated target-choice conversion | `AGENTS.md`, `money-flow/`, `services/routing/service.py`, `core/domain/models.py`, `core/interfaces/services.py`, `core/schemas/api.py`, `apps/api/app/api/routes.py`, tests, repo docs | done | 2026-05-01T05:39:34Z | 2026-05-01T05:58:03Z | Preserve same-target boundary; no preview/readiness/submission automation. | Obsidian workflow integrated; target-choice conversion approval hook added; focused and full non-migration tests passed. |

## Coordination Rules

- Record active work before touching substantial files.
- If two agents need the same file, record the conflict here before editing.
- Keep rows append-friendly; update only your own row unless an explicit handoff is agreed.
- Record blockers instead of silently overwriting another agent's changes.
- Repo operational docs remain code-state truth; this note coordinates people and agents.
