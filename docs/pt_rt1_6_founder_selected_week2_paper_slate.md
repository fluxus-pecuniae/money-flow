# PT-RT1.6 Founder-Selected Week 2 Paper Slate

Recorded at: 2026-06-06T22:24:15Z

## Verdict

PT-RT1.6 prepares the founder-selected Week 2 paper slate. The runtime is not started by this phase.

Default active Week 2 paper lanes:

- `money_flow_v1_2_baseline`
- `avoid_low_rolling_range_20`
- `mf_orig_1d_stage2_breakout_resistance_full_equity`

Archived/default-inactive lanes:

- `avoid_low_rolling_range_50`
- `mf_orig_stage_filter_only_full_equity`
- `mf_orig_stage2_pullback_reclaim_full_equity`
- `mf_orig_1d_stage2_5_20_crossover_full_equity`
- `wildcard_btc_regime_guard`
- `wildcard_multi_timeframe_alignment`
- `wildcard_volatility_expansion_breakout`

## Active Timeframes

Active paper-observation timeframes remain:

- `1h`
- `4h`
- `1d`

`15m` remains paused as `diagnostic_only` and `not_active_paper_scoring`.

## Lane Boundaries

`money_flow_v1_2_baseline` remains the only testnet-eligible lane when gated testnet transport is explicitly enabled for a later run.

`avoid_low_rolling_range_20` and `mf_orig_1d_stage2_breakout_resistance_full_equity` are synthetic-only. Archived lanes are default-inactive and not testnet eligible.

No strategy is production-approved. Live trading is not approved.

## Dashboard Cleanup

The Paper Trading dashboard now prefers the Week 2 runtime scope:

`reports/paper_runtime/pt_rt1_6_week2_active/`

Default dashboard behavior:

- Shows the three selected active lanes by default.
- Hides archived/default-inactive lanes from active scoring.
- Shows archived lanes as historical/research references only.
- Labels PnL as Synthetic Ledger.
- Labels signal truth as Public Mainnet Candles.
- Keeps testnet lifecycle separate from synthetic trades and PnL.
- Shows `No active paper run detected` unless the local control server reports a running process.
- Warns that stale runtime artifacts are not proof of an active run.

## Runtime Start Command

PT-RT1.6 does not start the runtime. After founder review, the documented command is:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_6_week2_active \
  --pt-rt1-5-week1-active \
  --signal-evaluation-mode candle_close_only \
  --fresh-signal-only-after-runtime-start \
  --enable-baseline-testnet-transport \
  --founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --public-mainnet-only
```

The dashboard control server defaults to the same Week 2 output scope when the founder explicitly starts a run from the UI.

## Boundaries

- Public Hyperliquid mainnet candles remain strategy truth.
- Synthetic paper ledgers remain PnL truth.
- Testnet fills do not update synthetic PnL.
- Candidate/MF-ORIG lanes remain synthetic-only.
- Only `money_flow_v1_2_baseline` is testnet eligible.
- No live trading was approved.
- No strategy was production-approved.
- No orders were submitted.
- The runtime was not started.

## Next Phase

After review, the founder may start the PT-RT1.6 Week 2 paper run. A later phase can evaluate Week 2 artifacts or perform destructive cleanup of unused strategy code only after the new run starts cleanly.
