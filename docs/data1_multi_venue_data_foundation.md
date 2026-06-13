# DATA1 — Multi-Venue Market & Funding Data Foundation

Every strategy test so far consumed **Hyperliquid-only** data — a real
limitation, sharpest for funding carry (HL's thin spot + fee schedule is most
of why carry failed) and for trend (one venue, one bull–bear cycle, 889
aligned daily candles). DATA1 builds the public, read-only, multi-venue
dataset (perp funding history, perp daily candles, spot daily candles) for
the liquid majors across the deepest venues, so the next funding test is
venue-fair and future trend/regime tests have materially longer history
(Coinbase BTC spot now reaches back to 2015-07 — ~3,979 daily candles vs the
889-candle HL window).

**Data ingestion only.** No strategy logic, no orders, no private/signed
endpoints, no API keys, no runtime change. Boundary flags are embedded in
the committed summary and pinned by test.

- Module / loader: `services/market_data/data1_multi_venue.py`
  (`load_data1_dataset()`)
- Fetch script: `.venv/bin/python scripts/fetch_data1_multi_venue_snapshot.py`
  (resume with `--reuse-artifacts`)
- Committed provenance: `docs/data1_multi_venue_snapshot_summary.json`
- Raw artifacts (ignored, regenerable): `var/data1/raw_series/` (durable repo home since MF-REPLAY1; previously `/tmp/money-flow-data1/raw_series/`, which macOS clears)
- Tests: `tests/test_data1_multi_venue.py` (blocking CI lane);
  `tests/test_data1_live_smoke.py` (env-gated live canary:
  `DATA1_LIVE_SMOKE=1`, skipped in CI)

## Universe and venues

Assets: **BTC ETH SOL XRP DOGE BNB AVAX**. Venues and what each publicly
offers (gaps are first-class records, never substitutions):

| Venue | Funding | Perp 1d | Spot 1d | Public endpoints | Funding interval (declared = observed) | Cited rate limit |
| --- | --- | --- | --- | --- | --- | --- |
| hyperliquid | 7/7 | 7/7 | 3/7 (BTC ETH SOL via Unit pairs) | `POST /info` `fundingHistory` / `candleSnapshot` | 1h = 1.0h | info weight budget 1200/min |
| binance | 7/7 | 7/7 | 7/7 | `fapi/v1/fundingRate`, `fapi/v1/klines`, `api/v3/klines` | 8h = 8.0h | 2400 weight/min |
| bybit | 7/7 | 7/7 | 7/7 | `v5/market/funding/history`, `v5/market/kline` | 8h = 8.0h | ~600 req/5s |
| okx | 6/7 (no BNB) | 6/7 | 6/7 | `public/funding-rate-history`, `market/history-candles` **bar=1Dutc** | 8h = 8.0h | 10 req/2s per endpoint |
| coinbase | 0/7 (no perp market data on the public Exchange API) | 0/7 | 6/7 (no BNB) | `products/{id}/candles` | n/a | ~10 req/s |
| kraken | 6/7 (no BNB; via Kraken Futures) | 6/7 | 6/7 | `0/public/OHLC`, futures `historicalfundingrates`, futures `charts/v1/trade` | 1h = 1.0h | spot ~1 req/s; futures light |

## Coverage obtained (history start per venue × asset; all end 2026-06-11)

Daily-candle and daily-funding-sum coverage from the committed summary
(`rows`, `missing_internal_days`, zero-volume accounting, and sha256 per
series live there). `—` = venue lacks the market (see gap report).

**Perp funding (daily sums of native-interval events):**

