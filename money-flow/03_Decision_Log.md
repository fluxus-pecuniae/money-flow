# Decision Log

Append entries only. Do not rewrite prior decisions except to add a dated correction.

## 2026-05-10T17:50:18Z - UAT3.2 - Fixed-Key Preflight Blocked Before Order Transport

- `decision`: Execute UAT3.2 only as one separately approved Hyperliquid testnet fixed-key readiness preflight plus one possible sandbox lifecycle attempt if every gate passed.
- `why`: UAT3.1 reached the order endpoint and was safely rejected because the testnet user/API wallet did not exist. The founder/operator reported fixed credentials and supplied separate approval, so the next safe step was account/API-wallet readiness before any second order-capable transport.
- `scope`: UAT3.2 validates exact approval text, sandbox/testnet endpoint boundary, fixed-key account/API-wallet recognition/authorization, live-fed sandbox drawdown, approval scope, risk gates, submit-lease duplicate prevention, sandbox artifact labels, endpoint classification, and nonmarketable/post-only ETH order shape. It must not submit live orders, use live keys, place more than one sandbox order attempt, create production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, routing expansion, Money Flow rule changes, evidence packs, broad top-20 submission, fanout, SOR, or target reselection.
- `result`: Exact UAT3.2 approval was verified, but fixed-key account/API-wallet readiness failed before `/exchange`: the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient. Order attempt count was `0`; no order/cancel/amend/retry endpoint was called; no production execution artifacts or paper/live behavior were created.
- `follow_up_implications`: UAT3.3 remains blocked until separate founder/operator approval exists and Hyperliquid testnet user/API wallet recognition/authorization plus sufficient sandbox equity are verifiably fixed. UAT4.0 live UAT trading dashboard / chart cockpit was captured as a future roadmap request only.

## 2026-05-10T15:42:33Z - UAT3.0.6 - Sandbox Submit Path Dry-Run Wired

- `decision`: Add a non-persistent sandbox submission plan and dry-run submit-path gate service before any UAT3.1 sandbox order attempt is considered.
- `why`: UAT3.0.5 verified live-fed sandbox account drawdown, but actual submission still needs proof that approval, drawdown, risk, submit-lease, endpoint classification, and sandbox-label gates compose before any order transport can be enabled.
- `scope`: UAT3.0.6 adds `UAT3SandboxSubmissionPlan`, `UAT3SandboxSubmitDryRunService`, endpoint-classification checks for the future `sandbox_order_submission` category, live-fed drawdown freshness/label checks, docs, and tests. It does not submit orders, create real `OrderIntent` / `PreparedVenueOrder` / `SubmittedOrder` / executable approval artifacts, call order/cancel/amend/retry endpoints, use exchange API keys, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. The dry-run path now reports no order intent, prepared order, submitted order, executable approval, or exchange call creation while blocking missing founder actual-submission approval, stale/missing drawdown, approval/risk failures, submit-lease duplicate/uncertainty failures, endpoint-classification failures, and missing sandbox labels.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator actual-submission approval, explicit later-phase sandbox/testnet order transport enablement, and final operator review proving the real submit path preserves the dry-run gates.

## 2026-05-10T16:50:05Z - UAT3.1 - First Sandbox/Testnet Lifecycle Probe Attempted

- `decision`: Execute exactly one founder-approved Hyperliquid testnet ETH sandbox/testnet lifecycle probe under the UAT3.1 gate chain.
- `why`: UAT3.0.6 proved the submit path in dry-run mode, and the founder/operator supplied exact one-attempt approval for sandbox/testnet plumbing validation only. The next safe step was one tiny nonmarketable/post-only testnet attempt with no paper/live, no broad top-20 submission, no strategy-performance claim, and no repeat behavior.
- `scope`: UAT3.1 validates exact approval text, sandbox/testnet endpoint boundary, live-fed sandbox drawdown status, approval scope, risk gates, submit-lease duplicate prevention, sandbox artifact labels, endpoint classification, and nonmarketable/post-only order shape before one Hyperliquid testnet order transport call. It creates no production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, routing expansion, Money Flow rule change, evidence pack, live endpoint use, broad top-20 submission, or second order.
- `result`: One Hyperliquid testnet ETH post-only limit attempt under 10 USDC notional was made. Hyperliquid rejected it with a sanitized user/API-wallet-not-found response, no cancel was required, reconciliation found no open order, and no unexpected fill or unknown state remained.
- `follow_up_implications`: UAT3.2 additional sandbox lifecycle testing may be scoped only with separate founder/operator approval. Before another attempt, review sandbox account/API-wallet configuration so accepted/open -> cancel lifecycle coverage can be tested without repeating the UAT3.1 user/API-wallet rejection.

## 2026-05-10T15:06:29Z - UAT3.0.5 - Testnet Read-Only Drawdown Verified

