# UAT1 Public Read-Only Connectivity And Top-20 Universe

Recorded at: `2026-05-10T07:18:43Z`

UAT1.1 follow-up: `docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md` adds model/report-only shadow signal audit, operator-visible shadow drawdown, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT1.1 cleared UAT2 start blockers for a future no-order phase; UAT1.1 does not run UAT2, run Money Flow over live data, submit orders, create strategy/execution artifacts, or approve paper/live trading.

UAT2 follow-up: `docs/uat2_shadow_strategy_top20_observation.md` completed a bounded no-order shadow strategy observation using this UAT1 universe snapshot, public read-only Hyperliquid candles, and shadow audit records only. UAT2 did not use API keys, private/signed/order endpoints, order submission, strategy/execution artifacts, paper/live behavior, routing artifacts, Money Flow rule changes, or evidence packs. UAT3 remains blocked pending explicit sandbox-order design approval and deeper sandbox lifecycle wiring.

## Scope

UAT1 is public read-only connectivity and universe resolution only. It does not run Money Flow, submit orders, use API keys, call private endpoints, call signed endpoints, call order endpoints, add paper trading, add live trading, add routing behavior, change Money Flow rules, or generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Runtime Mode And Network Gate

| Field | Value |
| --- | --- |
| Runtime mode | `uat` |
| UAT1 public read-only mode | `true` |
| Public read-only network allowed | `true` |
| Private endpoints allowed | `false` |
| Signed endpoints allowed | `false` |
| Order endpoints allowed | `false` |
| API keys used | `false` |

## Hyperliquid Public Info Type Results

| Info type | Attempted | Classification | Endpoint URL | Success | HTTP status | Shape usable | Needs follow-up | Sanitized error |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| `allMids` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |
| `candleSnapshot` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |
| `fundingHistory` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |
| `l2Book` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |
| `meta` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |
| `metaAndAssetCtxs` | `true` | `public_read_only` | `https://api.hyperliquid.xyz/info` | `true` | 200 | `true` | `false` |  |

## Top-20 Source

| Field | Value |
| --- | --- |
| Provider | `coingecko_public_markets` |
| URL | `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=20&page=1&sparkline=false` |
| Attempted | `true` |
| Success | `true` |
| Source timestamp | `2026-05-10T07:18:31+00:00` |
| Source freshness seconds | `0` |
| Ranking field | `source_order_from_volume_desc_response` |
| Volume metric | `24h_volume_usd` |
| API key used | `false` |
| Sanitized error |  |

## Top-20 Raw List Summary

| Rank | Symbol | 24h volume USD | Source asset id |
| ---: | --- | ---: | --- |
| 1 | `USDT` | 35077060298.00 | `tether` |
| 2 | `BTC` | 17770468644.00 | `bitcoin` |
| 3 | `ETH` | 9843539774.00 | `ethereum` |
| 4 | `USDC` | 6240446157.00 | `usd-coin` |
| 5 | `SOL` | 2164426801.00 | `solana` |
| 6 | `XRP` | 975090136.00 | `ripple` |
| 7 | `ZEC` | 755399794.00 | `zcash` |
| 8 | `BNB` | 635383847.00 | `binancecoin` |
| 9 | `SUI` | 618863097.00 | `sui` |
| 10 | `TON` | 575694663.00 | `the-open-network` |
| 11 | `DOGE` | 572841125.00 | `dogecoin` |
| 12 | `USD1` | 480726505.00 | `usd1-wlfi` |
| 13 | `TRX` | 440304476.00 | `tron` |
| 14 | `QUQ` | 416556245.00 | `quq` |
| 15 | `LAYER` | 344868660.00 | `solayer` |
| 16 | `BILL` | 327593848.00 | `billions-network` |
| 17 | `CHIP` | 317300755.00 | `chip-2` |
| 18 | `UNI` | 307054933.00 | `uniswap` |
| 19 | `ONDO` | 268306266.00 | `ondo-finance` |
| 20 | `AAVE` | 260017854.00 | `aave` |

## Hyperliquid Intersection Summary

Included assets: `15`.

Excluded assets: `5`.

Top-20 inclusion means observation candidate only. It is not strategy approval, paper-trading approval, live-trading approval, or order-submission approval.

## Included Assets

