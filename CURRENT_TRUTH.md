# CURRENT TRUTH

**Last reconciled:** 2026-06-12
**Scope:** `pt_rt2_mf_signal_observation`
**Canonical registry:** `current_truth.json` (generated — do not hand-edit)

> **For implementation prompts:** reference this file (`CURRENT_TRUTH.md`) and enforce its boundaries instead of re-embedding lane IDs, timeframes, or approval status inline. The machine-checkable fields in the Machine Block below are generated from code anchors and kept in sync by `tests/test_current_truth_registry.py`.

---

## Operating State

| Field | Value | Code anchor |
|---|---|---|
| Run scope | `pt_rt2_mf_signal_observation` | `pt_rt1.py::PT_RT2_RUNTIME_SCOPE` |
| Active surface | PT-RT2 Fresh Money Flow Signal Observation (paper only) | — |
| Strategy truth | Public Hyperliquid mainnet fully closed candles and derived indicators | — |
| PnL truth | Independent synthetic 10,000 USDC paper ledgers per lane (fresh at PT-RT2 start; no backfill) | — |
| Observation frame | Observation of a characterized signal, not a validated strategy; watching it live does not upgrade any committed verdict | `pt_rt1.py::PT_RT2_OBSERVATION_FRAME` |
| Production approved | **No** | `pt_rt1.py::strategy_lane_summary_payload` |
| Live trading approved | **No** | `settings.py::RuntimeSafetyPolicy.live_trading_enabled = False` |

Enforcing tests: `tests/test_pt_rt2_mf_signal_slate.py`, `tests/test_current_truth_registry.py`

---

## Active PT-RT2 Slate (2 lanes — paper only)

| Lane ID | Display Name | Role | Testnet Eligible |
|---|---|---|---|
| `mf_source_faithful_baseline` | MF source-faithful baseline | Control / Baseline | No |
| `mf_source_faithful_regime_gated` | MF source-faithful + regime gate | Informational Overlay Observation | No |

Code anchors: `pt_rt1.py::PT_RT2_ACTIVE_STRATEGY_LANE_IDS`, `pt_rt1.py::PT_RT2_ACTIVE_STRATEGY_LANES`, `pt_rt1.py::pt_rt2_lane_testnet_eligible()`

