# Tests and Validation

Up: [[00 Maps/Component Map]]

## Paths

- `tests/`
- `tests/test_operational_docs.py`
- `scripts/create_review_bundle.py`
- `scripts/manual_routed_flow.py`

## Current Role

Tests are phase-shaped and boundary-focused. The suite repeatedly proves both what exists and what must not happen.

## Important Test Families

- `test_phase3_strategy.py`: indicator and Money Flow strategy behavior.
- `test_phase401_trade_planning.py` and `test_phase41_risk.py`: desired trades and risk.
- `test_phase45_execution_lifecycle.py`: multi-venue lifecycle/recovery/cancel/amend/private-state behavior.
- `test_phase50_*` through `test_phase5101_*`: routing substrate and route-readiness audit.
- `test_phase600_*` through `test_phase69_*`: recommendation-backed routing and lifecycle.
- `test_phase70_routing_automation.py`: dry-run automation plans.
- `test_phase71_routing_automation_approvals.py`: approval gates and lineage truth.
- `test_phase72_approval_gated_recommendation_acceptance.py`: approval-gated recommendation acceptance atomicity.

## Operational Validation

`tests/test_operational_docs.py` checks repo memory discipline and review-bundle hygiene. The vault is intentionally ignored by `.gitignore` and `.archiveignore`, so it is a local brain rather than a tracked review artifact.

## Related Notes

- [[40 Operations/Operational Memory]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[90 Reference/Canonical Repo Docs]]
