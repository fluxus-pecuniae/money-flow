# REPO_TREE

Last reviewed: `2026-06-06T19:47:41Z`

## Top-Level Structure

```text
.
├── .archiveignore
├── .codex/
├── .env.example
├── .gitignore
├── AGENTS.md
├── CHANGELOG.md
├── DESIGN.md
├── KNOWN_ISSUES.md
├── TODO.md
├── REPO_TREE.md
├── money_flow_project_memory.md
├── README.md
├── apps/
├── core/
├── configs/
├── db/
├── docs/
├── infra/
├── money-flow/
├── scripts/
├── services/
└── tests/
```

## Responsibilities By Area

`.gitignore`
- Source-control hygiene guard for the `master` baseline.
- Excludes local secrets, virtualenvs, caches, local database/runtime state, logs, review bundles, handoff archives, generated strategy-validation evidence packs, Obsidian app state under `/money-flow/.obsidian/`, OS/editor files, and build artifacts while keeping `.env.example`, sample configs, and tracked Obsidian markdown notes trackable.

`.archiveignore`
- Review-bundle hygiene guard consumed by `scripts/create_review_bundle.py`.
- Excludes Git metadata, local secrets, virtualenvs, caches, generated archives, generated strategy-validation evidence packs, database/socket state, and Obsidian app state such as `money-flow/.obsidian/` from handoff ZIPs while keeping sample configs and tracked Obsidian markdown notes reviewable.

`.codex/`
- Project-scoped Codex workflow configuration.
- SUBAGENTS1 adds `.codex/agents/runtime_reviewer.toml`, `.codex/agents/dashboard_reviewer.toml`, and `.codex/agents/quant_reviewer.toml` as read-only-by-default review agents for PT-RT runtime safety, founder dashboard clarity, and paper-trade/quant review.
- `.codex/config.toml` sets conservative local subagent limits: `max_threads = 3` and `max_depth = 1`.

`DESIGN.md`
- Root pointer only.
- Points dashboard designers/operators to the canonical dashboard design system at `apps/dashboard/DESIGN.md`.

`configs/strategy_validation/`
- Strategy Validation research campaign configs.
- SV1.3 adds `money_flow_research_campaign.example.json` as a non-secret sample showing explicit symbols, components, fill timings, named windows, fees/slippage, capital, sizing, output directory, report formats, and the `(start_at, end_at]` candle-close window convention.
- SV1.4 adds `configs/strategy_validation/campaigns/` with canonical editable Money Flow evidence campaigns, currently `money_flow_core_btc.json` and `money_flow_core_multi_symbol.json`, for founder/operator review and data-readiness auditing. These configs contain no secrets and require only persisted historical candles.
- The 2026-05-05 SV1.12.4 research pass labels the January `money_flow_core_btc.json` / `money_flow_core_multi_symbol.json` configs as archival/vendor-data-required rather than the public Hyperliquid first-evidence baseline, because public January 2026 `15m` candles were unavailable.
- SV1.12.4 adds `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json`, a public-data-friendly BTC/ETH/SOL plan using `1h`/`4h` 2026 YTD and recent 51-day `15m` public Hyperliquid data. It is a data-preparation/import-readiness config and not a paper/live trading or evidence-pack-generation config.
- SV1.12.5 adds `configs/strategy_validation/campaigns/money_flow_supported_venues_public_ytd_recent.json`, a supported-adapter public candle-readiness plan covering Hyperliquid, Aster, Binance, OKX, Coinbase Advanced Trade, and Kraken. It records which public sources produced candidate files, which sources lack trade counts, and which sources are incomplete; it is not an executable evidence, paper/live trading, or import config.
- SV1.12.5 operator-approved Hyperliquid import uses `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json` as the immediate 9-file public campaign baseline. The January 18-file configs remain archival/vendor-data-required and are not the public first-import baseline.
- SV1.12.5.1 closes the import state by verifying the intended local `money_flow` DB contains the operator-approved 9-file Hyperliquid public campaign candle import (`25848` rows) and that no evidence packs have been generated before SV1.13.
- SV1.13 uses `configs/strategy_validation/campaigns/money_flow_hyperliquid_public_ytd_recent.json` as the first public evidence baseline and expands its component-specific `timeframe_windows` into three component-scoped evidence configs. Generated evidence packs are written under ignored `reports/strategy_validation/` paths and are summarized in `docs/strategy_validation_sv1_13_hyperliquid_public_evidence_review.md`.
- SV1.13.1 adds the founder interpretation layer for those existing evidence packs, clarifying grouped aggregate semantics, scenario-level fill/cost/drawdown truth, and ETH `sleeve_1h` concentration without regenerating evidence packs or changing strategy rules.
- SV1.13.2 adds `dynamic_equity_pct` capital sizing to Strategy Validation while preserving `constant_initial_capital_notional_per_trade` as the default. Dynamic evidence remains Hyperliquid-only and scenario-level; it does not import candles, generate evidence packs, change Money Flow rules, or create paper/live/routing artifacts.
- SV1.14 keeps the same public campaign/evidence baseline and adds trade-anatomy / market-structure diagnostics over existing evidence packs and imported candles. It does not alter campaign configs or Money Flow rules.
- SV1.15 keeps the same Hyperliquid public dynamic-equity evidence baseline and adds controlled research-only hypothesis experiments. It does not alter campaign configs, production Money Flow rules, paper/live behavior, routing, or execution.
- SV1.15.1 hardens experiment methodology truth by labeling completed-trade overlays, reporting-only attribution, deferred rejected-signal replay variants, and lookahead diagnostic proxies so SV1.15 results are not mistaken for true forward replays or authorized rule changes.
- SV1.16 adds per-candle rejected-signal context and a research-only chronological true replay substrate over the same Hyperliquid public campaign. The first narrow lower-RSI trend-intact replay example uses `dynamic_equity_pct`, preserves position occupancy, and does not alter campaign configs or production Money Flow rules.
- SV1.16.1 hardens replay methodology truth by adding explicit production-rule-in-replay-state field semantics, variant-divergence metadata, and separated production-rule rejection / variant-admitted-from-rejection / variant no-trade counters without changing production Money Flow rules.
- SV1.17 adds true replay experiment reporting for lower-RSI plus market-structure variants, expanded to the full Hyperliquid public BTC/ETH/SOL x 15m/1h/4h matrix under `dynamic_equity_pct`. It does not alter campaign configs, production Money Flow rules, paper/live behavior, routing, or execution.
- SV1.18 closes the current evidence cycle and freezes exactly one UAT observation candidate, Hyperliquid ETH `sleeve_1h` baseline current rules, while excluding 15m/4h/lower-RSI/market-structure/cross-venue candidates from current UAT scope. It is closeout and UAT planning only, not a campaign config change, import, evidence-pack generation, paper/live approval, routing, or execution.
- SV2.0 adds `configs/strategy_validation/campaigns/money_flow_sv2_0_hyperliquid_public_2025_expanded.json`, the Money Flow v1.2 expanded public-mainnet evidence config. It covers BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, and SHIB across `sleeve_15m`, `sleeve_1h`, `sleeve_4h`, and `sleeve_1d`, records the Jan 2025 target start, uses `dynamic_equity_pct`, and explicitly keeps testnet data out of strategy truth.
- SV2.0.2 adds `configs/strategy_validation/campaigns/sv2_0_2/` with 36 canonical DB-imported Money Flow v1.2 evidence configs: one per supported symbol/timeframe for BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, and AVAX across `15m`, `1h`, `4h`, and `1d`. The regenerated configs use each pair/timeframe's full available imported window, `dynamic_equity_pct` with 10000 USDC initial equity per independent scenario, explicit fee/slippage and no-testnet-strategy-truth boundaries, and exclude/defer SHIB/kSHIB from executable canonical evidence because unit semantics are not clean enough.
- SV2.1 adds `scripts/run_sv21_broad_1d_period_evidence.py`, `scripts/build_sv21_broad_1d_historical_replay.py`, `docs/sv2_1_broad_hyperliquid_1d_period_evidence.md`, and `docs/sv2_1_broad_hyperliquid_1d_period_evidence_summary.json` for founder-approved Hyperliquid public-mainnet 1D period evidence plus dashboard Historical Replay artifacts. Generated raw candles and generated period campaign configs remain local under `/tmp/money-flow-sv21-broad-1d/`; generated baseline/candidate evidence packs and selected chart/trade JSON remain ignored under `reports/strategy_validation/`. The rejected broad active-metadata run was removed from local generated outputs and replaced by the founder-approved PT-RT1 requested/resolved universe: BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, TRX, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, and TRUMP. PEPE/kPEPE and OKB are excluded by resolver policy. The 2026-05-15/16 rebuild imported public 1D candles back to 2024-01-01 where available, generated 90 baseline period packs across 2024, 2025, YTD, and ALL, then wrote 1800 selected replay chart JSON files and 810 evidence-only candidate/reference/wildcard pack directories covering all 10 PT-RT1 paper-observation lanes for founder review without changing Money Flow rules or approving paper/live. ASTER and TRUMP have no 2024 period pack because public candles do not cover that period.
- SV1.11 adds `configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json`, an offline/manual manifest for research-only BTC/ETH/SOL Hyperliquid perpetual USDC `instruments` and `symbols` rows required before candle imports. SV1.11.1 marks the example as requiring operator verification before non-dry-run writes, SV1.11.2 keeps the research seed non-trading by rejecting true strategy/trading eligibility, and the 2026-05-05 SV1.12.x research pass updates the manifest with public Hyperliquid `meta`-verified asset ids, size decimals, leverage, margin table ids, and derived tick/step values while leaving operator verification and trading/strategy eligibility false.

`money-flow/`
- Tracked Obsidian strategic brain.
- Contains the canonical command center, current phase, decision log, agent coordination, component/workflow maps, Strategy Validation map, UAT roadmap, UAT candidate freeze note, UAT0 safety/runtime hardening note, and the moved full project memory.
- OB1.0 reorganizes current truth so `money-flow/00_Money_Flow_Command_Center.md` is the only canonical command center; `money-flow/Money Flow Command Center.md` is a compatibility pointer. Strategy Validation is represented as its own closed major track through SV1.18.1, and UAT0 is the next proposed track.
- UAT0 updates the current-state notes after the safety/security/runtime audit: UAT0 audit is complete, UAT1 read-only connectivity is blocked by named safety gaps, the future UAT observation universe is top-20 supported assets, and UAT2 fill timing must compare `next_candle_open` and `next_candle_close` while keeping `same_candle_close_research_only` research-only.
- UAT0.1 updates current-state notes after the P0 API auth/authz and runtime lockout hardening: sensitive `/api/v1` routes require scoped bearer auth, a central fail-safe runtime safety policy is inspectable, UAT1 remains blocked by remaining P1 safety gaps, and no exchange connectivity/order submission/paper/live behavior is added.
- UAT0.2 updates current-state notes after adapter runtime-policy hardening: adapter private/signed/order paths are guarded before transport, public read-only methods are classified, a Hyperliquid future-UAT1 read-only allowlist artifact exists, representative redaction is tested, and no exchange connectivity/order submission/paper/live behavior is added.
- UAT0.3 updates current-state notes after top-20 universe/drawdown readiness preflight: fixture-tested top-20 resolver policy, Hyperliquid public read-only info-type allowlisting, and runtime drawdown monitor design exist; UAT1 public read-only connectivity may proceed under strict no-private/no-signed/no-order/no-API-key constraints.
- UAT1 updates current-state notes after public read-only connectivity and top-20 universe resolution: explicit public-read-only network mode was used, Hyperliquid allowed public info types were verified, a public no-key CoinGecko top-volume source was fetched, Hyperliquid-supported observation-only assets were resolved, and UAT2 remained blocked at that point by shadow-readiness gaps. No private/signed/order endpoints, API keys, order submissions, Money Flow live strategy execution, paper/live behavior, routing behavior, Money Flow rule changes, or evidence packs were added.
- UAT1.1 updates current-state notes after shadow-readiness hardening: model/report-only shadow signal audit records, operator-visible shadow drawdown, UAT1 universe snapshot loading, and representative API-error / structured-log redaction verification exist.
- UAT2 updates current-state notes after the bounded no-order shadow run: the UAT1 observation-only universe was evaluated across `sleeve_15m`, `sleeve_1h`, and `sleeve_4h` using public Hyperliquid candle snapshots, shadow audit records were emitted, and later UAT3.0 sandbox order design/readiness completed while UAT3.1 actual sandbox submission remains blocked.
- UAT2.1 updates current-state notes after dashboard visualization/readiness work: the static dashboard now loads the UAT2 summary JSON, displays shadow signal/reason/timing/drawdown/boundary panels, and shows UAT3 as blocked without adding approval/order actions.
- UAT3.0 updates current-state notes after sandbox-order design/readiness work: the future initial sandbox subset is narrowed to Hyperliquid ETH `sleeve_1h`, the founder/operator approval template and lifecycle/risk/drawdown/submit-lease requirements are documented, the dashboard adds an informational design panel, and UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.1 updates current-state notes after sandbox runtime / approval / risk readiness hardening: fixture-only validators now cover fail-closed sandbox runtime policy, sandbox artifact labels, actual-submission approval scope, sandbox risk gates, sandbox drawdown feed fixtures, and submit-lease duplicate-prevention checks. UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.2 updates current-state notes after sandbox gate integration dry-run / policy hardening: risk gates now propagate all sandbox runtime-policy blockers, non-positive quantity/notional/limit/drawdown values are rejected, and the unified dry-run sandbox gate preflight combines runtime, labels, approval scope, risk, drawdown, and submit-lease checks. UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.3 updates current-state notes after sandbox gate wiring / label-enforcement hardening: sandbox artifact boundary validators cover persistence/API/dashboard/report helper surfaces, and a dry-run executable gate service composes runtime, boundary labels, approval scope, risk gates, drawdown status, and submit-lease checks. UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.4 updates current-state notes after sandbox private read-only drawdown readiness: private read-only sandbox account policy, credential approval/boundary validation, endpoint category separation, redaction helpers, and sandbox account drawdown feed modeling exist. The required private read-only credential approval was not present, so no credentials were used and no private endpoints were called. UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.5 updates current-state notes after sandbox/testnet private read-only credential and drawdown verification: exact private-read-only approval is present, sandbox/testnet credential/base-URL verification helpers exist, one Hyperliquid testnet read-only account-state request returned HTTP 200, the sandbox account drawdown feed is `sandbox_drawdown_feed_live_fed_verified`, and order-capable categories remain blocked. No API key/private key was sent, no order endpoint was called, and UAT3.1 actual sandbox submission remains blocked.
- UAT3.0.6 updates current-state notes after sandbox submit path dry-run wiring: a non-persistent sandbox submission plan and dry-run gate chain now compose actual-submission approval, live-fed drawdown status, approval scope, risk gates, submit-lease duplicate prevention, endpoint classification, and sandbox artifact-label boundary validation without creating order artifacts or calling exchanges. UAT3.1 actual sandbox submission remains blocked.
- UAT3.1 updates current-state notes after the first approval-gated sandbox/testnet lifecycle probe: exact founder/operator approval was verified, one Hyperliquid testnet ETH post-only limit order attempt under 10 USDC notional was made, the venue rejected the request with a sanitized user/API-wallet-not-found response, no cancel was required, reconciliation found no open order, and no production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, routing expansion, Money Flow rule change, or evidence pack was created.
- UAT3.2 updates current-state notes after the fixed-key preflight / second approval-gated sandbox lifecycle attempt: exact founder/operator approval was verified, fixed-key account/API-wallet readiness blocked before order transport because the testnet user/API wallet was still not recognized/authorized and account equity was insufficient, zero order attempts were made, no order/cancel/amend/retry endpoint was called, and the future UAT4.0 dashboard chart cockpit request was captured as roadmap-only.
- UAT3.3 updates current-state notes after Hyperliquid account targeting and tick/lot precision hardening: normal master/user mode omits `vaultAddress`, subaccount/vault mode uses only the explicit configured target, the API-wallet signer remains separate from the target account, ETH price/size are formatted with Hyperliquid precision rules, and a later founder-approved follow-up verified one accepted/open ETH testnet order, successful cancel, and no-open-order reconciliation.
- UAT3.4 updates current-state notes after sandbox routing operationalization: the working ETH testnet route is represented as `fixed_target_hyperliquid_testnet_eth`, routed sandbox order ledger records exist, active account mode is normal user with `vaultAddress` omitted, standard perp clearinghouse equity is selected for the current route, unified/portfolio spot-clearinghouse USDC fallback remains supported, and the dashboard exposes routed-order ledger visibility without adding order controls.
- UAT4.0 updates current-state notes after the live UAT dashboard/chart cockpit: the static dashboard now exposes a read-only UAT Chart Cockpit from committed UAT2/UAT3.4 JSON summaries, including watchlist, market-data coverage, chart snapshot, indicators, shadow/sandbox markers, route/equity cards, routed-order ledger filters, and persistent no-order-control safety labeling.
- UAT4.2 updates current-state notes after live-market monitoring and internal paper-equity visibility: the dashboard now loads a UAT4.2 monitor summary JSON with public-read-only market rows, deterministic indicator snapshots, paper-observation scanner records, 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger while still adding no order controls or order endpoints.
- Phase 8.0.1 accepted the previously dirty Obsidian memory refresh as the strategic baseline and updated it to current Phase 8.0/8.0.1 truth.
- Phase 8.0.2 updates current-phase/coordination/decision notes for active submit-lease operator-summary truth only; full project memory remains untouched.
- SV1.0.1 updates current-phase/coordination/decision notes for strategy-validation research-truth/report hardening only; full project memory remains untouched.
- SV1.1 updates current-phase/coordination/decision notes for comparative strategy-validation batch reporting only; full project memory remains untouched.
- SV1.2 updates current-phase/coordination/decision notes for market-regime and data-coverage strategy-validation reporting only; full project memory remains untouched.
- SV1.2.1 updates current-phase/coordination/decision notes for window-boundary, coverage, and grouped-comparison research-truth hardening only; full project memory remains untouched.
- SV1.3 updates current-phase/coordination/decision notes for repeatable Money Flow research campaign/evidence-pack workflow only; full project memory remains untouched.
- SV1.4 updates current-phase/coordination/decision notes for evidence-pack review discipline and data-readiness baseline only; full project memory remains untouched.
- SV1.4.1 updates current-phase/coordination/decision notes for evidence-pack collision/overwrite integrity only; full project memory remains untouched.
- SV1.5 updates current-phase/coordination/decision notes for historical data-readiness and first canonical evidence-pack support only; full project memory remains untouched.
- SV1.5.1 updates current-phase/coordination/decision notes for candle-import and campaign-config research-truth hardening only; full project memory remains untouched.
- SV1.6 updates current-phase/coordination/decision notes for first canonical evidence-review summaries only; full project memory remains untouched.
- SV1.7 updates current-phase/coordination/decision notes for first real canonical evidence-review/data-gap reporting only; full project memory remains untouched.
- SV1.8 updates current-phase/coordination/decision notes for historical-data bootstrap and DB/schema/migration truth only; full project memory remains untouched.
- SV1.8.1 updates current-phase/coordination/decision notes for evidence-review schema-gate/report-truth only; full project memory remains untouched.
- SV1.9 updates current-phase/coordination/decision notes for intended strategy-validation DB target truth, canonical candle import requirements, and first-real evidence status only; full project memory remains untouched.
- SV1.10 updates current-phase/coordination/decision notes for intended local DB creation/migration truth, canonical candle import requirement grouping, and first-real evidence status only; full project memory remains untouched.
- SV1.11.2 updates current-phase/coordination/decision/current-state/roadmap notes for market-identity non-trading guard and complete requirement-aware preflight mapping only; full project memory remains untouched.
- SV1.12 updates current-phase/coordination/decision/current-state/roadmap notes for guarded canonical candle bundle import only; full project memory remains untouched.
- SV1.12.1 updates current-phase/coordination/decision/current-state/roadmap notes for guarded import run truth, explicit partial-persistence reporting, and operator-visible unmapped/missing requirement output only; full project memory remains untouched.
- SV1.12.2 updates current-phase/coordination/decision/current-state/roadmap notes for identity and canonical candle-file readiness only; full project memory remains untouched.
- SV1.12.3 updates current-phase/coordination/decision/current-state/roadmap notes for the guarded import attempt, blocked identity/file status, and no-evidence-pack boundary only; full project memory remains untouched.
- SV1.12.4 updates current-phase/coordination/decision/current-state/roadmap/strategy-lab/project-memory notes for the public YTD/recent Hyperliquid data campaign, while preserving the no-seed/no-import/no-evidence-pack boundary.
- SV1.12.5 updates current-phase/coordination/decision/current-state/roadmap/strategy-lab/project-memory notes for supported-venue public candle readiness, then updates current-phase/coordination/decision/current-state/roadmap notes again for the operator-approved Hyperliquid 9-file public campaign import. Full project memory remains untouched by the import bridge.
- SV1.12.5.1 updates command/current-phase/decision/coordination/current-state/roadmap/timeline/project-memory notes for repo and import-state closeout before SV1.13 evidence generation.
- SV1.13 updates command/current-phase/decision/coordination/current-state/roadmap/timeline/project-memory notes for first Hyperliquid public campaign evidence packs and keeps paper/live trading deferred.
- SV1.13.1 updates command/current-phase/decision/coordination/current-state/roadmap/timeline/project-memory notes for evidence interpretation truth and founder review readiness while preserving the no paper/live/routing/execution boundary.
- SV1.14 updates command/current-phase/decision/coordination/current-state/roadmap notes for trade anatomy and descriptive market-structure diagnostics while preserving no-rule-change/no-paper-live/no-routing boundaries.
- SV1.15 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for controlled research-only hypothesis experiments while preserving no-rule-change/no-paper-live/no-routing boundaries.
- SV1.15.1 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for experiment methodology truth, including the recent-low lookahead proxy downgrade and completed-trade overlay limitations.
- SV1.16 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for rejected-signal replay instrumentation and a narrow lower-RSI true replay substrate while preserving no-rule-change/no-paper-live/no-routing boundaries.
- SV1.16.1 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for replay context semantics and variant metric truth hardening while preserving no-rule-change/no-paper-live/no-routing boundaries.
- SV1.17 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for true replay experiment round one while preserving no-rule-change/no-paper-live/no-routing boundaries.
- SV1.18 updates command/current-phase/decision/coordination/current-state/roadmap/project-memory notes for evidence-cycle closeout and one UAT observation candidate freeze while preserving no-rule-change/no-paper-live/no-routing/no-exchange-call boundaries.
- OB1.0 updates Obsidian brain structure and operational-doc drift tests only. It adds `00 Maps/Strategy Validation Map.md`, `00 Maps/UAT Roadmap.md`, `00 Maps/Platform Architecture Map.md`, top-level product/timeline pointers, Strategy Validation summary/closeout/candidate notes, UAT0 safety/runtime hardening, agent workflow, and review-bundle hygiene notes. It changes no product behavior.
- Obsidian app state under `money-flow/.obsidian/` remains ignored.

`apps/api/`
- FastAPI control plane.
- Operator inspection and action endpoints for mandates/runtime, planning, non-executing routing assessments, route-readiness/data-sufficiency audits, controlled non-executing routing target recommendations, explicit recommendation acceptance into non-executing routing target choices, explicit target-choice-to-child-intent conversion, routed child-intent preparation/readiness inspection, explicit gated routed child-intent submission, routed submitted-order lineage, post-submit lifecycle/actionability, reconciliation and lifecycle-event audit inspection, read-only routed workflow aggregation, Phase 7.0 non-executing routing automation policy / dry-run plan inspection, Phase 7.1 durable routing automation approval / revocation / administrative consumption gate inspection, Phase 7.1.2 approvable-step policy truth, Phase 7.2 / 7.2.1 approval-gated recommendation acceptance into target choice only with coherent approval consumption, Phase 7.3 approval-gated target-choice conversion into one child intent only, Phase 7.4 approval-gated prepared-order preview/readiness inspection only, Phase 7.5 approval-gated submitted-order handoff through the existing explicit submit path only, Phase 7.5.1 post-submit approval-consumption pending truth, Phase 7.6 closeout regression coverage over the existing Phase 7 surfaces, execution readiness, submitted-order lifecycle, recovery, cancel, amendability/actionability, adapter/runtime session state, and private order/account-state visibility.
- UAT0.1 protects `/api/v1` with scoped bearer authentication by default. Read-only inspection requires `read_only_operator`; strategy/evaluation/planning/routing mutation surfaces require `operator`; account/private-state/exchange-sync/submit/cancel/amend/recovery surfaces require `admin`; approval consume and non-submit approval action hooks require `automation_admin` or `admin`; explicit submitted-order handoff requires `admin`. A test-only auth bypass is allowed only with `API_RUNTIME_MODE=test` and `API_AUTH_DISABLED_FOR_TESTS=true`.

