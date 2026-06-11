# TREND-SUITE1 — Canonical Trend-Following Suite Evidence

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change follows from this report. Modeled friction
(EXEC-EV1) is an assumption layer, not real depth; perp funding is NOT
modeled (the suite is long-only — longs typically PAY funding in bulls,
so absolute profits here are optimistic). Account basis: 10,000 USDC.

## Verdict (train-chosen config): `beats_buy_hold_risk_adjusted_oos`

Qualifiers: `['oos_absolute_sharpe_not_positive_relative_edge_only', 'oos_absolute_return_negative_defensive_value_only']`
Gate reasons: `['tsmom_gate_passed']`

## The two headline questions

**1. Does ANY trend form beat buy-and-hold risk-adjusted OOS *in absolute
terms* (positive OOS return and Sharpe, full gate)?** -> **False**

| Family | Champion (train-chosen) | Full gate | Profitable OOS (abs.) | Clears absolute bar |
| --- | --- | --- | --- | --- |
| donchian | `trend_suite1_donchian20x10_atr_vt_1d` | True | False | False |
| ma_cross | `trend_suite1_ma10x50_signal_vt_1d` | False | False | False |
| mtf | `trend_suite1_mtf30w8_signal_vt_1d` | False | False | False |
| tsmom | `trend_suite1_tsmom30_signal_vt_1d` | True | False | False |
| ensemble | `trend_suite1_ens_average_vt_1d` | False | False | False |

**2. Did removing vol-targeting unlock profit, or just add risk?**

Pairwise OOS effect of switching each signal cell from vol-targeted to
equal-dollar sizing (deterministic classification):

| Classification | Cells |
| --- | --- |
| `removing_vol_target_added_drawdown_without_more_return_oos` | 23 |

In 16 of 23 pairs the uncapped (equal-dollar) variant DID earn a
higher full-window return — the bull-window upside the vol cap suppresses —
but every pair gave it back out-of-sample: more drawdown, no more OOS return.
Removing the vol cap was leverage on the same signal, not a new edge.

Hindsight-best OOS config (NOT a verdict — not train-chosen): `trend_suite1_mtf60w8_atr_vt_1d` (OOS Sharpe -0.81968212, return -4.11521937%).

## Headline (chronological 70/30 OOS, conservative friction)

| | Sharpe (ann.) | Max DD % | Total return % | Days |
| --- | --- | --- | --- | --- |
| Suite chosen (`trend_suite1_tsmom30_signal_vt_1d`) | -1.47832067 | 16.56343291 | -12.23482357 | 266 |
| Buy-and-hold equal-weight | -1.80669701 | 65.68137978 | -61.69142244 | 266 |

- OOS Sharpe edge vs buy-hold: **0.32837634**
- OOS max-drawdown delta vs buy-hold (negative = improved): **-49.11794687**

## Family champions (train-chosen within family; full gate each)

| Family | Champion | OOS Sharpe | OOS return % | OOS max DD % | Gate | Reasons |
| --- | --- | --- | --- | --- | --- | --- |
| donchian | `trend_suite1_donchian20x10_atr_vt_1d` | -1.37100954 | -8.53682455 | 10.61772159 | beats_buy_hold_risk_adjusted_oos | `['tsmom_gate_passed']` |
| ma_cross | `trend_suite1_ma10x50_signal_vt_1d` | -1.92212447 | -15.08489556 | 16.49089744 | no_risk_adjusted_edge_vs_buy_hold | `['oos_sharpe_does_not_beat_buy_hold', 'walk_forward_sharpe_edge_not_positive_in_every_fold', 'leave_one_out_breaks_risk_adjusted_edge']` |
| mtf | `trend_suite1_mtf30w8_signal_vt_1d` | -1.13796041 | -6.68840724 | 9.62989869 | no_risk_adjusted_edge_vs_buy_hold | `['walk_forward_sharpe_edge_not_positive_in_every_fold']` |
| tsmom | `trend_suite1_tsmom30_signal_vt_1d` | -1.47832067 | -12.23482357 | 16.56343291 | beats_buy_hold_risk_adjusted_oos | `['tsmom_gate_passed']` |
| ensemble | `trend_suite1_ens_average_vt_1d` | -1.96475262 | -10.52861822 | 11.79239166 | no_risk_adjusted_edge_vs_buy_hold | `['oos_sharpe_does_not_beat_buy_hold', 'leave_one_out_breaks_risk_adjusted_edge']` |

## Benchmarks (same machinery, same friction)

| Benchmark | Full Sharpe | Full Max DD % | OOS Sharpe | Net PnL |
| --- | --- | --- | --- | --- |
| Buy-hold equal-weight | 0.36842536 | 67.47171829 | -1.80669701 | 590.60025361 |
| Always-long, no vol target | 0.43874186 | 67.43277505 | -1.84087208 | 1844.16387898 |
| Always-long, vol-targeted (beta probe) | 0.66077775 | 29.71444852 | -1.88976964 | 3005.49430252 |
| Random long/flat (20 seeds) | — | — | median -1.99941493 | — |

## Walk-forward (anchored thirds, train-only choice per fold; global pool)

- Fold B (`trend_suite1_tsmom30_signal_vt_1d`): Sharpe edge 1.16299475
- Fold C (`trend_suite1_tsmom30_signal_vt_1d`): Sharpe edge 0.41356891

## Leave-one-out (global chosen config; drop each asset from book AND benchmark)

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

## Late-entry sensitivity (global chosen config)

- Avg adverse move by lateness (bps): {'0': '-0.12720000', '1': '41.35047460', '2': '56.13201559'}
- +1 candle delay OOS Sharpe: -1.54841322
- +2 candle delay OOS Sharpe: -1.53480635

## Universe + design

- Liquid subset: AVAX, BNB, BTC, DOGE, ETH, SOL, SUI, XRP (excluded: HYPE)
- Window: 2024-01-02 00:00:00+00:00 -> 2026-06-08 00:00:00+00:00 (889 aligned days)
- Grid: 46 configs — Donchian 20/55 (channel + ATR exits), MA cross 3x3 (+ATR on 20x100), MTF 30/60/90 (+ATR on 60), TSMOM 30/60/90 carry-over, ensemble majority/average; every cell in vol-targeted AND equal-dollar sizing
- channel (Donchian), signal-off, ATR/chandelier trailing stop (2.8 x ATR14 from highest close since entry; re-entry requires a fresh signal)
- Cadence: daily for stop/cross exits (a hit stop must not ride for days), weekly for the TSMOM carry-over (EV1 parity); rebalance band 0.5% of equity suppresses dust

## Boundaries

Research/evidence only; no order, testnet, live, production, or approval
surface. Modeled depth, not real. Perp funding not modeled. Long-only.
The verdicts above are gate outputs and were not forced positive; the
signals were designed from the documented canon, not tuned to the verdict.
