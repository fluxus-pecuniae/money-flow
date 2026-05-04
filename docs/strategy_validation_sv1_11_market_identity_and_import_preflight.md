# SV1.11 Market Identity And Candle Import Preflight

SV1.11 is research-only. It does not change Money Flow rules, optimize parameters, recommend a variant, create paper/live artifacts, route, submit, call exchanges, or generate evidence packs.

## Why This Exists

SV1.10 left the intended local `money_flow` DB migrated and schema-ready, but empty:

- `candles` exists and contains `0` rows.
- `instruments` exists but has no canonical BTC/ETH/SOL Hyperliquid perpetual USDC rows.
- `symbols` exists but has no canonical BTC/ETH/SOL venue mappings.

The candle importer resolves symbol/instrument mappings before writing candles. Candle import therefore requires market identity rows first.

## Market Identity Manifest

Example manifest:

```text
configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json
```

The example is operator-editable and offline/manual. It seeds or verifies BTC, ETH, and SOL Hyperliquid perpetual USDC identity rows for Strategy Validation. The example marks symbols as `is_strategy_eligible=false` and `is_trading_eligible=false`; this seed path is not trading enablement.

Before real use, verify the manifest values against an accepted public/offline source:

- `price_tick_size`
- `quantity_step_size`
- `min_order_size`
- optional `size_decimals`
- optional `max_leverage`
- `exchange_symbol`

The seed script rejects malformed, non-finite, zero, or negative Decimal values.

## Dry Run

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --dry-run \
  --format markdown
```

Dry-run reports intended inserts/updates and writes nothing.

## Seed

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --format both \
  --output-dir /tmp/money-flow-sv1.11-market-identity
```

The seed path upserts only `InstrumentModel` and `SymbolModel` rows. It refuses to silently retarget an existing symbol mapping to another instrument identity.

## Verify Only

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --verify-only \
  --format markdown
```

Verify-only fails with explicit conflicts if any required BTC/ETH/SOL instrument or symbol mapping is missing or has drifted from the manifest.

## Candle Import Preflight

Run preflight before importing candle files:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --input /path/to/btc_15m_core_window_1.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --format markdown
```

Preflight validates without writing candles:

- required columns
- timezone-explicit `open_time` and `close_time`
- timeframe duration consistency
- finite positive OHLC
- `high >= max(open, close)`
- `low <= min(open, close)`
- non-negative volume
- non-negative optional `trade_count`
- known symbol mapping
- known `instrument_key` when supplied

Timezone-naive rows are rejected by default. Timezone-explicit source data remains the preferred canonical input.

## Review JSON Requirements

Preflight can also verify identity requirements from an evidence-review JSON:

```bash
.venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --requirements-from-review-json /path/to/evidence_review.json \
  --environment testnet \
  --venue hyperliquid \
  --format markdown
```

## Proceeding To Candle Import

After market identity verify-only and candle preflight pass, use the hardened offline importer:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/btc_15m_core_window_1.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_offline_btc_15m_core_window_1
```

No evidence packs should be generated until all 18 canonical BTC/ETH/SOL candle requirements from SV1.10 are covered.

## Current Status

SV1.11 adds tooling and report truth only. It does not seed the operator's local DB automatically and does not import candles automatically. First real evidence packs remain deferred until:

- the intended DB reports `migrated_schema_ready`
- canonical market identity verify-only passes
- all required candle files pass preflight
- candles are imported with timezone-explicit timestamps
- canonical evidence review reports sufficient data
