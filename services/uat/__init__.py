"""Research/UAT readiness helpers.

Policy helpers are fixture-testable by default. UAT1 public-read-only helpers
may connect only when explicit public-read-only network flags are supplied; no
helper submits orders or authorizes paper/live trading.
"""
