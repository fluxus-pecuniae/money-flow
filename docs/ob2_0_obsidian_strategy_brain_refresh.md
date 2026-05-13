# OB2.0 Obsidian Strategy Brain Refresh

## Executive Summary

Status: `implemented`

OB2.0 refreshes the Obsidian strategy brain and repo governance notes after EV-AUDIT1. It creates a clearer separation between current Money Flow v1.2, Original Money Flow / MF-ORIG, SOR repair variants, STRAT-EV discovery, canonical evidence methodology, Historical Replay / dashboard visualization, UAT sandbox plumbing, and future PT-RT1 real-time paper observation.

No production Money Flow rules changed. No evidence packs or dashboard chart data were regenerated. No exchange endpoints were called. No API keys were used. No paper runtime or live trading was approved.

## Obsidian Change Plan

| Area | Decision |
| --- | --- |
| Canonical command center | Updated `money-flow/00_Money_Flow_Command_Center.md` as the single current-truth entrypoint. |
| Duplicate command center | Converted `money-flow/Money Flow Command Center.md` into a concise pointer. |
| Strategy taxonomy | Created dedicated strategy-family map and strategy status register. |
| Evidence methodology | Created dedicated evidence/backtesting map. |
| Data truth | Created data-source and market-data map. |
| Dashboard truth | Created dashboard/UI map to separate display-only data from canonical evidence. |
| Original source | Created Original Money Flow source note and moved the PDF into `money-flow/90 Reference/`. |
| EV-AUDIT1 | Created EV-AUDIT1 Obsidian summary note. |
| Paper observation | Created PT-RT paper-observation roadmap note. |
| Stale notes | Converted or refreshed stale current-truth notes instead of deleting historical context. |

## Notes Created

- `money-flow/00 Maps/Strategy Family Map.md`
- `money-flow/00 Maps/Evidence and Backtesting Map.md`
- `money-flow/00 Maps/Data Source and Market Data Map.md`
- `money-flow/00 Maps/Dashboard and UI Map.md`
- `money-flow/00 Maps/Paper Observation Roadmap.md`
- `money-flow/10 Strategy/Strategy Status Register.md`
- `money-flow/10 Strategy/Original Money Flow Source Notes.md`
- `money-flow/20 Evidence/EV-AUDIT1 Summary.md`
- `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf`

## Notes Updated

- `money-flow/00_Money_Flow_Command_Center.md`
- `money-flow/01_Current_Phase.md`
- `money-flow/02_Product_North_Star.md`
- `money-flow/03_Decision_Log.md`
- `money-flow/05_Agent_Coordination.md`
- `money-flow/00 Maps/Current State Dashboard.md`
- `money-flow/00 Maps/Strategy Validation Map.md`
- `money-flow/00 Maps/UAT Roadmap.md`
- `money-flow/40 Operations/Future Work Roadmap.md`
- `money-flow/40 Operations/Phase 8 Focus.md`
- `money-flow/Project_Memory/money_flow_project_memory.md`

## Notes Converted To Pointers

- `money-flow/Money Flow Command Center.md`
- `money-flow/30 Strategy/Money Flow Strategy Lab.md`

## Stale Notes Found / Fixed

Status: `verified`

The refresh removed or superseded stale current-truth statements that treated PT0.0.3, UAT3.0.4, SOR-EV1, or old SV1/SV2 blockers as the active next phase. Historical notes remain available, but active/current notes now point to the canonical command center and current maps.

Known stale-danger themes handled:

- Old “next SOR-EV1” language.
- Old “PT0.0.3 current” pointer language.
- Old “PDF not present locally” source-availability truth.
- Old “SV2.0.1 canonical packs blocked” truth.
- Old “UAT3.1 next” Phase 8 focus language.

## Current Strategy Taxonomy

