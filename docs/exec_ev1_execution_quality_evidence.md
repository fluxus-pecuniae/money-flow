# EXEC-EV1 Execution-Quality Evidence

## Verdict

- Status: `execution_quality_evidence_complete`
- Purpose: re-score the three Week 2 lanes under a depth-aware modeled friction layer.
- **Modeled depth, not real depth.** Depth/liquidity is MODELED from historical candle volume, not real historical order-book depth (which does not exist; Hyperliquid public l2Book is a current snapshot only). Every cost is an assumption.
- Known issue: K-001 partially (modeled, not real, depth-aware execution quality)
- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.
- Trading boundary: no orders, private/signed/order/testnet/live endpoints, or approvals.

## Friction Model

- Impact law: `square_root_participation_rate`
- Liquidity proxy: `candle base-asset volume * typical price ((H+L+C)/3)`
- Guarantee: EXEC-EV1 cost >= SV2.3 parent cost; EXEC-EV1 net PnL <= SV2.3 net PnL per lane/scenario
- Components: `fee_bps (kept from SV2.3)`, `slippage_bps (kept from SV2.3)`, `adverse_gap_penalty_bps (kept from SV2.3)`, `spread_bps (NEW — per-symbol liquidity-tier half-spread)`, `impact_bps (NEW — square-root participation-rate market impact)`, `chase_bps (NEW — fill-probability unfilled-chase penalty)`

## Aggregate Results (EXEC-EV1 vs SV2.3)

| Strategy | Scenario | EXEC-EV1 Net | SV2.3 Net | Delta | Trades | Avg Friction bps | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `avoid_low_rolling_range_20` | `exec_ev1_base` | `-170022.78241201` | `-77394.55050274` | `-92628.23190927` | `10080` | `9.59290781` | `not_promoted_realistic_gate_failed` |
| `avoid_low_rolling_range_20` | `exec_ev1_conservative` | `-285441.80724516` | `-155254.99799294` | `-130186.80925222` | `10080` | `21.52014319` | `not_promoted_realistic_gate_failed` |
| `avoid_low_rolling_range_20` | `exec_ev1_stress` | `-400242.07639337` | `-241147.09720998` | `-159094.97918339` | `10080` | `40.63388329` | `not_promoted_realistic_gate_failed` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_base` | `112208.48643170` | `155140.87686128` | `-42932.39042958` | `2992` | `9.61797151` | `survives_size_aware_friction` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_conservative` | `43479.29881295` | `119776.22299882` | `-76296.92418587` | `2992` | `21.97997662` | `survives_size_aware_friction` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_stress` | `-52223.37529632` | `73473.05378781` | `-125696.42908413` | `2992` | `42.36033355` | `not_promoted_realistic_gate_failed` |
| `money_flow_v1_2_baseline` | `exec_ev1_base` | `-184348.04619093` | `-85740.74865029` | `-98607.29754064` | `11134` | `9.60677847` | `not_promoted_realistic_gate_failed` |
| `money_flow_v1_2_baseline` | `exec_ev1_conservative` | `-302776.64505633` | `-168633.91144830` | `-134142.73360803` | `11134` | `21.45989075` | `not_promoted_realistic_gate_failed` |
| `money_flow_v1_2_baseline` | `exec_ev1_stress` | `-415775.48126085` | `-257964.81857104` | `-157810.66268981` | `11134` | `40.34215615` | `not_promoted_realistic_gate_failed` |

## Late-Entry / Entry-Timing Cost (bps by lateness)

Adverse move from the signal candle to fills 0/1/2 candles late. Informs the
future RT-HISTSEED1 historical-position-seeding decision: small cost => seeding
not worth the runtime risk; large cost => edge decays fast at the signal (a red flag).

| Strategy | Scenario | +0 (next open) | +1 late | +2 late |
| --- | --- | ---: | ---: | ---: |
| `avoid_low_rolling_range_20` | `exec_ev1_base` | `0.52138783` | `-14.86507851` | `-21.06553800` |
| `avoid_low_rolling_range_20` | `exec_ev1_conservative` | `0.52138783` | `-14.86507851` | `-21.06553800` |
| `avoid_low_rolling_range_20` | `exec_ev1_stress` | `0.52138783` | `-14.86507851` | `-21.06553800` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_base` | `1.17949365` | `15.03967207` | `36.79053556` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_conservative` | `1.17949365` | `15.03967207` | `36.79053556` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `exec_ev1_stress` | `1.17949365` | `15.03967207` | `36.79053556` |
| `money_flow_v1_2_baseline` | `exec_ev1_base` | `0.49228242` | `-14.66586549` | `-20.90519988` |
| `money_flow_v1_2_baseline` | `exec_ev1_conservative` | `0.49228242` | `-14.66586549` | `-20.90519988` |
| `money_flow_v1_2_baseline` | `exec_ev1_stress` | `0.49228242` | `-14.66586549` | `-20.90519988` |

## Future Phase — RT-HISTSEED1

- Name: `RT-HISTSEED1`
- Status: `position_live_in_historical`
- Startup historical-position reconstruction. Iron rules: separate bucket, never blended into forward synthetic PnL, never eligible for testnet/live transport.

## Boundaries

- Public Hyperliquid mainnet candles from SV2.2 remain strategy truth.
- Depth is modeled from candle volume, never real order-book depth.
- No testnet/live strategy truth, no orders, no production or live approval.
