# CHANGELOG

Canonical repo changelog — the recent rolling window. New entries are added
here (newest-first). Older entries (v2026.06.08.001 and earlier) are in
[`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md); recent window + archive
together are the complete, canonical history. When this file exceeds ~25
entries, roll the oldest into the archive as part of the post-task update.

Entry schema:

- `version`
- `recorded_at_utc`
- `scope`
- `intent`
- `affected_files`
- `validation_performed`

---

## v2026.06.11.005

- `recorded_at_utc`: `2026-06-11T16:45:00Z`
- `scope`: `FUND-EV1 delta-neutral funding carry evidence`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Tests the structural non-predictive edge: harvest Hyperliquid perp funding hedged delta-neutral on ONE venue (short perp + long HL spot equal notional; BTC/ETH/SOL via Unit spot + native HYPE; aligned window 2025-05-11 -> 2026-06-08, limited by the youngest spot listing USOL), 10k USDC basis. New committed data input: public read-only fundingHistory hourly rates aggregated to daily sums per coin with provenance + sha256 (docs/fund_ev1_funding_data_snapshot_summary.json via scripts/fetch_fund_ev1_funding_snapshot.py; raw hourly + HL spot candles are documented ignored artifacts). New fourth strategy-type route funding_carry (prefix fund_ev1_) with its OWN gate: net carry after ALL costs positive OOS (chronological 70/30 + anchored walk-forward thirds), not bull-only, leave-one-out robust, tail drawdown inside documented limits (OOS <=5%, stressed <=8%) - judged on Sharpe + max drawdown, never gross funding. Simulator: pending-fill queue (fills only enter the book when their candle closes - a lagged hedge leg holds REAL one-leg exposure), exact daily funding accrual on the perp leg (positive funding pays the short), EXEC-EV1 friction + fees on BOTH legs (spot always at the widest mid-alt tier), trailing-funding tilt (causal), rebalance band, forced final close, per-symbol reconciliation (K-019). Bounded 8-config grid (collect_only/flip_sides x cadence 7/14 x top 2/4), train-only choice. RESULT: gate verdict carry_does_not_survive_costs_and_tail_oos - train (bull, funding 8-14%/yr) +4.23% Sharpe 7.2; OOS (2026 funding-compressed bear) -33 USDC (-0.32%, Sharpe -1.55) with gross OOS funding still +50 but two-leg conservative friction eating more than all of it; full-window net +392 vs gross +560 (costs ate 30.0%); walk-forward fold C negative; ALL leave-one-out drops negative. Clean-fill neutrality is tight (max residual 0.18%, stressed DD 0.92%) - the real tail is the LEGGED FILL: one slow hedge leg leaves up to 47.9% of equity unhedged for a day, a modeled 11.3% gap loss at the window's worst candle (23.6%). Flip-side rows assume unmodeled spot borrow (upper bounds, documented); daily-close accrual approximation documented. Research Log: authored outcome FAIL (badge 'costs + bear eat the carry'); schema class list extended with funding_carry; aggregator gains fund_ev1 computed views (15 entries, --check green). TREND-CARRY synthesis hypothesis recorded in TODO (trend short side paid by funding - with the regime caveat that funding compresses exactly when the bear arrives). Tests: tests/test_fund_ev1_evidence.py (14 deterministic offline tests: routing, exact funding accrual + sign, two-leg neutrality, costs on both legs, no-lookahead + leaky-reader catch, real one-leg-exposure stress, inversion exit, reconciliation, gate semantics incl. every reason code, committed-summary/snapshot reconciliation, research-log honesty pin) wired into the blocking CI lane. Oldest changelog entry (v2026.06.08.002) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/fund_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/fetch_fund_ev1_funding_snapshot.py`
  - `scripts/run_fund_ev1_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/fund_ev1_funding_data_snapshot_summary.json`
  - `docs/fund_ev1_delta_neutral_carry_evidence_summary.json`
  - `docs/fund_ev1_delta_neutral_carry_evidence.md`
  - `docs/research_log_schema.md`
  - `docs/research_log.json`
  - `tests/test_fund_ev1_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_fund_ev1_evidence.py`
  - `.venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_exec_ev1_execution_quality.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`
  - `python -m compileall -q services scripts tests`
  - `git diff --check`

## v2026.06.11.004

- `recorded_at_utc`: `2026-06-11T15:00:00Z`
- `scope`: `TSMOM-EV1 volatility-targeted time-series momentum evidence`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Tests trend done right after the earlier trend failures: per-asset time-series momentum (sign of trailing 30/60/90d return; exact zero = flat) with VOLATILITY TARGETING + equal risk budgets (risk parity) on the eight liquid majors (BTC/ETH/SOL/XRP/DOGE/BNB/SUI/AVAX; HYPE excluded - mid-alt tier, short history), 10k USDC basis, weekly rebalance, next-open fills, EXEC-EV1 depth-aware friction at traded notional, gross leverage cap 1.5x, per-asset weight cap 0.40, bounded 12-config grid chosen on train only. New third strategy-type route time_series_momentum (prefix tsmom_ev1_) with its OWN gate: Sharpe + max drawdown vs EQUAL-WEIGHT BUY-AND-HOLD, OOS (chronological 70/30 + anchored walk-forward thirds), post-conservative-friction, leave-one-out across all eight assets, late-entry sensitivity - never the selection random-benchmark or per-symbol breadth gates. Benchmarks computed on identical machinery: buy-hold equal-weight (headline), always-long no-vol-target, always-long vol-targeted (leveraged-beta probe), seeded random long/flat (20 seeds, sanity). RESULT: gate verdict beats_buy_hold_risk_adjusted_oos WITH non-failing honesty qualifiers (oos_absolute_sharpe_not_positive_relative_edge_only, oos_absolute_return_negative_defensive_value_only): chosen lb30/vt20/long-only OOS Sharpe -1.48 / DD 16.6% / return -12.2% vs buy-hold -1.81 / 65.7% / -61.7% in a bear window; edge survives both walk-forward folds (+1.16/+0.41) and all 8 leave-one-out drops; beats vol-targeted beta (-1.89) and random median (-2.00) but not the best random seeds (max -1.12); hindsight long/short configs had positive OOS Sharpe (+0.22) but the train split honestly chose long-only and perp funding is unmodeled (documented). Per-symbol PnL reconciles to net (K-019 lesson); max name share ~34%. Research Log: authored outcome MIXED (badge 'defensive, not profitable') - a relative pass with negative absolute OOS performance must never render green; new standing rule that relative gates carry absolute qualifiers (hardened-gates rail); schema class list extended with time_series_momentum. Tests: tests/test_tsmom_ev1_evidence.py (13 deterministic offline tests incl. vol-parity risk contributions, leaky-scorer catch, friction monotonicity, gate semantics + qualifier pins, committed-summary reconciliation, research-log honesty pin) wired into the blocking CI lane. Aggregator gains tsmom computed analytics views; research_log.json now 14 entries; DASH-QA1 12/12 with zero green badges preserved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `services/strategy_validation/tsmom_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/run_tsmom_ev1_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/tsmom_ev1_vol_targeted_momentum_evidence.md`
  - `docs/tsmom_ev1_vol_targeted_momentum_evidence_summary.json`
  - `docs/research_log.json`
  - `docs/research_log_schema.md`
  - `tests/test_tsmom_ev1_evidence.py`
  - `.github/workflows/ci.yml`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_tsmom_ev1_evidence.py` → deterministic evidence build (2.9s), verdict + qualifiers as documented
  - `.venv/bin/python -m pytest -q tests/test_tsmom_ev1_evidence.py tests/test_rlog1_research_log.py tests/test_sel_ev1_selection_evidence.py` → 34 passed
  - `.venv/bin/python scripts/build_research_log.py --check` → ok (14 entries)
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 12 passed (TSMOM renders amber mixed; zero green badges)
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.11.003

- `recorded_at_utc`: `2026-06-11T12:00:00Z`
- `scope`: `DASH-QASWEEP1 investor-readiness UI shakedown + fix`
- `intent`: `UI/display fixes only; chart + markers untouched; no safety label or honest verdict softened. Drove the whole dashboard like a user in two passes (deterministic + 1s-refresh-active with mocked endpoints, zero real network), recording console/page errors at every step. Fixed: (1) BLOCKER - the 1s market refresh destructively rebuilt every filter <select> (renderSelect/renderSelectWithoutAll) making dropdown picks take many clicks - now idempotent via data-render-key, never rebuilt under focus, value preserved; (2) Runtime Logs open log re-defaulted to latest each refresh - rows are now expandable details with state-tracked selection (latest only when nothing selected, survives re-renders); (3) console 404 noise from the control-server status probe - adaptive 10s/60s backoff + zero probes under ?disableLivePolling (explicit unavailable state; deterministic/CI loads are now console-clean); (4) 57px page overflow @1600 in all themes from the Output-slate select min-content blowout - min-width:0/width:100% on the control-grid fields; (5) 45px overflow <=1180 from stale tablet rules (3-col rail split + rigid 160/220 control-grid tracks) - rails single-column, override removed; (6) REGRESSION FOUND+FIXED: tablet/mobile stacking silently dead since DASH-IA1 (base terminal-grid rule appended after the legacy media blocks) - stacking re-asserted <=1180, verified 390/768/1180/1280 zero overflow; (7) inline-flex actions row spill - block flex. Flagged (not fixed): one native 404 per 60s probe persists on machines without the control server (not JS-suppressible) - run the control server for the demo. DASH-QA1 grew 10 -> 12 checks (refresh stability with mocked live endpoints; zero-console-error + no-overflow hygiene) - 12/12 green. Final sweep: zero issues, zero console errors. Demo screenshots + investor-readiness checklist in docs/dash_qasweep1_*. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `docs/dash_qasweep1_investor_readiness_sweep.md`
  - `docs/dash_qasweep1_investor_readiness_sweep_summary.json`
  - `docs/dash_qasweep1_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - full exploratory sweep (deterministic + mocked 1s-refresh passes) → 0 issues, 0 console/page errors
  - CI follow-up: QA check #12 exempts only the documented gitignored optional-artifact 404s (reports/paper_runtime/, reports/paper_reviews/ — absent on CI by design); verified via CI-emulation with reports/** forced to 404 → 0 non-exempt errors
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 12 passed
  - widths 390/768/1180/1280 → stacked/3-col as intended, zero horizontal overflow
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.11.002

- `recorded_at_utc`: `2026-06-11T07:00:00Z`
- `scope`: `RLOG1 Research Log: honest post-mortems, auto-joined + analytics`
- `intent`: `Display + docs/tooling only; read-only aggregation; Decision-Log backfill additive only. Must 1: machine-readable post-mortem schema — each research phase's 03_Decision_Log.md entry carries a fenced yaml research_log block (phase/date/class/outcome/why/worked/didnt/lesson/our_error/changed/evidence_summary/analytics/hardened_gate) with the honest outcome taxonomy fail|mixed|context|pass AUTHORED in the log, never inferred from a summary status string; backfilled into 12 phases (SEL-EV1, EXEC-EV1, SV2.3, SV2.2, GOAL-STRAT1/2, SOR-EV1/2/3, MF-ORIG-EV1.1, MF-ORIG-EV2, EV-AUDIT1) with honest our_error attribution (EXEC-EV1: missing concentration gate let ZEC slip through, fixed via leave-one-out; MF-ORIG-EV1.1: K-019 fee double-count corrected; SEL-EV1: null — the test caught its own overfit). Schema doc docs/research_log_schema.md. Must 2: scripts/build_research_log.py — read-only/deterministic/offline aggregator joining blocks to committed docs/*_summary.json (computed analytics: EXEC-EV1 per-symbol concentration ZEC 132%/ex-ZEC -36k/15-23 negative + top-5 table; SEL-EV1 random benchmark 2/50 + near-miss configs; SV2.3 aggregate -638k/0 survivors; GOAL-STRAT1 121/7/0; SV2.2 coverage), active lanes from current_truth.json, lessons rail from authored hardened_gate fields; emits docs/research_log.json (13 entries incl. RLOG1 itself) with a --check drift guard. Must 3: the dashboard Research Log renders the docs/dash_rlog1_prototype.html structure from research_log.json — standing strip, red verdict banner, expandable post-mortem timeline with six facets + analytics + evidence links, lessons rail, active-lanes card, boundaries footer; badges fail=red/mixed=amber/context=blue/pass=green; the naive verdict||audit_verdict||gate_status||status coloring is REMOVED so a non-positive result can never render green; theme-aware. Must 4: tests/test_rlog1_research_log.py (6 deterministic tests incl. the pinned regression that upbeat ready_for_founder_review/complete statuses keep authored non-positive outcomes) + build --check wired into the blocking CI lane; DASH-QA1 gained check #10 (>=12 post-mortems, zero green badges, SEL-EV1 renders fail, facets visible) — 10/10 green. Must 5: AGENTS.md post-task workflow now requires every research phase to author its research_log block and run the aggregator (CI drift guard enforces). Resolves K-033. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `AGENTS.md`
  - `scripts/build_research_log.py`
  - `docs/research_log.json`
  - `docs/research_log_schema.md`
  - `docs/rlog1_research_log.md`
  - `docs/rlog1_research_log_summary.json`
  - `docs/rlog1_screenshots/*`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/test_rlog1_research_log.py`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `.github/workflows/ci.yml`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/build_research_log.py --check` → ok (deterministic rebuild byte-identical)
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py` → 6 passed
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 10 passed
  - three-theme in-browser exercise → zero page errors
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.11.001

- `recorded_at_utc`: `2026-06-11T00:15:00Z`
- `scope`: `DASH-PT3 Paper Trading header + layout refinements`
- `intent`: `Dashboard display/layout only; chart + markers untouched; every #paper-observation-* id preserved. Six founder refinements on the 2-tab Money Flow OS: (1) always-visible critical-state pills in the header — #top-runtime-pill (RUNTIME ACTIVE green/blinking when the already-polled local control-server status reports a run; IDLE muted; CHECKING while polling) and #top-live-pill (LIVE DISABLED · NOT APPROVED, static red); no new data source. (2) The dense status strip #paper-observation-health-banner relocated from the top to the final full-width reference band after the Testnet footer with all content/ids/lane chips/safety labels intact. (3) Global Filters now lead the body (filters -> watchlist/chart/runtime -> blotter -> daily review -> testnet -> status strip). (4) Runtime Control truncation fixed: right rail widened to minmax(300px,344px) and the right-rail overflow:hidden clip changed to visible — message, copy, output slate, and safety profile all fit; chart stays the dominant panel. (5) Watchlist widened to minmax(212px,252px). (6) OKB removed from the watchlist DISPLAY: scanner_universe rows from the runtime summary bypassed the HIDDEN_DASHBOARD_SYMBOLS filter, so paperObservationBaseScannerRows now applies isVisibleDashboardSymbol to summary rows + configured fallback; pt_rt1.py resolver policy untouched. (7) Daily Review / Anomaly Flags nested scroll removed (max-height/overflow dropped, incl. the mobile variant). Lockstep guard updates: DASH-QA1 #9 extended (pills visible, live pill reads live disabled + not approved, strip renders after the testnet footer) — 9/9 green; static-asset ordering/grid/pill asserts updated — green. Three themes zero page errors; node --check clean; cache-buster dash-pt3-header-pills-20260611; before/after screenshots in docs/dash_pt3_screenshots/. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `docs/dash_pt3_header_and_layout_refinements.md`
  - `docs/dash_pt3_header_and_layout_refinements_summary.json`
  - `docs/dash_pt3_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py` → 9 passed
  - three-theme in-browser exercise → zero page errors; OKB absent from watchlist; pills render
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.007

- `recorded_at_utc`: `2026-06-10T23:30:00Z`
- `scope`: `DOC-LEAN1 changelog rotation + lean pre-task reading`
- `intent`: `Docs/tooling only; no history lost. CHANGELOG.md had grown to 800 KB / 9,257 lines / 292 entries and the AGENTS.md pre-task workflow forced every agent to read it (plus REPO_TREE 238 KB, KNOWN_ISSUES 67 KB, TODO 134 KB) before any task. Must 1: rotated the changelog — CHANGELOG.md now holds the 20 most recent entries (v2026.06.10.006..v2026.06.08.002, 45 KB) plus the archive pointer; new CHANGELOG_ARCHIVE.md holds the older 272 entries verbatim (v2026.06.08.001..v2026.04.06.017). Verified programmatically at rotation time: 20+272=292 headings, no entry dropped or duplicated, recent+archive version order equals the original, and the concatenated entry text reproduces the original byte-for-byte. Must 2: AGENTS.md Changelog Rules now define the recent rolling window + full archive as BOTH canonical (single complete history, not competing changelogs), with the ~25-entry rotation trigger handled in the post-task update; new entries are still written to CHANGELOG.md. Must 3: AGENTS.md Pre-Task Workflow rewritten to the lean current-state set read every task (AGENTS.md, CURRENT_TRUTH.md, 01_Current_Phase.md, the recent CHANGELOG.md, 05_Agent_Coordination.md, task-relevant component docs); REPO_TREE / KNOWN_ISSUES / TODO / CHANGELOG_ARCHIVE / Command Center / Project Memory demoted to consult-on-demand. The post-task UPDATE list is unchanged — reads trimmed, writes untouched. Must 4: tests/test_operational_docs.py updated and green (20 passed): archive added to existence + stale-draft guards; archive-pointer + <=25-entry rolling cap CI-enforced; new lossless-rotation-shape test (>=272 archived, no overlap/duplicates, newest-first continuity). No runtime, strategy, code-behavior, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `AGENTS.md`
  - `tests/test_operational_docs.py`
  - `docs/doc_lean1_changelog_rotation_and_lean_reading.md`
  - `docs/doc_lean1_changelog_rotation_and_lean_reading_summary.json`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - rotation check → 20 + 272 = 292 entries, none dropped/duplicated, entry text byte-for-byte verbatim across the two files
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` → 20 passed
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.10.006

- `recorded_at_utc`: `2026-06-10T22:30:00Z`
- `scope`: `DASH-IA1 consolidate the dashboard to 2 tabs (structural)`
- `intent`: `Dashboard display only. The founder decision: Money Flow OS is two surfaces — Paper Trading (the live desk, now the default tab) and Research Log (institutional memory of what has been tested). DASH-IA1 is the structural cut: nav collapsed from five tabs to two; Historical Replay, The Lab (evidence-lab), and Strategy retired (tabs + panels + view-router entries + ALL render/data-loading code and CSS exclusive to those views, plus the old Evidence renderers whose markup was replaced); Evidence renamed to Research Log with a minimal data-driven placeholder (phase/date/verdict rows read from up to 12 committed docs/*_summary.json evidence summaries with graceful omission; full post-mortem view lands in RLOG1). Monolith reduction: evidence-dashboard.js 12,004 -> 6,753 lines (-5,251, -43.7%), CSS 4,448 -> 3,706, index.html 1,088 -> 620. NOTHING deleted from disk: all SOR-EV/MF-ORIG/SV2.x evidence packs, replay JSON, builder scripts, and docs remain as reference; hidden non-nav UAT legacy panels untouched. Must 1b founder layout notes implemented: Global Filters is a full-width bar directly under the status strip (no longer inside the left rail); skinnier left (Watchlist) and right (Runtime Control) rails so the center chart dominates (prototype proportions); Testnet Order Transport relocated to a full-width footer card below Daily Review with all fields/ids/safety labels preserved; product renamed to Money Flow OS (title, top-bar brand, DESIGN.md). The Paper Trading chart and its markers are untouched. Notable preservation catches during the cut: renderSelectWithoutAll, the paper chart pane constants, and historicalConstantRows were defined inside retired-view code regions but used by Paper Trading — restored next to their surviving callers. DASH-QA1 updated in lockstep (still 9 checks): default-tab check now asserts Paper Trading default; check #7 relocated to assert the 3 current_truth active lanes in the Paper Trading status strip; new retired-tabs-absent + nav-exactly-two assertions; reflow assertions (filter bar not in left rail, testnet footer not in right rail); #9 also asserts footer labels. tests/test_dashboard_static_assets.py rewritten in lockstep with the same safety intent. Verification: DASH-QA1 9/9 green (multiple runs), 96 blocking-lane tests green, all three themes exercised with zero page errors, node --check clean, cache-buster dash-ia1-two-tabs-20260610, before/after screenshots in docs/dash_ia1_screenshots/. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `docs/dash_ia1_two_tab_consolidation.md`
  - `docs/dash_ia1_two_tab_consolidation_summary.json`
  - `docs/dash_ia1_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (multiple runs)
  - blocking-lane battery (safety invariants, truth registry/consistency, week2 slate, static assets, operational docs, obs daily review) → 96 passed
  - three-theme in-browser exercise → zero page errors
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.005

- `recorded_at_utc`: `2026-06-10T21:00:00Z`
- `scope`: `DASH-PT2 Paper Trading bolder exchange reskin`
- `intent`: `Dashboard display only. Elevates the existing DASH-PT1.2/1.3 Paper Trading terminal in place to a bolder, denser, color-coded exchange aesthetic (systematic-fund operator terminal), CSS-led, matching the founder prototype docs/dash_pt2_prototype.html. Must 1: theme-aware DASH-PT2 token layer in evidence-dashboard.css across dark/light/red-zone — per-lane accents mapped to the current_truth.json active lanes (baseline blue --lane-baseline, diagnostic comparator violet --lane-diagnostic, MF-ORIG candidate amber --lane-candidate), crisp --accent-live positive/health accent (+ --accent-live-deep/-ink), --accent-testnet, terminal chip/row-line tokens; the --color-chart-* tokens are untouched so the TradingView palette and theme-rebuild behavior are unchanged. Must 2: reskinned the top health banner into a dense 1px-grid status strip with state-colored cells and lane chips; denser cockpit filters + watchlist with live-accent selected row; bolder chart header (chart internals/bounded heights untouched); accent-gradient Start Run + accent runtime message; testnet-accented transport panel; blotter with accent-underlined tabs, dense sticky-header monospace tables, td.positive/td.negative PnL coloring, translucent terminal status tags; restyled daily review grid + anomaly flags; shared chrome intentionally restyled (top strip edge, brand glow, accent-gradient active nav tab) — no other tab body restyled. Must 3: zero behavior change — only display-only JS markup (paperObservationLaneChip helper + four status-strip state classes); every #paper-observation-* id and DASH-QA1-selected structure preserved verbatim (no selector updates needed); all three themes verified including the chart. Must 4: DASH-QA1 9/9 browser checks green (run twice); before/after Playwright screenshots committed under docs/dash_pt2_screenshots/ (desktop+mobile dark, desktop light/red-zone) via new scripts/capture_dash_pt2_screenshots.py; cache-buster bumped to dash-pt2-bold-terminal-20260610 on CSS+JS. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/index.html`
  - `apps/dashboard/DESIGN.md`
  - `scripts/capture_dash_pt2_screenshots.py`
  - `docs/dash_pt2_prototype.html`
  - `docs/dash_pt2_bolder_exchange_reskin.md`
  - `docs/dash_pt2_bolder_exchange_reskin_summary.json`
  - `docs/dash_pt2_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (two consecutive runs)
  - `.venv/bin/python scripts/capture_dash_pt2_screenshots.py --label before|after` → 5+5 screenshots, all three themes inspected
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.004

- `recorded_at_utc`: `2026-06-10T20:00:00Z`
- `scope`: `SEL-EV1 cross-sectional breakout selection evidence + strategy-type routing seam`
- `intent`: `Research/evidence only. Tests the founder's pivot from approach a (one universal rule per symbol — failed via ZEC concentration) to approach b (cross-sectional selection: each period rank the 23-symbol universe on breakout/relative strength, hold the strongest name(s), rotate as leadership changes). Supersedes the planned GOAL-STRAT3 breadth gate (wrong lens for a strategy designed to concentrate; the ZEC lesson is reframed as a rotation/diversity check; the breadth-gate idea is deferred). Must 0 adds a strategy_type routing seam (services/strategy_validation/strategy_types.py): per_symbol routes to the existing goal_strat1 simulator + breadth gate, cross_sectional_selection routes to the new SEL-EV1 portfolio simulator + random-benchmark gate; the gates can never cross-apply (StrategyTypeRoutingError) and the three Week 2 lanes are tagged per_symbol with behavior/results unchanged (byte-identical golden regression test). services/strategy_validation/sel_ev1.py adds a strict point-in-time cross-sectional simulator (selection at t uses only data <= t; next-candle-open fills; ATR(14)x2.8 trail; fixed-fraction sizing top-1 50% / top-3 30% per name — never full-equity-on-one; EXEC-EV1 depth-aware friction on every fill), bounded signals (donchian_breakout_strength, vol_adjusted_relative_momentum; lookbacks 20/40; top-1/top-3; 4h/1d = 16 configs), a matched-cadence seeded random-selection benchmark, equal-weight buy-and-hold + naive past-return baselines, rotation/diversity metrics, chronological 70/30 + anchored walk-forward thirds OOS with train-only parameter choice, and late-entry (+1/+2 candle) sensitivity. VERDICT: no_selection_skill_demonstrated. The train-chosen config (vol_adjusted_relative_momentum lb40 top3 1d, train net +54292) lost -10460 OOS post-conservative-friction and beat only 2 of 50 random seeds (empirical p 0.96 — worse than random); equal-weight buy-hold OOS -2147; in-sample positivity did not carry out-of-sample. Diversity itself was healthy (23 distinct symbols, max time share 0.13, no single-name bet). Late-entry decay is severe on the full period (+0 net 43832 -> +1 17366 -> +2 12334), confirming breakout selection is acutely timing-sensitive (relevant to RT-HISTSEED1). 15 deterministic offline tests (routing seam, byte-identical per-symbol regression, no-lookahead incl. a synthetic leak that must be caught, seed reproducibility, always-one-symbol diversity flag, friction-on-fills, chronological splits) wired into the blocking CI lane. No runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `services/strategy_validation/strategy_types.py`
  - `services/strategy_validation/sel_ev1.py`
  - `scripts/run_sel_ev1_selection_evidence.py`
  - `tests/test_sel_ev1_selection_evidence.py`
  - `tests/fixtures/sel_ev1/goal_strat1_per_symbol_golden.json`
  - `docs/sel_ev1_selection_evidence.md`
  - `docs/sel_ev1_selection_evidence_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_sel_ev1_selection_evidence.py` → 16 configs + 50 random seeds + baselines, verdict `no_selection_skill_demonstrated`
  - `.venv/bin/python -m pytest -q tests/test_sel_ev1_selection_evidence.py` → 15 passed
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.003

- `recorded_at_utc`: `2026-06-10T16:00:00Z`
- `scope`: `EXEC-EV1 depth-aware modeled execution-friction evidence layer`
- `intent`: `Research/evidence only. Adds a depth-aware modeled friction layer on top of SV2.3's fee/slippage/adverse-gap terms and re-scores the three Week 2 lanes. New model services/execution_quality/exec_ev1.py adds three terms: per-symbol liquidity-tier half-spread, size-aware square-root market impact (participation = notional / candle-dollar-volume liquidity proxy), and a fill-probability unfilled-chase penalty. EXEC-EV1 cost is always >= the SV2.3 parent cost, so EXEC-EV1 net PnL <= SV2.3 net PnL per lane/scenario (verified: 0 violations across 621 rows). MODELED, NOT REAL, DEPTH: liquidity is derived from historical candle volume, not real historical order-book depth (which does not exist; Hyperliquid public l2Book is a current snapshot only) — every output is labeled an assumption layer. Re-score verdicts: mf_orig_1d_stage2_breakout_resistance_full_equity survives base + conservative depth-aware friction but fails stress; money_flow_v1_2_baseline and avoid_low_rolling_range_20 fail all (already negative under SV2.3). Also adds a late-entry / entry-timing cost metric (adverse move from signal candle to fills 0/1/2 candles late): mf_orig cost rises with lateness (~+1.2 -> +15 -> +37 bps), signaling its edge decays at the signal and that historical-position seeding would erode it; the two failing lanes show negative late-entry cost (poor entries). scripts/run_exec_ev1_execution_quality.py reads SV2.2 candles from disk and performs no network I/O. tests/test_exec_ev1_execution_quality.py (14 deterministic tests) wired into the blocking CI lane. K-001 noted partially addressed (modeled, not real depth). Future phase RT-HISTSEED1 recorded. No runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `services/execution_quality/__init__.py`
  - `services/execution_quality/exec_ev1.py`
  - `scripts/run_exec_ev1_execution_quality.py`
  - `tests/test_exec_ev1_execution_quality.py`
  - `docs/exec_ev1_execution_quality_evidence.md`
  - `docs/exec_ev1_execution_quality_evidence_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_exec_ev1_execution_quality.py` → 621 result rows, 0 EXEC-EV1>SV2.3 violations
  - `.venv/bin/python -m pytest -q tests/test_exec_ev1_execution_quality.py` → 14 passed
  - `.venv/bin/python scripts/check_trading_safety_text.py` → OK
  - `.venv/bin/python scripts/check_secret_hygiene.py` → OK
  - `ruff check + format --check` on EXEC-EV1 modules → clean

---

## v2026.06.10.002

- `recorded_at_utc`: `2026-06-10T13:00:00Z`
- `scope`: `CI-CLEAN1 close CI enforcement loop + reproducible installs`
- `intent`: `CI/build config only. (1) Promoted dashboard-qa to blocking by removing continue-on-error=true (lane is consistently green on Ubuntu since DASH-QA1.1). (2) Split the single informational job into two independent jobs typecheck (mypy) and full-tests (pytest -q -m "not browser"), both continue-on-error=true, so a mypy failure no longer hides the full pytest signal. (3) Added pip-tools to dev extras, generated a 226-line requirements-dev.lock, and switched every CI job to install via "pip install -r requirements-dev.lock && pip install -e . --no-deps" for reproducible dependency resolution. KNOWN_ISSUES K-031 added for the strict-mypy informational debt with explicit promotion criterion (do not silence mypy or relax strict). No runtime, strategy, order, testnet, slate, approval, dashboard-behavior, or test-logic changes. mypy strict mode not silenced. browser marker not folded into the main test run.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `pyproject.toml`
  - `requirements-dev.lock`
  - `.github/workflows/ci.yml`
  - `docs/ci_clean1_ci_enforcement_close_and_locked_deps.md`
  - `docs/ci_clean1_ci_enforcement_close_and_locked_deps_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml` → 226 lines
  - `pip install -r requirements-dev.lock && pip install -e . --no-deps` → clean
  - `python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → 66 passed
  - `python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed
  - `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → YAML OK

---

## v2026.06.10.001

- `recorded_at_utc`: `2026-06-10T10:00:00Z`
- `scope`: `DASH-QA1 dashboard browser smoke + chart-stability regression`
- `intent`: `Added a deterministic Playwright-based browser-smoke suite for the Paper Trading dashboard that pins documented regressions: tab routing, terminal layout, chart growth stability (autoSize feedback-loop P0), tab-state persistence, blotter-tab refresh stability, Audit-tab absence, three-active-lane strategy view, 15m-paused timeframe filter, and synthetic/testnet/no-live boundary labels. Suite serves the repo root over a localhost HTTP server, opens index.html?disableLivePolling=true in headless Chromium, and sources expected lane/timeframe values from current_truth.json (TRUTH1). pyproject.toml adds pytest-playwright to dev extras, registers a browser marker, and sets addopts="-m 'not browser'" so the suite is opt-in. CI gains a dedicated dashboard-qa job that runs the suite; lane starts informational (continue-on-error) and will be promoted to blocking after 3 consecutive green CI runs. KNOWN_ISSUES K-030 notes the Chromium binary requirement. No dashboard behavior changed (no data-testid hooks added), no runtime/strategy/order/approval state changed.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `pyproject.toml`
  - `.github/workflows/ci.yml`
  - `tests/dashboard_qa/__init__.py`
  - `tests/dashboard_qa/conftest.py`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `docs/dash_qa1_dashboard_browser_smoke.md`
  - `docs/dash_qa1_dashboard_browser_smoke_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `playwright install chromium`
  - `python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (3 consecutive runs: 24.4s, 23.0s, 22.9s)
  - `python -m pytest --collect-only tests/dashboard_qa/` → 9 deselected (default discovery excludes browser marker)
  - `python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → 66 passed (pre-push safety check)

---

## v2026.06.09.003

- `recorded_at_utc`: `2026-06-09T13:00:00Z`
- `scope`: `CI-SAFE1.1 CI install fix + blocking-lane coverage`
- `intent`: `CI plumbing fix only. Replaced 'pip install -r requirements.txt' with 'pip install -e ".[dev]"' in both the blocking and informational jobs so CI installs from pyproject.toml (the canonical source — there is no requirements.txt). Restored four fast guard tests (test_pt_rt1_6_week2_slate.py, test_dashboard_static_assets.py, test_operational_docs.py, test_obs_os1_daily_review.py) to the blocking lane. No safety logic, scanner, registry, runtime, strategy, order, testnet eligibility, Week 2 slate, or approval state changed.`
- `affected_files`:
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `grep -rn "requirements.txt" .github/` → no matches
  - `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → YAML OK
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `python -m compileall -q core services apps tests scripts` → OK
  - `python scripts/export_current_truth.py --check` → OK
  - `python -m pytest -q tests/test_trading_safety_invariants.py tests/test_current_truth_consistency.py tests/test_current_truth_registry.py tests/test_pt_rt1_6_week2_slate.py tests/test_dashboard_static_assets.py tests/test_operational_docs.py tests/test_obs_os1_daily_review.py` → 96 passed
  - `python scripts/check_trading_safety_text.py && pytest tests/test_trading_safety_text_guards.py` → 12 passed
  - `python scripts/check_secret_hygiene.py && pytest tests/test_secret_hygiene.py` → 12 passed
  - `python -m pytest -q tests/test_review_bundle_hygiene.py` → 39 passed
  - `ruff check + format --check on CI-SAFE1 modules` → clean

---

## v2026.06.09.002

- `recorded_at_utc`: `2026-06-09T12:00:00Z`
- `scope`: `CI-SAFE1 CI Gate + Trading Safety Invariants`
- `intent`: `Added a GitHub Actions CI workflow and interlocking safety guards that make trading-safety regression visually impossible to merge. Blocking lane: JS syntax (node --check), Python compile (compileall), registry --check, trading safety invariants, registry consistency, trading-safety text guards, secret hygiene scan, review bundle hygiene, ruff on CI-SAFE1 modules. Informational: mypy strict, full pytest. KNOWN_ISSUES K-029 added for lightweight secret scan caveat. No runtime behavior changed, no orders submitted, no private endpoints used, no strategy production-approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `scripts/check_trading_safety_text.py`
  - `scripts/check_secret_hygiene.py`
  - `tests/test_trading_safety_invariants.py`
  - `tests/test_trading_safety_text_guards.py`
  - `tests/test_secret_hygiene.py`
  - `tests/test_review_bundle_hygiene.py`
  - `tests/test_current_truth_consistency.py`
  - `docs/ci_safe1_ci_gate_and_trading_safety_invariants.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `python -m compileall -q core services apps tests scripts`
  - `python scripts/export_current_truth.py --check`
  - `python scripts/check_trading_safety_text.py`
  - `python scripts/check_secret_hygiene.py`
  - `python -m pytest -q tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_secret_hygiene.py tests/test_review_bundle_hygiene.py tests/test_current_truth_consistency.py tests/test_current_truth_registry.py (123 passed)`
  - `ruff check + format --check on CI-SAFE1 modules (clean)`

---

## v2026.06.09.001

- `recorded_at_utc`: `2026-06-09T07:45:00Z`
- `scope`: `TRUTH1 Canonical Current-Truth Registry`
- `intent`: `Native entry. Added a canonical generated current-truth registry so prompts, tests, and docs reference the same code-grounded source and cannot drift. scripts/export_current_truth.py reads Python anchors from services/paper_runtime/pt_rt1.py (PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS, PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS, PT_RT1_6_ACTIVE_TIMEFRAMES, PT_RT1_4_DISABLED_TIMEFRAMES, pt_rt1_6_lane_testnet_eligible, PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC, SUPPORTED_CANONICAL_SYMBOLS, PT_RT1_6_RUNTIME_SCOPE) and core/config/settings.py (RuntimeSafetyPolicy defaults) and writes current_truth.json. CURRENT_TRUTH.md is the rendered human-readable form with active-lane table, archived-lane table, timeframes, symbols, boundaries, and a verbatim Machine Block. tests/test_current_truth_registry.py asserts on-disk json equals a fresh export (drift fails CI). AGENTS.md now includes a Canonical Current-Truth Registry section directing implementation prompts to CURRENT_TRUTH.md instead of re-embedding lane/timeframe/approval truth. money-flow/01_Current_Phase.md links the registry as the canonical quick-reference. Dashboard wiring (Must 4) is deferred: wiring async JSON fetch to PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS would require restructuring the sync init flow; recommend as a follow-up. No runtime behavior changed, no active PT-RT runtime was started/stopped/mutated, no orders were submitted, no private/signed/order endpoints or API keys were used, no testnet data was used as strategy truth, no strategy was production-approved, and live trading remains not approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `AGENTS.md`
  - `CURRENT_TRUTH.md`
  - `current_truth.json`
  - `scripts/export_current_truth.py`
  - `tests/test_current_truth_registry.py`
  - `money-flow/01_Current_Phase.md`
- `validation_performed`:
  - `.venv/bin/python scripts/export_current_truth.py`
  - `.venv/bin/python scripts/export_current_truth.py --check`
  - `.venv/bin/python -m pytest -q tests/test_current_truth_registry.py tests/test_pt_rt1_6_week2_slate.py` → 17 passed
  - `.venv/bin/ruff check scripts/export_current_truth.py tests/test_current_truth_registry.py` → all checks passed
  - `.venv/bin/ruff format --check scripts/export_current_truth.py tests/test_current_truth_registry.py` → 2 files already formatted

---

## v2026.06.08.012

- `recorded_at_utc`: `2026-06-08T13:02:00Z`
- `scope`: `SV2.3 Realistic Backtest + Latest Evidence Layer`
- `intent`: `Native entry. Added a research-only SV2.3 realistic backtest layer over the latest SV2.2 Hyperliquid public-mainnet candles for the founder-selected Week 2 strategies. SV2.3 uses promotion-facing next-candle-open fills only, applies base/conservative/stress execution-cost scenarios, keeps 1h/4h/1d active and 15m disabled, and writes committed Markdown/JSON Evidence outputs. The Evidence tab now defaults to Latest Evidence / SV2.3 realistic backtest instead of mixed legacy evidence packs and shows execution scenario, fee, slippage, and adverse-gap penalty columns. No runtime behavior changed, no active PT-RT runtime was started/stopped/mutated, no orders were submitted, no private/signed/order endpoints or API keys were used, no testnet data was used as strategy truth, no strategy was production-approved, and live trading remains not approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/README.md`
  - `apps/dashboard/DESIGN.md`
  - `docs/sv2_3_realistic_backtest.md`
  - `docs/sv2_3_realistic_backtest_summary.json`
  - `scripts/run_sv23_realistic_backtest.py`
  - `tests/test_dashboard_static_assets.py`
  - `tests/test_sv23_realistic_backtest.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
  - `money-flow/00 Maps/Evidence and Backtesting Map.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_sv23_realistic_backtest.py`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m py_compile scripts/run_sv23_realistic_backtest.py`
  - `.venv/bin/python -m pytest -q tests/test_sv23_realistic_backtest.py`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`

## v2026.06.08.011

- `recorded_at_utc`: `2026-06-08T11:31:59Z`
- `scope`: `SV2.2 Historical Replay UI QA Fix`
- `intent`: `Native entry. Tightened Historical Replay to the SV2.2 latest public-mainnet replay contract: the visible replay controls now use only the three founder-selected Week 2 strategies, active 1h/4h/1d timeframes, SV2.2 period, and supported next-candle fill assumptions. Removed the old fallback that could show baseline replay data for archived/unsupported strategy selections, compacted default chart markers to arrows-only, corrected SV2.2 source/readiness labels, hid the locked period selector, and stopped Paper Runtime status polling while Historical Replay is the active view. No runtime behavior changed, no runtime was started/stopped, no orders were submitted, no production strategy was approved, and live trading remains not approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/index.html`
  - `tests/test_dashboard_static_assets.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `.venv/bin/python -m pytest -q tests/test_sv22_research_refresh.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py`
  - `git diff --check`
  - `Playwright rendered QA against http://127.0.0.1:3001/apps/dashboard/index.html`

## v2026.06.08.010

- `recorded_at_utc`: `2026-06-08T10:57:45Z`
- `scope`: `SV2.2 Latest Public-Mainnet Replay Correction`
- `intent`: `Native entry. Corrected SV2.2 from a chart/readiness-only refresh into the intended latest public-mainnet Historical Replay pass for the founder-selected Week 2 strategies: money_flow_v1_2_baseline, avoid_low_rolling_range_20, and mf_orig_1d_stage2_breakout_resistance_full_equity. The refresh still uses Hyperliquid public mainnet meta/candleSnapshot only, covers the founder 23-symbol universe across 1h/4h/1d, keeps 15m disabled, and writes ignored replay/evidence-style artifacts under reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data/ plus per-strategy evidence-style pack directories. Historical Replay no longer treats sv2_2_public_candle_refresh as a replay strategy; it defaults to Money Flow v1.2 baseline with SV2.2 latest replay rows. SV2.2 remains research/evidence-style review only, not canonical SV2.0.2 replacement, not active PT-RT runtime behavior, not strategy approval, and not live approval. No runtime was started/stopped/mutated, no orders were submitted, no private/signed/order endpoints or API keys were used, and no production/live approval was introduced.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/DESIGN.md`
  - `apps/dashboard/README.md`
  - `apps/dashboard/evidence-dashboard.js`
  - `docs/sv2_2_hyperliquid_research_refresh.md`
  - `docs/sv2_2_hyperliquid_research_refresh_summary.json`
  - `scripts/run_sv22_hyperliquid_research_refresh.py`
  - `tests/test_dashboard_static_assets.py`
  - `tests/test_sv22_research_refresh.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
  - `money-flow/00 Maps/Evidence and Backtesting Map.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_sv22_hyperliquid_research_refresh.py --fetch-public-data --timeout-seconds 30`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m py_compile scripts/run_sv22_hyperliquid_research_refresh.py`
  - `.venv/bin/python -m pytest -q tests/test_sv22_research_refresh.py tests/test_dashboard_static_assets.py`

## v2026.06.08.009

- `recorded_at_utc`: `2026-06-08T10:25:19Z`
- `scope`: `SV2.2 Research Refresh and Dashboard Refocus`
- `intent`: `Native entry. Added a research-only Hyperliquid public-mainnet refresh for the founder 23-symbol universe across 1h/4h/1d, wrote a committed SV2.2 Markdown/JSON summary, generated ignored selected Historical Replay chart payloads under reports/strategy_validation/sv2_2_research_refresh_dashboard_chart_data/, and refocused the dashboard default landing surface to Historical Replay. SV2.2 is chart/readiness refresh data, not canonical evidence-pack regeneration, not strategy approval, and not active PT-RT runtime behavior. The active paper runtime was not started, stopped, or mutated; no orders were submitted; no private/signed/order endpoints, API keys, testnet strategy truth, live approval, or production approval were introduced.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/index.html`
  - `docs/sv2_2_hyperliquid_research_refresh.md`
  - `docs/sv2_2_hyperliquid_research_refresh_summary.json`
  - `scripts/run_sv22_hyperliquid_research_refresh.py`
  - `tests/test_dashboard_static_assets.py`
  - `tests/test_sv22_research_refresh.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
  - `money-flow/00 Maps/Evidence and Backtesting Map.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_sv22_hyperliquid_research_refresh.py --fetch-public-data --timeout-seconds 20`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m py_compile scripts/run_sv22_hyperliquid_research_refresh.py`
  - `.venv/bin/python -m pytest -q tests/test_sv22_research_refresh.py`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`

## v2026.06.08.008

- `recorded_at_utc`: `2026-06-08T09:08:40Z`
- `scope`: `PT-RT1.6.3 Testnet metadata resolver hotfix and XRP transport smoke plan`
- `intent`: `Native entry. Added a narrow Hyperliquid testnet metadata resolver hotfix for the currently blocked baseline transport symbols XRP/LINK/DOT/LTC/UNI/TRX/ZEC and prepared a PT-RT1.6.3 XRP-targeted transport-only smoke path. The smoke requires exact PT-RT1.6.3 approval, targets XRP only, uses fixed 25 USDC notional, creates no synthetic trade, does not update synthetic PnL, and fails closed before /exchange if XRP metadata or size preflight is unavailable. The active Week 2 pt_rt1_6_week2_active process was not restarted, stopped, or mutated; the hotfix applies to the next process start or the separately scoped smoke after the current 24h window. Candidate/MF-ORIG lanes remain synthetic-only, public mainnet candles remain strategy truth, no live trading was approved, and no strategy was production-approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `README.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `docs/pt_rt1_6_3_testnet_metadata_resolver_hotfix.md`
  - `docs/pt_rt1_6_3_testnet_metadata_resolver_hotfix_summary.json`
  - `scripts/run_pt_rt1_paper_observation.py`
  - `services/paper_runtime/pt_rt1.py`
  - `tests/test_pt_rt1_6_3_testnet_metadata_resolver.py`
  - `money-flow/00_Money_Flow_Command_Center.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_pt_rt1_6_3_testnet_metadata_resolver.py`
  - `.venv/bin/python -m pytest -q tests/test_pt_rt1_5_3_size_precision_hotfix.py`
  - `.venv/bin/python -m pytest -q tests/test_pt_rt1_paper_observation.py`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_control_server.py`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py`

## v2026.06.08.007

- `recorded_at_utc`: `2026-06-08T08:28:04Z`
- `scope`: `PT-RT1.6.2 Week 2 operating review and risk triage`
- `intent`: `Native entry. Added a committed Week 2 operating review over the active ignored pt_rt1_6_week2_active runtime logs. The review verifies the active three-lane slate, 1h/4h/1d-only decisions, 0 active 15m rows, closed-candle-only decision rows, open-position MTM availability, synthetic closed-trade counts from trades.jsonl, baseline-only testnet lifecycle triggers, 0 candidate-lane testnet rows, 0 unknown/open testnet state, 0 testnet PnL updates, and the current Daily Review status observation_may_continue. This is reporting/review only: no runtime behavior changed, no runtime was started or stopped, no manual orders were submitted, no live trading was approved, no strategy was production-approved, and candidate/MF-ORIG lanes remain synthetic-only.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `docs/pt_rt1_6_2_week2_operating_review.md`
  - `docs/pt_rt1_6_2_week2_operating_review_summary.json`
  - `tests/test_pt_rt1_6_2_operating_review.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
- `validation_performed`:
  - `.venv/bin/python scripts/watch_pt_rt1_runtime.py --status`
  - `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --status --scope pt_rt1_6_week2_active`
  - `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate --scope pt_rt1_6_week2_active`
  - `.venv/bin/python -m pytest -q tests/test_pt_rt1_6_2_operating_review.py`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m compileall core services apps tests scripts`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `.venv/bin/python -m pytest -q tests/test_obs_os1_daily_review.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_phase3_strategy.py`
  - `git diff --check`

## v2026.06.08.006

- `recorded_at_utc`: `2026-06-08T08:45:00Z`
- `scope`: `DASH-PT1.3 Paper Trading terminal layout QA hotfix`
- `intent`: `Native entry. Fixed UI QA issues from the DASH-PT1.2 Paper Trading terminal layout. The Cockpit / Global Filters controls now stay inside the left rail, the Watchlist is internally scroll-contained and no longer shows the low-value Status column, Runtime Control / Testnet Order Transport are height-bounded in the right rail, Daily Review / Anomaly Flags moved to the final full-width card below the Paper Trading blotter, the bottom blotter is no longer pushed thousands of pixels below the chart, Runtime details are compacted to the high-signal runtime fields, and paper chart marker labels are compacted while preserving marker data. This is dashboard/UI-only: no runtime behavior changed, no runtime was started or stopped, no orders were submitted, no live trading was approved, no strategy was production-approved, and the Week 2 slate/testnet eligibility boundaries were not changed.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/README.md`
  - `apps/dashboard/DESIGN.md`
  - `tests/test_dashboard_static_assets.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `Playwright Chromium screenshot QA at 1440x1000, 390x900, and final 1440x1000 polish review`

## v2026.06.08.005

- `recorded_at_utc`: `2026-06-08T08:10:00Z`
- `scope`: `DASH-PT1.2 Paper Trading exchange-style terminal polish`
- `intent`: `Native entry. Reorganized the Paper Trading view into a dense exchange-style terminal while preserving PT-RT1.6 Week 2 truth. The screen now uses a top health strip, left filter/watchlist rail, center Live Public Candles + Paper Markers chart, right Runtime Control / Testnet Order Transport / Daily Review rail, and a bottom tabbed blotter for Open Positions, Closed Trades, Signal Stream, Testnet Lifecycle, Runtime Logs, Weekly Scoreboard, and Diagnostics. The bottom tab state persists across the one-second market-refresh render path. This is dashboard/UI-only: no runtime behavior changed, no runtime was started or stopped, no orders were submitted, no live trading was approved, no strategy was production-approved, and the Week 2 slate/testnet eligibility boundaries were not changed.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `KNOWN_ISSUES.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/README.md`
  - `apps/dashboard/DESIGN.md`
  - `tests/test_dashboard_static_assets.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `git diff --check`

## v2026.06.08.004

- `recorded_at_utc`: `2026-06-08T07:35:00Z`
- `scope`: `OBS-OS1 Week 2 Paper Observation Operating System`
- `intent`: `Native entry. Added a read-only daily review/anomaly layer for the PT-RT1.6 Week 2 paper scope. The new generator summarizes ignored runtime logs from reports/paper_runtime/pt_rt1_6_week2_active/, writes ignored daily review packs under reports/paper_reviews/pt_rt1_6_week2_active/, and the Paper Trading dashboard now has a lower-priority Daily Review / Anomaly Flags panel that loads latest_review.json when present. This is observability/reporting only: no runtime behavior changed, no runtime was started or stopped, no orders were submitted, no live trading was approved, no strategy was production-approved, and the Week 2 slate was not changed.`
- `affected_files`:
  - `.archiveignore`
  - `.gitignore`
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `KNOWN_ISSUES.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/README.md`
  - `apps/dashboard/DESIGN.md`
  - `docs/obs_os1_week2_paper_observation_operating_system.md`
  - `docs/obs_os1_week2_paper_observation_operating_system_summary.json`
  - `scripts/build_pt_rt_week2_daily_review.py`
  - `tests/test_dashboard_static_assets.py`
  - `tests/test_obs_os1_daily_review.py`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/05_Agent_Coordination.md`
  - `money-flow/00 Maps/Dashboard and UI Map.md`
  - `money-flow/Project_Memory/money_flow_project_memory.md`
- `validation_performed`:
  - `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --status --scope pt_rt1_6_week2_active`
  - `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate --scope pt_rt1_6_week2_active`
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m pytest -q tests/test_obs_os1_daily_review.py tests/test_dashboard_static_assets.py`
  - `git diff --check`

## v2026.06.08.003

- `recorded_at_utc`: `2026-06-08T06:58:17Z`
- `scope`: `LOG-OBS1 Paper Trading Runtime Control layout polish`
- `intent`: `Native entry. Moved Paper Trading Runtime Control into the Live Public Candles + Paper Markers grid so it occupies the right-side chart whitespace, and split the Runtime Control lower area into Read-only log files on the left with Runtime details on the right. This is dashboard layout only: no runtime behavior changed, no runtime was started or stopped, no orders were submitted, no live trading was approved, and no strategy was production-approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.css`
  - `tests/test_dashboard_static_assets.py`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py`
  - `git diff --check`
