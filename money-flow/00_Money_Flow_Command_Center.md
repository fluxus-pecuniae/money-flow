# Money Flow Command Center

This is the canonical Obsidian command center for Money Flow agents and founder review.

## Current Truth

| Field | Current State |
| --- | --- |
| Current implemented milestone | `PT-RT1.1C` 24-hour probes-disabled runtime collection start on top of completed `PT-RT1.1B`, `PT-RT1.1A`, `PT-RT1`, `OB2.0`, and `EV-AUDIT1`; collection is running and evaluation is deferred to PT-RT1.1D after completion; no strategy candidate promoted |
| Current major track | Forward paper observation substrate after SV2.0.2 canonical baseline, SOR, MF-ORIG, EV-AUDIT1, and OB2.0 |
| Next recommended phase | Let `PT-RT1.1C` complete, then run `PT-RT1.1D` to evaluate ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`; PT-RT1.2 is blocked until that passes |
| UAT/PT status | UAT2 no-order shadow observation, UAT2.1 dashboard visualization, UAT3.0 sandbox-order design, UAT3.0.1 fixture/readiness hardening, UAT3.0.2 dry-run gate hardening, UAT3.0.3 dry-run executable gate wiring / label enforcement, UAT3.0.4 private read-only sandbox drawdown readiness, UAT3.0.5 sandbox/testnet private read-only drawdown verification, UAT3.0.6 sandbox submit path dry-run wiring, UAT3.1 first sandbox/testnet lifecycle probe, UAT3.2 fixed-key readiness preflight, UAT3.3 Hyperliquid account-targeting / precision hardening, UAT3.4 fixed-target sandbox routing ledger, UAT4.0 read-only chart cockpit, UAT4.1 exchange-style dashboard redesign, UAT4.2 live-market/paper-equity monitoring plus browser-side public testnet chart polling, PT0 TradingView charts / top-20 paper-sandbox runtime foundation, PT0.0.1 chart stability hotfix, PT0.0.2 historical replay cockpit, and PT0.0.3 historical data horizon / 1D replay support are complete |
| Paper trading | PT-RT1/PT-RT1.1A/PT-RT1.1B/PT-RT1.1C add synthetic paper-observation ledgers and runtime collection only. No strategy paper runtime is production-approved from EV-AUDIT1 or PT-RT1 evidence |
| Broader top-20 paper/sandbox | PT0 broader top-20 Hyperliquid-supported paper/sandbox scope is risk-gated and metadata-gated only. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. It is not production strategy approval |
| Live trading | Not approved |
| Additional exchange order submission | Live exchange order submission is not approved; sandbox/testnet routing remains risk-gated and default-disabled |
| Routing / SOR expansion | Deferred |
| Production Money Flow rules | Money Flow v1.2 adds `sleeve_1d`; existing 15m/1h/4h settings remain unchanged; EV-AUDIT1 changed no rules |
| Original source | Gerald Peters PDF is now present at `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf`; current v1.2 is derivative, MF-ORIG is the source-faithful evidence track |

EV-AUDIT1 is complete as audit-only founder review. It inventories Money Flow v1.2 canonical SV2.0.2 evidence, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and STRAT-EV1 plan-only status; audits data integrity and methodology; explains biggest winners, biggest losers, losing streaks, regime/control-pocket attribution, and P0/P1/P2/P3 issues. The audit promotes no clean strategy candidate. `avoid_low_rolling_range_50` is the best SOR founder-review candidate but still fails drawdown/control-pocket gates, and `mf_orig_1d_stage2_breakout_resistance_full_equity` is the best MF-ORIG full-equity review lane but is not a production candidate. The backtest/evidence estate is good enough for visual review and hypothesis filtering only. EV-AUDIT1 recommended real-time paper observation under separate scope; PT-RT1 is now implemented as substrate only and still does not approve paper runtime, production rule changes, live trading, or order submission.

PT-RT1 is implemented as a forward-observation substrate. The strategy-truth lane is Hyperliquid public mainnet market data only, with fully closed candle gating, indicator computation that does not default missing values to zero, duplicate synthetic-signal prevention, and independent synthetic 10,000 USDC ledgers. PT-RT1.1A expands the lab before runtime collection to exactly 10 lanes: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, `avoid_low_rolling_range_50`, `mf_orig_stage_filter_only_full_equity`, `mf_orig_stage2_pullback_reclaim_full_equity`, `mf_orig_1d_stage2_5_20_crossover_full_equity`, `mf_orig_1d_stage2_breakout_resistance_full_equity`, `wildcard_btc_regime_guard`, `wildcard_multi_timeframe_alignment`, and `wildcard_volatility_expansion_breakout`. It also adds founder-requested scanner symbols with requested/resolved visibility, TRON->TRX and PEPE->kPEPE alias truth, PEPE/kPEPE and SHIB/kSHIB unit-semantics blocks, OKB support-confirmation blocking, POL/MATIC delisting protection, and dashboard lane/wildcard diagnostics. PT-RT1.1B adds the public-mainnet connector and runtime command, runs a bounded public-mainnet smoke cycle, verifies `meta` and `allMids` connectivity, resolves 25 requested watchlist rows with 23 eligible and 2 blocked, records 80 bounded paper decision events, and exposes connection status in the dashboard. PT-RT1.1C produced ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/`; the local artifact set currently contains about 479k decision rows, 0 trade rows, and a latest summary timestamp of `2026-05-15T22:22:12Z`. PT-RT1 is not an always-on hosted service: new signal generation requires starting the runtime and keeping that process and machine awake/networked for the chosen session duration. The Paper Observation dashboard can now be served by `scripts/run_dashboard_control_server.py` for a localhost-only Start Run / Stop Run helper that launches allowlisted 5-minute, 1-hour, 6-hour, or 24-hour probes-disabled public-mainnet runs through Mac `caffeinate`; the helper always forces `--disable-testnet-probes` and `--public-mainnet-only`. Static dashboard serving still works for review, but runtime controls remain unavailable without that local control API. The Paper Observation dashboard also browser-polls Hyperliquid public mainnet `allMids` every 1 second for a compact symbol/mid/health watchlist and selected-pair `candleSnapshot` for a live TradingView chart; health is `unhealthy` when the latest tick is missing or stale for more than 2 minutes. The adjacent Signal Generation panel lists recorded synthetic `paper_opened` intended-entry decisions from the PT-RT1 decision stream. This is display/observation only and uses no private/signed/order/API-key path. The Hyperliquid testnet plumbing lane is separate, disabled and kill-switched by default, exact-approval gated, capped under 10 USDC, post-only `Alo`, cancel/reconcile required, and never updates strategy paper PnL. PT-RT1.1D evaluates the completed artifacts; PT-RT1.2 remains blocked until a real probes-disabled dry run passes. PT-RT1/PT-RT1.1/PT-RT1.1A/PT-RT1.1B/PT-RT1.1C do not approve production rules, strategy paper-runtime promotion, live trading, live or testnet orders, private/signed/order endpoints from strategy truth, API-key use, SOR/fanout/CBBO, or testnet data as strategy truth.