| Symbol | Rank | 24h volume USD | Venue symbol | Market type | Product type | Quote | Settlement | Asset id | Observation only | Strategy approved | Paper approved | Live approved |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BTC` | 2 | 17770468644.00 | `BTC` | `perpetual` | `perp` | `USDC` | `USDC` | `0` | `true` | `false` | `false` | `false` |
| `ETH` | 3 | 9843539774.00 | `ETH` | `perpetual` | `perp` | `USDC` | `USDC` | `1` | `true` | `false` | `false` | `false` |
| `SOL` | 5 | 2164426801.00 | `SOL` | `perpetual` | `perp` | `USDC` | `USDC` | `5` | `true` | `false` | `false` | `false` |
| `XRP` | 6 | 975090136.00 | `XRP` | `perpetual` | `perp` | `USDC` | `USDC` | `25` | `true` | `false` | `false` | `false` |
| `ZEC` | 7 | 755399794.00 | `ZEC` | `perpetual` | `perp` | `USDC` | `USDC` | `214` | `true` | `false` | `false` | `false` |
| `BNB` | 8 | 635383847.00 | `BNB` | `perpetual` | `perp` | `USDC` | `USDC` | `7` | `true` | `false` | `false` | `false` |
| `SUI` | 9 | 618863097.00 | `SUI` | `perpetual` | `perp` | `USDC` | `USDC` | `14` | `true` | `false` | `false` | `false` |
| `TON` | 10 | 575694663.00 | `TON` | `perpetual` | `perp` | `USDC` | `USDC` | `66` | `true` | `false` | `false` | `false` |
| `DOGE` | 11 | 572841125.00 | `DOGE` | `perpetual` | `perp` | `USDC` | `USDC` | `12` | `true` | `false` | `false` | `false` |
| `TRX` | 13 | 440304476.00 | `TRX` | `perpetual` | `perp` | `USDC` | `USDC` | `37` | `true` | `false` | `false` | `false` |
| `LAYER` | 15 | 344868660.00 | `LAYER` | `perpetual` | `perp` | `USDC` | `USDC` | `182` | `true` | `false` | `false` | `false` |
| `CHIP` | 17 | 317300755.00 | `CHIP` | `perpetual` | `perp` | `USDC` | `USDC` | `229` | `true` | `false` | `false` | `false` |
| `UNI` | 18 | 307054933.00 | `UNI` | `perpetual` | `perp` | `USDC` | `USDC` | `39` | `true` | `false` | `false` | `false` |
| `ONDO` | 19 | 268306266.00 | `ONDO` | `perpetual` | `perp` | `USDC` | `USDC` | `106` | `true` | `false` | `false` | `false` |
| `AAVE` | 20 | 260017854.00 | `AAVE` | `perpetual` | `perp` | `USDC` | `USDC` | `28` | `true` | `false` | `false` | `false` |

## Excluded Assets

| Symbol | Rank | 24h volume USD | Reason codes |
| --- | ---: | ---: | --- |
| `USDT` | 1 | 35077060298.00 | `unsupported_by_venue` |
| `USDC` | 4 | 6240446157.00 | `unsupported_by_venue` |
| `USD1` | 12 | 480726505.00 | `unsupported_by_venue` |
| `QUQ` | 14 | 416556245.00 | `unsupported_by_venue` |
| `BILL` | 16 | 327593848.00 | `unsupported_by_venue` |

## Public Market-Data Sample Status

| Symbol | Metadata | Mid/ticker | Candle sample | Order book sample | Funding context | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| `BTC` | `true` | `true` | `true` | `true` | `true` |  |
| `ETH` | `true` | `true` | `true` | `true` | `true` |  |
| `SOL` | `true` | `true` | `true` | `true` | `true` |  |
| `XRP` | `true` | `true` | `true` | `true` | `true` |  |
| `ZEC` | `true` | `true` | `true` | `true` | `true` |  |
| `BNB` | `true` | `true` | `true` | `true` | `true` |  |
| `SUI` | `true` | `true` | `true` | `true` | `true` |  |
| `TON` | `true` | `true` | `true` | `true` | `true` |  |
| `DOGE` | `true` | `true` | `true` | `true` | `true` |  |
| `TRX` | `true` | `true` | `true` | `true` | `true` |  |
| `LAYER` | `true` | `true` | `true` | `true` | `true` |  |
| `CHIP` | `true` | `true` | `true` | `true` | `true` |  |
| `UNI` | `true` | `true` | `true` | `true` | `true` |  |
| `ONDO` | `true` | `true` | `true` | `true` | `true` |  |
| `AAVE` | `true` | `true` | `true` | `true` | `true` |  |

## No-Private / No-Order Confirmation

- Private endpoints used: `false`.
- Signed endpoints used: `false`.
- Order endpoints used: `false`.
- API keys used: `false`.
- Orders submitted: `false`.
- Strategy decisions created: `false`.
- Order intents created: `false`.
- Submitted orders created: `false`.

## UAT2 Readiness Decision

Historical UAT1 decision at the time: `UAT2 is blocked`.

UAT1.1 later cleared the no-order UAT2 start blockers. UAT2 has now completed a bounded no-order shadow observation and did not submit orders.

Remaining blockers:
- `uat2_operator_visible_shadow_drawdown_state`
- `uat2_shadow_signal_audit_surface`
- `broader_structured_log_api_error_redaction_before_uat2_or_uat3`

UAT2, when allowed, remains shadow-only and must compare `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## Boundary Confirmation

UAT1 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, order endpoint calls, evidence packs, strategy variants, or Money Flow rule changes.
