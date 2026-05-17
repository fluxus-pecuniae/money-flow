> Historical note.
> This report is retained for audit/history.
> Current truth lives in [[00_Money_Flow_Command_Center]] and the latest PT-RT / SV / audit docs.
> Do not use this file as current operating instructions unless a current-phase note links to it explicitly.

# PT0 TradingView Charts + Top-20 Paper/Sandbox Runtime Foundation

PAPER TRADING IS APPROVED.

BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED.

PT0 establishes the approved Hyperliquid testnet/sandbox paper-runtime foundation. It integrates TradingView Lightweight Charts, keeps live public market monitoring active, models the internal 10,000 USDC paper-equity ledger, and represents the broader top-20 Hyperliquid-supported paper/sandbox universe behind metadata, precision, risk, lease, label, and no-live gates.

## Scope

| Area | Status | Notes |
| --- | --- | --- |
| Paper approval | `verified` | Founder/operator explicitly approved paper trading for Hyperliquid testnet/sandbox only. |
| Broader top-20 approval | `verified` | Founder/operator explicitly approved broader top-20 Hyperliquid-supported paper/sandbox trading, still gated and sandbox/testnet only. |
| TradingView Lightweight Charts | `implemented` | Dashboard uses the official local `lightweight-charts` standalone bundle at `apps/dashboard/vendor/lightweight-charts.standalone.production.js`. Hosted TradingView widgets, Advanced Charts, and Trading Platform libraries are not used. |
| Live charting | `implemented` | Browser-side Hyperliquid testnet public `allMids` and `candleSnapshot` polling remains public-read-only and feeds the chart. |
| Indicators | `implemented` | EMA5, EMA10, and SMA20 render as chart overlays; RSI, MACD, MACD signal, and MACD histogram remain visible in the indicator dock with explicit insufficient-history states when needed. |
| Entry/exit markers | `implemented` | Green/red Lightweight Charts markers are used for paper scanner and sandbox routed-order lifecycle markers; labels distinguish paper, shadow, and sandbox sources. |
| Watchlist | `implemented` | BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, and AAVE are shown with paper/sandbox eligibility status. |
| Paper scanner | `implemented` | PT0 summary represents paper/sandbox scanner records across 15m, 1h, and 4h. Secondary timeframes are explicitly marked when awaiting public refresh. |
| Paper-equity ledger | `implemented` | Internal paper equity starts at 10,000 USDC, tracks realized/unrealized PnL, and is labeled not-live/not-real-capital. |
| Balance/position polling | `implemented` | The polling policy remains 60 seconds, sandbox private read-only only, and forbids order/cancel/amend/retry/live categories. |
| Routing foundation | `implemented` | Top-20 paper/sandbox route candidates are modeled for Hyperliquid testnet only. Runtime order routing is default-disabled by `PT0_SANDBOX_ORDER_ROUTING_ENABLED=false`. |

## PT0.0.1 Stability Hotfix

PT0.0.1 fixes the dashboard P0 where the TradingView chart could grow/scroll the page downward and jump back around the 15-second refresh. The chart now has a stable bounded container height, live refreshes update existing chart/series handles where possible, the autosize feedback-loop risk is removed, `fitContent()` is not called on every refresh, and live public polling can be disabled with `?disableLivePolling=true` or `?livePolling=false` to use local summary JSON fallback.

PT0.0.1 does not change PT0 paper-equity math, routing policy, risk limits, scanner scope, order routing defaults, or Money Flow rules.

## Non-Goals

PT0 does not enable live trading, live exchange API keys, real-capital trading, production auto-submit, unbounded automation, smart routing, SOR, fanout, CBBO, target reselection, cross-venue routing, Money Flow rule changes, strategy optimization, market-making, evidence packs, or dashboard order buttons.

## Top-20 Eligibility

The initial paper/sandbox universe is the existing Hyperliquid-supported UAT universe:

`BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, AAVE`

