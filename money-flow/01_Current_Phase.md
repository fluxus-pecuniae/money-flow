# Current Phase

## Phase

Current implemented phase: `Phase 8.0.1`

Proposed next phase: `Phase 8.1`

## Purpose

Phase 7.6 is accepted complete. It closed out the controlled automation chain with safety-diligence proof:

- Walk the full approval-gated chain from existing recommendation through submitted-order handoff.
- Prove each action consumes only the exact current-lineage approval for its stage.
- Prove dry-run, approval creation, generic administrative consumption, action-specific consumption, readiness, and submitted-order handoff remain distinct.
- Prove `consumption_pending` is bounded and repeat calls reuse existing submitted-order truth without another adapter submit.
- Preserve readiness, live-submit, routed-submit, adapter/account, submit lease, and uncertainty gates as authoritative.

Phase 8.0 is implemented as the first operator-grade observability and manual-resolution inspection phase. It makes the existing chain easier to inspect, debug, reconcile, and manually manage without adding smart routing, new action stages, broad auto-submit, route-executor behavior, fanout, target reselection, or trading-action mutation from inspection.

Phase 8.0.1 is workflow hygiene only. It resolves the dirty Obsidian project-memory baseline left after Phase 8.0 by accepting the earlier Obsidian refresh as intentional, updating stale proposed-Phase-8 wording, confirming the root memory file remains a pointer, and cleaning the working tree before Phase 8.1.

## Accepted Baseline

- Phase 7.0 added non-executing routing automation policy and dry-run plans.
- Phase 7.1 added durable approval records and revocation/consumption state.
- Phase 7.1.1 made approvals expiry-safe, lineage-scoped, and active-scope unique.
- Phase 7.1.2 prevented manual-only and dry-run-only steps from receiving active approvals.
- Phase 7.2 added approval-gated recommendation acceptance into one target choice.
- Phase 7.2.1 made recommendation acceptance and approval consumption coherent in one commit.
- Phase 7.3 added approval-gated target-choice conversion into one child intent and integrated Obsidian workflow.
- Phase 7.3.1 hardened target-choice conversion negative tests.
- Phase 7.4 added approval-gated prepared-order preview/readiness inspection only.
- Phase 7.5 added approval-gated submitted-order handoff only.
- Phase 7.5.1 recorded `consumption_pending` approval truth when submitted-order persistence succeeds but approval consumption fails afterward.
- Phase 7.6 closed Phase 7 with end-to-end safety regression and docs alignment only.
- Phase 8.0 added read-only operator routed workflow summary inspection by desired trade.
- Phase 8.0.1 resolved the Obsidian memory / working-tree baseline without product behavior changes.

## Hard Boundaries

Do not build:

- smart routing
- best-binding selection
- CBBO
- ranking/scoring
- fanout or split allocation
- target reselection
- route executor behavior
- broad auto-submit
- cross-binding or cross-venue recovery
- new exchange behavior
- submission/cancel/amend/retry from read-only inspection
- silent manual-resolution of exchange/account truth

## Phase 8.0 Outcome

Phase 8.0 is successful when operators can inspect the full routed workflow by desired trade, understand approval and automation state without raw payload parsing, see manual-resolution needs and submit-lease uncertainty, see current blocking/uncertainty reasons, and identify the next safe manual action without creating target choices, child intents, readiness evaluations, submitted orders, exchange calls, recovery actions, or route-executor behavior.

Phase 8.0.1 is successful when the full Obsidian project memory is resolved, root memory remains pointer-only, Obsidian notes match implemented Phase 8.0 truth, review packaging remains clean, and the working tree is clean.

## Current Outcome

- Obsidian command center/current phase/decision log/coordination notes are now part of the required agent workflow.
- Full strategic project memory lives at `money-flow/Project_Memory/money_flow_project_memory.md`.
- Repo-root `money_flow_project_memory.md` is a compatibility pointer only.
- The approval-gated `recommendation_acceptance` action hook creates or reuses one target choice and consumes the matching approval.
- The approval-gated `target_choice_conversion` action hook creates or reuses one child intent and consumes the matching approval.
- The approval-gated `prepared_order_preview_and_readiness` hook runs preview/readiness inspection for exactly one existing child intent.
- The approval-gated `submitted_order_handoff` hook submits exactly one already-ready child intent through the existing explicit submit path.
- Phase 7.5.1 records `consumption_pending` approval state if submitted-order persistence succeeds but approval consumption fails afterward.
- Phase 7.6 adds closeout regression coverage proving the accepted hooks remain stage-specific and no-SOR.
- Phase 8.0 adds `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}` as a read-only operator summary over existing routed workflow artifacts, approval states, gate truth, manual-resolution requirements, submitted-order handoff safety, and submit-lease/concurrency state.
- Phase 8.0.1 accepts the prior Obsidian refresh as intentional memory baseline and updates it to current Phase 8.0/8.0.1 truth.
- Recovery, route execution, fanout, scoring, CBBO, target reselection, cross-venue retry, and broad auto-submit remain deferred.

## Next Phase Shape

Phase 8.1 should define explicit manual-resolution marker or administrative reconciliation workflows only after architecture review. It should keep operator acknowledgement separate from exchange/account truth and must not attach submit/cancel/amend/retry behavior to inspection.
