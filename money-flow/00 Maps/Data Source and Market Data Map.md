# Data Source and Market Data Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This note separates strategy evidence data, dashboard display data, sandbox execution plumbing, and current real-time Paper Trading observation data.

## Current Operator Summary

- Current operating surface: `Paper Trading` dashboard tab for PT-RT forward observation.
- Current runtime: `PT-RT1.5.1` smoke/review scope at `reports/paper_runtime/pt_rt1_5_1_smoke/`.
- Active timeframes: `1h`, `4h`, `1d`.
- Paused timeframes: `15m` is paused for Week 1 noise reduction and legacy review only.
- Strategy truth: public Hyperliquid mainnet fully closed candles and derived indicators.
- Synthetic PnL truth: independent synthetic 10,000 USDC paper ledgers per lane.
- Testnet plumbing: fixed 25 USDC Hyperliquid testnet transport is baseline-only and fresh-post-start only when PT-RT1.5.1 gates pass.
- Production approval: no strategy is production-approved.
- Live trading: not approved; no real-capital trading is approved.
- Next recommended action: keep public mainnet strategy truth, generated dashboard JSON, and Hyperliquid testnet plumbing explicitly separated.

## Historical Public Mainnet Evidence Data

| Field | Current Truth |
| --- | --- |
| canonical source | Hyperliquid public mainnet candles |
| canonical storage | Strategy Validation DB-imported candle store |
| canonical baseline | SV2.0.2 packs at `20260512T064916Z` |
| supported symbols | BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX |
| deferred symbol | SHIB/kSHIB, unit semantics deferred |
| timeframes | `15m`, `1h`, `4h`, `1d` |

Historical public mainnet candles are strategy evidence truth.

## Dashboard Chart Display Data

Generated chart/trade JSON under `reports/strategy_validation/*dashboard_chart_data*/` is for visualization. It can show candles, indicators, markers, trades, and equity curves, but it does not become canonical evidence and does not approve a strategy.

Dashboard date filters are display-only recalculations from loaded trades/candles.

## Hyperliquid Testnet / Sandbox Execution Plumbing

Hyperliquid testnet/sandbox is used for plumbing tests:

- account targeting
- sandbox private-read-only balance/drawdown checks
- tick/lot formatting
- one approved accepted/open -> cancel -> reconcile lifecycle
- routed sandbox ledger visibility

Hyperliquid testnet data is not strategy truth. Testnet prices are not strategy evidence truth.

## Real-Time Paper Trading Observation Data

PT-RT1 uses trusted public mainnet market data for strategy truth:

- fully closed candle detection
- real-time indicators
- signal audit logs
- internal 10,000 USDC paper ledger
- realized/unrealized PnL
- drawdown and data-health alarms

The founder-facing dashboard tab is Paper Trading. PT-RT remains a forward-observation substrate and does not approve production rules, live trading, order submission, or canonical historical evidence regeneration.

## Private / Signed Endpoints

Private/signed/order endpoints are not required for historical evidence or OB2.0. They remain forbidden unless a later explicit sandbox/testnet plumbing phase scopes them under approval. Live private/order endpoints remain not approved.
