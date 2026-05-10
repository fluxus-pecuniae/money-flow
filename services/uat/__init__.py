"""Research/UAT readiness helpers.

Policy helpers are fixture-testable by default. UAT1 public-read-only helpers
may connect only when explicit public-read-only network flags are supplied.
UAT1.1 shadow helpers define model/report-only audit and drawdown surfaces for
future UAT2. No helper submits orders, creates execution artifacts, or
authorizes paper/live trading.
"""
