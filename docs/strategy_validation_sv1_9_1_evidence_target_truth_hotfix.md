# SV1.9.1 Evidence Target Truth Hotfix

SV1.9.1 is a research-only evidence-target, candle-import, and Obsidian memory-governance hotfix. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, generate first real canonical evidence packs, create paper/live artifacts, call exchanges, route, submit, or approve paper trading.

## What Changed

- Evidence-pack generation now requires both migrated/current schema truth and a clearly intended non-maintenance strategy-validation DB target.
- Maintenance database names such as `postgres`, `template0`, and `template1` block evidence generation by default even if they have current schema and candles.
- No ambiguous DB-target override exists in SV1.9.1; operators must point evidence review at a non-maintenance intended Money Flow database instead.
- Offline candle import now rejects timezone-naive timestamps by default.
- A non-default `--assume-naive-utc` import override exists for fixture/exploratory research, records `timestamp_assumption=assume_naive_utc`, and should not be treated as clean canonical evidence without explicit founder/operator acceptance.
- Import summaries now include source file name, source file SHA-256, row count, rejected count, timestamp assumption, and naive timestamp override truth.
- Obsidian current-truth notes and full project memory were refreshed through SV1.9.

## Blocking DB Target States

Evidence-pack generation is blocked when any of these target-truth facts are present:

- `strategy_validation_db_target_not_intended`
- `strategy_validation_db_target_ambiguous`
- `maintenance_database_target_requires_confirmation`
- `evidence_generation_blocked_by_db_target_truth`

These target blockers are reported alongside schema/data blockers. They are operational evidence-readiness gaps, not Money Flow strategy results.

## Candle Import Timestamp Truth

Timezone-explicit source data is preferred for first canonical evidence.

Default behavior:

```bash
.venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/candles.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_dataset_name
```

Rows with timestamps like `2026-01-01T00:00:00` are rejected with `candle_import_naive_timestamp` / `timezone_required_for_candle_import`.

Non-default exploratory override:

```bash
.venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/candles.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_dataset_name \
  --assume-naive-utc
```

Override imports are marked with `timestamp_assumption=assume_naive_utc`, `naive_timestamp_override_used=true`, source label, file path/name/hash, affected environment/venue/symbol/timeframe, and warning reason codes. The current candle model still has no per-candle provenance table, so this provenance is summary-level only.

## Repo Hygiene

Generated research outputs remain excluded from normal commits and review bundles:

- `reports/strategy_validation/`
- `reports/strategy_validation_reviews/`
- `reports/strategy_validation_imports/`
- `data/strategy_validation/imports/`
- `data/strategy_validation/candles/`

Only tiny intentional test fixtures should be tracked under `tests/fixtures/`.

## Current Evidence Status

No first real canonical Money Flow evidence packs were generated in SV1.9.1. The next phase can prepare a migrated, non-maintenance Money Flow DB, import timezone-explicit public/offline BTC/ETH/SOL candles, and attempt first real evidence packs only after DB target, schema, and candle-readiness truth are clean.
