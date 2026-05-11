# PT0.0.3 Historical Data Horizon + 1D Replay Support

## Scope

Status: implemented

PT0.0.3 extends the historical replay cockpit to include `1D` historical replay support and truthful data-horizon reporting for BTC, ETH, and SOL across `15m`, `1h`, `4h`, and `1D`.

SV2.0 supersession note:

```text
PT0.0.3 did not create a production Money Flow 1D sleeve.
SV2.0 later adds sleeve_1d as a real Money Flow v1.2 sleeve.
SV2.0 also refreshes Hyperliquid public mainnet data for the expanded BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB universe.
```

Target historical start:

```text
2025-01-01T00:00:00Z
```

Generated replay export:

```text
docs/pt0_0_3_historical_strategy_replay_summary.json
```

## Non-Goals

Status: verified

- No orders were submitted.
- No order endpoints were called.
- Hyperliquid testnet market data is not strategy truth.
- Money Flow rules are unchanged.
- No strategy parameters were optimized.
- No stop-loss, entry, RSI, market-structure, or SOR variants were added.
- Research-only replay variants are available for visual analysis; they do not change production Money Flow rules.
- No paper/live execution behavior was added.
- Sandbox execution plumbing remains separate from historical replay.

## Source Strategy

Status: implemented

The committed PT0.0.2 historical replay summary is the trusted local historical source for PT0.0.3. It was built from Hyperliquid public historical candles and already separates historical strategy truth from Hyperliquid testnet execution plumbing.

Source priority remains:

1. Persisted strategy-validation candles.
2. Trusted offline imported CSV/JSON candles.
3. Deterministic aggregation from existing lower-timeframe historical candles.
4. Public/vendor/archive import requirement report.

For this repo state, the usable committed source is:

```text
docs/pt0_0_2_historical_strategy_replay_summary.json
```

## 1D Replay Support

Status: implemented

`1D` is now present in:

- Data readiness audit.
- Replay export JSON.
- Dashboard timeframe selector.
- Dashboard data horizon panel.
- BTC / ETH / SOL comparison data.
- Tests.

Important boundary:

```text
1D candles aggregated from 4h historical replay candles.
1D candles are aggregated from 4h historical replay candles.
This did not create a new Money Flow 1D sleeve in PT0.0.3.
SV2.0 later creates sleeve_1d as the real Money Flow v1.2 sleeve.
```

Aggregation convention:

- Source timeframe: `4h`.
- Day boundary: UTC.
- OHLCV: daily open from first 4h candle, high/low from in-day extrema, close from last 4h candle, volume sum.
- Replay markers/trades: projected from existing 4h replay trades onto daily candles for visual horizon analysis.
- Labels: `historical_aggregation_used`, `not_a_new_1d_money_flow_sleeve`.

## Data Readiness

Status: implemented

The Jan 2025 target is not met by the currently committed local replay source. This is reported as data readiness, not strategy failure.

| Symbol | Timeframe | Replay ready | Source | Earliest | Latest | Candles | Target met | Target coverage | Aggregation | Reason codes |
| --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| BTC | 15m | yes | trusted_offline_historical_candles | 2026-03-15T00:15:00+00:00 | 2026-05-05T00:00:00+00:00 | 4896 | no | 10.429448% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| BTC | 1h | yes | trusted_offline_historical_candles | 2026-01-01T01:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 2976 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| BTC | 4h | yes | trusted_offline_historical_candles | 2026-01-01T04:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 744 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| BTC | 1D | yes | deterministic_aggregation_from_historical_replay_candles | 2026-01-02T00:00:00Z | 2026-05-05T00:00:00Z | 124 | no | 25.357873% | yes, from 4h | historical_aggregation_used, historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| ETH | 15m | yes | trusted_offline_historical_candles | 2026-03-15T00:15:00+00:00 | 2026-05-05T00:00:00+00:00 | 4896 | no | 10.429448% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| ETH | 1h | yes | trusted_offline_historical_candles | 2026-01-01T01:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 2976 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| ETH | 4h | yes | trusted_offline_historical_candles | 2026-01-01T04:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 744 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| ETH | 1D | yes | deterministic_aggregation_from_historical_replay_candles | 2026-01-02T00:00:00Z | 2026-05-05T00:00:00Z | 124 | no | 25.357873% | yes, from 4h | historical_aggregation_used, historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| SOL | 15m | yes | trusted_offline_historical_candles | 2026-03-15T00:15:00+00:00 | 2026-05-05T00:00:00+00:00 | 4896 | no | 10.429448% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| SOL | 1h | yes | trusted_offline_historical_candles | 2026-01-01T01:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 2976 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| SOL | 4h | yes | trusted_offline_historical_candles | 2026-01-01T04:00:00+00:00 | 2026-05-05T00:00:00+00:00 | 744 | no | 25.357873% | no | historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |
| SOL | 1D | yes | deterministic_aggregation_from_historical_replay_candles | 2026-01-02T00:00:00Z | 2026-05-05T00:00:00Z | 124 | no | 25.357873% | yes, from 4h | historical_aggregation_used, historical_candles_available, historical_target_start_not_available, historical_earliest_available_after_target |

## Dashboard Updates

Status: implemented

The Historical Replay tab now loads `docs/pt0_0_3_historical_strategy_replay_summary.json` before falling back to PT0.0.2. The loader keeps the first available PT0.0.3 payload instead of overwriting it with the older PT0.0.2 fallback, so `1D` remains visible in the timeframe selector.

Dashboard additions:

- `1D` appears in the timeframe selector.
- Replay strategy selector includes `OG replay / strategy`, `MACD removed`, and `Only close on 5/20 cross`.
- Data horizon panel shows target start, earliest available, latest available, coverage, source, aggregation status, and warnings.
- `1D` selections are explicitly labeled as aggregated from lower-timeframe historical replay data.
- Testnet data remains labeled as not strategy truth.

## Dynamic Equity

Status: verified

Dynamic paper replay remains unchanged:

- Initial equity: `10000 USDC`.
- Capital sizing mode: `dynamic_equity_pct`.
- Sizing basis: realized equity.
- Risk display basis: realized plus unrealized.
- The replay does not reset every trade to static `10000 USDC`.

The 1D replay export includes candles, indicators, markers, trades, and equity curve records.

## Missing Horizon

Status: needs_verification

The current committed historical replay source does not contain candles back to Jan 2025.

Import need:

```text
BTC / ETH / SOL
15m / 1h / 4h
target start: 2025-01-01T00:00:00Z
venue/product: Hyperliquid USDC perpetual historical public candles
```

After import, regenerate PT0.0.3 so 1D can aggregate from the longer lower-timeframe source.

## Boundary Confirmation

Status: verified

- Historical/mainnet/public candle data remains strategy truth.
- Hyperliquid testnet remains execution plumbing only.
- No testnet prices are used as historical strategy truth.
- No live endpoint was used.
- No private/signed/order endpoint was used.
- No orders were submitted.
- Money Flow rules are unchanged.
- No 1D production strategy sleeve was created.
- `Only close on 5/20 cross` is research-only and does not change production Money Flow rules.

## Next Recommended Phase

Status: deferred

Recommended next phase:

```text
PT0.0.4 — Historical Data Backfill + Replay Regeneration
```

Scope should import or attach trusted historical BTC/ETH/SOL Hyperliquid public candles back to Jan 2025, rerun readiness, regenerate 15m/1h/4h/1D replay exports, and preserve strategy-rule freeze.
