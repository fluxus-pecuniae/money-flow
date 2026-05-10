# UAT0 Safety / Security / Runtime Hardening

Recorded at: `2026-05-09T14:17:37Z`

UAT0.1 update: `docs/uat0_1_api_auth_runtime_lockout.md` closes the P0 API auth/authz gap for sensitive routes and adds an inspectable runtime safety policy.

UAT0.2 update: `docs/uat0_2_adapter_runtime_policy_and_redaction.md` closed the adapter-level runtime-policy enforcement baseline, added a testable Hyperliquid future-UAT1 read-only allowlist artifact, and strengthened representative redaction checks. UAT0.2 kept UAT1 blocked at that time; UAT0.3 supersedes that decision for public read-only connectivity.

UAT0.3 update: `docs/uat0_3_top20_universe_and_drawdown_readiness.md` adds a fixture-tested top-20 UAT observation-universe resolver policy, completes the Hyperliquid public read-only info-type allowlist enough for a later UAT1 attempt, adds a fixture-tested runtime drawdown monitor policy/model, and changes the UAT1 decision to `UAT1 read-only connectivity may proceed` under public-read-only constraints. UAT0.3 makes no exchange calls and does not implement UAT1.

UAT1 update: `docs/uat1_public_read_only_connectivity_and_top20_universe.md` verifies explicit public-read-only Hyperliquid endpoint behavior, fetches a no-key public CoinGecko top-volume source, resolves the Hyperliquid-supported observation universe, and kept UAT2 blocked at that time pending shadow-readiness blockers. UAT1 does not use API keys, call private/signed/order endpoints, submit orders, run Money Flow live, create strategy/execution artifacts, add paper/live behavior, change Money Flow rules, or generate evidence packs.

UAT1.1 update: `docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md` adds model/report-only shadow signal audit, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 shadow strategy run may proceed as a future no-order phase; UAT1.1 does not implement UAT2, run Money Flow over live data, submit orders, or create strategy/execution artifacts.

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
| API authentication / authorization | `implemented` | UAT0.1 protects `/api/v1` with scoped bearer auth and stricter operator/admin scopes for sensitive route groups. |
| Secret/key hygiene | `implemented_baseline` | `.env`, virtualenvs, DB files, caches, generated evidence packs, and review bundles are excluded by `.archiveignore`; UAT0.2 adds representative redaction tests, while full application log/API redaction review remains. |
| Runtime mode separation | `implemented` | UAT0.1 adds `RuntimeSafetyPolicy`; UAT0.2 verifies adapter-helper enforcement before private/signed/order transport. |
| Sandbox/live separation | `needs_verification` | UAT0.1 adds runtime lockout flags and API auth; UAT0.2 adds the Hyperliquid future-UAT1 read-only allowlist artifact, but actual endpoint verification remains deferred to UAT1. |
| Risk limits | `needs_verification` | Risk services and readiness checks exist; broad UAT candidate/top-20 enforcement still needs verification. |
| Drawdown monitoring | `implemented_shadow_visibility` | UAT0.3 adds a fixture-tested UAT drawdown monitor policy/model; UAT1.1 adds operator-visible shadow drawdown state for UAT2. UAT3 still needs sandbox/live account feed wiring. |
| Kill switch / disable controls | `needs_verification` | `RISK_TRADING_ENABLED=false` blocks risk approval, but global UAT/candidate/universe disable controls are not complete. |
| Audit logging | `implemented_shadow_audit_surface` | Persisted workflow artifacts provide partial traceability; UAT1.1 adds model/report-only shadow signal audit records for future UAT2. UAT mode-change and UAT3 lifecycle audit verification remain deferred. |
| Approval gates | `implemented` | Phase 7 approval gates are lineage/scope-bound; they still need UAT3-specific verification before sandbox orders. |
| Duplicate order / submit lease | `implemented` | Submit leases and adapter uncertainty states block unsafe repeat submit guidance; UAT3 must reverify under sandbox lifecycle tests. |
| Uncertainty handling | `implemented` | `adapter_submit_may_have_started` and `adapter_submit_persistence_unknown` require manual reconciliation before repeat submit. |
| Debug stack trace exposure | `needs_verification` | `APP_DEBUG` defaults false, but structured traceback/log exposure needs explicit sandbox-like verification. |
| Endpoint safety | `implemented` | UAT0.1 protects sensitive route groups with auth/scopes; UAT0.2 blocks private/signed/order adapter paths before transport by default. |
| UAT1 readiness | `blocked` | UAT1 read-only connectivity should not proceed until P0/P1 blockers below are closed or explicitly accepted. |

## API Authentication / Authorization Review

Inspected:

- `apps/api/app/api/routes.py`
- `apps/api/app/dependencies.py`
- `apps/api/`
- `core/schemas/api.py`

Sensitive route groups include mandate/account setup, exchange sync, private-state inspection, strategy evaluation, routing automation approvals, readiness, child-intent submit/cancel/amend/recovery, and operator workflow inspection.

UAT0.1 status: `implemented`.

Sensitive `/api/v1` routes now require scoped bearer auth. High-risk administrative consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes. See `docs/uat0_1_api_auth_runtime_lockout.md` for the route inventory.

Superseded UAT1 preflight items, now closed by UAT0.3/UAT1/UAT1.1:

- verify selected Hyperliquid public read-only endpoint URLs and sandbox/testnet behavior without private/signed calls;
- complete representative structured log/API error redaction verification;
- implement top-20 symbol/market identity resolution policy.

## Secret / Key Hygiene Review

Current positives:

