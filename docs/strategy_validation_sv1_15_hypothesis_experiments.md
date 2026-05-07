# SV1.15 Controlled Money Flow Hypothesis Experiments

Recorded at: `2026-05-07T20:25:10Z`

Status: `controlled_hypothesis_experiments_ready_for_founder_review`

This report is research-only. It tests SV1.14 hypotheses as isolated Strategy Validation variants. No production Money Flow rules changed, no parameters were optimized globally, no routing/execution artifacts were created, and paper/live trading remains deferred.

Scope: Hyperliquid USDC perpetual public-candle research only. Main comparisons use `dynamic_equity_pct`; each scenario remains independent and is not one combined account.

## Methodology Truth

SV1.15.1 is a methodology-truth hotfix. Most SV1.15 variants are completed-trade overlay diagnostics, not true candle-by-candle strategy replays.

Completed-trade overlays filter or adjust already-completed baseline trades. They do not admit new alternative trades, do not fully model changed position occupancy, do not fully model changed future capital after skipped entries, and do not fully model exact earlier exit fills. They are useful for ranking hypotheses for later replay work, not for authorizing rules.

The `recent_low_invalidation_proxy_20c` result is a `lookahead_diagnostic_proxy`: it estimates an upper-bound diagnostic from completed baseline losers and is not a forward-tradable result. Exact earlier exit timing and fill modeling must be replayed before it can be considered for later candidate review.

## Baseline

Baseline is current Money Flow rules with `dynamic_equity_pct` sizing.

| Component | Scenario Count | Start Equity Sum | Ending Equity Sum | Net Account PnL Sum | Min Ending Equity | Max Drawdown | Trade Count |
|---|---:|---:|---:|---:|---:|---:|---:|
| sleeve_15m | 36 | $360,000.00 | $274,061.42 | $-85,938.58 | $6,459.22 | $3,645.61 | 7660 |
| sleeve_1h | 36 | $360,000.00 | $381,997.91 | $21,997.91 | $8,313.22 | $2,150.85 | 4484 |
| sleeve_4h | 36 | $360,000.00 | $287,620.62 | $-72,379.38 | $6,772.35 | $3,492.34 | 1280 |

## Experiment List

| Variant | Type | Methodology | Applies To | Status | Research Boundary |
|---|---|---|---|---|---|
| `resistance_proximity_0_25pct` | entry_filter | `completed_trade_overlay_estimate` | sleeve_15m,sleeve_1h,sleeve_4h | experimental | research_only=true, changes_rules=false |
| `resistance_proximity_0_50pct` | entry_filter | `completed_trade_overlay_estimate` | sleeve_15m,sleeve_1h,sleeve_4h | experimental | research_only=true, changes_rules=false |
| `higher_low_confirmation_20c` | entry_filter | `completed_trade_overlay_estimate` | sleeve_15m,sleeve_1h | experimental | research_only=true, changes_rules=false |
| `recent_low_invalidation_proxy_20c` | exit_filter | `lookahead_diagnostic_proxy` | sleeve_1h,sleeve_4h | diagnostic_upper_bound_requires_forward_replay | research_only=true, changes_rules=false |
| `sideways_regime_avoidance_15m` | entry_filter | `completed_trade_overlay_estimate` | sleeve_15m | experimental | research_only=true, changes_rules=false |
| `extension_limit_4h_2_0pct` | entry_filter | `completed_trade_overlay_estimate` | sleeve_4h | experimental | research_only=true, changes_rules=false |
| `extension_limit_4h_1_5pct` | entry_filter | `completed_trade_overlay_estimate` | sleeve_4h | experimental | research_only=true, changes_rules=false |
| `lower_half_rsi_attribution` | reporting_only_attribution | `reporting_only_attribution` | sleeve_15m,sleeve_1h,sleeve_4h | candidate_for_later_validation | research_only=true, changes_rules=false |
| `pullback_vs_continuation_attribution` | reporting_only_attribution | `reporting_only_attribution` | sleeve_15m,sleeve_1h,sleeve_4h | candidate_for_later_validation | research_only=true, changes_rules=false |
| `lower_rsi_floor_expansion_replay_required` | experimental_entry_variant | `deferred_requires_rejected_signal_replay` | sleeve_15m,sleeve_1h,sleeve_4h | needs_more_evidence | research_only=true, changes_rules=false |
| `lower_rsi_pullback_trend_intact_replay_required` | experimental_entry_variant | `deferred_requires_rejected_signal_replay` | sleeve_15m,sleeve_1h,sleeve_4h | needs_more_evidence | research_only=true, changes_rules=false |

