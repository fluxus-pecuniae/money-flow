# UAT3.3 Hyperliquid Account Targeting Precision And Order Attempt

Recorded at: `2026-05-11T05:15:20.315535Z`

## Scope

UAT3.3 fixes Hyperliquid account targeting and tick/lot precision, then runs one sandbox/testnet ETH manual lifecycle probe only if gates pass.

UAT3.3 is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

Approval text presence: `verified`

## Account Targeting

Status: `verified`

```json
{
  "account_role": "user",
  "endpoint_is_testnet": true,
  "environment": "testnet",
  "signer_address_abbrev": "0x0f42...04d9",
  "target_account_abbrev": "0x7580...8222",
  "vaultAddress_abbrev_if_present": null,
  "vaultAddress_present": false
}
```

Normal master/user account mode omits `vaultAddress`. Subaccount/vault mode uses `vaultAddress` only for the explicit subaccount/vault target.

## Precision Formatter

Status: `needs_followup`

Hyperliquid price formatting enforces up to five significant figures and no more than `6 - szDecimals` decimals for perpetuals. Size formatting floors to `szDecimals`.

| Symbol | Asset id | szDecimals | Max price decimals | Sample mid | Formatted post-only buy price | Formatted size | Passed | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | 3 | 5 | 1 | 80997.0 | 80997 | 0.00012 | true |  |
| ETH | 4 | 4 | 2 | 2345.3 | 2345.3 | 0.0042 | true |  |
| SOL | 0 | 2 | 4 | 97.215 | 97.215 | 0.1 | true |  |
| XRP | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ZEC | 193 | 0 | 6 | 138.65 | 138.65 | 1 | true |  |
| BNB | 6 | 3 | 3 | 653.165 | 653.16 | 0.015 | true |  |
| SUI | 25 | 1 | 5 | 1.2866 | 1.2866 | 7.7 | true |  |
| TON | 44 | 1 | 5 | 2.31545 | 2.3154 | 4.3 | true |  |
| DOGE | 173 | 0 | 6 | 0.10931 | 0.10931 | 91 | true |  |
| TRX | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| LAYER | 159 | 0 | 6 | 0.129545 | 0.12954 | 77 | true |  |
| CHIP | 207 | 0 | 6 | 0.060491 | 0.060491 | 165 | true |  |
| UNI | None | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ONDO | 87 | 0 | 6 | 0.451085 | 0.45108 | 22 | true |  |
| AAVE | 21 | 2 | 4 | 99.6115 | 99.611 | 0.1 | true |  |

## Gate Results

| Gate | Status |
| --- | --- |
| Approval | `True` |
| Endpoint testnet | `True` |
| Account/API-wallet readiness | `True` |
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
  "account_role": "user",
  "action_summary": {
    "grouping": "na",
    "orders": [
      {
        "a": 4,
        "b": true,
        "c": "0xc4b7fa627e05d6c49b2d6ffb1fd2dffb",
        "p": "2342.8",
        "r": false,
        "s": "0.0042",
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
  "endpoint_is_testnet": true,
  "environment": "testnet",
  "estimated_notional": "9.83976",
  "limit_price": "2342.8",
  "max_price_decimals": 2,
  "order_type": "post_only_limit",
  "price_precision_reason": "price_formatted_down_5_sig_figs_and_max_2_decimals",
  "quantity": "0.0042",
  "raw_signed_payload_included_in_report": false,
  "side": "buy",
  "signature_included_in_report": false,
  "signer_address_abbrev": "0x0f42...04d9",
  "size_precision_reason": "size_formatted_down_sz_decimals_4",
  "symbol": "ETH",
  "target_account_abbrev": "0x7580...8222",
  "tif": "Alo",
  "vaultAddress_abbrev_if_present": null,
  "vaultAddress_present": false
}
```

## Order Response Sanitized Summary

```json
{
  "response": {
    "data": {
      "statuses": [
        {
          "error": "Order must have minimum value of $10. asset=4"
        }
      ]
    },
    "type": "order"
  },
  "status": "ok"
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

Reconciliation:

```json
{
  "account_state_available": true,
  "open_orders": []
}
```

## Successful Follow-Up Sandbox Lifecycle

After the UAT3.3 minimum-order-value rejection, the founder/operator approved a capped 15 USDC follow-up Hyperliquid testnet attempt to verify the corrected route. The sanitized result is current truth for UAT3.4 operationalization:

- Account targeting: `verified`
- Target: `0x7580...8222`
- Account role: `user`
- Signer/API wallet: `0x0f42...04d9`
- `vaultAddress`: `omitted`
- Equity: `999.0`
- Equity source: `standard_perp_clearinghouse`
- Order: `ETH post-only limit buy`, price `2344.2`, size `0.0063`, estimated notional `14.76846`, TIF `Alo`, asset id `4`
- Order endpoint called: `yes_exactly_once`
- Exchange response: `order accepted open`, oid `52873216602`
- Cancel endpoint called: `yes_only_for_accepted_open_order`
- Cancel response: `success`
- Reconciliation: order status `canceled`, open orders `[]`
- Unexpected fill: `false`
- Open order remains: `false`
- Unknown state: `false`
- Live endpoint used: `false`
- Secrets printed: `false`

## Reason Codes

- `order_rejected`
- `Order must have minimum value of $10. asset=4`

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

`UAT3.4 additional sandbox lifecycle testing may be scoped`
