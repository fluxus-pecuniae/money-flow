# FUND-VENUES1 — Funding Carry on Deep Venues, with Leverage

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change follows from this report. Fees are cited
published schedules at the tier a 10k account's own flow earns; the
gateable verdict prices taker fills; maker is a non-gateable ceiling;
the venue-fair window is enforced from DATA1 coverage (K-036).
Account basis: 10,000 USDC.

## Verdicts per (construction, leverage)

| Cell | OOS net | OOS Sharpe | OOS maxDD | Borrow cost | Liq (full/stressed) | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| binance_single 1x | 179.18087731 | 3.50995605 | 0.08323323% | 5.21907880 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| binance_single 3x | -1.10440530 | -0.74053937 | 86.59334966% | 222.11780353 | 4/1 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| binance_single 5x | -92.75019757 | None | None% | 310.67994252 | 2/1 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| bybit_single 1x | 67.80197531 | 2.49358060 | 0.27622875% | 0E-8 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| bybit_single 3x | 89.18401796 | 0.94888824 | 0.92202622% | 1079.07652292 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| bybit_single 5x | 17.95861881 | 1.16838605 | 1.05732888% | 1247.78563677 | 1/1 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| binance_cross_coinbase 1x | -13.84182304 | -0.45169844 | 0.28758511% | 0E-8 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| binance_cross_coinbase 3x | -8.43026785 | -0.10098682 | 0.64722409% | 276.48342947 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |
| binance_cross_coinbase 5x | -24.60729307 | -0.18391682 | 1.19765929% | 961.91522402 | 0/0 | `carry_does_not_survive_realistic_costs_and_tail_oos` |

## Venue-fair windows (K-036 enforcement)

- binance: 2088 funding days — ELIGIBLE
- bybit: 1730 funding days — ELIGIBLE
- hyperliquid: 1089 funding days — EXCLUDED — funding_history_below_min_for_deep_oos (1126 days) and already answered by FUND-EV2 at cited HL costs (reference, not re-tested)
- kraken: 366 funding days — EXCLUDED — funding_history_below_min_for_deep_oos (~366 days public window)
- okx: 92 funding days — EXCLUDED — funding_history_below_min_for_deep_oos (~92 days public window)

## Cited cost basis

- Binance fee schedule (public fee page, fetched 2026-06-12, Regular user/VIP0): USDS-M perp maker 2.0 / taker 5.0 bps; spot maker 10 / taker 10 bps; BNB discount not assumed; VIP1 requires >=$1M 30d futures volume (own flow cannot earn it at 10k)
- Bybit fee schedule (public fee page, fetched 2026-06-12, non-VIP): derivatives maker 2.0 / taker 5.5 bps; spot maker 10 / taker 10 bps
- OKX fee schedule (public fee page, fetched 2026-06-12, regular user Lv1): perp maker 2.0 / taker 5.0 bps; spot maker 8 / taker 10 bps (cited for the record; venue excluded for funding depth)
- Coinbase Advanced retail volume tier (per FUND-EV2 citation 2026-06-11): spot taker 60 bps, maker 40 bps
- flat 2 USDC per cross-venue spot fill (on-chain transfer/settlement amortization, documented assumption carried over from FUND-EV2)
- modeled half-spreads with headroom over typical top-of-book on the deepest books (BTC/ETH 0.5 bps, other majors 1.0 bps; Binance/Bybit/Coinbase books are far deeper than the HL books FUND-EV2 calibrated at 0.08-2.4 bps); no per-venue l2 calibration in DATA1 — the cost-sensitivity sweep covers the residual uncertainty
- perp initial margin 10% (10x perp-side margin; venues allow far more on majors — conservative), maintenance 1.0% of gross notional (Binance USDS-M tier-1 maintenance 0.4-0.65% for majors at small notional, modeled with buffer), borrow 0.02%/day on the cash shortfall (documented assumption at the published Binance Cross Margin USDT VIP0 ballpark; swept with the cost sweep), borrow call buffer 5% of borrowed

## Per-cell detail

