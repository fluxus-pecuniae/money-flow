# Future Work Roadmap

Up: [[Money Flow Command Center]]

## Immediate Future

Current implemented phase: `SV1.13.2` dynamic equity capital simulation; SV1.13 generated component-scoped evidence packs, SV1.13.1 clarified that grouped aggregate research sums are not one account/scenario PnL, and SV1.13.2 adds per-scenario account-style dynamic equity sizing.

Strategy Validation is the current priority. First Hyperliquid public campaign evidence packs now exist for founder review, and SV1.13.1 adds the interpretation layer needed before any paper-trading design scope: grouped aggregate totals are descriptive research-run sums, scenario-level fill/cost results remain separate, ETH `sleeve_1h` concentration is explicit, and drawdown/regime/cost sensitivity are visible. SV1.13.2 adds `dynamic_equity_pct`, where each new simulated trade in a scenario sizes from current realized equity instead of reusing initial-capital notional; ETH `sleeve_1h` stayed above starting equity across tested dynamic fill/cost assumptions, while 15m and 4h dynamic scenarios ended below starting equity. The intended local `money_flow` DB is migrated/current, Hyperliquid BTC/ETH/SOL research identity has been seeded as operator-verified/non-trading/non-strategy-eligible by `Tercirafael`, the 9-file public YTD/recent Hyperliquid campaign imported `25848` candles, and SV1.13 generated component-scoped evidence packs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`. `apps/dashboard/` provides a static local dashboard to inspect those ignored JSON evidence artifacts in a human-readable way. SV1.12 keeps guarded import requirements authoritative for any future imports: intended non-maintenance DB, migrated/current schema, operator-verified research-only/non-trading identity, timezone-explicit files, complete one-to-one requirement-aware preflight, and hardened importer success are all required before candle writes. SV1.12.5 also extends readiness to supported venue adapters: Aster/Binance have 18 additional complete native-trade-count candidate files, OKX/Coinbase are blocked by missing public trade count, and Kraken is blocked by incomplete public REST coverage. The immediate next work should be manual founder/operator review of Hyperliquid-only constant-notional and dynamic-equity interpretation before any explicitly scoped paper-trading design; broader venue comparison needs the SV1.12.5 venue-specific blockers resolved first.

SV1.9.1 must remain the accepted guardrail: ambiguous/non-intended maintenance DB targets block evidence generation by default, timezone-naive candle imports are rejected by default unless a provenance-marked exploratory override is explicitly used, and generated research/import outputs stay out of Git and review bundles.

## Pre-Paper / Live Trading Blockers

These findings came from the 2026-05-06 external code/security review and must be fixed before paper trading, live trading, exposed API usage, or any production-like deployment. They do not block current Strategy Validation candle-data research, but they do block operational trading readiness.

- `critical`: Rotate any live credentials that were present in local `.env`, including Hyperliquid private key material, OKX API credentials, and Coinbase Advanced Trade credentials. Treat local plaintext secrets as compromised if they were available to review tooling.
- `critical`: Add API authentication/authorization before exposing the API beyond localhost. Current concern is unauthenticated execution-facing routes combined with `APP_API_HOST=0.0.0.0`.
- `high`: Enforce configured risk limits in the risk engine, including global gross exposure, account drawdown, and symbol concentration. Configured-but-unchecked limits are cosmetic.
- `high`: Replace hardcoded portfolio drawdown truth with real drawdown calculation so drawdown risk limits can trigger.
- `high`: Fix Strategy Validation mark-to-market equity/drawdown reporting so intra-trade equity accounts for expected exit fees or clearly labels the limitation before founder evidence review.
- `high`: Disable debug stack traces in exposed environments. `APP_DEBUG=true` is not acceptable with unauthenticated or remotely reachable APIs.
- `high`: Make OKX demo/live mode explicit and fail-safe so a missing `.env` or config fallback cannot silently switch expected environment behavior.
- `medium`: Fix or explicitly reason-code truncated signal/decision id collision risk, missing-indicator coercion to `0.0`, exact MACD-crossover invisibility, raw timeframe `KeyError` in Hyperliquid adapter, overly broad exchange exception flattening, and OKX public candle instrument-type assumptions.
- `low`: Revisit Hyperliquid nonce burst safety and the fact that `EXECUTION_DRY_RUN=true` is currently a major final guard between safe local work and multi-exchange live order placement.
- `strategy-validation`: Track external strategy concerns before paper trading: no hard stop-loss, narrow RSI bands, lagging MACD exits, optimistic same-candle fills, long-only bear-market exposure, cosmetic confidence-score risk, handcrafted parameters, and missing out-of-sample/risk-adjusted evidence. These are not approved rule changes; they are evidence-review questions.

Paper/live trading remains blocked until at least the critical and high items above are fixed, tested, and reviewed.

## Later Phase Shape

- Phase 7: controlled automation around the existing single-target path. Accepted complete.
- Phase 8.0: operator-grade observability, manual-resolution inspection, approval/automation state depth, submitted-order handoff safety inspection, and concurrency/lease visibility. Implemented; not SOR.
- Phase 8.0.1 / 8.0.2: Obsidian baseline cleanup and active submit-lease operator-summary truth hotfix. Implemented.
- SV1.0-SV1.13.2 plus the 2026-05-05/2026-05-06 research passes: Strategy Validation research track. Implemented through intended local DB readiness, unique canonical import requirements, market-identity bootstrap, operator-verified non-trading identity write guard, complete requirement-aware candle-import preflight, guarded canonical candle bundle import, explicit partial-persistence reporting, blocked import run truth, readiness-only checklist reporting, guarded import attempt reporting, public BTC/ETH/SOL Hyperliquid identity verification, January archival/vendor-data-required labeling, complete local 9-file Hyperliquid public YTD/recent file preparation, supported-venue public candle readiness across Hyperliquid/Aster/Binance/OKX/Coinbase/Kraken, the operator-approved Hyperliquid 9-file guarded import with `25848` candles inserted, closeout verification of DB/repo state, first Hyperliquid public campaign evidence packs, a static local evidence dashboard for founder review, SV1.13.1 interpretation truth separating grouped research sums from scenario-level evidence, and SV1.13.2 dynamic-equity capital sizing for per-scenario account-style evidence.
- Later Phase 8.x: manual-resolution markers or deeper operator dashboard read-only surfaces if Phase 8.0 keeps the mutation boundary clean.
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
- Broader dashboard/control-plane UI beyond the local Strategy Validation evidence viewer.
- Strategy Validation evidence review and historical candle data readiness.
- Alerts.
- Strategy family expansion.

## Non-Negotiable Boundary

Do not implement optimization language before the system has the data and controls to support it.

## Related Notes

- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Known Issues Index]]
- [[30 Strategy/Product North Star]]
