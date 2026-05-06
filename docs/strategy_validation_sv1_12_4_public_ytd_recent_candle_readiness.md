# SV1.12.4 Public YTD/Recent Hyperliquid Candle Readiness

This is a research-only data-preparation report for the next Strategy Validation evidence work. It verifies public Hyperliquid BTC/ETH/SOL perpetual USDC identity, replaces the January-only public-data plan with a public-data-friendly YTD/recent plan, records the local CSV files produced from public `candleSnapshot`, and reports the remaining import blocker.

It does not seed identity, import candles, generate evidence packs, approve paper trading, enable strategy/trading eligibility, submit orders, call private endpoints, or call signed endpoints.

## Summary

- Verification timestamp UTC: `2026-05-05T07:26:25Z`
- Public identity source: `POST https://api.hyperliquid.xyz/info` with `{"type":"meta"}`
- Public candle source: `POST https://api.hyperliquid.xyz/info` with `{"type":"candleSnapshot", ...}`
- Official docs checked:
  - Hyperliquid Info endpoint / `meta` / `candleSnapshot`: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
  - Hyperliquid perpetual `meta`: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals
  - Hyperliquid asset IDs: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids
  - Hyperliquid tick and lot size: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size
- Public `meta` response hash: `5415a7bf4819aaf91c5893d4040f21f4480411b4feb0f75217588dc92f676b63`
- Identity verified from public metadata: `BTC=true`, `ETH=true`, `SOL=true`
- Identity seeded in DB: `false`
- Strategy/trading eligibility in manifest: `false` for all three symbols
- Public campaign config: `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json`
- Local candle output directory: `/tmp/money-flow-sv1124-public-ytd-recent/csv`
- Files expected in the new public campaign: `9`
- Files produced locally: `9`
- Files preflight-passed: `0`
- Ready for guarded import: `false`

## Identity Verification

The public `meta` response matched the previously updated manifest. Hyperliquid docs state that perp asset IDs are the index of the coin in the `meta` universe. BTC/ETH/SOL remain normal first-dex perp names rather than builder-deployed `{dex}:{coin}` names.

| symbol | instrument_key | asset id / meta index | szDecimals | quantity_step_size | maxLeverage | marginTableId | price_tick_size used in manifest | active |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `BTC` | `perpetual:linear:BTC:USDC:USDC` | `0` | `5` | `0.00001` | `40` | `56` | `0.1` | `true` |
| `ETH` | `perpetual:linear:ETH:USDC:USDC` | `1` | `4` | `0.0001` | `25` | `55` | `0.01` | `true` |
| `SOL` | `perpetual:linear:SOL:USDC:USDC` | `5` | `2` | `0.01` | `20` | `54` | `0.0001` | `true` |

Uncertainty remains the same as the SV1.12.x report:

- Hyperliquid `meta` does not expose a simple fixed `price_tick_size`. The manifest uses the repo Hyperliquid adapter convention derived from the official documented perp price precision bound: `10^-(6 - szDecimals)`.
- Hyperliquid `meta` does not expose a separate `min_order_size`. The manifest uses `quantity_step_size` as the research import minimum. This does not make symbols trading eligible.
- `is_active=true` is inferred from presence in first-dex perp `meta` without `isDelisted`.

## Data Plan

The January-only public plan is no longer the public Hyperliquid first-evidence baseline. Public `candleSnapshot` returned no January 2026 `15m` rows in the prior research pass, and Hyperliquid documents that only the most recent `5000` candles are available.

January 2026 remains an archival/vendor-data-required campaign. The existing January configs are retained and labeled as archival/vendor-data-required:

- `configs/strategy_validation/campaigns/money_flow_core_btc.json`
- `configs/strategy_validation/campaigns/money_flow_core_multi_symbol.json`

The new public-data-friendly campaign uses:

- `1h` and `4h`: `2026-01-01T00:00:00Z -> 2026-05-05T00:00:00Z`
- `15m`: `2026-03-15T00:00:00Z -> 2026-05-05T00:00:00Z`

