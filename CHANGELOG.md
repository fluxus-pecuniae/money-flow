# CHANGELOG

Canonical repo changelog — the recent rolling window. New entries are added
here (newest-first). Older entries (v2026.06.08.006 and earlier) are in
[`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md); recent window + archive
together are the complete, canonical history. When this file exceeds ~25
entries, roll the oldest into the archive as part of the post-task update.

Entry schema:

- `version`
- `recorded_at_utc`
- `scope`
- `intent`
- `affected_files`
- `validation_performed`

---

## v2026.06.12.005

- `recorded_at_utc`: `2026-06-12T07:30:00Z`
- `scope`: `REGIME1 market-regime risk-off filter (risk tool, not alpha)`
- `intent`: `Research/tool only; signal-only — no orders, no private/signed endpoints, no testnet/live, no approval surface, no runtime change. Turns trend's one durable validated property (drawdown defense) into a reusable market-regime filter: breadth of per-asset tsmom_ev1.tsmom_signal trend signs across the liquid majors + a BTC bellwether rule (vote|required) -> risk_on/risk_off on closed candles only, graded risk_score exposed for display. Bounded grid (3 lookbacks x 3 breadth thresholds x 2 BTC rules = 18), train-only choice (chronological 70/30 on the DATA1 Binance perp universe, 7 assets, 2020-09 -> 2026-06, both books idle through a common 90-candle warm-up). The filter had to EARN its use on an equal-weight long book (always-long vs regime-gated, EXEC-EV1 conservative friction, weekly rebalance) and the verdict is the honest FAIL: regime_filter_does_not_reduce_drawdown_oos — the train-chosen lb30/br0.5/vote config reduced OOS max drawdown 29.76% vs the pre-committed 30% material bar (missed by 0.24pp) AND worsened drawdown in the chop fold (45.6% vs 39.4% in 2022-08->2024-07; 58 OOS flips — the whipsaw cost of a 30d-lookback filter), despite real defensive texture (OOS Sharpe 0.53 vs 0.13, return +26% vs -19.6%, dd 46.2% vs 65.7%; fold C dd 46% vs 66%). Hindsight texture surfaced and labeled NOT-A-VERDICT (TREND-SUITE1 precedent): lb60/br0.6/required would have cut OOS dd to 33.3% (49% reduction) and a min-train-drawdown criterion would have chosen lb90/br0.6/required (OOS dd 43.6%) — the criterion gap is itself a finding about regime-filter fragility; the committed train-Sharpe choice was not re-decided. Whipsaw fully characterized (OOS: 58 flips, 53% of days risk-off, 6/30 false spells, return given up vs drawdown avoided in USDC). Per Must 3 the tool ships anyway with the failed verdict on every surface: scripts/run_regime_filter.py (public read-only Binance klines or --input-json replay; live sample 2026-06-12: RISK_OFF, 0/7 majors trend-up, BTC down; writes ignored reports/regime1/current_regime_state.json) and the importable gate regime1.build_regime_gate(datasets) -> RegimeGate.is_risk_on(as_of) through the ADDITIVE strategy_types.REGIME_FILTER_REF seam (no routing/type/gate changes; defaults pinned by test to the committed train-only choice; the gate never guesses warm-up states and refuses pre-history as_of). Honest framing structural: the risk-tool-not-alpha disclaimer + committed-verdict note embedded in the module, every state dict, the CLI stdout/JSON, the gate, the summary, and the report; text guard green. 11 deterministic offline tests wired into blocking CI. Research Log authored fail; aggregator --check green. Four oldest changelog entries (v2026.06.09.001, v2026.06.08.012/.011/.010) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/regime1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/run_regime1_evidence.py`
  - `scripts/run_regime_filter.py`
  - `docs/regime1_market_regime_risk_off_filter_evidence.md`
  - `docs/regime1_market_regime_risk_off_filter_evidence_summary.json`
  - `docs/research_log.json`
  - `tests/test_regime1_filter.py`
  - `.github/workflows/ci.yml`
  - `.gitignore`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_regime1_evidence.py`
  - `.venv/bin/python scripts/run_regime_filter.py` (live public read-only sample)
  - `.venv/bin/python -m pytest -q tests/test_regime1_filter.py`
  - `.venv/bin/python scripts/build_research_log.py && .venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_operational_docs.py tests/test_tsmom_ev1_evidence.py tests/test_trend_suite1_evidence.py tests/test_trend_overlay1.py tests/test_sel_ev1_selection_evidence.py tests/test_fund_ev1_evidence.py tests/test_fund_ev2_evidence.py tests/test_fund_scale1_evidence.py tests/test_fund_venues1_evidence.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`

## v2026.06.12.004

- `recorded_at_utc`: `2026-06-12T06:00:00Z`
- `scope`: `RLOG display fix: TREND-SUITE1 vol-cap analytics rendered as a computed view`
- `intent`: `Display/tooling only; no research result, runtime, strategy, order, or approval change. The TREND-SUITE1 research_log analytics entry "Vol-cap removal effect (23 pairs)" pointed kind=value at the summary's headline_answers node — the dashboard rendered the whole nested object as a raw JSON blob, and the node was also the wrong one (the vol-cap pair data lives in vol_targeting_comparison). Added the trend_suite1_vol_cap_effect computed view to scripts/build_research_log.py (kvs: 23/23 pairs classified drawdown-without-more-OOS-return, 16/23 higher full-window return uncapped, 0/23 kept OOS; table: the five pairs with the most OOS drawdown added), repointed the Decision Log block's analytics to it, and recorded a dated correction line in the TREND-SUITE1 entry (display metadata only; no factual content changed). Aggregator rebuilt; --check green. Numbers reproduce the committed narrative exactly. Oldest changelog entry (v2026.06.08.009) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `scripts/build_research_log.py`
  - `docs/research_log.json`
  - `money-flow/03_Decision_Log.md`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
- `validation_performed`:
  - `.venv/bin/python scripts/build_research_log.py && .venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_trend_suite1_evidence.py tests/test_operational_docs.py tests/test_dashboard_static_assets.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`

## v2026.06.12.003

- `recorded_at_utc`: `2026-06-12T05:15:00Z`
- `scope`: `FUND-VENUES1 funding carry on deep venues with leverage`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. The structural re-open FUND-EV2/FUND-SCALE1 sanctioned: the same delta-neutral funding-carry hypothesis on venues with materially different cited fee schedules and 6-7 years of DATA1 funding history — Binance perp+spot and Bybit perp+spot carry the verdict (cross-venue Binance perp + Coinbase spot is the variant), with gross leverage {1x,3x,5x} as an explicitly modeled variable. New additive margin_model seam on the FUND-EV1 simulator (default None byte-identical, pinned by the 41 existing FUND tests): borrow interest on the real cash shortfall (documented 0.02%/day, swept with every cost term) and an account-level intraday liquidation check marking every leg at its worst same-day extreme; liquidation force-closes the book at stressed prices through the cited cost model. Fees cited (Binance VIP0 perp 2/5 spot 10/10 bps; Bybit non-VIP 2/5.5, 10/10; OKX Lv1 cited for the record; Coinbase 60 bps taker for the variant) at the tier a 10k account's OWN flow earns (FUND-SCALE1 rule); the gateable verdict prices taker fills only — maker is a non-gateable ceiling; the venue-fair window is enforced from DATA1 coverage (OKX ~92d / Kraken ~366d / HL 1126d funding excluded with recorded reasons, K-036). Gate v3 = FUND-EV2 full bar + every-OOS-regime positivity + zero liquidation events. VERDICT: honest FAIL in ALL NINE (construction x leverage) cells — carry_does_not_survive_realistic_costs_and_tail_oos. The texture is the finding: (1) deep venues DID fix the cost half of the HL fail — binance_single 1x has OOS net +179 (Sharpe 3.5, maxDD 0.08%), every fold/leave-one-out/OOS-regime/cycle-segment positive, cost breakpoint 5.0x cited costs (vs HL FUND-EV2 0.75x), zero liquidations — and fails ONLY the pre-committed legged-execution tail stress (9.68% vs 8% limit), with OOS capture economically thin (~0.76%/yr at 1x); (2) leverage, the hoped-for capture multiplier, is CATASTROPHIC, not thin: at 3x the 2021 alt-mania liquidates the book 4 times and wipes the account (full net -9999.82 = -100%), at 5x equity goes negative (-10788); even calm-window Bybit liquidates once at 5x with stressed DD ~90%; (3) discrete rebalancing means a nominal 1x book transiently needs ~58% of equity in financing during violent rallies (max_borrowed 5816 at 1x; the margin model priced it). Adversarial-review trigger (required before believing any POSITIVE verdict) did not fire — no cell passed; the near-miss was not softened and its positive components are attacked in the deterministic tests + report. strategy_types gains the fund_venues1_ prefix on the same funding_carry route/gate. 17 deterministic offline tests wired into blocking CI. Research Log authored fail; aggregator --check green. Oldest changelog entry (v2026.06.08.008) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/fund_venues1.py`
  - `services/strategy_validation/fund_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/run_fund_venues1_evidence.py`
  - `docs/fund_venues1_deep_venue_leverage_carry_evidence.md`
  - `docs/fund_venues1_deep_venue_leverage_carry_evidence_summary.json`
  - `docs/research_log.json`
  - `tests/test_fund_venues1_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_fund_venues1_evidence.py`
  - `.venv/bin/python -m pytest -q tests/test_fund_venues1_evidence.py`
  - `.venv/bin/python -m pytest -q tests/test_fund_ev1_evidence.py tests/test_fund_ev2_evidence.py tests/test_fund_scale1_evidence.py tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_trend_suite1_evidence.py tests/test_trend_overlay1.py tests/test_exec_ev1_execution_quality.py`
  - `.venv/bin/python scripts/build_research_log.py && .venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`

## v2026.06.12.002

- `recorded_at_utc`: `2026-06-12T02:30:00Z`
- `scope`: `DATA1 multi-venue market & funding data foundation`
- `intent`: `Data ingestion only — public read-only endpoints, no keys, no private/signed/order endpoints, no strategy logic, no runtime change. Fixes the HL-only data limitation every prior phase carried: builds the multi-venue base (perp funding history, perp daily candles, spot daily candles) for BTC ETH SOL XRP DOGE BNB AVAX across hyperliquid/binance/bybit/okx/coinbase/kraken at the longest history each PUBLIC API allows, so the next funding test is venue-fair (FUND-VENUES1 unblocked) and trend/regime re-tests get >1 OOS cycle (Coinbase BTC spot from 2015-07, ~3979 daily candles, vs the 889-candle HL window). services/market_data/data1_multi_venue.py: venue x asset x series catalog with explicit venue_lacks_market gaps (25 cells: Coinbase has no public perp/funding market data + no BNB; OKX/Kraken list no BNB; HL spot only BTC/ETH/SOL), paginated fetchers over an injected transport hard-restricted to a public-endpoint allowlist, strict normalizers (midnight-UTC daily guard — the probe-caught OKX UTC+8 default bar is fetched as 1Dutc and anything non-midnight is REFUSED, not mis-aligned), FUND-EV1-convention daily funding aggregation with exact Decimal sums + per-day event counts (1h HL/KrakenF vs 8h Binance/Bybit/OKX recorded declared AND observed, summed never rescaled; partial days reported never filled), union-calendar alignment with explicit None holes (no forward-fill/interpolation/truncation — the real Coinbase XRP 904-day delisting hole survives visibly), zero-volume backfill accounting (HL serves ~900+ pre-launch zero-volume perp candles per asset; counted via coverage.zero_volume_rows/first_nonzero_volume_close so backfill is never mistaken for market history), and the load_data1_dataset loader (sha256 verification raises on tamper; missing artifacts surface as artifact_missing_rerun_fetch_script, never fabricated; coverage flags + as-of on every series). scripts/fetch_data1_multi_venue_snapshot.py: one-shot resumable snapshot (101/101 expected series fetched OK 2026-06-11; raw 57MB native payloads stay ignored under /tmp/money-flow-data1/raw_series/), committed provenance docs/data1_multi_venue_snapshot_summary.json (endpoints, cited rate limits, funding intervals, coverage, gap report, sha256 per artifact, audit samples). Honest venue limits recorded: OKX public funding history is only a trailing ~3-month window; Kraken Futures funding ~1y; Kraken spot OHLC capped at last 720 candles. 20 deterministic offline tests wired into the blocking CI lane + an env-gated live smoke (DATA1_LIVE_SMOKE=1, skipped in CI). Research Log authored context (data_prep). Oldest changelog entry (v2026.06.08.007) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/market_data/data1_multi_venue.py`
  - `scripts/fetch_data1_multi_venue_snapshot.py`
  - `docs/data1_multi_venue_data_foundation.md`
  - `docs/data1_multi_venue_snapshot_summary.json`
  - `docs/research_log.json`
  - `tests/test_data1_multi_venue.py`
  - `tests/test_data1_live_smoke.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `KNOWN_ISSUES.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/fetch_data1_multi_venue_snapshot.py` (live public fetch; 101 series ok, 25 venue gaps recorded, 0 fetch failures)
  - `.venv/bin/python -m pytest -q tests/test_data1_multi_venue.py`
  - `.venv/bin/python scripts/build_research_log.py && .venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`

## v2026.06.12.001

- `recorded_at_utc`: `2026-06-12T01:45:00Z`
- `scope`: `TREND-SUITE1 canonical trend-following suite evidence`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Tests the canonical trend systems TSMOM-EV1 never tried — Donchian channel breakout (Turtle 20/55, channel + ATR/chandelier 2.8xATR14 trailing exits), dual-MA crossover ({10,20,30}x{50,100,200} +ATR variant on 20x100), multi-timeframe confirmation (daily 30/60/90d sign gated by a frozen 8-week weekly sign, +ATR variant on 60d), the TSMOM carry-over (30/60/90d, weekly cadence, apples-to-apples), and a majority/average ensemble of five fixed canonical members — EVERY signal cell under BOTH vol-targeted (EV1-style 0.20/N risk budget, 0.40 weight cap) and non-vol-targeted equal-dollar sizing (strength/N, same 1.5x gross cap), the key lever since vol targeting cuts exposure exactly in outlier trends. 46-config bounded grid on the eight liquid majors (889 aligned 1d candles), train-only choice, judged by the SAME buy-and-hold risk-adjusted gate as TSMOM-EV1 (new strategy_types route trend_suite / prefix trend_suite1_ deliberately shares TSMOM_GATE_ID; per_symbol/selection/funding gates still refuse it). The EV1 simulator is reused verbatim through its signal_provider/rebalance_timestamps seams; tsmom_ev1.target_weights now accepts fractional strengths (ensemble-average sizing) with the integer ±1 path byte-identical (pinned by test; all 78 existing evidence tests green). BOTH headline hypotheses came back NEGATIVE, decisively: (1) the richer suite finds nothing better than one-form TSMOM — the train-only choice across all 46 configs picked the EV1 signal again (trend_suite1_tsmom30_signal_vt_1d), whose OOS stats reproduce the committed EV1 numbers digit for digit (Sharpe -1.478 / return -12.23% / max DD 16.56% vs buy-hold -1.807 / -61.69% / 65.68%) — relative gate PASS with both absolute-loss qualifiers (defensive value only); NO trend form clears the absolute bar (hindsight-best mtf60w8_atr_vt still lost -4.1% OOS; ma_cross/mtf/ensemble family champions fail even the relative full gate; donchian20x10_atr_vt passes it, also at an absolute loss). (2) Vol-targeting was NOT the cap: all 23 vt-vs-eq pairs classify removing_vol_target_added_drawdown_without_more_return_oos — in 16 of 23 pairs the uncapped variant earned a higher full-window (bull-heavy) return and every pair gave it back OOS (leverage on the same signal, not a new edge). 29/46 configs pass the relative OOS screen (trend's defensive value is consistent across forms); per-family no-lookahead verified (truncation + future-tampering probes incl. a caught leaky scorer); per-symbol PnL reconciles to net for every conservative row (K-019). Full gate (walk-forward thirds + leave-one-out + late-entry) for the global chosen config and each family champion; per-config OOS screen with the same verdict vocabulary, never forced positive. Research Log: authored MIXED (badge 'defensive only - suite adds nothing'); aggregator rebuilt (19 entries, --check green). Tests: tests/test_trend_suite1_evidence.py (19 deterministic offline tests) wired into the blocking CI lane. Trend family closed on both sanctioned axes (signal form, sizing); TREND-OVERLAY1 stays deployed unchanged; REGIME1 / DATA1 / FUND-VENUES1 queued in TODO. Oldest changelog entry (v2026.06.08.006) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/trend_suite1.py`
  - `services/strategy_validation/strategy_types.py`
  - `services/strategy_validation/tsmom_ev1.py`
  - `scripts/run_trend_suite1_evidence.py`
  - `docs/trend_suite1_canonical_trend_suite_evidence.md`
  - `docs/trend_suite1_canonical_trend_suite_evidence_summary.json`
  - `docs/research_log.json`
  - `tests/test_trend_suite1_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_trend_suite1_evidence.py`
  - `.venv/bin/python scripts/build_research_log.py && .venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_trend_suite1_evidence.py tests/test_rlog1_research_log.py`
  - `.venv/bin/python -m pytest -q tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_trend_overlay1.py tests/test_fund_ev1_evidence.py tests/test_fund_ev2_evidence.py tests/test_fund_scale1_evidence.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`

## v2026.06.11.008

- `recorded_at_utc`: `2026-06-11T22:45:00Z`
- `scope`: `TREND-OVERLAY1 deployable trend drawdown-control overlay (signal only)`
- `intent`: `Read-only signal tool; no orders, no auto-execution, no private/signed/order endpoints, no testnet/live, no production approval, no runtime change. Operationalizes the TSMOM-EV1 finding (vol-targeted trend as DRAWDOWN CONTROL: bear drawdown 66% -> 17% while losing 12.2% absolute OOS; authored mixed - defensive, not profitable) as a forward calculator on the latest fully-closed public-mainnet candles. services/strategy_validation/trend_overlay1.py REUSES the exact TSMOM-EV1 machinery (tsmom_signal / realized_vol_annual / target_weights with the 0.40 weight cap and 1.5x gross cap) under the evidence run's train-chosen config (tsmom_ev1_lb30_vt20_long_only_1d) - nothing re-derived or re-tuned; the defaults are PINNED BY TEST to the committed TSMOM-EV1 summary so a silent re-tune fails CI. scripts/run_trend_overlay.py fetches the latest daily candles for the eight liquid majors from Hyperliquid public mainnet candleSnapshot (read-only, no keys), drops the in-progress candle (closed-candle-only no-lookahead boundary, tested: future/in-progress rows cannot change the output), prints the signal table, and writes the ignored runtime artifact reports/trend_overlay/current_trend_overlay.json (.gitignore extended); --input-json replays a saved payload offline (no network, used by tests); --account-size scales target exposure (default 10,000 USDC). HONEST FRAMING carried in every surface (module docstring, CLI stdout, JSON output, docs): drawdown-control overlay NOT alpha, signal only not an order, no production approval implied or granted - the trading-safety text guard is green (it caught and rejected one wording during the build, which was rephrased to a recognized negation). Real sample run committed in docs (2026-06-11): all eight majors in 30d downtrend -> the overlay's current target is FULLY FLAT (0 of 10,000 USDC exposed) - the validated defensive action in the live bear. OS panel decision: SKIPPED, documented - a dashboard panel would touch index.html/evidence-dashboard.js/static-asset guards/DASH-QA1 in lockstep plus empty-state handling for an ignored artifact; non-trivial surgery for a CLI-first tool; DASH-QA1 untouched. Research Log: authored CONTEXT (deployment of an existing validated finding, not a new strategy test; badge 'defensive overlay deployed - signal only'); aggregator unchanged except the new block (18 entries, --check green). Tests: tests/test_trend_overlay1.py (9 deterministic offline tests: defaults pinned to the committed TSMOM-EV1 choice, trend states, risk-equal vol targeting + vol-spike reduction, weight/gross caps, closed-candle no-lookahead, insufficient-history flat, disclaimer + signal-only boundaries on every surface, offline CLI end-to-end) wired into the blocking CI lane. Oldest changelog entry (v2026.06.08.005) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/trend_overlay1.py`
  - `scripts/run_trend_overlay.py`
  - `docs/trend_overlay1_deployable_drawdown_overlay.md`
  - `docs/trend_overlay1_deployable_drawdown_overlay_summary.json`
  - `docs/research_log.json`
  - `tests/test_trend_overlay1.py`
  - `.github/workflows/ci.yml`
  - `.gitignore`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_trend_overlay1.py`
  - `.venv/bin/python scripts/check_trading_safety_text.py`
  - `.venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py tests/test_rlog1_research_log.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`
  - `python -m compileall -q services scripts tests`
  - `git diff --check`

## v2026.06.11.007

- `recorded_at_utc`: `2026-06-11T21:45:00Z`
- `scope`: `FUND-SCALE1 funding carry scale & fee-tier viability map`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Maps the one axis FUND-EV2 sanctioned as new evidence: account size x cited fee tier. Published schedules cited in full (Hyperliquid 14d-weighted volume tiers T0-T6, spot counted double, perp taker 4.5->2.4 bps / spot taker 7.0->2.5 bps; Kraken Pro 30d tiers taker 40->5 bps; maker-volume-share rebates noted as market-maker flow, not modeled). Both size effects modeled honestly: tier fees + amortizing fixed costs (helps) AND EXEC-EV1 sqrt impact driven by the actual per-size traded notional (hurts). Two binding honesty rules: a tier counts as ACHIEVED only if the strategy's OWN traded volume at that size reaches the published qualifying volume (own 14d weighted volume at a $5M account: $1.8M vs $5M needed for HL tier 1), and any cell whose single fill exceeds 10% of its candle's dollar volume is impact-implausible and cannot pass. Sweep: 5 sizes (10k/50k/250k/1M/5M) x 5 tiers x 2 constructions with per-rung train-only config choice and the full gate battery (OOS, walk-forward, leave-one-out, regimes, legged stress at cost x2) on achieved + candidate cells; 96 cached deterministic sims. RESULT: verdict carry_does_not_reach_viability_at_credible_scale - the achieved-tier surface is negative at EVERY size and the loss as % of equity GROWS with size (-0.065% at 10k -> -0.101% at 5M, hl tier 0); the only positive stripe (Kraken 10 bps VIP at >=50k, +0.02-0.05%) needs ~30x the strategy's own volume AND fails participation plausibility - excluded on both grounds; the maker-bound line (passive fills, zero spread, non-fill risk unmodeled, explicitly NON-GATEABLE) ceilings at +0.26% OOS (~0.8%/yr). The 10k base-tier cell reproduces FUND-EV2's retail fail exactly (test-pinned; not re-litigated). Funding carry now closed on BOTH sanctioned axes (cost realism + scale/fee tiers); only structural changes (maker flow, fee regime, atomic execution) could reopen it as new phases. Additive seams: fund_ev1 simulate gains starting_equity + max-fill participation/notional tracking (defaults byte-identical; FUND-EV1/EV2 suites untouched). Research Log: authored FAIL (badge 'scale does not unlock it'); aggregator gains the viability-map view (17 entries, --check green). Tests: tests/test_fund_scale1_evidence.py (13 deterministic offline tests: tier tables monotone + cited, fee term isolation, fees-down=>net-up, impact/participation up with size, flat-cost amortization, own-volume tier achievement incl. spot-double, computed band semantics incl. assumed/implausible exclusion + contiguity, no-lookahead at size, K-019 at size, committed map/guard checks, FUND-EV2 retail-cell reproduction, research-log honesty pin) wired into the blocking CI lane. Oldest changelog entry (v2026.06.08.004) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/fund_scale1.py`
  - `services/strategy_validation/fund_ev1.py`
  - `scripts/run_fund_scale1_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/fund_scale1_size_fee_tier_viability_summary.json`
  - `docs/fund_scale1_size_fee_tier_viability.md`
  - `docs/research_log.json`
  - `tests/test_fund_scale1_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_fund_scale1_evidence.py tests/test_fund_ev2_evidence.py tests/test_fund_ev1_evidence.py`
  - `.venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_exec_ev1_execution_quality.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`
  - `python -m compileall -q services scripts tests`
  - `git diff --check`

## v2026.06.11.006

- `recorded_at_utc`: `2026-06-11T19:45:00Z`
- `scope`: `FUND-EV2 funding carry re-test at cited realistic costs`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. The one honest re-test of FUND-EV1's fail: was it our conservative cost model (HL spot priced at the widest mid-alt tier) or a real absence of capturable edge? DISCIPLINE GUARD: costs are CITED, never tuned to the verdict, and a cost-sensitivity sweep (0.25x-5x) publishes exactly where the OOS edge dies. Cited basis: Hyperliquid fee docs (fetched 2026-06-11, base tier: perp taker 4.5 bps, spot taker 7 bps); one-shot public read-only l2Book calibration of all eight books committed with provenance (docs/fund_ev2_l2book_calibration_summary.json via scripts/fetch_fund_ev2_l2book_calibration.py - measured half-spreads BTC perp 0.08 / UBTC spot 0.08 / USOL 2.37 bps etc., FUND-EV1's spot tier was ~15x too wide); Kraken Pro base tier spot taker 40 bps for the cross-venue leg (Coinbase Advanced base tier worse at 60 bps); flat 2 USDC/fill cross-venue settlement. Two constructions each with honest costs AND risks: hl_single (33-51 bps round trips) and cross_venue (115-119 bps - retail FEES close it before depth helps; cad14 configs never clear the entry bar). Selectivity + longer holds (Must 3): enter only when trailing-7d funding x planned hold >= 2x round-trip cost, hold-while-favorable hysteresis, 2% band, 14/28d cadences. Implemented as ADDITIVE seams on the FUND-EV1 simulator (optional leg_cost_model, per-config band, entry margin; defaults byte-identical - FUND-EV1's 14 tests untouched and green). RESULT: verdict carry_does_not_survive_realistic_costs_and_tail_oos - train-chosen hl_single cad14 top2 (train +4.36%, Sharpe 8.6) lost -6.5 USDC OOS; the SAME config under FUND-EV1's model lost -161 OOS (realistic re-pricing recovered ~155 of drag and still negative); hindsight cad28 rows were OOS-positive (+16.6/+8.6) but train choice honestly cannot find them (third overfit catch); leave-one-out mixed (drop-ETH negative); regimes all positive (bear +91 - the FUND-EV1 regime bleed fixed by selectivity); stressed tail inside limits (DD 3.1% vs 8%). THE BREAKPOINT: OOS edge dies at cost scale 0.75 - below the cited realistic level; positive only at 0.25-0.5x (implausibly cheap = fail by the guard). Conclusion stated plainly: FUND-EV1's spot-leg conservatism was ours (~15x, named in our_error) but correcting it does NOT flip the verdict - funding carry is CLOSED at 10k retail size; no FUND-EV3 cost tweak. Research Log: authored FAIL (badge 'edge dies below realistic costs'); aggregator gains fund_ev2 computed views (16 entries, --check green). TODO: TREND-CARRY inherits the cited cost model + the carry-cannot-pay-for-entries constraint. Tests: tests/test_fund_ev2_evidence.py (15 deterministic offline tests: routing, per-venue cited costs applied, sweep monotonicity on the pure-repricing path, selectivity gating + hysteresis, cross-venue legging exposure, simulator-level no-lookahead, K-019, gate v2 verdicts/breakpoint/fragility, committed-summary + calibration checks, research-log honesty pin) wired into the blocking CI lane. Oldest changelog entry (v2026.06.08.003) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/fund_ev2.py`
  - `services/strategy_validation/fund_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/fetch_fund_ev2_l2book_calibration.py`
  - `scripts/run_fund_ev2_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/fund_ev2_l2book_calibration_summary.json`
  - `docs/fund_ev2_realistic_cost_carry_evidence_summary.json`
  - `docs/fund_ev2_realistic_cost_carry_evidence.md`
  - `docs/research_log.json`
  - `tests/test_fund_ev2_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_fund_ev2_evidence.py tests/test_fund_ev1_evidence.py`
  - `.venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_exec_ev1_execution_quality.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`
  - `python -m compileall -q services scripts tests`
  - `git diff --check`

## v2026.06.11.005

- `recorded_at_utc`: `2026-06-11T16:45:00Z`
- `scope`: `FUND-EV1 delta-neutral funding carry evidence`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Tests the structural non-predictive edge: harvest Hyperliquid perp funding hedged delta-neutral on ONE venue (short perp + long HL spot equal notional; BTC/ETH/SOL via Unit spot + native HYPE; aligned window 2025-05-11 -> 2026-06-08, limited by the youngest spot listing USOL), 10k USDC basis. New committed data input: public read-only fundingHistory hourly rates aggregated to daily sums per coin with provenance + sha256 (docs/fund_ev1_funding_data_snapshot_summary.json via scripts/fetch_fund_ev1_funding_snapshot.py; raw hourly + HL spot candles are documented ignored artifacts). New fourth strategy-type route funding_carry (prefix fund_ev1_) with its OWN gate: net carry after ALL costs positive OOS (chronological 70/30 + anchored walk-forward thirds), not bull-only, leave-one-out robust, tail drawdown inside documented limits (OOS <=5%, stressed <=8%) - judged on Sharpe + max drawdown, never gross funding. Simulator: pending-fill queue (fills only enter the book when their candle closes - a lagged hedge leg holds REAL one-leg exposure), exact daily funding accrual on the perp leg (positive funding pays the short), EXEC-EV1 friction + fees on BOTH legs (spot always at the widest mid-alt tier), trailing-funding tilt (causal), rebalance band, forced final close, per-symbol reconciliation (K-019). Bounded 8-config grid (collect_only/flip_sides x cadence 7/14 x top 2/4), train-only choice. RESULT: gate verdict carry_does_not_survive_costs_and_tail_oos - train (bull, funding 8-14%/yr) +4.23% Sharpe 7.2; OOS (2026 funding-compressed bear) -33 USDC (-0.32%, Sharpe -1.55) with gross OOS funding still +50 but two-leg conservative friction eating more than all of it; full-window net +392 vs gross +560 (costs ate 30.0%); walk-forward fold C negative; ALL leave-one-out drops negative. Clean-fill neutrality is tight (max residual 0.18%, stressed DD 0.92%) - the real tail is the LEGGED FILL: one slow hedge leg leaves up to 47.9% of equity unhedged for a day, a modeled 11.3% gap loss at the window's worst candle (23.6%). Flip-side rows assume unmodeled spot borrow (upper bounds, documented); daily-close accrual approximation documented. Research Log: authored outcome FAIL (badge 'costs + bear eat the carry'); schema class list extended with funding_carry; aggregator gains fund_ev1 computed views (15 entries, --check green). TREND-CARRY synthesis hypothesis recorded in TODO (trend short side paid by funding - with the regime caveat that funding compresses exactly when the bear arrives). Tests: tests/test_fund_ev1_evidence.py (14 deterministic offline tests: routing, exact funding accrual + sign, two-leg neutrality, costs on both legs, no-lookahead + leaky-reader catch, real one-leg-exposure stress, inversion exit, reconciliation, gate semantics incl. every reason code, committed-summary/snapshot reconciliation, research-log honesty pin) wired into the blocking CI lane. Oldest changelog entry (v2026.06.08.002) rotated verbatim into CHANGELOG_ARCHIVE.md per DOC-LEAN1.`
- `affected_files`:
  - `services/strategy_validation/fund_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/fetch_fund_ev1_funding_snapshot.py`
  - `scripts/run_fund_ev1_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/fund_ev1_funding_data_snapshot_summary.json`
  - `docs/fund_ev1_delta_neutral_carry_evidence_summary.json`
  - `docs/fund_ev1_delta_neutral_carry_evidence.md`
  - `docs/research_log_schema.md`
  - `docs/research_log.json`
  - `tests/test_fund_ev1_evidence.py`
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -q tests/test_fund_ev1_evidence.py`
  - `.venv/bin/python scripts/build_research_log.py --check`
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py tests/test_tsmom_ev1_evidence.py tests/test_sel_ev1_selection_evidence.py tests/test_exec_ev1_execution_quality.py`
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py`
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py`
  - `python -m compileall -q services scripts tests`
  - `git diff --check`

## v2026.06.11.004

- `recorded_at_utc`: `2026-06-11T15:00:00Z`
- `scope`: `TSMOM-EV1 volatility-targeted time-series momentum evidence`
- `intent`: `Research/evidence only; no runtime, strategy-rule, order, testnet, live, or production-approval change. Tests trend done right after the earlier trend failures: per-asset time-series momentum (sign of trailing 30/60/90d return; exact zero = flat) with VOLATILITY TARGETING + equal risk budgets (risk parity) on the eight liquid majors (BTC/ETH/SOL/XRP/DOGE/BNB/SUI/AVAX; HYPE excluded - mid-alt tier, short history), 10k USDC basis, weekly rebalance, next-open fills, EXEC-EV1 depth-aware friction at traded notional, gross leverage cap 1.5x, per-asset weight cap 0.40, bounded 12-config grid chosen on train only. New third strategy-type route time_series_momentum (prefix tsmom_ev1_) with its OWN gate: Sharpe + max drawdown vs EQUAL-WEIGHT BUY-AND-HOLD, OOS (chronological 70/30 + anchored walk-forward thirds), post-conservative-friction, leave-one-out across all eight assets, late-entry sensitivity - never the selection random-benchmark or per-symbol breadth gates. Benchmarks computed on identical machinery: buy-hold equal-weight (headline), always-long no-vol-target, always-long vol-targeted (leveraged-beta probe), seeded random long/flat (20 seeds, sanity). RESULT: gate verdict beats_buy_hold_risk_adjusted_oos WITH non-failing honesty qualifiers (oos_absolute_sharpe_not_positive_relative_edge_only, oos_absolute_return_negative_defensive_value_only): chosen lb30/vt20/long-only OOS Sharpe -1.48 / DD 16.6% / return -12.2% vs buy-hold -1.81 / 65.7% / -61.7% in a bear window; edge survives both walk-forward folds (+1.16/+0.41) and all 8 leave-one-out drops; beats vol-targeted beta (-1.89) and random median (-2.00) but not the best random seeds (max -1.12); hindsight long/short configs had positive OOS Sharpe (+0.22) but the train split honestly chose long-only and perp funding is unmodeled (documented). Per-symbol PnL reconciles to net (K-019 lesson); max name share ~34%. Research Log: authored outcome MIXED (badge 'defensive, not profitable') - a relative pass with negative absolute OOS performance must never render green; new standing rule that relative gates carry absolute qualifiers (hardened-gates rail); schema class list extended with time_series_momentum. Tests: tests/test_tsmom_ev1_evidence.py (13 deterministic offline tests incl. vol-parity risk contributions, leaky-scorer catch, friction monotonicity, gate semantics + qualifier pins, committed-summary reconciliation, research-log honesty pin) wired into the blocking CI lane. Aggregator gains tsmom computed analytics views; research_log.json now 14 entries; DASH-QA1 12/12 with zero green badges preserved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `services/strategy_validation/tsmom_ev1.py`
  - `services/strategy_validation/strategy_types.py`
  - `scripts/run_tsmom_ev1_evidence.py`
  - `scripts/build_research_log.py`
  - `docs/tsmom_ev1_vol_targeted_momentum_evidence.md`
  - `docs/tsmom_ev1_vol_targeted_momentum_evidence_summary.json`
  - `docs/research_log.json`
  - `docs/research_log_schema.md`
  - `tests/test_tsmom_ev1_evidence.py`
  - `.github/workflows/ci.yml`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_tsmom_ev1_evidence.py` → deterministic evidence build (2.9s), verdict + qualifiers as documented
  - `.venv/bin/python -m pytest -q tests/test_tsmom_ev1_evidence.py tests/test_rlog1_research_log.py tests/test_sel_ev1_selection_evidence.py` → 34 passed
  - `.venv/bin/python scripts/build_research_log.py --check` → ok (14 entries)
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 12 passed (TSMOM renders amber mixed; zero green badges)
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.11.003

- `recorded_at_utc`: `2026-06-11T12:00:00Z`
- `scope`: `DASH-QASWEEP1 investor-readiness UI shakedown + fix`
- `intent`: `UI/display fixes only; chart + markers untouched; no safety label or honest verdict softened. Drove the whole dashboard like a user in two passes (deterministic + 1s-refresh-active with mocked endpoints, zero real network), recording console/page errors at every step. Fixed: (1) BLOCKER - the 1s market refresh destructively rebuilt every filter <select> (renderSelect/renderSelectWithoutAll) making dropdown picks take many clicks - now idempotent via data-render-key, never rebuilt under focus, value preserved; (2) Runtime Logs open log re-defaulted to latest each refresh - rows are now expandable details with state-tracked selection (latest only when nothing selected, survives re-renders); (3) console 404 noise from the control-server status probe - adaptive 10s/60s backoff + zero probes under ?disableLivePolling (explicit unavailable state; deterministic/CI loads are now console-clean); (4) 57px page overflow @1600 in all themes from the Output-slate select min-content blowout - min-width:0/width:100% on the control-grid fields; (5) 45px overflow <=1180 from stale tablet rules (3-col rail split + rigid 160/220 control-grid tracks) - rails single-column, override removed; (6) REGRESSION FOUND+FIXED: tablet/mobile stacking silently dead since DASH-IA1 (base terminal-grid rule appended after the legacy media blocks) - stacking re-asserted <=1180, verified 390/768/1180/1280 zero overflow; (7) inline-flex actions row spill - block flex. Flagged (not fixed): one native 404 per 60s probe persists on machines without the control server (not JS-suppressible) - run the control server for the demo. DASH-QA1 grew 10 -> 12 checks (refresh stability with mocked live endpoints; zero-console-error + no-overflow hygiene) - 12/12 green. Final sweep: zero issues, zero console errors. Demo screenshots + investor-readiness checklist in docs/dash_qasweep1_*. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `docs/dash_qasweep1_investor_readiness_sweep.md`
  - `docs/dash_qasweep1_investor_readiness_sweep_summary.json`
  - `docs/dash_qasweep1_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - full exploratory sweep (deterministic + mocked 1s-refresh passes) → 0 issues, 0 console/page errors
  - CI follow-up: QA check #12 exempts only the documented gitignored optional-artifact 404s (reports/paper_runtime/, reports/paper_reviews/ — absent on CI by design); verified via CI-emulation with reports/** forced to 404 → 0 non-exempt errors
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 12 passed
  - widths 390/768/1180/1280 → stacked/3-col as intended, zero horizontal overflow
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.11.002

- `recorded_at_utc`: `2026-06-11T07:00:00Z`
- `scope`: `RLOG1 Research Log: honest post-mortems, auto-joined + analytics`
- `intent`: `Display + docs/tooling only; read-only aggregation; Decision-Log backfill additive only. Must 1: machine-readable post-mortem schema — each research phase's 03_Decision_Log.md entry carries a fenced yaml research_log block (phase/date/class/outcome/why/worked/didnt/lesson/our_error/changed/evidence_summary/analytics/hardened_gate) with the honest outcome taxonomy fail|mixed|context|pass AUTHORED in the log, never inferred from a summary status string; backfilled into 12 phases (SEL-EV1, EXEC-EV1, SV2.3, SV2.2, GOAL-STRAT1/2, SOR-EV1/2/3, MF-ORIG-EV1.1, MF-ORIG-EV2, EV-AUDIT1) with honest our_error attribution (EXEC-EV1: missing concentration gate let ZEC slip through, fixed via leave-one-out; MF-ORIG-EV1.1: K-019 fee double-count corrected; SEL-EV1: null — the test caught its own overfit). Schema doc docs/research_log_schema.md. Must 2: scripts/build_research_log.py — read-only/deterministic/offline aggregator joining blocks to committed docs/*_summary.json (computed analytics: EXEC-EV1 per-symbol concentration ZEC 132%/ex-ZEC -36k/15-23 negative + top-5 table; SEL-EV1 random benchmark 2/50 + near-miss configs; SV2.3 aggregate -638k/0 survivors; GOAL-STRAT1 121/7/0; SV2.2 coverage), active lanes from current_truth.json, lessons rail from authored hardened_gate fields; emits docs/research_log.json (13 entries incl. RLOG1 itself) with a --check drift guard. Must 3: the dashboard Research Log renders the docs/dash_rlog1_prototype.html structure from research_log.json — standing strip, red verdict banner, expandable post-mortem timeline with six facets + analytics + evidence links, lessons rail, active-lanes card, boundaries footer; badges fail=red/mixed=amber/context=blue/pass=green; the naive verdict||audit_verdict||gate_status||status coloring is REMOVED so a non-positive result can never render green; theme-aware. Must 4: tests/test_rlog1_research_log.py (6 deterministic tests incl. the pinned regression that upbeat ready_for_founder_review/complete statuses keep authored non-positive outcomes) + build --check wired into the blocking CI lane; DASH-QA1 gained check #10 (>=12 post-mortems, zero green badges, SEL-EV1 renders fail, facets visible) — 10/10 green. Must 5: AGENTS.md post-task workflow now requires every research phase to author its research_log block and run the aggregator (CI drift guard enforces). Resolves K-033. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `AGENTS.md`
  - `scripts/build_research_log.py`
  - `docs/research_log.json`
  - `docs/research_log_schema.md`
  - `docs/rlog1_research_log.md`
  - `docs/rlog1_research_log_summary.json`
  - `docs/rlog1_screenshots/*`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/test_rlog1_research_log.py`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `.github/workflows/ci.yml`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/build_research_log.py --check` → ok (deterministic rebuild byte-identical)
  - `.venv/bin/python -m pytest -q tests/test_rlog1_research_log.py` → 6 passed
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 10 passed
  - three-theme in-browser exercise → zero page errors
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.11.001

- `recorded_at_utc`: `2026-06-11T00:15:00Z`
- `scope`: `DASH-PT3 Paper Trading header + layout refinements`
- `intent`: `Dashboard display/layout only; chart + markers untouched; every #paper-observation-* id preserved. Six founder refinements on the 2-tab Money Flow OS: (1) always-visible critical-state pills in the header — #top-runtime-pill (RUNTIME ACTIVE green/blinking when the already-polled local control-server status reports a run; IDLE muted; CHECKING while polling) and #top-live-pill (LIVE DISABLED · NOT APPROVED, static red); no new data source. (2) The dense status strip #paper-observation-health-banner relocated from the top to the final full-width reference band after the Testnet footer with all content/ids/lane chips/safety labels intact. (3) Global Filters now lead the body (filters -> watchlist/chart/runtime -> blotter -> daily review -> testnet -> status strip). (4) Runtime Control truncation fixed: right rail widened to minmax(300px,344px) and the right-rail overflow:hidden clip changed to visible — message, copy, output slate, and safety profile all fit; chart stays the dominant panel. (5) Watchlist widened to minmax(212px,252px). (6) OKB removed from the watchlist DISPLAY: scanner_universe rows from the runtime summary bypassed the HIDDEN_DASHBOARD_SYMBOLS filter, so paperObservationBaseScannerRows now applies isVisibleDashboardSymbol to summary rows + configured fallback; pt_rt1.py resolver policy untouched. (7) Daily Review / Anomaly Flags nested scroll removed (max-height/overflow dropped, incl. the mobile variant). Lockstep guard updates: DASH-QA1 #9 extended (pills visible, live pill reads live disabled + not approved, strip renders after the testnet footer) — 9/9 green; static-asset ordering/grid/pill asserts updated — green. Three themes zero page errors; node --check clean; cache-buster dash-pt3-header-pills-20260611; before/after screenshots in docs/dash_pt3_screenshots/. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `docs/dash_pt3_header_and_layout_refinements.md`
  - `docs/dash_pt3_header_and_layout_refinements_summary.json`
  - `docs/dash_pt3_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed
  - `.venv/bin/python -m pytest -q tests/test_dashboard_static_assets.py` → 9 passed
  - three-theme in-browser exercise → zero page errors; OKB absent from watchlist; pills render
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.007

- `recorded_at_utc`: `2026-06-10T23:30:00Z`
- `scope`: `DOC-LEAN1 changelog rotation + lean pre-task reading`
- `intent`: `Docs/tooling only; no history lost. CHANGELOG.md had grown to 800 KB / 9,257 lines / 292 entries and the AGENTS.md pre-task workflow forced every agent to read it (plus REPO_TREE 238 KB, KNOWN_ISSUES 67 KB, TODO 134 KB) before any task. Must 1: rotated the changelog — CHANGELOG.md now holds the 20 most recent entries (v2026.06.10.006..v2026.06.08.002, 45 KB) plus the archive pointer; new CHANGELOG_ARCHIVE.md holds the older 272 entries verbatim (v2026.06.08.001..v2026.04.06.017). Verified programmatically at rotation time: 20+272=292 headings, no entry dropped or duplicated, recent+archive version order equals the original, and the concatenated entry text reproduces the original byte-for-byte. Must 2: AGENTS.md Changelog Rules now define the recent rolling window + full archive as BOTH canonical (single complete history, not competing changelogs), with the ~25-entry rotation trigger handled in the post-task update; new entries are still written to CHANGELOG.md. Must 3: AGENTS.md Pre-Task Workflow rewritten to the lean current-state set read every task (AGENTS.md, CURRENT_TRUTH.md, 01_Current_Phase.md, the recent CHANGELOG.md, 05_Agent_Coordination.md, task-relevant component docs); REPO_TREE / KNOWN_ISSUES / TODO / CHANGELOG_ARCHIVE / Command Center / Project Memory demoted to consult-on-demand. The post-task UPDATE list is unchanged — reads trimmed, writes untouched. Must 4: tests/test_operational_docs.py updated and green (20 passed): archive added to existence + stale-draft guards; archive-pointer + <=25-entry rolling cap CI-enforced; new lossless-rotation-shape test (>=272 archived, no overlap/duplicates, newest-first continuity). No runtime, strategy, code-behavior, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `CHANGELOG_ARCHIVE.md`
  - `AGENTS.md`
  - `tests/test_operational_docs.py`
  - `docs/doc_lean1_changelog_rotation_and_lean_reading.md`
  - `docs/doc_lean1_changelog_rotation_and_lean_reading_summary.json`
  - `REPO_TREE.md`
  - `TODO.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - rotation check → 20 + 272 = 292 entries, none dropped/duplicated, entry text byte-for-byte verbatim across the two files
  - `.venv/bin/python -m pytest -q tests/test_operational_docs.py` → 20 passed
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_operational_docs.py` → passed

## v2026.06.10.006

- `recorded_at_utc`: `2026-06-10T22:30:00Z`
- `scope`: `DASH-IA1 consolidate the dashboard to 2 tabs (structural)`
- `intent`: `Dashboard display only. The founder decision: Money Flow OS is two surfaces — Paper Trading (the live desk, now the default tab) and Research Log (institutional memory of what has been tested). DASH-IA1 is the structural cut: nav collapsed from five tabs to two; Historical Replay, The Lab (evidence-lab), and Strategy retired (tabs + panels + view-router entries + ALL render/data-loading code and CSS exclusive to those views, plus the old Evidence renderers whose markup was replaced); Evidence renamed to Research Log with a minimal data-driven placeholder (phase/date/verdict rows read from up to 12 committed docs/*_summary.json evidence summaries with graceful omission; full post-mortem view lands in RLOG1). Monolith reduction: evidence-dashboard.js 12,004 -> 6,753 lines (-5,251, -43.7%), CSS 4,448 -> 3,706, index.html 1,088 -> 620. NOTHING deleted from disk: all SOR-EV/MF-ORIG/SV2.x evidence packs, replay JSON, builder scripts, and docs remain as reference; hidden non-nav UAT legacy panels untouched. Must 1b founder layout notes implemented: Global Filters is a full-width bar directly under the status strip (no longer inside the left rail); skinnier left (Watchlist) and right (Runtime Control) rails so the center chart dominates (prototype proportions); Testnet Order Transport relocated to a full-width footer card below Daily Review with all fields/ids/safety labels preserved; product renamed to Money Flow OS (title, top-bar brand, DESIGN.md). The Paper Trading chart and its markers are untouched. Notable preservation catches during the cut: renderSelectWithoutAll, the paper chart pane constants, and historicalConstantRows were defined inside retired-view code regions but used by Paper Trading — restored next to their surviving callers. DASH-QA1 updated in lockstep (still 9 checks): default-tab check now asserts Paper Trading default; check #7 relocated to assert the 3 current_truth active lanes in the Paper Trading status strip; new retired-tabs-absent + nav-exactly-two assertions; reflow assertions (filter bar not in left rail, testnet footer not in right rail); #9 also asserts footer labels. tests/test_dashboard_static_assets.py rewritten in lockstep with the same safety intent. Verification: DASH-QA1 9/9 green (multiple runs), 96 blocking-lane tests green, all three themes exercised with zero page errors, node --check clean, cache-buster dash-ia1-two-tabs-20260610, before/after screenshots in docs/dash_ia1_screenshots/. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/index.html`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/DESIGN.md`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `tests/test_dashboard_static_assets.py`
  - `docs/dash_ia1_two_tab_consolidation.md`
  - `docs/dash_ia1_two_tab_consolidation_summary.json`
  - `docs/dash_ia1_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (multiple runs)
  - blocking-lane battery (safety invariants, truth registry/consistency, week2 slate, static assets, operational docs, obs daily review) → 96 passed
  - three-theme in-browser exercise → zero page errors
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.005

- `recorded_at_utc`: `2026-06-10T21:00:00Z`
- `scope`: `DASH-PT2 Paper Trading bolder exchange reskin`
- `intent`: `Dashboard display only. Elevates the existing DASH-PT1.2/1.3 Paper Trading terminal in place to a bolder, denser, color-coded exchange aesthetic (systematic-fund operator terminal), CSS-led, matching the founder prototype docs/dash_pt2_prototype.html. Must 1: theme-aware DASH-PT2 token layer in evidence-dashboard.css across dark/light/red-zone — per-lane accents mapped to the current_truth.json active lanes (baseline blue --lane-baseline, diagnostic comparator violet --lane-diagnostic, MF-ORIG candidate amber --lane-candidate), crisp --accent-live positive/health accent (+ --accent-live-deep/-ink), --accent-testnet, terminal chip/row-line tokens; the --color-chart-* tokens are untouched so the TradingView palette and theme-rebuild behavior are unchanged. Must 2: reskinned the top health banner into a dense 1px-grid status strip with state-colored cells and lane chips; denser cockpit filters + watchlist with live-accent selected row; bolder chart header (chart internals/bounded heights untouched); accent-gradient Start Run + accent runtime message; testnet-accented transport panel; blotter with accent-underlined tabs, dense sticky-header monospace tables, td.positive/td.negative PnL coloring, translucent terminal status tags; restyled daily review grid + anomaly flags; shared chrome intentionally restyled (top strip edge, brand glow, accent-gradient active nav tab) — no other tab body restyled. Must 3: zero behavior change — only display-only JS markup (paperObservationLaneChip helper + four status-strip state classes); every #paper-observation-* id and DASH-QA1-selected structure preserved verbatim (no selector updates needed); all three themes verified including the chart. Must 4: DASH-QA1 9/9 browser checks green (run twice); before/after Playwright screenshots committed under docs/dash_pt2_screenshots/ (desktop+mobile dark, desktop light/red-zone) via new scripts/capture_dash_pt2_screenshots.py; cache-buster bumped to dash-pt2-bold-terminal-20260610 on CSS+JS. No runtime, strategy, data-source, order, testnet, or approval change.`
- `affected_files`:
  - `CHANGELOG.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `apps/dashboard/evidence-dashboard.css`
  - `apps/dashboard/evidence-dashboard.js`
  - `apps/dashboard/index.html`
  - `apps/dashboard/DESIGN.md`
  - `scripts/capture_dash_pt2_screenshots.py`
  - `docs/dash_pt2_prototype.html`
  - `docs/dash_pt2_bolder_exchange_reskin.md`
  - `docs/dash_pt2_bolder_exchange_reskin_summary.json`
  - `docs/dash_pt2_screenshots/*`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `.venv/bin/python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (two consecutive runs)
  - `.venv/bin/python scripts/capture_dash_pt2_screenshots.py --label before|after` → 5+5 screenshots, all three themes inspected
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.004

- `recorded_at_utc`: `2026-06-10T20:00:00Z`
- `scope`: `SEL-EV1 cross-sectional breakout selection evidence + strategy-type routing seam`
- `intent`: `Research/evidence only. Tests the founder's pivot from approach a (one universal rule per symbol — failed via ZEC concentration) to approach b (cross-sectional selection: each period rank the 23-symbol universe on breakout/relative strength, hold the strongest name(s), rotate as leadership changes). Supersedes the planned GOAL-STRAT3 breadth gate (wrong lens for a strategy designed to concentrate; the ZEC lesson is reframed as a rotation/diversity check; the breadth-gate idea is deferred). Must 0 adds a strategy_type routing seam (services/strategy_validation/strategy_types.py): per_symbol routes to the existing goal_strat1 simulator + breadth gate, cross_sectional_selection routes to the new SEL-EV1 portfolio simulator + random-benchmark gate; the gates can never cross-apply (StrategyTypeRoutingError) and the three Week 2 lanes are tagged per_symbol with behavior/results unchanged (byte-identical golden regression test). services/strategy_validation/sel_ev1.py adds a strict point-in-time cross-sectional simulator (selection at t uses only data <= t; next-candle-open fills; ATR(14)x2.8 trail; fixed-fraction sizing top-1 50% / top-3 30% per name — never full-equity-on-one; EXEC-EV1 depth-aware friction on every fill), bounded signals (donchian_breakout_strength, vol_adjusted_relative_momentum; lookbacks 20/40; top-1/top-3; 4h/1d = 16 configs), a matched-cadence seeded random-selection benchmark, equal-weight buy-and-hold + naive past-return baselines, rotation/diversity metrics, chronological 70/30 + anchored walk-forward thirds OOS with train-only parameter choice, and late-entry (+1/+2 candle) sensitivity. VERDICT: no_selection_skill_demonstrated. The train-chosen config (vol_adjusted_relative_momentum lb40 top3 1d, train net +54292) lost -10460 OOS post-conservative-friction and beat only 2 of 50 random seeds (empirical p 0.96 — worse than random); equal-weight buy-hold OOS -2147; in-sample positivity did not carry out-of-sample. Diversity itself was healthy (23 distinct symbols, max time share 0.13, no single-name bet). Late-entry decay is severe on the full period (+0 net 43832 -> +1 17366 -> +2 12334), confirming breakout selection is acutely timing-sensitive (relevant to RT-HISTSEED1). 15 deterministic offline tests (routing seam, byte-identical per-symbol regression, no-lookahead incl. a synthetic leak that must be caught, seed reproducibility, always-one-symbol diversity flag, friction-on-fills, chronological splits) wired into the blocking CI lane. No runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `services/strategy_validation/strategy_types.py`
  - `services/strategy_validation/sel_ev1.py`
  - `scripts/run_sel_ev1_selection_evidence.py`
  - `tests/test_sel_ev1_selection_evidence.py`
  - `tests/fixtures/sel_ev1/goal_strat1_per_symbol_golden.json`
  - `docs/sel_ev1_selection_evidence.md`
  - `docs/sel_ev1_selection_evidence_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_sel_ev1_selection_evidence.py` → 16 configs + 50 random seeds + baselines, verdict `no_selection_skill_demonstrated`
  - `.venv/bin/python -m pytest -q tests/test_sel_ev1_selection_evidence.py` → 15 passed
  - `.venv/bin/python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → passed

## v2026.06.10.003

- `recorded_at_utc`: `2026-06-10T16:00:00Z`
- `scope`: `EXEC-EV1 depth-aware modeled execution-friction evidence layer`
- `intent`: `Research/evidence only. Adds a depth-aware modeled friction layer on top of SV2.3's fee/slippage/adverse-gap terms and re-scores the three Week 2 lanes. New model services/execution_quality/exec_ev1.py adds three terms: per-symbol liquidity-tier half-spread, size-aware square-root market impact (participation = notional / candle-dollar-volume liquidity proxy), and a fill-probability unfilled-chase penalty. EXEC-EV1 cost is always >= the SV2.3 parent cost, so EXEC-EV1 net PnL <= SV2.3 net PnL per lane/scenario (verified: 0 violations across 621 rows). MODELED, NOT REAL, DEPTH: liquidity is derived from historical candle volume, not real historical order-book depth (which does not exist; Hyperliquid public l2Book is a current snapshot only) — every output is labeled an assumption layer. Re-score verdicts: mf_orig_1d_stage2_breakout_resistance_full_equity survives base + conservative depth-aware friction but fails stress; money_flow_v1_2_baseline and avoid_low_rolling_range_20 fail all (already negative under SV2.3). Also adds a late-entry / entry-timing cost metric (adverse move from signal candle to fills 0/1/2 candles late): mf_orig cost rises with lateness (~+1.2 -> +15 -> +37 bps), signaling its edge decays at the signal and that historical-position seeding would erode it; the two failing lanes show negative late-entry cost (poor entries). scripts/run_exec_ev1_execution_quality.py reads SV2.2 candles from disk and performs no network I/O. tests/test_exec_ev1_execution_quality.py (14 deterministic tests) wired into the blocking CI lane. K-001 noted partially addressed (modeled, not real depth). Future phase RT-HISTSEED1 recorded. No runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `services/execution_quality/__init__.py`
  - `services/execution_quality/exec_ev1.py`
  - `scripts/run_exec_ev1_execution_quality.py`
  - `tests/test_exec_ev1_execution_quality.py`
  - `docs/exec_ev1_execution_quality_evidence.md`
  - `docs/exec_ev1_execution_quality_evidence_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `.venv/bin/python scripts/run_exec_ev1_execution_quality.py` → 621 result rows, 0 EXEC-EV1>SV2.3 violations
  - `.venv/bin/python -m pytest -q tests/test_exec_ev1_execution_quality.py` → 14 passed
  - `.venv/bin/python scripts/check_trading_safety_text.py` → OK
  - `.venv/bin/python scripts/check_secret_hygiene.py` → OK
  - `ruff check + format --check` on EXEC-EV1 modules → clean

---

## v2026.06.10.002

- `recorded_at_utc`: `2026-06-10T13:00:00Z`
- `scope`: `CI-CLEAN1 close CI enforcement loop + reproducible installs`
- `intent`: `CI/build config only. (1) Promoted dashboard-qa to blocking by removing continue-on-error=true (lane is consistently green on Ubuntu since DASH-QA1.1). (2) Split the single informational job into two independent jobs typecheck (mypy) and full-tests (pytest -q -m "not browser"), both continue-on-error=true, so a mypy failure no longer hides the full pytest signal. (3) Added pip-tools to dev extras, generated a 226-line requirements-dev.lock, and switched every CI job to install via "pip install -r requirements-dev.lock && pip install -e . --no-deps" for reproducible dependency resolution. KNOWN_ISSUES K-031 added for the strict-mypy informational debt with explicit promotion criterion (do not silence mypy or relax strict). No runtime, strategy, order, testnet, slate, approval, dashboard-behavior, or test-logic changes. mypy strict mode not silenced. browser marker not folded into the main test run.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `pyproject.toml`
  - `requirements-dev.lock`
  - `.github/workflows/ci.yml`
  - `docs/ci_clean1_ci_enforcement_close_and_locked_deps.md`
  - `docs/ci_clean1_ci_enforcement_close_and_locked_deps_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml` → 226 lines
  - `pip install -r requirements-dev.lock && pip install -e . --no-deps` → clean
  - `python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → 66 passed
  - `python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed
  - `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → YAML OK

---

## v2026.06.10.001

- `recorded_at_utc`: `2026-06-10T10:00:00Z`
- `scope`: `DASH-QA1 dashboard browser smoke + chart-stability regression`
- `intent`: `Added a deterministic Playwright-based browser-smoke suite for the Paper Trading dashboard that pins documented regressions: tab routing, terminal layout, chart growth stability (autoSize feedback-loop P0), tab-state persistence, blotter-tab refresh stability, Audit-tab absence, three-active-lane strategy view, 15m-paused timeframe filter, and synthetic/testnet/no-live boundary labels. Suite serves the repo root over a localhost HTTP server, opens index.html?disableLivePolling=true in headless Chromium, and sources expected lane/timeframe values from current_truth.json (TRUTH1). pyproject.toml adds pytest-playwright to dev extras, registers a browser marker, and sets addopts="-m 'not browser'" so the suite is opt-in. CI gains a dedicated dashboard-qa job that runs the suite; lane starts informational (continue-on-error) and will be promoted to blocking after 3 consecutive green CI runs. KNOWN_ISSUES K-030 notes the Chromium binary requirement. No dashboard behavior changed (no data-testid hooks added), no runtime/strategy/order/approval state changed.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `pyproject.toml`
  - `.github/workflows/ci.yml`
  - `tests/dashboard_qa/__init__.py`
  - `tests/dashboard_qa/conftest.py`
  - `tests/dashboard_qa/test_dashboard_smoke.py`
  - `docs/dash_qa1_dashboard_browser_smoke.md`
  - `docs/dash_qa1_dashboard_browser_smoke_summary.json`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `playwright install chromium`
  - `python -m pytest -m browser tests/dashboard_qa/ -q` → 9 passed (3 consecutive runs: 24.4s, 23.0s, 22.9s)
  - `python -m pytest --collect-only tests/dashboard_qa/` → 9 deselected (default discovery excludes browser marker)
  - `python -m pytest -q tests/test_secret_hygiene.py tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py` → 66 passed (pre-push safety check)

---

## v2026.06.09.003

- `recorded_at_utc`: `2026-06-09T13:00:00Z`
- `scope`: `CI-SAFE1.1 CI install fix + blocking-lane coverage`
- `intent`: `CI plumbing fix only. Replaced 'pip install -r requirements.txt' with 'pip install -e ".[dev]"' in both the blocking and informational jobs so CI installs from pyproject.toml (the canonical source — there is no requirements.txt). Restored four fast guard tests (test_pt_rt1_6_week2_slate.py, test_dashboard_static_assets.py, test_operational_docs.py, test_obs_os1_daily_review.py) to the blocking lane. No safety logic, scanner, registry, runtime, strategy, order, testnet eligibility, Week 2 slate, or approval state changed.`
- `affected_files`:
  - `.github/workflows/ci.yml`
  - `CHANGELOG.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `grep -rn "requirements.txt" .github/` → no matches
  - `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` → YAML OK
  - `node --check apps/dashboard/evidence-dashboard.js` → OK
  - `python -m compileall -q core services apps tests scripts` → OK
  - `python scripts/export_current_truth.py --check` → OK
  - `python -m pytest -q tests/test_trading_safety_invariants.py tests/test_current_truth_consistency.py tests/test_current_truth_registry.py tests/test_pt_rt1_6_week2_slate.py tests/test_dashboard_static_assets.py tests/test_operational_docs.py tests/test_obs_os1_daily_review.py` → 96 passed
  - `python scripts/check_trading_safety_text.py && pytest tests/test_trading_safety_text_guards.py` → 12 passed
  - `python scripts/check_secret_hygiene.py && pytest tests/test_secret_hygiene.py` → 12 passed
  - `python -m pytest -q tests/test_review_bundle_hygiene.py` → 39 passed
  - `ruff check + format --check on CI-SAFE1 modules` → clean

---

## v2026.06.09.002

- `recorded_at_utc`: `2026-06-09T12:00:00Z`
- `scope`: `CI-SAFE1 CI Gate + Trading Safety Invariants`
- `intent`: `Added a GitHub Actions CI workflow and interlocking safety guards that make trading-safety regression visually impossible to merge. Blocking lane: JS syntax (node --check), Python compile (compileall), registry --check, trading safety invariants, registry consistency, trading-safety text guards, secret hygiene scan, review bundle hygiene, ruff on CI-SAFE1 modules. Informational: mypy strict, full pytest. KNOWN_ISSUES K-029 added for lightweight secret scan caveat. No runtime behavior changed, no orders submitted, no private endpoints used, no strategy production-approved.`
- `affected_files`:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `REPO_TREE.md`
  - `TODO.md`
  - `.github/workflows/ci.yml`
  - `scripts/check_trading_safety_text.py`
  - `scripts/check_secret_hygiene.py`
  - `tests/test_trading_safety_invariants.py`
  - `tests/test_trading_safety_text_guards.py`
  - `tests/test_secret_hygiene.py`
  - `tests/test_review_bundle_hygiene.py`
  - `tests/test_current_truth_consistency.py`
  - `docs/ci_safe1_ci_gate_and_trading_safety_invariants.md`
  - `money-flow/01_Current_Phase.md`
  - `money-flow/03_Decision_Log.md`
  - `money-flow/05_Agent_Coordination.md`
- `validation_performed`:
  - `node --check apps/dashboard/evidence-dashboard.js`
  - `python -m compileall -q core services apps tests scripts`
  - `python scripts/export_current_truth.py --check`
  - `python scripts/check_trading_safety_text.py`
  - `python scripts/check_secret_hygiene.py`
  - `python -m pytest -q tests/test_trading_safety_invariants.py tests/test_trading_safety_text_guards.py tests/test_secret_hygiene.py tests/test_review_bundle_hygiene.py tests/test_current_truth_consistency.py tests/test_current_truth_registry.py (123 passed)`
  - `ruff check + format --check on CI-SAFE1 modules (clean)`

---
