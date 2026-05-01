# Exchange Adapters

Up: [[00 Maps/Component Map]]

## Paths

- `services/exchange/base.py`
- `services/exchange/registry.py`
- `services/exchange/hyperliquid/`
- `services/exchange/aster/`
- `services/exchange/okx/`
- `services/exchange/coinbase/`
- `services/exchange/binance/`
- `services/exchange/kraken/`

## Current Venue Set

- Hyperliquid: deepest lifecycle path and current perpetual submit scope.
- Aster: perpetual adapter with submit/reconcile/cancel and bounded same-target retry; native amend unsupported.
- OKX: spot/perp adapter with submit/reconcile/cancel/recovery/native amend/private polling.
- Coinbase Advanced Trade: spot adapter with JWT submit/reconcile/cancel/recovery/native edit-order amend/private polling.
- Binance: spot adapter with submit/reconcile/cancel and bounded same-target retry; native amend unsupported.
- Kraken: spot adapter with submit/reconcile/cancel/recovery/native amend/private polling.

## Boundary Truth

- Venue-private state is inspection truth, not submitted-order identity.
- Direct private open-order/recent-fill support is uneven by venue.
- Aster/Binance ambiguous fill evidence is scoped and not exposed as plain submitted-order fill truth.
- Broader user-stream parity remains deferred.

## Related Notes

- [[10 Components/Execution Service]]
- [[40 Operations/Known Issues Index]]
