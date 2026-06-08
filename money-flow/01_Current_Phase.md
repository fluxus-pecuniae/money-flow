# Current Phase

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime config: `PT-RT1.6` founder-selected Week 2 slate is active under ignored `reports/paper_runtime/pt_rt1_6_week2_active/` and verified by the local control server.
- Dashboard state: `DASH-PT1.3` makes Paper Trading a contained exchange-style terminal: top health strip, left filter/watchlist rail with internal scrolling, center public-mainnet chart with compact paper markers, height-bounded right Runtime Control / Testnet Order Transport rail, bottom tabbed blotter for positions, trades, decisions, lifecycle, logs, scoreboard, and diagnostics, and a final full-width Daily Review / Anomaly Flags card below the blotter. The visible Audit tab remains removed. `LOG-OBS1` adds read-only Runtime Logs metadata and the terminal helper `scripts/watch_pt_rt1_runtime.py`. `OBS-OS1` adds a read-only daily review/anomaly generator plus the dashboard `Daily Review / Anomaly Flags` panel.
- Active Week 2 default slate: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- Active timeframes: `1h`, `4h`, `1d`.
- Paused timeframes: `15m` remains paused as diagnostic/legacy context only.
- Strategy truth: public Hyperliquid mainnet fully closed candles and derived indicators.
- Synthetic PnL truth: independent synthetic 10,000 USDC paper ledgers per lane.
- Testnet plumbing: fixed 25 USDC Hyperliquid testnet transport is allowed only for fresh post-start Money Flow v1.2 baseline opens when gates and local signing config pass. Candidate/MF-ORIG lanes remain synthetic-only and testnet fills never update synthetic PnL.
- Research discovery: `GOAL-STRAT1` supersedes `STRAT-DISC1` as the latest research-only discovery pass; 49 local public-mainnet selected replay datasets were accepted, 121 bounded candidate configurations were tested across 7 strategy families, and zero strategies passed the strict founder production-testing review gate.
- Research candidates: `GOAL-STRAT2` selected two non-existing strategies worth paper-testing review only: relative-strength rotation with ATR trailing exit, and Donchian breakout with ATR trailing exit.
- Strategy pruning: `STRAT-PRUNE1` is complete as a recommendation-only review, but the founder overrode its suggested slate for Week 2.
- Production approval: no strategy is production-approved.
- Live trading: not approved; no real-capital trading is approved.
- Latest operating review: `PT-RT1.6.2` reviewed active Week 2 logs through the `2026-06-08T08:00:00Z` closed-candle cycle. Status is `observation_may_continue`; 0 active `15m` rows, 0 candidate-lane testnet lifecycle rows, 0 unknown/open testnet state, and 0 testnet PnL updates were found.
- Next recommended action: continue the active `pt_rt1_6_week2_active` run unchanged for another 24h, then repeat the operating review before adding/removing lanes.
- Current daily-review command: `.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --status --scope pt_rt1_6_week2_active`; use `--generate` to write the ignored dashboard-readable daily pack.

## Current Implemented Milestone

`GOAL-STRAT1` Autonomous Strategy Discovery is complete as a separate research-only goal. It adds an expanded selected-replay JSON data inventory, a reusable strategy-discovery harness, bounded candidate generation, strict candidate gates, Markdown/JSON reports, a no-three-candidates exhaustion report, and focused tests. The run tested Money Flow repair, source-faithful Money Flow/stage, trend/breakout, volatility expansion, mean reversion, relative strength, and pairs/spread research families. It found no founder production-testing review candidates without overfitting/risk blockers after 121 candidate configurations. The closest near misses remain research-only because positive aggregate PnL pockets failed drawdown, chronological out-of-sample, anchored out-of-sample, concentration, profit-factor, sample-size, or market-structure gates. GOAL-STRAT1 changed no production Money Flow rules, mutated no PT-RT runtime artifacts, called no exchange/private/signed/order endpoints, submitted no orders, used no testnet strategy truth, approved no strategy for production, and approved no live trading.

`GOAL-STRAT2` Two Non-Existing Strategies Worth Testing is complete as research-only candidate selection. It consumes the committed GOAL-STRAT1 summary, excludes current PT runtime lanes plus Money Flow/SOR/MF-ORIG/wildcard-adjacent families and entry models, applies a weaker founder paper-testing gate, and selects exactly two family-diverse candidates: `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34` and `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20`. These are not production candidates and not active runtime lanes. The relative-strength candidate has both OOS checks positive but drawdown near the paper-testing limit and material ZEC/timeframe/period concentration. The Donchian candidate has strong aggregate PnL/PF/drawdown/sample, but both OOS checks are mildly negative and it also has concentration risk. GOAL-STRAT2 changed no production Money Flow rules, mutated no PT-RT runtime artifacts, called no exchange/private/signed/order endpoints, submitted no orders, used no testnet strategy truth, approved no strategy for production, and approved no live trading.