`apps/dashboard/`
- Static local Strategy Validation evidence dashboard for founder/operator review.
- Loads ignored local SV2.0.2 canonical evidence `batch_report.json` files plus generated dashboard chart/trade JSON from `reports/strategy_validation*` when served from the repo root, or accepts manual JSON file selection in the browser.
- Uses the root design tokens/variables when present and keeps visualization read-only: no evidence-pack generation, candle import, paper/live approval, exchange endpoint calls, or Money Flow rule changes.
- SV1.14 tightens labels so component cards are clearly sums across research runs and run rows are scenario results. The Strategy tab states RSI lower-floor entry truth and that market-structure diagnostics are not entry filters.
- SV1.15/SV1.15.1 added static controlled-hypothesis internals, but the invalid legacy Experiments surface is no longer exposed as a dashboard tab.
- SV1.16 and SV1.17 replay internals remain historical code/data context only, separate from Evidence-tab evidence-pack/review data. The visible dashboard remains visualization-only for local evidence and replay artifacts.
- SV1.18 adds no dashboard runtime behavior; UAT closeout remains a founder-readable docs/reporting layer.
- UAT0 adds no dashboard runtime behavior; future dashboard/operator visibility for top-20 shadow observation remains a UAT2 prerequisite.
- UAT2.1 adds the `UAT2 Shadow Run` tab. It loads `docs/uat2_shadow_strategy_top20_observation_summary.json`, renders summary cards, a filterable signal matrix, would-open inspection, no-trade reason breakdowns, the ETH evidence-candidate card, timing/drawdown panels, no-artifact boundary flags, and an informational UAT3 blocked readiness checklist. It creates no approval action, order intent, submitted order, exchange call, paper/live behavior, routing behavior, or Money Flow rule change.
- UAT3.0 adds an informational UAT3.0 sandbox design panel to the same UAT dashboard view. It shows the narrow ETH `sleeve_1h` sandbox subset, actual sandbox submission as not approved, founder approval as required, sandbox account drawdown feed as missing, and approval/submit-lease/lifecycle verification as designed but not complete. It adds no active order-submission or approval control.
- UAT3.0.1 updates that panel with fixture/readiness status for sandbox runtime policy, sandbox artifact label validation, approval scope validation, risk gates, sandbox drawdown feed fixtures, and submit-lease duplicate-prevention checks. It still adds no active order-submission or approval control.
- UAT3.0.2 updates that panel with unified dry-run preflight, runtime full-blocker propagation, numeric edge-case validation, missing actual sandbox approval, fixture-only drawdown, and missing artifact-label persistence enforcement. It still adds no active order-submission or approval control.
- UAT3.0.3 updates that panel with artifact label boundary enforcement, dry-run executable gate service, approval/risk/submit-lease dry-run wiring, runtime policy semantics, missing actual sandbox approval, fixture-only drawdown, and missing real sandbox submit path truth. It still adds no active order-submission or approval control.
- UAT3.0.4 does not update the dashboard. Private read-only sandbox drawdown readiness remains documented/tested only and still adds no active order-submission or approval control.
- UAT3.1 does not update the dashboard. The one-shot lifecycle probe is documented in `docs/uat3_1_first_sandbox_order_attempt.md` and has no general dashboard order button or repeated-order control.
- UAT3.4 adds a routed-orders visibility section to the UAT dashboard. It loads `docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json`, shows run/route/lifecycle/cancel/reconcile/equity-source/sandbox-label truth, and still has no order button, repeated-order control, live control, or approval action.
- UAT4.0 adds the read-only UAT Chart Cockpit from committed UAT2/UAT3.4 summaries.
- UAT4.1 rebuilds that cockpit into an exchange-style workstation with compact top bar, left market rail, central chart cockpit, right order-book/market/signal/risk rail, bottom blotter tabs, and the canonical `apps/dashboard/DESIGN.md` design system. It remains local-summary-only and adds no order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls.
- UAT4.2 wires the cockpit to `docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json`, showing refreshed public-read-only market data, deterministic indicators, paper-observation markers, internal paper-equity state, sandbox balance-poll policy, and explicit positions/unavailable-state visibility. It still adds no order, cancel, retry, amend, approval, live, route, or auto-trade controls.
- PT0 adds the official local TradingView Lightweight Charts bundle for the UAT/PT cockpit and browser-side Hyperliquid testnet public candle polling.
- PT0.0.1 stabilizes the TradingView chart by bounding chart height, containing parent chart layout, reusing chart/series handles across 15-second public refreshes, removing the `autoSize` / ResizeObserver `applyOptions` feedback-loop risk, limiting `fitContent()` to new symbol/timeframe initialization, and adding query flags to disable public polling while using local PT0/UAT4.2 JSON fallback. It adds no order controls and calls no private/signed/order/live endpoints.
- PT0.0.2 adds a separate `Historical Replay` tab. It loads historical replay summaries, renders historical BTC/ETH/SOL replay candles through TradingView Lightweight Charts, overlays EMA5/EMA10/SMA20 and historical entry/exit markers, shows a trade inspector, dynamic 10,000 USDC equity panel, BTC/ETH/SOL comparison table, and keeps the UAT3.4 sandbox execution ledger separate. The tab now includes a replay-strategy dropdown for `OG replay / strategy`, research-only `MACD removed`, and research-only `Only close on 5/20 cross` across all BTC/ETH/SOL x 15m/1h/4h combinations. Historical/mainnet public candle replay data is strategy truth; Hyperliquid testnet prices are not strategy truth.
- PT0.0.3 updates `Historical Replay` to prefer `docs/pt0_0_3_historical_strategy_replay_summary.json`, keeps the PT0.0.3 payload from being overwritten by PT0.0.2 fallback data, adds `1D` timeframe selection, displays Jan 2025 target-start data-horizon truth, and labels 1D as deterministic aggregation from 4h historical replay candles rather than a new production Money Flow sleeve. The dashboard still has no order controls and does not call private/signed/order/live endpoints.
- SV2.0 updates the dashboard Strategy and Historical Replay surfaces to display Money Flow v1.2, the real `sleeve_1d`, expanded Hyperliquid public-mainnet readiness/evidence rows, and explicit SHIB -> `kSHIB` alias truth from `docs/sv2_0_historical_data_refresh_summary.json`. Expanded symbols without full replay chart payloads are shown as readiness/evidence rows instead of being silently substituted with another chart. The dashboard still has no order controls and does not call private/signed/order/live endpoints.
- SV2.0.2 updates the Historical Replay data-horizon/status surfaces to show canonical evidence-pack status, DB-import truth, evidence-pack count, compact-replay noncanonical truth, and SHIB/kSHIB deferred status from `docs/sv2_0_historical_data_refresh_summary.json`. The follow-up display fix loads ignored SV2.0.2 chart/trade JSON for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX across 15m/1h/4h/1d, removes the invalid Experiments tab, keeps arrow descriptions off by default, and keeps the dashboard free of order controls/private/signed/order/live endpoint calls. The SOR-EV3 rolling-range replay follow-up extends the ignored chart-data generator so `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` are available as research-only Historical Replay strategies across all 9 supported symbols, 4 timeframes, and both fill assumptions.
- SOR-EV2.1 adds a visible `Evidence Lab` tab that loads committed SOR-EV1/SOR-EV2 summary bundles, labels canonical SV2.0.2 DB-imported evidence as baseline, and renders variant matrix, control-pocket impact, worst trades, late-entry analysis, large adverse-candle context, RSI/MACD rejection visibility, methodology warnings, and date-filter noncanonical warnings. SOR-EV2.2 adds the Evidence Lab baseline-vs-variant chart overlay, overlay controls, baseline SV2.0.2 entry/exit markers, linkable SOR-EV2 variant/context markers, worst-trade focus, control-pocket view, and explicit unavailable states for missing exact overlay data. SOR-EV3 adds a focused founder-candidate section for `avoid_sideways_low_volatility`, loading `docs/sor_ev3_avoid_sideways_low_volatility_summary.json` and displaying baseline parity, blocked signals vs matched baseline trades, avoided losers, missed winners, and control-pocket damage. These are UI/visualization only and do not approve variants, mutate Money Flow rules, submit orders, regenerate evidence packs, or call private/signed/order/live endpoints.
- MF-ORIG-EV2 extends the Historical Replay and Evidence Run Ledger loaders to auto-load ignored local chart/trade JSON from `reports/strategy_validation/mf_orig_ev2_dashboard_chart_data/20260513T002746Z/` when present. The replay strategies now cover four source-faithful 1% risk-sizing Original Money Flow hypotheses plus four full-equity/notional comparison counterparts across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and both fill assumptions. Evidence Lab now prefers `docs/mf_orig_ev2_multitimeframe_evidence_summary.json` after the EV1.1 fallback and labels MF-ORIG evidence as evidence-only with no production approval.
- The 2026-05-13 selected-scenario loader hotfix keeps compact Historical Replay rows lightweight while loading candles, indicators, markers, and trades from deterministic per-scenario JSON files under ignored `reports/strategy_validation/*/selected/` paths. The SV2.0.2 and MF-ORIG-EV2 chart-data builders now write those selected replay files in addition to combined symbol/timeframe bundles, so founder-selected charts do not depend on loading large multi-replay JSON bundles.
- EV-AUDIT1 adds an audit-only founder review report and compact JSON summary for the full current evidence estate. It inventories Money Flow v1.2, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and pending STRAT-EV1 plan-only status; audits SV2.0.2 data and backtest methodology; ranks biggest winners, losers, and losing streaks; reports regime/control-pocket attribution; and states that no clean strategy candidate is promoted. It does not regenerate evidence packs, change production rules, approve paper/live, submit orders, or call private/signed/order endpoints.
- OB2.0 refreshes the Obsidian strategic brain around one canonical command center and dedicated current maps/registers: `00 Maps/Strategy Family Map.md`, `00 Maps/Evidence and Backtesting Map.md`, `00 Maps/Data Source and Market Data Map.md`, `00 Maps/Dashboard and UI Map.md`, `00 Maps/Paper Observation Roadmap.md`, `10 Strategy/Strategy Status Register.md`, `10 Strategy/Original Money Flow Source Notes.md`, and `20 Evidence/EV-AUDIT1 Summary.md`. It also stores the Gerald Peters source PDF at `money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf`. OB2.0 is documentation/governance only; it changes no production strategy code, regenerates no evidence/chart data, calls no exchanges, and approves no paper/live behavior.
- The 2026-05-17 Obsidian cleanup makes the brain current-first: Paper Trading / PT-RT, SV2.x evidence, SOR/MF-ORIG research, dashboard founder review, and governance lead the current maps; UAT and earlier platform phases are preserved as historical plumbing context. `money-flow/00 Maps/Phase Timeline.md` is current-first, `money-flow/05_Agent_Coordination.md` has Active Work and Finished Work sections, and duplicate command-center/timeline entrypoints are pointer-only.
- PT-RT1 adds the runtime view now surfaced to the founder as `Paper Trading` and still implemented internally with the `paper-observation` view id. It is backed by `docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json`. PT-RT1.1A expands that view before the 24-hour run to show exactly 10 independent synthetic strategy lanes, founder-requested scanner symbols, blocked symbol reason codes, lane detail, wildcard diagnostics, and separate testnet plumbing status. PT-RT1.1B adds public-mainnet connection status, and PT-RT1.1C lets the dashboard prefer the active ignored runtime summary from `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` before the PT-RT1.1B smoke/readiness fallbacks. The Paper Trading browser also polls public mainnet `allMids` and selected-pair `candleSnapshot` for display, while PT-RT1.3 treats mids as warning-only when clean fully closed candles are available. Signal Generation loads recent `paper_opened` rows directly from ignored PT-RT `decisions.jsonl` files when present, so prior signals remain visible even if the latest runtime summary cycle has no new opens. PT-RT1.5 made `pt_rt1_5_week1_active` the active Week 1 scope and added candle-close scheduler/testnet lifecycle status. PT-RT1.5.1 added warm-start gate counts, signed transport configured/missing status, endpoint-called fields, and public-mainnet MTM. PT-RT1.5.2 defaulted the dashboard to `pt_rt1_5_2_week1_active` and proved the transport smoke reached Hyperliquid testnet but rejected on venue size validation. PT-RT1.5.3 adds lifecycle precision columns and a `pt_rt1_5_3_transport_smoke` source so the dashboard shows asset id, `szDecimals`, raw quantity, formatted quantity, and estimated notional for the fixed-25-USDC testnet size hotfix. The view separates public-mainnet strategy truth from Hyperliquid testnet plumbing, keeps candidate lanes synthetic-only, keeps date filters display-only, and adds no live trading approval, no production strategy changes, and no testnet strategy-PnL truth.
- `scripts/run_dashboard_control_server.py` serves the dashboard from localhost with a tiny Paper Observation control API. Its Start Run path launches `scripts/run_pt_rt1_paper_observation.py` through Mac `caffeinate` using only allowlisted durations/output directories and now defaults to PT-RT1.5.2 Week 1 active scope, `--fresh-signal-only-after-runtime-start`, `--disable-legacy-testnet-probes`, candle-close signal evaluation, fixed 25 USDC baseline-only signed testnet transport gates, `--public-mainnet-only`, and `--decision-log-mode compact`; static dashboard servers leave Start/Stop unavailable. It adds no arbitrary command execution, no private/signed/order endpoint use from strategy truth, no API-key use for strategy truth, and no live/paper production approval. Candidate lanes remain synthetic-only and testnet fills do not update paper PnL.
- `scripts/run_pt_rt1_paper_observation.py` defaults to compact decision logging for ignored runtime `decisions.jsonl`: actionable open/close rows and data-unavailable rows are written, first-seen non-actionable audit context is retained, repeated identical non-actionable rows are suppressed across cycles, and summary/state files record suppression/size stats. `--decision-log-mode full_audit` and `--decision-log-mode signals_only` remain explicit operator modes.
- PT-RT1.2 extends `scripts/run_pt_rt1_paper_observation.py` with persisted runtime paper state in each ignored output directory's `state.json`: processed signal keys, open synthetic positions, realized equity by lane, last processed close by lane/symbol/timeframe, duplicate-open counters, and open/close totals. Repeated same-candle open attempts become held/blocked decisions rather than new `paper_opened` rows, closed synthetic positions append to `trades.jsonl`, and `summary.json` separates public market-data unavailable rows from lane-expanded `data_unavailable` decisions. The script also exposes an explicit fakeable 20 USDC Hyperliquid testnet transport gate behind `--submit-testnet-probes` plus exact PT-RT1.2 transport approval while keeping dashboard-started runs audit/order-shape only.
- PT-RT1.3 changes runtime data-health semantics so Hyperliquid `allMids` gaps are warning-only when fully closed public-mainnet `candleSnapshot` rows are available. Scanner eligibility now relies on supported venue identity and precision rather than mid presence; `summary.json` and `data_health.json` expose `data_health_semantics=candle_strategy_truth`, `mid_health_blocks_strategy=false`, mid-warning counts, and candle/indicator blocking counts.
- PT-RT1.2.1 reorganizes the Paper Observation dashboard as a chart-first founder review surface: the visible Expanded Scanner Universe/watchlist is removed, Signal Generator and synthetic position tables are paginated, Open Synthetic Positions and Closed Synthetic Trades sit directly below Signal Generator, Symbol/Timeframe/Strategy filters apply across chart context, signals, open positions, closed trades, and chart markers, opened/closed synthetic trades render as chart markers, Closed Synthetic Trades loads ignored `trades.jsonl` for full entry/exit/price/quantity/PnL/equity fields, Strategy Lane Comparison overlays `paper_runtime_state.realized_equity_by_lane`, and Wildcard Diagnostics moves to the Strategy tab. It is UI/runtime visibility only and adds no trading behavior.
- PT-RT1.4 makes Paper Trading the weekly command center and cuts active Week 1 scoring to `1h`, `4h`, and `1d`. `15m` is `disabled_for_week1_noise_reduction`, preserved as paused/legacy data, and excluded from default lane comparison, all-active totals, and new synthetic entries after the cutover. Strategy Lane Comparison is selected-timeframe scoped by default, All active is explicitly 1h + 4h + 1d and not one combined account, Open/Closed Synthetic Trade tables are founder-readable, Signal Generator is a categorized paper-decision stream, and the testnet panel separates audit-only shapes from disabled order transport.
- PT-RT1.4.1 verifies the active-week cutover against ignored runtime artifacts and writes the committed daily founder review pack at `docs/pt_rt_week1_day_summary.md` and `docs/pt_rt_week1_day_summary.json`. The older `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` runtime is labeled pre-cutover burn-in because it continued producing 15m opens after cutover; the restarted active runtime writes ignored artifacts under `reports/paper_runtime/pt_rt1_4_1_active_week/` and produced 0 15m rows in its first artifact cycle.
- PT-RT1.5 resets the active Week 1 runtime scope to `reports/paper_runtime/pt_rt1_5_week1_active/`, archives prior runtime scopes by label rather than deleting them, keeps active timeframes at `1h`/`4h`/`1d`, keeps `15m` paused, separates market refresh from strategy signal evaluation, and adds a separate `testnet_order_lifecycle.jsonl` table for Money Flow v1.2 baseline-only fixed 25 USDC Hyperliquid testnet plumbing rows. PT-RT1.5.1 adds `reports/paper_runtime/pt_rt1_5_1_smoke/` as the fresh active smoke scope, warm-start false-to-true entry gating, PT-RT1.5.1 exact approval for signed baseline testnet transport, and open-position MTM fields from public mainnet mids/latest closed candles. PT-RT1.5.2 adds `reports/paper_runtime/pt_rt1_5_2_transport_smoke/` and `reports/paper_runtime/pt_rt1_5_2_week1_active/`, exact PT-RT1.5.2 approvals, one explicit smoke cap, scoped env loading without secret printing, and testnet root/API URL validation. PT-RT1.5.3 adds `reports/paper_runtime/pt_rt1_5_3_transport_smoke/`, exact hotfix-smoke approval, Hyperliquid testnet public metadata resolution for order sizing, invalid-size preflight, and venue invalid-size reason coding.
- DOCS-OB2.1 made the Markdown/Obsidian estate current-first for PT-RT1.5.1. PT-RT1.5.3 updates current truth to accepted/open -> canceled -> reconciled fixed-25-USDC testnet smoke verified, active `1h`/`4h`/`1d`, paused `15m`, public-mainnet strategy truth, independent synthetic ledgers, baseline-only testnet plumbing, and no production/live approval.

`docs/doc_ob2_1_markdown_current_truth_refresh.md`
- Founder/agent report for the DOCS-OB2.1 current-truth Markdown and Obsidian readability refresh.
- Documents scope, files updated, files marked historical, strategy/evidence/dashboard taxonomy, runtime/paper/testnet boundaries, stale wording fixed, and remaining docs debt.

`docs/doc_ob2_1_markdown_current_truth_refresh_summary.json`
- Compact machine-readable summary for DOCS-OB2.1.
- Lists updated files, archival banners, stale phrases fixed, current-truth files, dashboard tabs, strategy families, open docs debt, and validation status.

`docs/pt_rt1_2_runtime_state_and_testnet_probe_transport.md`
- Founder/operator report for PT-RT1.2 runtime state and testnet transport gates.

`docs/pt_rt1_3_candle_truth_data_health.md`
- Founder/operator report for PT-RT1.3 candle-truth data-health semantics and thin/stale-mid false-positive handling.
- Documents the repeated-open fix, persisted state shape, `data_unavailable` rollups, dashboard visibility, 20 USDC transport approval gate, audit-only dashboard default, and no-order/no-live/no-testnet-PnL boundaries.
- The 2026-05-14 dashboard styling checkpoint adds the small local `chillguy-logo.jpeg` brand asset plus theme-aware chart color variables and Historical Replay data-horizon card styling. It is UI styling only and changes no strategy, evidence, endpoint, paper/live, or order behavior.

`docs/pt_rt1_4_paper_trading_command_center_cleanup.md`
- Founder/operator report for PT-RT1.4 Paper Trading command-center cleanup.
- Documents the active Week 1 timeframe cutover to `1h`/`4h`/`1d`, the paused/legacy `15m` policy, timeframe-scoped lane comparison, cleaned open/closed trade tables, categorized paper-decision stream, testnet audit-shape/order-transport label split, active review window, and no-order/no-live boundaries.

`docs/pt_rt1_4_paper_trading_command_center_cleanup_summary.json`
- Compact machine-readable PT-RT1.4 summary.
- Contains active/disabled timeframe policy, active review start, lane comparison scope, table/status cleanup flags, testnet label policy, dashboard section order, boundary flags, and next review guidance without runtime logs.

`docs/pt_rt_week1_day_summary.md`
- Founder-readable PT-RT1.4.1 daily active-week review pack.
- Summarizes runtime cutover verification, lane/timeframe metrics, open/closed synthetic positions/trades, decision/reason-code review, testnet transport audit, dashboard QA, and go/no-go.

`docs/pt_rt_week1_day_summary.json`
- Compact machine-readable PT-RT1.4.1 daily review summary.
- Contains active runtime scope, pre-cutover burn-in labeling, lane/timeframe rollups, boundary flags, and daily go/no-go without embedding raw runtime logs.

`docs/pt_rt1_5_2_signed_testnet_transport_smoke_and_active_restart.md`
- Founder/operator report for PT-RT1.5.2 signed Hyperliquid testnet transport smoke and active Week 1 restart handoff.
- Documents scoped env loading, warm-start/fresh-signal gates, candle-close scheduler preservation, one explicit `testnet_transport_smoke_not_strategy_signal` lifecycle row, the sanitized `Order has invalid size.` venue reject, no synthetic PnL update, and the operator-start command for `reports/paper_runtime/pt_rt1_5_2_week1_active/`.

`docs/pt_rt1_5_2_signed_testnet_transport_smoke_and_active_restart_summary.json`
- Compact machine-readable PT-RT1.5.2 summary.
- Contains signed transport status, account targeting policy, warm-start gate status, scheduler status, smoke lifecycle result, fixed notional policy, active runtime restart command, and boundary flags without secrets or raw runtime logs.

`docs/pt_rt1_5_3_hyperliquid_testnet_size_precision_hotfix.md`
- Founder/operator report for PT-RT1.5.3 Hyperliquid testnet size/precision hotfix.
- Documents the PT-RT1.5.2 invalid-size reject, testnet public metadata / `szDecimals` formatting fix, local invalid-size preflight, fixed 25 USDC policy, one accepted/open -> canceled -> reconciled `testnet_transport_smoke_not_strategy_signal` smoke, dashboard lifecycle precision fields, and no-live/no-production boundaries.

`docs/pt_rt1_5_3_hyperliquid_testnet_size_precision_hotfix_summary.json`
- Compact machine-readable PT-RT1.5.3 size/precision hotfix summary.
- Contains formatter status, metadata source, fixed-notional policy, smoke result, transport scope, dashboard precision-field status, and boundary flags without secrets or raw runtime logs.

`docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing.md`
- Founder/operator report for PT-RT1 real-time public-mainnet paper observation and testnet plumbing probes.
- Documents the strategy-truth lane, plumbing lane, top-20 scanner, strategy lanes, paper-equity model, closed-candle gating, indicator handling, duplicate prevention, probe approval/caps/kill-switch gates, dashboard status, limitations, and next run sequence.

`docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json`
- Compact dashboard/config summary for PT-RT1.
- Contains public-mainnet strategy-truth policy, testnet-probe policy, supported symbols/timeframes, lane definitions, scanner/config health placeholders, ignored runtime state paths, dashboard status, runbooks, and no-order/no-live boundary flags.

`docs/pt_rt1_24h_dry_run_probes_disabled.md`
- Runbook for a 24-hour public-mainnet strategy-truth dry run with testnet probes disabled.

`docs/pt_rt1_24h_testnet_plumbing_probe_run.md`
- Runbook for one gated/capped Hyperliquid testnet plumbing-probe run after exact approval.

`docs/pt_rt1_60_day_forward_observation_plan.md`
- Founder/operator plan for the 60-day forward observation window, daily/weekly reviews, disqualification criteria, and future evidence-phase promotion criteria.

`docs/pt_rt1_1_24h_probes_disabled_dry_run.md`
- Founder/operator PT-RT1.1 dry-run validation report.
- Current status is `blocked` because no ignored 24-hour runtime artifacts exist under `reports/paper_runtime/pt_rt1_1_24h_dry_run/`; PT-RT1.2 remains blocked until a real probes-disabled dry run is executed and summarized.

`docs/pt_rt1_1_24h_probes_disabled_dry_run_summary.json`
- Compact machine-readable PT-RT1.1 dry-run summary.
- Records probes-disabled config, missing runtime artifacts, data-health/ledger/duplicate-signal not-verified states, no-order/no-live boundary flags, and the `PT-RT1.2 blocked` decision.

`docs/pt_rt1_1a_expanded_universe_and_strategy_lanes.md`
- Founder/operator PT-RT1.1A readiness report.
- Documents the 10 synthetic paper strategy lanes, three wildcard observation hypotheses, expanded requested symbol universe, alias/blocking policy, scanner eligibility rules, dashboard update status, testnet probe separation, and the handoff to PT-RT1.1B public-mainnet connection/runtime readiness.

`docs/pt_rt1_1a_expanded_universe_and_strategy_lanes_summary.json`
- Compact machine-readable PT-RT1.1A readiness summary.
- Contains lane definitions, wildcard reason codes, requested symbols, alias mappings, blocked-symbol policy, scanner eligibility rules, dashboard status, testnet probe policy, boundaries, and next-phase decision without runtime logs.

`docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness.md`
- Founder/operator PT-RT1.1B readiness report.
- Documents the Hyperliquid public-mainnet `/info` connector, expanded watchlist resolution, 10 strategy lane readiness, wildcard lane readiness, paper-ledger policy, dashboard connection status, disabled testnet-plumbing readiness, runtime command, smoke-run result, and `PT-RT1.1C` 24-hour probes-disabled collection handoff.

`docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json`
- Compact machine-readable PT-RT1.1B readiness summary.
- Records public-mainnet endpoint policy, connected smoke status, watchlist status, strategy lane count, scanner eligibility counts, dashboard status, disabled testnet-plumbing status, runtime commands, and no-order/no-live boundaries without runtime logs or secrets.

`docs/pt_rt1_1c_24h_runtime_collection_start.md`
- Founder/operator PT-RT1.1C runtime collection start report.
- Records the active 24-hour probes-disabled runtime command, process metadata, output directory, first-cycle artifact confirmation, 10 lanes, expanded universe, blocked symbols, dashboard URL, stop instructions, no-order/no-live boundaries, and PT-RT1.1D evaluation handoff.

