# Portfolio and Attribution

Up: [[00 Maps/Component Map]]

## Paths

- `services/portfolio/service.py`
- portfolio/account models in `db/models/trading.py`

## Current Role

Portfolio service loads account truth and related summaries. The platform keeps exchange truth separate from internal attribution overlays.

## Implemented Direction

- Venue account state is first-class.
- Exchange positions, balances, fills, and orders stay venue/account truth.
- Strategy and component attribution are overlays, not the source of exchange truth.

## Deferred

- Full strategy-attribution engine.
- True mandate-level aggregate account snapshot.
- Richer portfolio accounting.

## Related Notes

- [[10 Components/Runtime and Config]]
- [[40 Operations/Known Issues Index]]
- [[30 Strategy/Product North Star]]
