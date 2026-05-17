# PT-RT1 Real-Time Paper Observation + Testnet Plumbing

## Summary

Status: implemented

PT-RT1.4 makes Paper Trading the weekly founder command center and cuts active Week 1 paper-observation scoring to `1h`, `4h`, and `1d`. The `15m` timeframe is paused as `disabled_for_week1_noise_reduction`; existing 15m records remain visible as paused/legacy data but are excluded from active weekly scoring and new synthetic entries after the cutover. See `docs/pt_rt1_4_paper_trading_command_center_cleanup.md`.

PT-RT1.1C starts the 24-hour probes-disabled runtime collection after PT-RT1.1B public-mainnet readiness. The active collection uses the public-read-only `/info` connector, writes ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`, keeps testnet probes disabled and kill-switched, and defers evaluation to PT-RT1.1D after completion.

PT-RT1.1B connected the expanded lab to Hyperliquid public mainnet market data for readiness smoke validation. The public-read-only `/info` connector uses only `https://api.hyperliquid.xyz/info` public-read payloads, the runtime command writes ignored artifacts under `reports/paper_runtime/`, and the dashboard now prefers PT-RT1.1C/PT-RT1.1B runtime summaries when present.

PT-RT1.1A expanded the lab before the 24-hour dry run: the Paper Observation runtime now exposes 10 independent synthetic strategy lanes, an expanded requested scanner universe, requested/resolved symbol handling, blocked-symbol reason codes, and wildcard expert hypothesis diagnostics.

PT-RT1 adds the foundation for a 60-day forward-observation system. It is not a backtest and it does not approve any strategy for production, paper-runtime promotion, live trading, or real-capital execution.

The implementation has two separate lanes:

| Lane | Status | Purpose | Strategy PnL truth |
|---|---:|---|---|
| Strategy Truth Lane | implemented | Public-mainnet market data, closed-candle gating, indicators, synthetic paper decisions, independent 10,000 USDC paper ledgers | Hyperliquid public mainnet market data only |
| Testnet Plumbing Lane | implemented | Gated, capped, post-only Hyperliquid testnet probes for account targeting, precision, cancel/reconcile, and audit logging | Never |

## Non-Goals

- Production Money Flow v1.2 rules are unchanged.
- No strategy is production-approved.
- No paper runtime is approved as production behavior.
- No live trading is approved.
- No live exchange orders are submitted.
- The strategy-truth lane does not call private, signed, account-state, or order endpoints.
- Hyperliquid testnet prices and testnet fills are not strategy truth.
- Historical evidence packs were not regenerated.
- No SOR, fanout, CBBO, or cross-venue routing was added.

## Strategy Truth Lane

Status: implemented and smoke-verified in PT-RT1.1B

The strategy-truth lane uses public Hyperliquid mainnet `/info` payloads only. Allowed public info types are:

| Info type | Use |
|---|---|
| `meta` | market identity and precision metadata |
| `metaAndAssetCtxs` | public market context |
| `allMids` | mark/mid updates for unrealized PnL |
| `candleSnapshot` | fully closed candle inputs |
| `fundingHistory` | display/review context |
| `l2Book` | display context only |

Forbidden for strategy truth:

- `clearinghouseState`
- `spotClearinghouseState`
- `openOrders`
- `orderStatus`
- `userFills`
- API keys
- private/signed endpoints
- order endpoints
- Hyperliquid testnet prices

If public mainnet data is stale, degraded, or unavailable, the strategy-truth lane blocks new synthetic paper entries and records reason codes.

PT-RT1.1B adds `services/paper_runtime/hyperliquid_public_market_data.py` and `scripts/run_pt_rt1_paper_observation.py`. A bounded smoke run connected to public mainnet `meta` and `allMids`, resolved the expanded watchlist, loaded public `candleSnapshot` rows for a bounded sample, and recorded paper decision events without enabling probes or submitting orders. PT-RT1.1C then starts the 24-hour probes-disabled collection using the same public-mainnet-only runtime path.

## Top-20 Scanner

Status: implemented

The scanner resolver accepts a public top-20 symbol list and filters it against Hyperliquid public mainnet perpetual metadata and public market-data health.

Required output fields are represented:

- requested symbol
- resolved venue symbol
- asset id
- `szDecimals`
- precision status
- venue support status
- data health
- scanner eligibility
- reason codes

