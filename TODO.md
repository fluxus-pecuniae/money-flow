# TODO

Last reviewed: `2026-06-08T08:45:00Z`

## Active

- GOAL-STRAT1 found zero founder production-testing review candidates after 121 bounded research configurations across 7 families; do not promote any strategy from this goal.
- GOAL-STRAT2 identified two non-existing strategies worth founder paper-testing review: relative-strength rotation with ATR trailing exit, and Donchian breakout with ATR trailing exit. Treat both as research-only until separately scoped.
- PT-RT1.6 prepares the founder-selected Week 2 paper slate: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- STRAT-PRUNE1 remains recommendation-only and was overridden by the founder for Week 2 lane selection.
- STRAT-DISC1 found zero founder production-testing review candidates across 12 bounded research runs and is superseded by the broader GOAL-STRAT1 exhaustion result.
- Start the Week 2 paper run only after founder review; PT-RT1.6 did not start the runtime.
- LOG-OBS1 adds read-only runtime log visibility. Use `.venv/bin/python scripts/watch_pt_rt1_runtime.py --status` to see the active scope, file paths, file sizes, latest modification times, and exact tail commands.
- OBS-OS1 adds the read-only daily review layer. Use `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --status --scope pt_rt1_6_week2_active` during the day and `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate --scope pt_rt1_6_week2_active` to write the ignored dashboard-readable daily pack.
- DASH-PT1.3 contains the Paper Trading terminal layout after QA: filters stay inside the left rail, Watchlist scrolls internally with Symbol / Mid price / Health only, Runtime/Testnet right-rail panels are height-bounded, Daily Review / Anomaly Flags is the final full-width card below the blotter, Runtime details are compact, and chart marker labels are compact. If the browser still looks vertical/stacked, hard refresh because the dashboard CSS/JS cache-buster changed to `dash-pt1-2-terminal-20260608`.
- Review the next fresh Money Flow v1.2 baseline-triggered lifecycle row to confirm it uses Hyperliquid testnet metadata-based `szDecimals` formatting outside the explicit transport-smoke path.
- Continue confirming `1h`/`4h`/`1d` candle-close scheduling, warm-start fresh-signal gating, open-position MTM, and baseline-only fixed 25 USDC Hyperliquid testnet lifecycle separation.
- Keep `15m` paused for Week 2 scoring unless a later founder-approved phase explicitly re-enables it.
- Use the SUBAGENTS1 `runtime_reviewer`, `dashboard_reviewer`, and `quant_reviewer` for the next bounded read-only PT-RT runtime/dashboard/quant triage.

## Next

- If the founder wants another discovery pass, add longer non-overlapping OOS candle windows, execution-quality modeling, and stricter control-pocket slices before widening parameter ranges.
- After founder review, start `reports/paper_runtime/pt_rt1_6_week2_active/` using the documented PT-RT1.6 command or dashboard control server.
- If the founder wants to test GOAL-STRAT2 candidates, use the STRAT-PRUNE1 recommended slate as the implementation target; do not route either candidate to testnet or live trading.
- Treat GOAL-STRAT1 near misses as research triage only: volatility-expansion and Donchian-style variants had positive aggregate pockets but failed OOS and/or drawdown gates.
- Review the first PT-RT1.6 Week 2 runtime rows after the founder-started run begins.
- Keep candidate/MF-ORIG/wildcard lanes synthetic-only; do not route them to testnet.
- Keep SV2.0.2 canonical evidence, SV2.1 1D evidence, Historical Replay display, and PT-RT forward observation separated in future docs.

## Done Recently

- GOAL-STRAT2 selected two non-existing research-only strategies worth paper-testing review from GOAL-STRAT1 evidence and generated per-candidate reports.
- STRAT-PRUNE1 completed read-only lane pruning and recommended a smaller next paper slate without changing runtime behavior.
- PT-RT1.6 implemented the founder-selected three-lane Week 2 active slate and dashboard/control defaults without starting the runtime.
- DASH-PT1.1 removed the visible Audit tab, compacted Paper Trading into cockpit/chart/runtime/watchlist/positions/stream order, fixed configured Week 2 lane/symbol truth before runtime rows exist, and simplified the Strategy tab to the three active Week 2 lanes.
- LOG-OBS1 added a Runtime Logs panel plus a read-only terminal helper so operators can distinguish existing rows visible in VS Code from `tail -F` waiting for newly appended lines.
- OBS-OS1 added the read-only Week 2 daily review/anomaly generator plus a Paper Trading Daily Review / Anomaly Flags panel. The current local status is `observation_may_continue` with one informational `warm_start_block_spike` flag.
- DASH-PT1.2 reorganized Paper Trading into a top health strip, left filter/watchlist rail, center chart, right runtime/testnet/daily-review rail, and bottom tabbed blotter while preserving all Week 2 strategy/testnet/runtime boundaries.
- DASH-PT1.3 fixed Paper Trading terminal layout QA issues by containing left-rail filters/watchlist, bounding Runtime/Testnet right-rail cards, moving the blotter closer to the chart, compacting Runtime details, removing the Watchlist Status column, moving Daily Review / Anomaly Flags below the blotter, and compacting chart marker labels.
- GOAL-STRAT1 added a broader research-only autonomous discovery harness and report; 49 datasets were accepted, 121 candidate configurations were tested, and zero strategies passed the founder-review gate without overfitting/blockers.
- STRAT-DISC1 added the first research-only autonomous discovery harness and report; 50 datasets were accepted, 12 candidate runs were tested, and zero strategies passed the founder-review gate.
- SUBAGENTS1 added project-scoped read-only Codex reviewers for runtime, dashboard, and quant triage.
- PT-RT1.5.3 Hyperliquid testnet size/precision hotfix verified one accepted/open -> canceled -> reconciled fixed-25-USDC smoke using testnet public metadata.
- PT-RT1.5.2 signed testnet transport smoke and active runtime restart handoff.
- PT-RT1.5.1 signed testnet transport, warm-start signal gate, and open-position MTM hotfix.
- PT-RT1.5 active Week 1 reset, candle-close scheduler, and baseline-only fixed 25 USDC testnet lifecycle gates.
- PT-RT1.4.1 active-week runtime cutover verification and daily founder review pack.
- Obsidian current-truth cleanup with Active Work / Finished Work coordination sections.

## Archived Done

Older completed tasks remain below as the detailed historical follow-up log. Treat those rows as audit/history unless they are linked from the current phase.

## Archived Detailed Follow-Up Log

### T-151

- `priority`: `high`
- `status`: `implemented_pending_pt_rt1_5_1_smoke_review`
- `summary`: `PT-RT1.5.1 archives the pre-warm-start PT-RT1.5 smoke rows as pt_rt1_5_smoke_pre_warm_start_gate and defaults the active Paper Trading/control-server scope to reports/paper_runtime/pt_rt1_5_1_smoke/. Startup-valid confirmations are now recorded but blocked from synthetic opens and testnet orders until the entry context resets false and a fresh post-start Money Flow v1.2 baseline open occurs. Signed Hyperliquid testnet transport is wired behind exact PT-RT1.5.1 approval, local env secrets only, testnet URL validation, account-targeting/vaultAddress rules, duplicate order keys, and fixed 25 USDC notional; candidate, MF-ORIG, and wildcard lanes remain synthetic-only. Open synthetic positions now mark to public mainnet mids or latest closed candles and show MTM unavailable when no mark exists. Public mainnet candles remain strategy truth; testnet fills do not update synthetic PnL; no live trading or production approval follows. Next operator step is to run/review pt_rt1_5_1_smoke before the Week 1 observation window.`

### T-150

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1.4.1 active-week runtime cutover verification is complete. The retired pre-PT-RT1.4 runtime continued producing 15m synthetic opens after the cutover and is now labeled pre_pt_rt1_4_weekend_burn_in, excluded from active Week 1 scoring, and preserved only as legacy context. A fresh active-week runtime was started under ignored reports/paper_runtime/pt_rt1_4_1_active_week/; the first artifact cycle reported active timeframes 1h/4h/1d, disabled timeframe 15m, 0 new 15m opens, and 0 15m rows. The daily founder review pack now exists at docs/pt_rt_week1_day_summary.md and docs/pt_rt_week1_day_summary.json with runtime health, lane/timeframe metrics, open/closed trade review, decision/reason-code review, dashboard QA, and testnet transport audit. Week 1 paper observation may continue from the restarted runtime. No production Money Flow rules changed; no new strategies or threshold tuning were added; no evidence packs were regenerated; no paper/live production approval, live/testnet order submission, private/signed/order endpoint call, API-key use for strategy truth, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-149

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1.4 Paper Trading command-center cleanup is implemented. Active Week 1 paper observation now defaults to 1h, 4h, and 1d; 15m is disabled for week-one noise reduction, excluded from active weekly scoring, and preserved only as paused/legacy data. Strategy Lane Comparison is timeframe-scoped by default, all-active mode explicitly means 1h + 4h + 1d and not one combined account, Open Synthetic Positions and Closed Synthetic Trades are cleaned up for founder review, Signal Generator is now a categorized paper-decision stream, and testnet plumbing status separates audit-only shapes from disabled order transport. No production Money Flow rules changed; no evidence packs were regenerated; no paper/live approval, live/testnet order submission, private/signed/order endpoint call, API-key use for strategy truth, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-148

- `priority`: `medium`
- `status`: `done`
- `summary`: `Obsidian current-truth cleanup is complete. Phase Timeline now leads with Paper Trading / PT-RT, SV2.x evidence, SOR/MF-ORIG research, dashboard founder review, and governance; UAT/platform phases are preserved as historical plumbing context rather than the active center. Agent Coordination now has separate Active Work and Finished Work sections. Duplicate command-center and phase-timeline entrypoints remain pointer-only. Current-truth notes use Paper Trading as the founder-facing dashboard language and remove stale manual-report-loading/evidence-loaded top-chrome wording. This is docs/governance only: no code behavior, evidence packs, production Money Flow rules, paper/live approval, endpoint use, API keys, testnet strategy truth, or SOR/fanout/CBBO changed.`

### T-147

- `priority`: `medium`
- `status`: `done`
- `summary`: `PT-RT1.2.1 Paper Observation dashboard layout, marker visibility, visual polish, and runtime-ledger display truth are implemented. The dashboard top chrome now carries the logo, Money Flow Evidence Dashboard title, Load JSON control, theme control, and six primary tabs in one sticky top bar, and the visible SV2.0.2 + SV2.1 evidence-packs-loaded phrase is removed. The visible Expanded Scanner Universe/watchlist was removed, the live public candle chart now sits above Signal Generator, Open Synthetic Positions and Closed Synthetic Trades sit directly below Signal Generator, Strategy Lane Comparison sits directly below the trades section, Signal Generator / Open Synthetic Positions / Closed Synthetic Trades paginate at 10 rows, Wildcard Diagnostics moved to the Strategy tab, and the global Symbol / Timeframe / Strategy lane controls now drive chart context, signal rows, open rows, closed rows, and opened/closed synthetic chart markers. Closed Synthetic Trades now loads ignored PT-RT trades.jsonl rows for entry/exit/price/quantity/PnL fields and filters out sparse paper_closed decision rows that would display as n/a trade rows, and Strategy Lane Comparison overlays paper_runtime_state.realized_equity_by_lane plus open/closed counts so lanes do not remain at starting equity after closed trades. When Symbol or Timeframe is All, the chart uses the newest matching paper signal/open context and otherwise keeps the prior chart target. The page now has a cleaner cockpit hierarchy: compact safety notices, a two-column Local Mac runtime control card, a clearer global filter toolbar, a larger primary chart, and normalized panel spacing/radii. No production Money Flow rules changed; no evidence packs were regenerated; no paper/live approval, signed/private/order endpoint call, API-key use, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-146

- `priority`: `high`
- `status`: `done`
- `summary`: `Paper Observation Signal Generation dashboard visibility is fixed. The tab now loads recent ignored PT-RT decisions.jsonl rows in addition to summary.json, defaults Paper Observation filters to All, and renders durable synthetic paper_opened rows even when the latest runtime summary cycle contains no new opens. The testnet probe panel now separates audit/order-shape rows from signed testnet orders and explicitly labels audit_only as local 20 USDC shape generation without signed Hyperliquid testnet submission. This is UI/runtime-truth visibility only: no production Money Flow rules changed, no paper/live approval, signed/private/order endpoint call, API-key use, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-145

