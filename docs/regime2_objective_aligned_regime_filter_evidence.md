# REGIME2 — Objective-Aligned Regime Filter (fix the criterion, hold the bars)

> RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA: this signal reduces downside exposure in broad downtrends; it does not predict returns and does not guarantee profit (the gated book gives up return in choppy markets - the whipsaw cost is reported, not hidden). Signal only - not an order, not trading advice; nothing here submits orders or enables any trading mode.

Research/tool only. No runtime, strategy-rule, order, testnet, live, or
production-approval change follows from this report.

## Verdict: `regime_filter_does_not_reduce_drawdown_oos`

- Reasons: `['walk_forward_drawdown_not_reduced_in_every_fold']`; qualifiers: `['risk_tool_not_alpha_no_profit_claim']`

## Pre-registration (fixed before selection ran)

- the selection criterion and all gates above were fixed in regime2.py and the Decision Log and committed to git BEFORE this selection ran; the search space is REGIME1's grid unwidened; both REGIME1 bars are held unchanged
- Criterion: train-only, objective-aligned: lowest gated train max drawdown (= largest train drawdown reduction vs the shared always-long book); configs within 2.0 percentage points of the best are ties broken by FEWEST train state flips (whipsaw penalty), then config_id; OOS is never seen by selection
- Gate: OOS max-drawdown reduction >= 30% vs always-long (REGIME1 bar, unchanged)
- Gate: drawdown reduced vs always-long in EVERY walk-forward fold (REGIME1 bar, unchanged; strictly stronger than 'the chop fold must not worsen')
- Gate: OOS Sharpe >= always-long OOS Sharpe (REGIME1 bar, unchanged)
- Gate: OOS total return >= always-long OOS total return - 25pp (return-retention tolerance, pre-stated)
- Gate: minimum OOS days (REGIME1 bar, unchanged)
- Gate: no-lookahead probe verified (REGIME1 bar, unchanged)

## Selection (train only)

- Chosen: `regime1_lb90_br6_btc_required_1d` (ties considered: ['regime1_lb90_br6_btc_required_1d'])

| Rank | Config | Train maxDD | Train flips |
| --- | --- | --- | --- |
| 1 | regime1_lb90_br6_btc_required_1d | 37.57617417% | 60 |
| 2 | regime1_lb30_br6_btc_vote_1d | 51.96869310% | 144 |
| 3 | regime1_lb30_br5_btc_vote_1d | 51.97044262% | 116 |
| 4 | regime1_lb30_br5_btc_required_1d | 55.53468757% | 110 |
| 5 | regime1_lb90_br6_btc_vote_1d | 57.31978479% | 62 |
| 6 | regime1_lb30_br6_btc_required_1d | 57.73272702% | 132 |
| 7 | regime1_lb60_br6_btc_required_1d | 59.28381494% | 87 |
| 8 | regime1_lb60_br6_btc_vote_1d | 60.15454110% | 85 |
| 9 | regime1_lb30_br4_btc_required_1d | 60.88860687% | 118 |
| 10 | regime1_lb30_br4_btc_vote_1d | 61.88330219% | 104 |

## Always-long vs regime-gated (chronological 70/30 OOS, post-friction)

| Book | OOS return | OOS Sharpe | OOS maxDD | OOS days |
| --- | --- | --- | --- | --- |
| always-long | -19.58917762% | 0.12876359 | 65.72945095% | 627 |
| regime-gated | 60.88548524% | 0.88117293 | 43.62073804% | 627 |

- **OOS max drawdown reduction: 33.63593122%** (bar: >= 30%, held from REGIME1)
- Train: always 3188.17804342% (maxDD 78.91726695%) vs gated 2772.64021378% (maxDD 37.57617417%)

## Walk-forward folds (incl. the REGIME1-failing chop fold, now a hard gate)

- fold_b_chop (`regime1_lb30_br5_btc_required_1d`): gated maxDD 45.62452325% vs always 39.39753615%; return 51.14496317% vs 174.67796677%
- fold_c (`regime1_lb90_br6_btc_required_1d`): gated maxDD 43.62073804% vs always 65.72945095%; return 35.93093599% vs -24.99149558%

## Fixed-config fold texture (NOT a verdict)

- NOT A VERDICT: the pre-registered fold gate judges the SELECTION PROCESS (per-fold train-only choice, REGIME1's method unchanged) and failed; this block shows the final chosen config's own fold windows for consumers and cannot rescue the verdict
- fold_b_chop (`regime1_lb90_br6_btc_required_1d` fixed): gated maxDD 28.23852064% vs always 39.39753615%; return 120.03267067% vs 174.67796677%
- fold_c (`regime1_lb90_br6_btc_required_1d` fixed): gated maxDD 43.62073804% vs always 65.72945095%; return 35.93093599% vs -24.99149558%

## Whipsaw cost (the honest fine print)

- OOS: 35 flips (20.37480064/yr), 371 risk-off days (0.59170654), 18 spells, 3 FALSE risk-offs giving up 49216.38505327 USDC; drawdown avoided -649432.61746459 USDC
- false risk-off spell = always-long gained during the spell (return given up); true risk-off = always-long lost (drawdown avoided). Reported, never hidden.

## vs REGIME1

`{"regime1_chosen": "regime1_lb30_br5_btc_vote_1d (train Sharpe criterion)", "regime1_verdict": "regime_filter_does_not_reduce_drawdown_oos", "regime1_oos_dd_reduction_pct": "29.76", "what_changed": "ONLY the selection criterion (objective-aligned, pre-registered); same grid, bars, books, methods"}`

## Current state (latest closed candles in the evidence window)

`{"state": "risk_off", "risk_on": false, "breadth": "0", "breadth_up_count": 0, "universe_size": 7, "btc_trend_up": false, "risk_score": "0", "config_id": "regime1_lb90_br6_btc_required_1d", "disclaimer": "RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA: this signal reduces downside exposure in broad downtrends; it does not predict returns and does not guarantee profit (the gated book gives up return in choppy markets - the whipsaw cost is reported, not hidden). Signal only - not an order, not trading advice; nothing here submits orders or enables any trading mode.", "as_of_close": "2026-06-11 00:00:00+00:00"}`

## Boundaries

Signal only — no orders, no private/signed endpoints, no testnet/live, no
approval surface, no runtime change. Drawdown control, not alpha: the
filter reduces downside exposure; it does not predict returns and must
never be read as a profit claim.
