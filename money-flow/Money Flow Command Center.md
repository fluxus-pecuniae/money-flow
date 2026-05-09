# Money Flow Command Center

Canonical command center: [[00_Money_Flow_Command_Center|00 Money Flow Command Center]]

This compatibility note intentionally points to the canonical command center so duplicate current-truth dashboards do not drift.

Current implemented phase: `SV1.18` evidence credibility closeout and UAT candidate freeze.

Current focus: SV1.18 closes the current Hyperliquid Strategy Validation evidence cycle and freezes exactly one UAT observation candidate: Hyperliquid ETH `sleeve_1h` baseline current Money Flow rules. UAT is plumbing and behavior validation only, not performance validation. The intended local `money_flow` DB is migrated/current, Hyperliquid BTC/ETH/SOL research identity is operator-verified and non-trading/non-strategy-eligible, the 9 timezone-explicit public YTD/recent files were guarded-imported with `25848` candles inserted, and SV1.13 generated component-scoped evidence packs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`. 15m, 4h, BTC/SOL 1h, lower-RSI variants, market-structure variants, and cross-venue candidates are excluded from current UAT scope. SV1.12.5 also records supported-venue inventory: Aster/Binance produced 18 additional native-trade-count candidate files, OKX/Coinbase are blocked by missing public trade count, and Kraken is blocked by incomplete public REST coverage. Paper trading is not authorized.

Repo operational truth still lives in `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`.