`PT-RT1.6` Founder-Selected Week 2 Paper Slate is implemented as readiness/config only. The founder-selected active default paper slate is exactly `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`. The other prior PT-RT lanes are archived/default-inactive from active Week 2 scoring without deleting evidence, reports, or code. Active timeframes remain `1h`, `4h`, and `1d`; `15m` remains paused. Only the baseline control remains testnet eligible; `avoid_low_rolling_range_20`, the selected MF-ORIG lane, and archived lanes are synthetic-only. The dashboard/control server now prefer `reports/paper_runtime/pt_rt1_6_week2_active/` and show no-active-run/stale-artifact state. PT-RT1.6 does not start the runtime, submit orders, change production Money Flow rules, approve production, or approve live trading.

`PT-RT1.6.2` Week 2 Operating Review + Risk Triage is complete as reporting/review only. It reviewed the already-running ignored `pt_rt1_6_week2_active` runtime without starting/stopping it or changing runtime behavior. The review found 1056 decisions split evenly across the three selected lanes, active timeframes `1h`/`4h`/`1d`, 0 active `15m` rows, 58 open positions with MTM updated, 40 closed synthetic trades in `trades.jsonl`, 33 baseline-only testnet lifecycle rows, 21 accepted/canceled/reconciled testnet rows, 12 fail-closed metadata/precision blocks, 0 candidate-lane testnet triggers, 0 unknown/open testnet state, and 0 testnet PnL updates. Daily Review status is `observation_may_continue` with one informational warm-start block spike. The recommendation is to continue Week 2 observation unchanged for another 24h and triage blocked testnet metadata symbols only if transport coverage becomes important.

`DASH-PT1.1` Paper Trading Week 2 UI Truth + Readability Polish is complete as dashboard-only cleanup. Paper Trading now displays configured Week 2 truth even before runtime rows exist: three active lanes, seven archived/default-inactive lanes, configured paper symbols AVAX/BNB/BTC/DOGE/ETH/HYPE/SOL/SUI/XRP, active `1h`/`4h`/`1d`, and `15m` paused/legacy. The Strategy tab now lists only the three active Week 2 strategies as active/default. Audit artifacts remain historical docs/data, but the visible Audit tab/panel is removed from founder navigation. No runtime behavior changed, no runtime was started, no orders were submitted, no production approval was granted, and live trading remains not approved.

`LOG-OBS1` Runtime Log Visibility Fix is complete as observability-only operator tooling. The local dashboard control status payload now exposes runtime log-file metadata for the active output scope, including file path, size, modified timestamp, role, empty-file hint, and copyable `tail -n 50 -F` commands. Paper Trading Runtime Control renders that metadata in a compact Runtime Logs panel. `scripts/watch_pt_rt1_runtime.py` gives read-only terminal modes for status, latest rows, and tailing `runtime_audit.jsonl`, `decisions.jsonl`, `trades.jsonl`, and `testnet_order_lifecycle.jsonl`. This clarifies that VS Code can show existing rows while `tail -F` waits for newly appended lines, and that `trades.jsonl` can be empty until a synthetic position closes. No runtime behavior changed, no runtime was started or stopped, no orders were submitted, no production approval was granted, and live trading remains not approved.

`OBS-OS1` Week 2 Paper Observation Operating System is complete as read-only daily review tooling. `scripts/build_pt_rt_week2_daily_review.py` summarizes ignored Week 2 runtime logs, writes ignored Markdown/JSON packs under `reports/paper_reviews/pt_rt1_6_week2_active/`, and emits anomaly flags for runtime freshness, decision/trade activity, 15m boundary, testnet boundary, synthetic-PnL boundary, duplicate/warm-start spikes, MTM risk, and drawdown review. Paper Trading now loads `latest_review.json` in a lower-priority `Daily Review / Anomaly Flags` panel when present; DASH-PT1.3 places that panel as the final full-width card below the positions/trades/decisions blotter. The current local status is `observation_may_continue` with one informational `warm_start_block_spike` flag. OBS-OS1 changes no runtime behavior, starts/stops no runtime, submits no orders, approves no live trading, and approves no production strategy.

`DASH-PT1.2` Paper Trading exchange-style terminal polish is complete as dashboard-only UI work. Paper Trading now opens as a trading terminal rather than a vertical diagnostics stack: the top health strip summarizes Week 2 truth and safety boundaries, the left rail holds filters plus Watchlist, the center stage prioritizes the public-mainnet chart, the right rail holds Runtime Control and Testnet Order Transport, the bottom blotter tabs expose Open Positions, Closed Trades, Signal Stream, Testnet Lifecycle, Runtime Logs, Weekly Scoreboard, and Diagnostics, and Daily Review / Anomaly Flags sits as the final full-width card under the blotter. This changed no runtime behavior, started/stopped no runtime, submitted no orders, approved no live trading, and approved no production strategy.

