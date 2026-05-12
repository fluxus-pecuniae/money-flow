# SOR-EV2.1 Evidence Lab UI

## Summary

Status: implemented

SOR-EV2.1 adds a dashboard Evidence Lab / Variant Review tab for founder review of SOR-EV1 and SOR-EV2 research bundles.

This phase is UI/visualization only. It does not change Money Flow production rules, does not approve variants, does not submit orders, and does not regenerate canonical evidence.

## Scope

Status: implemented

- Added a visible `Evidence Lab` dashboard tab after `Evidence`.
- Loads committed SOR-EV1 and SOR-EV2 summary JSON bundles when present.
- Uses canonical SV2.0.2 DB-imported evidence as the baseline label.
- Shows variants as evidence-only with methodology and rejection/candidate taxonomy.
- Keeps dashboard date filters labeled as display-only recalculations, not canonical evidence generation.

## Non-Goals

Status: verified

- No production Money Flow rule changed.
- No variant was approved for production, paper runtime, or live trading.
- No orders were submitted.
- No private, signed, or order endpoints were added.
- Hyperliquid testnet prices are not used as strategy truth.
- No SOR, fanout, CBBO, cross-venue routing, or route executor behavior was added.

## Input Files Loaded

Status: implemented

- `docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json`
- `docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json`

Chart-data JSON under `reports/strategy_validation/sv2_0_2_dashboard_chart_data/20260512T064916Z/` remains visualization context only and is not canonical evidence.

## Dashboard Sections

Status: implemented

- Evidence Lab header with canonical baseline, evidence-only, no-rule-change, no-live, and no-order badges.
- Variant Summary Matrix with founder-review labels for promising, mixed, deferred, no-op, diagnostic-only, and hard-rejected outcomes.
- Control Pockets panel.
- Worst Trades panel.
- Late Entry Analysis panel.
- Large Adverse Candle Analysis panel.
- RSI / MACD Rejections panel.
- Variant Chart Overlay placeholder.

## Variant Matrix

Status: implemented

The matrix shows variant id, family, methodology, founder-review label, outcome taxonomy, tested/candidate flags, review status, hard-rejected status, ending-equity delta, drawdown delta, trade-count delta, control-pocket impact, and gate blockers. The labels are review aids only; no SOR-EV1/SOR-EV2 variant is approved for production.

Missing bundle fields render as `data_not_available_in_sor_ev_bundle` instead of silent zeroes.

## Worst Trades Panel

Status: implemented

Worst trades from SOR-EV1 are shown with symbol, timeframe, fill assumption, entry/exit times, PnL, equity before/after, entry classification, exit reason, large adverse candle classification, and max adverse excursion.

## Control Pocket Panel

Status: implemented

Control-pocket impact from SOR-EV2 is shown for each variant so the founder can see whether a rule preserved, improved, or damaged strong baseline pockets such as ETH 1h and positive 1d pockets.

## RSI / MACD Rejection Panel

Status: implemented

The panel shows rejection categories and variant admission counts when available. Missing good/bad admitted trade detail is labeled as unavailable instead of inferred.

## Large Adverse Candle Panel

Status: implemented

The panel summarizes large adverse-candle context from SOR-EV2 and SOR-EV1, including late exits, stop-helped counts, recent-low context, and stop-hurt/unavailable fields where the bundle lacks exact detail.

## Chart Overlay

Status: superseded_by_sor_ev2_2

SOR-EV2.1 originally deferred chart overlays. `SOR-EV2.2` now adds Evidence Lab overlay controls, baseline markers, linkable variant/context markers, worst-trade focus mode, control-pocket view, and explicit missing-overlay-data states without changing canonical evidence.

## Limitations

Status: verified

- SOR-EV1 completed-trade overlays and lookahead diagnostics are not production candidates.
- Only true-forward replay variants can become candidates for deeper evidence.
- Dashboard date-filtered numbers are display-only recalculations and do not regenerate canonical evidence packs.
- The Evidence Lab must not be used as proof that a variant is live-ready or paper-runtime approved.

## Next Recommended Phase

Status: needs_followup

If founder review identifies a narrow variant worth deeper review, run a separately scoped SOR-EV3 evidence phase with backend canonical Strategy Validation runs. Do not use dashboard-only date filters or overlays as canonical evidence.
