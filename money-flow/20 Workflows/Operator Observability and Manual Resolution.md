# Operator Observability and Manual Resolution

Up: [[00 Maps/Workflow Map]]

## Status

This is the implemented Phase 8.0 workflow.

The current codebase has read-only routed workflow aggregation, approval inspection, and Phase 8.0 operator summary inspection that makes those surfaces more operator-grade, structured, and reconciliation-aware.

## Current Baseline

Phase 7.6 accepted the controlled approval-gated automation chain:

```text
RoutingTargetRecommendation
-> RoutingTargetChoice
-> OrderIntent
-> PreparedVenueOrder preview
-> ExecutionReadinessAssessment
-> SubmittedOrder handoff
```

Each action stage consumes its own current-lineage approval. The stages remain separate from dry-run plans, approval creation, generic administrative consumption, readiness truth, submit leases, and exchange/account truth.

## Phase 8.0 Implemented Target

The operator should be able to inspect one desired trade and see:

- desired trade state
- routing assessment and route-readiness audit state
- recommendation and target-choice state
- child intent state
- preview/readiness state
- submitted-order state
- approval state by stage
- blocking reasons
- uncertainty reasons
- manual-resolution requirements
- submit lease/concurrency facts
- next safe manual operator action, when knowable

## Manual-Resolution Issues To Surface

The inspection layer should make these states visible without resolving them automatically:

- `consumption_pending`
- `adapter_submit_may_have_started`
- `adapter_submit_persistence_unknown`
- submit lease active or terminal-uncertain
- stale-lineage approval
- expired approval
- revoked approval
- blocked route-readiness audit
- blocked recommendation
- blocked readiness
- blocked submit gate

Each issue should answer:

- what artifact is affected
- what the system knows
- what the system does not know
- what an operator should check
- what is explicitly unsafe
- what action may become safe after manual review

## Non-Executing Rule

Inspection must not:

- create a target choice
- create a child intent
- run preview/readiness
- consume an approval
- create a submitted order
- call an adapter
- retry, cancel, or amend an order
- clear uncertainty without explicit operator provenance

## Related Notes

- [[40 Operations/Phase 8 Focus]]
- [[20 Workflows/Current Routed Workflow]]
- [[20 Workflows/Deferred Smart Routing]]
- [[10 Components/API Control Plane]]
- [[10 Components/Routing Service]]
