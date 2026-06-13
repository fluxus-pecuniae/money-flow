# Decision Log

Append entries only. Do not rewrite prior decisions except to add a dated correction.

## 2026-06-13T01:00:00Z - MF-REPLAY1 - Founder Visual Backtesting: Range-Accurate Replay of the PT-RT2 Lanes (Replay ≠ Evidence)

- `decision`: Give the founder visual backtesting — replay the two committed PT-RT2 lanes over the full DATA1 history with selectable ranges (all-time / calendar year / custom dates) and an accurate "started 10k → ended X" answer, on the dashboard's re-introduced Historical Replay tab. Replay is hypothetical context for founder judgment, NOT new evidence and NOT a validated strategy; it never feeds or backfills the live synthetic ledgers. Pre-registered range semantics (chosen before the UI): fresh-start FLAT at 10,000 USDC on the range's first closed candle taking only in-range entries (pre-range positions ignored until next fresh entry); indicator warm-up uses pre-range history (warm-up = data, fresh-start = position state); closed candles only; one code path (the committed `moneyflow_signal1.signal_states` surface + the PT-RT2 lane semantics, never a parallel calculator). Durable data foundation: the snapshot home moved from `/tmp` (cleared by macOS) to ignored `var/data1/raw_series/` with sha256 unchanged; append-only refresh + CSV export added. 7-major universe (the characterization universe).
- `result`: Range-accurate, deterministic-Decimal, no-lookahead-verified replay; honest numbers reported (all-time, every calendar year, and the founder range 2021-06-19→2025-05-31 for both lanes) — the regime overlay's defensive mechanic replays exactly where REGIME2 said it would (2022 bear: gated −23% / 3.0× gross vs baseline −97% / 7.0× gross; flat in 2020 when risk-off), at a whipsaw cost in chop. Accuracy pinned by `tests/test_mf_replay1.py` incl. the live-ledger equivalence test (replay reproduces the live PT-RT2 decision path + ledger arithmetic exactly on a non-overlapping single-symbol window). Dashboard Historical Replay tab re-introduced: range picker / lane selector / equity curve + result card (with max_gross_exposure_x / max_concurrent_positions) / candle+markers chart / dashed live-observation-start separator / characterization note. Serving: precomputed pack for all-time + years, `/api/mf-replay1/range` for custom dates (same engine).
- `honesty_notes`: A green range is window placement, not alpha — committed lesson (TSMOM-EV1's OOS window was absolutely negative; MONEYFLOW-SIGNAL1's was positive; same mechanic) rendered on the surface next to every result. The committed verdicts travel (`defensive_trend_mechanic_not_validated_alpha`; `source_faithful_but_underperformed`; regime overlay informational-not-validated-control). Re-introducing the Historical Replay tab (retired at DASH-IA1) was a deliberate supersede; the two-tab guard tests were updated at the same strictness, never weakened.
- `k037_founder_decision_flag`: The replay revealed (K-037) that full-equity sizing PER concurrent symbol position levers the committed PT-RT2 lanes up to ~7.8× gross when all 7 majors are long (all-time book draws down ~99% in 2022); the live overlap accounting can also drop realized PnL vs the additive ledger. This is a property of the already-merged PT-RT2 lanes, SURFACED here (exposure fields on every range; equivalence pinned on non-overlapping sequences) and NOT silently fixed. Open founder decision, separately scoped: is full-equity-per-position the intended paper-lane sizing? This phase changed no live sizing or live trajectories.
- `scope`: `services/paper_runtime/mf_replay1.py`, `scripts/refresh_data1_snapshot.py`, `scripts/export_data1_csv.py`, `scripts/build_mf_replay1_dashboard_data.py`, `scripts/run_dashboard_control_server.py` (range endpoint), `services/market_data/data1_multi_venue.py` + `scripts/fetch_data1_multi_venue_snapshot.py` + `docs/data1_*` (durable home), `apps/dashboard/*` (Historical Replay tab), `tests/test_mf_replay1.py`, dashboard guard tests, `KNOWN_ISSUES.md` (K-037), `docs/mf_replay1_*`, Obsidian notes.
- `boundaries`: Replay-only — no live ledger writes, no orders, no private/signed endpoints, no approval surface, no production strategy change. Live synthetic ledgers never backfilled/recomputed/touched.
- `follow_up_implications`: The founder can now visually backtest the committed lanes over any range. A K-037 sizing decision (full-equity-per-position vs fractional) is the natural next founder call — separately scoped because it changes live paper trajectories. The open strategy hunts are unchanged and characterized-not-started: stat-arb/cointegration (the one untested systematic-alpha avenue) and funding carry via institutional sub-candle atomic execution.

```yaml
research_log:
  phase: MF-REPLAY1
  date: 2026-06-13
  class: source_reconstruction
  outcome: context
  badge: founder visual backtesting (replay != evidence)
  title: Range-Accurate Replay of the PT-RT2 Lanes
  finding: >-
    The founder can replay the two committed PT-RT2 lanes over any range
    (all-time / year / custom) with an accurate fresh-start 10k->end answer,
    one code path through the committed signal surface, no-lookahead and
    live-ledger-equivalence pinned. Honest numbers: the regime overlay's
    defensive mechanic replays exactly where REGIME2 said it would (2022
    bear gated -23% vs baseline -97%); a green range is window placement,
    not alpha.
  why: >-
    Replay extends founder visibility into the committed lanes - it is
    hypothetical context for judgment, never new evidence and never a
    validated strategy; it cannot and does not upgrade any verdict.
  worked: >-
    The single-code-path design (replay consumes the same signal surface +
    lane semantics) made the live-ledger equivalence provable; pinning it
    on a non-overlapping sequence surfaced the K-037 overlap-accounting
    boundary instead of hiding it.
  didnt: >-
    The replay exposed that full-equity-per-position sizing levers the
    committed lanes up to ~7.8x gross (~99% drawdowns) - a real property of
    the merged PT-RT2 lanes, surfaced as a founder decision, not patched.
  lesson: >-
    Replay extends visibility, never upgrades a verdict - and a faithful
    replay surfaces the accounting truths (leverage, overlap) the live
    summary glosses.
  our_error: null
  changed: >-
    The DATA1 snapshot home is now durable (var/data1, off /tmp); the
    dashboard has a Historical Replay tab again; K-037 sizing is flagged
    for a founder decision.
  hardened_gate: replay is hypothetical, never feeds the live ledgers
  evidence_summary: docs/mf_replay1_founder_visual_backtesting_summary.json
```

## 2026-06-12T14:30:00Z - PT-RT2 - Fresh Paper Slate: The Trusted Signal Goes Under Live Observation, Verdicts Intact

- `decision`: Execute the three founder decisions: (1) a TWO-LANE fresh slate — `mf_source_faithful_baseline` (Control/Baseline) and `mf_source_faithful_regime_gated` (Informational Overlay Observation), both consuming the committed MONEYFLOW-SIGNAL1 surface with the characterization's exposure semantics (no re-implementation, no new rule variants, no tuning); (2) ARCHIVE the Week 2 slate, never delete — the 3 active lanes join the 7 archived (10 archived), synthetic ledgers and history untouched; (3) PAPER-ONLY first — NO lane is testnet eligible (the old baseline's eligibility ended with its active status; `pt_rt1_6_lane_testnet_eligible` now returns False for everything; the runtime refuses every testnet flag under the PT-RT2 scope); testnet for the new slate is a separate future founder decision. Universe is the 7 DATA1 majors (the characterization universe); HYPE/SUI stay configured but untraded (short histories). Timeframe is 1d ONLY — the committed surface is daily (page-cited); running it on other timeframes would be a new rule variant. Fresh 10,000 USDC ledgers at the phase's first closed candle in the new scope `pt_rt2_mf_signal_observation`; no backfill.
- `result`: The lanes flow through `moneyflow_signal1.signal_states` via a dedicated decision path in `pt_rt1.py` (drift-pinned: the lane decision equals the surface's own decision); the regime overlay builds per cycle through `strategy_types.resolve_regime_filter()` from the runtime's own closed daily candles, carries REGIME2's verdict verbatim, and on unavailability the gated lane HOLDS its prior state and flags it — never a silent risk-on/risk-off default (the signal's own exit still closes; exposure = signal AND risk_on, the characterization's gated-twin semantics). Live cycle sample 2026-06-12: regime RISK_OFF (config `regime1_lb90_br6_btc_required_1d`), both lanes flat on all 7 majors (`blocked_not_stage_2_markup`) — coherent with the MONEYFLOW-SIGNAL1 CLI picture. CURRENT_TRUTH regenerated (scope, 2 active / 10 archived, testnet table empty, 1d-only, observed universe 7); the registry/slate/invariants/static-assets/browser-smoke tests were superseded at the same strictness, never weakened. The MONEYFLOW-SIGNAL1 reviewer fixup (offline-replay timestamp normalization + overlay-availability assertion) landed as the first commit of this branch.
- `boundaries`: Paper only — synthetic ledgers, public closed candles as signal truth, no testnet orders for any lane, no live, no approval surface, no production Money Flow rule change. The committed verdicts travel on every lane surface: `defensive_trend_mechanic_not_validated_alpha` standalone, `source_faithful_but_underperformed` trade-level, `regime_filter_does_not_reduce_drawdown_oos` for the overlay (informational risk context, not a validated control). Watching it live upgrades none of them.
- `follow_up_implications`: The founder may start the PT-RT2 run from the dashboard control surface (the safe command is pinned: `--pt-rt2`, candle-close-only, fresh-signal gate, no testnet pathway). Any testnet decision for this slate, any timeframe widening, or any re-reading of the committed characterization is a NEW founder decision/phase. The open strategy hunts are unchanged: stat-arb/cointegration; institutional sub-candle atomic execution for carry.

```yaml
research_log:
  phase: PT-RT2
  date: 2026-06-12
  class: source_reconstruction
  outcome: context
  badge: trusted signal under live observation
  title: Fresh Paper Slate - Source-Faithful Signal Baseline + Regime-Gated Twin
  finding: >-
    The trusted MONEYFLOW-SIGNAL1 surface went under live paper observation
    as a fresh two-lane slate (baseline + regime-gated twin), with the Week 2
    slate archived intact, fresh 10k ledgers, the 7-major characterization
    universe, daily-only cadence, and NO testnet eligibility anywhere. Every
    payload carries the committed verdicts; the first live cycle was
    coherent with the committed picture (RISK_OFF, all majors stage-4,
    both lanes flat).
  why: >-
    The founder wants to watch the characterized signal tick on real
    candles. Observation is for trust and operational learning - the
    characterization already said what the signal is (defensive trend
    mechanic, not validated alpha) and live watching cannot upgrade that.
  worked: >-
    Reuse pins - the lane decision path consumes the committed surface
    directly and tests assert it cannot drift; the honest gate-unavailability
    semantics (hold prior state, flag it, never default) fell out naturally
    from the characterization's AND semantics.
  didnt: >-
    Nothing failed in-phase; the one inherited defect (offline-replay
    timestamps silently killing the regime overlay) was the reviewer fixup
    applied as this branch's first commit.
  lesson: >-
    Observation extends trust, never upgrades a verdict - the slate's
    payloads say so on every surface.
  our_error: null
  changed: >-
    The active paper surface is now the source-faithful signal itself
    (daily, 7 majors, paper-only); Week 2 is archived history; no lane can
    touch testnet without a new founder decision.
  hardened_gate: no testnet pathway exists under the PT-RT2 scope
  evidence_summary: docs/pt_rt2_fresh_mf_signal_observation_slate_summary.json
```

## 2026-06-12T12:30:00Z - MONEYFLOW-SIGNAL1 - The Namesake Ships As A Trusted Signal Surface, Not An Alpha Claim

- `decision`: Close the loop to the project's namesake by delivering a source-faithful, auditable Money Flow signal surface — NOT an alpha hunt. Pin the rules to the actual Gerald Peters PDF (found in the repo at `money-flow/90 Reference/`, sha256-pinned, read directly — an upgrade over MF-ORIG-EV1's prompt-summary basis), reuse the MF-ORIG-EV1 reconstruction primitives and the production indicator implementations unchanged (no re-derived lookalike), emit every intermediate term on closed candles only (`scripts/run_moneyflow_signal.py`), overlay the REGIME filter as informational risk context with its honest-FAIL verdict carried on every state, and characterize the signal honestly (standalone OOS post-friction vs buy-and-hold and random; alone vs regime-gated).
- `result`: Fidelity: every reused rule verified against the printed text with page citations (p.37 5/20 crossover = the basic buy/sell signal; p.150 exit hierarchy incl. the quarter-trim; p.127/p.140 RSI rules; p.146 Stage-2 entry; p.125 1% risk; p.142 daily/fractal; p.70 MACD-for-TSI now SOURCE-CONFIRMED, upgrading MF-ORIG's limitation); interpretation choices recorded, never silently picked; hand-computed fixtures pin the indicator arithmetic. Characterization: the pre-stated green-is-a-red-flag rule FIRED (exposure book OOS Sharpe 0.71 vs buy-and-hold 0.05) and the re-audit traced it honestly — the coin-flip random bar was churn-unfair (replaced with persistence-matched randoms, MF at ~p93 of 30 seeds) and the green is the KNOWN defensive trend mechanic (OOS dd 27% vs 72%, but MF gives up the rising third: +404% vs always-long's +1135%) — final label `defensive_trend_mechanic_not_validated_alpha`, consistent with the committed TSMOM-EV1/TREND-SUITE1 'defensive, not profitable' verdicts on this universe; the trade-level namesake result (`source_faithful_but_underperformed`, MF-ORIG-EV1.1/EV2) stands. Regime overlay: cuts OOS drawdown a further ~6-8% of the ungated book at a ~6pp OOS return cost, labeled informational, never a validated control. Live CLI sample 2026-06-12: all 7 majors stage_4_markdown / flat; regime RISK_OFF.
- `honesty_notes`: the re-audit corrected the benchmark (a methodology artifact) and contextualized the green against committed priors — it did NOT keep adding screens until the result failed; the labeling rule is two-sided and pre-stated in the runner, with `unexpected_return_prediction_signature_re_audit` reserved for a green that survives everything (it did not: no return-prediction signature).
- `scope`: `services/strategy_validation/moneyflow_signal1.py`, `scripts/run_moneyflow_signal.py`, `scripts/run_moneyflow_signal1_evidence.py`, `docs/moneyflow_signal1_*`, `tests/test_moneyflow_signal1.py`, CI fast lane, `.gitignore` (`reports/moneyflow_signal1/`), operational docs, Obsidian notes.
- `boundaries`: Signal only — no orders, no private/signed endpoints, no testnet/live, no approval surface, no runtime change, no production Money Flow rule change; the regime overlay is informational risk context, not a validated control; nothing predicts or guarantees profit.
- `follow_up_implications`: The namesake loop is CLOSED — the founder has a trusted, source-faithful Money Flow signal on real candles with the regime context attached. The remaining open strategy-hunt threads are unchanged and characterized, not started: stat-arb/cointegration (the one untested systematic-alpha avenue) and funding carry via institutional sub-candle atomic execution. Any future alpha claim from this signal family would need a dedicated pre-registered confirmatory phase; the defensive texture belongs to the risk-tool lane (REGIME/TREND-OVERLAY), not to a return-prediction claim.

```yaml
research_log:
  phase: MONEYFLOW-SIGNAL1
  date: 2026-06-12
  class: source_reconstruction
  outcome: context
  badge: namesake loop closed
  title: Source-Faithful Money Flow Signal Surface + Regime Overlay
  finding: >-
    The namesake ships as a trusted signal surface: rules pinned to the
    actual Peters PDF (sha256-pinned, page-cited, read directly this
    phase), MF-ORIG primitives reused unchanged, every intermediate term
    auditable on closed candles, regime overlay attached with its honest
    FAIL verdict. Characterization re-confirmed there is nothing to hunt:
    the exposure book's green vs buy-and-hold is the known defensive
    trend mechanic (cuts the bear, gives up the bull), not validated
    alpha; the trade-level underperformance result stands.
  why: >-
    Directional Money Flow already failed its alpha tests
    (MF-ORIG-EV1.1/EV2, STRAT-DISC1), so the deliverable was redefined as
    fidelity + trust: the founder can look at the signal and KNOW it is
    the documented system, see exactly what it does, and see it inside
    the regime risk context.
  worked: >-
    Reading the actual PDF (the prior phase never had it) - citations now
    quote the source and one MF-ORIG limitation (TSI deferred) turned out
    to be source-sanctioned; the pre-stated green-is-a-red-flag rule -
    it fired, caught a churn-unfair random benchmark, and forced the
    honest defensive-mechanic reading instead of a quiet green.
  didnt: >-
    The naive coin-flip random benchmark at daily decisions - it burns
    ~half the book in friction daily and flatters anything persistent;
    replaced with persistence-matched randoms (recorded, both reported).
  lesson: >-
    Fidelity and trust are the deliverable when alpha is known-absent -
    and a characterization that LOOKS green must be traced to its
    mechanic before it is allowed to mean anything.
  our_error: null
  changed: >-
    The namesake loop is closed; future strategy hunting points at the
    untested avenues (stat-arb/cointegration; institutional atomic
    execution for carry), not at re-tuning Money Flow.
  hardened_gate: green results trigger re-audit, not celebration
  evidence_summary: docs/moneyflow_signal1_source_faithful_signal_surface_evidence_summary.json
```

## 2026-06-12T09:00:00Z - REGIME2 - The Criterion Fix Cleared Every Endpoint Bar; The Selection Process Failed Its Own Walk-Forward

- `decision`: Execute the pre-registered protocol (see the PRE-REGISTRATION entry below, committed to git before the selection ran): REGIME1's exact 18-config grid unwidened, selection on lowest gated TRAIN max drawdown with the whipsaw tie-break (ties within 2.0pp -> fewest train flips -> config_id), all REGIME1 bars held unchanged plus the pre-stated 25pp return-retention tolerance.
- `result`: Honest FAIL — `regime_filter_does_not_reduce_drawdown_oos` — on exactly ONE pre-registered gate: walk-forward selection-process stability. The criterion chose `regime1_lb90_br6_btc_required_1d` (train dd 37.6% vs 52-79% for the fast filters REGIME1's Sharpe criterion loved; 60 train flips vs 116-144; alone in the tie band) and the endpoint result is strong everywhere the verdict looks at the END of history: OOS max-drawdown reduction 33.64% (bar 30%, held), OOS Sharpe 0.88 vs always-long 0.13, OOS return +60.9% vs -19.6% (tolerance trivially met), 35 OOS flips vs REGIME1's 58, 3/18 false risk-off spells, no-lookahead verified — and the SAME config held fixed reduces drawdown in BOTH fold windows (chop fold: 28.2% vs 39.4%; fold C: 43.6% vs 65.7%; surfaced as labeled NOT-A-VERDICT texture). But the pre-registered fold gate judges the SELECTION PROCESS (per-fold train-only choice — REGIME1's method, unchanged): at fold B's cutoff (~1/3 of history, essentially one violent bull) the min-train-drawdown criterion picks a FAST filter (`regime1_lb30_br5_btc_required_1d`) whose chop-fold drawdown WORSENS vs always-long (45.6% vs 39.4%). The objective-aligned criterion is right at full history and unstable on short history — that instability is the genuine, newly-learned failure mode.
- `honesty_notes`: re-reading the fold gate post-hoc as fixed-config windows (which would pass) was considered and REFUSED — the pre-registration defines the gate as the process test and changing the reading after seeing the result is the exact self-deception the guard forbids. The search was not widened; no bar moved; the criterion was committed before selection (git history on branch `regime2` proves the ordering).
- `scope`: `services/strategy_validation/regime2.py` (pre-registration, selection, gate v2), `scripts/run_regime2_evidence.py`, deployed-surface updates in `regime1.py` (DEFAULT_CONFIG -> the REGIME2 selection; COMMITTED_VERDICT_NOTE rewritten honestly), `docs/regime2_*`, `tests/test_regime2_filter.py` + REGIME1 test updates, CI fast lane.
- `boundaries`: Risk tool, not alpha; signal only; no orders, no private/signed endpoints, no testnet/live, no approval surface, no runtime change.
- `follow_up_implications`: MONEYFLOW-SIGNAL1 (next) imports the gate knowing exactly what it has: an endpoint-strong, process-unstable risk-off filter (informational risk context, not validated control; the note travels with every state). A REGIME3 would need a selection rule that is STABLE on short history — e.g., a structural always-slowest rule or a minimum-train-length guard before trusting the drawdown criterion — pre-registered like this phase, never a post-hoc re-read of this fold gate. The two regime phases together sharpen the repo's selection discipline: the criterion must match the objective AND be stable under the walk-forward it will be judged by.

```yaml
research_log:
  phase: REGIME2
  date: 2026-06-12
  class: time_series_momentum
  outcome: fail
  badge: endpoint bars cleared; process failed walk-forward
  title: Objective-Aligned Regime Filter (pre-registered re-test)
  finding: >-
    The pre-registered drawdown criterion chose the slow filter
    (lb90/br0.6/required) and cleared every endpoint bar - OOS drawdown
    reduction 33.64% vs the held 30% bar, Sharpe 0.88 vs 0.13, return
    +60.9% vs -19.6%, and drawdown reduced in both fold windows held
    fixed - but the verdict is an honest fail: at the early-history fold
    cutoff the same criterion picks a fast filter that worsens the chop
    fold. The selection process, not the config, failed its walk-forward.
  why: >-
    REGIME1 failed on a criterion mismatch (train Sharpe rewards fast
    stay-long filters; a drawdown tool needs a slow one). The fix had to
    be confirmatory-grade: criterion and gates pre-registered and
    committed to git before selection, grid unwidened, REGIME1 bars held.
  worked: >-
    The pre-registration discipline itself (the git history proves the
    criterion preceded the result); the objective-aligned criterion at
    full history (picked the slow filter, fewest flips, alone in the tie
    band); the mechanism again (the chosen filter cut OOS drawdown by a
    third while QUADRUPLING return vs always-long, and called the live
    bear correctly).
  didnt: >-
    Selection-process stability: with only ~580 train days (one violent
    bull) the min-train-drawdown criterion prefers fast filters - small
    drawdowns in a straight-up market - and the fast pick worsens the
    chop fold. The fold gate judges the process and the process is not
    yet trustworthy on short history. Re-reading the gate post-hoc was
    refused.
  lesson: >-
    A drawdown tool must be selected by drawdown AND the selection rule
    must itself survive walk-forward: criterion-objective alignment is
    necessary but not sufficient - stability of the rule on short history
    is the remaining gap, and only a pre-registered REGIME3 with a
    structurally stable rule could close it.
  our_error: >-
    REGIME1's criterion mismatch was ours, not the mechanism's - REGIME2
    confirms it: the same grid under the objective-aligned criterion
    clears every endpoint bar the Sharpe choice missed. The remaining
    fail (process instability on short history) is a genuine property of
    the selection rule, surfaced by our own pre-registered fold gate.
  changed: >-
    The deployed gate/CLI now pin the REGIME2 selection with the honest
    verdict embedded (informational risk context, not validated control).
    MONEYFLOW-SIGNAL1 imports it knowing that. A REGIME3 needs a
    short-history-stable selection rule, pre-registered; the fold gate is
    never re-read after the fact.
  hardened_gate:
    - selection criteria are pre-registered and committed before selection runs
    - the selection PROCESS must survive walk-forward, not just the final config
  evidence_summary: docs/regime2_objective_aligned_regime_filter_evidence_summary.json
  evidence_doc: docs/regime2_objective_aligned_regime_filter_evidence.md
```

## 2026-06-12T08:15:00Z - REGIME2 - PRE-REGISTRATION: Objective-Aligned Selection, Bars Held (committed before the selection run)

- `decision`: Re-test REGIME1 with exactly ONE change, pre-registered here and in `services/strategy_validation/regime2.py` BEFORE the selection runs (this entry and that module are committed to git first; the evidence run follows in a later commit). REGIME1's failure was the criterion, not the mechanism: train Sharpe rewards fast stay-long filters when a drawdown tool needs a slow one. REGIME2 selects on the OBJECTIVE — lowest gated TRAIN max drawdown (= largest train drawdown reduction vs the shared always-long book) — with a whipsaw tie-break: configs within 2.0 percentage points of the best train drawdown are ties, broken by FEWEST train state flips, then config_id. Selection never sees OOS.
- `pre_registered_gates_all_required`: (1) OOS max-drawdown reduction >= 30% vs always-long — REGIME1's bar, unchanged; (2) drawdown reduced vs always-long in EVERY walk-forward fold — REGIME1's bar, unchanged (strictly stronger than "the chop fold must not worsen"); (3) OOS Sharpe >= always-long — unchanged; (4) OOS total return >= always-long minus 25 percentage points (return-retention tolerance, stated here in advance); (5) minimum OOS days; (6) no-lookahead probe verified. A miss on ANY gate is an honest fail and will be recorded as one.
- `honesty_guard`: the search space is REGIME1's exact grid (3 lookbacks x 3 thresholds x 2 BTC rules = 18) — NOT widened; same universe (DATA1 Binance 7 majors), window, friction, books, common warm-up, folds, and OOS methods. The criterion is chosen on principle (the tool's objective is drawdown control); REGIME1's hindsight table is not consulted by the selection — whatever the criterion picks, the pre-registered gates judge it.
- `boundaries`: Risk tool, not alpha; signal only; no orders, no private/signed endpoints, no testnet/live, no approval surface, no runtime change.
- `result`: run complete — see the REGIME2 results entry above (2026-06-12T09:00:00Z); the selection chose `regime1_lb90_br6_btc_required_1d` and the verdict is the honest FAIL on walk-forward selection-process stability, with every endpoint bar cleared.

## 2026-06-12T07:30:00Z - REGIME1 - The Risk-Off Bell Rings True In Bears And Lies In Chop; The Honest Bar Says Not Yet

- `decision`: Turn trend's one durable validated property (drawdown defense, held across TSMOM-EV1/TREND-OVERLAY1/TREND-SUITE1) into a reusable market-regime risk-off filter: breadth = fraction of liquid majors whose reused `tsmom_signal` trend sign is up, combined with a BTC bellwether rule (vote|required), on closed candles only -> `risk_on`/`risk_off` (+ graded `risk_score` for display). Bounded grid (3 lookbacks x 3 thresholds x 2 BTC rules = 18), train-only choice on the gated book's train Sharpe (chronological 70/30). The filter had to EARN its use on an equal-weight long book of the 7 DATA1 Binance majors (2020-09 -> 2026-06, weekly rebalance, EXEC-EV1 conservative friction, both books idle through a common 90-candle warm-up): the risk-tool gate requires MATERIAL OOS max-drawdown reduction (>=30% relative), not-worse OOS Sharpe, drawdown reduced in EVERY walk-forward fold, enough OOS days, and a verified no-lookahead probe. Risk tool, not alpha — the disclaimer is structural on every surface.
- `result`: Honest FAIL — `regime_filter_does_not_reduce_drawdown_oos`. The train-chosen config (lb30/br0.5/btc-vote, the fast filter train Sharpe loves) cut OOS max drawdown 46.17% vs always-long 65.73% = a 29.76% relative reduction, 0.24pp UNDER the pre-committed 30% material bar — and it WORSENED drawdown in the chop fold (2022-08 -> 2024-07: gated 45.6% vs always 39.4%) on 58 OOS state flips (53% of OOS days risk-off; 6 of 30 OOS risk-off spells were FALSE — return given up while always-long gained). The defensive texture is real and visible (OOS Sharpe 0.53 vs 0.13; OOS return +26.0% vs -19.6%; fold C dd 46% vs 66%; train dd 52% vs 79% while EARNING more, 7244% vs 3188%, by sidestepping the 2022 bear) — but the committed bar says the filter as chosen did not earn its use, and the bar was not moved. Hindsight texture surfaced and labeled NOT-A-VERDICT (TREND-SUITE1 precedent): slower/stricter configs (lb60/br0.6/required) cut OOS dd to 33.3% (~49% reduction) and a min-train-drawdown criterion would have chosen lb90/br0.6/required — the criterion gap (train Sharpe loves fast filters; drawdown control wants slow ones) is itself the phase's sharpest lesson. Live sample at ship (2026-06-12 close, real public candles): RISK_OFF — 0/7 majors trend-up, BTC down (consistent with TREND-OVERLAY1's fully-flat posture in the current bear).
- `scope`: `services/strategy_validation/regime1.py` (state, whipsaw classification, risk-tool gate, importable `RegimeGate`), ADDITIVE `strategy_types.REGIME_FILTER_REF` + `resolve_regime_filter()` seam (no routing/type/gate changes to existing strategy types), `scripts/run_regime1_evidence.py`, `scripts/run_regime_filter.py` (read-only CLI), `docs/regime1_*`, `tests/test_regime1_filter.py`, CI fast lane, `.gitignore` (`reports/regime1/`).
- `rejected_alternatives`: Re-choosing the config or the criterion after seeing OOS (the hindsight rows would "pass" — that is exactly the overfit the discipline forbids; they are surfaced, labeled, and not believed); softening the 30% material bar to admit the 29.76% miss (a bar that bends to admit the result is not a bar); hysteresis/dual thresholds (doubles the grid — a REGIME2 design choice if ever scoped, chosen up front); judging the filter on return (it is a drawdown tool; return giveback is its nature and is reported as the whipsaw cost instead); withholding the tool because the gate failed (Must-3 scope ships it — with the failed verdict embedded in every output so no consumer can mistake it for validated control).
- `boundaries`: Signal only — no orders, no private/signed endpoints, no testnet/live, no approval surface, no runtime change. Public read-only data (DATA1 + the same Binance klines endpoint for the CLI). The state is informational risk context; the committed-verdict note travels with it everywhere.
- `follow_up_implications`: The reusable gate EXISTS at `strategy_types.resolve_regime_filter()` -> `build_regime_gate(datasets)` -> `is_risk_on(as_of)`, defaults pinned by test to the committed train-only choice, intended to suppress LONG entries in market-wide downtrends — MONEYFLOW-SIGNAL1 (next) may import it as an optional overlay knowing the verdict. A REGIME2 re-test with a drawdown-purposed train criterion (e.g., min train drawdown at acceptable Sharpe, pre-committed) and/or hysteresis would be a NEW phase with this phase's lesson baked in, never a re-tune of this grid after the fact.