SHIB/kSHIB remains excluded unless unit semantics are explicitly resolved:

`venue_symbol_unit_semantics_deferred`

## Lane Definitions

Status: implemented

Each lane starts with synthetic 10,000 USDC and compounds realized PnL forward. PT-RT1.1A expands the lane set to exactly 10 lanes with independent ledgers. These are not one combined account.

| Lane | Role | Status |
|---|---|---|
| `money_flow_v1_2_baseline` | control lane | production-derived rules unchanged; not approval |
| `avoid_low_rolling_range_20` | evidence-only candidate lane | not production-approved |
| `avoid_low_rolling_range_50` | evidence-only candidate lane | not production-approved |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG evidence-only reference lane | not production-approved |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG evidence-only reference lane | not production-approved |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG evidence-only reference lane | not production-approved |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG evidence-only reference lane | not production-approved |
| `wildcard_btc_regime_guard` | wildcard expert hypothesis lane | not production-approved |
| `wildcard_multi_timeframe_alignment` | wildcard expert hypothesis lane | not production-approved |
| `wildcard_volatility_expansion_breakout` | wildcard expert hypothesis lane | not production-approved |

The MF-ORIG lanes remain reference observation lanes. Wildcard lanes are expert hypotheses for forward observation only. None are production rules.

## PT-RT1.1A Expanded Scanner Universe

Status: implemented

PT-RT1.1A represents canonical SV2.0.2 symbols plus founder-requested additions before runtime collection:

`BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, PEPE, OKB`

Post-PT-RT1.3 runtime note: `TRUMP` is deferred from fresh paper-observation scanner runs because it created excessive runtime noise. This does not rewrite historical SV2.1 evidence artifacts that already included TRUMP.

Alias and blocked-symbol policy:

- `TRON -> TRX`.
- `PEPE -> kPEPE`, blocked by default with `pepe_kpepe_unit_semantics_deferred`.
- `OKB` is blocked unless public Hyperliquid metadata confirms active support.
- `POL` must resolve to active `POL`; delisted `MATIC` mapping is blocked.
- `SHIB/kSHIB` remains deferred.

## Paper-Equity Model

Status: implemented

Policy:

- `starting_equity = 10000 USDC` per lane.
- `realized_equity` compounds after every closed trade.
- `unrealized_pnl` updates from public mainnet market data.
- `total_equity = realized_equity + unrealized_pnl`.
- Sizing basis is current realized synthetic equity.
- Default fill model is `next_candle_open`.
- `next_candle_close` can be tracked as comparison metadata.
- Same-candle optimistic fills are not used.
- Runtime state is local/ignored under `reports/paper_runtime/`.

Runtime state paths:

| State | Path |
|---|---|
| State snapshot | `reports/paper_runtime/pt_rt1_state.json` |
| Decisions | `reports/paper_runtime/pt_rt1_decisions.jsonl` |
| Trades | `reports/paper_runtime/pt_rt1_trades.jsonl` |
| Equity curves | `reports/paper_runtime/pt_rt1_equity_curves.json` |
| Data health | `reports/paper_runtime/pt_rt1_data_health.json` |
| Testnet probe audit | `reports/paper_runtime/pt_rt1_testnet_probe_audit.jsonl` |

These runtime files are ignored and must not be committed.

## Fully Closed Candle Gating

Status: implemented

The runtime computes canonical candle close times from timeframe duration and blocks:

- `candle_not_closed`
- `duplicate_candle_ignored`
- `missing_candle_gap_detected`
- `out_of_order_candle`
- `insufficient_history`
- `indicator_unavailable`
- `public_market_data_unavailable`

## Indicator Model

Status: implemented

Implemented indicators:

- EMA5
- EMA10
- SMA20
- RSI14
- MACD 12/26/9
- MACD signal
- MACD histogram
- ATR14
- SMA50
- SMA200
- rolling range 20
- rolling range 50

Missing indicators are invalid input and do not default to zero. Missing fields produce explicit reason codes such as `missing_indicator_field`, `missing_ema5`, `missing_sma20`, `missing_rsi`, `missing_macd`, `missing_macd_signal`, `missing_macd_histogram`, and `insufficient_history`.

## Duplicate Prevention

Status: implemented

Duplicate synthetic signals are blocked with key:

`lane_id | strategy_id | symbol | timeframe | signal_candle_time | action`

