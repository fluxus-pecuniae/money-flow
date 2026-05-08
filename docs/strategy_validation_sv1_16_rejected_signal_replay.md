# SV1.16 Rejected-Signal Replay Instrumentation

Recorded at: `2026-05-08T06:06:02Z`

Status: `replay_substrate_ready_for_founder_review`

This report is research-only. SV1.16 records per-candle production-rule decision context and runs a narrow lower-RSI true replay example without changing production Money Flow rules, approving paper trading, adding live execution, routing, or calling exchange endpoints.

## Methodology

- Replay context methodology: `per_candle_true_replay_context_research_only`
- Each evaluated candle records production-rule action/reason context in the current replay state, RSI zone, indicator values, regime labels, and descriptive market-structure context.
- SV1.16.1 terminology: `production_rule_*_in_replay_state` means current Money Flow rule evaluation under the active replay state. In a variant run, once a variant-only entry is admitted, later production-rule evaluations are in the variant state rather than an independent baseline path.
- Legacy `baseline_*` fields remain as compatibility aliases for production-rule evaluation, but founder interpretation should use the clearer production-rule-in-replay-state fields.
- Rejected production-rule entry candles are retained so later lower-RSI variants can be tested from candles rather than completed-trade overlays.
- True replay maintains position occupancy and dynamic-equity path inside each independent scenario.
- This is not full margin, funding, liquidation, order-book, or portfolio simulation.

## Baseline Replay Parity

- Focused SV1.16 tests compare the baseline true replay against the existing Strategy Validation backtest on a deterministic fixture.
- The parity check covers trade count, entry times, exit times, net account PnL, and ending equity.
- If a future replay variant cannot preserve baseline parity, its founder-facing output must be treated as instrumentation-only until the mismatch is resolved.

## Baseline Vs Lower-RSI Trend-Intact Replay

| Component | Variant | Contexts | Trades | Ending Equity | Net Account PnL | Rejected Entries | Variant Candidates | Variant Entries |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sleeve_1h | `baseline_current_money_flow_rules` | 2976 | 117 | $11,388.93 | $1,388.93 | 2055 | 0 | 0 |
| sleeve_1h | `lower_rsi_floor_trend_intact_v1` | 2976 | 137 | $10,902.09 | $902.09 | 2011 | 1428 | 29 |

## SV1.16.1 Replay Methodology Truth

- Variant replay can diverge from the baseline path after a variant admits a candle that production rules rejected.
- The current SV1.16.1 report does not compute an independent per-candle baseline reference path after that divergence; it reports production-rule evaluation in the current replay state.
- Production-rule rejection counts are separated from variant no-trade truth.
- If production rules reject a candle and the variant admits it, that candle is counted under `variant_admitted_from_rejection_reason_counts`, not as a variant no-trade.
- The lower-RSI result remains a sampled research replay result, not a production rule, not paper trading authorization, and not live trading authorization.

## Variant Counter Separation

| Component | Variant | Production-Rule Rejections In Replay State | Admitted From Rejection | Variant No-Trade Reasons | Variant Rejected Candidates |
|---|---|---|---|---|---|
| sleeve_1h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=88 | `rsi_not_constructive`=29 | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=59 | `variant_candidate_rejected`=1399 |

## Rejected-Signal Summary

| Component | Variant | Top Rejection Reasons | RSI Zone Counts |
|---|---|---|---|
| sleeve_1h | `lower_rsi_floor_trend_intact_v1` | `bearish_alignment`=1690, `entry_quality_not_constructive`=10, `macd_not_constructive`=174, `overextended_rsi`=49, `rsi_not_constructive`=88 | `above_ceiling`=245, `below_floor`=1533, `lower_band_half`=726, `near_upper_band`=126, `unknown`=34, `upper_band_half`=312 |

## Lower-RSI Variant Boundary

- Variant id: `lower_rsi_floor_trend_intact_v1`
- It admits below-floor RSI candidates only in the Strategy Validation replay path.
- It still requires trend-intact context, constructive MACD, non-extended price, and pullback/support context.
- It is not a production rule, not a recommendation, and not paper/live authorization.

## Boundary Flags

- `approves_paper_trading`: `False`
- `calls_exchange_adapters`: `False`
- `changes_production_money_flow_rules`: `False`
- `creates_live_artifacts`: `False`
- `creates_routing_artifacts`: `False`
- `optimizes_parameters`: `False`
- `research_only`: `True`

## Deferred Work

- Add more true replay variants only after founder review of this substrate.
- Add exact stop/exit replay for recent-low invalidation separately.
- Add broader windows/out-of-sample checks before any later paper-trading design phase.
- Keep Aster/Binance/OKX/Coinbase/Kraken outside this Hyperliquid-only replay result.
