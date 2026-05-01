# Current Routed Workflow

Up: [[00 Maps/Workflow Map]]

## What Exists Today

The controlled routed path exists from mandate desired trade through explicit submitted-order handoff and read-only lifecycle inspection.

```text
1. StrategyDecision
2. MandateDesiredTrade
3. RoutingAssessment
4. RouteReadinessAudit
5. RoutingTargetRecommendation
6. RoutingTargetChoice
7. OrderIntent
8. PreparedVenueOrder
9. ExecutionReadinessAssessment
10. SubmittedOrder
11. Lifecycle / actionability / recovery / reconciliation / event inspection
```

## Important Transitions

- Recommendation creation is non-executing and data-sufficiency/current-truth bounded.
- Recommendation acceptance creates or reuses one non-executing target choice.
- Target-choice conversion creates or reuses exactly one routed child intent.
- Preview/readiness reuse the existing execution substrate and revalidate routed lineage.
- Submitted-order handoff goes through explicit gated child-intent submit.
- Post-submit surfaces expose read-only routed lifecycle context.

## Current Proofs

- Exactly one target choice in the controlled acceptance path.
- Exactly one child intent in the controlled conversion path.
- Exactly one submitted order after explicit gated submit.
- Same-target retry preserves routed lineage.
- Reconciliation payload collisions cannot overwrite platform-owned routed lineage.

## Related Notes

- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
- [[20 Workflows/Execution Lifecycle]]
- [[20 Workflows/Deferred Smart Routing]]
