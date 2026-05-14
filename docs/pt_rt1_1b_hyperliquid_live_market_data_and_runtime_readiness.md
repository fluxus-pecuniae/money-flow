# PT-RT1.1B Hyperliquid Live Market Data And Runtime Readiness

Status: implemented

PT-RT1.1B connects the expanded PT-RT1 paper-observation runtime to Hyperliquid public mainnet market data and prepares the 10-lane forward-observation lab for the next probes-disabled 24-hour collection. This phase is readiness and smoke validation only. It did not start the 24-hour run.

## Objective

Status: implemented

PT-RT1.1B verifies that the runtime can use Hyperliquid public mainnet `/info` data as strategy truth, resolve the expanded requested watchlist, evaluate paper-only strategy lanes from fully closed public candles, write ignored runtime artifacts, and expose readiness in the dashboard.

## Public Mainnet Data Connector

Status: verified

The connector lives at `services/paper_runtime/hyperliquid_public_market_data.py`.

Policy:

- Strategy truth endpoint: `https://api.hyperliquid.xyz/info`.
- Endpoint category: `public_read_only`.
- Allowed public info payloads: `meta`, `metaAndAssetCtxs`, `allMids`, `candleSnapshot`, `fundingHistory`, and display-only `l2Book`.
- Rejected for strategy truth: testnet URL, private/signed/order/account payloads, account state, open orders, order status, user fills, and API-key headers.
- Candle snapshots are normalized into open/close timestamps, OHLC validation, data-health status, and reason codes.

Smoke status:

- `meta`: `public_mainnet_data_connected`.
- `allMids`: `public_mainnet_data_connected`.
- Latest smoke artifact path: `reports/paper_runtime/pt_rt1_1b_smoke/summary.json` (ignored local runtime artifact).

## Watchlist Resolution

Status: verified

The runtime resolved the PT-RT1.1A requested universe from public mainnet metadata and mids during the smoke cycle.

Smoke result:

| Metric | Value |
| --- | ---: |
| Requested symbols | 25 |
| Resolved rows | 25 |
| Scanner-eligible rows | 23 |
| Blocked rows | 2 |

Blocked/deferred symbol policy remains visible:

- `PEPE -> kPEPE` is blocked by unit-semantics review.
- `OKB` is blocked unless active Hyperliquid public metadata support is confirmed.
- `SHIB/kSHIB` remains deferred outside the requested runtime universe.
- `POL` must resolve to active `POL`; delisted `MATIC` mapping is blocked.

## Ten Strategy Lanes

Status: verified

The runtime keeps the PT-RT1.1A 10-lane set active and independent:

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

Each lane remains synthetic paper only, starts at `10000 USDC`, compounds realized PnL forward, and is not one combined account.

## Wildcard Lane Readiness

Status: implemented

Wildcard lanes emit explicit reason codes:

- `wildcard_btc_regime_guard`: `btc_regime_guard_passed`, `btc_regime_guard_blocked_bearish`, `btc_regime_context_unavailable`, `btc_regime_clear_bearish_alignment`, `btc_regime_macd_histogram_not_constructive`.
- `wildcard_multi_timeframe_alignment`: `multi_timeframe_alignment_passed`, `multi_timeframe_alignment_blocked`, `higher_timeframe_context_unavailable`, `higher_timeframe_bearish_alignment`, `higher_timeframe_macd_not_constructive`.
- `wildcard_volatility_expansion_breakout`: `volatility_expansion_breakout_passed`, `volatility_expansion_blocked_low_range`, `volatility_expansion_missing_compression_context`, `volatility_expansion_no_recent_high_breakout`, `volatility_expansion_baseline_alignment_failed`.

They remain expert hypotheses for forward observation only.

## Paper Ledger Readiness

Status: implemented

Paper ledger policy is unchanged:

- `starting_equity = 10000 USDC` per lane.
- `total_equity = realized_equity + unrealized_pnl`.
- Closed trade net PnL changes realized equity.
- Open position PnL changes unrealized PnL.
- Equity does not reset after trades.
- Duplicate signal key: `lane_id | strategy_id | symbol | timeframe | signal_candle_close_time | action`.

The smoke cycle recorded 80 paper decision events across the bounded sample and created no production execution artifacts.

## Dashboard Status

Status: implemented

The Paper Observation dashboard now loads PT-RT1.1B/runtime summaries before the base PT-RT1 summary and shows:

- connection status;
- public-read-only endpoint category;
- expanded requested/resolved watchlist;
- blocked symbols and reason codes;
- all 10 strategy lanes;
- lane detail;
- wildcard diagnostics;
- public-mainnet candle summary when runtime candles exist;
- separate testnet plumbing readiness.

Dashboard filters remain display-only and do not mutate runtime ledgers.

## Testnet Plumbing Readiness

Status: verified

Testnet probes remain prepared but disabled:

- `PT_RT1_TESTNET_PROBES_ENABLED=false`.
- `PT_RT1_TESTNET_KILL_SWITCH=true`.
- Exact approval is required before any future probe phase.
- Post-only, notional cap, daily cap, cancel/reconcile, and blocked-symbol gates remain documented.
- Testnet fills do not update strategy paper PnL.

No testnet orders were submitted in PT-RT1.1B.

## Runtime Command

Status: implemented

24-hour command:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_1b_24h_dry_run \
  --disable-testnet-probes \
  --public-mainnet-only
```

Smoke command:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-minutes 1 \
  --output-dir reports/paper_runtime/pt_rt1_1b_smoke \
  --disable-testnet-probes \
  --public-mainnet-only
```

The runner fails closed if testnet probes are not disabled, public-mainnet-only mode is absent, or the output path is outside ignored `reports/paper_runtime/`.

## Smoke Run

Status: verified

Executed bounded smoke:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-minutes 1 \
  --output-dir reports/paper_runtime/pt_rt1_1b_smoke \
  --disable-testnet-probes \
  --public-mainnet-only \
  --max-cycles 1 \
  --max-candle-symbols 2
```

Result:

- Public mainnet fetch attempted: yes.
- Public mainnet connected: yes.
- Watchlist resolved: yes.
- Decisions recorded: 80.
- Latest chart sample: BTC `15m`, 120 closed candles.
- Testnet probes enabled: false.
- Orders submitted: false.
- Private/signed/order endpoints called: false.

## Limitations

Status: needs_followup

- The smoke run is not the required 24-hour collection.
- The 24-hour run must run long enough to verify duplicate prevention, data-health gating, ledger state changes, dashboard readability, and paper position/trade rows over time.
- Runtime artifacts remain ignored and uncommitted by design.
- No production strategy conclusion follows from PT-RT1.1B.

## PT-RT1.1C Go / No-Go

Status: verified

Decision: `PT-RT1.1C may start 24-hour probes-disabled runtime collection`.

PT-RT1.1C remains probes-disabled paper observation only. PT-RT1.2 testnet probes remain blocked until a real probes-disabled run passes.

## No-Order / No-Live Confirmation

Status: verified

No production Money Flow rules changed. No canonical historical evidence packs were regenerated. No live or testnet orders were submitted. Testnet probes remain disabled. No private/signed/order endpoints were called from the strategy-truth lane. No API keys were used for strategy truth. No testnet prices or fills were used as strategy PnL truth. No live trading, production paper runtime, SOR/fanout/CBBO, or real-capital behavior was approved.