```yaml
research_log:
  phase: REGIME1
  date: 2026-06-12
  class: time_series_momentum
  outcome: fail
  badge: rings true in bears, lies in chop
  title: Market-Regime Risk-Off Filter (when NOT to be long)
  finding: >-
    Honest fail by 0.24pp: the train-chosen fast filter (lb30) cut OOS max
    drawdown 29.76% vs the pre-committed 30% material bar and worsened
    drawdown in the 2022-24 chop fold (58 OOS flips). The defensive
    texture is real - OOS dd 46.2% vs 65.7%, Sharpe 0.53 vs 0.13, +26% vs
    -19.6% - but the committed bar held and was not moved.
  why: >-
    Trend's only surviving validated property is drawdown defense; a
    breadth-based risk-off bell is the cheapest reusable form of it, and
    future long strategies (MONEYFLOW-SIGNAL1) need a gate that says when
    NOT to be long. It had to earn that role against an always-long book,
    not be assumed into it.
  worked: >-
    The mechanism - breadth of reused tsmom signs steps aside in real
    bears (train: sidestepped 2022 and EARNED more doing it; fold C and
    the live 2026 sample both call risk-off correctly); the no-lookahead
    probes, the common warm-up discipline, and the whipsaw accounting
    (false vs true risk-off spells) made the cost auditable.
  didnt: >-
    The train criterion - train Sharpe loves fast filters, and the fast
    filter lies in chop: it missed the material bar and ADDED drawdown in
    the choppy middle fold. Hindsight configs that pass (slower lookback,
    stricter breadth) are surfaced and labeled not-a-verdict; believing
    them would be the overfit this repo exists to refuse.
  lesson: >-
    Trend's value really is regime defense and it is now reusable - but a
    drawdown tool must be CHOSEN by a drawdown criterion, decided up
    front. A risk filter chosen on Sharpe optimizes the wrong thing and
    whipsaws; the criterion gap, not the signal, is what failed here.
  our_error: null
  our_error_note: >-
    the method held - the bar was pre-committed and not moved for a
    0.24pp miss, the hindsight passes were surfaced and refused, and the
    criterion mismatch is recorded as the design lesson for any REGIME2
  changed: >-
    The importable risk-off gate ships (strategy_types.resolve_regime_filter,
    defaults pinned, failed verdict on every surface - informational risk
    context, not validated control). MONEYFLOW-SIGNAL1 is next and may
    layer it as an optional overlay knowing the verdict; a REGIME2 with a
    pre-committed drawdown criterion would be a new phase.
  hardened_gate: a drawdown tool must be train-chosen by a drawdown criterion, committed up front
  evidence_summary: docs/regime1_market_regime_risk_off_filter_evidence_summary.json
  evidence_doc: docs/regime1_market_regime_risk_off_filter_evidence.md
```

## 2026-06-12T05:15:00Z - FUND-VENUES1 - Deep Venues Fix The Costs, Not The Tail; Leverage Liquidates The Book

- `decision`: Run the structural re-open FUND-EV2/FUND-SCALE1 sanctioned: the SAME delta-neutral funding-carry hypothesis on venues with materially different cited fee schedules and 6-7 years of funding history (DATA1: Binance 2019-09+, Bybit 2020-03+), with gross leverage {1x, 3x, 5x} as an explicitly modeled variable — borrow financing on the real cash shortfall (documented 0.02%/day, swept with every cost term) and an account-level intraday liquidation check (every leg marked at its worst same-day extreme; breach force-closes the whole book at stressed prices). Constructions: binance_single and bybit_single carry the verdict; binance perp + Coinbase spot is the cross-venue variant. Fees cited at the tier a 10k account's OWN flow earns (Binance VIP0 perp 2/5 bps, spot 10/10; Bybit non-VIP 2/5.5, 10/10; Coinbase 60 bps taker for the variant; OKX cited for the record only); the gateable verdict prices taker fills — maker is a non-gateable ceiling; the venue-fair window is enforced from DATA1 coverage (OKX ~92d, Kraken ~366d, HL 1126d funding excluded with recorded reasons per K-036). Gate v3 = the full FUND-EV2 bar + net positive in every OOS regime bucket + zero liquidation events (OOS and stressed). Bounded grid (cadence 14/28 x top 2/4) per (construction, leverage) cell, train-only choice, FUND-EV2 selectivity (2x entry margin, hold-while-favorable).
- `result`: Honest FAIL in ALL NINE cells — `carry_does_not_survive_realistic_costs_and_tail_oos`. The texture is the finding. (1) THE VENUE WAS THE COST PROBLEM: binance_single 1x earns OOS net +179 USDC (Sharpe 3.5, maxDD 0.08%, 627 OOS days), positive in every walk-forward fold, every leave-one-out drop, every OOS regime bucket (bear +0.21 / neutral +26 / bull +153), and every calendar cycle (2021 bull +2845, 2022 bear +54, 2023-24 +990, 2025-26 +17); its cost-sensitivity breakpoint is 5.0x cited costs where FUND-EV2's HL book died at 0.75x. It fails ONLY the pre-committed legged-execution tail stress: 9.68% stressed max drawdown vs the documented 8% account limit (the stress holds one-leg exposure a full day on every rebalance at 2x costs — daily resolution overstates legging duration, documented since FUND-EV2, and the limit was not moved in either direction). The OOS capture is also economically thin: ~0.76%/yr at 1x — funding compressed post-2024. (2) LEVERAGE IS CATASTROPHIC, NOT A MULTIPLIER: at 3x the 2021 alt-mania (DOGE/XRP-style intraday spikes against the short perp legs) liquidates the book FOUR times and wipes the account to -100% (full net -9999.82); at 5x equity ends negative (-10788); even Bybit's calmer 2022+ window liquidates once at 5x with stressed drawdown ~90%. (3) A nominal 1x book transiently needs ~58% of equity in financing during violent rallies (max borrowed 5816 at 1x) — discrete rebalancing lets the spot leg inflate while equity stays hedged-flat; the margin model priced exactly this. (4) Cross-venue Coinbase spot is dead at every leverage (60 bps retail taker), reconfirming FUND-EV2's cross-venue conclusion on a second venue pair. Benchmarks: always-on at 1x earns less than the selective book (selectivity adds); the HL FUND-EV2 reference (-6.52 OOS) sits beside binance_single 1x (+179 OOS) — deep venues changed the cost answer, not the verdict.
- `scope`: `services/strategy_validation/fund_venues1.py`, additive `margin_model` seam in `fund_ev1.py` (default None byte-identical; 41 existing FUND tests green unchanged), `fund_venues1_` prefix on the funding_carry route in `strategy_types.py`, `scripts/run_fund_venues1_evidence.py`, `docs/fund_venues1_*`, `tests/test_fund_venues1_evidence.py`, CI fast lane.
- `rejected_alternatives`: Softening the 8% stressed-tail limit or the 1-day leg-lag stress for the near-miss (the bar is FUND-EV1's committed account limit and the stress is FUND-EV2's committed design — moving either to flip a verdict is exactly what the discipline guard forbids); gating on maker fills (non-fill risk unmodeled — reported as ceiling only; OOS maker ceiling +179.45 vs taker +179.18 anyway: selectivity binds OOS, not fees); assuming a reachable VIP tier (FUND-SCALE1 own-volume rule: 10k carry flow cannot earn Binance VIP1's $1M 30d volume); padding shallow funding histories (OKX/Kraken/HL excluded with recorded reasons); dropping BNB/SOL for their poor funding (kept — the universe is the venue's listing reality; selectivity must earn its keep); isolated-margin per-leg liquidation modeling (cross-margin account-level is the realistic operator setup AND the conservative same-day-adversarial-extremes marking already overstates basis risk).
- `boundaries`: Research/evidence only — DATA1 public read-only inputs (sha256-verified loader), no orders, no private/signed/live endpoints, no approval surface, no runtime change. Fees cited, never tuned; borrow rate a documented swept assumption; no per-venue l2 calibration (modeled half-spreads with headroom, swept); maker non-fill risk unmodeled (ceiling only); liquidation model conservative (adversarial same-day extremes); daily funding accrual approximation unchanged from FUND-EV1.
- `follow_up_implications`: The funding-carry family is now closed on its THIRD sanctioned axis (venues + leverage, after cost realism and scale/fee tiers). What survives, precisely: the gross funding edge is real on deep venues across 6 years and every regime, capture-positive at cited taker costs OOS at 1x — and the binding constraint is now the LEGGED-EXECUTION TAIL plus thin absolute capture, not fees. The only path that could reopen carry is sub-candle atomic-execution evidence (both legs filled near-simultaneously, shrinking the gap the stress prices) — a NEW phase with new evidence, never a re-tune of this grid. Leverage on a delta-neutral carry book is settled: catastrophic at the account scale tested. REGIME1 is the next research phase; MONEYFLOW-SIGNAL1 stays parked.

```yaml
research_log:
  phase: FUND-VENUES1
  date: 2026-06-12
  class: funding_carry
  outcome: fail
  badge: deep venues fix costs, not the tail
  title: Funding Carry on Deep Venues, with Leverage
  finding: >-
    Honest fail in all nine (construction x leverage) cells. Deep venues
    fixed the cost half of the HL fail - binance_single 1x is OOS-positive
    (+179 USDC, Sharpe 3.5) in every fold, drop, regime, and cycle with a
    5.0x cost breakpoint (HL died at 0.75x) - but it fails the committed
    legged-execution tail limit (9.68% vs 8%) and capture is ~0.76%/yr.
    Leverage liquidates the book: -100% at 3x in the 2021 mania.
  why: >-
    FUND-EV2 closed carry at retail on HL citations with 2.5y of data; the
    open question was whether the venue (thin spot, fees) or the edge was
    the problem. DATA1's 6-7y Binance/Bybit histories with real fee
    schedules made the venue-fair test possible, and leverage was the
    untested capture lever everyone reaches for.
  worked: >-
    The reuse discipline once more - the FUND-EV1 simulator ran unchanged
    through its cost/margin seams (defaults byte-identical, pinned); the
    venue-fair window enforcement (K-036) kept shallow funding histories
    out of the verdict; the margin model surfaced a non-obvious truth
    (a nominal 1x book transiently needs ~58% of equity in financing in
    violent rallies) and priced the 2021 liquidations the leverage story
    needed.
  didnt: >-
    Leverage as a capture multiplier - it multiplied the tail first (four
    liquidations and a wiped account at 3x; equity negative at 5x). The
    cross-venue construction died again on retail spot fees (Coinbase 60
    bps after Kraken 40 bps in FUND-EV2). And the tail discipline itself:
    the one near-miss fails exactly on the pre-committed stressed-tail
    limit, not on costs.
  lesson: >-
    The funding edge is real and venue-dependent capture is real - costs
    were the venue's fault, the tail is the strategy's. A delta-neutral
    book's binding risk is the legged-execution gap, and leverage turns
    that gap from a drawdown into a liquidation. Closing the family takes
    three axes: costs, scale, venues+leverage - all now tested, all fail.
  our_error: null
  our_error_note: >-
    HL-only was a recorded data limitation, not a method error - and the
    venue-fair re-test confirms it carried the cost half of the original
    fail (breakpoint 0.75x -> 5.0x on Binance) while the verdict still
    fails on the tail and thin capture; deep venues + leverage changed
    the diagnosis, not the answer.
  changed: >-
    Funding carry is closed on all three sanctioned axes; only sub-candle
    atomic-execution evidence could reopen it as a new phase. REGIME1 is
    next; MONEYFLOW-SIGNAL1 stays parked.
  hardened_gate:
    - every OOS regime bucket must be positive, not just non-bull
    - zero liquidation events in OOS and stressed runs at the tested leverage
  evidence_summary: docs/fund_venues1_deep_venue_leverage_carry_evidence_summary.json
  evidence_doc: docs/fund_venues1_deep_venue_leverage_carry_evidence.md
```

## 2026-06-12T02:30:00Z - DATA1 - The HL-Only Limitation Is Fixed: A Multi-Venue, Provenance-Tracked, Honestly-Gapped Data Foundation

- `decision`: Build the multi-venue public read-only dataset (perp funding history, perp daily candles, spot daily candles) for the liquid majors (BTC/ETH/SOL + XRP/DOGE/BNB/AVAX where listed) across hyperliquid, binance, bybit, okx, coinbase, kraken — data ingestion ONLY (no strategy logic, no orders, no private/signed endpoints, no keys, no runtime change), reusing the FUND-EV1 snapshot discipline: raw native payloads as ignored local artifacts, committed provenance + sha256 + coverage in `docs/data1_multi_venue_snapshot_summary.json`, and a loader (`load_data1_dataset`) that verifies integrity and exposes coverage flags instead of papering over gaps.
- `result`: 101 of 101 expected series fetched OK on 2026-06-11 (0 fetch failures); the 25 non-fetchable cells are real venue gaps recorded as `venue_lacks_market` (Coinbase has no public perp/funding market data and no BNB; OKX and Kraken list no BNB; HL spot exists only for BTC/ETH/SOL). History depth now: Coinbase BTC spot from 2015-07 (~3,979 daily candles) and Binance spot from 2017-08 vs the previous 889-candle HL-only window; Binance funding from 2019-09 (6.7y), Bybit from 2020-03. The probe + normalizers caught three traps that would have silently poisoned cross-venue work: (1) OKX default daily bars are UTC+8-aligned — fetched as `1Dutc`, and the normalizer REFUSES any non-midnight-UTC daily candle; (2) Hyperliquid serves ~900+ zero-volume perp candles per asset from BEFORE the venue traded (back to 2020-08) — kept as the venue serves them but counted per series (`zero_volume_rows`/`first_nonzero_volume_close`: real HL trading starts 2023-02/03 per asset); (3) public funding history is much shallower than candle history on some venues — OKX only ~3 months, Kraken Futures ~1y, recorded as venue limits (K-036). Coinbase XRP-USD carries its real 904-day delisting hole (2021-01-19 → 2023-07-13) as an explicit gap — union-calendar alignment never forward-fills, interpolates, or truncates.
- `scope`: `services/market_data/data1_multi_venue.py` (catalog with explicit gaps, allowlisted-endpoint fetchers over an injected transport, strict normalizers, FUND-EV1-convention daily funding aggregation with declared+observed intervals, union alignment, sha256-verifying loader), `scripts/fetch_data1_multi_venue_snapshot.py` (resumable one-shot snapshot), `docs/data1_*`, `tests/test_data1_multi_venue.py` (blocking CI), `tests/test_data1_live_smoke.py` (env-gated), CI fast lane.
- `rejected_alternatives`: Committing the bulk series (raw is 57MB — ignored artifacts + committed sha256 keep the repo lean and the data auditable/regenerable, the SV2.2 pattern); rescaling 8h funding rates to hourly equivalents (sums per day are comparable without pretending the venues are identical); forward-filling or intersection-truncating the aligned calendar (the gaps ARE the information); substituting Coinbase INTX or another source where a venue lacks a market (a wrong cross-venue assumption would poison the next funding test); hourly price candles (deep hourly needs thousands of paginated calls; funding events already carry the sub-daily resolution that matters — deferred, documented).
- `boundaries`: Public read-only market-data endpoints only, pinned by a module-level allowlist the fetchers enforce; no API keys read, no private/signed/account/order endpoint anywhere; nothing submitted; no strategy logic or gate; no runtime artifact touched. The dataset informs FUTURE phases; it changes no current verdict.
- `follow_up_implications`: FUND-VENUES1 is unblocked with a venue-fair funding base (five venues aligned daily) BUT any design must respect recorded depth limits (OKX ~3 months of funding; Kraken 1y). Trend/regime re-tests can now use >1 OOS cycle of spot history (2015+). The next phase consuming this data must read coverage flags from the loader — that is the contract.

```yaml
research_log:
  phase: DATA1
  date: 2026-06-12
  class: data_prep
  outcome: context
  badge: multi-venue data foundation
  title: Multi-Venue Market & Funding Data Foundation
  finding: >-
    101/101 expected series ingested across six venues (funding/perp/spot
    daily, BTC ETH SOL XRP DOGE BNB AVAX) with committed provenance +
    sha256; 25 real venue gaps recorded as coverage, never substituted.
    BTC spot history now reaches 2015-07 (~3,979 daily candles) vs the
    889-candle HL-only window.
  why: >-
    Every prior verdict stood on Hyperliquid-only data - sharpest for
    funding carry (HL's thin spot + fees drove the fail) and for trend
    (one venue, one bull-bear cycle). A venue-fair funding test and any
    longer-history trend/regime claim need this base first.
  worked: >-
    The FUND-EV1 snapshot discipline scaled to six venues unchanged
    (ignored raw artifacts + committed sha256 provenance); the probe-first
    approach caught the OKX UTC+8 daily-bar trap before a single byte was
    ingested; the midnight-UTC normalizer guard and zero-volume accounting
    turned two silent poisoning risks into recorded facts.
  didnt: >-
    Public funding history is far shallower than candle history on two
    venues (OKX ~3 months, Kraken Futures ~1y) - the venue-fair funding
    window is narrower than the candle window and tests must shrink or
    drop venues explicitly. Hyperliquid publishes ~900+ pre-launch
    zero-volume candles per asset that must never be read as market
    history. Kraken spot caps at 720 days.
  lesson: >-
    Cross-venue data is full of silent misalignment traps - bar timezone
    defaults, backfilled pre-launch candles, delisting holes, uneven
    history depth. Recording gaps as first-class coverage (and refusing
    non-midnight bars outright) is what makes the dataset trustworthy
    enough to base a venue-fair test on.
  our_error: null
  our_error_note: >-
    the probe + strict normalizers caught the traps before ingestion;
    nothing had to be corrected after the fact
  changed: >-
    FUND-VENUES1 is unblocked (five venues' funding aligned daily);
    trend/regime re-tests gain >1 OOS cycle of spot history; every future
    consumer must read the loader's coverage flags before comparing
    venues (K-036).
  hardened_gate: consult coverage flags before any cross-venue comparison
  evidence_summary: docs/data1_multi_venue_snapshot_summary.json
  evidence_doc: docs/data1_multi_venue_data_foundation.md
```

## 2026-06-12T01:30:00Z - TREND-SUITE1 - The Richer Trend Suite Finds Nothing Better Than TSMOM, And Vol-Targeting Was Not The Cap

