# UAT4.2 Live Market Dashboard + Paper-Equity Runtime Monitor

UAT4.2 adds read-only live-market monitoring surfaces and internal paper-equity visibility for the UAT dashboard.

This phase does not submit orders, does not add order controls, does not call live endpoints, does not call private order endpoints, does not use live exchange API keys, does not change Money Flow rules, does not add smart routing/SOR/fanout/target reselection, and does not generate evidence packs.

## Scope

| Item | Status | Notes |
| --- | --- | --- |
| Live public market data service | `implemented` | `services/uat/live_monitor.py` models Hyperliquid public-read-only market snapshots and validates allowlisted public info payloads only. |
| Dashboard data path | `implemented` | Dashboard loads `docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json` as the UAT4.2 local refresh JSON. |
| Watchlist coverage | `verified` | BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, and AAVE are represented as observation-only markets. |
| Chart status | `implemented` | The cockpit now prefers refreshed UAT4.2 candle/price data and falls back to UAT2 local summaries when needed. |
| Indicator status | `implemented` | EMA5, EMA10, SMA20, RSI, MACD, MACD signal, and MACD histogram are computed deterministically by UAT4.2 helpers. |
| Strategy scanner status | `implemented` | Scanner output is `paper_observation_signal` / shadow-style records only and creates no strategy or order artifacts. |
| Entry/exit marker status | `implemented` | Dashboard distinguishes shadow markers, paper-observation markers, and routed sandbox-order lifecycle markers. |
| Balance/position polling status | `implemented` | UAT4.2 defines a 60-second sandbox private-read-only polling policy that forbids order/cancel/amend/retry/live categories. |
| Internal paper-equity ledger | `implemented` | Starting internal paper equity is `10000` USDC; current equity updates as initial plus realized and unrealized PnL. |
| Routed orders tab | `implemented` | UAT3.4 routed sandbox order ledger remains visible without order controls. |
| PT0 supersession | `implemented_by_pt0` | PT0 has superseded the prior roadmap-only PT0 state with TradingView Lightweight Charts and top-20 Hyperliquid-supported paper/sandbox runtime foundation. |

## Live Market Data Status

Status: `implemented`

UAT4.2 adds `services/uat/live_monitor.py` and `scripts/refresh_uat42_live_monitor.py`.

The public market-data policy allows only Hyperliquid public-read-only info categories such as `allMids`, `candleSnapshot`, `l2Book`, `fundingHistory`, `meta`, and `metaAndAssetCtxs`.

The default generated summary is deterministic local refresh JSON for dashboard/runtime tests. It does not read credentials, call network, call private endpoints, call signed endpoints, or call order endpoints. A future operator refresh can wire caller-supplied public transport under the same public-read-only validator.

Live-charting hotfix status: `implemented`

The browser now polls Hyperliquid testnet public `allMids` and `candleSnapshot` every 15 seconds for watchlist prices and the selected chart. This uses no API keys, private endpoints, signed endpoints, order endpoints, order controls, or live endpoint. If public polling is unavailable, the cockpit falls back to `docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json`.

## Watchlist Coverage

Status: `verified`

The UAT dashboard watchlist covers:

`BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, AAVE`

Each row remains observation-only. ETH has routed sandbox lifecycle history from UAT3.4, but every future sandbox order still requires separate approval and gates. The top-20 assets are not broadly order-approved.

## Indicators

Status: `implemented`

The UAT4.2 monitor computes:

- EMA5
- EMA10
- SMA20
- RSI
- MACD
- MACD signal
- MACD histogram

If a candle set is too short, helpers return `indicator_unavailable_insufficient_history`. The dashboard must not invent missing indicator values.

## Strategy Scanner

Status: `implemented`

Scanner output is observation-only and may include:

- `paper_observation_signal`
- `would_open`
- `would_close`
- `would_hold`
- `would_reduce`
- `no_trade`
- `invalid`
- `risk_blocked`

Forbidden outputs remain:

- `StrategyDecision`
- `OrderIntent`
- `PreparedVenueOrder`
- `SubmittedOrder`
- executable approval
- live artifact

## Entry / Exit Markers

Status: `implemented`

Green markers:

- `shadow would-open`
- `paper observation would-open`
- `sandbox order accepted/open`

Red markers:

