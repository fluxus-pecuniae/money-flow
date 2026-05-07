# File Ownership Quick Reference

Up: [[Money Flow Command Center]]

## App And API

- `apps/api/app/main.py` - FastAPI app bootstrap.
- `apps/api/app/dependencies.py` - service wiring.
- `apps/api/app/api/routes.py` - operator endpoints.
- `apps/dashboard/` - static local Strategy Validation evidence dashboard.

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
- `tests/test_phase72_approval_gated_recommendation_acceptance.py` - Phase 7.2/7.2.1 approval-gated recommendation acceptance coverage.
- `tests/test_phase73_approval_gated_target_choice_conversion.py` - Phase 7.3/7.3.1 conversion coverage.
- `tests/test_phase74_approval_gated_preview_readiness.py` - Phase 7.4 preview/readiness coverage.
- `tests/test_phase75_approval_gated_submission_handoff.py` - Phase 7.5/7.5.1 submitted-order handoff and `consumption_pending` coverage.
- `tests/test_phase76_automation_closeout.py` - Phase 7.6 closeout safety proof.
- `tests/test_operational_docs.py` - operational-doc and bundle hygiene checks.

## Related Notes

- [[00 Maps/Repo Navigation]]
- [[10 Components/Tests and Validation]]