### binance_cross_coinbase|lev1

- Window 2021-10-01 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1715 days); chosen `fund_venues1_binance_cross_coinbase_lev1_cad28_top4_1d`
- OOS net **-13.84182304** (Sharpe -0.45169844, maxDD 0.28758511%, days 515)
- Full net 248.29655565 (funding 492.02713198, fees 233.95199323, borrow 0E-8, max borrowed 0E-8)
- Gross zero-cost 1658.82373189; maker ceiling (NON-GATEABLE) full 375.71362614 / OOS 1.20823115
- Folds: B 161.82602617, C 42.90293216
- OOS regimes: bull 15.80863047 (159d), neutral -26.45985065 (126d), bear -3.19060286 (229d)
- Cycles: 2020_2021_bull 19.63544064, 2022_bear -6.78640875, 2023_2024_recovery 234.52093479, 2025_2026_current -0.18785754
- Stressed (cost x2 + leg lag): net 0E-8, maxDD 0E-8%, liquidations 0
- Cost sweep OOS: 0.25x=52.24669086, 0.5x=19.39755134, 0.75x=2.67091296, 1.0x=-13.84182304, 1.25x=-29.00610871, 1.5x=0E-8, 2.0x=0E-8, 3.0x=0E-8, 5.0x=0E-8
- Breakpoint: 1.0
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_net_carry_not_positive_after_costs', 'leave_one_out_breaks_oos_net_carry', 'oos_regime_bear_net_carry_not_positive', 'oos_regime_neutral_net_carry_not_positive']; qualifiers []

### binance_cross_coinbase|lev3

- Window 2021-10-01 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1715 days); chosen `fund_venues1_binance_cross_coinbase_lev3_cad28_top4_1d`
- OOS net **-8.43026785** (Sharpe -0.10098682, maxDD 0.64722409%, days 515)
- Full net 646.43749730 (funding 1622.46102264, fees 667.00977756, borrow 276.48342947, max borrowed 13047.82571429)
- Gross zero-cost 5606.87130164; maker ceiling (NON-GATEABLE) full 855.37748890 / OOS 38.73346818
- Folds: B 388.07048540, C 149.59177601
- OOS regimes: bull 51.58155695 (159d), neutral -58.56072226 (126d), bear -1.45110254 (229d)
- Cycles: 2020_2021_bull 131.96382783, 2022_bear -33.93670336, 2023_2024_recovery 512.64898854, 2025_2026_current 26.61887234
- Stressed (cost x2 + leg lag): net 0E-8, maxDD 0E-8%, liquidations 0
- Cost sweep OOS: 0.25x=253.28128809, 0.5x=86.27997649, 0.75x=34.85131740, 1.0x=-8.43026785, 1.25x=-49.89500648, 1.5x=-96.60607601, 2.0x=0E-8, 3.0x=0E-8, 5.0x=0E-8
- Breakpoint: 1.0
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_net_carry_not_positive_after_costs', 'leave_one_out_breaks_oos_net_carry', 'oos_regime_bear_net_carry_not_positive', 'oos_regime_neutral_net_carry_not_positive']; qualifiers []

### binance_cross_coinbase|lev5

- Window 2021-10-01 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1715 days); chosen `fund_venues1_binance_cross_coinbase_lev5_cad28_top4_1d`
- OOS net **-24.60729307** (Sharpe -0.18391682, maxDD 1.19765929%, days 515)
- Full net 628.64737845 (funding 2706.24499275, fees 1058.12184294, borrow 961.91522402, max borrowed 28537.55131701)
- Gross zero-cost -10146.29624676; maker ceiling (NON-GATEABLE) full 765.23165911 / OOS 53.11212792
- Folds: B 317.43139783, C 167.65500819
- OOS regimes: bull 67.05133052 (159d), neutral -91.94812743 (126d), bear 0.28950384 (229d)
- Cycles: 2020_2021_bull 191.84036083, 2022_bear -64.14060437, 2023_2024_recovery 469.44175188, 2025_2026_current 18.19270701
- Stressed (cost x2 + leg lag): net 0E-8, maxDD 0E-8%, liquidations 0
- Cost sweep OOS: 0.25x=-7.31868028, 0.5x=149.14205127, 0.75x=48.73542530, 1.0x=-24.60729307, 1.25x=-94.56680489, 1.5x=-158.56474302, 2.0x=0E-8, 3.0x=0E-8, 5.0x=0E-8
- Breakpoint: 0.25
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_net_carry_not_positive_after_costs', 'non_bull_regime_net_carry_not_positive', 'leave_one_out_breaks_oos_net_carry', 'oos_regime_neutral_net_carry_not_positive']; qualifiers []

