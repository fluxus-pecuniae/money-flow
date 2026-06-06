# STRAT-PRUNE1 Strategy Lane Pruning

Recorded at: `2026-06-06T19:42:51Z`

Status: `completed_recommendation_only`

## Verdict

STRAT-PRUNE1 recommends reducing the next paper-observation slate to the Money Flow v1.2 baseline control plus three synthetic-only candidate lanes:

1. `money_flow_v1_2_baseline`
2. `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34`
3. `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20`
4. `avoid_low_rolling_range_20`

This is a recommendation only. The two GOAL-STRAT2 candidates are not implemented as runtime lanes in STRAT-PRUNE1. A later phase, likely `PT-RT1.6 - Add Selected Paper-Test Candidate Lanes`, should implement any selected lane changes.

No strategy is production-approved. Live trading is not approved. Candidate lanes remain synthetic-only. Only `money_flow_v1_2_baseline` may remain eligible for gated fixed-25-USDC Hyperliquid testnet plumbing under existing PT-RT gates.

## Read-Only Review Summary

The review inspected current PT-RT lane definitions, current repo and Obsidian truth, the Strategy Status Register, SOR-EV3, MF-ORIG-EV2, EV-AUDIT1, STRAT-DISC1, GOAL-STRAT1, GOAL-STRAT2, and PT-RT1.5.x runtime-boundary docs.

The current 10-lane PT-RT lab is too broad for the founder's next weekly paper run. It mixes the baseline, two SOR repair variants, four MF-ORIG full-equity reference lanes, and three wildcard diagnostics. That breadth is useful for research, but it makes weekly runtime review harder and increases dashboard/noise burden without enough evidence to justify each active lane.

Subagent use was attempted but blocked by the local agent thread limit. The review therefore proceeded locally and read-only.

## Evidence Reviewed

| Source | Use In STRAT-PRUNE1 |
| --- | --- |
| `services/paper_runtime/pt_rt1.py` | Current 10 lane definitions, active timeframe policy, testnet boundary policy. |
| `docs/sor_ev3_avoid_sideways_low_volatility.md` | Evidence for `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50`. |
| `docs/mf_orig_ev2_multitimeframe_evidence_packs.md` | Evidence for MF-ORIG source/reference lanes and their gate blockers. |
| `docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json` | Audit conclusion that no clean strategy candidate was promoted. |
| `docs/goal_strat1_strategy_discovery_summary.json` | Full autonomous discovery exhaustion, 121 configs, 0 strict candidates. |
| `docs/goal_strat2_two_non_existing_strategies_summary.json` | Two non-existing strategies worth founder paper-testing review. |
| `money-flow/10 Strategy/Strategy Status Register.md` | Current status and boundary labels for all strategy families. |
| `money-flow/00 Maps/Evidence and Backtesting Map.md` | Canonical evidence and dashboard-display boundaries. |
| `money-flow/00 Maps/Paper Observation Roadmap.md` | Current PT-RT1.5.3 active timeframe and runtime boundary truth. |

## Missing Evidence

- No completed 60-day forward-observation result exists.
- No current PT-RT1.5.3 active-week summary was used as a performance gate in this phase.
- Dashboard/runtime rows are not canonical backtest evidence.
- Candidate strategies from GOAL-STRAT2 are not yet implemented as runtime lanes, so they have no forward paper-observation rows.
- Execution-quality data remains incomplete: no order-book replay, funding, partial-fill, latency, market-impact, or live-reject modeling.

## Current Lane Inventory