MF-ORIG-EV2 is complete as an evidence-only multi-timeframe expansion, including the founder-requested full-equity comparison regeneration. It preserves the MF-ORIG-EV1.1 event-ledger accounting and peak-to-trough drawdown hotpatch, then generates 288 ignored evidence-pack directories and 612 ignored dashboard chart-data files across four source-faithful 1% risk-sizing Original Money Flow hypotheses plus four full-equity/notional counterparts, BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and both next-candle fill assumptions. Historical Replay and the Evidence Run Ledger now auto-load all eight MF-ORIG-EV2 strategy rows when local chart-data JSON exists. `1d` remains source-primary, `4h`/`1h` are fractal adaptations, and `15m` is a stress-test adaptation. Candidate gates were re-run against Money Flow v1.2 canonical SV2.0.2 baseline rows; no original hypothesis is production-approved and no paper/live behavior is authorized. MF-ORIG-EV1.1 remains the accounting/drawdown hotpatch baseline. The PDF is now stored in `money-flow/90 Reference/`, so future MF-ORIG work can perform source-exact reconciliation without changing current evidence numbers.

SOR-EV3 is complete. The founder-selected `avoid_sideways_low_volatility` family was tested as focused true-forward replay against canonical SV2.0.2 DB-imported pack paths only. Baseline parity passed for all 72 canonical scenarios. ATR-percentile, flat SMA20/EMA10 trend, rolling-range compression, MACD-flat chop, and conservative combined blockers were evaluated with blocked-entry attribution, loss-concentration reporting, avoided-loser / missed-winner counts, and control-pocket impact. Blocked open signals are separated from matched canonical baseline trades with PnL attribution. No variant was promoted and production Money Flow rules remain unchanged. The SOR-EV3 label follow-up now separates strict candidate promotion from founder-review labels: `avoid_low_rolling_range_20` is `promising_control_pocket_risk`, `avoid_low_rolling_range_50` is `promising_high_pnl_control_risk`, and hard rejection is limited to `avoid_low_atr_percentile_30` as `rejected_negative_aggregate`. `promising_*` labels are review context only, not approval. The Historical Replay regeneration follow-up now writes full research-only replays for `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` into the ignored SV2.0.2 chart-data files across 9 supported symbols, 4 timeframes, and both fill assumptions. SOR-EV2.2 is complete. Evidence Lab now exposes baseline-vs-variant overlay controls, baseline SV2.0.2 entry/exit/forced-close markers, linkable SOR-EV2 adverse-candle and stop-context markers where exact timestamps exist, worst-trade focus mode, selected-trade inspector, control-pocket view, methodology/date-filter warnings, explicit unavailable states, and a focused SOR-EV3 founder-candidate section. SOR-EV2.1 is complete and remains the table/panel review baseline; its SOR-EV1/SOR-EV2 Variant Summary Matrix now separates promising, mixed, deferred, no-op, diagnostic-only, and hard-rejected rows instead of flattening every non-candidate into rejected. SOR-EV2 is complete. Baseline parity passed for all 72 canonical SV2.0.2 scenarios, variants were replayed from persisted candle truth, rejected-signal and large-loss candle context is available, and no variant was promoted. SOR-EV1 is complete and remains the loss-anatomy baseline. It uses only the canonical SV2.0.2 DB-imported evidence packs to explain largest losses, adverse-move/late-entry patterns, fixed-stop overlay diagnostics, deferred true-replay variants, and control-pocket impact. It promotes no production candidate and changes no Money Flow rules. SV2.0.2 is complete and was regenerated on 2026-05-12. It imports normalized Hyperliquid public mainnet candles through the hardened Strategy Validation candle importer into the intended migrated `money_flow` DB, writes 36 per-symbol/per-timeframe canonical SV2.0.2 campaign configs for `15m`, `1h`, `4h`, and `1d`, and generates ignored canonical evidence packs for Money Flow v1.2 using the existing evidence-pack machinery. The regenerated packs use fully closed timeframe end-boundaries and each supported pair/timeframe's full available imported window. Supported canonical evidence symbols are BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, and AVAX; requested SHIB is represented as `kSHIB` but deferred from canonical evidence because unit semantics are not clean enough. SV2.0.1 is complete and remains the evidence-truth hotfix baseline: compact rows are noncanonical, close slots are canonical, import/staging truth is separated, runtime sleeve allocations are 0.25 each, and missing EMA/RSI/MACD inputs are invalid rather than zero. SV2.0 is complete: Money Flow v1.2 includes `sleeve_1d` as a real first-class sleeve while preserving existing 15m/1h/4h settings. `4h` and `1D` reach the Jan 2025 target; `15m` and `1h` carry `hyperliquid_public_5000_candle_limit`. UAT remains plumbing and behavior validation. Strategy evidence uses Hyperliquid public mainnet candles; Hyperliquid testnet remains sandbox execution plumbing only. Live trading is not approved. Real-capital trading is not approved. Live exchange order submission is not approved.

