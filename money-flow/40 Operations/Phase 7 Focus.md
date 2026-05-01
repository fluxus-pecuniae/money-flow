# Phase 7 Focus

Up: [[Money Flow Command Center]]

## Phase 7 Theme

Controlled automation around the already-built single-target recommendation-backed path.

Not SOR. Not fanout. Not auto-submit.

Phase 7 is accepted complete as of Phase 7.6.

## Completed In Phase 7 So Far

- Phase 7.0: dry-run automation plans over existing routed workflow records.
- Phase 7.1: durable approval records and reversible gates.
- Phase 7.1.1: approvals are expiry-safe, stale-lineage-aware, and active-scope unique.
- Phase 7.1.2: approvals can only be created or appear valid for currently approvable policy states.
- Phase 7.2: approval-gated recommendation acceptance into target choice only.
- Phase 7.2.1: acceptance and approval consumption happen atomically.
- Phase 7.3: Obsidian becomes the required strategic-memory / coordination layer, and a valid `target_choice_conversion` approval may convert one target choice into one child intent.
- Phase 7.3.1: target-choice conversion negative coverage hardens disabled/blocked/deferred/already-satisfied and wrong-lineage cases.
- Phase 7.4: a valid `prepared_order_preview_and_readiness` approval may run preview/readiness inspection for one exact child intent.
- Phase 7.5: a valid `submitted_order_handoff` approval may call the existing explicit submit path for one already-ready child intent.
- Phase 7.5.1: post-submit approval-consumption failure becomes `consumption_pending` instead of misleading clean-active truth.
- Phase 7.6: closeout regression proves the full chain remains exact-lineage-bound, same-target, no-SOR, and distinct across dry-run, approval, admin consume, action execution, readiness, and submitted-order handoff.

## Next Likely Question

Can Phase 8.0 make the accepted chain easier to inspect, debug, reconcile, and manually manage without adding new trading actions or routing intelligence?

## Guardrails

- Dry-run remains first-class.
- Operator approval remains first-class.
- Generic approval consume remains administrative only.
- Action hooks must validate current lineage.
- No child-intent fanout.
- No preview/readiness automation unless explicitly scoped.
- No new action stages after submitted-order handoff.
- No route executor.
- No ranking/scoring.
- No CBBO.
- No target reselection.
- No auto-submit.

## Related Notes

- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[10 Components/Routing Service]]
- [[40 Operations/Future Work Roadmap]]
- [[40 Operations/Phase 8 Focus]]
