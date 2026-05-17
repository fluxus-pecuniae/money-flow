# Money Flow Project Memory

This is the canonical long-horizon strategic project memory. Repo operational docs remain implementation truth.

## Founder Vision

Money Flow is a strategy-first, mandate-driven trading platform. The goal is not to build a generic bot or fake smart router. The goal is to validate strategy behavior, make execution boundaries safe, and eventually operate a controlled multi-venue system only when evidence and operational controls justify it.

## Project Purpose

Money Flow combines:

- Money Flow strategy research.
- historical Strategy Validation.
- mandate/account/binding-aware planning and risk.
- controlled routing-assessment and recommendation workflow.
- approval-gated action hooks.
- submitted-order lifecycle and reconciliation truth.
- operator observability.
- future UAT/sandbox behavior validation.
- UAT0 safety/security/runtime readiness plus UAT0.1 API/runtime lockout, UAT0.2 adapter-policy/redaction hardening, UAT0.3 top-20 universe/drawdown readiness preflight, UAT1 public read-only connectivity/universe resolution, UAT1.1 shadow-readiness surfaces, UAT2 bounded no-order shadow observation, UAT2.1 dashboard visualization, UAT3.0 sandbox-order design/readiness, UAT3.0.1 sandbox runtime / approval / risk readiness hardening, UAT3.0.2 sandbox gate integration dry-run / policy hardening, UAT3.0.3 sandbox gate wiring / label-enforcement hardening, UAT3.0.4 sandbox private read-only drawdown readiness, UAT3.0.5 sandbox/testnet private read-only drawdown verification, UAT3.0.6 sandbox submit path dry-run wiring, UAT3.1 first sandbox/testnet lifecycle probe, UAT3.2 fixed-key readiness preflight / second sandbox lifecycle attempt blocked before order transport, UAT3.3 Hyperliquid account-targeting / precision hardening, UAT3.4 production-like fixed-target sandbox routing pipeline plus routed-order ledger, UAT4.0 read-only dashboard/chart cockpit, UAT4.1 exchange-style dashboard redesign, UAT4.2 live market dashboard plus internal paper-equity monitor, PT0 TradingView charting / top-20 paper-sandbox runtime foundation, PT0.0.2 historical strategy replay cockpit, PT0.0.3 historical data horizon / 1D replay support, SV2.0 Money Flow v1.2 real 1D sleeve plus expanded Hyperliquid public-mainnet evidence refresh, SV2.0.1 canonical evidence truth hotfix, SV2.0.2 DB-backed canonical evidence-pack generation, SOR-EV1/SOR-EV2/SOR-EV3 evidence-only variant review, MF-ORIG-EV1 original Money Flow reconstruction evidence, MF-ORIG-EV1.1 accounting/drawdown evidence hotpatch, MF-ORIG-EV2 multi-timeframe Original Money Flow evidence packs plus full-equity comparison Historical Replay UI, EV-AUDIT1 full evidence/data/paper-readiness audit, OB2.0 Obsidian strategy brain refresh, PT-RT1 real-time public-market paper-observation substrate plus separate testnet plumbing probes, PT-RT1.1 blocked probes-disabled dry-run validation due missing runtime artifacts, PT-RT1.1A expanded paper-observation lab readiness with 10 synthetic strategy lanes and founder-requested scanner visibility, PT-RT1.1B public-mainnet runtime connector/readiness smoke validation, PT-RT1.1C 24-hour probes-disabled runtime collection start, PT-RT1.4 active timeframe cutover, PT-RT1.4.1 active-week runtime cutover verification plus daily founder review pack, PT-RT1.5 active Week 1 reset with candle-close scheduler plus baseline-only fixed-25 USDC Hyperliquid testnet lifecycle gates, and PT-RT1.5.1 signed-testnet transport warm-start gating plus open-position MTM hotfix.

## Platform Tracks Completed

