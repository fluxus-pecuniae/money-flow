# Runtime and Config

Up: [[00 Maps/Component Map]]

## Paths

- `core/config/settings.py`
- `core/config/profiles.py`
- `services/runtime/context.py`

## Current Role

Runtime context creates and loads the active client, focused venue account, active mandate, mandate account binding, mandate market-data source policy, and component configs.

## Current Hierarchy

```text
Client
  VenueAccount
  StrategyMandate
    MandateAccountBinding
      StrategyComponentConfig
```

## Important Boundaries

- The active runtime is mandate-first, but one process still targets one selected mandate at a time.
- Current source policy still supports one active planning/source venue per mandate.
- The hierarchy is deliberately not "one exchange bot".

## Related Notes

- [[10 Components/Domain Model]]
- [[10 Components/Planning and Risk]]
- [[30 Strategy/Product North Star]]
