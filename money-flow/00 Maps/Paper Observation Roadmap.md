# Paper Observation Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

This is the roadmap for a future PT-RT1 phase. It is not an approval.

## PT-RT1 Recommended Scope

EV-AUDIT1 recommends PT-RT1 as the next practical phase if the founder wants real-time observation:

- public mainnet market data
- fully closed candle detection
- real-time indicator computation
- paper-only strategy decisions
- internal 10,000 USDC paper ledger
- realized and unrealized PnL
- drawdown tracking
- entry/exit arrows on UI charts
- signal/event audit log
- duplicate signal prevention
- data outage handling
- founder review workflow

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

## Readiness Decision

Current EV-AUDIT1 status: `paper_observation_ready_with_conditions`.

This means the repo has enough evidence and UI substrate to scope observation, but not enough to approve production rules, paper runtime strategy authority, or live trading without a separately defined PT-RT1 phase.