| Lane | Family | Current Status | STRAT-PRUNE1 Recommendation | Reason Codes |
| --- | --- | --- | --- | --- |
| `money_flow_v1_2_baseline` | Current Money Flow v1.2 | Active control lane | `keep` | `keep_as_control`, `baseline_only_testnet_eligible`, `keep_for_forward_observation` |
| `avoid_low_rolling_range_20` | SOR repair | Active synthetic candidate | `keep` | `keep_for_forward_observation`, `useful_as_diagnostic_not_active_lane`, `candidate_synthetic_only`, `control_pocket_risk` |
| `avoid_low_rolling_range_50` | SOR repair | Active synthetic candidate | `archive_research_only` | `redundant_with_baseline`, `redundant_with_rolling_range_20`, `weak_historical_edge`, `control_pocket_risk`, `excessive_runtime_complexity` |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG reference | Active synthetic reference | `archive_research_only` | `archive_research_only`, `useful_as_diagnostic_not_active_lane`, `control_pocket_not_preserved`, `excessive_runtime_complexity` |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG reference | Active synthetic reference | `archive_research_only` | `archive_research_only`, `control_pocket_not_preserved`, `drawdown_worse_than_v1_2`, `excessive_runtime_complexity` |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG reference | Active synthetic reference | `archive_research_only` | `archive_research_only`, `control_pocket_not_preserved`, `drawdown_worse_than_v1_2`, `excessive_runtime_complexity` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG reference | Active synthetic reference | `watchlist` | `needs_more_evidence`, `useful_as_diagnostic_not_active_lane`, `control_pocket_not_preserved`, `archive_research_only` |
| `wildcard_btc_regime_guard` | Wildcard diagnostic | Active synthetic wildcard | `archive_research_only` | `useful_as_diagnostic_not_active_lane`, `missing_formal_backtest_gate`, `excessive_runtime_complexity`, `archive_research_only` |
| `wildcard_multi_timeframe_alignment` | Wildcard diagnostic | Active synthetic wildcard | `archive_research_only` | `useful_as_diagnostic_not_active_lane`, `missing_formal_backtest_gate`, `excessive_runtime_complexity`, `archive_research_only` |
| `wildcard_volatility_expansion_breakout` | Wildcard diagnostic | Active synthetic wildcard | `remove` | `overfit_or_low_sample`, `oos_instability`, `redundant_with_goal_strat_near_miss`, `reject_for_now` |

## Candidate Ranking Rubric

Candidates were ranked by:

1. Evidence quality.
2. Positive or near-positive PnL after fees/slippage.
3. Drawdown profile.
4. Out-of-sample stability.
5. Trade count and sample quality.
6. Concentration risk by symbol, timeframe, and period.
7. Runtime simplicity.
8. Founder readability.
9. Difference from baseline.
10. Whether the lane teaches something useful even if it fails.

High aggregate PnL was penalized when OOS, drawdown, control-pocket, concentration, or founder-readability risk was poor.

## Candidate Ranking Results

| Rank | Candidate | Recommendation | Evidence Notes | Caveats |
| ---: | --- | --- | --- | --- |
| 1 | `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34` | `add_candidate_for_future_phase` | GOAL-STRAT2 paper-testing candidate; active net PnL `3324.52698075`, PF `1.34770034`, 534 trades, both OOS checks positive. | Max DD `30.17%` is near the gate; ZEC/timeframe/period concentration requires monitoring. |
| 2 | `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20` | `add_candidate_for_future_phase` | GOAL-STRAT2 paper-testing candidate; active net PnL `5086.37911867`, PF `1.57118130`, max DD `16.37%`, 945 trades. | Both OOS checks are mildly negative; ZEC/timeframe/period concentration requires monitoring. |
| 3 | `avoid_low_rolling_range_20` | `keep` | SOR-EV3 directionally useful; lower-complexity low-range diagnostic; less aggressive than 50-window variant. | Still not promoted; SOR-EV3 reported control-pocket and drawdown blockers. |
| 4 | `mf_orig_1d_stage2_breakout_resistance_full_equity` | `watchlist` | Best MF-ORIG aggregate review lane; useful for source-reference comparison. | MF-ORIG-EV2 still reports control-pocket damage and worse drawdown; keep out of default active slate. |
| 5 | `avoid_low_rolling_range_50` | `archive_research_only` | Higher SOR-EV3 aggregate delta than 20-window variant. | More aggressive trade reduction and same control-pocket/drawdown blockers; redundant for next run. |

