# UAT3.4 Sandbox Routing Pipeline And Order Ledger

Recorded at: `2026-05-11T05:47:36.982043Z`

## Scope

UAT3.4 operationalizes the successful sandbox route as a production-like, fixed-target sandbox pipeline plus a routed-order ledger.

UAT3.4 is sandbox/testnet only. It is not paper trading, not live trading, not strategy performance validation, not broad top-20 order testing, and not approval for future orders.

## UAT3.3 Success Recap

```json
{
  "account_role": "user",
  "account_targeting": "verified",
  "cancel_endpoint_called": "yes_only_for_accepted_open_order",
  "cancel_response": "success",
  "equity": "999.0",
  "equity_source": "standard_perp_clearinghouse",
  "exchange_response": "order accepted open oid=52873216602",
  "live_endpoint_used": false,
  "order": "ETH post-only limit buy price=2344.2 size=0.0063 notional=14.76846 tif=Alo asset_id=4",
  "order_endpoint_called": "yes_exactly_once",
  "reconciliation": "canceled_open_orders_empty",
  "secrets_printed": false,
  "signer_api_wallet": "0x0f42...04d9",
  "target": "0x7580...8222",
  "vaultAddress": "omitted"
}
```

## Current Account Mode

| Field | Value |
| --- | --- |
| Account role | `user` |
| vaultAddress present | `False` |
| Target | `0x7580...8222` |
| Signer/API wallet | `0x0f42...04d9` |

Normal master/user accounts omit `vaultAddress`. Subaccounts/vaults may use `vaultAddress` only when explicitly configured as that mode.

## Unified-Mode Compatibility

Status: `implemented`

```json
{
  "perp_account_value": "999.0",
  "perp_withdrawable": "999.0",
  "reason_codes": [
    "standard_perp_clearinghouse_equity_selected"
  ],
  "selected_equity_source": "standard_perp_clearinghouse",
  "selected_sandbox_equity": "999.0",
  "spot_usdc_hold": "0.0",
  "spot_usdc_total": "0.0"
}
```

Active UAT3.4 route uses `standard_perp_clearinghouse` when perp account equity is available. Unified mode remains supported through `spotClearinghouseState` USDC total minus hold when perp account value is zero. Supported equity-source labels include `standard_perp_clearinghouse`, `unified_margin_spot_clearinghouse`, `portfolio_margin_spot_clearinghouse`, and `unified_margin_spot_clearinghouse_fallback`.

## Fixed-Target Sandbox Route

```json
{
  "account_role": "user",
  "approval_required": true,
  "environment": "testnet",
  "idempotency_key_required": true,
  "live_endpoint_forbidden": true,
  "max_attempts": 3,
  "notional_cap": "20",
  "order_type": "post_only_limit",
  "product": "USDC perpetual",
  "route_id": "fixed_target_hyperliquid_testnet_eth",
  "route_type": "fixed_target_sandbox",
  "sandbox_labels_required": true,
  "submit_lease_required": true,
  "symbol": "ETH",
  "vault_address_present": false,
  "venue": "hyperliquid"
}
```

This is fixed-target routing only. It is not smart routing, SOR, best-binding selection, target reselection, route executor behavior, or top-20 fanout.

## Precision Validation

| Symbol | Asset id | szDecimals | Max price decimals | Formatted post-only buy price | Formatted size | Passed | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | 3 | 5 | 1 | 80993 | 0.00012 | true |  |
| ETH | 4 | 4 | 2 | 2350.2 | 0.0042 | true |  |
| SOL | 0 | 2 | 4 | 97.099 | 0.1 | true |  |
| XRP | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ZEC | 193 | 0 | 6 | 138.65 | 1 | true |  |
| BNB | 6 | 3 | 3 | 654.65 | 0.015 | true |  |
| SUI | 25 | 1 | 5 | 1.2899 | 7.7 | true |  |
| TON | 44 | 1 | 5 | 2.3212 | 4.3 | true |  |
| DOGE | 173 | 0 | 6 | 0.10947 | 91 | true |  |
| TRX | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| LAYER | 159 | 0 | 6 | 0.12684 | 78 | true |  |
| CHIP | 207 | 0 | 6 | 0.060684 | 164 | true |  |
| UNI | None | None | None | None | None | false | unsupported_by_hyperliquid_meta |
| ONDO | 87 | 0 | 6 | 0.44965 | 22 | true |  |
| AAVE | 21 | 2 | 4 | 100.02 | 0.09 | true |  |

## Routed Order Ledger

| Run id | Route id | Venue | Environment | Symbol | Price | Size | Notional | Lifecycle | OID | Cancel | Reconcile | Equity source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uat3_4_sandbox_routing_pipeline_order_ledger | fixed_target_hyperliquid_testnet_eth | hyperliquid | testnet | ETH | 2346 | 0.0085 | 19.9410 | canceled | 52874322602 | success | completed | standard_perp_clearinghouse |

## Lifecycle Results

| Field | Value |
| --- | --- |
| UAT3.4 lifecycle attempts | `1` |
| Order endpoint calls | `1` |
| Cancel endpoint calls | `1` |
| Open order remains | `False` |
| Unknown state | `False` |
| Unexpected fill | `False` |

## Boundary Confirmation

- Top-20 order submission: `false`
- Live endpoint used: `false`
- Paper trading: `not approved`
- Live trading: `not approved`
- Money Flow rules changed: `false`
- Secrets included in report: `false`
- Dashboard order button added: `false`

## UAT4.0 Dashboard Roadmap Status

`captured`

Future requested phase: `UAT4.0 - Live UAT Trading Dashboard / Chart Cockpit`.

Requested capabilities: live charts for watched pairs; green entry arrows; red exit arrows; routed orders tab; watched-pair market data; EMA5 / EMA10 / SMA20 / RSI / MACD overlays; regime/trend context if available; UAT order lifecycle overlay; sandbox/not-live labels; no paper/live confusion.

## Next Readiness Decision

UAT4.0 readiness decision: `UAT4.0 live UAT dashboard/chart cockpit may be scoped`

UAT3.5 readiness decision: `UAT3.5 is blocked`

## Reason Codes

- `order_accepted_open`
- `uat_universe_precision_validation_incomplete`
