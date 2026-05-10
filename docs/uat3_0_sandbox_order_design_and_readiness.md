# UAT3.0 Sandbox Order Design And Approval/Lifecycle Readiness

Recorded at: `2026-05-10T10:10:00Z`

## Scope

UAT3.0 is a design and readiness phase for a future approval-gated sandbox-order test. It prepares the sandbox-order scope, approval language, runtime policy, drawdown-feed requirements, lifecycle design, artifact-labeling rules, submit-lease protections, approval gates, risk gates, dashboard readiness, and UAT3.1 decision.

UAT3.0 does not submit orders, does not call private or signed endpoints, does not use exchange API keys, does not create real `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or executable approval artifacts, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Actual sandbox order submission is not approved.

## UAT3 Sandbox Order Scope

Status: `defined`.

UAT2 used the top-20-supported Hyperliquid observation universe for behavior validation. UAT3 actual sandbox-order testing must not submit orders across that universe.

Initial UAT3 sandbox-order subset:

| Field | Value |
| --- | --- |
| Scope id | `uat3_initial_eth_1h_sandbox_order_subset` |
| Venue | `hyperliquid` |
| Product | `USDC perpetual` |
| Symbol | `ETH` |
| Component | `sleeve_1h` |
| Rules | `current baseline Money Flow rules` |
| Mode | `approval-gated sandbox/testnet only` |
| Quantity | `tiny operator-approved sandbox/testnet quantity only` |
| Universe status | `not top20_broad_order_submission` |

Distinctions:

- Frozen evidence candidate: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`.
- UAT2 observation universe: top-20-supported Hyperliquid assets for shadow behavior review only.
- UAT3 initial sandbox subset: ETH `sleeve_1h` only, tiny sandbox/testnet quantity only, explicit approval required.
- Future expansion candidates: a small operator-approved subset of the UAT2 observation universe only after separate approval.

## Founder / Operator Approval Template

Status: `defined_template_only`.

UAT3.0 completed design/scoping approval only. It did not approve an actual sandbox order submission.

Future UAT3.1 actual sandbox submission requires a separate explicit approval record with this exact intent:

```text
I approve one approval-gated sandbox/testnet order submission attempt under the exact scope below.

This approval is for sandbox/testnet only.
This approval does not approve live trading.
This approval does not approve paper trading with real capital.
This approval does not approve production auto-submit.
This approval does not approve broad top-20 order submission.
This approval does not approve repeated orders beyond the approved count.

Venue: Hyperliquid
Environment: sandbox/testnet only
Symbol: ETH
Product: USDC perpetual
Component: sleeve_1h
Rules: current baseline Money Flow rules
Maximum notional or quantity: <operator-filled tiny sandbox limit>
Maximum sandbox orders: <operator-filled small count>
Allowed order type: <operator-filled sandbox order type>
Time window: <operator-filled start/end>
Account / sandbox account id: <operator-filled sandbox account id>
Kill switch / disable control: <operator-filled control id>
Expected lifecycle to test: submit, accepted/open, partial fill or full fill if available, cancel, reject, expired, unknown/uncertainty, reconciliation, operator report

I understand this approval is not live trading approval, not real-capital paper trading approval, not route expansion approval, not automatic top-20 order submission approval, and not production auto-submit approval.
```

UAT2.1 dashboard acceptance does not authorize sandbox-order submission. UAT3.0 produces the template only; it does not execute it.

## Sandbox Runtime Policy

Status: `defined_missing_enablement`.

Required UAT3.1 runtime policy:

| Field | Required UAT3.1 Value |
| --- | --- |
| `runtime_mode` | `sandbox` or `uat_sandbox` |
| `live_trading_enabled` | `false` |
| `paper_trading_enabled` | `false` |
| `exchange_order_submission_enabled` | `false` by default |
| `sandbox_order_submission_enabled` | explicit `true` only for UAT3.1 approved run |
| `private_exchange_endpoints_enabled` | explicit sandbox-only |
| `live_endpoint_access` | `false` |
| `api_keys_required` | sandbox/testnet credentials only |

Current status: central runtime policy defaults remain fail-safe, but UAT3.1 still needs an explicit sandbox/testnet submission enablement path and sandbox-only private endpoint separation before any submission can be attempted.

Blocker: `sandbox_runtime_submission_policy_not_implemented`.

## Sandbox Account Drawdown Feed Requirements

Status: `missing`.

UAT3.1 requires sandbox account drawdown visibility before actual sandbox orders.

Required feed fields:

| Field | Requirement |
| --- | --- |
| `sandbox_account_equity` | required |
| `sandbox_realized_pnl` | required if venue provides it |
| `sandbox_unrealized_pnl` | required if venue provides it |
| `max_sandbox_equity` | required |
| `max_drawdown_amount` | required |
| `max_drawdown_percent` | required |
| `drawdown_threshold` | required |
| `threshold_breached` | required |
| `reason_codes` | required |
| `timestamp` | required |
| `venue_account_id` | required |
| `source` | `sandbox_account` |
| `not_live_account` | `true` |

Fixture/stub states may be used for UAT3.0 and tests only. UAT3.1 remains blocked until a real sandbox/testnet account feed is wired without live-account ambiguity.

Blocker: `sandbox_account_drawdown_feed_missing`.

## Approval-Gated Sandbox Order Lifecycle

Status: `designed_fixture_only`.

Future UAT3.1 lifecycle:

1. Shadow `would_open` event observed.
2. Operator selects one sandbox test candidate.
3. Approval request is created for exactly one scoped sandbox test.
4. Approval is explicitly granted.
5. Readiness/risk inspection runs.
6. Sandbox-specific intent or clearly labeled sandbox test artifact is prepared.
7. Submit lease is acquired.
8. Sandbox submit is attempted.
9. Lifecycle is observed: `accepted`, `open`, `partial_fill`, `full_fill`, `cancel`, `reject`, `expired`, `unknown_or_uncertain`.
10. Reconciliation runs.
11. Operator report is generated.

UAT3.0 models this lifecycle as design truth only. No actual submission, approval, order intent, submitted order, or exchange call was created.

## Sandbox Order Artifact Separation

Status: `defined_blocked_until_schema_or_policy_verified`.

UAT3.1 must decide whether to use existing execution artifacts or sandbox-specific test artifacts.

If existing artifacts are reused later, every row/payload must be unmistakably labeled:

- `sandbox`
- `testnet`
- `not_live`
- `not_paper`
- `uat_run_id`
- `sandbox_order = true`
- `live_endpoint_access = false`
- `real_capital = false`

If these labels cannot be enforced and surfaced in API, dashboard, reports, lifecycle events, and review bundles, UAT3.1 remains blocked.

Blocker: `sandbox_artifact_labeling_not_verified`.

## Submit Lease / Duplicate Prevention Design

Status: `designed_needs_uat3_verification`.

Future UAT3.1 sandbox orders must use the existing protection pattern:

- submit lease before transport;
- idempotency key scoped to UAT run, venue, account, symbol, component, and approval id;
- duplicate prevention for same candidate and same approval;
- uncertainty blocking if transport or persistence state is ambiguous;
- no unsafe retry after unknown state;
- no cross-venue failover;
- no route executor behavior;
- no automatic top-20 fanout.

Blocker: `uat3_submit_lease_lifecycle_verification_required`.

## Approval Gate Design

Status: `designed_needs_uat3_verification`.

Future UAT3.1 approval must be:

- explicit;
- one-time use;
- scoped to `uat_run_id`;
- scoped to `venue`;
- scoped to `account`;
- scoped to `symbol`;
- scoped to `component`;
- scoped to maximum notional or quantity;
- scoped to expiration;
- invalid after expiration;
- invalid after consumption;
- invalid for wrong symbol, account, venue, component, quantity, or run id;
- unable to turn manual-only or dry-run-only states into executable approval.

Existing Phase 7 approval concepts are useful but must be verified for sandbox/testnet labeling and exact UAT3.1 scope before any real sandbox order submission.

Blocker: `uat3_approval_scope_verification_required`.

## Risk Gate Design

Status: `defined_missing_uat3_implementation`.

Required UAT3.1 risk checks:

| Risk Gate | Required Behavior |
| --- | --- |
| `max_sandbox_notional` | block above approved tiny limit |
| `max_sandbox_order_count` | block above approved run count |
| `max_daily_sandbox_order_count` | block above daily sandbox cap |
| `max_sandbox_drawdown` | block when sandbox drawdown threshold breaches |
| `allowed_symbols` | ETH only for the first subset |
| `allowed_venue_account` | exact sandbox/testnet account only |
| `reduce_only_or_open_behavior` | explicit and audited |
| `forbidden_live_account` | hard block |
| `forbidden_live_endpoint` | hard block |
| `kill_switch_state` | must be enabled/safe before submit |
| `runtime_mode_state` | must be `sandbox` or `uat_sandbox` |

Blocker: `uat3_risk_gate_implementation_required`.

## Dashboard Readiness

Status: `implemented_informational_only`.

The dashboard UAT view includes a UAT3.0 design/readiness panel. It displays:

- UAT3.0 design status;
- UAT3.1 actual sandbox-order status;
- actual sandbox order submission: `not approved`;
- founder approval: `required`;
- sandbox account drawdown feed: `missing`;
- approval gate: `designed_needs_verification`;
- submit lease lifecycle: `designed_needs_verification`;
- lifecycle verification: `designed_needs_verification`;
- no active order submission button.

The panel is informational only and cannot enable orders.

## UAT3.1 Readiness Decision

`UAT3.1 is blocked`.

Reasons:

- `founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission`
- `sandbox_runtime_submission_policy_not_implemented`
- `sandbox_account_drawdown_feed_missing`
- `uat3_approval_scope_verification_required`
- `uat3_submit_lease_lifecycle_verification_required`
- `uat3_risk_gate_implementation_required`
- `sandbox_artifact_labeling_not_verified`

UAT3.1 first approval-gated sandbox order may proceed only after explicit founder/operator approval for actual sandbox submission, sandbox runtime mode separation, sandbox account drawdown feed wiring, approval gate verification, submit-lease/lifecycle verification, risk gate implementation, and sandbox artifact labeling are all complete.

Actual sandbox order submission is not approved.

## Boundary Confirmation

| Boundary | UAT3.0 Result |
| --- | --- |
| Orders submitted | `false` |
| Real order intents created | `false` |
| Submitted orders created | `false` |
| Executable approvals created | `false` |
| Private endpoints called | `false` |
| Signed endpoints called | `false` |
| Exchange API keys used | `false` |
| Paper trading added | `false` |
| Live trading added | `false` |
| Money Flow rules changed | `false` |
| Routing expansion added | `false` |
| Evidence packs generated | `false` |

UAT3.0 is design/readiness only.
