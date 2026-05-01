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
| Codex | Phase 7.3.1 target-choice conversion negative-test hardening | `tests/test_phase73_approval_gated_target_choice_conversion.py`, `CHANGELOG.md`, `TODO.md`, Obsidian current phase/coordination notes | done | 2026-05-01T06:39:00Z | 2026-05-01T06:46:04Z | Test-hardening only; no service behavior, preview/readiness automation, or submission automation changed. | Added disabled/blocked/deferred/already-satisfied and wrong recommendation/audit/desired-trade lineage negative tests; focused, approval regression, adjacent conversion/order-shape, operational docs, and full non-migration suites passed. |
| Codex | Phase 7.4 approval-gated prepared-order preview/readiness hook | `services/routing/service.py`, execution service helpers if needed, `core/domain/models.py`, `core/interfaces/services.py`, `core/schemas/api.py`, `apps/api/app/api/routes.py`, `tests/test_phase74_approval_gated_preview_readiness.py`, repo docs, Obsidian current phase/coordination notes | done | 2026-05-01T07:08:50Z | 2026-05-01T07:41:13Z | Preserve exact child-intent lineage; no submitted-order handoff, exchange submit, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit. | Implemented approval-gated preview/readiness endpoint and service hook; focused, approval-regression, adjacent routed readiness/conversion/API, operational-doc, and full non-migration suites passed. |
| Codex | Phase 7.5 approval-gated submitted-order handoff hook | `services/routing/service.py`, `core/domain/models.py`, `core/interfaces/services.py`, `core/schemas/api.py`, `apps/api/app/api/routes.py`, `tests/test_phase75_approval_gated_submission_handoff.py`, repo docs, Obsidian current phase/decision/coordination notes | done | 2026-05-01T08:14:00Z | 2026-05-01T08:49:19Z | Reused existing explicit submit path and submit lease/uncertainty guards; no route executor, broad auto-submit, fanout, ranking/scoring, CBBO, target reselection, cross-venue retry, or new exchange behavior. | Implemented approval-gated `submitted_order_handoff` hook and API; focused, automation-regression, routed closeout, API, operational-doc, full non-migration, migration-smoke, and review-bundle checks passed. |

## Coordination Rules

- Record active work before touching substantial files.
- If two agents need the same file, record the conflict here before editing.
- Keep rows append-friendly; update only your own row unless an explicit handoff is agreed.
- Record blockers instead of silently overwriting another agent's changes.
- Repo operational docs remain code-state truth; this note coordinates people and agents.