`DASH-PT1.3` Paper Trading terminal layout QA hotfix is complete as dashboard-only UI work. UI QA found left filter overflow, unbounded Watchlist height, right-rail card pushdown, bottom blotter pushdown, misleading runtime freshness labels, verbose chart marker labels, Daily Review competing with Runtime/Testnet in the right rail, and a low-value Watchlist Status column. The hotfix keeps filters inside the left rail, bounds Watchlist and right-rail panel heights with internal scrolling, compacts Runtime details to high-signal fields, removes the Watchlist Status column, moves Daily Review / Anomaly Flags below the blotter as the last card, and compacts chart marker labels while preserving marker data. This changed no runtime behavior, started/stopped no runtime, submitted no orders, approved no live trading, and approved no production strategy.

`STRAT-PRUNE1` Strategy Lane Pruning + Candidate Selection is complete as recommendation-only governance. It reviewed the existing 10 PT-RT lanes against GOAL-STRAT, STRAT-DISC, SOR, MF-ORIG, EV-AUDIT, and PT-RT evidence. Its suggested relative-strength/Donchian slate remains research-only because the founder selected a different Week 2 slate in PT-RT1.6.

`PT-RT1.5.3` Hyperliquid Testnet Size / Precision Hotfix is implemented on top of `PT-RT1.5.2`, `PT-RT1.5.1`, `PT-RT1.5`, `PT-RT1.4.1`, `PT-RT1.4`, `PT-RT1.3`, and the earlier PT-RT1 public-mainnet paper-observation setup. PT-RT1 remains the forward-observation substrate rather than another backtest: a public-mainnet strategy-truth lane with fully closed candle gating, indicator computation, independent synthetic 10,000 USDC paper ledgers, and a separate Hyperliquid testnet plumbing lane that never updates strategy paper PnL. PT-RT1.5.3 keeps active timeframes at `1h`, `4h`, and `1d`, keeps `15m` as `disabled_for_week1_noise_reduction`, preserves candle-close-only signal evaluation, preserves warm-start false-to-true gating, and fixes fixed-25-USDC testnet order sizing by resolving Hyperliquid testnet public metadata before submit. The smoke configured the signed client from scoped local env without printing secrets, called the Hyperliquid testnet signed order endpoint once, received accepted/open, canceled the order, reconciled to no open order, created no synthetic trade, and did not update synthetic PnL. Candidate/MF-ORIG/wildcard lanes remain synthetic-only. Public mainnet candles remain strategy truth, testnet fills never update synthetic PnL, no live trading is approved, no strategy is production-approved, and production Money Flow rules are unchanged.

`OB2.0` Obsidian Strategy Brain + Evidence Architecture Refresh is complete as the current documentation/governance baseline on top of completed `EV-AUDIT1`. OB2.0 refreshes the vault so founder/agents can distinguish current Money Flow v1.2, Original Money Flow / MF-ORIG, SOR repair variants, STRAT-EV plan-only discovery, canonical evidence methodology, dashboard display-only visualization, UAT sandbox plumbing, and PT-RT1 paper-observation readiness.

`EV-AUDIT1` Full Strategy Hypothesis, Data Integrity, and Paper-Readiness Audit is complete. It is audit-only and does not add strategy variants, regenerate evidence packs, change production Money Flow rules, approve paper/live, submit orders, or call private/signed/order endpoints. The audit inventories Money Flow v1.2 canonical SV2.0.2, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and STRAT-EV1 plan-only status; checks SV2.0.2 data integrity; scores methodology/data/candidate confidence; explains biggest winners, biggest losers, losing streaks, regime/control-pocket attribution, and P0/P1/P2/P3 issues. The verdict was: no clean strategy candidate is promoted, current evidence is good enough for visual review and hypothesis filtering only, and real-time paper observation was conditionally ready as separately scoped `PT-RT1`. PT-RT1 is now implemented as substrate only; EV-AUDIT1 still does not authorize production rule changes, strategy paper-runtime authorization, live trading, or real-capital behavior.

EV-AUDIT1 remains committed historical audit material, but `DASH-PT1.1` removes the visible `Audit Review` tab from the founder dashboard navigation to keep the Week 2 startup surface focused.

SUBAGENTS1 is a workflow/governance addition on top of this current phase: project-scoped Codex agents `runtime_reviewer`, `dashboard_reviewer`, and `quant_reviewer` exist under `.codex/agents/` and are read-only by default. They are intended for bounded review/triage of runtime artifacts, dashboard clarity, and paper-trade quality. They do not change strategy/runtime/dashboard behavior and do not approve production, paper, live, or testnet behavior.