## Recommended Next Paper Slate

Default next run:

| Slot | Lane | Source | Timeframes | Paper Eligible | Testnet Eligible | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Control | `money_flow_v1_2_baseline` | Existing PT-RT lane | `1h`, `4h`, `1d` | yes | yes, gated baseline-only | Keep as the control and only testnet-eligible lane. |
| Candidate 1 | `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34` | GOAL-STRAT2 | `1h`, `4h`, `1d` | future synthetic-only | no | Implement later as a research-only lane if founder approves PT-RT1.6. |
| Candidate 2 | `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20` | GOAL-STRAT2 | `1h`, `4h`, `1d` | future synthetic-only | no | Implement later as a research-only lane if founder approves PT-RT1.6. |
| Candidate 3 | `avoid_low_rolling_range_20` | Existing PT-RT / SOR-EV3 | `1h`, `4h`, `1d` | yes | no | Retain one low-range diagnostic to compare against baseline. |

Excluded from default slate:

- `15m`, still paused.
- All MF-ORIG reference lanes.
- All wildcard lanes.
- `avoid_low_rolling_range_50`.

## Candidate Caveats

- GOAL-STRAT2 candidates are not active runtime lanes yet.
- GOAL-STRAT2 candidates were selected under a paper-testing gate, not a production-testing gate.
- The relative-strength candidate has positive OOS checks but drawdown near the paper-testing limit.
- The Donchian candidate has strong aggregate metrics but negative OOS checks.
- Both GOAL-STRAT2 candidates have material ZEC contribution and timeframe/period concentration.
- `avoid_low_rolling_range_20` is retained for diagnostic value, not because it passed production-style gates.

## Runtime Boundary Confirmation

- Public Hyperliquid mainnet candles remain strategy truth.
- Synthetic paper ledgers remain PnL truth.
- Testnet fills do not update synthetic PnL.
- Candidate, MF-ORIG, wildcard, and GOAL-STRAT2 future lanes cannot send testnet orders.
- Only `money_flow_v1_2_baseline` may remain eligible for gated fixed-25-USDC Hyperliquid testnet plumbing.
- No active runtime artifacts were changed.
- No runtime behavior was changed.
- No exchange endpoints were called.
- No orders were submitted.
- No strategy is production-approved.
- Live trading is not approved.

## Dashboard Simplification Recommendations

- Default Paper Trading to the recommended slate once a later implementation phase adds selected candidates.
- Move archived MF-ORIG and wildcard lanes under an explicit research/archive toggle.
- Keep the Weekly Scoreboard to baseline plus selected candidates by default.
- Keep `15m` hidden from active scoring and visible only as legacy/noise context.
- Label GOAL-STRAT2 candidates as `research-only synthetic paper candidate` if implemented later.
- Do not show any candidate lane as testnet-eligible.

## Risks And Blind Spots

- No forward runtime evidence exists yet for the GOAL-STRAT2 candidates.
- The selected candidates were mined from existing local historical replay data and still need forward observation.
- Historical selected-replay data does not model order-book depth, funding, liquidation, latency, partial fills, or venue rejects.
- Strong 2025-H2 and ZEC contributions may not repeat.
- Reducing the slate improves founder readability but reduces diagnostic breadth.

## Next Phase Recommendation

Scope `PT-RT1.6 - Add Selected Paper-Test Candidate Lanes`.

PT-RT1.6 should:

- Add the two GOAL-STRAT2 candidates as synthetic-only paper lanes.
- Keep `avoid_low_rolling_range_20` if founder wants one SOR diagnostic comparator.
- Archive the removed/reference lanes from the default active view without deleting historical evidence.
- Preserve `1h`, `4h`, and `1d` only.
- Keep `15m` paused.
- Keep candidate lanes testnet-ineligible.
- Keep baseline-only fixed-25-USDC testnet plumbing eligibility.
- Preserve warm-start, duplicate, closed-candle, data-health, and MTM gates.

STRAT-PRUNE1 implements none of those runtime changes.
