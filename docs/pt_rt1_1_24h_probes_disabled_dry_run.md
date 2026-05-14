# PT-RT1.1 24-Hour Probes-Disabled Dry Run

## Summary

Status: blocked

Decision: **PT-RT1.2 blocked**

PT-RT1.1 is an observation/validation phase for the PT-RT1 public-mainnet paper-observation runtime. The required 24-hour runtime artifact directory was checked at:

`reports/paper_runtime/pt_rt1_1_24h_dry_run`

Artifact directory exists: `false`

Missing required runtime files: `state.json, decisions.jsonl, trades.jsonl, equity_curves.json, data_health.json, runtime_audit.jsonl, summary.json`

Because the 24-hour runtime artifacts are absent, this report does **not** claim that public market-data refresh, closed-candle gating, synthetic paper ledgers, duplicate prevention, or dashboard runtime behavior passed. PT-RT1.2 remains blocked until a real 24-hour probes-disabled run is executed and summarized.

## Runtime Config

| Setting | Required / Observed |
|---|---:|
| `PT_RT1_TESTNET_PROBES_ENABLED` | `false` |
| `PT_RT1_TESTNET_KILL_SWITCH` | `true` |
| `PT_RT1_TESTNET_DAILY_PROBE_CAP` | `0` |
| Strategy truth | Hyperliquid public mainnet data only |

Forbidden in this dry run: testnet prices as strategy truth, private/signed endpoints, order endpoints, API keys, account balances, and sandbox/testnet fills as strategy PnL.

## Start / End Time

| Field | Value |
|---|---:|
| Start time | `not_available` |
| End time | `not_available` |
| Observed duration hours | `0` |
| Required duration hours | `24` |

## Strategy Lanes

Expected lanes:

- `money_flow_v1_2_baseline`
- `avoid_low_rolling_range_50`
- `avoid_low_rolling_range_20`
- `mf_orig_1d_stage2_breakout_resistance_full_equity`

All lanes must start at synthetic `10000 USDC` and compound wins/losses forward during the actual dry run.

## Data-Health Results

Verdict: `not_verified_runtime_absent`

Runtime counters are not available because the 24-hour artifact set is absent. The next run must report public fetch successes/failures, stale symbols, missing candle gaps, out-of-order candles, incomplete candle skips, indicator-unavailable counts, and data-unavailable decisions.

## Decisions / Trades Summary

Status: `not_verified_runtime_absent`

No committed runtime decisions or trades are included in this report. Runtime decisions/trades must remain ignored under `reports/paper_runtime/pt_rt1_1_24h_dry_run/` and summarized here only after the real run completes.

## Ledger Summary

Verdict: `not_verified_runtime_absent`

Required invariants:

- `equity_does_not_reset_after_trades`
- `closed_trade_pnl_changes_realized_equity`
- `open_trade_pnl_changes_unrealized_pnl`
- `total_equity_equals_realized_equity_plus_unrealized_pnl`

The invariants are not runtime-verified for PT-RT1.1 yet because no dry-run artifacts exist.

## Duplicate-Signal Summary

Verdict: `not_verified_runtime_absent`

The dry run must report signal keys, first-seen timestamps, duplicate counts, and `duplicate_ignored` counts. No duplicate paper position from the same signal candle may be created.

## Dashboard Verification

Verdict: `not_verified_runtime_absent`

Static PT-RT1 dashboard support exists, but the Paper Observation dashboard was not verified against a completed 24-hour runtime artifact set. The next dry run must verify that the dashboard shows top-20 scanner state, public-mainnet data health, lane comparison, synthetic equity curves, open/closed synthetic trades, drawdown/losing streaks, testnet probes disabled, and no order controls.

## No-Order / No-Live Verification

| Boundary | Status |
|---|---:|
| Testnet probes disabled | `true` |
| Kill switch active | `true` |
| Daily probe cap zero | `true` |
| Orders submitted | `false` |
| Private/signed/order endpoints called | `false` |
| API keys used | `false` |
| `OrderIntent` created | `false` |
| `PreparedVenueOrder` created | `false` |
| `SubmittedOrder` created | `false` |
| Live endpoint used | `false` |

Basis: `static_PT_RT1_policy_and_no_PT_RT1_1_runtime_artifacts`

## Issues Found

| Severity | Issue | Impact | Required fix |
|---|---|---|---|
| P1 | `pt_rt1_1_24h_runtime_artifacts_missing` | Cannot validate market-data refresh, closed-candle gating, ledgers, duplicate prevention, or dashboard runtime behavior. | Run the PT-RT1 24-hour probes-disabled dry-run and retain ignored artifacts under reports/paper_runtime/pt_rt1_1_24h_dry_run/. |

## Go / No-Go For PT-RT1.2

**PT-RT1.2 blocked**

PT-RT1.2 may proceed only after a real 24-hour probes-disabled dry run demonstrates stable public mainnet data refresh, correct paper-ledger updates, no duplicate-signal bug, working data-health gates, readable dashboard runtime state, disabled testnet probes, and no private/signed/order endpoint calls.
