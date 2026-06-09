# CI-SAFE1 — CI Gate and Trading Safety Invariants

**Date**: 2026-06-09  
**Scope**: Automated safety enforcement — GitHub Actions CI, trading safety invariant tests, registry consistency guards, text guards, secret hygiene, review bundle hygiene.

---

## Summary

CI-SAFE1 adds a GitHub Actions CI workflow and a set of interlocking safety checks that make trading-safety regression visually impossible to merge undetected. The blocking CI lane enforces:

1. **JS syntax check** — `node --check apps/dashboard/evidence-dashboard.js`
2. **Python compile check** — `python -m compileall -q core services apps tests scripts`
3. **Registry up-to-date check** — `python scripts/export_current_truth.py --check`
4. **Trading safety invariants** — `test_trading_safety_invariants.py` (RuntimeSafetyPolicy defaults, VenueIntegrationConfig defaults, endpoint classification, PT-RT1.6 slate)
5. **Registry consistency** — `test_current_truth_consistency.py`, `test_current_truth_registry.py` (Machine Block, dashboard JS constants, on-disk JSON all in sync)
6. **Trading safety text guards** — `scripts/check_trading_safety_text.py` + `test_trading_safety_text_guards.py` (no positive live/production approval language in source)
7. **Secret hygiene scan** — `scripts/check_secret_hygiene.py` + `test_secret_hygiene.py` (no obvious committed key material)
8. **Review bundle hygiene** — `test_review_bundle_hygiene.py` (.archiveignore contract)
9. **Lint (scoped ruff)** — ruff check + format on CI-SAFE1 authored modules

An informational lane (continue-on-error) runs mypy strict and the full pytest suite — failures are visible in the PR but do not block merge.

---

## Safety Properties Enforced

| Property | Where enforced |
|---|---|
| `RuntimeSafetyPolicy.live_trading_enabled = False` by default | `test_trading_safety_invariants.py` |
| `RuntimeSafetyPolicy.exchange_order_submission_enabled = False` by default | `test_trading_safety_invariants.py` |
| `RuntimeSafetyPolicy.private_exchange_endpoints_enabled = False` by default | `test_trading_safety_invariants.py` |
| `RuntimeSafetyPolicy.sandbox_mode_required = True` by default | `test_trading_safety_invariants.py` |
| All lockout properties `True` by default | `test_trading_safety_invariants.py` |
| Only `money_flow_v1_2_baseline` testnet-eligible | `test_trading_safety_invariants.py` |
| Active timeframes exactly `1h`, `4h`, `1d` | `test_trading_safety_invariants.py` |
| `15m` paused (in `PT_RT1_4_DISABLED_TIMEFRAMES`) | `test_trading_safety_invariants.py` |
| ORDER_* endpoints blocked by default | `test_trading_safety_invariants.py` |
| PRIVATE_* endpoints blocked by default | `test_trading_safety_invariants.py` |
| Machine Block in sync with `current_truth.json` | `test_current_truth_consistency.py` |
| Dashboard JS constants in sync with registry | `test_current_truth_consistency.py` |
| No positive approval language in source | `check_trading_safety_text.py` |
| No real secrets in committed files | `check_secret_hygiene.py` (lightweight; see K-029) |
| Sensitive paths excluded from review bundle | `test_review_bundle_hygiene.py` |

---

## Files Created / Modified

### New files
- `.github/workflows/ci.yml` — GitHub Actions CI workflow (blocking + informational lanes)
- `scripts/check_trading_safety_text.py` — text guard scanner
- `scripts/check_secret_hygiene.py` — secret hygiene scanner
- `tests/test_trading_safety_invariants.py` — safety invariant tests (Must 2)
- `tests/test_trading_safety_text_guards.py` — text guard unit + repo scan tests (Must 3)
- `tests/test_secret_hygiene.py` — hygiene scanner unit + repo scan tests (Must 4)
- `tests/test_review_bundle_hygiene.py` — .archiveignore contract tests (Must 5)
- `tests/test_current_truth_consistency.py` — Machine Block + dashboard JS constant tests (Must 2b)
- `docs/ci_safe1_ci_gate_and_trading_safety_invariants.md` — this document

### Updated files
- `CHANGELOG.md` — v2026.06.09.002 entry
- `KNOWN_ISSUES.md` — K-029 (lightweight secret scan caveat)
- `REPO_TREE.md` — new CI-SAFE1 entries
- `TODO.md` — updated
- `money-flow/01_Current_Phase.md` — CI-SAFE1 section
- `money-flow/03_Decision_Log.md` — decision entry
- `money-flow/05_Agent_Coordination.md` — CI-SAFE1 row → done

---

## Known Limitations

**K-029**: `scripts/check_secret_hygiene.py` is a lightweight pattern scan only. It does NOT scan git history, binary files, or use entropy analysis. It is not a substitute for professional secret scanning (gitleaks, truffleHog). Use it to catch obvious mistakes; run a proper scanner for full audit coverage.

**Pre-existing ruff debt**: The CI ruff step is scoped to CI-SAFE1 authored modules. ~120+ files in the codebase have pre-existing lint violations (B008 FastAPI `Depends` patterns, E501 line length, I001 import ordering). These are tracked as tech debt and should be addressed in a separate lint-debt cleanup pass.

---

## Validation Performed

```
node --check apps/dashboard/evidence-dashboard.js                         → OK
python -m compileall -q core services apps tests scripts                  → OK
python scripts/export_current_truth.py --check                            → OK
python scripts/check_trading_safety_text.py                               → OK
python scripts/check_secret_hygiene.py                                    → OK
python -m pytest -q tests/test_trading_safety_invariants.py \
  tests/test_trading_safety_text_guards.py tests/test_secret_hygiene.py \
  tests/test_review_bundle_hygiene.py tests/test_current_truth_consistency.py \
  tests/test_current_truth_registry.py                                    → 123 passed
ruff check + format --check (CI-SAFE1 modules)                            → clean
```

---

## Boundaries

No runtime behavior was changed. No orders were submitted. No private, signed, or order endpoints were used. No API keys were loaded. No testnet data was used as strategy truth. No strategy was production-approved. Live trading remains not approved.
