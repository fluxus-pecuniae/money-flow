# Manual Routed Flow Harness

Up: [[00 Maps/Workflow Map]]

## Path

- `scripts/manual_routed_flow.py`
- `tests/test_phase65_manual_routed_flow.py`

## Current Role

The harness lets an operator/developer walk an existing desired trade through the current routed service chain and emit JSON traces.

## What It Can Inspect

- desired trade
- routing assessment
- route-readiness audit
- target recommendation
- recommendation acceptance
- target-choice conversion
- prepared-order preview
- execution readiness

## Submission Boundary

Submission is skipped by default. Submit attempts are blocked locally unless the explicit danger-confirmation flag is supplied, and even then the service gates still apply.

## Timing

Phase 6.6 added local `timing_ms` and per-step `elapsed_ms`. This is local harness timing, not production route-executor telemetry.

## Related Notes

- [[20 Workflows/Current Routed Workflow]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
