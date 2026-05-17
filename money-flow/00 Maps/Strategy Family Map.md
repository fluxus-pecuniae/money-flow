# Strategy Family Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the current strategy taxonomy. It separates production-derived baseline logic, source reconstruction, repair variants, paper-observation lanes, historical evidence tracks, and testnet plumbing so evidence-only work is not mistaken for production approval.

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime: `PT-RT1.5.1` smoke/review scope at `reports/paper_runtime/pt_rt1_5_1_smoke/`.
- Active timeframes: `1h`, `4h`, `1d`.
- Paused timeframes: `15m` is paused for Week 1 noise reduction and legacy review only.
- Strategy truth: public Hyperliquid mainnet fully closed candles and derived indicators.
- Synthetic PnL truth: independent synthetic 10,000 USDC paper ledgers per lane.
- Testnet plumbing: fixed 25 USDC Hyperliquid testnet transport is baseline-only and fresh-post-start only when PT-RT1.5.1 gates pass.
- Production approval: no strategy is production-approved.
- Live trading: not approved; no real-capital trading is approved.
- Next recommended action: review PT-RT1.5.1 smoke before making any strategy/paper-observation conclusion.

## Strategy Taxonomy

### SOR Repair Variants

SOR Repair Variants are evidence-only or synthetic paper-observation lanes unless a later founder-approved phase promotes one. No SOR row below is production-approved.

### STRAT-EV Discovery

STRAT-EV remains plan-only unless a committed future report and summary JSON exist. It is not current production logic and is not part of PT-RT1.5.1 transport.

| strategy_family | lane_or_variant | status | evidence_status | paper_status | testnet_transport_status | production_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Current Money Flow v1.2 | `money_flow_v1_2_baseline` | `production_baseline_logic` | `canonical_sv2_0_2_historical_baseline` | `synthetic_paper_only` | `baseline_only_25_usdc_when_pt_rt1_5_1_gates_pass` | `not_production_approved`, `not_live_approved` | Current derivative implementation with `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, `sleeve_1d`. |
| SOR repair variants | `avoid_low_rolling_range_20` | `synthetic_paper_only`, `evidence_only` | `SOR-EV3 true-forward replay; promising_control_pocket_risk` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Founder-review label only. |
| SOR repair variants | `avoid_low_rolling_range_50` | `synthetic_paper_only`, `evidence_only` | `SOR-EV3 true-forward replay; promising_high_pnl_control_risk` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Strongest SOR review lane but still control/drawdown blocked. |
| MF-ORIG source reconstruction | `mf_orig_stage_filter_only_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Original Money Flow source-reference comparison lane, not source-faithful risk sizing. |
| MF-ORIG source reconstruction | `mf_orig_stage2_pullback_reclaim_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Founder review lane only. |
| MF-ORIG source reconstruction | `mf_orig_1d_stage2_5_20_crossover_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | 1D source-style crossover comparison lane. |
| MF-ORIG source reconstruction | `mf_orig_1d_stage2_breakout_resistance_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Best MF-ORIG aggregate review lane; not production approved. |
| Wildcard paper-observation lanes | `wildcard_btc_regime_guard` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Expert-observation hypothesis, not canonical evidence. |
| Wildcard paper-observation lanes | `wildcard_multi_timeframe_alignment` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Expert-observation hypothesis, not canonical evidence. |
| Wildcard paper-observation lanes | `wildcard_volatility_expansion_breakout` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Expert-observation hypothesis, not canonical evidence. |
| SV2/SV2.1 historical evidence tracks | SV2.0.2 canonical packs | `historical_archive`, `canonical_evidence` | `canonical historical multi-timeframe baseline` | `not_runtime` | `none` | `not_production_approved`, `not_live_approved` | Backend evidence packs from DB-imported public candles. |
| SV2/SV2.1 historical evidence tracks | SV2.1 1D period evidence | `historical_archive`, `evidence_only` | `separate founder-review 1D track` | `not_runtime` | `none` | `not_production_approved`, `not_live_approved` | Does not supersede SV2.0.2. |
| UAT/testnet plumbing | Hyperliquid testnet lifecycle | `testnet_plumbing_only` | `not_strategy_evidence` | `not_synthetic_pnl_truth` | `baseline_only_25_usdc_when_gated` | `not_production_approved`, `not_live_approved` | Testnet fills do not update synthetic PnL. |

## Current 10 Paper Lanes

Each lane has an independent synthetic 10,000 USDC paper ledger. These are not one combined account.

| lane | family | active_week_status | testnet_transport |
| --- | --- | --- | --- |
| `money_flow_v1_2_baseline` | Current Money Flow v1.2 | active on `1h`, `4h`, `1d` | eligible only for fresh post-start baseline opens under PT-RT1.5.1 gates |
| `avoid_low_rolling_range_20` | SOR repair variant | active synthetic lane | cannot send testnet orders |
| `avoid_low_rolling_range_50` | SOR repair variant | active synthetic lane | cannot send testnet orders |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG reference | active synthetic lane | cannot send testnet orders |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG reference | active synthetic lane | cannot send testnet orders |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG reference | active synthetic lane | cannot send testnet orders |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG reference | active synthetic lane | cannot send testnet orders |
| `wildcard_btc_regime_guard` | wildcard observation | active synthetic lane | cannot send testnet orders |
| `wildcard_multi_timeframe_alignment` | wildcard observation | active synthetic lane | cannot send testnet orders |
| `wildcard_volatility_expansion_breakout` | wildcard observation | active synthetic lane | cannot send testnet orders |

## Active Week Timeframes

- Active: `1h`, `4h`, `1d`.
- Paused: `15m`.
- Reason: Week 1 noise reduction.
- `15m` legacy rows are archived/visible only through explicit review toggles.
- `15m` is excluded from active scoring and cannot trigger new active-week entries or testnet orders.

## Status Labels

| Label | Meaning |
| --- | --- |
| `production_baseline_logic` | Current baseline logic exists in code but is not production-approved. |
| `synthetic_paper_only` | Forward-observation ledger only, no real capital. |
| `evidence_only` | Research result, not production/paper/live approval. |
| `reference_only` | Comparison/source-reconstruction context. |
| `historical_archive` | Retained historical evidence or phase output. |
| `testnet_plumbing_only` | Sandbox/testnet lifecycle validation, not strategy truth. |
| `not_production_approved` | Cannot be treated as production strategy approval. |
| `not_live_approved` | Cannot be used for live real-capital trading. |