- `decision`: Test the canonical trend-following suite TSMOM-EV1 never tried — Donchian channel breakout (Turtle 20/55, channel + ATR/chandelier exits), dual-MA crossover (3x3 grid), multi-timeframe confirmation (daily gated by a frozen weekly sign), the TSMOM carry-over, and a majority/average ensemble — every signal cell under BOTH vol-targeted (EV1-style) and non-vol-targeted equal-dollar sizing, judged by the SAME buy-and-hold risk-adjusted gate on the same eight liquid majors after EXEC-EV1 conservative friction at 10,000 USDC. 46-config bounded grid, parameters chosen on the train split only; new `trend_suite` routing type (prefix `trend_suite1_`) deliberately shares the TSMOM gate id; the EV1 simulator is reused verbatim through its signal-provider/rebalance-timestamps seams.
- `result`: BOTH headline hypotheses came back negative, decisively. (1) The richer suite does NOT beat one-form TSMOM: the train-only choice across all 46 configs picked the EV1 signal again (`trend_suite1_tsmom30_signal_vt_1d`), and its OOS stats reproduce the committed EV1 numbers digit for digit (Sharpe -1.478, return -12.23%, max DD 16.56% vs buy-hold -61.69% / 65.68%) — relative gate PASS with both absolute-loss qualifiers, same as EV1. (2) Vol-targeting was NOT the cap: all 23 vt-vs-eq pairs classified `removing_vol_target_added_drawdown_without_more_return_oos`; in 16 of 23 pairs the uncapped variant DID earn a higher full-window (bull-heavy) return, but every pair gave it back out-of-sample — removing the cap was leverage on the same signal, not a new edge. No trend form clears the absolute bar (best OOS config in hindsight, `trend_suite1_mtf60w8_atr_vt_1d`, still lost -4.1%); two family champions (donchian ATR-trail VT, tsmom VT) pass the full relative gate as defensive value only; ma_cross, mtf, and ensemble champions fail it outright.
- `scope`: `services/strategy_validation/trend_suite1.py` (causal signal state machines, sizing/exit variants, screen + VT-effect classifier), `services/strategy_validation/strategy_types.py` (trend_suite route sharing TSMOM_GATE_ID), `services/strategy_validation/tsmom_ev1.py` (target_weights accepts fractional strengths; integer ±1 path byte-identical, pinned by test), `scripts/run_trend_suite1_evidence.py`, `docs/trend_suite1_*`, `tests/test_trend_suite1_evidence.py`, CI fast lane.
- `rejected_alternatives`: Judging the suite by a new bespoke gate (it would make results incomparable to EV1 — the shared gate is the point); long/short variants (EV1's grid already covered long_short and found no edge; the suite is long-only as the canon specifies "long on upper-channel break"); running leave-one-out for all 46 configs (full gate — walk-forward + leave-one-out + late-entry — runs for the global train-chosen config and each family champion; every config still gets the OOS screen with the same verdict vocabulary); tuning ensemble membership on this phase's data (members are fixed canonical cells, documented); treating the hindsight-best OOS config as a finding (surfaced, labeled not-a-verdict).
- `boundaries`: Research/evidence only. No runtime, strategy-rule, order, testnet, live, or production-approval change. Modeled depth (EXEC-EV1), never real order-book depth; perp funding NOT modeled (long-only books would typically PAY funding in bulls, so absolute profits are optimistic — and they were still negative). Signals were designed from the documented canon and not tuned to the verdict.
- `follow_up_implications`: The trend hypothesis family on this data is now closed on both sanctioned axes: signal form (TREND-SUITE1) and sizing (vol-targeting was not the cap). What survives: trend's defensive value is real and consistent (29 of 46 configs pass the relative OOS screen; the deployed TREND-OVERLAY1 posture is unchanged and needs no re-tune — the suite found nothing better to deploy). What could reopen trend: a different REGIME definition (REGIME1, queued: condition exposure on regime states rather than signal sign), longer/cross-venue history (DATA1), or carry financing the short side (TREND-CARRY, still constrained by FUND-EV2 costs). None of these is a re-tune of the present grid.
- `correction_2026-06-12`: the research_log analytics pointer originally referenced `headline_answers` as a raw `value` (rendered as an unformatted JSON blob in the dashboard, and pointing at the wrong node — the vol-cap pair data lives in `vol_targeting_comparison`); repointed to the `trend_suite1_vol_cap_effect` computed view. Display metadata only; no factual content of this entry changed.

```yaml
research_log:
  phase: TREND-SUITE1
  date: 2026-06-12
  class: time_series_momentum
  outcome: mixed
  badge: defensive only - suite adds nothing
  title: The Canonical Trend Suite vs One-Form TSMOM
  finding: >-
    The full canonical suite (Donchian 20/55, MA crossover 3x3,
    multi-timeframe confirmation, ensemble) finds nothing better than the
    TSMOM-EV1 signal: the train-only choice across 46 configs picked the
    EV1 config again, and no trend form is profitable OOS in absolute
    terms (best hindsight config still -4.1%). The relative gate passes as
    defensive value only (-12.2% vs buy-hold -61.7%).
  why: >-
    TSMOM-EV1 left two open hypotheses - a richer signal family might find
    profit where return-sign momentum found only defense, and the vol
    targeting might have capped the upside (it cuts exposure exactly in
    outlier trends). Both deserved a real test, not an assumption.
  worked: >-
    The reuse discipline again - the EV1 simulator ran every new signal
    through its provider seam, and the suite's TSMOM carry-over reproduces
    the committed EV1 OOS numbers digit for digit (pinned by test), so the
    comparison is apples-to-apples by construction. The pairwise
    vt-vs-equal-dollar design made the sizing question decidable.
  didnt: >-
    Every new signal form, as a profit source: Donchian, MA cross, MTF,
    and both ensembles all lose money OOS; three of five family champions
    fail even the relative gate. Removing the vol cap raised bull-window
    returns in 16 of 23 pairs and gave all of it back OOS in every pair -
    leverage, not edge.
  lesson: >-
    A richer trend suite does not beat one-form TSMOM on this data, and
    vol-targeting was not what kept trend from profiting - the OOS bear
    pays trend in avoided drawdown, not in returns, regardless of signal
    form or sizing. Trend here is a defensive overlay, not an alpha
    source; only a new regime definition or new data could reopen it.
  our_error: null
  changed: >-
    The trend family is closed on both sanctioned axes (signal form,
    sizing); TREND-OVERLAY1 stays deployed unchanged - the suite found
    nothing better to deploy. REGIME1 / DATA1 remain the only open doors.
  hardened_gate: suite carry-over must reproduce committed EV1 OOS digit for digit
  evidence_summary: docs/trend_suite1_canonical_trend_suite_evidence_summary.json
  evidence_doc: docs/trend_suite1_canonical_trend_suite_evidence.md
  analytics:
    - label: Vol-cap removal effect (23 pairs)
      kind: computed
      source: trend_suite1_vol_cap_effect
```

## 2026-06-11T22:30:00Z - TREND-OVERLAY1 - The Defensive Finding Becomes A Read-Only Tool; The Honest Framing Travels With It

- `decision`: (1) Operationalize the TSMOM-EV1 validated finding as a deployable READ-ONLY signal tool - a forward calculator on the latest fully-closed public-mainnet candles that reports per-asset trend state (hold / flat) and the vol-targeted target exposure for a configurable account size. This is the DEPLOYMENT of an existing finding, not a new strategy test: the tool reuses the exact TSMOM-EV1 computation under the train-chosen config (tsmom_ev1_lb30_vt20_long_only_1d) and the defaults are pinned by test to the committed evidence summary - changing them without new evidence fails CI. (2) Honest framing is structural, not optional: the drawdown-control-not-alpha disclaimer (including the absolute -12.2% OOS loss and the authored mixed outcome) is embedded in the module, the CLI stdout, every JSON output, and the docs; the trading-safety text guard enforces the posture. (3) The optional OS panel is SKIPPED, documented: it would require lockstep changes to index.html / evidence-dashboard.js / static-asset guards / DASH-QA1 plus empty-state handling for an ignored artifact - non-trivial dashboard surgery for a CLI-first tool. The deliverable is the CLI + JSON; a display-only panel can be its own phase.
- `scope`: `services/strategy_validation/trend_overlay1.py` (pure calculator: closed-candle filter, reused tsmom signal/vol/weights, disclaimer, signal-only boundaries), `scripts/run_trend_overlay.py` (public read-only candleSnapshot fetch or offline --input-json replay; writes ignored `reports/trend_overlay/current_trend_overlay.json`), `docs/trend_overlay1_*`, `tests/test_trend_overlay1.py`, CI fast lane, `.gitignore`.
- `result`: Live sample (2026-06-11, real latest candles): all eight liquid majors are in 30-day downtrend - the overlay's current target is FULLY FLAT, 0 of 10,000 USDC exposed (8 flat / 0 held). That is the validated defensive action in the live 2026 bear: an operator holding a long book sees the overlay calling for cash; it is not a prediction. Closed-candle no-lookahead verified (in-progress and future candles are dropped and cannot change the output); the text guard caught one wording during the build ("nothing here is production-approved" was not a recognized negation) and it was rephrased - the guard is green.
- `boundaries`: Signal only. Public read-only data (the same candleSnapshot endpoint the dashboard polls); no orders, no auto-execution, no private/signed/order endpoints, no testnet/live trading, no production approval implied or granted, no runtime change; the validated signal was not re-tuned.
- `follow_up_implications`: The operator can run `.venv/bin/python scripts/run_trend_overlay.py` any time for the current defensive posture (weekly cadence matches the evidence design; the JSON artifact is ignored runtime state). If the founder wants the overlay visible on the Money Flow OS, scope a display-only panel phase with DASH-QA1 lockstep. Any change to lookback/vol-target/mode is a RE-TUNE and requires new TSMOM evidence first (the pin test enforces this). TREND-CARRY remains a separate recorded hypothesis with its FUND-EV2 cost constraints.

```yaml
research_log:
  phase: TREND-OVERLAY1
  date: 2026-06-11
  class: time_series_momentum
  outcome: context
  badge: defensive overlay deployed - signal only
  title: Trend Drawdown-Control Overlay Operationalized (read-only tool)
  finding: >-
    The TSMOM-EV1 defensive finding (bear drawdown 66% -> 17%, authored
    mixed - defensive, not profitable) is now a deployable read-only
    calculator: current per-asset trend state + vol-targeted target
    exposure on the latest closed public-mainnet candles. Live sample at
    deployment: all eight majors in downtrend - target FULLY FLAT.
  why: >-
    Deployment of an existing validated finding, not a new strategy test -
    no new hypothesis was evaluated and no parameter was re-tuned (the
    defaults are pinned by test to the committed TSMOM-EV1 train choice).
  worked: >-
    The reuse discipline - the tool imports the exact evidence-run
    computation rather than re-implementing it, so the signal cannot drift
    from what was validated; the disclaimer travels in every output and
    the text guard enforces the posture mechanically.
  didnt: >-
    Nothing failed; the optional OS panel was deliberately skipped (it
    would require non-trivial DASH-QA1 lockstep surgery for an ignored
    artifact) and is available as its own display-only phase.
  lesson: >-
    A defensive finding is only useful if the honest framing survives
    deployment: the tool states drawdown control, not alpha - including
    the absolute loss - on every surface, so the operator cannot mistake
    risk reduction for a profit signal.
  our_error: null
  our_error_note: >-
    None - one disclaimer wording was rejected by the trading-safety text
    guard during the build and rephrased; the guard worked as designed.
  changed: >-
    The TSMOM-EV1 finding moved from evidence to an operator tool
    (scripts/run_trend_overlay.py); re-tuning the deployed signal without
    new evidence now fails CI by construction.
  hardened_gate: deployed signals are pinned to their evidence config - re-tuning fails CI
  evidence_summary: docs/trend_overlay1_deployable_drawdown_overlay_summary.json
  evidence_doc: docs/trend_overlay1_deployable_drawdown_overlay.md
  analytics:
    - label: Live sample at deployment
      kind: value
      source: sample_reading
```

## 2026-06-11T21:30:00Z - FUND-SCALE1 - Scale Does Not Unlock The Carry: Own Flow Never Earns The Tiers And Impact Grows Faster Than Fixed Costs Amortize

- `decision`: (1) The size/fee axis FUND-EV2 sanctioned is now mapped with published, cited tier schedules (Hyperliquid 14d-weighted volume tiers T0-T6 with spot counted double; Kraken Pro 30d tiers) and both size effects modeled honestly: tier fees + amortizing fixed costs (helps) AND EXEC-EV1 square-root impact driven by the actual per-size traded notional (hurts). (2) Two honesty rules bind the map: a fee tier counts as ACHIEVED only if the strategy's OWN traded volume at that size reaches the published qualifying volume; and any cell whose single fill exceeds 10% of its candle's dollar volume is impact-implausible and cannot pass regardless of its modeled number. (3) Verdict: `carry_does_not_reach_viability_at_credible_scale` - the achieved-tier surface is negative at EVERY account size, so funding carry stays closed at every credible scale for this operator, not just at 10k retail. The retail verdict was reproduced (the 10k base-tier cell equals FUND-EV2's -6.5), never re-litigated.
- `scope`: `services/strategy_validation/fund_scale1.py` (cited tier tables, tiered cost models that move only the fee term, own-volume tier achievement, participation plausibility, computed viability band), additive seams in `fund_ev1.py` (`starting_equity`, max-fill participation/notional tracking; defaults byte-identical - FUND-EV1/EV2 suites untouched and green), `scripts/run_fund_scale1_evidence.py`, `docs/fund_scale1_*`, `tests/test_fund_scale1_evidence.py`, CI fast lane, aggregator view.
- `result`: The map (5 sizes x 5 tiers x 2 constructions, per-rung train-only config choice, full gate battery on achieved + candidate cells): hl_single OOS net is negative in EVERY cell - and the loss as % of equity GROWS with size (-0.065% at 10k -> -0.101% at 5M at tier 0; same shape at every tier) because impact rises while fees only fall with tiers the strategy cannot earn: at a $5M account the carry's own flow generates $1.8M weighted 14d HL volume vs $5M needed for even tier 1 (tiers 2-4 need $25M/$100M/$500M). The ONLY positive stripe in the whole map - Kraken 10 bps VIP (>$10M 30d) at sizes >=50k, +0.02-0.05% of equity - requires ~30x the strategy's own 30d spot volume AND fails impact plausibility (fills exceed 10% of thin early HL-spot-proxy candles): excluded from the band on both grounds, reported as "what it would take". The maker-bound line (all fills passive at base maker fees, zero spread paid, non-fill risk unmodeled - explicitly NON-GATEABLE) ceilings at +0.26% OOS (~0.8%/yr) falling to +0.23% at 5M: even perfect passive execution yields under 1%/yr on this OOS window. Gate battery on every achieved cell: fail (OOS net negative + leave-one-out ETH-drop negative at every size). 96 deterministic sims, fully cached and reproducible.
- `boundaries`: Research/evidence only. Public read-only inputs reused (no new fetches); published fee schedules cited; no orders, no private/signed endpoints, no testnet/live, no runtime or approval change. Maker-volume-share rebates require market-maker flow - out of scope, noted not modeled. Institutional execution tooling (cross-venue routing) could reduce the legged gap but was not assumed.
- `follow_up_implications`: The funding-carry hypothesis family is now closed on BOTH sanctioned axes: cost realism (FUND-EV2) and scale/fee tiers (FUND-SCALE1). What remains true and reusable: the gross funding stream is real in every regime, the cited cost machinery (fund_ev2/fund_scale1 models) and the own-volume tier-achievement rule now exist for any future phase that books funding as a component (TREND-CARRY pricing rule unchanged: carry credit at cited costs only, never gross). The only paths that could reopen carry are structural, not parametric: market-maker flow (rebate tiers), a venue fee regime change, or sub-candle atomic execution evidence - each would be a new phase with new citations, not a re-tune.

```yaml
research_log:
  phase: FUND-SCALE1
  date: 2026-06-11
  class: funding_carry
  outcome: fail
  badge: scale does not unlock it
  title: Funding Carry Scale & Fee-Tier Viability Map
  finding: >-
    The size/fee axis FUND-EV2 sanctioned, mapped with published tier
    schedules and honest impact scaling: the achieved-tier surface is
    negative at EVERY account size (10k-5M), and the loss as % of equity
    GROWS with size. The viable band is empty: verdict
    carry_does_not_reach_viability_at_credible_scale.
  why: >-
    Two compounding facts: the strategy's own flow never earns the fee
    tiers (a $5M account generates $1.8M weighted 14d HL volume vs $5M
    needed for tier 1, $500M for the tier that would matter), and impact
    grows with size faster than the only amortizing cost (the flat
    cross-venue settlement) shrinks. The lone positive stripe (Kraken
    10 bps VIP at >=50k) needs ~30x the strategy's own volume AND fails
    the 10%-participation plausibility rule.
  worked: >-
    The honesty rules - own-volume tier achievement and the participation
    plausibility cap kept the map from "passing" on tiers and fills the
    operator could never have; the 10k base-tier cell reproduced
    FUND-EV2's retail verdict exactly (not re-litigated); fees-down /
    impact-up monotonicity is test-pinned.
  didnt: >-
    Scale as the rescue. Bigger is WORSE on the achieved surface; even the
    explicitly optimistic, non-gateable maker bound (passive fills, zero
    spread paid) ceilings at ~0.26% OOS (~0.8%/yr) - a number that informs
    and closes, rather than tempts.
  lesson: >-
    The gross edge is real but capital/fee-gated, and the gate does not
    open with capital: carry turnover is too low to earn volume tiers, so
    "institutional fees" are a flow privilege, not a size privilege. The
    viable band on this data is empty; only structural changes (maker
    flow, fee regime, atomic execution) could reopen it - each new
    evidence, not a re-tune.
  our_error: null
  our_error_note: >-
    None this run - the axis was tested exactly as FUND-EV2 sanctioned it,
    with published schedules and the discipline guard intact; the map
    closed the question rather than flattering it.
  changed: >-
    The funding-carry family is closed on both sanctioned axes (cost
    realism, scale/fee tiers); tier-achievement-from-own-volume and
    participation plausibility join the standing cost-honesty toolkit;
    TREND-CARRY keeps its cited-cost pricing constraint unchanged.
  hardened_gate: fee tiers count only if the strategy's own flow earns them
  evidence_summary: docs/fund_scale1_size_fee_tier_viability_summary.json
  evidence_doc: docs/fund_scale1_size_fee_tier_viability.md
  analytics:
    - label: Size x fee-tier viability map (hl_single)
      kind: computed
      source: fund_scale1_viability_map
```

## 2026-06-11T19:30:00Z - FUND-EV2 - Realistic Costs Recover Most Of The Drag And The OOS Edge Still Is Not There; Funding Carry Closes At Retail

- `decision`: (1) Cost assumptions in evidence phases must be CITED, never tuned to the verdict: FUND-EV2 re-prices the carry with named sources (Hyperliquid fee docs: perp taker 4.5 bps / spot taker 7 bps base tier; a one-shot public read-only l2Book calibration of all eight books, committed with provenance; Kraken Pro base tier spot taker 40 bps for the cross-venue leg, Coinbase Advanced base tier worse at 60 bps; flat 2 USDC/fill cross-venue settlement) and publishes a COST-SENSITIVITY SWEEP so "did we just assume it cheaper?" is auditable. (2) The discipline guard is binding: the OOS edge dies at cost scale 0.75 - BELOW the cited realistic level (positive only at 0.25-0.5x, implausibly cheap) - so the verdict is an honest fail and there is NO FUND-EV3 cost tweak: funding carry is CLOSED at 10k retail size. (3) Cross-venue spot (the "cheaper deeper books" intuition) is closed by retail FEES, not by depth: 115-119 bps round-trip vs 33-51 bps single-venue; the 14-day-cadence cross-venue configs never clear the entry bar even once.
- `scope`: `services/strategy_validation/fund_ev2.py` (cited per-venue cost models with sweep scale, gate v2 wrapper with breakpoint + fragility qualifier), additive seams in `fund_ev1.py` (optional leg_cost_model, per-config band, entry-margin selectivity with hold-while-favorable hysteresis; defaults byte-identical - FUND-EV1 suite untouched and green), `strategy_types.py` (fund_ev2_ prefix routes to the same funding_carry type/gate), `scripts/fetch_fund_ev2_l2book_calibration.py`, `scripts/run_fund_ev2_evidence.py`, `docs/fund_ev2_*`, `tests/test_fund_ev2_evidence.py`, CI fast lane, aggregator views.
- `result`: Gate verdict `carry_does_not_survive_realistic_costs_and_tail_oos` (reasons: OOS net carry negative, leave-one-out breaks). Measured books vs FUND-EV1's assumption: UBTC spot half-spread 0.08 bps vs the 7.5 bps modeled (~15x conservatism on the spot leg; USOL the thinnest at 2.37 bps). At cited costs the train-chosen config (hl_single cad14 top2; train +4.36%, Sharpe 8.6) lost -6.5 USDC OOS (Sharpe -0.60); the SAME config under FUND-EV1's model lost -161 OOS - realistic re-pricing recovered ~155 of OOS drag and still landed negative. Hindsight rows were OOS-positive (cad28: +16.6/+8.6, Sharpe ~1.1) but the train split honestly could not select them (the SEL-EV1/TSMOM overfit catch, third time). Selectivity worked as designed: cross-venue cad14 never entered (230 bps bar), regimes all positive full-window (bear +91 - the FUND-EV1 regime bleed fixed), stressed tail inside limits (DD 3.1% vs 8%; legged gap exposure 30% of equity = 7.1% modeled gap loss at the worst candle). Leave-one-out mixed: drop-ETH negative, drop-SOL +70 (SOL was the drag). Walk-forward both folds positive (+124.5/+4.7). Sweep (adaptive, trade counts visible): OOS +40.6/+55.7 at 0.25/0.5x, -1.5 at 0.75x, -6.5 at 1.0x, dead by 3x; breakpoint 0.75.
- `boundaries`: Research/evidence only. Public read-only data (fundingHistory, candleSnapshot, l2Book); no orders, no private/signed endpoints, no testnet/live, no runtime or approval change. l2Book calibration is point-in-time, not window history (sweep covers the uncertainty); spot borrow + liquidation mechanics unmodeled.
- `follow_up_implications`: Funding carry standalone is closed at retail size - both constructions, with the failure now demonstrated at cited realistic costs, not assumed ones. TREND-CARRY (TODO) inherits two constraints: any funding paid to the trend short side must be priced with the FUND-EV2 cited cost model (not gross funding), and the synthesis only makes sense if the trend book ALREADY holds the short for its own reason (carry cannot pay for entries it could not afford standalone). The fund_ev2 cost seams are reusable for that test. A larger account (fee tiers, maker fills) or a venue fee change would be NEW evidence - a different phase with different citations, not a re-tune of this one.

```yaml
research_log:
  phase: FUND-EV2
  date: 2026-06-11
  class: funding_carry
  outcome: fail
  badge: edge dies below realistic costs
  title: Funding Carry Re-Test At Cited Realistic Costs
  finding: >-
    The honest re-test of FUND-EV1's fail: cited per-venue costs (fee docs +
    live l2Book calibration) replace the widest-tier guess, entries turn
    selective (2x round-trip margin), holds lengthen. The OOS edge still is
    not there - it dies at 0.75x the cited cost level, below realistic, and
    leave-one-out breaks. Cross-venue spot is closed by retail fees alone
    (115 bps round trips vs 33 single-venue). Funding carry closes at retail.
  why: >-
    What survives realistic friction is the bull-window funding; the OOS
    window's compressed funding (2026 bear) leaves single-digit bps over
    33-bps round trips, and the train split cannot find the rows that
    happened to stay positive (cad28 hindsight +16.6 OOS) - in-sample Sharpe
    8.6 picked a config that lost OOS, the third time this log catches that.
  worked: >-
    The discipline - cited costs with a published sensitivity sweep made
    "did we assume it cheaper?" auditable (breakpoint 0.75x, positive only
    at 0.25-0.5x); selectivity fixed FUND-EV1's regime bleed (bear-regime
    net +91); the additive cost seams left FUND-EV1's suite byte-identical.
  didnt: >-
    The capturable edge at 10k retail. Realistic re-pricing recovered ~155
    of the 161 USDC OOS drag on the same config - and the result was still
    negative. Retail CEX fees (Kraken 40 bps taker base tier) close the
    cross-venue construction before depth matters.
  lesson: >-
    Distinguish the gross edge (real: funding collected positive in every
    regime) from the capturable edge (absent at this size): when a re-test
    must cite its costs and publish the breakpoint, "maybe cheaper costs fix
    it" stops being an open question - here the answer is no, and the next
    cost-tweak phase is forbidden by design.
  our_error: >-
    FUND-EV1's spot-leg cost (widest mid-alt tier, 7.5 bps half-spread under
    conservative) overstated the measured HL spot books ~15x (UBTC 0.08 bps
    live) - deliberate, documented conservatism, but ours, and it overstated
    the cost share of the FUND-EV1 verdict. Stated plainly: correcting it
    does NOT flip the verdict (breakpoint 0.75 < 1.0), so FUND-EV1's fail
    conclusion stands as a real strategy failure at retail size.
  changed: >-
    Cost realism became a first-class, cited, sweep-audited input
    (per-venue leg cost models on the funding_carry simulator, additive and
    regression-safe); funding carry is recorded closed at retail; TREND-
    CARRY inherits the cited cost model and the "carry cannot pay for
    entries it could not afford standalone" constraint.
  hardened_gate: cost assumptions must be cited and sweep-audited, never tuned to the verdict
  evidence_summary: docs/fund_ev2_realistic_cost_carry_evidence_summary.json
  evidence_doc: docs/fund_ev2_realistic_cost_carry_evidence.md
  analytics:
    - label: Realistic-cost headline (OOS)
      kind: computed
      source: fund_ev2_realistic_headline
    - label: Cost-sensitivity sweep + breakpoint
      kind: computed
      source: fund_ev2_cost_sweep
```

## 2026-06-11T16:30:00Z - FUND-EV1 - Funding Carry Is A Bull-Regime Income Stream That Costs And The Bear Eat; The Real Tail Is The Legged Fill

- `decision`: (1) Delta-neutral funding carry is its own strategy type (`funding_carry`, prefix `fund_ev1_`) with its own gate: net funding AFTER ALL COSTS positive out-of-sample (chronological 70/30 + anchored walk-forward thirds), NOT bull-only (bear+neutral net must be positive), leave-one-out robust, and tail drawdown inside documented limits (OOS <= 5%, stressed <= 8%) - judged on Sharpe + max drawdown, never on gross funding collected, and never by the price-rule gates. (2) Funding history is now a first-class committed data input: public read-only Hyperliquid `fundingHistory` hourly rates aggregated to daily sums per coin, committed with provenance + sha256 in `docs/fund_ev1_funding_data_snapshot_summary.json` (raw hourly + HL spot candles stay as documented ignored artifacts). (3) The single-venue HL construction (short perp + long HL spot: BTC/ETH/SOL via Unit + native HYPE) is the primary build; cross-venue spot and the flip-side book (long perp + short spot) remain documented extensions - flip rows assume unmodeled spot borrow and are upper bounds.
- `scope`: `services/strategy_validation/fund_ev1.py` (two-leg simulator with pending-fill queue, funding accrual, trailing-funding tilt, regime/tail analytics, gate), `strategy_types.py` (additive fourth route), `scripts/fetch_fund_ev1_funding_snapshot.py`, `scripts/run_fund_ev1_evidence.py`, `docs/fund_ev1_*`, `tests/test_fund_ev1_evidence.py`, CI fast lane, research-log aggregator views.
- `result`: Gate verdict `carry_does_not_survive_costs_and_tail_oos` (reasons: OOS net carry negative, walk-forward fold C negative, every leave-one-out drop negative). Train (bull, funding 8-14%/yr): +4.23%, Sharpe 7.2, ultra-smooth. OOS (2026 funding-compressed bear): -33 USDC (-0.32%, Sharpe -1.55) - gross OOS funding was still positive (+50) but conservative two-leg friction ate more than all of it. Full window: net +392 vs gross +560; costs ate 168 (30.0% of gross) at 10k size. Non-bull regime net was actually positive (+160) and tail structure with clean fills is tight (max residual delta 0.18%, stressed-run DD 0.92% vs 8% limit) - the carry fails on OOS robustness, not on the neutral-book mechanics. The REAL tail: a one-day legged fill leaves up to 47.9% of equity unhedged, and against the window's worst candle (23.6%, HYPE) that is a modeled 11.3% equity gap loss - the steamroller is execution, not funding. Funding-inversion bleed during signal lag is bounded (worst SOL -17). PnL reconciles per symbol (K-019); no-lookahead probes pass (leaky reader caught).
- `boundaries`: Research/evidence only. Public read-only data; no orders, no private/signed endpoints, no testnet/live, no runtime or approval change. Modeled depth; daily funding accrual approximation; spot borrow and liquidation mechanics unmodeled (documented).
- `follow_up_implications`: TREND-CARRY synthesis hypothesis recorded (TODO): TSMOM-EV1 showed the trend short side defends drawdown in bears but loses money; funding could pay that short side - but FUND-EV1 shows funding compresses exactly when the bear arrives, so the combined book must be tested on net carry through the same regime, not on bull-window funding. Any deployable carry also needs the legged-fill gap risk engineered away (atomic or near-atomic two-leg execution) before size matters. In-phase correction recorded honestly: the first leg-lag stress implementation only re-priced the lagged leg without holding the one-leg exposure; it was caught and rebuilt (pending-fill queue) before any conclusion was drawn.

```yaml
research_log:
  phase: FUND-EV1
  date: 2026-06-11
  class: funding_carry
  outcome: fail
  badge: costs + bear eat the carry
  title: Delta-Neutral Funding Carry (HL perp + HL spot)
  finding: >-
    Short the perp, hold the spot, collect funding. Real in the bull (train
    +4.2%, Sharpe 7.2) but FAILS the gate: OOS net carry -33 USDC in the
    funding-compressed 2026 bear, walk-forward fold C negative, and every
    leave-one-out drop negative. Costs ate 30% of gross at 10k size.
  why: >-
    Funding is a bull artifact on this data: 8-14%/yr while the market rose,
    compressed or inverted (SOL -6%/yr) once the bear arrived - exactly when
    a hedged book would matter. What survives compression, conservative
    two-leg friction then eats: gross OOS funding was +50, net was -33.
  worked: >-
    The method - exact funding accrual against committed public daily sums,
    two-leg book that reconciles per symbol (K-019), tight neutrality with
    clean fills (max residual 0.18%), and a legged-execution stress that
    holds REAL one-leg exposure instead of assuming it away.
  didnt: >-
    The carry as a standalone OOS edge at 10k size - and legged execution
    is the true steamroller: one slow hedge leg leaves ~48% of equity
    unhedged for a day, a modeled 11.3% gap loss at the window's worst
    candle (23.6%).
  lesson: >-
    Funding carry is bull-regime income, not an all-weather structural
    edge: it dies in the same regime where the trend short side earns its
    keep. Judge carry net-of-costs OOS and through the tail - gross funding
    collected is a vanity number.
  our_error: null
  our_error_note: >-
    Caught in-phase: the first leg-lag stress only re-priced the lagged
    fill without holding the one-leg exposure; rebuilt with a pending-fill
    queue before any conclusion was drawn.
  changed: >-
    Fourth strategy-type route (funding_carry) with its own net-OOS + tail
    gate; funding history became a committed first-class data input with
    provenance; TREND-CARRY (trend short side paid by funding) queued as
    the synthesis hypothesis with this phase's regime caveat attached.
  hardened_gate: carry is judged net-of-costs OOS through the tail, never on gross funding
  evidence_summary: docs/fund_ev1_delta_neutral_carry_evidence_summary.json
  evidence_doc: docs/fund_ev1_delta_neutral_carry_evidence.md
  analytics:
    - label: Net carry headline (OOS, conservative friction)
      kind: computed
      source: fund_ev1_carry_headline
    - label: Tail + leave-one-out
      kind: computed
      source: fund_ev1_tail_and_loo
```

## 2026-06-11T14:00:00Z - TSMOM-EV1 - Vol-Targeted Trend Beats Holding A Falling Market, Not Zero; A Relative Pass Must Carry Absolute Qualifiers

- `decision`: (1) Time-series momentum is its own strategy type (`time_series_momentum`, prefix `tsmom_ev1_`) with its own gate: risk-adjusted (Sharpe + max drawdown) versus EQUAL-WEIGHT BUY-AND-HOLD, out-of-sample, post-conservative-friction - never the selection random-benchmark gate, never the per-symbol breadth gate. (2) Volatility targeting + equal risk budgets (risk parity) on the eight liquid majors is the specific fix for the ZEC-class failure - the highest-vol name cannot dominate the book by construction. (3) A RELATIVE gate pass is not allowed to read as profit: the gate output carries non-failing honesty qualifiers, and this phase's relative pass (strategy OOS Sharpe -1.48 vs buy-hold -1.81 in a -62% bear window) is authored `mixed`, not `pass`.
- `scope`: `services/strategy_validation/tsmom_ev1.py` (signal, vol targeting, mark-to-market simulator, benchmarks, gate), `strategy_types.py` (additive third route), `scripts/run_tsmom_ev1_evidence.py`, `docs/tsmom_ev1_*`, `tests/test_tsmom_ev1_evidence.py`, CI fast lane.
- `result`: Gate verdict `beats_buy_hold_risk_adjusted_oos` WITH qualifiers (`oos_absolute_sharpe_not_positive_relative_edge_only`, `oos_absolute_return_negative_defensive_value_only`). Train-only choice picked lb30/vt20/long-only (train Sharpe 2.21 vs buy-hold 1.24). OOS: strategy -12.2% / Sharpe -1.48 / DD 16.6% vs buy-hold -61.7% / -1.81 / DD 65.7%. Edge survives both walk-forward folds (+1.16, +0.41) and all eight leave-one-out drops (+0.20..+0.56). Trend timing adds value over vol-targeted beta (-1.48 vs -1.89) and the random long/flat median (-2.00), but does not beat the best random seeds (max -1.12). Hindsight-best long/short configs had positive OOS Sharpe (+0.22) but train choice honestly picked long-only - and perp funding is unmodeled, so long/short rows are upper bounds. Per-symbol PnL reconciles to net (K-019 lesson); no single name dominates (max share DOGE ~34%, LOO robust).
- `boundaries`: Research/evidence only. No runtime, strategy-rule, order, testnet, live, or production-approval change. Modeled depth, not real. Perp funding not modeled. 10,000 USDC basis.
- `follow_up_implications`: Trend's demonstrated value on this data is DEFENSIVE (drawdown reduction in a bear), not positive return. If anything advances toward paper observation, it advances as a defensive overlay hypothesis, with funding modeled first for any long/short variant. Relative gates must always carry absolute qualifiers (now a standing rule).

```yaml
research_log:
  phase: TSMOM-EV1
  date: 2026-06-11
  class: time_series_momentum
  outcome: mixed
  badge: defensive, not profitable
  title: Volatility-Targeted Time-Series Momentum (liquid majors)
  finding: >-
    Trend done right - vol targeting + risk parity on eight liquid majors,
    judged risk-adjusted vs buy-and-hold OOS after friction. The relative bar
    PASSED: Sharpe -1.48 vs -1.81 and drawdown 16.6% vs 65.7% in a -62% bear
    window, surviving walk-forward and all leave-one-out drops. But the
    strategy itself still lost 12.2% OOS - defensive value, not profit.
  why: >-
    The OOS window was a severe bear; the strategy's edge came mostly from
    being flat (vol-targeted long-only goes to cash when trends die), plus
    real but modest timing value over vol-targeted beta (-1.48 vs -1.89).
    Absolute OOS Sharpe stayed negative, and the best random long/flat seeds
    (max -1.12) still beat it - so the timing signal is weak, not decisive.
  worked: >-
    The risk machinery - vol targeting + equal risk budgets eliminated the
    ZEC-class concentration by construction (max name share ~34%, all eight
    leave-one-out drops keep the edge); per-symbol PnL reconciles to net;
    train-only choice honestly refused the hindsight-best long/short configs.
  didnt: >-
    Trend as a profit source on this data. Long-only TSMOM lost money OOS;
    the hindsight long/short rows that made money are upper bounds because
    perp funding is unmodeled - and the train split could not have chosen
    them anyway.
  lesson: >-
    A relative gate (vs buy-and-hold) can pass while the strategy loses
    money. Relative passes must carry absolute-performance qualifiers, and
    "beats a collapsing benchmark" must never be read as edge.
  our_error: null
  our_error_note: >-
    None this run - the gate was built with the qualifiers from the start,
    and the authored outcome stays mixed despite the technically-green gate.
  changed: >-
    Third strategy-type route (time_series_momentum) with its own
    buy-hold risk-adjusted gate; standing rule that relative gates carry
    absolute qualifiers; trend is reframed as a defensive-overlay hypothesis,
    not a return source.
  hardened_gate: relative passes carry absolute-performance qualifiers
  evidence_summary: docs/tsmom_ev1_vol_targeted_momentum_evidence_summary.json
  evidence_doc: docs/tsmom_ev1_vol_targeted_momentum_evidence.md
  analytics:
    - label: Risk-adjusted headline (OOS, conservative friction)
      kind: computed
      source: tsmom_ev1_risk_adjusted_headline
    - label: Leave-one-out Sharpe edges
      kind: computed
      source: tsmom_ev1_leave_one_out
```

## 2026-06-11T12:00:00Z - DASH-QASWEEP1 - Shakedown Before The Walkthrough; Fix Clean, Flag Risky

- `decision`: Before the investor walkthrough, drive the entire dashboard like a user (including with the 1-second refresh active, mocked offline), hold a zero-console-error bar, fix the clear UI bugs, and flag anything risky instead of guessing. Working and clean - never overstated: the chart/markers stay untouched and every safety label and honest verdict stays exactly as it is.
- `scope`: `apps/dashboard/evidence-dashboard.js` (idempotent focus-safe selects; expandable state-tracked Runtime Log rows; adaptive control-server polling with deterministic-mode probe skip), `evidence-dashboard.css` (min-content blowout fixes, stale tablet rules, restored <=1180 stacking), `tests/dashboard_qa/test_dashboard_smoke.py` (checks #11 refresh stability + #12 console/overflow hygiene), `docs/dash_qasweep1_*`.
- `result`: Seven issues fixed (1 blocker, 5 major, 1 minor), one flagged (K-034: native 404 per 60s probe without the control server - run the server for demos). Notable find: tablet/mobile stacking had been silently dead since DASH-IA1 because the appended base grid rule out-cascaded the legacy media blocks - caught only because the sweep measured horizontal overflow at multiple widths. Final sweep: zero issues, zero console errors; DASH-QA1 12/12.
- `boundaries`: UI/display only. Chart + markers untouched. No safety-label softening (the text guard caught and rejected one wording during RLOG1; nothing similar here). No runtime, strategy, data-source, order, testnet, or approval change.
- `follow_up_implications`: The sweep's techniques are now pinned as permanent checks (focused-select stability, open-log persistence, zero-console-error load, multi-width overflow). Appended CSS must respect the cascade - new base rules placed after media blocks silently kill responsive behavior; QA #12 now guards the symptom. For demos: control server on, dark theme, desktop width, connectivity for live candles.

## 2026-06-11T07:00:00Z - RLOG1 - Post-Mortems Are Authored, Auto-Joined, And Can Never Render Green By Accident

- `decision`: (1) Every research phase records a structured post-mortem as a fenced yaml `research_log` block in its Decision Log entry — verdict, why it failed, what worked / didn't, the lesson, whether the error was ours or the strategy's, and what it changed — with the honest outcome taxonomy (`fail`/`mixed`/`context`/`pass`) AUTHORED in the log, never inferred from a summary's status string. (2) A read-only deterministic aggregator (`scripts/build_research_log.py`) joins those blocks to the committed evidence summaries and `current_truth.json` and emits `docs/research_log.json`, which is the only thing the dashboard Research Log renders. (3) The naive `verdict || audit_verdict || gate_status || status` coloring is removed: a non-positive result can never render green, pinned by regression tests and a DASH-QA1 check.
- `scope`: `scripts/build_research_log.py` (+ `--check` CI drift guard), 12 backfilled blocks in this log (additive only; the factual record above each block is untouched), `docs/research_log.json` + `docs/research_log_schema.md`, dashboard render (`research-log` panel + JS + CSS), `tests/test_rlog1_research_log.py` + DASH-QA1 check #10, AGENTS.md post-task step.
- `result`: 13 entries (12 backfilled + this phase), newest-first, with per-phase analytics joined from the real summaries (EXEC-EV1 ZEC 132% / ex-ZEC −36k / 15-of-23 negative; SEL-EV1 2/50 random seeds + near-miss configs; SV2.3 −638k aggregate; GOAL-STRAT1 121/7/0). Lessons → hardened gates rail derives from authored `hardened_gate` fields. DASH-QA1 10/10; aggregator reproducible byte-for-byte.
- `boundaries`: Display + docs/tooling only. Read-only over committed docs. No runtime, strategy, data-source, order, testnet, or approval change.
- `follow_up_implications`: Research phases that skip their `research_log` block now fail CI (`build_research_log.py --check` drifts when the block lands later, and the AGENTS.md post-task step makes it explicit). When a phase ever earns `pass`, it must come from the authored field after founder review — the render will show green only then.

```yaml
research_log:
  phase: RLOG1
  date: 2026-06-11
  class: audit
  outcome: context
  badge: process upgrade
  title: Research Log Post-Mortems (process / tooling)
  finding: >-
    Not a strategy test. Turned the research history into structured,
    auto-joined post-mortems with an authored outcome taxonomy, so the
    institutional memory renders honestly and can never show green by
    accident.
  why: >-
    Raw status strings ("ready_for_founder_review", "complete") read as
    success even when the underlying result was a failure - the display layer
    needed an authored verdict, not an inferred one.
  worked: >-
    Auto-joining from records that already existed (Decision Log, committed
    summaries, current_truth) - no new data source and no hand-maintained
    page.
  didnt: >-
    Nothing material; the placeholder's naive status coloring was the defect
    being removed.
  lesson: >-
    Verdicts are editorial decisions and belong to the authored record;
    pipelines should join and render them, never invent them.
  our_error: >-
    The DASH-IA1 placeholder colored entries from raw status strings - an
    upbeat status could render green for a failed phase. Removed here and
    pinned by regression.
  changed: >-
    Every research phase now authors its research_log block (AGENTS.md
    post-task step) and CI guards docs/research_log.json against drift.
  evidence_summary: docs/rlog1_research_log_summary.json
  evidence_doc: docs/rlog1_research_log.md
```

## 2026-06-11T00:15:00Z - DASH-PT3 - Critical State In The Header; The Status Strip Becomes The Bottom Reference Band

- `decision`: The two always-relevant signals — is the runtime running, and is live trading off — move into the header as persistent pills (RUNTIME ACTIVE/IDLE from the existing control-server polling; LIVE DISABLED · NOT APPROVED static red). With those signals always visible, the dense status strip ("H1") stops occupying the top of the page and becomes the final full-width reference band after the Testnet footer, letting Global Filters lead the body. Rails are resized for content truth: Runtime Control must never truncate (wider right rail + overflow visible), the watchlist gets room to breathe, OKB is removed from the watchlist display (resolver policy untouched), and Daily Review loses its nested scroll.
- `scope`: `apps/dashboard/index.html` (header pills, banner relocation), `evidence-dashboard.js` (pill renderer off state.paperRuntimeControl; hidden-symbol filter applied at paperObservationBaseScannerRows), `evidence-dashboard.css` (pill styles, rail widths minmax(212px,252px)/minmax(300px,344px), overflow + max-height removals), DASH-QA1 #9 + static-asset guards in lockstep, `apps/dashboard/DESIGN.md`, `docs/dash_pt3_*`.
- `result`: DASH-QA1 9/9 green; static guards green; three themes zero page errors; OKB verified absent from the rendered watchlist; Runtime Control renders all content untruncated; chart and markers untouched.
- `boundaries`: Dashboard display/layout only. No runtime, strategy, data-source, order, testnet, or approval change; pt_rt1.py resolver policy untouched.
- `follow_up_implications`: The header pills read the same polled status as Runtime Control — if a future phase changes the control-server payload, renderTopStatusPills consumes control.running/control.status only. Any future symbol display exclusions belong in HIDDEN_DASHBOARD_SYMBOLS (display) — never in resolver policy without a separately scoped backend decision.

## 2026-06-10T23:30:00Z - DOC-LEAN1 - Rolling Changelog Window + Lean Pre-Task Reads

- `decision`: (1) Rotate the changelog: `CHANGELOG.md` becomes a recent rolling window (~20 entries, all new entries still written there; oldest roll into the archive past ~25 entries as part of post-task updates, CI-enforced), and `CHANGELOG_ARCHIVE.md` holds the full older history verbatim. Both are canonical — one complete history split for reading cost, not competing changelogs. (2) Replace the read-everything pre-task workflow with a lean current-state set read every task — AGENTS.md, CURRENT_TRUTH.md (TRUTH1 registry), 01_Current_Phase.md, the recent CHANGELOG.md, 05_Agent_Coordination.md, and the task-relevant component docs — demoting REPO_TREE/KNOWN_ISSUES/TODO/CHANGELOG_ARCHIVE/Command Center/Project Memory to consult-on-demand. The post-task UPDATE list is deliberately unchanged: reads are trimmed, write discipline is not.
- `scope`: `CHANGELOG.md` (rotated, 292 -> 20 entries + pointer), `CHANGELOG_ARCHIVE.md` (new, 272 entries verbatim), `AGENTS.md` (Pre-Task Workflow + Changelog Rules + required-docs list + not-a-substitute line), `tests/test_operational_docs.py` (archive existence/pointer/no-overlap/<=25-cap/lossless-shape guards), `docs/doc_lean1_*`.
- `result`: Rotation verified programmatically: 20 + 272 = 292 entry headings, none dropped or duplicated, recent+archive ordering equals the original, concatenated entry text byte-for-byte identical to the original entry region. Operational-docs guard green at 20 tests. Agent pre-task reading drops from ~1.2 MB of mandatory logs to a small current-state set.
- `boundaries`: Docs/tests only. No runtime, strategy, code-behavior, order, testnet, or approval change. No changelog history lost.
- `follow_up_implications`: Future post-task updates must keep `CHANGELOG.md` at or under ~25 entries by rolling the oldest entries verbatim into the TOP of the archive's entry list (preserving newest-first in both files) — the guard fails CI at 26+. Agents needing deep history read the archive on demand. If other logs (TODO/KNOWN_ISSUES) keep growing, the same rotation pattern can be applied in a later phase.

## 2026-06-10T22:30:00Z - DASH-IA1 - The OS Is Two Surfaces; The Museums Are Retired

- `decision`: Consolidate the dashboard from five tabs to two. The Money Flow OS is **Paper Trading** (the live desk, default tab) and **Research Log** (institutional memory of what has been tested). Historical Replay, The Lab (evidence-lab), and Strategy were museum surfaces — useful while research phases were live, now navigation noise — so their tabs AND their render/data-loading code are removed from the monolith. Evidence is renamed Research Log with a minimal data-driven placeholder; the full post-mortem view is the queued RLOG1 phase. Nothing is deleted from disk: every evidence pack, replay JSON, builder script, and doc stays as reference.
- `scope`: `apps/dashboard/index.html` (nav 5 → 2, three panels removed, research-log panel added, Must 1b reflow, Money Flow OS rename), `apps/dashboard/evidence-dashboard.js` (12,004 → 6,753 lines, −43.7%: retired-view code, old Evidence renderers, dead loaders/constants/state/registry entries removed; Research Log loader+renderer added), `apps/dashboard/evidence-dashboard.css` (−742 lines exclusive rules + reflow/research-log additions), `tests/dashboard_qa/test_dashboard_smoke.py` + `tests/test_dashboard_static_assets.py` (lockstep updates), `apps/dashboard/DESIGN.md`, `docs/dash_ia1_*`.
- `result`: DASH-QA1 9/9 green with the relocated lane-truth check (#7 now asserts the three current_truth active lanes on the Paper Trading status strip) and new retired-tabs-absent + reflow assertions; 96 blocking-lane tests green; three themes with zero page errors. Paper Trading behavior unchanged except the founder-requested reflow (full-width Global Filters bar, skinnier rails, full-width Testnet Transport footer below Daily Review) and the rename; the chart and markers are untouched. Three shared helpers that lived inside retired code regions but are used by Paper Trading (renderSelectWithoutAll, the chart pane constants, historicalConstantRows) were caught by orphan/undefined-identifier sweeps and restored beside their surviving callers.
- `boundaries`: Dashboard display only. No runtime, strategy, data-source, order, testnet, or approval change. No artifacts deleted. Hidden non-nav UAT legacy regression panels unchanged.
- `follow_up_implications`: RLOG1 builds the full Research Log post-mortem view on the `research-log` panel, reusing the placeholder's committed-summary loader as its data spine. Any future research phase should ship a committed `docs/<phase>_summary.json` with a `verdict`/`conclusion`/`status` field so it appears in the Research Log automatically. Retired-surface artifacts remain reviewable from disk; if a deep in-app view is ever wanted again it should be built inside Research Log, not as new top-level tabs.

## 2026-06-10T21:00:00Z - DASH-PT2 - Elevate Paper Trading To A Bolder Color-Coded Terminal, In Place

- `decision`: Reskin the Paper Trading terminal to a bolder, denser, color-coded exchange aesthetic (serious systematic-fund operator terminal) strictly IN PLACE: CSS-led over the existing DASH-PT1.2/1.3 structure, translating the founder prototype `docs/dash_pt2_prototype.html` into the theme-aware CSS variable system rather than hardcoding its dark-only hex values. Per-lane accent colors become a first-class visual language mapped to the `current_truth.json` active lanes: baseline blue, diagnostic comparator violet, MF-ORIG candidate amber, plus a crisp live/health accent and a testnet accent.
- `scope`: `apps/dashboard/evidence-dashboard.css` (DASH-PT2 token layer for dark/light/red-zone + an appended, clearly-fenced reskin section scoped to the Paper Trading view and intentionally-restyled top bar/nav), `apps/dashboard/evidence-dashboard.js` (display-only markup only: `paperObservationLaneChip` helper + four status-strip state classes; no data/filter/polling/handler change), `apps/dashboard/index.html` (cache-buster `dash-pt2-bold-terminal-20260610`), `apps/dashboard/DESIGN.md`, `scripts/capture_dash_pt2_screenshots.py`, `docs/dash_pt2_*`.
- `result`: All nine DASH-QA1 browser checks stayed green (two consecutive runs) with zero selector updates — every `#paper-observation-*` id and the guarded DOM structure survived verbatim. All three themes verified including the chart (the `--color-chart-*` tokens are untouched by design, so the TradingView palette is unchanged). Before/after Playwright screenshots committed under `docs/dash_pt2_screenshots/` for founder visual review (desktop+mobile dark, desktop light, desktop red-zone).
- `boundaries`: Dashboard display only. No runtime, strategy, data-source, order, testnet, or approval change. No other tab body restyled; shared top bar/nav chrome intentionally restyled. Safety labels stay prominent and DASH-QA1 check #9 still guards them.
- `follow_up_implications`: Future dashboard work must keep the DASH-PT2 tokens theme-aware (never hardcode hex that breaks light/red-zone or the chart palette) and keep lane colors consistent with the `current_truth.json` active lanes. If lanes change in a future founder-approved slate, update `PAPER_OBSERVATION_LANE_ACCENTS` and the token mapping together. Other tabs (Historical Replay, Evidence, The Lab, Strategy) may be elevated to the same language in a separately scoped phase.

## 2026-06-10T20:00:00Z - SEL-EV1 - Pivot To The Selection Hypothesis; The Random Benchmark Is The Bar

- `decision`: (1) Pivot strategy research from approach a (one universal rule per symbol — shown to fail via ZEC concentration) to approach b (cross-sectional selection: each period rank the universe on breakout/relative strength, hold the strongest name(s), rotate as leadership changes). (2) Supersede the planned GOAL-STRAT3 breadth gate — the breadth/anti-concentration lens is wrong for a strategy that is *meant* to concentrate; the ZEC lesson is reframed as a rotation/diversity check (a selection strategy that is secretly always one name is a single-name bet and fails). The breadth-gate idea is deferred, not deleted. (3) The honesty bar for any selection claim is BEATING A RANDOM-SELECTION BENCHMARK out-of-sample after conservative depth-aware friction — never raw PnL. (4) Add a `strategy_type` routing seam so approach a (`per_symbol`) and approach b (`cross_sectional_selection`) coexist as parallel research tracks (and later, potentially, parallel paper lanes) whose simulators/gates/evaluations can never cross-contaminate.
- `scope`: `services/strategy_validation/strategy_types.py` (routing seam; gates raise `StrategyTypeRoutingError` on cross-application; Week 2 lanes tagged `per_symbol`, behavior byte-identical regression-locked), `services/strategy_validation/sel_ev1.py` (point-in-time portfolio simulator + signals + random benchmark + baselines + diversity + OOS + late-entry + selection gate), `scripts/run_sel_ev1_selection_evidence.py` (offline evidence runner over SV2.2 candles), `tests/test_sel_ev1_selection_evidence.py` (15 deterministic tests, blocking CI lane), `docs/sel_ev1_*`.
- `result`: **`no_selection_skill_demonstrated`.** Train-only parameter choice picked `vol_adjusted_relative_momentum_lb40_top3_1d` (+54292 train net); it lost −10460 out-of-sample post-conservative-friction and beat only 2 of 50 matched-cadence random seeds (empirical p 0.96 — materially worse than random). Equal-weight buy-and-hold OOS was −2147. Rotation diversity was healthy (23 distinct symbols, max time share 0.13 — the machinery rotates; the choices just weren't better than chance). Walk-forward thirds combined test net was positive (+15809) but the chronological OOS + random-benchmark failures dominate. Late-entry decay was severe on the full period (+0 43832 → +1 17366 → +2 12334), confirming breakout selection is acutely timing-sensitive and reinforcing the RT-HISTSEED1 red flag.
- `boundaries`: Research/evidence only. Modeled (EXEC-EV1) depth, not real depth. No runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval. Per-symbol lane behavior and results unchanged.
- `follow_up_implications`: Any future selection-strategy claim must clear the SEL-EV1 gate (beat random p95 OOS post-friction, positive walk-forward OOS, adequate OOS sample, no single-name-bet flag) before founder review. The large in-sample-vs-OOS gap here is the canonical local example of why in-sample selection PnL is not evidence. If a later phase revisits per-symbol strategies, the deferred breadth gate applies there — and only there.

```yaml
research_log:
  phase: SEL-EV1
  date: 2026-06-10
  class: cross_sectional_selection
  outcome: fail
  badge: no selection skill
  title: Cross-Sectional Breakout Selection
  finding: >-
    Rank the universe each candle, hold the strongest 1-3, rotate. The bar was
    beating a matched-cadence random benchmark OOS after friction - it failed
    at p~0.96 (beat 2 of 50 random seeds).
  why: >-
    The config that looked best on the train split overfit. Out-of-sample it
    lost to a matched-cadence random benchmark - the ranking signal carries no
    forward information about which pair runs next.
  worked: >-
    The method. The no-lookahead simulator + random benchmark caught the
    overfit cleanly, and rotation diversity confirmed it genuinely rotated
    (23 names, no single-symbol bet) - so the null is trustworthy, not an
    artifact.
  didnt: >-
    The signal. Donchian breakout strength and vol-adjusted momentum rank
    symbols no better than chance. Late-entry decay was severe (+0 to +2
    candles, 43.8k to 12.3k) - even a real edge here would be hard to capture
    live.
  lesson: >-
    In-sample selection PnL is worthless as evidence. The only honest bar for
    "can you pick winners" is beating random selection OOS after friction.
  our_error: null
  our_error_note: >-
    None this run. The test was clean and caught its own overfit before we
    could be fooled - exactly the guardrail EXEC-EV1 taught us to build.
  changed: >-
    Random-benchmark + rotation-diversity are now the standard gate for any
    selection strategy.
  hardened_gate: beat random OOS, or it's nothing
  evidence_summary: docs/sel_ev1_selection_evidence_summary.json
  evidence_doc: docs/sel_ev1_selection_evidence.md
  analytics:
    - label: Random benchmark headline
      kind: computed
      source: sel_ev1_random_benchmark
    - label: Best OOS configs (near-misses; train-choice picked none of them)
      kind: computed
      source: sel_ev1_top_oos_configs
```

## 2026-06-10T16:00:00Z - EXEC-EV1 - Judge Edges Against Modeled Size-Aware Friction, Not Flat Bps

- `decision`: Add a depth-aware MODELED execution-friction layer on top of SV2.3's flat fee/slippage/adverse-gap terms and re-score the three Week 2 lanes, to test whether any edge survives realistic, size-aware friction. Keep it offline/deterministic so the model gates CI.
- `scope`: `services/execution_quality/exec_ev1.py` (model), `scripts/run_exec_ev1_execution_quality.py` (evidence runner reading SV2.2 candles from disk), `tests/test_exec_ev1_execution_quality.py` (deterministic, blocking lane), `docs/exec_ev1_*`. Three added terms: per-symbol liquidity-tier half-spread, size-aware square-root market impact (participation = notional / candle-dollar-volume liquidity proxy), fill-probability unfilled-chase. EXEC-EV1 scenarios are parented to the SV2.3 scenarios and inherit their terms verbatim, so EXEC-EV1 cost >= SV2.3 cost and net PnL <= SV2.3 net PnL (verified 0 violations / 621 rows).
- `result`: `mf_orig_1d_stage2_breakout_resistance_full_equity` survives base + conservative depth-aware friction (net +112k / +43k) but fails stress (net -52k); `money_flow_v1_2_baseline` and `avoid_low_rolling_range_20` fail all (already negative under SV2.3). The late-entry/entry-timing metric shows `mf_orig` cost rising with lateness (~+1.2 -> +15 -> +37 bps) — its edge sits at the signal and decays fast if entered late; the two failing lanes show negative late-entry cost (poor entries).
- `boundaries`: **Modeled depth, not real depth.** Liquidity is derived from historical candle volume; historical order-book depth does not exist (Hyperliquid public l2Book is a current snapshot only). Every output is an assumption layer. Research/evidence only — no runtime mutation, no strategy-rule change, no orders, no private/signed/testnet/live endpoints, no production or live approval. Partially addresses K-001 (modeled, not real); the gap is not closed.
- `follow_up_implications`: Future strategy candidates should be judged against this layer. A clearly-optional one-shot read-only public `l2Book` calibration could refine the assumed constants in a later phase but must never be part of a deterministic evidence run. The late-entry evidence directly informs RT-HISTSEED1 (below): the only lane with a surviving edge loses it fast when entered late, a red flag against historical seeding.

```yaml
research_log:
  phase: EXEC-EV1
  date: 2026-06-10
  class: friction
  outcome: fail
  badge: edge = ZEC artifact
  title: Execution-Quality Evidence Layer
  finding: >-
    Re-scored the 3 lanes under size-aware depth friction. The one positive
    lane (mf_orig) was 132% ZEC - remove ZEC and it is negative. Friction cuts
    it hard and it goes negative under stress.
  why: >-
    The one positive lane's entire profit was ZEC (132% of total). Strip ZEC
    and it is -36k; 15 of 23 symbols lose. It is a single-name bet, not a
    strategy - and in a thin alt where modeled friction is least trustworthy
    (likely understated), so the +112k is optimistic.
  worked: >-
    Building the friction model exposed the concentration, and a fairness
    check held - the same engine produced sensible baseline and spread
    numbers, so the negatives are real, not the engine crippling the strategy.
  didnt: >-
    Aggregate-PnL scoring. Every earlier pass that ranked lanes on total PnL
    rewarded the ZEC concentration instead of catching it.
  lesson: >-
    Aggregate PnL hides single-symbol bets. Thin alts where the liquidity
    proxy is unreliable are exactly where fake edges hide.
  our_error: >-
    Yes - and corrected. Earlier passes scored lanes on aggregate PnL with no
    hard concentration gate, which is how ZEC slipped through for so long.
    That was a measurement gap on our side, not just a bad strategy. Fixed via
    leave-one-out + breadth gates.
  changed: >-
    Leave-one-out (remove the top symbol, must stay positive) + breadth are
    now hard discovery gates. The mirage cannot recur.
  hardened_gate:
    - leave-one-out concentration gate
    - size-aware friction in the gate
  evidence_summary: docs/exec_ev1_execution_quality_evidence_summary.json
  evidence_doc: docs/exec_ev1_execution_quality_evidence.md
  analytics:
    - label: mf_orig concentration (base scenario)
      kind: computed
      source: exec_ev1_symbol_concentration
```

## 2026-06-10T16:00:00Z - RT-HISTSEED1 (FUTURE PHASE) - Startup Historical-Position Reconstruction, Iron-Walled

- `decision`: Record (NOT yet build) a future phase `RT-HISTSEED1` for startup historical-position reconstruction, status `position_live_in_historical`. It would reconstruct what positions a lane "would have held" entering historically, to seed a runtime view.
- `iron_rules` (non-negotiable): (1) reconstructed historical positions live in a SEPARATE bucket; (2) they are NEVER blended into forward synthetic PnL; (3) they are NEVER eligible for testnet or live transport.
- `gating_evidence`: EXEC-EV1's entry-timing cost shows `mf_orig` (the one lane with a surviving modeled-friction edge) loses ~+15 to +37 bps when entered 1-2 candles late — the edge decays fast at the signal. Small late-entry cost would argue seeding is not worth the runtime risk; the observed large cost argues seeding would erode the edge. Either way the bar to build this is high.
- `status`: Not started. Do not build without an explicit, separately-scoped founder decision. This entry exists only to capture the iron rules before any implementation.

## 2026-06-10T13:00:00Z - CI-CLEAN1 - Promote dashboard-qa, Split Informational, Lock Deps

- `decision`: (1) Promote `dashboard-qa` to a blocking CI lane now that it is consistently green on Ubuntu after DASH-QA1.1. (2) Split the single sequential `informational` job into two independent `continue-on-error` jobs `typecheck` and `full-tests` so a mypy failure cannot hide the full pytest suite's signal. (3) Add `pip-tools` to dev extras and commit `requirements-dev.lock` so every CI job installs reproducibly via `pip install -r requirements-dev.lock && pip install -e . --no-deps`.
- `scope`: `.github/workflows/ci.yml`, `pyproject.toml`, `requirements-dev.lock` (new), `docs/ci_clean1_*`, `KNOWN_ISSUES.md` (K-031 mypy debt with explicit promotion criterion).
- `result`: dashboard-qa now gates merges. Informational mypy + full pytest report independently. Lock pins 226 lines. Local validation: 66 safety tests + 9 browser tests green with the locked install.
- `boundaries`: CI/build config only. No runtime, strategy, order, testnet, slate, approval, dashboard-behavior, or test-logic changes. mypy strict mode is NOT silenced. The `browser` pytest marker is NOT folded into the main test run.
- `follow_up_implications`: Any future `pyproject.toml` dep change requires regenerating the lock: `pip-compile --extra dev --output-file requirements-dev.lock pyproject.toml`. mypy promotion to blocking is gated on K-031 being resolved through incremental typing — no silencing or relaxation.

## 2026-06-10T10:00:00Z - DASH-QA1 - Pin Documented Dashboard Regressions With A Browser-Smoke Suite

- `decision`: Add a deterministic Playwright browser-smoke suite under `tests/dashboard_qa/` that pins documented dashboard regressions (tab routing, terminal layout, chart-growth feedback loop, tab/blotter persistence, Audit-tab absence, three-active-lane Strategy view, 15m-paused timeframe filter, synthetic/testnet/no-live boundary labels). Source expected lane/timeframe values from `current_truth.json` (TRUTH1).
- `scope`: `tests/dashboard_qa/` (conftest + 9 checks), `pyproject.toml` (pytest-playwright dev dep + `browser` marker + default deselect), `.github/workflows/ci.yml` (`dashboard-qa` job), `docs/dash_qa1_*`, `KNOWN_ISSUES.md` (K-030 Chromium binary requirement).
- `result`: 3 consecutive green local runs (9 tests, ~23s each on macOS arm64). Default pytest discovery deselects the suite (no Chromium needed for the existing lanes). CI lane starts informational; promotes to blocking after 3 consecutive green CI runs.
- `boundaries`: Tests + harness + CI + docs only. No `data-testid` or other dashboard hooks added — every check resolves through existing selectors/ARIA. No runtime, strategy, order, testnet, slate, or approval state changed. `?disableLivePolling=true` ensures no live Hyperliquid network is contacted.
- `follow_up_implications`: Promotion to blocking requires 3 consecutive green CI runs (Ubuntu runner can surface flakes not seen on macOS). Any future dashboard work must keep the nine checks green or update the suite + this decision log.

## 2026-06-09T13:00:00Z - CI-SAFE1.1 - Install From Pyproject And Restore Fast Guards To Blocking

- `decision`: Fix the CI install step to use `pip install -e ".[dev]"` (pyproject.toml is the canonical install source — there is no `requirements.txt`) and restore four fast guard tests to the blocking lane.
- `scope`: `.github/workflows/ci.yml` install step (both jobs) and the blocking pytest invocation. Restored `test_pt_rt1_6_week2_slate.py`, `test_dashboard_static_assets.py`, `test_operational_docs.py`, `test_obs_os1_daily_review.py` to the blocking lane.
- `result`: CI now installs on a clean runner. Blocking lane local validation passes (159 tests across the blocking suite — 96+12+12+39).
- `boundaries`: CI configuration only. No safety logic, scanner, registry, runtime, strategy, orders, testnet eligibility, Week 2 slate, or approval state changed.
- `follow_up_implications`: None. The CI gate is now actually executable on first push.

## 2026-06-09T12:00:00Z - CI-SAFE1 - Make Trading Safety Regression Impossible To Merge Undetected

- `decision`: Add a GitHub Actions CI workflow and interlocking safety guards so any relaxation of a safety default, any positive live/production approval language, or any committed secret key material fails CI before merge.
- `scope`: Blocking CI lane: JS syntax, Python compile, registry --check, trading safety invariant tests, registry consistency, trading-safety text guards, secret hygiene scan, bundle hygiene, ruff on CI-SAFE1 modules. Informational lane: mypy, full pytest. See `.github/workflows/ci.yml` and `docs/ci_safe1_ci_gate_and_trading_safety_invariants.md`.
- `result`: 123 tests passing. All blocking checks clean on `master`. Pre-existing ruff debt in non-CI-SAFE1 modules tracked in KNOWN_ISSUES as tech debt.
- `boundaries`: Governance/enforcement only. No runtime behavior changed, no orders submitted, no private/signed/order endpoints used, no API keys loaded, no strategy production-approved, live trading remains not approved.
- `follow_up_implications`: Any change that weakens `RuntimeSafetyPolicy` defaults, adds positive approval language, commits key material, or drifts the registry will now fail CI. Full-repo ruff adoption is a separate lint-debt cleanup task.

## 2026-06-09T07:45:00Z - TRUTH1 - Truth Flows One-Directionally From Code Anchors

- `decision`: Make code the single source of truth for active lanes, timeframes, symbols, testnet eligibility, and approval boundaries. Truth flows: `services/paper_runtime/pt_rt1.py` + `core/config/settings.py` → `current_truth.json` (generated) → `CURRENT_TRUTH.md` (rendered) + dashboard (static copy, guarded by tests).
- `scope`: `scripts/export_current_truth.py` reads Python anchors and writes `current_truth.json`. `CURRENT_TRUTH.md` carries a human-readable rendering and a verbatim Machine Block. `tests/test_current_truth_registry.py` asserts no drift. `AGENTS.md` directs implementation prompts to reference `CURRENT_TRUTH.md` instead of re-embedding truth inline.
- `result`: Drift between docs and code now fails CI. The Machine Block in `CURRENT_TRUTH.md` is generated (not hand-authored) and guarded. Dashboard constants are checked against the registry by `tests/test_current_truth_consistency.py`.
- `boundaries`: Read-only export only. No runtime behavior changed, no orders submitted, no live or production approval granted, no strategy rules changed.
- `follow_up_implications`: Any anchor change in `pt_rt1.py` or `settings.py` requires re-running `export_current_truth.py`. Dashboard async-read wiring (TRUTH1 Must 4) is deferred — static constants are kept in sync by tests until that lands.

## 2026-06-08T13:02:00Z - SV2.3 - Make Evidence The Realistic Promotion-Facing Layer

- `decision`: Add SV2.3 as the latest realistic backtest layer and make Evidence default to SV2.3 rather than mixed legacy evidence packs.
- `scope`: SV2.3 reads SV2.2 Hyperliquid public-mainnet candles for the founder 23-symbol universe, replays the three Week 2 strategies across `1h`/`4h`/`1d`, keeps `15m` disabled, and uses promotion-facing `next_candle_open` fills only under base/conservative/stress execution-cost scenarios.
- `result`: The run completed 621 result rows. All three Week 2 strategies are `not_promoted_realistic_gate_failed` under the stricter realistic aggregate gate. Evidence now shows scenario, fee, slippage, and adverse-gap penalty columns from `docs/sv2_3_realistic_backtest_summary.json`; Historical Replay remains chart inspection.
- `boundaries`: SV2.3 is research/evidence only. It does not mutate PT-RT runtime artifacts, start/stop runtime, submit orders, call private/signed/order endpoints, use API keys, use testnet data as strategy truth, update PnL from testnet fills, approve production, or approve live trading.
- `follow_up_implications`: Treat SV2.3 as the promotion-facing baseline for future strategy review. Do not promote same-candle or next-close rows. Any canonicalization, new runtime lane, or production-testing phase must be separately scoped and founder-approved.

```yaml
research_log:
  phase: SV2.3
  date: 2026-06-08
  class: per_symbol_rule
  outcome: fail
  badge: fails realistic gate
  title: Realistic Backtest (next-open + execution cost)
  finding: >-
    All three Week 2 lanes fail the realistic aggregate gate. 621 result rows;
    deeply negative in aggregate across base/conservative/stress scenarios.
  why: >-
    Promotion-facing next-candle-open fills with base/conservative/stress fee,
    slippage, and adverse-gap assumptions. No lane survives the stricter
    realistic aggregate gate.
  worked: >-
    The layered-scenario design - the same lanes that look survivable under
    optimistic fills fail consistently once any realistic cost is applied,
    which is a clear, reproducible negative.
  didnt: >-
    The Week 2 lane rules themselves. None of the three produce positive
    aggregate PnL after realistic costs.
  lesson: >-
    Promotion review must always use next-open fills plus execution-cost
    scenarios; same-candle optimistic fills flatter everything.
  our_error: null
  changed: >-
    Evidence review defaults to the SV2.3 realistic layer; promotion decisions
    never use same-candle or next-close rows.
  evidence_summary: docs/sv2_3_realistic_backtest_summary.json
  analytics:
    - label: Realistic gate aggregate
      kind: computed
      source: sv23_aggregate_net
```

## 2026-06-08T09:08:40Z - PT-RT1.6.3 - Target XRP For Metadata Smoke After Current 24h Window

- `decision`: Add a blocked-symbol Hyperliquid testnet metadata resolver and constrain the next transport-only metadata smoke to `XRP`.
- `scope`: PT-RT1.6.3 resolves XRP/LINK/DOT/LTC/UNI/TRX/ZEC metadata from Hyperliquid testnet public `meta` when present, records absent-symbol reason codes, adds `reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke/`, and requires exact PT-RT1.6.3 approval plus `--pt-rt1-6-3-testnet-smoke-symbol XRP`.
- `result`: The code path is prepared and tested. The active `pt_rt1_6_week2_active` process is not restarted or mutated by this phase. The smoke should run only after the current 24h window and daily review generation.
- `boundaries`: The smoke is `testnet_transport_smoke_not_strategy_signal`, fixed 25 USDC, baseline/testnet plumbing only, no synthetic trade, no synthetic PnL update, no candidate/MF-ORIG testnet orders, no live trading, and no production strategy approval.
- `follow_up_implications`: If XRP is absent from testnet `meta` or fails size preflight, block locally before `/exchange`. If the smoke safely resolves/rejects/blocks, restart Week 2 unchanged with the existing three-lane slate.

## 2026-06-08T10:25:19Z - SV2.2 - Refocus Research Review On Fresh Public Mainnet Candles

- `decision`: Add a new SV2.2 research-refresh layer and make Historical Replay the default dashboard landing surface while the Week 2 paper runtime continues separately.
- `scope`: SV2.2 targets the founder 23-symbol resolved Hyperliquid universe across `1h`, `4h`, and `1d`, uses public mainnet `meta` and `candleSnapshot` only, writes committed Markdown/JSON refresh summaries, and writes ignored selected chart/readiness payloads under `reports/strategy_validation/sv2_2_research_refresh_dashboard_chart_data/`.
- `result`: The refresh completed 69/69 datasets with latest closes `1h=2026-06-08T10:00:00Z`, `4h=2026-06-08T08:00:00Z`, and `1d=2026-06-08T00:00:00Z`.
- `boundaries`: SV2.2 is chart/readiness refresh data, not canonical evidence-pack regeneration, not strategy approval, not active PT-RT runtime behavior, and not testnet/live behavior. No orders were submitted; no private/signed/order endpoints, API keys, testnet strategy truth, production approval, or live approval were introduced.
- `follow_up_implications`: Use SV2.2 to review recent market context in Historical Replay/Evidence/The Lab. If updated candidate metrics/trades are required, scope a separate backend evidence/replay regeneration phase rather than treating SV2.2 chart payloads as canonical evidence.

## 2026-06-08T10:57:45Z - SV2.2 - Correct Refresh Into Latest Week 2 Strategy Replay

- `decision`: Correct SV2.2 so it is not represented as a standalone `sv2_2_public_candle_refresh` replay strategy.
- `scope`: SV2.2 now refreshes Hyperliquid public-mainnet candles for the founder 23-symbol universe across `1h`, `4h`, and `1d`, then replays `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity` using `next_candle_open` and `next_candle_close` fill assumptions.
- `result`: The corrected run completed 69 refreshed datasets and 414 replay rows, wrote ignored replay chart/trade payloads under `reports/strategy_validation/sv2_2_week2_replay_dashboard_chart_data/`, and wrote ignored evidence-style pack directories under `reports/strategy_validation/sv2_2_latest_public_mainnet_week2_*_evidence_only/`.
- `boundaries`: SV2.2 remains research/evidence-style review only. It does not replace canonical SV2.0.2/SV2.1 evidence, mutate active PT-RT runtime artifacts, submit orders, call private/signed/order endpoints, use testnet strategy truth, approve production, or approve live trading.
- `follow_up_implications`: Historical Replay/Evidence/The Lab can use SV2.2 as the latest data/replay review source for the current three-strategy Week 2 slate. Any new strategy promotion, canonical evidence adoption, or runtime lane addition remains separately scoped.

```yaml
research_log:
  phase: SV2.2
  date: 2026-06-08
  class: data_prep
  outcome: context
  badge: data refresh
  title: Hyperliquid Public-Mainnet Candle Refresh
  finding: >-
    Refreshed the founder 23-symbol universe across 1h/4h/1d through
    2026-06-08 and replayed the three Week 2 strategies over the latest data.
    Research/evidence replay data only - not canonical evidence and not
    approval.
  why: >-
    Not a strategy test - this is the data substrate SV2.3 / EXEC-EV1 /
    SEL-EV1 evaluate against.
  worked: >-
    Apples-to-apples data for every later evidence layer; public-mainnet
    candles stayed the single strategy truth.
  didnt: >-
    Nothing material; an earlier broad refresh framing was corrected the same
    day into the Week 2 strategy replay scope.
  lesson: >-
    Keep the data refresh separate from the verdict layers so a data update
    can never be mistaken for a strategy result.
  our_error: null
  changed: >-
    SV2.2 became the shared candle source for SV2.3, EXEC-EV1, and SEL-EV1.
  evidence_summary: docs/sv2_2_hyperliquid_research_refresh_summary.json
  analytics:
    - label: Refresh coverage
      kind: computed
      source: sv22_refresh_stats
```

## 2026-06-08T06:29:37Z - LOG-OBS1 - Add Read-Only Runtime Log Visibility

- `decision`: Add an operator log-visibility layer instead of changing runtime behavior to address Week 2 tail/log confusion.
- `scope`: The dashboard control status API now exposes read-only `runtime_log_files` metadata, Paper Trading Runtime Control renders a Runtime Logs panel, and `scripts/watch_pt_rt1_runtime.py` provides terminal `--status`, `--latest`, and `--tail` modes.
- `result`: Operators can identify the active output scope, see file sizes and modified timestamps, copy exact `tail -n 50 -F` commands, and understand that `tail -F` waits for new appended lines while VS Code may show existing rows.
- `boundaries`: No runtime strategy/order behavior changed, no runtime was started or stopped by this phase, no orders were submitted, no production strategy was approved, and live trading remains not approved.
- `follow_up_implications`: Restart the local dashboard control server to load the new status API code; the active paper runtime can continue independently.

## 2026-06-06T22:24:15Z - PT-RT1.6 - Founder Overrides STRAT-PRUNE1 Slate For Week 2

- `decision`: Use the founder-selected three-lane Week 2 default paper slate: `money_flow_v1_2_baseline`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`.
- `scope`: PT-RT1.6 configures runtime/dashboard defaults to prefer `reports/paper_runtime/pt_rt1_6_week2_active/`, hides all other prior PT-RT lanes from default active scoring, and labels archived lanes as historical/research reference only.
- `boundaries`: `1h`/`4h`/`1d` remain active, `15m` remains paused, only the baseline can be testnet eligible, selected candidate/MF-ORIG lanes are synthetic-only, testnet lifecycle remains separate from synthetic PnL, no runtime was started, no orders were submitted, no production strategy was approved, and live trading remains not approved.
- `follow_up_implications`: Start the Week 2 run only after founder review using the documented PT-RT1.6 command or dashboard control server. Do not reintroduce STRAT-PRUNE1 relative-strength/Donchian lanes unless a later phase explicitly scopes them.

## 2026-06-06T19:47:41Z - STRAT-PRUNE1 - Prune Next Paper Slate

- `decision`: Recommend a smaller next paper-testing slate before another forward run, without implementing runtime lane changes in STRAT-PRUNE1.
- `scope`: Added `docs/strat_prune1_strategy_lane_pruning.md`, `docs/strat_prune1_strategy_lane_pruning_summary.json`, and focused guardrail tests. The review classified all 10 existing PT-RT lanes, reviewed GOAL-STRAT, STRAT-DISC, SOR, MF-ORIG, EV-AUDIT, and PT-RT evidence, and ranked keep/archive/add candidates by evidence quality, PnL/drawdown/OOS/sample/concentration/runtime simplicity/founder readability/difference from baseline.
- `result`: Recommended next slate: `money_flow_v1_2_baseline` as control and sole testnet-eligible lane, plus synthetic-only `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34`, `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20`, and `avoid_low_rolling_range_20`. Recommended archiving `avoid_low_rolling_range_50`, MF-ORIG reference lanes, and wildcard lanes from the default active paper slate.
- `boundaries`: STRAT-PRUNE1 did not implement new runtime lanes, mutate active runtime artifacts, change production Money Flow rules, submit live/testnet orders, call exchange/private/signed/order endpoints, use testnet strategy truth, approve production strategy, or approve live trading.
- `follow_up_implications`: If the founder accepts the slate, scope `PT-RT1.6 - Add Selected Paper-Test Candidate Lanes`. Keep `15m` paused, candidate lanes synthetic-only, and testnet eligibility baseline-only.

## 2026-06-06T18:18:30Z - GOAL-STRAT2 - Two Non-Existing Strategies Worth Paper Testing

- `decision`: Select two non-existing strategies worth founder paper-testing review while preserving research-only boundaries.
- `scope`: Added `services/strategy_validation/goal_strat2.py`, `scripts/run_goal_strat2_worth_testing.py`, GOAL-STRAT2 report/summary/candidate docs, and focused tests. The selector consumes GOAL-STRAT1 evidence, excludes current PT runtime lanes plus Money Flow/SOR/MF-ORIG/wildcard-adjacent families and entry models, applies a weaker paper-testing gate, and enforces family diversity.
- `result`: Selected `relative_strength_rotation_top_n_trend_strength_atr_trail_equity_5pct_sma200_20_0p34` and `trend_breakout_donchian_breakout_atr_trail_equity_5pct_sma200_20` as `candidate_for_founder_paper_testing_review`. The relative-strength candidate has positive active net PnL, PF 1.3477, max drawdown 30.17%, 534 trades, and both OOS checks positive. The Donchian candidate has positive active net PnL, PF 1.5712, max drawdown 16.37%, 945 trades, and mild negative OOS checks.
- `boundaries`: GOAL-STRAT2 did not mutate active PT-RT runtime artifacts, change production Money Flow rules, submit live/testnet orders, call private/signed/order endpoints, use testnet strategy truth, create execution artifacts, approve production strategy, or approve live trading.
- `follow_up_implications`: Founder may review these for a separately scoped paper-only lane phase. Do not route either candidate to testnet/live, do not treat either as production approval, and monitor symbol/timeframe/period concentration plus candle-only execution limitations.

```yaml
research_log:
  phase: GOAL-STRAT2
  date: 2026-06-06
  class: per_symbol_rule
  outcome: mixed
  badge: review-only candidates
  title: Two Non-Existing Strategies Worth Testing
  finding: >-
    From the GOAL-STRAT1 evidence, selected exactly two family-diverse
    candidates worth founder paper-testing review only - relative-strength
    rotation and Donchian breakout, both with ATR trailing exits. Neither is
    promoted.
  why: >-
    Both candidates carry real blockers - the relative-strength candidate has
    drawdown near the limit plus ZEC/timeframe/period concentration; the
    Donchian candidate has mildly negative OOS checks and concentration risk.
  worked: >-
    The weaker paper-testing gate surfaced reviewable ideas without
    pretending they passed the strict production-testing gate.
  didnt: >-
    Neither candidate cleared OOS plus concentration cleanly; both remain
    research-only.
  lesson: >-
    Candidate selection and candidate approval are different bars; labeling
    review material honestly avoids promotion creep.
  our_error: null
  changed: >-
    Established the review-only candidate tier between discovery and paper
    testing.
  evidence_summary: docs/goal_strat2_two_non_existing_strategies_summary.json
```

## 2026-06-06T17:42:15Z - GOAL-STRAT1 - Expanded Discovery Still Finds No Three Candidates

- `decision`: Complete the founder-requested durable autonomous discovery goal as honest full exhaustion rather than promote weak or overfit results.
- `scope`: Added `services/strategy_validation/goal_strat1.py`, `scripts/run_goal_strat1_discovery.py`, GOAL-STRAT1 report/summary/no-three-candidates docs, and focused tests. The run inventoried local public-mainnet selected replay JSON, accepted 49 datasets, quarantined ASTER 1d for insufficient history, tested 121 bounded candidate configurations across 7 families, and applied strict founder production-testing review gates.
- `result`: `three_candidates_were_not_found_without_overfitting_after_full_autonomous_discovery`. Passing candidates: `0`. Top near misses were volatility-expansion and Donchian-style trend variants with positive aggregate PnL, but they failed drawdown and both chronological/anchored out-of-sample checks. Lower-risk variants reduced drawdown but still failed OOS checks.
- `boundaries`: GOAL-STRAT1 did not mutate active PT-RT runtime artifacts, change production Money Flow rules, submit live/testnet orders, call private/signed/order endpoints, use testnet strategy truth, create execution artifacts, approve production strategy, or approve live trading.
- `follow_up_implications`: Do not promote any GOAL-STRAT1 result. A future discovery pass should first add longer non-overlapping OOS windows, stricter control-pocket slices, and execution-quality constraints before widening candidate parameters further.

```yaml
research_log:
  phase: GOAL-STRAT1
  date: 2026-06-06
  class: per_symbol_rule
  outcome: fail
  badge: 0 candidates
  title: Autonomous Strategy Discovery (121 configs, 7 families)
  finding: >-
    Zero strategies passed the production-testing gate. Near-misses
    (volatility-expansion, Donchian) failed drawdown and out-of-sample.
  why: >-
    Exit/risk/regime/OOS variations across Money Flow repair, trend/breakout,
    volatility, mean-reversion, relative-strength, and pairs families produced
    positive aggregate pockets, but every one failed drawdown, chronological +
    anchored OOS, concentration, or sample-size gates.
  worked: >-
    The bounded-search discipline: 121 configurations with explicit gates and
    no unbounded optimizer, so the exhaustion result is meaningful.
  didnt: >-
    Every per-symbol rule family tested. None survives the full gate.
  lesson: >-
    Widening the parameter search does not create an edge; it creates more
    overfit pockets for the gates to reject.
  our_error: null
  changed: >-
    Per-symbol discovery was de-prioritized; the selection hypothesis
    (SEL-EV1) became the next genuinely different idea to test.
  evidence_summary: docs/goal_strat1_strategy_discovery_summary.json
  analytics:
    - label: Search budget used
      kind: computed
      source: goal_strat1_stats
```

## 2026-06-06T17:35:00Z - STRAT-DISC1 - No Three Candidates Found Without Overfitting

- `decision`: Complete the first autonomous research-only strategy-discovery pass without promoting any strategy.
- `scope`: Added `services/strategy_validation/strat_disc1.py`, `scripts/build_strat_disc1_autonomous_discovery.py`, STRAT-DISC1 report/summary docs, and focused tests. The run inventoried local public-mainnet selected replay JSON, accepted 50 datasets, tested 12 bounded curated hypotheses, and applied strict founder production-testing review gates.
- `result`: `no_three_candidates_found_without_overfitting`. Passing candidates: `0`. Top near misses remain research-only because they failed drawdown, largest-loss, profit-factor, concentration, or market-structure gates.
- `boundaries`: STRAT-DISC1 did not mutate active PT-RT runtime artifacts, change production Money Flow rules, submit live/testnet orders, call private/signed/order endpoints, use testnet strategy truth, create execution artifacts, approve production strategy, or approve live trading.
- `follow_up_implications`: Do not promote any STRAT-DISC1 result. A future discovery pass should first add longer non-overlapping OOS windows and stricter control-pocket slices before widening ranges or families.

## 2026-05-19T22:11:42Z - SUBAGENTS1 - Add Read-Only Codex Review Subagents

- `decision`: Add project-scoped Codex subagents for bounded read-only runtime, dashboard, and quant review.
- `scope`: `.codex/agents/runtime_reviewer.toml`, `.codex/agents/dashboard_reviewer.toml`, `.codex/agents/quant_reviewer.toml`, `.codex/config.toml`, workflow docs, report docs, and TOML guardrail tests.
- `why`: Founder wants a stronger review workflow that separates PT-RT runtime safety, founder dashboard clarity, and paper-trade/quant signal quality from the main builder session.
- `result`: `implemented_subagents1_pending_validation`. Initial subagents are read-only by default and intended for triage/summarization, not parallel write-heavy implementation.
- `boundaries`: No production Money Flow rules changed, no runtime behavior changed, no dashboard behavior changed, no exchange endpoints were called, no orders were submitted, no evidence packs were regenerated, no live trading was approved, and no strategy was production-approved.
- `follow_up_implications`: Use `runtime_reviewer`, `dashboard_reviewer`, and `quant_reviewer` for the next bounded PT-RT review; the parent Codex session remains responsible for coordination, edits, validation, and handoff.

## 2026-05-17T18:25:00Z - PT-RT1.5.3 - Hyperliquid Testnet Size / Precision Hotfix

- `decision`: Resolve fixed-25-USDC Hyperliquid testnet order sizing from Hyperliquid testnet public metadata before submit.
- `scope`: PT-RT1.5.3 adds exact hotfix-smoke approval, testnet `asset_id` / `szDecimals` sizing, raw/formatted quantity and estimated-notional lifecycle fields, local invalid-size preflight, venue invalid-size reason codes, and dashboard lifecycle precision columns.
- `result`: One labeled `testnet_transport_smoke_not_strategy_signal` order used BTC testnet asset id 3 / `szDecimals=5`, formatted quantity `0.00033`, reached accepted/open, was canceled, and reconciled to no open order. It created no synthetic trade and did not update synthetic PnL.
- `boundaries`: Public mainnet remains strategy truth; candidate/MF-ORIG/wildcard/15m transport stays blocked; testnet fills do not update synthetic PnL; no production strategy or live trading approval was added.
- `follow_up_implications`: Continue or restart Week 1 runtime with PT-RT1.5.3 present and review the next fresh Money Flow v1.2 baseline-triggered lifecycle row. Production Money Flow rules remain unchanged.

## 2026-05-17T12:54:24Z - PT-RT1.5 - Reset Active Week And Gate Baseline-Only Testnet Lifecycle Rows

- `decision`: Reset the active Week 1 Paper Trading scope to `pt_rt1_5_week1_active`, archive prior runtime rows by default, keep `1h`/`4h`/`1d` active, keep `15m` paused, and move strategy signal evaluation to candle-close-only scheduling.
- `scope`: PT-RT1.5 hides archived open/closed/signal rows by default while preserving them under explicit archived review, starts fresh independent 10,000 USDC active-week ledgers, adds scheduler status for next/last `1h`/`4h`/`1d` evaluations, and keeps market refresh separate for watchlist/chart/unrealized/data-health display. The Paper Trading dashboard uses a compact scrollable watchlist beside a clarified Testnet Order Transport widget and adds a separate Testnet Order Lifecycle table.
- `testnet_policy`: Only scheduled closed-candle `money_flow_v1_2_baseline` synthetic `paper_opened` rows on active `1h`/`4h`/`1d` timeframes may create Hyperliquid testnet lifecycle/order-shape rows. The testnet notional is fixed at 25 USDC regardless of synthetic notional. Candidate, MF-ORIG, wildcard, duplicate, data-unavailable, hold, trim, close, 15m, and intrabar rows cannot trigger testnet transport. Testnet fills never update synthetic paper PnL.
- `why`: Founder review needed a clean Week 1 command center without old runtime clutter, less noisy 15m behavior, no continuous signal scanning, and a scoped baseline-linked testnet plumbing path that remains separate from strategy truth and candidate lanes.
- `result`: `implemented_pt_rt1_5_active_week_reset_and_baseline_testnet_lifecycle_gates`. Public mainnet candles remain strategy truth. Production Money Flow rules are unchanged. No strategy is production-approved. Live trading is not approved.
- `follow_up_implications`: Start or restart runtime under `reports/paper_runtime/pt_rt1_5_week1_active/` using PT-RT1.5 flags. Review the first active cycles for candle-close scheduler timing, duplicate closed-candle blocking, fixed-25 baseline-only lifecycle rows when baseline opens occur, candidate-lane transport blocks, and no-live/no-production boundaries.

## 2026-05-17T15:17:31Z - DOCS-OB2.1 - Make Markdown Current-Truth First

- `decision`: Refresh repo Markdown and Obsidian current-truth surfaces around PT-RT1.5.1 Paper Trading as the active operating surface, while preserving older UAT/PT/SV reports as audit/history.
- `scope`: README, architecture, strategy, dashboard docs, command center, current phase, project memory, maps, strategy register, known issues, TODO, operational-doc tests, and selected old phase reports. Current visible dashboard tabs are `Paper Trading`, `Historical Replay`, `Evidence`, `The Lab`, `Audit`, and `Strategy`.
- `current_truth`: PT-RT1.5.1 is complete; active Week 1 timeframes are `1h`, `4h`, and `1d`; `15m` is paused; public Hyperliquid mainnet candles are strategy truth; synthetic paper ledgers are independent 10,000 USDC lanes; only fresh post-start Money Flow v1.2 baseline opens can trigger fixed 25 USDC Hyperliquid testnet plumbing when gates pass; candidate/MF-ORIG/wildcard lanes are synthetic-only; testnet fills never update synthetic PnL.
- `why`: Founder review found stale UAT/PT/SV wording and phase chronology made it hard for humans and agents to know what is current.
- `result`: `implemented_docs_ob2_1_current_truth_refresh_pending_validation`.
- `follow_up_implications`: Future docs should keep current summaries at the top, mark old reports historical instead of deleting them, and keep PT-RT forward observation, SV2 evidence, dashboard display filters, SOR/MF-ORIG research, and testnet plumbing separate. This decision changes no strategy/runtime/order behavior and approves no live or production trading.

## 2026-05-17T11:51:26Z - PT-RT1.4.1 - Verify Active-Week Runtime Cutover Before Daily Review

- `decision`: Treat the old `reports/paper_runtime/pt_rt1_1c_24h_dry_run/` artifact set as pre-PT-RT1.4 burn-in for active Week 1 scoring because it continued producing 15m synthetic opens after the PT-RT1.4 cutover.
- `scope`: PT-RT1.4.1 reads ignored runtime artifacts, stops/retires the old running process, starts a fresh active-week runtime under `reports/paper_runtime/pt_rt1_4_1_active_week/`, and commits only the daily founder review pack at `docs/pt_rt_week1_day_summary.md` plus compact JSON. Runtime artifacts remain ignored and uncommitted.
- `why`: Founder review required proof that 15m was actually paused in the runtime, not only in dashboard code. Artifact inspection found 79 retired-runtime 15m `paper_opened` rows after the cutover timestamp.
- `result`: `active_runtime_cutover_verified_after_restart`. The restarted active runtime reported active timeframes `1h`, `4h`, `1d`, disabled timeframe `15m`, 0 active 15m rows, and 0 active 15m opens in its first artifact cycle. The daily review decision is `Week 1 paper observation may continue`.
- `follow_up_implications`: Daily Week 1 reviews should use `docs/pt_rt_week1_day_summary.*` and `reports/paper_runtime/pt_rt1_4_1_active_week/`. The older `pt_rt1_1c_24h_dry_run` directory remains available as legacy burn-in context only. This decision does not change Money Flow production rules, add or tune strategies, approve paper/live/production, submit live/testnet orders, enable testnet order transport, call private/signed/order endpoints from strategy truth, use API keys, use testnet data as strategy truth, regenerate historical evidence packs, or add SOR/fanout/CBBO.

## 2026-05-17T08:45:23Z - OB-CLEANUP - Current-First Obsidian Brain And Coordination Split

- `decision`: The Obsidian brain should be current-first: Paper Trading / PT-RT, SV2.x evidence, SOR/MF-ORIG research, and founder dashboard review are the active path; UAT and older platform phases remain preserved as historical plumbing context.
- `scope`: `money-flow/00 Maps/Phase Timeline.md` is rewritten around current tracks with UAT moved to a historical archive pointer. `money-flow/05_Agent_Coordination.md` now has separate Active Work and Finished Work sections. Duplicate command-center and phase-timeline entrypoints stay as pointer notes only. Current-truth notes use Paper Trading as founder-facing language and remove stale founder-chrome references to manual report loading/evidence-loaded status text.
- `why`: Founder review found the Phase Timeline too UAT-heavy and several Obsidian pages outdated or confusing for handoff.
- `result`: `implemented_current_first_obsidian_cleanup`.
- `follow_up_implications`: Future agents should add themselves under Active Work before substantial edits and move/update the row under Finished Work when done. Historical decision entries remain append-only even if their old UI wording is no longer current. This cleanup changes no code behavior, evidence packs, strategy rules, order endpoints, API-key use, live approval, or SOR/fanout/CBBO behavior.

## 2026-05-17T03:08:07Z - PT-RT1.2.1 - Use Runtime Trade Ledger For Closed Trades And Runtime Equity For Lane Comparison

- `decision`: The Paper Observation dashboard must use ignored PT-RT `trades.jsonl` as the display source for Closed Synthetic Trades and `paper_runtime_state.realized_equity_by_lane` as the display source for current Strategy Lane Comparison equity.
- `scope`: `apps/dashboard/evidence-dashboard.js` now loads `trades.jsonl`, renders closed synthetic trade entry/exit/price/quantity/PnL/equity fields from those rows, and overlays runtime realized equity/open count/closed count/derived net PnL onto static lane definitions.
- `why`: Founder observed Closed Synthetic Trades missing entry/exit/PnL fields and Strategy Lane Comparison still showing starting equity after recent trades. Root cause: `summary.json.closed_trades` can be empty while the complete synthetic trade ledger lives in ignored `trades.jsonl`, and `strategy_lanes` is static lane config rather than current ledger state.
- `result`: `implemented_dashboard_runtime_ledger_display_truth`. The dashboard display now follows the synthetic public-mainnet paper ledger artifacts without changing runtime behavior.
- `follow_up_implications`: Future PT-RT dashboard changes should distinguish static config fields from runtime ledger state. This decision does not change Money Flow production rules, approve paper/live trading, regenerate evidence packs, submit orders, call private/signed/order endpoints, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

## 2026-05-17T03:19:49Z - PT-RT1.2.1 - Keep Dashboard Chrome Compact And Hide Sparse Closed-Trade Rows

- `decision`: The founder dashboard should keep the primary title, logo, tabs, and Load JSON control in one sticky top bar, and Closed Synthetic Trades should display only ledger-complete closed-trade rows.
- `scope`: `apps/dashboard/index.html` and `apps/dashboard/evidence-dashboard.css` move the title/logo/tabs/data controls into compact top chrome and make the Local Mac runtime control a two-column card. `apps/dashboard/evidence-dashboard.js` removes the visible combined SV2.0.2+SV2.1 loaded label and filters sparse `paper_closed` decision rows out of the closed-trade table when entry/exit/price/quantity/PnL/equity fields are missing.
- `why`: Founder review found the old hero/header consumed vertical space, the combined evidence-loaded phrase added noise, and sparse decision rows still appeared as n/a closed trades even after the full `trades.jsonl` ledger loader was added.
- `result`: `implemented_compact_chrome_and_closed_trade_complete_row_filter`. Strategy Lane Comparison now sits directly below Open/Closed Synthetic Trades so lane equity follows the trade ledger in founder review.
- `follow_up_implications`: Sparse `paper_closed` decisions remain audit context, but the Closed Synthetic Trades table should continue to represent synthetic trade-ledger truth. This decision does not change Money Flow production rules, approve paper/live trading, regenerate evidence packs, submit orders, call private/signed/order endpoints, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

## 2026-05-16T19:45:03Z - PT-RT1.3 - Surface Durable Paper Signals And Keep Testnet Probe Transport Explicit

- `decision`: The Paper Observation dashboard should read recent ignored PT-RT `decisions.jsonl` rows for Signal Generation, not only the current-cycle `summary.json` signal field, and should label audit/order-shape rows separately from signed testnet orders.
- `scope`: `apps/dashboard/evidence-dashboard.js` now loads recent `decisions.jsonl` rows from PT-RT runtime directories, defaults Paper Observation filters to All, renders durable synthetic `paper_opened` rows, and labels `audit_only` as local 20 USDC testnet probe shape generation without signed Hyperliquid testnet submission.
- `why`: Founder saw signals in runtime artifacts but not in the UI because the latest summary cycle had no new `paper_opened` rows. Founder also expected visible testnet submissions, but the current dashboard path intentionally writes audit/order-shape rows only.
- `result`: `implemented_dashboard_runtime_truth_visibility`. Existing local runtime artifacts can populate Signal Generation without restarting the run. Signed testnet transport remains off unless a future operator uses the separate PT-RT1.2 transport gate with exact approval and a configured client.
- `follow_up_implications`: A future signed-testnet-transport phase must be explicitly scoped and approved before any real Hyperliquid testnet order endpoint calls. This decision does not change Money Flow production rules, approve paper/live trading, regenerate evidence packs, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

## 2026-05-16T20:11:48Z - PT-RT1.2.1 - Make Paper Observation Chart-First And Marker-Aware

- `decision`: Treat PT-RT1.2.1 as a dashboard/UI-only phase that makes Paper Observation easier for founder review without changing runtime strategy behavior.
- `scope`: The visible Expanded Scanner Universe/watchlist is removed, Live Public Candles + Paper Markers moves above Signal Generator, Signal Generator/Open Synthetic Positions/Closed Synthetic Trades paginate at 10 rows, Wildcard Diagnostics moves to Strategy, global Symbol/Timeframe/Strategy filters apply across relevant Paper Observation widgets, and opened/closed synthetic paper rows render as chart markers.
- `why`: Founder review found the Paper Observation page hard to use and wanted the chart, signal rows, and synthetic paper ledger rows to be filter-consistent and visually connected.
- `result`: `implemented_chart_first_paper_observation_ui`. All Symbol/Timeframe selections use explicit choices when present; when set to All, the chart chooses the newest matching paper signal/open context or preserves the prior chart target.
- `follow_up_implications`: This is display/runtime visibility only. It does not change Money Flow production rules, approve paper/live trading, regenerate evidence packs, submit orders, call private/signed/order endpoints, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

## 2026-05-16T13:30:10Z - PT-RT1.3 - Defer TRUMP From Fresh Runtime Scanner

- `decision`: Remove TRUMP from fresh PT-RT paper-observation scanner runs and record it as a deferred runtime symbol.
- `scope`: `services/paper_runtime/pt_rt1.py` excludes TRUMP from `FOUNDER_REQUESTED_SYMBOLS` / `PT_RT1_REQUESTED_SCANNER_SYMBOLS` and exposes `deferred_runtime_symbols.TRUMP=runtime_noise_deferred_by_founder` in the PT-RT summary. PT-RT docs and Obsidian notes clarify that historical SV2.1 evidence artifacts already containing TRUMP remain historical evidence truth.
- `why`: Founder review found TRUMP generated too much runtime noise for the current paper-observation scanner.
- `result`: `implemented_runtime_scanner_deferral`. Fresh PT-RT runs should not scan TRUMP after the runtime is restarted.
- `follow_up_implications`: Restart any already-running PT-RT process to pick up the new scanner list. This does not change Money Flow production rules, approve paper/live trading, regenerate evidence packs, submit orders, call private/signed/order endpoints, use API keys, use testnet strategy truth, or add SOR/fanout/CBBO.

## 2026-05-16T11:00:18Z - PT-RT1 - Compact Decision Logging Default

- `decision`: Make PT-RT1 runtime decision logging compact by default and keep full-audit logging as an explicit mode.
- `scope`: `scripts/run_pt_rt1_paper_observation.py` now supports `--decision-log-mode compact|full_audit|signals_only`, defaults to compact, preserves actionable open/close and data-unavailable rows, suppresses repeated identical non-actionable rows across cycles, and writes log-size/suppression stats into `summary.json`. `scripts/run_dashboard_control_server.py` starts local runtime sessions with compact logging, and the Paper Observation dashboard displays log mode/size/written/suppressed stats.
- `why`: A local runtime run showed `decisions.jsonl` can become operationally large when repeated no-trade/non-actionable decisions are appended forever. Founder review needs manageable runtime artifacts without losing synthetic trade signals.
- `result`: Future dashboard-started PT-RT1 runs use compact logging. Existing ignored large local logs are not rewritten or deleted by this decision.
- `follow_up_implications`: PT-RT1.1D should evaluate compact-log health alongside market-data, candle-gating, duplicate-prevention, and no-order/no-live runtime checks. This decision does not change Money Flow rules, approve paper/live trading, submit orders, call private/signed/order endpoints, enable testnet probes, use API keys, use testnet data as strategy truth, regenerate evidence packs, or add SOR/fanout/CBBO.

## 2026-05-16T12:15:10Z - PT-RT1.2 - Persist Runtime State Before Signed Testnet Transport

- `decision`: Treat PT-RT1.2 as a runtime-correctness phase before any signed Hyperliquid testnet transport. Persist signal/position state, block repeated same-candle opens, and make data-unavailable expansion visible before allowing a future transport client.
- `scope`: `scripts/run_pt_rt1_paper_observation.py` now persists processed signal keys, open synthetic positions, realized equity by lane, and last processed close state in `state.json`; converts duplicate same-candle `paper_opened` attempts into held/blocked decisions; writes synthetic closed trades to `trades.jsonl`; summarizes unavailable market-data rows separately from lane-expanded `data_unavailable` decisions; and exposes an explicit fakeable transport gate behind `--submit-testnet-probes`, exact PT-RT1.2 transport approval, 20 USDC notional, and a configured client.
- `why`: The latest local run showed many repeated `paper_opened` rows because the runtime was effectively stateless across cycles. It also showed many `data_unavailable` rows because one unavailable symbol/timeframe market row expands across all 10 lanes. The founder also wanted 20 USDC testnet probes, but paper PnL must stay independent of testnet fills/prices.
- `result`: `implemented_runtime_state_and_transport_gates`. Dashboard-started runs remain audit/order-shape mode; no signed/order endpoint is called unless a future operator explicitly supplies the transport path and approval.
- `follow_up_implications`: A fresh PT-RT1.2 run should be reviewed for duplicate-open blocking, open/flat state, synthetic closes, compact-log size, and data-health rollups before any signed testnet transport. This does not change Money Flow production rules, approve strategy paper runtime as production behavior, approve live trading, call live endpoints, use API keys, or add SOR/fanout/CBBO.

## 2026-05-16T10:15:00Z - PT-RT1 - Local Caffeinated Dashboard Start Run Control

- `decision`: Add a localhost-only dashboard control server so the founder can start and stop PT-RT1 paper-observation runs from the Paper Observation tab while keeping a Mac awake.
- `scope`: `scripts/run_dashboard_control_server.py` serves the static dashboard and exposes only `/api/paper-runtime/status`, `/api/paper-runtime/start`, and `/api/paper-runtime/stop`. Start Run is allowlisted to durations `5m`, `1h`, `6h`, and `24h`, output directories `reports/paper_runtime/pt_rt1_1c_24h_dry_run` and `reports/paper_runtime/pt_rt1_1b_smoke`, and always runs `scripts/run_pt_rt1_paper_observation.py` through `caffeinate` with `--disable-testnet-probes` and `--public-mainnet-only`.
- `why`: The founder asked for a Start Run button and Mac caffeination so paper observation can run without manually managing a terminal command and sleep settings.
- `result`: `implemented_local_only_caffeinated_runtime_control`. Static `http.server` review still works, but the Start/Stop panel intentionally shows unavailable without the local control API.
- `follow_up_implications`: This is runtime ergonomics for synthetic paper observation only. It does not approve production strategy changes, strategy paper-runtime promotion, live trading, live/testnet orders, private/signed/order endpoints from strategy truth, API-key use, canonical evidence regeneration, SOR/fanout/CBBO, or testnet strategy truth.

## 2026-05-16T09:40:00Z - SV2.1 - Expand Founder-Approved Evidence To 10 PT-RT1 Lanes

- `decision`: Rebuild the SV2.1 founder-approved 1D Historical Replay/evidence layer so all 10 PT-RT1 paper-observation lanes are visible for founder comparison.
- `scope`: Keep the same founder-approved 1D symbol universe and period sets (`2024`, `2025`, `YTD`, `ALL`). Preserve the 90 baseline Money Flow v1.2 packs and generate evidence-only candidate/reference/wildcard packs for the nine non-baseline lanes: two SOR rolling-range lanes, four MF-ORIG full-equity lanes, and three wildcard observation lanes.
- `why`: The founder said the data was hard to compare and the latest evidence pack had lost the other paper-observation strategies, leaving only four visible strategies.
- `result`: `SV2.1 10-lane 1D evidence generated`. Counts: 90 baseline packs, 810 evidence-only candidate/reference/wildcard packs, and 1800 selected Historical Replay chart/trade JSON files at timestamp `20260516T091500Z`.
- `follow_up_implications`: This remains 1D founder-review research evidence only. It does not change production Money Flow rules, approve a variant, approve strategy paper runtime, approve live trading, submit orders, call private/signed/order endpoints, use API keys, use testnet data as strategy truth, or add SOR/fanout/CBBO.

## 2026-05-14T23:05:55Z - Paper Observation - Compact Watchlist and Signal Generation

- `decision`: Keep the founder-facing Paper Observation watchlist compact and replace the Market Data Health panel with Signal Generation.
- `scope`: The watchlist now displays only symbol, mid price, and health. It polls Hyperliquid public mainnet `allMids` every 1 second; health is `unhealthy` when the latest market-data tick is missing or stale for more than 2 minutes. Signal Generation lists recorded synthetic `paper_opened` intended-entry decisions from the PT-RT1 paper decision stream.
- `why`: The founder asked to remove extra watchlist columns, keep a health column, and use the adjacent panel to show intended trade entries whenever strategies generate them.
- `result`: `implemented_compact_symbol_mid_health_watchlist_and_signal_generation_panel`.
- `follow_up_implications`: This remains dashboard display/runtime observation only. It adds no bid/ask polling, order controls, submitted orders, private/signed/order/account payloads, API keys, testnet strategy truth, production Money Flow changes, canonical evidence regeneration, paper/live approval, or SOR/fanout/CBBO.

## 2026-05-15T01:05:00Z - SV2.1 - Replace Broad Evidence With Founder-Approved Universe

- `decision`: Reject the broad active-metadata SV2.1 evidence estate for founder review and rebuild the SV2.1 1D period packs only for the founder-approved requested/resolved universe.
- `scope`: The current SV2.1 run targets BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, TRX, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, and TRUMP. TRON maps to TRX; PEPE/kPEPE and OKB are excluded by resolver policy. Generated baseline/candidate packs and selected chart JSON remain ignored under `reports/strategy_validation/`; raw/config working files remain under `/tmp/money-flow-sv21-broad-1d/`.
- `why`: The founder rejected the broad evidence packs as not useful and asked to rerun the same evidence shape only for the chosen pairs while verifying the dashboard personally with Playwright.
- `result`: `SV2.1 founder-approved 1D evidence generated`. Counts: 90 baseline packs, 270 evidence-only candidate packs, and 720 selected Historical Replay chart/trade JSON files at timestamp `20260515T004500Z`. ASTER and TRUMP have no 2024 pack because public 1D candles do not cover that period.
- `follow_up_implications`: SV2.1 remains 1D founder-review research evidence only. It does not change Money Flow production rules, optimize parameters, approve a variant, approve strategy paper runtime, approve live trading, submit orders, call private/signed/order endpoints, use API keys, use testnet data as strategy truth, or add SOR/fanout/CBBO.

## 2026-05-14T23:09:49Z - SV2.1 - Historical Replay and Conservative Candidate Packs

- `decision`: Add Historical Replay visibility and evidence-only conservative candidate packs for the already-generated SV2.1 broad Hyperliquid 1D period evidence.
- `scope`: Generated ignored selected chart/trade JSON under `reports/strategy_validation/sv2_1_broad_1d_dashboard_chart_data/20260514T220500Z` and ignored candidate evidence-only packs under `reports/strategy_validation/` for `avoid_low_rolling_range_50`, `avoid_low_rolling_range_20`, and `mf_orig_1d_stage2_breakout_resistance_full_equity`. The dashboard Historical Replay tab now has a Period selector for 2024 / 2025 / YTD / ALL and lazy-loads SV2.1 1D rows by period, symbol, strategy, and fill.
- `why`: The founder asked to add the larger-symbol evidence refresh to Historical Replay and include the best three conservative candidates for visual review, without changing strategy rules or rerunning unrelated evidence.
- `result`: `SV2.1 historical replay artifacts generated`. Counts: 5116 selected chart/trade JSON files and 1912 candidate evidence-only pack directories. MF-ORIG candidate rows were skipped for 7 symbols with incomplete indicator context; baseline and rolling-range rows remain available where source period packs exist.
- `follow_up_implications`: SV2.1 remains 1D founder-review evidence only. It does not supersede canonical SV2.0.2 multi-timeframe evidence, approve variants, change Money Flow production rules, approve paper/live, submit orders, call private/signed/order endpoints, use API keys, use testnet data as strategy truth, or add SOR/fanout/CBBO.

## 2026-05-14T22:36:41Z - Paper Observation - Live Watchlist Ticker and Selected-Pair Chart

- `decision`: Add browser-side Paper Observation display polling for latest public mainnet market data and render a selected-pair live TradingView chart.
- `scope`: The dashboard now calls Hyperliquid public mainnet `/info` with allowlisted `allMids` for watchlist ticks and selected-pair `candleSnapshot` for live candles. The expanded scanner table keeps requested/resolved/block reason visibility and lets the founder select the pair for the chart.
- `why`: The founder wanted the Paper Observation watchlist ticking with latest market data and a live chart for the selected pair while the PT-RT1.1C probes-disabled runtime collection continues.
- `result`: `implemented_display_only_public_mainnet_ticker_and_selected_pair_chart`.
- `follow_up_implications`: This is dashboard display/runtime observation only. It does not add order controls, submit orders, call private/signed/order/account payloads, use API keys, use testnet prices as strategy truth, change production Money Flow rules, regenerate canonical evidence packs, approve paper/live behavior, or add SOR/fanout/CBBO.

## 2026-05-14T22:05:00Z - SV2.1 - Generate Broad Hyperliquid 1D Period Evidence

- `decision`: Regenerate research-only 1D Money Flow v1.2 evidence for the broad active Hyperliquid public metadata universe, sliced into 2024, 2025, YTD, and ALL period sets.
- `scope`: Used Hyperliquid public mainnet `meta` and `candleSnapshot` only; targeted 183 active public metadata symbols; imported available timezone-explicit 1D candles into the intended local `money_flow` Strategy Validation DB; generated 646 ignored evidence packs and 646 generated campaign configs. Generated raw candles and configs remain local under `/tmp/money-flow-sv21-broad-1d/`; generated evidence packs remain ignored under `reports/strategy_validation/`.
- `why`: The founder requested a larger-symbol evidence refresh and a deeper 1D history back to January 2024 where public data allows, with period sets for 2024, 2025, YTD, and ALL.
- `result`: `SV2.1 broad 1D evidence generated`. Period config counts: 2024=130, 2025=172, YTD=172, ALL=172. Blocked period rows represent no available public 1D candles in that period, not missing fabrication.
- `follow_up_implications`: SV2.1 is 1D founder-review research evidence only. It does not change Money Flow production rules, optimize parameters, approve a variant, approve strategy paper runtime, approve live trading, submit orders, call private/signed/order endpoints, use API keys, use testnet data as strategy truth, or add SOR/fanout/CBBO.

## 2026-05-14T21:57:58Z - PT-RT1.1C - Start 24-Hour Probes-Disabled Runtime Collection

- `decision`: Start the 24-hour PT-RT1 probes-disabled public-mainnet runtime collection under ignored local runtime storage.
- `scope`: Started `scripts/run_pt_rt1_paper_observation.py --duration-hours 24 --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run --disable-testnet-probes --public-mainnet-only` as PID `11158`, with testnet probes disabled, kill switch active, and daily probe cap zero. The first verified cycle wrote the expected ignored artifact set, resolved 25 watchlist rows, kept 23 scanner-eligible rows, blocked PEPE/kPEPE and OKB with reason codes, and wrote 920 decision rows.
- `why`: PT-RT1.1B proved connector/runtime readiness but did not produce the required full 24-hour probes-disabled artifact set. PT-RT1.1C starts the real forward-observation collection so PT-RT1.1D can evaluate data health, candle gating, duplicate prevention, paper ledgers, dashboard runtime readability, and no-order/no-live boundaries after completion.
- `result`: `PT-RT1.1D may evaluate 24-hour runtime artifacts after completion`. PT-RT1.2 testnet plumbing probes remain blocked until the probes-disabled run passes.
- `follow_up_implications`: PT-RT1.1C is runtime collection only. It does not approve production strategy changes, strategy paper-runtime promotion, live trading, live/testnet orders, private/signed/order endpoints from strategy truth, API-key use, canonical evidence regeneration, SOR/fanout/CBBO, or testnet strategy truth.

## 2026-05-14T20:20:36Z - PT-RT1.1A - Expand Paper Observation Lab Before Runtime Collection

- `decision`: Expand PT-RT1 before the 24-hour probes-disabled run to exactly 10 independent synthetic strategy lanes plus an expanded founder-requested scanner universe with requested/resolved/block reason-code visibility.
- `scope`: Added the Money Flow baseline lane, two SOR rolling-range lanes, four MF-ORIG full-equity reference lanes, and three wildcard expert observation lanes. Scanner truth now includes canonical symbols plus founder-requested TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, TRUMP, PEPE, and OKB, with TRON->TRX, PEPE->kPEPE, PEPE/kPEPE unit-semantics blocking, OKB support-confirmation blocking, and POL/MATIC delisting protection.
- `why`: The founder wanted the forward-observation lab expanded before collecting the first 24-hour runtime artifact set, so the run can observe broader symbols and strategy hypotheses from the start rather than retrofitting the dashboard after partial runtime logs exist.
- `result`: `PT-RT1.1B` was the public-mainnet connector/runtime-readiness follow-up before the 24-hour probes-disabled runtime collection. PT-RT1.2 testnet probes remain blocked until a real probes-disabled run passes.
- `follow_up_implications`: PT-RT1.1A is readiness only. It does not start runtime collection, enable testnet probes, submit testnet/live orders, call private/signed/order endpoints from strategy truth, use API keys, use testnet prices/fills as strategy PnL, regenerate canonical evidence packs, change production Money Flow rules, approve paper/live, or add SOR/fanout/CBBO.

## 2026-05-14T21:06:00Z - PT-RT1.1B - Connect Public Mainnet Data Before 24-Hour Collection

- `decision`: Add the Hyperliquid public mainnet data connector and runtime command before starting the full probes-disabled 24-hour run.
- `scope`: Added a public-read-only `/info` connector for `meta`, `metaAndAssetCtxs`, `allMids`, `candleSnapshot`, `fundingHistory`, and display-only `l2Book`; added the ignored runtime artifact writer/runner; updated the Paper Observation dashboard with connection status and PT-RT1.1B/runtime summary loading; and produced PT-RT1.1B founder report/summary.
- `why`: PT-RT1.1A expanded the lab configuration, but the repo still needed live public-mainnet connectivity and a concrete operator command before collecting 24-hour artifacts.
- `result`: A bounded smoke cycle connected to public mainnet `meta` and `allMids`, resolved 25 requested watchlist rows with 23 eligible and 2 blocked, loaded bounded public candle data, recorded 80 bounded paper decision events, and wrote ignored runtime artifacts under `reports/paper_runtime/pt_rt1_1b_smoke/`.
- `follow_up_implications`: `PT-RT1.1C may start 24-hour probes-disabled runtime collection`. This does not approve PT-RT1.2 testnet probes, production strategy changes, strategy paper-runtime promotion, live trading, live/testnet orders, private/signed/order endpoints from strategy truth, API-key use, canonical evidence regeneration, SOR/fanout/CBBO, or testnet strategy truth.

## 2026-05-13T22:03:37Z - OB2.0 - Obsidian Strategy Brain Uses SV2.0.2 / EV-AUDIT1 As Current Truth

- `decision`: Refresh the Obsidian brain around one canonical command center and dedicated strategy/evidence/data/dashboard/paper-observation maps.
- `scope`: Current Money Flow v1.2 is documented as the production-derived derivative baseline, while Original Money Flow / MF-ORIG is documented as a separate source-faithful evidence track. SOR repair variants, MF-ORIG hypotheses, STRAT-EV plan-only discovery, EV-AUDIT1, Historical Replay, Evidence Lab, UAT sandbox plumbing, and future PT-RT1 paper observation are separated.
- `source_truth`: The Gerald Peters Money Flow Trading System PDF is now a primary source stored in `money-flow/90 Reference/`. Current Money Flow v1.2 is not exact original-source implementation.
- `evidence_truth`: SV2.0.2 canonical DB-imported Hyperliquid public-mainnet evidence packs remain the current canonical baseline. Dashboard chart JSON and date-filter recalculations are display-only and are not canonical evidence regeneration.
- `approval_truth`: EV-AUDIT1 promotes no clean strategy candidate. No strategy is production-ready. PT-RT1 is recommended but not approved or implemented. No paper-runtime approval, live trading approval, production order automation, or live exchange order submission follows from OB2.0.
- `follow_up_implications`: Future agents should start from `money-flow/00_Money_Flow_Command_Center.md`, then use the new maps/registers to avoid mixing current v1.2, MF-ORIG, SOR, dashboard display data, UAT plumbing, and future paper-observation scope.

## 2026-05-14T19:20:14Z - PT-RT1.1 - 24-Hour Dry Run Cannot Pass Without Runtime Artifacts

- `decision`: Mark PT-RT1.1 blocked because the expected probes-disabled 24-hour runtime artifact directory `reports/paper_runtime/pt_rt1_1_24h_dry_run/` is absent.
- `scope`: The committed report/summary record the required dry-run config with testnet probes disabled, kill switch active, daily probe cap zero, public mainnet strategy truth only, no API keys, no private/signed/order endpoints, and no orders. They do not claim public data refresh, closed-candle gating, ledgers, duplicate-signal prevention, data-health gating, or dashboard runtime readability passed.
- `why`: PT-RT1.1 is an observation-validation phase. Without real runtime artifacts, passing the phase would fabricate forward-observation evidence.
- `result`: `PT-RT1.2 blocked`. Testnet plumbing probes and the 60-day observation should wait until the probes-disabled 24-hour run is actually executed and summarized.
- `follow_up_implications`: Preserve ignored runtime artifacts under `reports/paper_runtime/pt_rt1_1_24h_dry_run/` for the next PT-RT1.1 regeneration. Production Money Flow rules, paper-production approval, live trading, live orders, private/signed/order endpoints, API keys, historical evidence packs, and SOR/fanout/CBBO remain unchanged/not approved.

## 2026-05-13T08:27:33Z - MF-ORIG-EV2 - Full-Equity Comparison Rows Added Without Replacing Source 1% Risk Rows

- `decision`: Keep the four source-faithful 1% risk-sizing MF-ORIG-EV2 hypotheses and add four founder-requested full-equity/notional counterparts for direct comparison.
- `scope`: The regenerated MF-ORIG-EV2 run uses the same canonical SV2.0.2 DB-imported candle substrate, the same 9 supported symbols, 4 timeframes, and 2 fill assumptions. It writes ignored evidence/chart artifacts and compact committed summaries only.
- `result`: The regenerated summary now has 8 replay strategies, 576 scenario rows, 288 ignored evidence-pack directories, and 612 ignored dashboard chart-data files including 576 selected per-scenario replay JSON files.
- `follow_up_implications`: The full-equity rows are evidence-only comparison lanes, not source-faithful risk sizing and not production/paper/live approval. Production Money Flow v1.2 remains unchanged.

## 2026-05-12T23:26:20Z - MF-ORIG-EV1.1 - Accounting / Drawdown Conclusions Supersede MF-ORIG-EV1

- `decision`: Quarantine pre-hotpatch MF-ORIG-EV1 PnL/drawdown conclusions and treat regenerated MF-ORIG-EV1.1 reports as the current founder-review source.
- `scope`: MF-ORIG-EV1.1 keeps the original source interpretation and hypotheses unchanged, but fixes the research accounting model to event-ledger accounting, counts entry fees and trim PnL exactly once, closes only remaining quantity, computes realized and mark-to-market drawdown as peak-to-trough, audits all generated trades for accounting invariants, and filters `positive 1d pockets` to baseline-positive 1d scenarios.
- `why`: Review found P1 evidence-truth defects: entry fees and trim PnL could be double-counted, drawdown was not peak-to-trough, and the positive 1d control label included negative baseline 1d rows.
- `result`: Candidate gates were re-run. The strict conclusion did not change: all original hypotheses remain `source_faithful_but_underperformed` because baseline-positive 1d control pockets were not preserved. Production Money Flow v1.2 remains unchanged, no original hypothesis is approved, and no orders/private/signed/order endpoints/testnet strategy truth/live trading/paper runtime/SOR behavior were added.
- `follow_up_implications`: Use MF-ORIG-EV1.1 reports, not pre-hotpatch MF-ORIG-EV1 PnL/drawdown numbers, for founder review. Any MF-ORIG-EV2 still needs direct-PDF reconciliation and/or dashboard overlays before source-authority claims.

```yaml
research_log:
  phase: MF-ORIG-EV1.1
  date: 2026-05-12
  class: source_reconstruction
  outcome: mixed
  badge: corrected; underperformed
  title: Original Money Flow Reconstruction (accounting correction)
  finding: >-
    The corrected reconstruction run. After fixing the EV1 accounting bug the
    strict conclusion did not change - all four original hypotheses remain
    source_faithful_but_underperformed because baseline-positive 1d control
    pockets were not preserved.
  why: >-
    Source-faithful original rules underperform v1.2 on the gates that
    matter: drawdown and control-pocket preservation.
  worked: >-
    Event-ledger accounting with a PnL-vs-equity tolerance check - the rerun
    proved the comparison itself was sound once measurement was fixed.
  didnt: >-
    The first reconstruction's bookkeeping (see our error); and the original
    rules as a drop-in improvement.
  lesson: >-
    Trade net PnL must reconcile to equity delta within tolerance before any
    conclusion is trusted. A measurement bug looks exactly like a strategy
    result until you check.
  our_error: >-
    Yes - K-019, caught and fixed (EV1 -> EV1.1). The first reconstruction
    double-counted entry fees and trim PnL and mis-stated drawdown, distorting
    the early conclusions. Quarantined, then regenerated with event-ledger
    accounting, fees-once, and a PnL-vs-equity tolerance check.
  changed: >-
    The PnL-reconciles-to-equity invariant became a permanent evidence
    requirement.
  hardened_gate: PnL must reconcile to equity
  evidence_summary: docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json
```

## 2026-05-13T00:42:40Z - MF-ORIG-EV2 - Original Money Flow Multi-Timeframe Evidence Remains Evidence-Only

- `decision`: Generate MF-ORIG-EV2 multi-timeframe evidence packs and dashboard replay data for founder review without changing production Money Flow v1.2 or approving any Original Money Flow hypothesis.
- `scope`: MF-ORIG-EV2 preserves MF-ORIG-EV1.1 accounting/drawdown truth and runs four hypotheses across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, 15m/1h/4h/1d, and next_candle_open / next_candle_close. It writes ignored evidence-pack directories and ignored dashboard chart-data JSON plus committed compact Markdown/JSON summaries. Historical Replay and Evidence Run Ledger can load the MF-ORIG-EV2 strategies when those local chart files exist.
- `why`: Founder review suggested the broader MF-ORIG runs needed full Historical Replay visualization and comparison against Money Flow v1.2 across the same canonical SV2.0.2 evidence substrate, rather than relying on the earlier 1d-first EV1.1 summary only.
- `result`: Baseline parity passed for all 72 SV2.0.2 scenarios. The generated run produced 144 evidence-pack directories and 36 dashboard chart-data files. Candidate gates still do not approve an original hypothesis; 1d source-primary control-pocket damage remains a blocker even where aggregate multi-timeframe deltas improve.
- `follow_up_implications`: Founder can review MF-ORIG-EV2 in Historical Replay and the Evidence Run Ledger. Any MF-ORIG-EV3 must remain separately scoped, and direct-PDF reconciliation is still needed before source-authority claims because the PDF was not present locally.

```yaml
research_log:
  phase: MF-ORIG-EV2
  date: 2026-05-13
  class: source_reconstruction
  outcome: mixed
  badge: underperformed
  title: Original Money Flow (Gerald Peters) Multi-Timeframe Evidence
  finding: >-
    Source-faithful reconstruction across 4 hypotheses (plus full-equity
    counterparts), 9 symbols, 4 timeframes, both fill assumptions. All
    "higher return but higher drawdown" vs v1.2; control pockets not
    preserved. No original hypothesis approved.
  why: >-
    Source-faithful reconstruction of the original rules underperformed
    v1.2 - higher return but worse drawdown, and positive 1d control pockets
    were not preserved. Those are the gate blockers.
  worked: >-
    Having the source PDF in-repo let us reconcile rules to text; baseline
    parity passed on all 72 scenarios, so the comparison was sound (after the
    EV1.1 accounting fix).
  didnt: >-
    The original ruleset as an edge source on this data; full-equity sizing
    only amplified the drawdown problem.
  lesson: >-
    Source fidelity is a reconstruction property, not a performance argument
    - "faithful" and "better" are independent claims.
  our_error: >-
    Inherited from EV1 (K-019 accounting bug, fees double-counted) - corrected
    in EV1.1 before these conclusions were drawn.
  changed: >-
    MF-ORIG lanes were capped at evidence-only/synthetic-only status; one
    source-faithful candidate runs in Week 2 paper for observation, not
    promotion.
  evidence_summary: docs/mf_orig_ev2_multitimeframe_evidence_summary.json
```

## 2026-05-12T22:46:40Z - MF-ORIG-EV1 - Original Money Flow Reconstruction Is Evidence-Only

- `decision`: Reconstruct the original Money Flow Trading System as a separate Strategy Validation research family without changing production Money Flow v1.2.
- `scope`: MF-ORIG-EV1 uses the prompt-provided Gerald Peters September 5, 2019 source summary because the PDF was not present locally. It creates the source-specification/gap-matrix report, implements 1d-primary original hypotheses with Stage 1-4 classification, 5 EMA / 20 SMA triggers, RSI profit-warning trims, MACD-as-TSI substitute confirmation/warnings, prior support/pivot stop proxies, and 1% risk-budget sizing, then compares those hypotheses with canonical SV2.0.2 DB-imported Money Flow v1.2 evidence.
- `why`: The founder wanted to test whether current Money Flow v1.2 is source-faithful to the original Money Flow Trading System. The first finding is that v1.2 is Money Flow-inspired but not source-faithful in hierarchy: v1.2 uses EMA stack / RSI sleeve / MACD entry gates, while the source hierarchy emphasizes stages, 20 SMA foundation, 5 EMA trigger, RSI warning/profit context, and structure-based stops.
- `follow_up_implications`: The original hypotheses are not production-approved and do not authorize paper/live behavior. They showed pre-gate aggregate PnL/drawdown improvement but failed candidate gate due control-pocket preservation. Any MF-ORIG-EV2 should first reconcile against the actual PDF and then decide whether dashboard overlays or deeper source-rule modeling are worthwhile.

## 2026-05-12T21:09:29Z - Historical Replay - Rolling-Range SOR-EV3 Variants Added

- `decision`: Bring `avoid_low_rolling_range_20` and `avoid_low_rolling_range_50` into Historical Replay as full research-only replay strategies.
- `scope`: The SV2.0.2 dashboard chart-data generator now appends those two variants across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX, `15m`/`1h`/`4h`/`1d`, and both `next_candle_open` / `next_candle_close` fill assumptions. Regenerated ignored local chart-data files contain 72 canonical replays, 72 `avoid_low_rolling_range_20` replays, and 72 `avoid_low_rolling_range_50` replays.
- `why`: The founder does not want to rely on Evidence Lab alone for deeper review and needs the promising rolling-range options inspectable in the same candle/indicator/trade-inspector workflow as canonical Historical Replay.
- `follow_up_implications`: These replay strategies remain evidence/research-only. They do not approve production Money Flow rule changes, paper runtime, live trading, order submission, or SOR behavior.

## 2026-05-12T20:48:26Z - Evidence Lab - SOR-EV1/SOR-EV2 Matrix Uses Review Labels

- `decision`: Keep SOR-EV1/SOR-EV2 variants evidence-only and not promoted, but replace the founder-facing all-rejected Variant Summary Matrix presentation with more precise review labels.
- `scope`: The dashboard matrix now separates `promising_*`, `mixed_*`, `deferred_*`, `not_promoted_*`, diagnostic-only, and hard `rejected_*` rows. It also shows review status and gate blockers.
- `why`: Some SOR-EV1/SOR-EV2 rows had useful positive aggregate PnL or diagnostic signal but failed strict promotion gates because of methodology, drawdown, control-pocket damage, or trade-count risk. Flattening those rows into `rejected` obscured useful review signal.
- `follow_up_implications`: These labels are UI/review context only. They do not approve production Money Flow rules, paper runtime, live trading, or SOR behavior. Backend evidence status and methodology warnings remain authoritative.

## 2026-05-12T19:38:08Z - SOR-EV3 - Avoid Sideways / Low-Volatility Variants Remain Evidence-Only

- `decision`: Treat the founder-selected `avoid_sideways_low_volatility` family as tested but not promoted after focused true-forward replay.
- `scope`: Baseline parity passed for all 72 canonical SV2.0.2 scenarios. ATR percentile, flat SMA20/EMA10 slope, rolling-range compression, MACD-flat chop, and conservative combined blockers were replayed from persisted candle truth with dynamic equity, blocked-entry attribution, loss concentration, and control-pocket impact.
- `why`: The broad low-volatility/chop definitions did not produce a clean control-preserving candidate. Some variants improved aggregate PnL but damaged control pockets, raised drawdown, or overblocked; blocked open signals are not the same as canonical trade-count reduction.
- `follow_up_implications`: No production Money Flow rule changed and no variant is approved. Any SOR-EV4 must be narrower, out-of-sample-style, and control-pocket-preserving before rule-change discussion.

```yaml
research_log:
  phase: SOR-EV3
  date: 2026-05-12
  class: variant
  outcome: mixed
  badge: none promoted
  title: Avoid Sideways / Low-Volatility Variants
  finding: >-
    The founder-selected avoid-sideways drilldown - ATR percentile, flat
    trend, rolling-range, MACD-flat blockers - replayed true-forward with
    blocked-entry attribution. avoid_low_rolling_range was labeled promising
    on PnL but carried control-pocket risk; no variant promoted.
  why: >-
    The chop filters block losing entries but also block the control pockets
    that make the baseline reviewable; net effect fails the preservation bar.
  worked: >-
    Blocked-entry attribution - knowing exactly which trades a filter removes
    - made the trade-off visible instead of hidden in aggregates.
  didnt: >-
    Volatility/chop filtering as an edge source; at best it reshapes the same
    PnL.
  lesson: >-
    "Promising" is a review label, not a result - a filter that improves
    aggregate PnL while damaging control pockets is not an improvement.
  our_error: null
  changed: >-
    avoid_low_rolling_range_20 was carried into Week 2 as a synthetic-only
    diagnostic comparator, explicitly not as a promoted strategy.
  evidence_summary: docs/sor_ev3_avoid_sideways_low_volatility_summary.json
```

## 2026-05-12T20:37:54Z - SOR-EV3 - Founder Review Labels Separate Promising From Rejected

- `decision`: Keep the strict SOR-EV3 candidate gate unchanged, but replace the founder-facing all-rejected presentation with more precise review labels.
- `scope`: `avoid_low_rolling_range_20` is labeled `promising_control_pocket_risk`, `avoid_low_rolling_range_50` is labeled `promising_high_pnl_control_risk`, and `avoid_low_atr_percentile_30` remains hard rejected as `rejected_negative_aggregate`. Mixed positive-PnL rows remain not-promoted with control-damage labels.
- `why`: The rolling-range variants improved aggregate PnL materially, but they failed strict promotion because worst-scenario drawdown worsened and control pockets were damaged. Calling them simply rejected obscured useful founder-review signal.
- `follow_up_implications`: `promising_*` labels are evidence-review context only. They do not approve production rules, paper runtime, live trading, or SOR behavior. Any SOR-EV4 should focus on the promising rolling-range family with sliced validation and control-pocket preservation.

## 2026-05-12T13:18:15Z - SOR-EV2.2 - Evidence Lab Overlays Are Visualization Only

- `decision`: Add Evidence Lab baseline-vs-variant chart overlays for founder review without treating overlay output as canonical evidence or production-rule approval.
- `scope`: The overlay uses SV2.0.2 chart/trade JSON for baseline entry/exit/forced-close markers and committed SOR-EV1/SOR-EV2 bundle rows for linkable variant/adverse-candle context, worst-trade focus, and control-pocket review.
- `result`: Missing exact variant marker timestamps are shown as `exact_overlay_unavailable_from_sor_ev_bundle`; non-true-forward methods are labeled `diagnostic_only_not_candidate`. No production Money Flow rule changed, no variant was approved, no orders or private/signed/order endpoints were called, no Hyperliquid testnet price was used as strategy truth, no evidence packs were regenerated, and no live/paper runtime or SOR/fanout/CBBO/cross-venue behavior was added.
- `follow_up_implications`: Founder review can use overlays to decide whether a narrower backend evidence phase is worth scoping. Dashboard overlays and date filters remain display-only and noncanonical.

## 2026-05-12T12:08:11Z - SOR-EV2.1 - Evidence Lab Is Visualization Only

- `decision`: Add a dashboard Evidence Lab / Variant Review surface for SOR-EV1/SOR-EV2 bundle review without treating it as canonical evidence generation or production-rule approval.
- `scope`: The tab loads committed SOR-EV1 and SOR-EV2 summaries, labels canonical SV2.0.2 DB-imported evidence as the baseline, and shows variant matrix, control pockets, worst trades, late-entry, large adverse-candle, and RSI/MACD rejection panels.
- `result`: No production Money Flow rule changed, no variant was approved, no orders or private/signed/order endpoints were called, no Hyperliquid testnet price was used as strategy truth, and the invalid legacy Experiments tab remains absent.
- `follow_up_implications`: Founder review can use Evidence Lab to decide whether a narrower SOR-EV2.2/SOR-EV3 canonical evidence phase is worth scoping. Dashboard date-filter numbers and UI overlays remain noncanonical.

## 2026-05-12T11:05:00Z - SOR-EV2 - True-Forward Variants Do Not Promote Production Rule Changes

- `decision`: Treat SOR-EV2 true-forward replay as evidence-only triage and promote no variant.
- `scope`: Baseline parity passed for all 72 canonical SV2.0.2 scenarios. Fixed/ATR/recent-low/large-bear stops, earlier-MACD/lower-RSI entries, extension filters, and chop filters were replayed from persisted candle truth.
- `result`: No variant was clean enough for production-rule-change proposal. Some filters improved aggregate sums, but control-pocket and scenario-level damage kept them out of candidate status. Lower-RSI/MACD admission variants added many bad trades.
- `follow_up_implications`: Any SOR-EV3 should be narrower and out-of-sample-style; production Money Flow rules remain unchanged.

```yaml
research_log:
  phase: SOR-EV2
  date: 2026-05-12
  class: variant
  outcome: mixed
  badge: none promoted
  title: True-Forward Stop / Rejected-Signal Variants
  finding: >-
    Stop-loss, exit, and entry-filter variants replayed true-forward against
    the canonical baseline. Founder-review labels separated promising / mixed
    / deferred / hard-rejected - no variant was promoted.
  why: >-
    The "promising" rows bought their PnL with damaged control pockets or
    worse drawdown; nothing improved the baseline cleanly across gates.
  worked: >-
    True-forward replay semantics (no lookahead) and honest multi-level
    review labels instead of a binary promote/reject.
  didnt: >-
    Stop/exit repair as a family - variants shift losses around rather than
    remove them.
  lesson: >-
    A variant must preserve the baseline's control pockets, not just beat its
    aggregate PnL.
  our_error: null
  changed: >-
    Control-pocket preservation became an explicit review dimension for every
    later variant pass.
  evidence_summary: docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json
```

## 2026-05-12T10:20:00Z - SOR-EV1 - Loss Anatomy Uses Canonical SV2.0.2 Packs Only

- `decision`: Treat canonical SV2.0.2 DB-imported evidence packs as the only SOR-EV1 baseline source and keep all stop/entry variants evidence-only until true-forward replay exists.
- `scope`: SOR-EV1 analyzes worst losing trades, completed-trade adverse-move / late-entry classifications, aggregate RSI/MACD rejection limitations, fixed-stop overlay estimates, deferred ATR/recent-low/large-bear/entry variants, and control-pocket impact.
- `result`: No production Money Flow rule was changed, no variant was approved, no evidence packs were regenerated, no dashboard date-filter recalculation was used as canonical evidence, no Hyperliquid testnet price was used as strategy truth, and no order/private/signed endpoint was called.
- `follow_up_implications`: SOR-EV2 should be true-forward replay if the founder wants to test stop or entry variants seriously. Completed-trade overlays remain hypothesis triage only.

```yaml
research_log:
  phase: SOR-EV1
  date: 2026-05-12
  class: variant
  outcome: context
  badge: loss anatomy
  title: Money Flow Trade-Loss Anatomy
  finding: >-
    Evidence-only anatomy of where Money Flow v1.2 loses - largest losses,
    losing streaks, stop/exit behavior - against canonical SV2.0.2 packs, to
    seed the SOR variant hypotheses.
  why: >-
    Diagnostic, not a pass/fail test - it mapped the loss structure that
    SOR-EV2/EV3 variants then tried (and failed) to repair.
  worked: >-
    Grounding variant ideas in observed loss anatomy instead of intuition;
    canonical-pack-only inputs kept the numbers trustworthy.
  didnt: >-
    Early completed-trade overlays were lookahead-flattered; they were labeled
    diagnostic-only rather than candidates.
  lesson: >-
    Only true-forward replays can become candidates; completed-trade overlays
    are upper bounds, not evidence.
  our_error: null
  changed: >-
    The diagnostic-only vs true-forward distinction became a permanent
    labeling rule in variant review.
  evidence_summary: docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json
```

## 2026-05-12T07:59:37Z - Dashboard - SV2.0.2 Historical Replay Display Uses Canonical Chart Data

- `decision`: Use generated dashboard chart/trade JSON derived from existing SV2.0.2 canonical packs for Historical Replay display instead of regenerating evidence packs or continuing to rely on older PT/SV1.13 dynamic-equity summaries.
- `scope`: The display data covers BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX across 15m/1h/4h/1d when the ignored local files under `reports/strategy_validation/sv2_0_2_dashboard_chart_data/20260512T064916Z/` are present. Evidence controls are de-duplicated by timeframe, component cards include pair context, arrow descriptions default off, and the invalid Experiments surface is not exposed as a dashboard tab.
- `result`: No evidence packs were regenerated for this fix. The dashboard display now reflects the regenerated SV2.0.2 canonical evidence/trade data and keeps 4h/1d Jan 2025 history visible where available.
- `follow_up_implications`: If chart files are deleted locally, rerun `scripts/build_sv202_dashboard_chart_data.py` against the existing raw candle JSON and canonical packs. This remains visualization-only and does not change Money Flow rules, import candles, submit orders, call private/signed/order endpoints, or approve live trading.

## 2026-05-11T20:34:00Z - Historical Replay - 5EMA/20MA Cross-Close Variant Added

- `decision`: Add `Only close on 5/20 cross` as a research-only Historical Replay strategy and keep it out of production Money Flow rules.
- `scope`: The replay summary now includes OG replay/strategy, MACD removed, and Only close on 5/20 cross rows across BTC/ETH/SOL and available 15m/1h/4h/1D dashboard views. The new variant keeps baseline entry checks but waits for EMA5 to cross below SMA20 before close validation instead of closing solely because price closed below SMA20.
- `result`: The dashboard replay-strategy dropdown can switch to the new variant, the PT0.0.3 loader keeps 1D visible by preserving the first/latest summary payload, and chart arrows can optionally hide entry/exit descriptions and show only PnL.
- `follow_up_implications`: Founder review can visually compare the new close rule hypothesis before any future strategy-design decision. Production Money Flow rules, order behavior, live trading boundaries, and sandbox execution plumbing remain unchanged.

## 2026-05-11T21:27:44Z - SV2.0 - 1D Sleeve Added And Expanded Public-Mainnet Evidence Refreshed

- `decision`: Add `sleeve_1d` as a real first-class Money Flow sleeve and update the strategy version to Money Flow v1.2.
- `scope`: Existing 15m/1h/4h settings remain unchanged. The new 1D baseline is non-optimized: 50 bars, RSI 46-72, overbought 78, trim 84, max EMA5 extension 3.0%, and MACD required. The requested BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB universe is resolved through Hyperliquid public mainnet metadata, with SHIB explicitly mapped to `kSHIB`.
- `result`: Public mainnet `candleSnapshot` rows were fetched for supported symbols across 15m/1h/4h/1D. 4h and 1D reach the Jan 2025 target; 15m and 1h are limited by Hyperliquid public recent-candle availability and carry `hyperliquid_public_5000_candle_limit`. Compact dynamic-equity evidence rows and dashboard readiness are available in `docs/sv2_0_historical_data_refresh_summary.json`.
- `follow_up_implications`: A later SV2.x phase may generate full ignored evidence packs and/or DB-backed candle imports after artifact policy is confirmed. SV2.0 submits no orders, calls no private/signed/order endpoints, uses no API keys, uses no testnet data as strategy truth, and does not optimize parameters.

## 2026-05-11T17:40:05Z - PT0.0.3 - 1D Replay Is Aggregated Horizon View, Not New Strategy Sleeve

- `decision`: Add `1D` to the Historical Replay cockpit as a deterministic historical-data horizon view while keeping production Money Flow sleeves unchanged.
- `scope`: PT0.0.3 loads the trusted PT0.0.2 historical replay summary, reports Jan 2025 target-start readiness for BTC/ETH/SOL x 15m/1h/4h/1D, and creates `docs/pt0_0_3_historical_strategy_replay_summary.json`.
- `result`: Current committed local data does not reach `2025-01-01T00:00:00Z`; actual earliest/latest ranges and target coverage are shown per dataset. `1D` candles are aggregated from 4h historical replay candles and labeled `not_a_new_1d_money_flow_sleeve`.
- `follow_up_implications`: A future PT0.0.4 backfill/regeneration phase should source trusted BTC/ETH/SOL historical candles back to Jan 2025 where possible before deeper playback/market-structure inspection. No orders, endpoint calls, rule changes, or strategy optimizations were added.

## 2026-05-11T15:46:08Z - Historical Replay - MACD-Removed Research Variant Added

- `decision`: Add a research-only MACD-removed historical replay path to the PT0.0.2 Historical Replay cockpit.
- `scope`: The replay summary now includes OG replay/strategy and MACD-removed rows across BTC/ETH/SOL x 15m/1h/4h, and the dashboard exposes a replay-strategy dropdown under Historical Replay.
- `result`: MACD entry confirmation and MACD-rollover exit checks are removed only for this historical replay variant. Production Money Flow rules, order behavior, live trading boundaries, and sandbox execution plumbing remain unchanged.
- `follow_up_implications`: Founder review can compare OG baseline versus MACD-removed behavior visually before any future strategy-design decision. Any production rule change remains separately unapproved.

## 2026-05-11T14:18:00Z - PT0.0.2 - Historical Candles Are Strategy Truth

- `decision`: Pause Hyperliquid testnet-live market monitoring as a strategy-truth source and add a Historical Replay cockpit for Money Flow visual validation.
- `scope`: PT0.0.2 uses historical public candle replay data for BTC/ETH/SOL across 15m/1h/4h, generates a committed replay summary JSON, and renders historical TradingView candles, EMA overlays, green/red entry/exit markers, trade inspector, dynamic 10,000 USDC equity, BTC/ETH/SOL comparison, and a separate sandbox execution ledger.
- `result`: Hyperliquid testnet prices are explicitly not strategy truth; testnet remains sandbox execution plumbing only. No orders were submitted, no private/signed/order endpoints were called, no API keys were used, and Money Flow rules were unchanged.
- `follow_up_implications`: PT0.0.3 may add playback controls and market-structure inspection. PT0.1 supervised runtime must use trusted market data for strategy truth and continue to keep live trading and real-capital trading unapproved.

## 2026-05-11T11:42:10Z - PT0.0.1 - TradingView Chart Stability P0 Fixed

- `decision`: Stabilize the PT0 TradingView Lightweight Charts cockpit before any supervised paper/sandbox runtime week.
- `why`: Founder review found the page/chart grew or scrolled downward without user action and snapped back around the 15-second public market refresh, making the dashboard unusable for monitoring.
- `scope`: PT0.0.1 bounds chart height, contains chart parents, reuses existing chart/series handles across live refreshes, removes the `autoSize` / ResizeObserver `applyOptions` feedback-loop risk, limits `fitContent()` to new symbol/timeframe initialization, preserves the single polling timer guard, and adds `disableLivePolling` / `livePolling=false` query flags for local JSON fallback. It does not submit orders, add order controls, call private/signed/order/live endpoints, use exchange API keys, change Money Flow rules, or change PT0 paper/sandbox routing policy.
- `result`: Static/dashboard tests now cover the risky chart patterns and public-read-only/no-order boundaries. Browser visual confirmation remains the final operator check before PT0.1 is run continuously.
- `follow_up_implications`: PT0.1 may be scoped only after founder/operator confirms the chart no longer auto-scrolls/grows during real browser monitoring; live trading and real-capital trading remain not approved.

## 2026-05-11T08:08:44Z - UAT4.2 - Live Market Dashboard And Paper-Equity Monitor Added

- `decision`: Add a read-only UAT4.2 market-monitor and internal paper-equity visibility layer to the exchange-style dashboard without creating a trading runtime.
- `why`: UAT4.1 improved the dashboard layout, but the founder still needed practical visibility into watched-pair market state, indicators, signal markers, sandbox account confirmation, and internal paper-equity state before any later paper/sandbox runtime can be considered.
- `scope`: UAT4.2 adds public-read-only monitor helpers, deterministic indicator computation, paper-observation scanner records, a 60-second sandbox private-read-only balance polling policy, an internal 10,000 USDC paper-equity ledger, a current-equity sizing-policy view, dashboard wiring, docs, and tests. It does not submit orders, add order controls, call live endpoints, call private order endpoints, use exchange API keys, create production execution artifacts or executable approvals, change Money Flow rules, add routing/SOR/fanout, or generate evidence packs.
- `result`: The dashboard now loads a UAT4.2 summary JSON with watched-pair market rows, indicators, paper-observation entry/exit markers, routed sandbox lifecycle history, sandbox balance-poll policy, and internal paper-equity status. PT0 later superseded the roadmap-only state with founder-approved Hyperliquid testnet/sandbox paper trading and broader top-20 paper/sandbox scope.
- `follow_up_implications`: PT0 later preserved current-equity sizing, risk limits, kill switch, submit-lease behavior, no-live-endpoint guarantees, dashboard monitoring, and default-disabled sandbox routing while keeping live trading and real-capital trading unapproved.

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
- `follow_up_implications`: UAT4.1 was scoped as an exchange-style dashboard redesign; UAT4.2 later added the first read-only market-monitor and paper-equity visibility path. UAT3.5 additional sandbox routing lifecycle tests remain blocked by precision-validation scope and separate approval. Paper trading, live trading, dashboard order controls, broad top-20 orders, smart routing/SOR/fanout, Money Flow rule changes, and evidence packs remain unapproved.

## 2026-05-11T07:03:40Z - UAT4.1 - Dashboard Becomes An Exchange-Style UAT Workstation

- `decision`: Rebuild the UAT dashboard around an exchange-style information architecture: compact top bar, persistent safety banner, observation-only left market rail, central chart cockpit, right order-book/market/signal/risk rail, and bottom blotter tabs. Make `apps/dashboard/DESIGN.md` the canonical dashboard design system and reduce root `DESIGN.md` to a pointer.
- `why`: Founder review found the UAT4.0 report-card layout hard to understand. The cockpit needed to answer what market is active, what Money Flow observed, where sandbox lifecycle markers occurred, what happened to routed orders, and whether paper/live/order controls are disabled without more disconnected cards.
- `rejected_alternatives`: Copying exchange branding or logos; adding order, cancel, retry, amend, approval, paper/live, route, or auto-trade controls; adding private/signed/order endpoint calls; implementing live public refresh before fixing layout hierarchy.
- `follow_up_implications`: UAT4.2 later added read-only monitor summary data, deterministic indicators, paper-observation markers, sandbox balance-poll policy, and paper-equity visibility. Further chart-library integration remains future scope. UAT3.5 additional sandbox lifecycle tests remain blocked by precision-validation scope and separate approval. Paper trading, live trading, dashboard order controls, broad top-20 orders, smart routing/SOR/fanout, Money Flow rule changes, and evidence packs remain unapproved.

## 2026-05-11T10:44:00Z - PT0 - Paper/Sandbox Runtime Foundation Is Approved For Testnet Only

- `decision`: PAPER TRADING IS APPROVED. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. PT0 is limited to Hyperliquid testnet/sandbox, an internal 10,000 USDC paper-equity ledger, top-20 Hyperliquid-supported paper/sandbox scanning, TradingView Lightweight Charts, sandbox private-read-only balance/position polling policy, and default-disabled risk-gated sandbox route candidates.
- `why`: The founder wants to monitor Money Flow behavior in real time this week with real charting, paper-equity truth, Hyperliquid sandbox confirmation, and broader supported-asset scanner visibility while preserving no-live and no-real-capital boundaries.
- `rejected_alternatives`: Enabling live trading; using live exchange API keys; real-capital trading; production auto-submit; unbounded automation; smart routing/SOR/fanout/CBBO; cross-venue routing; changing Money Flow rules; strategy optimization; market-making; submitting unsupported assets; adding a general live order button.
- `follow_up_implications`: PT0.1 may be scoped as a supervised top-20 paper/sandbox runtime week. It must keep live trading, real-capital trading, live endpoints, cross-venue routing, SOR/fanout/CBBO, unsupported-asset routing, and Money Flow rule changes blocked unless a separate explicit phase approves them.

## 2026-05-11T23:12:00Z - SV2.0.1 - Compact SV2 Rows Are Not Canonical Evidence

- `decision`: Treat SV2 compact staged rows as provisional/noncanonical until refreshed public candles pass the canonical hardened DB import/upsert path and the strategy-validation evidence-pack machinery produces non-empty pack paths. Normalize Hyperliquid public close timestamps to canonical close slots, force-close dataset-end compact open positions with entry-fee accounting, split staged/imported/evidence-ready truth, set four-sleeve runtime allocations to 0.25 each, canonicalize internal `1d`, and reject missing indicators instead of defaulting them to zero.
- `why`: SOR-EV1 and stop-loss/strategy-variant evidence need clean baseline truth. Silent open-position omission, `.999Z` close slots, staged data reported as imported, allocation sums above 100%, mixed `1D`/`1d` joins, and zero-defaulted missing indicators could make evidence conclusions misleading.
- `rejected_alternatives`: Calling compact rows canonical evidence; treating fetched/staged JSON as DB import; leaving dataset-end open positions silent; relying on Hyperliquid raw `.999Z` close timestamps; reducing independent evidence scenarios to 2,500 USDC because runtime sleeves are 0.25 each; allowing missing indicators to trigger false close/reduce behavior; starting SOR-EV1 in the same phase.
- `follow_up_implications`: SOR-EV1 remains blocked unless canonical SV2 evidence packs are generated from DB-imported hardened candle data or a separate explicit decision accepts staged compact rows as noncanonical exploratory input. No orders, private/signed/order endpoints, API keys, testnet strategy truth, live trading, SOR/fanout/CBBO, variants, or parameter optimization were added.

## 2026-05-12T04:50:16Z - SV2.0.2 - DB-Backed Canonical SV2 Evidence May Unblock SOR-EV1

- `decision`: Generate canonical SV2 evidence only after normalized Hyperliquid public mainnet candles are imported through the hardened Strategy Validation candle importer into the intended migrated `money_flow` DB. Treat BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, and AVAX as canonical evidence-supported symbols for SV2.0.2, and keep requested SHIB represented as `kSHIB` but deferred because unit semantics are not clean enough.
- `why`: SOR-EV1 needs DB-backed canonical evidence-pack paths, not compact staged rows. The intended DB is reachable and current, importer/upsert succeeds on canonical close slots, existing evidence-pack machinery can run Money Flow v1.2 across 15m/1h/4h/1d, and unsupported/deferred symbols remain reason-coded rather than silently dropped.
- `rejected_alternatives`: Calling staged compact rows canonical; committing large generated candle/evidence-pack artifacts; guessing SHIB/kSHIB unit semantics; using Hyperliquid testnet data as strategy truth; changing 15m/1h/4h or 1D parameters; adding stop-loss/RSI/MACD variants in the import/evidence phase; calling private/signed/order endpoints or submitting orders.
- `follow_up_implications`: SOR-EV1 may proceed from the SV2.0.2 canonical baseline. Future variant evidence must keep dynamic equity, canonical close-slot data, import truth, unsupported-symbol reason codes, no-testnet-strategy-truth boundaries, and no-order/no-live constraints intact.

## 2026-05-12T07:02:22Z - SV2.0.2 - Regenerate Canonical Evidence With Fully Closed Per-Pair Windows

- `decision`: Regenerate SV2.0.2 canonical evidence packs with fully closed timeframe end-boundaries and per-symbol/per-timeframe campaign configs, so each supported pair backtests as far back as that pair/timeframe's DB-imported public data allows.
- `why`: The founder asked to regenerate the evidence packs and backtest as far back as the data allows for each pair. The prior common-window config shape could clip evidence to the shortest shared symbol window, and endpoint-edge candles needed explicit fully closed boundary filtering.
- `result`: The regenerated `20260512T064916Z` run produced 36 canonical packs for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d. Effective ends are `15m=2026-05-12T06:45:00Z`, `1h=2026-05-12T06:00:00Z`, `4h=2026-05-12T04:00:00Z`, and `1d=2026-05-12T00:00:00Z`; no latest candle exceeds those boundaries.
- `follow_up_implications`: SOR-EV1 may proceed from the regenerated SV2.0.2 baseline, but evidence remains research-only and not proof of profitability. No orders, private/signed/order endpoints, API keys, testnet strategy truth, live trading, parameter optimization, SOR/fanout/CBBO, target reselection, or strategy-rule changes were added.

## 2026-05-13T15:00:08Z - EV-AUDIT1 - Evidence Is Review-Ready But No Candidate Is Clean

- `decision`: Treat current evidence as good enough for founder visual review and hypothesis filtering only. No strategy or variant is promoted as a clean candidate, and no paper/live/runtime authorization follows from EV-AUDIT1.
- `why`: The audit inventories canonical SV2.0.2 Money Flow v1.2, SOR-EV1/SOR-EV2/SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and pending STRAT-EV1 plan-only status. It finds useful signals, including `avoid_low_rolling_range_50` as the best SOR founder-review candidate and `mf_orig_1d_stage2_breakout_resistance_full_equity` as the best MF-ORIG full-equity review lane, but control-pocket damage, drawdown tradeoffs, sample/horizon limitations, no live paper-observation logs, and missing order-book/funding/partial-fill modeling prevent any production-rule conclusion.
- `rejected_alternatives`: Treating aggregate PnL improvement as enough for promotion; using dashboard date-filter recalculations as canonical evidence; approving paper/live from backtests alone; ignoring 15m/1h public-data horizon limits; treating MF-ORIG source reconstruction as direct PDF-verified while the PDF remains unavailable locally; regenerating evidence packs in the audit phase.
- `follow_up_implications`: If the founder wants live observation, scope `PT-RT1` as real-time public market data plus internal paper observation with no production rule change, no live trading, and no order submission. Any later SOR/MF-ORIG rule proposal needs stricter control-pocket preservation, out-of-sample-style slices, and paper-observation evidence.

```yaml
research_log:
  phase: EV-AUDIT1
  date: 2026-05-13
  class: audit
  outcome: context
  badge: audit baseline
  title: Full Hypothesis + Paper-Readiness Audit
  finding: >-
    No clean strategy candidate. Evidence good enough for visual review and
    hypothesis filtering only - not for a production rule change.
  why: >-
    Audit, not a strategy test - it scored the whole evidence estate and
    found no hypothesis whose support survives methodology scrutiny.
  worked: >-
    Establishing the discipline this whole log enforces - no promotion on
    aggregate PnL; OOS, control-pocket, and concentration scrutiny required.
  didnt: >-
    The evidence estate as promotion support - horizon truncation, missing
    forward observation, and unmodeled execution were named as P-level gaps.
  lesson: >-
    Audit the measurement system before trusting any result it produced.
  our_error: null
  changed: >-
    Paper observation (PT-RT1) was conditionally green-lit as a separately
    scoped phase; promotion remained blocked.
  hardened_gate: no promotion on aggregate PnL
  evidence_summary: docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json
```

## 2026-05-14T01:22:49Z - PT-RT1 - Paper Observation Truth Is Public Mainnet, Testnet Is Plumbing Only

- `decision`: Implement PT-RT1 as two strictly separated lanes: public Hyperliquid mainnet strategy truth with synthetic paper ledgers, and Hyperliquid testnet plumbing probes with exact approval/cap/kill-switch/cancel-reconcile gates.
- `why`: EV-AUDIT1 found historical evidence useful for visual review and hypothesis filtering only. Founder decisions now need forward observation without confusing testnet fills, sandbox plumbing, or dashboard filters with strategy PnL truth.
- `rejected_alternatives`: Using Hyperliquid testnet prices as strategy truth; letting testnet fills update paper PnL; approving production paper runtime; enabling live trading; creating production `OrderIntent` / `PreparedVenueOrder` / `SubmittedOrder` artifacts from paper signals; regenerating historical evidence packs; adding SOR/fanout/CBBO/routing behavior.
- `follow_up_implications`: Run the 24-hour probes-disabled dry run, then begin the 60-day public-mainnet forward-observation window only if data health, closed-candle gating, duplicate prevention, and synthetic ledger accounting remain stable. Testnet plumbing probes require separate exact approval text and remain isolated from strategy PnL.

## 2026-05-16T11:30:00Z - PT-RT1 - Dashboard Runtime Uses 20 USDC Testnet Probe Audit Rows

- `decision`: Enable PT-RT1 dashboard-started testnet probe audit/order-shape rows with an exact 20 USDC notional per synthetic `paper_opened` signal while keeping public-mainnet data as strategy truth and synthetic paper PnL independent.
- `why`: The founder requested testnet probe visibility during paper observation but corrected the per-signal notional to 20 USDC. The runtime needs an inspectable plumbing trail without letting testnet fills or prices become strategy evidence.
- `rejected_alternatives`: Using the earlier 10 USDC cap, submitting signed testnet orders from PT-RT1, letting testnet fills update strategy paper PnL, adding dashboard order controls, using private/signed/order endpoints from strategy truth, or changing Money Flow strategy rules.
- `follow_up_implications`: `scripts/run_dashboard_control_server.py` starts PT-RT1 with `--enable-testnet-probes`, `--founder-approved-testnet-probes-20usdc`, `--testnet-probe-notional-usdc 20`, `--public-mainnet-only`, and compact logging. PT-RT1 currently records audit/order-shape rows only and explicitly records `order_endpoint_called=false` and `signed_order_endpoint_called=false`; any real signed testnet transport submission remains separately scoped.

## 2026-05-16T12:58:09Z - PT-RT1.3 - Closed Candles, Not Public Mids, Gate Strategy Data Health

- `decision`: Treat stale/thin/missing/nonpositive Hyperliquid public `allMids` as non-blocking operator warnings when clean fully closed public-mainnet `candleSnapshot` rows are available.
- `why`: The latest local runtime review showed false-positive `data_unavailable` rows for quiet Hyperliquid pairs whose mids did not tick frequently. Strategy truth is candle-based, so mid freshness should not block paper-decision evaluation when candles and indicators are available.
- `rejected_alternatives`: Keeping mid freshness as the scanner eligibility gate; hiding mid issues entirely; treating degraded/malformed candles as usable; changing strategy rules to compensate for data-health labels.
- `follow_up_implications`: Fresh PT-RT1.3 runs should show mid warnings separately from blocking candle/indicator unavailable rows. Founder review should inspect `summary.json`, `data_health.json`, and `decisions.jsonl` before treating any forward observation run as usable evidence. No production rules, paper/live approval, private/signed/order endpoints, API keys, testnet strategy truth, or SOR behavior were added.

## 2026-05-17T09:47:55Z - PT-RT1.4 - Paper Trading Weekly Review Uses 1h / 4h / 1d

- `decision`: Pause `15m` from active Week 1 paper trading and make Paper Trading the founder weekly command center scoped by selected timeframe. Active timeframes are `1h`, `4h`, and `1d`; `15m` is `disabled_for_week1_noise_reduction`, preserved as paused/legacy data, and excluded from active scoring and new synthetic entries.
- `why`: Founder review found the prior Paper Trading page confusing because lane comparison blended timeframes, 15m created too much runtime noise, open/closed tables were hard to read, and testnet audit-shape labels could look like enabled order transport.
- `rejected_alternatives`: Deleting existing 15m runtime records; silently hiding legacy 15m open positions; aggregating all timeframes without labels; calling audit-only testnet shapes "probes enabled" without transport context; enabling signed testnet transport; changing production Money Flow rules.
- `follow_up_implications`: Fresh active-week review should focus on 1h/4h/1d. All-active mode must mean only `1h + 4h + 1d` and not one combined account. Testnet order transport remains disabled; audit-only shapes remain separate from strategy PnL. No live trading, production strategy approval, private/signed/order endpoints from strategy truth, or SOR/fanout/CBBO behavior follows from this cleanup.

## 2026-05-17T14:51:49Z - PT-RT1.5.1 - Signed Testnet Transport Requires Fresh Baseline Signals

- `decision`: Archive the pre-warm-start PT-RT1.5 smoke rows, default fresh review to `pt_rt1_5_1_smoke`, require warm-start false-to-true signal gating before synthetic opens, and allow signed Hyperliquid testnet transport only for fresh post-start Money Flow v1.2 baseline `paper_opened` signals on `1h`/`4h`/`1d` with fixed 25 USDC notional.
- `why`: The first PT-RT1.5 smoke created synthetic opens from confirmations that were already true at runtime start and built 22 testnet lifecycle rows that stopped at `preflight_passed` because signed transport was not configured. Open-position rows also needed public-mainnet mark-to-market instead of displaying missing marks as zero.
- `rejected_alternatives`: Treating startup-valid confirmations as tradable signals; letting candidate/MF-ORIG/wildcard lanes send testnet orders; using testnet prices or fills as strategy truth; falling back to old active runtime files by default; showing zero unrealized PnL when no mark is available; changing production Money Flow rules; enabling live trading.
- `follow_up_implications`: Run/review `pt_rt1_5_1_smoke` before Week 1. Confirm startup-valid rows are blocked, fresh baseline opens can create signed testnet lifecycle rows when local env and gates pass, candidate transport remains blocked, open-position MTM is populated or explicitly unavailable, testnet fills do not update synthetic PnL, and no live/prod approval follows.

## 2026-05-17T16:36:34Z - PT-RT1.5.2 - Signed Testnet Transport Smoke Reaches Venue

- `decision`: Verify signed Hyperliquid testnet transport with one explicitly labeled `testnet_transport_smoke_not_strategy_signal` row, keep fresh baseline-only transport gates, and move the preferred active Week 1 runtime scope to `pt_rt1_5_2_week1_active`.
- `why`: PT-RT1.5.1 had the signed client path wired but prior shells could fail closed when local signing env was absent. The founder approved one scoped PT-RT1.5.2 testnet transport smoke if no fresh Money Flow v1.2 baseline signal occurred during the smoke window.
- `result`: The bounded PT-RT1.5.2 smoke loaded local env through a scoped allowlist without printing secrets, connected to public mainnet for candle context, configured the signed testnet transport client, called the Hyperliquid testnet signed order endpoint once with fixed 25 USDC notional, received sanitized venue reject `Order has invalid size.`, reconciled to no open order, created no synthetic trade, and did not update synthetic PnL.
- `rejected_alternatives`: Using testnet prices as strategy truth; letting the smoke appear as a strategy trade; routing candidate/MF-ORIG/wildcard/15m lanes to testnet; enabling live endpoints; starting a long-running background process from Codex without operator supervision; changing production Money Flow rules.
- `follow_up_implications`: Start the clean active runtime under `reports/paper_runtime/pt_rt1_5_2_week1_active/`. Before relying on accepted/open lifecycle coverage, fix or verify the testnet size formatter/min-size behavior that produced `Order has invalid size.` Candidate lanes remain synthetic-only, public mainnet candles remain strategy truth, testnet fills never update synthetic PnL, and no live/prod approval follows.
