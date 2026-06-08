# Money Flow Founder Dashboard Design

Canonical design document for `apps/dashboard/`.

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime config: `PT-RT1.6` founder-selected Week 2 slate is prepared; no active paper run is assumed unless the local control server reports one.
- DASH-PT1.3 layout: Paper Trading is a dense exchange-style terminal with top health strip, contained left Cockpit / Global Filters plus internally scrolling three-column Watchlist rail, center Live Public Candles + Paper Markers chart, height-bounded right Runtime Control / Testnet Order Transport rail, bottom tabbed blotter, and a final full-width Daily Review / Anomaly Flags card below the blotter.
- LOG-OBS1 observability: Runtime Control includes a compact Runtime Logs panel and the terminal helper `scripts/watch_pt_rt1_runtime.py` exposes status/latest/tail views without changing runtime state.
- OBS-OS1 daily review: Paper Trading includes a lower-priority `Daily Review / Anomaly Flags` panel that reads the latest generated daily review pack from ignored `reports/paper_reviews/pt_rt1_6_week2_active/`.
- Active Week 2 default slate: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- Active timeframes: `1h`, `4h`, `1d`.
- Paused timeframes: `15m` remains paused as diagnostic/legacy context only.
- Strategy truth: public Hyperliquid mainnet fully closed candles and derived indicators.
- Synthetic PnL truth: independent synthetic 10,000 USDC paper ledgers per lane.
- Testnet plumbing: fixed 25 USDC Hyperliquid testnet transport is baseline-only and fresh-post-start only when gates pass; selected candidate/MF-ORIG lanes remain synthetic-only and lifecycle rows never update synthetic PnL.
- Production approval: no strategy is production-approved.
- Live trading: not approved; no real-capital trading is approved.
- Next recommended action: after founder review, start the `pt_rt1_6_week2_active` run from the dashboard control server or documented command.

## Product Purpose

The dashboard is a founder workstation for Money Flow evidence review and PT-RT Paper Trading observation. It helps the founder see current synthetic paper signals, historical evidence, variant research, audit findings, strategy logic, and sandbox/testnet plumbing context without mixing those surfaces into production approval.

The dashboard is not an order-entry terminal.

## Design Goals

- Make the chart the center of the product.
- Make watched markets scannable like an exchange market list.
- Tie shadow markers and routed sandbox lifecycle markers directly to the active market.
- Make routed orders readable as a blotter, not as detached report cards.
- Keep sandbox, paper, and live boundaries visible without overwhelming the screen with prose.
- Preserve PT0 safety: no active order controls, no private/signed/order endpoint calls, no API keys for charts, no live behavior, and no real-capital behavior.

## User Mental Model

The founder should read the Paper Trading screen in this order:

1. Top health strip: active scope, runtime state, Week 2 lanes, timeframes, 15m paused, synthetic/testnet/no-live boundaries.
2. Left rail: Cockpit / Global Filters plus compact internally scrolling Watchlist.
3. Center stage: Live Public Candles + Paper Markers, the largest panel.
4. Right rail: height-bounded Runtime Control and Testnet Order Transport.
5. Bottom blotter: tabbed Open Positions, Closed Trades, Signal Stream, Testnet Lifecycle, Runtime Logs, Weekly Scoreboard, and Diagnostics.
6. Final review card: Daily Review / Anomaly Flags below the blotter.

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
- visible tabs: `Paper Trading`, `Historical Replay`, `Evidence`, `The Lab`, `Strategy`
- `Audit` is not a visible top-level tab after DASH-PT1.1; audit artifacts remain historical reference material.
- safety state: synthetic paper only, public mainnet candles, baseline-only testnet plumbing, candidate lanes synthetic-only, no live trading.

