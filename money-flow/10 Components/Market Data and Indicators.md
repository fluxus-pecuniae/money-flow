# Market Data and Indicators

Up: [[00 Maps/Component Map]]

## Paths

- `services/market_data/service.py`
- `services/indicators/service.py`
- `db/models/trading.py`
- `tests/test_phase2_services.py`
- `tests/test_phase3_strategy.py`

## Current Role

Market data persists candles and health/checkpoint facts. Indicators are deterministic snapshots used by the strategy layer.

## Implemented

- Candle bootstrap and persistence.
- Market-data health surfaces.
- Indicator computation and snapshot persistence.
- Stale-indicator rejection in strategy evaluation.

## Deferred

- Live execution-quality top-of-book and order-book depth implementations are not wired yet.
- Composite pricing/source policy remains future work.

## Related Notes

- [[10 Components/Strategy Engine]]
- [[10 Components/Planning and Risk]]
- [[40 Operations/Known Issues Index]]
