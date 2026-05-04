# SV1.10 First Real Evidence Status

SV1.10 is a research-only DB/schema/candle-readiness and first-real evidence attempt. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, create paper/live artifacts, call exchanges, route, submit, or approve paper trading.

## DB Target Used

The intended local strategy-validation DB target for this run was:

- Sanitized URL: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`
- Host: `127.0.0.1`
- Port: `5432`
- Database: `money_flow`
- User: `money_flow`
- Target role: `configured_money_flow_database`
- Intended strategy-validation DB: `true`
- Maintenance DB target: `false`

The default configured target `postgresql+psycopg://money_flow:***@postgres:5432/money_flow` still depends on a `postgres` DNS name that was not resolvable in this shell. Local Docker Compose was not available through `docker compose` or `docker-compose`, so the local Homebrew Postgres instance was used instead.

## Schema And Migration Status

The local Homebrew Postgres server at `127.0.0.1:5432` was started from `/opt/homebrew/var/postgresql@16`. The `money_flow` role and `money_flow` database were created locally, then Alembic migrations were applied to head:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python -m alembic upgrade head
```

Post-migration evidence-review DB status:

- Reachable: `true`
- `alembic_version` exists: `true`
- Applied revision: `20260430_0025`
- Repo head revision: `20260430_0025`
- Migrations current: `true`
- Schema status: `migrated_schema_ready`
- Required tables present: `candles`, `instruments`, `symbols`
- Persisted candle count: `0`

## Canonical Campaign Audit Status

Canonical configs audited:

- `configs/strategy_validation/campaigns/money_flow_core_btc.json`
- `configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json`

Review command:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --generate-evidence-packs \
  --format both \
  --review-output-dir /tmp/money-flow-sv1.10-local-review
```

Result:

- Overall status: `insufficient_data`
- Generated campaign count: `0`
- Blocked campaign count: `2`
- Generated evidence packs: `0`
- Evidence-pack paths: none

This is a candle-data readiness failure, not a Money Flow strategy result.

## Unique Import Requirements

The canonical review produced 18 unique import requirements after grouping overlapping BTC requirements across the BTC-only and multi-symbol campaigns.

All source candles must use timezone-explicit ISO-8601 `open_time` and `close_time` values. Timezone-naive rows are rejected by default. CSV or JSON files must include `symbol`, `open_time`, `close_time`, `open`, `high`, `low`, `close`, and `volume`; `instrument_key` is optional but preferred, and `trade_count` is optional.

| Symbol | Timeframe | Window `(start_at, end_at]` | Expected | Actual | Missing | Campaigns Impacted |
| --- | --- | --- | ---: | ---: | ---: | --- |
| BTC | 15m | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 1,344 | 0 | 1,344 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| BTC | 15m | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 1,632 | 0 | 1,632 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| BTC | 1h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 336 | 0 | 336 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| BTC | 1h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 408 | 0 | 408 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| BTC | 4h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 84 | 0 | 84 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| BTC | 4h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 102 | 0 | 102 | `money_flow_core_btc`, `money_flow_core_multi_symbol` |
| ETH | 15m | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 1,344 | 0 | 1,344 | `money_flow_core_multi_symbol` |
| ETH | 15m | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 1,632 | 0 | 1,632 | `money_flow_core_multi_symbol` |
| ETH | 1h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 336 | 0 | 336 | `money_flow_core_multi_symbol` |
| ETH | 1h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 408 | 0 | 408 | `money_flow_core_multi_symbol` |
| ETH | 4h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 84 | 0 | 84 | `money_flow_core_multi_symbol` |
| ETH | 4h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 102 | 0 | 102 | `money_flow_core_multi_symbol` |
| SOL | 15m | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 1,344 | 0 | 1,344 | `money_flow_core_multi_symbol` |
| SOL | 15m | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 1,632 | 0 | 1,632 | `money_flow_core_multi_symbol` |
| SOL | 1h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 336 | 0 | 336 | `money_flow_core_multi_symbol` |
| SOL | 1h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 408 | 0 | 408 | `money_flow_core_multi_symbol` |
| SOL | 4h | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | 84 | 0 | 84 | `money_flow_core_multi_symbol` |
| SOL | 4h | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | 102 | 0 | 102 | `money_flow_core_multi_symbol` |

Example import command shape:

```bash
DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/btc_15m_core_window_1.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_offline_btc_15m_core_window_1
```

## Evidence Status

Status is `insufficient_data`.

No canonical evidence packs were generated because the intended local DB is migrated and ready, but contains zero canonical candles and no symbol/instrument rows for BTC, ETH, or SOL. The founder cannot yet review real Money Flow evidence for paper-trading design from this local database.

Next manual action: acquire timezone-explicit public/offline BTC, ETH, and SOL candle files for the required 15m, 1h, and 4h windows, import them with the hardened importer, rerun the canonical audit, and generate evidence packs only if the audit reports sufficient data.

## Boundaries

- This report is not paper trading.
- This report is not live execution.
- This report is not proof of profitability.
- This report is not a strategy recommendation.
- No private exchange endpoints, order endpoints, routing behavior, or live artifacts were used.
