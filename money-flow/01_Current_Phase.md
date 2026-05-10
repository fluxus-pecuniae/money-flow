# Current Phase

## Current Implemented Milestone

`UAT3.1` first approval-gated sandbox/testnet order attempt is complete.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named gaps were closed. UAT0.1 closes the P0 API auth/authz baseline and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verifies allowed public Hyperliquid endpoint behavior, fetches a no-key public top-volume source, and resolves the Hyperliquid-supported top-20 observation universe. UAT1.1 adds shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 completed a bounded no-order Money Flow shadow observation across the UAT1 Hyperliquid top-20-supported universe. UAT2.1 makes that UAT2 output visually reviewable in the static dashboard and adds an informational UAT3 blocked readiness panel. UAT3.0 through UAT3.0.6 define and dry-run the sandbox/testnet gate chain. UAT3.1 is complete: exact founder/operator approval was verified, one Hyperliquid testnet ETH post-only limit order attempt under 10 USDC notional was made, Hyperliquid rejected it with a sanitized user/API-wallet-not-found response, no cancel was required, reconciliation found no open order, and no production execution artifacts were created.

SV1.18 is complete.

## Next Proposed Phase

`UAT3.2` additional sandbox lifecycle testing may be scoped only with separate approval.

UAT3.2 requires a separate founder/operator approval and should first address the UAT3.1 venue rejection: Hyperliquid testnet reported the submitted user/API wallet did not exist. A future accepted/open -> cancel lifecycle attempt should only be scoped after sandbox account/API-wallet configuration is reviewed. UAT remains plumbing and behavior validation only. It is not paper trading, live trading, unrestricted exchange order submission, routing expansion, or strategy optimization.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| UAT mode | Observation / shadow first |
| Execution | None until a later explicitly gated UAT phase |

The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline.

## UAT Observation Universe And Timing

Future UAT observation is not ETH-only. UAT1/UAT2 should use top 20 high-volume crypto assets supported by the selected UAT venue/environment to validate platform behavior, market metadata, symbol mapping, risk visibility, no-trade/rejected-signal reasoning, and operator explainability. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared:

- `next_candle_open`
- `next_candle_close`

`same_candle_close_research_only` remains research-only.

## Explicit Non-Approvals

- Paper trading is not approved.
- Live trading is not approved.
- Additional exchange order submission is not approved.
- Production Money Flow rule changes are not approved.
- Lower-RSI variants are not approved.
- Market-structure variants are not approved.
- Cross-venue evidence is not current UAT scope.
- Routing / SOR expansion is not current priority.

## Current Evidence Meaning

Current backtest/replay evidence does not prove profitability or future edge. It was sufficient only to justify founder review and a tightly scoped UAT0 safety/runtime audit.

SV1.18 selected ETH `sleeve_1h` baseline because it is the strongest observed Hyperliquid public-candle scenario. That does not make it a production strategy.

Excluded from UAT scope:

- `sleeve_15m`
- `sleeve_4h`
- BTC `sleeve_1h`
- SOL `sleeve_1h`
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 Result

UAT0 initially found UAT1 blocked. UAT0.1 closed these P0 items:

- API authentication / authorization for sensitive `/api/v1` routes.
- High-risk route authorization for admin consume, submit/cancel/amend/retry, account, and private-state surfaces.
- Inspectable fail-safe runtime safety policy with paper/live/order/private endpoint flags disabled by default.
- Test-only auth bypass limited to `API_RUNTIME_MODE=test`.

UAT0.2 closed or partially closed these P1 items:

- Adapter-level private/signed/order runtime-policy enforcement is implemented and tested before transport.
- Hyperliquid selected-venue future-UAT1 read-only allowlist exists as a testable policy artifact.
- Representative redaction for bearer tokens, API keys, secrets, passwords, and DB URLs is tested.

UAT0.3 closes the UAT1 preflight baseline:

- Top-20 source/intersection resolver policy exists and is fixture-tested.
- Hyperliquid public read-only info types are allowlisted for future UAT1.
- Runtime drawdown monitor policy/model exists and is fixture-tested from caller-supplied observed equity.
- UAT1 public read-only connectivity preflight was satisfied with no private endpoints, no signed endpoints, no order endpoints, no API keys, no paper trading, no live trading, and no order submission. UAT1 is now complete.

UAT1 is now complete:

- Explicit UAT1 public-read-only mode was required before network calls.
- Hyperliquid public read-only info types were verified with HTTP 200 and usable response shape.
- CoinGecko public markets data was fetched without API keys as the top-volume source.
- The generated UAT1 report includes 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets.
- No private, signed, or order endpoints were called; no strategy decisions, order intents, submitted orders, paper trades, live trades, evidence packs, or Money Flow rule changes were created.

UAT1.1 is now complete:

- Shadow signal audit records exist for no-trade / would-trade / risk-block explainability.
- Operator-visible shadow drawdown state exists and is clearly not live-account drawdown.
- UAT1 universe snapshot loading is available for UAT2.
- Representative structured API-error/log redaction verification exists.
- No UAT2 loop, strategy decisions, order intents, submitted orders, paper/live behavior, evidence packs, exchange calls, private/signed/order endpoints, or Money Flow rule changes were created.

UAT2 is now complete:

