# File Ownership Quick Reference

Up: [[Money Flow Command Center]]

## App And API

- `apps/api/app/main.py` - FastAPI app bootstrap.
- `apps/api/app/dependencies.py` - service wiring.
- `apps/api/app/api/routes.py` - operator endpoints.
- `apps/dashboard/README.md` - placeholder dashboard.

## Core

- `core/config/` - settings and profiles.
- `core/domain/enums.py` - domain enums.
- `core/domain/models.py` - main dataclass/domain model surface.
- `core/domain/routed_lifecycle.py` - routed submitted-order payload parser.
- `core/interfaces/services.py` - service protocols.
- `core/schemas/api.py` - Pydantic API schemas.

## Persistence

- `db/models/trading.py` - SQLAlchemy models.
- `db/migrations/versions/` - Alembic history.
- `db/session.py` - session setup.

## Services

- `services/runtime/context.py` - active mandate/account context.
- `services/market_data/service.py` - candles and market-data health.
- `services/indicators/service.py` - indicators.
- `services/strategy/` - strategy engines and Money Flow.
- `services/planning/service.py` - desired trade planning.
- `services/risk/engine.py` - risk evaluation.
- `services/routing/service.py` - routing, recommendation, automation, approvals.
- `services/execution/service.py` - readiness, submit, lifecycle, recovery, reconciliation.
- `services/exchange/` - venue adapters and registry.
- `services/portfolio/service.py` - portfolio/account truth.
- `services/alerts/service.py` - placeholder.
- `services/backtest/engine.py` - placeholder.

## Tools And Tests

- `scripts/manual_routed_flow.py` - manual routed workflow trace.
- `scripts/create_review_bundle.py` - review bundle creation.
- `tests/test_phase72_approval_gated_recommendation_acceptance.py` - latest Phase 7.2/7.2.1 coverage.
- `tests/test_operational_docs.py` - operational-doc and bundle hygiene checks.

## Related Notes

- [[00 Maps/Repo Navigation]]
- [[10 Components/Tests and Validation]]
