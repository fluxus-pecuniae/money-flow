# Paper Trading / PT-RT Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the roadmap and current status note for PT-RT1. The founder-facing dashboard tab is `Paper Trading`; the underlying runtime and code may still use Paper Observation / `paper-observation` names. This is not production approval, strategy paper-runtime approval, or live-trading approval.

## PT-RT1 Implemented Scope

PT-RT1 is implemented as a forward-observation substrate:

- public Hyperliquid mainnet market data as strategy truth
- fully closed candle detection
- real-time indicator computation
- paper-only strategy decisions
- independent internal 10,000 USDC paper ledgers per lane
- realized and unrealized PnL
- drawdown tracking
- entry/exit arrows on UI charts
- signal/event audit log
- duplicate signal prevention
- data outage handling
- founder review workflow

Required observation lanes after PT-RT1.1A:

- `money_flow_v1_2_baseline`
- `avoid_low_rolling_range_20`
- `avoid_low_rolling_range_50`
- `mf_orig_stage_filter_only_full_equity`
- `mf_orig_stage2_pullback_reclaim_full_equity`
- `mf_orig_1d_stage2_5_20_crossover_full_equity`
- `mf_orig_1d_stage2_breakout_resistance_full_equity`
- `wildcard_btc_regime_guard`
- `wildcard_multi_timeframe_alignment`
- `wildcard_volatility_expansion_breakout`

PT-RT1.1A scanner expansion:

- canonical symbols: BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX
- founder-requested symbols: TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, PEPE, OKB
- deferred from fresh PT-RT runtime scanner: TRUMP (`runtime_noise_deferred_by_founder`)
- aliases: TRON resolves to TRX; PEPE resolves to kPEPE
- blocked by default: PEPE/kPEPE unit semantics, SHIB/kSHIB unit semantics, OKB unless active Hyperliquid support is confirmed, delisted MATIC when POL is requested
- blocked symbols remain visible with reason codes

PT-RT1.1B public-mainnet readiness:

- Public connector exists at `services/paper_runtime/hyperliquid_public_market_data.py`.
- Runtime command exists at `scripts/run_pt_rt1_paper_observation.py`.
- Smoke output is ignored under `reports/paper_runtime/pt_rt1_1b_smoke/`.
- Smoke connected to public mainnet `meta` and `allMids`, resolved the requested watchlist, loaded bounded candle data, and recorded bounded paper decisions.
- The older dashboard-started 20 USDC audit/order-shape mode is historical context. PT-RT1.5 supersedes the active Week 1 surface with baseline-only fixed 25 USDC testnet lifecycle gates.

PT-RT1.2 runtime correctness:

- `state.json` now persists processed signal keys, open synthetic positions, realized equity by lane, and last processed close by lane/symbol/timeframe.
- Repeated same-candle `paper_opened` attempts are held/blocked instead of written as new opens.
- Synthetic closes append to `trades.jsonl` when an open position exists and exit conditions occur.
- `summary.json` separates unavailable public market-data rows from lane-expanded `data_unavailable` decisions.
- The dashboard surfaces open positions, duplicate-open blocks, market-row unavailable counts, lane-expanded unavailable counts, transport mode, submit/cancel/reconcile counts, and the synthetic public-mainnet paper PnL source.

PT-RT1.3 candle-truth data health:

- Hyperliquid `meta` and precision determine scanner eligibility; missing or stale `allMids` no longer blocks supported pairs by itself.
- Clean fully closed public-mainnet `candleSnapshot` rows are the strategy-readiness gate.
- Stale/thin/missing/nonpositive mids are visible as warning-only labels such as `mid_stale_or_thin_tick` and `mid_unavailable_but_candles_available`.
- Missing, malformed, or degraded candles and insufficient indicators remain blocking `data_unavailable` conditions.

PT-RT1.4 active weekly command-center cutover:

- Active Week 1 paper timeframes are `1h`, `4h`, and `1d`.
- `15m` is `disabled_for_week1_noise_reduction`.
- New 15m synthetic entries are blocked after the cutover.
- Existing 15m records are not deleted; they remain visible under paused/legacy review and are excluded from active weekly scoring.
- Strategy Lane Comparison defaults to selected timeframe only (`1h`).
- All-active mode is explicitly `1h + 4h + 1d`, excludes 15m, and is not one combined account.
- Signal Generator is now a categorized paper-decision stream.
- Testnet status separates audit-only shape generation from actual signed testnet order transport.

PT-RT1.4.1 active-week runtime verification:

- Cutover timestamp: `2026-05-17T09:47:55Z`.
- The older `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` runtime kept producing 15m opens after cutover and is now labeled `pre_pt_rt1_4_weekend_burn_in`.
- The old runtime is excluded from active Week 1 scoring.
- A restarted active runtime writes ignored artifacts under `reports/paper_runtime/pt_rt1_4_1_active_week/`.
- First active runtime artifact cycle: active `1h`/`4h`/`1d`, disabled `15m`, 0 15m rows, 0 15m opens.
- Daily founder review pack: `docs/pt_rt_week1_day_summary.md` and `docs/pt_rt_week1_day_summary.json`.
- Current decision: `Week 1 paper observation may continue`.

