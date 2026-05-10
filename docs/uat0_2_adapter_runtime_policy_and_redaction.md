# UAT0.2 Adapter Runtime Policy And Redaction

Recorded at: `2026-05-10T05:38:05Z`

UAT0.3 follow-up: `docs/uat0_3_top20_universe_and_drawdown_readiness.md` adds the fixture-tested top-20 resolver policy and drawdown monitor model, extends the Hyperliquid public read-only info-type allowlist, and records that UAT1 public read-only connectivity may proceed under strict no-private/no-signed/no-order/no-API-key constraints.

## Scope

UAT0.2 is a narrow safety-hardening phase. It verifies adapter-level runtime-policy enforcement, defines the selected-venue read-only endpoint allowlist for future UAT1, and strengthens representative redaction checks.

UAT0.2 does not implement UAT1, does not connect to exchanges, does not call public, private, signed, or order endpoints, does not use exchange API keys, does not submit orders, does not add paper trading, does not add live trading, does not add routing behavior, does not change Money Flow rules, and does not generate evidence packs.

Paper trading is not approved. Live trading is not approved. Exchange order submission is not approved.

## Adapter Runtime Policy Status

Status: `implemented`.

Adapter network helpers now classify endpoint intent before invoking transport:

- REST adapters use `services.exchange.safety.classify_rest_endpoint`.
- Hyperliquid `info` payloads use `classify_hyperliquid_info_payload`.
- Hyperliquid `exchange` payloads use `classify_hyperliquid_exchange_payload`.

Private, signed, unknown, and order-like categories are blocked before transport unless the central `RuntimeSafetyPolicy` explicitly enables the required capability. Defaults remain fail-closed:

| Runtime policy field | Default | Status |
| --- | --- | --- |
| `private_exchange_endpoints_enabled` | `false` | `verified` |
| `exchange_order_submission_enabled` | `false` | `verified` |
| `live_trading_enabled` | `false` | `verified` |
| `paper_trading_enabled` | `false` | `verified` |
| `sandbox_mode_required` | `true` | `verified` |

Blocked adapter calls raise before fake or real transport is invoked. This is adapter-level protection; API auth is not the only protection.

## Adapter Safety Inventory

Endpoint categories:

- `public_read_only`
- `private_read_only`
- `private_signed`
- `order_submission`
- `order_cancel`
- `order_amend`
- `order_retry_or_recovery`
- `unknown`

| Venue | Method / surface | Endpoint type | Runtime policy check | Guard status | Allowed in UAT1? | Remaining blocker |
| --- | --- | --- | --- | --- | --- | --- |
| Hyperliquid | `sync_symbols`, public metadata, top of book / depth where public | `public_read_only` | category classification | `implemented` | yes, after UAT1 approval | selected UAT1 connectivity not implemented |
| Hyperliquid | `orderStatus`, `userFills`, open orders, positions, account state | `private_read_only` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| Hyperliquid | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Hyperliquid | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Hyperliquid | `amend_order` | `order_amend` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Aster | public ping, exchange info, candles, top of book | `public_read_only` | category classification | `implemented` | not selected for UAT1 | deferred venue |
| Aster | balance, open orders, private trade evidence | `private_read_only` / `private_signed` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| Aster | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Aster | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Binance | public ping, exchange info, candles, top of book | `public_read_only` | category classification | `implemented` | not selected for UAT1 | deferred venue |
| Binance | account, open orders, private trade evidence | `private_read_only` / `private_signed` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| Binance | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Binance | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| OKX | public time, instruments, candles, market books | `public_read_only` | category classification | `implemented` | not selected for UAT1 | deferred venue |
| OKX | account balance, order state, private positions/fills | `private_read_only` / `private_signed` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| OKX | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| OKX | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| OKX | `amend_order` | `order_amend` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Coinbase Advanced Trade | public time, products, candles, best bid/ask | `public_read_only` | category classification | `implemented` | not selected for UAT1 | deferred venue |
| Coinbase Advanced Trade | accounts, fills, private order state | `private_read_only` / `private_signed` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| Coinbase Advanced Trade | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Coinbase Advanced Trade | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Coinbase Advanced Trade | `amend_order` | `order_amend` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Kraken | public time, asset pairs, OHLC, depth | `public_read_only` | category classification | `implemented` | not selected for UAT1 | deferred venue |
| Kraken | balance, query orders, open orders, trades history | `private_read_only` / `private_signed` | private endpoint flag | `implemented` | no | forbidden in UAT1 |
| Kraken | `submit_order` | `order_submission` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Kraken | `cancel_order` | `order_cancel` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |
| Kraken | `amend_order` | `order_amend` | private + order flags | `implemented` | no | forbidden until later gated sandbox order phase |

