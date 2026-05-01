# Known Issues Index

Up: [[Money Flow Command Center]]

## High-Signal Open Items

Source: repo `KNOWN_ISSUES.md`.

- Execution-quality market data: top-of-book and depth interfaces exist, but live implementation is not wired.
- Portfolio attribution: full strategy attribution engine remains deferred.
- Runtime orchestration: active runtime is mandate-first, but one process still targets one selected mandate at a time.
- Routing architecture: current routing is controlled single-target, not smart routing.
- Multi-account portfolio summaries: no true mandate-level aggregate snapshot yet.
- Venue parity: adapters have uneven amend, private-state, and user-stream depth.
- Planning source policy: current runtime supports one active planning/source venue per mandate.
- Live execution expansion: broader automation, fanout, target reselection, cross-binding/cross-venue recovery, and smart routing remain deferred.
- Routed order-shape policy: explicit LIMIT support exists, but slippage guards and market-data-derived limit price sources remain deferred.

## Watch Closely

- Future DB-level serialization for recommendation acceptance/conversion remains a hardening item before broader action-taking automation.
- Do not let approval-gated actions skip current lineage or current policy truth.
- Do not let route-readiness or recommendation language imply optimal execution.

## Related Notes

- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Future Work Roadmap]]
- [[10 Components/Exchange Adapters]]
- [[10 Components/Portfolio and Attribution]]
