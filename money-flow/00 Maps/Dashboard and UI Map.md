# Dashboard and UI Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This note explains current founder-facing dashboard surfaces and what each surface can and cannot prove.

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime config: `PT-RT1.6` founder-selected Week 2 slate is prepared; no active paper run is assumed unless the local control server reports one.
- Dashboard cleanup: `DASH-PT1.3` makes Paper Trading a contained exchange-style terminal while preserving configured Week 2 truth before runtime rows exist. `LOG-OBS1` adds read-only runtime log metadata and terminal log-watching helper support. `OBS-OS1` adds a read-only Daily Review / Anomaly Flags panel sourced from generated ignored paper-review packs; DASH-PT1.3 places it as the final full-width Paper Trading card below the blotter.
- Active Week 2 default slate: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- Active timeframes: `1h`, `4h`, `1d`.
- Paused timeframes: `15m` remains paused as diagnostic/legacy context only.
- Strategy truth: public Hyperliquid mainnet fully closed candles and derived indicators.
- Synthetic PnL truth: independent synthetic 10,000 USDC paper ledgers per lane.
- Testnet plumbing: fixed 25 USDC Hyperliquid testnet transport is baseline-only and fresh-post-start only when gates pass. Candidate/MF-ORIG lanes remain synthetic-only and testnet fills never update synthetic PnL.
- Production approval: no strategy is production-approved.
- Live trading: not approved; no real-capital trading is approved.
- Next recommended action: after founder review, start `pt_rt1_6_week2_active` from the dashboard control server or documented command.

## Source Files

- `apps/dashboard/index.html`
- `apps/dashboard/evidence-dashboard.js`
- `apps/dashboard/evidence-dashboard.css`
- `apps/dashboard/README.md`
- `apps/dashboard/DESIGN.md`
- `scripts/run_dashboard_control_server.py`

## Current Visible Tabs

| Surface | Data Source | Use It For | Do Not Infer |
| --- | --- | --- | --- |
| Paper Trading | PT-RT1 local runtime summaries plus browser public-mainnet display polling | Observe synthetic paper lanes, Signal Generator, open/closed synthetic trades, markers, and optional localhost Start/Stop runtime control | Do not infer live approval, production paper-runtime approval, order permission, or canonical evidence regeneration |
| Historical Replay | Generated local chart/trade JSON from SV2.0.2, SOR-EV3, MF-ORIG-EV2 where present | Visual candle/indicator/trade review | Do not treat date filters as canonical evidence regeneration |
| Evidence | SV2.0.2 batch reports and generated replay rows | Run ledger and comparison tables | Do not treat aggregate sums as one-account PnL |
| The Lab | SOR/MF-ORIG summary bundles and overlays | Variant review, loss anatomy, control-pocket review | Do not treat overlays as production candidates |
| Strategy | Static strategy/config summaries | Understand Money Flow v1.2 and variant ideas at a high level | Do not infer production approval |

## Current Hidden / Legacy Surfaces

The old `Experiments` tab must not be promoted as current truth. The visible `Audit` tab was removed by DASH-PT1.1; audit artifacts remain historical docs/data only. Legacy UAT surfaces may remain hidden for regression and historical context, but they should not compete with current Strategy / Historical Replay / Evidence / The Lab flows.

## Canonical vs Display-Only

- Canonical evidence lives in backend-generated evidence packs and committed founder-readable reports.
- Historical Replay chart JSON is visualization-only.
- Evidence Lab overlays are visualization-only.
- Date filters are display-only. Dashboard date filters are display-only recalculations.
- The Paper Trading view is now Week 2 terminal-first as of DASH-PT1.3: top health strip, contained left Cockpit / Global Filters plus internally scrolling three-column Watchlist rail, center Live Public Candles + Paper Markers chart with compact paper marker labels, height-bounded right Runtime Control / Testnet Order Transport rail, bottom tabbed blotter for Open Positions, Closed Trades, Signal Stream, Testnet Lifecycle, Runtime Logs, Weekly Scoreboard, and Diagnostics, and a final full-width Daily Review / Anomaly Flags card below the blotter. The underlying view id remains `paper-observation`, but current founder-facing language is Paper Trading. Configured Week 2 truth is shown even before runtime rows exist: three active lanes, seven archived/default-inactive lanes, configured symbols AVAX/BNB/BTC/DOGE/ETH/HYPE/SOL/SUI/XRP, active `1h`/`4h`/`1d`, and `15m` paused/legacy. Strategy Lane Comparison is lower-priority and archived lanes do not clutter the default active view.
- The Paper Trading Start Run helper is local runtime ergonomics only; it now defaults to the PT-RT1.6 Week 2 scope, public mainnet strategy truth, compact decision logging, candle-close signal evaluation, warm-start fresh-signal gating, disabled legacy probes, and baseline-only fixed 25 USDC testnet transport gates. Candidate/MF-ORIG/wildcard lanes cannot send testnet orders, and testnet fills do not update strategy paper PnL.
- LOG-OBS1 adds a Runtime Logs panel to Runtime Control and the read-only `scripts/watch_pt_rt1_runtime.py` helper. Operators can now see exact active-scope log paths, file size, modified time, file role, empty-file hint, and copyable `tail -n 50 -F` commands without changing runtime state.
- OBS-OS1 adds a lower-priority Daily Review / Anomaly Flags panel. It loads `reports/paper_reviews/pt_rt1_6_week2_active/latest_review.json` when generated by `scripts/build_pt_rt_week2_daily_review.py`, surfaces go/no-go, process/file freshness, decision/trade/lifecycle counts, synthetic/testnet boundary status, and top anomaly flags, and otherwise shows an explicit generate-command empty state. It is deliberately below the Paper Trading blotter so anomaly review is available without pushing Runtime Control or Testnet Order Transport down the right rail.
- The sticky dashboard top bar carries the logo, title, theme selector, and five primary tabs in founder-review order: Paper Trading, Historical Replay, Evidence, The Lab, Strategy. Paper Trading maps to the underlying Paper Observation runtime panel. Manual JSON loading and the visible evidence-pack-loaded status text are intentionally removed from the founder chrome; Codex/repo artifacts manage local report loading.
- Paper Trading decision-log stats are operational health signals only. Compact logging suppresses repeated non-actionable rows, but dashboard log-size warnings are not strategy evidence.
- Closed Synthetic Trades displays ledger-complete synthetic trade rows only. Sparse `paper_closed` decision rows remain useful audit context but should not be shown as n/a trade rows in the Closed Synthetic Trades table.
- Dashboard output does not submit orders, call private/signed/order endpoints, import candles, or regenerate evidence packs.

## Known UI Limitations

- Local ignored chart-data files must exist for full candle/indicator/trade visualization.
- Missing overlay timestamps are shown as unavailable states, not guessed.
- Historical Replay strategy rows are evidence/research-only unless a later approved phase changes status.
