# Platform Architecture Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Current Architecture Shape

Money Flow is a mandate-driven platform with these implemented layers:

- strategy evaluation
- planning and risk
- non-executing routing assessment
- route-readiness audit
- controlled target recommendation
- explicit recommendation acceptance
- target-choice conversion
- prepared-order preview and readiness inspection
- approval-gated submitted-order handoff for the existing same-target chain
- submitted-order lifecycle / reconciliation inspection
- read-only operator workflow summary
- Strategy Validation research reports, evidence packs, diagnostics, and replay experiments

## What It Is Not

- Not a full SOR.
- Not CBBO.
- Not best-binding selection.
- Not ranking/scoring.
- Not broad auto-submit.
- Not live trading.
- Not paper trading.

## Current Priority

UAT0 safety / security / runtime audit is complete. Current priority is UAT0 blocker remediation before UAT1 read-only top-20 universe and market metadata work.

Key blockers: API auth/authz, fail-safe UAT mode gating, live endpoint lockout, secret/log/error redaction verification, runtime drawdown monitoring, and top-20 symbol/market identity resolution.

## Canonical Repo Docs

- `docs/architecture.md`
- `docs/strategy.md`
- `README.md`
- `REPO_TREE.md`
