# Money Flow Evidence Dashboard

Static local dashboard for founder/operator review of Strategy Validation evidence packs.

Run it from the repo root so the dashboard can read ignored local evidence-pack JSON files:

```bash
.venv/bin/python -m http.server 8765
```

Then open:

```text
http://127.0.0.1:8765/apps/dashboard/index.html
```

The dashboard tries to load the regenerated SV2.0.2 Hyperliquid canonical DB-imported evidence packs and matching Historical Replay chart/trade JSON from `reports/strategy_validation*`. Those generated files stay ignored by Git and review bundles. If the files are not present, use the file picker in the dashboard to load `money_flow_evidence_review.json`, one or more `batch_report.json` files, or dashboard chart-data JSON files manually.

The visible top-level navigation is `Strategy`, `Historical Replay`, and `Evidence`. `Historical Replay` is the default view. The invalid legacy `Experiments` surface is not exposed as a tab. The former `UAT Chart Cockpit` and `UAT2 Shadow Run` surfaces remain as hidden legacy panels for regression coverage and historical context, but they are no longer exposed as primary tabs.

The `Historical Replay` tab loads SV2.0.2 dashboard chart data from `reports/strategy_validation/sv2_0_2_dashboard_chart_data/20260512T064916Z/` when available, then falls back to `docs/pt0_0_3_historical_strategy_replay_summary.json` and `docs/pt0_0_2_historical_strategy_replay_summary.json`. The SV2.0.2 chart-data set covers BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX across 15m/1h/4h/1d and pairs the historical candles with the regenerated canonical pack trades. Historical public candle replay data remains Money Flow strategy truth for rendered replay charts; Hyperliquid testnet prices are not strategy truth. The tab renders historical candlesticks through TradingView Lightweight Charts, overlays EMA5/EMA10/SMA20 on the price pane, shows RSI 14 and MACD in separate TradingView panes inside the same chart/crosshair timeline as the candles, places green entry-fill and red exit-fill markers, shows a trade inspector with RSI/MACD/cost/PnL/equity details, displays a dynamic 10,000 USDC paper-equity panel, compares replay scenarios, shows a Jan 2025 data-horizon panel, and keeps the UAT3.4 sandbox execution ledger in a separate section. Evidence and Historical Replay both expose date filters. When a start/end date is selected, the dashboard treats the range as a fresh 10,000 USDC scenario by including trades entered on/after the start date and exited on/before the end date, then compounding the loaded trade returns from 10,000 USDC. Historical Replay also filters visible candles/indicators to the selected dates. This is a browser display recalculation from loaded trades, not canonical evidence-pack regeneration. Chart arrows and trade table rows select the linked trade in the inspector; arrow reason descriptions are disabled by default so the chart opens with compact PnL labels only. The replay-strategy dropdown defaults to `SV2.0.2 canonical Money Flow v1.2`; older PT replay strategies remain fallback-only and research-only. PT0.0.3's `1D` replay was aggregated from `4h` candles, but SV2.0 now makes `sleeve_1d` a real Money Flow v1.2 sleeve and shows direct Hyperliquid public-mainnet 1d readiness/evidence rows for the expanded BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB universe. SV2.0.1 keeps internal timeframe value `1d` with dashboard label `1D`, shows staged-vs-DB-import truth, and does not present compact rows as canonical evidence. SV2.0.2 adds canonical DB-import and evidence-pack status visibility: the dashboard now defaults to the regenerated `20260512T064916Z` 36-pack per-symbol/per-timeframe canonical set for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX while SHIB/kSHIB is deferred. It calls no private/signed/order endpoints, uses no API keys, submits no orders, and does not optimize parameters.

The hidden legacy `UAT Chart Cockpit` panel loads `docs/uat2_shadow_strategy_top20_observation_summary.json`, `docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json`, `docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json`, and `docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json` by default when served from the repo root. UAT4.1 redesigned it as an exchange-style workstation: compact top bar, left market/watchlist rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs for Routed Orders / Paper Trades, Shadow Signals, Balances / Positions, Lifecycle, and Audit / Logs. PT0 uses the official local TradingView Lightweight Charts standalone bundle from `apps/dashboard/vendor/lightweight-charts.standalone.production.js` for candlesticks, volume, EMA overlays, crosshair, time/price scales, resize handling, and green/red markers. PT0.0.1 stabilizes that chart: the chart mount has an explicit bounded height, parent containers prevent layout growth loops, live refreshes update existing chart/series handles instead of destroying/recreating the chart, `fitContent()` is not called on every refresh, and the browser keeps a single live polling timer. The browser polls Hyperliquid testnet public `allMids` and `candleSnapshot` every 15 seconds and computes live indicator labels from public candles when available. The chart does not render non-selected symbols from synthetic local fallback candles while live polling is enabled; it waits for that symbol's public `candleSnapshot` result and keeps local summaries in the side panels. It does not use API keys or call private/signed/order endpoints.

