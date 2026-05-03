# SV1.8 Historical Data Bootstrap And First Real Evidence Review

SV1.8 is a research-only historical-data bootstrap check for canonical Money Flow evidence review. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, create paper/live trading artifacts, call exchanges, route, submit, or approve paper trading.

## Evidence Status

- Status: `insufficient_data`
- Evidence packs generated: `0`
- Canonical campaigns audited:
  - `configs/strategy_validation/campaigns/money_flow_core_btc.json`
  - `configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json`
- Founder review state: not ready for evidence review because the reachable local DB is not migrated and has no persisted canonical candles.

## DB Target Findings

SV1.8 checked both the default configured DB and the explicit local Postgres override used in SV1.7.

| DB target | reachable | schema status | alembic table | candles table | candle count | result |
| --- | --- | --- | --- | --- | --- | --- |
| `postgresql+psycopg://money_flow:***@postgres:5432/money_flow` | `false` | `database_unreachable` | `false` | `false` | `null` | blocked because host `postgres` is not resolvable in this shell |
| `postgresql+psycopg://postgres:***@127.0.0.1:54322/postgres` | `true` after sandbox escalation | `schema_missing` | `false` | `false` | `null` | blocked because the reachable DB is not a migrated Money Flow schema |

The repo migration head detected by the status check is `20260430_0025`.

## Canonical Campaign Audit Findings

The local reachable DB has no `candles` table, so campaign rows were blocked as schema/data-readiness gaps.

| campaign | rows checked | blocked rows | impacted runs | blocked reasons |
| --- | ---: | ---: | ---: | --- |
| `money_flow_core_btc` | `6` | `6` | `72` | `alembic_version_table_missing`, `candles_table_missing`, `schema_missing` |
| `money_flow_core_multi_symbol` | `18` | `18` | `216` | `alembic_version_table_missing`, `candles_table_missing`, `schema_missing` |

Missing data still required before canonical evidence can run:

- Symbols: `BTC`, `ETH`, `SOL`
- Components/timeframes: `sleeve_15m`, `sleeve_1h`, `sleeve_4h`
- Windows: all canonical Jan 2026 campaign windows
- Required table: `candles`
- Required migration state: Alembic current at repo head

## Commands

Check only DB/schema/candle readiness:

```bash
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --db-status-only \
  --format markdown
```

Run canonical evidence review against an explicit local DB target:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=postgres \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --format both \
  --review-output-dir /tmp/money-flow-sv1.8-local-db-review
```

Apply migrations to the intended Money Flow DB before importing candles:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=postgres \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python -m alembic upgrade head
```

Import public/offline historical candles after the DB is migrated:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=postgres \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/BTC_M15.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_offline_btc_m15
```

Repeat imports for each canonical symbol/timeframe file. The SV1.5.1 importer rejects malformed OHLCV rows, wrong timeframe durations, identity conflicts, and invalid partial files.

Generate evidence packs only after data-readiness audits are clean:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=postgres \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --generate-evidence-packs \
  --format both \
  --review-output-dir /tmp/money-flow-canonical-evidence-review
```

## Evidence-Pack Result

No evidence packs were generated in SV1.8 because the reachable local DB is not migrated and has no `candles` table. This is a historical-data readiness gap, not a Money Flow strategy result.

## Manual Review Notes

- `insufficient_data` means no founder/operator strategy conclusion should be drawn.
- `partial_evidence_ready_with_data_gaps` should be used only if at least one canonical campaign generates a pack while another remains blocked.
- `ready_for_founder_review` requires generated packs from sufficient persisted data and still does not approve paper trading.
- Backtest evidence is not proof of future profitability.
- Paper trading remains deferred until founder/operator review of real evidence explicitly justifies a new phase.
