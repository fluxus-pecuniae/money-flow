# PT-RT1.5.1 Signed Testnet Transport, Warm-Start Gate, And MTM Hotfix

## Summary

PT-RT1.5.1 is a scoped paper-runtime hotfix for the Week 1 Paper Trading lab. It does not approve live trading, production strategy behavior, or candidate strategy transport.

Status: implemented

## Objective

PT-RT1.5.1 addresses three runtime issues found during the PT-RT1.5 one-hour smoke:

- The prior smoke created synthetic opens from entry confirmations that were already true at runtime start.
- Hyperliquid testnet lifecycle rows stopped at `preflight_passed` because signed transport was not configured.
- Open synthetic positions showed missing current prices and zero unrealized PnL instead of true public-mainnet mark-to-market state.

## Archived Smoke State

The prior PT-RT1.5 smoke state is archived as `pt_rt1_5_smoke_pre_warm_start_gate`.

Old runtime rows are not deleted or mutated. The Paper Trading dashboard defaults to the new `pt_rt1_5_1_smoke` scope, so pre-warm-start rows are hidden unless an archive view is explicitly selected.

Reason codes:

- `pre_warm_start_gate_runtime_archived`
- `archived_smoke_rows_hidden_by_default`
- `active_week_reset_after_warm_start_hotfix`

## Warm-Start Signal Gate

Status: implemented

Default policy: `fresh_signal_only_after_runtime_start = true`.

This warm-start signal gate is intentionally conservative: startup-valid confirmations are recorded for review, but they do not open synthetic positions and they cannot send testnet orders.

At runtime start, the system evaluates the latest fully closed candle for each lane, symbol, and active timeframe. If an entry condition is already true, the runtime records the condition but does not create a synthetic open and does not create a testnet order.

A fresh open is allowed only after:

- warm-start evaluation completed;
- the signal candle closed after `runtime_start_utc`;
- the entry context reset from true to false if it was already true at startup;
- the entry condition transitions false to true after runtime start;
- the signal came from scheduled closed-candle evaluation;
- the signal is not duplicate.

Reason codes:

- `warm_start_evaluation_completed`
- `signal_good_but_runtime_started_after_setup`
- `entry_context_already_true_at_runtime_start`
- `entry_context_already_true_waiting_for_reset`
- `entry_context_reset_observed`
- `fresh_entry_signal_after_runtime_start`
- `warm_start_blocked_late_entry`

## Signed Hyperliquid Testnet Transport

Status: implemented with fail-closed configuration

PT-RT1.5.1 wires the signed Hyperliquid testnet transport client behind explicit gates. The client reads the local sandbox private key and target account from environment variables only. Secrets are not logged and are not committed.

Expected configured status when local env is present:

- `signed_testnet_transport_client_configured = true`
- `transport_submit_configured = true`

If local env is missing, transport remains blocked with:

- `signed_testnet_transport_client_not_configured`

## Testnet Order Policy

Only `money_flow_v1_2_baseline` fresh synthetic opens can trigger signed testnet order transport.

Required trigger:

- lane: `money_flow_v1_2_baseline`
- action: `paper_opened`
- timeframe: `1h`, `4h`, or `1d`
- scheduled closed-candle evaluation: true
- fresh signal after runtime start: true
- duplicate order key: false

Blocked triggers:

- candidate lanes
- MF-ORIG lanes
- wildcard lanes
- 15m
- startup-valid signals
- no-trade, hold, close, trim, data-unavailable, or duplicate rows

Fixed notional:

- `testnet_fixed_notional = 25 USDC`
- synthetic signal size does not change testnet notional
- sizing source: `fixed_testnet_plumbing_notional`

Testnet fills do not update synthetic PnL.

## Account Targeting And Margin Readiness

Account targeting policy remains unchanged:

- main/user mode omits `vaultAddress`;
- subaccount/vault mode uses `vaultAddress` only when explicit and valid;
- `Vault not registered` is recorded as a reject and is not retried endlessly.

Unified/spot margin information is represented only for testnet readiness. It is not strategy PnL truth.

## Precision / Tick / Lot Policy

The testnet order shape uses the existing Hyperliquid Decimal precision formatter.

Validated fields:

- asset id
- `szDecimals`
- post-only limit order
- 5 significant-figure price behavior
- size lot formatting
- trailing-zero stripping
- approximate 25 USDC notional

Tick or lot rejects are reason-coded as:

- `testnet_order_rejected_tick_size`
- `testnet_order_rejected_lot_size`

## Open-Position MTM Fix

Status: implemented

Open synthetic positions now populate:

- `current_price`
- `current_price_source`
- `current_price_time`
- `current_unrealized_pnl`
- `current_unrealized_pnl_pct`
- `position_notional`
- `total_equity_impact`

Preferred MTM source: public mainnet `allMids`.

Fallback MTM source: latest fully closed public mainnet candle close.

If MTM is unavailable, the dashboard displays `MTM unavailable` instead of a misleading zero.

## Dashboard Updates

Status: implemented

The Paper Trading dashboard now defaults to `pt_rt1_5_1_smoke` runtime files:

- `reports/paper_runtime/pt_rt1_5_1_smoke/summary.json`
- `reports/paper_runtime/pt_rt1_5_1_smoke/decisions.jsonl`
- `reports/paper_runtime/pt_rt1_5_1_smoke/trades.jsonl`
- `reports/paper_runtime/pt_rt1_5_1_smoke/testnet_order_lifecycle.jsonl`

Dashboard additions:

- signed transport client configured/missing status;
- warm-start gate counts;
- startup-valid signals blocked;
- waiting-for-reset counts;
- fresh post-start opens;
- lifecycle endpoint-called flags;
- fresh signal flag in the lifecycle table;
- MTM unavailable display for missing open-position marks.

## Smoke Run Status

Status: bounded one-cycle smoke verified

Recommended command:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 1 \
  --output-dir reports/paper_runtime/pt_rt1_5_1_smoke \
  --pt-rt1-5-week1-active \
  --signal-evaluation-mode candle_close_only \
  --fresh-signal-only-after-runtime-start \
  --enable-baseline-testnet-transport \
  --founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --disable-legacy-testnet-probes \
  --public-mainnet-only
```

The dashboard control server uses this PT-RT1.5.1-safe command shape when starting the default runtime.

Local bounded smoke result:

- scope: `pt_rt1_5_1_smoke`
- public mainnet data: connected
- decisions written: `30`
- startup-valid synthetic opens: `0`
- fresh post-start opens: `0`
- testnet lifecycle rows: `0` because no fresh baseline open occurred in the one-cycle smoke
- order endpoint calls: `0`
- signed order endpoint calls: `0`
- signed transport status: fail-closed as `signed_testnet_transport_client_not_configured` in the current shell because local Hyperliquid testnet signing env was not present

## Boundaries

- Public mainnet candles remain strategy truth.
- Testnet prices are not strategy truth.
- Testnet fills do not update synthetic PnL.
- Candidate lanes cannot send testnet orders.
- No live trading is approved.
- No strategy is production-approved.
- Production Money Flow rules are unchanged.

## Next Phase

Recommended next step: run `pt_rt1_5_1_smoke` for one hour, then review warm-start counts, MTM updates, and testnet lifecycle rows before starting the Week 1 observation window.
