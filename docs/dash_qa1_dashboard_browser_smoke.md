# DASH-QA1 — Dashboard Browser Smoke + Chart-Stability Regression

**Date**: 2026-06-10
**Scope**: Browser-level smoke suite for the Paper Trading dashboard. Pins documented regressions so they cannot silently return.

---

## Summary

DASH-QA1 adds a deterministic Playwright-based browser-smoke suite that:

1. Serves the **repo root** over a localhost HTTP server (so relative paths like `docs/*.json` and `apps/dashboard/vendor/...` resolve).
2. Opens `apps/dashboard/index.html?disableLivePolling=true` in headless Chromium.
3. Runs **nine grounded checks** against the real HTML/JS selectors documented in DASH-PT1.1 / DASH-PT1.2 / DASH-PT1.3.
4. Sources expected lane/timeframe values from `current_truth.json` (the TRUTH1 registry) so the suite stays in lockstep with the canonical truth.

No external network. No runtime artifacts under `reports/` consulted. No dashboard behavior changed — `data-testid` hooks were **not** required; every check resolves through the existing selectors and ARIA attributes.

---

## The nine checks

| # | Check | Regression guarded |
|---|---|---|
| 1 | Paper Trading tab loads (`#paper-observation-view` visible, `aria-selected="true"`) | Tab-routing breakage |
| 2 | Terminal layout visible (grid + left/center/right rails + bottom blotter) | DASH-PT1.2/1.3 layout regression |
| 3 | Chart does not grow the page infinitely (scrollHeight stable across 4s) | Documented `autoSize` / ResizeObserver feedback-loop P0 |
| 4 | Tab switching persists state (blotter selection retained on return) | Tab-history loss |
| 5 | Blotter tab does not reset every refresh cycle (3s observation) | DASH-PT1.3 refresh-rerender regression |
| 6 | No Audit tab — neither `data-view="audit"` nor "Audit" text | DASH-PT1.1 removal |
| 7 | Strategy view shows exactly the three `active_lanes` from `current_truth.json` | Lane drift from registry |
| 8 | `15m` is paused/legacy in the timeframe filter, never an active scoring option | PT-RT1.4 disabled-timeframe boundary |
| 9 | Synthetic / testnet / no-live-trading boundary labels visible in the paper view | Approval-language drift |

Test file: `tests/dashboard_qa/test_dashboard_smoke.py`. Harness: `tests/dashboard_qa/conftest.py`.

---

## How it runs

### Local

```bash
pip install -e ".[dev]"
playwright install chromium
python -m pytest -m browser tests/dashboard_qa/ -q
```

Stability runs during development: **3 consecutive green** (9 tests, ~23s each on macOS arm64).

### CI

A dedicated job `dashboard-qa` in `.github/workflows/ci.yml` runs the suite on every push to `main`/`master` and on PRs targeting them. It installs deps via `pip install -e ".[dev]"`, runs `playwright install --with-deps chromium`, then `python -m pytest -m browser tests/dashboard_qa/`.

**Lane**: starts as **informational** (`continue-on-error: true`). It will be promoted to blocking only after **3 consecutive green runs in CI** (not just locally) — Ubuntu runners can surface flakes that don't appear on macOS. The promotion criterion is: 3 consecutive green CI runs on the `dashboard-qa` job with no retries needed.

---

## Determinism guarantees

- `?disableLivePolling=true` short-circuits the Hyperliquid polling paths; no external HTTP is initiated from the browser.
- The HTTP server is started fresh per session on an ephemeral free port, bound to `127.0.0.1` only.
- No test inspects `reports/paper_runtime/` or other runtime-only artifacts — assertions cover the configured/empty-state truth that exists at static load.
- Bounded refresh-cycle waits (`page.wait_for_timeout(4000)`) are used **only** where a check deliberately observes stability across cycles (checks 3 and 5). All other assertions use `expect()` polling with the framework's default 5s.

---

## Pyproject changes

- `[project.optional-dependencies].dev` adds `pytest-playwright>=0.5.0`.
- `[tool.pytest.ini_options]` registers a `browser` marker and sets `addopts = "-m 'not browser'"` so the default pytest discovery excludes the suite (the `informational` CI lane's `pytest -q` will not try to run it without Chromium installed).

---

## Boundaries

Tests + harness + CI + docs only. No change to `evidence-dashboard.js`, `.css`, or `index.html` behavior. No `data-testid` or other hooks added. No runtime, strategy, order, testnet, slate, or approval state changed. No live endpoints contacted.

---

## Known limitations

- Requires Chromium binary (`playwright install chromium`) — captured in `KNOWN_ISSUES` and in this doc. The pytest `addopts = "-m 'not browser'"` prevents accidental failures elsewhere.
- macOS-arm64 local runs cannot guarantee Ubuntu-runner determinism; promotion to blocking requires 3 green CI runs, not 3 local runs.
- The suite asserts configured/empty-state truth only. Runtime-only assertions (live PnL, signed transport state) are out of scope.
