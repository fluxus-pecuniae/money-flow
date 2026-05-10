# Money Flow Evidence Dashboard

Static local dashboard for founder/operator review of Strategy Validation evidence packs.

Run it from the repo root so the dashboard can read ignored local evidence-pack JSON files:

```bash
.venv/bin/python -m http.server 8765
```

Then open:

```text
http://127.0.0.1:8765/apps/dashboard/index.html
```

The dashboard tries to load the current SV1.13.2 Hyperliquid dynamic-equity evidence review and component batch reports from `reports/strategy_validation*`. Those generated files stay ignored by Git and review bundles. If the files are not present, use the file picker in the dashboard to load `money_flow_evidence_review.json` and one or more `batch_report.json` files manually.

The `Experiments` tab shows the committed SV1.15/SV1.15.1 controlled hypothesis results from `docs/strategy_validation_sv1_15_hypothesis_experiments.md`, including baseline dynamic-equity sums, one-change variant deltas, ETH 1h preservation, methodology classifications, the recent-low lookahead-proxy downgrade, and lower-RSI attribution caveats. These are research-only diagnostics and no variant is authorized for production, paper trading, or live trading.

The `Experiments` tab also has a replay filter. Use `SV1.15 overlays` for the completed-trade overlay diagnostics, `SV1.16 true replay` for the rejected-signal replay result from `docs/strategy_validation_sv1_16_rejected_signal_replay.md`, `SV1.17 replay round 1` for the initial ETH 1h lower-RSI slice, and `SV1.17 full suite` for BTC/ETH/SOL across 15m/1h/4h from `docs/strategy_validation_sv1_17_true_replay_experiments_summary.json`. Replay views show baseline versus research-only variants, replay-only entries, rejected-entry counts, ending equity, drawdown, and methodology boundaries. They remain research-only and are not mixed into the Evidence tab.

The `UAT2 Shadow Run` tab loads `docs/uat2_shadow_strategy_top20_observation_summary.json` by default when served from the repo root. It shows UAT2 summary cards, a filterable 45-record signal matrix, would-open records, no-trade reason breakdowns, the ETH `sleeve_1h` evidence-candidate card, `next_candle_open` / `next_candle_close` timing status, the `same_candle_close_research_only` research-only boundary, shadow drawdown labeled not-live-account, no-artifact boundary flags, the blocked UAT3 readiness checklist, and the UAT3.0/UAT3.0.1 sandbox-design/readiness panel. It is a visualization and founder-review surface only; it adds no approval action and cannot enable orders.

The UAT3.0/UAT3.0.1 panel is informational. It shows that the future initial sandbox subset is Hyperliquid ETH USDC perpetual `sleeve_1h`, actual sandbox order submission is not approved, founder/operator approval is required for any later UAT3.1 submission, sandbox runtime policy and fixture validators exist, sandbox account drawdown is fixture-only / missing live sandbox feed, and submit/risk/approval wiring is still required. It has no active order submission button.

The `Strategy` tab visualizes the current Money Flow v1.1 rule flow from `services/strategy/money_flow.py`, including readiness gates, entry checks, position-management checks, sleeve thresholds, confidence scoring, RSI lower-floor truth, and the SV1.14 market-structure diagnostics boundary. It is a visual overview only and does not change strategy logic. Component cards show sums across research runs, and run rows are scenario results rather than one combined account.

This is a visualization surface only. It does not run Strategy Validation, generate evidence packs, import candles, call exchange endpoints, create approvals, submit orders, approve paper trading, approve live trading, or change Money Flow rules.
