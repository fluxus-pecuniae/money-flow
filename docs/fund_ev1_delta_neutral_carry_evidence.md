# FUND-EV1 — Delta-Neutral Funding Carry Evidence

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change follows from this report. Funding is modeled
from public hourly history (daily-close accrual approximation); depth is
modeled (EXEC-EV1), not real; flip-side rows assume unmodeled spot borrow.
Account basis: 10,000 USDC.

## Verdict: `carry_does_not_survive_costs_and_tail_oos`

Gate reasons: `['oos_net_carry_not_positive_after_costs', 'walk_forward_net_carry_not_positive_in_every_fold', 'leave_one_out_breaks_oos_net_carry']`
Qualifiers: `[]`

## The honest question

Short the Hyperliquid perp, hold the same notional in HL spot, collect the
funding stream with ~zero price exposure. Does the net stream survive BOTH
legs' costs out-of-sample — and the tail (crash days, funding inversions,
legged fills) — or is it pennies in front of a steamroller?

## Headline (chronological 70/30 OOS, conservative friction)

- Train-only choice: `fund_ev1_collect_only_cad14_top4_1d`
- OOS net carry (after all costs): **-33.23155156** USDC
- OOS Sharpe -1.55064866, OOS max drawdown 0.43885916%, OOS days 119
- Full-window net 392.01220006 vs gross zero-cost 560.01882147 — costs ate 168.00662141 (30.00017410% of gross)
- Funding collected (full window): 490.39038071

## Benchmarks

| Benchmark | Net PnL | OOS net | Full Sharpe | Max DD % |
| --- | --- | --- | --- | --- |
| Gross carry (zero cost, same positions) | 560.01882147 | 49.58126210 | 6.39721669 | 0.18779884 |
| Always-on carry, all 4 names | 429.96433701 | 0.07966261 | 5.31331149 | 0.27870780 |
| Cash (hold 10,000 USDC) | 0 | 0 | — | 0 |

## Walk-forward (anchored thirds, train-only choice per fold)

- Fold B (`fund_ev1_collect_only_cad14_top4_1d`): net carry 111.30883047
- Fold C (`fund_ev1_collect_only_cad14_top4_1d`): net carry -35.07111287

## Regimes (not bull-only check)

- BTC perp trailing 90d return, point-in-time; bear < -0.10, bull > +0.10
- bull: 130 days, net 232.43094448
- neutral: 86 days, net 114.38891540
- bear: 177 days, net 45.19234019
- Gate non-bull net carry: 159.58125559

## Leave-one-out (drop each asset)

| Dropped | OOS net carry | OOS Sharpe | OOS max DD % |
| --- | --- | --- | --- |
| BTC | -29.86234504 | -1.30833039 | 0.41574506 |
| ETH | -39.03711734 | -1.75125192 | 0.47717531 |
| HYPE | -49.76045628 | -2.28067810 | 0.56959235 |
| SOL | -15.63272220 | -0.71359635 | 0.29961716 |

## Tail stress (the gate that matters most)

- Worst days (chosen config): [['2025-10-12 00:00:00+00:00', '-17.55618239'], ['2026-03-16 00:00:00+00:00', '-14.14415144'], ['2026-04-27 00:00:00+00:00', '-10.69985232'], ['2026-05-11 00:00:00+00:00', '-9.82234336'], ['2026-03-30 00:00:00+00:00', '-9.64278663']]
- Residual delta: max 0.00177729, avg 0.00028573 of equity
- Worst single candle move in window: 23.60704400%
- Modeled gap loss at max residual: 0.04195656% of equity
- Stressed run (stress friction + spot leg lag 1): net 642.57787044, max DD 0.91582841% (limit 8%)
- Leg-lag-only run (conservative): net delta 365.97252178 (fill-price path luck, not edge), max DD 0.79866339%, **max one-leg exposure 0.47943451 of equity** -> modeled gap loss 11.31803158% of equity against the window's worst candle — the real steamroller
- Funding paid on negative days: {'BTC': '-9.44866777', 'ETH': '-10.04343723', 'HYPE': '-6.00177084', 'SOL': '-17.29896943'}
- perp margin basis ~1x effective leverage (leg notional = half equity, unencumbered other half); liquidation mechanics not modeled — at 1x a short perp liquidates only near +100% adverse move, far outside the observed worst candle above

## Universe + window

- BTC, ETH, HYPE, SOL (spot: {'BTC': 'UBTC/USDC', 'ETH': 'UETH/USDC', 'SOL': 'USOL/USDC', 'HYPE': 'HYPE/USDC'})
- Window: 2025-05-11 00:00:00+00:00 -> 2026-06-08 00:00:00+00:00 (394 aligned days)
- BTC/ETH/SOL via Unit spot + HYPE native spot — the liquid HL-spot-supported names; aligned window limited by the youngest spot listing (USOL 2025-05-10); UFART/UPUMP-tier listings excluded as thin

## Boundaries

Research/evidence only; no order, testnet, live, production, or approval
surface. Public read-only data; modeled depth; daily funding accrual
approximation; spot borrow unmodeled (flip rows are upper bounds);
liquidation mechanics unmodeled. The verdict above is the gate's output
and was not forced positive.