`docs/pt_rt1_1c_24h_runtime_collection_start_summary.json`
- Compact machine-readable PT-RT1.1C start summary.
- Contains process/start metadata, output directory, runtime configuration, first-cycle counts, lane/universe/blocker lists, boundary flags, and PT-RT1.1D handoff without embedding runtime logs.

`docs/ob2_0_obsidian_strategy_brain_refresh.md`
- Founder/operator report for the OB2.0 Obsidian strategy brain refresh.
- Lists notes created/updated/pointered, stale note handling, current strategy/evidence/data/dashboard/UAT/PT taxonomies, PT-RT1 recommendation, and boundary confirmations.

`docs/ob2_0_obsidian_strategy_brain_refresh_summary.json`
- Compact machine-readable OB2.0 summary.
- Contains created/updated/pointer note lists, stale phrase handling, strategy families, evidence sources, next recommended phase, boundary flags, and tests-run list.

`docs/uat0_safety_security_runtime_hardening.md`
- Founder/operator UAT0 safety, security, runtime, and operational-readiness audit.
- Records the evidence-candidate versus UAT-observation-universe distinction, top-20 universe policy, UAT shadow fill-timing policy, API auth status, secret/key hygiene status, runtime mode status, sandbox/live separation status, exchange endpoint safety, risk/drawdown/kill-switch/audit/approval/submit-lease status, blocker matrix, corrected UAT roadmap, and UAT1 readiness decision.
- UAT0 is audit/readiness only: no exchange calls, order submissions, paper/live behavior, Money Flow rule changes, routing expansion, or evidence-pack generation.

`docs/uat0_1_api_auth_runtime_lockout.md`
- Founder/operator UAT0.1 hardening report.
- Records the sensitive route inventory, scoped bearer-token auth implementation, authorization scope map, runtime safety defaults, live/private/order lockout status, test-only auth bypass policy, redaction baseline, remaining blockers, and UAT1 readiness decision.
- UAT0.1 closes the P0 API auth/authz baseline but leaves UAT1 blocked by remaining P1 adapter-policy, redaction, selected-venue sandbox/read-only, runtime drawdown, and top-20 identity gaps.

`docs/uat0_2_adapter_runtime_policy_and_redaction.md`
- Founder/operator UAT0.2 hardening report.
- Records the adapter safety inventory, adapter-level runtime-policy guard status, public read-only method classification, selected Hyperliquid future-UAT1 read-only allowlist artifact, forbidden endpoint categories, redaction verification status, remaining blockers, and UAT1 readiness decision.
- UAT0.2 closes the adapter-level runtime-policy / allowlist / representative redaction baseline. UAT0.3 later updates UAT1 readiness truth after adding top-20 resolver and drawdown monitor policy artifacts.

`docs/uat0_3_top20_universe_and_drawdown_readiness.md`
- Founder/operator UAT0.3 readiness report.
- Records top-20 source requirements, Hyperliquid market-intersection logic, inclusion/exclusion reason codes, ETH evidence-candidate versus top-20 observation-universe truth, Hyperliquid public read-only info-type allowlist status, runtime drawdown monitoring policy/status, redaction verification status, remaining blockers, and the UAT1 public-read-only readiness decision.

`docs/uat1_public_read_only_connectivity_and_top20_universe.md`
- Founder/operator UAT1 public-read-only connectivity and top-20 universe report.
- Records explicit runtime/network flags, Hyperliquid public info-type HTTP/shape results, no-key public top-volume source metadata, included/excluded Hyperliquid observation candidates, per-included-asset public market-data sample status, no-private/no-order confirmation, remaining blockers, and the UAT2 readiness decision.

`docs/uat1_public_read_only_connectivity_and_top20_universe_summary.json`
- Compact UAT1 report summary generated from the same public-read-only run for future dashboard/API consumption.
- Contains endpoint result flags, source metadata, included/excluded observation candidates, sample status, and boundary flags only; it is not an evidence pack, candle file, local DB export, strategy decision, order intent, submitted order, paper trade, or live trade.

`docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md`
- Founder/operator UAT1.1 shadow-readiness report.
- Records the shadow signal audit schema/surface, no-live-artifact boundary, UAT2 timing assumptions, operator-visible shadow drawdown state, drawdown reason codes, structured log/API error redaction verification status, UAT1 universe snapshot availability, UAT2 readiness decision, and remaining deferred UAT3 blockers.

`docs/uat2_shadow_strategy_top20_observation.md`
- Founder/operator UAT2 shadow strategy observation report.
- Records explicit UAT2 shadow/public-read-only runtime flags, the UAT1 observation universe snapshot used, evaluated symbols/components, public candle-fetch status, shadow audit signal summaries, no-trade reasons, next-candle timing availability, shadow drawdown state, ETH `sleeve_1h` evidence-candidate status, no-private/no-order boundary flags, and the UAT3 readiness decision.

`docs/uat2_shadow_strategy_top20_observation_summary.json`
- Compact UAT2 shadow run summary generated from the same bounded public-read-only run for future dashboard/API consumption.
- Contains shadow audit records, fetch status, summaries, drawdown state, and boundary flags only; it is not an evidence pack, candle file, local DB export, strategy decision, signal event, order intent, submitted order, approval, routing artifact, paper trade, or live trade.

`docs/uat2_1_dashboard_visualization_and_approval_readiness.md`
- Founder/operator UAT2.1 dashboard and review-readiness report.
- Documents the dashboard UAT2 tab, loaded JSON path, UAT2 counts, ETH evidence-candidate card, timing and not-live-account drawdown truth, boundary confirmation, UAT3 blocked readiness panel, and no-approval/no-order boundary.

`docs/uat3_0_sandbox_order_design_and_readiness.md`
- Founder/operator UAT3.0 sandbox-order design and readiness report.
- Defines the narrow initial sandbox subset, future approval template, sandbox runtime policy, sandbox account drawdown feed requirements, approval-gated lifecycle, sandbox artifact labeling, submit-lease / duplicate prevention, approval gate, risk gate, dashboard readiness, and UAT3.1 blocked decision.
- It is design/readiness only and creates no order intents, submitted orders, executable approvals, exchange calls, paper/live behavior, routing expansion, Money Flow rule changes, or evidence packs.

`docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md`
- Founder/operator UAT3.0.1 sandbox runtime / approval / risk readiness report.
- Records fixture-only runtime, artifact label, approval-scope, risk-gate, drawdown-feed, and submit-lease duplicate-prevention readiness. It does not authorize actual sandbox submission.

`docs/uat3_0_2_sandbox_gate_integration_dry_run.md`
- Founder/operator UAT3.0.2 sandbox gate integration dry-run report.
- Records runtime-policy blocker propagation, non-positive numeric validation, unified dry-run preflight behavior, founder actual-submission approval requirement, fixture-only drawdown blocker truth, artifact-label persistence enforcement blocker truth, and UAT3.1 blocked decision.
- Records the fixture-tested `SandboxRuntimePolicy`, sandbox artifact-label validator, sharpened actual-submission approval template, approval-scope validator, sandbox risk-gate evaluator, sandbox drawdown feed fixture, submit-lease duplicate-prevention fixture, dashboard readiness, UAT3.1 blocked decision, and no-order/no-artifact boundary.

`docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md`
- Founder/operator UAT3.0.3 sandbox gate wiring and label-enforcement report.
- Records sandbox artifact label boundary enforcement for persistence/API/dashboard/report helpers, dry-run executable gate service wiring, runtime policy semantics, approval/risk/submit-lease dry-run wiring, fixture-only drawdown blocker truth, dashboard readiness, UAT3.1 blocked decision, and no-order/no-artifact boundary.

`docs/uat3_0_4_sandbox_private_read_only_drawdown.md`
- Founder/operator UAT3.0.4 sandbox private read-only drawdown readiness report.
- Records the required private read-only credential approval boundary, credential safety/redaction status, private read-only account policy, endpoint classification, sandbox account drawdown feed model/status, no-order endpoint confirmation, UAT3 preflight drawdown-status support, UAT3.1 blocked decision, and no-order/no-artifact boundary.

`docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md`
- Founder/operator UAT3.0.5 sandbox/testnet private read-only credential and drawdown-feed verification report.
- Records the exact UAT3.0.5 approval boundary, local sandbox credential environment status, redaction status, private-read-only endpoint categories, no-order endpoint confirmation, verified sandbox drawdown-feed status, UAT3 preflight drawdown status, UAT3.1 blocked decision, and no-order/no-artifact boundary.

`docs/uat3_0_6_sandbox_submit_path_dry_run_wiring.md`
- Founder/operator UAT3.0.6 sandbox submit path dry-run wiring report.
- Records the non-persistent sandbox submission plan, executable dry-run gate chain, founder actual-submission approval requirement, live-fed sandbox drawdown status consumption, approval-scope/risk/submit-lease wiring, endpoint classification, artifact-label boundary enforcement, UAT3.1 blocked decision, and no-order/no-artifact/no-exchange boundary.

`docs/uat3_1_first_sandbox_order_attempt.md`
- Founder/operator UAT3.1 first sandbox/testnet lifecycle probe report.
- Records exact approval text presence, runtime/scope/risk/drawdown/lease/label gates, one sanitized Hyperliquid testnet ETH post-only limit order request, sanitized rejected response, no-cancel-needed result, reconciliation status, no-live/no-paper/no-production-artifact confirmation, and UAT3.2 readiness decision.

`docs/uat3_1_first_sandbox_order_attempt_summary.json`
- Sanitized machine-readable UAT3.1 summary.

`docs/uat3_2_second_sandbox_order_attempt.md`
- Founder/operator UAT3.2 fixed-key preflight / second sandbox/testnet lifecycle-attempt report.
- Records exact approval text presence, account/API-wallet readiness result, endpoint/runtime/scope/risk/drawdown/lease/label gates, zero-order-attempt blocked lifecycle result, sanitized no-request/no-response truth, no-live/no-paper/no-production-artifact confirmation, UAT4.0 dashboard roadmap capture, and UAT3.3 blocked decision.

`docs/uat3_2_second_sandbox_order_attempt_summary.json`
- Sanitized machine-readable UAT3.2 summary.
- Records that account/API-wallet readiness blocked before order transport, `order_attempt_count` is `0`, order/cancel endpoints were not called, and all production execution side-effect flags are false.
- Includes lifecycle status, drawdown status, sandbox labels, side-effect flags, sanitized request/response/reconciliation payloads, and no secret values.

`docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md`
- Founder/operator UAT3.3 Hyperliquid account-targeting / precision report.
- Records account role resolution, `vaultAddress` behavior, signer/target account summaries, UAT-universe precision validation, live-fed sandbox drawdown, runtime/scope/risk/lease/label gates, sanitized ETH post-only order shape, minimum-order-value rejection truth, the later successful follow-up lifecycle, no-live/no-paper/no-secret boundary confirmation, and UAT3.4 scoping decision.

`docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt_summary.json`
- Sanitized machine-readable UAT3.3 summary.

`docs/uat3_4_sandbox_routing_pipeline_and_order_ledger.md`
- Founder/operator UAT3.4 fixed-target sandbox routing and routed-order ledger report.
- Records the UAT3.3 success recap, current normal-user account mode with `vaultAddress` omitted, standard-perp selected equity source, unified-mode compatibility, fixed-target Hyperliquid testnet ETH route definition, UAT-universe precision validation, routed-order ledger, one accepted/open-then-canceled ETH lifecycle attempt, no-top-20/no-live/no-paper boundary confirmation, UAT4.0 dashboard roadmap status, and UAT3.5 blocked decision.

`docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json`
- Sanitized machine-readable UAT3.4 route/ledger summary consumed by the dashboard routed-orders section.
- Records that account targeting was verified, ETH precision formatting produced an exchange-valid post-only shape, live-fed sandbox drawdown was available with selected equity source `standard_perp_clearinghouse`, one UAT3.4 lifecycle attempt called the order endpoint once, the accepted/open order was canceled through one cancel endpoint call, reconciliation found no open order, and all production execution side-effect flags remain false.

`docs/uat4_0_live_uat_dashboard_chart_cockpit.md`
- Founder/operator UAT4.0 dashboard/chart cockpit report.
- Records dashboard sections, watchlist, market-data coverage, chart/indicator labels, entry/exit marker semantics, routed orders tab, active sandbox route card, unified equity-source visibility, no-order-control confirmation, limitations, and next dashboard improvements.

`docs/uat4_1_exchange_style_dashboard_redesign.md`
- Founder/operator UAT4.1 dashboard redesign report.
- Records the UAT4.0 usability problems, exchange-style layout principles, `apps/dashboard/DESIGN.md` replacement status, top bar / watchlist / chart cockpit / right rail / bottom blotter sections, marker and routed-order semantics, no-order-control confirmation, remaining UI limitations, and next dashboard work.

`docs/uat4_2_live_market_dashboard_and_paper_equity_monitor.md`
- Founder/operator UAT4.2 live-market monitoring and paper-equity dashboard report.
- Records live public market-data status, watchlist coverage, indicator computation, strategy scanner status, entry/exit marker semantics, 60-second sandbox private-read-only balance polling policy, internal 10,000 USDC paper-equity ledger, sizing policy, routed-orders visibility, no-order-control confirmation, and PT0 roadmap capture.

`docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json`
- Dashboard-consumed UAT4.2 monitor summary.
- Records public-read-only market snapshots for the UAT watchlist, indicator snapshots, paper-observation scanner records, sandbox balance confirmation/poll policy, internal paper-equity state, future sizing policy, routed-order source status, and no-order/no-live side-effect flags.

`docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md`
- Founder/operator PT0 report.
- Records that PAPER TRADING IS APPROVED and BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED for Hyperliquid testnet/sandbox only, plus TradingView Lightweight Charts status, top-20 eligibility, internal paper equity, balance polling, risk limits, routing-foundation defaults, no-live confirmation, and PT0.1 roadmap.

`docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json`
- Dashboard-consumed PT0 paper/sandbox runtime summary.
- Records official local TradingView Lightweight Charts bundle metadata, paper approval statements, top-20 paper universe eligibility, paper scanner records, internal 10,000 USDC paper-equity state, sizing policy, 60-second sandbox private-read-only polling policy, PT0 runtime limits, and routing side-effect flags.

`docs/pt0_0_1_tradingview_chart_stability_hotfix.md`
- Founder/operator PT0.0.1 hotfix report.
- Records the P0 chart vertical-growth/page-scroll bug, root cause, chart sizing fix, chart lifecycle fix, polling/timer fix, manual verification status, no-order/no-live confirmation, remaining browser-regression limitation, and PT0.1 next-phase note.

`docs/pt0_0_2_historical_strategy_replay_cockpit.md`
- Founder/operator PT0.0.2 report.
- Records why Hyperliquid testnet market data is not strategy truth, the historical replay source, BTC/ETH/SOL dataset readiness, fill/cost assumptions, dynamic 10,000 USDC equity policy, dashboard replay cockpit status, chart/marker/trade-inspector/equity/comparison status, sandbox-ledger separation, limitations, and PT0.0.3/PT0.1 roadmap.

`docs/pt0_0_2_historical_strategy_replay_summary.json`
- Dashboard-consumed PT0.0.2 historical replay summary.
- Contains replay-ready BTC/ETH/SOL x 15m/1h/4h datasets, baseline and MACD-removed research-only replay strategies, candles, indicators, historical entry/exit markers, trade inspector records, dynamic equity curves, comparison rows, source hash, DB audit status, no-order/no-live flags, and `testnet_prices_used_as_strategy_truth=false`.

`docs/pt0_0_3_historical_data_horizon_and_1d_readiness.md`
- Founder/operator PT0.0.3 report.
- Records 1D replay support, Jan 2025 target-start readiness, actual available candle horizons, data source labels, aggregation truth, dynamic equity preservation, no-testnet-strategy-truth boundary, no-order/no-live confirmation, and next historical backfill need.

`docs/pt0_0_3_historical_strategy_replay_summary.json`
- Dashboard-consumed PT0.0.3 historical replay summary.
- Extends the PT0.0.2 trusted historical replay export with BTC/ETH/SOL x 15m/1h/4h/1D readiness rows, actual data horizon rows, 1D candles aggregated from 4h replay candles, baseline/MACD-removed/5EMA-20MA-cross-close strategy replay rows, indicators, markers, trades, equity curves, comparison rows, Jan 2025 target-start truth, and no-order/no-testnet-strategy-truth flags.

`docs/sv2_0_historical_data_refresh_summary.json`
- Dashboard-consumed compact SV2.0/SV2.0.1 public-mainnet historical refresh and evidence-truth summary.
- Contains Money Flow v1.2, `sleeve_1d` settings, requested/supported/excluded universe truth, Hyperliquid public mainnet source metadata, market identity rows, BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB x 15m/1h/4h/1d readiness rows, canonical close-slot normalization, staged-vs-DB-imported flags, canonical-evidence blocked status, compact non-canonical dynamic-equity rows with final-open-position accounting, no-testnet-strategy-truth flags, and no-order/no-private-endpoint flags.

`docs/sv2_0_historical_data_refresh_1d_and_expanded_universe_readiness.md`
- Founder/operator SV2.0/SV2.0.1 historical-data readiness report.
- Records the requested expanded universe, Hyperliquid market identity resolution including SHIB -> `kSHIB`, public mainnet candleSnapshot source, Jan 2025 target horizon, public 5000-candle limits, canonical close-slot normalization, staged-only truth, `db_imported=false`, canonical-evidence blocked status, and no-order/no-live boundaries.

`docs/sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild.md`
- Founder/operator SV2.0/SV2.0.1 evidence rebuild report.
- Records Money Flow v1.2, initial non-optimized `sleeve_1d` settings, preserved 15m/1h/4h settings, compact non-canonical dynamic-equity rows, dataset-end open-position accounting, canonical evidence blocked status, dashboard status, limitations, and next evidence-pack/DB-import follow-up.

`docs/sv2_0_1_canonical_evidence_truth_hotfix.md`
- Founder/operator SV2.0.1 hotfix report.
- Records open-position accounting, Hyperliquid close-time normalization, canonical evidence status, import/staging truth, sleeve allocation budget, timeframe canonicalization, missing-indicator handling, SHIB/kSHIB status, no-order/no-live confirmation, and remaining blocker before SOR-EV1.

`docs/sor_ev2_1_evidence_lab_ui.md`
- Founder/operator SOR-EV2.1 UI report.
- Records the Evidence Lab scope, input SOR-EV1/SOR-EV2 bundles, dashboard sections, variant matrix, worst-trade, control-pocket, RSI/MACD, large adverse-candle, the SOR-EV2.2 overlay supersession, limitations, no-order/no-live confirmation, and next recommended evidence-review phase.

`docs/sor_ev2_2_variant_chart_overlay.md`
- Founder/operator SOR-EV2.2 UI report.
- Records the Evidence Lab overlay scope, input bundles, overlay controls, baseline markers, variant/context markers, worst-trade focus mode, control-pocket view, unavailable overlay data states, methodology/date-filter warnings, limitations, no-order/no-live confirmation, and next recommended evidence-review phase.

`docs/sor_ev3_avoid_sideways_low_volatility.md`
- Founder/operator SOR-EV3 evidence report.
- Records the founder-selected `avoid_sideways_low_volatility` true-forward drilldown against canonical SV2.0.2 evidence, objective regime feature definitions, baseline parity, controlled variant comparison, blocked-entry attribution, loss concentration, control-pocket impact, candidate/rejected status, and no-order/no-live/no-production-rule-change boundaries.

`docs/sor_ev3_avoid_sideways_low_volatility_summary.json`
- Compact SOR-EV3 dashboard/report source.
- Contains baseline references, feature definitions, variant rollups, blocked-entry attribution samples, loss-concentration summaries, control-pocket impact, boundary flags, and no approved variants without raw candle payloads.

`docs/mf_orig_ev1_original_money_flow_spec_and_gap_matrix.md`
- Founder/operator MF-ORIG-EV1.1 source-specification and gap-matrix report.
- Extracts the prompt-provided Gerald Peters original Money Flow source hierarchy into formal evidence-only rules, compares it against current Money Flow v1.2 behavior, and labels source assumptions/deferred subjective judgments. MF-ORIG-EV1.1 preserves the source interpretation while warning that pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions should not be used. The PDF is now stored in `money-flow/90 Reference/` for future source-exact reconciliation.

`docs/mf_orig_ev1_original_money_flow_reconstruction.md`
- Founder/operator MF-ORIG-EV1.1 evidence report.
- Records the Strategy Validation-only original Money Flow hypotheses, canonical SV2.0.2 baseline reference, 1d-first evidence summary, support/pivot-stop and 1% risk-sizing modeling, corrected event-ledger accounting, peak-to-trough drawdown, candidate gate outcome, limitations, and no-order/no-live/no-production-rule-change boundaries.

`docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json`
- Compact MF-ORIG-EV1.1 report source.
- Contains source metadata, gap matrix, hypothesis definitions, canonical baseline references, parity rows, replay rows, accounting invariant audit, trade samples, control-pocket results, candidate gate status, limitations, and boundary flags without raw candle payloads.

`docs/mf_orig_ev2_multitimeframe_evidence_packs.md`
- Founder/operator MF-ORIG-EV2 evidence report.
- Summarizes the four source-faithful 1% risk-sizing Original Money Flow hypotheses plus four full-equity/notional comparison counterparts across 9 canonical symbols, 15m/1h/4h/1d, both fill assumptions, 288 ignored evidence-pack paths, baseline deltas versus Money Flow v1.2, source-primary versus fractal/stress-test timeframe interpretation, candidate-gate outcomes, dashboard integration status, limitations, and no-order/no-live/no-production-rule-change boundaries.

`docs/mf_orig_ev2_multitimeframe_evidence_summary.json`
- Compact MF-ORIG-EV2 dashboard/report source.
- Records 576 replay scenario rows, 288 generated evidence-pack paths, per-symbol/timeframe/hypothesis summaries, event-ledger accounting invariant status, peak-to-trough drawdown truth, baseline parity, candidate gates, dashboard chart-data paths, and boundary flags without raw candle payloads.

`docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review.md`
- Founder/operator EV-AUDIT1 audit report.
- Reviews every current evidence family without adding another strategy variant: Money Flow v1.2 canonical SV2.0.2, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and pending STRAT-EV1 plan-only status. It includes evidence inventory, data integrity, methodology scorecard, full hypothesis comparison, top winners/losers, losing streaks, regime/control-pocket attribution, issue list, backtest adequacy decision, and real-time paper observation readiness.

`docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json`
- Compact EV-AUDIT1 report source.
- Contains the audit inventory, data integrity rows, methodology scores, comparison matrix, top winner/loser/streak extracts, issue counts, backtest adequacy decision, paper-observation readiness decision, boundary flags, and recommended next phase without raw candle payloads or secrets.

`docs/strat_disc1_autonomous_strategy_discovery.md`
- Founder/operator STRAT-DISC1 autonomous discovery report.
- Records the research-only data inventory, bounded strategy families, candidate gate, near misses, boundary flags, and final decision. The first STRAT-DISC1 run accepted 50 local public-mainnet selected replay datasets, executed 12 curated candidate runs, and promoted zero strategies.

`docs/strat_disc1_autonomous_strategy_discovery_summary.json`
- Compact STRAT-DISC1 machine-readable summary.
- Contains `data_inventory`, `candidate_runs`, `strategy_families_tested`, `rejected_candidates`, `passing_candidates`, `top_3_candidates`, `top_near_misses`, `candidate_gate`, `search_budget`, `search_budget_used`, `conclusion`, and no-order/no-live boundary flags without raw runtime logs or secrets.

`docs/goal_strat1_strategy_discovery.md`
- Founder/operator GOAL-STRAT1 autonomous strategy-discovery report.
- Records the expanded research-only data inventory, 7 tested strategy families, 121 candidate configurations, strict candidate gate, top near misses, boundary flags, and final honest-exhaustion decision. GOAL-STRAT1 promoted zero strategies because every positive pocket failed drawdown, out-of-sample, concentration, profit-factor, sample-size, or market-structure gates.

`docs/goal_strat1_strategy_discovery_summary.json`
- Compact GOAL-STRAT1 machine-readable summary.
- Contains `data_inventory`, `candidate_runs`, `strategy_families_tested`, `rejected_candidates`, `passing_candidates`, `top_3_candidates`, `top_near_misses`, `candidate_gate`, `search_budget`, `search_budget_used`, `subagent_review`, `conclusion`, and no-order/no-live boundary flags without raw runtime logs or secrets.

`docs/goal_strat1_no_three_candidates_found.md`
- Human-readable GOAL-STRAT1 failure/exhaustion report.
- Summarizes the tested families, candidate count, best near misses, blocker counts, evidence implications, and required next research before any future promotion attempt.

`docs/goal_strat2_two_non_existing_strategies.md`
- Founder/operator GOAL-STRAT2 report.
- Selects two non-existing strategies worth paper-testing review from GOAL-STRAT1 evidence while excluding current PT runtime lanes and Money Flow/SOR/MF-ORIG/wildcard-adjacent strategy families. The selected strategies are relative-strength rotation with ATR trailing exit and Donchian breakout with ATR trailing exit; both are research-only and not production/live approved.

`docs/goal_strat2_two_non_existing_strategies_summary.json`
- Compact GOAL-STRAT2 machine-readable summary.
- Contains source-summary reference, testing gate, excluded existing-strategy policy, selected candidates, near misses, rejection counts, and no-order/no-live boundary flags without raw runtime logs or secrets.

`docs/goal_strat2_candidate_*.md`
- Per-candidate GOAL-STRAT2 founder review notes.
- Record strategy logic, evidence metrics, OOS checks, concentration risks, why each is worth paper testing, why each may still fail, and no-production/no-live boundaries.

