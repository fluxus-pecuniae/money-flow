# PT-RT1.6.3 - Testnet Metadata Resolver Hotfix + XRP Transport Smoke Plan

Recorded at UTC: `2026-06-08T09:08:40Z`

## Verdict

PT-RT1.6.3 implements a narrow Hyperliquid testnet metadata resolver hotfix for the currently blocked baseline transport symbols and prepares an XRP-targeted transport-only smoke path.

The active Week 2 runtime process was not restarted, stopped, or mutated during implementation. The hotfix applies to the next process start or to the explicitly scoped PT-RT1.6.3 smoke command after the current 24h window ends.

## Objective

The PT-RT1.6.2 operating review found baseline-only testnet lifecycle rows blocked by metadata/precision coverage for:

```text
XRP
LINK
DOT
LTC
UNI
TRX
ZEC
```

PT-RT1.6.3 narrows that ambiguity by:

- resolving blocked-symbol metadata from Hyperliquid testnet public `meta` when present;
- recording whether metadata was resolved, alias-resolved, or absent from testnet;
- preparing one explicit XRP `testnet_transport_smoke_not_strategy_signal` path;
- failing closed before `/exchange` if XRP metadata or size preflight is unavailable.

## Implementation Summary

The runner now has a PT-RT1.6.3-specific smoke scope:

```text
reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke
```

New CLI controls:

```text
--founder-approved-pt-rt1-6-3-xrp-testnet-metadata-smoke
--pt-rt1-6-3-testnet-smoke-symbol XRP
```

The smoke target is intentionally constrained to `XRP` for this phase. If a caller tries to use a different symbol with the PT-RT1.6.3 approval, the runner fails before runtime.

## Metadata Resolver Policy

The resolver is plumbing-only. It does not use testnet metadata as strategy truth.

Strategy truth remains:

```text
public Hyperliquid mainnet fully closed candles
```

Metadata is used only for:

```text
testnet asset id
testnet venue symbol
szDecimals
fixed 25 USDC testnet order formatting
```

New reason codes:

```text
testnet_metadata_alias_resolved
testnet_metadata_symbol_not_on_testnet
testnet_metadata_blocked_symbol_resolved
testnet_transport_smoke_xrp_targeted
```

If XRP is not present in Hyperliquid testnet metadata, the smoke blocks locally and does not call `/exchange`.

## Smoke Command

Use this only after the current 24h Week 2 runtime window ends:

```bash
.venv/bin/python scripts/build_pt_rt_week2_daily_review.py --generate --scope pt_rt1_6_week2_active

.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-minutes 15 \
  --output-dir reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke \
  --pt-rt1-5-week1-active \
  --signal-evaluation-mode candle_close_only \
  --fresh-signal-only-after-runtime-start \
  --enable-baseline-testnet-transport \
  --founder-approved-pt-rt1-6-3-xrp-testnet-metadata-smoke \
  --pt-rt1-6-3-testnet-smoke-symbol XRP \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --max-testnet-orders-this-phase 1 \
  --public-mainnet-only
```

Acceptable smoke outcomes:

- `accepted_open` then canceled/reconciled;
- venue reject with sanitized reason;
- local block with `testnet_metadata_symbol_not_on_testnet`, `testnet_metadata_unavailable`, or `testnet_order_invalid_size_preflight`.

No repeated smoke attempt is allowed in this phase without a new scoped approval.

## Restart Policy

The active `pt_rt1_6_week2_active` process should continue unchanged until its current 24h window ends.

After the 24h window:

1. Generate the daily review pack.
2. Run the XRP transport-only smoke command above.
3. Inspect `reports/paper_runtime/pt_rt1_6_3_xrp_transport_smoke/testnet_order_lifecycle.jsonl`.
4. Restart Week 2 only if the smoke result is accepted/reconciled, safely rejected, or safely blocked locally.

The active Week 2 restart command remains the existing Week 2 command; PT-RT1.6.3 does not change the active slate:

```bash
.venv/bin/python scripts/run_pt_rt1_paper_observation.py \
  --duration-hours 24 \
  --output-dir reports/paper_runtime/pt_rt1_6_week2_active \
  --decision-log-mode compact \
  --pt-rt1-5-week1-active \
  --fresh-signal-only-after-runtime-start \
  --enable-baseline-testnet-transport \
  --founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc \
  --pt-rt1-5-testnet-order-notional-usdc 25 \
  --pt-rt1-5-testnet-daily-order-cap 25 \
  --pt-rt1-5-testnet-per-symbol-daily-cap 3 \
  --signal-evaluation-mode candle_close_only \
  --disable-legacy-testnet-probes \
  --public-mainnet-only
```

## Boundaries

- No production Money Flow rules changed.
- No active Week 2 strategy slate changed.
- No runtime restart was performed by this phase.
- No manual orders were submitted by this phase.
- Candidate and MF-ORIG lanes remain synthetic-only.
- Only `money_flow_v1_2_baseline` remains testnet-eligible.
- Testnet fills do not update synthetic PnL.
- Public mainnet candles remain strategy truth.
- No live trading is approved.
- No strategy is production-approved.

## Limitations

If Hyperliquid testnet does not list XRP in public `meta`, the phase intentionally blocks locally. That is a valid fail-closed outcome and means the testnet venue cannot currently cover XRP plumbing under this path.

This phase does not solve profitability, strategy edge, or production readiness. It only improves baseline testnet plumbing metadata truth.

## Next Recommended Action

Continue the active Week 2 runtime unchanged until the current 24h window ends. Then generate the daily review, run the single XRP transport-only smoke, and restart Week 2 with the same three-lane slate only after the smoke result is reviewed.
