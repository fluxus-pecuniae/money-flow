# Future Work Roadmap

Up: [[Money Flow Command Center]]

## Immediate Future

Current implemented phase: `SV1.12.1`.

Strategy Validation is the current priority. No first real canonical Money Flow evidence packs have been generated yet. The intended local `money_flow` DB is migrated/current, but it contains zero persisted candles and currently lacks BTC/ETH/SOL operator-verified research identity rows. SV1.12 adds the guarded canonical candle bundle import path: intended non-maintenance DB, migrated/current schema, operator-verified research-only/non-trading identity, timezone-explicit files, complete one-to-one requirement-aware preflight, and hardened importer success are all required before candle writes. SV1.12.1 makes partial import truth explicit and blocks the operational import report because identity rows and repo/session candle files are missing. The immediate next phase should complete guarded canonical candle import first, then run post-import canonical evidence review with evidence generation only after DB target/schema/identity/data readiness and import status are clean, and keep paper-trading design deferred until founder/operator evidence review justifies it.

SV1.9.1 must remain the accepted guardrail: ambiguous/non-intended maintenance DB targets block evidence generation by default, timezone-naive candle imports are rejected by default unless a provenance-marked exploratory override is explicitly used, and generated research/import outputs stay out of Git and review bundles.

## Later Phase Shape

- Phase 7: controlled automation around the existing single-target path. Accepted complete.
- Phase 8.0: operator-grade observability, manual-resolution inspection, approval/automation state depth, submitted-order handoff safety inspection, and concurrency/lease visibility. Implemented; not SOR.
- Phase 8.0.1 / 8.0.2: Obsidian baseline cleanup and active submit-lease operator-summary truth hotfix. Implemented.
- SV1.0-SV1.12.1: Strategy Validation research track. Implemented through intended local DB readiness, unique canonical import requirements, market-identity bootstrap, operator-verified non-trading identity write guard, complete requirement-aware candle-import preflight, guarded canonical candle bundle import, explicit partial-persistence reporting, and blocked import run truth; no first real canonical evidence packs yet.
- Later Phase 8.x: manual-resolution markers or dashboard read-only surfaces if Phase 8.0 keeps the mutation boundary clean.
- Future SOR foundations: only after market-data, fee, quote sufficiency, slippage, operator controls, and manual-resolution workflow are stronger.
- Phase 9: multi-child fanout or split execution only after single-target routing is boring and proven.
- Phase 10: production execution control plane, operator dashboards, kill switches, replayable audit trails, reconciliation jobs, incident tooling, post-trade analytics.

## Future Work Buckets

- Approval and policy expansion.
- Operator workflow summaries.
- Manual-resolution inspection.
- Submit-lease and approval-state observability.
- Execution-quality market data.
- Strategy attribution and portfolio accounting.
- Composite source/pricing policy.
- Venue parity and user-stream depth.
- Real dashboard/control plane UI.
- Strategy Validation evidence review and historical candle data readiness.
- Alerts.
- Strategy family expansion.

## Non-Negotiable Boundary

Do not implement optimization language before the system has the data and controls to support it.

## Related Notes

- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Known Issues Index]]
- [[30 Strategy/Product North Star]]
