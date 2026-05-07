# SV1.14 Money Flow Trade Anatomy And Market-Structure Diagnostics

Recorded at: `2026-05-07T12:16:00Z`

Status: `diagnostic_founder_review_ready`

This report is diagnostic only. No Money Flow rules changed, no parameters were optimized, no market-structure filters were added, no routing/execution artifacts were created, and paper/live trading remains deferred.

Scope: Hyperliquid USDC perpetual public-candle research only. Separate research scenarios are not one combined account.

## Current Money Flow Rule Logic

### Readiness Gates

- `strategy_family_enabled`
- `sleeve_enabled`
- `instrument_active`
- `instrument_strategy_eligible`
- `market_data_fresh`
- `indicators_available`
- `latest_candle_available`
- `enough_history`
- `valid_instrument_mapping`

### Entry Rules

- Entry requires `EMA5 > EMA10 > SMA20`.
- RSI must sit inside the configured sleeve band and below the overbought threshold.
- MACD must be constructive when the sleeve requires confirmation.
- Entry quality must be either controlled pullback or continuation quality.
- Price cannot be too extended above EMA5.
- The strategy currently does not enter long when RSI is below the sleeve floor.
- It is not a buy-deep-oversold-weakness system; it is a constructive momentum / controlled pullback system.

### Exit / Reduce / Hold Rules

- `ma_alignment_break_close`
- `trend_invalidated_close`
- `macd_rollover_close`
- `trim_on_overbought_rsi_reduce`
- `hold_when_no_exit_condition_is_active`

### Market Structure Boundary

Market-structure diagnostics in this report are descriptive only. Recent swing highs/lows, support/resistance proximity, and breakout context are not currently used as Money Flow entry or exit filters.

## Component Trade Anatomy

| Component | Runs | Trades | Avg Duration | Avg MAE | Avg MFE | Net Account PnL Sum Across Runs | Ending Equity Range | Most Common Exit | Main No-Trade Reason |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| sleeve_15m | 36 | 7660 | 1.45h | $-29.63 | $44.80 | $-85,938.58 | $6,459.22 to $8,823.01 | ma_alignment_break | bearish_alignment |
| sleeve_1h | 36 | 4484 | 6.57h | $-75.53 | $137.37 | $21,997.91 | $8,313.22 to $13,327.82 | ma_alignment_break | bearish_alignment |
| sleeve_4h | 36 | 1280 | 22.80h | $-146.66 | $211.92 | $-72,379.38 | $6,772.35 to $9,800.07 | ma_alignment_break | bearish_alignment |

### Entry / Exit Reason Diagnostics

#### sleeve_15m

- Entry reason distribution: `money_flow_entry_passed_all_current_entry_rules=7660`
- Exit reason distribution: `ma_alignment_break=6816, macd_rollover=580, trim_on_overbought_rsi=264`
- No-trade reason distribution: `bearish_alignment=97976, entry_quality_not_constructive=524, macd_not_constructive=11396, overextended_rsi=2976, rsi_not_constructive=10076`
- Invalid reason distribution: `insufficient_history=1224`
- Net PnL by entry reason: `money_flow_entry_passed_all_current_entry_rules=$-85,938.58`
- Net PnL by exit reason: `ma_alignment_break=$-140,403.50, macd_rollover=$3,353.00, trim_on_overbought_rsi=$51,111.93`
- Best trade: `ETH sleeve_15m next_candle_close net=$527.05 exit=trim_on_overbought_rsi`
- Worst trade: `ETH sleeve_15m next_candle_close net=$-225.02 exit=ma_alignment_break`

#### sleeve_1h

- Entry reason distribution: `money_flow_entry_passed_all_current_entry_rules=4484`
- Exit reason distribution: `end_of_window_forced_close=8, ma_alignment_break=3932, macd_rollover=352, trim_on_overbought_rsi=192`
- No-trade reason distribution: `bearish_alignment=61372, entry_quality_not_constructive=456, macd_not_constructive=5300, overextended_rsi=1148, rsi_not_constructive=3696`
- Invalid reason distribution: `insufficient_history=1224`
- Net PnL by entry reason: `money_flow_entry_passed_all_current_entry_rules=$21,997.91`
- Net PnL by exit reason: `end_of_window_forced_close=$-407.75, ma_alignment_break=$-93,593.44, macd_rollover=$29,436.36, trim_on_overbought_rsi=$86,562.74`
- Best trade: `ETH sleeve_1h same_candle_close_research_only net=$824.70 exit=trim_on_overbought_rsi`
- Worst trade: `ETH sleeve_1h same_candle_close_research_only net=$-436.18 exit=ma_alignment_break`

#### sleeve_4h

