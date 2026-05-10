"""Research/UAT readiness helpers.

Policy helpers are fixture-testable by default. UAT1 public-read-only helpers
may connect only when explicit public-read-only network flags are supplied.
UAT1.1 shadow helpers define model/report-only audit and drawdown surfaces for
future UAT2. UAT2 shadow helpers run bounded no-order public-read-only Money
Flow observation and emit shadow audit records only. UAT3 sandbox helpers are
fixture/readiness validators only. UAT3.0.5 helpers validate sandbox/testnet
private-read-only credential/drawdown boundaries without retaining secret values
or enabling order endpoints. UAT3.0.6 helpers wire the future sandbox submit
path in dry-run mode only, with no order transport. No helper submits orders, creates execution
artifacts, or authorizes paper/live trading.
"""
