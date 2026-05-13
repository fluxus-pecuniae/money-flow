# Original Money Flow Source Notes

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

Primary source: `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf`

The PDF is now present in the Obsidian reference tree. These notes summarize source concepts for evidence architecture and the source-faithful reconstruction track. They do not approve a strategy.

## Source System Summary

| Area | Source Concept | Evidence Translation Status |
| --- | --- | --- |
| Four stages | Stage 1 basing/sideways, Stage 2 markup/uptrend, Stage 3 topping/distribution, Stage 4 markdown/decline | Modeled deterministically in MF-ORIG, but still an implementation assumption. |
| 5 EMA / 20 SMA | 5 EMA trigger crossing the 20 SMA is the basic buy/sell signal | Implemented in MF-ORIG hypotheses. |
| 10 EMA | Alignment/context for trend strength and deciding whether RSI overbought should be ignored | Partially represented as context. |
| 20 SMA | Foundation/stage line; price above/below it defines bullish/bearish context | Core MF-ORIG rule. |
| 50 / 200 SMA | Longer-term support/resistance and context | Documented; not fully modeled as hard rule in first-pass MF-ORIG. |
| RSI 14 | Profit-taking/extreme warning; >70 warns to lock profits, <30 is investor/add context | MF-ORIG records profit warnings; trim requires additional context and is not a high-RSI-only full exit. |
| MACD / TSI | Confirmation/warning; MACD can substitute for TSI | MACD used because TSI remains deferred. |
| ADX/DMI | Helps identify no-trend Stage 1 / sideways conditions | Documented; not core production v1.2 rule. |
| Support/resistance | Supply/demand zones, prior highs/lows, range breakouts | Simplified deterministic proxies in MF-ORIG. |
| Pivots/stops | Stops should be structure-based rather than arbitrary fixed percent | MF-ORIG uses prior support/pivot proxies. |
| Position sizing | Ideally risk 1% or less of account balance per trade | Source-faithful MF-ORIG rows use 1% risk sizing; full-equity rows are comparison-only. |
| Timeframe | Book uses daily examples and says system is fractal | MF-ORIG labels `1d` source-primary, 4h/1h fractal adaptations, 15m stress-test. |

## Difference From Current Money Flow v1.2

Current Money Flow v1.2 is a derivative implementation:

- Uses EMA5 > EMA10 > SMA20 stack.
- Uses RSI sleeve bands as entry gates.
- Uses MACD constructive entry gates.
- Uses entry quality and invalidation reason codes.
- Uses current Strategy Validation dynamic-equity evidence.

Original Money Flow source hierarchy is different:

- Stages first.
- 20 SMA foundation line.
- 5 EMA trigger against 20 SMA.
- MACD/TSI confirmation or warning.
- RSI as profit-taking/extreme context, not a narrow entry sleeve.
- Support/resistance and pivots for risk structure.
- Risk-based position sizing.

## MF-ORIG Current Outcome

MF-ORIG-EV1.1 fixed accounting and drawdown. MF-ORIG-EV2 broadened the evidence across all supported SV2.0.2 symbols/timeframes and added full-equity comparison lanes.

No MF-ORIG hypothesis is production-approved. Source-faithful rows remain evidence-only and require deeper source/legal/implementation review before any later rule proposal.
