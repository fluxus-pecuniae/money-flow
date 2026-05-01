# Execution Lifecycle

Up: [[00 Maps/Workflow Map]]

## Current Execution Shape

Execution starts after a child `OrderIntent` exists. Preparation and readiness happen before submitted-order creation.

```text
OrderIntent
-> PreparedVenueOrder
-> ExecutionReadinessAssessment
-> explicit gated submit
-> SubmittedOrder
-> reconciliation / lifecycle events / actionability / recovery
```

## Safety Features

- Live submit gate and routed submit gate both matter.
- Routed submit revalidates recommendation lineage and current target truth.
- Submission lease serializes concurrent explicit submits for one child intent.
- Adapter-returned but persistence-failed state becomes `adapter_submit_persistence_unknown`.
- Adapter-in-flight uncertainty becomes `adapter_submit_may_have_started`.
- Uncertainty states block future submits until manual reconciliation.

## Same-Target Lifecycle

Same-target retry, cancel, amend, actionability, and reconciliation stay selected-account and selected-venue scoped. The system does not perform alternate binding or cross-venue recovery.

## Related Notes

- [[10 Components/Execution Service]]
- [[10 Components/Exchange Adapters]]
- [[20 Workflows/Current Routed Workflow]]
