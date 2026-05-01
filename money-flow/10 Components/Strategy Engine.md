# Strategy Engine

Up: [[00 Maps/Component Map]]

## Paths

- `services/strategy/base.py`
- `services/strategy/engine.py`
- `services/strategy/money_flow.py`
- `tests/test_phase3_strategy.py`

## Current Role

The strategy layer produces idempotent, inspectable strategy decisions. Money Flow is the first strategy family, not the whole platform.

## Money Flow Today

- Built around EMA/SMA/RSI/MACD-inspired logic.
- Supports Money Flow internal component lanes such as 15m, 1h, and 4h through component config.
- Produces hold, open, reduce, close, invalid/no-trade style decisions depending on state and indicators.

## Boundaries

- Strategy does not choose final execution venue/account.
- Strategy does not submit orders.
- Strategy should remain distinct from routing and execution.

## Related Notes

- [[30 Strategy/Money Flow Strategy Lab]]
- [[10 Components/Planning and Risk]]
- [[20 Workflows/Current Routed Workflow]]
