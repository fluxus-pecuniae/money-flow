# MF-ORIG-EV1 Original Money Flow Spec And Gap Matrix

## Source Document

- `title`: `The Money Flow Trading System`
- `author`: `Gerald Peters`
- `edition`: `September 5, 2019 Edition #2`
- `source_basis`: `prompt_provided_source_truth_summary`
- `direct_pdf_available_to_agent`: `false`

The PDF was not present in the repository or common local paths during this implementation. MF-ORIG-EV1 therefore records the prompt-provided source-truth summary as the source basis and marks subjective translations explicitly.

## Source Rule Extraction

| Section | Source Rule | Evidence Translation | Assumption Status |
| --- | --- | --- | --- |
| Four Stages | Stage 1 accumulation/sideways is whipsaw risk; Stage 2 markup is the primary long regime; Stage 3 distribution warns of topping; Stage 4 markdown is decline. | Classify stages deterministically from prior/current candles using close versus SMA20, EMA5/SMA20 crosses, whipsaw/range behavior, RSI/MACD warnings, and prior stage state. | `implemented_with_objective_no_lookahead_proxy` |
| Moving Averages | 5 EMA / 20 SMA crossover is the basic buy/sell signal; 10 EMA is trend/alignment context; 20 SMA is the foundation/stage line; 50/200 SMA are respected context. | Primary entries require close above SMA20 plus EMA5 crossing above SMA20 or a pullback/reclaim within Stage 2. Full exits use EMA5 cross below SMA20 or price close below SMA20. | `implemented` |
| TSI / MACD | TSI or MACD confirms trend and warns when profitable positions weaken. | TSI is deferred; MACD 12/26/9 is used as the accepted substitute. Bullish crossover or improving histogram confirms entries; bearish crossover while profitable trims 25%. | `tsi_deferred_macd_substitute_implemented` |
| RSI / Profit Taking | RSI > 70 is profit-taking/warning context, not necessarily a full exit. | RSI above 70 records profit warnings; when paired with bearish MACD while profitable, one 25% trim is applied. RSI high alone does not close the trade. | `implemented` |
| Support / Resistance / Pivots / Stops | Stops belong near logical support/resistance or pivots, not arbitrary fixed percent. | Use prior completed-candle support/pivot proxy: recent support low from the prior 10 candles, with optional confirmed pivot low when available before entry. | `implemented_simple_no_lookahead_proxy` |
| Position Sizing | Position sizing is based on defined risk, ideally 1% or less of current account equity per trade. | Risk budget is 1% of current realized equity. Size is risk budget divided by entry-stop distance with 100% equity notional cap. | `implemented` |
| Timeframe Adaptation | The book uses daily charts while describing the system as fractal. | Treat 1d as primary, 4h as secondary context, 1h as exploratory timing, and exclude 15m from original-source conclusions. | `implemented` |

## Gap Matrix

| Original PDF Rule | Current Money Flow v1.2 Behavior | Gap / Drift | Evidence Implication | Reconstruction |
| --- | --- | --- | --- | --- |
| Stage/20SMA/5EMA trigger hierarchy comes first. | EMA5 > EMA10 > SMA20 stack, RSI sleeve, MACD constructive gate, and pullback/continuation quality are primary. | Current v1.2 is Money Flow-inspired but not source-faithful; it treats RSI/MACD as entry gates rather than secondary warning/confirmation context. | MF-ORIG-EV1 must compare a 1d-first stage/crossover system against v1.2, not overwrite v1.2. | mf_orig_1d_stage2_5_20_crossover plus source-style exits/trims/stops/sizing. |
| RSI > 70 is profit-warning/profit-taking context. | RSI sleeve floors/ceilings act as entry eligibility gates and trim thresholds. | RSI has moved from warning context to entry filter. | Original hypotheses should not reject entries solely because RSI is below a v1.2 sleeve floor. | Only block extreme-overbought entries and use RSI > 70 as warning/trim context. |
| Full exit is 5 EMA crossing/closing below 20 SMA or price close below 20 SMA. | MA break plus MACD rollover can close/reduce under sleeve-specific logic. | Current exits can be more MACD-sensitive than the source hierarchy. | Original replay must separate full exits from profit-warning trims. | Full exits on EMA5/SMA20 bear cross or price below SMA20; MACD bearish while profitable trims. |
| Stops are placed around support/resistance or pivots and risk is sized from stop distance. | Canonical evidence primarily uses position_notional_pct dynamic equity and no source-structure stop model. | Current evidence does not model source-style structure stops or 1% risk sizing. | MF-ORIG-EV1 should test risk-budget sizing and prior support/pivot stops explicitly. | Risk 1% of realized equity, cap notional at current equity, and use prior support low/pivot proxy. |

## Required Boundaries

- MF-ORIG-EV1 is evidence-only.
- Current Money Flow v1.2 production rules remain unchanged.
- Original Money Flow is not production approved.
- No paper/live approval follows from MF-ORIG-EV1.
- Testnet execution is separate from strategy evidence.
- Dashboard date filters are display-only and not canonical evidence.
