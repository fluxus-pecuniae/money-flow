# CI-CLEAN1 — Close the CI enforcement loop + reproducible installs

**Date**: 2026-06-10
**Scope**: CI/build config + docs only. No runtime, strategy, order, testnet, slate, approval, dashboard-behavior, or test-logic changes.

---

## Summary

Three related cleanups complete the CI enforcement layer built by CI-SAFE1 / DASH-QA1 and make installs reproducible:

1. **dashboard-qa promoted to blocking.** Removed `continue-on-error: true` from the `dashboard-qa` job. The 9 Playwright browser checks now gate merges, same as the blocking lane.
2. **Informational lane split.** The single `informational` job was sequential — when mypy failed, the full pytest step was skipped and never reported. Split into two independent jobs, `typecheck` (mypy strict) and `full-tests` (`pytest -q -m "not browser"`), both `continue-on-error: true`. A mypy failure no longer hides the full test signal.
3. **Reproducible installs.** Added `pip-tools` to `[project.optional-dependencies].dev`, generated `requirements-dev.lock` (226 pinned lines), and switched every CI job to install reproducibly:
   ```
   pip install -r requirements-dev.lock
   pip install -e . --no-deps
   ```

---

## Workflow shape after CI-CLEAN1

| Job | Gating | Notes |
|---|---|---|
| `blocking` | **Blocking** | JS syntax, compile, registry --check, safety invariants + 4 fast guard tests, text guards, secret hygiene, bundle hygiene, scoped ruff. |
| `dashboard-qa` | **Blocking** (new) | Installs Chromium, runs the 9 browser-smoke checks via the `browser` pytest marker. |
| `typecheck` | Informational | mypy strict. Pre-existing debt tracked in KNOWN_ISSUES K-031; promote to blocking when clean. |
| `full-tests` | Informational | `pytest -q -m "not browser"`. Browser tests are owned by `dashboard-qa`. |

---

## Reproducible installs

### Why
`pip install -e ".[dev]"` resolves floating ranges (`>=`) at install time, so CI runs and local installs can pick different transitive versions across days — leading to "it passed yesterday" flakes.

### How
- `requirements-dev.lock` is committed and contains a fully-pinned dependency graph (project + dev deps + transitive). Regenerate it after any `pyproject.toml` dependency change:
  ```
  pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml
  ```
- Every CI job installs from the lock and then adds the local package without re-resolving deps:
  ```
  pip install -r requirements-dev.lock
  pip install -e . --no-deps
  ```
- Local developers can do the same to match CI exactly. The existing `.venv` + pip workflow is preserved — no migration to a different package manager.

### Refresh checklist
1. Edit `pyproject.toml` deps.
2. `pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml`
3. `pip install -r requirements-dev.lock && pip install -e . --no-deps` locally to verify.
4. Run safety tests + dashboard-qa locally to confirm nothing broke.
5. Commit both files together.

---

## What did NOT change

- No runtime, strategy, order, testnet, slate, or approval state.
- No dashboard behavior. No `data-testid` or other markup change.
- No test logic. The same 9 dashboard-qa checks, the same blocking-lane tests, the same scanners.
- mypy strict mode is **not** silenced. The intended path is incremental typing toward green; promotion to blocking is gated on KNOWN_ISSUES K-031 being resolved.
- The `browser` pytest marker is **not** folded into the main test run. `dashboard-qa` remains a separate job because it needs `playwright install chromium`.

---

## Validation performed

- `pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml` → 226-line lock generated.
- `pip install -r requirements-dev.lock && pip install -e . --no-deps` → clean.
- `pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → 66 passed (locked deps).
- `pytest -m browser tests/dashboard_qa/ -q` → 9 passed (locked deps).
- `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → YAML OK.
- This PR's own CI run is the live validation that the new workflow shape works.

---

## Boundaries

CI/build config + docs only. No runtime behavior changed. No orders submitted. No private endpoints used. No API keys loaded. No strategy production-approved. Live trading remains not approved.
