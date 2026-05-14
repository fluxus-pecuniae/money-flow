# PT-RT1 60-Day Forward Observation Plan

## Scope

PT-RT1 observes strategy behavior in real time using public mainnet market data and synthetic paper ledgers.

It is not:

- production approval
- paper-runtime approval as production behavior
- live trading approval
- exchange order automation
- historical evidence regeneration

## Start Criteria

- 24-hour dry run with probes disabled passes.
- PT-RT1.1A expanded readiness is in place: 10 synthetic lanes, expanded requested/resolved scanner universe, blocked-symbol reason codes, and wildcard diagnostics.
- Public mainnet market data health is stable.
- Fully closed candle gating is verified.
- Indicator missing values do not default to zero.
- Duplicate signal prevention is verified.
- Each strategy lane has an independent 10,000 USDC synthetic ledger.
- Dashboard Paper Observation view is readable.
- Testnet probes remain disabled unless separately approved.

## Strategy Lanes

| Lane | Purpose |
|---|---|
| `money_flow_v1_2_baseline` | control lane |
| `avoid_low_rolling_range_20` | evidence-only candidate lane |
| `avoid_low_rolling_range_50` | evidence-only candidate lane |
| `mf_orig_stage_filter_only_full_equity` | MF-ORIG evidence-only reference lane |
| `mf_orig_stage2_pullback_reclaim_full_equity` | MF-ORIG evidence-only reference lane |
| `mf_orig_1d_stage2_5_20_crossover_full_equity` | MF-ORIG evidence-only reference lane |
| `mf_orig_1d_stage2_breakout_resistance_full_equity` | MF-ORIG evidence-only reference lane |
| `wildcard_btc_regime_guard` | wildcard expert hypothesis lane |
| `wildcard_multi_timeframe_alignment` | wildcard expert hypothesis lane |
| `wildcard_volatility_expansion_breakout` | wildcard expert hypothesis lane |

## Daily Review Checklist

- Public mainnet data health by symbol/timeframe.
- Last fully closed candle per symbol/timeframe.
- New synthetic entries/exits/skips.
- Open synthetic positions and unrealized PnL.
- Closed synthetic trades and realized PnL.
- Total paper equity per lane.
- Max/current drawdown per lane.
- Consecutive losses and worst losing streak.
- Duplicate signal blocks.
- Data-health blocks.
- Candidate differences vs baseline.
- Wildcard reason-code behavior.
- Blocked requested symbols and updated public mainnet eligibility.
- Dashboard filter usage remains display-only.

## Weekly Review Checklist

- Lane-by-lane realized equity progression.
- Drawdown and losing-streak concentration.
- Sideways/low-volatility candidate behavior.
- MF-ORIG reference lane behavior.
- Symbol/timeframe concentration.
- Whether control pockets are preserved or damaged.
- Data outages or stale candles.
- Any runtime bug or audit finding.
- Whether testnet plumbing probes remain separate.

## Disqualification Criteria

A lane should be disqualified from further candidate consideration if:

- it depends on stale/degraded data,
- it duplicates entries on repeated refresh loops,
- drawdown is materially worse than the baseline,
- it damages control pockets,
- it underperforms both fill comparison assumptions if tracked,
- results depend on one symbol/timeframe,
- paper accounting fails invariant checks,
- it requires testnet fills as strategy truth.

## Promotion Criteria For A Future Evidence Phase

A lane may be considered for a later evidence phase only if:

- observation is true forward,
- public-mainnet data health remains acceptable,
- paper accounting is consistent,
- drawdown is controlled,
- losing streaks are explainable and acceptable,
- candidate behavior improves vs baseline without destroying controls,
- no production/paper/live approval language is used.

## Boundary

No live trading is approved. No live orders are submitted. No private/signed/order endpoints are called from the strategy-truth lane. Testnet probes are plumbing-only and do not affect strategy PnL.
