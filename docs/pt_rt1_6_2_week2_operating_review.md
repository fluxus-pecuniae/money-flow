# PT-RT1.6.2 Week 2 Operating Review

Recorded at: `2026-06-08T08:24:44Z`

## Verdict

Week 2 paper observation may continue unchanged.

The active runtime is writing to `reports/paper_runtime/pt_rt1_6_week2_active/`, the dashboard/control state reports `paper_runtime_started_with_caffeinate`, and the current Daily Review status is `observation_may_continue`.

This is an operating review only. It does not approve production trading, live trading, strategy promotion, candidate-lane testnet routing, or any Money Flow rule change.

## Runtime Scope

- Active runtime scope: `pt_rt1_6_week2_active`
- Runtime process status: running under Mac `caffeinate`
- First decision row reviewed: `2026-06-07T08:07:53Z`
- Latest decision row reviewed: `2026-06-08T08:02:50Z`
- Latest runtime audit heartbeat reviewed: `2026-06-08T08:25:41Z`
- Public mainnet connection: connected
- Strategy truth: public Hyperliquid mainnet candles
- Synthetic PnL truth: internal paper ledgers
- Testnet lifecycle truth: separate Hyperliquid testnet plumbing rows

## Week 2 Boundary Checks

| Check | Result |
| --- | --- |
| Active lanes are founder-selected Week 2 lanes only | Pass |
| Decisions per selected lane | `352` each |
| Active timeframes | `1h`, `4h`, `1d` |
| `15m` active rows | `0` |
| Scheduled closed-candle evaluations | `1056 / 1056` |
| Candidate/MF-ORIG testnet lifecycle triggers | `0` |
| Testnet lifecycle trigger lane | `money_flow_v1_2_baseline` only |
| Testnet fills update synthetic PnL | `0` rows |
| Unknown/open testnet state | `0` rows |
| Open-position MTM unavailable | `0` positions |

## Decision Flow

Total paper decisions reviewed: `1056`.

| Action | Count |
| --- | ---: |
| `no_trade` | 704 |
| `paper_hold` | 202 |
| `paper_opened` | 98 |
| `paper_closed` | 40 |
| `data_unavailable` | 12 |

| Timeframe | Count |
| --- | ---: |
| `1h` | 594 |
| `4h` | 330 |
| `1d` | 132 |

Top reason-code themes:

- `signal_evaluation_started_after_closed_candle`: 1056
- `public_mainnet_data_connected`: 1044
- `closed_candle_ready`: 1044
- `baseline_alignment_failed`: 483
- `macd_histogram_not_constructive`: 408
- `baseline_alignment_passed`: 387
- `price_below_sma20`: 375
- `warm_start_evaluation_completed`: 198
- `fresh_entry_signal_after_runtime_start`: 98
- `warm_start_blocked_late_entry`: 87

The warm-start gate is doing useful work: `87` startup/late-context entries were blocked, while `98` opens were marked fresh post-start signals.

## Lane Review

| Lane | Decisions | Open positions | Closed trades | Closed net PnL | Wins | Losses | Largest win | Largest loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `money_flow_v1_2_baseline` | 352 | 19 | 14 | `-817.6449408148801309161366460` | 3 | 11 | `126.6420091695289499509322865` | `-202.2831443335490081933875853` |
| `avoid_low_rolling_range_20` | 352 | 19 | 14 | `-817.6449408148801309161366460` | 3 | 11 | `126.6420091695289499509322865` | `-202.2831443335490081933875853` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | 352 | 20 | 12 | `-155.1942742746160639399457848` | 5 | 7 | `126.6420091695289499509322865` | `-176.4429153930358258885290272` |

Early read:

- The selected MF-ORIG lane is currently the least bad on closed synthetic PnL and loss profile.
- Baseline and `avoid_low_rolling_range_20` are identical on closed synthetic PnL so far; the rolling-range filter has not yet shown differentiated behavior in this early runtime window.
- These numbers are early operating telemetry only, not evidence of edge.

