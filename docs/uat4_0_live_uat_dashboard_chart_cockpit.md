# UAT4.0 Live UAT Dashboard / Chart Cockpit

Recorded at: `2026-05-11T06:24:00Z`

## Scope

UAT4.0 adds a read-only dashboard/chart cockpit for UAT market observation and sandbox lifecycle visibility.

UAT4.0 is dashboard/chart cockpit only.

UAT4.0 is dashboard and visualization only. It does not submit orders, does not add an order button, does not call private or signed endpoints, does not use exchange API keys, does not enable paper trading, does not enable live trading, does not change Money Flow rules, does not add smart routing, SOR, fanout, CBBO, best-binding selection, target reselection, or route executor behavior, does not generate evidence packs, and does not create live artifacts.

No private/signed/order endpoints are called by the UAT4.0 dashboard.

Paper trading is not approved. Live trading is not approved. Top-20 assets remain observation-only. Routed orders shown are sandbox/testnet lifecycle records.

## Dashboard Sections Added

Status: `implemented`.

The static dashboard now has a dedicated tab:

```text
UAT Chart Cockpit
```

The cockpit loads existing committed summary artifacts:

```text
docs/uat2_shadow_strategy_top20_observation_summary.json
docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json
```

Sections added:

- `UAT Chart Cockpit` safety banner and filters.
- UAT watchlist table.
- Market data coverage table.
- Static chart display from UAT2 local summary values.
- Indicator overlay panel.
- Entry / exit marker table.
- Active ETH sandbox route status card.
- Unified-mode equity-source visibility card.
- Routed Orders tab/table.
- Shadow Signals side panel.

No backend proxy or live public fetch was added in UAT4.0.

## Watchlist Status

Status: `implemented`.

Default watchlist:

```text
BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, AAVE
```

Each row shows:

- symbol
- venue: Hyperliquid
- product: USDC perpetual
- quote / settlement: USDC / USDC
- market data status from UAT2 local summary
- chart availability
- UAT3.4 precision status when available
- UAT observation-only status
- order-enabled status
- paper/live approval status

Only ETH has a routed sandbox ledger record, and the dashboard labels it as ledger visibility only with no dashboard control. Top-20 inclusion is not order approval.

## Market Data Coverage Status

Status: `implemented`.

The cockpit shows market data coverage from local summary JSON only:

- latest close or UAT3.4 sample mid where available
- candle availability
- selected timeframe
- last candle close time
- source artifact
- endpoint category: `public_read_only / local_summary_json`
- failure reason such as `market_data_unavailable`

Live public read-only refresh is `deferred` to a later UAT4.1-style phase. UAT4.0 does not call Hyperliquid public endpoints at dashboard runtime.

## Chart / Indicator Status

Status: `implemented`.

The chart display is a deterministic static snapshot from UAT2 summary values for the selected pair/timeframe. It is not a live feed.

Indicator labels shown:

- EMA5
- EMA10
- SMA20
- RSI
- MACD
- MACD signal
- MACD histogram

Regime, trend, and volatility labels are shown as:

```text
indicator_unavailable_insufficient_history
```

No fake indicator values are displayed.

## Entry / Exit Marker Status

Status: `implemented`.

Green markers:

- `green marker: shadow would-open`
- `green marker: sandbox order accepted/open`

Red markers:

- `red marker: sandbox cancel`

Marker rows include symbol, component/route, timestamp, marker type, source, reason codes, order id when available, sandbox/not-live labels, and no paper/live confirmation.

Shadow would-open markers are explicitly labeled as shadow signals and not actual trades. Sandbox markers are explicitly labeled `sandbox/testnet lifecycle probe`, not live, not paper, and not performance validation.

## Routed Orders Tab Status

Status: `implemented`.

The cockpit includes a `Routed Orders Tab` backed by the UAT3.4 routed-order ledger summary.

Fields shown:

- run id
- route id
- route type
- venue
- environment
- symbol
- side
- order type
- limit price
- size
- estimated notional
- TIF
- asset id
- order id / oid
- lifecycle status
- cancel status
- reconciliation status
- open order remains
- position changed
- selected equity source
- sandbox labels
- no-live/no-paper confirmation
- sanitized exchange response

Filters:

- symbol
- lifecycle status
- environment
- sandbox/not-live label status

No order submission, cancel, retry, amend, approval, route, auto-trade, paper/live, or live controls were added.

## Sandbox Route Status

Status: `implemented`.

The route card shows:

| Field | Value |
| --- | --- |
| Route id | `fixed_target_hyperliquid_testnet_eth` |
| Venue | `Hyperliquid` |
| Environment | `testnet/sandbox` |
| Symbol | `ETH` |
| Account role | `user` |
| vaultAddress | `omitted` |
| Selected equity source | `standard_perp_clearinghouse` |
| Unified compatibility | `supported` |
| Order scope | `sandbox only` |
| Paper/live | `not approved` |
| Broad top-20 orders | `not approved` |

## Unified Mode Visibility

Status: `implemented`.

The equity-source card shows:

- `selected_equity_source`
- standard perp clearinghouse status
- perp account value
- perp withdrawable
- unified-margin spot-clearinghouse fallback status
- spot USDC total
- spot USDC hold
- selected sandbox equity

This is visibility only. The dashboard does not change routing based on UI state.

## No-Order-Controls Confirmation

Status: `verified`.

The dashboard does not include:

- submit order control
- cancel order control
- retry control
- amend control
- approval action control
- route order control
- auto-trade toggle
- paper/live toggle

The persistent banner says:

```text
UAT sandbox/testnet observation only.
Paper trading is not approved.
Live trading is not approved.
Order submission controls are disabled.
Top-20 assets are observation-only.
```

## Limitations

Status: `deferred`.

- UAT4.0 uses committed local JSON summaries and does not perform live public refresh.
- The chart display is a snapshot, not a streaming chart.
- Regime/trend/volatility labels are unavailable in the current UAT2 summary and are shown as `indicator_unavailable_insufficient_history`.
- Shadow signal markers are mapped from UAT2 summary candle timestamps and should not be interpreted as executed trades.
- UAT3.4 has one routed ETH sandbox lifecycle record only.
- Full live chart cockpit behavior with public read-only refresh, candlestick charts, and richer overlays remains future work.

## Next Dashboard Improvements

Status: `deferred`.

Potential UAT4.1 scope:

- public-read-only live refresh for watched pairs
- richer candlestick chart rendering
- public candleSnapshot refresh without API keys
- indicator recalculation from refreshed public candles
- market-data freshness timers
- no-private/no-signed/no-order endpoint telemetry at dashboard runtime

UAT4.1 must still avoid order controls, API keys, private/signed endpoints, paper trading, live trading, and Money Flow rule changes unless separately scoped.

## Boundary Rules

- Do not change Money Flow rules.
- Do not optimize parameters.
- Do not approve paper trading.
- Do not add paper trading.
- Do not add live execution.
- Do not submit live orders.
- Do not use live exchange API keys.
- Do not expose sandbox/testnet API keys.
- Do not add smart routing, SOR, fanout, CBBO, best-binding selection, target reselection, or route executor behavior.
- Do not submit orders for the top-20 universe.
- Do not add production auto-submit.
- Do not generate evidence packs.
- Do not create live artifacts.
- Do not expose secrets.
- Do not add a general dashboard order button.
- Preserve all UAT0-UAT3.4 safety policies.