## One-Change-At-A-Time Comparison

Grouped rows below are sums across independent research scenarios, not one account result.

| Variant | Methodology | Scenarios | Baseline Net Sum | Variant Net Sum | Delta | Baseline Drawdown | Variant Drawdown | Baseline Trades | Variant Trades | Filtered Trades | Losing Trades Avoided | Winning Trades Missed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `extension_limit_4h_1_5pct` | `completed_trade_overlay_estimate` | 36 | $-72,379.38 | $-41,687.13 | $30,692.25 | $3,492.34 | $2,179.32 | 1280 | 1040 | 240 | 196 | 44 |
| `extension_limit_4h_2_0pct` | `completed_trade_overlay_estimate` | 36 | $-72,379.38 | $-66,323.01 | $6,056.37 | $3,492.34 | $3,093.98 | 1280 | 1208 | 72 | 52 | 20 |
| `higher_low_confirmation_20c` | `completed_trade_overlay_estimate` | 72 | $-63,940.66 | $-81,652.17 | $-17,711.51 | $3,645.61 | $3,645.61 | 12144 | 11736 | 408 | 251 | 157 |
| `recent_low_invalidation_proxy_20c` | `lookahead_diagnostic_proxy` | 72 | $-50,381.47 | $247,743.31 | $298,124.78 | $3,492.34 | $1,937.18 | 5764 | 3676 | 2088 | 2088 | 0 |
| `resistance_proximity_0_25pct` | `completed_trade_overlay_estimate` | 108 | $-136,320.05 | $-107,096.22 | $29,223.83 | $3,645.61 | $3,492.34 | 13424 | 10450 | 2974 | 2251 | 723 |
| `resistance_proximity_0_50pct` | `completed_trade_overlay_estimate` | 108 | $-136,320.05 | $-100,502.45 | $35,817.60 | $3,645.61 | $3,492.34 | 13424 | 7812 | 5612 | 4234 | 1378 |
| `sideways_regime_avoidance_15m` | `completed_trade_overlay_estimate` | 36 | $-85,938.58 | $-6,258.54 | $79,680.04 | $3,645.61 | $600.73 | 7660 | 672 | 6988 | 5459 | 1529 |

## ETH 1h Preservation

ETH `sleeve_1h` is the baseline pocket that variants must avoid damaging before later validation.

| Variant | ETH 1h Scenarios | Baseline Net Sum | Variant Net Sum | Delta | Baseline Trades | Variant Trades | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `higher_low_confirmation_20c` | 12 | $27,143.25 | $20,406.69 | $-6,736.57 | 1396 | 1224 | eth_1h_deteriorated |
| `recent_low_invalidation_proxy_20c` | 12 | $27,143.25 | $118,927.38 | $91,784.13 | 1396 | 795 | eth_1h_preserved_or_improved |
| `resistance_proximity_0_25pct` | 12 | $27,143.25 | $26,599.19 | $-544.06 | 1396 | 1246 | eth_1h_deteriorated |
| `resistance_proximity_0_50pct` | 12 | $27,143.25 | $3,727.39 | $-23,415.86 | 1396 | 1100 | eth_1h_deteriorated |

## Lower-RSI Experiment Section

Current production Money Flow does not enter below the RSI sleeve floor. SV1.15 keeps that unchanged.

### Lower-Half RSI Attribution Inside Current Band

