# Current Phase

## Phase

Current implemented phase: `SV1.0.1`

Proposed next phase: `SV1.1` strategy-validation depth after SV1.0.1 report review. `Phase 8.1` remains deferred until explicitly scoped.

## Purpose

Phase 7.6 is accepted complete. It closed out the controlled automation chain with safety-diligence proof:

- Walk the full approval-gated chain from existing recommendation through submitted-order handoff.
- Prove each action consumes only the exact current-lineage approval for its stage.
- Prove dry-run, approval creation, generic administrative consumption, action-specific consumption, readiness, and submitted-order handoff remain distinct.
- Prove `consumption_pending` is bounded and repeat calls reuse existing submitted-order truth without another adapter submit.
- Preserve readiness, live-submit, routed-submit, adapter/account, submit lease, and uncertainty gates as authoritative.

Phase 8.0 is implemented as the first operator-grade observability and manual-resolution inspection phase. It makes the existing chain easier to inspect, debug, reconcile, and manually manage without adding smart routing, new action stages, broad auto-submit, route-executor behavior, fanout, target reselection, or trading-action mutation from inspection.

Phase 8.0.1 is workflow hygiene only. It resolves the dirty Obsidian project-memory baseline left after Phase 8.0 by accepting the earlier Obsidian refresh as intentional, updating stale proposed-Phase-8 wording, confirming the root memory file remains a pointer, and cleaning the working tree before Phase 8.1.

Phase 8.0.2 is a narrow operator-summary truth hotfix. It makes active unexpired child-intent submit leases block repeat-submit safety and next-safe-action truth as `submission_in_progress`, while preserving terminal uncertainty and stale pre-adapter lease semantics. It adds no trading behavior, new action stage, manual-resolution mutation, route executor behavior, fanout, target reselection, ranking/scoring, CBBO, cross-venue retry, or auto-submit.

SV1.0 pivots to Strategy Validation. It adds the first Money Flow backtesting/reporting framework over persisted historical candles, reuses current Money Flow rules without optimization, simulates research-only trades with explicit capital/fee/slippage/sizing assumptions, and emits deterministic operator-readable reports. It creates no live desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing artifacts, approval changes, or exchange calls.

SV1.0.1 hardens Strategy Validation research truth. It adds explicit fill timing assumptions, supports next-candle open/close fills in addition to same-candle close research-only fills, separates closed-trade drawdown from mark-to-market drawdown, and expands the Markdown report for founder/operator review. It changes no Money Flow rules, optimization, paper/live trading, routing, execution automation, exchange calls, or live artifacts.

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
- Phase 8.0.2 fixed active submit-lease operator-summary truth without product behavior changes.
- SV1.0 added Money Flow strategy validation/backtesting reports without live execution artifacts or strategy-rule optimization.
- SV1.0.1 hardened Money Flow validation fill-timing/drawdown/report truth without strategy-rule changes.

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
- live trading artifacts from strategy validation
- Money Flow rule optimization before evidence review
- treating backtest output as proof of future profitability

## Phase 8.0 Outcome

Phase 8.0 is successful when operators can inspect the full routed workflow by desired trade, understand approval and automation state without raw payload parsing, see manual-resolution needs and submit-lease uncertainty, see current blocking/uncertainty reasons, and identify the next safe manual action without creating target choices, child intents, readiness evaluations, submitted orders, exchange calls, recovery actions, or route-executor behavior.

Phase 8.0.1 is successful when the full Obsidian project memory is resolved, root memory remains pointer-only, Obsidian notes match implemented Phase 8.0 truth, review packaging remains clean, and the working tree is clean.

Phase 8.0.2 is successful when the operator summary reports an active unexpired submit lease as `submission_in_progress`, blocks repeat-submit safety with `blocked_while_submission_in_progress`, reports the next safe operator action as not safe to automate, preserves terminal uncertainty behavior, leaves expired pre-adapter active leases stale-replaceable, and remains read-only.

SV1.0 is successful when operators/researchers can run a deterministic Money Flow validation report over persisted candles, inspect assumptions and core metrics, compare component/timeframe output where data exists, and verify validation remains separate from live routing/execution.

SV1.0.1 is successful when fill timing is explicit, same-candle close fills are labeled research-only/optimistic, closed-trade and mark-to-market drawdown are distinct, Markdown is useful for founder/operator review, and validation still creates no live artifacts or strategy-rule changes.

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
- Phase 8.0.2 makes the operator summary block approval-gated submit as the next safe action while an unexpired `active` submit lease is already in progress.
- SV1.0 adds `services/strategy_validation` and `scripts/run_money_flow_backtest.py` for deterministic Money Flow research reports from persisted candles.
- SV1.0.1 adds selectable validation fill timing, mark-to-market drawdown, expanded Markdown/JSON report detail, and direct research-truth tests.
- Recovery, route execution, fanout, scoring, CBBO, target reselection, cross-venue retry, and broad auto-submit remain deferred.

## Next Phase Shape

SV1.1 should be scoped after reviewing SV1.0.1 output. Likely candidates are deeper historical data coverage, regime analysis, report persistence if useful, and paper-trading readiness. Phase 8.1 should remain deferred until explicitly scoped; when it resumes, it should define explicit manual-resolution marker or administrative reconciliation workflows only after architecture review, keep operator acknowledgement separate from exchange/account truth, and not attach submit/cancel/amend/retry behavior to inspection.