Paper Trading cockpit:
- configured active lanes: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, `mf_orig_1d_stage2_breakout_resistance_full_equity`
- configured archived/default-inactive lanes: seven prior PT-RT lanes
- configured symbols: AVAX, BNB, BTC, DOGE, ETH, HYPE, SOL, SUI, XRP
- active timeframes: `1h`, `4h`, `1d`
- Runtime Logs panel: show `runtime_audit.jsonl`, `decisions.jsonl`, `trades.jsonl`, `testnet_order_lifecycle.jsonl`, `data_health.json`, `summary.json`, and the control-server log when available, with file size, modified time, and copyable `tail -n 50 -F` commands.
- Daily Review / Anomaly Flags panel: show generated timestamp, go/no-go label, decision/trade/lifecycle counts, synthetic/testnet boundary status, and top anomaly flags from `latest_review.json`; show an explicit generate-command empty state when absent; place as the final full-width Paper Trading card below the blotter.
- Runtime details panel: keep compact high-signal runtime fields only so it does not consume the full right column.
- disabled timeframe: `15m`, paused/legacy only

Center:
- chart cockpit
- timeframe context
- TradingView Lightweight Charts from the official local bundle
- indicator dock
- entry/exit marker dock

Side and lower panels:
- compact watchlist / markets
- testnet order lifecycle, explicitly separate from synthetic PnL
- runtime control and stale/no-run state
- lower-priority connection, scoreboard, timeframe, and risk diagnostics

Bottom:
- Routed Orders
- Shadow Signals
- Balances / Positions
- Lifecycle
- Audit / Logs

## Visual Hierarchy

- The chart is the largest and highest-priority region.
- The watchlist is compact and dense.
- The right rail is stacked, narrow, and limited to Runtime Control plus Testnet Order Transport.
- The bottom blotter is wide and tabbed.
- Safety is persistent but compact: one top warning strip and short status chips.
- Tables use dense rows, sticky headers, and monospace numbers.

## Tab Structure

Primary dashboard tabs are:
- Paper Trading
  - Current weekly PT-RT runtime truth.
  - Active Week 2 lanes are `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
  - Active Week 2 timeframes are `1h`, `4h`, and `1d`; `15m` is paused/legacy.
  - Candidate/MF-ORIG/wildcard lanes are synthetic-only unless the lane is the baseline control.
  - Fresh Money Flow v1.2 baseline opens can trigger fixed 25 USDC testnet plumbing only under explicit gates.
- Historical Replay
  - Historical visual reference from generated chart/trade JSON.
- Evidence
  - Includes a `Replay strategy` Run Ledger selector.
  - Default mode reviews canonical evidence-pack batch-report rows.
  - Generated replay modes review SV2.0.2 chart-data strategy rows such as canonical Money Flow v1.2 and SOR-EV3 rolling-range variants.
  - Generated replay rows include a `Result` badge comparing PnL and drawdown to the matching Money Flow v1.2 baseline row: green `improved_pnl_drawdown`, amber partial-improvement labels, neutral `same_result`, or red `no bueno`.
  - The selector is review/navigation only; it does not regenerate evidence or approve variants.
- The Lab
- Strategy
  - Shows only the three active Week 2 strategies as active/default UI truth.
  - Archived/research-only variants are intentionally not prominent in the Strategy tab.

The invalid legacy `Experiments` surface is not exposed as a primary tab. Evidence Lab is tied to SOR-EV1/SOR-EV2/SOR-EV3 committed summaries and canonical SV2.0.2 baseline context only.

EV-AUDIT1 remains a committed historical audit artifact, but DASH-PT1.1 removes Audit Review from the visible top-level dashboard navigation to keep Week 2 startup focused.

`UAT Chart Cockpit` and `UAT2 Shadow Run` remain hidden legacy panels for regression coverage and historical context, but they are no longer top-level navigation tabs.

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
- `evidence-lab-header`
- `evidence-lab-variant-matrix`
- `evidence-lab-control-pockets`
- `evidence-lab-worst-trades`
- `evidence-lab-late-entry`
- `evidence-lab-adverse-candles`
- `evidence-lab-rsi-macd`
- `evidence-lab-chart-overlay`
- `evidence-lab-overlay-controls`
- `evidence-lab-overlay-inspector`
- `evidence-lab-worst-focus-table`
- `evidence-lab-control-pocket-view`
- `audit-review-verdict-cards`
- `audit-review-scorecard`
- `audit-review-paper-readiness`
- `audit-review-top-hypotheses`
- `audit-review-worst-hypotheses`
- `audit-review-winning-trades`
- `audit-review-losing-trades`
- `audit-review-losing-streaks`
- `audit-review-issues`
- `audit-review-data-integrity`
- `audit-review-inventory`

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
| Chart background | `CHART_BACKGROUND_COLOR` | `#10171b` |
| Theme chart surface | `--color-chart-surface` | theme-specific |
| Theme chart grid | `--color-chart-grid` | theme-specific |
| Theme chart text | `--color-chart-text` | theme-specific |
| Up candle body | `CANDLE_UP_COLOR` | `#f5f7f2` |
| Down candle body | `CANDLE_DOWN_COLOR` | `#050607` |