- `decision`: Rerun UAT3.0.5 with local UAT-specific sandbox/testnet environment variables and record the resulting private-read-only drawdown verification.
- `why`: The first UAT3.0.5 pass had approval but no local UAT sandbox credentials. After the founder/operator added the variables to local `.env`, the safe next step was to validate the testnet boundary and call only the approved account-state read-only path.
- `scope`: One Hyperliquid testnet account-state read-only request returned HTTP 200 and produced a `sandbox_account` / `not_live_account` drawdown feed with `sandbox_drawdown_feed_live_fed_verified`. No API key/private key was sent, no order/cancel/amend/retry endpoint was called, and no real `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, routing expansion, Money Flow rule change, or evidence pack was created.
- `result`: The live-fed sandbox drawdown verification blocker is cleared for the UAT3.0.5 private read-only account-state boundary. UAT3.1 actual sandbox order submission remains blocked.
- `follow_up_implications`: UAT3.1 still requires explicit founder/operator actual-submission approval, real sandbox submit-path wiring, executable approval/risk gates wired to persistence/submit, submit-lease integration verification, and no live/paper/order ambiguity.

## 2026-05-10T14:20:21Z - UAT3.0.5 - Sandbox Private Read-Only Approval Validated, Drawdown Still Blocked

- `decision`: Validate the exact UAT3.0.5 sandbox/testnet private read-only credential-use approval boundary, add sandbox/testnet credential environment checks, block live Hyperliquid endpoints, and add Hyperliquid sandbox account-state drawdown parsing while preserving no-order boundaries.
- `why`: UAT3.0.4 left live-fed sandbox account drawdown blocked because private-read-only approval was absent. UAT3.0.5 has approval for account-state/drawdown verification only, so the next safe step is to verify the credential boundary and drawdown parser without enabling order-capable paths.
- `scope`: UAT3.0.5 adds UAT3.0.5 approval validation, sandbox/testnet env status inspection for `HYPERLIQUID_UAT_SANDBOX_*`, sandbox/testnet base URL validation, credential-boundary status mapping, Hyperliquid sandbox account-state payload parsing into `sandbox_account` / `not_live_account` drawdown feeds, docs, and tests. Local sandbox/testnet credential env vars were missing, so no credentials were loaded, no API keys were used, and no private endpoints were called. It does not submit orders, create real `OrderIntent` / `PreparedVenueOrder` / `SubmittedOrder` / executable approval artifacts, call order/cancel/amend/retry endpoints, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. Live-fed sandbox drawdown remains `sandbox_drawdown_feed_missing` until sandbox/testnet credentials and a verifiable sandbox/testnet account-state read are supplied under the private-read-only boundary. Order-capable categories remain blocked.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator actual-submission approval, live-fed sandbox account drawdown from sandbox/testnet account truth, real sandbox submit-path wiring, executable approval/risk gates wired to persistence/submit, submit-lease integration verification, and no live/paper/order ambiguity.

## 2026-05-10T13:58:00Z - UAT3.0.4 - Sandbox Private Read-Only Drawdown Readiness Complete

- `decision`: Add fail-closed sandbox/testnet private read-only account-state policy, credential approval/boundary validation, endpoint category separation, redaction helpers, and sandbox account drawdown feed modeling before any UAT3.1 sandbox submit path is considered.
- `why`: UAT3.0.3 left live-fed sandbox account drawdown as a blocker. Future sandbox/testnet order testing needs account drawdown visibility, but private read-only credential use must be explicitly approved and separated from all order-capable endpoints before any private endpoint is reachable.
- `scope`: UAT3.0.4 adds private read-only sandbox account policy helpers, exact approval-text validation, credential-boundary/redaction checks, private read-only versus order endpoint categories, sandbox account drawdown feed modeling, dry-run preflight drawdown-status support, docs, and tests. Because the exact founder/operator approval text was not present, it does not use API keys or call private endpoints. It does not submit orders, create real `OrderIntent` / `PreparedVenueOrder` / `SubmittedOrder` / executable approval artifacts, call order/cancel/amend/retry endpoints, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. Private read-only drawdown remains blocked until explicit credential approval and real sandbox/testnet account wiring exist; order-capable categories remain blocked even when private read-only sandbox account policy is enabled.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator actual-submission approval, live-fed sandbox account drawdown from sandbox/testnet account truth, real sandbox submit-path wiring, executable approval/risk gates wired to persistence/submit, submit-lease integration verification, and no live/paper/order ambiguity.

## 2026-05-10T12:57:00Z - UAT3.0.3 - Sandbox Gate Wiring And Label Enforcement Complete

- `decision`: Add dry-run sandbox artifact boundary enforcement helpers and a dry-run executable gate service before any UAT3.1 sandbox submit path is considered.
- `why`: UAT3.0.2 made missing artifact-label persistence enforcement explicit and combined fixture gates into one dry-run preflight. Future sandbox/testnet submission needs a clearer boundary model covering persistence, API serialization, dashboard display, and report generation, plus one composed dry-run path that calls approval scope, risk, drawdown, runtime, and submit-lease checks together.
- `scope`: UAT3.0.3 adds sandbox artifact boundary validators, testable runtime policy semantics, `UAT3SandboxDryRunGateService`, `evaluate_uat3_sandbox_executable_gate_dry_run`, dashboard readiness text, docs, and tests. It does not submit orders, create real `OrderIntent` / `PreparedVenueOrder` / `SubmittedOrder` / executable approval artifacts, call private/signed/order endpoints, use exchange API keys, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. Dry-run gate output now reports no order intent, prepared order, submitted order, executable approval, or exchange call creation while blocking missing founder actual-submission approval, fixture-only drawdown, missing real sandbox submit path, approval/risk failures, and submit-lease duplicate/uncertainty failures.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator approval for actual sandbox submission, real sandbox/testnet submit-path wiring, sandbox-only private endpoint separation, live-fed sandbox account drawdown, executable approval/risk gate wiring to persistence/submit, and submit-lease integration verification.

## 2026-05-10T12:10:00Z - UAT3.0.2 - Sandbox Gate Dry-Run Preflight Complete

- `decision`: Add a unified fixture-only sandbox gate dry-run preflight and harden UAT3.0.1 sandbox runtime/risk numeric policy before any UAT3.1 submit path is considered.
- `why`: Review found that sandbox risk evaluation only surfaced a subset of runtime-policy blockers. Future sandbox/testnet submission must fail closed on every runtime blocker, invalid sandbox numeric inputs, missing actual-submission approval, fixture-only drawdown, and missing persistence-level sandbox artifact labeling.
- `scope`: UAT3.0.2 propagates all `SandboxRuntimePolicy` blockers into risk/preflight reason codes, rejects non-positive approval quantities, risk limits, risk request notionals, and invalid drawdown values, adds `evaluate_uat3_sandbox_submission_preflight`, updates dashboard readiness text, and adds docs/tests. It does not submit orders, create real `OrderIntent` / `SubmittedOrder` / executable approval artifacts, call private/signed/order endpoints, use exchange API keys, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. The dry-run result now combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status while reporting no order intent, submitted order, executable approval, or exchange call creation.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator approval for actual sandbox submission, real sandbox/testnet submit-path wiring, sandbox-only private endpoint separation, live-fed sandbox account drawdown, executable approval/risk gate wiring, submit-lease integration verification, and persistence-level sandbox artifact-label enforcement.

## 2026-05-10T10:55:00Z - UAT3.0.1 - Sandbox Runtime / Approval / Risk Readiness Fixtures Complete

- `decision`: Add fixture-only readiness primitives for the future UAT3.1 sandbox order path while keeping actual sandbox submission blocked.
- `why`: UAT3.0 documented the required runtime, approval, drawdown, artifact-label, submit-lease, and risk gates. Before any real sandbox/testnet order attempt can be considered, those requirements need concrete testable primitives that fail closed without creating execution artifacts.
- `scope`: UAT3.0.1 adds `SandboxRuntimePolicy`, sandbox artifact-label validation, actual-submission approval-scope validation, sandbox risk-gate fixture evaluation, sandbox drawdown feed fixture support, submit-lease duplicate-prevention fixture checks, sharper UAT3.1 approval wording, dashboard readiness status, and docs/tests. It does not submit orders, create real `OrderIntent` / `SubmittedOrder` / executable approval artifacts, call private/signed/order endpoints, use exchange API keys, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked. Fixture checks now cover fail-closed runtime defaults, sandbox labels, approval scope mismatches/expiry/live/broad-top20 cases, risk-gate blocks, not-live-account sandbox drawdown fixtures, duplicate/uncertain submit blocking, cross-venue retry blocking, no top-20 fanout, and no route executor behavior.
- `follow_up_implications`: UAT3.1 may proceed only after explicit founder/operator approval for actual sandbox submission, real sandbox/testnet submit-path wiring, sandbox-only private endpoint separation, live-fed sandbox account drawdown, executable approval/risk gate wiring, submit-lease integration verification, and persistence-level sandbox artifact-label enforcement.

## 2026-05-10T09:22:47Z - UAT2.1 - UAT2 Dashboard Review Surface Complete, UAT3 Still Blocked

- `decision`: Add a review-only UAT2 Shadow Run dashboard view and founder approval readiness pack for the completed UAT2 no-order shadow run.
- `why`: Founder/operator review needs to inspect the 45 UAT2 shadow audit records, would-open versus no-trade outcomes, ETH `sleeve_1h` candidate truth, timing assumptions, shadow drawdown labels, forbidden-artifact boundary flags, and UAT3 blockers without reading only Markdown/JSON.
- `scope`: UAT2.1 visualizes `docs/uat2_shadow_strategy_top20_observation_summary.json` in the existing static dashboard and adds docs/tests. It does not implement UAT3, submit sandbox orders, create executable approvals, create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, or routing artifacts, call private/signed endpoints, use API keys, approve paper/live trading, change Money Flow rules, or generate evidence packs.
- `result`: The dashboard shows summary cards, a filterable signal matrix, would-open review, no-trade reason breakdowns, the ETH evidence-candidate card, `next_candle_open` / `next_candle_close` timing status, `same_candle_close_research_only` research-only truth, not-live-account shadow drawdown, UAT3 blockers, and no-forbidden-artifact boundary flags.
- `follow_up_implications`: UAT3.0 later accepted sandbox-order design scope; UAT3.1 actual sandbox order submission remains blocked until explicit founder/operator approval, sandbox account drawdown feed wiring, and approval/submit-lease lifecycle verification are addressed.

## 2026-05-10T10:10:00Z - UAT3.0 - Sandbox Order Design Complete, UAT3.1 Submission Blocked

- `decision`: Define UAT3.0 as sandbox-order design/readiness only, with no actual sandbox order submission and no executable approval/action path.
- `why`: After UAT2 shadow observation and UAT2.1 dashboard review, the next safe step is to specify exactly what a future sandbox test would be allowed to do, which gates must be present, and why actual sandbox submission remains blocked.
- `scope`: UAT3.0 narrows the future initial sandbox subset to Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules, defines the founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, risk gate design, and dashboard readiness. It does not submit orders, create real `OrderIntent` / `SubmittedOrder` / executable approval artifacts, call private/signed endpoints, use exchange API keys, approve paper/live trading, change Money Flow rules, add routing expansion, or generate evidence packs.
- `result`: UAT3.1 actual sandbox order submission remains blocked by explicit approval, sandbox runtime submission enablement, sandbox account drawdown feed wiring, approval-scope verification, submit-lease lifecycle verification, risk-gate implementation, and sandbox artifact labeling.
- `follow_up_implications`: UAT3.1 may be scoped only after the founder/operator explicitly approves actual sandbox submission and the remaining sandbox lifecycle prerequisites are implemented and test-covered. It must remain sandbox/testnet only and must not become automatic top-20 order submission.

## 2026-05-10T08:38:49Z - UAT2 - No-Order Shadow Observation Complete, UAT3 Blocked

- `decision`: Complete UAT2 as a bounded no-order Money Flow shadow observation across the UAT1 Hyperliquid top-20-supported universe using public read-only candles and shadow audit records only.
- `why`: UAT2 needed to prove that the platform can evaluate current baseline Money Flow behavior across the observation universe, expose would-trade/no-trade reasons, represent `next_candle_open` / `next_candle_close` assumptions, and show not-live-account shadow drawdown without creating execution artifacts.
- `scope`: UAT2 used explicit public-read-only shadow mode, evaluated `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`, and produced 45 shadow audit records. It did not submit orders, use API keys, call private/signed/order endpoints, create `StrategyDecision`, `SignalEvent`, `OrderIntent`, `PreparedVenueOrder`, `ExecutionReadinessAssessment`, `SubmittedOrder`, approvals, routing artifacts, paper/live trades, evidence packs, or Money Flow rule changes.
- `result`: UAT2 created 11 `would_open` and 34 `no_trade` records; ETH `sleeve_1h` was `no_trade` with `macd_not_constructive`. Shadow drawdown remained `shadow_simulated_drawdown` / `not_live_account_drawdown`.
- `follow_up_implications`: UAT3.0 later accepted sandbox-order design scope; UAT3.1 actual sandbox order submission remains blocked until the founder/operator explicitly approves actual sandbox submission and sandbox account drawdown, risk, approval, submit-lease, and lifecycle verification are addressed.

## 2026-05-10T08:00:33Z - UAT1.1 - Shadow Readiness Clears UAT2 Start Blockers

- `decision`: Add model/report-only shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification so UAT2 shadow strategy run may proceed as a future no-order phase.
- `why`: UAT2 should not begin until operators can inspect would-trade/no-trade/risk-block reasons, shadow drawdown state, and timing assumptions without creating live trading artifacts or exposing obvious secrets in representative error/log payloads.
- `scope`: UAT1.1 does not run the UAT2 shadow strategy loop, does not run Money Flow over live data, calls no private/signed/order endpoints, uses no exchange API keys, submits no orders, creates no `StrategyDecision`, `OrderIntent`, or `SubmittedOrder`, approves no paper/live trading, changes no Money Flow rules, adds no routing behavior, and generates no evidence packs.
- `follow_up_implications`: UAT2 must remain shadow-only, use the UAT1 top-20 Hyperliquid observation universe, compare `next_candle_open` and `next_candle_close`, keep `same_candle_close_research_only` research-only, and write/inspect shadow audit and drawdown state without order submission.

## 2026-05-10T07:18:43Z - UAT1 - Public Read-Only Connectivity Complete, UAT2 Blocked

- `decision`: Complete UAT1 public-read-only connectivity and top-20 universe resolution under explicit public-read-only network gating, while keeping UAT2 blocked.
- `why`: The platform needed one controlled public-read-only verification pass before shadow strategy work. UAT1 verified Hyperliquid allowed public info types, fetched a no-key public top-volume source, intersected supported Hyperliquid USDC perpetual markets, and preserved observation-only labels without implying strategy approval.
- `scope`: UAT1 uses no API keys, calls no private/signed/order endpoints, submits no orders, runs no Money Flow live strategy evaluation, creates no strategy decisions/order intents/submitted orders, approves no paper/live trading, changes no Money Flow rules, adds no routing behavior, and generates no evidence packs.
- `follow_up_implications`: UAT2 remains blocked until operator-visible shadow drawdown state, shadow signal audit surfaces, and broader structured log/API error redaction verification are complete. Future UAT2 must remain shadow-only and compare `next_candle_open` and `next_candle_close`.

## 2026-05-09T14:17:37Z - UAT0 - Block UAT1 Until Safety Gates Are Explicit

- `decision`: Complete UAT0 as a safety/security/runtime audit and block UAT1 read-only connectivity until API auth/authz, fail-safe UAT mode gating, live endpoint lockout, secret/log/error redaction verification, and top-20 market identity prerequisites are closed.
- `why`: Existing execution defaults, venue submission flags, approval gates, and submit-lease uncertainty protections are useful but do not compensate for unauthenticated sensitive API routes or missing one-piece UAT/live lockout. UAT should validate plumbing and behavior, not sneak into connectivity or trading.
- `scope`: UAT0 adds docs/tests and audit truth only. It makes no exchange calls, uses no API keys, submits no orders, creates no paper/live artifacts, changes no Money Flow rules, adds no routing behavior, implements no UAT1/UAT2/UAT3 runtime, and generates no evidence packs.
- `follow_up_implications`: Future UAT observation should cover top 20 high-volume crypto assets supported by the selected UAT venue/environment, but top-20 inclusion is not strategy approval. Future UAT2 shadow timing should compare `next_candle_open` and `next_candle_close`; `same_candle_close_research_only` remains research-only.

## 2026-05-10T06:24:03Z - UAT0.3 - Public Read-Only UAT1 May Proceed Under Constraints

- `decision`: Add fixture-tested top-20 UAT observation-universe resolver policy, Hyperliquid public read-only info-type allowlisting, and a fixture-tested runtime drawdown monitor model, then allow UAT1 public read-only connectivity to proceed under strict no-private/no-signed/no-order/no-API-key constraints.
- `why`: UAT1 needs enough policy truth to fetch public top-volume source data and public selected-venue market metadata without implying strategy approval or trading authorization. Runtime drawdown does not need live account feed for UAT1 metadata, but UAT2/UAT3 need visible shadow/sandbox drawdown state before signal observation or sandbox orders.
- `scope`: UAT0.3 adds policy/model code, tests, and docs only. It does not implement UAT1, connect to exchanges, call public/private/signed/order endpoints, use exchange API keys, submit orders, approve paper/live trading, change Money Flow rules, add routing behavior, or generate evidence packs.
- `follow_up_implications`: UAT1 remains public read-only only and must verify actual Hyperliquid endpoint URLs/sandbox behavior plus public top-20 source ingestion. Broader structured log/API error redaction, UAT2 operator-visible drawdown state, UAT3 sandbox account drawdown feed, and UAT-specific risk/kill-switch/audit visibility remain later blockers.

## 2026-05-10T05:38:05Z - UAT0.2 - Adapter Runtime Policy Must Block Before Transport

- `decision`: Add adapter-helper endpoint classification and enforce `RuntimeSafetyPolicy` before private, signed, unknown, or order-like adapter transport can run. Define Hyperliquid as the selected future UAT1 venue with a public-read-only allowlist artifact and keep UAT1 blocked until the remaining prerequisites are closed.
- `why`: API auth is not enough for exchange-facing safety. Future UAT work must prove that private/signed/order calls cannot bypass route protection or central runtime lockouts, and founder/operator review needs an explicit read-only allowlist before any connectivity phase.
- `scope`: UAT0.2 adds adapter guards, a testable read-only allowlist artifact, representative redaction hardening, tests, and docs only. It does not implement UAT1, connect to exchanges, call public/private/signed/order endpoints, use exchange API keys, submit orders, approve paper/live trading, change Money Flow rules, add routing behavior, or generate evidence packs.
- `follow_up_implications`: UAT1 remains blocked by top-20 symbol/market identity resolution, runtime drawdown monitoring, explicit Hyperliquid public read-only endpoint URL/sandbox verification, and broader structured application log/API error redaction review. UAT1 remains read-only only when later allowed.

## 2026-05-09T13:21:46Z - OB1.0 - Obsidian Brain Separates SV Closeout From UAT0

- `decision`: Make `money-flow/00_Money_Flow_Command_Center.md` the single canonical command center, add dedicated Strategy Validation and UAT roadmap maps, and treat SV1.18.1 as the completed milestone with UAT0 as the next proposed track.
- `why`: The vault had grown through Phase 8 and SV1.x and could make Strategy Validation look like an active Phase 8 sub-phase. Future agents need a clean current-state map before UAT work so they do not confuse research evidence, UAT observation, paper trading, live trading, or routing expansion.
- `scope`: OB1.0 is documentation and governance only. It does not implement UAT0, change Money Flow rules, approve paper/live trading, add exchange calls, create live artifacts, generate evidence packs, or add routing/execution behavior.
- `follow_up_implications`: UAT0 work should start from the UAT roadmap and UAT0 safety/runtime note, keep the frozen ETH `sleeve_1h` candidate narrow, and preserve paper/live/order-submission deferral until later explicit UAT gates.

## 2026-05-08T07:57:25Z - SV1.17 - Replay Results Must Cover The Full Public Suite

- `decision`: Expand SV1.17 true replay reporting from the initial ETH `sleeve_1h` slice to the full Hyperliquid public BTC/ETH/SOL x 15m/1h/4h suite.
- `why`: Founder review needs to see whether lower-RSI plus market-structure replay behavior is isolated to the strongest ETH 1h pocket or applies across the whole imported public campaign.
- `scope`: The full-suite run keeps each symbol/component as an independent dynamic-equity replay scenario and compares every variant only against its matching same-symbol/same-component baseline. Some variants improve losing baselines, ETH 1h baseline remains the strongest above-starting-equity pocket, and no variant is authorized.
- `follow_up_implications`: Future review should treat full-suite replay as scenario evidence, not a combined portfolio account. Fill/cost sensitivity, out-of-sample windows, exact stop/invalidation replay, and portfolio simulation remain separate future work.

## 2026-05-09T12:32:14Z - SV1.18 - Freeze One UAT Observation Candidate Only

- `decision`: Close the current Strategy Validation evidence cycle and freeze exactly one UAT observation candidate: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`, scoped to Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline Money Flow rules.
- `why`: Founder skepticism about backtest realism is valid. Current replay/backtest evidence does not model funding, liquidation, margin, order-book fills, partial fills, latency, outages, real rejects, or production exchange lifecycle behavior, so it can justify only a tightly scoped UAT plumbing/behavior phase, not paper/live trading.
- `scope`: 15m, 4h, BTC/SOL 1h, lower-RSI variants, market-structure variants, and non-Hyperliquid venues are excluded from current UAT scope. UAT0 is safety/security/runtime hardening only; no production Money Flow rules, routing, execution automation, exchange calls, API keys, paper trading, live trading, or live artifacts are added.
- `follow_up_implications`: UAT0 must verify auth/authz, secret hygiene, fail-safe sandbox/live separation, risk limits, drawdown monitoring, kill switch, audit logging, confirmation gates, duplicate-order prevention, submit-lease uncertainty handling, no private endpoint calls before explicit UAT authorization, and no accidental live endpoint reachability before any later sandbox order phase.

