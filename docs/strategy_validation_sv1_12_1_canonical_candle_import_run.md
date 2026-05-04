# SV1.12.1 Canonical Candle Import Run

SV1.12.1 is a guarded canonical candle import run / blocked-run report. It is research-only. It imports no candles unless DB, schema, operator-verified non-trading identity, one-to-one file mapping, requirement-aware preflight, and importer guards pass. It generates no evidence packs, changes no Money Flow rules, recommends no strategy variant, creates no paper/live artifacts, routes nothing, submits nothing, and calls no exchange adapters.

## Operational Result

- Final status: `import_blocked`
- Operational import attempted: `false`
- Evidence packs generated: `false`
- Bundle failure policy implemented: `explicit_partial_with_resume`
- Canonical import complete: `false`
- SV1.13 evidence review can proceed: `false`

The import was not run because the repo/session did not contain founder/operator-provided timezone-explicit canonical candle files, and the intended local DB does not yet contain operator-verified BTC/ETH/SOL research market identity rows.

## DB Status Checked

Command used for status-only inspection:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/review_money_flow_evidence_packs.py --db-status-only --format json
```

Observed sanitized DB status:

- DB URL: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`
- DB reachable: `true`
- DB target role: `configured_money_flow_database`
- Intended strategy-validation DB: `true`
- Schema status: `migrated_schema_ready`
- Alembic revision: `20260430_0025`
- Repo migration head: `20260430_0025`
- Required tables present: `candles`, `instruments`, `symbols`
- Persisted candle count: `0`

## Market Identity Status Checked

Command used for verify-only inspection:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --verify-only \
  --format json
```

Observed blocked identity requirements:

- `BTC` / `perpetual:linear:BTC:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`
- `ETH` / `perpetual:linear:ETH:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`
- `SOL` / `perpetual:linear:SOL:USDC:USDC`: `missing_instrument`, `missing_symbol_mapping`

No identity rows were written by the verify-only command.

## Candle Files

Repo/session file scan found no operator-provided canonical candle files. Only strategy-validation config JSON files were present under `configs/strategy_validation/`.

SV1.12.1 therefore did not run guarded import. The required candle files remain the 18 unique canonical BTC/ETH/SOL requirements reported by SV1.10/SV1.12:

- symbols: `BTC`, `ETH`, `SOL`
- timeframes/components: `15m`, `1h`, `4h`
- windows: canonical campaign windows from `configs/strategy_validation/campaigns/`
- timestamps: timezone-explicit only, preferably UTC `Z`
- mapping: every input file must map to exactly one requirement, and every requirement must have exactly one input file

## Failure Semantics

SV1.12.1 makes bundle-level import failure semantics explicit:

- Policy: `explicit_partial_with_resume`
- If a later file fails after an earlier file was committed by the lower-level per-file importer, the result is `partial_import`, not complete.
- Output records `partial_persistence_occurred`, `imported_requirement_ids`, `failed_requirement_ids`, `rows_inserted`, `rows_updated`, and `rows_unchanged`.
- Rerun is safe after fixing files because the lower-level candle importer is duplicate-safe for the same identity, but SV1.13 evidence review must not proceed unless the final guarded import status is `canonical_import_complete`.

SV1.12.1 also makes operator output more inspectable:

- every supplied input file appears in `file_import_results`
- unmapped input files get `unmapped_input_file_blocked`
- every supplied canonical requirement appears in `requirement_import_results`
- requirements with no mapped file get `missing_requirement_blocked`
- missing requirements are counted separately as `requirements_missing`

## Remaining Gaps

- Seed or verify BTC/ETH/SOL Hyperliquid perpetual USDC research market identity with explicit operator verification.
- Provide all 18 timezone-explicit canonical candle files.
- Provide a complete one-to-one input-to-requirement map.
- Run guarded import and confirm final status is `canonical_import_complete`.

Only after those gaps are closed should SV1.13 run post-import canonical evidence review and generate evidence packs if data readiness is clean.
