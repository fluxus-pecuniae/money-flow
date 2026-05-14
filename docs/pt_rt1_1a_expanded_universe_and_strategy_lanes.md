# PT-RT1.1A Expanded Universe And Strategy Lanes

## Objective

Status: implemented

PT-RT1.1A expands the PT-RT1 forward paper-observation lab before the 24-hour probes-disabled run starts. It does not start runtime collection, enable testnet probes, submit orders, approve paper/live trading, change production Money Flow rules, regenerate canonical evidence packs, or use testnet prices/fills as strategy truth.

## Why This Happened Before The Run

Status: implemented

PT-RT1.1 produced a blocked dry-run report because the 24-hour artifact set did not exist. Before collecting that artifact set, the founder requested a wider observation universe, 10 synthetic paper lanes, three wildcard expert hypotheses, requested/resolved symbol visibility, blocked-symbol reason codes, and expanded dashboard review surfaces.

## Ten Strategy Lanes

Status: implemented

Each lane is synthetic paper only, evidence-only, non-production, not live-approved, and starts with an independent `10000 USDC` ledger. Lanes compound realized wins/losses forward and are not combined into one account.

| Lane | Family | Status |
|---|---|---|
| `money_flow_v1_2_baseline` | Current Money Flow v1.2 control | implemented |
| `avoid_low_rolling_range_20` | SOR-EV3 candidate | implemented |
| `avoid_low_rolling_range_50` | SOR-EV3 candidate | implemented |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG reference | implemented |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG reference | implemented |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG reference | implemented |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG reference | implemented |
| `wildcard_btc_regime_guard` | Wildcard expert hypothesis | implemented |
| `wildcard_multi_timeframe_alignment` | Wildcard expert hypothesis | implemented |
| `wildcard_volatility_expansion_breakout` | Wildcard expert hypothesis | implemented |

## Wildcard Definitions

Status: implemented

- `wildcard_btc_regime_guard`: blocks non-BTC entries unless BTC 4h/1d context is constructive; reason codes include `btc_regime_guard_passed`, `btc_regime_guard_blocked_bearish`, and `btc_regime_context_unavailable`.
- `wildcard_multi_timeframe_alignment`: blocks lower-timeframe entries that lack higher-timeframe alignment; reason codes include `multi_timeframe_alignment_passed`, `multi_timeframe_alignment_blocked`, and `higher_timeframe_context_unavailable`.
- `wildcard_volatility_expansion_breakout`: blocks low-range sideways entries unless compression resolves through a recent-high breakout while baseline alignment remains valid; reason codes include `volatility_expansion_breakout_passed`, `volatility_expansion_blocked_low_range`, and `volatility_expansion_no_recent_high_breakout`.

These wildcard lanes are observation-only hypotheses. They are not production rules.

## Expanded Requested Symbol Universe

Status: implemented

Canonical SV2.0.2 symbols remain:

`BTC, ETH, SOL, XRP, DOGE, HYPE, BNB, SUI, AVAX`

Founder-requested additions are represented:

`TRON, ADA, ZEC, LINK, XMR, TON, LTC, UNI, DOT, ASTER, AAVE, POL, FIL, TRUMP, PEPE, OKB`

The runtime resolver preserves requested symbols, resolved venue symbols, sources, precision status, public-mid status, scanner eligibility, blocked status, and reason codes.

## Alias Mapping And Blocked-Symbol Policy

Status: implemented

| Requested | Resolved | Policy |
|---|---|---|
| `TRON` | `TRX` | Allowed only if public Hyperliquid metadata, precision, and public mids confirm eligibility at runtime. |
| `PEPE` | `kPEPE` | Blocked by default with `pepe_kpepe_unit_semantics_deferred`. |
| `OKB` | `OKB` | Blocked unless public Hyperliquid metadata confirms active support. |
| `POL` | `POL` | Must resolve to active `POL`; delisted `MATIC` mapping is blocked with `pol_matic_delisted_mapping_blocked`. |
| `SHIB` | `kSHIB` | Still deferred with unit-semantics reason codes. |

Unsupported, delisted, missing-precision, missing-mid, nonpositive-mid, ambiguous, stablecoin, or unit-deferred symbols remain visible instead of being silently dropped.

## Scanner Eligibility Policy

Status: implemented

A symbol is scanner-eligible only when it exists in current Hyperliquid public mainnet metadata, is not delisted, has `szDecimals`, has positive public `allMids`, has accepted unit semantics, has unambiguous identity, has precision formatting, and data health is healthy.

PT-RT1.1A does not fetch public metadata or mids. Runtime collection remains the next step and must populate health/eligibility fields from public mainnet data only.

## Testnet Probe Separation

Status: verified

Testnet probes remain disabled and kill-switched by default:

- `PT_RT1_TESTNET_PROBES_ENABLED=false`
- `PT_RT1_TESTNET_KILL_SWITCH=true`

Blocked symbols are rejected from probe eligibility with explicit testnet reason codes. Testnet fills cannot update synthetic strategy PnL.

## Dashboard Update Status

Status: implemented

The Paper Observation dashboard now exposes:

- all 10 strategy lanes;
- expanded requested/resolved scanner symbols;
- blocked symbols and reason codes;
- lane detail for selected strategy lanes;
- wildcard diagnostics;
- synthetic strategy PnL fields and runtime-empty states;
- separate testnet plumbing probe status.

Dashboard filters remain display-only and do not mutate ledgers.

## What Remains Before The 24-Hour Run

Status: needs_followup

PT-RT1.1B now follows this readiness expansion by connecting the runtime to Hyperliquid public mainnet data and running a bounded smoke cycle. The full 24-hour probes-disabled collection is still a separate PT-RT1.1C step and must verify public mainnet refresh stability, fully closed candle gating over time, indicator availability, ledger updates, duplicate-signal blocking, data-health gating, dashboard runtime readability, probes disabled, and no private/signed/order/API-key use.

## Decision

**PT-RT1.1B may connect public mainnet data and prepare PT-RT1.1C**

PT-RT1.1B is still not approval for PT-RT1.2 testnet probes. PT-RT1.2 remains blocked until a real probes-disabled runtime collection passes the dry-run criteria.

## No-Order / No-Live Confirmation

Status: verified

No production Money Flow rules changed. No canonical historical evidence packs were regenerated. No runtime collection started. No testnet probes were enabled. No live or testnet orders were submitted. No private/signed/order endpoints were called from the strategy-truth lane. No API keys were used for strategy truth. No live trading, production paper runtime, SOR/fanout/CBBO, or real-capital behavior was approved.
