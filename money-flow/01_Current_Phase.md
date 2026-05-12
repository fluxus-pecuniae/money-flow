# Current Phase

## Current Implemented Milestone

`MF-ORIG-EV1.1` Original Money Flow accounting and drawdown hotpatch is complete. It quarantines pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions and regenerates the original Money Flow reconstruction reports with event-ledger accounting, single-counted entry fees and trim PnL, final closes on remaining quantity only, peak-to-trough realized and mark-to-market drawdown, an all-trade accounting invariant audit, and truthful baseline-positive 1d control-pocket filtering. Candidate gates were re-run and the strict conclusion did not change: all four original hypotheses remain `source_faithful_but_underperformed` because baseline-positive 1d control pockets were not preserved. MF-ORIG remains Strategy Validation-only and production Money Flow v1.2 remains unchanged. No original hypothesis is production-approved, paper-approved, or live-approved. `SOR-EV3` Founder-Selected Avoid Sideways / Low-Volatility Drilldown is complete. The `avoid_sideways_low_volatility` family was tested as focused true-forward replay against canonical SV2.0.2 DB-imported pack paths only. Baseline parity passed for all `72` canonical scenarios. ATR-percentile, flat SMA20/EMA10 trend, rolling-range compression, MACD-flat chop, and conservative combined blockers were evaluated with dynamic equity, explicit blocked-entry attribution, loss-concentration reporting, avoided-loser / missed-winner counts, and control-pocket impact. Blocked open signals are reported separately from matched canonical baseline trades with PnL attribution. No variant was promoted and production Money Flow rules remain unchanged. The SOR-EV3 founder-review label follow-up now shows `avoid_low_rolling_range_20` as `promising_control_pocket_risk`, `avoid_low_rolling_range_50` as `promising_high_pnl_control_risk`, and `avoid_low_atr_percentile_30` as the hard `rejected_negative_aggregate` row; these labels are review context only and not approval. The Historical Replay regeneration follow-up now adds `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` as research-only replay strategies across all 9 supported SV2.0.2 symbols, 4 timeframes, and both fill assumptions in the ignored local chart-data JSON. `SOR-EV2.2` Variant Chart Overlay + Founder Review Workflow is complete. Evidence Lab now has overlay controls, baseline SV2.0.2 entry/exit/forced-close markers, linkable SOR-EV2 adverse-candle and stop-context markers where exact timestamps exist, worst-trade focus mode, selected-trade inspector, control-pocket view, methodology/date-filter warnings, explicit unavailable states where the SOR bundles lack exact overlay data, and a focused SOR-EV3 founder-candidate section. `SOR-EV2.1` Evidence Lab / Variant Review dashboard is complete and remains the table/panel review baseline; its SOR-EV1/SOR-EV2 Variant Summary Matrix now uses founder-review labels to separate promising, mixed, deferred, no-op, diagnostic-only, and hard-rejected rows instead of flattening every non-candidate into rejected. `SOR-EV2` True-Forward Stop/Exit + Rejected-Signal Replay is complete. Baseline parity passed for all `72` canonical SV2.0.2 scenarios, stop/exit and entry variants were evaluated from persisted candle truth, large-loss candle context is now available, rejected-signal counts are reported, no variant was promoted, and production Money Flow rules remain unchanged. `SOR-EV1` Money Flow Loss Anatomy + Evidence-Only Variant Diagnostics is complete and remains the loss-anatomy baseline. `SV2.0.2` Hardened Candle DB Import + Canonical SV2 Evidence Pack Generation is complete. Normalized Hyperliquid public mainnet candles were imported through the hardened Strategy Validation candle importer into the intended migrated `money_flow` DB, and the 2026-05-12 regeneration produced 36 per-symbol/per-timeframe canonical SV2.0.2 campaign configs plus ignored canonical evidence packs for Money Flow v1.2. The regenerated packs use fully closed timeframe end-boundaries and each supported pair/timeframe's full available imported public-data window. Effective ends are `15m=2026-05-12T06:45:00Z`, `1h=2026-05-12T06:00:00Z`, `4h=2026-05-12T04:00:00Z`, and `1d=2026-05-12T00:00:00Z`. Supported canonical evidence symbols are BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, and AVAX; requested SHIB is represented as `kSHIB` but deferred from executable canonical evidence because unit semantics are not clean enough. Dynamic equity uses `10000` USDC per independent scenario, dataset-end open positions are force-closed explicitly, and compact replay rows remain noncanonical. `SV2.0.1` remains the evidence-truth hotfix: compact rows count entry fees at open, normalize Hyperliquid `.999Z` close timestamps to canonical slots, split fetched/normalized/staged data from DB-imported/canonical-evidence-ready data, set runtime sleeve allocations to `0.25` each, canonicalize internal `1d` while displaying `1D`, and treat missing EMA/RSI/MACD inputs as invalid instead of zero. `SV2.0` Money Flow 1D Sleeve + Expanded Historical Data Refresh + Evidence Rebuild is complete. Money Flow v1.2 includes `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, and the real `sleeve_1d`; existing 15m/1h/4h settings remain unchanged. Testnet market data is not strategy truth. PAPER TRADING IS APPROVED. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED.