| Component | Symbol | RSI Zone | Trades | Net PnL | Win Rate | Avg MAE | Avg MFE |
|---|---|---|---:|---:|---:|---:|---:|
| sleeve_15m | BTC | `lower_band_half` | 1588 | $-8,676.02 | 26.13% | $-22.10 | $42.68 |
| sleeve_15m | BTC | `near_upper_band` | 352 | $-7,561.71 | 10.80% | $-31.70 | $32.13 |
| sleeve_15m | BTC | `upper_band_half` | 676 | $-10,876.84 | 21.15% | $-29.89 | $38.50 |
| sleeve_15m | ETH | `lower_band_half` | 1640 | $-18,143.52 | 21.22% | $-29.28 | $44.20 |
| sleeve_15m | ETH | `near_upper_band` | 216 | $-2,392.00 | 15.74% | $-39.77 | $52.09 |
| sleeve_15m | ETH | `upper_band_half` | 644 | $-6,375.63 | 28.26% | $-38.16 | $52.28 |
| sleeve_15m | SOL | `lower_band_half` | 1648 | $-19,456.69 | 21.24% | $-28.37 | $44.32 |
| sleeve_15m | SOL | `near_upper_band` | 228 | $2,258.95 | 31.58% | $-33.50 | $73.92 |
| sleeve_15m | SOL | `upper_band_half` | 668 | $-14,715.12 | 23.20% | $-37.30 | $46.07 |
| sleeve_1h | BTC | `lower_band_half` | 1164 | $612.59 | 26.72% | $-57.79 | $103.09 |
| sleeve_1h | BTC | `near_upper_band` | 108 | $-2,512.85 | 48.15% | $-91.30 | $91.14 |
| sleeve_1h | BTC | `upper_band_half` | 336 | $449.35 | 29.17% | $-54.34 | $104.97 |
| sleeve_1h | ETH | `lower_band_half` | 928 | $11,829.99 | 34.48% | $-71.89 | $146.54 |
| sleeve_1h | ETH | `near_upper_band` | 72 | $-4,765.64 | 33.33% | $-156.49 | $113.42 |
| sleeve_1h | ETH | `upper_band_half` | 396 | $20,078.91 | 45.96% | $-93.44 | $215.92 |
| sleeve_1h | SOL | `lower_band_half` | 992 | $-15,770.79 | 29.84% | $-87.03 | $128.23 |
| sleeve_1h | SOL | `near_upper_band` | 144 | $-3,323.87 | 30.56% | $-103.10 | $114.49 |
| sleeve_1h | SOL | `upper_band_half` | 344 | $15,400.22 | 51.45% | $-78.89 | $225.29 |
| sleeve_4h | BTC | `lower_band_half` | 312 | $-5,393.08 | 37.18% | $-120.72 | $210.34 |
| sleeve_4h | BTC | `near_upper_band` | 60 | $-866.26 | 40.00% | $-108.95 | $173.22 |
| sleeve_4h | BTC | `upper_band_half` | 80 | $-5,396.33 | 15.00% | $-121.32 | $145.13 |
| sleeve_4h | ETH | `lower_band_half` | 252 | $-10,536.85 | 26.98% | $-146.74 | $244.85 |
| sleeve_4h | ETH | `near_upper_band` | 60 | $-5,881.98 | 26.67% | $-249.94 | $206.35 |
| sleeve_4h | ETH | `upper_band_half` | 92 | $-8,113.59 | 20.65% | $-152.14 | $206.22 |
| sleeve_4h | SOL | `lower_band_half` | 328 | $-16,546.83 | 31.71% | $-134.69 | $230.28 |
| sleeve_4h | SOL | `near_upper_band` | 24 | $-7,365.83 | 33.33% | $-348.89 | $251.83 |
| sleeve_4h | SOL | `upper_band_half` | 72 | $-12,278.63 | 0.00% | $-212.33 | $124.98 |

### Lower RSI Floor Expansion / Pullback Variants

- Status: `partially_deferred_to_replay_instrumentation`
- Reason: Existing evidence packs contain completed trades and aggregate no-trade reason counts, but not every rejected candle's full indicator/market-structure snapshot. SV1.15 tests RSI-zone attribution from completed trades and records lower-floor entry variants as experimental designs; full admission of new lower-RSI trades needs a later replay runner that persists per-candle rejected-signal features.
- Risk: Lower RSI can improve pullback pricing only if trend stack and support context remain intact; otherwise it can add falling-knife entries.
- Lower RSI variants remain research-only. They are not production rules and are not paper/live authorization.

## Pullback vs Continuation Attribution

| Component | Symbol | Entry Style | Trades | Net PnL | Win Rate |
|---|---|---|---:|---:|---:|
| sleeve_15m | BTC | `continuation` | 36 | $272.32 | 41.67% |
| sleeve_15m | BTC | `pullback` | 2580 | $-27,386.89 | 22.52% |
| sleeve_15m | ETH | `continuation` | 72 | $-2,017.63 | 33.33% |
| sleeve_15m | ETH | `pullback` | 2428 | $-24,893.52 | 22.24% |
| sleeve_15m | SOL | `continuation` | 192 | $2,002.19 | 43.23% |
| sleeve_15m | SOL | `pullback` | 2352 | $-33,915.06 | 21.00% |
| sleeve_1h | BTC | `continuation` | 276 | $292.99 | 33.33% |
| sleeve_1h | BTC | `pullback` | 1332 | $-1,743.90 | 27.70% |
| sleeve_1h | ETH | `continuation` | 456 | $25,257.68 | 44.74% |
| sleeve_1h | ETH | `pullback` | 940 | $1,885.57 | 34.26% |
| sleeve_1h | SOL | `continuation` | 596 | $11,594.06 | 41.95% |
| sleeve_1h | SOL | `pullback` | 884 | $-15,288.49 | 30.20% |
| sleeve_4h | BTC | `continuation` | 244 | $-18,385.52 | 27.87% |
| sleeve_4h | BTC | `pullback` | 208 | $6,729.85 | 40.38% |
| sleeve_4h | ETH | `continuation` | 240 | $-26,132.26 | 16.67% |
| sleeve_4h | ETH | `pullback` | 164 | $1,599.84 | 38.41% |
| sleeve_4h | SOL | `continuation` | 268 | $-35,531.19 | 22.39% |
| sleeve_4h | SOL | `pullback` | 156 | $-660.10 | 33.33% |

