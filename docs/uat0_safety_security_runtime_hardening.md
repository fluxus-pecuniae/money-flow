# UAT0 Safety / Security / Runtime Hardening

Recorded at: `2026-05-09T14:17:37Z`

## Scope

UAT0 is a safety, security, runtime, and operational-readiness audit. It does not connect to exchanges, does not use API keys, does not call private or signed endpoints, does not submit orders, does not run paper trading, does not run live trading, does not change Money Flow rules, and does not generate evidence packs.

UAT validates plumbing and behavior. UAT is not performance validation.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Current Candidate And Observation Universe

### Evidence Candidate

The frozen evidence candidate from SV1.18 remains:

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Value |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow first |

This candidate is the strongest observed Strategy Validation pocket. It is not proof of edge, not paper-trading authorization, not live-trading authorization, and not exchange order-submission authorization.

### UAT Observation Universe

Future UAT observation must not be ETH-only. UAT observation should cover the top 20 high-volume crypto assets supported by the selected UAT venue/environment so the platform can validate symbol mapping, market identity, no-trade reasoning, risk visibility, operator explainability, and shadow would-trade behavior across a broader market set.

The UAT observation universe is not a list of approved strategy candidates.

Future UAT1 or later selection process:

1. Pull top 20 by volume from a trusted public market-data source.
2. Intersect that list with assets supported by the selected UAT venue/environment.
3. Resolve market identity by venue, product, quote asset, and settlement asset.
4. Include only assets with clean identity and public market-data support.
5. Keep unsupported or mismatched assets excluded with explicit reason codes.

Required future fields per candidate asset:

| Field | Required |
| --- | --- |
| Global symbol | yes |
| Source ranking | yes |
| 24h volume | yes |
| Selected venue support | yes/no |
| Venue symbol | yes when supported |
| Market type | yes |
| Product type | yes |
| Quote asset | yes |
| Settlement asset | yes |
| Included/excluded | yes |
| Exclusion reason | yes when excluded |

Reason codes:

- `unsupported_by_venue`
- `unsupported_market_type`
- `missing_market_identity`
- `quote_asset_mismatch`
- `settlement_asset_mismatch`
- `insufficient_public_market_data`
- `not_enabled_for_uat`

No top-20 list was fetched in UAT0. No top-20 asset is approved for paper trading, live trading, or order submission.

## UAT Shadow Fill-Timing Policy

Future UAT2 shadow reports must compare:

- `next_candle_open`
- `next_candle_close`

The existing mode `same_candle_close_research_only` remains research-only and must not be the primary UAT shadow assumption.

Future UAT2 reports should show, per symbol/component:

- signal count
- would-trade count
- `next_candle_open` hypothetical behavior
- `next_candle_close` hypothetical behavior
- divergence between open/close assumptions
- no-trade reasons
- risk blocks
- operator-visible explanation

## UAT0 Safety Status

