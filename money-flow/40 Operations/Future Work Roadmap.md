# Future Work Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Immediate Future

Current implemented milestone: `SV1.18.1` complete.

Next proposed phase: `UAT0` safety / security / runtime hardening.

UAT0 is plumbing and behavior validation preparation only. It does not implement exchange connectivity, private/signed endpoint calls, exchange order submission, paper trading, live trading, routing expansion, or Money Flow rule changes.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Current Strategy Validation Outcome

SV1 is closed for now. The current evidence cycle selected exactly one UAT observation candidate:

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

It is Hyperliquid ETH USDC perpetual, `sleeve_1h`, current baseline Money Flow rules, observation / shadow first.

Current evidence does not prove edge. It is sufficient only to justify a tightly scoped UAT0 safety/runtime phase and later shadow observation if UAT0 passes.

## UAT Roadmap

See [[00 Maps/UAT Roadmap|UAT Roadmap]].

- UAT0: safety / security / runtime hardening.
- UAT1: exchange sandbox read-only connectivity.
- UAT2: shadow strategy run, no orders.
- UAT3: approval-gated sandbox orders.
- UAT4: sandbox / simulated trading review.

## Pre-Paper / Live Trading Blockers

Before paper/live trading or production-like deployment, the project must address:

- API authentication / authorization.
- key and secret hygiene.
- fail-safe live/demo separation.
- configured risk-limit enforcement.
- real drawdown calculation and monitoring.
- kill switch behavior.
- debug stack trace exposure.
- audit logging and no-secret logs.
- operator confirmation gates.
- duplicate-order prevention.
- submit-lease uncertainty handling.
- sandbox/live endpoint isolation.

## Later Strategy Validation

Future research may revisit:

- broader true replay fill/cost sensitivity.
- out-of-sample windows.
- exact stop/invalidation exit replay.
- portfolio-level simulation.
- cross-venue comparisons after venue-specific identity/source gaps close.

No later research item is approved as a production rule.

## Deferred Platform Work

- Phase 8.1 manual-resolution marker design.
- Smart routing / SOR foundations.
- Best-binding selection.
- CBBO.
- Fanout / split allocation.
- Route executor behavior.
- Cross-binding or cross-venue recovery.
- Broader dashboard/control-plane UI beyond review surfaces.

## Non-Negotiable Boundary

Do not implement optimization, paper trading, live trading, exchange order submission, or routing expansion from this roadmap without a separate approved phase.
