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

## v2026.06.08.002

- `recorded_at_utc`: `2026-06-08T06:50:34Z`
- `scope`: `LOG-OBS1 Runtime Logs scroll stability hotfix`
- `intent`: `Native entry. Fixed the Paper Trading Runtime Logs widget so the Read-only log files scroll position is preserved across dashboard refreshes. The one-second Paper Trading market-refresh path re-rendered Runtime Control, which replaced the log-list DOM and jumped the nested scroll container back to the top. The renderer now skips identical log metadata updates, restores the nested log-list scroll offset after changed metadata renders, and cache-busts dashboard assets so the browser picks up the fix. This is dashboard display only: no runtime behavior changed, no runtime was started or stopped, no orders were submitted, no live trading was approved, and no strategy was production-approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `tests/test_dashboard_static_assets.py`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py tests/test_dashboard_control_server.py tests/test_pt_rt1_runtime_log_visibility.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `git diff --check`