### binance_single|lev1

- Window 2020-09-24 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (2087 days); chosen `fund_venues1_binance_single_lev1_cad14_top4_1d`
- OOS net **179.18087731** (Sharpe 3.50995605, maxDD 0.08323323%, days 627)
- Full net 3910.06722582 (funding 4258.27184332, fees 250.39126330, borrow 5.21907880, max borrowed 5815.59143049)
- Gross zero-cost 5289.66567819; maker ceiling (NON-GATEABLE) full 3981.42263968 / OOS 179.45143796
- Folds: B 800.70001608, C 203.42754046
- OOS regimes: bull 152.81713559 (237d), neutral 26.15254783 (160d), bear 0.21119389 (229d)
- Cycles: 2020_2021_bull 2845.45475575, 2022_bear 54.00990485, 2023_2024_recovery 989.87821396, 2025_2026_current 17.03136218
- Stressed (cost x2 + leg lag): net 869.50493732, maxDD 9.68437671%, liquidations 0
- Cost sweep OOS: 0.25x=561.30030639, 0.5x=380.53230522, 0.75x=189.80735451, 1.0x=179.18087731, 1.25x=131.68727414, 1.5x=118.95591809, 2.0x=105.96584265, 3.0x=80.30544983, 5.0x=0E-8
- Breakpoint: 5.0
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['stressed_tail_drawdown_exceeds_documented_limit']; qualifiers []

### binance_single|lev3

- Window 2020-09-24 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (2087 days); chosen `fund_venues1_binance_single_lev3_cad28_top2_1d`
- OOS net **-1.10440530** (Sharpe -0.74053937, maxDD 86.59334966%, days 627)
- Full net -9999.82279120 (funding 2601.54939904, fees 200.10193224, borrow 222.11780353, max borrowed 26436.85644213)
- Gross zero-cost -9999.17155388; maker ceiling (NON-GATEABLE) full -9998.01077929 / OOS 0.07551061
- Folds: B -11.76858703, C -1.09910082
- OOS regimes: bull -1.11426701 (237d), neutral 0.01025388 (160d), bear -0.00039216 (229d)
- Cycles: 2020_2021_bull -9987.02122370, 2022_bear 0.20951977, 2023_2024_recovery -13.02079593, 2025_2026_current -0.00014582
- Stressed (cost x2 + leg lag): net -10266.40609618, maxDD None%, liquidations 1
- Cost sweep OOS: 0.25x=0.04789894, 0.5x=0.02283892, 0.75x=0.13969465, 1.0x=-1.10440530, 1.25x=0.16744563, 1.5x=-0.84970450, 2.0x=-36.51748572, 3.0x=-130.64638274, 5.0x=-1102.52375052
- Breakpoint: 1.0
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_net_carry_not_positive_after_costs', 'walk_forward_net_carry_not_positive_in_every_fold', 'leave_one_out_breaks_oos_net_carry', 'oos_drawdown_exceeds_documented_limit', 'stressed_tail_drawdown_exceeds_documented_limit', 'oos_regime_bear_net_carry_not_positive', 'oos_regime_bull_net_carry_not_positive', 'liquidation_event_in_oos', 'liquidation_event_in_stressed_run']; qualifiers []

### binance_single|lev5

