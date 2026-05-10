# UAT0.3 Top-20 Universe And Drawdown Readiness

Recorded at: `2026-05-10T06:24:03Z`

## Scope

UAT0.3 is a safety/readiness phase. It adds a fixture-only top-20 UAT observation-universe resolver policy, completes the Hyperliquid public read-only info-type allowlist enough for a later UAT1 attempt, adds a runtime drawdown monitoring policy/model, and records a UAT1 readiness preflight.

UAT0.3 does not implement UAT1, does not connect to exchanges, does not call public, private, signed, or order endpoints, does not use exchange API keys, does not submit orders, does not add paper trading, does not add live trading, does not add routing behavior, does not change Money Flow rules, does not fetch real top-20 assets, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

UAT1 follow-up: `docs/uat1_public_read_only_connectivity_and_top20_universe.md` completed the allowed public-read-only endpoint verification and top-20 universe resolution. UAT2 remains blocked by shadow-readiness blockers.

## Evidence Candidate Versus UAT Universe

The ETH evidence candidate remains frozen:

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Value |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow first |

This is the strongest observed evidence candidate. It is not proof of edge, not strategy approval, not paper-trading approval, not live-trading approval, and not order-submission approval.

The UAT observation universe is separate: top-20 supported assets are used to validate platform behavior, market identity, no-trade reasoning, risk visibility, and operator explainability across a broader market set. Top-20 inclusion is not strategy approval.

## Top-20 Universe Policy

Status: `implemented`.

Testable model/service:

- `services.uat.universe.UATObservationUniversePolicy`
- `services.uat.universe.Top20UniverseResolver`

Policy defaults:

| Field | Value |
| --- | --- |
| Source ranking provider | Trusted public market-data source required in UAT1 |
| Top N | `20` |
| Volume metric | `24h_volume_usd` |
| Selected venue | `hyperliquid` |
| Market type requirement | `perpetual` |
| Product type requirement | `perp` |
| Quote asset requirement | `USDC` |
| Settlement asset requirement | `USDC` |
| Identity required | `true` |
| Venue support required | `true` |
| Private API keys allowed | `false` |
| Signed endpoints allowed | `false` |
| Deterministic tie-breaking | `source_rank_then_global_symbol` |

UAT0.3 uses fixture source data only. It does not fetch a live top-20 list.

## Top-20 Source Requirements

Future UAT1 source data must be public and unsigned.

Required source fields:

| Field | Required |
| --- | --- |
| Source provider / URL | yes |
| Source timestamp | yes |
| Source freshness | yes |
| Source rank | yes |
| 24h volume value | yes |
| Volume metric | `24h_volume_usd` |
| Symbol / asset id | yes |
| Deterministic tie-breaker | yes |

Forbidden source behavior:

- private API keys;
- signed endpoints;
- opaque rankings without volume value;
- stale source data without an explicit exclusion reason;
- permanent hardcoded top-20 lists.

## Hyperliquid Market Intersection Logic

Status: `implemented`.

The resolver takes caller-supplied top-volume source rows plus caller-supplied Hyperliquid public market metadata and returns included / excluded UAT observation candidates.

Required candidate fields:

| Field | Required |
| --- | --- |
| Global asset symbol | yes |
| Source rank | yes |
| Source 24h volume | yes |
| Venue | yes |
| Venue symbol | yes when included |
| Market type | yes when included |
| Product type | yes when included |
| Quote asset | yes when included |
| Settlement asset | yes when included |
| Venue asset id | yes when included |
| Included true/false | yes |
| Exclusion reason codes | yes when excluded |

Exclusion reason codes:

- `unsupported_by_venue`
- `unsupported_market_type`
- `missing_market_identity`
- `quote_asset_mismatch`
- `settlement_asset_mismatch`
- `insufficient_public_market_data`
- `not_enabled_for_uat`
- `top20_source_missing_volume`
- `top20_source_stale`

Included candidates are marked `observation_only=true`, `strategy_approved=false`, `paper_trading_approved=false`, and `live_trading_approved=false`.

## Hyperliquid Read-Only Endpoint Policy Status

Status: `implemented_as_policy_artifact`.

Testable artifact: `services.exchange.safety.HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST`.

Allowed future UAT1 category:

- `public_read_only`

Allowed unsigned public Hyperliquid info types:

- `meta`
- `metaAndAssetCtxs`
- `allMids`
- `l2Book`
- `candleSnapshot`
- `fundingHistory`

Forbidden in UAT1:

- private account state;
- private balances;
- private positions;
- private fills;
- private open orders;
- signed endpoints;
- API-key usage;
- order submission;
- cancel;
- amend;
- retry.

Endpoint URL status: `needs_verification`.

Sandbox/testnet behavior status: `needs_verification`.

Those checks are now UAT1 read-only tasks. They are not performed in UAT0.3.

## Runtime Drawdown Monitoring Policy

Status: `implemented_design_and_fixture_model`.

