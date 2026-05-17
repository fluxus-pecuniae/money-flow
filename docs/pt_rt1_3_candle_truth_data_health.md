> Historical note.
> This report is retained for audit/history.
> Current truth lives in [[00_Money_Flow_Command_Center]] and the latest PT-RT / SV / audit docs.
> Do not use this file as current operating instructions unless a current-phase note links to it explicitly.

# PT-RT1.3 Candle-Truth Data Health

## Scope

PT-RT1.3 fixes false-positive `data_unavailable` rows caused by thin, stale, or missing Hyperliquid public mids.

This phase changes runtime data-health semantics only. It does not change Money Flow strategy rules, sizing, testnet probe policy, order paths, live trading status, evidence-pack methodology, or SOR behavior.

## What Changed

- Hyperliquid `meta` and precision now determine whether a requested symbol can enter the scanner.
- Missing, nonpositive, stale, or thin `allMids` data is recorded as a non-blocking mid warning.
- Fully closed `candleSnapshot` availability is the strategy-readiness gate.
- If clean closed candles are available, paper-decision evaluation can proceed even when the mid is missing or stale.
- If candles are missing, malformed, degraded, or insufficient for indicators, the runtime still emits blocking `data_unavailable` decisions.

## New Runtime Semantics

- `mid_health_blocks_strategy`: `false`
- `candle_health_blocks_strategy`: `true`
- `data_health_semantics`: `candle_strategy_truth`

New warning/status labels include:

- `mid_stale_or_thin_tick`
- `mid_missing_or_nonpositive`
- `mid_health_warning_non_blocking`
- `mid_unavailable_but_candles_available`
- `candle_unavailable_blocking`

## Dashboard Meaning

The Paper Observation dashboard now separates:

- blocking candle rows
- non-blocking mid warning rows
- lane-expanded `data_unavailable` decisions

This means quiet Hyperliquid pairs should no longer look broken only because their public mid did not update. They should scan if clean fully closed candles exist.

## Boundaries

- Production Money Flow rules changed: no
- Strategy paper runtime approved as production behavior: no
- Live trading approved: no
- Private/signed/order endpoints added or called: no
- API keys used: no
- Testnet fills/prices update paper PnL: no
- SOR/fanout/CBBO/cross-venue routing added: no

## Operator Check

After starting a fresh runtime, review:

- `summary.json`
- `data_health.json`
- `decisions.jsonl`

Expected PT-RT1.3 behavior:

1. `mid_warning_non_blocking` can be nonzero.
2. `candle_unavailable_blocking` should identify true candle/endpoint blockers.
3. `lane_expanded_data_unavailable_decisions` should no longer rise only because a public mid is stale or missing.
4. `paper_opened` and `paper_closed` still depend on fully closed public-mainnet candles and unchanged strategy logic.
