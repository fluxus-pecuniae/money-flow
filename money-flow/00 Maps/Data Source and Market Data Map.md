# Data Source and Market Data Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This note separates strategy evidence data, dashboard display data, sandbox execution plumbing, and future real-time paper-observation data.

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

## Real-Time Paper Observation Future Data

PT-RT1, if scoped, should use trusted public mainnet market data for strategy truth:

- fully closed candle detection
- real-time indicators
- signal audit logs
- internal 10,000 USDC paper ledger
- realized/unrealized PnL
- drawdown and data-health alarms

PT-RT1 is not approved or implemented by OB2.0.

## Private / Signed Endpoints

Private/signed/order endpoints are not required for historical evidence or OB2.0. They remain forbidden unless a later explicit sandbox/testnet plumbing phase scopes them under approval. Live private/order endpoints remain not approved.