`docs/strat_prune1_strategy_lane_pruning.md`
- Founder/operator STRAT-PRUNE1 pruning report.
- Classifies all 10 current PT-RT paper-observation lanes, reviews GOAL-STRAT/SOR/MF-ORIG/EV-AUDIT/PT-RT evidence, and recommends a smaller next paper slate. It is recommendation-only and implements no runtime lane changes.

`docs/strat_prune1_strategy_lane_pruning_summary.json`
- Compact STRAT-PRUNE1 machine-readable summary.
- Contains per-lane/candidate recommendations, ranks, reason codes, evidence references, paper/testnet/production eligibility flags, timeframe scope, recommended next slate, and no-order/no-live boundaries.

`apps/dashboard/vendor/`
- PT0 vendored third-party charting bundle from the official `lightweight-charts` package.
- Contains `lightweight-charts.standalone.production.js`, `LICENSE`, and `package.json`; the dashboard uses this local bundle instead of a hosted TradingView widget.

`services/exchange/hyperliquid/precision.py`
- Decimal-only Hyperliquid precision formatter.
- Uses asset metadata `szDecimals`, perpetual max price decimals `6 - szDecimals`, five-significant-figure price formatting, and size flooring to asset size precision. It is used by UAT3.3 order planning and UAT observation-universe precision validation.

`services/uat/sandbox_order.py`
- UAT3.1 one-shot sandbox/testnet lifecycle probe helper.
- UAT3.2 fixed-key preflight / second sandbox/testnet lifecycle-attempt helper.
- UAT3.3 Hyperliquid account-targeting and precision helper.
- UAT3.4 fixed-target sandbox route definition, routed-order ledger record helpers, ETH-only route validation, active normal-user account-mode validation, and sandbox label mapping for dashboard/report ledgers.
- `scripts/run_uat32_second_sandbox_order.py` refuses to run without `--execute-approved-uat32`, validates exact UAT3.2 founder/operator approval before loading `.env`, writes sanitized UAT3.2 Markdown/JSON reports, and blocks before order transport when account/API-wallet readiness fails.
- `scripts/run_uat33_hyperliquid_precision_order.py` refuses to run without `--execute-approved-uat33`, resolves normal user/master versus subaccount/vault targeting, validates Hyperliquid precision across the UAT observation universe, writes sanitized UAT3.3 Markdown/JSON reports, and blocks before order transport when the configured target account fails readiness gates.
- `scripts/run_uat34_sandbox_routing_pipeline.py` refuses to run without `--execute-approved-uat34`, uses the fixed-target Hyperliquid testnet ETH route, preserves standard/unified equity-source reporting, enforces runtime/risk/lease/label/precision/endpoint gates, writes sanitized routed ledger Markdown/JSON reports, and caps approved UAT3.4 attempts at three without adding broad routing or dashboard order controls.
- `scripts/refresh_uat42_live_monitor.py` generates the UAT4.2 dashboard monitor summary from deterministic read-only helpers and the existing UAT3.4 routed-order summary. Default mode performs no network calls, reads no credentials, and calls no private/signed/order endpoints.
- Validates the exact actual-submission approval text, sandbox/testnet endpoint boundary, one-order maximum, manual lifecycle-probe labels, live-fed sandbox drawdown, UAT3 dry-run gates, post-only/non-marketable ETH order shaping, sanitized response summaries, and no production artifact side-effect flags before allowing a single testnet order transport call.

`services/uat/sandbox.py`
- Fixture-only UAT3 sandbox readiness helpers.
- Defines fail-closed sandbox runtime policy evaluation, sandbox private read-only account policy evaluation, UAT3.0.5 approval and sandbox/testnet credential-environment verification, redacted credential payload serialization, Hyperliquid sandbox account-state payload parsing into not-live-account drawdown feeds, sandbox artifact label validation, sandbox artifact boundary validation, actual-submission approval-scope validation, sandbox risk-gate evaluation, sandbox drawdown feed fixtures and sandbox account drawdown feed modeling, submit-lease duplicate-prevention checks, unified dry-run preflight, dry-run executable gate service composition, non-persistent UAT3.0.6 sandbox submission plans, and dry-run submit-path gate chaining.
- Creates no trading artifacts, submits no orders, calls no exchange endpoints, and authorizes no paper/live behavior.

`services/uat/live_monitor.py`
- UAT4.2 read-only live-market monitor and internal paper-equity helpers.
- Defines public-read-only Hyperliquid market-data policy validation, deterministic market snapshot fixtures, indicator computation, paper-observation scanner records, 60-second sandbox private-read-only balance polling policy, internal 10,000 USDC paper-equity ledger, future sizing policy from current paper equity, and summary generation for the dashboard.
- Defaults to no network calls, no credentials, no private/signed/order endpoints, no live endpoint, and no trading artifacts.

`services/uat/pt0_runtime.py`
- PT0 paper/sandbox runtime foundation helpers.
- Defines the explicit paper/top-20 approval statements, top-20 Hyperliquid testnet-supported paper universe eligibility, internal 10,000 USDC paper-equity ledger wrapper, realized-equity sizing policy, PT0 runtime limits, route-candidate risk decisions, paper scanner records, and summary generation for the dashboard.

`services/strategy_validation/historical_replay.py`
- PT0.0.2 historical replay export helpers.
- Adds research-only replay variants for MACD removed and `Only close on 5/20 cross` without changing production Money Flow rules.
- Audits persisted strategy-validation candle availability when DB connectivity is available and builds the dashboard replay summary from the trusted SV1.17 historical full-suite baseline export. It labels historical candle replay data as strategy truth, marks Hyperliquid testnet prices as not strategy truth, generates baseline plus research-only MACD-removed historical markers/trades/equity curves, and creates no orders or exchange calls.
- PT0.0.3 adds Jan 2025 target-start readiness helpers, 1D deterministic aggregation from 4h historical replay candles, actual horizon rows, and an export builder that did not create a production Money Flow 1D sleeve in that phase. SV2.0 later supersedes that state by adding the real `sleeve_1d` in strategy config and by loading direct Hyperliquid public-mainnet 1d readiness/evidence rows through the SV2.0 summary.
- Defaults to no network calls, no credentials, no private/signed/order endpoints, no live endpoint, no order submissions, no SOR/fanout/CBBO/target reselection, and no trading artifacts.

`services/strategy_validation/sv2.py`
- SV2.0/SV2.0.1 Hyperliquid public-mainnet historical refresh helpers.
- Resolves the requested expanded universe through public metadata, explicitly handles SHIB alias identity, builds public `candleSnapshot` requests for 15m/1h/4h/1d, normalizes Hyperliquid `.999Z` close times to canonical close slots while preserving raw venue close time, records Jan 2025 horizon/5000-candle-limit truth, separates fetched/normalized/staged/DB-imported/canonical-evidence flags, labels compact rows as non-canonical, and builds compact dynamic-equity rows with entry-fee-at-open plus dataset-end force-close/MTM accounting without calling private/signed/order/testnet endpoints or using API keys.

`services/strategy_validation/strat_disc1.py`
- STRAT-DISC1 research-only autonomous strategy-discovery harness.
- Loads local selected replay JSON without importing DB/session settings, inventories candle data quality, runs bounded curated hypotheses, computes dynamic-equity metrics, out-of-sample slices, symbol/timeframe/period concentration, and strict founder-review candidate gates. It creates no runtime artifacts, order intents, submitted orders, exchange calls, production-rule changes, testnet strategy truth, paper/live approvals, or active PT-RT mutations.

`services/strategy_validation/goal_strat1.py`
- GOAL-STRAT1 expanded research-only autonomous strategy-discovery harness.
- Loads local public-mainnet selected replay JSON, validates data quality, computes indicators locally, runs bounded strategy families across Money Flow repair, source-faithful Money Flow, trend/breakout, volatility expansion, mean reversion, relative strength, and pairs/spread research, scores 121 candidate configurations with chronological and anchored out-of-sample checks, and writes Markdown/JSON research reports. It creates no runtime artifacts, order intents, submitted orders, exchange calls, production-rule changes, testnet strategy truth, paper/live approvals, or active PT-RT mutations.

`services/strategy_validation/goal_strat2.py`
- GOAL-STRAT2 research-only selector for two non-existing strategies worth testing.
- Consumes the committed GOAL-STRAT1 summary, excludes current PT runtime lanes and existing/adjacent Money Flow/SOR/MF-ORIG/wildcard families, applies a paper-testing gate, enforces family diversity, writes Markdown/JSON candidate reports, and creates no runtime artifacts, order intents, submitted orders, exchange calls, production-rule changes, testnet strategy truth, paper/live approvals, or active PT-RT mutations.

`scripts/run_sv20_historical_refresh.py`
- SV2.0/SV2.0.1 public-mainnet metadata/candle refresh script.
- Writes `docs/sv2_0_historical_data_refresh_summary.json` when run with `--fetch-public-data`; default/no-network mode can still build blocked readiness from supplied metadata or empty metadata. The script targets only `https://api.hyperliquid.xyz/info` public info, refuses non-mainnet-public URL use, and records fetched/normalized/staged rows as `db_imported=false` until the hardened importer path is used.

`scripts/run_sv202_canonical_import_and_evidence.py`
- SV2.0.2 public-mainnet canonical DB-import and evidence-pack runner.
- Verifies the intended migrated strategy-validation DB, resolves Hyperliquid public market identity, defers SHIB/kSHIB when unit semantics are unclear, fetches/normalizes public `candleSnapshot` rows, filters rows past fully closed timeframe end-boundaries, writes temporary import files, imports through the hardened candle importer, generates per-symbol/per-timeframe canonical SV2.0.2 campaign configs using each dataset's full available imported window, runs existing evidence-pack machinery, and writes committed summary/report files.
- It uses no API keys, calls no private/signed/order endpoints, submits no orders, and keeps generated evidence packs under ignored `reports/strategy_validation/`.

`scripts/build_sv202_dashboard_chart_data.py`
- SV2.0.2 dashboard chart/trade export helper.
- Reads existing `/tmp/money-flow-sv202-candles` public-candle JSON plus existing regenerated canonical batch reports, computes dashboard-only indicator overlays, pairs candles with canonical pack trades, and writes ignored `reports/strategy_validation/sv2_0_2_dashboard_chart_data/<timestamp>/` JSON for Historical Replay display.
- It does not regenerate evidence packs, import candles, call exchange endpoints, use API keys, submit orders, or change Money Flow strategy rules.

`scripts/build_mf_orig_ev2_multitimeframe_evidence.py`
- MF-ORIG-EV2 evidence-pack and dashboard chart-data generator.
- Runs the Strategy Validation-only Original Money Flow reconstruction against canonical SV2.0.2 DB-imported candle truth, writes ignored evidence-pack directories and ignored dashboard chart-data JSON, and writes committed compact Markdown/JSON summaries.
- It does not import candles, call exchange endpoints, use API keys, submit orders, approve any strategy, or change production Money Flow rules.

`scripts/build_ev_audit1_full_review.py`
- EV-AUDIT1 audit report builder.
- Reads existing committed summaries and ignored local canonical/dashboard evidence artifacts where available, then writes the EV-AUDIT1 Markdown/JSON audit report. It performs evidence inventory, data/methodology scoring, biggest winner/loser/streak extraction, regime/control-pocket attribution, issue classification, and paper-readiness assessment.
- It does not regenerate evidence packs, import/refetch candles, call exchange endpoints, use API keys, submit orders, approve any strategy, or change production Money Flow rules.

`scripts/build_strat_disc1_autonomous_discovery.py`
- STRAT-DISC1 report builder.
- Runs the isolated research-only `strat_disc1.py` harness over local selected replay JSON and writes `docs/strat_disc1_autonomous_strategy_discovery.md` plus `docs/strat_disc1_autonomous_strategy_discovery_summary.json`. It avoids importing the broader `services.strategy_validation` package so unrelated runtime settings cannot affect discovery reporting.

`scripts/run_goal_strat1_discovery.py`
- GOAL-STRAT1 report builder.
- Runs the isolated research-only `goal_strat1.py` harness over local selected replay JSON and writes `docs/goal_strat1_strategy_discovery.md`, `docs/goal_strat1_strategy_discovery_summary.json`, candidate reports if three pass, or `docs/goal_strat1_no_three_candidates_found.md` when the strict gate promotes fewer than three. It avoids importing the broader `services.strategy_validation` package so unrelated runtime settings cannot affect discovery reporting.

`scripts/run_goal_strat2_worth_testing.py`
- GOAL-STRAT2 report builder.
- Runs the isolated research-only `goal_strat2.py` selector over the committed GOAL-STRAT1 summary and writes the two-strategy report, compact summary JSON, and per-candidate notes.

`scripts/refresh_pt0_runtime_summary.py`
- Generates the committed PT0 dashboard/runtime summary from deterministic helpers plus existing UAT3.3/UAT3.4/UAT4.2 summaries.

`scripts/refresh_pt002_historical_replay_summary.py`
- Generates the committed PT0.0.2 dashboard replay summary from the trusted offline SV1.17 historical full-suite replay JSON and an optional persisted-candle DB audit.
- It does not call exchange endpoints, use credentials, submit orders, change Money Flow rules, import candles, or generate evidence packs.
- Default mode performs no network calls, reads no credentials, and calls no private/signed/order endpoints.

`scripts/refresh_pt003_historical_replay_summary.py`
- Generates the committed PT0.0.3 dashboard replay summary from the PT0.0.2 trusted replay summary and optional persisted-candle DB audit.
- It adds 1D aggregation/readiness truth and Jan 2025 target-start reporting without importing candles, calling exchange endpoints, using credentials, submitting orders, changing Money Flow rules, or generating evidence packs.

`core/config/`
- Pydantic settings, environment profiles, runtime selection, and per-venue / strategy configuration.
- UAT0.1 adds `APIAuthConfig` and `RuntimeSafetyPolicy` settings. Defaults remain fail-safe: API auth enabled, paper/live/order/private endpoint flags disabled, and sandbox mode required.
- SV2.0 adds `sleeve_1d` and `MONEY_FLOW_1D_*` settings to the Money Flow strategy config. SV2.0.1 sets runtime sleeve allocations to 0.25 each and validates enabled allocation sum <= 1.0. Existing `sleeve_15m`, `sleeve_1h`, and `sleeve_4h` rule defaults remain unchanged.

`core/security.py`
- Security helper module for UAT/API hardening.
- Defines API auth scopes/principals plus representative redaction helpers for secret-like keys, bearer tokens, API-key/secret/password key-value text, database URLs, API-error payloads, and structured log events.

`core/logging/`
- Structured logging setup.
- UAT1.1 routes structlog event dictionaries through the representative redaction processor before JSON or console rendering so obvious bearer/API-key/secret/password/DB URL values are not exposed in structured events.

`core/domain/`
- Shared typed domain models and enums.
- Includes canonical instrument identity, exchange/account truth, mandate/binding/component hierarchy, source-policy, strategy decisions, desired trades, routing assessment, route-readiness audit, routing target recommendation, routing target choice, Phase 7.0 routing automation policy/plan models, Phase 7.1 / 7.1.1 / 7.1.2 routing automation approval/gate models and lineage-scoped / current-policy approval status truth, Phase 7.2 approval-gated recommendation acceptance result models, Phase 7.3 approval-gated target-choice conversion result models, Phase 7.4 approval-gated preview/readiness result models, Phase 7.5 approval-gated submitted-order handoff result models, Phase 7.5.1 `consumption_pending` approval status truth, child intents, readiness, submitted orders, routed submitted-order lifecycle context, lifecycle-event audit context, and recovery/actionability models.
- SV1.0 adds strategy-validation request, assumption, simulated-trade, metrics, component-report, and report dataclasses. SV1.0.1 extends them with explicit fill timing, fill-source metadata, closed-trade and mark-to-market drawdown fields, and component comparison report data. SV1.1 adds batch request/run/report dataclasses for comparative validation across explicit component, fill-timing, symbol, date-window, fee, and slippage assumptions. SV1.2 adds data-coverage and regime-summary report dataclasses for deterministic market-regime/data-quality research diagnostics. SV1.2.1 adds explicit data-coverage window-convention truth. These are research/backtest artifacts only and are separate from `SubmittedOrder` and live execution artifacts.
- Includes `core/domain/routed_lifecycle.py`, the shared parser for routed submitted-order audit payloads so execution service and API surfaces use one missing/malformed lineage truth source.

`core/interfaces/`
- Shared protocols and service boundaries.
- Includes exchange, market data, indicators, portfolio, planning, risk, routing assessment / readiness-audit / recommendation / target-choice, execution, and Strategy Validation service boundaries through SV1.7.

`core/schemas/`
- API request/response schemas.
- Includes route-readiness and routing-target-recommendation request/response schemas plus Phase 7.0 routing automation policy/plan schemas, Phase 7.1 / 7.1.1 / 7.1.2 routing automation approval/revocation/consumption schemas with approval scope/fingerprint fields and current-policy gate-state truth, Phase 7.2 approval-gated recommendation acceptance request/response schemas, Phase 7.3 approval-gated target-choice conversion request/response schemas, Phase 7.4 approval-gated preview/readiness request/response schemas, Phase 7.5 approval-gated submitted-order handoff request/response schemas, derived routed submitted-order lineage, lifecycle-context, lifecycle-event, prepared-order-preview, execution-readiness, read-only routed workflow inspection response fields, and Phase 8.0 read-only operator routed workflow summary response fields so API clients can inspect routed-origin, recommendation-backed audit metadata, approval state, manual-resolution needs, submitted-order safety, and submit-lease state without parsing raw payload directly.

`db/models/`
- SQLAlchemy persistence models for canonical instruments, symbol mappings, client/account/mandate hierarchy, source-policy, candles, indicators, strategy decisions, desired trades, routing assessments, route-readiness audits, routing target recommendations, routing target choices, routing automation approvals, readiness evaluations, child intents, explicit child-intent submission leases, submitted orders, fills, lifecycle events, checkpoints, and overlays.

`db/migrations/`
- Alembic migration history.
- Current head includes the Phase 6.1 binding-priority migration, after the Phase 6.0.0 routing-target-recommendation migration, the Phase 5.10.1 route-readiness audit migration, the Phase 5.1 routing target-choice migration, and the Phase 5.0 `routing_assessments` / `routing_assessment_candidates` substrate.
- Phases 5.2, 5.2.1, 5.3, and 5.3.1 add no migration; target-choice conversion and routed preparation/readiness lineage use existing `order_intents`, `execution_readiness_evaluations`, and structured provenance/idempotency.
- Phase 5.4 adds no migration; explicit routed submission uses existing `order_intents`, `execution_readiness_evaluations`, `submitted_orders`, and structured provenance/raw payload lineage.
- Phases 5.5, 5.6, 5.7, 5.7.1, 5.8, 5.8.1, 5.8.2, 5.9, 5.9.1, 5.9.2, 5.10, and 5.10.2 add no migration; routed submitted-order lineage/lifecycle/reconciliation-event inspection is derived from existing `submitted_orders.raw_payload`, reconciliation/update payload collisions cannot create, overwrite, or mutate platform `routed_submission` audit lineage, routed order-shape policy input/decision facts plus non-finite limit-price validation/reason-surface cleanup are handled through existing API/service models and child-intent provenance, Phase 5.10 closes the routing substrate with regression coverage rather than schema changes, and Phase 5.10.2 tightens route-readiness audit truth in service/tests/docs only.
- Phase 5.10.1 adds `20260419_0019_phase5101_route_readiness_audit.py`, a small durable audit migration for `route_readiness_audits` and `route_readiness_candidate_audits`; the tables are non-selecting data-sufficiency audit records only and do not store recommendations, rankings, scores, allocations, route plans, target choices, child intents, readiness evaluations, or submitted orders.
- Phase 6.0.0 adds `20260419_0020_phase600_routing_target_recommendation.py`, a small durable audit migration for `routing_target_recommendations`; the table stores non-executing `single_ready_candidate_only` recommendation/block outcomes and does not store rankings, scores, allocations, route plans, target choices, child intents, readiness evaluations, submitted orders, fanout, CBBO, or submit instructions.
- Phase 6.0.1 adds no migration; it hotpatches recommendation current-truth revalidation in service/tests/docs only.
- Phase 6.0.2 adds no migration; it hotpatches recommendation-time quote observation freshness checks and source audit `recommendation_created` truth in service/tests/docs only.
- Phase 6.1 adds `20260419_0021_phase61_binding_recommendation_priority.py`, a minimal nullable `target_recommendation_priority` field on `mandate_account_bindings` for the optional `explicit_binding_priority` recommendation policy. The field is operator preference only and does not store rank, score, venue quality, allocation, route plan, submit instruction, or execution behavior. Phase 6.1.1 adds no migration; it bounds accepted recommendation `policy_name` input, rejects malformed direct service policy names before persistence, and makes priority clearing explicit through existing binding APIs. Phase 6.2 adds no migration; recommendation acceptance uses existing routing target-choice rows plus existing recommendation/audit `target_choice_created` flags and provenance linkage. Phase 6.2.1 adds no migration; it hardens same-audit acceptance idempotency and timestamp provenance in service/tests/docs only. Phase 6.2.2 adds no migration; it gates same-audit idempotency so blocked recommendations cannot be marked accepted by an already accepted audit. Phase 6.3 adds no migration; accepted recommendation-backed target-choice conversion reuses existing `order_intents`, recommendation/audit `child_intent_created` flags, idempotency keys, and provenance lineage. Phase 6.4 adds no migration; recommendation-backed preview/readiness reuses existing `PreparedVenueOrder` and `ExecutionReadinessEvaluationModel` paths plus provenance-derived routed-lineage response fields. Phase 6.4.1 adds no migration; it hotpatches routed order-shape policy/current-intent drift checks plus readiness-time stale quote reason codes in service/tests/docs only. Phase 6.5 adds no migration; the manual routed-flow harness is tooling/tests/docs only and reuses existing service paths. Phase 6.6 adds no migration; manual harness timing is local tooling/tests/docs only and adds no telemetry persistence, route executor, config, or service-wide instrumentation. Phase 6.7 through Phase 6.10 add no migration; closeout reuses existing `order_intents`, `execution_readiness_evaluations`, `submitted_orders`, lifecycle-event rows, raw payload/provenance lineage, and read-only aggregation without new tables or config. Phase 6.10.1 adds `20260423_0022_phase6101_submission_leases.py`, a narrow `order_intent_submission_leases` guard table keyed by environment, intent id, and purpose so concurrent explicit submit calls for the same child intent cannot both reach adapter submission before a `SubmittedOrder` exists. Phase 6.10.2 adds `20260423_0023_phase6102_submission_lease_uncertainty.py`, widening only the lease status column so terminal `adapter_submit_persistence_unknown` can be stored when adapter submit returned but local submitted-order persistence failed. Phase 6.10.3 adds no migration because the widened status column and metadata JSON can store terminal `adapter_submit_may_have_started` state before adapter submission can begin. Phase 7.0 adds no migration; automation policy and dry-run plans are non-persisted API/service inspection models over existing routed workflow records. Phase 7.1 adds `20260426_0024_phase71_routing_automation_approvals.py`, a narrow durable `routing_automation_approvals` table for one-action operator approval gates with active/revoked/consumed/expired state, policy snapshots, lineage, and boundary flags. Phase 7.1.1 adds `20260430_0025_phase711_approval_truth_scope.py`, a narrow approval-truth migration adding lineage fingerprint/scope columns plus a partial unique active-scope index so only one active approval can exist for one current desired-trade/action/lineage scope. Phase 7.1.2 adds no migration; it tightens approval validation and gate-state truth so manual-only / dry-run-only / disabled / deferred / blocked / already-satisfied steps cannot create active approvals or appear approved. Phase 7.2 adds no migration; it consumes existing approval rows to call the existing recommendation acceptance path and records target-choice/no-downstream provenance in approval JSON fields. Phase 7.2.1 adds no migration; it refactors approval-gated acceptance to use one session/commit for target-choice creation or reuse plus approval consumption. Phase 7.3 adds no migration; it consumes existing approval rows to call the existing target-choice conversion validation/persistence helpers and records child-intent/no-downstream provenance in approval JSON fields. Phase 7.4 adds no migration; it consumes existing approval rows to call the existing child-intent prepared-order preview/readiness path and records preview/readiness/no-submission provenance in approval JSON fields. Phase 7.5 adds no migration; it consumes existing approval rows to call the existing explicit child-intent submit path, records submitted-order/no-route-executor/no-fanout/no-broad-auto-submit provenance in approval JSON fields, and relies on existing `submitted_orders` plus `order_intent_submission_leases`. Phase 7.5.1 adds no migration because the approval status column is already string-backed and approval JSON fields can record `consumption_pending` post-submit approval-consumption failure truth. Phase 7.6 adds no migration; it is closeout regression/docs coverage only and adds no action stage, persistence table, config, route executor, or broad auto-submit. Phase 8.0 adds no migration; operator workflow summaries are read-only aggregation over existing workflow, approval, readiness, submitted-order, and submission-lease records. Phase 8.0.1 also adds no migration; it is Obsidian/repo-memory hygiene only. Phase 8.0.2 adds no migration; it tightens read-only operator-summary truth for active unexpired submit leases in service/tests/docs only. SV1.0, SV1.0.1, SV1.1, SV1.2, SV1.2.1, SV1.3, SV1.4, SV1.4.1, SV1.5, and SV1.5.1 add no migration; strategy-validation reports, comparative batches, data-coverage diagnostics, market-regime summaries, window/coverage/grouped-comparison truth, campaign configs, evidence packs, canonical campaign configs, campaign data-readiness audits, review checklists, collision-safe evidence-pack write paths, Markdown readiness summaries, offline candle import/upsert tooling, and import-integrity validation use existing candle rows/tables and existing Money Flow logic, and simulated trades are not persisted as `SubmittedOrder` or live execution truth. Approval records do not act as `SubmittedOrder` reservations, and Phase 7.5 through SV1.5.1 add no route executor or broad auto-submit.
- SV1.6 through SV1.18 add no migration; canonical evidence-review summaries, DB target / reachability / schema / migration / candle-table gap truth, required strategy-validation table checks, canonical candle import requirements, partial-evidence status, first-real-run historical-data bootstrap reporting, schema-gated evidence-pack generation, DB-target evidence-generation blocking, candle-import timestamp/provenance summary hardening, intended local DB readiness reporting, de-duplicated import requirement grouping, research-only market-identity seed/verify, non-trading seed governance, requirement-aware candle preflight, guarded canonical candle bundle import, explicit partial-persistence reporting, operator-visible unmapped/missing requirement output, identity/file-readiness reporting, guarded import attempt reporting, public YTD/recent campaign planning, supported-venue public candle-readiness reporting, the operator-approved 9-file Hyperliquid public campaign guarded import, first Hyperliquid public campaign evidence-pack generation, dynamic-equity simulation, research-only hypothesis experiments, rejected-signal replay instrumentation, replay methodology-truth hardening, true replay experiment reporting, and evidence credibility closeout / UAT candidate freeze use existing campaign configs/tables and saved research outputs only.
- Phases 4.6 through 4.10.2 add no new migration and instead deepen lifecycle/private-state truth in service/adapter code.

