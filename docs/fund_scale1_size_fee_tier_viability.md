# FUND-SCALE1 — Funding Carry: Scale & Fee-Tier Viability

Research/evidence only. No runtime, strategy-rule, order, testnet, live,
or production-approval change. Fee tiers are the published schedules
(cited); tier achievement is derived from the strategy's OWN volume;
impact scales with the actual traded notional; implausible-participation
cells cannot pass. The 10k retail verdict (FUND-EV2) is not re-litigated.

## Verdict: `carry_does_not_reach_viability_at_credible_scale`

## Cited fee schedules

- Hyperliquid docs fee tiers (fetched 2026-06-11): perp T0-T6 taker 4.5/4.0/3.5/3.0/2.8/2.6/2.4 bps, spot T0-T6 taker 7.0/6.0/5.0/4.0/3.5/3.0/2.5 bps; 14d weighted volume, spot counted double; maker-volume-share rebates (-0.1/-0.2/-0.3 bps) require market-maker flow, not modeled
- Kraken Pro fee schedule (fetched 2026-06-11): spot taker 40/35/24/22/20/18/16/14/12/10/8/5 bps at 30d volume 0/10k/50k/100k/250k/500k/1M/2.5M/5M/10M/100M/500M
- Spreads/impact/slippage/settlement: the FUND-EV2 cited model (l2Book calibration + flat 2 USDC cross-venue settlement, amortizing with size)

- Tier achievement rule: a tier counts as achieved only if the strategy's own traded volume at that size reaches the published qualifying volume (HL 14d weighted, spot double; Kraken 30d)
- Impact plausibility: max single-fill participation <= 0.10 of candle $ volume

## Viability map (OOS net carry, USDC; * = tier NOT achieved by own volume; ! = impact implausible)

### hl_single

| Tier \ Size | 10,000 | 50,000 | 250,000 | 1,000,000 | 5,000,000 |
| --- | --- | --- | --- | --- | --- |
| hl_tier_0 | -7 | -34 | -180 | -803 | -5,071 |
| hl_tier_1 | -5* | -25* | -137* | -634* | -4,216* |
| hl_tier_2 | -3* | -16* | -94* | -461* | -3,350* |
| hl_tier_3 | -1* | -8* | -51* | -287* | -2,475* |
| hl_tier_4 | -1* | -4* | -30* | -206* | -2,072* |

### cross_venue

| Tier \ Size | 10,000 | 50,000 | 250,000 | 1,000,000 | 5,000,000 |
| --- | --- | --- | --- | --- | --- |
| kraken_tier_0 | -14 | -57 | -271 | -1,091 | -5,653 |
| kraken_tier_100k | -30* | -117* | -555* | -2,227 | -11,469 |
| kraken_tier_1m | -24* | -91*! | -426*! | -1,712*! | -8,906*! |
| kraken_tier_10m | -13* | 10*! | 122*! | 522*! | 2,425*! |
| kraken_tier_100m | -4* | -53* | -228* | -922* | -5,054* |

## Fee-axis breakpoint (first tier with positive OOS net, per size)

- hl_single: 10,000: none, 50,000: none, 250,000: none, 1,000,000: none, 5,000,000: none
- cross_venue: 10,000: none, 50,000: kraken_tier_10m, 250,000: kraken_tier_10m, 1,000,000: kraken_tier_10m, 5,000,000: kraken_tier_10m

## Maker-bound line (OPTIMISTIC, non-gateable)

- all fills passive at HL base maker fees with zero half-spread paid; non-fill/chase risk NOT modeled - informs, never passes
| Size | OOS net | OOS % of equity |
| --- | --- | --- |
| 10,000 | 26.4 | 0.26372525% |
| 50,000 | 130.9 | 0.26172637% |
| 250,000 | 643.2 | 0.25726824% |
| 1,000,000 | 2,492.4 | 0.24924194% |
| 5,000,000 | 11,470.4 | 0.22940760% |

## Boundaries

Research/evidence only; public read-only data; published fee schedules
cited; tier achievement derived from own volume; maker-bound line is an
optimistic non-gateable bound; spot borrow/liquidation unmodeled. The
verdict is computed from the gated cells and was not forced positive.