## 2026-05-08T06:52:35Z - SV1.17 - Lower-RSI Replay Round Needs Baseline Preservation

- `decision`: Run a small ETH `sleeve_1h` true replay experiment round before broadening lower-RSI or market-structure work.
- `why`: SV1.16.1 made replay counters trustworthy enough to test a few real candidate admissions. The first round needed to answer whether narrower below-floor RSI plus support/EMA10/resistance context could improve baseline without adding falling-knife/chop entries.
- `scope`: SV1.17 tests lower-RSI trend-intact v1, a narrower v2, support-confirmed, and EMA10-hold/no-resistance variants against the current ETH `sleeve_1h` baseline. No variant beat baseline; support-confirmed admitted no trades, and EMA10-hold/no-resistance reduced drawdown but still ended below baseline.
- `follow_up_implications`: Broader replay should not assume lower RSI is beneficial. Any further testing needs wider symbols/components, fill/cost sensitivity, out-of-sample windows, and exact stop/invalidation replay before paper-design discussion.

## 2026-05-08T05:55:00Z - SV1.16.1 - Replay Variant Metrics Need State Semantics

- `decision`: Add explicit replay context fields for production Money Flow rule evaluation under the active replay state, keep legacy `baseline_*` fields as compatibility aliases, and separate production-rule rejection counts from variant admission and variant no-trade counts.
- `why`: Once a variant admits a candle that production rules rejected, the replay path can diverge from the independent baseline path. Reporting later production-rule evaluations as plain baseline truth, or counting an admitted candle as variant no-trade, would mislead founder review before broader true replay experiments.
- `scope`: SV1.16.1 adds `production_rule_*_in_replay_state` fields, `variant_state_has_diverged_from_baseline`, `replay_state_source`, `variant_admitted_from_production_rule_rejection`, and separate variant summary counters. The lower-RSI replay result and baseline parity remain research-only and no production Money Flow rules changed.
- `follow_up_implications`: Broader true replay experiments should consume the clearer fields/counters and should not claim independent baseline context after divergence unless a separate baseline-reference path is explicitly computed.

## 2026-05-08T04:45:00Z - SV1.16 - True Replay Requires Per-Candle Rejected-Signal Context

- `decision`: Add a Strategy Validation-only replay substrate that captures every evaluated candle's baseline action/rejection context and supports chronological research variant replay without changing production Money Flow rules.
- `why`: SV1.15/SV1.15.1 completed-trade overlays can rank hypotheses, but they cannot answer what would have happened when baseline rejected a lower-RSI candle or when a filter changes position occupancy and dynamic-equity path. True lower-RSI and market-structure variant testing needs accepted and rejected candle context plus a replay runner.
- `scope`: SV1.16 records per-candle RSI zone, EMA/MACD/extension state, regime, recent swing high/low context, and baseline reason codes; the first `lower_rsi_floor_trend_intact_v1` ETH `sleeve_1h` replay is research-only and underperformed the sampled baseline.
- `follow_up_implications`: Broader true replay experiments, exact recent-low/ATR stop replay, out-of-sample checks, and dashboard/UI wiring can be scoped later. No production rule, paper/live trading, routing, execution behavior, or strategy authorization follows from SV1.16.

## 2026-05-08T00:00:00Z - SV1.15.1 - Hypothesis Experiments Need Methodology Labels

- `decision`: Classify every SV1.15 hypothesis by methodology and treat completed-trade overlays as diagnostic estimates, not true forward strategy replays.
- `why`: SV1.15 mostly evaluates completed baseline trades. Skipping completed trades, proxying earlier exits, or attributing RSI/entry style can rank hypotheses, but it does not model alternative candle-by-candle entries, position occupancy, future capital path, or exact exit fill timing. Founder review would be misleading if these diagnostics looked like fully replayed strategy variants.
- `rejected_alternatives`: Treating recent-low invalidation as a normal improvement candidate; treating completed-trade overlays as production-ready or paper-ready rule changes; testing lower-RSI admission without rejected-signal replay instrumentation; changing production Money Flow rules in the methodology hotfix.
- `follow_up_implications`: True rule testing needs a forward replay runner that can evaluate rejected candles, model skipped entries and changed position availability, update dynamic equity along the altered path, and simulate exact earlier exit timing/fills. Paper/live design remains deferred.