`docs/architecture.md`
- Canonical architecture document at head.
- Consolidated source of truth for platform hierarchy, venue matrix, execution boundary, and below-routing lifecycle depth.

`docs/strategy.md`
- Canonical strategy document at head.
- Consolidated source of truth for indicator, decision, desired-trade, child-intent, readiness, submitted-order, and below-routing execution behavior.

`docs/strategy_validation_sv1_7_first_evidence_review.md`
- Founder/operator-readable SV1.7 gap report from the first real canonical evidence-review attempt.
- Records sanitized DB access findings, canonical campaign audit outcomes, no-pack generation status, and the concrete historical-data/schema gap before paper-trading design can be considered.

`docs/strategy_validation_sv1_14_trade_anatomy_and_market_structure.md`
- Founder/operator-readable SV1.14 diagnostics report.
- Explains current Money Flow readiness/entry/exit logic, ETH `sleeve_1h` anatomy, 15m and 4h weak anatomy, descriptive recent swing high/low market-structure context, and later-test hypotheses without changing rules.

`docs/strategy_validation_sv1_15_hypothesis_experiments.md`
- Founder/operator-readable SV1.15/SV1.15.1 controlled experiment and methodology-truth report.
- Compares isolated research-only overlays against the dynamic-equity baseline, includes RSI and entry-style attribution, records lower-RSI admission as requiring later rejected-signal replay instrumentation, labels each variant by methodology, downgrades recent-low invalidation to a lookahead diagnostic upper bound, and keeps every hypothesis outside production Money Flow.

`docs/strategy_validation_sv1_16_rejected_signal_replay.md`
- Founder/operator-readable SV1.16/SV1.16.1 replay-instrumentation and methodology-truth report.
- Summarizes per-candle replay context, rejected-signal capture, baseline-vs-lower-RSI true replay metrics for Hyperliquid ETH `sleeve_1h`, production-rule-in-replay-state semantics, variant-divergence truth, separated rejection/no-trade counters, and deferred true-replay work while keeping production Money Flow rules, paper/live trading, routing, and execution behavior unchanged.

`docs/strategy_validation_sv1_17_true_replay_experiments.md`
- Founder/operator-readable SV1.17 true replay experiment round-one report.
- Compares Hyperliquid BTC/ETH/SOL `sleeve_15m` / `sleeve_1h` / `sleeve_4h` baselines against lower-RSI plus market-structure variants under `dynamic_equity_pct`, with same-symbol/same-component baseline deltas and research-only/non-authorized status.

`docs/strategy_validation_sv1_17_true_replay_experiments_summary.json`
- Compact SV1.17 replay summary for the static dashboard.
- Contains only scenario-level replay rows and boundary flags, not raw generated evidence packs, local candles, DB files, trades, or per-candle contexts.

`docs/strategy_validation_sv1_18_evidence_closeout_and_uat_candidate_freeze.md`
- Founder/operator-readable SV1.18 evidence closeout and UAT planning report.
- Freezes exactly one UAT observation candidate, Hyperliquid ETH `sleeve_1h` baseline current rules, while excluding weak/experimental/cross-venue candidates and defining UAT0-UAT4 as future plumbing/behavior validation phases rather than paper/live trading.

`docs/strategy_validation_sv1_8_historical_data_bootstrap.md`
- Founder/operator-readable SV1.8 historical-data bootstrap and first-real evidence review report.
- Records sanitized DB target findings, Alembic/schema status, migration command hints, canonical campaign audit blockers, missing canonical candle requirements, and no-pack generation status.

`docs/strategy_validation_sv1_8_1_schema_truth_hotfix.md`
- Founder/operator-readable SV1.8.1 schema-truth hotfix report.

`docs/strategy_validation_sv1_9_first_real_evidence_status.md`
- Founder/operator-readable SV1.9 first-real canonical evidence status report covering intended DB target truth, migration/schema status, canonical candle gaps, import commands, and generated-pack status.
- Records that evidence-pack generation now requires `migrated_schema_ready`, current Alembic migration truth, and required `candles` / `instruments` / `symbols` table presence; no first real evidence packs are generated by this hotfix.

`docs/strategy_validation_sv1_9_1_evidence_target_truth_hotfix.md`
- Founder/operator-readable SV1.9.1 evidence-target truth hotfix report.
- Records that ambiguous/non-intended maintenance DB targets now block evidence generation by default, timezone-naive candle timestamps are rejected by default unless an explicit non-canonical override is used, import summaries include stronger source/timestamp provenance, and no first real canonical evidence packs were generated.

`docs/strategy_validation_sv1_10_first_real_evidence_status.md`
- Founder/operator-readable SV1.10 first-real evidence status report.
- Records the intended local DB target `money_flow` on `127.0.0.1:5432`, Alembic head migration truth, required table availability, zero persisted candles, 18 unique canonical import requirements, and no evidence-pack generation because candle data remains missing.

`docs/strategy_validation_sv1_11_market_identity_and_import_preflight.md`
- Founder/operator-readable SV1.11 market-identity and candle-import preflight report.
- Explains the research-only BTC/ETH/SOL Hyperliquid perpetual USDC identity manifest, dry-run / seed / verify-only commands, no-write candle preflight, and why candle import remains blocked until identity and file validation pass.

`docs/strategy_validation_sv1_11_1_preflight_and_identity_guard_hardening.md`
- Founder/operator-readable SV1.11.1 hardening report.
- Records that non-dry-run market-identity writes require explicit operator verification plus `verified_by`, row-level preflight is not canonical coverage proof, and requirement-aware preflight must map files to exact canonical close-time requirements before bulk import.

`docs/strategy_validation_sv1_11_2_seed_and_preflight_governance_hotfix.md`
- Founder/operator-readable SV1.11.2 governance hotfix report.
- Records that Strategy Validation market-identity seed cannot enable strategy/trading eligibility, requirement-aware preflight requires complete one-to-one input-to-requirement mapping, review JSON candle import requirements are preferred for candle preflight, and no candles/evidence packs are generated.

`docs/strategy_validation_sv1_12_canonical_candle_import_status.md`
- Founder/operator-readable SV1.12 guarded canonical candle import status report.
- Records the intended migrated DB gate, operator-verified research identity gate, complete one-to-one requirement-aware preflight gate, guarded importer behavior, no-evidence-pack boundary, remaining operational import gap, and SV1.12.1 `explicit_partial_with_resume` / unmapped-input / missing-requirement truth.

`docs/strategy_validation_sv1_12_1_canonical_candle_import_run.md`
- Founder/operator-readable SV1.12.1 guarded import run / blocked-run report.
- Records the checked intended DB status, missing BTC/ETH/SOL identity rows, absence of repo/session canonical candle files, no import attempt, no evidence-pack generation, and remaining gaps before SV1.13 can review evidence.

`docs/strategy_validation_sv1_12_2_identity_and_file_readiness.md`
- Founder/operator-readable SV1.12.2 identity and canonical candle-file readiness report.
- Records the intended DB/schema status, missing operator-verified BTC/ETH/SOL identity, exact 18 canonical timezone-explicit candle file requirements, no available local candle files, no preflight run, no candle import, no evidence-pack generation, and remaining readiness gaps before guarded import.

`docs/strategy_validation_sv1_12_3_guarded_import_result.md`
- Founder/operator-readable SV1.12.3 guarded import attempt report.
- Records the intended DB/schema status, missing operator-verified BTC/ETH/SOL identity, missing 18 canonical timezone-explicit candle files, no preflight-ready bundle, no candle import, no evidence-pack generation, and whether SV1.13 evidence review can proceed.

`docs/strategy_validation_sv1_12_x_hyperliquid_identity_and_candle_readiness_research.md`
- Founder/operator-readable SV1.12.x research data-preparation report.
- Records public Hyperliquid source docs/endpoints checked, verified BTC/ETH/SOL perp USDC identity values, the updated non-trading manifest basis, the 12 local timezone-explicit `1h`/`4h` CSV files produced under `/tmp`, the six missing `15m` files, hashes/provenance, and the blocked preflight/import state.

`docs/strategy_validation_sv1_12_4_public_ytd_recent_candle_readiness.md`
- Founder/operator-readable SV1.12.4 public-data-friendly Hyperliquid readiness report.
- Records why January 2026 `15m` is archival/vendor-data-required, the selected public `1h`/`4h` YTD and recent `15m` ranges, the 9 local timezone-explicit CSV files produced under `/tmp`, file hashes/provenance, and the blocked preflight/import state caused by missing operator-verified DB identity rows.

`docs/strategy_validation_sv1_12_5_supported_venues_public_candle_readiness.md`
- Founder/operator-readable SV1.12.5 supported-venue public candle readiness report.
- Records the supported adapter venues considered, public endpoints checked, selected YTD/recent windows, 45 additional local CSVs under `/tmp/money-flow-sv1125-supported-venues-public/csv`, Aster/Binance candidate preflight blockers, OKX/Coinbase trade-count limitations, Kraken REST coverage limitations, and the no-seed/no-import/no-evidence-pack boundary.

`docs/strategy_validation_sv1_12_5_public_campaign_import_result.md`
- Founder/operator-readable SV1.12.5 Hyperliquid public campaign import result.
- Records operator-approved research identity seed status, the 9 Hyperliquid public files imported from `/tmp/money-flow-sv1124-public-ytd-recent/csv`, clean file coverage/preflight truth, `25848` inserted candles, no evidence-pack generation, SV1.13 readiness, and supported-venue inventory boundaries.

`docs/strategy_validation_sv1_13_hyperliquid_public_evidence_review.md`
- Founder/operator-readable SV1.13 Hyperliquid public campaign evidence review.
- Records the intended DB/schema/identity/candle readiness reconfirmation, component-scoped evidence-pack paths, high-level observed fill-timing/component/symbol/regime/drawdown/no-trade/invalid-reason metrics, manual founder-review status, Hyperliquid-only scope, paper/live/recommendation boundary, and SV1.13.1 clarification that grouped totals are sums across research runs.

`docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md`
- Founder/operator-readable SV1.13.1 Hyperliquid evidence interpretation report.
- Separates grouped aggregate research metrics from scenario-level results, shows component/symbol/fill/cost/drawdown/cost-sensitivity evidence, makes ETH `sleeve_1h` concentration explicit, summarizes regime/no-trade/drawdown interpretation, and keeps paper-trading design deferred for manual founder review.

`docs/strategy_validation_sv1_13_2_dynamic_equity_evidence.md`
- Founder/operator-readable SV1.13.2 dynamic-equity evidence report.
- Explains constant-notional replay versus `dynamic_equity_pct`, reports sequential account-style starting/ending equity for Hyperliquid public campaign scenarios, shows ETH `sleeve_1h` dynamic results, summarizes 15m/1h/4h context, and keeps paper-trading design deferred.

`docs/investors.md`
- Plain-language investor-facing overview.
- Explains what Money Flow is today, what it is intentionally not yet, and where the product roadmap goes next without assuming trading-systems background.

`money_flow_project_memory.md`
- Compatibility pointer to `money-flow/Project_Memory/money_flow_project_memory.md`.
- Not the canonical full strategic-memory source.

`services/exchange/hyperliquid/`
- Most mature venue adapter for reconciliation depth and current perpetual submit scope.
- Deepest current lifecycle path.
- Truthful cancel acknowledgement, native limit-order amend, deeper order-status-plus-fill reconciliation, and direct private open-order/recent-fill/open-position polling now exist for the current perpetual scope where account context is available.
- Direct open-position mark price now uses venue `markPx`, derives from `positionValue / abs(szi)` when needed, and remains `None` when no truthful mark price can be derived.
- UAT0.2 classifies Hyperliquid `info` / `exchange` payloads by endpoint safety category and enforces runtime policy before private/signed/order transport.

`services/exchange/aster/`
- Perpetual adapter with submit, reconcile, cancel, and bounded same-target retry support.
- Strict client-order-id reuse semantics now handled with fresh retry IDs.
- Native amend remains explicitly unsupported; reconciliation now preserves canceled/expired-after-partial-fill truth.
- Private open-order polling is direct and returned as venue-private order snapshots.
- Summary-layer recent fills remain persistence-backed, but same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks when no exchange order id exists.
- Ambiguous retry fill evidence remains scoped to `SubmittedOrderPrivateFillEvidence` and is not exposed through a plain submitted-order fill convenience method.

`services/exchange/okx/`
- Spot/perpetual adapter with submit, reconcile, truthful cancel lifecycle, bounded recovery execution, native amend, and direct private open-order/recent-fill polling with runtime-truthful source reporting.

`services/exchange/coinbase/`
- Spot adapter with JWT submit, reconcile, truthful cancel lifecycle, bounded recovery execution, native edit-order amend for the current spot limit-order scope, and direct private open-order/recent-fill polling with runtime-truthful source reporting.

`services/exchange/binance/`
- Spot adapter with submit, reconcile, cancel, and bounded same-target retry support.
- Strict client-order-id reuse semantics now handled with fresh retry IDs.
- Native amend remains explicitly unsupported at head.
- Private open-order polling is direct and returned as venue-private order snapshots.
- Summary-layer recent fills remain persistence-backed, but same-target retry safety can use submitted-at-bounded direct same-account/same-symbol private trade ambiguity checks when no exchange order id exists.
- Ambiguous retry fill evidence remains scoped to `SubmittedOrderPrivateFillEvidence` and is not exposed through a plain submitted-order fill convenience method.

`services/exchange/kraken/`
- Spot adapter with submit, reconcile, truthful cancel acknowledgement plus later cancel reconciliation, and bounded recovery execution.
- Native amend now exists for the current spot limit-order scope.
- Direct private open-order and recent-fill polling now exist for the current scope, with runtime-truthful source reporting.

`services/exchange/registry.py`
- Venue registry/factory used by the control plane to inspect Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken side by side.

`services/exchange/safety.py`
- UAT0.2 exchange endpoint safety policy helpers.
- Defines endpoint categories, REST/Hyperliquid payload classifiers, runtime-policy enforcement decisions, and the Hyperliquid future-UAT1 read-only allowlist artifact.
- UAT0.3 extends the Hyperliquid public info-type allowlist/classification to cover the future UAT1 public-read-only set: `meta`, `metaAndAssetCtxs`, `allMids`, `l2Book`, `candleSnapshot`, and `fundingHistory`.

`services/uat/`
- UAT readiness policy helpers.
- UAT0.3 adds fixture-only top-20 observation universe resolver models and runtime drawdown monitor models. UAT1 adds explicit public-read-only connectivity helpers for allowed Hyperliquid info types, no-key public top-volume source parsing, Hyperliquid metadata intersection, per-included-asset public sample checks, report rendering, and JSON serialization. UAT1.1 adds model/report-only shadow signal audit records, UAT2 timing policy representation, no-live-artifact boundary checks, UAT1 universe snapshot loading, operator-visible shadow drawdown state, and representative API-error / structured-log redaction verification helpers. UAT2 adds a bounded no-order shadow run service that fetches only public Hyperliquid `candleSnapshot` data under explicit UAT2 flags, evaluates current baseline Money Flow rule logic without creating production decision/signal/order artifacts, emits shadow audit records, and renders Markdown/JSON summaries. UAT helpers require explicit public-read-only mode/network flags for public calls and do not call private/signed/order endpoints, use API keys, submit orders, approve paper/live trading, create StrategyDecision/SignalEvent/OrderIntent/PreparedVenueOrder/ExecutionReadinessAssessment/SubmittedOrder artifacts, create approvals/routing artifacts, or change Money Flow rules.
- UAT3.1 is the narrow exception to the no-order UAT helper baseline: `services/uat/sandbox_order.py` supports exactly one founder-approved Hyperliquid testnet ETH manual lifecycle probe and still creates no production execution artifacts, no paper/live behavior, no routing expansion, and no repeated/broad submission behavior. UAT3.2 extends the helper with fixed-key account/API-wallet readiness and blocks before order transport when the testnet user/API wallet or equity gates fail.

`services/paper_runtime/`
- PT-RT1 public-mainnet paper-observation primitives.
- `services/paper_runtime/pt_rt1.py` validates Hyperliquid public mainnet strategy-truth payloads, resolves top-20 scanner eligibility, enforces fully closed candle gating, computes paper-observation indicators without defaulting missing fields to zero, models independent 10,000 USDC synthetic paper ledgers, prevents duplicate synthetic signals, defines the required Money Flow/SOR/MF-ORIG/wildcard observation lanes, evaluates synthetic paper decisions, and evaluates disabled-by-default Hyperliquid testnet plumbing-probe gates. Fresh PT-RT scanner runs defer `TRUMP` with reason `runtime_noise_deferred_by_founder` while preserving existing historical evidence artifacts as historical truth. PT-RT1.4 adds active review timeframe policy: `1h`/`4h`/`1d` active, `15m` disabled for Week 1 noise reduction and preserved as paused/legacy data. PT-RT1.5 adds active scope constants, candle-close scheduler status, retry/dedup reason codes, and `PT_RT15BaselineTestnetOrderPolicy` for Money Flow v1.2 baseline-only fixed 25 USDC Hyperliquid testnet order shapes/lifecycle rows. PT-RT1.5.2 adds testnet API-root URL acceptance while still rejecting live/mainnet URLs, the PT-RT1.5.2 smoke/active scopes, and the exact PT-RT1.5.2 approval text. PT-RT1.5.3 adds testnet size/precision hotfix constants, exact approval text, testnet metadata resolved flags, raw/formatted quantity and estimated-notional lifecycle fields, invalid-size preflight, and venue invalid-size reason codes. It does not import production Money Flow rule changes, call private/signed/order endpoints from strategy truth, use API keys for strategy truth, create production execution artifacts, or let testnet fills update paper PnL.
- `services/paper_runtime/hyperliquid_public_market_data.py` is the PT-RT1 public-read-only Hyperliquid mainnet connector. It calls only allowlisted `/info` payloads, normalizes `meta`, `allMids`, and `candleSnapshot`, resolves requested vs venue watchlist rows with reason codes, validates OHLC/timestamp truth, and exposes data-health status without credentials, private/signed/order endpoints, testnet prices as strategy truth, or order artifacts. Under PT-RT1.3, missing or stale mids are warning-only when clean fully closed candles are available.

`services/market_data/`
- Candle bootstrap, persistence, checkpoint semantics, and freshness handling.

`services/indicators/`
- Deterministic indicator computation and snapshot persistence.

`services/strategy/`
- Strategy framework and Money Flow strategy family.

`services/strategy_validation/`
- SV1.0 / SV1.0.1 / SV1.1 / SV1.2 / SV1.2.1 / SV1.3 / SV1.4 / SV1.4.1 / SV1.5 / SV1.5.1 / SV1.6 / SV1.7 / SV1.8 / SV1.8.1 / SV1.9 / SV1.9.1 / SV1.10 Money Flow validation/backtesting, research-campaign, evidence-readiness, evidence-integrity, historical-data readiness, evidence-review, DB/schema bootstrap, schema-gated first-real-run data-gap, evidence-target truth, candle-import timestamp/provenance, intended local DB readiness, and canonical import requirement grouping service boundary.
- Reads persisted historical candles, computes indicator snapshots in memory, reuses the current Money Flow strategy rules, simulates research-only trades with explicit fee/slippage/capital/fill-timing assumptions, and returns deterministic component and aggregate performance reports.
- SV1.0.1 supports `same_candle_close_research_only`, `next_candle_open`, and `next_candle_close` fill timing; reports closed-trade and mark-to-market drawdown separately; and emits expanded founder/operator Markdown reports with assumptions, component comparison, trade summaries, reason counts, and limitations.
- SV1.1 adds deterministic batch validation and comparison reports across explicit component, fill-timing, symbol, date-window, fee, and slippage assumptions. Comparison output is descriptive research only and does not optimize, recommend a variant, change Money Flow rules, route, or execute.
- SV1.2 adds deterministic data-coverage diagnostics, simple trend/volatility regime labels, regime-grouped performance summaries, and multi-window batch reporting support. Regimes are descriptive only and do not change strategy behavior.
- SV1.2.1 standardizes all validation windows on candle closes in `(start_at, end_at]`, counts expected close slots for coverage, warning-codes unaligned window boundaries, prevents coverage above 100%, and keeps blocked runs visible in grouped batch comparisons while computing metrics only from completed runs. It changes no Money Flow rules, optimization, routing, execution automation, exchange calls, paper/live trading, or live artifacts.
- SV1.3 adds campaign helpers that parse explicit JSON campaign configs, expand named symbols/components/fill timings/windows/cost assumptions into existing batch requests, and write timestamped evidence packs containing normalized config, manifest, JSON, Markdown, and README files. Campaign output preserves window-convention and blocked-run truth and remains research-only.
- SV1.4 adds persisted-candle campaign data-readiness audit helpers, JSON-ready audit output, evidence-pack review checklist content, and manual paper-trading readiness criteria. These surfaces are manual review aids only and create no paper/live trading artifacts.
- SV1.4.1 makes evidence-pack writes collision-safe: default `unique_suffix` creates a suffixed run directory instead of overwriting an existing pack, optional `fail_if_exists` raises explicitly, and manifests record requested/final run ids, final path, collision policy, collision occurrence, and suffix truth.
- SV1.5 validates campaign `window_convention` metadata against the platform `(start_at, end_at]` convention, adds founder-readable Markdown data-readiness audit output, and adds offline public CSV/JSON candle import/upsert helpers for research historical-data gaps.
- SV1.5.1 hardens campaign/import truth: contradictory inclusive-start `window_convention` text is rejected, existing candles cannot be silently retargeted to another resolved symbol/instrument identity, imported row duration must match the selected timeframe, malformed/non-finite/inconsistent OHLCV and negative trade counts fail, and invalid import files roll back without partial inserts or updates.
- SV1.6 adds first canonical evidence-review helpers that audit canonical configs, generate collision-safe evidence packs only when data-readiness is sufficient, summarize evidence-pack paths/data gaps/fill-timing/component/regime/drawdown/cost observations, and expose manual paper-readiness review status without approving paper trading.
- SV1.7 adds sanitized DB access inspection, candle-table existence and persisted-candle-count truth, synthetic blocked data-readiness rows for unreachable/missing-schema databases, `partial_evidence_ready_with_data_gaps` mixed-result status, and a tracked first-real-run gap report for canonical campaigns.
- SV1.8 adds DB/schema/migration bootstrap status, Alembic head/current truth, migration hints, and a status-only evidence-review CLI path before first real evidence packs.
- SV1.8.1 requires `migrated_schema_ready` plus required `candles`, `instruments`, and `symbols` tables before evidence-pack generation, and aggregates top-level live/exchange flags from campaign results.
- SV1.9 makes the strategy-validation DB target explicit in evidence-review output, including sanitized driver/host/port/name/user, target-role classification, intended-DB truth, maintenance-database warnings, and canonical candle import requirements for blocked or missing readiness rows. The local SV1.9 review generated no real evidence packs because the default `postgres` host was unresolved and the explicit `127.0.0.1:54322/postgres` override was unreachable in this shell and is also a maintenance database name requiring operator confirmation.
- SV1.9.1 makes ambiguous/non-intended maintenance DB targets generation-blocking by default, rejects timezone-naive candle imports by default, exposes `--assume-naive-utc` as a provenance-marked non-default import override, records source file name/hash/row-count/timestamp-assumption import summary truth, and refreshes Obsidian current-state memory through SV1.9.
- STRAT-DISC1 adds a self-contained research-only discovery harness that reads local selected replay JSON, validates candle data, tests bounded curated hypotheses, labels candidates/rejections, and writes no trading/runtime artifacts.
- SV1.10 records the intended local strategy-validation target as `money_flow` on `127.0.0.1:5432`, applies Alembic head locally when available, verifies required tables, groups overlapping canonical BTC import requirements across campaigns, and reports the remaining zero-candle `insufficient_data` gap without generating evidence packs.
- SV1.11 adds research-only market identity seed/verify helpers for canonical BTC/ETH/SOL Hyperliquid perpetual USDC instruments/symbol mappings, evidence-review canonical identity readiness reporting, and candle-import preflight that validates files/mappings without writing candles. SV1.11.1 hardens this boundary so non-dry-run identity writes require explicit operator verification/verified-by provenance, and requirement-aware preflight can prove a mapped input file covers the exact canonical close-time slots before import. SV1.11.2 blocks true strategy/trading eligibility in this research seed path and requires complete one-to-one input-to-requirement mapping before requirement-aware readiness can pass. SV1.12 adds a guarded canonical candle bundle import orchestrator that requires an intended migrated non-maintenance DB, operator-verified non-trading research identity, complete one-to-one requirement-aware preflight, and then delegates only preflight-passed files to the hardened candle importer; it generates no evidence packs and creates no live artifacts. SV1.12.2 adds `services/strategy_validation/import_readiness.py` so operators can check DB/schema status, optionally seed only explicitly verified research identity, list the exact 18 canonical candle-file requirements, and run preflight-only checks without importing candles. SV1.12.3 adds `services/strategy_validation/guarded_import_attempt.py`, which combines explicit identity-seed gates, canonical filename discovery, complete requirement mapping, guarded bundle import, and founder-readable final status without generating evidence packs. SV1.12.5 adds `services/strategy_validation/public_campaign_import.py`, which builds the 9-file Hyperliquid public YTD/recent campaign requirements, separates file coverage truth from DB identity readiness, can regenerate missing files from public Hyperliquid `candleSnapshot`, seeds only approved research identity, records supported-venue inventory, and runs guarded import without evidence-pack generation. SV1.13 adds public-campaign evidence expansion for `timeframe_windows`, preserving Hyperliquid-only component-scoped evidence generation and manifest no-live/no-routing/no-exchange truth. SV1.13.1 adds grouped aggregate semantics aliases/Markdown labels and a founder interpretation report; it changes no strategy rules or evidence numbers. SV1.13.2 adds first-class `dynamic_equity_pct` capital sizing, equity/account metrics, campaign/CLI capital-mode expansion, and a dynamic-equity founder report without changing strategy rules. SV1.14 adds `services/strategy_validation/trade_anatomy.py`, a descriptive diagnostics module that reads existing batch reports and optional persisted candles, summarizes trade anatomy, computes recent swing high/low context, and emits later-test hypotheses without changing strategy rules. SV1.15 adds `services/strategy_validation/hypothesis_experiments.py`, a Strategy Validation-only experiment module that compares isolated overlay variants and attribution against the dynamic-equity baseline without modifying production Money Flow. SV1.16 adds `services/strategy_validation/replay.py`, a research-only replay module that captures per-candle production-rule decisions/rejections and runs chronological variant replays with position occupancy plus dynamic-equity sizing. SV1.16.1 hardens that module with explicit production-rule-in-replay-state fields, variant divergence metadata, and separated rejection/admission/no-trade counters so broader replay experiments have unambiguous methodology truth. SOR-EV1 adds `services/strategy_validation/sor_ev1.py`, which reads only canonical SV2.0.2 DB-imported batch reports and produces evidence-only loss anatomy, fixed-stop overlay diagnostics, deferred true-replay variant status, control-pocket impact, JSON export, and boundary flags without changing production rules or creating trading artifacts. SOR-EV2 adds `services/strategy_validation/sor_ev2.py`, which replays canonical SV2.0.2 scenarios from persisted candle truth, measures baseline parity, evaluates fixed/ATR/recent-low/large-bear stop exits plus MACD/RSI/extension/chop entry variants as true-forward evidence, reports rejected-signal and large-loss candle context, and still creates no trading artifacts. SOR-EV3 adds `services/strategy_validation/sor_ev3.py`, which true-forward replays the founder-selected `avoid_sideways_low_volatility` family, computes past/current-candle-only regime features, measures blocked-entry attribution, loss concentration, avoided losers, missed winners, and control-pocket impact, and still creates no production rule changes or trading artifacts. MF-ORIG-EV1.1 updates `services/strategy_validation/mf_orig_ev1.py`, a Strategy Validation-only original Money Flow reconstruction that reads canonical SV2.0.2 pack references, treats 1d as primary source timeframe, models Stage 1-4 / 5EMA-20SMA triggers / RSI warning trims / MACD substitute warnings / prior support stop proxies / 1% risk sizing, and writes no trading artifacts. The hotpatch replaces unreliable pre-hotpatch accounting/drawdown outputs with event-ledger accounting, single-counted fees/trims, peak-to-trough drawdown, and truthful baseline-positive 1d control-pocket labeling.
- Creates no live desired trades, strategy decisions, child intents, prepared orders, readiness evaluations, submitted orders, routing artifacts, approval changes, private exchange calls, exchange order calls, or exchange adapter calls.