## Hypothesis Status

| Bucket | Hypotheses |
|---|---|
| `diagnostic_overlay_improved_needs_true_replay` | `extension_limit_4h_1_5pct`, `extension_limit_4h_2_0pct`, `resistance_proximity_0_25pct`, `resistance_proximity_0_50pct`, `sideways_regime_avoidance_15m` |
| `diagnostic_overlay_deteriorated_or_overfiltered` | `higher_low_confirmation_20c` |
| `lookahead_proxy_upper_bound_not_candidate` | `recent_low_invalidation_proxy_20c` |
| `reporting_attribution_only` | `lower_half_rsi_attribution`, `pullback_vs_continuation_attribution` |
| `deferred_requires_rejected_signal_replay` | `lower_rsi_floor_expansion_replay_required`, `lower_rsi_pullback_trend_intact_replay_required` |
| `not_authorized` | `extension_limit_4h_1_5pct`, `extension_limit_4h_2_0pct`, `higher_low_confirmation_20c`, `lower_half_rsi_attribution`, `lower_rsi_floor_expansion_replay_required`, `lower_rsi_pullback_trend_intact_replay_required`, `pullback_vs_continuation_attribution`, `recent_low_invalidation_proxy_20c`, `resistance_proximity_0_25pct`, `resistance_proximity_0_50pct`, `sideways_regime_avoidance_15m` |

## What Each Hypothesis Needs Before Rule Testing

| Hypothesis | Needed Before Rule Testing |
|---|---|
| `resistance_proximity` | Build a true replay entry filter and test whether skipped entries alter later signal availability, position occupancy, and capital path. |
| `sideways_regime_avoidance_15m` | Build a true replay regime gate and confirm it does not simply remove nearly all 15m activity or miss early trend transitions. |
| `extension_limit_4h` | Build a true replay entry filter, test longer windows, and verify late-entry control without over-removing durable trend participation. |
| `higher_low_confirmation` | Redesign before replay; the completed-trade overlay deteriorated ETH 1h and may over-filter constructive momentum pockets. |
| `recent_low_invalidation` | Build real exit replay with actual stop time, fill timing, slippage, capital path, and missed-recovery accounting. Current result is an upper-bound diagnostic only. |
| `lower_rsi` | Add rejected-signal replay instrumentation with per-candle indicator and market-structure snapshots before below-floor entry admission can be tested. |

## Interpretation Boundaries

- Completed-trade overlay deltas are methodology-limited research observations only.
- The recent-low invalidation proxy is a lookahead diagnostic upper bound, not a candidate rule result.
- No hypothesis receives authorization for production, paper trading, or live trading.
- Lower RSI can represent constructive pullback pricing only when trend and support context remain intact; otherwise it can add falling-knife risk.
- Full lower-RSI entry admission is intentionally deferred until the replay runner can persist rejected-candle feature rows.

## Boundary Flags

- `changes_production_money_flow_rules`: `false`
- `optimizes_parameters_globally`: `false`
- `approves_paper_trading`: `false`
- `creates_paper_trading_artifacts`: `false`
- `creates_live_artifacts`: `false`
- `creates_routing_artifacts`: `false`
- `calls_exchange_adapters`: `false`
- `calls_private_or_signed_exchange_endpoints`: `false`
- `calls_exchange_order_endpoints`: `false`
- `uses_api_keys`: `false`
- `uses_dynamic_equity_in_main_report`: `true`

## Deferred Work

- Build a per-candle rejected-signal replay runner before adding new lower-RSI entry-admission tests.
- Build true forward replay for entry filters so skipped entries, position occupancy, and capital path are modeled.
- Build real exit replay for recent-low invalidation with actual stop time and fill assumptions.
- Validate any candidate on additional windows before considering a separate founder-scoped paper-design phase.
- Keep Aster/Binance/OKX/Coinbase/Kraken outside this Hyperliquid-only experiment result.
