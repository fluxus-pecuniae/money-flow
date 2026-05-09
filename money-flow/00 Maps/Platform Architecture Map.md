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

UAT0 safety / security / runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. Current priority is remaining UAT0 P1 blocker remediation before UAT1 read-only top-20 universe and market metadata work.

Closed by UAT0.1: scoped API auth/authz for sensitive `/api/v1` routes and central fail-safe runtime lockout defaults.

Remaining blockers: adapter-level runtime-policy enforcement verification, selected-venue sandbox/read-only endpoint policy, secret/log/error redaction verification, runtime drawdown monitoring, and top-20 symbol/market identity resolution.

## Canonical Repo Docs

- `docs/architecture.md`
- `docs/strategy.md`
- `README.md`
- `REPO_TREE.md`