| Area | Status | Notes |
| --- | --- | --- |
| API authentication / authorization | `missing` | FastAPI sensitive routes do not use an authentication or authorization dependency. |
| Secret/key hygiene | `needs_verification` | `.env`, virtualenvs, DB files, caches, generated evidence packs, and review bundles are excluded by `.archiveignore`; log/API redaction still needs explicit UAT verification. |
| Runtime mode separation | `needs_verification` | Execution and venue defaults are conservative, but there is no single explicit UAT mode lockout for all API/runtime paths. |
| Sandbox/live separation | `blocked` | Live submission flags default false, but endpoint-level access control and UAT environment gating are not complete. |
| Risk limits | `needs_verification` | Risk services and readiness checks exist; broad UAT candidate/top-20 enforcement still needs verification. |
| Drawdown monitoring | `missing` | Strategy Validation drawdown exists; runtime UAT drawdown monitoring is not a real operator control yet. |
| Kill switch / disable controls | `needs_verification` | `RISK_TRADING_ENABLED=false` blocks risk approval, but global UAT/candidate/universe disable controls are not complete. |
| Audit logging | `needs_verification` | Persisted workflow artifacts provide partial traceability; UAT mode changes, top-20 inclusion/exclusion, and shadow decisions need explicit audit coverage. |
| Approval gates | `implemented` | Phase 7 approval gates are lineage/scope-bound; they still need UAT3-specific verification before sandbox orders. |
| Duplicate order / submit lease | `implemented` | Submit leases and adapter uncertainty states block unsafe repeat submit guidance; UAT3 must reverify under sandbox lifecycle tests. |
| Uncertainty handling | `implemented` | `adapter_submit_may_have_started` and `adapter_submit_persistence_unknown` require manual reconciliation before repeat submit. |
| Debug stack trace exposure | `needs_verification` | `APP_DEBUG` defaults false, but structured traceback/log exposure needs explicit sandbox-like verification. |
| Endpoint safety | `blocked` | Sensitive API routes are unprotected by auth and include exchange/private-state/readiness/approval/submission surfaces. |
| UAT1 readiness | `blocked` | UAT1 read-only connectivity should not proceed until P0/P1 blockers below are closed or explicitly accepted. |

## API Authentication / Authorization Review

Inspected:

- `apps/api/app/api/routes.py`
- `apps/api/app/dependencies.py`
- `apps/api/`
- `core/schemas/api.py`

Sensitive route groups currently include mandate/account setup, exchange sync, private-state inspection, strategy evaluation, routing automation approvals, readiness, child-intent submit/cancel/amend/recovery, and operator workflow inspection. These routes are mounted through normal dependency injection, but no route-level authentication or authorization dependency is enforced.

UAT0 status: `missing`.

Required before UAT1:

- define local/dev/test/sandbox access policy;
- add authentication and role/scope checks for sensitive route groups;
- ensure exchange/private-state/readiness/submission/approval routes cannot be reached from unauthenticated clients;
- add tests proving unauthorized requests are rejected.

## Secret / Key Hygiene Review

Current positives:

- `.env`, `.venv`, `.git`, local DB/socket data, caches, generated evidence reports, generated candle/import outputs, Obsidian app state, and review ZIPs are excluded by `.archiveignore`.
- Review bundles use `scripts/create_review_bundle.py`.
- Config summary responses do not expose raw DB URLs, API keys, or secrets.
- Venue account API responses expose credential reference labels rather than raw secrets.

Remaining status: `needs_verification`.

Required hardening:

- verify no secrets appear in structured logs or tracebacks;
- add explicit redaction for key/secret/token-like fields in error/log paths;
- keep DB URLs sanitized in docs and operator output;
- keep `.env` and generated local artifacts out of review bundles.

## Runtime Mode / Environment Gating

Current safe defaults:

- execution `dry_run=true`;
- `live_submission_phase_enabled=false`;
- `routed_submission_phase_enabled=false`;
- venue `submission_enabled=false` by default;
- venue `submission_authorized=false` by default;
- venue `read_only_mode=true` and/or `dry_run=true` defaults are present for supported venues.

Gap:

There is not yet one explicit UAT mode control that locks the entire API/runtime into read-only or shadow behavior across strategy, risk, exchange, and submission surfaces.

Required before UAT1/UAT2:

- fail-safe default such as `uat_mode=disabled|read_only|shadow`;
- `exchange_order_submission_enabled=false`;
- `paper_trading_enabled=false`;
- `live_trading_enabled=false`;
- `sandbox_mode_required=true` for UAT work;
- explicit tests that live endpoints and order submission cannot be reached accidentally.

## Exchange Endpoint Safety

No exchange calls were made in UAT0.