| Asset | hyperliquid (1h) | binance (8h) | bybit (8h) | okx (8h) | kraken futures (1h) |
| --- | --- | --- | --- | --- | --- |
| BTC | 2023-05-13 | 2019-09-11 | 2020-03-26 | 2026-03-12 | 2025-06-11 |
| ETH | 2023-05-13 | 2019-11-28 | 2020-10-22 | 2026-03-12 | 2025-06-11 |
| SOL | 2023-05-13 | 2020-09-14 | 2021-06-30 | 2026-03-12 | 2025-06-11 |
| XRP | 2023-06-19 | 2020-01-07 | 2021-05-14 | 2026-03-12 | 2025-06-11 |
| DOGE | 2023-05-13 | 2020-07-11 | 2021-06-03 | 2026-03-12 | 2025-06-11 |
| BNB | 2023-05-13 | 2020-02-11 | 2021-06-30 | — | — |
| AVAX | 2023-05-13 | 2020-09-23 | 2021-09-16 | 2026-03-12 | 2025-06-11 |

**Perp daily candles:**

| Asset | hyperliquid* | binance | bybit | okx | kraken futures |
| --- | --- | --- | --- | --- | --- |
| BTC | 2020-08-20* (traded 2023-02-27) | 2019-09-09 | 2020-03-26 | 2020-01-02 | 2022-03-24 |
| ETH | 2020-08-20* (traded 2023-02-27) | 2019-11-28 | 2021-03-16 | 2020-01-02 | 2022-03-24 |
| SOL | 2020-09-15* (traded 2023-03-05) | 2020-09-15 | 2021-10-16 | 2021-01-24 | 2022-03-24 |
| XRP | 2020-09-22* (traded 2023-06-18) | 2020-01-07 | 2021-05-14 | 2020-01-02 | 2022-03-24 |
| DOGE | 2020-08-20* (traded 2023-04-04) | 2020-07-11 | 2021-06-03 | 2020-07-12 | 2022-06-21 |
| BNB | 2020-08-20* (traded 2023-03-06) | 2020-02-11 | 2021-06-30 | — | — |
| AVAX | 2020-09-24* (traded 2023-03-06) | 2020-09-24 | 2021-09-16 | 2020-09-25 | 2022-03-24 |

\* Hyperliquid serves daily perp candles from **before the venue itself
traded** — ~900+ zero-volume backfilled price marks per asset (e.g., BTC:
921 zero-volume candles 2020-08-20 → 2023-02-26). They are kept exactly as
the venue serves them and counted per series
(`coverage.zero_volume_rows` / `first_nonzero_volume_close`), so backfill is
never mistaken for market history. **Real HL trading starts at the
first nonzero-volume candle** (dates in parentheses).

**Spot daily candles:**

| Asset | hyperliquid | binance | bybit | okx | coinbase | kraken |
| --- | --- | --- | --- | --- | --- | --- |
| BTC | 2025-02-04 | 2017-08-18 | 2021-07-06 | 2018-01-12 | **2015-07-21** | 2024-06-22† |
| ETH | 2025-03-27 | 2017-08-18 | 2021-07-06 | 2018-01-12 | 2016-05-19 | 2024-06-22† |
| SOL | 2025-05-11 | 2020-08-12 | 2021-10-22 | 2020-10-02 | 2021-06-18 | 2024-06-22† |
| XRP | — | 2018-05-05 | 2021-07-21 | 2020-01-02 | 2019-02-27‡ | 2024-06-22† |
| DOGE | — | 2019-07-06 | 2021-09-01 | 2020-01-02 | 2021-06-04 | 2024-06-22† |
| BNB | — | 2017-11-07 | 2022-03-11 | — | — | — |
| AVAX | — | 2020-09-23 | 2021-11-13 | 2020-09-24 | 2021-10-01 | 2024-06-22† |

† Kraken's public OHLC endpoint hard-caps history at the **last 720 daily
candles** regardless of `since` — a venue limit, recorded, not worked around.
‡ Coinbase XRP-USD has a single **904-day internal hole (2021-01-19 →
2023-07-13)** — the real SEC-suit delisting window. It stays a hole
(`missing_internal_days: 904`); nothing is filled. Coinbase ETH also has 2
missing days (2016 venue outages).

## Venue history limits found (the honest fine print)

