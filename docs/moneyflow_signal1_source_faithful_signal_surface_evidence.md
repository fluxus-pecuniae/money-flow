# MONEYFLOW-SIGNAL1 — Source-Faithful Money Flow Signal Surface (Evidence)

> SOURCE-FAITHFUL SIGNAL, NOT ALPHA: a faithful implementation of the documented Gerald Peters Money Flow Trading System, characterized honestly - the directional rules showed no standalone edge out-of-sample and this surface re-confirms that as characterization, not a profit claim. The regime overlay is informational risk context, not a validated control. Signal only - not an order, not trading advice; nothing here submits orders, enables any trading mode, or predicts or guarantees profit.

- `generated_at_utc`: `2026-06-12T12:00:00Z`
- `status`: `source_faithful_signal_surface_delivered_characterized_honestly`
- `standalone_characterization`: `defensive_trend_mechanic_not_validated_alpha`
- `regime_overlay`: informational risk context, not a validated control (committed REGIME2 verdict: honest FAIL - endpoint-strong, process-unstable)

## Source Document (the PDF, read directly this phase)

- `The Money Flow Trading System` — Gerald Peters, September 5, 2019 Edition #2
- repo path: `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf`
- sha256: `200c83feebc1c8d095ed4dce6f82afe0bc586ccdaaf2083c304b493e4296a616` (159 PDF pages)
- provenance check: present=`True`, sha256 match=`True`
- MF-ORIG-EV1 recorded direct_pdf_available_to_agent=false and worked from a prompt-supplied source summary; MONEYFLOW-SIGNAL1 located the PDF in the repo, read it directly, and verified every reused rule against the printed text - citations below quote the source.

## The Documented Rules (page-cited) and Their Implementation

| Rule | Printed page | Implementation |
| --- | --- | --- |
| `checklist_indicators` | 10 | indicator set is exactly EMA5, EMA10, SMA20, RSI14, MACD(12,26,9) via services.indicators.service (the production implementations); every value is emitted on the signal surface |
| `foundation_5_20_crossover` | 37 | basic_signal: 'buy' on EMA5 crossing above SMA20, 'sell' on EMA5 crossing below SMA20 (mf_orig_ev1._crossed_above/_crossed_below, reused unchanged) |
| `sma20_trend_and_stage_line` | 30-31, 36 | close_vs_sma20 emitted on every state; the stage classifier keys on close versus SMA20 (mf_orig_ev1._classify_stage, reused) |
| `macd_equals_tsi` | 70, 72 | MACD(12,26,9) is used for confirmation/warning - now SOURCE-CONFIRMED (the PDF itself authorizes MACD in place of TSI), upgrading MF-ORIG-EV1's 'tsi_deferred_macd_substitute' limitation |
| `stage2_breakout_entry` | 146 | source_entry_signal = mf_orig_ev1._entry_signal('mf_orig_1d_stage2_5_20_crossover'): Stage 2 active, close above SMA20, EMA5 crosses above SMA20, MACD bullish or improving, RSI below the extreme-overbought block |
| `stage3_warning_and_quarter_trim` | 150 | rsi_profit_warning (RSI14 > 70) and macd_sell_crossover (bearish signal-line cross while EMA5 > SMA20) are emitted as separate auditable flags; trim_context_25pct marks the documented quarter-trim context (the trade-level 25% trim itself lives in the reused MF-ORIG engine) |
| `full_exit_rule` | 150, 152 | exit_signal: ema5_cross_below_sma20_exit or price_close_below_sma20_exit - the same two conditions mf_orig_ev1._original_exit_reason closes on |
| `rsi_rules` | 127, 140 | rsi_profit_warning above 70; rsi_ignore_active when the EMA5 > EMA10 > SMA20 stack holds (the p.140 override) - both emitted, neither hidden inside the other |
| `structure_stops_not_fixed_pct` | 115, 118 | trade-level lane only (reused MF-ORIG engine: prior-10-candle support low / confirmed pivot-low proxy); the signal surface emits the current structure-stop reference for audit |
| `position_sizing_1pct_risk` | 125 | trade-level lane only (reused MF-ORIG engine sizes risk budget at 1% of realized equity over stop distance); not part of the signal state itself |
| `daily_timeframe_fractal` | 142 | the signal surface computes on closed DAILY candles only |
| `stage1_whipsaw_warning` | 143 | the stage classifier's whipsaw/low-progress branch labels Stage 1; the emitted stage gives the founder the documented whipsaw warning context |
| `trend_following_frame` | 3 | framing only - the system is trend-following by construction; no extra code rule |

