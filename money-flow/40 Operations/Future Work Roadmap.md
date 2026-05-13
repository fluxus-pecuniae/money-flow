# Future Work Roadmap

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Immediate Future

Current implemented documentation/governance milestone: `OB2.0` Obsidian Strategy Brain + Evidence Architecture Refresh, on top of completed `EV-AUDIT1`.

Historical context: SV1.18 closed the first Strategy Validation cycle, and UAT0 through UAT4.2 are completed plumbing/observability milestones. They remain context, not the active next phase.

Recommended next phase: `PT-RT1` real-time public market data + paper observation runtime.

PT-RT1 is not approved or implemented by OB2.0. It must be separately scoped as paper observation only:

- public mainnet market data as strategy truth;
- fully closed candle detection;
- real-time indicator and signal computation;
- internal 10,000 USDC paper ledger;
- realized/unrealized PnL and drawdown visibility;
- entry/exit arrows and audit trail;
- duplicate signal prevention and data outage handling;
- no exchange orders;
- no private/signed endpoints;
- no API keys;
- no live trading.

## Current Strategy And Evidence State

SV2.0.2 canonical Money Flow v1.2 evidence is the current baseline: 36 DB-imported Hyperliquid public-mainnet canonical packs across BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX and 15m/1h/4h/1d. SHIB/kSHIB remains deferred due venue unit semantics.

EV-AUDIT1 concludes:

- no clean strategy candidate is production-ready;
- evidence is good enough for visual review and hypothesis filtering only;
- evidence is not enough for production-rule change;
- evidence is not enough for strategy paper-runtime authorization;
- evidence is not enough for live trading;
- paper observation is ready with conditions.

`avoid_low_rolling_range_50` is the strongest founder-review SOR candidate but remains blocked by drawdown/control-pocket risk. MF-ORIG full-equity lanes are review evidence only and are not source-faithful production approvals.

## UAT / Sandbox Boundary

UAT1 through UAT4.2, PT0, PT0.0.2, PT0.0.3, SV2.0-SV2.0.2, SOR-EV1-SOR-EV3, MF-ORIG-EV1.1/MF-ORIG-EV2, and EV-AUDIT1 are complete or inventoried in the canonical command center.

PAPER TRADING IS APPROVED. Paper trading is approved for Hyperliquid testnet/sandbox only.

BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under metadata, precision, risk, lease, label, and no-live gates.

Live trading is not approved. Live exchange order submission is not approved. Strategy paper runtime is not approved by EV-AUDIT1 evidence.

Hyperliquid ETH `sleeve_1h` remains the frozen UAT observation context, not a production strategy.

## Current Roadmap Links

- [[00 Maps/Paper Observation Roadmap]]
- [[00 Maps/Strategy Family Map]]
- [[00 Maps/Evidence and Backtesting Map]]
- [[00 Maps/Data Source and Market Data Map]]
- [[00 Maps/Dashboard and UI Map]]
- [[10 Strategy/Strategy Status Register]]
- [[20 Evidence/EV-AUDIT1 Summary]]

## Deferred Work

- PT-RT1 real-time paper observation, separately scoped.
- MF-ORIG source-exact reconciliation against the now-present PDF if the founder wants a second source-faithful evidence pass.
- SOR-EV4 only if founder wants narrower control-pocket-preserving rolling-range follow-up.
- UAT3.5 additional sandbox lifecycle tests only after explicit approval and precision validation.
- SOR/fanout/CBBO/cross-venue routing remains deferred.
