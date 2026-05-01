# Database and Migrations

Up: [[00 Maps/Component Map]]

## Paths

- `db/models/trading.py`
- `db/models/__init__.py`
- `db/session.py`
- `db/migrations/versions/`

## Current Role

Persistence stores canonical instruments, symbol mappings, clients, venue accounts, mandates, bindings, source policy, market data, indicators, strategy decisions, desired trades, routing records, approvals, readiness, child intents, submitted orders, lifecycle events, checkpoints, and overlays.

## Recent Important Tables / Migrations

- `routing_assessments` and candidates: Phase 5.0.
- `routing_target_choices`: Phase 5.1.
- `route_readiness_audits` and candidate audits: Phase 5.10.1.
- `routing_target_recommendations`: Phase 6.0.0.
- binding `target_recommendation_priority`: Phase 6.1.
- `order_intent_submission_leases`: Phase 6.10.1.
- lease status widening: Phase 6.10.2.
- `routing_automation_approvals`: Phase 7.1.
- approval lineage fingerprint/scope uniqueness: Phase 7.1.1.

## Current Phase Notes

- Phase 7.2 through Phase 7.6 add no new migrations after the Phase 7.1 / 7.1.1 approval table and scope columns.
- Phase 7.2 through Phase 7.5 consume existing approval rows and existing routed workflow tables.
- Phase 7.5.1 uses string-backed approval status plus approval JSON fields for `consumption_pending`.
- Phase 7.6 is closeout tests/docs only.
- Phase 8.0 stayed read-only and added no persistence; if Phase 8.1 adds manual-resolution markers, their persistence semantics need explicit design.

## Related Notes

- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