SV1.18 closed the current Strategy Validation evidence cycle and froze exactly one evidence candidate. SV1.18.1 closed the remaining Obsidian coordination handoff gap. OB1.0 overhauled the Obsidian project brain. UAT0 audited safety/security/runtime readiness and blocked UAT1 until named gaps were closed. UAT0.1 closes the P0 API auth/authz baseline and adds an inspectable fail-safe runtime safety policy. UAT0.2 closes the adapter-level runtime-policy enforcement baseline, adds a Hyperliquid future-UAT1 read-only allowlist artifact, and strengthens representative redaction verification. UAT0.3 adds fixture-tested top-20 universe resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design. UAT1 verifies allowed public Hyperliquid endpoint behavior, fetches a no-key public top-volume source, and resolves the Hyperliquid-supported top-20 observation universe. UAT1.1 adds shadow signal audit records, operator-visible shadow drawdown state, UAT1 universe snapshot loading, and representative structured API-error/log redaction verification. UAT2 completed a bounded no-order Money Flow shadow observation across the UAT1 Hyperliquid top-20-supported universe. UAT2.1 makes that UAT2 output visually reviewable in the static dashboard and adds an informational UAT3 blocked readiness panel. UAT3.0 through UAT3.0.6 define and dry-run the sandbox/testnet gate chain. UAT3.1 is complete as a rejected one-shot Hyperliquid testnet ETH lifecycle probe. UAT3.2 is complete as a blocked fixed-key preflight. UAT3.3 fixed Hyperliquid account targeting and ETH precision, and a later founder-approved follow-up verified accepted/open -> cancel -> reconcile on Hyperliquid testnet with normal user mode and `vaultAddress` omitted. UAT3.4 operationalizes that success as a fixed-target sandbox routing pipeline and routed-order ledger: the active route is Hyperliquid testnet ETH only, selected equity source is `standard_perp_clearinghouse`, unified/portfolio spot-clearinghouse USDC fallback remains implemented/tested, one approved UAT3.4 order was accepted/open and canceled successfully, reconciliation found no open order, and the dashboard displays routed-order ledger truth without order controls. UAT4.0 added the read-only dashboard/chart cockpit. UAT4.1 rebuilt it into an exchange-style workstation with compact top bar, persistent safety banner, observation-only market rail, central chart cockpit, right order-book/market/signal/risk rail, bottom blotter tabs, and canonical design doc at `apps/dashboard/DESIGN.md`. UAT4.2 adds read-only public-market monitor summary data, deterministic indicators, paper-observation markers, a 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger without adding order controls or order endpoints. PT0 adds an official local TradingView Lightweight Charts bundle, live public testnet candle rendering, top-20 paper/sandbox universe eligibility, deterministic paper scanner records, an internal 10,000 USDC paper-equity ledger, current-equity sizing policy, 60-second sandbox private-read-only polling policy, and default-disabled risk-gated sandbox routing foundation. PT0.0.1 fixes the founder-reported TradingView chart growth/page-scroll P0 by bounding chart height, containing parent layout, updating existing chart/series handles across refreshes, removing the autosize feedback-loop risk, limiting `fitContent()` to new symbol/timeframe initialization, and adding emergency live-polling disable query flags. The follow-up dashboard chart correctness hotfix uses Playwright to verify BTC/SOL public candles are mixed red/green, prevents non-selected symbols from displaying synthetic local fallback candles as live chart data, and adds explicit price readouts beside the TradingView chart. PT0.0.2 adds a Historical Replay cockpit using historical public candle replay data, not Hyperliquid testnet prices, as Money Flow strategy truth for BTC/ETH/SOL x 15m/1h/4h, with TradingView historical candles, entry/exit markers, trade inspector, dynamic 10,000 USDC equity, BTC/ETH/SOL comparison, separate sandbox execution plumbing visibility, and a research-only MACD-removed replay strategy selector that does not change production rules.

