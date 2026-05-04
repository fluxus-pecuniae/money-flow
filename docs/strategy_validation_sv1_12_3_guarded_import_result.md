# SV1.12.3 Guarded Canonical Candle Import Result

SV1.12.3 is research-only. It can seed explicitly operator-verified non-trading market identity and run guarded canonical candle import only after all 18 timezone-explicit files pass requirement-aware preflight. It does not generate evidence packs, approve paper trading, route, submit, or call exchange adapters.

## Summary

- Generated at UTC: `2026-05-04T22:13:39+00:00`
- Final status: `identity_missing`
- SV1.13 evidence review can proceed: `False`
- Environment: `testnet`
- Venue: `hyperliquid`
- Operator verified: `False`
- Verified by: `None`
- Offline market identity values checked: `False`
- Identity seed requested: `False`
- Identity seed attempted: `False`
- Identity seeded: `False`
- Identity seed status: `not_requested`
- Input files seen: `0`
- Missing files: `18`
- Import attempted: `False`
- Import completed: `False`
- Bundle final status: `import_blocked`
- Bundle failure policy: `explicit_partial_with_resume`
- Partial persistence occurred: `False`
- Rows inserted: `0`
- Rows updated: `0`
- Rows unchanged: `0`
- Candles imported: `False`
- Evidence packs generated: `False`
- Reason codes: `['canonical_candle_files_missing', 'canonical_candle_import_preflight_not_ready', 'canonical_candle_import_requires_requirement_aware_preflight', 'canonical_candle_requirement_preflight_incomplete', 'input_requirement_mapping_missing', 'missing_instrument', 'missing_requirement_blocked', 'missing_symbol_mapping', 'operator_verified_market_identity_not_ready', 'operator_verified_research_market_identity_not_ready', 'requirement_mapping_incomplete', 'requirement_missing_input_file', 'sv1123_guarded_import_not_ready', 'unknown_instrument_key']`
- Warnings: `['canonical_candle_files_not_supplied', 'input_requirement_mapping_missing', 'market_identity_seed_not_requested']`

## Founder/Operator Conclusion

SV1.12.3 did not seed identity and did not import candles. The intended local `money_flow` DB is reachable and migrated/current, but explicit operator verification was not supplied, BTC/ETH/SOL research market identity rows are absent, and no timezone-explicit canonical candle files were found in the repo/session. SV1.13 evidence review cannot proceed until operator-verified non-trading research identity exists and all 18 canonical files are present, one-to-one mapped, requirement-aware preflighted, and guarded-imported.

## DB And Schema

- DB target: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`
- DB reachable: `True`
- Target role: `configured_money_flow_database`
- Intended strategy-validation DB: `True`
- Schema status: `migrated_schema_ready`
- Migrations current: `True`
- Required tables missing: `[]`
- Persisted candle count before attempt: `0`

## Market Identity

| symbol | instrument key | status | strategy eligible | trading eligible | verified by | reason codes |
| --- | --- | --- | --- | --- | --- | --- |
| `BTC` | `perpetual:linear:BTC:USDC:USDC` | `missing_market_identity` | `None` | `None` | `None` | `['missing_instrument', 'missing_symbol_mapping']` |
| `ETH` | `perpetual:linear:ETH:USDC:USDC` | `missing_market_identity` | `None` | `None` | `None` | `['missing_instrument', 'missing_symbol_mapping']` |
| `SOL` | `perpetual:linear:SOL:USDC:USDC` | `missing_market_identity` | `None` | `None` | `None` | `['missing_instrument', 'missing_symbol_mapping']` |

## File Availability

- Canonical requirements seen: `18` / `18`

### Present Files

- None.

### Missing Files

- `hyperliquid_btc_15m_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_btc_15m_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_btc_1h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_btc_1h_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_btc_4h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_btc_4h_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_eth_15m_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_eth_15m_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_eth_1h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_eth_1h_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_eth_4h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_eth_4h_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_sol_15m_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_sol_15m_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_sol_1h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_sol_1h_20260115_000000z_20260201_000000z.csv`
- `hyperliquid_sol_4h_20260101_000000z_20260115_000000z.csv`
- `hyperliquid_sol_4h_20260115_000000z_20260201_000000z.csv`

## Preflight And Import

- Preflight ready: `False`
- Preflight reason codes: `['input_requirement_mapping_missing', 'missing_instrument', 'requirement_mapping_incomplete', 'requirement_missing_input_file', 'unknown_instrument_key']`
- Imported requirement IDs: `[]`
- Failed requirement IDs: `[]`
- Missing requirement IDs: `['BTC|perpetual:linear:BTC:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344', 'BTC|perpetual:linear:BTC:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632', 'BTC|perpetual:linear:BTC:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336', 'BTC|perpetual:linear:BTC:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408', 'BTC|perpetual:linear:BTC:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84', 'BTC|perpetual:linear:BTC:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102', 'ETH|perpetual:linear:ETH:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344', 'ETH|perpetual:linear:ETH:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632', 'ETH|perpetual:linear:ETH:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336', 'ETH|perpetual:linear:ETH:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408', 'ETH|perpetual:linear:ETH:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84', 'ETH|perpetual:linear:ETH:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102', 'SOL|perpetual:linear:SOL:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344', 'SOL|perpetual:linear:SOL:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632', 'SOL|perpetual:linear:SOL:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336', 'SOL|perpetual:linear:SOL:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408', 'SOL|perpetual:linear:SOL:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84', 'SOL|perpetual:linear:SOL:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102']`
- Safe rerun/resume: If partial persistence occurred, fix failed or missing files and rerun the guarded bundle import. Candle upsert is duplicate-safe for the same identity, but SV1.13 evidence review must not proceed until bundle_import_final_status is canonical_import_complete.

## File Import Results

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `BTC|perpetual:linear:BTC:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102`
- Symbol: `BTC`
- Instrument key: `perpetual:linear:BTC:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `ETH|perpetual:linear:ETH:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102`
- Symbol: `ETH`
- Instrument key: `perpetual:linear:ETH:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|15m|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|1344`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|15m|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|1632`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `15m`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|1h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|336`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|1h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|408`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `1h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|4h|2026-01-01T00:00:00+00:00|2026-01-15T00:00:00+00:00|84`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

### `<missing input file>`

- Requirement identifier: `SOL|perpetual:linear:SOL:USDC:USDC|4h|2026-01-15T00:00:00+00:00|2026-02-01T00:00:00+00:00|102`
- Symbol: `SOL`
- Instrument key: `perpetual:linear:SOL:USDC:USDC`
- Timeframe: `4h`
- Import attempted: `False`
- Import succeeded: `False`
- File status: `missing_requirement_blocked`
- Reason codes: `['requirement_missing_input_file', 'missing_requirement_blocked']`

## Research Boundary

- Creates live artifacts: `False`
- Calls exchange adapters: `False`
- Calls private exchange endpoints: `False`
- Calls exchange order endpoints: `False`
- No evidence packs are generated in SV1.12.3.
- SV1.13 evidence review remains deferred unless final status is `canonical_import_complete`.