- `priority`: `medium`
- `status`: `done`
- `summary`: `TRUMP is deferred from fresh PT-RT paper-observation scanner runs after founder review because it created excessive runtime noise. New PT-RT requested scanner symbols exclude TRUMP, summaries expose deferred_runtime_symbols.TRUMP=runtime_noise_deferred_by_founder, and docs/Obsidian notes state that prior SV2.1 historical evidence artifacts containing TRUMP remain historical truth. Existing generated evidence packs were not rewritten or regenerated. No production Money Flow rules changed; no paper/live approval, order/private/signed endpoint call, API-key use, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-144

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1.3 candle-truth data-health semantics are implemented. Supported/precision-ready Hyperliquid symbols no longer require a fresh public allMids value to enter the scanner; stale/thin/missing/nonpositive mids are warning-only when clean fully closed public-mainnet candleSnapshot rows are available. Runtime summary/data_health output now exposes data_health_semantics=candle_strategy_truth, mid_health_blocks_strategy=false, candle_health_blocks_strategy=true, mid warning counts, candle blocking counts, indicator blocking counts, and lane-expanded data_unavailable decisions. Dashboard Paper Observation separates blocking candle rows from mid warning rows so quiet Hyperliquid pairs do not look broken solely because public mids are stale. No production Money Flow rules changed; no paper/live approval, private/signed/order endpoint call, API-key use, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-143

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1.2 runtime correctness and 20 USDC testnet transport gates are implemented. The paper-observation runner now persists processed signal keys, open synthetic positions, realized equity by lane, and last processed close state in each ignored output directory's state.json. Repeated same-candle open attempts are converted into held/blocked decisions instead of new paper_opened rows, closed synthetic positions write trades.jsonl rows, and summary.json separates public market-data unavailable rows from lane-expanded data_unavailable decisions. Dashboard Paper Observation now surfaces open positions, duplicate-open blocks, unavailable market rows versus lane decisions, transport mode, submitted/cancel/reconcile counts, and the synthetic public-mainnet paper PnL source. Signed testnet transport remains disabled unless a future operator uses --submit-testnet-probes with exact PT-RT1.2 transport approval and a configured client. No production Money Flow rules changed; no live trading, live endpoint, private/signed/order endpoint call during tests, API-key use, testnet strategy truth, or SOR/fanout/CBBO was added.`

### T-142

- `priority`: `high`
- `status`: `done`
- `summary`: `SV2.1 founder-approved Hyperliquid 1D period evidence regeneration is complete and now has Historical Replay/dashboard artifacts for all 10 PT-RT1 paper-observation lanes. The previous broad active-metadata evidence run was rejected for founder review and removed from local generated outputs. The current public-data run used Hyperliquid public mainnet meta/candleSnapshot only, targeted the founder-approved PT-RT1 requested/resolved list, mapped TRON to TRX, excluded PEPE/kPEPE and OKB by resolver policy, imported available timezone-explicit 1D candles into the intended local money_flow DB, and generated ignored Strategy Validation evidence packs for 2024, 2025, YTD, and ALL where each symbol had available candles. The run wrote 90 generated campaign configs under /tmp/money-flow-sv21-broad-1d/campaign_configs and 90 ignored baseline evidence-pack directories under reports/strategy_validation; period counts were 2024=21, 2025=23, YTD=23, and ALL=23. The follow-up Historical Replay builder wrote 1800 ignored selected chart/trade JSON files under reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data/20260516T091500Z and 810 ignored evidence-only candidate/reference/wildcard pack directories across all 9 non-baseline PT-RT1 lanes. ASTER and TRUMP lack 2024 packs because public candles do not cover that period; no candles were fabricated. Production Money Flow rules remain unchanged; no variant is approved; no orders/private/signed/order endpoints/API keys/testnet strategy truth/live trading/paper approval/SOR behavior were added.`

### T-141

- `priority`: `high`
- `status`: `runtime_artifacts_present_pending_evaluation`
- `summary`: `PT-RT1.1 24-hour probes-disabled dry-run validation was blocked because no full ignored 24-hour runtime artifact directory existed. PT-RT1.1A expanded readiness before the run: exactly 10 independent synthetic 10000 USDC strategy lanes are configured, founder-requested scanner symbols are represented with requested/resolved/block reason truth, TRON maps to TRX, PEPE maps to kPEPE and is blocked by unit semantics by default, OKB is blocked unless active Hyperliquid support is confirmed, POL remains distinct from delisted MATIC, and the Paper Observation dashboard shows lane detail, wildcard diagnostics, blocked symbols, and separate testnet probe status. PT-RT1.1B added the Hyperliquid public-mainnet connector/runtime command and smoke-verified public `meta`/`allMids`, watchlist resolution, bounded candle loading, and bounded paper decisions under ignored `reports/paper_runtime/pt_rt1_1b_smoke/`. PT-RT1.1C now has ignored local artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`; the local set contains about 479k decision rows, 0 trade rows, and latest summary timestamp `2026-05-15T22:22:12Z`. A later local run showed `decisions.jsonl` growth can become operationally large, so the runtime now defaults to `--decision-log-mode compact`: actionable `paper_opened`/`paper_closed` rows and `data_unavailable` rows are still written, repeated identical non-actionable rows are suppressed across cycles, summary.json records suppression/size stats, and `full_audit` remains an explicit mode. Existing large ignored logs are not rewritten by the compact default. PT-RT1 is not always-on or hosted; new signal generation requires starting the runtime and keeping that process and machine awake/networked. The dashboard now has a localhost-only `scripts/run_dashboard_control_server.py` Start Run / Stop Run helper that launches allowlisted 5-minute, 1-hour, 6-hour, or 24-hour public-mainnet runs through Mac `caffeinate`, with 20 USDC Hyperliquid testnet probe audit/order-shape rows enabled for synthetic open signals. These probe rows are not signed transport submissions and never update strategy paper PnL. Static dashboard serving keeps the controls unavailable. Public mainnet refresh stability over the full collection, closed-candle gating over time, paper-ledger updates, duplicate-signal behavior, data-health gating, dashboard runtime readability, compact-log behavior, and the 20 USDC probe audit trail still require PT-RT1.1D evaluation.`

### T-140

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1 real-time public market data paper observation and testnet plumbing probes are implemented as a forward-observation substrate. PT-RT1.1A expands the strategy-truth lane to 10 independent synthetic 10,000 USDC paper ledgers: Money Flow v1.2 baseline, two SOR rolling-range candidate lanes, four MF-ORIG full-equity reference lanes, and three wildcard expert observation hypotheses. The separate Hyperliquid testnet plumbing lane is disabled/kill-switched by default, requires exact approval, enforces cap/notional/account-targeting/precision/post-only gates, and never updates strategy paper PnL. The dashboard now has a Paper Observation view with expanded scanner metadata, lane detail, wildcard diagnostics, blocked-symbol reason codes, a 1-second public-mainnet compact watchlist showing symbol/mid/health, selected-pair public-mainnet TradingView chart, Signal Generation rows for recorded synthetic paper-opened intended entries, and testnet separation. Watchlist health is unhealthy when the latest market-data tick is missing or stale for more than 2 minutes. Production Money Flow rules remain unchanged; no evidence packs were regenerated; no live trading, strategy paper-production approval, live orders, private/signed/order endpoints from strategy truth, API keys, SOR/fanout/CBBO, or testnet strategy truth were added.`

### T-139

- `priority`: `high`
- `status`: `done`
- `summary`: `OB2.0 Obsidian Strategy Brain + Evidence Architecture Refresh is complete. The Obsidian vault now has one canonical command center plus refreshed strategy-family, evidence/backtesting, data-source, dashboard/UI, paper-observation, strategy status, Original Money Flow source, and EV-AUDIT1 summary notes. It documents Money Flow v1.2 as the current derivative/canonical SV2.0.2 baseline, Original Money Flow as a separate source-faithful MF-ORIG track, SOR repair variants as evidence-only, STRAT-EV as plan-only unless implemented, dashboard chart/date-filter data as display-only, UAT sandbox plumbing as separate from evidence, and PT-RT1 as recommended but not approved. The Gerald Peters PDF is stored in money-flow/90 Reference/. No production strategy code, evidence packs, dashboard chart data, exchange endpoints, API keys, paper approval, live approval, or strategy results changed.`

### T-137

- `priority`: `high`
- `status`: `done`
- `summary`: `EV-AUDIT1 full hypothesis, data-integrity, and paper-readiness audit is complete. The audit inventories Money Flow v1.2 canonical SV2.0.2 evidence, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and pending STRAT-EV1 plan-only status; scores methodology/data/candidate confidence; explains biggest winners, biggest losers, losing streaks, regime attribution, and control-pocket damage; and lists P0/P1/P2/P3 issues. No clean strategy candidate is promoted. Current evidence is good enough for visual review and hypothesis filtering only, not for production-rule changes, strategy paper-runtime authorization, or live trading. PT-RT1 real-time public market data plus paper observation is the recommended future phase under separate scope and gates. No evidence packs were regenerated, no production Money Flow rules changed, no orders/private/signed/order endpoints/testnet strategy truth/live trading/SOR behavior were added.`

### T-138

- `priority`: `high`
- `status`: `done`
- `summary`: `PT-RT1 has been implemented as the first real-time public-market paper-observation substrate plus separate testnet plumbing-probe gate. The 60-day observation run itself has not started; use the PT-RT1 dry-run and 60-day runbooks before relying on forward-observation rows.`

### T-135

- `priority`: `high`
- `status`: `done`
- `summary`: `Historical Replay selected-scenario chart/trade loading is fixed. The compact SV2.0.2/MF-ORIG-EV2 rows still seed selectors and comparison widgets immediately, but selected charts/trades now lazy-load deterministic per-scenario JSON files under ignored local reports/strategy_validation/*/selected/ paths instead of relying on giant symbol/timeframe chart bundles. The SV2.0.2 and MF-ORIG-EV2 chart-data builders now write those selected replay files reproducibly. This is UI/artifact-loading only: evidence metrics, production Money Flow v1.2 rules, MF-ORIG hypotheses, orders, private/signed/order endpoints, testnet strategy truth, paper runtime, and live trading approval remain unchanged.`

### T-136

- `priority`: `high`
- `status`: `done`
- `summary`: `MF-ORIG-EV2 full-equity comparison regeneration is complete. The four original source-faithful 1% risk-sizing hypotheses remain present, and four founder-requested full-equity/notional counterparts were added for direct full-equity replay comparison. The regenerated compact summary now contains 8 replay strategies, 576 scenario rows, 288 ignored evidence-pack directories, and 612 ignored dashboard chart-data files including 576 selected per-scenario replay JSON files. This remains evidence-only: production Money Flow v1.2 is unchanged, no hypothesis is approved, no orders/private/signed/order endpoints/testnet strategy truth/live trading/paper runtime/SOR behavior were added.`

### T-134

- `priority`: `high`
- `status`: `done`
- `summary`: `MF-ORIG-EV2 multi-timeframe evidence is complete. The corrected Original Money Flow reconstruction now has evidence-only packs across the four source-faithful 1% risk-sizing hypotheses plus four full-equity/notional comparison counterparts, BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and both next_candle_open and next_candle_close fill assumptions. The run preserved MF-ORIG-EV1.1 event-ledger accounting, single-counted entry fees/trims, force-close open-position handling, and peak-to-trough drawdown; 1d is labeled source-primary, 4h/1h fractal adaptations, and 15m a stress-test adaptation. Local ignored artifacts include 288 evidence-pack directories and 612 dashboard chart-data files; committed docs include docs/mf_orig_ev2_multitimeframe_evidence_packs.md and docs/mf_orig_ev2_multitimeframe_evidence_summary.json. Historical Replay and Evidence Run Ledger now auto-load all eight MF-ORIG-EV2 strategies when local chart-data JSON exists. Production Money Flow v1.2 remains unchanged; no original hypothesis is approved; no orders/private/signed/order endpoints/testnet strategy truth/live trading/paper runtime/SOR behavior were added.`

### T-133

- `priority`: `high`
- `status`: `done`
- `summary`: `MF-ORIG-EV1.1 accounting and drawdown hotpatch is complete. The Strategy Validation-only original Money Flow reconstruction now uses event-ledger accounting with entry_fee, trim_close, final_close, forced_close, and stop_close events; entry fees and trim PnL are counted exactly once; final closes operate only on remaining quantity; trade net PnL equals equity delta within the declared decimal tolerance; drawdown is peak-to-trough for realized and mark-to-market curves; and positive 1d control pockets filter only baseline-positive 1d rows. The MF-ORIG Markdown/JSON reports were regenerated and pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions are quarantined. Candidate gates were re-run and still mark all original hypotheses source_faithful_but_underperformed due baseline-positive 1d control-pocket damage. Production Money Flow rules remain unchanged; no original hypothesis is approved; no orders/private/signed/order endpoints/testnet strategy truth/live trading/paper runtime/SOR behavior were added.`

### T-132

- `priority`: `high`
- `status`: `done`
- `summary`: `MF-ORIG-EV1 original Money Flow reconstruction is complete as evidence-only research. It adds a formal source-specification and gap matrix, a Strategy Validation-only original Money Flow replay module, and generated Markdown/JSON reports comparing source-faithful 1d-first hypotheses against canonical SV2.0.2 Money Flow v1.2 DB-imported evidence. The reconstruction models Stage 1-4, 5 EMA / 20 SMA triggers, MACD-as-TSI substitute confirmation/warnings, RSI profit-warning trims, prior support/pivot stop proxies, and 1% risk-budget sizing. The source PDF is now present under money-flow/90 Reference/ for future source-exact reconciliation; OB2.0 did not regenerate or change MF-ORIG evidence numbers. Production Money Flow rules remain unchanged; no original hypothesis is production-approved; no orders/private/signed/order endpoints/live behavior/testnet strategy truth/SOR behavior were added.`

