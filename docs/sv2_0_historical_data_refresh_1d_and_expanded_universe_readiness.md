# SV2.0 Historical Data Refresh + 1D + Expanded Universe Readiness

Recorded at: `2026-05-11T23:01:36Z`

Status: `sv2_0_1_truth_hotfixed_staged_not_canonical`

SV2.0 added `sleeve_1d` as a real Money Flow sleeve and refreshed the requested expanded Hyperliquid public-mainnet candle universe. SV2.0.1 corrects the evidence/data truth labels: the refreshed candles are fetched, normalized, and staged for replay, but they are not DB-imported through the canonical hardened importer and are not canonical-evidence-ready.

No orders were submitted. No private, signed, order, testnet-strategy-truth, API-key, paper/live execution, SOR, fanout, CBBO, target-reselection, or route-executor behavior was added.

## Scope

- Money Flow version: `money_flow_v1_2`.
- Sleeve set: `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, `sleeve_1d`.
- Internal timeframe values: `15m`, `1h`, `4h`, `1d`.
- Dashboard/display label: `1D`.
- Requested universe: BTC / ETH / SOL / XRP / DOGE / HYPE / BNB / SUI / AVAX / SHIB.
- Source: Hyperliquid public mainnet `POST https://api.hyperliquid.xyz/info`, `type = candleSnapshot`.
- Testnet market data is not strategy truth.

## Market Identity

| Requested | Resolved venue symbol | Supported | Notes |
|---|---|---|---|
| BTC | BTC | yes | `symbol_supported` |
| ETH | ETH | yes | `symbol_supported` |
| SOL | SOL | yes | `symbol_supported` |
| XRP | XRP | yes | `symbol_supported` |
| DOGE | DOGE | yes | `symbol_supported` |
| HYPE | HYPE | yes | `symbol_supported` |
| BNB | BNB | yes | `symbol_supported` |
| SUI | SUI | yes | `symbol_supported` |
| AVAX | AVAX | yes | `symbol_supported` |
| SHIB | kSHIB | yes | `venue_symbol_alias_detected`, explicit alias, not guessed |

## Readiness Truth

The compact JSON summary is at `docs/sv2_0_historical_data_refresh_summary.json`.

| Field | Truth |
|---|---|
| Requested datasets | 40 rows: 10 symbols x 4 timeframes |
| `15m` Jan 2025 target | not met for all 10 symbols; Hyperliquid public 5000-candle limit |
| `1h` Jan 2025 target | not met for all 10 symbols; Hyperliquid public 5000-candle limit |
| `4h` Jan 2025 target | met for all 10 symbols |
| `1d` Jan 2025 target | met for all 10 symbols |
| `fetched` | true for all 40 rows |
| `normalized` | true for all 40 rows |
| `staged_for_replay` | true for all 40 rows |
| `db_imported` | false for all 40 rows |
| `canonical_evidence_ready` | false for all 40 rows |
| `evidence_ready` | false for all 40 rows |

Reason codes added by SV2.0.1 include:

- `historical_staged_for_replay_only`
- `db_import_not_attempted`
- `canonical_hardened_import_not_run`
- `canonical_sv2_evidence_packs_missing`

## Close-Slot Truth

SV2.0.1 normalizes Hyperliquid candle close slots to exact `(start_at, end_at]` boundaries. The generated readiness rows no longer use `.999Z` venue closes as canonical `close_time`.

Examples:

- `1d`: open `2025-01-01T00:00:00Z`, close `2025-01-02T00:00:00Z`.
- `4h`: open `2025-01-01T00:00:00Z`, close `2025-01-01T04:00:00Z`.

## Canonical Evidence Readiness

Status: `blocked`

Canonical SV2 evidence packs are not generated from this staged summary. Compact replay/evidence rows are provisional founder-readable rows only and must not be labeled canonical evidence.

Blocked reason:

```text
canonical_sv2_evidence_packs_missing
db_imported_false_for_staged_summary
compact_replay_rows_not_canonical_evidence
```

## Boundary Confirmation

SV2.0/SV2.0.1 remains Strategy Validation only. It submits no orders, uses no API keys, calls no private/signed/order endpoints, and does not use Hyperliquid testnet data as strategy truth.