- **OKX funding history is shallow**: the public `funding-rate-history`
  endpoint serves only a trailing **~3-month window** (92 daily sums per
  asset at fetch time). OKX candle history is deep; its funding history is
  not. Any OKX carry claim is near-term only.
- **Kraken Futures funding** returns a trailing **~1-year window** (366
  daily sums). Kraken spot candles cap at **720 days**.
- **Hyperliquid pre-launch backfill**: see the zero-volume note above.
- **Funding intervals differ by venue** (1h HL/Kraken vs 8h
  Binance/Bybit/OKX) and are both declared and observed per series; daily
  sums make them comparable without rescaling (the FUND-EV1 convention:
  slot closing at D 00:00Z sums events in [D−1 00:00Z, D 00:00Z); per-day
  event counts expose partial days — reported, never scaled or filled).
- **OKX daily bars are UTC+8 by default** (probe-verified 16:00Z opens). The
  fetcher requests `bar=1Dutc`; the normalizer refuses any non-midnight-UTC
  daily candle outright (`Data1AlignmentError`) rather than mis-align.
- Binance funding timestamps carry millisecond jitter (e.g. `…00004`); the
  daily bucketing floors event time, so settlement events land in the right
  slot on every venue identically.

## Coverage gap report (25 cells, all `venue_lacks_market`)

- Coinbase: no perp/funding market data on the public Exchange API (14
  cells); no BNB spot (1).
- OKX / Kraken: no BNB listing at all (3 cells each).
- Hyperliquid: no spot pair for XRP/DOGE/BNB/AVAX (4 cells).

No fetch failures in the committed snapshot: 101 of 101 expected series
fetched OK on 2026-06-11.

## Aligned dataset design + loader

One canonical row shape per series (funding events `{time_utc, rate}` +
daily sums `{close_time, funding_rate_sum, events}`; candles
`{open_time, close_time, open, high, low, close, volume_base}` — strings,
exact Decimal sums for funding). Alignment is **union-calendar**: per asset
and series, the calendar is the union of every venue's daily closes;
missing venue/days stay explicit `None` holes — no forward-fill, no
interpolation, no truncation to the intersection (listing-date offsets and
the XRP delisting hole survive visibly).

```python
from services.market_data.data1_multi_venue import load_data1_dataset

ds = load_data1_dataset()                      # committed summary + /tmp artifacts
btc = ds.get("binance", "BTC")                 # .funding / .perp_1d / .spot_1d
btc.funding.daily_funding                      # daily sums + per-day event counts
btc.funding.funding_interval_hours_observed    # 8.0
view = ds.aligned_daily("BTC", series="funding")  # union calendar across venues
ds.coverage_table()                            # full venue x asset x series flags
```

Loader honesty: artifacts are verified against the committed sha256
(tampering raises `Data1IntegrityError`); an absent artifact surfaces as
`artifact_missing_rerun_fetch_script` — data is never fabricated; venue
gaps pass through with their reasons; `as_of` comes from the committed
window. Strategy phases must consult the coverage flags before comparing
venues.

## Provenance

The committed `docs/data1_multi_venue_snapshot_summary.json` records, per
series: endpoint, venue symbol, native row count, first/last close, internal
missing days, zero-volume accounting, funding interval declared + observed,
first/last audit samples, and the **sha256 of the raw artifact**. Raw
native payloads (57 MB) stay ignored local artifacts, regenerable from the
same public endpoints by re-running the fetch script. Access is pinned in
`boundaries`: public read-only, no keys, no private/signed/order endpoints,
no order creation, no runtime mutation.

## What this unblocks

- **FUND-VENUES1**: the funding re-test is now venue-fair — five venues'
  funding series aligned daily, with honest depth limits per venue
  (Binance/Bybit carry 4–6.7 years; OKX only ~3 months; Kraken 1 year).
- Trend/regime re-tests on longer history: BTC spot daily from 2015-07
  (Coinbase) and 2017-08 (Binance) vs the previous single-venue 889-candle
  window — more than one full cycle of out-of-sample regimes.
- REGIME1 remains queued and independent of this dataset's venue breadth.