### T-131

- `priority`: `high`
- `status`: `done`
- `summary`: `Historical Replay now has full research-only replay coverage for the two founder-prioritized SOR-EV3 rolling-range variants. The SV2.0.2 dashboard chart-data generator appends avoid_low_rolling_range_20 and avoid_low_rolling_range_50 replay rows to the ignored local chart JSON for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, with both next_candle_open and next_candle_close fill assumptions. Regeneration wrote 36 chart-data files containing 72 canonical replays, 72 avoid_low_rolling_range_20 replays, and 72 avoid_low_rolling_range_50 replays. These rows are for founder Historical Replay investigation only; production Money Flow rules remain unchanged, no variant is approved, no orders/endpoints were called, no testnet prices are strategy truth, and no live/paper runtime or SOR behavior was added.`

### T-130

- `priority`: `high`
- `status`: `done`
- `summary`: `SOR-EV3 founder-selected avoid_sideways_low_volatility drilldown is complete. Baseline parity passed for all 72 canonical SV2.0.2 scenarios, and the controlled true-forward variant set tested ATR percentile, flat SMA20/EMA10 trend, low rolling range, MACD-flat chop, and a conservative combined sideways/low-volatility blocker. Blocked open signals are separated from matched canonical baseline trades with PnL attribution, avoided losers / missed winners are reported, loss-concentration and control-pocket impact are summarized, and no variant was promoted. Evidence Lab loads docs/sor_ev3_avoid_sideways_low_volatility_summary.json and now shows founder-review labels plus gate blockers instead of flattening every non-candidate into rejected: avoid_low_rolling_range_20 is promising_control_pocket_risk, avoid_low_rolling_range_50 is promising_high_pnl_control_risk, and avoid_low_atr_percentile_30 is rejected_negative_aggregate. No production Money Flow rules changed, no variant was approved, no orders/private/signed/order endpoints were called, no Hyperliquid testnet prices or dashboard date filters were used as canonical strategy truth, and no SOR/fanout/CBBO/cross-venue routing or live/paper runtime was added.`

### T-129

- `priority`: `medium`
- `status`: `done`
- `summary`: `SOR-EV2.2 Evidence Lab variant chart overlay is complete. The dashboard now has overlay controls for symbol, timeframe, fill assumption, variant, baseline/variant/both mode, large-loss trades, stop/context exits, late-extension entries, adverse candles, and MA/SMA break context. It renders baseline SV2.0.2 entry/exit/forced-close markers from chart/trade JSON, linkable SOR-EV2 adverse-candle and stop-context markers where exact timestamps exist, a worst-trade focus mode, selected-trade inspector, control-pocket view, and explicit data_not_available_in_sor_ev_bundle / exact_overlay_unavailable_from_sor_ev_bundle states where the SOR bundles lack exact overlay data. No production Money Flow rules changed, no variant was approved, no orders/private/signed/order endpoints were called, no Hyperliquid testnet prices were used as strategy truth, no live/paper runtime or SOR/fanout/CBBO/cross-venue behavior was added, and no canonical evidence packs were regenerated.`

### T-128

- `priority`: `medium`
- `status`: `done`
- `summary`: `SOR-EV2.1 Evidence Lab UI is complete. The dashboard now exposes a visible Evidence Lab tab that loads the committed SOR-EV1/SOR-EV2 summary bundles, labels canonical SV2.0.2 DB-imported evidence as the baseline, and shows variant matrix, control-pocket impact, worst-trade loss anatomy, late-entry analysis, large adverse-candle context, RSI/MACD rejection visibility, methodology warnings, date-filter noncanonical warnings, and a deferred chart-overlay status. The Variant Summary Matrix now uses founder-review labels to separate promising, mixed, deferred, no-op, diagnostic-only, and hard-rejected rows instead of flattening every non-candidate into rejected. No production Money Flow rules changed, no variant was approved, no orders/private/signed/order endpoints were called, no Hyperliquid testnet prices were used as strategy truth, and no SOR/fanout/CBBO/cross-venue routing behavior was added.`

### T-127

- `priority`: `high`
- `status`: `done`
- `summary`: `SOR-EV2 true-forward stop/exit and rejected-signal replay is complete. Baseline replay parity passed for all 72 canonical SV2.0.2 scenarios. Fixed-stop, ATR-stop, recent-low, large-bear-candle, earlier-MACD, lower-RSI, extension-filter, and chop-avoidance variants were evaluated as evidence-only true-forward replay from persisted candle truth. No variant was promoted: fixed/ATR/large-bear stops did not produce a clean control-preserving improvement, lower-RSI/MACD admissions added many bad trades, and extension/chop filters require narrower follow-up despite some aggregate improvements. No production Money Flow rules, orders, private/signed/order endpoints, paper/live approvals, dashboard date-filter evidence, testnet strategy truth, SOR/fanout/CBBO/target reselection, or route-executor behavior were added.`

### T-126

- `priority`: `high`
- `status`: `done`
- `summary`: `SOR-EV1 loss anatomy and evidence-only variant diagnostics are complete. The new report reads only canonical SV2.0.2 DB-imported evidence packs at 20260512T064916Z, explains the worst losses and late-entry/adverse-move patterns, labels fixed-stop results as completed-trade overlay estimates, defers ATR/recent-low/large-bear/RSI/MACD entry variants that require true replay, reports control-pocket impact, and promotes no production candidates. No production Money Flow rules, orders, private/signed/order endpoints, paper/live approvals, evidence-pack regeneration, dashboard date-filter evidence, testnet strategy truth, SOR/fanout/CBBO/target reselection, or route-executor behavior were added.`

### T-125

- `priority`: `medium`
- `status`: `done`
- `summary`: `SV2.0.2 dashboard display fixes are complete. Historical Replay now loads ignored chart/trade JSON derived from the regenerated canonical evidence packs for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d when the local files are present, so 1h exists for all supported symbols and 4h/1d Jan 2025 history remains visible where public data allows. Evidence controls de-duplicate timeframe buttons, component cards include pair context, arrow descriptions default off, the invalid Experiments tab/panel is removed from the visible dashboard, and the misleading legacy dynamic-equity default-load message is gone. No evidence packs were regenerated for this display fix and no strategy/rule/order behavior changed.`

### T-122

- `priority`: `high`
- `status`: `done`
- `summary`: `SV2.0 Money Flow 1D sleeve and expanded evidence refresh is complete. Money Flow v1.2 now includes sleeve_1d as a real first-class sleeve with initial non-optimized 1D settings while preserving existing 15m/1h/4h settings. Hyperliquid public mainnet metadata resolved BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, and SHIB, with SHIB explicitly mapped to venue symbol kSHIB. Public mainnet candleSnapshot rows were fetched for supported symbols across 15m/1h/4h/1D, Jan 2025 target coverage is reached for 4h and 1D, and 15m/1h carry hyperliquid_public_5000_candle_limit horizon warnings. The dashboard surfaces Money Flow v1.2, sleeve_1d, expanded symbol readiness, and the SV2.0 compact evidence summary while keeping sandbox execution separate. No orders, order controls, private/signed/order endpoints, API keys, testnet strategy truth, live trading, real capital, SOR/fanout/CBBO/target reselection, or parameter optimization were added.`

### T-123

- `priority`: `medium`
- `status`: `done`
- `summary`: `SV2.0.2 completes DB-backed candle import and canonical SV2 evidence-pack generation. Normalized Hyperliquid public mainnet candles were imported through the hardened Strategy Validation candle importer into the intended migrated money_flow DB, 36 per-symbol/per-timeframe canonical campaign configs were generated for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, and existing evidence-pack machinery emitted ignored canonical evidence packs for Money Flow v1.2. The 2026-05-12 regeneration uses fully closed timeframe end-boundaries and each pair/timeframe's full available imported public window. SHIB remains represented as venue symbol kSHIB but deferred from executable canonical evidence because unit semantics are not clean enough. No strategy parameters were changed and testnet data is not strategy truth.`

### T-124

- `priority`: `high`
- `status`: `done`
- `summary`: `SV2.0.2 removes the canonical-evidence blocker for SOR-EV1. Canonical DB-backed evidence pack paths now exist for Money Flow v1.2 with 15m/1h/4h/1d, dynamic_equity_pct, 10000 USDC initial equity per independent scenario, explicit fee/slippage, force-close-at-dataset-end open-position handling, supported expanded symbols, and unsupported/deferred SHIB reason codes. SOR-EV1 may proceed from the regenerated fully closed per-pair baseline, while live trading, real capital, order submission, SOR/fanout/CBBO/target reselection runtime behavior, and stop-loss/RSI/MACD variants still require separately scoped phases.`

### T-118

- `priority`: `high`
- `status`: `done`
- `summary`: `PT0.0.1 TradingView chart stability P0 hotfix is complete. The UAT/PT dashboard now gives the Lightweight Charts mount an explicit bounded height, contains parent chart layout, reuses the existing chart and series handles across 15-second public refreshes, removes the autoSize / ResizeObserver applyOptions feedback-loop risk, limits fitContent to new symbol/timeframe initialization, keeps a single live polling timer guard, and supports disableLivePolling/livePolling query flags for local JSON fallback. No orders were submitted, no order controls were added, no private/signed/order/live endpoint calls were added, no exchange API keys were used, and PT0 paper/sandbox routing policy remains unchanged.`

### T-119

- `priority`: `high`
- `status`: `done`
- `summary`: `PT0.0.2 historical strategy replay cockpit is complete. The dashboard now has a Historical Replay tab backed by historical replay summary JSON generated from the trusted SV1.17 historical full-suite baseline replay export. BTC/ETH/SOL x 15m/1h/4h datasets are audited and replay-ready, historical candles render through TradingView Lightweight Charts, green/red historical entry/exit markers are shown, the trade inspector exposes reasons/indicators/cost/PnL/equity details, the dynamic 10,000 USDC equity path is visible, and BTC/ETH/SOL comparison plus separate sandbox execution plumbing views exist. The replay-strategy selector supports OG replay/strategy, research-only MACD removed, and research-only Only close on 5/20 cross across all symbols/timeframes. Hyperliquid testnet market data is not strategy truth. No orders, order controls, private/signed/order endpoints, API keys, live endpoint use, Money Flow rule changes, strategy optimization, or evidence packs were added.`

### T-120

- `priority`: `high`
- `status`: `done`
- `summary`: `PT0.0.3 historical data horizon and 1D replay support is complete. The dashboard now prefers docs/pt0_0_3_historical_strategy_replay_summary.json, preserves that payload instead of overwriting it with PT0.0.2 fallback data, supports 15m/1h/4h/1D historical replay selection, shows a Jan 2025 target-start data-horizon panel, and reports actual earliest/latest candles plus warning reason codes per BTC/ETH/SOL timeframe. Current committed local data does not reach 2025-01-01T00:00:00Z. 1D candles are deterministically aggregated from 4h historical replay candles and labeled as not a new production Money Flow 1D sleeve. No orders, order controls, private/signed/order endpoints, API keys, live endpoint use, testnet strategy truth, Money Flow rule changes, strategy optimization, or evidence packs were added.`

### T-121

- `priority`: `high`
- `status`: `future`
- `summary`: `PT0.0.4 historical data backfill and replay regeneration is future work. It should import or attach trusted Hyperliquid BTC/ETH/SOL public historical candles back to 2025-01-01T00:00:00Z where available, regenerate 15m/1h/4h/1D replay exports, preserve historical candle strategy truth, and keep no-order/no-live/no-rule-change boundaries. Playback controls and market-structure inspection can be scoped after the data horizon is trustworthy.`

### T-092

- `priority`: `high`
- `status`: `done`
- `summary`: `OB1.0 overhauled the Obsidian project brain for the post-SV1.18.1 state. The vault now has one canonical command center, dedicated Strategy Validation and UAT maps, a UAT candidate freeze note, an explicit UAT0 safety/runtime hardening note, a concise project memory through SV1.18.1, and operational-doc tests that catch stale current-state drift. No UAT0 implementation, Money Flow rule change, routing/execution behavior, paper/live approval, exchange call, API-key use, evidence-pack generation, or live artifact was added.`

### T-090

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT0 safety/security/runtime hardening audit is complete. UAT0.1 closes the P0 API auth/authz baseline for sensitive routes and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and verifies representative bearer/API-key/secret/password/DB URL redaction. UAT0.3 adds fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 completes explicit public-read-only Hyperliquid endpoint verification and no-key public top-volume source / Hyperliquid observation-universe resolution. UAT0 defines the future top-20 supported-asset UAT observation universe and future UAT2 next_candle_open / next_candle_close shadow fill-timing policy while keeping same_candle_close_research_only research-only. No private/signed/order endpoint calls, order submissions, API-key use, paper/live behavior, Money Flow live strategy execution, Money Flow rule changes, routing expansion, or evidence-pack generation were added.`

### T-093

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT1 public read-only connectivity is complete. The UAT1 CLI requires explicit public-read-only network flags, verifies allowed Hyperliquid public info types, fetches public CoinGecko top-volume data without API keys, intersects the source list with Hyperliquid USDC perpetual metadata, records included/excluded observation-only assets, and keeps UAT2 blocked. No private/signed/order endpoints, API keys, order submissions, paper/live behavior, Money Flow live strategy execution, routing changes, Money Flow rule changes, or evidence packs were added.`

