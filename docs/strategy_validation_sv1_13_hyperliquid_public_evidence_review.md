# SV1.13 Hyperliquid Public Evidence Review

Recorded at: `2026-05-06T23:12:10Z`

Status: `ready_for_founder_review`

Implementation commit: `cd6e79c`

This report records the first real Money Flow evidence packs generated from imported Hyperliquid public campaign candles. It is research-only. It is not proof of future outcomes, not paper-trading authorization, not live-trading authorization, not a strategy recommendation, and not cross-venue Money Flow performance.

## Scope

- Campaign config: `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json`
- Venue/product scope: Hyperliquid USDC perpetual public-candle evidence only.
- Evidence expansion: the public campaign uses component-specific `timeframe_windows`, so SV1.13 expands it into three component-scoped evidence configs instead of a false component/window Cartesian product.
- Evidence pack run timestamp: `2026-05-06T23:12:10Z`
- DB target: `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow`
- Schema status: `migrated_schema_ready`, Alembic head `20260430_0025`
- Identity: BTC/ETH/SOL Hyperliquid research identity exists, is operator-verified by `Tercirafael`, and remains `is_strategy_eligible=false` / `is_trading_eligible=false`.

## Data Readiness

Imported candle counts were reconfirmed before evidence generation:

| Symbol | 15m | 1h | 4h | Total |
|---|---:|---:|---:|---:|
| BTC | 4,896 | 2,976 | 744 | 8,616 |
| ETH | 4,896 | 2,976 | 744 | 8,616 |
| SOL | 4,896 | 2,976 | 744 | 8,616 |

Total persisted Hyperliquid public campaign candles: `25,848`.

All three component-scoped campaign audits were covered with minimum coverage `1.00000000`, no thin rows, no missing rows, and no blocked rows.

## Evidence Packs

Generated local evidence packs:

- `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_15m/20260506T231210Z`
- `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_1h/20260506T231210Z`
- `reports/strategy_validation/money_flow_hyperliquid_public_ytd_recent_sleeve_4h/20260506T231210Z`

These generated packs are intentionally ignored by Git and review-bundle packaging. The committed artifact is this founder-readable summary. Each generated manifest records the campaign name, collision policy, sanitized DB target, venue, symbols, components, windows, fill timings, fee/slippage assumptions, data coverage summary, blocked-run counts, and no-live/no-routing/no-exchange flags.

## High-Level Observations

SV1.13.1 clarifies the interpretation of these tables: each fill-timing row below is a descriptive grouped aggregate across multiple completed research runs, including symbols and fee/slippage assumptions. The summed net PnL and trade counts are not one tradable account result. Use scenario-level rows in `docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md` for assumption-specific founder review.

The 15m component produced completed runs but observed aggregate net PnL was negative under all fill-timing assumptions:

| Fill timing | Sum net PnL across research runs | Sum trades across research runs | Largest observed MTM drawdown |
|---|---:|---:|---:|
| `next_candle_close` | `-29780.77017100` | 2,500 | `4355.71891546` |
| `next_candle_open` | `-33987.66171136` | 2,580 | `4373.47751921` |
| `same_candle_close_research_only` | `-34020.13284129` | 2,580 | `4374.41912412` |

The 1h component produced completed runs with positive observed aggregate net PnL under all fill-timing assumptions, led by ETH concentration:

| Fill timing | Sum net PnL across research runs | Sum trades across research runs | Largest observed MTM drawdown |
|---|---:|---:|---:|
| `next_candle_close` | `3116.20951745` | 1,468 | `2133.26535823` |
| `next_candle_open` | `10420.30076188` | 1,508 | `2364.77522310` |
| `same_candle_close_research_only` | `10513.41838468` | 1,508 | `2359.05584860` |

The 4h component produced completed runs but observed aggregate net PnL was negative under all fill-timing assumptions:

| Fill timing | Sum net PnL across research runs | Sum trades across research runs | Largest observed MTM drawdown |
|---|---:|---:|---:|
| `next_candle_close` | `-26382.93849581` | 408 | `4062.42292869` |
| `next_candle_open` | `-27049.49628213` | 436 | `4544.87301119` |
| `same_candle_close_research_only` | `-26949.79410780` | 436 | `4524.13375040` |

## Symbol And Regime Notes

- 15m symbol totals were negative for BTC, ETH, and SOL; SOL had the largest observed 15m drawdown.
- 1h symbol totals were concentrated: ETH was positive overall, while BTC and SOL were slightly negative overall.
- 4h symbol totals were negative for BTC, ETH, and SOL; SOL had the largest observed 4h drawdown.
- 1h uptrend regimes showed positive observed aggregate contribution, while 1h sideways/downtrend regimes were negative.
- 15m and 4h regime summaries showed negative observed aggregate contribution in the major covered trend regimes.

## No-Trade And Invalid Reasons

The most common no-trade reason across components was `bearish_alignment`. Other frequent reasons included `macd_not_constructive`, `rsi_not_constructive`, `entry_quality_not_constructive`, and `overextended_rsi`. The main invalid reason was `insufficient_history`, which is expected near the beginning of each requested window because indicator warmup is required.

## Manual Review Checklist

Founder/operator review should focus on:

- whether the 1h ETH concentration is acceptable or too narrow;
- whether the 15m and 4h negative observed results argue against those components for later design work;
- whether next-candle-open and next-candle-close fill timing are robust enough for any future paper-trading design;
- whether mark-to-market drawdowns and worst observed trades fit the founder's risk tolerance;
- whether regime behavior is too concentrated in uptrend conditions;
- whether fee/slippage assumptions remain realistic for Hyperliquid USDC perps;
- whether the existing external-review blockers are resolved before any paper/live phase.

Paper trading remains deferred. A later phase must be explicitly scoped and founder-accepted before paper-trading design or implementation begins.

## Deferred Scope

- Aster and Binance remain later comparative candidates after separate non-trading identity verification and guarded imports.
- OKX and Coinbase remain blocked until trade-count/source policy is resolved.
- Kraken remains blocked by public REST history limits for this data plan.
- Cross-venue results must not be merged with Hyperliquid or described as interchangeable because product type, quote asset, settlement asset, and data-source fields differ.
- Money Flow rule changes, parameter optimization, and strategy recommendations remain deferred.

## Commands Used

Read-only readiness check:

```bash
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=money_flow DB_USER=money_flow DB_PASSWORD=<redacted> \
  .venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --config configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json \
  --format json \
  --review-output-dir /tmp/money-flow-sv113-readiness
```

Evidence generation:

```bash
env DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=money_flow DB_USER=money_flow DB_PASSWORD=<redacted> \
  .venv/bin/python scripts/review_money_flow_evidence_packs.py \
  --config configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json \
  --generate-evidence-packs \
  --output-dir reports/strategy_validation \
  --run-timestamp 2026-05-06T23:12:10Z \
  --format both \
  --review-output-dir reports/strategy_validation_reviews/sv1_13_hyperliquid_public
```