Duplicate attempts produce:

`duplicate_ignored`

## Testnet Probe Gates

Status: implemented

Testnet probes are disabled by default and fail closed.

Default policy:

| Setting | Default |
|---|---:|
| `PT_RT1_TESTNET_PROBES_ENABLED` | `false` |
| `PT_RT1_TESTNET_DAILY_PROBE_CAP` | `1` |
| `PT_RT1_TESTNET_PROBE_NOTIONAL_CAP` | `10 USDC` |
| `PT_RT1_TESTNET_KILL_SWITCH` | `true` |

Exact approval text required:

```text
I APPROVE PT-RT1 TESTNET PLUMBING PROBES ONLY. HYPERLIQUID TESTNET ONLY. POST-ONLY UNDER 10 USDC DEFAULT NOTIONAL. CANCEL/RECONCILE REQUIRED. TESTNET FILLS MUST NOT UPDATE STRATEGY PAPER PNL. LIVE TRADING IS NOT APPROVED.
```

Probe eligibility requires:

- exact approval text
- testnet endpoint only
- no live endpoint
- resolved account targeting
- precision validation
- scanner-eligible signal
- daily cap available
- kill switch off
- notional under cap
- post-only `Alo`
- submit lease acquired
- testnet-only artifact label
- no unknown/open probe state

Accepted/open probes require immediate cancel/reconcile. Unknown probe state blocks future probes until reconciled.

## Account Targeting

Status: implemented

Account-targeting truth:

- main/user mode omits `vaultAddress`.
- subaccount/vault mode includes `vaultAddress` only when explicit and valid.
- normal main wallet plus `vaultAddress` is blocked.

This preserves the prior Hyperliquid UAT lesson that sending a main account as `vaultAddress` causes false “vault not registered” failures.

## Dashboard Status

Status: implemented and updated through the Paper Observation live-display follow-up

The dashboard adds a visible Paper Observation view with:

- public-mainnet connection status
- endpoint category `public_read_only`
- top-20 scanner state
- market data health
- strategy lane comparison
- ticking public-mainnet watchlist mids from browser-side `allMids`
- selected-pair TradingView chart from public-mainnet `candleSnapshot`
- open synthetic positions
- closed synthetic trades
- drawdown / losing streaks
- separate testnet plumbing probe status

The dashboard loads ignored runtime summaries from `reports/paper_runtime/pt_rt1_1c_24h_dry_run/summary.json` or `reports/paper_runtime/pt_rt1_1b_smoke/summary.json` when present, then falls back to committed PT-RT1.1B and base PT-RT1 summaries.

Dashboard filters are display-only:

`display-only filter`

`not canonical evidence`

`not backend replay`

## Runbooks

Status: implemented

Created:

- `docs/pt_rt1_24h_dry_run_probes_disabled.md`
- `docs/pt_rt1_24h_testnet_plumbing_probe_run.md`
- `docs/pt_rt1_60_day_forward_observation_plan.md`

## PT-RT1.1 Dry-Run Validation

Status: blocked

PT-RT1.1 checked for the first 24-hour probes-disabled runtime artifact set at:

`reports/paper_runtime/pt_rt1_1_24h_dry_run/`

That artifact directory does not exist, so the committed PT-RT1.1 report does not claim that public mainnet refresh, fully closed candle gating, synthetic paper ledgers, duplicate prevention, data-health gating, or dashboard runtime behavior passed.

Current decision:

`PT-RT1.2 blocked`

PT-RT1.2 may proceed only after the actual 24-hour probes-disabled dry run creates ignored runtime artifacts and the PT-RT1.1 report/summary are regenerated from those artifacts.

## Limitations

Status: needs_followup

- PT-RT1 implements the runtime substrate and dashboard surface; the 24-hour probes-disabled dry run and 60-day observation have not completed.
- The strategy-truth lane must be run in a supervised environment before founder review relies on live forward-observation rows.
- Testnet probes remain blocked until the exact approval text is captured and the kill switch is explicitly disabled.
- Paper observation is not production approval, paper-runtime approval, live approval, or real-capital readiness.

## Next Phase Recommendation

Status: deferred

Run the 24-hour dry run with probes disabled first. If public-mainnet data health, closed-candle gating, duplicate prevention, and paper ledgers are stable, start the 60-day forward-observation window. Testnet plumbing probes should remain separate and only run after exact approval.