### T-097

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT1.1 adds the UAT2 shadow-readiness surface: model/report-only shadow signal audit records, next_candle_open and next_candle_close timing assumptions, same_candle_close_research_only exclusion from primary UAT2 assumptions, no-live-artifact boundary flags, operator-visible shadow drawdown state labeled not-live-account, representative API-error / structured-log redaction verification, and UAT1 universe snapshot loading. UAT2 shadow strategy run may proceed as a future no-order phase. No UAT2 loop, Money Flow live-data evaluation, private/signed endpoint call, API-key use, order submission, StrategyDecision, OrderIntent, SubmittedOrder, paper/live behavior, routing expansion, Money Flow rule change, or evidence pack was added.`

### T-098

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT2 no-order shadow strategy run is complete. The explicit UAT2 runner requires shadow-only and public-read-only flags, loads the UAT1 observation-only universe snapshot, fetches only Hyperliquid public candleSnapshot data, evaluates current baseline Money Flow rules without creating production strategy/execution artifacts, writes shadow audit records, compares next_candle_open and next_candle_close availability, labels same_candle_close_research_only as research-only, and reports shadow_simulated_drawdown / not_live_account_drawdown with no PnL simulation. The generated UAT2 run evaluated 15 observation-only assets across sleeve_15m, sleeve_1h, and sleeve_4h: 45 public candle fetches succeeded, 11 records were would_open, 34 were no_trade, and UAT3 remains blocked. No StrategyDecision, SignalEvent, OrderIntent, PreparedVenueOrder, ExecutionReadinessAssessment, SubmittedOrder, approvals, private/signed/order endpoint calls, API-key usage, paper/live behavior, routing expansion, Money Flow rule change, strategy variant, or evidence pack was added.`

### T-100

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT2.1 dashboard visualization and founder approval readiness pack is complete. The existing static dashboard now loads docs/uat2_shadow_strategy_top20_observation_summary.json in a UAT2 Shadow Run view, shows summary cards, a filterable 45-record signal matrix, would-open inspection, no-trade reason breakdowns, the ETH sleeve_1h evidence-candidate card, next_candle_open / next_candle_close timing status, same_candle_close_research_only research-only truth, not-live-account shadow drawdown, boundary confirmation, and UAT3 blocked readiness. No approval action, sandbox order submission, StrategyDecision, SignalEvent, OrderIntent, PreparedVenueOrder, ExecutionReadinessAssessment, SubmittedOrder, routing artifact, private/signed endpoint call, API-key use, paper/live behavior, Money Flow rule change, or evidence pack was added.`

### T-101

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0 sandbox-order design/readiness is complete. The founder/operator report defines the initial ETH sleeve_1h sandbox subset, approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labels, submit-lease / duplicate-prevention design, approval gate design, risk gate design, UAT3.1 blockers, and dashboard readiness. The dashboard UAT view now has an informational UAT3.0 design panel. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, submitted orders, executable approvals, private/signed endpoints, exchange API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-102

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.1 ran after exact founder/operator approval for one sandbox/testnet order submission attempt. The UAT3.1 runner validates approval text, sandbox/testnet endpoint identity, live-fed sandbox drawdown, approval scope, risk gates, submit-lease duplicate prevention, sandbox artifact labels, and post-only/non-marketable ETH order shape before one transport call. The approved run made exactly one Hyperliquid testnet ETH order attempt under 10 USDC notional; Hyperliquid rejected it with a sanitized user/API-wallet-not-found response, so no cancel was required and reconciliation found no open order. No real OrderIntent, PreparedVenueOrder, SubmittedOrder, executable approval, paper/live behavior, broad top-20 order submission, route expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.`

### T-110

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.3 Hyperliquid account targeting and tick/lot precision hardening is complete. The UAT order path now separates normal master/user accounts from API-wallet signers and explicit subaccount/vault targets: normal mode omits vaultAddress, while subaccount/vault mode includes only the configured explicit subaccount/vault address. A Decimal-based Hyperliquid precision formatter uses meta szDecimals, five-significant-figure price rules, and perp max price decimals; UAT3.3 validates formatting across the UAT observation universe and plans ETH post-only prices/sizes with exchange-valid formatting. The approved runner verified account targeting, signer authorization, live-fed sandbox drawdown, runtime/risk/lease/label gates, and produced sanitized reports, then correctly blocked before /exchange because the configured target subaccount reported live-fed sandbox equity of 0.0. Order attempt count was 0; no order/cancel/amend/retry endpoint was called; no production order artifacts, executable approvals, paper/live behavior, routing expansion, Money Flow rule change, evidence pack, live endpoint, broad top-20 submission, or repeated sandbox order was created.`

### T-111

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.4 production-like sandbox routing operationalization is complete. The fixed-target route is Hyperliquid testnet ETH only, normal user account mode omits vaultAddress, standard perp clearinghouse equity is selected for the active route, unified/portfolio spot-clearinghouse USDC fallback remains implemented/tested, route validation rejects non-ETH/top-20/fanout/SOR/target-reselection/route-executor behavior, and routed sandbox order ledger records expose lifecycle/cancel/reconcile/equity-source/sandbox-label truth. The approved UAT3.4 run made exactly one ETH post-only testnet attempt under the 20 USDC cap; Hyperliquid accepted the order open, the runner canceled it successfully, and reconciliation found no open order. No live endpoint, secret exposure, production order artifacts, paper/live behavior, broad top-20 order submission, smart routing, Money Flow rule change, or evidence pack was added. UAT3.5 remains blocked by incomplete UAT-universe precision validation for testnet-unsupported observation symbols.`

### T-113

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT4.0 live UAT dashboard/chart cockpit is complete. The static dashboard now has a read-only UAT Chart Cockpit tab sourced from committed UAT2 shadow and UAT3.4 routed-order summary JSON, showing the UAT watchlist, market-data coverage, static chart snapshots, EMA5/EMA10/SMA20/RSI/MACD labels, shadow/sandbox lifecycle markers, active fixed-target ETH sandbox route card, unified equity-source visibility, routed-order ledger filters, and shadow-signal overlays. No order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls were added. UAT4.0 does not call private/signed/order endpoints, use exchange API keys, submit orders, create production order artifacts or executable approvals, change Money Flow rules, add routing expansion, or generate evidence packs.`

### T-114

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT4.1 exchange-style dashboard redesign is complete. The static dashboard cockpit has been rebuilt around a trading-workstation layout: compact top bar, persistent safety banner, left market/watchlist rail, central chart cockpit, right order-book / market-info / signal-context / risk-context rail, and bottom blotter tabs for Routed Orders, Shadow Signals, Balances / Positions, Lifecycle, and Audit / Logs. The canonical dashboard design system is now apps/dashboard/DESIGN.md, with root DESIGN.md reduced to a pointer. UAT4.1 remains dashboard redesign only: no order, cancel, retry, amend, approval, paper/live, route, auto-trade, private/signed/order endpoint, exchange API-key, Money Flow rule, routing expansion, or evidence-pack behavior was added.`

### T-115

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT4.2 live market dashboard and paper-equity monitor is complete. Added read-only UAT4.2 monitor helpers, a dashboard summary refresh script, committed UAT4.2 summary JSON, dashboard wiring for public-read-only market rows, deterministic indicators, paper-observation scanner markers, sandbox private-read-only 60-second balance polling policy, internal 10,000 USDC paper-equity ledger, and current-equity sizing policy visibility. UAT4.2 does not add order controls, submit orders, call live endpoints, call private order endpoints, use exchange API keys, create execution artifacts, change Money Flow rules, add routing/SOR/fanout, or generate evidence packs. PT0 approval-gated paper/sandbox trading runtime is captured as future work.`

### T-116

- `priority`: `high`
- `status`: `done`
- `summary`: `PT0 TradingView charting and top-20 paper/sandbox runtime foundation is complete. PAPER TRADING IS APPROVED for Hyperliquid testnet/sandbox only, and BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED under metadata, precision, risk, lease, label, and no-live gates. PT0 adds the official local TradingView Lightweight Charts bundle, deterministic PT0 runtime helpers, committed PT0 summary JSON, top-20 paper universe eligibility, paper scanner records, internal 10,000 USDC paper-equity ledger, realized-equity sizing policy, 60-second sandbox private-read-only balance/position polling policy, and route-candidate risk limits. Runtime sandbox order routing remains default-disabled by PT0_SANDBOX_ORDER_ROUTING_ENABLED=false, and no live trading, real-capital trading, order controls, SOR/fanout/CBBO/target reselection, cross-venue routing, Money Flow rule change, strategy optimization, or evidence pack was added.`

### T-117

- `priority`: `high`
- `status`: `future`
- `summary`: `PT0.1 supervised top-20 paper/sandbox runtime week is future work. It should run the scanner continuously, update TradingView charts in real time, produce eligible risk-gated paper/sandbox route candidates, update internal paper equity and PnL, display positions/PnL and chart arrows, and allow founder monitoring throughout the week while keeping Hyperliquid testnet/sandbox only. PT0.1 must still exclude live trading, real capital, live exchange API keys, SOR/fanout/CBBO/target reselection, cross-venue routing, Money Flow rule changes, strategy optimization, evidence packs, and unbounded automation unless separately approved.`

### T-112

- `priority`: `high`
- `status`: `future`
- `summary`: `UAT3.5 additional sandbox routing lifecycle tests remain blocked until UAT-universe precision validation is complete or the unsupported Hyperliquid testnet observation symbols are explicitly scoped out of routing precision acceptance. The UAT3.4 ETH route succeeded and is ledgered, but XRP, TRX, and UNI were not present in the current Hyperliquid testnet meta response used for pair-universe precision validation. Any future sandbox routing tests still require separate founder/operator approval, ETH-only or explicitly approved symbol scope, sandbox/testnet endpoint verification, live-fed not-live-account drawdown, approval/risk/lease/label gates, no live endpoint, no paper/live trading, no broad top-20 submission, no SOR/fanout/target reselection, and no Money Flow rule change.`

### T-109

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.2 ran after separate founder/operator approval for one second sandbox/testnet order attempt. The UAT3.2 runner validates exact approval text, fixed-key account/API-wallet readiness, sandbox/testnet endpoint identity, live-fed sandbox drawdown, approval scope, risk gates, submit-lease duplicate prevention, sandbox artifact labels, and post-only/nonmarketable ETH order shape before any order-capable transport. The recorded run blocked before /exchange because the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient for the tiny under-10-USDC order. Order attempt count was 0, no order/cancel/amend/retry endpoint was called, and no real OrderIntent, PreparedVenueOrder, SubmittedOrder, executable approval, paper/live behavior, broad top-20 order submission, route expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created. UAT4.0 dashboard chart cockpit was captured as a future roadmap request only.`

### T-103

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete. Added fail-closed SandboxRuntimePolicy, sandbox artifact label validation, actual-submission approval-scope validation, sandbox risk-gate fixture evaluation, sandbox drawdown feed fixture support, and submit-lease / duplicate-prevention fixture checks. Tightened the UAT3.1 actual sandbox approval template and updated the dashboard UAT3 panel to show fixture/readiness status. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoints, exchange API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-104

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.2 sandbox gate integration dry-run and policy hardening is complete. Risk gates now propagate all SandboxRuntimePolicy blockers, non-positive sandbox quantities/notionals/limits/drawdown values are explicitly rejected, and evaluate_uat3_sandbox_submission_preflight combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status into one fixture-only dry-run result. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoints, exchange API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-105

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.3 sandbox artifact label enforcement and executable gate wiring dry-run is complete. Sandbox label boundary validators now cover persistence, API serialization, dashboard display, and report generation helpers; UAT3SandboxDryRunGateService composes runtime policy, boundary labels, approval scope, risk gates, sandbox drawdown status, and submit-lease duplicate-prevention checks into one side-effect-free dry-run result; and runtime policy semantics now distinguish global exchange order submission from sandbox/testnet-only submission. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, prepared orders, submitted orders, executable approvals, private/signed/order endpoints, exchange API keys, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-106

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.4 sandbox private read-only drawdown readiness is complete. Added fail-closed private read-only sandbox account policy, explicit credential approval validation, credential-boundary/redaction helpers, endpoint category separation between private read-only account state and order-capable paths, sandbox account drawdown feed modeling with unavailable-field truth, and UAT3 dry-run preflight drawdown-status support. The required founder/operator approval for sandbox/testnet private read-only credential use was not present, so no API keys were used and no private endpoints were called. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, prepared orders, submitted orders, executable approvals, order/cancel/amend/retry endpoint calls, live API-key use, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-107

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete. The exact UAT3.0.5 private-read-only approval text is present and validated; sandbox/testnet base-URL checks, local credential environment-status inspection without retaining secret values, representative credential redaction, Hyperliquid account-state payload parsing into not-live-account drawdown feeds, and UAT3 preflight live-fed drawdown consumption are implemented and tested. The approved rerun performed one Hyperliquid testnet read-only account-state request, returned HTTP 200, and produced sandbox_drawdown_feed_live_fed_verified. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, prepared orders, submitted orders, executable approvals, order/cancel/amend/retry endpoint calls, live API-key use, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-108

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3.0.6 sandbox submit path dry-run wiring is complete. Added a non-persistent UAT3SandboxSubmissionPlan and UAT3SandboxSubmitDryRunService that compose runtime policy, founder actual-submission approval status, sandbox artifact-label boundary validation, approval scope validation, live-fed sandbox drawdown status, sandbox risk gates, submit-lease duplicate-prevention checks, and adapter endpoint classification. The dry-run classifies the future endpoint as sandbox_order_submission but forbids transport invocation in UAT3.0.6 and reports calls_exchange=false, creates_order_intent=false, creates_prepared_order=false, creates_submitted_order=false, and creates_executable_approval=false. UAT3.1 actual sandbox order submission remains blocked. No orders, real order intents, prepared orders, submitted orders, executable approvals, order/cancel/amend/retry endpoint calls, live API-key use, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs were added.`

### T-099

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT3 approval-gated sandbox order design has been scoped in UAT3.0 as design/readiness only. Actual UAT3.1 sandbox order submission remains blocked by explicit approval, sandbox runtime enablement, sandbox account drawdown feed wiring, UAT-specific risk/kill-switch/audit visibility verification, sandbox artifact labeling, and approval/submit-lease lifecycle verification. UAT3 must not become automatic top-20 order submission and must not use live endpoints, paper trading, routing expansion, Money Flow rule changes, or unapproved order submission.`

