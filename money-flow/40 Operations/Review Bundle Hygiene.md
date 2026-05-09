# Review Bundle Hygiene

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

Use `scripts/create_review_bundle.py` for phase handoff bundles.

Review bundles must exclude:

- generated evidence packs
- local candle files
- local DB/SQLite files
- nested archives
- Obsidian app state
- secrets
- `.env`
- `.venv`
- Git metadata
- caches
- review bundles

Use `.archiveignore` as the source of truth for exclusions.
