# Current Phase

## Current Implemented Milestone

`UAT1.1` shadow signal audit, drawdown visibility, and redaction verification is complete.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named gaps were closed. UAT0.1 closes the P0 API auth/authz baseline and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verifies allowed public Hyperliquid endpoint behavior, fetches a no-key public top-volume source, and resolves the Hyperliquid-supported top-20 observation universe. UAT1.1 adds shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification.

SV1.18 is complete.

## Next Proposed Phase

`UAT2` shadow strategy run as no-order observation.

UAT2 shadow strategy run may proceed as a future no-order phase. UAT remains plumbing and behavior validation only. It is not paper trading, live trading, exchange order submission, routing expansion, or strategy optimization.

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

Future UAT2 shadow timing must compare:

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

Remaining later blockers:

- UAT3 needs sandbox/live account drawdown feed wiring.
- Existing approval gates and submit leases are useful but require UAT3 verification before sandbox orders.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
