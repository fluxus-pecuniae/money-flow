# SV1.11.2 Seed And Preflight Governance Hotfix

SV1.11.2 is a narrow Strategy Validation governance hotfix. It imports no candles, generates no evidence packs, changes no Money Flow rules, performs no optimization, recommends no strategy variant, creates no paper/live artifacts, routes nothing, executes nothing, and calls no exchange adapters.

## What Changed

SV1.11.2 closes two pre-import trust gaps before SV1.12:

- The Strategy Validation market-identity seed path can no longer mark `SymbolModel` rows as strategy-eligible or trading-eligible.
- Requirement-aware candle preflight now requires complete one-to-one input-file-to-requirement mapping.

## Research-Only Market Identity

The market-identity seed script remains only for offline/manual Strategy Validation identity rows. It can seed or verify `instruments` and `symbols`, but it cannot promote symbols into trading use.

If a manifest sets either field to `true`, validation fails before any write:

- `is_strategy_eligible=true`
- `is_trading_eligible=true`

Successful writes keep:

- `is_strategy_eligible=false`
- `is_trading_eligible=false`
- `raw_metadata.research_only_market_identity_seed=true`
- `raw_metadata.source=manual_offline_manifest`
- `raw_metadata.operator_verified=true`
- `raw_metadata.verified_by`
- `raw_metadata.verified_at`

If future work needs to promote symbols for trading, that must be a separate explicit operational phase/tool. Strategy Validation seeding is not that tool.

## Complete Requirement-Aware Preflight

Row-level preflight remains useful for file shape, timezone, OHLCV, timeframe, and identity checks. It is still not proof of canonical campaign coverage.

Requirement-aware preflight is the gate before bulk import. When requirement-aware mode is used:

- every input file must map to exactly one requirement
- every supplied requirement must have exactly one input file
- extra unmapped input files block readiness
- missing input files for supplied requirements block readiness
- two files mapped to the same requirement block readiness

Only a complete one-to-one mapping can report `ready_for_import=true`, and only when row-level validation, identity validation, and exact `(start_at, end_at]` close-slot coverage also pass.

## Review JSON Selection

When `--requirements-from-review-json` is used for candle preflight and the review JSON contains both identity and candle import requirements, the preflight now inspects `canonical_candle_import_requirements` first. It falls back to `canonical_market_identity_requirements` only when candle import requirements are absent. Output includes the inspected `requirement_kind`.

## Current Status

SV1.11.2 still leaves first real evidence blocked by missing persisted canonical candles. SV1.12 remains the phase for guarded canonical candle bundle import and first evidence attempt, but only after operator-verified market identity and complete requirement-aware preflight pass.