| Venue | Public read-only known? | Private disabled by default? | Order endpoint disabled by default? | Sandbox/testnet known? | Notes |
| --- | --- | --- | --- | --- | --- |
| Hyperliquid | `implemented` | `implemented` | `implemented` | `implemented` | Testnet URL support exists; private/order use still requires explicit credentials and submit gates. |
| Aster | `implemented` | `implemented` | `implemented` | `missing` | Public integration exists; sandbox/testnet support is not established. |
| Binance | `implemented` | `implemented` | `implemented` | `needs_verification` | Testnet config exists but default URL is live public; must be explicitly gated before UAT. |
| OKX | `implemented` | `implemented` | `implemented` | `implemented` | Demo mode support exists; still requires endpoint/auth policy before UAT. |
| Coinbase Advanced Trade | `implemented` | `implemented` | `implemented` | `missing` | Sandbox/testnet path is not established in current config. |
| Kraken | `implemented` | `implemented` | `implemented` | `missing` | Sandbox/testnet path is not established in current config. |

Top-20 universe resolution must not imply trading eligibility.

## Risk / Drawdown / Kill Switch Review

Risk services enforce source-policy and eligibility checks for the existing planning/routing/execution workflow, and submission readiness rechecks venue/account/config gates. Those checks are useful but not sufficient for UAT without API auth and UAT-mode lockout.

Required report fields:

| Field | Status | Notes |
| --- | --- | --- |
| `runtime_drawdown_monitoring_status` | `missing` | Runtime API portfolio summary currently exposes placeholder drawdown truth, not a UAT monitor. |
| `strategy_validation_drawdown_status` | `implemented` | Backtest/replay reports include closed-trade and mark-to-market drawdown. |
| `uat_drawdown_blocker_status` | `blocked` | UAT2/UAT3 need runtime drawdown state, thresholds, reason codes, and operator visibility. |

Kill-switch status is `needs_verification`: risk-level trading disable exists, but explicit global UAT disable, candidate disable, universe disable, venue disable, and order-submission disable controls must be verified or added before shadow/sandbox phases.

## Approval / Submit-Lease / Duplicate-Order Review

Current status:

- approval creation remains separate from action execution;
- active approvals are lineage/scope-bound;
- expired/stale approvals cannot authorize current action hooks;
- dry-run/manual-only steps cannot become valid action approvals;
- submitted-order handoff remains readiness-gated;
- active submit leases block repeat submit guidance;
- adapter-submit uncertainty blocks unsafe repeat attempts;
- persistence-unknown states require manual reconciliation;
- same-target retry remains bounded;
- no cross-venue retry or route executor exists.

Status for UAT0: `implemented`, with UAT3-specific verification still required before any sandbox order phase.

## Debug Stack Trace / Error Exposure Review

`APP_DEBUG` defaults false. Structured traceback processors exist in logging setup, so sandbox-like error/log behavior needs explicit verification.

Status: `needs_verification`.

Required before UAT1:

- confirm user-facing API errors do not expose stack traces in sandbox-like mode;
- confirm exception messages do not leak DB URLs, API keys, wallet refs, credential refs, or request signatures;
- add regression tests for structured error responses where practical.

## Audit Logging / Operator Traceability Review

Existing persisted workflow artifacts provide partial auditability for strategy decisions, desired trades, route assessments, approvals, readiness, submitted orders, reconciliation, and operator routed workflow inspection.

Before UAT2/UAT3, audit fields must explicitly cover:

- strategy signal / would-trade decision;
- no-trade reason;
- rejected-signal reason;
- top-20 universe inclusion/exclusion;
- UAT candidate selection;
- UAT mode changes;
- risk blocks;
- approval creation and action hooks;
- readiness assessment;
- submit handoff;
- submitted-order lifecycle;
- manual resolution.

Status: `needs_verification`.

## UAT0 Blocker Matrix

