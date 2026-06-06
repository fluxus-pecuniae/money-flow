# Current State Dashboard

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Today In One Sentence

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform; PT-RT1.6 prepares the founder-selected Week 2 Paper Trading slate with `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`, active `1h`/`4h`/`1d`, paused `15m`, warm-start fresh-signal gating, open-position MTM, and baseline-only fixed 25 USDC Hyperliquid testnet plumbing. No active run is assumed unless the local control server reports one. SV2.0.2 canonical evidence remains the historical baseline, SOR/MF-ORIG/STRAT tracks are separated, no clean production strategy candidate exists, and no live approval follows.

Historical context preserved for drift tests: SV1.18 closed the first evidence cycle; UAT0, UAT0.1, UAT0.2, UAT0.3, UAT1 public read-only connectivity, UAT1.1, UAT2, UAT2.1, UAT3.0, UAT3.0.6, UAT3.1, UAT3.2, UAT3.3, UAT3.4, UAT4.0, UAT4.1, UAT4.2, PT0, PT0.0.1, PT0.0.2, PT0.0.3, SV2.0, SV2.0.1, and SV2.0.2 are represented in the canonical command center and maps. UAT remains plumbing and behavior validation.

## Current Product State

Money Flow can generate strategy decisions, inspect Strategy Validation evidence, visualize Paper Trading/Historical Replay/Evidence/The Lab/Audit/Strategy data, and preserve UAT sandbox plumbing boundaries as historical guardrails.

Current strategy evidence uses Hyperliquid public mainnet DB-imported candles. Dashboard chart JSON and browser date filters are display-only. Hyperliquid testnet prices are not strategy truth.

SV2.0.2 canonical evidence remains the current baseline for historical comparison. PT-RT1.1C local runtime artifacts under ignored `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` are now pre-cutover burn-in context. Fresh Week 2 review should use `reports/paper_runtime/pt_rt1_6_week2_active/` after founder review.

## Completed Current Evidence Tracks

| Track | Status | Meaning |
| --- | --- | --- |
| SV1 | closed | Historical first evidence cycle and ETH `sleeve_1h` UAT observation candidate freeze. |
| SV2.0 | complete | Money Flow v1.2 adds real `sleeve_1d` while preserving 15m/1h/4h settings. |
| SV2.0.1 | complete | Evidence truth hotfix: close slots, open-position accounting, import/staging truth, allocations, missing indicators. |
| SV2.0.2 | complete | Canonical DB-imported Money Flow v1.2 evidence: 36 packs, 9 supported symbols, 4 timeframes, 72 rows. |
| SOR-EV1-SOR-EV3 | complete | Evidence-only loss anatomy, variant replay, overlays, and avoid-sideways drilldown; no variant promoted. |
| MF-ORIG-EV1.1 | complete | Original Money Flow reconstruction accounting/drawdown hotpatch with event-ledger accounting and peak-to-trough drawdown. |
| MF-ORIG-EV2 | complete | Multi-timeframe MF-ORIG evidence and full-equity comparison rows for founder review; no hypothesis approved. |
| EV-AUDIT1 | complete | Full hypothesis/data/methodology audit; no clean production candidate; paper observation ready with conditions. |
| OB2.0 | complete | Obsidian strategy brain and evidence architecture refresh. |
| PT-RT1.6 | founder_selected_week2_three_lane_slate_ready_not_started | Current Paper Trading defaults to the three founder-selected Week 2 lanes, active timeframes are `1h`/`4h`/`1d`, `15m` is paused, startup-valid entries remain blocked until fresh post-start transitions, baseline-only fixed 25 USDC Hyperliquid testnet transport is gated, and candidate/MF-ORIG/wildcard lanes are synthetic-only. PT-RT1.6 does not start the runtime or submit orders. |

## UAT / Runtime Tracks

UAT0 safety/security/runtime audit through UAT4.2 read-only dashboard and paper-equity monitor are complete. PT0 TradingView charts and top-20 Hyperliquid-supported paper/sandbox runtime foundation are complete. PT0.0.2 historical replay and PT0.0.3 1D/data-horizon replay are complete.

Hyperliquid ETH `sleeve_1h` remains the frozen UAT observation context. UAT validates plumbing and behavior, not profitability.

Historical PT0 sandbox/testnet paper-plumbing scope remains audit context. Current PT-RT Paper Trading is synthetic forward observation from public mainnet data; it is not production strategy approval.

Broader top-20 Hyperliquid-supported sandbox/plumbing history remains audit context. Current PT-RT scanner scope and testnet transport policy are defined by the latest PT-RT1.6 docs and gates.

Live trading is not approved. Live exchange order submission is not approved. Strategy paper runtime is not approved by EV-AUDIT1 evidence.

## Current Evidence Verdict

EV-AUDIT1 says:

- evidence is good enough for visual review;
- evidence is good enough for hypothesis filtering;
- evidence is not good enough for production-rule change;
- evidence is not good enough for live or strategy paper-runtime approval;
- paper observation is ready with conditions;
- start the active Week 2 runtime after founder review, then review the next fresh baseline-triggered lifecycle row before making stronger Week 2 forward-observation claims.

## Current Candidate Review

| Item | Status |
| --- | --- |
| Money Flow v1.2 | canonical_baseline, not production-proven |
| `avoid_low_rolling_range_50` | candidate_for_review_only, blocked by drawdown/control-pocket risk |
| MF-ORIG full-equity review lanes | evidence_only, not source-faithful production approval |
| STRAT-EV1 regime_gated_trend | plan_only unless implementation/report exists |
| PT-RT1.6 | founder-selected Week 2 three-lane slate ready but not started; not approved for production/live |

## Read Next

- [[00 Maps/Strategy Family Map]]
- [[00 Maps/Evidence and Backtesting Map]]
- [[00 Maps/Data Source and Market Data Map]]
- [[00 Maps/Dashboard and UI Map]]
- [[00 Maps/Paper Observation Roadmap]]
- [[10 Strategy/Strategy Status Register]]
- [[20 Evidence/EV-AUDIT1 Summary]]
