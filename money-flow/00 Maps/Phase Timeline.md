# Phase Timeline

Up: [[Money Flow Command Center]]

## Condensed Timeline

- Phase 1: platform scaffold, domain boundaries, API/db/service shape.
- Phase 2: exchange/data/state foundation.
- Phase 3: indicators, Money Flow strategy family, decisions, repo governance.
- Phase 3.3 to 3.5: client, venue account, mandate, binding, component hierarchy.
- Phase 4: multi-venue adapters, desired-trade planning, risk, readiness, submission, lifecycle.
- Phase 5: non-executing routing substrate, target choices, conversion, routed readiness/submission/lifecycle inspection, route-readiness audit.
- Phase 6: controlled non-executing recommendation, explicit acceptance, recommendation-backed conversion/readiness/submission, workflow inspection, submit uncertainty hardening.
- Phase 7.0: dry-run automation plan substrate.
- Phase 7.1: durable approval gates.
- Phase 7.1.1: approval expiry, stale lineage, scope uniqueness.
- Phase 7.1.2: approvable-step truth.
- Phase 7.2: approval-gated recommendation acceptance action hook.
- Phase 7.2.1: atomicity hotpatch around approval-gated recommendation acceptance.
- Phase 7.3: approval-gated target-choice conversion and Obsidian strategic brain.
- Phase 7.3.1: target-choice conversion negative-test hardening.
- Phase 7.4: approval-gated preview/readiness inspection only.
- Phase 7.5: approval-gated submitted-order handoff only.
- Phase 7.5.1: `consumption_pending` approval truth after submitted-order handoff.
- Phase 7.6: controlled automation closeout safety proof.
- Phase 8.0: read-only operator workflow observability and manual-resolution inspection.
- Phase 8.0.1: Obsidian memory / working-tree baseline cleanup.
- Phase 8.0.2: active submit-lease operator-summary truth hotfix.
- SV1.0-SV1.4.1: Money Flow strategy validation, report truth, comparative batches, regime/coverage diagnostics, evidence campaigns, review discipline, and collision-safe evidence packs.
- SV1.5-SV1.5.1: historical-data readiness, offline public candle import, and import/config integrity.
- SV1.6-SV1.9: canonical evidence review, DB/schema/migration/candle data-gap reporting, schema gate, DB-target reporting, and canonical candle import requirements. No first real canonical evidence packs were generated.
- SV1.9.1: ambiguous DB-target evidence-generation blocking, default naive timestamp rejection, import provenance strengthening, and Obsidian current-truth refresh.
- SV1.10: intended local `money_flow` DB creation/migration truth, required table verification, 18 unique canonical candle import requirements, and no evidence packs because candle count is zero.
- SV1.11: research-only canonical market identity seed/verify tooling, evidence-review identity readiness, and candle-import preflight before candle import.
- SV1.11.1: SOR P2 hardening requiring explicit operator verification for non-dry-run identity writes and requirement-aware candle preflight before bulk import.
- SV1.11.2: governance hardening that keeps research market identity non-trading and requires complete one-to-one requirement-aware preflight mapping.
- SV1.12: guarded canonical candle bundle import requiring intended migrated DB truth, operator-verified non-trading identity, complete one-to-one requirement-aware preflight, and hardened importer success; no evidence packs generated.
- SV1.12.1: guarded import run / blocked-run truth; intended DB is reachable/current with zero candles, identity rows and candle files are missing, partial-persistence semantics are explicit, and unmapped inputs / missing requirements are operator-visible.
- SV1.12.2: readiness-only identity/file report; intended DB remains reachable/current with zero candles, operator-verified identity and candle files are still missing, exact 18-file requirements are documented, and no candles or evidence packs are generated.
- SV1.12.3: guarded import attempt wrapper; intended DB remains reachable/current, operator verification and all 18 candle files are still missing, no identity seed/import/evidence packs occurred.
- SV1.12.x 2026-05-05 research: public Hyperliquid `meta` verifies BTC/ETH/SOL identity values and updates the non-trading manifest; 12 local `1h`/`4h` CSVs are produced under `/tmp`, six `15m` files remain missing, no identity seed/import/evidence packs occurred.
- SV1.12.4 2026-05-05 public-data campaign: January 2026 is marked archival/vendor-data-required, a 9-file public YTD/recent Hyperliquid campaign config is added, all 9 local public CSVs are produced under `/tmp`, and Hyperliquid preflight remains blocked by missing DB identity.
- SV1.12.5 2026-05-06 supported-venue public-data readiness: Hyperliquid remains nearest guarded-import path; Aster/Binance produce 18 additional complete native-trade-count candidate files, OKX/Coinbase complete close-slot files are blocked by missing public trade count, and Kraken is blocked by incomplete public REST coverage.
- SV1.12.5 2026-05-06 operator-approved Hyperliquid public import: BTC/ETH/SOL research identity is seeded as non-trading/non-strategy-eligible, all 9 public YTD/recent files pass requirement-aware preflight, guarded import inserts `25848` candles, and evidence packs remain deferred.
- SV1.12.5.1 2026-05-06 closeout: repo state, DB target/schema, BTC/ETH/SOL identity, row counts by symbol/timeframe, no-evidence-pack boundary, and review-bundle hygiene are verified before SV1.13.

## Current Next Shape

See [[40 Operations/Future Work Roadmap]].

Current implemented phase: `SV1.12.5.1` import state / repo state closeout; Hyperliquid public campaign import is verified and evidence generation remains deferred.

The next proposed Strategy Validation work is post-import Hyperliquid evidence review and evidence-pack generation only if DB/schema/identity/candle data-readiness audits are clean. January 2026 remains archival/vendor-data-required. Aster/Binance identity verification, OKX/Coinbase trade-count sourcing, and Kraken archive/vendor/operator data are broader venue-comparison follow-ups. If data-readiness is incomplete, SV1.13 should report the remaining gaps instead of forcing evidence conclusions. Paper-trading design remains deferred until founder/operator evidence review justifies it. Phase 8.1 remains deferred until explicitly scoped.

## Strategic Memory

See [[40 Operations/Operational Memory]] for the repo memory workflow and [[30 Strategy/Product North Star]] for why the platform exists.
