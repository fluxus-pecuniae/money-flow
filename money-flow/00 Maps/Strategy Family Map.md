# Strategy Family Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the current strategy taxonomy. It separates production-derived rules, source reconstruction, repair variants, discovery ideas, and audit status so evidence-only work is not mistaken for production approval.

## Current Money Flow v1.2

| Field | Current Truth |
| --- | --- |
| status | `canonical_baseline` |
| implementation | Current derivative Money Flow implementation |
| sleeves | `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, `sleeve_1d` |
| core logic | EMA5 / EMA10 / SMA20 alignment, RSI sleeve bands, MACD gates, entry-quality and invalidation logic |
| canonical evidence | SV2.0.2 DB-imported Hyperliquid public-mainnet evidence, timestamp `20260512T064916Z` |
| production status | Production-derived strategy family, but not proven profitable and not production-ready for autonomous execution |
| paper/live status | No strategy paper runtime or live trading approval follows from evidence |

Current Money Flow v1.2 is Money Flow-inspired. It is not identical to the original Gerald Peters source system.

## Original Money Flow / MF-ORIG

| Field | Current Truth |
| --- | --- |
| status | `evidence_only` |
| source | `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf` |
| source concepts | Four stages, 5 EMA trigger, 10 EMA context, 20 SMA stage line, 50/200 SMA context, RSI profit-taking, MACD/TSI warning, support/resistance, pivots, structure stops, risk-based sizing |
| implemented track | MF-ORIG-EV1, MF-ORIG-EV1.1, MF-ORIG-EV2 |
| accounting truth | MF-ORIG-EV1.1 event-ledger accounting and peak-to-trough drawdown supersede pre-hotpatch EV1 conclusions |
| current outcome | No MF-ORIG hypothesis is production-approved |

MF-ORIG-EV2 includes four source-faithful 1% risk-sizing hypotheses plus four founder-requested full-equity comparison counterparts. The full-equity rows are comparison lanes, not source-faithful risk sizing.

## SOR Repair Variants

| Phase | Status | Current Truth |
| --- | --- | --- |
| SOR-EV1 | `diagnostic_only` / `evidence_only` | Loss anatomy and completed-trade overlays over canonical SV2.0.2 packs. |
| SOR-EV2 | `true_forward_replay` / `evidence_only` | Fixed/ATR/recent-low/large-bear exits and rejected-signal variants replayed true-forward. No variant promoted. |
| SOR-EV2.1 | `dashboard_display_only` | Evidence Lab matrix/panels for SOR bundles. |
| SOR-EV2.2 | `dashboard_display_only` | Evidence Lab chart overlays for baseline vs variant context. |
| SOR-EV3 | `true_forward_replay` / `candidate_for_review_only` | `avoid_low_rolling_range_50` is the strongest founder-review candidate but remains blocked by drawdown/control-pocket risk. |

`promising_*` labels are founder-review labels only. They do not approve a rule change, paper runtime, or live trading.

## STRAT-EV Discovery

| Field | Current Truth |
| --- | --- |
| status | `plan_only` unless a committed report/JSON appears |
| current named idea | `regime_gated_trend` |
| relationship to Money Flow | Separate discovery track, not production Money Flow v1.2 |
| evidence status | Not evidence unless a committed STRAT-EV report/JSON exists |

## EV-AUDIT

| Field | Current Truth |
| --- | --- |
| status | `audit_only` |
| latest phase | EV-AUDIT1 |
| verdict | No clean strategy candidate is production-ready or paper-runtime-approved |
| best review candidate | `avoid_low_rolling_range_50`, still blocked by drawdown/control-pocket risk |
| paper observation | `paper_observation_ready_with_conditions` for future PT-RT1, not approval |

## Status Labels

| Label | Meaning |
| --- | --- |
| `canonical_baseline` | Current baseline evidence source for comparison. |
| `evidence_only` | Research result, not production/paper/live approval. |
| `diagnostic_only` | Useful attribution or overlay; not candidate evidence by itself. |
| `plan_only` | Idea exists but no committed evidence run. |
| `not_implemented` | No implemented code/report. |
| `rejected` | Hard rejected under current evidence gate. |
| `candidate_for_review_only` | Worth founder review; not approved. |
| `blocked` | Cannot proceed without explicit blocker resolution. |

