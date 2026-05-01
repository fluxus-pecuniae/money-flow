# Approval Gated Recommendation Acceptance

Up: [[00 Maps/Workflow Map]]

## Phase 7 Controlled Automation Truth

One active, non-expired, current-lineage `recommendation_acceptance` approval can accept the exact approved `RoutingTargetRecommendation` into a created or reused `RoutingTargetChoice`.

Phase 7.2.1 hardens atomicity: approval validation, target-choice creation/reuse, recommendation/audit marking, approval consumption, and approval provenance update happen in one coherent session/commit.

Later Phase 7 hooks extend the same pattern without adding smart routing:

- `target_choice_conversion`: exact target choice to one child `OrderIntent`.
- `prepared_order_preview_and_readiness`: exact child intent to preview/readiness inspection.
- `submitted_order_handoff`: exact already-ready child intent through the existing explicit submit path.
- `consumption_pending`: submitted-order exists, but approval consumption needs manual reconciliation; repeat calls reuse the existing submitted order.

## Flow

```mermaid
flowchart TD
  Plan[Automation dry-run plan] --> Gate[Approval gate state]
  Gate --> Approval[Active recommendation_acceptance approval]
  Approval --> Validate[Validate current lineage, action, expiry, policy state]
  Validate --> Accept[Call existing recommendation acceptance path]
  Accept --> Choice[Create or reuse RoutingTargetChoice]
  Choice --> Consume[Consume approval with provenance]
  Consume --> Result[Return approval + target-choice result]
```

## Blocks Before Target Choice

- Expired approval.
- Revoked approval.
- Stale lineage.
- Wrong action.
- Wrong recommendation.
- Consumed approval for a different recommendation.
- Dry-run-only current policy.
- Manual-only current policy.
- Non-current desired-trade/recommendation/audit/selected-target truth.

## What This Does Not Do

- Does not convert target choice to child intent.
- Does not create readiness.
- Does not submit an order.
- Does not call an exchange.
- Does not create route executor behavior.
- Does not fan out.
- Does not rank, score, or use CBBO.
- Does not reselect target.
- Does not auto-submit.

## Related Notes

- [[40 Operations/Phase 7 Focus]]
- [[40 Operations/Phase 8 Focus]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[10 Components/Routing Service]]
- [[10 Components/API Control Plane]]
- [[20 Workflows/Current Routed Workflow]]
