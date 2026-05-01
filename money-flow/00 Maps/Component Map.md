# Component Map

Up: [[Money Flow Command Center]]

## Main Components

| Area | Note | Current role |
| --- | --- | --- |
| Domain | [[10 Components/Domain Model]] | Typed strategy, mandate, routing, approval, execution, lifecycle objects. |
| API | [[10 Components/API Control Plane]] | FastAPI operator inspection and explicit action endpoints. |
| Runtime | [[10 Components/Runtime and Config]] | Active client, mandate, binding, account, source-policy, config bootstrap. |
| DB | [[10 Components/Database and Migrations]] | SQLAlchemy models and Alembic phase history. |
| Market data | [[10 Components/Market Data and Indicators]] | Candles, health, deterministic indicators. |
| Strategy | [[10 Components/Strategy Engine]] | Money Flow strategy family and strategy decisions. |
| Planning/risk | [[10 Components/Planning and Risk]] | Desired trades, source policy, approval/rejection, child-intent boundary. |
| Routing | [[10 Components/Routing Service]] | Assessments, audits, recommendations, target choices, automation plans, approvals, Phase 7 action hooks, and routed workflow inspection. |
| Execution | [[10 Components/Execution Service]] | Preview, readiness, submit, lifecycle, actionability, recovery, reconciliation. |
| Venues | [[10 Components/Exchange Adapters]] | Adapter registry and six current venue integrations. |
| Portfolio | [[10 Components/Portfolio and Attribution]] | Account truth and incomplete attribution overlays. |
| Tests | [[10 Components/Tests and Validation]] | Phase-by-phase behavior and boundary proof. |

## Support / Placeholder Components

- `apps/dashboard/` is still a placeholder, not a production UI.
- `services/alerts/` is a placeholder; alert delivery is deferred.
- `services/backtest/` is a placeholder; backtesting is deferred.

## How To Navigate The Code

Use [[90 Reference/File Ownership Quick Reference]] for file paths, then jump into component notes above.

For the current operator-control layer and next manual-resolution design, start with [[40 Operations/Phase 8 Focus]] and [[20 Workflows/Operator Observability and Manual Resolution]].
