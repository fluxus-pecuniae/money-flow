# Money Flow UAT Dashboard Design

Canonical design document for `apps/dashboard/`.

## Product Purpose

The dashboard is a read-only UAT cockpit for Money Flow strategy observation and sandbox/testnet lifecycle review. It helps the founder answer what market is being watched, what Money Flow observed, where shadow or sandbox lifecycle markers appeared, what happened to routed sandbox orders, and whether the system is sandbox, paper, or live.

The dashboard is not an order-entry terminal.

## Design Goals

- Make the chart the center of the product.
- Make watched markets scannable like an exchange market list.
- Tie shadow markers and routed sandbox lifecycle markers directly to the active market.
- Make routed orders readable as a blotter, not as detached report cards.
- Keep sandbox, paper, and live boundaries visible without overwhelming the screen with prose.
- Preserve PT0 safety: no active order controls, no private/signed/order endpoint calls, no API keys for charts, no live behavior, and no real-capital behavior.

## User Mental Model

The founder should read the screen in this order:

1. Top bar: current environment, active market, timeframe, and safety state.
2. Left rail: watched market list and signal/coverage status.
3. Center: chart, indicators, and green/red markers.
4. Right rail: order-book availability, market facts, Money Flow context, and sandbox risk state.
5. Bottom blotter: routed orders, shadow records, balances/positions, lifecycle, and sanitized audit logs.

## Exchange-Like Layout References

The layout follows the common workstation pattern visible in OKX, Hyperliquid, and CoinRoutes-style products:

- market list on the left
- central TradingView-style chart region
- right-side order book / market context / risk context
- bottom blotter for orders, positions, lifecycle, and logs

The implementation uses this interaction model and information architecture only. It does not copy brand, logos, trademarks, proprietary visuals, or exact UI text from those products.

## Information Architecture

Top bar:
- product name: `Money Flow`
- environment badge: `sandbox/testnet`
- paper/live status: paper approved for Hyperliquid testnet/sandbox only; live not approved
- active market selector
- active venue and timeframe
- market status: public read-only
- safety state: no live endpoint, sandbox only, order controls disabled

Left rail:
- watchlist / markets
- filter chips: all, would-open, no-trade, active sandbox route, missing data, favorites
- per-symbol observation-only and order-approval status

Center:
- chart cockpit
- timeframe context
- TradingView Lightweight Charts from the official local bundle
- indicator dock
- entry/exit marker dock

Right rail:
- order book placeholder / public read-only source state
- market info / precision state
- signal context
- risk context

Bottom:
- Routed Orders
- Shadow Signals
- Balances / Positions
- Lifecycle
- Audit / Logs

## Visual Hierarchy

- The chart is the largest and highest-priority region.
- The watchlist is compact and dense.
- The right rail is stacked and narrow.
- The bottom blotter is wide and tabbed.
- Safety is persistent but compact: one top warning strip and short status chips.
- Tables use dense rows, sticky headers, and monospace numbers.

## Tab Structure

Primary dashboard tabs remain:
- Evidence
- Experiments
- UAT Chart Cockpit
- UAT2 Shadow Run
- Strategy

The UAT Chart Cockpit has its own bottom blotter tabs:
- Routed Orders
- Shadow Signals
- Balances / Positions
- Lifecycle
- Audit / Logs

## Component List

- `uat-topbar`
- `uat-safety-banner`
- `uat-left-rail`
- `market-list-shell`
- `uat-center-cockpit`
- `exchange-chart-shell`
- `tradingview-lightweight-chart`
- `indicator-dock`
- `marker-dock`
- `uat-right-rail`
- `right-rail-card`
- `uat-bottom-blotter`
- `blotter-tabs`
- `lifecycle-timeline`

## Color System

The dashboard uses an exchange-like dark theme.

| Role | Token | Value |
| --- | --- | --- |
| App shell | `--color-shell` | `#05080d` |
| Panel | `--color-panel` | `#0b1118` |
| Raised panel | `--color-panel-2` | `#101924` |
| Header panel | `--color-panel-3` | `#152232` |
| Line | `--color-line` | `#263445` |
| Text | `--color-text` | `#edf4fb` |
| Muted text | `--color-muted` | `#8392a5` |
| Entry / positive | `--color-green` | `#17c784` |
| Exit / cancel / risk | `--color-red` | `#f6465d` |
| UAT warning | `--color-amber` | `#f3ba2f` |
| Sandbox status | `--color-blue` | `#19a7ce` |
| Sandbox accent | `--color-teal` | `#28d7c5` |

## Typography System

