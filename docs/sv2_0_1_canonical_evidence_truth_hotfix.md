# SV2.0.1 Canonical Evidence Truth Hotfix

Recorded at: `2026-05-11T23:01:36Z`

Status: `implemented_with_canonical_evidence_blocked`

SV2.0.1 fixes P1 evidence/data/runtime truth issues found after SV2.0. It does not optimize Money Flow, does not add variants, does not submit orders, does not call private/signed/order endpoints, does not use API keys, and does not use Hyperliquid testnet prices as strategy truth.

Live trading is not approved.

## Summary

| Area | Status | Result |
|---|---|---|
| Open-position accounting | implemented | Compact SV2 rows now count entry fee at open and force-close final open positions at dataset end with explicit fields. |
| Close-time normalization | implemented | Hyperliquid `.999Z` close timestamps are normalized to exact canonical `(start_at, end_at]` close slots; raw venue close can be preserved on normalized candle rows. |
| Canonical evidence packs | blocked | No canonical SV2 pack paths exist yet because refreshed public candles are staged for replay only, not DB-imported through the hardened importer. |
| Import/staging truth | implemented | Summary rows now split `fetched`, `normalized`, `staged_for_replay`, `db_imported`, and `canonical_evidence_ready`. |
| Sleeve allocation | implemented | Runtime sleeve allocations are `0.25` each for `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, and `sleeve_1d`; enabled sum must be <= `1.0`. |
| Timeframe canonicalization | implemented | Internal/storage/campaign value is `1d`; dashboard/display label is `1D`. |
| Missing indicators | implemented | Missing EMA/RSI/MACD fields produce invalid input reason codes rather than defaulting to zero. |
| Existing sleeve drift check | verified | 15m / 1h / 4h rule settings remain unchanged except the runtime allocation budget. |

## Open-Position Accounting Fix

Status: `implemented`

The compact SV2 helper now:

- deducts entry fees when a position opens;
- tracks mark-to-market drawdown while a position remains open;
- force-closes any final open position at dataset end;
- reports `open_position_at_end`, `forced_close_applied`, `mark_to_market_applied`, `final_mtm_price`, `forced_close_price`, `forced_close_time`, and `open_position_unrealized_pnl`;
- labels compact rows as `compact_provisional_replay_not_canonical_evidence`.

The refreshed compact summary contains 40 rows, with 20 rows requiring dataset-end force-close. These compact rows are still not canonical evidence packs.

## Close-Time Normalization Fix

Status: `implemented`

Hyperliquid public `candleSnapshot` close/end values such as `23:59:59.999Z` and `03:59:59.999Z` are no longer used as canonical close slots. Canonical close time is now:

```text
close_time = open_time + timeframe_duration
```

Examples:

- `1d`: `2025-01-01T00:00:00Z -> 2025-01-02T00:00:00Z`
- `4h`: `2025-01-01T00:00:00Z -> 2025-01-01T04:00:00Z`
- `1h`: `2025-01-01T00:00:00Z -> 2025-01-01T01:00:00Z`
- `15m`: `2025-01-01T00:00:00Z -> 2025-01-01T00:15:00Z`

Readiness and coverage math use canonical close slots.

## Canonical Evidence Status

Status: `blocked`

Canonical SV2 evidence pack generation remains blocked with:

```text
canonical_sv2_evidence_packs_missing
db_imported_false_for_staged_summary
compact_replay_rows_not_canonical_evidence
```

Reason: the refreshed SV2.0.1 candle data was fetched and normalized from Hyperliquid public mainnet `candleSnapshot`, then staged in `docs/sv2_0_historical_data_refresh_summary.json`. It has not been upserted through the canonical hardened candle importer into the strategy-validation DB. Therefore compact replay rows cannot be called final canonical evidence.

Evidence pack paths: none.

SOR-EV1 status: `blocked_until_canonical_sv2_evidence_packs_exist_or_the_team_accepts_staged_compact_rows_as_noncanonical_input`.

## Import / Staging Truth

Status: `implemented`

All 40 refreshed dataset rows now report:

- `data_available = true`
- `fetched = true`
- `normalized = true`
- `staged_for_replay = true`
- `db_imported = false`
- `canonical_evidence_ready = false`
- `evidence_ready = false`

The legacy `imported` compatibility field mirrors `db_imported`, so staged-only rows cannot report `imported=true`.

## Sleeve Allocation Fix

Status: `implemented`

Runtime allocation defaults:

| Sleeve | Allocation |
|---|---:|
| `sleeve_15m` | `0.25` |
| `sleeve_1h` | `0.25` |
| `sleeve_4h` | `0.25` |
| `sleeve_1d` | `0.25` |

Enabled allocation sum is validated as `<= 1.0`.

Evidence behavior is unchanged: each independent evidence/scenario run still starts from `10000 USDC` with `capital_sizing_mode = dynamic_equity_pct` unless explicitly configured as a combined multi-sleeve account simulation.

## Missing Indicator Fix

Status: `implemented`

Required fields are:

- EMA5
- EMA10
- SMA20
- RSI
- MACD
- MACD signal
- MACD histogram

Missing, `None`, or non-finite values now produce reason codes such as `missing_indicator_field`, `missing_rsi`, `missing_macd`, `missing_ema5`, and `invalid_indicator_snapshot`. An open position with missing indicators now returns invalid/no-op instead of false-closing or reducing because missing values became zero.

## SHIB / kSHIB Status

Status: `verified`

`SHIB` remains represented as requested symbol `SHIB` and resolved Hyperliquid venue symbol `kSHIB` with `venue_symbol_alias_detected`. This alias is explicit and not guessed.

## No-Order / No-Live Confirmation

Status: `verified`

SV2.0.1 submitted no orders, created no order controls, used no API keys, called no private/signed/order endpoints, and did not use Hyperliquid testnet data as strategy truth.

## Remaining Blockers Before SOR-EV1

- Canonical SV2 evidence packs are still missing.
- Refreshed SV2 public candle data is staged-only and must be imported through the canonical hardened importer before final canonical evidence can be generated.
- SOR-EV1 should remain blocked if it requires canonical SV2 evidence as input.