## 2026-05-07T19:38:54Z - SV1.15 - Hypothesis Experiments Are Research Overlays Only

- `decision`: Add controlled Strategy Validation-only hypothesis experiments as overlays/attribution against the Hyperliquid public `dynamic_equity_pct` baseline, while keeping production Money Flow rules unchanged.
- `why`: SV1.14 produced plausible rule-change hypotheses, but applying them directly to production rules would mix diagnostics, parameter changes, and authorization. SV1.15 keeps one-change-at-a-time comparisons founder-readable and clearly separates observed research deltas from production behavior.
- `rejected_alternatives`: Modifying production RSI floors, market-structure filters, 15m regime filters, or 4h extension rules in place; stacking multiple filters and calling them one factor; treating ETH 1h preservation as paper-trading authorization; using lower-RSI admission without per-candle rejected-signal replay data.
- `follow_up_implications`: Founder review can use SV1.15 to triage hypotheses, but true lower-RSI entry admission needs a later replay runner that persists rejected-candle indicator/market-structure features. No hypothesis is production-authorized, and paper/live design remains deferred.

## 2026-05-07T10:19:14Z - SV1.13.2 - Dynamic Equity Is Separate From Constant-Notional Replay

- `decision`: Add `dynamic_equity_pct` as a first-class Strategy Validation capital sizing mode while preserving `constant_initial_capital_notional_per_trade` as the default and as the correct label for SV1.13/SV1.13.1 evidence.
- `why`: Founder review needs to answer whether a simulated account starting at `$10000` ended above or below starting equity. Constant-notional replay intentionally reuses initial-capital notional on every trade and is useful for research comparability, but it does not answer account-style sequential equity sizing.
- `rejected_alternatives`: Silently replacing constant-notional evidence; treating dynamic equity as full exchange margin/funding/liquidation simulation; combining BTC/ETH/SOL or fill/cost scenarios into one shared portfolio account; changing Money Flow rules; optimizing parameters; approving paper trading; adding routing/execution behavior.
- `follow_up_implications`: Founder review can compare constant-notional replay and per-scenario dynamic-equity results. Paper-trading design remains deferred and would still need explicit manual acceptance plus separate margin/funding/liquidation/portfolio constraints if scoped later.

## 2026-05-07T12:18:47Z - SV1.14 - Market Structure Is Diagnostic Only

- `decision`: Add trade-anatomy and market-structure diagnostics as a read-only Strategy Validation layer rather than changing Money Flow entries/exits.
- `why`: Founder review needs to understand why ETH `sleeve_1h` is strongest and why 15m/4h are weak before testing any rule changes. Recent swing high/low proximity, resistance/support context, and regime observations can explain behavior, but using them as filters would be a strategy change requiring a separately scoped controlled test.
- `rejected_alternatives`: Adding market-structure filters in the same phase; optimizing parameters; treating ETH 1h as a recommended variant; approving paper trading; adding routing/execution behavior; importing other venues; calling exchange/private/signed/order endpoints.
- `follow_up_implications`: Later SV work may test hypotheses one at a time, such as resistance proximity, higher-low confirmation, ATR/recent-low invalidation, 15m regime avoidance, or 4h extension limits. Until then, Money Flow rules remain unchanged and paper/live design remains deferred.

## 2026-05-07T08:03:28Z - SV1.13.1 - Grouped Evidence Aggregates Need Scenario Interpretation

- `decision`: Keep grouped comparison sums available as descriptive research aggregates, but label them as sums across completed research runs and add founder-readable scenario-level interpretation before any paper-trading design discussion.
- `why`: SV1.13 grouped metrics can sum across symbols, fill timings, fees, and slippage assumptions. Those sums are useful for research triage, but they are not one account/scenario PnL and could mislead founder review if interpreted as a tradable strategy result.
- `rejected_alternatives`: Treating grouped totals as one strategy result; selecting or recommending a strategy variant from aggregate sums; changing Money Flow rules; optimizing parameters; approving paper trading; adding routing/execution behavior; combining non-Hyperliquid venues into the Hyperliquid evidence result.
- `follow_up_implications`: Founder review should use scenario-level fill/cost/drawdown/regime evidence, with ETH `sleeve_1h` concentration explicitly reviewed, before any later paper-trading design phase is scoped.

## 2026-05-07T09:08:46Z - SV1.13.1 - Capital Sizing Must Be Labeled Constant Notional

- `decision`: Label current Strategy Validation sizing as `constant_initial_capital_notional_per_trade` and keep dynamic account-equity sizing deferred to a separately scoped evidence phase.
- `why`: SV1.13 uses `entry_notional = initial_capital * position_notional_pct` on every opened trade. Realized equity is used for PnL and drawdown metrics, but it does not shrink, compound, or stop subsequent trade sizing. Founder review would be misleading if this were read as account-equity portfolio simulation.
- `rejected_alternatives`: Silently treating SV1.13 results as dynamic account-equity evidence; changing Money Flow rules; implementing dynamic sizing in this interpretation hotfix; regenerating evidence packs; approving paper trading.
- `follow_up_implications`: Any paper-trading design discussion should either accept the constant-notional limitation explicitly or wait for a later `dynamic_equity_pct` evidence phase.

## 2026-05-01T05:39:34Z - Phase 7.3 - Obsidian Becomes Strategic Brain

