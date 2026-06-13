# MF-REPLAY1 — Founder Visual Backtesting: Range-Accurate Replay of the PT-RT2 Lanes

> **Hypothetical replay, not evidence.** Range replay of the committed PT-RT2 lane semantics for founder judgment only — not a validated strategy, not new evidence, and it never feeds or backfills the live synthetic ledgers. A green range is **window placement, not alpha** (TSMOM-EV1's OOS window was absolutely negative; MONEYFLOW-SIGNAL1's was positive — same defensive trend mechanic). Committed verdicts travel: `defensive_trend_mechanic_not_validated_alpha` (standalone); `source_faithful_but_underperformed` (trade level); the regime overlay carries REGIME2's honest-FAIL verdict (`regime_filter_does_not_reduce_drawdown_oos` — informational risk context, not a validated control).

## What this delivers

The founder can replay the two committed PT-RT2 lanes (`mf_source_faithful_baseline`, `mf_source_faithful_regime_gated`) over the full DATA1 history with selectable ranges (all-time / calendar year / custom dates) and an accurate equity answer for each: "if I started this range with 10,000 USDC, where did I end?" — on the dashboard's re-introduced **Historical Replay** tab.

## Durable data foundation (Must 1)

- Snapshot home moved from `/tmp/money-flow-data1/raw_series` (cleared by macOS) to the durable ignored repo path **`var/data1/raw_series/`**; the committed provenance summary's sha256 values are unchanged by the move and still verify on load.
- `scripts/refresh_data1_snapshot.py` — appends ONLY newly-closed candles, idempotent on re-run.
- `scripts/export_data1_csv.py` — per-symbol OHLCV CSVs (`var/data1/csv/`) for a portable founder copy.
- Coverage preserved & asserted: Binance perp 1d starts BTC 2019-09-09, ETH 2019-11-28, XRP 2020-01-02, BNB 2020-02-11, DOGE 2020-07-11, SOL 2020-09-15, AVAX 2020-09-24; the aligned 7-major window starts **2020-09-24**.

## Pre-registered range semantics (Must 2 — chosen before the UI)

- **Fresh start**: the range book starts FLAT with 10,000 USDC at the range's first aligned closed candle and takes only entries that fire INSIDE the range; a position the signal held before the range start is ignored until its next fresh entry ("if I had started running it on that date").
- **Warm-up uses pre-range history** (warm-up = data; fresh-start = position state); a symbol whose data + warm-up postdates the range start joins when ready and the surface says so — never guessed.
- Closed daily candles only; no-lookahead (truncation probe test-pinned); deterministic Decimal arithmetic; one code path — the replay runs the committed `moneyflow_signal1.signal_states` surface + the PT-RT2 lane semantics, never a parallel calculator.
- Ranges: all-time / calendar year (partials labeled) / custom.

## Range results (honest numbers — window placement, not alpha)

Full equity, both lanes, current snapshot (through 2026-06-13 close). Returns and drawdowns **include the K-037 leverage** (full-equity sizing per concurrent symbol position → up to ~7.8× gross).

### `mf_source_faithful_baseline` (Control)

| Range | End (USDC) | Return | Max DD | Trades | Max grossX |
| --- | --- | --- | --- | --- | --- |
| all-time (2020-09-24→) | 581,725 | +5,717% | 99% | 415 | 7.83× |
| 2020 (partial) | 63,198 | +531% | 39% | 14 | 4.81× |
| 2021 | 577,703 | +5,677% | 87% | 65 | 6.78× |
| 2022 | 285 | −97% | 98% | 76 | 6.96× |
| 2023 | 84,037 | +740% | 71% | 69 | 6.05× |
| 2024 | 65,710 | +557% | 80% | 74 | 6.77× |
| 2025 | 1,881 | −81% | 82% | 77 | 7.83× |
| 2026 (partial) | 6,117 | −38% | 59% | 34 | 5.65× |
| **2021-06-19 → 2025-05-31** | **29,702** | **+197%** | **99%** | **291** | **7.83×** |

### `mf_source_faithful_regime_gated` (Informational Overlay)

