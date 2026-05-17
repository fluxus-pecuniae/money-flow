> Historical note.
> This report is retained for audit/history.
> Current truth lives in [[00_Money_Flow_Command_Center]] and the latest PT-RT / SV / audit docs.
> Do not use this file as current operating instructions unless a current-phase note links to it explicitly.

# SV1.12.2 Identity And Canonical Candle-File Readiness

SV1.12.2 is a research-only readiness phase. It prepares the next guarded canonical candle import by checking operator-verified market identity and producing the exact canonical candle-file checklist. It does not import candles, generate evidence packs, change Money Flow rules, optimize parameters, recommend a strategy variant, create paper/live artifacts, route, submit, or call exchange adapters.

## Operational Result

- Final readiness status: `not_ready_for_guarded_import`
- Market identity seeded: `false`
- Candles imported: `false`
- Evidence packs generated: `false`
- SV1.12.3 guarded import can proceed: `false`

The founder/operator has not supplied explicit verification for the Hyperliquid perpetual USDC BTC/ETH/SOL market-identity manifest values in this task, so SV1.12.2 did not seed identity rows. The repo/session also does not contain the 18 timezone-explicit canonical candle files, so no requirement-aware file preflight was run.

## DB Status Checked

Command used:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/check_strategy_validation_import_readiness.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --format json
```

Observed sanitized DB status:

- DB URL: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`
- DB reachable: `true`
- DB target role: `configured_money_flow_database`
- Intended strategy-validation DB: `true`
- Schema status: `migrated_schema_ready`
- Alembic revision: `20260430_0025`
- Required tables present: `candles`, `instruments`, `symbols`
- Persisted candle count: `0`

## Market Identity Readiness

Verify-only inspection still reports missing research identity:

- `BTC` / `perpetual:linear:BTC:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`
- `ETH` / `perpetual:linear:ETH:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`
- `SOL` / `perpetual:linear:SOL:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`

The example manifest contains entries for BTC, ETH, and SOL, but SV1.12.2 did not write them because the prompt did not include explicit operator verification of the values.

Before seeding, the operator must verify for each symbol:

- `instrument_key`, `canonical_symbol`, `venue symbol`, and `exchange_symbol`
- `market_type`, `product_type`, `base_asset`, `quote_asset`, and `settlement_asset`
- `price_tick_size`, `quantity_step_size`, and `min_order_size`
- `size_decimals`, `max_leverage`, and isolated/cross constraints when present
- `venue_asset_id` / `asset_id` when present
- `is_strategy_eligible=false` and `is_trading_eligible=false`

If verified, seed research-only identity with:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/check_strategy_validation_import_readiness.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --seed-identity \
  --operator-verified \
  --verified-by "<operator-name>" \
  --format both \
  --output-dir /tmp/money-flow-sv1.12.2-readiness
```

This path writes only research identity. Successful symbols must remain `is_strategy_eligible=false` and `is_trading_eligible=false`.

## Canonical Candle File Requirements

All files must use timezone-explicit ISO-8601 `open_time` and `close_time` values ending in `Z` or carrying an explicit UTC offset. Timezone-naive timestamps are rejected for canonical import.

Required columns:

```text
symbol,instrument_key,open_time,close_time,open,high,low,close,volume,trade_count
```

Each file must cover candle closes in `(start_at, end_at]`. Row-level preflight alone is not canonical coverage proof; requirement-aware preflight must prove exact close-slot coverage.

| symbol | timeframe | component | window `(start_at, end_at]` | expected candles | suggested filename | impacted campaign(s) |
| --- | --- | --- | --- | --- | --- | --- |
| `BTC` | `15m` | `sleeve_15m` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `1344` | `hyperliquid_btc_15m_20260101_000000z_20260115_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `BTC` | `15m` | `sleeve_15m` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `1632` | `hyperliquid_btc_15m_20260115_000000z_20260201_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `BTC` | `1h` | `sleeve_1h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `336` | `hyperliquid_btc_1h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `BTC` | `1h` | `sleeve_1h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `408` | `hyperliquid_btc_1h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `BTC` | `4h` | `sleeve_4h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `84` | `hyperliquid_btc_4h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `BTC` | `4h` | `sleeve_4h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `102` | `hyperliquid_btc_4h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| `ETH` | `15m` | `sleeve_15m` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `1344` | `hyperliquid_eth_15m_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `ETH` | `15m` | `sleeve_15m` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `1632` | `hyperliquid_eth_15m_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |
| `ETH` | `1h` | `sleeve_1h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `336` | `hyperliquid_eth_1h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `ETH` | `1h` | `sleeve_1h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `408` | `hyperliquid_eth_1h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |
| `ETH` | `4h` | `sleeve_4h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `84` | `hyperliquid_eth_4h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `ETH` | `4h` | `sleeve_4h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `102` | `hyperliquid_eth_4h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `15m` | `sleeve_15m` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `1344` | `hyperliquid_sol_15m_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `15m` | `sleeve_15m` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `1632` | `hyperliquid_sol_15m_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `1h` | `sleeve_1h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `336` | `hyperliquid_sol_1h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `1h` | `sleeve_1h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `408` | `hyperliquid_sol_1h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `4h` | `sleeve_4h` | `(2026-01-01T00:00:00+00:00, 2026-01-15T00:00:00+00:00]` | `84` | `hyperliquid_sol_4h_20260101_000000z_20260115_000000z.csv` | `money_flow_core_multi_symbol` |
| `SOL` | `4h` | `sleeve_4h` | `(2026-01-15T00:00:00+00:00, 2026-02-01T00:00:00+00:00]` | `102` | `hyperliquid_sol_4h_20260115_000000z_20260201_000000z.csv` | `money_flow_core_multi_symbol` |

The count is 18 because BTC appears in both canonical campaigns but overlaps by symbol, timeframe, and window, so the BTC rows are de-duplicated.

## Available Files

Repo/session scan found no operator-provided canonical candle files. Only strategy-validation config JSON files were present under `configs/strategy_validation/`.

Because no files were available, SV1.12.2 did not run requirement-aware file preflight.

## Next Operator Action

1. Verify the Hyperliquid perpetual USDC BTC/ETH/SOL manifest values offline.
2. Seed research-only identity with `--seed-identity --operator-verified --verified-by "<operator-name>"`.
3. Provide the 18 timezone-explicit candle files above.
4. Run requirement-aware preflight for every file with a complete one-to-one input-to-requirement map.
5. Proceed to SV1.12.3 guarded import only if identity is ready and every file reports `ready_for_import=true`.

SV1.13 evidence review remains deferred until guarded import status is complete and data-readiness audits are clean.
