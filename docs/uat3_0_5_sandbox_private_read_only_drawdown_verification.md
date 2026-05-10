# UAT3.0.5 Sandbox Private Read-Only Drawdown Verification

Recorded at: `2026-05-10T14:20:21Z`

Verification rerun at: `2026-05-10T15:06:29Z`

## Scope

UAT3.0.5 is sandbox/testnet private read-only account-state and drawdown-feed verification readiness.

It validates the founder/operator approval boundary, sandbox/testnet credential environment boundary, credential redaction, private read-only endpoint category separation, no-order endpoint lockout, sandbox drawdown feed status, and UAT3 preflight drawdown status.

UAT3.0.5 does not submit orders, does not call order/cancel/amend/retry endpoints, does not create real `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or executable approval artifacts, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Actual sandbox order submission is not approved. Exchange order submission is not approved. Paper trading is not approved. Live trading is not approved.

## Status Summary

| Field | Status |
| --- | --- |
| approval status | `verified` |
| credential source status | `verified_local_environment` |
| sandbox drawdown feed status | `sandbox_drawdown_feed_live_fed_verified` |
| private account endpoints called | `true_read_only_account_state_only` |
| order endpoints called | `false` |
| API keys used | `false` |
| UAT3.1 readiness | `blocked` |

## Non-Goals

- No actual UAT3.1 sandbox order submission.
- No order submission, cancel, amend, retry, or recovery endpoint calls.
- No live exchange API-key use.
- No live endpoint access.
- No persisted order, prepared-order, readiness, submitted-order, or executable approval artifacts.
- No paper trading or live trading.
- No Money Flow rule changes.
- No routing expansion or automatic top-20 order submission.

## Approval Status

Status: `verified`.

Required approval language:

```text
I approve UAT3.0.5 sandbox/testnet private read-only credential use for account-state and drawdown-feed verification only.
```

The exact UAT3.0.5 private read-only approval text is present in the task context and this report.

This approval does not authorize:

- order submission;
- cancel / amend / retry;
- private order endpoints;
- paper trading;
- live trading;
- live endpoint access;
- production auto-submit;
- broad top-20 order submission.

This approval is not founder/operator approval for actual UAT3.1 sandbox order submission.

## Credential Source Status

Status: `verified_local_environment`.

UAT3.0.5 uses local environment-variable boundary checks only. Credentials must not be pasted into source, docs, Obsidian, reports, tests, or logs.

Expected local environment variables:

| Variable | Current status |
| --- | --- |
| `HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY` | `present_redacted_not_logged` |
| `HYPERLIQUID_UAT_SANDBOX_ACCOUNT` | `present_redacted_not_logged` |
| `HYPERLIQUID_UAT_SANDBOX_BASE_URL` | `verified_testnet_https` |

The sandbox/testnet base URL was verified as `https://api.hyperliquid-testnet.xyz`. The live Hyperliquid URL `https://api.hyperliquid.xyz` remains explicitly blocked for UAT3.0.5 private read-only verification. Do not use live endpoints as fallback.

The UAT3.0.5 rerun used only the account identifier against the sandbox/testnet read-only account-state path. It did not sign a request, did not send an API key, and did not use the private key value.

## Redaction Status

Status: `verified_representative`.

Credential/config redaction tests cover representative:

- Authorization bearer tokens;
- private keys;
- API keys;
- secrets;
- passwords;
- database URL passwords.

No raw sandbox/testnet key or secret is included in this report, Obsidian, tests, source code, logs, or the review bundle.

## Private Read-Only Endpoint Categories Used

Status: `verified_private_read_only_account_state`.

Allowed only after approval and safe sandbox/testnet credentials:

| Category | UAT3.0.5 status |
| --- | --- |
| `sandbox_private_read_only_account` | `verified_read_only_account_state_http_200` |
| `sandbox_private_read_only_balance` | `represented_in_account_state_if_available` |
| `sandbox_private_read_only_position` | `represented_in_account_state_if_available` |
| `sandbox_private_read_only_equity` | `verified_account_equity_available` |

Forbidden in UAT3.0.5:

| Category | Status |
| --- | --- |
| `sandbox_order_submission` | `blocked` |
| `sandbox_order_cancel` | `blocked` |
| `sandbox_order_amend` | `blocked` |
| `sandbox_order_retry` | `blocked` |
| `live_private_forbidden` | `blocked` |
| `private_signed_order` | `blocked` |
| `unknown` | `blocked` |