### T-094

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT0.1 adds scoped bearer authentication and authorization for sensitive API control-plane routes plus fail-safe runtime-mode lockout settings. Sensitive /api/v1 routes now require at least read_only_operator auth, high-risk admin consume / submit / cancel / amend / retry / account / private-state surfaces require elevated scopes, and the only auth bypass is explicit test runtime. RuntimeSafetyPolicy exposes default-disabled paper trading, live trading, exchange order submission, and private endpoint flags. UAT1 remains blocked by remaining P1 hardening gaps; no exchange calls, order submissions, API-key use, paper/live behavior, routing changes, Money Flow rule changes, or evidence packs were added.`

### T-095

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT0.2 adds adapter-level runtime-policy enforcement before private/signed/order transport, classifies public read-only adapter methods, defines a Hyperliquid future-UAT1 read-only allowlist artifact, and verifies representative redaction for bearer tokens, API keys, secrets, passwords, and DB URLs. UAT1 remains blocked by Hyperliquid public read-only endpoint URL/sandbox verification, broader structured application log/API error redaction verification, runtime drawdown monitoring, and top-20 symbol/market identity resolution. No exchange calls, public/private/signed/order endpoint calls, API-key use, order submissions, paper/live behavior, routing changes, Money Flow rule changes, or evidence packs were added.`

### T-096

- `priority`: `high`
- `status`: `done`
- `summary`: `UAT0.3 adds fixture-tested top-20 UAT observation-universe policy/resolver logic, Hyperliquid public read-only info-type allowlisting for meta, metaAndAssetCtxs, allMids, l2Book, candleSnapshot, and fundingHistory, and a fixture-tested runtime drawdown monitor policy/model. UAT1 public read-only connectivity may proceed under strict constraints. No exchange calls, real top-20 fetches, public/private/signed/order endpoint calls, API-key use, order submissions, paper/live behavior, routing changes, Money Flow rule changes, or evidence packs were added.`

### T-091

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.18 closes the current Strategy Validation evidence cycle and freezes exactly one UAT observation candidate: Hyperliquid ETH USDC perpetual sleeve_1h using current baseline Money Flow rules. The closeout excludes 15m, 4h, BTC/SOL 1h, lower-RSI variants, market-structure variants, and cross-venue candidates from current UAT scope. UAT is defined as plumbing and behavior validation only, not performance validation, paper trading, live trading, or proof of edge.`

### T-087

- `priority`: `high`
- `status`: `future`
- `summary`: `After the SV1.17 full-suite expansion, broader true replay work still remains for multiple fill/cost assumptions, out-of-sample windows, exact recent-low/ATR exit replay with real stop timing/fill modeling, portfolio-level simulation, and later resistance/regime/extension entry filters as true chronological replays. Future experiments should rely on production_rule_*_in_replay_state fields, variant divergence metadata, and separated production-rule rejection / variant-admitted-from-rejection / variant no-trade counters. These remain research-only until separately scoped; no production Money Flow rules, paper/live trading, routing, or execution behavior are authorized.`

### T-089

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.17 now runs true replay experiment round one for the full Hyperliquid BTC/ETH/SOL x 15m/1h/4h public campaign suite using dynamic_equity_pct. Tested lower_rsi_floor_trend_intact_v1, lower_rsi_floor_trend_intact_v2_narrow, lower_rsi_support_confirmed_v1, and lower_rsi_ema10_hold_no_resistance_v1 against each same-symbol/same-component baseline. Some variants improve losing baselines, but ETH sleeve_1h baseline remains the strongest above-starting-equity pocket. Production Money Flow rules, paper/live trading, routing, execution behavior, and exchange calls remain unchanged/deferred.`

### T-088

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.16.1 hardens replay methodology truth. Replay contexts now expose production_rule_*_in_replay_state fields so variant runs do not imply independent baseline-path truth after divergence; variant_state_has_diverged_from_baseline and replay_state_source make divergence visible; and variant-admitted candles are counted under variant_admitted_from_rejection_reason_counts rather than ambiguous variant no-trade. Baseline replay parity and numbers remain unchanged, lower-RSI replay remains research-only, and production Money Flow rules, paper/live trading, routing, execution behavior, and exchange calls remain unchanged/deferred.`

### T-085

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.16 adds the per-candle rejected-signal replay instrumentation that SV1.15/SV1.15.1 required before true lower-RSI or entry-filter variant testing. The new research-only replay substrate captures baseline decision/rejection context, RSI zones, EMA/MACD state, price extension, market regime, and recent swing high/low diagnostics for every evaluated candle; the true replay runner preserves position occupancy and dynamic_equity_pct sizing; and the narrow lower_rsi_floor_trend_intact_v1 example proves lower-RSI admission can be tested without changing production Money Flow rules. The sampled ETH sleeve_1h lower-RSI replay underperformed baseline, so broader variant testing remains future research.`

### T-086

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.15.1 hardens hypothesis-experiment methodology truth. Every SV1.15 variant now carries a methodology classification, completed-trade overlays are labeled as diagnostic estimates rather than true forward replays, recent-low invalidation is downgraded to a lookahead diagnostic upper bound that requires exact exit replay before candidate consideration, and lower-RSI admission remains deferred until rejected-signal replay instrumentation exists. No production Money Flow rules changed, no hypothesis is authorized, and paper/live/routing/execution behavior remains deferred.`

### T-084

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.15 adds a controlled Strategy Validation-only experiment layer over the Hyperliquid public dynamic-equity evidence. It compares one-change-at-a-time overlays for resistance proximity, higher-low/support context, recent-low invalidation proxy, 15m sideways-regime avoidance, and 4h extension limits against the current Money Flow baseline, adds lower-half RSI and pullback/continuation attribution, and produces a founder-readable experiment report. Production Money Flow rules did not change, no hypothesis is authorized, lower-RSI entry admission is explicitly deferred until rejected-signal replay instrumentation exists, and paper/live/routing/execution behavior remains deferred.`

### T-083

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.14 adds Money Flow trade-anatomy and market-structure diagnostics over existing Hyperliquid public dynamic-equity evidence. The founder report explains current readiness/entry/exit logic, confirms entries below the RSI sleeve floor are not allowed, shows ETH sleeve_1h anatomy, 15m and 4h weak anatomy, descriptive recent swing high/low context, and later-test hypotheses. Market structure remains diagnostic only, no filters or Money Flow rules changed, and paper/live/routing/execution behavior remains deferred.`

### T-082

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.13.2 adds dynamic_equity_pct capital sizing as a Strategy Validation simulation mode while keeping constant_initial_capital_notional_per_trade as the default. Dynamic mode sizes each new trade from current realized equity after prior closed-trade net PnL, reports starting/ending equity, net account PnL, realized-equity min/max, equity drawdown, and insufficient-equity skips, and records a Hyperliquid-only founder report. ETH sleeve_1h remained above starting equity across tested dynamic fill/cost assumptions; 15m and 4h dynamic scenarios ended below starting equity in this public campaign. Paper-trading design, portfolio-level allocation, margin/funding/liquidation modeling, Money Flow rule changes, routing/execution behavior, and live artifacts remain deferred.`

### T-081

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.13.1 capital-assumption interpretation hotfix labels current Strategy Validation sizing as constant initial-capital notional per trade. Generated Markdown and founder docs now state that each trade sizes from initial_capital * position_notional_pct, realized equity affects PnL/drawdown metrics only, and dynamic account-equity sizing remains deferred to a later explicitly scoped evidence phase. No evidence packs were regenerated, no imports ran, no Money Flow rules changed, and no paper/live/routing behavior was added.`

### T-080

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.13.1 added a founder-readable Hyperliquid evidence interpretation pack. It clarifies that grouped aggregate totals are sums across research runs, not one account/scenario PnL; shows scenario-level component/symbol/fill/cost/drawdown truth; makes ETH sleeve_1h concentration explicit; and keeps paper-trading design deferred for manual founder review. No new evidence packs, imports, Money Flow rule changes, routing/execution behavior, paper/live artifacts, private/signed/order endpoint calls, or cross-venue evidence merging were added.`

### T-079

- `priority`: `high`
- `status`: `done`
- `summary`: `Added a static local SV1.13 evidence dashboard under apps/dashboard so the founder can review the Hyperliquid evidence packs in human-readable panels, charts, filters, and ledgers. The dashboard uses the supplied design tokens/files, loads ignored local reports/strategy_validation* JSON when served from the repo root, supports manual JSON file loading, and remains visualization-only: it does not generate evidence packs, import candles, call exchange endpoints, approve paper/live trading, or change Money Flow rules. Manual founder review of the evidence remains the next Strategy Validation step.`

### T-078

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.13 generated the first Hyperliquid public campaign evidence packs from the operator-approved/imported 9-file YTD/recent candle campaign. Evidence review reconfirmed the intended migrated money_flow DB, operator-verified non-trading BTC/ETH/SOL Hyperliquid identity, and 25848 imported candles; generated component-scoped evidence packs for sleeve_15m, sleeve_1h, and sleeve_4h; and recorded status ready_for_founder_review. This is research evidence only, not proof of profitability, not strategy recommendation, and not paper/live approval. Founder manual review is the next step before any paper-trading design phase is scoped. Aster/Binance remain later comparative candidates after separate identity verification/import; OKX/Coinbase/Kraken remain blocked by trade-count/source/history gaps.`

### T-033

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.0 implemented the first controlled automation substrate without executing automation. It adds explicit routing automation modes (`disabled`, `dry_run_only`, `approval_required`, `explicit_automation_permitted`), a disabled-by-default policy inspection surface, and dry-run automation plans by desired trade that classify existing same-target recommendation-backed workflow steps as already satisfied, disabled, dry-run-only, approval-required, automation-eligible, manual-only, deferred, or blocked. Plans preserve desired-trade, route-readiness audit, recommendation, target-choice, child-intent, readiness, submitted-order, selected target, and no-fanout/no-CBBO/no-ranking/no-scoring/no-target-reselection/no-route-executor/no-auto-submit truth. Phase 7.0 creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-034

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1 implemented durable operator approval records and reversible action gating below action-taking automation. Approval records authorize exactly one same-target action stage, preserve policy snapshots plus desired-trade/recommendation/target-choice/child-intent/readiness/submitted-order lineage where present, and expose active/revoked/consumed/expired state through service/API inspection. Revocation is explicit while unused, consumption marks only that a future action hook used the gate, and approval creation/inspection/revocation/consumption does not accept recommendations, convert target choices, create readiness, submit orders, call exchanges, create a route executor, fan out, rank/score, use CBBO, reselect targets, or auto-submit.`

