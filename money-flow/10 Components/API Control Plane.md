# API Control Plane

Up: [[00 Maps/Component Map]]

## Paths

- `apps/api/app/main.py`
- `apps/api/app/dependencies.py`
- `apps/api/app/api/routes.py`
- `core/schemas/api.py`

## Current Role

The API is an operator control plane. It exposes inspection surfaces and explicit action endpoints for:

- config, health, readiness
- runtime context, clients, accounts, mandates, bindings
- exchange and venue status/capabilities/catalogs/private state
- market data, indicators, strategy decisions
- planning, risk, desired trades
- routing assessments, route-readiness audits, recommendations, target choices, conversions
- routing automation policy, plans, approvals, approval-gated recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff
- child intents, previews, readiness, submitted orders, lifecycle/actionability/recovery/reconciliation

## Current Important Entrypoints

- `GET /api/v1/routing-automation/policy`
- `POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}`
- `POST /api/v1/routing-automation/approvals`
- `GET /api/v1/routing-automation/approvals/{approval_id}`
- `GET /api/v1/routing-automation/approvals/by-desired-trade/{desired_trade_key}`
- `POST /api/v1/routing-automation/approvals/{approval_id}/revoke`
- `POST /api/v1/routing-automation/approvals/{approval_id}/consume`
- `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation`
- `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice`
- `POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness`
- `POST /api/v1/routing-automation/approvals/{approval_id}/submit`
- `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}`

## Boundaries

- The API is not a dashboard UI.
- Generic approval consumption is administrative state transition only.
- Phase 7 approval-consuming workflow actions are limited to recommendation acceptance, target-choice conversion, preview/readiness inspection, and submitted-order handoff.
- Phase 8.0 adds read-only operator observability/manual-resolution inspection before any dashboard UI or broader automation.

## Related Notes

- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[20 Workflows/Operator Observability and Manual Resolution]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