The initially suggested `15m` fixed window `2026-03-14T00:00:00Z -> 2026-05-05T00:00:00Z` returned only `4978` raw rows and began at the `2026-03-14T04:00:00Z` close, leaving the first 15 expected close slots unavailable. The selected `2026-03-15T00:00:00Z -> 2026-05-05T00:00:00Z` window is 51 days, stays within public availability, and produced complete close-slot coverage.

All logical windows use `(start_at, end_at]`: candle closes exactly at the start are excluded, and closes on or before the end are included. Hyperliquid may return a raw candle whose open equals `endTime`; those rows close after the logical end and were excluded from the canonical CSVs.

## Candle File Readiness

Each produced file uses:

```text
symbol,instrument_key,open_time,close_time,open,high,low,close,volume,trade_count
```

Timestamps are timezone-explicit UTC ISO-8601 strings ending in `Z`.

| filename | symbol | timeframe | logical window | rows expected | rows found | source | sha256 | preflight status |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `hyperliquid_btc_15m_20260315_000000z_20260505_000000z.csv` | `BTC` | `15m` | `(2026-03-15T00:00:00Z, 2026-05-05T00:00:00Z]` | `4896` | `4896` | Hyperliquid public `candleSnapshot` | `ffa1b6481e300b050dca1bcf15a63694f4f413f2ce0a1ea3d7c88398e45d2a11` | blocked: DB identity missing |
| `hyperliquid_btc_1h_20260101_000000z_20260505_000000z.csv` | `BTC` | `1h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `2976` | `2976` | Hyperliquid public `candleSnapshot` | `9d2e4d1f07f30e51f7c34ae0d438e6bbbac762ef0f82ac59350a84bb49dbde5e` | blocked: DB identity missing |
| `hyperliquid_btc_4h_20260101_000000z_20260505_000000z.csv` | `BTC` | `4h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `744` | `744` | Hyperliquid public `candleSnapshot` | `0bdb5576340150b4ff4b8d79d99330b579dac5575021109e0e33b20e17ab9635` | blocked: DB identity missing |
| `hyperliquid_eth_15m_20260315_000000z_20260505_000000z.csv` | `ETH` | `15m` | `(2026-03-15T00:00:00Z, 2026-05-05T00:00:00Z]` | `4896` | `4896` | Hyperliquid public `candleSnapshot` | `391f60f195fe3e7719b85909fe1c199be8584662b797c1e1ba633524a1c4c902` | blocked: DB identity missing |
| `hyperliquid_eth_1h_20260101_000000z_20260505_000000z.csv` | `ETH` | `1h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `2976` | `2976` | Hyperliquid public `candleSnapshot` | `b46d0c880c31947dfc00c7afc0be016fecb554240130b77af060324fdc7a8de3` | blocked: DB identity missing |
| `hyperliquid_eth_4h_20260101_000000z_20260505_000000z.csv` | `ETH` | `4h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `744` | `744` | Hyperliquid public `candleSnapshot` | `6d49723317d533d551bf7394e643918ea5ee606d2980bf74ff2400baba758de5` | blocked: DB identity missing |
| `hyperliquid_sol_15m_20260315_000000z_20260505_000000z.csv` | `SOL` | `15m` | `(2026-03-15T00:00:00Z, 2026-05-05T00:00:00Z]` | `4896` | `4896` | Hyperliquid public `candleSnapshot` | `e7db14c5347ef5f1ced8263f4856874a786056381388df485321703dc5edbe51` | blocked: DB identity missing |
| `hyperliquid_sol_1h_20260101_000000z_20260505_000000z.csv` | `SOL` | `1h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `2976` | `2976` | Hyperliquid public `candleSnapshot` | `9d27049f0eb6e41e2552d80aa146b06c153c8becc1c171de06c8b36d49fd1168` | blocked: DB identity missing |
| `hyperliquid_sol_4h_20260101_000000z_20260505_000000z.csv` | `SOL` | `4h` | `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]` | `744` | `744` | Hyperliquid public `candleSnapshot` | `af3125798f55058218d402787525a41095781d08abeb150bc6efd59d68c6c160` | blocked: DB identity missing |

Local provenance files:

- `/tmp/money-flow-sv1124-public-ytd-recent/raw`
- `/tmp/money-flow-sv1124-public-ytd-recent/csv`
- `/tmp/money-flow-sv1124-public-ytd-recent/summary_public_ytd_recent_9.json`
- `/tmp/money-flow-sv1124-public-ytd-recent/requirements_public_ytd_recent_9.json`
- `/tmp/money-flow-sv1124-public-ytd-recent/preflight/candle_import_preflight_concise.json`

## Preflight

Requirement-aware preflight was run against all 9 files and their one-to-one requirement JSON. It exited `1` as expected because the intended DB does not yet contain operator-verified BTC/ETH/SOL research identity rows.

Summary:

- Input files seen: `9`
- Input rows seen: `25848`
- Requirements seen: `9`
- Ready: `false`
- Reason codes: `missing_instrument`, `unknown_instrument_key`, `requirement_market_identity_not_ready`, `requirement_actual_candle_count_mismatch`, `requirement_missing_close_time_slots`

The apparent requirement count/missing-slot reason codes are downstream of identity resolution: row parsing fails before parsed close times can be accepted because the DB does not know the instrument keys yet. The local transformation summary independently reports exact expected rows and zero missing/extra close slots for all 9 produced files.

## Import Readiness

- Files expected: `9`
- Files produced: `9`
- Files preflight-passed: `0`
- Ready for guarded import: `false`
- Remaining blocker: operator-approved non-dry-run seed of public-verified, non-trading BTC/ETH/SOL research identity.

Do not run guarded import until identity rows are operator-verified and the same 9 files pass requirement-aware preflight. Do not generate evidence packs until guarded import is complete and post-import data-readiness audits are clean.

## Commands Run

```bash
curl -sS https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  -d '{"type":"meta"}' \
  -o /tmp/money-flow-sv1124-public-ytd-recent/raw/hyperliquid_meta_20260505.json