| Family | Current Status |
| --- | --- |
| Money Flow v1.2 | Current derivative implementation and canonical SV2.0.2 baseline. |
| Original Money Flow / MF-ORIG | Source-faithful evidence track from Gerald Peters PDF; no hypothesis promoted. |
| SOR repair variants | Evidence-only repair/variant research; no variant promoted. |
| STRAT-EV discovery | Plan-only unless a committed report/JSON exists. |
| EV-AUDIT | Audit-only evidence and methodology review; no production-ready candidate. |

## Current Evidence Taxonomy

| Evidence Type | Meaning |
| --- | --- |
| `canonical_evidence` | DB-imported hardened candle evidence packs, currently SV2.0.2 baseline. |
| `true_forward_replay` | Chronological replay using only available current/past candle data. |
| `completed_trade_overlay_estimate` | Diagnostic overlay over completed baseline trades, not production candidate evidence. |
| `lookahead_diagnostic_proxy` | Diagnostic only; not candidate evidence. |
| `dashboard_display_only` | Visualization/date-filter/browser recalculation only. |
| `compact_replay_only` | Provisional or lightweight replay summary, not canonical evidence. |
| `plan_only` | Proposed but not implemented evidence. |

## Current Data / Backtesting Model

Canonical baseline: SV2.0.2.

- Timestamp: `20260512T064916Z`.
- Source: Hyperliquid public mainnet DB-imported candles.
- Symbols: BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX.
- Deferred: SHIB/kSHIB due venue unit semantics.
- Timeframes: 15m, 1h, 4h, 1d.
- Packs: 36.
- Evidence rows: 72.
- Capital: 10000 USDC per independent scenario.
- Sizing: dynamic equity.
- Fill assumptions: next_candle_open and next_candle_close.
- Known limitation: 15m/1h public 5000-candle horizon; 4h/1d Jan 2025 coverage where public data supports it.

Dashboard chart/trade JSON and date filters are display-only. They do not regenerate canonical evidence packs.

## Current Dashboard Model

Dashboard surfaces are documented in `money-flow/00 Maps/Dashboard and UI Map.md`.

| Surface | Use |
| --- | --- |
| Strategy | Current strategy/evidence status review. |
| Historical Replay | Candle/indicator/trade visualization from generated local replay JSON. |
| Evidence | Loaded canonical-pack summaries and run ledger comparisons. |
| Evidence Lab | SOR/MF-ORIG/variant/audit bundle review. |
| Audit Review | EV-AUDIT1 visual review. |
| UAT/paper panels | Sandbox/paper-plumbing visibility only, not strategy truth. |

## Current UAT / PT State

UAT sandbox/testnet plumbing remains separate from strategy evidence. PT0 paper/sandbox approval is Hyperliquid testnet/sandbox only and does not approve strategy paper runtime from EV-AUDIT1.

Live trading is not approved. Live exchange order submission is not approved. No production order automation is approved.

## Current Next Recommended Phase

Recommended next phase: `PT-RT1` real-time public market data + paper observation runtime.

Status: `needs_separate_scope`

PT-RT1 must be paper observation only: trusted public mainnet candles, fully closed candle detection, real-time indicators, internal 10,000 USDC paper ledger, signal arrows/logging, duplicate-signal protection, data-health handling, no exchange orders, no private/signed endpoints, no API keys, and no live trading.

## Remaining Known Obsidian Gaps

- Older deep-history notes remain intentionally historical and were not rewritten exhaustively.
- MF-ORIG evidence numbers were not regenerated after adding the PDF to the vault; future MF-ORIG work can reconcile exact PDF language.
- Dashboard-generated replay files remain ignored local artifacts, not canonical Obsidian evidence truth.

## Boundary Confirmation

- Production Money Flow rules changed: `false`
- Evidence packs generated: `false`
- Dashboard chart data regenerated: `false`
- Exchange endpoints called: `false`
- API keys used: `false`
- Orders submitted: `false`
- Paper trading newly approved: `false`
- Live trading approved: `false`
