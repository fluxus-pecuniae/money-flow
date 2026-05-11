# PT0.0.1 TradingView Chart Stability Hotfix

Paper trading remains approved only for Hyperliquid testnet/sandbox.

Live trading is not approved.

PT0.0.1 fixes a dashboard P0. It does not submit orders, add order controls, call private/signed/order endpoints, call live endpoints, use exchange API keys, change Money Flow rules, add SOR/fanout/CBBO/target reselection, or generate evidence packs.

## P0 Bug Summary

| Item | Status | Notes |
| --- | --- | --- |
| Founder-observed bug | `verified` | The page/chart scrolled or grew downward without user action, then snapped back around the 15-second public market refresh. |
| User impact | `verified` | The UAT/PT dashboard was not usable for monitoring because the central chart region created visible layout instability. |
| Scope | `implemented` | Frontend chart lifecycle, sizing, and polling guardrails only. |

## Root Cause Found

| Cause | Status | Notes |
| --- | --- | --- |
| Chart recreated on refresh-time renders | `verified` | `renderTradingViewLightweightChart` destroyed/recreated the Lightweight Charts instance whenever the cockpit re-rendered, including live refreshes. |
| Unstable autosize behavior | `verified` | The chart was created with `autoSize: true`, while a `ResizeObserver` called `chart.applyOptions({ autoSize: true })`, creating a resize/reflow feedback-loop risk. |
| View reset on refresh-time rebuild | `verified` | `chart.timeScale().fitContent()` ran after every chart rebuild, causing the visible time-scale to jump on refresh. |
| Container sizing | `verified` | The chart container used a minimum height without a stable explicit height or parent containment, so chart children could influence layout height. |

## Files Changed

- `apps/dashboard/evidence-dashboard.css`
- `apps/dashboard/evidence-dashboard.js`
- `apps/dashboard/README.md`
- `apps/dashboard/DESIGN.md`
- `docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md`
- `docs/pt0_0_1_tradingview_chart_stability_hotfix.md`
- `tests/test_pt001_tradingview_chart_stability.py`
- repo operational docs and relevant Obsidian notes

## Chart Sizing Fix

| Area | Status | Notes |
| --- | --- | --- |
| Explicit chart height | `implemented` | The chart now has a stable bounded container height: `.tradingview-lightweight-chart` uses `height: clamp(420px, 56vh, 680px)`, `max-height: 680px`, `min-height: 0`, `overflow: hidden`, and `contain: layout paint size`. |
| Parent containment | `implemented` | `.exchange-workstation`, `.uat-center-cockpit`, and `.exchange-chart-shell` now enforce stable `min-height: 0` / `overflow: hidden` behavior around the chart. |
| Usability cleanup | `implemented` | The main chart area remains centered and bounded; technical refresh churn is kept out of the page layout. |

## Chart Lifecycle Fix

| Area | Status | Notes |
| --- | --- | --- |
| Reuse chart instance | `implemented` | The dashboard now creates the chart once per selected symbol/timeframe and stores series handles. |
| Refresh path | `implemented` | Live refresh updates existing candlestick, volume, EMA5, EMA10, SMA20, and marker handles with `setData()` / `setMarkers()` where possible. |
| Destroy/recreate boundary | `implemented` | Chart destruction is reserved for selected symbol/timeframe changes or invalid chart state. |
| Autosize loop removal | `implemented` | `autoSize: true` was removed. The chart now uses explicit `chart.resize(width, height)` from measured container dimensions. |
| `fitContent()` behavior | `implemented` | `fitContent()` is called only when the chart is initially created for a new symbol/timeframe, not on every 15-second refresh. |

## Polling / Timer Fix

| Area | Status | Notes |
| --- | --- | --- |
| Single live polling timer | `verified` | `startLiveMarketPolling()` keeps the existing guard: if `state.liveMarketData.timer` exists, it returns without creating another interval. |
| Disabled polling flag | `implemented` | `?disableLivePolling=true` or `?livePolling=false` disables browser-side Hyperliquid public polling and uses local PT0/UAT4.2 JSON fallback only. |
| Public-read-only boundary | `verified` | Dashboard polling remains allowlisted to Hyperliquid testnet public info payloads only and still rejects private/order-like payload keys. |

## Manual Verification Result

| Check | Status | Notes |
| --- | --- | --- |
| Local server 45-second smoke | `verified_terminal_smoke` | `http://127.0.0.1:8765/apps/dashboard/index.html` returned HTTP 200 before and after a 45-second wait on the existing local `SimpleHTTPServer` process. Static checks verify the risky patterns are removed. A human browser check remains the authoritative visual confirmation for scrollY/height behavior because this terminal session has no browser automation framework available. |
| Expected browser result | `implemented` | One chart instance should remain visible, page height should remain bounded, and 15-second public refreshes should update series without page scroll or layout jump. |

## No-Order / No-Live Confirmation

| Boundary | Status |
| --- | --- |
| Orders submitted by PT0.0.1 | `verified: false` |
| Dashboard order controls added | `verified: false` |
| Private/signed/order endpoints used | `verified: false` |
| Live endpoint used | `verified: false` |
| Exchange API keys used | `verified: false` |
| Money Flow rules changed | `verified: false` |

## Remaining Dashboard Limitations

- `deferred`: Browser-integrated regression for document height and scrollY after multiple timed refreshes should be added if Playwright or another browser harness is introduced.
- `deferred`: PT0.1 supervised runtime remains future work; this hotfix only stabilizes the chart shell.

## Next Recommended Phase

`PT0.1 — Supervised Top-20 Paper/Sandbox Runtime Week` may be scoped after founder/operator confirms the chart no longer grows or auto-scrolls during real browser monitoring.
