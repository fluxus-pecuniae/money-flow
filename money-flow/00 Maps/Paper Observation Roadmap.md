# Paper Observation Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the roadmap and current status note for PT-RT1. It is not production approval, strategy paper-runtime approval, or live-trading approval.

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
- founder-requested symbols: TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, TRUMP, PEPE, OKB
- aliases: TRON resolves to TRX; PEPE resolves to kPEPE
- blocked by default: PEPE/kPEPE unit semantics, SHIB/kSHIB unit semantics, OKB unless active Hyperliquid support is confirmed, delisted MATIC when POL is requested
- blocked symbols remain visible with reason codes

PT-RT1.1B public-mainnet readiness:

- Public connector exists at `services/paper_runtime/hyperliquid_public_market_data.py`.
- Runtime command exists at `scripts/run_pt_rt1_paper_observation.py`.
- Smoke output is ignored under `reports/paper_runtime/pt_rt1_1b_smoke/`.
- Smoke connected to public mainnet `meta` and `allMids`, resolved the requested watchlist, loaded bounded candle data, and recorded bounded paper decisions.
- Testnet probes stayed disabled and kill-switched.

Paper Observation dashboard live display:

- Browser-side watchlist polling calls Hyperliquid public mainnet `allMids` every 1 second.
- The visible watchlist is intentionally compact: `Symbol`, `Mid price`, and `Health`.
- Watchlist health is `unhealthy` when the latest market-data tick is missing or stale for more than 2 minutes.
- The selected pair/timeframe chart uses public mainnet `candleSnapshot`.
- The adjacent Signal Generation panel lists recorded synthetic `paper_opened` intended-entry decisions from the PT-RT1 decision stream.
- The local Start Run / Stop Run panel is available only when the dashboard is served by `scripts/run_dashboard_control_server.py`; it launches allowlisted probes-disabled public-mainnet sessions through Mac `caffeinate` and always forces `--disable-testnet-probes` plus `--public-mainnet-only`.
- Runtime decision logging now defaults to compact mode. It writes actionable `paper_opened`/`paper_closed` decisions, data-unavailable rows, and first-seen non-actionable audit rows while suppressing repeated identical non-actionable rows across cycles; `full_audit` remains an explicit short-diagnostic CLI mode.
- The dashboard displays decision-log mode, log size, rows written this cycle, and repeated rows suppressed this cycle from runtime summaries.
- Static `http.server` dashboard review still works, but runtime Start/Stop controls intentionally show unavailable there.
- This browser display path remains public-read-only and adds no order controls, private/signed/order/account payloads, API keys, testnet strategy truth, or paper/live approval.

Current next operational step:

1. Let the active `PT-RT1.1C` 24-hour dry run finish with testnet probes disabled.
2. Retain ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`.
3. Evaluate those artifacts in `PT-RT1.1D`.
4. If stable, start the 60-day public-mainnet forward-observation window.
5. Run testnet plumbing probes only after PT-RT1.1C/PT-RT1.1D pass, exact approval is captured, and strategy PnL separation remains intact.

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

## Testnet Plumbing Probe Policy

Testnet probes are implemented but blocked by default:

- `PT_RT1_TESTNET_PROBES_ENABLED=false`
- `PT_RT1_TESTNET_KILL_SWITCH=true`
- daily cap defaults to `1`
- notional cap defaults to under `10 USDC`
- exact approval text is required
- post-only `Alo` shape only
- cancel/reconcile required
- unknown/open probe state blocks future probes
- testnet fills never update strategy paper PnL

## Readiness Decision

Current PT-RT1 status: `implemented_substrate_observation_not_started`.

Current PT-RT1.1 status: `blocked_missing_24h_runtime_artifacts`.

Current PT-RT1.1A status: `implemented_expanded_readiness`.

Current PT-RT1.1B status: `implemented_public_mainnet_runtime_readiness_smoke_verified`.

Current PT-RT1.1C status: `runtime_artifacts_present_pending_evaluation`.

This means the repo now has code, dashboard, public-mainnet connector, runtime command, summary JSON, tests, and runbooks for controlled forward observation across the expanded 10-lane lab. The local PT-RT1.1C artifact set under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` currently contains about 479k paper decision rows, 0 trade rows, and latest summary timestamp `2026-05-15T22:22:12Z`. It is not an always-on hosted service: new signal generation requires manually starting `scripts/run_pt_rt1_paper_observation.py` and keeping that process and machine awake/networked for the chosen session. The Paper Observation dashboard also browser-polls Hyperliquid public mainnet `allMids` for a ticking symbol/mid/health watchlist and selected-pair `candleSnapshot` for a live TradingView chart, with Signal Generation showing recorded `paper_opened` intended-entry decisions. No 60-day observation result exists. It is not enough to approve production rules, paper runtime strategy authority, or live trading. PT-RT1.2 testnet plumbing probes remain blocked until the probes-disabled dry run passes.
