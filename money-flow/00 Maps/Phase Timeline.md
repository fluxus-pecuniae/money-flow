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

## Current Next Shape

See [[40 Operations/Future Work Roadmap]].

Current implemented phase: `SV1.12.1`.

The next proposed Strategy Validation work is completing guarded canonical candle import after BTC/ETH/SOL research identity and all 18 timezone-explicit candle files are available, then SV1.13 post-import canonical evidence review/evidence-pack generation only after guarded import status is complete and data-readiness audits are clean. If data remains incomplete, SV1.13 should report the remaining gaps instead of forcing evidence conclusions. Paper-trading design remains deferred until founder/operator evidence review justifies it. Phase 8.1 remains deferred until explicitly scoped.

## Strategic Memory

See [[40 Operations/Operational Memory]] for the repo memory workflow and [[30 Strategy/Product North Star]] for why the platform exists.
