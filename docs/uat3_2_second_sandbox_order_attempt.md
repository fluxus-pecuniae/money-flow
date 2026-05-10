# UAT3.2 Second Sandbox Order Attempt

## Scope

Status: `blocked`

UAT3.2 is one approval-gated Hyperliquid testnet/sandbox lifecycle probe after fixed-key account/API-wallet readiness preflight. It is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

Paper trading is not approved. Live trading is not approved. Additional sandbox/testnet order attempts require separate approval.

## Founder / Operator Approval

Approval text presence: `verified`

```text
FOUNDER / OPERATOR APPROVAL — UAT3.2 SECOND SANDBOX ORDER ATTEMPT

I approve one approval-gated sandbox/testnet order submission attempt under the exact scope below.

Approved scope:
- Venue: Hyperliquid testnet / sandbox only
- Symbol: ETH USDC perpetual
- Purpose: sandbox lifecycle plumbing validation only
- Strategy status: not a Money Flow performance test
- Order source: manual sandbox lifecycle probe, not an approved strategy signal
- Maximum order count: 1 order attempt
- Order type: non-marketable limit order or post-only limit order if supported
- Side: buy/open only if it can be placed safely as non-marketable; otherwise block
- Maximum notional: use the minimum practical testnet notional, capped at 10 USDC equivalent
- Expected lifecycle: submit -> accepted/open or rejected -> cancel if open -> reconcile
- If unexpectedly filled: stop, report immediately, and do not place any additional order without separate approval
- Environment: sandbox/testnet only
- Live endpoint access: not approved
- Paper trading: not approved
- Live trading: not approved
- Broad top-20 order submission: not approved
- Repeated orders: not approved
- Auto-submit: not approved

Required gates:
- sandbox runtime policy must pass
- sandbox/testnet account/API-wallet readiness must pass
- live-fed sandbox drawdown must be available
- approval scope must match this approval exactly
- sandbox risk gates must pass
- submit lease / duplicate prevention must pass
- sandbox artifact labels must be enforced
- no live endpoint may be reachable
- all secrets must remain redacted

This approval does not authorize paper trading, live trading, production auto-submit, real-capital trading, or additional sandbox orders.
```

## Fixed-Key Account / API-Wallet Readiness

Status: `blocked`

| Field | Value |
| --- | --- |
| checked | `true` |
| account role | `missing` |
| signer role | `missing` |
| signer is target account | `false` |
| API wallet authorized for account | `false` |
| sandbox account equity available | `true` |
| sandbox account equity sufficient | `false` |
| live-fed drawdown verified | `true` |
| drawdown not stale | `true` |
| account address | `0x0bf8...a3ee` |
| signer address | `0x1155...f669` |

## Gate Results

| Gate | Status |
| --- | --- |
| Runtime policy | `blocked` |
| Sandbox endpoint verification | `verified` |
| Approval scope | `verified` |
| Risk gate | `blocked` |
| Live-fed drawdown | `sandbox_drawdown_feed_live_fed_verified` |
| Submit lease / duplicate prevention | `verified` |
| Sandbox artifact labels | `verified` |
| Live endpoint access | `false` |
| Paper trading | `not approved` |
| Live trading | `not approved` |

## Order Request Sanitized Summary

```json
{}
```

## Order Response Sanitized Summary

```json
{}
```

## Lifecycle Result

| Field | Value |
| --- | --- |
| Order attempt count | `0` |
| Order status | `blocked` |
| Cancel status | `not_attempted` |
| Reconciliation status | `not_attempted` |
| Unexpected fill | `false` |
| Open order remains | `false` |
| Unknown state | `false` |

Cancel response:

```json
{}
```

Reconciliation summary:

```json
{}
```

## Sandbox Drawdown

Source: `sandbox_account`

Not live account: `true`

Unavailable fields:

- `sandbox_realized_pnl`
- `sandbox_unrealized_pnl`
- `open_positions_summary`

## Side-Effect Confirmation

| Artifact / Behavior | Created / Enabled |
| --- | --- |
| OrderIntent | `false` |
| PreparedVenueOrder | `false` |
| SubmittedOrder | `false` |
| Executable approval | `false` |
| Paper trading | `false` |
| Live trading | `false` |

## Reason Codes

- `fixed_key_account_api_wallet_readiness_failed`
- `hyperliquid_testnet_user_not_found`
- `hyperliquid_testnet_api_wallet_not_found`
- `hyperliquid_testnet_api_wallet_not_authorized_for_account`
- `sandbox_account_equity_insufficient`

## Secrets Redaction

Status: `verified`

The report includes only sanitized request/response summaries. It does not include private keys, raw authorization headers, raw signed payloads, or raw signatures.

## No-Live / No-Paper Confirmation

- Live endpoint access: `false`
- Paper trading: `not approved`
- Live trading: `not approved`
- Broad top-20 order submission: `not approved`
- Production auto-submit: `not approved`
- Money Flow performance validation: `not performed`

## Future Dashboard Roadmap Capture

Future requested phase: `UAT4.0 — Live UAT Trading Dashboard / Chart Cockpit`.

Requested capabilities: live charts for watched pairs, green entry arrows, red exit arrows, routed orders tab, observed/traded watchlist, market data for watched pairs, EMA5 / EMA10 / SMA20 / RSI / MACD overlays, regime/trend context if available, UAT order lifecycle overlay, sandbox/not-live labels, and no paper/live confusion.

UAT3.2 does not implement this dashboard phase.

## Next Readiness Decision

`UAT3.3 is blocked`

## UAT3.3 Follow-Up

Status: `implemented`

UAT3.3 later resolved the Hyperliquid account-targeting ambiguity and ETH tick/lot precision blocker. Normal master/user mode now omits `vaultAddress`; subaccount/vault mode uses only the explicit configured subaccount/vault target. The UAT3.3 runner verified signer authorization for the configured subaccount, generated a sanitized exchange-valid ETH post-only planned order under 10 USDC notional, and then correctly blocked before `/exchange` because the target subaccount live-fed sandbox equity was `0.0`.

UAT3.3 did not submit an order, did not call order/cancel/amend/retry endpoints, and did not approve paper trading, live trading, broad top-20 order submission, or future orders.