Quotes are recorded verbatim in the summary JSON (`source_citations[*].quote`).

## Recorded Interpretation Choices (never silently picked)

- `indicator_formula_conventions`: use the repo's production indicator implementations (services/indicators/service.py): SMA-seeded EMA with multiplier 2/(n+1), Wilder-smoothed RSI(14), MACD(12,26,9) with EMA(9) signal - the same StockCharts-documented conventions; fidelity tests pin the arithmetic with hand-computed fixtures
- `stage_classification_is_narrative`: reuse MF-ORIG-EV1's deterministic no-lookahead stage proxy unchanged (_classify_stage: close vs SMA20 + 5/20 crosses + whipsaw count + RSI/MACD warnings + prior stage)
- `trim_trigger_conjunction`: the signal surface emits rsi_profit_warning and macd_sell_crossover as SEPARATE flags plus trim_context_25pct for the p.150 MACD-while-5-above-20 condition; the reused MF-ORIG trade engine keeps its stricter conjunction (RSI>70 AND MACD bearish cross while profitable) - both readings are visible, nothing is silently chosen
- `entry_confirmation_set`: both are emitted: basic_signal (pure p.37 crossover) and source_entry_signal (MF-ORIG primary hypothesis: Stage 2 + close above SMA20 + crossover + MACD confirm + RSI<80 extreme block); the RSI>=80 entry block is an MF-ORIG interpretation (the PDF only says to IGNORE RSI 70+ when the MA stack is aligned, p.140) and is recorded as such
- `structure_stop_proxy`: reuse MF-ORIG's deterministic proxy: min(prior-10-candle support low, last confirmed 2/2 pivot low before the signal candle); the signal surface emits the reference value for audit only
- `characterization_scope_exposure_only`: the MONEYFLOW-SIGNAL1 characterization books model the signal's long/flat EXPOSURE (entry/exit rules) through the EXEC-EV1 friction simulator; structure stops, 25% trims, and 1%-risk sizing are trade-level mechanics already characterized honestly in MF-ORIG-EV1.1/EV2 (no standalone edge) and are not re-modeled at book level

## Honest Standalone Characterization (expected no-edge; reported straight)

- methodology: long/flat exposure of the signal at equal weight through tsmom_ev1.simulate_tsmom_portfolio (decisions at each aligned close, fills at next open, EXEC-EV1 friction); friction `exec_ev1_conservative`
- window: 2087 aligned days, warmed start `2020-12-23 00:00:00+00:00`, 70/30 split `2024-09-22 00:00:00+00:00`
- scope: the MONEYFLOW-SIGNAL1 characterization books model the signal's long/flat EXPOSURE (entry/exit rules) through the EXEC-EV1 friction simulator; structure stops, 25% trims, and 1%-risk sizing are trade-level mechanics already characterized honestly in MF-ORIG-EV1.1/EV2 (no standalone edge) and are not re-modeled at book level

| Book | OOS Sharpe | OOS max DD % | OOS return % | Flips |
| --- | --- | --- | --- | --- |
| `mf_source_stage2` | 0.71024840 | 27.02095320 | 31.57146190 | 804 |
| `mf_basic_5_20` | 0.70539233 | 27.59979127 | 31.55578256 | 818 |
| `mf_source_stage2_regime_gated` | 0.70014325 | 25.50704395 | 25.39471896 | 554 |
| `mf_basic_5_20_regime_gated` | 0.66176218 | 25.52067258 | 23.77219928 | 560 |
| `always_long` | 0.12359247 | 65.32596949 | -19.77179961 | 7 |
| `benchmark_buy_hold` | 0.04954653 | 72.25089323 | -31.44345790 | — |