| Track | Outcome |
| --- | --- |
| Phase 1-4 platform foundation | Domain/API/db/service scaffold, exchange/data/state foundation, indicators, Money Flow strategy family, planning/risk/execution substrate. |
| Phase 5-6 routing substrate | Non-executing assessment, route-readiness audit, recommendation, target choice, conversion, readiness, explicit same-target handoff, workflow inspection, submit uncertainty hardening. |
| Phase 7 controlled automation | Approval-gated same-target action hooks with exact-lineage safety proof. |
| Phase 8 operator observability | Read-only routed workflow/manual-resolution inspection and active submit-lease truth. |
| Strategy Validation SV1 | Hyperliquid evidence cycle from backtest truth through dynamic equity, diagnostics, replay experiments, and UAT candidate freeze. |
| Strategy Validation SV2.0 | Money Flow v1.2 adds real `sleeve_1d`; expanded Hyperliquid public-mainnet readiness/evidence covers BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB across 15m/1h/4h/1D. |
| Strategy Validation SV2.0.1 | Canonical evidence truth hotfix: compact rows are noncanonical, dataset-end open positions are force-closed with entry-fee accounting, Hyperliquid close slots are normalized, staged/imported/canonical-evidence truth is split, allocations are 0.25 each, `1d` is canonical internally, and missing indicators are invalid. |
| Strategy Validation SV2.0.2 | Hardened canonical import/evidence: normalized Hyperliquid public mainnet candles are DB-imported through the hardened importer, 36 regenerated fully closed per-pair canonical evidence packs exist for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, SHIB/kSHIB is deferred, and SOR-EV1 may proceed. |
| SOR-EV1-SOR-EV3 | Evidence-only variant review: loss anatomy, true-forward stop/entry variants, Evidence Lab review, chart overlays, and founder-selected `avoid_sideways_low_volatility` drilldown are complete. No variant was promoted and production Money Flow rules remain unchanged. |
| MF-ORIG-EV1-EV2 | Original Money Flow reconstruction plus evidence expansion: the prompt-provided Gerald Peters source hierarchy is formalized into a source spec/gap matrix and Strategy Validation-only hypotheses. MF-ORIG-EV1.1 quarantines pre-hotpatch PnL/drawdown conclusions and regenerates reports with event-ledger accounting, peak-to-trough drawdown, and baseline-positive 1d control-pocket filtering. MF-ORIG-EV2 then generates evidence-only packs and dashboard replay data across 9 symbols, 4 timeframes, 2 fill assumptions, the four source-faithful 1% risk-sizing original hypotheses, and four founder-requested full-equity/notional comparison counterparts. Current Money Flow v1.2 remains unchanged; source-faithful and full-equity comparison hypotheses are not production-approved. |
| EV-AUDIT1 | Full audit review: Money Flow v1.2, SOR, MF-ORIG, and pending strategy-discovery status are inventoried; data integrity and methodology are scored; winners, losers, loss streaks, regimes, control pockets, and P0/P1/P2/P3 issues are reviewed. No clean strategy candidate is promoted. Current evidence is adequate for visual review and hypothesis filtering only; PT-RT1 was later scoped and implemented as a Paper Trading observation substrate, not approval. |
| OB2.0 | Obsidian strategy brain refresh: one canonical command center, strategy-family map, evidence/backtesting map, data-source map, dashboard/UI map, strategy status register, Original Money Flow source note, EV-AUDIT1 summary, and paper-observation roadmap now separate current v1.2, MF-ORIG, SOR, STRAT-EV, canonical evidence, dashboard display-only data, UAT plumbing, and PT-RT1 readiness. |
| PT-RT1 | Real-time paper observation substrate: public Hyperliquid mainnet market data is the strategy-truth lane, fully closed candles and indicators feed independent synthetic 10,000 USDC ledgers, and Hyperliquid testnet plumbing probes are separate, disabled/kill-switched/exact-approval gated, capped, post-only, cancel/reconcile required, and never strategy PnL truth. No production strategy, paper runtime authority, live trading, live orders, private/signed/order endpoints from strategy truth, API keys, evidence-pack regeneration, or SOR/fanout/CBBO behavior is approved. |
| PT-RT1.1 | 24-hour probes-disabled dry-run validation: blocked because the expected ignored runtime artifact directory `reports/paper_runtime/pt_rt1_1_24h_dry_run/` does not exist. The report/summary record probes disabled, kill switch active, daily cap zero, no-order/no-live boundaries, and `PT-RT1.2 blocked`. Public mainnet refresh, candle gating, ledgers, duplicate prevention, data-health gating, and dashboard runtime readability remain not verified until a real dry run is executed. |
| PT-RT1.1A | Expanded paper-observation lab readiness: exactly 10 synthetic 10000 USDC lanes are configured, including Money Flow baseline, two SOR rolling-range lanes, four MF-ORIG full-equity reference lanes, and three wildcard expert observation hypotheses. The requested scanner universe now includes canonical symbols plus founder-requested additions, requested/resolved aliases, blocked-symbol reason codes, and dashboard lane/wildcard diagnostics. PT-RT1.1B followed as public-mainnet connector/runtime readiness; PT-RT1.2 remains blocked until a real probes-disabled run passes. |
| PT-RT1.1B | Public-mainnet runtime readiness: adds a Hyperliquid public mainnet `/info` connector, runtime command, ignored artifact writer, dashboard connection status, and bounded smoke validation. Smoke connected to public `meta` and `allMids`, resolved 25 requested rows with 23 eligible and 2 blocked, recorded 80 bounded paper decisions, and submitted no orders. PT-RT1.1C may start the 24-hour probes-disabled collection; PT-RT1.2 remains blocked until that run passes. |
| PT-RT1.1C | 24-hour probes-disabled runtime collection: ignored artifacts under `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` currently contain about 479k paper decision rows, 0 trade rows, and latest summary timestamp `2026-05-15T22:22:12Z`. PT-RT1 is not always-on or hosted; new signal generation requires manually starting `scripts/run_pt_rt1_paper_observation.py` and keeping that process and machine awake/networked for the chosen session. PT-RT1.1D evaluates the completed artifacts; PT-RT1.2 remains blocked until the probes-disabled run passes. |
| PT-RT1.2.1 | Paper Trading dashboard UI follow-up: the founder view is chart-first, the visible watchlist/scanner panel is removed, Signal Generator/Open Synthetic Positions/Closed Synthetic Trades paginate, opened and closed synthetic trades render as chart markers, global Symbol/Timeframe/Strategy filters apply across relevant widgets, and Wildcard Diagnostics moved to Strategy. This is UI visibility only and changes no production rules or trading permissions. |
| PT-RT1.4 | Paper Trading command-center cleanup and active timeframe cutover: active Week 1 paper review uses `1h`, `4h`, and `1d`; `15m` is paused as `disabled_for_week1_noise_reduction`, excluded from active scoring/new entries, and preserved as legacy data. Strategy Lane Comparison is timeframe-scoped, Open/Closed Synthetic Trade tables are founder-readable, Signal Generator is a categorized paper-decision stream, and testnet labels split audit-only shapes from disabled order transport. This changes no production rules or trading permissions. |
| PT-RT1.4.1 | Active-week runtime cutover verification and daily review pack: the old `pt_rt1_1c_24h_dry_run` runtime was found to still create 15m opens after the PT-RT1.4 cutover, so it is labeled `pre_pt_rt1_4_weekend_burn_in` and excluded from active scoring. A restarted runtime under `reports/paper_runtime/pt_rt1_4_1_active_week/` reported active `1h`/`4h`/`1d`, disabled `15m`, and 0 15m rows in its first artifact cycle. The committed `docs/pt_rt_week1_day_summary.*` pack says Week 1 paper observation may continue. This changes no production rules or trading permissions. |
| PT-RT1.5 | Active Week 1 reset, candle-close scheduler, and baseline-only testnet lifecycle gates: the default active scope is `pt_rt1_5_week1_active`, old runtime rows are archived and hidden by default, active timeframes stay `1h`/`4h`/`1d`, `15m` stays paused, market refresh is separated from signal evaluation, and strategies evaluate only after fully closed active candles plus grace delay. Only scheduled `money_flow_v1_2_baseline` `paper_opened` rows may create fixed 25 USDC Hyperliquid testnet lifecycle rows; candidate/MF-ORIG/wildcard lanes remain synthetic-only and testnet fills never update synthetic PnL. |
| PT-RT1.5.1 | Signed testnet transport, warm-start signal gate, and open MTM hotfix: pre-warm-start smoke rows are archived, the active smoke scope is `pt_rt1_5_1_smoke`, startup-valid entry confirmations are recorded but blocked until a fresh post-start false-to-true signal occurs, signed Hyperliquid testnet transport is wired only for fresh Money Flow v1.2 baseline opens with fixed 25 USDC notional, candidate/MF-ORIG/wildcard lanes stay synthetic-only, and open synthetic positions mark to public mainnet mids or latest closed candles instead of showing missing marks as zero. |

## Routing / SOR Status

The platform has a controlled routing substrate. It is not a full smart order router.

Deferred:

- best-binding selection.
- CBBO.
- venue ranking/scoring.
- fanout / split allocation.
- target reselection.
- route executor behavior.
- cross-binding / cross-venue recovery.
- broad auto-submit.

Routing expansion is not the current priority.

## Strategy Validation Timeline And Outcomes

| Range | Outcome |
| --- | --- |
| SV1.0-SV1.2.1 | Baseline backtest, fill timing, drawdown, window, coverage, and regime truth. |
| SV1.3-SV1.4.1 | Campaign/evidence-pack workflow and collision safety. |
| SV1.5-SV1.9.1 | Historical data/import/DB governance, schema gates, timestamp truth. |
| SV1.10-SV1.12.5.1 | Intended DB, Hyperliquid identity, public campaign import, repo/import closeout. |
| SV1.13-SV1.13.2 | First Hyperliquid public evidence and dynamic-equity sizing. |
| SV1.14-SV1.17 | Diagnostics, experiment methodology, rejected-signal replay, and full-suite true replay. |
| SV1.18-SV1.18.1 | Evidence credibility closeout, UAT candidate freeze, Obsidian coordination closeout. |
| SV2.0 | Real 1D sleeve, Money Flow v1.2, expanded Hyperliquid public-mainnet data/evidence refresh. |
| SV2.0.1 | Evidence-truth hotfix; compact rows remain noncanonical and import/staging truth is explicit. |
| SV2.0.2 | Canonical SV2 evidence packs generated from DB-imported hardened candle data. |

Current accepted interpretation:

- ETH `sleeve_1h` baseline is the strongest observed Hyperliquid public-candle candidate.
- 15m and 4h are weak and excluded from current UAT scope.
- BTC/SOL 1h are mixed/weaker and excluded from current UAT scope.
- Lower-RSI variants did not beat the ETH 1h baseline control pocket.
- Market-structure variants remain research-only.
- Current evidence does not prove future performance.
- SV2.0 adds a real `sleeve_1d` baseline and expanded public-mainnet compact evidence, but does not optimize parameters, approve live trading, or prove profitability.
- SV2.0.1 makes compact evidence truth stricter: compact rows are provisional/noncanonical, open final positions are force-closed, and staged data is not imported.
- SV2.0.2 generates DB-backed canonical evidence packs; the 2026-05-12 regeneration uses fully closed per-pair windows so each supported pair/timeframe backtests as far back as its DB-imported public data allows. SOR-EV1 may proceed, but the evidence still does not prove future performance or approve live trading.
- SOR-EV1/SOR-EV2/SOR-EV3 use canonical SV2.0.2 as the evidence baseline. Stop/entry variants and the founder-selected `avoid_sideways_low_volatility` family remain evidence-only; no variant has been promoted to production.
- MF-ORIG-EV1.1 shows current Money Flow v1.2 is Money Flow-inspired rather than source-faithful, while also correcting the first-pass MF-ORIG evidence accounting. Pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions should not be used. The regenerated reconstruction uses 1d as primary timeframe with Stage 1-4, 5EMA/20SMA, RSI warning, MACD substitute, structure-stop, 1% risk-sizing assumptions, event-ledger accounting, and peak-to-trough drawdown. It shows pre-gate aggregate improvement but still fails candidate gate because baseline-positive 1d control pockets were not preserved. The source PDF is now stored in `money-flow/90 Reference/`, so later MF-ORIG work can reconcile exact source text without changing existing evidence numbers.
- MF-ORIG-EV2 extends the corrected reconstruction across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and both next-candle fill assumptions. It now includes four source-faithful 1% risk-sizing rows plus four founder-requested full-equity/notional comparison rows, generating ignored evidence-pack and dashboard chart-data artifacts for founder review in Historical Replay while preserving no-rule-change/no-order/no-live boundaries. The `1d` source-primary control-pocket weakness remains a blocker even where aggregate multi-timeframe deltas improve.
- EV-AUDIT1 concludes that no clean strategy candidate is currently promoted. `avoid_low_rolling_range_50` is the strongest SOR founder-review candidate but still has drawdown/control-pocket blockers; `mf_orig_1d_stage2_breakout_resistance_full_equity` is the best MF-ORIG full-equity review lane but not a production candidate. The evidence estate is good enough for visual review and hypothesis filtering only. Real-time paper observation can be scoped next as PT-RT1 under trusted public market data and no-live/no-order boundaries, but EV-AUDIT1 does not approve strategy paper runtime or live trading.
- OB2.0 makes this taxonomy explicit in Obsidian: current Money Flow v1.2, Original Money Flow/MF-ORIG, SOR repair variants, STRAT-EV discovery, canonical evidence, display-only dashboard data, UAT sandbox plumbing, and PT-RT1 readiness are separated into dedicated maps/registers.
- PT-RT1 implements that next forward-observation substrate. It is not another backtest and it has not produced a completed 60-day observation result yet. PT-RT1.1 explicitly checked for the 24-hour artifact set and was blocked because it was missing. PT-RT1.1A expands the lab before the run to exactly 10 lanes, founder-requested scanner symbols, requested/resolved/blocked reason-code visibility, and wildcard diagnostics. PT-RT1.1B connects the runtime to Hyperliquid public mainnet data, verifies public `meta` and `allMids` connectivity in a bounded smoke cycle, and prepares PT-RT1.1C 24-hour probes-disabled collection. PT-RT1.4 cuts active Week 1 to `1h`/`4h`/`1d`; PT-RT1.4.1 then verifies that the original running artifact did not pick up that cutover, retires it as burn-in, and starts a fresh active-week runtime with 0 15m rows in the first cycle. PT-RT1.5 resets active Week 1 to `pt_rt1_5_week1_active`, archives older rows by default, evaluates strategy signals only after closed active candles, and permits only baseline-linked fixed-25 USDC Hyperliquid testnet lifecycle rows. PT-RT1.5.1 moves fresh smoke review to `pt_rt1_5_1_smoke`, blocks startup-valid confirmations until fresh post-start transitions, wires signed baseline-only testnet transport, and fixes open-position MTM. Strategy truth is public Hyperliquid mainnet market data only; testnet lifecycle rows are plumbing only and cannot update strategy PnL.

## Current UAT Candidate

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

- Venue: Hyperliquid.
- Product: USDC perpetual.
- Symbol: ETH.
- Component: `sleeve_1h`.
- Rules: current baseline Money Flow rules.
- Initial mode: observation / shadow first.
- Execution: UAT3.1 made one approved rejected sandbox/testnet attempt; UAT3.2 and the initial UAT3.3 run blocked before order transport; UAT3.3 follow-up and UAT3.4 proved accepted/open -> cancel -> reconcile sandbox lifecycle plumbing through the fixed Hyperliquid testnet ETH route.

Excluded from current UAT:

- 15m.
- 4h.
- BTC 1h.
- SOL 1h.
- lower-RSI variants.
- market-structure variants.
- Aster / Binance / OKX / Coinbase / Kraken.
- cross-venue comparison.

## UAT0 / UAT0.1 / UAT0.2 / UAT0.3 / UAT1 / UAT1.1 / UAT2 / UAT2.1 / UAT3.0 / UAT3.0.1 / UAT3.0.2 / UAT3.0.3 / UAT3.0.4 / UAT3.0.5 / UAT3.0.6 / UAT3.1 / UAT3.2 / UAT3.3 / UAT3.4 / UAT4.0 / UAT4.1 / UAT4.2 / PT0 / PT0.0.2 / PT0.0.3 / SV2.0 / SV2.0.1 / SV2.0.2 / PT-RT1 Outcome

UAT0 safety/security/runtime audit is complete. UAT0.1 API auth/authz and runtime lockout hardening is complete. UAT0.2 adapter runtime-policy, read-only allowlist, and representative redaction hardening is complete. UAT0.3 top-20 universe and drawdown readiness preflight is complete. UAT1 public read-only connectivity is complete. UAT1.1 shadow readiness is complete. UAT2 bounded no-order shadow observation is complete. UAT2.1 dashboard visualization is complete. UAT3.0 sandbox order design is complete. UAT3.0 sandbox-order readiness is documented. UAT3.0.1 sandbox runtime / approval / risk readiness hardening is complete. UAT3.0.2 sandbox gate integration dry-run / policy hardening is complete. UAT3.0.3 sandbox gate wiring / label-enforcement hardening is complete. UAT3.0.4 sandbox private read-only drawdown readiness is complete. UAT3.0.5 sandbox/testnet private read-only drawdown verification is complete. UAT3.0.6 sandbox submit path dry-run wiring is complete. UAT3.1 first sandbox/testnet lifecycle probe is complete. UAT3.2 fixed-key readiness preflight / second sandbox lifecycle attempt is complete as blocked before order transport. UAT3.3 Hyperliquid account-targeting / precision hardening is complete with a later accepted/open -> cancel follow-up lifecycle. UAT3.4 production-like sandbox routing pipeline and routed-order ledger are complete. UAT4.0 read-only dashboard/chart cockpit is complete. UAT4.1 exchange-style dashboard redesign is complete. UAT4.2 live market dashboard and paper-equity monitor is complete. UAT4.2 live market dashboard and internal paper-equity monitor is complete. PT0 TradingView charting and top-20 paper/sandbox runtime foundation is complete. PT0.0.2 historical strategy replay cockpit is complete. PT0.0.3 historical data horizon and 1D replay support is complete. SV2.0 Money Flow 1D sleeve and expanded public-mainnet evidence refresh is complete. SV2.0.1 canonical evidence truth hotfix is complete. SV2.0.2 hardened DB import and canonical evidence-pack generation is complete. PT-RT1 real-time public-market paper-observation substrate and separate Hyperliquid testnet plumbing-probe gates are implemented; PT-RT1.1 dry-run validation is blocked by missing 24-hour runtime artifacts; the 60-day observation result is not complete yet.

Historical Replay now includes three strategy dropdown choices for founder visual analysis: OG replay / strategy, MACD removed, and Only close on 5/20 cross. The two non-OG strategies are research-only and do not change production Money Flow rules. The dashboard preserves PT0.0.3 summary data ahead of PT0.0.2 fallback data so 1D remains visible.

