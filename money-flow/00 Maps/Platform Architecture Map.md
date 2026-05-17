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
- PT-RT public-mainnet Paper Trading observation substrate with synthetic ledgers and separate testnet plumbing probe audit rows
- founder dashboard review surfaces for Paper Trading, Historical Replay, Evidence, The Lab, Audit, and Strategy

## What It Is Not

- Not a full SOR.
- Not CBBO.
- Not best-binding selection.
- Not ranking/scoring.
- Not broad auto-submit.
- Not live trading.
- Not production-approved live trading or production strategy paper runtime.

## Current Priority

Current priority is Paper Trading / PT-RT runtime observation review and founder-readable evidence/dashboard clarity. UAT0 through UAT4.2 are complete historical plumbing and safety tracks, not the active center of the project.

Closed by UAT0.1: scoped API auth/authz for sensitive `/api/v1` routes and central fail-safe runtime lockout defaults.

Closed by UAT0.2: adapter private/signed/order runtime-policy guards before transport, public read-only classification, a Hyperliquid future-UAT1 read-only allowlist artifact, and representative bearer/API-key/secret/password/DB URL redaction tests.

Remaining current blockers: no clean production strategy candidate is promoted; fresh PT-RT runtime artifacts still need review before forward-observation claims; live trading and production auto-submit remain not approved.

## Canonical Repo Docs

- `docs/architecture.md`
- `docs/strategy.md`
- `README.md`
- `REPO_TREE.md`