- Entry reason distribution: `money_flow_entry_passed_all_current_entry_rules=1280`
- Exit reason distribution: `end_of_window_forced_close=32, ma_alignment_break=1156, macd_rollover=80, trim_on_overbought_rsi=12`
- No-trade reason distribution: `bearish_alignment=14884, entry_quality_not_constructive=368, macd_not_constructive=892, rsi_not_constructive=648`
- Invalid reason distribution: `insufficient_history=1404`
- Net PnL by entry reason: `money_flow_entry_passed_all_current_entry_rules=$-72,379.38`
- Net PnL by exit reason: `end_of_window_forced_close=$618.61, ma_alignment_break=$-80,579.92, macd_rollover=$630.89, trim_on_overbought_rsi=$6,951.03`
- Best trade: `ETH sleeve_4h next_candle_open net=$727.98 exit=trim_on_overbought_rsi`
- Worst trade: `SOL sleeve_4h next_candle_close net=$-583.30 exit=ma_alignment_break`

## ETH 1h Winning Anatomy

ETH `sleeve_1h` is the clearest positive pocket in the dynamic-equity evidence, but it remains a research observation for founder review.

| Fill | Fee bps | Slip bps | Ending Equity | Net Account PnL | Trades | Win Rate | Profit Factor | MTM Drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `next_candle_close` | 2 | 1 | $13,327.82 | $3,327.82 | 115 | 46.09% | 1.6774 | $1,342.76 |
| `next_candle_close` | 2 | 3 | $12,728.51 | $2,728.51 | 115 | 41.74% | 1.5369 | $1,424.94 |
| `next_candle_close` | 5 | 1 | $12,439.79 | $2,439.79 | 115 | 40.87% | 1.4719 | $1,465.80 |
| `next_candle_close` | 5 | 3 | $11,880.25 | $1,880.25 | 115 | 39.13% | 1.3516 | $1,545.38 |
| `next_candle_open` | 2 | 1 | $12,802.40 | $2,802.40 | 117 | 36.75% | 1.4674 | $1,500.68 |
| `next_candle_open` | 2 | 3 | $12,216.93 | $2,216.93 | 117 | 35.04% | 1.3594 | $1,597.90 |
| `next_candle_open` | 5 | 1 | $11,934.88 | $1,934.88 | 117 | 35.04% | 1.3092 | $1,646.01 |
| `next_candle_open` | 5 | 3 | $11,388.93 | $1,388.93 | 117 | 35.04% | 1.2163 | $1,753.27 |
| `same_candle_close_research_only` | 2 | 1 | $12,823.74 | $2,823.74 | 117 | 37.61% | 1.4714 | $1,499.37 |
| `same_candle_close_research_only` | 2 | 3 | $12,237.30 | $2,237.30 | 117 | 35.04% | 1.3629 | $1,596.62 |
| `same_candle_close_research_only` | 5 | 1 | $11,954.79 | $1,954.79 | 117 | 35.04% | 1.3126 | $1,644.75 |
| `same_candle_close_research_only` | 5 | 3 | $11,407.92 | $1,407.92 | 117 | 35.04% | 1.2194 | $1,751.75 |

- Top winning trades: `ETH sleeve_1h same_candle_close_research_only net=$824.70 exit=trim_on_overbought_rsi; ETH sleeve_1h next_candle_open net=$822.14 exit=trim_on_overbought_rsi; ETH sleeve_1h same_candle_close_research_only net=$802.30 exit=trim_on_overbought_rsi; ETH sleeve_1h next_candle_open net=$799.80 exit=trim_on_overbought_rsi; ETH sleeve_1h same_candle_close_research_only net=$791.54 exit=trim_on_overbought_rsi`
- Worst losing trades: `ETH sleeve_1h same_candle_close_research_only net=$-436.18 exit=ma_alignment_break; ETH sleeve_1h next_candle_open net=$-435.45 exit=ma_alignment_break; ETH sleeve_1h same_candle_close_research_only net=$-425.43 exit=ma_alignment_break; ETH sleeve_1h next_candle_open net=$-424.71 exit=ma_alignment_break; ETH sleeve_1h same_candle_close_research_only net=$-420.28 exit=ma_alignment_break`
- Entry features on ETH 1h winners: `avg_ema_extension_pct=0.0046, avg_macd_histogram=2.7872, avg_rsi_14=57.6786`
- Entry features on ETH 1h losers: `avg_ema_extension_pct=0.0037, avg_macd_histogram=2.9048, avg_rsi_14=56.4532`
- Exit reasons on ETH 1h winners: `ma_alignment_break=402, macd_rollover=28, trim_on_overbought_rsi=96`
- Exit reasons on ETH 1h losers: `ma_alignment_break=862, macd_rollover=8`
- Trade duration distribution: `0-4h=664, 4-24h=732`
- Regime contribution: `downtrend=$-637.13, sideways=$1,087.65, uptrend=$26,692.73`
- Founder question preserved: is the 1h pocket broad Money Flow behavior, or mostly one ETH window/sleeve pocket?

## 15m Losing Anatomy