`services/planning/`
- Mandate-level desired-trade drafting, source-policy inspection, convertibility checks, routing-candidate derivation, and normalized quote inspection ahead of later routing.

`services/routing/`
- Routing assessment, route-readiness audit, controlled non-executing target recommendation, target-choice audit, and explicit one-child-intent conversion substrate for `routing_required` mandate-scoped opens.
- Phase 7.0 adds non-executing routing automation policy and dry-run plan inspection over existing routed workflow records; it creates no artifacts and advances no workflow state.
- Phase 7.1 adds durable operator approval records for explicit same-target automation action gates; Phase 7.1.1 makes reuse lineage-scoped and current-truth-bound, and Phase 7.1.2 keeps approval validity bounded to currently approvable policy states, so approvals can be active, revoked, consumed, expired, stale-lineage, or Phase 7.5.1 `consumption_pending` after post-submit approval-consumption failure. Phase 7.2 adds the first approval-consuming action hook: recommendation acceptance into a target choice only. Phase 7.2.1 keeps that hook coherent by committing target-choice creation/reuse and approval consumption together. Phase 7.3 adds the second approval-consuming action hook: target-choice conversion into one child intent only. Phase 7.4 adds the third approval-consuming action hook: prepared-order preview/readiness inspection for one existing child intent only. Phase 7.5 adds the fourth approval-consuming action hook: submitted-order handoff for one already-ready child intent through the existing explicit submit path only. Phase 7.5.1 ensures a submitted order plus failed approval consumption is inspectable and repeatable without another adapter submit. Phase 7.6 adds closeout regression coverage proving the accepted Phase 7 chain remains approval-gated, current-lineage-bound, same-target, and separate from dry-run/admin-consume behavior.
- Phase 8.0 adds read-only operator routed workflow summaries by desired trade, combining existing routed workflow records, approval/gate state, manual-resolution requirements, submitted-order handoff safety, and submit-lease/concurrency state without creating artifacts, consuming approvals, resolving manual states, calling adapters, or adding trading behavior. Phase 8.0.2 makes unexpired active submit leases block repeat-submit safety and next-safe-action truth as `submission_in_progress`, while terminal uncertainty remains manual-reconciliation-required and expired pre-adapter active leases remain stale-replaceable.
- Persists candidate inventory, binary binding eligibility/ineligibility status, reason codes, missing-data facts, and operator-requested target-choice audit records; Phase 5.2 can convert one explicit valid target choice into one binding/account-targeted child intent without preparation, readiness evaluation, submission, splitting, ranking, or scoring, and Phase 5.2.1 hardens assessment / desired-trade / binding lineage checks before conversion.
- Converted routed child intents use Phase 5.8 explicit order-shape policy input/decision: omitted policy remains market order, no limit price, and reduce_only=false; explicit LIMIT requires a positive finite requested limit price and modeled order-type support. Phase 5.8.1 blocks non-finite LIMIT prices before child-intent creation, and Phase 5.8.2 keeps malformed/non-finite blocks from claiming `limit_price_explicit`. Slippage guards and market-data-derived price sources remain deferred.
- Phase 5.10.1 adds a non-selecting route-readiness/data-sufficiency audit beside routing assessment. It can audit a routing-required desired trade or existing routing assessment for missing, stale, unsupported, unavailable, policy-blocked, and blocking facts per candidate, with explicit data-source labels and `ready_for_recommendation` meaning data-sufficient only; it does not recommend, rank, score, choose, convert, prepare, assess execution readiness, submit, or execute. Phase 5.10.2 hotpatches audit truth so assessment-backed quote facts are not mislabeled as fresh venue queries, missing/invalid desired-trade side or quantity blocks readiness, malformed/non-finite/non-positive quote prices are reason-coded before notional math, and default MARKET policy is labeled defaulted rather than explicit.
- Phase 6.0.0 adds persisted non-executing `RoutingTargetRecommendation` records from route-readiness audits only. Phase 6.0.1 hotpatches current-truth revalidation so success also requires current mandate enablement, desired-trade symbol identity, and active/trading-eligible venue symbol mapping truth. Phase 6.0.2 hotpatches recommendation-time freshness so the recommended candidate's stored `quote_observed_at` must still be fresh and the source audit reports `recommendation_created=true` after any recommendation record is persisted. Phase 6.1 keeps `single_ready_candidate_only` as the default policy and adds optional `explicit_binding_priority`: lower positive operator-configured `MandateAccountBinding.target_recommendation_priority` wins only when one ready candidate has the winning priority; missing/malformed priority and ties block. Phase 6.1.1 bounds `policy_name` input to accepted values at the API boundary, keeps malformed/oversized direct service policy input out of persistence, preserves omitted priority on binding updates, clears priority only through `clear_target_recommendation_priority=true`, and verifies priority-selected candidates still block on stale quote observations. Phase 6.2 adds explicit operator-triggered recommendation acceptance into exactly one non-executing `RoutingTargetChoice` after revalidating recommendation status, audit/recommendation freshness, stored quote observation freshness, desired-trade/mandate/binding/account/symbol truth, and idempotency; repeated acceptance returns the existing choice. Phase 6.2.1 prevents duplicate successful recommendations from one route-readiness audit from creating multiple accepted target choices, returns the original choice, marks the later recommendation as linked, and preserves the original recommendation/audit acceptance timestamp while recording idempotent checks separately. Phase 6.2.2 gates same-audit idempotency behind successful-recommendation preflight so blocked recommendations from an already accepted audit cannot be marked `target_choice_created` or stamped with accepted-looking provenance. Phase 6.3 reuses the existing target-choice conversion path so an accepted recommendation-backed target choice can be explicitly converted into exactly one routed child `OrderIntent` after recommendation/audit/quote/current-truth revalidation, while repeated and same-audit duplicate conversion attempts return the existing child intent. Phase 6.4 lets those recommendation-backed child intents use the existing prepared-order preview and submission-readiness inspection paths with recommendation/audit/candidate quote/current-truth validation and top-level routed-lineage API response fields. Phase 6.4.1 blocks readiness if stored routed order-shape policy is missing, malformed, or mismatched against current child-intent order_type, limit_price, or reduce_only facts, and it reports stale stored quote observations at this surface with `quote_stale_at_readiness`. Phase 6.9 adds read-only routed workflow inspection by desired trade, aggregating existing desired trade, assessment, audit, recommendation, target choice, child intent, readiness, submitted-order, and lifecycle-event records without creating or mutating artifacts. Recommendations still do not use ranking, scoring, price comparison, CBBO, automatic target-choice creation, automatic child-intent creation, fanout, allocation, route plans, target reselection, or route executor behavior; submitted orders occur only after explicit child-intent submit gates pass.

`services/risk/`
- First-pass desired-trade approval/rejection layer.

`services/execution/`
- Child-intent preparation, hardened routed child-intent lineage validation before preview/readiness/submission, venue-native preview/preflight, execution readiness, submission for supported non-routed child-intent paths, explicit gated routed submission for already selected converted child intents, submitted-order lifecycle, routed post-submit lifecycle/actionability/reconciliation-event context, recovery recommendations, bounded same-target recovery execution, truthful cancel on supported scopes, selective native amend execution, amend-acknowledgement follow-up through later reconciliation, fill-merge preservation of terminal / cancel-pending submitted-order truth, and deeper downstream reliance on venue/account private-state inspection.
- Recommendation-backed routed preview/readiness validates source recommendation/audit/current truth, stored quote observation freshness, and stored routed order-shape policy against the current child intent shape before adapter preparation can proceed. Phase 6.7 submitted-order handoff uses the existing explicit submit path for the already selected recommendation-backed child intent, requires the normal live-submit and routed-submit gates plus current readiness, and stamps desired-trade, assessment, route-readiness audit, recommendation, target choice, intent, readiness, selected target, recommendation policy, routed order-shape policy, and no-fanout/no-allocation/no-scoring/no-target-reselection/no-auto-submit flags into the submitted-order routed payload. Phase 6.10.1 adds a narrow persistence-backed child-intent submit lease before adapter submission so concurrent explicit submit calls for one intent cannot both reach the adapter before a `SubmittedOrder` exists. Phase 6.10.2 marks adapter-returned/local-persistence-failed attempts as terminal `adapter_submit_persistence_unknown`, records manual-reconciliation metadata, and blocks future submits for that intent before adapter submission even after TTL. Phase 6.10.3 marks terminal `adapter_submit_may_have_started` before calling the adapter, so crashes, timeouts, transport ambiguity, and unknown post-call adapter exceptions cannot become TTL-retryable; stale pre-adapter `active` leases remain replaceable. The lease is not submitted-order truth or a route executor.
- Routed submitted-order lineage remains read-only audit metadata derived from platform-authored `SubmittedOrder.raw_payload["routed_submission"]`; missing, partial, or wrong-typed routed payloads are bounded through the shared domain parser and do not drive target reselection or lifecycle behavior. Phase 5.7 exposes routed lifecycle context on recovery/actionability surfaces while keeping recovery same-target / same-account / same-venue only, Phase 5.7.1 preserves that lineage on same-target routed retry results, Phase 5.9 preserves routed audit payload through reconciliation updates while exposing routed context on lifecycle-event responses, Phase 5.9.1 makes current platform lineage authoritative over colliding update-payload `routed_submission` keys, Phase 5.9.2 strips update-payload `routed_submission` from non-routed submitted-order raw payloads so adapters cannot fabricate routed origin, and Phase 5.10 closeout coverage verifies those existing surfaces remain consistent without adding execution behavior.
- Retry evidence remains same-target and conservative: live venue-private open-order proof blocks retry, while Aster/Binance private trade evidence without an exchange order id is recorded as submitted-at-bounded same-account/same-symbol ambiguity rather than targeted order fill proof and cannot be fetched as plain submitted-order fill truth.

`services/portfolio/`
- Portfolio/account-truth loaders and related summaries.

`scripts/`
- Local developer and review-support utilities.
- Includes `scripts/create_review_bundle.py` for deterministic review ZIP creation based on `.archiveignore`.
- Includes `scripts/manual_routed_flow.py` for Phase 6.5 manual routed-flow inspection from an existing desired trade key through optional existing service calls to readiness. It emits JSON, includes Phase 6.6 local `timing_ms` / per-step `elapsed_ms` fields, skips submission by default, and blocks submit attempts unless the explicit danger-confirmation flag is supplied.
- Includes `scripts/run_money_flow_backtest.py` for SV1.0/SV1.0.1 read-only Money Flow strategy-validation reports over persisted candles with explicit assumptions, selectable fill timing, and JSON/Markdown output.
- Includes `scripts/run_money_flow_validation_batch.py` for SV1.1/SV1.2/SV1.2.1 read-only comparative Money Flow validation across explicit matrices of components, fill timings, symbols, date windows, and cost assumptions, including repeated `--window start,end` support using candle closes in `(start, end]`.
- Includes `scripts/run_money_flow_research_campaign.py` for SV1.3/SV1.4/SV1.4.1/SV1.5 read-only Money Flow campaign configs, evidence-pack output, `--audit-only` persisted-candle readiness inspection, Markdown audit output, and explicit evidence-pack collision policy. It writes saved research reports only when not in audit-only mode and does not optimize, recommend, route, trade, or call exchange adapters.
- Includes `scripts/import_strategy_validation_candles.py` for SV1.5/SV1.5.1/SV1.9.1 offline/public CSV or JSON candle imports into existing `candles` rows. It is duplicate-safe for matching candle identity, rejects identity conflicts, timeframe-duration mismatches, malformed/non-finite/inconsistent OHLCV rows, negative trade counts, and timezone-naive timestamps by default, rolls back invalid files, records source file/hash/timestamp-assumption summary provenance, and remains research-only; it does not call exchange adapters, private endpoints, order endpoints, or create live trading artifacts.
- Includes `scripts/review_money_flow_evidence_packs.py` for SV1.6/SV1.7/SV1.8/SV1.8.1/SV1.9/SV1.9.1 read-only canonical evidence review. It audits canonical campaign configs by default, reports sanitized DB target/reachability/schema/migration/candle-table status, supports `--db-status-only`, optionally generates collision-safe evidence packs only when schema, target, and data-readiness are sufficient, emits JSON/Markdown review summaries plus canonical candle import requirements for blocked rows, and does not optimize, recommend, route, trade, or call exchange adapters.
- Includes `scripts/seed_strategy_validation_market_identity.py` for SV1.11/SV1.11.2 offline/manual research-only market identity seed/verify from manifest. It upserts only `instruments` and `symbols`, refuses symbol/instrument retargeting conflicts, rejects true strategy/trading eligibility, supports `--dry-run` / `--verify-only`, requires `--operator-verified --verified-by` for non-dry-run writes, and creates no candles, evidence packs, exchange calls, routing artifacts, or live artifacts.
- Includes `scripts/preflight_strategy_validation_candle_import.py` for SV1.11/SV1.11.2 candle-import preflight. It validates CSV/JSON candle files and/or evidence-review requirements without writing candles, rejects timezone-naive timestamps by default through the same validation semantics, verifies symbol/instrument mappings, supports requirement-aware complete one-to-one input-to-requirement coverage checks, prefers candle import requirements from review JSON when present, and creates no evidence packs, exchange calls, routing artifacts, or live artifacts.
- Includes `scripts/import_strategy_validation_candle_bundle.py` for SV1.12/SV1.12.1 guarded canonical candle bundle import. It requires the intended migrated non-maintenance strategy-validation DB, operator-verified research-only/non-trading market identity, complete one-to-one requirement-aware preflight, and then imports only preflight-passed timezone-explicit files through the hardened candle importer. SV1.12.1 reports explicit `partial_import` / `explicit_partial_with_resume` truth if a later file fails after earlier per-file persistence, surfaces unmapped inputs / missing requirements directly, and creates no evidence packs, exchange calls, routing artifacts, paper/live artifacts, or trading artifacts.
- Includes `scripts/check_strategy_validation_import_readiness.py` for SV1.12.2 readiness reporting. It can check DB/schema/identity/file readiness, optionally call the verified seed workflow only with explicit operator verification, emit the exact canonical 18-file checklist, and run preflight-only validation without importing candles or generating evidence packs.
- Includes `scripts/run_strategy_validation_guarded_import_attempt.py` for SV1.12.3 guarded import attempts. It can seed research identity only with explicit operator verification plus offline value confirmation, auto-discovers canonical files by the suggested filenames, runs guarded import only after complete preflight readiness, and emits JSON/Markdown without generating evidence packs.
- Includes `scripts/prepare_supported_venue_public_candles.py` for SV1.12.5 public-only supported-venue candle preparation. It calls public market-data endpoints only, uses no API keys, writes timezone-explicit local CSV/provenance outputs under `/tmp/money-flow-sv1125-supported-venues-public`, and does not seed identity, import candles, generate evidence packs, or call private/signed/order endpoints.
- Includes `scripts/run_strategy_validation_public_campaign_import.py` for the operator-approved SV1.12.5 Hyperliquid public-campaign bridge. It can seed BTC/ETH/SOL research identity only with explicit `--operator-verified --verified-by ... --market-identity-values-checked-offline`, maps the 9 public campaign files, runs requirement-aware preflight plus guarded import when gates pass, records supported-venue inventory, and generates no evidence packs.
- Includes `scripts/run_money_flow_trade_anatomy_diagnostics.py` for SV1.14 founder diagnostics. It reads existing Strategy Validation batch reports and, when DB candles are available, loads persisted candles for descriptive market-structure context. It writes founder-readable Markdown/optional JSON only and does not alter Money Flow rules, import candles, generate evidence packs, call exchanges, or create paper/live/routing artifacts.
- Includes `scripts/run_money_flow_hypothesis_experiments.py` for SV1.15 founder experiment reporting. It reads existing dynamic-equity Strategy Validation batch reports and optional DB candles, compares research-only overlays against baseline, and writes Markdown/optional JSON without altering Money Flow rules, importing candles, generating evidence packs, calling exchanges, or creating paper/live/routing artifacts.
- Includes `scripts/run_money_flow_true_replay.py` for SV1.16/SV1.16.1 replay instrumentation. It runs baseline and lower-RSI trend-intact research replays over imported candles, writes Markdown/optional JSON with replay-state semantics and separated counters, and creates no evidence packs, imports, exchange calls, paper/live artifacts, routing artifacts, or production Money Flow rule changes.
- Includes `scripts/run_money_flow_true_replay_experiments.py` for SV1.17 true replay experiment reporting. It compares a small set of research-only lower-RSI plus market-structure variants against matching baselines under `dynamic_equity_pct`, supports `--full-suite` for BTC/ETH/SOL x 15m/1h/4h, writes Markdown/optional JSON/compact summary output, and creates no evidence packs, imports, exchange calls, paper/live artifacts, routing artifacts, or production Money Flow rule changes.
- Includes `scripts/run_sv202_canonical_import_and_evidence.py` for SV2.0.2 hardened DB import plus canonical evidence-pack generation. It is public-mainnet strategy-validation evidence only, requires an intended migrated DB target before importing/generating packs, preserves import/staging truth fields, and creates no order/private/signed/live endpoint behavior.
- Includes `scripts/build_sv202_dashboard_chart_data.py` for SV2.0.2 Historical Replay display JSON. It derives ignored dashboard chart/trade files from existing public-candle JSON and existing canonical batch reports without importing candles, regenerating evidence packs, calling exchanges, or changing strategy rules.
- Includes `scripts/build_sor_ev1_loss_anatomy.py` for SOR-EV1 evidence-only loss anatomy and variant diagnostics. It writes `docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md` and the companion JSON summary from canonical SV2.0.2 pack paths only.
- Includes `scripts/build_sor_ev2_true_forward_replay.py` for SOR-EV2 true-forward stop/exit and rejected-signal replay. It writes `docs/sor_ev2_true_forward_stop_and_rejected_signal_replay.md` and the companion JSON summary from canonical SV2.0.2 pack references plus persisted candle truth.
- Includes `scripts/build_sor_ev3_avoid_sideways_low_volatility.py` for SOR-EV3 founder-selected low-volatility/chop drilldown. It writes `docs/sor_ev3_avoid_sideways_low_volatility.md` and the companion JSON summary from canonical SV2.0.2 pack references plus persisted candle truth, including founder-review labels such as `promising_control_pocket_risk` and `promising_high_pnl_control_risk` that are separate from strict candidate promotion. It does not alter Money Flow rules or create order/execution artifacts.
- Includes `scripts/build_mf_orig_ev1_original_money_flow.py` for MF-ORIG-EV1.1 original Money Flow reconstruction regeneration. It writes the source-specification/gap-matrix report, founder-readable reconstruction report, and compact JSON summary from canonical SV2.0.2 pack references plus persisted candle truth. The regenerated outputs use event-ledger accounting and peak-to-trough drawdown. It is evidence-only and does not alter production Money Flow rules, call exchanges, submit orders, or approve paper/live behavior.
- Includes `scripts/build_pt_rt1_summary.py` for PT-RT1 committed dashboard/config summary generation. It writes configuration-only JSON and performs no market-data fetches, exchange calls, credential reads, order submissions, or runtime-state writes.
- Includes `scripts/build_pt_rt1_1_dry_run_report.py` for PT-RT1.1 dry-run validation reporting. It reads the ignored `reports/paper_runtime/pt_rt1_1_24h_dry_run/` artifact directory when present and writes committed report/summary docs; if the 24-hour artifacts are absent or incomplete, it marks PT-RT1.2 blocked instead of fabricating runtime success.
- Includes `scripts/build_pt_rt_week1_day_summary.py` for PT-RT1.4.1 daily founder review reporting. It reads ignored PT-RT runtime artifacts, labels pre-cutover burn-in separately from active-week runtime truth, and writes compact Markdown/JSON under `docs/` without calling exchanges, mutating runtime state, regenerating evidence packs, approving strategies, or submitting orders.
- Includes `scripts/run_pt_rt1_paper_observation.py` for PT-RT1.1B public-mainnet paper-observation runtime readiness and PT-RT1.1C collection. It writes ignored runtime artifacts only under `reports/paper_runtime/`, uses no API keys for strategy truth, calls no private/signed/order endpoints from strategy truth, labels PT-RT1.1C output directories as runtime collection cycles, supports bounded smoke or 24-hour collection runs, defaults PT-RT1.4 fresh runtime cycles to active `1h`/`4h`/`1d`, and blocks explicit `15m` evaluation with no-new-entry reason codes. PT-RT1.5 adds `--pt-rt1-5-week1-active`, candle-close-only signal scheduling, `reports/paper_runtime/pt_rt1_5_week1_active/`, and baseline-only fixed 25 USDC testnet lifecycle rows in `testnet_order_lifecycle.jsonl`. PT-RT1.5.1 adds `--fresh-signal-only-after-runtime-start`, `--enable-baseline-testnet-transport`, `--founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc`, `reports/paper_runtime/pt_rt1_5_1_smoke/`, warm-start signal blocking, signed transport client configuration from local sandbox env, and open-position MTM updates. PT-RT1.5.2 adds `--founder-approved-pt-rt1-5-2-testnet-transport-smoke`, `--founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc`, `--max-testnet-orders-this-phase`, scoped `.env` loading without secret printing, explicit transport-smoke context loading from public mainnet candles, and `reports/paper_runtime/pt_rt1_5_2_*` scopes. PT-RT1.5.3 adds `--founder-approved-pt-rt1-5-3-testnet-size-hotfix-smoke`, `reports/paper_runtime/pt_rt1_5_3_transport_smoke/`, Hyperliquid testnet public metadata lookup for sizing, and invalid-size local/venue reason coding; candidate lanes remain synthetic-only and testnet fills never update paper PnL.
- Includes `scripts/run_uat1_public_read_only.py` for UAT1 public-read-only connectivity and top-20 universe resolution. It requires both `--uat1-public-read-only` and `--allow-public-read-only-network` before network calls, uses no API keys, calls only allowlisted public read-only endpoints/source URLs, writes the UAT1 Markdown/JSON reports, and creates no strategy decisions, order intents, submitted orders, paper/live artifacts, routing artifacts, evidence packs, or Money Flow rule changes.
- Includes `scripts/run_uat31_first_sandbox_order.py` for the one approved UAT3.1 Hyperliquid testnet lifecycle probe. It refuses to run without `--execute-approved-uat31`, validates exact founder/operator approval before credential use, reads sandbox/testnet credentials only from local environment or `.env`, writes sanitized UAT3.1 Markdown/JSON reports, and prevents repeat execution after a summary records an order attempt.
- Includes `scripts/run_uat32_second_sandbox_order.py` for the separately approved UAT3.2 fixed-key preflight / second sandbox lifecycle attempt. It refuses to run without `--execute-approved-uat32`, validates exact UAT3.2 founder/operator approval before credential use, reads sandbox/testnet credentials only from local environment or `.env`, writes sanitized UAT3.2 Markdown/JSON reports, captures the UAT4.0 dashboard roadmap request, and blocks before order transport when account/API-wallet readiness fails.

