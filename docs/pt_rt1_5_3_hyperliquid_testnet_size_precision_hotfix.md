# PT-RT1.5.3 Hyperliquid Testnet Size / Precision Hotfix

## Summary

`status`: implemented, verified

PT-RT1.5.3 fixes the Hyperliquid testnet fixed-25-USDC order-size path that PT-RT1.5.2 exposed with venue reject `Order has invalid size.` This is a testnet plumbing hotfix only.

Public Hyperliquid mainnet candles remain strategy truth. Synthetic paper ledgers remain PnL truth. Testnet fills do not update synthetic PnL. Candidate, MF-ORIG, wildcard, and `15m` lanes cannot send testnet orders. Live trading is not approved and no strategy is production-approved.

## Invalid-Size Reject Summary

`status`: verified

PT-RT1.5.2 reached Hyperliquid testnet with one labeled `testnet_transport_smoke_not_strategy_signal` order, but the fixed 25 USDC BTC order was rejected with `Order has invalid size.` The lifecycle reconciled to no open order and did not create a synthetic trade.

PT-RT1.5.3 resolves this by requiring testnet public metadata before testnet order shape construction and by recording size precision facts directly in lifecycle rows.

## Formatter Fix

`status`: implemented

Before any testnet order submit, the runtime now resolves Hyperliquid testnet public `meta` for the target asset and uses:

- `asset_id`
- `venue_symbol`
- `szDecimals`
- Hyperliquid price significant-figure / max-decimal formatting
- Hyperliquid size formatting by `szDecimals`

The runtime computes:

- `raw_quantity = 25 / limit_price`
- `formatted_quantity` rounded down to `szDecimals`
- `estimated_testnet_notional = formatted_quantity * formatted_limit_price`

If formatted quantity is zero, nonpositive, or too far from the fixed 25 USDC notional, the runtime blocks before `/exchange` with:

- `testnet_order_invalid_size_preflight`

If the venue still rejects with invalid size, the lifecycle records:

- `testnet_order_rejected_invalid_size`
- `venue_reject_order_has_invalid_size`

Repeated submits for the same lane/symbol/timeframe/candle/side key are blocked with `testnet_duplicate_order_blocked`.

## Fixed 25 USDC Policy

`status`: verified

The testnet plumbing order remains fixed at 25 USDC.

PT-RT1.5.3 does not use synthetic signal size, account equity sizing, or real balance sizing for the testnet order. Lifecycle rows record both:

- `synthetic_signal_notional`
- `testnet_fixed_notional = 25`
- `sizing_source = fixed_testnet_plumbing_notional`

## Smoke Result

`status`: verified

Bounded smoke command:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py --duration-minutes 1 --output-dir reports/paper_runtime/pt_rt1_5_3_transport_smoke --pt-rt1-5-week1-active --signal-evaluation-mode candle_close_only --fresh-signal-only-after-runtime-start --enable-baseline-testnet-transport --founder-approved-pt-rt1-5-3-testnet-size-hotfix-smoke --pt-rt1-5-testnet-order-notional-usdc 25 --max-testnet-orders-this-phase 1 --public-mainnet-only --max-cycles 1 --poll-seconds 1 --max-candle-symbols 2
```

Smoke outcome:

- `status`: `testnet_size_precision_hotfix_smoke_verified`
- `trigger_type`: `transport_smoke_not_strategy_signal`
- `symbol`: `BTC`
- `asset_id`: `3`
- `szDecimals`: `5`
- `raw_quantity`: `0.0003371657844161974442833541252`
- `formatted_quantity`: `0.00033`
- `formatted_limit_price`: `74147`
- `estimated_testnet_notional`: `24.46851`
- `order_endpoint_called`: `true`
- `signed_order_endpoint_called`: `true`
- `venue_response`: accepted/open
- `cancel_status`: `canceled`
- `reconcile_status`: `reconciled`
- `open_order_remains`: `false`
- `synthetic_trade_created`: `false`
- `strategy_pnl_update_from_testnet`: `false`

The smoke order was a plumbing connectivity/precision smoke, not a strategy signal and not strategy performance evidence.

## Dashboard Status

`status`: implemented

The Paper Trading `Testnet Order Lifecycle` table now shows:

- asset id
- `szDecimals`
- raw quantity
- formatted quantity
- limit price
- estimated notional
- endpoint-called flags
- signed endpoint-called flags
- reason codes
- strategy PnL update from testnet

## Boundaries

`status`: verified

- Production Money Flow rules are unchanged.
- Public mainnet candles remain strategy truth.
- Testnet prices are not strategy truth.
- Testnet fills do not update synthetic PnL.
- Candidate lanes remain synthetic-only.
- MF-ORIG lanes remain synthetic-only.
- Wildcard lanes remain synthetic-only.
- `15m` remains paused and cannot trigger testnet transport.
- No live trading is approved.
- No strategy is production-approved.
- Runtime artifacts under `reports/paper_runtime/` remain ignored and uncommitted.

## Next Recommended Action

`status`: needs_followup

Restart or continue the active Week 1 runtime only after this hotfix is present. Watch the next fresh Money Flow v1.2 baseline-triggered lifecycle row to confirm the same metadata-based size path is used outside the explicit transport-smoke path.
