# OBS-OS1 Week 2 Paper Observation Operating System

## Verdict

OBS-OS1 adds a read-only daily review and anomaly-flag layer for the Week 2 paper runtime scope `pt_rt1_6_week2_active`.

The operating system does not change runtime behavior, start or stop the runtime, submit orders, approve live trading, approve production strategy, or mutate runtime artifacts.

## Objective

The founder needed a lightweight operating cadence for Week 2 paper observation: one command to summarize the current runtime logs, identify anomalies, and produce a dashboard-readable review pack without waiting for Codex to manually inspect every JSONL file.

OBS-OS1 provides:

- A read-only generator: `scripts/build_pt_rt_week2_daily_review.py`
- Ignored daily outputs under `reports/paper_reviews/pt_rt1_6_week2_active/`
- A dashboard panel: `Daily Review / Anomaly Flags`
- Focused tests for report generation, boundary flags, and fail-soft missing-file behavior

## Commands

Status check without writing files:

```bash
.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --status --scope pt_rt1_6_week2_active
```

Generate the latest daily pack:

```bash
.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate --scope pt_rt1_6_week2_active
```

Default output files:

```text
reports/paper_reviews/pt_rt1_6_week2_active/YYYY-MM-DD_daily_review.json
reports/paper_reviews/pt_rt1_6_week2_active/YYYY-MM-DD_daily_review.md
reports/paper_reviews/pt_rt1_6_week2_active/latest_review.json
reports/paper_reviews/pt_rt1_6_week2_active/latest_review.md
```

These outputs are ignored by Git and excluded from review bundles.

## Runtime Inputs

The generator reads the active runtime scope only:

```text
reports/paper_runtime/pt_rt1_6_week2_active/
```

Read inputs:

- `summary.json`
- `state.json`
- `decisions.jsonl`
- `trades.jsonl`
- `testnet_order_lifecycle.jsonl`
- `runtime_audit.jsonl`
- `data_health.json`

Missing inputs are reported as review flags. Missing files do not cause the generator to fabricate metrics.

## Week 2 Truth

Active lanes:

```text
money_flow_v1_2_baseline
avoid_low_rolling_range_20
mf_orig_1d_stage2_breakout_resistance_full_equity
```

Active timeframes:

```text
1h
4h
1d
```

Disabled timeframe:

```text
15m
```

Only `money_flow_v1_2_baseline` is testnet eligible. Candidate and MF-ORIG lanes remain synthetic-only. Testnet fills do not update synthetic PnL.

## Anomaly Flags

OBS-OS1 reports anomaly flags with severity, code, detail, and review action.

Initial flag groups include:

- Missing or stale runtime files
- No detected runtime process
- No recent decisions
- No closed trades yet
- New 15m active rows
- Candidate-lane testnet lifecycle rows
- Unknown testnet state
- Missing cancel/reconcile after submitted/open lifecycle state
- Suspicious synthetic PnL update from testnet
- Duplicate-signal spikes
- Warm-start block spikes
- Large unrealized losses
- Lane drawdown review thresholds

Flags are review guidance, not production approval or live-trading controls.

## Dashboard Panel

Paper Trading now has a lower-priority panel:

```text
Daily Review / Anomaly Flags
```

The panel loads:

```text
reports/paper_reviews/pt_rt1_6_week2_active/latest_review.json
```

If no generated review is present, it shows an explicit empty state and the command to generate a pack. The panel displays runtime scope, generated timestamp, go/no-go label, decision/trade/lifecycle counts, critical/warning flag counts, synthetic PnL truth, testnet PnL boundary, and top anomaly flags.

The panel is dashboard display only. It does not start or stop runtime processes and does not submit orders.

## Current Generated Result

The local OBS-OS1 status check for `pt_rt1_6_week2_active` reported:

```text
go_no_go: observation_may_continue
anomaly_flags: 1
info: warm_start_block_spike = 81
```

This means the current review layer did not find a blocking condition. The warm-start spike is informational and should be reviewed as normal PT-RT warm-start gating behavior unless accompanied by unexpected synthetic opens or testnet lifecycle rows.

## Boundaries

- Synthetic paper only.
- Public Hyperliquid mainnet candles remain strategy truth.
- Synthetic paper ledgers remain PnL truth.
- Hyperliquid testnet lifecycle remains separate plumbing.
- Testnet fills do not update synthetic PnL.
- Candidate and MF-ORIG lanes remain synthetic-only.
- No live trading was approved.
- No strategy was production-approved.
- No orders were submitted by OBS-OS1.
- No runtime behavior was changed.

## Limitations

- OBS-OS1 summarizes available local runtime logs only.
- It does not prove strategy edge or profitability.
- It does not replace deeper lane-level quant review.
- It does not reconcile venue truth beyond the lifecycle rows already recorded by the runtime.
- It is intentionally conservative: suspicious or missing data becomes a review flag rather than a silent assumption.

## Recommended Cadence

Run the status command during the day and generate the daily pack at the end of each observation day.

Use the generated Markdown for founder review and the dashboard JSON for fast anomaly scanning.
