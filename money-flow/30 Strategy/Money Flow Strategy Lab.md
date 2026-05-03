# Money Flow Strategy Lab

Up: [[Money Flow Command Center]]

## Purpose

Keep the strategy thread visible while routing and execution work becomes complex.

## Current Money Flow Role

Money Flow is the first strategy family. It is not the universal vocabulary of the platform.

Current Strategy Validation focus: `SV1.9.1` has hardened evidence-target and candle-import truth before first real canonical evidence packs. No first real canonical Money Flow evidence packs have been generated yet, and paper trading is not approved.

The original strategy idea involved:

- 5 EMA
- 10 EMA
- 20 SMA
- RSI
- MACD
- 15m / 1h / 4h lanes

## Current Code Surface

- `services/strategy/money_flow.py`
- `services/strategy/engine.py`
- `services/indicators/service.py`
- `services/planning/service.py`

## Questions To Keep Alive

- Are the 15m, 1h, and 4h behaviors still faithful to the intended Money Flow logic?
- What evidence proves or disproves the strategy alpha?
- What strategy families should come after Money Flow?
- Which execution controls are needed because the strategy actually needs them, not because the router can do them?

## Related Notes

- [[10 Components/Strategy Engine]]
- [[10 Components/Market Data and Indicators]]
- [[30 Strategy/Product North Star]]
