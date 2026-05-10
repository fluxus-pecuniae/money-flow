# UAT3.0.1 Sandbox Runtime / Approval / Risk Readiness

Recorded at: `2026-05-10T10:55:00Z`

## Scope

UAT3.0.1 is fixture/readiness hardening only. It converts the UAT3.0 sandbox-order design into testable readiness primitives without enabling actual sandbox order submission.

UAT3.0.1 does not submit orders, does not call private or signed endpoints, does not use exchange API keys, does not create real `OrderIntent` rows, does not create real `SubmittedOrder` rows, does not create executable approvals, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Actual sandbox order submission is not approved. Paper trading is not approved. Live trading is not approved.

## Sandbox Runtime Policy Status

Status: `implemented`.

UAT3.0.1 adds a concrete `SandboxRuntimePolicy` fixture/readiness helper. Defaults are fail-closed:

| Field | Default |
| --- | --- |
| `runtime_mode` | `uat` |
| `live_trading_enabled` | `false` |
| `paper_trading_enabled` | `false` |
| `exchange_order_submission_enabled` | `false` |
| `sandbox_order_submission_enabled` | `false` |
| `private_exchange_endpoints_enabled` | `false` |
| `live_endpoint_access` | `false` |
| `api_keys_required` | `false` |
| `sandbox_only` | `true` |

Future UAT3.1 actual sandbox submission still requires explicit sandbox runtime enablement:

- `runtime_mode` must be `sandbox` or `uat_sandbox`.
- `sandbox_order_submission_enabled` must be explicit `true` for the approved UAT3.1 run.
- `private_exchange_endpoints_enabled` must be explicit sandbox-only.
- `live_endpoint_access` must remain `false`.
- sandbox/testnet credentials must be configured later without live-key ambiguity.

This policy is not wired to submit orders in UAT3.0.1.

## Sandbox Artifact Label Validation

Status: `implemented`.

UAT3.0.1 adds `SandboxArtifactLabels` and `validate_sandbox_artifact_labels`.

Required labels:

- `sandbox = true`
- `testnet = true`
- `not_live = true`
- `not_paper = true`
- `uat_run_id`
- `sandbox_order = true`
- `live_endpoint_access = false`
- `real_capital = false`

Validation fails if any label is missing or unsafe. This is a fixture/model validator only; it creates no `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, or `SubmittedOrder` row.

## Actual Sandbox Order Approval Template

Status: `implemented`.

UAT3.0 / UAT3.0.1 design/scoping approval is separate from actual sandbox order approval.

Future UAT3.1 actual sandbox submission must use wording like:

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

UAT3.0.1 does not create executable approval records.

## Approval Scope Fixture Validation

Status: `fixture_verified`.

UAT3.0.1 adds fixture-only approval scope validation. It checks:

- `uat_run_id`
- venue
- account
- symbol
- component
- maximum notional or quantity
- expiration
- environment is sandbox/testnet
- not live
- not paper
- not broad top-20 submission
- one-time-use intent
- consumed approvals cannot authorize again

Fixture tests cover rejection for wrong symbol, wrong venue, wrong account, expired approval, quantity above maximum, missing sandbox environment, live environment, broad top-20 approval, missing `uat_run_id`, and consumed approval.

This validation does not create executable approvals.

## Sandbox Risk Gate Fixture Validation

Status: `fixture_verified`.

UAT3.0.1 adds fixture-only sandbox risk gate evaluation. It checks:

- max sandbox notional
- max sandbox order count
- max daily sandbox order count
- max sandbox drawdown
- allowed symbols
- allowed venue/account
- forbidden live account
- forbidden live endpoint
- kill switch state
- runtime mode state
- sandbox submission enablement state

Reason codes include:

- `sandbox_notional_limit_exceeded`
- `sandbox_order_count_exceeded`
- `sandbox_daily_order_count_exceeded`
- `sandbox_drawdown_limit_breached`
- `symbol_not_allowed_for_sandbox`
- `venue_account_not_allowed_for_sandbox`
- `live_account_forbidden`
- `live_endpoint_forbidden`
- `kill_switch_enabled`
- `runtime_mode_not_sandbox`
- `sandbox_submission_disabled`

This evaluator is fixture/readiness logic only and submits no orders.

## Sandbox Drawdown Feed Fixture Status

Status: `fixture_verified`.

UAT3.0.1 adds a sandbox drawdown feed fixture model with:

- sandbox account equity
- sandbox realized PnL
- sandbox unrealized PnL if available
- max sandbox equity
- max drawdown amount
- max drawdown percent
- drawdown threshold
- threshold breached
- reason codes
- timestamp
- venue account id
- `source = sandbox_account`
- `not_live_account = true`

This is fixture/stub support only. It does not call private account endpoints. UAT3.1 remains blocked until a real sandbox/testnet account drawdown feed is wired and verified.

## Submit Lease / Duplicate Prevention Fixture Status

Status: `fixture_verified`.

UAT3.0.1 adds fixture-only submit preflight validation. Future UAT3.1 sandbox submission must require:

- submit lease
- idempotency key
- approval id
- UAT run id
- venue
- account
- symbol
- component
- environment is sandbox/testnet

Fixture checks prove:

- duplicate same approval plus same candidate blocks;
- unknown/uncertain prior submit blocks retry;
- cross-venue retry is not allowed;
- top-20 fanout is not allowed;
- route executor behavior is not introduced.

No real submit lease, order intent, submitted order, exchange call, or executable approval is created.

## Dashboard Readiness

Status: `implemented`.

The dashboard UAT3.0 panel now shows:

- sandbox runtime policy: `fixture/implemented`
- sandbox artifact label validator: `implemented`
- approval scope validator: `fixture-tested`
- risk gate evaluator: `fixture-tested`
- sandbox drawdown feed: `fixture only / missing live sandbox feed`
- submit lease duplicate-prevention: `fixture-tested`
- actual sandbox order submission: `not approved`
- UAT3.1: `blocked`

No active approval button or order submission button was added.

## UAT3.1 Readiness Decision

`UAT3.1 is blocked`.

Remaining blockers:

- `founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission`
- `sandbox_account_drawdown_feed_missing`
- `sandbox_private_endpoint_separation_not_wired_to_real_sandbox_account`
- `sandbox_submit_path_not_implemented`
- `sandbox_artifact_labeling_not_enforced_on_persistence`
- `uat3_approval_scope_not_wired_to_executable_gate`
- `uat3_risk_gate_not_wired_to_submit_path`
- `uat3_submit_lease_lifecycle_not_integration_verified`

UAT3.1 may proceed only after founder/operator approval for actual sandbox order submission exists, sandbox runtime policy is wired to a sandbox-only submit path, sandbox account drawdown feed is live-fed from sandbox/testnet account truth, approval scope validation is wired to the executable gate, risk gates are wired to the submit path, submit lease / duplicate-prevention is integration-verified, sandbox artifact labeling is enforced at persistence/API/dashboard/report boundaries, and no P0/P1 blockers remain.

Actual sandbox order submission is not approved.

## Boundary Confirmation

| Boundary | Value |
| --- | --- |
| Orders submitted | `false` |
| OrderIntent rows created | `false` |
| PreparedVenueOrder rows created | `false` |
| ExecutionReadinessAssessment rows created | `false` |
| SubmittedOrder rows created | `false` |
| Executable approvals created | `false` |
| Private/signed/order endpoint calls made | `false` |
| Exchange API keys used | `false` |
| Paper trading added | `false` |
| Live trading added | `false` |
| Money Flow rules changed | `false` |
| Routing expansion added | `false` |
| Evidence packs generated | `false` |

