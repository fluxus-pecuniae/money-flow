# DASH-PT3 — Paper Trading Header + Layout Refinements

Dashboard display/layout only. No runtime, strategy, data-source, order,
testnet, or approval change. **The Paper Trading chart and its markers are
untouched.** Every `#paper-observation-*` id preserved.

## The six founder-requested changes

1. **Runtime + Live status pills in the header.** `#top-runtime-pill`
   (`RUNTIME ACTIVE` green/blinking when the local control server reports a
   run, `RUNTIME IDLE` muted otherwise, `RUNTIME — CHECKING` while polling)
   and `#top-live-pill` (`LIVE DISABLED · NOT APPROVED`, static red). Driven
   by the same `state.paperRuntimeControl` status the dashboard already polls
   — display only, no new data source. Theme-aware via the DASH-PT2 tokens.
2. **Status strip moved to the end.** `#paper-observation-health-banner`
   relocated from the top of the Paper Trading view to the final full-width
   band after the Testnet footer — all content, ids, lane chips, and safety
   labels intact (it is the bottom reference band now that runtime/live state
   lives in the header).
3. **Global Filters lead the body.** `.paper-observation-filterbar` is now the
   first element under the header; order: filters → watchlist/chart/runtime →
   blotter → daily review → testnet footer → status strip.
4. **Runtime Control no longer truncates.** The right rail widened to
   `minmax(300px, 344px)` and the right-rail `overflow: hidden` clip replaced
   with `overflow: visible`; control-server message, copy, output slate, and
   safety profile all fit. The center chart remains the dominant flexible
   panel.
5. **Watchlist slightly wider.** Left rail `minmax(212px, 252px)` so
   symbol / mid price / health read cleanly.
6. **OKB removed from the watchlist display.** The watchlist rows come from
   the runtime summary's `scanner_universe`, which bypassed the existing
   `HIDDEN_DASHBOARD_SYMBOLS` display filter — `paperObservationBaseScannerRows`
   now applies `isVisibleDashboardSymbol` to both the summary rows and the
   configured fallback. Display-only; the `pt_rt1.py` resolver policy is
   untouched.
7. **Daily Review / Anomaly Flags scroll removed.** The
   `max-height: 360px; overflow: auto` on the final review card (and its
   mobile variant) dropped — the card renders at full height with no nested
   scroll.

## Verification

- DASH-QA1 **9/9 green** with lockstep updates: #9 now also asserts both
  header pills (live pill must read `live disabled` + `not approved`) and
  that the status strip renders after the testnet footer; #7 (lane chips in
  the status strip) and the rest unchanged and green.
- `tests/test_dashboard_static_assets.py` ordering + grid-column asserts
  updated (filters lead; strip after testnet footer; new rail widths; pill
  markup/CSS present) — 9/9 green.
- All three themes exercised in-browser with zero page errors; chart tokens
  untouched.
- `node --check` clean. Cache-buster `dash-pt3-header-pills-20260611`.
- Before/after screenshots in `docs/dash_pt3_screenshots/` (before = DASH-IA1
  master; after = header pills + new order, incl. full-page dark).

## Boundaries

Display/layout only. Chart + markers exactly as they were. No runtime,
strategy, data-source, order, testnet, or approval change; OKB backend
resolver policy unchanged.
