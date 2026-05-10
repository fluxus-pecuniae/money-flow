# UAT3.1 First Sandbox Order Attempt

## Scope

Status: `verified`

UAT3.1 is one approval-gated Hyperliquid testnet/sandbox lifecycle probe. It is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

Paper trading is not approved. Live trading is not approved. Additional exchange order submission is not approved without a separate later approval.

## Founder / Operator Approval

Approval text presence: `verified`

```text
FOUNDER / OPERATOR APPROVAL — UAT3.1 FIRST SANDBOX ORDER ATTEMPT

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
- If unexpectedly filled: stop, report immediately, and do not place any additional order without a separate approval
- Environment: sandbox/testnet only
- Live endpoint access: not approved
- Paper trading: not approved
- Live trading: not approved
- Broad top-20 order submission: not approved
- Repeated orders: not approved
- Auto-submit: not approved

Required gates:
- sandbox runtime policy must pass
- live-fed sandbox drawdown must be available
- approval scope must match this approval exactly
- sandbox risk gates must pass
- submit lease / duplicate prevention must pass
- sandbox artifact labels must be enforced
- no live endpoint may be reachable
- all secrets must remain redacted

This approval does not authorize paper trading, live trading, production auto-submit, real-capital trading, or additional sandbox orders.
```

## Gate Results

| Gate | Status |
| --- | --- |
| Runtime policy | `verified` |
| Sandbox endpoint verification | `verified` |
| Approval scope | `verified` |
| Risk gate | `verified` |
| Live-fed drawdown | `sandbox_drawdown_feed_live_fed_verified` |
| Submit lease / duplicate prevention | `verified` |
| Sandbox artifact labels | `verified` |
| Live endpoint access | `false` |
| Paper trading | `not approved` |
| Live trading | `not approved` |

## Order Request Sanitized Summary

```json
{
  "action_summary": {
    "grouping": "na",
    "orders": [
      {
        "a": 4,
        "b": true,
        "c": "0xa533900ab41519026e71e25e35e3bf65",
        "p": "2414.59",
        "r": false,
        "s": "0.0041",
        "t": {
          "limit": {
            "tif": "Alo"
          }
        }
      }
    ],
    "type": "order"
  },
  "asset_id": 4,
  "client_order_id_present": true,
  "endpoint": "/exchange",
  "endpoint_category": "sandbox_order_submission",
  "estimated_notional": "9.899819",
  "limit_price": "2414.59",
  "order_type": "post_only_limit",
  "quantity": "0.0041",
  "raw_signed_payload_included_in_report": false,
  "side": "buy",
  "signature_included_in_report": false,
  "symbol": "ETH",
  "tif": "Alo"
}
```

## Order Response Sanitized Summary

```json
{
  "response": "User or API Wallet 0xacea3493d856724768a8fa7cf3e2d64454960aa9 does not exist.",
  "status": "err"
}
```

## Lifecycle Result

| Field | Value |
| --- | --- |
| Order attempt count | `1` |
| Order status | `rejected` |
| Cancel status | `not_required` |
| Reconciliation status | `completed` |
| Unexpected fill | `false` |
| Open order remains | `false` |
| Unknown state | `false` |

Cancel response:

```json
{}
```

Reconciliation summary:

```json
{
  "account_state": {
    "assetPositions": [],
    "crossMaintenanceMarginUsed": "0.0",
    "crossMarginSummary": {
      "accountValue": "0.0",
      "totalMarginUsed": "0.0",
      "totalNtlPos": "0.0",
      "totalRawUsd": "0.0"
    },
    "marginSummary": {
      "accountValue": "0.0",
      "totalMarginUsed": "0.0",
      "totalNtlPos": "0.0",
      "totalRawUsd": "0.0"
    },
    "time": 1778431276915,
    "withdrawable": "0.0"
  },
  "open_orders": []
}
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

- `order_rejected`
- `hyperliquid_testnet_user_or_api_wallet_not_found`

## Remaining Follow-Up

- `hyperliquid_testnet_user_or_api_wallet_not_found`: the single approved testnet order attempt reached the testnet submit endpoint but was rejected by venue account/API-wallet validation.
- Any accepted/open -> cancel lifecycle coverage requires a separate UAT3.2 scope and separate founder/operator approval after sandbox account/API-wallet configuration is reviewed.
- No repeated order attempt is approved by this report.

## Secrets Redaction

Status: `verified`

The report includes only sanitized request/response summaries. It does not include private keys, raw authorization headers, raw signed payloads, or raw signatures.

## Next Readiness Decision

`UAT3.2 additional sandbox lifecycle testing may be scoped`