Endpoint category checks run before any modeled transport. Order-capable categories remain blocked even when sandbox private read-only account access is enabled in fixtures.

## No-Order Endpoint Confirmation

Status: `verified_runtime_and_rerun`.

| Boundary | Value |
| --- | --- |
| order endpoints called | `false` |
| order submission remains blocked | `true` |
| cancel remains blocked | `true` |
| amend remains blocked | `true` |
| retry remains blocked | `true` |
| broad exchange order submission enabled | `false` |
| sandbox order submission enabled | `false` |
| live endpoint access | `false` |
| real `OrderIntent` created | `false` |
| real `PreparedVenueOrder` created | `false` |
| real `ExecutionReadinessAssessment` created | `false` |
| real `SubmittedOrder` created | `false` |
| executable approval created | `false` |

## Sandbox Drawdown Feed Status

Status: `verified_live_fed_sandbox_account`.

Current UAT3.0.5 drawdown status:

```text
sandbox_drawdown_feed_live_fed_verified
```

The rerun fetched sandbox/testnet account-state data from the approved Hyperliquid testnet base URL and computed a live-fed sandbox account drawdown feed. The feed is labeled:

- `source = sandbox_account`;
- `not_live_account = true`;
- `status = sandbox_drawdown_feed_live_fed_verified`.

The feed reported drawdown within limit. It did not imply live account equity, paper trading, live trading, or order approval.

## Fields Available / Unavailable

Status: `verified_partial_account_state`.

| Field | Current UAT3.0.5 status |
| --- | --- |
| Sandbox account equity | `available_redacted` |
| Sandbox realized PnL | `unavailable_from_sandbox_account_response` |
| Sandbox unrealized PnL | `unavailable_from_sandbox_account_response` |
| Open positions summary | `unavailable_from_sandbox_account_response` |
| Max sandbox equity | `available_redacted` |
| Min sandbox equity | `available_redacted` |
| Drawdown amount / percent | `computed_redacted_within_limit` |

If an approved sandbox/testnet account response omits fields, UAT3.0.5 marks them with:

```text
unavailable_from_sandbox_account_response
```

Do not invent missing account values.

## UAT3 Preflight Drawdown Status

Status: `implemented_verified_current_run`.

UAT3 dry-run preflight can consume:

- `sandbox_drawdown_feed_missing`;
- `sandbox_drawdown_feed_fixture_only`;
- `sandbox_drawdown_feed_private_read_only_verified`;
- `sandbox_drawdown_feed_live_fed_verified`.

Current UAT3.0.5 status remains:

```text
sandbox_drawdown_feed_live_fed_verified
```

The prior live-fed sandbox account drawdown blocker is cleared for the UAT3.0.5 private read-only account-state verification boundary. Actual UAT3.1 sandbox order submission remains blocked by the separate actual-submission approval, real submit-path wiring, executable gate wiring, and submit-lease integration blockers.

UAT3.0.6 follow-up status: the future sandbox submit path is now wired in dry-run mode through a non-persistent submission plan and gate chain that consumes this live-fed drawdown status, checks approval scope, risk gates, submit-lease duplicate prevention, endpoint classification, and sandbox labels, and still creates no order artifacts or exchange calls. Actual UAT3.1 sandbox order submission remains blocked until explicit founder/operator actual-submission approval and later transport enablement exist.

## UAT3.1 Readiness Decision

`UAT3.1 is blocked`.

Remaining blockers:

- `founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission`
- `sandbox_submit_path_not_implemented`
- `uat3_approval_scope_not_wired_to_executable_gate`
- `uat3_risk_gate_not_wired_to_submit_path`
- `uat3_submit_lease_lifecycle_not_integration_verified`

UAT3.1 first approval-gated sandbox order may proceed only after founder/operator actual-submission approval exists, sandbox runtime policy is wired to a real sandbox/testnet path, sandbox account drawdown feed is live-fed from sandbox/testnet account truth, executable approval-scope gate is wired, risk gate is wired to the submit path, submit-lease / duplicate-prevention is integration-verified, sandbox artifact labels are enforced at real persistence/API/dashboard/report boundaries, the real sandbox submit path exists, and no P0/P1 blockers remain.

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
| Private account endpoints called | `true_read_only_account_state_only` |
| Private order endpoints called | `false` |
| Signed order endpoint calls made | `false` |
| Exchange API keys used | `false` |
| Paper trading added | `false` |
| Live trading added | `false` |
| Money Flow rules changed | `false` |
| Routing expansion added | `false` |
| Evidence packs generated | `false` |