SV2.0 supersedes PT0.0.3's dashboard-only 1D limitation: `sleeve_1d` is now a real Money Flow v1.2 sleeve, while existing 15m/1h/4h settings remain unchanged. The expanded requested evidence universe is BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, and SHIB; all are supported by Hyperliquid public mainnet metadata in the current run, with SHIB explicitly resolved as `kSHIB`. Public mainnet 4h and 1D data reach the Jan 2025 target, while 15m and 1h remain limited by Hyperliquid public recent-candle availability.

SV2.0.2 resolves the canonical SV2 evidence blocker: normalized public-mainnet candles were imported into the intended DB through the hardened importer, regenerated fully closed per-pair evidence packs now exist for supported symbols/timeframes, SHIB/kSHIB is deferred with reason codes, and SOR-EV1 may proceed. No orders, private/signed/order endpoints, API keys, testnet strategy truth, live trading, parameter optimization, stop-loss/RSI/MACD variants, SOR/fanout/CBBO, or target reselection were added.

Closed by UAT0.1:

- Sensitive `/api/v1` routes require scoped bearer authentication.
- High-risk admin consume, submit/cancel/amend/retry, account, and private-state surfaces require elevated scopes.
- Test auth bypass is limited to `API_RUNTIME_MODE=test`.
- `RuntimeSafetyPolicy` exposes fail-safe defaults for paper trading, live trading, exchange order submission, and private exchange endpoints.

Closed or partially closed by UAT0.2:

- Adapter private/signed/order calls are guarded by runtime policy before transport.
- Public read-only adapter methods are classified.
- Hyperliquid has a future-UAT1 read-only allowlist artifact.
- Representative bearer/API-key/secret/password/DB URL redaction is tested.

Closed by UAT0.3:

- Fixture-tested top-20 resolver policy and Hyperliquid market-intersection logic.
- Hyperliquid public read-only info-type allowlist for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- Fixture-tested runtime drawdown monitor policy/model.
- UAT1 public read-only connectivity may proceed under no-private/no-signed/no-order/no-API-key constraints. This preflight condition was exercised by UAT1.

Closed by UAT1:

