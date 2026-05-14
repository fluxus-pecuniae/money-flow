# Paper Observation Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the roadmap and current status note for PT-RT1. It is not production approval, strategy paper-runtime approval, or live-trading approval.

## PT-RT1 Implemented Scope

PT-RT1 is implemented as a forward-observation substrate:

- public Hyperliquid mainnet market data as strategy truth
- fully closed candle detection
- real-time indicator computation
- paper-only strategy decisions
- independent internal 10,000 USDC paper ledgers per lane
- realized and unrealized PnL
- drawdown tracking
- entry/exit arrows on UI charts
- signal/event audit log
- duplicate signal prevention
- data outage handling
- founder review workflow

Required observation lanes:

- `money_flow_v1_2_baseline`
- `avoid_low_rolling_range_50`
- `avoid_low_rolling_range_20`
- `mf_orig_1d_stage2_breakout_resistance_full_equity`

Current next operational step:

1. Run the 24-hour dry run with testnet probes disabled.
2. If stable, start the 60-day public-mainnet forward-observation window.
3. Run testnet plumbing probes only after exact approval and with strategy PnL separation.

## Required Boundaries

- no exchange orders.
- No private/signed endpoints.
- No API keys.
- No live trading.
- No real capital.
- No production rule change.
- No SOR/fanout/CBBO/route executor behavior.

## UAT Sandbox vs Paper Observation

| Lane | Purpose | Data / Endpoint Truth |
| --- | --- | --- |
| UAT sandbox/testnet execution plumbing | Verify account targeting, order lifecycle, cancel/reconcile, route ledger | Hyperliquid testnet/sandbox; not strategy truth |
| Real-time paper observation | Observe strategy signals and paper PnL in current market conditions | Public mainnet market data should be strategy truth |

PT-RT1 should keep these lanes separate.

## Testnet Plumbing Probe Policy

Testnet probes are implemented but blocked by default:

- `PT_RT1_TESTNET_PROBES_ENABLED=false`
- `PT_RT1_TESTNET_KILL_SWITCH=true`
- daily cap defaults to `1`
- notional cap defaults to under `10 USDC`
- exact approval text is required
- post-only `Alo` shape only
- cancel/reconcile required
- unknown/open probe state blocks future probes
- testnet fills never update strategy paper PnL

## Readiness Decision

Current PT-RT1 status: `implemented_substrate_observation_not_started`.

This means the repo now has code, dashboard, summary JSON, tests, and runbooks to start controlled forward observation, but no 60-day observation result exists yet. It is not enough to approve production rules, paper runtime strategy authority, or live trading.