PT-RT1.5 active-week reset, candle scheduler, and baseline-only testnet lifecycle:

- Active Week 1 default scope is now `pt_rt1_5_week1_active`.
- Prior runtime rows are archived, not deleted, and hidden by default unless the founder enables archived/weekend burn-in review.
- Fresh active-week ledgers start at 10,000 USDC per lane for default review.
- Active paper timeframes remain `1h`, `4h`, and `1d`; `15m` remains paused and cannot create new active-week synthetic opens or testnet lifecycle rows.
- Market-data refresh remains frequent for watchlist, chart, data-health, heartbeat, and unrealized-PnL display.
- Strategy signal evaluation is candle-close only for fully closed `1h`, `4h`, and `1d` candles with grace delays of 90, 120, and 180 seconds.
- Between scheduled candle-close evaluations the runtime records market-refresh/no-signal reasons instead of repeatedly scanning entries/exits.
- Only scheduled `money_flow_v1_2_baseline` `paper_opened` rows on active timeframes can create baseline-linked Hyperliquid testnet lifecycle rows.
- Testnet lifecycle rows use fixed 25 USDC notional, independent of synthetic signal size.
- Candidate, MF-ORIG, wildcard, 15m, duplicate, data-unavailable, hold, close, and trim rows cannot send testnet orders.
- Public mainnet candles remain strategy truth; testnet prices are formatting-only for testnet plumbing; testnet fills never update synthetic PnL.
- Runtime artifacts stay ignored under `reports/paper_runtime/pt_rt1_5_week1_active/`.

Paper Trading dashboard live display:

- Browser-side health polling can still call Hyperliquid public mainnet `allMids`, but the visible Expanded Scanner Universe/watchlist is removed from the founder Paper Trading page as of PT-RT1.2.1.
- The founder page now uses a weekly command-center layout: top health banner, timeframe-scoped Weekly Scoreboard, Timeframe Breakdown, selected-pair public-mainnet chart, Open Synthetic Positions, Closed Synthetic Trades, Signal / Decision Stream, and lower-priority data-health/testnet reference panels.
- The selected pair/timeframe chart uses public mainnet `candleSnapshot`; default chart timeframe follows the selected active timeframe rather than 15m.
- Opened and closed synthetic paper trades render as chart markers from runtime decisions/state/trades.
- Symbol, Timeframe, and Strategy lane controls apply to the chart context, chart markers, Signal Generator, Open Synthetic Positions, and Closed Synthetic Trades. If Symbol or Timeframe is `All`, the chart chooses the newest matching paper signal/open context and otherwise preserves the prior chart target.
- Open Synthetic Positions and Closed Synthetic Trades are cleaned up with active/legacy status, PnL, reason, and fee/slippage context.
- Strategy Lane Comparison is the Weekly Scoreboard and sits near the top so lane review is scoped before the chart and trade tables.
- Closed Synthetic Trades loads ignored `trades.jsonl` rows for complete entry/exit/price/quantity/PnL/equity fields; `summary.json.closed_trades` may be empty even when the synthetic trade ledger has closed trades, and sparse `paper_closed` decision rows are filtered out instead of being shown as n/a trade rows.
- Strategy Lane Comparison overlays `paper_runtime_state.realized_equity_by_lane`, open-position counts, closed-trade counts, and derived net PnL onto static lane definitions so active runtime ledgers do not remain displayed at starting equity.
- Signal / Decision Stream, Open Synthetic Positions, and Closed Synthetic Trades are paginated; open-position default page size is 25 rows.
- Wildcard Diagnostics moved to the Strategy tab and remains observation-only/non-production.
- The adjacent Signal Generator panel lists recorded synthetic `paper_opened` intended-entry decisions from the PT-RT1 decision stream.
- The compact watchlist shows symbol, mid, health, and status only. It is scrollable and sits beside the Testnet Order Transport widget.
- The Testnet Order Transport widget now separates audit-only shape generation from baseline-only order transport, shows fixed 25 USDC notional, candidate-lane transport blocks, signed testnet order counts, lifecycle counts, and `strategy PnL update from testnet = false`.
- The Testnet Order Lifecycle table is separate from Closed Synthetic Trades.
- The dashboard shows next/last scheduled `1h`/`4h`/`1d` signal-evaluation times and labels Signal Evaluation as candle-close only.
- The local Start Run / Stop Run panel is available only when the dashboard is served by `scripts/run_dashboard_control_server.py`; it launches allowlisted public-mainnet sessions through Mac `caffeinate` and now defaults to `pt_rt1_5_week1_active`, `--disable-testnet-probes`, `--pt-rt1-5-week1-active`, `--signal-evaluation-mode candle_close_only`, `--enable-pt-rt1-5-baseline-testnet-orders`, fixed `--pt-rt1-5-testnet-order-notional-usdc 25`, and `--public-mainnet-only`.
- Runtime decision logging now defaults to compact mode. It writes actionable `paper_opened`/`paper_closed` decisions, data-unavailable rows, and first-seen non-actionable audit rows while suppressing repeated identical non-actionable rows across cycles; `full_audit` remains an explicit short-diagnostic CLI mode.
- The dashboard displays decision-log mode, log size, rows written this cycle, and repeated rows suppressed this cycle from runtime summaries.
- Static `http.server` dashboard review still works, but runtime Start/Stop controls intentionally show unavailable there.
- This browser display path remains public-read-only for strategy truth and adds no order controls, private/signed/order/account payloads, API keys, testnet strategy truth, or paper/live approval.