- Explicit public-read-only network mode is required before UAT1 public calls.
- Hyperliquid public `info` endpoint behavior is verified for `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.
- CoinGecko public markets data was fetched without API keys as the top-volume source.
- The UAT1 report resolved 15 Hyperliquid USDC perpetual observation candidates and 5 excluded assets from the public top-20 source at run time.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, paper/live behavior, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT1.1:

- Representative structured application log/API error redaction is verified for UAT2; deployment-specific middleware/logging smoke tests remain before UAT3.
- Operator-visible shadow drawdown state exists for UAT2.
- A shadow signal audit surface exists for would-trade/no-trade/risk-block explainability.

Closed by UAT2:

- Explicit UAT2 shadow mode and public-read-only flags are required.
- The UAT1 universe snapshot was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.
- UAT2 created 45 shadow audit records: 11 `would_open`, 34 `no_trade`, 0 `invalid`, and 0 `risk_blocked`.
- ETH `sleeve_1h` produced `no_trade` with `macd_not_constructive`.
- UAT2 represented `next_candle_open` and `next_candle_close`; `same_candle_close_research_only` remained research-only.
- Shadow drawdown was labeled `shadow_simulated_drawdown` / `not_live_account_drawdown` and did not imply live account equity or performance.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, order intents, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were used or created.

Closed by UAT2.1:

- The existing static dashboard now has a UAT2 Shadow Run view that loads `docs/uat2_shadow_strategy_top20_observation_summary.json`.
- The dashboard shows UAT2 summary cards, a filterable 45-record signal matrix, would-open records, no-trade reason breakdowns, ETH `sleeve_1h` candidate truth, `next_candle_open` / `next_candle_close` timing status, `same_candle_close_research_only` research-only status, not-live-account shadow drawdown, UAT3 blockers, and forbidden-artifact boundary flags.
- UAT2.1 adds no interactive approval action and cannot enable order submission.
- No private endpoints, signed endpoints, order endpoints, API keys, order submissions, strategy decisions, signal events, order intents, prepared orders, execution readiness assessments, submitted orders, approvals, paper/live behavior, evidence packs, routing artifacts, or Money Flow rule changes were used or created.

Closed by UAT3.0:

- The future initial sandbox-order subset is defined as Hyperliquid ETH USDC perpetual `sleeve_1h` current baseline rules only.
- The founder/operator approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate-prevention design, approval gate design, and risk gate design are documented.
- The dashboard UAT view has an informational UAT3.0/UAT3.0.1/UAT3.0.2/UAT3.0.3 design/readiness panel.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.1:

- Fail-closed `SandboxRuntimePolicy` fixture/readiness helper exists and defaults sandbox submission, private endpoints, live endpoint access, paper/live trading, and generic exchange order submission to disabled.
- Sandbox artifact label validation exists and fails unsafe/missing sandbox/testnet/not-live/not-paper labels.
- Future UAT3.1 actual-submission approval wording is separate from design/scoping approval and requires exact venue, environment, symbol, component, max size/count, order type, time window, sandbox account, kill switch, and lifecycle scope.
- Approval scope validation, sandbox risk gate evaluation, sandbox drawdown feed fixture support, and submit-lease duplicate-prevention fixture checks exist and are test-covered.
- Dashboard UAT view shows fixture/readiness status.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.2:

- Sandbox risk gates now propagate all `SandboxRuntimePolicy` blockers into risk/preflight reason codes.
- Approval scopes, risk limits, risk requests, and drawdown fixtures reject invalid non-positive sandbox numeric values.
- `evaluate_uat3_sandbox_submission_preflight` combines runtime policy, artifact labels, approval scope, risk gates, drawdown feed status, submit preflight, founder actual-submission approval, and artifact-label persistence status into one fixture-only dry-run result.
- The dry-run preflight explicitly reports no order intent, submitted order, executable approval, or exchange call creation.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No orders, real order intents, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.3:

- Sandbox artifact label boundary helpers validate required sandbox/testnet/not-live/not-paper/no-real-capital labels before future persistence, API serialization, dashboard display, and report generation boundaries.
- `UAT3SandboxDryRunGateService` and `evaluate_uat3_sandbox_executable_gate_dry_run` compose runtime policy, boundary labels, approval scope, risk gates, drawdown feed status, and submit-lease duplicate-prevention checks into a dry-run executable gate result.
- Runtime policy semantics now explicitly separate broad/global exchange order submission from sandbox/testnet-only submission gating.
- The dry-run executable gate reports no order intent, prepared order, submitted order, executable approval, or exchange call creation.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No orders, real order intents, prepared orders, submitted orders, executable approvals, private/signed/order endpoint calls, exchange API keys, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.4:

- Private read-only sandbox account policy exists and fails closed without exact founder/operator credential approval.
- Credential boundary validation and redaction helpers exist for sandbox/testnet-only credentials.
- Sandbox private read-only account/balance/position/equity categories are separated from order/cancel/amend/retry/live-private endpoint categories.
- Sandbox account drawdown feed modeling exists with `sandbox_account` / `not_live_account` labels and explicit unavailable-field truth.
- UAT3 dry-run preflight can consume `sandbox_drawdown_feed_live_fed_verified`; UAT3.0.5 later verified that status through the approved Hyperliquid testnet read-only account-state path.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No credentials were used, no private endpoints were called, no order/cancel/amend/retry endpoints were called, and no orders, real order intents, prepared orders, submitted orders, executable approvals, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.5:

- The exact founder/operator approval text for sandbox/testnet private read-only account-state/drawdown verification is present and validated.
- Sandbox/testnet credential environment status is inspectable without retaining private key values.
- Live Hyperliquid endpoint URLs are blocked by sandbox/testnet boundary validation.
- Hyperliquid sandbox account-state payload parsing can produce `sandbox_account` / `not_live_account` drawdown feed truth from caller-supplied sandbox account payloads.
- The approved rerun used the Hyperliquid testnet base URL for one read-only account-state request, returned HTTP 200, and produced `sandbox_drawdown_feed_live_fed_verified`.
- No API key/private key was sent and no order/cancel/amend/retry endpoint was called.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order/cancel/amend/retry endpoints were called, and no orders, real order intents, prepared orders, submitted orders, executable approvals, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.0.6:

- A non-persistent `UAT3SandboxSubmissionPlan` records the future ETH `sleeve_1h` sandbox submit candidate with side-effect flags fixed false.
- `UAT3SandboxSubmitDryRunService` wires runtime policy, founder actual-submission approval status, sandbox artifact-label boundary checks, approval scope validation, live-fed sandbox drawdown status, sandbox risk gates, submit-lease duplicate-prevention checks, and adapter endpoint classification.
- The dry-run consumes `sandbox_drawdown_feed_live_fed_verified` and blocks missing, stale, fixture-only, threshold-breached, or not-live-account-mislabeled drawdown.
- The future endpoint is classified as `sandbox_order_submission`, but transport invocation remains forbidden in UAT3.0.6 and `calls_exchange=false`.
- At that point, UAT3.1 actual sandbox order submission remained blocked.
- No order/cancel/amend/retry endpoints were called, and no orders, real order intents, prepared orders, submitted orders, executable approvals, paper/live behavior, routing expansion, evidence packs, or Money Flow rule changes were used or created.

Closed by UAT3.1:

- Exact founder/operator approval for one sandbox/testnet order attempt was verified before credential/order-capable use.
- The UAT3.0.6 gate chain, live-fed sandbox drawdown status, approval scope, risk gate, submit-lease duplicate prevention, endpoint classification, sandbox labels, and nonmarketable/post-only order-shape checks passed before transport.
- One Hyperliquid testnet ETH post-only limit attempt under 10 USDC notional was made.
- Hyperliquid rejected the attempt with a sanitized user/API-wallet-not-found response.
- No cancel was required because no open order existed.
- Reconciliation completed and found no open order or unexpected fill.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or second order was created.

Closed by UAT3.2:

- Exact founder/operator approval for one second sandbox/testnet order attempt was verified.
- Fixed-key account/API-wallet readiness was checked before any order-capable transport.
- Hyperliquid testnet endpoint identity and live-fed sandbox drawdown remained verified.
- The readiness gate blocked before `/exchange` because the testnet user/API wallet was not recognized/authorized and sandbox equity was insufficient.
- Order attempt count was `0`; no order/cancel/amend/retry endpoint was called.
- UAT4.0 live UAT trading dashboard / chart cockpit is complete, and UAT4.1 rebuilds it as a read-only exchange-style workstation.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

Closed by UAT3.3:

- Hyperliquid UAT account targeting now separates normal master/user accounts, API-wallet/agent signer, and explicit subaccount/vault target.
- Normal master/user account mode omits `vaultAddress`; subaccount/vault mode uses only the explicit configured subaccount/vault target.
- A Decimal-based Hyperliquid precision formatter uses `meta` `szDecimals`, five-significant-figure price rules, and perpetual max price decimals.
- UAT-universe precision validation is reported for BTC, ETH, SOL, XRP, ZEC, BNB, SUI, TON, DOGE, TRX, LAYER, CHIP, UNI, ONDO, and AAVE.
- The runner verified configured subaccount targeting and signer authorization, generated a sanitized ETH post-only planned order under 10 USDC notional, and blocked before `/exchange` because target subaccount live-fed sandbox equity was `0.0`.
- Order attempt count was `0`; no order/cancel/amend/retry endpoint was called.
- No production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 order submission, routing expansion, Money Flow rule change, evidence pack, live endpoint use, or unapproved repeated order was created.

Closed by the later UAT3.3 follow-up and UAT3.4:

- The working Hyperliquid testnet route uses normal user account mode with `vaultAddress` omitted, target account `0x7580...8222`, and API-wallet signer `0x0f42...04d9`.
- UAT3.4 added a production-like fixed-target sandbox route, `fixed_target_hyperliquid_testnet_eth`, for ETH USDC perpetual only.
- UAT3.4 added a routed sandbox order ledger and dashboard routed-orders visibility without any order button or paper/live controls.
- UAT3.4 preserved standard and unified-margin equity-source resolution. The active route selected `standard_perp_clearinghouse`; unified spot-clearinghouse fallback remains fixture-tested for USDC total minus hold.
- One UAT3.4 ETH post-only testnet order was accepted open, canceled successfully, and reconciled with no open order remaining.
- UAT3.4 kept all artifacts sandbox/testnet/not-live/not-paper labeled, did not expose secrets, did not submit live orders, did not submit top-20 orders, and did not introduce smart routing, SOR, fanout, target reselection, paper trading, live trading, Money Flow rule changes, or evidence packs.
- UAT4.0 added a read-only static chart cockpit from committed UAT2/UAT3.4 summaries, including watchlist, market-data coverage, static chart snapshots, EMA/RSI/MACD labels, shadow/sandbox lifecycle markers, active route/equity cards, routed-order filters, and no-order-control safety banners.
- UAT4.1 rebuilt that cockpit as an exchange-style workstation with compact top bar, persistent safety banner, observation-only market rail, central chart cockpit, right order-book/market/signal/risk rail, bottom blotter tabs, and canonical `apps/dashboard/DESIGN.md`. It did not add private/signed/order endpoint calls, API-key use, order controls, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.
- UAT4.2 added read-only public market monitor summary data, deterministic indicator snapshots, paper-observation scanner records, green/red marker semantics, a 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger with current-equity sizing-policy visibility. It did not add order controls, submit orders, call live endpoints, call private order endpoints, use exchange API keys, create execution artifacts, change Money Flow rules, add routing expansion, or generate evidence packs.
- PT0 adds the official local TradingView Lightweight Charts bundle, live public Hyperliquid testnet candle rendering, deterministic top-20 paper scanner records, top-20 Hyperliquid-supported paper/sandbox universe eligibility, internal 10,000 USDC paper-equity ledger truth, current-realized-equity sizing policy, 60-second sandbox private-read-only balance polling policy, and default-disabled risk-gated sandbox route-candidate foundation. PAPER TRADING IS APPROVED. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. PT0 did not submit sandbox orders, add live trading, use live endpoints, expose secrets, add SOR/fanout/CBBO/cross-venue routing, change Money Flow rules, or generate evidence packs.
- PT0.0.2 adds a Historical Replay cockpit because Hyperliquid testnet prices are not strategy truth. BTC/ETH/SOL x 15m/1h/4h historical public candle replay data is the strategy-truth source; the dashboard shows TradingView historical candles, entry/exit markers, trade inspector, dynamic 10,000 USDC equity, comparison table, and separate sandbox execution plumbing. It submits no orders, calls no private/signed/order endpoints, uses no API keys, changes no Money Flow rules, and generates no evidence packs.
- PT0.0.3 adds 1D historical replay selection, Jan 2025 target-start readiness truth, actual available horizon reporting, and a dashboard data-horizon panel. Current committed data does not reach Jan 2025. 1D is deterministic aggregation from 4h historical replay candles and does not create a production Money Flow 1D sleeve. It submits no orders, calls no order endpoints, uses no testnet prices as strategy truth, changes no Money Flow rules, and generates no evidence packs.

Remaining UAT blockers:

- UAT3.5 additional sandbox routing lifecycle tests are blocked because UAT-universe precision validation still has unsupported symbols in the current Hyperliquid metadata response.
- PT0.0.4 historical data backfill and replay regeneration is future work.
- Historical replay playback controls and market-structure inspector are future work after the Jan 2025 data horizon is trustworthy.
- PT-RT1.1C 24-hour probes-disabled dry run and 60-day public-mainnet forward-observation window remain operationally not started. PT-RT1.1B public-mainnet connector/runtime readiness code, smoke artifact, dashboard, and runbooks exist for the expanded 10-lane lab, but founder decisions should wait for 24-hour runtime logs.
- PT0.1 supervised top-20 paper/sandbox runtime week is superseded by the PT-RT1 public-mainnet observation substrate for strategy truth. Any testnet probe must remain plumbing-only, exact-approval gated, capped, post-only, cancel/reconcile required, and separate from strategy PnL.
- Additional sandbox order submission outside explicit PT/UAT risk-gated scope, live trading, real-capital trading, production auto-submit, routing expansion, and Money Flow performance validation remain unapproved.

Future UAT/PT observation is not ETH-only. UAT1/UAT2 covered the top 20 high-volume crypto assets supported by the selected UAT venue/environment for platform behavior validation. PT0 approves the broader Hyperliquid-supported top-20 paper/sandbox universe under metadata, precision, risk, lease, label, and no-live gates. Top-20 inclusion is not live trading approval, cross-venue routing approval, SOR/fanout approval, or strategy profitability proof.

UAT2 shadow timing compares `next_candle_open` and `next_candle_close`. `same_candle_close_research_only` remains research-only.

## Paper / Live Status

PAPER TRADING IS APPROVED.

BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED.

Paper trading is approved for Hyperliquid testnet/sandbox only under historical PT0 gates. PT-RT1/PT-RT1.1A add synthetic public-mainnet paper-observation ledgers only and do not approve strategy paper runtime as production behavior. Internal paper equity starts at 10,000 USDC per lane and is separate from the real Hyperliquid sandbox account confirmation balance.

Live trading is not approved.

Real-capital trading is not approved.

Live exchange order submission is not approved.

The current evidence cycle can justify UAT0 safety/runtime hardening and later shadow observation only if the founder accepts that UAT validates plumbing and behavior, not performance.

## UAT Roadmap

- UAT0: safety / security / runtime hardening audit complete.
- UAT0.1: API auth/authz and runtime lockout hardening complete.
- UAT0.2: adapter runtime-policy and redaction hardening complete.
- UAT0.3: top-20 universe and drawdown readiness preflight complete.
- UAT1: top-20 universe plus read-only venue/market metadata complete under strict public-read-only constraints.
- UAT2: bounded no-order shadow strategy observation across top-20 supported assets complete.
- UAT2.1: dashboard visualization and founder approval readiness pack complete; no approval action or order-enabling behavior added.
- UAT3.0: sandbox order design is complete; sandbox-order readiness documented; no order submission, real order intents/submitted orders, or executable approvals added.
- UAT3.0.1: sandbox runtime / approval / risk readiness fixture hardening complete.
- UAT3.0.2: sandbox gate integration dry-run / policy hardening complete; actual UAT3.1 sandbox order submission remains blocked.
- UAT3.0.3: sandbox gate wiring / label-enforcement hardening complete; boundary-label helpers and dry-run executable gate service exist; actual UAT3.1 sandbox order submission remains blocked.
- UAT3.0.4: sandbox private read-only drawdown readiness complete; credential approval/boundary validation, endpoint category separation, redaction, and sandbox account drawdown feed modeling exist; no credentials or private endpoints were used because explicit approval was absent.
- UAT3.0.5: sandbox/testnet private read-only drawdown verification complete; exact approval text and sandbox/testnet credential boundaries are validated, one Hyperliquid testnet read-only account-state request returned HTTP 200, and `sandbox_drawdown_feed_live_fed_verified` is recorded with no API key/private key or order endpoint use.
- UAT3.0.6: sandbox submit path dry-run wiring complete; non-persistent submission plans and dry-run gate chaining now cover actual-submission approval, live-fed drawdown, approval scope, risk, submit-lease duplicate prevention, endpoint classification, and sandbox labels without artifacts or exchange calls.
- UAT3.1: first sandbox/testnet lifecycle probe complete; one Hyperliquid testnet ETH post-only limit attempt was rejected by venue user/API-wallet validation, required no cancel, and reconciled no open order.
- UAT3.2: fixed-key preflight / second sandbox lifecycle attempt complete as blocked before order transport; separate approval was verified, account/API-wallet readiness failed, order attempt count was `0`, and no order endpoint was called.
- UAT3.3: Hyperliquid account-targeting / precision hardening complete; a later follow-up proved accepted/open -> cancel lifecycle on Hyperliquid testnet.
- UAT3.4: production-like fixed-target sandbox routing pipeline and routed-order ledger complete; one ETH testnet post-only order was accepted open, canceled successfully, and reconciled with no open order remaining.
- UAT3.5: additional sandbox routing lifecycle tests are blocked pending complete UAT-universe precision coverage and separate approval.
- UAT4.0: live UAT trading dashboard / chart cockpit complete as read-only local visualization.
- UAT4.1: exchange-style dashboard redesign complete.
- UAT4.2: live market dashboard and internal paper-equity monitor complete.
- PT0: TradingView charting and top-20 paper/sandbox runtime foundation complete; paper trading and broader top-20 Hyperliquid-supported paper/sandbox scope are approved for testnet/sandbox only.
- PT0.0.2: historical strategy replay cockpit complete; historical public candle replay data is strategy truth, Hyperliquid testnet prices are sandbox execution plumbing only.
- PT0.0.3: historical data horizon and 1D replay support complete; SV2.0/SV2.0.2 supersede the earlier local-data limitation by providing canonical public-mainnet 4h/1d evidence/chart data back to Jan 2025 where Hyperliquid public history is available.
- PT-RT1: real-time public-market paper observation substrate complete; strategy truth lane uses public Hyperliquid mainnet market data only, strategy lanes have independent synthetic 10,000 USDC ledgers, and testnet plumbing probes are separate, disabled/kill-switched by default, exact-approval gated, capped, post-only, cancel/reconcile required, and never strategy PnL truth.
- PT-RT1.1A: expanded paper-observation readiness complete; 10 synthetic strategy lanes, founder-requested scanner symbols, alias/blocking policy, blocked-symbol reason codes, and Paper Observation lane/wildcard diagnostics are present before PT-RT1.1B runtime collection starts.
- PT-RT1.1B: public-mainnet connector/runtime readiness complete; smoke connected to Hyperliquid public mainnet, resolved the expanded watchlist, recorded bounded paper decisions, kept probes disabled, and leaves PT-RT1.1C as the next 24-hour probes-disabled collection phase.
- Paper Observation live display: while PT-RT1.1C runs, the dashboard browser-polls Hyperliquid public mainnet `allMids` every 1 second for a compact symbol/mid/health watchlist and selected-pair `candleSnapshot` for a live TradingView chart. Watchlist health is `unhealthy` when the latest market-data tick is missing or stale for more than 2 minutes. The Signal Generation panel lists recorded synthetic `paper_opened` intended-entry decisions. This is display-only, uses no private/signed/order/API-key path, and does not approve paper/live behavior.
- SV2.0.2 dashboard display fix: Historical Replay now loads ignored chart/trade JSON derived from existing regenerated canonical packs for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, with arrow descriptions off by default and the invalid Experiments tab removed.
- PT0.0.4: broader historical data backfill beyond available Hyperliquid public windows remains future work only.
- PT0.1: supervised top-20 paper/sandbox runtime week is future work only.

UAT1 public read-only connectivity is complete under strict constraints. UAT1 used no API keys, private endpoints, signed endpoints, order endpoints, paper trading, live trading, or order submission.

## Major Deferred Items

- deployment-specific structured log/API error redaction smoke tests before UAT3.
- secret hygiene beyond representative helper tests.
- fail-safe sandbox/live mode separation verification.
- risk-limit enforcement.
- UAT3 sandbox/live drawdown feed wiring and verification.
- UAT3 explicit design approval and sandbox lifecycle prerequisites.
- kill switch behavior.
- debug stack trace exposure hardening.
- audit logging review.
- operator confirmation gates.
- duplicate-order prevention.
- submit-lease uncertainty verification.
- funding/liquidation/margin modeling.
- order-book/partial-fill/latency/outage modeling.
- out-of-sample and cross-venue evidence.
- smart routing / SOR expansion.

## Required Agent Memory Workflow

Read the canonical command center, current phase, decision log, coordination note, and this project memory before substantial work. Update your own coordination row before overlapping edits and mark it `done` or `blocked` after work.

Do not create duplicate command centers or competing current-phase notes.

## 2026-05-14 - SV2.1 Broad 1D Evidence Refresh

SV2.1 generated broad active-Hyperliquid-public-metadata 1D Money Flow v1.2 period evidence as research-only founder-review data. The run used public Hyperliquid mainnet `meta` and `candleSnapshot` only, targeted 183 active symbols, imported available 1D candles back to 2024-01-01 where available, and produced 646 ignored evidence packs across 2024, 2025, YTD, and ALL. It changed no production Money Flow rules, approved no variant, approved no paper/live behavior, submitted no orders, and used no private/signed/order endpoints, API keys, or testnet strategy truth.

## 2026-05-14 - SV2.1 Historical Replay + Conservative Candidate Artifacts

SV2.1 broad 1D evidence now has dashboard Historical Replay artifacts and evidence-only conservative candidate packs. The builder produced 5116 ignored selected chart/trade JSON files under `reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data/20260514T220500Z` and 1912 ignored candidate pack directories for `avoid_low_rolling_range_50`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`. MF-ORIG candidate rows are skipped where indicator context is incomplete rather than defaulted or fabricated. The dashboard Historical Replay period selector can inspect 2024, 2025, YTD, and ALL 1D period sets. This remains founder-review evidence only: no production rules changed, no variant is approved, no paper/live behavior is approved, and no orders or private/signed/order endpoints were used.

