# DOCS-OB2.1 Markdown Current Truth Refresh

## Executive Summary

DOCS-OB2.1 refreshes repo Markdown and Obsidian current-truth surfaces so humans and Codex agents can quickly understand the project as it exists now. The active operating surface is `Paper Trading` / PT-RT1.5.1. Historical evidence, research variants, testnet plumbing, and forward synthetic observation are now described as separate things.

This is documentation/governance only. It changes no Money Flow strategy rules, runtime behavior, evidence packs, exchange endpoints, testnet transport gates, live trading approval, or production approval.

## Why The Refresh Was Needed

The Markdown estate had grown into a chronological phase diary. Current truth was present but mixed with older UAT/PT/SV wording, including historical PT0 paper/sandbox approval language, older 20 USDC probe wording, and PT-RT1.1/PT-RT1.3 phrases that could be misread as current. DOCS-OB2.1 makes the top-level surfaces current-first and labels selected older reports as historical.

## Files Updated

- `README.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `docs/architecture.md`
- `docs/strategy.md`
- `apps/dashboard/README.md`
- `apps/dashboard/DESIGN.md`
- `money-flow/00_Money_Flow_Command_Center.md`
- `money-flow/01_Current_Phase.md`
- `money-flow/03_Decision_Log.md`
- `money-flow/05_Agent_Coordination.md`
- `money-flow/Project_Memory/money_flow_project_memory.md`
- `money-flow/00 Maps/Current State Dashboard.md`
- `money-flow/00 Maps/Phase Timeline.md`
- `money-flow/00 Maps/Paper Observation Roadmap.md`
- `money-flow/00 Maps/Dashboard and UI Map.md`
- `money-flow/00 Maps/Data Source and Market Data Map.md`
- `money-flow/00 Maps/Evidence and Backtesting Map.md`
- `money-flow/00 Maps/Strategy Family Map.md`
- `money-flow/10 Strategy/Strategy Status Register.md`
- `tests/test_operational_docs.py`

## Files Marked Historical

Historical banners were added to selected high-risk old phase reports and notes, including representative UAT, PT0, PT-RT1.1/1.2/1.3, SV1, Strategy, and Phase 7/8 notes. The banner points readers back to `money-flow/00_Money_Flow_Command_Center.md` and the latest PT-RT/SV/audit docs.

## Current Strategy Taxonomy

- Current Money Flow v1.2 baseline: `production_baseline_logic`, but `not_production_approved` and `not_live_approved`.
- SOR repair variants: `evidence_only` and synthetic paper observation where included as PT-RT lanes.
- MF-ORIG source reconstruction: `reference_only` / `evidence_only`, not production strategy.
- Wildcard paper lanes: `synthetic_paper_only`.
- SV2/SV2.1 evidence tracks: historical evidence, not runtime.
- Hyperliquid testnet lifecycle: `testnet_plumbing_only`.

## Current Evidence Taxonomy

- SV2.0.2 canonical historical evidence is the canonical multi-timeframe baseline.
- SV2.1 broad 1D evidence is separate founder-review research.
- Historical Replay is visualization from generated chart/trade JSON.
- Evidence tab is canonical evidence summaries and generated replay rows.
- The Lab is research variants and overlays.
- Dashboard date filters are display-only recalculations, not canonical evidence regeneration.

## Current Dashboard Taxonomy

Visible tabs are:

- `Paper Trading`
- `Historical Replay`
- `Evidence`
- `The Lab`
- `Audit`
- `Strategy`

The legacy `Experiments` tab remains absent. UAT panels are historical/regression context and are not the current founder workflow.

## Runtime / Paper / Testnet Boundaries

- PT-RT1.5.1 is the current forward-observation runtime surface.
- Active Week 1 timeframes are `1h`, `4h`, and `1d`.
- `15m` is paused for Week 1 noise reduction and cannot trigger active-week entries or testnet lifecycle rows.
- Each paper lane has an independent synthetic 10,000 USDC ledger.
- Candidate/MF-ORIG/wildcard lanes cannot send testnet orders.
- Only fresh post-start Money Flow v1.2 baseline opens can trigger fixed 25 USDC Hyperliquid testnet transport after PT-RT1.5.1 gates pass.
- Public mainnet candles remain strategy truth.
- Testnet fills never update synthetic PnL.
- Live trading and production strategy approval remain not approved.

## Stale Phrases Fixed

- Older PT-RT1.1/PT-RT1.2/1.3 wording was moved to historical context where it appeared in current-truth files.
- Old 20 USDC probe wording was replaced in current dashboard docs with PT-RT1.5.1 fixed 25 USDC baseline-only transport wording.
- The dashboard design title was changed from UAT-specific wording to founder dashboard wording.
- Active dashboard tab names were aligned to `Paper Trading`, `Historical Replay`, `Evidence`, `The Lab`, `Audit`, and `Strategy`.
- Historical PT0 paper/sandbox approval language was reframed as audit context rather than current production strategy approval.

## Remaining Docs Debt

- Many older phase reports still contain their original wording by design. They are retained for audit/history and should not be rewritten unless a future phase needs them.
- README, architecture, and strategy still preserve deep platform chronology below current-first summaries. A future docs phase could move that chronology into dedicated archive pages.
- Runtime artifact docs remain separate from ignored runtime artifacts; future PT-RT review docs should keep artifact paths and current scope explicit.

## Validation Status

Status: `implemented_verified`.

Validation completed:

- `.venv/bin/python -m json.tool docs/doc_ob2_1_markdown_current_truth_refresh_summary.json`
- `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
- `.venv/bin/python -m compileall core services apps tests scripts`
- `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
- `.venv/bin/python -m pytest -q tests/test_uat41_exchange_dashboard_redesign.py tests/test_operational_docs.py`
- `.venv/bin/python -m pytest -q --ignore=tests/test_migrations.py` (`1060 passed`)
- `node --check apps/dashboard/evidence-dashboard.js`
- `git diff --check`
- `.venv/bin/python scripts/create_review_bundle.py --output /Users/tercirafael/money-flow-docs-ob2.1-review.zip`
- Review bundle scan: 551 entries, 0 excluded path hits, 0 private-key/Bearer-token pattern hits.

Review bundle:

- `/Users/tercirafael/money-flow-docs-ob2.1-review.zip`
