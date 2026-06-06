# Dashboard and UI Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This note explains current founder-facing dashboard surfaces and what each surface can and cannot prove.

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime config: `PT-RT1.6` founder-selected Week 2 slate is prepared; no active paper run is assumed unless the local control server reports one.
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
| Audit | EV-AUDIT1 summary JSON | Audit verdict, methodology/data confidence, issues, paper-readiness status | Do not treat audit display as strategy approval |
| Strategy | Static strategy/config summaries | Understand Money Flow v1.2 and variant ideas at a high level | Do not infer production approval |

## Current Hidden / Legacy Surfaces

The old `Experiments` tab must not be promoted as current truth. Legacy UAT surfaces may remain hidden for regression and historical context, but they should not compete with current Strategy / Historical Replay / Evidence / Evidence Lab / Audit Review flows.

## Canonical vs Display-Only

- Canonical evidence lives in backend-generated evidence packs and committed founder-readable reports.
- Historical Replay chart JSON is visualization-only.
- Evidence Lab overlays are visualization-only.
- Date filters are display-only. Dashboard date filters are display-only recalculations.
- The Paper Trading view is chart-first as of PT-RT1.2.1 and has a cleaner cockpit presentation: compact safety strip, tighter Start Run command card, global filter toolbar, larger primary chart, normalized panel spacing, and consistent summary cards. The underlying view id remains `paper-observation`, but current founder-facing language is Paper Trading. The visible watchlist/scanner panel is removed; Symbol/Timeframe/Strategy filters drive the live chart context, opened/closed markers, Signal Generator, and open/closed synthetic tables; Open Synthetic Positions and Closed Synthetic Trades sit directly below Signal Generator; Closed Synthetic Trades loads ignored `trades.jsonl` for entry/exit/price/quantity/PnL/equity fields; Strategy Lane Comparison overlays `paper_runtime_state.realized_equity_by_lane` so runtime ledgers do not appear stuck at starting equity; wildcard diagnostics live in the Strategy tab as observation-only context.
- The Paper Trading Start Run helper is local runtime ergonomics only; it now defaults to the PT-RT1.6 Week 2 scope, public mainnet strategy truth, compact decision logging, candle-close signal evaluation, warm-start fresh-signal gating, disabled legacy probes, and baseline-only fixed 25 USDC testnet transport gates. Candidate/MF-ORIG/wildcard lanes cannot send testnet orders, and testnet fills do not update strategy paper PnL.
- The sticky dashboard top bar now carries the logo, title, theme selector, and six primary tabs in founder-review order: Paper Trading, Historical Replay, Evidence, The Lab, Audit, Strategy. Paper Trading maps to the underlying Paper Observation runtime panel. Manual JSON loading and the visible evidence-pack-loaded status text are intentionally removed from the founder chrome; Codex/repo artifacts manage local report loading.
- Paper Trading decision-log stats are operational health signals only. Compact logging suppresses repeated non-actionable rows, but dashboard log-size warnings are not strategy evidence.
- Closed Synthetic Trades displays ledger-complete synthetic trade rows only. Sparse `paper_closed` decision rows remain useful audit context but should not be shown as n/a trade rows in the Closed Synthetic Trades table.
- Dashboard output does not submit orders, call private/signed/order endpoints, import candles, or regenerate evidence packs.

## Known UI Limitations

- Local ignored chart-data files must exist for full candle/indicator/trade visualization.
- Missing overlay timestamps are shown as unavailable states, not guessed.
- Historical Replay strategy rows are evidence/research-only unless a later approved phase changes status.