- Trade count across scenarios: `7660`
- Cost drag from fees/slippage: `$72,360.39`
- MA break exits: `6816`
- MACD rollover exits: `580`
- Average trade duration: `1.45h`
- Average win rate across runs: `22.72%`
- Worst trade group: `ETH sleeve_15m next_candle_close net=$-225.02 exit=ma_alignment_break; ETH sleeve_15m next_candle_close net=$-222.77 exit=ma_alignment_break; ETH sleeve_15m next_candle_close net=$-221.69 exit=ma_alignment_break; ETH sleeve_15m next_candle_close net=$-219.38 exit=ma_alignment_break; ETH sleeve_15m next_candle_close net=$-170.04 exit=ma_alignment_break`
- Whipsaw/chop proxy count: `7396`
- Main no-trade reason: `bearish_alignment`
- Interpretation: 15m weakness appears consistent with many trades, repeated cost drag, and frequent fast invalidation/chop exits. This is a diagnostic observation, not a rule change.

## 4h Losing Anatomy

- Trade count across scenarios: `1280`
- Cost drag from fees/slippage: `$12,713.79`
- MA break exits: `1156`
- MACD rollover exits: `80`
- Average trade duration: `22.80h`
- Average win rate across runs: `28.62%`
- Worst trade group: `SOL sleeve_4h next_candle_close net=$-583.30 exit=ma_alignment_break; SOL sleeve_4h next_candle_close net=$-581.13 exit=ma_alignment_break; SOL sleeve_4h next_candle_close net=$-579.87 exit=ma_alignment_break; SOL sleeve_4h next_candle_close net=$-577.67 exit=ma_alignment_break; SOL sleeve_4h next_candle_open net=$-528.14 exit=ma_alignment_break`
- Whipsaw/chop proxy count: `1236`
- Main no-trade reason: `bearish_alignment`
- Interpretation: 4h weakness appears consistent with sparse slower signals, larger adverse excursion, and late invalidation risk in the tested window. This is a diagnostic observation, not a rule change.

## Market-Structure Diagnostics

Definition: recent swing high/low use the prior `20` candles before entry. Support/resistance proximity is descriptive and not used by the strategy.

| Component | Trades With Context | Near Recent High | Near Recent Low | Breakout Context | Nearby Resistance | Median Distance To Swing High | Median Distance To Swing Low |
|---|---:|---:|---:|---:|---:|---:|---:|
| sleeve_15m | 7660 | 5522 | 978 | 1030 | 6160 | 0.28% | 0.98% |
| sleeve_1h | 4484 | 1392 | 60 | 596 | 2242 | 0.73% | 2.44% |
| sleeve_4h | 1280 | 90 | 0 | 84 | 218 | 1.68% | 5.72% |

## Rule-Change Hypotheses For Later Testing

| Hypothesis | Applies To | Reason | Expected Benefit | Risk | Prove / Disprove Metric |
|---|---|---|---|---|---|
| avoid entries too close to recent resistance | 15m and 4h continuation entries | diagnostics can show entries clustered near recent swing highs or nearby resistance | reduce whipsaw entries that have little room before resistance | may remove valid continuation trades in strong trends | net account PnL, trade count, win rate, MAE/MFE, and missed-run opportunity versus baseline |
| require higher-low context before pullback entries | BTC/SOL 1h and 15m pullback-style entries | current rules validate EMA/RSI/MACD but do not inspect local swing structure | favor constructive pullbacks over weak rebounds | adds lag and may over-filter ETH-like pockets | scenario-level dynamic ending equity, drawdown, and no-trade reason expansion |
| test ATR or recent-low risk invalidation | 4h and large-drawdown 1h trades | current exits wait for MA/trend/MACD deterioration and may react slowly | limit large adverse excursions | can stop out trades before recovery and increase churn | closed-trade drawdown, mark-to-market drawdown, worst trade, and net account PnL versus baseline |
| avoid 15m trades in sideways/choppy regimes | sleeve_15m | 15m evidence is negative across tested dynamic scenarios and likely pays repeated cost/chop drag | reduce high-frequency weak trades and cost exposure | regime labeling may be unstable and can remove valid early trend entries | fee/slippage cost drag, trade count, whipsaw exits, and dynamic ending equity |
| limit 4h entries when price is extended from EMA10/SMA20 | sleeve_4h | 4h signals may arrive late relative to the tested public window | reduce late trend entries and large drawdown trades | can under-participate in durable trends | entry extension distribution, trade duration, drawdown, and net account PnL |
| separate pullback entries from continuation entries in reporting and later tests | all components | current evidence stores successful entries under one passed-rule condition | identify whether one entry style carries most favorable excursion | requires added attribution before rule changes are justified | MFE/MAE, exit reasons, and scenario-level ending equity by entry style |

## Boundary Confirmation

- `changes_money_flow_rules`: `false`
- `optimizes_parameters`: `false`
- `creates_live_artifacts`: `false`
- `creates_paper_trading_artifacts`: `false`
- `creates_routing_artifacts`: `false`
- `calls_exchange_adapters`: `false`
- `calls_private_exchange_endpoints`: `false`
- `calls_signed_exchange_endpoints`: `false`
- `calls_exchange_order_endpoints`: `false`
- `market_structure_used_as_entry_filter`: `false`
- `regime_used_as_entry_filter`: `false`

## Next Diagnostic Work

- Controlled tests can later evaluate the hypotheses above, one change at a time.
- Paper-trading design remains deferred until the founder manually accepts a later scoped design phase.
- Live execution remains outside Strategy Validation.
