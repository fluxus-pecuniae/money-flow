# Repo Navigation

Up: [[Money Flow Command Center]]

## Important Repo Roots

- `apps/api/` - FastAPI app and operator control plane.
- `apps/dashboard/` - placeholder dashboard only.
- `core/config/` - settings, profiles, runtime config.
- `core/domain/` - typed domain models, enums, routed lifecycle parser.
- `core/interfaces/` - protocol boundaries.
- `core/schemas/` - API schemas.
- `db/models/` - SQLAlchemy models.
- `db/migrations/` - Alembic migration history.
- `docs/` - canonical architecture and strategy docs.
- `services/` - market data, indicators, strategy, planning, risk, routing, execution, portfolio, exchange adapters.
- `scripts/` - review bundle and manual routed-flow tooling.
- `tests/` - phase and behavior coverage.

## Quick Jumps

- [[10 Components/API Control Plane]]
- [[10 Components/Domain Model]]
- [[10 Components/Routing Service]]
- [[10 Components/Execution Service]]
- [[10 Components/Exchange Adapters]]
- [[10 Components/Tests and Validation]]
- [[90 Reference/Canonical Repo Docs]]

## Local Vault Note

This vault lives in `money-flow/` under the repo root and is ignored by `.gitignore` and `.archiveignore`. It is an operator map, not a review-bundle artifact.
