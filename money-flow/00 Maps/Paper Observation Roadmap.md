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

Current PT-RT1.1C status: `runtime_collection_started`.

This means the repo now has code, dashboard, public-mainnet connector, runtime command, summary JSON, tests, and runbooks for controlled forward observation across the expanded 10-lane lab. The first 24-hour probes-disabled run is active as PID `11158`, expected to end `2026-05-15T21:57:58Z`, and is writing ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`. No 60-day observation result exists. It is not enough to approve production rules, paper runtime strategy authority, or live trading. PT-RT1.2 testnet plumbing probes remain blocked until the probes-disabled dry run passes.
