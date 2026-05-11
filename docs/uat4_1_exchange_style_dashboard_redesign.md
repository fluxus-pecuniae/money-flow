# UAT4.1 Exchange-Style Dashboard Redesign

Recorded at: `2026-05-11T07:03:40Z`

## Scope

UAT4.1 rebuilds the static dashboard layout and design system around an exchange-style UAT workstation.

UAT4.1 is dashboard redesign only. It does not submit orders, does not create order controls, does not call private/signed/order endpoints, does not use exchange API keys, does not enable paper trading, does not enable live trading, does not change Money Flow rules, does not add smart routing/SOR/fanout/CBBO/best-binding selection/target reselection/route-executor behavior, does not generate evidence packs, and does not create live artifacts.

Top-20 assets remain observation-only. Routed orders shown are sandbox/testnet lifecycle records.

Paper trading is not approved. Live trading is not approved.

## What Was Wrong With UAT4.0

Status: `verified`.

UAT4.0 made the right data visible, but the UI still behaved like a stack of report cards:

- Too many disconnected panels.
- Chart was not visually central.
- Watchlist did not feel like a market list.
- Routed orders were not visually tied to the active market.
- Signal context required too much scanning.
- Sandbox/paper/live boundaries were text-heavy rather than integrated into the workstation status.

## New Design Principles

Status: `implemented`.

- Use a proven trading-workstation interaction model: market list, chart, right context rail, bottom blotter.
- Keep the active market and environment visible at all times.
- Make the chart the primary region.
- Put order lifecycle data in a blotter, not scattered cards.
- Use green/red marker semantics without implying shadow trades are actual trades.
- Make sandbox/testnet, paper, and live labels compact but persistent.
- Keep the dashboard read-only with no order controls.

## DESIGN.md Replacement Status

Status: `implemented`.

Canonical design doc:

```text
apps/dashboard/DESIGN.md
```

The previous root `DESIGN.md` has been replaced with a pointer to the canonical dashboard design doc.

The new design doc defines:

- product purpose
- dashboard goals
- user mental model
- exchange-like references
- information architecture
- visual hierarchy
- tab structure
- component list
- color system
- typography system
- spacing/grid system
- market-data display rules
- chart rules
- marker rules
- routed-order display rules
- sandbox/paper/live labels
- safety/no-order-control rules
- responsive behavior
- roadmap

## New Layout

Status: `implemented`.

The UAT Chart Cockpit now uses this structure:

| Region | Implementation |
| --- | --- |
| Top bar | `Money Flow`, sandbox/testnet environment, active market, timeframe, route/status chips |
| Safety banner | Persistent UAT/no-paper/no-live/no-order-control banner |
| Left rail | Exchange-like watchlist / markets list with filters |
| Center | Central chart cockpit, indicators, marker dock |
| Right rail | Order Book, Market Info, Signal Context, Risk Context |
| Bottom blotter | Routed Orders, Shadow Signals, Balances / Positions, Lifecycle, Audit / Logs |

The layout is inspired by OKX / Hyperliquid / CoinRoutes workstation patterns without copying brand, logos, trademarks, proprietary visuals, or exact UI text.

## Dashboard Sections Changed

Status: `implemented`.

Changed files:

- `apps/dashboard/index.html`
- `apps/dashboard/evidence-dashboard.css`
- `apps/dashboard/evidence-dashboard.js`

The UAT cockpit no longer uses stacked metric/report-card hierarchy. It now renders:

- compact top bar
- exchange-style watchlist
- central chart shell
- right rail context panels
- tabbed bottom blotter
- routed sandbox lifecycle timeline
- sanitized audit/log table

## Watchlist Status

Status: `implemented`.

Default watched assets:

```text
BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, AAVE
```

Each market row shows:

- symbol
- Hyperliquid perpetual product
- latest local-summary price if available
- 24h change unavailable when not present
- signal status
- market-data status
- observation-only label
- order-approval label

Filters:

- all
- would-open
- no-trade
- active sandbox route
- missing data
- favorites

All top-20 watchlist assets remain observation-only. ETH shows routed sandbox ledger visibility only; manual approval is required for every sandbox order.

## Chart Cockpit Status

Status: `implemented`.

The chart is now the center of the UAT cockpit. UAT4.1 still uses deterministic static chart values from committed local JSON:

```text
docs/uat2_shadow_strategy_top20_observation_summary.json
docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json
```

Live public refresh is deferred:

```text
live_public_refresh_deferred_to_uat4_2
```

No private/signed/order endpoints or API keys are required.

## Indicator Status

Status: `implemented`.

Displayed indicator labels:

- EMA5
- EMA10
- SMA20
- RSI
- MACD
- MACD signal
- MACD histogram

Unavailable context remains explicit:

```text
indicator_unavailable_insufficient_history
```

No fake indicator values are displayed.

## Marker Status

Status: `implemented`.

Green markers:

- `shadow would-open`
- `sandbox order accepted/open`

Red markers:

- `shadow would-close` when present
- `sandbox cancel`

Marker rows include source, reason codes, order id when available, sandbox/not-live labels, and no-paper/no-live confirmation.

Shadow markers are not actual trades. Sandbox lifecycle probes are not strategy performance trades.

## Right Rail Status

Status: `implemented`.

Right rail sections:

- Order Book: public-read-only status and explicit unavailable state when local JSON has no book depth.
- Market Info: latest local price, unavailable 24h/OI/funding fields, asset id, tick/lot precision status.
- Signal Context: Money Flow status, component, RSI/MACD/trend/entry-quality context.
- Risk Context: sandbox drawdown, equity source, not-live-account label, risk status, order controls disabled.

## Routed Orders Tab Status

Status: `implemented`.

The bottom `Routed Orders` tab shows UAT3.4 ledger fields:

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

The successful UAT3.4 lifecycle is readable as:

```text
accepted/open -> canceled -> reconciled
```

No order, cancel, retry, amend, approval, paper/live, or route action controls were added.

## No-Order-Control Confirmation

Status: `verified`.

The dashboard contains no active controls for:

- order entry
- cancel
- retry
- amend
- executable approval
- market buy/sell
- paper/live switching
- auto trading
- routing or target reselection

UAT4.1 calls no private/signed/order endpoints and uses no exchange API keys.

## Remaining UI Limitations

Status: `deferred`.

- Real public order-book depth is not loaded yet.
- Live public candle refresh is deferred.
- The chart shell is deterministic/static and should later be replaced by a real public-read-only chart library.
- Crosshair/tooltip behavior is represented by marker rows, not an interactive chart tooltip.
- 24h change, open interest, funding, and richer market microstructure fields are unavailable from current local summaries.

## Next Dashboard Work

Status: `deferred`.

Recommended next phase:

```text
UAT4.2 - public-read-only live market refresh / chart-library integration
```

UAT4.2 should remain no-key, public-read-only, no private/signed/order endpoints, no order controls, no paper/live trading, no Money Flow rule changes, and no routing expansion unless separately scoped.
