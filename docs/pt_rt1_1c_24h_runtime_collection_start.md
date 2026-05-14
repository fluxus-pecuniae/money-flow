# PT-RT1.1C 24-Hour Runtime Collection Start

Status: runtime_collection_started

PT-RT1.1C starts the 24-hour probes-disabled runtime collection for the expanded PT-RT1 paper-observation lab. This is runtime collection only. It is not production approval, paper-production approval, live trading approval, historical evidence regeneration, or a testnet probe phase.

## Objective

Start a 24-hour public-mainnet paper-observation run after PT-RT1.1B verified the Hyperliquid public `/info` connector, expanded watchlist, 10 synthetic strategy lanes, dashboard connection panel, and disabled testnet plumbing readiness.

## Runtime Command

The managed runtime was started with:

```bash
PT_RT1_TESTNET_PROBES_ENABLED=false \
PT_RT1_TESTNET_KILL_SWITCH=true \
PT_RT1_TESTNET_DAILY_PROBE_CAP=0 \
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_1c_24h_dry_run \
  --disable-testnet-probes \
  --public-mainnet-only
```

Start metadata:

| Field | Value |
| --- | --- |
| Runtime start status | `runtime_collection_started` |
| Process id | `11158` |
| Managed tool session id | `13630` |
| Start time UTC | `2026-05-14T21:57:58Z` |
| Expected end time UTC | `2026-05-15T21:57:58Z` |
| Output directory | `reports/paper_runtime/pt_rt1_1c_24h_dry_run` |
| Dashboard URL | `http://127.0.0.1:8765/apps/dashboard/index.html` |

An earlier `nohup` background attempt did not remain alive and wrote no JSON artifacts. It is not counted as the PT-RT1.1C runtime. The active runtime is the managed process above.

## Runtime Configuration

Required probes-disabled settings are active:

| Setting | Value |
| --- | --- |
| `PT_RT1_TESTNET_PROBES_ENABLED` | `false` |
| `PT_RT1_TESTNET_KILL_SWITCH` | `true` |
| `PT_RT1_TESTNET_DAILY_PROBE_CAP` | `0` |
| `public_mainnet_only` | `true` |
| Strategy truth endpoint category | `public_read_only` |

Forbidden in this run:

- testnet prices as strategy truth
- private endpoints
- signed endpoints
- order endpoints
- API keys
- account balances as strategy truth
- sandbox/testnet fills as paper PnL truth
- live endpoint use
- production execution artifacts

## Runtime Artifacts

Runtime artifacts are ignored and must not be committed:

- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/state.json`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/decisions.jsonl`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/trades.jsonl`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/equity_curves.json`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/data_health.json`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/runtime_audit.jsonl`
- `reports/paper_runtime/pt_rt1_1c_24h_dry_run/summary.json`

The first verified runtime cycle wrote the expected ignored artifacts and reported:

| Metric | Value |
| --- | ---: |
| Requested rows resolved | 25 |
| Scanner eligible rows | 23 |
| Blocked rows | 2 |
| Market-data health rows | 92 |
| First-cycle decision rows written | 920 |
| Latest decision rows retained in summary | 200 |

## Strategy Lanes

Exactly 10 synthetic paper lanes are included:

- `money_flow_v1_2_baseline`
- `avoid_low_rolling_range_20`
- `avoid_low_rolling_range_50`
- `mf_orig_stage_filter_only_full_equity`
- `mf_orig_stage2_pullback_reclaim_full_equity`
- `mf_orig_1d_stage2_5_20_crossover_full_equity`
- `mf_orig_1d_stage2_breakout_resistance_full_equity`
- `wildcard_btc_regime_guard`
- `wildcard_multi_timeframe_alignment`
- `wildcard_volatility_expansion_breakout`

Each lane starts with an independent `10000 USDC` synthetic ledger. Lanes are not one combined account and do not reset equity after trades.

## Requested Universe

Requested symbols:

`BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX, TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, TRUMP, PEPE, OKB`

Alias policy:

- `TRON -> TRX`
- `PEPE -> kPEPE`
- `POL` must resolve to active `POL`, not delisted `MATIC`

Blocked rows from the first cycle:

| Requested | Resolved | Reason codes |
| --- | --- | --- |
| `PEPE` | `kPEPE` | `unit_semantics_deferred`, `pepe_kpepe_unit_semantics_deferred`, `symbol_supported` |
| `OKB` | `OKB` | `okb_support_not_confirmed`, `market_data_unavailable`, `public_mid_missing_or_nonpositive` |

## Dashboard Verification

Dashboard URL:

`http://127.0.0.1:8765/apps/dashboard/index.html`

The Paper Observation dashboard now prefers `reports/paper_runtime/pt_rt1_1c_24h_dry_run/summary.json` when local ignored runtime artifacts exist. It remains paper-observation only and shows:

- public mainnet connection status
- expanded watchlist
- latest public-mainnet MD ticks from browser-side `allMids` polling
- requested/resolved symbols
- blocked symbols and reason codes
- all 10 strategy lanes
- synthetic ledgers
- open synthetic positions
- closed synthetic trades
- data health
- selected-pair public-mainnet TradingView chart from `candleSnapshot`
- drawdown / losing streak state
- testnet plumbing disabled
- kill switch active
- no order controls

Required warnings remain:

- Public mainnet data is strategy truth.
- Synthetic paper results are forward observation only.
- Testnet probes are plumbing only.
- Testnet fills do not update strategy PnL.
- No strategy is production-approved.
- Live trading is not approved.
- Dashboard filters are display-only.

## Boundary Verification

PT-RT1.1C startup verified:

- testnet probes disabled
- testnet kill switch active
- daily probe cap set to zero
- no order endpoint calls
- no private endpoint calls
- no signed endpoint calls
- no API key usage for strategy truth
- no account balance usage for strategy truth
- no live endpoint usage
- no production `OrderIntent`, `PreparedVenueOrder`, or `SubmittedOrder` from the strategy-truth lane

## Operator Instructions

Let the runtime continue until the expected end time. Do not commit files under `reports/paper_runtime/`.

Safe stop if required:

```bash
kill 11158
```

After the process exits, inspect:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("reports/paper_runtime/pt_rt1_1c_24h_dry_run/summary.json")
print(json.dumps(json.loads(p.read_text())["next_phase_decision"], indent=2))
PY
```

## Handoff

Decision: `PT-RT1.1D may evaluate 24-hour runtime artifacts after completion`.

Evaluation is deferred to PT-RT1.1D. PT-RT1.2 testnet plumbing probes remain blocked until the probes-disabled runtime is complete and reviewed.

## No-Order / No-Live Confirmation

No production Money Flow rules changed. No canonical historical evidence packs were regenerated. No live orders were submitted. No testnet orders were submitted. Testnet probes remain disabled. No private/signed/order endpoints were called from the strategy-truth lane. No API keys were used for strategy truth. No Hyperliquid testnet prices or fills were used as strategy PnL truth. No strategy is production-approved. Live trading is not approved.
