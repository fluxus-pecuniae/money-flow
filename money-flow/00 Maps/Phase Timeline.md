# Phase Timeline

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This timeline is intentionally current-first. Older UAT and platform phases remain preserved as historical plumbing context, but they are no longer the center of the active project brain.

## Current Tracks

| Track | Current Role | Status |
| --- | --- | --- |
| Paper Trading / PT-RT | Forward public-mainnet paper-observation substrate with synthetic 10,000 USDC ledgers, candle-truth data health, compact logging, persisted runtime state, dashboard Start/Stop control, and 20 USDC testnet probe audit/order-shape rows. | Current operational focus; fresh runs still need review before forward-observation evidence claims. |
| Strategy Validation SV2.x | Canonical historical evidence baseline plus founder-approved 1D breadth review. | SV2.0.2 is canonical multi-timeframe evidence; SV2.1 is 1D founder-review breadth only. |
| SOR / Variant Review | Evidence-only stop, exit, entry, and low-volatility/chop diagnostics. | SOR-EV1 through SOR-EV3 complete; no variant promoted. |
| MF-ORIG | Source-faithful Original Money Flow reconstruction and comparison lanes. | MF-ORIG-EV2 complete; no original hypothesis approved. |
| Dashboard / Founder Review | Human-readable Strategy, Historical Replay, Evidence, The Lab, Audit, and Paper Trading surfaces. | Current UI focus; no order controls and no canonical evidence regeneration from date filters. |
| Obsidian / Repo Governance | Keep current-truth notes, maps, coordination, and repo memory aligned with implementation. | Active cleanup target. |

## Current Product Milestones

- `SV2.0.2`: canonical DB-imported Money Flow v1.2 evidence across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX and 15m/1h/4h/1d.
- `SV2.1`: founder-approved 1D period evidence for the requested/resolved universe, including 2024/2025/YTD/ALL where public candles exist.
- `SOR-EV1` through `SOR-EV3`: evidence-only loss anatomy, true-forward variants, overlays, and avoid-sideways/low-volatility drilldown.
- `MF-ORIG-EV2`: Original Money Flow research lanes and full-equity comparison rows for founder review.
- `EV-AUDIT1`: audit verdict that no clean strategy candidate is promoted and evidence is for visual review/hypothesis filtering only.
- `PT-RT1.1A` through `PT-RT1.3`: real-time public-mainnet paper-observation substrate, 10 lanes, persisted state, compact logs, candle-truth data health, and separate testnet probe audit lane.
- `PT-RT1.2.1`: founder dashboard cleanup for chart-first Paper Trading review, paginated signals/trades, runtime ledger display, and chart markers.

## Current State

Current implemented milestone: `PT-RT1.2.1` Paper Trading dashboard polish on top of completed `PT-RT1.3` candle-truth data health.

Current next step: run and review a fresh PT-RT observation session before treating runtime artifacts as forward-observation evidence. Review candle readiness, mid warnings, duplicate-open blocking, synthetic open/close rows, compact-log stats, and 20 USDC testnet probe audit rows.

Live trading is not approved. Live exchange order submission is not approved. Production Money Flow rule changes and variant promotions are not approved.

## Historical Plumbing Archive

The following tracks are important context but not the active project center:

| Track | Range | Historical Meaning |
| --- | --- | --- |
| Platform foundation | Phase 1-4 | Strategy, planning, risk, execution, exchange/data/state, and submitted-order lifecycle substrate. |
| Routing substrate | Phase 5-6 | Non-executing routing assessment, recommendation, target choice, conversion, readiness, and explicit same-target handoff. |
| Controlled automation | Phase 7 | Approval-gated same-target action hooks with safety closeout; no full SOR. |
| Operator observability | Phase 8 | Read-only routed workflow/manual-resolution inspection and submit-lease truth. |
| UAT / sandbox plumbing | UAT0-UAT4.2, PT0-PT0.0.3 | Safety, public-read-only connectivity, sandbox/testnet lifecycle, dashboard cockpit, TradingView, and historical replay plumbing. |
| Strategy Validation SV1 | SV1.0-SV1.18.1 | First Hyperliquid public evidence cycle and historical ETH 1h UAT candidate freeze. |

Use [[00 Maps/UAT Roadmap|UAT Roadmap]] for the detailed UAT/sandbox history. Use [[00 Maps/Strategy Validation Map|Strategy Validation Map]] for SV/SOR/MF-ORIG evidence details.

## Interpretation Rule

Current work should lead with Paper Trading, SV2.x evidence, SOR/MF-ORIG review, and dashboard founder usability. UAT and earlier platform phases are historical guardrails unless a task explicitly reopens sandbox routing or platform plumbing.