Both lanes consume the committed MONEYFLOW-SIGNAL1 surface (`services/strategy_validation/moneyflow_signal1.py`) — no re-implementation, no new rule variants. Committed verdicts carried on every surface: standalone `defensive_trend_mechanic_not_validated_alpha`; trade-level `source_faithful_but_underperformed`; regime overlay `regime_filter_does_not_reduce_drawdown_oos` (informational risk context, not a validated control). Observed universe: the 7 DATA1 majors (`BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `BNB`, `AVAX`); `HYPE`/`SUI` stay configured but untraded (short histories). Both lanes: `production_approved=false`, `live_approved=false`, `testnet_eligible=false`, `pnl_source=Synthetic Ledger`, `signal_truth=Public Mainnet Candles`.

---

## Archived Lanes (10 lanes — Week 2 actives joined the archive; nothing deleted, ledgers/history untouched)

| Lane ID | Display Name | Role |
|---|---|---|
| `money_flow_v1_2_baseline` | Money Flow v1.2 baseline | Control / Baseline (archived; testnet eligibility ended with active status) |
| `avoid_low_rolling_range_20` | Avoid low rolling range 20 | Diagnostic Comparator |
| `avoid_low_rolling_range_50` | Avoid low rolling range 50 | Diagnostic Comparator |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG stage filter only full equity | MF-ORIG Source-Faithful Candidate |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG Stage 2 pullback reclaim full equity | MF-ORIG Source-Faithful Candidate |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG 1D Stage 2 5/20 crossover full equity | MF-ORIG Source-Faithful Candidate |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG 1D Stage 2 breakout resistance full equity | MF-ORIG Source-Faithful Candidate |
| `wildcard_btc_regime_guard` | Wildcard BTC regime guard | Wildcard Expert Observation |
| `wildcard_multi_timeframe_alignment` | Wildcard multi-timeframe alignment | Wildcard Expert Observation |
| `wildcard_volatility_expansion_breakout` | Wildcard volatility expansion breakout | Wildcard Expert Observation |

Code anchor: `pt_rt1.py::PT_RT2_ARCHIVED_STRATEGY_LANE_IDS`

---

## Timeframes

| Status | Timeframes | Code anchor |
|---|---|---|
| **Active** | `1d` | `pt_rt1.py::PT_RT2_ACTIVE_TIMEFRAMES` |
| **Paused** | `15m`, `1h`, `4h` | `pt_rt1.py::PT_RT2_DISABLED_TIMEFRAMES` |

The committed MONEYFLOW-SIGNAL1 surface is daily-only (page-cited); running it on other timeframes would be a new rule variant. Paused timeframes must not be re-enabled without explicit founder decision.

---

## Configured Paper Symbols (9) / Observed PT-RT2 Universe (7)

Configured: `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `HYPE`, `BNB`, `SUI`, `AVAX` (`pt_rt1.py::SUPPORTED_CANONICAL_SYMBOLS`)

Observed by the PT-RT2 lanes: `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `BNB`, `AVAX` (`pt_rt1.py::PT_RT2_UNIVERSE_SYMBOLS`) — exactly the MONEYFLOW-SIGNAL1 characterization universe. `HYPE`/`SUI` remain configured but no lane trades them (short histories; founder decision).

---

## Boundaries

| Boundary | Status |
|---|---|
| Testnet-eligible lanes | **None** (paper-only founder decision; testnet for the PT-RT2 slate is a separate future founder decision) |
| Testnet fills update synthetic PnL | **Never** |
| Any lane triggers testnet orders | **Blocked** (the runtime refuses every testnet flag under the PT-RT2 scope) |
| Testnet is not strategy truth | Public mainnet candles are strategy truth |
| Committed verdicts | Carried on every lane surface; observation does not upgrade them |
| `live_trading_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `exchange_order_submission_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `private_exchange_endpoints_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `sandbox_mode_required` | `true` (default, `RuntimeSafetyPolicy`) |

Code anchors: `pt_rt1.py::pt_rt2_lane_testnet_eligible()`, `pt_rt1.py::PT_RT2_*` verdict constants, `settings.py::RuntimeSafetyPolicy`

---

## Machine Block

> **Generated — do not hand-edit.** Re-generate with: `python scripts/export_current_truth.py`
> Drift from anchors fails: `tests/test_current_truth_registry.py`

```json
{
  "scope": "pt_rt2_mf_signal_observation",
  "active_surface": "PT-RT2 Fresh Money Flow Signal Observation (paper only)",
  "strategy_truth": "Public Hyperliquid mainnet fully closed candles and derived indicators",
  "pnl_truth": "Independent synthetic 10,000 USDC paper ledgers per lane (fresh at PT-RT2 start; no backfill)",
  "production_approved": false,
  "live_trading_approved": false,
  "observation_frame": "observation of a characterized signal, not a validated strategy; watching it live does not upgrade any committed verdict",
  "committed_characterization": {
    "standalone_label": "defensive_trend_mechanic_not_validated_alpha",
    "trade_level_label": "source_faithful_but_underperformed",
    "regime_overlay_verdict": "regime_filter_does_not_reduce_drawdown_oos",
    "regime_overlay_label": "informational risk context, not a validated control"
  },
  "active_lanes": [
    {
      "lane_id": "mf_source_faithful_baseline",
      "display_name": "MF source-faithful baseline",
      "role": "control_lane",
      "role_label": "Control / Baseline",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "mf_source_faithful_regime_gated",
      "display_name": "MF source-faithful + regime gate",
      "role": "informational_overlay_observation_lane",
      "role_label": "Informational Overlay Observation",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    }
  ],
  "archived_lanes": [
    {
      "lane_id": "money_flow_v1_2_baseline",
      "display_name": "Money Flow v1.2 baseline",
      "role": "control_lane",
      "role_label": "Control / Baseline",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "avoid_low_rolling_range_20",
      "display_name": "Avoid low rolling range 20",
      "role": "evidence_only_candidate_lane",
      "role_label": "Diagnostic Comparator",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "avoid_low_rolling_range_50",
      "display_name": "Avoid low rolling range 50",
      "role": "evidence_only_candidate_lane",
      "role_label": "Diagnostic Comparator",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "mf_orig_stage_filter_only_full_equity",
      "display_name": "MF-ORIG stage filter only full equity",
      "role": "mf_orig_evidence_only_reference_lane",
      "role_label": "MF-ORIG Source-Faithful Candidate",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "mf_orig_stage2_pullback_reclaim_full_equity",
      "display_name": "MF-ORIG Stage 2 pullback reclaim full equity",
      "role": "mf_orig_evidence_only_reference_lane",
      "role_label": "MF-ORIG Source-Faithful Candidate",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "mf_orig_1d_stage2_5_20_crossover_full_equity",
      "display_name": "MF-ORIG 1D Stage 2 5/20 crossover full equity",
      "role": "mf_orig_evidence_only_reference_lane",
      "role_label": "MF-ORIG Source-Faithful Candidate",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "mf_orig_1d_stage2_breakout_resistance_full_equity",
      "display_name": "MF-ORIG 1D Stage 2 breakout resistance full equity",
      "role": "mf_orig_evidence_only_reference_lane",
      "role_label": "MF-ORIG Source-Faithful Candidate",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "wildcard_btc_regime_guard",
      "display_name": "Wildcard BTC regime guard",
      "role": "wildcard_expert_observation_lane",
      "role_label": "Wildcard Expert Observation",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "wildcard_multi_timeframe_alignment",
      "display_name": "Wildcard multi-timeframe alignment",
      "role": "wildcard_expert_observation_lane",
      "role_label": "Wildcard Expert Observation",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    },
    {
      "lane_id": "wildcard_volatility_expansion_breakout",
      "display_name": "Wildcard volatility expansion breakout",
      "role": "wildcard_expert_observation_lane",
      "role_label": "Wildcard Expert Observation",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    }
  ],
  "active_timeframes": [
    "1d"
  ],
  "paused_timeframes": [
    "15m",
    "1h",
    "4h"
  ],
  "configured_symbols": [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "DOGE",
    "HYPE",
    "BNB",
    "SUI",
    "AVAX"
  ],
  "observed_universe_symbols": [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "DOGE",
    "BNB",
    "AVAX"
  ],
  "configured_not_traded_symbols": {
    "HYPE": "short_history_configured_not_traded_in_pt_rt2",
    "SUI": "short_history_configured_not_traded_in_pt_rt2"
  },
  "testnet_eligible_lanes": [],
  "testnet_policy": "paper-only founder decision: NO lane is testnet eligible; testnet for the PT-RT2 slate is a separate future founder decision",
  "testnet_fills_update_synthetic_pnl": false,
  "runtime_safety_policy": {
    "live_trading_enabled": false,
    "exchange_order_submission_enabled": false,
    "private_exchange_endpoints_enabled": false,
    "sandbox_mode_required": true
  }
}
```
