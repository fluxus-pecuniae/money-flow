# Deferred Smart Routing

Up: [[00 Maps/Workflow Map]]

## This Is Deliberately Not Implemented Yet

Current routing is controlled single-target workflow truth. It is not smart order routing.

## Deferred Capabilities

- Best-binding selection.
- Venue-quality scoring.
- Ranking.
- CBBO.
- Quote comparison across bindings.
- Child-intent fanout or split execution.
- Target reselection.
- Route plans.
- Route executor.
- Cross-binding recovery.
- Cross-venue retry/failover.
- Broad auto-submit.
- Slippage-controlled routed execution beyond current explicit order-shape policy.

## Why It Is Deferred

The repo has repeatedly chosen truthful substrate before optimization. Real SOR needs stronger execution-quality market data, fee truth, quote sufficiency, order-shape/slippage policy, operator controls, and post-submit lifecycle depth.

## What Exists Instead

- Binary eligibility/ineligibility facts.
- Route-readiness data-sufficiency audits.
- Non-executing recommendation under `single_ready_candidate_only` or explicit binding priority.
- Explicit target-choice acceptance.
- Explicit conversion and submit gates.
- Phase 7 dry-run plans and approval gates.

## Related Notes

- [[40 Operations/Future Work Roadmap]]
- [[10 Components/Routing Service]]
- [[40 Operations/Known Issues Index]]
