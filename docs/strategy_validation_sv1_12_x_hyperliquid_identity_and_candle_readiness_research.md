# SV1.12.x Hyperliquid Identity And Candle Readiness Research

This is a research-only data-preparation report for the next guarded Strategy Validation import/evidence phases. It verifies public Hyperliquid BTC/ETH/SOL perpetual USDC identity metadata, prepares the candle files available from public `candleSnapshot`, and records remaining blockers.

It does not seed identity, import candles, generate evidence packs, approve paper trading, enable strategy eligibility, enable trading eligibility, submit orders, call private endpoints, or call signed endpoints.

## Summary

- Verification timestamp UTC: `2026-05-05T05:48:50Z`
- Public identity source: `POST https://api.hyperliquid.xyz/info` with `{"type":"meta"}`
- Official docs checked:
  - Hyperliquid Info endpoint / `meta` / `candleSnapshot`: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
  - Hyperliquid perpetual `meta`: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals
  - Hyperliquid asset IDs: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids
  - Hyperliquid tick and lot size: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size
- Public `meta` response hash: `5415a7bf4819aaf91c5893d4040f21f4480411b4feb0f75217588dc92f676b63`
- Identity verified from public metadata: `BTC=true`, `ETH=true`, `SOL=true`
- Identity seeded in DB: `false`
- Strategy/trading eligibility in manifest: `false` for all three symbols
- Candle files produced locally: `12` / `18`
- Candle files still missing: `6` / `18`, all `15m`
- Requirement-aware preflight status: `blocked`
- Ready for guarded import: `false`

## Identity Verification

Public `meta` confirmed the current main perp universe entries below. Hyperliquid docs state perp asset IDs are the index of the coin in the `meta` universe; therefore BTC/ETH/SOL asset IDs are `0`, `1`, and `5`.

| symbol | instrument_key | asset id / meta index | szDecimals | quantity_step_size | maxLeverage | marginTableId | price_tick_size used in manifest | only_isolated | active |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `BTC` | `perpetual:linear:BTC:USDC:USDC` | `0` | `5` | `0.00001` | `40` | `56` | `0.1` | `false` | `true` |
| `ETH` | `perpetual:linear:ETH:USDC:USDC` | `1` | `4` | `0.0001` | `25` | `55` | `0.01` | `false` | `true` |
| `SOL` | `perpetual:linear:SOL:USDC:USDC` | `5` | `2` | `0.01` | `20` | `54` | `0.0001` | `false` | `true` |

Raw relevant metadata:

```json
{
  "BTC": {"index": 0, "meta": {"name": "BTC", "szDecimals": 5, "maxLeverage": 40, "marginTableId": 56}},
  "ETH": {"index": 1, "meta": {"name": "ETH", "szDecimals": 4, "maxLeverage": 25, "marginTableId": 55}},
  "SOL": {"index": 5, "meta": {"name": "SOL", "szDecimals": 2, "maxLeverage": 20, "marginTableId": 54}}
}
```

Margin table first tiers matched the universe `maxLeverage` fields:

```json
{
  "54": {"description": "tiered 20x (2)", "first_tier": {"lowerBound": "0.0", "maxLeverage": 20}},
  "55": {"description": "tiered 25x", "first_tier": {"lowerBound": "0.0", "maxLeverage": 25}},
  "56": {"description": "tiered 40x", "first_tier": {"lowerBound": "0.0", "maxLeverage": 40}}
}
```

Uncertainty:

- Hyperliquid `meta` does not expose a simple fixed `price_tick_size`. The manifest now uses the repo Hyperliquid adapter convention derived from the official documented perp price precision bound: `10^-(6 - szDecimals)`.
- Hyperliquid `meta` does not expose a separate `min_order_size`. The manifest uses `quantity_step_size` as the research import minimum, matching the existing repo adapter convention. This does not make symbols trading eligible.
- `is_active=true` is inferred because these entries are present in main perp `meta` and do not carry `isDelisted`.
- `is_builder_deployed=false` is inferred because BTC/ETH/SOL are in the first perp dex `meta` and do not use the builder-deployed `{dex}:{coin}` name format.

## Candle File Readiness

