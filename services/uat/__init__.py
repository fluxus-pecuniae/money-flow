"""Research/UAT readiness helpers.

Policy helpers are fixture-testable by default. UAT1 public-read-only helpers
may connect only when explicit public-read-only network flags are supplied.
UAT1.1 shadow helpers define model/report-only audit and drawdown surfaces for
future UAT2. UAT2 shadow helpers run bounded no-order public-read-only Money
Flow observation and emit shadow audit records only. No helper submits orders,
creates execution artifacts, or authorizes paper/live trading.
"""
