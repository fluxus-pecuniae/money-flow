# UAT2.1 Dashboard Visualization And Founder Approval Readiness

Recorded at: `2026-05-10T09:22:47Z`

## Scope

UAT2.1 makes the accepted UAT2 shadow run visually reviewable in the existing static dashboard and prepares an informational founder-readiness pack for later UAT3 design/scoping.

UAT2.1 does not implement UAT3, does not submit sandbox orders, does not create order intents, does not create submitted orders, does not create executable approvals, does not call private or signed endpoints, does not use API keys, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing behavior, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Dashboard Source

Status: `implemented`.

The dashboard now loads:

```text
docs/uat2_shadow_strategy_top20_observation_summary.json
```

The new tab is:

```text
UAT2 Shadow Run
```

This source is a compact UAT2 shadow summary. It is not an evidence pack, candle file, local DB export, strategy decision, signal event, order intent, submitted order, approval, routing artifact, paper trade, or live trade.

## UAT2 Run Shown

| Field | Value |
| --- | --- |
| Run id | `uat2-shadow-20260510T083835Z` |
| Runtime mode | `uat` |
| Shadow audit records | `45` |
| Would-open records | `11` |
| No-trade records | `34` |
| Invalid records | `0` |
| Risk-blocked records | `0` |
| Public candle fetch successes | `45` |
| Public candle fetch failures | `0` |

Symbols shown:

```text
BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, AAVE
```

Components shown:

```text
sleeve_15m, sleeve_1h, sleeve_4h
```

## Dashboard Sections Added

Status: `implemented`.

The dashboard UAT2 tab includes:

- Summary cards for run id, runtime mode, shadow-only status, symbol count, component count, signal counts, public candle-fetch status, and no-artifact boundary flags.
- A filterable signal matrix by symbol, component, status, and reason code.
- A focused would-open table with indicator context, next-candle timing status/value, and risk summary.
- No-trade reason breakdowns overall, by component, and by symbol.
- A dedicated ETH `sleeve_1h` evidence-candidate card.
- Timing-assumption explanation for `next_candle_open`, `next_candle_close`, and `same_candle_close_research_only`.
- A shadow drawdown card labeled `shadow_simulated` and `not_live_account_drawdown`.
- A UAT3 readiness panel that says UAT3 is blocked.
- A boundary confirmation panel for forbidden artifacts/actions.

## ETH Evidence Candidate Card

Status: `implemented`.

The dashboard shows:

| Field | Value |
| --- | --- |
| Candidate id | `money_flow_hyperliquid_eth_1h_baseline_uat_candidate` |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| UAT2 shadow status | `no_trade` |
| Reason | `macd_not_constructive` |

This remains observation-only. It is not paper-trading approval, live-trading approval, or order-submission approval.

## Timing Assumption Truth

Status: `implemented`.

The dashboard explains:

- `next_candle_open` is represented in UAT2.
- `next_candle_close` is represented in UAT2.
- `same_candle_close_research_only` is excluded from UAT2 primary action assumptions and remains research-only.
- UAT2 does not execute any action from these assumptions.

## Shadow Drawdown Truth

Status: `implemented`.

The dashboard shows:

| Field | Value |
| --- | --- |
| Source | `shadow_simulated` |
| Not live account drawdown | `true` |
| Initial shadow equity | `10000` |
| Current shadow equity | `10000` |
| Max drawdown amount | `0` |
| Max drawdown percent | `0` |
| Threshold breached | `false` |

UAT2 did not simulate PnL. The dashboard labels this as not live account drawdown and not performance validation.

## UAT3 Readiness Panel

Status: `implemented_informational_only`.

The dashboard shows:

```text
UAT3 is blocked.
```

Remaining blockers:

- `founder_operator_explicit_approval_required_before_uat3_sandbox_order_design`
- `sandbox_account_drawdown_feed_wiring_required_before_uat3`
- `uat3_approval_submit_lease_lifecycle_verification_required`

Founder approval at this stage would mean approving later UAT3 sandbox-order design/scoping only. It would not approve actual sandbox order submission, paper trading, or live trading.

No interactive approval action was added.

## Boundary Confirmation

Status: `verified_by_dashboard_flags`.

The dashboard shows these forbidden-action flags as `false`:

- `api_keys_used`
- `private_endpoints_called`
- `signed_endpoints_called`
- `order_endpoints_called`
- `orders_submitted`
- `strategy_decisions_created`
- `signal_events_created`
- `order_intents_created`
- `prepared_orders_created`
- `execution_readiness_assessments_created`
- `submitted_orders_created`
- `approvals_created`
- `routing_artifacts_created`
- `paper_trading_added`
- `live_trading_added`
- `evidence_packs_generated`
- `money_flow_rules_changed`

If a future summary marks any forbidden flag `true`, the dashboard highlights it as critical.

## UAT3 Readiness Decision

`UAT3 is blocked`.

UAT2.1 improves founder/operator review readiness, but it does not clear UAT3. UAT3 still requires explicit founder/operator acceptance of sandbox-order design scope and later sandbox drawdown/risk/lifecycle verification.

## Validation Notes

UAT2.1 added dashboard tests for:

- UAT2 summary JSON visibility.
- Expected UAT2 counts and boundary flags.
- Signal matrix, would-open warning, ETH candidate, timing, drawdown, and UAT3 blocked panels.
- Absence of order-enabling approval controls and forbidden approval/performance language.

