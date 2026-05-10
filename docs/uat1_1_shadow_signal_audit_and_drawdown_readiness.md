# UAT1.1 Shadow Signal Audit And Drawdown Readiness

Recorded at: `2026-05-10T08:08:18Z`

## Scope

UAT1.1 prepares shadow audit and drawdown visibility. It does not run the UAT2 shadow strategy loop, does not run Money Flow over live data, does not submit orders, does not call private or signed endpoints, does not use exchange API keys, does not create strategy decisions, order intents, submitted orders, approvals, paper trades, live trades, routing artifacts, evidence packs, or Money Flow rule changes.

UAT2 follow-up: `docs/uat2_shadow_strategy_top20_observation.md` completed the bounded no-order shadow strategy observation using the UAT1 universe snapshot, public read-only Hyperliquid candles, and the UAT1.1 shadow audit/drawdown surfaces. UAT2 did not create strategy decisions, order intents, submitted orders, approvals, paper/live trades, routing artifacts, evidence packs, or Money Flow rule changes.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Shadow Signal Audit Surface

Status: `implemented`.

The UAT shadow signal audit surface is model/report-only and is separate from production trading artifacts.

| Field | Example / status |
| --- | --- |
| Run id | `uat2-shadow-readiness-template` |
| Venue / symbol | `hyperliquid` / `ETH` |
| Component / timeframe | `sleeve_1h` / `1h` |
| Signal status | `no_trade` |
| Reason codes | `uat1_1_template_record_no_strategy_run` |
| Timing assumptions | `next_candle_open, next_candle_close` |
| Same-candle close status | `same_candle_close_research_only=true` |
| Operator explanation | Template audit record only; UAT1.1 did not run the live shadow strategy loop. |

Required future UAT2 signal statuses are `no_trade`, `would_open`, `would_hold`, `would_reduce`, `would_close`, `invalid`, and `risk_blocked`.

## No-Live-Artifact Boundary

Shadow audit no-live-artifact check: `true`.

The shadow audit surface does not create: `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, or live trades.

## Timing Assumptions

- `next_candle_open` is represented for future UAT2 shadow comparison.
- `next_candle_close` is represented for future UAT2 shadow comparison.
- `same_candle_close_research_only` remains research-only and is excluded from primary UAT2 shadow assumptions.

## Operator-Visible Shadow Drawdown State

Status: `implemented`.

| Field | Value |
| --- | --- |
| Run id | `uat2-shadow-readiness-template` |
| Candidate id | `money_flow_hyperliquid_eth_1h_baseline_uat_candidate` |
| Universe scope | `top20_hyperliquid_observation_universe` |
| Initial shadow equity | `10000` |
| Current shadow equity | `10025` |
| Max shadow equity | `10150` |
| Min shadow equity | `10000` |
| Max drawdown amount | `125` |
| Max drawdown percent | `0.01231527093596059113300492611` |
| Drawdown threshold | `0.10` |
| Threshold breached | `false` |
| Source | `shadow_simulated` |
| Not live account drawdown | `true` |
| Shadow simulated drawdown | `true` |
| Reason codes | `shadow_equity_source_not_live_account`, `shadow_drawdown_monitor_not_live_fed`, `shadow_drawdown_within_limit` |

This is `shadow_simulated_drawdown` and `not_live_account_drawdown`. It is operational risk visibility, not performance validation.

## Drawdown Threshold Reason Codes

- `shadow_drawdown_within_limit`
- `shadow_drawdown_threshold_breached`
- `shadow_equity_unavailable`
- `shadow_equity_source_not_live_account`
- `shadow_drawdown_monitor_not_live_fed`

## Structured Log / API Error Redaction Status

Status: `implemented_representative_api_error_and_structured_log_payloads`.

UAT1.1 verifies representative API-error and structured-log payloads through `core.security.redact_api_error_payload` and `core.security.redact_structured_log_event`. Structlog events also pass through `core.logging.setup.redact_structlog_event` before rendering. Covered examples include bearer tokens, authorization headers, API keys, secrets, passwords, runtime-policy tokens, exception text, and database URLs.

Remaining redaction follow-up before UAT3: deployment-specific middleware and logging processors should still be smoke-tested in a sandbox-like runtime.

## UAT1 Universe Snapshot For UAT2

Status: `available`.

- Source provider: `coingecko_public_markets`
- Source timestamp: `2026-05-10T07:18:31+00:00`
- Included observation-only assets: `BTC`, `ETH`, `SOL`, `XRP`, `ZEC`, `BNB`, `SUI`, `TON`, `DOGE`, `TRX`, `LAYER`, `CHIP`, `UNI`, `ONDO`, `AAVE`
- Excluded assets: `USDT`, `USDC`, `USD1`, `QUQ`, `BILL`
- Observation-only flags preserved: `true`

The UAT1 snapshot is not permanent strategy approval, paper-trading approval, live-trading approval, or order-submission approval.

## UAT2 Readiness Decision

Historical UAT1.1 decision at the time: `UAT2 shadow strategy run may proceed`.

UAT2 was accepted as next work and completed as no-order shadow mode. It compared `next_candle_open` and `next_candle_close`; it did not submit orders.

Remaining blockers:
- none for UAT2 shadow-only start; UAT3 sandbox-order blockers remain deferred.
- UAT3.0 later completed sandbox-order design/readiness. UAT3.1 actual sandbox order submission remains blocked pending explicit founder/operator approval, sandbox account drawdown feed wiring, and UAT3 approval/submit-lease/lifecycle verification.

## Boundary Confirmation

UAT1.1 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, exchange calls, private/signed calls, order endpoint calls, evidence packs, strategy variants, or Money Flow rule changes.