SV2.1 founder-approved 1D period evidence is complete as a separate research refresh and now has Historical Replay artifacts for all 10 PT-RT1 paper-observation lanes. The earlier broad active-metadata run was rejected for founder review and removed from local generated outputs. The current run used Hyperliquid public mainnet `meta` and `candleSnapshot` only, targeted the founder-approved requested/resolved universe, mapped TRON to TRX, excluded PEPE/kPEPE and OKB by resolver policy, imported available 1D candles back to 2024-01-01 where available, and generated 90 ignored baseline period packs for 2024, 2025, YTD, and ALL. The dashboard builder then generated 1800 ignored selected Historical Replay chart/trade JSON files and 810 ignored evidence-only candidate/reference/wildcard pack directories across all 9 non-baseline PT-RT1 lanes. ASTER and TRUMP have no 2024 period packs because public 1D candles do not cover that period. It broadens founder-review data for 1D only; it does not change Money Flow rules, supersede SV2.0.2 multi-timeframe evidence, approve a variant, approve paper/live, submit orders, or call private/signed/order endpoints.

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
| Execution status | UAT3.4 recorded one approved fixed-target Hyperliquid testnet ETH attempt: accepted/open, canceled successfully, reconciled to no open order; PT0 visualizes that ledger, shadow records, public-read-only monitor rows, TradingView Lightweight Charts, and internal paper-equity state; PT0.0.2/PT0.0.3 visualize historical strategy replay separately from sandbox execution plumbing; live exchange order submission is not approved |

This candidate is not a production strategy and not live-trading approval. PT0 separately approves Hyperliquid testnet/sandbox paper trading and broader top-20 paper/sandbox scope under gates only; it does not prove strategy profitability.

## UAT Observation Universe

Future UAT observation is not ETH-only. UAT1/UAT2 should use a top 20 high-volume crypto asset universe supported by the selected UAT venue/environment to validate platform behavior, no-trade reasoning, rejected-signal behavior, symbol mapping, risk visibility, and operator explainability. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## What Money Flow Is Today

Money Flow is a controlled trading-system substrate plus Strategy Validation research platform. The platform has strategy, planning, risk, routing-assessment, approval-gated action hooks, execution-readiness, submitted-order lifecycle, and operator observability foundations. The current business focus is not more routing scope; it is making the strongest observed Money Flow scenario safe to observe in UAT.

## Track Map

- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Phase Timeline|Phase Timeline]]
- [[00 Maps/Strategy Family Map|Strategy Family Map]]
- [[00 Maps/Evidence and Backtesting Map|Evidence and Backtesting Map]]
- [[00 Maps/Data Source and Market Data Map|Data Source and Market Data Map]]
- [[00 Maps/Dashboard and UI Map|Dashboard and UI Map]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[00 Maps/Paper Observation Roadmap|Paper Observation Roadmap]]
- [[00 Maps/Platform Architecture Map|Platform Architecture Map]]
- [[10 Strategy/Strategy Status Register|Strategy Status Register]]
- [[10 Strategy/Original Money Flow Source Notes|Original Money Flow Source Notes]]
- [[20 Evidence/EV-AUDIT1 Summary|EV-AUDIT1 Summary]]

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
