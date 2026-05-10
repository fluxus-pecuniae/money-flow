# UAT3.3 Hyperliquid Account Targeting Precision And Order Attempt

Recorded at: `2026-05-10T20:08:08.759004Z`

## Scope

UAT3.3 fixes Hyperliquid account targeting and tick/lot precision, then runs one sandbox/testnet ETH manual lifecycle probe only if gates pass.

UAT3.3 is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

Approval text presence: `verified`

## Account Targeting

Status: `verified`

```json
{
  "account_role": "subaccount",
  "endpoint_is_testnet": true,
  "environment": "testnet",
  "signer_address_abbrev": "0xd4c9...a551",
  "target_account_abbrev": "0xb645...34a9",
  "vaultAddress_abbrev_if_present": "0xb645...34a9",
  "vaultAddress_present": true
}
```

Normal master/user account mode omits `vaultAddress`. Subaccount/vault mode uses `vaultAddress` only for the explicit subaccount/vault target.

## Precision Formatter

Status: `needs_followup`

Hyperliquid price formatting enforces up to five significant figures and no more than `6 - szDecimals` decimals for perpetuals. Size formatting floors to `szDecimals`.

| Symbol | Asset id | szDecimals | Max price decimals | Sample mid | Formatted post-only buy price | Formatted size | Passed | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | 3 | 5 | 1 | 82950.5 | 82950 | 0.00012 | true |  |
| ETH | 4 | 4 | 2 | 2440.75 | 2440.7 | 0.004 | true |  |
| SOL | 0 | 2 | 4 | 98.125 | 98.125 | 0.1 | true |  |
| XRP | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ZEC | 193 | 0 | 6 | 138.65 | 138.65 | 1 | true |  |
| BNB | 6 | 3 | 3 | 663.23 | 663.23 | 0.015 | true |  |
| SUI | 25 | 1 | 5 | 1.3797 | 1.3797 | 7.2 | true |  |
| TON | 44 | 1 | 5 | 2.41855 | 2.4185 | 4.1 | true |  |
| DOGE | 173 | 0 | 6 | 0.11115 | 0.11115 | 89 | true |  |
| TRX | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| LAYER | 159 | 0 | 6 | 0.12514 | 0.12514 | 79 | true |  |
| CHIP | 207 | 0 | 6 | 0.065451 | 0.065451 | 152 | true |  |
| UNI | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ONDO | 87 | 0 | 6 | 0.420245 | 0.42024 | 23 | true |  |
| AAVE | 21 | 2 | 4 | 103.01 | 103.01 | 0.09 | true |  |

## Gate Results

| Gate | Status |
| --- | --- |
| Approval | `True` |
| Endpoint testnet | `True` |
| Account/API-wallet readiness | `False` |
| Runtime policy | `True` |
| Risk gate | `True` |
| Submit lease | `True` |
| Sandbox labels | `True` |
| Live-fed drawdown | `sandbox_drawdown_feed_live_fed_verified` |

## Side-Effect Confirmation

| Artifact / Behavior | Created / Enabled |
| --- | --- |
| OrderIntent | `false` |
| PreparedVenueOrder | `false` |
| SubmittedOrder | `false` |
| Executable approval | `false` |
| Paper trading | `false` |
| Live trading | `false` |

## Order Request Sanitized Summary

```json
{
  "account_role": "subaccount",
  "action_summary": {
    "grouping": "na",
    "orders": [
      {
        "a": 4,
        "b": true,
        "c": "0xe7219956c4cd07a387eabfc257cb943e",
        "p": "2438.9",
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
  "dry_run_planned_not_submitted": true,
  "endpoint": "/exchange",
  "endpoint_category": "sandbox_order_submission",
  "endpoint_is_testnet": true,
  "environment": "testnet",
  "estimated_notional": "9.99949",
  "limit_price": "2438.9",
  "max_price_decimals": 2,
  "order_type": "post_only_limit",
  "price_precision_reason": "price_formatted_down_5_sig_figs_and_max_2_decimals",
  "quantity": "0.0041",
  "raw_signed_payload_included_in_report": false,
  "side": "buy",
  "signature_included_in_report": false,
  "signer_address_abbrev": "0xd4c9...a551",
  "size_precision_reason": "size_formatted_down_sz_decimals_4",
  "symbol": "ETH",
  "target_account_abbrev": "0xb645...34a9",
  "tif": "Alo",
  "vaultAddress_abbrev_if_present": "0xb645...34a9",
  "vaultAddress_present": true
}
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

Reconciliation:

```json
{}
```

## Reason Codes

- `sandbox_account_equity_insufficient`

## Boundary Confirmation

- Live endpoint used: `false`
- Paper trading: `not approved`
- Live trading: `not approved`
- Broad top-20 order submission: `not approved`
- Production auto-submit: `not approved`
- Money Flow performance validation: `not performed`
- Secrets included in report: `false`

## UAT4.0 Dashboard Roadmap Capture

Future requested phase: `UAT4.0 - Live UAT Trading Dashboard / Chart Cockpit`.

Requested capabilities: live charts for watched pairs; green entry arrows; red exit arrows; routed orders tab; observed/traded watchlist; market data for watched pairs; EMA5 / EMA10 / SMA20 / RSI / MACD overlays; regime/trend context if available; UAT order lifecycle overlay; sandbox/not-live labels; and no paper/live confusion.

UAT3.3 does not implement UAT4.0.

## Next Readiness Decision

`UAT3.4 is blocked`
