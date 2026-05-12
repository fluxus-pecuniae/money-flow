# Strategy Validation Map

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## What Strategy Validation Did

| Phase Range | Purpose | Outcome |
| --- | --- | --- |
| SV1.0-SV1.2.1 | Baseline backtest truth | Fill timing, drawdown, window, coverage, and regime truth established. |
| SV1.3-SV1.4.1 | Campaigns / evidence packs | Repeatable evidence workflow and collision-safe packs. |
| SV1.5-SV1.9.1 | Data / import / DB governance | Candle import, DB target truth, schema gates, timestamp truth, and Obsidian governance. |
| SV1.10-SV1.12.5.1 | Hyperliquid data readiness / import | Intended DB migrated, research identity seeded, and 9 public campaign files imported. |
| SV1.13-SV1.13.2 | First evidence + dynamic equity | Hyperliquid public evidence generated; ETH `sleeve_1h` was strongest observed pocket. |
| SV1.14-SV1.17 | Diagnostics / replay experiments | Trade anatomy, market-structure diagnostics, completed-trade overlays, rejected-signal replay, and full-suite true replay experiments. Variants did not beat the ETH 1h baseline control pocket. |
| SV1.18-SV1.18.1 | Closeout / UAT candidate freeze | ETH 1h baseline frozen for UAT observation; coordination handoff cleaned up. |
| SV2.0 | 1D sleeve / expanded public-mainnet evidence refresh | Money Flow v1.2 adds real `sleeve_1d`; BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX/SHIB are resolved through Hyperliquid public mainnet metadata; SHIB maps to `kSHIB`; 15m/1h/4h/1D public candle readiness and compact dynamic-equity evidence are recorded. |
| SV2.0.1 | Canonical evidence truth hotfix | Compact SV2 rows are explicitly noncanonical; dataset-end open positions are force-closed with entry-fee accounting; Hyperliquid close slots are normalized; staged/imported/canonical-evidence truth is separated; runtime allocations are 0.25 each; internal timeframe is `1d` with display label `1D`; missing indicators are invalid instead of zero. Canonical evidence packs remain blocked. |
| SV2.0.2 | Hardened DB import / canonical evidence packs | Normalized Hyperliquid public mainnet candles are imported through the hardened importer into the intended DB, 36 fully closed per-pair Money Flow v1.2 evidence packs are generated for BTC/ETH/SOL/XRP/DOGE/HYPE/BNB/SUI/AVAX x 15m/1h/4h/1d, and SHIB/kSHIB is deferred with explicit reason codes. |

## What Strategy Validation Proved

- ETH `sleeve_1h` baseline is the strongest observed Hyperliquid public-candle candidate.
- Hyperliquid public evidence justifies tightly scoped UAT observation only.
- Dynamic-equity per-scenario simulation exists.
- Lower-RSI variants did not beat ETH `sleeve_1h` baseline in the accepted true replay work.
- 15m and 4h are excluded from current UAT candidate scope.
- SV2.0 proves only that 1D is now represented as a baseline Money Flow sleeve and that expanded Hyperliquid public-mainnet readiness/evidence can be generated for the requested universe; it does not prove profitability.
- SV2.0.1 proves evidence-truth guardrails are explicit; it does not generate canonical evidence packs.
- SV2.0.2 proves the SV2 baseline now has DB-backed canonical evidence-pack paths with dynamic equity, canonical close slots, fully closed end-boundaries, explicit open-position handling, per-pair full available imported windows, and supported/deferred symbol truth; it still does not prove profitability.

## What Strategy Validation Did Not Prove

- It did not prove profitability.
- It did not approve paper trading.
- It did not approve live trading.
- It did not validate cross-venue performance.
- It did not model funding.
- It did not model liquidation.
- It did not model production exchange margin behavior.
- It did not model real order-book fills.
- It did not model partial fills.
- It did not model latency or outages.
- It did not model live reject / cancel / fill reconciliation behavior.
- SV2.0 did not optimize 1D parameters, approve live trading, submit orders, or generate full committed evidence-pack directories.
- SV2.0.1 did not make compact staged rows canonical evidence, did not import staged candles into the DB, and did not unblock SOR-EV1 by itself.
- SV2.0.2 did not optimize parameters, add stop-loss or RSI/MACD variants, submit orders, call private/signed/order endpoints, use testnet data as strategy truth, commit large generated evidence packs, or approve live trading.

## Current Candidate

See [[30 Strategy/UAT Candidate Freeze|UAT Candidate Freeze]].

Candidate id: `money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

## Excluded From Current UAT Scope

- 15m sleeve.
- 4h sleeve.
- BTC `sleeve_1h`.
- SOL `sleeve_1h`.
- Lower-RSI variants.
- Market-structure variants.
- Aster / Binance / OKX / Coinbase / Kraken.
- Cross-venue comparison.

## Interpretation Rule

Every SV result remains research-only. A scenario can be observed, diagnostically useful, or suitable for UAT/PT observation without proving profitability or authorizing live trading.

PAPER TRADING IS APPROVED. Paper trading is approved for Hyperliquid testnet/sandbox only under PT0. BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under metadata, precision, risk, lease, label, and no-live gates. Live trading is not approved. Live exchange order submission is not approved.
