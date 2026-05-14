# PT-RT1 24-Hour Dry Run With Probes Disabled

## Goal

Run the PT-RT1 strategy-truth lane for 24 hours with testnet probes disabled.

This is paper observation only. It does not approve production trading, paper-runtime promotion, live trading, live orders, or testnet fills as strategy truth.

## Required Starting State

- Public mainnet market-data configuration is present.
- `PT_RT1_TESTNET_PROBES_ENABLED=false`.
- `PT_RT1_TESTNET_KILL_SWITCH=true`.
- No API keys are required for the strategy-truth lane.
- Runtime output path is local and ignored: `reports/paper_runtime/`.
- Dashboard Paper Observation view is available.

## Steps

1. Start the PT-RT1 paper-observation service in dry-run mode.
2. Confirm the strategy-truth lane uses Hyperliquid public mainnet data only.
3. Confirm public mainnet candle refreshes for eligible symbols.
4. Confirm only fully closed candles trigger evaluations.
5. Confirm indicators are computed without defaulting missing values to zero.
6. Confirm duplicate signal prevention blocks repeated loop evaluations.
7. Confirm each lane keeps its own 10,000 USDC synthetic ledger.
8. Confirm realized equity compounds after wins and losses.
9. Confirm open positions update unrealized PnL from public mainnet mids/closes.
10. Confirm no testnet order endpoint call occurs.
11. Confirm no private/signed endpoint call occurs.
12. Confirm no API key is loaded by the strategy-truth lane.
13. Review dashboard readability and data-health warnings.

## Success Criteria

- Public mainnet data refreshes.
- Fully closed candle detection works.
- Synthetic paper decisions record.
- Synthetic ledgers update.
- Duplicate prevention works.
- Dashboard remains readable.
- Testnet probe path remains disabled.
- No testnet order endpoint calls occur.
- No private/signed/order endpoints are called from strategy truth.
- No API keys are used.
- No live trading is approved or attempted.

## Failure Criteria

- Any strategy-truth code path calls private/signed/account/order endpoints.
- Any strategy-truth lane uses testnet prices.
- Any testnet fill updates paper PnL.
- Duplicate refresh loops create duplicate paper trades.
- Data health is stale/degraded but new entries continue.

If a failure occurs, stop the dry run and record the reason code in the PT-RT1 audit notes.
