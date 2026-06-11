# FUND-EV2 — Funding Carry Under Realistic, Cited Costs

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change follows from this report. Costs are cited
(fee schedules + one-shot public l2Book calibration), never tuned to the
verdict; the sensitivity sweep makes the cost dependence auditable.
Account basis: 10,000 USDC.

## Verdict: `carry_does_not_survive_realistic_costs_and_tail_oos`

Gate reasons: `['oos_net_carry_not_positive_after_costs', 'leave_one_out_breaks_oos_net_carry']`
Qualifiers: `[]`
**Cost breakpoint: OOS edge dies at scale 0.75** (1.0 = cited realistic level)

## The honest question

FUND-EV1 killed the carry with a deliberately conservative cost model
(HL spot at the widest tier). Was that our conservatism, or is there no
capturable edge? Same bar, cited costs, selective entries, longer holds.

## Cited cost basis

- Hyperliquid fee schedule (docs, fetched 2026-06-11): perp taker 4.5 bps, spot taker 7 bps (base tier)
- Hyperliquid public l2Book one-shot calibration 2026-06-11: docs/fund_ev2_l2book_calibration_summary.json
- Kraken Pro fee schedule (fetched 2026-06-11): spot taker 40 bps base tier (Coinbase Advanced base tier worse at 60 bps)
- Cross-venue settlement: flat 2 USDC per spot fill (documented assumption)

## Round-trip cost (both legs, entry+exit, bps at 2.5k notional)

| Asset | hl_single | cross_venue |
| --- | --- | --- |
| BTC | 33.00000000 | 115.00000000 |
| ETH | 35.00000000 | 116.00000000 |
| HYPE | 35.00000000 | 119.00000000 |
| SOL | 42.00000000 | 116.00000000 |

(cross_venue: Kraken retail taker fee 40 bps/side + transfers dominates —
the deeper book does not help at a 10k account; Coinbase base tier is worse)

## Headline (chronological 70/30 OOS, cited realistic costs)

- Train-only choice: `fund_ev2_hl_single_cad14_top2_1d` (construction hl_single)
- OOS net carry: **-6.52404520** USDC; OOS Sharpe -0.60369958, max DD 0.22799259%, days 119
- Train: 4.35673262% (Sharpe 8.59419426)
- Full net 432.72101383 vs zero-cost 725.51584511 — costs ate 292.79483128 (40.35677970% of gross)
- Same config under FUND-EV1's conservative model: net 182.08084115, OOS -161.08871317

## Cost-sensitivity sweep (the discipline guard)

| Cost scale | OOS net | Full net | Trades |
| --- | --- | --- | --- |
| 0.25 | 40.57999381 | 670.02100018 | 122 |
| 0.5 | 55.67641791 | 646.56727322 | 96 |
| 0.75 | -1.52572435 | 473.22926674 | 64 |
| 1.0 | -6.52404520 | 432.72101383 | 49 |
| 1.25 | -11.60040180 | 493.88220513 | 48 |
| 1.5 | -2.10138063 | 497.64241602 | 44 |
| 2.0 | -1.87514593 | 266.56201073 | 28 |
| 3.0 | 0E-8 | 0E-8 | 0 |
| 5.0 | 0E-8 | 0E-8 | 0 |

- adaptive sweep: the strategy re-decides entries at each cost scale; selectivity going flat at high cost reads as net 0 = edge dead

## Walk-forward + regimes + leave-one-out

- Fold B (`fund_ev2_hl_single_cad14_top4_1d`): net 124.53568247
- Fold C (`fund_ev2_hl_single_cad14_top2_1d`): net 4.73298031
- regime bull: 130 days, net 265.18321560
- regime neutral: 86 days, net 76.21619981
- regime bear: 177 days, net 91.32159841
- Gate non-bull net: 167.53779822

| Dropped | OOS net carry | OOS Sharpe |
| --- | --- | --- |
| BTC | 2.70590414 | 0.23286701 |
| ETH | -6.56960808 | -0.60374365 |
| HYPE | 8.06350787 | 0.81505650 |
| SOL | 70.10180900 | 4.33928299 |

## Tail / legged execution (per construction)

- Chosen (hl_single): stressed (cost x2.0, spot leg lag 1) net -187.85173263, max DD 3.14109964% (limit 8%), max one-leg exposure 0.30212779 of equity -> modeled gap loss 7.13234403% at the window's worst candle (23.60704400%)
- Other (cross_venue): stressed net 0E-8, max DD 0E-8%, max one-leg exposure 0E-8
- daily-candle resolution makes the legged stress hold one-leg exposure for a full day; real cross-venue legging is typically minutes-hours, so the stress OVERSTATES duration while honestly bounding the gap exposure

## Boundaries

Research/evidence only; public read-only data; no order, testnet, live,
production, or approval surface. Costs cited, never tuned to the verdict;
l2Book calibration is point-in-time (sweep covers the uncertainty); spot
borrow + liquidation mechanics unmodeled. The verdict is the gate's
output and was not forced positive.
