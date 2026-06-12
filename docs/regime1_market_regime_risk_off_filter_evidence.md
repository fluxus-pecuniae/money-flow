# REGIME1 — Market-Regime Risk-Off Filter (when NOT to be long)

> RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA: this signal reduces downside exposure in broad downtrends; it does not predict returns and does not guarantee profit (the gated book gives up return in choppy markets - the whipsaw cost is reported, not hidden). Signal only - not an order, not trading advice; nothing here submits orders or enables any trading mode.

Research/tool only. No runtime, strategy-rule, order, testnet, live, or
production-approval change follows from this report.

## Verdict: `regime_filter_does_not_reduce_drawdown_oos`

- Semantics: risk-tool pass: material OOS drawdown reduction at not-worse risk-adjusted performance — explicitly NOT an alpha claim
- Reasons: `['oos_drawdown_not_materially_reduced', 'walk_forward_drawdown_not_reduced_in_every_fold']`; qualifiers: `['risk_tool_not_alpha_no_profit_claim']`

## The rule

- per-asset tsmom_ev1.tsmom_signal trailing-return sign (reused, not re-derived); breadth = fraction of assets trend-up; risk_on iff breadth >= threshold AND (btc_rule == vote OR BTC trend up); graded risk_score = breadth (display only)
- Grid: lookbacks [30, 60, 90] x thresholds ['0.4', '0.5', '0.6'] x btc rules ['vote', 'required'] = 18 configs; train-only choice: `regime1_lb30_br5_btc_vote_1d`
- Book: equal-weight long book, 7d rebalance, EXEC-EV1 exec_ev1_conservative friction; window 2020-09-24 00:00:00+00:00 .. 2026-06-11 00:00:00+00:00 (2087 days)

## Always-long vs regime-gated (chronological 70/30 OOS, post-friction)

| Book | OOS return | OOS Sharpe | OOS maxDD | OOS days |
| --- | --- | --- | --- | --- |
| always-long | -19.58917762% | 0.12876359 | 65.72945095% | 627 |
| regime-gated | 25.95265912% | 0.52779250 | 46.16733474% | 627 |

- **OOS max drawdown reduction: 29.76156947%** (material bar: >= 30.00% relative)
- Train: always 3188.17804342% (maxDD 78.91726695%) vs gated 7244.08816859% (maxDD 51.97044262%)

## Walk-forward folds (drawdown gated vs always-long)

- fold_b (`regime1_lb30_br5_btc_vote_1d`): gated maxDD 45.62506528% vs always 39.39753615%; Sharpe 0.66170696 vs 1.17122609; return 45.96633280% vs 174.67796677%
- fold_c (`regime1_lb30_br5_btc_vote_1d`): gated maxDD 46.16733474% vs always 65.72945095%; Sharpe 0.52243701 vs 0.08700266; return 28.22501620% vs -24.99149558%

## Whipsaw cost (the honest fine print)

- OOS: 58 flips (33.76395534/yr), 331 risk-off days (0.52791069), 30 spells (mean 11.03333333d), 6 FALSE risk-offs giving up 120295.13580432 USDC; drawdown avoided in true risk-offs -1005464.36288682 USDC
- Full window: 175 flips, 21/88 false spells, given up 206362.85918466 vs avoided -1907172.68591172 USDC
- false risk-off spell = always-long gained during the spell (return given up); true risk-off = always-long lost (drawdown avoided). Reported, never hidden.

## Hindsight texture (NOT a verdict)

- NOT A VERDICT: surfaced for honesty only; the committed choice criterion is train Sharpe and was not re-decided
- Best OOS-drawdown config in hindsight: `regime1_lb60_br6_btc_required_1d` (OOS maxDD 33.30603446%)
- An alternative pre-committed criterion (min train drawdown) would have chosen `regime1_lb90_br6_btc_required_1d` — surfaced because the gap between criteria is itself a finding about regime-filter fragility

## Current state (latest closed candles in the evidence window)

`{"state": "risk_off", "risk_on": false, "breadth": "0", "breadth_up_count": 0, "universe_size": 7, "btc_trend_up": false, "risk_score": "0", "config_id": "regime1_lb30_br5_btc_vote_1d", "disclaimer": "RISK-OFF FILTER / DRAWDOWN CONTROL, NOT ALPHA: this signal reduces downside exposure in broad downtrends; it does not predict returns and does not guarantee profit (the gated book gives up return in choppy markets - the whipsaw cost is reported, not hidden). Signal only - not an order, not trading advice; nothing here submits orders or enables any trading mode.", "as_of_close": "2026-06-11 00:00:00+00:00"}`

## Reusable gate

- strategy_types.REGIME_FILTER_REF -> regime1.build_regime_gate(datasets) -> RegimeGate.is_risk_on(as_of)
- Default pinned to the train-only choice: `regime1_lb30_br5_btc_vote_1d` (re-tuning without new evidence fails CI)
- Intended use: suppress LONG entries while risk_off (drawdown control for long books; MONEYFLOW-SIGNAL1 and future per-asset strategies)

## Boundaries

Signal only — no orders, no private/signed endpoints, no testnet/live, no
approval surface, no runtime change. The filter reduces downside exposure;
it does not predict returns and must never be read as a profit claim.
