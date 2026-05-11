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

## What Strategy Validation Proved

- ETH `sleeve_1h` baseline is the strongest observed Hyperliquid public-candle candidate.
- Hyperliquid public evidence justifies tightly scoped UAT observation only.
- Dynamic-equity per-scenario simulation exists.
- Lower-RSI variants did not beat ETH `sleeve_1h` baseline in the accepted true replay work.
- 15m and 4h are excluded from current UAT candidate scope.

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
