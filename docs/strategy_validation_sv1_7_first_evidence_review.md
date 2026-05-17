> Historical note.
> This report is retained for audit/history.
> Current truth lives in [[00_Money_Flow_Command_Center]] and the latest PT-RT / SV / audit docs.
> Do not use this file as current operating instructions unless a current-phase note links to it explicitly.

# SV1.7 First Canonical Money Flow Evidence Review

Recorded at UTC: `2026-05-03T08:01:12Z`

Superseded by: [`docs/strategy_validation_sv1_8_historical_data_bootstrap.md`](strategy_validation_sv1_8_historical_data_bootstrap.md), which adds Alembic/schema status and confirms the reachable local DB is missing both `alembic_version` and `candles`.

## Scope

SV1.7 ran the canonical Money Flow evidence review path against the currently accessible local database state. This is research-only evidence review. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, create paper/live trading artifacts, call exchange adapters, route, submit, or prove profitability.

## Database Access Findings

Default configured DB:

- Sanitized URL: `postgresql+psycopg://money_flow:***@postgres:5432/money_flow`
- Reachable: `false`
- Blocking error: `failed to resolve host 'postgres'`
- Result: canonical campaigns cannot audit persisted candles from the default shell configuration.

Accessible local DB checked with explicit environment override:

```bash
DB_HOST=127.0.0.1 DB_PORT=54322 DB_USER=postgres DB_PASSWORD=<redacted> DB_NAME=postgres \
  .venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --format both \
  --review-output-dir /tmp/money-flow-sv1.7-local-db-review-escalated
```

- Sanitized URL: `postgresql+psycopg://postgres:***@127.0.0.1:54322/postgres`
- Reachable: `true`
- `candles` table exists: `false`
- Persisted candle count: `null`
- Result: canonical campaigns are blocked by `candles_table_missing`.

The reachable local database is not a populated Money Flow schema. It cannot support first real canonical evidence-pack generation yet.

## Canonical Campaign Audit Result

| campaign | status | evidence pack generated | blocked/gap reasons |
| --- | --- | --- | --- |
| `money_flow_core_btc` | `insufficient_data` | `false` | `blocked_campaign_rows`, `candles_table_missing` |
| `money_flow_core_multi_symbol` | `insufficient_data` | `false` | `blocked_campaign_rows`, `candles_table_missing` |

## Coverage Gap

- `money_flow_core_btc` checked 6 symbol/component/window rows and all 6 are blocked because the `candles` table is unavailable.
- `money_flow_core_multi_symbol` checked 18 symbol/component/window rows and all 18 are blocked because the `candles` table is unavailable.
- Missing symbols remain `BTC`, `ETH`, and `SOL` for canonical multi-symbol review.
- Missing components remain `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- No fill-timing, component, regime, drawdown, fee/slippage, no-trade, or invalid-reason observations are available until persisted candles exist.

## Evidence Status

Current evidence status: `insufficient_data`

No canonical evidence packs were generated from real persisted data in SV1.7. This is a historical-data/schema readiness gap, not a Money Flow strategy failure.

If a future run generates some packs while other canonical campaigns remain blocked, the review summary reports `partial_evidence_ready_with_data_gaps` so founder/operator review cannot mistake partial evidence for complete evidence.

## Next Research Actions

- Point the review CLI at a reachable Money Flow database with migrations applied and a populated `candles` table.
- Import or backfill public historical candles for the canonical BTC/ETH/SOL windows using `scripts/import_strategy_validation_candles.py` or another explicitly research-only data path.
- Rerun the canonical review with `--generate-evidence-packs` only after data-readiness audit rows are no longer missing, thin, or blocked.
- Review generated packs manually before any paper-trading design is scoped.

This report is not paper-trading approval, not live execution readiness, and not a strategy recommendation.
