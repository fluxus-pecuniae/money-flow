# UAT Candidate Freeze

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Frozen Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Value |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Sleeve | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow only |

## Why Selected

- It is the only clearly above-starting-equity pocket in the accepted Hyperliquid public dynamic-equity evidence.
- It is the best current UAT behavior-observation candidate.
- Lower-RSI variants did not beat it.
- It is narrow enough to keep UAT0/UAT1/UAT2 scoped.

## What Is Excluded

- `sleeve_15m`
- `sleeve_4h`
- BTC `sleeve_1h`
- SOL `sleeve_1h`
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## Warnings

- Profitability is not proven.
- PAPER TRADING IS APPROVED. Paper trading is approved for Hyperliquid testnet/sandbox only under PT0.
- BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED. Broader top-20 Hyperliquid-supported paper/sandbox trading is approved under gates only.
- Live trading is not approved.
- Live exchange order submission is not approved.
- UAT validates plumbing and behavior, not performance.

## UAT Observation Universe Correction

The frozen candidate above is the evidence candidate, not the full future UAT observation universe.

Future UAT observation should cover the top 20 high-volume crypto assets supported by the selected UAT venue/environment. That broader universe is for platform behavior validation only:

- signal generation
- no-trade reasoning
- rejected-signal behavior
- market metadata resolution
- symbol mapping
- venue support
- risk visibility
- shadow would-trade behavior
- dashboard/operator visibility

Top-20 inclusion is approved for PT0 paper/sandbox scanning and risk-gated Hyperliquid testnet/sandbox route candidates only. It is not strategy approval, live trading approval, cross-venue routing approval, SOR/fanout approval, or strategy profitability proof.