- Window 2020-09-24 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (2087 days); chosen `fund_venues1_binance_single_lev5_cad14_top2_1d`
- OOS net **-92.75019757** (Sharpe None, maxDD None%, days 627)
- Full net -10788.23279635 (funding 827.18076849, fees 119.33461397, borrow 310.67994252, max borrowed 33713.99296196)
- Gross zero-cost -10627.70103289; maker ceiling (NON-GATEABLE) full -10796.10845248 / OOS -93.67691439
- Folds: B -89.00902186, C -102.14380033
- OOS regimes: bull -34.55097616 (237d), neutral -23.48341944 (160d), bear -34.71580197 (229d)
- Cycles: 2020_2021_bull -10569.88005490, 2022_bear -43.03887192, 2023_2024_recovery -96.37535093, 2025_2026_current -78.56002984
- Stressed (cost x2 + leg lag): net -18490.33720779, maxDD None%, liquidations 1
- Cost sweep OOS: 0.25x=-20.43153476, 0.5x=-42.35194346, 0.75x=-66.63901008, 1.0x=-92.75019757, 1.25x=-122.91812301, 1.5x=-1029.14643282, 2.0x=-1585.76659519, 3.0x=-3129.19909845, 5.0x=-10582.14613681
- Breakpoint: 0.25
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_net_carry_not_positive_after_costs', 'walk_forward_net_carry_not_positive_in_every_fold', 'non_bull_regime_net_carry_not_positive', 'leave_one_out_breaks_oos_net_carry', 'oos_drawdown_exceeds_documented_limit', 'stressed_tail_drawdown_exceeds_documented_limit', 'oos_regime_bear_net_carry_not_positive', 'oos_regime_neutral_net_carry_not_positive', 'oos_regime_bull_net_carry_not_positive', 'liquidation_event_in_stressed_run']; qualifiers []

### bybit_single|lev1

- Window 2022-03-11 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1554 days); chosen `fund_venues1_bybit_single_lev1_cad28_top4_1d`
- OOS net **67.80197531** (Sharpe 2.49358060, maxDD 0.27622875%, days 467)
- Full net 1409.05097698 (funding 1570.38047049, fees 116.48271397, borrow 0E-8, max borrowed 0E-8)
- Gross zero-cost 1779.38048611; maker ceiling (NON-GATEABLE) full 1296.38736020 / OOS 94.81782121
- Folds: B 1024.19104111, C 99.92586134
- OOS regimes: bull 52.11603265 (130d), neutral 18.33053295 (112d), bear -2.64459029 (224d)
- Cycles: 2022_bear 69.70738651, 2023_2024_recovery 1234.16639379, 2025_2026_current 104.13701576
- Stressed (cost x2 + leg lag): net 1264.62128025, maxDD 0.61409383%, liquidations 0
- Cost sweep OOS: 0.25x=186.47453317, 0.5x=124.60643582, 0.75x=85.91519600, 1.0x=67.80197531, 1.25x=46.63579921, 1.5x=42.61312364, 2.0x=28.24038620, 3.0x=18.54882123, 5.0x=0.41269184
- Breakpoint: None
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['oos_regime_bear_net_carry_not_positive']; qualifiers []

### bybit_single|lev3

- Window 2022-03-11 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1554 days); chosen `fund_venues1_bybit_single_lev3_cad28_top4_1d`
- OOS net **89.18401796** (Sharpe 0.94888824, maxDD 0.92202622%, days 467)
- Full net 3514.31494587 (funding 5165.78612967, fees 414.33668793, borrow 1079.07652292, max borrowed 17807.38355427)
- Gross zero-cost 6300.59288822; maker ceiling (NON-GATEABLE) full 3012.42901238 / OOS 167.14300194
- Folds: B 2742.06949465, C 171.76760409
- OOS regimes: bull 117.03728864 (130d), neutral -19.82235198 (112d), bear -8.03091870 (224d)
- Cycles: 2022_bear 213.01609636, 2023_2024_recovery 3126.11593141, 2025_2026_current 173.06871622
- Stressed (cost x2 + leg lag): net 2780.04113047, maxDD 2.50871790%, liquidations 0
- Cost sweep OOS: 0.25x=601.54202818, 0.5x=310.01752404, 0.75x=188.38235747, 1.0x=89.18401796, 1.25x=158.60746399, 1.5x=139.61750363, 2.0x=87.68814162, 3.0x=53.98979122, 5.0x=-5.33266762
- Breakpoint: 5.0
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['leave_one_out_breaks_oos_net_carry', 'oos_regime_bear_net_carry_not_positive', 'oos_regime_neutral_net_carry_not_positive']; qualifiers []

