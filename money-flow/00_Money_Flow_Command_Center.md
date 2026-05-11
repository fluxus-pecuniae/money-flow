# Money Flow Command Center

This is the canonical Obsidian command center for Money Flow agents and founder review.

## Current Truth

| Field | Current State |
| --- | --- |
| Current implemented milestone | `PT0.0.2` Historical Strategy Replay Cockpit complete |
| Current major track | Strategy Validation evidence cycle is closed |
| Next proposed phase | `PT0.0.3` historical replay playback / market-structure inspector may be scoped; `PT0.1` supervised top-20 paper/sandbox runtime week remains future work using trusted market data; `UAT3.5` additional sandbox routing lifecycle tests are blocked by incomplete UAT-universe precision validation |
| UAT/PT status | UAT2 no-order shadow observation, UAT2.1 dashboard visualization, UAT3.0 sandbox-order design, UAT3.0.1 fixture/readiness hardening, UAT3.0.2 dry-run gate hardening, UAT3.0.3 dry-run executable gate wiring / label enforcement, UAT3.0.4 private read-only sandbox drawdown readiness, UAT3.0.5 sandbox/testnet private read-only drawdown verification, UAT3.0.6 sandbox submit path dry-run wiring, UAT3.1 first sandbox/testnet lifecycle probe, UAT3.2 fixed-key readiness preflight, UAT3.3 Hyperliquid account-targeting / precision hardening, UAT3.4 fixed-target sandbox routing ledger, UAT4.0 read-only chart cockpit, UAT4.1 exchange-style dashboard redesign, UAT4.2 live-market/paper-equity monitoring plus browser-side public testnet chart polling, PT0 TradingView charts / top-20 paper-sandbox runtime foundation, PT0.0.1 chart stability hotfix, and PT0.0.2 historical replay cockpit are complete |
| Paper trading | PAPER TRADING IS APPROVED. Hyperliquid testnet/sandbox only |
| Broader top-20 paper/sandbox | BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Risk-gated and metadata-gated only |
| Live trading | Not approved |
| Additional exchange order submission | Live exchange order submission is not approved; sandbox/testnet routing remains risk-gated and default-disabled |
| Routing / SOR expansion | Deferred |
| Production Money Flow rules | Unchanged |

SV1.18 is complete. UAT0 is complete as a safety/security/runtime audit. UAT0.1 closes the P0 API auth/authz baseline for sensitive `/api/v1` routes and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds a fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and a fixture-tested runtime drawdown monitor model. UAT1 verified explicit public-read-only Hyperliquid endpoint behavior, fetched a no-key public CoinGecko top-volume source, intersected it with Hyperliquid USDC perpetual metadata, and kept all included assets observation-only. UAT1.1 added model/report-only shadow signal audit records, operator-visible shadow drawdown, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 no-order shadow observation is complete; it evaluated the UAT1 Hyperliquid top-20-supported universe using only public read-only candles. UAT2.1 adds a dashboard UAT2 Shadow Run tab and founder-readiness pack so the UAT2 summary is visually reviewable without enabling approvals or orders. UAT3.0-UAT3.0.6 hardened sandbox/testnet gates. UAT3.1 made one approved rejected testnet lifecycle attempt; UAT3.2 blocked before order transport; UAT3.3 fixed account targeting and precision and later verified an accepted/open -> cancel -> reconcile follow-up. UAT3.4 is complete: the Hyperliquid testnet ETH route is now `fixed_target_hyperliquid_testnet_eth`, normal user mode omits `vaultAddress`, standard perp clearinghouse equity is selected, unified/portfolio USDC fallback remains implemented/tested, one approved UAT3.4 order was accepted/open then canceled successfully, reconciliation found no open order, and the dashboard shows a routed-order ledger without controls. UAT4.0 is complete: the static dashboard added a read-only UAT Chart Cockpit. UAT4.1 is complete: that cockpit is rebuilt as an exchange-style workstation with compact top bar, persistent safety banner, observation-only left market rail, central chart cockpit, right order-book/market/signal/risk rail, bottom blotter tabs, and canonical dashboard design system at `apps/dashboard/DESIGN.md`. UAT4.2 is complete: the dashboard now loads public-read-only monitor summary data, deterministic indicators, paper-observation markers, a 60-second sandbox private-read-only balance polling policy, an internal 10,000 USDC paper-equity ledger, and browser-side Hyperliquid testnet public chart polling every 15 seconds for `allMids` and `candleSnapshot`. PT0 is complete: PAPER TRADING IS APPROVED for Hyperliquid testnet/sandbox only, BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED under metadata/precision/risk gates, the dashboard now uses the official local TradingView Lightweight Charts bundle, the internal paper-equity ledger starts at 10,000 USDC, and sandbox routing remains default-disabled by `PT0_SANDBOX_ORDER_ROUTING_ENABLED=false`. PT0.0.1 is complete: the founder-reported TradingView chart vertical-growth/page-scroll P0 is fixed by bounding chart height, containing chart parents, reusing existing chart/series handles across 15-second refreshes, removing the autosize feedback-loop risk, limiting `fitContent()` to new symbol/timeframe initialization, and adding live-polling disable query flags for local JSON fallback. PT0.0.2 is complete: the dashboard now has a Historical Replay cockpit using historical public candle replay data, not Hyperliquid testnet prices, as Money Flow strategy truth for BTC/ETH/SOL x 15m/1h/4h, with TradingView candles, entry/exit markers, trade inspector, dynamic 10,000 USDC equity, comparison table, and a separate sandbox execution ledger. UAT3.1-PT0.0.2 created no production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, live real-capital behavior, smart routing/SOR/fanout, Money Flow rule change, evidence pack, live endpoint use, private order dashboard call, exchange API-key use, dashboard order controls, or unapproved repeated order. UAT remains plumbing and behavior validation. The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline. Live trading is not approved. Real-capital trading is not approved. Live exchange order submission is not approved.

