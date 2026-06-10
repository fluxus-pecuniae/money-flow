# DASH-PT2 — Paper Trading Bolder Exchange Reskin

Dashboard display only. No runtime, strategy, data-source, order, testnet, or
approval change. No other tab's behavior changed.

## What Changed

DASH-PT2 elevates the existing DASH-PT1.2/1.3 Paper Trading terminal **in
place** to a bolder, denser, color-coded exchange aesthetic — a systematic-fund
operator terminal — primarily through CSS, preserving every behavior, hook,
theme, and DASH-QA1 guard check. The visual reference is the founder prototype
`docs/dash_pt2_prototype.html`.

### Must 1 — Design tokens (theme-aware)

New DASH-PT2 token layer in `apps/dashboard/evidence-dashboard.css`, defined
for all three themes (`:root` dark, `html[data-theme="light"]`,
`html[data-theme="red-zone"]`):

| Token | Role | Dark value |
| --- | --- | --- |
| `--lane-baseline` | `money_flow_v1_2_baseline` lane accent | `#3d9bff` |
| `--lane-diagnostic` | `avoid_low_rolling_range_20` lane accent | `#a981ff` |
| `--lane-candidate` | `mf_orig_1d_stage2_breakout_resistance_full_equity` lane accent | `#ffb454` |
| `--lane-neutral` | unknown/archived lanes | muted |
| `--accent-live` | live / healthy / positive accent | `#2ee6a6` |
| `--accent-live-deep` / `--accent-live-ink` | gradient stop / ink on accent | `#15a47a` / `#06120d` |
| `--accent-testnet` | testnet plumbing accent | `#2fb6c9` |
| `--terminal-chip` / `--terminal-row-line` | chip + dense row hairlines | `#16202e` / `#131c28` |

The prototype is dark-only; the light and red-zone equivalents use darker
accessible accents (e.g. light `--accent-live: #0a8a60` with white ink). The
`--color-chart-*` tokens are intentionally untouched, so the TradingView chart
palette and theme-rebuild behavior are unchanged.

### Must 2 — Reskin (CSS-led, in place)

- **Top status strip** — the health banner renders as a dense 1px-grid of
  scannable cells: uppercase keys, bold monospace values, state-colored cells
  (runtime ok/warn, 15m amber, live trading red `not approved`, testnet
  accent), and the three active lanes as color-coded chips.
- **Left rail** — uppercase cockpit filter labels, monospace selects, denser
  watchlist rows with hover and a live-accent inset bar on the selected row.
- **Center chart** — remains the visual anchor; bolder display-font header;
  bounded heights and chart internals untouched.
- **Right rail** — Runtime Control with an accent-gradient `Start Run` button
  and accent runtime message; Testnet Order Transport carries the testnet
  accent; both stay height-bounded.
- **Bottom blotter** — accent-underlined tabs, dense sticky-header monospace
  tables, hover rows, colored `td.positive`/`td.negative` PnL columns, and
  translucent terminal-style status tags.
- **Daily Review / Anomaly Flags** — dense cell grid plus flag rows styled as
  terminal list items.
- **Per-lane color coding** — applied consistently across the status strip,
  watchlist-adjacent tables, Signal Stream, Weekly Scoreboard, Lane Detail,
  Testnet Lifecycle, Open Positions, and Closed Trades, mapped to the
  `current_truth.json` active lanes.
- **Shared chrome (intentional)** — top strip + brand mark get a subtle
  live-accent edge; the active nav tab uses the live-accent gradient. No other
  tab body is restyled.

### Must 3 — Behavior, hooks, theming preserved

- Zero changes to data loading, filters, polling, runtime control, or any JS
  behavior. The only JS edits are display-only markup: a `paperObservationLaneChip`
  helper (escaped span with `data-lane-accent`) used in lane cells, and fixed
  state classes on four status-strip cells.
- Every `#paper-observation-*` id and the DOM structure DASH-QA1 selects are
  preserved verbatim; no DASH-QA1 selector needed updating.
- All three themes verified (screenshots below), including the chart area;
  chart color tokens untouched.

### Must 4 — Verification

- DASH-QA1: **9/9 browser checks green**, run twice
  (`.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q`).
- Before/after Playwright screenshots in `docs/dash_pt2_screenshots/`
  (desktop 1600px + mobile 390px, dark; plus desktop light and red-zone), via
  `scripts/capture_dash_pt2_screenshots.py`.
- Cache-bust: `?v=dash-pt2-bold-terminal-20260610` on both the CSS and JS tags
  in `apps/dashboard/index.html`.

## Screenshots

| Shot | Before | After |
| --- | --- | --- |
| Desktop dark | `before-paper-trading-desktop-dark.png` | `after-paper-trading-desktop-dark.png` |
| Desktop dark (full page) | `before-paper-trading-desktop-dark-full.png` | `after-paper-trading-desktop-dark-full.png` |
| Mobile dark | `before-paper-trading-mobile-dark.png` | `after-paper-trading-mobile-dark.png` |
| Desktop light | `before-paper-trading-desktop-light.png` | `after-paper-trading-desktop-light.png` |
| Desktop red-zone | `before-paper-trading-desktop-red-zone.png` | `after-paper-trading-desktop-red-zone.png` |

## Boundaries

- Dashboard display only; research/observation surfaces unchanged in meaning.
- No runtime mutation, no strategy-rule change, no data-source change, no
  orders, no testnet behavior change, no production or live approval.
- Safety labels remain prominent (synthetic ledger, testnet separation,
  baseline-only transport, live trading `not approved`) and are guarded by
  DASH-QA1 check #9.