Public `candleSnapshot` was queried for BTC, ETH, and SOL over `2026-01-01T00:00:00Z` through `2026-02-01T00:00:00Z` for `15m`, `1h`, and `4h`. Hyperliquid's docs state only the most recent `5000` candles are available. The January 2026 `15m` windows returned zero rows from the public endpoint on `2026-05-05`; the `1h` and `4h` windows were available and transformed into timezone-explicit canonical CSVs under `/tmp/money-flow-sv112x-candles/`.

Each produced file uses:

```text
symbol,instrument_key,open_time,close_time,open,high,low,close,volume,trade_count
```

Timestamps are UTC ISO-8601 with `Z`, and files were split using the canonical `(start_at, end_at]` close-time convention.

| filename | rows expected | rows found | source | sha256 | preflight status |
| --- | ---: | ---: | --- | --- | --- |
| `hyperliquid_btc_15m_20260101_000000z_20260115_000000z.csv` | `1344` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_btc_15m_20260115_000000z_20260201_000000z.csv` | `1632` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_btc_1h_20260101_000000z_20260115_000000z.csv` | `336` | `336` | Hyperliquid public `candleSnapshot` | `7273d79f701f694a9050ba2db4cdd28a3f9a25863b40c6e4779fe36c47b7da64` | blocked: DB identity missing |
| `hyperliquid_btc_1h_20260115_000000z_20260201_000000z.csv` | `408` | `408` | Hyperliquid public `candleSnapshot` | `1c3270152404ab32d100a5e1bad5c69de62d610db202ababb391f6dc4fdda237` | blocked: DB identity missing |
| `hyperliquid_btc_4h_20260101_000000z_20260115_000000z.csv` | `84` | `84` | Hyperliquid public `candleSnapshot` | `d0672139892851c6e7f5756498a056d59480551589b85d32a76bf1ae4baa0250` | blocked: DB identity missing |
| `hyperliquid_btc_4h_20260115_000000z_20260201_000000z.csv` | `102` | `102` | Hyperliquid public `candleSnapshot` | `1d508269651121e3fd0a952192ecf9bb554e790cd9b986997b753e0eb7152b8c` | blocked: DB identity missing |
| `hyperliquid_eth_15m_20260101_000000z_20260115_000000z.csv` | `1344` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_eth_15m_20260115_000000z_20260201_000000z.csv` | `1632` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_eth_1h_20260101_000000z_20260115_000000z.csv` | `336` | `336` | Hyperliquid public `candleSnapshot` | `cc54f1a859d4be3e05b47a182e127dca21574ea556acb24d1577b57e3a3100c0` | blocked: DB identity missing |
| `hyperliquid_eth_1h_20260115_000000z_20260201_000000z.csv` | `408` | `408` | Hyperliquid public `candleSnapshot` | `8f35f0f9586e0c3a511624424fd2e47145332667e7970bee6b9155d996314d4b` | blocked: DB identity missing |
| `hyperliquid_eth_4h_20260101_000000z_20260115_000000z.csv` | `84` | `84` | Hyperliquid public `candleSnapshot` | `242ce3162ac7b55f5e9bc4d9ecfe6651bfdb3808dd4864a1b2f5ab6371e2f6bb` | blocked: DB identity missing |
| `hyperliquid_eth_4h_20260115_000000z_20260201_000000z.csv` | `102` | `102` | Hyperliquid public `candleSnapshot` | `973aa847416681daf8153b5ac02daf68b2bf7706a0200f3ef19ccdecf571abeb` | blocked: DB identity missing |
| `hyperliquid_sol_15m_20260101_000000z_20260115_000000z.csv` | `1344` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_sol_15m_20260115_000000z_20260201_000000z.csv` | `1632` | `0` | Hyperliquid public `candleSnapshot` | n/a | missing: public endpoint returned no rows |
| `hyperliquid_sol_1h_20260101_000000z_20260115_000000z.csv` | `336` | `336` | Hyperliquid public `candleSnapshot` | `cc7f417eeed918e067f565694c1b147501b128ba2a8f7bf62fe14d73bc633700` | blocked: DB identity missing |
| `hyperliquid_sol_1h_20260115_000000z_20260201_000000z.csv` | `408` | `408` | Hyperliquid public `candleSnapshot` | `bab902e7d70213c18c13e6f3424ba8a2980410a8bd3eb3470b702622622fd1d3` | blocked: DB identity missing |
| `hyperliquid_sol_4h_20260101_000000z_20260115_000000z.csv` | `84` | `84` | Hyperliquid public `candleSnapshot` | `eda1f1fbee6cf46e61f594548fa94ba09cb220258d88f11c5b12b7006449ca51` | blocked: DB identity missing |
| `hyperliquid_sol_4h_20260115_000000z_20260201_000000z.csv` | `102` | `102` | Hyperliquid public `candleSnapshot` | `61f5a0f56ce399847d967968741918d1590ab9f40bd0964735d0bdc2d2b75f61` | blocked: DB identity missing |

## Preflight Result

The requirement-aware preflight was run against the 12 generated files and 12 matching canonical requirements. It exited non-zero because the intended DB still lacks BTC/ETH/SOL `InstrumentModel` and `SymbolModel` identity rows. Since identity resolution failed first, requirement coverage was not accepted as import-ready.

Observed preflight summary:

- Input files seen: `12`
- Input rows seen: `2790`
- Requirements seen: `12`
- Overall ready: `false`
- Reason codes: `missing_instrument`, `unknown_instrument_key`, `requirement_market_identity_not_ready`, `requirement_actual_candle_count_mismatch`, `requirement_missing_close_time_slots`
- Generated preflight output: `/tmp/money-flow-sv112x-preflight/candle_import_preflight.json`

## Import Readiness

- All 18 files present: `false`
- All 18 preflight passed: `false`
- Operator-verified identity exists in DB: `false`
- Ready for guarded import: `false`

Remaining blocker: six `15m` files are missing and operator-verified research identity has not been seeded into the intended DB. Guarded import must not run until both are fixed and all 18 files pass requirement-aware preflight.

Recommended next action:

1. Have founder/operator explicitly approve seeding the now-public-verified non-trading research identity values.
2. Seed identity only through the guarded operator-verified path, with `verified_by`.
3. Source the six missing `15m` files from a trusted public historical vendor, founder/operator export, previously recorded Hyperliquid public data, or carefully documented trade-to-OHLCV aggregation.
4. Rerun requirement-aware preflight for all 18 files.
5. Run guarded import only after all 18 files are present and preflight-ready.

## Commands Run

```bash
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"meta"}' -o /tmp/mf_hl_meta.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"1h","startTime":1767225600000,"endTime":1768435200000}}' -o /tmp/mf_hl_btc_1h_probe.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"15m","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_BTC_15m_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"1h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_BTC_1h_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"4h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_BTC_4h_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"ETH","interval":"15m","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_ETH_15m_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"ETH","interval":"1h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_ETH_1h_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"ETH","interval":"4h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_ETH_4h_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"SOL","interval":"15m","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_SOL_15m_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"SOL","interval":"1h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_SOL_1h_jan2026.json
curl -sS https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' -d '{"type":"candleSnapshot","req":{"coin":"SOL","interval":"4h","startTime":1767225600000,"endTime":1769904000000}}' -o /tmp/mf_hl_SOL_4h_jan2026.json
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow .venv/bin/python scripts/check_strategy_validation_import_readiness.py --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json --format json --output-dir /tmp/money-flow-sv112x-readiness-updated
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow .venv/bin/python scripts/preflight_strategy_validation_candle_import.py --environment testnet --venue hyperliquid --requirement-json /tmp/money-flow-sv112x-candles/requirements_12_available.json --format json --output-dir /tmp/money-flow-sv112x-preflight --input /tmp/money-flow-sv112x-candles/hyperliquid_btc_1h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_btc_1h_20260115_000000z_20260201_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_btc_4h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_btc_4h_20260115_000000z_20260201_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_eth_1h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_eth_1h_20260115_000000z_20260201_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_eth_4h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_eth_4h_20260115_000000z_20260201_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_sol_1h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_sol_1h_20260115_000000z_20260201_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_sol_4h_20260101_000000z_20260115_000000z.csv --input /tmp/money-flow-sv112x-candles/hyperliquid_sol_4h_20260115_000000z_20260201_000000z.csv
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow .venv/bin/python scripts/seed_strategy_validation_market_identity.py --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json --dry-run --format json --output-dir /tmp/money-flow-sv112x-identity-dry-run-updated
.venv/bin/python -m json.tool configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json
```
