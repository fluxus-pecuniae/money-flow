# TREND-OVERLAY1 — Deployable Trend Drawdown-Control Overlay (signal only)

Read-only signal tool. No orders, no auto-execution, no private/signed
endpoints, no testnet/live trading, no production approval. The output is an
advisory number an operator may read.

## What this is

The TSMOM-EV1 finding — vol-targeted time-series momentum as **drawdown
control** (equal-weight buy-and-hold bear drawdown 66% vs overlay 17%, while
the overlay itself **lost 12.2% absolute** in that OOS window; authored
`mixed`, "defensive, not profitable") — operationalized as a forward
calculator on the latest fully-closed public-mainnet candles:

- `services/strategy_validation/trend_overlay1.py` — pure calculator that
  REUSES the exact TSMOM-EV1 machinery (`tsmom_signal`,
  `realized_vol_annual`, `target_weights` with the 0.40 weight cap and 1.5x
  gross cap) under the evidence run's train-chosen config
  (`tsmom_ev1_lb30_vt20_long_only_1d`). **Nothing re-derived, nothing
  re-tuned** — the defaults are pinned by test to the committed TSMOM-EV1
  summary.
- `scripts/run_trend_overlay.py` — CLI: fetches the latest daily candles for
  BTC/ETH/SOL/XRP/DOGE/BNB/SUI/AVAX from Hyperliquid public mainnet
  `candleSnapshot` (read-only, no keys — the same endpoint the dashboard
  already polls), drops the in-progress candle, prints the signal table, and
  writes `reports/trend_overlay/current_trend_overlay.json` (ignored runtime
  artifact). `--input-json` replays a saved payload offline (no network);
  `--account-size` scales the target exposure (default 10,000 USDC).

## The honest framing (in every output)

> DRAWDOWN-CONTROL OVERLAY, NOT ALPHA: this signal reduces downside on a
> held long crypto book by going flat / vol-targeted in downtrends
> (TSMOM-EV1 evidence: equal-weight buy-and-hold bear drawdown 66% vs
> overlay 17% - while the overlay itself LOST 12.2% absolute in that OOS
> window; authored outcome: mixed, defensive not profitable). It does not
> predict prices and does not aim to make money on its own. SIGNAL ONLY:
> not an order, no auto-execution, no testnet or live trading, and no
> production approval is implied or granted.

## Sample run (real latest candles, 2026-06-11)

```
symbol   trend state        vol (ann.)   weight  target USDC
--------------------------------------------------------------
AVAX     flat_downtrend       0.593462   0.0000         0.00
BNB      flat_downtrend       0.595281   0.0000         0.00
BTC      flat_downtrend       0.383020   0.0000         0.00
DOGE     flat_downtrend       0.518660   0.0000         0.00
ETH      flat_downtrend       0.564780   0.0000         0.00
SOL      flat_downtrend       0.547810   0.0000         0.00
SUI      flat_downtrend       0.674844   0.0000         0.00
XRP      flat_downtrend       0.475140   0.0000         0.00
--------------------------------------------------------------
PORTFOLIO gross weight 0.0000 = 0.00 USDC of 10,000 (0 held / 8 flat)
```

Reading: as of this sample all eight majors are in 30-day downtrend — the
overlay's target is **fully flat** (0 of 10,000 USDC exposed). That is the
validated defensive action in the live 2026 bear: an operator holding a long
book sees the overlay calling for cash. It is not a prediction.

## Closed-candle / no-lookahead rule

The calculator takes an explicit `as_of` and uses only candles whose close
time is at or before it; the in-progress candle and any future row are
excluded before any computation sees them (tested: appending future candles
does not change the output).

## OS panel decision: skipped (documented)

DASH-QASWEEP1 just stabilized the two-tab investor-ready dashboard behind 12
blocking browser checks. A new panel would touch `index.html`,
`evidence-dashboard.js`, the static-asset guards and DASH-QA1 in lockstep,
plus need empty-state handling for an ignored artifact that does not exist
on fresh clones — non-trivial dashboard surgery for a CLI-first tool. The
deliverable stays CLI + JSON; a display-only panel can be its own phase if
wanted. DASH-QA1 untouched and green.

## Boundaries

Public read-only data; signal only — not an order, no auto-execution, no
private/signed/order endpoints, no testnet or live trading, no production
approval implied or granted; the validated signal was not re-tuned.