The dashboard now exposes a `Paper Trading` tab that visualizes PT-RT runtime summaries for founder review using the DASH-PT1.1 command-center order. It shows configured Week 2 truth before runtime rows exist, keeps archived lanes out of the default active view, uses configured symbols instead of runtime-row-only symbols, labels `15m` as paused/legacy, prioritizes the public-mainnet chart, separates Testnet Order Lifecycle from synthetic trades, and keeps lower-priority scoreboards/diagnostics below positions/trades/decisions. The Runtime Control section also shows read-only Runtime Logs metadata for the selected output scope so operators can identify the correct files to inspect. The underlying implementation still uses the `paper-observation` view id and PT-RT Paper Observation runtime naming, but the current founder-facing tab is Paper Trading. The Start Run path uses PT-RT1.5.x-compatible Week 2 control flags, `--fresh-signal-only-after-runtime-start`, `--disable-legacy-testnet-probes`, candle-close signal evaluation, fixed 25 USDC baseline-only signed testnet transport gates, `--public-mainnet-only`, and compact decision logging. It exposes no arbitrary command, no private/signed/order endpoint path from strategy truth, no API-key path for strategy truth, no candidate-lane testnet order path, and no testnet strategy truth. The tab is display/runtime-observation UI only: dashboard filters are display-only, testnet lifecycle rows are plumbing only, no live order controls are present, and no paper/live production approval follows from the dashboard.

PT-RT1.2 remains the runtime-state and transport-gate baseline under PT-RT1.5.3: processed signal keys, open synthetic positions, realized equity by lane, last processed close state, closed synthetic trades in `trades.jsonl`, duplicate same-candle open blocking, and compact-log suppression/size stats are preserved. Signed testnet transport remains only an explicit gated path and is now wired for PT-RT1.5.3 behind exact approval, local env secrets, testnet URL validation, fresh post-start baseline opens or one labeled transport smoke, and the separate lifecycle ledger; it cannot be called from the strategy-truth lane. PT-RT1.3 remains the candle-truth data-health layer: stale/thin/missing/nonpositive Hyperliquid public mids are warning-only when clean fully closed public-mainnet `candleSnapshot` rows are available, with mid-warning rollups separated from candle/indicator blocking state. PT-RT1.4.1 status remains `active_runtime_cutover_verified_after_restart`; the older active runtime is archived rather than treated as default Week 1 scoring.

`MF-ORIG-EV2` Original Money Flow multi-timeframe evidence packs and Historical Replay UI are complete, including the founder-requested full-equity comparison regeneration. The corrected Original Money Flow reconstruction now has evidence-only packs across four source-faithful 1% risk-sizing hypotheses plus four full-equity/notional counterparts, BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and both next_candle_open / next_candle_close fill assumptions. The source PDF is now present in `money-flow/90 Reference/`, so future MF-ORIG work can reconcile direct source text instead of relying only on prompt summaries. Candidate gates were re-run against canonical SV2.0.2 Money Flow v1.2 baseline rows; no original hypothesis is production-approved, paper-approved, or live-approved. `SOR-EV3` Founder-Selected Avoid Sideways / Low-Volatility Drilldown is complete and no variant was promoted. `SV2.0.2` Hardened Candle DB Import + Canonical SV2 Evidence Pack Generation is complete with 36 canonical packs, 9 supported symbols, 4 timeframes, and 72 scenario rows. `SV2.0` made `sleeve_1d` a real Money Flow v1.2 sleeve while preserving existing 15m/1h/4h settings. Testnet market data is not strategy truth. PT0 sandbox/testnet paper-plumbing approval remains separate from strategy evidence; no strategy paper runtime is approved by EV-AUDIT1.