PT0.0.3 added 1D historical replay support and Jan 2025 data-horizon truth as an aggregated replay view only. SV2.0 supersedes that prior limitation by adding `sleeve_1d` as a real Money Flow sleeve and by using direct Hyperliquid public mainnet `1d` candle readiness/evidence where available. The SV2.0.2 dashboard display fix now loads ignored chart/trade JSON derived from the regenerated canonical packs, so Historical Replay can show BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX across 15m/1h/4h/1d when the generated local files are present. Historical Replay now also exposes generated SOR-EV3 `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` research replays across those same symbols/timeframes/fills. Historical Replay chart arrows select their linked trade in the Trade Inspector, arrow descriptions are off by default, and the invalid Experiments tab is not exposed. SOR-EV2.1 adds the visible Evidence Lab tab for SOR-EV1/SOR-EV2 bundle review while keeping variants evidence-only. SOR-EV2.2 adds Evidence Lab baseline-vs-variant overlays, worst-trade focus, and control-pocket overlay review while still keeping every variant evidence-only. SOR-EV3 adds a focused Evidence Lab section for `avoid_sideways_low_volatility`, but no variant is approved. The dashboard now shows Money Flow v1.2, expanded symbols, `sleeve_1d`, SV2.0.2 readiness/evidence, and SOR variant review panels while keeping sandbox execution separate.

SV2.0.2 is complete and regenerated with fully closed per-pair canonical evidence packs. SV2.0.1 and SV2.0 are complete.

## Next Proposed Phase

`MF-ORIG-EV2` may be scoped only if the founder wants direct-PDF reconciliation and/or dashboard overlays for the original Money Flow reconstruction. `SOR-EV4` may be scoped only if the founder selects a narrower hypothesis after reviewing SOR-EV3, and it must use stricter out-of-sample-style slices plus control-pocket preservation before any production-rule-change proposal. No production-rule-change phase is approved from MF-ORIG-EV1, SOR-EV1, SOR-EV2, or SOR-EV3. `PT0.1` supervised top-20 paper/sandbox runtime week remains future work and must use trusted market data for strategy truth.

UAT3.5 additional sandbox routing lifecycle tests are blocked until UAT-universe precision validation is complete or unsupported Hyperliquid testnet observation symbols are explicitly scoped out of routing precision acceptance. PT0.1 may run the supervised top-20 paper/sandbox runtime only if it preserves no-live-endpoint, no-live-capital, risk, kill-switch, current-equity sizing, submit-lease, and dashboard monitoring boundaries. UAT/PT remains plumbing and behavior validation plus controlled paper/sandbox runtime only. It is not live trading, unrestricted exchange order submission, routing expansion, or strategy optimization.

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
| Execution | UAT3.4 recorded one approved fixed-target sandbox route attempt, accepted/open then canceled and reconciled; PT0 visualizes this ledger, public-read-only monitor rows, browser-polled testnet chart candles, TradingView Lightweight Charts, and internal paper-equity state; PT0.0.2/PT0.0.3 visualize historical strategy replay separately from sandbox execution plumbing |

The frozen evidence candidate is Hyperliquid ETH `sleeve_1h` current baseline.

## UAT Observation Universe And Timing

Future UAT observation is not ETH-only. UAT1/UAT2 should use top 20 high-volume crypto assets supported by the selected UAT venue/environment to validate platform behavior, market metadata, symbol mapping, risk visibility, no-trade/rejected-signal reasoning, and operator explainability. Top-20 inclusion is not strategy approval.

UAT2 shadow timing compared:

- `next_candle_open`
- `next_candle_close`

`same_candle_close_research_only` remains research-only.

## Explicit Non-Approvals

