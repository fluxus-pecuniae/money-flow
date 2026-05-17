# Strategy Status Register

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

Every row below is explicit about evidence, paper, testnet, production, and live status. No strategy, variant, or lane is production-approved.

| strategy_family | lane_or_variant | status | evidence_status | paper_status | testnet_transport_status | production_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Current Money Flow v1.2 | `money_flow_v1_2_baseline` | `production_baseline_logic` | `SV2.0.2 canonical historical baseline` | `synthetic_paper_only` | `baseline_only_25_usdc_when_pt_rt1_5_1_gates_pass` | `not_production_approved`, `not_live_approved` | Current derivative implementation with real `sleeve_1d`; no proof of profitability. |
| SOR repair variants | `avoid_low_rolling_range_20` | `synthetic_paper_only`, `evidence_only` | `SOR-EV3 true-forward replay; promising_control_pocket_risk` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Founder review only. |
| SOR repair variants | `avoid_low_rolling_range_50` | `synthetic_paper_only`, `evidence_only` | `SOR-EV3 true-forward replay; promising_high_pnl_control_risk` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Strongest SOR review lane but still blocked. |
| SOR repair variants | fixed/ATR/recent-low/large-bear exits | `evidence_only` | `SOR-EV2 true_forward_replay` | `not_active_paper_lane` | `none` | `not_production_approved`, `not_live_approved` | No variant promoted. |
| SOR repair variants | earlier MACD / lower RSI entries | `evidence_only`, `rejected` | `SOR-EV2 true_forward_replay` | `not_active_paper_lane` | `none` | `not_production_approved`, `not_live_approved` | Admitted too many bad trades. |
| MF-ORIG source reconstruction | `mf_orig_stage_filter_only_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Source-reference comparison lane. |
| MF-ORIG source reconstruction | `mf_orig_stage2_pullback_reclaim_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Founder review lane. |
| MF-ORIG source reconstruction | `mf_orig_1d_stage2_5_20_crossover_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | 1D source-style comparison lane. |
| MF-ORIG source reconstruction | `mf_orig_1d_stage2_breakout_resistance_full_equity` | `synthetic_paper_only`, `reference_only` | `MF-ORIG-EV2 evidence-only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Strongest MF-ORIG aggregate review lane; not source-faithful risk sizing. |
| Wildcard paper-observation lanes | `wildcard_btc_regime_guard` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Observation hypothesis. |
| Wildcard paper-observation lanes | `wildcard_multi_timeframe_alignment` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Observation hypothesis. |
| Wildcard paper-observation lanes | `wildcard_volatility_expansion_breakout` | `synthetic_paper_only` | `paper_observation_only` | `synthetic_paper_only` | `cannot_send_testnet_orders` | `not_production_approved`, `not_live_approved` | Observation hypothesis. |
| SV2/SV2.1 historical evidence tracks | SV2.0.2 canonical packs | `historical_archive`, `canonical_evidence` | `canonical historical multi-timeframe baseline` | `not_runtime` | `none` | `not_production_approved`, `not_live_approved` | Backend evidence from DB-imported public candles. |
| SV2/SV2.1 historical evidence tracks | SV2.1 1D period packs | `historical_archive`, `evidence_only` | `separate founder-review 1D track` | `not_runtime` | `none` | `not_production_approved`, `not_live_approved` | Does not supersede SV2.0.2. |
| EV-AUDIT1 | full evidence audit | `audit_only` | `no clean strategy candidate` | `not_runtime` | `none` | `not_production_approved`, `not_live_approved` | Audit context only. |
| UAT/testnet plumbing | Hyperliquid testnet lifecycle | `testnet_plumbing_only` | `not_strategy_evidence` | `not_synthetic_pnl_truth` | `baseline_only_25_usdc_when_gated` | `not_production_approved`, `not_live_approved` | Testnet fills do not update synthetic PnL. |
