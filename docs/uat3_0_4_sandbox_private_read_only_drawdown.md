# UAT3.0.4 Sandbox Private Read-Only Drawdown

Recorded at: `2026-05-10T13:58:00Z`

Follow-up: UAT3.0.5 validated the exact private-read-only approval text and added sandbox/testnet credential environment checks plus Hyperliquid sandbox account-state drawdown parsing. The local `HYPERLIQUID_UAT_SANDBOX_*` environment variables were missing, so no credentials were loaded, no API keys were used, no private endpoints were called, and live-fed sandbox drawdown remains blocked.

## Scope

UAT3.0.4 is private read-only sandbox drawdown readiness and credential-boundary preflight.

It defines the policy, endpoint categories, credential safety checks, drawdown-feed model, and no-order boundary needed before any later sandbox/testnet account-state verification.

UAT3.0.4 does not submit orders, does not call order/cancel/amend/retry endpoints, does not create real `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or executable approval artifacts, does not add paper trading, does not add live trading, does not change Money Flow rules, does not add routing expansion, and does not generate evidence packs.

Actual sandbox order submission is not approved. Exchange order submission is not approved. Paper trading is not approved. Live trading is not approved.

## Non-Goals

- No actual UAT3.1 sandbox order submission.
- No order submission, cancel, amend, retry, or recovery endpoint calls.
- No live exchange API-key use.
- No sandbox/testnet credential use without explicit approval.
- No private endpoint calls without explicit approval.
- No persisted order, prepared-order, readiness, submitted-order, or executable approval artifacts.
- No paper trading or live trading.
- No Money Flow rule changes.
- No routing expansion or automatic top-20 order submission.

## Approval Status For Private Read-Only Credentials

Status: `blocked`.

This section records the approval status for private read-only credentials.

Required approval language:

```text
I approve UAT3.0.4 sandbox/testnet private read-only credential use for account-state and drawdown-feed verification only.
```

Current status: `explicit approval not present`.

Because the required approval was not present in the task context, UAT3.0.4 did not use API keys, did not load credentials, did not call sandbox/testnet private endpoints, and did not verify a live-fed sandbox account drawdown feed.

This approval would not authorize:

- order submission;
- cancel / amend / retry;
- private order endpoints;
- paper trading;
- live trading;
- live endpoint access;
- production auto-submit;
- broad top-20 order submission.

## Credential Boundary Status

Status: `implemented_blocked_without_approval`.

UAT3.0.4 adds credential-boundary validation for future sandbox/testnet private read-only account-state use. The boundary checks that credentials are sandbox/testnet-only, loaded only from an approved source, not committed, not logged, not written to Obsidian, not included in review bundles, and not exposed through raw authorization headers.

Representative credential/config payloads are redacted before display. The redaction checks cover authorization headers, bearer tokens, API keys, secrets, passwords, private keys, and database URL passwords.

Current run truth:

| Field | Status |
| --- | --- |
| Explicit private read-only approval | `missing` |
| Sandbox/testnet credentials loaded | `false` |
| API keys used | `false` |
| Private endpoints called | `false` |
| Raw Authorization header logged | `false` |
| Credentials written to Obsidian | `false` |
| Credentials included in review bundle | `false` |

## Private Read-Only Account Policy

Status: `implemented_fail_closed`.

Allowed in UAT3.0.4 only with explicit approval:

| Category | Status |
| --- | --- |
| `sandbox_private_read_only_account` | `allowed_with_explicit_approval_only` |
| `sandbox_private_read_only_position` | `allowed_with_explicit_approval_only` |
| `sandbox_private_read_only_balance` | `allowed_with_explicit_approval_only` |
| `sandbox_private_read_only_equity` | `allowed_with_explicit_approval_only` |

Forbidden in UAT3.0.4:

| Category | Status |
| --- | --- |
| `sandbox_order_submission` | `blocked` |
| `sandbox_order_cancel` | `blocked` |
| `sandbox_order_amend` | `blocked` |
| `sandbox_order_retry` | `blocked` |
| `live_private_forbidden` | `blocked` |
| `unknown` | `blocked` |

The policy fails closed. Missing approval, missing credentials, live credentials, live endpoint access, enabled paper/live trading, enabled global exchange order submission, enabled sandbox order submission, or unknown endpoint categories block the path.

## Endpoint Classification

Status: `implemented`.

UAT3.0.4 separates sandbox private read-only account-state categories from sandbox order-capable categories:

| Endpoint category | Classification | UAT3.0.4 behavior |
| --- | --- | --- |
| `sandbox_private_read_only_account` | account-state read | blocked until explicit approval and safe credentials exist |
| `sandbox_private_read_only_position` | position read | blocked until explicit approval and safe credentials exist |
| `sandbox_private_read_only_balance` | balance read | blocked until explicit approval and safe credentials exist |
| `sandbox_private_read_only_equity` | account-equity read | blocked until explicit approval and safe credentials exist |
| `sandbox_order_submission` | order-capable | always blocked in UAT3.0.4 |
| `sandbox_order_cancel` | order-capable | always blocked in UAT3.0.4 |
| `sandbox_order_amend` | order-capable | always blocked in UAT3.0.4 |
| `sandbox_order_retry` | order-capable | always blocked in UAT3.0.4 |
| `live_private_forbidden` | live private | always blocked |
| `unknown` | unknown | always blocked |

## Sandbox Account Drawdown Feed Status

Status: `implemented_model_only_blocked_live_feed`.

UAT3.0.4 adds a sandbox account drawdown feed model that can represent:

| Field | Status |
| --- | --- |
| Venue | `implemented` |
| Sandbox account id | `implemented` |
| Source | `sandbox_account` |
| Not live account | `true` |
| Timestamp | `implemented` |
| Sandbox account equity | `implemented_if_available` |
| Sandbox realized PnL | `explicitly_unavailable_if_missing` |
| Sandbox unrealized PnL | `explicitly_unavailable_if_missing` |
| Open positions summary | `explicitly_unavailable_if_missing` |
| Max sandbox equity | `implemented_if_available` |
| Min sandbox equity | `implemented_if_available` |
| Max drawdown amount | `computed_if_equity_available` |
| Max drawdown percent | `computed_if_equity_available` |
| Drawdown threshold | `implemented` |
| Threshold breached | `computed_if_equity_available` |
| Reason codes | `implemented` |

Supported drawdown feed statuses:

- `sandbox_drawdown_feed_missing`
- `sandbox_drawdown_feed_fixture_only`
- `sandbox_drawdown_feed_private_read_only_verified`
- `sandbox_drawdown_feed_live_fed_verified`

Current run status: `sandbox_drawdown_feed_missing`.

No private endpoint was called, so unavailable account fields remain unavailable rather than invented.

## Fields Available / Unavailable

Status: `blocked_without_private_read_only_approval`.

No sandbox/testnet account snapshot was fetched in UAT3.0.4 because the required private read-only approval was not present.

| Field | Current UAT3.0.4 Status |
| --- | --- |
| Sandbox account equity | `unavailable_private_read_only_not_approved` |
| Sandbox realized PnL | `unavailable_private_read_only_not_approved` |
| Sandbox unrealized PnL | `unavailable_private_read_only_not_approved` |
| Open positions summary | `unavailable_private_read_only_not_approved` |
| Max sandbox equity | `unavailable_private_read_only_not_approved` |
| Drawdown amount / percent | `unavailable_private_read_only_not_approved` |

## Redaction Confirmation

Status: `verified_representative`.

Tests verify that representative sandbox credential/config payloads redact:

- `Authorization: Bearer ...`
- `api_key`
- `secret`
- `password`
- `private_key`
- PostgreSQL URL passwords

The report, Obsidian notes, and review bundle contain no sandbox/testnet credential values.

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
| real `SubmittedOrder` created | `false` |
| executable approval created | `false` |

This remains true even when the future sandbox private read-only account categories are enabled in fixture policy.

## UAT3 Dry-Run Preflight Integration

Status: `implemented`.

The UAT3 dry-run preflight can now consume drawdown feed status values including:

- `sandbox_drawdown_feed_missing`
- `sandbox_drawdown_feed_fixture_only`
- `sandbox_drawdown_feed_private_read_only_verified`
- `sandbox_drawdown_feed_live_fed_verified`

For UAT3.1 readiness, the required status remains:

```text
sandbox_drawdown_feed_live_fed_verified
```

`sandbox_drawdown_feed_private_read_only_verified` is useful readiness evidence, but it does not by itself approve actual sandbox order submission unless all other UAT3.1 gates are wired and founder/operator actual-submission approval exists.

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

UAT3.1 first approval-gated sandbox order may proceed only after founder/operator actual-submission approval exists, sandbox runtime policy is wired to a real sandbox/testnet path, sandbox account drawdown feed is live-fed from sandbox/testnet account truth, executable approval-scope gate is wired, risk gate is wired to the submit path, submit-lease / duplicate-prevention is integration-verified, sandbox artifact labels are enforced at persistence/API/dashboard/report boundaries, the real sandbox submit path exists, and no P0/P1 blockers remain.

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