### T-035

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1.1 hardened approval truth before action-taking automation. Approval creation and inspection now expire old active records before reuse, mark approvals whose stored lineage no longer matches the current action-stage lineage as stale_lineage, expose lineage_fingerprint / approval_scope_key on approval records, and use a narrow partial unique active-scope index so repeated or concurrent creation cannot produce multiple active approvals for one desired trade / action / current lineage scope. Approval remains separate from execution and still creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-036

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.1.2 finished the approval-truth substrate before action hooks exist. Approval creation now rejects dry-run-only, manual-only, disabled, deferred, blocked, and already-satisfied current steps; only approval-required and explicitly automation-eligible steps can create active approvals. Gate-state inspection keeps current policy truth authoritative, so existing approval metadata cannot make a manual-only or dry-run-only step appear approved. Approval remains separate from execution and still creates no target choice, child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-037

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.2 implemented the first approval-consuming action hook and kept it limited to recommendation acceptance. One active, non-expired, current-lineage `recommendation_acceptance` approval can now accept the exact approved recommendation into a created or reused target choice through the existing Phase 6.2 acceptance path, then mark the approval consumed with actor, target choice id, and no-downstream-artifact provenance. Expired, revoked, stale-lineage, wrong-action, wrong-recommendation, consumed-for-different-recommendation, dry-run-only, and manual-only cases block before target-choice creation. Phase 7.2 creates no child intent, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-038

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.2.1 hardened approval-gated recommendation acceptance coherence. The action now validates approval, creates or reuses the target choice, updates recommendation/audit target-choice truth, consumes the approval, and records approval provenance in one session/commit. A forced failure between target-choice flush and approval consumption rolls back without leaving a target choice or misleading active approval side effect. Repeated calls with the same consumed approval remain idempotent and preserve consumed_at. Generic approval consumption remains administrative only and executes no recommendation acceptance, conversion, readiness, submitted-order handoff, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-039

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.3 implemented the second narrow approval-consuming action hook and integrated the Obsidian strategic brain. One active, non-expired, current-lineage `target_choice_conversion` approval can now convert the exact approved `RoutingTargetChoice` into a created or reused child `OrderIntent` through existing conversion validation/persistence helpers, then consume the approval with actor, child-intent id, routed order-shape policy, and no-downstream-artifact provenance in one coherent session/commit. Invalid, expired, revoked, stale-lineage, wrong-action, wrong-target-choice, dry-run-only, and manual-only cases block before child-intent creation. Phase 7.3 also moved full strategic memory into `money-flow/Project_Memory/money_flow_project_memory.md`, made Obsidian command/current-phase/decision/coordination notes part of the required agent workflow, and left repo-root `money_flow_project_memory.md` as a pointer only. It creates no prepared order, readiness assessment, submitted order, exchange call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-040

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.3.1 hardened focused target-choice conversion tests before Phase 7.4. Direct tests now cover approval-gated conversion rejection for disabled, blocked, deferred, and already-satisfied current step states plus wrong recommendation id, wrong route-readiness audit id, and wrong desired-trade lineage. Each negative case asserts no new child intent, no readiness assessment, no submitted order, and truthful unconsumed or stale-lineage approval state. No product behavior, migration, config, preview/readiness automation, submission automation, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit was added.`

### T-041

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.4 implemented the third narrow approval-consuming action hook and kept it limited to prepared-order preview plus execution-readiness inspection. One active, non-expired, current-lineage `prepared_order_preview_and_readiness` approval can now run the existing child-intent preview/readiness path for the exact routed child `OrderIntent`, persist or reuse the readiness assessment, and then consume the approval with actor, intent id, preview key, readiness id/outcome/reason codes, and explicit no-submitted-order/no-exchange-submit/no-auto-submit provenance. Expired, revoked, consumed-for-different-child, wrong-action, wrong-child-intent, stale-lineage, disabled, blocked, deferred, already-satisfied, dry-run-only, and manual-only cases block before preview/readiness execution. Phase 7.4 creates no `SubmittedOrder`, calls no adapter submit path, and adds no route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-042

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.5 implemented the fourth narrow approval-consuming action hook: submitted-order handoff for one already-ready routed child intent only. One active, non-expired, current-lineage `submitted_order_handoff` approval can now call the existing explicit child-intent submit path, and only when current readiness, live-submit and routed-submit gates, adapter/account authorization, routed lineage/order-shape truth, and submit lease/uncertainty guards pass. Approval is consumed only after `SubmittedOrder` persistence or safe reuse; blocked readiness/gates and submit uncertainty remain reason-coded and authoritative. Phase 7.5 adds no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, new exchange behavior, or broad auto-submit.`

### T-043

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.5.1 hardened approval-gated submitted-order handoff truth. If the existing explicit submit path persists or safely reuses a `SubmittedOrder` but approval consumption fails afterward, the approval is moved to `consumption_pending` with submitted-order id, child-intent id, failure provenance, and manual approval reconciliation reason codes. Repeating the same approval-gated submit call reuses the existing submitted order and attempts to complete approval consumption without another adapter submit. Existing adapter-in-flight / adapter-returned persistence uncertainty and submit lease behavior remain intact. No new action hook, route executor, broad auto-submit, fanout, ranking/scoring, CBBO, target reselection, cross-binding/cross-venue recovery, or new exchange behavior was added.`

### T-044

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 7.6 closed out the controlled automation chain with safety-diligence regression coverage and docs alignment rather than a new action hook. The closeout test walks the full approval-gated chain from existing recommendation through recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff; proves each step consumes only the correct current-lineage approval; proves dry-run, approval creation, administrative consumption, action hooks, and submitted-order handoff remain distinct; proves `consumption_pending` is bounded and repeat calls reuse the existing submitted order without another adapter submit; and asserts no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit. No production behavior, migration, config, or new action stage was added.`

### T-045

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0 implemented the first operator-grade observability/manual-resolution inspection layer without adding trading behavior. The new read-only operator summary by desired trade aggregates existing routed workflow artifacts, approval states, approval gate truth, manual-resolution requirements, submitted-order handoff safety facts, submit-lease/concurrency state, blocking/uncertainty reason codes, no-SOR boundary flags, and next safe operator action. It surfaces `consumption_pending`, stale-lineage/expired approvals, blocked recommendations/readiness, `adapter_submit_may_have_started`, and `adapter_submit_persistence_unknown` without creating artifacts, consuming approvals, resolving manual states, calling exchange adapters, submitting/canceling/amending/retrying, ranking/scoring, using CBBO, fanning out, reselecting targets, or adding route executor behavior.`

### T-046

- `priority`: `high`
- `status`: `future`
- `summary`: `Define Phase 8.1 through architecture review before adding manual-resolution mutation. Candidate work should add explicit, actor-stamped, reason-coded manual-resolution markers or administrative reconciliation workflows for `consumption_pending` and submit-lease uncertainty, while keeping operator acknowledgement separate from exchange/account truth. SV1.0 begins Strategy Validation before Phase 8.1; Phase 8.1 remains deferred until that work is explicitly scoped. Smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor behavior, cross-binding/cross-venue recovery, new action stages, and broad auto-submit remain deferred until explicitly designed and accepted.`

### T-047

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0.1 resolved the dirty Obsidian memory / working-tree baseline left after Phase 8.0. The earlier Obsidian refresh for accepted Phase 7.6 and proposed Phase 8.0 was accepted as intentional strategic-memory work, then updated to describe Phase 8.0 as implemented and Phase 8.0.1 as workflow hygiene only. The repo-root `money_flow_project_memory.md` remains a pointer only, the full project memory remains in `money-flow/Project_Memory/money_flow_project_memory.md`, and no product behavior, routing/execution logic, API behavior, schema, migration, smart routing, route executor behavior, auto-submit, or manual-resolution mutation was added.`

### T-048

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 8.0.2 fixed operator-summary truth for active unexpired child-intent submit leases. The read-only operator routed workflow summary now treats an active lease as `submission_in_progress`, blocks repeat-submit safety with `blocked_while_submission_in_progress`, and reports the next safe operator action as `submission_in_progress` / `safe_to_automate=false`. Terminal adapter uncertainty remains manual-reconciliation-required, expired pre-adapter active leases remain stale-replaceable, and no trading behavior, new action stage, manual-resolution mutation, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, cross-venue retry, or auto-submit was added. SV1.0 now begins Strategy Validation as a separate research track; Phase 8.1 remains deferred until explicitly scoped.`

### T-049

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.0 adds the first Money Flow strategy-validation/backtesting framework. The new service reads persisted candles, computes indicators in memory, reuses current Money Flow strategy rules, simulates research-only trades with explicit capital/fee/slippage/sizing assumptions, and reports deterministic aggregate/component metrics plus no-trade and invalid reason counts. A CLI can emit JSON or Markdown reports. Validation artifacts remain separate from live execution: SV1.0 creates no desired trades, child intents, prepared orders, readiness assessments, submitted orders, routing artifacts, approval state changes, or exchange adapter calls, and it does not optimize strategy rules.`

### T-051

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.0.1 hardens Money Flow validation report truth without changing strategy rules. Fill timing is now explicit and selectable as `same_candle_close_research_only`, `next_candle_open`, or `next_candle_close`; same-candle close is labeled research-only and potentially optimistic. Reports separate closed-trade drawdown from mark-to-market drawdown, add deterministic component comparison/reporting fields, expand Markdown with context, assumptions, aggregate metrics, component metrics, trade summary, reason counts, and limitations, and preserve validation as research-only output with no live desired trades, child intents, readiness, submitted orders, routing artifacts, approval changes, exchange calls, or strategy optimization.`

### T-050

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.1 adds comparative Money Flow validation batch reports. The batch runner executes explicit matrices of components/timeframes, fill-timing assumptions, symbols, date windows, fees, and slippage assumptions, then reports deterministic per-run metrics, assumptions matrix, fill-timing comparison, component comparison, optional symbol/date-window comparisons, observed top/bottom runs, warnings, and limitations. This is descriptive research only: it does not optimize Money Flow parameters, recommend a strategy variant, add paper/live trading, create live trading artifacts, call exchanges, route, or connect validation to execution automation.`

### T-052

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.2 adds data-coverage and market-regime analysis to Money Flow validation. Single-run and batch reports now include requested-versus-available candle coverage, expected/actual/missing candle counts where timeframe spacing is derivable, warning reason codes for thin/missing/gapped data, deterministic trend and volatility regime labels, regime-grouped performance summaries, and repeated CLI `--window start,end` support for multi-window comparison. Regimes are descriptive only and assigned by entry signal candle for trade metrics; they do not change Money Flow rules, optimize parameters, recommend variants, add paper/live trading, create live artifacts, call exchanges, route, or execute.`

### T-054

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.2.1 hardens Money Flow strategy-validation research truth before SV1.3 campaign/evidence-pack work. Validation windows now consistently use candle closes in `(start_at, end_at]` across strategy evaluation, data coverage, regime summaries, forced-close lookup, batch windows, CLI wording, JSON, and Markdown. Coverage expected counts now use expected close slots, unaligned window boundaries are warning-coded, coverage percent cannot exceed 100%, and grouped batch comparisons include blocked-run counts and reason counts while computing performance metrics only from completed runs. No Money Flow rules, optimization, strategy recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, route executor behavior, fanout, or auto-submit were added.`

### T-053

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.5 adds historical-data readiness and first canonical evidence-pack support after SV1.4.1. Campaign `window_convention` metadata is validated against the authoritative `(start_at, end_at]` candle-close convention, canonical campaign audits can emit founder-readable Markdown summaries of covered/thin/missing/blocked rows and missing-data remediation notes, and the new offline public CSV/JSON candle import CLI duplicate-safely upserts existing `candles` rows for research backfills. Collision-safe evidence-pack generation remains intact. SV1.5 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchange private/order endpoints or adapters, and does not connect validation to routing or execution automation.`

### T-055

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.3 adds repeatable Money Flow research campaigns and saved evidence packs. A JSON campaign config names explicit symbols/instruments, components, fill timings, named `(start_at, end_at]` windows, fee/slippage assumptions, capital, sizing, output directory, and report formats. The campaign runner expands that matrix through the existing Strategy Validation batch service, writes normalized config, manifest, JSON report, Markdown report, and README files under `reports/strategy_validation/<campaign_name>/<run_timestamp>/`, preserves blocked-run visibility, and fixes the remaining single-run CLI wording mismatch so `--start` is no longer described as inclusive. SV1.3 changes no Money Flow rules, performs no optimization, recommends no variant, creates no live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-056

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.4 adds Money Flow evidence-pack review discipline and data-readiness baseline. Canonical editable campaign configs now live under `configs/strategy_validation/campaigns/`, the research campaign CLI supports `--audit-only` persisted-candle coverage/readiness inspection, evidence-pack manifests/Markdown include a founder/operator review checklist plus manual paper-trading readiness criteria, and operational-doc tests now assert the current phase line instead of stale historical text. SV1.4 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-057

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.4.1 hardens Money Flow evidence-pack integrity before SV1.5. Campaign evidence-pack writes now use an explicit collision policy: default `unique_suffix` creates a suffixed run directory when the same campaign/timestamp already exists, while `fail_if_exists` raises an explicit collision error. Pack files refuse overwrite, and manifests record requested run id, final run id, final evidence-pack path, collision policy, collision occurrence, and suffix truth. SV1.4.1 changes no Money Flow rules, performs no optimization, recommends no variant, creates no paper/live artifacts, calls no exchanges, and does not connect validation to routing or execution automation.`

### T-058

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.6 adds the first canonical Money Flow evidence-review layer. The review service and CLI audit the canonical BTC and multi-symbol campaign configs, report insufficient/missing/thin data directly, optionally generate collision-safe evidence packs only when the existing data-readiness audit is clean, and emit JSON/Markdown summaries with generated pack paths, data gaps, fill-timing/component/regime/drawdown/cost observations, no-trade/invalid reason counts, and manual paper-readiness review status. This is descriptive founder/operator research review only: no Money Flow rules were changed, no optimization or strategy recommendation was added, no paper/live artifacts are created, no exchange calls are made, and validation remains separate from routing/execution automation.`

### T-059

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.5.1 hardens the historical candle import and campaign-config research-truth boundary before SV1.6 evidence review. Campaign `window_convention` metadata now uses strict approved text and rejects contradictory inclusive-start phrasing. Offline public candle imports now block existing-candle identity conflicts instead of silently retargeting symbol/instrument ids, enforce row duration matching the selected timeframe, reject non-finite/zero/negative/inconsistent OHLCV values and negative trade counts, and roll back invalid files without partial inserts or updates. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or evidence-review behavior.`