| Range | End (USDC) | Return | Max DD | Trades | Max grossX |
| --- | --- | --- | --- | --- | --- |
| all-time | 417,776 | +4,077% | 82% | 167 | 7.83× |
| 2020 (partial) | 10,000 | 0% | 0% | 0 | 0× |
| 2021 | 97,415 | +874% | 64% | 47 | 6.13× |
| 2022 | 7,641 | −23% | 23% | 5 | 3.00× |
| 2023 | 9,643 | −3% | 44% | 21 | 6.05× |
| 2024 | 132,695 | +1,226% | 63% | 46 | 5.56× |
| 2025 | 5,227 | −47% | 64% | 41 | 7.83× |
| 2026 (partial) | 9,202 | −7% | 24% | 5 | 3.88× |
| **2021-06-19 → 2025-05-31** | **35,877** | **+258%** | **82%** | **110** | **7.83×** |

The regime overlay's defensive mechanic is visible exactly where REGIME2 said it would be: in the 2022 bear it cut the drawdown (23% vs the baseline's 98%) and the exposure (3.0× vs 7.0× gross), and it sat flat in 2020 when the gate was risk-off — at the cost of whipsaw in chop. This is the committed `regime_filter_does_not_reduce_drawdown_oos` texture replayed, **not** a validated control.

## Accuracy proof (Must 4)

`tests/test_mf_replay1.py` (deterministic, offline, fast lane):

- **hand fixture** — per-trade fee/quantity/PnL/equity recomputed by hand from the engine's own entry/exit prices, matches to the cent;
- **year boundary** — a Dec-31 close lands in year N's book, a Jan-1 close in year N+1's;
- **fresh start** — a position held before the range start is not carried in; every in-range trade enters at/after the range start;
- **warm-up** — pre-range indicator history is used; an in-warmup range takes no entries and reports the symbol joining late;
- **no-lookahead** — truncating all post-end history reproduces the range result exactly;
- **live-ledger equivalence** — replaying the committed live PT-RT2 decision path + ledger arithmetic over a **non-overlapping (single-symbol)** window reproduces the replay engine's trajectory exactly.

### The K-037 equivalence boundary (surfaced, not hidden)

The live paper-runtime lane ledger stores equity-at-entry **per position** and, on close, sets realized equity to `position.equity_before + net_pnl`. With positions overlapping across symbols in one lane (the PT-RT2 lanes hold up to 7), that can drop realized PnL — the replay's sequential-additive ledger (each close adds net PnL to the lane's *current* equity) is the arithmetic that actually answers "where did 10,000 USDC end." The two provably coincide only on non-overlapping sequences, so the equivalence test is pinned on a single symbol and the divergence boundary is documented on the surface and in the test.

## K-037 — founder decision flag

Full-equity sizing **per concurrent symbol position** levers the committed PT-RT2 lanes up to ~7.8× gross when all 7 majors are long; the all-time book draws down ~99% in the 2022 bear. The replay surfaces `max_gross_exposure_x` and `max_concurrent_positions` on every range so this is never hidden. **Open founder decision (separately scoped):** is full-equity-per-position the intended paper-lane sizing? This phase does NOT change live sizing or live trajectories.

## Dashboard surface (Must 3)

Re-introduced **Historical Replay** tab: range picker (all-time / year / custom dates), lane selector, the replayed equity curve + a result card (start 10k → end equity, return, max DD, trades, **plus max gross exposure / max concurrent positions per K-037**), a candle chart with this range's entry/exit markers for the chart symbol, and a dashed **live-observation-start separator** so hypothetical replay and the live PT-RT2 window are never confused. The characterization note renders next to every result. **Serving:** the precomputed pack (`reports/mf_replay1/replay_pack.json`, built by `scripts/build_mf_replay1_dashboard_data.py`) for all-time + calendar years — the same committed/ignored-JSON pattern the rest of the dashboard uses; custom dates use the control server's `/api/mf-replay1/range` endpoint (same engine, one code path).

## Boundaries

Replay-only: no live ledger writes, no orders, no private/signed endpoints, no approval surface, no production strategy change. The live synthetic ledgers are never backfilled, recomputed, or touched.