`SV2.1` Founder-Approved Hyperliquid 1D Period Evidence is complete as a research-only data/evidence refresh and now has Historical Replay artifacts for all 10 PT-RT1 paper-observation lanes. The earlier broad active-metadata run was rejected for founder review and removed from local generated outputs. The current run used public Hyperliquid mainnet `meta` and `candleSnapshot` only, targeted the founder-approved requested/resolved universe, mapped TRON to TRX, excluded PEPE/kPEPE and OKB by resolver policy, imported available 1D candles into the intended local strategy-validation DB back to 2024-01-01 where available, and generated 90 ignored baseline period packs across 2024, 2025, YTD, and ALL. The follow-up builder generated 1800 ignored selected Historical Replay chart/trade JSON files under `reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data/20260516T091500Z` and 810 ignored evidence-only candidate/reference/wildcard pack directories across all 9 non-baseline PT-RT1 lanes. ASTER and TRUMP have no 2024 period packs because public 1D candles do not cover that period; no candles were fabricated. This is 1D founder-review evidence breadth only. It does not change production Money Flow rules, supersede the SV2.0.2 multi-timeframe canonical baseline, approve paper/live, submit orders, call private/signed/order endpoints, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named gaps were closed. UAT0.1 closes the P0 API auth/authz baseline and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verifies allowed public Hyperliquid endpoint behavior, fetches a no-key public top-volume source, and resolves the Hyperliquid-supported top-20 observation universe. UAT1.1 adds shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 completed a bounded no-order Money Flow shadow observation across the UAT1 Hyperliquid top-20-supported universe. UAT2.1 makes that UAT2 output visually reviewable in the static dashboard and adds an informational UAT3 blocked readiness panel. UAT3.0 through UAT3.0.6 define and dry-run the sandbox/testnet gate chain. UAT3.1 is complete as a rejected one-shot Hyperliquid testnet ETH lifecycle probe. UAT3.2 is complete as a blocked fixed-key preflight. UAT3.3 fixed Hyperliquid account targeting and ETH precision, and a later founder-approved follow-up verified accepted/open -> cancel -> reconcile on Hyperliquid testnet with normal user mode and `vaultAddress` omitted. UAT3.4 operationalizes that success as a fixed-target sandbox routing pipeline and routed-order ledger: the active route is Hyperliquid testnet ETH only, selected equity source is `standard_perp_clearinghouse`, unified/portfolio spot-clearinghouse USDC fallback remains implemented/tested, one approved UAT3.4 order was accepted/open and canceled successfully, reconciliation found no open order, and the dashboard displays routed-order ledger truth without order controls. UAT4.0 added the read-only dashboard/chart cockpit. UAT4.1 rebuilt it into an exchange-style workstation with compact top bar, persistent safety banner, observation-only market rail, central chart cockpit, right order-book/market/signal/risk rail, bottom blotter tabs, and canonical design doc at `apps/dashboard/DESIGN.md`. UAT4.2 adds read-only public-market monitor summary data, deterministic indicators, paper-observation markers, a 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger without adding order controls or order endpoints. PT0 adds an official local TradingView Lightweight Charts bundle, live public testnet candle rendering, top-20 paper/sandbox universe eligibility, deterministic paper scanner records, an internal 10,000 USDC paper-equity ledger, current-equity sizing policy, 60-second sandbox private-read-only polling policy, and default-disabled risk-gated sandbox routing foundation. PT0.0.1 fixes the founder-reported TradingView chart growth/page-scroll P0 by bounding chart height, containing parent layout, updating existing chart/series handles across refreshes, removing the autosize feedback-loop risk, limiting `fitContent()` to new symbol/timeframe initialization, and adding emergency live-polling disable query flags. The follow-up dashboard chart correctness hotfix uses Playwright to verify BTC/SOL public candles are mixed red/green, prevents non-selected symbols from displaying synthetic local fallback candles as live chart data, and adds explicit price readouts beside the TradingView chart. PT0.0.2 adds a Historical Replay cockpit using historical public candle replay data, not Hyperliquid testnet prices, as Money Flow strategy truth for BTC/ETH/SOL x 15m/1h/4h, with TradingView historical candles, entry/exit markers, trade inspector, dynamic 10,000 USDC equity, BTC/ETH/SOL comparison, separate sandbox execution plumbing visibility, and a research-only MACD-removed replay strategy selector that does not change production rules.

PT0.0.3 added 1D historical replay support and Jan 2025 data-horizon truth as an aggregated replay view only. SV2.0 supersedes that prior limitation by adding `sleeve_1d` as a real Money Flow sleeve and by using direct Hyperliquid public mainnet `1d` candle readiness/evidence where available. The SV2.0.2 dashboard display fix now loads ignored chart/trade JSON derived from the regenerated canonical packs, so Historical Replay can show BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX across 15m/1h/4h/1d when the generated local files are present. Historical Replay now also exposes generated SOR-EV3 `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` research replays across those same symbols/timeframes/fills. Historical Replay chart arrows select their linked trade in the Trade Inspector, arrow descriptions are off by default, and the invalid Experiments tab is not exposed. SOR-EV2.1 adds the visible Evidence Lab tab for SOR-EV1/SOR-EV2 bundle review while keeping variants evidence-only. SOR-EV2.2 adds Evidence Lab baseline-vs-variant overlays, worst-trade focus, and control-pocket overlay review while still keeping every variant evidence-only. SOR-EV3 adds a focused Evidence Lab section for `avoid_sideways_low_volatility`, but no variant is approved. The dashboard now shows Money Flow v1.2, expanded symbols, `sleeve_1d`, SV2.0.2 readiness/evidence, and SOR variant review panels while keeping sandbox execution separate.

SV2.0.2 is complete and regenerated with fully closed per-pair canonical evidence packs. SV2.0.1 and SV2.0 are complete.

## Next Proposed Phase

Do not promote any GOAL-STRAT1 or STRAT-DISC1 result. GOAL-STRAT2 candidates may be reviewed for a separately scoped paper-only test phase, but they are not production-approved, live-approved, testnet-transport eligible, or active PT runtime lanes. STRAT-PRUNE1 recommends a concrete next slate, but runtime implementation belongs to `PT-RT1.6 - Add Selected Paper-Test Candidate Lanes` if the founder accepts it. A future discovery pass should first improve non-overlapping out-of-sample coverage, control-pocket slicing, and execution-quality constraints before widening parameters or strategy families.

Run or continue a fresh PT-RT active-week observation session with PT-RT1.5.3 present. Keep `15m` paused/legacy unless the founder explicitly re-enables it in a later phase. The first review should confirm warm-start startup-valid signals are blocked, candle-close scheduler timing, market-refresh/no-signal cycles, duplicate closed-candle blocking, active-week row reset, open-position MTM, baseline-only fixed 25 USDC signed testnet lifecycle rows when a fresh Money Flow v1.2 baseline open occurs, candidate-lane transport blocks, testnet fills not updating synthetic PnL, and no-live/no-production boundaries. The older `reports/paper_runtime/pt_rt1_5_2_transport_smoke/`, `reports/paper_runtime/pt_rt1_5_1_smoke/`, `reports/paper_runtime/pt_rt1_5_week1_active/`, `reports/paper_runtime/pt_rt1_4_1_active_week/`, and `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` rows are archived context, not default active Week 1 scoring. The latest committed `PT-RT Week 1 Daily Summary` remains `docs/pt_rt_week1_day_summary.md` until the PT-RT1.5.3 hotfix-era scope has fresh active rows.

