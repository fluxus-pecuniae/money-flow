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
- routing automation policy, plans, approvals, approval-gated recommendation acceptance
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

## Boundaries

- The API is not a dashboard UI.
- Generic approval consumption is administrative state transition only.
- Approval-gated recommendation acceptance is the only current approval-consuming workflow action.

## Related Notes

- [[20 Workflows/Approval Gated Recommendation Acceptance]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
