"""Research/UAT readiness helpers.

Policy helpers are fixture-testable by default. UAT1 public-read-only helpers
may connect only when explicit public-read-only network flags are supplied.
UAT1.1 shadow helpers define model/report-only audit and drawdown surfaces for
future UAT2. UAT2 shadow helpers run bounded no-order public-read-only Money
Flow observation and emit shadow audit records only. UAT3 sandbox helpers are
fixture/readiness validators only. UAT3.0.5 helpers validate sandbox/testnet
private-read-only credential/drawdown boundaries without retaining secret values
or enabling order endpoints. UAT3.0.6 helpers wire the future sandbox submit
path in dry-run mode only, with no order transport. UAT3.1 helpers support one
explicitly founder-approved Hyperliquid testnet lifecycle probe without creating
production execution artifacts or authorizing paper/live trading. UAT3.2 helpers
add fixed-key account/API-wallet readiness before a second approved sandbox
lifecycle attempt and block before order transport when readiness fails. UAT3.3
helpers harden Hyperliquid account targeting and precision before any approved
sandbox transport and still block when target-account equity is insufficient.
UAT4.2 helpers add read-only live-market monitor and internal paper-equity
fixtures without order controls, live endpoints, or production trading artifacts.
PT0 helpers add the approved Hyperliquid testnet/sandbox paper-runtime
foundation, broader supported top-20 paper universe eligibility, internal
10,000 USDC paper-equity ledger, and risk-gated route-candidate modeling while
keeping live endpoints, real capital, and dashboard order controls disabled.
"""