## 2026-05-15 - SV2.1 Founder-Approved Evidence Correction

The broad active-metadata SV2.1 evidence estate was rejected for founder review and removed from local generated outputs. SV2.1 now uses the founder-approved requested/resolved universe only: BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, TRX, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, and TRUMP. PEPE/kPEPE and OKB remain excluded by resolver policy. The 2026-05-15 rebuild generated 90 ignored baseline 1D period packs, 270 ignored evidence-only candidate packs, and 720 ignored selected Historical Replay chart/trade JSON files at timestamp `20260515T004500Z`. ASTER and TRUMP have no 2024 packs because public 1D candles do not cover that period. The rebuild changed no production Money Flow rules, approved no variant, approved no paper/live behavior, submitted no orders, and used no private/signed/order endpoints, API keys, or testnet strategy truth.

2026-05-16 - SV2.1 10-Lane Founder Review Evidence

The SV2.1 founder-approved 1D evidence builder now covers all 10 PT-RT1 paper-observation lanes for founder comparison. The latest ignored artifacts use timestamp `20260516T091500Z`: 90 baseline Money Flow v1.2 period packs remain the 1D baseline, and the builder generated 810 evidence-only candidate/reference/wildcard pack directories plus 1800 selected Historical Replay chart/trade JSON files. The 10 lanes are Money Flow v1.2 baseline, two SOR rolling-range candidates, four MF-ORIG full-equity reference lanes, and three wildcard observation lanes. This remains 1D founder-review evidence only; no variant is approved, no paper/live behavior is approved, no orders/private/signed/order endpoints/API keys/testnet strategy truth were used, and production Money Flow rules did not change.