## Public Read-Only Classification

Status: `implemented`.

Public read-only methods are explicitly classified as `public_read_only`. They may be considered for future UAT1 only if they are unsigned, do not require private credentials, do not create trading artifacts, and are included in the selected-venue allowlist.

Examples:

- public market metadata;
- public candles;
- public tickers;
- public order book snapshots;
- public funding metadata when unsigned and documented.

No public endpoint was called in UAT0.2.

## Selected Venue For Future UAT1

Selected future UAT1 venue: `Hyperliquid`.

Reason: the frozen evidence candidate is Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline. This is an evidence candidate for observation, not proof of profitability and not paper/live/order approval.

## Hyperliquid UAT1 Read-Only Allowlist

Status: `implemented_as_policy_artifact`.

Testable model: `services.exchange.safety.HYPERLIQUID_UAT1_READ_ONLY_ALLOWLIST`.

Allowed future UAT1 categories:

- `public_read_only`

Allowed future UAT1 examples, after a separate UAT1 phase:

- public market metadata;
- public candles;
- public tickers / mids;
- public order book snapshots;
- public funding metadata if unsigned and documented.

Forbidden Endpoint Categories:

- `private_read_only`
- `private_signed`
- `order_submission`
- `order_cancel`
- `order_amend`
- `order_retry_or_recovery`
- `unknown`

Forbidden future UAT1 examples:

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

Hyperliquid public testnet endpoint support is `needs_verification` before UAT1. UAT0.2 does not connect to Hyperliquid.

## Redaction Verification Status

Status: `implemented_baseline`.

UAT0.2 strengthens `core.security` representative redaction:

- bearer tokens;
- `Authorization: Bearer ...` values;
- `api_key=...`;
- `secret=...`;
- `password=...`;
- `token=...`;
- private-key style key/value strings;
- PostgreSQL URLs with embedded passwords.

Adapter request error logging now redacts exception text before recording `last_error`, structured error fields, or adapter-raised error messages on the shared REST helpers and Hyperliquid helpers.

Remaining status: `needs_verification`.

Structured application logging and every API exception path still need broader sandbox-like review before UAT1. UAT0.2 proves representative helper behavior and adapter-helper error redaction; it does not certify every possible application log line.

## Review Bundle / Obsidian Secret Hygiene

Status: `verified_by_existing_bundle_workflow`.

Review bundles continue to use `.archiveignore` through `scripts/create_review_bundle.py`. Excluded categories include:

- `.env`
- `.venv`
- Git metadata
- caches
- local DB/SQLite files
- nested archives
- secrets
- Obsidian app state
- generated evidence packs
- local candle files
- review bundles

## Remaining Blockers

| Blocker | Status | Severity | Notes |
| --- | --- | --- | --- |
| Adapter-level runtime-policy enforcement | `implemented` | P1 closed by UAT0.2 | Private/signed/order helpers block before transport by default. |
| Hyperliquid selected-venue read-only endpoint policy | `implemented_as_policy_artifact` | P1 partially closed | UAT1 still must verify actual endpoint URLs without private/signed calls. |
| Structured log/error redaction verification | `implemented_baseline` | P1 partially closed | Representative redaction and adapter-helper redaction are tested; full application log/error review remains. |
| Runtime drawdown monitoring | `missing` | P1 | Deferred to later UAT0.x. |
| Top-20 symbol / market identity resolution | `missing` | P1 | Deferred to later UAT0.x. |

## UAT1 Readiness Decision

UAT0.2 decision at the time: `UAT1 is blocked`.

UAT0.3 updated decision: `UAT1 read-only connectivity may proceed` under public-read-only constraints after adding the top-20 resolver policy, drawdown monitor model, and expanded Hyperliquid read-only info-type allowlist.

Closed or partially closed by UAT0.2:

- adapter-level runtime-policy enforcement baseline;
- selected-venue Hyperliquid read-only allowlist artifact;
- representative redaction helper coverage;
- adapter-helper error redaction.

Remaining blockers before UAT1:

- top-20 symbol / market identity resolution is not implemented;
- runtime drawdown monitoring is missing;
- Hyperliquid public read-only endpoint URLs and sandbox/testnet behavior still need explicit UAT1 verification;
- broader structured application log/API error redaction still needs review.

UAT1, when later allowed, is read-only only. UAT1 must not submit orders.

## Boundary Confirmation

UAT0.2 created no `MandateDesiredTrade`, `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, routing artifacts, approvals, paper trades, live trades, exchange calls, private/signed calls, public exchange calls, order endpoint calls, evidence packs, or strategy-rule changes.
