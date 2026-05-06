# SV1.12.5 Supported Venues Public Candle Readiness

This is a research-only data-preparation report for extending the SV1.12.4 public YTD/recent candle pass across the venue adapters currently supported by the repo registry.

It does not seed identity, import candles, generate evidence packs, approve paper trading, enable strategy/trading eligibility, submit orders, call private endpoints, call signed endpoints, use API keys, or change Money Flow strategy rules.

## Scope

Supported adapter venues considered:

- `hyperliquid`
- `aster`
- `binance`
- `okx`
- `coinbase_advanced_trade`
- `kraken`

Selected logical windows preserve the SV1.12.4 public-data-friendly convention:

- `15m`: `(2026-03-15T00:00:00Z, 2026-05-05T00:00:00Z]`, expected `4896` candles per symbol.
- `1h`: `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]`, expected `2976` candles per symbol.
- `4h`: `(2026-01-01T00:00:00Z, 2026-05-05T00:00:00Z]`, expected `744` candles per symbol.

January 2026 `15m` remains archival/vendor-data-required, not the public first-evidence baseline.

## Public Sources Checked

| venue | public source | market scope used | public result |
| --- | --- | --- | --- |
| `hyperliquid` | `POST https://api.hyperliquid.xyz/info` / `candleSnapshot` | USDC linear perpetual | Already complete in SV1.12.4: 9 files under `/tmp/money-flow-sv1124-public-ytd-recent/csv`; preflight blocked on missing operator-verified DB identity. |
| `aster` | `GET https://fapi.asterdex.com/fapi/v1/klines` | USDT linear perpetual | Complete for all 9 files with native trade counts. |
| `binance` | `GET https://api.binance.com/api/v3/klines` | USDT spot | Complete for all 9 files with native trade counts. |
| `okx` | `GET https://www.okx.com/api/v5/market/history-candles` | USDT linear perpetual swaps | Complete close-slot coverage for all 9 files, but public payload lacks trade count, so not canonical import-ready under the current requirement. |
| `coinbase_advanced_trade` | `GET https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}/candles` | USD spot | Complete close-slot coverage for all 9 files, but public payload lacks trade count, so not canonical import-ready under the current requirement. |
| `kraken` | `GET https://api.kraken.com/0/public/OHLC` | USD spot | Incomplete for all 9 selected windows because public REST OHLC returns only recent rows. |

Official/public docs checked:

- Hyperliquid Info / `candleSnapshot`: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
- Aster API / `fapi/v1/klines`: https://docs.asterdex.com/product/asterex-pro/api/api-documentation
- Coinbase public product candles: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/public/get-public-product-candles
- OKX API market candles/history candles: https://www.okx.com/docs-v5/en/
- Kraken OHLC data: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data/

## Local Outputs

Primary run root:

`/tmp/money-flow-sv1125-supported-venues-public`

Important files:

- Summary/provenance: `/tmp/money-flow-sv1125-supported-venues-public/summary_supported_venues_public.json`
- All generated requirements: `/tmp/money-flow-sv1125-supported-venues-public/requirements_supported_venues_public.json`
- Candidate Aster requirements: `/tmp/money-flow-sv1125-supported-venues-public/requirements_aster_native_count_candidates.json`
- Candidate Binance requirements: `/tmp/money-flow-sv1125-supported-venues-public/requirements_binance_native_count_candidates.json`
- Aster preflight concise summary: `/tmp/money-flow-sv1125-supported-venues-public/preflight/aster_native_count_candidates/candle_import_preflight_concise.json`
- Binance preflight concise summary: `/tmp/money-flow-sv1125-supported-venues-public/preflight/binance_native_count_candidates/candle_import_preflight_concise.json`

Hyperliquid SV1.12.4 outputs remain at:

`/tmp/money-flow-sv1124-public-ytd-recent/csv`

## Venue Readiness Summary

| venue | expected logical files | files produced/found | complete close-slot coverage | candidate canonical files | preflight status | blocker |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `hyperliquid` | 9 | 9 | 9 | 9 | blocked in SV1.12.4 | Operator-verified non-trading identity is missing in DB. |
| `aster` | 9 | 9 | 9 | 9 | blocked | Venue identity rows are missing in DB. |
| `binance` | 9 | 9 | 9 | 9 | blocked | Venue identity rows are missing in DB. |
| `okx` | 9 | 9 | 9 | 0 | not run as canonical | Public source lacks trade count; identity also missing. |
| `coinbase_advanced_trade` | 9 | 9 | 9 | 0 | not run as canonical | Public source lacks trade count; identity also missing. |
| `kraken` | 9 | 9 partial files | 0 | 0 | not run | Public REST OHLC coverage is incomplete for selected windows. |

Across all six supported venues, the logical target set is `54` files. The local public outputs now include:

- `9` Hyperliquid files from SV1.12.4.
- `45` additional files from this pass.
- `36` files with complete close-slot coverage from this pass.
- `18` additional native-trade-count candidate files from this pass: Aster and Binance.
- `0` files passed requirement-aware preflight because no non-Hyperliquid venue identity rows are verified/seeded in the DB, and Hyperliquid remains blocked on operator-verified identity.

## File Readiness Detail

Full hashes and per-file missing-slot details are in:

`/tmp/money-flow-sv1125-supported-venues-public/summary_supported_venues_public.json`

Condensed table:

| filename | venue | symbol | timeframe | expected | found | status |
| --- | --- | --- | --- | ---: | ---: | --- |
| `aster_btc_15m_20260315_000000z_20260505_000000z.csv` | `aster` | `BTC` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `aster_btc_1h_20260101_000000z_20260505_000000z.csv` | `aster` | `BTC` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `aster_btc_4h_20260101_000000z_20260505_000000z.csv` | `aster` | `BTC` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `aster_eth_15m_20260315_000000z_20260505_000000z.csv` | `aster` | `ETH` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `aster_eth_1h_20260101_000000z_20260505_000000z.csv` | `aster` | `ETH` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `aster_eth_4h_20260101_000000z_20260505_000000z.csv` | `aster` | `ETH` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `aster_sol_15m_20260315_000000z_20260505_000000z.csv` | `aster` | `SOL` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `aster_sol_1h_20260101_000000z_20260505_000000z.csv` | `aster` | `SOL` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `aster_sol_4h_20260101_000000z_20260505_000000z.csv` | `aster` | `SOL` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `binance_btc_15m_20260315_000000z_20260505_000000z.csv` | `binance` | `BTC` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `binance_btc_1h_20260101_000000z_20260505_000000z.csv` | `binance` | `BTC` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `binance_btc_4h_20260101_000000z_20260505_000000z.csv` | `binance` | `BTC` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `binance_eth_15m_20260315_000000z_20260505_000000z.csv` | `binance` | `ETH` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `binance_eth_1h_20260101_000000z_20260505_000000z.csv` | `binance` | `ETH` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `binance_eth_4h_20260101_000000z_20260505_000000z.csv` | `binance` | `ETH` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `binance_sol_15m_20260315_000000z_20260505_000000z.csv` | `binance` | `SOL` | `15m` | 4896 | 4896 | candidate; identity preflight blocked |
| `binance_sol_1h_20260101_000000z_20260505_000000z.csv` | `binance` | `SOL` | `1h` | 2976 | 2976 | candidate; identity preflight blocked |
| `binance_sol_4h_20260101_000000z_20260505_000000z.csv` | `binance` | `SOL` | `4h` | 744 | 744 | candidate; identity preflight blocked |
| `okx_*` | `okx` | `BTC/ETH/SOL` | `15m/1h/4h` | per window | complete | blocked: public source lacks trade count |
| `coinbase_advanced_trade_*` | `coinbase_advanced_trade` | `BTC/ETH/SOL` | `15m/1h/4h` | per window | complete | blocked: public source lacks trade count |
| `kraken_*` | `kraken` | `BTC/ETH/SOL` | `15m/1h/4h` | per window | partial | blocked: public REST OHLC coverage cap |

## Preflight

Requirement-aware preflight was run for the additional candidate native-trade-count files only:

- `aster`: 9 files, 25,848 rows, `ready=false`
- `binance`: 9 files, 25,848 rows, `ready=false`

Reason codes:

- `missing_instrument`
- `unknown_instrument_key`

This is expected because Strategy Validation identity is currently Hyperliquid-focused and no operator-verified non-trading identity rows exist for Aster or Binance. The preflight did not import candles.

OKX and Coinbase were excluded from canonical preflight because the public candle payloads do not include trade counts. Kraken was excluded because the public REST OHLC endpoint did not provide complete selected-window coverage.

## Commands Run

Representative public probes:

```bash
curl -sS 'https://fapi.asterdex.com/fapi/v1/klines?symbol=BTCUSDT&interval=1h&startTime=1767225600000&endTime=1767232800000&limit=5'
curl -sS 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime=1767225600000&endTime=1767232800000&limit=5'
curl -sS 'https://www.okx.com/api/v5/market/history-candles?instId=BTC-USDT-SWAP&bar=1H&after=1767232800000&limit=5'
curl -sS 'https://api.coinbase.com/api/v3/brokerage/market/products/BTC-USD/candles?start=1767225600&end=1767232800&granularity=ONE_HOUR&limit=5'
curl -sS 'https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60&since=1767225600'
```

Bulk public download/normalization:

```bash
.venv/bin/python scripts/prepare_supported_venue_public_candles.py
```

Requirement-aware preflight, sanitized:

```bash
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=money_flow DB_PASSWORD=<redacted> DB_NAME=money_flow \
  .venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --environment testnet \
  --venue aster \
  --requirement-json /tmp/money-flow-sv1125-supported-venues-public/requirements_aster_native_count_candidates.json \
  --format json \
  --output-dir /tmp/money-flow-sv1125-supported-venues-public/preflight/aster_native_count_candidates \
  --input /tmp/money-flow-sv1125-supported-venues-public/csv/aster/aster_btc_15m_20260315_000000z_20260505_000000z.csv \
  ...
```

The same shape was run for `binance` using `/tmp/money-flow-sv1125-supported-venues-public/requirements_binance_native_count_candidates.json` and the 9 Binance input files.

## Import Readiness

Ready for guarded import: no.

Remaining blockers:

1. Hyperliquid still needs operator-verified non-trading identity seeded in the intended Strategy Validation DB.
2. Aster and Binance need public identity manifests reviewed, operator-verified, and seeded as non-trading/non-strategy-eligible before their candidate files can pass preflight.
3. OKX and Coinbase need either a source with trade counts or an explicit founder/operator decision changing the canonical import contract for trade-count-unavailable public candles.
4. Kraken needs an archive/vendor/operator source for the selected windows, because public REST OHLC does not cover them.

Recommended next action:

Keep Hyperliquid as the nearest import path. For broader venue comparison, verify and seed non-trading Aster/Binance research identity first, then rerun requirement-aware preflight for their 18 candidate files. Treat OKX/Coinbase/Kraken as source-policy/vendor-data follow-ups, not import-ready datasets.