For emergency chart debugging, append either query flag:

```text
?disableLivePolling=true
?livePolling=false
```

When live polling is disabled, the cockpit uses committed PT0/UAT4.2 local summary JSON and does not call Hyperliquid public endpoints.

PAPER TRADING IS APPROVED for Hyperliquid testnet/sandbox only. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED under PT0 metadata, precision, risk, lease, label, and no-live gates. Live trading, real-capital trading, live exchange API keys, SOR/fanout/CBBO/target reselection, cross-venue routing, production auto-submit, and dashboard order controls remain not approved.

The canonical dashboard design document is `apps/dashboard/DESIGN.md`. The root `DESIGN.md` is only a pointer.

The hidden legacy `UAT2 Shadow Run` panel loads `docs/uat2_shadow_strategy_top20_observation_summary.json` by default when served from the repo root. It shows UAT2 summary cards, a filterable 45-record signal matrix, would-open records, no-trade reason breakdowns, the ETH `sleeve_1h` evidence-candidate card, `next_candle_open` / `next_candle_close` timing status, the `same_candle_close_research_only` research-only boundary, shadow drawdown labeled not-live-account, no-artifact boundary flags, the blocked UAT3 readiness checklist, and the UAT3.0/UAT3.0.1/UAT3.0.2/UAT3.0.3 sandbox-design/readiness panel. It also loads `docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json` when present and displays UAT3.4 routed sandbox order ledger records with route, lifecycle, cancel, reconcile, equity-source, and sandbox/not-live labels. It is a visualization and founder-review surface only; it adds no approval action and cannot enable orders.

The UAT3.0/UAT3.0.1/UAT3.0.2/UAT3.0.3 panel is informational. It shows that the future initial sandbox subset is Hyperliquid ETH USDC perpetual `sleeve_1h`, actual sandbox order submission is not approved, founder/operator approval is required for any later UAT3.1 submission, sandbox runtime policy and fixture validators exist, unified dry-run preflight exists, runtime full-blocker propagation and numeric edge-case validation are implemented, artifact label boundary helpers cover persistence/API/dashboard/report surfaces, dry-run executable gate wiring exists for approval/risk/submit-lease checks, sandbox account drawdown is fixture-only / missing live sandbox feed, and real submit/risk/approval wiring is still required. The UAT3.4 routed-orders view is ledger visibility only; it has no active order submission button, repeated-order control, live control, or approval action.

The `Strategy` tab visualizes the current Money Flow v1.2 rule flow from `services/strategy/money_flow.py`, including readiness gates, entry checks, position-management checks, sleeve thresholds, confidence scoring, RSI lower-floor truth, and the SV1.14 market-structure diagnostics boundary. SV2.0 adds `sleeve_1d` as an initial non-optimized baseline while preserving existing 15m/1h/4h settings. It is a visual overview only and does not change strategy logic in the browser. Component cards show sums across research runs, and run rows are scenario results rather than one combined account.

This is a visualization and PT0 paper/sandbox monitoring surface only. The Historical Replay tab visualizes generated local replay/chart JSON and does not regenerate Strategy Validation in the browser. The dashboard does not generate evidence packs, import candles, call live/private/signed/order endpoints, create approvals, submit orders, add order controls, approve live trading, or change Money Flow rules.

## TradingView Lightweight Charts Bundle

PT0 vendors the official `lightweight-charts` standalone production build (`5.2.0`) locally:

```text
apps/dashboard/vendor/lightweight-charts.standalone.production.js
apps/dashboard/vendor/LICENSE
apps/dashboard/vendor/package.json
```

The dashboard uses TradingView Lightweight Charts, not TradingView Advanced Charts, not the Trading Platform library, and not the hosted TradingView widget. Chart attribution is displayed below the chart.

PT0.0.1 chart-stability rules:

- The chart container uses a fixed bounded responsive height rather than min-height-only sizing.
- Live 15-second refreshes update existing candlestick, volume, EMA, and marker handles where possible.
- The chart is destroyed/recreated only for symbol/timeframe changes or invalid chart state.
- `autoSize: true` is intentionally not used in the chart options.
- `ResizeObserver` schedules explicit `chart.resize(width, height)` calls and does not call `chart.applyOptions({ autoSize: true })`.
- `fitContent()` runs only on first creation for a selected symbol/timeframe.
- The chart renders live `candleSnapshot` candles for the selected symbol/timeframe only; non-selected symbols are never displayed from all-green local fallback candles as if they were live.
- A visible `Price USDC` readout sits beside the TradingView canvas so the latest, high, low, open, and close remain readable even when the native price scale is visually compressed.
