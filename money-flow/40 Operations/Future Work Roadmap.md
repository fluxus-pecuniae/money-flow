# Future Work Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Immediate Future

Current implemented milestone: `PT0` TradingView charts and top-20 paper/sandbox runtime foundation complete.

Next proposed phase: `PT0.1` supervised top-20 paper/sandbox runtime week may be scoped. `UAT3.5` additional sandbox routing lifecycle tests remain blocked by incomplete UAT-universe precision validation and require separate approval.

UAT1 public read-only connectivity is complete under strict constraints: no private endpoints, no signed endpoints, no order endpoints, no API keys, no paper trading, no live trading, and no order submission. UAT1.1 adds model/report-only shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured log/API error redaction verification. UAT2 bounded no-order shadow observation is complete. UAT2.1 dashboard visualization is complete and adds a review-only UAT2 dashboard view without approval/order actions. UAT3.0 through UAT3.0.6 prepared and dry-ran the sandbox/testnet gate chain. UAT3.1 verified exact founder/operator approval and made exactly one Hyperliquid testnet ETH post-only limit attempt under 10 USDC notional; Hyperliquid rejected it with a sanitized user/API-wallet-not-found response, no cancel was required, and reconciliation found no open order. UAT3.2 verified separate founder/operator approval but blocked before order transport because fixed-key account/API-wallet readiness still failed; order attempt count was `0` and no order/cancel/amend/retry endpoint was called. UAT3.3 fixed Hyperliquid account targeting and ETH precision formatting, and a later approved follow-up verified accepted/open -> cancel -> reconcile. UAT3.4 operationalized that route with a fixed-target sandbox routing pipeline and routed ledger. UAT4.0 added a read-only chart cockpit, UAT4.1 rebuilt it as an exchange-style workstation, and UAT4.2 adds public-read-only monitor rows, deterministic indicators, paper-observation markers, a 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger. PT0 integrates TradingView Lightweight Charts, top-20 Hyperliquid-supported paper/sandbox universe eligibility, paper scanner records, current-equity sizing, and default-disabled risk-gated sandbox route candidates. UAT3.1-PT0 created no production execution artifacts, live trading, live broad top-20 submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, private order dashboard call, dashboard order control, or unapproved repeated order.

UAT0 was plumbing and behavior validation preparation only. UAT0.1 closes the P0 sensitive-route auth/authz and central runtime-lockout baseline. UAT0.2 closes the adapter-level runtime-policy baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction tests. UAT0.3 adds fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verified allowed public-read-only Hyperliquid endpoint behavior and resolved the no-key public top-volume source against Hyperliquid supported markets. It did not implement private/signed endpoint calls, exchange order submission, paper trading, live trading, routing expansion, strategy execution, or Money Flow rule changes.

PAPER TRADING IS APPROVED. Paper trading is approved for Hyperliquid testnet/sandbox only. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under metadata, precision, risk, lease, label, and no-live gates. Live trading is not approved. Real-capital trading is not approved. Live exchange order submission is not approved. Sandbox/testnet routing remains default-disabled by `PT0_SANDBOX_ORDER_ROUTING_ENABLED=false` unless explicitly enabled for a scoped run.

## Current Strategy Validation Outcome

SV1 is closed for now. The current evidence cycle selected exactly one UAT observation candidate:

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

It is Hyperliquid ETH USDC perpetual, `sleeve_1h`, current baseline Money Flow rules, observation / shadow first.

Current evidence does not prove edge. It was sufficient only to justify a tightly scoped UAT0 safety/runtime audit and later shadow observation if blockers close.

Future UAT observation is not ETH-only. UAT1/UAT2 should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment for platform behavior validation only.

## UAT Roadmap

See [[00 Maps/UAT Roadmap|UAT Roadmap]].

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy and redaction hardening complete.
- UAT0.3: top-20 universe and drawdown readiness preflight complete.
- UAT1: top-20 universe plus read-only venue/market metadata complete under strict public-read-only constraints.
- UAT2: bounded no-order shadow strategy run across top-20 supported assets with `next_candle_open` / `next_candle_close` complete.
- UAT2.1: dashboard visualization and founder readiness pack complete; no approval action or order-enabling behavior added.
- UAT3.0: sandbox-order design/readiness complete; no order submission, no real order intents/submitted orders, and no executable approvals.
- UAT3.0.1: sandbox runtime / approval / risk readiness hardening complete with fixture-only validators; no order submission, real order intents/submitted orders, executable approvals, private/signed endpoint calls, API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.
- UAT3.0.2: sandbox gate integration dry-run / policy hardening complete; no order submission, real order intents/submitted orders, executable approvals, private/signed endpoint calls, API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.
- UAT3.0.3: sandbox gate wiring / label-enforcement hardening complete; boundary-label helpers and a dry-run executable gate service exist, with no order submission, real order intents/prepared orders/submitted orders, executable approvals, private/signed/order endpoint calls, API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.
- UAT3.0.4: sandbox private read-only drawdown readiness complete; private read-only account policy, credential approval/boundary validation, endpoint category separation, redaction, and sandbox account drawdown feed modeling exist. Explicit credential approval was absent, so no API keys were used and no private endpoints were called.
- UAT3.0.5: sandbox/testnet private read-only drawdown verification complete; exact approval text and sandbox/testnet credential boundaries are validated, one Hyperliquid testnet read-only account-state request returned HTTP 200, and `sandbox_drawdown_feed_live_fed_verified` is recorded with no API key/private key or order endpoint use.
- UAT3.0.6: sandbox submit path dry-run wiring complete; non-persistent submission plans and dry-run gate chaining cover actual-submission approval, live-fed drawdown, approval scope, risk, submit-lease duplicate prevention, endpoint classification, and sandbox labels without artifacts or exchange calls.
- UAT3.1: first approval-gated sandbox/testnet lifecycle probe complete; one Hyperliquid testnet ETH post-only limit attempt was rejected by venue user/API-wallet validation, required no cancel, reconciled no open order, and created no production execution artifacts.
- UAT3.2: fixed-key preflight / second sandbox lifecycle attempt complete as blocked before order transport; separate approval was verified, account/API-wallet readiness failed, order attempt count was `0`, and no order endpoint was called.
- UAT3.3: Hyperliquid account-targeting / precision hardening complete as blocked before order transport; normal accounts omit `vaultAddress`, subaccount/vault targets use explicit `vaultAddress`, ETH precision formatting is fixed, and target subaccount equity was `0.0`.
- UAT3.4: fixed-target sandbox routing pipeline and routed ledger complete.
- UAT4.0: live UAT trading dashboard / chart cockpit is complete as read-only local visualization.
- UAT4.1: exchange-style dashboard redesign complete.
- UAT4.2: live market dashboard and internal paper-equity monitor complete; no order controls or live endpoints added.
- PT0: TradingView charts and top-20 paper/sandbox runtime foundation complete; paper trading is approved for Hyperliquid testnet/sandbox only, broader top-20 paper/sandbox is approved under gates, live trading remains not approved, and repeated sandbox routing remains default-disabled.
- PT0.1: supervised top-20 paper/sandbox runtime week may be scoped later.

## Pre-PT0.1 / Live Trading Blockers

Before PT0.1 supervised runtime or any live deployment, the project must address:

- deployment-level structured application log/API error redaction verification beyond representative UAT1.1 tests.
- key and secret hygiene beyond representative helper tests.
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

Do not implement optimization, live trading, real-capital trading, live exchange order submission, cross-venue routing, SOR/fanout/CBBO, unsupported-asset routing, or routing expansion from this roadmap without a separate approved phase.
