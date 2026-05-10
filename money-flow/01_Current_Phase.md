# Current Phase

## Current Implemented Milestone

`UAT3.0` sandbox order design and readiness is complete.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named gaps were closed. UAT0.1 closes the P0 API auth/authz baseline and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verifies allowed public Hyperliquid endpoint behavior, fetches a no-key public top-volume source, and resolves the Hyperliquid-supported top-20 observation universe. UAT1.1 adds shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 completed a bounded no-order Money Flow shadow observation across the UAT1 Hyperliquid top-20-supported universe. UAT2.1 makes that UAT2 output visually reviewable in the static dashboard and adds an informational UAT3 blocked readiness panel. UAT3.0 defines the future sandbox-order scope, founder/operator approval template, sandbox runtime policy, sandbox drawdown feed requirements, lifecycle, artifact labeling, submit-lease, approval, and risk-gate requirements without enabling submission.

SV1.18 is complete.

## Next Proposed Phase

`UAT3.1` first approval-gated sandbox order remains blocked.

UAT3.1 may proceed only after explicit founder/operator approval for actual sandbox submission, sandbox runtime submission enablement, sandbox account drawdown feed wiring, UAT3 approval-scope verification, submit-lease/lifecycle verification, risk gate implementation, and sandbox artifact labeling. UAT remains plumbing and behavior validation only. It is not paper trading, live trading, unrestricted exchange order submission, routing expansion, or strategy optimization.

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
- Exchange order submission is not approved.
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
- UAT3.1 actual sandbox order submission remains blocked; the dashboard adds no active approval action and cannot enable orders.
- No private/signed/order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were created.

UAT3.0 is now complete:

- Initial sandbox-order scope is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- Founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- Dashboard UAT view includes an informational UAT3.0 design/readiness panel.
- UAT3.1 actual sandbox order submission remains blocked.
- No order intent, submitted order, executable approval, private/signed endpoint call, exchange API-key use, paper/live behavior, evidence pack, routing artifact, or Money Flow rule change was created.

Remaining later blockers:

- UAT3.1 needs explicit founder/operator approval for actual sandbox submission.
- UAT3.1 needs sandbox runtime submission enablement and sandbox-only private endpoint separation.
- UAT3.1 needs sandbox account drawdown feed wiring.
- Existing approval gates and submit leases are useful but require UAT3.1 verification before sandbox orders.
- Sandbox artifact labeling and risk gate implementation remain required before any actual sandbox order submission.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
