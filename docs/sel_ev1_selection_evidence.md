# SEL-EV1 Cross-Sectional Breakout Selection Evidence

## Verdict

- **Verdict: `no_selection_skill_demonstrated`**
- Gate reason codes: `oos_net_pnl_not_positive_post_friction`, `does_not_beat_random_selection_oos`
- The bar is beating a matched-cadence random-selection benchmark out-of-sample after conservative depth-aware friction — not raw PnL.
- Research/evidence only: no runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval.

## Strategy-Type Routing Seam (Must 0)

- `per_symbol` (approach a — Money Flow / MF-ORIG / avoid_low lanes) and `cross_sectional_selection` (approach b — this phase) are parallel research tracks with separate simulators, gates, and evaluations.
- The per-symbol breadth/anti-concentration gate never judges a selection strategy (point-in-time concentration is the design here), and the selection random-benchmark gate never judges a per-symbol strategy. Cross-application raises `StrategyTypeRoutingError`.
- Per-symbol lane behavior and results are unchanged (byte-identical regression check in `tests/test_sel_ev1_selection_evidence.py`).

## Hypothesis + Mechanics (Must 1-2)

- Universe: founder 23-symbol Hyperliquid set over SV2.2 public-mainnet candles; timeframes ['1d', '4h'].
- At each closed candle: score every symbol point-in-time, rank, hold the top-1 / top-3 (score must be > 0), enter at the NEXT candle open, hold while still top-ranked, rotate/exit otherwise; ATR(14) x 2.8 trailing stop.
- Signals (bounded; train-only choice): `donchian_breakout_strength` = (close - prior N-high) / ATR; `vol_adjusted_relative_momentum` = N-return / (ATR/close); lookbacks [20, 40].
- Sizing (explicit): fixed fraction of current equity per held name — top-1 -> 50%, top-3 -> 30% each. Never full-equity-on-one-name (the ZEC inflater).
- Friction: EXEC-EV1 depth-aware model on EVERY entry/exit/rotation fill (tier half-spread + sqrt participation impact + fill-probability chase on top of SV2.3 fee/slippage/adverse-gap). Depth is MODELED from candle volume, not real.
- OOS: chronological 70/30 split at `2025-09-28T16:00:00Z`; anchored walk-forward thirds; parameters chosen on train only.

## Headline — Strategy vs Random Selection (OOS, post-conservative-friction)

- Train-chosen config: `sel_ev1_vol_adjusted_relative_momentum_lb40_top3_1d` (best train net PnL).
- Strategy OOS net PnL: `-10459.81356118` over `84` trades.
- Random-selection OOS distribution (50 seeds, matched cadence): median `-4717.25806003`, mean `-5410.88476810`, p95 `-2940.68240647` (bar), max `-2105.38015737`.
- Random seeds beaten: `2` of `50`; empirical p-value vs random: `0.96078431`.
- Equal-weight buy-and-hold (OOS window): `-2146.90052646`.
- Naive highest-past-return top-1 (OOS): `43153.52734631`.
- Anchored walk-forward thirds combined test net: `15808.94442658`.

## Rotation / Diversity (reframed ZEC check)

- Distinct symbols held: `23`; rotations: `378`.
- Max single-symbol time-in-position share: `0.13163574` (threshold `0.50`).
- Max single-symbol positive-PnL share: `0.45789910` (threshold `0.60`).
- Single-name bet flag: `False`.

## Bounded Grid (conservative friction; train / OOS by entry time)

