# Phase 7 Focus

Up: [[Money Flow Command Center]]

## Phase 7 Theme

Controlled automation around the already-built single-target recommendation-backed path.

Not SOR. Not fanout. Not auto-submit.

## Completed In Phase 7 So Far

- Phase 7.0: dry-run automation plans over existing routed workflow records.
- Phase 7.1: durable approval records and reversible gates.
- Phase 7.1.1: approvals are expiry-safe, stale-lineage-aware, and active-scope unique.
- Phase 7.1.2: approvals can only be created or appear valid for currently approvable policy states.
- Phase 7.2: approval-gated recommendation acceptance into target choice only.
- Phase 7.2.1: acceptance and approval consumption happen atomically.
- Phase 7.3: Obsidian becomes the required strategic-memory / coordination layer, and a valid `target_choice_conversion` approval may convert one target choice into one child intent.

## Next Likely Question

Can the next phase safely add approval-gated preview/readiness without weakening current lineage truth or creating hidden automation?

## Guardrails

- Dry-run remains first-class.
- Operator approval remains first-class.
- Generic approval consume remains administrative only.
- Action hooks must validate current lineage.
- No child-intent fanout.
- No preview/readiness automation unless explicitly scoped.
- No submitted-order handoff automation.
- No route executor.
- No ranking/scoring.
- No CBBO.
- No target reselection.
- No auto-submit.

## Related Notes

- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[10 Components/Routing Service]]
- [[40 Operations/Future Work Roadmap]]