- `shadow would-close`
- `paper observation would-close`
- `sandbox cancel`

Shadow and paper-observation markers are not actual trades. Routed sandbox markers are sandbox/testnet lifecycle records, not paper/live trading and not performance validation.

## Balance / Position Polling

Status: `implemented`

UAT4.2 defines a 60-second sandbox private-read-only polling policy.

60-second poll policy: sandbox private-read-only only.

Allowed categories:

- `sandbox_private_read_only_account`
- `sandbox_private_read_only_balance`
- `sandbox_private_read_only_position`
- `sandbox_private_read_only_equity`

Forbidden categories:

- `sandbox_order_submission`
- `sandbox_order_cancel`
- `sandbox_order_amend`
- `sandbox_order_retry`
- `live_private_forbidden`
- `private_signed_order`

The dashboard displays sandbox account confirmation from current UAT summaries and labels it as sandbox/testnet, not-live, and not real capital. If realized PnL, unrealized PnL, positions, or open orders are unavailable, the summary marks the fields unavailable instead of inventing values.

## Internal 10,000 USDC Paper-Equity Ledger

Status: `implemented`

Initial internal paper equity: `10000` USDC.

Current paper equity:

`initial_paper_equity + realized_pnl + unrealized_pnl`

This ledger is internal paper/sandbox simulation. It is not live equity and not real account value. Hyperliquid testnet balance is displayed as sandbox account confirmation, not as live capital.

## Sizing Policy

Status: `implemented`

Preferred UAT policy:

- `sizing_basis = realized_equity`
- `risk_display_basis = realized_plus_unrealized`

Future paper/sandbox trades should size from current realized paper equity, not from a static `10000` USDC value on every trade. Unrealized PnL is included in the dashboard risk view.

PT0 now separately approves and gates the paper/sandbox runtime foundation.

## Dashboard Status

Status: `implemented`

The exchange-style UAT cockpit now shows:

- refreshed public-read-only market rows;
- computed indicators;
- paper-observation scanner markers;
- internal paper-equity card;
- sandbox balance polling policy card;
- positions/unavailable-state panel;
- UAT3.4 routed sandbox lifecycle ledger;
- no-live/no-real-capital labels.

## No-Order-Control Confirmation

Status: `verified`

No-order-control confirmation: verified.

UAT4.2 does not add:

- submit controls;
- cancel controls;
- retry controls;
- amend controls;
- approval controls;
- market buy/sell controls;
- paper/live toggle;
- auto-trade toggle.

Order submission remains disabled in the dashboard. UAT4.2 did not submit orders. UAT4.2 is not live trading. PT0 later approved Hyperliquid testnet/sandbox paper trading and broader top-20 supported paper/sandbox scope, but live trading remains not approved.

Live trading is not approved.

## PT0 Supersession Status

Status: `implemented_by_pt0`

PT0 has superseded the prior roadmap-only PT0 state and is now implemented as a separate phase in `docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md`.

PT0 adds:

- explicit paper-trading approval for Hyperliquid testnet/sandbox only;
- explicit broader top-20 Hyperliquid-supported paper/sandbox approval;
- TradingView Lightweight Charts integration;
- PT0 paper scanner/runtime summary;
- top-20 paper universe eligibility and metadata/precision blockers;
- internal 10,000 USDC paper-equity ledger and sizing policy;
- PT0 risk limits and sandbox routing default-disabled by `PT0_SANDBOX_ORDER_ROUTING_ENABLED=false`.

## PT0 Roadmap

Status: `captured`

PT0 — TradingView Lightweight Charts + Broad Top-20 Paper/Sandbox Runtime Foundation now includes:

- controlled paper-equity ledger;
- Hyperliquid sandbox/testnet only;
- no live endpoint;
- internal 10k equity;
- realized/unrealized PnL tracking;
- order sizing from current equity;
- approval-gated strategy-to-order path;
- risk limits;
- kill switch;
- dashboard monitoring;
- broader top-20 Hyperliquid-supported paper/sandbox approval, still gated and sandbox/testnet only.

## Current Decision

UAT4.2 is dashboard/live-monitoring and internal paper-equity visibility only.

PT0 is implemented after UAT4.2. PT0 remains Hyperliquid testnet/sandbox only and still does not approve live trading or real-capital trading.