| Area | Status | Severity | Required before UAT1? | Required before UAT2? | Required before UAT3? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| API auth | `missing` | P0 | yes | yes | yes | Sensitive API routes are unauthenticated. |
| Secret hygiene | `needs_verification` | P1 | yes | yes | yes | Bundle hygiene is good; log/error redaction needs proof. |
| Runtime mode separation | `needs_verification` | P1 | yes | yes | yes | Need explicit UAT/read-only/shadow/live lockout semantics. |
| Live endpoint lockout | `blocked` | P0 | yes | yes | yes | Endpoint safety depends on auth plus mode gating. |
| Sandbox/testnet config | `needs_verification` | P1 | yes | yes | yes | Hyperliquid/OKX known; venue-specific policy needed. |
| Top-20 universe policy | `implemented` | P2 | yes | yes | yes | Policy exists; UAT1 must implement source/intersection process. |
| Symbol/market identity resolution | `needs_verification` | P1 | yes | yes | yes | Must prove venue/product/quote/settlement identity before top-20 observation. |
| Fill-timing policy | `implemented` | P2 | no | yes | yes | UAT2 uses `next_candle_open` and `next_candle_close`; same-candle stays research-only. |
| Risk limits | `needs_verification` | P1 | no | yes | yes | Existing risk checks need UAT candidate/top-20 verification. |
| Drawdown monitoring | `missing` | P1 | no | yes | yes | Runtime UAT drawdown monitor is absent. |
| Kill switch | `needs_verification` | P1 | no | yes | yes | Need global/candidate/universe/order/venue disable controls. |
| Debug stack traces | `needs_verification` | P1 | yes | yes | yes | Sandbox-like API error behavior must be verified. |
| Audit logging | `needs_verification` | P1 | no | yes | yes | Shadow and UAT mode audit fields need coverage. |
| Approval gates | `implemented` | P2 | no | no | yes | Existing gates are strong; sandbox-order path needs UAT3 proof. |
| Submit lease / duplicate prevention | `implemented` | P2 | no | no | yes | Existing submit lease/uncertainty states need sandbox lifecycle proof. |
| Exchange endpoint safety | `blocked` | P0 | yes | yes | yes | No UAT connectivity until auth/mode/endpoint policy is closed. |
| Dashboard/operator visibility | `needs_verification` | P2 | no | yes | yes | UAT2 needs top-20 shadow and risk/no-trade visibility. |

## Corrected UAT Roadmap

### UAT0 - Safety / Security / Runtime Hardening

Allowed: inspect code, harden safe defaults, document blockers, define top-20 policy, define fill-timing policy.

Forbidden: exchange calls, private/signed endpoints, order submission, paper/live trading.

### UAT1 - Top-20 Universe + Read-Only Venue/Market Metadata

Allowed: fetch public market metadata, fetch a public top-20 volume list from a trusted source, intersect top-20 with selected venue-supported assets, verify symbol mapping, verify public read-only market data paths.

Forbidden: private endpoints, signed endpoints, order endpoints, paper trades, live trades.

### UAT2 - Shadow Strategy Run Across Top-20 Universe

Allowed: evaluate signals, produce would-trade decisions, compare `next_candle_open`, compare `next_candle_close`, log no-trade reasons, inspect signal frequency, inspect risk visibility.

Forbidden: order submission, paper trades, live trades.

### UAT3 - Approval-Gated Sandbox Orders

Allowed: tiny sandbox/testnet orders only after explicit approval gates, starting with a small operator-approved subset.

Forbidden: automatic top-20 order submission, live trading, ungated paper trading, routing expansion.

### UAT4 - Sandbox Review

Review behavior, lifecycle, rejects, fills, cancels, slippage, logs, risk visibility, and operational safety.

This is still not proof of edge.

## UAT1 Readiness Decision

`UAT1 is blocked`.

Blocking reasons:

- P0 API authentication / authorization is missing for sensitive routes.
- P0 live endpoint lockout and exchange endpoint safety depend on auth plus explicit UAT mode gating.
- P1 secret/log/error redaction needs sandbox-like verification.
- P1 runtime mode separation needs a single fail-safe UAT/read-only/shadow/live policy.
- P1 symbol/market identity resolution and selected-venue top-20 process are not implemented yet.

No exchange calls were made. No orders were submitted. No paper/live behavior was added. No Money Flow rules changed.
