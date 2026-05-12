# SV2.0 Money Flow 1D Sleeve + Expanded Universe Evidence Rebuild

Recorded at: `2026-05-11T23:01:36Z`

Status: `superseded_by_sv2_0_2_canonical_evidence_generated`

SV2.0 promotes `1D` from a PT0.0.3 dashboard aggregation into a real Money Flow sleeve: `sleeve_1d`. Money Flow v1.2 is now `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, and `sleeve_1d`. Existing 15m / 1h / 4h sleeve settings remain unchanged. The 1D sleeve settings are an initial baseline and are not optimized.

SV2.0.1 corrects the evidence truth: the committed compact rows are not canonical evidence packs. They are staged, founder-readable, provisional replay/evidence rows generated from Hyperliquid public mainnet candles. SV2.0.2 supersedes the blocked canonical-evidence state by importing normalized supported-symbol candles through the hardened importer and generating canonical evidence packs. Current canonical pack truth is in `docs/sv2_0_2_canonical_sv2_evidence_packs.md`.

No orders were submitted. Live trading is not approved. Testnet market data is not strategy truth. Strategy evidence uses Hyperliquid public mainnet candles only.

## Sleeve Settings

| Sleeve | Internal TF | Display TF | History | RSI band | Overbought | Trim | Max EMA5 extension | MACD |
|---|---|---|---:|---:|---:|---:|---:|---|
| `sleeve_15m` | `15m` | `15m` | 35 | 52-66 | 72 | 78 | 1.8% | required |
| `sleeve_1h` | `1h` | `1h` | 35 | 50-68 | 74 | 80 | 2.0% | required |
| `sleeve_4h` | `4h` | `4h` | 40 | 48-70 | 76 | 82 | 2.5% | required |
| `sleeve_1d` | `1d` | `1D` | 50 | 46-72 | 78 | 84 | 3.0% | required |

The 1D baseline is a strategy expansion, not parameter optimization.

## Universe Resolution

- Requested universe: BTC / ETH / SOL / XRP / DOGE / HYPE / BNB / SUI / AVAX / SHIB.
- Supported universe from Hyperliquid public mainnet metadata: BTC / ETH / SOL / XRP / DOGE / HYPE / BNB / SUI / AVAX / SHIB.
- SHIB identity: requested `SHIB`, venue symbol `kSHIB`, reason `venue_symbol_alias_detected`.

## Data Horizon

- Source: Hyperliquid public mainnet `candleSnapshot`.
- Target start: `2025-01-01T00:00:00Z`.
- `4h` and `1d` reached the Jan 2025 target for all 10 symbols.
- `15m` and `1h` are limited by public recent-candle availability and carry `hyperliquid_public_5000_candle_limit`.
- Candle close slots are normalized to exact timeframe boundaries. `.999Z` venue close timestamps are not canonical close times.
- Summary JSON: `docs/sv2_0_historical_data_refresh_summary.json`.

## Compact Provisional Rows

Each row is an independent symbol/timeframe scenario using:

- `initial_equity = 10000`
- `capital_sizing_mode = dynamic_equity_pct`
- `next_candle_open`
- `fee_bps = 5`
- `slippage_bps = 3`

SV2.0.1 adds explicit open-position accounting to compact rows:

- entry fees are counted at open;
- open positions are mark-to-market tracked for drawdown;
- final open positions are force-closed at dataset end;
- 20 of 40 refreshed compact rows had `open_position_at_end = true` and `forced_close_applied = true`.

These compact rows are still not canonical evidence packs. SV2.0.2 canonical packs are separate DB-backed artifacts.

## Canonical Evidence Status

Status: `resolved_by_sv2_0_2`

Evidence pack paths now exist in ignored `reports/strategy_validation/` directories; see `docs/sv2_0_2_canonical_sv2_evidence_packs.md`.

Former SV2.0.1 blocked reasons:

```text
canonical_sv2_evidence_packs_missing
compact_replay_rows_not_canonical_evidence
db_imported_false_for_staged_summary
```

SV2.0.1 intentionally blocks canonical status because the refreshed public candles are `staged_for_replay=true` but `db_imported=false`. Canonical evidence packs require the hardened import/upsert path and the existing Strategy Validation campaign/evidence-pack machinery.

SV2.0.2 completes that follow-up for supported canonical symbols BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, and AVAX. SHIB/kSHIB remains represented but deferred from canonical evidence because unit semantics are not clean enough.

## Observed Compact Highlights

These observations are provisional and cannot be used as final canonical evidence:

| Row | Net PnL | Notes |
|---|---:|---|
| HYPE 1D | 8572.26796714 | strongest compact row; force-closed final open position |
| ETH 1D | 5175.17008827 | strongest non-forced 1D compact row |
| XRP 4h | 2580.29371789 | positive compact row; force-closed final open position |
| SUI 4h | -5784.51677397 | weakest compact row; force-closed final open position |
| SHIB 4h | -5775.82179038 | weak compact row; SHIB venue alias is `kSHIB` |

Use the JSON summary for all row-level values. Do not treat this table as an optimized selection or live approval.

## Dashboard Status

- Historical Replay selectors use internal `1d` and display `1D`.
- Money Flow v1.2 and `sleeve_1d` remain visible.
- Expanded universe readiness remains visible.
- Compact rows are labeled separately from canonical evidence status.
- Sandbox execution ledger remains separate from historical strategy evidence.

## No-Order / No-Live Confirmation

SV2.0-SV2.0.2 submitted no orders, created no live artifacts, called no private/signed/order endpoints, used no API keys, and did not use Hyperliquid testnet prices as strategy truth.

## Remaining Limitation

SOR-EV1 may proceed from the SV2.0.2 DB-backed canonical baseline. Any SOR-EV1 variant work must remain separately scoped and must not change baseline Money Flow rules unless explicitly approved by that phase.