Current next operational step:

1. Start or restart the PT-RT1.5 active-week session scoped to `1h`, `4h`, and `1d`.
2. Retain ignored active artifacts under `reports/paper_runtime/pt_rt1_5_week1_active/`.
3. Use the Paper Trading tab as the weekly command center and keep archived/weekend burn-in rows hidden by default.
4. Review scheduler timing, duplicate closed-candle suppression, fixed-25 baseline-only testnet lifecycle rows, candidate transport blocks, and synthetic ledger isolation after the first active cycles.
5. If stable, continue the 60-day public-mainnet forward-observation window.

## Required Boundaries

- no exchange orders.
- No private/signed endpoints.
- No API keys.
- No live trading.
- No real capital.
- No production rule change.
- No SOR/fanout/CBBO/route executor behavior.

## UAT Sandbox vs Paper Observation

| Lane | Purpose | Data / Endpoint Truth |
| --- | --- | --- |
| UAT sandbox/testnet execution plumbing | Verify account targeting, order lifecycle, cancel/reconcile, route ledger | Hyperliquid testnet/sandbox; not strategy truth |
| Real-time paper observation | Observe strategy signals and paper PnL in current market conditions | Public mainnet market data should be strategy truth |

PT-RT1 should keep these lanes separate.

## Baseline Testnet Order Transport Policy

PT-RT1.5 testnet transport remains separate from strategy truth:

- public mainnet candles remain strategy truth
- only `money_flow_v1_2_baseline` scheduled `paper_opened` rows on `1h`/`4h`/`1d` are eligible
- candidate lanes, MF-ORIG lanes, wildcard lanes, `15m`, duplicate rows, data-unavailable rows, holds, trims, and closes cannot trigger testnet orders
- fixed testnet notional is `25 USDC`, independent of synthetic signal notional
- Hyperliquid testnet order shape is limit post-only `Alo`
- live Hyperliquid URLs are rejected
- main/user mode omits `vaultAddress`; subaccount/vault mode requires explicit valid `vaultAddress`
- duplicate testnet order keys are blocked
- unknown/open testnet state blocks new orders
- testnet lifecycle rows are separate from synthetic paper trades
- testnet fills never update strategy paper PnL
- no live trading or production strategy approval follows from the lifecycle rows

## Readiness Decision

Current PT-RT1 status: `implemented_forward_observation_substrate`.

Current PT-RT1.1 status: `historical_artifact_gate_superseded_by_runtime_followups`.

Current PT-RT1.1A status: `implemented_expanded_readiness`.

Current PT-RT1.1B status: `implemented_public_mainnet_runtime_readiness_smoke_verified`.

Current PT-RT1.1C status: `runtime_artifacts_present_pending_evaluation`.

Current PT-RT1.2 status: `implemented_runtime_state_and_transport_gates`.

Current PT-RT1.3 status: `implemented_candle_truth_data_health`.

Current PT-RT1.4 status: `implemented_paper_trading_command_center_and_active_timeframe_cutover`.

Current PT-RT1.4.1 status: `active_runtime_cutover_verified_after_restart`.

Current PT-RT1.5 status: `implemented_active_week_reset_candle_close_scheduler_and_baseline_testnet_lifecycle_gates`.

This means the repo now has code, dashboard, public-mainnet connector, runtime command, summary JSON, tests, runbooks, and a daily founder review pack for controlled forward observation across the expanded 10-lane lab. The old local PT-RT1.1C artifact set under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` is pre-cutover burn-in for active Week 1 because it kept generating 15m opens after cutover. The PT-RT1.4.1 active-week directory is now archived by default, and the PT-RT1.5 active Week 1 artifact directory is `reports/paper_runtime/pt_rt1_5_week1_active/`. It is not an always-on hosted service: new signal generation requires starting `scripts/run_pt_rt1_paper_observation.py` with PT-RT1.5 flags and keeping that process and machine awake/networked for the chosen session. No 60-day observation result exists. It is not enough to approve production rules, paper runtime strategy authority, or live trading.
