# Product North Star

Up: [[Money Flow Command Center]]

## Core Idea

Money Flow is not a single-exchange bot. It is becoming a strategy platform that can generate signals, evaluate policy, form mandate-level desired trades, route across eligible account groups, and execute across multiple venues when the lower layers are mature enough.

## Product Tracks

- Strategy track: build and validate profitable strategies.
- Execution/routing track: preserve truthful execution boundaries and controlled routing.
- Product/business track: become operable, explainable, and eventually sellable.

## Long-Term Platform Shape

```text
Client
  VenueAccounts
  StrategyMandates
    MandateAccountBindings
    StrategyComponentConfigs
    desired trades
    future routing/account-group policy
```

## Keep Repeating

- Strategies make the platform valuable.
- Execution trust makes it usable.
- Routing should serve strategy, not distract from it.
- Build dangerous automation last.
- The investor narrative should stay understandable to normal people and should not claim smart routing, broad auto-submit, or production dashboard capability before those exist.

## Related Notes

- [Investor Overview](../../docs/investors.md)
- [[30 Strategy/Money Flow Strategy Lab]]
- [[30 Strategy/Business and Product Track]]
- [[20 Workflows/Deferred Smart Routing]]
- [[40 Operations/Future Work Roadmap]]