## Open / Closed Position Review

- Reconstructed open positions: `58`
- Open positions by lane:
  - `money_flow_v1_2_baseline`: 19
  - `avoid_low_rolling_range_20`: 19
  - `mf_orig_1d_stage2_breakout_resistance_full_equity`: 20
- Open positions by timeframe:
  - `4h`: 48
  - `1h`: 10
- Closed synthetic trades: `40`
- Closed synthetic trade net PnL: `-1790.484155904376325772219076`
- Closed synthetic winners: `11`
- Closed synthetic losers: `29`
- Largest closed winner: `126.6420091695289499509322865`
- Largest closed loser: `-202.2831443335490081933875853`
- MTM status: `58 / 58` open positions updated; `0` unavailable.

## Testnet Lifecycle Review

Testnet lifecycle rows reviewed: `33`.

| Status | Count |
| --- | ---: |
| `reconciled` | 21 |
| `blocked` | 12 |

Transport checks:

- Trigger lane: `money_flow_v1_2_baseline` only
- Order endpoint called: 21 rows
- Signed order endpoint called: 21 rows
- Unknown/open testnet state: 0 rows
- Candidate-lane transport rows: 0 rows
- Testnet PnL updates: 0 rows

Accepted/canceled/reconciled symbols:

`ETH`, `SOL`, `DOGE`, `BNB`, `SUI`, `FIL`, `BTC`, `POL`, `AAVE`, `ADA`, `ASTER`, `XMR`, `HYPE`

Blocked symbols:

`XRP`, `LINK`, `DOT`, `LTC`, `UNI`, `TRX`, `ZEC`

Blocked reason codes:

- `testnet_order_precision_missing`
- `testnet_metadata_unavailable`

Interpretation:

The testnet layer is functioning safely. It submits only baseline-triggered fixed-notional testnet orders when metadata is ready, cancels/reconciles accepted orders, and fails closed when testnet precision metadata is unavailable. The blocked symbols are not a strategy issue; they are a testnet metadata/resolver readiness issue to triage later.

## Daily Review / Anomaly Status

Generated daily-review status:

- Scope: `pt_rt1_6_week2_active`
- Go/no-go: `observation_may_continue`
- Anomaly flag count: 1
- Current flag: informational `warm_start_block_spike: 63`

The warm-start spike is expected early-runtime behavior and should remain informational unless it repeats as a blocker or masks fresh-signal behavior.

## Risks And Blind Spots

- Early closed synthetic PnL is negative across all active lanes; do not infer edge from this window.
- `avoid_low_rolling_range_20` has not yet differentiated from baseline in closed-trade behavior.
- Several symbols cannot route testnet plumbing because testnet precision metadata is unavailable.
- The runtime summary file currently reports `closed_trades: []`; this review uses `trades.jsonl` as the closed-trade truth for the operating memo.
- The active symbol universe is broader than the compact configured dashboard filter list; future UI/reporting should continue making scanner-universe truth explicit.

## Recommendation

Continue Week 2 paper observation unchanged for another 24 hours, then repeat this operating review.

Do not add GOAL-STRAT2 candidates yet. Do not change strategy rules. Do not enable `15m`. Do not promote any lane. Do not route candidate/MF-ORIG lanes to testnet.

The next engineering follow-up, if prioritized, should be a narrow testnet metadata/resolver review for blocked symbols, not a strategy change.

## No-Order / No-Live Confirmation

- No live trading was approved.
- No strategy was production-approved.
- No production Money Flow rules changed.
- No runtime code behavior changed in this phase.
- No runtime was started or stopped by this phase.
- No manual live or testnet orders were submitted by this phase.
- Existing baseline-only testnet lifecycle rows remain plumbing only.
- Candidate and MF-ORIG lanes remain synthetic-only.
- Testnet fills do not update synthetic PnL.