- `decision`: Move full strategic project memory into the Obsidian vault and keep the repo-root `money_flow_project_memory.md` only as a compatibility pointer.
- `why`: Repo operational docs should stay concise and code-state focused, while founder intent, long-horizon memory, phase context, and cross-agent coordination need a richer project brain.
- `rejected_alternatives`: Keeping full strategic memory at repo root; treating Obsidian as a replacement for `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, or `TODO.md`.
- `follow_up_implications`: Future agents must read the Obsidian command center, current phase note, project memory, and coordination note before substantial work, then update relevant Obsidian notes after substantial work.

## 2026-05-01T05:58:03Z - Phase 7.3 - Approval-Gated Target-Choice Conversion Only

- `decision`: Add only the `target_choice_conversion` approval-consuming action hook for Phase 7.3.
- `why`: Phase 7.2/7.2.1 already proved approval-gated recommendation acceptance. The next safe automation step is converting the exact approved target choice into one child intent while keeping preview/readiness and submission explicit and separate.
- `rejected_alternatives`: Automating preview/readiness in the same phase; automating submitted-order handoff; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future action hooks must continue to consume one current-lineage approval for one same-target stage and must preserve dry-run/manual policy truth plus no-downstream-artifact boundaries.

## 2026-05-01T07:28:41Z - Phase 7.4 - Approval-Gated Preview/Readiness Only

- `decision`: Add only the `prepared_order_preview_and_readiness` approval-consuming action hook for Phase 7.4.
- `why`: Phase 7.3 already proved approval-gated target-choice conversion. The next safe automation step is running existing preview/readiness inspection for the exact approved child intent while keeping submitted-order handoff explicit and separate.
- `rejected_alternatives`: Treating approval as readiness eligibility; automating submitted-order handoff; calling adapter submit; introducing route-executor orchestration; adding ranking/scoring/fanout/target reselection.
- `follow_up_implications`: Future submitted-order automation must remain a separate phase and must consume its own current-lineage approval plus existing readiness, live/routed gates, and submit-lease uncertainty guards.

## 2026-05-01T08:41:37Z - Phase 7.5 - Approval-Gated Submitted-Order Handoff Only

- `decision`: Add only the `submitted_order_handoff` approval-consuming action hook for Phase 7.5.
- `why`: Phase 7.4 already proved approval-gated preview/readiness inspection. The next bounded step is submitting the exact already-ready child intent through the existing explicit submit path while keeping readiness, live/routed gates, adapter/account authorization, and submit-lease uncertainty protections authoritative.
- `rejected_alternatives`: Treating approval as a readiness override; adding a route executor; adding broad auto-submit; retrying or failing over to another target; adding ranking/scoring/fanout/CBBO/target reselection.
- `follow_up_implications`: Future phases should harden/close out operator inspection, regression, and concurrency/uncertainty observability before considering any broader automation.

## 2026-05-01T09:40:47Z - Phase 7.5.1 - Post-Submit Approval Consumption Truth

- `decision`: Represent submitted-order-created / approval-consumption-failed truth as `consumption_pending` on the approval record.
- `why`: A persisted `SubmittedOrder` is real exchange/account truth. If approval consumption fails after that point, leaving the approval clean-active would be misleading and could obscure which approval authorized the handoff.
- `rejected_alternatives`: Rolling back `SubmittedOrder` truth after submit persistence; treating the approval as clean active; adding a retry executor; submitting again to repair approval state.
- `follow_up_implications`: Future operator tooling can inspect `consumption_pending` approvals and complete or manually reconcile approval state without creating another submitted order.

## 2026-05-01T12:02:56Z - Phase 7.6 - Close Controlled Automation With Safety Proof

- `decision`: Close Phase 7 with end-to-end safety regression and docs alignment rather than adding another automation action hook.
- `why`: The full controlled chain now exists. Before broader automation, the project needs proof that the chain remains exact-lineage-bound, same-target, no-SOR, no-fanout, no-reselection, and distinct across dry-run, approval, administrative consumption, action execution, readiness, and submitted-order handoff.
- `rejected_alternatives`: Adding a route executor; adding smart routing or best-binding selection; adding fanout; adding target reselection; expanding broad auto-submit; treating generic administrative approval consumption as action execution.
- `follow_up_implications`: The next major phase should be architecture-reviewed and should prioritize operator-grade observability, reconciliation/manual-resolution, concurrency/serialization hardening, and dashboard/read-only inspection depth before any broader automation scope.

## 2026-05-01T12:59:46Z - Phase 8.0 Direction - Operator Observability Before SOR

- `decision`: Shape Phase 8.0 as operator-grade observability and manual-resolution inspection for the accepted Phase 7 controlled automation chain.
- `why`: The platform now has enough approval-gated workflow depth that operators need a structured way to inspect desired-trade state, approvals, readiness, submitted-order handoff, uncertainty, submit leases, and next safe manual action before any future smart-routing work.
- `rejected_alternatives`: Jumping directly into smart routing; adding best-binding selection, CBBO, ranking/scoring, fanout, target reselection, or route-executor behavior; auto-resolving uncertainty; treating operator acknowledgement as exchange/account truth.
- `follow_up_implications`: Phase 8.0 should default to read-only inspection. Manual-resolution marker mutation should be deferred or kept strictly append-only, actor-stamped, reason-coded, audited, and non-executing.

## 2026-05-01T13:20:57Z - Phase 8.0 - Read-Only Operator Summary

- `decision`: Add a read-only operator routed workflow summary by desired trade and defer manual-resolution marker mutation to a later phase.
- `why`: Operators need one structured view of workflow artifacts, approval/gate state, manual-resolution requirements, submitted-order safety, submit lease uncertainty, and next safe action before any broader routing or automation work.
- `rejected_alternatives`: Adding marker mutation in the first observability phase; auto-resolving `consumption_pending` or submit-lease uncertainty; attaching submit/cancel/amend/retry to inspection; introducing smart routing, ranking/scoring, CBBO, fanout, target reselection, or route executor behavior.
- `follow_up_implications`: Phase 8.1 can design explicit actor-stamped manual-resolution markers or administrative reconciliation flows, but those must remain separate from exchange/account truth and trading actions.

## 2026-05-01T14:19:39Z - Phase 8.0.1 - Accept Obsidian Memory Refresh As Baseline

- `decision`: Accept the dirty Obsidian full-project-memory refresh as intentional strategic-memory baseline, update stale "Phase 8.0 proposed" wording to implemented Phase 8.0 / cleanup Phase 8.0.1 truth, and keep the repo-root `money_flow_project_memory.md` as a pointer only.
- `why`: Phase 8.0 code was accepted, but the working tree remained dirty because the earlier Obsidian refresh had not been committed. Future agents need a clean baseline and current Obsidian context before Phase 8.1.
- `rejected_alternatives`: Reverting the full project-memory refresh; moving accepted strategic notes into drafts; leaving the working tree dirty; treating the root pointer as canonical full memory again.
- `follow_up_implications`: Phase 8.1 can start from a clean repo/Obsidian baseline. Repo operational docs remain code-state truth, and Obsidian remains strategic memory and coordination.

## 2026-05-01T15:04:52Z - Phase 8.0.2 - Active Submit Lease Blocks Operator Summary

- `decision`: Treat unexpired `active` child-intent submit leases as `submission_in_progress` blockers in the read-only operator summary's submission-safety and next-safe-action truth.
- `why`: The summary already surfaced active leases but could still report approval-gated submit as safe while a submit lease was in progress, which is unsafe operator guidance even though no trading behavior changed.
- `rejected_alternatives`: Converting expired pre-adapter active leases into terminal uncertainty; adding manual-resolution mutation; changing submit behavior; adding a new action stage.
- `follow_up_implications`: Strategy Validation can begin after this hotfix is accepted. Phase 8.1 remains deferred until manual-resolution marker semantics are explicitly scoped.

## 2026-05-01T17:40:40Z - SV1.0 - Validate Strategy Before More Routing Scope

- `decision`: Add Money Flow strategy validation as a separate research/backtest boundary instead of expanding routing or execution automation.
- `why`: Phase 7 and Phase 8.0 made the controlled execution chain inspectable and safe enough to pause routing expansion. The highest business uncertainty is whether Money Flow produces measurable edge after fees and slippage.
- `rejected_alternatives`: Adding smart routing, best-binding selection, new automation action hooks, strategy-rule optimization, paper trading, or live execution changes in SV1.0.
- `follow_up_implications`: SV1.x should review deterministic reports and deepen validation before strategy optimization or paper trading. Validation artifacts must remain separate from live `SubmittedOrder` and routing/execution truth.

## 2026-05-01T18:12:47Z - SV1.0.1 - Make Backtest Assumptions Review-Safe

- `decision`: Harden the SV1.0 report truth by making fill timing explicit, separating closed-trade drawdown from mark-to-market drawdown, and expanding Markdown/JSON report detail.
- `why`: Founder/operator review can be misled if same-candle close fills or closed-trade-only drawdown are presented as neutral performance truth. Research reports need to show timing bias, drawdown methodology, assumptions, limitations, component metrics, and trade details before any paper/live decision.
- `rejected_alternatives`: Changing Money Flow strategy rules, optimizing parameters, adding paper trading, connecting validation to routing/execution, or treating backtest output as proof of profitability.
- `follow_up_implications`: SV1.1 can deepen data/regime coverage and review workflows, but strategy changes should wait for evidence and architecture review.

## 2026-05-01T18:41:11Z - SV1.1 - Comparative Validation Before Paper Trading

- `decision`: Add comparative Money Flow batch validation reports as descriptive research, not optimization or recommendation.
- `why`: One backtest does not answer whether Money Flow has edge. The founder needs to compare components/timeframes, fill-timing assumptions, symbols, windows, and cost assumptions before deciding whether paper trading is justified.
- `rejected_alternatives`: Changing Money Flow rules, adding parameter optimization, recommending a strategy variant, creating paper/live trading artifacts, connecting validation to routing/execution automation, or calling exchange adapters.
- `follow_up_implications`: SV1.2 should review comparative outputs and likely deepen data coverage and market-regime labeling before any paper-trading or strategy-rule changes.

## 2026-05-01T19:20:34Z - SV1.2 - Regime And Coverage Before Paper Trading

- `decision`: Add data-coverage and deterministic market-regime reporting to Money Flow validation as descriptive research diagnostics.
- `why`: A strategy can appear profitable overall while relying on one market regime or weak historical data coverage. Founder/operator review needs coverage warnings and regime-grouped performance before paper trading is considered.
- `rejected_alternatives`: Changing Money Flow rules, optimizing parameters, recommending a variant, adding paper/live trading, connecting validation to routing/execution, or using regimes as strategy filters.
- `follow_up_implications`: Future Strategy Validation should broaden historical data ingestion/coverage and review regime evidence before any paper-trading readiness or strategy-rule change is scoped.

## 2026-05-01T20:12:36Z - SV1.2.1 - Standardize Validation Window Truth

- `decision`: Use candle closes in `(start_at, end_at]` everywhere in Strategy Validation and keep blocked runs visible in grouped batch comparisons.
- `why`: SV1.3 campaign/evidence-pack reports would be misleading if adjacent windows double-counted boundary candles, if coverage could exceed 100% on unaligned windows, or if blocked runs disappeared from grouped comparison tables.
- `rejected_alternatives`: Keeping mixed inclusive/exclusive semantics; treating unaligned coverage as exact without warnings; filtering grouped comparisons down to completed runs only; changing Money Flow strategy rules or optimizing parameters.
- `follow_up_implications`: SV1.3 can build repeatable research campaigns on a cleaner window/coverage truth layer, while validation remains research-only and disconnected from live routing/execution.

## 2026-05-01T21:08:26Z - SV1.3 - Repeatable Research Campaign Evidence Packs

- `decision`: Add explicit JSON Money Flow research campaign configs plus timestamped evidence-pack output on top of the existing Strategy Validation batch runner.
- `why`: Founder/operator review needs repeatable evidence across symbols, components, fill timings, windows, fees, and slippage assumptions rather than isolated one-off backtests.
- `rejected_alternatives`: Adding parameter optimization; recommending a strategy variant; changing Money Flow rules; adding paper/live trading; connecting validation output to routing/execution automation; storing evidence as live execution artifacts.
- `follow_up_implications`: Future SV work should review campaign evidence packs, broaden historical data coverage where needed, and scope paper-trading readiness only after evidence review.

## 2026-05-02T05:22:25Z - SV1.4 - Evidence Readiness Before Paper Trading

- `decision`: Add canonical editable Money Flow campaign configs, campaign data-readiness audit, evidence-pack review checklist, and manual paper-trading readiness criteria without changing strategy rules.
- `why`: Evidence packs are useful only when data coverage and blocked runs are explicit and founder/operator review criteria are defined before any paper-trading decision.
- `rejected_alternatives`: Auto-approving paper trading from campaign reports; optimizing Money Flow rules; recommending a strategy variant; adding paper/live trading artifacts; connecting validation outputs to routing or execution automation.
- `follow_up_implications`: Next SV work should run/review canonical campaigns on real persisted data, backfill historical candle gaps where the audit shows weakness, and scope paper-trading readiness only after manual evidence review.

## 2026-05-02T06:57:28Z - SV1.4.1 - Evidence Packs Must Not Overwrite

- `decision`: Use `unique_suffix` as the default evidence-pack collision policy, with `fail_if_exists` available for explicit fail-fast workflows.
- `why`: Research evidence packs must behave like durable records. A same-campaign same-timestamp rerun should never silently replace an existing `manifest.json`, report, config copy, or README before SV1.5 starts generating real evidence.
- `rejected_alternatives`: Keeping `mkdir(..., exist_ok=True)` and overwriting files; relying on operators to avoid same-second runs; making the default fail unexpectedly for founder/operator workflows.
- `follow_up_implications`: SV1.5 can generate first real campaign evidence packs using stable final run ids and manifest collision truth. Future comparison tooling should use `final_run_id` / `final_evidence_pack_path` rather than assuming requested timestamps are unique.

## 2026-05-02T07:36:56Z - SV1.5 - Offline Public Candle Import Before Evidence Review

- `decision`: Use validated campaign window-convention metadata plus offline/public CSV/JSON candle import/upsert tooling as the first historical-data remediation path for canonical Money Flow evidence runs.
- `why`: SV1.5 needs a safe way to make missing persisted candles visible and remediable before first meaningful evidence-pack review. Offline/public imports are narrower than adapter-driven backfill, avoid private or order endpoints, and keep Strategy Validation separate from routing/execution automation.
- `rejected_alternatives`: Treating config `window_convention` text as behavior-changing; requiring live public adapter backfill for SV1.5; calling private exchange or order endpoints; creating live desired trades, approvals, routing artifacts, paper trades, or submitted orders from validation; changing Money Flow rules to fit available data.
- `follow_up_implications`: Future evidence review should rerun canonical audits after sufficient candle data is imported or confirmed. If per-candle source provenance becomes required, the candle persistence model may need a separate schema change; current import source labels are summary-only.

## 2026-05-02T08:21:54Z - SV1.5.1 - Historical Candle Import Truth Before Evidence Review

- `decision`: Harden campaign window-convention validation and offline candle imports before SV1.6 uses imported candles for first real evidence review.
- `why`: Evidence packs can be misleading if config text implies inclusive-start windows, if an existing candle can be silently retargeted to a different symbol/instrument identity, if row duration does not match the selected timeframe, or if malformed OHLCV rows partially persist. Import integrity must be fixed before saved campaign evidence is reviewed.
- `rejected_alternatives`: Treating contradictory `window_convention` text as harmless metadata; allowing existing candle identity retargeting during upsert; accepting timeframe-duration mismatches; accepting non-finite, zero, negative, or internally inconsistent OHLCV rows; allowing partial invalid-file imports; changing Money Flow rules, adding optimization, adding paper/live trading, routing, or execution behavior.
- `follow_up_implications`: SV1.6 can review canonical evidence packs on a safer historical candle substrate. Future provenance work may still add per-candle source fields, but SV1.5.1 remains schema-free and source labels remain import-summary-only.

## 2026-05-03T05:27:59Z - SV1.6 - First Canonical Evidence Review Is Descriptive Only

- `decision`: Add a canonical Money Flow evidence-review layer that audits canonical campaign configs, reports insufficient data directly, and generates collision-safe evidence packs only when data-readiness audits are clean.
- `why`: The founder needs a repeatable way to see which canonical campaigns can run, which are blocked by data, where generated packs are located, and whether evidence is ready for manual review without treating missing data as strategy failure or treating backtests as approval for paper trading.
- `rejected_alternatives`: Auto-approving paper trading from evidence summaries; treating insufficient data as a Money Flow failure; changing or optimizing Money Flow rules; adding strategy recommendations; adding paper/live trading artifacts; calling exchange adapters, private endpoints, or order endpoints; connecting validation output to routing/execution automation.
- `follow_up_implications`: Next work should import or verify enough public historical candles, rerun the canonical review with evidence generation enabled, and use founder/operator review before any paper-trading design is scoped.

## 2026-05-03T08:08:05Z - SV1.7 - Evidence Review Must Report DB/Data Gaps Before Packs

- `decision`: Make canonical Money Flow evidence review inspect and report sanitized DB reachability, candle-table existence, persisted candle count, and DB/schema blockers before attempting campaign evidence generation.
- `why`: SV1.6 showed the default `postgres` host could be unresolved in the local shell. First real evidence review must not hide connection/schema failures or present missing persisted candles as a strategy result.
- `rejected_alternatives`: Treating DB connection failure as a test-only concern; generating evidence packs from incomplete audits; treating a reachable database without `candles` as ready; changing Money Flow rules; importing data automatically from exchange/private/order endpoints; connecting validation to routing/execution automation.
- `follow_up_implications`: Evidence remains `insufficient_data` until a reachable migrated Money Flow database is available and populated with enough canonical BTC/ETH/SOL candles. Mixed future outcomes should use `partial_evidence_ready_with_data_gaps` so generated packs cannot be mistaken for complete canonical evidence.

## 2026-05-03T14:04:33Z - SV1.8 - Evidence Review Must Distinguish DB Reachability From Migrated Schema

- `decision`: Extend canonical Money Flow evidence review with DB/schema/migration bootstrap status and a read-only `--db-status-only` CLI path before evidence-pack generation.
- `why`: SV1.7 established that a local Postgres endpoint can be reachable yet still unusable for evidence review. Founder/operator review needs to know whether the intended DB is migrated, whether Alembic has recorded a current revision, whether `candles` exists, and whether canonical candles are present before interpreting campaign gaps.
- `rejected_alternatives`: Treating reachable-but-unmigrated DBs as simple candle-data gaps; applying migrations automatically to an ambiguous `postgres` database; generating placeholder evidence packs; importing candles without an explicit migrated DB target; changing Money Flow rules; adding optimization, recommendations, paper/live trading, routing, or execution behavior.
- `follow_up_implications`: Next Strategy Validation work should point at or create the intended Money Flow database, run Alembic to head, import public/offline BTC/ETH/SOL candles for the canonical windows/timeframes, rerun canonical evidence review with `--generate-evidence-packs`, and keep paper-trading design deferred until founder/operator review of real packs.

## 2026-05-03T14:40:50Z - SV1.8.1 - Evidence Packs Require Migrated Schema Truth

- `decision`: Gate canonical evidence-pack generation on `migrated_schema_ready`, current Alembic migration truth, and required strategy-validation tables (`candles`, `instruments`, and `symbols`) rather than raw `candles` table presence.
- `why`: Evidence packs should not be generated from a database whose schema state is unknown or partial. A `candles` table without Alembic truth or required symbol/instrument schema can mislead founder/operator research review before first real evidence packs.
- `rejected_alternatives`: Treating a `candles` table as sufficient schema truth; letting missing Alembic truth proceed to evidence-pack generation; allowing partial required schema to fail downstream during canonical review; relying on top-level no-live/no-exchange dataclass defaults rather than aggregating campaign results.
- `follow_up_implications`: First real evidence-pack work must use a reachable DB that reports `migrated_schema_ready` before generating packs. Missing/outdated migration truth remains a schema/data readiness gap, not a Money Flow strategy result.

## 2026-05-03T20:11:02Z - SV1.9 - Evidence Review Must Expose Intended DB Target And Import Requirements

- `decision`: Extend canonical Money Flow evidence review with sanitized DB target metadata, intended-database classification, maintenance-database warnings, and canonical candle import requirements before first real evidence packs.
- `why`: SV1.8/SV1.8.1 made schema readiness authoritative, but founder/operator review still needed clarity on which configured DB was intended for strategy validation and exactly which canonical candles are missing. A `postgres` maintenance database target should not be silently treated as canonical Money Flow evidence storage.
- `rejected_alternatives`: Treating any reachable Postgres database as intended; generating evidence packs from an ambiguous maintenance database; hiding canonical candle gaps behind generic blocked runs; changing Money Flow rules; adding optimization, recommendations, paper/live trading, routing, exchange calls, or execution behavior.
- `follow_up_implications`: Next work should use a reachable migrated non-maintenance Money Flow database, import or verify the reported canonical BTC/ETH/SOL candle requirements, and rerun evidence review with `--generate-evidence-packs` only after schema and data readiness are clean.

## 2026-05-03T22:02:39Z - SV1.9.1 - Evidence Generation Requires Intended DB Target And Explicit Candle Timezones

- `decision`: Block evidence-pack generation from ambiguous or non-intended maintenance DB targets by default, reject timezone-naive candle imports by default, and refresh Obsidian current-truth memory through SV1.9 before first real evidence packs.
- `why`: A migrated `postgres` maintenance database with candles would otherwise be able to produce canonical-looking evidence despite not being the intended strategy-validation DB. Similarly, silently treating naive public CSV/JSON timestamps as UTC could corrupt historical candle truth before first real evidence review.
- `rejected_alternatives`: Treating maintenance DB ambiguity as a warning only; adding a broad ambiguous-DB override in this phase; silently assuming UTC for naive timestamps; treating override-derived imports as clean canonical evidence; generating first real evidence packs before target/schema/candle truth is clean.
- `follow_up_implications`: SV1.10 can prepare a migrated non-maintenance Money Flow DB and import timezone-explicit canonical candles. If an override is ever added for ambiguous DB targets, it must be explicit, provenance-rich, and non-canonical by default.

## 2026-05-04T05:14:29Z - SV1.10 - Use Local `money_flow` DB But Do Not Generate Packs Without Candles

- `decision`: Treat `postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow` as the intended local strategy-validation DB for this shell, migrate it to Alembic head, and keep canonical evidence generation blocked until real persisted candles exist.
- `why`: SV1.9/SV1.9.1 established that maintenance DBs and unknown schema cannot produce credible evidence. SV1.10 made the non-maintenance local DB concrete and current, but evidence review still found zero persisted candles, so generating packs would be misleading.
- `rejected_alternatives`: Using the `postgres` maintenance database; weakening DB-target/schema gates; generating placeholder evidence packs; treating missing candles as Money Flow failure; changing Money Flow rules; importing timezone-naive data as canonical.
- `follow_up_implications`: Next SV work should import timezone-explicit BTC/ETH/SOL candles for the 18 unique canonical requirements, rerun evidence review with generation enabled, and keep paper-trading design deferred until founder/operator review sees real evidence.

## 2026-05-04T06:06:09Z - SV1.11 - Seed Market Identity Before Candle Import

- `decision`: Add an offline/manual research-only market identity manifest plus seed/verify CLI before importing canonical candles.
- `why`: SV1.10 produced a migrated intended DB but no canonical BTC/ETH/SOL instrument or symbol rows. The candle importer correctly requires those mappings before candle writes, so evidence work needs a safe identity-readiness step before file import.
- `rejected_alternatives`: Auto-fetching exchange metadata; treating placeholder manifest values as live trading eligibility; importing candles without symbol/instrument mappings; changing Money Flow rules; generating evidence packs in this phase.
- `follow_up_implications`: Next SV work should have the founder/operator verify manifest tick/size values, seed or verify market identity, preflight timezone-explicit candle files, import candles only after preflight passes, and generate evidence packs only after target/schema/identity/data readiness is clean.

## 2026-05-04T07:15:35Z - SV1.11.1 - Identity Writes Need Operator Verification And Preflight Must Prove Requirements

- `decision`: Require explicit operator verification plus `verified_by` provenance before non-dry-run market-identity seed writes, and add requirement-aware candle preflight that maps input files to canonical requirements and verifies exact `(start_at, end_at]` close-time slots.
- `why`: Row-level file validation alone can pass for a file that does not satisfy a specific canonical requirement, and writing example-derived market identity without an explicit operator guard could make manual placeholder values look accepted.
- `rejected_alternatives`: Treating dry-run success as authorization to write; allowing unverified example manifests to seed identity rows; treating row-level candle validation as canonical coverage proof; importing candles or generating evidence packs in the hardening phase.
- `follow_up_implications`: SV1.12 should use operator-verified identity seed/verify plus requirement-aware `ready_for_import=true` preflight before guarded canonical candle import. First real evidence packs remain deferred until target/schema/identity/candle readiness is clean.

## 2026-05-04T19:48:32Z - SV1.11.2 - Research Identity Must Stay Non-Trading And Preflight Mapping Must Be Complete

- `decision`: Block Strategy Validation market-identity seed manifests that set `is_strategy_eligible=true` or `is_trading_eligible=true`, and require complete one-to-one input-file-to-requirement mapping for requirement-aware candle preflight.
- `why`: The research seed uses shared `SymbolModel` rows that execution/routing code can inspect, so it must not be able to promote symbols into trading eligibility. Requirement-aware preflight also must not let unmapped files or unmapped requirements appear ready before guarded import.
- `rejected_alternatives`: Allowing manifest edits to promote trading eligibility; treating partial preflight coverage as acceptable; silently ignoring extra files or missing requirements; importing candles or generating evidence packs in the governance hotfix.
- `follow_up_implications`: SV1.12 can proceed to guarded canonical candle bundle import only after operator-verified non-trading identity and complete one-to-one `ready_for_import=true` preflight pass for the canonical candle files.

## 2026-05-04T20:26:41Z - SV1.12 - Guarded Candle Import Remains Separate From Evidence Packs

- `decision`: Canonical candle bundle import must compose intended non-maintenance DB target truth, migrated/current schema truth, operator-verified non-trading research identity, complete one-to-one requirement-aware preflight, and hardened importer success before candle writes; SV1.12 does not generate evidence packs.
- `why`: Importing historical candles is data readiness, not strategy evidence. Keeping import separate from evidence-pack generation makes failures auditable and prevents partial preflight, ambiguous DB targets, or unverified identity from becoming first-real Money Flow evidence.
- `rejected_alternatives`: Generating evidence packs in the import phase; importing from ambiguous maintenance DB targets; allowing unverified or trading-eligible identity; treating row-level preflight alone as canonical coverage proof; changing Money Flow rules; adding routing/execution behavior.
- `follow_up_implications`: SV1.13 may run post-import canonical evidence review and generate collision-safe packs only after guarded import status and data-readiness audits are clean; otherwise it should report remaining data gaps.

## 2026-05-04T20:50:34Z - SV1.12.1 - Partial Import Truth Must Be Explicit Before Operational Import

- `decision`: Guarded canonical candle bundle import uses explicit partial-persistence semantics (`explicit_partial_with_resume`) instead of implying all-or-nothing bundle behavior across lower-level per-file commits. Unmapped input files and missing requirements must appear directly in operator output.
- `why`: The lower-level candle importer commits per file. If a later file fails after an earlier file commits, the platform must not let partial historical data look like a complete canonical import. Operators also need to see which exact input file or requirement is unmapped/missing without reverse-engineering global reason codes.
- `rejected_alternatives`: Pretending bundle import is all-or-nothing without refactoring the lower-level importer transaction boundary; hiding unmapped files or missing requirements only in aggregate reason codes; generating evidence packs after a partial import; treating missing identity/files as strategy failure.
- `follow_up_implications`: Complete guarded canonical import remains required before SV1.13 evidence review. If partial persistence occurs, rerun is duplicate-safe for same identity, but evidence review must remain blocked until final import status is `canonical_import_complete`.

## 2026-05-04T21:28:20Z - SV1.12.2 - Do Not Seed Identity Without Operator Verification

- `decision`: Treat SV1.12.2 as readiness-only unless the founder/operator explicitly verifies the Hyperliquid perpetual USDC BTC/ETH/SOL market-identity manifest values. The phase documents the exact 18 canonical candle-file requirements and may run preflight-only checks, but imports no candles and generates no evidence packs.
- `why`: SV1.12.1 showed the DB/schema gate is ready but identity and files are missing. Writing shared `SymbolModel` rows or importing candles before explicit identity verification and complete file coverage would make first evidence review less trustworthy.
- `rejected_alternatives`: Seeding example manifest values without operator verification; treating missing identity/files as strategy failure; importing partial candle files; running evidence review/evidence packs before guarded import completes.
- `follow_up_implications`: SV1.12.3 should seed only operator-verified non-trading research identity, preflight all 18 timezone-explicit candle files one-to-one against canonical requirements, and run guarded import only when every gate is clean.

## 2026-05-04T22:20:00Z - SV1.12.3 - Guarded Import Attempt Blocks Without Verification And Files

- `decision`: Add an operational guarded import attempt wrapper, but keep identity seed and candle import blocked unless explicit operator verification, offline market-value confirmation, and all 18 preflight-ready canonical files are supplied.
- `why`: The intended DB/schema gate is ready, but first real evidence integrity still depends on verified market identity and complete historical candle coverage. A single command should make the blocked state founder-readable without seeding unverified identity, importing partial files, or generating evidence packs.
- `rejected_alternatives`: Seeding identity from the example manifest without explicit verification; importing a partial file set; treating missing files as strategy evidence; generating evidence packs in the import phase; relaxing requirement-aware preflight.
- `follow_up_implications`: The next operator action is to provide explicit verification plus all 18 timezone-explicit files, then rerun the guarded import attempt until final status is `canonical_import_complete`. SV1.13 remains blocked until that import status and data-readiness audits are clean.

## 2026-05-05T05:56:00Z - SV1.12.x - Public Identity Verified, Import Still Blocked

- `decision`: Accept public Hyperliquid `meta` as the research identity source for BTC/ETH/SOL perpetual USDC manifest values, update the manifest with those values, and keep DB seeding/import blocked until founder/operator approval plus complete 18-file preflight exists.
- `why`: Public `meta` verifies the current asset ids, size decimals, leverage, and margin table ids needed for research identity, but first canonical import still needs operator-verified DB rows and complete historical candle coverage. Hyperliquid public `candleSnapshot` could produce the 12 `1h`/`4h` files but returned zero rows for the six January 2026 `15m` windows.
- `rejected_alternatives`: Seeding identity without explicit approval; treating public verification as a non-dry-run operator verification; fabricating 15m candles; importing the 12 partial files; generating evidence packs from incomplete data.
- `follow_up_implications`: Next work should seed non-trading research identity only with explicit `verified_by`, source the missing six 15m files from trusted public/vendor/operator/trade-derived data with provenance, rerun complete 18-file requirement-aware preflight, and only then rerun guarded import.

## 2026-05-05T07:43:37Z - SV1.12.4 - Public YTD/Recent Campaign Selected

- `decision`: Keep January 2026 as an archival/vendor-data-required campaign and select a public Hyperliquid first-evidence data plan using BTC/ETH/SOL `1h` and `4h` from `2026-01-01T00:00:00Z` to `2026-05-05T00:00:00Z`, plus BTC/ETH/SOL `15m` from `2026-03-15T00:00:00Z` to `2026-05-05T00:00:00Z`.
- `why`: The prior public January `15m` plan was too old for Hyperliquid public `candleSnapshot`. The initially suggested `2026-03-14T00:00:00Z -> 2026-05-05T00:00:00Z` recent `15m` probe still missed the first close slots, while the 51-day `2026-03-15T00:00:00Z -> 2026-05-05T00:00:00Z` window produced complete public close-slot coverage.
- `rejected_alternatives`: Treating January `15m` as public-baseline data; accepting a recent `15m` file with missing close slots; fabricating candles; using private/signed/order/account endpoints; seeding identity without founder/operator approval; importing candles while preflight is blocked; generating evidence packs from unimported or incomplete data.
- `follow_up_implications`: The next Strategy Validation bridge should seed non-trading research identity only with explicit `verified_by`, rerun requirement-aware preflight for the 9 public campaign files, then run guarded import only if preflight passes. January 2026 can still be pursued separately through vendor/archive/operator-provided data.

## 2026-05-06T06:17:04Z - SV1.12.5 - Supported-Venue Public Candle Readiness Is Source-Limited

- `decision`: Extend the public YTD/recent candle readiness plan across registry-supported venue adapters while keeping Hyperliquid as the nearest guarded-import path. Accept Aster and Binance public files as candidate native-trade-count datasets for later identity-gated preflight; mark OKX and Coinbase blocked under the current canonical trade-count contract; mark Kraken blocked by incomplete public REST coverage.
- `why`: Aster and Binance public kline endpoints returned complete BTC/ETH/SOL `15m` recent plus `1h`/`4h` 2026 YTD coverage with native trade counts. OKX and Coinbase returned complete close-slot OHLCV coverage but no trade-count field, which the canonical CSV contract currently requires. Kraken public REST OHLC did not return complete selected-window coverage.
- `rejected_alternatives`: Fabricating trade counts; treating zero placeholder trade counts as canonical for OKX/Coinbase; accepting Kraken partial files; using private/signed/order/account endpoints or API keys; seeding venue identity without founder/operator verification; importing candles or generating evidence packs while identity/source gates are blocked.
- `follow_up_implications`: Hyperliquid should remain the first guarded-import candidate after operator-verified non-trading identity is seeded. Broader venue comparison requires Aster/Binance identity verification/seed first, an explicit trade-count source or contract decision for OKX/Coinbase, and archive/vendor/operator coverage for Kraken.

## 2026-05-06T21:01:42Z - External Review - Paper/Live Trading Blockers Must Be Fixed First

- `decision`: Track the 2026-05-06 external security/risk review findings as standing blockers before paper trading, live trading, exposed API usage, or production-like deployment.
- `why`: Reported local live credentials, unauthenticated execution-facing API routes, unenforced configured risk limits, hardcoded drawdown truth, debug exposure, config mode ambiguity, and backtest fee/drawdown limitations can make the platform unsafe or misleading even if the Strategy Validation data track continues.
- `rejected_alternatives`: Treating the findings as normal cleanup; proceeding to paper/live trading after candle import/evidence alone; storing actual secret values in Obsidian; weakening current Strategy Validation research-only boundaries.
- `follow_up_implications`: Before paper/live trading, rotate reported credentials, add API auth, enforce risk limits, calculate real drawdown, fix Strategy Validation mark-to-market fee truth, make exposed config fail-safe, and add regression tests/review for the critical/high items. Current research-only data readiness work can continue separately.

## 2026-05-06T21:09:00Z - External Strategy Review - Treat Concerns As Validation Questions

- `decision`: Track the external strategy critique as Strategy Validation questions, not as immediate Money Flow rule changes.
- `why`: The strategy may be coherent, but no first real evidence packs exist yet. Concerns about no hard stop-loss, narrow RSI bands, lagging MACD exits, long-only exposure, optimistic same-candle fills, cosmetic confidence scores, sizing/drawdown assumptions, and handcrafted parameters should shape evidence review before any paper-trading or rule-change phase.
- `rejected_alternatives`: Adding ATR stops immediately; optimizing RSI/extension/MACD parameters before real evidence; treating same-candle research results as paper/live readiness; presenting the current strategy as proven.
- `follow_up_implications`: Evidence review should emphasize next-candle-open fills, out-of-sample validation, risk-adjusted metrics such as Sharpe/Sortino, fee/slippage/drawdown truth, and a later explicitly scoped strategy-change phase if evidence supports changes.

## 2026-05-06T22:20:00Z - SV1.12.5 - Hyperliquid Public Campaign Imported After Operator Approval

- `decision`: Use explicit founder/operator approval to seed only Hyperliquid BTC/ETH/SOL research identity as non-trading/non-strategy-eligible, then import only the 9-file Hyperliquid public YTD/recent campaign after requirement-aware preflight passes.
- `why`: Hyperliquid is the nearest clean first-evidence data path: public identity metadata is verified, public candle files have native trade count and complete close-slot coverage, and its USDC perpetual product should not be mixed with Aster/OKX USDT perps or Binance/Coinbase/Kraken spot products. Completing import before evidence review preserves the SV1.12 import/evidence boundary.
- `rejected_alternatives`: Using the archival January 18-file campaign as the public baseline; importing Aster/Binance/OKX/Coinbase/Kraken in the same phase; treating OKX/Coinbase placeholder trade counts as canonical; generating evidence packs during import; enabling strategy/trading eligibility; calling private/order endpoints.
- `follow_up_implications`: SV1.13 can run post-import Hyperliquid evidence review/evidence-pack generation if data-readiness audits are clean. Paper-trading design remains deferred pending founder/operator review of evidence packs and unresolved pre-paper/live blockers.

## 2026-05-06T22:23:16Z - SV1.12.5.1 - Close Import State Before Evidence Packs

- `decision`: Treat the accepted SV1.12.x / SV1.12.4 / SV1.12.5 source, tests, docs, and Obsidian updates as the reviewed import baseline, verify the intended DB import state, and commit a clean repo state before SV1.13 evidence generation.
- `why`: The SV1.12.5 operational import succeeded but was left on a dirty tree containing prior readiness work. Strategy Validation evidence generation should not start while repo state, Obsidian state, and imported DB truth are ambiguous.
- `rejected_alternatives`: Leaving the dirty tree for SV1.13; generating evidence packs before repo/data-state closeout; reverting accepted readiness/import changes without evidence; committing generated candle files, local import outputs, evidence packs, secrets, or review bundles.
- `follow_up_implications`: SV1.13 can proceed as post-import evidence review only if the committed repo baseline, intended DB/schema, operator-verified non-trading identity, and imported candle counts remain clean. No paper/live trading decision follows automatically from import readiness.

## 2026-05-06T23:12:10Z - SV1.13 - First Hyperliquid Public Evidence Is Review-Only

- `decision`: Generate first Money Flow evidence packs only from the imported Hyperliquid public YTD/recent campaign and expand the public config into component-scoped evidence configs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- `why`: The public campaign has component-specific timeframe windows. Treating those windows as a Cartesian matrix would create false audit combinations, while Hyperliquid is the only venue with operator-verified research identity and imported public campaign candles in the intended DB.
- `rejected_alternatives`: Combining Aster/Binance/OKX/Coinbase/Kraken with Hyperliquid; using the old January archival/vendor-data-required campaign as the public first-evidence baseline; treating generated evidence as paper/live approval; changing Money Flow rules or optimizing parameters.
- `follow_up_implications`: Founder/operator manual review is now the next Strategy Validation step. Paper-trading design remains deferred unless explicitly approved after reviewing Hyperliquid-only data coverage, fill timing robustness, drawdown, regime behavior, costs, no-trade reasons, and standing pre-paper/live blockers.

## 2026-05-07T07:50:13Z - SV1.13 Dashboard - Visualization Is Review-Only

- `decision`: Add a static local dashboard for human review of generated Strategy Validation evidence artifacts, using the newly supplied design files and keeping it separate from evidence generation/import/trading workflows.
- `why`: The founder needs a readable way to inspect evidence-pack results, fill-timing sensitivity, component behavior, symbols, regimes, and manual-review blockers without reading raw JSON or Markdown tables.
- `rejected_alternatives`: Generating new evidence from the dashboard; connecting it to trading approval; adding API/exchange calls; treating visualization as proof of profitability; changing Money Flow strategy rules.
- `follow_up_implications`: Manual founder/operator evidence review can use `apps/dashboard/`, but paper/live trading remains deferred until explicit approval and standing blockers are resolved.

## 2026-05-09T15:35:00Z - UAT0.1 - Protect Sensitive API Routes And Keep Runtime Fail-Closed

- `decision`: Add scoped bearer authentication/authorization to sensitive `/api/v1` routes and add an inspectable runtime safety policy whose defaults keep paper trading, live trading, private exchange endpoints, and exchange order submission disabled.
- `why`: UAT0 found UAT1 blocked by unauthenticated sensitive control-plane routes and ambiguous runtime/live lockout truth. Before read-only connectivity can be considered, operator/admin surfaces must fail closed and runtime capability flags must be visible and safe by default.
- `rejected_alternatives`: Leaving sensitive routes public because execution submit gates are disabled; adding a broad unauthenticated local-only exception; enabling sandbox/read-only exchange connectivity in the same phase; treating central runtime flags as permission to submit orders.
- `follow_up_implications`: UAT1 remains blocked until adapter-level runtime-policy enforcement, selected-venue sandbox/read-only endpoint policy, structured secret/log/error redaction, runtime drawdown monitoring, and top-20 market identity resolution are completed or explicitly accepted. Paper trading, live trading, and exchange order submission remain unapproved.

## 2026-05-10T19:50:14Z - UAT3.3 - Hyperliquid Account Targeting And Precision Are Gate Requirements

- `decision`: Treat Hyperliquid account targeting and order precision as explicit UAT sandbox gates. Normal master/user accounts must omit `vaultAddress`; subaccount/vault targets may use `vaultAddress` only when explicitly configured. API-wallet signer identity is separate from the target account. Hyperliquid price/size formatting must use venue metadata precision before any sandbox order transport.
- `why`: Sanitized testnet diagnostics showed that copying a normal/main account into `vaultAddress` caused `Vault not registered`, while switching to a subaccount removed that rejection and exposed the next blocker: `Price must be divisible by tick size. asset=4`. These are integration correctness gates, not strategy questions.
- `rejected_alternatives`: Inferring vault/subaccount mode from an address string alone; copying the target account into `vaultAddress` for normal user/master mode; formatting prices with binary floats or generic decimal places; bypassing the sandbox equity gate to force an order attempt.
- `follow_up_implications`: UAT3.3 verifies the configured subaccount targeting and signer authorization and produces an exchange-valid ETH post-only planned order shape, but blocks before `/exchange` because the target subaccount live-fed sandbox equity is `0.0`. UAT3.4 remains blocked until sufficient testnet equity is visible on the configured target under separate founder/operator approval. Paper trading, live trading, broad top-20 order submission, routing/SOR/fanout, future orders, and Money Flow rule changes remain unapproved.

## 2026-05-11T05:50:00Z - UAT3.4 - Fixed-Target Sandbox Routing Ledger Is The Current UAT Route

- `decision`: Treat the working Hyperliquid testnet ETH lifecycle as a fixed-target sandbox route, not smart routing. UAT3.4 route id is `fixed_target_hyperliquid_testnet_eth`, active account mode is normal user with `vaultAddress` omitted, active equity source is `standard_perp_clearinghouse`, and unified/portfolio spot-clearinghouse USDC fallback remains implemented for compatibility.
- `why`: UAT3.3 and the follow-up diagnostics proved the earlier integration issues were account targeting, order precision, and sizing rather than Money Flow strategy logic. UAT3.4 needed repeatable operational plumbing and a routed-order ledger without reintroducing SOR/fanout/target reselection or dashboard execution controls.
- `rejected_alternatives`: Enabling broad top-20 sandbox order submission; adding smart routing/SOR/fanout/CBBO/target reselection; treating UAT3.4 as Money Flow performance validation; removing unified-mode support because current funds are in the standard perp wallet; adding a dashboard order button.
- `follow_up_implications`: UAT4.0 live UAT dashboard/chart cockpit may be scoped around visualization, watchlists, charts, indicators, and routed-order overlays. UAT3.5 additional sandbox routing lifecycle tests remain blocked until UAT-universe precision validation is complete or unsupported testnet observation symbols are explicitly scoped out under a later approval.

## 2026-05-11T06:45:00Z - UAT4.0 - Read-Only UAT Chart Cockpit Is The Current Dashboard Surface

- `decision`: Add a static read-only `UAT Chart Cockpit` dashboard tab that visualizes UAT watchlist, market-data coverage, chart snapshots, indicators, shadow/sandbox lifecycle markers, active ETH sandbox route/equity-source status, and routed-order ledger filters from committed local UAT2/UAT3.4 JSON summaries.
- `why`: Founder review needs a cockpit that makes shadow signals and sandbox lifecycle plumbing visually inspectable without confusing UAT sandbox behavior with paper/live trading or enabling order actions.
- `rejected_alternatives`: Adding live/private exchange refresh in this phase; adding order/cancel/retry/amend/approval buttons; adding paper/live toggles; treating shadow would-open markers as actual trades; treating sandbox lifecycle probes as Money Flow performance validation.
- `follow_up_implications`: UAT4.1 was scoped as an exchange-style dashboard redesign; UAT4.2 public-read-only live refresh may be scoped later. UAT3.5 additional sandbox routing lifecycle tests remain blocked by precision-validation scope and separate approval. Paper trading, live trading, dashboard order controls, broad top-20 orders, smart routing/SOR/fanout, Money Flow rule changes, and evidence packs remain unapproved.

## 2026-05-11T07:03:40Z - UAT4.1 - Dashboard Becomes An Exchange-Style UAT Workstation

- `decision`: Rebuild the UAT dashboard around an exchange-style information architecture: compact top bar, persistent safety banner, observation-only left market rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs. Make `apps/dashboard/DESIGN.md` the canonical dashboard design system and reduce root `DESIGN.md` to a pointer.
- `why`: Founder review found the UAT4.0 report-card layout hard to understand. The cockpit needed to answer what market is active, what Money Flow observed, where sandbox lifecycle markers occurred, what happened to routed orders, and whether paper/live/order controls are disabled without more disconnected cards.
- `rejected_alternatives`: Copying exchange branding or logos; adding order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls; adding private/signed/order endpoint calls; implementing live public refresh before fixing layout hierarchy.
- `follow_up_implications`: UAT4.2 may scope public-read-only live refresh and chart-library integration. UAT3.5 additional sandbox lifecycle tests remain blocked by precision-validation scope and separate approval. Paper trading, live trading, dashboard order controls, broad top-20 orders, smart routing/SOR/fanout, Money Flow rule changes, and evidence packs remain unapproved.
