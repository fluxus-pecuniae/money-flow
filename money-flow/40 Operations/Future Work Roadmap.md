# Future Work Roadmap

Up: [[Money Flow Command Center]]

## Immediate Future

Phase 7 is accepted complete. It added controlled automation policy, durable approvals, four narrow approval-consuming action hooks through submitted-order handoff, `consumption_pending` truth, and closeout no-SOR safety coverage.

The immediate next phase should be Phase 8.0: operator-grade observability and manual-resolution inspection for the existing controlled routed automation chain.

See [[40 Operations/Phase 8 Focus]].

## Later Phase Shape

- Phase 7: controlled automation around the existing single-target path. Accepted complete.
- Phase 8.0: operator-grade observability, manual-resolution inspection, approval/automation state depth, submitted-order handoff safety inspection, and concurrency/lease visibility. Not SOR.
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
- Backtesting.
- Alerts.
- Strategy family expansion.

## Non-Negotiable Boundary

Do not implement optimization language before the system has the data and controls to support it.

## Related Notes

- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Known Issues Index]]
- [[30 Strategy/Product North Star]]