2026-05-16 - PT-RT1 Local Dashboard Runtime Control

The Paper Trading dashboard now has a localhost-only Start Run / Stop Run helper when served by `scripts/run_dashboard_control_server.py`. It starts `scripts/run_pt_rt1_paper_observation.py` through Mac `caffeinate` for allowlisted 5-minute, 1-hour, 6-hour, or 24-hour synthetic paper-observation sessions. It initially forced probes-disabled public-mainnet runs, then temporarily supported 20 USDC audit/order-shape rows, PT-RT1.5 started `pt_rt1_5_week1_active`, and PT-RT1.5.1 now defaults to `pt_rt1_5_1_smoke` with candle-close signal evaluation, fresh-signal-only warm-start gating, disabled legacy probes, public-mainnet strategy truth, and baseline-only fixed 25 USDC signed testnet transport gates. Static dashboard serving remains review-only and shows the controls unavailable. This is runtime ergonomics only: it changes no production Money Flow rules, approves no live behavior, uses no private/signed/order endpoint from strategy truth, uses no API keys for strategy truth, and does not make testnet data strategy truth.

2026-05-16 - PT-RT1 Compact Decision Logging Default

PT-RT1 runtime starts now default to compact decision logging after a local runtime run showed `decisions.jsonl` can grow to operationally large sizes. Compact mode preserves actionable synthetic open/close rows, data-unavailable rows, and first-seen non-actionable audit rows while suppressing repeated identical non-actionable rows across cycles. Runtime `summary.json` records log mode, rows written, rows suppressed, and `decisions.jsonl` size, and the Paper Trading dashboard displays those stats. `full_audit` remains an explicit CLI mode for short diagnostics. Existing ignored large local logs are not rewritten by this change. No production Money Flow rule changed, no paper/live approval was added, no order/private/signed endpoint/API-key/testnet-strategy-truth path was added, and no evidence pack was regenerated.

2026-05-16 - PT-RT1 20 USDC Testnet Probe Audit Mode

The Paper Trading dashboard-started runtime temporarily enabled Hyperliquid testnet probe audit/order-shape rows at exactly 20 USDC per synthetic `paper_opened` signal while preserving public-mainnet strategy truth and independent synthetic paper PnL. PT-RT1.5 superseded this founder surface with baseline-only fixed 25 USDC testnet lifecycle rows, and PT-RT1.5.1 further requires fresh post-start Money Flow v1.2 baseline opens before signed testnet transport. The old 20 USDC mode remains historical context and should not be treated as the current active Week 1 transport policy.

2026-05-16 - PT-RT1.2 Runtime State And Transport Gates

PT-RT1.2 fixes the runtime-correctness issue found in local review: repeated same-candle synthetic opens were caused by stateless cycles. Fresh runs now persist processed signal keys, open synthetic positions, realized equity by lane, and last processed close state; duplicate same-candle opens become held/blocked rows; synthetic closes write `trades.jsonl`; and summaries separate public market-data unavailable rows from lane-expanded `data_unavailable` decisions. The 20 USDC Hyperliquid testnet probe lane remains audit/order-shape by default; signed transport requires an explicit PT-RT1.2 submit flag, exact transport approval, and a configured client. Testnet fills/prices never update synthetic paper PnL. No production Money Flow rule changed, no paper/live approval was added, and no SOR/fanout/CBBO behavior was added.

2026-05-16 - PT-RT1.3 Candle-Truth Data Health

