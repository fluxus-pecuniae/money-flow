# SV1.11.1 Preflight And Identity Guard Hardening

SV1.11.1 is a narrow SOR P2 hotfix. It is research-only and changes no Money Flow rules, optimization parameters, strategy recommendation language, routing, execution automation, exchange calls, paper trading, live trading, candle imports, or evidence-pack generation.

## What Changed

SV1.11 added market-identity seed/verify tooling and a no-write candle preflight. SV1.11.1 hardens two points before SV1.12:

- Non-dry-run market-identity writes now require explicit operator verification.
- Candle preflight now has a requirement-aware mode that proves a specific file covers a specific canonical candle requirement.

## Operator-Verified Market Identity Writes

Dry-run and verify-only still work without operator verification:

```bash
.venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --dry-run

.venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --verify-only
```

Actual writes require both verification flags:

```bash
.venv/bin/python scripts/seed_strategy_validation_market_identity.py \
  --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json \
  --operator-verified \
  --verified-by "<operator-or-reviewer-name>"
```

Written `symbols.raw_metadata` records `operator_verified`, `verified_by`, `verified_at`, `sv_phase=SV1.11.1`, `research_only_market_identity_seed=true`, and `source=manual_offline_manifest`.

Verification metadata does not make symbols trading-eligible or strategy-eligible. The example manifest keeps `is_trading_eligible=false` and `is_strategy_eligible=false` unless an operator explicitly edits those fields in the manifest.

## Row-Level Preflight Is Not Coverage Proof

The original SV1.11 preflight still validates file shape, OHLCV truth, timezone-explicit timestamps, timeframe duration, and identity mappings without writing candles:

```bash
.venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --input /path/to/btc_15m.csv \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m
```

That row-level mode is useful, but it is not proof that the file satisfies a canonical campaign requirement.

## Requirement-Aware Preflight

Before bulk import in SV1.12, use requirement-aware preflight. A requirement JSON must identify:

- `symbol`
- `instrument_key`
- `timeframe`
- `requested_start_at`
- `requested_end_at`
- `expected_candle_count`
- optional `window_label`

Example:

```bash
.venv/bin/python scripts/preflight_strategy_validation_candle_import.py \
  --input /path/to/btc_15m_window_1.csv \
  --requirement-json /path/to/btc_15m_window_1.requirement.json \
  --environment testnet \
  --venue hyperliquid \
  --timeframe 15m \
  --format markdown
```

Requirement-aware preflight checks that close times exactly cover the canonical `(requested_start_at, requested_end_at]` slots, with no missing, duplicate, or extra close-time slots. Output separates:

- `row_level_ready`
- `identity_ready`
- `requirement_coverage_ready`
- `ready_for_import`

A file can be row-level valid but still fail `requirement_coverage_ready`.

## Current Status

SV1.11.1 imports no candles and generates no evidence packs. SV1.12 remains the phase for guarded canonical candle bundle import and the first evidence attempt, but only after operator-verified market identity and requirement-aware preflight pass for all 18 canonical BTC/ETH/SOL requirements.
