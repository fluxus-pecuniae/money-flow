# Money Flow Command Center

Canonical command center: [[00_Money_Flow_Command_Center|00 Money Flow Command Center]]

This compatibility note intentionally points to the canonical command center so duplicate current-truth dashboards do not drift.

Current implemented phase: `SV1.12`

Current focus: Strategy Validation guarded canonical candle import. The intended local `money_flow` DB must remain migrated/current, research identity must be operator-verified and non-trading, timezone-explicit candle files must map one-to-one to canonical requirements and pass requirement-aware preflight before import, no evidence packs are generated in SV1.12, and paper trading is not approved.

Repo operational truth still lives in `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`.