TradingView candlesticks use a black/white palette so candle direction does not compete with green/red entry/exit markers, RSI/MACD colors, or EMA overlays. The dashboard resolves chart colors through CSS variables so dark, light, and red-zone themes stay readable; theme changes rebuild chart instances to apply the updated palette. Down candles keep light borders and wicks so they remain visible on the muted chart background.

The brand mark uses the small local `chillguy-logo.jpeg` asset. It is decorative and does not change dashboard evidence, runtime, or endpoint behavior.

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
- PT0.0.2 adds a separate Historical Replay chart lane. It must use historical public candle replay JSON as strategy truth and must not use Hyperliquid testnet public live prices as strategy truth.
- Historical Replay has strategy, symbol, timeframe, period, fill, and date selectors. The default SV2.0.2 lane is `SV2.0.2 canonical Money Flow v1.2`; generated SOR-EV3 research lanes include `SOR-EV3 avoid low rolling range 20` and `SOR-EV3 avoid low rolling range 50` across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1D and both fill assumptions. SV2.1 adds broad active-Hyperliquid-public-metadata 1D replay rows for 2024 / 2025 / YTD / ALL periods, including Money Flow v1.2 plus evidence-only `avoid_low_rolling_range_50`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity` where local selected chart-data JSON exists. MF-ORIG-EV2 adds evidence-only Original Money Flow hypothesis lanes across the same 9 symbols, 4 timeframes, and both fill assumptions when local chart-data JSON exists. Removed older `MACD removed` and `Only close on 5/20 cross` options must stay out of the active selector. No research replay strategy may be presented as a production Money Flow rule change or approval.
- PT0.0.3 added `1D` to Historical Replay and a data-horizon panel as deterministic aggregation from `4h` historical replay candles. SV2.0 supersedes that prior dashboard-only state by adding `sleeve_1d` as a real Money Flow v1.2 sleeve and by loading direct Hyperliquid public-mainnet 1d readiness/evidence rows.
- SV2.0.1 canonicalizes internal timeframe values to `1d` while displaying `1D`, surfaces staged-vs-DB-import truth, and must not label compact replay/evidence rows as canonical evidence when `canonical_evidence_status.status` is blocked.
- Historical Replay selectors may show expanded SV2.0 symbols even when full replay chart candles are not yet present. In that case, show readiness/evidence status and an explicit no-replay-chart state rather than substituting another symbol/timeframe chart.
- Historical Replay must show compact range, coverage, source, canonical-evidence/import status, aggregation status, and warnings so missing Jan 2025 or period-specific data is visible instead of silently shortening the window.
- Historical Replay must make RSI and MACD visible during entry/exit review. EMA5/EMA10/SMA20 remain on the price pane, while RSI 14 and MACD render in separate TradingView panes inside the same chart instance so the crosshair/time scale stays aligned with candles and each indicator has its own readable value scale.
- Historical replay markers mean historical paper replay fills only: green is entry fill, red is exit fill, yellow is trim/reduce. They are not live trades and not testnet orders.
- Historical replay markers are clickable. Clicking an arrow selects the linked replay trade in the Trade Inspector; trade table row clicks use the same selection path and should not force a full chart rebuild.
- The Trade Inspector should read like a focused review card, not a raw data dump: selected trade, PnL, entry/exit price, equity movement, entry/exit reason chips, indicator tiles, and cost context should be visually grouped.
- Historical replay must keep the sandbox execution ledger visually separate from replay equity and PnL.
- PT0 prefers live Hyperliquid testnet public candles. While browser live polling is enabled, the chart must wait for the selected symbol/timeframe `candleSnapshot` and must not render non-selected symbols from committed synthetic/local fallback candles as if they were live.
- Local PT0/UAT summaries may still populate watchlist, side-panel, and fallback status text; chart rendering from local summaries is reserved for explicit disabled-polling/debug fallback states.
- The dashboard uses a local official `lightweight-charts` standalone bundle, not TradingView Advanced Charts, not the Trading Platform library, and not the hosted TradingView widget.
- If candles are insufficient, display explicit unavailable states.
- The native Lightweight Charts right price scale must remain visible, and the dashboard adds a compact `Price USDC` readout beside the chart for latest/high/low/open/close price context.
- PT0.0.1 chart stability requires an explicit bounded chart height, currently implemented as a responsive clamp rather than min-height-only sizing.
- Parent chart containers must use `min-height: 0` and `overflow: hidden` where needed so Lightweight Charts children cannot grow the page.
- The TradingView chart instance and series handles must be reused across 15-second public refreshes whenever the selected symbol/timeframe has not changed.
- Live refreshes should call `setData()`, `setMarkers()`, and explicit `chart.resize(width, height)` from measured dimensions instead of destroying/recreating the chart.
- `autoSize: true` must not be reintroduced without proving it cannot form a ResizeObserver feedback loop.
- `chart.applyOptions({ autoSize: true })` must not be called from `ResizeObserver`.
- `fitContent()` should run only on initial chart creation for a symbol/timeframe or from a future explicit reset-view action, never on every live refresh.
- Emergency public-polling fallback flags are supported: `?disableLivePolling=true` and `?livePolling=false`.

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

## Evidence Lab Rules

- Evidence Lab reviews SOR-EV1/SOR-EV2/SOR-EV3 research variants and the latest MF-ORIG-EV2 / MF-ORIG-EV1.1 Original Money Flow evidence JSON against canonical SV2.0.2 DB-imported baseline context.
- The MF-ORIG section must label EV2 as evidence-only generated evidence packs when present, and EV1.1 as corrected replay/report fallback when EV2 is unavailable.
- The SOR-EV1/SOR-EV2 Variant Summary Matrix must use founder-review labels to distinguish `promising_*`, `mixed_*`, `deferred_*`, no-op, diagnostic-only, and hard-rejected rows instead of flattening every non-candidate into rejected.
- SOR-EV3 `avoid_sideways_low_volatility` rows must distinguish blocked open signals from matched canonical baseline trades with PnL attribution.
- SOR-EV3 founder-review labels must distinguish `candidate_for_more_evidence`, `promising_*`, mixed/not-promoted, and hard rejected labels. A `promising_*` label is review context only and must not imply approval.
- SOR variants and MF-ORIG hypotheses are evidence-only and must not be labeled approved for production.
- Completed-trade overlays and lookahead diagnostics are not production candidates.
- Only true-forward replay variants can become candidates for deeper canonical evidence.
- Missing bundle fields must render as `data_not_available_in_sor_ev_bundle`, not as zero.
- Dashboard date filters are display-only recalculations and do not regenerate canonical evidence packs.
- SOR-EV2.2 variant chart overlays use SV2.0.2 chart/trade JSON as visualization context, not as new canonical evidence.
- Baseline markers use canonical SV2.0.2 entries/exits: green for baseline entry, red for baseline exit, yellow for forced close.
- Variant/context markers may render only when SOR-EV2 supplies linkable timestamps. Missing exact marker data must render as `exact_overlay_unavailable_from_sor_ev_bundle`.
- Non-true-forward overlay methods must display `diagnostic_only_not_candidate`.
- Worst-trade focus mode may center the chart on a selected loss and update the inspector, but it must not imply a production variant approval.
- Evidence Lab must not add order controls, paper/live toggles, private/signed/order endpoint calls, or rule mutation behavior.

Shadow and paper-observation markers are not actual trades. Sandbox lifecycle probes are not strategy performance trades.

## Paper Trading Rules

- Paper Trading is PT-RT1 forward-observation UI, not canonical evidence regeneration and not historical replay.
- Strategy truth must be labeled as Hyperliquid public mainnet market data.
- The weekly command-center default must use `1h` selected-timeframe scope. `All active` must mean only `1h + 4h + 1d`, must exclude `15m`, and must state that it is not one combined account.
- `15m` must stay visible only as paused/legacy data with `disabled_for_week1_noise_reduction`; it must not create new active Week 1 entries.
- PT-RT1.1B public-mainnet connection status should be visible before founder starts the 24-hour probes-disabled run.
- Browser-side Paper Observation market-data polling may call Hyperliquid public mainnet `allMids` and selected-pair `candleSnapshot` only; it must not call testnet prices, private/signed/order/account payloads, or require API keys.
- The expanded scanner watchlist should visibly tick latest public market data and keep the visible table compact: symbol, mid price, and health. Market-data health is `unhealthy` when the latest tick is missing or stale for more than 2 minutes.
- The selected pair/timeframe should render a live TradingView Lightweight chart from public mainnet candles when available and fall back to ignored PT-RT1 runtime summary candles without guessing missing timestamps.
- Testnet probes must be displayed in a separate plumbing-only panel.
- Testnet fills must never be displayed as strategy PnL.
- Each lane must show an independent synthetic 10,000 USDC ledger.
- PT-RT1.1A requires exactly 10 visible lanes: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, `avoid_low_rolling_range_50`, `mf_orig_stage_filter_only_full_equity`, `mf_orig_stage2_pullback_reclaim_full_equity`, `mf_orig_1d_stage2_5_20_crossover_full_equity`, `mf_orig_1d_stage2_breakout_resistance_full_equity`, `wildcard_btc_regime_guard`, `wildcard_multi_timeframe_alignment`, and `wildcard_volatility_expansion_breakout`.
- Scanner metadata must keep requested/resolved symbol, source list, supported/blocked state, precision, data health, scanner eligibility, and reason codes available to runtime/detail surfaces; the visible founder watchlist stays compact with symbol, mid price, and health.
- The Signal / Decision Stream replaces the old Market Data Health panel and should categorize intended entries, actual synthetic opens, no-trade/blocked rows, exits, duplicate ignored rows, and data-unavailable rows from the PT-RT1 decision stream.
- Testnet plumbing status must distinguish audit-only shape generation from actual testnet order transport. In the normal Paper Trading view, testnet order transport is disabled and signed testnet orders are zero.
- Wildcard lanes must expose pass/block reason-code summaries and remain observation-only expert hypotheses.
- Candidate and MF-ORIG lanes must be labeled evidence-only / not production-approved.
- Date filters must say `display-only filter`, `not canonical evidence`, and `not backend replay`.
- Runtime summary files under `reports/paper_runtime/` are ignored local state; committed summaries are readiness/configuration fallbacks.
- Missing runtime state must render as explicit empty state; do not show fake zero trades as evidence.
- The testnet probe panel must show disabled/enabled state, kill switch, daily cap, remaining count, last lifecycle, unknown-state block, and testnet-only labels.
- No order, cancel, retry, amend, approval, live, route, SOR, fanout, CBBO, or target-reselection controls may be added.

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