### T-060

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.13 fulfills the first Hyperliquid public evidence follow-up after SV1.12.5/SV1.12.5.1 import closeout. Founder/operator approval had seeded BTC/ETH/SOL Hyperliquid perpetual USDC identity as research-only, non-trading, and non-strategy-eligible with `verified_by=Tercirafael`; all 9 timezone-explicit public YTD/recent files were imported into the intended migrated local `money_flow` DB; and SV1.13 generated three component-scoped evidence packs from those 25848 candles. January 2026 remains archival/vendor-data-required, especially for `15m`, and should stay separate from the public Hyperliquid evidence baseline. Aster/Binance remain later comparative candidates after separate venue identity verification/seed/import; OKX/Coinbase remain blocked by trade-count/source policy; Kraken remains blocked by incomplete public REST history. Do not optimize Money Flow rules, recommend a variant, add paper/live trading, create live artifacts, call private/signed/order endpoints, or connect validation outputs to routing/execution automation until manual evidence review explicitly justifies a new phase.`

### T-067

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.12.5 added the campaign-aware public import bridge in `scripts/run_strategy_validation_public_campaign_import.py` and `services/strategy_validation/public_campaign_import.py`. The wrapper uses `money_flow_hyperliquid_public_ytd_recent.json`, maps the 9 public YTD/recent files, separates file coverage truth from identity readiness, seeds only explicitly operator-verified non-trading research identity, runs requirement-aware preflight, and delegates only preflight-passed files to guarded import. The local approved Hyperliquid run inserted `25848` candles and generated no evidence packs. Aster/Binance files cover 18 additional candidate requirements but still lack verified DB identity; OKX/Coinbase are blocked by missing public trade counts; Kraken is blocked by incomplete public REST OHLC coverage. January `15m` remains an archival/vendor/operator-data gap, not a public Hyperliquid first-evidence blocker. No Money Flow rule change, optimization, recommendation, paper/live trading, routing, or private/signed/order endpoint call occurred.`

### T-061

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.7 added first-real canonical Money Flow evidence-review/data-gap reporting. The review service and CLI now inspect sanitized DB URL/source, reachability, candle-table existence, persisted candle count when available, and blocking DB/schema errors before canonical campaign audits. Unreachable databases or databases missing `candles` produce explicit blocked data-readiness rows instead of uncaught failures or misleading evidence packs. Mixed generated/blocked outcomes use `partial_evidence_ready_with_data_gaps`. The local SV1.7 run audited `money_flow_core_btc.json` and `money_flow_core_multi_symbol.json`, found no usable persisted candle table, generated no evidence packs, and recorded the gap in `docs/strategy_validation_sv1_7_first_evidence_review.md` without changing Money Flow rules, optimizing, recommending a variant, adding paper/live trading, creating live artifacts, calling exchanges, routing, or connecting validation outputs to execution automation.`

### T-062

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.8 added historical data bootstrap and first-real evidence-pack generation truth. Evidence-review DB status now reports sanitized DB target, reachability, Alembic version-table existence, applied revisions, repo migration heads, migration-current status when derivable, schema status/reason codes, migration and DB override hints, `candles` table existence, and persisted candle count. The evidence-review CLI now supports `--db-status-only` for read-only DB/schema/candle readiness inspection. The local SV1.8 run found the default `postgres` host unresolved and the explicit `127.0.0.1:54322/postgres` target reachable but unmigrated with no `alembic_version` table and no `candles` table, so canonical BTC and multi-symbol campaigns remain `insufficient_data` and no evidence packs were generated. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, or exchange calls.`

### T-063

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.8.1 hardened evidence-review schema truth before first real evidence packs. Evidence-pack generation now requires `migrated_schema_ready`, current Alembic migration truth, and required strategy-validation tables (`candles`, `instruments`, and `symbols`); a DB with only `candles` is blocked if Alembic truth is missing, migrations are outdated/unknown, or symbol/instrument schema is partial. Top-level no-live/no-exchange flags now aggregate from campaign results. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or first-real evidence-pack generation.`

### T-064

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.9 made first-real canonical evidence status more operationally precise. Evidence-review DB status now reports sanitized driver, host, port, database name, username, intended strategy-validation DB truth, and target-role warnings; maintenance database names such as `postgres` are flagged as ambiguous instead of silently treated as the Money Flow strategy-validation DB. Evidence-review summaries now emit canonical candle import requirements for blocked/missing readiness rows, including symbol, timeframe, window, expected/actual/missing counts, file format expectations, and example offline importer commands. The SV1.9 local probes found the default intended `money_flow` DB host unresolved and the explicit `127.0.0.1:54322/postgres` override unreachable in this shell, so no first real canonical evidence packs were generated. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or import integrity behavior.`

### T-065

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.9.1 hardened evidence-target truth, candle-import timestamp/provenance truth, and Obsidian memory governance before SV1.10 attempts first real evidence packs. Evidence-pack generation now blocks ambiguous/non-intended maintenance DB targets such as `postgres`, `template0`, and `template1` by default even if schema/candles are otherwise present. No DB-target override was added. Offline candle imports now reject timezone-naive timestamps by default, and the non-default `--assume-naive-utc` override records `timestamp_assumption=assume_naive_utc`, source label, file path/name/hash, row counts, imported environment/venue/timeframe, override truth, and warning reason codes in the import summary. Obsidian command/current/dashboard/timeline/roadmap/project-memory notes were refreshed through SV1.9, operational docs tests now catch stale current-truth drift, and generated research/import outputs remain ignored by Git/review bundles. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, exchange calls, or first-real evidence-pack generation.`

### T-066

- `priority`: `high`
- `status`: `done`
- `summary`: `SV1.10 made the intended local strategy-validation DB target real enough for canonical candle import. The local Homebrew Postgres target `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow` was created, migrated to Alembic head `20260430_0025`, and verified to contain the required `candles`, `instruments`, and `symbols` tables. Canonical evidence review ran with evidence generation enabled but generated no packs because persisted candle count is zero. Evidence-review import requirements are now grouped into 18 unique actionable rows with expected/actual/missing counts, impacted campaigns, required fields, timezone-explicit timestamp requirement, and example importer commands. This changes no Money Flow rules, optimization, recommendations, paper/live trading, live artifacts, routing, execution automation, or exchange calls.`

### T-001

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.0 implemented the first controlled routing substrate: non-executing routing request/assessment models, persisted candidate inventory, binary binding eligibility/ineligibility facts, explicit reason codes, missing-data facts, and operator inspection endpoints without best-binding selection, CBBO, child-intent fanout, mandate-scoped OPEN submission, or hidden cross-venue recovery.`

### T-011

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.1 added operator-requested non-executing target-choice audit records from persisted routing assessments, with explicit assessment/candidate/binding/account validation, blocked statuses, and no child-intent conversion, submission, fanout, CBBO, price/quality scoring, or mandate-scoped OPEN live submission. Phase 5.1.1 now revalidates the current source desired trade before recording a successful target choice.`

### T-012

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.2 implemented controlled target-choice-to-child-intent conversion, and Phase 5.2.1 hardened its lineage checks. One explicit recorded target choice can create exactly one binding/account-targeted child intent only after revalidating target choice, assessment id/ref/environment, candidate, desired-trade client/mandate/source identity, binding mandate ownership, venue-account, and symbol truth. Conversion is idempotent and still avoids preparation, readiness assessment, submission, fanout, CBBO, price/quality scoring, and live routing execution.`

### T-013

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.3 implemented the controlled routed child-intent preparation/readiness handoff, and Phase 5.3.1 hardened its lineage checks. Converted routed child intents can use existing prepared-order preview and readiness inspection only after route-lineage validation; stale desired-trade, routing assessment, target-choice, binding/account, selected-target provenance, child-intent client/mandate identity, target-choice desired-trade linkage, or symbol-mapping drift blocks explicitly. Phase 5.4 now controls routed submission behind a separate explicit gate, while Phase 5.3/5.3.1 still avoid fanout, CBBO, price/quality scoring, and target reselection.`

### T-014

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.4 added the controlled explicit routed submission handoff, and Phase 5.4.1 tightened its phase-boundary truth. A converted routed child intent can submit only through an explicit submit action after Phase 5.3.1 route-lineage validation, normal readiness, the normal live-submit gate, and the separate routed-submit gate pass. Routed phase-boundary submit blocks, including routed-gate and normal live-gate deferrals, preserve child-intent status and write last_submission_block rather than last_submission_failure. The path still avoids auto-submit, fanout, CBBO, venue scoring, target reselection, route executor behavior, and cross-binding recovery.`

### T-015

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.5 added the first routed submitted-order lineage inspection layer, Phase 5.6 tightened malformed-lineage type truth, Phase 5.7 added routed post-submit lifecycle/actionability context, Phase 5.7.1 preserved routed lineage through same-target routed retry while centralizing the routed lineage parser, Phase 5.9 extended that audit context to reconciliation/lifecycle-event surfaces, Phase 5.9.1 made existing platform routed_submission lineage authoritative over colliding reconciliation/update payload keys, and Phase 5.9.2 prevents update payloads from creating routed_submission lineage on non-routed orders. SubmittedOrder API responses now expose read-only routed-origin audit metadata derived from existing submitted-order raw payload; recovery recommendation, recovery execution response, actionability responses, reconciliation responses, and lifecycle-event responses expose same-target routed lifecycle context; non-routed orders/retries/events do not fabricate route ids; malformed routed payloads are bounded with missing-lineage and malformed-lineage facts; and same-target lifecycle behavior remains unchanged. No auto-submit, fanout, CBBO, venue scoring, target reselection, route executor behavior, migration, config, endpoint, or new execution behavior was added.`

### T-016

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.7 implemented the next controlled post-submit routed lifecycle inspection layer after Phase 5.5/5.6, Phase 5.7.1 hotpatched routed same-target retry lineage preservation plus parser deduplication, Phase 5.9 extended the same read-only context to reconciliation/lifecycle-event audit surfaces, Phase 5.9.1 prevents adapter/update payloads from overwriting platform-owned routed_submission audit lineage, and Phase 5.9.2 prevents adapter/update payloads from creating that lineage on non-routed orders. Routed submitted-order recovery/actionability/reconciliation/lifecycle-event surfaces are now route-aware but same-target / same-account / same-venue only, expose routed lifecycle context and malformed-lineage facts, preserve routed audit lineage on same-target retry and reconciliation update results, and still do not add auto-submit, fanout, CBBO, venue scoring, target reselection, cross-binding recovery, cross-venue retry, or route executor behavior.`

### T-017

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.6 defined the first explicit routed order-shape policy for target-choice conversion, Phase 5.8 expanded that policy to accept optional explicit MARKET/LIMIT inputs, Phase 5.8.1 hardened non-finite LIMIT price validation, and Phase 5.8.2 cleaned the malformed/non-finite LIMIT reason surface. Current default conversion remains MARKET / no limit price / reduce_only=false and remains visible in child-intent provenance. Explicit LIMIT now requires a positive finite limit_price and modeled order-type support, while slippage expansion, market-data-derived limit-price sources, auto-submit, fanout, target reselection, route executor work, and broader routed submission expansion remain future work.`

### T-018

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.8 added bounded explicit LIMIT order-shape policy input for routed target-choice conversion, Phase 5.8.1 blocks non-finite LIMIT prices before child-intent creation, and Phase 5.8.2 prevents malformed/non-finite blocks from reporting limit_price_explicit. LIMIT is not inferred and only works with an explicit positive finite limit_price plus modeled order-type support; invalid, non-finite, or unsupported policy blocks before child-intent creation. Slippage guard semantics and market-data-derived limit-price sources remain deferred without target reselection, fanout, CBBO, venue scoring, or auto-submit.`

### T-019

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.9 added routed post-submit reconciliation and lifecycle-event audit visibility only where code/test-proven, Phase 5.9.1 hardened reconciliation raw-payload merging so existing platform routed_submission audit lineage always wins over colliding update payload keys, and Phase 5.9.2 reserves that namespace so update payloads cannot create routed lineage on non-routed orders. Reconciliation responses preserve routed audit payload and expose routed lifecycle context, lifecycle-event responses derive the same context through the shared parser, malformed routed payloads remain bounded, non-routed events do not fabricate route ids, and recovery remains same-target / same-account / same-venue with no target reselection, route executor behavior, fanout, CBBO, venue scoring, auto-submit, cross-binding recovery, or cross-venue retry/failover.`

### T-020

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.10 closed the routing substrate with a focused end-to-end regression pass instead of new routing behavior. The closeout test exercises routing-required desired trade -> routing assessment -> explicit target choice -> exactly-one child-intent conversion -> routed preview/readiness -> explicit gated routed submission -> submitted-order detail/list -> actionability/recovery -> reconciliation with a colliding update-payload routed_submission -> lifecycle-event routed context, while proving selected-account scoping, platform-owned routed_submission namespace truth, typed routed lineage consistency, no extra child intents/submitted orders, and no fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, or auto-submit.`