`MF-ORIG-EV3` or `SOR-EV4` may be scoped only after founder review and stricter control-pocket/out-of-sample-style slicing. No production-rule-change phase is approved from EV-AUDIT1, MF-ORIG-EV2, SOR-EV1, SOR-EV2, SOR-EV3, or PT-RT1.

UAT3.5 additional sandbox routing lifecycle tests are blocked until UAT-universe precision validation is complete or unsupported Hyperliquid testnet observation symbols are explicitly scoped out of routing precision acceptance. PT0.1 may run the supervised top-20 paper/sandbox runtime only if it preserves no-live-endpoint, no-live-capital, risk, kill-switch, current-equity sizing, submit-lease, and dashboard monitoring boundaries. UAT/PT remains plumbing and behavior validation plus controlled paper/sandbox runtime only. It is not live trading, unrestricted exchange order submission, routing expansion, or strategy optimization.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| UAT mode | Observation / shadow first |
| Execution | UAT3.4 recorded one approved fixed-target sandbox route attempt, accepted/open then canceled and reconciled; PT0 visualizes this ledger, public-read-only monitor rows, browser-polled testnet chart candles, TradingView Lightweight Charts, and internal paper-equity state; PT0.0.2/PT0.0.3 visualize historical strategy replay separately from sandbox execution plumbing |

The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline.

## UAT Observation Universe And Timing

Future UAT observation is not ETH-only. UAT1/UAT2 should use top 20 high-volume crypto assets supported by the selected UAT venue/environment to validate platform behavior, market metadata, symbol mapping, risk visibility, no-trade/rejected-signal reasoning, and operator explainability. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared:

- `next_candle_open`
- `next_candle_close`

`same_candle_close_research_only` remains research-only.

## Explicit Non-Approvals

- PT-RT1 synthetic paper observation is not production paper-runtime approval.
- Historical PT0 sandbox/testnet paper-plumbing approval remains separate from strategy evidence and does not approve a production strategy.
- Live trading is not approved.
- Live exchange order submission is not approved.
- Sandbox/testnet order routing is default-disabled and remains risk-gated by `PT0_SANDBOX_ORDER_ROUTING_ENABLED`.
- Further Money Flow rule changes, optimizations, and variant promotions are not approved beyond the SV2.0-approved addition of `sleeve_1d`.
- Lower-RSI variants are not approved.
- Market-structure variants are not approved.
- Cross-venue evidence is not current UAT scope.
- Routing / SOR expansion is not current priority.

## Current Evidence Meaning

Current backtest/replay evidence does not prove profitability or future edge. It was sufficient only to justify founder review and a tightly scoped UAT0 safety/runtime audit.

SV1.18 selected ETH `sleeve_1h` baseline because it is the strongest observed Hyperliquid public-candle scenario. That does not make it a production strategy.

Excluded from UAT scope:

- `sleeve_15m`
- `sleeve_4h`
- BTC `sleeve_1h`
- SOL `sleeve_1h`
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 Result

UAT0 initially found UAT1 blocked. UAT0.1 closed these P0 items:

- API authentication / authorization for sensitive `/api/v1` routes.
- High-risk route authorization for admin consume, submit/cancel/amend/retry, account, and private-state surfaces.
- Inspectable fail-safe runtime safety policy with paper/live/order/private endpoint flags disabled by default.
- Test-only auth bypass limited to `API_RUNTIME_MODE=test`.

UAT0.2 closed or partially closed these P1 items:

- Adapter-level private/signed/order runtime-policy enforcement is implemented and tested before transport.
- Hyperliquid selected-venue future-UAT1 read-only allowlist exists as a testable policy artifact.
- Representative redaction for bearer tokens, API keys, secrets, passwords, and DB URLs is tested.

UAT0.3 closes the UAT1 preflight baseline:

- Top-20 source/intersection resolver policy exists and is fixture-tested.
- Hyperliquid public read-only info types are allowlisted for future UAT1.
- Runtime drawdown monitor policy/model exists and is fixture-tested from caller-supplied observed equity.
- UAT1 public read-only connectivity preflight was satisfied with no private endpoints, no signed endpoints, no order endpoints, no API keys, no paper trading, no live trading, and no order submission. UAT1 is now complete.

UAT1 is now complete:

- Explicit UAT1 public-read-only mode was required before network calls.
- Hyperliquid public read-only info types were verified with HTTP 200 and usable response shape.
- CoinGecko public markets data was fetched without API keys as the top-volume source.
- The generated UAT1 report includes 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets.
- No private, signed, or order endpoints were called; no strategy decisions, order intents, submitted orders, paper trades, live trades, evidence packs, or Money Flow rule changes were created.