- Explicit UAT2 shadow mode and public-read-only network flags were required.
- The UAT1 universe snapshot was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- UAT2 produced 45 shadow audit records: 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked`.
- ETH `sleeve_1h` produced `no_trade` with `macd_not_constructive`.
- `next_candle_open` and `next_candle_close` were represented; `same_candle_close_research_only` remained research-only.
- Shadow drawdown was visible as `shadow_simulated_drawdown` / `not_live_account_drawdown`, with no PnL simulation and no live account equity implication.
- No private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

UAT2.1 is now complete:

- The static dashboard has a `UAT2 Shadow Run` tab sourced from `docs/uat2_shadow_strategy_top20_observation_summary.json`.
- It displays UAT2 summary cards, a filterable 45-record shadow signal matrix, would-open inspection, no-trade reason breakdowns, ETH `sleeve_1h` candidate truth, timing assumptions, not-live-account shadow drawdown, no-artifact boundary flags, and UAT3 blockers.
- At that point, UAT3.1 actual sandbox order submission remained blocked; the dashboard adds no active approval action and cannot enable orders.
- No private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

UAT3.0 is now complete:

- Initial sandbox-order scope is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- Founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- Dashboard UAT view includes an informational UAT3.0 design/readiness panel.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.1 is now complete:

- Fail-closed sandbox runtime policy exists and defaults sandbox submission, private endpoints, live endpoint access, paper/live trading, and generic exchange order submission to disabled.
- Sandbox artifact label validation exists and fails missing/unsafe sandbox/testnet/not-live/not-paper labels.
- Future UAT3.1 actual-submission approval wording now requires a one-attempt sandbox/testnet approval with exact venue, environment, symbol, component, max size/count, order type, time window, sandbox account, kill switch, and lifecycle scope.
- Approval scope validator, sandbox risk gate evaluator, sandbox drawdown feed fixture, and submit-lease duplicate-prevention fixture are implemented and fixture-tested.
- Dashboard UAT view shows fixture/readiness status.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.2 is now complete:

- Sandbox risk gates propagate all `SandboxRuntimePolicy` blockers into risk/preflight reason codes instead of silently ignoring non-mode blockers.
- Approval scope, risk limits, risk requests, and drawdown fixtures reject non-positive or invalid sandbox numeric values with explicit reason codes.
- A unified fixture-only dry-run sandbox gate preflight evaluates runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder/operator actual-submission approval, and artifact-label persistence status.
- The dry-run result reports that it creates no order intent, submitted order, executable approval, or exchange call.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.3 is now complete:

- Sandbox artifact label boundary helpers cover persistence, API serialization, dashboard display, and report generation.
- A dry-run executable gate service wires runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks into one side-effect-free path.
- Runtime semantics now explicitly separate broad/global exchange order submission from sandbox/testnet-only submission.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.4 is now complete:

- Private read-only sandbox account policy and endpoint categories distinguish account/balance/position/equity reads from order submission/cancel/amend/retry paths.
- Credential approval and credential-boundary validation require the exact founder/operator private-read-only approval text before any sandbox/testnet private read-only credential use.
- Credential redaction covers representative authorization headers, bearer tokens, API keys, secrets, passwords, private keys, and DB URLs.
- Sandbox account drawdown feed modeling can represent unavailable fields explicitly and can report `sandbox_drawdown_feed_missing`, `sandbox_drawdown_feed_fixture_only`, `sandbox_drawdown_feed_private_read_only_verified`, and `sandbox_drawdown_feed_live_fed_verified`.
- The required private-read-only credential approval was not present, so no credentials were used and no private endpoints were called.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.5 is now complete:

- The exact founder/operator approval for sandbox/testnet private read-only credential use is present and validated for account-state/drawdown-feed verification only.
- Local sandbox/testnet credential environment variables are present and the base URL is verified as Hyperliquid testnet.
- Sandbox/testnet base URL validation blocks live Hyperliquid endpoints and requires sandbox/testnet host identity before any private read-only path can proceed.
- One Hyperliquid testnet read-only account-state request returned HTTP 200 and produced a `sandbox_account` / `not_live_account` drawdown feed with `sandbox_drawdown_feed_live_fed_verified`.
- No API key/private key was sent; no order/cancel/amend/retry endpoint was called.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.0.6 is now complete:

- A non-persistent `UAT3SandboxSubmissionPlan` exists for the future ETH `sleeve_1h` sandbox path and records all dry-run no-artifact/no-exchange side-effect flags as false.
- `UAT3SandboxSubmitDryRunService` composes runtime policy, founder actual-submission approval status, sandbox artifact-label boundary validation, approval scope validation, live-fed sandbox drawdown status, sandbox risk gates, submit-lease duplicate-prevention checks, and adapter endpoint classification.
- The dry-run consumes the UAT3.0.5 `sandbox_drawdown_feed_live_fed_verified` status and blocks if drawdown is missing, stale, fixture-only, threshold-breached, or not labeled `not_live_account`.
- The future endpoint category is classified as `sandbox_order_submission`, but transport invocation remains forbidden in UAT3.0.6 and `calls_exchange=false`.
- UAT3.1 was blocked at the time because founder/operator actual-submission approval was still required and actual transport enablement belonged to a later explicit UAT3.1 phase.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

UAT3.1 is now complete:

- Exact founder/operator approval for one sandbox/testnet order submission attempt was present and validated.
- The UAT3.1 runner used sandbox/testnet endpoint validation, live-fed sandbox drawdown, approval scope validation, sandbox risk gates, submit-lease duplicate prevention, sandbox artifact labels, endpoint classification, and post-only/nonmarketable order-shape checks before transport.
- Exactly one Hyperliquid testnet ETH post-only limit order attempt under 10 USDC notional was made.
- Hyperliquid rejected the attempt with a sanitized user/API-wallet-not-found response.
- No cancel was required, reconciliation found no open order, and no unexpected fill occurred.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.

Remaining later blockers:

- UAT3.2 requires separate founder/operator approval before any additional sandbox order attempt.
- Sandbox account/API-wallet configuration should be reviewed before attempting accepted/open -> cancel lifecycle coverage, because UAT3.1 was rejected by venue user/API-wallet validation.
- Additional sandbox orders remain unapproved.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
