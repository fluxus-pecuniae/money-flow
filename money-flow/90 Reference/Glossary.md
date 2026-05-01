# Glossary

Up: [[Money Flow Command Center]]

## Platform Objects

- `Client`: owner namespace for accounts and mandates.
- `VenueAccount`: exchange account truth.
- `StrategyMandate`: logical strategy umbrella and future account-group routing umbrella.
- `MandateAccountBinding`: membership/policy surface linking a mandate to a venue account.
- `StrategyComponentConfig`: family-specific component config, currently used for Money Flow lanes.

## Strategy And Planning

- `StrategyDecision`: strategy output.
- `MandateDesiredTrade`: mandate-level desire, before final target selection.
- `RiskEvaluation`: approval/rejection boundary for desired trade.
- `OrderIntent`: targeted child intent for one venue/account/symbol path.

## Routing

- `RoutingAssessment`: candidate inventory and binary eligibility facts.
- `RouteReadinessAudit`: non-selecting data-sufficiency audit.
- `RoutingTargetRecommendation`: non-executing recommendation.
- `RoutingTargetChoice`: explicit selected-target audit record.
- `RoutingAutomationPolicy`: automation mode and action policy input.
- `RoutingAutomationApproval`: durable one-action approval gate.

## Execution

- `PreparedVenueOrder`: preview/preflight shape.
- `ExecutionReadinessAssessment`: readiness gate before submit.
- `SubmittedOrder`: platform post-submit truth.
- `LifecycleEvent`: persisted lifecycle/reconciliation event.

## Boundary Phrases

- Recommendation is not action.
- Approval is not execution.
- Target choice is not child intent.
- Readiness is not submit.
- SubmittedOrder is post-submit truth.
- Venue-private open order is not SubmittedOrder.
- Routing is not smart routing yet.
