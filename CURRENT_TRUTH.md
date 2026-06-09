# CURRENT TRUTH

**Last reconciled:** 2026-06-09
**Scope:** `pt_rt1_6_week2_active`
**Canonical registry:** `current_truth.json` (generated — do not hand-edit)

> **For implementation prompts:** reference this file (`CURRENT_TRUTH.md`) and enforce its boundaries instead of re-embedding lane IDs, timeframes, or approval status inline. The machine-checkable fields in the Machine Block below are generated from code anchors and kept in sync by `tests/test_current_truth_registry.py`.

---

## Operating State

| Field | Value | Code anchor |
|---|---|---|
| Run scope | `pt_rt1_6_week2_active` | `pt_rt1.py::PT_RT1_6_RUNTIME_SCOPE` |
| Active surface | PT-RT1.6 Week 2 Paper Observation | — |
| Strategy truth | Public Hyperliquid mainnet fully closed candles and derived indicators | — |
| PnL truth | Independent synthetic 10,000 USDC paper ledgers per lane | — |
| Production approved | **No** | `pt_rt1.py::strategy_lane_summary_payload` |
| Live trading approved | **No** | `settings.py::RuntimeSafetyPolicy.live_trading_enabled = False` |

Enforcing tests: `tests/test_pt_rt1_6_week2_slate.py`, `tests/test_current_truth_registry.py`

---

## Active Week 2 Slate (3 lanes)

| Lane ID | Display Name | Role | Testnet Eligible |
|---|---|---|---|
| `money_flow_v1_2_baseline` | Money Flow v1.2 baseline | Control / Baseline | **Yes** |
| `avoid_low_rolling_range_20` | Avoid low rolling range 20 | Diagnostic Comparator | No |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG 1D Stage 2 breakout resistance full equity | MF-ORIG Source-Faithful Candidate | No |

Code anchors: `pt_rt1.py::PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS`, `pt_rt1.py::PT_RT1_6_ACTIVE_STRATEGY_LANES`, `pt_rt1.py::pt_rt1_6_lane_testnet_eligible()`

All three lanes: `production_approved=false`, `live_approved=false`, `pnl_source=Synthetic Ledger`, `signal_truth=Public Mainnet Candles`.

---

## Archived Lanes (7 lanes — default-inactive from Week 2 scoring)

| Lane ID | Display Name | Role |
|---|---|---|
| `avoid_low_rolling_range_50` | Avoid low rolling range 50 | Diagnostic Comparator |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG stage filter only full equity | MF-ORIG Source-Faithful Candidate |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG Stage 2 pullback reclaim full equity | MF-ORIG Source-Faithful Candidate |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG 1D Stage 2 5/20 crossover full equity | MF-ORIG Source-Faithful Candidate |
| `wildcard_btc_regime_guard` | Wildcard BTC regime guard | Wildcard Expert Observation |
| `wildcard_multi_timeframe_alignment` | Wildcard multi-timeframe alignment | Wildcard Expert Observation |
| `wildcard_volatility_expansion_breakout` | Wildcard volatility expansion breakout | Wildcard Expert Observation |

Code anchor: `pt_rt1.py::PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS`

---

## Timeframes

| Status | Timeframes | Code anchor |
|---|---|---|
| **Active** | `1h`, `4h`, `1d` | `pt_rt1.py::PT_RT1_6_ACTIVE_TIMEFRAMES` |
| **Paused** | `15m` | `pt_rt1.py::PT_RT1_4_DISABLED_TIMEFRAMES` |

`15m` is paused/legacy and must not be re-enabled without explicit founder decision.

---

## Configured Paper Symbols (9)

`BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `HYPE`, `BNB`, `SUI`, `AVAX`

Code anchor: `pt_rt1.py::SUPPORTED_CANONICAL_SYMBOLS`

---

## Boundaries

| Boundary | Status |
|---|---|
| Testnet fills update synthetic PnL | **Never** |
| Candidate / MF-ORIG lanes trigger testnet orders | **Blocked** |
| Only baseline testnet-eligible | `money_flow_v1_2_baseline` only |
| Testnet fixed notional | 25 USDC |
| Testnet is not strategy truth | Public mainnet candles are strategy truth |
| XRP smoke | Transport-only, not strategy signal |
| `live_trading_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `exchange_order_submission_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `private_exchange_endpoints_enabled` | `false` (default, `RuntimeSafetyPolicy`) |
| `sandbox_mode_required` | `true` (default, `RuntimeSafetyPolicy`) |

Code anchors: `pt_rt1.py::pt_rt1_6_lane_testnet_eligible()`, `pt_rt1.py::PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC`, `settings.py::RuntimeSafetyPolicy`

---

## Machine Block

> **Generated — do not hand-edit.** Re-generate with: `python scripts/export_current_truth.py`
> Drift from anchors fails: `tests/test_current_truth_registry.py`

```json
{
  "scope": "pt_rt1_6_week2_active",
  "active_surface": "PT-RT1.6 Week 2 Paper Observation",
  "strategy_truth": "Public Hyperliquid mainnet fully closed candles and derived indicators",
  "pnl_truth": "Independent synthetic 10,000 USDC paper ledgers per lane",
  "production_approved": false,
  "live_trading_approved": false,
  "active_lanes": [
    {
      "lane_id": "money_flow_v1_2_baseline",
      "display_name": "Money Flow v1.2 baseline",
      "role": "control_lane",
      "role_label": "Control / Baseline",
      "testnet_eligible": true,
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
      "lane_id": "mf_orig_1d_stage2_breakout_resistance_full_equity",
      "display_name": "MF-ORIG 1D Stage 2 breakout resistance full equity",
      "role": "mf_orig_evidence_only_reference_lane",
      "role_label": "MF-ORIG Source-Faithful Candidate",
      "testnet_eligible": false,
      "production_approved": false,
      "live_approved": false,
      "pnl_source": "Synthetic Ledger",
      "signal_truth": "Public Mainnet Candles"
    }
  ],
  "archived_lanes": [
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
    "1h",
    "4h",
    "1d"
  ],
  "paused_timeframes": [
    "15m"
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
  "testnet_eligible_lanes": [
    "money_flow_v1_2_baseline"
  ],
  "testnet_fixed_notional_usdc": 25,
  "testnet_fills_update_synthetic_pnl": false,
  "runtime_safety_policy": {
    "live_trading_enabled": false,
    "exchange_order_submission_enabled": false,
    "private_exchange_endpoints_enabled": false,
    "sandbox_mode_required": true
  }
}
```
