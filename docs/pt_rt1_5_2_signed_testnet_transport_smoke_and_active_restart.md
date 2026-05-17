# PT-RT1.5.2 Signed Testnet Transport Smoke And Active Restart

## Objective

PT-RT1.5.2 verifies signed Hyperliquid testnet transport from a clean active-week runtime shell, keeps the warm-start gate active, and prepares the Week 1 active runtime restart.

This phase is testnet plumbing validation only. Public Hyperliquid mainnet candles remain strategy truth. Synthetic paper ledgers remain PnL truth. Testnet fills do not update synthetic PnL. No live trading is approved and no strategy is production-approved.

## Starting State

- status: implemented
- previous PT-RT1.5.1 smoke state is archived as `pt_rt1_5_1_smoke_archived` / `pre_pt_rt1_5_2_runtime`.
- no existing `run_pt_rt1_paper_observation` process was running at PT-RT1.5.2 preflight.
- active timeframes remain `1h`, `4h`, and `1d`.
- `15m` remains paused and cannot trigger active-week synthetic opens or testnet transport.

## Signed Transport Env Status

- status: verified
- local `.env` was read through the scoped PT-RT1.5.2 allowlist only.
- private key and raw secret values were not printed.
- signed testnet transport client was configured from local env.
- target account and signer were recorded only as abbreviated values in runtime summary.
- live/mainnet URL remains rejected.

## Warm-Start Gate Verification

- status: verified
- `fresh_signal_only_after_runtime_start = true`.
- startup-valid signals cannot create synthetic opens.
- startup-valid signals cannot create testnet orders.
- a fresh false-to-true post-start Money Flow v1.2 baseline open is required for strategy-linked transport.

## Candle-Close Scheduler Verification

- status: verified
- market refresh can update watchlist, chart, data health, and MTM.
- strategy signal evaluation remains candle-close only.
- active strategy timeframes are `1h`, `4h`, and `1d`.
- no continuous intrabar strategy scanning is enabled.

## Testnet Smoke Result

- status: verified_with_venue_reject
- smoke trigger used: `testnet_transport_smoke_not_strategy_signal`.
- trigger lane: `none`.
- synthetic trade created: `false`.
- strategy PnL update from testnet: `false`.
- fixed notional: `25 USDC`.
- order endpoint called: `true`.
- signed order endpoint called: `true`.
- venue result: rejected with sanitized message `Order has invalid size.`
- cancel status: `not_required`.
- reconcile status: `reconciled`.
- open orders after reconcile: `[]`.

The venue reject proves the signed testnet transport path reached Hyperliquid testnet and stayed separate from strategy PnL. The size reject is a follow-up formatter/readiness item before relying on accepted/open lifecycle coverage.

## Open-Position MTM Verification

- status: verified_no_open_positions_in_smoke
- preferred MTM source remains public mainnet `allMids`.
- fallback remains latest fully closed public mainnet candle close.
- smoke had no open synthetic positions, so no MTM row changed.
- MTM updates do not trigger strategy signal evaluation.

## Active Runtime Restart Status

- status: operator_start_required
- a clean 24-hour active runtime was not started by Codex as a background process.
- use this command for the clean Week 1 active runtime:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_5_2_week1_active \
  --pt-rt1-5-week1-active \
  --signal-evaluation-mode candle_close_only \
  --fresh-signal-only-after-runtime-start \
  --enable-baseline-testnet-transport \
  --founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --public-mainnet-only
```

## Dashboard Status

- status: implemented
- Paper Trading now prefers `pt_rt1_5_2_week1_active` runtime files.
- Testnet Order Lifecycle can also display the PT-RT1.5.2 transport-smoke lifecycle.
- dashboard control defaults to PT-RT1.5.2 active runtime settings.

## Boundaries

- live trading approved: `false`
- production strategy approved: `false`
- production Money Flow rules changed: `false`
- candidate lane testnet transport: `blocked`
- MF-ORIG lane testnet transport: `blocked`
- wildcard lane testnet transport: `blocked`
- testnet fills update synthetic PnL: `false`
- runtime artifacts committed: `false`

## Next Recommended Action

Start the clean PT-RT1.5.2 Week 1 active runtime using the operator command above, then review the next fresh baseline open. Before depending on accepted/open testnet lifecycle coverage, address the Hyperliquid testnet `Order has invalid size.` venue reject in the formatter/readiness path.