curl -sS https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"15m","startTime":1773532800000,"endTime":1777939200000}}' \
  -o /tmp/money-flow-sv1124-public-ytd-recent/raw/hyperliquid_btc_15m_20260315_20260505.json

curl -sS https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"1h","startTime":1767225600000,"endTime":1777939200000}}' \
  -o /tmp/money-flow-sv1124-public-ytd-recent/raw/hyperliquid_btc_1h_20260101_20260505.json

curl -sS https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"4h","startTime":1767225600000,"endTime":1777939200000}}' \
  -o /tmp/money-flow-sv1124-public-ytd-recent/raw/hyperliquid_btc_4h_20260101_20260505.json
```

The ETH and SOL requests used the same payload shape, replacing `coin` and output filename. An initial `15m` probe for `2026-03-14T00:00:00Z -> 2026-05-05T00:00:00Z` was also run and rejected as the selected logical window because it did not include the first expected close slots.

Requirement-aware preflight command:

```bash
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --environment testnet \
  --venue hyperliquid \
  --requirement-json /tmp/money-flow-sv1124-public-ytd-recent/requirements_public_ytd_recent_9.json \
  --format json \
  --output-dir /tmp/money-flow-sv1124-public-ytd-recent/preflight \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_btc_15m_20260315_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_btc_1h_20260101_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_btc_4h_20260101_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_eth_15m_20260315_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_eth_1h_20260101_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_eth_4h_20260101_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_sol_15m_20260315_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_sol_1h_20260101_000000z_20260505_000000z.csv \
  --input /tmp/money-flow-sv1124-public-ytd-recent/csv/hyperliquid_sol_4h_20260101_000000z_20260505_000000z.csv
```

Sanitized DB URL: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`

## Next Step

Founder/operator should approve and run the research-only market identity seed with `operator_verified=true`, `verified_by=<operator-name>`, and strategy/trading eligibility still false. Then rerun requirement-aware preflight for the 9 public-campaign files. If all 9 pass, the guarded import can be considered for this new public-data campaign only. January 2026 `15m` remains a separate archival/vendor/operator-data campaign.
