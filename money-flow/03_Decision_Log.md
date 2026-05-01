# Decision Log

Append entries only. Do not rewrite prior decisions except to add a dated correction.

## 2026-05-01T05:39:34Z - Phase 7.3 - Obsidian Becomes Strategic Brain

- `decision`: Move full strategic project memory into the Obsidian vault and keep the repo-root `money_flow_project_memory.md` only as a compatibility pointer.
- `why`: Repo operational docs should stay concise and code-state focused, while founder intent, long-horizon memory, phase context, and cross-agent coordination need a richer project brain.
- `rejected_alternatives`: Keeping full strategic memory at repo root; treating Obsidian as a replacement for `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, or `TODO.md`.
- `follow_up_implications`: Future agents must read the Obsidian command center, current phase note, project memory, and coordination note before substantial work, then update relevant Obsidian notes after substantial work.

## 2026-05-01T05:58:03Z - Phase 7.3 - Approval-Gated Target-Choice Conversion Only

- `decision`: Add only the `target_choice_conversion` approval-consuming action hook for Phase 7.3.
- `why`: Phase 7.2/7.2.1 already proved approval-gated recommendation acceptance. The next safe automation step is converting the exact approved target choice into one child intent while keeping preview/readiness and submission explicit and separate.
- `rejected_alternatives`: Automating preview/readiness in the same phase; automating submitted-order handoff; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future action hooks must continue to consume one current-lineage approval for one same-target stage and must preserve dry-run/manual policy truth plus no-downstream-artifact boundaries.

## 2026-05-01T07:28:41Z - Phase 7.4 - Approval-Gated Preview/Readiness Only

- `decision`: Add only the `prepared_order_preview_and_readiness` approval-consuming action hook for Phase 7.4.
- `why`: Phase 7.3 already proved approval-gated target-choice conversion. The next safe automation step is running existing preview/readiness inspection for the exact approved child intent while keeping submitted-order handoff explicit and separate.
- `rejected_alternatives`: Treating approval as readiness eligibility; automating submitted-order handoff; calling adapter submit; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future submitted-order automation must remain a separate phase and must consume its own current-lineage approval plus existing readiness, live/routed gates, and submit-lease uncertainty guards.

## 2026-05-01T08:41:37Z - Phase 7.5 - Approval-Gated Submitted-Order Handoff Only

- `decision`: Add only the `submitted_order_handoff` approval-consuming action hook for Phase 7.5.
- `why`: Phase 7.4 already proved approval-gated preview/readiness inspection. The next bounded step is submitting the exact already-ready child intent through the existing explicit submit path while keeping readiness, live/routed gates, adapter/account authorization, and submit-lease uncertainty protections authoritative.
- `rejected_alternatives`: Treating approval as a readiness override; adding a route executor; adding broad auto-submit; retrying or failing over to another target; adding ranking/scoring/fanout/CBBO/target reselection.
- `follow_up_implications`: Future phases should harden/close out operator inspection, regression, and concurrency/uncertainty observability before considering any broader automation.

## 2026-05-01T09:40:47Z - Phase 7.5.1 - Post-Submit Approval Consumption Truth

- `decision`: Represent submitted-order-created / approval-consumption-failed truth as `consumption_pending` on the approval record.
- `why`: A persisted `SubmittedOrder` is real exchange/account truth. If approval consumption fails after that point, leaving the approval clean-active would be misleading and could obscure which approval authorized the handoff.
- `rejected_alternatives`: Rolling back `SubmittedOrder` truth after submit persistence; treating the approval as clean active; adding a retry executor; submitting again to repair approval state.
- `follow_up_implications`: Future operator tooling can inspect `consumption_pending` approvals and complete or manually reconcile approval state without creating another submitted order.

## 2026-05-01T12:02:56Z - Phase 7.6 - Close Controlled Automation With Safety Proof

- `decision`: Close Phase 7 with end-to-end safety regression and docs alignment rather than adding another automation action hook.
- `why`: The full controlled chain now exists. Before broader automation, the project needs proof that the chain remains exact-lineage-bound, same-target, no-SOR, no-fanout, no-reselection, and distinct across dry-run, approval, administrative consumption, action execution, readiness, and submitted-order handoff.
- `rejected_alternatives`: Adding a route executor; adding smart routing or best-binding selection; adding fanout; adding target reselection; expanding broad auto-submit; treating generic administrative approval consumption as action execution.
- `follow_up_implications`: The next major phase should be architecture-reviewed and should prioritize operator-grade observability, reconciliation/manual-resolution, concurrency/serialization hardening, and dashboard/read-only inspection depth before any broader automation scope.

## 2026-05-01T12:59:46Z - Phase 8.0 Direction - Operator Observability Before SOR

- `decision`: Shape Phase 8.0 as operator-grade observability and manual-resolution inspection for the accepted Phase 7 controlled automation chain.
- `why`: The platform now has enough approval-gated workflow depth that operators need a structured way to inspect desired-trade state, approvals, readiness, submitted-order handoff, uncertainty, submit leases, and next safe manual action before any future smart-routing work.
- `rejected_alternatives`: Jumping directly into smart routing; adding best-binding selection, CBBO, ranking/scoring, fanout, target reselection, or route-executor behavior; auto-resolving uncertainty; treating operator acknowledgement as exchange/account truth.
- `follow_up_implications`: Phase 8.0 should default to read-only inspection. Manual-resolution marker mutation should be deferred or kept strictly append-only, actor-stamped, reason-coded, audited, and non-executing.

## 2026-05-01T13:20:57Z - Phase 8.0 - Read-Only Operator Summary

- `decision`: Add a read-only operator routed workflow summary by desired trade and defer manual-resolution marker mutation to a later phase.
- `why`: Operators need one structured view of workflow artifacts, approval/gate state, manual-resolution requirements, submitted-order safety, submit lease uncertainty, and next safe action before any broader routing or automation work.
- `rejected_alternatives`: Adding marker mutation in the first observability phase; auto-resolving `consumption_pending` or submit-lease uncertainty; attaching submit/cancel/amend/retry to inspection; introducing smart routing, ranking/scoring, CBBO, fanout, target reselection, or route executor behavior.
- `follow_up_implications`: Phase 8.1 can design explicit actor-stamped manual-resolution markers or administrative reconciliation flows, but those must remain separate from exchange/account truth and trading actions.

## 2026-05-01T14:19:39Z - Phase 8.0.1 - Accept Obsidian Memory Refresh As Baseline

- `decision`: Accept the dirty Obsidian full-project-memory refresh as intentional strategic-memory baseline, update stale "Phase 8.0 proposed" wording to implemented Phase 8.0 / cleanup Phase 8.0.1 truth, and keep the repo-root `money_flow_project_memory.md` as a pointer only.
- `why`: Phase 8.0 code was accepted, but the working tree remained dirty because the earlier Obsidian refresh had not been committed. Future agents need a clean baseline and current Obsidian context before Phase 8.1.
- `rejected_alternatives`: Reverting the full project-memory refresh; moving accepted strategic notes into drafts; leaving the working tree dirty; treating the root pointer as canonical full memory again.
- `follow_up_implications`: Phase 8.1 can start from a clean repo/Obsidian baseline. Repo operational docs remain code-state truth, and Obsidian remains strategic memory and coordination.

## 2026-05-01T15:04:52Z - Phase 8.0.2 - Active Submit Lease Blocks Operator Summary

- `decision`: Treat unexpired `active` child-intent submit leases as `submission_in_progress` blockers in the read-only operator summary's submission-safety and next-safe-action truth.
- `why`: The summary already surfaced active leases but could still report approval-gated submit as safe while a submit lease was in progress, which is unsafe operator guidance even though no trading behavior changed.
- `rejected_alternatives`: Converting expired pre-adapter active leases into terminal uncertainty; adding manual-resolution mutation; changing submit behavior; adding a new action stage.
- `follow_up_implications`: Strategy Validation can begin after this hotfix is accepted. Phase 8.1 remains deferred until manual-resolution marker semantics are explicitly scoped.

## 2026-05-01T17:40:40Z - SV1.0 - Validate Strategy Before More Routing Scope

- `decision`: Add Money Flow strategy validation as a separate research/backtest boundary instead of expanding routing or execution automation.
- `why`: Phase 7 and Phase 8.0 made the controlled execution chain inspectable and safe enough to pause routing expansion. The highest business uncertainty is whether Money Flow produces measurable edge after fees and slippage.
- `rejected_alternatives`: Adding smart routing, best-binding selection, new automation action hooks, strategy-rule optimization, paper trading, or live execution changes in SV1.0.
- `follow_up_implications`: SV1.x should review deterministic reports and deepen validation before strategy optimization or paper trading. Validation artifacts must remain separate from live `SubmittedOrder` and routing/execution truth.