## Frozen UAT Observation Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Scope |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Component | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow first |
| Execution status | UAT3.4 recorded one approved fixed-target Hyperliquid testnet ETH attempt: accepted/open, canceled successfully, reconciled to no open order; PT0 visualizes that ledger, shadow records, public-read-only monitor rows, TradingView Lightweight Charts, and internal paper-equity state; PT0.0.2 visualizes historical strategy replay separately from sandbox execution plumbing; live exchange order submission is not approved |

This candidate is not a production strategy and not live-trading approval. PT0 separately approves Hyperliquid testnet/sandbox paper trading and broader top-20 paper/sandbox scope under gates only; it does not prove strategy profitability.

## UAT Observation Universe

Future UAT observation is not ETH-only. UAT1/UAT2 should use a top 20 high-volume crypto asset universe supported by the selected UAT venue/environment to validate platform behavior, no-trade reasoning, rejected-signal behavior, symbol mapping, risk visibility, and operator explainability. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## What Money Flow Is Today

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform. The platform has strategy, planning, risk, routing-assessment, approval-gated action hooks, execution-readiness, submitted-order lifecycle, and operator observability foundations. The current business focus is not more routing scope; it is making the strongest observed Money Flow scenario safe to observe in UAT.

## Track Map

- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Phase Timeline|Phase Timeline]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[00 Maps/Platform Architecture Map|Platform Architecture Map]]

## Strategy Validation Closeout

SV1.18 closed the current Hyperliquid public-candle evidence cycle. It established:

- ETH `sleeve_1h` baseline is the strongest observed candidate.
- 15m, 4h, BTC/SOL 1h, lower-RSI variants, market-structure variants, and cross-venue candidates are excluded from current UAT scope.
- Current evidence is useful for UAT planning, but it does not prove edge.
- Strategy Validation did not model funding, liquidation, production margin, order-book fills, partial fills, latency, outages, or live reject/reconcile behavior.

Read [[00 Maps/Strategy Validation Map|Strategy Validation Map]] and [[30 Strategy/SV Evidence Closeout|SV Evidence Closeout]] before interpreting SV results.

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 Result

UAT0 initially found UAT1 blocked. UAT0.1 closed the P0 API authentication/authorization and central runtime-policy baseline:

- Sensitive `/api/v1` routes require scoped bearer authentication.
- Administrative consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes.
- Test auth bypass is limited to `API_RUNTIME_MODE=test`.
- `RuntimeSafetyPolicy` defaults paper trading, live trading, exchange order submission, and private exchange endpoints to disabled.

UAT0.2 closed or partially closed the next safety layer:

- Adapter private/signed/order helpers block before transport when runtime policy disables them.
- Hyperliquid has a testable future-UAT1 read-only allowlist artifact.
- Representative bearer/API-key/secret/password/DB URL redaction is tested.
- Adapter-helper error messages redact obvious secrets before logging/raising.

UAT0.3 closes the UAT1 preflight baseline:

- Top-20 source/intersection resolver policy exists and is fixture-tested.
- Hyperliquid public read-only info types are allowlisted for future UAT1: `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- Runtime drawdown monitor policy/model exists and is fixture-tested from caller-supplied observed equity.
- UAT1 public read-only connectivity preflight was satisfied and UAT1 has now completed under strict constraints.

UAT3.1 later used the UAT3.0.6 gate chain for one approved sandbox/testnet lifecycle probe. UAT3.2 later verified separate approval but blocked before order transport because sandbox account/API-wallet readiness still failed. UAT3.3 later fixed Hyperliquid account-targeting semantics and ETH precision formatting, then a founder-approved follow-up verified accepted/open -> cancel -> reconcile. UAT3.4 operationalizes that route as a fixed-target sandbox routing pipeline and routed-order ledger. Additional sandbox order attempts still require separate explicit approval and must remain sandbox/testnet only.

## UAT1 / UAT1.1 Result

UAT1 public read-only connectivity is complete:

- Explicit UAT1 public-read-only network mode was required before network access.
- Hyperliquid public `info` endpoint behavior was verified for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- CoinGecko public markets data was used as a no-key top-volume source.
- The top-20 source list resolved to 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets in the generated UAT1 report.
- No API keys, private endpoints, signed endpoints, order endpoints, order submissions, paper/live behavior, Money Flow live strategy evaluation, evidence packs, or live artifacts were used or created.

UAT1.1 shadow readiness is complete:

- Model/report-only shadow signal audit records exist for future no-trade / would-trade / risk-block inspection.
- Operator-visible shadow drawdown state exists and is labeled `shadow_simulated_drawdown` / `not_live_account_drawdown`.
- UAT1 universe snapshot loading is available for UAT2.
- Representative API-error and structured-log redaction verification exists.
- UAT2 shadow strategy run was cleared as a future no-order phase.

UAT2 shadow observation is complete:

- Bounded UAT2 shadow mode required explicit no-order/public-read-only flags.
- The UAT1 universe snapshot was evaluated for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- UAT2 created 45 shadow audit records, with 11 `would_open` and 34 `no_trade` records.
- ETH `sleeve_1h` produced `no_trade` with `macd_not_constructive`.
- Shadow drawdown was labeled `shadow_simulated_drawdown` / `not_live_account_drawdown`; no PnL or live account equity was implied.
- No API keys, private endpoints, signed endpoints, order endpoints, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were used or created.
- At that point, UAT3.1 actual sandbox order submission remained blocked until explicit founder/operator approval and sandbox runtime/drawdown/approval/submit-lease/risk/artifact-labeling prerequisites are implemented and test-covered.

UAT2.1 dashboard visualization is complete:

- The static dashboard has a `UAT2 Shadow Run` tab sourced from `docs/uat2_shadow_strategy_top20_observation_summary.json`.
- The tab shows summary cards, filterable shadow signal matrix, would-open records, no-trade reason breakdowns, ETH `sleeve_1h` candidate status, timing assumptions, not-live-account shadow drawdown, no-artifact boundary flags, and UAT3 blockers.
- The UAT3 readiness panel is informational only and says UAT3 is blocked.
- No approval action, order intent, submitted order, exchange call, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0 sandbox order design is complete:

- The future initial sandbox subset is Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- The founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- The dashboard UAT view includes an informational UAT3.0 design/readiness panel.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete:

- Fail-closed `SandboxRuntimePolicy` exists and is fixture-tested.
- Sandbox artifact label validation exists and fails unsafe/missing labels.
- Future UAT3.1 actual-submission approval wording now separates design approval from one sandbox/testnet order-attempt approval.
- Approval scope validation, sandbox risk gate evaluation, sandbox drawdown feed fixtures, and submit-lease duplicate-prevention fixtures are implemented and tested.
- Dashboard UAT view shows fixture/readiness status.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0.2 sandbox gate integration dry-run / policy hardening is complete:

- Sandbox risk gates now propagate every `SandboxRuntimePolicy` blocker into risk/preflight reason codes.
- Non-positive approval quantities, risk limits, risk request notionals, drawdown percentages, and drawdown thresholds are explicitly rejected.
- `evaluate_uat3_sandbox_submission_preflight` combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status into one fixture-only dry-run result.
- At that point, UAT3.1 actual sandbox order submission remained blocked by missing founder actual-submission approval, live-fed sandbox drawdown, real sandbox submit path wiring, executable approval/risk wiring, submit-lease integration verification, and persistence-level sandbox artifact-label enforcement.
- No order intent, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0.3 sandbox gate wiring / label-enforcement hardening is complete:

- Sandbox artifact label boundary helpers now cover persistence, API serialization, dashboard display, and report generation.
- A dry-run executable gate service composes runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks.
- Runtime semantics distinguish broad/global exchange order submission from sandbox/testnet-only submission.
- At that point, UAT3.1 actual sandbox order submission remained blocked by missing founder actual-submission approval, live-fed sandbox drawdown, real sandbox submit path wiring, executable approval/risk wiring to persistence/submit, and submit-lease integration verification.
- No order intent, prepared order, submitted order, executable approval, private/signed/order endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0.4 sandbox private read-only drawdown readiness is complete:

- Private read-only sandbox account policy, credential approval/boundary validation, endpoint category separation, credential redaction, and sandbox account drawdown feed modeling exist.
- The exact founder/operator approval for sandbox/testnet private read-only credential use was not present, so no API keys were used and no private endpoints were called.
- Order submission, cancel, amend, retry, live endpoint access, paper trading, and live trading remain blocked.
- At that point, UAT3.1 actual sandbox order submission remained blocked by missing founder actual-submission approval, live-fed sandbox account drawdown, real sandbox submit path wiring, executable approval/risk wiring to persistence/submit, and submit-lease integration verification.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete:

- The exact founder/operator approval for private read-only sandbox/testnet credential use is present for account-state and drawdown-feed verification only.
- Local `HYPERLIQUID_UAT_SANDBOX_*` credential environment variables are present and the base URL is verified as Hyperliquid testnet.
- One Hyperliquid testnet read-only account-state request returned HTTP 200 and produced a not-live-account drawdown feed with `sandbox_drawdown_feed_live_fed_verified`.
- No API key/private key was sent; order submission, cancel, amend, retry, private order endpoints, live endpoint access, paper trading, and live trading remain blocked.
- At that point, UAT3.1 actual sandbox order submission remained blocked by missing actual-submission approval, real sandbox submit path wiring, executable approval/risk wiring to persistence/submit, and submit-lease integration verification.
- No order intent, prepared order, submitted order, executable approval, private endpoint call, order endpoint call, exchange API-key use, paper/live behavior, routing artifact, evidence pack, or Money Flow rule change was added.

UAT3.1 first sandbox/testnet lifecycle probe is complete:

- Exact founder/operator approval for one sandbox/testnet order submission attempt was present and validated.
- The UAT3.1 runner used the UAT3.0.6 gate chain, live-fed sandbox drawdown, sandbox/testnet endpoint validation, approval-scope validation, risk gates, submit-lease duplicate prevention, sandbox artifact labels, and nonmarketable/post-only ETH order-shape checks before the one order transport call.
- Exactly one Hyperliquid testnet ETH post-only limit order attempt under 10 USDC notional was made.
- Hyperliquid rejected the attempt with a sanitized user/API-wallet-not-found response; no cancel was required, reconciliation found no open order, and no unexpected fill occurred.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.
- UAT3.2 later verified separate founder/operator approval but blocked before order transport because the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient.

UAT3.2 fixed-key preflight / second sandbox lifecycle attempt is complete:

- Exact founder/operator approval for one second sandbox/testnet order submission attempt was present and validated.
- The runner verified Hyperliquid testnet endpoint identity, live-fed sandbox drawdown, approval scope, sandbox labels, submit-lease duplicate prevention, and fixed-target ETH post-only/nonmarketable order shape before any order-capable transport.
- Account/API-wallet readiness blocked because the testnet user/API wallet was not recognized/authorized and sandbox equity was insufficient for the tiny under-10-USDC order.
- Order attempt count was `0`; no order/cancel/amend/retry endpoint was called; cancel and reconciliation were not attempted because no order existed.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.
- UAT4.0 live UAT trading dashboard / chart cockpit is complete, and UAT4.1 rebuilt it as a read-only exchange-style workstation.
- UAT3.3 remains blocked until separate founder/operator approval plus recognized/authorized testnet user/API wallet and sufficient testnet equity are available.

Read [[00 Maps/UAT Roadmap|UAT Roadmap]] and [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]] before any UAT work.

## Required Agent Workflow

Before substantial work, read:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`
- this command center
- [[01_Current_Phase|Current Phase]]
- [[03_Decision_Log|Decision Log]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
- the current track map relevant to the task

Before editing overlapping files, update your own row in [[05_Agent_Coordination|Agent Coordination]]. After work, mark the row `done` or `blocked`.

Do not create duplicate command centers or competing current-phase notes.

## Repo Truth Sources

Repo operational truth remains in:

- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

Obsidian is strategic memory and coordination. It does not replace repo operational docs.
