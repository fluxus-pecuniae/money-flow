# UAT0.1 API Auth/Authz And Runtime Lockout

Recorded at: `2026-05-09T15:10:00Z`

## Scope

UAT0.1 is a narrow P0 safety hardening phase. It adds API authentication / authorization gates for sensitive control-plane routes and adds an inspectable fail-safe runtime safety policy.

UAT0.1 does not implement UAT1, does not connect to exchanges, does not call private or signed exchange endpoints, does not use exchange API keys, does not submit orders, does not add paper trading, does not add live trading, does not add routing behavior, does not change Money Flow rules, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Sensitive Route Inventory

All `/api/v1` routes now require at least `read_only_operator` authentication unless an explicit test-only bypass is active in `API_RUNTIME_MODE=test`.

| Route group | Sensitivity | Required auth | Required role / scope | Protection status | Blocker status |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/config/summary` | Runtime/config inspection | Bearer token | `read_only_operator` | `implemented` | none |
| `/api/v1/sleeves`, `/api/v1/components`, strategy status/signals/decisions | Strategy state inspection | Bearer token | `read_only_operator` | `implemented` | none |
| `/api/v1/strategy/evaluate` | Creates strategy evaluation artifacts | Bearer token | `operator` | `implemented` | none |
| `/api/v1/clients`, `/api/v1/mandates`, runtime context, binding components | Runtime hierarchy inspection | Bearer token | `read_only_operator` | `implemented` | none |
| `/api/v1/accounts`, portfolio bootstrap summary | Account / venue-account inspection | Bearer token | `admin` | `implemented` | none |
| `POST /api/v1/mandates`, `POST /api/v1/mandates/{mandate_key}/bindings` | Account/mandate mutation | Bearer token | `admin` | `implemented` | none |
| `/api/v1/venues/{venue}/account-connectivity` | Exchange account connectivity | Bearer token | `admin` | `implemented` | none |
| `/api/v1/venues/{venue}/account-snapshot` | Private account state | Bearer token | `admin` | `implemented` | none |
| `/api/v1/venues/{venue}/private-state-*` | Private open orders, fills, positions | Bearer token | `admin` | `implemented` | none |
| `POST /api/v1/exchange/sync/universe` | Exchange public catalog mutation | Bearer token | `admin` | `implemented` | none |
| `POST /api/v1/exchange/sync/account` | Private exchange account sync | Bearer token | `admin` | `implemented` | none |
| `POST /api/v1/venues/{venue}/sync/catalog` | Venue catalog sync | Bearer token | `admin` | `implemented` | none |
| `POST /api/v1/market-data/sync/candles` | Market-data persistence | Bearer token | `operator` | `implemented` | none |
| `POST /api/v1/indicators/sync` | Indicator persistence | Bearer token | `operator` | `implemented` | none |
| `/api/v1/planning/*` inspection routes | Planning and desired-trade inspection | Bearer token | `read_only_operator` | `implemented` | none |
| `POST /api/v1/planning/desired-trades/from-decision/{decision_id}` | Desired-trade creation path when persisted | Bearer token | `operator` | `implemented` | none |
| `POST /api/v1/routing-assessments/*`, route-readiness, recommendations, target choices | Routing assessment / target-choice surfaces | Bearer token | `operator` | `implemented` | none |
| `/api/v1/routing-automation/policy`, approval inspection | Automation inspection | Bearer token | `read_only_operator` | `implemented` | none |
| `POST /api/v1/routing-automation/plans/*`, approval create/revoke | Automation planning / approval state | Bearer token | `operator` | `implemented` | none |
| `POST /api/v1/routing-automation/approvals/{approval_id}/consume` | Administrative consume state transition | Bearer token | `automation_admin` or `admin` | `implemented` | none |
| Recommendation acceptance, target-choice conversion, preview/readiness with approval | Approval-gated action hooks except submit | Bearer token | `automation_admin` or `admin` | `implemented` | none |
| `POST /api/v1/routing-automation/approvals/{approval_id}/submit` | Approval-gated submitted-order handoff | Bearer token | `admin` | `implemented` | none |
| `/api/v1/child-intents`, execution readiness, submitted-order inspection | Execution workflow inspection | Bearer token | `read_only_operator` | `implemented` | none |
| Child-intent prepared-order preview / submission-readiness | Execution readiness inspection | Bearer token | `operator` | `implemented` | none |
| `POST /api/v1/child-intents/{intent_id}/submit` | Direct explicit submit surface | Bearer token | `admin` | `implemented` | none |
| Submitted-order reconcile / cancel / amend / recovery execute / fills | Private lifecycle mutation or private fills | Bearer token | `admin` | `implemented` | none |
| `/health` | Liveness only | none | public | `implemented` | none |

## Auth Implementation Status

Status: `implemented`.

UAT0.1 adds scoped bearer-token authentication in `apps/api/app/dependencies.py`.

Supported scopes:

- `read_only_operator`
- `operator`
- `admin`
- `automation_admin`
- `uat_admin`

Scope behavior:

- `admin` satisfies every API scope.
- `operator` satisfies operator and read-only inspection scopes.
- `automation_admin` satisfies automation-admin, operator, and read-only inspection scopes.
- `uat_admin` satisfies UAT-admin, operator, and read-only inspection scopes.
- `read_only_operator` cannot use mutation, automation-consume, submit, cancel, amend, retry, or private account surfaces.

Token configuration is environment-driven:

- `API_READ_ONLY_OPERATOR_TOKEN`
- `API_OPERATOR_TOKEN`
- `API_ADMIN_TOKEN`
- `API_AUTOMATION_ADMIN_TOKEN`
- `API_UAT_ADMIN_TOKEN`

Tokens are not returned in config summaries or report output.

## Test / Local Bypass Policy

Status: `implemented`.

An auth bypass exists only for automated tests:

- `API_AUTH_DISABLED_FOR_TESTS=true`
- `API_RUNTIME_MODE=test`

If `API_AUTH_DISABLED_FOR_TESTS=true` is set outside `API_RUNTIME_MODE=test`, sensitive routes still reject unauthenticated requests. Development, UAT, sandbox, paper, and live-like modes fail closed.

## Runtime Mode Policy

Status: `implemented`.

UAT0.1 adds an inspectable `RuntimeSafetyPolicy` via `AppSettings.runtime_safety`.

Default values:

| Field | Default | Status |
| --- | --- | --- |
| `api_runtime_mode` | `development` | `implemented` |
| `uat_mode_enabled` | `false` | `implemented` |
| `sandbox_mode_required` | `true` | `implemented` |
| `paper_trading_enabled` | `false` | `implemented` |
| `live_trading_enabled` | `false` | `implemented` |
| `exchange_order_submission_enabled` | `false` | `implemented` |
| `private_exchange_endpoints_enabled` | `false` | `implemented` |
| `live_endpoint_lockout_enabled` | `true` | `implemented` |
| `order_endpoint_lockout_enabled` | `true` | `implemented` |
| `private_endpoint_lockout_enabled` | `true` | `implemented` |

The config summary exposes lockout truth without exposing tokens or secrets.

## Live / Private / Order Endpoint Lockout Status

| Area | Status | Notes |
| --- | --- | --- |
| Live trading default | `verified` | `live_trading_enabled=false`; existing execution live-submit phase remains false by default. |
| Private endpoint default | `verified` | `private_exchange_endpoints_enabled=false`; private-state routes now require `admin`. |
| Exchange order submission default | `verified` | `exchange_order_submission_enabled=false`; existing execution submit phases and venue submission flags remain false by default. |
| Sandbox/UAT enablement | `deferred` | UAT0.1 does not enable sandbox or read-only exchange connectivity. |
| Runtime policy enforcement inside every adapter | `needs_verification` | UAT0.1 adds central policy and API protection; adapter-level runtime-policy assertions remain a P1 hardening item before UAT1/UAT2. |

## Redaction Status

Status: `implemented_baseline`.

UAT0.1 adds `core/security.py` redaction helpers for representative secret-bearing structures:

- API keys
- secrets
- passwords
- passphrases
- bearer tokens
- authorization headers
- private/signing keys
- JWT material
- PostgreSQL URLs

Remaining status: `needs_verification`.

Structured logging and all exception paths still need broader review before UAT1. This remains a P1 blocker unless separately verified.

## UAT1 Readiness Decision

`UAT1 is blocked`.

Closed by UAT0.1:

- P0 API auth/authz missing for sensitive routes.
- P0 unauthenticated access to admin consume, submit/cancel/amend/retry, account, and private exchange surfaces.
- P0 missing inspectable runtime safety policy.

Remaining blockers:

- P1 adapter-level runtime-policy enforcement needs verification.
- P1 structured log / error redaction needs broader verification.
- P1 selected-venue sandbox/read-only endpoint policy is not implemented.
- P1 runtime drawdown monitoring is missing.
- P1 top-20 symbol / market identity resolution is not implemented.

UAT1 remains read-only only when it is later allowed. UAT1 must not submit orders.

## Boundary Confirmation

UAT0.1 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, exchange calls, private/signed calls, order endpoint calls, evidence packs, or strategy-rule changes.