Testable model/service:

- `services.uat.drawdown.UATDrawdownPolicy`
- `services.uat.drawdown.UATDrawdownMonitor`

The monitor tracks caller-supplied observed equity values:

| Field | Status |
| --- | --- |
| Initial observed equity | `implemented` |
| Current observed equity | `implemented` |
| Realized PnL if available | `implemented` |
| Unrealized PnL if available | `implemented` |
| Max observed equity | `implemented` |
| Max drawdown amount | `implemented` |
| Max drawdown percent | `implemented` |
| Drawdown threshold | `implemented` |
| Threshold breach flag | `implemented` |
| Reason codes | `implemented` |
| Candidate id | `implemented` |
| Universe asset id | `implemented` |
| Timestamp | `implemented` |

If live balances/equity are not available, observations are labeled shadow or simulated. This is operational risk visibility only. It is not performance validation.

## Drawdown Requirements By UAT Phase

| UAT phase | Requirement | Status |
| --- | --- | --- |
| UAT1 read-only metadata | May proceed with drawdown monitor designed but not live-fed | `implemented_design` |
| UAT2 shadow run | Must expose shadow/runtime drawdown state to operator views | `required_before_uat2` |
| UAT3 sandbox orders | Must wire and test sandbox/live account drawdown feed | `required_before_uat3` |

## Redaction Verification Status

Status: `implemented_fixture_baseline`.

UAT0.2 added representative redaction helpers and adapter-helper error redaction. UAT0.3 adds fixture coverage for API-error-like structured payloads using nested dictionaries/lists and strings containing bearer tokens, API keys, secrets, passwords, and database URLs.

Remaining status: `needs_verification_before_uat2_or_uat3`.

Broader structured application logging, middleware error responses, and deployment-specific traceback behavior still need sandbox-like verification. UAT1 may proceed only as public read-only connectivity with no private endpoints, no API keys, and no order endpoints.

## Remaining Blockers

| Blocker | Status | Severity | Blocks UAT1? | Blocks UAT2? | Blocks UAT3? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| API auth/authz | `implemented` | P0 closed | no | no | no | Sensitive routes require scoped bearer auth. |
| Runtime private/order lockout | `implemented` | P0 closed | no | no | no | Defaults fail closed. |
| Adapter private/signed/order policy | `implemented` | P1 closed | no | no | no | Blocks before transport by default. |
| Hyperliquid public read-only allowlist | `implemented_as_policy_artifact` | P1 closed enough for UAT1 attempt | no | no | no | Actual endpoint URL/sandbox behavior is UAT1 verification. |
| Hyperliquid endpoint URL/sandbox verification | `needs_verification` | P1 | no | yes | yes | UAT1 read-only task; must not use private/signed/order endpoints. |
| Top-20 source/intersection resolver | `implemented_fixture_policy` | P1 closed enough for UAT1 attempt | no | no | no | Live source fetch deferred to UAT1. |
| Runtime drawdown monitor | `implemented_design_and_fixture_model` | P1 closed enough for UAT1 attempt | no | yes | yes | UAT2 needs operator-visible shadow state; UAT3 needs sandbox account feed. |
| Structured log/API error redaction | `implemented_fixture_baseline` | P1 partially closed | no | yes | yes | Broader app/middleware verification remains. |
| Risk/kill switch/audit visibility | `needs_verification` | P1/P2 | no | yes | yes | Later UAT0.x/UAT2/UAT3 checks. |

## UAT1 Readiness Decision

`UAT1 read-only connectivity may proceed`.

Conditions:

- UAT1 is public read-only only.
- UAT1 may fetch public top-20 source data and public Hyperliquid market metadata only.
- UAT1 must not use API keys.
- UAT1 must not call private endpoints.
- UAT1 must not call signed endpoints.
- UAT1 must not call order endpoints.
- UAT1 must not submit orders.
- UAT1 must keep paper trading, live trading, and exchange order submission disabled.
- UAT1 must verify actual Hyperliquid endpoint URLs and sandbox/testnet/public behavior before UAT2.

Rationale:

- No P0 blocker remains.
- Sensitive API auth/authz is in place.
- Runtime private/order lockouts are in place.
- Adapter-level private/signed/order guards are in place.
- Hyperliquid public read-only info types are classified.
- A fixture-tested top-20 universe resolver policy exists.
- A fixture-tested drawdown monitor policy/model exists; live-fed drawdown is not required for UAT1 read-only metadata.

UAT1 is still not paper trading, not live trading, not order submission, not a profitability test, and not strategy approval.

UAT1 follow-up result: UAT1 public read-only connectivity is complete under those constraints. UAT2 is blocked until operator-visible shadow drawdown state, shadow signal audit surfaces, and broader structured log/API error redaction verification are complete.

## Boundary Confirmation

UAT0.3 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, exchange calls, public exchange calls, private/signed calls, order endpoint calls, evidence packs, or strategy-rule changes.
