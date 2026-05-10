# UAT3.0.5 Sandbox Private Read-Only Drawdown Verification

Recorded at: `2026-05-10T14:20:21Z`

## Scope

UAT3.0.5 is sandbox/testnet private read-only account-state and drawdown-feed verification readiness.

It validates the founder/operator approval boundary, sandbox/testnet credential environment boundary, credential redaction, private read-only endpoint category separation, no-order endpoint lockout, sandbox drawdown feed status, and UAT3 preflight drawdown status.

UAT3.0.5 does not submit orders, does not call order/cancel/amend/retry endpoints, does not create real `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or executable approval artifacts, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Actual sandbox order submission is not approved. Exchange order submission is not approved. Paper trading is not approved. Live trading is not approved.

## Status Summary

| Field | Status |
| --- | --- |
| approval status | `verified` |
| credential source status | `blocked_missing_local_environment` |
| sandbox drawdown feed status | `sandbox_drawdown_feed_missing` |
| private account endpoints called | `false` |
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

Status: `blocked_missing_local_environment`.

UAT3.0.5 uses local environment-variable boundary checks only. Credentials must not be pasted into source, docs, Obsidian, reports, tests, or logs.

Expected local environment variables:

| Variable | Current status |
| --- | --- |
| `HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY` | `missing` |
| `HYPERLIQUID_UAT_SANDBOX_ACCOUNT` | `missing` |
| `HYPERLIQUID_UAT_SANDBOX_BASE_URL` | `missing` |

Because the required local sandbox/testnet credential environment was missing in this run, UAT3.0.5 did not load credentials, did not use API keys, did not call sandbox/testnet private endpoints, and did not verify live-fed sandbox account drawdown.

If credentials are supplied later, the base URL must be provably sandbox/testnet. The live Hyperliquid URL `https://api.hyperliquid.xyz` is explicitly blocked for UAT3.0.5 private read-only verification. Do not use live endpoints as fallback.

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

Status: `blocked_no_private_call`.

Allowed only after approval and safe sandbox/testnet credentials:

| Category | UAT3.0.5 status |
| --- | --- |
| `sandbox_private_read_only_account` | `blocked_missing_local_environment` |
| `sandbox_private_read_only_balance` | `blocked_missing_local_environment` |
| `sandbox_private_read_only_position` | `blocked_missing_local_environment` |
| `sandbox_private_read_only_equity` | `blocked_missing_local_environment` |

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

Status: `verified_fixture`.

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

Status: `blocked_missing_local_environment`.

Current UAT3.0.5 drawdown status:

```text
sandbox_drawdown_feed_missing
```

No sandbox/testnet account-state response was fetched because local sandbox/testnet credentials were not configured. UAT3.0.5 therefore did not compute a live-fed sandbox account drawdown feed.

The implementation can parse caller-supplied Hyperliquid sandbox/testnet account-state payloads into a feed labeled:

- `source = sandbox_account`;
- `not_live_account = true`;
- `status = sandbox_drawdown_feed_live_fed_verified`.

That path remains gated by exact UAT3.0.5 approval, sandbox/testnet endpoint verification, credential-boundary validation, and private-read-only endpoint category checks.

## Fields Available / Unavailable

Status: `blocked_missing_local_environment`.

| Field | Current UAT3.0.5 status |
| --- | --- |
| Sandbox account equity | `unavailable_missing_local_sandbox_credentials` |
| Sandbox realized PnL | `unavailable_missing_local_sandbox_credentials` |
| Sandbox unrealized PnL | `unavailable_missing_local_sandbox_credentials` |
| Open positions summary | `unavailable_missing_local_sandbox_credentials` |
| Max sandbox equity | `unavailable_missing_local_sandbox_credentials` |
| Min sandbox equity | `unavailable_missing_local_sandbox_credentials` |
| Drawdown amount / percent | `unavailable_missing_local_sandbox_credentials` |

If an approved sandbox/testnet account response omits fields, UAT3.0.5 marks them with:

```text
unavailable_from_sandbox_account_response
```

Do not invent missing account values.

## UAT3 Preflight Drawdown Status

Status: `implemented_blocked_current_run`.

UAT3 dry-run preflight can consume:

- `sandbox_drawdown_feed_missing`;
- `sandbox_drawdown_feed_fixture_only`;
- `sandbox_drawdown_feed_private_read_only_verified`;
- `sandbox_drawdown_feed_live_fed_verified`.

Current UAT3.0.5 status remains:

```text
sandbox_drawdown_feed_missing
```

The prior live-fed sandbox account drawdown blocker is not cleared in this run because local sandbox/testnet credentials were missing and no account-state response was fetched.

## UAT3.1 Readiness Decision

`UAT3.1 is blocked`.

Remaining blockers:

- `founder_operator_explicit_approval_required_before_uat3_1_actual_sandbox_submission`
- `sandbox_account_drawdown_feed_missing`
- `sandbox_private_endpoint_separation_not_wired_to_real_sandbox_account`
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
| Private account endpoints called | `false` |
| Private order endpoints called | `false` |
| Signed order endpoint calls made | `false` |
| Exchange API keys used | `false` |
| Paper trading added | `false` |
| Live trading added | `false` |
| Money Flow rules changed | `false` |
| Routing expansion added | `false` |
| Evidence packs generated | `false` |
