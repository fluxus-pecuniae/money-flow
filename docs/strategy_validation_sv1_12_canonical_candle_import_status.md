# SV1.12 Canonical Candle Import Status

SV1.12 adds guarded canonical candle bundle import for Strategy Validation. It is research-only candle import readiness/import workflow. It changes no Money Flow rules, performs no optimization, recommends no strategy variant, generates no evidence packs, creates no paper/live artifacts, routes nothing, submits nothing, and calls no exchange adapters.

## What SV1.12 Adds

SV1.12 adds a guarded import wrapper and CLI:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/import_strategy_validation_candle_bundle.py \
  --input /path/to/btc_15m_core_window_1.csv \
  --requirements-from-review-json /path/to/evidence_review.json \
  --input-requirement-map /path/to/input_requirement_map.json \
  --environment testnet \
  --venue hyperliquid \
  --format both \
  --output-dir /tmp/money-flow-sv1.12-import
```

The wrapper composes the existing Strategy Validation gates:

- intended non-maintenance DB target
- reachable migrated/current schema
- required `alembic_version`, `candles`, `instruments`, and `symbols` tables
- complete requirement-aware candle preflight
- operator-verified research market identity
- non-trading / non-strategy-eligible symbols
- timezone-explicit candle rows
- hardened all-or-nothing candle importer

## DB Gate

Canonical candle import is blocked unless the DB target is clearly intended for Strategy Validation and is not a maintenance database such as `postgres`, `template0`, or `template1`.

The DB must report:

- reachable: `true`
- schema status: `migrated_schema_ready`
- migrations current: `true`
- required tables present: `candles`, `instruments`, and `symbols`
- Alembic version table present

If any DB/schema condition fails, no candle files are imported.

## Market Identity Gate

Each canonical requirement must resolve to operator-verified research identity:

- instrument exists
- symbol mapping exists
- `raw_metadata.research_only_market_identity_seed=true`
- `raw_metadata.source=manual_offline_manifest`
- `raw_metadata.operator_verified=true`
- `raw_metadata.verified_by` exists
- `raw_metadata.verified_at` exists
- `is_strategy_eligible=false`
- `is_trading_eligible=false`

This is research identity only. It is not live trading eligibility, not exchange certification, and not permission to route or execute.

## Preflight Gate

SV1.12 requires the SV1.11.2 requirement-aware preflight gate before import:

- every input file maps to exactly one canonical requirement
- every supplied requirement has exactly one input file
- no duplicate requirement mappings
- no unmapped input files
- no missing input files
- row-level OHLCV/timestamp/timeframe validation passes
- symbol and `instrument_key` match the requirement
- close-time slots exactly cover `(requested_start_at, requested_end_at]`
- no missing, duplicate, extra, or out-of-window close slots

Row-level preflight alone is still useful, but it is not canonical coverage proof.

## Import Behavior

Only files whose guardrail status is clean are imported. The import path calls the existing hardened offline importer, which keeps invalid files all-or-nothing and blocks identity retargeting, malformed OHLCV, timeframe mismatches, and timezone-naive timestamps by default.

SV1.12.1 makes bundle-level failure semantics explicit before the first operational import. The current policy is `explicit_partial_with_resume`: if a later file fails after a prior file was committed by the lower-level per-file importer, the result is `partial_import`, imported and failed requirement IDs are listed, row counts are shown, and the bundle cannot be treated as complete. Rerun is duplicate-safe for the same candle identity, but evidence review must not proceed until final guarded import status is `canonical_import_complete`.

SV1.12.1 also makes mapping problems inspectable. Unmapped input files appear as blocked file rows with `unmapped_input_file_blocked`, and supplied requirements with no file appear as blocked requirement rows with `missing_requirement_blocked`. Operators should not need to inspect only global reason codes to identify which file or requirement is missing.

## Current Operational Status

SV1.12 implemented and test-proved the guarded import path. SV1.12.1 checked the intended local DB and found it reachable, migrated/current, and still empty (`persisted_candle_count=0`), but operator-verified BTC/ETH/SOL market identity rows and repo/session canonical candle files were still missing. No generated import outputs were committed and no evidence packs were generated.

The remaining operational step is to seed/verify operator-verified research-only BTC/ETH/SOL market identity, provide all 18 timezone-explicit canonical candle files, and rerun the guarded import with complete one-to-one requirement mapping.

## Next Step

After guarded import succeeds for all 18 canonical BTC/ETH/SOL requirements, SV1.13 can rerun canonical evidence review and generate first real evidence packs if data readiness is clean.

SV1.13 must still treat evidence as manual research review input only, not proof of profitability, not paper-trading approval, and not a strategy recommendation.