- `.env`, `.venv`, `.git`, local DB/socket data, caches, generated evidence reports, generated candle/import outputs, Obsidian app state, and review ZIPs are excluded by `.archiveignore`.
- Review bundles use `scripts/create_review_bundle.py`.
- Config summary responses do not expose raw DB URLs, API keys, or secrets.
- Venue account API responses expose credential reference labels rather than raw secrets.

Remaining status: `implemented_baseline`.

Required hardening:

- verify no secrets appear in all structured logs or tracebacks;
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

UAT0.1 adds `RuntimeSafetyPolicy`, with fail-safe defaults.

Required before UAT1/UAT2:

- verify Hyperliquid public read-only endpoint URLs and sandbox/testnet behavior in the explicit UAT1 phase;
- keep `exchange_order_submission_enabled=false`, `paper_trading_enabled=false`, `live_trading_enabled=false`, and `private_exchange_endpoints_enabled=false` until later explicit phases.

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
| `runtime_drawdown_monitoring_status` | `implemented_design` | UAT0.3 adds a fixture-tested drawdown monitor policy/model from caller-supplied observed equity values. It is not live-fed account truth yet. |
| `strategy_validation_drawdown_status` | `implemented` | Backtest/replay reports include closed-trade and mark-to-market drawdown. |
| `uat_drawdown_blocker_status` | `implemented_for_uat2_shadow_required_before_uat3` | UAT1.1 adds shadow drawdown state, thresholds, reason codes, and operator visibility for UAT2. UAT3 still needs sandbox/live account drawdown feed wiring and testing. |

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
| API auth | `implemented` | P0 closed by UAT0.1 | yes | yes | yes | Sensitive `/api/v1` routes require scoped bearer auth. |
| Secret hygiene | `implemented_baseline` | P1 partially closed by UAT0.2 | yes | yes | yes | Bundle hygiene and representative redaction are tested; full log/error review remains. |
| Runtime mode separation | `implemented` | P1 closed by UAT0.2 | yes | yes | yes | `RuntimeSafetyPolicy` exists and adapter helper enforcement is verified for private/signed/order categories. |
| Live endpoint lockout | `implemented` | P0 closed by UAT0.1 / adapter baseline closed by UAT0.2 | yes | yes | yes | Lockout flags default safe and private/signed/order adapter paths block before transport. |
| Sandbox/testnet config | `needs_verification` | P1 | yes | yes | yes | Hyperliquid UAT1 read-only allowlist exists; actual endpoint URL/sandbox behavior still needs UAT1 verification. |
| Top-20 universe policy | `implemented` | P1 closed by UAT0.3 | yes | yes | yes | Fixture-tested policy exists; UAT1 must fetch public source/venue metadata and run the resolver with real read-only data. |
| Symbol/market identity resolution | `implemented_fixture_policy` | P1 closed enough for UAT1 attempt | yes | yes | yes | UAT0.3 defines venue/product/quote/settlement identity and exclusion reason policy; UAT1 must verify with public metadata. |
| Fill-timing policy | `implemented` | P2 | no | yes | yes | UAT2 uses `next_candle_open` and `next_candle_close`; same-candle stays research-only. |
| Risk limits | `needs_verification` | P1 | no | yes | yes | Existing risk checks need UAT candidate/top-20 verification. |
| Drawdown monitoring | `implemented_design` | P1 closed enough for UAT1 attempt | no | yes | yes | UAT0.3 adds fixture-tested model; UAT2/UAT3 need live/shadow wiring. |
| Kill switch | `needs_verification` | P1 | no | yes | yes | Need global/candidate/universe/order/venue disable controls. |
| Debug stack traces | `needs_verification` | P1 | yes | yes | yes | Sandbox-like API error behavior must be verified. |
| Audit logging | `needs_verification` | P1 | no | yes | yes | Shadow and UAT mode audit fields need coverage. |
| Approval gates | `implemented` | P2 | no | no | yes | Existing gates are strong; sandbox-order path needs UAT3 proof. |
| Submit lease / duplicate prevention | `implemented` | P2 | no | no | yes | Existing submit lease/uncertainty states need sandbox lifecycle proof. |
| Exchange endpoint safety | `implemented_baseline` | P1 closed enough for UAT1 attempt | yes | yes | yes | Adapter-level private/signed/order guards and Hyperliquid public read-only info-type allowlist exist; actual UAT1 read-only connectivity remains deferred to the UAT1 phase. |
| Dashboard/operator visibility | `needs_verification` | P2 | no | yes | yes | UAT2 implementation should expose top-20 shadow and risk/no-trade visibility; UAT1.1 adds the model/report-only audit surface. |

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

`UAT1 read-only connectivity may proceed`.

UAT1 has now been completed under those constraints. UAT1.1 also completed the shadow-readiness blockers for no-order UAT2.

UAT2 readiness update:

`UAT2 shadow strategy run may proceed`.

Conditions:

- UAT1 is public read-only only.
- UAT1 may fetch public top-20 source data and public Hyperliquid market metadata only.
- UAT1 must not use API keys, private endpoints, signed endpoints, order endpoints, paper trading, live trading, or order submission.
- UAT2 must remain shadow-only.
- UAT2 must compare `next_candle_open` and `next_candle_close`.
- UAT2 must keep `same_candle_close_research_only` research-only.
- UAT2 must not submit orders, use API keys, call private/signed/order endpoints, create strategy/execution artifacts, or approve paper/live trading.

Remaining blockers for UAT2/UAT3:

- P2 deployment-specific middleware/logging redaction smoke tests remain useful before or during UAT2.
- P1 UAT3 sandbox/live account drawdown feed is not wired.
- P1 risk/kill-switch/audit/operator visibility checks still need UAT-specific verification.

No exchange calls were made. No orders were submitted. No paper/live behavior was added. No Money Flow rules changed.