The latest PT0 summary records 12 currently eligible assets and 3 blocked assets from current testnet metadata truth. Assets with missing metadata or precision are labeled with blockers such as `paper_universe_unavailable_current_testnet_metadata`, `paper_symbol_not_supported_on_testnet`, and `paper_precision_metadata_missing`. Unsupported assets must not become route candidates.

## Paper Equity

Internal paper equity starts at `10000 USDC`.

The sandbox account balance is only a Hyperliquid testnet confirmation source. It is not live equity and not real capital. The leverage assumption is `10x` because the sandbox account has roughly `1000 USDC`, while PT0 simulates a `10000 USDC` internal paper ledger.

Formula:

```text
current_paper_equity = initial_paper_equity + realized_pnl + unrealized_pnl
```

PT0 sizing policy:

```text
sizing_basis = realized_equity
risk_display_basis = realized_plus_unrealized
```

Future paper/sandbox order sizing must use current internal paper equity, not the static initial 10,000 USDC.

## Risk And Routing Limits

Default PT0 limits:

| Limit | Value |
| --- | --- |
| Max notional pct of paper equity | `0.01` |
| Max absolute notional | `100 USDC` |
| Max orders per day | `5` |
| Max open positions | `3` |
| Max open positions per symbol | `1` |
| Allowed venue | `Hyperliquid testnet` |
| Allowed environment | `sandbox/testnet` |
| Kill switch | must be `false` |
| Live endpoint access | must be `false` |

`PT0_SANDBOX_ORDER_ROUTING_ENABLED` defaults to `false`. A paper scanner signal may create a paper/sandbox route candidate, but unsupported assets, failed precision, fanout/SOR/target reselection, live endpoint access, kill-switch, and limit failures all return `risk_blocked` and do not submit orders.

## No-Live Confirmation

PT0 uses Hyperliquid testnet public-read-only market data for charts and a modeled sandbox private-read-only polling policy for balances/positions. It does not call live endpoints, private order endpoints, signed order endpoints, submit endpoints, cancel endpoints, amend endpoints, retry endpoints, or use API keys for charting.

## Dashboard

The dashboard now uses TradingView Lightweight Charts for candlesticks, volume, EMA overlays, and markers. The safety banner states:

```text
PAPER TRADING IS APPROVED FOR HYPERLIQUID TESTNET/SANDBOX ONLY.
BROADER TOP-20 SUPPORTED PAPER/SANDBOX TRADING IS APPROVED.
LIVE TRADING IS NOT APPROVED.

Live trading is not approved.
REAL-CAPITAL TRADING IS NOT APPROVED.
INTERNAL PAPER EQUITY STARTS AT 10,000 USDC.
```

The dashboard still has no submit, cancel, retry, amend, approve, market buy/sell, live toggle, paper/live toggle, or auto-trade controls.

## PT0.0.2 Historical Replay Note

PT0.0.2 adds a separate Historical Replay cockpit. Historical public candle replay data is Money Flow strategy truth for that cockpit; Hyperliquid testnet prices are not strategy truth and remain sandbox execution plumbing only. The replay cockpit submits no orders, calls no private/signed/order endpoints, uses no API keys, changes no Money Flow rules, and keeps the UAT3.4 sandbox execution ledger separate from historical replay equity.

## Remaining Blockers For PT0.1

- `needs_verification`: supervised continuous scanner operation over the full week.
- `needs_verification`: runtime-controlled sandbox order routing remains disabled by default until PT0.1 approval/run configuration.
- `needs_verification`: 15m and 4h live public candle refresh should be observed during runtime, not inferred from local summary fixtures.
- `blocked`: live trading and real-capital trading remain not approved.

## PT0.1 Roadmap

PT0.1 — Supervised Top-20 Paper/Sandbox Runtime Week may scope continuous scanner operation, real-time chart updates, eligible risk-gated top-20 paper/sandbox route candidates, internal paper-equity/PnL updates, positions/PnL display, chart arrows, and founder monitoring throughout the week.

PT0.1 must still exclude live trading, real capital, SOR, fanout, CBBO, target reselection, and cross-venue routing unless a later explicit approval changes those boundaries.
