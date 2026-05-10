# UAT2 Shadow Strategy Top-20 Observation

Recorded at: `2026-05-10T08:38:49Z`

## Scope

UAT2 is a bounded no-order shadow strategy observation run over public read-only market data. It does not submit orders, does not use API keys, does not call private or signed endpoints, does not create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approval, routing, paper-trade, or live-trade artifacts, does not change Money Flow rules, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Runtime Mode

| Field | Value |
| --- | --- |
| Run id | `uat2-shadow-20260510T083835Z` |
| Runtime mode | `uat` |
| UAT2 shadow mode | `true` |
| Shadow only | `true` |
| Public read-only allowed | `true` |
| Private endpoints allowed | `false` |
| Signed endpoints allowed | `false` |
| Order endpoints allowed | `false` |
| API keys used | `false` |
| Order submission enabled | `false` |
| Paper trading enabled | `false` |
| Live trading enabled | `false` |

## Universe Snapshot Used

- Source provider: `coingecko_public_markets`
- Source timestamp: `2026-05-10T07:18:31+00:00`
- Included observation-only symbols evaluated: `BTC`, `ETH`, `SOL`, `XRP`, `ZEC`, `BNB`, `SUI`, `TON`, `DOGE`, `TRX`, `LAYER`, `CHIP`, `UNI`, `ONDO`, `AAVE`
- Top-20 inclusion remains observation-only and is not strategy approval, paper-trading approval, live-trading approval, or order-submission approval.

## Bounded Run Definition

- Started at: `2026-05-10T08:38:35.325955+00:00`
- Completed at: `2026-05-10T08:38:49.512364+00:00`
- Components evaluated: `sleeve_15m, sleeve_1h, sleeve_4h`
- Public data lookback candles per symbol/component: `80`
- Evaluation candle policy: `latest_candle_with_next_candle_available`
- Continuous daemon: `false`

## Public Read-Only Data Status

- Candle fetch successes: `45`
- Candle fetch failures: `0`
- Endpoint category used: `public_read_only` / Hyperliquid `candleSnapshot`.

## Signal Summary

| Metric | Count |
| --- | ---: |
| Shadow audit records | `45` |
| `would_open` | `11` |
| `no_trade` | `34` |
| `invalid` | `0` |
| `risk_blocked` | `0` |

## Signal Summary By Symbol / Component

