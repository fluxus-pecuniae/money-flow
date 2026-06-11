# DASH-QASWEEP1 — Investor-Readiness UI Shakedown + Fix

UI/display fixes only. No runtime, strategy, data-source, order, testnet, or
approval change. **The Paper Trading chart and its markers were not touched.**
**No safety label or honest verdict was removed, softened, or hidden.**

## Issue catalog (severity-tagged)

| # | Severity | Where | Issue | Status |
| - | --- | --- | --- | --- |
| 1 | blocker | Global Filters | The 1s market refresh destructively rebuilt every `<select>` (`renderSelect` / `renderSelectWithoutAll` reset `innerHTML` + `.value` each tick) — picking a pair took many clicks | **Fixed**: idempotent `data-render-key` rebuild only when the option set changes; never rebuild while `document.activeElement === select`; `.value` preserved |
| 2 | major | Runtime Logs | Open log re-defaulted to latest on every status refresh | **Fixed**: rows are expandable `<details>`; `state.paperRuntimeControl.selectedLogKey` tracks the operator's open log; latest is default only when nothing is selected; survives changed re-renders (extends the scroll-restore hotfix) |
| 3 | major | Console hygiene | `/api/paper-runtime/status` probe logged a browser-native 404 console error every 10s when the local control server isn't running | **Fixed**: adaptive cadence (10s available / 60s unavailable backoff, auto-recovers) and `?disableLivePolling=true` now skips control-server probes entirely (explicit unavailable state) → zero console errors in deterministic/CI mode |
| 4 | major | Right rail @1600 | 57px horizontal page overflow in all themes — `#paper-runtime-output`'s long option text blew out the runtime-control grid (`min-width:auto`) | **Fixed**: `min-width:0` + `width:100%` on the control-grid labels/selects |
| 5 | major | Right rail ≤1180 | 45px overflow at 1000px — stale tablet rules split the now single-card rails into 3/2 columns and forced rigid `160px/220px` control-grid tracks | **Fixed**: rails single-column in the legacy 1180px block; stale control-grid override removed |
| 6 | major | Responsive regression | **Tablet/mobile stacking has been silently dead since DASH-IA1**: the terminal-grid base rule was appended after the legacy media blocks, so the grid kept three desktop columns at every width | **Fixed**: stacking re-asserted after the base rule (≤1180px → single column); verified 390/768/1180/1280px with zero overflow |
| 7 | minor | Runtime actions | `.paper-runtime-actions` was `inline-flex` (max-content box that ignores its grid track and spills at narrow widths) | **Fixed**: block-level `flex` |
| 8 | minor | Console hygiene (flagged) | On a machine without the control server, one browser-native 404 console entry can still appear per 60s probe (not suppressible from JS) | **Flagged**: run the local control server during the demo → zero 404s and live pills/logs |

Sweep-tooling note: one false positive (Research Log "missing facets") was a
driver bug (Playwright boolean-attribute semantics), fixed in the sweep
driver — the app renders all facets correctly.

## What was tested (full sweep, two passes)

- **Pass A (deterministic)**: default tab; both nav tabs back/forth; header
  Runtime/Live pills; all five Global Filters dropdowns (open + change +
  revert); all seven blotter tabs; watchlist (rows, selection, no OKB);
  chart presence (untouched); Runtime Control truncation probes; Daily
  Review no-scroll; testnet footer + status-strip-at-end order; Research Log
  (all 13 entries expanded/collapsed, facets, analytics tables, honest
  badges — zero green, evidence links); dark/light/red-zone; 1600/1000/390px.
- **Pass B (1s refresh ACTIVE, endpoints mocked — zero real network)**:
  dropdown focus + pick stability through refreshes; blotter tab persistence;
  open-log persistence through changing status payloads; chart height
  stability with live candles.
- **Console/page errors recorded at every step: final result zero.**
  CI nuance (post-merge-check fix): on runners without the gitignored local
  runtime artifacts (`reports/paper_runtime/*`, `reports/paper_reviews/*`),
  the dashboard's optional-artifact probes 404 by design and the browser logs
  native resource errors that JS cannot suppress. QA check #12 exempts ONLY
  those documented optional paths — any other console error (including a 404
  for a committed file) still fails. Verified both ways: normal local pass
  and a CI-emulation pass with `reports/**` forced to 404 (10 exempt 404s,
  zero non-exempt errors, the paper view renders its explicit empty states).

## Verification

- DASH-QA1 grew from 10 to **12 checks** (new: #11 refresh stability with
  mocked live endpoints; #12 zero console errors + no horizontal overflow at
  1600/1000/390) — **12/12 green**.
- `node --check` clean; cache-buster `dash-qasweep1-20260611`.
- Demo screenshots: `docs/dash_qasweep1_screenshots/` (both tabs dark full +
  viewport, light + red-zone smoke).

## Investor-readiness checklist (for the walkthrough)

1. **Run the local control server first**: `.venv/bin/python
   scripts/run_dashboard_control_server.py --host 127.0.0.1 --port 8767` —
   live header pills, real Runtime Logs, zero console noise. Hard-refresh
   once (cache-buster changed).
2. **Demo theme**: dark. Theme switching works live (chart rebuilds by
   design — a brief blank flicker on the chart during the rebuild is normal).
3. **Safe flow**: Paper Trading (status pills → filters → watchlist → chart →
   runtime rail → blotter tabs → daily review → testnet footer → status
   strip) → Research Log (standing strip → verdict banner → expand SEL-EV1 +
   EXEC-EV1 post-mortems → lessons rail).
4. **Rough edges to avoid on stage**: the chart needs live polling + network
   to show candles (offline it shows an explicit empty state — honest, but
   plan for connectivity); Daily Review shows the generated pack only if
   `latest_review.json` exists locally (generate it beforehand if wanted);
   don't run the demo below ~1280px width — it works (stacks cleanly ≤1180)
   but the three-column terminal reads best at desktop width.
5. **The honesty is the pitch**: Research Log deliberately shows zero green —
   passed gate 0, production NONE, live NOT APPROVED. Don't apologize for it;
   it's the discipline on display.

## Boundaries

Chart + markers untouched. All safety labels and honest verdicts intact (the
text guard stays green). No runtime, strategy, data-source, order, testnet,
or approval change.
