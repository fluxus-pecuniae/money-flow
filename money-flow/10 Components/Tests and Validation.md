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
- `test_phase73_approval_gated_target_choice_conversion.py`: approval-gated target-choice conversion and negative lineage/status coverage.
- `test_phase74_approval_gated_preview_readiness.py`: approval-gated preview/readiness boundary and no submission.
- `test_phase75_approval_gated_submission_handoff.py`: approval-gated submitted-order handoff, submit gates, leases, uncertainty, and `consumption_pending`.
- `test_phase76_automation_closeout.py`: full Phase 7 closeout safety proof.

## Operational Validation

`tests/test_operational_docs.py` checks repo memory discipline, required Obsidian brain notes, and review-bundle hygiene. Tracked Obsidian markdown notes are part of the review surface; Obsidian app state under `money-flow/.obsidian/` remains ignored.

## Related Notes

- [[40 Operations/Operational Memory]]
- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[90 Reference/Canonical Repo Docs]]
