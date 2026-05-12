# SOR-EV2.2 Variant Chart Overlay

## Summary

`SOR-EV2.2` adds a dashboard Evidence Lab chart-overlay workflow for founder review of baseline versus SOR-EV1/SOR-EV2 variant behavior.

Status: `implemented`

This phase is UI/visualization only. It does not change Money Flow production rules, approve variants, submit orders, call private/signed/order endpoints, use Hyperliquid testnet prices as strategy truth, add live trading, add paper runtime, add SOR/fanout/CBBO/cross-venue routing, regenerate canonical evidence packs, or treat dashboard date filters as canonical evidence.

## Input Bundles Loaded

Status: `verified`

- `docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json`
- `docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json`
- `reports/strategy_validation/sv2_0_2_dashboard_chart_data/20260512T064916Z/*.json`

The SV2.0.2 chart-data JSON is used only for visualization context. Canonical baseline remains SV2.0.2 DB-imported evidence at timestamp `20260512T064916Z`.

## Overlay Controls

Status: `implemented`

Evidence Lab now includes overlay controls for:

- symbol
- timeframe
- fill assumption
- variant
- baseline / variant / both mode
- large-loss trades
- stop/context exits
- late-extension entries
- adverse candles
- MA/SMA break context

Default mode is baseline plus selected variant context.

## Baseline Markers

Status: `implemented`

Baseline markers render from SV2.0.2 chart/trade JSON:

- baseline entry: green
- baseline exit: red
- baseline forced close: yellow

Markers are labeled as canonical-baseline visualization context, not live trades and not testnet orders.

## Variant Markers

Status: `implemented`

Where the SOR-EV2 bundle contains linkable timestamps, the overlay renders variant/context markers:

- stop/adverse-candle context: orange
- late-extension entry context: blue
- adverse candle diagnostic context: purple/gray

Status: `needs_followup`

SOR-EV2 does not provide full per-trade variant marker streams for every variant. When exact timestamps are missing, the dashboard shows `exact_overlay_unavailable_from_sor_ev_bundle` instead of guessing.

## Worst-Trade Focus Mode

Status: `implemented`

The Evidence Lab overlay includes a Worst Trades Focus table. Selecting a trade updates the overlay symbol/timeframe/fill, highlights the selected baseline entry/exit window, and updates the side inspector.

The inspector shows rank, symbol, timeframe, fill assumption, entry classification, net PnL, max adverse excursion, large red candle status, stop-helped/hurt context when available, current exit reason, selected variant result, methodology, and candidate/diagnostic warning.

## Control-Pocket View

Status: `implemented`

The selected variant view summarizes:

- ETH 1h control pocket
- positive 1D pockets
- other positive baseline pockets
- preserved / improved / damaged status
- drawdown and return impact
- trade-count impact
- candidate/rejected reasoning

## Unavailable Overlay Data

Status: `verified`

Missing SOR-EV fields render as `data_not_available_in_sor_ev_bundle`.

Exact marker data that the bundles do not contain renders as `exact_overlay_unavailable_from_sor_ev_bundle`.

Non-true-forward methodologies render `diagnostic_only_not_candidate`.

The dashboard does not infer missing timestamps and does not silently show zero for missing evidence fields.

## Methodology Warnings

Status: `verified`

The overlay keeps the warning visible:

Only `true_forward_replay` variants can become candidates for deeper evidence. Completed-trade overlays and lookahead diagnostics are not production candidates. No variant is approved for production, paper runtime, or live trading.

## Date-Filter Warning

Status: `verified`

Evidence Lab keeps the date-filter boundary visible:

Dashboard date filters are display-only recalculations from loaded trades. They do not regenerate canonical evidence packs. Exact arbitrary-date canonical evidence requires a backend Strategy Validation run.

## Limitations

Status: `needs_followup`

- SOR-EV2 aggregate variant rows do not contain full variant trade-marker streams.
- MA/SMA break rows include boolean/context flags but not exact break timestamps for every trade.
- Some variant overlays are therefore side-panel/context markers, not full alternative trade paths.
- A future SOR-EV2.3 or SOR-EV3 can generate dedicated per-variant chart-marker exports if founder review requires exact alternate entry/exit paths.

## Next Recommended Phase

Status: `deferred`

If founder review identifies a narrow variant worth deeper work, run a separately scoped evidence phase that generates backend canonical Strategy Validation outputs or explicit variant marker exports. Do not use dashboard overlays or date-filter recalculations as canonical evidence.
