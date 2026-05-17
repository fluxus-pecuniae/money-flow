# PT-RT1.5 Week 1 Reset, Baseline Testnet Orders, and Candle Scheduler

## Executive Summary

PT-RT1.5 resets the active Week 1 Paper Trading scope to `pt_rt1_5_week1_active`, hides archived runtime rows by default, keeps 15m paused, and switches strategy signal evaluation to fully closed 1h / 4h / 1d candle-close events. Market-data refresh remains frequent for watchlist, chart, data-health, and unrealized-PnL display.

This phase also implements baseline-linked Hyperliquid testnet order lifecycle gating for `money_flow_v1_2_baseline` synthetic opens only. The testnet order notional is fixed at 25 USDC and is independent of the synthetic paper signal size. Candidate, MF-ORIG, and wildcard lanes remain synthetic-only.

PT-RT1.5 does not approve production rules, paper as production, live trading, or real-capital behavior.

Follow-up: PT-RT1.5.1 supersedes the fresh active smoke scope with `pt_rt1_5_1_smoke`, adds warm-start gating so startup-valid confirmations cannot create late synthetic opens/testnet orders, wires signed Hyperliquid testnet transport behind fresh Money Flow v1.2 baseline opens only, and fixes open-position mark-to-market. The PT-RT1.5 `pt_rt1_5_week1_active` rows are archived by default for PT-RT1.5.1 review.

## Active Week Reset Policy

- Active runtime scope: `pt_rt1_5_week1_active`.
- Active runtime path: `reports/paper_runtime/pt_rt1_5_week1_active/`.
- Active review start: `2026-05-17T12:54:24Z`.
- Default dashboard rows: active Week 1 only.
- Archive toggle: archived / weekend burn-in rows are visible only when explicitly selected.
- Archived scopes: `pre_pt_rt1_4_weekend_burn_in`, `pt_rt1_1c_24h_dry_run`, `pt_rt1_4_1_active_week`, `legacy_runtime`.

Old runtime data is archived, not deleted or mutated.

The previously running PT-RT1.4.1 process (`reports/paper_runtime/pt_rt1_4_1_active_week/`, old 20 USDC probe-audit flags) was stopped during PT-RT1.5 implementation so it cannot continue writing old-scope rows. Restart Week 1 with the PT-RT1.5 command below.

## Active Timeframes

- Active: `1h`, `4h`, `1d`.
- Paused: `15m`.
- 15m does not create new active-week synthetic entries.
- 15m does not trigger testnet orders.
- 15m rows remain visible only through paused / archived filters.

Reason codes include `timeframe_disabled_by_founder_for_week1`, `timeframe_excluded_from_active_scoreboard`, `legacy_15m_position_visible`, and `no_new_15m_entries`.

## Candle-Close Scheduler

Strategy signal evaluation is now candle-close only:

- 1h: hourly close plus 90 second grace delay.
- 4h: 00/04/08/12/16/20 UTC close plus 120 second grace delay.
- 1d: 00:00 UTC close plus 180 second grace delay.

Between scheduled evaluations the runtime may refresh market data for display, but it records `market_refresh_only_no_signal_evaluation` and does not scan for new entries/exits.

If an expected closed candle is unavailable, the runtime records `expected_closed_candle_missing` / retry reason codes instead of faking a decision. Duplicate closed-candle evaluations are blocked with `duplicate_candle_signal_ignored`.

## Baseline-Only Testnet Order Policy

Allowed trigger:

- Lane: `money_flow_v1_2_baseline`.
- Action: `paper_opened`.
- Timeframes: `1h`, `4h`, `1d`.
- Source: scheduled fully closed candle evaluation.
- Symbol: scanner-eligible and precision-ready.

Blocked triggers:

- 15m.
- Candidate lanes.
- MF-ORIG lanes.
- Wildcard lanes.
- Duplicate closed-candle signals.
- Market refresh / intrabar updates.
- Data-unavailable, hold, close, trim, or skipped rows.

Testnet order shape:

- Venue: Hyperliquid.
- Environment: testnet.
- Side: long / buy.
- Type: post-only limit, `Alo`.
- Notional: fixed 25 USDC.
- Sizing source: `fixed_testnet_plumbing_notional`.

The synthetic signal notional is recorded for context, but it does not affect testnet order size.

## Testnet Lifecycle Policy

Lifecycle rows are written separately to `testnet_order_lifecycle.jsonl` and shown separately in the dashboard. They are not synthetic paper trades.

Statuses include `created`, `preflight_passed`, `submitted`, `accepted_open`, `filled`, `partially_filled`, `rejected`, `cancel_requested`, `canceled`, `reconciled`, `unknown_state`, and `blocked`.

Week 1 lifecycle intent is plumbing validation: submit post-only, verify lifecycle, cancel/reconcile, and do not leave unknown/open testnet state. In this Codex implementation path, signed transport remains gated by configured client/runtime authorization; no live order path is added.

Testnet fills never update synthetic PnL.

## Account And Precision Policy

- Main/user mode omits `vaultAddress`.
- Subaccount/vault mode uses `vaultAddress` only when explicit and valid.
- `Vault not registered` is recorded and not retried endlessly.
- Unified/spot USDC readiness is represented only for testnet transport readiness and never strategy PnL.
- Hyperliquid tick/lot formatting is used for testnet order shape.

## Dashboard Changes

- Paper Trading remains the weekly command center.
- Watchlist is compact, scrollable, and shows only symbol, mid, health, and status.
- Watchlist and testnet transport/lifecycle sections are side by side.
- Top status shows Week 1 active scope, 1h/4h/1d active, 15m paused, market refresh active, and signal evaluation candle-close only.
- Open positions, closed trades, signal stream, and lifecycle tables default to active week only.
- Testnet Order Lifecycle is separate from Closed Synthetic Trades.

## Runtime Command

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_5_week1_active \
  --pt-rt1-5-week1-active \
  --signal-evaluation-mode candle_close_only \
  --enable-pt-rt1-5-baseline-testnet-orders \
  --founder-approved-pt-rt1-5-baseline-testnet-orders-25usdc \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --disable-testnet-probes \
  --public-mainnet-only
```

The local dashboard control server starts this allowlisted PT-RT1.5 mode through `caffeinate`.

## Boundaries

- Public mainnet candles remain strategy truth.
- Testnet prices are not strategy truth.
- Testnet fills do not update synthetic strategy PnL.
- Candidate lanes are synthetic-only.
- Production Money Flow rules are unchanged.
- No strategy is production-approved.
- Live trading is not approved.
- No live orders are submitted.
- No SOR/fanout/CBBO/cross-venue routing is added.
- Historical evidence packs are not regenerated.

## Limitations And Next Phase

The implementation provides PT-RT1.5 scheduling, lifecycle gating, dashboard visibility, and runtime command support. Actual signed testnet submission still requires a configured Hyperliquid testnet transport client and all PT-RT1.5 gates to pass at runtime.

Recommended next step: start or restart the active Week 1 runtime under `pt_rt1_5_week1_active`, then review the first candle-close cycle and lifecycle rows.
