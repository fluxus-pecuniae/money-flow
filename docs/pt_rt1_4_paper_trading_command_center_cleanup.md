# PT-RT1.4 Paper Trading Command Center Cleanup

## Executive Summary

PT-RT1.4 makes Paper Trading the founder weekly review surface and cuts the active Week 1 paper-observation scope to `1h`, `4h`, and `1d`.

The `15m` timeframe is paused for Week 1 because it was creating excessive paper-trading noise. Existing 15m runtime records are not deleted; they remain available under a paused/legacy review filter and are excluded from the default active weekly scoreboard.

This phase is dashboard/runtime cleanup only. Production Money Flow rules are unchanged. No strategy is production-approved. No live trading is approved. No live or testnet orders were submitted.

## Active Timeframes

| Timeframe | PT-RT1.4 status | Active weekly scoring | New synthetic entries |
| --- | --- | --- | --- |
| `1h` | active | yes | allowed by existing paper rules |
| `4h` | active | yes | allowed by existing paper rules |
| `1d` | active | yes | allowed by existing paper rules |
| `15m` | `disabled_for_week1_noise_reduction` | no | blocked after cutover |

Cutover timestamp:

```text
pt_rt1_4_active_review_start_utc = 2026-05-17T09:47:55Z
```

Reason codes added for the cutover:

- `timeframe_disabled_by_founder_for_week1`
- `timeframe_excluded_from_active_scoreboard`
- `legacy_15m_position_visible`
- `no_new_15m_entries`

## Lane Comparison Scope

The Strategy Lane Comparison is now timeframe-scoped by default.

Default mode:

```text
selected timeframe only = 1h
```

Available modes:

- `1h`
- `4h`
- `1d`
- `All active timeframes: 1h + 4h + 1d`
- `15m paused / legacy`

The all-active mode is explicitly labeled:

```text
sum across active paper timeframes only: 1h + 4h + 1d
not one combined account
independent synthetic lane/timeframe observations
```

## Dashboard Changes

Paper Trading now follows this command-center order:

1. Top health banner.
2. Weekly Scoreboard / timeframe-scoped Strategy Lane Comparison.
3. Timeframe Breakdown.
4. Live Public Candles + Paper Markers plus compact watchlist.
5. Open Synthetic Positions.
6. Closed Synthetic Trades.
7. Signal / Decision Stream.
8. Summary, connection, lane detail, drawdown, and testnet plumbing reference panels.

Open Synthetic Positions now emphasizes lane, symbol, timeframe, entry age, entry/current price, notional, unrealized PnL, entry reason, data health, and active/legacy status.

Closed Synthetic Trades now includes founder-readable summary cards for count, winners, losers, largest win/loss, average win/loss, and total net PnL.

Signal Generator is now the Signal / Decision Stream and can be filtered by:

- Actual synthetic opens + intended entries.
- Intended entries.
- Actual synthetic opens.
- No-trade / blocked.
- Exits.
- Duplicate ignored.
- Data unavailable.

The watchlist remains visible inside the live chart section with only:

- symbol
- mid price
- health

Market-data health is marked stale/unhealthy when the latest public-mainnet tick is older than 2 minutes.

## Testnet Label Cleanup

The dashboard no longer shows an ambiguous `Probes enabled` label without context.

It now separates:

- Audit-only shapes: simulated testnet probe-shape checks only.
- Testnet order transport: disabled.
- Signed testnet orders: `0`.
- Strategy PnL update from testnet: `false`.

Reason code:

```text
audit_only_not_submitted
```

## Boundaries

- Public mainnet data remains strategy truth.
- Synthetic paper results are forward-observation only.
- Testnet probes are plumbing only.
- Testnet fills do not update strategy PnL.
- No strategy is production-approved.
- Live trading is not approved.
- Production Money Flow rules are unchanged.
- Historical evidence packs were not regenerated.

## Limitations

PT-RT1.4 changes the active review surface and runtime timeframe defaults. It does not evaluate whether any lane is profitable or ready for production.

Existing pre-cutover 15m records can still be reviewed, but they should not be included in Week 1 active scoring.

## PT-RT1.4.1 Runtime Verification Follow-Up

PT-RT1.4.1 verified that the active timeframe cutover had to be applied to the running process, not only to dashboard code.

Runtime finding:

```text
retired_runtime_cutover_not_applied = true
retired_runtime_new_15m_entries_after_cutover = 79
retired_runtime_label = pre_pt_rt1_4_weekend_burn_in
```

The old `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` process was stopped and excluded from active Week 1 scoring because it continued producing 15m synthetic opens after the PT-RT1.4 cutover.

The restarted active runtime writes ignored artifacts under:

```text
reports/paper_runtime/pt_rt1_4_1_active_week/
```

Its first artifact cycle reported:

```text
active_timeframes = 1h, 4h, 1d
disabled_timeframes = 15m
active_runtime_new_15m_entries_after_restart = 0
active_runtime_15m_rows_after_restart = 0
```

The current daily founder review source is:

```text
docs/pt_rt_week1_day_summary.md
docs/pt_rt_week1_day_summary.json
```

## Review Cadence

Recommended founder weekly review:

- Start with Paper Trading top health banner.
- Review 1h scoreboard first.
- Check 4h and 1d separately.
- Use all-active only as a labeled summary across active timeframes.
- Review open losing positions and recent largest losses before considering any candidate stronger.
- Keep Historical Replay, Evidence, The Lab, Audit, and Strategy tabs as reference surfaces.

## Decision

PT-RT1.4 command-center cleanup is implemented.

Next review should use:

```text
Paper Trading active week only
timeframes = 1h / 4h / 1d
15m = paused / legacy
```

No-order/no-live confirmation:

```text
live_orders_submitted = false
testnet_orders_submitted = false
private_signed_order_endpoints_called_from_strategy_truth = false
api_keys_used_for_strategy_truth = false
production_money_flow_rules_changed = false
live_trading_approved = false
```
