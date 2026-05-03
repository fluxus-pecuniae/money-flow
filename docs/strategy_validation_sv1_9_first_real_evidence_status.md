# SV1.9 First Real Evidence Status

Superseded/clarified by `docs/strategy_validation_sv1_9_1_evidence_target_truth_hotfix.md`: ambiguous or non-intended maintenance DB targets now block evidence-pack generation by default, and timezone-naive candle imports are rejected by default unless a provenance-marked non-canonical override is explicitly used.

SV1.9 is a research-only DB/schema/candle-readiness and first-real evidence-pack attempt for canonical Money Flow campaigns. It does not change Money Flow rules, optimize parameters, recommend a strategy variant, create paper/live artifacts, call exchanges, route, submit, or approve paper trading.

## Evidence Status

- Status: `insufficient_data`
- Evidence packs generated: `0`
- Canonical campaigns audited:
  - `configs/strategy_validation/campaigns/money_flow_core_btc.json`
  - `configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json`
- Top-level live artifacts created: `false`
- Top-level exchange adapters called: `false`
- Founder review state: not ready for evidence review because no accessible migrated DB with canonical candles was available from this shell.

## DB Target Findings

| DB target | target role | intended strategy-validation DB | reachable | schema status | required tables | candle count | result |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `postgresql+psycopg://money_flow:***@postgres:5432/money_flow` | `configured_money_flow_database` | `true` | `false` | `database_unreachable` | `candles`, `instruments`, `symbols` missing because DB is unreachable | `null` | blocked because host `postgres` is not resolvable in this shell |
| `postgresql+psycopg://postgres:***@127.0.0.1:54322/postgres` | `maintenance_database_name_requires_operator_confirmation` | `false` | `false` | `database_unreachable` | `candles`, `instruments`, `symbols` unavailable because DB is unreachable | `null` | blocked because local Postgres on port `54322` refused the connection |

The repo migration head detected by the status check is `20260430_0025`.

SV1.9 did not apply migrations because no intended reachable Money Flow DB target was available. Evidence-pack generation remains blocked unless the target reports `migrated_schema_ready` with current Alembic truth and required `candles`, `instruments`, and `symbols` tables.

## Canonical Campaign Audit Findings

The default configured DB could not be reached, so both canonical campaigns were represented as blocked data-readiness rows rather than strategy results.

| campaign | rows checked | blocked rows | impacted runs | blocked reasons |
| --- | ---: | ---: | ---: | --- |
| `money_flow_core_btc` | `6` | `6` | `72` | `database_unreachable`, `database_host_unresolved`, `schema_not_ready_for_evidence_generation` |
| `money_flow_core_multi_symbol` | `18` | `18` | `216` | `database_unreachable`, `database_host_unresolved`, `schema_not_ready_for_evidence_generation` |

## Missing Candle Requirements

No public/offline candle files were available in the repo/session beyond the campaign JSON configs, so SV1.9 did not import candles.

Unique canonical candle files still needed before the campaigns can be reviewed:

| symbol | timeframe | window | expected candles | file requirement |
| --- | --- | --- | ---: | --- |
| `BTC` | `15m` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `1344` | CSV/JSON rows with `symbol`, `instrument_key`, `open_time`, `close_time`, `open`, `high`, `low`, `close`, `volume`, optional `trade_count` |
| `BTC` | `15m` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `1632` | same schema |
| `BTC` | `1h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `336` | same schema |
| `BTC` | `1h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `408` | same schema |
| `BTC` | `4h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `84` | same schema |
| `BTC` | `4h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `102` | same schema |
| `ETH` | `15m` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `1344` | same schema |
| `ETH` | `15m` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `1632` | same schema |
| `ETH` | `1h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `336` | same schema |
| `ETH` | `1h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `408` | same schema |
| `ETH` | `4h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `84` | same schema |
| `ETH` | `4h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `102` | same schema |
| `SOL` | `15m` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `1344` | same schema |
| `SOL` | `15m` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `1632` | same schema |
| `SOL` | `1h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `336` | same schema |
| `SOL` | `1h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `408` | same schema |
| `SOL` | `4h` | `(2026-01-01T00:00:00Z, 2026-01-15T00:00:00Z]` | `84` | same schema |
| `SOL` | `4h` | `(2026-01-15T00:00:00Z, 2026-02-01T00:00:00Z]` | `102` | same schema |

The BTC-only campaign overlaps with the BTC rows in the multi-symbol campaign. The unique data-acquisition requirement is therefore BTC/ETH/SOL across 15m/1h/4h for the two canonical windows.

## Reproducible Commands

Check the configured DB target:

```bash
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --db-status-only \
  --format markdown
```

Point at the intended local Money Flow DB, then inspect status:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=<user> \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --db-status-only \
  --format markdown
```

Apply migrations only after the DB target is confirmed:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=<user> \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python -m alembic upgrade head
```

Import one public/offline candle file after the DB reports `migrated_schema_ready`:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=<user> \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/import_strategy_validation_candles.py \
  --input /path/to/BTC_15m_2026-01-01_2026-01-15.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --source-label public_offline_btc_15m_jan_1_to_jan_15
```

Generate evidence packs only after audits are clean:

```bash
DB_HOST=127.0.0.1 \
DB_PORT=54322 \
DB_USER=<user> \
DB_PASSWORD=<redacted> \
DB_NAME=<intended_money_flow_db> \
.venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --generate-evidence-packs \
  --format both \
  --review-output-dir /tmp/money-flow-canonical-evidence-review
```

## Evidence-Pack Result

No evidence packs were generated in SV1.9. This is a DB/schema/historical-data readiness gap, not a Money Flow strategy result.

## Manual Review Notes

- `insufficient_data` means no founder/operator strategy conclusion should be drawn.
- `partial_evidence_ready_with_data_gaps` should be used only if at least one canonical campaign generates a pack while another remains blocked or insufficient.
- `ready_for_founder_review` requires generated packs from sufficient persisted data and still does not approve paper trading.
- Backtest evidence is not proof of future profitability.
- Paper trading remains deferred until founder/operator review of real evidence explicitly justifies a new phase.
