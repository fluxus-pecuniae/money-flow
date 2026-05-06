# Money Flow Command Center

Canonical command center: [[00_Money_Flow_Command_Center|00 Money Flow Command Center]]

This compatibility note intentionally points to the canonical command center so duplicate current-truth dashboards do not drift.

Current implemented phase: `SV1.12.5.1` import state / repo state closeout; Hyperliquid public campaign import is verified and evidence generation remains deferred.

Current focus: Strategy Validation post-import Hyperliquid evidence review. The intended local `money_flow` DB is migrated/current, Hyperliquid BTC/ETH/SOL research identity is operator-verified and non-trading/non-strategy-eligible, and the 9 timezone-explicit public YTD/recent files under `/tmp/money-flow-sv1124-public-ytd-recent/csv` were guarded-imported with `25848` candles inserted. SV1.12.5 also records supported-venue inventory: Aster/Binance produced 18 additional native-trade-count candidate files, OKX/Coinbase are blocked by missing public trade count, and Kraken is blocked by incomplete public REST coverage. Evidence packs are not generated yet, and paper trading is not approved.

Repo operational truth still lives in `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`.