## Operational Entrypoints

- API app: `apps.api.app.main:app`
- Alembic: `alembic upgrade head`
- Test suite: `.venv/bin/pytest -q`
- Review bundle: `.venv/bin/python scripts/create_review_bundle.py --output /tmp/money-flow-review.zip`
- Manual routed-flow inspection: `.venv/bin/python scripts/manual_routed_flow.py --desired-trade-key <desired_trade_key> --run-through-readiness`
- Money Flow strategy validation: `.venv/bin/python scripts/run_money_flow_backtest.py --venue <venue> --symbol <symbol> --component sleeve_15m --start <iso> --end <iso> --initial-capital <amount> --fee-bps <bps> --slippage-bps <bps> --fill-timing next_candle_open`
- Money Flow comparative validation batch: `.venv/bin/python scripts/run_money_flow_validation_batch.py --venue <venue> --symbol <symbol> --component sleeve_15m --component sleeve_1h --fill-timing same_candle_close_research_only --fill-timing next_candle_open --start <iso> --end <iso> --initial-capital <amount> --fee-bps <bps> --slippage-bps <bps> --format markdown`; validation windows use candle closes in `(start, end]`.
- Money Flow research campaign evidence pack: `.venv/bin/python scripts/run_money_flow_research_campaign.py --config configs/strategy_validation/money_flow_research_campaign.example.json --format both`; campaign windows use candle closes in `(start, end]`, generated packs are written under `reports/strategy_validation/` by default, and the default `unique_suffix` collision policy prevents silent overwrite on duplicate run ids.
- Money Flow campaign data-readiness audit: `.venv/bin/python scripts/run_money_flow_research_campaign.py --config configs/strategy_validation/campaigns/money_flow_core_btc.json --audit-only --audit-format markdown`; audit output is read-only JSON or Markdown over persisted candle coverage and creates no evidence pack or live artifacts.
- Money Flow historical candle import: `.venv/bin/python scripts/import_strategy_validation_candles.py --input /path/to/candles.csv --environment testnet --venue hyperliquid --timeframe 15m --source-label public_dataset`; imports are duplicate-safe candle upserts only, require timezone-explicit timestamps by default, can use non-default `--assume-naive-utc` only with provenance-marked exploratory/non-canonical intent, and do not create strategy, routing, approval, or execution artifacts.
- Strategy Validation market identity seed/verify: `.venv/bin/python scripts/seed_strategy_validation_market_identity.py --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json --dry-run`; seed writes only canonical research `instruments` / `symbols` rows when not dry-run and does not create candles or live artifacts.
- Strategy Validation candle import preflight: `.venv/bin/python scripts/preflight_strategy_validation_candle_import.py --input /path/to/candles.csv --environment testnet --venue hyperliquid --timeframe 15m`; preflight writes no candles and validates file/mapping readiness before the importer is run.
- Strategy Validation guarded candle bundle import: `.venv/bin/python scripts/import_strategy_validation_candle_bundle.py --requirements-from-review-json /path/to/review.json --input /path/to/btc_15m.csv --input-requirement-map /path/to/input_requirement_map.json --environment testnet --venue hyperliquid --format both`; guarded import writes candles only after intended DB/schema, operator-verified non-trading identity, complete one-to-one requirement-aware preflight, and hardened importer gates pass. It reports explicit partial-persistence truth if a later file fails and does not generate evidence packs or live artifacts.
- Strategy Validation guarded import attempt: `.venv/bin/python scripts/run_strategy_validation_guarded_import_attempt.py --manifest configs/strategy_validation/market_identity/hyperliquid_perp_usdc.example.json --input-dir /path/to/canonical-candle-files --environment testnet --venue hyperliquid --format markdown`; identity seed is skipped unless explicit operator verification, `verified_by`, and offline value confirmation flags are supplied, import runs only when all 18 canonical files are present and preflight-ready, and no evidence packs are generated.
- Money Flow canonical evidence review: `.venv/bin/python scripts/review_money_flow_evidence_packs.py --format markdown`; add `--db-status-only` for DB target/schema/candle readiness checks, and add `--generate-evidence-packs` to generate collision-safe packs only for campaigns whose DB target is clearly intended/non-maintenance, whose DB schema reports `migrated_schema_ready`, and whose data-readiness audit has no missing, thin, or blocked rows. The review reports sanitized DB driver/host/port/name/user, intended strategy-validation DB truth, reachability/schema/migration/candle-table status, canonical candle import requirements, can report `partial_evidence_ready_with_data_gaps`, and remains manual/descriptive only; it does not approve paper trading.
- Money Flow trade-anatomy diagnostics: `.venv/bin/python scripts/run_money_flow_trade_anatomy_diagnostics.py --output docs/strategy_validation_sv1_14_trade_anatomy_and_market_structure.md`; diagnostics read existing evidence packs and optional DB candles, explain current rule logic, and report descriptive market-structure context only.
- Money Flow hypothesis experiments: `.venv/bin/python scripts/run_money_flow_hypothesis_experiments.py --output docs/strategy_validation_sv1_15_hypothesis_experiments.md`; experiments read existing dynamic-equity evidence packs and optional DB candles, compare research-only overlays against baseline, and do not change production Money Flow rules.
- Money Flow true replay instrumentation: `.venv/bin/python scripts/run_money_flow_true_replay.py --output docs/strategy_validation_sv1_16_rejected_signal_replay.md --symbol ETH --component sleeve_1h`; replay captures per-candle baseline/rejected context and runs research-only variants without changing production Money Flow rules.
- Money Flow true replay experiments: `.venv/bin/python scripts/run_money_flow_true_replay_experiments.py --output docs/strategy_validation_sv1_17_true_replay_experiments.md --symbol ETH --component sleeve_1h`; experiments compare lower-RSI plus market-structure replay variants against baseline and remain research-only.
- UAT1 public read-only connectivity: `.venv/bin/python scripts/run_uat1_public_read_only.py --uat1-public-read-only --allow-public-read-only-network --runtime-mode uat`; this is public read-only only, uses no API keys, and must not call private/signed/order endpoints or run Money Flow live.
- UAT1.1 shadow readiness is model/report-only through `services.uat.shadow`; it defines future UAT2 audit/drawdown surfaces and creates no strategy/execution artifacts or exchange calls.
- UAT2 no-order shadow run: `.venv/bin/python scripts/run_uat2_shadow_strategy.py --uat2-shadow-run --shadow-only --public-read-only --allow-public-read-only-network --runtime-mode uat`; this uses the UAT1 snapshot and public Hyperliquid candle snapshots only, emits shadow audit/report artifacts, and must not call private/signed/order endpoints, use API keys, submit orders, create production strategy/execution artifacts, approve paper/live trading, or change Money Flow rules.
- UAT3.1 first sandbox/testnet lifecycle probe: `.venv/bin/python scripts/run_uat31_first_sandbox_order.py --execute-approved-uat31`; this is one founder-approved Hyperliquid testnet ETH post-only/nonmarketable lifecycle probe only, creates no production execution artifacts, and must not be reused for repeated orders, paper/live trading, broad top-20 submission, routing expansion, or Money Flow performance validation.
- UAT3.2 fixed-key preflight / second sandbox lifecycle attempt: `.venv/bin/python scripts/run_uat32_second_sandbox_order.py --execute-approved-uat32`; this is one separately founder-approved Hyperliquid testnet ETH lifecycle attempt only. The recorded run blocked before order transport because account/API-wallet readiness failed, so `order_attempt_count` is `0`.
- UAT3.4 fixed-target sandbox routing ledger run: `.venv/bin/python scripts/run_uat34_sandbox_routing_pipeline.py --execute-approved-uat34 --attempts 1`; this is approved Hyperliquid testnet ETH fixed-target sandbox routing only, writes routed ledger reports, and is not smart routing, SOR, fanout, broad top-20 submission, paper/live trading, or strategy performance validation.
- Routing automation policy/plan/approval inspection and the narrow Phase 7.2 / 7.3 / 7.4 / 7.5 action hooks: `GET /api/v1/routing-automation/policy`, `POST /api/v1/routing-automation/plans/by-desired-trade/{desired_trade_key}`, `POST /api/v1/routing-automation/approvals`, `GET /api/v1/routing-automation/approvals/{approval_id}`, `GET /api/v1/routing-automation/approvals/by-desired-trade/{desired_trade_key}`, `POST /api/v1/routing-automation/approvals/{approval_id}/revoke`, administrative `POST /api/v1/routing-automation/approvals/{approval_id}/consume`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/accept-recommendation`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/convert-target-choice`, action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/preview-readiness`, and action-executing `POST /api/v1/routing-automation/approvals/{approval_id}/submit`
- Phase 8.0 operator routed workflow summary: `GET /api/v1/operator-routed-workflows/by-desired-trade/{desired_trade_key}`

## Main Test Surfaces

`tests/test_config.py`
- settings defaults and hermetic env/bootstrap behavior

`tests/test_api.py`
- API startup and control-plane endpoints, including adapter/runtime session-state and private order/account-state inspection surfaces

`tests/test_phase2_services.py`
- exchange/data/state and portfolio bootstrap semantics

`tests/test_phase3_strategy.py`
- indicators, strategy evaluation, idempotency, stale-indicator rejection, and Money Flow decision paths

`tests/test_sv10_strategy_validation.py`
- SV1.0/SV1.0.1 Money Flow strategy-validation framework: verifies deterministic backtest reports over persisted candles, simulated trade generation, explicit fill-timing behavior, mark-to-market drawdown truth, expanded Markdown sections/limitations, fee/slippage impact on net PnL, no-trade reason surfacing, component/timeframe report truth, CLI request assumptions, and no live desired-trade / child-intent / readiness / submitted-order / persisted signal or decision artifacts.

`tests/test_sv11_strategy_validation_batch.py`
- SV1.1 comparative Money Flow validation: verifies batch reports across components and fill timings, deterministic JSON output, founder-readable comparison Markdown tables, per-run missing-candle limitations, no optimization/recommendation language, and no live desired-trade / routing / approval / child-intent / readiness / submitted-order / persisted signal or decision artifacts.

`tests/test_sv12_strategy_validation_regimes.py`
- SV1.2/SV1.2.1 data-coverage, market-regime, and window-truth validation: verifies complete/thin coverage diagnostics, deterministic uptrend/downtrend/sideways/unknown labels, regime-grouped trade metrics, Markdown regime/data sections, repeated CLI windows, `(start, end]` adjacent-window boundary truth, unaligned-window coverage warnings, blocked-run grouped comparison visibility, no optimization/recommendation language, and no live artifacts.

`tests/test_sv13_research_campaigns.py`
- SV1.3 research campaign/evidence-pack validation: verifies campaign config parsing, named windows to batch requests, single-run CLI `(start, end]` help wording, evidence-pack file creation, manifest metadata, window-convention visibility, adjacent-window no-double-counting, blocked-run visibility, campaign CLI help, no optimization/recommendation wording, and no live artifacts.

`tests/test_sv14_evidence_readiness.py`
- SV1.4 evidence readiness validation: verifies executable canonical campaign configs parse, the SV1.12.4 Hyperliquid and SV1.12.5 supported-venue public YTD/recent data-plan configs are research-only, data-readiness audit reports covered/thin/missing windows and manual-only flags, evidence packs include review checklist plus manual paper-trading readiness criteria, audit-only CLI help is truthful, and no live artifacts are created.
- SV1.4.1 evidence-pack integrity validation: verifies duplicate same-timestamp campaign runs do not overwrite the first pack, `unique_suffix` manifests record final run identity/collision truth, `fail_if_exists` raises explicitly without mutating the original pack, generated evidence packs remain excluded from review bundles, and no live artifacts are created.

`tests/test_sv15_historical_data_readiness.py`
- SV1.5 historical-data readiness validation: verifies campaign `window_convention` mismatch handling, canonical campaign audit summaries for missing/thin data, founder-readable audit Markdown, duplicate-safe offline candle import/upsert behavior, first canonical evidence-pack generation path with collision safety, research-only CLI help, and no live artifacts.

`tests/test_sv151_candle_import_integrity.py`
- SV1.5.1 candle import and campaign-config research-truth validation: verifies strict window-convention contradiction rejection, candle identity-conflict blocking without retargeting or duplicate insert, same-identity duplicate-safe upsert behavior, timeframe-duration mismatch rejection, malformed/non-finite/invalid OHLCV and trade-count rejection, all-or-nothing rollback for invalid import files, and no live artifacts.

`tests/test_sv16_evidence_review.py`
- SV1.6 first canonical evidence-review validation: verifies canonical campaign audits report insufficient data without generated packs, seeded sufficient campaigns produce evidence-pack paths in review summaries, collision-safe duplicate runs still suffix instead of overwriting, review Markdown uses manual/descriptive status language, the review CLI is research-only, audit-only review creates no packs, and no live artifacts are created.

`tests/test_sv17_evidence_review_real_data_gaps.py`
- SV1.7 first-real canonical evidence-review/data-gap validation: verifies unreachable database status is surfaced as blocked canonical campaign rows, reachable databases without `candles` are reported as schema/data gaps, mixed generated/blocked outcomes use `partial_evidence_ready_with_data_gaps`, generated packs remain collision-safe where seeded data is sufficient, no recommendation/optimization wording appears, and no live artifacts are created.

`tests/test_sv18_historical_data_bootstrap.py`
- SV1.8 historical-data bootstrap validation: verifies DB/schema/migration status reporting, status-only evidence-review output, missing Alembic/candle-table gaps, seeded sufficient evidence generation behind schema checks, no recommendation/optimization wording, and no live artifacts.

`tests/test_sv181_evidence_schema_truth.py`
- SV1.8.1 evidence schema-truth validation: verifies evidence-pack generation is blocked without current Alembic truth or required `candles` / `instruments` / `symbols` tables, partial schema gaps report cleanly, top-level live/exchange flags aggregate from campaign results, and no live artifacts are created.

`tests/test_sv19_evidence_status.py`
- SV1.9 first-real evidence status validation: verifies DB target metadata reports sanitized host/port/name/user and intended-database truth, outdated migration revisions block evidence generation, canonical missing-candle rows emit import requirements, seeded sufficient data can still generate evidence packs with current schema truth, top-level live/exchange flags remain aggregated, and no live artifacts are created.

`tests/test_sv191_evidence_target_and_import_truth.py`
- SV1.9.1 evidence-target and candle-import truth validation: verifies migrated/current maintenance DB targets still block evidence generation by default, blocked results expose DB-target reason codes and write no pack, timezone-naive imports fail by default without persisted candles, explicit `--assume-naive-utc` service override succeeds only with provenance/timestamp-assumption warnings, and no live artifacts are created.

`tests/test_sv110_evidence_db_readiness.py`
- SV1.10 intended DB/candle readiness validation: verifies intended DB target reporting, required table inspection, unique canonical import-requirement grouping, timezone-explicit import requirement guidance, insufficient/seeded canonical audit paths, artifact hygiene, and no live artifacts.

`tests/test_sv111_market_identity_preflight.py`
- SV1.11 market-identity and preflight validation: verifies offline manifest parsing, dry-run/verify-only/seed behavior for canonical BTC/ETH/SOL identity rows, conflict and Decimal guards, evidence-review identity readiness, row-level candle preflight, and no candle/evidence/live artifacts.

`tests/test_sv1111_market_identity_preflight_hardening.py`
- SV1.11.1 hardening validation: verifies unverified non-dry-run identity writes block, dry-run/verify-only still work without verification, operator-verified writes record metadata without flipping eligibility, requirement-aware preflight detects wrong windows/duplicates/missing slots/wrong identity, complete synthetic requirements pass, and no candle/evidence/live artifacts are created.

`tests/test_sv1112_market_identity_preflight_governance.py`
- SV1.11.2 governance validation: verifies the research market-identity seed rejects strategy/trading eligibility promotion without writes, successful seed remains research-only/non-trading, dry-run reports invalid eligibility truth, verify-only stays non-writing, requirement-aware preflight blocks unmapped inputs/unmapped requirements/duplicate mappings, complete one-to-one mappings can pass, review JSON selection prefers candle import requirements, and no candle/evidence/live artifacts are created.

`tests/test_sv112_guarded_candle_import.py`
- SV1.12/SV1.12.1 guarded canonical candle import validation: verifies maintenance/ambiguous DB targets block import, operator-verified non-trading identity is required, timezone-naive files block, complete one-to-one requirement mapping and exact requirement coverage are required, preflight-passed synthetic files can import through the hardened importer, late file failures are reported as explicit partial persistence with imported/failed requirement IDs, unmapped input files and missing requirements appear in operator output, and no evidence/live/exchange/routing artifacts are created.
- SV1.12.2 readiness validation: verifies missing operator verification produces a checklist without seed writes, explicit verified seed writes remain non-trading/non-strategy-eligible, the exact 18 canonical file requirements include `(start_at, end_at]` and timezone requirements, preflight-only synthetic checks write no candles, and no evidence/live/exchange artifacts are created.

`tests/test_sv1123_guarded_import_attempt.py`
- SV1.12.3 guarded import attempt validation: verifies missing operator verification prevents identity seed, verified synthetic identity remains non-trading, missing files and incomplete mappings block import, failed requirement-aware preflight blocks import, a complete synthetic 18-file bundle can import through the guarded path, and no evidence/live/exchange/routing artifacts are created.
- SV1.12.4 public-data readiness validation: verifies public campaign JSON parses, public candleSnapshot outputs are transformed into timezone-explicit local CSVs outside the repo, requirement-aware preflight blocks on missing operator-verified DB identity instead of importing, and no evidence/live/exchange/routing artifacts are created.

`tests/test_phase34_mandates.py`
- mandate hierarchy bootstrap, multi-binding scoping, reusable accounts across mandates, and differing component configs

`tests/test_phase35_cleanup.py`
- deployment-era cleanup validation and repo hygiene ignores

`tests/test_phase4a_venues.py`
- multi-venue adapter wiring, capability matrices, catalog normalization, and venue maturity surfaces

`tests/test_phase401_trade_planning.py`
- desired-trade drafting, source-policy, convertibility, routing-candidates, and quote normalization

`tests/test_phase41_risk.py`
- desired-trade approval/rejection and selective child-intent preparation

`tests/test_phase411_venue_preparation.py`
- support levels, venue-native prepared-order previews, and preflight rejection reasons

`tests/test_phase42_execution_readiness.py`
- readiness outcomes above prepared child intents

`tests/test_phase43_submission.py`
- explicit submit flow and submitted-order persistence

`tests/test_phase431_submission_truth.py`
- signed/transmitted submit-body fidelity, auth/signing truth, and same-venue multi-account targeting

`tests/test_phase44_submission_lifecycle.py`
- submitted-order lifecycle truth, Hyperliquid partial-fill/open-order coexistence, and rejection propagation

`tests/test_phase45_execution_lifecycle.py`
- broader venue reconciliation, recovery recommendations, truthful cancel lifecycle, same-target retry/cancel/amend/reconcile behavior, strict client-order-id retry truth for Aster/Binance, direct live open-order retry blocking, submitted-at-bounded ambiguity-scoped Aster/Binance private fill retry blocking without plain submitted-order fill leakage, Binance fill-query-failure retry blocking, Hyperliquid nullable/derived mark-price truth, polling-first private-state truth, venue-private open-order boundary truth, runtime source truth, and same-venue multi-account targeting through private open-order/recent-fill reads

`tests/test_phase50_routing_substrate.py`
- Phase 5.0 non-executing routing assessment substrate: routing-required mandate-scoped opens produce persisted assessments, bindings are enumerated without creating target-choice records during assessment, missing-data/no-eligible cases are explicit, same-venue multi-account candidate inventory remains intact, no child intents or submitted orders are created, and public routing surfaces avoid live-routing/optimization wording.

`tests/test_phase51_routing_target_choice.py`
- Phase 5.1 non-executing routing target-choice substrate: operators can request one explicit eligible binding from a valid routing assessment, assessment/candidate id semantics stay correct, no auto-pick occurs, stale desired-trade truth plus ineligible or stale binding/account truth blocks target choice, desired trades are not mutated by target choice, and no child intents or submitted orders are created.

`tests/test_phase52_target_choice_conversion.py`
- Phase 5.2 target-choice conversion substrate plus Phase 5.2.1 lineage hardening: one explicit recorded target choice can create exactly one binding/account-targeted child intent with routing assessment / target-choice lineage, idempotent duplicate handling, stale desired-trade/binding/account/candidate mismatch blocking, assessment id/environment mismatch blocking, desired-trade ownership drift blocking, binding mandate ownership blocking, symbol-mapping drift blocking, same-venue multi-account targeting, and no prepared orders, readiness evaluations, submitted orders, fanout, scoring, CBBO, or submission.

`tests/test_phase53_routed_child_intent_readiness.py`
- Phase 5.3 routed child-intent preparation/readiness handoff plus Phase 5.3.1 hardening: converted routed child intents can use existing preview/readiness paths after route-lineage validation; stale desired-trade/binding/account/route-lineage drift, selected-target provenance drift, child-intent client/mandate drift, target-choice desired-trade drift, and routed submit attempts with the routed gate disabled block before adapter submission; same-venue multi-account routed readiness uses only the selected account; and no extra child intents, fanout, scoring, CBBO, target reselection, or auto-submit are created.

`tests/test_phase54_routed_submission_handoff.py`
- Phase 5.4 explicit routed submission handoff plus Phase 5.4.1 truth hotpatch: routed submission remains phase-blocked while either the separate routed gate or normal live gate blocks submission, phase-boundary submit attempts preserve child-intent status and record `last_submission_block`, routed preview payloads report actual routed/live gate deferral truth, enabled routed submission creates exactly one SubmittedOrder for the already selected binding/account after lineage/readiness validation, routed lineage is preserved in submitted-order raw payload, stale lineage/binding/account/symbol truth blocks before adapter submit, same-venue multi-account routed submission uses only the selected account, and API behavior stays explicit without auto-submit, fanout, CBBO, scoring, target reselection, or route executor behavior.

`tests/test_phase55_routed_submitted_order_lineage.py`
- Phase 5.5 routed submitted-order lineage inspection plus Phase 5.6 malformed-type hardening: routed submitted-order detail/list responses expose derived routed-origin lineage without raw-payload parsing, non-routed submitted orders do not fabricate routing ids, malformed routed payloads are bounded with missing-lineage and malformed-lineage facts, same-target actionability remains selected-account scoped, and inspection creates no extra child intents or submitted orders.

`tests/test_phase56_routed_order_shape_policy.py`
- Phase 5.6 / Phase 5.8 / Phase 5.8.1 / Phase 5.8.2 routed order-shape policy: target-choice conversion uses explicit policy-backed MARKET / no-limit / reduce_only=false default shape, accepts explicit MARKET/LIMIT policy input, blocks invalid or non-finite LIMIT / unsupported order types / reduce_only=true before child-intent creation, keeps malformed/non-finite LIMIT blocks from reporting `limit_price_explicit`, preserves idempotency, prevents policy mismatch from creating a second child intent, and keeps slippage / market-data-derived price guard expansion deferred.

`tests/test_phase57_routed_post_submit_lifecycle.py`
- Phase 5.7 routed post-submit lifecycle/actionability inspection plus Phase 5.7.1 hotpatch coverage: routed submitted-order detail/list/recovery/actionability responses expose read-only lifecycle context, routed same-target retry preserves routed lineage, non-routed retry/orders do not fabricate routed context, malformed routed payloads remain bounded through the shared parser, same-venue multi-account actionability uses only the selected account, and inspection creates no extra child intents or submitted orders.

`tests/test_phase59_routed_reconciliation_lifecycle_audit.py`
- Phase 5.9 routed reconciliation/lifecycle audit visibility plus Phase 5.9.1/5.9.2 namespace hotpatch coverage: routed reconciliation responses preserve and expose selected route context, existing platform `routed_submission` lineage wins over colliding update payloads, non-routed update-payload collisions cannot create platform routed lineage, lifecycle-event responses derive routed context through the shared parser, non-routed reconciliation/events do not fabricate route context, malformed routed payloads stay bounded, same-venue multi-account reconciliation context remains selected-account scoped, and audit inspection creates no extra child intents, readiness evaluations, submitted orders, fanout, scoring, allocation, target reselection, or route plans.

`tests/test_phase510_routing_substrate_closeout.py`
- Phase 5.10 final routing-substrate closeout regression: exercises the accepted routed chain from routing-required desired trade through assessment, explicit target choice, exactly-one conversion, routed preview/readiness, explicit gated routed submission, submitted-order detail/list, actionability/recovery, reconciliation with a colliding update-payload `routed_submission`, and lifecycle-event context. Verifies typed routed lineage consistency, selected-account same-venue targeting, platform-owned routed_submission namespace truth, and absence of fanout, allocation, scoring, CBBO, target reselection, route plan, route executor behavior, auto-submit, extra child intents, or extra submitted orders.

`tests/test_phase5101_route_readiness_audit.py`
- Phase 5.10.1 / 5.10.2 non-selecting route-readiness/data-sufficiency audit: verifies audits can be created from routing-required desired trades and existing routing assessments, persisted and fetched by id, reason-code missing/stale market data, inactive binding/account and symbol-mapping blockers, unsupported order-shape facts, economic fee/balance/private-state visibility, same-venue multi-account account-scoped facts, API inspection, quote source labels derived from existing assessment snapshots rather than fresh venue-query overclaims, desired-trade side/quantity blockers, malformed/non-finite/non-positive quote-price safety, defaulted MARKET order-shape wording, and no target choice, child intent, readiness evaluation, submitted order, fanout, scoring, CBBO, route plan, target reselection, route executor behavior, or auto-submit.

`tests/test_phase600_routing_target_recommendation.py`
- Phase 6.0.0 / 6.0.1 / 6.0.2 / 6.1 / 6.1.1 controlled non-executing target recommendation: verifies persisted recommendations can be created from route-readiness audits, default `single_ready_candidate_only` behavior remains backward-compatible, multiple ready candidates still block by default, explicit `explicit_binding_priority` can recommend exactly one lower-priority ready binding, missing priority blocks, priority ties block, malformed priority blocks, current-truth revalidation still blocks after priority selection, priority-selected stale quotes block, invalid API policy names return validation errors without persistence, malformed direct service policy names are rejected before persistence, priority clear/preserve semantics are explicit, unknown short direct-service policy attempts persist a controlled blocked record, quote observation freshness remains enforced, source audits report recommendation-created truth after a recommendation record is persisted, API create/get inspection works, and no target choice, child intent, readiness evaluation, submitted order, fanout, CBBO, rank, score, allocation, route plan, target reselection, route executor behavior, or auto-submit is created during recommendation creation.

`tests/test_phase62_recommendation_acceptance.py`
- Phase 6.2 / 6.2.1 / 6.2.2 explicit recommendation acceptance: verifies successful `single_ready_candidate_only` and `explicit_binding_priority` recommendations can be accepted into exactly one non-executing target choice, blocked or unknown recommendations cannot be accepted, blocked recommendations from an already accepted audit cannot reuse same-audit idempotency or be stamped as accepted, disabled binding and stale quote facts block new acceptance, repeated acceptance returns the existing target choice, duplicate successful recommendations from one route-readiness audit cannot create multiple target choices, original recommendation/audit acceptance timestamps remain stable after idempotent retries, recommendation/source-audit `target_choice_created` truth updates only after valid acceptance, target-choice provenance carries recommendation/audit/policy/selected-target lineage, API acceptance returns target-choice inspection, and no child intent, readiness evaluation, submitted order, fanout, CBBO, rank, score, allocation, route plan, target reselection, route executor behavior, or auto-submit is created.

`tests/test_phase63_recommendation_target_choice_conversion.py`
- Phase 6.3 explicit accepted-recommendation target-choice conversion: verifies accepted recommendation-backed target choices convert into exactly one routed child `OrderIntent`, conversion response and child-intent provenance expose recommendation/audit/target-choice/selected-target/order-shape lineage, repeated conversion returns the existing child intent, duplicate same-audit target-choice paths cannot create multiple child intents, blocked recommendation-backed target choices cannot be laundered into conversion, disabled binding/account, inactive/non-trading symbol mapping, and stale quote facts block new conversion, explicit positive finite LIMIT policy succeeds, invalid LIMIT policy blocks before child-intent creation, `explicit_binding_priority` recommendations can convert after acceptance, API conversion exposes recommendation lineage, and no prepared order, readiness assessment, submitted order, fanout, CBBO, rank, score, route plan, target reselection, route executor behavior, or auto-submit is created.

`tests/test_phase64_recommendation_backed_readiness.py`
- Phase 6.4 / 6.4.1 recommendation-backed child-intent preview/readiness inspection: verifies accepted recommendation-backed child intents use existing prepared-order preview and submission-readiness paths, preview/readiness API responses expose recommendation/audit/target-choice/selected-target/order-shape lineage, disabled binding/account and inactive/non-trading symbol truth block before adapter preparation, stale stored quote observations block readiness with `quote_stale_at_readiness`, stored routed order-shape policy drift for order_type / LIMIT price / reduce_only blocks before adapter preparation, missing policy blocks, explicit positive finite LIMIT policy remains visible through readiness, and no submitted order, exchange submit call, route executor behavior, fanout, allocation, ranking/scoring, CBBO, target reselection, or auto-submit is created.

`tests/test_phase65_manual_routed_flow.py`
- Phase 6.5 / 6.6 manual routed-flow harness coverage: verifies the internal JSON harness can run from an existing routing-required desired trade through readiness inspection using existing services, output key artifact ids/statuses/reason codes/routed lineage, include local top-level `timing_ms` and per-step `elapsed_ms` for executed steps, omit skipped-step timing rather than fabricating zero work, skip submission by default, create no `SubmittedOrder` by default, and block `--submit` without the danger-confirmation flag before service submission while recording local submission-block timing.

`tests/test_phase67_recommendation_backed_submission.py`
- Phase 6.7 / 6.10.1 / 6.10.2 / 6.10.3 explicit recommendation-backed submitted-order handoff: verifies a recommendation-backed child intent submits only through the existing explicit gated submit path when live and routed gates pass, serializes concurrent explicit submit attempts with the submission lease before adapter submission, writes terminal `adapter_submit_may_have_started` before adapter submission can begin, preserves post-adapter/pre-persistence uncertainty as terminal `adapter_submit_persistence_unknown`, blocks later submits for that intent before adapter submission even after TTL, keeps stale pre-adapter active leases replaceable, blocks before adapter submit when gates, quote truth, recommendation lineage, or routed order-shape policy drift fail, creates exactly one SubmittedOrder, exposes recommendation/audit/target-choice/intent/readiness lineage, preserves first submitted-order provenance across same-target retry, and still adds no fanout, allocation, scoring, CBBO, target reselection, route executor behavior, or auto-submit.

`tests/test_phase68_recommendation_backed_lifecycle.py`
- Phase 6.8 recommendation-backed post-submit lifecycle inspection: verifies submitted-order detail/list/actionability/recovery/reconciliation/lifecycle-event surfaces expose recommendation-aware routed lifecycle context, reconciliation cannot overwrite platform-owned recommendation lineage, non-routed orders cannot fabricate recommendation lineage from update payload collisions, and same-target retry preserves recommendation/audit/target-choice lineage without alternate binding or venue recovery.

`tests/test_phase69_routed_workflow_inspection.py`
- Phase 6.9 / 6.10.1 read-only routed workflow inspection API: verifies `GET /api/v1/routed-workflows/by-desired-trade/{desired_trade_key}` aggregates full and partial routed chains without creating artifacts, distinguishes unknown desired trades cleanly, exposes consistent routed lineage, artifact counts, and a truthful `same_target_lifecycle_summary`, and never submits or advances workflow state.

`tests/test_phase70_routing_automation.py`
- Phase 7.0 controlled automation substrate: verifies default disabled policy, dry-run-only plans, approval-required plans, explicit same-target automation eligibility, blocked-recommendation behavior, API policy/plan surfaces, lineage preservation, no dry-run mutation, and absence of smart routing, fanout, ranking/scoring, CBBO, target reselection, route executor behavior, or auto-submit.

`tests/test_phase71_routing_automation_approvals.py`
- Phase 7.1 / 7.1.1 / 7.1.2 operator approval and reversible gating substrate: verifies approval creation, routed lineage and policy snapshot preservation, approval inspection by desired trade, expiry replacement, stale-lineage replacement, active-scope idempotency/uniqueness, rejection of dry-run-only and manual-only approvals, gate-state truth for non-approvable current steps, revocation, consumed approvals not being reusable, blocked recommendations not receiving approval, API create/inspect/revoke surfaces, continued dry-run non-execution, and no target choice, child intent, readiness, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects.

`tests/test_phase72_approval_gated_recommendation_acceptance.py`
- Phase 7.2 / 7.2.1 approval-gated recommendation acceptance action hook: verifies a valid current recommendation-acceptance approval can create/reuse exactly one target choice and be consumed, repeated calls are idempotent, a forced failure between target-choice flush and approval consumption rolls back without misleading state, generic approval consumption is administrative only, expired/revoked/wrong-action/wrong-recommendation/consumed-for-different-recommendation approvals block, dry-run-only/manual-only policies cannot execute, API response exposes consumed approval plus target choice, and no child intent, readiness evaluation, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase73_approval_gated_target_choice_conversion.py`
- Phase 7.3 approval-gated target-choice conversion action hook plus Phase 7.3.1 negative-test hardening: verifies a valid current target-choice-conversion approval can create/reuse exactly one child intent and be consumed, repeated calls are idempotent, a forced failure between child-intent flush and approval consumption rolls back without misleading state, expired/revoked/wrong-action/wrong-target-choice/stale-lineage/consumed-for-different-target-choice approvals block, dry-run-only/manual-only policies cannot execute, disabled/blocked/deferred/already-satisfied current step states reject conversion directly, wrong recommendation / route-readiness audit / desired-trade lineage rejects without consuming approval, API response exposes consumed approval plus child intent, Obsidian workflow requirements are operational-test-covered, and no prepared order, readiness evaluation, submitted order, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase74_approval_gated_preview_readiness.py`
- Phase 7.4 approval-gated preview/readiness action hook: verifies a valid current `prepared_order_preview_and_readiness` approval can run existing child-intent preview/readiness, persist or reuse exactly one readiness assessment, and be consumed; repeated calls are idempotent; forced approval-consumption failure rolls back readiness persistence; expired/revoked/wrong-action/stale-lineage/consumed-for-different-child approvals block; disabled/blocked/deferred/already-satisfied/dry-run-only/manual-only step states reject action; blocked readiness remains reason-coded; API response exposes consumed approval plus preview/readiness; and no submitted order, adapter submit call, route executor, fanout, ranking/scoring, CBBO, target reselection, or auto-submit side effects occur.

`tests/test_phase75_approval_gated_submission_handoff.py`
- Phase 7.5 / 7.5.1 approval-gated submitted-order handoff action hook: verifies a valid current `submitted_order_handoff` approval submits exactly one already-ready routed child intent through the existing explicit submit path, consumes approval only after submitted-order persistence or safe reuse, preserves idempotency, keeps live/routed submit gates and readiness blockers authoritative, rejects expired/revoked/wrong-action/wrong-lineage/consumed-for-different-child approvals and non-executable current step states, preserves submit lease/concurrency/uncertainty behavior, records `consumption_pending` if approval consumption fails after submitted-order persistence, retries that pending approval by reusing the existing submitted order without another adapter submit, exposes API response truth, and adds no extra child intents, fanout, ranking/scoring, CBBO, target reselection, route executor behavior, cross-venue retry, or broad auto-submit.

`tests/test_phase76_automation_closeout.py`
- Phase 7.6 controlled automation closeout safety proof: walks the full approval-gated chain from existing recommendation through recommendation acceptance, target-choice conversion, preview/readiness, and submitted-order handoff; verifies each stage consumes only the exact current-lineage approval and creates/reuses only its expected artifact; proves dry-run, approval creation, generic administrative consume, action-specific consume, readiness, and submitted-order handoff remain distinct; proves stale-lineage and cross-stage approvals cannot authorize actions; proves `consumption_pending` is bounded and repeat calls reuse the existing submitted order without another adapter submit; and asserts no smart routing, best-binding selection, ranking/scoring, CBBO, fanout, split allocation, target reselection, route executor behavior, cross-binding/cross-venue recovery, or broad auto-submit.

`tests/test_phase80_operator_observability.py`
- Phase 8.0 / 8.0.2 operator observability/manual-resolution inspection: verifies the read-only operator routed workflow summary returns the full Phase 7 chain without mutation, exposes approval states and gate truth, surfaces `consumption_pending`, adapter-submit uncertainty, active `submission_in_progress` leases, blocked recommendation/readiness, stale-lineage approvals, submitted-order handoff safety, submit lease/concurrency state, next safe operator action, and no-SOR/no-fanout/no-reselection/no-route-executor boundary flags without creating artifacts, consuming approvals, resolving manual states, calling exchange adapters, or submitting orders.

`tests/test_phase610_phase6_closeout.py`
- Phase 6.10 Phase 6 closeout regression: exercises the complete accepted explicit recommendation-backed single-target path through submitted order, detail/list, actionability/recovery, reconciliation collision protection, lifecycle events, and read-only workflow inspection while proving exactly one target choice, one child intent, and one submitted order with no fanout, allocation, scoring, CBBO, target reselection, route executor behavior, auto-submit, cross-binding recovery, or cross-venue retry.

`tests/conftest.py`
- pytest bootstrap isolation from local `.env` and developer-machine env contamination

`tests/test_operational_docs.py`
- operational-doc existence/reference validation plus review-bundle hygiene validation against an actually produced ZIP

`tests/test_dashboard_static_assets.py`
- Static dashboard asset and boundary checks, including SV evidence, Historical Replay, hidden legacy UAT panels, the SOR-EV2.1/SOR-EV2.2 Evidence Lab tab and overlay controls, SOR-EV1/SOR-EV2 summary path references, canonical SV2.0.2 label, variant matrix/panel visibility, baseline/variant overlay functions, methodology/date-filter warnings, missing-field unavailable states, absence of the invalid Experiments tab, and no order/private/live controls.

`tests/test_uat21_dashboard_visualization.py`
- UAT2.1 dashboard visualization checks: verifies the UAT2 summary JSON loads, expected UAT2 counts are represented, the signal matrix / would-open / no-trade / ETH candidate / timing / drawdown / UAT3 panels and UAT3.4 routed-orders visibility are present, no interactive approval action is added, and forbidden paper/live/order/profitability language is absent from the dashboard surface.
- UAT3.0 sandbox-order design checks: verifies the design report, founder approval template, narrow ETH `sleeve_1h` sandbox subset, sandbox runtime/drawdown/artifact/approval/submit-lease/risk requirements, UAT3.1 blocked decision, dashboard design panel, no active order control, and no order/exchange/live artifact boundaries.

`tests/test_uat304_sandbox_private_read_only_drawdown.py`
- UAT3.0.4 sandbox private read-only drawdown readiness checks: verifies explicit credential approval is required, missing approval blocks private read-only paths, credentials are redacted, private read-only endpoint categories are distinct from order categories, order/cancel/amend/retry/live endpoint paths remain blocked, sandbox account drawdown feeds are labeled `sandbox_account` / `not_live_account`, unavailable fields are explicit, UAT3 dry-run preflight can consume live-fed drawdown status, and the UAT3.0.4 report keeps UAT3.1 blocked.

`tests/test_uat306_sandbox_submit_path_dry_run.py`
- UAT3.0.6 sandbox submit path dry-run checks: verifies the non-persistent submission plan creates no artifacts, the dry-run gate reports no exchange calls, missing actual-submission approval blocks, missing/stale/non-live-fed drawdown blocks, approval/risk/submit-lease failures block, unknown endpoint classification blocks, sandbox order submission is classified without transport invocation, missing artifact labels block, broad top-20 fanout/cross-venue retry/route executor behavior block, and the UAT3.0.6 report keeps UAT3.1 blocked.

`tests/test_uat31_first_sandbox_order_attempt.py`
- UAT3.1 first sandbox/testnet lifecycle probe checks: verifies exact approval is required before credential/transport use, live endpoints block, prior attempts block, manual lifecycle-probe labels are enforced, post-only/nonmarketable order shaping remains under the 10 USDC cap, transport is called only after all gates pass, cancel is scoped only to the submitted sandbox order if open, unexpected fill stops further action, summaries remain redacted, and no production `OrderIntent`, `PreparedVenueOrder`, `SubmittedOrder`, executable approval, paper/live behavior, broad top-20 submission, or second order is created.
- UAT3.2 fixed-key preflight / second sandbox lifecycle attempt checks: verifies exact UAT3.2 approval is required before credential/transport use, fixed-key account/API-wallet readiness is evaluated, live endpoints and prior attempts block, manual lifecycle-probe labels are enforced, order transport is called only when all gates pass, readiness failures block before `/exchange`, cancel is scoped only to the submitted sandbox order if open, unexpected fills stop further action, summaries remain redacted, the UAT4.0 dashboard roadmap request is captured, and no production execution artifacts, paper/live behavior, broad top-20 submission, or second order is created.

`tests/test_uat34_sandbox_routing_pipeline.py`
- UAT3.4 sandbox routing pipeline checks: verifies standard perp equity selection, unified spot USDC fallback, fixed-target ETH-only route validation, top-20/fanout/SOR/target-reselection/route-executor blockers, routed ledger lifecycle/cancel/reconcile/equity-source/sandbox-label fields, duplicate submit preflight blocking, and UAT4.0 roadmap capture.

`tests/test_uat40_dashboard_chart_cockpit.py`
- UAT4.0 dashboard cockpit checks: verifies the UAT Chart Cockpit tab, observation-only watchlist, active ETH sandbox route card, market-data coverage, indicator labels, shadow/sandbox marker semantics, routed-order ledger fields, persistent no-paper/no-live/no-order-control safety labels, and absence of order/cancel/retry/amend/approval/paper-live controls.

`tests/test_uat41_exchange_dashboard_redesign.py`
- UAT4.1 exchange-style dashboard redesign checks: verifies the rebuilt canonical design doc, root design pointer, exchange workstation sections, top bar, watchlist, central chart, right rail, bottom blotter tabs, routed-order lifecycle visibility, observation-only watchlist labels, indicator/marker semantics, and absence of order/cancel/retry/amend/approval/paper-live controls.

`tests/test_uat42_live_market_dashboard_paper_equity.py`
- UAT4.2 dashboard/runtime monitor checks: verifies public-read-only market-data policy, watchlist coverage, deterministic indicators and insufficient-history labeling, observation-only scanner side effects, 60-second sandbox private-read-only balance polling policy, internal 10,000 USDC paper-equity ledger math, sizing from current paper equity, dashboard live-monitor surfaces, marker semantics, no order controls, report existence, and PT0 roadmap capture.

`tests/test_pt001_tradingview_chart_stability.py`
- PT0.0.1 dashboard stability checks: verifies explicit chart height, parent containment, no `autoSize` chart feedback loop, refresh-time series updates without chart destruction, single polling timer guard, live-polling disable query flags, public-read-only endpoint boundaries, no order controls, and no live/paper toggle enabling live.

`tests/test_pt002_historical_strategy_replay_cockpit.py`
- PT0.0.2 historical replay cockpit checks: verifies historical replay truth uses the committed replay summary rather than Hyperliquid testnet prices, audits BTC/ETH/SOL x 15m/1h/4h readiness, requires dynamic 10,000 USDC equity updates, validates fill/cost assumptions, checks entry/exit marker semantics, verifies the dashboard Historical Replay tab and stable chart container, confirms sandbox execution ledger separation, and enforces no-order/no-live dashboard boundaries.

`tests/test_pt003_historical_data_horizon_1d.py`
- PT0.0.3 historical horizon checks: verifies Jan 2025 target-start truth, BTC/ETH/SOL x 15m/1h/4h/1D readiness rows, actual earliest-after-target reporting, labeled 1D aggregation from 4h, dynamic equity preservation, 1D replay export contents, dashboard data-horizon panel, no-testnet-strategy-truth boundary, and no-order/no-private-endpoint dashboard boundaries.

`tests/test_pt_rt1_paper_observation.py`
- PT-RT1 paper-observation checks: verifies public-mainnet strategy-truth payload policy, testnet/private/API-key rejection for strategy truth, expanded requested/resolved scanner blocking for unsupported/precision/stablecoin/unit-semantics cases, the exact 10 PT-RT1.1A lane list, wildcard reason codes, fully closed candle gating, missing indicators not defaulting to zero, independent 10,000 USDC paper-ledger compounding/drawdown/losing-streak behavior, duplicate signal prevention, evidence-only lane labels, disabled-by-default static testnet probe gates, exact approval/cap/kill-switch/unknown-state enforcement, account-targeting vaultAddress semantics, 20 USDC post-only `Alo` order-shape generation for testnet-only plumbing audit rows, PT-RT1.4 active `1h`/`4h`/`1d` timeframe cutover with paused `15m`, reports, and no production execution artifact construction from the strategy lane.

`tests/test_pt_rt1_1_24h_dry_run.py`
- PT-RT1.1 dry-run validation checks: verifies the dry-run report and summary exist, probes-disabled config is enforced with kill switch active and daily cap zero, public-mainnet strategy truth and no private/signed/order/API-key boundaries are reported, missing 24-hour artifacts block PT-RT1.2, duplicate-signal/data-health/ledger sections do not silently pass without runtime evidence, dashboard no-order labels remain expected, and the report builder can mark a complete synthetic artifact set as verified.

`tests/test_pt_rt1_1a_expanded_universe.py`
- PT-RT1.1A readiness checks: verifies the report and summary exist, all 10 lanes and three wildcard lanes are present, alias/blocking policies are documented, the PT-RT1 summary exposes expanded scanner rows, dashboard readiness flags, disabled-by-default testnet probe policy, no-order/no-live boundaries, PT-RT1.1B readiness metadata, and the PT-RT1.1C handoff decision.

`tests/test_pt_rt1_1b_public_market_data.py`
- PT-RT1.1B public-mainnet readiness checks: verifies the Hyperliquid public-mainnet connector policy, testnet/private/account/API-key rejection, requested/resolved watchlist rows, TRON/TRX and PEPE/kPEPE handling, OKB/POL blocking policies, candle normalization, fully closed candle decision wiring, missing-indicator no-zero behavior, runtime command presence, and PT-RT1.1B report/summary existence.
- PT-RT1.1C runtime-start checks: verifies the start report and summary JSON exist, the runtime command includes `--duration-hours 24`, `--disable-testnet-probes`, `--public-mainnet-only`, the output directory is `reports/paper_runtime/pt_rt1_1c_24h_dry_run`, runtime artifacts remain ignored, all 10 lanes and the expanded universe are listed, blocked symbols carry reason codes, no-order/no-live boundaries are stated, the dashboard URL is recorded, and the PT-RT1.1D handoff exists.

`tests/test_sv20_money_flow_1d_expanded_evidence.py`
- SV2.0/SV2.0.1 Money Flow 1D and expanded-universe checks: verifies Money Flow v1.2 includes `sleeve_1d`, existing 15m/1h/4h settings remain unchanged, internal SV2 timeframe is `1d` with display label `1D`, Hyperliquid public mainnet candle payloads stay public/read-only, SHIB alias resolution is explicit, readiness rows split staged data from DB-imported/canonical evidence truth, and dashboard/docs expose the expanded universe without order behavior.

`tests/test_sv201_canonical_evidence_truth_hotfix.py`
- SV2.0.1 canonical evidence truth hotfix checks: verifies Hyperliquid `.999Z` close times normalize to exact boundaries, staged-only data cannot report `imported=true`, compact rows force-close final open positions and count entry fees at open, compact rows cannot be labeled canonical evidence, runtime sleeve allocations are 0.25 each with sum validation, and internal/display timeframe canonicalization remains `1d`/`1D`.


`tests/test_sor_ev1_loss_anatomy.py`
- SOR-EV1 evidence-only validation: verifies canonical SV2.0.2 pack path usage, forbidden evidence-source exclusion, loss anatomy/report output, methodology labels, fixed/deferred variant status, control-pocket reporting, no-order/no-live/no-rule-change flags, and forbidden proof/live-approval language avoidance.

`tests/test_sor_ev3_avoid_sideways_low_volatility.py`
- SOR-EV3 founder-selected low-volatility/chop drilldown checks: verifies canonical SV2.0.2 pack usage, baseline parity, controlled variant list, past/current-candle-only feature definitions, blocked-entry attribution, avoided-loser/missed-winner fields, control-pocket reporting, founder-review label fields, no production Money Flow rule mutation, and no forbidden proof/live-approval language.

`tests/test_ev_audit1_full_review.py`
- EV-AUDIT1 audit report checks: verifies the Markdown/JSON audit exists, inventories Money Flow v1.2 / SOR / MF-ORIG / pending STRAT-EV1 status, includes data integrity, methodology scorecard, comparison matrix, biggest winners/losers, losing streaks, regime/control-pocket sections, issue list, backtest adequacy, paper-observation readiness, boundary flags, no dashboard-date-filter canonical evidence, and no production-rule mutation.

`tests/test_strat_disc1_autonomous_discovery.py`
- STRAT-DISC1 research harness checks: verifies data inventory generation, candidate gate thresholds/labels, no runtime/order boundary flags, no private/signed/order path imports, lookahead/OOS policy, summary/report artifact writing, and no-production/no-live approval semantics.

`tests/test_goal_strat1_discovery.py`
- GOAL-STRAT1 expanded research harness checks: verifies data inventory generation, candidate gate thresholds/labels, drawdown/profit-factor/concentration calculations, report/summary/failure artifact writing, no runtime/order boundary flags, no private/signed/order path imports, lookahead/OOS policy, and no-production/no-live approval semantics.

`tests/test_goal_strat2_worth_testing.py`
- GOAL-STRAT2 selector checks: verifies exactly two non-existing research-only candidates, family diversity, testing-gate metrics, existing-lane/family exclusions, report/summary/candidate artifact writing, no runtime/order boundary flags, and no-production/no-live approval semantics.

`tests/test_strat_prune1_strategy_lane_pruning.py`
- STRAT-PRUNE1 pruning guardrail checks: verifies the report/summary exist, all 10 current PT-RT lanes are classified, the recommended next slate has no more than four candidates plus baseline, `15m` is paused, candidate lanes are synthetic-only, only baseline is testnet-eligible, no lane is production/live eligible, and future add-candidates are recommendation-only rather than implemented runtime lanes.