| Config | Train net | OOS net | OOS trades | Distinct symbols | Single-name? |
| --- | ---: | ---: | ---: | ---: | --- |
| `sel_ev1_donchian_breakout_strength_lb20_top1_1d` | `-2048.06435273` | `13700.37668215` | `65` | `23` | `False` |
| `sel_ev1_donchian_breakout_strength_lb20_top1_4h` | `-7093.51969370` | `-1608.06628053` | `420` | `23` | `False` |
| `sel_ev1_donchian_breakout_strength_lb20_top3_1d` | `300.50292446` | `7559.54623217` | `104` | `23` | `False` |
| `sel_ev1_donchian_breakout_strength_lb20_top3_4h` | `-7096.97989164` | `-1423.77943230` | `678` | `23` | `False` |
| `sel_ev1_donchian_breakout_strength_lb40_top1_1d` | `-2723.01471688` | `10434.03564176` | `48` | `22` | `False` |
| `sel_ev1_donchian_breakout_strength_lb40_top1_4h` | `-3887.21262390` | `-1862.49561355` | `302` | `23` | `False` |
| `sel_ev1_donchian_breakout_strength_lb40_top3_1d` | `3355.55624268` | `7465.31058296` | `69` | `22` | `False` |
| `sel_ev1_donchian_breakout_strength_lb40_top3_4h` | `-4375.53170388` | `-1921.34604749` | `458` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb20_top1_1d` | `3586.00045114` | `42023.76159031` | `63` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb20_top1_4h` | `-5684.45413862` | `651.21008030` | `399` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb20_top3_1d` | `40524.15907929` | `-24875.60251591` | `146` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb20_top3_4h` | `-6977.91952270` | `-1139.76958069` | `897` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb40_top1_1d` | `37231.89526423` | `1772.63668447` | `31` | `19` | `True` |
| `sel_ev1_vol_adjusted_relative_momentum_lb40_top1_4h` | `-5152.36921456` | `-569.10427145` | `302` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb40_top3_1d` | `54291.56890894` | `-10459.81356118` | `84` | `23` | `False` |
| `sel_ev1_vol_adjusted_relative_momentum_lb40_top3_4h` | `-4624.89955242` | `-2472.82914824` | `665` | `23` | `False` |

## Friction Impact (chosen config across EXEC-EV1 scenarios)

| Scenario | Full net | OOS net | Avg friction bps | Friction paid (quote) |
| --- | ---: | ---: | ---: | ---: |
| `exec_ev1_base` | `58295.22857379` | `-9678.23644889` | `8.68290438` | `4961.01838601` |
| `exec_ev1_conservative` | `43831.75534776` | `-10459.81356118` | `20.20134486` | `9733.64845651` |
| `exec_ev1_stress` | `26209.80545391` | `-10245.19835018` | `39.41998873` | `14568.78493391` |

## Late-Entry Sensitivity (Must 5; chosen config, conservative friction)

Selection chases breakouts, so entry timing is acute. `+k` = filled k candles
after the normal next-open fill. Connects to the RT-HISTSEED1 question.

| Lateness | Full net | OOS net | Avg entry-timing cost bps |
| --- | ---: | ---: | ---: |
| `+0` | `43831.75534776` | `-10459.81356118` | `-0.79641745` |
| `+1` | `17365.54034278` | `-10124.61409564` | `55.24030197` |
| `+2` | `12333.53025135` | `-3327.64831188` | `41.31865044` |

## Boundaries

- `research_only`: `True`
- `changes_production_money_flow_rules`: `False`
- `changes_per_symbol_lane_behavior_or_results`: `False`
- `mutates_active_pt_rt_runtime`: `False`
- `mutates_runtime_artifacts`: `False`
- `creates_order_intent`: `False`
- `creates_prepared_venue_order`: `False`
- `creates_submitted_order`: `False`
- `submits_live_orders`: `False`
- `submits_testnet_orders`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `uses_testnet_data_as_strategy_truth`: `False`
- `approves_live_trading`: `False`
- `approves_production_strategy`: `False`
- `modeled_depth_not_real`: `True`

## Honest Caveats

- Depth/liquidity is modeled from historical candle volume, never real order-book depth; every cost is an assumption.
- A single historical period; OOS here is still one market regime.
- The random benchmark shares the strategy's trade cadence; it does not answer whether the *cadence itself* (vs buy-and-hold) is wise.
- If the verdict is `no_selection_skill_demonstrated`, that is a real result on a genuinely new hypothesis, not a failure of the harness.