### bybit_single|lev5

- Window 2022-03-11 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (1554 days); chosen `fund_venues1_bybit_single_lev5_cad14_top2_1d`
- OOS net **17.95861881** (Sharpe 1.16838605, maxDD 1.05732888%, days 467)
- Full net -8338.72118750 (funding 4693.09567981, fees 354.10196798, borrow 1247.78563677, max borrowed 28803.82807468)
- Gross zero-cost -15327.73159652; maker ceiling (NON-GATEABLE) full -17528.71883590 / OOS -669.90713863
- Folds: B -13516.67896596, C 25.61833006
- OOS regimes: bull 25.10120171 (130d), neutral 5.43097415 (112d), bear -12.57355705 (224d)
- Cycles: 2022_bear 0E-8, 2023_2024_recovery -8368.06311599, 2025_2026_current 29.24434015
- Stressed (cost x2 + leg lag): net -8903.34477894, maxDD 89.82450665%, liquidations 1
- Cost sweep OOS: 0.25x=-126.93125407, 0.5x=-335.06264557, 0.75x=-490.87336852, 1.0x=17.95861881, 1.25x=4.48964580, 1.5x=-45.86562041, 2.0x=0E-8, 3.0x=0E-8, 5.0x=0E-8
- Breakpoint: 0.25
- Verdict `carry_does_not_survive_realistic_costs_and_tail_oos` — reasons ['walk_forward_net_carry_not_positive_in_every_fold', 'leave_one_out_breaks_oos_net_carry', 'stressed_tail_drawdown_exceeds_documented_limit', 'oos_regime_bear_net_carry_not_positive', 'liquidation_event_in_stressed_run']; qualifiers []

## Adversarial review

- Trigger: required before believing any POSITIVE verdict. Cells passed: False — log: `not_required_no_positive_verdict`.
- The near-miss (binance_single 1x, single failing reason) was NOT softened; its
  positive components were attacked anyway and the scrutiny is pinned in tests:
  - lookahead in the funding/price join: only-future-funding tampering cannot
    change decisions (test), and funding accrues on positions held through the
    candle (FUND-EV1 convention, unchanged);
  - fee optimism: the tier is VIP0/non-VIP because the strategy's own 10k flow
    cannot earn a volume tier (FUND-SCALE1 rule); maker is never gated on;
  - survivorship: negative-mean-funding BNB and ~zero-mean SOL stay in the
    universe; XRP is excluded only from the cross-venue cell for the real
    Coinbase 904-day delisting hole;
  - fragility: the OOS bear-regime bucket is +0.21 USDC over 229 days — one
    trade's rounding from a second failing reason; reported, not smoothed;
  - the binding failure (stressed legged-execution tail 9.68% vs the 8%
    documented account limit) reuses FUND-EV1/EV2's pre-committed stress and
    limit verbatim — the bar was not moved in either direction.

## Benchmarks

- HL FUND-EV2 committed reference: {"verdict": "carry_does_not_survive_realistic_costs_and_tail_oos", "oos_net_carry": "-6.52404520", "cost_breakpoint_scale": "0.75", "note": "the HL-only answer this phase re-tests on deep venues"}

## Boundaries

Public read-only DATA1 inputs; no orders, private/signed endpoints, or
approval surface. Fees cited, never tuned; borrow rate a documented
swept assumption; maker non-fill risk unmodeled (ceiling only);
liquidation model conservative (isolated adversarial same-day extremes).
The verdict is the gate's output and was not forced positive.
