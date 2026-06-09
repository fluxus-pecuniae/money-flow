# SV2.2 Hyperliquid Latest Public-Mainnet Replay Refresh

## Verdict

- Status: `latest_replay_complete`
- Purpose: refresh public-mainnet historical data and run the founder-selected Week 2 Paper Trading strategies through Historical Replay.
- Artifact mode: latest-data replay/evidence-style review artifacts; SV2.2 is not itself a replay strategy.
- Runtime boundary: PT-RT paper runtime was not started, stopped, or mutated.
- Trading boundary: no orders, private/signed/order endpoints, API keys, testnet strategy truth, live approval, or production approval.

## Scope

- Generated at UTC: `2026-06-08T10:52:07Z`
- Symbols: `23` founder-approved/resolved symbols
- Timeframes: `1h, 4h, 1d`
- Disabled timeframes: `15m`
- Data source: `public_hyperliquid_mainnet_candles`

## Refresh Result

- Datasets: `69`
- Refreshed datasets: `69`
- Completed strategy replays: `414`
- Status counts: `{'refreshed': 69}`
- Latest 1h close: `2026-06-08T10:00:00Z`
- Latest 4h close: `2026-06-08T08:00:00Z`
- Latest 1d close: `2026-06-08T00:00:00Z`
- Chart data root: `reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data/20260608T105207Z`
- Evidence-style pack count: `207`

## Selected Strategy Replay Scope

- Strategies: `money_flow_v1_2_baseline, avoid_low_rolling_range_20, mf_orig_1d_stage2_breakout_resistance_full_equity`
- Fill assumptions: `next_candle_open, next_candle_close`
- Timeframe scope: `1h, 4h, 1d`; `15m` remains disabled.
- Replay source: refreshed Hyperliquid public-mainnet candles fetched by SV2.2, not stale dashboard rows.

## Top Replay Rows By Net PnL

| Strategy | Symbol | Timeframe | Fill | Net PnL | Trades | Max DD |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `ZEC` | `1d` | `next_candle_open` | `121198.83988580` | `11` | `103199.68356062` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `ZEC` | `1d` | `next_candle_close` | `88253.32715099` | `11` | `93546.07118492` |
| `money_flow_v1_2_baseline` | `ZEC` | `4h` | `next_candle_open` | `45179.58141451` | `98` | `4904.20658752` |
| `avoid_low_rolling_range_20` | `ZEC` | `4h` | `next_candle_open` | `45179.58141451` | `98` | `4904.20658752` |
| `money_flow_v1_2_baseline` | `ZEC` | `1d` | `next_candle_open` | `41615.29499918` | `35` | `37760.60119535` |
| `avoid_low_rolling_range_20` | `ZEC` | `1d` | `next_candle_open` | `41615.29499918` | `35` | `37760.60119535` |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | `XRP` | `1d` | `next_candle_open` | `34536.66291091` | `10` | `14939.83669704` |
| `money_flow_v1_2_baseline` | `ZEC` | `1d` | `next_candle_close` | `32984.77446933` | `35` | `10341.82983117` |
| `avoid_low_rolling_range_20` | `ZEC` | `1d` | `next_candle_close` | `32984.77446933` | `35` | `10341.82983117` |
| `money_flow_v1_2_baseline` | `ZEC` | `4h` | `next_candle_close` | `31583.52865090` | `98` | `7079.77525581` |


## Dashboard Use

- Historical Replay should show SV2.2 as a latest data/replay source, not as a standalone candle-refresh pseudo-strategy.
- Evidence and The Lab should show SV2.2 latest replay freshness separately from canonical SV2.0.2/SV2.1 evidence status.
- The replay strategy dropdown should contain the three Week 2 strategies, not a candle-refresh pseudo-strategy.

## Boundaries

- Public Hyperliquid mainnet candles remain strategy truth.
- Testnet data is not strategy truth.
- Testnet fills do not update synthetic PnL.
- No live trading is approved.
- No strategy is production-approved.
