# TSMOM-EV1 — Volatility-Targeted Time-Series Momentum Evidence

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change follows from this report. Modeled friction
(EXEC-EV1) is an assumption layer, not real depth; perp funding is NOT
modeled. Account basis: 10,000 USDC.

## Verdict: `beats_buy_hold_risk_adjusted_oos`

Gate reasons: `['tsmom_gate_passed']`

## The honest question

Does per-asset trend with volatility targeting + risk parity add
risk-adjusted value (Sharpe / max drawdown) over simply holding the same
liquid universe — out-of-sample, after conservative friction? The
vol-targeted always-long benchmark separates 'trend timing' from 'vol
targeting applied to beta'.

## Headline (chronological 70/30 OOS, conservative friction)

| | Sharpe (ann.) | Max DD % | Total return % | Days |
| --- | --- | --- | --- | --- |
| TSMOM chosen (`tsmom_ev1_lb30_vt20_long_only_1d`) | -1.47832067 | 16.56343291 | -12.23482357 | 266 |
| Buy-and-hold equal-weight | -1.80669701 | 65.68137978 | -61.69142244 | 266 |

- OOS Sharpe edge vs buy-hold: **0.32837634**
- OOS max-drawdown delta vs buy-hold (negative = improved): **-49.11794687**

## Benchmarks (same machinery, same friction, full window)

| Benchmark | Full Sharpe | Full Max DD % | OOS Sharpe | Net PnL |
| --- | --- | --- | --- | --- |
| Buy-hold equal-weight | 0.36842536 | 67.47171829 | -1.80669701 | 590.60025361 |
| Always-long, no vol target | 0.43874186 | 67.43277505 | -1.84087208 | 1844.16387898 |
| Always-long, vol-targeted (beta probe) | 0.66077775 | 29.71444852 | -1.88976964 | 3005.49430252 |
| Random long/flat (20 seeds) | — | — | median -1.99941493 | — |

## Walk-forward (anchored thirds, train-only choice per fold)

- Fold B (`tsmom_ev1_lb30_vt20_long_only_1d`): Sharpe edge 1.16299475
- Fold C (`tsmom_ev1_lb30_vt20_long_only_1d`): Sharpe edge 0.41356891

## Leave-one-out (drop each asset from book AND benchmark)

| Dropped | OOS strategy Sharpe | OOS buy-hold Sharpe | Edge |
| --- | --- | --- | --- |
| AVAX | -1.44844097 | -1.78507558 | 0.33663461 |
| BNB | -1.66824047 | -1.91902563 | 0.25078516 |
| BTC | -1.51031985 | -1.80973866 | 0.29941881 |
| DOGE | -1.59148555 | -1.78951622 | 0.19803067 |
| ETH | -1.34882346 | -1.80148933 | 0.45266587 |
| SOL | -1.47872802 | -1.76403653 | 0.28530851 |
| SUI | -1.50130194 | -1.72505178 | 0.22374984 |
| XRP | -1.24539199 | -1.80461390 | 0.55922191 |

## Late-entry sensitivity

- Avg adverse move by lateness (bps): {'0': '-0.12720000', '1': '41.35047460', '2': '56.13201559'}
- +1 candle delay OOS Sharpe: -1.54841322
- +2 candle delay OOS Sharpe: -1.53480635

## Universe + design

- Liquid subset: AVAX, BNB, BTC, DOGE, ETH, SOL, SUI, XRP (excluded: HYPE)
- Window: 2024-01-02 00:00:00+00:00 -> 2026-06-08 00:00:00+00:00 (889 aligned days)
- sign of trailing lookback return (30/60/90d); exact zero = flat
- Vol targeting: equal risk budget per asset = portfolio_vol_target / N; weight = sign * min(budget / realized_vol_30d, 0.40)
- Gross leverage cap 1.5; weekly rebalance; band 0.005 of equity

## Boundaries

Research/evidence only; no order, testnet, live, production, or approval
surface. Modeled depth, not real. Perp funding not modeled. The verdict
above is the gate's output and was not forced positive.
