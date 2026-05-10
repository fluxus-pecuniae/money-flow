# UAT3.0.6 Sandbox Submit Path Dry-Run Wiring

Recorded at: `2026-05-10T15:40:00Z`

## Scope

UAT3.0.6 wires the future sandbox submit path in dry-run mode only. It composes the executable gate chain that a later UAT3.1 sandbox/testnet order attempt must satisfy, while keeping all order transport and persistence disabled.

UAT3.0.6 does not submit orders, does not call order/cancel/amend/retry endpoints, does not create real `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or executable approval artifacts, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Actual sandbox order submission is not approved. Exchange order submission is not approved. Paper trading is not approved. Live trading is not approved.

## Non-Goals

- No actual UAT3.1 sandbox order submission.
- No order, cancel, amend, retry, recovery, private order, or live endpoint call.
- No exchange API-key use for order paths.
- No persisted order, prepared-order, readiness, submitted-order, or executable approval artifact.
- No paper trading or live trading.
- No Money Flow rule changes.
- No routing expansion, route executor, cross-venue retry, or automatic top-20 order submission.

## Dry-Run Submission Plan

Status: `implemented`.

UAT3.0.6 adds `UAT3SandboxSubmissionPlan`, a non-persistent dry-run plan object for the future UAT3.1 sandbox/testnet submit path.

The plan records:

| Field | Status |
| --- | --- |
| `uat_run_id` | `implemented` |
| `venue` | `implemented` |
| `environment` | `sandbox_or_testnet_required` |
| `account_id` | `implemented` |
| `symbol` | `implemented` |
| `component` | `implemented` |
| `candidate_id` | `implemented` |
| `order_side` | `implemented` |
| `order_type` | `implemented` |
| `requested_notional_or_quantity` | `implemented` |
| `max_notional_or_quantity` | `implemented` |
| `approval_id` | `implemented` |
| `idempotency_key` | `implemented` |
| `submit_lease_key` | `implemented` |
| `sandbox_labels` | `implemented` |
| `runtime_policy_snapshot` | `implemented` |
| `drawdown_feed_status` | `implemented` |
| `risk_gate_result` | `implemented` |
| `approval_scope_result` | `implemented` |
| `submit_lease_result` | `implemented` |
| `artifact_label_result` | `implemented` |
| `endpoint_category` | `implemented` |
| `would_submit_if_enabled` | `false_in_uat3_0_6` |
| `creates_order_intent` | `false` |
| `creates_prepared_order` | `false` |
| `creates_submitted_order` | `false` |
| `creates_executable_approval` | `false` |
| `calls_exchange` | `false` |

The dry-run plan is not a trading artifact and is not persisted as an order.

## Executable Gate Chain

Status: `implemented`.

UAT3.0.6 adds:

```text
UAT3SandboxSubmitDryRunService
evaluate_uat3_sandbox_submit_path_dry_run
```

The dry-run gate chain evaluates, in order:

1. `SandboxRuntimePolicy`.
2. Founder/operator actual-submission approval status.
3. Sandbox artifact-label boundary validation.
4. Approval scope validation.
5. Live-fed sandbox drawdown status.
6. Sandbox risk gate validation.
7. Submit-lease / duplicate-prevention validation.
8. Adapter endpoint classification.
9. Final no-submit dry-run result.

Output includes:

- `allowed_for_future_submit`;
- `blocked`;
- `reason_codes`;
- `gate_results`;
- `submission_plan`;
- `would_call_exchange = false`;
- `would_create_order_intent = false`;
- `would_create_prepared_order = false`;
- `would_create_submitted_order = false`;
- `would_create_executable_approval = false`;
- `would_submit_if_enabled = false`.

The service does not persist anything, does not call adapters, does not call exchange transport, does not create approvals, and does not create order artifacts.

## Founder Actual-Submission Approval Requirement

Status: `implemented_blocking`.

UAT3.0.6 blocks unless a future founder/operator actual-submission approval exists. Missing approval returns:

```text
founder_operator_actual_sandbox_submission_approval_required
```

The required future approval is distinct from:

- UAT2.1 dashboard review;
- UAT3.0 design/scoping approval;
- UAT3.0.5 private read-only account-state verification approval.

Required future actual-submission approval wording must include:

```text
I approve one approval-gated sandbox/testnet order submission attempt under the exact scope below.
```

It must also specify venue, sandbox/testnet environment, symbol, component, maximum notional or quantity, maximum number of sandbox orders, allowed order type, time window, sandbox account id, kill switch / disable control, expected lifecycle to test, no live trading, no paper trading with real capital, no production auto-submit, no broad top-20 submission, and no repeated orders beyond the approved count.

UAT3.0.6 does not create executable approval records.

## Live-Fed Sandbox Drawdown Status

Status: `implemented_verified_input_consumed`.

The UAT3.0.6 dry-run path consumes the UAT3.0.5 verified drawdown status:

```text
sandbox_drawdown_feed_live_fed_verified
```

The dry-run blocks for:

- `sandbox_drawdown_feed_missing`;
- `sandbox_drawdown_feed_fixture_only`;
- `sandbox_drawdown_feed_stale`;
- `sandbox_drawdown_feed_not_live_fed_verified`;
- `sandbox_drawdown_feed_not_labeled_not_live_account`;
- `sandbox_drawdown_threshold_breached`.

UAT3.0.6 does not refresh private read-only account state and does not call private endpoints. It uses the verified status/report boundary from UAT3.0.5 for dry-run wiring.

## Approval-Scope Wiring

Status: `fixture_verified`.

The dry-run gate calls the existing approval scope validator and blocks for:

- missing approval / missing UAT run id;
- wrong symbol;
- wrong venue;
- wrong account;
- wrong component;
- expired approval;
- quantity above max;
- non-positive quantity;
- live environment;
- paper environment;
- broad top-20 approval;
- consumed approval;
- missing one-time-use intent.

No executable approval rows are created.

## Risk-Gate Wiring

Status: `fixture_verified`.

The dry-run gate calls the sandbox risk evaluator and blocks for:

- runtime policy blockers;
- notional over limit;
- non-positive notional;
- order count exceeded;
- daily order count exceeded;
- drawdown limit breached;
- unsupported symbol;
- forbidden venue/account;
- live account;
- live endpoint;
- kill switch enabled;
- sandbox submission disabled.

No order artifacts are created.

## Submit-Lease / Duplicate-Prevention Wiring

Status: `fixture_verified`.

The dry-run gate calls the submit preflight / duplicate-prevention fixture and blocks for:

- missing submit lease;
- missing idempotency key;
- missing approval id;
- missing UAT run id;
- non-sandbox environment;
- duplicate same approval/candidate;
- prior submit uncertainty;
- cross-venue retry;
- top-20 fanout;
- route executor behavior.

No real submit lease is created and no order is submitted.

## Endpoint Classification

Status: `implemented_no_transport`.

UAT3.0.6 adds `SandboxAdapterEndpointClassification` plus a UAT3.0.6 endpoint-classification check.

Expected future UAT3.1 submit category:

```text
sandbox_order_submission
```

UAT3.0.6 result:

| Field | Value |
| --- | --- |
| `endpoint_category` | `sandbox_order_submission` |
| `transport_invoked` | `false` |
| `calls_exchange` | `false` |

The dry-run blocks if the endpoint category is `unknown`, if it is not `sandbox_order_submission`, or if transport/exchange invocation is detected.

## Artifact-Label Boundary Enforcement

Status: `implemented`.

The UAT3.0.6 dry-run path uses the UAT3.0.3 sandbox artifact boundary helpers before any future artifact would cross:

- persistence;
- API serialization;
- dashboard display;
- report generation.

Required labels:

- `sandbox = true`;
- `testnet = true`;
- `not_live = true`;
- `not_paper = true`;
- `uat_run_id` present;
- `sandbox_order = true`;
- `live_endpoint_access = false`;
- `real_capital = false`.

The dry-run blocks if labels are missing or unsafe.

## UAT3.1 Readiness Decision

`UAT3.1 is blocked`.

Remaining blockers:

- `founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission`;
- explicit UAT3.1 phase approval to enable actual sandbox/testnet order transport;
- final operator review of the dry-run submit-path output before enabling the real submit attempt.

UAT3.0.6 wires the future submit path in dry-run mode, consumes live-fed sandbox drawdown status, and integrates approval, risk, submit-lease, endpoint classification, and artifact-label gates. It does not approve or perform actual sandbox order submission.

UAT3.1 first approval-gated sandbox order may proceed only after founder/operator actual-submission approval exists and a later explicit UAT3.1 phase enables the real sandbox/testnet submit attempt under the exact approved scope.

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
| Private account endpoints called | `false` |
| Private order endpoints called | `false` |
| Order/cancel/amend/retry endpoints called | `false` |
| Signed order endpoint calls made | `false` |
| Exchange API keys used | `false` |
| Paper trading added | `false` |
| Live trading added | `false` |
| Money Flow rules changed | `false` |
| Routing expansion added | `false` |
| Evidence packs generated | `false` |