- Paper trading is approved for Hyperliquid testnet/sandbox only. PAPER TRADING IS APPROVED.
- Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under metadata, precision, risk, lease, label, and no-live gates. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED.
- Live trading is not approved.
- Live exchange order submission is not approved.
- Sandbox/testnet order routing is default-disabled and remains risk-gated by `PT0_SANDBOX_ORDER_ROUTING_ENABLED`.
- Further Money Flow rule changes, optimizations, and variant promotions are not approved beyond the SV2.0-approved addition of `sleeve_1d`.
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

UAT3.2 is now complete:

- Exact founder/operator approval for one second sandbox/testnet order attempt was present and validated.
- The runner checked fixed-key account/API-wallet readiness, Hyperliquid testnet endpoint identity, live-fed sandbox drawdown, approval scope, sandbox risk, submit-lease duplicate prevention, sandbox labels, and post-only/nonmarketable ETH order shape before any order-capable transport.
- Fixed-key readiness blocked because the testnet user/API wallet was still not recognized/authorized and sandbox equity was insufficient.
- Order attempt count was `0`; no order, cancel, amend, retry, or private order endpoint was called.
- Cancel and reconciliation were not attempted because no order existed.
- UAT4.0 live UAT trading dashboard / chart cockpit is complete, and UAT4.1 rebuilds it as a read-only exchange-style workstation.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

UAT3.3 is now complete:

- Exact founder/operator approval for one Hyperliquid testnet/sandbox ETH manual lifecycle probe was present.
- Account targeting now separates normal master/user accounts, API-wallet signers, and subaccount/vault targets.
- Normal master/user mode omits `vaultAddress`; subaccount/vault mode uses only the configured explicit target address.
- Hyperliquid precision formatting now uses `meta` `szDecimals`, five-significant-figure price rules, and perpetual max price decimals.
- UAT-universe precision validation is reported for BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, and AAVE.
- The runner verified the configured subaccount targeting and signer authorization, generated a sanitized planned ETH post-only order with valid precision under 10 USDC notional, then blocked before `/exchange` because target subaccount equity was `0.0`.
- Order attempt count was `0`; no order, cancel, amend, retry, or private order endpoint was called.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

UAT4.0 is now complete:

- The dashboard has a `UAT Chart Cockpit` tab sourced from committed UAT2 shadow and UAT3.4 routed-order summary JSON.
- It shows watchlist, market-data coverage, static chart snapshots, EMA5 / EMA10 / SMA20 / RSI / MACD labels, shadow/sandbox lifecycle markers, active route/equity-source cards, routed-order filters, and no-order-control safety labeling.
- It calls no private, signed, or order endpoints; uses no API keys; creates no approvals or order artifacts; and adds no paper/live behavior.

UAT4.1 is now complete:

- The dashboard cockpit has been rebuilt into an exchange-style workstation with compact top bar, persistent safety banner, left market rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs.
- `apps/dashboard/DESIGN.md` is now the canonical dashboard design system; root `DESIGN.md` is a pointer.
- It keeps top-20 assets observation-only, shows the ETH sandbox route as ledger visibility only, and adds no order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls.

Remaining later blockers:

- PT0.0.4 may scope historical data backfill and replay regeneration to reach Jan 2025 where possible; it must preserve historical candle strategy truth and no-order/no-live boundaries.
- PT0.1 requires explicit founder/operator scope before supervised top-20 paper/sandbox runtime is operated continuously.
- PT0.1 should use trusted market data for strategy truth, not Hyperliquid testnet prices.
- PT0.1 needs deployment-mode monitoring, continuous scanner scheduling, current-equity sizing enforcement against live paper PnL, submit-lease behavior, no-live-endpoint smoke checks, and operator kill-switch runbooks.
- UAT3.5 requires separate founder/operator approval before any additional sandbox order attempt.
- UAT-universe precision validation remains incomplete for unsupported Hyperliquid testnet observation symbols.
- Additional sandbox orders outside PT0/PT0.1 risk-gated scope remain unapproved.

## Required Reading For Next Work

- [[00_Money_Flow_Command_Center|Money Flow Command Center]]
- [[00 Maps/Current State Dashboard|Current State Dashboard]]
- [[00 Maps/Strategy Validation Map|Strategy Validation Map]]
- [[00 Maps/UAT Roadmap|UAT Roadmap]]
- [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]]
- [[40 Operations/UAT0 Safety Runtime Hardening|UAT0 Safety Runtime Hardening]]
- [[05_Agent_Coordination|Agent Coordination]]
- [[Project_Memory/money_flow_project_memory|Project Memory]]