### T-021

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 5.10.1 added the non-selecting route-readiness/data-sufficiency audit gate before future recommendation, and Phase 5.10.2 hotpatched its truth surface. Audits can be created from routing-required desired trades or existing routing assessments, persist global and per-candidate facts, expose missing/stale/unsupported/unavailable/policy-blocked/blocking reason codes plus data-source labels, label assessment-backed quote facts as derived from the existing assessment rather than fresh venue queries, block missing side and missing/zero/negative quantity, block malformed/non-finite/non-positive quote prices without crashing, and report ready_for_recommendation only as data sufficiency. Default MARKET audit policy is defaulted, not explicit. The audit does not recommend, choose, rank, score, create target choices, create child intents, prepare orders, assess execution readiness, submit, fan out, use CBBO, reselect targets, or execute.`

### T-022

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.0.0 begins controlled single-target recommendation above Phase 5.10.1 / 5.10.2 route-readiness audits, Phase 6.0.1 hotpatches its current-truth boundary, Phase 6.0.2 hotpatches recommendation-time quote freshness plus source-audit recommendation-created truth, Phase 6.1 adds optional deterministic binding-priority recommendation, Phase 6.1.1 tightens policy input / priority clearing truth, Phase 6.2 adds explicit recommendation acceptance into target choice only, Phase 6.2.1 hardens same-audit acceptance idempotency plus original timestamp truth, Phase 6.2.2 gates same-audit idempotency so blocked recommendations cannot be marked accepted, and Phase 6.3 adds explicit accepted recommendation-backed target-choice conversion into exactly one routed child intent. `RoutingTargetRecommendation` records are persisted from route-readiness audits only. The default policy remains `single_ready_candidate_only`: exactly one ready candidate can be recommended after audit freshness, stored candidate quote observation freshness, and current desired-trade/mandate/binding/account/symbol truth are re-checked. The optional `explicit_binding_priority` policy must be requested explicitly, uses nullable `MandateAccountBinding.target_recommendation_priority`, treats lower positive integers as the operator-preference winner, and blocks missing priority, malformed/out-of-range priority, ties, and stale quote observations for the selected candidate. API `policy_name` input is bounded to accepted policies; omitted priority updates preserve existing priority, and `clear_target_recommendation_priority=true` intentionally clears it. Successful recommendations can be explicitly accepted into exactly one non-executing `RoutingTargetChoice` after another current-truth and quote-freshness check; repeated same-recommendation or duplicate successful same-audit acceptance returns the existing target choice and preserves the original recommendation/audit accepted timestamp. Blocked same-audit recommendations remain blocked, retain `target_choice_created=false`, and do not receive accepted-looking provenance. Accepted recommendation-backed target choices can now be explicitly converted through the existing conversion path into exactly one child `OrderIntent`; repeated or duplicate same-audit conversion returns the existing child intent. Conversion still creates no prepared order, readiness evaluation, submitted order, rank, score, allocation, route plan, fanout, CBBO, route executor behavior, target reselection, exchange call, or auto-submit.`

### T-023

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.1 implemented the deterministic multiple-ready-candidate policy as explicit `explicit_binding_priority`, Phase 6.1.1 cleaned up its input and priority-clear semantics, and Phase 6.2 preserves that recommendation behavior while adding explicit acceptance into target choice only. The priority policy is request-level only, uses operator-configured binding priority, accepts only bounded known policy names through the API, preserves omitted priority on updates, clears priority only through `clear_target_recommendation_priority=true`, blocks missing/malformed/tied priority facts, blocks stale selected-candidate quote observations, and still does not create child intents, readiness evaluations, submitted orders, rank, score, allocation, route plans, fanout, CBBO, route executor behavior, target reselection, or auto-submit.`

### T-024

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.2 implemented the recommendation-to-target-choice workflow as an explicit operator-triggered acceptance action, Phase 6.2.1 hardens idempotency across duplicate successful recommendations from the same route-readiness audit, Phase 6.2.2 prevents blocked same-audit recommendations from bypassing validity through idempotency, and Phase 6.3 adds explicit accepted recommendation target-choice conversion into exactly one routed child intent. Acceptance creates or returns exactly one non-executing target choice, accepts only successful recommendations before new target-choice creation or same-audit reuse, revalidates recommendation status, audit/recommendation freshness, stored quote freshness, desired-trade/mandate/binding/account/symbol truth, records recommendation/audit/policy lineage in target-choice provenance, updates recommendation/source-audit `target_choice_created=true` only for valid acceptance, returns the existing target choice on repeated or duplicate successful same-audit acceptance, preserves the first recommendation/audit `recommendation_accepted_at`, and records idempotent retry checks separately. Blocked recommendations from an audit that already has a target choice remain `target_choice_created=false` and are not stamped with acceptance provenance. Phase 6.3 conversion validates accepted recommendation-backed lineage, reuses existing child intent conversion, updates recommendation/source-audit `child_intent_created=true` only after a valid child intent exists, and returns existing child intents for repeated or duplicate same-audit conversions. It does not create prepared orders, readiness evaluations, submitted orders, fanout, CBBO, ranking/scoring, auto-submit, cross-binding/cross-venue recovery, or route-executor behavior.`

### T-025

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.3 implemented the recommendation-accepted target-choice-to-child-intent workflow as a separate explicit operator-triggered phase. It reuses the existing target-choice conversion path, validates accepted recommendation-backed lineage and current truth before new child-intent creation, creates or returns exactly one routed child `OrderIntent`, preserves recommendation/audit/target-choice/order-shape lineage, and still does not create prepared orders, readiness evaluations, submitted orders, fanout, CBBO, ranking/scoring, auto-submit, cross-binding/cross-venue recovery, or route-executor behavior.`

### T-026

- `priority`: `medium`
- `status`: `future`
- `summary`: `Consider remaining persistence-level uniqueness guards or serialized paths for concurrent Phase 6 recommendation acceptance and accepted target-choice conversion if multiple workers can act on the same route-readiness audit or child intent simultaneously. Phase 6.2.1 uses application-level idempotency to return the existing target choice for repeated same-recommendation and duplicate successful same-audit acceptance, Phase 6.2.2 gates that same-audit reuse so blocked recommendations cannot appear accepted, Phase 6.3 uses service-level same-desired-trade/same-audit child-intent reuse, Phase 6.10.1 adds a narrow persistence-backed explicit child-intent submit lease so concurrent submit calls for one intent cannot both reach adapter submission before a SubmittedOrder exists, Phase 6.10.2 makes adapter-returned/local-persistence-failed submit uncertainty terminal until operator reconciliation/manual cleanup, and Phase 6.10.3 makes adapter-in-flight uncertainty terminal before the adapter call begins. These phases preserve original timestamps and add no broad workflow engine; future DB-level serialization for recommendation acceptance/conversion remains a hardening item before automation or multi-worker route execution.`

### T-027

- `priority`: `medium`
- `status`: `done`
- `summary`: `Initialized source-control hygiene for the Phase 6.3 baseline on the `master` branch. The baseline tracks source, tests, migrations, docs, operational memory, `.gitignore`, and `.env.example`, while `.env`, virtualenvs, caches, local database/runtime state, logs, review ZIPs, and handoff archives are intentionally ignored. Future phase work should use short-lived branches off `master`.`

### T-028

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.4 implemented the recommendation-backed child-intent preparation/readiness inspection handoff. Accepted recommendation-backed child intents now use the existing prepared-order preview and submission-readiness paths with additional validation for source recommendation, route-readiness audit, candidate quote freshness, current mandate, binding/account, and active/trading-eligible symbol mapping. Preview/readiness API responses expose routed lineage including recommendation/audit/target-choice/selected-target/order-shape facts. The phase creates no submitted orders, exchange submit calls, route executor behavior, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit.`

### T-029

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.4.1 hotpatched recommendation-backed preview/readiness truth. Routed child-intent lineage validation now blocks when stored routed order-shape policy is missing, malformed, or mismatched against the current OrderIntent order_type, limit_price, or reduce_only fields; readiness-time stale stored quote observations now use quote_stale_at_readiness. Tests prove order-type, LIMIT-price, reduce-only, missing-policy, and stale-quote blockers occur before adapter preparation/submission. No migration, config, endpoint, submitted order, exchange submit call, route executor, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit was added.`

### T-030

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.5 added a manual routed-flow inspection harness in scripts/manual_routed_flow.py. It starts from an existing desired trade key, emits JSON artifact traces, can explicitly call the current routing assessment, route-readiness audit, target recommendation, recommendation acceptance, target-choice conversion, prepared-order preview, and execution-readiness service paths through --run-through-readiness, and skips submission by default. Submit attempts are locally blocked without --i-understand-this-can-place-a-live-order and any confirmed submit still relies on existing service gates. Tests cover readiness-through flow output, default no-submission behavior, no SubmittedOrder creation, and local submit blocking. No smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, new exchange behavior, config, or migration was added.`

### T-031

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.6 added local per-step timing visibility to the manual routed-flow harness. scripts/manual_routed_flow.py now emits top-level timing_ms, including total runtime, and adds elapsed_ms to each executed step using monotonic timing. Default inspect-only still runs only the desired-trade step, --run-through-readiness still stops before submission, and --submit without the danger-confirmation flag still blocks locally before service submission while recording local submission-block timing. Tests verify timing shape, non-negative numeric values, omitted skipped-step timing, and continued no-submission behavior. No smart routing, best-binding selection, ranking/scoring, CBBO, fanout, target reselection, route executor, auto-submit, new exchange behavior, telemetry persistence, config, or migration was added.`

### T-032

- `priority`: `high`
- `status`: `done`
- `summary`: `Phase 6.7 through Phase 6.10 close Phase 6 as controlled explicit single-target recommendation-backed routed execution, and Phase 6.10.1/6.10.2/6.10.3 hotpatch submit/workflow truth before merge. The accepted recommendation-backed child intent can create exactly one SubmittedOrder only through the existing explicit gated child-intent submit path; concurrent explicit submit calls are serialized with a persistence-backed child-intent submit lease before adapter submission; adapter-in-flight attempts are marked `adapter_submit_may_have_started` before adapter submission can begin; adapter-returned/local-persistence-failed attempts are marked `adapter_submit_persistence_unknown`; both uncertainty states block future submits until operator reconciliation/manual cleanup; submitted-order and lifecycle/actionability/recovery/reconciliation surfaces expose recommendation/audit/target-choice/intent/readiness lineage; same-target retry preserves the first submitted-order id while exposing latest/retry submitted ids separately; reconciliation payload collisions cannot overwrite platform-owned routed lineage or fabricate recommendation lineage on non-routed orders; and a read-only routed workflow inspection endpoint aggregates existing records by desired trade without creating or mutating artifacts. Closeout regression proves exactly one target choice, one child intent, one submitted order, selected account/venue/symbol consistency, and no hidden auto-submit, route executor, fanout, allocation, ranking/scoring, CBBO, target reselection, cross-binding recovery, or cross-venue retry.`

### T-002

- `priority`: `high`
- `status`: `future`
- `summary`: `Deepen the approval layer into broader mandate/account exposure, drawdown, concentration, and binding-policy checks without collapsing desired-trade approval into routing or execution.`

### T-003

- `priority`: `high`
- `status`: `future`
- `summary`: `Implement later routed execution orchestration only after the Phase 5.4 explicit selected-child-intent submission handoff has enough post-submit lifecycle depth. Target reselection, fanout, CBBO, price/quality scoring, and auto-submit remain out of scope until separately designed and tested.`

### T-004

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement execution-quality market data for top-of-book and depth summary across Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken with clearer parity expectations.`

### T-005

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement richer portfolio accounting and attribution overlays for mandate-aware and venue-account-scoped policy evaluation.`

### T-006

- `priority`: `medium`
- `status`: `future`
- `summary`: `Add additional strategy families without hardcoding the platform around Money Flow.`

### T-007

- `priority`: `medium`
- `status`: `future`
- `summary`: `Implement mandate-level routing across a binding account group after the live-execution layer below routing is mature enough, including later best-binding selection, CBBO support, quote comparison across bindings, and child-intent orchestration without static allocation weights.`

### T-008

- `priority`: `medium`
- `status`: `future`
- `summary`: `Extend mandate market-data / pricing source policy beyond the current single-source mode into richer source-policy behavior, including later composite pricing support and fuller decoupling between planning-source selection and routing venues.`

### T-009

- `priority`: `low`
- `status`: `future`
- `summary`: `Extend the six current venues beyond the current Phase 4.10.2 submit/reconcile/cancel/amend/recovery/private-state depth into broader truthful amend parity for Aster/Binance where support can be proven, fuller private-account streams, richer direct account-state/event parity, and deeper order-state visibility without blurring venue-private views into platform submitted-order identity.`

### T-010

- `priority`: `low`
- `status`: `future`
- `summary`: `Evaluate optional external execution backends such as CoinRoutes after the native decision/risk/intent/execution path is mature enough.`