| Symbol | Component | Timeframe | No trade | Would open | Would hold | Would reduce | Would close | Invalid | Risk blocked | Top no-trade reasons | Top invalid reasons | Top risk-block reasons |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `AAVE` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `entry_quality_not_constructive`: `1` |  |  |
| `AAVE` | `sleeve_1h` | `1h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `AAVE` | `sleeve_4h` | `4h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `BNB` | `sleeve_15m` | `15m` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `BNB` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `BNB` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `BTC` | `sleeve_15m` | `15m` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `BTC` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `BTC` | `sleeve_4h` | `4h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `CHIP` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `CHIP` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `CHIP` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `DOGE` | `sleeve_15m` | `15m` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `DOGE` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `DOGE` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `ETH` | `sleeve_15m` | `15m` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `ETH` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `ETH` | `sleeve_4h` | `4h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `LAYER` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `LAYER` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `LAYER` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `overextended_rsi`: `1` |  |  |
| `ONDO` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `ONDO` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `ONDO` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `SOL` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `SOL` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `SOL` | `sleeve_4h` | `4h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `SUI` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `overextended_rsi`: `1` |  |  |
| `SUI` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `SUI` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `TON` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `TON` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `TON` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `TRX` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `TRX` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `TRX` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `UNI` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `UNI` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `overextended_rsi`: `1` |  |  |
| `UNI` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `XRP` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `rsi_not_constructive`: `1` |  |  |
| `XRP` | `sleeve_1h` | `1h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `bearish_alignment`: `1` |  |  |
| `XRP` | `sleeve_4h` | `4h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `ZEC` | `sleeve_15m` | `15m` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |
| `ZEC` | `sleeve_1h` | `1h` | `0` | `1` | `0` | `0` | `0` | `0` | `0` |  |  |  |
| `ZEC` | `sleeve_4h` | `4h` | `1` | `0` | `0` | `0` | `0` | `0` | `0` | `macd_not_constructive`: `1` |  |  |

## Timing Assumptions

- `next_candle_open` is represented in each shadow audit record.
- `next_candle_close` is represented in each shadow audit record.
- `same_candle_close_research_only` remains research-only and is excluded from UAT2 action assumptions.
- Timing status is `available` when the bounded public candle window includes the next candle; otherwise it is `pending_next_candle`, `not_applicable`, or `blocked`.

## Shadow Drawdown State

| Field | Value |
| --- | --- |
| Source | `shadow_simulated` |
| Not live account drawdown | `true` |
| Shadow simulated drawdown | `true` |
| Initial shadow equity | `10000` |
| Current shadow equity | `10000` |
| Max drawdown amount | `0` |
| Max drawdown percent | `0` |
| Threshold breached | `false` |

UAT2 is signal-only and does not simulate PnL. Shadow equity is held flat for operator visibility; this is `shadow_drawdown_not_computed_for_no_order_signal_only_run` and `not_live_account_drawdown`, not live account equity and not performance validation.

## Risk Visibility

`risk_visibility_deferred_no_live_artifacts` appears on would-trade/no-trade records because UAT2 does not create order intents or execution-readiness artifacts. Drawdown state is visible, order submission remains disabled, and risk must be wired more deeply before any UAT3 sandbox-order phase.

## Evidence Candidate Section

- Evidence candidate: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`
- Scope: Hyperliquid ETH USDC perpetual, `sleeve_1h`, current baseline Money Flow rules.
- UAT2 ETH `sleeve_1h` shadow status: `no_trade`
- UAT2 ETH `sleeve_1h` reason codes: `macd_not_constructive`
- This remains the evidence candidate only. It is not proof of profitability and not paper/live/order approval.

## Boundary Confirmation

- `api_keys_used`: `false`
- `approvals_created`: `false`
- `evidence_packs_generated`: `false`
- `execution_readiness_assessments_created`: `false`
- `live_trading_added`: `false`
- `money_flow_rules_changed`: `false`
- `order_endpoints_called`: `false`
- `order_intents_created`: `false`
- `orders_submitted`: `false`
- `paper_trading_added`: `false`
- `prepared_orders_created`: `false`
- `private_endpoints_called`: `false`
- `public_read_only_allowed`: `true`
- `routing_artifacts_created`: `false`
- `signal_events_created`: `false`
- `signed_endpoints_called`: `false`
- `strategy_decisions_created`: `false`
- `submitted_orders_created`: `false`

## UAT3 Readiness Decision

`UAT3 is blocked`.

Remaining blockers:
- `founder_operator_explicit_approval_required_before_uat3_sandbox_order_design`
- `sandbox_account_drawdown_feed_wiring_required_before_uat3`
- `uat3_approval_submit_lease_lifecycle_verification_required`

UAT3 may not submit sandbox orders until a later explicit phase scopes approval-gated sandbox order design and the founder/operator explicitly accepts that scope.

## UAT2.1 Dashboard Follow-Up

UAT2.1 adds dashboard visualization for this UAT2 summary in `apps/dashboard/` and documents the review surface in `docs/uat2_1_dashboard_visualization_and_approval_readiness.md`.

The dashboard UAT2 tab loads `docs/uat2_shadow_strategy_top20_observation_summary.json`, shows the 45 shadow records, would-open/no-trade breakdowns, ETH `sleeve_1h` candidate status, timing assumptions, not-live-account shadow drawdown, boundary flags, and UAT3 blockers. It is informational only: it does not implement UAT3, create approvals, enable order submission, approve paper/live trading, or change Money Flow rules.