- Display: condensed trading-terminal style for product labels and panel titles.
- UI: compact sans for controls and labels.
- Mono: numbers, prices, ids, lifecycle status, and table rows.

The design avoids default-looking large report text and favors dense workstation scanning.

## Spacing / Grid System

- Outer shell: 12px to 16px gaps.
- Workstation grid: left rail / center chart / right rail.
- Bottom blotter: full-width tabbed grid.
- Mobile: rails stack vertically; the chart remains before the blotter.

## Market Data Display Rules

- Show latest price/mid only when present in local UAT/PT summaries, PT0/UAT4.2 local refresh JSON, or public read-only data.
- Show `market_data_unavailable` instead of fabricated values.
- Label sources as `local_summary_json`, `refreshed_public_read_only_local_json`, or `public_read_only`.
- Never require private endpoints or API keys for dashboard display.
- PT0 keeps the UAT4.2 local refresh summary path and public-read-only monitor helpers, adds `docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json`, and lets the browser poll Hyperliquid testnet public `allMids` and `candleSnapshot` every 15 seconds before falling back to committed/local JSON.

## Chart Rules

- The chart area must be central.
- PT0 uses TradingView Lightweight Charts for candlesticks, volume histogram, crosshair, price scale, time scale, resize handling, EMA overlays, and markers.
- PT0 prefers live Hyperliquid testnet public candles, falls back to refreshed public-read-only monitor candles, then falls back to committed PT0/UAT summaries.
- The dashboard uses a local official `lightweight-charts` standalone bundle, not TradingView Advanced Charts, not the Trading Platform library, and not the hosted TradingView widget.
- If candles are insufficient, display explicit unavailable states.

## Signal Marker Rules

Green markers mean:
- `shadow would-open`
- `paper observation would-open`
- `sandbox order accepted/open`
- `sandbox fill` if ever applicable

Red markers mean:
- `shadow would-close`
- `paper observation would-close`
- `sandbox cancel`
- `sandbox exit` if ever applicable

Marker tooltips/rows must include:
- symbol
- component or route
- timeframe
- timestamp
- source: shadow audit, paper observation scanner, or routed sandbox ledger
- reason codes
- order id when available
- sandbox/not-live labels
- no paper/live confirmation

Shadow and paper-observation markers are not actual trades. Sandbox lifecycle probes are not strategy performance trades.

## Routed Order Display Rules

Routed Orders must show:
- time / run id
- route id and route type
- symbol
- side
- price
- size
- notional
- lifecycle
- cancel status
- reconcile status
- order id / oid
- selected equity source
- sandbox/not-live labels
- sanitized exchange response

The UAT3.4 lifecycle should be visually clear:

`accepted/open -> canceled -> reconciled`

No retry, cancel, amend, route, or approval actions are allowed in the dashboard.

## Sandbox / Paper / Live Labeling Rules

- UAT cockpit: `sandbox/testnet observation only`.
- Paper trading: `approved for Hyperliquid testnet/sandbox only`.
- Broader top-20 paper/sandbox trading: `approved under PT0 metadata, precision, risk, lease, label, and no-live gates`.
- Live trading: `not approved`.
- Internal paper equity: `paper-equity simulation`, `not real capital`.
- Sandbox balance confirmation: `sandbox private read-only`, `not live account`.
- Top-20 assets: `paper/sandbox eligible only when Hyperliquid testnet metadata and precision pass`.
- ETH route: fixed-target sandbox route ledger visibility plus PT0 route-candidate foundation; runtime routing remains gated and default-disabled.
- Routed ledger records: sandbox/testnet lifecycle records, not paper, not live, not performance validation.

## Safety / No-Order-Control Rules

The dashboard must not include active controls for:
- order entry
- cancel / retry / amend
- approval execution
- paper/live switching
- auto trading
- routing or target reselection

If future control mocks are ever shown, they must be disabled, inert, and labeled `not implemented`, `not approved`, and `no action`. Preferred state remains no controls.

## Responsive Behavior

- Desktop: left market rail, center chart, right context rail, bottom blotter.
- Tablet: watchlist and chart remain first; right rail wraps below chart.
- Mobile: all regions stack; controls remain compact and read-only.

## Future Roadmap

Deferred UAT/PT work:
- PT0.1 supervised top-20 paper/sandbox runtime week
- operator-served live public refresh endpoint
- real order-book/public depth display
- richer crosshair / tooltip behavior
- routed-order timeline overlays on the chart

None of the above authorize live trading, live endpoints, real-capital trading, private order endpoints, signed order endpoints, API-key exposure, routing expansion, SOR/fanout/CBBO/target reselection, cross-venue routing, or Money Flow rule changes.
