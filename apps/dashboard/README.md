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

The `Experiments` tab shows the committed SV1.15 controlled hypothesis results from `docs/strategy_validation_sv1_15_hypothesis_experiments.md`, including baseline dynamic-equity sums, one-change variant deltas, ETH 1h preservation, and lower-RSI attribution caveats. These are research-only diagnostics and no variant is authorized for production, paper trading, or live trading.

The `Strategy` tab visualizes the current Money Flow v1.1 rule flow from `services/strategy/money_flow.py`, including readiness gates, entry checks, position-management checks, sleeve thresholds, confidence scoring, RSI lower-floor truth, and the SV1.14 market-structure diagnostics boundary. It is a visual overview only and does not change strategy logic. Component cards show sums across research runs, and run rows are scenario results rather than one combined account.

This is a visualization surface only. It does not run Strategy Validation, generate evidence packs, import candles, call exchange endpoints, approve paper trading, or change Money Flow rules.