PT-RT1.3 fixes false-positive `data_unavailable` rows caused by stale/thin/missing Hyperliquid public mids. Fresh runs now treat public `allMids` issues as warning-only when clean fully closed public-mainnet `candleSnapshot` rows are available. Scanner eligibility depends on supported venue identity and precision; candle validity, candle availability, and indicator readiness remain the blocking strategy-data gates. Dashboard Paper Observation separates blocking candle rows from non-blocking mid warning rows. No production Money Flow rule changed, no paper/live approval was added, no private/signed/order endpoint or API-key path was added, testnet data remains non-strategy truth, and no SOR/fanout/CBBO behavior was added.

2026-05-16 - PT-RT1.3 TRUMP Runtime Scanner Deferral

TRUMP is deferred from fresh PT-RT paper-observation scanner runs after founder review because it created excessive runtime noise. New PT-RT requested scanner symbols exclude TRUMP and summary metadata records `deferred_runtime_symbols.TRUMP=runtime_noise_deferred_by_founder`. Existing SV2.1 historical evidence artifacts that already include TRUMP remain historical truth and were not regenerated or rewritten. No production Money Flow rule changed, no paper/live approval was added, no order/private/signed endpoint/API-key/testnet-strategy-truth path was added, and no SOR/fanout/CBBO behavior was added.

2026-05-16 - PT-RT1.3 Paper Observation Signal Visibility

The Paper Trading dashboard now loads recent ignored PT-RT `decisions.jsonl` rows for Signal Generation so durable synthetic `paper_opened` signals remain visible even when the latest `summary.json` cycle has no new opens. The testnet probe panel separated local 20 USDC audit/order-shape rows from signed testnet orders and labels `audit_only` as no signed Hyperliquid testnet submission. PT-RT1.5 superseded the active founder surface with a dedicated Testnet Order Transport widget and separate Testnet Order Lifecycle table for baseline-only fixed 25 USDC lifecycle rows. PT-RT1.5.1 now defaults that surface to the fresh smoke scope, shows warm-start gate counters and signed client status, and prevents fallback to old logs by default. No production Money Flow rule changed, no paper/live approval was added, no strategy-truth order/private/signed endpoint/API-key/testnet-strategy-truth path was added, and no SOR/fanout/CBBO behavior was added.

2026-05-17 - PT-RT1.2.1 Dashboard Chrome And Closed-Trade Display Cleanup

The dashboard now uses compact top chrome with the logo, Money Flow Evidence Dashboard title, theme selector, and six primary tabs; manual report loading and evidence-loaded status text are intentionally absent from founder chrome. Paper Trading's Local Mac runtime control is a two-column card with duration/output/start/stop/caffeinate context on the left and runtime details on the right. Closed Synthetic Trades displays only ledger-complete synthetic trade rows from `trades.jsonl`/complete summaries and filters sparse `paper_closed` decision rows that would show entry/exit/qty/PnL as n/a. Strategy Lane Comparison sits directly below the Open/Closed Synthetic Trades section. This is dashboard display/layout only; no runtime behavior, production Money Flow rule, evidence pack, paper/live approval, order/private/signed endpoint/API-key/testnet-strategy-truth path, or SOR/fanout/CBBO behavior changed.

2026-05-17 - PT-RT1.4 Paper Trading Active Timeframe Cutover

Paper Trading is now the active weekly command center. Active Week 1 scoring and new paper entries are scoped to `1h`, `4h`, and `1d`; `15m` is paused for noise reduction, preserved as legacy data, and excluded from all-active lane totals. The dashboard top health banner states public-mainnet strategy truth, active timeframes, paused 15m, disabled testnet order transport, and no live approval. Weekly Scoreboard is timeframe-scoped by default, Timeframe Breakdown makes 15m pause visible, Open/Closed Synthetic Trades are cleaned up, Signal Generator is a categorized Signal / Decision Stream, and testnet plumbing labels distinguish audit-only shapes from actual order transport. No production Money Flow rule changed, no paper/live approval was added, no order/private/signed endpoint/API-key/testnet-strategy-truth path was added, and no SOR/fanout/CBBO behavior was added.

2026-05-17 - PT-RT1.4.1 Active Runtime Cutover Verification

PT-RT1.4.1 proves the active timeframe cutover in runtime artifacts. The old `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` process continued writing 15m synthetic opens after the cutover timestamp, so that directory is now pre-cutover burn-in and excluded from active Week 1 scoring. The restarted active runtime writes to `reports/paper_runtime/pt_rt1_4_1_active_week/`; its first artifact cycle had active timeframes `1h`, `4h`, and `1d`, disabled `15m`, 0 new 15m opens, and 0 15m rows. The daily founder pack at `docs/pt_rt_week1_day_summary.md` / `.json` says Week 1 paper observation may continue. No production Money Flow rule changed, no strategy/threshold changed, no paper/live approval was added, no live/testnet orders or private/signed/order endpoint/API-key path was added, no testnet strategy truth was introduced, and no SOR/fanout/CBBO behavior was added.

2026-05-17 - PT-RT1.5 Active Week Reset And Baseline Testnet Lifecycle Gates

PT-RT1.5 resets active Week 1 to `pt_rt1_5_week1_active`, archives older runtime rows by default, keeps `1h`, `4h`, and `1d` active, and keeps `15m` paused for active scoring/new entries/testnet triggers. Market refresh remains available for watchlist, chart, data-health, heartbeat, and unrealized PnL display, but strategy signals are evaluated only after fully closed active candles plus grace delays. Only scheduled `money_flow_v1_2_baseline` synthetic `paper_opened` rows may create Hyperliquid testnet lifecycle rows, and those rows use fixed 25 USDC notional independent of synthetic signal size. Candidate, MF-ORIG, and wildcard lanes remain synthetic-only. Public mainnet candles remain strategy truth, testnet fills do not update synthetic PnL, no live trading is approved, no strategy is production-approved, and production Money Flow rules are unchanged.

2026-05-17 - PT-RT1.5.1 Signed Testnet Transport, Warm-Start Gate, And Open MTM

PT-RT1.5.1 archives the pre-warm-start PT-RT1.5 smoke rows as `pt_rt1_5_smoke_pre_warm_start_gate` and defaults fresh review/runtime control to `pt_rt1_5_1_smoke`. The new warm-start gate records startup-valid entry confirmations but blocks synthetic opens and testnet orders until the context resets false and a fresh post-start Money Flow v1.2 baseline signal appears on a scheduled closed-candle evaluation. Signed Hyperliquid testnet transport is wired behind exact PT-RT1.5.1 approval and local sandbox env only, with live URL rejection, account-targeting/vaultAddress rules, duplicate testnet order keys, fixed 25 USDC notional, and lifecycle endpoint-called flags. Open synthetic positions now mark to public mainnet mids or latest closed candles and display `MTM unavailable` instead of fake zero when no price is available. Candidate, MF-ORIG, and wildcard lanes remain synthetic-only. Public mainnet candles remain strategy truth, testnet fills do not update synthetic PnL, no live trading is approved, no strategy is production-approved, and production Money Flow rules are unchanged.

2026-05-17 - Obsidian Current-Truth Cleanup

The Obsidian brain now treats Paper Trading / PT-RT, SV2.x evidence, SOR/MF-ORIG research, and dashboard founder review as the current path, while UAT and older platform phases are preserved as historical plumbing context. Phase Timeline is current-first, Agent Coordination has separate Active Work and Finished Work sections, duplicate command-center and phase-timeline entrypoints are pointers only, and current-truth notes no longer present manual report loading or old evidence-loaded status text as founder chrome. This is documentation/governance cleanup only; no code behavior, evidence pack, strategy rule, order/private/signed endpoint, API-key use, live approval, or SOR/fanout/CBBO behavior changed.
