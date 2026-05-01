# Routing Service

Up: [[00 Maps/Component Map]]

## Path

- `services/routing/service.py`

## Current Role

Routing is the deepest and most actively phased layer. It handles non-executing candidate assessment, route-readiness audit, controlled recommendation, target-choice creation, target-choice conversion, automation planning, approval records, and the Phase 7.2 approval-gated recommendation acceptance hook.

## Implemented Stack

- Phase 5.0: routing assessments.
- Phase 5.1: target-choice audit records.
- Phase 5.2: target-choice to one child intent.
- Phase 5.10.1: route-readiness/data-sufficiency audit.
- Phase 6.0: non-executing routing target recommendation.
- Phase 6.1: optional explicit binding-priority recommendation.
- Phase 6.2: explicit recommendation acceptance into target choice.
- Phase 6.3: accepted target-choice conversion.
- Phase 6.9: read-only routed workflow inspection.
- Phase 7.0: automation policy and dry-run plans.
- Phase 7.1: durable approvals.
- Phase 7.1.1: expiry/stale-lineage/scope uniqueness.
- Phase 7.1.2: approvable-step truth.
- Phase 7.2 / 7.2.1: approval-gated recommendation acceptance into target choice only.

## Core Non-Goals

- No best-binding selection.
- No price/quality scoring.
- No CBBO.
- No fanout.
- No route executor.
- No target reselection.
- No auto-submit.

## Related Notes

- [[20 Workflows/Current Routed Workflow]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Phase 7 Focus]]
