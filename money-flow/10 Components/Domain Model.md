# Domain Model

Up: [[00 Maps/Component Map]]

## What Lives Here

Primary paths:

- `core/domain/enums.py`
- `core/domain/models.py`
- `core/domain/routed_lifecycle.py`
- `core/domain/hyperliquid.py`

## Main Object Families

- Client/account hierarchy: `Client`, `VenueAccount`, `StrategyMandate`, `MandateAccountBinding`, `StrategyComponentConfig`.
- Strategy objects: signals, indicators, `StrategyDecision`.
- Planning/risk objects: `MandateDesiredTrade`, convertibility, `RiskEvaluation`.
- Routing objects: `RoutingAssessment`, `RouteReadinessAudit`, `RoutingTargetRecommendation`, `RoutingTargetChoice`.
- Automation objects: `RoutingAutomationPolicy`, dry-run plans, approval records, approval gate state, approval-gated recommendation acceptance result.
- Execution objects: `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`.
- Lifecycle objects: actionability, recovery, reconciliation, routed lifecycle context, lifecycle events.

## Core Boundary Ideas

- `StrategyDecision` says what the strategy wants.
- `MandateDesiredTrade` says what the mandate wants.
- `RoutingTargetRecommendation` is advice, not action.
- `RoutingTargetChoice` is explicit target-choice audit truth, not execution.
- `OrderIntent` is account/venue/symbol targeted intent, not submitted order.
- `SubmittedOrder` is post-submit platform truth.
- Venue-private order views are not `SubmittedOrder` records.

## Related Notes

- [[20 Workflows/Current Routed Workflow]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
- [[90 Reference/Glossary]]
