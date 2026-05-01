# Planning and Risk

Up: [[00 Maps/Component Map]]

## Paths

- `services/planning/service.py`
- `services/risk/engine.py`
- `tests/test_phase401_trade_planning.py`
- `tests/test_phase41_risk.py`

## Current Role

Planning converts strategy decisions into mandate-level desired trades and related convertibility/routing-candidate facts. Risk evaluates whether desired trades can proceed.

## Main Objects

- `MandateDesiredTrade`
- `DesiredTradeConvertibilityAssessment`
- `BindingRoutingCandidate`
- `RiskEvaluation`
- `OrderIntent`

## Boundaries

- Desired trade is mandate-level, not final venue execution.
- Risk approval is not routing.
- Child intent creation is explicit and targeted.
- Current runtime remains one selected mandate per process.

## Related Notes

- [[10 Components/Runtime and Config]]
- [[10 Components/Routing Service]]
- [[20 Workflows/Current Routed Workflow]]
