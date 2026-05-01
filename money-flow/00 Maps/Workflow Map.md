# Workflow Map

Up: [[Money Flow Command Center]]

## Current End-to-End Path

```mermaid
flowchart LR
  A[Market Data] --> B[Indicators]
  B --> C[StrategyDecision]
  C --> D[MandateDesiredTrade]
  D --> E[RiskEvaluation]
  D --> F[RoutingAssessment]
  F --> G[RouteReadinessAudit]
  G --> H[RoutingTargetRecommendation]
  H --> I[RoutingTargetChoice]
  I --> J[OrderIntent]
  J --> K[PreparedVenueOrder]
  K --> L[ExecutionReadinessAssessment]
  L --> M[SubmittedOrder]
  M --> N[Lifecycle / Actionability / Reconciliation]
```

## Workflow Notes

- [[20 Workflows/Current Routed Workflow]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Execution Lifecycle]]
- [[20 Workflows/Manual Routed Flow Harness]]
- [[20 Workflows/Deferred Smart Routing]]

## Control Boundaries

```mermaid
flowchart TD
  Rec[Recommendation] -->|explicit acceptance or valid approval hook| Choice[Target Choice]
  Choice -->|explicit conversion or valid approval hook| Intent[Child OrderIntent]
  Intent -->|explicit preview/readiness or valid approval hook| Ready[Readiness]
  Ready -->|explicit gated submit or valid approval hook| Submitted[SubmittedOrder]

  Rec -. not action .-> Stop1[No hidden target choice]
  Choice -. not execution .-> Stop2[No hidden child intent]
  Ready -. not auto submit .-> Stop3[No hidden SubmittedOrder]
```

## Read This First

If you only have five minutes, read:

- [[00 Maps/Current State Dashboard]]
- [[20 Workflows/Current Routed Workflow]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[40 Operations/Phase 7 Focus]]
- [[40 Operations/Phase 8 Focus]]
- [[20 Workflows/Deferred Smart Routing]]
