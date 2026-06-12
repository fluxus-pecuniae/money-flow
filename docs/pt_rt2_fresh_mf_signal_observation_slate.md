# PT-RT2 — Fresh Paper Slate: the Source-Faithful Money Flow Signal as Live Baseline (+ Regime-Gated Twin)

> OBSERVATION OF A CHARACTERIZED SIGNAL, NOT A VALIDATED STRATEGY. The committed verdicts travel on every surface and watching the lanes live upgrades none of them: standalone `defensive_trend_mechanic_not_validated_alpha`; trade-level `source_faithful_but_underperformed`; the regime overlay carries REGIME2's honest-FAIL verdict (`regime_filter_does_not_reduce_drawdown_oos` — informational risk context, not a validated control). Paper only: synthetic ledgers, public closed candles as signal truth, NO lane is testnet eligible, no live, no approval surface.

## The three founder decisions (recorded in the Decision Log)

1. **Two-lane slate**: `mf_source_faithful_baseline` (Control/Baseline) + `mf_source_faithful_regime_gated` (Informational Overlay Observation) — both consuming the committed MONEYFLOW-SIGNAL1 surface, no re-implementation, no new rule variants.
2. **Archive, don't delete**: the 3 Week 2 active lanes joined the 7 already-archived lanes (10 archived); synthetic ledgers and history preserved untouched.
3. **Paper-only first**: NO lane is testnet eligible — the old baseline's eligibility ended with its active status; testnet for the new slate is a separate future founder decision. The runtime refuses every testnet flag under the PT-RT2 scope.

## The slate

| Lane | Role | Rule source |
|---|---|---|
| `mf_source_faithful_baseline` | Control / Baseline | Long/flat per the MONEYFLOW-SIGNAL1 source-faithful signal states (Stage-2 confirmed entry, documented p.150 exits) — the characterization's exposure semantics, full-equity synthetic ledger |
| `mf_source_faithful_regime_gated` | Informational Overlay Observation | Identical, gated by `strategy_types.resolve_regime_filter()` (committed pinned config `regime1_lb90_br6_btc_required_1d`): risk_off suppresses entries and exits opens; an unavailable gate holds prior state and flags it — never a silent default |

- Universe: the 7 DATA1 majors (BTC, ETH, SOL, XRP, DOGE, BNB, AVAX) — exactly the MONEYFLOW-SIGNAL1 characterization universe. HYPE/SUI stay configured symbols but no lane trades them (short histories).
- Timeframe: **1d only** — the committed surface is daily (page-cited); other timeframes would be a new rule variant.
- Fresh ledgers: 10,000 USDC at the phase's first closed candle; no backfill of fictional history (new scope directory `reports/paper_runtime/pt_rt2_mf_signal_observation/`).
- Every payload: `production_approved=false`, `live_approved=false`, `testnet_eligible=false`, `pnl_source=Synthetic Ledger`, `signal_truth=Public Mainnet Candles`, committed characterization labels, and (gated lane) REGIME2's verdict note verbatim.

## Reuse pins (no lookalike)

Both lanes flow through `services/strategy_validation/moneyflow_signal1.py` (`signal_states` → entry/exit/position machine) via `pt_rt1._evaluate_pt_rt2_mf_signal_decision`; the regime context builds through the committed `strategy_types.resolve_regime_filter()` seam from the runtime's own closed daily candles. Drift pins in `tests/test_pt_rt2_mf_signal_slate.py` assert the lane decision equals the surface's own decision and the verdict strings equal the committed modules'.

## Live cycle sample (2026-06-12, public read-only)

One PT-RT2 runtime cycle on real Hyperliquid mainnet candles: regime context `available=true`, `risk_on=false` (RISK_OFF as of 2026-06-12 close, config `regime1_lb90_br6_btc_required_1d`) — coherent with the MONEYFLOW-SIGNAL1 CLI's picture (7/7 majors `stage_4_markdown`). Both lanes flat on every symbol with `blocked_not_stage_2_markup`; the gated lane additionally carries `regime_risk_off_long_entries_suppressed` context when an entry would fire. Fresh ledgers at 10,000 USDC.

## Boundaries

Signal truth is public mainnet closed candles only; testnet fills can never update synthetic PnL (and no testnet pathway exists in this scope); no production Money Flow rule changed; no orders, no private/signed endpoints, no live trading, no approval surface. Observation extends trust in the surface — it never upgrades a verdict.
