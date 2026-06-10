# DASH-IA1 — Consolidate the Dashboard to 2 Tabs (structural)

Dashboard display only. No runtime, strategy, data-source, order, testnet, or
approval change. **Nothing deleted from disk** — every SOR-EV / MF-ORIG / SV2.x
evidence pack, replay JSON, builder script, and doc stays as reference; only
navigation surface and the code that rendered the retired views was removed.

## The decision

Money Flow OS is two surfaces:

1. **Paper Trading** — the live desk (default tab).
2. **Research Log** — institutional memory of what has been tested (renamed
   from Evidence; placeholder now, full post-mortem view lands in **RLOG1**).

Retired from navigation (tabs + exclusive render code/markup/CSS):
**Historical Replay**, **The Lab** (evidence-lab), **Strategy** — plus the old
Evidence view innards (replaced by the Research Log placeholder).

## Must 1 — Monolith reduction (the structural cut)

| File | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `apps/dashboard/evidence-dashboard.js` | 12,004 | 6,753 | **−5,251 (−43.7%)** |
| `apps/dashboard/evidence-dashboard.css` | 4,448 | 3,706 | −742 |
| `apps/dashboard/index.html` | 1,088 | 620 | −468 |

Removed: the three nav buttons + their `[data-view-panel]` sections; the view
router entries; the historical-replay block (replay chart/panes, filters,
trade inspector, pair comparison, equity panel, sandbox ledger, SV2.0.2 /
SV2.1 / SV2.2 / MF-ORIG replay-row builders and lazy chart-data loaders); the
evidence-lab block (variant matrix, worst trades, control pockets,
baseline-vs-variant overlay chart, founder-candidate / MF-ORIG sections); the
static Strategy panel + wildcard diagnostics; the old Evidence renderers
(metrics, filters, date controls, strategy comparison SVG, component cards,
detail, run ledger) and their batch-summary helper cluster; retired-view
loaders, dead constants, dead element-registry entries, dead state fields, and
~120 exclusive CSS rules.

Preserved shared helpers that audits proved are still used by surviving
surfaces (notable catches: `renderSelectWithoutAll`, the paper chart's
`PAPER_OBSERVATION_*_PANE` constants, and `historicalConstantRows` — all used
by Paper Trading but previously defined inside retired-view code regions; they
were restored next to their surviving callers). Hidden non-nav UAT legacy
panels (`uat-cockpit`, `uat-shadow`) are untouched.

## Must 1b — Paper Trading layout reflow + rename (founder notes)

- **Global Filters**: now a full-width bar directly under the status strip,
  above the watchlist / chart / runtime row (no longer inside the left rail).
- **Skinnier rails**: terminal grid columns are now
  `minmax(188px, 226px) / minmax(0, 1fr) / minmax(236px, 262px)` (prototype
  proportions 206px / 1fr / 252px) — the chart is the dominant panel.
- **Testnet Order Transport**: relocated to a full-width footer card at the
  very bottom (below Daily Review / Anomaly Flags) — all fields, ids, and
  safety labels preserved; display relocation only.
- **Renamed to "Money Flow OS"** in the page `<title>`, top-bar brand, and
  DESIGN.md.
- **The Paper Trading chart and its markers are untouched.**

## Must 2 — Nav collapsed to two

`Paper Trading` (default, `aria-selected=true` on load) and `Research Log`
(`evidence` view renamed to `research-log`, id `#research-log-view`).
The JS router accepts `research-log` / `paper-observation` (+ the two hidden
legacy UAT panels) and defaults to `paper-observation`.

## Must 3 — Research Log placeholder (data-driven)

Reads up to 12 committed summaries (omitting absent ones gracefully) and
renders phase / date / verdict / source rows sorted newest-first, styled with
the DASH-PT2 tokens, with the visible note that the full post-mortem view
lands in RLOG1. Sources: SEL-EV1, EXEC-EV1, SV2.3, SV2.2, GOAL-STRAT2,
GOAL-STRAT1, EV-AUDIT1, MF-ORIG-EV2, MF-ORIG-EV1.1, SOR-EV3, SOR-EV2, SOR-EV1
(`docs/*_summary.json`). Verdict precedence:
`verdict → conclusion → audit_verdict → gate_status → status`. No hand-coded
data.

## Must 4 — DASH-QA1 updated in lockstep (still 9 checks, all green)

- #1 now asserts Paper Trading is the **default** tab (was: Historical Replay
  default) and Research Log opens on click.
- #2 asserts the reflow: filter bar visible and **not** inside the left rail;
  testnet footer visible and **not** inside the right rail; grid/rails/chart/
  blotter all present.
- #4/#5 unchanged in intent (switch-away now uses Research Log).
- #6 → retired tabs absent (`historical-replay`, `evidence-lab`, `strategy`,
  `evidence`, `audit`) and nav is exactly `['Paper Trading', 'Research Log']`.
- **#7 relocated**: the 3 active lanes from `current_truth.json` must appear
  in the Paper Trading status strip (their surviving home).
- #9 additionally asserts the testnet/synthetic labels in the relocated
  footer.
- `tests/test_dashboard_static_assets.py` (blocking lane) rewritten in
  lockstep: 2-tab IA, Money Flow OS title, reflow ordering, lab-retirement +
  artifacts-preserved guard; same safety intent (no order controls, boundary
  labels, lane truth).

## Must 5 — Verification

- DASH-QA1: **9/9 green** (multiple runs) after the update.
- Blocking-lane battery: 96 tests green (`trading safety invariants`,
  `current truth consistency/registry`, `week2 slate`,
  `dashboard static assets`, `operational docs`, `obs daily review`).
- All three themes exercised in-browser with **zero page errors**.
- `node --check` clean. Cache-buster bumped to `dash-ia1-two-tabs-20260610`.
- Before/after screenshots in `docs/dash_ia1_screenshots/` (before = master
  with 5 tabs; after = 2 tabs, reflow, Research Log).

## Boundaries

No runtime mutation, no strategy-rule change, no data-source change, no
orders, no testnet behavior change, no production or live approval. Paper
Trading behavior unchanged except the two founder-requested Must 1b layout
moves (filters bar, testnet footer) and the rename; the chart and markers are
exactly as they were.
