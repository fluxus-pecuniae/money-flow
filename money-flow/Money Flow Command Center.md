# Money Flow Command Center

Canonical command center: [[00_Money_Flow_Command_Center|00 Money Flow Command Center]]

This compatibility note intentionally points to the canonical command center so duplicate current-truth dashboards do not drift.

Current implemented milestone: `PT0.0.3` Historical Data Horizon + 1D Replay Support complete.

Current focus: Strategy Validation SV1 is closed for now. UAT0-UAT3.4 safety, shadow, sandbox-gate, Hyperliquid ETH `sleeve_1h` sandbox lifecycle, fixed-target routing, routed-ledger, and unified-equity compatibility work is complete. UAT4.0 added the read-only chart cockpit, UAT4.1 rebuilt it as an exchange-style workstation, and UAT4.2 added public-read-only monitor rows, deterministic indicators, paper-observation markers, a 60-second sandbox private-read-only balance polling policy, and an internal 10,000 USDC paper-equity ledger. PT0 is complete: PAPER TRADING IS APPROVED. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. PT0.0.2 adds a Historical Replay cockpit using historical public candle replay data, not Hyperliquid testnet prices, as strategy truth for BTC/ETH/SOL x 15m/1h/4h. PT0.0.3 adds 1D historical replay support, Jan 2025 target-start readiness truth, and explicit 4h-to-1D aggregation labeling without creating a production Money Flow 1D sleeve. This approval is Hyperliquid testnet/sandbox only, uses an internal 10,000 USDC paper-equity ledger, and keeps live trading, real-capital trading, live endpoint use, production auto-submit, smart routing/SOR/fanout/CBBO, cross-venue routing, and Money Flow rule changes not approved. Live trading is not approved. Live exchange order submission is not approved. UAT/PT remains plumbing and behavior validation plus controlled paper/sandbox runtime foundation, not performance validation.

Repo operational truth still lives in `AGENTS.md`, `CHANGELOG.md`, `REPO_TREE.md`, `KNOWN_ISSUES.md`, `TODO.md`, `README.md`, `docs/architecture.md`, and `docs/strategy.md`.
