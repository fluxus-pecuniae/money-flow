# SV1.8.1 Evidence Review Schema Truth Hotfix

SV1.8.1 is a research-only schema-gate and report-truth hotfix. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, generate first real evidence packs, create paper/live artifacts, call exchanges, route, submit, or approve paper trading.

## What Changed

- Evidence-pack generation now requires `migrated_schema_ready`.
- A `candles` table alone is not enough to generate canonical evidence packs.
- Schema readiness requires current Alembic migration truth and required strategy-validation tables:
  - `candles`
  - `instruments`
  - `symbols`
- DBs with missing, unknown, or outdated migration truth are reported as schema/data-readiness gaps.
- Top-level no-live/no-exchange flags are now aggregated from campaign results instead of relying on dataclass defaults.

## Blocking DB States

The evidence-review layer blocks evidence-pack generation for:

- `database_unreachable`
- `schema_missing`
- `schema_present_migration_version_unknown`
- `required_schema_missing`
- `migrations_out_of_date`
- `candles_table_missing`
- missing `alembic_version`
- missing required strategy-validation tables

These states mean schema/data readiness is incomplete. They are not Money Flow strategy results.

## Founder / Operator Meaning

Before first real canonical evidence packs can be generated, the intended Money Flow database must be reachable, migrated to the repo Alembic head, and populated with enough public/offline historical candles for the canonical BTC/ETH/SOL campaign windows and timeframes.

Use the read-only status check first:

```bash
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --db-status-only \
  --format markdown
```

Only after the status reports `migrated_schema_ready` and campaign audits show sufficient candle coverage should evidence-pack generation be run:

```bash
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --generate-evidence-packs \
  --format both
```

## Current Evidence Status

SV1.8.1 generated no first real canonical evidence packs. It fixes the schema gate that must be trusted before those packs are generated in a later phase.

## Limitations

- Backtest evidence is not proof of future profitability.
- Paper trading remains deferred.
- Strategy rules remain unchanged.
- Historical candle import remains public/offline/research-only.
- Evidence review remains separate from routing, approvals, submitted orders, and exchange adapters.
