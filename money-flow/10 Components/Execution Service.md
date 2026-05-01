# Execution Service

Up: [[00 Maps/Component Map]]

## Path

- `services/execution/service.py`

## Current Role

Execution handles child-intent preparation, venue-native previews, execution readiness, explicit submit, submitted-order persistence, lifecycle/actionability, recovery, cancel/amend where supported, reconciliation, and routed lifecycle context.

## Implemented For Routed Flow

- Recommendation-backed child intents can use existing preview/readiness paths.
- Readiness revalidates source recommendation, audit, selected target, quote freshness, binding/account/symbol truth, and routed order-shape policy.
- Submitted-order handoff is explicit and gated.
- Submit lease blocks concurrent submits for the same child intent before adapter submission.
- `adapter_submit_persistence_unknown` and `adapter_submit_may_have_started` are terminal uncertainty states requiring manual reconciliation.
- Routed lifecycle, actionability, recovery, reconciliation, and lifecycle events expose read-only routed context.

## Boundaries

- `SubmittedOrder` is post-submit truth.
- Venue-private open orders are not platform submitted orders.
- Same-target retry remains conservative and selected-account scoped.
- No cross-binding or cross-venue recovery exists.

## Related Notes

- [[20 Workflows/Execution Lifecycle]]
- [[10 Components/Exchange Adapters]]
- [[20 Workflows/Current Routed Workflow]]