- coin-flip randoms (30 seeds; churn-unfair, kept for transparency): OOS Sharpe median -0.76206806, p95 -0.34213204
- persistence-matched randoms (the fair bar; p_enter 0.03654213253340605399509135533, p_exit 0.08281829419035846724351050680): OOS Sharpe median 0.08509632, p95 0.60003397; Money Flow percentile vs matched: 0.9333333333333333333333333333
- stage-1 raw screens: beats buy-and-hold OOS `True`, beats coin-flip p95 `True` — re-audit fired: `True`
- stage-2 re-audit: beats persistence-matched p95 `True`; rising third `first_third` return MF 403.76379188% vs always-long 1134.74495311% (return-prediction signature: `False`)
- committed context: a 5/20 MA long/flat book clearing the relative bar on this universe is the KNOWN defensive trend mechanic on a refreshed window, not a new discovery; the absolute sign of OOS return is window placement (TSMOM-EV1's OOS was a -62% bear and absolutely negative)
- **defensive_trend_mechanic_not_validated_alpha** — the long/flat exits avoid the bear windows (OOS drawdown 27% vs buy-and-hold 72%) while giving up most of the rising third's return - drawdown-avoidance, exactly the committed TSMOM-EV1/TREND-SUITE1/REGIME texture on this universe; single window, window-dependent, NOT validated alpha, and ~p95 against only 30 matched randoms is no multiplicity-aware significance claim; the trade-level namesake result (source_faithful_but_underperformed) stands

### Sub-window texture (thirds of the aligned timeline)

| Book | First third Sharpe / return % | Middle third Sharpe / return % | Final third Sharpe / return % |
| --- | --- | --- | --- |
| `mf_source_stage2` | 2.33876585 / 403.76379188 | 1.29490622 / 94.89860136 | 0.60229912 / 28.02186878 |
| `always_long` | 1.91978110 / 1134.74495311 | 1.14118634 / 164.46251814 | 0.08072726 / -25.25860033 |
| `benchmark_buy_hold` | 1.51128338 / 610.10596296 | 1.00374513 / 136.74508381 | -0.00123446 / -38.08361864 |

## Money Flow Alone vs Regime-Gated (informational overlay, not a validated control)

- regime config: `regime1_lb90_br6_btc_required_1d`; committed verdict: `regime_filter_does_not_reduce_drawdown_oos`
- verdict note: evidence verdict (REGIME2, pre-registered): regime_filter_does_not_reduce_drawdown_oos — the deployed config cleared every endpoint bar (33.6% OOS drawdown reduction; Sharpe 0.88 vs 0.13; reduces drawdown in both fold windows held fixed) but the pre-registered selection process failed walk-forward stability at the early-history cutoff; the emitted state is informational risk context, not a validated control
- risk-off days: 1150 of 1997 regime-series days

| Base book | OOS DD % ungated | OOS DD % gated | DD reduction (% of ungated) | OOS return ungated % | OOS return gated % | Extra flips |
| --- | --- | --- | --- | --- | --- | --- |
| `mf_source_stage2` | 27.02095320 | 25.50704395 | 5.602723333979202480540175763 | 31.57146190 | 25.39471896 | -250 |
| `mf_basic_5_20` | 27.59979127 | 25.52067258 | 7.533095702284997751723939034 | 31.55578256 | 23.77219928 | -258 |

## Limitations

- equal_weight_long_only_books
- exposure_books_do_not_model_structure_stops_trims_or_1pct_sizing (trade-level lane characterized in MF-ORIG-EV1.1/EV2)
- random_benchmarks_are_seeded_coin_flip_and_persistence_matched_long_flat
- regime_overlay_carries_its_honest_fail_verdict_everywhere
- seven_major_perp_universe_only
- single_venue_binance_perp_daily_candles
- single_window_result_window_dependent (the OOS tail is a deep bear; long/flat exit rules are mechanically flattered there)

## Boundaries

- `approves_live_trading`: `False`
- `approves_paper_trading`: `False`
- `calls_private_signed_or_order_endpoints`: `False`
- `changes_production_money_flow_rules`: `False`
- `changes_runtime_behavior`: `False`
- `enables_any_trading_mode`: `False`
- `is_alpha_claim`: `False`
- `predicts_or_guarantees_profit`: `False`
- `regime_overlay_is_informational_risk_context`: `True`
- `regime_overlay_is_validated_control`: `False`
- `signal_only`: `True`
- `standalone_edge_claim`: `False`
- `submits_orders`: `False`
- `uses_api_keys`: `False`

> SOURCE-FAITHFUL SIGNAL, NOT ALPHA: a faithful implementation of the documented Gerald Peters Money Flow Trading System, characterized honestly - the directional rules showed no standalone edge out-of-sample and this surface re-confirms that as characterization, not a profit claim. The regime overlay is informational risk context, not a validated control. Signal only - not an order, not trading advice; nothing here submits orders, enables any trading mode, or predicts or guarantees profit.