UAT1.1 is now complete:

- Shadow signal audit records exist for no-trade / would-trade / risk-block explainability.
- Operator-visible shadow drawdown state exists and is clearly not live-account drawdown.
- UAT1 universe snapshot loading is available for UAT2.
- Representative structured API-error/log redaction verification exists.
- No UAT2 loop, strategy decisions, order intents, submitted orders, paper/live behavior, evidence packs, exchange calls, private/signed/order endpoints, or Money Flow rule changes were created.

UAT2 is now complete:

- Explicit UAT2 shadow mode and public-read-only network flags were required.
- The UAT1 universe snapshot was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- UAT2 produced 45 shadow audit records: 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked`.
- ETH `sleeve_1h` produced `no_trade` with `macd_not_constructive`.
- `next_candle_open` and `next_candle_close` were represented; `same_candle_close_research_only` remained research-only.
- Shadow drawdown was visible as `shadow_simulated_drawdown` / `not_live_account_drawdown`, with no PnL simulation and no live account equity implication.
- No private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

UAT2.1 is now complete:

- The static dashboard has a `UAT2 Shadow Run` tab sourced from `docs/uat2_shadow_strategy_top20_observation_summary.json`.
- It displays UAT2 summary cards, a filterable 45-record shadow signal matrix, would-open inspection, no-trade reason breakdowns, ETH `sleeve_1h` candidate truth, timing assumptions, not-live-account shadow drawdown, no-artifact boundary flags, and UAT3 blockers.
- At that point, UAT3.1 actual sandbox order submission remained blocked; the dashboard adds no active approval action and cannot enable orders.
- No private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

UAT3.0 is now complete:

- Initial sandbox-order scope is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- Founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- Dashboard UAT view includes an informational UAT3.0 design/readiness panel.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.1 is now complete:

- Fail-closed sandbox runtime policy exists and defaults sandbox submission, private endpoints, live endpoint access, paper/live trading, and generic exchange order submission to disabled.
- Sandbox artifact label validation exists and fails missing/unsafe sandbox/testnet/not-live/not-paper labels.
- Future UAT3.1 actual-submission approval wording now requires a one-attempt sandbox/testnet approval with exact venue, environment, symbol, component, max size/count, order type, time window, sandbox account, kill switch, and lifecycle scope.
- Approval scope validator, sandbox risk gate evaluator, sandbox drawdown feed fixture, and submit-lease duplicate-prevention fixture are implemented and fixture-tested.
- Dashboard UAT view shows fixture/readiness status.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.2 is now complete:

- Sandbox risk gates propagate all `SandboxRuntimePolicy` blockers into risk/preflight reason codes instead of silently ignoring non-mode blockers.
- Approval scope, risk limits, risk requests, and drawdown fixtures reject non-positive or invalid sandbox numeric values with explicit reason codes.
- A unified fixture-only dry-run sandbox gate preflight evaluates runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder/operator actual-submission approval, and artifact-label persistence status.
- The dry-run result reports that it creates no order intent, submitted order, executable approval, or exchange call.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.3 is now complete:

- Sandbox artifact label boundary helpers cover persistence, API serialization, dashboard display, and report generation.
- A dry-run executable gate service wires runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks into one side-effect-free path.
- Runtime semantics now explicitly separate broad/global exchange order submission from sandbox/testnet-only submission.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.4 is now complete:

- Private read-only sandbox account policy and endpoint categories distinguish account/balance/position/equity reads from order submission/cancel/amend/retry paths.
- Credential approval and credential-boundary validation require the exact founder/operator private-read-only approval text before any sandbox/testnet private read-only credential use.
- Credential redaction covers representative authorization headers, bearer tokens, API keys, secrets, passwords, private keys, and DB URLs.
- Sandbox account drawdown feed modeling can represent unavailable fields explicitly and can report `sandbox_drawdown_feed_missing`, `sandbox_drawdown_feed_fixture_only`, `sandbox_drawdown_feed_private_read_only_verified`, and `sandbox_drawdown_feed_live_fed_verified`.
- The required private-read-only credential approval was not present, so no credentials were used and no private endpoints were called.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.5 is now complete:

- The exact founder/operator approval for sandbox/testnet private read-only credential use is present and validated for account-state/drawdown-feed verification only.
- Local sandbox/testnet credential environment variables are present and the base URL is verified as Hyperliquid testnet.
- Sandbox/testnet base URL validation blocks live Hyperliquid endpoints and requires sandbox/testnet host identity before any private read-only path can proceed.
- One Hyperliquid testnet read-only account-state request returned HTTP 200 and produced a `sandbox_account` / `not_live_account` drawdown feed with `sandbox_drawdown_feed_live_fed_verified`.
- No API key/private key was sent; no order/cancel/amend/retry endpoint was called.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.6 is now complete:

- A non-persistent `UAT3SandboxSubmissionPlan` exists for the future ETH `sleeve_1h` sandbox path and records all dry-run no-artifact/no-exchange side-effect flags as false.
- `UAT3SandboxSubmitDryRunService` composes runtime policy, founder actual-submission approval status, sandbox artifact-label boundary validation, approval scope validation, live-fed sandbox drawdown status, sandbox risk gates, submit-lease duplicate-prevention checks, and adapter endpoint classification.
- The dry-run consumes the UAT3.0.5 `sandbox_drawdown_feed_live_fed_verified` status and blocks if drawdown is missing, stale, fixture-only, threshold-breached, or not labeled `not_live_account`.
- The future endpoint category is classified as `sandbox_order_submission`, but transport invocation remains forbidden in UAT3.0.6 and `calls_exchange=false`.
- UAT3.1 was blocked at the time because founder/operator actual-submission approval was still required and actual transport enablement belonged to a later explicit UAT3.1 phase.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.1 is now complete:

- Exact founder/operator approval for one sandbox/testnet order submission attempt was present and validated.
- The UAT3.1 runner used sandbox/testnet endpoint validation, live-fed sandbox drawdown, approval scope validation, sandbox risk gates, submit-lease duplicate prevention, sandbox artifact labels, endpoint classification, and post-only/nonmarketable order-shape checks before transport.
- Exactly one Hyperliquid testnet ETH post-only limit order attempt under 10 USDC notional was made.
- Hyperliquid rejected the attempt with a sanitized user/API-wallet-not-found response.
- No cancel was required, reconciliation found no open order, and no unexpected fill occurred.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.

UAT3.2 is now complete:

- Exact founder/operator approval for one second sandbox/testnet order attempt was present and validated.
- The runner checked fixed-key account/API-wallet readiness, Hyperliquid testnet endpoint identity, live-fed sandbox drawdown, approval scope, sandbox risk, submit-lease duplicate prevention, sandbox labels, and post-only/nonmarketable ETH order shape before any order-capable transport.
- Fixed-key readiness blocked because the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient.
- Order attempt count was `0`; no order, cancel, amend, retry, or private order endpoint was called.
- Cancel and reconciliation were not attempted because no order existed.
- UAT4.0 live UAT trading dashboard / chart cockpit is complete, and UAT4.1 rebuilds it as a read-only exchange-style workstation.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

UAT3.3 is now complete:

- Exact founder/operator approval for one Hyperliquid testnet/sandbox ETH manual lifecycle probe was present.
- Account targeting now separates normal master/user accounts, API-wallet signers, and subaccount/vault targets.
- Normal master/user mode omits `vaultAddress`; subaccount/vault mode uses only the configured explicit target address.
- Hyperliquid precision formatting now uses `meta` `szDecimals`, five-significant-figure price rules, and perpetual max price decimals.
- UAT-universe precision validation is reported for BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, and AAVE.
- The runner verified the configured subaccount targeting and signer authorization, generated a sanitized planned ETH post-only order with valid precision under 10 USDC notional, then blocked before `/exchange` because target subaccount equity was `0.0`.
- Order attempt count was `0`; no order, cancel, amend, retry, or private order endpoint was called.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

UAT4.0 is now complete:

- The dashboard has a `UAT Chart Cockpit` tab sourced from committed UAT2 shadow and UAT3.4 routed-order summary JSON.
- It shows watchlist, market-data coverage, static chart snapshots, EMA5 / EMA10 / SMA20 / RSI / MACD labels, shadow/sandbox lifecycle markers, active route/equity-source cards, routed-order filters, and no-order-control safety labeling.
- It calls no private, signed, or order endpoints; uses no API keys; creates no approvals or order artifacts; and adds no paper/live behavior.

UAT4.1 is now complete:

- The dashboard cockpit has been rebuilt into an exchange-style workstation with compact top bar, persistent safety banner, left market rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs.
- `apps/dashboard/DESIGN.md` is now the canonical dashboard design system; root `DESIGN.md` is a pointer.
- It keeps top-20 assets observation-only, shows the ETH sandbox route as ledger visibility only, and adds no order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls.

Remaining later blockers:

- PT0.0.4 may scope historical data backfill and replay regeneration to reach Jan 2025 where possible; it must preserve historical candle strategy truth and no-order/no-live boundaries.
- PT0.1 requires explicit founder/operator scope before supervised top-20 paper/sandbox runtime is operated continuously.
- PT0.1 should use trusted market data for strategy truth, not Hyperliquid testnet prices.
- PT0.1 needs deployment-mode monitoring, continuous scanner scheduling, current-equity sizing enforcement against live paper PnL, submit-lease behavior, no-live-endpoint smoke checks, and operator kill-switch runbooks.
- UAT3.5 requires separate founder/operator approval before any additional sandbox order attempt.
- UAT-universe precision validation remains incomplete for unsupported Hyperliquid testnet observation symbols.
- Additional sandbox orders outside PT0/PT0.1 risk-gated scope remain unapproved.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
